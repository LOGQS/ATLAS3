# Runtime Infrastructure and Lifecycle

## Status

Canonical. This file defines the runtime substrate of ATLAS3: the process and inter-process topology the application runs as, the asynchronous-execution and concurrency substrate every other layer schedules work on, the background-worker model and its supervision, the in-process work queues and timer primitives, the service-composition container that wires the backend together, the transports that carry the one event bus and the frontend bridge, the ordered application lifecycle (startup, shutdown, crash recovery, relaunch), the bootstrap-configuration boundary, the global intervention cancellation token, and operational health and remediation. It owns the runtime *mechanics* that Files 04, 10, 17, 20, 23, 33, and 36 each declare a lifecycle, worker, transport, or supervision participation in and delegate here, and it introduces the net-new primitives those files reference but do not own: the `Runtime`, the `BackgroundWorker` and its supervision, the `WorkQueue`, the `RuntimeTimer`, the `ServiceGraph`, the `Transport`, the `BootstrapConfig`, and the operational-health remediation contract. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the chosen model: the `Runtime` — the one substrate service that hosts the process, the asynchronous-execution runtime, the service graph, the workers, the queues, the timers, and the transports — and the rule that it is a substrate *beneath* the one run model (File 04), the one ledger and event stream (File 10), the one scheduler (File 33), and the storage substrate (File 20), never a parallel engine, scheduler, queue, or store of its own
- the process and inter-process topology — the Rust-first authoritative core with a browser-based UI shell, the multi-process model (backend, UI shell, helper and sidecar processes), single-instance enforcement with running-instance handoff, and the native inter-process-communication posture
- the asynchronous-execution and concurrency substrate — the async runtime, the blocking-work offload discipline, the runtime concurrency caps, and the rule that no backend, session, process, connection, or service is an implicit single-instance lock
- the `BackgroundWorker` model, the closed `WorkerState` set, the `WorkerSupervisor`, and the `SupervisionPolicy` — how registered long-lived runtime execution units are spawned, made observable, kept alive, restarted, circuit-broken, and reaped
- the `WorkQueue` — the bounded, prioritized, resume-ordered, backpressure-aware in-process work-dispatch primitive, and the serialized-writer-queue it composes with at the storage boundary
- the `RuntimeTimer` — the single-armed-timer primitive against which deadline guards and the scheduler's next-fire instants are armed, and the event-first-not-polling discipline it enforces
- the `ServiceGraph` — the service-composition container that wires the backend's services at startup and at runtime, the static-and-dynamic registration split, and the command-rail, command-line, and headless invocation parity over it
- the `Transport` model and the closed `TransportKind` set — the wire implementations beneath the one event bus and the frontend bridge, and the contract that every transport preserves the canonical envelope, ordering, sensitivity filtering, and per-context-tuple sequence
- the application lifecycle — the ordered, deterministic startup boot graph; the shutdown-and-drain contract; crash, restart, and recovery; and update application and relaunch
- the `BootstrapConfig` — the startup-only configuration read before the settings service exists, its discovery, and the rule that it is not a runtime settings source
- the global intervention cancellation token the `Runtime` maintains across the agent loop, tool calls, sandbox operations, and service calls
- operational health and remediation — the operate side of the observability boundary, the health-driven restart and route-around decisions, degraded-mode operation, and the observe-not-operate seam with File 41
- runtime resource governance — process-level resource posture, connection and worker pools, and load shedding, and its boundary with per-sandbox resource limits (File 23) and per-run budgets (File 04)
- the runtime events, the settings dimensions, the persistence/locality/replay contract, the operating constraints, the explicit rejections, and the consequences for later specs

This file does not define:

- the `Run` lifecycle, the capability-call pipeline, child runs, cancellation semantics, budgets, stuck detection, or the orphan-run reconciliation *policy* — File 04 owns those; this file provides the process, worker, queue, timer, and transport substrate they run on and enforces the orphan reconciliation at restart
- the `ExecutionLedger`, the `EventStream`, the `EventEnvelope`, the closed `AppEvent`/`LedgerEntryKind` catalogues, the `Hook` primitive, the lifecycle and background-worker *event kinds*, the delivery classes, or replay semantics — File 10 owns those; this file consumes the bus, emits the lifecycle and worker facts through it, and implements the transport beneath it
- the settings cascade, scope resolution, profiles, the TOML overlay, or the per-key bootstrap-versus-runtime classification — File 15 owns those; this file owns the bootstrap-configuration boundary and reads settings for its tunable dimensions
- the `ProviderAdapter`, the `ProviderHealth` state machine, `RateLimitState`, transport-level provider retry, or the credential pool — File 17 owns those; this file provides the worker, connection-pool, and transport substrate the provider layer runs on and consumes its health facts
- the storage engine, the connection model, transactional guarantees, the blob store, projection rebuild *mechanics*, the on-disk layout, schema migration, garbage collection, backup, or the storage-side reconstruction *internals* — File 20 owns those; this file owns the ordered application lifecycle these storage phases sit within and invokes them
- the secret vault, credential lifecycle, the trust model, encryption, egress governance, or the audit-chain cryptography — File 22 owns those; this file orchestrates the vault-unlock phase at startup and honors the secret boundary across every transport and process
- the `Sandbox` contract, process spawning, `ProcessGroup`s, filesystem and network enforcement, resource limits, killability, the elevated helper, or the subprocess-wrapper isolation — File 23 owns those; this file invokes the kill-and-reap contract at shutdown and at restart and does not reimplement process spawning, confinement, or killability
- the `Trigger`, the `TriggerKind` taxonomy, the `Scheduler`'s detection and arbitration, the `WatchPolicy`, the `Automation` object, missed-fire reconciliation *policy*, or the non-interactive-execution posture — File 33 owns those; this file owns the worker-scheduling primitives the `Scheduler` and watch poller run on, places the one `Scheduler` in the boot graph, and provides the single-armed-timer primitive
- the `Connector`, the `ConnectorRegistry`, the `McpSession`, the `McpTransportKind` protocol semantics, the `ConnectionState` machine, or connector reconnect *policy* — File 36 owns those; this file owns the transport implementation and the connection-pool and reaper substrate the connectors run on
- the `Observatory`, `LogRecord`, `Span`/`Trace`, `MetricInstrument`, the health-status *data contract*, telemetry egress, or the debug-surface data contracts — File 41 owns those and observes; this file operates and remediates, and emits the operational facts File 41 projects
- the `Shell`, the renderer registry, panel layout, the rendering of any runtime surface, or accessibility presentation — Files 37 and 38 own those; this file owns the frontend-bridge transport and the data contracts they render
- the installer, update channels and distribution, the sidecar binary inventory, platform integration, the platform crash-handler registration, the native-messaging-host registration, or release artifacts — the future Packaging, Platform, and Distribution spec owns those; this file owns the *running* lifecycle, the apply-on-restart and relaunch mechanics, and the managed-service lifecycle contract sidecars are run under
- the capability declaration field set, the registry, or the runtime-registration semantics; the version graph; the world-model entities; or workspace identity and the disk-sync loop — Files 05, 11, 18, and 24 own those; this file orchestrates the startup phases that register capabilities, rebuild projections, warm world state, and re-attach workspaces

## Source Resolution

Families reviewed: the ATLAS3 specbase infrastructure and cross-cutting layer (`infrastructure/lifecycle.md` — the four-phase startup with latency envelopes, the graceful-shutdown sequence, signal handling, port cycling, and the database-lock/corruption/provider/config/sidecar error scenarios; `cross-cutting/service-layer.md` — the `AppState` container, the service trait pattern, the `DynamicServiceRegistry`, the thin-command-wrapper rule, command-line/inter-process-communication parity, and the `spawn_blocking` discipline; `infrastructure/configuration.md` — the six startup-only bootstrap variables read once, settings registration at startup, live overlay reload without restart, and the secret-vault unlock lifecycle; `infrastructure/database.md` — the single-writer/N-reader pool, write-ahead-logging pragmas, busy-timeout, and forward-only migration at startup; `infrastructure/errors-and-retry.md` — the `retryable`-authoritative gate, the typed retry strategies, and the `Closed`/`Open{until}`/`HalfOpen` circuit breaker; `infrastructure/sync.md` — the background sync loop and the local-first never-block invariant; `infrastructure/mcp.md` and `infrastructure/external-apis.md` — spawn-on-demand server lifecycle and the startup loading pipeline with vault dependency ordering; `cross-cutting/events.md` — the bus, the `hooks.toml` compiled at startup, and `EventBufferOverflow` backpressure; `cross-cutting/state-awareness.md` — the panel register/unregister lifecycle and the broadcast watch channel; `cross-cutting/README.md` — the service init-ordering directed acyclic graph; `systems/19-scheduling-pipeline.md` — the one-scheduler check, the unified directed-acyclic-graph executor, and the loop/debounce governance; `unit12-infrastructure.md` — the `AppState` service registry, the startup phase ordering, the seven named background workers and their cadences, the profile-driven first-run bootstrap, the two-database synced/device-local split, the global interrupt token, and the webhook receiver and plugin-reaper workers; `unit02-cross-cutting-infra-and-presentation.md` — the register-definitions → run-settings-migrations → boot-services ordering and the flush-frontend-log-batch shutdown mandate; `atlas3-core/CONSTRAINTS.md` — the Rust/Tauri/React inter-process-communication topology, the backend `UiState` updated by frontend events, the six bootstrap environment variables read exactly once, the `tracing` mandate, the `backend_id`-bearing event envelope, and settings-over-constants; `atlas3-core/TODO.md` §20 — startup housekeeping, graceful shutdown, signal handling, port cycling, the connection pool, idempotent startup sync, the bootstrap variables read once, and the exponential-backoff-with-jitter retry; `atlas3-core/Context.md` — the Tauri-v2/typed-invoke-plus-Channel/no-HTTP-server posture and the `AppState` dependency-injection container); the strategic target-state review (`codex_recommendations.md` §3.1 Rust-first core with a browser UI shell, §3.2 the three frontend state classes, §3.3 the hybrid append-only-ledger-plus-projections persistence, §11.2 the lifecycle additions — projection rebuild and verification, capability health checks, world-graph warmers, run recovery, stale-approval-lease cleanup, §13.1 the core service decomposition, §4.2 the bus-versus-ledger split); the external ecosystems (`claude_code_tool.md` the in-process idle-gated durable cron with jitter and the foreground/background agent execution; `claude_cowork_tool.md` worktree isolation with auto-cleanup and the two-environment sandbox; `chatgpt_tool.md` and `codex_tool.md` the persistent-automations and the session-versus-persistent execution-environment split); and the wider repository corpus on application lifecycle, daemons, worker pools, queues, supervision, transports, and single-instance enforcement (`terax-ai`/`voicebox`/`opencode`/`sidex`/`warp` the Tauri-stack sidecar lifecycle, health-check racing, parent-process-identifier watchdog, port-reuse detection, single-writer thread, Unix-domain-socket and native-messaging transports, debounced flush-on-hide, and `Platform.restart`/`update`; `multica`/`multica-2`/`hermes`/`operator-use`/`evolver` the daemon poll-loop, semaphore-gated worker pools, recover-orphans-at-startup, file-lock single-instance, graceful drain, heartbeat-driven dispatch, the garbage-collection sweeper, the idle scheduler, the proxy-mailbox inter-process boundary, the typed-backoff stake bootstrap, and the independent validator daemon; `claude-mem`/`context-mode`/`omi`/`bytebot`/`open-cowork` the orphan reaper, the parent-process-identifier death detection, the generation counter and unclean-shutdown flag file, the priority queue with resume-first ordering, the session cache with eviction, and the scheduled-task poll loop; `t3code` the event-sourced command queue, the pure-function Decider, the `DrainableWorker` drain-without-poll pattern, the layer/service interface split, and the transport state machine; `n8n`/`affine`/`langflow`/`deer-flow` the leader-only scheduled-task firing with jitter, the concurrency-control queue, the auto-reconnect reference-counted connection pool, the dependency-injection scope hierarchy, and the dual scheduler/execution thread pools; `goose`/`goose-rust`/`gemini-cli`/`forgecode`/`codebuff`/`continue` the `SchedulerTrait`, the session-type and background-execution-mode variants, the `tokio` concurrency primitives and process-global lazy initialization, the message-bus pub/sub, the compaction-strategy composition, and the multi-process core/IDE/webview topology).

Resolution rule: this file owns the runtime *mechanics* and the application *lifecycle*; it re-owns no policy, no business logic, and no consequential-fact store. The run model, child runs, cancellation, budgets, and orphan-reconciliation policy stay File 04's; the ledger, bus, hooks, events, and replay stay File 10's; the settings cascade and the bootstrap-versus-runtime classification stay File 15's; provider health, retry, and the credential pool stay File 17's; the storage engine, transactions, projections, migration, garbage collection, and storage-reconstruction internals stay File 20's; the vault, trust, egress, and audit cryptography stay File 22's; the sandbox, process spawning, confinement, killability, and the elevated helper stay File 23's; triggers, the scheduler's detection and arbitration, watches, automations, and missed-fire policy stay File 33's; connectors, the session, the transport protocol, and reconnect policy stay File 36's; the observability projections and the health data contract stay File 41's; UI rendering stays Files 37 and 38's; the installer, update channels, the sidecar binary inventory, the crash-handler and native-messaging-host registration, and release artifacts stay the future Packaging spec's. This file introduces the `Runtime`, the `BackgroundWorker` and its supervision, the `WorkQueue`, the `RuntimeTimer`, the `ServiceGraph`, the `Transport` and its kinds, the `BootstrapConfig`, the boot graph and shutdown contract, the global intervention cancellation token's realization, and the operational-health remediation contract.

Resolved tensions:

- **A new runtime engine, scheduler, queue, and store versus the substrate beneath the existing ones.** The corpus is full of daemons that own their own loop, scheduler, store, and execution model. Resolved decisively toward the substrate framing: there is already one run model (File 04), one ledger and event stream (File 10), one scheduler (File 33), and one storage substrate (File 20). A second of any of these would fracture replay, audit, and the single source of truth. This file is the process, worker, queue, timer, transport, and lifecycle *substrate* those layers run on; it adds no second engine, scheduler, queue-of-record, or store. This is the load-bearing reframe, the same move File 41 made for observability.
- **Single-process versus multi-process.** A single in-process design is simplest but cannot isolate a crashing browser engine, a runaway code-execution runtime, or an elevated operation from the authoritative core. A fully service-oriented multi-daemon design maximizes isolation but multiplies inter-process-communication, lifecycle, and failure surface and contradicts the local-first single-application posture. Resolved toward the Rust-first authoritative core with a browser-based UI shell and helper and sidecar processes for work that must be isolated or is foreign to the core (`codex_recommendations.md` §3.1: "Rust-first with a browser UI shell," not "a web app wrapped in Tauri"). The core owns the world model, execution, persistence, policy, retrieval, sync, evaluation, and the registry; the UI shell renders; helpers and sidecars are `ManagedProcess`es (File 23) under a managed-service lifecycle this file contracts.
- **A polling daemon loop versus event-first with armed timers and deadline guards.** Source schedulers and monitors poll on tight loops (one-second, thirty-second, sixty-second). `core.event-first-by-default` (File 01 §7.15) forbids time-based polling as a correctness mechanism. Resolved toward event-first: workers react to bus events and to typed liveness facts, the scheduler arms a single timer to a computed instant (File 33 §3.3), and the one legitimate periodic shape — a per-worker missed-heartbeat watchdog — is a finite, configurable deadline re-armed on each heartbeat and computed as a deadline, not a continuous poll (`core.event-first-by-default`, File 01 §7.15's allowance for "explicit scheduler timers and safety guards owned by the relevant subsystem and computed as deadlines"). It is the one flagged periodic exception this file owns.
- **Worker liveness ownership.** File 41 §11.3 states explicitly that observability infers no staleness from missing heartbeats and owns no liveness timeout, cooldown, restart, or remediation, and that those belong here. Resolved by accepting that ownership: this file owns the missed-heartbeat watchdog, the liveness classification it drives, and the remediation it triggers; File 41 projects the resulting facts. The observe-not-operate seam is fixed (§16).
- **Auto-restart everything versus typed supervision policy.** Blanket auto-restart can mask a deterministic crash loop and silently re-run a failed orphan. Resolved toward a per-worker `SupervisionPolicy` with backoff and a circuit breaker (`Closed`/`Open`/`HalfOpen`, reusing File 17 and File 36 shapes), a strict separation of the three orphan classes — orphan *runs* are never auto-resumed and are surfaced for the user (File 04 §28); orphan *processes, sandboxes, and process groups* are reaped (File 23 §10.3); orphan *workers* restart under policy — and recovery driven by source/state/probe/user signals, with cooldown only as a configurable safety guard, never proof of recovery.
- **Shutdown-timer correctness versus commit-boundary correctness.** A shutdown that depends on a drain timer to be correct loses data when the timer is too short on weak hardware. Resolved toward commit-boundary-and-restart-reconciliation correctness (File 10 §13.4, File 20 §13.4): acknowledged critical records are durable before success is reported, in-flight drain is best-effort, and a forced-shutdown backstop is a finite safety guard, never a correctness condition. "Atlas is ready to close at any time."
- **Static-only versus static-plus-dynamic service composition.** Compile-time-only service wiring cannot host plugins, connectors, and user-defined subsystem extensions added at runtime; a purely string-keyed dynamic registry loses type safety for the core. Resolved toward both (`cross-cutting/service-layer.md`): typed static services wired in the `ServiceGraph` at startup, plus a `DynamicServiceRegistry` for runtime-registered services declaring typed method descriptors, with dispatch resolving static-first then dynamic.
- **A bundled local network server versus native inter-process communication.** A hosted local HTTP/server-sent-events server is the conventional shape but adds a network attack surface, a fixed port to contend for, and a transport mismatch with a desktop shell. Resolved toward native inter-process communication as the default frontend transport (typed invoke plus a streaming channel, `atlas3-core/Context.md`): the application binds no application-level network port of record. Loopback ports are used only by sidecars, the inbound-webhook receiver (File 33/36), and an optional user-run telemetry collector (File 41), each allocated dynamically with collision handling, never a fixed application port.
- **Fixed-port-bind versus lock-file-plus-handoff for single-instance.** Resolved toward a single-instance lock with running-instance handoff: a second launch detects the lock, hands its request to the running instance over inter-process communication and exits, and a stale lock from a crashed process is detected and reclaimed (`infrastructure/lifecycle.md`). The lock file's placement is File 20's (§8.3); the acquisition and handoff are this file's.
- **In-place update versus apply-on-restart with rollback.** Mutating a running installation risks a half-applied update and a corrupt run. Resolved toward apply-on-restart: the future Packaging spec stages the update, this file sequences the relaunch, and File 20's last-known-good marker and self-check rollback (File 20 §12.3) guard a bad update.

## 1. Chosen Model

Anchor: `runtime.chosen-model`

### 1.1 Definition

ATLAS3 has one runtime substrate, the `Runtime`. The `Runtime` is the substrate service (`core.substrate-services`, File 01 §2.4) that hosts the operating-system process or processes the application runs as, the asynchronous-execution runtime that all backend work is scheduled on, the `ServiceGraph` that wires the backend's services, the `BackgroundWorker`s and their supervision, the `WorkQueue`s and `RuntimeTimer`s work is dispatched through, the `Transport`s that carry the one event bus and the frontend bridge, and the ordered application lifecycle that brings all of this to a usable state, drains it on shutdown, and recovers it after a crash. The `Runtime` is the realization of the Infrastructure layer (`core.system-layers`, File 01 §2.5) that "hosts and executes the runtime."

The `Runtime` is a substrate, not an engine. It runs the one run model (File 04), the one ledger and event stream (File 10), the one scheduler (File 33), and the one storage substrate (File 20); it does not duplicate them. It schedules work; it does not decide what the work means. It supervises and remediates the processes and workers those layers spawn; it does not own their semantics.

### 1.2 Purpose

Files 04, 10, 17, 20, 23, 33, and 36 each declare a startup phase, a background worker, a transport, a connection pool, a reaper, or a supervision need and defer the mechanics to "the future Runtime Infrastructure and Lifecycle spec." File 04 needs a process that hosts the run loop and a token that cancels it; File 10 needs the bus delivered over a transport, the lifecycle events emitted, and a startup and shutdown sequence; File 17 needs a worker and connection-pool substrate and provider warmers; File 20 needs the broader application lifecycle its storage phases sit within; File 23 needs the application lifecycle around its process startup and shutdown participation and the kill-and-reap invocation; File 33 needs the worker-scheduling primitives and the single-armed-timer the scheduler runs on and its placement in the boot graph; File 36 needs the transport implementation, the connection pool, and the reaper. This file is the single place those mechanics become concrete, so that no later spec invents a parallel process model, a private worker loop, an ungoverned transport, a second scheduler runtime, or an unsupervised daemon.

### 1.3 Rule

- There is one `Runtime`. No subsystem, surface, plugin, or connector opens a parallel application process model, a private asynchronous runtime, a private worker-supervision loop, a private timer or queue of record, a private transport beneath the bus, or a second startup/shutdown sequence. Every long-lived runtime execution unit is a `BackgroundWorker`, every internal work-dispatch queue is a `WorkQueue`, every armed deadline is a `RuntimeTimer`, and every backend service is composed in the `ServiceGraph`.
- The `Runtime` is a substrate beneath the canonical engines, never a parallel one. It hosts the run model, the ledger and bus, the scheduler, and storage; it adds no second run model, ledger, scheduler, or store. A trigger-originated run is an ordinary `Run` (File 04 §28), a consequential fact is a `LedgerEntry` (File 10), a scheduled fire is the one `Scheduler`'s (File 33), and a durable write is the `StorageEngine`'s (File 20).
- Detection, supervision, and remediation are event-first. Workers react to bus events and typed liveness facts; the scheduler arms a single timer; the one periodic shape this file owns is the per-worker missed-heartbeat watchdog, a finite configurable deadline re-armed on each heartbeat (§6.4), flagged as the explicit exception. Time-based polling is never a correctness mechanism.
- The `Runtime` is killable and recoverable by construction. Every worker, queue, timer, transport, and helper process it owns is cancellable and reapable through the killability contract (File 04 §17.3, File 23 §10), shutdown correctness comes from commit boundaries and restart reconciliation rather than a drain timer, and no orphan run auto-resumes at startup.
- The `Runtime` owns mechanics, not policy or business logic. Business logic stays in the owning service (the service-layer-ownership rule, File 01 §7.7); retry, backoff, and circuit-breaking policy declarations stay with the owning layer (Files 04, 17, 33, 36); the `Runtime` executes the supervision and provides the substrate.

### 1.4 Net-New Objects and Supersession

The net-new noun-objects this file introduces are deliberately minimal: `Runtime`, `BackgroundWorker` (+ the closed `WorkerState` set), `WorkerSupervisor` (+ `SupervisionPolicy`), `WorkQueue`, `RuntimeTimer`, `ServiceGraph`, `Transport` (+ the closed `TransportKind` set), `BootstrapConfig`, and the operational-health `RemediationPolicy`. Everything else is consumed: runs from File 04, the bus and the lifecycle and worker event kinds from File 10, settings from File 15, provider health from File 17, the storage lifecycle phases from File 20, the vault from File 22, processes and the kill-and-reap contract from File 23, the scheduler and triggers from File 33, the connector connection state from File 36, and the health projection from File 41.

`Runtime` supersedes any earlier vocabulary that named the same substrate: "the app", "the host", "the main process", "the backend", "the kernel", "the daemon", "the tokio runtime", "the service container", "AppState", "the supervisor", "the supervisor tree". `BackgroundWorker` supersedes "background task", "daemon thread", "background goroutine", "tokio task", "poller", "sweeper", "maintenance loop", "worker", "sidecar loop". `WorkQueue` supersedes "job queue", "task queue", "dispatch queue", "command queue", "submission queue", "concurrency-control queue", "mailbox". `RuntimeTimer` supersedes "timer", "ticker", "scheduled callback", "delay", "deadline". `ServiceGraph` supersedes "service container", "AppState", "dependency-injection container", "service registry", "module graph". `Transport` supersedes "IPC channel", "event channel", "bridge", "Tauri channel", "WebSocket channel", "Unix socket", "named pipe", "broadcast channel", "wire". These are the canonical typed shapes the rest of this file uses; earlier names from source material map into them.

This model elaborates `core.system-layers` (File 01 §2.5) (the Infrastructure layer), the Rust service layer (File 01 §6.1) and the service-layer-ownership rule (File 01 §7.7) (services live in the Rust backend; this file composes and hosts them), `core.event-first-by-default` (File 01 §7.15) (supervision is event-driven; one flagged deadline exception), the user-control-and-killability invariant (File 01 §7.11) (every runtime unit is killable), `core.non-destructive-by-default` (File 01 §7.13) (recovery loses no committed fact), `core.projection` (File 01 §6.11) (runtime handles are rebuildable projections), and `core.stack-commitments` (File 01 §9) (the Rust core and the shell). It discharges the runtime mechanics deferred by `ledger.lifecycle-integration` (File 10 §17.5), `storage.lifecycle-reconstruction` (File 20 §13.4), `sandbox.consequences-for-later-specs` (File 23 §21), `automation.scheduler` (File 33 §9.4) and `automation.consequences-for-later-specs` (File 33 §23), `integration.mcp-lifecycle` (File 36 §5.7), `integration.mcp-session` (File 36 §6.5), and `integration.connection-recovery` (File 36 §7.7), and it operates the health facts `observability.health` (File 41 §11) projects.

## 2. Boundaries with Adjacent Layers

Anchor: `runtime.boundaries-with-adjacent-layers`

### 2.1 With File 04 (Execution and Run Model)

File 04 owns the `Run`, the model/tool loop, child runs, the cancellation contract (`run.cancellation`, File 04 §17.3), per-run and per-stage budgets (`run.budgets-limits`, File 04 §21), stuck detection, and the orphan-run reconciliation *policy* (`run.cancellation`, File 04 §17.3 `process_restart_orphan`). This file provides the process and asynchronous-execution substrate the run loop executes on, the `WorkQueue` and concurrency substrate parallel units are dispatched through, the global intervention cancellation token the loop honors (§15), and it enforces the orphan reconciliation at restart (§13). It owns no run semantics: a run's budget is File 04's, the runtime's concurrency caps are this file's, and the two compose without duplication. The rejection of single-instance backend locks (`run.explicit-rejections`, File 04 §28) is a property this file's substrate provides: parallel runs and parallel calls against the same provider, session, sandbox, or service are first-class and demultiplexed by the `backend_id` envelope dimension (File 10 §5.2).

### 2.2 With File 10 (Execution Ledger, Event Stream, and Hooks)

File 10 owns the ledger, the bus, the envelope, the closed `AppEvent` and `LedgerEntryKind` catalogues (including `AppStarted`, `AppShuttingDown`, `AppStopped`, `BackgroundWorkerSpawned`, `BackgroundWorkerHeartbeat`, `BackgroundWorkerStopped`, `BackgroundWorkerFailed`, `EventBufferOverflow`), the delivery classes and aggregation policies, the `Hook` primitive, the subscription-persistence and lifecycle-integration contracts (`ledger.subscription-persistence-lifecycle`, File 10 §13; `ledger.lifecycle-integration`, File 10 §17), and replay. This file consumes the bus, emits the lifecycle and worker facts through it, and owns the transport beneath it (§10): every `Transport` preserves the canonical envelope, the per-`sequence_scope` ordering, the sensitivity filtering, and the delivery classes File 10 defines (`ledger.streaming-live-partials`, File 10 §12.6). File 10 §17.5 states that "the actual lifecycle mechanics are owned by the future Runtime Infrastructure and Lifecycle spec"; this file is that owner. The bus is transient coordination; this file never makes a transport a durable store.

### 2.3 With File 15 (Settings, Profiles, and Scope Resolution)

File 15 owns the settings cascade, scope resolution, profiles, the TOML overlay, and the bootstrap boundary (`settings.bootstrap-boundary`, File 15 §12), which states that "exact bootstrap variable names, file locations, and discovery order belong to infrastructure." This file is that infrastructure: it defines the `BootstrapConfig` contract and its variable set, reads it once before the settings service exists, and never treats it as a runtime settings source (§14). Every tunable runtime dimension — worker concurrency caps, supervision thresholds, drain backstops, queue depths, idle-detection thresholds — is a setting (`settings.settings-over-constants`, File 15 §13), not a hardcoded constant. Live overlay reload without restart feeds the settings reactivity, not a bypass of it.

### 2.4 With File 17 (Provider Layer, Rate Limits, and Usage Accounting)

File 17 owns the `ProviderAdapter`, the `ProviderHealth` state machine (`provider.provider-health`, File 17 §12), `RateLimitState`, transport-level provider retry (`provider.transport-level-retry-backoff`, File 17 §11), and the credential pool. This file provides the worker and connection-pool substrate the provider layer runs on and the provider-warmer phase at startup (§11) — the model-catalogue refresh that is the implicit connectivity check (File 17 §12.4), never a scheduled health ping. It consumes `ProviderHealth` as an operational-health input (§16); it never recomputes provider health, never polls a provider on a schedule, and never reimplements provider retry — the retry strategy is File 17's, the worker that runs it and the connection it runs over are this file's.

### 2.5 With File 20 (Storage and Persistence)

File 20 owns the `StorageEngine`, the connection model, transactions, the blob store, projection rebuild mechanics, the on-disk layout and locality partition (`storage.physical-layout-locality`, File 20 §8), schema migration, garbage collection, backup and recovery, and the storage-side lifecycle and reconstruction *internals* (`storage.lifecycle-reconstruction`, File 20 §13). File 20 §13.4 states that "the broader application lifecycle beyond storage — provider warmers, UI initialization — is the future Runtime Infrastructure and Lifecycle spec's; this file owns the storage phases within it." This file owns the ordered application boot graph (§11) and shutdown contract (§12); the storage phases — acquire the single-instance lock, open and integrity-check the substrate, migrate after backup, warm caches, rebuild and verify projections, recover interrupted work, clean stale leases — are invoked in that graph as File 20's sub-sequence. The single-instance lock file is placed by File 20 (§8.3); its acquisition and handoff are this file's (§4.4). The last-known-good marker and self-check rollback (File 20 §12.3) are the storage substrate's; this file sequences the relaunch that consults them (§18).

### 2.6 With File 22 (Security, Credentials, and Trust Boundaries)

File 22 owns the secret vault, the credential lifecycle, the trust model, encryption, egress governance, and the audit cryptography. This file orchestrates the vault-unlock phase in the boot graph (§11) and honors the secret boundary across every transport and process boundary it owns: no raw `Secret` material crosses a `Transport` or is injected into a spawned helper's environment except as File 22 and File 23 §16 permit, and every transport's payloads pass the redaction the secret boundary requires (`secret.backend-boundary`, File 22 §4). The elevated helper's process model is File 23's; this file's lifecycle never elevates the core process.

### 2.7 With File 23 (Sandbox, Process Control, and Isolation)

File 23 owns the `Sandbox` contract, process spawning, `ProcessGroup`s, filesystem and network enforcement, resource limits, killability and reaping, the elevated helper, and the subprocess-wrapper isolation. The boundary is the application-lifecycle-versus-process-containment split: File 23 owns *how* a process is spawned, confined, killed, and reaped; this file owns *when* in the application lifecycle that spawning, killing, and reaping happens and the supervision that decides to restart a worker or remediate a degraded one. A sidecar or helper process is a `ManagedProcess` in a `ProcessGroup` (File 23 §5, §6); this file owns its managed-service lifecycle contract (start condition, health signal, restart policy, shutdown order, ownership transfer — `process.groups`, File 23 §6.3) and invokes File 23's kill-and-reap at shutdown and at restart (File 23 §10.3). This file reimplements no process spawning, confinement, or killability (`sandbox.consequences-for-later-specs`, File 23 §21).

### 2.8 With File 33 (Automation and Triggers)

File 33 owns the `Trigger`, the `TriggerKind` taxonomy, the `Scheduler`'s detection and arbitration, the `WatchPolicy`, the `Automation` object, missed-fire reconciliation policy, and the non-interactive posture. File 33 §9.4 and §23 state that "the Runtime Infrastructure and Lifecycle spec owns the background-worker scheduling primitives the `Scheduler` and watch poller run on, the startup ordering that re-arms triggers and reconciles missed fires, and the graceful shutdown that stops the workers," and that it "must place the one `Scheduler` in the startup graph." This file is that owner: the `Scheduler` and the watch poller are `BackgroundWorker`s (§6) placed in the boot graph (§11), the single-armed-timer the scheduler computes its next-fire instant against is a `RuntimeTimer` (§8), and the startup re-arm and missed-fire reconciliation are boot-graph steps (§11, §13). This file owns no trigger detection, no watch evaluation, and no automation semantics; the `Scheduler` runs on its substrate.

### 2.9 With File 36 (MCP and External Integrations)

File 36 owns the `Connector`, the `ConnectorRegistry`, the transport-agnostic `McpSession`, the closed `McpTransportKind` protocol semantics, the `ConnectionState` machine (`integration.connection-recovery`, File 36 §7), and connector reconnect policy. File 36 §5.7, §6.5, and §7.7 hand this file "the startup-phase orchestration," "the transport implementation," and "the reaper and the connection-pool implementation." This file owns the transport wire implementations (§10), the connection-pool and idle-reaper substrate, and the spawn-on-demand placement in the lifecycle; File 36 owns the session protocol, the connection-state semantics, and the reconnect-on-next-call policy that run on that substrate. The `ConnectionState` machine and the `ProviderHealth` machine are reused as the canonical connection-supervision shapes (§6, §16); this file invents no third connection-state machine.

### 2.10 With File 41 (Telemetry, Logging, and Observability)

The `41↔42` seam is fixed (`observability.health`, File 41 §11.2): File 41 **observes** operational facts and exposes health projections; this file **operates** and remediates. File 41 owns the health-status data contract, the metric and trace projections, the diagnostic log stream, and the debug-surface data contracts, and "infers no stale liveness state and owns no liveness timeout, cooldown, restart, or remediation" (File 41 §11.3). This file owns the missed-heartbeat watchdog, the liveness classification it drives, the restart/backoff/circuit-breaker remediation, and the operational-health decisions (§16); it emits the worker and lifecycle facts File 41 projects and consumes File 41's health view to render its own decisions inspectable. There is no runtime watchdog inside File 41 and no observability projection inside this file.

### 2.11 With the future Packaging, Platform, and Distribution spec (File 43)

The future Packaging spec owns the installer, update channels and distribution, the sidecar binary inventory, platform integration, the platform crash-handler registration, the native-messaging-host registration, and release artifacts. This file owns the *running* lifecycle, the apply-on-restart and relaunch *mechanics* (§18), and the managed-service lifecycle contract sidecars are run under (§4.5). The seam: Packaging delivers and stages binaries and registers platform handlers; this file starts, supervises, drains, and relaunches them. A platform crash handler Packaging registers feeds this file's restart-and-recovery path and File 41's redaction-and-consent boundary; a staged update Packaging produces is applied by this file's relaunch sequence against File 20's last-known-good guard.

### 2.12 Boundary

This file is the runtime substrate and the application lifecycle. It owns the `Runtime`, the process and inter-process topology, the asynchronous-execution and concurrency substrate, the `BackgroundWorker` model and its supervision, the `WorkQueue` and `RuntimeTimer` primitives, the `ServiceGraph`, the `Transport`s, the boot graph and shutdown contract, crash recovery and relaunch, the `BootstrapConfig`, the global intervention cancellation token, operational health and remediation, and runtime resource governance. It owns no run, ledger, settings, provider, storage, secret, sandbox, trigger, connector, observability, UI, or packaging semantics; it provides each of those layers the substrate they run on and the lifecycle they participate in.

## 3. The `Runtime`

Anchor: `runtime.runtime`

### 3.1 Definition

The `Runtime` is the always-on substrate service that hosts the application's execution. It owns the process or processes the application runs as (§4), the asynchronous-execution runtime that schedules backend work (§5), the `ServiceGraph` that composes the backend's services (§9), the `BackgroundWorker`s and their `WorkerSupervisor` (§6), the `WorkQueue`s and `RuntimeTimer`s (§7, §8), the `Transport`s carrying the bus and the frontend bridge (§10), and the ordered lifecycle that starts, drains, recovers, and relaunches all of it (§11–§13, §18).

The `Runtime` is:

- a **substrate service**, always on, beneath every work surface, control rail, and substrate service; it is not a work surface and registers no `SurfaceContract`
- a **host**, not an engine: it executes the run model, the ledger and bus, the scheduler, and storage, and supervises the processes and workers they spawn, without owning their semantics
- a **single owner**: there is exactly one `Runtime` per running installation, enforced by the single-instance contract (§4.4)
- a **service face** for the agent and the user only for its read and operational capabilities (§16, §19); its lifecycle controls (relaunch, worker restart) are user-gated and policy-bound

The `Runtime` is not:

- a parallel run model, scheduler, ledger, queue-of-record, or store — those are Files 04, 33, 10, and 20
- a business-logic layer — services hold the logic (the service-layer-ownership rule, File 01 §7.7); the `Runtime` composes and hosts them
- an observability layer — File 41 observes; the `Runtime` operates

### 3.2 Boundary

This section establishes the `Runtime` as the umbrella. Its components are §§4–18; the facts it emits are §19; the dimensions it exposes are §20. The semantics of what it hosts are owned by the hosted specs.

## 4. Process and Inter-Process Topology

Anchor: `runtime.process-topology`

### 4.1 Definition

The process topology is the set of operating-system processes the application runs as and the inter-process channels that connect them. ATLAS3 runs as a Rust-first authoritative core, a browser-based UI shell, and a set of helper and sidecar processes for isolated or foreign work, connected by native inter-process communication.

### 4.2 Purpose

The authoritative state, execution, and policy must live in a memory-safe systems core that the UI cannot corrupt and a crashing browser engine or runaway runtime cannot take down. A single in-process design cannot isolate those failures; a fully service-oriented multi-daemon design multiplies failure surface against a local-first single-application product. The Rust-first core with a rendering shell and isolated helpers is the shape that keeps the authoritative core safe while letting the UI and foreign runtimes fail independently.

### 4.3 Rule

- The **authoritative core** is a Rust backend process that owns the world model, execution, persistence, policy, retrieval, synchronization, evaluation, the capability registry, and the `Runtime` itself (`codex_recommendations.md` §3.1). It is the single writer of durable state. The committed realization is a Tauri-shelled Rust binary; the contract is independent of it.
- The **UI shell** is a rendering surface, not a business-logic layer (the service-layer-ownership rule, File 01 §7.7). It holds session-ephemeral view state and optimistic mutation envelopes that reconcile against the core's authoritative event stream; it holds no authoritative durable state (`codex_recommendations.md` §3.2's three state classes). The committed realization is a browser-based webview; the core also supports a terminal and a headless mode over the same `ServiceGraph` (§9.4).
- **Helper and sidecar processes** run work that must be isolated from the core or is foreign to it — a search backend, a challenge-solver, a code-execution runtime, a managed browser, a command-line subscription wrapper, the one-shot elevated helper. Each is a `ManagedProcess` in a `ProcessGroup` (File 23 §5, §6) under the managed-service lifecycle contract (§4.5). The core process never runs elevated (File 23 §11).
- **Inter-process communication is native and typed.** The frontend bridge is a typed request/response channel plus a streaming channel (§10); the application binds no application-level network server port of record. A helper or sidecar communicates over the local loopback or a local socket confined to `LoopbackOnly` (File 23 §8.3); the browser extension communicates over the authenticated, local, session-bound native-messaging channel (File 36 §6.2). Cross-device coordination is the sync layer's (File 21), never a direct runtime transport.
- **The topology is observable and demultiplexed.** Every process the `Runtime` owns is a `Process` world entity (File 18 §4) projected from its `ManagedProcess` handle, and every event it emits carries the `backend_id` dimension (File 10 §5.2) so concurrent instances are individually observable, signallable, and killable. No process, session, or connection is an implicit single-instance lock (`run.explicit-rejections`, File 04 §28).

### 4.4 Single-Instance Enforcement and Handoff

- A single-instance lock prevents two cores from owning the same data root for writing (`storage.lifecycle-reconstruction`, File 20 §13.3). The lock file is placed under the data root by File 20 (§8.3); the `Runtime` acquires it as the first lifecycle step after bootstrap resolution (§11).
- The lock record carries enough owner identity to distinguish a live owner from a stale or unrelated process for the same data root: process identity, data-root identity, session or launch nonce, and the handoff endpoint identity or platform equivalent. A second launch that finds the lock held by a verified live instance hands its request — the launch arguments, the document or deep-link to open — to that instance over a local authenticated inter-process channel and exits; the running instance surfaces the request (focuses, opens the target). A lock whose owner is proven gone is stale and is reclaimed before proceeding. If ownership cannot be verified safely, startup fails with a typed diagnostic rather than racing or guessing.
- The committed realizations are a platform single-instance facility, a lock file with a recorded process identity, a bound loopback health endpoint, or a named mutex; each is named for grounding and sits behind the single-instance contract.

### 4.5 The Managed-Service Lifecycle Contract

- A sidecar or helper is a managed service process, not a private daemon (`process.groups`, File 23 §6.3). Its lifecycle declares: an owner service, a `SandboxProfile` and network posture (default `LoopbackOnly` or `None`), a start condition (eager at boot, lazy on first use, or spawn-on-demand), a health signal, a `SupervisionPolicy` (§6.5), a shutdown order, an output policy, a kill relationship to its owner, and parent-death behavior.
- A sidecar starts per its start condition, is health-checked event-first (a readiness signal, a first-successful-call, or a bound endpoint), is supervised (§6.5), and is reaped on shutdown through File 23's kill contract (§12). It cannot outlive its owning `ProcessGroup` unless ownership is explicitly transferred to another registered service owner. Ownership transfer is recorded and assigns the sidecar to another registered owner and `ProcessGroup`. When the owner dies unexpectedly, the sidecar is terminated or becomes inert through a platform parent-death signal, job object, inherited pipe or session closure, or equivalent; where a platform cannot provide immediate owner-loss signaling, startup reaping (§13) is the fallback and the orphaned process must be harmless while waiting to be reaped. A sidecar that fails its readiness check disables its dependent feature with graceful degradation (§16) and surfaces a typed setup state; it never blocks core startup.
- The sidecar binary inventory, packaging, and distribution are the future Packaging spec's; the start-health-supervise-reap lifecycle is this file's.

### 4.6 Boundary

This section owns the process and inter-process topology, single-instance enforcement, and the managed-service lifecycle contract. File 23 owns the `ManagedProcess`, the `ProcessGroup`, and the kill-and-reap; File 20 owns the data root and the lock-file placement; File 36 owns the native-messaging session protocol; File 21 owns cross-device coordination; the future Packaging spec owns the sidecar binary inventory. The frontend-bridge transport is §10.

## 5. The Asynchronous-Execution and Concurrency Substrate

Anchor: `runtime.async-concurrency-substrate`

### 5.1 Definition

The asynchronous-execution substrate is the single in-process runtime on which all backend work is scheduled: the cooperative asynchronous task executor, the offload pool for blocking work, and the concurrency governance that bounds how much runs at once. The committed realization is a multi-threaded asynchronous runtime with a dedicated blocking-offload pool; the contract is independent of it.

### 5.2 Purpose

A single, shared, well-governed concurrency substrate is what keeps the streaming UI responsive while the core does heavy work, prevents blocking I/O from starving the cooperative executor, and makes parallelism a first-class, bounded property rather than an ad-hoc spawn-everywhere free-for-all. One substrate also makes cancellation, backpressure, and resource accounting universal rather than per-consumer.

### 5.3 Rule

- All backend work runs on the one asynchronous runtime. Cooperative asynchronous tasks run on the shared executor; blocking work — synchronous file and database I/O, native library calls, CPU-bound transforms — is offloaded to the blocking pool rather than blocking a cooperative worker (`cross-cutting/service-layer.md`'s `spawn_blocking` discipline). A cooperative task must not perform an unbounded blocking call inline.
- Concurrency is bounded and governed, never unbounded spawn. Parallel work is admitted under a concurrency cap (`run.parallelism`, File 04 §15.1); the cap is a setting, resolvable globally, per workload class, and per workspace, with a conservative default. Excess work queues in a `WorkQueue` (§7) rather than over-subscribing the runtime.
- No backend, session, process, connection, or service is an implicit single-instance lock (`run.explicit-rejections`, File 04 §28). Parallel runs and parallel calls against the same provider, sandbox, browser, or connector are first-class; the substrate supports them concurrently with full demultiplexing identity on every event (`backend_id`, File 10 §5.2). Where two units would conflict on a mutable resource, the mutation rule serializes, isolates, parks, or fails (`run.mutation-rule`, File 04 §15.4); the runtime never silently single-instance-locks to avoid the conflict.
- The substrate preserves stable result ordering even when work finishes out of order (`run.parallelism`, File 04 §15.2), and it propagates the global intervention cancellation token (§15) into every spawned unit so cancellation reaches all of them.
- A spawned unit is owned. Every cooperative task and blocking job the `Runtime` spawns belongs to a `BackgroundWorker` (§6), a `Run` (File 04), or a request handler; the runtime spawns no detached, unowned, unkillable task. A fire-and-forget pattern is modeled as a tracked unit with a recorded outcome, never an untracked spawn whose failure disappears.

### 5.4 Boundary

This section owns the asynchronous-execution and concurrency substrate and the no-single-instance-lock and no-detached-spawn rules. Per-run and per-stage budgets are File 04's (§21); per-sandbox resource limits are File 23's (§9); the worker model that uses long-lived tasks is §6; the queue is §7.

## 6. Background Workers and Supervision

Anchor: `runtime.background-workers`

### 6.1 Definition

A `BackgroundWorker` is a long-lived runtime execution unit, owned by a subsystem, that performs work outside the direct request/response and run paths — consolidation, sweeping, indexing, scheduling, watching, syncing, accounting, log rotation, and equivalent recurring or reactive work. The `WorkerSupervisor` is the component that spawns workers in the boot graph, observes their liveness, restarts them under a `SupervisionPolicy`, circuit-breaks a repeatedly-failing one, and reaps them at shutdown. A `BackgroundWorker` is the object the `BackgroundWorkerSpawned` / `BackgroundWorkerHeartbeat` / `BackgroundWorkerStopped` / `BackgroundWorkerFailed` events (File 10 §4.1, §17.2) describe.

### 6.2 The Closed `WorkerState` Set

A `BackgroundWorker`'s liveness is a closed canonical state:

- `Starting` — spawned, performing its own initialization, not yet ready
- `Healthy` — ready and heartbeating within its deadline
- `Degraded { since, contributing_failures }` — recent failures observed; still running and attempted, with logging
- `Stalled { last_heartbeat }` — its missed-heartbeat watchdog (§6.4) fired; the worker is presumed hung and is subject to remediation
- `Failed { reason }` — exited or errored; subject to the `SupervisionPolicy`
- `Stopped` — cooperatively stopped at shutdown or by explicit control
- `CircuitOpen { until }` — the `SupervisionPolicy`'s circuit breaker opened after repeated failures; not restarted until recovery

The state is event-first: a heartbeat returns the worker to `Healthy`; a typed failure transitions to `Failed`; a watchdog deadline transitions to `Stalled`; the supervisor's restart and circuit transitions are recorded. This reuses the shape of `ProviderHealth` (File 17 §12) and the connector `ConnectionState` (File 36 §7.1) rather than inventing a third liveness vocabulary.

### 6.3 Worker Registration Catalogue

The `Runtime` hosts registered `BackgroundWorker` declarations, each owned by its subsystem and registered with the `WorkerSupervisor`. A worker registration declares the owner subsystem, purpose, enablement setting, liveness signal, `SupervisionPolicy`, durable reconstruction source, shutdown order, and whether its work is idempotent or completion-marker-guarded. Known required registrations from existing specs include: the one `Scheduler` and the watch poller (File 33 §9); the audit-overlay writer and the lineage tracker (File 10, File 09); the memory consolidator (File 14); the retrieval and knowledge indexer (File 12); the storage garbage-collection and reconciliation sweeper and the blob verifier (File 20 §6, §11); the sync loop (File 21); the usage and rate-limit accounting and reset worker (File 17); the diagnostic-log rotation and the resource-gauge sampler (File 41 §8.5); and the inbound-webhook receiver (File 33 §5.2, File 36). Subsystem-specific workers — spaced-repetition scheduling, data-source monitors, browser watchdogs — register the same way through their owning specs. This file owns the worker substrate and supervision; each worker's *work* is its owning spec's.

### 6.4 Liveness, the Missed-Heartbeat Watchdog, and the Flagged Periodic Exception

- Worker liveness is event-first: a worker emits `BackgroundWorkerHeartbeat` and typed lifecycle facts; the supervisor consumes them. A worker performing reactive work emits a heartbeat on activity and may emit a configured idle heartbeat cadence when no activity event would otherwise prove liveness. The cadence is a liveness signal, not a work trigger.
- The one periodic shape this file owns is the per-worker missed-heartbeat watchdog: each worker arms a `RuntimeTimer` (§8) to its heartbeat deadline, re-armed on every heartbeat. If the deadline elapses without a heartbeat, the worker transitions to `Stalled` and is remediated (§16). This is the explicit flagged exception to `core.event-first-by-default` (File 01 §7.15): it is a finite, configurable deadline computed once and re-armed, owned by this subsystem as a safety guard, not a continuous poll and not a correctness condition (File 41 §11.3 assigns this ownership here). The deadline is a setting with a generous default; no liveness decision depends on the deadline being short.

### 6.5 Supervision, Restart, and the Circuit Breaker

- Each worker declares a `SupervisionPolicy`: whether it restarts on failure, the restart backoff (a typed strategy — exponential with cap and jitter, fixed, or decorrelated — reusing File 17 §11 and File 36 §7 shapes), the circuit-breaker threshold and cooldown, and the escalation when the circuit opens (disable the worker, degrade its feature, notify the user). The policy is settings-owned with conservative defaults; it is never a hardcoded constant where meaningful variation exists.
- On `Failed` or `Stalled`, the supervisor applies the policy: it restarts the worker after backoff, or, after a configured number of consecutive failures, opens the circuit breaker (`Closed` → `Open { until }` → `HalfOpen`) and stops restarting into a failing condition. Recovery is driven by source-recovery signals, lifecycle events, a bounded policy-gated half-open probe, or explicit user reset; a configurable cooldown is a flapping guard, never proof of recovery, and elapsed time alone never closes a circuit.
- Restart preserves identity: a restarted worker re-resolves the same identity, re-arms its triggers and subscriptions from durable declarations (§21), and reconciles any work it owns; restart is a rebuild, never a loss of the worker's identity or its accepted durable work. Durable work reprocessed after restart is idempotent by construction, keyed by an external idempotency key, or guarded by progress and completion markers in the owning durable substrate. Non-idempotent work without a trustworthy completion marker parks with a typed diagnostic for user or owner-subsystem adjudication instead of retrying blindly.
- A worker restart is distinct from a run resume. The supervisor restarts a *worker*; it never auto-resumes an orphan *run* (File 04 §28) — orphan runs are surfaced for the user (§13). A worker that drives runs (the scheduler) restarts and re-arms; the runs it would fire are gated by the missed-fire and eligibility policy (File 33).

### 6.6 Worker Lifecycle Facts

Every worker emits `BackgroundWorkerSpawned` on start, `BackgroundWorkerHeartbeat` under its delivery class, `BackgroundWorkerStopped` on cooperative stop, and `BackgroundWorkerFailed` on failure (File 10 §17.2), each stamped with the worker identity and the `backend_id` dimension. File 41 projects these into the health view (`observability.health`, File 41 §11); this file emits them and acts on them. A restart, a circuit-open, and a remediation each record their typed fact; no worker disappears, restarts, or is disabled silently.

### 6.7 Boundary

This section owns the `BackgroundWorker`, the closed `WorkerState`, the `WorkerSupervisor`, the `SupervisionPolicy`, the missed-heartbeat watchdog, and the worker-registration hosting. File 10 owns the worker event kinds and delivery classes; File 41 owns the health projection over them; each worker's work is its owning spec's; the timer the watchdog arms is §8; the orphan-run rule is File 04's (§13).

## 7. Work Queues and Dispatch

Anchor: `runtime.work-queues`

### 7.1 Definition

A `WorkQueue` is a bounded, backpressure-aware, in-process dispatch primitive through which deferred or rate-governed work is enqueued and drained by a worker or a worker pool. It carries priority, supports resume-first ordering for crash recovery, and reports overflow rather than dropping silently.

### 7.2 Purpose

Bursty or rate-limited work — a batch of files to index, a stream of storage writes to coalesce, a pile of fires to run under a concurrency cap, a backlog of uploads — must be dispatched in bounded, ordered, recoverable fashion rather than spawned unbounded or processed by a tight poll. One queue primitive makes bounding, prioritization, backpressure, and crash recovery uniform.

### 7.3 Rule

- A `WorkQueue` is bounded. It declares a maximum depth and an admission class. Work beyond the depth is rejected before acceptance with a typed, recorded outcome, backpressures or parks the producer, or applies a declared overflow policy for deferrable work (coalesce duplicates, shed diagnostic or coalescible work), never silently dropped. Accepted consequential work is never discarded by queue overflow. Overflow is observable (it composes the `EventBufferOverflow` discipline, File 10 §5.5, where the queue feeds the bus).
- Dispatch is event-first. A worker drains its queue when an item is enqueued and when capacity frees, driven by enqueue and completion events; it does not poll an empty queue on a clock. A queue with no work and no events is idle, not spinning.
- A `WorkQueue` supports priority, deterministic fairness within each admission class, and resume-first ordering: on restart, work that was already in progress is ordered ahead of fresh work so a crash-interrupted batch resumes before new arrivals (the resume-first pattern). Accepted durable work the queue represents — a queued automation fire (File 33 §12.2), a staged upload — is a handle to an owning durable record, not a record inside the runtime queue. It is reconstructed from durable state at restart (§21), never lost because its in-memory queue did not survive.
- Reprocessing a resumed durable queue item follows the worker restart rule (§6.5): the worker checks the owning progress or completion marker before re-executing; external side effects use idempotency keys or an outbox-style completion record where the external system supports it; unsafe uncertainty parks the item with a typed diagnostic.
- The high-frequency storage-write queue composes with, and does not duplicate, File 20's serialized-writer queue (`storage.engine-connection-model`, File 20 §4.3): coalescing redundant projection writes and batching source-of-truth appends is the storage layer's, and the `WorkQueue` feeds it rather than reimplementing it. Coalescing never removes, merges, or hides a semantic fact.
- Backpressure is honored end to end: a slow consumer applies backpressure to its producer (the frontend bridge pauses the backend when its buffer is full, §10), and a queue that cannot keep up degrades diagnostic or coalescible work first, never blocking a consequential commit to preserve a transient. Long-deferred work surfaces as backlog or degradation rather than silently starving.

### 7.4 Boundary

This section owns the in-process `WorkQueue` primitive and its bounding, ordering, and backpressure. The serialized storage writer is File 20's; the bus delivery classes and overflow signal are File 10's; the scheduler's atomic claim and overlap policy are File 33's; per-run parallelism is File 04's.

## 8. Timers and the Event-First Timing Substrate

Anchor: `runtime.timers`

### 8.1 Definition

A `RuntimeTimer` is the single-armed deadline primitive: it arms one wake-up to a computed instant and fires once when the instant is reached. It is the substrate against which the scheduler's next-fire instants, the missed-heartbeat watchdogs, the cooperative-stop and shutdown backstops, and any other finite deadline guard are armed.

### 8.2 Purpose

The project rejects time-based polling as a correctness mechanism (`core.event-first-by-default`, File 01 §7.15). A single, shared, armed-timer primitive is what lets every legitimate timing need — a schedule's next fire, a worker's liveness deadline, a cancellation's cooperative-stop backstop — be expressed as a deadline computed once and armed, rather than a clock evaluated continuously in a loop.

### 8.3 Rule

- A `RuntimeTimer` arms one wake-up to a computed instant; it does not busy-poll a clock. When it fires, the owner recomputes and re-arms the next instant if the work recurs (`automation.schedule-trigger`, File 33 §3.3). The clock is read to compute a deadline, not evaluated as a continuous condition.
- Every timing need in the runtime is one of: a scheduler next-fire instant (File 33), a finite safety-guard deadline (a cooperative-stop deadline, File 04 §17.3; a worker heartbeat deadline, §6.4; a shutdown-drain backstop, §12; a sidecar readiness deadline, §4.5; a connection-pool idle reap, §10), or a presentation convenience (a debounce or throttle window). None is a correctness condition: a safety-guard deadline is finite and configurable with a generous default, and missing it escalates to a recorded typed outcome, never a silent one.
- A periodic scan is permitted only as a flagged, configurable fallback where a timer cannot be armed or a source emits no change event (`automation.schedule-trigger`, File 33 §3.3; `infrastructure/sync.md`'s flagged sync interval); it is never the default and never a correctness condition, and the owning subsystem flags it. This file introduces no tight clock-poll of its own.
- Debounce and throttle windows are coalescing conveniences (`automation.watch`, File 33 §4.3): a burst of change events within a window collapses into one unit of work. They shape delivery, not correctness, and their windows are settings.

### 8.4 Boundary

This section owns the `RuntimeTimer` primitive and the event-first timing discipline. The scheduler that arms next-fire instants is File 33's; the cooperative-stop deadline is File 04's; the resource-gauge sampling interval is File 41's; the wall-clock external-process safety guard is File 23's (§9). This file provides the primitive and enforces that none of them becomes a poll.

## 9. The Service-Composition Substrate

Anchor: `runtime.service-graph`

### 9.1 Definition

The `ServiceGraph` is the container in which the backend's services are constructed, wired to their dependencies, and held for the application's lifetime. It composes the typed static services known at compile time and a `DynamicServiceRegistry` for services registered at runtime, and it is the single object through which every control rail, the command line, and the headless entry point reach the backend.

### 9.2 Purpose

Business logic lives in the Rust service layer, not in command wrappers or the UI (the service-layer-ownership rule, File 01 §7.7). The `ServiceGraph` is how those services are wired once and reached uniformly: it is what makes adding subsystem N+1 a flat-cost change (`core.extension-planes`, File 01 §6.14), what gives the command rail, the command line, and headless mode the same backend, and what lets plugins register services at runtime without restructuring the core.

### 9.3 Rule

- Services are typed traits returning typed results across the boundary (`cross-cutting/service-layer.md`); each takes immutable references to its dependencies (the storage engine, the settings service, the event bus, other services) and is constructed in the `ServiceGraph` at the service-initialization phase of the boot graph (§11). Construction is fallible and typed; a service that fails to initialize fails startup with a typed error or degrades its feature, per its declaration (§16).
- The `ServiceGraph` holds typed static services for the core and a `DynamicServiceRegistry` for runtime-registered services (plugins, user-defined subsystems, runtime-registered capabilities whose service identity was unknown at startup). A dynamic service registration is a source-attributed registry contribution, not an untyped private object insertion. It requires a source-approved declaration from the owning plugin, connector, subsystem, or user-defined extension, carrying owner, method descriptors, capability or backend bindings if exposed, required resources, teardown behavior, trust/source metadata, and lifecycle hooks. A dynamic service may expose invocable operations only through the capability registry or a declared internal service method consumed by an approved owner. Dispatch resolves static-first, then dynamic (`cross-cutting/service-layer.md`). Plugins register and unregister cleanly; unregistering tears down the service's registrations through the normal channels (File 35), non-destructively (File 01 §7.13).
- Command rails are thin adapters, not ownership boundaries (the Rust service layer, File 01 §6.1): an inter-process-communication command, a command-line command, an automation, and an external-protocol invocation each marshal arguments, call a service method, and marshal the result; they contain no business logic. The command-line and headless entry points compose the same `ServiceGraph` as the UI shell.
- Service wiring is observable and reconstructable: the registered service set is a runtime-handle projection (`storage.projection-store`, File 20 §7.3) rebuilt at startup from durable declarations and settings, never a durable store of its own. A service-graph change (a plugin loaded, a dynamic service registered) emits the registry events the owning spec defines (File 05, File 35).

### 9.4 Headless and Multi-Front Parity

The `Runtime` runs with a graphical shell, a terminal interface, or headless, over the same `ServiceGraph`. A headless run (an automation fire on a server-like deployment, a command-line invocation) composes the full backend without a UI shell; the frontend-bridge transport (§10) is simply absent, and the operational surfaces remain reachable through the command rail. No capability or service depends on a UI being present; a feature that genuinely requires the shell declares it and returns a typed unsupported result in a headless context.

### 9.5 Boundary

This section owns the `ServiceGraph`, the static-and-dynamic composition, and the rail-parity rule. The service-layer ownership rule is File 01's (§7.7); the capability declaration and runtime registration are File 05's; the plugin contribution model is File 35's; the command rails are File 26's; what each service does is its owning spec's.

## 10. Transports and the Frontend Bridge

Anchor: `runtime.transports`

### 10.1 Definition

A `Transport` is a wire over which the one event bus and the typed request/response calls travel between processes, threads, tabs, or peers. The `TransportKind` set is the closed catalogue of those wires. The frontend bridge is the transport between the authoritative core and the UI shell.

### 10.2 The Closed `TransportKind` Set

The canonical `TransportKind` set is closed-canonical-plus-`Custom`:

- `InProcessBus` — the in-memory broadcast within the core process; the bus's native substrate
- `FrontendBridge` — the typed request/response channel plus the streaming channel between the core and the UI shell; the committed realization is the shell's native inter-process invoke plus a streaming channel, not a bundled network server
- `CrossTab` — the intra-device, cross-tab/cross-window broadcast for multiple UI views of the one core
- `LocalSocket` — a local socket or named pipe for a helper, sidecar, or command-line client of the same installation, confined to local/loopback (File 23 §8.3)
- `NativeMessaging` — the authenticated, local, session-bound browser-extension channel (File 36 §6.2)
- `Network` — an outbound connection to an external provider, connector, or service, governed by egress policy (File 22 §11) and run over the connection-pool substrate
- `Custom { transport_id }` — a registered transport for a variant outside the set, admitted through source approval (File 06 §9)

Cross-device propagation is not a `TransportKind`: the bus does not cross devices; the sync layer (File 21) propagates state across a user's devices.

### 10.3 Rule

- Every `Transport` preserves the canonical event contract: the full `EventEnvelope` (File 10 §5.2), the per-`sequence_scope` monotonic ordering, the sensitivity labels and filtering (no raw `Secret` crosses any cross-process transport, File 22 §4), and the delivery classes and aggregation policies (File 10 §5.5). Payloads preserve sensitivity labels and are redacted before logging, persistence, projection, diagnostic display, export, or model context. Transported messages carry `SecretRef`s or capability-scoped handles by default; raw secret material is not serialized across process boundaries except through the explicit File 22/File 23 credential-injection mechanisms. A transport is a wire, never a re-interpretation of the event model and never a durable store.
- The frontend bridge carries the three state classes (`codex_recommendations.md` §3.2): Rust-authoritative replicated state flows core→shell as events the shell renders; session-ephemeral view state lives only in the shell; optimistic mutation envelopes flow shell→core and reconcile against the authoritative event stream, with the core as the single writer of durable state. An optimistic mutation envelope carries a correlation identity and resolves through an authoritative outcome: confirmed, rejected, or superseded. Rejection (policy denial, validation failure) or supersession (a concurrent authoritative change) rolls the shell back to authoritative state and surfaces the typed outcome; File 37 owns rendering, but this file owns the transport contract. The shell never becomes a second source of truth.
- Transports are backpressure-aware: a bounded buffer per subscriber, `EventBufferOverflow` on overflow with the subscriber marked degraded (File 10 §5.1), and end-to-end backpressure where a slow consumer pauses its producer. High-frequency streams are aggregated under the delivery policy before crossing a transport (File 10 §12.3), not delivered per-chunk.
- Reconnection is identity-preserving and resumable best-effort: a disconnected client reconnects and requests resume from its last-seen `event_id` within the transport's bounded buffer; when the range cannot be replayed, the transport returns a typed gap signal and the client reloads durable projections then resumes the live tail (`ledger.streaming-live-partials`, File 10 §12.5). Resume tokens are conveniences, not durability guarantees.
- Network transports run on the connection-pool and idle-reaper substrate this file owns (the substrate File 17 and File 36 run their adapters and sessions on): connections are pooled, reference-counted, idle-reaped on a `RuntimeTimer` deadline (§8), and never health-pinged on a schedule (File 17 §12.4, File 36 §7.5). The pool is the substrate; the provider and connector retry and reconnect *policy* over it is Files 17 and 36's.

### 10.4 Boundary

This section owns the transport implementations, the closed `TransportKind` set, the frontend-bridge contract, and the connection-pool substrate. The event model, envelope, ordering, delivery classes, and resume contract are File 10's; the secret boundary is File 22's; the egress policy a `Network` transport passes is File 22's; the native-messaging session protocol and the connector reconnect policy are File 36's; cross-device propagation is File 21's; the UI rendering on the other side of the frontend bridge is Files 37 and 38's.

## 11. Application Lifecycle: Startup

Anchor: `runtime.startup`

### 11.1 Definition

Startup is the ordered, deterministic boot graph that brings the application from process launch to a usable steady state. It composes the storage phases (File 20 §13.3), the bus/registry/hook phases (File 10 §13.2, §17.1), the capability-registration phases (File 05 §16.1), and the runtime phases this file adds, into one ordered sequence the `Runtime` orchestrates.

### 11.2 Purpose

Every persistence and registration contract requires deterministic reconstruction across restart (File 20 §13.2). Startup is where those reconstructions, the service wiring, the worker spawning, and the trigger re-arming happen in one ordered, recorded sequence, so that a new run after restart sees the same materialized state it would have seen before, modulo recorded offline changes, and so that a failure in one phase is isolated and recoverable rather than corrupting the next.

### 11.3 The Canonical Boot Graph

The `Runtime` brings the application up in this order; each step names its owner, which owns the step's internals while this file owns the ordering and the determinism guarantee:

1. **Bootstrap resolution** — read the `BootstrapConfig` once (§14): resolve the data root, the storage paths, the vault path, the logging baseline, the configuration overlay, and the startup-only flags. Validate; on failure exit with a structured, actionable typed error.
2. **Single-instance acquisition** — acquire the single-instance lock; hand off to a running instance and exit if one holds it; reclaim a stale lock (§4.4).
3. **Logging and tracing init** — initialize the structured logging and tracing baseline (File 41 §4) so all subsequent phases are instrumented.
4. **Storage open and integrity** — open and integrity-check the substrate; take the pre-migration backup; run forward-only migrations after backup; on migration failure roll back and stop with a typed error (File 20 §10, §12, §13.3).
5. **Cache warm and projection rebuild** — warm hot caches; rebuild and verify projections, healing stale or incomplete ones from the durable substrate (File 20 §7; `codex_recommendations.md` §11.2).
6. **Bus and transports** — initialize the event bus and the transports (§10), subscriber registry empty.
7. **Service composition** — construct the `ServiceGraph` (§9): wire the typed static services; on a fallible service's failure, fail startup or degrade per its declaration.
8. **Capability and hook registration** — register capability declarations and hook subscriptions in the canonical order (built-in → subsystem → plugin → MCP → API → user-defined), each registration failure recorded and the unit marked unavailable without aborting startup (File 05 §16.1, File 10 §13.2).
9. **Settings resolution** — resolve the settings cascade and spawn settings-change watchers (File 15).
10. **Vault unlock** — unlock the secret vault per its policy (eager, on-demand, or deferred) (File 22); credentials resolve at point of use thereafter.
11. **Warmers and health checks** — warm world-graph state (File 18), refresh the provider model catalogue as the implicit connectivity check (File 17 §12.4), and run capability health checks (`codex_recommendations.md` §11.2), each non-blocking and degrading gracefully on failure.
12. **Worker spawn and supervision** — spawn the canonical background workers and register them with the `WorkerSupervisor` (§6), placing the one `Scheduler` and the watch poller in the graph (File 33 §9).
13. **Recovery and reconciliation** — recover interrupted runs and reconcile orphans, surfacing resume-or-discard affordances and never auto-resuming (File 04 §17.3, §13); re-arm triggers and reconcile missed fires under the cold-start guard (File 33 §3.4, §18); clean or revalidate stale leases (File 06 §11.6).
14. **Frontend bridge / front-end open** — open the frontend-bridge transport and the UI shell, or the terminal interface, or nothing in headless mode (§9.4, §10).
15. **Steady state** — commit `AppStarted` with the settings and registry snapshot identities (File 10 §4.1); the application is usable.

### 11.4 Rule

- Startup is idempotent and deterministic: re-running it over the same durable substrate produces the same steady state, and replay reads `AppStarted` to know the state in effect (File 10 §17.1). Phase ordering is fixed; a later phase depends only on earlier ones.
- Startup isolates and surfaces errors. A phase failure that compromises a core invariant (storage corruption with no recovery source, a failed migration) stops startup with a typed, actionable error and rolls back to the last-known-good state (File 20 §12.3); a phase failure that only disables a feature (a sidecar that will not start, a provider that will not authenticate, a plugin that fails to load) is recorded, degrades that feature gracefully (§16), and does not abort startup (`infrastructure/lifecycle.md`).
- Startup is observable by phase: each boot phase emits typed runtime facts for start, completion, degradation, and failure where consequential, as `Custom { namespace: "runtime" }` entries under the one bus and ledger (§19.2), not as new top-level event kinds. The facts include phase id, owner subsystem, required-versus-degradable classification, dependency ids, and typed failure or degradation reason.
- Startup is responsive: phases that are not prerequisites for a usable UI (provider warmers, projection verification of cold data, sidecar readiness, indexer warm-up) run as background work after the bridge opens, so the application is interactive against cached and rebuilt state while warmers stream in. The responsiveness budget is a setting; the contract is that the UI opens against a consistent state, never against a half-migrated or unverified substrate. A capability that depends on a still-warming background phase returns a typed warming/not-ready state, or waits or queues only when that capability explicitly supports doing so and the work is admitted under the `WorkQueue`, shutdown, and backpressure rules. It never returns silently incomplete results. This warming state is distinct from degraded unavailable-backend mode (§16): it is transiently not-ready and derives from startup-phase readiness facts.
- Startup performs no work whose absence is a correctness condition on a timer: latency envelopes are responsiveness targets, not correctness deadlines, and a slow phase on weak hardware delays readiness rather than skipping a required step.

### 11.5 Boundary

This section owns the ordered boot graph and the determinism, isolation, and responsiveness rules. The storage phases are File 20's; the bus/hook/registration phases are Files 10 and 05's; the settings cascade is File 15's; the vault unlock is File 22's; the warmers and health checks are Files 18, 17, and 05's; the worker work is each worker's owning spec's; the orphan-run policy is File 04's; the trigger re-arm is File 33's; the UI is Files 37 and 38's.

## 12. Application Lifecycle: Shutdown and Drain

Anchor: `runtime.shutdown`

### 12.1 Definition

Shutdown is the ordered sequence that stops accepting new work, drains in-flight work to a safe boundary, flushes durable state, reaps processes and workers, releases the single-instance lock, and exits. It composes File 10 §13.4 and File 20 §13.4 into the application-wide shutdown the `Runtime` orchestrates.

### 12.2 Purpose

The application must be ready to close at any time without losing a committed fact. A graceful shutdown completes in-flight work and flushes pending state where it cheaply can; correctness, however, comes from commit boundaries and restart reconciliation, not from waiting on a drain timer, so that a hard close, a crash, or a power loss loses only work-in-flight, never committed work.

### 12.3 The Shutdown Sequence

On a shutdown signal (a termination signal, a user interrupt, a window-close, an operating-system shutdown):

1. set the shutting-down flag and apply shutdown admission classes: admit `ShutdownCritical` work, continue or reconstruct `AlreadyAcceptedDurable` work, park or defer `Deferrable` work, and reject `RejectNew` work with a typed result;
2. emit `AppShuttingDown` with the configured grace policy (File 10 §4.1), so the UI disables new actions and shows a saving indicator;
3. signal in-flight runs and workers cooperatively through the global intervention cancellation token (§15) and File 04's cancellation contract — ask in-flight work to wrap up, drain queues to a safe boundary;
4. flush acknowledged critical ledger and audit-overlay records synchronously, and best-effort flush noncritical buffers and the frontend log batch (File 10 §13.4; `unit02-cross-cutting-infra-and-presentation.md`);
5. complete the storage shutdown — commit or roll back pending transactions at safe boundaries, checkpoint the write-ahead log, close the substrate (File 20 §13.4);
6. reap sidecars, helpers, processes, and sandboxes through File 23's kill contract (cooperative termination, then forceful escalation, in the declared shutdown order, File 23 §10, §6.3), discarding or orphaning staged partials per capability declaration;
7. release the single-instance lock, commit the final lifecycle state when safely possible, emit `AppStopped`, and exit.

### 12.4 Rule

- Shutdown correctness does not depend on a drain timer (File 10 §13.4): a successful critical commit is durable before success is reported, in-flight drain is best-effort, and a forced-shutdown backstop is a finite safety guard armed as a `RuntimeTimer` (§8), never a correctness condition. On the backstop's expiry the `Runtime` forcefully terminates remaining units (File 23 §10) and records the forced outcome; it never reports clean completion of work it abandoned.
- Drain is event-driven, not polled: the `Runtime` waits on the completion events of the in-flight units and the drained queues, not on a clock loop, and the backstop is the deadline that bounds the wait deterministically (the `DrainableWorker` shape — synchronize on completion, not on a sleep).
- Shutdown admits no new user, automation, connector, or agent-initiated consequential work after the shutting-down flag unless that work was already accepted durably before shutdown. New external invocations fail or park with a typed `RuntimeShuttingDown { retry_after_restart: true }`-style result; they never silently enter an in-memory-only queue.
- A forceful shutdown (crash, kill, power loss) loses in-flight events but no acknowledged durable fact; the next startup detects and reconciles orphans (§13). The `Runtime` treats every shutdown path — graceful, forced, crashed — as recoverable on the next boot.
- Shutdown is non-destructive: it commits or rolls back at safe boundaries and discards only staged partials a capability declared non-meaningful (File 04 §17.3); it deletes no durable user content.

### 12.5 Boundary

This section owns the application shutdown orchestration and the commit-boundary-correctness rule. The storage flush and close are File 20's; the cooperative-then-forceful kill is File 23's and File 04's; the lifecycle event kinds are File 10's; the orphan reconciliation on the next boot is §13.

## 13. Crash, Restart, and Recovery

Anchor: `runtime.crash-recovery`

### 13.1 Definition

Crash recovery is the set of rules by which the next startup returns the application to a consistent state after an unclean shutdown: reconciling orphan runs, reaping orphan processes and sandboxes, reconstructing runtime handles, and rolling back a bad update. It is the recovery side of the lifecycle, realized in the boot graph (§11).

### 13.2 Rule

- **Orphan runs are surfaced, never auto-resumed.** A run that was `running` or `cancelling` at restart transitions to `failed` with the typed reason `process_restart_orphan` unless its capability declared `resume_on_restart` and provides a resume handler (File 04 §17.3); the user is presented a per-run resume-or-discard affordance. The `Runtime` never auto-resumes an orphan run at startup (`run.explicit-rejections`, File 04 §28). A capability with a resume handler has it invoked, and the handler revalidates and either continues or fails with a specific typed reason.
- **Orphan processes, sandboxes, and process groups are reaped.** A `ManagedProcess` handle is a transient runtime-handle projection that does not survive restart (File 23 §14); the `Runtime` reaps orphaned processes, sandboxes, and groups left by the prior process rather than reconnecting to their stale handles (File 23 §10.3), except where a capability declared genuinely resumable infrastructure and a resume handler revalidates before resuming.
- **Runtime handles are reconstructed, not restored.** Active subscriptions, worker handles, watcher handles, connection-pool entries, armed timers, and the scheduler's arming state are runtime-handle projections (File 20 §7.3) rebuilt at startup from durable declarations and the ledger (§21); their loss across a restart is a rebuild, never a loss of identity or accepted durable work.
- **A bad update rolls back.** A startup whose self-checks fail (substrate schema integrity, settings loadable, core services startable, required extensions loadable) rolls back to the last-known-good state, restoring the pre-migration backup (File 20 §12.3); a successful startup after an update records a new last-known-good marker.
- **Recovery is recorded and surfaced, never silent.** An unclean prior shutdown is detected (a not-cleanly-cleared running marker), the recovery actions are recorded as typed facts, and a recovery that lost work-in-flight surfaces it to the user; the `Runtime` never reports a clean start over a recovery gap.

### 13.3 Boundary

This section owns the application-level crash recovery orchestration. The orphan-run reconciliation policy is File 04's; the process and sandbox reaping is File 23's; the storage integrity, last-known-good, and reconstruction internals are File 20's; the trigger re-arm and missed-fire reconciliation are File 33's; the lease revalidation is File 06's.

## 14. Bootstrap Configuration

Anchor: `runtime.bootstrap-config`

### 14.1 Definition

`BootstrapConfig` is the startup-only configuration the `Runtime` reads before the settings service exists, to locate the application home and primary storage, the secret-vault path, the logging baseline, the configuration overlay, and the startup-only flags. It is read once, at the first boot-graph step, from the process environment and a configuration file under the application home.

### 14.2 Purpose

The settings service cannot configure where its own database lives or what log level to initialize with, because it does not yet exist when those decisions are made. `BootstrapConfig` is the minimal, startup-only configuration that bootstraps the substrate the settings service is then built on — the boundary `settings.bootstrap-boundary` (File 15 §12) delegates to infrastructure.

### 14.3 Rule

- `BootstrapConfig` resolves at minimum: the application home / data root, the primary storage path, the secret-vault path, the logging-baseline level, the configuration-overlay path, an updater-disable flag, and a developer/debug-affordance flag. The committed realization reads a small set of namespaced environment variables (an application-home variable, a database-path variable, a vault-path variable, a log-level variable, a configuration-overlay variable, an updater-disable variable, and a debug flag) and a configuration file under the data root; exact names are the realization, defined here as the bootstrap contract (`atlas3-core/CONSTRAINTS.md`'s startup-only variable set), and a missing configuration file is created with safe defaults rather than failing.
- `BootstrapConfig` is read exactly once, at bootstrap resolution; it is not re-read on a clock and is not a runtime settings source. It does not override registered settings after startup (`settings.bootstrap-boundary`, File 15 §12); a value meaningful to vary at runtime is a setting, not a bootstrap variable (`settings.settings-over-constants`, File 15 §13).
- `BootstrapConfig` may carry secret injection for first-run provisioning, but a secret so injected is moved into the vault and never persisted to the bootstrap file or a log (File 22 §4); the bootstrap path honors the secret boundary like every other path.
- A configuration-overlay reload — a runtime re-read of the overlay file without a restart — feeds the settings reactivity (`infrastructure/configuration.md`'s live reload; the configuration-reload signal), updating the resolved settings cascade through the normal change events, not by mutating `BootstrapConfig` or bypassing the cascade. The bootstrap variables themselves (data root, storage path) are not live-reloadable; changing them requires a restart.

### 14.4 Boundary

This section owns the `BootstrapConfig` contract and the read-once, not-a-runtime-source rule. The settings cascade and the bootstrap-versus-runtime classification are File 15's; the data-root and file placement are File 20's; the vault is File 22's; the logging baseline is File 41's.

## 15. The Global Intervention Cancellation Token

Anchor: `runtime.cancellation-token`

### 15.1 Definition

The `Runtime` maintains a global intervention handler with a cancellation token shared across the agent loop, long-running tool calls, sandbox operations, service calls, workers, and queued work. A user-initiated interrupt sets the token; every cooperative unit checks it at safe points and aborts cleanly. This is the runtime realization of `ledger.lifecycle-integration` (File 10 §17.3) and the substrate of File 04's cancellation contract.

### 15.2 Rule

- The token is shared and hierarchical: a run's shared cancellation signal (File 04 §17.3) is a scoped child of the runtime token, so a global interrupt cancels everything and a per-run cancel cancels one run and its tree. Every spawned unit (§5.3) receives the appropriate token and checks it at safe cancellation points.
- Setting the token is recorded as `InterventionRecorded` (File 10 §14.2); the cancellation it drives records through File 04's cancellation entries (File 10 §14.1). The token is the mechanism; the cancellation semantics, deadlines, and partial-output rules are File 04's, and the process kill is File 23's.
- The token honors cooperative-then-forceful escalation: a unit that does not stop cooperatively within its deadline (a `RuntimeTimer`, §8) is forcefully terminated through File 23's kill contract; the runtime never relies on cooperation alone for a unit that must stop.

### 15.3 Boundary

This section owns the global token's maintenance and propagation. The cancellation contract, deadlines, and partial-output rules are File 04's; the process and sandbox kill is File 23's; the intervention and cancellation event recording is File 10's.

## 16. Operational Health and Remediation

Anchor: `runtime.operational-health`

### 16.1 Definition

Operational health is the `Runtime`'s live assessment of whether its workers, processes, connections, providers, storage, and sidecars are functioning, and remediation is the action it takes when they are not — restart, route-around, degrade, or surface. This is the operate side of the observe-not-operate seam with File 41 (`observability.health`, File 41 §11.2).

### 16.2 Purpose

Something must actually restart a stalled worker, reap a crashed sidecar, open a circuit breaker on a failing connection, and degrade a feature whose backend is unavailable. File 41 only observes; this file is where health drives action, so that the application self-heals where it safely can and degrades transparently where it cannot.

### 16.3 Rule

- The `Runtime` consumes the typed liveness and health facts the substrate produces — `WorkerState` transitions (§6), `ProviderHealth` (File 17 §12), connector `ConnectionState` (File 36 §7), storage integrity events (File 20 §12), sidecar readiness (§4.5) — and drives remediation from them, event-first. It infers health from facts, never from a scheduled health ping (File 17 §12.4, File 36 §7.5); the one deadline shape is the missed-heartbeat watchdog (§6.4).
- Remediation follows a `RemediationPolicy` per unit: restart under the `SupervisionPolicy` (§6.5), route around a degraded provider or connector (the selection layer skips it, File 16; File 36), open a circuit breaker against a persistently failing one, degrade the dependent feature with a typed reason, or surface a setup or repair step to the user. Remediation never silently masks a deterministic failure: a unit that fails repeatedly trips its circuit and notifies, rather than restarting into a failing condition forever.
- Degraded-mode operation is first-class and graceful: a feature whose backend (a sidecar, a provider, a connector, a hardware-dependent capability) is unavailable is disabled with a typed reason and a re-enable path, independent features continue, and the degradation is surfaced as state, never as a crash or a silent absence (`world.environment-temporal-connection-facts`, File 18 §6; File 23 §15.3). The application starts and runs with any subset of optional backends available.
- The `Runtime` operates; it does not observe in File 41's sense. It emits the worker, process, and remediation facts; File 41 projects the health view and renders the health card. There is no observability projection inside the `Runtime` and no remediation watchdog inside File 41.
- Health-driven action is recorded and policy-bound: a restart, a circuit-open, a route-around, and a degrade each record a typed fact, including whether the action was automatic, policy-approved, user-approved, or rejected. Automatic remediation is limited to declared idempotent runtime mechanics under `SupervisionPolicy`: restarting a worker, re-arming a timer, routing around an unavailable optional backend, or reaping an orphaned runtime process. A remediation that crosses a policy, security, user-data, credential, or user-visible side-effect boundary — restarting an elevated helper, re-establishing a credentialed connection, deleting or cleaning durable data, changing settings, relaunching, or enabling a disabled backend — passes the owning layer's capability and policy path (Files 05, 06, 22), with typed confirmation where required, never a privileged side door.

### 16.4 Boundary

This section owns operational health assessment and remediation. The health-status data contract, the metric and trace projections, and the health-card rendering are File 41's; the `ProviderHealth` state machine is File 17's; the connector `ConnectionState` is File 36's; the storage integrity and recovery are File 20's; the process kill is File 23's; the model route-around is File 16's.

## 17. Runtime Resource Governance

Anchor: `runtime.resource-governance`

### 17.1 Definition

Runtime resource governance is the `Runtime`'s management of the in-process resources it owns — the concurrency caps, the worker and connection pools, the queue depths, the buffer sizes, and the load it admits — to keep the application bounded and responsive under pressure.

### 17.2 Rule

- The `Runtime` governs the resources of the core process: worker-pool sizes and concurrency caps, connection-pool sizes and idle-reap deadlines, queue depths and backpressure thresholds, and event-buffer sizes. Each is a setting with a conservative default (`settings.settings-over-constants`, File 15 §13); the `Runtime` imposes no hidden ceiling and never silently single-instance-locks to limit load (§5.3).
- Runtime resource governance is distinct from, and composes with, the two adjacent budget layers: per-sandbox resource limits (memory, processor, process count, descriptors, disk, output, the wall-clock safety guard) are File 23's (`sandbox.resource-limits`, File 23 §9), enforced at the operating-system level on spawned processes; per-run and per-stage budgets (model steps, tool calls, child-run depth, context, output, provider) are File 04's (`run.budgets-limits`, File 04 §21), opt-in and enforced on a run. The `Runtime` owns the in-process pools and caps beneath both; it duplicates neither.
- Load shedding is graceful, deterministic, and typed: under genuine resource pressure the `Runtime` sheds or coalesces the lowest-priority deferrable work first (coalescible and diagnostic work before consequential commits), applies backpressure to producers, and surfaces the pressure (composing the context-pressure and budget-warning boundaries, File 04 §20.1, §21), never dropping a consequential commit or crashing under load. Admission classes define ordering and fairness; low-priority work that remains deferred surfaces as backlog or degraded state rather than starving silently.
- The `Runtime` observes its own resource consumption as facts it emits for File 41's resource metric family (File 41 §6.3, §8.5); it consumes File 41's resource gauge only as an input to governance, and the resource gauge's sampling is File 41's one flagged periodic exception, not a runtime poll.

### 17.3 Boundary

This section owns in-process resource governance and load shedding. Per-sandbox limits are File 23's; per-run budgets are File 04's; the resource metric and gauge are File 41's; the storage connection pool's sizing is File 20's (§4) and this file governs no storage-internal concurrency.

## 18. Update Application and Relaunch

Anchor: `runtime.update-relaunch`

### 18.1 Definition

Update application is the relaunch mechanics by which a staged update becomes the running application: the `Runtime` sequences the drain, the relaunch, and the post-update verification, consuming the staged update the future Packaging spec produces and the last-known-good guard File 20 maintains.

### 18.2 Rule

- An update is applied on restart, never in place on a running core: the future Packaging spec stages the new version and signals readiness; the `Runtime` performs a graceful shutdown (§12), relaunches into the staged version, and runs the startup self-checks (§11.4). A mutate-the-running-installation update is rejected.
- A relaunch is sequenced, not abrupt: the `Runtime` drains in-flight work to a safe boundary (§12), records that the restart is an update relaunch (so recovery distinguishes it from a crash), relaunches, and on the next startup verifies the update self-checks and either records a new last-known-good marker or rolls back to the prior one (File 20 §12.3).
- A self-initiated relaunch (a configuration change requiring restart, a recovery escalation, a user-requested restart) uses the same drain-relaunch-verify path and is a user-gated or policy-gated operational capability (§19), never a silent self-restart loop.
- The update channel, the download and staging, the signature and integrity verification of the new binary, the installer, and the platform crash-handler and native-messaging-host registration are the future Packaging spec's; the drain, relaunch, and post-update verification mechanics are this file's.

### 18.3 Boundary

This section owns the apply-on-restart and relaunch mechanics. The update channel, staging, and binary integrity are the future Packaging spec's; the last-known-good marker and self-check rollback are File 20's; the graceful shutdown and startup sequences are §§11–12.

## 19. The Capability Surface and Events

Anchor: `runtime.capability-surface-events`

### 19.1 The Capability Surface

The `Runtime` exposes its read and operational facts and controls as canonical capabilities (declared per File 05, gated per File 06), surface-and-service in nature, with no runtime-mode field:

- `runtime.query_health()` — the operational-health snapshot the `Runtime` operates on (the operate-side counterpart of File 41's `observability.query_health`); `ReadOnly`
- `runtime.list_workers()` / `runtime.list_processes()` / `runtime.list_transports()` — enumerate the supervised workers, the owned processes (composing File 23's process listing), and the active transports; `ReadOnly`
- `runtime.restart_worker(worker_id)` — restart a supervised worker through the `WorkerSupervisor`; `UserApproval`
- `runtime.reload_overlay()` — re-read the configuration overlay into the settings reactivity (§14.3); `UserApproval`
- `runtime.relaunch(reason)` — perform a drain-relaunch (§18); `UserApproval`, and typed-confirmation where in-flight work would be interrupted
- the process spawn, kill, and sandbox capabilities are File 23's (`sandbox.capability-surface`, File 23 §17); the scheduler and automation capabilities are File 33's; the `Runtime` adds no parallel process or scheduling capability

Reads are `ReadOnly` and agent-invocable under the standard agent-exposure rules; operational controls (restart, relaunch, overlay reload) are user-gated and policy-bound — an agent may propose a restart or relaunch but does not perform one unattended, and the lifecycle controls carry the tier their blast radius warrants.

### 19.2 Events

The `Runtime` emits and consumes through the one event bus (File 10 §5), reusing the reserved lifecycle and worker entries — `AppStarted`, `AppShuttingDown`, `AppStopped`, `BackgroundWorkerSpawned`, `BackgroundWorkerHeartbeat`, `BackgroundWorkerStopped`, `BackgroundWorkerFailed` (File 10 §4.1) — and registering runtime-specific facts (a worker `CircuitOpen`, a sidecar readiness transition, a transport reconnect, an update relaunch, a remediation action) as `Custom { namespace: "runtime" }` extensions (File 10 §4.3). It introduces no new top-level event or ledger-entry kind and no parallel bus. Consequential facts (lifecycle transitions, worker failures, remediations, relaunches) commit to the ledger; transient runtime coordination (heartbeats under their delivery class, pool churn) flows on the bus per its delivery class. A security-relevant operational action (an elevated-helper restart, a relaunch) records into the audit overlay (File 10 §16.4).

### 19.3 Boundary

File 05 owns the capability declaration and registry; File 06 owns the policy gating; File 10 owns the envelope, the catalogue, the delivery split, and the reserved entries; File 23 owns the process and sandbox capabilities; File 33 owns the scheduler and automation capabilities. This section declares the runtime capability set and event vocabulary.

## 20. Settings

Anchor: `runtime.settings`

Every runtime mechanism with meaningful variation is configurable through `settings.setting-definition` (File 15), with namespaced keys (`runtime.*`) declaring scope, agent exposure (`policy.agent-exposure-policy-settings`, File 06 §16.4), locality, and export/sync behavior. Runtime settings that bind to one device or platform default to device-local unless their declaration proves portability. At minimum, settings support:

- the asynchronous-runtime concurrency caps (global and per workload class) and the blocking-offload pool sizing;
- per-worker `SupervisionPolicy` defaults — restart-on-failure, backoff strategy and bounds, circuit-breaker threshold and cooldown, and the missed-heartbeat deadline — per worker and as a category default;
- registered workers' enablement, idle heartbeat cadence, and missed-heartbeat deadline (the work cadence each worker needs is its owning spec's setting, surfaced here as the dimension the runtime hosts);
- `WorkQueue` depths, overflow policies, and backpressure thresholds per queue;
- connection-pool sizes, idle-reap deadlines, and per-transport buffer sizes;
- the startup responsiveness budget and the phase-failure degradation defaults;
- the shutdown grace policy and the forced-shutdown backstop deadline;
- the single-instance handoff behavior and stale-lock-reclaim policy;
- the sidecar and managed-service lifecycle defaults (start condition, health signal, supervision policy, shutdown order);
- the configuration-overlay live-reload enablement;
- the update-relaunch policy and the updater-disable flag's runtime surface;
- the operational-health remediation thresholds and degraded-mode notification policy.

Specific defaults belong to tested settings profiles, not hardcoded constants (`settings.settings-over-constants`, File 15 §13). Agent exposure of runtime settings is conservative: the lifecycle, supervision, and resource-governance settings are `OnRequest` to read; their mutation and the lifecycle controls (restart, relaunch) are user-gated; no runtime behavior is a hidden hardcoded branch where a meaningful variation exists. Device-local runtime settings include data-root-derived paths, lock and handoff details, process and connection pool sizing, sidecar binary paths, platform integration, transport buffers, and resource limits. Portable runtime settings are allowed only when platform-independent, such as user-facing relaunch preference, feature enablement, or display policy declared safe to sync or export.

## 21. Persistence, Locality, and Replay

Anchor: `runtime.persistence-replay`

### 21.1 What Is Durable, Computed, and Device-Local

- **Durable (owned by other layers, referenced here):** the `BackgroundWorker` *declarations* (which workers exist, their owner, supervision policy, reconstruction source, and idempotency or completion-marker rule — settings and capability declarations), the managed-service *definitions* (sidecar lifecycle declarations), and the accepted durable work the queues represent (a queued automation fire keyed by `fire_id`, File 33 §12.2; a staged upload) — all durable through their owning substrate (Files 15, 33, 20), never a parallel runtime table. A `WorkQueue` entry for durable work is only a handle to that owning record.
- **Computed / runtime-handle projections (this file's transient state):** the live worker handles, the armed `RuntimeTimer`s, the active subscriptions and connection-pool entries, the transport sessions, the `ServiceGraph`'s resolved service set, the in-memory `WorkQueue` contents, and the operational-health snapshot. These are runtime-handle projections (`storage.projection-store`, File 20 §7.3), rebuilt at startup from durable declarations and the ledger; their loss across a restart is a rebuild, never a loss of identity or accepted durable work.
- **Device-local:** the runtime's process identity, the single-instance lock, the connection-pool and transport state, and the resolved health snapshot are device-local and never sync (`storage.physical-layout-locality`, File 20 §8.3); the `Runtime` is a per-device host, and a definition that syncs (a worker or sidecar declaration) re-resolves its runtime handles on the importing device.

### 21.2 Reconstruction and Replay

- The `Runtime` reconstructs its runtime state deterministically at startup from durable declarations and the ledger (§11, §13); it re-derives nothing from a live mutable source and re-queries no live endpoint for a historical fact (`context.assembly-replay-snapshot`; `provider.token-source`, File 17). A worker, a timer, a pool entry, and a service handle are rebuilt, not restored from a stale handle.
- Replay reads recorded lifecycle and worker facts; it re-runs no startup phase and re-spawns no live process for a historical view (File 23 §14.3). The `AppStarted` entry's snapshot identities (File 10 §17.1) anchor the state in effect for a replayed run.
- This file defines no new hash and no new canonical encoding; every identity and integrity record it touches reuses the ledger, storage, and block hashes of Files 10, 20, and 08, each computed over a declared `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14), never over physical bytes.

### 21.3 Boundary

This section owns the durable-versus-runtime-handle split for runtime state and the reconstruction-from-declarations rule. Storage realization is File 20's; sync and the portable bundle are File 21's; the worker, sidecar, and queued-work declarations are owned by their declaring specs (Files 33, 15, 04); the replay engine is File 40's.

## 22. Operating Constraints

Anchor: `runtime.operating-constraints`

The `Runtime` operates under these constraints, all configurable as settings (§20) with the stated canonical defaults:

- **Substrate, not engine.** The `Runtime` never becomes a second run model, scheduler, ledger, queue-of-record, or store; it hosts the canonical ones. A consequential fact is a `LedgerEntry`, a scheduled fire is the one `Scheduler`'s, a durable write is the `StorageEngine`'s.
- **Event-first.** Supervision, health, dispatch, and reconnection are event-driven; the one flagged periodic shape is the per-worker missed-heartbeat watchdog computed as a deadline (§6.4); a periodic scan is a flagged fallback only where no timer can be armed and no change event exists; tight clock-polling is rejected.
- **Killable and recoverable by construction.** Every worker, queue, timer, transport, and helper process is cancellable and reapable; shutdown correctness comes from commit boundaries and restart reconciliation, not a drain timer; no orphan run auto-resumes.
- **Local-first and never-block.** The application starts and runs against local state with any subset of optional backends available; a sidecar, provider, connector, sync, or network failure degrades a feature gracefully and never blocks core startup or the local experience (`infrastructure/sync.md`'s never-block invariant).
- **No hidden ceiling, no silent single-instance lock.** The `Runtime` imposes no hidden resource limit and single-instance-locks no backend, session, process, or connection (`run.explicit-rejections`, File 04 §28); parallelism is first-class and demultiplexed.
- **Secret boundary across every transport and process.** No raw `Secret` crosses a cross-process transport or enters a spawned process except as Files 22 and 23 permit; transports preserve sensitivity labels and redaction boundaries; the core process never elevates.
- **Operate, do not observe.** The `Runtime` operates and remediates; it computes no observability projection and surfaces its decisions through File 41's data contracts; File 41 observes and owns no watchdog.
- **No silent failure.** A worker restart, a circuit-open, a remediation, a degradation, a recovery gap, a queue overflow, and a forced shutdown each record a typed fact; nothing restarts, degrades, drops, or disappears without a recorded transition.

## 23. Explicit Rejections

Anchor: `runtime.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel run model, scheduler, ledger, queue-of-record, or store inside the runtime — the `Runtime` hosts the one of each; it adds no second engine
- a background or automated execution path that is a separate architecture from the run model — a trigger-originated run is an ordinary `Run` (`run.explicit-rejections`, File 04 §28); background work runs on the same model, ledger, and policy
- a tight clock-poll loop as a worker's, monitor's, or supervisor's mechanism — workers are event-first, the scheduler arms a single timer, the missed-heartbeat watchdog is a re-armed deadline, and a periodic scan is a flagged configurable fallback only
- inferring worker, provider, or connection health from a scheduled health ping — health is observed from call outcomes and typed liveness facts; the model-catalogue refresh is the implicit connectivity check; a scheduled ping is rejected (File 17 §12.4, File 36 §7.5)
- a detached, unowned, unkillable spawned task — every spawned unit belongs to a worker, a run, or a request handler and is cancellable and reapable; fire-and-forget is modeled as a tracked unit with a recorded outcome
- auto-resuming an orphan run at startup — orphan runs transition to `failed` with `process_restart_orphan` and are surfaced with a resume-or-discard affordance, never silently resumed (`run.explicit-rejections`, File 04 §28)
- reprocessing in-flight durable work after worker restart without idempotency, idempotency keys, or an owning durable completion marker — worker restart must not double-execute a committed side effect
- reconnecting to a stale process or sandbox handle after restart instead of reaping it — handles are transient projections; orphans are reaped (File 23 §10.3), and only a declared resumable-infrastructure capability revalidates and resumes
- returning silently incomplete capability results while a startup phase the capability depends on is still warming — the capability returns typed not-ready/warming state or explicitly waits or queues under admission policy
- a shutdown whose correctness depends on a drain timer — correctness comes from commit boundaries and restart reconciliation; drain is best-effort and the forced-shutdown backstop is a finite safety guard, never a correctness condition
- accepting new external consequential work into an in-memory-only queue after shutdown begins — shutdown admits only shutdown-critical work or already-accepted durable work
- mutating a running installation to apply an update — updates apply on restart with a staged version and a last-known-good rollback guard (File 20 §12.3); a silent self-restart loop is rejected
- a bundled local network server of record as the frontend transport, or a fixed application port — the frontend bridge is native inter-process communication; the application binds no application-level network port of record; loopback ports are sidecar/webhook/optional-collector-only and dynamically allocated
- a single-instance design that races on a fixed port instead of a lock with running-instance handoff and stale-lock reclaim
- trusting or reclaiming a single-instance lock without verifying owner identity for the current data root, or accepting handoff over an unauthenticated non-local channel
- business logic in a command wrapper, the UI shell, or the runtime itself — logic lives in services (the service-layer-ownership rule, File 01 §7.7); the `Runtime` composes and hosts services and the command rails are thin adapters
- a dynamic service registered as a private privileged backend outside source approval, capability registration, and teardown rules
- a service or backend treated as an implicit single-instance lock, or a runtime that serializes parallel runs or parallel calls against the same provider, session, sandbox, or connector (`run.explicit-rejections`, File 04 §28)
- a hidden hardcoded concurrency cap, supervision threshold, queue depth, drain backstop, idle deadline, or buffer size — every one is a configurable setting with a canonical default (`settings.settings-over-constants`, File 15 §13)
- a runtime watchdog inside the observability layer, or an observability projection inside the runtime — the `41↔42` seam is fixed: File 41 observes, this file operates (File 41 §11.2)
- a transport that re-interprets, reorders across a `sequence_scope`, drops the sensitivity filter on, or durably stores the events it carries — a transport is a wire that preserves the canonical envelope, ordering, sensitivity, and delivery classes (File 10 §12.6)
- a frontend shell retaining a rejected or superseded optimistic mutation as if applied — optimistic state must resolve against the authoritative event stream and roll back on rejection or supersession
- raw `Secret` material crossing a transport or injected into a spawned process by default, or the core process running elevated — the secret boundary and the never-elevate-the-core rule hold across every transport and process (File 22 §4, File 23 §11)
- `BootstrapConfig` used as a runtime settings source, or a runtime-meaningful value frozen as a bootstrap variable instead of a setting (`settings.bootstrap-boundary`, File 15 §12)
- a silent restart, circuit-open, remediation, degradation, recovery gap, queue overflow, or forced shutdown — every one records a typed fact and is surfaced where it lost or risked work
- a new top-level `AppEvent` or `LedgerEntryKind` for the runtime, or a parallel runtime bus — the runtime reuses the reserved lifecycle and worker entries and registers `Custom { namespace: "runtime" }` extensions on the one bus

## 24. Consequences for Later Specs

Anchor: `runtime.consequences-for-later-specs`

Every later spec that spawns a worker, defers work to a queue, arms a timer, opens a transport, registers a service, participates in startup or shutdown, or recovers after a crash consumes this layer as defined here. The canonical principles later specs follow:

- run long-lived work as a registered `BackgroundWorker` under the `WorkerSupervisor` with a declared `SupervisionPolicy`, idle heartbeat cadence, missed-heartbeat deadline, shutdown order, durable reconstruction source, and idempotency or completion-marker rule; emit the worker lifecycle facts (File 10 §17.2); never run a private daemon, supervision loop, or poll loop
- defer bursty or rate-governed work through a `WorkQueue` with a bounded depth, admission class, declared overflow policy, and durable-record handle for accepted durable work; never spawn unbounded, drop accepted consequential work, or reprocess durable side effects without an idempotency/completion guard
- express every timing need as a `RuntimeTimer` deadline or the scheduler's armed instant; never poll a clock as a correctness mechanism
- compose services in the `ServiceGraph` with logic in the service and thin command-rail adapters; register runtime services through the source-approved `DynamicServiceRegistry`; keep command-rail, command-line, and headless parity
- carry the canonical event envelope, ordering, sensitivity, delivery classes, secret-reference boundary, and optimistic-mutation correlation outcomes over every `Transport`; never re-interpret or durably store the events a transport carries
- participate in the boot graph and shutdown contract at the assigned phase; make startup idempotent and deterministic; emit runtime phase facts; return typed warming/not-ready state for capabilities whose background startup prerequisite is not ready; degrade a feature gracefully on a non-fatal phase failure; never auto-resume an orphan run; surface every recovery gap
- read startup-only configuration through `BootstrapConfig` and runtime-variable configuration through settings; never freeze a runtime-meaningful value as a bootstrap variable
- emit operational facts for File 41 to project and consume File 41's health view; operate and remediate here, observe there; never put a watchdog in observability or a projection in the runtime

Specific integration contracts:

- the **run model** (File 04) runs on this substrate, honors the global intervention cancellation token, and owns the orphan-run reconciliation policy this file enforces at restart; the **ledger and event stream** (File 10) is delivered over this file's transports and emits its lifecycle and worker events through the one bus; the **settings** (File 15) layer classifies the bootstrap-versus-runtime boundary this file realizes
- the **provider layer** (File 17) and **MCP and external integrations** (File 36) run their adapters, sessions, and reconnect policy on this file's worker, connection-pool, transport, and reaper substrate, and reuse — rather than duplicate — the `ProviderHealth` and `ConnectionState` shapes this file's supervision mirrors; neither is health-pinged on a schedule
- the **storage** (File 20) layer's lifecycle phases are sub-sequences of this file's boot graph and shutdown contract; the single-instance lock it places is acquired here; its last-known-good marker guards the relaunch this file sequences
- the **sandbox** (File 23) layer's processes, sidecars, and elevated helper are spawned, supervised, drained, and reaped within this file's lifecycle and managed-service contract, through File 23's kill-and-reap; this file reimplements no spawning, confinement, or killability
- the **automation** (File 33) layer's `Scheduler` and watch poller are placed in this file's boot graph as supervised workers, arm their next-fire instants against this file's `RuntimeTimer`, and have their triggers re-armed and missed fires reconciled in this file's startup recovery
- the **observability** (File 41) layer projects the worker, process, transport, and remediation facts this file emits and renders the health card; this file operates the remediation it observes, owning the missed-heartbeat watchdog and the liveness classification File 41 declines
- the **memory, retrieval, knowledge, sync, and per-surface** specs (Files 12, 14, 21, 27–32) run their consolidators, indexers, sweepers, sync loops, and monitors as `BackgroundWorker`s on this substrate, and their isolated work as `ManagedProcess`es (File 23) within this file's lifecycle
- the future **Packaging, Platform, and Distribution** spec stages updates this file applies on restart, registers the platform crash handler and native-messaging host this file's recovery and transports consume, and ships the sidecar binary inventory this file runs under its managed-service lifecycle contract; the running lifecycle is this file's, the delivery is Packaging's

## 25. Canonical Rule Anchors

Anchor: `runtime.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `runtime.chosen-model`, `runtime.boundaries-with-adjacent-layers`, `runtime.runtime`, `runtime.process-topology`, `runtime.async-concurrency-substrate`, `runtime.background-workers`, `runtime.work-queues`, `runtime.timers`, `runtime.service-graph`, `runtime.transports`, `runtime.startup`, `runtime.shutdown`, `runtime.crash-recovery`, `runtime.bootstrap-config`, `runtime.cancellation-token`, `runtime.operational-health`, `runtime.resource-governance`, `runtime.update-relaunch`, `runtime.capability-surface-events`, `runtime.persistence-replay`, and `runtime.operating-constraints`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
