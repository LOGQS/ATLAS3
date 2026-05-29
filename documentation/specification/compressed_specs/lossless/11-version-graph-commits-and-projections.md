> Lossless render of canonical/11-version-graph-commits-and-projections.md — original 160423 chars

# Version Graph, Commits, and Projections

## Status
Canonical.

## Scope
Defines: `ContextVersion` (durable per-conversation version-graph node, required fields, identity); `VersionDiff` (typed compact difference on each non-root version, closed canonical field set, hashing rule protecting materialized-view integrity); `VersionOpSummary` (closed canonical enum of commit-trigger kinds + registered-extension mechanism); closed canonical commit-boundary set (expanding the minimum in [`run.version-commits`], aligning with [`block.commit-boundary-set`]); pending-operations buffer (`pending_ops` on `ConversationVersionState`) — accumulation, in-session undo, discard, boundary-fires-commit rule; `ContextOp` (closed canonical operation vocabulary applied against materialized view by user/agent/hooks/subsystems; per-op contribution to `VersionDiff`); materialized view (`context_view`) — canonical read-optimised projection of active version's view-state over block pool; version switching (deterministic path-walk, reverse-and-forward diff application, strategic-cache-node optimisation); branching+forking (sibling branches as non-destructive divergence primitive, fork-from-version, named cross-conversation fork); per-version derived state maps — `BlockLifecycle` [`block.block-lifecycle-non-destructive-edits`], `PinState` [same], `ArtifactLifecycle`/`ReviewState`/`ValidationState` [`artifact.artifact-lifecycle-states`], `ClaimStatus` [`artifact.claim-status`] all derived from version-graph action log; sibling-block versioning over block pool (interaction with [`block.edit-semantics`] + `supersedes` edge); artifact version chains as specialisation of sibling-block versioning incl. entity-record `current_version_block_id` pointer [`artifact.artifact`] + per-`ContextVersion` resolution; `Snapshot` (closed canonical typed-reference vocabulary the ledger/runs/capability invocations/replay use to address registry/settings/world/policy/pricing/routing state at a durable anchor); version-graph-backed projections (concrete projection contract for materialized view, derived state maps, snapshot views, version-history surfaces, inheriting [`core.projection`]); replay semantics (three closed modes `Inspect`/`SimulateDeterministic`/`FullRerun` per [`ledger.replay-semantics`] + version-graph data they require); forensic reconstruction ("what did the model see at moment X" + closed canonical comparison-and-diff operations); canonical undo/redo/restore/revert operation set expressed through version-graph; persistence contract (durable / computed / reconstructable + deterministic reconstruction across restart/retry/edit/reroute/branch/child-run); cross-device sync contract (version-tree-aware merge, no last-write-wins, both-children-survive sibling resolution, per-device materialized-view pointer); garbage collection + pruning (closed canonical retention policy set, typed tombstone/compaction/payload-deletion ops, user-controlled storage reclamation from [`core.non-destructive-by-default`]); canonical version-graph event vocabulary on unified bus [`ledger.event-stream`] — `PendingOpApplied`, `VersionCommitted`, `VersionSwitched`, `BranchCreated`, `VersionLabelled`, `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted`, `MaterializedViewRebuilt`, `MaterializedViewIntegrityViolated`; settings dimensions with agent-exposure rules [`policy.agent-exposure-policy-settings`]; closed set of explicit rejections; canonical contract every later spec consumes when producing a versioned artefact / declaring a snapshot identity / building a derived projection / querying history / replaying an execution.

Does not define: `Block` model / `BlockKind` catalogue / `BlockContent` variants / block commit validator / sibling-block edit semantics / hard-delete tombstones (File 08 — consumed here); `Artifact` entity record field set / `ArtifactKind` catalogue / materialization policy / tombstone shape / artifact-specific behaviours (File 09 — this file specifies how artifact versions participate); run lifecycle / capability-call pipeline / retry-reroute-branch at run level / cancellation / pending-ops promotion to artifacts / completion-verification (File 04 — this file specifies which run-level transitions correspond to commit boundaries); policy evaluation algorithm / approval flows / lease lifecycle / contradiction-checking (File 06 — this file specifies lease state is a projection over policy events [`policy.persistence`]); tool-surface composition / surface zoning (File 07 — tool surface is a projection [`surface.chosen-model`], registry snapshots address registry state at a durable anchor); `ExecutionLedger` row format / `EventEnvelope` field set / live-bus delivery contract (File 10 — this file specifies which version-graph events flow through the bus + which ledger entry kinds record them); storage on-disk layout / per-table schema / replication / projection-store realisation / indexing strategy (future Storage spec); cross-device sync transport / libsql embedded-replica mechanics / conflict-detection pipeline / import-export bundle format (future Sync spec — version-tree-aware merge is canonical conflict-resolution semantics); retrieval/indexing/KB/RAG/hybrid-search (File 12 — retrieval indexes are projections rebuildable from durable substrates); context-assembly / compaction algorithms / token-budget / per-policy block selection (File 13 — materialized view is canonical context-assembly input + typed boundary at which compaction passes commit); memory promotion/salience/recall/decay (File 14 — memory entries consolidating prior blocks linked via `consolidates` edges from [`block.canonical-edge-kinds`], participate in version graph as ordinary blocks); model strategy/provider routing/rate-limit reconciliation/provider-health (Files 16, 17); workspace materialization mechanics / materialized-path resolution / disk→block sync / workspace-tree management (future Workspaces spec — disk state is a projection of active version's view per [`artifact.disk-entity-sync`]); security primitives/sandbox isolation/credential management (future specs); UI rendering for version-timeline/tree view/comparison-board/history-panel/inspector previews/undo affordances/accessibility (future UI specs — this file specifies canonical data contracts those surfaces consume); specific evaluation-suite/benchmark schemas (future Evaluation spec — consumes the replay surface here).

## Source Resolution
Resolves undo/redo, branches, commits, snapshots, forks, compaction, tombstoning, sync, materialized views into one boundary: version graph + derived state projections. Resolved: a ContextVersion tree records accepted state transitions over a shared block pool (versions don't copy conversations wholesale); commits capture turn/operation-boundary net diffs after pending operations accepted; active view state, ordering, lifecycle, pins, scopes, materializations derived from versioned actions not mutable block edits; branching+forking non-destructive, merging+conflict handling explicit; tombstoning/compaction/deletion preserve reconstructability unless user explicitly accepts a typed provenance gap; sync keeps divergent branches visible rather than silent last-write-wins.

## 1. Chosen Model `version.chosen-model`
One `VersionGraph` per conversation; uses File 01 `Projection` primitive for read-optimised derived views over durable state. Tree of `ContextVersion` nodes rooted at conversation's empty initial state; every non-root is child of exactly one parent + carries one compact typed `VersionDiff` describing net change from that parent; topology accumulates as commit boundaries fire; materialized view (`context_view`) holds active version's fully resolved state for O(1) reads; switching to another version walks path between current+target applying reverse-and-forward diffs to rebuild in O(path length); branching = new commit after switching to a non-leaf version (new commit becomes sibling of prior leaf, both branches permanent + switchable).

Single mechanism handles every surface that felt like a separate "history" feature: conversation retry + message edit are commit boundaries (`Retry`, `EditMessage`) producing new branches when prior leaf wasn't latest; inspector operations (mask/drop/pin/unpin/reorder/group/ungroup) accumulate in `pending_ops`, render live in `context_view`, commit as one `ContextEdit` version when boundary fires; file edits create sibling blocks [`block.edit-semantics`] (version graph records active sibling per `ContextVersion`; reverting a file is a forward `ContextEdit` swapping active sibling or a backward switch); artifact-version commits are sibling `Artifact`-kind blocks [`artifact.artifact-version`] (entity's `current_version_block_id` updates atomically; branch-aware surfaces resolve effective version through active `ContextVersion`); compaction passes commit `ContextEdit` versions recording mask/drop/consolidate (restoring is the same as switching); system-agent rollback is a surface projection of version-tree branching; QC corrections produce sibling versions (rejected candidate = alternative branch); coder "checkpoints and undo" is a UI projection over the version tree (every checkpoint = one `context_versions` row).

No parallel checkpoint table, no `file_checkpoints` row type, no `SessionCheckpoint`/`ToolCallCheckpoint`/`MessageVersion`/`VersionSnapshot` type, no per-tool-call atomic version commit, no shadow-directory snapshot mechanism. Pre-canonical specbase named + deleted those variants in favour of the unified version graph; this file confirms the deletion + reserves canonical names.

File 01 owns the general `Projection` primitive; this file applies it to version-graph-backed projections (materialized view, per-`ContextVersion` lifecycle+pin maps, snapshot resolutions, version timelines, comparison diffs, version-aware surface lenses); projections are rebuildable, non-authoritative read models whose corruption costs rebuild time never data loss.

Composes with: File 08 (block pool + sibling-versioning rule; this file owns per-`ContextVersion` view over pool); File 09 (artifact entity records, materialization policies, entity events; this file owns version-graph membership of artifact versions + per-`ContextVersion` artifact-lifecycle/review-state/validation-state derivation); File 10 (unified `ExecutionLedger`+`EventStream`; this file owns canonical version-graph events + ledger entry kinds, all emitted through canonical bus + recorded with canonical envelope); File 04 (run lifecycle + canonical commit-boundary list as a minimum; this file expands+closes the boundary catalogue); File 06 (lease lifecycle+approval; this file owns version-graph commits recording lease grants + reuses "projection over events"); File 07 (tool-surface composition; this file owns registry-snapshot identity anchoring a run's surface composition for replay).

`ContextVersion` supersedes "version node","history snapshot","context snapshot","conversation state node","checkpoint commit","session checkpoint","context-version row". `VersionDiff` supersedes "version delta","context diff","snapshot diff". `VersionOpSummary` supersedes "commit type","version reason","version label". `ContextOp` supersedes "context operation","atomic context change","inspector operation". `Snapshot` supersedes "snapshot id","frozen state record","point-in-time reference". `Projection` supersedes "derived view","materialized view","read model","computed view","cache" (for durably-derivable read-side data). Canonical interpretation is durable-anchor addressing, not wall-clock lookup.

## 2. Boundaries with Adjacent Layers `version.boundaries-with-adjacent-layers`
### 2.1 With File 01
[`core.versioned-durable-state`] declares `Versioned Durable State` (purpose: undo, branching, inspection, deterministic reconstruction). [`core.projection`] declares `Projection` (every projection rebuildable from source-of-truth data; declares rebuild trigger event-driven/on-demand/periodic; not source of truth for any durable fact; cost of stale/corrupted projection is rebuild never data loss). This file elaborates both into version-graph machinery + general projection contract. [`core.durable-history-transient-coordination`] establishes durable-history-vs-live-coordination separation (version graph is durable history substrate, emits through live bus per File 10). [`core.non-destructive-by-default`] establishes non-destructive-by-default + user-controlled storage management (branching/switching/GC/tombstoning/compaction/payload-deletion honour both). [`core.explicit-rejections`] forbids unkeyed model-dependent scalars (forbids storing token counts/costs/any such scalar on `ContextVersion` rows).

### 2.2 With File 02
Conversation versioning operates at conversation-context level not per-message (`No MessageVersion struct`); branching (sibling at same parent) + forking (new conversation seeded from chosen message) are canonical conversation-versioning operations. [`intent.task`]'s revision-safe task updates are commits whose `op_summary` is `TaskRevision` — task's revision counter advances when a commit lands on the path between task's prior revision-commit + new branch head; concurrent updates produce sibling branches.

### 2.3 With File 03
[`routing.route-record`] Route Record produced at routing time, carries `routing_snapshot_id` (resolves to routing-table state at routing time per §13), `policy_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `registry_snapshot_id`. Route record becomes part of version graph through `RouterEmission` block producer [`block.block`]; replay reads snapshot references to reconstruct routing inputs deterministically.

### 2.4 With File 04
[`run.version-commits`] enumerates a minimum commit-boundary set (user message, accepted agent turn, accepted artifact revision, accepted task revision, retry branch, edit branch, context edit, import/export operation); §5 closes the canonical catalogue, expanding with inspector-apply, workflow-node-complete, consolidation, manual-draft-commit, subsystem-internal-boundary cases from [`block.commit-boundary-set`]. [`run.version-commits`] defines the pending-operations buffer accumulating between boundaries + committing as one durable net change; §6 specifies the buffer's typed shape + operation contract. [`run.retry-reroute-branch`] specifies retry/reroute/branch as run-level operations not interfering with prior in-flight run (default prior run continues, new run becomes linked parallel attempt, both accessible as distinct versions); version graph records each as a branch from appropriate boundary; new run's commits land as children of the boundary version that triggered. [`run.user-intervention`] specifies `control` field on a `Run`; when control flips to `User`, subsequent user actions recorded as first-class blocks attached to run, version graph records takeover-end commit when control returns; takeover blocks participate in same `pending_ops` buffer. [`run.termination`]'s completion-forgery guard enforced at ledger commit boundary [`ledger.forgery-guards`]; version-graph commit recording run completion doesn't commit unless guard passes, but guard doesn't depend on version graph itself only on ledger entries the run's scope produced.

### 2.5 With File 05
[`capability.replay-class`] declares per-capability `replay_class` (`deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable`); consumed in §14 to select replay mode for each invocation. [`capability.registered-capability`] records registered-capability runtime state; a `registry_snapshot_id` resolves to registered-capability set at named version including `enabled`, `availability_status`, `resolved_backend_binding`, `trust_state`, `active_aliases`, registered declaration version; derivable from durable substrate (canonical capability declarations + recorded registry-state mutation events with typed timestamps) per [`ledger.replay-semantics`].

### 2.6 With File 06
[`policy.persistence`] establishes "lease state is a projection over policy events" — generalised into the `Projection` primitive contract (§16); lease state computed from `LeaseGranted`/`LeaseRevoked`/`LeaseNarrowed`/`LeaseStale` ledger entries + current world snapshot's lease-evidence facts; version-graph commit at policy decision time captures `policy_snapshot_id` + contributing scopes. A `policy_snapshot_id` resolves to active policy rule set, lease set, approval template set, contradiction-check rules at named version; derivable from durable policy-event substrate per same projection rebuild contract.

### 2.7 With File 07
[`surface.chosen-model`] establishes a `ToolSurface` is "a typed projection over the Capability Registry" — another `Projection` instance. [`surface.persistence-reconstruction`]'s reconstruction contract ("reconstruction across retry, edit, reroute, branch, and child-run spawn is deterministic from current inputs") is the same contract this file specifies for the materialized view; registry snapshot anchors surface composition for replay.

### 2.8 With File 08
File 08 owns block pool, `BlockKind` catalogue, `BlockEdge` catalogue, block commit validator, sibling-block edit semantics, hard-delete tombstones, canonical block-commit boundary set §7.6; this file consumes those boundaries as canonical commit-boundary set (§5) + specifies per-`ContextVersion` view over the pool. [`block.block-lifecycle-non-destructive-edits`] declares `BlockLifecycle`+`PinState` as derived per-`ContextVersion` view-state; §10 specifies derivation algorithm + materialized-view representation. [`block.canonical-edge-kinds`]'s `supersedes` edge is the canonical sibling-block versioning mechanism consumed for artifact version chains (§12), file edits, message edits, knowledge-entry edits, validator+adapter updates, every other "create sibling, swap active reference, record swap in diff" case. [`block.block-scope`]'s scope (`run`,`intent_thread`,`task`,`conversation`,`workspace`,`global`,`reusable_policy_rule`) bounds version-graph membership: a `ContextVersion` row is conversation-scoped; the materialized view sees blocks at conversation scope + broader; narrower-scoped (run-scoped, intent-thread-scoped) visible to runs+threads that produced them.

### 2.9 With File 09
[`artifact.artifact-version`] specifies `ArtifactVersion` is an `Artifact`-kind block per [`block.kind-catalogue`] linked by `supersedes`, artifact lifecycle/review state/validation state derived per `ContextVersion` from version-graph action log; this file specifies action-log shape (§4) + derivation rules (§10). [`artifact.provenance`] establishes canonical provenance query surface (`query_lineage`, `query_evidence_set`, `query_contributing_runs`, `query_contributing_capabilities`, `query_replay_trace`, `query_derivation_chain`, `contradiction_check`, `query_artifact_versions`); §15 specifies the forensic reconstruction surface those queries consume.

### 2.10 With File 10
[`ledger.execution-ledger`] specifies durable `ExecutionLedger`; version-graph commits become ledger entries (`VersionCommitted`, `VersionSwitched`, `BranchCreated`, `PendingOpApplied`, `VersionLabelled`, `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted`, `MaterializedViewRebuilt`, `MaterializedViewIntegrityViolated`) flowing through canonical event bus + envelope. [`ledger.replay-semantics`] establishes three replay modes; this file specifies version-graph data each consumes. [`ledger.forgery-guards`] do not apply to version-graph commits in addition to existing guards — version-graph commits are themselves carriers of consequential transitions, ledger's existing rules (status-transition forgery, unkeyed-scalar rejection, sensitivity-aware persistence) govern them at ledger commit boundary.

### 2.11 Boundary
This file is the durable-state-versioning + read-projection layer. Owns: `ContextVersion` shape + topology; `VersionDiff` field set + `VersionOpSummary` enum; canonical commit-boundary set; `ContextOp` vocabulary + `pending_ops` buffer contract; materialized view shape + rebuild contract; canonical version-switching algorithm; per-`ContextVersion` derived-state derivation rules; canonical snapshot identity catalogue + resolution contract; `Projection` primitive contract; forensic reconstruction query surface; cross-device sync model; explicit rejections; consequences. Doesn't own: block schema/edge catalogue/sibling-block edit mechanics (File 08); artifact entity record schema/materialization policy (File 09); ledger row schema/event envelope/hook contract (File 10); run lifecycle/capability-call pipeline (File 04); policy evaluation/lease lifecycle (File 06); tool-surface composition (File 07); storage on-disk layout/sync transport (future); UI rendering of timelines/comparison boards/inspectors (future UI); retrieval algorithms (File 12); context-assembly/compaction algorithms (File 13).

## 3. `ContextVersion` `version.context-version`
### 3.1 Definition
Durable, immutable, identified node of conversation-context version graph; represents one committed state (blocks active in view, their order, per-version lifecycle+pin state, per-version derived state every adjacent entity layer reads); substrate every projection rebuilds against, every snapshot resolves against, every replay mode reads from.

A `ContextVersion`: stable identity (`version_id`; never reassigned/reused/mutated); owned by exactly one `conversation_id` (cross-conversation reference uses fork §9.3 or block-level reference [`block.cross-scope-references`], never shared `version_id`); at most one `parent_version_id` (root has `parent_version_id = null`); may carry merge-source references when a commit intentionally combines branches (provenance, not tree parentage); one immutable typed `VersionDiff` (§4); one `VersionOpSummary` (§5.2); optional user-assigned `label`; typed snapshot references (`registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id`, others §13) anchored at commit time when substrate consulted; `producer` reference (matching [`block.block`]'s `producer` enum); durable across restart/archival/projection rebuild/schema migration/compaction; addressable across every layer (ledger references `version_id` [`ledger.cross-references`]; materialized view consumes it §7; artifact entity's `current_version_block_id` resolves through it [`artifact.artifact`]; surface composition record references the `version_id` at which surface consumed [`surface.persistence-reconstruction`]).

Is NOT: a snapshot of full model-request context (assembled requests reconstructable from materialized view at version, not stored on row); a copy of block content (content in block pool per File 08, version references blocks by `block_id`); a UI element (surfaces are projections, canonical row independent of presentation); a row in any single backend; a transient coordination signal (those are `AppEvent`s [`ledger.event-stream`], version is durable history); mutable (every observable change commits a new sibling/supersession version, prior preserved).

### 3.2 Required Fields (minimum):
- `version_id` — globally stable UUID (v4/v7 per CONSTRAINTS.md §15); never reassigned/mutated
- `conversation_id` — owning conversation; immutable
- `parent_version_id` — `Option<version_id>`; `None` for root; immutable
- `merge_source_version_ids` — optional set of additional source versions when a commit intentionally combines branches; immutable; absent for ordinary linear/branch commits
- `committed_at` — full-granularity commit timestamp (when boundary fired, not when operations started)
- `committed_by` — typed `producer` reference per [`block.block`]: `UserMessage { user_id }`, `CapabilityCommit { capability_id, invocation_id }`, `RouterEmission { route_id }`, `InspectorApply { inspector_lens, user_id }`, `WorkflowNode { workflow_id, node_id }`, `Import { source_kind, source_ref }`, `Consolidation { policy_id, source_block_ids }`, `Subsystem { subsystem_id, reason }`
- `op_summary` — `VersionOpSummary` enum value (§5.2)
- `diff` — `VersionDiff` payload (§4)
- `label` — optional `String`; user-assigned name; mutable through `label_version` (§17.4), not through diff updates
- `bookmarked` — `bool`; user-marked retention preference exempting version from GC retention policies (§19.4); mutable through `bookmark_version`
- `snapshot_refs` — typed map of snapshot identities the version anchors (§13): `registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id`, + registered extension keys; unused entries absent rather than null-padded
- `version_schema_version` — version of canonical row shape
- `diff_hash` — SHA-256 over canonical serialised `VersionDiff` payload; supports materialized-view integrity verification (§7.6) + forgery guards (§19.5)
- `expected_view_hash` — optional SHA-256 over canonical serialised materialized view at this version; integrity sentinel for path-walk verification (§7.6, §8.4); present when storage chose to record; absent versions still valid

Immutable for lifetime: `diff`, `snapshot_refs`, `committed_at`, `committed_by`, `op_summary`, `version_id`, `parent_version_id`, `merge_source_version_ids`, `conversation_id`, `version_schema_version`, `diff_hash`. Mutable through explicit operations (§17, §7.6): `label`, `bookmarked`, `expected_view_hash`; mutations emit typed events + ledger entries.

### 3.3 Identity — a `version_id` is:
globally unique within installation; assigned at commit; never reused/reassigned/mutated; canonical cross-layer reference (ledger entries [`ledger.cross-references`]'s `version_id` key, block-pool queries [`block.what-is-computed`]'s per-version lifecycle map keying, artifact-entity surface resolution [`artifact.per-version-vs-per-entity-derivation`], tool-surface reconstruction [`surface.reconstruction-across-retry-edit-reroute-branch`], replay invocations §15, forensic queries §16, cross-conversation forks §9.3); a UUID (v4/v7) per CONSTRAINTS.md §15. Identity independent of content; two versions with identical `VersionDiff` content have different `version_id`s; deduplication not required + explicitly not attempted (equal-content versions addressable separately, can carry independent labels/bookmarks/produced-by attributions).

### 3.4 Boundary
`ContextVersion` defines durable version-graph identity + immutable per-version metadata; block pool owns block content; materialized view (§7) projects active version's view-state over the pool; ledger records events producing each commit; version graph is an append-only tree over immutable `ContextVersion` rows; label/bookmark/expected-view-hash mutations recorded as typed events but don't alter immutable fields.

## 4. `VersionDiff` `version.version-diff`
### 4.1 Required Shape — compact (only changes recorded; unchanged blocks/lifecycle/pin/positions not enumerated). Closed canonical field set:
- `added` — `Vec<(BlockId, Position)>` — blocks newly active in this version's view, with position
- `removed` — `Vec<BlockId>` — blocks removed from view (lifecycle → `Dropped` from any prior `Active`/`Masked`/`Recovered`, or block unreferenced after a child-removal in a `Composed` parent this version supersedes)
- `lifecycle_changes` — `Vec<(BlockId, BlockLifecycle, BlockLifecycle)>` — `(block_id, from_state, to_state)` from `BlockLifecycle` [`block.block-lifecycle-non-destructive-edits`] (`Raw`,`Active`,`Masked`,`Dropped`,`Recovered`)
- `pin_changes` — `Vec<(BlockId, PinState, PinState)>` — `(block_id, from_state, to_state)` from `PinState` [same] (`Unpinned`,`Pinned`,`Protected`)
- `position_changes` — `Vec<(BlockId, Position)>` — blocks whose sequence position changed, with new position
- `metadata_changes` — `Vec<MetadataChange>` — typed per-block metadata changes the version-graph layer tracks (sensitivity-tag override at this version, description regeneration sibling activated, scope promotion projection adopted); each a closed enum from §4.3
- `hard_deletes` — `Vec<BlockId>` — blocks this commit physically destroyed [`block.hard-delete`]; transitioned to tombstones; irreversible by version switch; switching to a version where block was active produces a tombstone placeholder [`block.hard-delete`'s materialized-by fallback]
- `derived_state_changes` — `Vec<DerivedStateChange>` — typed per-entity derived-state transitions computed at commit: `(ArtifactReviewState, artifact_id, from, to)`, `(ArtifactValidationState, artifact_version_block_id, from, to)`, `(ClaimStatus, claim_id, from, to)`, + registered extension entries; §10

`Position` is integer in `[0, view_size)` denoting block's index in active version's render-order sequence; not stable identifiers; same block at different versions may occupy different positions. The diff is the net effect of all `ContextOp`s accumulated in `pending_ops` between prior commit + this one (§6); mask+unmask+commit → neither change in diff (net zero); add+remove+add-at-different-position → only final add-at-position entry appears.

### 4.2 Storage and Serialisation
Stored as single typed payload on `context_versions` row; storage may use JSON/MessagePack/CBOR/Protobuf or any serialisation preserving typed shape (canonical contract is field set + per-field type, not byte-level encoding). Compact: typical agent turn ~3–10 entries; context-edit accumulating an editing session ~5–50 entries; import committing a large block group several hundred entries. Immutable for lifetime; corrections (malformed entry detected in field, missed `lifecycle_change` discovered through audit) commit a new sibling version with `op_summary: Correction` + a `diff` applying the correction; prior remains with original diff (preserves replay determinism — replay reading prior version sees original possibly-malformed diff + reproduces historical behaviour; corrected sibling becomes new active version going forward).

### 4.3 Canonical `MetadataChange` Catalogue — closed set:
- `SensitivityOverrideApplied { block_id, prior, new, field_path: Option<JsonPath> }` — block sensitivity raised at this version [`block.sensitivity`]; lowering requires typed-confirmation policy override + emits same change with `prior > new`
- `DescriptionRegenerated { old_block_id, new_block_id }` — description regenerated through canonical regeneration capability, producing sibling block [`block.description-immutability`]; diff records the supersession
- `ScopePromotionAdopted { source_block_id, projection_block_id, source_scope, target_scope }` — a `scope_projection_of` or `promotes_scope_of` edge committed [`block.scope-promotion`]; records the promotion projection visible at broader scope
- `MaterializationRecorded { block_id, materialized_paths }` — active version's render of this block has a recorded materialization footprint at named workspace paths [`artifact.materialized-paths-provenance`]; used by disk→block sync loop
- `Custom { namespace, name, payload }` — typed extension entries registered through proposal-first [`capability.runtime-mutation`]

### 4.4 Per-Entity Derived-State Change Catalogue — closed set:
- `ArtifactReviewState { artifact_id, version_block_id, prior, new }` — explicit review-state change [`artifact.review-state`]
- `ArtifactValidationState { artifact_version_block_id, prior, new, validation_block_id }` — derived validation state transition from `validated_by` edge addition [`artifact.validation-state-derivation`]
- `ArtifactLifecycle { artifact_id, version_block_id, prior, new }` — derived artifact-lifecycle transition [`artifact.artifact-lifecycle`]; typically read-time, recorded on version when change derives deterministically (new version commit moves prior version to `Superseded`)
- `ClaimStatus { claim_id, prior, new, derivation_reason }` — derived claim-status change from evidence-link set change [`artifact.claim-status`]
- `TaskRevisionAdvanced { task_id, prior_revision, new_revision }` — revision-safe task-update commit [`intent.promotion-rule`]
- `IntentThreadContinuitySummaryRecorded { intent_thread_id, summary_block_id }` — continuity-summary block committed at a thread boundary [`intent.creation`]
- `Custom { namespace, name, payload }` — typed extension entries

Recorded on version commit when change derives deterministically from commit's contents (evidence-link addition flipping a claim from `Unresolved` to `Supported`; artifact-version commit moving prior to `Superseded`). Pure read-time recomputation not involving substrate change does not record on a version; entity-derived state recomputed on demand [`artifact.per-version-vs-per-entity-derivation`].

### 4.5 Hashing `version.diff-hash`
`diff_hash` (§3.2) is SHA-256 over `CanonicalVersionDiffEncoding` — a `CanonicalEncoding` [`core.canonical-encoding`] of `VersionDiff` payload + `version_schema_version` discriminator — not physical storage representation [`core.canonical-hash`]. All order-insensitive diff collections sorted by stable key before hashing (`block_id`, `artifact_id`, `claim_id`, `op_id` as applicable); order-sensitive sequences preserved only where diff operation explicitly defines semantic order. Supports: materialized-view integrity verification at path-walk strategic-cache nodes (§7.6, §8.6); forgery detection (stored diff whose hash mismatches recomputed-from-payload triggers `MaterializedViewIntegrityViolated` + forces rebuild from action log); cross-device duplicate detection (two devices committing same operation at same parent under deterministic conditions produce identical `diff_hash`es though typically `version_id` differs; sync layer may use hash to confirm a sibling identical to a remote sibling before suppressing duplicate-sync notifications only when both peers use same `CanonicalVersionDiffEncoding` version — optimization not correctness basis for sync [`core.canonical-hash`]). `diff_hash` + `expected_view_hash` (§7.6) share one canonicalization philosophy: storage-independent encoding, explicit schema-version tag, stable ordering, deterministic field representation. `NOT NULL` + immutable.

### 4.6 Boundary
`VersionDiff` defines what changed at a commit; materialized view (§7) is integrated result of applying every diff from the root; ledger records events; hash supports integrity verification but is not a forgery guard at commit (the diff itself is the authority) — it is a verification artifact for replay+rebuild.

## 5. `VersionOpSummary` and the Commit Boundary Set `version.version-op-summary-commit-boundary-set`
### 5.1 Definition
A commit boundary = point at which `pending_ops` (§6) flushes into a new `ContextVersion`; not implicit; every commit fires from a typed trigger producing a `VersionOpSummary` value; every commit boundary corresponds to a `BlockCommitted` boundary in [`block.commit-boundary-set`] + a `LedgerEntry` of kind `VersionCommitted` in [`ledger.entry-kind-catalogue`].

### 5.2 Closed Canonical Catalogue:
Transcript-anchor boundaries (conversation level):
- `UserMessage` — user submitted a new message; diff adds user's `MessageUser` block + attached children
- `AgentTurn` — assistant turn reached accepted final state [`run.lifecycle` step 8]; diff adds `MessageAssistant` block + constituent `ToolCallProposal`, `ToolResult`, `ReasoningTrace`, `Failure`, `ToolDenial`, `Observation`, text children + context operations agent performed during turn
- `EditMessage` — user-message edit [`intent.message`] produced a sibling block; records swap (prior `MessageUser` block → `Removed` from active view; new sibling → `Active`); downstream blocks dependent on prior message become orphans [`intent.message`] unless retry produces a new branch
- `Retry` — user clicked retry on a message; diff adds new response block(s) as siblings to prior, sharing same `parent_block_id` [`intent.message`, `run.retry`]

Inspector / manual-edit boundaries:
- `ContextEdit` — one or more `ContextOp` operations (mask/drop/pin/reorder/group/ungroup/etc.) committed through user "Apply" or canonical commit capability; records net effect
- `ContextEditWithLabel` — same as `ContextEdit` but user explicitly assigned a label at commit

Capability-execution boundaries:
- `CapabilityCommit` — a capability invocation completed + committed produced blocks [`run.call-pipeline` step 10]; used when not the assistant's `respond_with_tools` loop (which commits as `AgentTurn`) but a standalone invocation (inspector-initiated, workflow node, automation trigger)
- `WorkflowNodeComplete` — a workflow node committed its declared output [`run.structure-shapes` graph/workflow execution]; records produced blocks for the node
- `Consolidation` — a compaction/consolidation pass committed [`block.group-ungroup` group / [`block.kind-catalogue`] `Consolidation` block kind]; records `Consolidation`-kind block + masked/dropped source blocks via `lifecycle_changes`

Routing boundaries:
- `RouterEmission` — router emitted a `RouteRecord` [`routing.route-record`] producing visible blocks (routing explanation block, routing-decision capability call); typically nested inside parent `AgentTurn`/`UserMessage` but may stand alone for automation runs

Entity boundaries (when a single entity transition justifies a standalone commit):
- `ArtifactVersion` — artifact-version commit [`artifact.version-creation`] that stands alone (outside `AgentTurn`/workflow); diff carries `ArtifactCreated`/`ArtifactVersionCommitted` derived-state change
- `TaskRevision` — revision-safe task update [`intent.promotion-rule`] when not nested inside `AgentTurn`; carries `TaskRevisionAdvanced`
- `ClaimPublication` — `claim.publish` capability committed [`artifact.claim-extraction`] outside `AgentTurn`; records `Claim`-kind block + `ClaimStatus` derived-state change
- `EvidenceLink` — `evidence.link` committed an evidence-link edge outside `AgentTurn`; records edge metadata change
- `ValidationRun` — a validation run committed a `Validation` block outside `AgentTurn`

Import / portability boundaries:
- `Import` — block group imported from another conversation [`intent.message`] or portable export bundle; records imported blocks with `producer: Import { source_kind, source_ref }`
- `Export` — version graph records export; diff typically minimal (no view-state change), version carries export's anchor identity for later cross-installation reference

Workspace / disk-sync boundaries:
- `ExternalEdit` — filesystem watcher detected external edit to a materialized file + committed a sibling block [`artifact.disk-entity-sync`]; records swap

Recovery / correction boundaries:
- `Correction` — a malformed prior version's diff corrected by a new sibling version (per §4.2); rare; records corrected state
- `Recovery` — a partial-output orphan promoted to a durable block on cooperative-stop recovery [`run.cancellation`]; records promoted orphan as added to view

Subsystem boundaries:
- `Subsystem` — substrate subsystem (Memory consolidator, knowledge-base curator, scheduler) committed internal boundary; carries produced blocks + `committed_by: Subsystem { subsystem_id, reason }`
- `Automation` — automation trigger fired + produced blocks; carries produced blocks + `committed_by` naming the automation

Extension:
- `Custom { namespace, name }` — subsystem-specific commit-boundary kinds registered by subsystem/plugin/user-defined extension; `namespace` matches [`capability.capability-source`], `name` is kind id; register via proposal-first [`capability.runtime-mutation`] declaring: allowed `committed_by` producer variants; whether allowed as transcript-anchor commit; canonical `MetadataChange` + `DerivedStateChange` entries typically committed; surface-display label template; description shown in inspector + history-panel timeline

Closed catalogue canonical for cross-cutting reasoning; `Custom` for subsystem+surface specialisation; every commit declares exactly one `op_summary` — no commit ever has unparseable summary.

### 5.3 Boundary Composition — multiple logical operations may share one boundary:
- a `UserMessage` boundary with attachments commits one version adding `MessageUser` + `FileAttachment`+`SourceExcerpt` children; one boundary, one commit, one diff
- an `AgentTurn` boundary that produced tool calls/results/reasoning/final response commits one version adding `MessageAssistant` + all children + any agent-initiated `ContextOp`
- an `AgentTurn` boundary that produced a new artifact version commits one version adding new `Artifact`-kind block, recording `ArtifactReviewState`+`ArtifactLifecycle` derived-state changes, updating entity's `current_version_block_id` — all one commit
- a `ContextEdit` boundary batching many operations (mask 5, drop 2, pin 1, reorder, undo one mask) commits one version with one net diff; in-session operations live in `pending_ops` until boundary fires + merge into net effect

Canonical rule: one boundary, one commit, one diff per boundary. A run producing multiple meaningful boundaries (long automation committing one workflow-node per stage) produces multiple commits, one per boundary, each with own diff.

### 5.4 Boundary Discipline Rules:
- a boundary fires only when producing operation reached a canonical commit point [`block.commit-boundary-set`]; partial progress before commit lives in `pending_ops` + `Event`s on the bus, never as a `ContextVersion`
- a boundary cannot fire mid-stream; streaming events flow during production; commit fires when producer's declared boundary reached (model's final text accepted, capability's commit returned, workflow node's typed result delivered)
- a boundary that would produce no diff (no operations since prior commit) does not fire; system doesn't commit empty versions; exception: `Recovery` + `Correction` boundaries always commit even when net diff is small
- a boundary that would violate the block commit validator [`block.block-commit-validator`] for any committed block does not fire; validator's typed error returns through [`run.denial-is-in-band`]'s in-band denial path
- a boundary fires synchronously with producing operation's commit point; runtime cannot defer commit to a later moment (would break replay determinism)

### 5.5 Boundary
Commit-boundary catalogue defines what triggers a new version; pending-operations buffer (§6) defines what accumulates between boundaries; `VersionDiff` (§4) defines what each commit records; ledger (File 10) records events emitted at each boundary; none invent new commit semantics.

## 6. Pending-Operations Buffer `version.pending-operations-buffer`
### 6.1 Definition
`pending_ops` = per-conversation accumulation point for `ContextOp` operations applied between commit boundaries; held on per-conversation `ConversationVersionState` record; flushes into next `ContextVersion`'s `VersionDiff` when a boundary fires.

`ConversationVersionState { conversation_id, current_version_id, pending_ops: Vec<ContextOp>, updated_at }`.

Buffer is durable — every `ContextOp` applied through versioning operation surface (§17.5) recorded in `pending_ops` immediately, survives restart, recovered from durable storage when conversation reloads; NOT a transient in-memory queue.

### 6.2 Buffer Lifecycle:
1. Empty — after a boundary commits, buffer clears; `current_version_id` points at new committed version
2. Accumulating — as user/agent invokes `apply_op` (mask/drop/pin/reorder), each appends to `pending_ops` + updates materialized view live for immediate UI feedback; version graph not yet aware of operation as committed fact
3. In-session undo — user may undo most-recently-applied operation via `undo_pending` (pops last `ContextOp`, re-derives materialized view from previous state); no new commit, buffer simply shrinks; multiple undos walk backward; `redo_pending` re-applies (if supported §6.5)
4. Commit — when a boundary fires (§5), runtime computes net diff of `pending_ops` against pre-buffer materialized view, creates new `ContextVersion` with that diff, clears buffer, advances `current_version_id`, emits canonical events (`PendingOpApplied` per contributing operation; `VersionCommitted` for new version)
5. Discard — user-cancellation of in-flight assistant turn [`run.cancellation`] may discard buffer entirely (cooperatively cancel producing operations, drop accumulated `pending_ops`, re-derive materialized view to state at `current_version_id`); conversation returns to pre-buffer state with no version commit

### 6.3 In-Session Undo — `undo_pending(conversation_id)`:
requires `pending_ops` non-empty (empty buffer's undo is no-op); pops most recent `ContextOp`; re-derives materialized view by re-applying remaining operations from post-`current_version_id` baseline (or by applying inverse of popped operation if inverse well-defined for that kind §11.4); emits typed `PendingOpUndone { conversation_id, popped_op }`. Non-destructive: popped operation not recorded as committed history (never committed); walking buffer backward by repeated undo is the canonical in-session undo affordance.

### 6.4 Buffer Discard — `discard_pending(conversation_id, reason)`:
requires `pending_ops` non-empty; drops every operation; re-derives materialized view to state at `current_version_id`; emits typed `PendingOpsDiscarded { conversation_id, reason, dropped_count }`. Used by user-cancellation of in-flight assistant turn [`run.cancellation` cooperative cancellation] + run-level supersession (retry explicitly discarding prior turn's pending state instead of committing). Discarded operation's blocks remain in pool as orphans [`run.cancellation`], subject to block/storage retention policy; any timed retention requires explicit user/profile selection + must preserve provenance + tombstone requirements; version graph doesn't retain a record of discard beyond the typed event in the ledger.

### 6.5 Redo — `redo_pending(conversation_id)` optional:
storage may maintain a forward redo stack alongside backward undo stack within buffer's lifetime; when supported, re-applies most-recently-undone operation; both stacks clear when a commit boundary fires (post-commit, redo doesn't cross the boundary — way to redo post-commit is to switch back to prior version via §8). Settings-driven (`versioning.in_session_redo_enabled`); optional not mandatory.

### 6.6 Buffer Storage
Stored on per-conversation `ConversationVersionState { conversation_id, current_version_id, pending_ops (typed payload — JSON/MessagePack/CBOR per storage), updated_at }`. Survives restart; on restart runtime reloads `ConversationVersionState`, re-derives materialized view from `current_version_id` + buffer, conversation resumes. If buffer's contents inconsistent with substrate (referenced block hard-deleted between operations, referenced version_id no longer exists), runtime emits `PendingOpsInconsistencyDetected` + discards buffer with typed reason (rare, corresponds to a substrate violation).

### 6.7 Concurrent Modifications
Multiple actors may modify `pending_ops` for same conversation (user clicks mask while agent performs a context operation during a turn); buffer is a single ordered sequence; operations serialised at the versioning operation boundary; two operations targeting same `block_id` follow canonical operation-merge rules §11.6 (typically later operation wins for state changes; reorders interleaved by application order).

### 6.8 Boundary
Pending buffer defines accumulation point; commit boundary (§5) defines when buffer flushes; materialized view (§7) reflects buffer's live state for instant UI feedback; ledger records typed events at apply/undo/discard; version graph updated only at commit.

## 7. Materialized View (`context_view`) `version.materialized-view-context-view`
### 7.1 Definition
Canonical read-optimised projection of active conversation version's view-state over the block pool; consumed by context assembly, surface rendering, retrieval, downstream operations needing current state. Source of truth is version graph + block pool + relevant durable substrates; `context_view` rebuildable from those + holds no facts they don't. Single shared materialized projection layer for active conversation state; inherits File 01's `Projection` contract.

### 7.2 Required Shape — per-conversation table of typed rows:
`ContextViewRow { conversation_id, block_id, position (sequence index in render order), lifecycle_state (BlockLifecycle: Raw|Active|Masked|Dropped|Recovered), pin_state (PinState: Unpinned|Pinned|Protected) }`. For each `(conversation_id, block_id)` active at conversation's `current_version_id`, exactly one row. `BlockLifecycle::Dropped` blocks retained as rows (so version-graph layer can resolve them on demand + inspector can render masked/dropped placeholders), but downstream layers filter `Dropped` out of context assembly + standard retrieval [`block.block-lifecycle-non-destructive-edits`]. Per-version derived state for adjacent entity layers (artifact lifecycle/review/validation, claim status) computed on demand at read time from version graph + entity records; only `lifecycle_state` + `pin_state` stored on the row (load-bearing per-`ContextVersion` view-state, accessed at every context-assembly read).

### 7.3 Properties:
- Live updates — every `ContextOp` through versioning operation surface updates `context_view` immediately, before commit; buffer + live view together represent user's current intent; version graph records commit at boundaries
- O(1) reads — direct table lookup by `(conversation_id, block_id)` or `(conversation_id, position)` returns active state without traversing version graph; dominant access pattern for context assembly/render/retrieval
- O(path-length) rebuild — version switching (§8) walks path between current+target applying reverse+forward diffs; strategic-cache nodes (§7.6) shorten long-range walks
- Per-conversation isolation — each conversation has its own view; switching in one doesn't affect another's
- Rebuildable from durable substrate — contents entirely derivable from `(current_version_id, pending_ops)` + chain of `ContextVersion`s + their `VersionDiff`s from root; corruption resolved by rebuild never loss of canonical state
- No durable facts unique to the view — every fact reconstructable; projection not source of truth

### 7.4 Update Triggers — rebuilds/updates on:
- Apply — `apply_context_op(op)` applies effect in place; buffer accumulates operation, view updated live for instant feedback; cost O(1) for most operations, O(view_size) for reorder
- Undo/Discard — `undo_pending`+`discard_pending` re-derive view per §6.3, §6.4
- Commit — diff computed from buffer's net effect; view already at post-commit state, no rebuild required; `current_version_id` advances, buffer clears
- Switch — `switch_to_version(target_id)` walks path applying reverse/forward diffs; view ends at target's state
- Block-pool mutation — new sibling block committed at active version [`block.edit-semantics`] added to view at supersession's recorded position; view updates synchronously with block commit
- Hard delete — hard-deleted block's row transitions to tombstone placeholder [`block.hard-delete`]; referenced positions remain but resolve to tombstone
- Restart — view rebuilt from durable storage (view itself durable in `context_view` rows; corruption fallback rebuilds from action log)
- Integrity violation — detected `MaterializedViewIntegrityViolated` event (§7.6) triggers full rebuild from action log

### 7.5 Rebuild Trigger Declaration — per [`core.projection`]:
event-driven (every `apply_op`, every commit, every block-pool mutation at active version, every switch); on-demand (explicit rebuild on integrity violation, explicit rebuild requested by inspector/maintenance); periodic (none — view doesn't periodically rebuild).

### 7.6 Integrity Verification `version.expected-view-hash`
Verifiable through `expected_view_hash` (§3.2). At strategic-cache nodes (§8.6) + at commit, storage may compute a canonical hash over `context_view` for active version + store it. Subsequent rebuilds/reads verify by: (1) recomputing canonical hash over current `context_view`; (2) comparing against stored `expected_view_hash`; (3) on mismatch, emitting `MaterializedViewIntegrityViolated { conversation_id, version_id, expected_hash, actual_hash }` ledger entry, marking conversation's view `degraded`, rebuilding from action log; (4) after rebuild, recomputing + recording corrected hash. Storage may make hash computation mandatory/optional based on `versioning.view_integrity_check_strictness` setting (`Strict`, `CacheAnchorsOnly`, `Off`); exact defaults belong to settings profiles. Canonical hash domain: SHA-256 over a `CanonicalEncoding` [`core.canonical-encoding`, `core.canonical-hash`] of the row set sorted by `(block_id)` (order-insensitive collection sorted by stable key), each row serialised as `(block_id, position, lifecycle_state, pin_state)` + explicit schema-version tag; computed over storage-independent encoding not physical bytes (independent of insertion order, durable across implementations, stable across backends); cross-peer comparison requires same encoding version.

### 7.7 Cross-Surface Materialized View
Each conversation has one view; surfaces project through surface-specific filters [`surface.chosen-model`, `block.cross-surface-interoperability`, `artifact.per-surface-projections`]; underlying view shared across all surfaces. Coder-surface render filters for `FileAttachment`+`Artifact`; transcript render filters for transcript-anchorable kinds; inspector render shows every row incl. `Dropped` placeholders; all read same `context_view` rows.

### 7.8 Boundary
Materialized view defines active-version projection over the pool; version graph defines action log; block pool defines content; ledger records events; storage realises durability (§18); view's shape + integrity contract owned here, rest consumed.

## 8. Version Switching `version.version-switching`
### 8.1 Definition
Changes a conversation's `current_version_id` to a target version's id, rebuilding the materialized view to match target's state; non-destructive (prior current version remains, reachable through subsequent switches).

### 8.2 The Algorithm — `switch_to_version(conversation_id, target_version_id)`:
1. Validate — target must exist in conversation's version tree; current must exist; both share conversation's root
2. Find path — compute path in tree from current to target (walk up from current to common ancestor with target, then down from common ancestor to target); path is sequence of `(direction, version_id)` pairs where direction is `Up`/`Down`
3. Discard pending operations — any `pending_ops` from current version's session discarded (no implicit commit on switch §6.4); buffer clears; view re-derived against current version's state before the walk begins
4. Apply reverse diffs (up) — for each `Up` step, apply reverse of that version's diff to `context_view`: `added` removed; `removed` re-added at old positions; `lifecycle_changes` reverse `(block_id, from, to)` → `(block_id, to, from)`; `pin_changes` similarly; `position_changes` move blocks back to parent-version positions; `metadata_changes`+`derived_state_changes` reverse per typed inverse rules; `hard_deletes` cannot be reversed by switch (affected blocks remain tombstones, view shows tombstone placeholder)
5. Apply forward diffs (down) — for each `Down` step, apply forward diff of that version
6. Verify integrity — if target has `expected_view_hash`, recompute canonical hash + verify per §7.6; on mismatch emit `MaterializedViewIntegrityViolated` + rebuild from action log
7. Advance pointer — update `ConversationVersionState.current_version_id` to `target_version_id`
8. Discard pending again — buffer remains empty (discarded in step 3); no operations from prior version's session retained
9. Emit events — `VersionSwitched { conversation_id, from_version_id, to_version_id, path_length, rebuild_from_action_log: bool }` (boolean indicates whether full rebuild required) through canonical bus + record in ledger

### 8.3 Path-Length Complexity
Retry-then-undo switch 1–3 hops; adjacent siblings 2 hops (one up, one down); two recent branches 3–10 hops; long-range jumps to early state 50–500 hops (strategic-cache nodes §8.6 shorten). Application of each step O(diff_size); typical diff size single-digit entries; even at 500-hop walks with 5-entry diffs total work bounded + cheap (microseconds to low milliseconds).

### 8.4 Hard Delete Handling
If path includes versions with `hard_deletes`, those deletions not reversible by switch; affected blocks remain tombstones [`block.hard-delete`]; materialized view at versions where blocks were active resolves to tombstone placeholder; composition-materialization fallback [`block.hard-delete`] applies if a `Composed` parent's child hard-deleted (resolved content materialized into new block linked by `materialized_by`, preserving view's resolvability past deletion). Switching to a version before a `hard_delete` does not restore the deleted block; tree records block was once active then destroyed; tombstone represents what remains.

### 8.5 Switching from Buffered State — if `pending_ops` non-empty when `switch_to_version` called:
if configured to discard, runtime discards buffer (§6.4) + warns user via typed event `PendingOpsDiscardedOnSwitch { conversation_id, discarded_count }`. User may configure `versioning.switch_with_pending_behaviour` to: `Discard` (discard buffer, switch, warn); `Commit` (commit buffer first as a `ContextEdit`, then switch); `AskUser` (open typed-confirmation flow [`policy.permission-floor-typed-confirmation`] asking Commit/Discard/Cancel).

### 8.6 Strategic-Cache Nodes
For long-range switches, storage may maintain materialized-view caches at strategic version nodes; when a switch's path crosses a strategic-cache node, walk starts from nearest cached node instead of root; storage optimisation (canonical algorithm doesn't require it); cache placement/eviction/count limits storage/profile concerns; cache corruption triggers rebuild from durable substrate, never changes canonical state. May also serve as anchor points for `expected_view_hash` integrity verification (§7.6).

### 8.7 Boundary
Version switching defines deterministic path-walk algorithm; materialized view (§7) is the substrate; block pool (File 08) is the content source; strategic-cache nodes (§8.6) are storage optimisations; ledger records switch events; no layer redefines switch semantics.

## 9. Branching and Forking `version.branching-forking`
### 9.1 Branching
A branch = a sibling `ContextVersion` of an existing non-leaf version; canonical non-destructive divergence primitive: when user/agent commits a new version after switching to a non-leaf, new commit becomes a child of switched-to version instead of prior leaf, both branches remain permanent + switchable. Mechanics: (1) switch to `version_id_X` (§8); (2) perform operations accumulating in `pending_ops`; (3) boundary fires, new version `version_id_Y` created with `parent_version_id = version_id_X`; (4) if `version_id_X` already has child `version_id_Z` (from before switch), `version_id_Y` becomes its sibling (both have `parent_version_id = version_id_X`); (5) `current_version_id` advances to `version_id_Y`; `version_id_Z` + descendants remain reachable. Natural consequence of switching plus committing; user doesn't invoke a separate "branch" operation. Canonical event `BranchCreated { conversation_id, branched_from_version_id, new_branch_root_version_id }` whenever a commit creates a new branch (not when it merely extends existing leaf). Branch labels: branches may be labelled at branch-root version (§17.4 `label_version`); surfaces may show branches as sibling lines from shared parent.

### 9.2 Branch Merge Provenance
Version graph remains a single-parent tree; when a user intentionally combines work from multiple branches, resulting commit is a normal child of the branch chosen as base + carries `merge_source_version_ids` for additional contributing versions. `merge_source_version_ids` are provenance references not topology edges for path-walk switching; preserves simple tree algorithm while making merge contribution inspectable for history/comparison/replay.

### 9.3 Forking — a fork = a new conversation seeded from an existing conversation's version:
(1) creates new `conversation_id` (File 02); (2) copies allowed materialized-view rows from source's target version into new conversation's root view; (3) creates new conversation's root `ContextVersion` with `parent_version_id = null` + an `Import` op_summary referencing source `(source_conversation_id, source_version_id)`; (4) establishes block-pool references for blocks whose scope/sensitivity/policy allow visibility in destination; (5) records `ConversationForked { source_conversation_id, source_version_id, new_conversation_id }`; (6) forks reachable through `provenance.query_lineage` for new conversation [`artifact.provenance`]. Forking is explicit-copy variant of cross-conversation reference; share-without-copy variant [`block.cross-scope-references`] also supported (a block at `workspace` scope or broader is addressable from any conversation without forking). Blocks whose scope/sensitivity prevents visibility in destination omitted by default + replaced with typed placeholder `ForkOmitted { source_block_id, reason: ScopeRestriction | SensitivityRestriction | PolicyDenial }` (a block in forked pool carrying source identity for provenance but no content; user may later promote scope with approval per File 06, copy with new identity + redacted content, or leave placeholder; sharing-by-default for restricted blocks explicitly invalid). Subsequent edits in fork commit new versions under fork's `conversation_id`; source unaffected; edits creating sibling blocks [`block.edit-semantics`] place new siblings in unified pool (both conversations see them but only fork's version graph references them as active).

### 9.4 Cross-Workspace Forking
Requires future Sync, Import, Export spec's portable bundle mechanism. Canonical contract: a fork imports source conversation's relevant blocks, version chain (or flattened root with `Import` op_summary), entity records, edge metadata into destination workspace; source's `version_id`s do not transfer (each workspace has its own UUID space); import produces new identities + records source-to-destination mapping for provenance queries.

### 9.5 Branch Topology Visualisation — version tree is a directed tree with `parent_version_id` defining child→parent edge. Canonical rendering data:
root at top, children below, siblings horizontal; linear runs (parent has exactly one child, child has exactly one parent) collapse into "linear run of N versions" summary in tree view; branch points (parent with multiple children) emit distinct visual nodes for each child; conversation's `current_version_id` highlighted, leaves addressable through "go to leaf" navigation; labelled + bookmarked versions visually distinguished. Tree view + expandable list view are surface projections of the same data [`intent.presentation`, source `03-versioning-and-branching.md`]; switching between views is a rendering choice not a data reload.

### 9.6 Boundary
Branching is natural consequence of switch-plus-commit; merge-source references preserve merge provenance without changing tree parentage; forking is explicit-copy variant of cross-conversation reference; tree topology is data structure the materialized view rebuilds against; none add new commit semantics.

## 10. Per-Version Derived State Maps `version.per-version-derived-state-maps`
### 10.1 Definition
Per-`ContextVersion` derived state — `BlockLifecycle`, `PinState`, `ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`, `TaskRevision`, + registered extensions — computed from version-graph action log over block pool + entity records; version graph is substrate, entity records carry stable identity, derived state is the active version's view-state of each entity. This file defines derivation rules; adjacent layers consume (context assembly reads `BlockLifecycle` to decide what to include; surface renderers read `ArtifactLifecycle` to mark "Draft"/"Active" badges; policy layer reads `ClaimStatus` to evaluate confidence-floor rules).

### 10.2 Block Lifecycle Derivation
Per [`block.block-lifecycle-non-destructive-edits`], `BlockLifecycle` is `Raw|Active|Masked|Dropped|Recovered`. Per `ContextVersion`, each block's lifecycle = result of: (1) block's initial state at first commit (typically `Raw` for transient, `Active` for transcript+standard committed blocks); (2) all `lifecycle_changes` entries in `VersionDiff`s along path from version where block first added to current; (3) final state declared in latest applicable `lifecycle_change`. Materialized view stores the result; action log is substrate; deterministic.

### 10.3 Pin State Derivation
Per [`block.block-lifecycle-non-destructive-edits`], `PinState` is `Unpinned|Pinned|Protected`; same derivation as `BlockLifecycle` (initial state + all `pin_changes` along path).

### 10.4 Artifact-Level Derived State
Per [`artifact.artifact-lifecycle-states`], `ArtifactLifecycle` is `Draft|Active|Validated|Superseded|Archived|Discarded`; `ReviewState` is `Unreviewed|AcceptedByUser|AcceptedByAgent|Rejected|NeedsRevision`; `ValidationState` is `NotValidated|PendingValidation|Passed|Failed|NeedsReview`. Per `ContextVersion`, each artifact's effective state derived from: active version-block for the artifact (via entity's `current_version_block_id` or version-tree's branch-aware projection); `derived_state_changes` entries explicitly recording artifact-state transitions; `validated_by` edges on the active version-block [`artifact.validation-state-derivation`]. Entity record's denormalised `current_version_block_id` is default/latest pointer for non-branch-specific reads; branch-aware surfaces resolve effective version through active `ContextVersion`'s view of artifact-version chain.

### 10.5 Claim Status Derivation
Per [`artifact.claim-status`], `ClaimStatus` is `Candidate|Supported|Contradicted|Unresolved|Superseded|Withdrawn`. Per `ContextVersion`, a claim's effective status derived from: set of `EvidenceLink` edges active at the version [`artifact.evidence`]; `claim.evidence_threshold` setting in effect at version (per `settings_snapshot_id`); explicit `ClaimStatusOverridden` events since publication; explicit `ClaimWithdrawn` events. When substrate changes (evidence link added/removed; claim overridden/withdrawn), corresponding `ClaimStatus` change recorded in committing version's `derived_state_changes`; pure read-time recomputation not involving a substrate change does not record on a version.

### 10.6 Task Revision Derivation
Per [`intent.promotion-rule`], task updates carry a revision counter; concurrent updates produce sibling branches. Per `ContextVersion`, a task's effective revision = latest committed `TaskRevisionAdvanced` derived-state change on path from task's creation commit to current version.

### 10.7 Custom Derived-State Extension
Subsystems/plugins may register additional derived-state kinds via proposal-first [`capability.runtime-mutation`]. Registered kinds declare: derivation source (which `VersionDiff` entries trigger recomputation); derivation rule (deterministic algorithm computing new state from substrate); canonical event kind emitted when state changes; surface-display rendering hint. Participate via `derived_state_changes::Custom { namespace, name, payload }` entries per §4.4.

### 10.8 Boundary
Per-version derived state computed on demand from substrate (action log + entity records + snapshot references); materialized view stores only `BlockLifecycle`+`PinState` (accessed on every read); other derived state recomputed at query time or cached as a separate materialized projection per storage optimisations; derivation deterministic, corruption resolved by rebuild.

## 11. `ContextOp` — Closed Canonical Operation Vocabulary `version.context-op-closed-canonical-operation-vocabulary`
### 11.1 Definition
A `ContextOp` = one user-or-agent-or-subsystem-applied operation against the materialized view; operations accumulate in `pending_ops` (§6) + merge into one `VersionDiff` at next commit boundary (§5); operations are the version-graph's action language, diff is the net result.

### 11.2 Closed Catalogue:
`ContextOp { Mask { block_id }; Unmask { block_id }; Drop { block_id }; Recover { block_id }; Pin { block_id }; Unpin { block_id }; Protect { block_id }; Unprotect { block_id }; Reorder { block_ids } (new order for listed blocks); AddToContext { block_id, position } (add an existing block to active view); RemoveFromContext { block_id } (remove from active view, transitions to Dropped); Group { constituent_ids, name, description, group_kind } (create a Group block [`block.group-ungroup`]); Ungroup { group_id } (dissolve a Group block from active view); AddToGroup { group_id, block_ids, position } (add blocks to a Composed parent); RemoveFromGroup { group_id, block_ids } (remove from a Composed parent); EditBlock { old_block_id, new_content_variant } (create sibling block [`block.edit-semantics`]); PromoteScope { block_id, target_scope } (create a scope-promotion projection [`block.scope-promotion`]); ApplySensitivityOverride { block_id, prior, new, field_path } (raise sensitivity [`block.sensitivity`]); HardDeleteBlock { block_id } (destructive [`block.hard-delete`]); Custom { namespace, name, payload } (registered extension) }`. `Position` is `Option<usize>`; `None` = "append at end."

### 11.3 Operation Semantics:
- Mask — `BlockLifecycle` → `Masked` for active version's view; compaction reads `Masked` blocks' descriptions instead of content; block stays in pool
- Unmask — `Masked`/`Recovered` → `Active`; block already in view, only lifecycle state changes
- Drop — → `Dropped`; excluded from retrieval + standard context assembly; reachable only through explicit recovery
- Recover — `Dropped`/`Masked` → `Recovered` (semantically `Active` + historical mark)
- Pin/Unpin — `PinState` → `Pinned`/`Unpinned`; compaction respects pinned blocks unless explicitly configured + approved otherwise
- Protect/Unprotect — `PinState` → `Protected`/`Unpinned`; protection stronger than pin (compaction skips protected blocks entirely)
- Reorder — new positions for listed blocks; positions for blocks not listed unchanged
- AddToContext/RemoveFromContext — add/remove a block from active view at given position; `RemoveFromContext` → `Dropped` (recoverable); `AddToContext` requires block to exist in pool
- Group — creates a new `Group`-kind `Composed` block with the constituents as children; block commit at next boundary; `pending_ops` entry records intent
- Ungroup — dissolves group's presence in active view (group block remains in pool; view stops rendering it as container, exposes children at appropriate positions)
- AddToGroup/RemoveFromGroup — modify a `Composed` parent's children — produces a new sibling `Composed` block with new children list [`block.cross-reference-vs-containment` — composition immutability]
- EditBlock — creates a new sibling block with new content [`block.edit-semantics`] + updates active view to reference new block at position old block occupied; old block stays in pool
- PromoteScope — creates a `scope_projection_of`/`promotes_scope_of` projection [`block.scope-promotion`]; original remains at narrower scope
- ApplySensitivityOverride — raises block's effective sensitivity [`block.sensitivity`]; lowering requires typed-confirmation [`policy.permission-floor-typed-confirmation`]
- HardDeleteBlock — physically destroys the block [`block.hard-delete`]; destructive, requires typed-confirmation when block referenced, produces a tombstone
- Custom — records a registered extension operation; semantics declared in extension registration

### 11.4 Operation Inverses (for in-session undo §6.3) — each operation has a typed inverse:
`Mask ↔ Unmask`; `Drop ↔ Recover`; `Pin ↔ Unpin`; `Protect ↔ Unprotect`; `Reorder` inverse = re-apply prior positions for the touched blocks (recorded as snapshot of pre-reorder positions on buffer entry); `AddToContext ↔ RemoveFromContext`; `Group ↔ Ungroup` (inverse of creating group is dissolving it; group block remains in pool; redo of group restores same block reference rather than committing a new sibling); `AddToGroup ↔ RemoveFromGroup`; `EditBlock` inverse = revert view's reference to prior block (new sibling stays in pool, not destroyed by undo); `PromoteScope` inverse = remove projection from active view (projection block remains in pool); `ApplySensitivityOverride` inverse = lower-back permitted only when user explicitly authored the raise, otherwise inverse rejected by typed-confirmation; `HardDeleteBlock` has no inverse (once destroyed, cannot be restored by undo; in-session undo of a not-yet-committed `HardDeleteBlock` supported since destruction not yet committed; post-commit undo impossible); `Custom` operations declare their inverse in registration. Undo machinery uses these inverses to walk backward through `pending_ops`.

### 11.5 Operation Side Effects on Block Pool
Several operations cause block-pool mutations through File 08's mechanisms: `Group`, `AddToGroup`, `RemoveFromGroup`, `EditBlock`, `PromoteScope` all create new sibling blocks (block commit at next boundary; operation in `pending_ops` references new sibling's `block_id` reserved at apply time); `HardDeleteBlock` physically destroys a block [`block.hard-delete`]. The operation in the buffer references the new sibling's `block_id`; block commit pipeline [`block.block-commit-validator`] validates the block at commit boundary; if validation fails, entire commit fails + `pending_ops` preserved for user correction.

### 11.6 Operation Merge Rules (Concurrent/Conflicting) — when two operations in `pending_ops` target same `block_id`:
- Sequential lifecycle changes — later operation wins for final state; `Mask → Unmask → Mask` = `Masked`; `Drop → Recover` = `Recovered` (which is `Active` + historical mark)
- Sequential pin changes — later operation wins; `Pin → Unpin` = `Unpinned`
- Reorder + position change — most recent position assignment for a block wins
- AddToContext after RemoveFromContext — net effect block is `Active` at new position
- RemoveFromContext after AddToContext — net effect block is `Dropped` (no record in diff except lifecycle change if block was previously `Active`)
- EditBlock + EditBlock — second edit's new sibling supersedes first; first edit's sibling remains in pool but not the active reference
- HardDeleteBlock — terminal; subsequent operations on same `block_id` are typed errors (block no longer exists)

Merge computed deterministically at commit; diff's `lifecycle_changes`/`pin_changes`/`position_changes` reflect only net effect, not intermediate states.

### 11.7 Authority and Authorisation — operations subject to canonical capability policy (File 06):
every agent-invoked `ContextOp` flows through a registered capability + the File 04 execution pipeline (agents don't mutate version history through side channels); ordinary view mutations (`Mask`, `Drop`, `Pin`, `Reorder`, `AddToContext`, `RemoveFromContext`) are `WorkspaceWrite` unless narrowed by policy; `HardDeleteBlock` has `permission_floor: Denied` + requires typed-confirmation [`policy.permission-floor-typed-confirmation`]; `ApplySensitivityOverride` that lowers sensitivity has `permission_floor: Denied` + requires typed-confirmation; `PromoteScope { target_scope: global }` is `UserApproval` tier or stricter (broadens visibility to all workspaces); destructive/broadening operations (`HardDeleteBlock`, sensitivity lowering, global scope promotion, version tombstoning, version payload deletion, retention application) user-confirmed or policy-denied by default. User invocation through inspector/palette + hook-mediated substitution both pass through same policy boundary; hooks may substitute or block proposed operations only through File 10 hook authority classes.

### 11.8 Boundary
`ContextOp` vocabulary defines the operation language; pending buffer (§6) accumulates operations; diff (§4) records net effect at commit; committed `VersionDiff` is the canonical state-reconstruction input; `PendingOpApplied`/`PendingOpUndone` ledger entries may preserve operation history for audit + UI inspection, but rebuild + switch semantics depend on diffs not replaying the full operation sequence.

## 12. Sibling-Block Versioning over the Block Pool `version.sibling-block-versioning-over-block-pool`
### 12.1 Definition
Canonical mechanism by which observable content changes produce new immutable blocks in the unified pool, linked to prior by `supersedes` edges [`block.canonical-edge-kinds`], with active reference in materialized view updated to point at new block; version graph records swap in diff; prior block stays in pool reachable through version-tree-aware projection. Shared across: file edits (§12.2); message edits (§12.3); artifact-version commits (§13); knowledge-entry edits (§12.4); validator+adapter updates (§12.5); description regeneration [`block.description-immutability`]; composed-block child changes [`block.cross-reference-vs-containment`]; instruction-fragment updates + reusable-policy-rule updates.

### 12.2 File Edits
A file edit [`artifact.version-creation`, `tools/file-operations.md`] creates a new sibling `Artifact`-kind block (or a `FileAttachment` block for non-artifact files) with new content: fresh `block_id`; same `parent_block_id` as prior; a `supersedes` edge to prior; new content in `BlockContent` (variant matching prior — `Inline`/`External`/`Composed`); fresh `content_hash`; fresh `created_at`; `producer` reflecting edit source (user edit, agent `file.edit` invocation, filesystem watcher). Materialized view's row for active file block transitions to reference the new sibling at same position; version diff records swap as `(BlockId, Position)` removed-and-added pair + any per-version metadata changes. Reverting a file [`artifact.version-creation`, `domains/coder/checkpoints-undo.md`] — two paths: Forward revert (`coder.file_reverted`) commit a new `ContextEdit` version swapping active file block back to historical sibling (current branch advances, prior current-branch state reachable through switch); Switch revert switch conversation's `current_version_id` to a version where historical file block was active (both branches remain). File-sync layer [`artifact.disk-entity-sync`] detects active-block change + rewrites materialized file on disk to match.

### 12.3 Message Edits
A message edit [`intent.message`] creates a new sibling `MessageUser` block with new content; same `parent_block_id` as prior message block; version graph commits an `EditMessage` version recording the swap; downstream blocks (assistant responses, tool calls, results dependent on prior message) become orphans of new sibling's lineage; user typically follows up with `Retry` to produce a new downstream branch, or with a manual continuation producing new assistant turns referencing the edited message. Orphan downstream non-destructively preserved: prior message's downstream remains in pool reachable through version-tree-aware switch back to pre-edit version.

### 12.4 Knowledge-Entry Edits
Knowledge entries carrying durable content participate in the version tree as blocks. The `KnowledgeEntry` metadata record carries a content-version pointer such as `current_version_block_id` (a denormalised projection to active entry block), not the conversation's `current_version_id`. Edits follow same sibling pattern: user edits → `current_version_block_id` advances to new entry block immediately on commit; agent-proposed edits with user approval → same (advances on accept); agent-proposed edits with user rejection → new sibling block remains in pool, canonical `current_version_block_id` stays on prior entry block, rejected version left as a sibling branch reachable through version-tree view. Plugin-bundled knowledge entries a user wants to customise can be forked by creating a user-owned sibling block linked by `supersedes`; original remains under plugin's source attribution, user's fork carries `UserDefined` source; both remain in unified pool; user's fork becomes canonical `current_version_block_id` at user's preferred scope.

### 12.5 Validator and Adapter Updates
`Validator`-kind + `Adapter`-kind blocks [`artifact.artifact-kind`] follow same sibling-versioning pattern; updates to a validator's rules or an adapter's logic create new siblings; canonical execution path reads active sibling at conversation's `current_version_id` (or at broader-scope active version for workspace/global-scope validators).

### 12.6 Boundary
Sibling-block versioning is the canonical content-change mechanism shared across all entity layers; File 08 owns block-pool mechanics, this section owns version-graph integration; `supersedes` edge + active-reference swap in materialized view are canonical signals of "this content was edited"; version-tree branch is canonical record of "here's where in history that edit happened."

## 13. Artifact Version Chains `version.artifact-version-chains`
### 13.1 Definition
An artifact version chain = linear (or DAG-shaped under multi-parent merges) sequence of `Artifact`-kind blocks linked by `supersedes` edges representing the evolution of a single artifact entity [`artifact.artifact-version`]. Chain has: stable entity identity (`artifact_id`) shared across all versions; a typed `ArtifactVersion` metadata record per version [`artifact.artifact-version`] carrying `version_id` (same value as version-block's `block_id`), `artifact_id`, `version_number` (monotonically increasing integer per artifact), `parent_version_id`, `derivation_summary`, `produced_by_run_id`, `produced_by_node_id`, `produced_by_capability_id`, `materialized_paths`, `validation_report_id`, `metadata`; a default/latest pointer on the entity record (`current_version_block_id`) for non-branch-specific reads; branch-aware resolution through active `ContextVersion`'s view of the chain.

### 13.2 Chain Topology
Default topology linear (each version has one parent, prior version's `block_id` as `supersedes` edge target). DAG topology supported through `artifact.merge` [`artifact.version-creation`], producing a new version with one principal parent (recorded as `parent_version_id`) + additional parents linked by `derives_from` edges; version graph captures merge as a single commit; resulting topology in chain is a DAG with new version having multiple incoming edges.

### 13.3 Per-`ContextVersion` Resolution
Non-branch-specific reads use entity record's `current_version_block_id`. Branch-aware reads: (1) start at conversation's `current_version_id`; (2) walk back through version graph until diff containing the artifact's most recent version-commit found; (3) active version-block = artifact's version-block produced by that commit; (4) if no version-commit for the artifact found on path back to root, artifact has no version in current view — return `None` (artifact may exist in broader workspace scope but not in this conversation's tree). Resolution O(path-length from current to artifact's first commit in this conversation); strategic-cache nodes (§8.6) + per-artifact version-pointer caches may optimise.

### 13.4 Branch-Aware Artifact Versions
When a conversation branches + artifact edited on multiple branches, artifact's effective version diverges per branch; materialized view of each branch resolves artifact to its branch-active version-block; entity record carries default/latest pointer (typically leaf branch's most recent version), but branch-aware surfaces (comparison board, version inspector, cross-branch diff renderer) resolve per branch. Artifact's version chain in DAG form may carry multi-parent versions when user merges two branches' versions through `artifact.merge`.

### 13.5 Materialization Across Versions
Per [`artifact.materialized-paths-provenance`], each version's `materialized_paths` records workspace paths where version's content was written; when conversation switches versions, workspace's disk state updates to match active version's `materialized_paths` [`artifact.disk-entity-sync` disk-sync loop]; prior versions' materializations remain on disk per workspace retention policy [`artifact.materialized-paths-provenance` — paths typically include the `version_id` in the path template to avoid overwriting].

### 13.6 Boundary
Artifact version chains are a specialisation of sibling-block versioning over the unified pool; File 09 owns entity-record schema, this section owns version-graph integration + per-`ContextVersion` resolution rule; materialization contract owned by [`artifact.artifact-materialization`].

## 14. Snapshots `version.snapshots`
### 14.1 Definition
A snapshot = a typed, durable, addressable reference to the state of a canonical substrate (registry, settings, world, policy, pricing, routing) at a durable anchor; NOT stored copies of substrate content — identities the ledger, run records, capability invocations, replay machinery carry to address substrate state for forensic queries + deterministic replay; resolves to substrate state through canonical replay machinery (§15). Snapshot identity includes snapshot kind, stable id, anchor, substrate schema/version, resolver contract; ids unique within installation, never reassigned.

### 14.2 Closed Canonical Snapshot Catalogue `version.closed-canonical-snapshot-catalogue` — each addressable as `<kind>_snapshot_id`:
- `registry_snapshot_id` — addresses `RegisteredCapability` state at named version [`capability.registered-capability`]; resolution walks capability-registration ledger entries [`ledger.entry-kind-catalogue`: `CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityUpdated`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `CapabilityRegistryStateChanged`] from install boot to snapshot's substrate anchor; result is registered-capability set with `enabled`, `availability_status`, `resolved_backend_binding`, `trust_state`, `active_aliases`, registered declaration version at that anchor
- `settings_snapshot_id` — addresses effective settings source stack at named version (File 15); captures explicit durable values, active profile context + profile layers, invocation overlays when used, definition versions, locality metadata, validation diagnostics affecting resolution, redaction-safe overlay/default source metadata; TOML file remains per-device + unsynced, but if execution depended on a TOML-provided non-secret value, snapshot records effective resolved value or redaction-safe placeholder so replay+audit can explain
- `world_snapshot_id` — addresses world-model state at named version [`core.world-model`]; world model maintains its own durable substrate (active surface + owning subsystem, mounted panels, focused element, available capabilities/control affordances, active workspaces); snapshot resolves by walking that substrate to the world-substrate sequence anchor through world-model service's replay path
- `policy_snapshot_id` — addresses active policy rule set, lease set, approval templates, contradiction-check rules at named version (File 06); resolution walks policy-event ledger entries from boot to anchor; result is policy state at that moment incl. all live leases [`policy.persistence`'s projection pattern]
- `pricing_snapshot_id` — addresses per-provider, per-model `PricingTier` records active at named version [`ledger.cost-computation`]; resolution walks pricing-update ledger entries; result is pricing state at that moment supporting deterministic cost computation for replay
- `routing_snapshot_id` — addresses routing-table state (model routing rules, capability-family routing, custom routes) at named version [`routing.route-record`]; resolution walks routing-config-update ledger entries to anchor
- `<custom>_snapshot_id` — registered extension snapshots (KB index snapshot, memory-consolidator state snapshot, active-workspace-tree snapshot); declare: substrate addressed; ledger entry kinds whose events resolution walks; resolution algorithm; canonical event kind emitted when anchored substrate changes; surface-display label; registered through proposal-first [`capability.runtime-mutation`]

### 14.3 Snapshot Anchoring — anchored at specific commit boundaries:
a `ContextVersion`'s `snapshot_refs` map carries snapshot ids of every substrate the commit consulted; a run record carries snapshot ids of every substrate consulted across execution; a capability invocation record carries snapshot ids in effect at invocation's commit; a `RouteRecord` [`routing.route-record`] carries snapshot ids in effect at routing time. Anchor = durable point at which snapshot captured (normally commit boundary's `committed_at` + corresponding substrate sequence position); resolution walks substrate events up to but not beyond the anchor.

### 14.4 Snapshot Resolution `version.snapshot-resolution` — `resolve_snapshot(snapshot_kind, snapshot_id) -> SubstrateState`:
(1) identify substrate by `snapshot_kind`; (2) identify substrate anchor + sequence position by `snapshot_id`; (3) walk substrate's durable event log from substrate's boot or a storage-owned baseline to the anchor; (4) apply each event to substrate's projection; (5) return resolved state. Deterministic given the durable event log; two devices replaying same resolution against same event log produce identical substrate states; if a snapshot cannot be resolved, resolver returns a typed error, never silently falls back to current state.

### 14.5 Snapshot Composition
A single commit may anchor multiple snapshot ids; each resolves independently; combining produces a full substrate snapshot for that commit's run; order of resolution doesn't matter (snapshots are independent substrates).

### 14.6 Snapshot Storage — not stored as copies; storage layer maintains:
per-substrate durable event logs (ledger entries [`ledger.entry-kinds`]); optional per-substrate baselines used only to bound replay length (storage decides whether/how); the `snapshot_refs` map on each `ContextVersion`, run record, etc. Resolution walks event log from relevant substrate baseline (if one exists) to anchor; baselines are storage optimisations + not part of canonical snapshot identity.

### 14.7 Boundary
Snapshots define addressable substrate identity at a durable anchor; substrates (registry, settings, world, policy, pricing, routing) own their own event logs + projection mechanics, this section owns typed snapshot-identity catalogue + resolution contract; resolution machinery owned by substrate's own projection layer.

## 15. Replay Semantics `version.replay-semantics`
### 15.1 Definition
Replay reconstructs past execution state from durable substrates (block pool, version graph, execution ledger, snapshot resolution). Per [`ledger.replay-semantics`], three closed canonical modes:
- `Inspect` — read-only forensic reconstruction; no execution, no side effects
- `SimulateDeterministic` — re-execute deterministic-replayable capabilities [`capability.replay-class`] against captured inputs + snapshot state; produces a new run record but doesn't commit observable side effects
- `FullRerun` — re-execute run from scratch observing all snapshot state at replay time (not capture time); produces a new run record + may commit observable side effects per replay-class declarations

### 15.2 `Inspect` Mode — reads:
the `ContextVersion` at any point in run's path; `VersionDiff` at each commit; materialized view as it was at run's anchor commits (reconstructed by walking from root); `snapshot_refs` on each commit (resolved through §14.4 to substrate state at anchor); block pool's content (File 08); ledger entries the run produced [`ledger.execution-ledger`]. Answers: "What did the model see at the moment of this run's model call?" (resolve materialized view at relevant anchor version; context assembly reconstructs model-request text/content from that view + settings + policy; File 07 reconstructs callable declarations; File 10 ledger entries identify model-call inputs, snapshots, provider invocation records); "What capability calls did this run make + with what arguments?" (read `ToolCallProposed`+`ToolCallExecuted` ledger entries in run's scope); "What was the policy state when this approval was granted?" (resolve `policy_snapshot_id` on the `ApprovalGranted` ledger entry); "What did the workspace look like at this version?" (resolve materialized view's `materialized_paths` [`artifact.materialized-paths-provenance`] at the version). No execution, no side effects, deterministic given durable substrate.

### 15.3 `SimulateDeterministic` Mode
Re-executes capabilities classified `deterministic_replayable` [`capability.replay-class`] against: captured input arguments (read from `ToolCallProposed` ledger entry); captured snapshot state (resolved through §14.4); captured world state [`artifact.observation`'s observation `staleness_fingerprint`]. Re-executed capability produces a result; simulation compares against original `ToolCallCompleted` ledger entry; mismatches indicate non-determinism (or a bug in capability's classification). Capabilities classified `snapshot_replayable` may be re-executed by using captured snapshot state + captured observation's `staleness_fingerprint` to revalidate currency (if world unchanged since observation, simulation proceeds). Capabilities classified `effect_replayable_with_policy`/`not_replayable` not re-executed in `SimulateDeterministic`; results read from ledger but cannot be re-validated by simulation. New run record references replayed source run via `replay_source_run_id`.

### 15.4 `FullRerun` Mode
Re-executes entire run from scratch with replay-time snapshot state; original snapshot anchors read for reference but not enforced; rerun observes whatever substrate state current at replay time (registry, settings, world, policy, pricing). Produces a new run record; if rerun produces observable side effects (writes files, calls APIs, makes purchases) they happen per standard [`run.call-pipeline`] pipeline incl. policy approval. The user-initiated "redo this run with current state" operation; rare + explicit; most replay needs `Inspect`/`SimulateDeterministic`.

### 15.5 Replay Identity — every replay invocation:
carries a `replay_id` (UUID); records `replay_source_run_id`, `replay_mode`, `replay_initiated_at`, `replay_initiated_by`; emits a `ReplayStarted` ledger entry (`Custom { namespace: replay, name: started }`) + a `ReplayCompleted` entry on completion; new run record (`SimulateDeterministic`+`FullRerun` only) references the replay invocation.

### 15.6 Replay-Capability Surface
`provenance.query_replay_trace` [`artifact.provenance`] returns ledger entries that produced any version/artifact/claim. Replay capabilities declared:
- `replay.inspect { run_id, query_kind, query_target }` — read-only forensic query; `permission_floor: Denied`-free; `ReadOnly` tier
- `replay.simulate_deterministic { run_id, capability_filter }` — re-execute deterministic-replayable capabilities; `WorkspaceWrite` tier (new run record is a write)
- `replay.full_rerun { run_id }` — full re-execution; `UserApproval` tier with typed-confirmation [`policy.permission-floor-typed-confirmation`] (replayed side effects may be consequential)

### 15.7 Boundary
Replay reads durable substrates (version graph, ledger, block pool, snapshot resolution) + produces typed results; version graph defines substrate shape, substrates define own content, replay capabilities orchestrate read/re-execution; no part of replay alters the durable substrates of the source run; new runs commit to new substrate state per standard pipeline.

## 16. Version-Graph-Backed Projections `version.version-graph-backed-projections`
### 16.1 Definition
File 01 defines the general `Projection` primitive; this file applies it to projections whose substrate is the version graph, the block pool, or version-anchored snapshot resolution.

### 16.2 Required Contract — every version-graph-backed projection must:
- Declare its substrate — closed set of durable facts it derives from; adding a new substrate is a canonical declaration change
- Declare its rebuild trigger — one of `event-driven`, `on-demand`, or an explicitly configured maintenance trigger; triggers may be combined
- Be rebuildable from the substrate — no projection holds a fact the substrate doesn't produce; complete rebuild produces same projection content (modulo bounded eventual consistency for event-driven projections during a rebuild window)
- Emit `<Projection>Rebuilt` events — every full rebuild emits a typed event through canonical bus (File 10) for downstream consumers + observability
- Tolerate corruption — detected corruption (hash mismatch, stale read, schema-version mismatch) triggers a rebuild; cost is rebuild time never data loss; rows not durable in the source-of-truth sense (rebuildable artifacts)
- Carry a `version` discriminator (when schema may evolve) — storage migrates supported earlier projection versions on load; unsupported versions trigger a rebuild

### 16.3 Canonical Projections:
- `context_view` — active version's view-state over block pool (§7); event-driven; substrate = version graph + block pool + entity records
- per-`ContextVersion` lifecycle/pin maps — derived §10; event-driven; substrate = version-graph action log
- artifact-entity `current_version_block_id` resolution — branch-aware default/latest projection consumed from File 09; substrate = artifact's version chain + active `ContextVersion`
- per-version derived state (`ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`) — derived §10; on-demand; substrate = action log + entity records
- snapshot resolutions — derived §14.4; on-demand at query time; substrate = per-substrate event log
- version-timeline + comparison-diff views — on-demand; substrate = version graph + labels + bookmarks + selected version ids

Adjacent projections (lease state, tool surfaces, retrieval indexes, token caches, workspace mirrors, conversation lists, UI visualisations) owned by their own specs; they may consume the version graph but File 11 doesn't define their full projection contracts.

### 16.4 Custom Projections
Subsystems/plugins may register projection types via proposal-first [`capability.runtime-mutation`]; registered custom projections declare: substrate (block pool, version graph, ledger, registry, settings, world, policy, or registered extension substrates); rebuild triggers; canonical event kinds emitted on rebuild; surface-display rendering hints. Participate in same observability + lifecycle machinery as canonical projections.

### 16.5 Boundary
`Projection` primitive defines the contract; adjacent layers own their own projections; storage layer realises durability of projection state (or chooses not to durably store rebuildable projections); version graph (this file) is the canonical substrate for several projections but is not itself a projection — the version graph is durable state.

## 17. Service Surface `version.service-surface`
### 17.1 Definition
Version graph exposes a canonical operation surface; exact Rust traits, Tauri commands, storage tables, transport bindings are implementation details owned by implementation+storage specs. Canonical requirement: every read/mutation crosses this surface, emits File 10 events/ledger entries where consequential, respects File 06 policy where applicable.

### 17.2 Operation Groups:
reads (current version, version by id, version tree, active materialized view, pending operations, path-spec resolution); pending-buffer operations (apply operation, undo pending, redo pending when enabled, discard pending); commit operations (commit pending operations with a `VersionOpSummary` + snapshot references); navigation (switch to version); labels + bookmarks (label, unlabel, bookmark, unbookmark); forensic + diff queries (diff versions, reconstruct view at version, integrity check); retention + cleanup (tombstone version, compact version range, hard-delete version payload, apply retention policy); cross-conversation (fork conversation).

### 17.3 Read Surface
Deterministic reads. `get_current_version` returns row at `current_version_id`; `get_version_tree` returns typed tree topology (each node with `parent_version_id`, `op_summary`, `committed_at`, `label`, `bookmarked`); `get_context_view` returns materialized view at `current_version_id`; `get_version_at_path` resolves a path expression (e.g. "the version 5 commits back on this branch") to a concrete `version_id`.

### 17.4 Label and Bookmark Operations
`label_version` assigns a user-facing label to a `version_id`; label mutable (relabellable) but the change is itself a typed event in the ledger (`VersionLabelled { version_id, prior_label, new_label }`); label appears in tree view/list view/history panel/comparison board. `bookmark_version` toggles the `bookmarked` flag; bookmarked versions exempt from retention-policy pruning (§20) regardless of policy's age/count thresholds; bookmark is a typed event (`VersionBookmarked { version_id }`).

### 17.5 Service Composition — every version-graph operation:
emits typed events through canonical bus [`ledger.event-stream`]; records consequential operations as ledger entries [`ledger.execution-ledger`]; respects capability policy (File 06); returns `Result<T, AppError>` per `cross-cutting/errors.md`; exposed to surfaces through app's capability/service transport.

### 17.6 Boundary
Service surface defines canonical mutation + read API for the version graph; doesn't define Rust trait, command transport, or physical storage schema.

## 18. Persistence Contract `version.persistence-contract`
### 18.1 What Is Durably Stored:
- the version-graph itself — every `ContextVersion` row survives restart/archival/compaction until explicit tombstoning, reconstruction-preserving compaction, or payload deletion; required durable fields: `version_id`, `conversation_id`, `parent_version_id`, `merge_source_version_ids` when present, `committed_at`, `committed_by`, `op_summary`, `diff`, `label`, `bookmarked`, `snapshot_refs`, `version_schema_version`, `diff_hash`, `expected_view_hash` when present
- the materialized view — `context_view` rows for each conversation's active version are durable; on restart reload from storage; a corrupted/missing materialized view rebuilds from action log
- the pending-operations buffer — `ConversationVersionState` carries `current_version_id`, `pending_ops`, revision/update metadata; durable
- labels + bookmarks — mutations to `label`+`bookmarked` durable through the ledger (`VersionLabelled`, `VersionBookmarked`); latest values stored on the `ContextVersion` row
- `expected_view_hash` records — durable when present; storage layer chooses where

### 18.2 What Is Computed:
per-version `ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`, `TaskRevision` (§10) — derived on demand from action log + entity records; storage may cache as a materialized projection (§16.3) but source of truth is substrate; materialized view rebuilds (derived from action log when on-demand rebuild requested); snapshot resolutions (§14.4); version-tree projection (topology with collapsed linear runs, branch-point markers, bookmark highlights) for tree-view rendering; per-tokenizer token counts of active materialized view [`block.what-is-computed`]; conversation-list metadata (surfaces used, last activity, active status) — derived.

### 18.3 Reconstruction Across Restart — on restart:
version graph reloads from durable storage; materialized views (`context_view`) reload, corruption triggers rebuild; `ConversationVersionState` reloads with `current_version_id`+`pending_ops`; per-version derived state recomputes on first read (or from cached materialized projections); snapshot resolutions recompute on first query; active view a new run sees after restart = same view it would have seen before, modulo offline-interval changes [`block.reconstruction-across-restart`]. In-flight `pending_ops` not committed at restart survive (buffer durable §6.6); if buffer's contents inconsistent with substrate (referenced block hard-deleted between operations), runtime emits `PendingOpsInconsistencyDetected` + discards buffer.

### 18.4 Reconstruction Across Retry, Edit, Reroute, Branch, Child-Run
Per [`run.retry-reroute-branch`], retry/reroute/edit/branch produce new runs linked to prior; version graph records: a retry's new run commits a new branch under the boundary version that triggered (prior run's branch remains); a reroute's new run commits under appropriate boundary per [`routing.mid-execution-reroute`]'s reroute resolution path; an edit's new run commits an `EditMessage` version branch; a branch's new run commits a sibling branch from chosen point. Block pool shared (new run's blocks join same pool); version trees may diverge across branches (one masks a block another keeps active); block records remain singular [`block.reconstruction-across-retry-edit-reroute-branch`]. Child runs [`run.child-runs-multi-agent-work`] commit: isolated child runs — no version commit by child, parent's incorporation step [`run.merge`] records child's typed output as a tool result block in parent's pending buffer, parent's `AgentTurn` boundary commits it; inline child runs — contributions land in parent's pending buffer, parent's boundary commits them as part of parent's turn.

### 18.5 Reconstruction Across Sync
Per §19, cross-device sync preserves version graph's branching topology; concurrent commits on two devices produce sibling branches, no last-write-wins; on sync pull, materialized view stays on local device's `current_version_id`, remote's new commits appended as siblings/different branch in the tree.

### 18.6 Boundary
Persistence is storage layer's responsibility; this section specifies what must be persisted (field set above) + reconstructed (computed views); storage schema/replication/indexing/migration owned by future Storage and Persistence spec.

## 19. Cross-Device Sync and Conflict Resolution `version.cross-device-sync-conflict-resolution`
### 19.1 Definition
Cross-device sync replicates version-graph state across multiple devices using canonical sync transport (future Sync spec); version-tree-aware: concurrent commits on two devices produce sibling branches; no last-write-wins, no implicit merge, no squashing.

### 19.2 Sync Boundary — transport decides which physical records replicate; File 11 specifies only semantic requirements:
replicated version-graph state must preserve `ContextVersion` identity, parentage, merge-source references, diffs, tombstones, labels, bookmarks, snapshot references; replicated block state must preserve immutable block identity + content-addressing semantics from File 08; active `current_version_id` + `pending_ops` are per-device conversation state unless a future Sync spec explicitly defines a shared mode; rebuildable caches, provider rate-limit state, audit-integrity overlays, other per-device projections are not canonical version-graph state.

### 19.3 Conflict Resolution — canonical rule: both branches survive.
Scenario: Device A on `v_X` commits new child `v_Y_A`; Device B also on `v_X` (synced at that moment) commits a different child `v_Y_B`; when devices sync: both `v_Y_A`+`v_Y_B` appear in tree as siblings of `v_X`; neither overwrites; remote's children appended to local's tree; each device's local `current_version_id` remains unchanged (its own most recent commit); a `SyncVersionDiverged { conversation_id, local_version, remote_version }` event fires [`ledger.entry-kind-catalogue` `SyncVersionDiverged`]; UI may notify user of divergence + offer to switch to remote branch. No automatic merge, no last-write-wins, no squash; branching is legitimate (user made different edits on two devices), version tree is the right place to represent that. Block-level concurrent edits never conflict because blocks immutable [`block.edit-semantics`] — concurrent edits produce concurrent sibling blocks, version graph records which sibling is active per branch.

### 19.4 Per-Device Materialized-View Pointer
Each device maintains its own `ConversationVersionState.current_version_id`+`pending_ops`; when sync pulls remote commits, local `current_version_id` doesn't change automatically (local user remains on whatever version they last committed/switched to); remote's commits reachable through tree, user explicitly switches; preserves local-first ergonomics (a remote sync doesn't yank user away from current view).

### 19.5 External Content Sync
Per `infrastructure/sync.md`, binary blobs live outside libsql in a content-addressed external store (`workspaces/<workspace-id>/external/<sha>/<sha>`); on sync pull, blobs fetch on demand at first access (not pre-fetched); blob fetch failures don't break the conversation (affected block resolves to its description per [`block.block-description`] placeholder rendering, user offered option to re-fetch).

### 19.6 Sync Events — canonical sync ledger entry kinds + bus events [`ledger.entry-kind-catalogue`]:
`SyncPulled { version_count, block_count, duration_ms }`; `SyncPushed { version_count, block_count, duration_ms }`; `SyncVersionDiverged { conversation_id, local_version, remote_version }`; `SyncBlobFetched { uri, size_bytes }`; `SyncFailed { reason }`.

### 19.7 Boundary
Sync transport owned by future Sync, Import, Export, and Data Portability spec; this section specifies version-tree-aware merge semantics + per-device materialized-view pointer rule; conflict resolution is canonical contract, transport realises it.

## 20. Garbage Collection and Pruning `version.garbage-collection-pruning`
### 20.1 Definition
User-initiated or settings-driven operations reducing version-graph storage; non-destructive by default [`core.non-destructive-by-default`] — bookmarked versions exempt; tombstones preserve identity for provenance closure [`artifact.artifact-tombstones`]. Canonical mechanisms: `tombstone_version`; `compact_version_range`; `hard_delete_version_payload`; retention-policy-driven cleanup invoking one of those typed operations. `delete_version` may exist as UI shorthand but is not a primitive (must resolve to one of the typed operations).

### 20.2 `tombstone_version(version_id)` — typed user operation that:
requires version to exist + to not be conversation's `current_version_id`; requires version to not be bookmarked unless user explicitly unbookmarks first; requires `permission_floor: Denied`-tier typed-confirmation when version has descendants; preserves version's topology identity (no silent physical row removal, no descendant reparenting); emits `VersionTombstoned { conversation_id, version_id, parent_version_id, has_descendants }`; records a tombstone so provenance queries resolve version as `Tombstoned`. Tombstoning a version with descendants has a hard reconstruction constraint: must either preserve the original diff with per-field content redaction for sensitive material, or replace the diff with a reconstruction-preserving compacted summary that produces identical materialized-view state when applied during a path-walk; if neither achievable because the diff contains irreducibly `Secret` content that cannot be summarised without leaking, operation fails with `TombstoneReconstructionUnsafe { version_id, reason }` (user must then choose `hard_delete_version_payload` explicitly acknowledging reconstruction loss for descendants + recording that loss as a typed provenance gap, or narrow cleanup to a version without descendants). The blocks the version's diff added are not destroyed by tombstoning (remain in unified pool, subject to their own hard-delete contract [`block.hard-delete`]).

### 20.3 Tombstones — a version tombstone retains:
`version_id` (preserved for provenance lookup); `conversation_id` (preserved); `deleted_at`; `deleted_by` (actor identity); `deletion_reason` (typed enum: `UserRequested`, `RetentionPolicy`, `MaintenanceCleanup`, `Custom { code, description }`); version's `committed_at`, `op_summary`, `label` (preserved for inspector display). Tombstone replaces user-visible access to full version row; doesn't erase topology required for path-walk reconstruction; provenance queries traversing through the tombstone receive a typed `Tombstoned` placeholder, reconstruction uses either preserved redacted diff or reconstruction-preserving compacted summary.

### 20.4 `compact_version_range(start_version_id, end_version_id)`
Replaces a linear range of versions with a reconstruction-preserving compacted segment; applies only to linear segments (every version in compacted range must have exactly one child except last, which may have any number); if range includes a branching point, operation fails with `CompactionBranchingPointInRange { version_id }`. Constraint exists because compaction merges sequential diffs into one composed diff; divergent children's diffs computed against different intermediate states + cannot be safely reanchored to compacted endpoint without per-child diff rewriting (a storage-layer optimization not a canonical version-graph operation); user must narrow range to exclude branch point or use per-version `tombstone_version` for non-linear segments.

### 20.5 `hard_delete_version_payload(version_id, payload_scope)`
Physically removes selected payload data from version records/related substrate entries after typed confirmation + closure checks; if descendants/provenance queries lose reconstructability, operation records a typed provenance gap; explicit destructive path, must never be invoked silently by retention policy.

### 20.6 Retention Policies — canonical enum [`domains/coder/checkpoints-undo.md`, `versioning.retention_policy` setting]:
`RetentionPolicy { KeepAll (No expiry); KeepRecentN { n: u32, exempt_bookmarks: bool } (Keep N most recent non-bookmarked); KeepWithin { duration, exempt_bookmarks: bool } (Keep versions newer than given duration); Custom { policy_id, params } (Registered extension) }`. `KeepRecentN`+`KeepWithin` apply to non-current, non-bookmarked, non-labelled versions; bookmarked + labelled versions always exempt regardless of `exempt_bookmarks` (flag governs only how the policy treats unlabelled non-bookmarked versions); policy invokes typed cleanup operations for affected versions. Per File 01 constraint, no time-based pruning fires without explicit user/selected-profile opt-in; retention execution cadence is a settings/profile concern + not a correctness condition; each retention invocation durably recorded (`RetentionPolicyApplied { conversation_id, policy_id, affected_count, applied_at }`).

### 20.7 Hard-Delete Reclamation
A user-initiated "reclaim storage" operation [`core.non-destructive-by-default`] may invoke: `tombstone_version`/`compact_version_range`/`hard_delete_version_payload` for non-bookmarked old versions; `HardDeleteBlock` [`block.hard-delete`] for blocks user no longer wants stored; physical removal of corresponding `external_content_metadata` entries + `external/<sha>/<sha>` blobs when no version-tree row references them. Cleanup respects full version tree not just active view (a version that references a block keeps the block reachable); blocks become eligible for cleanup only when no version in the tree (incl. tombstones) references them [`artifact.materialized-paths-provenance`].

### 20.8 Boundary
GC user-driven + policy-driven; canonical retention-policy enum closes the catalogue; tombstones preserve identity + reconstruction safety; compaction preserves equivalent materialized-view state across linear ranges; hard payload deletion records reconstruction loss when accepted; reclamation surface honours [`core.non-destructive-by-default`]'s storage-management invariant.

## 21. Events `version.events`
### 21.1 Canonical Event Vocabulary — every version-graph operation emits typed events through canonical bus [`ledger.event-stream`]; each also a `LedgerEntryKind` [`ledger.entry-kind-catalogue`]:
Apply and commit:
- `PendingOpApplied { conversation_id, op: ContextOp }` — operation applied to buffer
- `PendingOpUndone { conversation_id, popped_op }` — in-session undo
- `PendingOpsDiscarded { conversation_id, reason, dropped_count }` — buffer discard
- `VersionCommitted { conversation_id, version_id, parent_version_id, op_summary, diff_summary, committed_by, snapshot_refs }` — new version committed

Switching and branching:
- `VersionSwitched { conversation_id, from_version_id, to_version_id, path_length, rebuilt_from_action_log }` — active version changed
- `BranchCreated { conversation_id, branched_from_version_id, new_branch_root_version_id }` — new branch from a non-leaf parent
- `ConversationForked { source_conversation_id, source_version_id, new_conversation_id }` — fork operation

Labels and bookmarks:
- `VersionLabelled { version_id, prior_label, new_label }`
- `VersionUnlabelled { version_id, prior_label }`
- `VersionBookmarked { version_id }`
- `VersionUnbookmarked { version_id }`

Materialized view:
- `MaterializedViewRebuilt { conversation_id, version_id, source: RebuildSource }` — rebuild completed (`RebuildSource` typed enum: `IntegrityViolation`, `ManualRequest`, `Restart`, `SwitchPathTooLong`, `CacheRefresh`)
- `MaterializedViewIntegrityViolated { conversation_id, version_id, expected_hash, actual_hash }` — hash mismatch detected

Deletion and retention:
- `VersionTombstoned { conversation_id, version_id, parent_version_id, has_descendants }`
- `VersionRangeCompacted { conversation_id, start_version_id, end_version_id, compacted_segment_id }`
- `VersionPayloadHardDeleted { conversation_id, version_id, payload_scope, provenance_gap }`
- `RetentionPolicyApplied { conversation_id, policy_id, affected_count, applied_at }`

Inconsistency:
- `PendingOpsInconsistencyDetected { conversation_id, reason, dropped_count }` — buffer state inconsistent with substrate

Domain-specific history-panel, file-revert, surface-display events are `Custom { namespace, name, payload }` extensions declared by their owning specs; File 11 reserves the extension mechanism, doesn't predeclare surface-specific custom events.

### 21.2 Event Sensitivity
Version-graph events default `Public` sensitivity [`ledger.producer-seeded-sensitivity`]; events touching `Secret`-sensitivity blocks (a version commit that hard-deletes a `Secret` block) are `Sensitive`; raw secret payloads never appear in version-graph event payloads [`ledger.sensitivity-aware-persistence-retention` durable ledger rules apply].

### 21.3 Hookable Events — per [`ledger.hook-decision-vocabulary`, `cross-cutting/events.md`], blocking hooks may subscribe to:
`VersionCommitted` (for validators that want to review a commit before it lands + potentially reject; canonical commit-validation pattern); `BranchCreated` (for tooling reacting to new branches, e.g. automated comparison runs); `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted` (for audit-required policies before cleanup). Blocking hook decisions follow canonical typed decision vocabulary [`ledger.hook-decision-vocabulary`] (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`); hook's `priority`+`authority_class` subject to canonical policy [`ledger.priority-ordering`, `ledger.authority-classes`].

### 21.4 Boundary
This file owns the version-graph event kinds above; File 10 owns the envelope, sequence, sensitivity, delivery, hookability, ledger persistence contracts.

## 22. Settings `version.settings`
### 22.1 Configurable Dimensions — every version-graph mechanism configurable via settings [`core.settings-system`, `cross-cutting/settings.md`]; File 11 names dimensions, settings system owns cascade+storage:
Buffer:
- `versioning.in_session_redo_enabled` — whether `redo_pending` supported
- `versioning.switch_with_pending_behaviour` — `Discard`|`Commit`|`AskUser`
- `versioning.pending_buffer_max_size` — soft cap on `pending_ops` length before forcing a `ContextEdit` commit

Materialized-view:
- `versioning.view_integrity_check_strictness` — `Strict`|`CacheAnchorsOnly`|`Off`
- `versioning.strategic_cache_policy` — storage/profile-selected cache placement + eviction policy
- `versioning.strategic_cache_max_count` — optional cap on strategic caches per conversation

Retention:
- `versioning.retention_policy` — typed `RetentionPolicy` enum
- `versioning.retention_apply_trigger` — explicit user/profile-selected trigger for retention execution
- `versioning.cleanup_confirmation_threshold` — typed-confirmation requirements for `tombstone_version`/`compact_version_range`/`hard_delete_version_payload` [`policy.permission-floor-typed-confirmation`]

Branching:
- `versioning.allow_branch_from_non_leaf` — whether commits after switching to a non-leaf produce branches
- `versioning.label_required_on_branch` — whether new branches must have a label

Snapshot:
- `versioning.snapshot_resolution_cache_enabled` — whether snapshot resolutions cache
- `versioning.snapshot_resolution_failure_policy` — how unresolved snapshots surface typed failures

Replay:
- `versioning.replay_default_mode` — profile-selected default replay mode for user-initiated replay (`Inspect`, `SimulateDeterministic`, `FullRerun`)
- `versioning.replay_full_rerun_confirmation` — typed-confirmation requirements for `FullRerun` mode

Sync:
- `versioning.sync_divergence_notify` — whether to notify user when sync produces a divergent branch
- `versioning.sync_auto_switch_to_remote` — whether to auto-switch to remote branch on sync

Agent-exposure [`policy.agent-exposure-policy-settings`]:
- `versioning.version_tree_visible_to_agent` — `OnRequest`|`Hidden`|`InModelRequest`
- `versioning.commit_boundary_set_visible_to_agent` — `InModelRequest` (agent knows boundary kinds)
- `versioning.context_op_vocabulary_visible_to_agent` — `OnRequest` (agent can list operations through `tool.search`); `InModelRequest` for commonly-used subset (Mask, Drop, Pin, Recover)
- `versioning.history_query_capabilities_default_zone` — `Borrowable`|`Primary`|`Disabled` — surface zone for `context.list_versions`, `provenance.query_lineage`, related queries

### 22.2 Settings-Key Convention
`versioning.<dimension>`; per-conversation overrides use File 15's conversation scope; per-subsystem/per-surface/per-capability/per-category variation = namespaced keys resolved through File 15's source stack.

### 22.3 Boundary
This section names dimensions; settings system owns cascade resolution + storage + inspector UI; per-dimension defaults belong to tested settings profiles not hardcoded constants.

## 23. Explicit Rejections `version.explicit-rejections`
- Parallel checkpoint systems — no `file_checkpoints` table, no `SessionCheckpoint`/`FileCheckpoint`/`ToolCallCheckpoint` rows, no shadow-directory checkpoint mechanism, no per-tool-call atomic checkpoint commit; "checkpoint" vocabulary maps onto the unified version graph (checkpoints in any UI are commit boundaries)
- `MessageVersion` rows — messages don't version at row level, the version tree does; "version of message X" view reconstructed by walking the version graph to the version where message X was last edited
- `VersionSnapshot` table separate from version diffs — versioning uses per-version diffs against parent, materialized view rebuilt by walking the tree; storing full snapshots on every version row contradicts compact-diff discipline; strategic-cache nodes (§8.6) store materialized-view caches as storage optimisations not the canonical version-storage shape
- In-place mutation of `ContextVersion` fields — every field except `label`/`bookmarked`/`expected_view_hash` immutable; observable corrections commit a `Correction` sibling §4.2; in-place mutation of `diff`/`op_summary`/`committed_at`/`committed_by`/`parent_version_id`/`snapshot_refs`/any other immutable field invalid
- `pending_ops` buffer as transient in-memory queue — buffer durable on `ConversationVersionState`, survives restart; treating it as in-memory state loses user-applied operations across crashes
- Implicit commit on switch — switching with pending operations must follow configured `versioning.switch_with_pending_behaviour`; an implicit unconfigured commit would bury in-session edits in the wrong place
- Per-operation atomic version commits — fine-grained operations accumulate in `pending_ops`, commit boundary fires one version with net diff; a version per operation creates noise (a 20-operation editing session = 20 versions of incidental detail) + violates "commit at meaningful boundaries"
- Branching that overwrites the prior branch — a commit after switching to a non-leaf creates a sibling branch; overwriting the prior leaf would lose alternate history; canonical mechanism preserves both branches non-destructively
- Last-write-wins for sync conflicts — concurrent commits on two devices produce sibling branches, neither overwrites; `if remote.updated_at > local.updated_at { remote } else { local }` logic invalid
- Squashing or implicit merge of sibling branches at sync — both branches survive; user explicitly switches/merges; merge-source references preserve contribution provenance without changing single-parent tree topology; no implicit merge ever fires
- Snapshot as a stored copy of substrate content — snapshots are typed references to substrate state at a point in time; substrate maintains its own durable event log, snapshot resolves by walking the log; storing duplicate substrate content as a snapshot row violates projection contract + storage-cost discipline
- Token counts or costs stored on `ContextVersion` rows — per [`core.explicit-rejections`], model-dependent scalars never stored as unkeyed values; token counts + costs computed per `(block_id, tokenizer_id)` [`block.what-is-computed`]; version graph never stores them as version-row fields
- Materialized view as the source of truth — materialized view is a projection, version-graph action log is the substrate; treating the view as authoritative leads to corruption when projections fall out of sync; cost of corruption is rebuild never data loss
- Time-based version pruning by default — per File 01 constraint, time-based behaviour invalid unless explicitly justified; time-based policies require explicit user/selected-profile opt-in
- Implicit hard-delete of versions — version cleanup explicit, typed, policy-governed; no automated process hard-deletes versions/payloads without user authorisation
- Descendant reparenting during cleanup — tombstoning/cleaning a version must not silently reparent descendants to a different parent; descendant diffs were computed against their actual parent state
- Compaction across branch points — `compact_version_range` applies only to linear segments; a range containing a branching point must fail with `CompactionBranchingPointInRange`
- Sharing restricted fork blocks by default — cross-conversation forks must omit restricted blocks with `ForkOmitted` placeholders unless explicit policy-approved copy/redaction/scope promotion occurs
- Per-surface version trees — every conversation has one version tree; per-surface views (coder history panel, system-agent rollback DAG, comparison board) are projections of the unified tree; per-surface version trees would fragment the history substrate + break cross-surface composition
- Per-message version structs — versioning happens at conversation-context level not per-message; a "message version" reconstructed by switching versions + observing the active message block
- `updated_at` on block rows — blocks immutable, `updated_at` invalid; per [`block.edit-semantics`] edits create siblings; sync-resolution logic comparing `updated_at` invalid (version graph is the conflict-resolution substrate)
- Time-based mask/drop/lifecycle transitions — per [`block.lifecycle-transition-rules`] + File 01 constraints, no implicit time-based lifecycle transition; compaction policies invoke explicit `Mask`/`Drop` operations driven by own logic never clock time
- Treating `ContextVersion` and `Block` as the same primitive — `ContextVersion` is the version-graph node addressing a conversation's view-state; `Block` is the durable content carrier; a conversation has many versions, each references many blocks, blocks live in the unified pool addressable by any conversation; two distinct primitives that compose
- Treating `Projection` as authoritative for any durable fact — projections are derived; any durable fact existing only in a projection is invalid; substrate must produce the fact, projection reads it
- Snapshot-as-full-model-request-audit — capturing the full assembled model-request context as a separate audit record at every model call is the wrong shape; File 11 reconstructs the materialized view input; File 13/07/10 reconstruct the final model request, callable declarations, snapshots, provider invocation record
- `expected_view_hash` as the source of truth for view content — the hash is a verification artifact, the action log is the substrate; a hash mismatch triggers rebuild never trust-the-hash-over-the-substrate
- Operation sequence as reconstruction source — committed `VersionDiff` is the canonical reconstruction input; operation-sequence ledger facts are audit + UI inspection data; switching + rebuilds must not depend on replaying every pending operation event
- Forging a `VersionCommitted` ledger entry without producing a version row — per [`ledger.forgery-guards`], ledger entries naming a version_id must reference an existing version; orphan references rejected at ledger commit
- Storing per-version aggregate metrics (total tokens, total cost, total blocks) — derived, never stored on the version row; computed on demand from substrate, cached as separate projections §16.3
- Version-graph events emitted outside the canonical bus — per [`ledger.event-stream`], all events flow through the unified bus; side-channel notification for version-graph operations invalid
- Diffs that reference blocks not in the pool — a `VersionDiff` whose `added`/`removed`/`lifecycle_changes`/`pin_changes`/`position_changes` references a non-existent `block_id` is rejected at commit; producing operation undone + re-tried after the block is committed
- Snapshot ids that lack global uniqueness or get reassigned — every snapshot id must be unique within the install, stable, never reused
- Sync of `dag_node_output_cache`, `rate_limit_state`, or audit-log hash chain — explicitly per-device; cross-device sync of any of them violates the projection contract + per-device integrity guarantee

## 24. Consequences for Later Specs `version.consequences-for-later-specs`
- Later specs must not introduce parallel history/checkpoint/rollback/undo/fork/versioning primitives; consume `ContextVersion`, `VersionDiff`, `ContextOp`, snapshots, File 10 events, materialized-view contract defined here.
- Storage + persistence must store required `ContextVersion` fields, `ConversationVersionState`, active `context_view`, labels, bookmarks, tombstones, compacted segments, payload-deletion provenance gaps, hashes when present, snapshot references; physical schema/indexing/migration/storage optimisation remain storage-spec concerns.
- Sync/import/export/portability must preserve version topology, parent links, `merge_source_version_ids`, tombstones, compacted segments, block identity, content-addressing semantics, per-device active pointers unless a later sync spec explicitly defines a shared-pointer mode; last-write-wins remains invalid.
- Context assembly + compaction consume the materialized view as input; compaction that changes durable context state commits explicit `ContextEdit`/`Consolidation`/tombstone/range-compaction operations; must preserve evidence/provenance closure instead of silently severing chains.
- Retrieval, memory, knowledge, artifact, claim, validation, workspace mirror, UI-history surfaces are projections or sibling-block version chains over this substrate; may cache derived views but don't own separate history stores.
- Model strategy, provider, pricing, settings, world, routing, policy, perception, evaluation, replay specs consume snapshot identities + the File 10 ledger to reconstruct past execution state; File 11 provides the version-graph substrate, those specs own their own replay details.
- Extensions, plugins, MCP integrations, workflows, automation, quality control, work surfaces register custom op summaries, context ops, metadata changes, derived-state changes, snapshot kinds, projections through the File 05 proposal-first mechanism; must not bypass the versioning operation surface or the File 06 policy layer.
- UI + customization specs render version timelines, comparison views, history panels, rollback surfaces, inspectors, undo/redo/restore/revert affordances, fork views from the canonical data contracts here; presentation can vary freely, the substrate cannot.

Specific integration contracts stated in those files when written.
