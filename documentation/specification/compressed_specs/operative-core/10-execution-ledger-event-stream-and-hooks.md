# Execution Ledger, Event Stream, and Hooks — Operative Core

## 1. Chosen Model `ledger.chosen-model`
- Three primitives: `ExecutionLedger`, `EventStream`, `Hook`. One `EventEnvelope`, one closed `AppEvent` catalogue with `Custom`, one hook decision vocabulary, one bus.
- Extensions never produce parallel buses/ledgers/hook systems.

## 2. Boundaries With Adjacent Layers `ledger.boundaries-with-adjacent-layers`
### 2.8 Boundary

## 3. `ExecutionLedger` `ledger.execution-ledger`
### 3.1 Definition
- The ledger is: durable; append-only (corrections create new entries linked via `supersedes`); queryable; scoped; sensitivity-aware; cross-referenced; attribution-bearing.
- `Secret` payloads do NOT persist.
### 3.2 Required Fields (every `LedgerEntry`)
- `entry_id`, `kind`, `envelope`, `scope`, `payload`, `cross_references`, `produced_at`, `producer`, `entry_schema_version`, `idempotency_key`, `supersedes`.
- `entry_id` never reused/reassigned/mutated.
- `producer` variants: `Executor { run_id, step_id }`, `RouterEmission { route_id }`, `Subsystem { subsystem_id, reason }`, `Hook { hook_id, source }`, `UserAction { user_id, action_kind }`, `Automation { trigger_id }`.
### 3.3 Append-Only Invariant
- A committed entry's `kind`, `envelope`, `scope`, `payload`, `cross_references`, `produced_at`, `producer`, `entry_schema_version` are fixed at commit.
- A reader at `t1` and again at `t2` MUST see the same content for any entry committed before `t1`.
### 3.6 Cross-References `ledger.cross-references`
- Reference key set: `conversation_id`, `run_id`, `task_id`, `intent_thread_id`, `workspace_id`, `parent_run_id`, `route_id`, `invocation_id`, `capability_id`, `capability_version`, `source_instance_id`, `backend_binding_id`, `block_id`, `version_id`, `artifact_id`, `artifact_version_block_id`, `claim_id`, `evidence_link_edge_id`, `lease_id`, `approval_request_id`, `hook_id`, `subscription_id`, `observation_id`, `validation_id`, `critique_id`, `staleness_fingerprint`, `policy_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `registry_snapshot_id`, `event_id`, `supersedes_entry_id`, `parent_entry_id`, `child_entry_ids`.
### 3.7 Forgery Guards `ledger.forgery-guards`
- Status-transition forgery guard: `running → completed` REJECTED on a contract-required-action run with no `ToolCallExecuted`/`ToolCallCompleted`, no `ArtifactVersionCommitted`, no non-pure-text `ModelCallCompleted` in scope; produces `LedgerCommitRejected` + `RunCompletionForgeryAttempted`.
- Contract-revision forgery guard: a `Weakening`/`Removal` `RunCompletionContractRevised` REJECTED unless `authority_source` is at least as strong as each affected requirement's introducing authority; a weakening/removal authored by the run's own executing agent is REJECTED.
- Unkeyed-scalar forgery guard: every model-dependent scalar MUST be keyed by `(provider_id, model_id, tokenizer_id)`; unkeyed entry REJECTED as `UnkeyedModelDependentScalar`.
- `Secret`-tagged payloads MUST never persist to the durable ledger.
- Every `entry_id` MUST be globally unique; `supersedes` MUST resolve to a prior entry.

## 4. Canonical `LedgerEntryKind` Catalogue `ledger.entry-kinds`
### 4.1 Closed Canonical Catalogue `ledger.entry-kind-catalogue`
**Run lifecycle:** `RunCreated`, `RunStatusChanged`, `RunResumed`, `RunSuperseded`, `RunCompletionContractRevised`, `RunCompletionForgeryAttempted`, `ControlTransferred`.
- `RunCompletionContractRevised.revision_kind`: `Additive`, `Narrowing`, `Weakening`, `Removal`.
**Routing:** `RoutingFrameComposed`, `PrecheckEvaluated`, `RouterDecisionEmitted`, `RouteRecordCommitted`, `MidExecutionRerouteRequested`, `MidExecutionRerouteResolved`.
- `PrecheckEvaluated` verdict: `resolved`, `constrained`, `no_op`.
- `MidExecutionRerouteResolved` path: `router_resolved`, `self_routed`, `direct_handback`.
**Capability invocation pipeline:** `ToolCallProposed`, `ValidatorRan`, `PolicyDecisionMade`, `ApprovalRequested`, `ApprovalGranted`, `ApprovalDenied`, `LeaseGranted`, `LeaseRevoked`, `LeaseStale`, `LeaseNarrowed`, `PolicyContradictionDetected`, `PolicyContradictionResolved`, `PolicyFloorViolated`, `ClassifierMediatedDecision`, `ToolCallApproved`, `ToolCallDenied`, `ToolCallExecuted`, `ToolCallStreamingPartial`, `ToolCallCompleted`, `ToolCallFailed`, `ObservationCommitted`, `ValidationCommitted`, `CritiquePosted`.
- `ValidatorRan` verdict: `valid`, `invalid_with_correction`, `invalid`.
**Model calls:** `ModelCallStarted`, `ModelCallCompleted`, `ModelCallStreamingDelta`, `ModelCallFailed`, `ProviderHealthChanged`, `RateLimitSnapshotReconciled`, `TokenCountEstimationTelemetry`.
- `ModelCallFailed` retry classification: `retryable`, `rate_limited`, `fatal`.
- `ProviderHealthChanged` states: `Healthy`, `Degraded`, `Unhealthy`.
**Block and version-graph:** `BlockCommitted`, `BlockLifecycleChanged`, `BlockPinChanged`, `BlockGrouped`, `BlockUngrouped`, `BlockHardDeleted`, `VersionCommitted`, `VersionSwitched`, `PendingOpApplied`.
**Artifact and entity:** `ArtifactCreated`, `ArtifactVersionCommitted`, `ArtifactLifecycleChanged`, `ArtifactReviewStateChanged`, `ArtifactValidationStateChanged`, `ArtifactMaterialized`, `ArtifactExternallyEdited`, `ArtifactArchived`, `ArtifactDiscarded`, `ArtifactRestored`, `ArtifactHardDeleted`, `ClaimPublished`, `ClaimStatusOverridden`, `ClaimWithdrawn`, `EvidenceLinked`, `EvidenceLinkRemoved`, `CitationCaptured`, `ProvenanceQueryExecuted`.
**Surface and capability registry:** `ToolSurfaceComposed`, `ToolSurfaceShrunk`, `ToolSurfaceOverflow`, `CapabilityBorrowed`, `CapabilityBorrowReturned`, `CapabilityZoneChanged`, `CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityUpdated`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `CapabilityRegistryStateChanged`, `SubsystemSurfaceSpecUpdated`, `PrimarySurfaceChanged`, `LensFilterChanged`, `SourceConnected`, `SourceDisconnected`, `SourceRegistrationApproved`, `SourceRegistrationDenied`, `SourceRegistrationDeferred`, `ShortcutConflict`.
**Child run, parallel work, merge:** `ChildRunSpawned`, `ChildRunStatusChanged`, `ChildRunMerged`, `SiblingAborted`, `DependencyFailureSkipped`, `BatchCoalesced`.
- `ChildRunMerged` merge mode: summary, artifact, patch, evidence-set, validation-report, proposed-task-update, proposed-workflow-step.
**Streaming and live partials:** `StreamStarted`, `StreamProgressBatch`, `StreamCompleted`, `StreamCancelled`, `FilePartialWriteStaged`, `FilePartialWriteAborted`, `FilePartialWriteCommitted`.
**Hook events:** `HookSubscriptionRegistered`, `HookSubscriptionUnregistered`, `HookSubscriptionEnabledChanged`, `HookFired`, `HookDecisionRecorded`, `HookTimedOut`, `HookHandlerError`, `HookActionInvoked`.
**Error and recovery:** `TypedErrorRaised`, `RecoveryStrategyApplied`, `ContextPressureObserved`, `StuckDetected`, `StuckEscalated`, `BudgetWarning`, `BudgetExhausted`, `LoopDetected`, `RetryAttempted`, `BranchCreated`, `RerouteResolved`.
- `RecoveryStrategyApplied` strategy: `retry_same_unit`, `expose_to_model`, `switch_model_profile`, `switch_capability_implementation`, `narrow_capability_scope`, `revoke_and_narrow_lease`, `request_user_clarification`, `branch_strategy`, `restore_or_rollback`, `stop_with_typed_failure`.
- `StuckDetected` pattern: `repeated_identical_tool_calls`, `repeated_failed_validations`, `repeated_provider_errors`, `no_new_durable_output`, `cyclic_child_waiting`, `ping_pong`, `single_iteration_empty_response`.
**Cancellation and intervention:** `CancellationRequested`, `CancellationProgressing`, `CancellationEscalated`, `CancellationCompleted`, `OrphanOutputDetected`, `InterventionRecorded`, `TakeoverStarted`, `TakeoverEnded`.
- `InterventionRecorded` kind: `continuation_with_new_instruction`, `pause`, `cancel`, `branch`, `reroute`, `approval_grant`, `approval_denial`, `scope_narrowing`, `explicit_takeover`.
**Workspace, file, external state:** `WorkspaceOpened`, `WorkspaceClosed`, `FileIngested`, `FileExternallyModified`, `FileMaterialized`, `EnvironmentSnapshotCaptured`.
- Domain-specific workspace/source-control/browser/perception/system-watch/memory/retrieval/knowledge-base/SRS facts are NOT predeclared; declared as `Custom { namespace, name, payload }`.
**Validation and quality control:** `CompletionVerificationFired`, `QualityControlValidatorRan`, `QualityControlViolationDetected`.
**Approval and contradiction:** `BatchApprovalRequested`, `BatchApprovalResolved`, `TypedConfirmationRequested`, `TypedConfirmationSatisfied`, `TypedConfirmationMismatched`, `DeniedFloorOverridden`, `SourceApprovalFlowOpened`, `SourceApprovalFlowResolved`.
**Automation, scheduling, triggers:** `AutomationTriggerFired`, `WebhookReceived`, `OsEventReceived`.
**Sync and persistence:** `SyncPulled`, `SyncPushed`, `SyncVersionDiverged`, `SyncBlobFetched`, `SyncFailed`, `LedgerCompactionRan`.
**System / app lifecycle:** `AppStarted`, `AppShuttingDown`, `AppStopped`, `BackgroundWorkerSpawned`, `BackgroundWorkerStopped`, `BackgroundWorkerHeartbeat`, `LedgerCommitRejected`.
**Custom extension:** `Custom { namespace, name, payload }`.
### 4.2 Kind Composition Rules
- Every capability-invocation kind (`ToolCallProposed`, `ToolCallExecuted`, `ToolCallCompleted`, `ToolCallFailed`, `ToolCallDenied`) MUST share a single `invocation_id`.
- Every model-call kind (`ModelCallStarted`, `ModelCallCompleted`, `ModelCallStreamingDelta`, `ModelCallFailed`) MUST share a single `request_id`.
- Every `BlockCommitted` MUST reference the produced `block_id` + the producing `invocation_id` (when capability-produced).
- Every artifact-event kind MUST reference the `artifact_id` + `artifact_version_block_id`.
- Every hook-decision kind (`HookDecisionRecorded`, `HookTimedOut`, `HookHandlerError`) MUST reference the originating `event_id` + `subscription_id`.
- Every cancellation kind MUST reference the `run_id` (or `tool_call_id` if narrower) + the `requester`.
### 4.3 Custom Kind Registration `ledger.custom-kind-registration`
- A custom kind cannot violate canonical composition rules; registration REJECTED if it would.
- Unknown custom kinds storable/renderable only as opaque safe records until schema registered + trusted.
### 4.4 Boundary
- Adding a new canonical kind is a canonical-spec change, not a runtime registration.

## 5. `EventStream` `ledger.event-stream`
### 5.1 Definition
- The bus IS: typed; ordered within `sequence_scope`; fan-out; backpressure-aware; sensitivity-aware.
### 5.2 `EventEnvelope` `ledger.event-envelope`
- Fields: `event_id`, `conversation_id`, `context_refs`, `parent_event_id`, `causal_event_ids`, `trace_context`, `sequence_scope`, `sequence`, `timestamp`, `sensitivity`.
- `context_refs` keys: `run_id`, `step_id`, `node_id`, `workspace_id`, `worktree_id`, `backend_id`, `capability_id`, `ledger_entry_id`, registered extension refs.
- `event_id` never reused; `sensitivity` closed: `Public`, `Sensitive`, `Secret`.
- The envelope itself is mandatory.
### 5.3 Closed `AppEvent` Catalogue `ledger.app-event-catalogue`
- Catalogue = the `LedgerEntryKind` set (§4) plus transient-coordination kinds.
**Transient-coordination kinds (live bus only, not durable):** `MessageChunk`, `ReasoningChunk`, `BlockStreamStarted`, `BlockStreamCompleted`, `ContextAssembled`, `ContextBudgetWarning`, `CompactionStarted`, `CompactionCompleted`, `UiPanelRegistered`, `UiPanelUnregistered`, `UiPrimaryPanelChanged`, `UiSelectionChanged`, `UiModeChanged`, `UiAvailableCapabilitiesRecomputed`, `UiThemeChanged`, `UiKeybindingChanged`, `UiLayoutChanged`, `DebugLog`, `EventBufferOverflow`, `Ping`, `Pong`, `SocketIoMessage`, `Heartbeat`.
- All `LedgerEntryKind` variants from §4 are also `AppEvent` variants.
### 5.4 Delivery Semantics
- Within a `sequence_scope`: events delivered in monotonic `sequence` order, deterministic across replay.
- Observing an event never creates the durable fact.
### 5.5 Delivery Classes and Aggregation Policies
- Delivery classes: `lossless_consequential`, `coalescible`, `latest_only`, `sampled_diagnostic`.
- Aggregation never silently drops consequential events.
### 5.6 Sensitivity Tagging at Emission
- Every event carries `sensitivity` at emission; downstream MUST NOT lower the classification (only raise).
- Executor stamps `Sensitive` on credentials/secrets/raw user-private data/`sensitivity_field_map`-flagged payloads.
- Executor stamps `Secret` on raw credentials in flight and strips/replaces before any persistence path.
- `Secret`-tagged events MUST NOT flow to storage paths (durable ledger, sync, export, telemetry).
- `Secret` payloads never delivered to ordinary subscribers.
### 5.7 Frontend Bridge
- The bridge MUST gate `Secret`-tagged events (frontend never receives a raw secret payload).

## 6. Per-Call Model-Call Attribution `ledger.per-call-model-call-attribution`
### 6.1 Definition
- Every `ModelCallCompleted` MUST carry a complete `TokenUsageRecord` keyed by `(provider_id, model_id, tokenizer_id, role)`.
### 6.2 `TokenUsageRecord` fields
- `record_id`, `entry_id`, `conversation_id`, `run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `provider_id`, `model_id`, `tokenizer_id`, `role`, `prompt_tokens`, `completion_tokens`, `cache_creation_tokens`, `cache_read_tokens`, `reasoning_tokens`, `request_id`, `token_source`, `usage_source`, `cost_calculated_at`, `pricing_snapshot_id`, `pricing_tier_id`, `latency_ms`, `inference_time_ms`, `cached_input_tokens`, `image_tokens`, `audio_tokens`, `video_tokens`.
- `role`: `router`, `responder`, `critic`, `validator`, `summarizer`, `sub_agent`, `classifier`, `judge`, or registered custom role.
- `usage_source`: provider-reported, local-estimated, provider-counting-endpoint, multimodal-estimated, mixed.
- The record is NOT durable as a single scalar (no unkeyed `total_tokens`).
### 6.3 `TokenSource` (closed)
- `ProviderNative { confidence }`, `LocalTokenizer { tokenizer_id, confidence }`, `ProviderCountingApi { endpoint_ref, confidence }`, `CharacterApproximation { formula_id, safety_margin, confidence }`, `MultimodalEstimate { dimension, units, formula_id }`.
### 6.4 Cost Computation `ledger.cost-computation`
- Cost MUST never be stored as unkeyed scalar in any ledger row.
- `PricingTier` fields: `provider_id`, `model_id`, `input_usd_per_million`, `output_usd_per_million`, `cache_creation_usd_per_million`, `cache_read_usd_per_million`, `multimodal_pricing`, `pricing_version`, `effective_from`, `effective_until`.
- Queries needing cost emit a typed `PricingUnavailable` error when no tier matches.
### 6.6 STT / TTS Usage
- `SttUsageRecord { provider_id, model_id, audio_seconds, duration_ms, request_id }`; `TtsUsageRecord { provider_id, voice_id, chars_synthesised, audio_seconds_generated, request_id }`.

## 7. `Hook` `ledger.hook`
### 7.1 Definition
- Every hook declares: `event_kinds`, `mode` (`Blocking`/`NonBlocking`), `priority` (`i16`), `timeout_ms`, `hook_category`, `authority_class`, `handler`, `source`, `enabled`, `subscription_id`, per-error-class retry behavior, `payload_filter`.
- `hook_category`: `approval`, `validator`, `completion_verification`, `postcondition_check`, `safety_gate`, `transformer`, `formatter`, `enricher`, `localizer`, `observer`, registered extension.
- `authority_class`: `observe_only`, `narrowing_only`, `allow_capable`, `substitute_capable`.
- `source`: `Builtin`, `Subsystem { id }`, `Plugin { id, version }`, `McpServer { server_id }`, `Api { api_id }`, `UserDefined { scope }`.
### 7.2 Hook Decision Vocabulary `ledger.hook-decision-vocabulary`
- Closed `HookDecision`: `Continue { reason }`, `Substitute { new_payload, reason, substitution_kind }`, `Block { reason, error_kind }`, `RedirectSuggestion { target_capability_id, suggested_args, reason }`.
- `substitution_kind`: `narrowing_only`, `redaction`, `transparent_redirect`, registered extension.
- Semantic target/action changes REQUIRE `Block` + a follow-up ask-user flow, not silent `Substitute`.
- A decision outside this set is rejected.
### 7.3 Priority and Ordering `ledger.priority-ordering`
- Priority convention: `-100` audit/logging; `0` transformers/validators/narrowing; `+100` approval router.
- User-authored + third-party hooks register within `[-99, +99]` (cannot place above approval router or below audit tier without explicit user-defined-policy approval).
- All substitutions MUST record safe before/after hashes or summaries.
- The approval router evaluates the final substituted proposal.
### 7.4 Authority Classes `ledger.authority-classes`
- `observe_only`: MUST NOT produce `Block`/`Substitute`/`RedirectSuggestion`; non-`Continue` treated as `Continue` + warning.
- `narrowing_only`: MUST NOT produce `Continue` bypassing a prior hook's stricter decision.
- `allow_capable`, `substitute_capable`: registered only by `Builtin`/`Subsystem`/`Verified`/explicitly user-approved sources.
- `Community`/`Unverified`/`Plugin`/`McpServer`/`Api`/`UserDefined` default to `narrowing_only` until user upgrades.
- No hook can bypass `permission_floor`, typed-confirmation requirements, contradiction detection, or touched-resource constraints.
### 7.5 Timeout and Fail-Direction
- Security-category hooks (`approval`, `validator`, `completion_verification`, `postcondition_check`, `safety_gate`) default-on-timeout/error to `Block`.
- Non-security hooks (`formatter`, `enricher`, `localizer`, `observer`) default to `Continue` + warning.
- Security-category hooks cannot be set fail-open without typed confirmation.
### 7.6 Hook Lifecycle Events
- `HookSubscriptionRegistered`, `HookSubscriptionUnregistered`, `HookSubscriptionEnabledChanged`, `HookFired`, `HookDecisionRecorded`, `HookTimedOut`, `HookHandlerError`, `HookActionInvoked`.
### 7.7 Hook Categories
- Approval; Quality-control validators; Audit and logging; Transformers; Observers; Completion-verification; Stuck detectors; Recovery; Surface mutation observers; Entity event observers; Streaming UI observers; Background workers.

## 8. Hook Registration and Discovery `ledger.hook-registration-discovery`
### 8.3 Plugin / MCP / API / User-Defined Hooks
- External + user-defined sources register through capability-registration with proposal-first source-approval.
- `Community`/`Unverified` trust default to `narrowing_only` and cannot register at `+100` or below `-99`.
### 8.4 User-Authored Hook Declarations
- Three mechanisms: Settings-backed (typed `HookDeclaration`); File-based (TOML); Runtime registration capability (`tools.register_hook`, `UserApproval` tier).
### 8.5 Hook Discovery and Inspection
- `hooks.list`, `hooks.inspect { subscription_id }`, `hooks.decision_history { subscription_id, time_range }` — all `ReadOnly` tier.

## 9. Hook Effect Vocabulary `ledger.hook-action-vocabulary`
### 9.1 Definition
- Closed `HookAction`: `RunScript { command, args, env, stdin_template, timeout_ms, working_directory, sensitivity_classification }`, `InvokeCapability { capability_id, args_template, sensitivity_classification }`, `EmitEvent { event_kind, payload_template }`, `InternalHandler { handler_id }`.
- Action settled at registration; a hook does not switch action kinds at runtime.
### 9.2 `RunScript` Wire Protocol
- stdout decision schema fields: `decision` (`continue`/`block`/`substitute`/`redirect_suggestion`), `reason`, `new_payload`, `substitution_kind`, `target_capability_id`, `suggested_args`, `error_kind`, `context_modification`, `system_message_injection`.
- Runtime MUST enforce: the timeout; `Secret`-tagged payloads never written to stdin in raw form.
### 9.4 `EmitEvent` Semantics
- A hook does NOT receive its own derivative events by default.
- Recursive subscriptions MUST declare maximum depth, cycle policy, and whether repeated loops allowed.
- Infinite unbounded loops are not a valid default.
### 9.5 `InternalHandler` Semantics
- Not exposed to external sources without explicit user approval (`Verified` trust).
### 9.6 Boundary
- Hook-effect vocabulary is closed: `RunScript`, `InvokeCapability`, `EmitEvent`, `InternalHandler`. New kinds require a canonical-spec update.

## 10. Sensitivity-Aware Persistence and Retention `ledger.sensitivity-aware-persistence-retention`
### 10.1 Three Classes
- Closed set: `Public`, `Sensitive`, `Secret`.
- `Secret`: persisted with payload redaction at commit; only `safe_description` strings persist; raw held only transiently or in vault, zeroed after use.
### 10.2 Producer-Seeded Sensitivity `ledger.producer-seeded-sensitivity`
- Producer cannot lower a field's effective sensitivity below its inherited/declared baseline.
- Lowering requires a typed-confirmation policy override.
### 10.3 Persistence Effects
- Redaction happens at commit, not query time.
- Runtime MUST ensure no path ever sees raw `Secret` content.
### 10.4 Retention Policies
- `events.retention.public`, `events.retention.sensitive`, `events.retention.secret` (N/A raw; safe descriptions follow sensitive).
- No storage layer may silently prune `Sensitive` or safe-description `Secret` records without a recorded policy transition.
### 10.5 Hash-Chained Audit-Log Tier
- Structure: `{ ledger_entry_id, timestamp, actor, action, target, canonical_redacted_entry_hash, prev_entry_hash, entry_hash, device_id, chain_id }`.
- Per-device only — the audit log MUST NEVER sync across devices.
- Never disabled — security-sensitive operations always write to the audit log.
- Any hash mismatch produces `AuditChainTamperDetected` (halts sync of the affected device).
### 10.6 Export and Share Filtering
- Default export/share include only `Public`-tagged entries.
- `Secret` payloads never included.
- Settings: `events.sensitivity_export_default`, `events.sensitivity_sync_default`, `events.sensitivity_clipboard_default`.

## 11. Replay Semantics `ledger.replay-semantics`
### 11.1 Definition
### 11.2 What Is Required for Replay
- full ledger entries; block pool; version-graph snapshot; entity pool; registry snapshot; settings snapshot; policy snapshot; world-model snapshot; observation staleness fingerprints.
### 11.3 Replay Classes (`replay_class`)
- `deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable`.
### 11.4 Replay Modes
- `Inspect`, `SimulateDeterministic`, `FullRerun`.
- Each replay records a `ReplayRun` entry.
### 11.5 Forensic Queries (closed, `ReadOnly`)
- `query_what_did_the_agent_see_at_time_t(run_id, timestamp)`, `query_which_capabilities_did_run_invoke(run_id)`, `query_which_model_calls_consumed_what_tokens(run_id)`, `query_which_blocks_did_run_produce(run_id)`, `query_which_artifacts_did_run_modify(run_id)`, `query_which_hooks_fired(run_id)`, `query_run_lineage(run_id)`, `query_evidence_chain(claim_id)`.

## 12. Streaming and Live Partials `ledger.streaming-live-partials`
### 12.1 Streaming Categories
- Model text deltas (`MessageChunk`); reasoning deltas (`ReasoningChunk`, default `Sensitive`); tool-input streaming; tool-output streaming; file/artifact live partial-write; reasoning summary streaming; progress events.
### 12.2 Commit Boundary Contract
- Streamed partials are NOT durable blocks until the producer's declared commit boundary fires.
- On pre-commit failure, no committed block exists; runtime emits `StreamCancelled`.
### 12.4 Live-Partial-Write Capabilities
- The capability MUST validate the target before any write; write into a temp/staged location; atomic rename on commit; delete the staged file on cancellation.
### 12.5 Resumption
- Transport resume tokens are conveniences, not durability guarantees.
- When the stream cannot replay the missing range, it emits `StreamGapDetected`.

## 13. Subscription Persistence and Lifecycle `ledger.subscription-persistence-lifecycle`
### 13.2 Startup Sequence
- bus init → built-in capability declarations → built-in hooks → subsystems → plugins → MCP servers → external-API definitions → user-defined hooks → background workers → operational → `AppStarted`.
- Failed hook registration recorded as `HookSubscriptionRegistrationFailed`; startup does not abort.
### 13.3 Runtime Mutation
- `hooks.register { declaration }`, `hooks.unregister { subscription_id }`, `hooks.update { subscription_id, declaration_updates }`, `hooks.set_enabled { subscription_id, enabled, scope }` — `UserApproval` tier.
### 13.4 Shutdown
- Acknowledged critical ledger + audit-overlay records MUST be flushed synchronously before success.
- Runs in `running`/`cancelling` at restart transition to `failed` with `process_restart_orphan` unless `resume_on_restart: true`.
### 13.5 Restart Reconciliation
- User MUST see a surface for orphan runs with per-run resume-or-discard affordances.

## 14. Cancellation, Lifecycle, Restart `ledger.cancellation-lifecycle-restart`
### 14.1 Cancellation Recording
- `CancellationRequested`, `CancellationProgressing`, `CancellationEscalated`, `KillRequested`, `KillSucceeded`, `KillFailed`, `CleanupCompleted`, `CancellationCompleted`.
- `CancellationRequested` scope: `single_target`, `cascade`.
- `OrphanOutputDetected`: orphan output does NOT commit.
### 14.2 Intervention Recording
- `InterventionRecorded`, `TakeoverStarted`, `TakeoverEnded`.
- User actions during takeover record as first-class ledger entries attributed to the user, indistinguishable from agent-produced.
### 14.3 Restart Behavior
- Auto-resume of orphans is forbidden.

## 15. Settings `ledger.settings`
### 15.1 Configurable Dimensions
- Every mechanism here MUST be configurable.
- Hook: `hooks.timeout_default_ms`, `hooks.fail_direction_default`, `hooks.retry_per_error_class.<error_class>`, `hooks.priority_default`, `hooks.priority_max_user_authored`, `hooks.priority_min_user_authored`, `hooks.recursion_depth_limit`, `hooks.discovery_path`, `hooks.shell_script_allowlist`.
- Event bus: `events.buffer_size_per_subscriber`, `events.aggregation.<event_kind>.batch_ms`, `events.aggregation.<event_kind>.batch_max_count`, `events.aggregation.<event_kind>.suppress_threshold`, `events.resumption_window`, `events.frontend_bridge_max_event_kinds`, `events.debug_panel_ring_buffer_size`, `events.delivery_class.<event_kind>`.
- Ledger: `ledger.retention.public`, `ledger.retention.sensitive`, `ledger.retention.<entry_kind>`, `ledger.compaction_policy`, `ledger.compaction_schedule`, `ledger.export_default_sensitivity`, `ledger.sync_default_sensitivity`.
- Attribution: `attribution.token_source_preference`, `attribution.tokenizer_fallback_chain`, `attribution.cache_token_pricing.<provider>`, `attribution.cost_calculation_enabled`, `attribution.pricing_tier_user_managed`.
- Audit: `audit.enabled` (never globally disable for security-sensitive operations), `audit.path`, `audit.hash_algorithm`, `audit.tier_membership.<entry_kind>`.
- Streaming: `streaming.chunk_batch_ms`, `streaming.chunk_batch_max_bytes`, `streaming.partial_block_orphan_retention`, `streaming.frontend_render_pace_ms`.
- Lifecycle: `lifecycle.shutdown_safety_guard`, `lifecycle.background_worker_health_policy`, `lifecycle.orphan_run_reconciliation_default` (never `auto_resume`), `lifecycle.log_rotation_size`.
- Sensitivity: `events.sensitivity_export_default`, `events.sensitivity_clipboard_default`, `events.sensitivity_sync_default`, `events.sensitivity_telemetry_default`, `events.sensitivity_override.<capability_id>`.
### 15.3 Agent Exposure of Settings
- `audit.enabled` — `Hidden`; agents cannot disable audit.
- the active hook chain for the current event — `Hidden`.

## 16. Hash-Chained Audit Log `ledger.hash-chained-audit-log`
### 16.2 Required Fields
- `ledger_entry_id`, `timestamp`, `actor`, `action`, `target`, `canonical_redacted_entry_hash`, `prev_entry_hash`, `entry_hash`, `device_id`, `chain_id`.
- `action` verbs: `approve_tool_call`, `grant_lease`, `revoke_lease`, `accept_typed_confirmation`, `apply_system_change`, `rollback_system_change`, `delete_block`, `delete_artifact`, `register_capability`, `approve_source`, `deny_source`.
### 16.3 Per-Device Integrity
- The audit log MUST NEVER sync across devices.
### 16.4 Membership (baseline minimum)
- every `PolicyDecisionMade`; every `ApprovalGranted`/`ApprovalDenied`; every `LeaseGranted`/`LeaseRevoked`/`LeaseStale`/`LeaseNarrowed`; every `TypedConfirmationSatisfied`/`TypedConfirmationMismatched`; every `PolicyFloorViolated`; every `SourceRegistrationApproved`/`SourceRegistrationDenied`/`SourceRegistrationDeferred`; every credential/secret operation; every system-state mutation; every hard delete (`BlockHardDeleted`, `ArtifactHardDeleted`, `LeaseHardDeleted`, `CapabilityHardDeleted`); every `DeniedFloorOverridden`; every `RunCompletionForgeryAttempted`; every hook authority-class change.
### 16.5 Verification
- Any mismatch produces `AuditChainTamperDetected`; the device's sync stops until the user resolves.

## 17. Lifecycle Integration `ledger.lifecycle-integration`
### 17.1 Startup Phases
- infrastructure → registry → settings → hooks → background workers → UI → `AppStarted`.
### 17.3 Cancellation Token
- The interrupt is recorded as `InterventionRecorded`.
### 17.4 Shutdown
- Correctness does not depend on a shutdown timer.

## 18. Explicit Rejections `ledger.explicit-rejections`
- Parallel event bus, ledger, or hook system.
- Silent execution (invocation without `ToolCallProposed` + outcome entry).
- Silent hook decisions (decision without `HookDecisionRecorded`; timeout/error without `HookTimedOut`/`HookHandlerError`).
- Unkeyed model-dependent scalars.
- `Secret`-tagged payloads persisting to the durable ledger.
- Mutable ledger entries.
- Entries outside the closed catalogue plus registered `Custom`.
- Time-based hook firing (hooks fire only on event emission).
- Hard-coded hook timeouts.
- Hooks that bypass the event bus / mutate the ledger directly.
- Implicit ledger inference from events.
- Live events as durable history.
- Cross-device sync of the audit log.
- Silent retention or pruning.
- Canceled-but-still-running operations completing silently.
- Forgery of run completion.
- Hooks exceeding declared authority.
- Ad-hoc hook decision shapes.
- Silent batched approval.
- Bypassing the approval router for capability invocations.
- Per-capability custom approval logic in handlers.
- Event sequence numbers used across devices for global ordering.
- Per-tokenizer scalars on the block.
- Mutating entries for retroactive sensitivity reclassification (use sibling `SensitivityReclassified`).
- The bus claiming durability guarantees.
- `Substitute` combined with semantic target change.
- Pre-validation hooks running after validators.
- Ledger entries with omitted envelopes.
- Hook handlers mutating global state outside the typed action taxonomy.
- Shutdown grace periods as correctness.
- Ledger silently becoming the version graph.
- Duplicating per-capability data into ledger payloads.
- `Custom` event kinds for canonical concerns.
- Treating cancellation as a destructive operation.

## 19. Consequences for Later Specs `ledger.consequences-for-later-specs`
- Later specs MUST: emit events through the canonical bus with the standard envelope; record consequential facts via the canonical `LedgerEntry`; register extensibility points as `Hook` subscriptions; honor the typed `HookDecision` vocabulary; honor the priority convention; honor authority-class semantics; honor per-call attribution (`TokenUsageRecord` keyed by model identifier); honor sensitivity-aware persistence; honor the forgery guards; consume the closed `AppEvent` + `LedgerEntryKind` catalogues, declaring new kinds via `Custom { namespace, name, payload }`.
