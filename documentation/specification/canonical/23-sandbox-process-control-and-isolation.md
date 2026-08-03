# Sandbox, Process Control, and Isolation

## Status

Canonical. This file defines the execution-containment layer of ATLAS3: how processes are spawned and tracked, how a unit of execution is confined to a filesystem, network, and resource budget, how that confinement is enforced and verified, how every spawned unit is killed and reaped, and how privileged operations cross the trust boundary. It realizes the containment, killability, filesystem-boundary, network-enforcement, and process-isolation primitives that Files 01, 04, 05, 06, 09, 10, 17, 18, 19, 20, and 22 declare and delegate to this layer, and it introduces the net-new primitives those files reference but do not own: the `Sandbox` contract, the `ManagedProcess` and `ProcessGroup` model, the `IsolationTier` ordinal, the filesystem and network enforcement mechanics, and the elevated-helper process model. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the chosen model: one execution-containment substrate, expressed as a typed `Sandbox` contract, that supersedes every per-surface ad-hoc sandbox and is the single owner of process spawning, confinement, and killability
- the `Sandbox` contract — its lifecycle (create, spawn, signal, teardown), its `SandboxSpec` configuration, the settings-owned `SandboxProfile` per-consumer defaults, and the rule that the concrete operating-system mechanism is a replaceable implementation behind the contract
- the `IsolationTier` ordinal (`None`, `RuntimeConfined`, `OsConfined`, `Virtualized`) and how a unit's trust class (File 22) and policy requirements select the minimum tier that contains it
- process spawning and the `ManagedProcess` model — command, arguments, working directory, the environment policy, standard-stream capture, the process handle, and the rule that no execution-containment unit is non-killable
- `ProcessGroup`s and the sandbox-to-process ownership tree that makes categorical kill (a sandbox and everything it owns) and individual kill (one process) both first-class
- filesystem boundary enforcement — canonical-path containment at the single service-trait chokepoint, symlink resolution before the boundary check, the time-of-check-to-time-of-use discipline, and the operating-system-level filesystem confinement that contains a spawned process the service trait does not mediate
- network policy enforcement — the closed `NetworkPolicy`, the operating-system-level network confinement of a spawned process, the application-layer destination check that consumes File 22's egress-destination policy, and per-hop redirect re-validation
- resource isolation and limits — the closed `ResourceLimits` dimensions, the event-driven threshold-kill, and the rule that an elapsed-time guard is a finite configurable external-process safety guard, never a correctness condition
- killability, escalation, and reaping — the realization of File 04's cancellation contract for processes and sandboxes: cooperative stop, forceful escalation, categorical and individual targets, post-kill cleanup, and orphan reaping at restart
- the elevated-helper process model — a separate, least-privilege, lazily-installed helper reachable only over local inter-process communication with a versioned built-in helper-operation manifest; the pairing credential and least-privilege principle remain File 22's
- subprocess-wrapper and home isolation — process-group-tracked subprocess lifecycle for command-line subscription wrappers, per-instance home-directory and environment isolation, and the typed runtime-environment context
- declared-versus-observed enforcement — the runtime catching of touched resources outside a capability's declared scope and the typed violations it emits
- process and sandbox observation, handles, and reconstruction — the transient runtime handles the world model projects from, the snapshot `Observation` blocks capability revalidation depends on, and reaping rather than reconnection at restart
- the cross-platform realization, the secret and trust boundary across the process boundary, the sandbox/process capability surface, the event vocabulary, the settings dimensions, the explicit rejections, and the consequences later specs consume

This file does not define:

- the run, child-run, cancellation, or completion contracts themselves — File 04 owns the `Run`, the shared cancellation signal, the cooperative-stop-deadline-then-forceful-escalation contract, the categorical-and-individual cancellation requirement, the orphan-run reconciliation policy, and the isolation-primitive *selection* policy per child run; this file enforces them over processes and sandboxes and provides the primitives File 04 §16.2 and §29 name
- the capability declaration schema, the touched-resource expression grammar, the resource-class catalogue, or the policy evaluation, lease, tier, and approval algorithms — Files 05 and 06 own those; this file is the runtime sandbox that enforces what those declarations name and emits typed violations when actual access escapes the declared scope (`capability.touched-resources`, File 05 §6.6; `policy.touched-resource-matching-against-lease-scope`, File 06 §6)
- secret-vault internals, credential lifecycle, trust classes and verification, encryption, the egress-destination *policy classification*, or the privilege-separation pairing credential — File 22 owns those; this file consumes the trust decision, the egress policy, and the secret rules across process boundaries, and owns the elevated-helper process the pairing credential authorizes
- the sensitivity taxonomy, the event envelope structure, the hook authority model, the audit-chain construction, or the cancellation ledger-entry catalogue — File 10 owns those; this file emits process and sandbox events through that bus, uses the `backend_id` envelope dimension, and writes the reserved kill and cleanup entries
- the storage substrate, the data-root and read-only-installation-directory layout, blob storage, or runtime-handle projection rebuild — File 20 owns those; this file builds filesystem enforcement on the layout File 20 places and declares process and sandbox handles transient projections reaped at restart
- workspace identity, materialized workspace and worktree directories, or git worktree management — File 24 owns those; this file owns the filesystem confinement the worktree directory is one boundary of, not the workspace mirror
- the per-surface capability extensions a sandbox carries — graphical-input and screen observation (GUI Control), browser navigation and profile semantics (Web), code-execution language runtimes and preview rendering (Coder), device control (System Agent) — the per-surface specs own those as extensions over this file's base `Sandbox` contract; this file owns the base contract, the process and isolation primitives, and the filesystem, network, resource, and kill enforcement they compose with
- the model-provider, automation, plugin, MCP-transport, packaging, and UI concerns adjacent to processes — the owning files define those; this file provides the managed-process substrate they spawn through and the data contracts they render

## Source Resolution

This file resolves process spawning, shell and command execution, code-execution sandboxes, virtual-machine and container isolation, browser-process management, graphical-control desktop isolation, filesystem-boundary enforcement, network-egress enforcement, resource limits, process killability, elevated and privileged operations, and subprocess-wrapper lifecycle into one boundary: the execution-containment layer that spawns, confines, observes, and kills every Atlas-managed unit of execution, without re-owning any run semantics, policy algorithm, secret, or storage layout.

Resolved design:

- ATLAS3 has one execution-containment substrate, expressed as a typed `Sandbox` contract. Every place the system runs code that could touch the filesystem, the network, resources, or the operating system — a shell command, a code-execution call, a preview process, a custom-tool runtime, a graphical-control session, a managed browser, a command-line subscription wrapper, a bundled sidecar — runs inside a `Sandbox` and produces `ManagedProcess`es tracked in `ProcessGroup`s. There is no second sandbox abstraction, no private process spawner, and no ungoverned filesystem or network path.
- The concrete operating-system isolation mechanism is a replaceable implementation behind the contract (`core.extension-integrity`, File 01 §7.10). A canonical rule may name a committed realization — operating-system process sandboxes, kernel filesystem and syscall confinement, virtual machines and containers, in-process bytecode runtimes — for grounding, but never depends on a mechanism the contract does not expose.
- Confinement is expressed along orthogonal dimensions — filesystem, network, resource — plus a coarse `IsolationTier` ordinal that names the boundary an escape must cross. The runtime selects the minimum tier that satisfies the unit's trust class and policy requirements; stricter isolation is never the silent default where it is not needed, and untrusted code never runs below the tier its trust class requires.
- Enforcement is structural and defense-in-depth. The filesystem and network boundaries are enforced both at the single service-trait chokepoint that mediates Atlas's own access and at the operating-system level that contains a spawned process the service trait does not mediate. A declared scope the runtime cannot enforce is still the contract; the runtime catches the violation and emits a typed error (`capability.touched-resources`, File 05 §6.6).
- Every Atlas-managed unit of execution is killable, both categorically and individually, at a safe boundary (File 01 §7.11). This file defines no intentionally non-killable unit: a spawned process belongs to a process group, and the group is the categorical-kill target; cooperative stop precedes forceful termination; a forceful-kill failure is a typed platform violation that is surfaced, quarantined where possible, and never treated as successful termination.
- Time is never a correctness condition. Elapsed-time guards are finite, configurable, killable external-process safety nets: decisive only where no reliable completion signal exists, and otherwise a backstop for a signal-bearing process that hangs (`run.budgets-limits`, File 04 §21; `run.cancellation`, File 04 §17.3). Resource and output limits are event-driven thresholds, not timers.
- Privileged operations cross a sharp boundary. The main process never runs elevated; a separate, least-privilege, lazily-installed helper performs the narrow set of privileged operations the user authorizes, reachable only over local inter-process communication with a versioned built-in helper-operation manifest.

Resolved tensions:

- One shared sandbox abstraction versus the four divergent ad-hoc sandboxes the source material accreted (a shell sandbox, a code-execution sandbox, a preview sandbox, and a graphical-control sandbox, with a custom-tool runtime sandbox a fifth): resolved decisively toward one `Sandbox` contract with per-consumer `SandboxProfile` defaults and per-surface capability extensions, because divergent sandboxes are unauditable, drift apart, and re-implement the same filesystem and kill enforcement four times. The unification was the explicitly-stated mandate of the source recommendations; this file is that single owner.
- A single ordinal isolation level versus orthogonal per-dimension policies: resolved toward both, kept orthogonal. The `IsolationTier` ordinal answers "what boundary contains an escape" and drives selection and display; the `FilesystemPolicy`, `NetworkPolicy`, and `ResourceLimits` dimensions answer "what may this unit touch" and drive enforcement. Conflating them — for example treating a graphical-control mode's window cloaking as a security tier — would misrepresent isolation that is presentational as if it were a security boundary.
- Service-trait path validation versus operating-system filesystem confinement: resolved toward defense-in-depth. The service-trait chokepoint is the always-on structural enforcement for Atlas-mediated file access (the rule File 22 §13.3 deferred here); the operating-system filesystem confinement is what contains a spawned subprocess whose own file access never passes through the trait. Neither alone is sufficient; both are required.
- Blocklists versus allowlists for dangerous commands and environment variables: resolved toward allowlists and structural inspection over blocklists. No fixed blocklist of dangerous command names is treated as complete; command safety comes from the permission tier, machine-readable command inspection surfaced to the policy layer, an environment-variable allowlist, and user-authored guardrail hooks (`run.hook-integration`, File 04 §23.3). A blocklist of forbidden command names is rejected as the safety boundary because it is trivially bypassed and never complete.
- Time-based safety guards versus the no-time-based-behavior rule: resolved by confining elapsed time to the external-process safety-guard role File 04 §21 already carved out. A wall-clock guard is a finite, configurable, killable safety net — decisive only for a process with no reliable completion signal, and otherwise a backstop for one that hangs past its signal; it is never a correctness condition, and resource and output limits are event-driven thresholds rather than timers.

## 1. Chosen Model

Anchor: `sandbox.chosen-model`

### 1.1 Definition

ATLAS3 has one execution-containment substrate. It is a substrate service (`core.substrate-services`, File 01 §2.4) expressed as a typed `Sandbox` contract beneath every other layer that runs code. A `Sandbox` is a confined execution environment with a declared filesystem policy, network policy, resource budget, and isolation tier. A `ManagedProcess` is an operating-system process Atlas spawned and tracks; a `ProcessGroup` is the set of managed processes a sandbox or run owns and the unit of categorical kill. The committed realizations behind the contract are the platform's process-sandbox, kernel-confinement, virtual-machine, container, and in-process-runtime mechanisms; all sit behind the `Sandbox` contract.

### 1.2 Purpose

Files 01 through 22 each declare an execution-containment boundary and delegate its internals here: File 01 the killability invariant (§7.11); File 04 the isolation primitives, the cancellation contract over processes and sandboxes, and the resource budgets; File 05 the runtime sandbox that enforces touched resources; File 06 the filesystem, network, and process-group containment leases narrow; File 09 the snapshot observations sandboxed runs depend on; File 10 the events sandbox and process operations emit; File 17 the subprocess-wrapper lifecycle; File 18 the process and sandbox entities the world model reasons about; File 19 the sandbox writable roots perception reports; File 20 the force-termination at shutdown; File 22 the containment of an untrusted source, the network enforcement of the egress policy, and the elevated-helper process. This file is the single place those internals become concrete, so that no later spec invents a parallel process spawner, a private sandbox, an ungoverned filesystem path, an unenforced network destination, or a non-killable unit of execution.

### 1.3 Rule

- There is one `Sandbox` contract, one `ManagedProcess` and `ProcessGroup` model, one filesystem-boundary enforcement chokepoint, one network-enforcement contract, and one elevated-helper model. No subsystem, surface, plugin, or connector may spawn a process outside the managed-process model, open a private sandbox abstraction, perform its own filesystem-boundary validation, reach the network from a sandboxed process outside the network policy, or run a privileged operation outside the elevated-helper boundary.
- Every unit of execution that can touch the filesystem, the network, resources, or the operating system runs inside a `Sandbox`, configured by a `SandboxSpec`, and produces `ManagedProcess`es tracked in a `ProcessGroup`. The concrete operating-system mechanism is a replaceable implementation behind the contract; a canonical rule may name a committed realization for grounding but must not depend on a mechanism-specific capability the contract does not expose.
- Confinement is least-authority by default and selected, not assumed: the runtime confines a unit to the narrowest filesystem, network, and resource policy and the minimum isolation tier that does the job, derived from the unit's trust class and policy requirements; broad authority and weak isolation are explicit, recorded choices, never silent defaults.
- Enforcement is structural and defense-in-depth: the filesystem and network boundaries are enforced both at the service-trait chokepoint and at the operating-system level. A declared scope the runtime cannot enforce is still the contract; the runtime catches the violation and emits a typed error.
- Every Atlas-managed unit of execution is killable both categorically and individually at a safe boundary. This file defines no intentionally non-killable unit. Cooperative stop precedes forceful termination, killing a sandbox kills everything it owns, and any platform-level kill failure is recorded as a typed failure rather than hidden.
- Time is never a correctness condition. Wall-clock guards are finite, configurable, killable external-process safety guards; resource and output limits are event-driven thresholds.
- The main process never runs elevated. Privileged operations cross the elevated-helper boundary, which is human-governed and least-privilege by construction (`core.extension-planes`, File 01 §6.14; `security.device-trust`, File 22 §10.3).

### 1.4 Boundary

This file owns the `Sandbox` contract, the process and isolation primitives, and the filesystem, network, resource, and kill enforcement. File 04 owns the run, child-run, and cancellation contracts and the isolation-primitive selection policy; this file enforces them and provides the primitives. Files 05 and 06 own the capability declaration and policy evaluation; this file is the runtime sandbox that enforces what they decide. File 22 owns trust, secrets, egress classification, and the pairing credential; this file consumes those and owns the helper process. Files 10, 18, 19, and 20 own events, world entities, perception, and storage; this file emits, projects, reports, and persists through them.

## 2. Boundaries with Adjacent Layers

Anchor: `sandbox.boundaries-with-adjacent-layers`

### 2.1 With File 01 (Core Thesis, Invariants, and Primitives)

User control and killability (File 01 §7.11) requires that runs, child-run trees, processes, sandboxes, and tool calls be cancellable or killable both categorically and individually, and that non-killable execution be an explicit, justified exception. This file realizes that invariant for processes and sandboxes (§10) and declares no intentionally non-killable unit. `core.extension-planes` (File 01 §6.14) forbids extensions from overriding security-critical system state, including the environment variables that control paths, linkers, and interpreters; this file is where that prohibition is enforced at the process-spawn boundary through the environment-variable allowlist (§5, §12). `core.extension-integrity` and the replaceable-behind-a-contract rule (File 01 §7.10) ground the `Sandbox` contract over a replaceable operating-system mechanism. `core.canonical-hash` and `core.canonical-encoding` (File 01 §6.15, §7.14) govern canonical integrity records this file defines, including the helper manifest and snapshot observation fingerprint; executable helper bytes are verified by artifact digest and package evidence (§11). `core.stack-commitments` (File 01 §9) grounds the Tauri process model and the Rust backend the helper and sandbox services live in.

### 2.2 With File 04 (Execution and Run Model)

The boundary is the contract-versus-enforcement split. File 04 owns the `Run`, the shared cancellation signal all listeners receive (`run.cancellation`, File 04 §17.3), the cooperative-stop-deadline-then-forceful-escalation contract, the categorical-and-individual cancellation requirement, the partial-output and orphan-run rules, the per-run resource budgets (`run.budgets-limits`, File 04 §21), and the policy that selects which isolation primitive a child run uses (`run.isolation`, File 04 §16.2). This file owns the process and sandbox primitives that contract is enforced over: it registers the spawned processes and sandboxes as cancellation listeners, performs the cooperative-then-forceful kill, reaps on orphan-run reconciliation, and provides the isolated process group, the operating-system sandbox, and the virtual-machine instance File 04 §16.2 and §29 name as the canonical isolation primitives. The runtime's choice of which primitive to use for a given child run is File 04's; the primitive itself is this file's.

### 2.3 With File 05 (Capability Contracts and Registry) and File 06 (Capability Policy, Approvals, and Leases)

File 05 owns the capability declaration, the closed resource-class catalogue (`filesystem`, `network`, `process`, `env`, and the rest, `capability.touched-resources`, File 05 §6.2), the touched-resource expressions (`capability.resource-expressions`, File 05 §6.4), and the rule that a declared scope the runtime cannot enforce is still the contract while the runtime catches violations (`capability.touched-resources`, File 05 §6.6). File 06 owns the touched-resource matching that decides whether a call's resolved resources fall within an active lease's constraints, including filesystem path-subtree containment, network host-set containment, and process-group containment (`policy.touched-resource-matching-against-lease-scope`, File 06 §6.3). This file is the runtime sandbox those declarations name: it enforces the resolved filesystem, network, and process scopes at execution time (§7, §8, §13), catches access that escapes the declared or leased scope, and emits the typed violations (§13). It owns no policy evaluation; it is the layer at which the policy's resolved scope becomes an enforced boundary.

### 2.4 With File 09 (Artifacts, Claims, Evidence, and Provenance)

`artifact.consequences-for-later-specs` (File 09 §22) requires this file to commit `Observation` blocks for sandboxed-process snapshots that capability runs depend on for revalidation, conforming to the observation contract (kind, payload, staleness fingerprint, `artifact.observation`, File 09 §13). This file produces `ProcessSnapshot` and `SandboxSnapshot` observations through the canonical `observation.commit` path (§14) so that a capability whose mutation depends on prior process or sandbox state can revalidate currency (`run.call-pipeline`, File 04 §8.2) and so cross-surface inspection sees the same snapshots. File 09 owns the observation contract and provenance; this file produces the process and sandbox observations against it.

### 2.5 With File 10 (Execution Ledger, Event Stream, and Hooks)

File 10 owns the event envelope, the `backend_id` dimension that demultiplexes concurrent provider, sandbox, and process instances (`ledger.event-envelope`, File 10 §5.2), the cancellation and kill entry catalogue (`CancellationRequested`, `KillRequested`, `KillSucceeded`, `KillFailed`, `CleanupCompleted`, `CancellationCompleted`, File 10 §14), the sensitivity taxonomy, and the hook authority and fail-direction rules. This file emits process and sandbox events through that bus, stamps the `backend_id` so multiple sandboxes and processes of the same kind are demultiplexable, writes the reserved kill and cleanup entries when it terminates a unit, and registers sandbox-specific facts as named `Custom { namespace, name, payload }` kinds under the `sandbox` and `process` namespaces. The global intervention cancellation token File 10 shares across the agent loop, tool calls, sandbox operations, and service calls (File 10 §17.3) is the signal this file's processes and sandboxes honor.

### 2.6 With File 17 (Provider Layer, Rate Limits, and Usage Accounting)

`provider.consequences-for-later-specs` (File 17 §26) requires this file to support the subscription-wrapper subprocess lifecycle in its sandbox primitives — process groups, home isolation, and shadow homes — and the provider-adapter contract (File 17 §3) defines the typed `runtime_environment` sandbox-or-process context for subscription wrappers. This file provides that lifecycle (§12): a command-line subscription wrapper runs as a `ManagedProcess` in a `ProcessGroup`, with per-instance home-directory isolation and an environment-variable allowlist, and the `runtime_environment` resolves to a `SandboxSpec`. The provider adapter owns the wrapper's protocol, argument shaping, and usage parsing; this file owns the process isolation and lifecycle it runs in.

### 2.7 With File 18 (World Model) and File 19 (Perception)

File 18 owns the `Process`, `Sandbox`, and `Connection` `WorldEntity` kinds, their liveness facts, and the `produced_by` and `bound_to` relations (File 18 §4); most are device-local and never sync. This file provides the runtime handles and liveness facts those entities project from (§14): a `Process` entity projects from a `ManagedProcess`, a `Sandbox` entity projects from a `Sandbox`, and their liveness is the live process and sandbox status this file reports. File 19 owns the perception capture pipeline and the `Environment` sensor that reports sandbox writable roots and the workspace boundary, resolving symlinks before the boundary check (`perception.capture-privacy`, File 19 §10). This file owns the sandbox writable roots perception reports and the symlink-before-boundary rule perception applies; perception senses, this file confines.

### 2.8 With File 20 (Storage and Persistence)

`storage.physical-layout-locality` (File 20 §8) places the data root, makes the installation directory read-only to the running application, and resolves paths through a bootstrap environment variable; this file builds the workspace and sandbox filesystem boundaries on that layout (§7). `storage.lifecycle-reconstruction` (File 20 §13.3) requires that at shutdown, eligible processes be cancelled or killed through File 04's killability contract — which this file enforces (§10) — and that subprocess and sandbox handles are runtime-handle projections reconstructed during startup; this file declares those handles transient and reaps orphaned processes and sandboxes at restart rather than reconnecting to them (§14). File 20 owns the storage substrate and the handle-projection rebuild orchestration; this file owns the processes and sandboxes the handles point at.

### 2.9 With File 22 (Security, Credentials, and Trust Boundaries)

The boundary is sharp and was fixed by File 22 §2.8 and §19. File 22 owns the trust decision that selects how strictly to sandbox an untrusted source (`security.trust-model`, File 22 §9), the egress-destination policy the network enforcement consults (`security.egress-governance`, File 22 §11), the secret and credential rules across process boundaries and the backend secret boundary (`secret.backend-boundary`, File 22 §4), and the privilege-separation pairing credential (`security.device-trust`, File 22 §10.3). This file consumes the trust decision to select the isolation tier (§4), enforces the egress-destination policy at the network boundary (§8), honors the secret boundary across the process boundary (§16), and owns the elevated-helper *process* the pairing credential authorizes (§11). File 22 decides trust and policy; this file enforces containment.

### 2.10 With File 24 (Workspaces) and the per-surface, automation, and packaging specs

File 24 owns workspace identity, the materialized workspace and worktree directories, and the disk-to-block mirror; this file owns the filesystem confinement the worktree directory is one boundary of, not the directory's identity or lifecycle. The per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) own the capability extensions a sandbox carries — graphical input and screen observation, browser navigation, code-execution language runtimes, preview rendering, device control — as extensions over this file's base `Sandbox` contract. File 33 (Automation and Triggers) spawns non-interactive work through this file's managed-process substrate under least authority. The Packaging, Platform, and Distribution spec (File 43) owns the sidecar binary inventory and packaging; this file owns the managed-process substrate sidecars are spawned and killed through.

### 2.11 Boundary

This file is the execution-containment layer. It owns no run semantics, no policy algorithm, no capability schema, no secret, no trust class, no egress classification, no event envelope, no world-entity catalogue, no storage layout, and no workspace identity. It owns the `Sandbox` contract, the process and isolation primitives, and the filesystem, network, resource, and kill enforcement, and supplies each to the layer that consumes it.

## 3. The Sandbox Contract, Profiles, and the Registry

Anchor: `sandbox.contract`

### 3.1 Definition

A `Sandbox` is a confined execution environment with a typed contract. The contract exposes at least: create a sandbox from a `SandboxSpec`; spawn a `ManagedProcess` inside it; signal a process it owns; report the filesystem, network, and resource policies in force; check a proposed filesystem path, network destination, or resource request against those policies; observe its own liveness and resource usage; and tear down, killing every process it owns. A `SandboxSpec` is the configuration of a sandbox: its `IsolationTier` (§4), `FilesystemPolicy` (§7), `NetworkPolicy` (§8), `ResourceLimits` (§9), `EnvPolicy` and home isolation (§5, §12), and working directory. A `SandboxProfile` is a named, settings-owned default `SandboxSpec` for a consumer class — a shell execution, a code-execution call, a preview process, a custom-tool runtime, a graphical-control session, a managed browser, a subscription-wrapper subprocess, a bundled sidecar.

### 3.2 Purpose

The source material accreted four divergent sandbox abstractions — a shell sandbox, a code-execution sandbox, a preview sandbox, and a graphical-control sandbox, with a custom-tool runtime sandbox a fifth — each re-implementing filesystem confinement, resource limits, and process kill. Four abstractions cannot be audited as one, drift apart over time, and force every new consumer to choose which to copy. One contract with per-consumer profiles makes confinement a single auditable surface: every consumer configures the same contract, and a new consumer declares a profile rather than inventing a sandbox.

### 3.3 Rule

- The `Sandbox` contract is the single execution-containment abstraction. The graphical-control sandbox, the shell sandbox, the code-execution sandbox, the preview sandbox, and the custom-tool runtime sandbox are profiles of this one contract, not separate abstractions; a per-surface sandbox extends the base contract with its capability extension (graphical input and observation, browser navigation) and does not redefine the lifecycle, the policies, or the kill semantics.
- Every consumer that runs confined code declares a `SandboxProfile`: the default `SandboxSpec` for that consumer class, owned as settings (§19) so the default is tunable per profile, workspace, and platform and is never a hardcoded constant. A call may narrow the spec for a specific invocation; it may widen the spec only through the policy and approval layer (File 06).
- A `SandboxRegistry` records the available sandbox realizations on the current device — which isolation tiers and mechanisms the platform supports — so the runtime can resolve a `SandboxSpec` to a concrete realization and so a spec requesting an unavailable tier resolves to a typed `SandboxUnavailable` state rather than silently downgrading. Downgrading isolation below the requested tier is never silent: it surfaces and re-gates through policy.
- The contract is the semantic boundary; the concrete mechanism behind it is replaceable. A canonical rule names a committed realization for grounding but never makes a mechanism-specific capability the contract does not expose load-bearing.
- A sandbox owns its processes. Tearing down a sandbox kills every `ManagedProcess` in its `ProcessGroup` (§6, §10); no process outlives the sandbox that owns it except where a capability declares resumable infrastructure (`run.cancellation`, File 04 §17.3) and the runtime hands the process to a new owner.

### 3.4 Boundary

This section owns the contract, the profile model, and the registry. File 04 owns which profile or primitive a child run selects. The per-surface specs own the capability extensions that extend the base. File 15 owns the settings cascade the profiles resolve through.

## 4. Isolation Tiers and the Trust-to-Strictness Mapping

Anchor: `sandbox.isolation-tiers`

### 4.1 Definition

The `IsolationTier` is a closed, ordinal classification of the boundary an escape from a sandbox must cross. It is orthogonal to the filesystem, network, and resource policies, which answer what a unit may touch; the tier answers what contains it if it tries to touch more. The tiers, from weakest to strongest:

- `None` — no containment boundary. The code is trusted to stay within bounds; the only protections are the application-layer service-trait checks (§7, §8). Used for the application's own trusted execution and for active-desktop graphical control where the agent operates the user's real session.
- `RuntimeConfined` — an in-process bytecode or language runtime whose only escape is a capability-mediated host interface. The runtime cannot reach the filesystem, network, operating system, foreign-function interface, native addon mechanism, or equivalent native-code escape except through host functions the contract grants. Used for in-process custom-tool and artifact runtimes, which run inside the backend's own process and shared address space; because that address space holds resident secret material, a trust floor governs which sources may run there (§4.3).
- `OsConfined` — a host operating-system process confined by kernel-level filesystem, syscall, and network restriction. It shares the host kernel; the boundary is the kernel's enforcement of the sandbox's filesystem, network, and resource policies. Used for shell, code-execution, preview, and subprocess-wrapper processes that must run native binaries but stay confined.
- `Virtualized` — a separate execution environment such as a microvirtual-machine, virtual machine, or containerized environment with its own namespace set and guest agent. The realization declares whether the kernel boundary is `SeparateKernel` or `SharedKernel`; a trust class that demands a kernel boundary is satisfied only by a separate-kernel realization. Used for untrusted code, for graphical control requiring full operating-system isolation, and wherever the trust class demands an environment boundary stronger than host-process confinement.

### 4.2 Purpose

A single boolean "sandboxed or not" cannot express that an in-process Wasm runtime, a kernel-confined shell process, and a microvirtual-machine offer materially different containment against materially different threats. Naming the boundary precisely is what lets the runtime select honestly: the minimum tier that contains the unit, and never weaker than its trust class requires.

### 4.3 Rule

- The runtime selects the minimum `IsolationTier` that satisfies the unit's trust class and policy requirements. An untrusted or unverified source (`security.trust-model`, File 22 §9) never runs below the tier its trust class requires; a `Verified`, `User`, or `System` source may run at a weaker tier where policy allows. The trust-to-tier mapping is THIS section's table, consuming the File 22 §9 trust class (§4.4, File 22 §2.8 — File 22 owns the class and its changes; this file owns the mapping and the selection):

  | Trust class (File 22 §9.2) | Default minimum tier | May policy weaken it? |
  |---|---|---|
  | `System` | `None` | No lower tier exists — the runtime itself. |
  | `Verified` | `RuntimeConfined` | Yes, to `None`, through explicit typed policy widening (File 06). |
  | `User` | `RuntimeConfined` | Yes, to `None`, through explicit typed policy widening (File 06). |
  | `Community` | `OsConfined`, in a separate process | No direct weakening. |
  | `Unverified` | `OsConfined`, in a separate process | No direct weakening. |
  | `Sideloaded` | `OsConfined`, in a separate process | No direct weakening. |

  The table states floors, never ceilings: unit, effect, consumer-profile, platform, and policy requirements may select a stronger tier (§4.1 — a trust class or policy demanding a kernel boundary is satisfied only by a separate-kernel `Virtualized` realization), and `Community` sits with the untrusted classes because the canonical trust-escalation table already groups it there (`policy.effective-tier-resolution`, File 06 §4.2 step 3). Policy never directly waives a class floor: the sanctioned escape is the explicit File 22 §9.8 effective-trust override — capped at `User`-equivalent — after which this table re-evaluates under the raised class. A floor the platform cannot realize resolves to `SandboxUnavailable` and re-gates (§3.3), never a silent downgrade.
- `RuntimeConfined` is valid only when every host interaction is enumerated, mediated, and revocable through the sandbox's capability surface. A runtime whose host interface includes unmediated foreign-function or native-code escape paths — Python `ctypes`, Node native addons, JNI, or equivalent — does not qualify for `RuntimeConfined`; the unmediated escape is functionally equivalent to `None` isolation and must run at `OsConfined` or higher.
- `RuntimeConfined` executes in the backend's own process and address space, which holds resident secret material (`secret.backend-boundary`, File 22 §4), so it carries a trust floor independent of its host-interface mediation. A `Verified`, `User`, or `System` source may run `RuntimeConfined` in-backend; a `Community`, `Unverified`, or `Sideloaded` source (`security.trust-model`, File 22 §9) does not, and runs at `OsConfined` or higher in a separate process (`plugin.code-backends`, File 35 §8) — the §4.3 table's floor and this in-backend floor coincide for those classes. Where below-floor code must run in-process, it runs only on a memory-safe engine with no secret material resident in the address space during its execution, or in a separate unprivileged host process; the shared secret address space is never exposed to a source below the floor.
- Window cloaking, virtual-desktop placement, and other presentational separation are not isolation tiers. They are presentation-isolation facets owned by the graphical-control surface; a graphical-control mode that visually separates the agent's windows from the user's but shares the registry, environment, filesystem, network, and process table provides `None` security isolation with a presentation overlay, and this file classifies it as such. Untrusted code requiring a real boundary runs at `Virtualized`.
- The tier is recorded on every spawn and sandbox creation and is part of the touched-resource and policy preview the user sees before approval (`policy.approval-router`, File 06). A unit's tier never silently weakens; weakening requires policy re-evaluation.
- The tier the registry resolves may exceed the requested tier (the platform offers only stronger isolation); it never silently falls below it. A requested tier the platform cannot provide resolves to `SandboxUnavailable` and re-gates.
- Each concrete realization records its mechanism and kernel boundary. A shared-kernel container may satisfy `Virtualized` where namespace isolation is enough, but it does not satisfy a policy or trust class requiring separate-kernel isolation.

### 4.4 Boundary

This section owns the tier ordinal and the selection rule. File 22 owns the trust class the selection consumes. The per-surface specs own presentational isolation facets. The concrete mechanism realizing each tier is §15's.

## 5. Process Spawning and the Managed-Process Model

Anchor: `process.spawning`

### 5.1 Definition

A `ManagedProcess` is an operating-system process Atlas spawned and tracks for its whole lifetime. It is created inside a `Sandbox` from a spawn request that carries the program and its argument vector (never a shell-interpreted string unless a shell is the explicit program), the working directory, the environment under an `EnvPolicy`, the standard-stream disposition, and the owning `ProcessGroup`. The runtime returns a `ProcessHandle` — a transient runtime reference, not a durable identity — through which the process is observed, signalled, and killed.

### 5.2 Purpose

Every consequential process must be created the same way, tracked the same way, and killable the same way. An untracked process is an unkillable process and an unaccountable one; confining all spawning to one model is what makes killability (§10), observation (§14), and resource accounting (§9) universal rather than per-consumer.

### 5.3 Rule

- A process is spawned with an explicit program and argument vector. A shell is invoked only when a shell is the explicit program (for example a login shell running a script); the runtime never builds a single shell-interpreted command string from agent-supplied fragments and hands it to a shell, because that erases the argument boundary. When the explicit program is a shell or interpreter that accepts command text, a registered inspector parses the payload before spawn and emits policy-visible facts for filesystem redirections, process mutation, network attempts, environment mutation, package-manager activity, destructive operations, and unknown dynamic constructs. Parse failure or unsupported dynamic behavior escalates through File 06 policy; safety does not depend on command-name blocklists.
- The environment a process receives is governed by an `EnvPolicy`: `Allowlist` (the default — a synthesized environment containing only allowlisted variables plus approved per-call additions), `HostEnvironment` (the full parent environment, permitted only for explicitly user-trusted interactive execution), or `Empty`. The allowlist is the mechanism that enforces `core.extension-planes` (File 01 §6.14) at the spawn boundary: variables that control paths, shells, linkers, interpreters, startup files, package managers, and secret-bearing state are excluded by default and never silently inheritable by a spawned process. `HOME`, temp roots, path variables, linker variables, interpreter variables, and shell startup variables are synthesized or explicitly approved. The allowlist is settings-owned (§19) and never a hardcoded constant where meaningful variation exists.
- The working directory defaults to the sandbox's confined root and may not be set outside the sandbox's filesystem policy; a working directory outside the confined root is a filesystem-boundary violation (§7), not a silent escape.
- Standard output and standard error are captured, bounded, and streamed. Output is write-throttled and bounded by an event-driven byte cap (§9); a process exceeding the cap is killed, not allowed to exhaust memory. Standard input is supplied explicitly; a process never blocks indefinitely on an interactive prompt the runtime did not intend, and interactive programs run on a pseudo-terminal (§5.4) when interactivity is required.
- Every `ManagedProcess` belongs to exactly one `ProcessGroup` (§6) and is killable both individually and as part of its group. The runtime defines no non-killable process.
- A spawn that the policy layer denies returns a typed `SpawnDenied` result in-band (`run.denial-is-in-band`, File 04 §8.3); a spawn that fails for an operating-system reason returns a typed spawn error; neither crashes the run.

### 5.4 Pseudo-Terminal and Plain-Subprocess Spawning

A process may be spawned with captured pipes (the default for non-interactive command execution) or on a pseudo-terminal when interactivity, job control, or terminal-aware output is required. The pseudo-terminal realization is the platform's native facility (a controlling-terminal pair on Unix, a pseudo-console on Windows); it is a spawn mode of the managed-process model, not a separate process abstraction. The pseudo-terminal carries terminal dimensions, propagates terminal resize and control signals (interrupt, suspend, end-of-file) to the process, and is killable on the same contract as a piped process. Output is buffered into a bounded rolling buffer so a late-attaching observer can catch up; the buffer is a transient projection, not a durable record.

### 5.5 Boundary

This section owns the spawn model, the environment policy, interpreter-payload inspection at the spawn boundary, and the pseudo-terminal mode. File 05 and File 06 own the capability declaration and policy evaluation that consume the inspection facts; the per-surface tool catalogues that expose process spawning are the per-surface specs'. The terminal-rendering surface is File 37's.

## 6. Process Groups and Categorical Ownership

Anchor: `process.groups`

### 6.1 Definition

A `ProcessGroup` is the set of `ManagedProcess`es a sandbox, a run, or a child run owns, plus their descendant processes, tracked as one unit. It is the categorical-kill target: killing the group kills every process in it, including children a managed process spawned itself. The sandbox-to-process ownership tree is the hierarchy of process groups under sandboxes under runs and child runs, which makes both categorical kill (a whole subtree) and individual kill (one process) first-class.

### 6.2 Purpose

A process that spawns its own children — a build that forks compilers, a shell that runs a pipeline, a wrapper that launches a model command-line tool — leaves orphans if only the parent is killed. The process group is what makes "kill this sandbox and everything it spawned" a single, reliable operation rather than a best-effort sweep, and what makes File 04's categorical-versus-individual cancellation contract enforceable.

### 6.3 Rule

- Every spawned process is placed in a process group at spawn time, by the platform's native grouping mechanism, so that the group can be signalled and killed as one. A process's own descendants join its group; the group, not the individual process identifier, is the durable categorical-kill target for the lifetime of the work.
- The ownership tree binds process groups to sandboxes and sandboxes to runs and child runs. Killing a run kills its child-run tree (File 04 §17.3); killing a child run kills its sandboxes; killing a sandbox kills its process groups; killing a process group kills its processes and their descendants. Each level is also individually killable without killing its parent.
- Categorical kill maps to the platform's group-kill primitive — a process-group signal, a job-object close, or a virtual-machine teardown — so the whole subtree dies in one operation even if the owning Atlas process panics. The committed realizations (§15) are a process-group leader and signal on Unix, a job object configured to kill its children when its handle closes on Windows, and a guest teardown for virtual machines.
- A bundled sidecar is a managed service process, not a private daemon. It declares an owner subsystem, `SandboxProfile`, loopback or network policy, start condition, health signal, restart policy, shutdown order, output policy, and kill relationship. A sidecar cannot outlive its owning process group unless ownership is explicitly transferred to another registered service owner. Restart and health behavior are event-driven where possible, bounded, configurable, and killable; Packaging owns the sidecar inventory and distribution, not the process lifecycle contract.
- A live process's confinement is fixed at spawn and is not retroactively tightened: its isolation tier, filesystem policy, network policy, and resource budget are immutable for its lifetime. When ownership of a live process transfers to a new owner (§3.3) whose confinement is narrower than the process was spawned under, the transfer never silently loosens the new owner's boundary — the runtime either re-gates the broader confinement through policy under the new owner's authority (`policy.approval-router`, File 06) or kills the process and requires a re-spawn under the narrower confinement. Confinement never widens by transfer.
- The kill targets this model exposes are exactly the cancellation targets File 10 enumerates (run, child run, sandbox, process, and the rest, `ledger.cancellation-lifecycle-restart`, File 10 §14). The user-facing process-management surface (File 10 §14) renders this ownership tree so the user can stop a whole cascade or a specific sandbox, process, or child run.

### 6.4 Boundary

This section owns the group and ownership-tree model and the categorical-kill mapping. File 04 owns the run and child-run cancellation relationships the tree binds to. File 10 owns the cancellation target taxonomy and the user-facing surface's events.

## 7. Filesystem Boundary Enforcement

Anchor: `sandbox.filesystem-enforcement`

### 7.1 Definition

Filesystem boundary enforcement is the mechanism that confines file access to an allowed region of the filesystem and rejects access outside it. It has two layers: the service-trait chokepoint that mediates Atlas's own file access, and the operating-system filesystem confinement that contains a spawned process whose file access the service trait does not mediate. The `FilesystemPolicy` is the closed declaration of the allowed region: `Isolated` (a private temporary root only), `WorkspaceOnly` (the workspace root and nothing else), `WorkspaceWithExtras` (the workspace root plus declared additional typed roots), or `Unrestricted` (the host filesystem, for user-trusted execution). Every allowed root declares its root kind, concrete resolved path, access mode, sensitivity, owner, and source expression from the capability/policy layer. A policy carries an explicit deny overlay that overrides allows. `Unrestricted` still enforces the deny overlay unconditionally: credential directories, key stores, vault files, and paths excluded by security policy are rejected even under `Unrestricted`. No filesystem policy permits access to explicitly denied paths; the deny overlay is structural, not an opt-out.

### 7.2 Purpose

One missed path check anywhere is a path-traversal vulnerability. Centralizing Atlas's own file access at a single service-trait chokepoint makes that guarantee structural — it is impossible to reach the operating system's file interface without passing the check — which is the rule File 22 §13.3 deferred here. But the service trait governs only Atlas-mediated access; a spawned subprocess reads and writes files directly, never through the trait. The operating-system filesystem confinement is what contains that subprocess. Both layers are required: the chokepoint for everything Atlas does itself, the kernel confinement for everything a sandboxed process does.

### 7.3 Rule

- **The service-trait chokepoint.** All Atlas-mediated file access flows through one filesystem service trait whose implementation validates every path before any operation. Validation canonicalizes the path (resolving `.`, `..`, and symbolic links to a real path), then verifies the canonical path lies within the sandbox's allowed region per the `FilesystemPolicy`, then applies the deny overlay. A path outside the allowed region returns a typed boundary error discriminated by which boundary it escaped: `PathOutsideWorkspace` when the violated region is a workspace-scoped policy's workspace root (`WorkspaceOnly`, or the workspace root of `WorkspaceWithExtras`), and `PathOutsideSandbox` when it is any other confined region (an `Isolated` private root, a `WorkspaceWithExtras` extra root, or the operating-system confinement boundary of a spawned process). A denied path returns `PathDenied`. No subsystem performs its own path validation; the invariant is structural at the trait boundary, not scattered across call sites (`security.local-posture`, File 22 §13.3).
- **Typed roots and access modes.** A filesystem allow is a machine-resolvable root declaration, not prose. Additional roots in `WorkspaceWithExtras` carry an access mode — read-only, read-write, create/staging-only where supported, or equivalent policy-defined modes — and the operating-system confinement must enforce the same access mode rather than merely including the path. Exact resource-expression grammar remains File 05/File 06's; this file enforces the resolved roots.
- **Symlink resolution before the check.** Symbolic links are resolved to their real target before the containment check, so a symlink inside the allowed region that points outside it does not bypass the boundary. This is the same rule perception applies before its capture boundary (`perception.capture-privacy`, File 19 §10).
- **Canonical mutation identity.** The canonical real path produced by validation is also the filesystem mutation identity consumed by the execution concurrency layer (`run.parallelism`, File 04 §15.2). Alias spellings of the same file — symlinks, relative components, workspace-relative versus absolute paths, and platform case-folding where applicable — share one identity, so a read-modify-write queue cannot be bypassed by spelling the path differently.
- **Operating-system filesystem confinement.** A sandbox at `OsConfined` or `Virtualized` tier confines its spawned processes' file access at the operating-system level — a filesystem namespace, a sandbox profile, or a virtual-machine boundary — so a process that never calls the service trait still cannot read or write outside the sandbox's `FilesystemPolicy`. The committed realizations are kernel filesystem confinement on Unix, a sandbox profile on macOS, restricted-token and directory confinement on Windows, and the guest filesystem of a virtual machine; all sit behind the policy. Where the platform cannot confine a process at the operating-system level, the runtime records the gap and the unenforced scope remains the contract (`capability.touched-resources`, File 05 §6.6).
- **Time-of-check-to-time-of-use.** The canonicalize-then-open sequence has an inherent race: a path validated as inside the region can be redirected by a concurrent symlink swap before it is opened. The realization closes this window where the platform supports it — by opening through the resolved real path with operating-system semantics that bind to the resolved target, or by re-validating at open — and where the platform's symbolic-link or junction semantics leave a residual window, the gap is declared and hardened, not silently assumed closed. The canonical contract is canonical-path containment; the realization is responsible for not letting a swap defeat it. The residual window is a declared, hardened gap, not an accepted permanent state: a deny-at-open closure of it is adopted if it ever becomes achievable without a correctness trade-off.
- **Reserved names, length, and control characters.** Validation rejects platform-reserved device names, paths exceeding the platform length limit, and paths bearing control characters, each with a typed error. A filesystem-boundary rejection is a security boundary, not a transient fault, and is non-retryable (`security.local-posture`, File 22 §13.4).
- **Atomic mutation.** A write that the sandbox commits is staged and atomically promoted (write to a temporary path in the same filesystem boundary, make durable, then rename over the destination), so a cancelled or failed write never leaves a partially-written destination (`run.streaming-partial-execution`, File 04 §12). Staged partials are deleted on cancellation before any promotion.

### 7.4 Boundary

This section owns both enforcement layers and the canonical-path-containment contract. File 20 owns the data-root and workspace-root layout the region is defined against (`storage.physical-layout-locality`, File 20 §8). File 24 owns the workspace and worktree directory identities. File 05 and File 06 own the declared and leased filesystem scope this enforcement realizes.

## 8. Network Policy Enforcement

Anchor: `sandbox.network-enforcement`

### 8.1 Definition

Network policy enforcement is the mechanism that confines a sandboxed unit's outbound network access to allowed destinations and blocks the rest. The `NetworkPolicy` is the closed declaration: `None` (no network), `LoopbackOnly` (local loopback and explicitly local IPC only, for sidecar communication), `AllowList` (only structured destination expressions approved by policy), or `Unrestricted` (any destination, subject still to the egress-destination policy and the per-destination gate). Like the filesystem boundary, enforcement has two layers: the application-layer destination check that mediates Atlas's own outbound requests, and the operating-system network confinement that contains a spawned process's own connections.

### 8.2 Purpose

A spawned process that fetches a hostile URL or exfiltrates data over a connection the application never saw bypasses any application-layer check. The operating-system network confinement is what contains it. The application-layer check is what enforces the egress-destination policy on Atlas's own requests, including per-hop redirect re-validation. Both layers are required, and both consume the egress policy File 22 owns rather than inventing a parallel one.

### 8.3 Rule

- **The application-layer destination check.** Every outbound request Atlas itself makes resolves its destination and checks it against the egress-destination policy (`security.egress-governance`, File 22 §11) before connecting. This file performs the check; File 22 classifies the destination and owns the allowlist, denylist, and the default-deny floor for credential and secret destinations. A destination the policy denies is blocked with a typed `NetworkDestinationBlocked` error; a destination requiring escalation routes to the gate.
- **Structured destination expressions.** An allowed network destination is machine-resolvable over protocol, host or domain pattern, port, IP or CIDR range, loopback/private/public class, DNS behavior, and redirect handling. DNS resolution and DNS egress are part of the network policy. If a platform cannot enforce a destination expression directly for a spawned process, the runtime uses a mediated proxy, denies network, or records the unenforced gap and re-gates through policy; it never treats host-only allowlists as complete enforcement.
- **Operating-system network confinement.** A sandbox confines its spawned processes' network access at the operating-system level per the `NetworkPolicy` — a network namespace with no default route, a loopback-only configuration, a filtering proxy, or the virtual-machine network boundary — so a process that opens its own connection cannot reach a destination the policy forbids. The committed realizations sit behind the policy; where the platform cannot confine a process's network at the operating-system level, the runtime records the gap and the declared scope remains the contract.
- **Per-hop redirect re-validation.** Where an outbound request can be redirected (a redirect chain, a destination supplied by untrusted content), each hop's destination is re-validated against the egress-destination policy, so an initially-allowed destination cannot redirect to a forbidden one (`security.untrusted-content`, File 22 §12.5). This is the exfiltration-via-redirect defense, enforced here.
- **`LoopbackOnly` for sidecars.** A bundled support process that communicates with the application over the local host is confined to `LoopbackOnly`: it may bind and serve on IPv4 loopback, IPv6 loopback, localhost aliases, or explicitly local IPC, and reach nothing external. Sidecar communication over the local loopback is the committed channel; a sidecar never receives broad network access by default.
- **No network as the safe default for confined execution.** A sandbox's default `NetworkPolicy` is the narrowest its consumer needs: `None` for code-execution and preview by default, widened only by explicit per-request or per-profile opt-in through policy. Network access is granted, never assumed.

### 8.4 Boundary

This section owns the network-enforcement mechanics and the two-layer model. File 22 owns the egress-destination classification, the allowlist and denylist, and the sensitivity tiers the destinations are gated against. File 06 owns the policy gate the escalation routes through. File 12 and the per-surface specs own the higher-level fetch and connector services that spawn requests through this enforcement.

## 9. Resource Isolation, Limits, and the Time-Guard Rule

Anchor: `sandbox.resource-limits`

### 9.1 Definition

`ResourceLimits` is the closed set of dimensions a sandbox bounds a unit's resource consumption along: maximum memory, maximum processor share (a core count, a percentage, or processor-seconds), maximum process count, maximum open file descriptors, maximum disk consumption, maximum captured-output size, and a wall-clock guard. Enforcement is event-driven: crossing a threshold raises a typed event and, for a hard limit, kills the unit. The captured-output cap is applied per stream — standard output and standard error are bounded independently — so a unit's worst-case captured output is at most twice the nominal cap, and a stream that crosses its cap kills the unit (§5.3, §9.3). The wall-clock guard is the one time-based dimension, and it is a safety guard, not a correctness condition.

### 9.2 Purpose

A confined process that exhausts memory, forks unbounded children, or emits gigabytes of output can take down the host as effectively as malicious code. Resource limits are what keep a confined unit's worst case bounded. Making them event-driven thresholds rather than timers keeps them honest under the project's rejection of time-based correctness conditions; making the one unavoidable timer an explicit, finite, configurable safety guard keeps it honest too.

### 9.3 Rule

- A sandbox enforces its `ResourceLimits` through the platform's resource-control mechanism — control groups, job-object limits, resource limits, or the virtual-machine's resource allocation — where available, and through best-effort monitoring and threshold-kill where not, recording the gap in the latter case. The maximum-process-count limit is one setting enforced defense-in-depth at both layers: the application layer counts the live `ManagedProcess`es in the `ProcessGroup`, and the control-group realization caps `pids.max` on the cgroup leaf that holds the group — the leaf, not a sandbox-wide aggregate — so a process that forks below the application-layer count cannot outrun the kernel bound.
- Resource and output limits are event-driven thresholds. The output byte cap is enforced as the captured output accumulates, and a process exceeding it is killed immediately rather than allowed to exhaust memory before any timer fires. A memory or process-count limit crossing raises a typed `ResourceLimitExceeded` event and kills the unit for a hard limit or warns for a soft one. No resource limit depends on elapsed time.
- The wall-clock guard is the sole time-based dimension and is governed strictly. It is a universal, finite, configurable, killable external-process safety net: it is the decisive stop only for a process that has no reliable completion signal (`run.budgets-limits`, File 04 §21; `run.cancellation`, File 04 §17.3), and otherwise a last-resort backstop that catches a signal-bearing process that hangs past every completion signal it should have raised. It is never a correctness condition: a legitimate long-running process must succeed under a generous guard rather than be cut off, the guard is settings-owned with a long-tolerance default, the model may raise it per call within a finite ceiling, and a timeout-less operation is not permitted. A wall-clock guard expiry escalates to the cooperative-then-forceful kill path (§10), never a silent kill.
- Resource budgets compose with File 04's run-level and per-stage budgets without duplicating them: File 04 owns the run's budget enforcement; this file owns the per-sandbox operating-system resource confinement. Every `SandboxProfile` declares visible safety floors for host-protection dimensions such as output size, process count, disk or temp growth, and wall-clock safety guard where no completion signal exists; memory and CPU limits are declared where the platform can enforce them. Untrusted or unknown sources require bounded profiles. The runtime never imposes a hidden resource ceiling where the consumer did not ask for one; profile defaults are settings-owned and visible.

### 9.4 Boundary

This section owns the per-sandbox resource confinement and the time-guard rule. File 04 owns the run-level and per-stage budgets. File 10 owns the resource event envelope. The threshold defaults are settings (§19).

## 10. Killability, Escalation, and Reaping

Anchor: `process.killability`

### 10.1 Definition

Killability is the contract that every Atlas-managed unit of execution is constructed with a categorical and individual stop path. It has three movements: cooperative stop (the unit is asked to stop and given a bounded chance to clean up), forceful escalation (the runtime uses the strongest platform termination primitive available when cooperative stop does not complete in time or when immediate stop is required), and reaping (the unit's resources are reclaimed, including orphans left by a process restart). This is the enforcement, over processes and sandboxes, of the cancellation contract File 04 §17.3 defines.

### 10.2 Purpose

File 01 §7.11 makes user control over long-running work non-negotiable, and File 04 §17.3 makes cancellation cooperative-first with forceful escalation. This file is where that becomes real over operating-system processes: a cooperative signal a process may honor, a forceful kill path, a group kill intended to leave no orphans, typed failure when the platform cannot complete termination, and a restart that reaps what a crash left behind.

### 10.3 Rule

- **Cooperative stop first.** On cancellation, a managed process receives the run's shared cancellation signal (`run.cancellation`, File 04 §17.3) and the platform's graceful-termination signal (a terminate signal on Unix, a control-break to its process group on Windows). The process is given until the cooperative-stop deadline — declared per capability, defaulting from settings with a long tolerance (§19; File 04 §27) — to stop cleanly, preserve committed outputs, discard staged partials, and exit.
- **Forceful escalation.** When the cooperative-stop deadline expires, or when policy requires immediate stop, the runtime forcefully terminates the unit: a kill signal to the process group on Unix, a forced tree-kill on Windows, a job-object close, or a virtual-machine teardown. Atlas-managed units are registered only through mechanisms that provide a forceful kill path. If the platform primitive fails, leaves a unit unreaped, or cannot prove teardown, the runtime records `KillFailed` with a typed reason, quarantines or marks the unit unsafe where possible, prevents silent continuation, and surfaces the failure to the user and policy layer. File 10 §14 reserves the `KillFailed` entry but defines no reason vocabulary; this file owns the closed reason set — `PermissionDenied` (the platform refused the signal, such as `EPERM` on macOS), `NoSuchProcess` (the target was already gone, such as `ESRCH` on Linux, which a concurrent reap or PID reuse can produce), `ReapRequired` (teardown could not be proven and the unit must be reaped at restart), `PlatformUnkillable` (no available primitive can force termination), and `Other { detail }` for a platform failure none of these name — carried on the entry as a `Custom` payload under the `process` namespace (§18).
- **Categorical and individual.** Both targets are first-class (§6): killing a sandbox kills its process groups and their descendants in one operation; killing one process leaves its siblings and parent running. The cancellation user surface offers both (`run.cancellation`, File 04 §17.3; File 10 §14).
- **Cleanup and partial side effects.** After a kill, the runtime performs the unit's declared post-kill cleanup — deleting staged partials, releasing handles, tearing down sandboxes and sessions — and records what cleanup ran, what partial side effects may remain, and whether the kill was cooperative, escalated, or forceful (`run.cancellation`, File 04 §17.3). A capability declares whether its partial output is meaningful and is retained or discarded accordingly.
- **Reaping at restart.** A managed process or sandbox is a transient runtime handle, not a durable identity (§14). On process restart, the runtime reaps orphaned processes, sandboxes, and process groups left by the prior run rather than reconnecting to them, transitioning the owning runs per File 04's orphan-run rules (`run.cancellation`, File 04 §17.3, `process_restart_orphan`) and per File 20's shutdown and reconstruction sequence (`storage.lifecycle-reconstruction`, File 20 §13.3). A capability that owns genuinely resumable infrastructure may declare `resume_on_restart` and provide a resume handler; the runtime calls it instead of reaping, and the handler revalidates and either resumes or fails with a typed reason.
- **Kill events.** Every kill writes the reserved kill and cleanup entries to File 10's ledger and bus — `KillRequested`, `KillSucceeded` or `KillFailed`, `CleanupCompleted`, and the cancellation completion entry (`ledger.cancellation-lifecycle-restart`, File 10 §14) — stamped with the `backend_id` of the affected sandbox or process. A kill is never silent.

### 10.4 Boundary

This section owns the process-and-sandbox enforcement of the cancellation contract. File 04 owns the contract, the cooperative-stop-deadline policy, the partial-output retention rule, and the orphan-run reconciliation. File 10 owns the kill entry catalogue and the user-facing cancellation surface's events. File 20 owns the shutdown sequence this kill participates in.

## 11. The Elevated Helper Process

Anchor: `sandbox.elevated-helper`

### 11.1 Definition

The elevated helper is a separate, minimal, least-privilege operating-system process that performs the narrow set of privileged operations the user authorizes, so that the main Atlas process never runs with elevated privileges. This section owns the helper's process model — its lifecycle, its inter-process channel, its versioned operation manifest, and its integrity. The pairing credential that authorizes the main process to drive it and the least-privilege principle behind it are File 22's (`security.device-trust`, File 22 §10.3).

### 11.2 Purpose

A long-lived elevated main process is a standing risk: every bug in it is a privileged bug. A separate, lazily-installed, one-shot-per-command helper with a versioned built-in operation manifest keeps the privileged surface as small and as auditable as a single process running a single named operation, and keeps the main process unprivileged.

### 11.3 Rule

- **The main process is never elevated.** Privileged operations — those requiring administrator or superuser rights — are performed only by the elevated helper, never by the main Atlas process. The helper is a separate per-platform binary in the read-only installation directory (`storage.physical-layout-locality`, File 20 §8).
- **Lazy installation.** The helper is installed only when the user first attempts a privileged operation, never at application install time, so an installation that never needs privilege never gains a privileged component. Uninstalling Atlas removes the helper; removing only the helper leaves Atlas in unprivileged mode.
- **One-shot per operation, preferred.** The helper prefers a one-shot model: spawn an elevated process, run a single authorized operation, capture its output, and exit, over a long-running elevated process. The committed elevation realizations are the platform's privilege-escalation facility — a privileged manifest and consent prompt on Windows, a privilege-authorizing facility on macOS, a policy-aware privilege tool on Linux — all behind the helper contract.
- **Versioned operation manifest over local inter-process communication.** The helper accepts only built-in, versioned operation ids with typed arguments, over a local inter-process channel (a local socket or named pipe), and rejects anything outside the manifest. It never accepts an arbitrary command string. The manifest is part of the trusted helper package, not user-, plugin-, model-, or settings-mutable runtime configuration; new privileged operations require installing an approved helper/package version. Only the paired main process may drive it (`security.device-trust`, File 22 §10.3); the pairing credential is vault-held or stored with least-privilege file permissions and is File 22's.
- **Integrity and audit.** The helper package manifest is a canonical integrity record (`core.canonical-hash`, File 01 §7.14) that names the helper executable as an `ExecutableArtifact` value with declared canonical encoding. The installed helper is trusted only when its materialized bytes and package signature or distribution evidence verify against that artifact record. A mismatch is a tamper signal that re-gates and blocks helper use until repaired or reinstalled. Every elevated operation writes to the device-local hash-chained audit overlay (`ledger.hash-chained-audit-log`, File 10 §16; `security.audit-crypto`, File 22 §14), which is never disabled.
- **Privilege is human-governed.** No agent, plugin, automation, or imported record drives the helper through ordinary capability paths; an elevated operation is an explicit, audited user action gated by the policy floor and typed confirmation File 06 and File 22 define (`core.extension-planes`, File 01 §6.14).

### 11.4 Boundary

This section owns the helper's process model, lifecycle, channel, operation manifest, and integrity. File 22 owns the pairing credential, the least-privilege principle, and the trust the helper's integrity verification composes with. File 06 owns the policy floor and typed-confirmation gate the elevated operations carry. The platform-specific elevation facilities are committed realizations behind the helper contract.

## 12. Subprocess Wrappers and Home Isolation

Anchor: `sandbox.subprocess-wrapper`

### 12.1 Definition

A subprocess wrapper is a long-lived or one-shot child process that wraps an external command-line tool — a command-line subscription wrapper for a model provider, an external agent runner, or a tool with no library interface — and communicates with it over its standard streams. Home isolation is the per-instance redirection of the home directory and the configuration and authentication state rooted there, so multiple accounts or instances of the same external tool do not collide. This section provides the lifecycle and isolation File 17 §26 delegates here.

### 12.2 Purpose

A command-line subscription wrapper that runs a model provider's tool, or several accounts of it, must not leak one account's authentication or configuration into another's, must not be killed by signalling the wrong process, and must inherit a controlled environment. Per-instance home isolation, process-group tracking, and the environment allowlist make multiple instances and accounts first-class without collision.

### 12.3 Rule

- A subprocess wrapper runs as a `ManagedProcess` in a `ProcessGroup` (§5, §6), confined by a `SandboxSpec` resolved from the adapter's typed runtime-environment context (the provider-adapter contract, File 17 §3). It is killable on the standard contract (§10), and cancelling its work terminates it cooperatively then forcefully.
- Home isolation is a sandbox facet: each instance receives a per-instance home directory through a home-directory override in its `EnvPolicy`, so its configuration, session, and authentication state are isolated from the user's real home and from other instances. Where an external tool's state must be seeded from the user's real home, the seeding copies or links the read-only inputs into the isolated home while keeping writes inside it; this file owns the isolation primitive (the per-instance home and environment), and the provider adapter owns the seeding policy.
- The environment a wrapper receives is the allowlist (§5.3): the environment variables that control paths, linkers, and interpreters are excluded, the home override is applied, and only the wrapper's required variables cross. A wrapper never receives the full parent environment except under explicit user-trusted interactive opt-in.
- Multiple wrappers and multiple accounts run in parallel; each is a distinct `ManagedProcess` with a distinct process group and home, demultiplexed by the `backend_id` envelope dimension (`ledger.event-envelope`, File 10 §5.2) so concurrent instances are individually observable, signallable, and killable (`run.explicit-rejections`, File 04 §28 — no single-instance lock on a backend).

### 12.4 Boundary

This section owns the subprocess-wrapper lifecycle and the home-isolation primitive. File 17 owns the wrapper's protocol, argument shaping, usage parsing, and the runtime-environment declaration. File 22 owns the credential the wrapper resolves and the secret boundary across its process boundary (§16).

## 13. Declared-versus-Observed Enforcement

Anchor: `sandbox.declared-vs-observed`

### 13.1 Definition

Declared-versus-observed enforcement is the runtime catching of a unit touching or attempting to touch a resource — a filesystem path, a network destination, a process, an environment variable — that lies outside the scope its capability declared or its lease granted, and the typed violation it emits. The declared scope is the capability's touched-resource expression resolved by the policy layer (`capability.touched-resources`, File 05 §6; `policy.touched-resource-matching-against-lease-scope`, File 06 §6). Runtime facts are separated into successful observed touches and denied attempted touches; this section is the runtime that compares them.

### 13.2 Purpose

A capability declares what it may touch, and the policy layer leases a scope, but neither can prevent a buggy or hostile unit from trying to touch more. The runtime sandbox is the last line: it confines the unit to the resolved scope at the operating-system level and emits a typed violation when the unit tries to escape, so the declaration is a checked contract rather than a promise (`capability.touched-resources`, File 05 §6.6).

### 13.3 Rule

- The runtime confines a unit to the filesystem region (§7), network destinations (§8), process group (§6), and environment (§5) the policy layer resolved for the call, and to the resource budget (§9). The resolved scope is the enforced boundary.
- An access that escapes the resolved or leased scope is caught and produces a typed violation in-band: `PathOutsideWorkspace` or `PathOutsideSandbox` for filesystem, `NetworkDestinationBlocked` for network, a process-scope violation for a process outside the group, an environment violation for a forbidden variable, `ResourceLimitExceeded` for a resource, and `SandboxEscapeAttempt` for an attempt to break the isolation boundary itself. The violation flows to the agent loop as ordinary execution input (`run.denial-is-in-band`, File 04 §8.3), and the runtime records it; policy may terminate the run for a high-risk violation.
- A declared scope the runtime cannot enforce at the operating-system level is still the contract. The runtime records that the scope is unenforced for the current platform, catches what it can at the application layer, and emits a typed violation on a detected escape; it never silently treats an unenforceable scope as enforced (`capability.touched-resources`, File 05 §6.6).
- The runtime records three resource views: the declared resources from capability policy, denied attempted resources from enforcement points, and successful observed resources after execution. Denied attempts are typed policy/security facts, sensitivity-filtered, and never merged into the successful-touch set.
- Observed and attempted resources are recorded for audit and provenance (`capability.touched-resources`, File 05 §6.5) so a run's actual filesystem, network, environment, and process footprint is reconstructable from the resolved-versus-observed comparison. Paths, hosts, process names, command fragments, and environment names are redacted or summarized according to sensitivity. Unexplained attempted touches may affect future policy and trust scoring without silently mutating the original capability declaration.

### 13.4 Boundary

This section owns the runtime enforcement and the typed violations. File 05 owns the declaration and the resource-class catalogue; File 06 owns the touched-resource matching and the lease scopes; this file enforces the resolved result and reports the observed footprint.

## 14. Observation, Handles, and Reconstruction

Anchor: `process.observation`

### 14.1 Definition

A `ProcessHandle` and a sandbox handle are transient runtime references through which a managed process or sandbox is observed, signalled, and killed; they are not durable identities and do not survive a process restart. A `ProcessSnapshot` and a `SandboxSnapshot` are `Observation` blocks (`artifact.observation`, File 09 §13) that record a point-in-time view of a process's or sandbox's state — its liveness, its resource usage, its exit status, its confined roots, and the identity evidence needed to detect reuse or restart — with a staleness fingerprint, committed when a capability run depends on that state for later revalidation.

### 14.2 Purpose

The world model reasons about processes and sandboxes as entities, capability runs revalidate against the state they observed, and the storage layer reconstructs the runtime after restart. Each needs a different fidelity: the world model needs live liveness, a capability needs a durable recorded snapshot it can revalidate against, and reconstruction needs to know that a handle is transient and an orphaned process must be reaped, not trusted. Separating the transient handle from the durable snapshot is what keeps replay honest and reconstruction safe.

### 14.3 Rule

- A process or sandbox handle is a transient runtime-handle projection (`storage.projection-store`, File 20 §7.3): it is rebuilt from live operating-system state, never stored as a durable identity, and is meaningless after restart. The world model's `Process` and `Sandbox` entities project their liveness from these handles (File 18 §4); their durable record is the snapshot observation and the ledger and audit entries, not the handle.
- When a capability's mutation depends on prior process or sandbox state — a server expected to be running on a port, a sandbox expected to hold a checked-out repository — the runtime commits a `ProcessSnapshot` or `SandboxSnapshot` `Observation` through the canonical `observation.commit` path (`artifact.observation`, File 09 §13; `artifact.consequences-for-later-specs`, File 09 §22), carrying the observation kind, the state-defining payload, and a staleness fingerprint. The snapshot includes the sandbox id, process group id, process id where applicable, platform creation time or start nonce where available, executable identity, owner run or capability, observed state, resource counters, and confined roots. The capability's later mutation revalidates currency against the recorded snapshot (`run.call-pipeline`, File 04 §8.2), detects PID reuse or sandbox restart before relying on the snapshot, and produces a typed state-changed error on a mismatch. When the identity evidence is insufficient to prove a reused process identifier is the same process — a recycled PID with no matching creation time or start nonce — the identity resolves as changed, never as a match: the runtime re-gates or kills and restarts, and never silently adopts the reused identifier as the original process.
- Live process and sandbox facts are `Ephemeral` (`world.durability-tiers`, File 18 §7): replay, audit, and historical reconstruction consume the recorded snapshot observations and the immutable ledger and audit entries, and re-derive nothing by re-spawning or re-querying a live process (`context.assembly-replay-snapshot`; `ledger.replay-semantics`, File 10 §11). A model-derived result computed over a snapshot is keyed and recorded, not recomputed at replay (`perception.output-contract`, File 19 §9).
- On restart, the runtime reaps orphaned processes, sandboxes, and process groups rather than reconnecting to their stale handles, transitioning the owning runs per File 04's orphan rules and File 20's reconstruction sequence (§10.3). A capability declaring resumable infrastructure is the only exception and revalidates before resuming.

### 14.4 Boundary

This section owns the transient-handle rule and the snapshot-observation production. File 09 owns the observation contract and provenance. File 18 owns the process and sandbox entities and their liveness model. File 20 owns the handle-projection rebuild and the reconstruction sequence.

## 15. Cross-Platform Realization

Anchor: `sandbox.cross-platform`

### 15.1 Definition

The cross-platform realization is the set of committed, per-platform operating-system mechanisms that implement the `Sandbox` contract, the process-group model, the filesystem and network confinement, the resource limits, the kill primitives, and the elevation facility, all behind the contracts the preceding sections define.

### 15.2 Purpose

The contract is platform-invariant; the mechanisms are not. Naming the committed realizations grounds the design and makes the per-platform differences explicit — what each platform can and cannot enforce — without freezing a mechanism as the semantic boundary or letting a missing mechanism on one platform break the contract on another.

### 15.3 Rule

- The per-platform mechanisms sit behind the contract and are selected at build and run time by the `SandboxRegistry` (§3.3). A platform that lacks a mechanism for a requested tier or policy resolves to `SandboxUnavailable` or records an unenforced-scope gap (§13.3); it never silently presents weaker isolation as the requested one.
- The committed realizations, named for grounding and replaceable behind the contract, are: kernel filesystem, syscall, and resource confinement and process-group signalling on Unix-family systems; sandbox profiles and resource limits on macOS; job objects, restricted tokens, process-group control, and tree-kill on Windows; and virtual machines, microvirtual-machines, and containerized environments for the `Virtualized` tier across platforms, each declaring whether the kernel boundary is shared or separate. The in-process bytecode runtimes realizing `RuntimeConfined` are only those whose host imports are mediated and revocable. Pseudo-terminals use each platform's native facility. None of these is the contract; each is one implementation of it.
- A capability or tool that exists only on platforms where its mechanism is available is registered only on those platforms and returns a typed unsupported-platform result elsewhere (`world.environment-temporal-connection-facts`, File 18 §6); it never appears as available on a platform that cannot enforce it.
- Behavior that is hardware- or display-server-dependent (a Linux input daemon requiring a kernel device, a compositor-specific rendering workaround) is detected at first use and surfaced to the user as a setup step, never assumed present; the dependent capability is disabled until the setup completes, and the independent capabilities continue.

### 15.4 Boundary

This section owns the per-platform realization and the registry's platform resolution. The platform integration, packaging, and bundling of the mechanisms and their dependencies are File 43's. The per-surface specs own the platform-specific capability mechanics (graphical input tiers, browser engines) that compose with this file's process and isolation primitives.

## 16. The Secret and Trust Boundary Across Processes

Anchor: `sandbox.secret-trust-boundary`

### 16.1 Definition

The secret and trust boundary across processes is the rule set governing what crosses from the trusted backend into a spawned process: which secrets, under what confinement, and at what trust. A sandboxed child process is a lower-trust process boundary than the backend that spawned it (`security.threat-model`, File 22 §3.3); this section owns how the secret boundary and the trust decision are honored across the spawn.

### 16.2 Purpose

A spawned process can leak whatever it is given. Confining what crosses the spawn — never raw secrets by default, only the minimum a capability needs, and only under the confinement the trust class requires — is what keeps a sandboxed process from becoming an exfiltration path for the credentials and data the backend holds.

### 16.3 Rule

- Raw secret material does not cross the spawn boundary by default. A sandboxed process is a lower-trust boundary across which raw `Secret` material never passes unless the capability explicitly requires it, the policy layer authorizes it, and the secret is resolved at the point of use inside the backend and injected under the narrowest confinement (`secret.backend-boundary`, File 22 §4). A secret injected into a process's environment or input is a deliberate, policy-gated, audited act, never a default inheritance; the environment allowlist (§5.3) excludes secret-bearing variables by default.
- When a secret must cross the spawn boundary, the injection channel is chosen for least exposure: a file descriptor, standard input, or a local socket is preferred over the process environment, because environment variables are readable by any same-user process and are inherited by descendant processes. Environment injection is a flagged last resort, used only when the target program accepts a secret no other way, and the injected variable is scoped to the single process and never inherited beyond it.
- The trust class of the source whose code runs in a sandbox selects the isolation tier (§4): untrusted and unverified sources run at the tier their trust class requires and never below it (`security.trust-model`, File 22 §9). The trust decision is File 22's; the tier selection it drives is enforced here.
- Output a sandboxed process emits is treated as untrusted content (`security.untrusted-content`, File 22 §12): it carries no authority, is scrubbed of detected secret material before it re-enters model context or persists (`security.secret-detection-redaction`, File 22 §7), and an instruction embedded in it is data, not a command.
- The elevated helper (§11) is the one boundary across which privilege rises, and it does so only for the narrow allowlisted operations the user authorized; no ordinary spawn raises privilege.

### 16.4 Boundary

This section owns how the secret and trust rules are honored across the spawn. File 22 owns the secret vault, the backend secret boundary, the trust classes, the secret detector, and the untrusted-content rule; this file consumes and enforces them at the process boundary.

## 17. Sandbox and Process Capability Surface

Anchor: `sandbox.capability-surface`

### 17.1 Definition

The execution-containment layer exposes canonical capabilities for spawning and killing processes, creating and tearing down sandboxes, signalling and inspecting processes, listing active sandboxes and process groups, and inspecting resource usage, declared and gated like every other capability.

### 17.2 Rule

- Canonical capabilities include: executing a command and spawning a background process (each producing a `ManagedProcess` in a `ProcessGroup`), checking and waiting on a job's status, signalling a process, listing the active processes and sandboxes, killing a process or a sandbox or a whole group, creating and tearing down a sandbox, and inspecting a sandbox's resource usage and confined roots. The process-spawning capabilities carry the permission tier their blast radius warrants — process execution defaults to `UserApproval` (`run.approval-during-execution`, File 04 §11), elevated operations carry the `permission_floor: Denied` plus typed-confirmation gate (`policy.permission-floor-typed-confirmation`, File 06 §7) — and a kill of a unit the current run did not spawn carries a stronger tier than a kill of one it owns.
- Each capability declares its touched resources, concurrency, reversibility, cooperative-stop deadline, and partial-output meaningfulness per File 05 and File 04; process spawning declares the `process` and, where applicable, `filesystem` and `network` resource classes so the policy layer resolves and the runtime enforces them (§13). The capabilities are surfaced per File 07 and cancellable per File 04.
- The user-facing process-management surface (`ledger.cancellation-lifecycle-restart`, File 10 §14) is realized from this capability surface and the observation handles (§14): the surface lists active process-like units — runs, child runs, sandboxes, processes, sessions — and lets the user stop a whole cascade or a specific unit. This file provides the data contracts; the UI specs render them.
- No capability bypasses the policy layer, the filesystem or network enforcement, the kill contract, or the audit overlay. Spawning a process, opening a sandbox, and driving the elevated helper are all capability calls through the standard pipeline (`run.call-pipeline`, File 04 §8.2); there is no privileged side door.

### 17.3 Boundary

This section names the capability surface. File 05 owns the declarations, File 06 the policy gating, File 07 the surfacing, File 04 the cancellation and concurrency, File 10 the events and the cancellation surface's entries. This file declares the execution-containment capabilities as canonical built-ins.

## 18. Events

Anchor: `sandbox.events`

### 18.1 Rule

- Process and sandbox events emit through File 10's canonical bus with the standard envelope and sensitivity (`ledger.event-stream`, File 10 §5), stamped with the `backend_id` dimension that demultiplexes concurrent sandbox and process instances and the `worktree_id` dimension where the unit runs in an isolated worktree (`ledger.event-envelope`, File 10 §5.2). Process spawn and exit, sandbox creation and teardown, resource-limit crossings, filesystem and network violations, and cleanup outcomes flow through this bus.
- Cancellation and kill events use the entries File 10 already reserves (`CancellationRequested`, `KillRequested`, `KillSucceeded`, `KillFailed`, `CleanupCompleted`, `CancellationCompleted`, `ledger.cancellation-lifecycle-restart`, File 10 §14); each references the affected unit's identity. Sandbox- and process-specific facts that File 10 does not already define are registered as named `Custom { namespace, name, payload }` kinds under the `sandbox` and `process` namespaces, declaring their payload schema, retention class, sensitivity, and ledger participation at registration (File 10 §4.3).
- Live event emission and durable recording are distinct (`core.durable-history-transient-coordination`, File 01 §7.3): live process and sandbox liveness is `Ephemeral` and coordinates; the durable record is the snapshot observation (§14), the ledger entries, and the audit-overlay entries for elevated operations (§11). Events that touch `Secret` content carry the corresponding sensitivity and never include raw secret material (`secret.backend-boundary`, File 22 §4).

### 18.2 Boundary

This section names the event behavior. File 10 owns the envelope, the delivery classes, the sensitivity, the cancellation entries, and the custom-event registration. This file emits through that shared mechanism.

## 19. Settings

Anchor: `sandbox.settings`

### 19.1 Rule

Every execution-containment mechanism with meaningful variation is configurable through File 15 settings, with namespaced keys (`sandbox.*`, `process.*`) declaring scope, agent exposure, and locality. Dimensions include:

- the default `SandboxProfile` per consumer class (shell, code-execution, preview, custom-tool runtime, graphical control, managed browser, subprocess wrapper, sidecar): its isolation tier, filesystem policy, network policy, resource limits, and environment policy
- the environment-variable allowlist and exceptional host-environment mode for spawned processes (composed with the security and shell allowlists, not a parallel store)
- resource safety floors, resource-limit defaults per profile, and the output byte cap
- cooperative-stop deadlines per capability and category default, and the cancellation surface's default kill target (composed with File 04 §27, not duplicated)
- the wall-clock guard defaults and ceilings (finite, long-tolerance, never a correctness condition)
- the network policy default per consumer (narrowest by default) and the per-profile network opt-in
- the per-platform isolation-mechanism selection where the platform offers more than one, and the registry's tier-resolution strictness
- the elevated-helper enablement, lazy-install behavior, and trusted helper-operation manifest version
- per-instance home-isolation behavior for subprocess wrappers
- sidecar lifecycle defaults: owner, sandbox profile, health signal, restart policy, shutdown order, output policy, and ownership transfer rules

Specific defaults belong to tested settings profiles, not hardcoded constants (`settings.settings-over-constants`, File 15 §13). Agent exposure of execution-containment settings is conservative: the elevated-helper configuration, the environment allowlist, and the isolation floors are `Hidden` or `OnRequest` from the agent; the isolation floors a trust class requires are not lowerable by an agent. No execution-containment behavior is a hidden hardcoded branch where a meaningful variation exists.

### 19.2 Boundary

This section names the dimensions. File 15 owns the cascade, storage, and agent-exposure enforcement; File 04 owns the cancellation-deadline settings these compose with; File 22 owns the security settings these compose with. This file declares the execution-containment settings through that shared mechanism.

## 20. Explicit Rejections

Anchor: `sandbox.explicit-rejections`

The following shapes are wrong for this layer:

- a second sandbox abstraction, a per-surface private sandbox, or a per-consumer re-implementation of filesystem confinement, resource limits, or process kill — there is one `Sandbox` contract with per-consumer profiles and per-surface capability extensions
- a process spawned outside the managed-process model, an untracked process, or a process that is not a member of a process group — every spawned process is tracked and killable both individually and as part of its group
- an intentionally non-killable unit of execution, a sandbox whose teardown leaves its processes running, or a forceful-kill failure treated as success — every Atlas-managed unit is killable by construction, killing a sandbox targets everything it owns, and platform kill failures are typed, surfaced, and quarantined where possible
- a single shell-interpreted command string built from agent-supplied fragments and handed to a shell, or shell/interpreter command text spawned without registered inspection — a process is spawned with an explicit program and argument vector; a shell is invoked only as an explicit program and its payload is inspected before spawn
- filesystem-boundary validation scattered across call sites, a path check that omits symlink resolution before the containment check, or a sandboxed process whose own file access is unconfined at the operating-system level — path validation is structural at one service-trait chokepoint and the operating-system filesystem confinement contains spawned processes
- a network destination reached from a sandboxed process outside the network policy, an outbound request that skips the egress-destination check, or a redirect chain that is validated only at the first hop — the network boundary is enforced at the application layer and the operating-system level, and every redirect hop is re-validated
- a blocklist of forbidden command names treated as the safety boundary, or an environment-variable blocklist instead of an allowlist — command safety comes from the permission tier, machine-readable command inspection, the environment allowlist, and user guardrail hooks; the path/linker/interpreter environment variables are excluded by default
- a time-based condition treated as a correctness mechanism, or a timeout-less long-running process — wall-clock guards are finite, configurable, killable external-process safety guards: decisive only where no completion signal exists, otherwise a last-resort backstop for a signal-bearing process that hangs past its signal (§9.3); resource and output limits are event-driven thresholds
- a resource limit imposed silently by default where the consumer did not ask for one, an unbounded profile for untrusted execution, or a resource limit that depends on elapsed time — safety floors are visible profile settings, stricter limits are settings-owned, and enforcement is event-driven
- the main process running elevated, a long-lived elevated process where a one-shot helper suffices, an elevated helper accepting an arbitrary command string, a helper operation added by plugin/settings/model code, or a helper installed at application-install time rather than lazily on first privileged use — privilege is confined to a separate, least-privilege, lazily-installed helper with a versioned built-in operation manifest
- a sandboxed process inheriting raw secret material by default, a secret injected into a process without policy authorization, or a sandboxed process's output treated as trusted or authoritative — the secret boundary and the no-authority-from-untrusted-content rule hold across the spawn
- a process or sandbox handle treated as a durable identity, an orphaned process reconnected to rather than reaped at restart, or a live process re-spawned or re-queried during replay — handles are transient projections, orphans are reaped, and replay consumes recorded snapshot observations
- presentational separation (window cloaking, virtual-desktop placement) presented as a security isolation tier, or untrusted code run below the isolation tier its trust class requires
- a declared touched-resource scope silently treated as enforced on a platform that cannot enforce it — an unenforceable scope is recorded as a gap, caught at the application layer, and surfaced as a typed violation on escape
- a build-only platform check that presents a capability as available on a platform whose mechanism cannot enforce it, or a hardware- or display-dependent capability assumed present rather than detected and set up
- a sandbox, process, or kill operation that bypasses the policy layer, the filesystem or network enforcement, the cancellation contract, or the audit overlay

## 21. Consequences for Later Specs

Anchor: `sandbox.consequences-for-later-specs`

Every later spec that spawns a process, confines execution, enforces a filesystem or network boundary, kills a unit, or crosses the privilege boundary consumes this layer as defined here.

- File 24 owns the workspace and worktree directory identities and lifecycle; it materializes them within the filesystem region this file confines, and a worktree directory is one filesystem boundary this file enforces, never a private path that bypasses the boundary.
- The **per-surface specs** (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) run all confined execution through this file's `Sandbox` contract: a shell command, a code-execution call, a preview process, a managed browser, a graphical-control session, and a device operation each declare a `SandboxProfile` and spawn `ManagedProcess`es in `ProcessGroup`s. They extend the base contract with their capability surface (graphical input and observation, browser navigation, language runtimes) and never redefine the lifecycle, the filesystem or network enforcement, or the kill semantics. Graphical-control presentational isolation (virtual desktops, window cloaking) is a presentation facet, not a security tier; untrusted code runs at the `Virtualized` tier with a separate-kernel realization when policy requires a kernel boundary.
- The **Automation and Triggers** spec (File 33) spawns non-interactive work through this file's managed-process substrate under least authority, confines it to the narrowest sandbox, resolves credentials at point of use without injecting raw secrets into the spawned process, and kills it on the standard contract; an automation never spawns an untracked or non-killable process and never escalates privilege without the user.
- The **Extension and Plugin System** (File 35) and **MCP and External Integrations** (File 36) specs run plugin and connector code, and command-line subscription wrappers, through this file's sandbox and subprocess-wrapper lifecycle: a plugin's code runs at the isolation tier its trust class requires, an MCP server subprocess is a `ManagedProcess` in a `ProcessGroup` reaped on shutdown, and a subscription wrapper uses per-instance home isolation and the environment allowlist.
- The **Telemetry, Logging, and Observability** spec (File 41) consumes the process and sandbox events and snapshots this file emits as data, never re-spawns or re-queries a live process for a historical view, and renders the process-management surface from the observation handles and the cancellation entries.
- The **Runtime Infrastructure and Lifecycle** spec (File 42) owns the broader application lifecycle around this file's process and sandbox startup and shutdown participation; it invokes the kill and reap contract at shutdown (`storage.lifecycle-reconstruction`, File 20 §13.3) and does not reimplement process spawning, confinement, or killability.
- The **Evaluation and Benchmarking** spec (File 40) verifies the filesystem boundary (no path escapes the confined region, including via symlink), the network boundary (no destination outside the policy, including via redirect and DNS), the resource limits (a runaway process is bounded and killed), the killability contract (every unit is killable categorically and individually, kill failures are typed, no orphans survive restart), the isolation-tier selection (untrusted code never runs below its required tier), the elevated-helper boundary (the main process never elevates, the helper accepts only its versioned manifest operations), and the secret boundary across the spawn; it replays over recorded snapshot observations and immutable entries, not live process state.
- Every later spec that introduces a process, a sandbox, a filesystem or network boundary, a resource limit, a kill target, or a privileged operation declares it against this file's `Sandbox` contract, managed-process model, enforcement, kill contract, and elevated-helper boundary, and obeys the one-containment-substrate, killable-by-construction, structural-filesystem-and-network-enforcement, least-authority-isolation, no-time-based-correctness, never-elevated-main-process, and secret-boundary-across-the-spawn rules this file fixes.

## 22. Canonical Rule Anchors

Anchor: `sandbox.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `sandbox.chosen-model`, `sandbox.boundaries-with-adjacent-layers`, `sandbox.contract`, `sandbox.isolation-tiers`, `process.spawning`, `process.groups`, `sandbox.filesystem-enforcement`, `sandbox.network-enforcement`, `sandbox.resource-limits`, `process.killability`, `sandbox.elevated-helper`, `sandbox.subprocess-wrapper`, `sandbox.declared-vs-observed`, `process.observation`, `sandbox.cross-platform`, `sandbox.secret-trust-boundary`, `sandbox.capability-surface`, `sandbox.events`, and `sandbox.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
