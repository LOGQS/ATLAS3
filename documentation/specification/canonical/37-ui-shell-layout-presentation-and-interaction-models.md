# UI Shell, Layout, Presentation, and Interaction Models

## Status

Canonical. This file defines the presentation layer: the application shell, the layout container, the rendering of substrate state into views, the streaming and live-update contract, the presentation of control rails and approval/elicitation flows, the interaction models, and the accessibility, internationalization, and renderer-boundary contracts the user-facing frontend obeys. It realizes the UI-rendering boundary that Files 01–36 declare and delegate to this file, and introduces the net-new presentation primitives those files reference without owning: the `Shell` region model, the presentation-as-projection contract, the `RendererRegistry`, the `InteractionModel` lens set, the focused-dialog selector, and the accessibility contract. It is horizontal and surface-neutral — it defines how the one shared runtime is rendered and how user gestures are surfaced, not what any one surface does. The per-surface specs (27–32) declare what their views contain; this file defines how any view renders. Later canonical files may refine it, but may not contradict it. The UI Customization, Widgets, and Theming spec (File 38) consumes this file's contracts to define customization, widgets, and theming.

## Scope

This file defines:

- the presentation layer as a deterministic rendering of substrate projections plus a router of gestures into the control rails (File 26) for resolution — a layer that owns no business logic and no private durable state, realizing `core.invariants` (File 01 §7.5/§7.7) and `core.projection` (File 01 §6.11)
- the precise disambiguation of "UI," "surface," "view," "presentation," and "shell," and the distinction of the presentation layer from a work surface (File 25), a control rail (File 26), a presentation surface (`intent.presentation`, File 02 §8), an interaction shape (`core.interaction-shapes`, File 01 §2.2), the live `SurfaceState` (`world.surface-state`, File 18 §5), and the `ToolSurface` (File 07)
- the presentation-as-projection contract: every view is a typed projection over a named substrate source with an event-first rebuild trigger; the `RendererRegistry` that dispatches a typed substrate kind to its render component; and the no-private-presentation-state invariant
- the application `Shell` — the closed-canonical region model (command rail, focus surface, inspector dock, execution console, artifact navigator, conversation view, status region, notification region) realizing `worksurface.activation-shell` (File 25 §11.3) and `controlrail.shell-relationship` (File 26 §15) — plus navigation and the multi-window model
- the layout container — the recursive split structure, panel visibility states, the resize/split/dock mechanism, and responsive behavior — and the boundary with File 38's saved-layout customization
- surface presentation and morphing: rendering a work surface's declared panels and `ViewPreset`s, morphing as a projection of the `SurfaceContract` + live `SurfaceState` + routing decision, and panel self-registration
- the `InteractionModel` lens set (conversation-only, inline assist, sidecar, paired, orchestration desk) as presentation lenses, and the rendering of the consequences of the deleted autonomy/participation/persona fields without reintroducing them
- conversation and transcript presentation: the transcript as a projection of the block pool, `Message`-versus-`Event` rendering, conversation activity state, the message-collapse and grouping pipeline, inline capability-call rendering, message actions and variants, and the input-composer presentation
- the rendering of substrate primitives into views: block rendering, artifact rendering (two pipelines, three display modes, the confined interactive-artifact runtime), evidence/claim/citation/observation/provenance rendering, and version-timeline, comparison, and forensic-reconstruction views
- the streaming and live-presentation contract: typed-partial rendering, the streamed-partial-to-committed-block boundary, event-first reactivity, the rendering-performance requirements, sticky-scroll, and parallel presentation
- control-rail presentation (palette, keybinding capture and editor, voice and handsfree, menus/toolbars, steering affordances, slash commands, mentions and attachments, quick-open) and the available-action enable/disable contract
- dialog, elicitation, and notification presentation: the single focused-dialog priority selector, the rendering of the `policy.approval-ui-surface-contract` (File 06 §13) and `controlrail.elicitation` (File 26 §13) data contracts, and the notification/toast/badge surface
- inspector and management-surface presentation: the explainable context inspector, the substrate-service management surfaces, the observability surface, the debug surface, and the version-history/forensic-reconstruction view
- accessibility as a first-class, dual-purpose (human assistive technology and agent machine readability) invariant; internationalization presentation; the renderer-to-backend boundary and frontend architecture; UI loading/empty/error/degraded/onboarding states; world-model/perception/state-awareness integration; the `ui.*` capability surface, events, settings, persistence/locality, explicit rejections, and consequences for later specs

This file does not define:

- the `WorkSurface` primitive, the `SurfaceContract`, the `SurfaceRegistry`, the `PanelKind`/`ViewPreset` model, the no-private-architecture invariant, or the autonomy-field deletion — File 25 owns those; this file renders the contract they declare
- the `ControlRail` primitive, the `RailResolution` set, the input-resolution contract, the keymap model, the slash grammar, the voice-session contract, or the elicitation contract — File 26 owns those; this file renders the rails and the gestures they resolve
- the live `SurfaceState`, `PanelState`, `Selection`, `UiMode`, the world-entity catalogue, the durability tiers, the availability evaluator, or snapshot resolution — File 18 owns those; this file renders them and feeds them through self-registration
- the `Block`/`BlockKind`/`BlockContent`/lifecycle model, the `Artifact`/`Claim`/`Evidence`/`Citation`/`Observation`/`Provenance`/`Validation` model, or materialization — Files 08, 09, 24 own those; this file renders them
- the `ExecutionLedger` row format, the `EventEnvelope`, the `AppEvent` catalogue, the hook contract, the streamed-partial-to-committed-block durability rule, or aggregation policy — File 10 owns those; this file consumes the event stream and renders it
- the version graph, `ContextVersion`/`VersionDiff`, materialized view, branching, replay, or snapshot resolution — File 11 owns those; this file renders history, comparison, and reconstruction views as projections over them
- the policy evaluation algorithm, the approval router, leases, the `ApprovalRequest`/`ApprovalResponse`/`BatchApprovalRequest`/`ContradictionResolutionRequest` data contract, or effective-tier resolution — File 06 owns those; this file renders the data contract and never invents a parallel approval shape
- context assembly, the budget report, compaction, or token counting — File 13 owns those; this file renders the budget and the context inspector over its outputs
- audio capture, voice-activity detection, wake-word detection, transcription, screen capture, accessibility-tree capture, or any sensor mechanics — File 19 owns those; this file renders the voice session and observation viewers over their outputs
- the settings object model, the cascade, scopes, profiles, locality, the TOML overlay, or agent exposure — File 15 owns those; this file names the presentation settings dimensions and consumes the cascade
- the sandbox contract, isolation tiers, process control, or the elevated helper — File 23 owns those; the interactive-artifact runtime and any confined preview run through that contract
- the secret vault, trust model, egress governance, encryption, or the untrusted-content rule — File 22 owns those; this file honors the no-raw-secret-in-shareable-state and untrusted-content rules
- design tokens, the theme system and engine, named saved layouts and the save/switch/customize flow, widgets and widget placement, AI-assisted UI customization, plugin UI placement mechanics, or the realization of the `customization_policy` — File 38 owns those; this file owns the shell, the layout container, the rendering contracts, the interaction models, and the semantic-token discipline they consume
- packaging, the installer, the auto-updater, window-decoration platform mechanics, or sidecar lifecycle — the Packaging, Platform, and Distribution spec (File 43) owns those; this file owns the shell regions, the multi-window model, and the window-state presentation
- telemetry collection, log retention, or trace storage — the Telemetry, Logging, and Observability spec (File 41) owns those; this file owns the observability and debug surfaces that render them

## Source Resolution

Families reviewed: the application-shell and presentation material (`ui/14-1-application-shell.md`, `ui/14-2-chat-list-and-history.md`, `ui/14-3-streaming-ui.md`, `ui/14-4-source-management.md`, `ui/14-5-debug-and-performance.md`, `ui/14-6-to-14-8-theming-additional-windows-state.md`, `ui/15-1-layout-customizability.md`, `ui/15-2-domain-based-workspace-morphing.md`, `ui/15-3-and-15-4-participation-levels-personas.md`, `ui/context-management.md`, `ui/accessibility.md`, `ui/README.md`, `unit13-ui.md`); the UX-input and visual-design material (`ux-input/design-principles.md`, `ux-input/visual-identity.md`, `ux-input/whiteboard-and-handsfree.md`, `unit15-ux-distribution-files-glossary.md`); the conversation-presentation material (`conversation/01-core-chat.md`, `conversation/02-message-operations.md`, `conversation/03-versioning-and-branching.md`, `conversation/04-text-to-speech.md`, `conversation/05-voice-input.md`, `conversation/06-chat-dag.md`, `conversation/INDEX.md`, `unit03-conversation-engine.md`); the cross-cutting presentation contracts (`cross-cutting/actions.md`, `cross-cutting/artifacts.md`, `cross-cutting/blocks.md`, `cross-cutting/theming.md`, `cross-cutting/i18n.md`, `cross-cutting/state-awareness.md`, `cross-cutting/events.md`, `cross-cutting/service-layer.md`, `cross-cutting/errors.md`, `cross-cutting/response-parser.md`, `unit02-cross-cutting-infra-and-presentation.md`); the per-surface UI sections (`unit08-coder.md`, `domains/coder/ide-interface.md`, `domains/coder/command-palette.md`, `domains/coder/checkpoints-undo.md`, `domains/coder/agent-execution.md`, `domains/coder/terminal.md`, `unit09-web.md`, `domains/web/04-ui-and-modes.md`, `domains/web/00-overview.md`, `unit10-gui-control.md`, `domains/gui-control/06-element-inspector.md`, `unit11a-memory.md`, `unit11b-data-processor.md`, `unit11c-system-agent.md`, `unit11d-teacher.md`); the cross-tool UI synthesis (`unit11-cross-tool-learning.md`, `kuzeys-ui-customization-and-widgets-addendum.md`, `kuzeys-context-duplicate-prompt-handling-addendum.md`); the frontend-architecture addenda (`claude-code-frontend-addendum.md`, `claude-code-frontend-addendum-part2.md`, `opencode-frontend-addendum.md`, `continue-frontend-addendum.md`, `goose-frontend-addendum.md`, `goose-rust-addendum.md`, `cline-frontend-addendum.md`, `open-canvas-frontend-addendum.md`, `bolt-diy-frontend-addendum.md`, `open-webui-ux-addendum.md`); the locked stack and constraints (`foundations/stack.md`, `foundations/architecture.md`, `atlas3-core/CONSTRAINTS.md`, `atlas3-specbase/SKILL.md`, `distribution/packaging.md`); the strategic target-state review (`codex_recommendations.md` §5.1, §8.1, §8.12, §10.1–§10.9, §14.10); and the cross-ecosystem UI patterns (`warp-compressed.md`, `open-codesign-compressed.md`, `open-canvas-compressed.md`, `claudecodeui-compressed.md`, `t3code-compressed.md`, `terax-ai-compressed.md`, `suna-addendum.md`, `omi-compressed.md`, `voicebox-compressed.md`, `chatgpt_tool.md`, `claude_cowork_tool.md`).

Resolution rule: this file realizes and renders, it does not re-own. The work surface stays File 25's, the control rail stays File 26's, the live surface state stays File 18's, the block and artifact models stay Files 08/09's, the event stream stays File 10's, the version graph stays File 11's, the policy and approval contract stays File 06's, context assembly stays File 13's, perception stays File 19's, settings stay File 15's, security stays File 22's, the sandbox stays File 23's, and the design tokens, themes, widgets, and saved-layout customization stay File 38's. This file owns the `Shell` region model, the presentation-as-projection contract, the `RendererRegistry`, the layout container, the `InteractionModel` lens set, the focused-dialog selector, the accessibility contract, and the renderer-boundary rule, and supplies each to the layers that consume it.

Resolved tensions:

- **What the UI is.** The strongest position across the most-evolved sources (`atlas3-core/CONSTRAINTS.md` §1, `cross-cutting/service-layer.md`, `foundations/stack.md`, `cross-cutting/blocks.md` "the chat view is one projection of the block stream … the context inspector is a different projection … all three read the same underlying blocks") is that the UI is a rendering of substrate projections, not a place where state or logic lives. This file adopts it as a load-bearing invariant: the presentation layer owns no business logic (`core.invariants`, File 01 §7.7, `core.explicit-rejections`, File 01 §8 "business logic in React or command wrappers") and no durable state the substrate does not already own; every view is a projection (`core.projection`, File 01 §6.11), and the cost of any UI-state loss is a rebuild, never data loss.
- **Shell anatomy — chat-as-container versus task-centered shell.** Early specbase drafts framed conversation as the primary pane and surfaces as panels that "morph" around it; `codex_recommendations.md` §5.1/§10.1 and `intent.presentation` (File 02 §8) reject chat-as-universal-container and resolve toward a task-centered shell where conversation is an always-available control rail and view, not the forced primary pane. This file adopts the task-centered shell (§4), consistent with `worksurface.activation-shell` (File 25 §11.3), `controlrail.shell-relationship` (File 26 §15), and `core.product-thesis` (File 01 §1). The "chat is always visible, surfaces compose alongside" composition rule from `ui/15-2-domain-based-workspace-morphing.md` survives as the default conversation-first presentation, not as a container constraint.
- **Participation levels, autonomy modes, and personas.** Nearly every reviewed source still names a `Drive`/`Supervise`/`Collaborate`/`Delegate` participation level, a `PermissionMode`/`GooseMode`/agent-mode dial, or a persona/personality preset attached to interaction. The canon deletes all of them at every layer (`worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17; `world.surface-state`, File 18 §5.5; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `settings.explicit-rejections`, File 15 §20). This file adopts the deletion and fixes the presentation consequence (§7): the UI renders the *effect* those fields once described — the approval posture (Files 05, 06), which panels and `ViewPreset` are open (File 25), and progressive disclosure — without any mode field, dial, or autonomy control at any UI layer. An interaction shape is a presentation lens varied freely by the user and the UI, never a backend primitive.
- **The 37/38 boundary.** `worksurface.views-presets` (File 25 §7.6), `worksurface.consequences-for-later-specs` (File 25 §21), and `controlrail.consequences-for-later-specs` (File 26 §21) split presentation from customization: the UI Shell spec owns shell, panel, and morphing presentation; the UI Customization spec owns concrete placement, widgets, and theming. This file fixes the line precisely (§5.5): File 37 owns the layout container, the panel-type rendering, the built-in `ViewPreset` rendering, the morphing presentation, the renderer registry, the interaction models, and the semantic-token discipline; File 38 owns user-saved named layouts and the save/switch/customize flow, widgets and widget placement, the design-token system and themes, AI-assisted customization, and plugin UI placement. The default rendering is complete without File 38; File 38 adds customization over it.
- **Rendering as a registry versus per-surface bespoke views.** The source frontends converge on a kind-to-renderer registry (`unit13-ui.md` D13.11 `BlockRendererRegistry`, `claudecodeui-compressed.md` declarative tool configs, `opencode-frontend-addendum.md` tool-info registry, `cross-cutting/artifacts.md` `mime_type`-to-pipeline table). This file adopts one `RendererRegistry` (§3.3): a typed substrate kind dispatches to a render component, extensible through the same proposal-first source-approval path every other registry uses, so a surface or plugin contributes a renderer rather than forking a parallel rendering path.
- **Streaming as typed partials versus token strings.** `codex_recommendations.md` §10.2 and the frontend addenda resolve that streaming operates at the level of typed partials (text, plan, task-state, artifact-preview, diff-preview, validation, observation deltas), not only token strings, so the UI reads as an execution environment. This file adopts typed-partial streaming (§10) over `ledger.streaming-live-partials` (File 10 §12), and adopts the event-first, never-poll reactivity the project constraint requires (`core.event-first-by-default`, File 01 §7.15).
- **The locked frontend stack.** `foundations/stack.md`, `atlas3-specbase/SKILL.md`, and `core.stack-commitments` (File 01 §9) lock the renderer to a webview frontend over typed IPC (request-response invoke plus a streaming channel), with no in-renderer network server, and a compile-time type bridge between the backend service layer and the renderer. This file specifies the provider-invariant contract (§16) — the renderer is an adapter over typed IPC, business logic stays in the service layer, the same service layer serves the headless and command-line clients — without copying any specific library API; concrete library, bundler, and platform-window mechanics are the renderer implementation's and File 43's.

## 1. Chosen Model

Anchor: `ui.chosen-model`

ATLAS3 has one presentation layer. It renders the one shared runtime and routes the user's gestures into the control rails (File 26) that resolve against it. It is the realization of `core.invariants` (File 01 §7.5)'s flexible-presentation rule — "presentation shape may vary by surface, interaction shape, and request complexity without changing the underlying runtime model" — and the structural enforcement of `core.invariants` (File 01 §7.7)'s service-layer-ownership rule.

The presentation layer does two things and only two things:

- it **renders projections** of substrate state — `SurfaceState` and `UiMode` (File 18 §5), the materialized view over the block pool (Files 08, 11), the `Artifact`/`Evidence`/`Claim`/`Citation`/`Observation`/`Provenance` entity layer (File 09), the event stream and live partials (File 10), the version graph (File 11), the tool surface and available-capability list (Files 07, 18 §9), the budget report (File 13), the approval and elicitation contracts (Files 06, 26), and the run presentation projection (`run.presentation`, File 04 §25)
- it **captures gestures** in its modalities and routes them to the `ControlRail` layer (File 26), which resolves them to `Capability` invocations (File 05) gated by the one policy layer (File 06) and routed by the one router (File 03); and it **self-registers** the live state of its panels back to the world model (`world.observation-state-update`, File 18 §8.1)

The presentation layer owns no business logic and no private durable state. Every view is a `core.projection` (File 01 §6.11): rebuildable from its source-of-truth substrate, declaring an event-first rebuild trigger, never the source of truth for any durable fact, and recoverable by rebuild on loss. Its only state is ephemeral view state — which panels are open, scroll position, focus, in-progress composition — which is itself the live `SurfaceState` the world model holds (transient), plus client-only presentation preferences resolved and persisted through the settings system (File 15). Business logic, durable state, and the source of truth live in the backend service layer; command handlers and the renderer are adapters (`core.invariants`, File 01 §7.7; `atlas3-core/CONSTRAINTS.md` §1 realized).

This file introduces the net-new presentation primitives the prior files referenced without owning: the `Shell` region model (§4), the presentation-as-projection contract and the `RendererRegistry` (§3), the layout container (§5), the `InteractionModel` lens set (§7), the focused-dialog selector (§12), and the accessibility contract (§14). `Shell`, `RendererRegistry`, `InteractionModel`, and `PresentationView` are new canonical noun-objects.

### 1.1 "UI," "Surface," "View," and "Shell" Are Disambiguated

Anchor: `ui.disambiguation`

The words "UI," "surface," "view," and "mode" are overloaded across the canon. This file fixes the presentation-layer meanings and distinguishes them:

- the **presentation layer** (this file) — the rendering of substrate projections plus the capture and routing of gestures (resolved by the control rails, File 26). It owns no business logic, no durable store, and no work model. It is the realization layer for the rendering every prior file delegates to "the UI specs."
- a **work surface** (`worksurface.work-surface`, File 25 §3) — a primary user-facing work environment with specialized workflows and views, declared by a `SurfaceContract`. The presentation layer renders a work surface; it is not one.
- a **control rail** (`controlrail.control-rail`, File 26 §3) — a gesture-and-control mechanism that resolves a gesture to a `RailResolution`. The presentation layer renders a rail's surface (the palette, the keymap capture, the voice session) and routes gestures to it; it is not a rail.
- a **presentation surface** (`intent.presentation`, File 02 §8) — a projection over the underlying work: a conversation-first transcript, a comparison board, a notebook view, an observability trace, an artifact diff. A presentation surface is a *kind of view*; this file is the layer that realizes the rendering of presentation surfaces and fixes that the set is extensible.
- a **`PresentationView`** (this file, §3) — a single rendered projection: a typed view over a named substrate source, produced by a renderer from the `RendererRegistry`. A presentation surface is composed of one or more `PresentationView`s.
- an **interaction shape** (`core.interaction-shapes`, File 01 §2.2) — conversation-only, inline assist, sidecar, paired, orchestration desk: a presentation and involvement lens. This file realizes it as the `InteractionModel` (§7), a presentation lens, never a backend field.
- the live **`SurfaceState`** and **`UiMode`** (`world.surface-state`, File 18 §5) — the runtime values of the active surface, panels, focus, selection, available capabilities, and interaction mode. The presentation layer renders these values and produces them through self-registration; File 18 holds them.
- the **`ToolSurface`** (`surface.chosen-model`, File 07 §1) — the capability-visibility projection an invoker sees. The presentation layer renders the palette, menu, and rail projections of the `ToolSurface`; it does not compose it.
- the **`Shell`** (this file, §4) — the composition of the always-available control rails, the focus surface, the inspectors, the execution console, the artifact navigator, and the conversation view into one application window. It is a region model and a rendering relationship, not a durable object and not a work surface.

### 1.2 Boundary

This file defines how the runtime is rendered and how gestures are surfaced. It does not define what any surface does (the per-surface specs), how a gesture resolves (File 26), whether an invocation is permitted (File 06), what a lens shows (File 07), how a run executes (File 04), how live interaction state is held (File 18), how content is captured (File 19), or how the UI is customized, themed, or extended with widgets (File 38).

## 2. Boundaries with Adjacent Layers

Anchor: `ui.boundaries`

### 2.1 With File 01 (Core Thesis)

This file realizes `core.invariants` (File 01 §7.5) flexible presentation, §7.7 service-layer ownership, §7.9 system-wide customization (the simple-by-default, progressive-disclosure spectrum), §7.10 extension integrity (renderers and widgets are reversible, policy-bound, source-trusted), and §7.11 user control (the steering and cancellation affordances). It realizes `core.interaction-shapes` (File 01 §2.2) as the `InteractionModel` lens (§7), `core.projection` (File 01 §6.11) as the presentation-as-projection contract (§3), and `core.typed-errors` (File 01 §6.9) at the renderer boundary (§16). It honors `core.stack-commitments` (File 01 §9) for the webview frontend and typed IPC, and `core.explicit-rejections` (File 01 §8): no business logic in the renderer, no interaction shape coupled to surface or model identity, no autonomy control in core architecture. `Shell`, `RendererRegistry`, `InteractionModel`, and `PresentationView` are new canonical noun-objects.

### 2.2 With File 02 (Conversation, Intent, Task)

`intent.presentation` (File 02 §8) is the primary delegation this file discharges: a presentation surface is a projection over work, the set is extensible, conversation-first and workspace-first are both first-class, parallel activity must not be forced into one flat stream, and presentation customization never changes the work model. §6, §7, §8, and §10 of this file realize those rules. `intent.conversation-state` (File 02 §2.3)'s coarse activity state (`streaming`/`processing`/`awaiting_user`/`idle` plus the `compacting` indicator) is rendered as a projection (§8.3); `intent.message` (File 02 §3.3)'s `Message`-versus-`Event` distinction is the transcript-rendering contract (§8.2). This file renders conversation; File 02 owns the conversation model.

### 2.3 With File 03 (Routing and Dispatch) and File 04 (Execution and Run Model)

The presentation layer surfaces the routing result and allows override (`intent.run-intent`, File 02 §4.2; `routing.route-record`, File 03) but does not route. It renders `run.presentation` (File 04 §25)'s execution projection — the same run shown as a conversation answer, compact progress, expandable timeline, workspace activity, multi-agent board, artifact diff, workflow graph, or observability trace — and the run facts that section requires the UI to show (status, active execution unit, pending approvals, model route, capability calls and results, child runs, artifacts, failure and recovery path). Steering affordances render the user-facing surface of `run.user-intervention` (File 04 §17.1) and `run.cancellation` (File 04 §17.3); the rail resolves them (File 26 §10) and File 04 carries them out.

### 2.4 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces)

Every user-invocable control the presentation layer renders is a presentation of a `Capability` (`capability.capability`, File 05 §2.1), reachable through a rail (File 26) and gated by policy (File 06); the UI invokes no operation out of band. The palette, menus, and shortcut surfaces render the lens `surface.visibility-composition-resolution-algorithm` (File 07 §9) composes and `surface.presentation-in-user-facing-surfaces` (File 07 §12) projects; the available-capability list is `world.state-aware-capability-availability` (File 18 §9). Approval and elicitation rendering consumes the `policy.approval-ui-surface-contract` (File 06 §13) data contract verbatim and never invents a parallel approval shape (§12).

### 2.5 With Files 08, 09, 11 (Blocks, Artifacts, Version Graph)

The transcript, the inspectors, and the execution views are three projections of the one block pool (`block.cross-surface-interoperability`, File 08 §12; `cross-cutting/blocks.md` realized). The presentation layer renders `Block`s through the `RendererRegistry` (§9) and the entity layer (`Artifact`/`Claim`/`Evidence`/`Citation`/`Observation`/`Provenance`/`Validation`, File 09) through their renderers and the `artifact.per-surface-projections` (File 09 §17.2) lenses; it introduces no private block pool, kind catalogue, or content model. History, comparison, undo affordances, and forensic reconstruction are projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24); the UI introduces no parallel checkpoint, snapshot, or history store, and renders artifact and file edits live as new versions commit.

### 2.6 With File 10 (Ledger, Events, Hooks)

The presentation layer is the primary live subscriber to the event bus. It consumes `ledger.event-stream` (File 10 §5) with the `ledger.event-envelope` (File 10 §5.2) envelope and the `ledger.app-event-catalogue` (File 10 §5.3) vocabulary, renders `ledger.streaming-live-partials` (File 10 §12)'s streamed partials and the partial-to-committed-block boundary, and honors `ledger.sensitivity-aware-persistence-retention` (File 10 §10) — `Secret` content never renders into shareable state, and the envelope's sensitivity classification gates what appears in screenshots and exports. The UI emits its own presentation facts as `Custom { namespace: "ui" }` events (§21); it opens no side-channel and no parallel bus.

### 2.7 With File 13 (Context Assembly), File 16/17 (Model Strategy, Provider Layer)

The context inspector and budget bar render `context.context-policies` (File 13 §4)'s outputs and the budget report `context.consequences-for-later-specs` (File 13 §22) exposes, including the live dry-run preview; the UI assembles no model request. Model-route indicators, usage and cost dashboards, and provider-health indicators render `model.model-strategy-layer` (File 16) selections and `provider.consequences-for-later-specs` (File 17 §26)'s per-call attribution and health state; the UI selects no model and tracks no usage.

### 2.8 With File 15 (Settings)

Every presentation behavior with meaningful variation is a setting (`settings.settings-over-constants`, File 15 §13) resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); the UI is not a durable settings scope (§22). The renderer reads settings reactively (the setting-change event drives re-render) and persists client-only presentation preferences through the settings system, never a private store (§16, §19). The presentation layer renders no autonomy or participation knob, because none exists in settings (`settings.explicit-rejections`, File 15 §20).

### 2.9 With File 18 (World Model) and File 19 (Perception)

This file renders `world.surface-state` (File 18 §5) — the `SurfaceState`, `PanelState`, `Selection`, and `UiMode` File 18 §5.6 states "the UI specs render" — and produces it: the presentation layer's panels self-register their state to the world model on mount, focus, selection, and content change (`world.observation-state-update`, File 18 §8.1), so the UI is both the renderer and the source of live `SurfaceState`. Available-action enable/disable renders the availability evaluator's output (`world.state-aware-capability-availability`, File 18 §9). Observation viewers (screenshots, accessibility-tree overlays, page and machine snapshots) render `Observation` blocks (File 09 §13) produced by `perception.*` (File 19); the UI captures nothing and screen-scrapes nothing of its own state.

### 2.10 With Files 22, 23, 24 (Security, Sandbox, Workspaces)

The presentation layer honors `secret.backend-boundary` (File 22 §4) — raw secrets never reach the renderer and never render into shareable state — and `security.untrusted-content` (File 22 §12): rendered untrusted content (web pages, foreign application captures, ingested documents) carries no authority and is presented as content, never as instruction. The interactive-artifact runtime and any confined preview render inside the one `Sandbox` contract (File 23) at a least-authority origin; the UI opens no private sandbox. Workspace, file-tree, and materialized-path views render `workspace.materialization` (File 24 §10)'s mirror as a projection of the active version; the UI writes to disk only through the workspace materialization path.

### 2.11 With File 25 (Work Surface Contract) and File 26 (Control Rails)

`worksurface.consequences-for-later-specs` (File 25 §21) and `controlrail.consequences-for-later-specs` (File 26 §21) name this file as the consumer that renders the `SurfaceContract`, live `SurfaceState`, and routing decision into shell presentation and surface morphing (§4–§7), and renders the command rail plus focus surface, the palette, the keybinding capture and editor, the voice waveform and confirmation, the menus and toolbars, and the steering affordances over the data and resolution contracts those files fix (§11). Presentation may vary freely; the surface and rail contracts may not. This file renders both and re-owns neither.

### 2.12 With File 38 (UI Customization, Widgets, and Theming) and File 43 (Packaging)

This file owns the shell, the layout container, the panel-type rendering, the built-in `ViewPreset` rendering, the morphing presentation, the renderer registry, the interaction models, and the semantic-token discipline. File 38 owns user-saved named layouts and the save/switch/customize flow, widgets and widget placement, the design-token system and themes, AI-assisted customization, and plugin UI placement, consuming this file's contracts (§5.5). File 43 owns the installer, the auto-updater, platform window-decoration mechanics, and sidecar lifecycle; this file owns the shell regions, the multi-window model, and the window-state presentation that File 43 packages.

### 2.13 Boundary

This file is the presentation layer. It owns the `Shell`, the layout container, the rendering contracts, the interaction models, the dialog/elicitation/notification presentation, the accessibility and internationalization contracts, and the renderer boundary. It owns no work model, no rail resolution, no policy, no capability, no live state ownership, no capture, no settings storage, no design-token system, and no customization mechanics. It renders the substrate; the owning files realize it.

## 3. The Presentation-as-Projection Contract

Anchor: `ui.presentation-projection`

### 3.1 Definition

A `PresentationView` is one rendered projection: a typed view over a named substrate source, produced by a renderer, that displays the source's current state and updates when the source changes. The presentation-as-projection contract is the rule that every view in the UI is a `PresentationView`, that it holds no source-of-truth state, and that it is rebuildable from its substrate.

### 3.2 Rule

- Every `PresentationView` declares the substrate source it projects (a block-pool query, a `SurfaceState` scope, an event-stream subscription, a version-graph projection, an entity-pool lens, a budget report, an approval-contract subscription) and the event-first trigger that rebuilds it (`core.projection`, File 01 §6.11; `world.state-change-events-reactivity`, File 18 §12). A view never polls a substrate on a timer; it subscribes to the substrate's change events. A periodic refresh is a flagged, configurable fallback only where a source emits no change events (a hardware metric sample), never a correctness condition (`core.event-first-by-default`, File 01 §7.15).
- A `PresentationView` holds no durable fact. Its rendered content derives from the substrate; its view-local state (expanded/collapsed, scroll position, in-progress composition, focus) is ephemeral and is the live `SurfaceState` the world model holds (File 18 §5), reconstructed from self-registration on remount. The cost of losing any view state is a rebuild, never data loss.
- The presentation layer holds no business logic. A view computes derived presentation values (formatting, grouping, layout arithmetic, syntax highlighting) but never the substrate's truth: it does not decide policy, route, select a model, mutate a block, evaluate availability, or own a capability's effect. Those are service-layer concerns reached through typed invocations (§16; `core.invariants`, File 01 §7.7).
- A `PresentationView` renders `Secret`-classified content as masked, never raw, and respects the sensitivity classification of the envelope and block it renders (File 10 §10, File 22 §4); a view never persists or exports raw secret material.

### 3.3 The `RendererRegistry`

The `RendererRegistry` is the one registry that maps a typed substrate kind to the renderer that displays it. A renderer is registered for a `BlockKind` (File 08 §3.1), an `ArtifactKind` (File 09 §4.1), an `ObservationKind` (File 09 §13.2), a `PanelKind` (File 25 §5.3), an `AppEvent` kind (File 10 §5.3), or an external-content media type, and dispatches that kind to its render component.

Renderer trust and content trust are separate. A renderer is registered code from a built-in or source-approved contribution; the content it renders keeps its own authority class and sensitivity. External, web, connector, model, or tool-returned content is data and must not execute as host UI code. Executable or interactive untrusted artifacts use the sandboxed artifact-runtime path (§9.3), not ordinary renderer dispatch.

- Dispatch checks the registry first, then a canonical baseline renderer; an unregistered or unknown kind renders through a safe typed-placeholder renderer that shows the kind, a description, and a recovery action, never a crash or a blank (`block.kind-catalogue`, File 08 §3.1's custom-kind path; `intent.presentation`, File 02 §8.1's typed-placeholder-elsewhere rule). The baseline includes renderers for the canonical block kinds (message, reasoning, tool-call and tool-result, file attachment, retrieved-content, evidence, citation, observation, validation, critique, claim, plan, group), the canonical artifact kinds, and the canonical panel kinds.
- Surface-specific and plugin-contributed renderers register through the one proposal-first source-approval-gated path (`capability.runtime-mutation`, File 05 §16.2; `policy.source-approval-flow`, File 06 §9), under the same source taxonomy and trust model as every other contribution; a surface or plugin contributes a renderer, never a parallel rendering pipeline. There is one `RendererRegistry`; no surface, rail, or plugin maintains a private renderer table.
- A contributed renderer may override a baseline renderer only within a bounded anti-shadowing policy, so a source-approved contribution cannot silently shadow a security- or trust-critical presentation — the presentation realization of the renderer-override rule `plugin.contribution-points` (File 35 §5.3) delegates to this file. Baseline-only kinds — the approval and elicitation dialogs (§12), tool-call and tool-result rendering, masked-secret rendering, and the trust and provenance indicators — render through the canonical baseline renderer only and are never overridable by a surface, rail, or plugin contribution. The canonical content kinds (the block, artifact, observation, and panel kinds the baseline covers) are overridable, but an override that shadows a canonical renderer is surfaced to the user and applied only with consent (`policy.source-approval-flow`, File 06 §9), never silently. `Custom { namespace, name }` kinds are freely registered and overridden within their own namespace.
- A renderer receives the typed substrate value and a presentation context (the active `InteractionModel`, the display mode, the scope, the resolved semantic tokens, the resolved locale) and returns a `PresentationView`. Renderers consume only the semantic-token layer for visual properties (§16.5); a renderer that references a raw color, radius, font, spacing, or animation value rather than a semantic token is invalid.

### 3.4 Boundary

This section fixes the projection contract and the renderer registry. The substrate files own each source; this file requires every view to be a projection over one. File 38 owns the widget and theme layers that register additional renderers and tokens through this same registry and the same token discipline.

## 4. The Application Shell

Anchor: `ui.shell`

### 4.1 Definition

The `Shell` is the composition of the always-available control rails, the focus surface, the supporting inspectors, the execution console, the artifact navigator, and the conversation view into one application window. It is the rendering realization of the shell relationship `worksurface.activation-shell` (File 25 §11.3) and `controlrail.shell-relationship` (File 26 §15) name, and of `codex_recommendations.md` §10.1's task-centered shell. It is a region model and a rendering relationship, not a durable object.

### 4.2 The Region Model

The `Shell` is a closed-canonical set of `ShellRegion`s, each a placement for `PresentationView`s. The canonical regions:

- **command rail** — the always-available entry-and-control region rendering the conversation input rail and the command palette trigger (File 26 §5, §6); always reachable regardless of the focus surface
- **focus surface** — the primary region rendering the currently active work surface or presentation surface (File 25 §11.2); whatever the task currently needs
- **inspector dock** — the secondary region rendering management and inspection surfaces (context inspector, sources, memory, world state, settings; §13)
- **execution console** — the region rendering the live execution projection of active runs (`run.presentation`, File 04 §25): status, active execution unit, progress, the activity feed
- **artifact navigator** — the region rendering the artifact and output pool (`artifact.per-surface-projections`, File 09 §17.2): produced artifacts, history, and entry points to open them
- **conversation view** — the region rendering the transcript (§8); an expand/collapse view, available alongside any focus surface, never the forced primary pane
- **status region** — the persistent region rendering coarse run and connection state, model route, and shell-level indicators
- **notification region** — the region rendering transient notifications, toasts, and badges (§12.4)

`ShellRegion` is closed-canonical-plus-`Custom { namespace, name }` (`core.closed-canonical`, File 01 §6.16); a new region kind is a canonical-spec change or a registered extension, never an ad-hoc placement. A region may be present or absent in a given presentation; the conversation view is always available to expand. No region is the mandatory primary: the focus surface is whatever the work needs, and conversation is an always-available control rail and view, never the forced container (`core.product-thesis`, File 01 §1; `intent.presentation`, File 02 §8; the chat-as-universal-container rejection, File 25 §20).

### 4.3 The Composition Rule

- The default conversation-first presentation renders the conversation view as the focus content with the other regions collapsed or minimal; richer presentations compose work-surface focus and supporting regions alongside the conversation view without replacing it (`ui/15-2-domain-based-workspace-morphing.md` realized; `atlas3-specbase/SKILL.md` "chat is the substrate"). The same work moves between conversation-first and a work-surface focus over time without changing the work model (`intent.presentation`, File 02 §8.2/§8.3).
- The presentation activation of a region or surface (opening, focusing, expanding, collapsing) is a UI-state operation scoped to the conversation, workspace, or session (`worksurface.activation-shell`, File 25 §11.2); it updates live `SurfaceState` (File 18) and may influence future routing or user-invoked resolution, but it never rewrites an active run's execution binding. A run's primary surface and execution context change only through `routing.mid-execution-reroute` (File 03 §12) or explicit user override (`worksurface.explicit-rejections`, File 25 §20's presentation-focus-is-not-reroute rule).
- A supporting region may auto-reveal on a declared reveal-trigger class. The canonical `RevealTrigger` set is closed-canonical-plus-`Custom { namespace, name }` — `RunStarted`, `FirstOutput`, `ArtifactProduced`, and `PendingRequest` — with each region declaring which classes it honors: the execution console may reveal on `RunStarted`, the artifact navigator on `ArtifactProduced` or `FirstOutput`, and a custom region declares and honors its own `Custom` trigger classes. Approval and elicitation remain the focused-dialog selector's domain (§12); a `PendingRequest` at most drives a badge on a relevant region, never a region reveal that displaces the focused-dialog selector. Auto-reveal never moves keyboard or assistive-technology focus off the focus surface, never blocks it, and falls back to badge-only behavior when disabled.
- Shell composition is scope-resolved: there is no single global active region or surface when multiple sessions are live (`world.surface-state`, File 18 §5.1); the shell resolves the regions for the scope it presents.

### 4.4 Navigation

The shell renders navigation between conversations, surfaces, and workspaces: the conversation list and history (grouped, searched, filtered, with per-entry metadata and unread indication), the surface and workspace selectors, breadcrumb and back affordances, and the quick-open and global-search surfaces (§11). Navigation resolves through a typed `NavigationTarget`: a conversation plus block or version, a surface plus selection, an artifact plus version, or a management surface plus filter. Quick-open, global search, notification reveal actions, and External-Protocol rail deep links (File 26 §12) resolve through the same target contract. Navigation is presentation: selecting a target activates or reveals it for the scope and re-renders; it commits no work-model change beyond the activation the underlying capability performs. Conversation, surface, and workspace navigation render the identities Files 02, 25, and 24 own; the UI maintains no parallel list. Navigation originating from an external deep link is reveal-only and `ReadOnly`; any consequential action encoded by a link enters through the normal rail, capability, policy, and approval path.

### 4.5 The Multi-Window Model

The shell is one primary window rendering the region model, plus a bounded set of independent secondary windows for surfaces that are genuinely separable: a settings window, a voice-companion window, a hand-out or presentation view, and equivalent. Each secondary window is an independent renderer root over the same service layer (§16); windows share no in-memory state and coordinate only through the event bus and the settings system (`foundations/stack.md` realized). A secondary window follows a focus-or-create discipline (activating an already-open window rather than creating a duplicate), persists its position and size as client-only preferences (§19), and restores on next open. Restore is device-local and revalidated against the current display, virtual desktop, workspace, and permission state; if the saved placement is unavailable, unsafe, or off-screen, the shell uses a safe default placement and records a diagnostic UI event. Window-decoration and platform-window mechanics are File 43's; this file owns the region rendering and the cross-window coordination contract.

### 4.6 Boundary

This section owns the shell region model, the composition rule, navigation, and the multi-window model. File 25 owns the shell relationship and the surface activation it renders; File 26 owns the rails it places; File 18 owns the live state it resolves; File 43 owns the window and installer mechanics; File 38 owns customization of region placement. This file renders the shell.

## 5. Layout

Anchor: `ui.layout`

### 5.1 Definition

The layout container is the structural model the shell uses to arrange `PresentationView`s within and across regions: how panels split, size, dock, collapse, and reflow. This section owns the container and its behavior; File 38 owns user customization of it.

### 5.2 The Container

- The layout container is a recursive split structure: a node is a single panel or a split (horizontal or vertical) of child nodes, each carrying a size or flex weight and a minimum size, with a divider position at each split. Panels carry a visibility value drawn from the `PanelState` set (`open`, `collapsed`, `side`, `fullscreen`, `hidden`, `world.surface-state` File 18 §5.3) and may be detached to a secondary window (§4.5).
- A panel renders a `PanelKind` (File 25 §5.3) through the `RendererRegistry` (§3.3). Panel types are the cross-surface roles File 25 declares (editor, terminal, browser, inspector, document, canvas, list, board, timeline, graph, diff, preview, and equivalents); two surfaces rendering the same panel kind share the renderer (`block.cross-surface-interoperability`, File 08 §12), and an embedded borrowed panel carries its own `surface_binding` for invocation resolution and attribution without changing the host surface (`worksurface.activation-shell`, File 25 §11.4).
- The container supports resize (drag a divider, with min-size clamping), split and unsplit, reorder, collapse and expand, and detach to a window. These are presentation operations on view state; they commit no work-model change. The interaction affordances (drag handles, focus indicators) expose the structural semantics §14 requires.

### 5.3 Built-in Presentation Presets

- The shell renders a surface's declared `ViewPreset`s (`worksurface.views-presets`, File 25 §7.2): a named startup layout shape binding a panel set, arrangement, focus shape, and visible inspectors. Applying a `ViewPreset` changes presentation only; it never silently changes model selection, context policy, execution entry, budget, sandbox profile, approval posture, or instruction-source authority (`worksurface.views-presets`, File 25 §7.2; the silent-policy-change rejection, File 25 §20). A `ViewPreset` is a presentation seed, not an autonomy mode (§7).
- The shell ships a default layout per surface and a default conversation-first layout; the default rendering is complete without any user customization. Where a surface or profile declares a default `ViewPreset`, the shell renders it on activation; the user may switch presets through the rail (`controlrail.command-rail`, File 26 §6), and switching is a presentation change.

### 5.4 Responsive Behavior

The layout container adapts to the available viewport: at a narrow width, horizontal splits stack vertically, dividers collapse, and the shell presents one primary panel at a time with navigation between them. The breakpoints and the stacked behavior are presentation settings (§22). A constrained-platform shell (mobile) is a purpose-built presentation, not a reflowed desktop shell (`foundations/stack.md` "a dedicated UX shell, not a responsive desktop"); this file owns the desktop shell's responsive behavior and the contract that a constrained shell renders the same substrate through a distinct region composition.

### 5.5 The File 37 / File 38 Boundary

This section fixes the line between presentation and customization:

- **File 37 owns**: the layout container and its structure, the resize/split/dock/collapse/detach mechanism, panel-kind rendering, built-in `ViewPreset` rendering, the default layouts, responsive behavior, the morphing presentation (§6), the `RendererRegistry`, the interaction models, and the semantic-token *discipline* (renderers consume only tokens).
- **File 38 owns**: user-saved named layouts and the save, switch, rename, and reset flow; widgets and widget placement into customizable regions; the design-token *system* and the themes; AI-assisted layout and widget customization; plugin UI placement; and the realization of the surface's `customization_policy` (`worksurface.views-presets`, File 25 §7.4).

The boundary is structural: File 37's layout container renders a layout; File 38 supplies user-customized layouts, widgets, and themes that the container renders through the same contracts. A user-saved layout, a widget placement, and a theme are all settings/customization records (File 15, File 38) that this file's container and registry render without special-casing.

### 5.6 Boundary

This section owns the layout container, the built-in presets, responsive behavior, and the customization boundary. File 25 owns the `PanelKind`/`ViewPreset` model and the `customization_policy`; File 18 owns the panel visibility state; File 15 and File 38 own the saved-customization records. This file renders the container.

## 6. Surface Presentation and Morphing

Anchor: `ui.surface-presentation-morphing`

### 6.1 Definition

Surface presentation is the rendering of an active work surface into the focus region: its declared panels, its `ViewPreset`, its inspectors, and its cross-cutting affordances. Morphing is the transition between presentations as the active surface, view preset, or task changes. This section owns the rendering and the transition; File 25 owns the surface declaration, File 18 owns the live state.

### 6.2 Rule

- The shell renders a surface from three inputs `worksurface.views-presets` (File 25 §7.3) fixes: the surface's `SurfaceContract` (the declared panels, view presets, inspectors, and cross-cutting affordances), the live `SurfaceState` (the open panels, primary panel, focus, selection, and `UiMode`, File 18 §5), and the routing decision (the `primary_surface`, File 03 §8). The surface declares the shape; the world model holds the values; the router selects the execution binding; this file renders the composition.
- Morphing is a presentation projection. When the active presentation surface changes — the user activates a different surface, applies a different `ViewPreset`, or the run's task state and produced artifact type change — the shell re-composes the focus region and supporting regions and animates the transition. Morphing is driven by the surface, view preset, live state, and, for runs, the task state and artifact type, not by a domain identity alone (`codex_recommendations.md` §10.4's refinement). Morphing changes presentation, never the work model (`intent.presentation`, File 02 §8.1/§8.5; `worksurface.views-presets`, File 25 §7.3).
- A surface's panels self-register their live state to the world model on mount, focus, selection, and content change, and unregister on unmount (`world.observation-state-update`, File 18 §8.1); the shell renders the registered state and never screen-scrapes a surface to learn its own state (`perception.tiered-sensing`, File 19 §5.4). A panel or control that cannot be represented structurally — that exposes no semantic role, label, interaction kind, and state relationship sufficient for the world model, the control rails, and assistive technology — is invalid (`worksurface.explicit-rejections`, File 25 §20's structural-invisibility rejection; §14).
- Transition, animation, and navigation behavior are this file's. Animations use the semantic motion tokens (§16.5), are GPU-friendly (transform and opacity, not layout properties), honor the reduced-motion preference (§14), and never gate correctness on elapsed time. A morph in flight never blocks substrate updates: a region renders live substrate state throughout the transition.

### 6.3 Boundary

This section owns the surface-presentation rendering and the morphing transition. File 25 owns the `SurfaceContract`, the `ViewPreset` model, and the morphing-shape declaration; File 18 owns the live state; File 03 owns the routing decision; File 38 owns morphing customization. This file renders the morph.

## 7. Interaction Models

Anchor: `ui.interaction-models`

### 7.1 Definition

An `InteractionModel` is a presentation lens over the running experience — the degree and shape of user involvement the UI presents — realizing `core.interaction-shapes` (File 01 §2.2). It is a presentation choice, not a backend primitive, not a stored field, and not an autonomy control.

### 7.2 The Lens Set

The canonical closed-plus-`Custom` `InteractionModel` set:

- `ConversationOnly` — the user stays in the conversation view; the runtime uses surfaces, tools, and subsystems internally without presenting them as focus (`intent.presentation`, File 02 §8.2)
- `InlineAssist` — assistance overlaid on a non-conversation surface (suggestions, ghost completions, inline edits) without leaving that surface
- `Sidecar` — a work or artifact surface presented alongside the conversation, receiving the agent's edits and the user's review in place (the canvas/side-document shape)
- `Paired` — a hands-on shared workspace where the user and the agent work the same surface, with steering and takeover always available
- `OrchestrationDesk` — a multi-agent or multi-run control view presenting parallel activity, comparison, and steering across runs (`intent.parallel-work`, File 02 §7)

`InteractionModel` is closed-canonical-plus-`Custom { namespace, name }`. It is a UX lens varied freely by the user and the UI; it is never coupled to surface or model identity (`core.explicit-rejections`, File 01 §8), never stored as a backend field, and never a `SurfaceContract` or `ControlRail` field (`worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17).

### 7.3 The Deleted Autonomy Fields and What the UI Renders Instead

The presentation layer carries no participation-level, autonomy-mode, persona, agent-mode, plan-versus-build-mode, or phase field, in any form, at any layer. This is the unanimous, most-evolved position across the canon (`core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `world.surface-state`, File 18 §5.5; `worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17; `settings.explicit-rejections`, File 15 §20). The UI renders the *consequences* the deleted fields once described:

- **autonomy** is rendered as the approval posture the policy layer resolves — the effective tier indicator on a control (`policy.effective-tier-resolution`, File 06 §4), the pending approvals the policy layer raises (§12), and the active leases — not as a per-surface or per-rail dial. A "skip approvals" or "auto-approve" affordance the UI presents is a control over the `approval-posture preset` and `agent.unrestricted_mode` of `policy.settings-resolution-for-policy` (File 06 §16.3), rendered as a policy setting, never a presentation-layer autonomy field.
- **progressive disclosure** — the simple-to-power spectrum — is rendered as which panels, regions, and `ViewPreset` are open (§4, §5, §6), not as a mode. The default presentation is clean and minimal; depth is reachable by opening more regions, switching to a richer view preset, and expanding inspectors (`core.product-thesis`, File 01 §1; `core.invariants`, File 01 §7.9).
- **interaction shape** is rendered as the active `InteractionModel` lens (§7.2), varied freely.

There is no participation-level change event because there is no participation level to change (`world.state-change-events-reactivity`, File 18 §12; File 25 §18.1; File 26 §19.1). The agent adapts to what is asked and to the live `SurfaceState`, not to a declared mode.

### 7.4 Boundary

This section owns the interaction-model lens and the rendering of the deleted-field consequences. File 06 owns the permission tiers, leases, and approval-posture preset that provide autonomy; File 18 owns the `UiMode` and live state that provide progressive disclosure; Files 25 and 26 fix the deletion at the surface and rail layers. This file fixes that the presentation layer carries no autonomy field.

## 8. Conversation and Transcript Presentation

Anchor: `ui.conversation-presentation`

### 8.1 Definition

Conversation presentation is the rendering of the conversation as a transcript view and an input rail. The transcript is a projection of the block pool; the input rail is the Conversation control rail's surface. This section owns the rendering; File 02 owns the conversation model, File 26 §5 owns the rail resolution.

### 8.2 Transcript Rendering

- The transcript is one projection of the block pool over the active version's materialized view (`block.cross-surface-interoperability`, File 08 §12; `cross-cutting/blocks.md` realized; `version.consequences-for-later-specs`, File 11 §24); the context inspector and the execution views are other projections of the same blocks. The transcript renders the two transcript content shapes `intent.message` (File 02 §3.3) fixes: `Message`s (durable, addressable, retryable, editable, branchable anchors) and `Event`s (live coordination markers — streaming partials, tool-call activity, hook output, parallel-activity summaries, status timelines, dialog requests) projected into or alongside the transcript. Each block renders through the `RendererRegistry` (§3.3); a composed response block renders its children in version order.
- The transcript applies a collapse-and-grouping pipeline of pure functions before rendering: it normalizes, collapses low-stakes and repeated activity (read/search/list groups, background work, hook sequences, consolidations) into expandable summary units with stable derived identities so keys do not remount on append, groups by natural unit, and reorders for the compaction boundary. A derived presentation identity is computed from canonical input references using `CanonicalEncoding`: source block, version, event, or invocation ids; ordered child references for aggregates; the transform id; and the relevant presentation-policy version. It is a deterministic rendering handle for selection, collapse state, and replay alignment, not a new durable content identity. Which kinds collapse is a settings dimension and is extensible; the pipeline never discards a block (the underlying blocks remain individually reachable). Internal blocks that a producer marks not-visible in the transcript (a non-display execution node) render in the inspector and execution views, not the transcript scroll; whether a block kind may anchor a transcript message is `block.kind-catalogue` (File 08 §3.4)'s `transcript_anchorable`, and the transcript projection filters non-anchorable and non-display blocks out of the scroll.
- Inline capability-call rendering presents each invocation through a collapsible unit carrying an icon, a title and subtitle, a status (`pending`/`running`/`complete`/`error`), and an expandable result, driven by the renderer registered for the capability's output kind; running state is indicated by a non-spinner shimmer or equivalent live indicator and by the activity-state projection (§8.3). The rendering of an invocation is the rendering of a `Block` and its `CapabilityInvocation` facts (Files 05, 08, 09); the UI computes no result.
- Message actions — retry, edit, branch, fork, delete (soft by default, with in-session restore), pin, copy (with format and metadata), quote-back, and bulk operations — render the operations `intent.message` (File 02 §3.1) and `run.retry-reroute-branch` (File 04 §19) define and resolve through the rail like any gesture (§11). Parallel and sibling responses render with a variant indicator and navigation between siblings (the version graph's branches, File 11); the transcript renders no parallel history store of its own.
- Message metadata (model, provider, stop reason, token counts, timing, cost estimate) renders as a derived projection (`intent.message` File 02 §3.3; the metadata is computed on demand and cached, not stored on the block, `conversation/02-message-operations.md` realized); the UI renders a compact and an expandable form and computes no token count or cost itself.

### 8.3 Conversation Activity State

The shell renders `intent.conversation-state` (File 02 §2.3)'s coarse activity state — `streaming`, `processing`, `awaiting_user`, `idle` — as a projection over the conversation's active runs, with the first-matching-state priority that section fixes, plus the orthogonal `compacting` indicator and any later orthogonal indicators. A single run blocked on user input while another streams leaves the conversation `streaming` and surfaces the blocked condition on that run's own element (File 02 §2.3). The UI renders this projection; it does not collapse conversation state into per-run execution state, and it assumes no single active stream per conversation (`intent.explicit-rejections`, File 02 §9).

### 8.4 The Input Composer

The Conversation rail's input composer (`controlrail.conversation-rail`, File 26 §5) renders: multi-line composition, mention and reference insertion, attachment and paste handling (a large paste presents as a reference token with the content held aside and expanded on submit, never ballooning the composer), inline slash-token and mention type-ahead, the pre-dispatch transformation choices (duplicate-overlap handling presented as a fast, non-destructive, reversible, send-scoped choice per `context.duplicate-overlap-handling`, File 13 §8 and `kuzeys-context-duplicate-prompt-handling-addendum.md`), the queue-versus-interrupt affordance for mid-execution input (`intent.intent-thread`, File 02 §5.5; `run.retry-reroute-branch`, File 04 §19), and the active `UiMode` indicator. Paste, drag/drop, file attachment, and external selection import are gestures that create governed input references or capability proposals; files and external objects are not read into model context merely because they were dropped, but are registered as references, sensitivity-scanned, and included only through the normal context and capability paths. The composer renders the rail; it owns no submission logic, applies no transformation of its own, and a presented auto-continue countdown is a configurable convenience, never a correctness condition (`core.event-first-by-default`, File 01 §7.15).

### 8.5 Boundary

This section owns transcript and composer rendering. File 02 owns conversation, message, activity state, and the submission lifecycle; File 26 §5 owns the conversation rail; File 08/11 own the blocks and version graph projected; File 13 owns duplicate-overlap detection. This file renders them.

## 9. Rendering Substrate Primitives into Views

Anchor: `ui.substrate-rendering`

### 9.1 Definition

This section fixes how the typed substrate primitives — blocks, artifacts, the evidence and provenance entities, observations, and version history — render into views through the `RendererRegistry` (§3.3).

### 9.2 Block Rendering

Each `Block` renders through its registered renderer keyed by `BlockKind` (§3.3). A renderer presents the block's content and its derived view-state (lifecycle `Raw`/`Masked`/`Dropped`/`Recovered`, pin state, sensitivity) as projections (`block.block-lifecycle-non-destructive-edits`, File 08 §6.1; `version.consequences-for-later-specs`, File 11); a masked block renders its description, not its content. External-content blocks render a reference and the description, never pulling the blob into the view unless the user opens it. A `Memory`-sourced block renders its content as natural prose in the transcript and does not gratuitously frame it as memory retrieval; memory attribution is allowed and sometimes required — when the user asks what is remembered or why an answer was personalized, when a memory is being edited, deleted, or resolved, when confidence or freshness is uncertain, or when policy or the UI requires inspectability — and the inspector always exposes which memories materially influenced an answer (`memory.natural-use-inspectability`, File 14 §13). This transcript-prose rule is a renderer-level constraint, never a suppression of memory inspectability.

### 9.3 Artifact Rendering

- An `Artifact` (File 09 §3) renders through one of two pipelines, sharing one set of display modes (`cross-cutting/artifacts.md` realized): the **interactive-artifact runtime** for executable, interactive content, and **type-specific renderers** for documents, tables, diffs, images, media, and structured data. The pipeline is selected by the artifact's kind and media type through the `RendererRegistry`; the mapping is a registry table, extensible by registration.
- The three display modes are uniform across both pipelines: **inline** (a compact card with title, preview, and expand control in the transcript), **side panel** (a resizable region alongside the conversation, with multiple artifacts navigable within it), and **fullscreen** (the artifact fills the focus region with a back control). The user changes modes the same way for any artifact. Artifact and file edits render live as new versions commit (File 11); switching versions re-renders the artifact at the chosen version.
- The interactive-artifact runtime renders the artifact inside the one `Sandbox` contract (File 23) at a least-authority origin, with a restricted host bridge: the runtime may read and write its own artifact, emit a `Custom { namespace: "artifact.runtime", name, payload }` event, and request its own state be persisted (with consent), and has no other access — no network, no other files, no block store, no agent, no secrets — unless the user explicitly grants it (`security.egress-governance`, File 22 §11; File 23). Runtime events carry `artifact_id` as an envelope cross-reference key, payload field, or source identity; they are sensitivity-defaulted, carry no authority, are never read as instruction, cannot impersonate system events, and cannot trigger security-category hooks (`security.untrusted-content`, File 22 §12; File 10 §8.3). Persistent interactive-artifact state requires explicit user consent and is stored as substrate, not a private UI store. The runtime is a confined renderer and a consumer of the sandbox contract, not a parallel execution architecture (`sandbox.consequences-for-later-specs`, File 23 §21).

### 9.4 Evidence, Claim, Citation, Observation, and Provenance Rendering

The entity layer renders through the `artifact.per-surface-projections` (File 09 §17.2) lenses: claims render as assertions with confidence and status; evidence and citations render as linked support with source span and trust; observations render through their viewers (a captured page, an accessibility-tree overlay, a screenshot series, a machine snapshot, a database result); provenance renders as the derived lineage view (File 09 §15) — why an output exists, what supports it, what it derives from. Validation and critique render as badges and panels deriving the artifact's validation and review state (File 09 §14). The UI renders these as projections; it derives no confidence, status, or lineage of its own.

### 9.5 Version History, Comparison, and Forensic Reconstruction

History, comparison, and undo affordances render as projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24): a version timeline (a linear list and a branch-tree view, switchable as a rendering toggle), per-version operation summaries and diffs, the comparison board for parallel branches, runs, or agents, the read-only state-visualization overlay ("what the state was at this version"), and the forensic reconstruction ("what the model saw at this point," File 11's replay surface). Undo, redo, restore, revert, branch, and switch render the version-graph operations Files 04 and 11 define; the UI introduces no parallel checkpoint, snapshot, or undo store, and renders no per-tool-call version (`version.explicit-rejections`, File 11 §23).

### 9.6 Boundary

This section owns substrate rendering. Files 08, 09, 11 own the blocks, entities, and version graph; File 23 owns the sandbox the interactive runtime runs in; File 22 owns the secret and untrusted-content rules; File 38 owns widget renderers and themes. This file renders them through the one registry.

## 10. Streaming and Live Presentation

Anchor: `ui.streaming-presentation`

### 10.1 Definition

Streaming presentation is the rendering of live substrate change as it happens: the event stream, the streamed partials, and the transition from partial to committed state. This section owns the rendering and its performance contract; File 10 owns the events and the partial-to-committed boundary.

### 10.2 Rule

- The presentation layer renders the live event stream (`ledger.event-stream`, File 10 §5) reactively and event-first: a view subscribes to the events scoped to its concern, demultiplexes by the envelope's identifiers (`ledger.event-envelope`, File 10 §5.2 — conversation, run, step, node, and where present worktree and backend identifiers), and re-renders on receipt. It never polls for live state. Reconnection after a transport interruption rebuilds the affected views from the durable substrate and execution ledger, resumes subscription from the latest available sequence, and re-syncs stale subscriptions against the substrate. If transient partial chunks were missed and cannot be reconstructed, the renderer shows a typed stream-gap presentation marker until committed blocks or final results replace the partial view. The marker is presentation state, not a durable block unless the event or execution system explicitly records it.
- Streaming renders typed partials, not only token text (`codex_recommendations.md` §10.2; `ledger.streaming-live-partials`, File 10 §12): text deltas, reasoning deltas (rendered as a distinct, collapsible region, default-collapsed), plan deltas, task-state deltas, artifact and diff previews, validation results, and observation snapshots each render through the renderer for their kind. A reasoning or thinking partial is presentation that the user may expand; it is rendered distinctly from the response and is never asserted as the answer.
- The partial-to-committed transition is rendered as a single continuous view: the streamed partial renders incrementally as deltas arrive, and on the committed-block boundary (`ledger.streaming-live-partials`, File 10 §12) the view transitions the same element to the committed block without remount or flicker. The UI treats the durable committed block as the source of truth and the partials as the live projection that converges to it; it never persists a partial as truth.
- High-frequency rendering is throttled and aggregated for performance without losing data: visual scroll is decoupled from re-render (high-frequency scroll updates the view directly; re-render is quantized to coarse bins), long transcripts and lists are virtualized (only the visible window plus an overscan is mounted, with a stable list origin and clamped mount expansion so a jump to a distant entry never flashes blank), jump-to-item resolves by stable item identity rather than pixel offset, text streams render at a paced, word-boundary-snapping cadence rather than per-token, and high-frequency event categories are coalesced for display per the aggregation policy (`ledger.streaming-live-partials`, File 10 §12). These are rendering-performance requirements, not data policy; no rendered content is dropped, only its render cadence is bounded. Hidden or detached views suspend expensive render loops while preserving durable subscription and replay or sequence position, so re-showing the view re-syncs against the substrate without a gap.

### 10.3 Sticky Scroll and Auto-Follow

The transcript and live views auto-follow the latest content while the user is at the bottom, and stop auto-following when the user scrolls away, re-engaging when the user returns to the bottom band. Auto-follow distinguishes user-initiated scroll from renderer-initiated auto-scroll: a renderer auto-scroll never registers as a user action, so an arriving message never yanks the user away from content they scrolled up to read (`ui/14-3-streaming-ui.md`, `claude-code-frontend-addendum-part2.md` realized). Text selection pauses auto-follow.

### 10.4 Parallel Presentation

Parallel activity renders readably and never as one forced flat stream (`intent.presentation`, File 02 §8.4). The shell renders the parallel shapes `intent.parallel-work` (File 02 §7) allows — concurrent runs, sibling responses, fan-out, multi-agent transcripts, comparison branches — through grouped activity summaries, side-by-side or stacked panes (independently scrollable), a comparison board, a classroom or debate view, and an orchestration board, each a projection over the runs and blocks involved. Background activity in a non-focused surface or run renders as a badge or summary with the current operation and progress, and an entry point to focus it; a non-focused parallel activity never blocks the focus surface.

### 10.5 Boundary

This section owns streaming and parallel presentation. File 10 owns the events, the envelope, the partial-to-committed boundary, and the aggregation policy; File 02 owns the parallel-work shapes and activity state; File 16/17 own the model and usage facts. This file renders them.

## 11. Control-Rail Presentation

Anchor: `ui.rail-presentation`

### 11.1 Definition

Control-rail presentation is the rendering of the control rails' surfaces and the routing of gestures into them. The presentation layer renders each rail; File 26 owns the rail primitive, the resolution contract, the keymap, the slash grammar, the voice session, and the steering contract.

### 11.2 Rule

- **Command palette.** The shell renders the command palette as an overlay (never a separate window) that searches the available-capability list (`world.state-aware-capability-availability`, File 18 §9) filtered to the palette lens (`surface.presentation-in-user-facing-surfaces`, File 07 §12.1), ranks by match quality, recency, and frequency as a presentation convenience, presents each entry's resolved effective-tier and availability indicators (read from File 06, never recomputed), and elicits missing required arguments before dispatch (§12). A quick-open variant searches a registered catalog (files, recent entities, artifacts) and resolves to an open or reveal invocation. The palette renders the `controlrail.command-rail` (File 26 §6) surface; it composes no visibility and decides no authority.
- **Menus, toolbars, context menus, and selection actions.** Menu items, toolbar buttons, context-menu entries, and selection-scoped floating actions render as presentations of capabilities (`worksurface.actions-declaration`, File 25 §6.4; `controlrail.command-rail`, File 26 §6.4), filtered to the available-capability list, current `Selection`, policy state, surface binding, and user settings, and show the same policy indicators as the palette. Copy, quote, explain, ask, cite, export, save-to-memory, and equivalent actions appear only when their capabilities are available and allowed. Selection actions are reachable by keyboard and assistive technology. Renderer-provided copy and export projections inherit sensitivity, provenance, and egress governance; raw secret or restricted content never bypasses File 22 filtering. A native menu or tray item bridges to the same capability invocation.
- **Keybinding capture and editor.** The shell captures keyboard input and resolves it through the keymap (`controlrail.keybinding-keymap`, File 26 §7): a keybinding-context contributes its context to the active context stack as the surface, panel, or dialog that owns it becomes active, and the shell renders the keybinding editor (rebinding, conflict surfacing, unbind, platform-validity diagnostics) over File 26's keymap model. The resolver is File 26's; the capture, the context-stack contribution from live presentation and focus, and the editor presentation are this file's.
- **Voice and handsfree.** The shell renders the voice rail's session (`controlrail.voice-rail`, File 26 §9): the recording indicator, the live transcription preview, the confidence and disambiguation surface, the spoken-output and caption presentation, and the confirmation step, over the capture, transcription, and consent File 19 owns and the session File 26 owns. The shell renders the `Handsfree` `UiMode` and a companion-capture window (§4.5) where configured. The UI renders the session; it owns no capture, transcription, or intent resolution.
- **Steering affordances.** The shell renders stop, cancel, pause, resume, interject, takeover, and barge-in as affordances resolving to `Steer` outcomes (`controlrail.steering-rail`, File 26 §10): the cancellation targets (run, child-run tree, specific child run, tool call, sandbox/process) with the default and expanded options, the cooperative-then-forceful state, and the queue-versus-interrupt choice for mid-execution input. A presented countdown is a configurable presentation of File 04's safety guard, never a correctness condition. The UI renders the affordance; File 04 carries out the intervention.
- **Slash commands, mentions, and attachments.** The composer renders the slash-command and mention type-ahead and the attachment surface (`controlrail.slash-command-rail`, File 26 §8; §8.4), resolving through the rail. Custom-command definitions render with source attribution and precedence; a prompt-template command's contributed text renders as attributed content, never as a hidden instruction.

### 11.3 Available-Action Enable/Disable

The shell renders a control's availability from the serialized availability predicate the action registry exposes (`cross-cutting/actions.md` realized; `world.state-aware-capability-availability`, File 18 §9), so a control enables or disables against the current `SurfaceState` and `UiMode` without round-tripping per state change. An unavailable control renders a typed unavailability indicator (greyed with a reason), never a control that fails on invocation. Availability re-renders event-first on the recompute event (File 18 §12); the shell does not poll.

### 11.4 Boundary

This section owns rail rendering and the available-action enable/disable contract. File 26 owns the rails, the keymap, the slash grammar, the voice session, and the steering contract; File 07 owns the lens; File 18 owns availability; File 19 owns capture; File 05/06 own the capability and its policy. This file renders the rails.

## 12. Dialog, Elicitation, and Notification Presentation

Anchor: `ui.dialog-elicitation-notification`

### 12.1 Definition

This section fixes how the system's requests for typed user input — approvals, clarifications, choices, corrections, interventions, credential and confirmation prompts — and its transient notifications render, and how the UI arbitrates which request currently holds focus.

### 12.2 The Focused-Dialog Selector

The pending-request set and its resolution are owned by the policy and elicitation systems (Files 06 and 26) and shared through the event bus. The focused-dialog selector is per renderer root: the shell, each secondary window, and the headless or command-line client each compute presentation focus over the same shared pending set. Answering a request in any compatible client emits the one typed response and resolves the request for all clients, so a request is never double-answered and never left stale in another renderer root. The selector replaces per-request visibility flags with a single computed focus (`unit13-ui.md` D13.5; `unit15-ux-distribution-files-glossary.md` D15.UX.1 realized). It uses a deterministic priority tuple: blocking/security class, capability or policy severity, user-visible urgency metadata, dependency relationship to the active run, then enqueue sequence. Enqueue sequence is a logical sequence number, not a wall-clock correctness condition. Pending lower-priority dialogs remain visible in a queue, badge, or panel; dialogs revalidate before presentation and before action. Security, approval, credential, payment, destructive, and typed-confirmation dialogs never auto-approve, auto-deny, or silently expire because of UI timing.

### 12.3 Rendering the Contracts

- The presentation layer renders the `policy.approval-ui-surface-contract` (File 06 §13) data contract verbatim — `ApprovalRequest`, `LeaseOption`, `ApprovalResponse`, `BatchApprovalRequest`, `BatchApprovalResponse`, and `ContradictionResolutionRequest` — and the `controlrail.elicitation` (File 26 §13) contract — the `Elicitation` with its closed-canonical-plus-`Custom` kind set (approval, clarification, choice, correction, intervention); the credential, payment, confirmation, file-picker, and multi-step-wizard flows the sources name are rendering cases of these kinds or registered `Custom` kinds, not additional baseline members. It never invents a parallel approval or elicitation data shape (`policy.consequences-for-later-specs`, File 06 §18; the File 06 §13.6 rule that the policy layer emits typed events and the UI renders and responds). The approval and elicitation dialogs are baseline-only kinds: they render through the canonical baseline renderer only, and no surface, rail, or plugin contribution may override or shadow them (§3.3).
- An approval renders the capability identity, the resolved arguments (with declared-sensitivity redactions applied), the stated reason, the resolved tier and floor, the touched resources, the available lease options, and any contradictions; it offers the typed response options the contract defines (allow once and the lease-scope grants, deny once and the deny-scope grants, with the lease-narrowing affordance) and the typed-confirmation entry where required. A batched approval renders the constituent requests together as a non-modal surface that leaves the rest of the UI navigable, with per-item resolution and a batch-level accept or deny (`policy.batched-approval-flow`, File 06 §5.5; `unit04-routing-agents-prompt.md` D4.5). A change-review approval renders the before/after diff and per-change accept, reject, or modify where the producing surface supplies the diff.
- An elicitation renders its kind through the appropriate surface (a choice as tappable options, a credential through the platform-native masked field, a correction inline, an intervention as a steering handoff) and is answerable through any compatible rail; the response flows back through the one typed response channel and is linked to the request identity, never issued as a new unrelated command (`controlrail.elicitation`, File 26 §13.2). A persistent request survives restart and re-renders.
- The response to any request is dispatched as the typed response event the contract defines; the presentation layer enforces no policy and grants no authority — it renders the request and returns the user's typed choice (File 06 §13.6).

### 12.4 Notifications, Toasts, and Badges

Transient notifications, toasts, and badges render as projections over the event stream (§10): a badge on a region or surface reflects pending or unread activity, a toast surfaces a completed background task or a recoverable condition, and a notification may carry the provenance context needed for a context-aware follow-up (`omi-compressed.md` realized). Notification payloads are sensitivity-filtered summaries. External OS notifications, lock-screen notifications, and previews must not expose secret, restricted, or policy-hidden content. A notification with an action renders the action as a capability invocation through the rail and revalidates availability, policy, and current substrate state when invoked. Notification delivery to external channels and the desktop notification surface render the events the owning specs emit; this file owns the in-shell notification region (§4.2) and the rendering, not the dispatch.

### 12.5 Boundary

This section owns the dialog/elicitation/notification rendering and the focus selector. File 06 owns the approval contract and the policy decision; File 26 owns the elicitation contract; File 04 owns the intervention; the event-owning specs own the notification events. This file renders the requests and returns typed responses, inventing no parallel shape.

## 13. Inspector and Management-Surface Presentation

Anchor: `ui.inspector-presentation`

### 13.1 Definition

A management surface is a user-facing presentation of a substrate service's data and capabilities — an inspector, a browser, a dashboard, or a console — rendered into the inspector dock or a secondary window. This section owns the rendering; the substrate-service specs own the content, and File 25 §14 classifies these as management surfaces, not work surfaces.

### 13.2 Rule

- The shell renders the substrate-service management surfaces as projections over their services (`worksurface.management-surfaces`, File 25 §14): the context inspector, the source and knowledge browsers, the memory browser, the world-model inspector, the settings panel, the capability-registry and source and connector managers, the storage-accounting view, and the automation and workflow dashboards. Each renders its service's state through the `RendererRegistry` and self-registers its panel state (§3, §6); none is a focus work surface, none registers a `SurfaceContract`, and opening one gives the host run no new primary surface.
- The **context inspector** renders the assembled context as an explainable projection (`codex_recommendations.md` §10.9; `ui/context-management.md` realized): the block tree with per-block token counts, pin and lock state, and content previews; the budget bar with per-category breakdown and the live dry-run preview (`context.consequences-for-later-specs`, File 13 §22); and, per included or omitted element, why it is in or out, what replaced it if compacted, what it supports, and whether it is conversation, retrieved content, memory, or evidence. The user's block operations (pin, mask, drop, recover, reorder, edit, delete) render the operation vocabulary Files 08 and 11 define and resolve through the rail; the inspector is the surface for those user invocations (`cross-cutting/blocks.md` realized).
- The **observability surface** renders the execution and quality projections (`codex_recommendations.md` §8.12; `run.presentation`, File 04 §25): traces and execution timelines, validations, retrieval inspections, prompt and context reconstructions (the forensic "what the model saw," §9.5), policy decisions, run comparisons, evaluation results, and usage/cost/latency metrics, each a projection over the ledger and version graph. The **debug surface** renders the live event log (a bounded ring buffer with filtering, search, and high-frequency aggregation), the performance monitor, and the debug toggles (`ui/14-5-debug-and-performance.md` realized); it is reachable behind a developer affordance, renders with bounded overhead, and adds zero overhead when inactive. Debug and observability surfaces render filtered projections by default; raw payload inspection, copy, export, or sharing reuses File 22 egress governance, File 06 policy, and the relevant sensitivity labels. Enabling deeper capture is an explicit state change with visible scope and retention.
- A management surface renders only what its service exposes and computes nothing of its own; it honors sensitivity (a `Secret`-classified value renders masked, File 22) and emits the user's operations as capability invocations.

### 13.3 Boundary

This section owns management-surface rendering. The substrate-service specs (Files 06, 07, 12, 13, 14, 18, 20, 21, 33, 34, 35, 36, 40, and 41) own the content; File 25 §14 classifies them; File 11 owns the version-graph replay the reconstruction view renders; Files 40 and 41 own the data the observability surface renders. This file renders them.

## 14. Accessibility

Anchor: `ui.accessibility`

### 14.1 Definition

Accessibility is a first-class, dual-purpose invariant of the presentation layer: the UI must be operable and perceivable by human assistive technology and structurally legible to the agent and the world model. It is not an add-on (`codex_recommendations.md` §10.6; `ui/accessibility.md` realized).

### 14.2 Rule

- Every rendered panel, control, and affordance exposes the structural semantics `worksurface.explicit-rejections` (File 25 §20) requires — a stable semantic role, an accessible label and description, the interaction kinds it supports, focus behavior, and its state relationships — sufficient for the world model and control rails (so the agent can perceive and operate the UI through structure, not screenshots) and for assistive technology (so a screen reader, keyboard, or voice control can operate it). A control that cannot be represented structurally is invalid (the structural-invisibility rejection, File 25 §20; §6.2). This dual-purpose semantic layer is the same surface the self-registration contract (File 18 §8.1) and the accessibility tree consume.
- The baseline standard is WCAG 2.1 Level AA: text-alternative for non-text content; minimum contrast ratios with no color-only information (status carries an icon and text, not color alone); full keyboard operability with a logical focus order, a visible focus indicator, and no keyboard trap; pointer targets meeting the minimum size; readable, actionable language with input assistance and labeled fields; and semantic structure with correct roles. Dynamic and live regions announce updates appropriately; modals trap focus, restore it on close, and are announced. The active accessibility conformance profile may target newer WCAG AA versions, Section 508, ATAG, or equivalent jurisdictional or authoring profiles through settings and validation; it does not create a parallel accessibility architecture.
- The presentation layer honors the user's accessibility preferences as settings (§22): a reduced-motion preference suppresses non-essential animation (§6.2), a high-contrast preference selects a high-contrast presentation, a font-scale and density preference reflows accordingly, and reading-level and dyslexia-support preferences (carried in the learner persona where present, `unit11d-teacher.md`) adapt presentation. Read-aloud and voice operation are accessibility paths: every operable control is reachable through the keyboard, the command palette, and the voice rail, and voice maps an utterance to an available capability (`controlrail.voice-rail`, File 26 §9; §11.2).
- Accessibility is verified, not assumed: a conformant presentation passes automated checks and is operable end to end by keyboard and by screen reader. The accessibility contract applies to every surface, panel, dialog, and state, including loading, empty, and error states (§17), virtualized lists, drag/drop alternatives, selection action surfaces, focus restoration, and screen-reader semantics.

### 14.3 Boundary

This section owns the accessibility contract for the presentation layer. File 18 owns the self-registration the structural layer feeds; File 26 §9 owns the voice rail accessibility composes; File 19 owns capture; the per-surface specs declare surface-specific accessibility affordances (a surface's accessibility concerns are this contract applied to its panels). This file fixes that accessibility is a rendering invariant.

## 15. Internationalization Presentation

Anchor: `ui.i18n`

### 15.1 Rule

- Every user-facing string the presentation layer renders is a localizable key, with no exceptions: UI copy, control labels and descriptions, error and notification messages, tooltips, accessible labels, and placeholder text (`atlas3-core/CONSTRAINTS.md` §2 realized; `cross-cutting/i18n.md`). The discipline extends to the strings the substrate exposes for rendering: capability display names, policy explanations, and provenance and validation strings render through the same localization discipline (`codex_recommendations.md` §10.7; `capability.display-fields`, File 05 §3.2's localizable-descriptor rule). A rendered string that is not a key, or a hardcoded user-facing literal in presentation logic, is invalid.
- The active locale is resolved from the settings system (the `ui.language` dimension, File 15), not from a renderer-private store; the renderer reads the locale reactively and re-renders on change. Locale resolution supports a fallback chain to a default locale, and a missing key renders a visible diagnostic in development rather than a blank. The presentation layer renders right-to-left and locale-aware formatting (dates, numbers, week boundaries) per the resolved locale. The headless and command-line clients share the same keys (§16).
- Localization is part of the rendering contract, not a per-surface concern: a surface, rail, or plugin that contributes a renderer or a control contributes its strings as keys, and translation completeness is verifiable.

### 15.2 Boundary

This section owns the internationalization rendering contract. File 15 owns the language setting and resolution; File 05 owns the localizable display-field descriptors; the contributing specs own their strings as keys. This file renders them localized.

## 16. The Renderer-to-Backend Boundary and Frontend Architecture

Anchor: `ui.renderer-boundary`

### 16.1 Definition

The renderer-to-backend boundary is the contract between the presentation layer and the service layer: the renderer is an adapter that calls the service layer and renders its outputs, holding no business logic and no durable state. This section fixes the boundary and the provider-invariant frontend architecture.

### 16.2 Rule — The UI Is an Adapter

- Business logic, durable state, and the source of truth live in the backend service layer; the renderer and the command handlers are adapters (`core.invariants`, File 01 §7.7; `core.explicit-rejections`, File 01 §8; `atlas3-core/CONSTRAINTS.md` §1; `cross-cutting/service-layer.md` realized). A presentation view computes presentation values only (§3.2); it never owns a capability's effect, a policy decision, a route, a model selection, an availability evaluation, or a substrate mutation. The same service layer serves the graphical shell and the headless and command-line clients, so the service layer is rendering-agnostic and the renderer is one of several adapters over it.
- The renderer communicates with the service layer over typed inter-process communication: a request-response invocation path for commands and queries, and a streaming channel for live events (`foundations/stack.md`; `core.stack-commitments`, File 01 §9 — "typed IPC"). The renderer opens no in-renderer network server and uses no network-style transport to reach its own backend. The boundary is statically typed: the command and event types are generated from the backend contract so a backend change that breaks the contract breaks the build, not the runtime.

### 16.3 Typed Errors at the Boundary

Cross-boundary failures are typed (`core.typed-errors`, File 01 §6.9; `cross-cutting/errors.md`) and drive presentation behavior, not only display: a retryable failure renders a retry affordance, a rate-limited failure renders a countdown and retry, a validation failure highlights the field with a corrective message, and an unrecoverable failure renders an actionable explanation. A failure is never rendered as a raw internal error string to the user; it renders through the typed-error renderer with a localized, actionable message (§15).

### 16.4 Ephemeral View State and No Private Store

The presentation layer holds only ephemeral view state — the live `SurfaceState` (open panels, focus, selection, in-progress composition, scroll position; File 18 §5) reconstructed from self-registration — plus client-only presentation preferences (the active theme reference, the active layout reference, window position and size, density and font scale) persisted through the settings system as syncable user preferences or device-local values per their declared locality (§19; File 15). The presentation layer maintains no private durable store, no parallel persistence, and no source-of-truth state; its loss is a rebuild (§3.2, `core.projection`, File 01 §6.11). Cross-window state is shared through the event bus and settings, never shared in-memory state (§4.5).

### 16.5 Semantic-Token Discipline

Every visual property a renderer applies — color, radius, shadow, font, spacing, animation timing — comes from a semantic token, never a raw value (`customize.design-tokens`, File 38 §4; `cross-cutting/theming.md` realized). This file owns the discipline (renderers consume only tokens); File 38 owns the token system and the themes that resolve the tokens. The discipline makes the presentation fully themeable and high-contrast-capable without renderer changes.

### 16.6 Performance Contract

The presentation layer meets interactive-responsiveness budgets: gesture-to-feedback is near-immediate, input latency is imperceptible, scrolling holds the display refresh rate, and streaming text renders smoothly (the concrete budgets are tested defaults and settings, not canonical constants; `ux-input/design-principles.md`, `codex_recommendations.md`). Performance is achieved through the projection, virtualization, scroll-decoupling, aggregation, paced-rendering, and off-screen-freeze techniques §10 requires, never by dropping substrate data.

### 16.7 Boundary

This section owns the renderer boundary, the typed-error contract, the ephemeral-state rule, the semantic-token discipline, and the performance contract. File 01 §9 fixes the stack commitments; File 15 owns settings persistence; File 38 owns the token system; File 43 owns packaging and platform-window mechanics. This file fixes that the renderer is an adapter.

## 17. UI States

Anchor: `ui.states`

### 17.1 Rule

- The presentation layer renders the full state space of every view, not only the populated state: a loading or skeleton state while a projection's source is resolving, an empty state that guides the user toward the next action, an error state rendered through the typed-error contract (§16.3), and a degraded or offline state when a capability, sidecar, connection, or provider is unavailable — rendered as a typed unavailability with the reason and a recovery path, never a silent failure or a broken view.
- First-run and onboarding render as presentation flows over substrate operations: a first-run flow that establishes the initial presentation (a profile or starting-point selection that applies a default `ViewPreset` and presentation preferences, §5.3), permission and capability setup surfaces (a setup card when a capability is unavailable for lack of a system permission, with the reason and the action, `unit10-gui-control.md`, `conversation/05-voice-input.md`), and migration or recovery surfaces where a substrate operation requires user input (a workspace-recovery dialog, `workspace.relocation-recovery`, File 24 §6; `unit15-ux-distribution-files-glossary.md` D15.F.4). Onboarding may render as a guided conversation rather than a separate wizard where appropriate. Each onboarding step is a capability invocation rendered as a step; the flow owns no durable state of its own.

### 17.2 Boundary

This section owns the UI state-space rendering. The owning specs own the underlying conditions (capability availability, connection state, permission state, workspace recovery); File 38 owns onboarding customization. This file renders the states.

## 18. World-Model, Perception, and State-Awareness Integration

Anchor: `ui.world-state-integration`

### 18.1 Rule

- The presentation layer is both the renderer of `SurfaceState` and the producer of it: every rendered panel self-registers its live state to the world model on mount, focus, selection, content change, and unmount (`world.observation-state-update`, File 18 §8.1), so the agent, the rails, and other views read the user's current context as structured data, never a screenshot (`world.chosen-model`, File 18 §1; `perception.tiered-sensing`, File 19 §5.4). A panel that fails to register its state is a blind spot the agent cannot use; registration is mandatory for every interactive panel.
- Atlas-owned windows and elements may be represented in accessibility, world-model, and substrate projections for inspection, assistive technology, and Atlas-native UI capabilities. They are not valid targets for desktop GUI Control. Actions that manage Atlas state must go through Atlas capabilities, control rails, approval policy, and settings, not through puppeting Atlas's own UI (`gui.action-execution`, File 31 §8.1).
- The presentation layer renders the available-action list the availability evaluator computes (`world.state-aware-capability-availability`, File 18 §9) and re-renders it event-first on recompute (§11.3); it maintains no private available-action store. It renders the world-model entities and observations through their viewers (§9.4) as projections; a surface that observes the unowned environment renders perception's observations (File 19), never a private observer.
- The presentation layer renders no interaction-shape, autonomy, participation, or execution-mode field in the world model, because none exists (`world.surface-state`, File 18 §5.5; §7.3). It renders `UiMode` as live interaction state, not an autonomy control.

### 18.2 Boundary

This section fixes the world-model and perception integration. File 18 owns the entities, the self-registration contract, the durability tiers, and the availability evaluator; File 19 owns capture and observations. This file renders them and feeds the self-registration.

## 19. Persistence, Locality, and Portability

Anchor: `ui.persistence-locality`

### 19.1 Rule

- The presentation layer persists no durable source-of-truth state. Its live state — open panels, focus, selection, in-progress composition, scroll position, the materialized presentation — is computed and rebuilt from self-registration and the substrate projections, never a durable fact (§3.2, §16.4; `world.persistence-contract`, File 18 §14.2). Its loss is a rebuild, never data loss (`core.projection`, File 01 §6.11).
- Client-only presentation preferences — the active theme reference, the active layout and view-preset references, window position and size, density and font scale, animation and reduced-motion preferences, and equivalent — persist through the settings system as settings/customization records (File 15, File 38), each declaring its locality (`settings.locality-sync-export`, File 15 §18): a saved layout and a default-presentation preference are syncable user preferences, while a device-bound presentation value (a platform-specific window placement) is device-local. The presentation layer introduces no private persistence path.
- The presentation layer persists no raw secret in any rendered, cached, exported, or shared state (`secret.backend-boundary`, File 22 §4), and honors the sensitivity classification of what it renders in screenshots and exports (`ledger.sensitivity-aware-persistence-retention`, File 10 §10). Every hash a presentation record relies on is computed over a declared `CanonicalEncoding`, never physical bytes (`core.canonical-hash`, File 01 §7.14); this file defines no new canonical hash.

### 19.2 Boundary

This section fixes the presentation layer's persistence and locality. File 15 owns the settings persistence and locality; File 20 owns storage; File 21 owns sync and portability; File 22 owns the secret boundary; File 38 owns the saved-customization records. This file owns no durable store.

## 20. The UI Capability Surface

Anchor: `ui.capability-surface`

### 20.1 Rule

- The presentation layer's user-facing operations are canonical capabilities in the one Capability Registry (`capability.declaration`, File 05 §3), declared as built-ins, tier-gated by policy (File 06), surfaced through tool-surface composition (File 07), and invoked through the shared pipeline (`run.call-pipeline`, File 04 §8.2). Presentation capabilities declare touched resources and effect by kind:
  - reading the shell composition, the rendered views, and the presentation state is `ReadOnly`
  - transient presentation operations — open, close, focus, arrange, split, collapse, detach a panel; switch the active surface or `ViewPreset`; toggle an inspector; set the interaction-model lens; open the palette or a management surface — are UI-state writes scoped to the conversation, workspace, or session, with the effective tier resolved from touched resources and policy
  - saving or deleting a user presentation preference (a layout, a default view preset, the interaction-model lens default, a density or theme reference) is a client-only presentation-preference write per scope, composed as a settings/customization write with File 15 and File 38, not duplicated
- Every presentation capability is the single source for all its invocation paths — palette, shortcut, voice, menu, agent tool, automation trigger, external protocol (`core.extension-planes`, File 01 §6.14); the presentation layer declares no out-of-band presentation operation. The agent invokes presentation capabilities the same way the user does — through the one capability system under policy — so an agent that arranges the UI for a task (opening a relevant panel, switching a view preset) does so through the same gated path, never through a private UI mutation. Custom presentation operations register through the proposal-first mechanism (File 05 §16.2) and never bypass policy.

### 20.2 Boundary

This section names the presentation capability families and their effect classes. File 05 owns the capability contract; File 06 owns tier resolution and approval; File 07 owns surfacing; File 04 owns execution; File 38 owns the customization capabilities that compose with these. This file declares the presentation capabilities as built-ins.

## 21. Events

Anchor: `ui.events`

### 21.1 Rule

- The presentation layer emits its own consequential presentation facts as `Custom { namespace: "ui", name, payload }` events (`ledger.custom-kind-registration`, File 10 §4.3) through the one event bus and ledger with the canonical envelope (`ledger.event-envelope`, File 10 §5.2): a shell-region or panel opened, closed, focused, or detached; a `ViewPreset` applied; an interaction-model lens changed; a management surface opened; a window opened or closed. Each declares its payload schema, cross-reference keys, default sensitivity, retention, and owner per File 10. Live surface-state changes (panel registration, focus, selection, mode) are owned by `world.state-change-events-reactivity` (File 18 §12) and emitted by the world model from the presentation layer's self-registration; this file consumes them and does not duplicate them. Surface-lifecycle and tool-surface events are Files 25 and 07's; rail-resolution events are File 26's; this file emits only its own presentation facts.
- A presentation event is live coordination; a consequential fact (a preference saved, a window opened) is committed to the durable record by the owning settings or registry path, never inferred from event observation (`core.durable-history-transient-coordination`, File 01 §7.3). High-frequency presentation events (scroll, cursor, key-down, partial composition) are transient by default and not durable unless diagnostics are explicitly enabled with a retention class and sensitivity label (§13.2). There is no participation-level or autonomy-mode event (§7.3).

### 21.2 Boundary

This section reserves the `ui` event namespace and declares presentation-fact events only. File 10 owns the envelope, delivery, sensitivity, and custom registration; Files 18, 25, 07, 26 own the events this file consumes. This file emits through the shared bus.

## 22. Settings

Anchor: `ui.settings`

### 22.1 Rule

- Presentation behavior is configurable through the one settings system (`core.settings-system`, File 01 §6.8; File 15); this file names the dimensions, the settings system owns the cascade and storage. Presentation settings are namespaced keys resolved through the standard cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); the presentation layer is not a durable settings scope, and per-presentation variation is namespaced keys plus profile layers, never a new scope.
- The canonical presentation settings dimensions include at least: the default and per-scope `ViewPreset` and default surface for a new conversation or workspace (composed with File 25's settings); the default layout and whether saved layouts apply (composed with File 38); supporting-region auto-reveal per region and per reveal trigger class, with badge-only always selectable; the density, font scale, and information-density preference; the default and active interaction-model lens, durably scope-pinned to Global, Workspace, or Conversation (`settings.scopes-profile-contexts-overlays`, File 15 §5.1) with any session-scoped lens riding the transient overlay; the reduced-motion preference and the animation-duration scale; the streaming render-pace and the high-frequency aggregation thresholds; the sticky-scroll re-engage band; the transcript-collapse and grouping defaults; the conversation-list grouping and unread behavior; the queue-versus-interrupt default and the duplicate-handling and auto-continue conveniences (composed with Files 02, 13, 26); notification, toast, and external-notification detail behavior; the active accessibility conformance profile; the debug-surface accessibility and retention controls (developer-only by default); and the active locale, theme reference, and high-contrast preference (composed with File 15 and File 38). Profiles carry per-profile presentation defaults (`settings.profiles`, File 15 §7).
- Each presentation setting declares its locality (`settings.locality-sync-export`, File 15 §18) — saved layouts, view-preset, density, and locale preferences are syncable user preferences; device-bound window placement is device-local — and its agent exposure (`policy.agent-exposure-policy-settings`, File 06 §16.4), so the agent cannot read or change security-sensitive presentation configuration without policy. No presentation behavior with meaningful variation is a hardcoded constant (`core.typed-configuration-failure`, File 01 §7.6; `settings.settings-over-constants`, File 15 §13).

### 22.2 Boundary

This section names the presentation settings dimensions and their layer. File 15 owns the settings object model, the cascade, locality, agent exposure, and profiles; Files 02, 06, 13, 25, 26, and 38 own the per-substrate settings the presentation composes with. This file names the presentation-relevant dimensions.

## 23. Explicit Rejections

Anchor: `ui.explicit-rejections`

The following are architecturally invalid for any later or per-surface spec:

- **Business logic in the renderer or command wrappers** — a presentation view computes presentation values only; policy, routing, model selection, availability evaluation, substrate mutation, and capability effects live in the service layer; the renderer and command handlers are adapters (§3, §16; `core.invariants`, File 01 §7.7; `core.explicit-rejections`, File 01 §8).
- **A private durable UI store or source-of-truth state** — every view is a projection rebuildable from the substrate; the presentation layer holds only ephemeral view state (the live `SurfaceState`) plus client-only preferences persisted through the settings system; no parallel persistence, no UI-owned durable fact (§3, §16.4, §19; `core.projection`, File 01 §6.11).
- **A participation-level, autonomy-mode, persona, agent-mode, plan-versus-build-mode, or phase field at any UI layer** — autonomy is the approval posture (permission tiers, leases, approval-posture preset) the policy layer resolves; progressive disclosure is which panels and view preset are open; interaction shape is a presentation lens; the UI renders the consequences, never a mode field (§7; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; File 25 §13; File 26 §17).
- **Conversation forced as the universal container or the mandatory primary pane** — conversation is an always-available control rail and an expand/collapse view; the focus surface is whatever the work needs (§4; `core.product-thesis`, File 01 §1; `intent.presentation`, File 02 §8; `worksurface.explicit-rejections`, File 25 §20).
- **A parallel renderer table, approval shape, dialog system, or available-action store** — there is one `RendererRegistry`, one approval and elicitation data contract rendered verbatim, one focused-dialog selector, and one availability evaluator; a surface or plugin contributes a renderer through the one registry and renders the one approval contract, never a parallel shape (§3, §11.3, §12; `policy.consequences-for-later-specs`, File 06 §18).
- **A view that polls a substrate on a timer for live state, or time-based correctness in presentation** — views are event-first; a periodic refresh is a flagged, configurable fallback only where a source emits no change events; auto-continue countdowns and animation timings are conveniences, never correctness conditions (§3.2, §10; `core.event-first-by-default`, File 01 §7.15).
- **A streamed partial persisted as truth, or a partial-to-committed transition that remounts or flickers** — the durable committed block is the source of truth and the partial is the live projection that converges to it; the transition is a single continuous view (§10.2; `ledger.streaming-live-partials`, File 10 §12).
- **An external deep link that executes consequential work** — external-origin navigation is reveal-only and `ReadOnly`; any consequential action encoded in a link must enter through the normal rail, capability, policy, and approval path (§4.4; File 26 §12).
- **An interactive artifact event treated as trusted, authoritative, instructional, or system-owned** — artifact-runtime events use the registered `artifact.runtime` namespace, carry the artifact identity as data, and cannot impersonate system events or trigger security-category hooks (§9.3; File 10 §8.3).
- **Parallel work forced into one flat stream, or a single-active-stream assumption** — parallel activity renders readably as grouped, side-by-side, board, or comparison projections; the conversation may have multiple concurrent streams (§10.4; `intent.presentation`, File 02 §8.4; `intent.explicit-rejections`, File 02 §9).
- **A visual-only panel or control that cannot be represented structurally** — every panel and control exposes the semantic role, label, interaction kind, and state relationships sufficient for the world model, the rails, and assistive technology; rendering may vary, structural invisibility is invalid (§6.2, §14; `worksurface.explicit-rejections`, File 25 §20).
- **A hardcoded user-facing string, a raw visual value bypassing semantic tokens, or a presentation behavior hardcoded instead of a setting** — every user-facing string is a localizable key, every visual property is a semantic token, and every meaningful presentation variation is a setting (§15, §16.5, §22; `atlas3-core/CONSTRAINTS.md` §2/§3; `settings.explicit-rejections`, File 15 §20).
- **An in-renderer network server or network-style transport to reach the backend** — the renderer reaches the service layer over typed inter-process communication only (§16.2; `foundations/stack.md`; `core.stack-commitments`, File 01 §9).
- **Raw secret material rendered, cached, exported, or shared, or untrusted rendered content treated as instruction** — the renderer honors the secret boundary and the no-authority-from-untrusted-content rule; rendered foreign content is content, never instruction (§3.2, §9, §19; `secret.backend-boundary`, File 22 §4; `security.untrusted-content`, File 22 §12).
- **A presentation-focus change treated as an execution reroute** — opening, focusing, or detaching a region or panel affects presentation and invocation context, but an active run's primary surface and execution context change only through File 03/File 04 reroute or explicit user override (§4.3; `worksurface.explicit-rejections`, File 25 §20).
- **A management surface treated as a focus work surface** — memory, context, knowledge, registry, settings, world-model, observability, and equivalent surfaces are presentations of always-on substrate services, not focus work surfaces; they register no `SurfaceContract` (§13; `worksurface.management-surfaces`, File 25 §14).
- **A widget, theme, design-token system, saved-layout flow, or plugin UI injection defined here** — those are File 38's; this file owns the shell, the layout container, the rendering contracts, the interaction models, and the semantic-token discipline they consume (§5.5; `worksurface.views-presets`, File 25 §7.6).

## 24. Consequences for Later Specs

Anchor: `ui.consequences-for-later-specs`

Later specs must follow these rules:

- The **UI Customization, Widgets, and Theming** spec (File 38) consumes this file's `Shell` region model, layout container, `RendererRegistry`, `PanelKind` rendering, built-in `ViewPreset` rendering, interaction models, and semantic-token discipline to define user-saved named layouts and the save/switch/customize flow, widgets and widget placement, the design-token system and themes, AI-assisted customization, and plugin UI placement, realizing the `customization_policy` (File 25 §7.4) without bypassing these contracts. It introduces no parallel shell, layout container, renderer table, or rendering path.
- The **per-surface specs** (27–32 and equivalent future surfaces) declare what their panels, view presets, inspectors, and observation viewers contain (File 25); this file renders them. A per-surface spec contributes renderers and panel kinds through the one `RendererRegistry` and the one self-registration contract, declares no private rendering path, and renders its history, comparison, and reconstruction views as projections over the one version graph. Per-surface accessibility, internationalization, and streaming concerns are this file's contracts applied to the surface's panels.
- The **Quality Control and Validation** spec validates presentation conformance — that the renderer holds no business logic and no private durable store, that every view is a projection, that every panel and control exposes structural semantics, that accessibility and internationalization hold, and that the approval and elicitation contracts render verbatim — through the registration validator and event and capability hooks, not a separate pipeline.
- The **Telemetry, Logging, and Observability** spec and the **Evaluation and Benchmarking** spec own the data the observability and debug surfaces (§13.2) render; this file owns the surfaces. The **Runtime Infrastructure and Lifecycle** spec orchestrates the renderer's startup and the service-layer connection around the storage lifecycle; this file owns the shell rendering.
- The **Packaging, Platform, and Distribution** spec (File 43) owns the installer, the auto-updater, the platform window-decoration and tray mechanics, and sidecar lifecycle; this file owns the shell regions, the multi-window model, and the window-state presentation it packages. The **MCP and External Integrations**, **Extension and Plugin System**, **Automation and Triggers**, and **Workflows, Templates, and Reuse** specs render their manager, dashboard, editor, and discovery surfaces (the connector manager, the plugin browser, the automation dashboard, the workflow editor) through this file's management-surface, inspector, and renderer contracts; they introduce no private UI shell or rendering path.
