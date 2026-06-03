# Workspaces and Materialization

## Status

Canonical. This file defines the `Workspace` primitive and the materialization mechanism that mirrors durable substrate content to and from the local filesystem. It realizes the workspace-identity and disk-mirror contracts that Files 01–23 declared and delegated to the Workspaces and Materialization spec — this file — and introduces the net-new `Workspace` and `Worktree` primitives those files referenced without owning. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `Workspace` primitive — a durable scoped context that may bind to a local directory for files, execution, settings, and materialization for one or more conversations (realizes `core.workspace-model`, File 01 §3)
- the `WorkspaceRecord` — the durable identity, its field set, and the locality split that lets a workspace's logical identity travel while its device-local root binding is absent or rebinds per device
- workspace lifecycle: create, open (mount an existing directory), close, archive, restore, delete, and the temporary quick-start variant
- workspace relocation, integrity, and recovery (moved, renamed, permission-changed, drive-unmounted, deleted directories)
- the conversation–workspace binding and the `workspace` scope label other files already consume
- the workspace internal layout — the per-workspace `.atlas/` directory — and its relationship to the data-root `~/.atlas/` directory File 20 places
- workspace instruction-file identity (the `ATLAS.md` family and the `.atlasignore` ignore file)
- **Materialization** — the disk↔substrate mirror: the rule that the on-disk workspace tree is a projection of the selected `materialization_head`, the materialized-path resolution algorithm, the disk→substrate sync loop for external edits, and the freshness/atomic-write discipline
- mounted projects, external-codebase ingestion, and multi-root workspaces
- worktree directory identity and lifecycle (the git working-copy and equivalent copy isolation primitive directories used for parallel/isolated child-run work)
- the workspace as a substrate family: its persistence over File 20, its export/import over File 21, and its storage accounting and reclamation
- the workspace world-model and perception integration points
- the workspace capability surface, event vocabulary, and settings

This file does not define:

- the block model, block content variants, or `content_hash` — File 08 owns those; this file uses `FileAttachment` and `Artifact` blocks and projects them to disk
- artifact identity, the `ArtifactKind` catalogue, the `MaterializationPolicy` enum, the per-artifact `materialized_paths` record, or the per-artifact disk→entity sibling-commit contract — File 09 owns those; this file owns the workspace-side path resolution and the sync-loop mechanism File 09 §7.3/§7.5 delegate
- the version graph, the materialized view (`context_view`), branching, forking, or the version-switch action log — File 11 owns those; this file declares that disk state is a projection of the selected workspace materialization head and consumes the materialized view
- the storage engine, the content-addressed blob store, the data-root on-disk layout, projection rebuild orchestration, or the physical locality partition — File 20 owns those; this file resolves external content from the blob store and names the materialization directories File 20 places
- the sync transport, conflict resolution, the `PortablePackage` format, or the import-pipeline stages — File 21 owns those; this file declares that workspace export/import rides them
- the secret boundary, egress governance, or untrusted-content defense — File 22 owns those; this file consumes them (no unredacted secret in a materialized file; workspace export through governed egress; ingested code carries no authority)
- filesystem-boundary enforcement, the atomic-write primitive, sandbox/process isolation, or per-instance home isolation — File 23 owns those; this file materializes within the region File 23 confines and writes through File 23's atomic-write chokepoint
- retrieval/indexing of workspace files (File 12), instruction-source inclusion in the model request (File 13), or the world-entity catalogue (File 18)
- per-surface workspace workflows, editor/terminal/browser views, or surface-specific materialization (Coder File 27, Web File 28, Data Processor File 29, Teacher File 30, GUI Control File 31, and System Agent File 32 surface specs); this file is horizontal and surface-neutral

## Source Resolution

Families reviewed: the workspace-management material (`domains/coder/workspace-management.md`, `domains/coder/README.md`, `atlas3-core/TODO.md` §3/§6/§7/§15/§20, `unit08-coder.md`); the workspace-record and directory-layout material (`unit12-infrastructure.md` D12.1 §28 / D12.13, `unit15-ux-distribution-files-glossary.md` D15.F.2–F.5 / D15.G.2, `GLOSSARY.md`, `infrastructure/database.md`, `infrastructure/lifecycle.md`); the materialization and disk-sync material (`files/file-management.md`, `files/README.md`, `tools/file-operations.md`, `domains/coder/checkpoints-undo.md`, `domains/coder/session-logging.md`, `cross-cutting/artifacts.md`, `unit06-tools.md`); the worktree material (`infrastructure/git.md`, `domains/coder/git-integration.md`, `claude-code-compressed.md`, `archon-compressed.md`, `oh-my-codex-compressed.md`, `kilocode-compressed.md`); the instruction-file material (`systems/16-knowledge-base.md`, `unit14-systems.md` D14.KB.5, `agent-zero`, `warp`, `goose`, `codebuff`); the boundary/security material (`cross-cutting/security.md`, `cross-cutting/actions.md`, `open-cowork-compressed.md`); the strategic target-state review (`codex_recommendations.md` §1.2/§7/§11/§14); and the existing-ecosystem worktree and project-container patterns (`continue`, `cline`, `affine`, `space-agent`, `hermes-agent`, `multica`).

Resolution rule: this file realizes, it does not re-own. Every substrate's semantics stay with its owning file (blocks 08, artifacts 09, version graph 11, storage 20, sync 21, security 22, sandbox 23). This file owns workspace identity, the workspace lifecycle, and the disk↔substrate mirror, and supplies each to the layer that consumes it.

Resolved tensions:

- **Workspace identity — "directories, not database entities" versus a durable record.** `file-management.md` states "Workspaces are directories, not database entities... they don't have a separate `workspaces` table because they don't need one"; `unit12` D12.1 §28 observes "A workspace concept has been referenced repeatedly across units 2, 8, 9, 10, 11 but no `workspaces` table exists" and makes it first-class. This file resolves toward the durable `WorkspaceRecord` (§3): relocation, archival, missing-state recovery, and binding multiple conversations to one workspace each require a stable identity decoupled from the current path, which the "no table" position cannot represent. The GLOSSARY's meaning — "a directory on disk; identity is the path plus the chats bound to it" — is preserved as the *definition*; the record gives that meaning a stable handle.
- **Disk mirror — independent store, shadow-checkpoint store, or projection.** Eight Coder-surface source files describe a `file_checkpoints` table and `.atlas/checkpoints/<session>/<file>.snap` shadow directories; `checkpoints-undo.md`, `unit08` Recommendation 1, `file-operations.md`, and the GLOSSARY all delete them in favor of "the version tree is the single history mechanism; disk state is the materialized view of the active version." This file adopts the projection model (§10), consistent with `version.consequences-for-later-specs` (File 11 §24): the workspace mirror is a projection over the version-graph substrate and owns no separate history store.
- **Worktree placement — inside the workspace, sibling of the workspace, or under the data root.** `git-integration.md` places worktrees as siblings of the workspace root; the GLOSSARY's `Worktree Manager` references `.atlas/worktrees/<chat-id>/<agent-id>/`; `unit15` D15.F.5 places them under the data root at `~/.atlas/worktrees/`. This file resolves toward data-root placement (§15) to keep the user's project directory pristine and consistent with File 20 §8's placement of per-workspace materialization directories under the data root.
- **Workspace-first as the root model.** `codex_recommendations.md` §1.2 rejects workspace-first as the universal root ("Workspace-first models fit coding but underfit research, learning, and general operating flows"), keeping Task/Artifact/Evidence/Execution as the durable root family. This file honors that: a workspace is a system capability and a durable scoped context, never a mandatory doorway (`core.workspace-model`, File 01 §3), and conversation-only work needs no visible workspace.

## 1. Chosen Model

Anchor: `workspace.chosen-model`

A `Workspace` is a durable scoped context that can bind to a local directory for files, execution, settings, history, and materialization of one or more conversations. It is the realization of `core.workspace-model` (File 01 §3): "a durable scoped environment for files, state, tools, history, and user-visible work materialization."

The model has two halves and one invariant binding them:

- **Identity.** A workspace has a durable `WorkspaceRecord` (§3) with a stable `workspace_id` independent of any local directory path. The record is a source-of-truth substrate family; its device-local root binding may be absent, may point at a local root, or may require rebind (§4).
- **Materialization.** The on-disk file tree under a bound workspace root is a **projection** of a selected `materialization_head` over the block pool (`version.materialized-view-context-view`, File 11 §7), not an independent store. The version graph is the single history mechanism; the disk tree is rebuilt to match the selected conversation/version, and external edits to the disk tree commit back as sibling-block versions (§10–§12). The disk mirror holds no durable fact the substrate does not; its loss is a rebuild, never data loss (`core.projection`, File 01 §6.11).

The binding invariant: **a workspace exists as a durable scoped context whether or not it is surfaced as a visible workspace.** A conversation's durable scoped context (`intent.conversation`, File 02 §2.1) is its bound workspace; that workspace may be exposed as a user-facing workspace surface or remain latent while the user stays in the conversation interface (`core.workspace-model`, File 01 §3). Workspace-first is one presentation, never the universal root model.

## 2. Boundaries with Adjacent Layers

Anchor: `workspace.boundaries`

### 2.1 With File 01 (Core)

This file realizes `core.workspace-model` (§3), obeys `core.non-destructive-by-default` (§7.13) for materialization and reclamation, computes every hash over a declared `CanonicalEncoding` (`core.canonical-hash`, §7.14), treats the disk mirror as a `Projection` (§6.11), and resolves workspace settings through the `core.settings-system` (§6.8). The `Workspace`, `WorkspaceRecord`, and `Worktree` are canonical noun-objects.

### 2.2 With File 02 (Conversation, Intent, Task) and File 04 (Execution)

A conversation's durable scoped context is its bound workspace (§7). A workspace holds one or many conversations over time (`intent.conversation-state`, File 02 §2.2). Run outputs that are file materializations (`run.output-semantics`, File 04 §24) land in the workspace through this file's materialization path; isolated child-run work that needs a private working copy uses a worktree (§15), whose directory identity this file owns while File 04 §16 owns the isolation-primitive selection and the shared-workspace exception.

### 2.3 With Files 08, 09, and 11 (Blocks, Artifacts, Version Graph)

File 08 owns the `FileAttachment` and `Artifact` block kinds and `content_hash`; this file projects those blocks to disk and commits sibling blocks on external edit. File 09 owns the `MaterializationPolicy` enum, the per-artifact `materialized_paths` record, and the per-artifact disk→entity sibling-commit contract (`artifact.artifact-materialization` §7.3, `artifact.materialized-paths-provenance` §7.4, `artifact.disk-entity-sync` §7.5); this file implements the `InWorkspace` path-resolution algorithm File 09 §7.2 delegates and owns the workspace-tree sync loop. File 11 owns the version graph and the materialized view; this file declares the disk tree a projection of that view and consumes `MaterializationRecorded` and the `ExternalEdit` `ContextOp` (File 11 §5). The workspace mirror introduces no parallel history store (`version.consequences-for-later-specs`, File 11 §24).

### 2.4 With File 20 (Storage) and File 21 (Sync)

File 20 owns the storage engine, the content-addressed blob store, the data-root on-disk layout, and the physical locality partition; this file resolves external file content from that blob store, places its directories within the data root File 20 lays out, and persists the workspace and worktree records as durable families File 20 stores. File 21 owns the sync transport, conflict resolution, the `PortablePackage`, and the import pipeline; this file declares workspace export/import rides them and that workspace identity is syncable while device-local root bindings are not.

### 2.5 With File 22 (Security) and File 23 (Sandbox)

File 22 owns the secret boundary, egress governance, and untrusted-content defense; this file forbids unredacted secrets in materialized files, routes workspace export through governed egress, and treats ingested external code as carrying no authority. File 23 owns filesystem-boundary enforcement, the atomic-write primitive, and per-instance home isolation; this file materializes only within the region File 23 confines (`sandbox.filesystem-enforcement`, File 23 §7), writes through File 23's atomic-write chokepoint, and never reaches the operating-system file interface except through File 23's service-trait. A worktree directory is one filesystem boundary File 23 enforces, never a private path that bypasses it (`sandbox.consequences-for-later-specs`, File 23 §21).

### 2.6 With Files 12, 13, 18, and 19

This file owns workspace instruction-file identity (the `ATLAS.md` family, §9); File 12 indexes those files as workspace-scoped knowledge entries (`retrieval.workspace-instruction-files-atlas-md`, File 12 §15) and File 13 decides their inclusion in the model request (`context.instruction-sources-workspace-files`, File 13 §16). This file exposes active workspaces as `Workspace` world entities (`world.world-entity`, File 18 §4.3); File 18 owns the entity catalogue and File 19 captures workspace and repository state as filesystem observations.

### 2.7 With the per-surface and later specs

The per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) project this file's workspace and materialization primitives into surface-specific views (editor file trees, browser download directories, dataset working files) and never introduce a private workspace model or a parallel disk-history store. This file owns the horizontal substrate; surfaces own the presentation and the surface-specific capabilities.

## 3. The `Workspace` and the `WorkspaceRecord`

Anchor: `workspace.workspace`

### 3.1 Definition

A `Workspace` is a durable scoped context for files, execution, settings, history, and materialization. Its identity is a stable `workspace_id`; its device-local directory binding may be absent, bound to a local root, or rebound without changing the identity.

### 3.2 Purpose

Every prior file uses `workspace` as a scope label (`block.block-scope` File 08 §11, `policy.lease-primitive` File 06 §11, `ledger.execution-ledger` File 10 §3.5, `world.world-entity` File 18 §4.2, `MemoryScope::Workspace` File 14, `KnowledgeScope::Workspace` File 12) and as a foreign key (`workspace_id` on memory, knowledge, retrieval, log, and artifact records), yet none defines what the identifier resolves to. A durable `WorkspaceRecord` gives that identifier a single owner, a lifecycle, and a relocation-safe identity, so a moved or renamed directory does not orphan everything keyed to it.

### 3.3 The `WorkspaceRecord`

The `WorkspaceRecord` is a durable source-of-truth substrate family (§22). Its minimum field set:

- `workspace_id` — stable opaque identifier (UUID), assigned at creation, never reused, never derived from the path; the value every `workspace_id` foreign key across the canon resolves to
- `name` — user-facing display name; defaults to the binding conversation's name; mutable
- `binding_state` — device-local root binding: `Unbound`, `Bound { root_path }`, or `NeedsRebind { reason }`; materialization requires `Bound`
- `original_path` — the absolute path at creation or first bind on this device, retained for relocation heuristics when safe
- `relocation_history` — an ordered list of `{ at, old_path, new_path, reason }` entries recording every rebind on this device
- `lifecycle_status` — syncable logical state: `Active`, `Archived`, `DeletedTombstone`, with the `Custom { code }` extension reserved
- `availability_status` — device-local availability state: `Available`, `Missing { reason }`, `PermissionDenied`, `DriveUnmounted`, `NeedsRebind`, with the `Custom { code }` extension reserved
- `materialization_head` — optional device-local pointer `{ conversation_id, version_id, selected_by, selected_at }` naming the conversation/version projection that currently owns the bound root's mutable disk mirror
- `profile_id` — optional binding to a settings/layout profile (`settings.profiles`, File 15); syncable
- `kind` — a closed canonical enum: `Managed` (an Atlas-created directory under the data root), `Mounted` (an existing external user directory opened into a workspace, §14), `Temporary` (a quick-start scratch workspace, §5.4)
- `is_temporary` — true for quick-start workspaces not yet saved to a permanent location
- `vcs_binding` — optional stable version-control binding metadata when the root is a repository: `{ kind, repository_root_ref, default_remote_ref, initialized_by_atlas }`, where `kind` is `None`, `Git`, or `Custom { name }`; live branch and dirty state are world/observation facts, not workspace-record identity
- `created_at`, `updated_at`, `last_accessed_at` — full-granularity timestamps

Derived, never stored as source-of-truth (computed on demand, §17): `size_bytes`, `file_count`, git dirty state, current branch, and storage breakdown. Model-dependent or live values (git status, file counts) are world facts (§18) or projections, not record fields.

### 3.4 Required

- A `workspace_id` is assigned exactly once and is immutable; relocation changes `binding_state`, never `workspace_id`.
- `root_path` uniqueness is enforced among `Bound` workspaces on a device; opening a directory already bound to an active workspace resolves to that workspace rather than creating a second record (`Mounted` deduplication, §14.3).
- Every conversation binds to exactly one workspace at a time (§7); a workspace binds zero or more conversations.
- The record carries no absolute path in any syncable field except as device-local data excluded from replication (§4).

### 3.5 Boundary

This file owns the `WorkspaceRecord` field set and identity rules. File 20 owns its physical schema, table placement, and migration; File 18 owns the live `Workspace` world entity projected from it; File 15 owns the `profile_id` it references.

## 4. Workspace Locality and the Identity/Path Split

Anchor: `workspace.locality`

### 4.1 Definition

Workspace locality is the rule that a workspace's logical identity is portable across devices while its physical root binding is device-local, optional, and rebinds on each device.

### 4.2 Purpose

A bound `root_path` is an absolute path on one machine — `/home/alice/projects/atlas` — and is meaningless on another device, which may have a different home directory, drive layout, or operating system. But the user's named project, its profile binding, and the conversations bound to it are part of the user's portable identity and should follow them across devices. A per-table sync filter that tried to replicate `root_path` would carry a value that resolves to the wrong directory or to nothing. Splitting the record by locality makes "the path does not travel, the identity does" structural rather than a filter that can be misconfigured (`storage.physical-layout-locality`, File 20 §8).

### 4.3 Rule

- The `WorkspaceRecord` splits by locality (`settings.locality-sync-export`, File 15 §18; `storage.physical-layout-locality`, File 20 §8). The **syncable** part is the logical identity: `workspace_id`, `name`, `profile_id`, `kind` (excluding `Temporary`), `lifecycle_status`, stable `vcs_binding`, and the set of bound conversation identities. The **device-local** part is the physical binding and live projection state: `binding_state`, `original_path`, `relocation_history`, `availability_status`, `materialization_head`, and observed VCS facts.
- The device-local part lives in the device-local substrate (`atlas-local.db` per File 20 §8.3); the syncable identity lives in the syncable substrate. A cross-partition reference is a soft identity reference (`storage.durable-substrate`, File 20 §3.4), never an enforced foreign key spanning the partition.
- On a device that has not yet bound a synced workspace identity, the workspace resolves to `binding_state: Unbound`; reads never fail, and the bound conversations remain available with materialization deferred until the bind.
- `Temporary` workspaces never sync (§5.4).
- This locality rule is the workspace-specific realization of the replication-eligibility contract (`portability.what-replicates`, File 21 §11): stable workspace definitions are syncable, device-specific bindings are not.

### 4.4 Boundary

This file declares the identity/path split and which fields are syncable. File 20 places the two partitions; File 21 replicates the syncable identity and rebinds the path on receive; File 15 owns the locality vocabulary.

## 5. Workspace Lifecycle

Anchor: `workspace.lifecycle`

### 5.1 Definition

The workspace lifecycle is the closed set of state transitions a workspace passes through: creation, opening, closing, archival, restoration, and deletion, plus the temporary quick-start variant.

### 5.2 Creation

A workspace is created by one of three triggers: a new conversation requesting a fresh workspace, opening an existing directory (§5.3), or a quick-start request (§5.4). Creation of a `Managed` workspace:

1. allocates a `workspace_id` and a directory under the data root (the canonical default is `<data-root>/workspaces/<workspace_id>/`, owned by File 20 §8 and named here);
2. creates the workspace-internal `.atlas/` directory and its baseline contents (§8);
3. optionally initializes version control when `git_init` is enabled (a settings default, §21), creating an initial commit and a `.gitignore` seeded with the workspace-internal exclusions (§8.4);
4. optionally seeds from a template (`empty`, a language template, or a named template) when requested;
5. writes the `WorkspaceRecord` (§3) and binds the requesting conversation (§7);
6. emits `WorkspaceCreated` and `WorkspaceOpened` (§20).

Creation is a `WorkspaceWrite`-tier capability (§19). The directory and the record are created in one logical operation; a failure after directory creation but before the record commit is reconciled at startup (the orphaned directory is offered for adoption or cleanup, never silently deleted).

### 5.3 Opening (mounting an existing directory)

Opening binds an existing external directory as a `Mounted` workspace (§14): the path is validated and contained (`sandbox.filesystem-enforcement`, File 23 §7), a preview shows existing files, ignored files, `.atlas/` status, expected materialization writes, import/index behavior, and collision risk, and the workspace-internal `.atlas/` directory is created only if the open-without-`.atlas` setting and policy allow it. Opening a non-empty, previously unrelated, or cross-trust/sensitivity target escalates to `UserApproval` or typed confirmation as appropriate. Opening a directory already bound to an active workspace resolves to the existing record (§3.4). Opening emits `WorkspaceOpened`.

### 5.4 Quick-start and temporary workspaces

A quick-start workspace is a `Temporary` workspace created without a user-chosen permanent location, with a disposable device-local binding under the data root's scratch area when materialization is needed (the canonical default `<data-root>/tmp/quickstart-<workspace_id>/`). It is `is_temporary = true`, excluded from the persistent workspace list, and never synced (§4). On conversation close, the user is offered to save it to a permanent location (promoting it to `Managed` or `Mounted`, which assigns a durable local binding and clears `is_temporary`) or to discard it. A discarded temporary workspace deletes only its scratch mirror; its bound conversation's durable history (blocks, version tree) survives in the substrate independent of the disk mirror.

### 5.5 Closing

Closing releases the workspace's live, device-local runtime state (open handles, the active filesystem watcher, in-memory projections) without destroying any durable fact. Closing a non-temporary workspace with unsaved external-edit state surfaces the pending changes for commit-or-discard before the watcher detaches (§12); the version tree and block pool are unaffected by close. Closing emits `WorkspaceClosed`. Reopening rebuilds the disk mirror and the live projections from the selected `materialization_head` (§10).

### 5.6 Archival and restoration

Archival sets `lifecycle_status = Archived` and may move the directory to an archive area (the canonical default `<data-root>/workspaces/.archive/<workspace_id>/` for `Managed` workspaces; `Mounted` workspaces are flagged archived without moving the user's directory). An archived workspace is retained, listed under an archived filter, and read-inspectable; its bound conversations remain visible but their materialization is disabled until restoration. Restoration sets `lifecycle_status = Active` and rebinds the directory if needed. Archival and restoration are non-destructive (`core.non-destructive-by-default`, File 01 §7.13).

### 5.7 Deletion

Deletion is the only destructive workspace operation and is never automatic. `workspace.delete` is a capability with `permission_floor: Denied` and a typed-confirmation override (`policy.effective-tier-resolution`, File 06; `run.approval-during-execution`, File 04 §11). It tombstones the `WorkspaceRecord` by setting `lifecycle_status = DeletedTombstone`; it does not erase the `workspace_id`. The tombstone preserves at least `workspace_id`, prior name if safe, deletion actor/source, deletion time, deletion reason, bound conversation ids, and a sensitivity-safe path description. A `Managed` workspace's directory payload may be deleted after confirmation; a `Mounted` workspace removes the binding and the `.atlas/` internal directory by default but never deletes the user's source files unless the user explicitly requests a separate typed-confirmation reclamation operation. Bound conversations, durable blocks, versions, and artifacts remain governed by their own hard-delete contracts (`block.hard-delete`, File 08 §6.6; `artifact.artifact-tombstones`, File 09 §8). Hard-deleting the tombstone itself is allowed only when no durable references remain, or when the user explicitly accepts a typed provenance gap through File 21/File 10 mechanisms. Deletion emits `WorkspaceTombstoned` or `WorkspacePayloadDeleted` as appropriate and records an audit entry (`security.audit-crypto`, File 22).

### 5.8 Boundary

This file owns the lifecycle states and transitions. File 04 owns the run lifecycle that operates within a workspace; File 11 owns the version-tree history that survives workspace deletion; File 22 owns the audit entry deletion records.

## 6. Relocation, Integrity, and Recovery

Anchor: `workspace.relocation-recovery`

### 6.1 Definition

Relocation is rebinding a workspace to a new local directory without changing its `workspace_id`. Recovery is the resolution of a workspace whose local binding is absent or cannot currently be reached.

### 6.2 Purpose

A workspace directory may be moved, renamed, have its permissions changed, live on an external drive that is unplugged, or be deleted outside Atlas. Because everything keyed to `workspace_id` (history, memory, knowledge, logs, artifacts) is decoupled from the path (§3), the workspace survives these events; this section defines how the system detects an unreachable directory and offers recovery without losing the bound work.

### 6.3 Rule

- On binding a workspace (open, conversation activation, startup), the system resolves `binding_state`. When a bound path is unreachable, `availability_status` becomes `Missing { reason }` and a typed `reason` is recorded — a closed canonical enum: `Moved`, `Renamed`, `PermissionDenied`, `DriveUnmounted`, `Deleted`, `Unknown`.
- A workspace with `Unbound`, `NeedsRebind`, or `Missing` availability surfaces a recovery affordance, never a silent failure or a fabricated empty directory. The recovery options are: **rebind** (the user locates the directory; `workspace.rebind` records the new `binding_state` and appends to `relocation_history` after preview), **archive** (`workspace.mark_archived` flips `lifecycle_status` and disables edits while preserving the conversation), or **tombstone/delete payload** (tombstone the workspace or remove the local binding while preserving substrate history per §5.7).
- The system may offer a heuristic relocation suggestion — a basename match against likely parent directories — but never rebinds automatically; rebinding is an explicit user action because a wrong rebind would materialize a different directory's contents over the workspace.
- Reads of a `Missing` workspace's durable history (conversations, blocks, versions, artifacts) never fail; only disk materialization is deferred until the workspace is rebound (`core.projection`, File 01 §6.11 — the disk mirror is a projection, so its absence is a deferred rebuild, not data loss).
- Relocation of a `Managed` workspace updates the bound root and re-resolves every relative materialized path against the new root (§11); materialized paths are stored workspace-relative precisely so a move re-resolves rather than breaks (`artifact.materialized-paths-provenance`, File 09 §7.4). Rebinding to a non-empty, unrelated, or mutation-risking directory requires the preview and tier escalation defined in §19.

### 6.4 Boundary

This file owns relocation and recovery. File 19 captures the filesystem-change observations that may signal a move; File 18 reflects workspace availability in the world model; File 20's startup reconstruction surfaces unresolved bindings.

## 7. Conversation–Workspace Binding and the Workspace Scope

Anchor: `workspace.conversation-binding`

### 7.1 Definition

The conversation–workspace binding is the association between a conversation and the workspace that provides its durable scoped context. The `workspace` scope is the visibility and addressability scope this binding establishes, already consumed by Files 06, 08, 10, 11, and 18.

### 7.2 Rule

- Every conversation binds to exactly one workspace at a time; that workspace is the conversation's durable scoped context for storage, execution, settings, and materialization (`intent.conversation`, File 02 §2.1). A conversation may rebind to a different workspace over its life (`intent.conversation`, File 02 §2.2 — "one or many workspaces over time").
- A workspace binds zero or more conversations. The single-conversation case (one workspace per conversation) and the project case (many conversations sharing one workspace) are both valid; which is the default is a setting (§21).
- The `workspace` scope label (`block.block-scope`, File 08 §11) is the broadest-but-one visibility scope: a `workspace`-scoped block, lease, ledger entry, memory entry, or world entity is visible across the conversations bound to the workspace and narrower than `global`. This file is the owner of what that label resolves to; it does not redefine the scope ordering, which File 08 fixes.
- Cross-workspace access (a capability call whose resolved touched resource lies in another workspace) is not silently allowed: it escalates the effective permission tier (`PathAwareWorkspaceResolver` pattern, `capability.touched-resources` File 05 §6) and requires `UserApproval` regardless of the file's relative location, with the approval surfacing which other workspace is targeted (§19).
- The binding is durable and syncable (the bound conversation set is part of the workspace's portable identity, §4.3); any local root it resolves to is device-local.

### 7.3 Boundary

This file owns the binding and what the `workspace` scope resolves to. File 08 owns the scope enum and ordering; File 06 owns the lease-scope matching against the workspace; File 02 owns conversation identity.

## 8. Workspace Internal Layout

Anchor: `workspace.internal-layout`

### 8.1 Definition

The workspace internal layout is the per-workspace `.atlas/` directory under the workspace root, holding workspace-local configuration and Atlas-internal materializations, distinct from the data-root `~/.atlas/` directory that holds cross-workspace state.

### 8.2 Purpose

Two kinds of Atlas state are rooted at a directory named `.atlas/`, and they must not be conflated. The **data root** (`~/.atlas/` on Linux/macOS, the platform application-data directory elsewhere — owned by `storage.physical-layout-locality`, File 20 §8) holds cross-workspace state: the substrate databases, the content-addressed blob store, the worktree directories, the ingest area, the secret vault, and the audit overlay. The **workspace-internal `.atlas/`** (under the user's workspace root) holds state that belongs to that one workspace and travels with its directory: workspace settings, environment files, custom command definitions, materialized session-export views, and Atlas-internal artifact materializations. This file owns the workspace-internal `.atlas/`; File 20 owns the data root.

### 8.3 Rule — the workspace-internal `.atlas/` directory

The canonical baseline contents of `<workspace_root>/.atlas/`:

- `settings.json` — the workspace-scoped settings overlay (§21), a materialized File 15 settings layer and import/edit source, never a parallel settings store
- `.env`, `.env.local` — workspace environment files; both are secret-scanned and governed by File 22. `.env.local` is device-local and git-ignored by default; `.env` is portable only when values are non-secret or represented as secret references. Raw secret values are never exposed to the model, ledger, sync, or export
- `commands/` — custom command definitions (the workspace's slash commands), each a declarative definition resolved through the capability system, never an out-of-band execution path
- `logs/<task-id>/` — the materialized session-export view: a projection of the task's version-tree and execution history (a human-readable summary, an activity view, optional per-call captures), produced on demand or at task completion, never a parallel live write path and never a source of truth (`storage.projection-store`, File 20 §7)
- `artifacts/<artifact_id>/<version_id>/` — Atlas-internal artifact materializations for artifact versions that have no natural workspace-relative location (§11), the realization of File 09 §7.2's default `InWorkspace` path
- `.gitignore` (when the workspace is a repository) — seeded so the Atlas-internal entries that should not be version-controlled are excluded (§8.4)

The workspace-internal `.atlas/` directory does **not** contain a checkpoint or shadow-history directory: there is no `.atlas/checkpoints/` and no per-file snapshot store. File history is the version tree (§10, `version.consequences-for-later-specs`, File 11 §24).

### 8.4 Rule — git-ignored Atlas-internal entries

When the workspace root is a git repository, the materialized Atlas-internal entries that are device-local or rebuildable are git-ignored by default: `.atlas/.env.local`, `.atlas/logs/`, and `.atlas/artifacts/` where it holds rebuildable projections. Workspace-portable entries the user may want version-controlled (`.atlas/settings.json`, `.atlas/commands/`, the `ATLAS.md` instruction files) are not git-ignored by default, but their contents still pass File 15 settings validation and File 22 secret scanning. The exact default ignore set is a setting (§21).

### 8.5 Boundary

This file owns the workspace-internal `.atlas/` directory identity and baseline contents. File 20 owns the data-root layout the worktree, blob, and ingest directories live under; File 15 owns the settings cascade `.atlas/settings.json` participates in; File 09 owns the artifact whose version materializes under `.atlas/artifacts/`.

## 9. Workspace Instruction Files

Anchor: `workspace.instruction-files`

### 9.1 Definition

A workspace instruction file is a workspace-local, user-authored source — the `ATLAS.md` family — that carries durable guidance scoped to the workspace or a directory within it. This file owns the instruction file's identity and discovery; File 12 owns its indexing and File 13 owns its inclusion in the model request.

### 9.2 Rule

- `ATLAS.md` is the default instruction-file name; the name, the lookup order, enablement, and inclusion behavior are settings (`retrieval.workspace-instruction-files-atlas-md`, File 12 §15; `context.instruction-sources-workspace-files`, File 13 §16).
- The instruction-file hierarchy resolves from general to specific: a global file under the data root (`<data-root>/instructions.md`), the workspace root `ATLAS.md`, surface- or subsystem-qualified variants such as `ATLAS.<surface_id>.md`, per-directory `ATLAS.md` files discovered by walking from the active selection toward the workspace root, and a git-ignored machine-local override (`ATLAS.local.md`). The recognized qualifier set comes from the registered subsystem/surface catalogue, not from a separate domain taxonomy. Per-directory files apply when the active work lies under their directory.
- Instruction files are workspace-scoped knowledge entries; this file establishes their identity and discovery, File 12 indexes them (`KnowledgeScope::Workspace`, marked featured, tagged with their directory), and File 13 decides inclusion. Specificity orders instruction sources only within the same authority class and source family. Authority class, sensitivity, trust, source attribution, and user/system precedence remain governed by File 13; knowledge indexing alone grants no instruction authority.
- Instruction files from mounted or ingested external codebases carry no instruction authority until accepted or policy-classified. Their content is untrusted source data by default, with source attribution and instruction-boundary markers rendered per File 13 and File 07.
- Instruction files are agent-writable only through the same proposal-and-approval path as any user content: the agent proposes an addition, the user approves, and the edit commits as a sibling block and materializes to disk through the ordinary materialization path (§10). The agent never edits an instruction file out of band.
- The workspace ignore file (`.atlasignore`, name configurable) uses git-ignore-style patterns and bounds which workspace files participate in automatic materialization, indexing, and disk→substrate capture (§12). It is itself a workspace file, discovered at the workspace root and at subdirectories.

### 9.3 Boundary

This file owns instruction-file identity, the lookup hierarchy, and the ignore file. File 12 owns indexing them as retrievable knowledge; File 13 owns their model-request inclusion and authority.

## 10. Materialization — the Disk↔Substrate Mirror

Anchor: `workspace.materialization`

### 10.1 Definition

`Materialization` is the process by which durable substrate content — file blocks, artifact versions, generated outputs — becomes addressable on the workspace's local filesystem, and by which external edits to that filesystem are reflected back into the substrate. The on-disk workspace tree is the **materialized mirror**: a projection of the workspace's current `materialization_head` over the block pool.

### 10.2 Purpose

The user works with files on disk through ordinary editors, terminals, and tools; the agent and the substrate work with blocks, versions, and artifacts. Materialization is the bidirectional bridge: it writes the selected head's file content to disk so the user and external tools see real files, and it captures external edits back as new versions so the substrate stays authoritative. Treating the disk tree as a projection — not an independent store and not a parallel history — is what keeps the version graph the single source of truth and makes the disk mirror a rebuild on loss rather than a data-loss surface (`core.projection`, File 01 §6.11; `version.consequences-for-later-specs`, File 11 §24).

### 10.3 Rule — the mirror is a projection

- The on-disk file tree under a bound workspace root is a projection of the selected `materialization_head` (`version.materialized-view-context-view`, File 11 §7). It holds no durable fact the substrate does not. Its rebuild trigger is declared (`core.projection`, File 01 §6.11): it updates on file-block commit, on version switch, on workspace-head switch, and on workspace open; it rebuilds wholesale from the selected version when the mirror is absent, stale, or corrupt.
- A workspace root has exactly one active mutable `materialization_head` at a time. The head references `{ conversation_id, version_id }` and selects which conversation/version projection owns the root. Multiple conversations may share one workspace identity, but they do not independently materialize into the same mutable root unless a later surface declares separate per-conversation roots over this same contract.
- A file is a `FileAttachment` block (File 08); its content is the source of truth, inline or external (resolved from the content-addressed blob store, `storage.blob-store`, File 20 §6). Materialization writes that content to the resolved path (§11). The version tree is the single file-history mechanism: reverting a file is a version switch (`version.version-switching`, File 11 §8), and there is no separate checkpoint table or shadow-snapshot directory.
- **Block→disk.** When a file block becomes active in the conversation's current version, the materializer writes its content to the resolved path through File 23's atomic-write chokepoint (§13). When a file block is superseded by a sibling (an edit, `block.edit-semantics`, File 08 §6.2), the materializer rewrites the file. When a file block leaves the active view (a version switch drops it), the materializer deletes the file from disk; the block remains in the pool, only the mirror changes.
- **Version or head switch.** When the selected conversation switches to another version, or the workspace switches its `materialization_head`, the materializer walks the version diff (`version.version-diff`, File 11 §4), determines which file blocks belong in the target view, and rewrites, deletes, or restores files on disk to match. Switching the head is an explicit workspace operation with a conflict preview when it would overwrite uncommitted external edits. Open editor projections reflect the switched state. This is the disk realization of `MaterializationRecorded` (File 11 §5).
- The materializer is idempotent (re-running against an already-correct disk state is a no-op), batched (rapid consecutive operations coalesce, §12), and preserves the atomic-write invariant so a partial state is never visible (§13).
- Listing and browsing the workspace read from the materialized view (the projection), not by walking the disk, so they reflect the selected head even mid-flush during a version/head switch.

### 10.4 Rule — materialization policy

- An artifact's `MaterializationPolicy` (`artifact.artifact-materialization`, File 09 §7.2 — `InWorkspace`, `ExternalRef`, `None`) decides whether and how its versions materialize. This file implements the `InWorkspace` resolution and sync loop File 09 delegates; it does not redefine the policy enum.
- `ExternalRef` artifacts are not written to the workspace tree by default; their content lives in external storage and the user may opt to materialize a local cache (`artifact.artifact-materialization`, File 09 §7.2). `None` artifacts have no on-disk presence.

### 10.5 Boundary

This file owns the disk↔substrate mirror loop and that the mirror is a projection. File 11 owns the materialized view and the version diff the mirror projects; File 08 owns the file block and its content; File 09 owns the `MaterializationPolicy` and the per-artifact `materialized_paths` record; File 20 owns the blob store the external content resolves from.

## 11. Materialized-Path Resolution

Anchor: `workspace.materialized-path-resolution`

### 11.1 Definition

Materialized-path resolution is the deterministic algorithm that maps a materializable unit (a file block, an artifact version) to the path it occupies under a workspace root. This is the path-resolution algorithm File 09 §7.2 delegates to this file.

### 11.2 Rule — the two materialization targets

Resolution chooses one of two targets by whether the unit has a natural user-facing location:

- **User-facing files.** A `FileAttachment` block or an artifact whose materialization is a principal user-facing file resolves to its **natural workspace-relative path** — the path the user (or the agent acting as the user) named for it, under the workspace root (`<workspace_root>/<relative_path>`). A coder's `src/main.rs`, a generated `report.md`, an ingested project's existing tree all live at their natural paths, not buried in an Atlas-internal directory. Explicit user/model-requested paths never silently suffix: a collision produces a typed conflict and requires overwrite, new-path, branch/version, or cancel. Auto-generated unnamed files may suffix deterministically from the producing block/artifact identity.
- **Atlas-internal artifact versions.** An artifact version with no natural user-facing location resolves under the workspace-internal `.atlas/artifacts/` directory, computed deterministically from `(workspace_id, artifact_id, artifact_kind, version_id)` — the canonical default `<workspace_root>/.atlas/artifacts/<artifact_id>/<version_id>/<kind-typed-leaf>` (the default File 09 §7.2 states). Multi-file artifacts materialize every constituent path; the principal file is flagged (`content_role: Primary`, `artifact.materialized-paths-provenance`, File 09 §7.4).

### 11.3 Rule — path discipline

- Materialized paths are recorded **workspace-relative** (`relative_path` against the workspace root, or `root_alias:/relative/path` for multi-root); the absolute path is a runtime projection for local display and process invocation, never canonical identity (`artifact.materialized-paths-provenance`, File 09 §7.4). This is what makes relocation (§6) a re-resolution rather than a break: moving the workspace re-resolves every relative path against the new root.
- Model-facing content addresses workspace files by their workspace-relative path or a stable workspace-rooted alias, not by the device's absolute path. The runtime does not expose the host's absolute directory layout to the model by default; absolute paths are device-local sensitive data and require File 18 consumer authorization plus File 22 sensitivity filtering before model, plugin, sync, export, or broad UI exposure.
- Every resolved path is validated and contained before any write: it is canonicalized (resolving `.`, `..`, and symlinks), checked to lie within the workspace root (or an additional mounted root, §14), and rejected with a typed `PathOutsideWorkspace` error otherwise (`sandbox.filesystem-enforcement`, File 23 §7). This file resolves the path; File 23 enforces the boundary.
- Resolution is deterministic and stable: the same unit resolves to the same workspace-relative path across processes and devices, so the materialized-path record replays identically (`context.assembly-replay-snapshot` discipline). The selected collision policy is recorded in materialized-path provenance: `ExplicitPathRequiresDecision`, `GeneratedPathDeterministicSuffix`, `OverwriteAllowedByPolicy`, or `VersionedPathTemplate`.

### 11.4 Boundary

This file owns the resolution algorithm and the workspace-relative discipline. File 09 owns the `materialized_paths` record the resolution populates; File 23 enforces the containment; File 20 owns the data-root and workspace-root layout the relative path is resolved against.

## 12. The Disk→Substrate Sync Loop

Anchor: `workspace.disk-sync-loop`

### 12.1 Definition

The disk→substrate sync loop is the mechanism that detects external edits to materialized files and reflects them back into the substrate as new sibling-block versions, keeping the version tree authoritative when the user or an external tool edits a file directly.

### 12.2 Purpose

The user edits files in their own editor, runs build tools that write outputs, and uses external programs that change the workspace tree without going through a capability call. Those changes must enter the substrate so history, retrieval, and the agent's view stay correct, and so the version tree remains the single source of truth. This loop is the inbound half of the mirror; the materializer (§10) is the outbound half.

### 12.3 Rule

- The system runs a filesystem watcher over each open workspace's tree using the operating system's change-notification interface, event-first (`perception.triggers`, File 19 §8). Polling is not the primary mechanism; a polling interval is a flagged, configurable fallback for sources without change events, never a correctness condition (`core.event-first-by-default`, File 01 §7.15; File 19 §8.2). Git status and dirty-state likewise update from watcher events, not from a timed poll.
- Watcher events are coalesced through an event-batching window (a debounce that batches a burst of events from a single logical change), so rapid consecutive writes commit as one version rather than many. Event-batching is OS-event-driven coalescing, not time-based polling, and is the permitted realization (File 19 §8).
- The materializer writes through explicit write-intent records carrying path, expected content hash, materialization operation id, version id, and target block/artifact id. Watcher events matching an active write intent are suppressed as self-writes after hash verification. Non-matching events become external edits or conflicts. During version/head switches and mirror rebuilds, classification pauses but observation continues; queued events reconcile after the rebuild.
- On each flush, the loop compares the disk state to the materialized view's expected state and, per changed path role, commits the substrate consequence:
  - **Created** — a file on disk with no corresponding tracked active block may commit a new `FileAttachment` block and a version edit only if it passes ignore, size, binary, and sensitivity policy; bulk mounted-tree discovery does not auto-commit (§14).
  - **Modified** — a file whose content hash differs from its active block commits a sibling block (`block.edit-semantics`, File 08 §6.2), swaps the active reference, and records the `ExternalEdit` `ContextOp` (`version.version-diff`, File 11 §5).
  - **Deleted natural workspace file** — a file present in the active view but absent on disk removes the block from the active view (not from the pool) and commits.
  - **Deleted artifact materialization** — a deleted artifact materialization records the materialized path as missing/removed and may update the active materialization record, but does not delete the artifact or artifact version.
  - **Deleted internal projection/cache** — a deleted `.atlas/` projection or cache triggers rebuild or cleanup, not user-content deletion.
  - **Moved/Renamed** — a rename commits a sibling block with the new path and the same content.
- The committing actor is attributed: a user-driven edit is producer `UserMessage`; an edit not directly attributable is producer `Subsystem { subsystem_id: filesystem_watcher, reason: "external_edit" }` (`block.block`, File 08 §2.2; `artifact.disk-entity-sync`, File 09 §7.5). When the changed file is a materialized artifact, the artifact's `current_version_block_id` updates and `ArtifactExternallyEdited` emits through File 09/File 10 (§20).
- The loop respects the workspace ignore file (`.atlasignore`, §9), build-output and cache exclusions, binary/size policy, and File 22 secret scanning, so ephemeral, generated, secret-bearing, and oversized files do not flood the substrate with versions.
- Freshness is verified before an in-place capability edit overwrites a file: a read records `mtime` and `content_hash`, and a subsequent edit carries the expected values; a mismatch is a typed `FileChangedSinceRead` condition that surfaces the external change rather than silently overwriting it (§13).

### 12.4 Boundary

This file owns the sync loop and the watcher. File 08 owns the sibling block it commits; File 11 owns the version commit and the `ExternalEdit` op; File 09 owns the artifact-entity consequence; File 19 owns the perception-side filesystem observation when the change is also a perception signal.

## 13. Atomic Write, Freshness, and the Filesystem Boundary

Anchor: `workspace.atomic-write`

### 13.1 Definition

This section fixes how materialization writes to disk safely (atomicity), detects intervening external changes (freshness), and stays inside the workspace boundary (containment), by consuming the primitives File 23 owns.

### 13.2 Rule

- **Atomic write.** Every materialization write is staged and atomically promoted: content is written to a temporary path in the same filesystem boundary, made durable, then renamed over the destination, so a cancelled or failed write never leaves a partially-written file (`sandbox.filesystem-enforcement`, File 23 §7.3; `run.streaming-partial-execution`, File 04 §12). A streaming materialization writes incrementally to the staged temporary path and atomic-renames at the commit boundary; a cancelled stream deletes the staged file and commits no version (`block.streaming-commit-boundary`, File 08 §7). This file invokes the atomic-write primitive; File 23 owns it.
- **Freshness.** Before an in-place edit, the captured `mtime` and `content_hash` from the prior read are checked against the current file; a mismatch is the typed `FileChangedSinceRead` condition, which routes to the disk→substrate loop (§12) to capture the external change rather than overwrite it. The content-hash check is the authority; `mtime` is the fast pre-check (it is unreliable on some network and virtualized filesystems).
- **Containment.** Every materialized path is canonicalized and confined to the workspace root (or a declared additional mounted root, §14) before any operation, with symlinks resolved before the containment check; a path outside the region is rejected with `PathOutsideWorkspace`, a non-retryable security boundary (`sandbox.filesystem-enforcement`, File 23 §7; `security.local-posture`, File 22 §13). The workspace root is the `WorkspaceOnly` (or `WorkspaceWithExtras` for multi-root) filesystem region File 23 confines a workspace-scoped sandbox to.
- **Secrets.** No unredacted secret is written to a materialized file that syncs, exports, enters the model request, or persists to the ledger. Workspace environment files (`.atlas/.env`, `.atlas/.env.local`) are secret-scanned; `.env.local` is device-local and excluded from sync and ordinary export, while `.env` is portable only when values are non-secret or represented as secret references (`secret.backend-boundary`, File 22; §16).

### 13.3 Boundary

This file owns the materialization-side discipline (when to stage, when to check freshness, when to contain). File 23 owns the atomic-write primitive and the canonical-path-containment chokepoint; File 22 owns the secret boundary; File 08 owns the content hash the freshness check uses.

## 14. Mounted Projects, Ingestion, and Multi-Root Workspaces

Anchor: `workspace.mounted-projects`

### 14.1 Definition

A mounted project is an existing external directory bound as (or into) a workspace. Ingestion is the act of bringing an external codebase into a workspace as managed content. A multi-root workspace is a workspace with a primary root plus additional mounted roots.

### 14.2 Rule — mounting

- A `Mounted` workspace's root is an existing user directory rather than an Atlas-created one (§5.3). Mounting validates and contains the path, creates the workspace-internal `.atlas/` directory if absent only when settings and policy allow it, detects stable version-control binding metadata, and binds the requesting conversation. The user's existing files are not moved or copied. Mounted roots enter first as observed/indexable filesystem roots; File 12 may index them, but first open does not bulk-commit the entire directory into blocks. Blocks are created only for files that are uploaded, edited by Atlas, externally edited after being tracked/materialized, or explicitly captured through a previewed import/capture plan.
- Mounting deduplicates by canonical path: opening a directory already bound to an active workspace resolves to that workspace (§3.4).

### 14.3 Rule — ingestion

- Ingesting an external codebase brings a git repository or a local directory into the workspace context through an explicit mode:
  - `ReferenceOnly` — index/read the external source without copying source files into the workspace.
  - `CloneIntoWorkspace` — create a user-visible working copy under the workspace root.
  - `CloneIntoDataRoot` — create a managed backing copy outside the user workspace and expose selected materializations.
  - `CopyIntoWorkspace` — copy selected files into the workspace as owned source material.
  - `ImportAsBlocks` — commit selected files into substrate blocks/artifacts without preserving a working repository.
- Each ingestion mode declares ownership, cleanup, sync/export eligibility, authority, default indexing, and materialization behavior. The data-root ingest area canonical default is `<data-root>/ingest/<source-id>/<workspace_id>/`, placed by File 20 §8 and named here.
- Ingested content is indexed under the workspace-qualified retrieval namespace (`ingested_codebase:<workspace_id>`, `retrieval.namespaces`, File 12 §8) so it is retrievable and citeable; this file owns the workspace/repository identity, File 12 owns the indexing.
- Ingested external code carries no authority: instructions embedded in ingested files are content, not commands, and never confer capability or policy authority on the agent (`security.untrusted-content`, File 22 §12). Ingestion records a provenance producer stamp so the imported origin is traceable (`block.block`, File 08 §2.2 `Import`).

### 14.4 Rule — multi-root

- A workspace has one primary root and may have additional `WorkspaceRootRecord`s, each with `root_id`, `alias`, `root_kind`, device-local `binding_state`, policy/ignore settings, access mode, and optional sync/export eligibility. Root ordering is a UI/display preference, not identity. Multi-root is opt-in (a setting, §21); the single-root case is the default.
- Materialized-path resolution (§11) and the disk→substrate loop (§12) operate over the declared root set; containment (§13) admits any declared root and rejects everything else. When more than one root exists, model-facing and capability-facing paths name the root explicitly as `root_alias:/relative/path`, and file-touching capabilities resolve both `workspace_id` and `root_id`.

### 14.5 Boundary

This file owns mounting, ingestion identity, and the multi-root root set. File 12 owns indexing ingested content; File 23 enforces the multi-root containment and access modes; File 22 owns the untrusted-content rule ingested code is subject to; File 20 places the ingest area.

## 15. Worktrees — Identity and Lifecycle

Anchor: `workspace.worktree`

### 15.1 Definition

A `Worktree` is a filesystem-or-resource-level working copy of a workspace's repository that shares the underlying object store, used to isolate parallel or independent child-run work (the canonical example is a git worktree). This file owns the worktree directory identity and lifecycle; File 04 §16 owns the isolation-primitive selection and the shared-workspace exception, and File 23 confines the worktree directory.

### 15.2 Purpose

Multiple agents working in parallel on the same repository — or an isolated branch of work the user wants to keep separate — need independent working copies that do not collide on the same files, while sharing the repository's object store so the cost is one working tree per copy, not one full repository per copy. Worktrees are the directory realization of the code-touching isolation primitive File 04 §16 names; this file gives those directories device-local identity and a lifecycle so they are observable, mergeable, quarantineable, and explicitly cleanable.

### 15.3 Rule — the worktree record and placement

- A worktree has a device-local durable `WorktreeRecord` (a substrate family, §22): `worktree_id` (stable identifier), `parent_workspace_id`, the associated `run_id`/child-run and `agent_id` where applicable, `root_path`, `base_commit_ref`, `branch_name`, `status` (a closed canonical enum: `Active`, `Merged`, `Discarded`, `Orphaned`, `Quarantined`, `Adopted`, `KeptDetached`), `created_at`, `closed_at`. The path fields are device-local (§4); the record does not sync. Process and sandbox handles inside the worktree are transient and reaped at restart, but the directory payload is preserved unless explicit cleanup policy permits deletion.
- Worktree directories are placed under the data root, not inside the user's workspace tree: the canonical default is `<data-root>/worktrees/<workspace_id>/<worktree_id>/`, placed by File 20 §8 and named here. This keeps the user's workspace directory pristine and the worktree from being committed into the user's repository. (Alternative placements — as a sibling of the workspace root, or inside the workspace-internal `.atlas/` — are rejected, §23.) A worktree shares the parent workspace's repository object store; its working-tree cost is one working copy, not a full repository clone.
- A permanent worktree the user wants to keep is created outside the managed `<data-root>/worktrees/` hierarchy and is exempt from automatic cleanup (§15.5).

### 15.4 Rule — lifecycle

- **Create.** `worktree.create` adds a working copy at the resolved path on a named branch from a base ref (`git worktree add` for git repositories), writes the `WorktreeRecord`, and emits `WorktreeCreated`. It is a `WorkspaceWrite`-tier capability.
- **Operate.** The child run works in its worktree, committing to its branch; its mutations land in its own working copy and do not touch the parent workspace's disk tree (`run.isolation`, File 04 §16.2).
- **Compare.** Parallel worktrees are presented for side-by-side comparison of their results (a surface concern; this file provides the records the comparison reads).
- **Merge or discard.** The user (or the parent run's merge step, `run.merge`, File 04 §16.4) selects which worktree's result to incorporate; merging applies the chosen branch back to the workspace (status `Merged`), and the others are discarded (status `Discarded`). Removal is `worktree.remove`, a `UserApproval`-tier capability because it is destructive of an isolated working copy.
- **Cleanup.** Worktrees with no live associated run (orphaned by a crash) are detected at startup. Runtime handles are reaped; directories with possible unmerged content become `Orphaned` or `Quarantined`, are excluded from active execution, and require explicit user or policy-governed cleanup. Available outcomes are `Adopt`, `Merge`, `Discard`, `KeepDetached`, or `DeleteIfEmptyOrRebuildable`. Quarantined worktrees appear as a distinct category in workspace storage accounting and workspace management UI. When their count or aggregate storage exceeds a user-configured threshold, the system proposes cleanup through the standard preview/capability/policy path. The trigger is state-driven, never time-based. The proposal distinguishes unmerged worktrees, which require explicit merge/discard/adopt, from empty or fully merged orphans, which may be automatically cleaned only under a preconfigured cleanup policy/profile with notification and audit recording.
- **Shared-workspace exception.** When child runs share the workspace non-destructively — a single codebase the user is also editing, parallel non-interfering observations — no worktree is created and the runs operate in the workspace directly (`run.isolation`, File 04 §16.2). Worktree creation is contextual, not always preferable; the isolation decision is File 04's per-child-run policy, and this file owns only the directory identity when a worktree is chosen.

### 15.5 Rule — permission and confinement

- `worktree.list` is `ReadOnly`, `worktree.create` is `WorkspaceWrite`, `worktree.remove` and `worktree.merge` are `UserApproval` (`policy.effective-tier-resolution`, File 06).
- A worktree directory is one filesystem boundary File 23 confines (`sandbox.consequences-for-later-specs`, File 23 §21); a child run operating in a worktree is contained to that worktree's root, never reaching outside it through the boundary.

### 15.6 Boundary

This file owns worktree directory identity, placement, and lifecycle. File 04 owns the isolation-primitive selection, the merge target, and the shared-workspace exception; File 23 confines the worktree directory and owns the per-instance home isolation a subprocess wrapper in a worktree uses; the git object-store mechanics are an implementation detail behind the worktree contract.

## 16. Workspace Export, Import, and Portability

Anchor: `workspace.export-import`

### 16.1 Definition

Workspace portability is the lossless movement of a workspace — its identity, its bound conversations' durable history, its artifacts, its materialized content, and its workspace-internal configuration — across installations and devices, plus the lossy convenience export to a plain archive.

### 16.2 Rule — lossless portability

- Lossless workspace export and import use File 21's `PortablePackage`, content-addressed blob transport, and the import pipeline (`portability.consequences`, File 21 §18). A workspace export bundles: the workspace's syncable identity (`workspace_id`, `name`, `profile_id`, `lifecycle_status`, bound-conversation set — not the device-local root binding), the bound conversations' version trees and block pool, the artifacts and their `materialized_paths` metadata, the workspace-internal `.atlas/` portable configuration (`settings.json`, `commands/`, the instruction files), and the content-addressed blobs the records reference, under the bundle's `CanonicalEncoding` with an integrity hash (`portability.export-bundle`, File 21).
- On import, `root_path` is never imported as authoritative. The workspace imports as `Unbound` or asks the user for a local binding (§4). UUID identity is preserved by default (`workspace_id` and `artifact_id`s carry across), but the import participates in File 21's collision classes: same id and same canonical content is no-op/dedup; same id where local state descends from the import is `SupersededLocally` and skipped by default; hard collisions require fork/new identity or explicit provenance-gap acknowledgement. Any identity remap is recorded in `CrossInstallationMap`.
- Content deduplicates by content hash, and the disk mirror plus all indexes rebuild on receive as projections — they are never transported (`portability.what-replicates`, File 21 §11; `core.projection`, File 01 §6.11). Import is non-destructive and produces an `ImportPlan` preview (`portability.import-pipeline`, File 21).
- Device-local and secret content does not move: root bindings, `relocation_history`, worktree records, `.atlas/.env.local`, raw `.env` secret values, and the materialized disk projection are excluded; the secret boundary applies to every exported file (`secret.backend-boundary`, File 22; `portability.sensitivity-egress`, File 21 §12).

### 16.3 Rule — lossy convenience export

- A workspace may also be exported as a plain archive (a zip of the on-disk tree) for sharing outside Atlas. This is a lossy egress capability: it carries the materialized files but not the substrate history, and it passes through egress governance, audit recording, and sensitivity filtering (`portability.consequences`, File 21 §18; `security.egress-governance`, File 22 §11). It excludes secret-bearing and build-output paths by default. It is a convenience capability, never the portability mechanism of record.

### 16.4 Boundary

This file declares what a workspace export contains and that it rides File 21. File 21 owns the package format, the blob transport, the import-pipeline stages, and the movement-side application of egress governance; File 22 owns the secret boundary and the egress security policy; File 09 owns the artifact identity preserved across export.

## 17. Storage Accounting and Reclamation

Anchor: `workspace.storage-accounting`

### 17.1 Definition

Storage accounting is the per-workspace measurement of consumed storage; reclamation is the user-controlled recovery of that storage at workspace granularity.

### 17.2 Rule

- The system reports per-workspace storage as structured data the backend serves and the frontend renders: total size, file count, and a breakdown by category (source files, materialized artifacts, logs, build outputs and caches, worktrees), computed on demand from the disk tree and the substrate, never stored as an authoritative scalar (`core.non-destructive-by-default`, File 01 §7.13; `storage.retention-gc-accounting`, File 20 §11).
- Reclamation operates at every granularity the user controls — whole-workspace tombstone/payload deletion (§5.7), archival (§5.6), and selective cleanup — with a dry-run preview before any deletion. Selective cleanup targets only rebuildable or disposable content: build artifacts, dependency directories, git-ignored caches, and empty or fully merged quarantined worktrees when a preconfigured cleanup policy allows it. The substrate history (blocks, versions, artifacts) is never deleted by a cleanup operation because it is the source of truth and lives in the substrate, not on the disk mirror (`core.projection`, File 01 §6.11).
- Reclamation is never time-based or automatic without prior policy: no workspace, materialized file, or worktree is pruned by elapsed time. Low-disk pressure or state thresholds may trigger detection, accounting, warnings, and cleanup proposals. Actual deletion runs only through a capability with preview, policy, and the configured maintenance profile; source content, unmerged worktrees, secrets, and non-rebuildable blobs require explicit approval (`core.non-destructive-by-default`, File 01 §7.13; `storage.retention-gc-accounting`, File 20 §11).

### 17.3 Boundary

This file owns workspace-granularity accounting and reclamation. File 20 owns the underlying storage-accounting and blob-GC mechanisms this realizes; File 11 owns the version-tree retention the substrate history is governed by.

## 18. World-Model and Perception Integration

Anchor: `workspace.world-integration`

### 18.1 Definition

This section fixes how active workspaces and worktrees appear in the live world model and how their state is observed.

### 18.2 Rule

- Each active or open workspace is exposed as a `Workspace` world entity (`world.world-entity`, File 18 §4.3), carrying workspace identity, binding availability, profile binding, and observed dirty/branch facts. Absolute root paths are device-local sensitive data: policy-authorized UI and capability views may see them, while context-assembly and plugin views receive aliases and relative paths unless File 18 consumer authorization and File 22 sensitivity filtering allow more detail. The world model references the workspace by `workspace_id` and this file owns the identity it references. Open files, directories, and editor documents within the workspace are the `File`, `Directory`, and `EditorDocument` entities File 18 catalogues, related to the workspace by `contained_in`.
- The active workspace root is a world environment fact (`world.environment-temporal-connection-facts`, File 18 §6.1): the current working directory and active workspace root ground the agent and capabilities.
- Workspace open, close, and relocation, and worktree create and remove, are `Durable`-tier world-state-change facts (`world.durability-tiers`, File 18 §7.3); they survive restart and a `world_snapshot_id` resolves over them. Live dirty/branch state and ephemeral file-open state are `Ephemeral` or `Observed`-tier facts the world model recomputes.
- A `VirtualDesktop` (`world.world-entity`, File 18 §4.3) is a logical presentation grouping that may organize workspaces and windows; it is a presentation grouping owned by File 18 and the per-surface specs, distinct from the `Workspace` substrate primitive this file owns. This file references `VirtualDesktop` but does not own it.
- Perception captures workspace and repository state through the filesystem sensor as `WorkspaceSnapshot` and `FileSnapshot` observations (`perception.sensor`, File 19 §4); this file owns the workspace and repository identity those observations reference, and the observations feed the world model and the disk→substrate loop without re-deriving workspace identity.

### 18.3 Boundary

This file owns the workspace and worktree identities the world model and perception reference. File 18 owns the entity catalogue, durability tiers, and `world_snapshot_id` resolution; File 19 owns the capture mechanics; the per-surface specs own the editor/terminal/browser projections.

## 19. The Workspace Capability Surface

Anchor: `workspace.capability-surface`

### 19.1 Definition

The workspace capability surface is the set of canonical capabilities through which the user and the agent create, manage, materialize, and reclaim workspaces and worktrees, declared once and invoked through every control rail (`core.extension-planes`, File 01 §6.14).

### 19.2 Rule

- Workspace lifecycle and management capabilities, with their default permission tiers (`policy.effective-tier-resolution`, File 06; `capability.touched-resources`, File 05 §6):
  - `workspace.create`, `workspace.open` (mount an existing directory) — `WorkspaceWrite`, escalating to `UserApproval` or typed confirmation when opening a non-empty, unrelated, cross-trust/sensitivity, or mutation-risking target
  - `workspace.close`, `workspace.list`, `workspace.get` — `ReadOnly` or non-mutating
  - `workspace.archive`, `workspace.restore`, `workspace.rebind`, `workspace.mark_archived` — `WorkspaceWrite` for archive/restore/rebind; rebind requires preview and escalates when the new target is non-empty, outside the previous root, would overwrite files, or crosses a trust/sensitivity boundary
  - `workspace.delete` — `permission_floor: Denied` with typed-confirmation override (destructive)
  - `workspace.cleanup` — `WorkspaceWrite` for rebuildable content; `dry_run` previews; deleting source content escalates to `UserApproval`
  - `workspace.ingest_external_codebase`, `workspace.mount` (add an additional root), `workspace.capture_snapshot` — `WorkspaceWrite`; cross-origin ingestion, bulk capture, and non-empty-root mounting may escalate to `UserApproval`
  - `workspace.export`, `workspace.import` — export is egress-governed (`UserApproval` or higher when sensitivity warrants, `security.egress-governance`, File 22 §11); import is non-destructive with an `ImportPlan` preview
  - `workspace.materialize` — materialize an artifact version to disk (`WorkspaceWrite`)
- Worktree capabilities: `worktree.list` (`ReadOnly`), `worktree.create` (`WorkspaceWrite`), `worktree.remove` and `worktree.merge` (`UserApproval`).
- A capability whose resolved touched resource lies outside the active workspace (a cross-workspace path, an absolute path outside the root) escalates its effective tier and surfaces which workspace is targeted (§7.2, `capability.touched-resources`, File 05 §6); the `WorkspaceWrite` tier means "mutations confined to the active workspace," and escaping that boundary re-resolves the tier upward (`policy.effective-tier-resolution`, File 06).
- Every capability is the single source for all invocation paths — command palette, shortcut, agent tool, automation trigger, external protocol (`core.extension-planes`, File 01 §6.14); this file declares no out-of-band workspace operation.
- Custom workspace and worktree operations register through the proposal-first capability mechanism (`capability.runtime-mutation`, File 05 §16) and never bypass the policy layer.

### 19.3 Boundary

This file owns the workspace and worktree capability identities and their default tiers. File 05 owns the capability contract and registration; File 06 owns the tier resolution and approval; File 04 owns the execution of capability calls within a run.

## 20. Events

Anchor: `workspace.events`

### 20.1 Rule

- File 10 carries the canonical events this file emits where they already exist: `WorkspaceOpened`, `WorkspaceClosed`, `FileMaterialized`, and `FileExternallyModified` or the equivalent external-file modification event. Artifact materialization events (`ArtifactMaterialized`, `ArtifactExternallyEdited`) are owned by File 09 and flow through File 10; this file triggers or consumes them when workspace materialization touches artifact versions.
- Additional workspace events are registered as `Custom { namespace: "workspace", name, payload }` extensions through the canonical mechanism (`ledger.event-stream`, File 10 §4.3): `WorkspaceCreated`, `WorkspaceArchived`, `WorkspaceRestored`, `WorkspaceTombstoned`, `WorkspacePayloadDeleted`, `WorkspaceRelocated` (rebind), `WorkspaceMissing` (with the typed `reason`), `WorkspaceMirrorRebuilt`, `WorkspaceMaterializationHeadChanged`, `WorktreeCreated`, `WorktreeQuarantined`, `WorktreeRemoved`, `WorktreeMerged`, and `ExternalCodebaseIngested`. Each registered kind declares payload schema, cross-reference keys, default sensitivity, retention, and owner/source subsystem per File 10. This file reserves the `workspace` namespace and declares these kinds.
- Every event carries the canonical envelope (`conversation_id` where applicable, `context_refs` including `workspace_id`, `root_id`, and `worktree_id`, `sequence_scope`, `sequence`, `timestamp`, `sensitivity`) and keeps raw secret payloads out of durable persistence (`ledger.event-envelope`, File 10 §5.2). Workspace creation, tombstoning, payload deletion, relocation, and worktree removal also record audit entries through the device-local hash-chained overlay (`security.audit-crypto`, File 22).
- Events are live coordination, not the source of truth: a consequential workspace fact is committed to the durable record by the executor, never inferred from event observation (`core.durable-history-transient-coordination`, File 01 §7.3).

### 20.2 Boundary

This file declares which events it emits and reserves the `workspace` namespace. File 10 owns the event catalogue, envelope, delivery classes, and the `Custom` registration mechanism; File 22 owns the audit overlay the destructive operations record to.

## 21. Settings

Anchor: `workspace.settings`

### 21.1 Rule

- Workspace behavior is governed by typed settings resolved through File 15's canonical settings source stack (`settings.scopes-profile-contexts-overlays`, File 15 §5.2), with the workspace-scoped layer materialized at `<workspace_root>/.atlas/settings.json` (§8) as one cascade layer, never a parallel store. No workspace behavior is a hardcoded constant where meaningful variation exists (`core.typed-configuration-failure`, File 01 §7.6; settings-over-constants).
- The canonical workspace settings include at least: the default workspace root location, whether a new conversation creates a fresh workspace or reuses one, the single-conversation-versus-project default, the git-init-on-create default, the open-without-`.atlas` behavior, the workspace instruction-file name and lookup order (`retrieval.workspace-instruction-files-atlas-md`, File 12 §15), the ignore-file name (`.atlasignore`) and default ignore set, the materializer debounce/coalescing window, the worktree base directory and branch-naming pattern, quarantine cleanup thresholds by count/storage, preauthorized empty-or-merged-orphan cleanup behavior, the multi-root toggle, the workspace-scoped permission and tool-surface overrides, and the cleanup default-exclusion set.
- Each setting declares its locality (`settings.locality-sync-export`, File 15 §18): the workspace instruction-file name and the project/single defaults are syncable user preferences; the workspace root location, root bindings, and worktree directory are device-local; secret-bearing workspace settings and env-file values are secret-reference-only. Edits to `.atlas/settings.json` are validated through File 15; invalid edits produce typed settings errors rather than silently changing runtime behavior.
- Each setting declares its agent-exposure (`core.settings-system`, File 01 §6.8): whether it is hidden from, available on request to, or included in the model request, so the agent cannot read or change security-sensitive workspace configuration without policy.

### 21.2 Boundary

This file declares the workspace settings dimensions and their layer. File 15 owns the settings object model, the cascade, locality, agent-exposure, and migration; File 06 owns the policy the permission-override settings feed.

## 22. Persistence Contract

Anchor: `workspace.persistence-contract`

### 22.1 Rule

- The durable workspace families are source-of-truth substrate records persisted through File 20's contract (`storage.durable-substrate`, File 20 §3): the `WorkspaceRecord`'s syncable identity (syncable substrate) and device-local binding (device-local substrate, §4), and the materialized-path provenance records (`artifact.materialized-paths-provenance`, File 09 §7.4). Each declares its substrate family, its source-of-truth-versus-projection classification, its locality, and its schema version, and obeys the no-unkeyed-scalar and immutable-source-of-truth rules File 20 fixes.
- The materialized disk mirror is a **projection**, not a source-of-truth family: it is rebuildable from the selected `materialization_head`'s materialized view plus the block pool and blob store, declares its rebuild triggers (file-block commit, version switch, head switch, workspace open, corruption), and its loss is a rebuild (`storage.projection-store`, File 20 §7; `core.projection`, File 01 §6.11). The session-export views (`.atlas/logs/`) and the storage-accounting figures are likewise projections.
- `WorktreeRecord`s are device-local records. Runtime handles inside worktrees are reaped at restart (File 23 §14); orphaned worktree directories are detected and quarantined or explicitly cleaned according to §15.4, not silently deleted.
- Startup reconstruction resolves each active workspace's `binding_state`, surfaces unresolved bindings as `Unbound`, `NeedsRebind`, or `Missing` for recovery (§6), reaps orphaned process/sandbox handles, quarantines orphaned worktree directories when needed, and rebuilds the disk mirror lazily on workspace open — never re-deriving any durable fact from live mutable disk state, only from the recorded substrate (`storage.lifecycle-reconstruction`, File 20 §13).
- Every hash this file relies on — the file `content_hash` used for freshness (§13), the blob address for external content (§10), the export bundle integrity hash (§16) — is computed over a declared `CanonicalEncoding`, never over physical disk or storage bytes (`core.canonical-hash`, File 01 §7.14); this file defines no new canonical hash and inherits each from its owning file (File 08 `content_hash`, File 20 blob address, File 21 bundle hash).

### 22.2 Boundary

This file declares which workspace state is durable source-of-truth and which is a rebuildable projection. File 20 owns the storage engine, the partition, and the rebuild orchestration; File 21 owns the replication of the syncable families; File 11 owns the version tree the disk mirror projects.

## 23. Explicit Rejections

Anchor: `workspace.explicit-rejections`

The following are architecturally invalid for any later or per-surface spec:

- **Workspace-first as the universal root model** — making a visible workspace a mandatory doorway for all work, or treating the workspace as the durable root that conversation, task, and artifact hang from. The workspace is a system capability and a durable scoped context; conversation-only and research/learning flows need no visible workspace (`core.workspace-model`, File 01 §3; `codex_recommendations.md` §1.2).
- **A workspace as a path with no durable identity** — keying durable state to a raw local path with no stable `workspace_id`, so a moved or renamed directory orphans the bound history. The `WorkspaceRecord` and the identity/path split are required (§3, §4).
- **A separate file-history store** — a `file_checkpoints` table, a `.atlas/checkpoints/` shadow directory, per-file `.snap` snapshots, or any parallel history primitive for workspace files. The version tree is the single file-history mechanism; the disk tree is its projection (§10; `version.consequences-for-later-specs`, File 11 §24).
- **The disk tree as a source of truth** — treating on-disk files as authoritative over the block pool and version tree, or as a store the substrate copies from rather than projects to. The mirror is a projection and its loss is a rebuild, never data loss (§10; `core.projection`, File 01 §6.11).
- **A second blob store or a private materialization store** — resolving external file content from anywhere other than File 20's content-addressed blob store, or introducing a per-workspace external store (`storage.consequences`, File 20 §18).
- **Replicating the device-local root binding** — syncing or exporting a workspace's absolute path as if it were portable identity. The path rebinds per device; only the logical identity travels (§4).
- **Worktrees inside the user's workspace tree as the default** — placing managed worktrees inside the user's repository (where they would be committed or clutter the project) or as arbitrary siblings of the workspace root as the default. Managed worktrees live under the data root (§15.3).
- **Time-based or polling workspace behavior** — polling the filesystem as the primary change-detection mechanism, polling for git status, or pruning workspaces, materialized files, or worktrees by elapsed time. Capture is event-first with flagged polling fallback; reclamation is explicit and user-governed (§12, §17; `core.event-first-by-default`, File 01 §7.15).
- **A non-killable or unmanaged worktree process** — a worktree execution unit whose runs, sandboxes, or processes cannot be killed or whose runtime handles survive restart as trusted state. Runtime handles are killable and reaped; directory payloads with possible user/agent work are quarantined and explicitly resolved, not silently deleted (§15.4; File 01 §7.11).
- **Time-based quarantine cleanup** — deleting or proposing deletion of quarantined worktrees because elapsed time passed. Quarantine cleanup is driven by explicit user action, configured state thresholds, or preauthorized cleanup policy.
- **Materializing a secret unredacted** — writing a raw secret into a materialized file that syncs or exports, or exposing the host's absolute directory layout to the model by default (§11, §13; `secret.backend-boundary`, File 22).
- **A private workspace or materialization model in a surface** — any surface, plugin, or integration introducing a parallel workspace identity, a private disk-history store, or a materialization path that bypasses this file's mirror and File 23's filesystem boundary (`block.consequences-for-later-specs`, File 08; `version.consequences-for-later-specs`, File 11 §24).

## 24. Consequences for Later Specs

Anchor: `workspace.consequences-for-later-specs`

Later specs must follow these rules:

- The **per-surface specs** (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) consume this file's `Workspace`, materialization mirror, and worktree primitives and project them into surface-specific views (editor file trees, browser download directories, dataset working files, lesson materials). They declare their surface-specific workspace capabilities through the canonical mechanism, never introduce a private workspace identity or a parallel disk-history store, and materialize only through this file's mirror and File 23's filesystem boundary. The Coder surface's worktree comparison board, IDE file tree, and checkpoint UI are projections over this file's worktree records and the version tree, not new primitives.
- The **Work Surface Contract** spec defines how surfaces declare their state, actions, views, and context policies against the shared workspace; the workspace is the durable scoped context a surface's views render over.
- The **Automation and Triggers** spec drives workspace and file-change triggers from explicit filesystem-watcher events and world-state changes, not from a timed poll over the workspace, and confines non-interactive workspace work to the narrowest sandbox over this file's roots.
- The **Workflows, Templates, and Reuse** spec treats a workspace template (the seed structure a `copyTemplate` or named template instantiates, §5.2) as a reusable artifact, and workflow outputs that warrant durable identity materialize through this file's mirror.
- The **Extension and Plugin** and **MCP** specs may contribute workspace templates, instruction-file conventions, and ingestion sources through the proposal-first mechanism; plugin-registered workspace and worktree operations participate in the canonical capability and policy layer the same way built-ins do.
- The **UI** specs render the workspace picker, browser, recent-workspaces list, file tree, materialization status, relocation-recovery dialogs, worktree comparison, storage-accounting views, and export/import surfaces from the canonical data contracts here; presentation may vary freely, the substrate cannot.
- The **Quality Control and Validation** spec validates materialization integrity (the disk mirror matches the selected head after a switch, an external edit commits a sibling version, a relocated workspace re-resolves its relative paths) and the filesystem-boundary containment, integrating through event and capability hooks rather than a separate pipeline.
- The **Telemetry, Logging, and Observability** spec consumes the workspace and materialization events as data and renders the workspace inspector from observation handles, never re-walking the disk for a historical view.
- The **Runtime Infrastructure and Lifecycle** spec orchestrates the workspace startup reconstruction (binding resolution, missing/unbound-workspace surfacing, orphan-worktree quarantine, lazy mirror rebuild) around the storage lifecycle File 20 owns, and invokes this file's reconstruction rather than reimplementing it.
- The **Evaluation and Benchmarking** spec verifies the materialization round-trip (block→disk→external-edit→sibling-version→disk reproduces the edit), the relocation re-resolution, the worktree create/merge/discard/quarantine lifecycle, and the export/import workspace round-trip, replaying over recorded snapshots and immutable references, not live disk state.
- The **Packaging, Platform, and Distribution** spec ships the built-in declarations for every canonical workspace and worktree capability, the workspace and worktree event kinds, and the default workspace settings as the `Builtin` source in every install.

Specific integration contracts will be stated in those files when they are written.
