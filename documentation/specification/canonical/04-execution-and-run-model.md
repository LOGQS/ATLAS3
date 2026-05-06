# Execution and Run Model

## Status

Canonical.

## Scope

This file defines:

- `Run` as the durable execution attempt
- execution entry from `RunIntent`
- execution lifecycle
- execution structure
- model, programmatic, workflow, domain, and multi-agent execution shapes
- capability/tool execution semantics
- tool-surface management
- approval and denial handling during execution
- parallelism and child runs
- task promotion and task updates during execution
- mid-execution reroute mechanics
- interruption, cancellation, retry, and recovery
- budgets, ledger, events, outputs, and version commit boundaries

This file does not define:

- full task schema
- full capability contract schema
- policy and approval UI
- exact tool schemas
- context assembly algorithm
- compaction policy
- provider failover internals
- storage schema
- model/provider registry schema
- domain-specific tool catalogs
- frontend layout behavior

## Source Resolution

This file is a resolved design, not a summary.

Primary source families reviewed:

- `documentation/specification/canonical/01-core-thesis-invariants-and-primitives.md`
- `documentation/specification/canonical/02-conversation-intent-and-task.md`
- `documentation/specification/canonical/03-routing-and-dispatch.md`
- `documentation/sources/atlas3-project-knowledge/atlas3-core/*`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit01-foundations-and-cross-cutting-core.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit03-conversation-engine.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit04-routing-agents-prompt.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit05-providers.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit06-tools.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit07-context.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit11c-system-agent.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit12-infrastructure.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit14-systems.md`
- `documentation/sources/atlas3-specbase/references/agents/*`
- `documentation/sources/atlas3-specbase/references/conversation/*`
- `documentation/sources/atlas3-specbase/references/cross-cutting/*`
- `documentation/sources/atlas3-specbase/references/context/*`
- `documentation/sources/atlas3-specbase/references/tools/*`
- `documentation/sources/atlas3-specbase/references/providers/*`
- `documentation/sources/atlas3-specbase/references/systems/*`
- `documentation/sources/atlas3-specbase/references/domains/*`
- `documentation/sources/atlas3-project-knowledge/compressed-repos/*`
- `documentation/sources/atlas3-project-knowledge/addendums/*`
- `documentation/sources/existing_ecosystems/*`
- `documentation/sources/codex_recommendations.md`

Resolution rule:

- preserve the durable run envelope
- preserve concrete execution mechanics where they are load-bearing
- reject any wording that collapses execution into one linear loop, one chat transcript, one task graph, or one frontend presentation

Resolved tensions:

- keep the old chat DAG insight, but do not make chat chronology the execution root
- keep the agent loop, but define it as one execution shape, not the whole architecture
- keep hierarchical task-graph power, but specify behavior before exact storage shape
- keep programmatic agents, but do not split them into a separate backend architecture
- keep parallelism, but require explicit ownership, isolation, and merge rules
- keep fast path, but record router-owned work as execution, not invisible preprocessing
- keep approval hooks, but place policy mechanics in the capability and policy specs
- keep task promotion, but require explicit capability invocation rather than router heuristics

## 1. Chosen Model

This file defines what happens after routing produces a `RunIntent`.

Execution consumes routing, context assembly, model strategy, capability registry, capability policy, blocks, artifacts, versioning, settings, and typed errors. It does not replace those systems. Its responsibility is to create or resume the run, orchestrate work, record what happened, expose live state, and commit accepted outputs through the correct durable primitives.

Execution centers on `Run`.

`Run` is the durable record of one bounded attempt to progress work. It may answer a simple chat request, perform tool-using work, execute a workflow, run a domain runtime, or coordinate multiple child runs.

The chosen execution model is:

- routing produces `RunIntent`
- execution creates or resumes a `Run`
- the run executes a structured set of steps
- every consequential action passes through capability contracts and policy
- outputs become messages, blocks, artifacts, claims, memory proposals, task updates, or workflow candidates
- the execution ledger records what happened
- the event stream projects live state to the UI and hooks

This makes execution inspectable and reusable without forcing ordinary chat into heavy task ceremony.

## 2. Run

### 2.1 Definition

`Run` is a durable execution attempt.

It is not:

- a message
- a task
- a conversation
- a frontend mode
- a raw tool call
- a raw model response
- a DAG by definition

It may attach to all of them.

### 2.2 Required Attachments

Every run must attach to:

- one conversation
- one primary intent thread
- one trigger
- one route result or equivalent non-chat trigger decision

A run may also attach to:

- a task
- parent run
- child runs
- produced artifacts
- evidence and claims
- approvals and leases
- workspace or world state snapshots

### 2.3 Trigger Kinds

Allowed trigger kinds:

- user request
- retry
- edited request reroute
- continuation
- child run
- automation
- external event
- user-invoked action

All trigger kinds use the same run model. Background execution is not a separate architecture.

### 2.4 Run Status

Required statuses:

- `pending`: created but not started
- `running`: actively executing
- `awaiting_user`: waiting for approval, clarification, or intervention
- `paused`: intentionally suspended and resumable
- `cancelling`: cancellation requested but cleanup is not complete
- `cancelled`: stopped by user or policy before completion
- `failed`: ended without satisfying the execution contract
- `completed`: ended with accepted outputs
- `superseded`: replaced by edit, reroute, retry, or branch

Status changes must be ledgered.

### 2.5 Ownership

Run ownership is set at creation.

The primary conversation, primary intent thread, and trigger do not change during the run. If execution needs a different work line or route, it creates a child, continuation, branch, or superseding run rather than mutating ownership in place.

### 2.6 Minimum Durable Reconstruction

A run record must preserve enough durable information to reconstruct:

- stable run identity
- conversation, intent thread, task, parent, and child relationships
- trigger and route linkage
- status, stop reason, and ordering of creation and completion
- policy, capability, model, settings, and world-state snapshot references used by the attempt
- produced output references
- approval, denial, lease, interruption, reroute, and cancellation facts
- `control` of the run (default `Assistant`; set to `User` during explicit user takeover, with the user's actions during the takeover recorded as first-class blocks attached to the run)

Run `control` answers "who is producing the run's next blocks" and is orthogonal to task ownership: ownership names the responsible work-line owner at the task level, while control names the present driver at the run level. Control is not a gate on the user. The user may act through any external surface (their own editor, terminal, browser) at any time without first taking control; the field tracks what the system knows is producing observable blocks, not what the user is permitted to do.

Exact storage fields belong in the storage spec. This file requires reconstructability, not a final database schema.

## 3. From `RunIntent` to Run

Execution consumes `RunIntent`.

The handoff must preserve:

- triggering message
- selected intent thread
- attachment kind
- primary and supporting surfaces
- capability families
- execution entry
- model route
- tool-surface strategy, if present
- fast-path results or failures
- routing explanation
- user overrides

Fast-path work belongs to the run record. If the router performed a capability call before downstream execution, the created run must include that work as an initial execution record or attached preparation record.

No fast-path result may be treated as invisible context.

## 4. Execution Entry

`RunIntent.execution_entry` selects the initial execution shape. It does not create a separate backend architecture.

Entry types:

- `respond_inline`: produce a direct response, usually one model step or deterministic answer.
- `respond_with_tools`: use the standard model/tool loop when tools may be useful.
- `domain_runtime`: enter a surface-specific runtime while still using shared execution semantics.
- `multi_step_agent`: execute a persistent multi-step structure until completion, pause, failure, or user intervention.

All entries share:

- run lifecycle
- ledger
- event stream
- capability policy
- model strategy
- context compilation
- cancellation and retry semantics

## 5. Execution Structure

### 5.1 Principle

A run has an execution structure.

The structure may be as small as one model response or as rich as a hierarchical graph of deterministic steps, model steps, capability calls, validations, and child runs.

The canonical requirement is not a specific graph schema. The canonical requirement is that execution is decomposable, inspectable, resumable, and safely parallelizable.

### 5.2 Execution Unit

An execution unit is any bounded part of a run that can be tracked independently.

Common unit kinds:

- deterministic step
- model step
- model/tool loop iteration
- capability proposal
- capability execution
- retrieval step
- context compilation step
- validation step
- recovery step
- user-ask step
- artifact commit step
- child run

Each unit must have:

- goal or purpose
- inputs
- outputs or explicit no-output result
- status
- owning run
- ordering relationship
- error state, if any

### 5.3 Structure Shapes

Allowed execution shapes:

- inline response
- model-with-tools loop
- deterministic orchestration with model steps where needed
- graph or workflow execution
- domain runtime execution
- multi-agent parent run with child runs
- automation run using a saved execution template

These shapes share the same run lifecycle and ledger.

## 6. Lifecycle

The standard lifecycle is:

1. Create or resume run.
2. Attach route, trigger, conversation, intent thread, and optional task.
3. Snapshot relevant world, settings, policy, capability, and model state.
4. Build the minimal execution structure needed for the request.
5. Compile context or deterministic inputs for the next schedulable units.
6. Execute schedulable units subject to policy, capability, and concurrency rules.
7. Record observations, partials, outputs, errors, approvals, and validations.
8. Commit accepted outputs to durable objects.
9. Update projections for UI, search, task state, artifacts, and observability.
10. Decide whether to continue, pause, ask, branch, retry, reroute, fail, or complete.

Planning is not a mandatory phase. Plans are artifacts, task updates, or execution units only when they improve the work.

### 6.1 No Mandatory Phases

Execution does not have required planning, execution, verification, or reflection phases.

Those behaviors may happen when useful, but they are expressed as ordinary execution units, model steps, capability calls, task updates, artifacts, or validation results. A simple run must not pay phase machinery cost, and a complex run must not be forced into a fixed phase sequence.

## 7. Model/Tool Loop

### 7.1 Role

The model/tool loop is the default shape for ordinary agentic work.

It is not the only execution shape.

### 7.2 Iteration

A loop iteration proceeds logically as:

1. Compile context for the current run and execution unit.
2. Call the selected model with available tools and instructions.
3. Parse output into typed response, tool calls, reasoning, and partial blocks.
4. Execute proposed tool calls through the capability pipeline.
5. Return tool results, denials, failures, and observations to the model context.
6. Stop if no more tool calls are needed or a termination condition applies.

Context is compiled for each model iteration, not only at run start. The context compiler decides how to handle overflow; execution observes the result and continues, pauses, recovers, or fails according to typed outcomes.

Model output may stream through the event stream during generation. Streaming is live projection; accepted blocks, artifacts, and commits still follow the normal capability, ledger, and version rules.

### 7.3 Stop Conditions

A loop may stop when:

- no tool calls are proposed
- an explicit finish capability is invoked
- the run is cancelled
- the run is paused or awaits user input
- a configured budget is reached
- an unrecoverable typed error occurs
- the run reroutes or is superseded

## 8. Capability Execution

### 8.1 Rule

All side effects must pass through capability contracts and policy.

This applies equally to:

- user-triggered actions
- model-triggered tool calls
- workflow nodes
- child runs
- automation runs
- system actions

### 8.2 Call Pipeline

A capability execution must follow this logical pipeline:

1. Resolve capability.
2. Validate input.
3. Produce proposal if the action can mutate state or cross a policy boundary.
4. Run validators and policy checks.
5. Determine denial, approval need, persisted decision, or active lease.
6. Execute with the declared isolation and concurrency semantics.
7. Stream partials when supported.
8. Record observations and result.
9. Validate postconditions when declared.
10. Commit or expose output according to capability semantics.

"Active lease" in step 5 refers to the `Lease` object defined in §11; the pipeline consults active leases before falling back to ad-hoc approval.

Every capability declares minimum execution-relevant metadata beyond input/output schemas:

- `concurrency` (§15.2): one of `ConcurrencySafe`, `SelfParallel`, `Exclusive`.
- `reversibility_class`: one of `none` (cannot be reversed), `compensable` (a paired or related capability undoes the effect — file edits reversed via the version graph; staged commits reversed via `git restore`), or `reversible` (the capability owns a symmetric reverse operation invokable directly).
- `idempotent`: whether calling the capability twice with the same arguments has the same observable effect as calling it once. Idempotency is independent of reversibility class — `set_value(key, x)` is idempotent regardless of whether it is `compensable` or `none`. The runtime uses idempotency to drive safe retry on unknown-outcome timeouts, to enable coalescing of duplicate concurrent calls (§15.4), and to inform recovery strategy choice (§20).
- `preview_mode`: one of `none`, `dry_run` (the capability can execute against simulated state and return a typed result describing what would happen — examples: `--dry-run` shell commands, simulated package install, automation deploy plans), `structural_preview` (the capability can return a structured description of the change without executing — parsed AST of an edit, planned subprocess pipeline, planned API request), or `diff_preview` (the capability can return a diff between current and post-execution state — file edits, DOM mutations, database row changes).
- `partial_output_meaningful` (§17.3), `cooperative_stop_deadline_ms` (§17.3), `sibling_abort_on_failure` (§15.3), and `resume_on_restart` (§17.3) where applicable.

These declarations may be deterministic (the capability author classifies once at registration) or model-mediated per call where deterministic classification is impossible. A `shell.exec` capability cannot declare a single `reversibility_class` for all bash commands: the runtime supports a model-mediated classification mode where a designated model classifies the specific call against the configured policy prompt before the pipeline proceeds. The classification mode is a setting per capability or capability family, not hardcoded.

A capability whose mutation depends on prior observation should validate observation currency before mutating. The pattern: the prior observation captures state-defining metadata (file mtime and content hash, DOM tree fingerprint, screen element id and bounds, browser session cookie state); the mutating call carries `expected_*` fields the capability checks against current state; a mismatch returns a typed `StateChangedSinceObservation` error rather than silently overwriting. The agent loop receives the typed error in-band and may re-observe and retry, branch, or stop. This is a capability-author responsibility; the executor enforces nothing additional.

The exact contract fields and approval UI belong in later capability and policy specs.

Blocking hooks and validators may participate at proposal, pre-execution, and pre-commit boundaries. They are part of the shared event/capability system, not a separate execution pipeline.

### 8.3 Denial Is In-Band

A denied capability call does not crash the run by default.

The executor records a denial result linked to the proposal. The model or programmatic executor sees the denial as normal execution input and may ask the user, choose a different path, narrow scope, or stop.

Policy may still terminate the run immediately for high-risk cases.

## 9. Tool Calls

Tool calls are one form of capability invocation.

The executor must support:

- native provider tool calls
- parsed text-pattern tool calls when the provider lacks native tools
- user-invoked actions
- borrowed or deferred capability loading
- partial tool blocks
- failed tool results as first-class model context

The response parser may vary by provider. The execution pipeline after parsing must not vary.

A capability handling input variants internally (a file-read capability dispatching between text and binary paths based on the resolved file kind) is the same capability with sub-modes; this is not a separate capability call. Variant handling, default-value selection, and progressive-fallback behavior all live inside the capability and pass through one validation, one approval, and one ledger entry.

Cross-capability composition happens at a higher layer: the model may emit one or more direct tool calls, and programmatic execution (§14) may chain capability calls deterministically — passing the output of one call as input to the next within a single execution unit — without forcing the model to emit each call as a separate model turn.

## 10. Tool Surface

### 10.1 Definition

Each run has a tool surface: the capability subset visible to the executing model or programmatic unit.

The tool surface is a prompt and availability strategy, not a security boundary. Policy still governs every call.

### 10.2 Zones

The tool surface has three zones:

- `primary`: full schemas available immediately
- `borrowable`: names and short descriptions visible; full schema loaded only after borrow
- `deferred`: not visible until explicitly loaded by route, user setting, or capability discovery

Borrowed tools are scoped to the current run turn or execution unit unless a later capability spec grants a wider scope.

The zone model defines execution semantics, not a fixed product policy. Users must be able to customize which tools or capability groups appear in each zone, including aggressive policies such as always-loaded primary tools and conservative policies such as mostly-deferred loading.

### 10.3 Routing Influence

If `RunIntent` includes a tool-surface strategy, execution respects it:

- `use_current_surface_tools`: standard primary surface
- `borrow_foreign_capabilities`: expand the borrowable set
- `load_deferred_capabilities`: load specified deferred groups before execution

When absent, execution uses the active surface defaults and settings.

Routing is not the only entry point for capability loading. Deferred capabilities may be discovered and loaded mid-execution by the model itself, through canonical built-in capabilities — `tool.borrow` for already-named borrowable tools whose schemas need to be loaded, and `tool.search` or `mcp.search` for discovering deferred capabilities by name, family, or description. Discovery and borrow are themselves capability calls and pass through the full pipeline (§8); newly loaded tools become part of the run's tool surface for the rest of the turn or for the duration of the granting lease, whichever is longer.

The default surface composition follows the active model's context budget. When all primary plus borrowable tools fit, they may be fully loaded; under context pressure, the runtime auto-shrinks to selective loading and surfaces the trade-off to the user through the settings UI (with concrete recommendations) rather than silently dropping tools. Domain runtimes load their domain-scoped tools by default within the domain; capabilities outside the domain are reachable only through `tool.search` or `tool.borrow`, never through silent autoload — this keeps the active prompt focused while preserving full reachability.

### 10.4 User Customization

Tool-surface behavior must be deeply customizable through settings.

Users must be able to inspect available tools in grouped form, such as by domain, capability family, risk class, integration source, or other useful categories. The settings UI may present these groups as collapsible views, but the canonical requirement is grouped inspectability and fine-grained control.

At minimum, users must be able to configure:

- whether broad capability families are primary, borrowable, or deferred by default
- whether individual tools are primary, borrowable, deferred, or disabled from prompt exposure
- whether all tools are always loaded, selectively loaded, or loaded only on demand
- per-surface, per-profile, per-workspace, per-chat, and per-run overrides where meaningful
- whether routing may expand or preload tools automatically
- whether the model may borrow foreign tools automatically or only from explicitly allowed sets

The best default should remain disciplined and efficient, but the system must not hardcode one tool-loading policy when users want a different one.

## 11. Approval During Execution

Execution uses the shared capability policy system. There is no agent-specific approval mechanism.

Capabilities declare a permission tier. The canonical tiers are `Denied`, `ReadOnly`, `WorkspaceWrite`, `UserApproval`, `Unrestricted`. `Denied` means the capability cannot be auto-approved by any lease; the only path to execution is `typed-confirmation` (below) or an equivalent policy-defined override path. Tiers compose with leases: a lease can lower friction within a tier (a `UserApproval` capability with an `AlwaysAllow` lease for the granted scope runs without prompting) but cannot escalate above the capability's declared tier or below `Denied`. The capability's permission tier and reversibility class (§8.2) together drive the default approval policy template.

Approval behavior must support:

- immediate allow
- immediate deny
- ask user
- typed-confirmation: a variant of "ask user" that requires the user to type a specific confirmation string (the action's identifier, the exact path, the branch name) before the call proceeds. Used for irreversible high-blast-radius operations (force push to a protected branch, account deletion, bulk filesystem delete). Typed-confirmation is not lifted by global trust toggles; it always asks.
- persisted approval as a `Lease`. A lease has scope, duration, revocation conditions, inherited constraints, and a recorded grant reason. A trivial persisted approval is a degenerate lease with full-capability scope, indefinite duration, and no constraints. A lease's scope is one of: `single-proposal` (no lease created — one-shot decision recorded as a policy event), `run`, `task`, `workspace`, `chat`, `global`, or `reusable-policy-rule` (a user-authored approval template applied as policy). Inherited constraints may narrow a lease to a path subtree, host set, or session set; revocation conditions may include manual revoke, workspace switch, policy change, or grant-context loss.
- model-mediated policy evaluation, including the named `auto-decide` mode, where a designated model classifies each proposed call against a configured policy prompt and returns allow, deny, ask user, or escalate.
- policy-driven escalation
- batched approval for multiple pending calls

When several approval-required calls are pending in the same scope (the same run, the same child run, the same simultaneously dispatched batch), the policy layer presents them as one batch where possible. The user can approve or deny each item independently, or accept the batch as a whole. Subsequently dispatched calls in the same scope start a fresh batch; calls in different scopes batch separately.

Persisted decisions are policy records, not hidden execution state.

Model-mediated policy evaluation means the policy layer may use a designated model to interpret a configured approval policy template and classify a proposed action as allow, deny, ask user, or escalate. This is still part of the shared capability policy system: the model evaluates against policy, audit rules, and configured constraints rather than inventing approval behavior ad hoc.

The system must support built-in approval policy templates as well as user-provided custom templates. A template may define how the policy evaluator reasons about risk classes, touched resources, reversibility, scope, prior approvals, workspace boundaries, or other approval-relevant context. Tier overrides, lease grants, modes, and templates compose across the scope hierarchy (single-proposal, run, task, workspace, chat, global, reusable-policy-rule). Policy validation must reject contradictory combinations across scope levels rather than resolving them silently — for example, a chat-level deny under a global-level lease must surface as a contradiction, not as a silent denial of the lease.

Model-mediated policy evaluation must not silently replace explicit user approval where policy still requires a human decision. It decides how the policy should classify the proposal; it does not erase the distinction between system-approved and user-approved actions.

## 12. Streaming and Partial Execution

Execution may stream:

- model text deltas
- reasoning summaries where allowed
- tool-input streaming: the model is still emitting a tool call's structured arguments; the UI may render them live (a `Reading src/index.ts...` indicator while the path argument is still being generated)
- tool-output partials: the executing capability is emitting partial results (streaming text, growing diff, growing file content)
- file or artifact previews
- command output
- validation progress
- child-run progress

Tool-input streaming and tool-output partials commit at different boundaries: the input stream commits when the model finishes the call and the executor enters the capability pipeline; the output stream commits at the capability's declared commit point.

Partial streaming is live projection. A durable mutation is accepted only at the capability's commit point.

For file or artifact writes, partial rendering must preserve atomicity:

- validate target before writing
- write into temporary or staged materialization
- commit only when the full call completes and passes policy/postconditions
- delete or orphan staged partials on cancellation according to block/version rules

Capabilities whose input is itself a content payload (full-replace file create or edit, document generation) may support live partial-write: as the model emits the input, the capability writes it incrementally into the staged temporary file, the user sees the content appearing live in the destination pane, and the atomic rename happens only when the call completes and passes policy and postconditions; cancellation deletes the staged file before any rename. The pattern preserves end-to-end atomicity (no destructive change to the live target until commit), gives the user immediate feedback, and never leaks partial corruption regardless of where the call fails.

## 13. Model Steps

Model steps are execution units, not the whole execution model.

A model step may:

- produce final text
- request tool calls
- update or propose a plan
- request clarification
- request reroute
- summarize state
- validate or critique output
- delegate to child runs when allowed

The runtime owns orchestration, policy, retries, concurrency, persistence, and merge semantics.

Models own semantic judgment, synthesis, open-ended planning, extraction, and natural-language interaction.

## 14. Programmatic Execution

Programmatic execution is first-class.

It means deterministic orchestration controls the run structure and calls model steps only where judgment or generation is needed.

Programmatic execution may yield:

- capability calls
- child-run requests
- model-step requests
- validation requests
- recovery requests
- finish signals

Use it for:

- known workflows
- context pruning
- batch retrieval and aggregation
- validation chains
- multi-agent coordination
- repeated transformations
- automation templates

Programmatic execution must still use the same run, ledger, capability, policy, and artifact rules.

## 15. Parallelism

### 15.1 Rule

Parallelism is allowed when ownership and merge semantics are explicit.

Parallel units may run only when:

- their required capabilities are compatible
- their mutable resource scopes do not conflict
- their policy leases allow it
- their outputs have a defined merge or comparison path
- cancellation and failure behavior are defined

### 15.2 Tool-Level Concurrency

Capabilities must declare enough concurrency metadata for the executor to know whether calls can run together. The canonical concurrency tag is one of:

- `ConcurrencySafe` — safe to run concurrently with any unrelated call.
- `SelfParallel` — safe to run multiple instances of the same capability concurrently, with the executor enforcing that the resource scopes of those instances are disjoint.
- `Exclusive` — runs alone within its declared resource scope.

The default for newly declared capabilities is `Exclusive`. The executor must detect when two `Exclusive` calls have disjoint resource scopes and is permitted to schedule them in parallel; the tag declares the pessimistic case, the executor refines it. Backends, sessions, processes, and external services must not be implicit single-instance locks: parallel runs and parallel calls against the same provider are first-class and must be addressable through the event envelope (§23.2).

The executor must preserve stable result ordering even when work finishes out of order.

### 15.3 Failure in Parallel Work

Parallel failure must preserve useful work unless policy requires immediate abort.

Default behavior:

- in-flight sibling units continue running when one unit fails; their results are retained on completion. This preserves useful work in independent batches.
- failed units produce typed error outputs.
- downstream units that require failed outputs are skipped or blocked.
- retry can target failed units, failed units plus downstream, or the whole structure.

Capabilities can opt into sibling abort by declaring `sibling_abort_on_failure: true`. When set, the executor cancels in-flight siblings on first failure within the same batch — used for first-wins-races, best-of-N selectors with early termination, and tightly coupled coordinated batches. Parallel batches may also declare per-call `depends_on` relationships at dispatch time; when a dependency fails, the dependent units are skipped or blocked, matching the existing downstream-on-failure rule. Both the per-capability declaration and the per-call dependency are user-customizable.

Silent absence is forbidden.

### 15.4 Mutation Rule

Concurrent mutation of the same resource is forbidden unless a capability explicitly owns a safe merge protocol.

When safe merge is unavailable, execution must choose one of:

- serialize the work
- isolate the work in separate branches, worktrees, documents, sessions, or artifacts
- ask for user direction
- fail before mutation

Silent last-write-wins behavior is forbidden.

For `SelfParallel` read capabilities and idempotent reads with deterministic results, coalescing concurrent identical calls is a recommended optimization: instead of dispatching N parallel identical calls, dispatch one and broadcast the result to all N callers. The capability declares a key function that derives a canonical request hash; the runtime maintains an in-flight table keyed by that hash. Coalescing is not a correctness requirement — capabilities whose surface arguments mask semantic distinctions (timestamp-changing URLs, session state, live tickers) opt out explicitly. Coalescing policy is fully customizable: users may override globally, per capability, per scope, or enable a model-mediated `auto-mode` where a designated model decides per call whether the cached result is acceptable or whether the call must execute fresh.

## 16. Child Runs and Multi-Agent Work

### 16.1 Definition

A child run is a run created by another run.

Child runs are used for:

- subagents
- parallel research branches
- independent coding worktrees
- isolated browser tasks
- validator or critic passes
- comparison runs (best-of-N with a selector child run, arena-style ranked rounds, tournament-style pairwise comparison)
- delegated domain execution

### 16.2 Isolation

Each child run must declare:

- parent run
- purpose
- allowed capability scope
- context-sharing policy
- output contract
- merge target
- cancellation relationship to parent
- lifecycle visibility

Context sharing must be explicit. A child run does not receive unrestricted parent context by default.

The canonical isolation primitives for child runs are filesystem-or-resource-level copies that share the underlying object store, image, or kernel: git worktrees for code-touching work; isolated browser profiles for browser work; sandboxed VM instances or virtual desktops for GUI control work; isolated process groups for shell work. The runtime selects the primitive based on the child run's declared capability scope and the parent's host environment. Isolation is contextual, not always preferable: when child runs share a workspace non-destructively (a single codebase the user is also editing, a browser session that must preserve human-verification cookies, parallel non-interfering observations), running without isolation is the right choice and the runtime must permit it. The isolation decision is a per-child-run policy; defaults follow the capability scope, and users may override per task, per surface, or per call.

### 16.3 Isolated and Inline Work

`isolated` child work gets its own context policy, tool surface, budget, and output contract.

`inline` work is allowed only when it is better modeled as a nested execution unit inside the parent run. If it can independently pause, fail, retry, or own tools, it should be a child run instead.

Inline work must not bypass policy, ledgering, or version boundaries.

An inline child run's mutations land in the parent's pending-operations buffer (§23.4) and commit at the parent's version-commit boundary. An isolated child run does not contribute to the parent's pending buffer; its work is captured as a single tool result block (or a sequence of blocks) returned to the parent under the declared output contract. The parent's incorporation step (§16.4) decides whether to apply that returned work to its own buffer, branch on it, or discard it.

### 16.4 Merge

Child run outputs do not automatically mutate parent state.

They must return through one of:

- summary
- artifact
- patch
- evidence set
- validation report
- proposed task update
- proposed workflow step

The parent run decides how to incorporate the output according to the declared merge target.

## 17. Interruption, Pause, and Cancellation

### 17.1 User Intervention

The user may intervene during execution.

Intervention is a run input, not an out-of-band chat hack. It must be recorded and may cause:

- continuation with new instruction
- pause
- cancellation
- branch
- reroute
- approval grant or denial
- scope narrowing
- explicit takeover of the run's surface (the run's `control` field flips to `User`)

When the user takes over the run's surface, subsequent user actions are recorded as first-class blocks attached to the run, indistinguishable in the ledger from agent-produced blocks. When control returns to the agent, the system offers (does not require) a summary input: the user may describe what they did or skip. The next agent iteration receives whatever summary the user supplied alongside any observable filesystem or workspace deltas the runtime detected; either, both, or neither may be present, and no agent flow blocks on this input.

External changes the user makes outside the run's observation surface (an edit in their own editor, a command in their own terminal, a workspace modification through any other surface) are not required to be tracked exhaustively. The runtime records what it can observe through registered watchers, version-graph deltas, and capability-mediated reads; capabilities whose mutation depends on prior observation revalidate currency before mutating (§8.2). The agent treats its last-known state as potentially stale, not as ground truth. This is a resilience property, not a synchronization system.

### 17.2 Pause and Resume

A paused run must preserve enough state to resume safely or explain why it cannot resume.

Resumption must revalidate:

- world state freshness
- capability availability
- policy leases
- resource locks or scopes
- model route validity
- user-visible assumptions

### 17.3 Cancellation

Cancellation must support both cooperative stop and forceful termination.

Each active run must have a shared cancellation signal. All registered listeners (the model/tool loop, child runs per declared relationship, active capability calls, sandbox/process operations, and other long-running execution units) receive the cancellation signal simultaneously and respond cooperatively. The parent run stays in `cancelling` until all listeners acknowledge completion or the cooperative-stop deadline expires; on deadline expiry, the runtime escalates to forceful termination of the remaining listeners and transitions the run to `cancelled`. Listeners that report completion after the run is `cancelled` produce typed orphan-output ledger entries; their outputs are not committed.

The default path is cooperative cancellation. Long-running capabilities must check the signal at safe cancellation points when possible. They should stop cleanly, preserve committed outputs, discard or orphan staged partials according to capability semantics, and report a typed cancellation outcome.

That is not sufficient as the only cancellation model. Nearly every Atlas-managed long-running unit should be killable both categorically and individually.

Categorical control includes, for example:

- cancelling a run together with its child-run tree
- killing a sandbox together with processes or sessions owned by it
- aborting an automation, workflow branch, or browser-control session as one target

Individual control includes, for example:

- cancelling one child run without killing the whole parent run
- killing one specific sandbox
- stopping one specific tool call or spawned process
- cutting off one provider stream or remote operation when supported

Capabilities must declare enough cancellation semantics for the runtime and UI to know:

- whether the action is cooperatively stoppable
- whether it is forcefully killable
- what cleanup or rollback may still happen after kill
- what partial side effects may remain after kill
- the cooperative-stop deadline before forceful escalation
- whether partial outputs are meaningful (`partial_output_meaningful: bool`)
- whether the capability owns resumable infrastructure (`resume_on_restart: bool`)

The system should prefer clean cooperative stop first when that is fast enough for safety and user control. It must escalate to forceful termination when immediate stop is required or when cooperative stop fails to complete promptly enough for the active policy.

The cooperative-stop deadline is declared per capability. If undeclared, the runtime uses a configurable default (§27 settings: cancellation default deadlines). Defaults must be set with long tolerance — a legitimate long-running command (a 24-hour build, a slow shell pipeline on weak hardware) must succeed under the default rather than be cut off — but every cancellation path must carry a finite deadline. The model may override the deadline per call (raising it for a specific operation when the default would be too short), but every override must itself remain finite; timeoutless operations are not permitted. The cancellation UI surfaces the deadline as a countdown so the user can intervene before forceful escalation.

Cancellation choices are user-customizable. The cancel UI must offer at minimum: cancel the run alone, cancel the run and its child-run tree, cancel a specific tool call without cancelling the run, cancel a specific child run without cancelling siblings or the parent, and cancel a specific sandbox or process. The default action of the cancel button is configurable; its expanded menu surfaces the rest. Every active long-running unit owned by the runtime must be wrappable into one of these targets and reliably cancellable.

Non-killable execution is an explicit exception. If a process or operation cannot be killed, later specs must identify that limitation explicitly and define fallback control behavior.

Cancellation must record:

- requester
- affected run and child runs
- cleanup performed
- whether cancellation was cooperative, escalated, or forceful
- partial outputs retained or discarded
- final status

Each capability declares whether its partial output is meaningful. When `partial_output_meaningful` is `true`, partial outputs produced before cancellation are kept by default; when `false`, partial outputs are discarded. If the capability does not declare, the runtime defaults to keep-on-cooperative-stop and discard-on-forceful-kill. The user can override the default per cancellation through the cancellation UI; the user's choice is recorded in the ledger.

Runs that were `running` or `cancelling` at process restart become `failed` with typed reason `process_restart_orphan` by default; their resources (worktrees, sandboxes, child processes, leases) are reaped according to each capability's declared post-kill cleanup. The runtime preserves the run's saved state across restart — most agentic progress lives in durable storage, so failure-on-restart loses work-in-flight, not committed work. Capabilities that own genuinely resumable infrastructure (long-lived browser sessions, scheduled tasks, durable workflows) may declare `resume_on_restart: true` and provide a resume handler; the runtime calls the handler instead of marking the run failed. The handler must revalidate world state, re-acquire leases, and either continue execution or transition the run to `failed` with a more specific typed reason. Runs that fail-on-restart must be surfaced to the user with a per-run resume-or-discard affordance — the runtime must not auto-resume orphaned runs at startup, but the user must be able to retry or resume any one of them on demand.

## 18. Task Promotion and Task Updates

Task promotion happens through explicit capability invocation.

Execution may create or update a task when the work benefits from explicit structure, including:

- multi-step progress tracking
- durable artifact ownership
- automation potential
- approvals tied to a goal
- pause/resume continuity
- success criteria and validation

Task promotion is not:

- automatic router behavior
- required for ordinary chat
- a hidden heuristic

Task updates must be revision-safe. A task update carries the revision it was based on and fails or branches if the task changed concurrently.

## 19. Retry, Reroute, and Branch

Retry, reroute, and branch must not interfere with a prior in-flight run. The default is to leave the prior run executing in parallel while creating the new run as a linked parallel attempt; both remain accessible as distinct versions. This behavior is configurable at the general and per-action level — users may instead require cancellation of the prior run, prompting, or other resolutions. Explicit cancellation is always available as a separate action regardless of this setting.

### 19.1 Retry

A retry creates a new run or execution branch linked to the prior attempt.

It must not mutate the historical ledger of the prior run.

Retry may reuse:

- same route
- same task
- same inputs
- same artifacts
- same policy snapshot

Retry may change:

- model route
- capability implementation
- context compilation
- recovery strategy
- user-provided instruction

### 19.2 Reroute

Mid-execution reroute is allowed when current execution lacks the right surface, model route, capability family, policy scope, or domain runtime.

Reroute happens at a safe boundary:

- after the current model output is parsed
- after current capability calls reach safe commit, cancellation, or staged state
- before new mutation begins under the new route

If accepted, execution must choose one:

- suspend and hand off
- create a child or continuation run
- branch
- supersede current run

If rejected, the rejection is returned in-band to the current run.

The new run receives the reroute reason and prior run link. It does not inherit in-flight context state implicitly.

### 19.3 Branch

Branching is required when two plausible execution paths should be preserved rather than overwritten.

Branching applies to:

- tasks
- conversations
- artifacts
- workflows
- child run strategies

## 20. Error Handling, Recovery, and Stuck Detection

### 20.1 Boundary Rule

Execution coordinates errors; it does not absorb every subsystem's internal policy.

Provider retries, rate-limit fallback, and model failover belong to the model strategy and provider layers. Execution receives either a model response or a typed provider failure and records the outcome.

Context overflow is not an execution-layer compaction trigger. Context assembly reports overflow or degraded assembly; context management decides whether to compact, adjust budget, ask the user, or return a typed failure. Execution then retries the affected unit or follows the recovery path.

Execution may signal observed context pressure to the context layer through a typed boundary (e.g., a `ContextPressureObserved { used_pct, kind }` event), but the choice of context strategy — which compaction policy to run, whether to summarize or paginate — stays in the context layer. Execution recovers by retrying the affected unit after the context layer responds.

Capability failures produce typed result objects whenever the run can continue. The active model or programmatic executor receives the failure as execution input and may recover, ask, branch, or stop.

Budget exhaustion preserves partial outputs. Before a non-fatal hard stop, execution should surface a typed budget-warning input to the active model or deterministic unit so it can summarize, request extension, or hand off useful partial work.

### 20.2 Recovery

Recovery is first-class execution behavior.

Required recovery strategies:

- retry same unit with corrected input
- expose error to model as context
- switch model profile
- switch capability implementation
- narrow capability scope
- revoke stale leases and reacquire with narrower scope (when a long-lived lease's grant context — workspace, file subtree, network host set — has changed, revoke the lease, narrow the new request, and re-prompt for grant)
- request user clarification
- branch strategy
- restore or propose rollback of materialized output
- stop with typed failure

### 20.3 Stuck Detection

The runtime must detect obvious stuck states, including:

- repeated identical tool calls without progress
- repeated failed validations
- repeated provider/tool errors
- no new durable output after configured iteration limits (including single-iteration empty responses where the model produced neither tool calls nor committable text — these escalate per the soft-warning rule below)
- child runs waiting on each other cyclically
- ping-pong between repeated tool/action patterns

Stuck detection must escalate in-band before hard-stopping. On detection, the executor first injects a typed warning into the active model or programmatic unit's context — the model can self-correct, narrow scope, or stop. Repeated detection within the same run escalates: the warning becomes a structured directive, then a hard stop with typed failure. The number of warnings before hard escalation, the warning text templates, and per-pattern overrides (some patterns escalate immediately because the model cannot resolve them in-band — cyclic child waiting, for instance) are all settings, not hardcoded constants.

The runtime may also use a model-mediated stuck detector as an opt-in option, where a designated model evaluates the stuck signal and decides whether to continue, warn, or stop. This carries an extra model call and is off by default; users may enable it globally or per pattern when the higher cost is justified by the lower false-positive rate.

## 21. Budgets and Limits

Runs must support configurable budgets.

Budget dimensions:

- maximum model steps
- maximum tool or capability calls
- maximum child-run depth
- maximum concurrent units
- context budget
- output budget
- provider budget
- artifact or resource budget

Elapsed-time guards may be used only as external-process safety guards when no reliable completion signal exists. They are not correctness conditions and must be configurable.

Programmatic execution and graph or workflow execution may compose per-stage budgets within a single run. A research pipeline declares a thinking budget, an acting budget, and a final-response budget; a multi-stage research pipeline declares per-stage budgets. When configured, the runtime enforces both the per-stage and the run-level budgets; the per-stage warning fires before the per-stage limit, and the run-level warning fires before the run-level limit (the soft-warning escalation rule from §20.3 applies to both). Budgets are not enforced by default — provider rate limits and model-internal stop conditions are sufficient for ordinary work — and the runtime must not silently impose hidden budget limits. Users opt into per-run and per-stage enforcement when they want it, at the granularity they want it (per turn, per task, per domain, per workspace, globally).

Before a non-fatal budget limit is reached, execution should emit a budget warning through the ledger/event/context path appropriate to the active unit. The warning must be visible to the model or programmatic executor before wrap-up is expected.

## 22. Termination

A run may terminate because:

- it produced the requested answer
- task success criteria were satisfied
- user cancelled
- policy blocked
- required capability was unavailable
- validation failed unrecoverably
- configured budget was reached
- execution was superseded by edit, retry, or reroute

A successful completion requires accepted output and:

- any postconditions declared on the executed capabilities have been validated and recorded in the ledger;
- the run has at least one ledger entry beyond the model's textual claim of success when the run contract required action (a forgery guard — a run with no recorded capability executions, no committed artifact revisions, and no model-step outputs beyond plain text cannot terminate as `completed` if its contract required action).

A fluent assistant response is not sufficient when the run contract required artifact mutation, validation, approval, or evidence capture.

These checks are deterministic and impose no extra model call. Beyond them, a configurable completion-verification hook surface (§23.3) is available for users who want stronger semantic checks on whether a run satisfied the user's request. The hook surface accepts both deterministic checks (capability postconditions, structured output validators, evidence-set comparators) and model-mediated checks (a designated model evaluating whether the run's outputs meet a per-task expected outcome). It runs at user-configured cadence (every N model steps, in parallel as a background observer, sequentially before completion, or only at explicit `verify_now` invocations) and supports per-task, per-surface, and per-profile configuration. Default ships disabled — the deterministic forgery guard above is the canonical termination floor; the hook surface is the opt-in extension for users who want richer verification at the cost of additional checks or model calls.

## 23. Ledger, Events, and Commits

### 23.1 Execution Ledger

The execution ledger is the durable source of consequential execution history.

It records:

- run creation and status changes
- route attachment
- execution unit starts and finishes
- capability proposals
- approvals, denials, leases, and policy decisions
- model calls, including provider, model identifier, role (router, responder, critic, validator, and so on), prompt tokens, completion tokens, cache creation tokens, cache read tokens, and cost estimate (per-call cost is computed from per-model pricing, not stored as an unkeyed scalar — cf. File 01 §8 invariant)
- tool calls and tool results
- observations
- validation results
- errors and recovery decisions
- produced outputs
- child run relationships
- cancellation and intervention

The list above is a minimum, not an exhaustive schema. The ledger must record full-granularity timestamps on every entry and any additional execution-relevant attribution the storage spec requires (request ids, trace context, attempt counters, classification metadata) without forcing the canonical to enumerate exhaustively. The storage spec extends the schema; this file specifies the minimum that execution reasoning depends on.

The ledger enforces a forgery guard at status transition: a transition from `running` to `completed` is rejected if the run has no recorded capability executions, no committed artifact revisions, and no model-step outputs beyond plain text — when the run contract required action. The forgery guard is the storage-side counterpart to §22's run-completion contract.

### 23.2 Event Stream

The event stream is the live projection channel.

It drives:

- streaming UI
- hooks
- inspectors
- progress views
- approvals
- validators
- logs

Every event carries an envelope with at least: `chat_id`, `step_id` (which execution unit produced the event), `node_id` (which DAG node, if applicable), `worktree_id` (for parallel worktrees, §16), `backend_id` (which concrete service instance produced the event — required so that parallel runs against the same provider, sandbox, browser, or other backend can be demultiplexed back to the correct handle), `sequence` (per-stream monotonic), `timestamp`, and `sensitivity` (`Public`, `Sensitive`, or `Secret`; default `Public`). Sensitive events are excluded from shareable chat exports and copy-to-clipboard operations on the event log and are stored under shorter retention. Capabilities tag at emit time — a generic `shell.exec` event is `Public`, but the same call against a credentials path is `Sensitive`. Secret payloads in flight (raw credentials, unredacted secrets) must never be persisted to the durable ledger.

Events may be transient. Consequential events must also be represented in the ledger.

### 23.3 Hook Integration

The event stream is also the execution hook surface.

Blocking hooks may run at safe boundaries such as capability proposal, iteration start, context assembly result, and version commit. They return one of four typed decisions:

- `Continue` — proceed with the original payload.
- `Substitute { new_payload }` — proceed with a hook-modified payload (a guardrail rewrites a path; a transformer normalizes arguments).
- `Block { reason }` — abort the proposed action; the executor records a denial and the typed reason flows in-band as a tool result.
- `RedirectSuggestion { tool_id, args, reason }` — abort the proposed action and signal that the agent should retry using the suggested tool. The agent loop consumes this as a typed retry signal.

Multiple blocking hooks can subscribe to the same boundary. Each subscription declares a `priority: i16`. Lower priority runs first. The convention is: audit and logging hooks at `-100` (capture pre-validation state); transformers and validators at `0` (default); the approval router at `+100` (sees post-validation payload last). The executor evaluates blocking hooks in priority order; the first non-`Continue` decision wins.

Each blocking hook subscription declares a `timeout_ms`. If the hook does not return a decision within `timeout_ms`, the executor synthesizes a default decision and records the timeout in the ledger. The default decision and the equivalent default on hook error follow the hook's declared authority:

- hooks that can return `Block`, `Substitute`, or `RedirectSuggestion` default-on-timeout and default-on-error to `Block { reason: "hook timeout" }` or `Block { reason: "hook error" }` (fail-closed). A hung or broken security hook must not let dangerous proposals through.
- hooks that can only return `Continue` (declared observers) default-on-timeout and default-on-error to `Continue` (fail-open). A hung observer must not block execution it has no authority to block.

Defaults are per-hook category, not a single global value: quality-control validators are typically tighter (hundreds of milliseconds) and logging or background hooks are looser. All defaults and per-hook overrides are settings, and per-error-class behavior is configurable — for example, a hook that fails because of a known transient cause (provider rate limit, transient network error) may be configured to retry within the timeout rather than fail closed immediately.

Non-blocking hooks may observe model streaming, capability execution, status changes, iteration completion, validation results, and produced outputs. They must not control execution flow.

Quality control validators, logging, plugin hooks, user hooks, policy gates, and the completion-verification hook surface (§22) integrate through this shared mechanism. They must not create a second hidden execution path.

### 23.4 Version Commits

Version commits are meaningful history boundaries, not every ledger event.

Typical commit boundaries:

- user message
- accepted agent turn
- accepted artifact revision
- accepted task revision
- retry branch
- edit branch
- context edit
- import/export operation

During a turn-like run, pending block and artifact operations accumulate in a pending-operations buffer. The accepted boundary commits that buffer as one durable net change. Tool-level checkpoints may exist inside that boundary without becoming separate version commits; rejecting a checkpoint updates the pending buffer before commit.

The ledger explains how a commit was produced. The version graph records the accepted durable state.

## 24. Output Semantics

Runs may produce:

- conversation messages
- blocks
- artifact versions
- file materializations
- patches
- claims
- evidence links
- memory proposals
- task revisions
- workflow candidates
- validation reports
- execution summaries

Important outputs should become artifacts or typed durable objects. Transcript text may describe or cite them, but should not be their only identity.

Large outputs should be stored as referenced artifacts or blobs, not forced into the transcript or model context.

## 25. Presentation

Execution presentation is a projection.

The same run may be shown as:

- a normal chat answer
- compact progress summary
- expandable timeline
- workspace activity
- multi-agent board
- artifact diff
- workflow graph
- observability trace

Changing presentation does not change backend execution semantics.

The UI must be able to show:

- current run status
- active execution unit
- pending approvals or questions
- selected model route when relevant
- capability calls and results
- child runs
- produced artifacts
- failure and recovery path

## 26. Automation and Reuse

Successful runs should be eligible for reuse.

The runtime may propose:

- workflow template
- automation
- custom capability wrapper
- validation recipe
- prompt fragment
- retrieval recipe
- document or artifact template

Promotion to automation must preserve:

- trigger shape
- required inputs
- capability scope
- policy requirements
- validation requirements
- output contract
- failure handling

Automation uses the same run model when executed.

## 27. Settings

Execution behavior must be configurable through settings.

At minimum, settings must support:

- default and per-surface run budgets
- model-step limits
- tool/capability concurrency caps
- tool-surface policy selection
- grouped and per-tool zone overrides
- always-load, selective-load, and on-demand-load policies
- child-run depth limit
- reroute enablement
- programmatic execution availability
- tool borrowing and deferred loading behavior
- budget warning thresholds
- stuck detection thresholds
- partial-output retention behavior
- approval persistence scopes
- approval mode selection
- approval policy template selection
- custom approval policy templates and per-scope overrides
- prior-run resolution policy for retry, reroute, and branch, with a general default and per-action overrides
- permission tier resolution and `Denied`-tier override paths, including `typed-confirmation` selection per capability or capability family
- lease scope hierarchy enablement (single-proposal, run, task, workspace, chat, global, reusable-policy-rule) and the policy-validation rules that reject contradictory combinations across scope levels
- approval-policy mode selection, including model-mediated `auto-decide` and per-template prompts
- coalescing policy (off, recommended, auto-mode model-mediated) per capability or globally, including per-call cache-vs-fresh control
- sibling-abort and `depends_on` dispatch behavior per capability and per batch
- per-capability and category-default cancellation deadlines, partial-output retention overrides, and resume-on-restart enablement, plus the cancel UI's default action and expanded-menu options
- stuck detection thresholds (per pattern), in-band soft-warning escalation rules, and opt-in model-mediated stuck detection
- per-stage and per-run budget composition (off by default), warning thresholds, and granularity (per turn, per task, per domain, per workspace, global)
- completion-verification hook surface configuration: enablement, deterministic-versus-model-mediated mode, cadence (every N steps, parallel/background, sequential, on demand), and per-task expected-outcome shape
- hook subscription configuration: priority, timeout, fail-direction overrides per hook category and per error class
- event sensitivity classification overrides per capability or capability family
- ledger-record retention granularity and additional attribution fields beyond the canonical minimum
- domain-scoped tool loading defaults, cross-domain borrow restriction (search-only by default), and context-pressure auto-shrink behavior
- isolation primitive defaults per child run kind, with per-task and per-call overrides for shared-workspace work
- classification mode per capability — deterministic declaration vs. model-mediated per-call classification — for `reversibility_class`, `idempotent`, and other declarations where a single static value is not meaningful

Settings define intended product variation. They must not become hidden hardcoded branches.

## 28. Explicit Rejections

The following shapes are wrong for this layer:

- treating chat message generation as the whole execution model
- making every request a heavy task graph
- making the linear agent loop the universal core architecture
- making planning a mandatory phase
- allowing side effects outside capability and policy flow
- treating background work as a separate execution architecture
- allowing child agents to mutate parent state directly
- using silent last-write-wins for concurrent mutations
- recording fast-path work only as hidden router context
- treating live events as durable execution truth
- treating frontend participation style as backend execution mode
- task promotion by hidden router or execution heuristic
- automatic merge of parallel outputs without an explicit merge path
- automatic compaction as an execution-layer side effect
- provider retry and failover logic implemented inside the execution layer
- hardcoding one tool-loading policy with no meaningful user override
- hardcoding one approval-policy interpretation mode or template with no meaningful user override
- hardcoding retry, loop, budget, or stuck thresholds outside settings
- locking parallel runs or parallel calls against the same backend, session, sandbox, or external service to single-instance access — full parallelism and multi-use of every service is the canonical posture, and the event envelope must carry enough demultiplexing identity for it
- accepting `completed` status without recorded execution evidence when the run contract required action
- treating a tool's internal handling of input variants as a separate capability call (binary vs text branches inside one read tool, fallback paths inside one write tool) — internal sub-handling is the same capability with sub-modes
- silently auto-resuming orphaned in-flight runs at process restart without user-surfaced affordance
- enforcing budgets by default — budgets must be opt-in
- requiring or imposing model-mediated checks where the deterministic floor is sufficient, and conversely silently relying on deterministic checks where the user has configured semantic verification

## 29. Consequences for Later Specs

Later specs must follow these rules:

- task specs must define revision-safe task updates and success criteria
- capability specs must define proposals, leases, previews, reversibility, idempotency, postconditions, concurrency metadata, partial-output meaningfulness, cooperative-stop deadlines, sibling-abort behavior, resume-on-restart handlers, stale-state revalidation patterns, and per-capability classification mode (deterministic vs. model-mediated)
- policy specs must define approval, denial, escalation, lease semantics, the permission tier hierarchy including `Denied`, `typed-confirmation`, the lease scope hierarchy, model-mediated `auto-decide` mode, and contradiction-checking across scope levels
- provider specs must expose model role, tool support, modality, streaming, and fallback metadata, and must surface backend identity for parallel-run demultiplexing
- context specs must compile context from run, task, artifact, world, memory, and evidence state, and expose overflow/degraded-assembly outcomes without mutating state, including the typed context-pressure boundary execution signals through
- storage specs must separate ledger, version commits, artifacts, and projections, must record full per-call provider/model/role/token/cache/cost attribution keyed by model identifier, must carry full-granularity timestamps and any extension attribution, must enforce the ledger-side forgery guard at status transition, and must define the orphan-run reconciliation policy at process restart
- event specs must carry envelope identity (`chat_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`) and `sensitivity` (`Public` / `Sensitive` / `Secret`) on every event, and must keep `Secret` payloads out of durable persistence
- UI specs must present runs without making presentation the execution truth, must surface failed-on-restart runs with per-run resume-or-discard affordances, and must expose the cancel UI's default action plus expanded-menu options (cancel run / run+children / specific child / specific tool call / specific sandbox)
- automation specs must reuse the run model instead of creating a parallel scheduler runtime, and must compose per-stage budgets within the run model
- domain specs must declare default tool surfaces, context policies, budgets, and child-run affordances, and must default cross-domain capability access to search-and-borrow rather than autoload
- quality-control specs must integrate through event/capability hooks instead of a separate execution pipeline, and the completion-verification hook surface must support both deterministic and model-mediated checks at user-configured cadence
- workspace and isolation specs must define the canonical isolation primitives (git worktrees, isolated browser profiles, sandboxed VM instances, isolated process groups) and the runtime selection policy plus the shared-workspace exception
