# Execution Ledger, Event Stream, and Hooks

## Status

Canonical.

## Scope

This file defines:

- `ExecutionLedger` — the durable, append-only record of every consequential execution fact the runtime produces
- the closed canonical set of `LedgerEntry` kinds, the schema each entry must carry, and the cross-references each entry shares with `Block`, `Artifact`, `Claim`, `Evidence`, `RegisteredCapability`, `Lease`, `ToolSurface`, version-graph commit, and approval record
- `EventStream` — the typed live coordination channel that carries every transient and consequential signal between subsystems, hooks, the UI shell, and external integrations
- `EventEnvelope` — the canonical envelope every event carries, with the demultiplexing identifiers, the per-stream monotonic sequence, the full-granularity timestamp, and the closed sensitivity classification
- `AppEvent` — the closed canonical event-kind catalogue plus the `Custom { namespace, name, payload }` extension mechanism
- `Hook` — the canonical extensibility primitive over the event bus, including the typed decision vocabulary, the priority convention, the authority-class semantics, the per-error-class retry behavior, and the hook-action contract
- the relationship between live `EventStream` and durable `ExecutionLedger`: which events also become ledger entries, which remain transient
- per-call model-call attribution as a load-bearing ledger requirement, with `TokenUsageRecord` schema, `TokenSource` accuracy hierarchy, and cost computation keyed by model identifier (per `core.explicit-rejections`, File 01 §8)
- replay semantics over the ledger: how the ledger plus durable snapshots reconstruct a past execution state deterministically
- the canonical forgery guards (run-status transition guard from `run.termination` (File 04 §22), unkeyed-scalar rejection from `core.explicit-rejections` (File 01 §8), sensitivity-aware persistence)
- sensitivity-aware retention: `Public` / `Sensitive` / `Secret` and what each entails for the ledger, exports, sync, and telemetry
- the hash-chained audit-log tier for security-sensitive operations, retained per-device and excluded from cross-device sync
- the subscription model: how built-in subscribers, subsystem subscribers, plugin and MCP-sourced subscribers, and user-authored subscriptions all register through one path
- the hook-action contract: how a hook decision is produced (in-process handler, registered capability call, shell script over a typed wire protocol, or synthesized event)
- streaming and live partial events, the boundary between a streamed partial and a committed block, and the aggregation policies that govern high-frequency event categories
- lifecycle integration: startup ordering, shutdown flushing, restart resumption, and orphaned in-flight reconciliation
- the settings dimensions every mechanism in this file exposes, with the agent-exposure rules per `policy.agent-exposure-policy-settings` (File 06 §16.4)
- the closed set of explicit rejections covering ledger-bypass, secret leakage, parallel event buses, time-based hook firing, mutable ledger entries, and forgery
- the canonical contract every later spec consumes when it produces or consumes execution facts, emits or subscribes to events, registers a hook, or queries the ledger for replay, audit, telemetry, or evaluation

This file does not define:

- the `Run` lifecycle, the capability-call pipeline, the typed hook-decision authority rules in evaluation context, or the cancellation primitives themselves — File 04 owns those; this file specifies the durable and live recording contracts the pipeline obeys
- the `CapabilityDeclaration` field set, the registered-entry runtime state, or the per-call `CapabilityInvocation` record's structural fields — File 05 owns those; this file specifies what the ledger records about an invocation
- the policy-evaluation algorithm, lease lifecycle, approval router, or approval flows — File 06 owns those; this file specifies how policy events are recorded and how the approval router participates as one hook subscriber
- the `ToolSurface` composition algorithm, surface zoning, or per-lens composition contracts — File 07 owns those; this file specifies the surface-relevant events that flow through this layer
- the `Block` schema, `BlockKind` catalogue, `BlockContent` variants, the block commit validator, or the streaming-to-block commit boundary — File 08 owns those; this file specifies which block-related events flow through and which block-commit events become durable ledger entries
- the entity layer over blocks (`Artifact`, `Claim`, `Evidence`, `Citation`, `Observation`, `Validation`, `Critique`, `Provenance`) or the entity-relevant event vocabulary itself — File 09 owns those; this file specifies the unified bus and ledger they emit through
- the version-graph commit storage, the version-tree action-log algorithms, or the materialized-view rebuild semantics — File 11 owns those; this file specifies which version-commit events flow through and how the ledger references version identities
- the storage schema, on-disk layout, indexing strategy, projection rebuild policies, or per-table durability invariants — File 20 owns those; this file specifies what is durable, what is computed, and the deterministic-reconstruction contract storage must support
- sync, import, export, or portability mechanics — the future Sync, Import, Export, and Data Portability spec owns those; this file specifies which ledger entries sync, which do not (the hash-chained audit log is per-device), and how sensitivity gates participation
- credential storage internals, trust-state cryptography, or secret-vault primitives — the future Security, Credentials, and Trust Boundaries spec owns those; this file specifies the canonical `Secret` sensitivity class and the rule that `Secret` payloads never persist to the durable ledger
- sandbox primitives, process control internals, or isolation mechanics — the future Sandbox, Process Control, and Isolation spec owns those; this file specifies the events sandbox and process operations emit and the `backend_id` envelope dimension that demultiplexes them
- the model-strategy layer, provider-routing logic, fallback chains, rate-limit reconciliation, or provider-health tracking — Files 16 and 17 own those; this file specifies the per-call attribution and per-error-class retry classification the ledger records
- retrieval, indexing, knowledge-base mechanics, retrieval-augmented generation mechanics, or hybrid-search algorithms — File 12 owns those; this file specifies that the ledger is the substrate over which forensic and replay queries operate
- context-assembly, compaction algorithms, token-budget mechanics, or per-policy block selection — File 13 owns those; this file specifies the typed `ContextPressureObserved` boundary and the compaction-related events that flow through the bus
- the UI shell, the rendering of live or durable events into UI components, modal layouts, or accessibility surface choices — the future UI specs own those; this file specifies the typed envelope and event vocabulary the UI consumes
- specific provider transport mechanics (Tauri IPC, Server-Sent Events, WebSocket, Unix sockets, MCP transports) — the future Runtime Infrastructure and Lifecycle spec owns those; this file specifies the canonical wire-format contract the transport must preserve

## Source Resolution

This file resolves events, ledger entries, hooks, runtime observability, streaming, audit, attribution, and replay material into one boundary: live coordination plus durable execution history.

Resolved design:

- Events are transient coordination signals; ledger entries are durable facts. The ledger is the source of truth for what happened.
- One envelope and dispatch mechanism covers execution progress, capability proposals, policy decisions, hooks, registry changes, version commits, errors, and cancellations.
- Domain-specific events are `Custom` extensions registered by owning specs rather than predeclared global kinds.
- Hooks are typed integration points with declared authority, ordering, fail-direction, and audit behavior.
- Secret or high-sensitivity payloads are redacted or referenced by key; observability must not become a data leak.
- Replay and inspection reconstruct durable behavior from ledgered facts without pretending nondeterministic provider calls are byte-identical.

## 1. Chosen Model

Anchor: `ledger.chosen-model`

ATLAS3 has three primitives in this layer: `ExecutionLedger`, `EventStream`, and `Hook`. They share one `EventEnvelope`, one closed cross-cutting `AppEvent` catalogue with `Custom` extension, one hook decision vocabulary, and one cross-cutting bus through which every consequential execution fact, every live coordination signal, and every extensibility decision flows.

`ExecutionLedger` is the durable, append-only, queryable record of consequential execution facts. Every status transition, every routing decision, every capability invocation, every approval verdict, every model call with per-call attribution keyed by model identity, every block commit, every version commit, every artifact-version commit, every claim publication, every evidence link, every observation capture, every validation outcome, every error, every recovery decision, every child-run relationship, every cancellation, every intervention — every fact later specs depend on for replay, audit, evaluation, telemetry, or learning — is recorded as a `LedgerEntry` in the canonical pool.

`EventStream` is the live coordination channel that carries typed `AppEvent` values through one event bus. Every subsystem that needs to react to system state (streaming UI, hooks, inspectors, progress views, approval routers, validators, structured loggers, telemetry, replay machinery, cross-tab coordination, frontend reactivity, automation triggers) subscribes to the bus. Events carry the canonical envelope, the closed sensitivity classification, and the per-stream monotonic sequence. Consequential events flow through both the live bus and the durable ledger; transient coordination events (token deltas, cursor updates, scroll positions, UI focus changes) flow through the bus only.

`Hook` is the canonical extensibility primitive. Hooks share one registration model, but dispatch has two paths: blocking hooks run at interceptable boundaries before the proposed action continues, while non-blocking hooks observe emitted events through the live bus. A hook declares its `event_kinds`, `mode`, `priority`, `timeout_ms`, category, authority class, handler reference, and source. A blocking hook returns one of four typed `HookDecision` outcomes: `Continue`, `Substitute { new_payload, reason }`, `Block { reason }`, or `RedirectSuggestion { target_capability_id, suggested_args, reason }`. The executor (per `run.call-pipeline`, File 04 §8.2) and the policy layer (per `policy.approval-router`, File 06 §3) consume hook decisions through the same hook mechanism. There is no parallel hook system: the approval router, quality-control validators, completion-verification hooks, user-authored guardrails, plugin hooks, and MCP hooks register through the same mechanism with source-approval gating.

The three primitives compose:

- the executor produces events at each phase of the capability-call pipeline (per `run.call-pipeline`, File 04 §8.2) — `ToolCallProposed`, `ToolCallApproved`, `ToolCallExecuted`, `ToolCallCompleted`, `ToolCallFailed`, `ToolCallDenied`. Hook subscribers fire at each phase, including the approval router at `ToolCallProposed`. Consequential events also commit to the ledger as typed entries.
- the model-strategy layer emits `ModelCallStarted` and `ModelCallCompleted` with full per-call attribution. The ledger records `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)` per `run.execution-ledger` (File 04 §23.1).
- the block layer (per `block.streaming-commit-boundary`, File 08 §7) commits blocks at the canonical commit boundaries; each commit emits `BlockCommitted` to the bus and records `BlockCommitted` (with `block_id`, `kind`, `producer`, `origin_run_id`, `content_hash`, sensitivity, scope) to the ledger.
- the version graph (per File 11) commits version nodes at the canonical boundaries; each commit emits `VersionCommitted` (with `version_id`, `parent_version_id`, `op_summary`, `diff`) to the bus and ledger.
- the policy layer (per `policy.approval-policy-templates`, File 06 §12) emits `PolicyDecisionMade`, `LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `PolicyContradictionDetected`, `PolicyFloorViolated`, and records each as a ledger entry.
- the entity layer (per `artifact.events`, File 09 §20) emits `ArtifactCommitted`, `ArtifactLifecycleChanged`, `ClaimPublished`, `EvidenceLinked`, `ObservationCommitted`, `ValidationCommitted`, `CritiquePosted`, `ProvenanceQueryExecuted`, and records the consequential ones.
- the surface layer (per `surface.surface-relevant-events`, File 07 §13) emits `ToolSurfaceComposed`, `CapabilityBorrowed`, `CapabilityRegistered`, `CapabilityAvailabilityChanged`, and records the consequential ones.
- the routing layer (per File 03) emits `RouteAttached`, `RoutingFrameComposed`, `RouterDecisionEmitted`, and records the route record per `routing.route-record` (File 03 §3.5).

There is one envelope, one vocabulary, one bus, one ledger. Other specs declare new event kinds and ledger-entry kinds through `Custom { namespace, name, payload }` extensions, registered through the canonical capability-registration mechanism (per `capability.runtime-mutation`, File 05 §16.2 proposal-first) and gated by source-approval (per `policy.source-approval-flow`, File 06 §9). New extensions never produce parallel buses, parallel ledgers, or parallel hook systems.

The model elaborates the canonical primitives from `core.execution-ledger` (File 01 §6.4) (`Execution Ledger`), §6.5 (`Event Stream`), and the broader extensibility-and-extension-planes framework in §6.14. It honors `run.ledger-events-commits` (File 04 §23)'s promise that the ledger and event stream coordinate execution while remaining distinct, that hooks are the extension surface, and that nothing flows outside the canonical bus.

`ExecutionLedger` supersedes any earlier vocabulary that named the same primitive: "audit log", "execution log", "operation log", "history table", "session log", "command log", "trace log", "activity log", "telemetry store", "agent journal". `EventStream` supersedes any earlier vocabulary that named the same channel: "event bus", "live stream", "real-time channel", "pub-sub channel", "broadcast channel", "SSE stream", "WebSocket channel", "Tauri event channel". `Hook` supersedes any earlier vocabulary that named the same primitive: "callback", "trigger", "middleware", "interceptor", "before/after handler", "pre/post hook", "filter chain", "decision pipeline", "subscriber", "observer", "PreToolUse / PostToolUse handler", "guardrail middleware". `EventEnvelope`, `AppEvent`, `LedgerEntry`, `LedgerEntryKind`, `HookDecision`, `HookSubscription`, and `TokenUsageRecord` are the canonical typed shapes the rest of this file uses; earlier names from source material map into these.

## 2. Boundaries With Adjacent Layers

Anchor: `ledger.boundaries-with-adjacent-layers`

### 2.1 With File 04 (Execution and Run Model)

`run.call-pipeline` (File 04 §8.2) defines the capability-call pipeline. This file specifies the durable record and live event each pipeline step produces. `run.execution-ledger` (File 04 §23.1) enumerates the canonical minimum ledger content; this file expands that minimum into the full closed catalogue, the per-call attribution schema, the forgery guards, and the replay-reference rules.

`run.event-stream` (File 04 §23.2) defines the event envelope's minimum identifiers; this file specifies the canonical envelope. The conversation field is `conversation_id`; legacy conversation-identifier wording in older source material is normalized to `conversation_id`.

`run.hook-integration` (File 04 §23.3) defines the typed hook decision vocabulary (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`) and priority convention; this file specifies the full hook contract, the subscription schema, category-aware fail-direction, dispatch mechanics, source-trust integration, and action-handler taxonomy.

`run.completion-contract` (File 04 §2.7) defines the `RunCompletionContract` and its authority-gated, monotonic revision rule, and §22 the termination rule and deterministic forgery guard; this file specifies the ledger-side enforcement at status transition, the contract-revision forgery guard, and the configurable completion-verification hook surface (a hook category subscribers register against).

`run.failure-in-parallel-work` (File 04 §15.3) defines the parallelism rules including `sibling_abort_on_failure` and per-call `depends_on`; this file specifies the ledger entries that record these per-batch dispatch decisions and the events that fan out to subscribers.

`run.cancellation` (File 04 §17.3) defines cancellation primitives; this file specifies the cancellation ledger entries and events (`CancellationRequested`, `CancellationProgressing`, `CancellationCompleted`) with the requester, the affected scope, the cooperative-vs-forceful classification, and the partial-output retention outcome.

`run.retry-reroute-branch` (File 04 §19) defines retry, reroute, and branch; this file specifies the ledger entries that record each (`RunRetryStarted`, `RerouteRequested`, `BranchCreated`) and the cross-references that link the new run to the prior run.

`run.error-handling` (File 04 §20) defines error handling and recovery; this file specifies the typed error classification recorded in ledger entries and the recovery-attempt ledger entries (`RecoveryStrategyApplied`, `ContextPressureObserved`, `StuckDetected`, `StuckEscalated`, `BudgetWarning`).

### 2.2 With File 05 (Capability Contracts and Registry)

File 05 owns the `CapabilityDeclaration`, the `RegisteredCapability`, and the `CapabilityInvocation` record. This file specifies what the ledger records about an invocation: declaration version, resolved backend binding identity at call time, resolved touched-resource expressions, resolved model-mediated classifications, resolved permission tier, applied lease identity, call outcome, produced block ids, produced event ids, error variant if any. The invocation record is owned by `capability.invocation-record` (File 05 §11); this file specifies the ledger-side cross-reference to the invocation record and the events emitted at each invocation phase.

`capability.runtime-mutation` (File 05 §16.2) owns the proposal-first capability-registration mechanism; this file specifies the ledger entries (`CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityUpdated`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `CapabilityTrustChanged`) and the corresponding events emitted at registration lifecycle boundaries.

### 2.3 With File 06 (Capability Policy, Approvals, and Leases)

`policy.approval-router` (File 06 §3) owns the approval router as a blocking hook subscriber on `ToolCallProposed` at convention priority `+100`. This file specifies the canonical event the router subscribes to, the typed decision it emits, and the ledger entries it produces (`PolicyDecisionMade`, `ApprovalRequested`, `ApprovalGranted`, `ApprovalDenied`).

`policy.lease-primitive` (File 06 §11) owns the `Lease` primitive; this file specifies the ledger entries that record lease lifecycle (`LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `LeaseNarrowed`).

`policy.approval-policy-templates` (File 06 §12) owns the policy event vocabulary; this file specifies that those events flow through the canonical bus and ledger.

`policy.approval-ui-surface-contract` (File 06 §13) owns the approval UI surface contract; this file specifies that approval requests and responses flow through the canonical bus with the standard envelope (including `sensitivity` for redaction).

### 2.4 With File 07 (Tool Surfaces and Capability Loading)

`surface.visibility-composition-resolution-algorithm` (File 07 §9) owns the deterministic surface composition algorithm; this file specifies the `ToolSurfaceComposed` event that fires when a composition is consumed by an invoker, and the ledger entry that records the consumed snapshot for replay.

`surface.surface-relevant-events` (File 07 §13) owns the surface-relevant event vocabulary (`ToolSurfaceComposed`, `CapabilityBorrowed`, `CapabilityBorrowReturned`, `CapabilityZoneChanged`, `CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `ToolSurfaceShrunk`, `ToolSurfaceOverflow`, `SubsystemSurfaceSpecUpdated`, `PrimarySurfaceChanged`, `SurfaceSettingsChanged`, `SourceConnected`, `SourceDisconnected`, `LensFilterChanged`, `ShortcutConflict`); this file specifies that those events flow through the canonical bus with the canonical envelope and that the consequential subset commits to the ledger.

### 2.5 With File 08 (Blocks and Block Graph)

`block.commit-boundary-set` (File 08 §7.6) owns the canonical block-commit boundary set; this file specifies the `BlockCommitted` event and ledger entry produced at each boundary, including the block id, kind, producer, content hash, sensitivity, scope, and parent linkage.

`block.block-lifecycle-non-destructive-edits` (File 08 §6) owns block lifecycle (`Raw`, `Active`, `Masked`, `Dropped`, `Recovered`) and `PinState` as derived per-`ContextVersion` view-state; this file specifies the `BlockLifecycleChanged` and `BlockPinChanged` events emitted when explicit operations transition view state, and the ledger entries that record them.

`block.hard-delete` (File 08 §6.6) owns the hard-delete contract; this file specifies the `BlockHardDeleted` event and ledger entry, including the deleting actor, the deletion reason, the orphaned-references set, and the composition-materialization outcome.

### 2.6 With File 09 (Artifacts, Claims, Evidence, and Provenance)

`artifact.events` (File 09 §20) owns the entity-relevant event vocabulary (`ArtifactCreated`, `ArtifactVersionCommitted`, `ArtifactLifecycleChanged`, `ArtifactReviewStateChanged`, `ArtifactValidationStateChanged`, `ArtifactMaterialized`, `ArtifactExternallyEdited`, `ArtifactArchived`, `ArtifactDiscarded`, `ArtifactRestored`, `ArtifactHardDeleted`, `ClaimPublished`, `ClaimStatusOverridden`, `ClaimWithdrawn`, `EvidenceLinked`, `EvidenceLinkRemoved`, `CitationCaptured`, `ObservationCommitted`, `ValidationCommitted`, `CritiquePosted`, `ProvenanceQueryExecuted`); this file specifies that those events flow through the canonical bus, the consequential subset commits to the ledger, and `Secret`-tagged payloads do not persist.

### 2.7 With Cross-Cutting Substrate

The structured logging substrate (cross-cutting/logging.md) uses the `tracing` crate with `#[tracing::instrument]` for span instrumentation; this file specifies that every ledger-event boundary carries the span context (`span_id`, `parent_span_id`, `operation`, `service`) that links structured logs to ledger entries.

The typed error substrate (`core.typed-errors`, File 01 §6.9) defines `AppError` with discriminant variants; this file specifies that ledger entries recording errors carry the typed `AppError` plus an optional `TraceContext` field linking the error to the originating span.

The settings substrate (cross-cutting/settings.md, `core.settings-system` (File 01 §6.8)) defines the typed settings system; this file specifies the settings keys this layer reads (hook timeouts, fail-direction overrides, retention granularity, sensitivity classification overrides, aggregation policies, etc.).

The service-layer substrate (cross-cutting/service-layer.md) defines services as Rust traits returning `Result<T, AppError>`; this file specifies `LedgerService`, `EventBusService`, and `HookService` as canonical service traits following the same pattern, with frontend access through Tauri commands or equivalent transport.

### 2.8 Boundary

This file is the durable-and-live recording layer over execution. It owns:

- the closed canonical `LedgerEntryKind` catalogue
- the `EventEnvelope` and closed `AppEvent` vocabulary
- the `Hook` subscription contract, decision vocabulary, action taxonomy, and registration mechanism
- the per-call attribution schema (`TokenUsageRecord`)
- the forgery guards, sensitivity-aware persistence, and replay-reference contracts
- the hash-chained audit-log tier semantics
- the settings dimensions every mechanism here exposes
- the explicit rejections
- the consequences other specs consume

It does not own:

- the capability-call pipeline mechanics (`run.call-pipeline`, File 04 §8.2)
- the capability declaration field set (File 05)
- the policy evaluation algorithm (File 06)
- the surface composition algorithm (File 07)
- the block schema or version graph internals (Files 08 and 11)
- the entity layer (File 09)
- the storage on-disk layout (File 20)
- the sync mechanics (future Sync spec)
- the security primitives (future Security spec)
- the UI rendering (future UI specs)
- the model-strategy and provider-routing internals (Files 16 and 17)

## 3. `ExecutionLedger`

Anchor: `ledger.execution-ledger`

### 3.1 Definition

The `ExecutionLedger` is the durable, append-only, queryable record of consequential execution facts the runtime produces. It is the canonical source of truth for replay, audit, evaluation, telemetry, learning, and forensic queries.

The ledger is:

- durable across process restart, conversation archival, version-graph rewrites, and storage migrations
- append-only — once a `LedgerEntry` is committed, its content does not change; corrections create new entries that link to the prior entry via the `supersedes` cross-reference
- queryable along multiple axes: by `conversation_id`, `run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, time range, entry kind, capability id, model id, error variant, sensitivity, scope, custom predicate
- scoped — every entry carries a scope drawn from the canonical set (`run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule`) matching `policy.lease-primitive` (File 06 §11) lease scopes and `block.block-scope` (File 08 §11) block scopes
- sensitivity-aware — every entry carries a `sensitivity` tag (`Public`, `Sensitive`, `Secret`); `Secret` payloads do not persist (see §10)
- cross-referenced — every entry that names a `Block`, `Artifact`, `Claim`, `Lease`, `Capability`, `Version`, `Run`, `Task`, `IntentThread`, `Conversation`, or other addressable primitive carries the stable identifier
- attribution-bearing — every model-call entry carries the per-call `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)` per `run.execution-ledger` (File 04 §23.1)

The ledger is not:

- a UI representation — UI components consume the ledger through projections; the ledger itself is the durable substrate, not the rendered view
- a memory or knowledge-base mechanism — Memory and the knowledge base are separate primitives; the ledger may be read by them but does not subsume them
- the version graph — version-graph commits emit ledger entries and reference block ids in the same pool, but File 11 owns the version tree's structural invariants; the ledger records that a commit happened
- a parallel block pool — the ledger references `block_id`, but does not duplicate block content
- a substitute for the event stream — events deliver real-time coordination; the ledger is the durable record. Consequential events commit to both; pure UI-coordination events live only on the bus

### 3.2 Required Fields

Every `LedgerEntry` carries at minimum:

- `entry_id` — globally stable identifier; assigned at commit; never reused, never reassigned, never mutated
- `kind` — typed `LedgerEntryKind` discriminator drawn from the closed canonical catalogue (§4) plus the `Custom { namespace, name }` extension mechanism
- `envelope` — the canonical `EventEnvelope` (§5.2) at the moment of recording, including `conversation_id`, optional context references, `sequence_scope`, `sequence`, `timestamp`, `sensitivity`, and trace/causality fields
- `scope` — broadest visibility scope (per `block.block-scope`, File 08 §11), declared at commit
- `payload` — typed payload appropriate to the `kind`; the payload's structural schema is closed canonical for canonical kinds and declared at registration for `Custom` kinds
- `cross_references` — typed map naming the canonical primitives this entry depends on or refers to: `(block_id, artifact_id, version_id, lease_id, capability_id, capability_version, source_instance_id, invocation_id, run_id, task_id, intent_thread_id, conversation_id, workspace_id)`; entries unused for a given entry kind are absent rather than null-padded
- `produced_at` — full-granularity timestamp of recording, distinct from the envelope's event timestamp when the event was emitted earlier than the ledger commit. Timestamps are query/display metadata and may be used as explicit uncertainty-bearing fallback evidence when no sequence or causal relation can answer an ordering query; they are not a correctness basis.
- `producer` — typed reference to what produced the entry: `Executor { run_id, step_id }` for capability-pipeline entries, `RouterEmission { route_id }` for routing entries, `Subsystem { subsystem_id, reason }` for subsystem-internal entries, `Hook { hook_id, source }` for hook-decision entries, `UserAction { user_id, action_kind }` for user-initiated entries, `Automation { trigger_id }` for automation-fired entries
- `entry_schema_version` — version of the ledger record shape; storage normalizes supported earlier versions on load (per `run.execution-ledger`, File 04 §23.1's allowance for extension)
- `idempotency_key` — required for consequential writes that may be retried; scoped by producer, boundary, operation, and source request where applicable. Duplicate keys reject duplicate durable facts or link repeated attempts to the original entry.
- `supersedes` — optional `entry_id` of a prior entry this entry corrects, retracts, or amends; the prior entry remains in the ledger with the new entry's `entry_id` reachable via reverse-link queries (no in-place mutation)

The payload's typed shape is per-kind; §4 enumerates the closed canonical kinds and their payload schemas. The cross-reference map's keys are drawn from a closed canonical set; new keys register through the `Custom` extension mechanism with proposal-first source approval.

### 3.3 Append-Only Invariant

The ledger is append-only. A committed entry's `kind`, `envelope`, `scope`, `payload`, `cross_references`, `produced_at`, `producer`, and `entry_schema_version` fields are fixed at commit. Observable corrections (a typed error variant was misclassified; a token count was misreported by a provider that later corrected its `usage` field) commit a new entry with `kind: LedgerCorrection`, `supersedes: <prior_entry_id>`, and the corrected payload. The prior entry remains in the pool; forensic queries see both.

This rule is load-bearing for audit: an audit reader who reads the ledger at time `t1` and again at time `t2` sees the same content for any entry committed before `t1`. Mutations would defeat audit, replay, and the hash-chained integrity tier (§16).

### 3.4 Minimum Canonical Entry Set

Per `run.execution-ledger` (File 04 §23.1) the ledger records at minimum:

- run creation and status changes (with stop reason, ordering of creation and completion, `control` field per `run.minimum-durable-reconstruction` (File 04 §2.6))
- route attachment (per `routing.route-record`, File 03 §3.5 route record)
- execution unit starts and finishes
- capability proposals
- approvals, denials, leases, and policy decisions (per `policy.approval-policy-templates`, File 06 §12)
- model calls, including provider, model identifier, role (router / responder / critic / validator / sub-agent / etc.), input tokens, completion tokens, cache creation tokens, cache read tokens, and cost (computed from per-model pricing — never stored as an unkeyed scalar; per `core.explicit-rejections` (File 01 §8) invariant)
- tool calls and tool results
- observations (per `artifact.observation`, File 09 §13)
- validation results (per `artifact.validation-critique`, File 09 §14)
- errors and recovery decisions
- produced outputs (block ids, artifact-version ids, claim ids, evidence-link edge ids, memory-proposal ids, task-update ids)
- child-run relationships (parent and child run ids, spawn reason, output contract)
- cancellation and intervention (per `run.user-intervention` (File 04 §17.1) and `run.cancellation` (File 04 §17.3))
- block commits (at canonical commit boundaries per `block.commit-boundary-set` (File 08 §7.6))
- version commits (per File 11)
- artifact-version commits (per `artifact.version-creation`, File 09 §6.3)
- claim publication and status changes (per `artifact.claim`, File 09 §9)
- evidence-link grants and removals (per `artifact.evidence`, File 09 §11)
- citation captures (per `artifact.citation`, File 09 §12)
- surface compositions consumed by an invoker (per `surface.persistence-reconstruction`, File 07 §14)
- capability registrations, unregistrations, and lifecycle transitions (per `capability.lifecycle`, File 05 §16)
- backend binding lifecycle (resolved binding rebound, source connection lost / restored, per `capability.backend-binding-lifecycle` (File 05 §10.4))
- hook subscriptions and decisions (per §5 below)

Section 4 enumerates the full closed canonical `LedgerEntryKind` catalogue with payload schemas. The closed catalogue is canonical for cross-cutting reasoning. `Custom { namespace, name }` extension is canonical for specialization through proposal-first registration.

### 3.5 Storage Contract

The ledger's persistence is owned by File 20. This file specifies what must be durable:

- every `LedgerEntry`'s structural fields above
- the cross-reference map's keys and values
- the per-kind payload at the schema appropriate for the kind
- the `entry_schema_version` for normalization-on-load

The following are not durable (computed from the durable substrate):

- per-tokenizer token counts as scalars (the canonical `TokenUsageRecord` carries per-call counts; aggregate scalars are queries, not durable rows)
- aggregate costs as scalars (computed from `TokenUsageRecord` × pricing tier on demand)
- per-projection materialized views (debug-panel last-N-events, telemetry dashboards, evaluation reports)
- secondary indexes used for query acceleration (rebuildable from the durable substrate)

Reconstruction across restart, retry, edit, reroute, branch, and child-run is deterministic from the durable substrate plus the registry snapshot, settings snapshot, world-model snapshot, and per-capability replay-class declaration (per `capability.replay-class`, File 05 §7.3). See §9 below.

### 3.6 Cross-References

Anchor: `ledger.cross-references`

A ledger entry's `cross_references` map names every primitive the entry depends on or affects. The canonical reference key set:

- `conversation_id` — the conversation the entry belongs to when the event is conversation-scoped
- `run_id` — the executing `Run`
- `task_id` — the `Task` the run advances, if any
- `intent_thread_id` — the owning `IntentThread`
- `workspace_id` — the active workspace
- `parent_run_id` — for child-run entries
- `route_id` — the `RouteRecord` that produced the entry's run
- `invocation_id` — the `CapabilityInvocation` record for capability-call entries
- `capability_id` and `capability_version` — for capability-call entries
- `source_instance_id` — for source-bound entries (which plugin instance, which MCP server connection, which API definition)
- `backend_binding_id` — the resolved live binding at call time (per `capability.backend-binding-lifecycle`, File 05 §10.4) — distinct from `backend_id` envelope (which identifies the running provider/sandbox/process instance)
- `block_id` — for entries that name produced or referenced blocks
- `version_id` — for entries that name a version-graph commit
- `artifact_id` and `artifact_version_block_id` — for entries that name an artifact
- `claim_id` — for entries that name a claim
- `evidence_link_edge_id` — for entries that grant or revoke evidence links
- `lease_id` — for entries that name a lease
- `approval_request_id` — for approval-flow entries
- `hook_id` and `subscription_id` — for hook-decision entries
- `observation_id` — for observation entries
- `validation_id` and `critique_id` — for validation and critique entries
- `staleness_fingerprint` — for entries whose mutation depended on a prior observation (per `artifact.observation`, File 09 §13)
- `policy_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `registry_snapshot_id` — for entries whose semantics depend on the snapshot state at the time of recording
- `event_id` — when the entry was committed in response to a specific event
- `supersedes_entry_id` — when the entry corrects or retracts a prior entry
- `parent_entry_id` — for entries that nest within a parent operation (e.g., a `ChildRunSpawned` entry's `parent_entry_id` points at the spawning entry)
- `child_entry_ids` — optional list pointing to consequential child entries (computed at query time, optionally cached)

Extension keys register through the `Custom` cross-reference extension mechanism. A canonical entry that references an extension cross-reference key must declare the extension in its kind registration (per `capability.runtime-mutation`, File 05 §16.2).

### 3.7 Forgery Guards

Anchor: `ledger.forgery-guards`

The ledger enforces three non-negotiable forgery guards at commit time:

**Status-transition forgery guard** (per `run.termination`, File 04 §22): a status transition from `running` to `completed` is verified against the run's latest authorized `RunCompletionContract` (`run.completion-contract`, File 04 §2.7). On a `Run` whose contract required action, the transition is rejected if no `ToolCallExecuted` or `ToolCallCompleted` entry exists in the run's scope, no `ArtifactVersionCommitted` entry exists in the run's scope, and no `ModelCallCompleted` entry beyond pure-text response exists in the run's scope. The forgery guard fires at the ledger boundary, not only in the executor: a hook subscriber attempting to record `RunStatusChanged { status: Completed }` against a no-evidence run produces a `LedgerCommitRejected` error and a `RunCompletionForgeryAttempted` audit-log entry; the run remains in `running` until evidence is recorded or another terminal status (`failed`, `cancelled`, `superseded`) is committed.

**Contract-revision forgery guard** (per `run.completion-contract`, File 04 §2.7): a `RunCompletionContractRevised` entry whose `revision_kind` is `Weakening` or `Removal` is rejected unless its `authority_source` is at least as strong as the authority that introduced each affected requirement, and the removal/weakening discharge for that authority is recorded (explicit user action for user-introduced requirements, policy approval for policy-introduced requirements, reroute or route override for router-introduced requirements). A weakening or removal authored by the run's own executing agent is rejected. A rejected revision produces `LedgerCommitRejected` and a `RunCompletionForgeryAttempted` audit-log entry. This closes the relocate-the-forgery hole: a run cannot weaken its contract to reach trivial completion, because the weakening fails the same guard the forged completion would.

**Unkeyed-scalar forgery guard** (per `core.explicit-rejections`, File 01 §8): every model-dependent scalar — token counts, cache statistics, cost — must be recorded keyed by `(provider_id, model_id, tokenizer_id)`. A `LedgerEntry` whose payload carries an unkeyed token count or cost is rejected at commit with `LedgerCommitRejected: UnkeyedModelDependentScalar`. The `TokenUsageRecord` schema (§6) enforces the keying.

Additional integrity rules:

- `Secret`-tagged payloads never persist to the durable ledger (§10); the commit validator rejects entries whose payload contains material classified `Secret`, with the entry recording a `safe_description` instead per `artifact.tombstone-fields` (File 09 §8.2) tombstone pattern
- a ledger entry's `entry_id` must be globally unique; entries are uniquely addressable across the ATLAS3 install
- a ledger entry's `supersedes` reference must resolve to a prior entry in the pool; orphan supersession is rejected
- a ledger entry whose payload references blocks, artifacts, claims, or other primitives must reference primitives that exist at commit time (or were previously committed; tombstoned primitives remain referenced via their preserved identity per `block.hard-delete` (File 08 §6.6) and `artifact.artifact-tombstones` (File 09 §8))

### 3.8 Boundary

The ledger defines durable execution truth. The event bus delivers live coordination. The version graph records the version-tree state machine. The storage layer realizes durability. None of those layers invents new entry semantics; they consume what this file defines. File 20 realizes the durability contract; the future Sync, Import, Export spec realizes cross-device propagation; the future Telemetry, Logging, and Observability spec consumes ledger entries to drive projections; the future Evaluation and Benchmarking spec reads the ledger for replay.

## 4. Canonical `LedgerEntryKind` Catalogue

Anchor: `ledger.entry-kinds`

### 4.1 Closed Canonical Catalogue

Anchor: `ledger.entry-kind-catalogue`

Every ledger entry declares its `kind` at commit. The canonical closed catalogue:

**Run lifecycle:**

- `RunCreated` — run instantiated; payload includes trigger kind, route id, capability families, model route, attachment kind
- `RunStatusChanged` — status transition; payload includes from-status, to-status, stop reason, partial-output retention outcome. A transition to `completed` additionally references the `run_completion_contract_id` (or an embedded contract snapshot), the satisfied-requirement list, and the ledger, block, artifact, or policy evidence satisfying each requirement (per `run.completion-contract`, File 04 §2.7)
- `RunResumed` — paused or orphan-restart-resumed run; payload includes prior status, reason, lease revalidation outcome
- `RunSuperseded` — run replaced by edit / reroute / branch / retry; payload includes superseding-run id, supersession reason
- `RunCompletionContractRevised` — the run's `RunCompletionContract` was revised (per `run.completion-contract`, File 04 §2.7); payload includes `run_id`, `old_contract_hash`, `new_contract_hash`, `revision_kind` (`Additive`, `Narrowing`, `Weakening`, or `Removal`), `authority_source`, `reason`, and `evidence_refs`. `Weakening` and `Removal` revisions require qualifying authority and are subject to the contract-revision forgery guard (§3.7)
- `RunCompletionForgeryAttempted` — forgery guard fired; payload includes attempt details, the forging actor's identity (rare, audited)
- `ControlTransferred` — run `control` field changed (per `run.minimum-durable-reconstruction`, File 04 §2.6); payload includes from-actor, to-actor, reason

**Routing:**

- `RoutingFrameComposed` — router context policy assembled the frame; payload includes policy id, snapshot references, included context categories
- `PrecheckEvaluated` — deterministic precheck applied; payload includes precheck id, verdict (`resolved`, `constrained`, `no_op`), changes to frame
- `RouterDecisionEmitted` — router produced `RunIntent`; payload includes the resolved `RunIntent` fields per `routing.run-intent` (File 03 §4.3)
- `RouteRecordCommitted` — full route record persisted; payload includes route_id and the route record's identifiers
- `MidExecutionRerouteRequested` — reroute requested per `routing.mid-execution-reroute` (File 03 §12); payload includes trigger source (model / runtime / user), suggested route, reasoning
- `MidExecutionRerouteResolved` — reroute resolved through one of the three paths; payload includes resolution path (`router_resolved`, `self_routed`, `direct_handback`), the resulting `RunIntent`

**Capability invocation pipeline (per `run.call-pipeline`, File 04 §8.2):**

- `ToolCallProposed` — proposal entered the pipeline; payload includes the `CapabilityInvocation` record reference, resolved arguments (with sensitivity-tagged redaction), resolved touched-resource expressions
- `ValidatorRan` — declared input validator ran (per `capability.input-validators`, File 05 §8.1); payload includes validator id, verdict (`valid`, `invalid_with_correction`, `invalid`), correction applied if any
- `PolicyDecisionMade` — approval router emitted a decision (per `policy.approval-router`, File 06 §3.4); payload includes decision (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`), contributing scope, lease used, contradictions detected
- `ApprovalRequested` — ask-user, typed-confirmation, batched, or contradiction-resolution flow opened (per `policy.approval-ui-surface-contract`, File 06 §13); payload includes the `ApprovalRequest` reference
- `ApprovalGranted` / `ApprovalDenied` — user resolved the approval; payload includes choice, customized constraints, typed-confirmation string if applicable (redacted per sensitivity rules)
- `LeaseGranted` / `LeaseRevoked` / `LeaseStale` / `LeaseNarrowed` — lease lifecycle events (per `policy.persistence`, File 06 §11.6); payload includes lease id and the lease projection over its source events
- `PolicyContradictionDetected` / `PolicyContradictionResolved` — cross-scope conflict (per `policy.contradiction-checking-across-scope-levels`, File 06 §14)
- `PolicyFloorViolated` — attempt to lower below `permission_floor` (per `policy.permission-floor-typed-confirmation`, File 06 §7); payload includes the violating actor and the override choice
- `ClassifierMediatedDecision` — `auto-decide` classifier ran (per `policy.auto-decide-mode`, File 06 §8); payload includes classifier result, confidence, fallback choice
- `ToolCallApproved` — proposal cleared policy; payload includes the per-call resolved facts (tier, touched resources, lease)
- `ToolCallDenied` — proposal denied; payload includes denial reason, in-band synthesis of the typed result block id
- `ToolCallExecuted` — capability handler invoked; payload includes start timestamp, isolation primitive used (per `run.isolation`, File 04 §16.2), backend binding instance
- `ToolCallStreamingPartial` — capability emitted a partial during streaming (per `run.streaming-partial-execution`, File 04 §12); payload includes partial-block handle, byte counts, sensitivity
- `ToolCallCompleted` — capability returned its declared output; payload includes produced block ids, postcondition outcomes, declared replay-class metadata
- `ToolCallFailed` — capability returned a typed error; payload includes the typed `AppError`, recovery action taken or proposed
- `ObservationCommitted` — observation block committed (per `artifact.observation`, File 09 §13); payload includes observation kind, staleness fingerprint, block id
- `ValidationCommitted` — validation block committed (per `artifact.validation-critique`, File 09 §14); payload includes validation outcome
- `CritiquePosted` — critique block committed (per `artifact.validation-critique`, File 09 §14)

**Model calls (per `run.execution-ledger`, File 04 §23.1):**

- `ModelCallStarted` — provider call initiated; payload includes provider id, model id, tokenizer id, role, request fingerprint, and cache markers used
- `ModelCallCompleted` — provider returned; payload includes the full `TokenUsageRecord` (§6.2), the cost computed from per-model pricing, the stop reason, the parsed `ParsedResponse` reference
- `ModelCallStreamingDelta` — provider streamed a chunk; payload includes delta size, accumulated counts, partial-block handle (aggregated per §13.4)
- `ModelCallFailed` — provider returned an error; payload includes the typed provider error (per File 06 errors module), retry classification (`retryable`, `rate_limited`, `fatal`), `retry_after_ms` if provider-supplied
- `ProviderHealthChanged` — provider transitioned `Healthy / Degraded / Unhealthy`; payload includes prior state, new state, and contributing failure count
- `RateLimitSnapshotReconciled` — provider headers reconciled local rate-limit state; payload includes the typed `RateLimitSnapshot`
- `TokenCountEstimationTelemetry` — post-call accuracy comparison; payload includes estimated count, actual count, delta percentage, tokenizer id

**Block and version-graph events:**

- `BlockCommitted` — block committed at a canonical boundary (per `block.commit-boundary-set`, File 08 §7.6); payload includes block id, kind, content variant, content hash, sensitivity, scope, producer
- `BlockLifecycleChanged` — explicit `Mask`, `Drop`, `Recover` operation (per `block.mask-drop-recover`, File 08 §6.3); payload includes block id, from-state, to-state, version it applies to
- `BlockPinChanged` — explicit `Pin`, `Unpin`, `Protect`, `Unprotect` operation (per `block.pin-protect`, File 08 §6.4)
- `BlockGrouped` / `BlockUngrouped` — `Group`-kind block created or dissolved (per `block.group-ungroup`, File 08 §6.5)
- `BlockHardDeleted` — physical destruction (per `block.hard-delete`, File 08 §6.6); payload includes deleting actor, deletion reason, tombstone reference, materialization-fallback outcome
- `VersionCommitted` — version-graph commit; payload includes version id, parent version id, `op_summary`, the compact `VersionDiff`
- `VersionSwitched` — active version pointer changed; payload includes from-version, to-version, view rebuild outcome
- `PendingOpApplied` — context operation applied to the materialized view (per `block.block-lifecycle-non-destructive-edits`, File 08 §6); payload includes operation kind, affected block id, pending buffer state

**Artifact and entity events (per `artifact.events`, File 09 §20):**

- `ArtifactCreated` — first version of an artifact committed; payload includes artifact id, kind, materialization policy, producing context
- `ArtifactVersionCommitted` — subsequent artifact version committed; payload includes version id, derivation summary, materialized paths
- `ArtifactLifecycleChanged` — derived lifecycle transition recorded (Draft → Active → Validated etc.); payload includes from-state, to-state
- `ArtifactReviewStateChanged` — explicit review-state update; payload includes choice, actor
- `ArtifactValidationStateChanged` — validation outcome derived from validated_by edges
- `ArtifactMaterialized` — artifact written to workspace path; payload includes materialized paths and content hashes
- `ArtifactExternallyEdited` — filesystem watcher committed a sibling version for an externally-modified materialized file
- `ArtifactArchived` / `ArtifactDiscarded` / `ArtifactRestored` — explicit lifecycle operations
- `ArtifactHardDeleted` — tombstone created (per `artifact.artifact-tombstones`, File 09 §8); payload includes the tombstone reference
- `ClaimPublished` — claim block committed via `claim.publish` (per `artifact.claim-extraction`, File 09 §10)
- `ClaimStatusOverridden` / `ClaimWithdrawn` — explicit claim-state changes
- `EvidenceLinked` — typed evidence-link edge created (per `artifact.evidence`, File 09 §11)
- `EvidenceLinkRemoved` — explicit evidence-link removal
- `CitationCaptured` — citation block committed
- `ProvenanceQueryExecuted` — canonical provenance query ran (per `artifact.provenance`, File 09 §15); payload includes query kind, target, result summary

**Surface and capability registry events (per `surface.surface-relevant-events`, File 07 §13 and `capability.events` (File 05 §12.2)):**

- `ToolSurfaceComposed` — resolved tool surface consumed by an invoker; payload includes surface id, invoker kind, scope context, zoned-entries summary, auto-shrink record, composition diagnostics
- `ToolSurfaceShrunk` — auto-shrink demoted capabilities (per `surface.auto-shrink-algorithm`, File 07 §8.2)
- `ToolSurfaceOverflow` — composition failed to fit pinned tools (per `surface.auto-shrink-algorithm`, File 07 §8.2)
- `CapabilityBorrowed` — `tool.borrow` granted a `BorrowGrant` (per `surface.borrow-grant`, File 07 §7.3)
- `CapabilityBorrowReturned` — `BorrowGrant` expired or revoked
- `CapabilityZoneChanged` — zone reassignment between compositions (per `surface.surface-relevant-events`, File 07 §13)
- `CapabilityRegistered` — registration succeeded (per `capability.capability-registry`, File 05 §12.3)
- `CapabilityUnregistered` — registration removed
- `CapabilityUpdated` — version increment registered (per `capability.lifecycle`, File 05 §16.4)
- `CapabilityEnabledChanged` — enable flag toggled at any scope
- `CapabilityAvailabilityChanged` — `availability_status` transition (per `capability.registered-capability`, File 05 §10)
- `CapabilityRegistryStateChanged` — binding rebound, trust override applied, collision resolved
- `SubsystemSurfaceSpecUpdated` — subsystem updated its declared default surface (per `surface.subsystem-surface-spec`, File 07 §5)
- `PrimarySurfaceChanged` — active `SubsystemSurfaceSpec` changed mid-run (per `surface.primary-surface-changes`, File 07 §5.4)
- `LensFilterChanged` — per-lens visibility setting changed
- `SourceConnected` / `SourceDisconnected` — plugin or MCP server source lifecycle
- `SourceRegistrationApproved` / `SourceRegistrationDenied` / `SourceRegistrationDeferred` — source-approval flow outcome (per `policy.source-approval-flow`, File 06 §9)
- `ShortcutConflict` — keyboard-shortcut collision detected

**Child run, parallel work, and merge:**

- `ChildRunSpawned` — child run created (per `run.child-runs-multi-agent-work`, File 04 §16); payload includes parent run id, child run id, declared output contract, isolation primitive
- `ChildRunStatusChanged` — mirrors `RunStatusChanged` for child runs
- `ChildRunMerged` — parent run incorporated child output (per `run.merge`, File 04 §16.4); payload includes merge mode (summary / artifact / patch / evidence-set / validation-report / proposed-task-update / proposed-workflow-step)
- `SiblingAborted` — sibling cancelled due to `sibling_abort_on_failure` (per `run.failure-in-parallel-work`, File 04 §15.3)
- `DependencyFailureSkipped` — downstream unit skipped due to upstream `depends_on` failure
- `BatchCoalesced` — duplicate concurrent identical calls coalesced (per `run.mutation-rule`, File 04 §15.4)

**Streaming and live partials:**

- `StreamStarted` — typed stream opened (model text, reasoning, tool input, tool output, partial block, file partial write); payload includes stream kind, partial-block handle
- `StreamProgressBatch` — aggregated batch summary (per §13.4); payload includes batched delta counts, byte counts, aggregation policy
- `StreamCompleted` — stream reached its declared commit boundary; payload includes committed block id, total bytes, total chunks
- `StreamCancelled` — stream cancelled mid-flight; payload includes the orphan-block outcome per `run.cancellation` (File 04 §17.3)
- `FilePartialWriteStaged` — live-partial-write capability wrote into a temp file (per `run.streaming-partial-execution`, File 04 §12)
- `FilePartialWriteAborted` — staged temp file deleted on cancellation
- `FilePartialWriteCommitted` — atomic rename moved the staged temp file to the destination

**Hook events (this file's primary concern):**

- `HookSubscriptionRegistered` — hook subscription added; payload includes subscription id, event kinds, mode, priority, timeout, fail-direction, authority class, source
- `HookSubscriptionUnregistered` — subscription removed
- `HookSubscriptionEnabledChanged` — subscription toggled at any scope
- `HookFired` — hook handler invoked at a matching event; payload includes hook id, event id, run-context references
- `HookDecisionRecorded` — blocking hook returned a decision; payload includes the typed `HookDecision`
- `HookTimedOut` — handler did not return within `timeout_ms`; payload includes the synthesized default decision and the configured fail-direction
- `HookHandlerError` — handler raised an error; payload includes typed error, fail-direction synthesis
- `HookActionInvoked` — when a hook's action invoked a capability, ran a shell script, or emitted a synthesized event; payload includes the action kind and the resulting events / capability invocation reference

**Error and recovery:**

- `TypedErrorRaised` — a typed `AppError` was raised in the run; payload includes the typed variant, the originating span context, and the affected operation
- `RecoveryStrategyApplied` — a recovery strategy fired (per `run.recovery`, File 04 §20.2); payload includes the strategy (`retry_same_unit`, `expose_to_model`, `switch_model_profile`, `switch_capability_implementation`, `narrow_capability_scope`, `revoke_and_narrow_lease`, `request_user_clarification`, `branch_strategy`, `restore_or_rollback`, `stop_with_typed_failure`)
- `ContextPressureObserved` — execution observed context pressure (per `run.boundary-rule`, File 04 §20.1); payload includes used percentage, kind of pressure
- `StuckDetected` — runtime detected obvious stuck state (per `run.stuck-detection`, File 04 §20.3); payload includes pattern detected (`repeated_identical_tool_calls`, `repeated_failed_validations`, `repeated_provider_errors`, `no_new_durable_output`, `cyclic_child_waiting`, `ping_pong`, `single_iteration_empty_response`)
- `StuckEscalated` — escalation step taken (soft warning, structured directive, hard stop); payload includes the active escalation level
- `BudgetWarning` — execution approached a configured budget (per `run.budgets-limits`, File 04 §21); payload includes budget kind, threshold percentage
- `BudgetExhausted` — budget hit; payload includes the budget kind, partial-output retention
- `LoopDetected` — agent or capability loop detected (action signature repetition, page-stagnation, ping-pong); payload includes the detector, the offending pattern
- `RetryAttempted` — explicit retry attempt; payload includes the prior entry id, the retry mode (per `run.retry`, File 04 §19.1)
- `BranchCreated` — branch created (per `run.branch`, File 04 §19.3); payload includes the parent execution boundary
- `RerouteResolved` — reroute resolved (per `run.reroute`, File 04 §19.2)

**Cancellation and intervention:**

- `CancellationRequested` — user or policy requested cancellation; payload includes the cancel target (run / run+children / specific child / specific tool call / specific sandbox), the requester, the cooperative-stop deadline
- `CancellationProgressing` — cooperative stop in progress; payload includes the listeners that have acknowledged, the deadline countdown
- `CancellationEscalated` — escalation to forceful termination after the deadline expired
- `CancellationCompleted` — final cancellation outcome; payload includes the affected run / child-run / tool-call ids, cleanup performed, cooperative-vs-escalated-vs-forceful classification, partial outputs retained or discarded, final status
- `OrphanOutputDetected` — listener reported completion after the run was already cancelled; payload includes the orphan reference
- `InterventionRecorded` — explicit user intervention during execution (per `run.user-intervention`, File 04 §17.1); payload includes the intervention kind (`continuation_with_new_instruction`, `pause`, `cancel`, `branch`, `reroute`, `approval_grant`, `approval_denial`, `scope_narrowing`, `explicit_takeover`), the actor
- `TakeoverStarted` — `control` flipped to `User` (per `run.minimum-durable-reconstruction`, File 04 §2.6)
- `TakeoverEnded` — `control` returned to `Assistant`; payload includes the optional user-supplied summary and observable workspace delta references

**Workspace, file, and external state:**

- `WorkspaceOpened` / `WorkspaceClosed` — workspace lifecycle (per future Workspaces and Materialization spec)
- `FileIngested` — new file block created from an upload or import
- `FileExternallyModified` — filesystem watcher detected an external edit (per `block.streaming-commit-boundary`, File 08 §7)
- `FileMaterialized` — block content written to workspace (per `artifact.artifact-materialization`, File 09 §7.3)
- `EnvironmentSnapshotCaptured` — environment captured for replay (env vars, working directory, virtual desktop, focus state, DPI)

Domain-specific workspace, source-control, browser, perception, system-watch, memory, retrieval, knowledge-base, and SRS facts are not predeclared in the canonical catalogue. Their owning specs declare them as `Custom { namespace, name, payload }` extensions through §4.3. File 10 reserves the mechanism and namespace discipline; it does not predeclare those kinds.

**Validation and quality control:**

- `CompletionVerificationFired` — completion-verification hook surface ran (per `run.termination`, File 04 §22); payload includes the deterministic-vs-model-mediated mode, the verdict
- `QualityControlValidatorRan` — quality-control validator fired; payload includes validator id, verdict, decisive validator chain
- `QualityControlViolationDetected` — violation surfaced

**Approval and contradiction:**

- `BatchApprovalRequested` / `BatchApprovalResolved` — batched approval flow (per `policy.batched-approval-flow`, File 06 §5.5)
- `TypedConfirmationRequested` / `TypedConfirmationSatisfied` / `TypedConfirmationMismatched` — typed-confirmation flow (per `policy.permission-floor-typed-confirmation`, File 06 §7)
- `DeniedFloorOverridden` — typed-confirmation override of a `Denied`-floor capability (per `policy.denied-carve-out`, File 06 §7.4)
- `SourceApprovalFlowOpened` / `SourceApprovalFlowResolved` — source-approval flow (per `policy.source-approval-flow`, File 06 §9)

**Automation, scheduling, and triggers:**

- `AutomationTriggerFired` — automation trigger emitted a run (per future Automation and Triggers spec)
- `WebhookReceived` — external webhook delivered to the system
- `OsEventReceived` — external OS event delivered

**Sync and persistence:**

- `SyncPulled` / `SyncPushed` / `SyncVersionDiverged` / `SyncBlobFetched` / `SyncFailed` — cross-device sync lifecycle (per cross-cutting infrastructure/sync.md)
- `LedgerCompactionRan` — ledger compaction collapsed older entries (per §10 retention)

**System / app lifecycle:**

- `AppStarted` — application initialized; payload includes versions, settings snapshot id, registry snapshot id
- `AppShuttingDown` — graceful shutdown initiated with grace period (per cross-cutting infrastructure/lifecycle.md)
- `AppStopped` — application terminated
- `BackgroundWorkerSpawned` / `BackgroundWorkerStopped` — background worker (memory consolidator, scheduler, audit writer, lineage tracker, watch poller)
- `BackgroundWorkerHeartbeat` — periodic worker health signal
- `LedgerCommitRejected` — a commit-time forgery guard or validation rule rejected an entry; payload includes the proposed entry's fields (with sensitivity redaction) and the rejection reason

**Custom extension:**

- `Custom { namespace, name, payload }` — subsystem-, surface-, plugin-, MCP-, API-, or user-defined kind registered through proposal-first registration. Registration follows `capability.runtime-mutation` (File 05 §16.2). The registration declares the namespace, schema id/version, payload shape, allowed cross-reference keys, default sensitivity, retention class, owner, and canonical event vocabulary the kind participates in.

### 4.2 Kind Composition Rules

The catalogue above is not free-form. The following composition rules apply:

- every capability-invocation kind (`ToolCallProposed`, `ToolCallExecuted`, `ToolCallCompleted`, `ToolCallFailed`, `ToolCallDenied`) shares a single `invocation_id` cross-reference so the full pipeline is correlatable
- every model-call kind (`ModelCallStarted`, `ModelCallCompleted`, `ModelCallStreamingDelta`, `ModelCallFailed`) shares a single `request_id`
- every block-commit kind (`BlockCommitted`) references the produced `block_id` and the `invocation_id` that produced it (when produced by a capability)
- every artifact-event kind references the `artifact_id` and the `artifact_version_block_id` it operates on
- every hook-decision kind (`HookDecisionRecorded`, `HookTimedOut`, `HookHandlerError`) references the originating `event_id` and the `subscription_id`
- every cancellation kind references the `run_id` (or `tool_call_id` if narrower) it targets and the `requester` (the user, the policy, the budget exhaustion, the watchdog)

### 4.3 Custom Kind Registration

Anchor: `ledger.custom-kind-registration`

A `Custom { namespace, name }` ledger entry kind is registered through the canonical capability-registration capability (per `capability.runtime-mutation`, File 05 §16.2). The registration declares:

- the `namespace` (matching the owning subsystem or extension source)
- the `name` within that namespace
- the schema id and schema version
- the payload schema (typed structural shape)
- the required and optional cross-reference keys
- the default sensitivity
- the retention class
- the owner/source subsystem
- the allowed canonical events this kind participates in (which events trigger committing this kind)
- the human-readable description

Registered custom kinds enter the same registry as canonical kinds and follow the same source-trust narrowing rules (per `policy.source-approval-flow`, File 06 §9). A custom kind cannot violate canonical composition rules; the registration is rejected if it would.

Unknown custom kinds are storable and renderable only as opaque safe records. They are not executable as hook decisions, policy facts, or capability inputs until their schema is registered and trusted.

### 4.4 Boundary

The canonical kind catalogue defines what consequential execution facts the system reasons about across cross-cutting subsystems. Domain-specific facts use `Custom` extensions. Storage and projection layers consume the catalogue; they do not extend it (only the registered `Custom` extension does). Adding a new canonical kind is a canonical-spec change, not a runtime registration.

## 5. `EventStream`

Anchor: `ledger.event-stream`

### 5.1 Definition

The `EventStream` is the typed live coordination channel through which every system event flows. It carries `AppEvent` values wrapped in the canonical `EventEnvelope`. The bus is the single coordination substrate for the streaming UI, hook subscribers, inspectors, progress views, approval routers, validators, structured loggers, telemetry, replay machinery, cross-tab coordination, frontend reactivity, automation triggers, and external integrations.

The bus is not:

- the durable execution history — that is the `ExecutionLedger`; the bus is live coordination
- a parallel message queue per subsystem — there is one bus; subsystems subscribe with filters
- a place where consequential events disappear — every consequential event is also recorded as a ledger entry
- a substitute for typed errors — error propagation through services uses `Result<T, AppError>` (per cross-cutting/errors.md); the bus carries `TypedErrorRaised` events as observations of errors, not as the error-propagation channel itself

The bus is:

- typed — every event is a closed `AppEvent` variant or `Custom { namespace, name, payload }`
- ordered within declared `sequence_scope` tuples (subscribers within a context tuple see events in monotonic sequence order)
- fan-out — multiple subscribers receive the same event in parallel
- backpressure-aware — each subscriber has a bounded buffer; overflow emits `EventBufferOverflow` and marks the subscriber `degraded`
- sensitivity-aware — `Secret` payloads are stripped or replaced with safe descriptions before any persistence path (logging, telemetry, sync, export)

### 5.2 `EventEnvelope`

Anchor: `ledger.event-envelope`

Every event carries the canonical envelope:

- `event_id` — globally stable identifier for the event; assigned at emission; never reused
- `conversation_id` — the active conversation when conversation-scoped; absent for explicitly system-wide events
- `context_refs` — typed contextual references when applicable: `run_id`, `step_id`, `node_id`, `workspace_id`, `worktree_id`, `backend_id`, `capability_id`, `ledger_entry_id`, and registered extension refs. Inapplicable refs are absent rather than null-padded.
- `parent_event_id` — the causally-prior event (the event whose handler emitted this event); `None` for root events; enables causality chain reconstruction
- `causal_event_ids` — optional set of additional events this event depends on when one parent is insufficient
- `trace_context` — optional propagation envelope for cross-run observability (per `routing.run-intent`, File 03 §4.3); typically a stable trace id and a span id, semantics defined by the future Telemetry spec
- `sequence_scope` — the tuple within which `sequence` is monotonic, usually the conversation/run/worktree/backend context that produced the event
- `sequence` — monotonic identifier within `sequence_scope`; used for de-duplication and ordering within a context
- `timestamp` — full-granularity timestamp. It may support display, search, and explicit uncertainty-bearing fallback inference, but never replaces sequence or causal links as the correctness basis.
- `sensitivity` — the closed sensitivity classification: `Public`, `Sensitive`, or `Secret`

The envelope itself is mandatory. Contextual references inside it are optional or explicitly not applicable. Subscribers filter by any combination of envelope fields plus the event kind.

The envelope's `sequence` is monotonic within `sequence_scope`. Subscribers deduplicate using `event_id` first and `sequence` within scope second. Predictable event chains should include the expected causal relation or next expected sequence where the producer can know it; consumers use that relation to detect gaps without relying on time.

### 5.3 Closed `AppEvent` Catalogue

Anchor: `ledger.app-event-catalogue`

Every event is an `AppEvent` variant. The closed canonical catalogue is the same set as the `LedgerEntryKind` catalogue (§4), with the addition of transient-coordination kinds that do not commit to the ledger:

**Transient-coordination kinds (live bus only, not durable):**

- `MessageChunk` — model text delta during streaming
- `ReasoningChunk` — model reasoning delta during streaming (per `capability.permission-policy-fields`, File 05 §3.5 sensitivity defaults; `Sensitive` by default)
- `BlockStreamStarted` — a block began streaming (the durable counterpart is `StreamStarted`; the transient form notifies the UI immediately)
- `BlockStreamCompleted` — a block finished streaming (durable counterpart is `StreamCompleted`)
- `ContextAssembled` — context assembly produced a model request (per cross-cutting/context-assembly.md); payload includes budget breakdown
- `ContextBudgetWarning` — context approached a budget (per cross-cutting/context-assembly.md)
- `CompactionStarted` / `CompactionCompleted` — compaction pipeline events (per File 13)
- `UiPanelRegistered` / `UiPanelUnregistered` / `UiPrimaryPanelChanged` / `UiSelectionChanged` / `UiModeChanged` / `UiAvailableCapabilitiesRecomputed` — UI state-awareness events (per cross-cutting/state-awareness.md)
- `UiThemeChanged` / `UiKeybindingChanged` / `UiLayoutChanged` — UI customization events
- `DebugLog` — structured log entry (sensitive by default; secret content always redacted)
- `EventBufferOverflow` — a subscriber's bounded buffer overflowed; the subscriber transitions to `degraded` state
- `Ping` / `Pong` — heartbeat events for cross-tab or remote subscribers
- `SocketIoMessage` — gateway-bridge wire message (for systems exposing the bus over network transports)
- `Heartbeat` — periodic liveness signal from a background worker

All `LedgerEntryKind` variants from §4 are also `AppEvent` variants; the consequential events fan out to both the bus (live coordination) and the ledger (durable record).

The catalogue is extensible via `Custom { namespace, name, payload }` events registered through the canonical mechanism (per `capability.runtime-mutation`, File 05 §16.2). Custom events declare whether they are transient-only or also produce ledger entries.

### 5.4 Delivery Semantics

The bus delivers events through these rules:

- **Within a `sequence_scope`**, events are delivered to subscribers in monotonic `sequence` order. Subscribers see the same event ordering, deterministic across replay of that scope.
- **Across context tuples**, no ordering is guaranteed; subscribers cannot assume that an event in conversation A precedes an event in conversation B in the same wall-clock order.
- **Fan-out** to multiple subscribers happens in parallel; the bus does not block one subscriber's processing on another's.
- **Blocking hook dispatch** happens at interceptable boundaries before the consequential action proceeds. Passive bus delivery is non-blocking fan-out and does not become the authority for mutating or approving the action.
- **Backpressure** is bounded per subscriber: each subscription declares a buffer profile. Overflow emits `EventBufferOverflow` and marks the subscription `degraded`; degraded subscriptions stop receiving events until the subscriber acknowledges recovery through an explicit reconnection.
- **Cross-process delivery** uses the transport substrate (Tauri channels for backend-to-frontend, Server-Sent Events for browser clients, Unix sockets for shell-script hooks, MCP transport for external clients). The transport substrate preserves the wire-format contract this file specifies; specifics are owned by the future Runtime Infrastructure and Lifecycle spec.
- **Persistence boundary**: consequential events commit to the ledger before being delivered to the bus, or atomically alongside delivery (the storage layer specifies the durability semantics). The ordering guarantee is: if an event is durably persisted, all subscribers see its ledger commit before any subscriber observes a later sequence number in the same context tuple. Transient events may be delivered without ledger commit.

The owning subsystem commits consequential facts through the ledger API and emits an event referencing the committed `ledger_entry_id` or causal entry. Observing an event never creates the durable fact; a consequential event without its required durable record is an incomplete execution state.

### 5.5 Delivery Classes and Aggregation Policies

Every event kind declares a delivery class:

- `lossless_consequential` — must be durably represented before completion or linked to a durable fact; never silently dropped
- `coalescible` — may aggregate multiple updates into a typed summary when the summary preserves the meaning needed by subscribers
- `latest_only` — only the latest state matters, such as focus or cursor state
- `sampled_diagnostic` — diagnostic or telemetry events where sampling is acceptable under settings

High-frequency events aggregate before bus emission to prevent saturation. Aggregation policies are typed, declarative, and settings-driven; subscribers see the aggregated form, not raw underlying mutations. Examples include token delta aggregation into `StreamProgressBatch`, UI position coalescing into latest-state summaries, heartbeat summaries, and structured-log batches. Canonical specs do not bake fixed millisecond windows, pixel thresholds, or event-count constants into correctness rules.

Aggregation never silently drops consequential events. A `Block`-tier hook decision, a `ToolCallProposed`, a `ModelCallCompleted`, or any other consequential event flows through the ledger path and bus individually. Aggregation applies only where the declared delivery class permits it, and coalesced or dropped noncritical details must preserve a typed summary when user-facing inspection or debugging needs it.

### 5.6 Sensitivity Tagging at Emission

Every event carries `sensitivity` at emission. The producer is responsible for the initial tag; the policy layer and downstream subscribers may not lower the classification (only raise). The canonical rules:

- a capability emits events at its declared `data_sensitivity` (per `capability.permission-policy-fields`, File 05 §3.5), with per-event override allowed
- the executor stamps `sensitivity = Sensitive` on any event payload that includes credentials, secrets, raw user-private data, or anything flagged by the capability's per-field `sensitivity_field_map`
- the executor stamps `sensitivity = Secret` on any event payload that includes raw credentials in flight (the executor strips or replaces the raw secret before any persistence path; only safe labels persist in the durable form)
- subscribers respect the tag: `Secret`-tagged events do not flow to storage paths (durable ledger, sync, export, telemetry), only to the in-process subscribers that need them (the executor itself, the immediate consumer, a sandbox handler) and only for the duration of their handling

The bus enforces: `Secret`-tagged event payloads are passed by reference to the in-process handler; the reference is zeroed after the handler returns; no copy persists to durable storage.

Subscriptions are policy-governed. A subscriber declares event kinds, scope filters, maximum sensitivity, authority, and purpose. The dispatcher provides each subscriber with a redacted projection appropriate to its grants. `Secret` payloads are never delivered to ordinary subscribers; `Sensitive` payloads require explicit permission and default to safe summaries.

### 5.7 Frontend Bridge

The bus exposes a Tauri-or-equivalent bridge for frontend subscription. Frontend subscribers receive events through `listen<EventEnvelope>('app://event-bus', handler)` (or per-channel subscriptions for high-volume kinds). The bridge:

- preserves the envelope's identifiers
- streams events in monotonic `sequence` order per context tuple
- supports transport-level resume tokens such as `Last-Event-Id` where the transport provides them
- handles backpressure: if the frontend cannot keep up, the bridge marks the subscription `degraded` and emits `EventBufferOverflow`
- gates `Secret`-tagged events: the frontend never receives a raw secret payload; redaction happens at the bridge boundary
- supports per-event-kind subscription filters: the frontend declares which event kinds it subscribes to, reducing wire traffic

The bridge implementation is owned by the future Runtime Infrastructure and Lifecycle spec. This file specifies the contract.

### 5.8 Boundary

The event bus is the live coordination substrate. It does not own:

- the underlying transport (Tauri, SSE, WebSocket, Unix socket, MCP — future Runtime Infrastructure spec)
- the durable persistence of consequential events (File 20)
- the cross-device sync mechanics (future Sync spec)
- the UI rendering of event-driven updates (future UI specs)
- the typed-error propagation through services (cross-cutting/errors.md)
- the policy-evaluation logic that consumes events (File 06)

It does own the wire-format contract, the envelope, the closed `AppEvent` catalogue, the delivery and ordering semantics, the aggregation policies, the sensitivity rules at emission, and the subscription contract.

## 6. Per-Call Model-Call Attribution

Anchor: `ledger.per-call-model-call-attribution`

### 6.1 Definition

Per-call model-call attribution is the canonical recording mechanism for every model invocation the system makes. It is load-bearing for cost accounting, replay accuracy, rate-limit reconciliation, evaluation, and the unkeyed-scalar invariant from `core.explicit-rejections` (File 01 §8).

Every `ModelCallCompleted` ledger entry must carry a complete `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)`.

### 6.2 `TokenUsageRecord`

The required schema:

- `record_id` — stable identifier for the record
- `entry_id` — the parent `ModelCallCompleted` ledger entry id
- `conversation_id`, `run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id` — envelope/context identifiers
- `provider_id` — the provider identity
- `model_id` — the resolved model identity at call time
- `tokenizer_id` — the tokenizer or counting strategy used for any local estimation
- `role` — the model's role in the call: `router`, `responder`, `critic`, `validator`, `summarizer`, `sub_agent`, `classifier`, `judge`, or registered custom role
- `prompt_tokens` — input token count
- `completion_tokens` — output token count
- `cache_creation_tokens` — cache write tokens when the provider exposes or can derive them
- `cache_read_tokens` — cache hit tokens when the provider exposes or can derive them
- `reasoning_tokens` — extended-thinking tokens (when the provider exposes them; `None` otherwise)
- `request_id` — provider-supplied request id (for cross-referencing with provider dashboards or audit)
- `token_source` — the typed `TokenSource` (§6.3) indicating accuracy provenance
- `usage_source` — provider-reported, local-estimated, provider-counting-endpoint, multimodal-estimated, or mixed
- `cost_calculated_at` — timestamp of cost calculation when cost is displayed or stored as a projection
- `pricing_snapshot_id` — reference to the pricing snapshot used when cost is shown or stored
- `pricing_tier_id` — reference to the `PricingTier` record used for cost calculation, if cost projection uses tier-based pricing
- `latency_ms` — round-trip latency including any network time
- `inference_time_ms` — server-reported inference time when available
- `cached_input_tokens` — provider-side cached input (where the provider exposes this field)
- `image_tokens`, `audio_tokens`, `video_tokens` — for multimodal calls; computed from modality-specific accounting rules per `run.execution-ledger` (File 04 §23.1)

The record is not durable as a single scalar (no unkeyed `total_tokens` field; aggregation is a query, not a stored row). Aggregation views (`total_tokens_per_session`, `cost_per_run`, `tokens_per_model`) are queries computed from `TokenUsageRecord` rows. Storage may materialize aggregation views, but the source of truth is the per-call record.

### 6.3 `TokenSource`

`TokenSource` is the closed canonical enum classifying the accuracy of the recorded counts:

- `ProviderNative { confidence }` — counts are from the provider's response body or equivalent native usage record
- `LocalTokenizer { tokenizer_id, confidence }` — counts are from a registered local tokenizer or counting library selected by provider/model descriptor
- `ProviderCountingApi { endpoint_ref, confidence }` — counts are from a provider-exposed counting operation
- `CharacterApproximation { formula_id, safety_margin, confidence }` — counts are from a documented approximation formula; used only as last-resort fallback
- `MultimodalEstimate { dimension, units, formula_id }` — counts are computed from media properties using a registered multimodal accounting formula

The fallback chain at call time tries `ProviderNative` first when native usage is available, `LocalTokenizer` when a matching tokenizer is registered, `ProviderCountingApi` when the provider exposes a counting operation, and `CharacterApproximation` last. The chosen source is recorded so post-hoc accuracy analysis can compute per-counting-source delta percentages.

### 6.4 Cost Computation

Anchor: `ledger.cost-computation`

Cost is never stored as an unkeyed scalar in any ledger row. Cost is a projection over usage. When stored or displayed, it is keyed by provider, model, tokenizer, usage source, and the pricing snapshot that produced it. Cost is computed on demand from `TokenUsageRecord` × the `PricingTier` in effect at the record's `cost_calculated_at`:

- `PricingTier { provider_id, model_id, input_usd_per_million, output_usd_per_million, cache_creation_usd_per_million, cache_read_usd_per_million, multimodal_pricing, pricing_version, effective_from, effective_until }`
- `cost_usd = (input_tokens / 1_000_000 × input_usd_per_million) + (output_tokens / 1_000_000 × output_usd_per_million) + (cache_creation_tokens / 1_000_000 × cache_creation_usd_per_million) + (cache_read_tokens / 1_000_000 × cache_read_usd_per_million) + multimodal_cost`

Pricing tiers are user-maintained; the user adds or edits pricing through the settings system. The system never assumes a default pricing; queries that need cost emit a typed `PricingUnavailable` error when no pricing tier matches.

### 6.5 Accuracy Telemetry

After every call, post-response token counting compares the provider-reported counts to any local pre-call estimate. The delta is recorded as a `TokenCountEstimationTelemetry` ledger entry:

- `estimated_count` (pre-call local estimate using `LocalTokenizer` or `CharacterApproximation`)
- `actual_count` (provider-native count from response)
- `delta_pct` (percentage delta)
- `tokenizer_id` and `model_id`
- `request_id` cross-reference to the `ModelCallCompleted` entry

The telemetry table supports per-tokenizer accuracy analysis: "your token estimates for model X have been averaging 12% below actual." Settings consume telemetry to recommend tokenizer changes or safety margin adjustments.

### 6.6 STT / TTS Usage

Speech-to-text and text-to-speech calls record analogous attribution:

- `SttUsageRecord { provider_id, model_id, audio_seconds, duration_ms, request_id }`
- `TtsUsageRecord { provider_id, voice_id, chars_synthesised, audio_seconds_generated, request_id }`

These are sibling ledger entries to `TokenUsageRecord`; cost calculation reads the same `PricingTier` mechanism with audio-specific pricing dimensions.

### 6.7 Boundary

Per-call attribution is owned by this file. Per-model pricing maintenance, accuracy projections, and budget-enforcement actions are owned by adjacent specs (File 17 and the future Budget and Telemetry specs). This file specifies what must be recorded; those specs specify what to do with the records.

## 7. `Hook`

Anchor: `ledger.hook`

### 7.1 Definition

A `Hook` is a typed subscriber on the canonical event bus. It is the canonical extensibility primitive: every component that wants to react to system events, intercept proposed actions, or extend the runtime registers as a `Hook` against the bus.

Hook registration is unified; dispatch is not. Blocking hooks run through interceptable boundary dispatch before the proposed action proceeds. Non-blocking hooks observe emitted events through the live bus after the authoritative subsystem has emitted or recorded the fact.

Every hook declares:

- the `event_kinds` it subscribes to (closed canonical kinds plus registered `Custom` kinds)
- its `mode`: `Blocking` (the executor / emitter awaits the hook's decision before continuing) or `NonBlocking` (the hook observes without holding the emitter)
- its `priority` (`i16`, lower runs first; convention `-100` for audit / logging, `0` for transformers / validators, `+100` for the approval router)
- its `timeout_ms` or equivalent deadline profile for external/hanging handler safety; this is configurable and is not a correctness condition
- its `hook_category` (`approval`, `validator`, `completion_verification`, `postcondition_check`, `safety_gate`, `transformer`, `formatter`, `enricher`, `localizer`, `observer`, or registered extension)
- its `authority_class` (`observe_only`, `narrowing_only`, `allow_capable`, `substitute_capable`; per `policy.internal-composition-policy-inspectors` (File 06 §3.3))
- its `handler` reference (in-process closure, registered capability id, shell-script command, MCP tool reference)
- its `source` (`Builtin`, `Subsystem { id }`, `Plugin { id, version }`, `McpServer { server_id }`, `Api { api_id }`, `UserDefined { scope }`)
- its `enabled` flag (settings-controlled per scope)
- its `subscription_id` (stable identifier for revocation reference)
- per-error-class retry behavior overrides
- the typed `payload_filter` (optional declarative filter narrowing which events of the subscribed kinds reach the hook — by capability id, by run id, by sensitivity, by source, by argument shape)

### 7.2 Hook Decision Vocabulary

Anchor: `ledger.hook-decision-vocabulary`

A blocking hook returns one of four typed `HookDecision` outcomes (per `run.hook-integration`, File 04 §23.3):

- `Continue { reason }` — proceed with the original event payload; the emitter continues
- `Substitute { new_payload, reason, substitution_kind }` — proceed with a hook-modified payload; `substitution_kind` is `narrowing_only`, `redaction`, `transparent_redirect`, or registered extension. Semantic target / action changes (changing what the agent does, not how the proposal is shaped) require `Block` and a follow-up ask-user flow, not silent `Substitute`.
- `Block { reason, error_kind }` — abort the proposed action; the executor records a denial and the typed reason flows in-band as a tool result (per `run.denial-is-in-band`, File 04 §8.3)
- `RedirectSuggestion { target_capability_id, suggested_args, reason }` — abort the proposed action and signal that the agent should retry using the suggested capability; the agent loop consumes this as a typed retry signal

The four-outcome vocabulary is closed. A hook decision outside this set is an Explicit Rejection (§18).

### 7.3 Priority and Ordering

Anchor: `ledger.priority-ordering`

The canonical priority convention (per `run.hook-integration`, File 04 §23.3):

- `-100` — audit and logging hooks (capture pre-validation state, observe-only authority)
- `0` — transformers, validators, narrowing hooks (default for most extensions)
- `+100` — the approval router and equivalent final-decision hooks (post-validation, the policy layer's authoritative decision)

Within the same priority, hooks run in stable registration order, with ties logged as warnings on first occurrence. The executor evaluates blocking hooks in priority order and composes proposal transformations before terminal decisions:

- `Continue` leaves the proposal unchanged.
- `Substitute` stages a transformed proposal and normally allows later hooks to inspect the transformed proposal.
- `Block` is terminal and skips remaining hooks unless a higher-authority canonical override path explicitly applies.
- `RedirectSuggestion` is terminal for the current proposal and returns a typed retry suggestion.

All substitutions record safe before/after hashes or summaries. The approval router evaluates the final substituted proposal, not the original proposal when earlier hooks transformed it.

User-authored and third-party hooks register with explicit priority within the `[-99, +99]` envelope (cannot place above the approval router or below the canonical audit tier without explicit user-defined-policy approval). They can register at the same priority as built-in transformers / validators; tie-break ordering is registration order.

### 7.4 Authority Classes

Anchor: `ledger.authority-classes`

Each hook declares an `authority_class` (per `policy.internal-composition-policy-inspectors`, File 06 §3.3):

- `observe_only` — may emit notes and explanations through `DebugLog` events; may not produce a `Block`, `Substitute`, or `RedirectSuggestion` decision; the executor treats any non-`Continue` decision from an `observe_only` hook as `Continue` plus a recorded warning
- `narrowing_only` — may produce `Block`, `Substitute { substitution_kind: narrowing_only | redaction }`, or `RedirectSuggestion`; may not produce `Continue` that bypasses a prior hook's stricter decision
- `allow_capable` — may produce `Continue` even when prior hooks expressed concern (used by the approval router and equivalent terminal-authority hooks); registered only by `Builtin`, `Subsystem`, `Verified`, or explicitly user-approved sources
- `substitute_capable` — may produce `Substitute { substitution_kind: transparent_redirect }` (changing the target capability while preserving semantics); registered with the same trust restriction as `allow_capable`

`Community`, `Unverified`, `Plugin`, `McpServer`, `Api`, and `UserDefined` sources default to `narrowing_only` until the user explicitly upgrades authority through source-approval (per `policy.source-approval-flow`, File 06 §9). No hook can bypass `permission_floor`, typed-confirmation requirements, contradiction detection, or touched-resource constraints.

### 7.5 Timeout and Fail-Direction

Each blocking hook subscription declares a timeout/deadline profile used only as a safety guard against hung handlers. If the handler does not return a decision within the configured guard, the executor synthesizes a default decision per the hook category, authority class, and boundary risk:

- security-category hooks (`approval`, `validator`, `completion_verification`, `postcondition_check`, `safety_gate`) default-on-timeout to `Block { reason: "hook timeout" }` and default-on-error to `Block { reason: "hook error" }`
- non-security hooks (`formatter`, `enricher`, `localizer`, `observer`) default to `Continue` with the original payload plus a warning
- non-security hooks that can allow or substitute a consequential pre-action proposal default to fail-closed, because their absence could permit unsafe execution

The same category-and-authority rule applies on hook handler error. User settings may override fail-direction per hook within policy limits. Security-category hooks cannot be set to fail-open without typed confirmation.

Per-error-class retry behavior is configurable (per `run.hook-integration`, File 04 §23.3 and `policy.approval-router` (File 06 §3.5)): a hook that fails because of a known transient cause (provider rate limit, sandbox temporary unavailability, recoverable transport failure) may be configured to retry within its safety guard rather than fail immediately. The retry classification is part of the hook's declaration.

`HookTimedOut` and `HookHandlerError` ledger entries record the timeout / error, the synthesized default decision, and the hook's authority class.

### 7.6 Hook Lifecycle Events

A hook participates in the lifecycle through:

- `HookSubscriptionRegistered` — when the hook registers (at startup, plugin install, MCP server connect, user action, or source-approval flow completion)
- `HookSubscriptionUnregistered` — when the hook unregisters (at shutdown, plugin uninstall, MCP server disconnect, user action, or revocation)
- `HookSubscriptionEnabledChanged` — when the hook's `enabled` flag toggles at any scope (per-scope settings overlay)
- `HookFired` — when a matching event reaches the hook
- `HookDecisionRecorded` — when the hook returns a typed decision (blocking hooks)
- `HookTimedOut` — when the handler exceeds `timeout_ms`
- `HookHandlerError` — when the handler raises an error
- `HookActionInvoked` — when the hook's action invokes a capability, runs a shell script, or emits a synthesized event (§12)

### 7.7 Hook Categories

Hooks fall into canonical categories that share defaults:

- **Approval hooks**: the approval router (per `policy.approval-router`, File 06 §3), the typed-confirmation flow, the batched-approval flow. Priority `+100`, blocking, fail-closed, `allow_capable` authority.
- **Quality-control validators** (future Quality Control spec): structural / semantic / real-time validators. Priority `0`, blocking, fail-closed by default as security-category hooks unless their owning policy explicitly classifies them as advisory, `narrowing_only` authority.
- **Audit and logging hooks**: structured-logging recorders, telemetry collectors. Priority `-100`, blocking (so logs capture pre-validation state) or non-blocking (so logs do not slow execution), fail-open, `observe_only` authority.
- **Transformers** (per `run.hook-integration`, File 04 §23.3): argument normalizers, sensitivity-tag adjusters, locale-converters. Priority `0`, blocking, category/authority-dependent fail-direction, `narrowing_only` or `substitute_capable` authority for the substitution kind they emit.
- **Observers** (per `run.hook-integration`, File 04 §23.3): UI state-awareness watchers, surface inspectors, completion summarizers. Non-blocking (the emitter does not wait), `observe_only` authority, fail-open.
- **Completion-verification hooks** (per `run.termination`, File 04 §22): deterministic or model-mediated post-execution checks of whether the run satisfied the user's request. Per-run cadence (every N steps, in parallel, sequentially before completion, or only on explicit `verify_now`). Blocking when sequential, non-blocking when parallel; `narrowing_only` authority.
- **Stuck detectors** (per `run.stuck-detection`, File 04 §20.3): deterministic stuck-pattern matchers plus opt-in model-mediated detectors. Non-blocking; emit `StuckDetected` events that hooks consume to inject corrective prompts or escalate.
- **Recovery hooks**: subscribe to `TypedErrorRaised` events; emit recovery strategy decisions (per `run.recovery`, File 04 §20.2). `narrowing_only` authority.
- **Surface mutation observers** (per `surface.surface-relevant-events`, File 07 §13): subscribe to surface-relevant events to react to capability registration, availability changes, source connections. Non-blocking, `observe_only`.
- **Entity event observers** (per `artifact.events`, File 09 §20): subscribe to artifact / claim / evidence / observation events for memory promotion, knowledge-base curation, or downstream analysis. Non-blocking, `observe_only`.
- **Streaming UI observers**: subscribe to `MessageChunk`, `StreamProgressBatch`, `BlockCommitted` to update the streaming UI. Non-blocking, `observe_only`.
- **Background workers**: memory consolidator, SRS scheduler, system audit writer, data lineage tracker, watch poller, scheduled task runner. Each spawns and subscribes to its triggering events. Non-blocking, `observe_only`.

Each category has settings-driven defaults (priority, timeout, fail-direction, authority) that subscribers may override within their authority envelope. The categories are conventional groupings; the canonical rule is that every hook declares its own typed parameters.

### 7.8 Boundary

This section defines the hook primitive. The approval router's specific algorithm is owned by File 06. The completion-verification hook surface's specific deterministic / model-mediated mechanics are owned by `run.termination` (File 04 §22) and the future Quality Control spec. Specific quality-control validators are owned by the future Quality Control and Validation spec. This file specifies the subscription contract, the decision vocabulary, the priority and authority rules, and the lifecycle events.

## 8. Hook Registration and Discovery

Anchor: `ledger.hook-registration-discovery`

### 8.1 Built-in Hooks

The system ships with built-in hooks registered at startup:

- the approval router (`policy.approval_router`) on `ToolCallProposed` at priority `+100`
- the structured-logging audit hook (`logging.audit_recorder`) on every consequential event at priority `-100`, blocking
- the telemetry collector (`telemetry.metrics_collector`) on every event, non-blocking, observe-only
- the canonical stuck detectors (`runtime.stuck_pattern_matcher`) on `ToolCallExecuted`, non-blocking
- the canonical completion-verification deterministic floor (`runtime.completion_forgery_guard`) on `RunStatusChanged { to: Completed }`, blocking, narrowing
- the memory consolidator background worker (`memory.consolidator`) on `AgentTurnCompleted` and scheduled triggers, non-blocking
- the data lineage tracker (`data.lineage_tracker`) on `BlockCommitted` for blocks with certain kinds, non-blocking
- the watch poller (`scheduler.watch_poller`) on watchdog ticks, non-blocking

The full set is declared in built-in capability declarations (per File 05) and registered during startup phase 1 (per `capability.startup-registration`, File 05 §16.1).

### 8.2 Subsystem-Registered Hooks

Subsystems (work surfaces, substrate services per `capability.capability-source` (File 05 §9.1)) register their own hooks at subsystem load. Examples:

- Coder subsystem registers a git-status watcher on `FileExternallyModified` events
- Web subsystem registers a session-watchdog hook on its registered browser-session lifecycle `Custom` events
- Memory subsystem registers a memory-extraction hook on the cross-cutting turn-completion boundary and declares memory-specific events in the Memory spec
- Data Processor registers a lineage hook on data-transformation events
- System Agent registers an audit-log writer on every system-mutation event

Subsystems declare their hook subscriptions in their `SubsystemSurfaceSpec` (per `surface.subsystem-surface-spec`, File 07 §5) or in a dedicated `subsystem_hooks` declaration.

### 8.3 Plugin / MCP / API / User-Defined Hooks

External and user-defined sources register hooks through the same capability-registration mechanism (per `capability.runtime-mutation`, File 05 §16.2) with proposal-first source-approval (per `policy.source-approval-flow`, File 06 §9). A registration declaration includes:

- the subscription's `event_kinds`, `mode`, `priority`, `timeout_ms`, `authority_class`, `handler` reference, `payload_filter`
- the hook's `description` for the user
- the source's identity and trust state

The source-approval flow surfaces the proposed hook subscription to the user before activation: declared event kinds, declared authority class, declared handler kind (shell script command, registered capability id, MCP tool name), declared timeout, declared fail-direction. The user can accept defaults, customize (override priority, narrow authority, change fail-direction), deny outright, defer source-level policy, or cancel registration.

Sources with `Community` or `Unverified` trust default to `narrowing_only` authority and cannot register at the `+100` priority of the approval router or below `-99`. The user can explicitly upgrade authority through source approval.

### 8.4 User-Authored Hook Declarations

Users author hooks through one of three mechanisms:

- **Settings-backed declarations**: hooks registered through the canonical settings system (per File 15) with a typed `HookDeclaration` schema. Persisted in the settings substrate; sync behavior follows the setting's locality and sensitivity rules.
- **File-based declarations**: an infrastructure-owned hook declaration file may declare hooks in TOML with the same schema. The runtime watches the file through event-driven file watching and re-registers hooks on edit.
- **Runtime registration capability**: the agent or the user invokes `tools.register_hook` (a registered capability with `UserApproval` tier) to add a hook at runtime. The capability call carries the full hook declaration and goes through the source-approval flow.

User-authored hooks default to the user's identity as the source (`UserDefined { scope: user_id }`). The user can author hooks at `conversation`, `workspace`, or `global` scope.

### 8.5 Hook Discovery and Inspection

The hook system exposes inspection through canonical read-only capabilities:

- `hooks.list` — enumerate registered subscriptions with their declarations and current `enabled` state
- `hooks.inspect { subscription_id }` — return the full declaration including handler reference, recent decision history, and recent error rate
- `hooks.decision_history { subscription_id, time_range }` — return the recent typed decisions the hook returned (within sensitivity-aware filters)

These capabilities are `ReadOnly` tier and respect the standard agent-exposure rules (per `policy.agent-exposure-policy-settings`, File 06 §16.4). The user-facing inspector lens (per `surface.inspector-lens`, File 07 §12.4) renders the hook catalog.

### 8.6 Boundary

The registration mechanism is owned by File 05 (capability registry) for the registry side and this file for the hook-subscription contract. Source-approval is owned by `policy.source-approval-flow` (File 06 §9). Settings persistence and profile-layer resolution are owned by File 15. File-based hook discovery is an infrastructure/plugin concern whose enablement and visibility are settings-controlled.

## 9. Hook Effect Vocabulary

Anchor: `ledger.hook-action-vocabulary`

### 9.1 Definition

A `HookAction` is what the hook does when it fires. Every hook declares one of the canonical action kinds plus the action-specific payload:

- `RunScript { command, args, env, stdin_template, timeout_ms, working_directory, sensitivity_classification }` — execute a shell command over a typed wire protocol. The runtime spawns the command, writes the typed JSON event payload to its stdin, awaits a typed JSON decision on stdout. Stderr captures errors. The wire protocol is closed canonical; the JSON shape is specified in §9.2.
- `InvokeCapability { capability_id, args_template, sensitivity_classification }` — invoke a registered capability through the standard `run.call-pipeline` (File 04 §8.2) pipeline. The hook receives the capability's typed result as the hook's decision input.
- `EmitEvent { event_kind, payload_template }` — synthesize a new event into the bus. The synthesized event carries the canonical envelope (with `parent_event_id` set to the triggering event) and the typed payload. Useful for transforming one event into multiple downstream events or for "this happened, but as a different kind."
- `InternalHandler { handler_id }` — invoke an in-process registered handler function. Used by built-in and subsystem hooks; not available to plugin / MCP / user-defined sources without explicit source-approval upgrade.

The action is settled at registration; a hook does not switch action kinds at runtime. If a hook needs multiple actions, it registers multiple subscriptions or uses a single `InvokeCapability` action whose target capability orchestrates the multiple actions internally through the capability pipeline.

### 9.2 `RunScript` Wire Protocol

Shell-script hooks operate over a typed JSON wire protocol:

- **stdin** (from runtime to handler): a JSON object containing the canonical event envelope and the typed event payload. The runtime adds metadata fields (`event_kind`, `subscription_id`, `hook_call_id`, `expected_response_schema`) at the top level. Sensitivity-tagged fields in the payload are redacted at the wire boundary if the hook's authority class does not include access to the sensitivity level.
- **stdout** (from handler to runtime): a JSON object containing the typed `HookDecision`. The schema:

```
{
  "decision": "continue" | "block" | "substitute" | "redirect_suggestion",
  "reason": "<string>",
  "new_payload": { ... } | null,
  "substitution_kind": "narrowing_only" | "redaction" | "transparent_redirect" | null,
  "target_capability_id": "<string>" | null,
  "suggested_args": { ... } | null,
  "error_kind": "<string>" | null,
  "context_modification": "<string>" | null,
  "system_message_injection": "<string>" | null
}
```

The `context_modification` field is a hook-specific extension allowing the hook to add attributed text to the next model request (per the cline pattern); it is consumed by the agent loop when the hook is on a user-input-submitted or `PreToolUse`-equivalent event.

The `system_message_injection` field similarly injects a system-level note (e.g., "memory available" hint from claude-mem; "loop detected" warning from openclaw).

- **stderr**: any output here is captured as a `DebugLog` event with `Sensitive` sensitivity, attributed to the hook. The runtime does not require stderr to be empty.
- **exit codes**: exit code 0 means the stdout JSON is the decision. Exit code 2 (or other configured "client bug" codes) indicates a client-side bug and produces `HookHandlerError`. Non-2 non-zero exit codes are treated as transport failures and produce `HookHandlerError`; the synthesized default decision applies per fail-direction rules.

The runtime enforces:

- the timeout: kills the handler process at `timeout_ms`
- `Secret`-tagged payloads: never written to stdin in raw form; the runtime substitutes safe labels per per-field sensitivity_field_map (per `block.per-field-override`, File 08 §9.2)
- the working directory: the hook's declared working directory; default is the active workspace root
- the environment: the runtime passes a minimal allowlist of environment variables (per shell-operations.md); additional variables are declared in the hook's `env` configuration

### 9.3 `InvokeCapability` Semantics

An `InvokeCapability` hook is a wrapper around a registered capability. The capability runs through the standard `run.call-pipeline` (File 04 §8.2) pipeline, including its own policy evaluation, validators, isolation, and result production. The hook's authority class limits which decisions the capability's typed result can map to: an `observe_only` hook cannot use `InvokeCapability` to invoke a capability that emits a `Block` decision; the wrapper enforces this by treating non-`Continue` outcomes as `Continue` plus a warning.

`InvokeCapability` actions are the canonical mechanism for "use the registered capability infrastructure to make a hook decision." It composes the registry, the policy layer, the executor, and the ledger uniformly.

### 9.4 `EmitEvent` Semantics

An `EmitEvent` hook emits a new event into the bus when fired. The synthesized event:

- carries the canonical envelope with `parent_event_id` set to the triggering event
- carries `originating_hook_id` and causal chain metadata so recursion and self-triggering can be detected
- has the kind and payload declared in the hook's action
- inherits the triggering event's `sensitivity` unless the hook declaration overrides (subject to the sensitivity-monotonicity rule: only raise, never lower)
- is recorded as a ledger entry if the kind is one of the consequential kinds

Use cases: transforming a raw event into a higher-level specialized event (for example, a capability completion fires an `EmitEvent` hook that synthesizes a subsystem-specific registered `Custom` event); annotating events with hook-computed metadata (for example, a stuck detector fires `EmitEvent` to synthesize `StuckDetected` with the diagnosed pattern).

Hook recursion is allowed only inside explicit safety bounds. A hook does not receive its own derivative events by default. Subscriptions that opt into recursive handling declare maximum depth, cycle policy, and whether repeated loops are allowed. The runtime detects causal cycles and records typed hook failures when configured bounds are exceeded. Users may override limits through settings, but infinite unbounded loops are not a valid default.

### 9.5 `InternalHandler` Semantics

An `InternalHandler` action invokes an in-process function registered with a stable `handler_id`. The function takes the typed event payload as input and returns a typed `HookDecision`. Used by built-in and subsystem hooks; not exposed to external sources (plugins, MCP, user-defined) by default. A plugin or MCP source that wants to register an `InternalHandler` action requires explicit user approval of the handler binary, with `Verified` trust classification.

### 9.6 Boundary

The hook-effect vocabulary is closed: `RunScript`, `InvokeCapability`, `EmitEvent`, `InternalHandler`. New hook-effect kinds require a canonical-spec update. Hook-effect handlers themselves (the shell command implementation, the capability handler, the in-process function) are not owned by this file; they are implementation details that the canonical mechanism dispatches into.

## 10. Sensitivity-Aware Persistence and Retention

Anchor: `ledger.sensitivity-aware-persistence-retention`

### 10.1 Three Classes

Every ledger entry and every event payload carries a `sensitivity` tag drawn from the canonical closed set:

- `Public` — the entry / event may appear in shareable exports, may be cached by external services that handle public content (provider-side model-request caches when permitted), and is persisted in the durable ledger with default retention
- `Sensitive` — the entry / event contains user-private or workspace-specific data; excluded from shareable exports and clipboard-copy operations by default; persisted in the durable ledger; subject to shorter default retention if settings configure it; never sent to external telemetry without explicit user opt-in
- `Secret` — the entry / event contains credentials, raw API keys, OAuth tokens, password content, hidden user files/blocks, or equivalent never-leak material. `Secret` payloads are persisted to the durable ledger with payload redaction applied at commit; only `safe_description` strings persist, never the raw secret. The original raw `Secret` material is held only in transient memory or the credential/vault substrate and zeroed after use.

### 10.2 Producer-Seeded Sensitivity

Anchor: `ledger.producer-seeded-sensitivity`

The capability emitter (per `capability.permission-policy-fields`, File 05 §3.5 `data_sensitivity`) seeds the sensitivity tag at emission. Per-field overrides through `sensitivity_field_map` (per `block.per-field-override`, File 08 §9.2) refine individual fields. The producer cannot lower a field's effective sensitivity below its inherited or declared baseline.

The runtime stamps sensitivity automatically when known patterns appear (a credential vault reference, an API key in arguments, a password field, a user-marked secret block, a protected file scope), defaulting up rather than down. Explicit user override raising the sensitivity is always allowed; lowering requires a typed-confirmation policy override (per `policy.permission-floor-typed-confirmation`, File 06 §7).

### 10.3 Persistence Effects

- `Public` entries / events: persisted to the durable ledger at default retention; replayable, exportable, queryable through standard mechanisms
- `Sensitive` entries / events: persisted at default retention or settings-configured shorter retention; excluded from default exports; queryable but not surfaced in default search projections; not sent to external telemetry without opt-in
- `Secret` entries / events: persisted with redaction; the entry's structural fields (envelope, kind, cross-references, producer, timestamp) persist, but the payload retains only a `safe_description` (a one-line summary that does not reveal the secret content). The raw payload is held only in transient memory or a credential/vault subsystem; references to it from in-flight handlers expire when handling completes. Future Secret-related queries return the safe description.

The redaction happens at commit, not at query time. The runtime ensures that no path (ledger row, sync stream, export, telemetry, debug panel rendering, structured log output) ever sees raw `Secret` content. This is the ledger/event/sync/export/telemetry enforcement of the cross-cutting backend secret boundary (`secret.backend-boundary`, File 17 §23.6): raw `Secret` material never crosses out of the backend's transient buffers and vault substrate; only opaque references and safe descriptions persist or propagate.

### 10.4 Retention Policies

Retention is configurable per sensitivity class through settings:

- `events.retention.public` — policy default, commonly indefinite unless user-controlled storage management says otherwise
- `events.retention.sensitive` — policy default, configurable per source class, workspace, and export/sync profile
- `events.retention.secret` — N/A for raw content; safe descriptions follow `events.retention.sensitive`

Per-event-kind retention overrides are configurable: a noisy event kind (e.g., `ToolCallStreamingPartial`) may have shorter retention than other entries. The override applies to durable storage only; the bus delivery is unaffected.

Storage maintenance (`LedgerCompactionRan` events) runs as a background worker and respects retention. Compacted entries collapse into summary entries linked by `consolidates` cross-reference (mirroring `block.kind-catalogue` (File 08 §3.1) `Consolidation` block-kind semantics).

Retention and pruning decisions are themselves durable facts. No storage layer may silently prune `Sensitive` or safe-description `Secret` records without a policy-level transition recorded in the ledger.

### 10.5 Hash-Chained Audit-Log Tier

A subset of ledger entries (security-sensitive operations) is also represented in a local hash-chained audit overlay for tamper-evident integrity:

- entries: an infrastructure-owned local audit-chain file
- structure: `{ ledger_entry_id, timestamp, actor, action, target, canonical_redacted_entry_hash, prev_entry_hash, entry_hash, device_id, chain_id }`
- chain: `entry_hash = sha256(prev_entry_hash + canonical_redacted_entry_hash + timestamp + actor + action + target + device_id)`
- per-device only — the audit log NEVER syncs across devices; each device's hash chain has its own integrity
- never replaced by ordinary ledger — the audit log is an integrity overlay; every audit entry references an ordinary ledger entry, but only the audit overlay carries the hash chain
- never disabled — even when telemetry / logging is disabled, security-sensitive operations write to the audit log

Operations that flow through the audit log:

- every approval verdict (`PolicyDecisionMade`)
- every lease grant / revoke (`LeaseGranted`, `LeaseRevoked`)
- every typed-confirmation completion (`TypedConfirmationSatisfied`)
- every floor violation (`PolicyFloorViolated`)
- every source approval / denial (`SourceRegistrationApproved`, `SourceRegistrationDenied`)
- every credential or secret operation registered by the Security, Credentials, and Trust Boundaries spec, including secret storage, backend-only resolution-for-use, rotation, revocation, deletion, export, and vault backup/restore
- every system-state mutation (`SystemChangeApplied`, `SystemChangeRolledBack`)
- every hard delete (`BlockHardDeleted`, `ArtifactHardDeleted`)
- every `DeniedFloorOverridden`

The audit overlay is verifiable: a verifier computes `entry_hash` for each audit overlay entry in order and checks it matches the recorded `entry_hash`. Any mismatch produces `AuditChainTamperDetected` event (high-severity, surfaced to the user, halts sync of the affected device).

### 10.6 Export and Share Filtering

Default export and share operations include only `Public`-tagged entries. The user can explicitly opt to include `Sensitive` entries per export by acknowledging the inclusion through typed-confirmation. `Secret` payloads are never included (only safe descriptions).

Cross-device sync follows the same rules: default sync transports `Public` entries; `Sensitive` syncs only when the user enables it per workspace or per device; `Secret` content never syncs (only safe descriptions persist locally on each device, with the hash chain remaining per-device).

Settings `events.sensitivity_export_default`, `events.sensitivity_sync_default`, `events.sensitivity_clipboard_default` govern the defaults.

### 10.7 Boundary

Sensitivity is a durable property of every entry and event. The policy layer (File 06) decides what to do at policy boundaries based on sensitivity. The event stream uses the same value set for transient coordination. Surface rendering consumes sensitivity to gate displays. The future Security, Credentials, and Trust Boundaries spec owns credential vault internals and trust cryptography; this file specifies the canonical sensitivity classification and the persistence rules.

## 11. Replay Semantics

Anchor: `ledger.replay-semantics`

### 11.1 Definition

Replay is reconstruction or controlled re-execution of a past execution state from the ledger plus durable snapshots. It supports debugging ("what did the model see at time T?"), audit ("which sequence of decisions produced this artifact?"), evaluation ("re-run this dataset against a new model and compare"), forensic analysis, and learning. It does not promise byte-identical rerun of model calls or external systems unless their responses were captured or the capability is declared deterministic under the recorded inputs.

### 11.2 What Is Required for Replay

To replay a run, the system requires:

- the full ledger entries for the run's scope (every `LedgerEntry` with `cross_references.run_id = <target>` plus parent / child related runs)
- the block pool (every `Block` referenced by ledger entries; blocks are immutable per `block.block` (File 08 §2.2))
- the version-graph snapshot (the `ContextVersion` ids referenced by ledger entries; version graph is reconstructable from durable action log per `block.block-persistence-contract` (File 08 §13))
- the entity pool (every `Artifact`, `Claim`, `Evidence`, `Observation`, `Validation`, `Critique` referenced)
- the registry snapshot at the time of execution (`CapabilityDeclaration` versions, `RegisteredCapability` states, source instance metadata per `capability.registered-capability` (File 05 §10))
- the settings snapshot at the time of execution
- the policy snapshot (lease set, template states, scope-level overrides per `policy.lease-primitive` (File 06 §11))
- the world-model snapshot (active surfaces, focused elements, ui_mode, etc. per `core.world-model` (File 01 §6.7))
- the observation staleness fingerprints (per `artifact.observation`, File 09 §13)

The ledger entries reference all of these via cross-references; replay walks the references to resolve.

### 11.3 Replay Classes

Every capability declares its `replay_class` (per `capability.replay-class`, File 05 §7.3):

- `deterministic_replayable` — same inputs and same referenced state produce same result; safe to re-execute during replay without policy gates
- `snapshot_replayable` — replay requires recorded snapshots (file content at the path, page snapshot, accessibility tree fingerprint); the ledger's `staleness_fingerprint` cross-reference resolves; replay reads the snapshot rather than re-fetching live state
- `effect_replayable_with_policy` — replay would cause external effects (email send, API call, database mutation); replay treats these as "would have happened" and either skips them or routes them through a replay-specific policy (the user explicitly approves re-execution)
- `not_replayable` — closures, transient session-bound resources, inherently uncontrolled side effects; replay reads the recorded result without re-executing

The replay engine reads `replay_class` from the recorded `invocation_id`'s capability declaration version (not the current declaration; replay uses the declaration in effect at the original call time).

### 11.4 Replay Modes

The system supports three replay modes:

- **`Inspect`**: walks the ledger and resolves cross-references, producing a structured view of the execution. No re-execution. Used for debugging, audit, and "what happened" reconstruction.
- **`SimulateDeterministic`**: re-executes `deterministic_replayable` and `snapshot_replayable` capabilities, skipping `effect_replayable_with_policy` and `not_replayable`. Used for evaluation when the goal is to test whether the execution produces the same result given the same inputs.
- **`FullRerun`**: re-executes every capability, routing `effect_replayable_with_policy` through the replay-time policy (typically a sandbox or with explicit user approval). Used for testing and migration scenarios where actually running the full execution is the point.

The user / evaluator selects the mode per replay. Each replay records a `ReplayRun` entry in the ledger with mode, source run id, comparison outcome. Model output replay is byte-identical only when a provider response snapshot or equivalent captured output exists; otherwise `FullRerun` is a new execution attempt over recorded inputs.

### 11.5 Forensic Queries

The ledger supports closed canonical forensic queries:

- `query_what_did_the_agent_see_at_time_t(run_id, timestamp)` — reconstructs the agent's model context at time `t`: the assembled context blocks, active tool surface, available skills, active lease set, world-model snapshot
- `query_which_capabilities_did_run_invoke(run_id)` — enumerates all `ToolCallExecuted` entries
- `query_which_model_calls_consumed_what_tokens(run_id)` — aggregates `TokenUsageRecord` rows keyed by model
- `query_which_blocks_did_run_produce(run_id)` — enumerates `BlockCommitted` entries
- `query_which_artifacts_did_run_modify(run_id)` — enumerates `ArtifactVersionCommitted` entries
- `query_which_hooks_fired(run_id)` — enumerates `HookFired` and `HookDecisionRecorded` entries
- `query_run_lineage(run_id)` — walks `parent_run_id` and `supersedes` cross-references to produce the run's lineage chain (retries, reroutes, branches)
- `query_evidence_chain(claim_id)` — delegates to `artifact.provenance` (File 09 §15) provenance queries

Forensic queries are themselves capabilities (registered with `ReadOnly` tier) and run through the standard pipeline. Their execution is itself recorded as `ProvenanceQueryExecuted` ledger entries.

### 11.6 Boundary

Replay is the consumer of the ledger and the durable snapshots. The replay engine itself is owned by the future Evaluation and Benchmarking spec. This file specifies what is required for replay to succeed (the cross-references, snapshot identifiers, replay-class consumption); the engine realizes the actual replay.

## 12. Streaming and Live Partials

Anchor: `ledger.streaming-live-partials`

### 12.1 Streaming Categories

The system streams several kinds of partial output through the event bus:

- **Model text deltas** — `MessageChunk` events for token-by-token model output
- **Reasoning deltas** — `ReasoningChunk` events for extended-thinking content (default `Sensitive`)
- **Tool-input streaming** (per `run.streaming-partial-execution`, File 04 §12) — the model is still emitting a tool call's structured arguments; the UI may render them live ("Reading src/index.ts...")
- **Tool-output streaming** — the executing capability is emitting partial results (streaming text, growing diff, growing file content)
- **File-or-artifact live partial-write** — capabilities that write incrementally into materialized state (per `run.streaming-partial-execution`, File 04 §12 and `block.live-partial-write-capabilities` (File 08 §7.5))
- **Reasoning summary streaming** — when the provider exposes intermediate reasoning summaries
- **Progress events** — specialized progress (file conversion progress, web fetch progress, indexing progress)

### 12.2 Commit Boundary Contract

Streamed partials are not durable blocks until the producer's declared commit boundary fires (per `block.streaming-commit-boundary`, File 08 §7). The pattern:

1. Producer begins emitting partials; each partial flows through the bus as a transient `MessageChunk` / `ReasoningChunk` / `ToolCallStreamingPartial` event with a `partial_block_handle` referencing the eventual block id
2. The bus delivers partials to subscribers live (streaming UI, hook listeners that subscribe to streaming events)
3. The producer reaches its declared commit boundary
4. The runtime commits a durable `Block` (per `block.streaming-commit-boundary`, File 08 §7) and emits a durable `BlockCommitted` event and ledger entry
5. The streaming UI transitions from live partial rendering to durable block rendering on commit

Between partials and commit, the partial events fan out to the bus but do not commit to the ledger. After commit, the durable `StreamCompleted` ledger entry references the committed block id.

If the producer fails before commit (cancellation, error, timeout, crash), no committed block exists. The runtime emits `StreamCancelled` and decides per the capability's `partial_output_meaningful` declaration (per `run.cancellation`, File 04 §17.3) whether to preserve the partial as an orphan block.

### 12.3 Aggregation for Streaming

Per §5.5, streaming events aggregate before bus emission according to settings-driven delivery policies:

- `MessageChunk` aggregates into `StreamProgressBatch` events under the active chunk batching policy
- `ReasoningChunk` aggregates similarly with potentially different thresholds (per category settings)
- Tool-input streaming chunks aggregate at the same cadence
- Tool-output streaming chunks aggregate per the capability's declared `streaming_chunk_policy` (default same as `MessageChunk`)

Aggregation policies are settings-configurable per kind. The aggregation summary carries the cumulative byte count, the chunk count, and the most recent chunk content; subscribers see one batched event per interval, not one per chunk.

### 12.4 Live-Partial-Write Capabilities

For capabilities that write incrementally into materialized state (file edits, artifact generation, document generation per `run.streaming-partial-execution` (File 04 §12)), the pattern:

- the capability validates the target before any write
- the capability writes into a temp / staged location during streaming
- partials flow through the bus as `FilePartialWriteStaged` events
- on commit, atomic rename moves the staged file to the destination
- the `FilePartialWriteCommitted` ledger entry records the final outcome
- on cancellation, the staged file is deleted (`FilePartialWriteAborted`)

This preserves end-to-end atomicity: the destination is never partially written; cancellation never leaks partial corruption.

### 12.5 Resumption

Subscribers that disconnect and reconnect can request resume from their last-seen event using a transport token such as `Last-Event-Id` where supported. The reconnection request carries the last successfully-processed `event_id` and sequence scope; the bus replays events with higher `sequence` in that scope if they remain in its bounded buffer. Aggregation rebuilds from the durable counterpart when a durable counterpart exists.

This is bounded and best-effort. When the stream cannot replay the missing range, it emits or returns `StreamGapDetected`; clients reload durable projections or ledger-backed state, then resume the live tail. Transport resume tokens are conveniences, not durability guarantees.

### 12.6 Cross-Tab and Cross-Process Coordination

For coordination across multiple browser tabs, multiple processes, or multiple devices, the bus exposes coordination channels:

- intra-process: the bus itself, with in-memory broadcast
- intra-device cross-tab: BroadcastChannel pattern (per the bolt-diy and terax-ai pattern in batch-05) for browser-based UIs
- inter-process: Tauri events (or equivalent transport) for backend-to-frontend
- inter-device: cross-device sync (future Sync spec); the bus does not directly cross devices (the future Sync spec handles propagation)

The transport-layer specifics are owned by the future Runtime Infrastructure and Lifecycle spec. This file specifies the contract: every transport preserves the canonical envelope, the ordering, the sensitivity filtering, and the per-context-tuple sequence semantics.

### 12.7 Boundary

Streaming is the live half of the durable-history-versus-live-coordination split. The ledger records the commit points; the bus carries the live deltas. The aggregation policies and resumption semantics keep the bus responsive without losing coordination guarantees.

## 13. Subscription Persistence and Lifecycle

Anchor: `ledger.subscription-persistence-lifecycle`

### 13.1 Durable State

The following hook-related state is durable:

- registered subscriptions (settings-backed, file-backed, or durable plugin / MCP registration records) — survive restart
- per-subscription `enabled` flags scoped per workspace, conversation, or globally — survive restart through the settings system
- the source-approval state for each source — survive restart per `policy.persistence` (File 06 §11.6)
- the audit log of hook lifecycle events (`HookSubscriptionRegistered`, `HookSubscriptionUnregistered`, `HookSubscriptionEnabledChanged`) — durable in the ledger

The following hook-related state is computed:

- the active in-process subscription list (the runtime resolves declarations into runnable subscriptions at startup and on declaration updates)
- per-subscription performance metrics (decision counts, error rates, average latency) — derived from `HookDecisionRecorded`, `HookTimedOut`, `HookHandlerError` entries
- the currently-active hook chain for a given event kind (computed at emission time from registered subscriptions filtered by `event_kinds`, `payload_filter`, and `enabled` state)

### 13.2 Startup Sequence

On startup (per cross-cutting infrastructure/lifecycle.md):

1. the event bus initializes (subscriber registry empty)
2. built-in capability declarations register (per `capability.startup-registration`, File 05 §16.1 phase 1)
3. built-in hook subscriptions register (the approval router, structured-logging audit, telemetry collector, stuck detectors, completion-forgery guard)
4. subsystems load and register their hooks
5. plugins load and register their hooks subject to source-approval state
6. MCP servers connect and register hooks subject to source-approval state
7. external-API definitions load
8. user-defined hooks register from settings and file-based declarations
9. background workers spawn and subscribe to their triggering events
10. the bus enters operational state
11. `AppStarted` ledger entry committed

If a hook fails to register (handler unresolved, source unavailable, declaration invalid), the failure is recorded as a `HookSubscriptionRegistrationFailed` event and the hook is marked `unavailable` until the underlying cause resolves; startup does not abort.

### 13.3 Runtime Mutation

Subscriptions register, update, and unregister at runtime through canonical capability calls:

- `hooks.register { declaration }` — `UserApproval`-tier; goes through source-approval flow for non-builtin sources
- `hooks.unregister { subscription_id }` — `UserApproval`-tier
- `hooks.update { subscription_id, declaration_updates }` — `UserApproval`-tier; updates fields like priority, timeout, fail-direction
- `hooks.set_enabled { subscription_id, enabled, scope }` — `UserApproval`-tier (or lower if the user has authorized scoped management)

Each capability call goes through the standard pipeline and produces the canonical lifecycle events.

### 13.4 Shutdown

On graceful shutdown (per cross-cutting infrastructure/lifecycle.md):

1. `AppShuttingDown` event emitted with the configured shutdown policy.
2. new work is rejected or queued according to policy.
3. in-flight work receives cancellation / pause / fast-finish signals according to its capability declaration.
4. critical ledger and audit-overlay records that were already acknowledged as successful are flushed synchronously.
5. noncritical buffers and diagnostics are flushed best-effort without making shutdown correctness depend on elapsed time.
6. final lifecycle state is committed when the process can do so safely, then the process exits.

Atlas should be ready to close at any time. Graceful handling is best effort for active work; correctness comes from commit boundaries and restart reconciliation, not from waiting for a shutdown timer.

On forceful shutdown (crash, SIGKILL, power loss, task-manager kill), in-flight events may be lost. Durable ledger entries written before the crash remain. The next startup detects orphan runs (per `run.cancellation`, File 04 §17.3) and reconciles per the orphan-run rules: runs in `running` or `cancelling` state at process restart transition to `failed` with typed reason `process_restart_orphan` unless they declared `resume_on_restart: true`.

### 13.5 Restart Reconciliation

On restart:

- the ledger reloads (durable state survives)
- orphan runs are identified and reconciled (per `run.cancellation`, File 04 §17.3)
- `BorrowGrant`s reload (per `surface.reconstruction-across-restart`, File 07 §14.2)
- subscription registry rebuilds from durable declarations
- the user sees a surface for orphan runs with per-run resume-or-discard affordances
- `AppStarted` ledger entry committed

### 13.6 Boundary

Subscription persistence is owned by this file (the contract) and the settings system / capability registry (the storage). The actual on-disk format is owned by File 20.

## 14. Cancellation, Lifecycle, and Restart

Anchor: `ledger.cancellation-lifecycle-restart`

### 14.1 Cancellation Recording

Every cancellation or kill action (per `run.cancellation`, File 04 §17.3) records:

- `CancellationRequested` — requester, target, scope (`single_target` / `cascade`), and cooperative-stop policy
- `CancellationProgressing` — listeners that have acknowledged and remaining targets
- `CancellationEscalated` — escalation to forceful termination when cooperative stop is not sufficient
- `KillRequested` / `KillSucceeded` / `KillFailed` — forceful stop outcome for an individual process-like target
- `CleanupCompleted` — cleanup outcome for staged files, sandboxes, subprocesses, browser sessions, and orphanable resources
- `CancellationCompleted` — final outcome with cleanup performed, cooperative-vs-escalated-vs-forceful classification, partial outputs retained or discarded, final status

Each cancellation entry references the target's `run_id` or narrower target id. Targets include run, child run, model call, provider stream, capability call, hook execution, sandbox, process, browser session, MCP call, scheduler job, and registered extension targets. Cascade operations record the root target and each affected child target where safely knowable.

The same target model powers user-facing process management surfaces: the UI can show active process-like units and allow the user to stop a whole cascade or a specific sandbox, tool call, subprocess, stream, or child run.

`OrphanOutputDetected` ledger entries record when a listener reports completion after the run is already `cancelled`; the orphan output does not commit.

### 14.2 Intervention Recording

Every user intervention (per `run.user-intervention`, File 04 §17.1) records:

- `InterventionRecorded` with the intervention kind (`continuation_with_new_instruction`, `pause`, `cancel`, `branch`, `reroute`, `approval_grant`, `approval_denial`, `scope_narrowing`, `explicit_takeover`), the actor, the target
- `TakeoverStarted` and `TakeoverEnded` when `control` (per `run.minimum-durable-reconstruction`, File 04 §2.6) transitions

User actions during takeover record as first-class ledger entries attributed to the user, indistinguishable in audit from agent-produced entries (per `run.user-intervention`, File 04 §17.1).

### 14.3 Restart Behavior

Per §13.5, restart loads the durable state and reconciles orphans. The user is presented with orphan runs and resume-or-discard affordances. Auto-resume of orphans is forbidden (per `run.explicit-rejections`, File 04 §28 explicit rejection).

### 14.4 Boundary

Cancellation and intervention mechanics are owned by File 04. This file specifies the durable recording.

## 15. Settings

Anchor: `ledger.settings`

### 15.1 Configurable Dimensions

Every mechanism in this file is configurable through settings. The dimensions:

**Hook configuration:**

- `hooks.timeout_default_ms` per category (`approval`, `validator`, `transformer`, `observer`, `completion_verification`, `audit`) as a safety guard, not a correctness condition
- `hooks.fail_direction_default` per category and authority class, with typed-confirmation required before security-category hooks may fail open
- `hooks.retry_per_error_class.<error_class>` per hook category (e.g., transient network failure may retry once before fail-closed)
- `hooks.priority_default` per category
- `hooks.priority_max_user_authored` and `hooks.priority_min_user_authored` (preventing user-authored hooks from claiming the approval router tier or below the canonical audit tier without explicit policy approval)
- `hooks.recursion_depth_limit` and per-hook recursion policy
- `hooks.discovery_path` — file-based hook discovery location, when infrastructure exposes one
- `hooks.shell_script_allowlist` — explicit allowlist of shell-script hook handler commands per source class

**Event bus configuration:**

- `events.buffer_size_per_subscriber`
- `events.aggregation.<event_kind>.batch_ms` — per-kind aggregation cadence
- `events.aggregation.<event_kind>.batch_max_count` — per-kind aggregation cap
- `events.aggregation.<event_kind>.suppress_threshold` — per-kind suppression (e.g., mouse moves below 50px)
- `events.resumption_window` — bounded best-effort live replay window
- `events.frontend_bridge_max_event_kinds` — max event kinds the frontend may subscribe to simultaneously
- `events.debug_panel_ring_buffer_size`
- `events.delivery_class.<event_kind>` — delivery class override within canonical limits

**Ledger configuration:**

- `ledger.retention.public`
- `ledger.retention.sensitive`
- `ledger.retention.<entry_kind>` per kind (e.g., `ToolCallStreamingPartial` shorter retention)
- `ledger.compaction_policy` (`disabled`, `default`, `aggressive`)
- `ledger.compaction_schedule`
- `ledger.export_default_sensitivity` (default `Public`)
- `ledger.sync_default_sensitivity` (default `Public`; user opts in to `Sensitive`)

**Per-call attribution configuration:**

- `attribution.token_source_preference` — preference order for token-counting sources
- `attribution.tokenizer_fallback_chain` per provider/model descriptor
- `attribution.cache_token_pricing.<provider>` per provider (cache_creation_multiplier, cache_read_multiplier)
- `attribution.cost_calculation_enabled`
- `attribution.pricing_tier_user_managed` — flag indicating the user maintains pricing tiers

**Audit log configuration:**

- `audit.enabled` (never globally disable for security-sensitive operations)
- `audit.path`
- `audit.hash_algorithm`
- `audit.tier_membership.<entry_kind>` — which entry kinds participate in the audit log

**Streaming configuration:**

- `streaming.chunk_batch_ms` per kind
- `streaming.chunk_batch_max_bytes` per kind
- `streaming.partial_block_orphan_retention` per capability (when `partial_output_meaningful` is true)
- `streaming.frontend_render_pace_ms`

**Lifecycle configuration:**

- `lifecycle.shutdown_safety_guard`
- `lifecycle.background_worker_health_policy`
- `lifecycle.orphan_run_reconciliation_default` (must surface to user, never `auto_resume`)
- `lifecycle.log_rotation_size`

**Sensitivity configuration:**

- `events.sensitivity_export_default` (`Public` excluded by default, `Sensitive` requires opt-in, `Secret` never)
- `events.sensitivity_clipboard_default`
- `events.sensitivity_sync_default`
- `events.sensitivity_telemetry_default`
- `events.sensitivity_override.<capability_id>` — per-capability override

### 15.2 Settings-Key Convention

Hook and event settings use the namespaced dotted-key convention per `capability.settings-key-convention` (File 05 §18.2). Plugin / MCP-registered hooks register their settings keys at registration time under the source identity.

### 15.3 Agent Exposure of Settings

Per `policy.agent-exposure-policy-settings` (File 06 §16.4):

- `hooks.timeout_default_ms.*`, `events.aggregation.*`, `ledger.retention.*` — `OnRequest` (agent reads on demand); the agent never sees raw subscription declarations
- `hooks.discovery_path` — `OnRequest`
- the active hook chain for the current event — `Hidden` (the agent does not see which specific hooks are about to fire)
- `audit.enabled` — `Hidden`; agents cannot disable audit
- `attribution.token_source_preference` — `OnRequest`
- `ledger.compaction_policy` — `OnRequest`

### 15.4 Settings Changes Emit Events

Per `run.event-stream` (File 04 §23.2) and cross-cutting/settings.md, every settings change emits `SettingChanged` to the bus. Affected subscriptions recompose on receipt; affected ledger queries re-evaluate.

### 15.5 Boundary

This file names the settings dimensions. The settings system owns cascade resolution, storage, and validation. Defaults belong to tested settings profiles, not hardcoded constants in this canonical layer.

## 16. Hash-Chained Audit Log

Anchor: `ledger.hash-chained-audit-log`

### 16.1 Definition

The hash-chained audit log is a local integrity overlay on a subset of ledger facts for security-sensitive operations. Audit overlay entries reference ordinary ledger entries and hash their canonical redacted representation; they do not replace the ledger and do not form a second execution-history store.

### 16.2 Required Fields

Each audit-overlay entry carries:

- `ledger_entry_id` — cross-reference to the corresponding ordinary ledger entry
- `timestamp` — full-granularity
- `actor` — user identity, agent identity, automation identity, system identity
- `action` — typed verb (e.g., `approve_tool_call`, `grant_lease`, `revoke_lease`, `accept_typed_confirmation`, `apply_system_change`, `rollback_system_change`, `delete_block`, `delete_artifact`, `register_capability`, `approve_source`, `deny_source`)
- `target` — the affected primitive (capability id, block id, artifact id, lease id, source id, etc.)
- `canonical_redacted_entry_hash` — hash of the canonical redacted ledger entry or safe summary
- `prev_entry_hash` — the prior entry's `entry_hash`; for the first entry, the genesis hash (zero bytes or installation-specific genesis seed)
- `entry_hash` — hash over the prior hash, canonical redacted entry hash, actor, action, target, timestamp, device id, and chain id
- `device_id` and `chain_id` — identify the local chain

### 16.3 Per-Device Integrity

The audit log NEVER syncs across devices. Each device maintains its own hash chain with its own genesis. Sync of ordinary ledger entries does not propagate audit-log integrity; per-device audit logs preserve integrity for that device's actions only.

This is intentional: cross-device sync would require resolving hash-chain merges, which would weaken the integrity guarantee. Per-device audit logs are tamper-evident on the device they protect.

### 16.4 Membership

The canonical operation classes that participate in the audit log:

- every policy decision (`PolicyDecisionMade`)
- every approval grant or denial (`ApprovalGranted`, `ApprovalDenied`)
- every lease lifecycle event (`LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `LeaseNarrowed`)
- every typed-confirmation completion (`TypedConfirmationSatisfied`, `TypedConfirmationMismatched`)
- every floor violation (`PolicyFloorViolated`)
- every source approval / denial (`SourceRegistrationApproved`, `SourceRegistrationDenied`, `SourceRegistrationDeferred`)
- every credential or secret operation (the future Security, Credentials, and Trust Boundaries spec registers the entries)
- every system-state mutation declared by System Agent, runtime infrastructure, or security specs
- every hard delete (`BlockHardDeleted`, `ArtifactHardDeleted`, `LeaseHardDeleted`, `CapabilityHardDeleted`)
- every `DeniedFloorOverridden` (the typed-confirmation override path through `Denied`)
- every `RunCompletionForgeryAttempted`
- every hook authority-class change

Settings `audit.tier_membership.<entry_kind>` allows the user to add additional entry kinds to the audit tier; the canonical baseline above is the minimum.

### 16.5 Verification

A verifier reads the audit log entries in order, recomputes `entry_hash` for each, and checks against the recorded hash. Any mismatch produces:

- `AuditChainTamperDetected` event with the offending entry's `ledger_entry_id`
- the device's sync stops until the user resolves (replay from a known-good backup or accept the tamper detection and proceed with a fresh chain)
- the user is surfaced with the audit chain's state

Verification may run:

- on demand through `audit.verify` (a registered `ReadOnly` capability)
- at startup using the configured verification profile
- during shutdown only when it does not delay fast close; shutdown is not a correctness condition for audit integrity

### 16.6 Boundary

The audit log is a local integrity overlay over selected ledger entries. The future Security, Credentials, and Trust Boundaries spec owns the cryptographic primitives and audit storage details. This file specifies the structure, membership, and verification contract.

## 17. Lifecycle Integration

Anchor: `ledger.lifecycle-integration`

### 17.1 Startup Phases

Startup (per cross-cutting infrastructure/lifecycle.md and `capability.startup-registration` (File 05 §16.1)):

1. infrastructure: SQLite / libsql open, schema migrations applied, file system watchers spawned, event bus initialized
2. registry: capability declarations register (built-in → subsystem → plugin → MCP → API → user-defined)
3. settings: settings cascade resolves, settings change watchers spawn
4. hooks: hook subscriptions register per §13.2
5. background workers: spawned and subscribed to their triggering events
6. UI: frontend bridge opens
7. `AppStarted` ledger entry committed

Startup ordering is deterministic; replay reads `AppStarted` to know the state in effect.

### 17.2 Background Workers

Background workers are process-like execution units registered by their owning subsystems. Cross-cutting examples include audit-overlay writing, lineage tracking, system-watch evaluation, and scheduled-trigger dispatch. Domain workers such as memory consolidation or SRS scheduling declare their own `Custom` events in their owning specs.

Each worker emits `BackgroundWorkerSpawned`, health/progress events under its declared delivery class, and `BackgroundWorkerStopped`. Failure of a worker emits `BackgroundWorkerFailed` and triggers recovery according to settings and policy. Time-based cadences, when a worker inherently needs them, are settings-controlled scheduling inputs, not correctness conditions for this layer.

### 17.3 Cancellation Token

A global intervention handler maintains a cancellation token shared between the agent loop, long-running tool calls, sandbox operations, and git service calls. User-initiated interrupt sets the token; operations check at safe points and abort cleanly. The interrupt is itself recorded as `InterventionRecorded`.

### 17.4 Shutdown

Per §13.4, shutdown stops new work, signals active work, flushes acknowledged critical ledger/audit-overlay records synchronously, best-effort flushes noncritical buffers, and records final lifecycle state when safely possible. Correctness does not depend on a shutdown timer.

### 17.5 Boundary

Lifecycle integration ties the durable and live recording layer into the application's startup, runtime, and shutdown sequences. The actual lifecycle mechanics are owned by the future Runtime Infrastructure and Lifecycle spec.

## 18. Explicit Rejections

Anchor: `ledger.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel event bus, parallel ledger, or parallel hook system — every event flows through one bus, every consequential fact persists to one ledger, every extensibility point is a hook on the canonical bus; subsystems, plugins, MCP servers, and user-defined sources never invent parallel mechanisms
- silent execution: any capability invocation that does not produce a `ToolCallProposed` followed by either `ToolCallExecuted` plus `ToolCallCompleted` or `ToolCallFailed` or `ToolCallDenied` violates the canonical pipeline contract; every consequential action is recorded
- silent hook decisions: any blocking hook that returns a decision without emitting `HookDecisionRecorded`, or any timeout / error without `HookTimedOut` / `HookHandlerError`, is invalid
- unkeyed model-dependent scalars: token counts, costs, cache statistics, or any model-dependent value as an unkeyed integer or float on a ledger row violates `core.explicit-rejections` (File 01 §8) and is rejected at commit
- `Secret`-tagged payloads persisting to the durable ledger: the commit validator rejects entries that would persist raw secret content; only safe descriptions persist
- mutable ledger entries: a committed `LedgerEntry`'s structural fields are fixed; corrections create new entries via `supersedes` cross-reference, never in-place updates
- ledger entries with payload schemas outside the closed canonical catalogue plus registered `Custom` extensions — every entry is typed
- time-based hook firing: hooks fire only on event emission; the runtime never polls for hooks; periodic background work uses background workers (per §17.2), not hook-polling
- hard-coded hook timeouts: every timeout is a settings dimension; canonical defaults exist but the user can override per category
- hooks that bypass the event bus: a hook handler must dispatch through the standard `HookAction` taxonomy (`RunScript`, `InvokeCapability`, `EmitEvent`, `InternalHandler`); ad-hoc procedural execution is rejected
- hooks that mutate the ledger directly: hooks emit decisions that the executor records as `HookDecisionRecorded` entries; hooks do not write ledger entries themselves
- implicit ledger inference from events: events are live coordination; consequential events must be explicitly committed to the ledger by the executor / emitter; the ledger never silently materializes from event observation
- live events as durable history: events are transient; the ledger is durable; pure UI-coordination events do not persist
- cross-device sync of the audit log: the audit log is per-device for hash-chain integrity; sync of ordinary ledger entries is separate
- silent retention or pruning: every retention transition is `LedgerCompactionRan` or per-kind retention policy; nothing disappears without a recorded event
- canceled-but-still-running operations: cancellation must record `CancellationCompleted` with the final state; runs do not silently complete after cancellation
- forgery of run completion: the status-transition forgery guard rejects `running → completed` transitions without ledger evidence of action (per `run.termination`, File 04 §22)
- hooks that exceed their declared authority: a hook declared `observe_only` returning a non-`Continue` decision is downgraded to `Continue` plus a warning; hooks cannot escalate authority at runtime
- ad-hoc hook decision shapes: only `Continue`, `Substitute`, `Block`, `RedirectSuggestion` are valid decisions; ad-hoc payloads or out-of-vocabulary decisions are rejected
- silent batched approval: every approval (whether per-call or batched) records `ApprovalRequested` / `ApprovalGranted` / `ApprovalDenied`
- bypassing the approval router for capability invocations: every consequential capability invocation goes through `ToolCallProposed`, which the approval router subscribes to at priority `+100`
- per-capability custom approval logic in handlers: capability authors implement operations, not approval flows; approval is a hook subscription, not a capability-internal concern
- using event sequence numbers across devices for global ordering: sequences are per declared `sequence_scope`; cross-device ordering relies on the future Sync spec, not on a global monotonic counter
- recording per-tokenizer scalars on the block: token counts are computed on demand keyed by tokenizer per `block.what-is-computed` (File 08 §13.2); never persist a single integer on the block row without model identifier
- mutating ledger entries to reflect retroactive sensitivity reclassification: sensitivity is fixed at commit; if a `Public` entry is later judged `Sensitive`, the original entry persists but a sibling `SensitivityReclassified` entry is committed and downstream filters honor the reclassification
- the bus claiming durability guarantees: the bus is transient coordination; consequential events also persist to the ledger but the bus delivery itself is best-effort with bounded buffers; subscribers seeking durable guarantees query the ledger
- combining `Substitute` with semantic target change: `Substitute { substitution_kind: transparent_redirect }` may change a target capability to a safer equivalent only when the change is declared transparent; meaningful behavioral changes require `Block` followed by ask-user
- pre-validation hooks running after validators: priority `-100` hooks run first; placement is canonical, not negotiable; ordering relies on this convention
- ledger entries with omitted envelopes: every entry carries the full envelope; contextual refs inside `context_refs` may be absent only when inapplicable
- hook handlers that mutate global state outside the typed action taxonomy: handlers either return a typed decision, invoke a registered capability, or emit a synthesized event; direct global-state mutation is forbidden
- using shutdown grace periods as correctness: successful critical ledger/audit-overlay commits must be durable before success is reported; shutdown flushing is best effort for remaining noncritical buffers
- the ledger silently becoming the version graph: the ledger references version ids; File 11 owns the version-tree action log; ledger entries do not duplicate version-graph operations
- duplicating per-capability data into ledger payloads: ledger entries reference capability declarations via `(capability_id, capability_version)`; they do not embed the declaration content
- using `Custom` event kinds for canonical concerns: if a new canonical-kind need arises, the canonical catalogue extends through a canonical-spec update; `Custom` is for subsystem-, surface-, plugin-, MCP-, API-, or user-defined extensions, not for canonical workarounds
- treating cancellation as a destructive operation: cancellation is a recorded ledger event; partial outputs may persist per declaration; cancellation does not erase prior ledger entries

## 19. Consequences for Later Specs

Anchor: `ledger.consequences-for-later-specs`

Every later spec that produces or consumes execution facts, emits or subscribes to events, registers a hook, or queries the ledger for replay, audit, telemetry, or evaluation consumes this layer as defined here.

The canonical principles later specs must follow:

- emit events through the canonical bus with the standard envelope; never invent a parallel event bus or omit envelope fields
- record consequential facts to the ledger through the canonical `LedgerEntry` mechanism; never invent a parallel durable record store
- register extensibility points as `Hook` subscriptions on the canonical bus; never invent a parallel hook system or middleware chain
- honor the typed `HookDecision` vocabulary (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`); never invent new decision shapes
- honor the priority convention (`-100` audit, `0` validators / transformers, `+100` approval router); never claim positions outside the user-authored envelope without explicit canonical extension
- honor the authority-class semantics; never escalate hook authority at runtime
- honor the per-call attribution requirement (`TokenUsageRecord` keyed by model identifier); never store unkeyed model-dependent scalars
- honor the sensitivity-aware persistence rules (`Public` / `Sensitive` / `Secret`); never persist `Secret` raw content
- honor the forgery guards (run-completion contract, unkeyed-scalar rejection); never bypass through subsystem-internal paths
- consume the closed `AppEvent` and `LedgerEntryKind` catalogues; declare new specialized kinds through `Custom { namespace, name, payload }` with proposal-first source-approval
- record specialized events through the canonical mechanism; the ledger and bus integrate them uniformly with the standard envelope, sensitivity, and cross-references

Specific integration contracts:

- Version Graph, Commits, and Projections consume ledger commit boundaries and emit version events through this layer; the ledger references version ids but does not own version-tree invariants.
- Retrieval, Indexing, Knowledge Base, Memory, Perception, Web, Coder, Teacher, Data Processor, GUI Control, System Agent, SRS, Automation, Workflows, and surface-specific specs declare specialized event and ledger-entry kinds through `Custom { namespace, name, payload }` rather than adding them to the closed canonical catalogue here.
- Context Assembly and Compaction emit context-budget and compaction facts through the bus and ledger, while owning the model-request assembly and compaction algorithms.
- Model Strategy, Provider, Rate Limits, and Usage Accounting consume `TokenUsageRecord`, provider identity, tokenizer identity, and pricing snapshots; they must not store unkeyed token or cost scalars.
- World Model, Settings, Storage, Sync, Security, Sandbox, Process Control, Workspaces, Control Rails, Plugins, MCP integrations, UI, Quality Control, Evaluation, Telemetry, Runtime Infrastructure, and Packaging consume this file's envelope, delivery-class, sensitivity, hook, audit-overlay, replay, and ledger contracts.

Specific integration contracts will be stated in those specs when they are written. Until then, the canonical contract here is the load-bearing reference for every spec that touches execution recording, live coordination, or extensibility.
