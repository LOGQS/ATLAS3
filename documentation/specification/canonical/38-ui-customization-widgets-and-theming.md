# UI Customization, Widgets, and Theming

## Status

Canonical. This file defines the customization layer of the presentation: the design-token system and themes, user-saved named layouts and the save/switch/customize flow, the `Widget` primitive and widget placement, the realization of the surface `customization_policy`, AI-assisted customization, plugin UI placement, and per-profile UI defaults. It consumes the contracts File 37 declares — the `Shell` region model, the layout container, the `RendererRegistry`, `PanelKind` rendering, built-in `ViewPreset` rendering, the `InteractionModel` lens set, and the semantic-token *discipline* — and realizes the `customization_policy` `worksurface.views-presets` (File 25 §7.4) declares and the widget/theme/view-preset/panel contribution kinds `plugin.contribution-points` (File 35 §5.2) routes here. It is the second UI-layer spec: horizontal and surface-neutral, the way File 37 is. The default rendering is complete without this file; this file adds customization over it. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the customization layer as a set of net-new presentation declaration primitives over File 37's container and the one settings substrate, owning no private durable store: a customization is a settings/customization record (File 15) rendered by File 37's container and registries, never a parallel persistence path, realizing `core.invariants` (File 01 §7.7/§7.9/§7.10) and `ui.renderer-boundary` (File 37 §16)
- the precise disambiguation of "customization," "widget," "panel," "block," "theme," "design token," "layout," "preset," and "slot," and the distinction of a `Widget` from a `PanelKind` (File 25 §5.3), a `Block` (File 08), an `Artifact` (File 09), a `PresentationView` (File 37 §3), a `ShellRegion` (File 37 §4.2), and a `ViewPreset` (File 25 §7.2)
- the `DesignTokenSystem` — the three-layer primitive/semantic/component token model, the perceptually-uniform color contract, the relative-color derivation rule, and the discipline File 37 fixed (renderers consume only tokens) that this file's token system fills
- the `Theme` and the `ThemeRegistry` — a theme as a named override set over the semantic-token layer with light/dark color-scheme variants, theme registration and validation (required tokens, contrast floor), theme switching, per-surface token overlays, the high-contrast theme, and theme-as-contribution
- theme persistence, the event-first switching contract, and the single sanctioned device-local first-paint cache (the one carve-out from the no-private-store rule, framed as a rebuildable projection)
- the `SavedLayout` — a user-saved named layout over File 37's layout container, the save/switch/rename/reset/duplicate/set-default flow, the built-in-preset-versus-user-layout relationship, scope and skip-unavailable recovery, and the persistence/locality split
- the `Widget` primitive, the closed-canonical `WidgetKind` archetype set, the `WidgetRegistry`, widget rendering through File 37's `RendererRegistry`, the confined widget runtime for executable widgets, and the widget data/action source contract (the governed binding to substrate, capabilities, connectors, secrets, and plugin sources)
- the realization of the surface `customization_policy`: the slot/region model, the placement-compatibility contract, per-surface customization-freedom variation, and the who-may-place (user/plugin/AI) and density/safety bounds
- widget placement, per-instance configuration, multi-instance behavior, and the instance lifecycle
- the structural UI understanding contract — the semantic-relational projection the agent reads for customization, over File 18's live state, and the rejection of raw-coordinate reasoning as the primary interface
- AI-assisted customization as a capability flow (inspect → propose diff/preview → policy gate → reversible commit → provenance) over the same paths as manual customization, with no agent-only path or store
- plugin UI placement: the widget/theme/view-preset/panel contributions File 35 routes here, the default-slot-as-proposal rule, the confined plugin widget runtime, and the no-arbitrary-core-mutation invariant
- per-profile UI defaults (theme, density, font scale, default layout, widget set, startup layout) over File 15 profiles, the onboarding application as profile-layer defaults, the presets-are-seeds rule, and the rendering of the deleted participation/autonomy/persona field as a consequence — never a reintroduced mode dial
- customization safety and reversibility (removable, resettable, non-destructive, snapshot-before-commit, policy-gated), and the explicit rejection of reintroducing any autonomy/participation/persona field at the customization layer
- the persistence/locality/portability split, the `customize.*` capability surface, events, settings dimensions, explicit rejections, and consequences for later specs

This file does not define:

- the `Shell` region model, the layout container and its split/resize/dock/collapse/detach mechanism, panel-kind rendering, built-in `ViewPreset` rendering, the `RendererRegistry`, the `InteractionModel` lens set, the focused-dialog selector, streaming, the renderer boundary, or the semantic-token *discipline* — File 37 owns those; this file's themes, widgets, and saved layouts render through them
- the `WorkSurface`/`SurfaceContract`/`SurfaceRegistry`, the `PanelKind`/`SelectionKind` model, the `ViewPreset` declaration, the `customization_policy` declaration itself, or the no-private-architecture invariant — File 25 owns those; this file realizes the `customization_policy` and consumes the panel and preset declarations
- the `SettingDefinition`, the source-stack cascade, scopes, profiles, the TOML overlay, locality classes, agent exposure, or orphaned-value handling — File 15 owns those; every customization record is a settings/customization record persisted and resolved through it
- the live `SurfaceState`, `PanelState`, `Selection`, `UiMode`, the world-entity catalogue, the durability tiers, the self-registration contract, or the availability evaluator — File 18 owns those; this file's structural-understanding projection reads them and feeds the customization flow
- the `Plugin`/`PluginManifest`/`PluginRegistry`, the contribution taxonomy, bundle-granularity trust/approval, the install/update/uninstall lifecycle, or the agent/user install boundary — File 35 owns those; this file owns the UI customization registries the plugin's widget/theme/preset/panel contributions land in
- the policy-evaluation algorithm, effective-tier resolution, leases, approval flows, typed-confirmation, or the source-approval flow — File 06 owns those; this file's customization capabilities are gated by them
- the `Sandbox` contract, isolation tiers, process control, or the elevated helper — File 23 owns those; the confined widget runtime runs through them
- the secret vault, trust model, egress governance, encryption, or the untrusted-content rule — File 22 owns those; widget data access honors them
- the `Automation`/`Trigger`/`Scheduler` and the observability/consumption contract — File 33 owns those; widgets that surface automation output read that contract
- the `Workflow`/`WorkflowGraph`/`TemplateLibrary`, the `Connector`/`McpServer`/`ExternalApi`, the storage substrate, the sync transport, or the version graph — Files 34, 36, 20, 21, 11 own those; customizations ride them
- the installer, the auto-updater, platform window-decoration and tray mechanics, sidecar lifecycle, or the bundling of ship-with themes and plugins into the installer image — the Packaging, Platform, and Distribution spec (File 43) owns those; this file owns the theme/widget/layout declarations they distribute
- the concrete frontend library, bundler, canvas engine, color library, or component framework — those are the renderer implementation's and File 43's; this file specifies the provider-invariant contract

## Source Resolution

Families reviewed: the theming and visual-identity material (`cross-cutting/theming.md` — the three-layer primitive/semantic/component token system, the `[data-theme]` switch, "adding a new theme = one CSS file, no component changes", the light/dark/high-contrast/custom theme files, the glass and animation tokens; `ux-input/visual-identity.md` — the color primitives, 8px spacing scale, radius/elevation/typography/animation system, dark-primary/light-secondary themes, WCAG AA, responsive breakpoints; `ui/14-6-to-14-8-theming-additional-windows-state.md` — the settings-backed `useSetting('app.theme')` switch with no `localStorage`, the `[data-domain]` token overlay, the appearance settings section, the state-awareness hooks; `atlas3-core/CONSTRAINTS.md` §3 design tokens / §4 app-state-awareness / §7 settings / §2 i18n / §10 accessibility / §5 action registry); the layout-customization material (`ui/15-1-layout-customizability.md` — the recursive `SplitLayout` tree, `LayoutConfig`/`PanelLayout`, built-in presets per surface, drag-divider/panel-header, auto-save with preset fallback, layout selector and save-as flow; `ui/15-2-domain-based-workspace-morphing.md` — named custom layouts saved in settings, panel lifecycle states, background-activity indicators, animation tokens, skip-unavailable recovery; `ui/15-3-and-15-4-participation-levels-personas.md` — the `ViewPreset`/`PanelSlot`/`LayoutShape`/`ViewPresetService`/`PresetScope` model and the explicit "presets are not autonomy modes — a seed not a contract, every decision reversible"; `ui/14-1-application-shell.md` — the CSS token vocabulary, layout defaults by user type, drag-and-drop, theme toggle, scoping convention; `ui/context-management.md` — the context-inspector panel widget; `ui/14-2-chat-list-and-history.md` — the semantic-token vocabulary in use, inline-rename, virtual-scroll, state-awareness registration); the widget and per-profile-default synthesis (`kuzeys-ui-customization-and-widgets-addendum.md` — the user-authored charter; `unit11-cross-tool-learning.md` CT.5 widget/block kinds and the per-profile widget table, CT.8 canvas side-document, CT.12 scoped artifact storage, CT.13 in-artifact `window.atlas` API, CT.14 plugin bundles and per-profile presets, CT.18 personality preset over the persona block, CT.19 writing blocks; `unit13-ui.md` D13.11 widget block renderers, D13.12 the panel inventory and slot defaults, D13.13 the ten per-profile view presets and onboarding, D13.14 the device-local first-paint cache, D13.15 the perceptually-uniform theme token model and no-flash preload and per-surface relative-color overlay, D13.17 the floating-action registry, D13.18 the shimmer animation token; `unit15-ux-distribution-files-glossary.md` D15.D.6 the theme ship format and contrast validation, D15.VI.1 perceptually-uniform color migration, D15.VI.2 default-theme-not-only-theme and the per-profile default-theme table, D15.UX.5 the per-profile density/font/spacing table, D15.D.1 the plugin view-preset/panels/ux-defaults manifest contributions, D15.D.2 the per-profile ship-with plugins and their panels; `unit11a-memory.md` D11.M.12 the per-profile memory-browser presets and D11.M.16 the shared whiteboard widget; `unit11b-data-processor.md` the per-profile view presets and notebook layout); the cross-cutting substrate (`cross-cutting/blocks.md` view-as-projection and the `Custom` block kind; `cross-cutting/actions.md` the action registry, `ActionCategory::Custom`, runtime-closure handler, permission tiers, availability predicates; `cross-cutting/artifacts.md` the interactive sandbox runtime, three display modes, runtime-hint registry, host bridge, persistence model; `cross-cutting/settings.md` the setting-definition schema, `ui.theme`/`ui.compactness` built-ins, agent exposure, reactive subscriptions, TOML overlay; `cross-cutting/state-awareness.md` the structured-state mirror; `infrastructure/configuration.md` the five-layer precedence and secret-vault boundary; `agents/domain-architecture.md` the per-domain panel contributions and the no-participation-level deletion; `systems/17-agent-self-modification.md` the iframe sandbox display; `systems/19-scheduling-pipeline.md` and the scheduler dashboard widget; `distribution/packaging.md` the tray and multilingual UI; `foundations/architecture.md`/`foundations/stack.md`/`atlas3-core/TODO.md` the self-registration-into-the-token-system invariant and the locked stack); the strategic target-state review (`codex_recommendations.md` §10.1 task-centered shell, §10.3 task-mode layout presets, §10.4 morph-by-task-state, §10.5 named visual focus modes plus density and trust-state token axes, §10.6 dual-purpose accessibility, §3.2 the three state classes, §4.5 named layout profiles and "why is this active?" explainers, §14.10 the surface `layout_presets`/`focus_modes` fields); and the cross-ecosystem customization patterns (`existing_ecosystems/chatgpt_tool.md` the `user_settings` accent/appearance/personality read-then-set with allowed-values guard, the structured web widget types, the canvas side-document; `existing_ecosystems/claude_cowork_tool.md` the extension-driven artifact renderers and the design-system/theme-factory skills; `warp-compressed.md` the pane-tree persistence with persisted-versus-ephemeral discrimination, the settings macro with toml-path/sync/private/feature-flag, multi-source contribution discovery with precedence, and layout-config-as-agent-skill; `open-canvas-compressed.md` user-defined quick actions and reflection-derived style preferences; `onlook-compressed.md` the stable element-identity system, the visual-context-to-AI-context pipeline, and the read/edit toolset split; `langflow-compressed.md` the typed-edge slot-compatibility and the runtime tweak-without-mutating-definition pattern; `pi-compressed.md` the custom-renderer registration and per-renderer theme-context; `t3code-compressed.md` the shell/detail subscription split and per-instance accent; `tlbrowse-compressed.md` the embedded-canvas widget and the iframe-to-shell bridge; `multica-compressed-2.md` the workspace-scoped customization storage and the pinned-item model; `claudecodeui-compressed.md` the declarative renderer-config registry; `omi-compressed.md` the always-on ambient control bar; `open-webui-compressed.md` the presentation-settings catalogue and the collapsible content pattern).

Resolution rule: this file realizes and introduces, it does not re-own. The shell, the layout container, the rendering contracts, the `RendererRegistry`, the interaction models, and the semantic-token discipline stay File 37's; the surface contract, `PanelKind`, `ViewPreset` declaration, and the `customization_policy` declaration stay File 25's; the settings cascade, profiles, locality, and agent exposure stay File 15's; live state and the structural projection's source stay File 18's; the plugin bundle, contribution taxonomy, and install lifecycle stay File 35's; policy and approval stay File 06's; the sandbox stays File 23's; security and egress stay File 22's; storage, sync, and the version graph stay Files 20, 21, and 11's; automation and workflow observability stay Files 33 and 34's; connectors stay File 36's; the installer and distribution stay File 43's. This file owns the `DesignTokenSystem`, the `Theme` and `ThemeRegistry`, the `SavedLayout`, the `Widget` and `WidgetRegistry`, the realization of the `customization_policy`, the structural-understanding projection, the AI-assisted customization flow, the per-profile UI defaults, and the `customize.*` capability surface, and supplies each to the layer that consumes it.

Resolved tensions:

- **A customization subsystem versus a layer over the container and settings.** The sources offer two postures: a dedicated customization store and runtime (the per-tool pane-tree tables, the per-domain layout JSON files), or a thin layer whose every customization is a settings/customization record persisted through the one settings substrate and rendered by File 37's container. `worksurface.no-private-architecture` (File 25 §12.2), `ui.renderer-boundary` (File 37 §16.4 — the presentation layer holds no private durable store), and `settings.consequences-for-later-specs` (File 15 §21 — no parallel store or cascade) are decisive. This file adopts the layer posture absolutely: a `SavedLayout`, a widget placement, a per-widget configuration, a theme selection, and a per-profile default are all settings/customization records (§3); the net-new primitives this file introduces — `Theme`, `Widget`, `SavedLayout`, and the `DesignTokenSystem` — are declarations and registries over File 37's container, not a parallel persistence path or runtime.
- **Theme as a CSS-file swap versus a typed token override set.** The specbase describes themes as CSS files mapping semantic variables to raw values; the unit synthesis and distribution specs refine this to a typed token set keyed in a perceptually-uniform color space with relative derivation and contrast validation. A canonical UI spec must define provider-invariant contracts rather than copying one renderer library's syntax. This file defines the `DesignTokenSystem` and `Theme` as the provider-invariant *contract* (§4, §5) — three token layers, a perceptually-uniform color model, the override-the-semantic-layer rule, the required-token and contrast-floor validation, and the adding-a-theme-is-one-declaration property — and leaves the concrete color library, file format, and utility-class registration to the renderer implementation, consistent with how File 37 keeps vendor names out of the body.
- **Persona, personality, and participation as a customization dimension.** Nearly every reviewed source still attaches a personality preset, participation level, or persona to a profile or surface. The canon deletes the field at every layer (`core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17; `world.surface-state`, File 18 §5.5; `settings.explicit-rejections`, File 15 §20; `ui.interaction-models`, File 37 §7). This file adopts the deletion and fixes the per-profile consequence (§17): a profile default selects which theme, density, layout, and widgets open — the *consequences* the deleted fields once described — and any "personality" a profile carries is a Memory or instruction preset governed by File 14, a starting template the user edits, never a customization-layer mode, dial, autonomy control, or backend field.
- **Widget as a block renderer versus a placeable customization unit.** The sources use "widget" for two distinct things: a block renderer that displays a structured result inline in the transcript (a weather card, a chart) and a placeable ambient unit the user composes into a customizable region (a dashboard tile, a sidebar status panel). This file separates them (§8): the inline block renderer is File 37's `RendererRegistry` rendering a `Block` (`ui.substrate-rendering`, File 37 §9), already canonical; the `Widget` is the net-new customization primitive — a declared, placeable, configurable, data-bound unit a user, plugin, or agent composes into a slot. A `Widget` may *render* a block, artifact, or observation projection, but it adds placement, configuration, data/action binding, and lifecycle as a customization unit.
- **AI customization as a special path versus the one capability path.** The charter and the strategic review both insist that manual and AI customization use one layer, and that the agent customizes through the same interface a human does. `core.extension-integrity` (File 01 §7.10 — "AI-assisted customization must use the same system paths as manual customization") and `worksurface.views-presets` (File 25 §7.4 — "AI-assisted surface, view-preset, widget, or layout mutation is a capability flow: inspect, propose a diff or preview, pass policy, commit reversibly, record provenance") are decisive. This file adopts the one-path posture (§14): there is no agent-only customization API and no agent-only customization store; the agent reads the structural projection and proposes through the same `customize.*` capabilities the user invokes, every change is policy-gated and reversible, and natural-language customization resolves through the control rails into those capabilities.
- **Structural understanding versus coordinate reasoning.** The charter (§5) and the world-model spec resolve that the interface is described to the agent structurally and relationally — what surface, what regions, what is open, nested, focused, selected, collapsed, pinned, primary — and that raw pixel coordinates are a weak primary representation. `world.chosen-model` (File 18 §1, structured-data-first) and `core.world-model` (File 01 §6.7, screenshot-driven self-perception is fallback) already fix this for perception. This file adopts the same posture for customization (§13): the agent reasons over the semantic-relational customization projection — the shell regions, surfaces, panels, widgets, slots, and their relationships — never over coordinates as the primary interface.

## 1. Chosen Model

Anchor: `customize.chosen-model`

ATLAS3 has one customization layer. It is how the user, the agent, and plugins shape the presentation: the themes that resolve the visual tokens, the saved layouts that arrange the panels, the widgets that compose ambient and actionable units into customizable regions, and the per-profile defaults that seed all of these. It builds entirely over File 37's rendering layer and the one settings substrate, and it realizes the customization the prior files declare and delegate.

The customization layer does four things and only four things:

- it **resolves the visual tokens** through the `DesignTokenSystem` (§4) and the active `Theme` (§5), which override the semantic-token layer File 37 requires every renderer to consume
- it **arranges the container** through `SavedLayout`s (§7) over File 37's layout container, and seeds those arrangements from built-in `ViewPreset`s (File 25) and per-profile defaults (§16)
- it **composes widgets** — the `Widget` primitive (§8) registered in the `WidgetRegistry` (§9), placed into the customizable regions a surface's `customization_policy` permits (§11), data-bound and action-bound through the governed substrate (§10)
- it **mediates customization** through the one customization flow — manual through direct manipulation and AI-assisted through the same capability path (§14), every change reversible, policy-gated, and recorded

The customization layer owns no business logic and no private durable store. A customization is a settings/customization record (`settings.setting-definition`, File 15 §3; `core.versioned-durable-state`, File 01 §6.10) rendered by File 37's container and registries; its loss is a rebuild, never data loss (`core.projection`, File 01 §6.11). Every theme, layout, widget, placement, and configuration is reversible and resettable (`core.non-destructive-by-default`, File 01 §7.13; the charter's removability rule).

This file introduces the net-new customization primitives the prior files referenced without owning: the `DesignTokenSystem` (§4), the `Theme` and `ThemeRegistry` (§5), the `SavedLayout` (§7), and the `Widget` and `WidgetRegistry` (§8, §9). `Theme`, `Widget`, `SavedLayout`, `WidgetRegistry`, `ThemeRegistry`, and `DesignTokenSystem` are new canonical noun-objects.

### 1.1 "Customization," "Widget," "Theme," and "Layout" Are Disambiguated

Anchor: `customize.disambiguation`

This file fixes the customization-layer meanings of the overloaded words and distinguishes them from adjacent concepts:

- a **`Widget`** (this file, §8) — a declared, placeable, configurable, data-bound modular UI unit a user, plugin, or agent composes into a customizable region. It is not a `PanelKind` (`worksurface.state-declaration`, File 25 §5.3 — a surface-declared work-environment region kind), not a `Block` (`block.chosen-model`, File 08 — a durable content-bearing unit), not an `Artifact` (File 09), not a `PresentationView` (`ui.presentation-projection`, File 37 §3 — one rendered projection), and not a `ShellRegion` (`ui.shell`, File 37 §4.2 — a placement region of the shell). A widget *renders through* a `PresentationView` and *may project* a block, artifact, or observation, but it adds placement, configuration, binding, and lifecycle as a customization unit.
- a **`Theme`** (this file, §5) — a named override set over the semantic-token layer, with color-scheme variants. It is not the `RendererRegistry` (File 37 §3.3) and not the semantic-token discipline (File 37 §16.5 — the rule that renderers consume only tokens); it is the system that fills the tokens that discipline requires.
- a **design token** (this file, §4) — a named, themeable visual value (a color, a spacing step, a radius, a shadow, a font, a motion timing) a renderer consumes instead of a raw value. This file owns the token system; File 37 owns the discipline.
- a **`SavedLayout`** (this file, §7) — a user-saved named arrangement of the layout container. It is not the layout container itself (`ui.layout`, File 37 §5 — the recursive split structure) and not a built-in `ViewPreset` (`worksurface.views-presets`, File 25 §7.2 — a surface-shipped startup presentation seed); it is the user's customized, reversible override that the container renders and the settings substrate persists.
- a **`ViewPreset`** (`worksurface.views-presets`, File 25 §7.2) — a surface-declared, named startup presentation seed. File 25 owns the declaration; File 37 renders built-in presets; this file owns user-saved presets and the save/switch/customize flow over them, and treats a preset as a seed the `SavedLayout` may capture and a customization may freely override.
- a **slot** (this file, §11) — a customizable placement target within a shell region or a surface panel, declared by the surface's `customization_policy`, into which a `Widget` or panel may be placed. A slot is the realization of `worksurface.views-presets` (File 25 §7.4)'s abstract customization kinds.
- a **profile** (`settings.profiles`, File 15 §7) — a named local setup that contributes ordered default layers. File 15 owns the profile; this file owns the per-profile UI defaults (§16) it carries and applies.

### 1.2 Boundary

This file defines how the presentation is themed, laid out, and composed with widgets, and how customization is made and reversed. It does not define how the runtime is rendered (File 37), what any surface declares (File 25), how live state is held (File 18), how settings resolve (File 15), how plugins install (File 35), or how customizations are stored or synced (Files 20, 21).

## 2. Boundaries with Adjacent Layers

Anchor: `customize.boundaries`

### 2.1 With File 01 (Core Thesis)

This file realizes `core.invariants` (File 01 §7.9 system-wide customization — "customization spans settings, profiles, layouts, themes, workflows, tools, model behavior, and integrations … the system must not gatekeep valid behavioral variations"), §7.10 extension integrity (customizations are inspectable, reversible, toggleable, and policy-bound; AI-assisted customization uses the same paths as manual), §7.7 service-layer ownership (no business logic in the customization layer), and §7.13 non-destructive-by-default (every customization is reversible). It honors `core.interaction-shapes` (File 01 §2.2) and `core.explicit-rejections` (File 01 §8): no participation level, autonomy mode, or persona is reintroduced as a customization field (§17). It realizes `core.projection` (File 01 §6.11) — every customized view is a projection — and `core.versioned-durable-state` (File 01 §6.10) — a customization is a versioned durable record. `Theme`, `Widget`, `SavedLayout`, `WidgetRegistry`, `ThemeRegistry`, and `DesignTokenSystem` are new canonical noun-objects.

### 2.2 With File 37 (UI Shell, Layout, Presentation, Interaction Models)

This is the primary delegation this file discharges. `ui.layout` (File 37 §5.5) and `ui.consequences-for-later-specs` (File 37 §24) name this file as the owner of user-saved named layouts and the save/switch/customize flow, widgets and widget placement, the design-token system and themes, AI-assisted customization, and plugin UI placement, consuming File 37's `Shell` region model, layout container, `RendererRegistry`, `PanelKind` rendering, built-in `ViewPreset` rendering, interaction models, and semantic-token discipline. This file introduces no parallel shell, layout container, renderer table, or rendering path (§3, §9). Themes fill the tokens `ui.renderer-boundary` (File 37 §16.5) requires every renderer to consume; widgets render through `ui.presentation-projection` (File 37 §3) and the artifact runtime `ui.substrate-rendering` (File 37 §9.3); saved layouts arrange the container `ui.layout` (File 37 §5) renders.

### 2.3 With File 25 (Work Surface Contract)

`worksurface.views-presets` (File 25 §7.4) declares the `customization_policy` — which kinds of customization a surface permits (panel rearrangement, widget placement, custom panel registration, per-panel extension regions), the maximum extension density or safety bound, and whether user, plugin, or AI placement is allowed per kind — and delegates to this file the concrete slot identifiers, region geometry, renderer constraints, widget runtime, and placement algorithms. §11 of this file realizes that policy. `worksurface.views-presets` (File 25 §7.2) owns the `ViewPreset` declaration and §7.6 fixes that this file defines concrete placement and widget mechanics without bypassing the surface contract; `worksurface.consequences-for-later-specs` (File 25 §21) names this file the consumer of `ViewPreset`, `customization_policy`, `PanelKind`, control-affordance semantics, and settings/profile records. `worksurface.persistence-locality` (File 25 §16.1) fixes that user-saved layouts, widget placements, and customization records reference `surface_id`, `surface_contract_version` where needed, `panel_kind`, and policy-owned placement identifiers; §18 of this file conforms.

### 2.4 With File 15 (Settings, Profiles, Scope Resolution)

Every customization is a settings/customization record. A theme selection, a density preference, a saved layout, a widget placement, and a per-widget configuration are `SettingValue`s or settings-owned customization records resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2) and persisted through the settings substrate (`settings.logical-persistence`, File 15 §17); the `ui.theme` and `ui.compactness` built-ins and the `ColorToken`/`KeyboardShortcut` value semantics (`settings.types-semantics-constraints`, File 15 §4.2) already exist there. Per-profile UI defaults are `ProfileLayer` defaults (`settings.profiles`, File 15 §7.3 — activating a profile records layer metadata, never copies values into explicit rows). Each customization setting declares its locality (`settings.locality-sync-export`, File 15 §18) and agent exposure (`settings.agent-exposure`, File 15 §8). This file names the dimensions; File 15 owns the model, cascade, and storage.

### 2.5 With File 18 (World Model) and File 19 (Perception)

The structural-understanding projection (§13) the AI-assisted flow reads is over `world.surface-state` (File 18 §5) — the active surface, open panels, focused element, selection, and `UiMode` File 18 holds — plus this file's customization-facing extension (slot occupancy, placed widgets, the active theme and layout). Placed widgets self-register their live state to the world model on mount, focus, and content change (`world.observation-state-update`, File 18 §8.1), exactly as panels do (`ui.world-state-integration`, File 37 §18); a widget that fails to register is a blind spot the agent cannot use. The projection is read structurally, never screen-scraped (`perception.tiered-sensing`, File 19 §5.4). Widgets that observe the unowned environment render perception's observations, never a private observer.

### 2.6 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces)

The `customize.*` operations (§19) are canonical capabilities in the one registry (`capability.declaration`, File 05 §3), gated per call by `policy.effective-tier-resolution` (File 06 §4) and surfaced through tool-surface composition (File 07). A widget action is a presentation of a `Capability` (`capability.capability`, File 05 §2.1) reached through a control rail (File 26) and gated by policy; a widget invokes no operation out of band. AI-assisted customization passes the same proposal-first source-approval (`policy.source-approval-flow`, File 06 §9) and approval flows (`policy.approval-router`, File 06 §3) as any agent contribution; the customization-preview and confirm dialogs render through the approval/elicitation contract verbatim (`policy.approval-ui-surface-contract`, File 06 §13; `ui.dialog-elicitation-notification`, File 37 §12). Custom widget and theme kinds register through the proposal-first runtime-mutation path (`capability.runtime-mutation`, File 05 §16.2).

### 2.7 With Files 08, 09, 10, 11 (Blocks, Artifacts, Ledger/Events, Version Graph)

A widget that displays substrate content renders a projection of the one block pool (`block.cross-surface-interoperability`, File 08 §12) and the entity layer (`artifact.per-surface-projections`, File 09 §17.2) through File 37's `RendererRegistry`; it introduces no private block pool or content model. Widget custom block, kind, and event registrations use the canonical `Custom` mechanisms (`block.kind-catalogue`, File 08 §3.1; `ledger.custom-kind-registration`, File 10 §4.3). Widgets bind to the event stream event-first (`ledger.event-stream`, File 10 §5; `ui.streaming-presentation`, File 37 §10), never by polling. Customization history, undo, and reset are projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24); a reverted customization is a version-graph or settings sibling, never a private undo store, and the snapshot-before-commit (§14) is a version commit, not a parallel checkpoint.

### 2.8 With File 33 (Automation) and File 34 (Workflows)

A widget that surfaces background or scheduled output reads the automation observability and consumption contract (`automation.observability`, File 33 §17.3 — which names the widgets that surface automation output as ambient interfaces) and the run-now and enable/disable controls; it consumes that data contract and never becomes the firing or run truth (`automation.consequences-for-later-specs`, File 33 §23). A widget action that triggers an automation or a workflow resolves to `automation.run_now` (File 33 §19) or the `workflow.*` invocation surface (`workflow.invocation`, File 34) through the one capability path. The widget renders; File 33 fires and File 34 executes.

### 2.9 With File 35 (Extension and Plugin System)

`plugin.contribution-points` (File 35 §5.2) routes the `Panel`/`Widget`/`View`, `Theme`, and `ViewPreset` contribution kinds to this file's registries, and `plugin.consequences-for-later-specs` (File 35 §18) fixes that this file renders the placement of plugin-contributed panels, widgets, and themes, that the theming and widget contribution kinds register through this file's own registries, and that this file must not make the presentation the install or trust truth. §15 of this file owns the UI customization registries those contributions land in; File 35 owns the plugin bundle, the contribution attribution, trust, and the install/update/uninstall lifecycle. A plugin's widget or theme is treated identically to a built-in of the same kind, distinguished only by source, trust, bundle ownership, and default enablement (`capability.sourcing-equivalence`, File 05 §9.3).

### 2.10 With Files 22, 23 (Security, Sandbox)

Widget data access honors `secret.backend-boundary` (File 22 §4) — a widget references a secret by vault reference, never inline, and a raw secret never reaches the widget renderer or any shareable, cached, exported, or synced customization state — and `security.untrusted-content` (File 22 §12): external, web, connector, or plugin-rendered content carries no authority and is presented as content, never instruction. Widget data egress passes through `security.egress-governance` (File 22 §11). An executable or interactive widget renders inside the one `Sandbox` contract (File 23) at a least-authority origin through the confined interactive-artifact runtime (`ui.substrate-rendering`, File 37 §9.3); this file opens no private sandbox (`sandbox.consequences-for-later-specs`, File 23 §21).

### 2.11 With Files 20, 21, and Packaging (Storage, Sync, Packaging)

Customization records persist as settings/customization records and substrate through the one storage contract (`storage.consequences`, File 20 §18); their locality split (§18) and portability ride File 21 (`portability.what-replicates`, File 21 §5.3; `portability.export-bundle`, File 21 §10). The installer, the auto-updater, platform window-decoration and tray mechanics, sidecar lifecycle, and the bundling of ship-with themes and plugins into the installer image belong to the Packaging, Platform, and Distribution spec (File 43); this file owns the theme, widget, and layout declarations that spec distributes and the first-paint cache contract the renderer consumes.

### 2.12 Boundary

This file is the customization layer. It owns the design-token system, the themes, the saved layouts, the widgets, the realization of the customization policy, the structural-understanding projection, the AI-assisted customization flow, the per-profile UI defaults, and the `customize.*` capability surface. It owns no rendering contract, no work model, no settings model, no live state, no plugin lifecycle, no policy, no sandbox, no storage, and no installer. It customizes the presentation; the owning files realize it.

## 3. The Customization Substrate and the No-Private-Store Invariant

Anchor: `customize.customization-substrate`

### 3.1 Definition

A customization is any user-, plugin-, or agent-made change to the presentation that the customization layer permits: an active theme, a saved layout, a placed widget, a per-widget configuration, a density or font-scale preference, a per-profile UI default. The customization substrate is the rule that every customization is a settings/customization record persisted and resolved through the one settings substrate (File 15) and rendered by File 37's container and registries, with no private durable store of its own.

### 3.2 Rule

- Every customization is a settings/customization record (`settings.setting-definition`, File 15 §3; `settings.logical-persistence`, File 15 §17). The customization layer maintains no private durable store, no parallel persistence, and no source-of-truth state; it renders projections (`core.projection`, File 01 §6.11) and persists changes through the settings substrate and the canonical storage contract (`storage.consequences`, File 20 §18). The single permitted device-local cache — the first-paint theme cache (§6) — is a rebuildable projection of the settings-resolved theme, not a source of truth.
- A customization record references the substrate it customizes by canonical identity, never by duplicating it (`worksurface.persistence-locality`, File 25 §16.1): a `surface_id` and `surface_contract_version` where the customization targets a surface, a `panel_kind`, a `WidgetKind` and source-qualified widget id, a policy-owned slot identifier, a source-qualified theme id, and the scope it applies at. Source-qualified registry identities are structural `{ source_id, local_id }` identities; display names are mutable and need not be unique. A customization that names a missing surface, panel, widget, or theme becomes an unavailable record with a typed diagnostic and a recovery action; it is never silently deleted or rewritten (`worksurface.registry`, File 25 §10.4).
- Every customization record carries `source_ref` and `provenance_refs`. `source_ref` identifies the user, built-in seed, plugin bundle, profile seed, import, or AI proposal that created or last materially changed the record. `provenance_refs` point to the request or observation, source approval, profile bundle, import plan, ledger event, settings revision, or version that explains why it exists. These are references, not duplicated provenance blobs, and feed the source-agnostic "why is this active?" inspector (§17.1).
- Durable customization writes are revision-safe. A write carries the current customization revision or resolved-state hash for the records it changes; if the base is stale, the write fails with a typed conflict and repair path instead of silently overwriting newer user, plugin, import, or agent changes.
- A customization record may carry a `CustomizationDependency` closure: the themes, widgets, plugins, profiles, connectors, capability declarations, renderer registrations, and surface versions required to apply it. Import, sync, layout resolution, and plugin uninstall use this closure to explain unavailable records and repair options.
- Every customization is reversible, removable, and resettable (`core.non-destructive-by-default`, File 01 §7.13; the charter's removability rule): resetting a layout, theme, widget, or preference restores the default or profile-default value, and the prior value survives as a version-graph or settings sibling, never a destructive overwrite. The user is never trapped by a customization, whether made manually or by the agent.
- A customization is policy-resolved and scoped through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2): a customization applies at the `Global`, `Workspace`, or `Conversation` scope, or as a profile-layer default; the customization layer is not a durable settings scope and invents no new scope.
- A customization holds no business logic. The customization layer computes presentation values (placement geometry, token resolution, layout arithmetic) but never the substrate's truth (`ui.renderer-boundary`, File 37 §16.2; `core.invariants`, File 01 §7.7).

### 3.3 Customization Is a Projection

A customized view is a `core.projection` (File 01 §6.11): rebuildable from the customization records plus the substrate, declaring an event-first rebuild trigger (a setting-change event, a layout-switch, a theme-switch, a widget-placement event), never the source of truth for any durable fact, and recoverable by rebuild on loss. The cost of losing the rendered customization state is a rebuild from the records, never data loss.

### 3.4 Boundary

This section fixes the customization-as-record and no-private-store invariant. File 15 owns the settings model, cascade, and persistence; File 20 owns the physical storage; File 11 owns the version graph that records reversibility; File 37 owns the container and registries that render the customization. This file requires every customization to be a record.

## 4. The `DesignTokenSystem`

Anchor: `customize.design-tokens`

### 4.1 Definition

The `DesignTokenSystem` is the layered model of named, themeable visual values that renderers consume in place of raw values. It fills the semantic-token discipline `ui.renderer-boundary` (File 37 §16.5) fixes (a renderer that references a raw color, radius, font, spacing, or motion value rather than a token is invalid) and is the substrate every `Theme` (§5) overrides.

### 4.2 The Three Token Layers

The token system has three layers, resolving outward:

- **Primitive tokens** — raw values with no semantic meaning (a specific color value, a spacing step, a radius, a shadow, a font family, a motion duration). Primitives are the palette; a renderer never references a primitive directly.
- **Semantic tokens** — intent mapped to primitives, and the layer themes override. The canonical semantic-token families are surface (background and elevation surfaces, borders), text (primary, secondary, tertiary, disabled, inverse), interactive (accent and its hover/active/disabled states, success, danger, warning), feedback (error, success, warning, info, and their backgrounds), component radius and shadow, motion (short, normal, long durations and easing classes), typography (body, heading, and monospace families and sizes), spacing, and the surface-density and information-density axes. A renderer consumes only semantic (and, where declared, component) tokens.
- **Component tokens** (optional) — for complex multi-part components, derived from semantic tokens for local roles; they never introduce raw values and always resolve to semantic tokens or primitives.

The semantic-token family set is closed-canonical-plus-`Custom` (`core.closed-canonical`, File 01 §6.16); a surface or plugin that needs a new semantic role registers a `Custom` token through the proposal-first mechanism (§9), declaring its default mapping, and never references a raw value.

### 4.3 The Perceptually-Uniform Color Contract

- Color tokens are defined in a perceptually-uniform cylindrical color space (lightness, chroma, hue, with optional alpha), not in a device-RGB hexadecimal encoding. Perceptual uniformity is the load-bearing property: it lets a theme derive a related token by a relative transform of one axis (a slightly darker surface variant by lowering lightness) without recomputing the whole token set, and it makes contrast validation (§5.4) tractable.
- A hexadecimal or device-RGB value may appear only as a reference annotation or a primitive; the source of truth for a color token is the perceptually-uniform encoding. The concrete color library and CSS encoding are the renderer implementation's; this file fixes the contract that color tokens are perceptually-uniform and relatively derivable.

### 4.4 The Token Discipline

- A renderer — built-in, surface-contributed, or plugin-contributed — consumes only semantic and component tokens, never a raw value (`ui.renderer-boundary`, File 37 §16.5; `worksurface.no-private-architecture`, File 25 §12.3). A widget or theme that references a raw color, radius, font, spacing, or motion value is invalid and is rejected at registration (§9, §5.5).
- A surface or widget that needs a local visual variant layers a scoped token overlay (a per-surface or per-widget token set derived from the semantic layer, §5.6), never a raw value and never a fork of the token system. A scoped overlay resolves to the semantic layer so a theme switch propagates without component changes.
- Adding a token is a declaration: a new semantic or component token registers with its default mapping and is immediately available to renderers and themes, at flat marginal cost (`core.extension-planes`, File 01 §6.14; the self-registration-into-the-token-system invariant). No central file is edited to add a token.

### 4.5 Boundary

This section owns the token model, the color contract, and the discipline's content. File 37 owns the discipline's enforcement at the renderer boundary; §5 owns the themes that override the semantic layer; the renderer implementation owns the concrete color library and utility-class registration. This file fixes the system the discipline consumes.

## 5. The `Theme` and the `ThemeRegistry`

Anchor: `customize.theme`

### 5.1 Definition

A `Theme` is a named, registered override set over the semantic-token layer, carrying one or more color-scheme variants. The active theme resolves the semantic tokens every renderer consumes; switching the theme re-resolves the tokens and re-renders, without any component change. The `ThemeRegistry` is the one registry of available themes.

### 5.2 The `Theme`

A `Theme` carries: a stable source-qualified theme identity, display name, author, license, version, source metadata, and dependency closure; the color-scheme variants it provides (a light variant, a dark variant, or both); and, per variant, a `ThemeTokenSet` mapping the semantic-token names (§4.2) to perceptually-uniform values. A theme overrides the semantic layer only; it never redefines primitives' meaning, never references a raw value in a renderer, and never carries logic, arbitrary CSS selectors, global stylesheets, remote imports, scripts, remote asset URLs, or executable styling authority. A theme changes more than color: it sets radius, shadow, blur, font, spacing, and motion-timing tokens, so a flat theme, a glass theme, and a high-contrast theme differ structurally, not only in palette.

`ColorScheme` is the closed-canonical set `Light`, `Dark`, plus `Auto` (follow the system preference). The active color scheme is resolved from settings; `Auto` resolves to the system light/dark preference event-first and re-resolves when the system preference changes (`ui.settings`, File 37 §22; the no-time-based-polling rule, `core.workspace-model`, File 01 §3 constraint).

`ColorScheme` is not the visual-style extension point. Additional visual variants are themes, accessibility preferences, or scoped token overlays, not new color-scheme enum values.

### 5.3 The `ThemeRegistry`

The `ThemeRegistry` is the one registry that holds the available themes (built-in, plugin-contributed, and user-authored), keyed by source-qualified theme identity `{ source_id, local_id }`, and exposes lookup, enumeration, and the active-theme resolution. There is one `ThemeRegistry`; no surface, widget, or plugin maintains a private theme table. A plugin contributes a theme through the proposal-first source-approval-gated path (`plugin.contribution-points`, File 35 §5.2; `policy.source-approval-flow`, File 06 §9) under the same source taxonomy and trust model as every other contribution (§15). A built-in baseline set of themes ships as worked examples, including at least a default theme, a light and a dark theme, and a high-contrast theme (§5.7); the exact shipped catalogue is distribution's, not canonical here.

### 5.4 Theme Validation

A theme validates before it is registered or selectable through a `ThemeValidationMatrix`: every required semantic token is present in each declared variant; each color value lies in the valid range of the perceptually-uniform space; typography, radius, spacing, motion, transparency, and asset references are declarative and bounded; arbitrary CSS, undeclared assets, remote imports, scripts, and raw renderer values are rejected; and the active accessibility conformance profile's contrast floors hold for normal text, large text, UI components, focus indicators, selection, disabled states, feedback/status states, trust-state tokens, and transparency or blur substitutions (`ui.accessibility`, File 37 §14.2). A nonconforming theme may be saved as a draft or preview with a typed diagnostic, but it is never silently presented as conformant; activation requires the active conformance profile to pass.

### 5.5 Theme Switching and the Default-Theme-Not-Only-Theme Rule

- Theme selection is the `ui.theme` setting resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2; `settings.types-semantics-constraints`, File 15 §4.2's `ColorToken` semantic). Switching the theme is a settings write; the renderer reads it reactively and re-resolves the tokens, re-rendering without remount (`ui.settings`, File 37 §22). Theme switching commits no work-model change and never silently changes model selection, context policy, execution, budget, sandbox profile, approval posture, or instruction-source authority.
- The shipped default theme is a default, not the only theme: the visual language (typography scale, spacing base, radius system, elevation system, motion timings) is token-based and color-independent, so any theme fills the same tokens and every renderer responds to the change. A theme is a complete swap of the semantic layer, not a per-component opt-in.

### 5.6 Per-Surface and Per-Widget Token Overlays

A surface or a widget may layer a scoped token overlay — a named token set derived from the active theme's semantic tokens for local roles (a surface's editor-background derived from the surface-background token, a widget's accent derived from the interactive-accent token) — applied within the surface or widget's scope. An overlay resolves to the semantic layer through the relative-color and derivation rules (§4.3, §4.4), so a theme switch propagates into the overlay without an overlay change. A scoped overlay never introduces a raw value, never escapes its scope, and never forks the theme; it is the canonical mechanism for the per-surface visual identity the per-surface specs may declare.

### 5.7 The High-Contrast and Accessibility Themes

The high-contrast theme is a first-class theme, not an afterthought (`ui.accessibility`, File 37 §14.3): it maximizes contrast, removes transparency, and squares or simplifies radii and shadows where clarity requires, by overriding the semantic tokens — no component change. The reduced-motion and font-scale accessibility preferences (`ui.accessibility`, File 37 §14.2) compose with the active theme through the motion and typography token axes, not through a separate theme. The accessibility conformance is verified against the active theme, including the dark and high-contrast variants (`ui.accessibility`, File 37 §14.2).

### 5.8 Named Visual Focus and Trust-State Token Axes

Beyond color-scheme variants, the token system carries two further token axes a theme and a customization may set without introducing a mode field (`codex_recommendations.md` §10.5 realized):

- **information-density axis** — a token-resolved density level (a compact, a comfortable, and a spacious level, with their padding, font-size, and control-size tokens) selectable as a preference (§16) and per-profile default; it is a token axis, not a mode dial.
- **trust-state tokens** — semantic tokens that visually cue risky actions, low-confidence output, and unverified claims, resolved by the theme so the cue is consistent and themeable. These render the consequences of the policy and provenance layers (Files 06, 09), never a new authority.

A named visual focus (a command-focus, an artifact-focus, a teaching-focus, a review-focus) is a presentation lens realized as which regions, panels, and widgets are open and which density and token overlay apply — a `SavedLayout` plus token state — never a backend autonomy mode (`ui.interaction-models`, File 37 §7; §17).

### 5.9 Boundary

This section owns the theme model, the registry, validation, switching, the overlay layer, and the accessibility and density/trust token axes. File 37 owns the renderer semantic-token discipline and contrast standard; File 15 owns settings persistence; File 35 owns plugin theme contribution. This file owns the theme system.

## 6. Theme Persistence, Switching, and the First-Paint Cache

Anchor: `customize.theme-persistence`

### 6.1 Rule

- The active theme and color scheme are the source-of-truth in the settings substrate (`ui.theme` and the color-scheme setting), resolved through the canonical cascade and synced as user preferences per their declared locality (`settings.locality-sync-export`, File 15 §18). The customization layer persists the theme selection nowhere else; there is no browser-local-storage settings store (`settings.explicit-rejections`, File 15 §20).
- Theme switching is event-first: a setting-change event drives re-resolution and re-render (`ui.settings`, File 37 §22; `settings.events-snapshots`, File 15 §14). `Auto` color-scheme tracking subscribes to the system preference change, never polls.

### 6.2 The First-Paint Cache

The renderer maintains one device-local cache of the resolved theme tokens for the active theme, read synchronously before the main renderer mounts, so the first paint applies the user's theme without a flash of an unthemed or default-themed frame. This cache is the single sanctioned device-local presentation cache and is bounded by these rules:

- it is a **rebuildable projection**, not a source of truth: it holds a copy of the tokens the settings-resolved theme produces, keyed to the active theme identity and version, color scheme, token-system/schema version, relevant renderer/theme-engine version, active accessibility conformance inputs, profile/default layer identity where it affects tokens, source/contribution identity for plugin themes, and locale or font availability where typography tokens depend on them; it is rebuilt whenever any key input changes, and its loss is a re-resolution, never data loss (`core.projection`, File 01 §6.11)
- it fails safe: a cache miss, stale key, failed integrity check, missing source, or validation mismatch causes synchronous token resolution from the settings/customization substrate before first paint, never reuse of an invalid cache entry
- it holds **no source-of-truth state, no preference, no authority, and no secret**: the theme selection is the settings substrate's, and the cache holds only resolved visual tokens for first paint, never layout, widget, plugin code, raw contribution payloads, or policy state
- it is **device-local and never syncs** (`settings.locality-sync-export`, File 15 §18's `DeviceLocal`; `portability.what-replicates`, File 21 §5.3); a new device re-resolves and re-caches on first run
- the concrete synchronous storage mechanism is the renderer implementation's and File 43's; this file fixes that the first-paint cache is a device-local rebuildable projection of the settings-resolved theme

This is the one carve-out from the no-private-store rule (§3.2, `ui.renderer-boundary`, File 37 §16.4), and it is permitted precisely because it is a projection: it owns no fact the substrate does not already own.

### 6.3 Boundary

This section owns the theme-persistence contract and the first-paint-cache exception. File 15 owns the theme setting and its locality; File 43 owns the concrete first-paint mechanism; File 21 owns sync. This file fixes that the theme is a setting and the cache is a projection.

## 7. The `SavedLayout` and Layout Customization

Anchor: `customize.saved-layout`

### 7.1 Definition

A `SavedLayout` is a user-saved, named arrangement of File 37's layout container: which panels and widgets are placed in which regions and slots, their split structure and sizes, their visibility, and the focus shape. It is the user's customized, reversible override over the built-in `ViewPreset`s (File 25) the surface ships and File 37 renders. Layout customization is the save/switch/rename/reset/duplicate/set-default flow over saved layouts.

### 7.2 The Saved-Layout Record

A `SavedLayout` carries: a stable id and display name; the scope it applies at (`Global`, `Workspace`, or `Conversation`, or a profile layer, §18) and the surface or shell context it customizes; the arrangement — the recursive split structure of the layout container (`ui.layout`, File 37 §5.2), the panel and widget placements with their `PanelKind`/`WidgetKind`, source-qualified identities, slot, visibility, and focus shape; its source/provenance references, revision, and `CustomizationDependency` closure; and whether it is a built-in seed or a user-authored override. Layout geometry is stored as logical constraints: topology, flex weights or proportions, semantic minimum constraints, stable anchors, and responsive adaptation rules. Physical divider positions and pixel offsets are renderer hints or derived state, not canonical portable identity. A `SavedLayout` is a settings/customization record (§3); it references panels, widgets, and surfaces by identity and stores no panel content.

### 7.3 The Save/Switch/Customize Flow

- The user arranges the container through File 37's resize/split/dock/collapse/detach mechanism and the widget-placement operations (§12), then saves the current arrangement as a named `SavedLayout` at a chosen scope (capture-current). The user switches between saved layouts and built-in presets, renames, duplicates, resets a layout to its seed or the surface default, and sets a default layout per scope or per profile. Each operation is a `customize.layout.*` capability (§19) and a settings/customization write; none commits a work-model change.
- Applying a `SavedLayout` changes presentation only (`worksurface.views-presets`, File 25 §7.2): it never silently changes model selection, context policy, execution entry, budget, sandbox profile, approval posture, or instruction-source authority. A layout is a presentation arrangement, not an autonomy mode (§17). A saved layout may reference an associated settings/profile bundle, but applying the layout applies those settings only if the user explicitly applies the bundle through the settings path.
- A `SavedLayout` is a seed the user freely overrides: applying it establishes the initial arrangement, after which the user's ongoing changes (open a panel, move a widget, resize a split) are tracked as live `SurfaceState` (File 18) and may be re-captured into a new or updated saved layout. Switching away and back restores the saved arrangement.

### 7.4 Built-in Presets, User Layouts, and the Seed Rule

- A built-in `ViewPreset` (`worksurface.views-presets`, File 25 §7.2) is a surface-shipped startup seed File 37 renders; a `SavedLayout` is the user's customization over the container. The two compose: a user captures a preset as a starting `SavedLayout` and customizes from there, or saves a fresh layout. A preset is a seed, not a contract — every arrangement it makes is reversible (the `ui/15-3-and-15-4` rule realized).
- The shell ships a default layout per surface and a default conversation-first layout (`ui.layout`, File 37 §5.3); the default rendering is complete without any saved layout. On activation, the resolved layout is the user's saved default for the scope and surface if present, else the surface's default preset, else the conversation-first default — the preset-fallback chain.

### 7.5 Skip-Unavailable Recovery and Responsiveness

- A `SavedLayout` that references a missing panel, widget, surface, or surface-contract version (a feature not installed, a plugin disabled, a surface unavailable) is restored with the missing element skipped and a typed unavailability diagnostic and recovery action; it is never silently deleted or rewritten (`worksurface.registry`, File 25 §10.4). If no saved layout can be applied, the shell falls back to the surface default and records a diagnostic (`ui.states`, File 37 §17).
- Applying a `SavedLayout` produces a deterministic `LayoutResolutionReport` carrying the input layout id/revision, target surface or shell context, viewport/adaptation profile, policy version, applied placements, skipped entries, unavailable dependencies, incompatible placements, density-bound rejections, responsive adaptations, fallback used, and repair actions. Resolution never rewrites the source layout silently.
- A `SavedLayout` declares its behavior at a constrained viewport: at a narrow width the layout container stacks and presents one primary panel at a time (`ui.layout`, File 37 §5.4); a saved arrangement has a defined narrow-width adaptation, and a constrained-platform shell is a purpose-built presentation, not a reflowed desktop saved layout. The layout-change responsiveness budget is a tested default and a setting, not a canonical constant.

### 7.6 Boundary

This section owns the saved-layout record and the customization flow. File 37 owns the layout container and its mechanism; File 25 owns the `ViewPreset` declaration and the `PanelKind`; File 18 owns the live `PanelState`; File 15 owns the persistence and scope. This file owns the user-saved layout over the container.

## 8. The `Widget` Primitive and `WidgetKind`

Anchor: `customize.widget`

### 8.1 Definition

A `Widget` is a declared, placeable, configurable, data-bound modular UI unit that a user, plugin, or agent composes into a customizable region. A widget displays live or cached information, summarizes background or runtime state, exposes actions, triggers workflows or commands, navigates into a fuller surface, or reflects scheduled or background processes — an ambient interface to the runtime, not a decorative card (the charter's §6 rule). A widget is the net-new customization primitive this file introduces.

### 8.2 Purpose

The presentation is bounded by what it surfaces and where. Different users and different work benefit from different visible context — a research feed near the research area, a task-and-blockers summary near the conversation rail, a workflow-status or scheduled-output tile, a memory-proposal or reminder unit — and a stable widget layer is how that ambient, actionable context is added without hardcoding it into the shell, editing core source, or one-off plugin hacks (the charter's §2 rule). The widget primitive carries that addition while reusing the substrate underneath, so adding a widget is a declaration and a placement, not a new architecture (`core.local-extensibility`, File 01 §7.8).

### 8.3 The Widget Declaration

A `Widget` is declared by a `WidgetDeclaration` carrying: a stable source-qualified widget identity and `WidgetKind` (§8.4); localized display name, description, and icon key (`capability.display-fields`, File 05 §3.2's localizable-descriptor discipline); the data sources it binds (§10) and the capabilities it exposes as actions (§10); its typed configuration schema and defaults (§12); its renderer (registered in the `WidgetRegistry`, §9); its placement constraints — the slot kinds and region classes it fits, its minimum and default size, and its supported display modes (inline, side, fullscreen, where applicable, mirroring `ui.substrate-rendering`, File 37 §9.3); the structural semantics it exposes (`ui.accessibility`, File 37 §14 — a stable role, accessible label and description, interaction kinds, focus behavior, and state relationships) sufficient for the world model, the rails, and assistive technology; its source and trust state (built-in, plugin-contributed, or user-authored); its `CustomizationDependency` closure; and its default live-versus-cached data behavior (§10). A widget declaration that omits the required fields or cannot be represented structurally is invalid and rejected at registration (§9).

### 8.4 `WidgetKind`

`WidgetKind` is closed-canonical-plus-`Custom`. The canonical baseline is a small set of structural archetypes by data-and-behavior role, not a frozen product catalogue:

- `Information` — displays live or cached read-only data projected from substrate or an external source (a status summary, a feed, a metric)
- `Status` — summarizes the live state of a larger process — a run, an automation, a workflow, a connection, a budget — as an ambient indicator (`automation.observability`, File 33 §17; `run.presentation`, File 04 §25)
- `Action` — exposes one or more capability invocations as controls (run-now, enable/disable, a quick command), gated by policy (§10)
- `Navigation` — resolves to opening or revealing a fuller surface, entity, or view through the navigation target contract (`ui.shell`, File 37 §4.4)
- `Composite` — composes child widgets and substrate projections into a panel-scale unit (a dashboard tile group, an overview area)
- `EmbeddedRuntime` — renders executable or interactive content inside the confined interactive-artifact runtime (§9.3) — a chart, a canvas, an agent- or plugin-authored mini-interface
- `Custom { namespace, name }` — a surface-, plugin-, or user-registered widget kind, registered through the proposal-first mechanism (§9), declaring its data contract, renderer, placement constraints, and structural semantics

The concrete widgets the sources name — a weather unit, a latest-research feed, an active-tasks-and-blockers summary, a memory-proposal review, a workflow-status tile, a scheduled-automation-output tile, a recent-artifacts list, a lesson-progress unit, a project-health summary, a context-budget indicator, a usage-and-rate-limit indicator, a sync-status panel, a whiteboard or node-canvas surface — are built-in or plugin-contributed *instances* of these archetypes registered in the `WidgetRegistry`, not canonical kinds. The baseline archetype set is for cross-cutting reasoning, placement, and policy; it never gatekeeps which concrete widgets may exist (the charter's §13/§14 rule). Adding a canonical archetype is a canonical-spec change; runtime extension uses `Custom`.

### 8.5 Widget Versus Block, Artifact, Panel, and Presentation View

A `Widget` is distinct from the adjacent rendering units (§1.1): a `Block` (File 08) and an `Artifact` (File 09) are durable content units a widget may *project*; a `PanelKind` (File 25 §5.3) is a surface-declared work-environment region a widget may *render within* or *borrow*; a `PresentationView` (File 37 §3) is the rendered projection a widget's renderer *produces*. The inline block renderer that displays a structured result in the transcript (a weather card, a chart) is File 37's `RendererRegistry` rendering a `Block` (`ui.substrate-rendering`, File 37 §9), already canonical and unchanged; the `Widget` is the placed, configured, data-bound customization unit that a user composes into a region and that may itself render such a block. The two are not duplicated: a widget that displays a block kind reuses File 37's renderer for that kind.

### 8.6 Boundary

This section owns the widget primitive, its declaration, and the kind archetypes. File 37 owns the rendering the widget produces; File 25 owns the panel kinds and the customization policy; File 08/09 own the blocks and artifacts a widget projects. §9 owns the registry and rendering dispatch; §10 owns the data and action binding.

## 9. The `WidgetRegistry` and Widget Rendering

Anchor: `customize.widget-registry`

### 9.1 Definition

The `WidgetRegistry` is the one registry that holds the available widget declarations, keyed by source-qualified widget identity `{ source_id, local_id }` and `WidgetKind`, and dispatches a widget to its renderer through File 37's `RendererRegistry`. It is the widget counterpart of the `ThemeRegistry` (§5.3) and the realization of the widget contribution kind `plugin.contribution-points` (File 35 §5.2) routes here.

### 9.2 Rule

- There is one `WidgetRegistry`. No surface, rail, or plugin maintains a private widget table. A widget's renderer registers through the one `RendererRegistry` (`ui.presentation-projection`, File 37 §3.3) — a widget kind dispatches to its render component like any substrate kind, with a safe typed-placeholder for an unknown or unavailable widget kind, never a crash or a blank. A widget is registered code from a built-in or source-approved contribution; the content it renders keeps its own authority class and sensitivity (`ui.presentation-projection`, File 37 §3.3 — renderer trust and content trust are separate).
- Built-in, surface-contributed, plugin-contributed, and user-authored widgets register through the same proposal-first source-approval-gated path (`capability.runtime-mutation`, File 05 §16.2; `policy.source-approval-flow`, File 06 §9) under the one source taxonomy and trust model (§15), and are treated identically thereafter, distinguished only by source, trust, bundle ownership, and default enablement (`capability.sourcing-equivalence`, File 05 §9.3). A widget renderer consumes only the semantic-token layer (§4.4) and receives a presentation context (the active theme, display mode, scope, resolved tokens, and resolved locale) like any renderer (`ui.presentation-projection`, File 37 §3.3).
- A widget declaration validates at registration: the required fields are present (§8.3), the renderer is registered, the declared data and action bindings resolve to governed sources (§10), the structural semantics are sufficient (§8.3), and the declared visual values are tokens, not raw values (§4.4). An invalid declaration is rejected with a typed diagnostic; an optional binding that cannot resolve enters an unavailable state, never a silent substitution.
- A disabled or removed widget's renderer degrades safely: a widget contributed by a disabled plugin renders the typed placeholder and is not invocable, never a crash; a stale widget reference resolves to the placeholder until repaired (`ui.states`, File 37 §17).

### 9.3 The Confined Widget Runtime

An `EmbeddedRuntime` widget (§8.4), and any widget that renders executable or interactive content, runs inside the one interactive-artifact runtime (`ui.substrate-rendering`, File 37 §9.3) at a least-authority origin in the one `Sandbox` contract (File 23), inherits File 23's per-runtime CPU, memory, process, network, filesystem, and cleanup limits, and uses the restricted host bridge: the runtime may read and write its own widget state (with consent, §10.4), emit `Custom { namespace: "widget.runtime", name, payload }` events, and request its own state be persisted, and has no other access — no network, no other files, no block store, no agent, no secrets — unless the user explicitly grants it (File 22, File 23). Widget-runtime events carry widget instance id, source-qualified widget identity, source/plugin identity, and rendered substrate references as envelope cross-references or payload fields; they are sensitivity-defaulted, carry no authority, are never read as instruction, and cannot impersonate system events or trigger security-category hooks (File 10 §8.3; `ui.substrate-rendering`, File 37 §9.3). The runtime-hint registry that selects an executable widget's runtime backend is the settings-backed, extensible registry File 37 §9.3 names; this file introduces no new sandbox or runtime architecture.

### 9.4 Boundary

This section owns the widget registry, the rendering dispatch, and the confined-runtime rule. File 37 owns the `RendererRegistry` and the interactive-artifact runtime; File 23 owns the sandbox; File 06 owns the approval the registration passes; File 35 owns the plugin widget's bundle. This file owns the one widget registry over them.

## 10. Widget Data and Action Sources

Anchor: `customize.widget-data-action-sources`

### 10.1 Definition

A widget's data and action sources are the governed bindings through which it reads state and exposes operations: Atlas-native substrate, workflow and automation output, capabilities and commands, external APIs, user-approved secrets and environment values, and plugin-defined sources (the charter's §7 set). The load-bearing rule is that widget data and action access is governed by the same permission, secret, egress, and extensibility boundaries as the rest of the system; a widget is never a hidden backdoor around the system boundaries (the charter's §7 rule).

### 10.2 Data Sources

A widget binds its data through one of the governed sources, event-first:

- **Atlas-native substrate** — a projection of the one block pool (`block.cross-surface-interoperability`, File 08 §12), the entity layer (`artifact.per-surface-projections`, File 09 §17.2), the world model and live state (`world.exposure-consumption`, File 18 §11), the memory substrate (`memory.consequences-for-later-specs`, File 14 §22), the context budget (`context.consequences-for-later-specs`, File 13 §22), the run presentation (`run.presentation`, File 04 §25), or the version graph (File 11). The widget subscribes to the change events of the facts it reads (`ledger.event-stream`, File 10 §5; `world.state-change-events-reactivity`, File 18 §12) and re-renders event-first; it never polls. A periodic refresh is a flagged, configurable fallback only where a source emits no change events (`ui.presentation-projection`, File 37 §3.2; `core.workspace-model`, File 01 §3 constraint).
- **Workflow and automation output** — the automation observability and consumption contract (`automation.observability`, File 33 §17.3) and the run-history projection; a widget that surfaces scheduled or background output reads that contract and never becomes the firing or run truth (§2.8).
- **External APIs and connectors** — through the one connector layer (`connector.*`, File 36) under egress governance (`security.egress-governance`, File 22 §11); a widget makes no out-of-band network request.
- **Secrets and environment values** — by vault reference only (`secret.backend-boundary`, File 22 §4; `settings.secret-boundary`, File 15 §10's `SecretRef`); a raw secret never reaches the widget renderer, and a widget that needs a credential references it by id, the secret resolved on the backend (`infrastructure/configuration.md` realized).
- **Plugin-defined sources** — registered by a plugin through its owning registry (§15), governed identically to a built-in source.

### 10.3 Action Sources

A widget action is a presentation of a `Capability` (`capability.capability`, File 05 §2.1): the widget declares which capabilities it surfaces as controls, and an invocation resolves through the control rail (File 26) and is gated, per call, by `policy.effective-tier-resolution` (File 06 §4). Action availability displayed by the widget is advisory; invocation re-resolves capability availability, touched resources, invoker context, policy, leases, source trust, and sandbox constraints before dispatch. A stale action returns a typed unavailable or approval-required result, never a silent execution. A widget action that runs an automation resolves to `automation.run_now` (File 33 §19); one that runs a workflow resolves to the `workflow.*` surface (File 34); one that navigates resolves through the navigation target contract (`ui.shell`, File 37 §4.4). A widget invokes no operation out of band and grants no authority of its own; its available actions are the available-capability list the world model computes for its scope (`world.state-aware-capability-availability`, File 18 §9).

### 10.4 Widget Persistent State

A widget that needs durable per-instance state (a display preference, a last-fetched value) persists it as scoped substrate, not a private store: per-widget configuration is a settings/customization record (§12), and per-widget-instance runtime state requiring persistence uses a scoped, consent-gated storage scope (per widget instance, per widget kind, per workspace, or global), the same scoped-artifact-storage discipline the interactive-artifact runtime uses (`ui.substrate-rendering`, File 37 §9.3). Cross-session persistence of an interactive widget's state requires explicit user consent and is stored as substrate, never a private UI store.

### 10.5 Rule

- A widget's data and action access goes through the same capability, policy, secret, egress, and sandbox boundaries as every other consumer; a widget is not a privileged path and not a backdoor (the charter's §7 rule). Every action revalidates at invocation time, even if the widget previously rendered the action as available.
- A widget binds data event-first and never polls except as a flagged fallback; it renders live and cached data distinctly and shows a typed staleness or unavailability state, never a silent stale value (`ui.streaming-presentation`, File 37 §10; `world.observation-state-update`, File 18 §8.5).
- A widget renders `Secret`-classified content masked, never raw, and a raw secret never reaches the renderer or any shareable, cached, exported, or synced state (`secret.backend-boundary`, File 22 §4; `ui.presentation-projection`, File 37 §3.2).
- A widget that renders external, web, connector, model, or tool-returned content treats it as data, never instruction, and carries its authority class and sensitivity (`security.untrusted-content`, File 22 §12; `ui.presentation-projection`, File 37 §3.3).

### 10.6 Boundary

This section owns the widget data/action binding contract. Files 05/06 own the capability and policy; File 33/34 own the automation and workflow; File 36 owns the connector; File 22 owns the secret and egress; File 18 owns the live state and availability; File 08/09 own the substrate the widget projects. This file requires a widget to bind through them.

## 11. The `CustomizationPolicy` Realization

Anchor: `customize.customization-policy`

### 11.1 Definition

The customization-policy realization is the concrete slot and placement model that fills the `customization_policy` `worksurface.views-presets` (File 25 §7.4) declares. File 25 declares which kinds of customization a surface permits, the maximum extension density or safety bound, and whether user, plugin, or AI placement is allowed per kind; this file owns where and how those customizations render — the slot vocabulary, the placement-compatibility contract, the per-surface customization-freedom variation, and the bound enforcement.

### 11.2 The Slot Model

- A slot is a declared, customizable placement target within a `ShellRegion` (`ui.shell`, File 37 §4.2) or a surface panel: the canonical slot classes are the customizable shell regions (the inspector dock, the artifact navigator, the conversation-adjacent rail, the status and notification regions, and a dashboard or overview region), the customizable areas of a surface's declared panels, and the per-panel extension regions the surface permits. Each slot declares the widget and panel kinds it accepts, its size and density bounds, and the placement sources it allows (user, plugin, AI). A slot is a policy-owned placement identifier (`worksurface.persistence-locality`, File 25 §16.1), referenced by saved layouts and widget placements.
- Placement is compatibility-checked: a widget or panel may be placed in a slot only if the slot accepts its kind, the placement is within the slot's density and safety bound, and the placement source is permitted by the surface's `customization_policy` for that kind. An incompatible placement is rejected with a typed diagnostic; the customization layer never forces an incompatible placement.

### 11.3 Per-Surface Customization-Freedom Variation

Customization freedom varies by surface (the charter's §4.2/§13 rule): a surface's `customization_policy` may permit little or no customization, moderate customization, or heavy customization, and may permit different kinds at different slots. The customization layer enforces the declared policy uniformly: a surface that declares no widget-placement slots hosts no widgets; a surface that declares a heavy dashboard region permits broad placement within its bounds. The default presentation is clean and complete without any customization (`core.product-thesis`, File 01 §1; `ui.interaction-models`, File 37 §7.3's progressive-disclosure rule); customization adds depth where the surface permits it.

### 11.4 Who May Place and the Bounds

- The `customization_policy` declares, per customization kind and per slot, whether the user, a plugin, or the agent may place; this file enforces it (§14, §15). A plugin's default placement is a proposal resolved through settings and the policy, never a forced placement (§15). The agent places only through the AI-assisted flow (§14), policy-gated and reversible.
- The maximum extension density or safety bound a surface declares is enforced at placement: a slot's widget count, the total customization density, any per-kind safety bound, and the aggregate concurrent active-widget-runtime budget are caps the placement check respects, surfaced when reached, never silently exceeded (the no-silent-cap discipline, `perception.consequences-for-later-specs`, File 19). Active visible or running `EmbeddedRuntime` widgets consume the aggregate runtime budget; off-screen frozen widgets do not unless they keep background work alive under an explicit policy. Bounds are settings, not hardcoded limits (`settings.settings-over-constants`, File 15 §13).

### 11.5 Boundary

This section owns the slot and placement realization. File 25 owns the `customization_policy` declaration and the per-surface variation it permits; File 37 owns the regions and the container the slots sit in; File 18 owns the live placement state. This file realizes the policy as slots and placement.

## 12. Widget Placement, Configuration, and Per-Instance State

Anchor: `customize.widget-placement`

### 12.1 Definition

A widget placement is a `WidgetInstance` — a placed, configured occurrence of a widget kind in a slot. Placement, per-instance configuration, multi-instance behavior, and the instance lifecycle are this section's.

### 12.2 The Widget Instance

A `WidgetInstance` carries: a stable instance id, the source-qualified widget id and `WidgetKind`, the slot and scope it is placed at, its size and visibility (`PanelState`, `world.surface-state` File 18 §5.3), its typed per-instance configuration (validated against the widget's configuration schema, §8.3), its data-source binding instance (§10), revision, `source_ref`, `provenance_refs`, and dependency references. A `WidgetInstance` is a settings/customization record (§3) referenced by the `SavedLayout` it belongs to; multiple instances of the same widget kind may be placed independently, each with its own configuration, data binding, and refresh state (the multiple-terminal-sessions analog). A widget instance self-registers its live state to the world model on mount, focus, and content change (`world.observation-state-update`, File 18 §8.1; §2.5).

### 12.3 Configuration

Per-instance configuration is a settings/customization record resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); a widget declares its configuration schema with typed defaults and declarative constraints (`settings.types-semantics-constraints`, File 15 §4) — the data source it binds, its display options, its density, its refresh behavior — and the customization UI renders configuration from that metadata (`settings.consequences-for-later-specs`, File 15 §21). Configuration follows progressive disclosure: essential options by default, advanced configuration revealed on demand (`ux-input/design-principles.md` realized). A widget's configuration is overridable per instance and may carry a per-instance token overlay (§5.6) and accent.

### 12.4 Lifecycle

- A widget is added (placed into a slot, compatibility-checked, §11.2), moved (re-placed into another compatible slot), configured (its per-instance settings changed), enabled or disabled (hidden without losing configuration and refresh state — the close-hides-not-kills rule), and removed (unplaced, its configuration preserved as an orphaned customization record reclaimable on re-placement, never destroyed, `settings.setting-definition` File 15 §3.4). Every operation is a `customize.widget.*` capability (§19) and a settings/customization write, reversible and resettable (§3.2).
- A disabled or off-screen widget suspends its expensive render and data-refresh loops while preserving its durable subscription and configuration (`ui.streaming-presentation`, File 37 §10.2's off-screen-freeze rule; the persisted-versus-ephemeral discrimination); re-showing it re-syncs against the substrate without a gap. A widget instance whose underlying widget kind, data source, or capability becomes unavailable renders the typed placeholder and is not invocable, never a crash (§9.2).

### 12.5 Boundary

This section owns the widget instance, its configuration, and its lifecycle. §11 owns the slot the instance is placed in; §10 owns the data binding; File 15 owns the configuration persistence; File 18 owns the live instance state. This file owns the placed widget over them.

## 13. Structural UI Understanding

Anchor: `customize.structural-understanding`

### 13.1 Definition

Structural UI understanding is the semantic-relational projection of the customizable interface the agent reads to reason about and customize the presentation: what surface is active, what regions are visible, what panels and widgets are open, what is nested inside what, what is beside, above, below, or inside what, what is focused and selected, what is collapsed, pinned, floating, hidden, or expanded, what is primary versus secondary, what slot occupancy exists, and what customization actions are available. It is the realization of the charter's §5 requirement that the agent understand the interface structurally rather than from screenshots or raw coordinates.

### 13.2 Rule

- The structural projection is over `world.surface-state` (File 18 §5) — the active surface, open panels, primary panel, focused element, selection, available capabilities, and `UiMode` File 18 holds and the presentation layer self-registers (`ui.world-state-integration`, File 37 §18) — plus this file's customization-facing extension: the active theme and color scheme, the active layout, the slot model and its occupancy, the placed widget instances and their kinds and configurations, and the available customization actions. The projection is policy-filtered for the consumer: it includes ids, roles, relationships, safe summaries, and redacts or omits fields according to File 15 agent exposure, File 06 policy, File 10 sensitivity, and File 22 secret rules. External, tool, connector, model, or plugin-rendered data keeps its authority class and source attribution. The agent reads this structured projection; it never screen-scrapes the rendered UI (`world.chosen-model`, File 18 §1; `perception.tiered-sensing`, File 19 §5.4).
- The projection is semantic and relational, not coordinate-based: it describes regions, panels, widgets, and slots and their containment, adjacency, focus, selection, and visibility relationships, and their primary-versus-secondary roles. Coordinates may exist as secondary metadata, but they are never the primary interface for reasoning (the charter's §5.2/§5.3 rule). A panel, widget, or control that cannot be represented structurally — that exposes no role, label, interaction kind, and state relationship sufficient for this projection, the world model, the rails, and assistive technology — is invalid (`worksurface.explicit-rejections`, File 25 §20; `ui.accessibility`, File 37 §14; §8.3). This is the same dual-purpose structural layer accessibility consumes (`codex_recommendations.md` §10.6 realized).
- The projection is bounded and event-first: it is compact (identifiers, roles, relationships, and short summaries, not resource bodies, `world.surface-state` File 18 §5.2), refreshed event-first on the world-model and customization change events, and fits comfortably in a model request. It is the substrate the AI-assisted customization flow (§14) reads to inspect the current configuration and the explainable context the customization UI renders.

### 13.3 Boundary

This section owns the structural-understanding projection's content and contract. File 18 owns the live state and the self-registration the projection reads; File 37 owns the self-registration the panels feed; §14 owns the flow that consumes the projection. This file fixes that customization reasons over structure, never coordinates.

## 14. AI-Assisted Customization

Anchor: `customize.ai-assisted`

### 14.1 Definition

AI-assisted customization is the agent's participation in shaping the presentation — suggesting widgets, rearranging layouts, simplifying crowded views, creating workflow-oriented or per-use-case views, and personalizing startup layouts — in response to a natural-language request or its own observation, through the same customization layer the user uses. It is the realization of the charter's §10 requirement and the `worksurface.views-presets` (File 25 §7.4) capability-flow rule.

### 14.2 The One-Path Rule

AI-assisted customization uses the same paths as manual customization (`core.extension-integrity`, File 01 §7.10). There is no agent-only customization API, no agent-only customization store, and no separate AI-customization pathway. The agent reads the structural projection (§13) and proposes through the same `customize.*` capabilities the user invokes (§19); a natural-language customization request ("make this screen simpler," "show weather and my tasks here," "put my paper feed near the research area," "make a dashboard for my morning workflow") resolves through the control rails (`controlrail.input-resolution`, File 26 §4) into those capabilities. The agent customizes only what the surface's `customization_policy` permits for the AI source (§11.4).

### 14.3 The Customization Flow

An AI-assisted customization is a capability flow (`worksurface.views-presets`, File 25 §7.4):

1. **inspect** — the agent reads the policy-filtered structural projection (§13) and the current customization records through a `ReadOnly`, agent-invocable inspect capability (§19); it reasons over the structure, never coordinates
2. **propose** — the agent produces a typed customization proposal: a diff over the layout, widget placements, theme, or configuration, carrying the base customization revision or resolved-state hash and a `CustomizationPreview` the user can see before it applies. The proposal is data, not an applied change; generating a proposal (including an AI-generated layout or dashboard) is never a silent apply
3. **gate** — the proposal passes policy (`policy.effective-tier-resolution`, File 06 §4) and, for an agent-initiated contribution, the proposal-first source-approval flow (`policy.source-approval-flow`, File 06 §9); the customization-preview and confirm dialog render through the approval/elicitation contract verbatim (`policy.approval-ui-surface-contract`, File 06 §13; `ui.dialog-elicitation-notification`, File 37 §12), never a parallel approval shape
4. **commit** — on approval, the change revalidates its base revision or resolved-state hash, applies as a reversible customization record, and takes a snapshot of the prior state before the commit (§3.2, §17.3), so it can be reverted in one operation; a stale base returns a typed conflict and repair path, not an overwrite; the commit is a settings/customization write and, where it touches versioned state, a version-graph sibling (File 11)
5. **record provenance** — the change records `source_ref` and `provenance_refs` (the request or observation that prompted it, the proposal, and the actor) so the user can see why a customization was made and revert it (`core.evidence-provenance`, File 01 §7.12; the "why is this active?" explainer, §17.1)

Direct mutation of core UI code, a surface manifest, or runtime state outside this flow is invalid (`worksurface.views-presets`, File 25 §7.4; the charter's §11.1 rule).

### 14.4 Reversibility and the No-Trap Rule

Every AI-made customization is reversible and removable; the user is never trapped by an AI-made UI change (the charter's §4.4 rule). A reset restores the prior or default state, and the snapshot-before-commit (§14.3 step 4) makes the revert exact. The bounds on agent self-customization — a maximum number of active agent-made customizations, the default approval posture for agent-initiated customization — are settings, not hardcoded limits (`settings.settings-over-constants`, File 15 §13).

### 14.5 Boundary

This section owns the AI-assisted customization flow. §13 owns the projection it inspects; §19 owns the capabilities it proposes through; File 06 owns the policy and approval it passes; File 11 owns the snapshot it commits against; File 26 owns the rail it resolves through. This file fixes that AI customization is the one customization path.

## 15. Plugin UI Placement

Anchor: `customize.plugin-ui`

### 15.1 Definition

Plugin UI placement is the contribution of widgets, themes, view presets, and panels by a plugin into the customization layer's registries, and the placement of those contributions into the customizable regions the surfaces permit. It realizes the `Panel`/`Widget`/`View`, `Theme`, and `ViewPreset` contribution kinds `plugin.contribution-points` (File 35 §5.2) routes here.

### 15.2 Rule

- A plugin contributes a widget, a theme, a view preset, or a panel through this file's registries (the `WidgetRegistry` §9, the `ThemeRegistry` §5.3, the preset library `worksurface.views-presets` File 25 §7, and the `RendererRegistry` for the contribution's renderer, File 37 §3.3), through the one proposal-first source-approval-gated path (`plugin.lifecycle`, File 35 §10; `policy.source-approval-flow`, File 06 §9) under the plugin source and trust (`plugin.trust-integrity-approval`, File 35 §7). The contribution registers like a built-in of the same kind and is treated identically thereafter, distinguished only by source, trust, bundle ownership, source-qualified identity, and default enablement (`capability.sourcing-equivalence`, File 05 §9.3; `plugin.registry`, File 35 §9).
- On plugin update, customization-layer validators re-run. A contributed theme re-runs the `ThemeValidationMatrix`, so an update cannot silently regress contrast below the active accessibility conformance profile. A contributed widget update that adds a data source, surfaced action, egress path, sensor dependency, runtime authority, or resource envelope is an effect-envelope expansion that parks pending source review; the previous valid contribution remains active where possible until the user or policy accepts the expansion.
- A plugin's declared default placement (a default slot for a contributed panel or widget, a default theme for a profile) is a placement proposal resolved through settings, the surface's `customization_policy`, and the slot-compatibility check (§11.2), never a forced placement and never by plugin load order (`plugin.contribution-points`, File 35 §5.3). Source and bundle attribution remain visible (`plugin.registry`, File 35 §9.3).
- A plugin's executable widget renderer runs confined through the existing backend descriptors and the one `Sandbox` (`plugin.code-backends`, File 35 §8; §9.3), at least authority; it overrides no security-critical state and opens no new sandbox. A plugin's widget data and action access is governed identically to a built-in widget's (§10); plugin source approval, trust, or install never grants a widget camera, audio, screen, or other sensor consent, which remains modality-specific and owning-policy-governed (`plugin.contribution-points`, File 35 §5.2).
- Plugin UI placement is never arbitrary core-UI mutation (`worksurface.explicit-rejections`, File 25 §20; the charter's §11.1 rule): a plugin contributes through the registries and the customization policy, never by editing core UI code, the shell, or runtime state outside the customization flow. Disabling or uninstalling a plugin unregisters its widgets, themes, and presets and renders placed instances as the typed placeholder with a recovery action; produced customization records orphan non-destructively (`plugin.lifecycle`, File 35 §10.4).

### 15.3 The Ship-With Plugin UI

A ship-with per-profile plugin (`plugin.distribution`, File 35 §11.4) may carry the per-profile UI bundle — the contributed panels and widgets, the default theme and density, and the default view preset for its profile — delivered as profile-layer defaults the user accepts at onboarding (§16) and freely overrides. The plugin is treated like any other; the registry distinguishes it only by its built-in-bundled source and the application's installation trust.

### 15.4 Boundary

This section owns the placement of plugin UI contributions into the customization layer. File 35 owns the plugin bundle, the contribution attribution, trust, and the install lifecycle; this file's registries own the contributions; File 25's `customization_policy` and §11's slots gate the placement; File 23 owns the sandbox the plugin renderer runs in. This file places the plugin's UI through the one customization layer.

## 16. Per-Profile UI Defaults

Anchor: `customize.per-profile-defaults`

### 16.1 Definition

Per-profile UI defaults are the presentation defaults a profile carries — the default theme and color scheme, the information density and font scale, the default layout and startup layout, and the default widget set — applied as profile-layer defaults the user freely overrides. They realize the per-profile customization the charter and the sources describe, over File 15 profiles.

### 16.2 Rule

- A profile (`settings.profiles`, File 15 §7) contributes its UI defaults as a profile layer: activating the profile records the layer metadata and resolves the defaults through the canonical cascade, never copying values into explicit user rows (`settings.profiles`, File 15 §7.3; `plugin.distribution`, File 35 §11.4). The per-profile UI defaults include at least the default theme per color scheme, the information-density level (§5.8) and font scale, the default and startup `SavedLayout` or `ViewPreset` per surface, and the default widget set per customizable region. A profile's defaults are seeds, not contracts (`worksurface.views-presets`, File 25 §7.2): the user overrides any of them, and a later profile-bundle update re-seeds only the profile layer, never an explicit user row (`plugin.distribution`, File 35 §11.4).
- Onboarding applies a profile's UI defaults as a presentation flow over substrate operations (`ui.states`, File 37 §17.1): selecting a profile activates the profile, applies its theme, density, layout, and widget defaults as profile-layer defaults, and sets its default startup layout; skipping selects a clean, minimal default profile. Each onboarding step is a capability invocation; the flow owns no durable state of its own.
- A per-profile UI default is a presentation default only. It selects which theme, density, layout, and widgets open — the consequences the deleted participation, autonomy, and persona fields once described (§17) — and it carries no participation level, autonomy mode, or persona as a backend or customization field. Any "personality" or instruction style a profile bundles is a Memory or instruction preset governed by File 14 and File 13's authority-class rules — a starting template the user edits, applied through the memory and instruction-source paths, never a customization-layer mode, dial, autonomy control, or coupling to surface or model identity (`core.interaction-shapes`, File 01 §2.2; `ui.interaction-models`, File 37 §7.3; `worksurface.no-autonomy-field`, File 25 §13; `memory.consequences-for-later-specs`, File 14 §22).

### 16.3 Boundary

This section owns the per-profile UI defaults and their application. File 15 owns the profile and the layer model; File 35 owns the profile-bundle delivery; File 14 owns the memory/instruction preset a profile may carry; §17 owns the deleted-field consequence. This file owns the presentation defaults a profile carries.

## 17. Customization Safety, Reversibility, and the Deleted-Field Consequence

Anchor: `customize.safety-reversibility`

### 17.1 Reversibility

Every customization — a theme, a layout, a widget placement, a configuration, a per-profile default, an AI-made change — is removable, reversible, and resettable (`core.non-destructive-by-default`, File 01 §7.13; the charter's §4.4 rule). A reset restores the default or profile-default; the prior value survives as a version-graph or settings sibling (§3.2); and the user is never trapped, whether the change was made manually or by the agent (§14.4). There is no destructive customization without explicit confirmation, and no AI customization that cannot be reverted in one operation. The "why is this active?" inspector is a uniform projection over every customization source — user, built-in seed, plugin default, profile seed, import, and AI proposal — rendered through File 37's inspector before revert or repair.

### 17.2 Policy and Source Gating

A customization is gated by the surface's `customization_policy` (§11.4) and, where it touches policy-relevant state or comes from a plugin or the agent, by `policy.effective-tier-resolution` (File 06 §4) and the source-approval flow (`policy.source-approval-flow`, File 06 §9). A plugin or AI customization that exceeds its permitted kind, slot, source, or density bound is rejected with a typed diagnostic, never silently applied. A customization never pierces a `permission_floor` (`policy.permission-floor`, File 06 §7) and never grants authority a capability could not declare.

### 17.3 Snapshot Before Commit

A customization commit takes a snapshot of the prior customization state before applying, so the change is exactly revertible (§14.3). The snapshot is a version-graph or settings sibling (File 11; `settings.logical-persistence`, File 15 §17), not a parallel undo store; reverting a customization is the same operation as switching to any prior customization state. Commits are revision-safe: compare-and-commit uses the base revision or resolved-state hash and fails with a typed conflict if the target changed between preview and apply.

### 17.4 The Deleted-Field Consequence

The customization layer carries no participation-level, autonomy-mode, persona, agent-mode, plan-versus-build-mode, or phase field, in any form, at any layer. This is the unanimous, most-evolved canonical position (`core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `world.surface-state`, File 18 §5.5; `worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17; `settings.explicit-rejections`, File 15 §20; `ui.interaction-models`, File 37 §7). The customization layer renders the *consequences* the deleted fields once described:

- a **per-profile or per-use-case "mode"** is rendered as which theme, density, layout, widgets, and view preset are active — a `SavedLayout` plus token and per-profile-default state — never a backend mode field (§16, §5.8)
- a **"personality" preset** is rendered as a Memory or instruction preset governed by File 14 — a starting template the user edits — never a customization-layer autonomy field (§16.2)
- **autonomy** is rendered as the approval posture the policy layer resolves (`policy.effective-tier-resolution`, File 06 §4) and the pending approvals it raises — surfaced as the consequence of policy, never as a customization dial (`ui.interaction-models`, File 37 §7.3)
- **progressive disclosure** is rendered as which regions, panels, and widgets are open and which density applies — reachable by customizing more, never a mode (`core.product-thesis`, File 01 §1; `ui.interaction-models`, File 37 §7.3)

There is no participation-level, autonomy-mode, or persona customization event because there is no such field to change (§20).

### 17.5 Boundary

This section owns the safety, reversibility, and deleted-field rules. File 06 owns the policy and floor; File 11 owns the snapshot; File 14 owns the memory/instruction preset; Files 01/25/26/37 fix the deletion at their layers. This file fixes that customization is reversible and carries no autonomy field.

## 18. Persistence, Locality, and Portability

Anchor: `customize.persistence-locality`

### 18.1 What Is Durable, Device-Local, and Portable

- **Durable and (where its owner syncs) syncable** — the customization records: saved layouts, widget placements and configurations, the active theme and color-scheme selection, the information-density and font-scale preferences, per-profile UI defaults, and user-authored and plugin-contributed themes and widgets. They carry source/provenance references, revisions, and dependency closures; persist as settings/customization records and substrate (`settings.logical-persistence`, File 15 §17; `storage.consequences`, File 20 §18); and follow their declared locality (`settings.locality-sync-export`, File 15 §18): saved layouts, theme selection, density, and per-profile defaults are `Syncable` user preferences so a user's customization follows them across devices (`portability.what-replicates`, File 21 §5.3).
- **Device-local and rebuilt** — the first-paint theme cache (§6.2), device-bound window placement (`ui.shell`, File 37 §4.5; `settings.locality-sync-export`, File 15 §18's `DeviceLocal`), physical layout measurements, and device-bound widget runtime state. These are device-local projections rebuilt per device; their loss is a rebuild, never a loss of a customization record.
- **Portable** — saved layouts, themes, widget configurations, and view presets export and import over the `PortablePackage` (`portability.export-bundle`, File 21 §10); portable layout identity uses logical constraints and dependency closures, not device-local geometry. A plugin-sourced theme or widget re-resolves and re-approves locally on import (imported trust is inert, `security.trust-model`, File 22 §9.7; `plugin.distribution`, File 35 §11.5), and an unresolved reference imports as an unavailable record with a typed diagnostic, never a silent substitution.

### 18.2 Security and Hashing

A customization record, export, or sync stream contains no raw secret: a widget's credential is a vault reference (`secret.backend-boundary`, File 22 §4; `settings.secret-boundary`, File 15 §10), never inline; raw secrets never sync, export, or materialize (`portability.sensitivity-egress`, File 21 §12). A customization record honors the sensitivity classification of what it renders in screenshots and exports (`ledger.sensitivity-aware-persistence-retention`, File 10 §10). Every hash a customization record relies on is computed over a declared `CanonicalEncoding`, never physical storage bytes (`core.canonical-hash`, File 01 §7.14); this file defines no new canonical hash and inherits each from its owning file.

### 18.3 Boundary

This section owns the durable-versus-device-local-versus-portable split for customizations. File 15 owns the settings persistence and locality; File 20 owns storage; File 21 owns sync and the portable bundle; File 22 owns the secret boundary and the import re-approval. This file classifies the customization records.

## 19. The `customize.*` Capability Surface

Anchor: `customize.capability-surface`

### 19.1 Closed Canonical Capabilities

The customization layer exposes its operations as built-in capabilities declared per `capability.declaration` (File 05 §3), flowing through the standard call pipeline (`run.call-pipeline`, File 04 §8.2) and policy (File 06). These compose with, and do not duplicate, the presentation capabilities File 37 declares (`ui.capability-surface`, File 37 §20, which routes layout, view-preset, density, and theme-reference writes here). The canonical families:

- **theme** — `customize.theme.list` / `customize.theme.get` / `customize.theme.preview` (`ReadOnly`, `ConcurrencySafe`); `customize.theme.set(theme_id, color_scheme, scope, base_revision)` (a settings/customization write); `customize.theme.install(source)` / `customize.theme.author(definition)` (user-only, source-approval-gated, composed with File 35)
- **layout** — `customize.layout.list` / `customize.layout.get` (`ReadOnly`); `customize.layout.preview(operation_or_diff)` (`ReadOnly`); `customize.layout.save` / `customize.layout.switch` / `customize.layout.rename` / `customize.layout.reset` / `customize.layout.duplicate` / `customize.layout.set_default` (settings/customization writes carrying a base revision or resolved-state hash)
- **widget** — `customize.widget.list_kinds` / `customize.widget.get` / `customize.widget.list_instances` (`ReadOnly`); `customize.widget.preview(operation_or_diff)` (`ReadOnly`); `customize.widget.add` / `customize.widget.move` / `customize.widget.configure` / `customize.widget.enable` / `customize.widget.disable` / `customize.widget.remove` (settings/customization writes carrying a base revision or resolved-state hash and slot-compatibility-checked); `customize.widget.register` (a custom widget kind, source-approval-gated, composed with File 35)
- **density and preference** — `customize.preference.set(key, value, scope)` for the density, font-scale, and other presentation preferences this file names (composed with File 15, not duplicated)
- **AI-assisted flow** — `customize.inspect` (the policy-filtered structural projection and current customization records, `ReadOnly`, agent-invocable, §13); `customize.propose(diff, base_revision_or_hash)` (produce a typed customization proposal with a preview, `ReadOnly`, agent-invocable, never applies, §14); `customize.apply(proposal_id, base_revision_or_hash)` (commit an approved proposal after revision revalidation, policy-gated, snapshot-before-commit); `customize.revert(customization_ref)` (revert to a prior customization state)
- **profile defaults** — `customize.profile_defaults.get` / `customize.profile_defaults.apply` (apply a profile's UI defaults as profile-layer defaults at onboarding or on profile switch, composed with File 15 and File 35)

### 19.2 Rule

- The customization capabilities are built-in declarations under the one registry, carrying the touched-resource and tier metadata their effects warrant (the `setting` and presentation resource classes, `capability.touched-resources` File 05 §6; `settings.settings-capabilities` File 15 §16). Reads are `ReadOnly`; layout, widget, theme-selection, and preference writes are settings/customization writes with the effective tier resolved from touched resources and policy; theme/widget install or registration is user-only and source-approval-gated; `customize.inspect` and `customize.propose` are `ReadOnly` and agent-invocable but never apply; `customize.apply` is gated and snapshot-backed. Every nontrivial durable customization write has a preview/proposal form; direct drag and resize gestures may render transiently, but committing them still writes through the revision-safe capability path.
- Every customization capability is the single source for all its invocation paths — command palette, shortcut, voice, menu, agent tool, automation trigger, external protocol (`core.extension-planes`, File 01 §6.14); the customization layer declares no out-of-band customization operation. The agent invokes these capabilities the same way the user does — through the one capability system under policy — so AI-assisted customization and manual customization are one path (§14). Custom customization operations register through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2) and never bypass policy.

### 19.3 Boundary

This section names the customization capability families and effect classes. File 05 owns the capability contract; File 06 owns tier resolution and approval; File 07 owns surfacing; File 04 owns execution; File 15 owns the settings the writes compose with; File 35 owns the plugin install the theme/widget install triggers. This file declares the customization capabilities as built-ins.

## 20. Events

Anchor: `customize.events`

### 20.1 Rule

- The customization layer emits its consequential customization facts as `Custom { namespace: "customize", name, payload }` events (`ledger.custom-kind-registration`, File 10 §4.3) through the one event bus and ledger with the canonical envelope (`ledger.event-envelope`, File 10 §5.2): a theme changed or installed, a saved layout saved, switched, renamed, reset, duplicated, or set as default, a widget added, moved, configured, enabled, disabled, or removed, a customization proposed, applied, or reverted, and per-profile UI defaults applied. Each declares its payload schema, cross-reference keys, default sensitivity, retention, and owner per File 10. Widget runtime events are `Custom { namespace: "widget.runtime", name, payload }`, carry no authority, and are distinct from customization facts. Live surface-state changes (panel and widget registration, focus, selection, mode) are owned by `world.state-change-events-reactivity` (File 18 §12) and emitted by the world model from the presentation layer's self-registration; this file consumes them and does not duplicate them. Presentation facts the shell owns (region opened, view preset applied) are File 37's `ui` events; this file emits only its own customization facts.
- A customization event is live coordination; a consequential customization fact (a layout saved, a theme installed) is committed to the durable record by the settings or registry path, never inferred from event observation (`core.durable-history-transient-coordination`, File 01 §7.3). High-frequency transient customization activity (a drag in progress, a resize in flight) is transient by default and not durable unless an explicit save commits it. There is no participation-level, autonomy-mode, or persona event because there is no such field (§17.4). Security-relevant customization facts — a theme or widget installed from an untrusted plugin, a customization that touches policy-relevant state — carry the source and trust attribution File 35 fixes and default to the appropriate sensitivity.

### 20.2 Boundary

This section reserves the `customize` event namespace and declares customization-fact events only. File 10 owns the envelope, delivery, sensitivity, and custom registration; Files 18 and 37 own the live-state and presentation events this file consumes; File 35 owns the contribution events. This file emits through the shared bus.

## 21. Settings

Anchor: `customize.settings`

### 21.1 Rule

- Customization behavior is configurable through the one settings system (`core.settings-system`, File 01 §6.8; File 15); this file names the dimensions, the settings system owns the cascade and storage. Customization settings are namespaced keys resolved through the standard cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); the customization layer is not a durable settings scope, and per-customization variation is namespaced keys plus profile layers, never a new scope.
- The canonical customization settings dimensions include at least: the active theme and color scheme (composed with File 37's theme-reference dimension), the information-density level and font scale, the reduced-motion and high-contrast preferences (composed with File 37's accessibility dimensions); the default and startup `SavedLayout` or `ViewPreset` per surface and per scope, and whether saved layouts apply; the per-customizable-region default widget set and per-widget-instance configurations; the per-surface customization-freedom and bound overrides the `customization_policy` permits (composed with File 25), including the aggregate active-widget-runtime budget; the AI-assisted-customization enablement and bounds (whether the agent may inspect and propose customizations, the maximum active agent-made customizations, the default approval posture for agent-initiated customization); the plugin-UI-placement and theme/widget-install policy (composed with File 35); the first-paint-cache and theme-switch behavior; and the per-profile UI default bundles (composed with File 15 profiles and File 35 bundles).
- Each customization setting declares its locality (`settings.locality-sync-export`, File 15 §18) — saved layouts, theme selection, density, and per-profile defaults are syncable user preferences; window placement and the first-paint cache are device-local — and its agent exposure (`policy.agent-exposure-policy-settings`, File 06 §16.4; `settings.agent-exposure`, File 15 §8), so the agent cannot read or change security-sensitive customization configuration without policy. No customization behavior with meaningful variation is a hardcoded constant (`core.typed-configuration-failure`, File 01 §7.6; `settings.settings-over-constants`, File 15 §13).

### 21.2 Boundary

This section names the customization settings dimensions and their layer. File 15 owns the settings object model, the cascade, locality, agent exposure, and profiles; Files 25, 35, and 37 own the per-substrate settings the customization layer composes with. This file names the customization-relevant dimensions.

## 22. Explicit Rejections

Anchor: `customize.explicit-rejections`

The following are architecturally invalid for any later or per-surface spec:

- **A private customization store, runtime, or parallel persistence** — every customization is a settings/customization record persisted and resolved through the one settings substrate and rendered by File 37's container and registries; there is no browser-local-storage settings store, no per-surface customization config file as a live source of truth, and no parallel customization persistence (§3; `settings.explicit-rejections`, File 15 §20; `ui.renderer-boundary`, File 37 §16.4). The single device-local first-paint theme cache is a rebuildable projection, not a store (§6.2).
- **A parallel renderer table, theme table, widget table, or shell** — there is one `RendererRegistry` (File 37), one `ThemeRegistry`, one `WidgetRegistry`, and one shell and layout container; a surface, widget, or plugin contributes through them, never a parallel rendering path, theme store, widget store, or shell (§5.3, §9.2; `ui.explicit-rejections`, File 37 §23; `worksurface.explicit-rejections`, File 25 §20).
- **A raw visual value bypassing the token system, a theme that fails the contrast floor presented as conformant, or a theme with arbitrary styling authority** — every visual property is a semantic or component token, color tokens are perceptually-uniform and relatively derivable, and a theme validates against the required-token and contrast floors; a renderer or theme that references a raw value is invalid; a contrast-failing theme is never silently presented as conformant; and themes carry no arbitrary CSS selectors, global stylesheets, scripts, remote imports, or remote asset URLs (§4, §5.4; `ui.renderer-boundary`, File 37 §16.5; `ui.accessibility`, File 37 §14).
- **A widget as a backdoor around the system boundaries** — a widget's data and action access goes through the same capability, policy, secret, egress, and sandbox boundaries as every other consumer; a widget is not a privileged path, references secrets only by vault reference, treats external content as data not instruction, and runs executable content only in the confined runtime (§10, §9.3; the charter's §7 rule; `secret.backend-boundary`, File 22 §4; `security.untrusted-content`, File 22 §12).
- **A widget or layout that polls a substrate on a timer for live state** — widgets and customized views are event-first; a periodic refresh is a flagged, configurable fallback only where a source emits no change events (§10.5; `ui.streaming-presentation`, File 37 §10; `core.workspace-model`, File 01 §3 constraint).
- **A participation-level, autonomy-mode, persona, agent-mode, or phase field at the customization layer** — a per-profile or per-use-case default selects which theme, density, layout, and widgets open; a "personality" is a Memory or instruction preset governed by File 14; autonomy is the approval posture the policy layer resolves; the customization layer renders the consequences, never a mode field (§16, §17.4; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `worksurface.no-autonomy-field`, File 25 §13; `ui.interaction-models`, File 37 §7).
- **A non-reversible or non-removable customization, or an AI customization that traps the user** — every customization is reversible, removable, and resettable, with a snapshot before commit; the user is never trapped by a customization, whether made manually or by the agent (§3.2, §14.4, §17; `core.non-destructive-by-default`, File 01 §7.13; the charter's §4.4 rule).
- **An agent-only customization API, store, or path, or a silent AI customization** — AI-assisted customization uses the same `customize.*` capabilities, registries, validation, and approval as manual customization; the agent inspects and proposes, and a proposal applies only through the policy-gated, snapshot-backed commit; there is no agent-only API, no agent-only store, and no silent apply (§14; `core.extension-integrity`, File 01 §7.10).
- **AI customization that reasons over raw coordinates as the primary interface** — the agent reasons over the semantic-relational structural projection (regions, panels, widgets, slots, and their relationships); coordinates are secondary metadata, never the primary interface; a panel, widget, or control that cannot be represented structurally is invalid (§13; the charter's §5 rule; `worksurface.explicit-rejections`, File 25 §20).
- **Plugin UI placement by arbitrary core-UI mutation, by load order, or as a forced placement** — a plugin contributes widgets, themes, and presets through the registries and the source-approval path, its default placement is a proposal resolved through settings and the `customization_policy`, and it never edits core UI code or forces a placement (§15; `plugin.contribution-points`, File 35 §5.2; the charter's §11.1 rule).
- **A customization that exceeds the surface's `customization_policy`, slot compatibility, or density bound, or that pierces a permission floor** — placement is compatibility-checked and bound-enforced, the source (user/plugin/AI) must be permitted, and a customization never pierces a `permission_floor` or grants authority a capability could not declare (§11, §17.2; `worksurface.explicit-rejections`, File 25 §20; `policy.permission-floor`, File 06 §7).
- **Per-instance or per-plugin event namespaces for widget runtimes** — widget runtime events use the fixed `widget.runtime` namespace with source and instance identity as envelope cross-references or payload fields; dynamic namespaces such as one namespace per widget instance or plugin break File 10's registered custom-kind model and are invalid (§9.3, §20).
- **A raw secret in a customization record, export, or sync, or a customization synced as device-local-only state** — credentials are vault references, raw secrets never sync or export, and device-local customization state (the first-paint cache, window placement) never syncs as authority (§18; `secret.backend-boundary`, File 22 §4; `portability.sensitivity-egress`, File 21 §12).
- **A hardcoded customization behavior, bound, or visual value where meaningful variation belongs in settings** — themes, density levels, layout defaults, widget sets, AI-customization bounds, and placement bounds are settings, not hardcoded constants (§21; `settings.settings-over-constants`, File 15 §13).

## 23. Consequences for Later Specs

Anchor: `customize.consequences-for-later-specs`

Later specs must follow these rules:

- The **per-surface specs** (27–32 and equivalent future surfaces) declare their `customization_policy` (`worksurface.views-presets`, File 25 §7.4) — which kinds of customization they permit, at which slots, by which sources, within which bounds — and this file realizes it as slots and placement (§11); they contribute their built-in `ViewPreset`s, panel kinds, and any surface widgets and per-surface token overlays through the one registries and the token system, declare no private customization store, renderer table, theme table, or widget table, and render the deleted-field consequences (§17), never a participation, autonomy, or persona field. Their per-profile defaults are profile-layer defaults (§16).
- The **Extension and Plugin System** spec (File 35) contributes plugin widgets, themes, view presets, and panels through this file's `WidgetRegistry`, `ThemeRegistry`, preset library, and the `RendererRegistry`, under the bundle-granularity source approval, trust, attribution, and lifecycle it owns; this file places those contributions through the customization policy and the slot model, treating a plugin-sourced contribution identically to a built-in of the same kind (§15).
- The **Automation and Triggers** spec (File 33) and the **Workflows, Templates, and Reuse** spec (File 34) own the firing, run, and execution truth their widgets surface; a widget that displays their output reads their observability and consumption contracts and the run-now and enable/disable controls, and never becomes the firing or run truth (§2.8, §10).
- The **Quality Control and Validation** spec validates customization conformance — that every customization is a settings/customization record and not a private store, that every theme passes the required-token and contrast floors, that every widget and control exposes structural semantics, that every customization is reversible, that the AI customization path is the one capability path, and that no participation, autonomy, or persona field is reintroduced — through the registration validator and event and capability hooks, not a separate pipeline.
- The **Telemetry, Logging, and Observability** spec and the **Evaluation and Benchmarking** spec consume the customization events and the structural-understanding projection; they introduce no parallel customization-state store and honor the sensitivity and attribution of customization facts (§20).
- The **Runtime Infrastructure and Lifecycle** spec orchestrates the first-paint cache read and the customization-record load around the storage lifecycle, the device-local rebuild of the first-paint cache and the customization projections, and the registration of built-in and plugin widget renderers and themes in the startup phase order; it places no parallel customization runtime and persists no customization state across sync that §18 declares device-local.
- The **Packaging, Platform, and Distribution** spec (File 43) owns the installer, the auto-updater, the platform window-decoration and tray mechanics, the sidecar lifecycle, the concrete first-paint cache mechanism, and the bundling of the ship-with themes and plugins into the installer image; this file owns the theme, widget, layout, and per-profile-default declarations that spec distributes and the first-paint-cache contract.

Specific integration contracts will be stated in those files when they are written.
