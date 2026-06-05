# Phase 17 — Surfaces Wave 3: GUI Control & System Agent

## 1. Goal & why now

The last two baseline surfaces — the highest-risk, heaviest perception + sandbox + policy consumers
in the canon: **GUI Control** (perception-grounded, adapter-first desktop control) and **System
Agent** (safe-system-operation over the host OS). They come last among the surfaces deliberately:
they require mature perception, world-state identity, policy floors, typed confirmation,
self-interaction guards, process control, and observability before they can be safely useful. This
phase also lands their prerequisites: File 19's desktop/system sensor completions and File 23 §11's
**elevated-helper process model**. Both surfaces are excluded from other surfaces' default zones
(borrow-only under their own postures). At exit, the six-surface baseline is complete (32 §23).

## 2. Canonical scope & deferrals

- **File 19 — additive completion**: the `DesktopAccessibilityTree` sensor (role/name/bounds/state,
  modal scope, embedded-web handoff to `BrowserPage`, element-cache invalidation on OS UI events,
  diff-based re-traversal); the `Screen` sensor with coordinate-space/scale-factor recording; full
  `SystemMetric`/`Network`/`Liveness` contracts; `VisualGrounding`/`Ocr` processors (model-routed,
  availability-gated); the `Audio` sensor + VAD + consent (unblocking 26 §9's Voice rail).
- **File 23 — §11**: the elevated-helper model — a separate least-privilege binary, **lazily
  installed on first privileged use, never at app install**; a versioned built-in operation manifest
  over local IPC (rejects arbitrary command strings); `ExecutableArtifact` canonical-hash integrity;
  the main process never elevates; every elevated op audited.
- **File 31 — complete core**: the GUI Control `SurfaceContract` (`surface_id: gui_control`,
  `gui.*`); structured-first observation → element-grounded action → **the observe-act-verify loop**
  with read-before-act staleness (§6–§8); action-targeting + input-dispatch tier ladders —
  structured reference → accessibility identity → coordinate → vision-grounded, each a fallback
  (§7.2, §8.2); **the coordinate-space mapping discipline** — model coordinates mapped from their
  recorded space through scale factors before dispatch; an unresolvable space is a typed error,
  never a blind dispatch (§8.3); **the self-interaction block** — `SelfInteractionBlocked` before
  dispatch for Atlas-owned targets (§8.1); post-action verification + loop detection → hard stop
  (§8.5); window/application management as ManagedProcesses (§13.4); application adapters —
  adapter-first, generic accessibility default, vision final recovery; narrowing-only adapter policy
  defaults (§9); macros (the shared `Macro` shape) with fresh revalidating playback (§10);
  **operating modes as isolation tiers** — active-desktop/background = `None` security isolation
  (cloaking is presentation, marked as such), untrusted automation = `Virtualized` (§13);
  destructive-target/sensitive-context/out-of-focus escalations to the `Denied`-floor
  typed-confirmation a per-tool `AlwaysAllow` never lifts (§11.3); takeover + resume over the run
  `control` field; takeover recording **off by default** (§12); first-run permission setup —
  `PermissionRequired`, guided acquisition, never silently granted (§14.3).
- **File 32 — complete core**: the System Agent `SurfaceContract` (`surface_id: system_agent`,
  `sys.*`); structured-first introspection + the health snapshot as the canonical first read (§6,
  §8.2); **the safe-operation lifecycle** — parse → guardrail → preview → approve → sandbox →
  execute → verify → audit → record-reversal, stage-for-stage on canonical owners — contributed
  posture, not a private middleware chain (§7.2); capability categories: the config store
  (cross-platform peer of the Windows registry), services, processes, packages
  (settings-overridable name mappings), network, device/power, filesystem maintenance with dry-run
  (§8); **the reversibility model** — Reversible/ReversibleWithSnapshot/Irreversible as capability
  metadata; a change = ledger entry + before/after `SystemStateSnapshot` observations + declared
  inverse (no `system_changes` table); **rollback = a fresh inverse invocation through the full
  lifecycle, never historical ledger replay**; multi-step rollback walks the provenance chain in
  reverse with typed partial-rollback stops; workspace-file changes reverse via the version graph
  (§9); scripts/shell with **`SecretInCommandLine` rejection** + out-of-band credential delivery
  (§10); **the denied-operation floor rules** (recursive root delete, whole-disk overwrite,
  disabling security/audit/update — settings-extensible, never hardcoded) +
  **`SelfModificationBlocked`** — Atlas-critical targets derived from runtime-known identities, not
  a hardcoded path list (§11); watches/schedules as thin Automation aliases — the metric-sampling
  interval is the flagged polling exception (§12); audit-overlay membership for world-affecting ops
  (§21.2); elevation only through the helper (§14.2); first-run setup per facility (§14.4).

## 3. Prerequisites

P15/P16 — borrowed capabilities + the shared `Macro` shape exist. P14 — watches/schedules. P13 —
postcondition validators. P10 — the perception substrate. P8 — sandbox, OsConfined, the trust/egress
layer. The Web↔GUI↔System environment boundaries (browser page / applications / OS) are now
enforceable.

## 4. Lanes

(a) Sensors (desktop tree, screen, system, audio); (b) the elevated helper; (c) GUI Control;
(d) System Agent. (c) and (d) are parallel after (a)+(b) and a shared self-protection lane (the
`SelfInteractionBlocked`/`SelfModificationBlocked` guards, built once, consumed by both). Voice-rail
enablement is a thin closing lane over (a)'s audio sensor.

## 5. Build plan

1. **Sensors first**: accessibility-tree capture per platform (typed gaps where mechanisms differ);
   screen capture with coordinate spaces; system sensors; audio + VAD + consent.
2. **Elevated helper** (23 §11): build + integrity-verify + lazy-install flow; one-shot-per-operation
   preference; every op audited.
3. **Shared self-protection**: Atlas-owned windows excluded from target sets; the Atlas-critical
   state set (data root, DB, blob store, vault, `.atlas/` internals, audit overlay, helper state,
   policy kernel) derived from runtime identities; both guards reject pre-dispatch.
4. **GUI observation slice**: `AccessibilityTreeSnapshot` observations; observation-local ordinal
   labels (never durable identity); the compact model-facing projection. Large tree and inspector
   renderers stay behind the `RendererRegistry` and are selected by measured per-platform evidence.
5. **GUI action slice**: element-grounded dispatch through confined input mechanisms;
   observe-act-verify; post-action diff + loop detection → corrective signal → hard stop;
   per-target escalations.
6. **GUI extras**: adapters; macros with revalidating playback; takeover/resume; vision tiers where
   a vision model is available.
7. **System introspection slice**: health snapshot + read-only introspection wherever the platform
   facility exists.
8. **System mutation slice**: the config store first through the full safe-op lifecycle, then
   services/packages/network/device/power/filesystem-maintenance; multi-target semantics declared
   (atomic/staged_compensating/best_effort_partial); idempotent-against-end-state = success.
9. **Reversibility + rollback**: before-state snapshots; declared inverses; multi-step provenance-
   chain rollback.
10. **Watches/schedules**: `sys.monitor.*`/`sys.schedule.*` as Automation aliases; Voice rail goes
    available (consent-gated, registry-derived intents — no hardcoded `SpokenIntent` enum).
11. **Registrations**: both contracts; GUI/system validators into 39; GUI + System eval suites into
    40.

## 6. Test obligations & acceptance evidence

- **No-private-architecture conformance**: both contracts pass the P11 validator; no private
  desktop-state model/capture pipeline/adapter registry/input mechanism; no `system_changes`/
  `system_watches`/`system_rollback_dag`/side-channel audit file — grep + validator.
- 31 — the conformance round-trips (§23), **replayed over recorded observations, never a live
  desktop; no historical replay re-captures or re-dispatches**: capture→structured-observation-with-
  fingerprint; element-grounded action→verified effect; the coordinate-space mapping; the
  observe-act-verify loop; destructive/disruptive/sensitive escalations; user-takeover-and-resume;
  **the self-interaction block**; macro revalidating playback; the adapter-first fallback chain.
  Plus: unresolvable coordinate space = typed error, never blind dispatch (§8.3 — the most-cited
  computer-use failure); read-before-act staleness (§7.3); per-target confirmation that
  `AlwaysAllow` never lifts (§11.3); captured foreign content holds no authority (§11.2);
  **cloaking-is-not-security** — background mode classified `None`, marked, immediate stop/takeover
  exposed (§13.3); capture redaction + no biometric inference (§11.5); first-run permissions never
  silently granted (§14.3); waits event-driven, never fixed delays.
- 32 — the conformance round-trips (§23 + §6): the safe-op lifecycle stage harness — preview
  produces a typed change preview without effect (§7.2); **the denied-operation floor** —
  structurally catastrophic ops denied, not liftable by `AlwaysAllow`/`agent.unrestricted_mode`
  (§11.2); **`SelfModificationBlocked`** pre-dispatch (§11.3); **rollback = fresh inverse**,
  revalidating the change is still in effect — never ledger replay re-applying live effects (§9.4);
  multi-step partial-rollback typed stops (§9.5); idempotent end-state = success (§6.4);
  **`SecretInCommandLine` rejection** + credential delivery channels (§10.2); verification uses the
  strongest identity evidence, weaker grades typed (§8.3); captured machine content =
  `untrusted_source_data` (§11.5); non-interactive runs pin posture + park on floors (§12.4);
  **the elevated-helper boundary** — manifest-only ops, integrity mismatch re-gates, main process
  never elevates, every op audited (23 §11/§21); watches event-first with the flagged sampling
  exception (§12.2).
- Environment-boundary tests: Web drives the page, GUI drives applications/chrome, System operates
  the OS — composition only via borrow/reroute.
- Renderer-performance evidence: large accessibility trees, element inspectors, process/service
  trees, rollback/provenance views, and equivalent system dashboards have File 40 `Latency` suites
  over recorded fixtures on all three desktop platform webview realizations.
- **Closed-set pinning**: dispatch tiers, operating modes, reversibility classes, multi-target
  semantics, env/PATH scopes, both surfaces' panel/selection/produced kinds (`Macro` shared;
  `SystemStateSnapshot`/`SystemHealthSnapshot` custom ObservationKinds; **no `Script` artifact
  kind** — a script is a file artifact).
- Conformance matrix gains: 31/32 anchors + 23 §11 + the 19 desktop/system/audio sensor anchors;
  the Voice-rail stub row closes. **The six-surface baseline is complete.**

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: both surface contracts; the adapter declaration shape; the elevated-helper
  operation manifest + integrity record; coordinate/action record schemas; recorded
  accessibility-tree/system fixtures.
- **Docs**: GUI surface doc (the perception-grounded reframe + the tier ladders); System surface doc
  (the safe-operation reframe + the reversibility model); the self-protection doc (both guards); the
  elevated-helper doc; per-platform mechanism notes with typed gaps.
- **CI/local commands**: the GUI round-trip, system safe-op lifecycle, self-protection,
  coordinate-mapping, rollback, helper-boundary, unattended-safety, and renderer-latency suites as
  named CI jobs — recorded fixtures in CI, live smoke local per platform.

## 8. Exit criteria

- [ ] GUI: a recorded cross-application task (observe → act → verify → complete) green in replay CI;
      live smoke locally per platform.
- [ ] System: a config-store mutation previewed, approved, applied at OsConfined, verified, rolled
      back via fresh inverse — fully audited; a privileged op crosses the helper boundary correctly.
- [ ] All six SurfaceContracts pass the P11 conformance harness; the environment boundaries enforced
      by tests; Voice rail live.
- [ ] M0–M3 still green.

## 9. Locked in this phase

- **The safe-operation lifecycle stage→owner mapping** (32 §7.2) and **the reversibility-class
  metadata + change-record shape** (ledger + snapshots + declared inverse; no system tables).
- **`SelfInteractionBlocked` + `SelfModificationBlocked`** — the agent may never puppet or mutate
  Atlas itself through these surfaces; the critical-target set derived from runtime identities.
- **The elevated-helper operation-manifest model + `ExecutableArtifact` integrity binding** (23 §11)
  — the privileged boundary forever.
- The operating-mode → isolation-tier mapping + the cloaking-is-not-security rule; the adapter
  declaration shape; coordinate/action record schemas; the denied-operation reusable-rule set
  (settings-extensible, never hardcoded); audit-overlay membership for world-affecting ops; the
  `gui`/`system_agent` event namespaces.
