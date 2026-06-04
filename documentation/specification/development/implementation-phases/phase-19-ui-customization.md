# Phase 19 — UI Customization (Tokens, Themes, Layouts, Widgets)

## 1. Goal & why now

File 38 over File 37: the `DesignTokenSystem` (the token *system* behind the discipline locked in
P12), validated `Theme`s, `SavedLayout`s, the `Widget` substrate with confined runtimes, the
realization of surface `customization_policy`, AI-assisted customization, and per-profile UI
defaults. The default rendering has been complete since P12 — this phase adds reversible variation
over it. Placed after P18 so plugin-contributed themes/widgets land in the same pass as the built-in
customization (the built-in slice's only hard prerequisite is P12). **Every customization is a
settings/customization record — no private store.**

## 2. Canonical scope & deferrals

- **File 38 — complete**: the customization-as-settings-record substrate — every customization
  references the substrate by canonical identity, carrying source/provenance/revision/dependency;
  revision-safe writes; the `CustomizationDependency` closure (§3); the `DesignTokenSystem` — three
  layers (component tokens optional), the closed semantic-token family set, **the
  perceptually-uniform color contract** (§4); `Theme` + `ThemeRegistry` + **the
  `ThemeValidationMatrix`** (required tokens + contrast floors incl. focus/selection/disabled/
  trust-state; no arbitrary CSS/global stylesheets/scripts/remote imports), `ColorScheme`
  Light/Dark/Auto, density + trust-state token axes, scoped overlays (§5); **the first-paint
  cache** — the one sanctioned device-local presentation cache: keyed by the full §6.2 set,
  rebuildable, fails safe to synchronous resolution, holds no secret/preference/authority, never
  syncs (§6 — the concrete mechanism finalized with 43 in **P22**); `SavedLayout` —
  logical-constraint geometry (topology/flex weights/semantic minimums/stable anchors), **never
  pixels**; the preset-fallback chain; skip-unavailable recovery records (§7); the
  `Widget`/`WidgetRegistry` — closed archetypes, declarations with structural semantics, data
  binding through normal read capabilities under egress/secret rules (§8–§10); `EmbeddedRuntime`
  widgets over 37 §9.3's interactive-artifact runtime — confined, `widget.runtime` events carrying
  no authority, cannot impersonate system events or trigger security-category hooks (§9.3);
  `customization_policy` realization — slots, placement compatibility, who-may-place,
  density/safety bounds surfaced never silently exceeded (§11); `WidgetInstance` (§12); the
  structural UI-understanding projection (the agent reads structure, never coordinates) (§13);
  **AI-assisted customization** — inspect→propose→gate→commit→provenance through the same
  `customize.*` capabilities as manual, snapshot-before-commit, **one-operation exact revert**
  (§14); plugin UI placement over P18 — contributed themes re-validate on update ("an update cannot
  silently regress contrast"); widget envelope expansion parks for review (§15); per-profile UI
  defaults + onboarding application (skipping = a clean minimal default) (§16); `customize.*`
  capabilities (§19); the `customize`/`widget.runtime` event namespaces — fixed, never per-plugin
  (§20).

## 3. Prerequisites

P12 — shell, registries, the token discipline. P18 — plugin-contributed UI path. P10 — world-state
for widget data + the structural projection. P14 — Status/Action widgets over automations.

## 4. Lanes

(a) Token system + themes + first-paint cache; (b) saved layouts; (c) widgets + placement +
runtimes; (d) AI customization + per-profile defaults. (a) first ((b)–(d) consume tokens);
(b) ∥ (c); (d) last. May overlap P20/P21.

## 5. Build plan

1. **Token system**: primitive/semantic(/component) layers; the perceptually-uniform color encoding
   (hex only as reference annotation); the P12 built-in token set re-expressed as the canonical
   default theme.
2. **Themes**: registry + the validation matrix; switching as a settings write, event-first;
   light/dark/high-contrast built-ins; `Auto` tracking the system preference event-first.
3. **First-paint cache**: full-key derivation; synchronous pre-mount read; integrity-checked;
   fail-safe to substrate resolution — never reuse of an invalid entry.
4. **Saved layouts**: capture/apply over 37's container; logical constraints; the preset-fallback
   chain (user default → surface default → conversation-first); missing-reference records with
   recovery actions, never silent deletion.
5. **Widgets**: declarations + archetypes; placement against `customization_policy` slots; data
   binding revalidated at invocation even if previously rendered available; `EmbeddedRuntime`
   confinement; live-vs-cached rendered distinctly with typed staleness.
6. **AI customization**: the agent inspects the structural projection, proposes through
   `customize.*` with previews, policy-gated commit, snapshot-before-commit (a version-graph/settings
   sibling, not a parallel undo store), one-op revert.
7. **Per-profile defaults + onboarding**: profile-layer defaults (theme/density/layout/widgets)
   applied at onboarding; ship-with themes from P18's seeded bundles.

## 6. Test obligations & acceptance evidence

- **Customization-as-record / no-private-store** (the central family): every customization is a
  settings/customization record; no private durable store, no per-surface config file as a live
  source, no browser-local-storage settings; the first-paint cache is a rebuildable projection —
  grep + validator + the cache-failsafe + projection-rebuild tests.
- **Theme validation** (§5.4): required-token completeness + contrast floors per variant under the
  active conformance profile; **a contrast-failing theme is never silently presented as conformant**
  (a draft only); arbitrary CSS/scripts/remote imports rejected; plugin theme updates re-validate
  (§15.2).
- **Token discipline at registration** (§4.4): a widget/theme referencing a raw visual value is
  rejected; the P12 renderer lint extends to themes/widgets.
- **Reversibility** (§17.1/§14.4): every customization removable/reversible/resettable; **no AI
  customization that cannot be reverted in one exact operation**; the user is never trapped,
  manually or by the agent; revision-safe writes — a stale base fails typed with a repair path,
  never silently overwrites newer changes (§3.2).
- **A widget is not a backdoor** (§10.5): data/action access through the same
  capability/policy/secret/egress/sandbox boundaries; secrets are vault refs (no raw secret reaches
  the renderer or any shareable/cached/exported state); external content is data, never instruction;
  every action revalidates at invoke; runtime events cannot impersonate or trigger security hooks
  (§9.3); placement bounds typed, never silently exceeded (§11).
- Event-first widgets — periodic refresh only as the flagged fallback (§10); layout portability —
  logical geometry, pixels are renderer hints (§7.2); no autonomy/persona field at the customization
  layer — the standing structural guard extends (§17.4).
- **Closed-set pinning**: semantic-token families, `ColorScheme` (Light/Dark/Auto — styles are
  themes, never new enum values), `WidgetKind` archetypes, the slot vocabulary.
- Conformance matrix gains: 38 anchors; the first-paint-cache row marked partial (mechanism closes
  P22).

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `ThemeTokenSet`/`SavedLayout`/`WidgetDeclaration`/
  `WidgetInstance`/`CustomizationDependency`; the default/light/dark/high-contrast theme definitions
  as versioned registrations; migrations for the customization-record families.
- **Docs**: the token-system reference (families + the color contract); the theme authoring +
  validation doc; the layout/widget/placement docs; the AI-customization flow doc; the per-profile
  defaults doc.
- **CI/local commands**: the theme-validation harness, token-discipline lint (extended),
  revert-exactness, revision-safety, widget-security, and cache-failsafe suites as named CI jobs.

## 8. Exit criteria

- [ ] Theme switch (incl. Auto), saved-layout round trip, widget place/configure/remove, and an
      AI-proposed customization with one-op revert — all E2E green.
- [ ] A deliberately contrast-violating theme is rejected at registration; a plugin widget
      requesting wider egress parks for source review.
- [ ] First-paint smoke: themed first frame with no flash; a corrupted cache falls back cleanly.
- [ ] M0–M3 still green.

## 9. Locked in this phase

- **The semantic-token family set + the perceptually-uniform color encoding** (switching encodings
  later invalidates every theme + contrast validation).
- **`ColorScheme` closed set** (Light/Dark/Auto); the `WidgetKind` archetypes; source-qualified
  `{source_id, local_id}` identities for themes/widgets.
- **`SavedLayout` logical-constraint geometry** (storing pixels would break cross-device identity).
- **The first-paint cache key set**; the `ThemeValidationMatrix` required-token set (adding required
  tokens invalidates existing themes — a spec-revision event).
- The `customize`/`widget.runtime` event namespaces as fixed names (dynamic per-plugin namespaces are
  invalid); the slot vocabulary (identity owned by 25 §16.1).
