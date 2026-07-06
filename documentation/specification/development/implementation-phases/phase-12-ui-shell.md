# Phase 12 — UI Shell

## 1. Goal & why now

The full File 37 presentation layer matures the P4 window: Shell regions, the RendererRegistry with
the canonical baseline renderers, transcript as a pure block-pool projection, the focused-dialog
selector rendering the approval/elicitation contracts verbatim, streaming, accessibility, i18n, and
the semantic-token discipline. The shell must precede the six surfaces (P15–P17) so they render
through one container and one renderer registry instead of inventing private UI. The renderer holds
**no business logic and no durable state** — and the backend remains fully usable headless.

## 2. Canonical scope & deferrals

- **File 37 — complete core**: presentation-as-projection + `PresentationView` (every view declares
  its substrate source + event-first rebuild trigger, holds no source-of-truth fact) (§3); the
  `RendererRegistry` — one registry dispatching every typed substrate kind, contributed renderers via
  the proposal-first source-approval path, **safe typed placeholder for unknown/unavailable kinds,
  never a crash or blank** (§3.3); the `Shell` region model + default conversation-first layout with
  regions collapsed (§4); the layout container — recursive split, PanelState, resize/dock/detach
  (§5); surface presentation/morphing over 25's ViewPresets (§6–§7); the `InteractionModel` lens
  set — presentation-only (§7.2); conversation/transcript rendering over `context_view` + **parallel
  activity rendered readably, never one forced flat stream** (§8); substrate-primitive rendering
  incl. version history/comparison (§9); typed-partial streaming — partial→committed without
  remount/flicker, stream-gap markers, sticky scroll distinguishing user vs renderer scroll (§10);
  rail presentation — palette/keybinding-editor/steering affordances over 26 (§11); **the
  focused-dialog selector + verbatim approval/elicitation rendering** — one presentation focus per
  renderer root over the shared pending set; never double-answered, never stale in another root;
  security dialogs never auto-approve/deny/expire on UI timing (§12); management surfaces v1 —
  context inspector ("what did the model see" over AssemblySnapshots), settings manager with
  "why is this active?", registry browser (§13); the accessibility contract — verified, not assumed
  (§14); i18n — every string a key, dev-visible missing-key diagnostics (§15); the renderer
  boundary — tokens-only visuals, typed IPC, no in-renderer network server (§16); UI state-space
  (loading/empty/error/degraded/first-run) (§17); multi-window — independent renderer roots over one
  service layer (§4.5); `ui.*` capabilities + events (§20–§21).
- Deferred: the design-token *system*, themes, widgets, saved layouts → **P19** (File 38; this phase
  consumes the token *discipline* against a built-in default token set); the interactive-artifact
  runtime (§9.3) → **P19** (with widget-runtime confinement); observation viewers for
  desktop/browser captures → with their surfaces (P15/P17).

## 3. Prerequisites

P11 — rails to render and route gestures into; the surface contract for morphing. P10 — SurfaceState
self-registration (the UI both renders and produces it). P6/P7 — runs to present, streams to render.

## 4. Lanes

(a) RendererRegistry + baseline renderers; (b) shell regions + layout container; (c) transcript +
streaming; (d) dialogs + management surfaces; (e) a11y/i18n/token hardening across all of them.
(a)/(b) first, (c)/(d) over them. Cross-phase overlap: P13 may proceed in parallel (independent
prerequisites).

## 5. Build plan

1. **RendererRegistry**: kind→component dispatch (BlockKind/ArtifactKind/ObservationKind/PanelKind/
   AppEvent/media); registration through the proposal-first path; renderer trust ≠ content trust;
   the typed placeholder fallback; **a contributed renderer never shadows a canonical baseline
   renderer** — a contribution registered for a kind that has a baseline cannot override it (37 §3.3);
   renderer choices are per-kind implementations behind the registry, not canonical library commitments.
2. **Shell + layout**: regions (command rail, focus surface, inspector dock, execution console,
   conversation view, status, notifications); the default conversation-first preset; progressive
   disclosure as the staging axis; per-region auto-reveal configurable with badge-only selectable.
3. **Transcript**: projection over the active version's `context_view`; lifecycle/pin states
   rendered; version history/branch navigation; derived presentation identity via CanonicalEncoding
   (§8.2 — selection/collapse/replay alignment).
4. **Streaming**: typed partials over 10 §12; one continuous element across partial→committed;
   gap markers; auto-follow that never yanks the user.
5. **Dialogs**: the focused-dialog selector over the shared pending-request set with the
   deterministic priority tuple; approval (06 §13) + elicitation (26 §13) rendered **verbatim** —
   the P5 headless harness and this UI are two clients of one contract; persistent requests survive
   restart; revalidation before presentation and action.
6. **Execution console + steering UI**: run projection (04 §25); cancel/pause/takeover affordances
   via the steering rail.
7. **a11y + i18n + tokens**: WCAG 2.1 AA baseline; full keyboard operability; screen-reader
   semantics from the structural-semantics contract (every interactive panel/control self-registers
   role/label/interaction-kind — structural invisibility is invalid); string-key extraction; the
   token-discipline lint (raw visual values rejected).
8. **Management surfaces v1**: context inspector, settings manager, registry browser — read paths
   over existing services.
9. **Multi-window**: focus-or-create secondaries; device-local restore revalidated against current
   displays; focused-dialog correctness across roots.

## 6. Test obligations & acceptance evidence

- **Presentation conformance** (§24): no business logic or private durable store in the renderer
  (no policy/route/model-selection/availability computed in a view); every view a projection with
  loss-is-a-rebuild; verified by grep + validator + a projection-rebuild test of presentation state.
- **a11y verified, not assumed** (§14.2): automated checks on every surface/dialog/state including
  loading/empty/error; keyboard-only and screen-reader E2E paths; focus restoration; drag/drop
  alternatives.
- Placeholder fallback + **baseline-renderer anti-shadowing** — a contributed renderer cannot
  override a canonical baseline renderer for its kind (§3.3); token-discipline lint (§16.5); i18n
  key-coverage + hardcoded-literal lint, missing keys visible in dev (§15).
- Streaming: partial→committed without remount/flicker; **a streamed partial is never persisted as
  truth**; reconnection rebuilds views from substrate + ledger and marks unreconstructable gaps
  (§10.2); auto-follow distinguishes user-initiated scroll (§10.3).
- **Multi-client dialog correctness** (§12.2): one typed response resolves for all roots — never
  double-answered, never stale; security dialogs never resolve on UI timing; verbatim-contract
  rendering — no parallel approval/elicitation shape exists (grep).
- Self-registration mandatory: every interactive panel/control registers structural state on
  mount/focus/selection/change; structurally-invisible controls are invalid (§18, with 25 §5.2).
- Secret-masked rendering, incl. screenshots/exports (§3.2/§19); views never poll (§3.2);
   compile-time IPC type-bridge break test (§16.2); interactive-responsiveness budgets as tested
   settings, not constants (§16.6).
- Renderer-performance evidence: any shell, inspector, registry, graph, canvas, or large-list panel
  introduced here has a File 40 `Latency` suite over recorded fixtures on the three desktop platform
  webview realizations; the weakest supported engine's result is binding for the budget.
- Headless parity retained: the CLI client still drives the same flows (the service layer is
  rendering-agnostic).
- Conformance matrix gains: 37 anchors; the P4 thin-IPC stub row closes.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: the typed IPC bindings extended (break-the-build on drift); the
  i18n string-key catalog (extraction-generated); shared types for `ShellRegion`/
  `InteractionModel`/`NavigationTarget`/`PresentationView`.
- **Docs**: shell + region-model doc; the RendererRegistry reference; the
  presentation-as-projection doc; the focused-dialog + verbatim-contract doc; the a11y conformance
  doc; the i18n conventions doc.
- **CI/local commands**: the a11y suite (automated + keyboard E2E), i18n key-coverage check,
  token-discipline lint, placeholder-fallback test, multi-client dialog suite, streaming
  continuity suite, and renderer-latency suite as named CI jobs.

## 8. Exit criteria

- [ ] Full conversational UX over the real backend: transcript, streaming, tool-call cards, approval
      dialogs, steering, history navigation — Playwright E2E green on 3 OSes.
- [ ] a11y suite green; i18n at 100% key coverage; token lint green.
- [ ] Headless CLI parity proven again; M0–M2 still green.

## 9. Locked in this phase

- **`ShellRegion` + `InteractionModel` closed sets**; the structural prohibition on
  autonomy/persona/mode fields at every UI layer (§7.3/§23) — including "plan-vs-build" phase
  fields.
- **RendererRegistry dispatch keys** (one registry, no parallel renderer table).
- **The derived presentation-identity scheme** (§8.2 — selection/collapse/replay alignment breaks if
  changed).
- **The semantic-token discipline** (the token *system* lands in P19; the renderers-consume-only-
  tokens rule is permanent now).
- **The `NavigationTarget` typed contract**; PanelState set (shared with 18 §5.3); the
  verbatim-contract rendering rule (any 06 §13 / 26 §13 change ripples here — no parallel shapes
  ever).
