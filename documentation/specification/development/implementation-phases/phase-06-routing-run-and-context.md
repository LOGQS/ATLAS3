# Phase 6 — Routing, Run Model & Context Assembly (M1: Loop Closed)

## 1. Goal & why now

A user message becomes a governed run: the File 03 dispatch pipeline emits a real `RunIntent`, the
File 04 run model executes it through the capability call pipeline with the completion-contract
termination floor live, the File 13 read-side assembler builds every model request deterministically,
and the File 07 tool surface projects the registry. End of phase: a complete conversation turn against
a **mock `ModelStep`** (canned tool-call + text behind the `capability.backend-descriptor` seam) —
fully ledgered, versioned, replayable, forgery-guarded, with real policy on the path. This is
milestone **M1 (loop closed)** — the design-risk retirement gate: when this merges green, every later
phase adds breadth against a proven spine.

## 2. Canonical scope & deferrals

- **File 03 — complete core**: the 7-step dispatch pipeline for every trigger kind (§3); the routing
  frame — four input categories, `compact` default router-context policy, never full-raw-replay as
  default (§3.1; world-model snapshot stubbed → **P10**); deterministic prechecks via the hook
  system — ordered, settings-enabled, short-circuiting (§3.2); the router with **local-classifier
  substitution** (§3.3 explicitly allows it; the model router becomes real after P7); full
  `RunIntent` schema + closed enums (§4); continuity attachment (§5); the durable route record —
  every precheck verdict + pre-routing transformation recorded (§3.5); fast path as real
  router-owned capability work, not a policy bypass (§9); visibility/override (§10);
  retry/edit/reroute rules + mid-execution reroute (§11–§12); routing settings (§13). Routing
  summaries (§6) deferred until richer context policies are wanted.
- **File 04 — core**: `Run` + required attachments (§2.2); status enum + ledgered transitions
  (§2.4); `control` field (§2.6); **`RunCompletionContract` + authority-gated monotonic revision**
  (§2.7 — completes the contract object whose guard mechanism landed in P3); the standard lifecycle,
  no mandatory phases (§6); the model/tool loop with the mock `ModelStep` (§7); the full capability
  call pipeline — resolve → normalize+validate → input validators → proposal → hooks → **real P5
  policy** → execute → stream partials → record → postconditions → commit (§8.2), incl. input
  normalization + typed in-band schema mismatch (§8.2.1) and bounded results + terminal-result hints
  (§8.2.2); tool-surface zone consumption (§10); approval-during-execution wired to P5 (§11);
  streaming/partials (§12); mid-execution input (02 §5.5); the single DAG executor for parallel
  topologies — concurrency tags, disjoint-resource-scope parallelism, stable result ordering,
  sibling-failure handling (§15 — filesystem mutation keying completes in **P8** with 23 §7.3);
  task promotion/updates (§18); retry/reroute/branch (§19–§20) + stuck-detection scaffolding
  (model-mediated off); budgets, opt-in (§21); **termination + the deterministic completion-forgery
  floor integrated end-to-end** (§22); ledger/event/commit/hook integration (§23); restart
  orphan reconciliation — `process_restart_orphan`, never auto-resume (§17.3, completing boot step
  13). Closes `SimulateDeterministic`/`FullRerun` re-execution data paths against recorded inputs
  (engine orchestration → P13/P21). Child-run isolation primitives (§16) → **P8/P9** (worktrees).
- **File 13 — read side**: `ContextAssemblyService` as the single model-request path from day one
  (§1); AssemblyParts + per-part authority/sensitivity (§2); semantic regions (§3); `ContextPolicy`
  Minimal/Full (§4); router assembly (§5); the deterministic single-pass algorithm (§6); retention
  priority + non-destructive overflow + `BudgetReport` (§7–§9) over a conservative local token
  estimator (§10 tiers — provider-keyed counting → **P7**); `AssemblySnapshot` per model-bound
  invocation (§19). Compaction write-side (§12–§14) → **P7**.
- **File 07 — complete core**: the computed `ToolSurface` projection (§2); the closed five-zone
  model (§3); `SubsystemSurfaceSpec` (§5); discovery-capability **ids registered** as Builtin
  (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `tool.inspect`; `mcp.search` id reserved
  — mechanics → **P18**) (§7); `BorrowGrant` (§7.3); the deterministic 17-step composition —
  byte-identical from identical inputs (§9); model-request presentation + the untrusted-data
  instruction boundary + cache-friendly ordering (§11); persistence/reconstruction (§14);
  auto-shrink registered behind its setting as a no-op until real budgets (§8 → **P7**).

## 3. Prerequisites

P5 — registry, policy, interaction objects. P3 — spine, forgery-guard engine. The mock `ModelStep`
honors the future File 17 request/response shape; its recorded fixtures become the deterministic
test double for all later CI (overview §6 rule 5).

## 4. Lanes

(a) Routing — frame, prechecks, classifier-router, `RunIntent`, route record; (b) run model + call
pipeline + DAG executor (tightly coupled, largely serial internally); (c) context read-side
assembler; (d) tool-surface composition. (c) and (d) are independent of (a) and join (b) at the loop.

## 5. Build plan

1. **Routing**: frame builder (capability families from the P5 registry; placeholder model/provider
   metadata per 03 §4.4); prechecks (explicit-override + exact-capability-invocation first);
   classifier-as-router; `RunIntent` materialization; durable + replayable route record.
2. **Run model**: run creation from `RunIntent` (fast-path results materialized, never invisible);
   lifecycle with snapshot refs (registry/settings real; world/pricing resolvers stubbed); the loop:
   compile context (13) → mock model step → tool calls through the **full call pipeline with real
   policy** → commit boundaries (11) → completion decision under the contract floor.
3. **Completion integrity end-to-end**: P3's guard engine + P5's authority model + this phase's
   contract object — the full forgery chain integration (04 §2.7/§22 ↔ 10 §3.7).
4. **Context assembly**: deterministic assembler; parts carry authority classes (the structural
   substrate P8's injection defense composes with); `AssemblySnapshot` persisted for every
   model-bound invocation.
5. **Tool surface**: compose for the ModelAgent lens; byte-determinism; consumed-surface ledger
   snapshots; rendered into the request by 13; `tool.borrow` issuing run-scoped `BorrowGrant`s
   through the full pipeline.
6. **DAG executor**: parallel topologies under concurrency tags; resource-scope serialization
   (string-level until P8's canonical-path keying); no silent last-write-wins; sibling-abort vs
   continue per declaration.
7. **Restart**: orphan-run reconciliation completes boot step 13; retry/edit/reroute as version
   branches.

## 6. Test obligations & acceptance evidence

- **Completion-contract forgery (the crown-jewel test)**: a run whose contract required action
  cannot reach `completed` on fluent prose; the agent cannot weaken its own contract; a
  qualifying-authority weakening passes only through the ledgered revision path (04 §2.7/§22,
  10 §3.7).
- **Routing-never-bypassed**: every trigger kind passes routing before downstream execution;
  pre-filling/inheritance constrain routing, never skip it (03 §2/§14). **Fast-path-not-a-bypass**:
  an approval-requiring capability still requires it on the fast path; fast-path failure recorded,
  never discarded (§9.3–9.4). Route-record completeness + replay determinism (§3.5); closed-enum
  validity (§4.3); single-attachment (§5.1); edit-invalidates-route (§11.2); override validity
  (§10.3); precheck determinism + short-circuit ordering.
- **Pipeline correctness**: a handler never receives schema-invalid arguments; normalization is
  declaration-backed; coercion never broadens touched resources/tier/scope (04 §8.2.1); denial is
  in-band; raw/normalized argument records ledgered with redaction; bounded-envelope mandatory +
  hint-never-completes (§8.2.2); every side effect through the pipeline — no bypass; every commit at
  a canonical boundary.
- **DAG executor**: disjoint-scope `Exclusive` calls parallelize; same-resource read-modify-write
  serializes; stable result ordering; **no silent last-write-wins**; parallel-failure visibility
  (§15.3–15.4).
- **Assembly determinism** (13 §6) over frozen inputs; **snapshot-replay with live sources
  disconnected** (`context.assembly-replay-snapshot`, §19); overflow non-destructive — reports
  pressure, never drops user content silently (§9); authority is per-part, not per-region (§2.3);
  fail-safe on undecidable sensitivity (§2.4); the current user request never replaced by a summary
  (§5).
- **Surface determinism**: byte-identical `ResolvedToolSurface` + rendered request from identical
  snapshots (07 §9.2); **surface-vs-policy separation** — visible ≠ permitted, invisible ≠ blocked
  (§3.6/§10); consumed-surface snapshots reconstruct what the model saw (§2.3); cache-friendly
  ordering stability (§11.7); BorrowGrant scope non-transfer across retry/edit/branch (§14.3);
  no-clock composition (§17.5).
- Cancellation/restart: cooperative stop honors `cooperative_stop_deadline_ms`; orphan runs surfaced,
  never silently resumed; `partial_output_meaningful` governs orphan-block promotion; retry safety —
  unknown-outcome non-idempotent calls are not auto-retried (`UnknownOutcomeRequiresReview`); elapsed
  time is never proof of recovery (04 §17/§20.2.1).
- Keyed per-call attribution enforced on the loop's ledger entries (04 §23.1).
- **E2E (the M1 test)**: message → route → run → tool call → approval round trip (headless harness)
  → bounded result → completion — asserted against ledger/version/block contents; then replay the
  route + assembly + surface snapshots and compare byte-stably. **Mock-seam isolation**: swapping the
  mock `ModelStep` for a different mock changes only the model step — proving the P7 swap point.
- **Closed-set pinning**: trigger kinds, `attachment_kind`, `execution_entry`,
  `tool_surface_strategy`, run statuses, retry shapes, authority classes, regions, zones, invoker
  kinds.
- Conformance matrix gains: `routing.*`, `run.*` core (esp. `run.completion-contract`,
  `run.call-pipeline`, `run.hook-integration`), `context.assembly-replay-snapshot` + 13 read-side,
  `surface.*` core.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `Run`/`RunIntent`/`RunCompletionContract`/
  `CapabilityInvocation`/`RouteRecord`/`AssemblyPart`/`AssemblyOutput`/`BudgetReport`/
  `ResolvedToolSurface`/`SubsystemSurfaceSpec`/`BorrowGrant`; migrations for the run/route/
  assembly-snapshot/borrow-grant families; **the mock-provider fixture format** (recorded
  request/response pairs — the CI test double for the project's lifetime).
- **Docs**: run-model + executor doc; the completion-contract + forgery-guard doc; the call-pipeline
  reference; routing dispatch-pipeline + fast-path-vs-cheap-routing docs; assembly algorithm +
  authority-class reference; zone-model + composition-algorithm reference; decision record for the
  mock-`ModelStep` seam (so P7 knows the contract it swaps into).
- **CI/local commands**: the completion-forgery, routing-never-bypassed, fast-path-not-a-bypass,
  assembly-determinism, surface-determinism, no-last-write-wins, and cancellation/restart suites as
  named CI jobs; the M1 full-loop integration + restart-reconstruction job.

## 8. Exit criteria

- [ ] **M1**: the full governed loop green in CI on 3 OSes — including a policy approval round trip
      — and byte-stable under snapshot replay.
- [ ] The forgery-chain integration suite green (the run that tries to lie cannot complete).
- [ ] Mock-seam isolation proven; recorded fixtures drive the loop deterministically.
- [ ] M0 still green (no regression).

## 9. Locked in this phase

- **`RunIntent` field schema + its closed enums** (03 §4) — the execution-entry contract, durable in
  route records.
- **Run status enum; `RunCompletionContract` shape + requirement kinds + revision protocol**
  (04 §2.4/§2.7).
- **The capability call-pipeline step order** (04 §8.2) and the bounded-result envelope shape
  (§8.2.2) — wire shapes for every capability ever.
- **`AssemblyPart` authority classes + the semantic region set + `AssemblySnapshot` contents**
  (13 §2–§3, §19) — the replay-determinism contract.
- **The five-zone model; `ResolvedToolSurface` shape; composition step order + byte-determinism;
  the discovery-capability canonical ids** (07).
- The mock-fixture format (CI's deterministic backbone).
