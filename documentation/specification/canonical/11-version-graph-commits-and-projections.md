# Version Graph, Commits, and Projections

## Status

Canonical.

## Scope

This file defines:

- `ContextVersion` — the durable per-conversation version-graph node, its required fields, and its identity
- `VersionDiff` — the typed compact difference recorded on each non-root version, the closed canonical field set, and the hashing rule that protects materialised-view integrity
- `VersionOpSummary` — the closed canonical enum of commit-trigger kinds plus the registered-extension mechanism
- the closed canonical commit-boundary set, expanding the minimum in File 04 §23.4 and aligning with the block-commit boundary set in File 08 §7.6
- the pending-operations buffer (`pending_ops` on `ConversationVersionState`) — accumulation semantics, in-session undo, discard, and the boundary-fires-commit rule
- `ContextOp` — the closed canonical operation vocabulary the user, the agent, hooks, and subsystems apply against the materialised view; per-operation contribution to `VersionDiff`
- the materialised view (`context_view`) — the canonical read-optimised projection of the active version's view-state over the block pool
- version switching — the deterministic path-walk algorithm, the reverse-and-forward diff application contract, and the strategic-cache-node optimisation
- branching and forking — sibling branches as the canonical non-destructive divergence primitive, fork-from-version semantics, and the named cross-conversation fork operation
- per-version derived state maps — `BlockLifecycle` (per File 08 §6.1), `PinState` (per File 08 §6.1), `ArtifactLifecycle` / `ReviewState` / `ValidationState` (per File 09 §5), `ClaimStatus` (per File 09 §9.4) all derived from the version-graph action log
- sibling-block versioning over the block pool — the canonical interaction with File 08 §6.2 edit semantics and the `supersedes` edge
- artifact version chains as a specialisation of sibling-block versioning, including the entity-record `current_version_block_id` pointer (per File 09 §3.2) and the per-`ContextVersion` resolution rule
- `Snapshot` — the closed canonical typed-reference vocabulary the ledger, runs, capability invocations, and replay use to address registry / settings / world / policy / pricing / routing state at a point in time
- version-graph-backed projections — the concrete projection contract used by the materialised view, derived state maps, snapshot views, and version-history surfaces, inheriting the general primitive from File 01 §6.11
- replay semantics — the three closed canonical replay modes (`Inspect`, `SimulateDeterministic`, `FullRerun`) per File 10 §11 and the version-graph data they require
- forensic reconstruction — the "what did the model see at moment X" query surface plus the closed canonical comparison-and-diff operations
- the canonical undo / redo / restore / revert operation set, all expressed through the version-graph mechanism
- the persistence contract — what is durable, what is computed, what is reconstructable, plus the deterministic reconstruction guarantee across restart, retry, edit, reroute, branch, and child-run
- the cross-device sync contract — version-tree-aware merge with no last-write-wins, both-children-survive sibling resolution, and the per-device materialised-view pointer
- garbage collection and pruning — the closed canonical retention policy set, typed tombstone / compaction / payload-deletion operations, and the user-controlled storage-reclamation surface from File 01 §7.13
- the canonical version-graph event vocabulary on the unified event bus (per File 10 §5) — `PendingOpApplied`, `VersionCommitted`, `VersionSwitched`, `BranchCreated`, `VersionLabelled`, `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted`, `MaterialisedViewRebuilt`, `MaterialisedViewIntegrityViolated`
- the settings dimensions every mechanism in this file exposes, with the agent-exposure rules per File 06 §16.4
- the closed set of explicit rejections covering parallel checkpoint systems, mutable diffs, time-based pruning, snapshot-as-full-prompt-audit, version-as-storage-shape, and forgery
- the canonical contract every later spec consumes when it produces a versioned artefact, declares a snapshot identity, builds a derived projection, queries history, or replays an execution

This file does not define:

- the `Block` model, `BlockKind` catalogue, `BlockContent` variants, the block commit validator, sibling-block edit semantics, or hard-delete tombstones — File 08 owns those; this file consumes them
- the `Artifact` entity record field set, `ArtifactKind` catalogue, materialization policy, tombstone shape, or artifact-specific behaviours — File 09 owns those; this file specifies how artifact versions participate in the version graph
- the run lifecycle, capability-call pipeline, retry / reroute / branch mechanics at the run level, cancellation, pending-operations promotion to artifacts, or completion-verification — File 04 owns those; this file specifies which run-level transitions correspond to commit boundaries
- the policy evaluation algorithm, approval flows, lease lifecycle, or contradiction-checking — File 06 owns those; this file specifies that lease state is a projection over policy events (per File 06 §11.6)
- the tool-surface composition algorithm or surface zoning — File 07 owns those; this file specifies that the tool surface is a projection (per File 07 §1) and that registry snapshots address registry state at a point in time
- the `ExecutionLedger` row format, the `EventEnvelope` field set, or the live-bus delivery contract — File 10 owns those; this file specifies which version-graph events flow through the canonical bus and which corresponding ledger entry kinds record them
- the storage on-disk layout, the per-table physical schema, replication mechanics, projection-store realisation, or indexing strategy — the future Storage and Persistence spec owns those; this file specifies what must be durable and what must be reconstructable
- the cross-device sync transport, the libsql embedded-replica mechanics, the conflict-detection pipeline, or import / export bundle format — the future Sync, Import, Export, and Data Portability spec owns those; this file specifies that the version-tree-aware merge is the canonical conflict-resolution semantics
- retrieval, indexing, knowledge-base mechanics, or RAG hybrid-search algorithms — the future Retrieval, Indexing, and Knowledge Base spec owns those; this file specifies that retrieval indexes are projections rebuildable from the durable substrates
- context-assembly, compaction algorithms, token-budget mechanics, or per-policy block selection — the future Context Assembly and Compaction spec owns those; this file specifies the materialised view as the canonical context-assembly input and the typed boundary at which compaction passes commit
- memory promotion, salience scoring, recall, or decay — the future Memory spec owns those; this file specifies that memory entries that consolidate prior blocks are linked via `consolidates` edges from File 08 §5.2 and participate in the version graph as ordinary blocks
- model strategy, provider routing, rate-limit reconciliation, or provider-health tracking — the future Model Strategy and Provider Layer specs own those
- workspace materialization mechanics, materialised-path resolution, disk → block sync, or workspace-tree management beyond declaring that disk state is a projection of the active version's view per File 09 §7.5 — the future Workspaces and Materialization spec owns those
- security primitives, sandbox isolation, or credential management — the future Security, Credentials, Sandbox specs own those
- UI rendering choices for the version-timeline, tree view, comparison-board, history-panel, inspector previews, undo affordances, or accessibility surfaces — the future UI Shell, UI Customization, and per-surface specs own those; this file specifies the canonical data contracts those surfaces consume
- specific evaluation-suite or benchmark schemas — the future Evaluation and Benchmarking spec owns those, though it consumes the replay surface defined here

## Source Resolution

This file is a resolved design, not a summary.

Source families reviewed:

- `documentation/specification/canonical/01-core-thesis-invariants-and-primitives.md`
- `documentation/specification/canonical/02-conversation-intent-and-task.md`
- `documentation/specification/canonical/03-routing-and-dispatch.md`
- `documentation/specification/canonical/04-execution-and-run-model.md`
- `documentation/specification/canonical/05-capability-contracts-and-registry.md`
- `documentation/specification/canonical/06-capability-policy-approvals-and-leases.md`
- `documentation/specification/canonical/07-tool-surfaces-and-capability-loading.md`
- `documentation/specification/canonical/08-blocks-and-block-graph.md`
- `documentation/specification/canonical/09-artifacts-claims-evidence-and-provenance.md`
- `documentation/specification/canonical/10-execution-ledger-event-stream-and-hooks.md`
- `documentation/sources/atlas3-specbase/references/conversation/03-versioning-and-branching.md`
- `documentation/sources/atlas3-specbase/references/conversation/01-core-chat.md`
- `documentation/sources/atlas3-specbase/references/conversation/02-message-operations.md`
- `documentation/sources/atlas3-specbase/references/conversation/06-chat-dag.md`
- `documentation/sources/atlas3-specbase/references/conversation/INDEX.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/blocks.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/composition.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/artifacts.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/events.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/actions.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/settings.md`
- `documentation/sources/atlas3-specbase/references/cross-cutting/state-awareness.md`
- `documentation/sources/atlas3-specbase/references/context/context-assembly.md`
- `documentation/sources/atlas3-specbase/references/context/token-counting-and-tracking.md`
- `documentation/sources/atlas3-specbase/references/infrastructure/database.md`
- `documentation/sources/atlas3-specbase/references/infrastructure/sync.md`
- `documentation/sources/atlas3-specbase/references/infrastructure/lifecycle.md`
- `documentation/sources/atlas3-specbase/references/infrastructure/configuration.md`
- `documentation/sources/atlas3-specbase/references/files/file-management.md`
- `documentation/sources/atlas3-specbase/references/tools/file-operations.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/checkpoints-undo.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/README.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/workspace-management.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/ide-interface.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/git-integration.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/session-logging.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/agent-execution.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/terminal.md`
- `documentation/sources/atlas3-specbase/references/domains/coder/INDEX.md`
- `documentation/sources/atlas3-specbase/references/ui/context-management.md`
- `documentation/sources/atlas3-specbase/references/ui/14-2-chat-list-and-history.md`
- `documentation/sources/atlas3-specbase/references/ui/14-3-streaming-ui.md`
- `documentation/sources/atlas3-specbase/references/agents/agent-execution.md`
- `documentation/sources/atlas3-specbase/references/GLOSSARY.md`
- `documentation/sources/atlas3-specbase/references/foundations/architecture.md`
- `documentation/sources/atlas3-project-knowledge/atlas3-core/CONSTRAINTS.md`
- `documentation/sources/atlas3-project-knowledge/atlas3-core/TODO.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit01-foundations-and-cross-cutting-core.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit02-cross-cutting-infra-and-presentation.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit03-conversation-engine.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit04-routing-agents-prompt.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit08-coder.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit11c-system-agent.md`
- `documentation/sources/atlas3-project-knowledge/unit-specs/unit14-systems.md`
- `documentation/sources/atlas3-project-knowledge/compressed-repos/*`
- `documentation/sources/atlas3-project-knowledge/addendums/*`
- `documentation/sources/existing_ecosystems/*`
- `documentation/sources/codex_recommendations.md`

Resolution rule:

- preserve the unified-version-graph invariant — every conversation has one tree of `ContextVersion` nodes; every artifact / file / knowledge entry / claim version is a sibling block in the unified pool addressed by that tree; there is no parallel checkpoint table, no parallel snapshot store, no per-surface history substrate, no `MessageVersion` row type, no `file_checkpoints` table, no shadow-directory checkpoint mechanism, and no per-tool-call atomic-version path.
- preserve the non-destructive-by-default invariant from File 01 §7.13 — branches are permanent; switching to an earlier version does not destroy the abandoned branch; orphaned branches remain reachable through the version-graph view; physical destruction is explicit, typed, policy-governed, and separated from topology-preserving tombstoning and compaction
- preserve the durable-history-versus-live-coordination separation from File 01 §7.3 — the version graph is durable history; the event bus is live coordination; consequential version-graph operations commit to both (a `LedgerEntry` plus an `AppEvent`), but the version graph itself is the source of truth for "what state existed when"
- preserve the immutability-versus-derived-state separation from File 08 §6 — block content is immutable; per-version view-state (lifecycle, pin, sequence, review, validation, claim status) is derived per `ContextVersion` from the action log over the block pool, never stored on the block row
- preserve File 04 §23.4's pending-operations-buffer and version-commit-boundary contract — fine-grained operations accumulate in `pending_ops`; the boundary fires one version with the net diff; tool-level checkpoints inside a boundary do not become separate version commits; rejecting a checkpoint updates the pending buffer before commit
- preserve File 04 §19's retry / reroute / branch semantics — these run-level operations produce new run records linked to prior ones and may produce a new version branch when they commit accepted output; the version graph records the branch
- preserve File 09 §6's artifact-version contract — `ArtifactVersion` is an `Artifact`-kind `Block` per File 08 §3.1 linked by `supersedes`; the entity record's `current_version_block_id` is a default/latest pointer for non-branch-specific reads; branch-aware surfaces resolve via the active `ContextVersion`
- preserve File 10 §4.1's typed ledger entry kinds for version operations — `VersionCommitted`, `VersionSwitched`, `PendingOpApplied`, `BranchCreated` — and File 10 §5.3's distinction between transient bus-only events and consequential bus-and-ledger events
- preserve File 10 §11's three replay modes (`Inspect`, `SimulateDeterministic`, `FullRerun`) and consume them as the canonical interface to the version-graph data
- preserve File 06 §11.6's pattern of lease state as a projection over policy events, applying the same pattern to the materialised view, derived state maps, and downstream projections — the durable substrate is the action log; everything else rebuilds from it
- preserve the storage-cost discipline — per-version diffs are compact net boundary changes, not full snapshots; the materialised view is a hot projection sized by current view, not by history
- preserve the unkeyed-scalar rejection from File 01 §8 — token counts, costs, and other model-dependent scalars are never stored on `ContextVersion` rows; they are computed per `(block_id, tokenizer_id)` per File 08 §13.2
- preserve cross-device sync without last-write-wins — version-tree-aware merge keeps both concurrent children as siblings; no `if remote.updated_at > local.updated_at` logic; the version graph itself is the conflict-resolution substrate
- treat snapshots as references to durable state at a point in time, not as inline copies — `registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id` are typed cross-references the ledger and execution invocations carry; the snapshot resolves to durable substrate state through replay machinery, not through a parallel snapshot table that duplicates content

Resolved tensions:

- keep the per-conversation version tree (the load-bearing primary mechanism) without forcing per-surface version trees: artifacts, files, knowledge entries, validators, and tool registrations are all blocks; their versioning is sibling-block versioning per File 08 §6.2 over the unified pool, and the conversation's `ContextVersion` tree records when those siblings became active in the view. The unified tree is the only branching topology; sibling-block chains are a derived shape inside the unified pool.
- keep the version graph fast and compact without sacrificing semantic richness: per-version diffs carry typed change sets (`added`, `removed`, `lifecycle_changes`, `pin_changes`, `position_changes`, `hard_deletes`, `metadata_changes`), not action-by-action replay; the diff is the net effect of a commit boundary. Aggregate state at any version is reconstructable by walking the path from root.
- keep snapshot identity addressable without duplicating substrate state: snapshots are typed references with a `kind` and a per-kind addressing scheme. A `registry_snapshot_id` resolves to the per-capability `(capability_id, registered_at_or_before)` state visible to the run; a `settings_snapshot_id` resolves to the cascade-resolved settings tree at the named version; etc. Snapshot resolution is a query against durable substrate, not a stored copy.
- keep cross-conversation forks first-class without creating divergent block pools: `fork_conversation(source_conversation_id, source_version_id)` creates a new conversation whose root version inherits allowed source material by reference; restricted source material is omitted with provenance-preserving placeholders unless explicitly copied, redacted, or scope-promoted through policy. This composes with cross-conversation reference (File 08 §11.3) — forking is the explicit-copy variant; reference is the share-without-copy variant.
- keep the version graph addressable in work-surface UIs (coder history panel, conversation transcript, system-agent rollback DAG, context inspector, comparison board) without per-surface history substrates: each surface is a projection lens over the unified version graph plus the unified block pool. Surface-specific events render the same canonical version operations with surface-specific labels.
- keep replay semantically correct without promising byte-identical reruns for non-deterministic operations: replay class declarations from File 05 §7.3 govern what each capability supports (`deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable`); the version graph plus typed snapshots plus observation `staleness_fingerprint` per File 09 §13 are the inputs; replay machinery composes them per the mode chosen.
- keep undo affordances at every meaningful granularity (last operation, last version, last branch, file-level revert, chunk-level revert) without inventing parallel undo stacks: every undo affordance is either a `pending_ops` pop (pre-commit) or a version switch / new `ContextEdit` (post-commit). The coder surface's chunk-level revert is a `ContextEdit` that swaps the active file block back to a historical sibling.
- keep garbage collection user-controlled, not time-based: retention policies are explicit storage-management choices, not correctness mechanisms. No implicit time-based pruning fires without explicit user or profile opt-in; bookmarked, labelled, current, and provenance-required versions are exempt unless separately confirmed; tombstones preserve identity for provenance closure per File 09 §8 even after content is reclaimed.

## 1. Chosen Model

ATLAS3 has one `VersionGraph` per conversation. It uses the File 01 `Projection` primitive for read-optimised derived views over durable state.

The `VersionGraph` is a tree of `ContextVersion` nodes rooted at the conversation's empty initial state. Every non-root node is a child of exactly one parent and carries one compact typed `VersionDiff` describing the net change from that parent. The tree topology accumulates as commit boundaries fire; the materialised view (`context_view`) holds the active version's fully resolved state for O(1) reads; switching to any other version walks the path between current and target and applies reverse-and-forward diffs to rebuild the view in O(path length); branching is what happens when a new commit is made after switching to a non-leaf version — the new commit becomes a sibling of the prior leaf, and both branches remain permanent and switchable.

This single mechanism handles every product surface that used to feel like a separate "history" feature:

- conversation retry and message edit are commit boundaries (`Retry`, `EditMessage`) that produce new version-tree branches when the prior leaf was not the latest version
- inspector operations (mask, drop, pin, unpin, reorder, group, ungroup) accumulate in `pending_ops`, render live in `context_view` for instant feedback, and commit as one `ContextEdit` version when the boundary fires
- file edits create sibling blocks in the unified pool (per File 08 §6.2); the version graph records the active sibling per `ContextVersion`; reverting a file is either a forward `ContextEdit` that swaps which sibling is active or a backward switch to a version where the historical sibling was active
- artifact-version commits are sibling `Artifact`-kind blocks (per File 09 §6); the artifact entity's `current_version_block_id` updates atomically with each commit; branch-aware surfaces resolve the artifact's effective version through the active `ContextVersion`
- compaction passes commit `ContextEdit` versions whose diff records mask / drop / consolidate changes; restoring a compaction is the same operation as switching to any other version
- system-agent rollback is a surface projection of the version-tree branching the system-agent operations produced
- quality-control corrections produce sibling versions: the rejected candidate becomes the alternative branch the user can switch to with one click
- the coder surface's "checkpoints and undo" feature is a UI projection over the version tree; every checkpoint visible in that timeline corresponds to one `context_versions` row

There is no parallel checkpoint table, no `file_checkpoints` row type, no `SessionCheckpoint` / `ToolCallCheckpoint` / `MessageVersion` / `VersionSnapshot` type, no per-tool-call atomic version commit, and no shadow-directory snapshot mechanism. The pre-canonical specbase explicitly named and deleted those vocabulary variants in favour of the unified version graph; this file confirms the deletion and reserves the canonical names.

File 01 owns the general `Projection` primitive. This file applies that primitive to version-graph-backed projections: the materialised view, per-`ContextVersion` lifecycle and pin maps, snapshot resolutions, version timelines, comparison diffs, and version-aware surface lenses. Adjacent layers may define their own projections over the same substrates, but they inherit File 01's rule: projections are rebuildable, non-authoritative read models whose corruption costs rebuild time, never data loss.

The version graph composes with adjacent layers:

- File 08 owns the block pool and the sibling-versioning rule; this file owns the per-`ContextVersion` view over the pool
- File 09 owns the artifact entity records, materialization policies, and entity-relevant events; this file owns the version-graph membership of artifact versions and the per-`ContextVersion` artifact-lifecycle / review-state / validation-state derivation
- File 10 owns the unified `ExecutionLedger` and `EventStream`; this file owns the canonical version-graph events and ledger entry kinds, all emitted through the canonical bus and recorded with the canonical envelope
- File 04 owns the run lifecycle and the canonical commit-boundary list as a minimum; this file expands and closes the boundary catalogue
- File 06 owns lease lifecycle and approval; this file owns the version-graph commits that record lease grants and reuses File 06's "projection over events" pattern for the materialised view
- File 07 owns tool-surface composition; this file owns the registry-snapshot identity that anchors a run's surface composition for replay

`ContextVersion` supersedes any earlier vocabulary that named the same primitive: "version node", "history snapshot", "context snapshot", "chat state node", "checkpoint commit", "session checkpoint", "context-version row". `VersionDiff` supersedes "version delta", "context diff", "snapshot diff". `VersionOpSummary` supersedes "commit type", "version reason", "version label". `ContextOp` supersedes "context operation", "atomic context change", "inspector action". `Snapshot` supersedes "snapshot id", "frozen state record", "point-in-time reference". `Projection` supersedes "derived view", "materialised view", "read model", "computed view", "cache" (when applied to durably-derivable read-side data). Earlier names from source material map into these canonical typed shapes.

## 2. Boundaries with Adjacent Layers

### 2.1 With File 01 (Core Thesis, Invariants, and Primitives)

File 01 §6.10 declares `Versioned Durable State` as a canonical primitive whose purpose is "undo, branching, inspection, and deterministic reconstruction." File 01 §6.11 declares `Projection` as a canonical primitive whose rules are "every projection must be rebuildable from its source-of-truth data; projections must declare their rebuild trigger (event-driven, on-demand, or periodic); projections are not the source of truth for any durable fact; the cost of a stale or corrupted projection is a rebuild, never data loss." This file elaborates both primitives into the version-graph machinery and the general projection contract.

File 01 §7.3 establishes the durable-history-versus-live-coordination separation; this file's version graph is the durable history substrate and emits through the live bus per File 10. File 01 §7.13 establishes non-destructive-by-default and the user-controlled storage management surface; this file's branching, switching, garbage collection, tombstoning, compaction, and payload-deletion operations honour both. File 01 §8 forbids unkeyed model-dependent scalars; this file forbids storing token counts, costs, or any such scalar on `ContextVersion` rows.

### 2.2 With File 02 (Conversation, Intent, and Task)

File 02 establishes that a conversation versioning unit operates at the conversation-context level, not per-message (`No MessageVersion struct`), and that branching (sibling at same parent) and forking (new conversation seeded from a chosen message) are the canonical conversation-versioning operations. This file specifies the underlying mechanics. File 02 §6's revision-safe task updates are commits in the version graph whose `op_summary` is `TaskRevision` — the task's revision counter advances when a commit lands on the path between the task's prior revision-commit and the new branch head; concurrent updates produce sibling branches per the canonical branching rule.

### 2.3 With File 03 (Routing and Dispatch)

File 03 §3.5 specifies the `Route Record` as a durable record produced at routing time. The Route Record carries `routing_snapshot_id` (which resolves to the routing-table state at routing time per §13 below), `policy_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, and `registry_snapshot_id`. The route record itself becomes part of the version graph through the `RouterEmission` block producer per File 08 §2.2; replay reads the route record's snapshot references to reconstruct the routing inputs deterministically.

### 2.4 With File 04 (Execution and Run Model)

File 04 §23.4 enumerates a minimum commit-boundary set ("user message, accepted agent turn, accepted artifact revision, accepted task revision, retry branch, edit branch, context edit, import/export operation"). §5 of this file closes the canonical catalogue, expanding the minimum with the inspector-apply, workflow-node-complete, consolidation, manual-draft-commit, and subsystem-internal-boundary cases from File 08 §7.6. File 04 §23.4 also defines the pending-operations buffer that accumulates between boundaries and commits as one durable net change; §6 of this file specifies the buffer's typed shape and operation contract.

File 04 §19 specifies retry, reroute, and branch as run-level operations that do not interfere with the prior in-flight run (default: prior run continues; new run becomes a linked parallel attempt; both remain accessible as distinct versions). The version graph records each as a branch from the appropriate boundary. The new run's commits land as children of the boundary version that triggered the retry / reroute / branch.

File 04 §17.1 specifies the `control` field on a `Run`; when control flips to `User`, subsequent user actions are recorded as first-class blocks attached to the run, and the version graph records the takeover-end commit when control returns. Takeover blocks participate in the same `pending_ops` buffer the agent uses.

File 04 §22's completion-forgery guard is enforced at the ledger commit boundary (per File 10 §3.7); the version-graph commit that records run completion does not commit unless the guard passes — but the guard does not depend on the version graph itself, only on the ledger entries the run's scope produced.

### 2.5 With File 05 (Capability Contracts and Registry)

File 05 §7.3 declares the per-capability `replay_class` (`deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable`). This file consumes the replay class in §14 to select the appropriate replay mode for each invocation in a run being replayed.

File 05 §10 records the registered-capability runtime state. A `registry_snapshot_id` resolves to the registered-capability set at the named version, including `enabled` flags, `availability_status`, `resolved_backend_binding`, `trust_state`, `active_aliases`, and the registered declaration version. The snapshot is derivable from the durable substrate (the canonical capability declarations plus the recorded registry-state mutation events with their typed timestamps) per File 10 §11.

### 2.6 With File 06 (Capability Policy, Approvals, and Leases)

File 06 §11.6 establishes that "lease state is a projection over policy events" — the canonical pattern this file generalises into the `Projection` primitive contract (§16). Lease state at any moment is computed from `LeaseGranted` / `LeaseRevoked` / `LeaseNarrowed` / `LeaseStale` ledger entries plus the current world snapshot's lease-evidence facts. The version-graph commit at policy decision time captures the `policy_snapshot_id` and the contributing scopes.

A `policy_snapshot_id` resolves to the active policy rule set, lease set, approval template set, and contradiction-check rules at the named version. The snapshot is derivable from the durable policy-event substrate per the same projection rebuild contract.

### 2.7 With File 07 (Tool Surfaces and Capability Loading)

File 07 §1 establishes that a `ToolSurface` is "a typed projection over the Capability Registry" — another instance of the canonical `Projection` primitive this file generalises. File 07 §14's reconstruction contract — "reconstruction across retry, edit, reroute, branch, and child-run spawn is deterministic from current inputs" — is the same contract this file specifies for the materialised view across the same operations. The registry snapshot anchors the surface composition for replay.

### 2.8 With File 08 (Blocks and Block Graph)

File 08 owns the block pool, the `BlockKind` catalogue, the `BlockEdge` catalogue, the block commit validator, sibling-block edit semantics, hard-delete tombstones, and the canonical block-commit boundary set in §7.6. This file consumes those boundaries as the canonical commit-boundary set (§5) and specifies the per-`ContextVersion` view over the pool. File 08 §6 declares `BlockLifecycle` and `PinState` as derived per-`ContextVersion` view-state; §10 of this file specifies the derivation algorithm and the materialised-view representation.

File 08 §5.2's `supersedes` edge is the canonical sibling-block versioning mechanism this file consumes for artifact version chains (§12), file edits, message edits, knowledge-entry edits, validator and adapter updates, and every other case where observable content changes through "create a sibling block, swap the active reference in the materialised view, record the swap in the diff."

File 08 §11's block scope (`run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule`) bounds version-graph membership: a `ContextVersion` row is conversation-scoped; the materialised view it projects sees blocks at conversation scope and broader; narrower-scoped blocks (run-scoped, intent-thread-scoped) are visible to the runs and threads that produced them.

### 2.9 With File 09 (Artifacts, Claims, Evidence, and Provenance)

File 09 §6 specifies that `ArtifactVersion` is an `Artifact`-kind block per File 08 §3.1 linked by `supersedes`, and that artifact lifecycle / review state / validation state are derived per `ContextVersion` from the version-graph action log. This file specifies the action-log shape (§4) and the derivation rules (§10) those entity states consume.

File 09 §15 establishes the canonical provenance query surface (`query_lineage`, `query_evidence_set`, `query_contributing_runs`, `query_contributing_capabilities`, `query_replay_trace`, `query_derivation_chain`, `contradiction_check`, `query_artifact_versions`); §15 of this file specifies the forensic reconstruction surface those queries consume.

### 2.10 With File 10 (Execution Ledger, Event Stream, and Hooks)

File 10 §3 specifies the durable `ExecutionLedger`; this file's version-graph commits become ledger entries (`VersionCommitted`, `VersionSwitched`, `BranchCreated`, `PendingOpApplied`, `VersionLabelled`, `VersionTombstoned`, `VersionRangeCompacted`, `VersionPayloadHardDeleted`, `MaterialisedViewRebuilt`, `MaterialisedViewIntegrityViolated`) and flow through the canonical event bus with the canonical envelope. File 10 §11 establishes the three replay modes; this file specifies the version-graph data each mode consumes.

File 10 §3.7's forgery guards do not apply to version-graph commits in addition to the existing guards — version-graph commits are themselves the carriers of the consequential transitions, and the ledger's existing rules (status-transition forgery, unkeyed-scalar rejection, sensitivity-aware persistence) govern them at the ledger commit boundary.

### 2.11 Boundary

This file is the durable-state-versioning and read-projection layer. It owns:

- the `ContextVersion` shape and the version-graph topology
- the `VersionDiff` field set and the `VersionOpSummary` enum
- the canonical commit-boundary set
- the `ContextOp` operation vocabulary and the `pending_ops` buffer contract
- the materialised view's shape and rebuild contract
- the canonical version-switching algorithm
- the per-`ContextVersion` derived-state derivation rules
- the canonical snapshot identity catalogue and resolution contract
- the `Projection` primitive contract
- the forensic reconstruction query surface
- the cross-device sync model
- the explicit rejections
- the consequences other specs consume

It does not own:

- the block schema, edge catalogue, or sibling-block edit mechanics (File 08)
- the artifact entity record schema or materialization policy (File 09)
- the ledger row schema, event envelope, or hook contract (File 10)
- the run lifecycle or capability-call pipeline (File 04)
- the policy evaluation algorithm or lease lifecycle (File 06)
- the tool-surface composition algorithm (File 07)
- the storage on-disk layout or sync transport (future specs)
- the UI rendering of timelines, comparison boards, or inspectors (future UI specs)
- the retrieval / context-assembly / compaction algorithms (future specs)

## 3. `ContextVersion`

### 3.1 Definition

A `ContextVersion` is the durable, immutable, identified node of the conversation-context version graph. Each version represents one committed state of the conversation's context: the set of blocks active in the view, their order, their per-version lifecycle and pin state, and the per-version derived state every adjacent entity layer reads. Versions are the substrate every projection in this file rebuilds against, every snapshot resolves against, and every replay mode reads from.

A `ContextVersion`:

- has stable identity (`version_id`); never reassigned, never reused, never mutated after creation
- is owned by exactly one `conversation_id`; cross-conversation reference uses fork (§9.3) or block-level reference (File 08 §11.3), never shared `version_id`
- has at most one `parent_version_id`; the root version of each conversation has `parent_version_id = null`
- may carry merge-source references when a commit intentionally combines branches; these references are provenance, not tree parentage
- carries one immutable typed `VersionDiff` (§4) describing the net change from its parent
- declares one `VersionOpSummary` (§5.2) identifying the commit-trigger kind
- carries an optional user-assigned `label` for surface display and named-bookmark reference
- carries the typed snapshot references (`registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id`, others §13) anchored at the commit time, when the corresponding substrate was consulted
- carries the `producer` reference (matching File 08 §2.2's `producer` enum) — the actor that committed the version
- is durable across process restart, conversation archival, projection rebuild, schema migration, and version-graph compaction
- is addressable across every layer: the execution ledger references `version_id` per File 10 §3.6; the materialised view consumes `version_id` per §7; the artifact entity's `current_version_block_id` denormalised pointer resolves through `version_id` per File 09 §3.2; the surface composition record references the `version_id` at which the surface was consumed per File 07 §14

A `ContextVersion` is not:

- a snapshot of full prompt context — assembled prompts are reconstructable from the materialised view at the version, not stored on the version row
- a copy of block content — content lives in the block pool per File 08; the version references blocks by `block_id`
- a UI element — surfaces (the conversation transcript, the coder history panel, the comparison board, the inspector timeline) are projections of the version graph; the canonical row is independent of presentation
- a row in any single storage backend — the storage layer chooses physical layout subject to the persistence contract (§18)
- a transient coordination signal — those are `AppEvent`s on the event bus per File 10 §5; the version is durable history
- mutable — every observable change to a version commits a new sibling or supersession version, with the prior version preserved

### 3.2 Required Fields

Every `ContextVersion` carries at minimum:

- `version_id` — globally stable UUID (v4 or v7 per CONSTRAINTS.md §15); never reassigned, never mutated
- `conversation_id` — owning conversation; immutable
- `parent_version_id` — `Option<version_id>`; `None` for the conversation's root version; immutable
- `merge_source_version_ids` — optional set of additional source versions when a commit intentionally combines branches; immutable; absent for ordinary linear or branch commits
- `committed_at` — full-granularity timestamp of commit (when the boundary fired, not when operations started)
- `committed_by` — typed `producer` reference per File 08 §2.2: `UserMessage { user_id }`, `CapabilityCommit { capability_id, invocation_id }`, `RouterEmission { route_id }`, `InspectorApply { inspector_lens, user_id }`, `WorkflowNode { workflow_id, node_id }`, `Import { source_kind, source_ref }`, `Consolidation { policy_id, source_block_ids }`, `Subsystem { subsystem_id, reason }`
- `op_summary` — `VersionOpSummary` enum value (§5.2)
- `diff` — `VersionDiff` payload (§4)
- `label` — optional `String`; user-assigned name; mutable through the `label_version` operation (§17.4), not through diff updates
- `bookmarked` — `bool`; user-marked retention preference exempting the version from garbage-collection retention policies (§19.4); mutable through the `bookmark_version` operation
- `snapshot_refs` — typed map of snapshot identities the version anchors (§13): `registry_snapshot_id`, `settings_snapshot_id`, `world_snapshot_id`, `policy_snapshot_id`, `pricing_snapshot_id`, `routing_snapshot_id`, plus registered extension keys; entries unused for a given commit are absent rather than null-padded
- `version_schema_version` — version of the canonical row shape, so the future Storage spec can normalise supported earlier shapes during registration
- `diff_hash` — SHA-256 over the canonical serialised `VersionDiff` payload; supports materialised-view integrity verification (§7.6) and forgery guards (§19.5)
- `expected_view_hash` — optional SHA-256 over the canonical serialised materialised view at this version, used as an integrity sentinel for path-walk verification (§7.6 and §8.4); present when the storage layer chose to record it; absent versions are still valid

The `diff`, `snapshot_refs`, `committed_at`, `committed_by`, `op_summary`, `version_id`, `parent_version_id`, `merge_source_version_ids`, `conversation_id`, `version_schema_version`, and `diff_hash` fields are immutable for the version's lifetime. `label`, `bookmarked`, and `expected_view_hash` are mutable through the explicit operations named in §17 and §7.6; mutations emit typed events and ledger entries.

### 3.3 Identity

A `version_id` is:

- globally unique within the ATLAS3 installation
- assigned at commit time
- never reused, never reassigned, never mutated
- the canonical cross-layer reference: ledger entries (per File 10 §3.6's `version_id` cross-reference key), block-pool queries (per File 08 §13.2's per-version lifecycle map keying), artifact-entity surface resolution (per File 09 §5.4), tool-surface reconstruction (per File 07 §14.3), replay invocations (§15 of this file), forensic queries (§16), and cross-conversation forks (§9.3)
- a UUID (v4 or v7) per the project-wide UUID schema invariant (CONSTRAINTS.md §15)

A version's identity is independent of its content. Two versions with identical `VersionDiff` content have different `version_id`s. Deduplication is not required and is explicitly not attempted; equal-content versions are addressable separately and can carry independent labels, bookmarks, and produced-by attributions.

### 3.4 Boundary

The `ContextVersion` defines durable version-graph identity and the immutable per-version metadata. The block pool owns block content. The materialised view (§7) projects the active version's view-state over the block pool. The ledger records the events that produced each commit. The version graph itself is an append-only tree over immutable `ContextVersion` rows; mutations to label, bookmark, or expected-view-hash are recorded as typed events but do not alter the immutable fields.

## 4. `VersionDiff`

### 4.1 Required Shape

Every non-root `ContextVersion` carries one `VersionDiff` describing the net change from its parent. The diff is compact by design: only changes are recorded; unchanged blocks, lifecycle states, pin states, and positions are not enumerated. The closed canonical field set:

- `added` — `Vec<(BlockId, Position)>` — blocks newly active in this version's materialised view, with their position in the sequence
- `removed` — `Vec<BlockId>` — blocks removed from the materialised view in this version (lifecycle transitioned to `Dropped` from any prior `Active` / `Masked` / `Recovered`, or block was unreferenced after a child-removal in a `Composed` parent that this version supersedes)
- `lifecycle_changes` — `Vec<(BlockId, BlockLifecycle, BlockLifecycle)>` — per-block lifecycle transitions in this version's view: `(block_id, from_state, to_state)` where states are drawn from `BlockLifecycle` per File 08 §6.1 (`Raw`, `Active`, `Masked`, `Dropped`, `Recovered`)
- `pin_changes` — `Vec<(BlockId, PinState, PinState)>` — per-block pin transitions in this version's view: `(block_id, from_state, to_state)` where states are drawn from `PinState` per File 08 §6.1 (`Unpinned`, `Pinned`, `Protected`)
- `position_changes` — `Vec<(BlockId, Position)>` — blocks whose sequence position changed in this version's view, with their new position
- `metadata_changes` — `Vec<MetadataChange>` — typed per-block metadata changes that the version-graph layer tracks (sensitivity-tag override applied at this version, description regeneration sibling activated, scope promotion projection adopted); each `MetadataChange` is a closed enum drawn from the canonical set in §4.3
- `hard_deletes` — `Vec<BlockId>` — blocks that this version's commit physically destroyed (per File 08 §6.6); the affected blocks have transitioned to tombstones; this change is irreversible by version switch; switching to a version where the block was active produces a tombstone placeholder (per File 08 §6.6's materialised-by fallback)
- `derived_state_changes` — `Vec<DerivedStateChange>` — typed per-entity derived-state transitions that the version graph computes at commit: `(ArtifactReviewState, artifact_id, from, to)`, `(ArtifactValidationState, artifact_version_block_id, from, to)`, `(ClaimStatus, claim_id, from, to)`, plus registered extension entries; documented in §10

`Position` is an integer in `[0, view_size)` denoting the block's index in the active version's render-order sequence. Positions are not stable identifiers; the same block at different versions may occupy different positions.

The diff is the net effect of all `ContextOp`s accumulated in `pending_ops` between the prior commit and this one (§6). If a user masks a block, unmasks it, and then commits, neither change appears in the diff — the net effect is zero. If the same block is added, removed, and added again at a different position, only the final add-at-position entry appears.

### 4.2 Storage and Serialisation

`VersionDiff` is stored as a single typed payload on the `context_versions` row. Storage may use JSON, MessagePack, CBOR, Protobuf, or any serialisation that preserves the typed shape; the canonical contract is the field set and the per-field type, not the byte-level encoding. The per-row diff is compact: a typical agent turn commits ~3–10 entries; a context-edit commit accumulating an editing session commits ~5–50 entries; an import commit committing a large block group may carry several hundred entries.

The diff is immutable for the version's lifetime. Corrections to a diff (a malformed entry detected in the field, a missed `lifecycle_change` discovered through audit) commit a new sibling version with `op_summary: Correction` and a `diff` that applies the correction; the prior version remains in the pool with the original diff intact. This preserves replay determinism — a replay reading the prior version sees the original (possibly malformed) diff and reproduces the historical behaviour; the corrected sibling becomes the new active version going forward.

### 4.3 Canonical `MetadataChange` Catalogue

`metadata_changes` carries typed entries from the closed canonical set:

- `SensitivityOverrideApplied { block_id, prior, new, field_path: Option<JsonPath> }` — block sensitivity raised at this version (per File 08 §9; lowering requires a typed-confirmation policy override and emits the same change with `prior > new`)
- `DescriptionRegenerated { old_block_id, new_block_id }` — the block's description was regenerated through the canonical regeneration capability, producing a sibling block (per File 08 §10.4); the diff records the supersession
- `ScopePromotionAdopted { source_block_id, projection_block_id, source_scope, target_scope }` — a `scope_projection_of` or `promotes_scope_of` edge was committed (per File 08 §11.2); the diff records that the promotion projection is now visible at the broader scope
- `MaterializationRecorded { block_id, materialised_paths }` — the active version's render of this block has a recorded materialisation footprint at the named workspace paths (per File 09 §7.4); used by the disk → block sync loop
- `Custom { namespace, name, payload }` — typed extension entries registered through the canonical proposal-first mechanism (per File 05 §16.2)

### 4.4 Per-Entity Derived-State Change Catalogue

`derived_state_changes` carries typed entries from the closed canonical set:

- `ArtifactReviewState { artifact_id, version_block_id, prior, new }` — explicit review-state change (per File 09 §5.2)
- `ArtifactValidationState { artifact_version_block_id, prior, new, validation_block_id }` — derived validation state transition from `validated_by` edge addition (per File 09 §14.2)
- `ArtifactLifecycle { artifact_id, version_block_id, prior, new }` — derived artifact-lifecycle transition (per File 09 §5.1); typically computed at read time, but recorded on the version when the change derives deterministically from the commit's contents (a new version commit moves the prior version to `Superseded`)
- `ClaimStatus { claim_id, prior, new, derivation_reason }` — derived claim-status change from evidence-link set change (per File 09 §9.4)
- `TaskRevisionAdvanced { task_id, prior_revision, new_revision }` — revision-safe task-update commit (per File 02 §6.3)
- `IntentThreadContinuitySummaryRecorded { intent_thread_id, summary_block_id }` — continuity-summary block committed at a thread boundary (per File 02 §5.3)
- `Custom { namespace, name, payload }` — typed extension entries

These derived-state changes are recorded on the version commit when the change derives deterministically from the commit's contents (an evidence-link addition that flips a claim from `Unresolved` to `Supported`; an artifact-version commit that moves the prior version to `Superseded`). Pure read-time recomputation that does not involve a substrate change does not record on a version; entity-derived state is recomputed on demand per File 09 §5.4.

### 4.5 Hashing

The `diff_hash` field on `ContextVersion` (§3.2) is SHA-256 over the canonical serialised `VersionDiff` payload plus the `version_schema_version` discriminator. The hash supports:

- materialised-view integrity verification at path-walk strategic-cache nodes (§7.6, §8.6)
- forgery detection — a stored diff whose hash does not match recomputed-from-payload triggers a `MaterialisedViewIntegrityViolated` event and forces a rebuild from the action log
- cross-device sync deduplication — two devices that committed the same operation at the same parent under deterministic conditions produce identical `diff_hash`es (though typically `version_id` differs); the sync layer may use the hash to confirm a sibling is identical to a remote sibling before suppressing duplicate-sync notifications

The hash is `NOT NULL` and immutable.

### 4.6 Boundary

The `VersionDiff` defines what changed at a commit. The materialised view (§7) is the integrated result of applying every diff on the path from the root. The ledger (per File 10) records the events that produced each commit. The hash supports integrity verification but is not a forgery guard at commit (the diff itself is the authority); it is a verification artifact for replay and rebuild.

## 5. `VersionOpSummary` and the Commit Boundary Set

### 5.1 Definition

A commit boundary is the point at which `pending_ops` (§6) flushes into a new `ContextVersion`. Boundaries are not implicit — every commit fires from a typed trigger, every trigger produces a `VersionOpSummary` value identifying the kind, and every commit boundary corresponds to a `BlockCommitted` boundary in File 08 §7.6 plus a `LedgerEntry` of kind `VersionCommitted` in File 10 §4.1.

### 5.2 Closed Canonical Catalogue

Every `ContextVersion` declares its `op_summary` at commit. The canonical closed catalogue:

**Transcript-anchor boundaries (conversation level):**

- `UserMessage` — user submitted a new message; the diff adds the user's `MessageUser` block and any attached children
- `AgentTurn` — an assistant turn reached accepted final state (per File 04 §6 lifecycle step 8); the diff adds the `MessageAssistant` block plus its constituent `ToolCallProposal`, `ToolResult`, `ReasoningTrace`, `Failure`, `ToolDenial`, `Observation`, and text children, plus any context operations the agent performed during the turn
- `EditMessage` — a user-message edit (per File 02 §3.1) produced a sibling block; the diff records the swap (the prior `MessageUser` block transitions to `Removed` from the active view; the new sibling becomes `Active`); downstream blocks dependent on the prior message become orphans per File 02 §3.1 unless retry produces a new branch
- `Retry` — a user clicked retry on a message; the diff adds the new response block(s) as siblings to the prior, sharing the same `parent_block_id` (per File 02 §3.1 and File 04 §19.1)

**Inspector / manual-edit boundaries:**

- `ContextEdit` — one or more `ContextOp` operations (mask / drop / pin / reorder / group / ungroup / etc.) committed through user "Apply" or through the canonical commit capability; the diff records the net effect of the accumulated operations
- `ContextEditWithLabel` — same as `ContextEdit` but the user explicitly assigned a label at commit time

**Capability-execution boundaries:**

- `CapabilityCommit` — a capability invocation completed and committed produced blocks (per File 04 §8.2 pipeline step 10); used when the capability is not the assistant's `respond_with_tools` loop (which commits as `AgentTurn`) but a standalone invocation (an inspector-initiated capability call, a workflow node, an automation trigger)
- `WorkflowNodeComplete` — a workflow node committed its declared output (per File 04 §5.3 graph or workflow execution); the diff records the produced blocks for the node
- `Consolidation` — a compaction or consolidation pass committed (per File 08 §6.5 group / File 08 §3.1 `Consolidation` block kind); the diff records the `Consolidation`-kind block plus the masked / dropped source blocks via `lifecycle_changes`

**Routing boundaries:**

- `RouterEmission` — the router emitted a `RouteRecord` per File 03 §3.5 that produced visible blocks (a routing explanation block, a routing-decision capability call); typically nested inside a parent `AgentTurn` or `UserMessage` boundary but may stand alone for automation runs

**Entity boundaries (when a single entity transition justifies a standalone commit):**

- `ArtifactVersion` — an artifact-version commit (per File 09 §6.3) that stands alone (outside an `AgentTurn` or workflow); the diff carries the `ArtifactCreated` or `ArtifactVersionCommitted` derived-state change
- `TaskRevision` — a revision-safe task update (per File 02 §6.3) commits with this `op_summary` when not nested inside an `AgentTurn`; the diff carries the `TaskRevisionAdvanced` derived-state change
- `ClaimPublication` — `claim.publish` capability committed (per File 09 §10) outside of an `AgentTurn`; the diff records the `Claim`-kind block and the `ClaimStatus` derived-state change
- `EvidenceLink` — `evidence.link` committed an evidence-link edge outside of an `AgentTurn`; the diff records the edge metadata change
- `ValidationRun` — a validation run committed a `Validation` block outside of an `AgentTurn`

**Import / portability boundaries:**

- `Import` — a block group imported from another conversation (per File 02 §3) or from a portable export bundle; the diff records the imported blocks with `producer: Import { source_kind, source_ref }`
- `Export` — the version graph records the export operation; the diff is typically minimal (no view-state change) but the version carries the export's anchor identity for later cross-installation reference

**Workspace / disk-sync boundaries:**

- `ExternalEdit` — the filesystem watcher detected an external edit to a materialised file and committed a sibling block per File 09 §7.5; the diff records the swap

**Recovery / correction boundaries:**

- `Correction` — a malformed prior version's diff is being corrected by a new sibling version (per §4.2); used rarely; the diff records the corrected state
- `Recovery` — a partial-output orphan was promoted to a durable block on cooperative-stop recovery (per File 04 §17.3); the diff records the promoted orphan as added to the view

**Subsystem boundaries:**

- `Subsystem` — a substrate subsystem (Memory consolidator, knowledge-base curator, scheduler) committed its internal boundary; the diff carries the subsystem's produced blocks and the `committed_by: Subsystem { subsystem_id, reason }` attribution
- `Automation` — an automation trigger fired and produced blocks; the diff carries the produced blocks and the `committed_by` attribution naming the automation

**Extension:**

- `Custom { namespace, name }` — subsystem-specific commit-boundary kinds registered by a subsystem, plugin, or user-defined extension. The `namespace` matches the canonical sourcing taxonomy from File 05 §9.1; the `name` is the kind id within that namespace. Custom op-summaries register through the proposal-first mechanism (per File 05 §16.2) and declare:
  - allowed `committed_by` producer variants
  - whether the kind is allowed as a transcript-anchor commit
  - the canonical `MetadataChange` and `DerivedStateChange` entries the kind typically commits
  - the surface-display label template
  - the description shown in the inspector and history-panel timeline

The closed catalogue is canonical for cross-cutting reasoning. The `Custom` extension is canonical for subsystem and surface specialisation. Every commit at runtime declares exactly one `op_summary` — no commit ever has an unparseable summary.

### 5.3 Boundary Composition

Multiple logical operations may share one commit boundary. The canonical compositions:

- a `UserMessage` boundary that includes attachments commits one version whose diff adds the `MessageUser` block plus its `FileAttachment` and `SourceExcerpt` children; this is one boundary, one commit, one diff
- an `AgentTurn` boundary that produced tool calls, tool results, reasoning, and a final response commits one version whose diff adds the `MessageAssistant` block plus all its children plus any agent-initiated `ContextOp` operations the agent performed during the turn
- an `AgentTurn` boundary that produced a new artifact version commits one version whose diff adds the new `Artifact`-kind block, records the `ArtifactReviewState` and `ArtifactLifecycle` derived-state changes, and updates the entity's `current_version_block_id` pointer — all as one commit
- a `ContextEdit` boundary that batches many operations (mask 5, drop 2, pin 1, reorder, undo one mask) commits one version with one net diff; the in-session operations live in `pending_ops` until the boundary fires and merge into the net effect

The canonical rule: one boundary, one commit, one diff per boundary. A run that produces multiple meaningful boundaries (a long automation run that commits one workflow-node per stage) produces multiple commits, one per boundary, each with its own diff.

### 5.4 Boundary Discipline Rules

The following rules govern commit-boundary firing:

- a boundary fires only when the producing operation has reached a canonical commit point (per File 08 §7.6's boundary set); partial progress before commit lives in `pending_ops` and `Event`s on the bus, never as a `ContextVersion`
- a boundary cannot fire mid-stream — streaming events flow during production; the commit fires when the producer's declared boundary is reached (the model's final text accepted, the capability's commit returned, the workflow node's typed result delivered)
- a boundary that would produce no diff (no operations were performed since the prior commit) does not fire; the system does not commit empty versions. An exception is `Recovery` and `Correction` boundaries which always commit even when the net diff is small
- a boundary that would violate the block commit validator (per File 08 §8.2) for any committed block does not fire; the validator's typed error returns through File 04 §8.3's in-band denial path
- a boundary fires synchronously with the producing operation's commit point; the runtime cannot defer the commit to a later moment, because that would break replay determinism

### 5.5 Boundary

The commit-boundary catalogue defines what triggers a new version. The pending-operations buffer (§6) defines what accumulates between boundaries. The `VersionDiff` (§4) defines what each commit records. The ledger (File 10) records the events emitted at each boundary. None of those layers invents new commit semantics; they consume what this section defines.

## 6. Pending-Operations Buffer

### 6.1 Definition

The pending-operations buffer (`pending_ops`) is the per-conversation accumulation point for `ContextOp` operations applied between commit boundaries. It is held on the per-conversation `ConversationVersionState` record and flushes into the next `ContextVersion`'s `VersionDiff` when a boundary fires.

`ConversationVersionState`:

```
ConversationVersionState {
    conversation_id,
    current_version_id,
    pending_ops: Vec<ContextOp>,
    updated_at,
}
```

The buffer is durable — every `ContextOp` applied through the versioning operation surface (§17.5) is recorded in `pending_ops` immediately, survives process restart, and is recovered from durable storage when the conversation reloads. The buffer is not a transient in-memory queue.

### 6.2 Buffer Lifecycle

The buffer's lifecycle:

1. **Empty.** After a boundary commits, the buffer clears. The conversation's `current_version_id` points at the new committed version.
2. **Accumulating.** As the user or the agent invokes `apply_op` (mask, drop, pin, reorder, etc.), each operation appends to `pending_ops` and updates the materialised view live for immediate UI feedback. The version graph is not yet aware of the operation as a committed fact.
3. **In-session undo.** The user may undo the most recently applied operation via `undo_pending`, which pops the last `ContextOp` from `pending_ops` and re-derives the materialised view from the previous state. No new commit is created; the buffer simply shrinks. Multiple undos walk backward through the buffer; `redo_pending` re-applies (if supported per §6.5).
4. **Commit.** When a boundary fires (per §5), the runtime computes the net diff of `pending_ops` against the pre-buffer materialised view, creates a new `ContextVersion` with that diff, clears the buffer, advances `current_version_id`, and emits the canonical events (`PendingOpApplied` for each operation that contributed; `VersionCommitted` for the new version).
5. **Discard.** A user-cancellation of an in-flight assistant turn (per File 04 §17.3) may discard the buffer entirely: cooperatively cancel the producing operations, drop the accumulated `pending_ops`, and re-derive the materialised view to the state at `current_version_id`. The conversation returns to the pre-buffer state with no version commit.

### 6.3 In-Session Undo

`undo_pending(conversation_id)` is a typed operation that:

- requires `pending_ops` to be non-empty; an empty buffer's undo is a no-op
- pops the most recent `ContextOp` from the buffer
- re-derives the materialised view by re-applying the remaining operations from the post-`current_version_id` baseline (or by applying the inverse of the popped operation if the inverse is well-defined for that operation kind — see §11.4)
- emits a typed `PendingOpUndone { conversation_id, popped_op }` event

The operation is non-destructive: the popped operation is not recorded as committed history (it never committed). Walking the buffer backward by repeated undo is the canonical in-session undo affordance.

### 6.4 Buffer Discard

`discard_pending(conversation_id, reason)` is a typed operation that:

- requires `pending_ops` to be non-empty
- drops every operation in the buffer
- re-derives the materialised view to the state at `current_version_id`
- emits a typed `PendingOpsDiscarded { conversation_id, reason, dropped_count }` event

Used by user-cancellation of an in-flight assistant turn (per File 04 §17.3 cooperative cancellation) and by run-level supersession (a retry that explicitly discards the prior turn's pending state instead of committing it).

A discarded operation's blocks remain in the block pool as orphans per File 04 §17.3, subject to the block/storage retention policy. Any timed retention requires explicit user or profile selection and must preserve provenance and tombstone requirements. The version graph does not retain a record of the discard beyond the typed event in the ledger.

### 6.5 Redo

`redo_pending(conversation_id)` is optional; storage may maintain a forward redo stack alongside the backward undo stack within the buffer's lifetime. When supported, `redo_pending` re-applies the most recently undone operation; both stacks clear when a commit boundary fires (post-commit, redo does not cross the boundary — the way to redo post-commit is to switch back to the prior version via §8).

Whether `redo_pending` is supported is settings-driven (`versioning.in_session_redo_enabled`). This file makes redo optional rather than mandatory.

### 6.6 Buffer Storage

The buffer is stored on the per-conversation `ConversationVersionState` record:

```
ConversationVersionState {
    conversation_id,
    current_version_id,
    pending_ops,     -- typed payload (JSON / MessagePack / CBOR per storage)
    updated_at,
}
```

The buffer survives process restart. On restart, the runtime reloads `ConversationVersionState`, re-derives the materialised view from `current_version_id` plus the buffer, and the conversation resumes from where it was. If the buffer's contents are inconsistent with the substrate (a referenced block was hard-deleted between operations, a referenced version_id no longer exists), the runtime emits a `PendingOpsInconsistencyDetected` event and discards the buffer with a typed reason; this is rare and corresponds to a substrate violation.

### 6.7 Concurrent Modifications

Multiple actors may modify `pending_ops` for the same conversation (the user clicks a mask button while the agent is performing a context operation during a turn). The buffer is a single ordered sequence; operations are serialised at the versioning operation boundary. Two operations that target the same `block_id` follow the canonical operation-merge rules of §11.6 — typically the later operation wins for state changes, and reorders are interleaved by application order.

### 6.8 Boundary

The pending buffer defines the accumulation point. The commit boundary (§5) defines when the buffer flushes. The materialised view (§7) reflects the buffer's live state for instant UI feedback. The ledger records the typed events at apply, undo, and discard. The version graph itself is updated only at commit.

## 7. Materialised View (`context_view`)

### 7.1 Definition

The materialised view (`context_view`) is the canonical read-optimised projection of the active conversation version's view-state over the block pool, consumed by context assembly, surface rendering, retrieval, and downstream operations that need the current state. The source of truth is the version graph plus the block pool and relevant durable substrates. `context_view` is rebuildable from those substrates and holds no facts they do not.

`context_view` is the single shared materialised projection layer for active conversation state. It inherits File 01's `Projection` contract.

### 7.2 Required Shape

The materialised view is a per-conversation table of typed rows:

```
ContextViewRow {
    conversation_id,
    block_id,
    position,           // sequence index in render order
    lifecycle_state,    // BlockLifecycle: Raw | Active | Masked | Dropped | Recovered
    pin_state,          // PinState: Unpinned | Pinned | Protected
}
```

For each `(conversation_id, block_id)` active at the conversation's `current_version_id`, there is exactly one row. Blocks at `BlockLifecycle::Dropped` are retained as rows in the materialised view (so the version-graph layer can resolve them on demand and so the inspector can render their masked/dropped placeholders), but downstream layers filter `Dropped` blocks out of context assembly and standard retrieval per File 08 §6.

Per-version derived state for adjacent entity layers (artifact lifecycle / review / validation, claim status) is computed on demand at read time from the version graph plus the entity records; only `lifecycle_state` and `pin_state` are stored on the row, because those are the load-bearing per-`ContextVersion` view-state of every block and are accessed at every context-assembly read.

### 7.3 Properties

- **Live updates.** Every `ContextOp` applied through the versioning operation surface updates `context_view` immediately, before the commit. The buffer plus the live materialised view together represent the user's current intent; the version graph records the commit at boundaries.
- **O(1) reads.** Direct table lookup by `(conversation_id, block_id)` or by `(conversation_id, position)` returns the active state without traversing the version graph. This is the dominant access pattern for context assembly, render, and retrieval.
- **O(path-length) rebuild.** Version switching (§8) rebuilds `context_view` by walking the path between the current version and the target, applying reverse and forward diffs. For long-range jumps, strategic-cache nodes (§7.6) shorten the walk.
- **Per-conversation isolation.** Each conversation has its own materialised view; switching versions in one conversation does not affect another's view.
- **Rebuildable from durable substrate.** The view's contents are entirely derivable from `(current_version_id, pending_ops)` plus the chain of `ContextVersion`s and their `VersionDiff`s reachable from the root. Any corruption is resolved by rebuild, never by loss of canonical state.
- **No durable facts unique to the view.** Every fact the view holds is reconstructable; the view is a projection, not a source of truth.

### 7.4 Update Triggers

The materialised view rebuilds or updates on:

- **Apply.** `apply_context_op(op)` applies the operation's effect to the view in place; the buffer accumulates the operation but the view is updated live for instant feedback. Update cost: O(1) for most operations; O(view_size) for reorder.
- **Undo / Discard.** `undo_pending` and `discard_pending` re-derive the view to the appropriate state per §6.3 and §6.4.
- **Commit.** At commit, the diff is computed from the buffer's net effect; the view is already at the post-commit state, so no rebuild is required; `current_version_id` advances and the buffer clears.
- **Switch.** `switch_to_version(target_id)` walks the path and applies reverse / forward diffs; the view ends at the target version's state.
- **Block-pool mutation.** A new sibling block committed at the active version (per File 08 §6.2) is added to the view at the supersession's recorded position; the view updates synchronously with the block commit.
- **Hard delete.** A hard-deleted block's row in the view transitions to a tombstone placeholder (per File 08 §6.6); referenced positions remain but resolve to the tombstone.
- **Restart.** On process restart, the view is rebuilt from durable storage (the view itself is durable in `context_view` rows; corruption fallback rebuilds from action log).
- **Integrity violation.** A detected `MaterialisedViewIntegrityViolated` event (§7.6) triggers full rebuild from the action log.

### 7.5 Rebuild Trigger Declaration

Per File 01 §6.11, every projection declares its rebuild triggers. The materialised view declares:

- **event-driven** — every `apply_op`, every commit, every block-pool mutation at the active version, every switch
- **on-demand** — explicit rebuild on integrity violation, explicit rebuild requested by inspector or maintenance operation
- **periodic** — none; the view does not periodically rebuild

### 7.6 Integrity Verification

The materialised view's integrity is verifiable through the `expected_view_hash` field on `ContextVersion` (§3.2). At strategic-cache nodes (§8.6) and at commit, the storage layer may compute a canonical hash over `context_view` for the active version and store it on the version row. Subsequent rebuilds or reads can verify by:

1. Recomputing the canonical hash over the current `context_view`
2. Comparing against the stored `expected_view_hash` on the active version
3. On mismatch, emitting a `MaterialisedViewIntegrityViolated { conversation_id, version_id, expected_hash, actual_hash }` ledger entry, marking the conversation's view as `degraded`, and rebuilding from the action log
4. After rebuild, recomputing and recording the corrected hash

Storage may make hash computation mandatory or optional based on the `versioning.view_integrity_check_strictness` setting (`Strict`, `CacheAnchorsOnly`, `Off`). Exact defaults belong to settings profiles, not this canonical layer.

The canonical hash domain is SHA-256 over the row set sorted by `(block_id)` with each row serialised as `(block_id, position, lifecycle_state, pin_state)`. The hash is independent of insertion order, durable across implementations, and stable across storage backends.

### 7.7 Cross-Surface Materialised View

Each conversation has one materialised view. Surfaces project the view through surface-specific filters (per File 07 §1, File 08 §12, File 09 §17.2); the underlying view is shared across all surfaces of the conversation. A coder-surface render filters for `FileAttachment` and `Artifact` blocks; a transcript render filters for transcript-anchorable kinds; an inspector render shows every row including `Dropped` placeholders. All read from the same `context_view` rows.

### 7.8 Boundary

The materialised view defines the active-version projection over the block pool. The version graph defines the action log. The block pool defines content. The ledger records the events. The storage layer realises the durability (per §18). The view's shape and integrity contract are owned by this section; the rest is consumed.

## 8. Version Switching

### 8.1 Definition

Version switching changes a conversation's `current_version_id` to a target version's id, rebuilding the materialised view to match the target's state. Switching is non-destructive: the prior current version remains in the tree and is reachable through subsequent switches.

### 8.2 The Algorithm

`switch_to_version(conversation_id, target_version_id)`:

1. **Validate.** The target must exist in the conversation's version tree; the current version must exist; both must share the conversation's root.
2. **Find path.** Compute the path in the tree from the current version to the target: walk up from current to the common ancestor with target, then walk down from the common ancestor to target. The path is a sequence of `(direction, version_id)` pairs where direction is `Up` or `Down`.
3. **Discard pending operations.** Any `pending_ops` accumulated from the current version's session are discarded (no implicit commit on switch per §6.4). The buffer clears; the materialised view is re-derived against the current version's state before the walk begins.
4. **Apply reverse diffs (up).** For each `Up` step, apply the reverse of that version's diff to `context_view`. Reverse semantics: `added` entries are removed; `removed` entries are re-added at their old positions; `lifecycle_changes` reverse `(block_id, from, to)` to `(block_id, to, from)`; `pin_changes` reverse similarly; `position_changes` move blocks back to their parent-version positions; `metadata_changes` and `derived_state_changes` reverse per their typed inverse rules; `hard_deletes` cannot be reversed by switch — affected blocks remain tombstones, and the materialised view shows the tombstone placeholder.
5. **Apply forward diffs (down).** For each `Down` step, apply the forward diff of that version to `context_view`.
6. **Verify integrity.** If the target has an `expected_view_hash`, recompute the canonical hash and verify per §7.6. On mismatch, emit `MaterialisedViewIntegrityViolated` and rebuild from the action log.
7. **Advance pointer.** Update `ConversationVersionState.current_version_id` to `target_version_id`.
8. **Discard pending again.** The buffer remains empty (it was discarded in step 3); no operations from the prior version's session are retained.
9. **Emit events.** Emit `VersionSwitched { conversation_id, from_version_id, to_version_id, path_length, rebuild_from_action_log: bool }` (the boolean indicates whether a full rebuild was required) through the canonical bus and record it in the ledger.

### 8.3 Path-Length Complexity

For typical workflows:

- a retry-then-undo switch is 1–3 hops
- switching between adjacent siblings is 2 hops (one up, one down)
- switching between two recent branches is 3–10 hops
- long-range jumps to early conversation state may be 50–500 hops; for these, strategic-cache nodes (§8.6) shorten the walk

Application of each step is O(diff_size). Typical diff size is single-digit entries; even at 500-hop walks with 5-entry diffs, the total work is bounded and cheap (microseconds to low milliseconds).

### 8.4 Hard Delete Handling

If the path includes versions with `hard_deletes`, those deletions are not reversible by switch. The affected blocks remain tombstones in the block pool (per File 08 §6.6); the materialised view at versions where the blocks were active resolves them to the tombstone placeholder. The composition-materialisation fallback (per File 08 §6.6) applies if a `Composed` parent's child was hard-deleted: the composed block's resolved content is materialised into a new block linked by `materialized_by`, preserving the view's resolvability past the deletion.

Switching to a version before a `hard_delete` does not restore the deleted block. The version tree records that the block was once active and then destroyed; the tombstone represents what remains.

### 8.5 Switching from Buffered State

If `pending_ops` is non-empty when `switch_to_version` is called:

- If configured to discard, the runtime discards the buffer (per §6.4) and warns the user through the typed event `PendingOpsDiscardedOnSwitch { conversation_id, discarded_count }`.
- The user may configure `versioning.switch_with_pending_behaviour` to one of:
  - `Discard` — discard the buffer, switch, warn
  - `Commit` — commit the buffer first (as a `ContextEdit`), then switch
  - `Prompt` — open a typed-confirmation flow (per File 06 §7) asking the user to choose Commit / Discard / Cancel

### 8.6 Strategic-Cache Nodes

For long-range switches, the storage layer may maintain materialised-view caches at strategic version nodes. When a switch's path crosses a strategic-cache node, the walk starts from the nearest cached node instead of the root. This is a storage optimisation; the canonical algorithm does not require it. Cache placement, eviction, and count limits are storage/profile concerns. Cache corruption triggers rebuild from the durable substrate and never changes canonical state.

Strategic-cache nodes may also serve as anchor points for `expected_view_hash` integrity verification (§7.6).

### 8.7 Boundary

Version switching defines the deterministic path-walk algorithm. The materialised view (§7) is the substrate. The block pool (File 08) is the content source. Strategic-cache nodes (§8.6) are storage optimisations. The ledger records the switch events. No layer redefines the switch semantics; they consume what this section specifies.

## 9. Branching and Forking

### 9.1 Branching

A branch is a sibling `ContextVersion` of an existing non-leaf version. Branching is the canonical non-destructive divergence primitive: when the user (or the agent) commits a new version after switching to a non-leaf version, the new commit becomes a child of the switched-to version instead of the prior leaf, and both branches remain permanent and switchable.

The mechanics:

1. The user switches to `version_id_X` (per §8).
2. The user (or the agent) performs operations, accumulating in `pending_ops`.
3. A boundary fires; the new version `version_id_Y` is created with `parent_version_id = version_id_X`.
4. If `version_id_X` already has a child `version_id_Z` (from before the switch), then `version_id_Y` becomes its sibling: both `version_id_Z` and `version_id_Y` have `parent_version_id = version_id_X`.
5. The conversation's `current_version_id` advances to `version_id_Y`. `version_id_Z` and its descendants remain reachable through the version tree.

Branching is the natural consequence of switching plus committing. The user does not invoke a separate "branch" operation. The canonical event emitted is `BranchCreated { conversation_id, branched_from_version_id, new_branch_root_version_id }` whenever a commit creates a new branch (not when it merely extends the existing leaf).

Branch labels: branches may be labelled at the branch-root version (per §17.4 `label_version`) so users can refer to them by name. Surface displays may show branches as sibling lines emanating from their shared parent.

### 9.2 Branch Merge Provenance

The version graph remains a single-parent tree. When a user intentionally combines work from multiple branches, the resulting commit is a normal child of the branch chosen as the base and carries `merge_source_version_ids` for the additional contributing versions.

`merge_source_version_ids` are provenance references, not topology edges for path-walk switching. This preserves the simple tree algorithm while making merge contribution inspectable for history, comparison, and replay.

### 9.3 Forking

A fork is a new conversation seeded from an existing conversation's version. Forking:

1. Creates a new `conversation_id` (per File 02)
2. Copies allowed materialised-view rows from the source's target version into the new conversation's root materialised view
3. Creates the new conversation's root `ContextVersion` with `parent_version_id = null` and an `Import` op_summary referencing the source `(source_conversation_id, source_version_id)`
4. Establishes block-pool references for blocks whose scope, sensitivity, and policy allow visibility in the destination
5. Records the fork event `ConversationForked { source_conversation_id, source_version_id, new_conversation_id }` through the canonical bus
6. Forks are reachable through `provenance.query_lineage` for the new conversation per File 09 §15

Forking is the explicit-copy variant of cross-conversation reference. The share-without-copy variant (per File 08 §11.3) is also supported: a block at `workspace` scope or broader is addressable from any conversation without forking.

Blocks whose scope or sensitivity prevents visibility in the destination are omitted by default and replaced with a typed placeholder: `ForkOmitted { source_block_id, reason: ScopeRestriction | SensitivityRestriction | PolicyDenial }`. The placeholder is a block in the forked conversation's pool carrying source identity for provenance but no content. The user may later promote scope with approval per File 06, copy with new identity and redacted content, or leave the placeholder. Sharing-by-default for restricted blocks is explicitly invalid.

Subsequent edits in the fork commit new versions under the fork's `conversation_id`; the source conversation is unaffected. Edits that create sibling blocks (per File 08 §6.2) place the new siblings in the unified pool, where both conversations can see them but only the fork's version graph references them as active.

### 9.4 Cross-Workspace Forking

Cross-workspace forking requires the future Sync, Import, Export spec's portable bundle mechanism. The canonical contract: a fork imports the source conversation's relevant blocks, version chain (or a flattened root with `Import` op_summary), entity records, and edge metadata into the destination workspace. The source's `version_id`s do not transfer (each workspace has its own UUID space); the import operation produces new identities and records the source-to-destination mapping for provenance queries.

### 9.5 Branch Topology Visualisation

The version tree's topology is a directed tree with `parent_version_id` defining the edge from child to parent. The canonical rendering data:

- root version at the top; children below; siblings horizontal
- linear runs (parent has exactly one child, child has exactly one parent) collapse into a "linear run of N versions" summary in the tree view
- branch points (a parent with multiple children) emit distinct visual nodes for each child
- the conversation's `current_version_id` is highlighted; the leaves of the tree are addressable through "go to leaf" navigation
- labelled versions and bookmarked versions are visually distinguished

Tree view and expandable list view are surface projections of the same data per File 02 §8 and source `03-versioning-and-branching.md`. Switching between views is a rendering choice, not a data reload.

### 9.6 Boundary

Branching is the natural consequence of switch-plus-commit. Merge-source references preserve merge provenance without changing tree parentage. Forking is the explicit-copy variant of cross-conversation reference. Tree topology is the data structure the materialised view rebuilds against. None of these add new commit semantics; they compose with the existing primitives.

## 10. Per-Version Derived State Maps

### 10.1 Definition

Per-`ContextVersion` derived state — `BlockLifecycle`, `PinState`, `ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`, `TaskRevision`, plus registered extensions — is computed from the version-graph action log over the block pool plus the entity records. The version graph is the substrate; the entity records carry stable identity; the derived state is what the active version's view-state of each entity is.

This file defines the derivation rules. Adjacent layers consume the derived state (context assembly reads `BlockLifecycle` to decide what to include; surface renderers read `ArtifactLifecycle` to mark "Draft" vs "Active" badges; the policy layer reads `ClaimStatus` to evaluate confidence-floor rules).

### 10.2 Block Lifecycle Derivation

Per File 08 §6.1, `BlockLifecycle` is `Raw | Active | Masked | Dropped | Recovered`. Per `ContextVersion`, each block's lifecycle is the result of:

1. The block's initial state at first commit (typically `Raw` for transient blocks, `Active` for transcript and standard committed blocks)
2. All `lifecycle_changes` entries in `VersionDiff`s along the path from the version where the block was first added to the current version
3. The final state declared in the latest applicable `lifecycle_change`

The materialised view stores the result; the action log is the substrate. The derivation is deterministic.

### 10.3 Pin State Derivation

Per File 08 §6.1, `PinState` is `Unpinned | Pinned | Protected`. Same derivation as `BlockLifecycle`: initial state plus all `pin_changes` along the path.

### 10.4 Artifact-Level Derived State

Per File 09 §5, `ArtifactLifecycle` is `Draft | Active | Validated | Superseded | Archived | Discarded`; `ReviewState` is `Unreviewed | AcceptedByUser | AcceptedByAgent | Rejected | NeedsRevision`; `ValidationState` is `NotValidated | PendingValidation | Passed | Failed | NeedsReview`.

Per `ContextVersion`, each artifact's effective state is derived from:

- the active version-block for the artifact (via the entity's `current_version_block_id` or the version-tree's branch-aware projection)
- the `derived_state_changes` entries in the version graph that explicitly recorded artifact-state transitions
- the `validated_by` edges on the active version-block (per File 09 §14.2)

The entity record's denormalised `current_version_block_id` is a default/latest pointer for non-branch-specific reads. Branch-aware surfaces resolve the artifact's effective version through the active `ContextVersion`'s view of the artifact-version chain.

### 10.5 Claim Status Derivation

Per File 09 §9.4, `ClaimStatus` is `Candidate | Supported | Contradicted | Unresolved | Superseded | Withdrawn`. Per `ContextVersion`, a claim's effective status is derived from:

- the set of `EvidenceLink` edges active at the version (per File 09 §11)
- the `claim.evidence_threshold` setting in effect at the version (per the `settings_snapshot_id` snapshot reference)
- the explicit `ClaimStatusOverridden` events recorded since the claim's publication
- the explicit `ClaimWithdrawn` events

When the substrate changes (an evidence link is added or removed; a claim is overridden or withdrawn), the corresponding `ClaimStatus` change is recorded in the committing version's `derived_state_changes`. Pure read-time recomputation that does not involve a substrate change does not record on a version.

### 10.6 Task Revision Derivation

Per File 02 §6.3, task updates carry a revision counter; concurrent updates produce sibling branches. Per `ContextVersion`, a task's effective revision is the latest committed `TaskRevisionAdvanced` derived-state change on the path from the task's creation commit to the current version.

### 10.7 Custom Derived-State Extension

Subsystems and plugins may register additional derived-state kinds through the canonical proposal-first mechanism (per File 05 §16.2). Registered kinds declare:

- the derivation source (which `VersionDiff` entries trigger recomputation)
- the derivation rule (the deterministic algorithm computing the new state from the substrate)
- the canonical event kind emitted when the state changes
- the surface-display rendering hint

Registered custom derived state participates in the version graph through `derived_state_changes::Custom { namespace, name, payload }` entries per §4.4.

### 10.8 Boundary

Per-version derived state is computed on demand from the substrate (action log plus entity records plus snapshot references). The materialised view stores only `BlockLifecycle` and `PinState` because those are accessed on every read; other derived state is recomputed at query time or cached as a separate materialised projection per the storage layer's optimisations. The derivation is deterministic; corruption is resolved by rebuild.

## 11. `ContextOp` — Closed Canonical Operation Vocabulary

### 11.1 Definition

A `ContextOp` is one user-or-agent-or-subsystem-applied operation against the materialised view. Operations accumulate in `pending_ops` (§6) and merge into one `VersionDiff` at the next commit boundary (§5). Operations are the version-graph's action language; the diff is the net result.

The canonical closed catalogue:

### 11.2 Closed Catalogue

```
ContextOp {
    Mask { block_id },
    Unmask { block_id },
    Drop { block_id },
    Recover { block_id },
    Pin { block_id },
    Unpin { block_id },
    Protect { block_id },
    Unprotect { block_id },
    Reorder { block_ids },                                     // new order for the listed blocks
    AddToContext { block_id, position },                       // add an existing block to the active view
    RemoveFromContext { block_id },                            // remove from active view (transitions to Dropped)
    Group { constituent_ids, name, description, group_kind },  // create a Group block (per File 08 §6.5)
    Ungroup { group_id },                                      // dissolve a Group block from the active view
    AddToGroup { group_id, block_ids, position },              // add blocks to a Composed parent
    RemoveFromGroup { group_id, block_ids },                   // remove from a Composed parent
    EditBlock { old_block_id, new_content_variant },           // create sibling block (per File 08 §6.2)
    PromoteScope { block_id, target_scope },                   // create a scope-promotion projection (per File 08 §11.2)
    ApplySensitivityOverride { block_id, prior, new, field_path },  // raise sensitivity (per File 08 §9)
    HardDeleteBlock { block_id },                              // destructive (per File 08 §6.6)
    Custom { namespace, name, payload },                       // registered extension
}
```

`Position` is an `Option<usize>`; `None` means "append at end."

### 11.3 Operation Semantics

Each operation has typed semantics:

- **Mask** transitions a block's `BlockLifecycle` to `Masked` for the active version's view. Compaction algorithms read `Masked` blocks' descriptions instead of content. The block stays in the pool.
- **Unmask** transitions a `Masked` or `Recovered` block back to `Active`. The block was already in the view; only the lifecycle state changes.
- **Drop** transitions a block to `Dropped`. The block is excluded from retrieval and standard context assembly. Reachable only through explicit recovery.
- **Recover** transitions a `Dropped` (or `Masked`) block to `Recovered` (semantically equivalent to `Active` with the historical mark).
- **Pin** / **Unpin** modify `PinState` to `Pinned` / `Unpinned`; compaction policies respect pinned blocks unless explicitly configured and approved otherwise.
- **Protect** / **Unprotect** modify `PinState` to `Protected` / `Unpinned`; protection is stronger than pin — compaction skips protected blocks entirely.
- **Reorder** sets new positions for the listed blocks. Positions for blocks not listed are unchanged.
- **AddToContext** / **RemoveFromContext** add or remove a block from the active view at the given position. `RemoveFromContext` transitions to `Dropped` (recoverable). `AddToContext` requires the block to exist in the pool.
- **Group** creates a new `Group`-kind `Composed` block with the constituents as children. The block commit happens at the next boundary; the `pending_ops` entry records the intent.
- **Ungroup** dissolves the group's presence in the active view (the group block remains in the pool; the view stops rendering it as a container, exposing its children at the appropriate positions instead).
- **AddToGroup** / **RemoveFromGroup** modify a `Composed` parent's children — produces a new sibling `Composed` block with the new children list (per File 08 §4.4 — composition immutability).
- **EditBlock** creates a new sibling block with the new content (per File 08 §6.2) and updates the active view to reference the new block at the position the old block occupied. The old block stays in the pool.
- **PromoteScope** creates a `scope_projection_of` or `promotes_scope_of` projection per File 08 §11.2; the original remains at its narrower scope.
- **ApplySensitivityOverride** raises the block's effective sensitivity per File 08 §9; lowering requires typed-confirmation per File 06 §7.
- **HardDeleteBlock** physically destroys the block per File 08 §6.6; this operation is destructive, requires typed-confirmation when the block is referenced, and produces a tombstone.
- **Custom** records a registered extension operation; its semantics are declared in the extension registration.

### 11.4 Operation Inverses

For in-session undo (§6.3), each operation has a typed inverse:

- `Mask ↔ Unmask`
- `Drop ↔ Recover`
- `Pin ↔ Unpin`
- `Protect ↔ Unprotect`
- `Reorder` inverse: re-apply the prior positions for the blocks the reorder touched (recorded as a snapshot of pre-reorder positions on the buffer entry)
- `AddToContext ↔ RemoveFromContext` (inverse of add-at-position is remove)
- `Group ↔ Ungroup` (inverse of creating the group is dissolving it; the group block itself remains in the pool, and a redo of the group restores the same block reference rather than committing a new sibling)
- `AddToGroup ↔ RemoveFromGroup`
- `EditBlock` inverse: revert the view's reference to the prior block (the new sibling stays in the pool — it is not destroyed by undo)
- `PromoteScope` inverse: remove the projection from the active view (the projection block remains in the pool)
- `ApplySensitivityOverride` inverse: lower-back is permitted only when the user explicitly authored the raise; otherwise the inverse is rejected by typed-confirmation
- `HardDeleteBlock` has no inverse — once destroyed, the block cannot be restored by undo. In-session undo of a not-yet-committed `HardDeleteBlock` operation is supported (the block's destruction has not yet been committed); post-commit undo is impossible.
- `Custom` operations declare their inverse in the registration.

The undo machinery uses these inverses to walk backward through `pending_ops`.

### 11.5 Operation Side Effects on Block Pool

Several operations cause block-pool mutations through File 08's mechanisms:

- `Group`, `AddToGroup`, `RemoveFromGroup`, `EditBlock`, `PromoteScope` all create new sibling blocks (the block commit happens at the next boundary; the operation in `pending_ops` references the new sibling's `block_id` reserved at apply time)
- `HardDeleteBlock` physically destroys a block per File 08 §6.6

The operation in the buffer references the new sibling's `block_id`; the block commit pipeline (per File 08 §8.2) validates the block at the commit boundary; if validation fails, the entire commit fails and `pending_ops` is preserved for user correction.

### 11.6 Operation Merge Rules (Concurrent / Conflicting)

When two operations in `pending_ops` target the same `block_id`, the canonical merge rules:

- **Sequential lifecycle changes** — later operation wins for the final state. `Mask → Unmask → Mask` results in `Masked`; `Drop → Recover` results in `Recovered` (which is `Active` with the historical mark).
- **Sequential pin changes** — later operation wins. `Pin → Unpin` results in `Unpinned`.
- **Reorder + position change** — the most recent position assignment for a block wins.
- **AddToContext after RemoveFromContext** — net effect: the block is `Active` at the new position.
- **RemoveFromContext after AddToContext** — net effect: the block is `Dropped` (no record in the diff except for the lifecycle change if the block was previously `Active`).
- **EditBlock + EditBlock** — the second edit's new sibling supersedes the first. The first edit's sibling remains in the pool but is not the active reference in the view.
- **HardDeleteBlock** — terminal; subsequent operations on the same `block_id` are typed errors (the block no longer exists).

The merge is computed deterministically at commit time; the diff's `lifecycle_changes`, `pin_changes`, `position_changes` entries reflect only the net effect, not the intermediate states.

### 11.7 Authority and Authorisation

Operations are subject to the canonical capability policy (per File 06):

- every agent-invoked `ContextOp` flows through a registered capability and the File 04 execution pipeline; agents do not mutate version history through side channels
- ordinary view mutations (`Mask`, `Drop`, `Pin`, `Reorder`, `AddToContext`, `RemoveFromContext`) are `WorkspaceWrite` unless narrowed by policy
- `HardDeleteBlock` has `permission_floor: Denied` and requires typed-confirmation (per File 06 §7)
- `ApplySensitivityOverride` that lowers sensitivity has `permission_floor: Denied` and requires typed-confirmation
- `PromoteScope { target_scope: global }` is `UserApproval` tier or stricter because it broadens visibility to all workspaces
- destructive or broadening operations (`HardDeleteBlock`, sensitivity lowering, global scope promotion, version tombstoning, version payload deletion, retention application) are user-confirmed or policy-denied by default

User invocation through the inspector / palette and hook-mediated substitution both pass through the same policy boundary. Hooks may substitute or block proposed operations only through File 10 hook authority classes.

### 11.8 Boundary

The `ContextOp` vocabulary defines the operation language. The pending buffer (§6) accumulates operations. The diff (§4) records the net effect at commit. The committed `VersionDiff` is the canonical state-reconstruction input. `PendingOpApplied` / `PendingOpUndone` ledger entries may preserve operation history for audit and UI inspection, but rebuild and switch semantics depend on diffs, not replaying the full operation sequence.

## 12. Sibling-Block Versioning over the Block Pool

### 12.1 Definition

Sibling-block versioning is the canonical mechanism by which observable content changes produce new immutable blocks in the unified pool, linked to the prior by `supersedes` edges (per File 08 §5.2), with the active reference in the materialised view updated to point at the new block. The version graph records the swap in the diff; the prior block stays in the pool, reachable through the version-tree-aware projection.

This mechanism is shared across:

- file edits (§12.2)
- message edits (§12.3)
- artifact-version commits (§13)
- knowledge-entry edits (§12.4)
- validator and adapter updates (§12.5)
- description regeneration (per File 08 §10.4)
- composed-block child changes (per File 08 §4.4)
- prompt-fragment updates and reusable-policy-rule updates

### 12.2 File Edits

A file edit (per File 09 §6.3 and `tools/file-operations.md`) creates a new sibling `Artifact`-kind block (or a `FileAttachment` block for non-artifact files) with the new content. The new sibling has:

- a fresh `block_id`
- the same `parent_block_id` as the prior block
- a `supersedes` edge to the prior block
- the new content in `BlockContent` (variant matching the prior — `Inline`, `External`, or `Composed`)
- a fresh `content_hash`
- a fresh `created_at`
- a `producer` field reflecting the edit source (user edit, agent `file.edit` invocation, filesystem watcher)

The materialised view's row for the active file block transitions to reference the new sibling at the same position. The version diff records the swap as a `(BlockId, Position)` removed-and-added pair plus any per-version metadata changes.

Reverting a file: per File 09 §6.3 and `domains/coder/checkpoints-undo.md`, there are two paths:

- **Forward revert** (`coder.file_reverted`): commit a new `ContextEdit` version that swaps the active file block back to the historical sibling. The current branch advances; the prior current-branch state is reachable through switch.
- **Switch revert**: switch the conversation's `current_version_id` to a version where the historical file block was active. Both branches remain in the tree.

The file-sync layer (per File 09 §7.5) detects the active-block change and rewrites the materialised file on disk to match.

### 12.3 Message Edits

A message edit (per File 02 §3.1) creates a new sibling `MessageUser` block with the new content. The new sibling has the same `parent_block_id` as the prior message block. The version graph commits an `EditMessage` version whose diff records the swap. Downstream blocks (the assistant responses, tool calls, results dependent on the prior message) become orphans of the new sibling's lineage; the user typically follows up with `Retry` to produce a new downstream branch, or with a manual continuation that produces new assistant turns referencing the edited message.

The orphan downstream is non-destructively preserved: the prior message's downstream remains in the block pool, reachable through the version-tree-aware switch back to the pre-edit version.

### 12.4 Knowledge-Entry Edits

Knowledge entries that carry durable content participate in the version tree as blocks. The `KnowledgeEntry` metadata record carries a content-version pointer such as `current_version_block_id` (a denormalised projection to the active entry block), not the conversation's `current_version_id`. Edits follow the same sibling pattern:

- user edits: `current_version_block_id` advances to the new entry block immediately upon commit
- agent-proposed edits with user approval: same — `current_version_block_id` advances on accept
- agent-proposed edits with user rejection: the new sibling block remains in the pool, the canonical `current_version_block_id` stays on the prior entry block, and the rejected version is left as a sibling branch reachable through the version-tree view

Plugin-bundled knowledge entries that a user wants to customise can be forked by creating a user-owned sibling block linked by `supersedes`. The original remains under the plugin's source attribution; the user's fork carries `UserDefined` source. Both remain in the unified pool; the user's fork becomes the canonical `current_version_block_id` at the user's preferred scope.

### 12.5 Validator and Adapter Updates

`Validator`-kind and `Adapter`-kind blocks (per File 09 §4) follow the same sibling-versioning pattern. Updates to a validator's rules or an adapter's logic create new siblings; the canonical execution path reads the active sibling at the conversation's `current_version_id` (or at the broader-scope active version for workspace/global-scope validators).

### 12.6 Boundary

Sibling-block versioning is the canonical content-change mechanism shared across all entity layers. File 08 owns the block-pool mechanics; this section specifies the version-graph integration. The `supersedes` edge plus the active-reference swap in the materialised view are the canonical signals of "this content was edited"; the version-tree branch is the canonical record of "here's where in history that edit happened."

## 13. Artifact Version Chains

### 13.1 Definition

An artifact version chain is the linear (or DAG-shaped under multi-parent merges) sequence of `Artifact`-kind blocks linked by `supersedes` edges, representing the evolution of a single artifact entity (per File 09 §6).

The chain has:

- a stable entity identity (`artifact_id`) shared across all versions
- a typed `ArtifactVersion` metadata record per version (per File 09 §6.2) carrying `version_id` (same value as the version-block's `block_id`), `artifact_id`, `version_number` (monotonically increasing integer per artifact), `parent_version_id`, `derivation_summary`, `produced_by_run_id`, `produced_by_node_id`, `produced_by_capability_id`, `materialized_paths`, `validation_report_id`, `metadata`
- a default/latest pointer on the entity record (`current_version_block_id`) for non-branch-specific reads
- branch-aware resolution through the active `ContextVersion`'s view of the chain

### 13.2 Chain Topology

The default chain topology is linear: each version has one parent (the prior version's `block_id` as the `supersedes` edge target). DAG topology is supported through `artifact.merge` (per File 09 §6.3), which produces a new version with one principal parent (recorded as `parent_version_id`) plus additional parents linked by `derives_from` edges. The version graph captures the merge as a single commit; the resulting topology in the artifact's chain is a DAG with the new version having multiple incoming edges.

### 13.3 Per-`ContextVersion` Resolution

For non-branch-specific reads, the entity record's `current_version_block_id` is the default. For branch-aware reads, the resolution rule:

1. Start at the conversation's `current_version_id`
2. Walk back through the version graph until the diff containing the artifact's most recent version-commit is found
3. The active version-block is the artifact's version-block produced by that commit
4. If no version-commit for the artifact is found on the path back to the root, the artifact has no version in the current view — return `None` (the artifact may exist in the broader workspace scope, but not in this conversation's tree)

The resolution is O(path-length from current version to the artifact's first commit in this conversation); strategic-cache nodes (§8.6) and per-artifact version-pointer caches may optimise the resolution.

### 13.4 Branch-Aware Artifact Versions

When a conversation branches and the artifact is edited on multiple branches, the artifact's effective version diverges per branch. The materialised view of each branch resolves the artifact to its branch-active version-block; the artifact's entity record carries the default/latest pointer (typically the leaf branch's most recent version), but branch-aware surfaces (the comparison board, the version inspector, the cross-branch diff renderer) resolve per branch.

The artifact's version chain in DAG form may carry multi-parent versions when the user merges two branches' versions of the artifact through `artifact.merge`.

### 13.5 Materialisation Across Versions

Per File 09 §7.4, each version's `materialized_paths` record carries the workspace paths where the version's content was written. When the conversation switches versions, the workspace's disk state updates to match the active version's `materialized_paths` (per File 09 §7.5 disk-sync loop). Prior versions' materialisations remain on disk according to the workspace retention policy (per File 09 §7.4 — paths typically include the `version_id` in the path template to avoid overwriting).

### 13.6 Boundary

Artifact version chains are a specialisation of sibling-block versioning over the unified pool. File 09 owns the entity-record schema; this section owns the version-graph integration and the per-`ContextVersion` resolution rule. The materialisation contract is owned by File 09 §7.

## 14. Snapshots

### 14.1 Definition

A snapshot is a typed, durable, addressable reference to the state of a canonical substrate (registry, settings, world, policy, pricing, routing) at a point in time. Snapshots are not stored copies of substrate content; they are identities the ledger, run records, capability invocations, and replay machinery carry to address substrate state for forensic queries and deterministic replay. The snapshot resolves to substrate state through the canonical replay machinery (§15).

Snapshot identity includes the snapshot kind, stable id, anchor, substrate schema/version, and resolver contract. Snapshot ids are unique within the installation and never reassigned.

### 14.2 Closed Canonical Snapshot Catalogue

The canonical typed snapshot identities, each addressable as `<kind>_snapshot_id`:

**`registry_snapshot_id`** — addresses the `RegisteredCapability` state at the named version per File 05 §10. Resolution: walk the capability-registration ledger entries (per File 10 §4.1 `CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityUpdated`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `CapabilityRegistryStateChanged`) from the install boot to the snapshot's anchor timestamp; the result is the registered-capability set with their `enabled`, `availability_status`, `resolved_backend_binding`, `trust_state`, `active_aliases`, and registered declaration version at that moment.

**`settings_snapshot_id`** — addresses the cascade-resolved settings tree at the named version per File 01 §6.8 and cross-cutting/settings.md. Resolution: walk the settings-change ledger entries from the install boot to the snapshot's anchor timestamp; the result is the per-scope settings cascade (global / workspace / conversation / per-capability overrides) as it would have resolved at that moment. Per cross-cutting/settings.md, the TOML overlay is per-device and not synced; the snapshot captures the SQLite-sourced settings, not the TOML overlay. Settings snapshots are SQLite-sourced; the TOML overlay is an out-of-band per-device runtime override that the snapshot does not capture (a deliberate consequence of the per-device exclusion from sync).

**`world_snapshot_id`** — addresses the world-model state at the named version per File 01 §6.7. Resolution: the world model maintains its own durable substrate (active subsystem/surface, mounted panels, focused element, available actions, active workspaces, etc.); the snapshot resolves to the world state at the anchor timestamp through the world-model service's replay path.

**`policy_snapshot_id`** — addresses the active policy rule set, lease set, approval templates, and contradiction-check rules at the named version per File 06. Resolution: walk the policy-event ledger entries from boot to the anchor; the result is the policy state at that moment, including all live leases (per File 06 §11.6's projection pattern).

**`pricing_snapshot_id`** — addresses the per-provider, per-model `PricingTier` records active at the named version per File 10 §6.4. Resolution: walk the pricing-update ledger entries; the result is the pricing state at that moment, supporting deterministic cost computation for replay.

**`routing_snapshot_id`** — addresses the routing-table state (model routing rules, capability-family routing, custom routes) at the named version per File 03 §3.5. Resolution: walk the routing-config-update ledger entries to the anchor.

**`<custom>_snapshot_id`** — registered extension snapshots (a knowledge-base index snapshot, a memory-consolidator state snapshot, an active-workspace-tree snapshot). Custom snapshots declare:
- the substrate they address
- the ledger entry kinds whose events the resolution walks
- the resolution algorithm
- the canonical event kind emitted when the snapshot's anchored substrate changes
- the surface-display label

Registered through proposal-first per File 05 §16.2.

### 14.3 Snapshot Anchoring

Snapshots are anchored at specific commit boundaries:

- a `ContextVersion`'s `snapshot_refs` map carries the snapshot ids of every substrate the commit consulted
- a run record carries the snapshot ids of every substrate consulted across its execution
- a capability invocation record carries the snapshot ids in effect at the invocation's commit
- a `RouteRecord` (per File 03 §3.5) carries the snapshot ids in effect at routing time

The anchor is the durable point at which the snapshot was captured, normally the commit boundary's `committed_at` plus the corresponding substrate sequence position. The snapshot's resolution walks substrate events up to, but not beyond, the anchor.

### 14.4 Snapshot Resolution

`resolve_snapshot(snapshot_kind, snapshot_id) -> SubstrateState` walks the appropriate substrate's event stream:

1. Identify the substrate by `snapshot_kind`
2. Identify the substrate's anchor timestamp by `snapshot_id`
3. Walk the substrate's durable event log from the substrate's boot or a storage-owned baseline to the anchor
4. Apply each event to the substrate's projection
5. Return the resolved state

The resolution is deterministic given the durable event log. Two devices replaying the same snapshot resolution against the same event log produce identical substrate states. If a snapshot cannot be resolved, the resolver returns a typed error; it never silently falls back to current state.

### 14.5 Snapshot Composition

A single commit may anchor multiple snapshot ids. The composition rule: each snapshot id resolves independently; combining them produces a full substrate snapshot for that commit's run. The order of resolution does not matter (snapshots are independent substrates).

### 14.6 Snapshot Storage

Snapshots are not stored as copies. The storage layer maintains:

- per-substrate durable event logs (ledger entries per File 10 §4)
- optional per-substrate baselines used only to bound replay length; storage decides whether and how to maintain them
- the `snapshot_refs` map on each `ContextVersion`, run record, etc.

Resolution walks the event log from the relevant substrate baseline, if one exists, to the anchor. Baselines are storage optimisations and are not part of canonical snapshot identity.

### 14.7 Boundary

Snapshots define addressable substrate identity at a point in time. The substrates (registry, settings, world, policy, pricing, routing) own their own event logs and projection mechanics; this section owns the typed snapshot-identity catalogue and the resolution contract. The resolution machinery is owned by the substrate's own projection layer; this file declares the contract.

## 15. Replay Semantics

### 15.1 Definition

Replay reconstructs past execution state from the durable substrates (block pool, version graph, execution ledger, snapshot resolution). Per File 10 §11, there are three closed canonical modes:

- **`Inspect`** — read-only forensic reconstruction; no execution, no side effects
- **`SimulateDeterministic`** — re-execute deterministic-replayable capabilities (per File 05 §7.3) against captured inputs and snapshot state; produces a new run record but does not commit observable side effects
- **`FullRerun`** — re-execute the run from scratch, observing all snapshot state at replay time (not capture time); produces a new run record and may commit observable side effects per the replay-class declarations

This file specifies the version-graph data each mode consumes.

### 15.2 `Inspect` Mode

`Inspect` mode reads:

- the `ContextVersion` at any point in the run's path
- the `VersionDiff` at each commit
- the materialised view as it was at the run's anchor commits (reconstructed by walking from the root)
- the `snapshot_refs` on each commit (resolved through §14.4 to substrate state at the anchor)
- the block pool's content (per File 08)
- the ledger entries the run produced (per File 10 §3)

Inspect answers queries like:

- "What did the model see at the moment of this run's model call?" — resolve the materialised view at the relevant anchor version; context assembly reconstructs the model-request text/content from that view, settings, and policy; File 07 reconstructs callable declarations; File 10 ledger entries identify model-call inputs, snapshots, and provider invocation records
- "What capability calls did this run make, and with what arguments?" — read the `ToolCallProposed` and `ToolCallExecuted` ledger entries in the run's scope
- "What was the policy state when this approval was granted?" — resolve the `policy_snapshot_id` on the `ApprovalGranted` ledger entry
- "What did the workspace look like at this version?" — resolve the materialised view's `materialized_paths` per File 09 §7.4 at the version

No execution; no side effects; deterministic given the durable substrate.

### 15.3 `SimulateDeterministic` Mode

`SimulateDeterministic` re-executes capabilities classified as `deterministic_replayable` (per File 05 §7.3) against:

- the captured input arguments (read from the `ToolCallProposed` ledger entry)
- the captured snapshot state (resolved through §14.4)
- the captured world state (per File 09 §13's observation `staleness_fingerprint`)

The re-executed capability produces a result; the simulation compares the result against the original `ToolCallCompleted` ledger entry. Mismatches indicate non-determinism (or a bug in the capability's classification).

Capabilities classified as `snapshot_replayable` may be re-executed in `SimulateDeterministic` mode by using the captured snapshot state plus the captured observation's `staleness_fingerprint` to revalidate currency; if the world has not changed since the observation, the simulation proceeds.

Capabilities classified as `effect_replayable_with_policy` or `not_replayable` are not re-executed in `SimulateDeterministic`; their results are read from the ledger but cannot be re-validated by simulation.

The new run record produced by `SimulateDeterministic` references the replayed source run via `replay_source_run_id`.

### 15.4 `FullRerun` Mode

`FullRerun` re-executes the entire run from scratch with replay-time snapshot state. The original snapshot anchors are read for reference but not enforced; the rerun observes whatever substrate state is current at replay time (registry, settings, world, policy, pricing).

The rerun produces a new run record; if the rerun produces observable side effects (writes files, calls APIs, makes purchases), those happen per the standard File 04 §8.2 pipeline including policy approval.

`FullRerun` is the user-initiated "redo this run with current state" operation; it is rare and explicit. Most replay needs `Inspect` or `SimulateDeterministic`.

### 15.5 Replay Identity

Every replay invocation:

- carries a `replay_id` (UUID)
- records the `replay_source_run_id`, the `replay_mode`, the `replay_initiated_at`, and the `replay_initiated_by`
- emits a `ReplayStarted` ledger entry (`Custom { namespace: replay, name: started }`); a `ReplayCompleted` entry on completion
- the new run record (`SimulateDeterministic` and `FullRerun` only) references the replay invocation

### 15.6 Replay-Capability Surface

`provenance.query_replay_trace` (per File 09 §15) returns the ledger entries that produced any version, artifact, or claim. Replay capabilities are declared:

- `replay.inspect { run_id, query_kind, query_target }` — read-only forensic query; `permission_floor: Denied`-free; `ReadOnly` tier
- `replay.simulate_deterministic { run_id, capability_filter }` — re-execute deterministic-replayable capabilities; `WorkspaceWrite` tier (the new run record is a write)
- `replay.full_rerun { run_id }` — full re-execution; `UserApproval` tier with typed-confirmation per File 06 §7 (the replayed side effects may be consequential)

### 15.7 Boundary

Replay reads the durable substrates (version graph, ledger, block pool, snapshot resolution) and produces typed results. The version graph defines the substrate shape; the substrates define their own content; the replay capabilities orchestrate the read or re-execution. No part of replay alters the durable substrates of the source run; new runs commit to new substrate state per the standard pipeline.

## 16. Version-Graph-Backed Projections

### 16.1 Definition

File 01 defines the general `Projection` primitive. This file applies that primitive to projections whose substrate is the version graph, the block pool, or version-anchored snapshot resolution.

### 16.2 Required Contract

Every version-graph-backed projection must:

- **Declare its substrate.** A `Projection`'s substrate is the closed set of durable facts it derives from. Adding a new substrate is a canonical declaration change.
- **Declare its rebuild trigger.** One of: `event-driven`, `on-demand`, or an explicitly configured maintenance trigger. Triggers may be combined.
- **Be rebuildable from the substrate.** No projection holds a fact that the substrate does not produce. A complete rebuild from the substrate must produce the same projection content (modulo bounded eventual consistency for event-driven projections during a rebuild window).
- **Emit `<Projection>Rebuilt` events.** Every full rebuild emits a typed event through the canonical bus (per File 10) for downstream consumers and observability.
- **Tolerate corruption.** A detected corruption (hash mismatch, stale read, schema-version mismatch) triggers a rebuild; the cost is rebuild time, never data loss. The projection's rows are not durable in the source-of-truth sense — they are rebuildable artifacts.
- **Carry a `version` discriminator** (when the projection's schema may evolve). Storage migrates supported earlier projection versions on load; unsupported versions trigger a rebuild.

### 16.3 Canonical Projections

The canonical projections this file establishes:

- `context_view` — the active version's view-state over the block pool (§7); event-driven; substrate is the version graph + block pool + entity records
- per-`ContextVersion` lifecycle / pin maps — derived per §10; event-driven; substrate is the version-graph action log
- artifact-entity `current_version_block_id` resolution — branch-aware default/latest projection consumed from File 09; substrate is the artifact's version chain plus the active `ContextVersion`
- per-version derived state (`ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`) — derived per §10; on-demand; substrate is the action log plus entity records
- snapshot resolutions — derived per §14.4; on-demand at query time; substrate is the per-substrate event log
- version-timeline and comparison-diff views — on-demand; substrate is the version graph plus labels, bookmarks, and selected version ids

Adjacent projections such as lease state, tool surfaces, retrieval indexes, token caches, workspace mirrors, conversation lists, and UI visualisations are owned by their own specs. They may consume the version graph, but File 11 does not define their full projection contracts.

### 16.4 Custom Projections

Subsystems and plugins may register projection types through the canonical proposal-first mechanism per File 05 §16.2. Registered custom projections declare:

- the substrate (block pool, version graph, ledger, registry, settings, world, policy, or registered extension substrates)
- the rebuild triggers
- the canonical event kinds emitted on rebuild
- the surface-display rendering hints

Registered projections participate in the same observability and lifecycle machinery as canonical projections.

### 16.5 Boundary

The `Projection` primitive defines the contract. Adjacent layers own their own projections. The storage layer realises the durability of projection state (or chooses not to durably store rebuildable projections). The version graph (this file) is the canonical substrate for several projections but is not itself a projection — the version graph is durable state.

## 17. Service Surface

### 17.1 Definition

The version graph exposes a canonical operation surface. Exact Rust traits, Tauri commands, storage tables, and transport bindings are implementation details owned by implementation and storage specs. The canonical requirement is that every read or mutation crosses this operation surface, emits File 10 events/ledger entries where consequential, and respects File 06 policy where applicable.

### 17.2 Operation Groups

The semantic operation groups are:

- reads: current version, version by id, version tree, active materialised view, pending operations, path-spec resolution
- pending-buffer operations: apply operation, undo pending, redo pending when enabled, discard pending
- commit operations: commit pending operations with a `VersionOpSummary` and snapshot references
- navigation: switch to version
- labels and bookmarks: label, unlabel, bookmark, unbookmark
- forensic and diff queries: diff versions, reconstruct view at version, integrity check
- retention and cleanup: tombstone version, compact version range, hard-delete version payload, apply retention policy
- cross-conversation: fork conversation

### 17.3 Read Surface

The read methods provide deterministic reads of version-graph state. `get_current_version` returns the row at `current_version_id`. `get_version_tree` returns the typed tree topology (each node with `parent_version_id`, `op_summary`, `committed_at`, `label`, `bookmarked`). `get_context_view` returns the materialised view at `current_version_id`. `get_version_at_path` resolves a path expression (e.g., "the version 5 commits back on this branch") to a concrete `version_id`.

### 17.4 Label and Bookmark Operations

`label_version` assigns a user-facing label to a `version_id`. The label is mutable (a `version_id` can be relabelled) but the label change is itself a typed event recorded in the ledger (`VersionLabelled { version_id, prior_label, new_label }`). The label appears in tree view, list view, history panel, and comparison board.

`bookmark_version` toggles the `bookmarked` flag. Bookmarked versions are exempt from retention-policy pruning (§20) regardless of the policy's age or count thresholds. The bookmark is a typed event (`VersionBookmarked { version_id }`).

### 17.5 Service Composition

Every version-graph operation:

- emits typed events through the canonical bus per File 10 §5
- records consequential operations as ledger entries per File 10 §3
- respects capability policy per File 06
- returns `Result<T, AppError>` per cross-cutting/errors.md
- is exposed to surfaces through the app's capability/service transport

### 17.6 Boundary

The service surface defines the canonical mutation and read API for the version graph. It does not define the Rust trait, command transport, or physical storage schema.

## 18. Persistence Contract

### 18.1 What Is Durably Stored

The following version-graph facts are durable:

- the version-graph itself — every `ContextVersion` row survives process restart, conversation archival, and version-graph compaction until explicit tombstoning, reconstruction-preserving compaction, or payload deletion applies. Required durable fields: `version_id`, `conversation_id`, `parent_version_id`, `merge_source_version_ids` when present, `committed_at`, `committed_by`, `op_summary`, `diff`, `label`, `bookmarked`, `snapshot_refs`, `version_schema_version`, `diff_hash`, `expected_view_hash` when present
- the materialised view — `context_view` rows for each conversation's active version are durable; on restart, they reload from storage; a corrupted or missing materialised view rebuilds from the action log
- the pending-operations buffer — `ConversationVersionState` carries `current_version_id`, `pending_ops`, and revision/update metadata; durable
- labels and bookmarks — mutations to `label` and `bookmarked` are durable through the ledger (`VersionLabelled`, `VersionBookmarked`); the latest values are stored on the `ContextVersion` row
- `expected_view_hash` records — durable when present; the storage layer chooses where to store them

### 18.2 What Is Computed

The following are computed, not stored:

- per-version `ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`, `TaskRevision` (per §10) — derived on demand from the action log plus entity records; storage may cache as a materialised projection (per §16.3) but the source of truth is the substrate
- materialised view rebuilds — derived from the action log when on-demand rebuild is requested
- snapshot resolutions — derived per §14.4
- the version-tree projection (tree topology with collapsed linear runs, branch-point markers, bookmark highlights) — derived for tree-view rendering
- per-tokenizer token counts of the active materialised view (per File 08 §13.2)
- conversation-list metadata such as surfaces used, last activity, and active status — derived

### 18.3 Reconstruction Across Restart

On process restart:

- the version graph reloads from durable storage
- materialised views (`context_view`) reload; corruption triggers rebuild
- `ConversationVersionState` reloads with `current_version_id` and `pending_ops`
- per-version derived state recomputes on first read (or from cached materialised projections)
- snapshot resolutions recompute on first query
- the active view a new run sees after restart is the same view a new run would have seen before restart, modulo any changes recorded during the offline interval (per File 08 §13.3)

In-flight `pending_ops` that were not committed at restart survive — the buffer is durable per §6.6. If the buffer's contents are inconsistent with the substrate (a referenced block was hard-deleted between operations), the runtime emits `PendingOpsInconsistencyDetected` and discards the buffer.

### 18.4 Reconstruction Across Retry, Edit, Reroute, Branch, Child-Run

Per File 04 §19, retry / reroute / edit / branch produce new runs linked to prior ones. The version graph records:

- a retry's new run commits a new branch under the boundary version that triggered the retry — the prior run's branch remains
- a reroute's new run commits under the appropriate boundary per File 03 §12's reroute resolution path
- an edit's new run commits an `EditMessage` version branch
- a branch's new run commits a sibling branch from the chosen point

The block pool itself is shared: the new run's blocks join the same pool. Version trees may diverge across branches (one branch masks a block another keeps active). Block records remain singular per File 08 §13.4.

Child runs (per File 04 §16) commit:

- isolated child runs: no version commit by the child; the parent's incorporation step (per File 04 §16.4) records the child's typed output as a tool result block in the parent's pending buffer; the parent's `AgentTurn` boundary commits it
- inline child runs: contributions land in the parent's pending buffer; the parent's boundary commits them as part of the parent's turn

### 18.5 Reconstruction Across Sync

Per §19, cross-device sync preserves the version graph's branching topology. Concurrent commits on two devices produce sibling branches; no last-write-wins. On sync pull, the materialised view stays on the local device's `current_version_id`; the remote's new commits are appended as siblings or as a different branch in the tree.

### 18.6 Boundary

Persistence is the storage layer's responsibility. This section specifies what the storage layer must persist (the field set above) and what it must reconstruct (the computed views). The storage schema, replication, indexing, and migration mechanics are owned by the future Storage and Persistence spec.

## 19. Cross-Device Sync and Conflict Resolution

### 19.1 Definition

Cross-device sync replicates version-graph state across multiple devices using the canonical sync transport (per future Sync, Import, Export spec). The sync model is version-tree-aware: concurrent commits on two devices produce sibling branches; no last-write-wins, no implicit merge, no squashing.

### 19.2 Sync Boundary

The sync transport decides which physical records replicate. File 11 specifies only the semantic requirements:

- replicated version-graph state must preserve `ContextVersion` identity, parentage, merge-source references, diffs, tombstones, labels, bookmarks, and snapshot references
- replicated block state must preserve immutable block identity and content-addressing semantics from File 08
- active `current_version_id` and `pending_ops` are per-device conversation state unless a future Sync spec explicitly defines a shared mode
- rebuildable caches, provider rate-limit state, audit-integrity overlays, and other per-device projections are not canonical version-graph state

### 19.3 Conflict Resolution

The canonical conflict-resolution rule for version-graph commits: both branches survive.

Scenario: Device A is on version `v_X` and commits a new child `v_Y_A`. Device B is also on `v_X` (synced state at that moment) and commits a different child `v_Y_B`. When the devices sync:

- both `v_Y_A` and `v_Y_B` appear in the version tree as siblings of `v_X`
- neither overwrites the other
- the remote's children are appended to the local's tree
- each device's local `current_version_id` remains unchanged (its own most recent commit)
- a `SyncVersionDiverged { conversation_id, local_version, remote_version }` event fires (per File 10 §4.1 `SyncVersionDiverged`)
- the UI may notify the user of the divergence and offer to switch to the remote branch

There is no automatic merge. There is no last-write-wins. There is no squash. The branching is legitimate — the user made different edits on two devices — and the version tree is the right place to represent that.

Block-level concurrent edits never conflict because blocks are immutable (per File 08 §6.2) — concurrent edits produce concurrent sibling blocks; the version graph records which sibling is active per branch.

### 19.4 Per-Device Materialised-View Pointer

Each device maintains its own `ConversationVersionState.current_version_id` and `pending_ops`. When sync pulls remote commits, the local `current_version_id` does not change automatically — the local user remains on whatever version they last committed or switched to. The remote's commits are reachable through the version tree; the user explicitly switches to them.

This preserves local-first ergonomics: a remote sync does not yank the user away from their current view.

### 19.5 External Content Sync

Per `infrastructure/sync.md`, binary blobs live outside libsql in a content-addressed external store (`workspaces/<workspace-id>/external/<sha>/<sha>`). On sync pull, blobs fetch on demand at first access (not pre-fetched). Blob fetch failures do not break the conversation — the affected block resolves to its description per File 08 §10.5 placeholder rendering, and the user is offered the option to re-fetch.

### 19.6 Sync Events

Per File 10 §4.1, the canonical sync ledger entry kinds and bus events:

- `SyncPulled { version_count, block_count, duration_ms }`
- `SyncPushed { version_count, block_count, duration_ms }`
- `SyncVersionDiverged { conversation_id, local_version, remote_version }`
- `SyncBlobFetched { uri, size_bytes }`
- `SyncFailed { reason }`

### 19.7 Boundary

The sync transport is owned by the future Sync, Import, Export, and Data Portability spec. This section specifies the version-tree-aware merge semantics and the per-device materialised-view pointer rule. The conflict resolution is the canonical contract; the transport realises it.

## 20. Garbage Collection and Pruning

### 20.1 Definition

Garbage collection and pruning are user-initiated or settings-driven operations that reduce version-graph storage. They are non-destructive by default per File 01 §7.13 — bookmarked versions are exempt; tombstones preserve identity for provenance closure per File 09 §8.

The canonical mechanisms:

- `tombstone_version`
- `compact_version_range`
- `hard_delete_version_payload`
- retention-policy-driven cleanup that invokes one of those typed operations

`delete_version` may exist as UI shorthand, but it is not a primitive. It must resolve to one of the typed operations above.

### 20.2 `tombstone_version`

`tombstone_version(version_id)` is a typed user operation that:

- requires the version to exist and to not be the conversation's `current_version_id`
- requires the version to not be bookmarked, unless the user explicitly unbookmarks it first
- requires `permission_floor: Denied`-tier typed-confirmation when the version has descendants in the tree
- preserves the version's topology identity: no silent physical row removal and no descendant reparenting
- emits `VersionTombstoned { conversation_id, version_id, parent_version_id, has_descendants }`
- records a tombstone so provenance queries resolve the version as `Tombstoned`

Tombstoning a version with descendants has a hard reconstruction constraint. It must either preserve the original diff with per-field content redaction for sensitive material, or replace the diff with a reconstruction-preserving compacted summary that produces identical materialised-view state when applied during a path-walk. If neither is achievable because the diff contains irreducibly `Secret` content that cannot be summarised without leaking, the operation fails with `TombstoneReconstructionUnsafe { version_id, reason }`. The user must then choose `hard_delete_version_payload`, explicitly acknowledging reconstruction loss for descendants and recording that loss as a typed provenance gap, or narrow cleanup to a version without descendants.

The blocks the version's diff added are not destroyed by tombstoning — they remain in the unified pool, subject to their own hard-delete contract per File 08 §6.6.

### 20.3 Tombstones

A version tombstone retains:

- `version_id` (preserved for provenance lookup)
- `conversation_id` (preserved)
- `deleted_at` (timestamp)
- `deleted_by` (actor identity)
- `deletion_reason` (typed enum: `UserRequested`, `RetentionPolicy`, `MaintenanceCleanup`, `Custom { code, description }`)
- the version's `committed_at`, `op_summary`, `label` (preserved for inspector display)

The tombstone replaces user-visible access to the full version row. It does not erase the topology required for path-walk reconstruction. Provenance queries that traverse through the tombstone receive a typed `Tombstoned` placeholder, and reconstruction uses either the preserved redacted diff or the reconstruction-preserving compacted summary.

### 20.4 `compact_version_range`

`compact_version_range(start_version_id, end_version_id)` replaces a linear range of versions with a reconstruction-preserving compacted segment. It applies only to linear segments: every version in the compacted range must have exactly one child, except the last, which may have any number. If the range includes a branching point, the operation fails with `CompactionBranchingPointInRange { version_id }`.

This constraint exists because compaction merges sequential diffs into one composed diff. Divergent children's diffs were computed against different intermediate states and cannot be safely reanchored to the compacted endpoint without per-child diff rewriting, which is a storage-layer optimization, not a canonical version-graph operation. The user must narrow the range to exclude the branch point or use per-version `tombstone_version` for non-linear segments.

### 20.5 `hard_delete_version_payload`

`hard_delete_version_payload(version_id, payload_scope)` physically removes selected payload data from version records or related substrate entries after typed confirmation and closure checks. If descendants or provenance queries lose reconstructability, the operation records a typed provenance gap. This is the explicit destructive path; it must never be invoked silently by retention policy.

### 20.6 Retention Policies

The canonical retention-policy enum (per domains/coder/checkpoints-undo.md and `versioning.retention_policy` setting):

```
RetentionPolicy {
    KeepAll,                                          // No expiry
    KeepRecentN { n: u32, exempt_bookmarks: bool },   // Keep N most recent non-bookmarked
    KeepWithin { duration, exempt_bookmarks: bool },  // Keep versions newer than given duration
    Custom { policy_id, params },                     // Registered extension
}
```

`KeepRecentN` and `KeepWithin` apply to non-current, non-bookmarked, non-labelled versions; bookmarked and labelled versions are always exempt regardless of `exempt_bookmarks` (the flag governs only how the policy treats unlabelled non-bookmarked versions). The policy invokes typed cleanup operations for affected versions.

Per File 01 constraint, no time-based pruning fires without explicit user or selected-profile opt-in. Retention execution cadence is a settings/profile concern and is not a correctness condition. Each retention invocation is durably recorded (`RetentionPolicyApplied { conversation_id, policy_id, affected_count, applied_at }`).

### 20.7 Hard-Delete Reclamation

A user-initiated "reclaim storage" operation (per File 01 §7.13) may invoke:

- `tombstone_version`, `compact_version_range`, or `hard_delete_version_payload` for non-bookmarked old versions
- `HardDeleteBlock` (per File 08 §6.6) for blocks the user no longer wants stored
- physical removal of the corresponding `external_content_metadata` entries and `external/<sha>/<sha>` blobs when no version-tree row references them

The cleanup respects the full version tree, not just the active view: a version that references a block keeps the block reachable. Blocks become eligible for cleanup only when no version in the tree (including tombstones) references them per File 09 §7.4.

### 20.8 Boundary

Garbage collection is user-driven and policy-driven. The canonical retention-policy enum closes the catalogue; tombstones preserve identity and reconstruction safety; compaction preserves equivalent materialised-view state across linear ranges; hard payload deletion records reconstruction loss when it is accepted. The reclamation surface honours File 01 §7.13's storage-management invariant.

## 21. Events

### 21.1 Canonical Event Vocabulary

Every version-graph operation emits typed events through the canonical bus per File 10 §5. The canonical version-graph events (each also a `LedgerEntryKind` per File 10 §4.1):

**Apply and commit:**

- `PendingOpApplied { conversation_id, op: ContextOp }` — operation applied to the buffer
- `PendingOpUndone { conversation_id, popped_op }` — in-session undo
- `PendingOpsDiscarded { conversation_id, reason, dropped_count }` — buffer discard
- `VersionCommitted { conversation_id, version_id, parent_version_id, op_summary, diff_summary, committed_by, snapshot_refs }` — new version committed

**Switching and branching:**

- `VersionSwitched { conversation_id, from_version_id, to_version_id, path_length, rebuilt_from_action_log }` — active version changed
- `BranchCreated { conversation_id, branched_from_version_id, new_branch_root_version_id }` — new branch from a non-leaf parent
- `ConversationForked { source_conversation_id, source_version_id, new_conversation_id }` — fork operation

**Labels and bookmarks:**

- `VersionLabelled { version_id, prior_label, new_label }`
- `VersionUnlabelled { version_id, prior_label }`
- `VersionBookmarked { version_id }`
- `VersionUnbookmarked { version_id }`

**Materialised view:**

- `MaterialisedViewRebuilt { conversation_id, version_id, source: RebuildSource }` — rebuild completed (with `RebuildSource` typed enum: `IntegrityViolation`, `ManualRequest`, `Restart`, `SwitchPathTooLong`, `CacheRefresh`)
- `MaterialisedViewIntegrityViolated { conversation_id, version_id, expected_hash, actual_hash }` — hash mismatch detected

**Deletion and retention:**

- `VersionTombstoned { conversation_id, version_id, parent_version_id, has_descendants }`
- `VersionRangeCompacted { conversation_id, start_version_id, end_version_id, compacted_segment_id }`
- `VersionPayloadHardDeleted { conversation_id, version_id, payload_scope, provenance_gap }`
- `RetentionPolicyApplied { conversation_id, policy_id, affected_count, applied_at }`

**Inconsistency:**

- `PendingOpsInconsistencyDetected { conversation_id, reason, dropped_count }` — buffer state inconsistent with substrate

Domain-specific history-panel, file-revert, and surface-display events are `Custom { namespace, name, payload }` extensions declared by their owning specs. File 11 reserves the extension mechanism; it does not predeclare surface-specific custom events.

### 21.2 Event Sensitivity

Version-graph events default to `Public` sensitivity per File 10 §10.2. Events that touch `Secret`-sensitivity blocks (a version commit that hard-deletes a `Secret` block) are `Sensitive`. Raw secret payloads never appear in version-graph event payloads (per File 10 §10.1 the durable ledger rules apply).

### 21.3 Hookable Events

Per File 10 §7.2 and `cross-cutting/events.md`, blocking hooks may subscribe to:

- `VersionCommitted` — for validators that want to review a commit before it lands (and potentially reject); the canonical commit-validation pattern
- `BranchCreated` — for tooling that wants to react to new branches (e.g., automated comparison runs)
- `VersionTombstoned`, `VersionRangeCompacted`, and `VersionPayloadHardDeleted` — for audit-required policies before cleanup

Blocking hook decisions follow the canonical typed decision vocabulary per File 10 §7.2 (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`); the hook's `priority` and `authority_class` are subject to the canonical policy per File 10 §7.3 and §7.4.

### 21.4 Boundary

This file owns the version-graph event kinds above. File 10 owns the envelope, sequence, sensitivity, delivery, hookability, and ledger persistence contracts.

## 22. Settings

### 22.1 Configurable Dimensions

Every version-graph mechanism in this file is configurable through settings (per File 01 §6.8 and cross-cutting/settings.md). File 11 names the dimensions; the settings system owns the cascade and storage.

**Buffer dimensions:**

- `versioning.in_session_redo_enabled` — whether `redo_pending` is supported
- `versioning.switch_with_pending_behaviour` — `Discard` | `Commit` | `Prompt`
- `versioning.pending_buffer_max_size` — soft cap on `pending_ops` length before forcing a `ContextEdit` commit

**Materialised-view dimensions:**

- `versioning.view_integrity_check_strictness` — `Strict` | `CacheAnchorsOnly` | `Off`
- `versioning.strategic_cache_policy` — storage/profile-selected cache placement and eviction policy
- `versioning.strategic_cache_max_count` — optional cap on strategic caches per conversation

**Retention dimensions:**

- `versioning.retention_policy` — typed `RetentionPolicy` enum
- `versioning.retention_apply_trigger` — explicit user/profile-selected trigger for retention execution
- `versioning.cleanup_confirmation_threshold` — typed-confirmation requirements for `tombstone_version`, `compact_version_range`, and `hard_delete_version_payload` (per File 06 §7)

**Branching dimensions:**

- `versioning.allow_branch_from_non_leaf` — whether commits after switching to a non-leaf produce branches
- `versioning.label_required_on_branch` — whether new branches must have a label

**Snapshot dimensions:**

- `versioning.snapshot_resolution_cache_enabled` — whether snapshot resolutions cache
- `versioning.snapshot_resolution_failure_policy` — how unresolved snapshots surface typed failures

**Replay dimensions:**

- `versioning.replay_default_mode` — profile-selected default replay mode for user-initiated replay (`Inspect`, `SimulateDeterministic`, or `FullRerun`)
- `versioning.replay_full_rerun_confirmation` — typed-confirmation requirements for `FullRerun` mode

**Sync dimensions:**

- `versioning.sync_divergence_notify` — whether to notify the user when sync produces a divergent branch
- `versioning.sync_auto_switch_to_remote` — whether to auto-switch to the remote branch on sync

**Agent-exposure dimensions** (per File 06 §16.4):

- `versioning.version_tree_visible_to_agent` — `OnRequest` | `Hidden` | `InPrompt`
- `versioning.commit_boundary_set_visible_to_agent` — `InPrompt` (the agent knows the boundary kinds)
- `versioning.context_op_vocabulary_visible_to_agent` — `OnRequest` (the agent can list operations through `tool.search`); `InPrompt` for the commonly-used subset (Mask, Drop, Pin, Recover)
- `versioning.history_query_capabilities_default_zone` — `Borrowable` | `Primary` | `Disabled` — defines the surface zone for `context.list_versions`, `provenance.query_lineage`, and related queries

### 22.2 Settings-Key Convention

Version-graph settings use the dotted-key convention `versioning.<dimension>`. Per-conversation overrides use `versioning.<dimension>.conversation.<conversation_id>`. Per-subsystem, per-surface, per-capability, and per-category overrides use the settings cascade defined by the future Settings, Profiles, and Scope Resolution spec.

### 22.3 Boundary

This section names the settings dimensions. The settings system owns cascade resolution, storage, and the inspector UI. Per-dimension defaults belong to tested settings profiles, not to hardcoded constants in this canonical layer.

## 23. Explicit Rejections

The following shapes are wrong for this layer:

- **Parallel checkpoint systems** — no `file_checkpoints` table, no `SessionCheckpoint` / `FileCheckpoint` / `ToolCallCheckpoint` rows, no shadow-directory checkpoint mechanism, no per-tool-call atomic checkpoint commit. The "checkpoint" vocabulary maps onto the unified version graph; checkpoints in any UI are commit boundaries in the version graph.
- **`MessageVersion` rows** — messages do not version at the row level; the version tree does. The "version of message X" view is reconstructed by walking the version graph to the version where message X was last edited.
- **`VersionSnapshot` table separate from version diffs** — versioning uses per-version diffs against the parent; the materialised view is rebuilt by walking the tree. Storing full snapshots on every version row contradicts the compact-diff discipline. Strategic-cache nodes (§8.6) store materialised-view caches as storage optimisations, not as the canonical version-storage shape.
- **In-place mutation of `ContextVersion` fields** — every field except `label`, `bookmarked`, and `expected_view_hash` is immutable. Observable corrections commit a `Correction` sibling per §4.2. In-place mutation of `diff`, `op_summary`, `committed_at`, `committed_by`, `parent_version_id`, `snapshot_refs`, or any other immutable field is invalid.
- **`pending_ops` buffer as transient in-memory queue** — the buffer is durable on `ConversationVersionState`; the buffer survives restart. Treating it as in-memory state loses user-applied operations across crashes.
- **Implicit commit on switch** — switching with pending operations must follow the configured `versioning.switch_with_pending_behaviour`. An implicit unconfigured commit would bury in-session edits in the wrong place in the tree.
- **Per-operation atomic version commits** — fine-grained operations accumulate in `pending_ops`; the commit boundary fires one version with the net diff. Creating a version per operation creates noise (a 20-operation editing session produces 20 versions of incidental detail) and violates the "commit at meaningful boundaries" rule.
- **Branching that overwrites the prior branch** — when a commit is made after switching to a non-leaf, the new commit creates a sibling branch. Overwriting the prior leaf would lose the alternate history. The canonical mechanism preserves both branches non-destructively.
- **Last-write-wins for sync conflicts** — concurrent commits on two devices produce sibling branches; neither overwrites the other. `if remote.updated_at > local.updated_at { remote } else { local }` logic is invalid.
- **Squashing or implicit merge of sibling branches at sync** — both branches survive. The user explicitly switches between them or explicitly merges; merge-source references preserve contribution provenance without changing single-parent tree topology. No implicit merge ever fires.
- **Snapshot as a stored copy of substrate content** — snapshots are typed references to substrate state at a point in time. The substrate (registry, settings, world, policy, pricing, routing) maintains its own durable event log; the snapshot resolves by walking the log. Storing duplicate substrate content as a snapshot row violates the projection contract and the storage-cost discipline.
- **Token counts or costs stored on `ContextVersion` rows** — per File 01 §8, model-dependent scalars are never stored as unkeyed values. Token counts and costs are computed per `(block_id, tokenizer_id)` per File 08 §13.2; the version graph never stores them as version-row fields.
- **Materialised view as the source of truth** — the materialised view is a projection; the version-graph action log is the substrate. Treating the view as authoritative leads to corruption when projections fall out of sync. The cost of corruption is rebuild, never data loss.
- **Time-based version pruning by default** — per File 01 constraint, time-based behaviour is invalid unless explicitly justified. Time-based policies require explicit user or selected-profile opt-in.
- **Implicit hard-delete of versions** — version cleanup is explicit, typed, and policy-governed. No automated process hard-deletes versions or payloads without user authorisation.
- **Descendant reparenting during cleanup** — tombstoning or cleaning a version must not silently reparent descendants to a different parent. Descendant diffs were computed against their actual parent state.
- **Compaction across branch points** — `compact_version_range` applies only to linear segments. A range containing a branching point must fail with `CompactionBranchingPointInRange`.
- **Sharing restricted fork blocks by default** — cross-conversation forks must omit restricted blocks with `ForkOmitted` placeholders unless explicit policy-approved copy, redaction, or scope promotion occurs.
- **Per-surface version trees** — every conversation has one version tree. Per-surface views (the coder history panel, the system-agent rollback DAG, the comparison board) are projections of the unified tree. Per-surface version trees would fragment the history substrate and break cross-surface composition.
- **Per-message version structs** — versioning happens at the conversation-context level, not per-message. A "message version" is reconstructed by switching versions and observing the active message block.
- **`updated_at` on block rows** — blocks are immutable; `updated_at` is invalid. Per File 08 §6.2, edits create siblings. Sync-resolution logic that compares `updated_at` is invalid; the version graph is the conflict-resolution substrate.
- **Time-based mask / drop / lifecycle transitions** — per File 08 §6.7 and File 01 constraints, no implicit time-based lifecycle transition. Compaction policies invoke explicit `Mask` / `Drop` operations driven by their own logic, never by clock time.
- **Treating `ContextVersion` and `Block` as the same primitive** — `ContextVersion` is the version-graph node addressing a conversation's view-state. `Block` is the durable content carrier. A conversation has many versions; each version references many blocks; blocks live in the unified pool addressable by any conversation. The two are distinct primitives that compose.
- **Treating `Projection` as authoritative for any durable fact** — projections are derived. Any durable fact that exists only in a projection is invalid. The substrate must produce the fact; the projection reads it.
- **Snapshot-as-full-prompt-audit** — capturing the full assembled prompt context as a separate audit record at every model call is the wrong shape. File 11 reconstructs the materialised view input; Context Assembly, File 07, and File 10 reconstruct the final model request, callable declarations, snapshots, and provider invocation record.
- **`expected_view_hash` as the source of truth for view content** — the hash is a verification artifact; the action log is the substrate. A hash mismatch triggers rebuild, never trust-the-hash-over-the-substrate.
- **Operation sequence as reconstruction source** — the committed `VersionDiff` is the canonical reconstruction input. Operation-sequence ledger facts are audit and UI inspection data; switching and rebuilds must not depend on replaying every pending operation event.
- **Forging a `VersionCommitted` ledger entry without producing a version row** — per File 10 §3.7, ledger entries that name a version_id must reference an existing version; orphan references are rejected at ledger commit.
- **Storing per-version aggregate metrics (total tokens, total cost, total blocks)** — derived; never stored on the version row. Computed on demand from the substrate; cached as separate projections per §16.3.
- **Version-graph events emitted outside the canonical bus** — per File 10 §5, all events flow through the unified bus. Side-channel notification for version-graph operations is invalid.
- **Diffs that reference blocks not in the pool** — a `VersionDiff` whose `added`, `removed`, `lifecycle_changes`, `pin_changes`, or `position_changes` references a non-existent `block_id` is rejected at commit; the producing operation is undone and re-tried after the block is committed.
- **Snapshot ids that lack global uniqueness or get reassigned** — every snapshot id must be unique within the install, stable, and never reused.
- **Sync of `dag_node_output_cache`, `rate_limit_state`, or audit-log hash chain** — these are explicitly per-device. Cross-device sync of any of them violates the projection contract and the per-device integrity guarantee.

## 24. Consequences for Later Specs

Later specs must follow these rules:

- Later specs must not introduce parallel history, checkpoint, rollback, undo, fork, or versioning primitives. They consume `ContextVersion`, `VersionDiff`, `ContextOp`, snapshots, File 10 events, and the materialised-view contract defined here.
- Storage and persistence must store the required `ContextVersion` fields, `ConversationVersionState`, active `context_view`, labels, bookmarks, tombstones, compacted segments, payload-deletion provenance gaps, hashes when present, and snapshot references. Physical schema, indexing, migration, and storage optimisation choices remain storage-spec concerns.
- Sync, import, export, and portability must preserve version topology, parent links, `merge_source_version_ids`, tombstones, compacted segments, block identity, content-addressing semantics, and per-device active pointers unless a later sync spec explicitly defines a shared-pointer mode. Last-write-wins remains invalid.
- Context assembly and compaction consume the materialised view as input. Compaction that changes durable context state commits explicit `ContextEdit`, `Consolidation`, tombstone, or range-compaction operations; it must preserve evidence/provenance closure instead of silently severing chains.
- Retrieval, memory, knowledge, artifact, claim, validation, workspace mirror, and UI-history surfaces are projections or sibling-block version chains over this substrate. They may cache derived views, but they do not own separate history stores.
- Model strategy, provider, pricing, settings, world, routing, policy, perception, evaluation, and replay specs consume snapshot identities and the File 10 ledger to reconstruct past execution state. File 11 provides the version-graph substrate; those specs own their own replay details.
- Extensions, plugins, MCP integrations, workflows, automation, quality control, and work surfaces register custom op summaries, context ops, metadata changes, derived-state changes, snapshot kinds, and projections through the File 05 proposal-first mechanism. They must not bypass the versioning operation surface or the File 06 policy layer.
- UI and customization specs render version timelines, comparison views, history panels, rollback surfaces, inspectors, undo/redo/restore/revert affordances, and fork views from the canonical data contracts here. Presentation can vary freely; the substrate cannot.

Specific integration contracts will be stated in those files when they are written.
