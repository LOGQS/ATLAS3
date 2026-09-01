# Evaluation and Benchmarking

## Status

Canonical.

## Scope

This file defines:

- the offline evaluation layer — measuring, comparing, and regression-testing the system over recorded runs and fixtures, as the offline counterpart to File 39's inline validation
- the `EvalSuite` primitive — the versioned, parameterized binding of a fixture set to scorers, golden artifacts or expected properties, a pinned policy and model-profile configuration, success criteria, and a regression baseline
- the `EvalCase` — one fixture plus its expected outcome and the scorers that apply to it
- the fixture model — `RecordedRunFixture` (a pinned reference to a past run's ledgered scope and snapshots) and `SyntheticFixture` (a typed, pinned input bundle), and the determinism contract that an evaluation re-derives nothing from live mutable sources
- golden-artifact comparison — the closed `GoldenComparison` taxonomy (`ExactMatch`, `StructuralDiff`, `PropertyAssertion`, `SemanticEquivalence`) and the cheap-deterministic-first ordering
- the `Scorer` and the per-case verdict-and-score model — reuse of File 39's `Validator` and File 09's `Validation`/`Critique` as the per-case verdict, the binary/multi-class-not-continuous rule, and the aggregate-figures-are-projections rule
- the `EvalRun` — the recorded execution of a suite, run as a `Run`, fanning child runs per case, reusing the replay engine and the replay modes; and the eval-forgery guard
- the closed `EvalFamily` set and each family's primary artifact — discharging the offline-evaluation deferrals left by Files 03, 07, 13, 14, 16, 17, 21, 24, 25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 38
- comparison evaluation — A/B, best-of-N, arena, and tournament-pairwise comparison over the canonical comparison-run shapes, the blind-comparator discipline, and win-rate / ranking projections
- regression detection and evaluation-gated evolution — the `RegressionBaseline`, the `RegressionReport`, the eval-blind-iteration guard, and the optional eval-pass gate on graduation, install, and promotion
- the judge-optimization pipeline — the long-running, user-gated, cost-previewed `JudgeOptimization` run, the annotation queue and dataset, the error-analysis workflow, the train-a-judge-from-a-conversation flow, the provider-agnostic optimizer, and the deploy-as-ensemble-behind-a-router option
- `EvalScore`, `EvalReport`, and leaderboards as derived projections
- cost, budgets, and scheduling of evaluation runs; the `eval.*` capability surface and the evaluation surface-and-service duality; events; settings and per-profile defaults; persistence, locality, and replay

This file does not define:

- the `Validator` primitive, the `ValidationBoundary` set, `ValidationSeverity`, the validation gate, the non-destructive correction model, the inline judge-execution discipline, or the validator registration path — File 39 owns those; this file consumes the `Validator` and runs it offline over recorded inputs
- the `Validation`, `Critique`, `Claim`, `Evidence`, `Citation`, or `Observation` block kinds, `ValidationOutcome`, `ValidationKind`, `ValidationState` derivation, the golden `ArtifactVersion`, or the `validation.run`/`validation.attach` and `provenance.*` capabilities — File 09 owns those; this file consumes them
- the `Run` lifecycle, the `RunCompletionContract`, the completion-forgery guard, child-run orchestration, the comparison-run shapes, budgets, or recovery — File 04 owns those; an `EvalRun` runs as a `Run`
- the `Hook` primitive, the ledger and event substrate, the `LedgerEntryKind` catalogue, the event envelope, or the custom-kind registration mechanism — File 10 owns those; this file registers `Custom { namespace: "evaluation" }` kinds
- the replay-capability declarations (`replay.inspect`, `replay.simulate_deterministic`, `replay.full_rerun`), the `ReplayRun` record, the replay modes, the `VersionDiff`/`diff_hash` golden-comparison primitives, or the version-graph-backed projection contract — Files 10 and 11 own those; this file owns the replay-engine realization those capabilities invoke and the evaluation layer over it
- `ModelSelectionRecord`, `ModelProfile`, `ModelSelectionPlan`, or `FallbackPolicy` — File 16 owns those; this file consumes them as the primary artifacts of model-selection evaluation
- `TokenUsageRecord`, `PricingSnapshot`, provider health, or rate limits — File 17 owns those; this file consumes them as the primary artifacts of cost evaluation
- live metrics, traces, structured logs, observability projections, or the observatory rendering surface plumbing — the Telemetry, Logging, and Observability spec (File 41) owns those; this file owns offline suites, benchmarks, scoring, and judge optimization
- the secret vault, secret detection/redaction, untrusted-content defense, or sandbox/process isolation within which an evaluation executes code — Files 22 and 23 own those
- storage schemas, sync transport, or UI rendering of evaluation dashboards, leaderboards, annotation queues, or comparison boards — Files 20, 21, 37, and 38 own those; this file specifies the data contracts they consume
- per-surface and per-subsystem evaluation content beyond declaring the family and its primary artifact — the owning specs register their family scorers through File 39's path

## Source Resolution

This file resolves evaluation, benchmarking, regression-testing, scenario-harness, golden-comparison, scoring, leaderboard, LLM-as-judge, judge-optimization, replay-evaluation, and eval-driven-iteration material into one boundary: the offline measurement layer over the one run, replay, validator, block, ledger, version, model-selection, and settings substrate.

Resolved design:

- Offline evaluation is not a separate engine, a parallel test runner, a second scheduler, or a private store. An `EvalRun` is a `Run` (File 04) that replays recorded runs or runs synthetic fixtures through the one replay engine, scores their outputs with `Validator`s (File 39) producing `Validation`/`Critique` blocks (File 09) and deterministic golden comparators, and records its results through the one ledger and version substrate. The net-new durable objects are the evaluation definition and record objects: `EvalSuite`, `EvalCase`, `EvalRun`; `EvalScore` and the reports are derived projections.
- Inline validation (File 39) and offline evaluation (this file) are the two layers of one quality discipline. File 39 gates live execution in real time; this file measures and compares over recorded and fixture inputs. The strategic single `EvaluationService` is honored by the two layers sharing the `Validator` and `Validation`/`Critique` contracts. File 39 is the inline service; this file is the offline service.
- Evaluation re-derives nothing from live mutable sources. It consumes recorded snapshots and immutable references; a deterministic evaluation reproduces its scores on replay, and a model-mediated evaluation reproduces its recorded verdict rather than re-invoking the model.
- Evaluation ships machinery, not foregone verdicts. The system ships the suite/case/run/score object model, the fixture and golden-comparison machinery, the scorer slot, the comparison shapes, and the judge-optimization pipeline. It does not ship a built-in general-purpose correctness or quality benchmark with foregone scores; suites and judges are narrow, authored per concern, and calibrated against recorded traces.
- Per-case verdicts are binary or small-closed-set, with reasoning; continuous quality figures are downstream aggregates, never per-case scores.
- Evaluation makes the system improvable without flying blind. Evaluation-gated evolution is the canonical posture: a change to an evaluated configuration dimension carries replayable before/after evidence before it is accepted as an improvement, and agent-generated extensions may be required to pass an evaluation before installation.

## 1. Chosen Model

Anchor: `eval.chosen-model`

ATLAS3 has one quality discipline with two layers. File 39 is the inline layer — `Validator`s that run as hooks during and around live execution and gate it. This file is the offline layer — evaluation suites that run the same validators, plus deterministic golden comparators, over recorded runs and fixtures to measure, compare, and regression-test the system without gating any live request.

An `EvalSuite` is the offline analog of a body-of-work over the one execution substrate, mirroring the body-versus-binding split used across the series (File 33's `Automation` binds a `Trigger` to a `RunIntent`; File 34's `Workflow` is the reusable body; File 05's `Capability` declares while File 09's `validation.run` invokes; File 39's `Validator` is the rule while File 09's `Validation` is the result). Here: an `EvalSuite` is the versioned definition; an `EvalRun` is a `Run` that executes it; a per-case verdict is a `Validation`/`Critique` block; an `EvalScore` is a derived aggregation projection.

The chosen model is the composition of objects already canonical plus three primary net-new durable definition-and-record objects:

- **Reuses the one run model.** An `EvalRun` is a `Run` (`run.run`, File 04 §2) created from a `RunIntent`; it fans out one child run per case (`run.child-runs-multi-agent-work`, File 04 §16) and uses the canonical comparison-run shapes (`run.child-runs-multi-agent-work`, File 04 §16.1 — best-of-N with a selector child run, arena-style ranked rounds, tournament-style pairwise comparison) for comparison evaluation. There is no parallel evaluation scheduler or runtime, exactly as `run.consequences-for-later-specs` (File 04 §29) requires of automation.
- **Reuses the one replay engine.** Evaluation over a recorded run is replay (`ledger.replay-semantics`, File 10 §11; `version.replay-semantics`, File 11 §15). `ledger.replay-semantics` (File 10 §11.6) assigns the replay-engine realization to this file. This file owns that realization and the comparison-and-scoring layer over it; it consumes the `replay.inspect`/`replay.simulate_deterministic`/`replay.full_rerun` capabilities and the `ReplayRun` record (`version.replay-semantics`, File 11 §15.5–15.6) rather than redeclaring them.
- **Reuses the one validator and result substrate.** A scorer is a `Validator` (`qc.validator`, File 39 §3) run offline, or a deterministic golden comparator; its per-case result is a `Validation` or `Critique` block (`artifact.validation-critique`, File 09 §14). There is no parallel scorer registry and no parallel result carrier.
- **Reuses the one ledger, version, settings, model-selection, and cost substrate.** Evaluation events are `Custom { namespace: "evaluation" }` (`ledger.custom-kind-registration`, File 10 §4.3); golden comparison uses `version.diff-hash` (File 11 §4.5); the evaluation invocation overlay is the `SettingsOverlay` evaluation context already named by `settings.scopes-profile-contexts-overlays` (File 15 §5.3); model-selection evaluation reads `ModelSelectionRecord`s (`model.model-selection-record`, File 16 §8); cost evaluation reads `TokenUsageRecord` and `PricingSnapshot` (File 17).
- **Owns three primary net-new objects.** `EvalSuite`, `EvalCase`, and `EvalRun` are durable definition-and-record objects realized through File 20's storage substrate. `EvalScore` and the derived reports are rebuildable projections (`core.projection`, File 01 §6.11), not durable source-of-truth objects.

`EvalSuite` is the canonical noun for an evaluation definition. "Eval set", "test suite", "regression suite", "benchmark", "scenario harness", "eval harness", and "scorecard" are vocabulary variants in source material for one or more aspects of the system this file defines; the canonical names here are `EvalSuite`, `EvalCase`, `EvalRun`, `EvalScore`, `EvalFamily`, `Scorer`, `GoldenComparison`, `RegressionBaseline`, `AnnotationQueue`, and `JudgeOptimization`.

This model realizes `core.substrate-services` (File 01 §2.4), which names "logging and evaluation" among substrate services, and `core.evidence-provenance` (File 01 §7.12). It discharges the offline-evaluation deferrals named by `qc.boundaries-with-adjacent-layers` (File 39 §2.6), `qc.judge-discipline` (File 39 §6.4), `qc.events-metrics` (File 39 §17.3), `qc.consequences-for-later-specs` (File 39 §22), `ledger.replay-semantics` (File 10 §11.6), `version.consequences-for-later-specs` (File 11 §24), and the "evaluation specs should/must" consequences of Files 03, 07, 13, 14, 16, 17, 21, 24, 25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, and 38.

## 2. Boundaries with Adjacent Layers

Anchor: `eval.boundaries`

### 2.1 With File 39 (Quality Control and Validation)

The boundary is fixed and load-bearing. File 39 owns the **inline** layer: the `Validator` rule, where it attaches (`ValidationBoundary`), what its verdict gates (`ValidationSeverity`, the validation gate), the non-destructive correction model, the inline judge-execution discipline, and the validator registration path. This file owns the **offline** layer: collecting validators into suites, running them over recorded and fixture inputs, comparing against golden artifacts and expected properties, aggregating scores, detecting regressions, and optimizing judges. The two layers share the `Validator` primitive and the `Validation`/`Critique` result objects: an offline suite runs the same validators over recorded inputs and aggregates their outcomes (`qc.validation-report`, File 39 §12.3 already states "a `ValidationReport` over recorded inputs is what an offline evaluation suite aggregates"). This file never redefines the `Validator`, the validation gate, `ValidationOutcome`, `ValidationSeverity`, or the judge discipline; it consumes them and runs them offline. The judge discipline (`qc.judge-discipline`, File 39 §6 — narrow not omnibus, context-isolated, binary-or-small-closed-set verdict, verdict-plus-reasoning, provider-agnostic, no built-in general judge) binds every model-mediated scorer and every judge this file optimizes. File 39 owns the inline execution of an optimized judge against live targets; this file owns the optimization run that produced it.

### 2.2 With File 09 (Artifacts, Claims, Evidence, and Provenance)

File 09 owns the result objects and the golden material: the `Validation`/`Critique` block kinds and their content, `ValidationOutcome`, `ValidationKind` (including `EvaluatorScore`), `ValidationState` derivation, the `Claim`/`Evidence`/`Citation`/`Observation` kinds, the `ArtifactVersion` (the durable golden artifact), and the `validation.run`/`validation.attach`/`provenance.*` capabilities. This file consumes them: a per-case verdict is a `Validation` or `Critique`; a golden artifact is a pinned `ArtifactVersion`; expected properties are `Claim`s and `Validation`s; the eval-forgery guard reuses `provenance.query_replay_trace` (`artifact.provenance`, File 09 §15.3) to verify evidence. This file introduces no parallel result block and no parallel provenance query.

### 2.3 With File 04 (Execution and Run Model)

An `EvalRun` is a `Run`. File 04 owns the run lifecycle, the `RunCompletionContract` and the completion-forgery guard, child-run orchestration and merge, the comparison-run shapes, budgets, and recovery. This file owns the evaluation semantics layered over them: which fixtures become which child runs, what each run is scored against, and how case results aggregate. The eval-forgery guard (§7.6) is the offline analog of `run.termination` (File 04 §22)'s completion-forgery guard and reuses the same ledger-boundary rejection (`ledger.forgery-guards`, File 10 §3.7); this file adds no new guard mechanism. A best-of-N, arena, or tournament comparison evaluation uses the comparison-run shapes `run.child-runs-multi-agent-work` (File 04 §16.1) already names and the `ModelSelectionPlan` `model.multi-model-selection-plans` (File 16 §13) already defines; this file specifies the evaluation reading of those shapes.

### 2.4 With Files 10 and 11 (Ledger/Events/Hooks; Version Graph/Replay)

File 10 owns the ledger, the event stream and envelope, the `LedgerEntryKind` catalogue, and the custom-kind registration mechanism; it assigns the replay-engine realization to this file (`ledger.replay-semantics`, File 10 §11.6). File 11 owns the version graph, the `VersionDiff` and `diff_hash`/`expected_view_hash` golden-comparison primitives (`version.version-diff`, File 11 §4), the replay modes and the `replay.*` capabilities (`version.replay-semantics`, File 11 §15.6), the `ReplayRun` record, and the version-graph-backed projection contract (`version.version-graph-backed-projections`, File 11 §16). This file consumes all of those. It registers its events as `Custom { namespace: "evaluation" }` (no evaluation kind is in the canonical catalogue per `ledger.entry-kind-catalogue`, File 10 §4.1); it computes golden comparisons over `diff_hash`; it invokes `replay.*` and records `ReplayRun`s; and it declares its score and report views as version-graph-backed projections.

### 2.5 With File 16 and File 17 (Model Strategy; Provider Layer)

`model.consequences-for-later-specs` (File 16 §16) directs this file to "measure model-selection correctness, fallback correctness, cost prediction, cache effectiveness, data-boundary filtering, and role-specific model quality using `ModelSelectionRecord`s as primary artifacts." This file discharges that as the `ModelSelection` family (§8). `provider.token-source` (File 17) and `TokenUsageRecord`/`PricingSnapshot` (File 17 §"usage accounting") are the primary artifacts of the `Cost` family. A model-comparison evaluation that re-runs a fixture against a different model (`FullRerun` over a recorded run with a new model profile, the central "re-run this dataset against a new model and compare" use case of `ledger.replay-semantics`, File 10 §11.1) reselects the model through File 16 and records a new `ModelSelectionRecord`. This file reads those records; it never re-derives a historical cost or token count from a live endpoint (`provider.token-source`).

### 2.6 With File 33 and File 34 (Automation and Triggers; Workflows)

The 40↔33 seam mirrors the 33↔34 seam: File 33 owns the trigger binding, this file owns the suite body. A scheduled or event-triggered regression run is an `Automation` (File 33) whose pinned `RunIntent` runs an `EvalSuite`; File 33 owns the trigger, the arming gate, and the non-interactive safety posture, and this file owns the suite that runs. The 40↔34 seam: File 34 owns the `Workflow` body and its declared reliability metadata; this file owns the reliability harness that consumes that metadata (`workflow` reliability is "derived from its run history ... and evaluated by File 40's harness, which this file's reliability metadata feeds" — File 34 §"validation/simulation/reliability"). A workflow- or automation-completion evaluation is the `Reliability` family (§8).

### 2.7 With File 41 (Telemetry, Logging, and Observability)

The 40↔41 seam is fixed: this file owns the **offline** layer that runs suites, benchmarks, and judge optimizations and produces evaluation results; File 41 owns the **live** layer that observes execution and computes metric projections (validator-accuracy, false-positive rate, latency distribution, pass-rate aggregates over windows — the metric sources `qc.events-metrics` (File 39 §17.2) names). Both consume the same ledger and events; neither introduces a parallel store. The live metrics the telemetry spec computes are inputs an evaluation may consume (a latency-regression suite reads recorded latency facts); the offline scores this file computes are data the telemetry spec may surface. The Observatory surface (run comparisons, evaluation-suite results, traces, latency/cost metrics) is rendered by File 37; its evaluation data is owned by this file, its live-metric data by the telemetry spec, and its version-graph replay by File 11.

### 2.8 With the per-surface, plugin, and extension specs

Each surface and subsystem registers its owned scorers (validators) through the one registration path (`qc.validator-registration`, File 39 §10) and declares the family its work belongs to and the primary artifact that family scores. This file declares the closed family set and the canonical evaluation object model the surfaces' suites consume; the surfaces specialize. No surface owns a private evaluation pipeline. A plugin contributes scorers, fixtures, and suites through the plugin contribution path (File 35) under source approval and trust narrowing, and may seed per-profile evaluation defaults; agent-generated extensions may be required to pass an evaluation before installation (§10.4). Plugin, MCP, API, and user-defined suites and scorers carry source attribution into reports and gates. Low-trust sources may advise by default, but they cannot satisfy a high-trust installation, graduation, or promotion gate unless the gate policy explicitly accepts that source class. A plugin-supplied suite cannot be the sole gate for installing or upgrading the same plugin without an explicit circular-provenance warning and user approval.

### 2.9 Boundary

This file is the offline evaluation-orchestration layer. It owns no result-block schema, no validator primitive or validation gate, no run lifecycle, no replay capability declarations or version-diff primitives, no model-selection or cost records, no live-metric projection, no storage schema, and no UI rendering. It owns the `EvalSuite`/`EvalCase`/`EvalRun` object model, the fixture and golden-comparison contracts, the scorer-and-verdict aggregation, the family set and primary-artifact map, the comparison and regression contracts, the judge-optimization pipeline and annotation queue, the evaluation capability surface, and the evaluation-gated-evolution posture.

## 3. The `EvalSuite`

Anchor: `eval.eval-suite`

### 3.1 Definition

An `EvalSuite` is a versioned, parameterized, named definition that binds a fixture set to scorers, golden artifacts or expected properties, a pinned policy and model-profile configuration, success criteria, and a regression baseline. It is the canonical unit of offline evaluation: the durable answer to "run this set of cases under this configuration and tell me how the system does."

An `EvalSuite` is not:

- an `EvalRun` — the suite is the definition; the run is one recorded execution of it at a pinned configuration
- a `Validator` — a validator is one inline checking rule; a suite is a collection of scorers (validators run offline plus golden comparators) over a fixture set
- a `Workflow` — a workflow is a reusable body of multi-step work; a suite measures the system, and may itself run as a `Run`, but is not exposed as an operation
- a parallel test runner or scheduler — a suite executes as a `Run`; there is no separate evaluation runtime

### 3.2 Required Properties

Every `EvalSuite` declaration carries at minimum:

- `suite_id` — a stable, namespaced identifier
- `version` — the suite's version; revisions are non-destructive siblings in the version graph (`core.non-destructive-by-default`, File 01 §7.13; `version.version-diff`, File 11 §4)
- `source` — the typed source (`Builtin`, `Subsystem`, `Plugin`, `McpServer`, `Api`, `UserDefined`; per `capability.capability-source`, File 05 §9.1)
- `family` — the `EvalFamily` (§8) the suite measures; a suite measures one family or declares `CrossFamily`
- `cases` — the set of `EvalCase`s (§4), or a query that resolves to a case set (a recorded-run selector, a sampled set, an annotated dataset)
- `scorers` — the `Scorer` set (§6) applied to each case's output: validators run offline and golden comparators
- `replay_mode` — the default replay mode for recorded-run cases (`Inspect`, `SimulateDeterministic`, or `FullRerun`; §7.2), overridable per case
- `pinned_configuration` — the configuration under test: a pinned `ModelProfile` set, policy profile, capability revision set, prompt/instruction revision, and retrieval/context configuration where the family varies them; the configuration the suite holds fixed so that a change to one dimension is measurable in isolation
- `success_criteria` — the typed thresholds a run must meet to be reported as passing (a minimum pass rate per scorer, a maximum regression delta, a latency or cost ceiling); success criteria are declarative and inspectable, never prose-only
- `regression_baseline` — the pinned prior `EvalRun` against which a new run is compared (§10), or `None` for an unbaselined suite
- `sampling` — the trigger-independent sampling policy over the case set (`EveryCase` for a regression suite, `Sampled { fraction }` for a cheap monitoring suite, `DeepDive { fraction }` for an expensive sampled deep-dive; §14), defaulting to `EveryCase`
- `budget` — the run and per-stage budgets (`run.budgets-limits`, File 04 §21) and the cost-preview policy (§14)
- `settings` references — the scoped enablement and threshold configuration resolved through the canonical settings stack (§17)

A declaration lacking any required field is invalid unless that field is explicitly nullable or default-resolved by this contract. `regression_baseline` may be `None`; `sampling` may resolve to the declared default but the resolved value is recorded on the run; a report-only suite declares typed report-only success criteria instead of omitting criteria. Silent absence of required fields is invalid.

### 3.3 The Suite Is a Definition, Not a Result

An `EvalSuite` carries no scores. Scores live on the `EvalRun` (as `Validation`/`Critique` blocks) and in the derived `EvalScore` projection. The suite is fixed at a version; changing a fixture, a scorer, the pinned configuration, or a success criterion commits a new suite version (a sibling), preserving the prior version so that a historical `EvalRun` keeps resolving against the suite version it ran. This mirrors the immutable-diff rule of `version.version-diff` (File 11 §4.2): a historical run reading a prior suite version reproduces the historical evaluation; the new suite version becomes current going forward.

### 3.4 Sourcing and Versioning

Built-in suites ship as built-in definitions registered at startup. Subsystem and surface suites register when the owning subsystem loads. Plugin suites register through the plugin contribution path (File 35) under source approval and trust narrowing. User-authored suites register through an evaluation-registration capability (§15). The agent may draft and propose a suite; it may never self-install one without user approval. A suite's library governance — discovery, scoping (project, workspace, user, plugin, built-in), layered precedence, and export/import — reuses the reusable-unit governance shape established by `workflow.library` (File 34 §9) and the settings layering of `settings.profiles` (File 15 §7); this file does not invent a parallel library.

### 3.5 Boundary

The suite declaration defines what to measure and how. The replay engine runs the cases (§7). The scorers produce the verdicts (§6). The version graph holds the suite versions (File 11). The settings stack resolves enablement and thresholds (File 15). None of those layers invents new evaluation semantics; they consume what this file defines.

## 4. `EvalCase` and Fixtures

Anchor: `eval.eval-case-fixtures`

### 4.1 `EvalCase`

An `EvalCase` is one fixture plus its expected outcome and the scorers that apply to it. Required fields: `case_id`, the `fixture` (§4.2), the `expected` outcome (a golden artifact reference, a set of expected properties, or both; §5), the `applicable_scorers` (a subset of the suite's scorers, or all), and an optional `case_weight` and `tags` (the error-mode or difficulty labels used for grouping and Pareto-aware selection; §11). A case's `expected` outcome may be empty when the case is scored only by intrinsic property assertions (a "the output must be valid JSON and tests must pass" case needs no golden reference).

### 4.2 The Fixture Model

A fixture is the pinned input an evaluation runs against. The closed canonical fixture set:

- `RecordedRunFixture` — a pinned reference to a past `Run`'s ledgered scope and durable snapshots: the run's ledger entries (`ledger.replay-semantics`, File 10 §11.2), the referenced blocks and entities, the `AssemblySnapshot`s (`context.assembly-replay-snapshot`, File 13 §19), the registry/settings/policy/world snapshots, and the observation staleness fingerprints. A recorded-run fixture is what an evaluation replays.
- `SyntheticFixture` — a typed, pinned input bundle authored for evaluation: a triggering input plus a pinned world/settings/policy/model-profile snapshot sufficient to run it deterministically. A synthetic fixture has no prior run; it is executed fresh under the suite's pinned configuration.

A fixture is immutable and content-addressed where it carries content (`core.canonical-hash`, File 01 §7.14). A `RecordedRunFixture` references durable substrate rather than copying it; it never duplicates the ledger or block pool. A fixture set may be a curated list, a query over recorded runs (by family, by failure, by surface, by recorded sequence or other event-derived selector), or an annotated dataset (§12).

### 4.3 The Determinism Contract

Evaluation re-derives nothing from live mutable sources. This is the load-bearing invariant repeated across the substrate specs (`context.assembly-replay-snapshot`, File 13 §19; File 20 §"consequences" — "the Evaluation and Benchmarking spec reads the durable substrate and replays over the recorded snapshots this file reconstructs; it re-derives nothing from live mutable sources"; and the "replays over recorded snapshots and immutable references, not live state" clauses of Files 21, 24, 25, 27, 32, 36). Concretely:

- a `RecordedRunFixture` is replayed from its recorded `AssemblySnapshot`s and immutable references; live retrieval, memory, world model, and token-counting endpoints are not consulted during a deterministic replay
- a model-mediated scorer reproduces its recorded verdict on replay rather than re-invoking the model (`qc.persistence-replay`, File 39 §10.5/§19; `provider.token-source`, File 17)
- a `FullRerun` (§7.2) that deliberately re-executes against replay-time state is the explicit exception: it produces a new run and is the mechanism for the "re-run this dataset against a new model and compare" use case; its observable side effects route through replay-time policy and default to isolated destinations (sandbox, worktree, browser profile, artifact branch, or evaluation conversation scope) unless policy and typed confirmation allow writing to an original or external resource

### 4.4 Fixtures Are Not a Parallel Store

A `RecordedRunFixture` is a reference into the one ledger, block pool, version graph, and snapshot substrate; a `SyntheticFixture` is a pinned typed bundle persisted as ordinary blocks. There is no parallel fixture database. Large fixture content (a captured screenshot series, a large dataset) uses `External` block content (`block.block-content`, File 08 §4) like any other large artifact. A `RecordedRunFixture`, and any suite, baseline, or regression report that depends on it, places a retention hold on the ledger scopes, blocks, snapshots, blobs, and version references it needs for replay. If a referenced substrate is unavailable, the fixture is marked unreplayable with a typed dangling-reference diagnostic and is never scored against partial data.

### 4.5 Boundary

The fixture model defines what an evaluation runs against. The replay engine resolves and replays it (§7). The snapshot resolution and immutable references are owned by Files 10, 11, and 13. This file specifies the fixture taxonomy and the determinism contract.

## 5. Golden Artifacts and Expected Properties

Anchor: `eval.golden-comparison`

### 5.1 Principle

An evaluation decides whether a produced output is acceptable by comparing it against an expectation. The expectation is a golden artifact (a known-good reference output), a set of expected properties (declarative assertions the output must satisfy), or both. The system ships the comparison machinery, not a universal "is this output right" comparator; the expectation is authored per case.

### 5.2 The `GoldenComparison` Taxonomy

`GoldenComparison` is a closed canonical set naming how a produced output is compared against its expectation:

- `ExactMatch` — the produced output's canonical-encoding hash equals the golden artifact's hash (`version.diff-hash`, File 11 §4.5; `block.content-hash`, File 08; `version.expected-view-hash`, File 11 §7.6). Used where the output is deterministic and a byte-for-byte match is meaningful (a serialized structured object, a generated file under a deterministic generator). The hash is computed over a declared `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14), never over physical storage bytes.
- `StructuralDiff` — a typed `VersionDiff` (`version.version-diff`, File 11 §4) between the produced version and the golden version, reporting added, removed, and modified elements. Used where an exact match is too strict but the structural shape must match (a code patch touching the same regions, a document with the same sections). The comparison passes only under a machine-parseable `allowed_diff_contract` declaring allowed regions, ignored fields, normalization rules, order tolerance, and forbidden additions or removals. Without an explicit contract, structural comparison defaults to exact structural equality.
- `PropertyAssertion` — the produced output must satisfy a set of declared expected properties, each expressed as a `Validator` producing a `Validation` (a "tests pass" `Test` validation, a "claim X is grounded to source span Y" `CitationCheck`, a "schema conforms" `SchemaValidation`, a "every font size is within 0.5×–5× of the body size" property check). Property assertions are the default and most robust comparison: they tolerate legitimate variation while pinning what must hold.
- `SemanticEquivalence` — a `ModelMediated` judge verdict that the produced output is semantically equivalent to (or as good as) the golden artifact, under the judge discipline (`qc.judge-discipline`, File 39 §6): narrow, binary or small-closed-set verdict, with reasoning, context-isolated, provider-agnostic. Used only where no deterministic comparison expresses the concern.

### 5.3 Cheap-Deterministic-First Ordering

Where a comparison admits both a deterministic form and a model-mediated form, the deterministic form is preferred, mirroring the cheap-deterministic-first rule of `qc.validation-kind-taxonomy` (File 39 §5.4). The ordering is `ExactMatch` → `StructuralDiff` → `PropertyAssertion` → `SemanticEquivalence`: a suite uses the cheapest comparison sufficient to express its concern, and reserves the model-mediated `SemanticEquivalence` for the residue that no deterministic comparison captures. A `SemanticEquivalence` comparison records its replay key (`qc.persistence-replay`, File 39 §10.5) so that historical reconstruction reads the recorded verdict.

### 5.4 Golden Artifacts Are Pinned Artifact Versions

A golden artifact is a pinned `ArtifactVersion` (`artifact.version-creation`, File 09 §6.3) — a normal, durable, versioned artifact designated as a reference. Expected properties are `Claim`s and `Validation`s (File 09). Designating, updating, or retiring a golden artifact is a versioned, audit-visible operation; updating a golden creates a new suite version (§3.3) so that historical runs keep comparing against the golden they used. A golden artifact is never silently regenerated; a "accept the new output as the golden" operation is an explicit, recorded user action.

### 5.5 Boundary

The golden artifacts, the version diffs, and the validator results are owned by Files 09 and 11. This file specifies the comparison taxonomy, the cheap-deterministic-first ordering, and the golden-versioning rule. The rendering of a golden comparison (a side-by-side diff, a property checklist) is owned by Files 37 and 38.

## 6. `Scorer` and the Verdict-and-Score Model

Anchor: `eval.scorer-verdict-model`

### 6.1 The `Scorer`

A `Scorer` is what produces a per-case verdict. A scorer is one of:

- a `Validator` (`qc.validator`, File 39 §3) run offline over the case's recorded or freshly-produced output — `Deterministic` (a registered capability computing a verdict), `ModelMediated` (a judge under the judge discipline), or `UserManual` (a human reviewer)
- a deterministic golden comparator (§5.2 `ExactMatch`, `StructuralDiff`, or `PropertyAssertion`)

A scorer is not a net-new primitive: a validator scorer is exactly File 39's `Validator` invoked offline; a golden comparator is a deterministic capability over the version graph. This file adds no parallel scorer registry; the scorer set of a suite is a selection of registered validators plus declared golden comparators.

Each suite-level scorer binding declares a role: `Required`, `Advisory`, or `Informational`. `Required` scorers participate in the case and suite pass/fail derivation. `Advisory` scorers surface findings and may be referenced by explicit success criteria, but do not affect pass/fail unless the criteria say so. `Informational` scorers feed reports and leaderboards only. The role is resolved before execution and recorded on the `EvalRun` so historical reports remain stable.

### 6.2 The Per-Case Verdict Is Binary or Small-Closed-Set, With Reasoning

A per-case verdict is a `ValidationOutcome` (`Passed`/`Failed`/`Inconclusive`; `artifact.validation-critique`, File 09 §14.1), or, for a scorer whose verdict is multi-class, a small mutually-exclusive closed enum declared on the scorer. A per-case verdict is never a one-to-five or zero-to-one numerical score (the rule of `qc.judge-discipline`, File 39 §6.2, applied to offline scoring). A model-mediated scorer records its verdict and its reasoning; the reasoning is required for transparency, for user adjudication, and for the judge-optimization loop that learns the implicit policy from annotated examples (§11). An optional numerical `confidence` may accompany a verdict for ranking and thresholding, but confidence is not the verdict.

### 6.3 Continuous Figures Are Aggregates

The continuous quality figures evaluation reports — pass rate, accuracy, win rate, regression delta, latency distribution, cost figure — are downstream aggregates computed by the `EvalScore` projection (§13) over many binary or small-closed-set per-case verdicts, never per-case scores. Aggregate scoring models that the source material uses — win rate (a routing-comparison ratio), Elo or Bradley-Terry rankings (an arena projection over many pairwise outcomes), and item-response-theory difficulty or ability estimates (a calibration projection over many graded responses) — are computed downstream over the binary outcomes; they are aggregate projections, never per-case verdicts. A per-interaction one-to-five score surfaced as the verdict is an Explicit Rejection (§19).

### 6.4 Scorer Chain and Coverage

For a case, every applicable scorer either produces a verdict or an explicit diagnostic explaining why it did not run (`NotApplicable`, `BudgetExceeded`, `DisabledBySetting`, `BackendUnavailable`). A report must never imply that a skipped scorer passed (the rule of `qc.validation-gate`, File 39 §8.4, applied to offline scoring). A case's aggregate outcome is derived from the resolved scorer roles: the case `Passed` only when every applicable `Required` scorer `Passed`; a `Failed` required scorer makes the case `Failed`; an `Inconclusive` required scorer makes the case `NeedsReview`. `Advisory`, `Informational`, skipped, inapplicable, budget-dropped, and backend-unavailable scorer results remain visible and counted separately in coverage.

### 6.5 Boundary

The validators and their results are owned by File 39 and File 09. This file specifies the scorer composition, the binary-not-continuous verdict rule applied offline, the aggregate-figures-are-projections rule, and the coverage rule.

## 7. `EvalRun` and the Replay Engine

Anchor: `eval.eval-run-replay`

### 7.1 Definition

An `EvalRun` is the recorded execution of an `EvalSuite` at a pinned configuration over its cases. It is a `Run` (`run.run`, File 04 §2): it is created from a `RunIntent`, it fans out one child run per case (`run.child-runs-multi-agent-work`, File 04 §16), it records its lifecycle and outputs through the ledger and event substrate, and it terminates under a `RunCompletionContract` (`run.completion-contract`, File 04 §2.7). An `EvalRun` records the `suite_id` and suite version; the pinned configuration actually used (the resolved `ModelProfile` set, policy profile, capability revision set, prompt/instruction revision, and retrieval/context configuration); the replay mode; the per-case `ReplayRun` references; the produced artifacts; the derived `EvalScore` projection reference; and the `RegressionReport` reference where a baseline exists.

### 7.2 Replay Modes

An `EvalRun` runs each case in one of the three closed replay modes (`ledger.replay-semantics`, File 10 §11.4; `version.replay-semantics`, File 11 §15), consumed from Files 10 and 11, never redefined:

- `Inspect` — read-only forensic reconstruction of a recorded run; the case is scored over the recorded outputs without re-execution. Used for scoring a recorded run against expected properties or against a golden artifact when the run's outputs are already recorded.
- `SimulateDeterministic` — re-executes the `deterministic_replayable` and `snapshot_replayable` capabilities (`capability.replay-class`, File 05 §7.3) against the recorded inputs and snapshots, skipping `effect_replayable_with_policy` and `not_replayable`. Used to test that the system produces the same output given the same inputs, and to detect non-determinism or a behavior change in a deterministic path. Divergence in a deterministic-declared path records a typed determinism-violation finding attributable to the misdeclared capability, replay class, snapshot, or deterministic substrate, distinct from an output-quality failure.
- `FullRerun` — re-executes the case from its inputs against replay-time state, producing a new run. Outputs default to isolated evaluation destinations: a worktree, sandbox, browser profile, artifact branch, or evaluation conversation scope. Writes to the original source, an external service, or a non-evaluation destination require the replay-time policy and typed confirmation File 11 requires. Used for the central comparison use case: re-run a recorded run (or a synthetic fixture) under a new model profile, prompt, policy, or capability revision and compare the new output against the recorded baseline or the golden artifact.

A replayed case produces a `ReplayRun` (`ledger.replay-semantics`, File 10 §11.4; `version.replay-semantics`, File 11 §15.5) referencing the source run via `replay_source_run_id`; the `EvalRun` aggregates the `ReplayRun`s and their scores. A `SyntheticFixture` case has no source run and is always executed fresh (the synthetic-fixture analog of `FullRerun`).

### 7.3 The Replay Engine

The replay-engine realization — resolving a fixture's references, reconstructing the recorded context (`context.assembly-replay-snapshot`, File 13 §19), re-executing per replay class and replay mode, and producing the comparison inputs — is owned by this file (`ledger.replay-semantics`, File 10 §11.6 assigns it here). The engine invokes the `replay.inspect`/`replay.simulate_deterministic`/`replay.full_rerun` capabilities (`version.replay-semantics`, File 11 §15.6) at their declared tiers (`ReadOnly`, `WorkspaceWrite`, and `UserApproval`-with-typed-confirmation respectively). The engine alters no durable substrate of the source run; new runs commit to new substrate per the standard pipeline (`version.replay-semantics`, File 11 §15.7).

### 7.4 Fan-Out, Parallelism, and Ordering

An `EvalRun` runs its cases as child runs under the canonical parallelism rules (`run.parallelism`, File 04 §15). Cases are parallel-eligible only after the normal conflict analysis over resolved touched resources, isolation scopes, side-effect class, model/provider budgets, and replay mode (Files 04, 05, and 06). Isolated cases may run concurrently (for example a fresh worktree for a coding case, an isolated browser profile for a web case, a sandboxed process group for a shell case); cases that share exclusive resources serialize. Failure in one case does not abort siblings unless the suite declares otherwise (`run.failure-in-parallel-work`, File 04 §15.3). The engine preserves stable case ordering even when cases finish out of order. Concurrency is bounded by the run's concurrency caps and budget (§14), not by a parallel evaluation queue.

### 7.5 Replay of the Evaluation Itself

An `EvalRun` over recorded inputs is itself deterministic and replayable: replaying the same recorded fixtures under the same pinned configuration reproduces the same per-case verdicts and the same aggregate scores, modulo explicitly-typed model-mediated nondeterminism that is recorded rather than re-derived (`qc.persistence-replay`, File 39 §19.4). A replay-equivalence property holds for the evaluation: re-running a recorded `EvalRun` reproduces its outcomes modulo recorded model-mediated nondeterminism. Wherever a golden comparison or a fixture identity depends on a hash, the hash is computed over a declared `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14); this file defines no new hash and reuses the block, version-diff, and ledger hashes of Files 08, 10, and 11.

### 7.6 The Eval-Forgery Guard

An `EvalRun` cannot record a case as `Passed` without the ledgered evidence its scorers require. A scored pass is rejected at the ledger boundary when:

- a scorer's `Validation` block does not exist or does not reference the actual produced output (the offline analog of the completion-forgery guard of `run.termination`, File 04 §22 and `ledger.forgery-guards`, File 10 §3.7, reusing the same rejection mechanism)
- a golden comparison records a pass without referencing the actual produced artifact version and the golden version it compared against
- a model-mediated scorer records a verdict without its replay key (`qc.persistence-replay`, File 39 §10.5)
- a `FullRerun` case records a pass with no execution evidence (no recorded capability executions, no committed outputs, no model-step outputs beyond plain text) when its scorers required produced action — mirroring the empty-trace, zero-blast-radius, no-recorded-outcome forgery patterns

Every scorer declared on a case must produce a verdict or an explicit skipped diagnostic; coverage is required (§6.4). A run whose recorded passes are not backed by evidence is an integrity violation, surfaced and not silently accepted.

### 7.7 Boundary

The run lifecycle, child-run orchestration, budgets, and the completion-forgery guard are owned by File 04. The replay modes, capabilities, and `ReplayRun` record are owned by Files 10 and 11. This file owns the replay-engine realization, the eval-run record, the fan-out reading of child runs, the replay-of-the-evaluation determinism contract, and the eval-forgery guard.

## 8. Eval Families and Primary Artifacts

Anchor: `eval.eval-families`

### 8.1 Definition

An `EvalFamily` classifies an evaluation by the system dimension it measures. Each family declares its **primary artifact** — the recorded object an evaluation of that family scores. The family classification drives which scorers and golden comparisons are meaningful and which recorded snapshots the fixtures reference. The family set is closed for interoperability (`core.closed-canonical`, File 01 §6.16) with a `Custom` extension.

### 8.2 The Closed Family Set and Primary Artifacts

- `Routing` — primary artifact: the route record (`RouteRecordCommitted` / `RoutingFrameComposed`; `routing.route-record`, File 03 §3.5). Discharges File 03 §"consequences" ("evaluation specs must include routing-evals as a first-class evaluation family, with the route record as the eval artefact"): given a recorded input, did the router produce the expected `RunIntent`?
- `ModelSelection` — primary artifact: the `ModelSelectionRecord` (`model.model-selection-record`, File 16 §8). Discharges `model.consequences-for-later-specs` (File 16 §16): model-selection correctness, fallback correctness, cost prediction, cache effectiveness, data-boundary filtering, and role-specific model quality.
- `Retrieval` — primary artifact: the normalized `RetrievalHit` set (`retrieval.retrieval-result`, File 12 §9). Retrieval relevance, ranking quality, and grounding-of-retrieved-context.
- `Context` — primary artifact: the `AssemblySnapshot` and `BudgetReport` (`context.assembly-replay-snapshot`, File 13 §19; §9). Discharges File 13 §"consequences" (context correctness, continuity preservation, duplicate handling, overflow recovery, cache effectiveness, compaction quality).
- `Memory` — primary artifact: the memory entries and the `MemoryHit` set. Discharges File 14 §"consequences" (memory extraction accuracy, false-memory rate, retrieval relevance, source attribution, conflict handling, expiration behavior, consolidation quality, natural-but-inspectable use).
- `Coding` — primary artifact: the code-artifact `ArtifactVersion` and the `Test`, `Lint`, and coder build (`Custom { namespace: "coder" }`) validations. Discharges File 27 §"consequences" (the edit-to-artifact-revision-to-materialization-to-external-edit-to-version round-trip, code-search retrieval, the test-and-validation gate, revert-as-version-switch, worktree-backed multi-agent merge, session-export projection).
- `Research` — primary artifact: the research output `Artifact` with its `Claim`/`Evidence`/`Citation` set. Research-synthesis quality, citation grounding, source quality.
- `Perception` — primary artifact: the `Observation` (accessibility-tree snapshot, screenshot, grounded extraction) and the perception confidence. GUI/desktop/web perception and grounding accuracy.
- `Reliability` — primary artifact: the run history and the `Workflow`/`Automation` reliability metadata (File 34's reliability metadata; File 33's run history). Discharges File 34 §"consequences" (the workflow-reliability harness — success rate, recurring failure modes, cost profile) and the automation/workflow completion-success families. Workflow-completion and automation-completion are scored against the `RunCompletionContract` and the declared validations.
- `PolicyRegression` — primary artifact: the policy decision records (`PolicyDecisionMade`, lease lifecycle, `permission_floor` events; File 06). Did a policy change improve safety without breaking flow; did a previously-approved action stay approved and a previously-denied action stay denied?
- `Latency` — primary artifact: the recorded timing facts (per-call latency, time-to-first-token, end-to-end run duration, rendered-interaction timing for UI surfaces). Latency and resource-budget regressions against declared targets. Heavy graph-like panels — block graphs, workflow DAGs, run trees, inspectors, node canvases, and equivalent large interactive visualizations — are measured here through ordinary `EvalSuite`s with per-OS success criteria. They do not create a new evaluation primitive or a canonical renderer-library commitment; the renderer is selected per surface behind the `RendererRegistry` based on recorded performance, accessibility, interaction, export, and debugging evidence.
- `Cost` — primary artifact: the `TokenUsageRecord` and `PricingSnapshot` (File 17). Discharges File 17 §"consequences" (cost-correctness, cache-effectiveness, tokenizer-accuracy measurements).
- `ToolUse` — primary artifact: the `ToolSurface` snapshot and the tool-search/borrow/invocation trace (`surface.surface-relevant-events`, File 07 §13). Discharges File 07 §"consequences" (tool-use efficiency; replay reconstructs the exact surface a past invocation saw).
- `Surface` — primary artifact: the `SurfaceContract` activation and composition records (`worksurface.*`, File 25). Discharges File 25 §"consequences" (surface activation, cross-surface composition, the no-private-architecture invariant, the morphing-as-projection round-trip).
- `ControlRail` — primary artifact: the `RailResolution` records (`controlrail.*`, File 26). Discharges File 26 §"consequences" (rail-resolution correctness: gesture → expected `RailResolution`).
- `Portability` — primary artifact: the `PortablePackage` and the workspace materialization records (File 21; File 24). Discharges File 21 §"consequences" (package export/import round-trip, import idempotence, interruption safety, tamper rejection, additive sync safety, causal settings conflicts, restore staging, golden canonical-encoding fixtures for package hashes, replay equivalence) and File 24 §"consequences" (the materialization round-trip, relocation re-resolution, the worktree create/merge/discard/quarantine lifecycle, the export/import workspace round-trip).
- `Connector` — primary artifact: the connector contract and the recorded invocation-plus-descriptor snapshot (`mcp.*`/`connector.*`, File 36). Discharges File 36 §"consequences" (a remote schema change is a version increment, reconnection preserves identity, an external call passes egress governance, an inbound payload holds no authority, a connector operation replays from recorded snapshots).
- `Plugin` — primary artifact: the plugin's contributed records (File 35). Discharges File 35 §"consequences" (the reliability evaluation a plugin's contributions feed).
- `Safety` — primary artifact: the `SafetyCheck` validations and the security-primitive outcomes (File 22 wrapped as validators per `qc.boundaries-with-adjacent-layers`, File 39 §2.7). Content-safety and injection-defense quality, scored offline.
- `UX` — primary artifacts: the customization events, the structural-understanding projection, the generated shipped-copy catalogue, and the copy-override resolution records (File 38; File 37). Discharges File 38 §"consequences" and the UX-level interaction evals for critical surfaces; consumes the events with no parallel customization store. Its clean-baseline localization suites pin a configuration with the copy-override layer disabled and evaluate shipped-catalogue completeness and product-language conformance against it; separate cases cover exact-locale override resolution, per-key fall-through, causal reset, typed conflicts, and the protected semantic companion.
- `CrossFamily` — a suite spanning more than one family, declaring its primary artifacts per case.
- `Custom { namespace, name }` — a specialized family registered through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2). Registration declares the owner/source, primary artifact reference type, default scorer bindings, expected fixture kinds, report dimensions, event names where any are emitted, and sensitivity and retention defaults. A custom family gets no private pipeline or result carrier.

### 8.3 Families Are Suite Configurations, Not Pipelines

A family is a classification and a primary-artifact map, not a parallel pipeline. Every family's evaluations run as `EvalRun`s over the shared substrate, score with `Validator`s, and compare against golden artifacts. The round-trip and reproducibility verifications that the substrate specs defer here (materialization, sync export/import, connector replay, surface morphing) are realized as cases within the relevant family, each consuming the owning spec's recorded snapshots and immutable references, never live state (§4.3). No family introduces a private evaluation runtime.

### 8.4 Boundary

The primary artifacts are owned by their producing specs. This file declares the family set, the primary-artifact map, and the rule that families are suite configurations. The owning specs register their family scorers through File 39's path and may ship built-in suites for their family.

## 9. Comparison Evaluations

Anchor: `eval.comparison-evals`

### 9.1 Definition

A comparison evaluation runs the same fixtures under two or more configurations (the **arms** — different model profiles, prompts, policies, capability revisions, or routing strategies) and produces a typed comparison: a per-case relative verdict and an aggregate comparison figure. Comparison is the mechanism behind "did this change improve or harm" and "which of these models/prompts/strategies is better."

### 9.2 Comparison Shapes

Comparison evaluations use the canonical comparison-run shapes (`run.child-runs-multi-agent-work`, File 04 §16.1) and the `ModelSelectionPlan` (`model.multi-model-selection-plans`, File 16 §13); this file specifies their evaluation reading:

- **A/B (paired)** — two arms over the same fixture set; the per-case relative verdict is the delta between the two arms' per-case outcomes (improved / unchanged / regressed), and the aggregate is the win/tie/loss distribution.
- **Best-of-N** — N arms (or N samples of one configuration) over each fixture; a selector child run picks the best per case under declared criteria. Used to evaluate the quality ceiling of a configuration and to select among candidate outputs.
- **Arena** — many arms compared pairwise across a fixture set; the aggregate is a ranking projection (an Elo or Bradley-Terry ranking over the pairwise outcomes; §13). A leaderboard is the rendered projection.
- **Tournament-pairwise** — pairwise comparisons advancing a winner per fixture until one arm remains, for selecting a single best arm with fewer total comparisons than full arena.

### 9.3 The Blind-Comparator Discipline

A pairwise relative verdict produced by a `ModelMediated` judge is blind: the judge receives the two outputs without knowing which arm produced which, and the arm-to-label assignment is randomized per comparison and recorded. The judge receives only the blinded outputs, the comparison criterion, the validation-relevant evidence or source excerpts, and the typed references required for the comparison. It does not receive arm identity, model, profile, provider, prompt, source, or execution metadata unless the evaluated dimension explicitly requires that metadata. Blindness removes position and source bias from the comparison. The pairwise judge follows the judge discipline (`qc.judge-discipline`, File 39 §6): a binary or small-closed-set verdict (`first` / `second` / `tie`), with reasoning; narrow (one comparison dimension per judge where the concern decomposes); context-isolated; provider-agnostic. A deterministic comparison (a metric delta, a golden-comparison difference) is preferred over a judge where one expresses the concern (cheap-deterministic-first, §5.3). The assignment seed and output order are recorded, and positions are balanced where possible.

### 9.4 Aggregates and Determinism

The comparison aggregate — win rate, win/tie/loss distribution, ranking, regression delta — is an `EvalScore` projection (§13) over the per-case relative verdicts, never a per-case continuous score (§6.3). A comparison evaluation is replayable: the recorded per-case relative verdicts (including the recorded blind label assignment and the model-mediated judge's recorded verdict and replay key) reproduce the aggregate on replay (§7.5).

### 9.5 Boundary

The comparison-run shapes and the multi-model selection plan are owned by Files 04 and 16. This file specifies the comparison evaluation semantics — the arms, the relative verdict, the blind-comparator discipline, and the aggregate-as-projection rule.

## 10. Regression Detection and Evaluation-Gated Evolution

Anchor: `eval.regression-gated-evolution`

### 10.1 The Regression Baseline

A suite carries a `RegressionBaseline`: a pinned prior `EvalRun` against which a new run is compared. The baseline is set explicitly (an `EvalRun` the user accepts as the reference) and is itself a versioned, audit-visible designation. A suite without a baseline reports absolute scores; a suite with a baseline additionally reports a regression comparison. A baseline is compatible only with the same suite version or with a declared compatibility or migration relation. Changes to scorer identity or role, case weight, expected properties, golden artifact version, or success criteria make older baselines stale unless an explicit compatibility relation says otherwise. A stale baseline remains inspectable but cannot gate a change.

### 10.2 The `RegressionReport`

A new `EvalRun` against a baselined suite computes a `RegressionReport`: per-case and per-scorer deltas versus the baseline, classified as `Improved`, `Unchanged`, or `Regressed`, plus the aggregate regression figure (the net pass-rate delta, the set of newly-failing cases, the set of newly-passing cases). The report is a projection over the new run's verdicts and the baseline run's recorded verdicts (`core.projection`, File 01 §6.11). A regression that crosses a declared threshold (a suite `success_criteria`, §3.2) flags the run as a regression, and — where the suite is used as a gate (§10.4) — blocks the change that produced it.

### 10.3 The Eval-Blind-Iteration Guard

Evaluation-gated evolution is the canonical posture (a `core` invariant realized here, with eval-blind iteration as the rejected anti-pattern). The rule: a change to an evaluated configuration dimension — a prompt or instruction revision, a routing strategy, a policy template, a model profile, a capability revision, a retrieval or context configuration — should carry replayable before/after evaluation evidence before it is accepted as an improvement, and the evaluation evidence is recorded as provenance on the change (`artifact.provenance`, File 09 §15). This is a configurable posture, not a hard block on every change: trivial changes, and changes the user explicitly accepts without evaluation, proceed; the guard surfaces the absence of before/after evidence rather than forbidding the change. The strongest form is the eval-pass gate (§10.4). The posture is settings-governed (§17) and never a hidden hardcoded branch.

### 10.4 The Eval-Pass Gate

An evaluation may gate a graduation, an installation, or a promotion. The gate realizes the requirement that agent-generated extensions pass an evaluation or a cheap smoke-test before installation:

- a generated `Validator`, `Workflow`, custom tool, adapter, extraction schema, or prompt fragment may be required to pass a designated `EvalSuite` (or a cheap smoke-test suite) before it is installed or graduated — the gate this file offers, consumed by the workflow graduation path (File 34), the plugin install path (File 35), and the self-modification path
- a routing, policy, or model-profile change may be gated by a regression suite that must not regress beyond a declared threshold
- the gate is a `Completion`-boundary required validation on the gating run's `RunCompletionContract` where it gates a single run (`run.completion-contract`, File 04 §2.7; `qc.completion-gate`, File 39 §14), or a precondition on the install/graduation capability where it gates a durable registration

The gate is opt-in per the gating path's policy and is never a silent default that blocks all changes; it is a declared requirement on the specific path that wants it.

A suite used as an eval-pass gate, or as any high-trust installation, graduation, or promotion gate, must trace to a ground-truth anchor: human annotations, deterministic golden comparisons, property assertions, or calibrated independent validators accepted by the gate policy. It may not rest solely on uncalibrated model-mediated scorers. A generated validator gated by a generated suite scored only by model judges is a self-certifying loop and is invalid for high-trust gates unless the user explicitly accepts that circular provenance.

### 10.5 Boundary

The baseline, the regression report, and the guard are this file's. The provenance recording is File 09's. The graduation, install, and promotion mechanics are owned by Files 34, 35, and 09; this file offers the eval-pass gate they may require and does not own their lifecycle. The settings that govern the posture are File 15's.

## 11. The Judge-Optimization Pipeline

Anchor: `eval.judge-optimization`

### 11.1 Definition

A `JudgeOptimization` is a long-running, user-gated, cost-previewed `Run` that calibrates a model-mediated judge (a `ModelMediated` `Validator`) against an annotated dataset, producing an optimized judge prompt registered back as a `Validator` through File 39's registration path. It is the offline pipeline that `qc.judge-discipline` (File 39 §6.4) and `qc.events-metrics` (File 39 §17.3) explicitly defer to this file: "the offline optimization pipeline that calibrates a judge against annotated traces — that pipeline is a long-running evaluation run owned by the Evaluation and Benchmarking spec (File 40), gated by explicit user invocation, with cost preview."

### 11.2 The Pipeline

A `JudgeOptimization` runs as a `Run` (not a separate pipeline runtime) with declared stages: load the annotated dataset and split it by task (not by trace) into training and held-out validation sets with no leakage; iterate candidate judge prompts; evaluate candidates over the training set; select; validate the result on the held-out set; and register the resulting judge (user-gated). The optimizer:

- uses a capable reflector model to propose improved prompts from failing examples and their reasoning, and a cheaper judge model that runs over every example — the asymmetric reflector-capable / judge-cheap deployment topology
- requires the annotations' reasoning, not just verdicts, because the optimizer learns the implicit policy from the reasoning (§12)
- is provider-agnostic — wired through the model-strategy and provider layers (Files 16, 17), never coupled to one provider's API
- selects candidates by per-task performance, not by average alone, preserving candidates that solve distinct cases (a Pareto-diverse selection), so that a candidate solving a small but unique slice survives
- is generalizable beyond judges: the same config-and-evaluate loop optimizes a router prompt, a subsystem instruction set, a retrieval configuration, or a compaction policy — any serializable configuration evaluated against an `EvalSuite` — but every optimization is gated and cost-previewed

### 11.3 Cost, Gating, and Deployment

A `JudgeOptimization` is expensive (many model calls over many candidates and examples). It is therefore:

- user-gated — the agent may draft and propose an optimization and may never start one without explicit user invocation
- cost-previewed — the run computes and surfaces a cost estimate before starting (the fixture/candidate/budget product against the `PricingSnapshot`; §14), treated like any other long-running, costed pipeline
- budgeted — it runs under the canonical run and per-stage budgets (`run.budgets-limits`, File 04 §21), is cancellable as a group and individually (`run.cancellation`, File 04 §17.3), and is resumable where its stages declare resumption

The result is a calibrated narrow judge. Where an optimization produces several specialized judges (one per error mode), they may be deployed as an ensemble behind a router (`model.multi-model-selection-plans`, File 16 §13; `CustomStrategy`, File 16 §4.3) rather than forcibly merged into one prompt; the router selects the specialist judge per target. Each specialist judge is registered as a versioned `Validator` with its dataset, replay key, source, and calibration metadata. The router records the selected specialist, the selection inputs, and the selection result for every verdict, so an ensemble remains inspectable and replayable rather than becoming an opaque convenience wrapper.

### 11.4 No Built-In General Judge

This file ships the optimization machinery, the annotation queue, and the dataset contract — not a built-in general-purpose correctness or hallucination judge, and not a built-in general-quality benchmark with foregone scores (the rule of `qc.judge-discipline`, File 39 §6.3, applied to the offline layer). Judges are authored per failure mode, calibrated against observed traces, and registered like any other validator. A judge optimized here is registered as a narrow `Validator` (File 39); File 39 owns its inline execution.

### 11.5 Boundary

The judge primitive, the judge discipline, and the inline judge execution are File 39's. The model strategy and provider layers are Files 16 and 17. The run model, budgets, and cancellation are File 04's. This file owns the optimization run, its stages, the provider-agnostic optimizer contract, the cost-preview and gating rules, and the ensemble-behind-a-router deployment option.

## 12. Annotation, Datasets, and Error Analysis

Anchor: `eval.annotation-datasets`

### 12.1 The `Annotation`

An `Annotation` is a labeling of a recorded target (a run, trace, block, or artifact) that rides the File 09 Validation block: its `verdict` and `reasoning` are the File 09 Validation block's verdict and reasoning fields (`artifact.validation-critique`, File 09 §14.1), and its `role` (`GroundTruthLabel`, `ReviewerNote`, `ModelAssistedLabel`, or a registered custom role) is a thin File-40 evaluation-layer tag carried over that block, not a parallel record. It records the annotator identity and reuses the `Critique`- or `Validation`-shaped records File 09 defines, but it is not treated as `validated_by` provenance and does not affect File 09's `ValidationState` unless explicitly attached as a validation. Annotations are the labeled ground truth a suite scores against and a `JudgeOptimization` learns from. The reasoning is required: the optimizer cannot discover the implicit policy from verdicts alone. A model-assisted annotation records the annotating model identity. A producer-model self-label used as a gate anchor or judge-optimization shortcut without independent human or independent-model review is flagged and cannot silently satisfy a high-trust gate.

### 12.2 The `AnnotationQueue`

An `AnnotationQueue` is a derived work-list projection over recorded runs selected for labeling — by sampling, by similarity to a failed run (block-embedding similarity over the retrieval substrate, File 12), by error-mode filter, or by family. It is a projection, not a parallel store; the annotations it collects are durable records. The queue surfaces traces for an annotator to label with verdict and reasoning.

### 12.3 Error Analysis and Dataset Quality

The canonical workflow for building a narrow judge follows the error-analysis discipline: review a sample of recorded traces, cluster their failures into error modes, and formalize each error-mode cluster as one narrow judge with its own annotated dataset. Many narrow judges, one per error mode, are correct; one omnibus judge is not (`qc.judge-discipline`, File 39 §6.2). Annotation quality dominates the result: a judge optimized against noisy or auto-generated-without-review annotations is capped well below its potential, so annotations are user-authored or carefully model-assisted-then-reviewed, never silently treated as ground truth. The train/validation split is by task, not by trace, to prevent leakage.

### 12.4 Train-a-Judge-From-a-Conversation

The end-to-end flow named by `qc.events-metrics` (File 39 §17.3) is owned here: the user selects a conversation or run where the agent failed; the system finds similar recorded runs by block-embedding similarity (File 12); it opens an annotation queue over those runs; the user labels a set with verdict and reasoning; a `JudgeOptimization` run (§11) calibrates a judge from the labeled dataset; and the resulting judge is registered as a candidate `Validator`, user-gated. The flow runs entirely inside the system over recorded runs; no external tooling is required.

### 12.5 Boundary

The annotation records are blocks (File 09); the similarity retrieval is File 12's; the registration handoff is File 39's. This file owns the annotation queue projection, the dataset contract, the error-analysis discipline, and the train-a-judge flow.

## 13. `EvalScore`, `EvalReport`, and Leaderboards

Anchor: `eval.eval-score-report`

### 13.1 `EvalScore` Is a Derived Projection

An `EvalScore` is the derived aggregation view over an `EvalRun`'s per-case verdicts (`Validation`/`Critique` blocks) and golden-comparison results. It is computed on read, exactly as `ValidationReport` is computed over validation blocks (`qc.validation-report`, File 39 §12) and `Provenance` over the block graph (`artifact.provenance`, File 09 §15). It is not a stored primitive and not a parallel result ledger; the per-case verdicts are the source of truth, and any score cache is a rebuildable projection (`core.projection`, File 01 §6.11) invalidated event-driven on new verdicts.

### 13.2 What the Projection Computes

An `EvalScore` summarizes: pass rate per scorer, per family, and per suite; the set of decisive failing cases with their failure details; the per-scorer false-positive context where annotation feedback exists; the latency distribution and the cost figures (from `TokenUsageRecord`/`PricingSnapshot`, File 17); the regression deltas versus the baseline (§10); and, for comparison evaluations, the win/tie/loss distribution and any ranking projection (Elo or Bradley-Terry over the pairwise outcomes; §9). It carries the denominator policy and resolved case/scorer weights used for aggregation, and counts `Skipped`, `NotApplicable`, `BudgetDropped`, `BackendUnavailable`, `Inconclusive`, and `NeedsReview` separately from `Passed` and `Failed`. It carries a `truncated` flag with truncation details when aggregation bounds were hit; a truncated report is not proof that no further failures exist beyond the bound (the rule of `qc.validation-report`, File 39 §12.2).

### 13.3 Leaderboards and Rankings Are Projections

A leaderboard (an arena ranking of arms, a cross-runner comparison of systems) is a projection over recorded comparison outcomes; it holds no fact the underlying verdicts do not produce, and it is rebuildable. Rankings are aggregate projections over binary per-case relative verdicts, never per-case scores (§6.3, §9.4).

### 13.4 Determinism

Given the same per-case verdicts and the same baseline, two `EvalScore` computations return identical results; this is the load-bearing property for replay and audit (mirroring `qc.validation-report`, File 39 §12.3). An `EvalReport` is the rendered, user-facing form of one or more `EvalScore`s plus the run's configuration and regression context.

### 13.5 Boundary

The verdicts are blocks (File 09). The projection contract is File 11's (`version.version-graph-backed-projections`, File 11 §16). The rendering is Files 37 and 38's; the live-metric surfacing is the telemetry spec's. This file specifies the score aggregation contract, the leaderboard-as-projection rule, and the determinism property.

## 14. Cost, Budgets, and Scheduling

Anchor: `eval.cost-budgets-scheduling`

### 14.1 Cost Preview

Before an expensive evaluation (a full-suite `EvalRun`, a `FullRerun` over many cases, a `JudgeOptimization`, an arena), the system computes and surfaces a typed cost preview. The preview records its assumptions: fixture, arm, candidate, and scorer counts; `PricingSnapshot` identity; cache assumptions; replay-mode costs; unknown-cost components; uncertainty or upper-bound treatment; and the budget gate it will enforce. Historical cost replay reads recorded `TokenUsageRecord`s and the recorded `PricingSnapshot`; it never queries a live provider endpoint to reinterpret old cost. Expensive runs are user-gated with the preview, exactly as a long-running costed pipeline is. A cheap, sampled monitoring suite needs no gate; the gate is proportional to projected cost.

### 14.2 Budgets and Sampling

An `EvalRun` runs under the canonical run and per-stage budgets (`run.budgets-limits`, File 04 §21). A suite declares its sampling policy (§3.2): `EveryCase` for a regression suite (every fixture, deterministic), `Sampled { fraction }` for a cheap monitoring suite, and `DeepDive { fraction }` for an expensive sampled deep-dive (a fraction, run with capable models for drift and trend analysis). File 33 or explicit user action decides when the suite is triggered; the sampling policy decides which cases within that trigger are selected. A suite may declare a fixed per-case budget so that arms are compared fairly under the same resource ceiling. Silent truncation of the case set is forbidden: when a budget or sampling bound drops cases, the dropped set is recorded and reported (§13.2), so a partial run never reads as full coverage.

### 14.3 Scheduling Without a Parallel Scheduler

Evaluation runs are `Run`s; they are triggered manually (a user runs a suite), by an eval-pass gate (a graduation, install, or promotion; §10.4), or by an `Automation` (File 33 — a configured `Schedule` or `Event` trigger). File 33 owns the trigger, the arming gate, and the non-interactive safety posture; this file owns the suite body (the 40↔33 seam, §2.6). There is no separate evaluation scheduler or evaluation execution queue; an evaluation's concurrency and resource posture are the run model's concurrency caps and budgets, not a parallel queue.

### 14.4 Boundary

The budgets, the run model, and cancellation are File 04's. The cost projection is File 17's. The trigger is File 33's. This file owns the cost-preview rule, the sampling policy, the fair-comparison budget, the no-silent-truncation rule, and the no-parallel-scheduler rule.

## 15. The `eval.*` Capability Surface and the Evaluation Surface-and-Service Duality

Anchor: `eval.capability-surface`

### 15.1 Surface-and-Service Duality

Evaluation is a substrate service with a management surface (the surface-and-service duality of the Teacher and System Agent surfaces; `core.substrate-services`, File 01 §2.4 names "logging and evaluation"). As a service, the `eval.*` capability family is borrowable cross-surface — any surface or run may register a suite, run an evaluation, query a score, or open an annotation queue. As a surface, an evaluation management view (an inspector lens, the Observatory's evaluation pane) renders the suite catalogue, run history, scores, regression reports, comparison boards, leaderboards, and annotation queues. There is no evaluation-mode field; the management view is a presentation of the service's durable state.

### 15.2 The Capability Family

The canonical evaluation capabilities, each a built-in capability declared per `capability.declaration` (File 05 §3):

- `eval.suite.register(suite_declaration)` — register an `EvalSuite` (proposal-first; `UserApproval`; under source approval)
- `eval.suite.list(filter?)` / `eval.suite.inspect(suite_id)` — enumerate and inspect suites and their versions (`ReadOnly`)
- `eval.case.add(suite_id, case)` / `eval.case.remove(suite_id, case_id)` — manage a suite's cases (commits a new suite version; `WorkspaceWrite`)
- `eval.run(suite_id, configuration?, replay_mode?)` — execute a suite as an `EvalRun`; tier resolves from the replay mode and the cases' side effects (an `Inspect` run is `ReadOnly`; a `SimulateDeterministic` run is `WorkspaceWrite`; a `FullRerun` run inherits the replayed cases' tiers and may require `UserApproval` per `version.replay-semantics`, File 11 §15.6)
- `eval.preview_cost(suite_id, configuration?)` — compute and return the cost preview without running (§14.1; `ReadOnly`)
- `eval.compare(suite_id, arms, comparison_shape)` — run a comparison evaluation over two or more arms (§9)
- `eval.report(eval_run_id, options?)` — compute and return the `EvalScore`/`EvalReport` for a run (`ReadOnly`; deterministic-replayable)
- `eval.baseline.set(suite_id, eval_run_id)` — designate a regression baseline (§10; `WorkspaceWrite`, audit-visible)
- `eval.annotate(target_ref, verdict, reasoning)` — record an `Annotation` (§12; `WorkspaceWrite`)
- `eval.queue.open(selector)` — open an `AnnotationQueue` over selected recorded runs (§12; `ReadOnly` to read, `WorkspaceWrite` to persist the queue)
- `eval.optimize_judge(judge_id, dataset_ref, budget)` — start a `JudgeOptimization` run (§11; long-running, `UserApproval` with cost preview)

Evaluation reuses `validation.run`/`validation.attach`/`validation.report` (File 09 §16; `qc.capability-surface`, File 39 §16) for the underlying scoring and the `replay.*` capabilities (`version.replay-semantics`, File 11 §15.6) for the replay; it does not redefine those signatures. Surface- and subsystem-specific evaluation capabilities expose family-namespaced adapter capabilities (a Coder `coder.eval.run`, a Web `web.eval.research`) over `eval.run`; the underlying record is always a canonical `EvalRun`.

### 15.3 Boundary

The capability declarations and registry are owned by File 05; the policy on each call by File 06; the management view rendering by Files 37 and 38. This file declares the family, its semantics, and the surface-and-service duality.

## 16. Events

Anchor: `eval.events`

Evaluation emits through `Custom { namespace: "evaluation" }` and `Custom { namespace: "replay" }` events registered through the canonical mechanism (`ledger.custom-kind-registration`, File 10 §4.3); the canonical `LedgerEntryKind` catalogue reserves no evaluation kinds (`ledger.entry-kind-catalogue`, File 10 §4.1), and surface-, subsystem-, plugin-, MCP-, API-, and user-defined evaluation facts register as `Custom`. Expected event families: `EvalCaseScored`, `GoldenComparisonRan`, `RegressionDetected`, `ComparisonVerdictRecorded`, `BaselineSet`, `AnnotationRecorded`, `AnnotationQueueOpened`, and `EvalPassGateEvaluated`. An `EvalRun` and a `JudgeOptimization` are `Run`s (§7, §11); their start and completion are ordinary run-ledger data carried by the canonical run lifecycle events (`RunCreated`, `RunStatusChanged`; `ledger.entry-kind-catalogue`, File 10 §4.1), and this section declares evaluation-specific facts, not parallel eval-run or judge-optimization lifecycle events that would duplicate the run lifecycle. The `ReplayStarted` / `ReplayCompleted` events the replay engine emits are the `Custom { namespace: "replay" }` kinds already established by `version.replay-semantics` (File 11 §15.5). Each event carries the canonical envelope (`ledger.event-envelope`, File 10 §5.2). Consequential evaluation facts (a run's outcome, a regression, a baseline change, a judge registration) are ledger entries; the event stream is live coordination, not the source of truth (`core.durable-history-transient-coordination`, File 01 §7.3). `Secret`-tagged payloads follow the never-persist-Secret rule (`ledger.event-stream`, File 10 §5.6).

## 17. Settings, Profiles, and Per-Profile Defaults

Anchor: `eval.settings`

### 17.1 Configurable Dimensions

Every evaluation mechanism is configurable through the canonical settings system (`core.settings-system`, File 01 §6.8) resolved through the canonical settings source stack (`settings.scopes-profile-contexts-overlays`, File 15 §5.2), using the evaluation invocation overlay the settings model already names (`settings.scopes-profile-contexts-overlays`, File 15 §5.3; File 13 §20). At minimum, settings support:

- per-suite enablement and scoped overrides (global, workspace, conversation, per-profile)
- the default replay mode, the sampling policy and trigger-binding defaults, and the per-case and per-run budgets
- the cost-preview threshold above which a run is user-gated
- per-suite success criteria thresholds (minimum pass rates, maximum regression deltas, latency and cost ceilings) — thresholds are settings, never hardcoded constants (`settings.settings-over-constants`, File 15 §13)
- the regression policy: which delta classifies as a regression, and whether a regression flags or blocks
- the evaluation-gated-evolution posture: whether a change to an evaluated dimension requires before/after evidence, and where the eval-pass gate is required (graduation, install, promotion)
- the golden-comparison preference (which comparison kind a suite defaults to) and the fuzzy-tolerance thresholds
- the judge-optimization budget ceilings, the reflector and judge model preferences, and the annotation-sampling policy
- the comparison defaults (blind-comparator enablement, the arena/tournament shape, the ranking model)

### 17.2 Per-Profile Defaults

Suite enablement and the evaluation posture carry per-profile defaults so that the default experience fits the user's work: a coding profile defaults the `Coding`, `ToolUse`, and `Reliability` suites on; a research profile defaults the `Research`, `Retrieval`, and `Safety` suites on; a development profile defaults the regression gate on for prompt and policy changes. Defaults are seeded by built-in defaults and by plugin evaluation-default contributions (File 35), then by the user's durable overrides as audit-visible records (the built-in-then-override pattern of `policy.built-in-reusable-policy-rules`, File 06 §11.5). The default posture is the best overall option; the user may override any of it.

### 17.3 Boundary

The settings cascade, profiles, and overlay resolution are owned by File 15; the plugin contribution mechanism by File 35. This file names the dimensions and the per-profile default discipline.

## 18. Persistence, Locality, and Replay

Anchor: `eval.persistence-replay`

### 18.1 What Is Durable

The durable evaluation state is carried by existing substrates plus the net-new definition-and-record objects: `EvalSuite`, `EvalCase`, and `EvalRun` records realized through File 20's storage substrate; the per-case verdicts as `Validation`/`Critique` blocks in the block pool (Files 08, 09); the annotations as durable records (§12); the evaluation ledger entries (`Custom { namespace: "evaluation" }`, File 10); the regression baselines as versioned designations; and the suite versions in the version graph (File 11). Suite enablement and per-profile defaults are settings records (File 15). There is no parallel evaluation result store; the per-case verdicts are the source of truth.

### 18.2 What Is Computed

The `EvalScore`, the `EvalReport`, the leaderboards, the rankings, the regression reports, and the annotation queue are computed projections over the durable substrates, rebuildable from them (`version.version-graph-backed-projections`, File 11 §16; `core.projection`, File 01 §6.11). A stale or corrupted score, report, leaderboard, or queue projection costs a rebuild, never data loss.

### 18.3 Locality

Suite, case, and annotation definitions follow the locality of the substrates that carry them: definitions sync per the block-sync eligibility rules (File 21); a recorded-run fixture references durable ledger scopes and snapshots and does not duplicate them; device-local evaluation state (a resolved run handle, a cached projection) is rebuildable per device and not synced. Recorded-run fixtures and the suites, baselines, and regression reports that reference them place retention holds on the referenced substrate until the user or policy explicitly releases those holds with preview. A model-mediated scorer or judge replays from its recorded replay key (`qc.persistence-replay`, File 39 §10.5), never from the live model endpoint (`provider.token-source`, File 17).

### 18.4 Replay and Test Obligations

An `EvalRun` over recorded inputs is replayable: replaying the recorded fixtures under the same pinned configuration reproduces the per-case verdicts and aggregate scores, modulo explicitly-typed model-mediated nondeterminism that is recorded (§7.5). A replay-equivalence test is required wherever an `EvalRun`'s outcomes are claimed to reproduce: re-running a recorded run reproduces its outcomes modulo recorded nondeterminism. Wherever a golden comparison or a fixture identity is defined over a hash, a golden canonical-encoding test is required: a fixed typed input encodes to a fixed byte sequence and a fixed hash, pinning the encoding against drift (`core.canonical-hash`, File 01 §7.14). This file defines no new hash; it reuses the block, version-diff, and ledger hashes of Files 08, 10, and 11, and inherits their golden-test obligation.

### 18.5 Boundary

Storage realization is owned by File 20; sync and portability by File 21; replay mechanics by Files 10 and 11. This file specifies what is durable, what is computed, the locality split, and the replay-equivalence and golden-encoding obligations for evaluations.

## 19. Explicit Rejections

Anchor: `eval.explicit-rejections`

The following shapes are wrong for this layer:

- a separate evaluation engine, a parallel evaluation runtime, a second scheduler, or an evaluation execution queue distinct from the run model — an `EvalRun` is a `Run`; a parallel architecture that does the same thing is rejected (`run.consequences-for-later-specs`, File 04 §29)
- a parallel evaluation result store, a parallel scorer registry, or a parallel result carrier — suites/cases/runs are the net-new definition-and-record objects; verdicts are `Validation`/`Critique` blocks; scores and leaderboards are derived projections
- redefining the `Validator`, the validation gate, `ValidationOutcome`, the judge discipline, the `Validation`/`Critique` blocks, the replay capabilities, the `VersionDiff`/`diff_hash` primitives, `ModelSelectionRecord`, or `TokenUsageRecord` — those are owned by Files 39, 09, 10, 11, 16, and 17; this file consumes them
- a built-in general-purpose correctness or quality judge, or a built-in general-quality benchmark with foregone scores, surfaced as a default — the system ships the suite/case/run/score machinery, the comparison shapes, and the judge-optimization pipeline, not foregone verdicts; suites and judges are narrow and authored per concern
- a one-to-five or zero-to-one numerical score as a per-case verdict — per-case verdicts are `Passed`/`Failed`/`Inconclusive` or a small closed enum; continuous figures (pass rate, win rate, Elo, item-response-theory estimates) are downstream aggregate projections, never per-case scores
- a model-mediated scorer or comparison judge that returns a verdict without reasoning, or that is not blind to which arm produced which output in a pairwise comparison — reasoning is required for transparency, adjudication, and optimization; blindness removes position and source bias
- re-deriving any evaluation input from a live mutable source — evaluation replays recorded snapshots and immutable references; a deterministic evaluation reproduces its scores, and a model-mediated evaluation reproduces its recorded verdict rather than re-invoking the model
- recording a case as `Passed` without the ledgered evidence its scorers require, or presenting a skipped scorer as passed, or silently truncating the case set so a partial run reads as full coverage — the eval-forgery guard, the coverage rule, and the no-silent-truncation rule forbid these
- silently regenerating or overwriting a golden artifact — a golden is a pinned `ArtifactVersion`; accepting a new output as the golden is an explicit, recorded user action that commits a new suite version
- auto-triggering an expensive evaluation or a judge optimization without a cost preview and a user gate — expensive runs are gated proportional to projected cost
- coupling the judge optimizer or any scorer to one provider's API — optimization and scoring are provider-agnostic, wired through Files 16 and 17
- a gating or graduation evaluation grounded solely in uncalibrated model-mediated scorers, with no human-annotated, deterministic, property-assertion, or calibrated independent anchor — that is a self-certifying loop, not evidence
- scoring a determinism violation in a deterministic-declared replay path as a plain output-quality failure — the failure is a replay-class or deterministic-substrate declaration problem and must be typed that way
- scoring a fixture whose referenced substrate is missing or partially pruned — a recorded-run fixture with dangling references is unreplayable until repaired or intentionally released from that obligation
- a hard, non-configurable block on every change lacking before/after evaluation evidence — evaluation-gated evolution is the posture and the eval-pass gate is opt-in per path; the guard surfaces the absence of evidence and gates the paths that declare a gate, never gatekeeps all changes
- folding inline runtime validation, the validation gate, or the live-metric projections into this layer — inline validation that gates live execution is File 39's; live metrics, traces, and observability projections are File 41's; this layer is offline measurement over recorded and fixture inputs
- treating live evaluation events as durable evaluation truth — consequential evaluation facts are records and blocks; the event stream is live coordination
- hardcoding success-criteria thresholds, regression thresholds, sampling policy, trigger defaults, budgets, fuzzy tolerances, or the evaluation posture as constants instead of settings — evaluation behavior is configurable product variation

## 20. Consequences for Later Specs

Anchor: `eval.consequences-for-later-specs`

Later specs must follow these rules:

- the **Telemetry, Logging, and Observability** spec (File 41) must compute live metrics, traces, and quality-metric projections (validator-accuracy, false-positive rate, latency, pass-rate aggregates) over the ledger and events without introducing a parallel store, and must consume — never redefine — this file's `EvalScore`/`EvalReport`/leaderboard contracts where the Observatory renders evaluation results; the 40↔41 seam is fixed (offline-suites-and-comparison versus live-observation-and-aggregation)
- the **Runtime Infrastructure and Lifecycle** spec (File 42) must orchestrate evaluation-run execution through the one run model and the one scheduler/trigger substrate (File 33), never a parallel evaluation scheduler, and must realize the replay-engine execution within the run lifecycle
- the **Packaging, Platform, and Distribution** spec (File 43) must bundle built-in suites and golden fixtures into the image as ship-with content, and must not introduce a parallel evaluation distribution path
- the **storage and sync specs** (Files 20, 21) — already written — must realize `EvalSuite`/`EvalCase`/`EvalRun` records and evaluation ledger entries through their storage substrate, respect recorded-run fixture retention holds, keep `EvalScore`/leaderboard projections rebuildable, follow the locality split (synced definitions; device-local resolved handles and caches), and provide the golden canonical-encoding fixtures for any hashed comparison; the `Portability` family (§8) verifies their round-trips over recorded snapshots
- the **per-surface specs** (Files 25–32) — already written — register their family scorers through File 39's path, declare the family and primary artifact their work belongs to, and may ship built-in suites; none introduces a private evaluation pipeline; the surface, perception, coding, control-rail, and connector families discharge their offline-evaluation consequences over recorded snapshots
- the **automation and workflow specs** (Files 33, 34) — already written — own the trigger binding and the workflow body respectively; this file confirms a scheduled regression run is an `Automation` over an `EvalSuite` body (the 40↔33 seam) and the workflow-reliability harness consumes File 34's reliability metadata (the 40↔34 seam), with no parallel scheduler or harness runtime
- the **plugin and extension spec** (File 35) — already written — contributes suites, scorers, fixtures, and per-profile evaluation defaults through the plugin contribution path under source approval and trust narrowing, and may require the eval-pass gate (§10.4) on a generated extension before installation
- the **model strategy and provider specs** (Files 16, 17) — already written — supply `ModelSelectionRecord`, `TokenUsageRecord`, and `PricingSnapshot` as the primary artifacts of the `ModelSelection` and `Cost` families; this file measures over them and never re-derives a historical selection, cost, or token count from a live endpoint
- any spec that introduces a new evaluable system dimension must declare the `EvalFamily` and the primary artifact it is scored against, rather than inventing a bespoke benchmark; the suite/case/run/score-plus-family contract of this file is the canonical shape for "is this dimension correct, and did a change improve or regress it"

## 21. Canonical Rule Anchors

Anchor: `eval.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `eval.chosen-model`, `eval.boundaries`, `eval.eval-suite`, `eval.eval-case-fixtures`, `eval.golden-comparison`, `eval.scorer-verdict-model`, `eval.eval-run-replay`, `eval.eval-families`, `eval.comparison-evals`, `eval.regression-gated-evolution`, `eval.judge-optimization`, `eval.annotation-datasets`, `eval.eval-score-report`, `eval.cost-budgets-scheduling`, `eval.capability-surface`, `eval.events`, `eval.settings`, and `eval.persistence-replay`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
