# Phase 3 — Data Spine (Ledger, Events, Hooks, Blocks, Version Graph)

## 1. Goal & why now

The coupled durable substrate at the heart of the system, designed **together**: the ExecutionLedger +
EventStream + Hook system (File 10), the immutable Block pool (File 08), and the VersionGraph with
projections (File 11). Blocks are content, the ledger is consequential-fact history, the version graph
is accepted-state history; they share commit boundaries, the scope/sensitivity vocabularies, and the
three canonical hashes. Everything downstream — execution, surfaces, retrieval, UI — needs durable
content to create, revise, cite, and render, and a history that cannot be forged. The three forgery
guards and the three hashes land here and never move.

## 2. Canonical scope & deferrals

- **File 10 — core**: `LedgerEntry` schema + append-only + `supersedes` corrections (§3.2–§3.3);
  cross-reference key set (§3.6); **`ledger.forgery-guards`** — status-transition, contract-revision,
  unkeyed-scalar, enforced at the ledger commit boundary (§3.7); the closed `LedgerEntryKind`
  catalogue (§4.1 — types defined for all kinds, payloads populated as producers come online);
  `EventEnvelope` + per-`sequence_scope` monotonic ordering + dedup (§5.2); AppEvent catalogue +
  transient/durable split + delivery classes + backpressure (§5.3–§5.5); sensitivity-at-emission +
  Secret-stripped-at-commit (§5.6, §10); the `Hook` contract — decision vocabulary
  {Continue, Substitute, Block, RedirectSuggestion}, `priority: i16` convention (−100/0/+100),
  authority classes, fail-direction, `InternalHandler` action (§7–§9 partial); `TokenUsageRecord`
  schema + `TokenSource` enum (§6 — populated for real in P7); the **hash-chained per-device audit
  overlay** (§10.5, §16 — crypto binding completed in P7/P8 with File 22 §14); replay-semantics
  *contract* + required cross-references (§11 — engine realization → **P13/P21**).
- **File 08 — complete core**: `Block` required fields (§2.2); `BlockContent`
  Inline/External/Composed over P2 blobs (§4); **`block.content-hash`** over CanonicalEncoding with
  per-variant domains (§4.5); closed `BlockKind` + `BlockEdgeKind` catalogues + `Custom` registration
  (§3, §5); the 11-check commit validator (§8.2); event-then-block streaming commit boundary (§7);
  lifecycle/pin as *derived* version-graph state — state set + transition rules here, the maps in
  this phase's version-graph lane (§6); sensitivity + per-field map + composition max-inheritance
  (§9); scope + promotion (§11); hard delete + tombstones (§6.6, exercised via the version-graph
  `HardDeleteBlock` op).
- **File 11 — complete core**: `ContextVersion` (§3.2); `VersionDiff` + **`version.diff-hash`** (§4);
  `VersionOpSummary` + commit-boundary discipline (§5); the durable `pending_ops` buffer +
  in-session undo via typed inverses (§6); the `context_view` materialized view +
  **`version.expected-view-hash`** (§7); deterministic switching (§8); branching/forking — both
  branches permanent (§9); derived-state maps (§10); the `ContextOp` vocabulary + inverses + merge
  rules + `HardDeleteBlock` floor (§11); sibling-block versioning (§12); `Snapshot` catalogue +
  resolution contract (§14 — per-substrate resolvers stub until owners exist); the generalized
  `Projection` contract (§16); GC/tombstone/compaction ops (§20); **both-children-survive / no-LWW
  merge semantics** (§19 — implemented here, transported in **P20**); `Inspect` replay data (§15 —
  read-only reconstruction; the engine → **P13**).
- Deferred: hook actions RunScript/InvokeCapability/EmitEvent → **P5+** (with policy/capabilities);
  entity layer over blocks → **P9**.

## 3. Prerequisites

P2 — storage families, blob store, projection orchestrator, write-boundary guards. P1 hashes.

## 4. Lanes

A **design pass precedes code**: one short design doc fixing the interlocking shapes — the commit
boundary set (08 §7.6 ≡ 11 §5.2), lifecycle/pin ownership (08 defines, 11 owns), id formats, the
three hash domains — reviewed against all three canonical files. Then three lanes converging at the
commit boundary: (a) ledger + bus + hooks + audit overlay, (b) block pool + commit validator,
(c) version graph + `context_view` + pending-ops. The forgery-guard mechanism belongs to lane (a);
its full completion-contract integration waits for P6 (the contract object is authored there — the
guard engine is built now against the contract *type*).

## 5. Build plan

1. **Ledger + stream**: append-only ledger family over P2; the event stream with envelope + per-scope
   monotonic sequence + dedup; consequential events commit to the ledger before/atomically-with stream
   delivery — pure coordination stays stream-only (10 §5.4).
2. **Forgery guards at the commit boundary** (10 §3.7): deterministic, no model calls;
   `LedgerCommitRejected` + `RunCompletionForgeryAttempted` paths; plus Secret-payload rejection,
   unique `entry_id`, resolvable `supersedes`, existing referenced primitives.
3. **Hook system**: subscription registry, blocking + non-blocking dispatch, priority ordering with
   Substitute staging, authority enforcement (observe_only downgrade + warning), fail-direction by
   category, timeout-synthesized decisions, `InternalHandler` only.
4. **Block pool**: immutable records; commit validator (the 11 checks, typed `BlockCommitRejected`);
   content_hash; kind/edge catalogues + `Custom` registration (duplicate `(namespace,name)`
   rejected); edit-as-sibling + `supersedes`; event-then-block boundary with `partial_block_handle`.
5. **Version graph**: ContextVersion tree; VersionDiff (net effect, not per-op) + diff_hash; durable
   `pending_ops` on `ConversationVersionState` (survives restart); commit-at-boundary; `context_view`
   registered with the P2 orchestrator (O(1) reads, O(path) rebuild); `expected_view_hash`
   verification + rebuild-on-mismatch; switch path-walk; branch-on-commit-after-switch; derived
   lifecycle/pin maps; ContextOps + undo inverses + merge rules; hard delete with tombstone — a
   live-`Composed`-parent target fails closed as typed `Unsupported` per File 08 §6.6's parked
   disposition plan (the carrier kinds are catalogue-registered; the disposition workflow is not
   scheduled here); snapshot reference catalogue + deterministic resolution (resolvers
   stubbed per-substrate, never falling back to current state).
6. **Audit overlay**: per-device hash chain (entry_hash formula 10 §16.2), genesis at first boot,
   verify-at-startup, never-syncs.
7. **Restart reconstruction**: pool reload → version-graph reload → `context_view` verify/rebuild →
   `pending_ops` reload (inconsistent buffer discarded with `PendingOpsInconsistencyDetected`) →
   derived maps recompute on first read (08 §13.3, 11 §18.3).

## 6. Test obligations & acceptance evidence

- **Forgery-guard suite** (10 §3.7) — the spine tests: `running → completed` with no action evidence
  rejected (`LedgerCommitRejected` + `RunCompletionForgeryAttempted`); unauthorized contract
  Weakening rejected ("weakening fails the same guard"); unkeyed model-dependent scalar rejected.
- **Hash goldens ×3**: `block.content-hash` (all three content variants; Composed order-sensitive;
  External hashes the reference identity; Sensitive fields included), `version.diff-hash`
  (`CanonicalVersionDiffEncoding`, stable sort, schema-version tag), `version.expected-view-hash`
  (row set sorted by block_id).
- Append-only/immutability: committed entries fixed (corrections supersede); block in-place mutation
  of `content`/`kind`/`content_hash`/`producer` invalid; ContextVersion immutable except
  label/bookmarked/expected_view_hash.
- Commit-validator positive/negative per check (composed-with-no-children, evidence-without-cites,
  oversized inline artifact, sensitivity-underreport auto-escalation, undeclared kind, dangling
  refs); id-stability (08 §8.1).
- **`context_view` rebuild equivalence** into the P2 harness; tampered diff fails the view-hash →
  rebuild + `MaterializedViewIntegrityViolated`, never trust-the-hash.
- Switch/branch determinism: switch to any node and back reproduces the exact view; commit after
  switching to a non-leaf creates a sibling, both switchable, neither overwritten; net-diff
  correctness (mask→unmask→commit = empty diff); operation-merge determinism; undo inverses;
  `pending_ops` durability across restart.
- **No-LWW at the version layer**: concurrent commits produce sibling branches, never a clobber;
  per-device pointer never yanked (11 §19.3–19.4, unit level).
- Event ordering: monotonic per sequence_scope; ledger-commit-before-later-sequence (10 §5.4);
  `lossless_consequential` never silently dropped; overflow → `EventBufferOverflow` + degraded.
- Hook suite: priority order incl. Substitute staging; authority downgrade; fail-direction; timeout
  synthesis; out-of-vocabulary decisions rejected.
- Secret-redaction-at-commit across ledger/event persistence paths (10 §5.6/§10.3); audit-chain
  tamper detection breaks the chain forward + halts sync (10 §16.5).
- Lifecycle: no time-based transitions (08 §6.7); derived maps rebuild from the action log.
- **Closed-set pinning** for `BlockKind`, `BlockEdgeKind`, `LedgerEntryKind`, `AppEvent`,
  `HookDecision`, `HookAction`, `ContextOp`, `VersionOpSummary`, the `Snapshot` catalogue.
- Conformance matrix gains: `ledger.*` core, `block.*`, `version.*` anchors; forgery-guard,
  secret-boundary, audit-chain, closed-set, projection-rebuild families flip to implemented for the
  spine.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared Rust↔TS types for `Block`/`BlockKind`/`BlockContent`/`BlockEdgeKind`,
  `ContextVersion`/`VersionDiff`/`ContextOp`/`VersionOpSummary`, the ledger/event catalogues + the
  envelope schema, `TokenUsageRecord` (keying enforced); migrations for the ledger/block/version/audit
  families; the three hash fixture sets.
- **Docs**: spine design doc (the interlock decisions); block-model + kind/edge catalogue reference;
  version-graph + commit-boundary catalogue + `context_view` integrity docs; ledger/event/hook module
  docs + the forgery-guard doc; audit-overlay doc; **banned-vocabulary update** — the deleted
  checkpoint vocabulary (`file_checkpoints`, `MessageVersion`, `SessionCheckpoint`, "audit log",
  "event bus", "middleware") wired into the grep.
- **CI/local commands**: the hash-golden suites, forgery-guard suite, audit-chain suite, and
  no-deleted-vocabulary grep as named CI jobs.

## 8. Exit criteria

- [ ] All three hash goldens green cross-OS; forgery-guard suite green.
- [ ] P2 equivalence harnesses extended with the spine families + `context_view`, still green.
- [ ] Kill-mid-session restart test: reload → identical derived state or typed gaps.
- [ ] Audit chain verifies at startup; deliberate tamper detected.

## 9. Locked in this phase

- **`LedgerEntry` schema + `EventEnvelope` shape** — carried by every fact in the system; changing
  them migrates the entire ledger / ripples to every transport and consumer.
- **The three forgery guards' semantics and their placement at the ledger commit boundary** — the
  integrity floor; relocating or weakening them reopens completion forgery.
- **Block required-field set, `BlockContent` variants, kind/edge catalogues**; `block_id` stability.
- **`VersionDiff` field set + net-effect semantics; ContextVersion immutability boundary; the
  Snapshot catalogue + references-not-copies discipline.**
- **Hook decision vocabulary + priority convention + authority classes** — the shared extensibility
  contract for 03/06/35/39 and beyond.
- **Both-children-survive / no-LWW / no-squash merge semantics** (11 §19.3) — the durable-state merge
  guarantee P20 transports later.
- Lifecycle/pin as version-graph-owned derived state — never stored on blocks (the tempting
  "optimization" that breaks the architecture).
