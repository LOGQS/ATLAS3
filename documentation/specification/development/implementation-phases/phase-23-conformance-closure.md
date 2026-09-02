# Phase 23 — Conformance Closure & 1.0 (M4)

## 1. Goal & why now

No new subsystems — proof. Every load-bearing rule anchor in Files 01–43 traces to a passing test,
eval suite, or structural enforcement (or a deliberate, recorded waiver); the cross-cutting
properties that only make sense over the whole system are verified end-to-end; performance and
resource budgets are tested settings; and the release pipeline ships 1.0. This phase is the system
answering for the entire canon at once. Milestone **M4 / 1.0**.

## 2. Canonical scope & deferrals

Cross-cutting over all 43 files. Per-file anchors were discharged phase-by-phase; this phase owns
the **whole-system obligations** no single phase could close:

- The pervasive invariants restated across the corpus: canonical-encoding-for-hashing everywhere; no
  unkeyed model-dependent scalars; projections rebuildable, never sources of truth; event-first with
  only the canon's flagged timer exceptions; killability everywhere; no raw-secret egress anywhere;
  replay re-derives nothing from live sources; no parallel store/registry/runtime/scheduler
  anywhere.
- File 40 §8.2's `CrossFamily` evals; 25 §12 / 26 §16 no-private-architecture sweeps over the
  *final* dependency graph; File 01 §10's meta-rule (nothing contradicts §2–§6, violates §7, or
  reintroduces a §8 rejection).

Deferrals: none. Post-1.0 work is governed by the standing guardrails this phase leaves behind.

## 3. Prerequisites

P0–P22 all exited. The conformance matrix has grown monotonically since P0; this phase drives it to
closure.

## 4. Lanes

(a) Matrix closure sweep; (b) the destructive drills (each independently scriptable); (c) the
cross-family eval baseline; (d) performance/resource budgets; (e) docs + release. Highly parallel —
(a) seeds work for the others as it finds gaps.

## 5. Build plan

1. **Matrix closure sweep**: for every anchor in the corpus — link to its test/eval/structural
   check, or write the missing one, or record a justified waiver (waivers reviewed, counted, and
   targeted at near-zero). The matrix CI check flips from "tracks coverage" to **"fails on unmapped
   anchors"** — permanently.
2. **Whole-system destructive drills** (scripted, repeatable, joining CI/scheduled jobs):
   - **Replay-everything**: a long recorded session (all six surfaces, automations, plugins,
     connectors, sync) replayed with live sources severed — every projection, trace, eval verdict,
     and provenance query reconstructs or returns typed gaps.
   - **Kill-everything**: crash injection at every lifecycle stage (mid-run, mid-commit, mid-update,
     mid-sync, mid-import) → restart → the restart-equivalence guarantee holds globally; orphans
     surfaced never auto-resumed; a process audit finds no unkillable unit.
   - **Leak-scan**: seeded secrets of every detector shape pushed through every path (runs, blocks,
     exports, sync, telemetry, crash capsules, materialized files, logs, model context) → zero
     leaks.
   - **Injection**: adversarial instructions embedded in web pages, ingested files, tool results,
     study materials, webhook payloads, plugin descriptions, MCP tool metadata → zero authority
     escalations (the structural rule, system-wide).
   - **Rebuild-the-world**: delete every projection store and cache → full rebuild →
     byte-equivalence modulo typed gaps (the P2 harness at maximal scope).
3. **Cross-family eval baseline**: assemble and pin the 1.0 regression baseline across all eval
   families; eval-gated evolution becomes the standing change-control mechanism for post-1.0 work
   (40 §10.3).
4. **Performance/resource budgets**: interaction responsiveness (37 §16.6), boot-to-usable, memory/
   disk accounting, model-cost projections — all tested settings with budgets, never constants;
   regressions gate.
   For each host-mediation-sensitive operation class admitted to the 1.0 profile, pin its reference
   responsiveness envelope, the applicable mechanism-specific crossing-count bound, host-resource-claim
   bound, or explicit justified not-applicable or retained-boundary waiver, its resident
   memory/processor/process-count budget, and the platform and profile matrix the budget is
   calibrated on. Only a calibrated budget gates; a learned responsiveness baseline never decides pass
   or fail. A reusable managed-service decision is judged on avoided cold-boundary latency and steady
   resident cost together, so reducing spawn latency does not pass the budget gate by relocating the
   cost into permanent resident load.
5. **Docs + release**: user-facing docs complete; the canon↔implementation drift check clean (any
   divergence resolved by code fix or canonical spec revision per the invariants doc — never silent
   divergence); 1.0 ships through the full P22 pipeline; release provenance published.
6. **Post-1.0 posture**: the recurring regression Automation + the closed conformance matrix + the
   pinned eval baseline + the drills become the permanent guardrails. The phase plan ends; the
   invariants doc continues.

## 6. Test obligations & acceptance evidence

This phase *is* test obligations. Closure items checked explicitly because they span phases:

- 01 §7.11 killability audit: every long-running unit enumerated, killable categorically +
  individually.
- 01 §7.15 anti-polling audit: every timer in the codebase is one of the canon's flagged exceptions,
  settings-governed (wall-clock guard 23 §9.3; missed-heartbeat watchdog 42 §6.4; resource-gauge
  sampling 41 §8.5; metric-sampling watches 32 §12.2; declared `NoChangeEvents` sensor fallbacks).
- 05 §13.6 / 10 §11.3 version-pinned replay across capability updates (replay reads the declaration
  version at call time).
- 11 §19 + 21 §6 sync semantics under adversarial interleavings (property-based two-device fuzzing
  over the P20 harness).
- 15 §6 settings-resolution fuzzing across scope/profile/overlay combinations.
- 22 §19 + 23 §21 mandatory suites re-run against the **complete** system — every sink and spawn
  path now exists.
- 25 §12.4 / 26 §16.2 structural no-private-architecture verification over the final dependency
  graph — automated: imports, DB tables, and registries audited against the closed reuse list.
- The full accessibility conformance pass over every surface, dialog, and state (37 §14.2).
- The 3-OS platform-conditional behavior matrix: every typed platform gap recorded, none silent.
- Host-boundary conformance: every anchor amended by the host-mediation set maps to its applicable
  deterministic multiplicity or resource-claim check, fault-injection evidence, replay or structural
  check, or calibrated budget. A seeded avoidable repeated crossing, or an unnecessarily long-lived or
  contended host-mediated resource claim, fails its applicable check; a cost required for isolation,
  confinement, categorical cancellation, durability, or security records the reason it is retained
  rather than being optimized away — the gate is proven in both directions.
- The superseded-vocabulary grep at full strength: every banned legacy name across the canon absent
  from code and schema.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: the closed conformance matrix (the permanent CI gate); the waiver
  register; the pinned 1.0 eval baseline; the drill scripts.
- **Docs**: user-facing documentation set; the 1.0 release notes + provenance; the post-1.0
  guardrail doc (what gates every future change).
- **CI/local commands**: `drill-replay`, `drill-kill`, `drill-leak`, `drill-inject`,
  `drill-rebuild`; the matrix-closure gate; the budget-regression gate; the full release pipeline.

## 8. Exit criteria

- [ ] Conformance matrix: 100% of anchors mapped (test/eval/structural) or waived with recorded
      justification; CI enforces closure permanently.
- [ ] All five destructive drills green and scripted as repeatable jobs.
- [ ] The cross-family eval baseline pinned; the scheduled regression green for a sustained window
      (measured in consecutive green runs, not wall-clock sentiment).
- [ ] **1.0 released** through the full pipeline: signed, provenance-published, offline-capable
      first run, update path proven from the previous build.

## 9. Locked in this phase

- The 1.0 regression baseline (the reference point for all future eval-gated change).
- The waiver register (every accepted gap is a recorded, visible decision).
- The permanent CI gate set: matrix closure + the drills + budgets + scheduled evals — the system's
  standing definition of "still correct."
