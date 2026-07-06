# Quality Control and Validation

## Status

Canonical.

## Scope

This file defines:

- the `Validator` primitive — the registered, typed, named checking rule that binds a check backend to a validation boundary and produces `Validation`/`Critique` records
- the closed canonical `ValidationBoundary` set — where validators attach in the execution lifecycle
- the structural-versus-semantic check taxonomy over File 09's `ValidationKind`, and the latency posture each implies
- `validator_kind` semantics (`Deterministic`, `ModelMediated`, `UserManual`) and the model-mediated judge discipline
- the outcome, severity, and finding model — reuse of File 09's `ValidationOutcome`, the closed `ValidationSeverity` set, and the failure/finding contract
- the validation gate — blocking semantics per boundary, fail-direction, and how quality control gates run completion through the `RunCompletionContract`
- the non-destructive correction model — version-branch correction, `CorrectionConfidence`, and the pre-execution `Block`/`RedirectSuggestion`/`Substitute` decisions
- validator registration, sourcing, trust, and the per-capability inline special case (`input_validators`, `postconditions`)
- the `ValidationReport` derived aggregation projection
- real-time / streaming validation
- completion verification and its integration with `run.termination` (File 04 §22)
- the baseline surface and subsystem validators and how each surface specializes
- the `validation.*` capability surface and the quality-control management surface (surface-and-service duality)
- quality-control events, settings, per-profile defaults, persistence, locality, and replay
- the operating constraints (precision-over-recall, latency budget, transparency, no-blocking-on-user-input-during-generation)

This file does not define:

- the `Validation`, `Critique`, `Evidence`, `Claim`, or `Observation` block kinds, `ValidationOutcome`, `ValidationState` derivation, or the `validation.run`/`validation.attach` capabilities — File 09 owns those; this file consumes them
- the `Hook` primitive, hook categories, hook decision vocabulary, priority, authority classes, timeout/fail-direction mechanics, or hook registration/discovery — File 10 owns those; this file specifies the validator semantics that use them
- the `RunCompletionContract`, the completion-forgery guard, the completion-verification hook surface mechanics, or the capability-call pipeline — File 04 owns those; this file specifies the validator content that runs on the hook surface and how validations become completion requirements
- the `CapabilityDeclaration` field set (`input_validators`, `postconditions`, `stale_state_revalidation`), the registry, or backend bindings — File 05 owns those; this file generalizes the per-capability validators into the cross-cutting `Validator` concept
- the policy engine, the approval router, approval-policy templates, leases, permission tiers, or the behavioral and safety policy templates (`prefer_dedicated_tools`, `fetch_fallback_ban`, `clarify_first_for_multistep`, protected-branch rules) — File 06 owns those; this file owns quality validators, not permission gating
- offline evaluation suites, benchmarks, regression harnesses, scenario fixtures, golden-artifact comparison, and judge-prompt optimization runs — the Evaluation and Benchmarking spec (File 40) owns those; this file owns inline runtime validation that gates live execution
- the secret vault, secret detection/redaction primitives, untrusted-content/injection defense primitives, or encryption — File 22 owns those; this file wraps them as `SafetyCheck` validators where they gate output quality
- sandbox or process isolation primitives within which validators execute code — File 23 owns those
- storage schemas, projection rebuild internals, or sync/portability of validation records — Files 20 and 21 own those
- UI rendering of validation badges, quality-control panels, correction toasts, or annotation queues — Files 37 and 38 own those; this file specifies the data contracts they consume
- per-surface runtime designs — the per-surface specs (Files 27–32) own those; this file declares the canonical baseline validators and the registration contract surfaces specialize

## Source Resolution

This file resolves quality-control, validation, verification, guardrail, completion-check, grounding-check, correction, and critic material into one boundary: the inline validation layer over the one hook, block, ledger, completion, and policy substrate.

Resolved design:

- Quality control is not a separate pipeline, a parallel validator runtime, or a subsystem. A `Validator` is a registered checking rule that runs as a validator-category `Hook` (File 10) whose handler is a check backend (a capability, a designated model, or a user) and whose result is a `Validation` or `Critique` block (File 09). There is no parallel validator registry, no second execution path, and no private validation store.
- Validation gates execution at declared boundaries. A blocking validator denies, redirects, or narrows a proposed action; gates a commit; or contributes a completion requirement. An advisory validator records and surfaces without blocking.
- Corrections are non-destructive. A correction creates a sibling version or returns a typed in-band signal; it never silently mutates the produced output in place.
- Quality control ships machinery, not foregone verdicts. The system ships the validator primitive, the deterministic check backends, and the model-mediated judge slot. It does not ship a built-in general-purpose correctness or hallucination judge as a default.
- Inline validation (this file) and offline evaluation (the Evaluation and Benchmarking spec (File 40)) are two layers of one quality discipline. This file owns the layer that runs during and around live execution and gates it; the offline layer runs over recorded runs to measure and compare.

## 1. Chosen Model

Anchor: `qc.chosen-model`

ATLAS3 has one quality-control layer. Every check that decides whether a proposed action, a generated output, a produced artifact, a captured observation, or an asserted claim is well-formed, correct, complete, grounded, consistent, or safe is a `Validator`. A `Validator` produces a `Validation` block (a pass/fail/inconclusive check) or a `Critique` block (an evaluative finding) per `artifact.validation-critique` (File 09 §14), records its run through the canonical ledger and event entries reserved for quality control (`QualityControlValidatorRan`, `QualityControlViolationDetected`, `CompletionVerificationFired`, `ValidationCompleted`, `CritiquePublished`, `ArtifactValidationStateChanged`; per `ledger.entry-kind-catalogue`, File 10 §4.1), and — when blocking — gates execution through the typed hook decision vocabulary (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`; per `ledger.hook-decision-vocabulary`, File 10 §7.2).

A `Validator` is the composition of three things already canonical:

- a **boundary binding** — a `Hook` subscription (per `ledger.hook`, File 10 §7) of a quality-control category (`validator`, `completion_verification`, `postcondition_check`, `safety_gate`) at a declared `ValidationBoundary` (§4)
- a **check backend** — a `Deterministic` registered capability, a `ModelMediated` designated model evaluating a configured policy model-request template, or a `UserManual` reviewer (the `validator_kind` already named by `artifact.validation-critique`, File 09 §14.1)
- a **result contract** — the `Validation` or `Critique` block the check commits, plus the typed gate decision the boundary consumes

There is no second registry, no per-subsystem bespoke quality pipeline, no parallel validator runtime, and no "QC engine" separate from the run model. The validator-category hooks in the one hook registry are the validator catalogue. The check backends live in the one Capability Registry. The results live in the one block pool. The gate decisions flow through the one hook bus. Quality control is an orchestration of existing primitives, not a new architecture.

`Validator` is the canonical noun for the checking rule. "Guardrail", "tripwire", "validator node", "inspector", "verifier pass", "critic", and "quality gate" are vocabulary variants in source material for one or more aspects of the system this file defines; the canonical names here are `Validator`, `ValidationBoundary`, `ValidationSeverity`, `CorrectionPolicy`, and `ValidationReport`.

This model elaborates `core.evidence` (File 01 §4.4) (validations are a kind of evidence), `core.evidence-provenance` (File 01 §7.12) (important outputs preserve validation state), the execution-ledger requirement to record validations (`core.execution-ledger`, File 01 §6.4), and `run.hook-integration` (File 04 §23.3)'s rule that "quality control validators … integrate through this shared mechanism … must not create a second hidden execution path." It discharges the quality-control deferrals named in `ledger.hook` (File 10 §7.7, §7.8) and `run.termination` (File 04 §22), and the quality-control note left by `customize.consequences-for-later-specs` (File 38 §23).

## 2. Boundaries with Adjacent Layers

Anchor: `qc.boundaries-with-adjacent-layers`

### 2.1 With File 09 (Artifacts, Claims, Evidence, and Provenance)

The boundary is sharp. File 09 owns the result objects: the `Validation` and `Critique` block kinds, the `ValidationKind` enum, the `ValidationOutcome` enum (`Passed`, `Failed`, `Inconclusive`), the `validator_kind` enum (`Deterministic`, `ModelMediated`, `UserManual`), the `ValidationState` derivation over `validated_by` edges (`artifact.validation-state-derivation`, File 09 §14.2), and the `validation.run`/`validation.attach` capabilities. File 39 owns the rule that produces those results — the `Validator` — and the orchestration that decides which validators run when, what their verdicts gate, and how corrections are applied. File 39 never redefines the `Validation` block, never introduces a parallel result carrier, and never bypasses File 09's `ValidationState` derivation. Every validator outcome commits a `Validation` (or `Critique`) block via File 09's capabilities and File 08's commit validator.

### 2.2 With File 10 (Execution Ledger, Event Stream, and Hooks)

File 10 owns the `Hook` primitive, the closed quality-control `hook_category` set (`validator`, `completion_verification`, `postcondition_check`, `safety_gate`), the four-outcome decision vocabulary, the priority convention (validators at `0`, the approval router at `+100`), the authority classes, the timeout-with-category-aware-fail-direction rule (security-category hooks fail closed; security-category hooks cannot be set to fail open without typed confirmation), hook registration and discovery, and the quality-control ledger and event kinds. File 39 inherits all of those. It does not redefine the hook decision shape, the priority envelope, the fail-direction rule, or the registration mechanics. It specifies how a validator declares its category, boundary, and severity, and how those map onto the hook contract.

### 2.3 With File 04 (Execution and Run Model)

`run.call-pipeline` (File 04 §8.2) places validation at pipeline steps 2 (validate input), 4 (run validators and policy checks), and 9 (validate postconditions). `run.termination` (File 04 §22) defines the completion-verification hook surface and the deterministic completion-forgery guard as the canonical termination floor. `run.completion-contract` (File 04 §2.7) defines the `RunCompletionContract` whose requirement kinds include `validation result`. File 39 owns the validator content that runs at each of those points and the rule by which a required validation becomes a completion requirement on the contract. File 39 does not change the completion-forgery guard, the contract revision authority, or the hook-surface cadence configuration; it supplies what runs on the surface and how a failed required validation prevents `completed`.

### 2.4 With File 05 (Capability Contracts and Registry)

`capability.validation-postconditions` (File 05 §8) declares per-capability `input_validators` (pre-execution), `postconditions` (post-execution), and `stale_state_revalidation`. These are the inline, per-capability special case of a `Validator`: an `input_validators` entry is a validator bound to the `InputProposed` boundary for one capability; a `postconditions` entry is a validator bound to the `PostExecution` boundary for one capability. File 39 generalizes the concept to cross-cutting validators that are not tied to a single capability and unifies their result shape (a `Validation` block) and their gate semantics (§8) with the per-capability case. File 39 does not move the per-capability declarations out of File 05; it consumes them as inline validators and adds the registered cross-cutting validators alongside them.

### 2.5 With File 06 (Capability Policy, Approvals, and Leases)

The line between quality control and policy is fixed and load-bearing. File 06 governs **permission**: whether an invoker is allowed to perform an action, resolved from permission tier, source trust, leases, touched-resource constraints, approval-policy templates, and the permission floor. File 39 governs **quality**: whether an action's input is well-formed and safe-as-content, whether a produced output or artifact is correct, complete, grounded, consistent, and safe-as-content, and whether a run actually achieved its goal. The behavioral and safety policy templates that gate tool choice on permission grounds — `prefer_dedicated_tools`, `fetch_fallback_ban`, `clarify_first_for_multistep`, `todos_for_multistep`, the protected-branch and dangerous-command reusable policy rules (`policy.built-in-reusable-policy-rules`, File 06 §11.5; `policy.approval-policy-templates`, File 06 §12) — are File 06 policy, not File 39 validators; File 39 references them and never duplicates them. Where both a validator and the approval router subscribe to `ToolCallProposed`, the priority convention orders them (validators at `0`, the approval router at `+100`); the validator sees the proposal first and the router decides permission last over the possibly-narrowed proposal. Content safety (an output that contains unsafe material) is a File 39 `SafetyCheck` validator; permission to act is a File 06 decision.

### 2.6 With Evaluation and Benchmarking

File 39 owns the **inline** layer — validators that run during and around live execution and gate it in real time. The Evaluation and Benchmarking spec (File 40) owns the **offline** layer — evaluation suites, benchmarks, regression harnesses, scenario fixtures, golden-artifact comparison, scoring over recorded runs, and judge-prompt optimization. The two layers share the `Validator` primitive and the `Validation`/`Critique` result objects: an offline evaluation suite runs the same validators over recorded inputs and aggregates their outcomes. A single `EvaluationService` spanning inline and offline layers is realized by this split — File 39 is the inline service, File 40 is the offline service, and both consume the same validator and result contracts. File 39 names the surface through which a validator is promoted into an offline suite; File 40 owns the suite, the run record, the scoring aggregation, and the optimization pipeline.

### 2.7 With File 22 (Security, Credentials, and Trust Boundaries)

File 22 owns the security primitives: secret detection and redaction, the untrusted-content and prompt-injection defense, the trust model, and egress governance. File 39 wraps the relevant primitives as `SafetyCheck` validators where they gate output or input quality: a content-safety validator that detects unsafe material invokes File 22's redaction primitive to produce a corrected sibling, and an injection-detection validator over untrusted inbound content runs as a `safety_gate`-category hook. File 39 owns the validator orchestration; File 22 owns the security mechanism the validator calls. A `Secret`-tagged validation payload follows File 22's secret boundary and File 10's never-persist-Secret-to-the-ledger rule (`ledger.forgery-guards`, File 10 §3.7).

### 2.8 With the Per-Surface Specs

Each work surface registers its owned validators through the one registration path and produces the canonical `Validation`/`Critique` blocks: the Coder surface registers type-check, lint, build, and test validators and code-review critiques (File 27); the Data Processor surface registers dataset-schema and data-quality validators and grounded-extraction checks (File 29); the Teacher surface registers grading and rubric validators (File 30); the Web surface registers citation, grounding, and source-quality validators (File 28); the GUI Control and System Agent surfaces register observe-act-verify and post-operation verification validators (Files 31, 32). File 39 defines the canonical baseline and the registration contract; the surfaces specialize. No surface owns a private validation pipeline.

### 2.9 Boundary

File 39 is the inline validation-orchestration layer. It owns no result-block schema, no hook primitive, no completion mechanics, no permission policy, no offline suite, no storage schema, and no UI rendering. It owns the `Validator` primitive, the boundary and severity vocabularies, the gate and correction semantics, the completion-requirement contribution, the baseline validator set, and the quality-control capability surface.

## 3. The `Validator`

Anchor: `qc.validator`

### 3.1 Definition

A `Validator` is a registered, typed, named checking rule that runs at a declared `ValidationBoundary`, evaluates a target through a check backend, and produces a `Validation` or `Critique` result that may gate execution. A validator is the canonical unit of quality control.

A `Validator` is not:

- a separate execution pipeline or DAG node kind — it is a validator-category `Hook` whose handler is a check backend (`run.hook-integration`, File 04 §23.3; `ledger.hook`, File 10 §7)
- a `Validation` block — the block is the result; the validator is the rule that produces it
- an approval-policy template or a permission inspector — those gate on permission and live in File 06; a validator gates on quality
- a capability — a deterministic validator's check backend is a capability, but the validator is the boundary binding plus the severity and correction policy layered over that capability
- an evaluation suite — a suite in the Evaluation and Benchmarking spec (File 40) is an offline collection of validators run over recorded inputs; a validator is a single inline rule

### 3.2 Required Properties

Every `Validator` declaration carries at minimum:

- `validator_id` — a stable, namespaced identifier (per the capability and hook namespacing conventions of `capability.id`, File 05 §13.1)
- `validation_kind` — the `ValidationKind` (per `artifact.validation-critique`, File 09 §14.1) the validator produces (§5)
- `result_kind` — `Validation` (pass/fail/inconclusive) or `Critique` (evaluative findings); a validator produces exactly one result kind
- `boundary` — the `ValidationBoundary` the validator attaches to (§4)
- `severity` — the `ValidationSeverity` (§7.2) that determines what a `Failed` outcome does at the gate; the hook `mode` (`Blocking` or `NonBlocking`, per the hook `mode` of `ledger.hook`, File 10 §7.1) derives from it — a `Blocking` severity registers a blocking hook, and `Advisory` or `Informational` registers a non-blocking one
- `validator_kind` — `Deterministic`, `ModelMediated`, or `UserManual` (per `artifact.validation-critique`, File 09 §14.1)
- `check_backend` — the resolved backend: for `Deterministic`, a registered capability id; for `ModelMediated`, the designated model id plus the policy model-request template id; for `UserManual`, the review-request contract
- `target_input_contract` — the typed validator invocation envelope (§3.3): target reference, target kind, boundary, validation criterion, typed target snapshot or immutable references, included proposal/observation/result payloads, authority classes, relevant run/task/completion criteria, validator declaration version, and relevant settings/profile snapshot
- `backend_effect_envelope` — the backend's touched resources, side-effect class, reversibility class, replay class, isolation/sandbox requirements, killability/cancellation behavior, and egress; a validator backend that reads files, executes code, calls a model, queries the network, observes a GUI, or mutates state inherits the corresponding capability, policy, and sandbox rules
- `applicability` — a typed predicate naming which targets the validator applies to (target block kinds, artifact kinds, capability families, claim kinds, surfaces, scopes), evaluated declaratively against the target and world-model snapshot
- `inconclusive_policy` — for `Blocking` validators, the declared treatment of `Inconclusive` outcomes (§8.2), defaulting to gate/fail-closed
- `correction_policy` — the `CorrectionPolicy` (§9) governing whether and how the validator may propose a correction
- `authority_class` — the hook authority (`observe_only`, `narrowing_only`, `allow_capable`, `substitute_capable`; per `ledger.authority-classes`, File 10 §7.4); quality-control validators default to `narrowing_only`
- `enabled` and `settings` references — the scoped enablement and threshold/fail-direction configuration (§18), resolved through the canonical settings stack
- `source` — the typed source (`Builtin`, `Subsystem`, `Plugin`, `McpServer`, `Api`, `UserDefined`; per `capability.capability-source`, File 05 §9.1)

A declaration lacking any of these is invalid and is rejected at registration.

### 3.3 Typed Invocation Envelope

A validator receives typed target data, not arbitrary prompt text or hidden subsystem state. The runtime constructs a validator invocation envelope from the target and boundary: `target_ref`, `target_kind`, `boundary`, validation criterion, immutable target snapshot or snapshot references, relevant proposal/observation/result payloads, content authority classes, required typed references, applicable run/task success criteria and completion contract fragments, validator declaration version, and relevant settings/profile snapshot. A validator may render this envelope into a model request or tool input internally, but the canonical quality-control contract is typed data first. A validator that needs subsystem-private state must be registered by the subsystem that owns that state; File 39 does not open a second access path.

### 3.4 The Validator Is a Hook Whose Handler Is a Check

A validator registers as a `Hook` (per `ledger.hook-registration-discovery`, File 10 §8). The hook's `event_kinds` and `payload_filter` resolve from the validator's `boundary` and `applicability`; the hook's `handler` invokes the `check_backend`; the hook's returned `HookDecision` is computed from the produced `Validation` block's `ValidationOutcome` and the validator's `severity` (§8). The validator declaration is the quality-control-layer object; the hook is its registration; the `Validation` block is its result; the capability or model is its backend. There is no validator object that is not, at runtime, a registered hook.

### 3.5 Boundary

The validator declaration defines the rule. The hook registry holds the live subscription. The check backend implements the check. The block pool holds the result. The policy layer is unaffected. None of those layers invents new validator semantics; they consume what this file defines. A capability whose handler internally performs checks is not thereby a validator; it becomes a validator only when its check is registered at a boundary and produces a `Validation` block. Internal sub-mode validation inside a capability (a write capability that internally checks its argument before writing) is the capability's own concern and need not be a registered validator unless its result is meant to gate or be inspected as a `Validation`.

## 4. `ValidationBoundary`

Anchor: `qc.validation-boundary`

### 4.1 Definition

A `ValidationBoundary` names where in the execution lifecycle a validator attaches. The set is closed and maps onto the canonical hookable boundaries (`ledger.priority-ordering`, File 10 §7.3; the blocking hook dispatch of `ledger.hook`, File 10 §7.1, and the commit hookability of `version.events`, File 11 §21.3) and the capability-call pipeline (`run.call-pipeline`, File 04 §8.2). A validator declares exactly one boundary.

### 4.2 The Closed Set

- `InputProposed` — before a proposed capability invocation executes, on the proposal boundary (`ToolCallProposed`). The target is the proposed call and its resolved arguments and touched resources. Used for argument well-formedness beyond schema, structural input validation (parsed-command safety, path-safety, stale-state currency), and content-safety of inputs. A blocking validator here may `Block`, `RedirectSuggestion`, or narrow via `Substitute` (§8.2, §9.3). This boundary co-resides with the approval router; validators run first (priority `0`), the router last (priority `+100`).
- `PostExecution` — after a capability executes, on the execution-completed boundary (`ToolCallExecuted`). The target is the call's observed result. Used for postcondition verification (`capability.validation-postconditions`, File 05 §8.2): declared output-schema conformance, resource-state checks, and observe-act-verify confirmation that the action had its declared effect.
- `PreCommit` — before a block, artifact version, or claim commits, on the commit boundary (`BlockCommitted`/`VersionCommitted` interception; commit hookability per `version.events`, File 11 §21.3). The target is the staged output. Used for output validation that must gate the durable landing of the output (format conformance, artifact structural validity, claim-grounding before publication). A blocking validator here prevents the commit and returns typed feedback in-band.
- `PostOutput` — after an agent turn or generation completes, on the turn-completed boundary (`AgentTurnCompleted`). The target is the committed output of the turn. Used for output quality checks that observe the whole turn (consistency, factuality, content-safety, behavioral conformance) and that may propose a non-destructive correction (§9).
- `Completion` — at run termination, on the run-status-to-completed boundary, as a completion-verification check (`run.termination`, File 04 §22). The target is the run and its outputs against the `RunCompletionContract`. Used to verify that required validations passed and that the run achieved its declared goal. A required `Completion`-boundary validation that fails prevents `completed` (§14).
- `Streaming` — incrementally during generation, on the streaming-partial boundary, batched (§13). The target is the accumulating partial output. Used for early detection of violations during long generations; runs only cheap synchronous checks inline and surfaces real-time advisories; the authoritative validation runs at `PostOutput` on the complete output.

### 4.3 Boundary Selection

A validator's boundary is determined by what it validates and when blocking is useful:

- structural input checks and pre-execution safety gates use `InputProposed`
- declared postconditions and observe-act-verify use `PostExecution`
- output checks that must gate a durable landing use `PreCommit`
- output quality checks that observe the whole turn and may correct use `PostOutput`
- goal-achievement and required-validation checks use `Completion`
- long-generation early warning uses `Streaming`

A single quality concern may be served by validators at more than one boundary (a grounding concern may run a cheap `Streaming` advisory and an authoritative `PostOutput` check). Each boundary attachment is its own validator declaration.

### 4.4 Boundary

The boundary set is closed for runtime interoperability (`core.closed-canonical`, File 01 §6.16). A validator that needs a boundary not in this set either uses a registered `Custom` hook event (per `ledger.hook`, File 10 §7.1) declared by its owning subsystem and maps it to the nearest canonical boundary semantics, or the canonical set is revised in a later spec. Ad-hoc boundaries outside the hook surface are an Explicit Rejection (§21).

## 5. `ValidationKind` and the Structural-Semantic Taxonomy

Anchor: `qc.validation-kind-taxonomy`

### 5.1 Reuse of File 09's `ValidationKind`

A validator's `validation_kind` is drawn from the closed `ValidationKind` set already canonical in `artifact.validation-critique` (File 09 §14.1): `Postcondition`, `TypeCheck`, `Lint`, `Test`, `EvaluatorScore`, `SchemaValidation`, `CitationCheck`, `FactualityCheck`, `ConsistencyCheck`, `SafetyCheck`, and `Custom { namespace, name }`. File 39 introduces no new validation kinds; it organizes the existing set into a taxonomy that drives boundary, validator-kind, and latency defaults.

### 5.2 Structural Validators

A structural validator decides its outcome from parsing, schema-matching, deterministic computation, or comparison against a recorded fact. Structural kinds: `SchemaValidation`, `TypeCheck`, `Lint`, `Postcondition`, and the deterministic forms of `CitationCheck` (source-span alignment) and `Test` (a test process exit result). Structural validators:

- are `Deterministic` `validator_kind`
- are eligible for `Blocking` mode at the `InputProposed`, `PostExecution`, and `PreCommit` boundaries because they are cheap enough to run within the blocking-hook budget
- produce a reproducible outcome for the same target and recorded inputs (`deterministic_replayable`; §19)

Structural validation is the default for input-shape, output-format, postcondition, and well-formedness checks. The latency posture is "run inline; block on failure."

### 5.3 Semantic Validators

A semantic validator decides its outcome from a model judgment or an expensive analysis. Semantic kinds: `FactualityCheck`, `ConsistencyCheck`, `SafetyCheck` (model-graded), `EvaluatorScore`, and the model-mediated forms of `CitationCheck`. Semantic validators:

- are usually `ModelMediated` (`UserManual` for human review)
- default to `NonBlocking` at the `PostOutput` boundary, or to the deferred/parallel completion-verification cadence (`run.termination`, File 04 §22), because a model call typically exceeds the blocking-hook budget
- may be `Blocking` only when their cost fits the configured budget for the boundary, or when the run is configured to wait for them at `Completion`
- record their model identity, policy model-request template, and input snapshot for replay (§10.5, §19)

Semantic validation is the default for grounding-beyond-alignment, factuality, content-safety judgment, cross-turn consistency, and quality scoring. The latency posture is "run in background or at completion; surface as advisory unless explicitly configured to gate."

### 5.4 The Cheap-Deterministic-First Rule

Where a quality concern admits a deterministic check, the deterministic check is preferred over a model-mediated one. Grounding is the canonical example: a citation or extraction whose text can be aligned to an exact source span is validated deterministically (the alignment either succeeds or yields no span); only the residue that cannot be aligned needs a model judgment. A validator author chooses the model-mediated form only when no deterministic check expresses the concern. This keeps the common case cheap, blocking-eligible, and reproducible, and reserves model calls for genuinely semantic judgments.

### 5.5 Boundary

The taxonomy classifies; it does not extend the kind set. The Evaluation and Benchmarking spec (File 40) reuses the same kinds in offline suites. Surfaces and subsystems declare which kinds their owned validators produce. The `Custom` kind is registered through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2) and declares its structural-versus-semantic classification so the runtime can choose its blocking and latency defaults.

## 6. `validator_kind` and the Model-Mediated Judge Discipline

Anchor: `qc.judge-discipline`

### 6.1 The Three Validator Kinds

`validator_kind` is reused from `artifact.validation-critique` (File 09 §14.1):

- `Deterministic` — the check is a registered capability that computes a verdict from the target and recorded inputs; the verdict is reproducible
- `ModelMediated` — the check is a designated model evaluating the target against a configured policy model-request template; the verdict carries the model's reasoning and a confidence the validator records
- `UserManual` — the check is a human reviewer applying a verdict through the review-request contract; it is never a synchronous blocking hook during generation and is used for explicit review, advisory/asynchronous validation, or user-triggered validation

### 6.2 The Judge Discipline

A `ModelMediated` validator is a judge. The system ships the judge machinery — the `ModelMediated` validator slot, the policy model-request template surface, the annotation and optimization handoff to the Evaluation and Benchmarking spec (File 40) — but it does not ship a built-in general-purpose judge as a default validator. The following discipline is canonical for every `ModelMediated` validator, built-in or user-authored:

- **Narrow, not omnibus.** A judge validates one error mode (one failure cluster derived from observed traces), not "is this good." Each error mode gets its own judge. An omnibus judge cannot be calibrated and is rejected (§21).
- **Context-isolated by default.** A judge receives an isolated, validation-relevant context through a fresh model invocation: the validation criterion, run/task success criteria and completion contract where relevant, the target artifact or block, cited evidence and source excerpts with authority classes, and required typed references. It does not inherit the producer's intermediate reasoning, self-justification, or unrelated conversation history unless the validator explicitly opts in and its declaration says why. Isolation is configurable per validator, but inherited producer reasoning is never the default.
- **Verdict shape is `ValidationOutcome` or a small closed enum, never a continuous score.** A judge returns `Passed`/`Failed`/`Inconclusive` (or, for an `EvaluatorScore` validator, a small mutually-exclusive closed class set declared on the validator). It does not return a 1-to-5 or 0-to-1 numerical score as its verdict. Continuous quality figures are aggregates computed downstream over many validations (the proportion passing a given validator over a window; §17, §18), never a per-validation surfaced score. An optional numerical `confidence` may accompany a verdict for ranking and threshold purposes (mirroring `confidence_score` on claims and evidence, `artifact.claim` (File 09 §9.2)), but confidence is not the verdict.
- **Verdict plus reasoning, never verdict alone.** A `ModelMediated` validation records the verdict and the model's reasoning. The reasoning is required for transparency, for user adjudication of false positives, and for the offline optimization loop that learns the implicit policy from annotated examples.
- **Provider-agnostic.** A judge is wired through the model-strategy and provider layers (Files 16, 17); it is never coupled to one provider's API.

### 6.3 Why No General-Purpose Built-In Judge

A built-in "general correctness judge" or "general hallucination judge" surfaced as a default validator reads as a feature but is actively harmful: if the producing model could reliably detect its own incorrect output, it would not have produced it. Shipping such a default hands the user a green light that does not track reality. The system therefore ships only the machinery and a set of narrow, mostly-deterministic baseline validators (§15.1); semantic judges are authored per failure mode by the user, by a surface, or by a plugin, calibrated against observed traces, and registered like any other validator.

### 6.4 Boundary

The judge discipline constrains validator declarations; it does not define the offline optimization pipeline that calibrates a judge against annotated traces — that pipeline is a long-running evaluation run owned by the Evaluation and Benchmarking spec (File 40), gated by explicit user invocation, with cost preview. File 39 owns the registration of the resulting judge as a validator and the inline execution of that judge against live targets.

## 7. Outcome, Severity, and Findings

Anchor: `qc.outcome-severity-findings`

### 7.1 Outcome

A validator's result outcome is the closed `ValidationOutcome` from `artifact.validation-critique` (File 09 §14.1): `Passed`, `Failed`, `Inconclusive`. A `Critique`-producing validator does not carry an outcome; it carries findings (§7.3) and an optional `recommended_action`, and it never gates state (`artifact.validation-critique`, File 09 §14.4). File 39 introduces no new outcome values.

### 7.2 `ValidationSeverity`

`ValidationSeverity` is a closed canonical set declared on a validator that determines what a `Failed` outcome does at the gate:

- `Blocking` — a `Failed` outcome gates: at a pre-action boundary it denies, redirects, or narrows the action; at a commit boundary it prevents the commit; at the completion boundary it prevents `completed`. Blocking validators are security-category hooks and fail closed (the hook timeout-and-fail-direction rule, File 10 §7.5).
- `Advisory` — a `Failed` outcome records the `Validation` (or a `Critique`) and surfaces a violation to the user and the agent, but never blocks. The agent may act on the advisory in-band; the user may act on it asynchronously.
- `Informational` — the validation is recorded for inspection and metrics only; no violation is surfaced and nothing is gated.

Severity is distinct from outcome. Outcome answers "did the check pass." Severity answers "what happens when it does not." A `Blocking` validator that returns `Passed` proceeds silently; the same validator returning `Failed` gates. An `Advisory` validator that returns `Failed` flags without gating. This separation lets the same check run as a gate in one profile and as a flag in another (§18) without changing the check.

The legacy three-level violation vocabulary (`Error`/`Warning`/`Info`) maps onto `(outcome, severity)`: an `Error` is a `Failed`+`Blocking` validation; a `Warning` is a `Failed`+`Advisory` validation; an `Info` is a `Passed` or `Failed`+`Informational` validation. File 39 uses `(outcome, severity)` rather than a single conflated level so that the gate decision is explicit and configurable.

### 7.3 Findings

A `Failed` `Validation` carries `failure_details` (the rule violated, the expected value, the actual value; per `artifact.validation-critique`, File 09 §14.1). An `Inconclusive` `Validation` carries `inconclusive_reason`. A `Critique` carries a structured `findings` list (each with severity, location reference, description, and optional suggested resolution; per `artifact.validation-critique`, File 09 §14.1) and an optional `recommended_action`. File 39 introduces no parallel finding object; the failure and finding contracts on the `Validation` and `Critique` blocks are the canonical violation record. A "violation" in this file is a `Failed` `Validation` (or a `Critique` finding) that has been surfaced; `QualityControlViolationDetected` (`ledger.entry-kind-catalogue`, File 10 §4.1) records its surfacing.

### 7.4 Severity Taxonomy for Critiques

A `Critique` finding may carry a finer review-severity (a critical/important/suggestion/nit gradation) within its structured findings, for review-panel presentation. This finer gradation is presentation metadata on the finding; it does not change the `ValidationSeverity` gate semantics, because critiques never gate (§7.1). A critique that a reviewer wants to be blocking is expressed by the reviewer running (or requiring) a corresponding `Validation` whose outcome gates (`artifact.validation-critique`, File 09 §14.4).

### 7.5 Boundary

Outcomes and findings are block content owned by File 09. Severity is the File 39 gate-policy layer over the outcome. The presentation of severity (badges, colors, panels) is owned by Files 37 and 38.

## 8. The Validation Gate

Anchor: `qc.validation-gate`

### 8.1 Definition

The validation gate is the deterministic mapping from a validator's `(outcome, severity, boundary, authority)` to a hook decision or a completion-requirement effect. The gate is what makes a blocking validator gate and an advisory validator merely record.

### 8.2 Gate Semantics by Boundary

For a `Blocking` validator:

- at `InputProposed`: `Failed` produces `Block { reason, error_kind }` by default; the typed denial flows in-band as a tool result per `run.denial-is-in-band` (File 04 §8.3) and the agent loop receives it and may self-correct, narrow, or stop. A validator with `narrowing_only` authority may instead return `RedirectSuggestion { capability_id, args, reason }` (suggest a safer capability) or `Substitute { new_payload, substitution_kind }` restricted to `narrowing_only` or `redaction` substitutions (narrow a path, redact a secret argument); a semantic change to what the agent intended requires `Block`, never silent `Substitute` (`ledger.hook-decision-vocabulary`, File 10 §7.2).
- at `PostExecution`: `Failed` records the postcondition-failure `Validation`; the failure flows in-band as a typed result and may trigger declared compensation per the capability's `reversibility_class` (`capability.execution-semantic-fields`, File 05 §3.6) and the recovery strategies of `run.recovery` (File 04 §20.2). A `PostExecution` validator does not retroactively un-execute the call; it records the failed postcondition and drives recovery.
- at `PreCommit`: `Failed` prevents the staged block/artifact/claim from committing; the typed reason flows in-band; no `ArtifactVersion` is created (consistent with the staged-partial discard rule of `run.streaming-partial-execution`, File 04 §12). The agent may produce a corrected version (§9).
- at `PostOutput`: `Failed` records the `Validation` and may drive a non-destructive correction (§9); because the output has already committed at this boundary, the gate effect is correction-via-sibling, not prevention.
- at `Completion`: a `Failed` required validation prevents the run from terminating `completed` (§14); the run continues, pauses for user input, or terminates `failed` per the completion contract.

For a `Blocking` validator whose outcome is `Inconclusive`, the validator's declared `inconclusive_policy` applies and defaults to gate/fail-closed. A weaker policy such as proceed-as-advisory requires explicit configuration and is forbidden for required validations, security or policy-floor validators, and typed-confirmation gates. `Inconclusive` is a valid verdict, not a backend timeout or handler error (§8.3), and it is never silently treated as `Passed`.

For a `NonBlocking` (`Advisory` or `Informational`) validator at any boundary: the validation is recorded and (for `Advisory`) the violation surfaced; the emitter does not wait and nothing is gated (`ledger.hook`, File 10 §7.1 non-blocking observation).

### 8.3 Fail-Direction

A `Blocking` validator is a security-category hook and follows the hook timeout-and-fail-direction rule (File 10 §7.5): on timeout or handler error the synthesized decision is `Block` (fail closed). A user may override a specific validator's fail-direction only within policy limits, and a security-category validator may not be set to fail open without typed confirmation. An `Advisory` or `Informational` validator fails open with a warning, because its absence cannot permit an unsafe action. Per-error-class retry is governed by the validator's configured retry policy within the safety guard; no retry count is hardcoded by this file.

### 8.4 Validator Chain Aggregation

At a boundary, every applicable validator either produces a result or an explicit diagnostic explaining why it did not run, such as `PriorBlockingDecision`, `BudgetExceeded`, `DisabledBySetting`, or `NotApplicable`. Implementations may short-circuit expensive downstream checks after a decisive blocking result, but a report must never imply that skipped validators passed. The gate decision is the most restrictive decisive result produced by the applicable chain, and skipped validators remain visible in the decisive-chain record.

### 8.5 Determinism of the Gate

Given a `Validation` block, the validator's declared severity, and the boundary, the gate decision is deterministic. The mapping above is the contract; an implementation that produces a different gate decision for the same inputs is an Explicit Rejection (§21). The decisive validator chain and the resulting decision are recorded in `QualityControlValidatorRan` and `HookDecisionRecorded` (`ledger.entry-kind-catalogue`, File 10 §4.1) for inspection and replay.

### 8.6 Boundary

The gate consumes the hook decision vocabulary and authority rules owned by File 10 and the completion contract owned by File 04. File 39 specifies the mapping from validator result to gate effect. The execution of the resulting decision (denying the call, preventing the commit, holding the run) is owned by File 04's executor.

## 9. The Non-Destructive Correction Model

Anchor: `qc.correction-model`

### 9.1 Principle

A correction never silently mutates a produced output in place. Corrections are non-destructive by default, consistent with `core.non-destructive-by-default` (File 01 §7.13). A correction either returns a typed in-band signal that the agent acts on, narrows or redacts a not-yet-executed proposal, or produces a sibling version that preserves the original. The legacy pattern of mutating the generated response in place before the user sees it is rejected (§21); the system corrects by branching, not by overwriting.

### 9.2 `CorrectionPolicy` and `CorrectionConfidence`

A validator declares a `CorrectionPolicy`:

- `None` — the validator never proposes a correction; a `Failed` outcome only gates or flags
- `Suggest` — the validator proposes a correction as a candidate the user or agent may adopt; the original is always preserved
- `AutoApplyAsCurrent { confidence_floor: High | Medium }` — the validator's correction, when its `CorrectionConfidence` is at or above the floor, becomes the current version while the original is preserved as a sibling; below the floor, the correction is offered as a candidate (`Suggest` behavior)

`CorrectionConfidence` is a closed set: `High` (the correction is mechanical and unambiguous — extracting a JSON object from surrounding prose, redacting a detected secret, normalizing a malformed argument), `Medium` (the correction is reliable but worth surfacing — redacting probable personal data, reflowing a flagged phrase), `Low` (the correction is a judgment the user should adjudicate — a factuality or consistency rewrite). An `AutoApplyAsCurrent` correction applies only when the correction confidence is at or above the configured floor. `Low` corrections are always `Suggest` (offered as an alternative, never auto-applied).

### 9.3 Correction by Boundary

- **Pre-execution (`InputProposed`):** a correction is a `Substitute` (narrowing or redaction only) or a `RedirectSuggestion`; the not-yet-executed proposal is shaped before it runs, and no durable output exists to branch. Semantic changes require `Block` plus agent self-correction, not silent substitution.
- **Output (`PostOutput`, `PreCommit`):** a correction produces a sibling version (per the version graph, File 11, and the artifact version chain, `artifact.version-creation`, File 09 §6.3). Under `AutoApplyAsCurrent` with sufficient confidence, the corrected sibling becomes current and the original is preserved as a reachable sibling branch; under `Suggest` or low confidence, the original remains current and the correction is offered as a candidate sibling the user may switch to. In both cases the original is preserved, the change is forensically inspectable (what was corrected and why, via the `validated_by` and `derives_from` edges), the correction is one-click reversible (switch versions), and multiple validators that each propose a correction compete gracefully as distinct sibling candidates rather than overwriting one another. When more than one correction qualifies for `AutoApplyAsCurrent` on the same target in a single pass, none auto-applies — the runtime cannot elect a single current version between competing confident fixes, so all qualifying corrections fall back to `Suggest` and the user chooses which sibling becomes current.
- **Execution failure (`PostExecution`):** the correction is recovery, not output rewriting — a typed error in-band drives the agent's recovery (`run.recovery`, File 04 §20.2) or declared compensation; the validator records the failed postcondition.

### 9.4 Correction Re-Validation and Non-Convergence

A correction sibling is itself a validation target. After a correction is produced, applicable validators re-run against the corrected sibling under the same typed invocation and replay rules as any other target. Correction cascades are bounded by the configured correction-iteration depth per target. If validators conflict, produce no progress across iterations, or would oscillate between sibling candidates, the runtime stops auto-application and falls back to `Suggest` or user adjudication rather than continuing the cascade. This mirrors the bounded recovery discipline of `run.recovery` (File 04 §20.2).

### 9.5 Corrections Are Capability Invocations

A correction that produces a sibling version is itself a capability invocation (an `artifact.commit_version`, a `claim.publish` supersession, a block commit) and goes through the full capability-call pipeline, policy, and ledger. There is no hidden correction path that bypasses policy or the ledger. A correction inherits the permission tier of the mutation it performs; a correction that would cross a permission boundary surfaces approval like any other call.

### 9.6 Precision Over Recall

The default correction posture is precision over recall: a false correction is worse than a missed violation, because a confident wrong "fix" erodes trust more than a flagged-but-uncorrected issue. Auto-apply is therefore reserved for `High`/`Medium` confidence; everything uncertain is surfaced as a candidate. This posture is a configurable default (§18), not a hardcoded rule; a profile may lower the auto-apply floor where the cost of a false correction is low.

### 9.7 Boundary

The correction model consumes the version graph (File 11), the artifact version chain (File 09), the hook decision vocabulary (File 10), and the recovery strategies (File 04). File 39 specifies the correction policy, the confidence gradation, and the non-destructive sibling-branch contract. The presentation of a correction (the "switch to correction" affordance, the alternative-candidate toast, the diff between original and corrected) is owned by Files 37 and 38.

## 10. Validator Registration, Sourcing, and Trust

Anchor: `qc.validator-registration`

### 10.1 One Registration Path

A validator registers through the one capability-and-hook registration path (`capability.runtime-mutation`, File 05 §16.2; `ledger.hook-registration-discovery`, File 10 §8) under the proposal-first source-approval flow (`policy.source-approval-flow`, File 06 §9). There is no parallel validator registry. The check backend registers in the Capability Registry (for `Deterministic` validators) or resolves through the model-strategy layer (for `ModelMediated` validators); the boundary binding registers as a validator-category hook; the validator declaration ties them together. The catalogue of validators is the set of validator-category hooks in the one hook registry, attributed to their sources.

### 10.2 Sourcing

- **Built-in validators** ship as built-in capabilities plus built-in hook subscriptions registered at startup through the same capability/hook machinery as every other validator (the baseline set, §15.1). Built-in source identity changes defaults and trust, not the registration path.
- **Subsystem validators** register when the owning subsystem loads. The subsystem owns its validators and registers them itself; the quality-control layer does not duplicate subsystem access (the Memory subsystem registers its consistency and preference validators; the Coder surface registers its type-check, lint, and test validators; and so on).
- **Plugin validators** register through the plugin contribution path (File 35) under source-approval and trust narrowing; a plugin's `[plugin.quality_control.defaults]` contribution seeds per-profile validator defaults (§18).
- **User-authored validators** register through a validator-registration capability (a `UserApproval`-tier call under source-approval) or as a `Validator`-kind artifact (`artifact.artifact-kind`, File 09 §4.1) the user or agent authors and installs. The agent may draft and propose a validator; it may never self-install one without user approval.

### 10.3 Trust and Authority

A validator's authority is bounded by its source's effective trust (`capability.trust-source-approval-flow`, File 05 §9.2) and the hook authority classes (`ledger.authority-classes`, File 10 §7.4). Community, unverified, plugin, MCP, API, and user-defined validators default to `narrowing_only` authority until the user explicitly upgrades them through source approval — a validator from an untrusted source may flag, block, redirect, or narrow, but may not produce an `allow_capable` decision that overrides a stricter prior decision, and may never bypass a permission floor, typed-confirmation requirement, contradiction detection, or touched-resource constraint. A `Blocking` validator from any source still fails closed within its authority.

### 10.4 The Per-Capability Inline Special Case

A capability's declared `input_validators` and `postconditions` (`capability.validation-postconditions`, File 05 §8) are inline validators: each is a validator bound to the `InputProposed` or `PostExecution` boundary for that one capability, declared on the capability rather than registered as a free-standing hook. They produce `Validation` blocks and gate per §8 exactly like registered validators. File 39 unifies them with the registered cross-cutting validators under the `Validator` concept: a `ValidationReport` (§12) over a capability invocation includes both the capability's inline postcondition validations and any cross-cutting validators that fired. The inline declaration remains File 05's; the unification is File 39's.

### 10.5 Replay Keying for Model-Mediated Validators

A `ModelMediated` validation records, on its `Validation` block and ledger entry, the keying required to replay it without re-querying the model: the `ModelSelectionRecord`, resolved model identity and profile, policy model-request template id and version, validator declaration version, relevant settings/profile snapshot, canonical model-request assembly snapshot or immutable source references sufficient to reconstruct it, provider request/response metadata where File 17 records it, and the produced verdict, reasoning, and confidence carried on the `Validation` block per `artifact.validation-critique` (File 09 §14.1), together with any declared nondeterminism. Historical reconstruction reads the recorded verdict; it never re-invokes the model (the `provider.token-source` reconstruction rule, File 17). A replayed run reproduces the recorded validation outcome modulo explicitly-typed model-mediated nondeterminism, which is recorded rather than re-derived (§19).

### 10.6 Boundary

Registration mechanics are owned by File 05 (capability side) and File 10 (hook side); source-approval and trust are owned by File 06; plugin packaging is owned by File 35. File 39 specifies the validator declaration the registration carries and the trust/authority rules specific to validators.

## 11. Quality Control Does Not Duplicate Permission, Security, or Subsystem Logic

Anchor: `qc.no-duplication`

### 11.1 Against Permission Duplication

A validator does not re-implement permission policy. Permission tier resolution, approval flows, leases, and the behavioral and safety policy templates are File 06's. A quality validator that needs an action blocked on permission grounds defers to the approval router; a quality validator blocks on quality grounds (the content is unsafe, the output is malformed, the claim is ungrounded). Where a concern is genuinely both (a dangerous command is both a permission concern and a content-safety concern), the permission aspect is a File 06 reusable policy rule and the content aspect is a File 39 `SafetyCheck` validator; they compose at the shared `InputProposed` boundary by priority.

### 11.2 Against Security Duplication

A validator does not re-implement secret detection, redaction, or injection defense. Those primitives are File 22's. A `SafetyCheck` validator invokes them; it owns the orchestration (when to run, what to gate, how to correct), not the mechanism.

### 11.3 Against Subsystem Duplication

A validator does not reach into a subsystem's private state to check it. The subsystem registers its own validators with the access it already has (the Memory subsystem checks consistency against stored facts because it owns memory access; the quality-control layer does not open a second memory path). The quality-control layer provides the validator primitive, the boundaries, the gate, and the correction model; the subsystems provide the owned checks.

### 11.4 Boundary

This section is a no-private-architecture rule for the quality-control layer, mirroring the no-private-architecture invariants of `worksurface.no-private-architecture` (File 25 §12) and the per-surface specs. Validation is a cross-cutting service realized through existing registries and existing subsystem access, never a parallel surveillance layer.

## 12. `ValidationReport`

Anchor: `qc.validation-report`

### 12.1 Definition

A `ValidationReport` is a derived aggregation view over the `Validation` blocks linked to a target (a run, an artifact version, a claim, a turn, or a block) by File 09's validation target relation and over `Critique` blocks whose canonical target is the same target. It is the canonical answer to "what was checked, what passed, what failed, what remains inconclusive, and what review findings exist" for a target. It is named among run outputs by `run.output-semantics` (File 04 §24) and returned among child-run merge forms by `run.merge` (File 04 §16.4).

### 12.2 Derivation, Not Storage

A `ValidationReport` is computed on read from the underlying `Validation`/`Critique` blocks, exactly as `Provenance` is computed over the block graph (`artifact.provenance`, File 09 §15). It is not a stored primitive and not a parallel report ledger. Its computation:

- collects `Validation` blocks linked to the target through File 09's validation target relation and `Critique` blocks whose canonical target is the same target
- derives the target's `ValidationState` from `Validation` blocks only, per `artifact.validation-state-derivation` (File 09 §14.2); critiques contribute findings and recommended actions, not state
- summarizes pass/fail/inconclusive counts, the set of decisive `Failed` validations with their `failure_details`, the set of `Critique` findings, the severity rollup, and the per-validator outcomes
- carries a `truncated` flag plus `truncation_details` when aggregation bounds (§18) were hit: which dimension hit the bound, which relation or kind was truncated, and whether decisive failed validations were included before truncation

A truncated report is not proof that no additional failures exist beyond the bound.

Caching the report is a storage optimization; the underlying blocks are the source of truth, and cache invalidation is event-driven on new validation commits (mirroring `artifact.provenance`, File 09 §15.4).

### 12.3 Determinism

Given the same target and the same block-pool, version-graph, and ledger snapshots, two `ValidationReport` computations return identical results. This is the load-bearing property for replay and audit. A `ValidationReport` over recorded inputs is what an offline evaluation suite aggregates.

### 12.4 Boundary

The report is a query surface over File 09's result blocks. File 39 specifies the aggregation contract; File 09 owns the blocks and the `ValidationState` derivation; Files 37 and 38 render the report as a badge, a panel, or a timeline; the Telemetry, Logging, and Observability spec (File 41) consumes the validation blocks and QC ledger entries these reports aggregate.

## 13. Real-Time and Streaming Validation

Anchor: `qc.streaming-validation`

### 13.1 The `Streaming` Boundary

A validator bound to the `Streaming` boundary runs incrementally on the accumulating partial output during a long generation, batched (a configured token or character cadence, not per token). Streaming validation exists to surface violations early on long outputs; it is not the authoritative check.

### 13.2 Constraints

Streaming validation must not stall the stream. Therefore:

- only `Deterministic`, synchronous, cheap validators run inline on the streaming boundary; a `ModelMediated` validator over streamed output runs in the background and does not hold the stream
- a streaming-detected violation surfaces in real time as an `Advisory` (it informs the user and may inform the agent), but the authoritative validation runs at `PostOutput` over the complete output, and the gate decision (§8) is taken there, not mid-stream
- a streaming advisory is provisional: it is superseded, retracted, or confirmed when the authoritative `PostOutput` validation runs, or when the partial output it referenced is revised by generation; it never persists as a standing violation past the authoritative check without reconciliation
- the streaming batch cadence and the set of streaming-eligible validators are settings (§18), not hardcoded

### 13.3 Unverified-Partial Discipline

Where a generation's earlier portion has been compacted or summarized, the summarized portion is marked unverified, and a completion or output validator must not treat a summarized step as a confirmed completed step unless the producer independently confirmed it. This discipline prevents a forged completion claim derived from summarized rather than confirmed work; it complements the deterministic completion-forgery guard (§14) at the content level.

### 13.4 Boundary

Streaming delivery, partial-commit boundaries, and aggregation/pacing are owned by File 10 (`ledger.streaming-live-partials`) and File 37 (streaming presentation). File 39 specifies which validators may run on the streaming boundary, the advisory-only-mid-stream rule, and the authoritative-at-`PostOutput` rule.

## 14. Completion Verification

Anchor: `qc.completion-gate`

### 14.1 The Completion Floor and the Verification Extension

The deterministic completion-forgery guard (`run.termination`, File 04 §22; `ledger.forgery-guards`, File 10 §3.7) is the canonical termination floor: a run whose `RunCompletionContract` required action cannot terminate `completed` without ledgered evidence of action. File 39 does not change this floor; it owns the opt-in extension that runs richer validators at the `Completion` boundary through the completion-verification hook surface.

### 14.2 Required Validations as Completion Requirements

A validation becomes a completion requirement when something with sufficient authority adds a `validation result` requirement to the run's `RunCompletionContract` (`run.completion-contract`, File 04 §2.7). The authorities that may do so:

- a capability declares a required postcondition validation, which the contract records when the capability is invoked
- a surface or subsystem declares a default required validation for a kind of work (the Coder surface may require that a code-artifact's tests pass before the artifact is `Validated`; the Web surface may require that a published claim is grounded)
- a policy or user requirement adds a required validation (a profile that requires factuality validation on cited reports before completion)
- a workflow or automation declares a required validation in its body (File 34) or its `validation_policy` (File 33 §6.2, §14.1)

A run whose contract carries a required validation cannot terminate `completed` until a `Validation` block for that requirement exists with outcome `Passed`. A required validation that is `Failed` or remains `Inconclusive` holds the run in `running`, drives it to ask the user, or terminates it `failed` per the contract; it never silently allows `completed`. A required validation is satisfied only by a `Passed` validation matching the requirement's declared target, kind, accepted validator identity or class, minimum trust/authority, severity, and version-compatibility rule. A weaker validator, advisory-only validator, stale validator, or insufficient-trust validator cannot satisfy a stronger completion requirement. The version-compatibility rule defaults to exact-target-version: a `Passed` validation satisfies the requirement only for the exact artifact version or claim revision it validated, and a validation of a superseded version satisfies the requirement only under a compatibility relation the requirement declares (for example, one marking a non-semantic or metadata-only revision as inheriting the prior version's validation); absent such a relation, a new version requires re-validation. The required validation requirement is itself subject to the contract's monotonicity and forgery guards: the executing agent may add but never remove or weaken its own required validations (`run.completion-contract`, File 04 §2.7).

### 14.3 Cadence

The completion-verification surface runs at the user-configured cadence inherited from `run.termination` (File 04 §22): every N steps, in parallel as a background observer, sequentially before completion, or only at explicit `verify_now` invocation. A `Blocking` `Completion` validator runs sequentially before completion (it must pass for `completed`); a `NonBlocking` completion-verification validator runs in parallel and surfaces advisories. The deterministic floor always runs; the richer validators are opt-in per task, surface, and profile, and default to disabled (consistent with `run.termination`, File 04 §22).

### 14.4 Goal-Achievement Verification

A `Completion` validator may be a model-mediated check of whether the run achieved the user's goal (the "did it actually do what was asked" check), evaluated against a per-task expected outcome. This goal-achievement judge follows the judge discipline (§6): it is narrow, returns `Passed`/`Failed`/`Inconclusive` with reasoning, and is off by default. It is the canonical mechanism against the failure mode where the model "answers fluently" but the task state is unresolved — but it is an extension, not the floor, because the deterministic forgery guard already prevents the trivial forged completion.

### 14.5 Boundary

The completion contract, the forgery guard, the hook-surface cadence, and the run lifecycle are owned by File 04. File 39 owns the validator content that runs at the `Completion` boundary and the rule by which a required validation becomes a contract requirement.

## 15. Baseline and Surface Validators

Anchor: `qc.baseline-and-surface-validators`

### 15.1 The Baseline Validator Set

The system ships a baseline set of validator declarations, predominantly `Deterministic`, each narrow. Baseline validators are built-in capabilities and hook subscriptions registered at startup through the same registration path as other validators; they have built-in source identity and default enablement, not a private runtime.

- **Tool-call shape** (`SchemaValidation`, `InputProposed`, structural): the proposed call names a registered capability, its arguments match the input schema, required arguments are present, and declared argument constraints hold. (This complements, and does not replace, the schema validation File 04's pipeline already performs at step 2; the validator surfaces a `Validation` record and a typed gate.)
- **Output format** (`SchemaValidation`, `PreCommit`/`PostOutput`, structural): a produced output that declares a format (a structured object, a code block, a typed artifact) conforms to it; a malformed-but-recoverable output (a JSON object embedded in prose) yields a `High`-confidence extraction correction.
- **Postcondition** (`Postcondition`, `PostExecution`, structural): the canonical wrapper around capability-declared postconditions, producing the `Validation` block and the gate.
- **Grounding alignment** (`CitationCheck`, `PostOutput`, structural): a citation or extraction whose text aligns to an exact source span passes; one that cannot be aligned is flagged as likely ungrounded. Deterministic where alignment suffices; the residue is handed to an optional model-mediated grounding judge.
- **Content safety** (`SafetyCheck`, `PostOutput`/`InputProposed`, structural-then-semantic): a fast pattern pass for known-unsafe content and personal-data patterns, with redaction corrections at `High`/`Medium` confidence, escalating to a model-mediated safety judge only where configured. Invokes File 22's redaction primitive.
- **Output budget** (`Postcondition` or `Custom { namespace: "context", name: "budget_fit" }`, `PreCommit`, structural): a produced output that would exceed the remaining context or output budget is flagged for truncation or compaction (driving the recovery cascade of `run.recovery`, File 04 §20.2). Budget fit is a resource/contract check, not schema conformance.

The baseline set does not include a general-purpose correctness or hallucination judge (§6.3). All baseline semantic checks are narrow and mostly off by default at higher cost (factuality and model-mediated safety default off; structural checks default on), with per-profile defaults (§18).

### 15.2 Surface Validators

Each surface registers its owned validators producing canonical `Validation`/`Critique` blocks:

- **Coder** (File 27): `TypeCheck` and `Lint` validators that run the language server or linter after an edit and inject diagnostics in-band as an immediate feedback loop; `Test` validators that run the test process and produce a pass/fail `Validation`; build validators registered under a coder `Custom { namespace: "coder" }` `ValidationKind` (File 09's closed `ValidationKind` set is not widened); and `CodeReview` critiques from a reviewer pass. The edit-then-diagnose-then-feedback loop is a `PostExecution`/`PostOutput` validator that lets the producing model fix issues in the same turn.
- **Data Processor** (File 29): dataset-schema and data-quality validators (a declarative rule-set producing a per-rule pass/fail validation report); profiling that surfaces detected issues; and grounded-extraction checks that tie extracted values to source spans.
- **Teacher** (File 30): grading validators (`ModelMediated` rubric grading and `Deterministic` sandboxed-test grading) that produce a graded `Validation`; rubric conformance; and `Critique` reviews from a critic classroom agent.
- **Web** (File 28): citation and grounding validators; source-quality validators that gate whether a source may be cited as evidence; and completion validators that require a separate planner to confirm a navigator's completion claim.
- **GUI Control** and **System Agent** (Files 31, 32): observe-act-verify validators (a closed verification-check set over the post-action observation), with `VerificationFailed` as a typed outcome driving recovery; and post-operation verification that confirms a system change had its intended effect before the change is recorded as successful.

### 15.3 Specialization, Not Forking

A surface validator is a specialization of the `Validator` primitive, not a private pipeline. It registers through the one path, produces the canonical blocks, attaches at a canonical boundary, and gates per §8. A surface may declare default required validations (§14.2) and per-surface enablement defaults (§18), but it owns no parallel validation runtime. The baseline cross-cutting validators run alongside surface validators on the same target.

### 15.4 Boundary

The baseline set is canonical here; the surface specializations are owned by their surface specs, which declare their validators' kinds, boundaries, severities, and required-validation defaults. File 39 declares the baseline and the registration-and-gate contract the surfaces consume.

## 16. The `validation.*` Capability Surface and the Quality-Control Surface

Anchor: `qc.capability-surface`

### 16.1 Surface-and-Service Duality

Quality control is a substrate service with a management surface (the surface-and-service duality of the Teacher and System Agent surfaces; `core.substrate-services`, File 01 §2.4 names "logging and evaluation" among substrate services). As a service, the `validation.*` capability family is borrowable cross-surface — any surface or run may run a validator, query a report, or register a validator. As a surface, a quality-control management view (an inspector lens) renders the validator catalogue, validation reports, violation history, correction candidates, and per-profile defaults. There is no quality-control mode field; the management view is a presentation of the service's durable state.

### 16.2 The Capability Family

The canonical quality-control capabilities, each a built-in capability declared per `capability.declaration` (File 05 §3):

- `validation.run(...)` — invoke a validator on a target, reused exactly as defined by `artifact.capability-surface` (File 09 §16); File 39 adds registry/profile/options semantics for selecting which validator declaration runs, but does not redefine the File 09 signature. The tier resolves from the validator backend and touched resources: pure read validators are `ReadOnly`; validators that execute code, call models, use credentials, observe GUI state, query the network, or mutate state inherit the appropriate tier.
- `validation.attach(...)` — link a precomputed `Validation` block to a target, reused exactly as defined by File 09; File 39 does not redefine the attachment signature or edge semantics
- `validation.register_validator(validator_declaration)` — register a validator (proposal-first; `UserApproval`; under source-approval)
- `validation.list_validators(filter?)` — enumerate registered validators with their declarations and scoped enablement (`ReadOnly`)
- `validation.inspect_validator(validator_id)` — return a validator's full declaration, recent decision history, and recent false-positive rate (`ReadOnly`)
- `validation.enable_validator(validator_id, scope)` / `validation.disable_validator(validator_id, scope)` — toggle scoped enablement without unregistering (`WorkspaceWrite`)
- `validation.report(target_id, options?)` — compute and return the `ValidationReport` for a target (§12; `ReadOnly`; `deterministic_replayable`)
- `validation.set_profile(profile, defaults)` — set per-profile validator defaults (§18; `WorkspaceWrite`, or `UserApproval` where it weakens a safety validator)
- `validation.record_feedback(validation_id, feedback)` — record user feedback on a validation (`Accepted`/`Rejected`/`Ignored`/`FalsePositive`) for the accuracy feedback loop (§17; `WorkspaceWrite`)

Surface- and subsystem-specific validators expose their own family-namespaced run capabilities (`coder.validate.*`, `data.sheet.validate`, `teacher.quiz.grade`, `gui.verify`) as adapter capabilities (`capability.adapter-capabilities`, File 05 §17.4) over `validation.run`; the underlying result is always a canonical `Validation`/`Critique` block.

### 16.3 Surface Aliasing

A surface that presents quality control under its own vocabulary (a Coder "checks" panel, a Web "source quality" indicator, a Teacher "grading" view) does so as a presentation of the one `validation.*` service; the surface's quality affordances alias the canonical capabilities and produce the canonical blocks. No surface introduces a parallel quality-control service.

### 16.4 Boundary

The capability declarations and registry are owned by File 05; the policy on each call by File 06; the management view rendering by Files 37 and 38. File 39 declares the family, its semantics, and the surface-and-service duality.

## 17. Events, Metrics, and the Accuracy Feedback Loop

Anchor: `qc.events-metrics`

### 17.1 Events

Quality control emits through the canonical ledger and event kinds already reserved (`ledger.entry-kind-catalogue`, File 10 §4.1): `QualityControlValidatorRan` (validator id, verdict, decisive validator chain, latency), `QualityControlViolationDetected` (the surfaced violation), `CompletionVerificationFired` (mode and verdict), `ValidationCompleted`, `CritiquePublished`, and `ArtifactValidationStateChanged`. A correction emits the version-commit events of the sibling it produces. File 39 introduces no new top-level event kinds; subsystem-specific quality events (for example, a Data Processor data-quality-failure event or a Teacher misconception-detection event) are registered as `Custom` events by their owning specs where those specs declare them.

### 17.2 Metrics

Quality metrics are aggregates over the recorded validations, computed downstream and never surfaced as per-validation continuous scores (§6.2): the proportion of targets passing a given validator over a window, the per-validator false-positive rate from user feedback, the per-validator latency distribution, and the most-common violation kinds. These aggregates are projections; the Telemetry, Logging, and Observability spec (File 41) renders them, and the Evaluation and Benchmarking spec (File 40) uses them for offline measurement. File 39 names the metric sources and the feedback loop.

### 17.3 The Accuracy Feedback Loop

A validation may receive user feedback (`Accepted`, `Rejected`, `Ignored`, `FalsePositive`) through `validation.record_feedback`. The feedback drives the validator-accuracy projection (which validators are noisy), informs per-profile default tuning (a high-false-positive validator may be downgraded to advisory or disabled for a profile), and — for `ModelMediated` validators — feeds the offline judge-optimization pipeline in the Evaluation and Benchmarking spec (File 40) that calibrates a judge against annotated examples. The agent may propose registering a new validator trained from a conversation where it failed; the user gates the registration. File 39 owns the inline feedback recording and the registration handoff; File 40 owns the optimization run.

### 17.4 Boundary

Events and the ledger are owned by File 10; the telemetry projection by the Telemetry, Logging, and Observability spec (File 41); the offline optimization by the Evaluation and Benchmarking spec (File 40). File 39 names the events, the metric sources, and the feedback loop.

## 18. Settings, Profiles, and Customization

Anchor: `qc.settings`

### 18.1 Configurable Dimensions

Every quality-control mechanism is configurable through the canonical settings system (`core.settings-system`, File 01 §6.8) resolved through the canonical settings source stack (`settings.scopes-profile-contexts-overlays`, File 15 §5.2). At minimum, settings support:

- per-validator `enabled` state, scoped global, workspace, conversation, and run, and per-profile
- per-validator `severity` (blocking/advisory/informational) overrides — the blocking-versus-non-blocking hook `mode` derives from severity — within authority limits (a security-category validator cannot be made fail-open without typed confirmation, and a permission-floor concern cannot be downgraded)
- per-validator thresholds (confidence floors, alignment thresholds, the factuality and contradiction thresholds the semantic validators consult) — thresholds are settings, never hardcoded constants
- per-validator fail-direction overrides within the hook timeout-and-fail-direction rule (File 10 §7.5) limits
- per-validator retry policy by error class, within the safety guard
- per-validator `inconclusive_policy`, within the rule that required validations, security or policy-floor validators, and typed-confirmation gates cannot proceed-as-advisory on `Inconclusive`
- per-validator latency budget and the blocking-hook timeout the validator runs under — the operating latency targets are settings, not hardcoded
- the correction posture: per-validator `CorrectionPolicy`, the auto-apply confidence floor, and the global precision-over-recall default
- the correction-iteration depth and non-convergence policy per target
- the validator cadence: every-target versus sampled (the cost topology that distinguishes a cheap every-target validator from an expensive sampled deep-dive validator), and the completion-verification cadence inherited from `run.termination` (File 04 §22)
- the streaming-eligible validator set and the streaming batch cadence
- the `ValidationReport` aggregation bounds (depth and cardinality) and truncation-detail behavior
- per-capability validation overrides (whether a capability's declared inline validators run, beyond schema validation)

### 18.2 Per-Profile Defaults

Validator enablement and severity carry per-profile defaults so that the default experience fits the user's work: factuality and grounding validators default on for research, study, and data profiles where an ungrounded cited fact is high-cost; content-safety and personal-data validators default on for office and data profiles handling third-party data; consistency validation defaults off for creative profiles where intentional contradiction is legitimate. The defaults are the best overall option per profile; the user may override any of them. A profile's defaults are seeded by built-in defaults and by plugin `[plugin.quality_control.defaults]` contributions (File 35), then by the user's durable overrides, applied as audit-visible records (mirroring the built-in-then-override pattern of `policy.built-in-reusable-policy-rules`, File 06 §11.5).

### 18.3 The No-Hidden-Branch Rule

Quality-control behavior is product variation expressed in settings, never hidden hardcoded branches. The latency budget, the precision-over-recall posture, the per-profile enablement, the thresholds, and the cadence are all configurable; the canonical defaults are the best overall options, and progressive disclosure keeps the default experience clean while making depth reachable.

### 18.4 Boundary

The settings cascade, profiles, and overlay resolution are owned by File 15; the plugin contribution mechanism by File 35. File 39 names the dimensions and the per-profile default discipline.

## 19. Persistence, Locality, and Replay

Anchor: `qc.persistence-replay`

### 19.1 What Is Durable

The durable quality-control state is carried by existing substrates: `Validation` and `Critique` blocks in the block pool (File 08/09), File 09's validation and critique target relations, `derives_from` edges for corrections, the quality-control ledger entries (File 10), and the validator declarations as hook subscriptions and capability declarations (Files 05, 10). Validator enablement and per-profile defaults are settings records (File 15). There is no parallel validation store.

### 19.2 What Is Computed

The `ValidationReport` (§12), the per-target `ValidationState` (File 09 §14.2), and the quality metrics (§17.2) are computed projections over the durable substrates, rebuildable from them. A stale or corrupted projection costs a rebuild, never data loss (`core.projection`, File 01 §6.11).

### 19.3 Locality

Validation results and validator declarations follow the locality of the substrates that carry them: `Validation` blocks and edges sync per the block-sync eligibility rules (File 21); device-local validator state (the resolved live hook subscription, a cached report projection) is rebuildable per-device and not synced. A `ModelMediated` validation replays from its recorded replay key (§10.5), never from the live model endpoint, exactly as a provider call reconstructs from `provider.token-source` (File 17) rather than re-querying.

### 19.4 Replay

Replay of a run reproduces its validations: deterministic validations re-derive identically from the recorded target and inputs; model-mediated validations reproduce the recorded verdict, reasoning, and confidence from the recorded replay key rather than re-invoking the model. Replay re-derives nothing from live mutable sources (`context.assembly-replay-snapshot`). A replay-equivalence property holds: replaying the recorded inputs reproduces the original validation outcomes modulo explicitly-typed model-mediated nondeterminism, which is recorded. Wherever a validation's identity or a report's aggregation depends on a hash, the hash is computed over a declared `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14), never over physical storage bytes; File 39 defines no new hash and reuses the block and ledger hashes of Files 08 and 10.

### 19.5 Boundary

Storage realization is owned by File 20; sync and portability by File 21; replay mechanics by Files 10 and 11. File 39 specifies what is durable, what is computed, and the replay-keying and replay-equivalence contracts for validations.

## 20. Operating Constraints

Anchor: `qc.operating-constraints`

The quality-control layer operates under these constraints, all configurable as settings (§18) with the stated canonical defaults:

- **Bounded latency.** A blocking validator runs within a configured budget; a validator that exceeds its budget fails per its category fail-direction (security-category fails closed). The default budgets keep blocking validators cheap and deterministic; expensive checks run non-blocking or at completion. The budget is a setting, not a hardcoded duration.
- **No blocking on user input during generation.** A blocking validator's decision is automatic (deterministic or fast model-mediated); a validation that requires a human judgment runs as an advisory or an asynchronous review, never as a synchronous gate that stalls generation waiting for the user. User adjudication of a flagged violation or a low-confidence correction happens after the output is produced, on the non-destructive sibling.
- **Precision over recall by default.** A false correction is worse than a missed violation; auto-apply is reserved for high-confidence corrections, and everything uncertain is surfaced rather than imposed. The posture is the default, configurable per profile.
- **Transparency.** Every validation, violation, and correction is recorded, ledgered, and inspectable; a user can see what was checked, what failed, what was corrected, and why, and can switch a correction back. Quality control is never a silent hidden hand.
- **Tunability.** Every validator is enable-able, disable-able, severity-adjustable, and threshold-tunable within authority limits, at the scope the user wants.

These constraints are the canonical posture; the per-error-class and per-profile configuration lets the user trade latency for thoroughness or recall for precision where their work justifies it.

## 21. Explicit Rejections

Anchor: `qc.explicit-rejections`

The following shapes are wrong for this layer:

- a separate quality-control pipeline, a parallel validator runtime, a dedicated validator DAG node kind, or a "QC engine" distinct from the run model — validators are validator-category hooks over the one event bus; a parallel primitive that does the same thing is rejected
- a parallel validation store, a parallel validator registry, or a parallel validation-result carrier — validators register through the one capability/hook path; results are `Validation`/`Critique` blocks in the one pool; reports are derived projections
- redefining the `Validation` block, `ValidationOutcome`, `ValidationState` derivation, or the `validation.run`/`validation.attach` capabilities — those are File 09's; File 39 consumes them
- in-place mutation of a produced output as a correction — corrections are non-destructive sibling versions or typed in-band signals; silently overwriting the generated output is rejected
- a built-in general-purpose correctness judge or hallucination judge surfaced as a default validator — the system ships the machinery and narrow validators, not foregone verdicts; a model cannot reliably judge its own output's correctness as a default
- a model-mediated judge that inherits the producer's reasoning, self-justification, or unrelated conversation history by default — judges receive isolated, validation-relevant context unless explicitly configured otherwise
- a one-to-five or zero-to-one numerical score as a judge's verdict — verdicts are `Passed`/`Failed`/`Inconclusive` or a small closed enum; continuous quality figures are downstream aggregates, never per-validation surfaced scores
- a model-mediated validator that returns a verdict without reasoning — reasoning is required for transparency, adjudication, and offline calibration
- a quality validator that re-implements permission policy, secret detection, redaction, or injection defense — those are Files 06 and 22; a validator orchestrates them, it does not duplicate them
- a quality validator that reaches into a subsystem's private state — the subsystem registers its own validators with the access it owns; the quality layer does not open a second path
- a blocking validator set to fail open without typed confirmation, or any validator that bypasses a permission floor, typed-confirmation requirement, contradiction detection, or touched-resource constraint — quality control narrows, it never escalates authority
- folding offline evaluation suites, benchmarks, regression harnesses, or judge-optimization runs into this layer — those are owned by the Evaluation and Benchmarking spec (File 40); this layer is inline validation that gates live execution
- treating an `Inconclusive` outcome as `Passed` at any blocking boundary — uncertainty must gate or follow an explicit allowed `inconclusive_policy`
- presenting skipped validators as passed in a validation report — skipped checks remain visible as skipped diagnostics
- gating generation on a synchronous human judgment — blocking validators are automatic; human adjudication is asynchronous over the non-destructive sibling
- hardcoding latency budgets, retry counts, precision-over-recall posture, thresholds, cadence, correction-iteration depth, or per-profile enablement as constants instead of settings — quality-control behavior is configurable product variation
- a completion that is allowed to reach `completed` with a `Failed` or unsatisfied required validation, or a run that weakens its own required validation to reach trivial completion — required validations are completion-contract requirements subject to the forgery and monotonicity guards
- treating live validation events as durable validation truth — consequential validations are blocks and ledger entries; the event stream is live coordination, not the source of truth

## 22. Consequences for Later Specs

Anchor: `qc.consequences-for-later-specs`

Later specs must follow these rules:

- the **Evaluation and Benchmarking** spec (File 40) must build offline eval suites by running the `Validator` primitive and aggregating `Validation`/`Critique` results over recorded runs; it must own the judge-optimization pipeline, the suite and run records, and the scoring aggregation, and it must consume — never redefine — the validator and result contracts of this file. The boundary is fixed: File 39 is the inline layer that gates live execution; the Evaluation and Benchmarking spec (File 40) is the offline layer that measures and compares.
- the **Telemetry, Logging, and Observability** spec (File 41) must compute quality metrics as projections over the quality-control ledger entries and validation blocks named here, surfacing validator-accuracy, false-positive, latency, and pass-rate aggregates without introducing a parallel quality store.
- the **per-surface specs** (Files 27–32) must register their owned validators through the one path, produce canonical `Validation`/`Critique` blocks, attach at canonical `ValidationBoundary` values, gate per §8, and declare their default required validations and per-surface enablement defaults; none may introduce a private validation pipeline.
- **automation and workflow specs** (Files 33, 34) — already written — bind required validations through the run-completion contract and the workflow body; this file confirms that a workflow's or automation's declared validation requirement is a `Completion`-boundary required validation, gated per §14, and that an automation's non-interactive safety posture treats a `Failed` required validation as a park-and-notify outcome, never an auto-pass.
- the **plugin and extension spec** (File 35) — already written — contributes validators through the plugin contribution path under source-approval and trust narrowing, seeds per-profile defaults through `[plugin.quality_control.defaults]`, and never grants a plugin validator authority above `narrowing_only` without explicit user upgrade.
- the **storage and sync specs** (Files 20, 21) must persist `Validation`/`Critique` blocks and quality-control ledger entries through the existing block and ledger schemas, must keep cached `ValidationReport` projections rebuildable, and must follow the locality split (synced results, device-local resolved subscriptions and caches) and the model-mediated replay-keying rule of §19.
- **UI specs** (Files 37, 38) must render validation reports, badges, violations, correction candidates, and the validator catalogue from the canonical data contracts, and must present a correction as a non-destructive sibling the user can adopt or revert, never as an already-applied in-place mutation the user cannot undo.
- any spec that introduces a new kind of produced output or a new kind of action must say which validators gate it and at which boundary, rather than inventing a bespoke check; the validator-plus-boundary-plus-severity contract of this file is the canonical shape for "is this correct, complete, grounded, consistent, and safe."

## 23. Canonical Rule Anchors

Anchor: `qc.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `qc.chosen-model`, `qc.boundaries-with-adjacent-layers`, `qc.validator`, `qc.validation-boundary`, `qc.validation-kind-taxonomy`, `qc.judge-discipline`, `qc.outcome-severity-findings`, `qc.validation-gate`, `qc.correction-model`, `qc.validator-registration`, `qc.no-duplication`, `qc.validation-report`, `qc.streaming-validation`, `qc.completion-gate`, `qc.baseline-and-surface-validators`, `qc.capability-surface`, `qc.events-metrics`, `qc.settings`, `qc.persistence-replay`, and `qc.operating-constraints`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
