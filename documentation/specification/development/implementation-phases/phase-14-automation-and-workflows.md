# Phase 14 — Automation & Workflows

## 1. Goal & why now

The two "fixed counterparts" that crystallize work into reusable, schedulable operations: File 34's
`Workflow`/`WorkflowGraph` (the execution-graph schema File 04 §5 deliberately left open) + the one
`TemplateLibrary`, and File 33's `Automation`/`Trigger`/the one `Scheduler` with the non-interactive
safety posture. Both sit on the core substrate, beneath the surfaces — every per-surface monitor,
pipeline, curriculum, macro, and saved command in P15–P17 aliases over these instead of growing
private engines. This phase also lands File 42's worker substrate (the Scheduler and watch poller are
its first real `BackgroundWorker`s). Built before the surfaces so the aliasing rule is enforceable
from each surface's first monitor feature.

## 2. Canonical scope & deferrals

- **File 42 — §6/§7/§8**: `BackgroundWorker` + `WorkerState` + `WorkerSupervisor` +
  `SupervisionPolicy` (restart/backoff/circuit ladder); bounded backpressure-aware resume-first
  `WorkQueue`; the single-armed `RuntimeTimer` — placed at boot step 13 with shutdown drain order.
  The missed-heartbeat watchdog is P14's in full: the §6.4 deadline substrate and the §6.5
  supervisor response to `Stalled` (restart/backoff/circuit) both ship in the supervision engine;
  the generalized §16 operational-health orchestration (route-around, degrade, surface — across
  providers, connectors, storage, and sidecars) → **P21**.
- **File 34 — complete core**: the `WorkflowGraph` body grammar — nodes/edges/`EdgeCondition`/
  activation; the closed `NodeKind` set with `Model`/`Tool`/`Branch`/`Merge` first, `Loop`
  (bounded, mandatory max-iterations)/`SubWorkflow` (recursion-guarded, acyclic reference graph)/
  `Programmatic` next; **no `Approval`/`Human`/`ManualDecision` node kind, even via `Custom`** (§3);
  typed parameter slots + **the no-raw-interpolation invariant** — security-sensitive fields never
  caller-bindable, credential slots are vault refs (§4); composition + workflow-as-operation via
  **adapter capability only** — a `Workflow` is distinct from a `Capability` and a `Skill` (§5); the
  reusable-unit family + the `Skill`/`InstructionFragment` boundary (§7); the one `TemplateLibrary`
  over the shared `dag_configs`/`dag_presets` persistence — no parallel workflows/templates/macros
  tables (§8); sources + sharing (§9); creation & graduation — crystallization-from-successful-run
  primary, **the promotion forgery guard** (§11); validate-before-save + simulation/dry-run
  (coverage-aware, no external side effects) + output contracts + `declared_effect_envelope` with
  understatement rejection (§12); execution as an ordinary `Run` — topological waves, pin-at-save +
  run-time revalidation (later stricter policy wins), `NodeExecutionFingerprint` node-output reuse
  (device-local cache), the four-option retry vocabulary over 04/11 mechanics (§13);
  `workflow.*`/`template.*` capabilities (§14–§15). Macros (§6) → recorded by surfaces in P15/P17.
- **File 33 — complete core**: the `Automation` object — the governing field set as a versioned
  block-backed `Custom{automation, definition}` entity; no `automations`/`scheduled_tasks` tables
  (§6); the closed `TriggerKind` set — `Schedule`/`Event`/`Manual` now, `WorldCondition` over
  `world.watch` (available since P10), `Webhook` *framing* (transport → **P18**) (§2);
  `RecurrenceRule` (Once/CalendarLocal/ElapsedDuration) + **single-armed-timer discipline** (§3);
  `WatchPolicy` — Edge default, hysteresis/dedupe/debounce (§4); **the one `Scheduler`** as
  supervised workers — detection only, never execution (§9); the deterministic eligibility gate
  chain + **`fire_id` atomic claim** (§8–§9); fired trigger → RouteRequest → ordinary Run +
  intent-thread attachment + target-conversation validation (§10); **the non-interactive safety
  posture — park-and-notify**; typed-confirmation/`Denied` floors never lift unattended;
  pre-authorized scope = leases; the recursive-trigger cycle guard (§11); overlap policies (§12);
  failure handling + circuit breaker — retryable-only retry (§13); validation policy + output
  contract — failing either = failed run (§14); creation paths + no-silent-creation (§15); the
  surface-aliasing rule (§16); the persistence split — definitions durable+syncable, arming state
  device-local and reconstructed (§18); `automation.*` capabilities incl. ReadOnly `test_trigger`
  (§19).

## 3. Prerequisites

P11 — Trigger-rail framing, elicitation for park-and-notify. P13 — validation policies reference 39
validators (RUNTIME — definitions reference by id). P10 — `world.watch` + perception signals. P6 —
routing pin-through, the run model + DAG executor (the graph slot 34 fills). P5 — leases.

## 4. Lanes

(a) The 42 worker substrate; (b) workflow grammar + library + graduation; (c) the scheduler +
triggers + eligibility + non-interactive posture; (d) NL/manual creation flows. (a) first (the
scheduler runs on it); (b) ∥ (c) — they share the parameter contract and pin-at-save shape, fixed in
a short joint design note before the lanes split.

## 5. Build plan

1. **Worker substrate** (42 §6–§8): registration declaration (owner/liveness-signal/supervision/
   reconstruction-source/shutdown-order/idempotency-marker); supervisor ladder; bounded queues;
   single-armed timers; boot step 13 + drain order.
2. **WorkflowGraph + library**: the grammar + structural validator (acyclic, bounded loops,
   resolvable refs, parseable constraints, envelope-understatement rejection); parameter slots;
   library persistence over `dag_configs`/`dag_presets`; the adapter-capability invocation path;
   graduation from a successful run gated by the promotion forgery guard (reusing the P3 guard
   mechanism at crystallization time). The workflow DAG editor renders through the `RendererRegistry`
   and must meet the heavy-graph renderer-performance gate before the phase exits.
3. **Execution**: workflow runs as ordinary Runs — nodes map to 04 execution units; ready nodes run
   in topological waves with deterministic completion order; per-node policy gating;
   `WorkflowNodeComplete` commits (11 §5.2); pin-at-save-time field set (the single realization all
   surfaces defer to).
4. **Scheduler**: definition load → trigger arming (one timer per next-fire instant, never
   busy-poll) → fire → eligibility gates (blocked fires recorded with gate + reason, never silently
   dropped) → atomic claim by `fire_id` → RouteRequest with `trigger_kind: automation` → run in the
   validated target conversation with intent-thread attachment; missed-fire reconciliation at
   startup under the cold-start guard (joins boot step 12); firing state reconstructed from
   definitions, never persisted.
5. **Non-interactive posture**: park-and-notify through the elicitation rail; pre-authorized scope
   via leases with the lease-dependency projection (a later gate failure records the specific
   `lease_id`); the cycle guard; save-time rejection of unbounded self-retriggering.
6. **Watches**: `WorldCondition` triggers over `world.watch` + 19 signals; Edge-firing default with
   reset/hysteresis/dedupe; memory-consolidation cadence becomes the first real Automation.
7. **Creation flows**: `automation.create_from_run` (graduation primary) + manual construction;
   every path requires explicit user acceptance; agent-initiated creation passes source-approval and
   defaults `UserApproval`.

## 6. Test obligations & acceptance evidence

- **One scheduler / one trigger / one automation** (the central family): no parallel scheduler/
  watch-poller/cron-runtime; no automation tables; firing state reconstructed from definitions at
  startup, persisting none — grep + the startup-reconstruction test.
- **One workflow primitive / one grammar / one library**: no parallel engine/store/tables; a
  workflow is not a capability or a Skill; runs-as-a-`Run` with no separate runtime — grep +
  validator.
- 33 — the named suites: **event-first timing** — a Schedule trigger arms a single timer, never
  clock-polls; next-fire is a pure recomputed function; missed fires reconciled per policy,
  coalesced for `RunOnce`, recorded never dropped; **atomic fire** — duplicate `fire_id` links to
  the original, never a second run; **unattended-safety (the headline)** — anything beyond direct
  allow/deny parks-and-notifies and waits without timeout-based auto-resolution;
  typed-confirmation/`Denied`-floor ops never execute unattended; non-interactive is strictly
  weaker; **pin-at-save + reproducibility** — fire-time routing fills only unpinned fields; a later
  stricter policy/revoked lease wins over the pin; **eligibility + no-silent-drop** — gate chain
  deterministic, evidence recorded + linked by `fire_id`, no routing into tombstoned targets;
  **payload authority** — trigger payloads are `untrusted_source_data`, bind only through declared
  slots; cycle guard; overlap determinism + bounded concurrency + accepted-fire restart survival;
  retryable-only retry + circuit breaker (cooldown is a safety guard, recovery is event/state/user-
  driven); validation/output-contract failure = failed run; `run_locality` resolution —
  `any-device` stays unarmed without an atomic cross-device claim; `test_trigger` is ReadOnly and
  never creates a run; **no-silent-creation**.
- 34 — the named suites: **promotion forgery guard** — a hollow run (empty trace, no outputs)
  cannot graduate; **structural validate-before-save** matrix (cycles, unreachable nodes, unknown
  refs, unbound required inputs, reference cycles, unbounded loops, unparseable constraints,
  understated envelopes — errors block); **no-raw-interpolation** — values only through declared
  typed slots, body/capability-identity never caller-bindable, `Secret` params redacted everywhere;
  **simulation commits no side effects** + coverage-aware (`SimulationUnavailable` for
  side-effecting nodes without previews); **output contract** — completing without satisfying it is
  a failed run; **`NodeExecutionFingerprint` cache correctness** — the full output-affecting input
  set, non-deterministic nodes reuse only on explicit retry, cache stores committed block refs never
  raw secrets, device-local; deterministic wave ordering; **no manual-decision node kind** —
  approvals park through policy, input through elicitation; sibling versions on concurrent edits.
- 42: worker restart never double-executes a committed side effect (idempotency-keyed/
  completion-marker-guarded); accepted consequential work never discarded by queue overflow —
  overflow observable; timers tested with the injected clock; the missed-heartbeat path proven
  with the injected clock — heartbeat deadline elapses → `Stalled` → force-terminate →
  supervision-policy fold (restart-with-backoff or circuit-open).
- Workflow DAG renderer performance: a File 40 `Latency` suite covers representative node counts and
  edge shapes on all three desktop platform webview realizations; DOM/SVG-heavy rendering is
  acceptable only while it meets the declared interaction budget.
- **Closed-set pinning**: TriggerKind, RecurrenceRule variants, WatchPolicy fields, OverlapPolicy,
  missed-fire policy, `run_locality`, NodeKind, EdgeCondition, activation rules, scorer-role and
  source taxonomies.
- Conformance matrix gains: 33/34 anchors + 42 worker anchors.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `Automation`/`Trigger`/`RecurrenceRule`/`WatchPolicy`/
  `fire_id` derivations, `WorkflowGraph`/`NodeKind`/parameter slots/`NodeExecutionFingerprint`,
  `BackgroundWorker`/`SupervisionPolicy`; migrations for the definition/library/lease-dependency
  families (definitions syncable, arming/cache device-local).
- **Docs**: the scheduler + trigger + eligibility reference; the non-interactive-posture doc; the
  workflow grammar + parameter-contract + graduation docs; the 33↔34 fixed-counterparts doc (body vs
  trigger binding); the worker-substrate doc; **banned-vocabulary update** (autopilot, cron job,
  scheduled_tasks, Human/Approval node).
- **CI/local commands**: the timer-vs-poll, missed-fire, fire-idempotency, unattended-safety,
  promotion-forgery, structural-validation, no-raw-interpolation, simulation-coverage, and
  workflow-dag-renderer-latency suites as named CI jobs (injected time throughout — no wall-clock
  waits).

## 8. Exit criteria

- [ ] A successful run graduates into a Workflow; the Workflow runs as a scheduled Automation; a
      typed-confirmation step parks it and notifies — end-to-end in CI with injected time.
- [ ] Restart mid-cycle: armed state rebuilt from definitions, missed fires reconciled, accepted
      fires resumed — no loss, no duplication (`fire_id` proofs).
- [ ] Scheduler + watch poller live as supervised workers; the kill-a-worker chaos test green.
- [ ] M0–M2 still green.

## 9. Locked in this phase

- **The `WorkflowGraph` grammar + the closed `NodeKind` catalogue** — THE schema
  `run.execution-structure` left open; the executor, every surface's pipelines/classrooms/data
  nodes, and every automation bind to it. The highest-leverage lock in this phase.
- **`NodeExecutionFingerprint` composition**; `EdgeCondition`/activation enums;
  `declared_effect_envelope` shape; the parameter-slot shape (shared with 33's automation
  parameters).
- **The closed `TriggerKind` set + per-kind `fire_id` derivation** (idempotency keys in the ledger
  forever); the `Automation` field set + its `Custom{automation, definition}` representation;
  RecurrenceRule/WatchPolicy/OverlapPolicy/missed-fire/`run_locality` enums.
- **The pin-at-save-time field set** (33 §6.3 / 34 §13.2) — every surface's "pin surface and
  policies" rule realized once.
- 42's `BackgroundWorker`/`SupervisionPolicy`/`WorkQueue`/`RuntimeTimer` contracts (every later
  worker declares against them).
