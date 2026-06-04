# Phase 13 — Quality Machinery (Inline Validation + Eval Foundation)

## 1. Goal & why now

The two layers of the one quality discipline get their machinery: File 39's `Validator` primitive
(validators-as-hooks, the deterministic baseline set, the gate, non-destructive corrections,
completion-requirement integration) and File 40's minimal offline layer (`EvalSuite`/`EvalCase`/
`EvalRun`, recorded fixtures, **the Inspect replay-engine realization**, deterministic golden
comparisons). Placed deliberately **before** the surfaces: 39 §10.2 has surface validators register
when the owning surface loads — the machinery must pre-exist them — and eval-gated evolution is
worthless if eval arrives after most of the build. QC is not a separate pipeline: a Validator is a
validator-category Hook, its result a `Validation`/`Critique` block, its gate the hook vocabulary +
the completion contract.

## 2. Canonical scope & deferrals

- **File 39 — complete core**: the `Validator` declaration — a declaration lacking any required
  field is invalid (§3.2) — + validator-as-hook registration (§3.4); the closed `ValidationBoundary`
  set (§4.2); severity + **the deterministic `(outcome, severity, boundary, authority)` gate**
  producing the four-outcome hook decision (§7–§8); non-destructive corrections —
  None/Suggest/AutoApplyAsCurrent, sibling-version corrections, bounded cascades with
  non-convergence fallback (§9); registration/trust — untrusted-source validators narrowing-only
  (§10); the typed validator invocation envelope — typed data first, not prompt text (§3.3); the
  `ValidationReport` derived projection (§12); streaming-boundary advisory validation (§13);
  **completion-requirement contribution** over the 04 §22 floor — required validations become
  `validation result` completion requirements; the agent may add but never weaken its own (§14);
  **the baseline deterministic validators** — tool-call shape, output format, postcondition,
  grounding alignment, content safety, output budget; structural checks default-on, semantic
  default-off; **no built-in general-purpose correctness/hallucination judge** (§15); `validation.*`
  capabilities (§16); accuracy-feedback metric sources (§17). Model-mediated judges ship as
  machinery + frozen discipline constraints; semantic judges are authored per failure mode by later
  phases.
- **File 40 — minimal**: `EvalSuite`/`EvalCase`/`EvalRun` (§3); `RecordedRunFixture`/
  `SyntheticFixture` + File 20 retention holds (§4); deterministic `GoldenComparison` —
  ExactMatch/StructuralDiff (with explicit `allowed_diff_contract`)/PropertyAssertion (§5); scorers =
  validators offline, Required/Advisory/Informational roles resolved + recorded per run (§6); **the
  replay-engine realization, Inspect mode** — the File 10 §11.6 assignment lands here, driving the
  P3 replay data (§7.3); **the eval-forgery guard** (§7.6); `EvalScore`/`EvalReport` projections
  (§13); `eval.*` capabilities (§15). SimulateDeterministic/FullRerun orchestration, comparison
  shapes, regression baselines, eval-pass gates, judge optimization (§7.2 rest, §9–§12) → **P21**.

## 3. Prerequisites

P6 — call pipeline + hookable boundaries + the completion floor. P9 — Validation/Critique blocks +
ValidationState derivation. P3 — hooks, the replay contract. P2 — retention holds. (P12 rendering of
badges/reports is optional — the machinery is headless-complete.) May run in parallel with P11/P12.

## 4. Lanes

(a) Validator machinery — declaration, hook registration, the gate, corrections; (b) baseline
validators; (c) eval objects + fixtures + retention holds; (d) the Inspect replay engine + golden
comparators + `EvalScore`. (a) → (b); (c)/(d) parallel to (b).

## 5. Build plan

1. **Validator-as-hook**: declaration validation; boundary→hook-event mapping; deterministic
   backends as capabilities; the gate; the decisive chain recorded
   (`QualityControlValidatorRan` + `HookDecisionRecorded`).
2. **Baseline validators** as Builtin + hook subscriptions at startup (the 42 boot step 8 / 10 §8
   path) — predominantly deterministic; everything semantic default-off.
3. **Corrections**: Suggest first; AutoApplyAsCurrent as sibling versions behind confidence floors
   (`Low` always Suggest); a correction is a capability invocation through the full pipeline — no
   hidden path; the original always preserved and one-click reversible.
4. **Completion integration**: required validations gate at the Completion boundary; satisfied only
   by a `Passed` Validation matching target/kind/accepted-identity/min-trust/severity/version; the
   monotonicity guard composes with P3's contract-revision guard.
5. **Eval objects + fixtures**: `RecordedRunFixture` referencing durable substrate (never
   duplicating) + retention holds; suite registration at startup; pinned configuration via File 15
   invocation overlays.
6. **The Inspect replay engine**: resolve fixture refs → reconstruct recorded context (route
   records, AssemblySnapshots, surface snapshots, observations) → score recorded outputs with
   deterministic scorers → `EvalScore`. Re-derives nothing from live sources.
7. **First real suites**: seeded from the P6/P7 recorded fixtures — Routing (route records), Context
   (AssemblySnapshots), Cost (TokenUsageRecords) — proving the family/primary-artifact bindings
   before the surfaces multiply them.

## 6. Test obligations & acceptance evidence

- **One quality layer / no second pipeline** (the central family): a validator is a hook + a backend
  + a Validation/Critique block; no parallel validator registry, no validator DAG node kind, no QC
  engine beside the run model, no parallel result store; QC re-implements no policy/secret/redaction
  machinery — grep + validator.
- **Gate determinism + fail-closed + Inconclusive-gates** (39 §8): same
  (validation, severity, boundary, authority) → same decision — divergence is an Explicit Rejection;
  blocking validators are security-category hooks failing closed (fail-open needs typed
  confirmation); **`Inconclusive` never silently `Passed`** at a blocking boundary; **a skipped
  validator is never presented as passed**; truncated reports carry `truncated` + details; the
  most-restrictive decisive result wins; no validator bypasses floors/typed-confirmation/
  touched-resources.
- **Non-destructive correction** (39 §9): sibling versions or in-band signals — never in-place
  mutation of produced output; semantic changes require `Block` + agent self-correction, never a
  silent `Substitute`; bounded cascade; competing correctors yield distinct sibling candidates.
- **Judge discipline frozen** (39 §6.2/§21): narrow per-error-mode judges; context-isolated by
  default; closed-enum verdicts with reasoning — **never a continuous score**; provider-agnostic;
  no omnibus judge in the baseline.
- **Completion-requirement guard** (39 §14.2): a run cannot reach `completed` until the matching
  `Passed` Validation exists; add-but-never-weaken monotonicity.
- `ValidationReport` determinism over snapshots (39 §12.3); replay-equivalence — deterministic
  validators re-derive, model-mediated reproduce recorded verdicts from the replay key, never
  re-invoking the model (39 §19.4, §10.5).
- **Eval-forgery guard** (40 §7.6): a case cannot record `Passed` without the ledgered evidence its
  scorers require — rejected at the ledger boundary (the offline analog of completion forgery).
- Eval determinism: same fixtures + pinned config → same verdicts + aggregates (40 §7.5);
  `EvalScore` determinism (§13.4); per-case verdicts binary/closed-enum with reasoning, never 1–5 or
  0–1 (§6.2); coverage honesty — skip kinds counted separately, the case set never silently
  truncated (§6.4/§13.2); a dangling-reference fixture is unreplayable, never scored partially
  (§4.4); goldens never silently regenerated — accepting new output is an explicit recorded suite
  version (§5.4); golden canonical-encoding tests wherever fixture identity hashes (§18.4).
- **Closed-set pinning**: ValidationBoundary, ValidationSeverity, CorrectionPolicy/Confidence,
  GoldenComparison taxonomy, fixture kinds, scorer roles, replay modes.
- Conformance matrix gains: 39 anchors; 40 minimal anchors (Inspect engine, eval-forgery guard);
  reuse-only confirmed — File 39 introduces no new validation kinds/outcomes/event kinds.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `Validator`/`ValidationBoundary`/`ValidationReport`,
  `EvalSuite`/`EvalCase`/`EvalRun`/`EvalScore`, the golden-comparison taxonomy; migrations for the
  suite/fixture/retention-hold families; the seeded suite definitions as versioned registrations.
- **Docs**: the validator + gate reference; the judge-discipline doc (the frozen constraints); the
  correction model doc; the eval-object + fixture + replay-engine docs; the eval-gated-evolution
  posture doc (pointing at the invariants doc's prime directive).
- **CI/local commands**: `eval-run` (suite execution over recorded fixtures); the gate-determinism,
  inconclusive-never-passes, correction-non-destructive, eval-forgery, and replay-equivalence
  (Inspect) suites as named CI jobs; the seeded regression suites join CI.

## 8. Exit criteria

- [ ] Baseline validators live on every run; a deliberately malformed tool call is Blocked at
      InputProposed with a recorded decisive chain.
- [ ] A required validation gates completion end-to-end (the run parks until a `Passed` Validation
      exists).
- [ ] `eval.run` over the recorded P6/P7 fixture set reproduces byte-stable scores in CI; a
      deliberately corrupted fixture trips the forgery guard.
- [ ] M0–M2 still green.

## 9. Locked in this phase

- **The `Validator` declaration field set + the ValidationBoundary/Severity closed sets + the gate
  mapping** (replay/audit depend on it).
- **The typed validator invocation envelope** (39 §3.3) and the **ModelMediated replay key set**
  (39 §10.5).
- **Judge discipline as canon**: closed-enum verdicts with reasoning; narrow judges; no continuous
  per-case scores — frozen forever (39 §6.2, 40 §6.2).
- **`EvalSuite` required fields + the closed fixture set + the GoldenComparison taxonomy + the
  replay-engine realization contract** (everything in P21 builds on these).
- File 39's reuse-only rule — additive validation kinds/outcomes route through 09/10, never here.
