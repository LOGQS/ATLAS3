# Phase 21 — Evaluation Completion & Observability

## 1. Goal & why now

The offline and live quality layers complete over a now-rich recorded corpus: File 40's full
evaluation machinery (SimulateDeterministic/FullRerun replay, comparison evals with blind judging,
regression baselines, eval-pass gates, annotation queues, the judge-optimization pipeline) and
File 41's Observatory (log/trace/metric projections over the one ledger, consent-gated telemetry
sinks, the debug surface) — plus File 42 §16's operate-side health/remediation, the other half of
the 41↔42 observe/operate seam. With six surfaces, automations, and extensions live, eval families
have real primary artifacts and observability has real load.

## 2. Canonical scope & deferrals

- **File 40 — completion**: replay modes — `SimulateDeterministic` (re-executes
  `deterministic_replayable` capabilities against captured inputs; divergence is a **typed
  determinism-violation finding** attributable to the misdeclared capability/replay-class/substrate,
  never a plain quality failure) and `FullRerun` (replay-time state, isolated destinations via 23,
  UserApproval + typed confirmation via 11 §15.7) (§7.2); comparison evals — A/B → best-of-N →
  arena → tournament over 04 §16 run shapes, **the blind-comparator discipline** (randomized
  recorded label assignment, no arm/source metadata) (§9); regression detection +
  `RegressionBaseline` compatibility rules + the eval-blind-iteration guard + **the eval-pass
  gate** (a Completion-boundary required validation per-run, or a precondition on
  install/graduation — consumed by 34 graduation and 35 install) (§10); **judge optimization** —
  user-gated, cost-previewed, train/validation **split by task** (never by trace), ensemble-behind-
  a-router as a refinement; **the self-certifying-loop guard** — high-trust gates must trace to a
  ground-truth anchor, never resting solely on uncalibrated model judges (§11); annotation queues +
  `Annotation` records (reasoning required; model-assisted labels reviewed, never silently ground
  truth) (§12); the full closed `EvalFamily` set bound to primary artifacts — the per-phase-seeded
  suites formalized (§8.2); scheduled regression runs as Automations — no separate eval scheduler
  (§14.3); leaderboards/reports as projections (§13).
- **File 41 — complete**: the `Observatory` panes (§3); `LogRecord`/`LogLevel` + the bounded
  rotating device-local diagnostic stream — the one durable artifact this file adds (§4);
  `Span`/`Trace`/`TraceContext` — the meaning of File 10's envelope field; span identity recorded or
  deterministically derived, **never projection-time random**; a span with no terminating event is
  `Incomplete`/`Unknown`, never silently `Ok` (§5); `MetricInstrument` closed kinds + the baseline
  metric families + accuracy/authority classes — `DiagnosticOnly` never an authoritative gate;
  keyed-never-unkeyed enforced at registration; **metrics are aggregates, never per-item verdict
  scores** (§6); **`TelemetrySink` + `TelemetryConsent`** — **zero-egress by default**, no built-in
  hosted-telemetry dependency; redaction→sensitivity-gate→anonymization→policy-gated egress;
  **consent is user-only** (no lease/auto-decide/profile/automation grants it), per-category,
  per-device, revocable; anonymization pseudonyms keyed + scoped, never content hashes;
  `DiagnosticBundle` (NOT a PortablePackage) + the optional OTel backend with a no-op fallback (§7);
  the debug surface — `ATLAS3_DEBUG`-gated, zero overhead inactive, ring buffer with redacted-only
  search + overflow reporting (§8); observability retention over 20 GC (§9); **the audit boundary**
  — audit never disabled when telemetry is, never synced, surfaced read-only (§10); health
  projections — **observe-only: never blocks/gates/remediates; infers no liveness from missing
  heartbeats; owns no watchdog/timeout/restart** (§11); the instrumentation-declaration contract —
  one path, no parallel instrumentation registry (§12); `observability.*` capabilities (§13). The
  two named hooks (`logging.audit_recorder` −100, `telemetry.metrics_collector` observe-only) get
  their full behavior.
- **File 42 — §16**: operational health + `RemediationPolicy` — the operate side: **the
  missed-heartbeat watchdog** (the flagged periodic exception 41 declines), liveness classification,
  automatic remediation limited to declared idempotent runtime mechanics; anything crossing a
  policy/security/user-data/credential boundary passes the capability+policy path with typed
  confirmation — never a privileged side door; degraded-mode operation first-class.

## 3. Prerequisites

P13 — the validator/eval foundation + the Inspect engine. P14 — the scheduler (regression
Automations) + workers to supervise/observe. P15–P17 — the surface corpus + per-surface suites.
P12 — Observatory rendering. P20 — sink credential patterns. May overlap P19/P20.

## 4. Lanes

(a) Replay completion + comparisons + regression/gates; (b) judge pipeline + annotations;
(c) traces/metrics/logs + the Observatory; (d) sinks/consent/debug surface; (e) 42 §16
watchdog/remediation. (a)→(b); (c)/(d) independent; (e) joins (c) at the health seam.

## 5. Build plan

1. **Replay completion**: SimulateDeterministic with determinism-violation typing; FullRerun with
   isolation + replay-time policy gates.
2. **Comparisons**: paired/best-of-N/arena shapes over child-run structures; blind assignment
   recorded; verdicts as Validation blocks; leaderboard projections (Elo/Bradley-Terry/IRT as
   downstream aggregates of binary verdicts).
3. **Regression + gates**: baselines with compatibility rules (scorer-identity/role/golden-version
   changes stale them); the eval-pass gate wired into 34 graduation + 35 install; recurring
   scheduled regression Automations (cadence a setting — e.g., nightly — never a hardcoded
   constant).
4. **Judge pipeline**: annotation queues (similarity-assisted via 12); judge optimization with
   ground-truth anchoring; the self-certifying-loop guard.
5. **Traces/metrics/logs**: span projection from recorded entries; metric instruments + baseline
   families (latency/throughput/usage+cost/error/cache/quality/provider-health/resource); the
   resource-gauge sampler as the one flagged periodic worker; the diagnostic stream under the data
   root.
6. **Sinks + consent**: consent records; the egress pipeline; `DiagnosticBundle` under egress
   governance; the OTel adapter as a replaceable backend.
7. **Observatory + debug surface**: panes over existing projections; the reconstruction pane = File
   11 forensic queries; ring buffer + debug toggles.
8. **42 §16**: the watchdog + supervision-integrated remediation; worker/lifecycle facts flow 42→41.

## 6. Test obligations & acceptance evidence

- 40: **replay equivalence** — same fixtures + pinned config → same verdicts + aggregates, typed
  recorded nondeterminism (§7.5/§18.4); **the determinism contract** — evaluation re-derives nothing
  from live mutable sources; deterministic replay consults no live retrieval/memory/world/counting
  endpoint (§4.3); determinism-violation classification (§7.2); **blind-comparator** (§9.3);
  **the self-certifying-loop guard** — a generated validator gated by a generated suite scored only
  by model judges is rejected for high-trust gates (§10.4); goldens never silently regenerated
  (§5.4); baseline staleness rules (§10.1); cost-preview + user gate on expensive evals (§14.1);
  judge dataset split-by-task (§12.3); coverage honesty — the case set never silently truncated,
  skips counted separately (§6.4/§13.2).
- 41: **observe-only / never-authority** (the headline) — observability never
  blocks/gates/throttles/kills/remediates the observed operation; an observe-only hook's
  non-Continue decision downgrades to Continue + warning; **41 owns no watchdog and infers no stale
  liveness from missing heartbeats** (the 41↔42 seam); a log/trace/metric is never the source of
  truth for a consequential fact (§11/§17); trace/metric **replay equivalence** — rebuilt from
  recorded entries, no live re-query, no re-derived model-dependent values (§16.3); span integrity —
  no terminating event → `Incomplete`, never silently `Ok`; sequence-first ordering, wall-clock
  never canonical (§5); **keyed model facts + no verdict scores** — unkeyed model-dependent metrics
  rejected at registration; cost read from 17, never recomputed, never `Unknown`→0; no 1–5/0–1
  per-item quality scores (§6); **privacy/zero-egress** — nothing leaves by default; redaction
  before write and before egress, never before display; raw `Secret` a forbidden destination in
  every log/trace/metric-label/projection/bundle/egress; **consent user-only**; pseudonyms keyed,
  never content-addressed (§4.5/§7); ring-buffer redacted-only search + overflow reported (§8.2);
  **the audit boundary** — disabling telemetry never disables audit; tamper surfaced, 41 changes
  nothing (§10); the one sampled exception (host-resource gauge) flagged + configurable (§8.5); no
  time-based retention as correctness (§9.3).
- 42 §16: remediation never silently masks a deterministic failure (trips the circuit + notifies);
  boundary-crossing remediation passes capability+policy with typed confirmation; degraded-mode —
  the app starts and runs with any subset of optional backends.
- **Closed-set pinning**: EvalFamily, comparison shapes, `Annotation` roles, `LogLevel`, span
  status, metric kinds, accuracy/authority classes, `WorkerState`/`RemediationPolicy` shapes.
- Conformance matrix gains: 40 remaining + 41 + 42 §16 anchors; the P13 replay-mode and P14
  watchdog stub rows close.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `RegressionBaseline`/`Annotation`/`EvalScore`
  extensions, `LogRecord`/`Span`/`TraceContext`/`MetricInstrument`, `TelemetrySink`/
  `TelemetryConsent`/`DiagnosticBundle`, `RemediationPolicy`; migrations for the
  baseline/annotation/consent families; the recurring regression suite-set as versioned
  registrations.
- **Docs**: the replay-modes + comparison + regression docs; the judge-optimization +
  ground-truth-anchor doc; the Observatory reference; the zero-egress/consent doc; the 41↔42 seam
  doc; the degraded-mode doc.
- **CI/local commands**: `eval-run --suite <set>` extended; the replay-equivalence (full),
  blind-comparator, self-certifying-guard, observe-only, redaction-before-write, consent-user-only,
  and watchdog/remediation suites as named CI jobs; the **recurring regression Automation**
  (settings-configured cadence) becomes a standing scheduled job.

## 8. Exit criteria

- [ ] The scheduled regression Automation runs the full suite catalog over recorded fixtures; a
      seeded regression is caught with baseline deltas.
- [ ] A judge trained from annotations deploys under the discipline constraints; the
      self-certifying-loop guard demonstrably rejects an all-model-judged gate.
- [ ] The Observatory renders logs/traces/metrics/usage/health for a real session; **zero-egress
      verified by a network-assertion harness**; the consent flow E2E.
- [ ] M0–M3 still green.

## 9. Locked in this phase

- **The `EvalFamily` set + primary-artifact bindings**; `RegressionBaseline` compatibility rules;
  the `Annotation` record shape; the per-case verdict contract (frozen since P13, now exercised
  under comparisons).
- **The `LogRecord`/`Span`/`TraceContext`/`MetricInstrument` shapes**; span-identity derivation
  rules; the anonymization scheme (keyed pseudonymization, never content hashes).
- **`TelemetryConsent` semantics** (user-only, per-device default, revocable);
  `DiagnosticBundle` ≠ PortablePackage; the observe-only/no-authority invariants; **the 41↔42
  watchdog seam** — a watchdog in observability or a projection-of-record in the runtime is invalid
  forever.
