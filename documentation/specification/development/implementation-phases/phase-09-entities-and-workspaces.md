# Phase 9 — Entity Layer & Workspaces

## 1. Goal & why now

Durable products and places: the File 09 entity layer (Artifacts, Claims, Evidence, Citations,
Observations, Validation/Critique shapes, derived Provenance) over the block pool, and the File 24
Workspace with the disk↔substrate materialization mirror through the P8 chokepoint. Surfaces need
artifacts to produce and workspaces to work in; the completion forgery guard starts reading the
entity layer ("a run whose contract required artifact creation cannot complete without an
`ArtifactVersion`"); observations + staleness fingerprints make read-before-act revalidation real.

## 2. Canonical scope & deferrals

- **File 09 — complete core**: the `Artifact` entity + required fields over Artifact-kind blocks
  (§3); the closed `ArtifactKind` catalogue (§4); ArtifactLifecycle/ReviewState/ValidationState —
  **derived per-ContextVersion, never entity-stored** (§5); `ArtifactVersion` (§6);
  `MaterializationPolicy` (§7 — `InWorkspace` resolution delegated to 24, closed in this phase);
  tombstones + hard-delete floors (§8); the `Claim` block-kind extension + deterministic
  `ClaimStatus` derivation + confidence classes — policy-grade enums, scores for ranking only (§9);
  claim extraction — explicit `claim.publish`; auto-extraction default off (§10); `EvidenceLink` +
  relations + bounded evidence-set closure (§11); `Citation` + the `SourceSpan` grammar (§12);
  `Observation` + the **`StalenessFingerprint` contract** — completing 04 §8.2 revalidation and
  23 §14 snapshot commits (§13); `Validation`/`Critique` shapes + ValidationState derivation
  (§14 — orchestration machinery → **P13**); the derived `Provenance` query surface — deterministic,
  byte-identical over the same snapshots (§15); the entity capability set as Builtin (§16); entity
  events (§20).
- **File 24 — complete core**: the `WorkspaceRecord` — stable `workspace_id` independent of any
  path, the value every workspace FK across the canon resolves to (§3); the **identity/path locality
  split** — syncable logical identity vs device-local binding (§4); lifecycle —
  create/open/quick-start/close/archive/restore; delete is the only destructive op, `Denied`-floor +
  typed-confirmation, tombstoned never erased (§5); relocation/recovery — explicit rebind, never
  auto-rebind, never a fabricated empty dir; durable-history reads never fail on `Missing` (§6);
  conversation–workspace binding + `workspace` scope resolution + cross-workspace escalation (§7);
  the workspace-internal `.atlas/` layout — **no checkpoints/shadow-history dir** (§8);
  instruction-file identity (`ATLAS.md` family + `.atlasignore`) (§9 — indexing → **P10**);
  **materialization** — the disk tree as a projection of `materialization_head`, block→disk through
  the P8 atomic chokepoint, head/version-switch rewrite, idempotent + batched (§10);
  materialized-path resolution — workspace-relative, deterministic, replay-stable; absolute paths
  device-local sensitive (§11); the **disk→substrate sync loop** — event-first watcher, write-intent
  self-write suppression, external edits → sibling-block versions + `ExternalEdit` op (§12);
  atomic-write/freshness/containment via 23 — `FileChangedSinceRead`, `PathOutsideWorkspace`
  non-retryable (§13); mounted projects + ingestion modes, `ReferenceOnly` first — mounting never
  bulk-commits, ingested code carries no authority (§14); **worktrees** — device-local
  `WorktreeRecord`, placed under the data root never in the user's tree, create/operate/compare/
  merge/discard/quarantine, state-driven cleanup never time-based (§15); storage accounting (§17).
  Export/import (§16) → **P20**.
- **File 04 — §16 completion**: child-run isolation-primitive selection (worktrees now exist);
  pending-operations buffer merging as one net change.

## 3. Prerequisites

P8 — chokepoint, atomic writes, watcher confinement, ManagedProcess (worktree handles). P3 —
blocks/versions for sibling commits. P5/P6 — entity ops are capabilities through the pipeline;
hard-delete floors need policy.

## 4. Lanes

(a) Entity records + derivations + provenance queries; (b) workspace record + lifecycle +
relocation; (c) materialization mirror + path resolution + sync loop; (d) worktree lifecycle.
(a) and (b) are independent; (c) joins after (b) and consumes (a)'s `MaterializationPolicy`;
(d) joins after (c).

## 5. Build plan

1. **Entity records**: Artifact/ArtifactVersion over Artifact-kind blocks; `artifact.create`/
   `commit_version` capabilities; derived-state evaluators over the version-graph action log (the
   P3/P6 trivial derivations become real).
2. **Claims/Evidence/Citations**: `claim.publish`; EvidenceLink edge metadata; deterministic status
   derivation; the SourceSpan grammar; evidence-set closure with depth/cardinality bounds.
3. **Observations**: the observation-commit path; fingerprints computed at capture;
   `StateChangedSinceObservation` revalidation wired into the call pipeline (04 §8.2.2); 23's
   Process/Sandbox snapshots commit through it.
4. **Provenance**: closure rules + the deterministic ReadOnly query capabilities
   (`provenance.query_lineage`/`query_evidence_set`/`query_derivation_chain`/…).
5. **Workspace**: WorkspaceRecord (every prior `workspace_id` FK now resolves); binding; `.atlas/`
   creation; quick-start Temporary kind; relocation recovery affordances.
6. **Materialization mirror**: path resolution (natural workspace-relative vs
   `.atlas/artifacts/<id>/<version>/`); block→disk staged-atomic; head/version-switch rewrite;
   wholesale rebuild on absent/stale/corrupt mirror.
7. **Sync loop**: event-first watcher (flagged polling fallback only); self-write suppression by
   write-intent + hash; external edits → sibling `FileAttachment`/Artifact versions +
   `ArtifactExternallyEdited`.
8. **Worktrees**: WorktreeRecord under the data root; orphan quarantine at startup; merge/discard
   tiers (04 §16's isolation selection now realized).
9. **Forgery-guard extension**: the `artifact commit` completion requirement enforceable end-to-end.

## 6. Test obligations & acceptance evidence

- 09: derived-state never entity-stored (§5.4); `ClaimStatus` derivation conformance —
  withdrawal → supersession → aggregation, equal-confidence → Unresolved (§9.4);
  confidence-class-not-score policy reads (§9.5); evidence-set closure + **compaction preserves
  closure for Supported/Validated** (§11.5, wired into P7 compaction); ValidationState derivation +
  critique-never-gates (§14); **provenance determinism** — byte-identical over the same snapshots
  (§15.4); staleness revalidation — observations without fingerprints cannot back mutations (§13.3);
  hard-delete floors — `Denied` + typed-confirmation, never weakened for discarded/only-version
  artifacts (§8.1); completion-evidence integration (§2.2); disk→entity sync sibling commits (§7.5);
  import-producer provenance shape readiness (§15.5).
- 24 — the named suites: **disk-mirror-is-a-projection** — holds no durable fact the substrate does
  not; loss/corruption is a wholesale rebuild, never data loss; no parallel file-history store (no
  `file_checkpoints`, no `.atlas/checkpoints/`) — grep + rebuild test into the P2 harness;
  **materialization round-trip** — block→disk→external-edit→sibling-version→disk reproduces the
  edit; head-switch rewrites/deletes/restores to match the target view; **identity/path split** —
  `workspace_id` immutable, never path-derived; relocation re-resolves every workspace-relative
  path; `Missing`-binding reads never fail; **atomic-write/freshness/containment** — staged +
  atomic-rename, cancelled stream deletes the staged file and commits no version; content-hash is
  the freshness authority (mtime pre-check only) → `FileChangedSinceRead` routes to the sync loop,
  never overwrites; canonicalized + confined → `PathOutsideWorkspace`; **event-first watcher** —
  polling a flagged fallback, git status from events; **self-write suppression**;
  **mount-no-bulk-commit** + ingested-code-carries-no-authority; **worktree lifecycle** — data-root
  placement, orphans quarantined never silently deleted or time-pruned, unmerged distinguished from
  empty; **no-secret-materialized** — nothing unredacted in files that sync/export/enter the model;
  `.env.local` device-local; **delete discipline** — tombstones, Mounted source files never deleted
  without separate confirmation.
- 3-OS coverage explicitly includes case-insensitive filesystems and path-separator handling.
- **Closed-set pinning**: ArtifactKind, lifecycle/review/validation state sets,
  ClaimKind/Status/ConfidenceClass, EvidenceRelation, CitationReferenceKind, SourceSpan variants,
  ObservationKind, **StalenessFingerprint variants**, MaterializationPolicy, workspace
  kind/binding/availability/lifecycle enums, WorktreeRecord status set.
- Conformance matrix gains: `artifact.*` and `workspace.*` anchors; the projection-rebuild and
  materialization-round-trip families flip to implemented.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for the entity records + enums, `WorkspaceRecord` (split
  syncable/device-local), `WorktreeRecord`, materialized-path provenance; migrations for the
  entity/workspace/worktree families; default workspace settings (`git_init`, ignore set).
- **Docs**: entity-layer module doc + the claim/evidence/provenance derivation references; workspace
  module doc + identity/path-split + `.atlas/` layout + materialization-mirror + sync-loop +
  worktree docs; **banned-vocabulary update** (checkpoint dir names, shadow-history terms).
- **CI/local commands**: the materialization-round-trip, mirror-rebuild, relocation, atomic-write,
  self-write-suppression, and worktree-lifecycle suites as named CI jobs.

## 8. Exit criteria

- [ ] Materialization round-trip suite green on 3 OSes.
- [ ] An agent run produces a cited Document artifact, materialized to a workspace, externally
      edited, re-versioned — fully ledgered; `provenance.query_derivation_chain` reconstructs the
      lineage.
- [ ] Worktree create→merge→discard→orphan-quarantine cycle green.
- [ ] M0–M2 still green.

## 9. Locked in this phase

- **The closed entity enums** — ArtifactKind, state sets, Claim/Evidence/Citation/Observation
  taxonomies, **StalenessFingerprint variants** (04's revalidation depends on them),
  MaterializationPolicy.
- **EvidenceLink edge-metadata shape + the ClaimStatus/ValidationState derivation rules**
  (replay-deterministic algorithms).
- **`workspace_id` identity (UUID, never path-derived) + the identity/path locality split** ("the
  path does not travel, the identity does") — P20 sync depends on it.
- **Disk-tree-is-a-projection** — no parallel file-history store, ever (24 §8.3/§23).
- The `.atlas/` layout + instruction-file hierarchy; the materialized-path resolution algorithm;
  WorktreeRecord status enum + data-root placement.
