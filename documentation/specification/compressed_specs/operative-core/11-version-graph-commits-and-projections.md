# Version Graph, Commits, and Projections

## 1. Chosen Model {version.chosen-model}
There MUST be one `VersionGraph` per conversation, a tree of `ContextVersion` nodes rooted at the empty initial state.
Every non-root version MUST be the child of exactly one parent and MUST carry one compact typed `VersionDiff`.
The materialized view (`context_view`) MUST hold the active version's fully resolved state for O(1) reads.
There MUST be no parallel checkpoint table, no `file_checkpoints` row type, no `SessionCheckpoint`/`ToolCallCheckpoint`/`MessageVersion`/`VersionSnapshot` type, no per-tool-call atomic version commit, no shadow-directory snapshot mechanism.
Projections MUST be rebuildable, non-authoritative read models.

## 2. Boundaries with Adjacent Layers {version.boundaries-with-adjacent-layers}
Token counts/costs/any model-dependent scalar MUST NOT be stored on `ContextVersion` rows.
Conversation versioning MUST operate at conversation-context level, not per-message.

## 3. `ContextVersion` {version.context-version}
### 3.1 Definition {version.context-version-definition}
A `ContextVersion` MUST be durable, immutable, identified; owned by exactly one `conversation_id`; have at most one `parent_version_id`; carry one immutable typed `VersionDiff`; carry one `VersionOpSummary`.
A cross-conversation reference MUST use a fork or block-level reference, never a shared `version_id`.
A `ContextVersion` MUST NOT be a copy of block content, a UI element, or mutable.

### 3.2 Required Fields {version.context-version-required-fields}
Minimum: `version_id`, `conversation_id`, `parent_version_id`, `merge_source_version_ids`, `committed_at`, `committed_by`, `op_summary`, `diff`, `label`, `bookmarked`, `snapshot_refs`, `version_schema_version`, `diff_hash`, `expected_view_hash`.
`committed_by` variants: `UserMessage`, `CapabilityCommit`, `RouterEmission`, `InspectorApply`, `WorkflowNode`, `Import`, `Consolidation`, `Subsystem`.
`snapshot_refs` keys: `registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id` (+ registered extension keys); unused entries absent rather than null-padded.
Immutable for lifetime: `diff`, `snapshot_refs`, `committed_at`, `committed_by`, `op_summary`, `version_id`, `parent_version_id`, `merge_source_version_ids`, `conversation_id`, `version_schema_version`, `diff_hash`.
Mutable only through explicit operations: `label`, `bookmarked`, `expected_view_hash`; mutations MUST emit typed events + ledger entries.

### 3.3 Identity {version.context-version-identity}
A `version_id` MUST be globally unique within the installation, assigned at commit, never reused/reassigned/mutated.
Deduplication of equal-content versions MUST NOT be attempted.

## 4. `VersionDiff` {version.version-diff}
### 4.1 Required Shape {version.version-diff-required-shape}
Compact; only changes recorded. Closed canonical field set: `added`, `removed`, `lifecycle_changes`, `pin_changes`, `position_changes`, `metadata_changes`, `hard_deletes`, `derived_state_changes`.
`BlockLifecycle` values: `Raw`, `Active`, `Masked`, `Dropped`, `Recovered`.
`PinState` values: `Unpinned`, `Pinned`, `Protected`.
The diff MUST be the net effect of all `ContextOp`s accumulated in `pending_ops`.

### 4.2 Storage and Serialisation {version.version-diff-storage}
A `VersionDiff` MUST be immutable for lifetime; corrections MUST commit a new sibling version with `op_summary: Correction`; the prior MUST remain with its original diff.

### 4.3 Canonical `MetadataChange` Catalogue {version.metadata-change-catalogue}
Closed set: `SensitivityOverrideApplied`, `DescriptionRegenerated`, `ScopePromotionAdopted`, `MaterializationRecorded`, `Custom { namespace, name, payload }`.

### 4.4 Per-Entity Derived-State Change Catalogue {version.derived-state-change-catalogue}
Closed set: `ArtifactReviewState`, `ArtifactValidationState`, `ArtifactLifecycle`, `ClaimStatus`, `TaskRevisionAdvanced`, `IntentThreadContinuitySummaryRecorded`, `Custom { namespace, name, payload }`.
A derived-state change MUST be recorded on commit only when it derives deterministically from the commit's contents; pure read-time recomputation MUST NOT record on a version.

### 4.5 Hashing {version.diff-hash}
`diff_hash` MUST be SHA-256 over `CanonicalVersionDiffEncoding` + `version_schema_version` discriminator, not physical storage representation.
Order-insensitive diff collections MUST be sorted by stable key before hashing.
A stored diff whose hash mismatches recomputation MUST trigger `MaterializedViewIntegrityViolated` and force a rebuild.
`diff_hash` MUST be `NOT NULL` and immutable.

## 5. `VersionOpSummary` and the Commit Boundary Set {version.version-op-summary-commit-boundary-set}
### 5.1 Definition {version.commit-boundary-definition}
Every commit MUST fire from a typed trigger producing a `VersionOpSummary`; every commit boundary MUST correspond to a `BlockCommitted` boundary and a `VersionCommitted` ledger entry.

### 5.2 Closed Canonical Catalogue {version.version-op-summary-catalogue}
Catalogue: `UserMessage`, `AgentTurn`, `EditMessage`, `Retry`, `ContextEdit`, `ContextEditWithLabel`, `CapabilityCommit`, `WorkflowNodeComplete`, `Consolidation`, `RouterEmission`, `ArtifactVersion`, `TaskRevision`, `ClaimPublication`, `EvidenceLink`, `ValidationRun`, `Import`, `Export`, `ExternalEdit`, `Correction`, `Recovery`, `Subsystem`, `Automation`, `Custom { namespace, name }`.
Every commit MUST declare exactly one `op_summary`; no commit may have an unparseable summary.

### 5.3 Boundary Composition {version.boundary-composition}
Canonical rule: one boundary, one commit, one diff per boundary.

### 5.4 Boundary Discipline Rules {version.boundary-discipline-rules}
A boundary MUST fire only when the producing operation reached a canonical commit point; partial progress MUST live in `pending_ops` + `Event`s, never as a `ContextVersion`.
A boundary MUST NOT fire mid-stream.
A boundary producing no diff MUST NOT fire; exception: `Recovery` + `Correction` MUST always commit.
A boundary that would violate the block commit validator MUST NOT fire.
A boundary MUST fire synchronously with the producing operation's commit point.

## 6. Pending-Operations Buffer {version.pending-operations-buffer}
### 6.1 Definition {version.pending-buffer-definition}
`ConversationVersionState { conversation_id, current_version_id, pending_ops, updated_at }`.
The buffer MUST be durable, survive restart, and MUST NOT be a transient in-memory queue.

### 6.2 Buffer Lifecycle {version.pending-buffer-lifecycle}
States: Empty, Accumulating, In-session undo, Commit, Discard.
On commit the runtime MUST compute the net diff against the pre-buffer view, create the new `ContextVersion`, clear the buffer, advance `current_version_id`, and emit `PendingOpApplied` + `VersionCommitted`.

### 6.3 In-Session Undo {version.in-session-undo}
`undo_pending` MUST require non-empty `pending_ops`, pop the most recent `ContextOp`, re-derive the view, and emit `PendingOpUndone`; the popped operation MUST NOT be recorded as committed history.

### 6.4 Buffer Discard {version.buffer-discard}
`discard_pending` MUST require non-empty `pending_ops`, drop every operation, re-derive the view to `current_version_id`, and emit `PendingOpsDiscarded`.

### 6.6 Buffer Storage {version.buffer-storage}
The buffer MUST be stored on `ConversationVersionState` and survive restart.
If buffer contents are inconsistent with substrate the runtime MUST emit `PendingOpsInconsistencyDetected` and discard the buffer.

### 6.7 Concurrent Modifications {version.concurrent-modifications}
Operations MUST be serialised at the versioning operation boundary into a single ordered sequence.

## 7. Materialized View (`context_view`) {version.materialized-view-context-view}
### 7.1 Definition {version.materialized-view-definition}
`context_view` MUST be rebuildable from the version graph + block pool + relevant durable substrates and MUST hold no facts they don't.

### 7.2 Required Shape {version.materialized-view-required-shape}
`ContextViewRow { conversation_id, block_id, position, lifecycle_state, pin_state }`.
For each `(conversation_id, block_id)` active at `current_version_id` there MUST be exactly one row.
`Dropped` blocks MUST be retained as rows; downstream layers MUST filter `Dropped` out of context assembly + standard retrieval.
Only `lifecycle_state` + `pin_state` MUST be stored on the row.

### 7.3 Properties {version.materialized-view-properties}
Every `ContextOp` MUST update `context_view` immediately, before commit.
The view MUST be rebuildable from durable substrate; no durable fact unique to the view is permitted.

### 7.6 Integrity Verification {version.expected-view-hash}
On `expected_view_hash` mismatch the runtime MUST emit `MaterializedViewIntegrityViolated`, mark the view `degraded`, rebuild from the action log, then recompute + record a corrected hash.
The canonical hash MUST be SHA-256 over a `CanonicalEncoding` of the row set sorted by `(block_id)`, storage-independent.

## 8. Version Switching {version.version-switching}
### 8.1 Definition {version.version-switching-definition}
Switching MUST be non-destructive; the prior current version MUST remain reachable.

### 8.2 The Algorithm {version.switch-algorithm}
`switch_to_version` MUST: (1) validate target+current exist and share root; (2) find the tree path; (3) discard pending operations (no implicit commit on switch); (4) apply reverse diffs up; (5) apply forward diffs down; (6) verify integrity against `expected_view_hash` when present; (7) advance `current_version_id`; (8) keep buffer empty; (9) emit `VersionSwitched`.

### 8.4 Hard Delete Handling {version.switch-hard-delete}
`hard_deletes` MUST NOT be reversible by switch; affected blocks MUST remain tombstones; switching before a `hard_delete` MUST NOT restore the deleted block.

### 8.5 Switching from Buffered State {version.switch-buffered-state}
With non-empty `pending_ops`, switching MUST follow `versioning.switch_with_pending_behaviour`: `Discard`, `Commit`, or `AskUser`.

## 9. Branching and Forking {version.branching-forking}
### 9.1 Branching {version.branching}
A commit after switching to a non-leaf MUST become a child of the switched-to version (sibling of the prior leaf); both branches MUST remain permanent + switchable.
A `BranchCreated` event MUST fire whenever a commit creates a new branch.

### 9.2 Branch Merge Provenance {version.branch-merge-provenance}
The version graph MUST remain a single-parent tree; combining branches MUST produce a normal child carrying `merge_source_version_ids` as provenance references, not topology edges.

### 9.3 Forking {version.forking}
A fork MUST create a new `conversation_id`, a new root `ContextVersion` with `parent_version_id = null` and an `Import` op_summary referencing the source, and record `ConversationForked`.
Source `version_id`s MUST NOT transfer.
Blocks whose scope/sensitivity/policy prevent visibility MUST be omitted with a typed `ForkOmitted { source_block_id, reason: ScopeRestriction | SensitivityRestriction | PolicyDenial }` placeholder; sharing restricted blocks by default is invalid.

## 10. Per-Version Derived State Maps {version.per-version-derived-state-maps}
### 10.1 Definition {version.derived-state-definition}
Per-`ContextVersion` derived state (`BlockLifecycle`, `PinState`, `ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`, `TaskRevision`) MUST be computed from the version-graph action log over block pool + entity records.

### 10.2 Block Lifecycle Derivation {version.block-lifecycle-derivation}
Per-version block lifecycle MUST be derived deterministically from initial state + all `lifecycle_changes` along the path; the materialized view stores the result, the action log is substrate.

### 10.3 Pin State Derivation {version.pin-state-derivation}
`PinState` MUST be derived from initial state + all `pin_changes` along the path.

### 10.4 Artifact-Level Derived State {version.artifact-level-derived-state}
`ArtifactLifecycle`: `Draft`, `Active`, `Validated`, `Superseded`, `Archived`, `Discarded`.
`ReviewState`: `Unreviewed`, `AcceptedByUser`, `AcceptedByAgent`, `Rejected`, `NeedsRevision`.
`ValidationState`: `NotValidated`, `PendingValidation`, `Passed`, `Failed`, `NeedsReview`.

### 10.5 Claim Status Derivation {version.claim-status-derivation}
`ClaimStatus`: `Candidate`, `Supported`, `Contradicted`, `Unresolved`, `Superseded`, `Withdrawn`.
A `ClaimStatus` change MUST be recorded in the committing version's `derived_state_changes` when the substrate changes; pure read-time recomputation MUST NOT record on a version.

### 10.6 Task Revision Derivation {version.task-revision-derivation}
A task's effective revision MUST be the latest committed `TaskRevisionAdvanced` change on the path from creation to current.

### 10.7 Custom Derived-State Extension {version.custom-derived-state-extension}
Registered kinds MUST be registered proposal-first, declaring derivation source, derivation rule, canonical event kind, and rendering hint, and participate via `derived_state_changes::Custom`.

## 11. `ContextOp` — Closed Canonical Operation Vocabulary {version.context-op-closed-canonical-operation-vocabulary}
### 11.1 Definition {version.context-op-definition}
Operations MUST accumulate in `pending_ops` and merge into one `VersionDiff` at the next commit boundary.

### 11.2 Closed Catalogue {version.context-op-catalogue}
`ContextOp`: `Mask`, `Unmask`, `Drop`, `Recover`, `Pin`, `Unpin`, `Protect`, `Unprotect`, `Reorder`, `AddToContext`, `RemoveFromContext`, `Group`, `Ungroup`, `AddToGroup`, `RemoveFromGroup`, `EditBlock`, `PromoteScope`, `ApplySensitivityOverride`, `HardDeleteBlock`, `Custom { namespace, name, payload }`.

### 11.3 Operation Semantics {version.context-op-semantics}
`AddToGroup`/`RemoveFromGroup` MUST produce a new sibling `Composed` block.
`EditBlock` MUST create a new sibling block; the old block stays in the pool.
`HardDeleteBlock` MUST require typed-confirmation when the block is referenced and MUST produce a tombstone.

### 11.4 Operation Inverses {version.context-op-inverses}
Inverses: `Mask↔Unmask`, `Drop↔Recover`, `Pin↔Unpin`, `Protect↔Unprotect`, `AddToContext↔RemoveFromContext`, `Group↔Ungroup`, `AddToGroup↔RemoveFromGroup`.
`ApplySensitivityOverride` lower-back MUST be permitted only when the user explicitly authored the raise.
`HardDeleteBlock` MUST have no post-commit inverse.

### 11.5 Operation Side Effects on Block Pool {version.context-op-side-effects}
`Group`, `AddToGroup`, `RemoveFromGroup`, `EditBlock`, `PromoteScope` MUST create new sibling blocks; if validation fails at commit, the entire commit MUST fail and `pending_ops` MUST be preserved.

### 11.6 Operation Merge Rules {version.context-op-merge-rules}
On same `block_id`: later lifecycle/pin operation MUST win for final state; most recent position assignment MUST win; `HardDeleteBlock` MUST be terminal (subsequent operations are typed errors).
The diff MUST reflect only net effect, not intermediate states.

### 11.7 Authority and Authorisation {version.context-op-authority}
Every agent-invoked `ContextOp` MUST flow through a registered capability + the File 04 pipeline; agents MUST NOT mutate version history through side channels.
`HardDeleteBlock` MUST have `permission_floor: Denied` + typed-confirmation.
`ApplySensitivityOverride` that lowers sensitivity MUST have `permission_floor: Denied` + typed-confirmation.
`PromoteScope { target_scope: global }` MUST be `UserApproval` tier or stricter.

## 12. Sibling-Block Versioning over the Block Pool {version.sibling-block-versioning-over-block-pool}
### 12.1 Definition {version.sibling-block-versioning-definition}
Observable content changes MUST produce new immutable blocks linked by `supersedes`, with the active reference in the materialized view updated; the prior block MUST stay in the pool.

### 12.2 File Edits {version.file-edits}
A file edit MUST create a new sibling block with fresh `block_id`, same `parent_block_id`, a `supersedes` edge, fresh `content_hash`, fresh `created_at`, edit-source `producer`.

### 12.3 Message Edits {version.message-edits}
A message edit MUST create a new sibling `MessageUser` block and commit an `EditMessage` version recording the swap; orphan downstream MUST be non-destructively preserved.

### 12.4 Knowledge-Entry Edits {version.knowledge-entry-edits}
An agent-proposed edit that the user rejects MUST leave the new sibling in the pool with `current_version_block_id` staying on the prior entry block.

### 12.5 Validator and Adapter Updates {version.validator-adapter-updates}
`Validator`-kind + `Adapter`-kind blocks MUST follow the sibling-versioning pattern; execution MUST read the active sibling at the conversation's `current_version_id`.

## 13. Artifact Version Chains {version.artifact-version-chains}
### 13.1 Definition {version.artifact-version-chain-definition}
A chain MUST share a stable `artifact_id`, carry a typed `ArtifactVersion` metadata record per version (`version_id`, `artifact_id`, `version_number`, `parent_version_id`, `derivation_summary`, `produced_by_run_id`, `produced_by_node_id`, `produced_by_capability_id`, `materialized_paths`, `validation_report_id`, `metadata`), and a `current_version_block_id` pointer.

### 13.3 Per-`ContextVersion` Resolution {version.artifact-per-context-version-resolution}
Branch-aware reads MUST walk back from `current_version_id` to the diff containing the artifact's most recent version-commit; if none is found, resolution MUST return `None`.

### 13.5 Materialization Across Versions {version.materialization-across-versions}
On version switch, disk state MUST update to match the active version's `materialized_paths`.

## 14. Snapshots {version.snapshots}
### 14.1 Definition {version.snapshot-definition}
A snapshot MUST be a typed durable addressable reference to substrate state at a durable anchor, NOT a stored copy of substrate content.
Snapshot ids MUST be unique within the installation and never reassigned.

### 14.2 Closed Canonical Snapshot Catalogue {version.closed-canonical-snapshot-catalogue}
Each `<kind>_snapshot_id`: `registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id`, `<custom>_snapshot_id`.

### 14.3 Snapshot Anchoring {version.snapshot-anchoring}
Resolution MUST walk substrate events up to but not beyond the anchor.

### 14.4 Snapshot Resolution {version.snapshot-resolution}
`resolve_snapshot` MUST be deterministic given the durable event log; on an unresolvable snapshot the resolver MUST return a typed error and MUST NEVER silently fall back to current state.

## 15. Replay Semantics {version.replay-semantics}
### 15.1 Definition {version.replay-definition}
Three closed canonical modes: `Inspect`, `SimulateDeterministic`, `FullRerun`.

### 15.2 `Inspect` Mode {version.replay-inspect}
`Inspect` MUST be read-only with no execution and no side effects, deterministic given durable substrate.

### 15.3 `SimulateDeterministic` Mode {version.replay-simulate}
Only `deterministic_replayable` (and revalidated `snapshot_replayable`) capabilities MUST be re-executed; `effect_replayable_with_policy`/`not_replayable` MUST NOT be re-executed; the new run record MUST reference `replay_source_run_id`.

### 15.4 `FullRerun` Mode {version.replay-full-rerun}
`FullRerun` side effects MUST happen per the standard call pipeline including policy approval.

### 15.5 Replay Identity {version.replay-identity}
Every replay invocation MUST carry a `replay_id`, record `replay_source_run_id`/`replay_mode`/`replay_initiated_at`/`replay_initiated_by`, and emit `ReplayStarted` + `ReplayCompleted` ledger entries.

### 15.6 Replay-Capability Surface {version.replay-capability-surface}
`replay.inspect` MUST be `ReadOnly` tier; `replay.simulate_deterministic` MUST be `WorkspaceWrite` tier; `replay.full_rerun` MUST be `UserApproval` tier with typed-confirmation.

### 15.7 Boundary {version.replay-boundary}
No part of replay MAY alter the durable substrates of the source run.

## 16. Version-Graph-Backed Projections {version.version-graph-backed-projections}
### 16.2 Required Contract {version.projection-required-contract}
Every projection MUST declare its substrate, declare its rebuild trigger (`event-driven`, `on-demand`, or configured maintenance), be rebuildable from substrate, emit `<Projection>Rebuilt` events, tolerate corruption (rebuild not data loss), and carry a `version` discriminator when schema may evolve.

### 16.3 Canonical Projections {version.canonical-projections}
`context_view`; per-`ContextVersion` lifecycle/pin maps; artifact-entity `current_version_block_id` resolution; per-version derived state; snapshot resolutions; version-timeline + comparison-diff views.

### 16.4 Custom Projections {version.custom-projections}
Registered custom projections MUST be registered proposal-first, declaring substrate, rebuild triggers, canonical rebuild event kinds, and rendering hints.

### 16.5 Boundary {version.projection-boundary}
The version graph MUST NOT itself be a projection; it is durable state.

## 17. Service Surface {version.service-surface}
### 17.1 Definition {version.service-surface-definition}
Every read/mutation MUST cross this surface, emit File 10 events/ledger entries where consequential, and respect File 06 policy where applicable.

### 17.4 Label and Bookmark Operations {version.label-bookmark-operations}
`label_version` MUST emit `VersionLabelled`; `bookmark_version` MUST emit `VersionBookmarked` and exempt the version from retention-policy pruning.

### 17.5 Service Composition {version.service-composition}
Every operation MUST emit typed events, record consequential operations as ledger entries, respect capability policy, and return `Result<T, AppError>`.

## 18. Persistence Contract {version.persistence-contract}
### 18.1 What Is Durably Stored {version.what-is-durably-stored}
MUST durably store: every `ContextVersion` row with required fields (`version_id`, `conversation_id`, `parent_version_id`, `merge_source_version_ids` when present, `committed_at`, `committed_by`, `op_summary`, `diff`, `label`, `bookmarked`, `snapshot_refs`, `version_schema_version`, `diff_hash`, `expected_view_hash` when present); the materialized view; `ConversationVersionState`; labels + bookmarks.

### 18.2 What Is Computed {version.what-is-computed}
Per-version `ArtifactLifecycle`/`ReviewState`/`ValidationState`/`ClaimStatus`/`TaskRevision`, view rebuilds, snapshot resolutions, version-tree projection, per-tokenizer token counts MUST be computed.

### 18.3 Reconstruction Across Restart {version.reconstruction-across-restart}
On restart the version graph, materialized views, and `ConversationVersionState` MUST reload; a corrupted view MUST rebuild; uncommitted `pending_ops` MUST survive.

### 18.4 Reconstruction Across Retry, Edit, Reroute, Branch, Child-Run {version.reconstruction-across-retry}
Retry/reroute/edit/branch MUST share the block pool; isolated child runs MUST NOT commit a version themselves (parent's boundary commits their output).

### 18.5 Reconstruction Across Sync {version.reconstruction-across-sync}
Concurrent commits on two devices MUST produce sibling branches with no last-write-wins.

## 19. Cross-Device Sync and Conflict Resolution {version.cross-device-sync-conflict-resolution}
### 19.1 Definition {version.sync-definition}
Sync MUST be version-tree-aware: no last-write-wins, no implicit merge, no squashing.

### 19.2 Sync Boundary {version.sync-boundary}
Replicated state MUST preserve `ContextVersion` identity, parentage, merge-source references, diffs, tombstones, labels, bookmarks, snapshot references, and block identity + content-addressing semantics.

### 19.3 Conflict Resolution {version.conflict-resolution}
Canonical rule: both branches MUST survive; neither overwrites; a `SyncVersionDiverged` event MUST fire.

### 19.4 Per-Device Materialized-View Pointer {version.per-device-pointer}
Each device MUST maintain its own `current_version_id`+`pending_ops`; a sync pull MUST NOT change the local pointer automatically.

### 19.5 External Content Sync {version.external-content-sync}
Blobs MUST fetch on demand at first access; a blob fetch failure MUST NOT break the conversation.

### 19.6 Sync Events {version.sync-events}
`SyncPulled`, `SyncPushed`, `SyncVersionDiverged`, `SyncBlobFetched`, `SyncFailed`.

## 20. Garbage Collection and Pruning {version.garbage-collection-pruning}
### 20.1 Definition {version.gc-definition}
GC MUST be non-destructive by default; bookmarked versions MUST be exempt.
Canonical mechanisms: `tombstone_version`, `compact_version_range`, `hard_delete_version_payload`, retention-policy-driven cleanup; `delete_version` MUST NOT be a primitive.

### 20.2 `tombstone_version` {version.tombstone-version}
MUST require the version to exist and not be `current_version_id`; MUST require unbookmarking first; MUST require `permission_floor: Denied`-tier typed-confirmation when the version has descendants; MUST preserve topology identity (no descendant reparenting); MUST emit `VersionTombstoned`.
MUST either preserve the original diff with redaction or replace it with a reconstruction-preserving compacted summary; if neither is safe it MUST fail with `TombstoneReconstructionUnsafe`.

### 20.3 Tombstones {version.tombstones}
A tombstone MUST retain `version_id`, `conversation_id`, `deleted_at`, `deleted_by`, `deletion_reason` (`UserRequested`, `RetentionPolicy`, `MaintenanceCleanup`, `Custom { code, description }`), `committed_at`, `op_summary`, `label`.

### 20.4 `compact_version_range` {version.compact-version-range}
MUST apply only to linear segments; a range including a branching point MUST fail with `CompactionBranchingPointInRange`.

### 20.5 `hard_delete_version_payload` {version.hard-delete-version-payload}
MUST require typed confirmation + closure checks; MUST record a typed provenance gap on reconstructability loss; MUST NEVER be invoked silently by retention policy.

### 20.6 Retention Policies {version.retention-policies}
`RetentionPolicy`: `KeepAll`, `KeepRecentN { n, exempt_bookmarks }`, `KeepWithin { duration, exempt_bookmarks }`, `Custom { policy_id, params }`.
Bookmarked + labelled versions MUST always be exempt.
No time-based pruning MUST fire without explicit user/selected-profile opt-in.
Each retention invocation MUST be durably recorded (`RetentionPolicyApplied`).

### 20.7 Hard-Delete Reclamation {version.hard-delete-reclamation}
Blocks MUST become eligible for cleanup only when no version in the tree (including tombstones) references them.

## 21. Events {version.events}
### 21.1 Canonical Event Vocabulary {version.event-vocabulary}
Every version-graph operation MUST emit typed events through the canonical bus; each is also a `LedgerEntryKind`.
Events: `PendingOpApplied`, `PendingOpUndone`, `PendingOpsDiscarded`, `VersionCommitted`, `VersionSwitched`, `BranchCreated`, `ConversationForked`, `VersionLabelled`, `VersionUnlabelled`, `VersionBookmarked`, `VersionUnbookmarked`, `MaterializedViewRebuilt` (`RebuildSource`: `IntegrityViolation`, `ManualRequest`, `Restart`, `SwitchPathTooLong`, `CacheRefresh`), `MaterializedViewIntegrityViolated`, `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted`, `RetentionPolicyApplied`, `PendingOpsInconsistencyDetected`.

### 21.2 Event Sensitivity {version.event-sensitivity}
Raw secret payloads MUST NEVER appear in version-graph event payloads.

### 21.3 Hookable Events {version.hookable-events}
Blocking hooks MAY subscribe to `VersionCommitted`, `BranchCreated`, `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted`; decisions MUST follow `Continue`/`Substitute`/`Block`/`RedirectSuggestion`.

## 22. Settings {version.settings}
### 22.1 Configurable Dimensions {version.configurable-dimensions}
Buffer: `versioning.in_session_redo_enabled`, `versioning.switch_with_pending_behaviour`, `versioning.pending_buffer_max_size`.
Materialized-view: `versioning.view_integrity_check_strictness`, `versioning.strategic_cache_policy`, `versioning.strategic_cache_max_count`.
Retention: `versioning.retention_policy`, `versioning.retention_apply_trigger`, `versioning.cleanup_confirmation_threshold`.
Branching: `versioning.allow_branch_from_non_leaf`, `versioning.label_required_on_branch`.
Snapshot: `versioning.snapshot_resolution_cache_enabled`, `versioning.snapshot_resolution_failure_policy`.
Replay: `versioning.replay_default_mode`, `versioning.replay_full_rerun_confirmation`.
Sync: `versioning.sync_divergence_notify`, `versioning.sync_auto_switch_to_remote`.
Agent-exposure: `versioning.version_tree_visible_to_agent`, `versioning.commit_boundary_set_visible_to_agent`, `versioning.context_op_vocabulary_visible_to_agent`, `versioning.history_query_capabilities_default_zone`.

### 22.2 Settings-Key Convention {version.settings-key-convention}
Keys MUST follow `versioning.<dimension>`.

## 23. Explicit Rejections {version.explicit-rejections}
- Parallel checkpoint systems (`file_checkpoints`, `SessionCheckpoint`/`FileCheckpoint`/`ToolCallCheckpoint`, shadow-directory, per-tool-call atomic checkpoint)
- `MessageVersion` rows
- `VersionSnapshot` table separate from version diffs
- in-place mutation of `ContextVersion` fields
- `pending_ops` buffer as transient in-memory queue
- implicit commit on switch
- per-operation atomic version commits
- branching that overwrites the prior branch
- last-write-wins for sync conflicts
- squashing or implicit merge of sibling branches at sync
- snapshot as a stored copy of substrate content
- token counts or costs stored on `ContextVersion` rows
- materialized view as the source of truth
- time-based version pruning by default
- implicit hard-delete of versions
- descendant reparenting during cleanup
- compaction across branch points
- sharing restricted fork blocks by default
- per-surface version trees
- per-message version structs
- `updated_at` on block rows
- time-based mask/drop/lifecycle transitions
- treating `ContextVersion` and `Block` as the same primitive
- treating `Projection` as authoritative for any durable fact
- snapshot-as-full-model-request-audit
- `expected_view_hash` as the source of truth for view content
- operation sequence as reconstruction source
- forging a `VersionCommitted` ledger entry without producing a version row
- storing per-version aggregate metrics
- version-graph events emitted outside the canonical bus
- diffs that reference blocks not in the pool
- snapshot ids that lack global uniqueness or get reassigned
- sync of `dag_node_output_cache`, `rate_limit_state`, or audit-log hash chain

## 24. Consequences for Later Specs {version.consequences-for-later-specs}
- Later specs MUST NOT introduce parallel history/checkpoint/rollback/undo/fork/versioning primitives.
- Storage MUST store required `ContextVersion` fields, `ConversationVersionState`, active `context_view`, labels, bookmarks, tombstones, compacted segments, payload-deletion provenance gaps, hashes, snapshot references.
- Sync/import/export MUST preserve version topology, parent links, `merge_source_version_ids`, tombstones, compacted segments, block identity, per-device active pointers; last-write-wins remains invalid.
- Context assembly + compaction MUST commit explicit `ContextEdit`/`Consolidation`/tombstone/range-compaction operations and preserve evidence/provenance closure.
- Retrieval/memory/knowledge/artifact/claim/validation/workspace-mirror/UI-history surfaces MUST be projections or sibling-block chains over this substrate, not separate history stores.
- Model/provider/pricing/settings/world/routing/policy/perception/evaluation/replay specs MUST consume snapshot identities + the File 10 ledger.
- Extensions/plugins/MCP/workflows/automation/QC/work surfaces MUST register custom op summaries/context ops/metadata changes/derived-state changes/snapshot kinds/projections proposal-first and MUST NOT bypass the versioning operation surface or File 06 policy.
- UI specs MUST render timelines/comparison views/history/rollback/inspectors/undo-redo-restore-revert/fork views from the canonical data contracts here.
