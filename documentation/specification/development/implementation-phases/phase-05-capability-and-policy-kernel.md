# Phase 5 — Capability & Policy Kernel

## 1. Goal & why now

The single operation primitive and its single authority layer: the Capability Registry validating
full `CapabilityDeclaration`s (with File 04's execution metadata and the typed `capability_class`
schematized up front), the Approval Router as the +100 hook running deterministic effective-tier
resolution, durable Leases, typed-confirmation with the `Denied` carve-out — plus the five
interaction objects (File 02) they will govern. Every later operation enters through this registry
and this policy pipeline; routing, execution, rails, surfaces, automations, plugins, and providers
all presuppose it. This phase deliberately breaks the 04↔05↔06↔07 chicken-and-egg cluster at the
spec-documented stub points.

## 2. Canonical scope & deferrals

- **File 05 — core**: `CapabilityDeclaration` full required field set (§2.2, §3) **including the
  File 04 §8.2.2 execution-semantic fields** (`concurrency`, `reversibility_class`, `idempotent`,
  `preview_mode`, `partial_output_meaningful`, `cooperative_stop_deadline_ms`,
  `sibling_abort_on_failure`, `resume_on_restart`, `terminates_sequence`, `replay_class`,
  `classification_mode`, `result_bounding`) **and the typed `capability_class`** policy will resolve
  on; schemas + `error_vocabulary` (§4); permission tiers + `TierResolver` + `permission_floor` (§5);
  `touched_resources` typed expressions + canonical resource classes + **the resource-expression
  grammar** (§6); `replay_class` (§7.3); sources + trust-state shape (§9); `RegisteredCapability`
  state, distinct from the immutable declaration (§10); the `CapabilityInvocation` record shape
  (§11, owned at execution time by P6); registry operations + events (§12);
  identity/namespacing/semver/schema_version (§13); collision resolution (§14); availability-contract
  *shape* (§15.2–15.3 — the evaluator arrives **P10**); startup registration **phase 1: Builtin**
  (§16.1, slotted into boot step 8); settings dimensions (§18). Plugin/MCP/API/user sources →
  **P18**.
- **File 06 — core**: the Approval Router as the single blocking `ToolCallProposed` hook at +100,
  composing the named inspectors with authority classes (§3); **`policy.effective-tier-resolution`**
  — the fixed-order algorithm + closed terminal-outcome set + tier-to-outcome mapping (§4); ask-user
  + typed-confirmation flows (§5.2–5.3, §7) incl. the **`Denied` carve-out** (§7.4); the **`Lease`**
  durable primitive — events as source of truth, lease record as projection, the lifecycle
  Active/Stale/Revoked (§11); lease selection (narrower-wins → deny-wins → most-recent) +
  touched-resource containment for filesystem/network classes (§6); **built-in reusable safety
  rules** (force-push-to-protected, account-delete, credential-export, dangerous-shell →
  `AlwaysDeny` + typed-confirmation override) (§11.5); approval-policy templates + the verdict
  lattice (§12); contradiction-checking (§14); risk classification (§15); the approval-UI **data
  contract** (§13 — consumed headless now, rendered verbatim in **P12**); posture presets (§16.3);
  mid-execution re-evaluation, event-driven (§10 — world-change triggers wired in **P10**).
  Auto-decide (§8, off by default) → after **P7** (needs a real model); the full source-approval
  flow → **P18** (typed shapes land now).
- **File 02 — complete**: Conversation/Message/IntentThread/Task (§1–§6) with the activity-state
  reduction (§2.3, over a stubbed run-state source until P6), the task minimum schema + monotonic
  revision + revision-safe updates (§6.2, §7.2), driver transitions (§6.4), ownership-chain identity
  (§7.2), the pre-dispatch contract shape (§3.4). `RunIntent` remains a stub envelope until P6.

## 3. Prerequisites

P4 — boot step 8 slot, settings resolution; P3 — hooks, ledger, blocks (registrations, policy
events, and decisions are ledgered; the audit overlay records policy facts).

## 4. Lanes

Three lanes: (a) declaration types + validation + registry operations + restart determinism;
(b) the policy engine — tier resolution + leases + the router with its inspectors, converging at
`ApprovalDecision`; (c) the File 02 interaction objects. Lane (b) consumes lane (a)'s
`capability_class` — the explicit cross-lane gate (the canonical wrong-order trap).

## 5. Build plan

1. **Registry**: declaration validation (reject-on-missing-field — a declaration lacking
   touched-resources / error vocabulary / replay-class / execution metadata / `capability_class` is
   invalid); Builtin source + ServiceMethod/Closure backends (closure ⇒ `not_replayable` enforced);
   registration atomicity; collision reject-by-default + reversible shadowing; alias-aware lookup;
   `resolve_for_invocation`; registry events; restart re-registration determinism (05 §16.6).
2. **Resource-expression grammar** (05 §6.4): parser + containment semantics for filesystem-subtree
   and network host-set classes first (06 §6.3 consumes it for lease matching); prose-only
   expressions invalid for write-capable capabilities.
3. **Policy engine**: effective-tier resolution exactly in spec step order (declared → floor clamp →
   trust narrowing [stub: all System] → scope overrides → lease lookup → decision); the closed
   outcome set; the router registered at +100, failing closed, every decision ledgered + audit-
   overlay-written.
4. **Leases**: durable lease *events* → lease projection (the File 11 §16 `Projection` contract's
   first non-spine consumer); selection rule; declarative typed revocation conditions (ad-hoc
   procedural revocation rejected); built-in rules re-register at boot, then user overrides apply as
   separate audit-visible records (06 §11.5).
5. **Typed-confirmation**: always-asks; never persists; never batched; the `Denied` carve-out as the
   only path through `Denied`.
6. **Interaction objects** (File 02): durable Conversation and Message, the Message anchored over the
   block pool (a Message anchors a primary block); IntentThread single-primary-ownership; Task with revision-safe
   concurrent updates (succeed / typed-conflict / branch); activity-state reduction.
7. **Headless approval harness**: policy emits the §13 data-contract objects; a test harness consumes
   and answers them (06 §13.8) — P12 renders the *same* contract verbatim.

## 6. Test obligations & acceptance evidence

- Registry: registration-validation conformance per required field + atomicity + typed errors
  (05 §12.3); **`capability_class` present and typed on every declaration** — the explicit gate that
  must hold before policy resolves on it; touched-resource expression conformance (§6.1);
  closure-above-`not_replayable` rejected (§7.3); registry-state-vs-declaration separation —
  enable/disable/trust/collision never mutate the declaration, `(id, version)` immutable (§10/§13);
  platform-as-availability — incompatible capability catalogued `UnavailablePlatform`, not absent
  (§9.4); restart determinism (§16.6); collision tests (§14.1).
- Policy — the named suites: **floor-never-pierced** (no setting, lease, trust upgrade, scope
  override, `agent.unrestricted_mode`, or template lowers below `permission_floor`;
  `PolicyFloorViolated` + floor wins); **typed-confirmation-unliftable** (no lease/auto-decide/
  batch/trust/mode lifts it; per-call; never an `AlwaysAllow` lease); **tier-determinism** (same
  declaration + context + leases + settings → same `EffectiveTierDecision`; closed outcome
  mapping); **no-silent-decision** (every allow/deny emits `PolicyDecisionMade`; denial in-band;
  contradictions surface typed, never silently resolved); lease lifecycle (selection determinism —
  never averaging/votes; containment + fallthrough incl. canonicalized paths; staleness → ask-user
  with reason, never silent revoke; event-driven re-evaluation, no polling); `Denied` carve-out;
  router fail-closed on timeout/config error (§3.5); lease validation (§11.2); restart — built-ins
  re-register then overrides apply (§11.5/§11.6); audit-overlay membership for every policy
  decision/lease event/floor violation.
- File 02: state-reduction precedence fixtures (§2.3); single-primary-attachment invariant (§5.4);
  revision-conflict property tests (§7.2); driver-transition recording (§6.4); ownership-chain
  completeness (§7.2).
- **Closed-set pinning**: `ApprovalDecision`, terminal outcomes, lease scopes, inspector authority
  classes, source/backend taxonomies, tier set, task lifecycle enum.
- No-hardcoded-numeric-policy-defaults audit (06 §17 — thresholds/batch-sizes/timeouts live in
  settings profiles).
- Conformance matrix gains: `capability.*` core, `policy.effective-tier-resolution`,
  `policy.lease-primitive`, `policy.permission-floor`, `policy.approval-router`, `intent.*` anchors.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `CapabilityDeclaration` (the full field set),
  `ApprovalDecision`/`Lease`/`EffectiveTierDecision`/`ApprovalRequest`/`ApprovalResponse`/
  `SourceRegistrationProposal`; migrations for the registry + lease/policy-event families; the
  built-in reusable-rule default set as a versioned, audit-visible registration (not hardcoded
  behavior).
- **Docs**: capability-registry module doc + declaration field-set reference + id/namespacing doc +
  the `Action`-superseded note; policy module doc + router/inspector composition + floor/
  typed-confirmation + lease lifecycle docs; **banned-vocabulary update** (goose mode, YOLO
  classifier, permission grant, AskForApproval, auto-approve toggle).
- **CI/local commands**: the floor-not-pierced, typed-confirmation-unliftable, tier-determinism,
  no-silent-decision, and `capability_class`-present suites as named CI jobs.

## 8. Exit criteria

- [ ] A registered Builtin capability can be proposed (synthetic `ToolCallProposed`), policy-
      resolved, allowed/denied/asked, leased, revoked — every decision ledgered, explainable, and
      audit-chained — all headless.
- [ ] Effective-tier golden suite green; lease grant→use→revoke→restart cycle green.
- [ ] Task revision-conflict property tests green; conversation state-reduction goldens green.
- [ ] The P4 skeleton still boots and round-trips (no regression).

## 9. Locked in this phase

- **The `CapabilityDeclaration` required field set incl. the File 04 execution metadata and
  `capability_class`** — THE operation contract Files 06–43 consume; defining these late forces a
  registry-wide migration. This is why they are schematized now, one phase before the executor
  consumes them.
- **The resource-expression grammar** (05 §6.4) — every stored lease and policy decision depends on
  it.
- **Effective-tier-resolution step order + the tier-to-outcome mapping** (06 §4) — changing it
  changes every approval decision ever made.
- **Lease event shapes** (the durable source of truth; the lease record is a projection).
- The permission-tier set + lease-scope set (authored 04 §11, bound here); the approval-UI data
  contract shapes (06 §13); capability id namespacing + `(id, version)` immutability.
- Task lifecycle enum + minimum schema + revision counter (02 §6.2).
