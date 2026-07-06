# Edge Audit — Pre-Construction Dependency Verification

## Status

Companion to `00-overview.md`. Not a phase. A verification, run against the phase files on disk
before the first commit on P0, that the dependency graph across the 24 phases is sound: acyclic,
ordering-edge-compliant, forward-references-resolve, lanes genuinely parallel. Re-run (and amend)
whenever a phase file's prerequisites or deferrals change.

## Verdict

**The build order is sound.** The phase graph is a DAG (no phase hard-depends on a later phase), all
load-bearing ordering edges hold, every "→ destination phase" deferral resolves into a phase that
names it closed, and every parallel-lane claim is real. Five findings below — all tracked, none
blocking P0.

## 1. The hard-prerequisite graph

| Phase | Hard prerequisites | Notes |
|---|---|---|
| P0 | — | |
| P1 | P0 | |
| P2 | P1 | canonical encoding before any stored hash |
| P3 | P2 | (+P1 hashes) |
| P4 | P3 | the round trip commits through the real spine |
| P5 | P4, P3 | boot step 8 slot; hooks/ledger/blocks |
| P6 | P5, P3 | real policy on the loop path |
| P7 | P6 | (+P2 secret forms; vault → provider → strategy internally serial) |
| P8 | P5, P6 | **trust/egress lane additionally needs P7 (vault)**; sandbox-core lane does not |
| P9 | P8, P3, P5/P6 | chokepoint before materialization |
| P10 | P9, P8 | (P7 optional — lexical-only retrieval is spec-valid) |
| P11 | P10, P9, P5/P6 | evaluator + `.atlas/commands/` + lenses |
| P12 | P11, P10, P6/P7 | rails to render; SurfaceState to produce |
| P13 | P6, P9, P3, P2 | **independent of P11/P12** |
| P14 | P11, P10, P6, P5 | (P13 RUNTIME — validation policies reference validators by id) |
| P15 | P8–P14 | the full substrate + contract + machinery |
| P16 | P15 (Coder exec, Web search), P14, P13, P10 | Data→Teacher intra-phase edge (Finding 3) |
| P17 | P15/P16 (Macro shape, borrowed caps), P14, P13, P10, P8 | + its own sensor/helper lanes |
| P18 | P8, P14, P17, P5, P12 | full contribution-point coverage |
| P19 | P12, P18, P10, P14 | built-in slice needs only P12 (Finding 4) |
| P20 | P9, P8, P3, P2 | (+P14/P18 sync-eligibility declarations, by reference) |
| P21 | P13, P14, P15–P17 (corpus), P12 | P20 by reference only (sink-credential patterns) — soft, may overlap (§4) |
| P22 | P21, P18, P19, P17, P0/P4 | |
| P23 | all | |

**Acyclicity:** every hard prerequisite references a strictly lower-numbered phase; walking the
table top-to-bottom, no back-edge exists. Forward references in the files (e.g., P8 "elevated helper
→ P17", P9 "export/import → P20", P13 "Simulate/FullRerun → P21") are all **deferred-to/closed-by
edges, not build prerequisites** — the earlier phase defines the contract + durable state, the later
phase realizes the implementation behind the unchanged seam.

## 2. Load-bearing ordering-edge compliance

| # | Edge | Holds? | Where |
|---|---|---|---|
| 1 | Canonical encoding before any hash | ✓ | P1 lands encoding/hash; block/diff/view hashes (P3), capture encodings (P10), package hash (P20), release hashes (P0/P22) all after |
| 2 | Storage before the spine | ✓ | P2 < P3 |
| 3 | `context_view` before run commits | ✓ | P3 < P6 |
| 4 | Capability registry before any capability invocation | ✓ | P5 < P6; P4's round trip is a `CommitMessage`-class service operation, not a capability invocation (Finding 1) |
| 5 | `capability_class` typed before policy resolves on it | ✓ | both in P5; lane (a) explicitly gates lane (b) — the in-phase gate is named in P5 §4 |
| 6 | Secret boundary before any credential | ✓ | P2 forms < P7 vault < the first real credential (P7 provider); P6 uses a credential-free mock |
| 7 | `provider.token-source` before strategy / real calls | ✓ | P7 internal order vault → provider → strategy is declared serial |
| 8 | The one DAG executor before automation/workflows/eval-runs | ✓ | P6 < P13 (EvalRun is a Run) and < P14 |
| 9 | Ledger/events before observability/audit surfacing | ✓ | P3 < P21; audit-chain scaffold P3, crypto binding P7/P8, surfaced read-only P21 |
| 10 | Policy before sandbox enforcement | ✓ | P5 < P8 (File 23 consumes touched-resource matching + the approval router) |
| 11 | The filesystem chokepoint before any file-mutating capability | ✓ | P8 < P9 (materialization) < P15 (Coder); the P2 StorageEngine exception is documented (overview §6.1) |
| 12 | Surface contract before any surface | ✓ | P11 < P15–P17; P4's minimal surface is a seed explicitly matured by P11 §5.2 |
| 13 | Replay substrate before replay-dependent layers | ✓ | P3 (data + contract) + P13 (Inspect engine) < P21 (Simulate/FullRerun, comparisons) |
| 14 | Validator machinery before surfaces register validators | ✓ | P13 < P15 (39 §10.2's load-order rule is satisfiable) |
| 15 | The one Scheduler before surface monitors | ✓ | P14 < P15 (28 §12, 29 §17.4, 30 §17.4, 32 §12 alias over it) |
| 16 | World/perception before GUI/System surfaces | ✓ | P10 (+P17's additive sensors) < P17 |
| 17 | Trust/integrity before source approval | ✓ | P8 < P18 |
| 18 | Webhook trigger framing before the webhook transport | ✓ | P14 < P18 |
| 19 | Crash-capsule consent before crash-handler egress | ✓ | P21 < P22 |
| 20 | The borrow graph: Coder exec + Web/Data extraction before Teacher | ✓ | P15 < P16; Data's extract/chart slices sequenced early within P16 (Finding 3) |

## 3. Forward-reference resolution (every deferral lands)

| Deferred from | To | Closed? |
|---|---|---|
| P0 hash/signature on bare artifacts | P4 installers; P22 full pipeline | ✓ named in P4 §2/§5.7 and P22 §3 |
| P0 BuiltinBundle manifest skeleton | P22 | ✓ P22 §5.3 |
| P2 secret-boundary forms / detector | P7 vault; P8 trust/egress | ✓ P7 §5.1, P8 §5.7 |
| P3 forgery-guard engine vs contract type | P6 | ✓ P6 §5.3 |
| P3 snapshot resolvers (stubs) | P7 (pricing/settings), P10 (world/registry) | ✓ P7/P10 build plans |
| P3 replay contract / Inspect data | P13 engine; P21 modes | ✓ P13 §5.6, P21 §5.1 |
| P4 thin IPC window | P12 | ✓ P12 §1 |
| P4 logging baseline | P21 | ✓ P21 §2 |
| P5 headless approval harness | P12 verbatim rendering | ✓ P12 §5.5 |
| P5 source-approval shapes | P18 | ✓ P18 §5.1 |
| P5 availability predicates (always-true) | P10 evaluator | ✓ P10 §5.2 |
| P6 mock `ModelStep` | P7 | ✓ P7 §5.3 ("the headline") |
| P6 conservative token estimator / no-op auto-shrink | P7 | ✓ P7 §5.5–5.6 |
| P6 discovery ids (`mcp.search`) | P18 | ✓ P18 §2 |
| P6 world-snapshot refs unresolvable | P10 | ✓ P10 §5.6 |
| P6 in-process-only cancellation | P8 forceful kill | ✓ P8 §5.3 |
| P8 elevated helper absent | P17 | ✓ P17 §5.2 |
| P8 device-trust shapes | P20 pairing | ✓ P20 §5.5 |
| P9 workspace export/import | P20 | ✓ P20 §2 (24 §16) |
| P9 entity Validation/Critique orchestration | P13 | ✓ P13 §2 |
| P10 sensor set (FS/Env/Repo/Process) | P15 (BrowserPage), P17 (desktop/system/audio) | ✓ P15 §2, P17 §2 |
| P10 implicit learning/consolidation (14 §8.2) | P14 (§5 consolidation cadence) | ✓ P14 §5.6 |
| P11 Trigger-rail / external-protocol framing | P14 scheduler; P18 transports | ✓ P14 §2, P18 §2 |
| P11 Voice rail gated off | P17 | ✓ P17 §5.10 |
| P13 eval families seeded per producer | P21 full set + gates | ✓ P21 §2 |
| P14 graduation (34) / P18 install (35) eval-pass gating (40 §10.4) | P21 | ✓ P21 §2 + §5.3 (the eval-pass gate is realized at P21 and wired into 34 graduation + 35 install; P14/P18 build their primitives ungated, P21 adds the gate) |
| P14 watchdog absent | P21 (42 §16) | ✓ P21 §2 |
| P14 macro recording mechanics | P15 (Web) / P17 (GUI) | ✓ P15 §2, P17 §2 |
| P19 first-paint cache mechanism | P22 (43 §10.3) | ✓ P22 §2; P19 matrix row marked partial (Finding 4) |
| P4 runtime update-relaunch absent | P22 (42 §18) | ✓ P22 §2 |
| Settings locality declared (P4) | P20 enforcement | ✓ P20 §2 (15 §18 / 21 §5) |

Every deferral in the overview §5 maturation table resolves to a phase that names it.

## 4. Lane-parallelism check

| Claim | Real? | Reasoning |
|---|---|---|
| P0–P6 strictly serial | ✓ | each phase's hard prereq is the immediately prior one; within-phase lanes only |
| P8 sandbox-core ∥ P7 | ✓ | P8 §3 names P5/P6 as the core lane's only hard prereqs; only trust/egress waits on the vault |
| P13 ∥ P11/P12 | ✓ | P13's prereqs (P6/P9/P3/P2) are disjoint from P11/P12's outputs |
| P15 Coder ∥ Web | ✓ | no surface depends on another surface — the widest lane |
| P16 Data ∥ Teacher (mostly) | ✓ with Finding 3 | Teacher's teach-from-document + progress slices wait on Data's extract/chart slices, sequenced early in-phase |
| P17 GUI ∥ System after shared lanes | ✓ | sensors + helper + self-protection built once, consumed by both |
| P18/P19/P20/P21 overlap windows | ✓ | per the overview §3 graph; each names its true prereqs |

## 5. Findings (tracked, none blocking)

1. **P4's round trip is pre-capability — deliberate, not a bypass.** The message commit is a
   `CommitMessage`-class service operation (File 26 §4's resolution vocabulary), not a capability
   invocation; no capability side effect occurs before P5's registry exists. Track: P11 §5.5 must
   retrofit the P4 entry path onto the Conversation rail contract — it does.
2. **P14→P13 is a soft edge.** Automation validation policies reference validators by id (RUNTIME);
   the merge order P13 < P14 keeps them resolvable at save time. No reorder needed.
3. **P16 carries an intra-phase edge** (Teacher's two slices ← Data's extract/chart). Handled by
   lane sequencing inside the phase file; Teacher's conformance rows for those slices must not be
   marked done before the Data slices merge.
4. **P19 exits with a partial row**: the first-paint cache is a rebuildable projection from P19 but
   its concrete mechanism is 43-owned and closes in P22. The conformance matrix carries it as
   partial; P19's exit criteria do not claim it.
5. **P10 lists P7 as optional.** Lexical-only retrieval is spec-valid (12 §6.1); enabling vectors
   later requires the embedding identity tuple already locked in P10 — no retrofit risk because the
   tuple is schematized regardless of whether a backend is configured.
