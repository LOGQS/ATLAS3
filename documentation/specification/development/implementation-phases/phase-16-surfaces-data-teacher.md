# Phase 16 — Surfaces Wave 2: Data Processor & Teacher

## 1. Goal & why now

The third and fourth surfaces, in dependency order *within* the phase: **Data Processor** first (the
artifactized data lab; its `data.extract`/`data.chart` are hard dependencies of Teacher's flagship
slices), then **Teacher** (artifactized, mastery-tracked tutoring — the heaviest cross-surface
borrower in the system: Coder code-exec for grading, Data extraction for teach-from-document, Web
search for sources). This wave proves the borrow graph under real load: surfaces composing other
surfaces' capabilities through policy, never through private integration.

## 2. Canonical scope & deferrals

- **File 29 — complete core**: the Data Processor `SurfaceContract` (`surface_id: data_processor`,
  `data.*`); **the artifactized-data contract + analytical query** — `data.query` over a sandboxed
  in-process analytical engine, file-resident tabular data, schema inference; results are
  `Table`/`Dataset` artifacts + `DatabaseQueryResult` observations + `derives_from` lineage;
  in-memory relations never cross run/turn/export boundaries unless materialized (§6–§7); query
  read-only by default — write-back a distinct gated mode with preview + typed-confirmation (§7.7);
  document extraction — parse/schema-driven/table/entity with **`SourceSpan` grounding** ("an
  ungroundable extraction is likely fabricated") (§8); transforms with lineage-bearing revisions
  (§9.2); pipelines as `Pipeline`-context workflows contributing data `Custom` node kinds into the
  P14 catalogue + the node cache-key rule ("content hash alone is insufficient") (§9.3); notebooks —
  `Notebook` artifact = Composed block of immutable cell children, outputs as linked blocks (§10);
  profiling — the canonical first operation, a projection keyed by content hash + config (§11);
  validation — `SchemaValidation` → the completion floor (§12); visualization — `Chart` = spec +
  data binding + renderer hint (§13); media-as-data; **generative media explicitly out** —
  borrowable, a future surface (§14.3); DB connections via vault refs, redaction-safe metadata only
  (§22.3). Vision/OCR extraction availability-gated on a vision model.
- **File 30 — complete core**: the Teacher `SurfaceContract` (`surface_id: teacher`, `teacher.*`);
  **the explanation contract** — `teacher.explain` → `Lesson` artifacts (Composed blocks of typed
  parts, **no `LessonBlock` kind**) with proportionate citation grounding — pedagogical framing
  needs no citation, load-bearing claims do (§6–§7); teach-from-document — curriculum over
  **borrowed `data.extract`**; the concept-prerequisite graph IS the File 12 entity-relationship
  projection, never a private skill tree (§8); assessment — generation/grading; objective →
  `Validation`, subjective → `Critique`, with recorded rubric/model-selection for replay; **code
  grading via borrowed Coder execution + its SandboxProfile — Teacher owns no sandbox** (§9);
  interactive artifacts with `schema_version` + load-state migration hooks (§10.4); practice/SRS —
  flashcards; **scheduling state in `Mastery` memory validity** (no schedule table) + event-first
  review-due Automations over P14 (§10); the multi-agent classroom — coordinator + role-differentiated
  child runs over 02 §7/04 §16, director strategies, scene filtering via the availability evaluator
  (§11); mastery + learner persona over File 14 — `Mastery` kind, core-memory persona read at session
  start, learner data `Sensitive` by default, **no `user_id` ever** (single-learner; multi-learner is
  a future Memory-scope extension) (§12); progress via borrowed `data.chart` (§12.3); per-profile
  seeds + accessibility-first presets (§16).

## 3. Prerequisites

P15 — Coder exec + Web search to borrow. P14 — pipelines/curricula as workflows; review-due
Automations. P13 — SchemaValidation + grading validators. P10 — memory `Mastery` + the
entity-relationship projection + retrieval. P8/P9 — sandboxed engine; artifacts.

## 4. Lanes

Data Processor and Teacher are parallel lanes **except** Teacher's teach-from-document and progress
slices, which wait for Data's extract/chart capabilities — sequence Data's extraction/chart slices
early so Teacher's dependent slices unblock mid-phase. Within Data: query engine → extraction →
transforms/pipelines → notebooks/profiling/charts. Within Teacher: explanation → curriculum →
assessment → mastery/SRS → classroom.

## 5. Build plan

1. **Data engine slice**: the analytical engine as a confined dependency (sandbox profile per
   §15.4); `data.query`; artifactized results + lineage edges.
2. **Data extraction slice**: document parsing with grounding; structured outputs validated against
   declared schemas; `SourceExcerpt` promotion.
3. **Data composition slice**: transforms; pipelines (data node kinds registered into the P14
   `NodeKind` catalogue); notebooks; profiling; `SchemaValidation`; charts. Heavy chart, notebook,
   pipeline, and graph renderers stay behind the `RendererRegistry` and are selected by measured
   per-surface evidence.
4. **Teacher explanation slice**: `teacher.explain` → Lesson artifacts; depth as a workflow
   parameter; transient spoken explanation commits nothing (§6.2).
5. **Teacher curriculum slice**: teach-from-document over borrowed extraction; the concept graph;
   source-bound runs produce typed provenance gaps for uncovered concepts — general model knowledge
   never silently becomes source-grounded material (§13.2).
6. **Teacher assessment slice**: quiz/practice generation; grading → Validation/Critique; code
   practice via borrowed Coder exec; historical inspection reads recorded critiques, never
   re-grades.
7. **Teacher mastery slice**: assess-and-update-mastery proposals through 14's grounded-update +
   approval discipline; SRS via validity + review-due Automation; progress via borrowed
   `data.chart`.
8. **Teacher classroom slice**: coordinator + child agents over a shared transcript; director
   strategies; scene-based action filtering.
9. **Registrations**: both contracts through the P11 validator; data validators (schema, lineage,
   grounding) + teaching validators **tied to a Rubric/source-grounding target — "generic
   uncalibrated correctness judges are not canonical defaults"** into 39; Data + Teaching eval
   suites into 40.

## 6. Test obligations & acceptance evidence

- **No-private-architecture conformance** (the central family): both contracts pass the P11
  validator; **no `data_lineage` table** (lineage IS the `derives_from` graph); **no
  notebook/cell tables** (Composed blocks); **no `teacher_*` tables, no `LessonBlock`, no private
  classroom orchestrator/SRS scheduler/adaptive-difficulty engine/skill tree**; a feature that seems
  to need a new durable table is reframed as block/artifact/memory/observation/edge/projection —
  grep + validator.
- 29 — the conformance round-trips (§24), **replayed over recorded observations, never a live
  query/engine**: ingest→dataset-artifact; query→table+observation; extract→grounded-structured-
  output; transform→lineage-edge; notebook-cell-execution; pipeline-as-execution-structure;
  profile-as-observation; schema-validation gate; chart-as-artifact; lossless dataset+lineage export
  round trip. Plus: the grounding harness — ungroundable values flagged/excluded (§8.4); the
  completion floor — prose-only valid only for explanation-only runs (§15.5); replay isolation —
  recorded results never re-query, refresh is a new invocation (§7.6); **node cache-key
  completeness** (§9.3); untrusted-data authority — instructions inside ingested files/DB values
  hold none (§8.6); PII/credential redaction (§22.3); write-back gated (§7.7).
- 30 — the conformance round-trips (§24), **replayed over recorded blocks, never live
  re-explanation/re-grade**: explanation→lesson-artifact; document→grounded-curriculum;
  quiz-generation-and-grading→Validation/Critique; practice-code→validation;
  classroom-as-child-run-structure; mastery-update→memory; flashcard-review→mastery-validity;
  lossless lesson/curriculum export. Plus: the proportionate-grounding boundary (§6.4/§8.3);
  source-binding gaps typed (§13.2); untrusted-study-material authority (§8.6); **the implicit
  code-execution guard** — snippets from material run only through a visible, policied, borrowed
  execution invocation (§15.4); **learner-data privacy** — `Sensitive` by default, redacted in
  context/events, egress opt-in, destructive reset behind the `Denied`-floor typed-confirmation
  (§22.3); interactive-artifact `schema_version` migration (§10.4); **no `user_id`** (grep).
- **The borrow graph under policy**: Teacher borrowing Coder/Data/Web capabilities passes the same
  declarations/policy/ledger paths — no surface-private shortcuts (the wave's headline integration
  test).
- Renderer-performance evidence: large chart/table/notebook views, data pipeline graphs, and the
  teacher concept-prerequisite graph have File 40 `Latency` suites over recorded fixtures on all
  three desktop platform webview realizations.
- **Closed-set pinning**: both surfaces' panel/selection/produced-kind sets; data event names;
  teacher event names; director strategies; classroom roles.
- Conformance matrix gains: 29/30 anchors; Data + Teaching eval families seeded.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: both surface contracts; data node-kind registrations; shared types for
  the produced kinds; the node cache-key and profile cache-key schemas; recorded
  engine/extraction/grading fixtures.
- **Docs**: data surface doc (the artifactized-data-lab reframe); teacher surface doc (the
  mastery-tracked-tutor reframe + the borrowed-capability map); the `data/` and `teacher/` workspace
  subdir conventions; decision record: the analytical-engine choice (replaceable behind the
  contract).
- **CI/local commands**: the data round-trip, teacher round-trip, grounding, borrow-under-policy,
  learner-privacy, renderer-latency, and no-private-table grep suites as named CI jobs.

## 8. Exit criteria

- [ ] Data: CSV → profile → query → transform → chart → export, lineage queryable end-to-end via
      `provenance.query_derivation_chain`; replayed in CI.
- [ ] Teacher: document → curriculum → lesson → quiz → graded code exercise (through the borrowed
      Coder sandbox) → mastery update → review-due automation fires (injected time) — end-to-end;
      replayed in CI.
- [ ] The borrow graph proven under policy; both contracts pass conformance.
- [ ] M0–M3 still green.

## 9. Locked in this phase

- **Lineage = the `derives_from` graph** (no lineage table); **notebook = Composed-block artifact**;
  the `DatabaseQueryResult` observation field set (the replay schema); the Table-vs-Dataset
  inline/external split; the Chart spec shape; the data node cache-key composition.
- **Lesson/Curriculum = Composed-block artifacts**; **no `user_id`/learner record** — multi-learner
  is a future Memory-scope extension, never a parallel user table (30 §12.4); **SRS state in
  `Mastery` validity** (no schedule table); classroom = run structure + version-tree projection; the
  submitted-attempt block shape.
- Produced-kind registrations + the `data`/`teacher` event namespaces;
  `surface.data_processor.*`/`surface.teacher.*` settings; selection kinds; the concept graph as the
  shared entity-relationship projection (coupling Teacher to File 12's schema).
