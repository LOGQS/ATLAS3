# Phase 10 — Substrate Services (World Model, Perception, Retrieval, Memory)

## 1. Goal & why now

The four always-available substrate services: the File 18 WorldModel (live structured environment
state + the capability-availability evaluator), File 19 Perception (sensing + observations), File 12
Retrieval (rebuildable index projections + the knowledge base), and File 14 Memory (curated learned
state). Closing this phase un-stubs the consumers that have been waiting: routing's world snapshot
(03 §3.1), capability availability predicates (05 §15.2), lease revalidation triggers (06 §10.3),
surface availability filtering (07 §9), run-start world snapshots (04 §6), and memory/retrieval as
assembly sources (13 §3/§6). The surfaces cannot be specced honestly without these four.

## 2. Canonical scope & deferrals

- **File 18 — complete core**: `WorldEntity` + the closed kind catalogue + relations (§4);
  `SurfaceState`/`PanelState`/`Selection`/`UiMode` (§5); durability tiers + floors (§7); the
  deterministic projection `(world_model, signal) → world_model` + producer-ownership + revision
  preconditions (§8); **the availability evaluator** over `requires`/`blocked_by` + pure named
  checks + prerequisite capabilities (§9); the durable world-state log + `world_snapshot_id`
  resolution (§10); `WorldView` consumer projections (§11); reactivity events (§12); the world
  capability surface (§13); restart reconciliation — stale never presented as current (§8.7).
- **File 19 — core**: `Sensor` + the closed `SensorKind` catalogue (§4); tiered sensing
  Structured/Grounded/Raw + `CaptureNeed` + merge-not-cascade (§5); the capture pipeline +
  content-addressed dedup + **golden capture encodings** (§6); structured sensors now —
  `FileSystem`, `Environment`, `Repository`, `Process`, `SystemMetric` basics (§7 per-modality
  contracts instantiated as needed); the output contract — transient `PerceptionSignal` → the 18
  projector, deliberate Observation commits → 09 with fingerprints (§9); the capture-privacy layer —
  permission states, consent gates, redaction, scope bounding, capture ethics (§10); per-source
  failure isolation (§12). Desktop accessibility tree, browser, audio sensors → **P15/P17**
  (additive registrations); model-mediated processors (OCR/grounding/transcription) → with their
  consumers.
- **File 12 — complete core**: `RetrievalIndex` projections — Lexical + ById + Structural first,
  Vector when an embedding backend is configured with the full identity tuple (§2, §6);
  `IndexNamespace` families (§3); source records over blocks/versions/observations (§4);
  `SourceExcerpt` promotion (§5); the query pipeline + normalized
  `RetrievalQuery`/`RetrievalResult`/`RetrievalHit` (§7–§9); the knowledge-base entity layer +
  curation (§10); sensitivity — Secret never enters an index, chunks split-or-reject (§11); the
  indexing commit path + deterministic rebuild (§12); ingestion (§14); **ATLAS.md indexing** (§15)
  joining 13 §16's inclusion authority.
- **File 14 — complete core**: `MemoryEntry` over Memory blocks (§3); kinds/scopes/facets (§4);
  CoreMemory/ArchivalMemory tiers (§5–§6); explicit remember/forget/recall + **the grounded 4-op
  update protocol with local-id remapping** (§8.1/§8.3); proposal policies (§8.4); recursion
  prevention (§8.5); salience/validity/retention shapes (§7, §9–§10); provenance (§11); memory in
  assembly — core early, archival via RetrievedContext (§2.3); the `memory:` namespace (§6).
  Implicit learning/distillation + consolidation (§8.2, §12) → any later phase (background
  extraction is ordinary execution; the explicit path is v1-complete per §18 — consolidation cadence
  becomes an Automation in P14).

## 3. Prerequisites

P9 — Observations + fingerprints, workspace identity, instruction files. P7 — embedding/model
backends optional (lexical-only is spec-valid). P8 — watcher/process confinement for sensors.

## 4. Lanes

Four lanes: (a) world model — store, projector, SurfaceState, snapshots, evaluator; (b) perception —
pipeline + the structured sensors (joins (a) at the signal contract); (c) retrieval — indexes,
query pipeline, knowledge base, ATLAS.md; (d) memory — entity + explicit path + assembly
contribution (consumes (c)'s `memory:` namespace). (a)∥(c) fully; (b) after (a)'s projector;
(d) after (c).

## 5. Build plan

1. **World model**: in-memory entity store + the durable world-state log; self-registration APIs
   (`world.register_surface`/`set_focus`/`update`) with producer ownership + revision preconditions;
   SurfaceState per scope (headless descriptor valid); snapshot resolution over the log (the P3/P6
   resolver stubs become real).
2. **Availability evaluator** (18 §9): deterministic over (world, registry, ledger) snapshots;
   un-stub 05 §15.2 filtering, 07 composition step 9, and 06 §10 lease-revalidation triggers.
3. **Perception**: capture pipeline with golden encodings; the FileSystem sensor first — composing
   24's watcher discipline (one watcher substrate, no parallel watchers); Environment/Repository/
   Process sensors; signals → projector; deliberate observations → 09 with fingerprints; consent/
   permission gates + redaction before durable commit.
4. **Retrieval**: index projections registered with the P2 rebuild orchestrator; deterministic
   entry identity; conversation/workspace/knowledge/memory/observation namespaces; the query
   pipeline (skip-irrelevant-stages); ATLAS.md → source records → 13 instruction inclusion with
   authority classes.
5. **Memory**: the explicit-command path end-to-end (remember/forget/recall capabilities); grounded
   updates — the runtime supplies the candidate set, the model selects by local id, the runtime
   resolves + revision-checks (the forgery guard for memory); core-memory contribution to assembly;
   archival search via 12.
6. **Integration un-stubbing pass**: routing frame world snapshot; run-start snapshot refs; 13
   RetrievedContext + memory regions live; lease revalidation on world change.

## 6. Test obligations & acceptance evidence

- 18: **projection determinism** — same ordered signals → same world model (§8.2); snapshot
  resolution determinism + never-falls-back-to-current (§10.3); **evaluator determinism + no clock
  effects** (§9.5); named-check purity — no hidden inputs (§9.3); producer-ownership conflicts
  typed, no LWW (§8.2); restart reconciliation (§8.7); rebuild-equivalence into the P2 harness
  (§10.4); Secret facts never durable raw + durability floors hold (§7.3); availability
  recomputation is event-driven (a capability appears/disappears from the tool surface as world
  state changes — no clocks).
- 19: **golden capture-encoding fixtures** (§6.4 — explicit canonical obligation);
  capture-replay determinism — a recorded Observation + fingerprint reconstructs; an unchanged
  source re-captures to the same content hash (§6.2/§9.5); processor invocation-identity keying
  (§9.4); fingerprints computed at capture back mutations (§9.3); consent/permission gates +
  secret/PII redaction + scope bounding + symlink-resolved-before-boundary (§10); per-source
  failure isolation — one sensor's failure never crashes the service (§12.3); event-first — the
  system remains correct if a fallback capture never runs (§8.2).
- 12: rebuild determinism + entry-identity preservation over unchanged inputs (§2.3, §12.3 — golden
  index states); freshness by fingerprints/version anchors, never time (§2.4); **Secret never
  indexed** + chunk split-or-reject (§11); dedup preserves provenance + contradictions (§8.3);
  corruption → rebuild/degrade-typed/fail-typed, never silent partial retrieval (§12.4); result
  traceability + replay reconstruction (§19); the embedding identity tuple enforced when vectors
  enable (§6.1).
- 14: **grounded-update forgery guard** — the model never invents memory ids (§8.3); revision-safe
  concurrent edits — no silent LWW (§8.3); **recursion prevention** — no self-amplification from
  memory-injected content (§8.5); index loss never destroys memory content (§6); equal-strength
  contradiction stays unresolved (§11); no raw secret in any memory sink (§18); expiration is a
  validity rule, not polling (§7); no unqualified mutable scalars (§3.3/§10).
- **Closed-set pinning**: WorldEntityKind, SurfaceState/PanelState/SelectionKind/UiMode, durability
  tiers, SensorKind, SensingTier/CaptureNeed, index kinds, namespace families, hit kinds,
  MemoryKind/MemoryScope.
- Conformance matrix gains: 18/19/12/14 core anchors; the P5/P6 availability and snapshot stub rows
  flip from partial to implemented.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `WorldEntity`/`SurfaceState`/`WorldPredicate`,
  `Sensor`/`CaptureRequest`/`PerceptionSignal`, `RetrievalQuery`/`Result`/`Hit`, `MemoryEntry`;
  golden capture-encoding fixtures; migrations for the world-log/sensor/index/knowledge/memory
  families.
- **Docs**: world-model module doc + the evaluator reference; perception pipeline + capture-privacy
  docs; retrieval substrate + namespace + knowledge-base docs; memory module doc + the
  grounded-update protocol reference; the instruction-file (ATLAS.md) indexing/inclusion doc.
- **CI/local commands**: `index-rebuild`, `world-verify`; the projector-determinism,
  evaluator-determinism, capture-golden, index-rebuild-determinism, grounded-update, and
  memory-recursion suites as named CI jobs.

## 8. Exit criteria

- [ ] All four services pass their determinism/rebuild suites; the P2 equivalence harnesses extended
      and green.
- [ ] Availability evaluation live end-to-end (event-driven appearance/disappearance test).
- [ ] An agent turn can recall a memory, search the workspace index, cite an ATLAS.md instruction
      (with correct authority class), and act on a fresh observation — fully recorded and replayable.
- [ ] M0–M2 still green.

## 9. Locked in this phase

- **The `WorldEntityKind` catalogue + `WorldEntity` field set + `SurfaceState` shapes** (consumed by
  03/06/07/25/26/37).
- **The `WorldPredicate` families + evaluator determinism contract** — capability availability
  system-wide.
- **Capture canonical encodings + `capture_encoding_id`/versions** (golden-locked); the **processor
  invocation-identity tuple**; the `PerceptionSignal` shape (cross-file with 18 §8.2).
- **Index-entry identity derivation + the embedding identity tuple + namespace string formats**
  (`conversation:`, `workspace:`, `knowledge:`, `memory:<scope_id>`, `observation:`,
  `ingested_codebase:<workspace_id>`, `web_cache:` reserved).
- **The `RetrievalQuery`/`RetrievalResult`/`RetrievalHit` required fields** (every consumer from 13
  to the surfaces).
- **MemoryKind/MemoryScope enums + the grounded-update wire protocol + the entity/block content
  split** (separate sources of truth rejected).
