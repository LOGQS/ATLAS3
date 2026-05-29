> Lossless render of canonical/10-execution-ledger-event-stream-and-hooks.md — original 160641 chars

# Execution Ledger, Event Stream, and Hooks

Status: Canonical.

## Scope
- Defines: `ExecutionLedger` (durable append-only record of every consequential execution fact); the closed canonical `LedgerEntry` kinds + schema + cross-references shared with `Block`/`Artifact`/`Claim`/`Evidence`/`RegisteredCapability`/`Lease`/`ToolSurface`/version-graph commit/approval record; `EventStream` (typed live coordination channel); `EventEnvelope` (canonical envelope: demux identifiers, per-stream monotonic sequence, full-granularity timestamp, closed sensitivity classification); `AppEvent` (closed event-kind catalogue + `Custom { namespace, name, payload }`); `Hook` (extensibility primitive over the bus — typed decision vocabulary, priority convention, authority-class semantics, per-error-class retry, hook-action contract); relationship between live `EventStream` and durable `ExecutionLedger`; per-call model-call attribution with `TokenUsageRecord`, `TokenSource` hierarchy, cost keyed by model identifier (per [`core.explicit-rejections`], File 01 §8); replay semantics; canonical forgery guards (run-status transition from [`run.termination`] File 04 §22, unkeyed-scalar rejection from [`core.explicit-rejections`] File 01 §8, sensitivity-aware persistence); sensitivity-aware retention (`Public`/`Sensitive`/`Secret`); hash-chained audit-log tier (per-device, excluded from sync); subscription model; hook-action contract; streaming/live partials + commit boundary + aggregation policies; lifecycle integration; settings dimensions (with agent-exposure rules per [`policy.agent-exposure-policy-settings`], File 06 §16.4); explicit rejections; the canonical contract later specs consume.
- Does NOT define: `Run` lifecycle/capability-call pipeline/hook-decision authority in evaluation context/cancellation primitives (File 04 — this file specifies durable+live recording contracts the pipeline obeys); `CapabilityDeclaration` field set/`RegisteredCapability` runtime state/`CapabilityInvocation` structural fields (File 05); policy-evaluation algorithm/lease lifecycle/approval router/approval flows (File 06); `ToolSurface` composition/zoning/per-lens contracts (File 07); `Block` schema/`BlockKind` catalogue/`BlockContent` variants/commit validator/streaming-to-block boundary (File 08); entity layer (`Artifact`/`Claim`/`Evidence`/`Citation`/`Observation`/`Validation`/`Critique`/`Provenance`) + entity event vocabulary (File 09); version-graph commit storage/action-log algorithms/materialized-view rebuild (File 11); storage schema/on-disk layout/indexing/projection rebuild/durability invariants (future Storage); sync/import/export/portability (future Sync — this file says which entries sync, which don't [audit log per-device], how sensitivity gates participation); credential storage internals/trust crypto/secret-vault primitives (future Security — this file specifies the `Secret` class + the never-persist rule); sandbox primitives/process control/isolation (future Sandbox — this file specifies events + `backend_id`); model-strategy/provider routing/fallback/rate-limit/provider-health (Files 16/17 — this file specifies per-call attribution + per-error-class retry classification); retrieval/indexing/knowledge-base/RAG/hybrid-search (File 12 — ledger is the forensic/replay substrate); context-assembly/compaction/token-budget/block selection (File 13 — this file specifies the typed `ContextPressureObserved` boundary + compaction events flowing through bus); UI shell/rendering/modal layouts/accessibility (future UI); specific provider transports (Tauri IPC, SSE, WebSocket, Unix sockets, MCP — future Runtime Infrastructure; this file specifies the canonical wire-format contract).

## Source Resolution
- Resolves events/ledger entries/hooks/observability/streaming/audit/attribution/replay into one boundary: live coordination + durable execution history.
- Events = transient coordination signals; ledger entries = durable facts. Ledger is the source of truth for what happened.
- One envelope + dispatch mechanism covers execution progress, capability proposals, policy decisions, hooks, registry changes, version commits, errors, cancellations.
- Domain-specific events are `Custom` extensions registered by owning specs, not predeclared global kinds.
- Hooks are typed integration points with declared authority, ordering, fail-direction, audit behavior.
- Secret/high-sensitivity payloads redacted or referenced by key; observability must not become a data leak.
- Replay/inspection reconstruct durable behavior from ledgered facts without pretending nondeterministic provider calls are byte-identical.

## 1. Chosen Model `ledger.chosen-model`
- Three primitives: `ExecutionLedger`, `EventStream`, `Hook`. Share one `EventEnvelope`, one closed cross-cutting `AppEvent` catalogue with `Custom` extension, one hook decision vocabulary, one cross-cutting bus.
- `ExecutionLedger` = durable, append-only, queryable record of consequential execution facts (status transitions, routing decisions, capability invocations, approval verdicts, model calls with per-call attribution keyed by model identity, block commits, version commits, artifact-version commits, claim publications, evidence links, observation captures, validation outcomes, errors, recovery decisions, child-run relationships, cancellations, interventions) as `LedgerEntry` in the canonical pool.
- `EventStream` = live coordination channel carrying typed `AppEvent` through one event bus. Every reacting subsystem subscribes (streaming UI, hooks, inspectors, progress views, approval routers, validators, structured loggers, telemetry, replay machinery, cross-tab coordination, frontend reactivity, automation triggers). Events carry the canonical envelope, the closed sensitivity classification, the per-stream monotonic sequence. Consequential events flow through both bus + ledger; transient coordination events (token deltas, cursor updates, scroll positions, UI focus changes) flow through the bus only.
- `Hook` = canonical extensibility primitive. One registration model; two dispatch paths: blocking hooks run at interceptable boundaries before the proposed action continues; non-blocking hooks observe emitted events. A hook declares `event_kinds`, `mode`, `priority`, `timeout_ms`, category, authority class, handler reference, source. A blocking hook returns one of four `HookDecision`: `Continue`, `Substitute { new_payload, reason }`, `Block { reason }`, `RedirectSuggestion { target_capability_id, suggested_args, reason }`. The executor ([`run.call-pipeline`] File 04 §8.2) and policy layer ([`policy.approval-router`] File 06 §3) consume hook decisions through the same mechanism. No parallel hook system: approval router, QC validators, completion-verification hooks, user guardrails, plugin/MCP hooks register through the same mechanism with source-approval gating.
- Composition: executor produces events at each capability-call pipeline phase ([`run.call-pipeline`]) — `ToolCallProposed`, `ToolCallApproved`, `ToolCallExecuted`, `ToolCallCompleted`, `ToolCallFailed`, `ToolCallDenied`; hooks fire at each phase incl. approval router at `ToolCallProposed`; consequential events also commit to ledger. Model-strategy layer emits `ModelCallStarted`/`ModelCallCompleted` with full attribution; ledger records `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)` per [`run.execution-ledger`] (File 04 §23.1). Block layer ([`block.streaming-commit-boundary`] File 08 §7) emits `BlockCommitted` (with `block_id`, `kind`, `producer`, `origin_run_id`, `content_hash`, sensitivity, scope) to bus + ledger. Version graph (File 11) emits `VersionCommitted` (with `version_id`, `parent_version_id`, `op_summary`, `diff`). Policy layer ([`policy.approval-policy-templates`] File 06 §12) emits `PolicyDecisionMade`, `LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `PolicyContradictionDetected`, `PolicyFloorViolated` + records each. Entity layer ([`artifact.events`] File 09 §20) emits `ArtifactCommitted`, `ArtifactLifecycleChanged`, `ClaimPublished`, `EvidenceLinked`, `ObservationCommitted`, `ValidationCommitted`, `CritiquePosted`, `ProvenanceQueryExecuted`. Surface layer ([`surface.surface-relevant-events`] File 07 §13) emits `ToolSurfaceComposed`, `CapabilityBorrowed`, `CapabilityRegistered`, `CapabilityAvailabilityChanged`. Routing layer (File 03) emits `RouteAttached`, `RoutingFrameComposed`, `RouterDecisionEmitted` + records the route record per [`routing.route-record`] (File 03 §3.5).
- One envelope, one vocabulary, one bus, one ledger. Other specs declare new event/ledger-entry kinds via `Custom { namespace, name, payload }`, registered via canonical capability-registration ([`capability.runtime-mutation`] File 05 §16.2 proposal-first) and gated by source-approval ([`policy.source-approval-flow`] File 06 §9). Extensions never produce parallel buses/ledgers/hook systems.
- Elaborates canonical primitives from [`core.execution-ledger`] (File 01 §6.4) (`Execution Ledger`), §6.5 (`Event Stream`), §6.14 (extensibility planes). Honors [`run.ledger-events-commits`] (File 04 §23).
- `ExecutionLedger` supersedes: "audit log", "execution log", "operation log", "history table", "session log", "command log", "trace log", "activity log", "telemetry store", "agent journal". `EventStream` supersedes: "event bus", "live stream", "real-time channel", "pub-sub channel", "broadcast channel", "SSE stream", "WebSocket channel", "Tauri event channel". `Hook` supersedes: "callback", "trigger", "middleware", "interceptor", "before/after handler", "pre/post hook", "filter chain", "decision pipeline", "subscriber", "observer", "PreToolUse / PostToolUse handler", "guardrail middleware". `EventEnvelope`, `AppEvent`, `LedgerEntry`, `LedgerEntryKind`, `HookDecision`, `HookSubscription`, `TokenUsageRecord` are the canonical typed shapes; earlier names map into these.

## 2. Boundaries With Adjacent Layers `ledger.boundaries-with-adjacent-layers`
### 2.1 File 04
- [`run.call-pipeline`] (§8.2) defines the pipeline; this file specifies the durable record + live event each step produces. [`run.execution-ledger`] (§23.1) gives canonical minimum content; this file expands into full closed catalogue + per-call attribution schema + forgery guards + replay-reference rules. [`run.event-stream`] (§23.2) defines minimum envelope identifiers; this file specifies the canonical envelope (conversation field is `conversation_id`; legacy wording normalized). [`run.hook-integration`] (§23.3) defines the typed hook decision vocabulary + priority convention; this file specifies the full hook contract/subscription schema/category-aware fail-direction/dispatch/source-trust/action-handler taxonomy. [`run.completion-contract`] (§2.7) + §22; this file specifies ledger-side enforcement at status transition, the contract-revision forgery guard, the configurable completion-verification hook surface. [`run.failure-in-parallel-work`] (§15.3) `sibling_abort_on_failure` + `depends_on`; this file specifies ledger entries recording per-batch dispatch decisions + fan-out events. [`run.cancellation`] (§17.3); this file specifies cancellation ledger entries + events (`CancellationRequested`, `CancellationProgressing`, `CancellationCompleted`) with requester/affected scope/cooperative-vs-forceful classification/partial-output retention. [`run.retry-reroute-branch`] (§19); this file specifies entries (`RunRetryStarted`, `RerouteRequested`, `BranchCreated`) + cross-refs linking new run to prior. [`run.error-handling`] (§20); this file specifies typed error classification + recovery-attempt entries (`RecoveryStrategyApplied`, `ContextPressureObserved`, `StuckDetected`, `StuckEscalated`, `BudgetWarning`).

### 2.2 File 05
- File 05 owns `CapabilityDeclaration`, `RegisteredCapability`, `CapabilityInvocation`. This file specifies what the ledger records about an invocation: declaration version, resolved backend binding identity at call time, resolved touched-resource expressions, resolved model-mediated classifications, resolved permission tier, applied lease identity, call outcome, produced block ids, produced event ids, error variant if any. Invocation record owned by [`capability.invocation-record`] (File 05 §11); this file specifies the ledger-side cross-ref + events at each phase. [`capability.runtime-mutation`] (§16.2) owns proposal-first registration; this file specifies entries (`CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityUpdated`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `CapabilityTrustChanged`).

### 2.3 File 06
- [`policy.approval-router`] (§3) owns the approval router as a blocking hook subscriber on `ToolCallProposed` at priority `+100`. This file specifies the canonical event it subscribes to, the typed decision it emits, the entries it produces (`PolicyDecisionMade`, `ApprovalRequested`, `ApprovalGranted`, `ApprovalDenied`). [`policy.lease-primitive`] (§11) owns `Lease`; this file specifies lease-lifecycle entries (`LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `LeaseNarrowed`). [`policy.approval-policy-templates`] (§12) owns policy event vocabulary; flow through canonical bus + ledger. [`policy.approval-ui-surface-contract`] (§13); approval requests/responses flow through bus with standard envelope (incl. `sensitivity`).

### 2.4 File 07
- [`surface.visibility-composition-resolution-algorithm`] (§9) owns composition algorithm; this file specifies `ToolSurfaceComposed` event when a composition is consumed by an invoker + the ledger entry recording the consumed snapshot for replay. [`surface.surface-relevant-events`] (§13) owns the surface event vocabulary (`ToolSurfaceComposed`, `CapabilityBorrowed`, `CapabilityBorrowReturned`, `CapabilityZoneChanged`, `CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `ToolSurfaceShrunk`, `ToolSurfaceOverflow`, `SubsystemSurfaceSpecUpdated`, `PrimarySurfaceChanged`, `SurfaceSettingsChanged`, `SourceConnected`, `SourceDisconnected`, `LensFilterChanged`, `ShortcutConflict`); flow through canonical bus, consequential subset commits.

### 2.5 File 08
- [`block.commit-boundary-set`] (§7.6) owns the boundary set; this file specifies `BlockCommitted` event + entry (block id, kind, producer, content hash, sensitivity, scope, parent linkage). [`block.block-lifecycle-non-destructive-edits`] (§6) owns lifecycle (`Raw`, `Active`, `Masked`, `Dropped`, `Recovered`) + `PinState` as derived per-`ContextVersion` view-state; this file specifies `BlockLifecycleChanged`/`BlockPinChanged` events + entries. [`block.hard-delete`] (§6.6) owns hard-delete; this file specifies `BlockHardDeleted` event + entry (deleting actor, deletion reason, orphaned-references set, composition-materialization outcome).

### 2.6 File 09
- [`artifact.events`] (§20) owns the entity event vocabulary (`ArtifactCreated`, `ArtifactVersionCommitted`, `ArtifactLifecycleChanged`, `ArtifactReviewStateChanged`, `ArtifactValidationStateChanged`, `ArtifactMaterialized`, `ArtifactExternallyEdited`, `ArtifactArchived`, `ArtifactDiscarded`, `ArtifactRestored`, `ArtifactHardDeleted`, `ClaimPublished`, `ClaimStatusOverridden`, `ClaimWithdrawn`, `EvidenceLinked`, `EvidenceLinkRemoved`, `CitationCaptured`, `ObservationCommitted`, `ValidationCommitted`, `CritiquePosted`, `ProvenanceQueryExecuted`); flow through canonical bus, consequential subset commits, `Secret`-tagged payloads do not persist.

### 2.7 Cross-Cutting Substrate
- Structured logging substrate uses the `tracing` crate with `#[tracing::instrument]`; this file specifies every ledger-event boundary carries span context (`span_id`, `parent_span_id`, `operation`, `service`) linking logs to entries. Typed error substrate ([`core.typed-errors`] File 01 §6.9) defines `AppError` with discriminant variants; error-recording entries carry the typed `AppError` + an optional `TraceContext`. Settings substrate ([`core.settings-system`] File 01 §6.8) defines the typed settings system; this file specifies settings keys this layer reads. Service-layer substrate defines services as Rust traits returning `Result<T, AppError>`; this file specifies `LedgerService`, `EventBusService`, `HookService` as canonical service traits, frontend access via Tauri commands or equivalent.

### 2.8 Boundary
- This file owns: closed `LedgerEntryKind` catalogue; `EventEnvelope` + closed `AppEvent`; `Hook` subscription contract/decision vocabulary/action taxonomy/registration; per-call attribution schema (`TokenUsageRecord`); forgery guards/sensitivity-aware persistence/replay-reference contracts; hash-chained audit-log tier; settings dimensions; explicit rejections; consequences.
- It does NOT own: capability-call pipeline mechanics ([`run.call-pipeline`]); capability declaration field set (File 05); policy evaluation algorithm (File 06); surface composition algorithm (File 07); block schema/version graph internals (Files 08/11); entity layer (File 09); storage on-disk layout (future Storage); sync mechanics (future Sync); security primitives (future Security); UI rendering (future UI); model-strategy/provider-routing internals (Files 16/17).

## 3. `ExecutionLedger` `ledger.execution-ledger`
### 3.1 Definition
- Durable, append-only, queryable record of consequential execution facts; canonical source of truth for replay/audit/evaluation/telemetry/learning/forensic queries.
- The ledger IS: durable across process restart/conversation archival/version-graph rewrites/storage migrations; append-only (once committed, content does not change; corrections create new entries linked via `supersedes`); queryable by `conversation_id`, `run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, time range, entry kind, capability id, model id, error variant, sensitivity, scope, custom predicate; scoped (canonical set `run`/`intent_thread`/`task`/`conversation`/`workspace`/`global`/`reusable_policy_rule` matching [`policy.lease-primitive`] File 06 §11 lease scopes + [`block.block-scope`] File 08 §11 block scopes); sensitivity-aware (every entry carries `Public`/`Sensitive`/`Secret`; `Secret` payloads do not persist, see §10); cross-referenced (every entry naming `Block`/`Artifact`/`Claim`/`Lease`/`Capability`/`Version`/`Run`/`Task`/`IntentThread`/`Conversation`/etc. carries the stable identifier); attribution-bearing (every model-call entry carries the per-call `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)`).
- The ledger is NOT: a UI representation (UI consumes via projections); a memory/knowledge-base mechanism (separate primitives; ledger may be read but does not subsume); the version graph (commits emit entries + reference block ids in the same pool, but File 11 owns the version tree's invariants; the ledger records that a commit happened); a parallel block pool (references `block_id`, does not duplicate content); a substitute for the event stream (events = real-time; ledger = durable; consequential events commit to both; pure UI-coordination events live only on the bus).

### 3.2 Required Fields (every `LedgerEntry`)
- `entry_id`: globally stable; assigned at commit; never reused/reassigned/mutated.
- `kind`: typed `LedgerEntryKind` from the closed catalogue (§4) + `Custom { namespace, name }`.
- `envelope`: the canonical `EventEnvelope` (§5.2) at recording (incl. `conversation_id`, optional context refs, `sequence_scope`, `sequence`, `timestamp`, `sensitivity`, trace/causality fields).
- `scope`: broadest visibility scope (per [`block.block-scope`]), declared at commit.
- `payload`: typed payload per `kind`; closed canonical for canonical kinds, declared at registration for `Custom`.
- `cross_references`: typed map naming canonical primitives this entry depends on/refers to: `(block_id, artifact_id, version_id, lease_id, capability_id, capability_version, source_instance_id, invocation_id, run_id, task_id, intent_thread_id, conversation_id, workspace_id)`; unused entries absent rather than null-padded.
- `produced_at`: full-granularity timestamp of recording, distinct from envelope event timestamp when event emitted earlier than commit. Timestamps are query/display metadata, may serve as explicit uncertainty-bearing fallback evidence when no sequence/causal relation can answer an ordering query; not a correctness basis.
- `producer`: typed reference to what produced the entry: `Executor { run_id, step_id }` (capability-pipeline), `RouterEmission { route_id }` (routing), `Subsystem { subsystem_id, reason }` (subsystem-internal), `Hook { hook_id, source }` (hook-decision), `UserAction { user_id, action_kind }` (user-initiated), `Automation { trigger_id }` (automation-fired).
- `entry_schema_version`: version of the record shape; storage normalizes supported earlier versions on load.
- `idempotency_key`: required for consequential writes that may be retried; scoped by producer/boundary/operation/source request. Duplicate keys reject duplicate durable facts or link repeated attempts to the original entry.
- `supersedes`: optional `entry_id` of a prior entry this corrects/retracts/amends; prior entry remains, new `entry_id` reachable via reverse-link queries (no in-place mutation).
- Payload shape is per-kind (§4). Cross-ref keys drawn from a closed canonical set; new keys register through `Custom` extension with proposal-first source approval.

### 3.3 Append-Only Invariant
- Append-only. A committed entry's `kind`, `envelope`, `scope`, `payload`, `cross_references`, `produced_at`, `producer`, `entry_schema_version` are fixed at commit. Observable corrections (misclassified typed error variant; token count later corrected by a provider's `usage` field) commit a new entry with `kind: LedgerCorrection`, `supersedes: <prior_entry_id>`, corrected payload. Prior entry remains; forensic queries see both.
- Load-bearing for audit: a reader at `t1` and again at `t2` sees the same content for any entry committed before `t1`. Mutations would defeat audit/replay/hash-chained integrity (§16).

### 3.4 Minimum Canonical Entry Set (per [`run.execution-ledger`] File 04 §23.1)
- run creation + status changes (stop reason, ordering of creation/completion, `control` per [`run.minimum-durable-reconstruction`] File 04 §2.6); route attachment (per [`routing.route-record`] File 03 §3.5); execution unit starts/finishes; capability proposals; approvals/denials/leases/policy decisions (per [`policy.approval-policy-templates`] File 06 §12); model calls (provider, model identifier, role [router/responder/critic/validator/sub-agent/etc.], input/completion/cache-creation/cache-read tokens, cost computed from per-model pricing — never unkeyed scalar; per [`core.explicit-rejections`] File 01 §8); tool calls + results; observations (per [`artifact.observation`] File 09 §13); validation results (per [`artifact.validation-critique`] File 09 §14); errors + recovery decisions; produced outputs (block ids, artifact-version ids, claim ids, evidence-link edge ids, memory-proposal ids, task-update ids); child-run relationships (parent/child run ids, spawn reason, output contract); cancellation + intervention (per [`run.user-intervention`] §17.1 + [`run.cancellation`] §17.3); block commits (per [`block.commit-boundary-set`] File 08 §7.6); version commits (File 11); artifact-version commits (per [`artifact.version-creation`] File 09 §6.3); claim publication + status changes (per [`artifact.claim`] File 09 §9); evidence-link grants/removals (per [`artifact.evidence`] File 09 §11); citation captures (per [`artifact.citation`] File 09 §12); surface compositions consumed by an invoker (per [`surface.persistence-reconstruction`] File 07 §14); capability registrations/unregistrations/lifecycle transitions (per [`capability.lifecycle`] File 05 §16); backend binding lifecycle (resolved binding rebound, source connection lost/restored, per [`capability.backend-binding-lifecycle`] File 05 §10.4); hook subscriptions + decisions (§5).
- §4 enumerates the full closed catalogue. Closed catalogue canonical for cross-cutting reasoning; `Custom { namespace, name }` canonical for specialization via proposal-first registration.

### 3.5 Storage Contract
- Persistence owned by future Storage spec. Must be durable: every structural field above; cross-ref map keys + values; per-kind payload; `entry_schema_version` for normalization-on-load.
- NOT durable (computed from substrate): per-tokenizer token counts as scalars (the canonical `TokenUsageRecord` carries per-call counts; aggregate scalars are queries); aggregate costs as scalars (computed from `TokenUsageRecord` × pricing tier on demand); per-projection materialized views (debug-panel last-N-events, telemetry dashboards, evaluation reports); secondary indexes (rebuildable).
- Reconstruction across restart/retry/edit/reroute/branch/child-run is deterministic from the durable substrate + registry snapshot + settings snapshot + world-model snapshot + per-capability replay-class declaration (per [`capability.replay-class`] File 05 §7.3). See §9.

### 3.6 Cross-References `ledger.cross-references`
- Canonical reference key set: `conversation_id` (when conversation-scoped); `run_id` (executing `Run`); `task_id` (the `Task` the run advances, if any); `intent_thread_id` (owning `IntentThread`); `workspace_id`; `parent_run_id` (child-run entries); `route_id` (the `RouteRecord` producing the run); `invocation_id` (the `CapabilityInvocation` for capability-call entries); `capability_id` + `capability_version`; `source_instance_id` (which plugin instance/MCP connection/API definition); `backend_binding_id` (resolved live binding at call time per [`capability.backend-binding-lifecycle`] — distinct from `backend_id` envelope which identifies the running provider/sandbox/process instance); `block_id`; `version_id`; `artifact_id` + `artifact_version_block_id`; `claim_id`; `evidence_link_edge_id`; `lease_id`; `approval_request_id`; `hook_id` + `subscription_id`; `observation_id`; `validation_id` + `critique_id`; `staleness_fingerprint` (entries whose mutation depended on a prior observation per [`artifact.observation`] File 09 §13); `policy_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `registry_snapshot_id` (entries whose semantics depend on snapshot state); `event_id` (when committed in response to a specific event); `supersedes_entry_id`; `parent_entry_id` (entries nesting within a parent operation, e.g., a `ChildRunSpawned` points at the spawning entry); `child_entry_ids` (optional list of consequential child entries, computed at query time, optionally cached).
- Extension keys register via the `Custom` cross-reference extension mechanism; a canonical entry referencing one MUST declare it in its kind registration (per [`capability.runtime-mutation`]).

### 3.7 Forgery Guards `ledger.forgery-guards`
- Three non-negotiable guards at commit time:
  - **Status-transition forgery guard** (per [`run.termination`] File 04 §22): `running → completed` is verified against the run's latest authorized `RunCompletionContract` ([`run.completion-contract`]). On a run whose contract required action, the transition is rejected if no `ToolCallExecuted`/`ToolCallCompleted` entry exists in scope, no `ArtifactVersionCommitted` exists in scope, and no `ModelCallCompleted` beyond pure-text response exists in scope. Fires at the ledger boundary, not only in the executor: a hook subscriber trying to record `RunStatusChanged { status: Completed }` against a no-evidence run produces `LedgerCommitRejected` + a `RunCompletionForgeryAttempted` audit entry; the run stays `running` until evidence is recorded or another terminal status (`failed`/`cancelled`/`superseded`) is committed.
  - **Contract-revision forgery guard** (per [`run.completion-contract`]): a `RunCompletionContractRevised` whose `revision_kind` is `Weakening` or `Removal` is rejected unless its `authority_source` is at least as strong as the authority that introduced each affected requirement, and the removal/weakening discharge for that authority is recorded (explicit user action for user-introduced, policy approval for policy-introduced, reroute/route override for router-introduced). A weakening/removal authored by the run's own executing agent is rejected. A rejected revision produces `LedgerCommitRejected` + `RunCompletionForgeryAttempted`. Closes the relocate-the-forgery hole: a run cannot weaken its contract to reach trivial completion.
  - **Unkeyed-scalar forgery guard** (per [`core.explicit-rejections`] File 01 §8): every model-dependent scalar (token counts, cache statistics, cost) MUST be keyed by `(provider_id, model_id, tokenizer_id)`. An entry with an unkeyed token count or cost is rejected at commit with `LedgerCommitRejected: UnkeyedModelDependentScalar`. The `TokenUsageRecord` schema (§6) enforces keying.
- Additional integrity rules: `Secret`-tagged payloads never persist to the durable ledger (§10); the commit validator rejects entries whose payload contains `Secret` material, recording a `safe_description` instead per [`artifact.tombstone-fields`] (File 09 §8.2) tombstone pattern. Every `entry_id` must be globally unique. `supersedes` must resolve to a prior entry; orphan supersession rejected. Entries referencing blocks/artifacts/claims/other primitives must reference primitives that exist at commit (or were previously committed; tombstoned primitives remain referenced via preserved identity per [`block.hard-delete`] File 08 §6.6 + [`artifact.artifact-tombstones`] File 09 §8).

### 3.8 Boundary
- Ledger defines durable execution truth; bus delivers live coordination; version graph records the version-tree state machine; storage realizes durability. None invents new entry semantics. Future Storage realizes durability; future Sync realizes cross-device propagation; future Telemetry/Logging/Observability consumes entries for projections; future Evaluation/Benchmarking reads the ledger for replay.

## 4. Canonical `LedgerEntryKind` Catalogue `ledger.entry-kinds`
### 4.1 Closed Canonical Catalogue `ledger.entry-kind-catalogue`
**Run lifecycle:**
- `RunCreated` — run instantiated; payload: trigger kind, route id, capability families, model route, attachment kind.
- `RunStatusChanged` — status transition; payload: from-status, to-status, stop reason, partial-output retention outcome. A transition to `completed` additionally references `run_completion_contract_id` (or embedded contract snapshot), satisfied-requirement list, and ledger/block/artifact/policy evidence satisfying each requirement (per [`run.completion-contract`]).
- `RunResumed` — paused or orphan-restart-resumed run; payload: prior status, reason, lease revalidation outcome.
- `RunSuperseded` — run replaced by edit/reroute/branch/retry; payload: superseding-run id, supersession reason.
- `RunCompletionContractRevised` — contract revised (per [`run.completion-contract`]); payload: `run_id`, `old_contract_hash`, `new_contract_hash`, `revision_kind` (`Additive`/`Narrowing`/`Weakening`/`Removal`), `authority_source`, `reason`, `evidence_refs`. `Weakening`/`Removal` require qualifying authority + subject to contract-revision forgery guard (§3.7).
- `RunCompletionForgeryAttempted` — forgery guard fired; payload: attempt details, forging actor's identity (rare, audited).
- `ControlTransferred` — run `control` field changed (per [`run.minimum-durable-reconstruction`]); payload: from-actor, to-actor, reason.

**Routing:**
- `RoutingFrameComposed` — router context policy assembled the frame; payload: policy id, snapshot references, included context categories.
- `PrecheckEvaluated` — deterministic precheck applied; payload: precheck id, verdict (`resolved`/`constrained`/`no_op`), changes to frame.
- `RouterDecisionEmitted` — router produced `RunIntent`; payload: resolved `RunIntent` fields per [`routing.run-intent`] (File 03 §4.3).
- `RouteRecordCommitted` — full route record persisted; payload: route_id + route record identifiers.
- `MidExecutionRerouteRequested` — reroute requested per [`routing.mid-execution-reroute`] (File 03 §12); payload: trigger source (model/runtime/user), suggested route, reasoning.
- `MidExecutionRerouteResolved` — reroute resolved through one of three paths; payload: resolution path (`router_resolved`/`self_routed`/`direct_handback`), resulting `RunIntent`.

**Capability invocation pipeline (per [`run.call-pipeline`]):**
- `ToolCallProposed` — proposal entered pipeline; payload: `CapabilityInvocation` ref, resolved arguments (sensitivity-tagged redaction), resolved touched-resource expressions.
- `ValidatorRan` — declared input validator ran (per [`capability.input-validators`] File 05 §8.1); payload: validator id, verdict (`valid`/`invalid_with_correction`/`invalid`), correction applied if any.
- `PolicyDecisionMade` — approval router emitted a decision (per [`policy.approval-router`] File 06 §3.4); payload: decision (`Continue`/`Substitute`/`Block`/`RedirectSuggestion`), contributing scope, lease used, contradictions detected.
- `ApprovalRequested` — ask-user/typed-confirmation/batched/contradiction-resolution flow opened (per [`policy.approval-ui-surface-contract`] File 06 §13); payload: `ApprovalRequest` ref.
- `ApprovalGranted` / `ApprovalDenied` — user resolved approval; payload: choice, customized constraints, typed-confirmation string if applicable (redacted).
- `LeaseGranted` / `LeaseRevoked` / `LeaseStale` / `LeaseNarrowed` — lease lifecycle (per [`policy.persistence`] File 06 §11.6); payload: lease id + lease projection over its source events.
- `PolicyContradictionDetected` / `PolicyContradictionResolved` — cross-scope conflict (per [`policy.contradiction-checking-across-scope-levels`] File 06 §14).
- `PolicyFloorViolated` — attempt to lower below `permission_floor` (per [`policy.permission-floor-typed-confirmation`] File 06 §7); payload: violating actor + override choice.
- `ClassifierMediatedDecision` — `auto-decide` classifier ran (per [`policy.auto-decide-mode`] File 06 §8); payload: classifier result, confidence, fallback choice.
- `ToolCallApproved` — proposal cleared policy; payload: per-call resolved facts (tier, touched resources, lease).
- `ToolCallDenied` — proposal denied; payload: denial reason, in-band synthesis of the typed result block id.
- `ToolCallExecuted` — capability handler invoked; payload: start timestamp, isolation primitive used (per [`run.isolation`] File 04 §16.2), backend binding instance.
- `ToolCallStreamingPartial` — capability emitted a partial during streaming (per [`run.streaming-partial-execution`] File 04 §12); payload: partial-block handle, byte counts, sensitivity.
- `ToolCallCompleted` — capability returned its declared output; payload: produced block ids, postcondition outcomes, declared replay-class metadata.
- `ToolCallFailed` — capability returned a typed error; payload: the typed `AppError`, recovery action taken/proposed.
- `ObservationCommitted` — observation block committed (per [`artifact.observation`]); payload: observation kind, staleness fingerprint, block id.
- `ValidationCommitted` — validation block committed (per [`artifact.validation-critique`]); payload: validation outcome.
- `CritiquePosted` — critique block committed (per [`artifact.validation-critique`]).

**Model calls (per [`run.execution-ledger`]):**
- `ModelCallStarted` — provider call initiated; payload: provider id, model id, tokenizer id, role, request fingerprint, cache markers used.
- `ModelCallCompleted` — provider returned; payload: full `TokenUsageRecord` (§6.2), cost computed from per-model pricing, stop reason, parsed `ParsedResponse` ref.
- `ModelCallStreamingDelta` — provider streamed a chunk; payload: delta size, accumulated counts, partial-block handle (aggregated per §13.4).
- `ModelCallFailed` — provider returned an error; payload: typed provider error (File 06 errors module), retry classification (`retryable`/`rate_limited`/`fatal`), `retry_after_ms` if provider-supplied.
- `ProviderHealthChanged` — provider transitioned `Healthy / Degraded / Unhealthy`; payload: prior state, new state, contributing failure count.
- `RateLimitSnapshotReconciled` — provider headers reconciled local rate-limit state; payload: the typed `RateLimitSnapshot`.
- `TokenCountEstimationTelemetry` — post-call accuracy comparison; payload: estimated count, actual count, delta percentage, tokenizer id.

**Block and version-graph events:**
- `BlockCommitted` — block committed at a canonical boundary (per [`block.commit-boundary-set`]); payload: block id, kind, content variant, content hash, sensitivity, scope, producer.
- `BlockLifecycleChanged` — explicit `Mask`/`Drop`/`Recover` (per [`block.mask-drop-recover`] File 08 §6.3); payload: block id, from-state, to-state, version it applies to.
- `BlockPinChanged` — explicit `Pin`/`Unpin`/`Protect`/`Unprotect` (per [`block.pin-protect`] File 08 §6.4).
- `BlockGrouped` / `BlockUngrouped` — `Group`-kind block created/dissolved (per [`block.group-ungroup`] File 08 §6.5).
- `BlockHardDeleted` — physical destruction (per [`block.hard-delete`]); payload: deleting actor, deletion reason, tombstone reference, materialization-fallback outcome.
- `VersionCommitted` — version-graph commit; payload: version id, parent version id, `op_summary`, compact `VersionDiff`.
- `VersionSwitched` — active version pointer changed; payload: from-version, to-version, view rebuild outcome.
- `PendingOpApplied` — context operation applied to the materialized view (per [`block.block-lifecycle-non-destructive-edits`]); payload: operation kind, affected block id, pending buffer state.

**Artifact and entity events (per [`artifact.events`]):**
- `ArtifactCreated` — first version of an artifact committed; payload: artifact id, kind, materialization policy, producing context.
- `ArtifactVersionCommitted` — subsequent version committed; payload: version id, derivation summary, materialized paths.
- `ArtifactLifecycleChanged` — derived lifecycle transition (Draft → Active → Validated etc.); payload: from-state, to-state.
- `ArtifactReviewStateChanged` — explicit review-state update; payload: choice, actor.
- `ArtifactValidationStateChanged` — validation outcome derived from validated_by edges.
- `ArtifactMaterialized` — artifact written to workspace path; payload: materialized paths + content hashes.
- `ArtifactExternallyEdited` — filesystem watcher committed a sibling version for an externally-modified materialized file.
- `ArtifactArchived` / `ArtifactDiscarded` / `ArtifactRestored` — explicit lifecycle operations.
- `ArtifactHardDeleted` — tombstone created (per [`artifact.artifact-tombstones`]); payload: tombstone ref.
- `ClaimPublished` — claim block committed via `claim.publish` (per [`artifact.claim-extraction`] File 09 §10).
- `ClaimStatusOverridden` / `ClaimWithdrawn` — explicit claim-state changes.
- `EvidenceLinked` — typed evidence-link edge created (per [`artifact.evidence`]).
- `EvidenceLinkRemoved` — explicit evidence-link removal.
- `CitationCaptured` — citation block committed.
- `ProvenanceQueryExecuted` — canonical provenance query ran (per [`artifact.provenance`] File 09 §15); payload: query kind, target, result summary.

**Surface and capability registry events (per [`surface.surface-relevant-events`] File 07 §13 + [`capability.events`] File 05 §12.2):**
- `ToolSurfaceComposed` — resolved tool surface consumed by an invoker; payload: surface id, invoker kind, scope context, zoned-entries summary, auto-shrink record, composition diagnostics.
- `ToolSurfaceShrunk` — auto-shrink demoted capabilities (per [`surface.auto-shrink-algorithm`] File 07 §8.2).
- `ToolSurfaceOverflow` — composition failed to fit pinned tools (per [`surface.auto-shrink-algorithm`]).
- `CapabilityBorrowed` — `tool.borrow` granted a `BorrowGrant` (per [`surface.borrow-grant`] File 07 §7.3).
- `CapabilityBorrowReturned` — `BorrowGrant` expired/revoked.
- `CapabilityZoneChanged` — zone reassignment between compositions (per [`surface.surface-relevant-events`]).
- `CapabilityRegistered` — registration succeeded (per [`capability.capability-registry`] File 05 §12.3).
- `CapabilityUnregistered` — registration removed.
- `CapabilityUpdated` — version increment registered (per [`capability.lifecycle`] File 05 §16.4).
- `CapabilityEnabledChanged` — enable flag toggled at any scope.
- `CapabilityAvailabilityChanged` — `availability_status` transition (per [`capability.registered-capability`] File 05 §10).
- `CapabilityRegistryStateChanged` — binding rebound, trust override applied, collision resolved.
- `SubsystemSurfaceSpecUpdated` — subsystem updated its declared default surface (per [`surface.subsystem-surface-spec`] File 07 §5).
- `PrimarySurfaceChanged` — active `SubsystemSurfaceSpec` changed mid-run (per [`surface.primary-surface-changes`] File 07 §5.4).
- `LensFilterChanged` — per-lens visibility setting changed.
- `SourceConnected` / `SourceDisconnected` — plugin or MCP server source lifecycle.
- `SourceRegistrationApproved` / `SourceRegistrationDenied` / `SourceRegistrationDeferred` — source-approval flow outcome (per [`policy.source-approval-flow`]).
- `ShortcutConflict` — keyboard-shortcut collision detected.

**Child run, parallel work, and merge:**
- `ChildRunSpawned` — child run created (per [`run.child-runs-multi-agent-work`] File 04 §16); payload: parent run id, child run id, declared output contract, isolation primitive.
- `ChildRunStatusChanged` — mirrors `RunStatusChanged` for child runs.
- `ChildRunMerged` — parent incorporated child output (per [`run.merge`] File 04 §16.4); payload: merge mode (summary/artifact/patch/evidence-set/validation-report/proposed-task-update/proposed-workflow-step).
- `SiblingAborted` — sibling cancelled due to `sibling_abort_on_failure` (per [`run.failure-in-parallel-work`]).
- `DependencyFailureSkipped` — downstream unit skipped due to upstream `depends_on` failure.
- `BatchCoalesced` — duplicate concurrent identical calls coalesced (per [`run.mutation-rule`] File 04 §15.4).

**Streaming and live partials:**
- `StreamStarted` — typed stream opened (model text, reasoning, tool input, tool output, partial block, file partial write); payload: stream kind, partial-block handle.
- `StreamProgressBatch` — aggregated batch summary (per §13.4); payload: batched delta counts, byte counts, aggregation policy.
- `StreamCompleted` — stream reached its declared commit boundary; payload: committed block id, total bytes, total chunks.
- `StreamCancelled` — stream cancelled mid-flight; payload: orphan-block outcome per [`run.cancellation`].
- `FilePartialWriteStaged` — live-partial-write capability wrote into a temp file (per [`run.streaming-partial-execution`]).
- `FilePartialWriteAborted` — staged temp file deleted on cancellation.
- `FilePartialWriteCommitted` — atomic rename moved the staged temp file to the destination.

**Hook events (this file's primary concern):**
- `HookSubscriptionRegistered` — hook subscription added; payload: subscription id, event kinds, mode, priority, timeout, fail-direction, authority class, source.
- `HookSubscriptionUnregistered` — subscription removed.
- `HookSubscriptionEnabledChanged` — subscription toggled at any scope.
- `HookFired` — hook handler invoked at a matching event; payload: hook id, event id, run-context references.
- `HookDecisionRecorded` — blocking hook returned a decision; payload: the typed `HookDecision`.
- `HookTimedOut` — handler did not return within `timeout_ms`; payload: synthesized default decision + configured fail-direction.
- `HookHandlerError` — handler raised an error; payload: typed error, fail-direction synthesis.
- `HookActionInvoked` — hook's action invoked a capability, ran a shell script, or emitted a synthesized event; payload: action kind + resulting events/capability invocation ref.

**Error and recovery:**
- `TypedErrorRaised` — a typed `AppError` raised in the run; payload: typed variant, originating span context, affected operation.
- `RecoveryStrategyApplied` — recovery strategy fired (per [`run.recovery`] File 04 §20.2); payload: strategy (`retry_same_unit`/`expose_to_model`/`switch_model_profile`/`switch_capability_implementation`/`narrow_capability_scope`/`revoke_and_narrow_lease`/`request_user_clarification`/`branch_strategy`/`restore_or_rollback`/`stop_with_typed_failure`).
- `ContextPressureObserved` — execution observed context pressure (per [`run.boundary-rule`] File 04 §20.1); payload: used percentage, kind of pressure.
- `StuckDetected` — runtime detected obvious stuck state (per [`run.stuck-detection`] File 04 §20.3); payload: pattern (`repeated_identical_tool_calls`/`repeated_failed_validations`/`repeated_provider_errors`/`no_new_durable_output`/`cyclic_child_waiting`/`ping_pong`/`single_iteration_empty_response`).
- `StuckEscalated` — escalation step taken (soft warning, structured directive, hard stop); payload: active escalation level.
- `BudgetWarning` — execution approached a configured budget (per [`run.budgets-limits`] File 04 §21); payload: budget kind, threshold percentage.
- `BudgetExhausted` — budget hit; payload: budget kind, partial-output retention.
- `LoopDetected` — agent/capability loop detected (action signature repetition, page-stagnation, ping-pong); payload: detector, offending pattern.
- `RetryAttempted` — explicit retry attempt; payload: prior entry id, retry mode (per [`run.retry`] File 04 §19.1).
- `BranchCreated` — branch created (per [`run.branch`] File 04 §19.3); payload: parent execution boundary.
- `RerouteResolved` — reroute resolved (per [`run.reroute`] File 04 §19.2).

**Cancellation and intervention:**
- `CancellationRequested` — user/policy requested cancellation; payload: cancel target (run/run+children/specific child/specific tool call/specific sandbox), requester, cooperative-stop deadline.
- `CancellationProgressing` — cooperative stop in progress; payload: listeners that acknowledged, deadline countdown.
- `CancellationEscalated` — escalation to forceful termination after deadline expired.
- `CancellationCompleted` — final outcome; payload: affected run/child-run/tool-call ids, cleanup performed, cooperative-vs-escalated-vs-forceful classification, partial outputs retained/discarded, final status.
- `OrphanOutputDetected` — listener reported completion after run already cancelled; payload: orphan reference.
- `InterventionRecorded` — explicit user intervention (per [`run.user-intervention`]); payload: intervention kind (`continuation_with_new_instruction`/`pause`/`cancel`/`branch`/`reroute`/`approval_grant`/`approval_denial`/`scope_narrowing`/`explicit_takeover`), actor.
- `TakeoverStarted` — `control` flipped to `User` (per [`run.minimum-durable-reconstruction`]).
- `TakeoverEnded` — `control` returned to `Assistant`; payload: optional user-supplied summary + observable workspace delta references.

**Workspace, file, and external state:**
- `WorkspaceOpened` / `WorkspaceClosed` — workspace lifecycle (future Workspaces and Materialization spec).
- `FileIngested` — new file block created from an upload/import.
- `FileExternallyModified` — filesystem watcher detected an external edit (per [`block.streaming-commit-boundary`] File 08 §7).
- `FileMaterialized` — block content written to workspace (per [`artifact.artifact-materialization`] File 09 §7.3).
- `EnvironmentSnapshotCaptured` — environment captured for replay (env vars, working directory, virtual desktop, focus state, DPI).
- Domain-specific workspace/source-control/browser/perception/system-watch/memory/retrieval/knowledge-base/SRS facts are NOT predeclared; owning specs declare them as `Custom { namespace, name, payload }` via §4.3. File 10 reserves the mechanism + namespace discipline; does not predeclare those kinds.

**Validation and quality control:**
- `CompletionVerificationFired` — completion-verification hook surface ran (per [`run.termination`]); payload: deterministic-vs-model-mediated mode, verdict.
- `QualityControlValidatorRan` — quality-control validator fired; payload: validator id, verdict, decisive validator chain.
- `QualityControlViolationDetected` — violation surfaced.

**Approval and contradiction:**
- `BatchApprovalRequested` / `BatchApprovalResolved` — batched approval flow (per [`policy.batched-approval-flow`] File 06 §5.5).
- `TypedConfirmationRequested` / `TypedConfirmationSatisfied` / `TypedConfirmationMismatched` — typed-confirmation flow (per [`policy.permission-floor-typed-confirmation`]).
- `DeniedFloorOverridden` — typed-confirmation override of a `Denied`-floor capability (per [`policy.denied-carve-out`] File 06 §7.4).
- `SourceApprovalFlowOpened` / `SourceApprovalFlowResolved` — source-approval flow (per [`policy.source-approval-flow`]).

**Automation, scheduling, and triggers:**
- `AutomationTriggerFired` — automation trigger emitted a run (future Automation and Triggers spec).
- `WebhookReceived` — external webhook delivered.
- `OsEventReceived` — external OS event delivered.

**Sync and persistence:**
- `SyncPulled` / `SyncPushed` / `SyncVersionDiverged` / `SyncBlobFetched` / `SyncFailed` — cross-device sync lifecycle (per cross-cutting infrastructure/sync.md).
- `LedgerCompactionRan` — ledger compaction collapsed older entries (per §10 retention).

**System / app lifecycle:**
- `AppStarted` — application initialized; payload: versions, settings snapshot id, registry snapshot id.
- `AppShuttingDown` — graceful shutdown initiated with grace period (per cross-cutting infrastructure/lifecycle.md).
- `AppStopped` — application terminated.
- `BackgroundWorkerSpawned` / `BackgroundWorkerStopped` — background worker (memory consolidator, scheduler, audit writer, lineage tracker, watch poller).
- `BackgroundWorkerHeartbeat` — periodic worker health signal.
- `LedgerCommitRejected` — a commit-time forgery guard or validation rule rejected an entry; payload: proposed entry's fields (sensitivity redaction) + rejection reason.

**Custom extension:**
- `Custom { namespace, name, payload }` — subsystem-/surface-/plugin-/MCP-/API-/user-defined kind registered through proposal-first registration ([`capability.runtime-mutation`]). Registration declares namespace, schema id/version, payload shape, allowed cross-reference keys, default sensitivity, retention class, owner, canonical event vocabulary the kind participates in.

### 4.2 Kind Composition Rules
- Every capability-invocation kind (`ToolCallProposed`, `ToolCallExecuted`, `ToolCallCompleted`, `ToolCallFailed`, `ToolCallDenied`) shares a single `invocation_id` so the full pipeline is correlatable.
- Every model-call kind (`ModelCallStarted`, `ModelCallCompleted`, `ModelCallStreamingDelta`, `ModelCallFailed`) shares a single `request_id`.
- Every block-commit kind (`BlockCommitted`) references the produced `block_id` + the `invocation_id` that produced it (when capability-produced).
- Every artifact-event kind references the `artifact_id` + `artifact_version_block_id` it operates on.
- Every hook-decision kind (`HookDecisionRecorded`, `HookTimedOut`, `HookHandlerError`) references the originating `event_id` + `subscription_id`.
- Every cancellation kind references the `run_id` (or `tool_call_id` if narrower) it targets + the `requester` (user/policy/budget exhaustion/watchdog).

### 4.3 Custom Kind Registration `ledger.custom-kind-registration`
- A `Custom { namespace, name }` kind is registered via canonical capability-registration ([`capability.runtime-mutation`]). Registration declares: `namespace` (owning subsystem/extension source); `name` within namespace; schema id + schema version; payload schema (typed structural shape); required + optional cross-reference keys; default sensitivity; retention class; owner/source subsystem; allowed canonical events this kind participates in (which events trigger committing this kind); human-readable description.
- Registered custom kinds enter the same registry as canonical kinds, follow the same source-trust narrowing rules (per [`policy.source-approval-flow`]). A custom kind cannot violate canonical composition rules; the registration is rejected if it would.
- Unknown custom kinds are storable/renderable only as opaque safe records; not executable as hook decisions/policy facts/capability inputs until schema is registered + trusted.

### 4.4 Boundary
- The canonical kind catalogue defines what consequential facts the system reasons about across cross-cutting subsystems. Domain-specific facts use `Custom`. Storage/projection layers consume the catalogue; they do not extend it (only registered `Custom` extension does). Adding a new canonical kind is a canonical-spec change, not a runtime registration.

## 5. `EventStream` `ledger.event-stream`
### 5.1 Definition
- Typed live coordination channel carrying `AppEvent` wrapped in the canonical `EventEnvelope`; single coordination substrate for streaming UI, hook subscribers, inspectors, progress views, approval routers, validators, structured loggers, telemetry, replay machinery, cross-tab coordination, frontend reactivity, automation triggers, external integrations.
- The bus is NOT: the durable execution history (that's `ExecutionLedger`); a parallel message queue per subsystem (one bus; subscribers subscribe with filters); a place where consequential events disappear (every consequential event also recorded as a ledger entry); a substitute for typed errors (error propagation through services uses `Result<T, AppError>`; the bus carries `TypedErrorRaised` events as observations of errors, not as the error-propagation channel).
- The bus IS: typed (every event a closed `AppEvent` variant or `Custom { namespace, name, payload }`); ordered within declared `sequence_scope` tuples (subscribers within a context tuple see monotonic sequence order); fan-out (multiple subscribers in parallel); backpressure-aware (each subscriber has a bounded buffer; overflow emits `EventBufferOverflow` + marks `degraded`); sensitivity-aware (`Secret` payloads stripped or replaced with safe descriptions before any persistence path — logging/telemetry/sync/export).

### 5.2 `EventEnvelope` `ledger.event-envelope`
- `event_id` — globally stable for the event; assigned at emission; never reused.
- `conversation_id` — active conversation when conversation-scoped; absent for explicitly system-wide events.
- `context_refs` — typed contextual references when applicable: `run_id`, `step_id`, `node_id`, `workspace_id`, `worktree_id`, `backend_id`, `capability_id`, `ledger_entry_id`, registered extension refs. Inapplicable refs absent rather than null-padded.
- `parent_event_id` — the causally-prior event (whose handler emitted this); `None` for root events; enables causality chain reconstruction.
- `causal_event_ids` — optional set of additional events this depends on when one parent is insufficient.
- `trace_context` — optional propagation envelope for cross-run observability (per [`routing.run-intent`]); typically a stable trace id + span id, semantics defined by future Telemetry spec.
- `sequence_scope` — the tuple within which `sequence` is monotonic, usually conversation/run/worktree/backend context producing the event.
- `sequence` — monotonic identifier within `sequence_scope`; used for de-duplication + ordering within a context.
- `timestamp` — full-granularity. May support display/search/explicit uncertainty-bearing fallback inference, but never replaces sequence or causal links as correctness basis.
- `sensitivity` — closed: `Public`, `Sensitive`, or `Secret`.
- The envelope itself is mandatory; contextual references inside are optional/explicitly N/A. Subscribers filter by any combination of envelope fields + event kind. `sequence` monotonic within `sequence_scope`; subscribers deduplicate using `event_id` first and `sequence` within scope second. Predictable event chains should include the expected causal relation or next expected sequence; consumers use it to detect gaps without relying on time.

### 5.3 Closed `AppEvent` Catalogue `ledger.app-event-catalogue`
- Every event is an `AppEvent` variant. The closed catalogue = same set as the `LedgerEntryKind` catalogue (§4), plus transient-coordination kinds that do not commit to the ledger:
**Transient-coordination kinds (live bus only, not durable):**
- `MessageChunk` — model text delta during streaming.
- `ReasoningChunk` — model reasoning delta during streaming (per [`capability.permission-policy-fields`] File 05 §3.5 sensitivity defaults; `Sensitive` by default).
- `BlockStreamStarted` — a block began streaming (durable counterpart `StreamStarted`; transient form notifies the UI immediately).
- `BlockStreamCompleted` — a block finished streaming (durable counterpart `StreamCompleted`).
- `ContextAssembled` — context assembly produced a model request (per cross-cutting/context-assembly.md); payload: budget breakdown.
- `ContextBudgetWarning` — context approached a budget (per cross-cutting/context-assembly.md).
- `CompactionStarted` / `CompactionCompleted` — compaction pipeline events (per File 13).
- `UiPanelRegistered` / `UiPanelUnregistered` / `UiPrimaryPanelChanged` / `UiSelectionChanged` / `UiModeChanged` / `UiAvailableCapabilitiesRecomputed` — UI state-awareness events (per cross-cutting/state-awareness.md).
- `UiThemeChanged` / `UiKeybindingChanged` / `UiLayoutChanged` — UI customization events.
- `DebugLog` — structured log entry (sensitive by default; secret content always redacted).
- `EventBufferOverflow` — a subscriber's bounded buffer overflowed; subscriber transitions to `degraded`.
- `Ping` / `Pong` — heartbeat events for cross-tab or remote subscribers.
- `SocketIoMessage` — gateway-bridge wire message (for systems exposing the bus over network transports).
- `Heartbeat` — periodic liveness signal from a background worker.
- All `LedgerEntryKind` variants from §4 are also `AppEvent` variants; consequential events fan out to both bus (live coordination) and ledger (durable record).
- Extensible via `Custom { namespace, name, payload }` events registered through the canonical mechanism ([`capability.runtime-mutation`]). Custom events declare whether transient-only or also produce ledger entries.

### 5.4 Delivery Semantics
- Within a `sequence_scope`: events delivered in monotonic `sequence` order; subscribers see the same ordering, deterministic across replay of that scope.
- Across context tuples: no ordering guaranteed; subscribers cannot assume an event in conversation A precedes one in conversation B in same wall-clock order.
- Fan-out to multiple subscribers in parallel; the bus does not block one on another.
- Blocking hook dispatch happens at interceptable boundaries before the consequential action proceeds. Passive bus delivery is non-blocking fan-out and does not become the authority for mutating/approving the action.
- Backpressure bounded per subscriber: each subscription declares a buffer profile; overflow emits `EventBufferOverflow` + marks `degraded`; degraded subscriptions stop receiving events until the subscriber acknowledges recovery through explicit reconnection.
- Cross-process delivery uses the transport substrate (Tauri channels backend-to-frontend, SSE for browser clients, Unix sockets for shell-script hooks, MCP transport for external clients). Transport preserves the wire-format contract; specifics owned by future Runtime Infrastructure.
- Persistence boundary: consequential events commit to the ledger before bus delivery, or atomically alongside delivery (storage layer specifies durability semantics). Ordering guarantee: if an event is durably persisted, all subscribers see its ledger commit before any subscriber observes a later sequence number in the same context tuple. Transient events may be delivered without ledger commit.
- The owning subsystem commits consequential facts through the ledger API + emits an event referencing the committed `ledger_entry_id` or causal entry. Observing an event never creates the durable fact; a consequential event without its required durable record is an incomplete execution state.

### 5.5 Delivery Classes and Aggregation Policies
- Every event kind declares a delivery class:
  - `lossless_consequential` — must be durably represented before completion or linked to a durable fact; never silently dropped.
  - `coalescible` — may aggregate multiple updates into a typed summary when the summary preserves meaning needed by subscribers.
  - `latest_only` — only the latest state matters (focus/cursor state).
  - `sampled_diagnostic` — diagnostic/telemetry events where sampling is acceptable under settings.
- High-frequency events aggregate before bus emission to prevent saturation. Aggregation policies typed/declarative/settings-driven; subscribers see the aggregated form, not raw underlying mutations (token delta aggregation into `StreamProgressBatch`, UI position coalescing into latest-state summaries, heartbeat summaries, structured-log batches). Canonical specs do not bake fixed millisecond windows, pixel thresholds, or event-count constants into correctness rules.
- Aggregation never silently drops consequential events. A `Block`-tier hook decision, a `ToolCallProposed`, a `ModelCallCompleted`, or any other consequential event flows through ledger + bus individually. Aggregation applies only where the declared delivery class permits; coalesced/dropped noncritical details must preserve a typed summary when user-facing inspection/debugging needs it.

### 5.6 Sensitivity Tagging at Emission
- Every event carries `sensitivity` at emission; producer responsible for initial tag; policy layer + downstream subscribers may NOT lower the classification (only raise). Canonical rules:
  - a capability emits events at its declared `data_sensitivity` (per [`capability.permission-policy-fields`]), per-event override allowed.
  - the executor stamps `sensitivity = Sensitive` on any payload including credentials/secrets/raw user-private data/anything flagged by `sensitivity_field_map`.
  - the executor stamps `sensitivity = Secret` on any payload including raw credentials in flight (executor strips/replaces the raw secret before any persistence path; only safe labels persist in durable form).
  - subscribers respect the tag: `Secret`-tagged events do not flow to storage paths (durable ledger, sync, export, telemetry), only to in-process subscribers that need them (executor itself, immediate consumer, sandbox handler) and only for the duration of handling.
- The bus enforces: `Secret`-tagged event payloads passed by reference to the in-process handler; reference zeroed after the handler returns; no copy persists to durable storage.
- Subscriptions are policy-governed. A subscriber declares event kinds, scope filters, maximum sensitivity, authority, purpose. The dispatcher provides a redacted projection appropriate to grants. `Secret` payloads never delivered to ordinary subscribers; `Sensitive` payloads require explicit permission and default to safe summaries.

### 5.7 Frontend Bridge
- The bus exposes a Tauri-or-equivalent bridge for frontend subscription via `listen<EventEnvelope>('app://event-bus', handler)` (or per-channel subscriptions for high-volume kinds). The bridge: preserves the envelope's identifiers; streams events in monotonic `sequence` order per context tuple; supports transport-level resume tokens such as `Last-Event-Id`; handles backpressure (marks subscription `degraded` + emits `EventBufferOverflow`); gates `Secret`-tagged events (frontend never receives a raw secret payload; redaction at the bridge boundary); supports per-event-kind subscription filters (reducing wire traffic).
- Bridge implementation owned by future Runtime Infrastructure; this file specifies the contract.

### 5.8 Boundary
- The bus is the live coordination substrate. It does NOT own: the underlying transport (Tauri/SSE/WebSocket/Unix socket/MCP — future Runtime Infrastructure); durable persistence of consequential events (future Storage); cross-device sync (future Sync); UI rendering of event-driven updates (future UI); typed-error propagation through services (cross-cutting/errors.md); policy-evaluation logic consuming events (File 06). It DOES own: the wire-format contract, envelope, closed `AppEvent` catalogue, delivery/ordering semantics, aggregation policies, sensitivity rules at emission, subscription contract.

## 6. Per-Call Model-Call Attribution `ledger.per-call-model-call-attribution`
### 6.1 Definition
- Canonical recording mechanism for every model invocation; load-bearing for cost accounting, replay accuracy, rate-limit reconciliation, evaluation, the unkeyed-scalar invariant ([`core.explicit-rejections`] File 01 §8).
- Every `ModelCallCompleted` MUST carry a complete `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)`.

### 6.2 `TokenUsageRecord` (required schema)
- `record_id` — stable identifier.
- `entry_id` — the parent `ModelCallCompleted` entry id.
- `conversation_id`, `run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id` — envelope/context identifiers.
- `provider_id` — provider identity.
- `model_id` — resolved model identity at call time.
- `tokenizer_id` — tokenizer/counting strategy used for any local estimation.
- `role` — model's role: `router`, `responder`, `critic`, `validator`, `summarizer`, `sub_agent`, `classifier`, `judge`, or registered custom role.
- `prompt_tokens` — input token count.
- `completion_tokens` — output token count.
- `cache_creation_tokens` — cache write tokens when provider exposes/derives.
- `cache_read_tokens` — cache hit tokens when provider exposes/derives.
- `reasoning_tokens` — extended-thinking tokens (when provider exposes; `None` otherwise).
- `request_id` — provider-supplied request id (cross-ref with provider dashboards/audit).
- `token_source` — typed `TokenSource` (§6.3) indicating accuracy provenance.
- `usage_source` — provider-reported, local-estimated, provider-counting-endpoint, multimodal-estimated, or mixed.
- `cost_calculated_at` — timestamp of cost calculation when cost is displayed/stored as projection.
- `pricing_snapshot_id` — ref to pricing snapshot used when cost shown/stored.
- `pricing_tier_id` — ref to the `PricingTier` record used for cost calculation, if tier-based.
- `latency_ms` — round-trip latency incl. any network time.
- `inference_time_ms` — server-reported inference time when available.
- `cached_input_tokens` — provider-side cached input (where exposed).
- `image_tokens`, `audio_tokens`, `video_tokens` — multimodal calls; computed from modality-specific accounting rules per [`run.execution-ledger`].
- The record is NOT durable as a single scalar (no unkeyed `total_tokens`; aggregation is a query). Aggregation views (`total_tokens_per_session`, `cost_per_run`, `tokens_per_model`) are queries from `TokenUsageRecord` rows. Storage may materialize aggregation views, but the source of truth is the per-call record.

### 6.3 `TokenSource` (closed canonical enum classifying accuracy)
- `ProviderNative { confidence }` — counts from the provider's response body or equivalent native usage record.
- `LocalTokenizer { tokenizer_id, confidence }` — counts from a registered local tokenizer/counting library selected by provider/model descriptor.
- `ProviderCountingApi { endpoint_ref, confidence }` — counts from a provider-exposed counting operation.
- `CharacterApproximation { formula_id, safety_margin, confidence }` — counts from a documented approximation formula; last-resort fallback.
- `MultimodalEstimate { dimension, units, formula_id }` — counts from media properties using a registered multimodal accounting formula.
- Fallback chain at call time: `ProviderNative` first when native usage available, `LocalTokenizer` when a matching tokenizer registered, `ProviderCountingApi` when provider exposes a counting operation, `CharacterApproximation` last. Chosen source recorded so post-hoc accuracy analysis computes per-counting-source delta percentages.

### 6.4 Cost Computation `ledger.cost-computation`
- Cost never stored as unkeyed scalar in any ledger row. Cost is a projection over usage; when stored/displayed, keyed by provider/model/tokenizer/usage source/pricing snapshot. Computed on demand from `TokenUsageRecord` × the `PricingTier` in effect at the record's `cost_calculated_at`:
  - `PricingTier { provider_id, model_id, input_usd_per_million, output_usd_per_million, cache_creation_usd_per_million, cache_read_usd_per_million, multimodal_pricing, pricing_version, effective_from, effective_until }`.
  - `cost_usd = (input_tokens / 1_000_000 × input_usd_per_million) + (output_tokens / 1_000_000 × output_usd_per_million) + (cache_creation_tokens / 1_000_000 × cache_creation_usd_per_million) + (cache_read_tokens / 1_000_000 × cache_read_usd_per_million) + multimodal_cost`.
- Pricing tiers are user-maintained (user adds/edits via settings). System never assumes a default pricing; queries needing cost emit a typed `PricingUnavailable` error when no tier matches.

### 6.5 Accuracy Telemetry
- After every call, post-response token counting compares provider-reported counts to any local pre-call estimate. Delta recorded as `TokenCountEstimationTelemetry`: `estimated_count` (pre-call local estimate using `LocalTokenizer`/`CharacterApproximation`); `actual_count` (provider-native); `delta_pct`; `tokenizer_id` + `model_id`; `request_id` cross-ref to `ModelCallCompleted`.
- Supports per-tokenizer accuracy analysis ("token estimates for model X averaging 12% below actual"). Settings consume telemetry to recommend tokenizer changes or safety margin adjustments.

### 6.6 STT / TTS Usage
- `SttUsageRecord { provider_id, model_id, audio_seconds, duration_ms, request_id }`; `TtsUsageRecord { provider_id, voice_id, chars_synthesised, audio_seconds_generated, request_id }`. Sibling ledger entries to `TokenUsageRecord`; cost calculation reads the same `PricingTier` mechanism with audio-specific pricing dimensions.

### 6.7 Boundary
- Per-call attribution owned by this file. Per-model pricing maintenance, accuracy projections, budget-enforcement actions owned by adjacent specs (File 17 + future Budget/Telemetry). This file specifies what must be recorded; those specify what to do with the records.

## 7. `Hook` `ledger.hook`
### 7.1 Definition
- A `Hook` = a typed subscriber on the canonical event bus; the canonical extensibility primitive. Every component that reacts to events, intercepts proposed actions, or extends the runtime registers as a `Hook`.
- Registration unified; dispatch not. Blocking hooks run through interceptable boundary dispatch before the action proceeds; non-blocking hooks observe emitted events after the authoritative subsystem has emitted/recorded the fact.
- Every hook declares: `event_kinds` (closed canonical + registered `Custom`); `mode` (`Blocking` — executor/emitter awaits decision before continuing; or `NonBlocking` — observes without holding the emitter); `priority` (`i16`, lower runs first; convention `-100` audit/logging, `0` transformers/validators, `+100` approval router); `timeout_ms` or equivalent deadline profile for external/hanging handler safety (configurable, not a correctness condition); `hook_category` (`approval`/`validator`/`completion_verification`/`postcondition_check`/`safety_gate`/`transformer`/`formatter`/`enricher`/`localizer`/`observer`/registered extension); `authority_class` (`observe_only`/`narrowing_only`/`allow_capable`/`substitute_capable`; per [`policy.internal-composition-policy-inspectors`] File 06 §3.3); `handler` reference (in-process closure, registered capability id, shell-script command, MCP tool reference); `source` (`Builtin`/`Subsystem { id }`/`Plugin { id, version }`/`McpServer { server_id }`/`Api { api_id }`/`UserDefined { scope }`); `enabled` flag (settings-controlled per scope); `subscription_id` (stable identifier for revocation); per-error-class retry behavior overrides; typed `payload_filter` (optional declarative filter narrowing which events of subscribed kinds reach the hook — by capability id/run id/sensitivity/source/argument shape).

### 7.2 Hook Decision Vocabulary `ledger.hook-decision-vocabulary`
- A blocking hook returns one of four `HookDecision` (per [`run.hook-integration`]):
  - `Continue { reason }` — proceed with original payload.
  - `Substitute { new_payload, reason, substitution_kind }` — proceed with a hook-modified payload; `substitution_kind` is `narrowing_only`, `redaction`, `transparent_redirect`, or registered extension. Semantic target/action changes (changing what the agent does, not how the proposal is shaped) require `Block` + a follow-up ask-user flow, not silent `Substitute`.
  - `Block { reason, error_kind }` — abort; executor records a denial, the typed reason flows in-band as a tool result (per [`run.denial-is-in-band`]).
  - `RedirectSuggestion { target_capability_id, suggested_args, reason }` — abort + signal the agent should retry using the suggested capability; agent loop consumes as a typed retry signal.
- The four-outcome vocabulary is closed; a decision outside this set is an Explicit Rejection (§18).

### 7.3 Priority and Ordering `ledger.priority-ordering`
- Canonical priority convention (per [`run.hook-integration`]): `-100` audit/logging hooks (capture pre-validation state, observe-only); `0` transformers/validators/narrowing hooks (default for most extensions); `+100` the approval router + equivalent final-decision hooks (post-validation, the policy layer's authoritative decision).
- Within the same priority, hooks run in stable registration order, ties logged as warnings on first occurrence. Executor evaluates blocking hooks in priority order, composing proposal transformations before terminal decisions: `Continue` leaves the proposal unchanged; `Substitute` stages a transformed proposal and normally allows later hooks to inspect it; `Block` is terminal and skips remaining hooks unless a higher-authority canonical override path explicitly applies; `RedirectSuggestion` is terminal for the current proposal and returns a typed retry suggestion.
- All substitutions record safe before/after hashes or summaries. The approval router evaluates the final substituted proposal, not the original when earlier hooks transformed it.
- User-authored + third-party hooks register with explicit priority within `[-99, +99]` (cannot place above the approval router or below the canonical audit tier without explicit user-defined-policy approval). They can register at the same priority as built-in transformers/validators; tie-break = registration order.

### 7.4 Authority Classes `ledger.authority-classes`
- Each hook declares `authority_class` (per [`policy.internal-composition-policy-inspectors`]):
  - `observe_only` — may emit notes/explanations via `DebugLog`; may NOT produce `Block`/`Substitute`/`RedirectSuggestion`; the executor treats any non-`Continue` decision from one as `Continue` + a recorded warning.
  - `narrowing_only` — may produce `Block`, `Substitute { substitution_kind: narrowing_only | redaction }`, or `RedirectSuggestion`; may NOT produce `Continue` bypassing a prior hook's stricter decision.
  - `allow_capable` — may produce `Continue` even when prior hooks expressed concern (approval router + equivalent terminal-authority); registered only by `Builtin`/`Subsystem`/`Verified`/explicitly user-approved sources.
  - `substitute_capable` — may produce `Substitute { substitution_kind: transparent_redirect }` (changing target capability while preserving semantics); same trust restriction as `allow_capable`.
- `Community`, `Unverified`, `Plugin`, `McpServer`, `Api`, `UserDefined` sources default to `narrowing_only` until the user explicitly upgrades via source-approval (per [`policy.source-approval-flow`]). No hook can bypass `permission_floor`, typed-confirmation requirements, contradiction detection, or touched-resource constraints.

### 7.5 Timeout and Fail-Direction
- Each blocking hook subscription declares a timeout/deadline profile used only as a safety guard against hung handlers. If no decision within the guard, executor synthesizes a default per category/authority class/boundary risk:
  - security-category hooks (`approval`, `validator`, `completion_verification`, `postcondition_check`, `safety_gate`) default-on-timeout to `Block { reason: "hook timeout" }` and default-on-error to `Block { reason: "hook error" }`.
  - non-security hooks (`formatter`, `enricher`, `localizer`, `observer`) default to `Continue` with the original payload + a warning.
  - non-security hooks that can allow/substitute a consequential pre-action proposal default to fail-closed (their absence could permit unsafe execution).
- Same category-and-authority rule applies on handler error. User settings may override fail-direction per hook within policy limits. Security-category hooks cannot be set fail-open without typed confirmation.
- Per-error-class retry behavior configurable (per [`run.hook-integration`] + [`policy.approval-router`] File 06 §3.5): a hook failing for a known transient cause (provider rate limit, sandbox temporary unavailability, recoverable transport failure) may retry within its safety guard rather than fail immediately. Retry classification is part of the hook's declaration.
- `HookTimedOut` + `HookHandlerError` entries record the timeout/error, synthesized default decision, hook's authority class.

### 7.6 Hook Lifecycle Events
- `HookSubscriptionRegistered` (registers at startup/plugin install/MCP connect/user action/source-approval completion); `HookSubscriptionUnregistered` (unregisters at shutdown/plugin uninstall/MCP disconnect/user action/revocation); `HookSubscriptionEnabledChanged` (`enabled` toggles at any scope, per-scope settings overlay); `HookFired` (matching event reaches the hook); `HookDecisionRecorded` (blocking hooks return a typed decision); `HookTimedOut` (exceeds `timeout_ms`); `HookHandlerError` (handler raises); `HookActionInvoked` (action invokes a capability/runs a shell script/emits a synthesized event — §12 [§9 effect vocabulary]).

### 7.7 Hook Categories (share defaults; conventional groupings; every hook declares its own typed parameters)
- **Approval hooks**: the approval router (per [`policy.approval-router`]), typed-confirmation flow, batched-approval flow. Priority `+100`, blocking, fail-closed, `allow_capable`.
- **Quality-control validators** (future Quality Control spec): structural/semantic/real-time validators. Priority `0`, blocking, fail-closed by default as security-category unless owning policy classifies advisory, `narrowing_only`.
- **Audit and logging hooks**: structured-logging recorders, telemetry collectors. Priority `-100`, blocking (capture pre-validation state) or non-blocking (don't slow execution), fail-open, `observe_only`.
- **Transformers** (per [`run.hook-integration`]): argument normalizers, sensitivity-tag adjusters, locale-converters. Priority `0`, blocking, category/authority-dependent fail-direction, `narrowing_only` or `substitute_capable` for the substitution kind they emit.
- **Observers** (per [`run.hook-integration`]): UI state-awareness watchers, surface inspectors, completion summarizers. Non-blocking, `observe_only`, fail-open.
- **Completion-verification hooks** (per [`run.termination`]): deterministic or model-mediated post-execution checks. Per-run cadence (every N steps, in parallel, sequentially before completion, or only on explicit `verify_now`). Blocking when sequential, non-blocking when parallel; `narrowing_only`.
- **Stuck detectors** (per [`run.stuck-detection`]): deterministic stuck-pattern matchers + opt-in model-mediated detectors. Non-blocking; emit `StuckDetected` events hooks consume to inject corrective prompts or escalate.
- **Recovery hooks**: subscribe to `TypedErrorRaised`; emit recovery strategy decisions (per [`run.recovery`]). `narrowing_only`.
- **Surface mutation observers** (per [`surface.surface-relevant-events`]): subscribe to surface events to react to capability registration/availability changes/source connections. Non-blocking, `observe_only`.
- **Entity event observers** (per [`artifact.events`]): subscribe to artifact/claim/evidence/observation events for memory promotion, knowledge-base curation, downstream analysis. Non-blocking, `observe_only`.
- **Streaming UI observers**: subscribe to `MessageChunk`, `StreamProgressBatch`, `BlockCommitted` to update the streaming UI. Non-blocking, `observe_only`.
- **Background workers**: memory consolidator, SRS scheduler, system audit writer, data lineage tracker, watch poller, scheduled task runner. Each spawns + subscribes to its triggering events. Non-blocking, `observe_only`.
- Each category has settings-driven defaults (priority, timeout, fail-direction, authority) that subscribers may override within their authority envelope.

### 7.8 Boundary
- Defines the hook primitive. The approval router's algorithm owned by File 06. Completion-verification deterministic/model-mediated mechanics owned by [`run.termination`] + future Quality Control. Specific QC validators owned by future Quality Control and Validation. This file specifies the subscription contract, decision vocabulary, priority/authority rules, lifecycle events.

## 8. Hook Registration and Discovery `ledger.hook-registration-discovery`
### 8.1 Built-in Hooks (registered at startup)
- approval router (`policy.approval_router`) on `ToolCallProposed` at `+100`; structured-logging audit hook (`logging.audit_recorder`) on every consequential event at `-100`, blocking; telemetry collector (`telemetry.metrics_collector`) on every event, non-blocking, observe-only; canonical stuck detectors (`runtime.stuck_pattern_matcher`) on `ToolCallExecuted`, non-blocking; canonical completion-verification deterministic floor (`runtime.completion_forgery_guard`) on `RunStatusChanged { to: Completed }`, blocking, narrowing; memory consolidator background worker (`memory.consolidator`) on `AgentTurnCompleted` + scheduled triggers, non-blocking; data lineage tracker (`data.lineage_tracker`) on `BlockCommitted` for certain kinds, non-blocking; watch poller (`scheduler.watch_poller`) on watchdog ticks, non-blocking.
- Full set declared in built-in capability declarations (File 05), registered during startup phase 1 (per [`capability.startup-registration`] File 05 §16.1).

### 8.2 Subsystem-Registered Hooks
- Subsystems (work surfaces, substrate services per [`capability.capability-source`] File 05 §9.1) register hooks at subsystem load. Examples: Coder registers a git-status watcher on `FileExternallyModified`; Web registers a session-watchdog hook on its registered browser-session lifecycle `Custom` events; Memory registers a memory-extraction hook on the cross-cutting turn-completion boundary + declares memory-specific events in the Memory spec; Data Processor registers a lineage hook on data-transformation events; System Agent registers an audit-log writer on every system-mutation event.
- Subsystems declare hook subscriptions in their `SubsystemSurfaceSpec` (per [`surface.subsystem-surface-spec`]) or a dedicated `subsystem_hooks` declaration.

### 8.3 Plugin / MCP / API / User-Defined Hooks
- External + user-defined sources register through the same capability-registration ([`capability.runtime-mutation`]) with proposal-first source-approval (per [`policy.source-approval-flow`]). Declaration includes the subscription's `event_kinds`, `mode`, `priority`, `timeout_ms`, `authority_class`, `handler` reference, `payload_filter`; the hook's `description`; the source's identity + trust state.
- Source-approval surfaces the proposed subscription before activation: declared event kinds, authority class, handler kind (shell script command/registered capability id/MCP tool name), timeout, fail-direction. User can accept defaults, customize (override priority, narrow authority, change fail-direction), deny outright, defer source-level policy, or cancel.
- Sources with `Community`/`Unverified` trust default to `narrowing_only` and cannot register at the `+100` priority or below `-99`. User can explicitly upgrade authority via source approval.

### 8.4 User-Authored Hook Declarations (three mechanisms)
- **Settings-backed**: registered through the canonical settings system (File 15) with a typed `HookDeclaration` schema; persisted in settings substrate; sync follows the setting's locality/sensitivity rules.
- **File-based**: an infrastructure-owned hook declaration file may declare hooks in TOML with the same schema; runtime watches the file via event-driven file watching and re-registers on edit.
- **Runtime registration capability**: agent/user invokes `tools.register_hook` (a registered capability with `UserApproval` tier) to add a hook at runtime; call carries the full declaration + goes through source-approval.
- User-authored hooks default to the user's identity as source (`UserDefined { scope: user_id }`); user can author at `conversation`/`workspace`/`global` scope.

### 8.5 Hook Discovery and Inspection (canonical read-only capabilities)
- `hooks.list` — enumerate registered subscriptions with declarations + current `enabled` state.
- `hooks.inspect { subscription_id }` — full declaration incl. handler reference, recent decision history, recent error rate.
- `hooks.decision_history { subscription_id, time_range }` — recent typed decisions (within sensitivity-aware filters).
- These are `ReadOnly` tier, respect standard agent-exposure rules (per [`policy.agent-exposure-policy-settings`]). The user-facing inspector lens (per [`surface.inspector-lens`] File 07 §12.4) renders the hook catalog.

### 8.6 Boundary
- Registration mechanism owned by File 05 (registry side) + this file (hook-subscription contract). Source-approval owned by [`policy.source-approval-flow`]. Settings persistence + profile-layer resolution owned by File 15. File-based hook discovery is an infrastructure/plugin concern whose enablement/visibility are settings-controlled.

## 9. Hook Effect Vocabulary `ledger.hook-action-vocabulary`
### 9.1 Definition
- A `HookAction` = what the hook does when it fires. Every hook declares one canonical action kind + action-specific payload:
  - `RunScript { command, args, env, stdin_template, timeout_ms, working_directory, sensitivity_classification }` — execute a shell command over a typed wire protocol. Runtime spawns the command, writes the typed JSON event payload to stdin, awaits a typed JSON decision on stdout. Stderr captures errors. Wire protocol closed canonical; JSON shape in §9.2.
  - `InvokeCapability { capability_id, args_template, sensitivity_classification }` — invoke a registered capability through standard [`run.call-pipeline`]; hook receives the capability's typed result as the hook's decision input.
  - `EmitEvent { event_kind, payload_template }` — synthesize a new event into the bus (carries the canonical envelope with `parent_event_id` set to the triggering event + typed payload). Useful for transforming one event into multiple downstream events or "this happened, but as a different kind."
  - `InternalHandler { handler_id }` — invoke an in-process registered handler function. Used by built-in/subsystem hooks; not available to plugin/MCP/user-defined sources without explicit source-approval upgrade.
- Action settled at registration; a hook does not switch action kinds at runtime. If multiple actions needed, register multiple subscriptions or use a single `InvokeCapability` whose target capability orchestrates internally through the capability pipeline.

### 9.2 `RunScript` Wire Protocol
- **stdin** (runtime → handler): a JSON object containing the canonical event envelope + typed event payload. Runtime adds metadata at top level (`event_kind`, `subscription_id`, `hook_call_id`, `expected_response_schema`). Sensitivity-tagged fields redacted at the wire boundary if the hook's authority class lacks access to the sensitivity level.
- **stdout** (handler → runtime): a JSON object containing the typed `HookDecision`. Schema:
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
  - `context_modification` — a hook-specific extension allowing the hook to add attributed text to the next model request (cline pattern); consumed by the agent loop when the hook is on a user-input-submitted or `PreToolUse`-equivalent event.
  - `system_message_injection` — injects a system-level note (e.g., "memory available" hint from claude-mem; "loop detected" warning from openclaw).
- **stderr**: captured as a `DebugLog` event with `Sensitive` sensitivity, attributed to the hook. Runtime does not require stderr to be empty.
- **exit codes**: 0 means stdout JSON is the decision. Exit code 2 (or other configured "client bug" codes) indicates a client-side bug → `HookHandlerError`. Non-2 non-zero exit codes treated as transport failures → `HookHandlerError`; synthesized default decision per fail-direction rules.
- Runtime enforces: the timeout (kills the handler process at `timeout_ms`); `Secret`-tagged payloads never written to stdin in raw form (runtime substitutes safe labels per per-field sensitivity_field_map per [`block.per-field-override`] File 08 §9.2); working directory (hook's declared, default active workspace root); environment (minimal allowlist per shell-operations.md; additional variables declared in `env` configuration).

### 9.3 `InvokeCapability` Semantics
- A wrapper around a registered capability; runs through standard [`run.call-pipeline`] incl. own policy evaluation, validators, isolation, result production. The hook's authority class limits which decisions the capability's typed result can map to: an `observe_only` hook cannot use `InvokeCapability` to invoke a capability that emits a `Block` decision; the wrapper enforces this by treating non-`Continue` outcomes as `Continue` + a warning.
- Canonical mechanism for "use the registered capability infrastructure to make a hook decision." Composes registry, policy layer, executor, ledger uniformly.

### 9.4 `EmitEvent` Semantics
- Emits a new event when fired. Synthesized event: carries the canonical envelope with `parent_event_id` set to the triggering event; carries `originating_hook_id` + causal chain metadata so recursion/self-triggering can be detected; has the kind + payload declared in the hook's action; inherits the triggering event's `sensitivity` unless the declaration overrides (subject to sensitivity-monotonicity: only raise, never lower); recorded as a ledger entry if the kind is one of the consequential kinds.
- Use cases: transforming a raw event into a higher-level specialized event (capability completion fires an `EmitEvent` hook synthesizing a subsystem-specific registered `Custom` event); annotating events with hook-computed metadata (a stuck detector fires `EmitEvent` to synthesize `StuckDetected` with the diagnosed pattern).
- Hook recursion allowed only inside explicit safety bounds. A hook does not receive its own derivative events by default. Subscriptions opting into recursive handling declare maximum depth, cycle policy, and whether repeated loops are allowed. Runtime detects causal cycles + records typed hook failures when bounds exceeded. Users may override limits via settings, but infinite unbounded loops are not a valid default.

### 9.5 `InternalHandler` Semantics
- Invokes an in-process function registered with a stable `handler_id`; takes the typed event payload, returns a typed `HookDecision`. Used by built-in/subsystem hooks; not exposed to external sources (plugins/MCP/user-defined) by default. A plugin/MCP source wanting to register an `InternalHandler` action requires explicit user approval of the handler binary, with `Verified` trust classification.

### 9.6 Boundary
- Hook-effect vocabulary is closed: `RunScript`, `InvokeCapability`, `EmitEvent`, `InternalHandler`. New kinds require a canonical-spec update. Hook-effect handlers themselves (shell command implementation, capability handler, in-process function) are not owned by this file; implementation details the canonical mechanism dispatches into.

## 10. Sensitivity-Aware Persistence and Retention `ledger.sensitivity-aware-persistence-retention`
### 10.1 Three Classes
- Every ledger entry + event payload carries `sensitivity` from the closed set:
  - `Public` — may appear in shareable exports, may be cached by external services handling public content (provider-side model-request caches when permitted); persisted in durable ledger with default retention.
  - `Sensitive` — contains user-private/workspace-specific data; excluded from shareable exports + clipboard-copy by default; persisted in durable ledger; subject to shorter default retention if settings configure; never sent to external telemetry without explicit opt-in.
  - `Secret` — contains credentials, raw API keys, OAuth tokens, password content, hidden user files/blocks, or equivalent never-leak material. Persisted to durable ledger with payload redaction at commit; only `safe_description` strings persist, never the raw secret. Original raw `Secret` held only in transient memory or the credential/vault substrate and zeroed after use.

### 10.2 Producer-Seeded Sensitivity `ledger.producer-seeded-sensitivity`
- The capability emitter (per [`capability.permission-policy-fields`] File 05 §3.5 `data_sensitivity`) seeds the tag at emission. Per-field overrides through `sensitivity_field_map` (per [`block.per-field-override`] File 08 §9.2) refine individual fields. Producer cannot lower a field's effective sensitivity below its inherited/declared baseline.
- Runtime stamps automatically when known patterns appear (credential vault reference, API key in arguments, password field, user-marked secret block, protected file scope), defaulting up rather than down. Explicit user override raising sensitivity always allowed; lowering requires a typed-confirmation policy override (per [`policy.permission-floor-typed-confirmation`]).

### 10.3 Persistence Effects
- `Public`: persisted at default retention; replayable, exportable, queryable through standard mechanisms.
- `Sensitive`: persisted at default retention or settings-configured shorter; excluded from default exports; queryable but not surfaced in default search projections; not sent to external telemetry without opt-in.
- `Secret`: persisted with redaction — structural fields (envelope, kind, cross-references, producer, timestamp) persist, payload retains only a `safe_description` (one-line summary not revealing secret content). Raw payload held only in transient memory or a credential/vault subsystem; references from in-flight handlers expire when handling completes. Future Secret-related queries return the safe description.
- Redaction happens at commit, not query time. Runtime ensures no path (ledger row, sync stream, export, telemetry, debug panel rendering, structured log output) ever sees raw `Secret` content. This is the ledger/event/sync/export/telemetry enforcement of the cross-cutting backend secret boundary ([`secret.backend-boundary`] File 17 §23.6): raw `Secret` material never crosses out of the backend's transient buffers + vault substrate; only opaque references + safe descriptions persist/propagate.

### 10.4 Retention Policies (configurable per sensitivity class via settings)
- `events.retention.public` — policy default, commonly indefinite unless user-controlled storage management says otherwise.
- `events.retention.sensitive` — policy default, configurable per source class/workspace/export-sync profile.
- `events.retention.secret` — N/A for raw content; safe descriptions follow `events.retention.sensitive`.
- Per-event-kind retention overrides configurable: a noisy kind (e.g., `ToolCallStreamingPartial`) may have shorter retention. Applies to durable storage only; bus delivery unaffected.
- Storage maintenance (`LedgerCompactionRan` events) runs as a background worker + respects retention. Compacted entries collapse into summary entries linked by `consolidates` cross-reference (mirroring [`block.kind-catalogue`] File 08 §3.1 `Consolidation` block-kind semantics).
- Retention/pruning decisions are themselves durable facts. No storage layer may silently prune `Sensitive` or safe-description `Secret` records without a policy-level transition recorded in the ledger.

### 10.5 Hash-Chained Audit-Log Tier
- A subset of ledger entries (security-sensitive operations) is also represented in a local hash-chained audit overlay for tamper-evident integrity:
  - entries: an infrastructure-owned local audit-chain file.
  - structure: `{ ledger_entry_id, timestamp, actor, action, target, canonical_redacted_entry_hash, prev_entry_hash, entry_hash, device_id, chain_id }`.
  - chain: `entry_hash = sha256(prev_entry_hash + canonical_redacted_entry_hash + timestamp + actor + action + target + device_id)`.
  - per-device only — the audit log NEVER syncs across devices; each device's hash chain has its own integrity.
  - never replaced by ordinary ledger — an integrity overlay; every audit entry references an ordinary ledger entry, but only the overlay carries the hash chain.
  - never disabled — even when telemetry/logging is disabled, security-sensitive operations write to the audit log.
- Operations that flow through the audit log: every approval verdict (`PolicyDecisionMade`); every lease grant/revoke (`LeaseGranted`, `LeaseRevoked`); every typed-confirmation completion (`TypedConfirmationSatisfied`); every floor violation (`PolicyFloorViolated`); every source approval/denial (`SourceRegistrationApproved`, `SourceRegistrationDenied`); every credential/secret operation (`SecretAccessed`, `SecretRotated`, `SecretRevoked`); every system-state mutation (`SystemChangeApplied`, `SystemChangeRolledBack`); every hard delete (`BlockHardDeleted`, `ArtifactHardDeleted`); every `DeniedFloorOverridden`.
- The overlay is verifiable: a verifier computes `entry_hash` for each overlay entry in order and checks it matches the recorded `entry_hash`. Any mismatch produces `AuditChainTamperDetected` event (high-severity, surfaced to the user, halts sync of the affected device).

### 10.6 Export and Share Filtering
- Default export/share include only `Public`-tagged entries. User can explicitly opt to include `Sensitive` per export by acknowledging via typed-confirmation. `Secret` payloads never included (only safe descriptions).
- Cross-device sync follows the same rules: default sync transports `Public`; `Sensitive` syncs only when user enables it per workspace/device; `Secret` content never syncs (only safe descriptions persist locally on each device, hash chain remains per-device).
- Settings `events.sensitivity_export_default`, `events.sensitivity_sync_default`, `events.sensitivity_clipboard_default` govern defaults.

### 10.7 Boundary
- Sensitivity is a durable property of every entry + event. Policy layer (File 06) decides what to do at policy boundaries based on sensitivity. The event stream uses the same value set for transient coordination. Surface rendering consumes sensitivity to gate displays. Future Security spec owns credential vault internals + trust cryptography; this file specifies the canonical sensitivity classification + persistence rules.

## 11. Replay Semantics `ledger.replay-semantics`
### 11.1 Definition
- Replay = reconstruction or controlled re-execution of a past execution state from ledger + durable snapshots. Supports debugging ("what did the model see at time T?"), audit ("which sequence of decisions produced this artifact?"), evaluation ("re-run this dataset against a new model and compare"), forensic analysis, learning. Does NOT promise byte-identical rerun of model calls/external systems unless responses were captured or the capability is declared deterministic under recorded inputs.

### 11.2 What Is Required for Replay
- full ledger entries for the run's scope (every `LedgerEntry` with `cross_references.run_id = <target>` plus parent/child related runs); the block pool (every `Block` referenced; blocks immutable per [`block.block`] File 08 §2.2); the version-graph snapshot (the `ContextVersion` ids referenced; version graph reconstructable from durable action log per [`block.block-persistence-contract`] File 08 §13); the entity pool (every `Artifact`/`Claim`/`Evidence`/`Observation`/`Validation`/`Critique` referenced); the registry snapshot at execution time (`CapabilityDeclaration` versions, `RegisteredCapability` states, source instance metadata per [`capability.registered-capability`]); the settings snapshot; the policy snapshot (lease set, template states, scope-level overrides per [`policy.lease-primitive`]); the world-model snapshot (active surfaces, focused elements, ui_mode, etc. per [`core.world-model`] File 01 §6.7); the observation staleness fingerprints (per [`artifact.observation`]).
- Ledger entries reference all of these via cross-references; replay walks the references to resolve.

### 11.3 Replay Classes (every capability declares `replay_class` per [`capability.replay-class`])
- `deterministic_replayable` — same inputs + same referenced state produce same result; safe to re-execute during replay without policy gates.
- `snapshot_replayable` — requires recorded snapshots (file content at path, page snapshot, accessibility tree fingerprint); the ledger's `staleness_fingerprint` cross-reference resolves; replay reads the snapshot rather than re-fetching live state.
- `effect_replayable_with_policy` — would cause external effects (email send, API call, database mutation); replay treats as "would have happened" and either skips them or routes through a replay-specific policy (the user explicitly approves re-execution).
- `not_replayable` — closures, transient session-bound resources, inherently uncontrolled side effects; replay reads the recorded result without re-executing.
- The replay engine reads `replay_class` from the recorded `invocation_id`'s capability declaration version (the declaration in effect at original call time, not the current one).

### 11.4 Replay Modes (three; user/evaluator selects per replay)
- `Inspect` — walks the ledger + resolves cross-references, producing a structured view. No re-execution. For debugging/audit/"what happened" reconstruction.
- `SimulateDeterministic` — re-executes `deterministic_replayable` + `snapshot_replayable`, skipping `effect_replayable_with_policy` + `not_replayable`. For evaluation testing whether execution produces the same result given same inputs.
- `FullRerun` — re-executes every capability, routing `effect_replayable_with_policy` through the replay-time policy (typically a sandbox or with explicit user approval). For testing/migration where actually running the full execution is the point.
- Each replay records a `ReplayRun` entry with mode, source run id, comparison outcome. Model output replay is byte-identical only when a provider response snapshot or equivalent captured output exists; otherwise `FullRerun` is a new execution attempt over recorded inputs.

### 11.5 Forensic Queries (closed canonical; themselves capabilities registered `ReadOnly`, run through the standard pipeline, recorded as `ProvenanceQueryExecuted` entries)
- `query_what_did_the_agent_see_at_time_t(run_id, timestamp)` — reconstructs the agent's model context at time `t`: assembled context blocks, active tool surface, available skills, active lease set, world-model snapshot.
- `query_which_capabilities_did_run_invoke(run_id)` — enumerates all `ToolCallExecuted` entries.
- `query_which_model_calls_consumed_what_tokens(run_id)` — aggregates `TokenUsageRecord` rows keyed by model.
- `query_which_blocks_did_run_produce(run_id)` — enumerates `BlockCommitted` entries.
- `query_which_artifacts_did_run_modify(run_id)` — enumerates `ArtifactVersionCommitted` entries.
- `query_which_hooks_fired(run_id)` — enumerates `HookFired` + `HookDecisionRecorded` entries.
- `query_run_lineage(run_id)` — walks `parent_run_id` + `supersedes` cross-references to produce the run's lineage chain (retries, reroutes, branches).
- `query_evidence_chain(claim_id)` — delegates to [`artifact.provenance`] (File 09 §15) provenance queries.

### 11.6 Boundary
- Replay is the consumer of the ledger + durable snapshots. The replay engine itself owned by future Evaluation and Benchmarking. This file specifies what is required for replay to succeed (cross-references, snapshot identifiers, replay-class consumption); the engine realizes the actual replay.

## 12. Streaming and Live Partials `ledger.streaming-live-partials`
### 12.1 Streaming Categories
- Model text deltas — `MessageChunk`. Reasoning deltas — `ReasoningChunk` (default `Sensitive`). Tool-input streaming (per [`run.streaming-partial-execution`]) — model still emitting a tool call's structured arguments; UI may render live ("Reading src/index.ts..."). Tool-output streaming — capability emitting partial results (streaming text, growing diff, growing file content). File-or-artifact live partial-write — capabilities writing incrementally into materialized state (per [`run.streaming-partial-execution`] + [`block.live-partial-write-capabilities`] File 08 §7.5). Reasoning summary streaming — when the provider exposes intermediate reasoning summaries. Progress events — specialized (file conversion progress, web fetch progress, indexing progress).

### 12.2 Commit Boundary Contract
- Streamed partials are not durable blocks until the producer's declared commit boundary fires (per [`block.streaming-commit-boundary`] File 08 §7). Pattern:
  1. Producer begins emitting partials; each flows through the bus as a transient `MessageChunk`/`ReasoningChunk`/`ToolCallStreamingPartial` event with a `partial_block_handle` referencing the eventual block id.
  2. Bus delivers partials live (streaming UI, hook listeners subscribing to streaming events).
  3. Producer reaches its declared commit boundary.
  4. Runtime commits a durable `Block` (per [`block.streaming-commit-boundary`]) + emits a durable `BlockCommitted` event + ledger entry.
  5. Streaming UI transitions from live partial rendering to durable block rendering on commit.
- Between partials and commit, partial events fan out to the bus but do not commit. After commit, the durable `StreamCompleted` entry references the committed block id.
- If the producer fails before commit (cancellation/error/timeout/crash), no committed block exists. Runtime emits `StreamCancelled` + decides per the capability's `partial_output_meaningful` declaration (per [`run.cancellation`]) whether to preserve the partial as an orphan block.

### 12.3 Aggregation for Streaming (per §5.5, settings-driven delivery policies)
- `MessageChunk` aggregates into `StreamProgressBatch` events under the active chunk batching policy.
- `ReasoningChunk` aggregates similarly with potentially different thresholds (per category settings).
- Tool-input streaming chunks aggregate at the same cadence.
- Tool-output streaming chunks aggregate per the capability's declared `streaming_chunk_policy` (default same as `MessageChunk`).
- Aggregation policies settings-configurable per kind. The aggregation summary carries the cumulative byte count, chunk count, most recent chunk content; subscribers see one batched event per interval, not one per chunk.

### 12.4 Live-Partial-Write Capabilities (file edits, artifact/document generation per [`run.streaming-partial-execution`])
- The capability validates the target before any write; writes into a temp/staged location during streaming; partials flow through the bus as `FilePartialWriteStaged` events; on commit, atomic rename moves the staged file to the destination; the `FilePartialWriteCommitted` entry records the final outcome; on cancellation, the staged file is deleted (`FilePartialWriteAborted`).
- Preserves end-to-end atomicity: destination never partially written; cancellation never leaks partial corruption.

### 12.5 Resumption
- Subscribers that disconnect/reconnect can request resume from their last-seen event using a transport token such as `Last-Event-Id` where supported. The reconnection request carries the last successfully-processed `event_id` + sequence scope; the bus replays events with higher `sequence` in that scope if they remain in its bounded buffer. Aggregation rebuilds from the durable counterpart when one exists.
- Bounded + best-effort. When the stream cannot replay the missing range, it emits/returns `StreamGapDetected`; clients reload durable projections or ledger-backed state, then resume the live tail. Transport resume tokens are conveniences, not durability guarantees.

### 12.6 Cross-Tab and Cross-Process Coordination (coordination channels the bus exposes)
- intra-process: the bus itself, with in-memory broadcast.
- intra-device cross-tab: BroadcastChannel pattern (bolt-diy + terax-ai pattern in batch-05) for browser-based UIs.
- inter-process: Tauri events (or equivalent transport) for backend-to-frontend.
- inter-device: cross-device sync (future Sync spec); the bus does not directly cross devices.
- Transport-layer specifics owned by future Runtime Infrastructure. This file specifies the contract: every transport preserves the canonical envelope, ordering, sensitivity filtering, per-context-tuple sequence semantics.

### 12.7 Boundary
- Streaming is the live half of the durable-history-vs-live-coordination split. The ledger records commit points; the bus carries live deltas. Aggregation policies + resumption semantics keep the bus responsive without losing coordination guarantees.

## 13. Subscription Persistence and Lifecycle `ledger.subscription-persistence-lifecycle`
### 13.1 Durable State
- Durable: registered subscriptions (settings-backed, file-backed, or durable plugin/MCP registration records) — survive restart; per-subscription `enabled` flags scoped per workspace/conversation/globally — survive restart via the settings system; source-approval state for each source — survive restart per [`policy.persistence`] (File 06 §11.6); the audit log of hook lifecycle events (`HookSubscriptionRegistered`, `HookSubscriptionUnregistered`, `HookSubscriptionEnabledChanged`) — durable in the ledger.
- Computed: the active in-process subscription list (resolved from declarations at startup + on declaration updates); per-subscription performance metrics (decision counts, error rates, average latency) — derived from `HookDecisionRecorded`/`HookTimedOut`/`HookHandlerError`; the currently-active hook chain for a given event kind (computed at emission from registered subscriptions filtered by `event_kinds`, `payload_filter`, `enabled` state).

### 13.2 Startup Sequence
1. event bus initializes (subscriber registry empty).
2. built-in capability declarations register (per [`capability.startup-registration`] File 05 §16.1 phase 1).
3. built-in hook subscriptions register (approval router, structured-logging audit, telemetry collector, stuck detectors, completion-forgery guard).
4. subsystems load + register their hooks.
5. plugins load + register hooks subject to source-approval state.
6. MCP servers connect + register hooks subject to source-approval state.
7. external-API definitions load.
8. user-defined hooks register from settings + file-based declarations.
9. background workers spawn + subscribe to triggering events.
10. the bus enters operational state.
11. `AppStarted` ledger entry committed.
- If a hook fails to register (handler unresolved, source unavailable, declaration invalid), recorded as `HookSubscriptionRegistrationFailed` event + marked `unavailable` until the cause resolves; startup does not abort.

### 13.3 Runtime Mutation (canonical capability calls)
- `hooks.register { declaration }` — `UserApproval`-tier; goes through source-approval for non-builtin sources.
- `hooks.unregister { subscription_id }` — `UserApproval`-tier.
- `hooks.update { subscription_id, declaration_updates }` — `UserApproval`-tier; updates priority/timeout/fail-direction.
- `hooks.set_enabled { subscription_id, enabled, scope }` — `UserApproval`-tier (or lower if the user authorized scoped management).
- Each call goes through the standard pipeline + produces the canonical lifecycle events.

### 13.4 Shutdown (graceful)
1. `AppShuttingDown` event emitted with the configured shutdown policy.
2. new work rejected or queued per policy.
3. in-flight work receives cancellation/pause/fast-finish signals per its capability declaration.
4. critical ledger + audit-overlay records already acknowledged as successful flushed synchronously.
5. noncritical buffers + diagnostics flushed best-effort without making shutdown correctness depend on elapsed time.
6. final lifecycle state committed when the process can do so safely, then the process exits.
- Atlas should be ready to close at any time. Graceful handling is best effort for active work; correctness comes from commit boundaries + restart reconciliation, not from waiting for a shutdown timer.
- On forceful shutdown (crash, SIGKILL, power loss, task-manager kill), in-flight events may be lost. Durable entries written before the crash remain. Next startup detects orphan runs (per [`run.cancellation`]) + reconciles: runs in `running`/`cancelling` state at restart transition to `failed` with typed reason `process_restart_orphan` unless they declared `resume_on_restart: true`.

### 13.5 Restart Reconciliation
- ledger reloads (durable state survives); orphan runs identified + reconciled (per [`run.cancellation`]); `BorrowGrant`s reload (per [`surface.reconstruction-across-restart`] File 07 §14.2); subscription registry rebuilds from durable declarations; the user sees a surface for orphan runs with per-run resume-or-discard affordances; `AppStarted` ledger entry committed.

### 13.6 Boundary
- Subscription persistence owned by this file (contract) + settings system/capability registry (storage). The on-disk format owned by future Storage and Persistence.

## 14. Cancellation, Lifecycle, and Restart `ledger.cancellation-lifecycle-restart`
### 14.1 Cancellation Recording (every cancellation/kill per [`run.cancellation`] records)
- `CancellationRequested` — requester, target, scope (`single_target`/`cascade`), cooperative-stop policy.
- `CancellationProgressing` — listeners that acknowledged + remaining targets.
- `CancellationEscalated` — escalation to forceful termination when cooperative stop insufficient.
- `KillRequested` / `KillSucceeded` / `KillFailed` — forceful stop outcome for an individual process-like target.
- `CleanupCompleted` — cleanup outcome for staged files, sandboxes, subprocesses, browser sessions, orphanable resources.
- `CancellationCompleted` — final outcome with cleanup performed, cooperative-vs-escalated-vs-forceful classification, partial outputs retained/discarded, final status.
- Each entry references the target's `run_id` or narrower target id. Targets include run, child run, model call, provider stream, capability call, hook execution, sandbox, process, browser session, MCP call, scheduler job, registered extension targets. Cascade operations record the root target + each affected child target where safely knowable.
- Same target model powers user-facing process management surfaces: UI can show active process-like units + allow the user to stop a whole cascade or a specific sandbox/tool call/subprocess/stream/child run.
- `OrphanOutputDetected` entries record when a listener reports completion after the run is already `cancelled`; the orphan output does not commit.

### 14.2 Intervention Recording (every user intervention per [`run.user-intervention`] records)
- `InterventionRecorded` with intervention kind (`continuation_with_new_instruction`/`pause`/`cancel`/`branch`/`reroute`/`approval_grant`/`approval_denial`/`scope_narrowing`/`explicit_takeover`), actor, target.
- `TakeoverStarted` + `TakeoverEnded` when `control` (per [`run.minimum-durable-reconstruction`]) transitions.
- User actions during takeover record as first-class ledger entries attributed to the user, indistinguishable in audit from agent-produced entries (per [`run.user-intervention`]).

### 14.3 Restart Behavior
- Per §13.5, restart loads durable state + reconciles orphans. User presented with orphan runs + resume-or-discard affordances. Auto-resume of orphans is forbidden (per [`run.explicit-rejections`] File 04 §28 explicit rejection).

### 14.4 Boundary
- Cancellation + intervention mechanics owned by File 04. This file specifies the durable recording.

## 15. Settings `ledger.settings`
### 15.1 Configurable Dimensions (every mechanism here configurable)
**Hook configuration:**
- `hooks.timeout_default_ms` per category (`approval`/`validator`/`transformer`/`observer`/`completion_verification`/`audit`) as a safety guard, not a correctness condition.
- `hooks.fail_direction_default` per category + authority class, with typed-confirmation required before security-category hooks may fail open.
- `hooks.retry_per_error_class.<error_class>` per hook category (e.g., transient network failure may retry once before fail-closed).
- `hooks.priority_default` per category.
- `hooks.priority_max_user_authored` + `hooks.priority_min_user_authored` (prevent user-authored hooks claiming the approval router tier or below the canonical audit tier without explicit policy approval).
- `hooks.recursion_depth_limit` + per-hook recursion policy.
- `hooks.discovery_path` — file-based hook discovery location, when infrastructure exposes one.
- `hooks.shell_script_allowlist` — explicit allowlist of shell-script hook handler commands per source class.

**Event bus configuration:**
- `events.buffer_size_per_subscriber`.
- `events.aggregation.<event_kind>.batch_ms` — per-kind aggregation cadence.
- `events.aggregation.<event_kind>.batch_max_count` — per-kind aggregation cap.
- `events.aggregation.<event_kind>.suppress_threshold` — per-kind suppression (e.g., mouse moves below 50px).
- `events.resumption_window` — bounded best-effort live replay window.
- `events.frontend_bridge_max_event_kinds` — max event kinds the frontend may subscribe to simultaneously.
- `events.debug_panel_ring_buffer_size`.
- `events.delivery_class.<event_kind>` — delivery class override within canonical limits.

**Ledger configuration:**
- `ledger.retention.public`; `ledger.retention.sensitive`; `ledger.retention.<entry_kind>` per kind (e.g., `ToolCallStreamingPartial` shorter retention); `ledger.compaction_policy` (`disabled`/`default`/`aggressive`); `ledger.compaction_schedule`; `ledger.export_default_sensitivity` (default `Public`); `ledger.sync_default_sensitivity` (default `Public`; user opts in to `Sensitive`).

**Per-call attribution configuration:**
- `attribution.token_source_preference` — preference order for token-counting sources.
- `attribution.tokenizer_fallback_chain` per provider/model descriptor.
- `attribution.cache_token_pricing.<provider>` per provider (cache_creation_multiplier, cache_read_multiplier).
- `attribution.cost_calculation_enabled`.
- `attribution.pricing_tier_user_managed` — flag indicating the user maintains pricing tiers.

**Audit log configuration:**
- `audit.enabled` (never globally disable for security-sensitive operations); `audit.path`; `audit.hash_algorithm`; `audit.tier_membership.<entry_kind>` — which entry kinds participate.

**Streaming configuration:**
- `streaming.chunk_batch_ms` per kind; `streaming.chunk_batch_max_bytes` per kind; `streaming.partial_block_orphan_retention` per capability (when `partial_output_meaningful` is true); `streaming.frontend_render_pace_ms`.

**Lifecycle configuration:**
- `lifecycle.shutdown_safety_guard`; `lifecycle.background_worker_health_policy`; `lifecycle.orphan_run_reconciliation_default` (must surface to user, never `auto_resume`); `lifecycle.log_rotation_size`.

**Sensitivity configuration:**
- `events.sensitivity_export_default` (`Public` excluded by default, `Sensitive` requires opt-in, `Secret` never); `events.sensitivity_clipboard_default`; `events.sensitivity_sync_default`; `events.sensitivity_telemetry_default`; `events.sensitivity_override.<capability_id>` — per-capability override.

### 15.2 Settings-Key Convention
- Hook + event settings use the namespaced dotted-key convention per [`capability.settings-key-convention`] (File 05 §18.2). Plugin/MCP-registered hooks register their settings keys at registration under the source identity.

### 15.3 Agent Exposure of Settings (per [`policy.agent-exposure-policy-settings`])
- `hooks.timeout_default_ms.*`, `events.aggregation.*`, `ledger.retention.*` — `OnRequest` (agent reads on demand; never sees raw subscription declarations).
- `hooks.discovery_path` — `OnRequest`.
- the active hook chain for the current event — `Hidden` (agent does not see which hooks are about to fire).
- `audit.enabled` — `Hidden`; agents cannot disable audit.
- `attribution.token_source_preference` — `OnRequest`.
- `ledger.compaction_policy` — `OnRequest`.

### 15.4 Settings Changes Emit Events
- Per [`run.event-stream`] + cross-cutting/settings.md, every settings change emits `SettingChanged` to the bus. Affected subscriptions recompose on receipt; affected ledger queries re-evaluate.

### 15.5 Boundary
- This file names the settings dimensions. The settings system owns cascade resolution, storage, validation. Defaults belong to tested settings profiles, not hardcoded constants in this canonical layer.

## 16. Hash-Chained Audit Log `ledger.hash-chained-audit-log`
### 16.1 Definition
- A local integrity overlay on a subset of ledger facts for security-sensitive operations. Overlay entries reference ordinary ledger entries + hash their canonical redacted representation; they do not replace the ledger and do not form a second execution-history store.

### 16.2 Required Fields (each overlay entry)
- `ledger_entry_id` — cross-reference to the corresponding ordinary ledger entry.
- `timestamp` — full-granularity.
- `actor` — user identity, agent identity, automation identity, system identity.
- `action` — typed verb (e.g., `approve_tool_call`, `grant_lease`, `revoke_lease`, `accept_typed_confirmation`, `apply_system_change`, `rollback_system_change`, `delete_block`, `delete_artifact`, `register_capability`, `approve_source`, `deny_source`).
- `target` — the affected primitive (capability id, block id, artifact id, lease id, source id, etc.).
- `canonical_redacted_entry_hash` — hash of the canonical redacted ledger entry or safe summary.
- `prev_entry_hash` — the prior entry's `entry_hash`; for the first entry, the genesis hash (zero bytes or installation-specific genesis seed).
- `entry_hash` — hash over prior hash, canonical redacted entry hash, actor, action, target, timestamp, device id, chain id.
- `device_id` + `chain_id` — identify the local chain.

### 16.3 Per-Device Integrity
- The audit log NEVER syncs across devices. Each device maintains its own hash chain with its own genesis. Sync of ordinary ledger entries does not propagate audit-log integrity; per-device audit logs preserve integrity for that device's actions only.
- Intentional: cross-device sync would require resolving hash-chain merges, weakening the integrity guarantee. Per-device audit logs are tamper-evident on the device they protect.

### 16.4 Membership (canonical operation classes; the baseline minimum)
- every policy decision (`PolicyDecisionMade`); every approval grant/denial (`ApprovalGranted`, `ApprovalDenied`); every lease lifecycle event (`LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `LeaseNarrowed`); every typed-confirmation completion (`TypedConfirmationSatisfied`, `TypedConfirmationMismatched`); every floor violation (`PolicyFloorViolated`); every source approval/denial (`SourceRegistrationApproved`, `SourceRegistrationDenied`, `SourceRegistrationDeferred`); every credential/secret operation (future Security spec registers the entries); every system-state mutation declared by System Agent/runtime infrastructure/security specs; every hard delete (`BlockHardDeleted`, `ArtifactHardDeleted`, `LeaseHardDeleted`, `CapabilityHardDeleted`); every `DeniedFloorOverridden` (the typed-confirmation override path through `Denied`); every `RunCompletionForgeryAttempted`; every hook authority-class change.
- Settings `audit.tier_membership.<entry_kind>` allows the user to add additional entry kinds; the canonical baseline above is the minimum.

### 16.5 Verification
- A verifier reads the overlay entries in order, recomputes `entry_hash` for each, checks against the recorded hash. Any mismatch produces: `AuditChainTamperDetected` event with the offending entry's `ledger_entry_id`; the device's sync stops until the user resolves (replay from a known-good backup or accept the tamper detection + proceed with a fresh chain); the user is surfaced with the audit chain's state.
- Verification may run: on demand through `audit.verify` (a registered `ReadOnly` capability); at startup using the configured verification profile; during shutdown only when it does not delay fast close (shutdown is not a correctness condition for audit integrity).

### 16.6 Boundary
- A local integrity overlay over selected ledger entries. Future Security spec owns the cryptographic primitives + audit storage details. This file specifies structure, membership, verification contract.

## 17. Lifecycle Integration `ledger.lifecycle-integration`
### 17.1 Startup Phases (per cross-cutting infrastructure/lifecycle.md + [`capability.startup-registration`] File 05 §16.1)
1. infrastructure: SQLite/libsql open, schema migrations applied, file system watchers spawned, event bus initialized.
2. registry: capability declarations register (built-in → subsystem → plugin → MCP → API → user-defined).
3. settings: settings cascade resolves, settings change watchers spawn.
4. hooks: hook subscriptions register per §13.2.
5. background workers: spawned + subscribed to triggering events.
6. UI: frontend bridge opens.
7. `AppStarted` ledger entry committed.
- Startup ordering deterministic; replay reads `AppStarted` to know the state in effect.

### 17.2 Background Workers
- Process-like execution units registered by their owning subsystems. Cross-cutting examples: audit-overlay writing, lineage tracking, system-watch evaluation, scheduled-trigger dispatch. Domain workers (memory consolidation, SRS scheduling) declare their own `Custom` events in their owning specs.
- Each worker emits `BackgroundWorkerSpawned`, health/progress events under its declared delivery class, `BackgroundWorkerStopped`. Failure emits `BackgroundWorkerFailed` + triggers recovery per settings/policy. Time-based cadences, when inherently needed, are settings-controlled scheduling inputs, not correctness conditions for this layer.

### 17.3 Cancellation Token
- A global intervention handler maintains a cancellation token shared between the agent loop, long-running tool calls, sandbox operations, git service calls. User-initiated interrupt sets the token; operations check at safe points + abort cleanly. The interrupt is itself recorded as `InterventionRecorded`.

### 17.4 Shutdown
- Per §13.4, shutdown stops new work, signals active work, flushes acknowledged critical ledger/audit-overlay records synchronously, best-effort flushes noncritical buffers, records final lifecycle state when safely possible. Correctness does not depend on a shutdown timer.

### 17.5 Boundary
- Ties the durable + live recording layer into the application's startup/runtime/shutdown sequences. The actual lifecycle mechanics owned by future Runtime Infrastructure.

## 18. Explicit Rejections `ledger.explicit-rejections`
- A parallel event bus, parallel ledger, or parallel hook system — every event flows through one bus, every consequential fact persists to one ledger, every extensibility point is a hook on the canonical bus; subsystems/plugins/MCP servers/user-defined sources never invent parallel mechanisms.
- Silent execution: any capability invocation that does not produce a `ToolCallProposed` followed by either `ToolCallExecuted` + `ToolCallCompleted`, or `ToolCallFailed`, or `ToolCallDenied`, violates the canonical pipeline contract; every consequential action is recorded.
- Silent hook decisions: any blocking hook that returns a decision without emitting `HookDecisionRecorded`, or any timeout/error without `HookTimedOut`/`HookHandlerError`, is invalid.
- Unkeyed model-dependent scalars: token counts, costs, cache statistics, or any model-dependent value as an unkeyed integer/float on a ledger row violates [`core.explicit-rejections`] + is rejected at commit.
- `Secret`-tagged payloads persisting to the durable ledger: commit validator rejects entries that would persist raw secret content; only safe descriptions persist.
- Mutable ledger entries: a committed `LedgerEntry`'s structural fields are fixed; corrections create new entries via `supersedes`, never in-place updates.
- Ledger entries with payload schemas outside the closed canonical catalogue plus registered `Custom` extensions — every entry is typed.
- Time-based hook firing: hooks fire only on event emission; the runtime never polls for hooks; periodic background work uses background workers (§17.2), not hook-polling.
- Hard-coded hook timeouts: every timeout is a settings dimension; canonical defaults exist but the user can override per category.
- Hooks that bypass the event bus: a hook handler must dispatch through the standard `HookAction` taxonomy (`RunScript`/`InvokeCapability`/`EmitEvent`/`InternalHandler`); ad-hoc procedural execution is rejected.
- Hooks that mutate the ledger directly: hooks emit decisions the executor records as `HookDecisionRecorded` entries; hooks do not write ledger entries themselves.
- Implicit ledger inference from events: events are live coordination; consequential events must be explicitly committed by the executor/emitter; the ledger never silently materializes from event observation.
- Live events as durable history: events are transient; the ledger is durable; pure UI-coordination events do not persist.
- Cross-device sync of the audit log: per-device for hash-chain integrity; sync of ordinary ledger entries is separate.
- Silent retention or pruning: every retention transition is `LedgerCompactionRan` or per-kind retention policy; nothing disappears without a recorded event.
- Canceled-but-still-running operations: cancellation must record `CancellationCompleted` with the final state; runs do not silently complete after cancellation.
- Forgery of run completion: the status-transition forgery guard rejects `running → completed` transitions without ledger evidence of action (per [`run.termination`]).
- Hooks that exceed their declared authority: a hook declared `observe_only` returning a non-`Continue` decision is downgraded to `Continue` + a warning; hooks cannot escalate authority at runtime.
- Ad-hoc hook decision shapes: only `Continue`, `Substitute`, `Block`, `RedirectSuggestion` are valid; ad-hoc payloads or out-of-vocabulary decisions rejected.
- Silent batched approval: every approval (per-call or batched) records `ApprovalRequested`/`ApprovalGranted`/`ApprovalDenied`.
- Bypassing the approval router for capability invocations: every consequential invocation goes through `ToolCallProposed`, which the approval router subscribes to at `+100`.
- Per-capability custom approval logic in handlers: capability authors implement operations, not approval flows; approval is a hook subscription, not a capability-internal concern.
- Using event sequence numbers across devices for global ordering: sequences are per declared `sequence_scope`; cross-device ordering relies on the future Sync spec, not a global monotonic counter.
- Recording per-tokenizer scalars on the block: token counts computed on demand keyed by tokenizer per [`block.what-is-computed`] (File 08 §13.2); never persist a single integer on the block row without model identifier.
- Mutating ledger entries to reflect retroactive sensitivity reclassification: sensitivity is fixed at commit; if a `Public` entry is later judged `Sensitive`, the original persists but a sibling `SensitivityReclassified` entry is committed + downstream filters honor the reclassification.
- The bus claiming durability guarantees: the bus is transient coordination; consequential events also persist to the ledger but bus delivery itself is best-effort with bounded buffers; subscribers seeking durable guarantees query the ledger.
- Combining `Substitute` with semantic target change: `Substitute { substitution_kind: transparent_redirect }` may change a target capability to a safer equivalent only when the change is declared transparent; meaningful behavioral changes require `Block` followed by ask-user.
- Pre-validation hooks running after validators: priority `-100` hooks run first; placement is canonical, not negotiable; ordering relies on this convention.
- Ledger entries with omitted envelopes: every entry carries the full envelope; contextual refs inside `context_refs` may be absent only when inapplicable.
- Hook handlers that mutate global state outside the typed action taxonomy: handlers either return a typed decision, invoke a registered capability, or emit a synthesized event; direct global-state mutation is forbidden.
- Using shutdown grace periods as correctness: successful critical ledger/audit-overlay commits must be durable before success is reported; shutdown flushing is best effort for remaining noncritical buffers.
- The ledger silently becoming the version graph: the ledger references version ids; File 11 owns the version-tree action log; ledger entries do not duplicate version-graph operations.
- Duplicating per-capability data into ledger payloads: entries reference capability declarations via `(capability_id, capability_version)`; they do not embed the declaration content.
- Using `Custom` event kinds for canonical concerns: if a new canonical-kind need arises, the canonical catalogue extends through a canonical-spec update; `Custom` is for subsystem-/surface-/plugin-/MCP-/API-/user-defined extensions, not canonical workarounds.
- Treating cancellation as a destructive operation: cancellation is a recorded ledger event; partial outputs may persist per declaration; cancellation does not erase prior ledger entries.

## 19. Consequences for Later Specs `ledger.consequences-for-later-specs`
- Every later spec that produces/consumes execution facts, emits/subscribes to events, registers a hook, or queries the ledger for replay/audit/telemetry/evaluation consumes this layer as defined here.
- Canonical principles later specs must follow:
  - emit events through the canonical bus with the standard envelope; never invent a parallel event bus or omit envelope fields.
  - record consequential facts to the ledger through the canonical `LedgerEntry` mechanism; never invent a parallel durable record store.
  - register extensibility points as `Hook` subscriptions on the canonical bus; never invent a parallel hook system or middleware chain.
  - honor the typed `HookDecision` vocabulary (`Continue`/`Substitute`/`Block`/`RedirectSuggestion`); never invent new decision shapes.
  - honor the priority convention (`-100` audit, `0` validators/transformers, `+100` approval router); never claim positions outside the user-authored envelope without explicit canonical extension.
  - honor the authority-class semantics; never escalate hook authority at runtime.
  - honor the per-call attribution requirement (`TokenUsageRecord` keyed by model identifier); never store unkeyed model-dependent scalars.
  - honor the sensitivity-aware persistence rules (`Public`/`Sensitive`/`Secret`); never persist `Secret` raw content.
  - honor the forgery guards (run-completion contract, unkeyed-scalar rejection); never bypass through subsystem-internal paths.
  - consume the closed `AppEvent` + `LedgerEntryKind` catalogues; declare new specialized kinds through `Custom { namespace, name, payload }` with proposal-first source-approval.
  - record specialized events through the canonical mechanism; the ledger + bus integrate them uniformly with the standard envelope, sensitivity, cross-references.
- Specific integration contracts:
  - Version Graph, Commits, and Projections consume ledger commit boundaries + emit version events through this layer; the ledger references version ids but does not own version-tree invariants.
  - Retrieval, Indexing, Knowledge Base, Memory, Perception, Web, Coder, Teacher, Data Processor, GUI Control, System Agent, SRS, Automation, Workflows, surface-specific specs declare specialized event + ledger-entry kinds through `Custom { namespace, name, payload }` rather than adding them to the closed canonical catalogue here.
  - Context Assembly and Compaction emit context-budget + compaction facts through bus + ledger, while owning the model-request assembly + compaction algorithms.
  - Model Strategy, Provider, Rate Limits, and Usage Accounting consume `TokenUsageRecord`, provider identity, tokenizer identity, pricing snapshots; must not store unkeyed token/cost scalars.
  - World Model, Settings, Storage, Sync, Security, Sandbox, Process Control, Workspaces, Control Rails, Plugins, MCP integrations, UI, Quality Control, Evaluation, Telemetry, Runtime Infrastructure, Packaging consume this file's envelope, delivery-class, sensitivity, hook, audit-overlay, replay, ledger contracts.
- Specific integration contracts stated in those specs when written. Until then, the canonical contract here is the load-bearing reference for every spec touching execution recording, live coordination, or extensibility.
