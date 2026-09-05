# UI Shell, Layout, Presentation, and Interaction Models

## Status

Canonical. This file defines the presentation layer: the application shell, the presentation composition, the rendering of substrate state into views, the streaming and live-update contract, the presentation of control rails and approval/elicitation flows, the interaction models, and the accessibility, internationalization, and renderer-boundary contracts every user-facing frontend obeys. It realizes the UI-rendering boundary that Files 01–36 declare and delegate to this file, and introduces the net-new presentation primitives those files reference without owning: the `Shell` role model, the presentation-as-projection contract, the `RendererRegistry`, the `PresentationComposition`, the frontend-profile layering (§1.3), the `InteractionModel` lens set, the focused-dialog selector, and the accessibility contract. It is horizontal and medium-neutral — it defines how the one shared runtime is rendered and how user gestures are surfaced in any medium, not what any one surface does and not what any one frontend looks like. Its rules bind every frontend; a frontend's own realization of a rule binds only a session that declares the profile carrying it (§1.3). The per-surface specs (27–32) declare what their views contain; this file defines how any view renders. Later canonical files may refine it, but may not contradict it. The UI Customization, Widgets, and Theming spec (File 38) consumes this file's contracts to define customization, presentation contributions, and theming.

## Scope

This file defines:

- the presentation layer as a deterministic rendering of substrate projections plus a router of gestures into the control rails (File 26) for resolution — a layer that owns no business logic and no private durable state, realizing `core.invariants` (File 01 §7.5/§7.7) and `core.projection` (File 01 §6.11)
- the precise disambiguation of "UI," "surface," "view," "presentation," and "shell," and the distinction of the presentation layer from a work surface (File 25), a control rail (File 26), a presentation surface (`intent.presentation`, File 02 §8), an interaction shape (`core.interaction-shapes`, File 01 §2.2), the live `SurfaceState` (`world.surface-state`, File 18 §5), and the `ToolSurface` (File 07)
- the presentation-as-projection contract: every view is a typed projection over a named substrate source with an event-first rebuild trigger; the `RendererRegistry` that dispatches a typed substrate kind to its render component; and the no-private-presentation-state invariant
- the application `Shell` — the closed-canonical `PresentationRole` model (control entry, primary focus, inspection, execution status, produced output, conversation, ambient status, attention) realizing `worksurface.activation-shell` (File 25 §11.3) and `controlrail.shell-relationship` (File 26 §15) — plus navigation and the multi-context model
- the presentation composition — the declared unit set with its role bindings, grouping, ordering, primacy and viability constraints, unit prominence, the composition operations, and adaptation to a reduced presentation budget — and the boundary with File 38's saved-composition customization
- surface presentation and morphing: rendering a work surface's declared presentation units and `ViewPreset`s, morphing as a projection of the `SurfaceContract` + live `SurfaceState` + routing decision, and unit self-registration
- the `InteractionModel` lens set (conversation-only, inline assist, sidecar, paired, orchestration desk) as presentation lenses, and the rendering of the consequences of the deleted autonomy/participation/persona fields without reintroducing them
- conversation and transcript presentation: the transcript as a projection of the block pool, `Message`-versus-`Event` rendering, conversation activity state, the message-collapse and grouping pipeline, inline capability-call rendering, message actions and variants, and the input-composer presentation
- the rendering of substrate primitives into views: block rendering, artifact rendering (two pipelines, three uniform prominence levels, the confined interactive-artifact runtime), evidence/claim/citation/observation/provenance rendering, and version-timeline, comparison, and forensic-reconstruction views
- the streaming and live-presentation contract: typed-partial rendering, the streamed-partial-to-committed-block boundary, event-first reactivity, the rendering-performance requirements, attention following, and parallel presentation
- control-rail presentation (the discovery surface, gesture capture and the binding editor, the spoken session and handsfree operation, direct affordances, steering affordances, token commands, mentions and attachments, quick-open) and the available-action enable/disable contract
- dialog, elicitation, and attention presentation: the single focused-dialog priority selector, the rendering of the `policy.approval-ui-surface-contract` (File 06 §13) and `controlrail.elicitation` (File 26 §13) data contracts, and the three non-preemptive attention classes
- inspector and management-surface presentation: the explainable context inspector, the substrate-service management surfaces, the observability surface, the debug surface, and the version-history/forensic-reconstruction view
- accessibility as a first-class, dual-purpose (human assistive technology and agent machine readability) invariant; internationalization presentation; the renderer-to-backend boundary and frontend architecture; UI loading/empty/error/degraded/onboarding states; world-model/perception/state-awareness integration; the `ui.*` capability surface, events, settings, persistence/locality, explicit rejections, and consequences for later specs

This file does not define:

- the `WorkSurface` primitive, the `SurfaceContract`, the `SurfaceRegistry`, the `PresentationUnitKind`/`ViewPreset` model, the no-private-architecture invariant, or the autonomy-field deletion — File 25 owns those; this file renders the contract they declare
- the `ControlRail` primitive, the `RailResolution` set, the input-resolution contract, the binding map, the token grammar, the speech grammar and the spoken session, or the elicitation contract — File 26 owns those; this file renders the rails and the gestures they resolve
- the live `SurfaceState`, `PresentationUnitState`, `PresentationProminence`, `Selection`, `UiMode`, the world-entity catalogue, the durability tiers, the availability evaluator, or snapshot resolution — File 18 owns those; this file renders them and feeds them through self-registration
- the `Block`/`BlockKind`/`BlockContent`/lifecycle model, the `Artifact`/`Claim`/`Evidence`/`Citation`/`Observation`/`Provenance`/`Validation` model, or materialization — Files 08, 09, 24 own those; this file renders them
- the `ExecutionLedger` row format, the `EventEnvelope`, the `AppEvent` catalogue, the hook contract, the streamed-partial-to-committed-block durability rule, or aggregation policy — File 10 owns those; this file consumes the event stream and renders it
- the version graph, `ContextVersion`/`VersionDiff`, materialized view, branching, replay, or snapshot resolution — File 11 owns those; this file renders history, comparison, and reconstruction views as projections over them
- the policy evaluation algorithm, the approval router, leases, the `ApprovalRequest`/`ApprovalResponse`/`BatchApprovalRequest`/`ContradictionResolutionRequest` data contract, or effective-tier resolution — File 06 owns those; this file renders the data contract and never invents a parallel approval shape
- context assembly, the budget report, compaction, or token counting — File 13 owns those; this file renders the budget and the context inspector over its outputs
- audio capture, voice-activity detection, wake-word detection, transcription, screen capture, accessibility-tree capture, or any sensor mechanics — File 19 owns those; this file renders the voice session and observation viewers over their outputs
- the settings object model, the cascade, scopes, profiles, locality, the TOML overlay, or agent exposure — File 15 owns those; this file names the presentation settings dimensions and consumes the cascade
- the sandbox contract, isolation tiers, process control, or the elevated helper — File 23 owns those; the interactive-artifact runtime and any confined preview run through that contract
- the secret vault, trust model, egress governance, encryption, or the untrusted-content rule — File 22 owns those; this file honors the no-raw-secret-in-shareable-state and untrusted-content rules
- design tokens, the theme system and engine, named saved compositions and the save/switch/customize flow, presentation contributions and their placement, AI-assisted UI customization, plugin UI placement mechanics, or the realization of the `customization_policy` — File 38 owns those; this file owns the shell, the composition model, the rendering contracts, the interaction models, and the semantic-token discipline they consume
- packaging, the installer, the auto-updater, window-decoration platform mechanics, or sidecar lifecycle — the Packaging, Platform, and Distribution spec (File 43) owns those; this file owns the presentation roles, the multi-context model, and the presentation of a context's own state
- telemetry collection, log retention, or trace storage — the Telemetry, Logging, and Observability spec (File 41) owns those; this file owns the observability and debug surfaces that render them

## Source Resolution

Families reviewed: the application-shell and presentation material (`ui/14-1-application-shell.md`, `ui/14-2-chat-list-and-history.md`, `ui/14-3-streaming-ui.md`, `ui/14-4-source-management.md`, `ui/14-5-debug-and-performance.md`, `ui/14-6-to-14-8-theming-additional-windows-state.md`, `ui/15-1-layout-customizability.md`, `ui/15-2-domain-based-workspace-morphing.md`, `ui/15-3-and-15-4-participation-levels-personas.md`, `ui/context-management.md`, `ui/accessibility.md`, `ui/README.md`, `unit13-ui.md`); the UX-input and visual-design material (`ux-input/design-principles.md`, `ux-input/visual-identity.md`, `ux-input/whiteboard-and-handsfree.md`, `unit15-ux-distribution-files-glossary.md`); the conversation-presentation material (`conversation/01-core-chat.md`, `conversation/02-message-operations.md`, `conversation/03-versioning-and-branching.md`, `conversation/04-text-to-speech.md`, `conversation/05-voice-input.md`, `conversation/06-chat-dag.md`, `conversation/INDEX.md`, `unit03-conversation-engine.md`); the cross-cutting presentation contracts (`cross-cutting/actions.md`, `cross-cutting/artifacts.md`, `cross-cutting/blocks.md`, `cross-cutting/theming.md`, `cross-cutting/i18n.md`, `cross-cutting/state-awareness.md`, `cross-cutting/events.md`, `cross-cutting/service-layer.md`, `cross-cutting/errors.md`, `cross-cutting/response-parser.md`, `unit02-cross-cutting-infra-and-presentation.md`); the per-surface UI sections (`unit08-coder.md`, `domains/coder/ide-interface.md`, `domains/coder/command-palette.md`, `domains/coder/checkpoints-undo.md`, `domains/coder/agent-execution.md`, `domains/coder/terminal.md`, `unit09-web.md`, `domains/web/04-ui-and-modes.md`, `domains/web/00-overview.md`, `unit10-gui-control.md`, `domains/gui-control/06-element-inspector.md`, `unit11a-memory.md`, `unit11b-data-processor.md`, `unit11c-system-agent.md`, `unit11d-teacher.md`); the cross-tool UI synthesis (`unit11-cross-tool-learning.md`, `kuzeys-ui-customization-and-widgets-addendum.md`, `kuzeys-context-duplicate-prompt-handling-addendum.md`); the frontend-architecture addenda (`claude-code-frontend-addendum.md`, `claude-code-frontend-addendum-part2.md`, `opencode-frontend-addendum.md`, `continue-frontend-addendum.md`, `goose-frontend-addendum.md`, `goose-rust-addendum.md`, `cline-frontend-addendum.md`, `open-canvas-frontend-addendum.md`, `bolt-diy-frontend-addendum.md`, `open-webui-ux-addendum.md`); the locked stack and constraints (`foundations/stack.md`, `foundations/architecture.md`, `atlas3-core/CONSTRAINTS.md`, `atlas3-specbase/SKILL.md`, `distribution/packaging.md`); the strategic target-state review (`codex_recommendations.md` §5.1, §8.1, §8.12, §10.1–§10.9, §14.10); and the cross-ecosystem UI patterns (`warp-compressed.md`, `open-codesign-compressed.md`, `open-canvas-compressed.md`, `claudecodeui-compressed.md`, `t3code-compressed.md`, `terax-ai-compressed.md`, `suna-addendum.md`, `omi-compressed.md`, `voicebox-compressed.md`, `chatgpt_tool.md`, `claude_cowork_tool.md`).

Resolution rule: this file realizes and renders, it does not re-own. The work surface stays File 25's, the control rail stays File 26's, the live surface state stays File 18's, the block and artifact models stay Files 08/09's, the event stream stays File 10's, the version graph stays File 11's, the policy and approval contract stays File 06's, context assembly stays File 13's, perception stays File 19's, settings stay File 15's, security stays File 22's, the sandbox stays File 23's, and the design tokens, themes, presentation contributions, and saved-composition customization stay File 38's. This file owns the `Shell` role model, the presentation-as-projection contract, the `RendererRegistry`, the `PresentationComposition`, the frontend-profile layering, the `InteractionModel` lens set, the focused-dialog selector, the accessibility contract, and the renderer-boundary rule, and supplies each to the layers that consume it.

Resolved tensions:

- **What the UI is.** The strongest position across the most-evolved sources (`atlas3-core/CONSTRAINTS.md` §1, `cross-cutting/service-layer.md`, `foundations/stack.md`, `cross-cutting/blocks.md` "the chat view is one projection of the block stream … the context inspector is a different projection … all three read the same underlying blocks") is that the UI is a rendering of substrate projections, not a place where state or logic lives. This file adopts it as a load-bearing invariant: the presentation layer owns no business logic (`core.invariants`, File 01 §7.7, `core.explicit-rejections`, File 01 §8 "business logic in React or command wrappers") and no durable state the substrate does not already own; every view is a projection (`core.projection`, File 01 §6.11), and the cost of any UI-state loss is a rebuild, never data loss.
- **Shell anatomy — chat-as-container versus task-centered shell.** Early specbase drafts framed conversation as the primary pane and surfaces as panels that "morph" around it; `codex_recommendations.md` §5.1/§10.1 and `intent.presentation` (File 02 §8) reject chat-as-universal-container and resolve toward a task-centered shell where conversation is an always-available control rail and view, never the mandatory primary presentation. This file adopts the task-centered shell (§4), consistent with `worksurface.activation-shell` (File 25 §11.3), `controlrail.shell-relationship` (File 26 §15), and `core.product-thesis` (File 01 §1). The "chat is always visible, surfaces compose alongside" composition rule from `ui/15-2-domain-based-workspace-morphing.md` survives as the default conversation-first presentation, not as a container constraint.
- **Participation levels, autonomy modes, and personas.** Nearly every reviewed source still names a `Drive`/`Supervise`/`Collaborate`/`Delegate` participation level, a `PermissionMode`/`GooseMode`/agent-mode dial, or a persona/personality preset attached to interaction. The canon deletes all of them at every layer (`worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17; `world.surface-state`, File 18 §5.5; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `settings.explicit-rejections`, File 15 §20). This file adopts the deletion and fixes the presentation consequence (§7): the UI renders the *effect* those fields once described — the approval posture (Files 05, 06), which units are presented and at what prominence under which `ViewPreset` (File 25), and progressive disclosure — without any mode field, dial, or autonomy control at any UI layer. An interaction shape is a presentation lens varied freely by the user and the UI, never a backend primitive.
- **The 37/38 boundary.** `worksurface.views-presets` (File 25 §7.6), `worksurface.consequences-for-later-specs` (File 25 §21), and `controlrail.consequences-for-later-specs` (File 26 §21) split presentation from customization: the UI Shell spec owns shell, unit, and morphing presentation; the UI Customization spec owns concrete placement, contributions, and theming. This file fixes the line precisely (§5.5): File 37 owns the composition model, the unit-kind rendering, the built-in `ViewPreset` rendering, the morphing presentation, the renderer registry, the interaction models, and the semantic-token discipline; File 38 owns user-saved named compositions and the save/switch/customize flow, presentation contributions and their placement, the design-token system and themes, AI-assisted customization, and plugin UI placement. The default rendering is complete without File 38; File 38 adds customization over it.
- **Rendering as a registry versus per-surface bespoke views.** The source frontends converge on a kind-to-renderer registry (`unit13-ui.md` D13.11 `BlockRendererRegistry`, `claudecodeui-compressed.md` declarative tool configs, `opencode-frontend-addendum.md` tool-info registry, `cross-cutting/artifacts.md` `mime_type`-to-pipeline table). This file adopts one `RendererRegistry` (§3.3): a typed substrate kind dispatches to a render component, extensible through the same proposal-first source-approval path every other registry uses, so a surface or plugin contributes a renderer rather than forking a parallel rendering path.
- **Streaming as typed partials versus token strings.** `codex_recommendations.md` §10.2 and the frontend addenda resolve that streaming operates at the level of typed partials (text, plan, task-state, artifact-preview, diff-preview, validation, observation deltas), not only token strings, so the UI reads as an execution environment. This file adopts typed-partial streaming (§10) over `ledger.streaming-live-partials` (File 10 §12), and adopts the event-first, never-poll reactivity the project constraint requires (`core.event-first-by-default`, File 01 §7.15).
- **The locked frontend stack.** `foundations/stack.md`, `atlas3-specbase/SKILL.md`, and `core.stack-commitments` (File 01 §9) lock the renderer to a webview frontend over typed IPC (request-response invoke plus a streaming channel), with no in-renderer network server, and a compile-time type bridge between the backend service layer and the renderer. This file specifies the provider-invariant contract (§16) — the renderer is an adapter over typed IPC, business logic stays in the service layer, and one service layer serves every client whatever its medium — without copying any specific library API; concrete library, bundler, and platform-window mechanics are the renderer implementation's and File 43's. The webview stack is the shipped windowed-desktop frontend's realization of that contract and binds only a session declaring that profile (§1.3), never the contract itself: a terminal, a spoken, a spatial, or a third party's client reaches the same service layer over the same typed boundary.

## 1. Chosen Model

Anchor: `ui.chosen-model`

ATLAS3 has one presentation layer. It renders the one shared runtime and routes the user's gestures into the control rails (File 26) that resolve against it. It is the realization of `core.invariants` (File 01 §7.5)'s flexible-presentation rule — "presentation shape may vary by surface, interaction shape, and request complexity without changing the underlying runtime model" — and the structural enforcement of `core.invariants` (File 01 §7.7)'s service-layer-ownership rule.

The presentation layer does two things and only two things:

- it **renders projections** of substrate state — `SurfaceState` and `UiMode` (File 18 §5), the materialized view over the block pool (Files 08, 11), the `Artifact`/`Evidence`/`Claim`/`Citation`/`Observation`/`Provenance` entity layer (File 09), the event stream and live partials (File 10), the version graph (File 11), the tool surface and available-capability list (Files 07, 18 §9), the budget report (File 13), the approval and elicitation contracts (Files 06, 26), and the run presentation projection (`run.presentation`, File 04 §25)
- it **captures gestures** in its modalities and routes them to the `ControlRail` layer (File 26), which resolves them to `Capability` invocations (File 05) gated by the one policy layer (File 06) and routed by the one router (File 03); and it **self-registers** the live state of its presentation units back to the world model (`world.observation-state-update`, File 18 §8.1)

The presentation layer owns no business logic and no private durable state. Every view is a `core.projection` (File 01 §6.11): rebuildable from its source-of-truth substrate, declaring an event-first rebuild trigger, never the source of truth for any durable fact, and recoverable by rebuild on loss. Its only state is ephemeral view state — which presentation units are presented and at what prominence, the attended position within a presented unit, focus, in-progress composition — which is itself the live `SurfaceState` the world model holds (transient), plus client-only presentation preferences resolved and persisted through the settings system (File 15). Business logic, durable state, and the source of truth live in the backend service layer; command handlers and the renderer are adapters (`core.invariants`, File 01 §7.7; `atlas3-core/CONSTRAINTS.md` §1 realized).

This file introduces the net-new presentation primitives the prior files referenced without owning: the `Shell` role model (§4), the presentation-as-projection contract and the `RendererRegistry` (§3), the `PresentationComposition` (§5), the frontend-profile layering (§1.3), the `InteractionModel` lens set (§7), the focused-dialog selector (§12), and the accessibility contract (§14). `Shell`, `PresentationRole`, `RendererRegistry`, `PresentationComposition`, `InteractionModel`, and `PresentationView` are new canonical noun-objects, and a frontend profile is the named layer at which one medium's realization of any of them binds.

### 1.1 "UI," "Surface," "View," and "Shell" Are Disambiguated

Anchor: `ui.disambiguation`

The words "UI," "surface," "view," and "mode" are overloaded across the canon. This file fixes the presentation-layer meanings and distinguishes them:

- the **presentation layer** (this file) — the rendering of substrate projections plus the capture and routing of gestures (resolved by the control rails, File 26). It owns no business logic, no durable store, and no work model. It is the realization layer for the rendering every prior file delegates to "the UI specs."
- a **work surface** (`worksurface.work-surface`, File 25 §3) — a primary user-facing work environment with specialized workflows and views, declared by a `SurfaceContract`. The presentation layer renders a work surface; it is not one.
- a **control rail** (`controlrail.control-rail`, File 26 §3) — an entry class and a resolution contract that turns a gesture its declared `GestureGrammar` admits into a `RailResolution`. The presentation layer renders a rail's surface (the discovery surface, gesture capture, the spoken session) and routes gestures to it; it is not a rail.
- a **presentation surface** (`intent.presentation`, File 02 §8) — a projection over the underlying work: a conversation-first transcript, a comparison board, a notebook view, an observability trace, an artifact diff. A presentation surface is a *kind of view*; this file is the layer that realizes the rendering of presentation surfaces and fixes that the set is extensible.
- a **`PresentationView`** (this file, §3) — a single rendered projection: a typed view over a named substrate source, produced by a renderer from the `RendererRegistry`. A presentation surface is composed of one or more `PresentationView`s.
- an **interaction shape** (`core.interaction-shapes`, File 01 §2.2) — conversation-only, inline assist, sidecar, paired, orchestration desk: a presentation and involvement lens. This file realizes it as the `InteractionModel` (§7), a presentation lens, never a backend field.
- the live **`SurfaceState`** and **`UiMode`** (`world.surface-state`, File 18 §5) — the runtime values of the active surface, the presented units, focus, selection, available capabilities, and interaction mode. The presentation layer renders these values and produces them through self-registration; File 18 holds them, and File 18 §5.5 fixes the `UiMode` member set this file never restates.
- the **`ToolSurface`** (`surface.chosen-model`, File 07 §1) — the capability-visibility projection an invoker sees. The presentation layer renders the discovery, direct-affordance, and rail projections of the `ToolSurface`; it does not compose it.
- the **`Shell`** (this file, §4) — the binding of the always-available control rails, the primary focus, the inspections, the execution status, the produced-output access, and the conversation into the `PresentationRole` model a presentation context serves. It is a role model and a rendering relationship, not a durable object and not a work surface; there is one `Shell` role model and any number of presentation contexts serving roles from it (§4.5).
- a **`PresentationContext`** (`world.surface-state`, File 18 §5.1; this file, §4.5) — one independently attended client surface over the one service layer (§16), in whatever medium it presents: a window, a terminal, a spoken surface, a spatial canvas, an embedding host. A presentation context holds only ephemeral view state, is the unit at which presentation focus, input capture, and dialog presentation resolve (§11.2, §12.2), and is never a work-model identity, a settings scope, or a durable object. Its identity is a `PresentationContextRef { context_id, generation }` — a context-lifetime reference whose value may be recorded durably as historical correlation, while the live handle is a runtime-handle projection (`runtime.persistence-replay`, File 42 §21.1) and a closed generation never resolves to a later context. Attachedness is declared by the client session, never inferred from the medium: an `Interactive` context is capable of user interaction in any modality and never implies a graphical renderer, and a session that attends through no context at all is `NonInteractive` (File 18 §5.1).
- a **`PresentationUnit`** (`worksurface.state-declaration`, File 25 §5.3) — an independently addressable projection of substrate or work state whose `PresentationUnitKind` declares its content semantics, its compact state shape, the selection kinds it yields, and its structural semantics, with no assumption of a pane, a tab, a role binding, or simultaneity with any other unit. The canonical baseline is exactly twelve kinds and every other id a surface declares is a registered `Custom` kind (File 25 §5.3). File 25 declares the kinds and File 18 holds each unit's live state and prominence (`world.surface-state`, File 18 §5.3); this file renders them and composes them (§5).
- a **`PresentationComposition`** (this file, §5.2) — the declared set of presentation units a context presents, with their role bindings, grouping, ordering, primacy, co-presence constraints, and minimum-viability constraints. It fixes no topology and no geometry. It is not the *in-progress composition* of §8.4, which is the user's unsent content, held as live `SurfaceState` (`world.surface-state`, File 18 §5) and submitted through the message-submission lifecycle (`intent.message`, File 02 §3.4); where either word could be read for the other, this file writes "presentation composition" and "in-progress composition" in full.

### 1.2 Boundary

This file defines how the runtime is rendered and how gestures are surfaced. It does not define what any surface does (the per-surface specs), how a gesture resolves (File 26), whether an invocation is permitted (File 06), what a lens shows (File 07), how a run executes (File 04), how live interaction state is held (File 18), how content is captured (File 19), or how the UI is customized, themed, or extended with presentation contributions (File 38).

### 1.3 Frontend Profiles

Anchor: `ui.frontend-profile`

A frontend profile is a named, declared realization of the pattern rules of the frontend-facing files. A client session declares, for each presentation context it opens, the profiles that context implements and the roles it serves, at establishment (`runtime.transports`, File 42 §10.1; `world.surface-state`, File 18 §5). The declaration is a session fact, never a durable setting.

A profile declaration carries what the rules of the other files resolve against: the profile's own name and version, by which every clause below finds the sessions it binds; the entry classes and gesture grammars its sessions support, so the rails register for exactly those and no session is told about a class it cannot reach (`controlrail.registry`, File 26 §14.2); the presentation-budget unit, capacity and reduced-budget thresholds its medium affords, so §5.4's adaptation has both a scale to adapt against and the points at which it adapts (`customize.saved-layout`, File 38 §7.5); and the semantic-token families its medium declares, which is where the token discipline of §16.5 finds the family set it resolves against (`customize.design-tokens`, File 38 §4.2). A session declaring no profile declares those four directly. The presentation roles served are declared per presentation context, not per profile, because one session may open contexts serving different role sets (`world.surface-state`, File 18 §5.1).

A profile's clauses bind a session that declares the profile and no other. A session declaring no profile is conformant when it satisfies the pattern rules alone; a pattern rule is never satisfied by satisfying a profile clause; where a profile clause contradicts a pattern rule, the pattern rule wins and the profile clause is the defect; and a profile clause introduces no substrate or business semantics absent from the pattern. The shipped windowed-desktop frontend (`runtime.process-topology`, File 42 §4.3) declares the `desktop.windowed` profile, whose clauses are the `Windowed-Desktop Profile` subsections of Files 25, 26, 37 and 38.

A profile clause is written as its section's last subsection, after that section's `Boundary` subsection, titled `Windowed-Desktop Profile` for this profile and opening with the status line that cites this rule; each clause names the pattern rule it realizes. A pattern rule out of which a realization moved keeps a pointer to it and no second copy of its mechanics. Nothing about the concrete technology a profile is built on — a rendering library, a bundler, a platform window manager — is canonical at either layer, except where a profile clause states it as its own.

## 2. Boundaries with Adjacent Layers

Anchor: `ui.boundaries`

### 2.1 With File 01 (Core Thesis)

This file realizes `core.invariants` (File 01 §7.5) flexible presentation, §7.7 service-layer ownership, §7.9 system-wide customization (the simple-by-default, progressive-disclosure spectrum), §7.10 extension integrity (renderers and presentation contributions are reversible, policy-bound, source-trusted), and §7.11 user control (the steering and cancellation affordances). It realizes `core.interaction-shapes` (File 01 §2.2) as the `InteractionModel` lens (§7), `core.projection` (File 01 §6.11) as the presentation-as-projection contract (§3), and `core.typed-errors` (File 01 §6.9) at the renderer boundary (§16). It honors `core.stack-commitments` (File 01 §9) for the client-to-service transport contract — typed inter-process communication, of which the webview frontend is one client — and `core.explicit-rejections` (File 01 §8): no business logic in the renderer, no interaction shape coupled to surface or model identity, no autonomy control in core architecture. `Shell`, `PresentationRole`, `RendererRegistry`, `PresentationComposition`, `InteractionModel`, and `PresentationView` are new canonical noun-objects.

### 2.2 With File 02 (Conversation, Intent, Task)

`intent.presentation` (File 02 §8) is the primary delegation this file discharges: a presentation surface is a projection over work, the set is extensible, conversation-first and workspace-first are both first-class, parallel activity must not be forced into one flat stream, and presentation customization never changes the work model. §6, §7, §8, and §10 of this file realize those rules. `intent.conversation-state` (File 02 §2.3)'s coarse activity state (`streaming`/`processing`/`awaiting_user`/`idle` plus the `compacting` indicator) is rendered as a projection (§8.3); `intent.message` (File 02 §3.3)'s `Message`-versus-`Event` distinction is the transcript-rendering contract (§8.2). This file renders conversation; File 02 owns the conversation model.

### 2.3 With File 03 (Routing and Dispatch) and File 04 (Execution and Run Model)

The presentation layer surfaces the routing result and allows override (`intent.run-intent`, File 02 §4.2; `routing.route-record`, File 03) but does not route. It renders `run.presentation` (File 04 §25)'s execution projection — the same run shown as a conversation answer, compact progress, expandable timeline, workspace activity, multi-agent board, artifact diff, workflow graph, or observability trace — and the run facts that section requires the UI to show (status, active execution unit, pending approvals, model route, capability calls and results, child runs, artifacts, failure and recovery path). Steering affordances render the user-facing surface of `run.user-intervention` (File 04 §17.1) and `run.cancellation` (File 04 §17.3); the rail resolves them (File 26 §10) and File 04 carries them out.

### 2.4 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces)

Every user-invocable control the presentation layer renders is a presentation of a `Capability` (`capability.capability`, File 05 §2.1), reachable through a rail (File 26) and gated by policy (File 06); the UI invokes no operation out of band. The discovery, direct-affordance, and binding surfaces render the lens `surface.visibility-composition-resolution-algorithm` (File 07 §9) composes and `surface.presentation-in-user-facing-surfaces` (File 07 §12) projects; the available-capability list is `world.state-aware-capability-availability` (File 18 §9). Approval and elicitation rendering consumes the `policy.approval-ui-surface-contract` (File 06 §13) data contract verbatim and never invents a parallel approval shape (§12).

### 2.5 With Files 08, 09, 11 (Blocks, Artifacts, Version Graph)

The transcript, the inspectors, and the execution views are three projections of the one block pool (`block.cross-surface-interoperability`, File 08 §12; `cross-cutting/blocks.md` realized). The presentation layer renders `Block`s through the `RendererRegistry` (§9) and the entity layer (`Artifact`/`Claim`/`Evidence`/`Citation`/`Observation`/`Provenance`/`Validation`, File 09) through their renderers and the `artifact.per-surface-projections` (File 09 §17.2) lenses; it introduces no private block pool, kind catalogue, or content model. History, comparison, undo affordances, and forensic reconstruction are projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24); the UI introduces no parallel checkpoint, snapshot, or history store, and renders artifact and file edits live as new versions commit.

### 2.6 With File 10 (Ledger, Events, Hooks)

The presentation layer is the primary live subscriber to the event bus. It consumes `ledger.event-stream` (File 10 §5) with the `ledger.event-envelope` (File 10 §5.2) envelope and the `ledger.app-event-catalogue` (File 10 §5.3) vocabulary, renders `ledger.streaming-live-partials` (File 10 §12)'s streamed partials and the partial-to-committed-block boundary, and honors `ledger.sensitivity-aware-persistence-retention` (File 10 §10) — `Secret` content never renders into shareable state, and the envelope's sensitivity classification gates what appears in screenshots and exports. The UI emits its own presentation facts as `Custom { namespace: "ui" }` events (§21); it opens no side-channel and no parallel bus.

### 2.7 With File 13 (Context Assembly), File 16/17 (Model Strategy, Provider Layer)

The context inspector and budget bar render `context.context-policies` (File 13 §4)'s outputs and the budget report `context.consequences-for-later-specs` (File 13 §22) exposes, including the live dry-run preview; the UI assembles no model request. Model-route indicators, usage and cost dashboards, and provider-health indicators render `model.model-strategy-layer` (File 16) selections and `provider.consequences-for-later-specs` (File 17 §26)'s per-call attribution and health state; the UI selects no model and tracks no usage.

### 2.8 With File 15 (Settings)

Every presentation behavior with meaningful variation is a setting (`settings.settings-over-constants`, File 15 §13) resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); the UI is not a durable settings scope (§22). The renderer reads settings reactively (the setting-change event drives re-render) and persists client-only presentation preferences through the settings system, never a private store (§16, §19). The presentation layer renders no autonomy or participation knob, because none exists in settings (`settings.explicit-rejections`, File 15 §20).

### 2.9 With File 18 (World Model) and File 19 (Perception)

This file renders `world.surface-state` (File 18 §5) — the `SurfaceState`, `PresentationUnitState`, `Selection`, and `UiMode` File 18 §5.6 states "the UI specs render" — and produces it: the presentation layer's units self-register their state to the world model on activation, focus, selection, and content change (`world.observation-state-update`, File 18 §8.1), so the UI is both the renderer and the source of live `SurfaceState`. Available-action enable/disable renders the availability evaluator's output (`world.state-aware-capability-availability`, File 18 §9). Observation viewers (screenshots, accessibility-tree overlays, page and machine snapshots) render `Observation` blocks (File 09 §13) produced by `perception.*` (File 19); the UI captures nothing of its own state and reads none of it back from a rendered image.

### 2.10 With Files 22, 23, 24 (Security, Sandbox, Workspaces)

The presentation layer honors `secret.backend-boundary` (File 22 §4) — raw secrets never reach the renderer and never render into shareable state — and `security.untrusted-content` (File 22 §12): rendered untrusted content (web pages, foreign application captures, ingested documents) carries no authority and is presented as content, never as instruction. The interactive-artifact runtime and any confined preview render inside the one `Sandbox` contract (File 23) at a least-authority origin; the UI opens no private sandbox. Workspace, file-tree, and materialized-path views render `workspace.materialization` (File 24 §10)'s mirror as a projection of the active version; the UI writes to disk only through the workspace materialization path.

### 2.11 With File 25 (Work Surface Contract) and File 26 (Control Rails)

`worksurface.consequences-for-later-specs` (File 25 §21) and `controlrail.consequences-for-later-specs` (File 26 §21) name this file as the consumer that renders the `SurfaceContract`, live `SurfaceState`, and routing decision into shell presentation and surface morphing (§4–§7), and renders the control-entry and primary-focus roles, the discovery surface, gesture capture and the binding editor, the spoken session and its confirmation, the direct affordances, and the steering affordances over the data and resolution contracts those files fix (§11). Presentation may vary freely; the surface and rail contracts may not. This file renders both and re-owns neither.

### 2.12 With File 38 (UI Customization, Widgets, and Theming) and File 43 (Packaging)

This file owns the shell, the composition model, the unit-kind rendering, the built-in `ViewPreset` rendering, the morphing presentation, the renderer registry, the interaction models, and the semantic-token discipline. File 38 owns user-saved named compositions and the save/switch/customize flow, presentation contributions and their placement, the design-token system and themes, AI-assisted customization, and plugin UI placement, consuming this file's contracts (§5.5). File 43 owns the installer, the auto-updater, platform window-decoration mechanics, and sidecar lifecycle; this file owns the presentation roles, the multi-context model, and the presentation of a context's own state that File 43 packages for the frontends it ships.

### 2.13 Boundary

This file is the presentation layer. It owns the `Shell`, the composition model, the frontend-profile layering, the rendering contracts, the interaction models, the dialog, elicitation and attention presentation, the accessibility and internationalization contracts, and the renderer boundary. It owns no work model, no rail resolution, no policy, no capability, no live state ownership, no capture, no settings storage, no design-token system, and no customization mechanics. It renders the substrate; the owning files realize it.

## 3. The Presentation-as-Projection Contract

Anchor: `ui.presentation-projection`

### 3.1 Definition

A `PresentationView` is one rendered projection: a typed view over a named substrate source, produced by a renderer, that displays the source's current state and updates when the source changes. The presentation-as-projection contract is the rule that every view in the UI is a `PresentationView`, that it holds no source-of-truth state, and that it is rebuildable from its substrate.

### 3.2 Rule

- Every `PresentationView` declares the substrate source it projects (a block-pool query, a `SurfaceState` scope, an event-stream subscription, a version-graph projection, an entity-pool lens, a budget report, an approval-contract subscription) and the event-first trigger that rebuilds it (`core.projection`, File 01 §6.11; `world.state-change-events-reactivity`, File 18 §12). A view never polls a substrate on a timer; it subscribes to the substrate's change events. A periodic refresh is a flagged, configurable fallback only where a source emits no change events (a hardware metric sample), never a correctness condition (`core.event-first-by-default`, File 01 §7.15).
- A `PresentationView` holds no durable fact. Its rendered content derives from the substrate; its view-local state (prominence, the attended position within it, in-progress composition, focus) is ephemeral and is the live `SurfaceState` the world model holds (File 18 §5), reconstructed from self-registration when the view is activated again. The cost of losing any view state is a rebuild, never data loss.
- The presentation layer holds no business logic. A view computes derived presentation values (formatting, grouping, composition arithmetic, syntax highlighting) but never the substrate's truth: it does not decide policy, route, select a model, mutate a block, evaluate availability, or own a capability's effect. Those are service-layer concerns reached through typed invocations (§16; `core.invariants`, File 01 §7.7).
- A `PresentationView` renders `Secret`-classified content as masked, never raw, and respects the sensitivity classification of the envelope and block it renders (File 10 §10, File 22 §4); a view never persists or exports raw secret material.

### 3.3 The `RendererRegistry`

The `RendererRegistry` is the one registry that maps a typed substrate kind to the renderer that displays it. A renderer is registered for a `BlockKind` (File 08 §3.1), an `ArtifactKind` (File 09 §4.1), an `ObservationKind` (File 09 §13.2), a `PresentationUnitKind` (File 25 §5.3), an `AppEvent` kind (File 10 §5.3), or an external-content media type, and dispatches that kind to its render component.

Renderer trust and content trust are separate. A renderer is registered code from a built-in or source-approved contribution; the content it renders keeps its own authority class and sensitivity. External, web, connector, model, or tool-returned content is data and must not execute as host UI code. Executable or interactive untrusted artifacts use the sandboxed artifact-runtime path (§9.3), not ordinary renderer dispatch.

- Dispatch checks the registry first, then a canonical baseline renderer; an unregistered or unknown kind renders through a safe typed-placeholder renderer that shows the kind, a description, and a recovery action, never a crash or a blank (`block.kind-catalogue`, File 08 §3.1's custom-kind path; `intent.presentation`, File 02 §8.1's typed-placeholder-elsewhere rule). The baseline includes renderers for the canonical block kinds (message, reasoning, tool-call and tool-result, file attachment, retrieved-content, evidence, citation, observation, validation, critique, claim, plan, group), the canonical artifact kinds, and the canonical presentation-unit kinds.
- Surface-specific and plugin-contributed renderers register through the one proposal-first source-approval-gated path (`capability.runtime-mutation`, File 05 §16.2; `policy.source-approval-flow`, File 06 §9), under the same source taxonomy and trust model as every other contribution; a surface or plugin contributes a renderer, never a parallel rendering pipeline. There is one `RendererRegistry`; no surface, rail, or plugin maintains a private renderer table.
- A contributed renderer may override a baseline renderer only within a bounded anti-shadowing policy, so a source-approved contribution cannot silently shadow a security- or trust-critical presentation — the presentation realization of the renderer-override rule `plugin.contribution-points` (File 35 §5.3) delegates to this file. Baseline-only kinds — the approval and elicitation dialogs (§12), tool-call and tool-result rendering, masked-secret rendering, and the trust and provenance indicators — render through the canonical baseline renderer only and are never overridable by a surface, rail, or plugin contribution. The canonical content kinds (the block, artifact, observation, and presentation-unit kinds the baseline covers) are overridable, but an override that shadows a canonical renderer is surfaced to the user and applied only with consent (`policy.source-approval-flow`, File 06 §9), never silently. `Custom { namespace, name }` kinds are freely registered and overridden within their own namespace.
- A renderer receives the typed substrate value and a rendering environment (the active `InteractionModel`, the unit's prominence and its placement in the composition, the scope, the resolved semantic tokens, the resolved locale) and returns a `PresentationView`. Renderers consume only the semantic-token layer for the presentation properties they vary (§16.5); a renderer that references a raw value rather than a semantic token is invalid.

### 3.4 Boundary

This section fixes the projection contract and the renderer registry. The substrate files own each source; this file requires every view to be a projection over one. File 38 owns the presentation-contribution and theme layers that register additional renderers and tokens through this same registry and the same token discipline.

## 4. The Application Shell

Anchor: `ui.shell`

### 4.1 Definition

The `Shell` is the binding of the always-available control rails, the primary focus, the supporting inspections, the execution status, the produced-output access, and the conversation into the `PresentationRole` model a presentation context serves (§4.5). It is the rendering realization of the shell relationship `worksurface.activation-shell` (File 25 §11.3) and `controlrail.shell-relationship` (File 26 §15) name, and of `codex_recommendations.md` §10.1's task-centered shell. It is a role model and a rendering relationship, not a durable object.

### 4.2 The Presentation-Role Model

The `Shell` is a closed-canonical set of `PresentationRole`s, each a promise about what a context does for the user, bound to whatever affordance the medium has. A context declares which roles it serves and is bound by the semantics of each role it declares; the binding, not the affordance, is what this file fixes. The canonical roles:

- `ControlEntry` — the always-available entry-and-control role presenting the conversation input rail and the discovery rail's entry point (File 26 §5, §6); reachable whatever holds primary focus, and never displaced by what it invokes
- `PrimaryFocus` — the role presenting the currently active work surface or presentation surface (File 25 §11.2); whatever the task currently needs
- `Inspection` — the role presenting management and inspection surfaces (context inspector, sources, memory, world state, settings; §13) subordinate to primary focus
- `ExecutionStatus` — the role presenting the live execution projection of active runs (`run.presentation`, File 04 §25): status, active execution unit, progress, the activity projection
- `ProducedOutput` — the role presenting the artifact and output pool (`artifact.per-surface-projections`, File 09 §17.2): produced artifacts, history, and entry points to open them
- `Conversation` — the role presenting the transcript (§8); available without becoming the container, so adding a work focus never removes conversational access and conversation is never the forced primary
- `AmbientStatus` — the continuously available role presenting coarse run and connection state, the model route, and context-level indicators
- `Attention` — the role presenting non-preemptive attention items: persistent pending state, transient completion and recoverable conditions, and provenance-carrying follow-up (§12.4)

`PresentationRole` is closed-canonical with no `Custom` arm (`core.closed-canonical`, File 01 §6.16); a new role is a canonical-spec change, never a registered extension and never an ad-hoc binding, because the role set is what a cross-medium contract is written against and what File 25 §11.3's guarantees bind to. A context declares the subset it serves and binds each declared role to an affordance of its medium; a role it does not declare it does not serve, and no rule resolves to a role a context has not declared. The minimum an `Interactive` context must declare to be usable at all is `ControlEntry` and one of `PrimaryFocus` or `Conversation`: without an entry point nothing can be invoked, and without one of the two nothing can be worked on or said. What a role binds to is the medium's (realized in the windowed-desktop profile as a region model, §4.7). No role is the mandatory primary: `PrimaryFocus` is whatever the work needs, and `Conversation` is always reachable where it is declared, never the forced container (`core.product-thesis`, File 01 §1; `intent.presentation`, File 02 §8; the chat-as-universal-container rejection, File 25 §20).

A context that declares every role serves the whole model, and one that declares a subset serves that subset and never claims the set (§4.5); "full" describes a declaration, and the canon closes no second class of context around it. The role set is unchanged by how many contexts are open: there is one closed-canonical `PresentationRole` set, and each context binds the roles it declares independently of every other.

### 4.3 The Composition Rule

- The default conversation-first presentation gives `Conversation` primacy with the other declared roles at minimal prominence; richer presentations give a work surface primacy and present supporting roles co-present with conversation rather than in place of it (`ui/15-2-domain-based-workspace-morphing.md` realized; `atlas3-specbase/SKILL.md` "chat is the substrate"). Adding a work focus never removes conversational access. The same work moves between conversation-first and a work-surface focus over time without changing the work model (`intent.presentation`, File 02 §8.2/§8.3).
- The presentation activation of a role binding or surface (presenting it, focusing it, raising or lowering its prominence) is a UI-state operation scoped to the conversation, workspace, or session (`worksurface.activation-shell`, File 25 §11.2); it updates live `SurfaceState` (File 18) and may influence future routing or user-invoked resolution, but it never rewrites an active run's execution binding. A run's primary surface and execution context change only through `routing.mid-execution-reroute` (File 03 §12) or explicit user override (`worksurface.explicit-rejections`, File 25 §20's presentation-focus-is-not-reroute rule).
- A supporting role may auto-reveal on a declared reveal-trigger class. The canonical `RevealTrigger` set is closed-canonical-plus-`Custom { namespace, name }` — `RunStarted`, `FirstOutput`, `ArtifactProduced`, and `PendingRequest` — with each role binding declaring which classes it honors: `ExecutionStatus` may reveal on `RunStarted`, `ProducedOutput` on `ArtifactProduced` or `FirstOutput`, and a `Custom` trigger class is declared and honored by the binding that registers it. Approval and elicitation remain the focused-dialog selector's domain (§12); a `PendingRequest` at most raises a non-interrupting indication on a relevant role, never a reveal that displaces the focused-dialog selector. Auto-reveal is context-scoped: a reveal trigger acts only in contexts presenting a scope the triggering event's carried references match — matched against the context's presented scope and its units' declared bindings, never a universal event scope — and by default it reveals in the origin or attention context only (§4.4), every other matching context degrading to a non-interrupting indication; fan-out reveal across matching contexts is a setting (§22). A reveal never preempts the user's current attention or input target: it never brings a context forward over the one being attended, never moves focus or assistive-technology focus off `PrimaryFocus`, never blocks it, and falls back to indication-only behavior when disabled (realized in the windowed-desktop profile as a badge, §4.7).
- Shell composition is scope-resolved and context-resolved: there is no single global active role or surface when multiple sessions are live, and no single global focus when multiple presentation contexts are open (`world.surface-state`, File 18 §5.1); each context resolves the role bindings for the scope it presents. Two contexts presenting the same scope share every scope-keyed fact — the same blocks, the same active version, the same workspace binding, the same pending requests — and differ only in ephemeral per-context view state (File 18 §5.1).

### 4.4 Navigation

The shell renders navigation between conversations, surfaces, and workspaces. Navigation exposes each target class as an enumerable, filterable set with per-entry metadata and an unread predicate, an ancestry path for the current position, and a return path to where the user was — plus the quick-open and global-search surfaces (§11). The affordance that carries each of those is the medium's (realized in the windowed-desktop profile as named navigation controls, §4.7). Navigation resolves through a typed `NavigationTarget`: a conversation plus block or version, a surface plus selection, an artifact plus version, or a management surface plus filter. Quick-open, global search, notification reveal actions, and External-Protocol rail deep links (File 26 §12) resolve through the same target contract. Navigation is presentation: selecting a target activates or reveals it for the scope and re-renders; it commits no work-model change beyond the activation the underlying capability performs. Conversation, surface, and workspace navigation render the identities Files 02, 25, and 24 own; the UI maintains no parallel list. Navigation originating from an external deep link is reveal-only and `ReadOnly`; any consequential action encoded by a link enters through the normal rail, capability, policy, and approval path.

A `NavigationTarget` resolves into a presentation context through one service-layer context resolver taking the gesture's origin and a requested disposition — `ReuseOrigin`, `RevealExisting`, or `CreateNew` — and returning a typed result: `Resolved`, `Created`, `LimitReached`, `NoPresentationContext`, or `TargetUnavailable`. The default navigation disposition resolves in order: the context the gesture originated in; else an open context already presenting the target's scope, which is brought to the user's attention; else the attention target; else creation of a context. An explicit open-in-a-new-context gesture is `CreateNew` — it never silently reuses, and it still answers `LimitReached` when the configured maximum is met (§22). The **attention target** is the presentation context most recently attended, maintained as one device-local logical ordering over attention-change events — never a wall-clock condition (`core.event-first-by-default`, File 01 §7.15) — and it is a presentation hint for navigation and dialog placement only: it never enters routing, policy, or any authority decision (File 18 §11.3). External deep links (`packaging.platform-integration`, File 43 §7.3) and the single-instance handoff (`runtime.process-topology`, File 42 §4.4) resolve through this same resolver; an invocation with no attending client (automation, a command-line or programmatic entry) answers `NoPresentationContext` rather than implicitly materializing one, and context creation at boot or restore is the restore policy's own entry path (§4.5; File 42 §11.3), not a navigation resolution. Bringing a context to the user's attention is presentation: it commits no work-model change and never rewrites an active run's execution binding (`worksurface.explicit-rejections`, File 25 §20).

### 4.5 The Multi-Context Model

A presentation context is described by the role subset it declares (§4.2) and by nothing else; the canon closes no classification of contexts around that declaration, and a purpose or a per-subject cardinality is a fact of one medium's packaging that the profile declaring it owns (§1.3, §4.7):

- Presentation contexts are peers over one core: none is primary, none is subordinate, and any number may be open up to a configured maximum that is a setting with a canonical default, never a hidden ceiling (§22; `runtime.operating-constraints`, File 42 §22). A context is created only by explicit user or capability action (§20.1), by the context resolver's creation outcome (§4.4), or by the restore policy at launch. Context multiplicity is a presentation fact only: one core process per data root (`runtime.process-topology`, File 42 §4.4), one authoritative service layer, one substrate, however many contexts present them.
- A context serving a subset of the roles for one declared purpose serves that purpose and claims nothing more. Where a declaring profile marks a purpose unique for a subject, a request for that subject follows focus-or-create: it brings the open context to the user's attention rather than creating a duplicate (realized in the windowed-desktop profile as an auxiliary window, §4.7).

Every presentation context carries the same trust class: no context, a settings or credential-entry context included, is a privileged renderer — the renderer sits below the backend behind typed allowlisted inter-process methods, and credential entry remains the one controlled write-only ingress (`security.process-ipc-trust-boundary`, File 22 §13.2). Contexts share no in-memory state and coordinate only through the event bus and the settings system (§16.4; `foundations/stack.md` realized); an optimistic mutation envelope is context-local — it applies, rolls back, or is superseded only in the context that issued it, every other context observing only the authoritative outcome (`runtime.transports`, File 42 §10.3).

A context's identity is its `PresentationContextRef { context_id, generation }` (§1.1): the reference may be recorded durably as historical correlation, but no durable current-context registry or live handle is reconstructed from it — after the matching generation closes, the reference has historical meaning only and never resolves to a later context, so a delayed or replayed message can never act on a replacement context (`runtime.persistence-replay`, File 42 §21.1).

Context state persists as one device-local presentation-context record — a settings value, never a settings scope (`settings.scopes-profile-contexts-overlays`, File 15 §5.1; §22.1) — holding one entry per presentation context: a stable restore key distinct from the runtime `context_id`, the presented-scope reference, the composition or view-preset reference, and the declared profile the entry was recorded under. Where a medium has a placement or an equivalent situating fact, it rides the entry as a profile-local realization payload or a typed, namespaced, renderer-declared restore hint that a client which does not understand it ignores without loss of correctness; no such value is a canonical field of the record, because a medium that has none must still restore completely (realized in the windowed-desktop profile as a window placement, §4.7). The record stores restore intent and no unit content or durable fact; syncable composition and preset records are referenced, never copied device-local. Entries mutate individually under expected-revision atomicity with typed conflict, never by whole-record overwrite from concurrent contexts (File 18 §8.2). Whether the previous context set restores on launch, and what a launch with no restorable set opens, are settings (§22). Restore is device-local and revalidated per entry against the current environment, workspace, permission, and local-authentication and sensitivity state before the context first presents (`security.local-authentication-gate`, File 22 §13.5); an entry whose recorded realization is unavailable or unsafe restores without it, an entry that cannot restore safely is skipped, and each adjustment or skip records its own diagnostic UI event — one bad entry never blocks the rest. Restoring a context is restore intent only: it never rebinds a conversation, switches a workspace `materialization_head`, or resumes a run (`workspace.conversation-binding`, File 24 §7.2; `workspace.materialization`, File 24 §10.3).

Closing a presentation context is a presentation operation: it unregisters the context's units and subscriptions and cancels nothing in the work model — no run, no execution binding, no materialization. In-progress local input is protected: a close that would discard an unsaved draft or in-progress composition surfaces it rather than silently losing it (`core.invariants`, File 01 §7.13). Whether losing the last presentation context ends the process or leaves the application resident is a context-lifecycle resolution this file owns — evaluating the remaining contexts, any host-provided residency the declared profile reports, and the close-last-context setting (§22) — and only its typed `QuitRequested` outcome enters the runtime shutdown sequence (`runtime.shutdown`, File 42 §12.3); an explicit quit action, a termination signal, and an operating-system shutdown are shutdown signals directly and bypass the close-last preference. The residency mechanism is the host platform's (`packaging.platform-integration`, File 43 §7.2), never this file's (realized in the windowed-desktop profile as tray residency, §4.7).

A presentation unit relocates between presentation contexts through the one unit-relocation operation (§5.2), preserving its identity, its role binding, and its declared bindings; a context presenting that one unit is its degenerate target. Window-decoration and platform-window mechanics are File 43's; this file owns the role binding, the role declaration, the context-resolution rule (§4.4), the context-lifecycle resolution, and the cross-context coordination contract.

### 4.6 Boundary

This section owns the shell role model, the composition rule, navigation and its context-resolution rule, and the multi-context model. File 25 owns the shell relationship and the surface activation it renders; File 26 owns the rails it binds; File 18 owns the live state it resolves; File 42 owns the client sessions and the shutdown sequence the context-lifecycle resolution feeds; File 43 owns the window and installer mechanics; File 38 owns customization of role binding. This file renders the shell in every presentation context.

### 4.7 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §4.2. The profile binds the eight roles to eight regions of one window: `ControlEntry` to the command rail, which renders the conversation input rail and the command-palette trigger and is always reachable regardless of the focus surface; `PrimaryFocus` to the focus surface; `Inspection` to the inspector dock; `ExecutionStatus` to the execution console; `ProducedOutput` to the artifact navigator; `Conversation` to the conversation view, an expand/collapse view available alongside any focus surface and never the forced primary pane; `AmbientStatus` to the status region; and `Attention` to the notification region. A region may be present or absent in a given presentation; the conversation view is always available to expand.

Realizes: §4.3. A reveal this profile does not act on renders as a badge on the region concerned: auto-reveal never raises, focuses, or reorders a window, and never moves keyboard or assistive-technology focus off the focus surface.

Realizes: §4.4. Navigation renders as the conversation list and history (grouped, searched, filtered, with per-entry metadata and unread indication), the surface and workspace selectors, and breadcrumb and back affordances. The attention target is the shell window most recently holding keyboard input focus.

Realizes: §4.5. A context declaring every role is a **shell window**; a context declaring a subset for one declared purpose is an **auxiliary window**, and `Created` opens one while `RevealExisting` raises one. The purpose set of an auxiliary window is closed-canonical-plus-`Custom { namespace, name }`: `Settings`, `VoiceCompanion`, `Presentation`, `DetachedUnit`. Each purpose declares its cardinality — `Settings` and `VoiceCompanion` are unique per installation, `DetachedUnit` is unique per subject (detaching relocates one unit, it never duplicates the unit's identity), `Presentation` is multi-instance per subject (the same subject may present on two displays or to two audiences), and a `Custom` purpose declares its own.

Realizes: §4.5. A window's placement — its display, its virtual desktop, its position and its size — is the situating fact this profile records as the presentation-context record's realization payload. It is revalidated per entry against the current display, virtual desktop, and permission state before first paint; an entry whose placement is unavailable, unsafe, or off-screen gets a safe default placement rather than being skipped for that reason alone. Two shell windows on two displays are two presentation contexts of one client session, each with its own placement, sharing every scope-keyed fact.

Realizes: §4.5. Residency is the tray affordance (`packaging.platform-integration`, File 43 §7.2): closing the last shell window either quits the application or leaves it resident behind the tray item, per the close-last-context setting (§22).

**Coder surface.** Realizes: File 27 §9.2. The Coder surface binds version-control state to the status region: the status bar carries the current branch, ahead/behind counts where a remote is tracked, and a change summary.

**Coder surface.** Realizes: File 27 §17.3. An inline indicator is shown while any prompt capture is active.

## 5. Presentation Composition

Anchor: `ui.layout`

### 5.1 Definition

A `PresentationComposition` is the declared set of presentation units a context presents, with their role bindings, grouping, ordering, primacy, co-presence constraints, and minimum-viability constraints. It is the structural model the shell uses to compose `PresentationView`s across the roles a context serves, and it fixes no topology and no geometry: how a medium arranges what the composition declares is the medium's. This section owns the composition and its behavior; File 38 owns user customization of it.

### 5.2 The Composition Model

- A composition declares, for each unit it presents: the role it binds (§4.2), the group it belongs to, its order within that group, whether it is the primary unit, the units it must or must not be co-present with, and the minimum presentation budget below which it is not viable. It declares no topology, no geometry and no adjacency; a medium realizes the declaration with whatever arrangement it has, and a composition that cannot be realized within the current budget degrades by §5.4 rather than by being refused (realized in the windowed-desktop profile as a layout container, §5.7). Units carry a `PresentationProminence` (`Absent`, `Minimal`, `Present`, `Exclusive`, `world.surface-state` File 18 §5.3) — the share of the context's finite attention the unit holds, which says nothing about geometry — and may be relocated to another presentation context through the one unit-relocation operation, a context presenting that one unit being its degenerate target (§4.5).
- A unit renders a `PresentationUnitKind` (File 25 §5.3) through the `RendererRegistry` (§3.3). Unit kinds are the cross-surface roles File 25 declares (editor, terminal, browser, inspector, document, canvas, list, board, timeline, graph, diff, preview); two surfaces presenting the same unit kind share the renderer (`block.cross-surface-interoperability`, File 08 §12), and an embedded borrowed unit carries its own `surface_binding` for invocation resolution and attribution without changing the host surface (`worksurface.activation-shell`, File 25 §11.4).
- The composition supports re-grouping, subdivision, reordering, primacy change, prominence change, and relocation as presentation operations on view state; they commit no work-model change. Each is reachable through every modality the context declares, never through one input device alone, and each exposes the structural semantics §14 requires (realized in the windowed-desktop profile as a layout container, §5.7).

### 5.3 Built-in Presentation Presets

- The shell renders a surface's declared `ViewPreset`s (`worksurface.views-presets`, File 25 §7.2): a named, presentation-only startup intent naming which units are active, which is primary, and optional profile hints, opaque outside the declaring profile (`worksurface.views-presets`, File 25 §7.2). Applying a `ViewPreset` changes presentation only; it never silently changes model selection, context policy, execution entry, budget, sandbox profile, approval posture, or instruction-source authority (`worksurface.views-presets`, File 25 §7.2; the silent-policy-change rejection, File 25 §20). A `ViewPreset` is a presentation seed, not an autonomy mode (§7).
- The shell ships a default composition per surface and a default conversation-first composition; the default rendering is complete without any user customization. Where a surface or settings profile declares a default `ViewPreset`, the shell renders it on activation; the user may switch presets through the rail (`controlrail.command-rail`, File 26 §6), and switching is a presentation change.

### 5.4 Adaptation to the Presentation Budget

A context declares its **presentation budget** — how much simultaneously attendable presentation the medium affords, as one scalar in a named unit with a declared set of reduced-budget thresholds (`customize.saved-layout`, File 38 §7.5), carried by the profile it declares (§1.3) — and the composition adapts to it. Under a reduced budget the composition degrades to the primary unit with navigation among the rest, dropping co-presence before it drops a unit and never dropping a unit that a co-presence constraint makes necessary; a unit below its declared minimum viability is not presented rather than presented unusably, and the degradation is announced, never silent. The thresholds and the degraded shape are presentation settings (§22). A constrained realization is a purpose-built presentation, not a reflowed one (`foundations/stack.md` "a dedicated UX shell, not a responsive desktop"): each frontend owns the adaptation its own budget calls for (realized in the windowed-desktop profile as a breakpoint, §5.7), while this file owns the contract that a constrained presentation renders the same substrate through a distinct role binding.

### 5.5 The File 37 / File 38 Boundary

This section fixes the line between presentation and customization:

- **File 37 owns**: the composition model and its constraints, the composition operations, unit-kind rendering, built-in `ViewPreset` rendering, the default compositions, budget adaptation, the morphing presentation (§6), the `RendererRegistry`, the interaction models, and the semantic-token *discipline* (renderers consume only tokens).
- **File 38 owns**: user-saved named compositions and the save, switch, rename, and reset flow; presentation contributions and their placement into the slots a role or unit declares; the design-token *system* and the themes; AI-assisted composition and contribution customization; plugin UI placement; and the realization of the surface's `customization_policy` (`worksurface.views-presets`, File 25 §7.4).

The boundary is structural: File 37's composition model renders a composition; File 38 supplies user-customized compositions, contributions, and themes that the model renders through the same contracts. A `SavedComposition`, a contribution placement, and a theme are all settings/customization records (File 15, File 38) that this file's composition model and registry render without special-casing.

### 5.6 Boundary

This section owns the composition model, the built-in presets, budget adaptation, and the customization boundary. File 25 owns the `PresentationUnitKind`/`ViewPreset` model and the `customization_policy`; File 18 owns the unit's prominence; File 15 and File 38 own the saved-customization records. This file renders the composition.

### 5.7 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §5.2. A **panel** is the windowed-desktop realization of a presentation unit: a pane or a tab with a caret, tabs, bars, side-by-side placement and collapsibility. The composition is arranged in a layout container — a recursive split structure whose node is a single panel or a split (horizontal or vertical) of child nodes, each carrying a size or flex weight and a minimum size, with a divider position at each split. Prominence maps onto the container's states: `Present` renders as open or side, `Exclusive` as fullscreen, `Minimal` as collapsed, `Absent` as hidden.

Realizes: §5.2. The container supports resize (drag a divider, with min-size clamping), split and unsplit, reorder, collapse and expand, and detach to a window. The interaction affordances (drag handles, focus indicators) expose the structural semantics §14 requires.

Realizes: §5.4. The presentation budget is the available viewport: at a narrow width, horizontal splits stack vertically, dividers collapse, and the shell presents one primary panel at a time with navigation between them. The breakpoints and the stacked behavior are presentation settings (§22). This profile owns the desktop shell's responsive behavior; a constrained-platform shell (mobile) is a purpose-built presentation declaring its own profile, not a reflowed desktop shell.

**Coder surface.** Realizes: File 27 §4.2. The `editor` unit carries the active file path, caret position, selections, viewport range, and dirty state.

**Coder surface.** Realizes: File 27 §4.2. The `file_tree` unit carries expanded directories and selected files.

**Coder surface.** Realizes: File 27 §4.2. The `worktree_comparison` unit presents a side-by-side comparison of parallel-agent results.

**Coder surface.** Realizes: File 27 §8.2. A version switch updates the materialized view, the on-disk files, and the open editor tabs to match.

**Coder surface.** Realizes: File 27 §9.4. The surface presents multiple branches or parallel-agent results side by side — their diffs, change counts, and previews — with a select-for-merge affordance.

**Coder surface.** Realizes: File 27 §10.4. A preview displays the capture in a resizable view with optional device-frame simulation.

**Coder surface.** Realizes: File 27 §19.2. `EditorDocument` is the open buffer with caret, selections, and viewport, distinct from the on-disk file.

**Web surface.** Realizes: File 28 §4.2. The `browser` unit is the browser viewport over a `BrowserPage`.

**Web surface.** Realizes: File 28 §4.2. The declared scope renders as the academic-versus-web scope toggle.

**Web surface.** Realizes: File 28 §4.2. A report renders with per-section navigation and per-claim citation drill-down.

**Web surface.** Realizes: File 28 §14.4. The Web surface's permitted arrangement includes the browser-and-canvas split.

**Data Processor surface.** Realizes: File 29 §4.2. The `table` unit is a tabular view over a `Table`/`Dataset` artifact: sortable, filterable, paginated columns with inline cell edit and export.

**Data Processor surface.** Realizes: File 29 §4.2. The `pipeline` unit is the data pipeline canvas: a node-graph view over the data pipeline execution structure, a projection of the shared execution-graph canvas with a data node library; the canvas widget is a replaceable implementation behind the panel.

**Data Processor surface.** Realizes: File 29 §4.2. The `profile` unit is the dataset card: a profiling view over a `DataProfile` observation, with per-column statistics, distributions, and detected issues.

**Data Processor surface.** Realizes: File 29 §4.2. The `query` unit is a query editor over the analytical engine: the active query, the result preview, and the inferred schema.

**Data Processor surface.** Realizes: File 29 §4.2. The `file_tree` unit is a workspace data-directory projection carrying expanded directories.

**Data Processor surface.** Realizes: File 29 §16.4. The Data Processor surface's permitted arrangement includes the notebook-and-pipeline split.

**Data Processor surface.** Realizes: File 29 §24. The UI renders the data panels — the table and dataset views, the chart and dashboard renderers, the notebook view, the pipeline and lineage canvases, the profile dataset card, the query and schema-map editors, the activity projection, the command palette, the binding contexts, and the view presets — over the data and behavior contracts File 29 fixes.

**Teacher surface.** Realizes: File 30 §4.2. The `lesson` unit is a lesson reader over a `Lesson` artifact: rendered sections, worked examples, inline runnable code, math, and diagrams.

**Teacher surface.** Realizes: File 30 §4.2. The `curriculum` unit is a concept-map and skill-tree view over a `Curriculum` artifact and the concept-prerequisite graph: nodes are concepts with mastery-derived status, edges are prerequisites, a node opens its lesson.

**Teacher surface.** Realizes: File 30 §4.2. The `classroom` unit's whiteboard/canvas, its spotlighted elements and its student panel are presented together with the shared transcript.

**Teacher surface.** Realizes: File 30 §4.2. The `assessment` unit presents answer entry per question type.

**Teacher surface.** Realizes: File 30 §4.2. The `practice` unit is a practice view: a problem, starter code, progressive hints, a run control over borrowed code execution, and per-test pass/fail.

**Teacher surface.** Realizes: File 30 §4.2. The `flashcard` unit presents the current card front/back, the grade-recall control, and the review-due queue derived from `Mastery` memory.

**Teacher surface.** Realizes: File 30 §11.3. Certain actions are available only in certain scenes: the whiteboard and the slide spotlight are mutually exclusive, and students cannot draw.

**Teacher surface.** Realizes: File 30 §16.2. The classroom preset composes the classroom transcript, whiteboard, and student panel for a multi-agent session.

**Teacher surface.** Realizes: File 30 §16.5. The Teacher surface's permitted arrangement includes the lesson-and-exercise split, and its named contributions are a "today's scheduled learning tasks" or "review due" widget and a classroom or lesson utility widget.

**Teacher surface.** Realizes: File 30 §24. The UI renders the teaching panels — the lesson reader, the curriculum concept map and skill tree, the classroom view with whiteboard and student panel, the assessment and practice views, the flashcard review, the sources and progress views, the activity projection — and the view presets that compose them.

**GUI Control surface.** Realizes: File 31 §4.2. The `screen` unit is the live desktop or target-window view, co-presenting the overlay of detected elements when the inspector is active.

**System Agent surface.** Realizes: File 32 §4.2. The `console` unit is the script builder with preview and the confined command terminal.

## 6. Surface Presentation and Morphing

Anchor: `ui.surface-presentation-morphing`

### 6.1 Definition

Surface presentation is the rendering of an active work surface into the `PrimaryFocus` role: its declared presentation units, its `ViewPreset`, its inspections, and its cross-cutting affordances. Morphing is the transition between presentations as the active surface, view preset, or task changes. This section owns the rendering and the transition; File 25 owns the surface declaration, File 18 owns the live state.

### 6.2 Rule

- The shell renders a surface from three inputs `worksurface.views-presets` (File 25 §7.3) fixes: the surface's `SurfaceContract` (the declared units, view presets, inspections, and cross-cutting affordances), the live `SurfaceState` (the presented units, the primary unit, focus, selection, and `UiMode`, File 18 §5), and the routing decision (the `primary_surface`, File 03 §8). The surface declares the shape; the world model holds the values; the router selects the execution binding; this file renders the composition.
- Morphing is a presentation projection. When the active presentation surface changes — the user activates a different surface, applies a different `ViewPreset`, or the run's task state and produced artifact type change — the shell re-composes the primary focus and the supporting roles and transitions between the two compositions. A morph preserves what the work depends on: focus identity, selection, in-progress input, and every live subscription survive it, and only the composition changes; a morph that would lose one of them is not a morph but a discard, and is invalid. Morphing is driven by the surface, view preset, live state, and, for runs, the task state and artifact type, not by a domain identity alone (`codex_recommendations.md` §10.4's refinement). Morphing changes presentation, never the work model (`intent.presentation`, File 02 §8.1/§8.5; `worksurface.views-presets`, File 25 §7.3).
- A surface's units self-register their live state to the world model when they are activated — when they enter the context's composition, at whatever prominence — and on focus, selection, and content change, and unregister when they are deactivated (`world.observation-state-update`, File 18 §8.1); the shell renders the registered state and never reads a surface's own state back from a rendered image (`perception.tiered-sensing`, File 19 §5.4). A unit or affordance that cannot be represented structurally — that exposes no semantic role, label, interaction kind, and state relationship sufficient for the world model, the control rails, and assistive technology — is invalid (`worksurface.explicit-rejections`, File 25 §20's structural-invisibility rejection; §14).
- Transition and navigation behavior are this file's. A transition resolves its properties from the semantic tokens (§16.5), honors the reduced-motion preference (§14), never gates correctness on elapsed time, and never blocks substrate updates: every role renders live substrate state throughout the transition. The technique a medium uses to perform it is the renderer's.
- This file defines no product auditory-feedback cue, and implementations emit none. A future presentation-design contract may add auditory feedback only where sound is never the sole carrier of information (§14), where application mute and the operating system's quiet modes are honored, and where the cues are suppressible through the accessibility preferences the settings system carries (§14, §22).

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

`InteractionModel` is closed-canonical-plus-`Custom { namespace, name }`. Each lens, canonical or `Custom`, declares what it guarantees while it is active: which scope is presented, where the user's involvement points are, and that steering stays reachable (`controlrail.steering-rail`, File 26 §10) — a lens that guarantees none of the three constrains nothing and is not a lens. It is a UX lens varied freely by the user and the UI; it is never coupled to surface or model identity (`core.explicit-rejections`, File 01 §8), never stored as a backend field, and never a `SurfaceContract` or `ControlRail` field (`worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17).

### 7.3 The Deleted Autonomy Fields and What the UI Renders Instead

The presentation layer carries no participation-level, autonomy-mode, persona, agent-mode, plan-versus-build-mode, or phase field, in any form, at any layer. This is the unanimous, most-evolved position across the canon (`core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `world.surface-state`, File 18 §5.5; `worksurface.no-autonomy-field`, File 25 §13; `controlrail.no-autonomy-field`, File 26 §17; `settings.explicit-rejections`, File 15 §20). The UI renders the *consequences* the deleted fields once described:

- **autonomy** is rendered as the approval posture the policy layer resolves — the effective tier indicator on a control (`policy.effective-tier-resolution`, File 06 §4), the pending approvals the policy layer raises (§12), and the active leases — not as a per-surface or per-rail dial. A "skip approvals" or "auto-approve" affordance the UI presents is a control over the `approval-posture preset` and `agent.unrestricted_mode` of `policy.settings-resolution-for-policy` (File 06 §16.3), rendered as a policy setting, never a presentation-layer autonomy field.
- **progressive disclosure** — the simple-to-power spectrum — is rendered as which units are presented, at what prominence, under which roles and `ViewPreset` (§4, §5, §6), not as a mode. The default presentation is clean and minimal; depth is reachable by presenting more roles, switching to a richer view preset, and raising an inspection unit's prominence (`core.product-thesis`, File 01 §1; `core.invariants`, File 01 §7.9).
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
- The transcript applies a folding-and-grouping pipeline of pure functions before rendering: it normalizes, folds low-stakes and repeated activity (read/search/list groups, background work, hook sequences, consolidations) into summary units the user can open, each with a stable derived identity so an append updates the projection incrementally rather than rebuilding it, groups by natural unit, and reorders for the compaction boundary (realized in the windowed-desktop profile as a collapsible group, §8.6). A derived presentation identity is computed from canonical input references using `CanonicalEncoding`: source block, version, event, or invocation ids; ordered child references for aggregates; the transform id; and the relevant presentation-policy version. It is a deterministic rendering handle for selection, collapse state, and replay alignment, not a new durable content identity. Which kinds collapse is a settings dimension and is extensible; the pipeline never discards a block (the underlying blocks remain individually reachable). Internal blocks that a producer marks not-visible in the transcript (a non-display execution node) render in the inspection and execution views, not the transcript projection; whether a block kind may anchor a transcript message is `block.kind-catalogue` (File 08 §3.1)'s `transcript_anchorable`, and the transcript projection filters non-anchorable and non-display blocks out of itself.
- Inline capability-call rendering presents each invocation through one unit carrying its identity, its typed status (`pending`/`running`/`complete`/`error`), and a result the user can open, driven by the renderer registered for the capability's output kind; a running invocation is continuously indicated as running, in the medium's own idiom, and by the activity-state projection (§8.3; realized in the windowed-desktop profile as a live indicator, §8.6). An `icon_key` a capability declares (`capability.display-fields`, File 05 §3.2) is one such identity element: a medium resolves it to its own symbol form or ignores it without loss of correctness. The rendering of an invocation is the rendering of a `Block` and its `CapabilityInvocation` facts (Files 05, 08, 09); the UI computes no result.
- Message actions — retry, edit, branch, fork, delete (soft by default, with in-session restore), pin, copy (with format and metadata), quote-back, and bulk operations — render the operations `intent.message` (File 02 §3.1) and `run.retry-reroute-branch` (File 04 §19) define and resolve through the rail like any gesture (§11). Parallel and sibling responses render with a variant indicator and navigation between siblings (the version graph's branches, File 11); the transcript renders no parallel history store of its own.
- Message metadata (model, provider, stop reason, token counts, timing, cost estimate) renders as a derived projection (`intent.message` File 02 §3.3; the metadata is computed on demand and cached, not stored on the block, `conversation/02-message-operations.md` realized); the UI renders a compact and an expandable form and computes no token count or cost itself.

### 8.3 Conversation Activity State

The shell renders `intent.conversation-state` (File 02 §2.3)'s coarse activity state — `streaming`, `processing`, `awaiting_user`, `idle` — as a projection over the conversation's active runs, with the first-matching-state priority that section fixes, plus the orthogonal `compacting` and `paused` indicators (a paused conversation is `idle` plus `paused`, never bare `idle`) and any later orthogonal indicators. A single run blocked on user input while another streams leaves the conversation `streaming` and surfaces the blocked condition on that run's own element (File 02 §2.3). The UI renders this projection; it does not collapse conversation state into per-run execution state, and it assumes no single active stream per conversation (`intent.explicit-rejections`, File 02 §9).

### 8.4 The Input Composer

The Conversation rail's input composer (`controlrail.conversation-rail`, File 26 §5) renders: multi-line composition, mention and reference insertion, attachment and ingestion handling (oversized inbound content enters as a governed reference resolved at submission, never inlined into the pending composition), token-command and mention completion, the pre-dispatch transformation choices (duplicate-overlap handling presented as a fast, non-destructive, reversible, send-scoped choice per `context.duplicate-overlap-handling`, File 13 §8 and `kuzeys-context-duplicate-prompt-handling-addendum.md`), the queue-versus-interrupt affordance for mid-execution input (`intent.intent-thread`, File 02 §5.5; `run.retry-reroute-branch`, File 04 §19), and the active `UiMode` indicator. However content enters an in-progress composition, it becomes a governed input reference or a capability proposal: a file or an external object is not read into model context by the fact of its arrival, but is registered as a reference, sensitivity-scanned, and included only through the normal context and capability paths (realized in the windowed-desktop profile as external-content ingestion, §8.6). The composer renders the rail; it owns no submission logic, applies no transformation of its own, and a presented auto-continue countdown is a configurable convenience, never a correctness condition (`core.event-first-by-default`, File 01 §7.15).

### 8.5 Boundary

This section owns transcript and composer rendering. File 02 owns conversation, message, activity state, and the submission lifecycle; File 26 §5 owns the conversation rail; File 08/11 own the blocks and version graph projected; File 13 owns duplicate-overlap detection. This file renders them.

### 8.6 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §8.2. A summary unit the user can open renders as a collapsible group with a disclosure control.

Realizes: §8.2. An invocation renders as a collapsible unit carrying an icon, a title and subtitle, a status, and an expandable result, with running state indicated by a non-spinner shimmer or equivalent live indicator.

Realizes: §8.4. Content enters the composer by paste, drag and drop, file attachment, and external selection import; a large paste presents as a reference token with the content held aside and expanded on submit, never ballooning the composer.

Realizes: §8.4. Token-command and mention completion render as inline type-ahead in the composer.

## 9. Rendering Substrate Primitives into Views

Anchor: `ui.substrate-rendering`

### 9.1 Definition

This section fixes how the typed substrate primitives — blocks, artifacts, the evidence and provenance entities, observations, and version history — render into views through the `RendererRegistry` (§3.3).

### 9.2 Block Rendering

Each `Block` renders through its registered renderer keyed by `BlockKind` (§3.3). A renderer presents the block's content and its derived view-state (lifecycle `Raw`/`Masked`/`Dropped`/`Recovered`, pin state, sensitivity) as projections (`block.block-lifecycle-non-destructive-edits`, File 08 §6.1; `version.consequences-for-later-specs`, File 11); a masked block renders its description, not its content. External-content blocks render a reference and the description, never pulling the blob into the view unless the user opens it. A `Memory`-sourced block renders its content as natural prose in the transcript and does not gratuitously frame it as memory retrieval; memory attribution is allowed and sometimes required — when the user asks what is remembered or why an answer was personalized, when a memory is being edited, deleted, or resolved, when confidence or freshness is uncertain, or when policy or the UI requires inspectability — and the inspector always exposes which memories materially influenced an answer (`memory.natural-use-inspectability`, File 14 §13). This transcript-prose rule is a renderer-level constraint, never a suppression of memory inspectability.

### 9.3 Artifact Rendering

- An `Artifact` (File 09 §3) renders through one of two pipelines, sharing one set of prominence levels (`cross-cutting/artifacts.md` realized): the **interactive-artifact runtime** for executable, interactive content, and **type-specific renderers** for documents, tables, diffs, images, media, and structured data. The pipeline is selected by the artifact's kind and media type through the `RendererRegistry`; the mapping is a registry table, extensible by registration.
- Three uniform prominence levels are available across both pipelines: **embedded in flow** (the artifact presented within the transcript at `Minimal` prominence, openable), **adjacent and persistent** (the artifact presented co-present with the conversation at `Present` prominence, with multiple artifacts navigable among themselves), and **exclusive** (the artifact holds the whole of primary focus at `Exclusive` prominence, with a return path). The user changes level the same way for any artifact, and the placement each level implies is the composition's (§5.2), never this section's (realized in the windowed-desktop profile as a display mode, §9.7). Artifact and file edits render live as new versions commit (File 11); switching versions re-renders the artifact at the chosen version.
- The interactive-artifact runtime renders the artifact inside the one `Sandbox` contract (File 23) at a least-authority origin, with a restricted host bridge: the runtime may read and write its own artifact, emit a `Custom { namespace: "artifact.runtime", name, payload }` event, and request its own state be persisted (with consent), and has no other access — no network, no other files, no block store, no agent, no secrets — unless the user explicitly grants it (`security.egress-governance`, File 22 §11; File 23). Runtime events carry `artifact_id` as an envelope cross-reference key, payload field, or source identity; they are sensitivity-defaulted, carry no authority, are never read as instruction, cannot impersonate system events, and cannot trigger security-category hooks (`security.untrusted-content`, File 22 §12; File 10 §8.3). Persistent interactive-artifact state requires explicit user consent and is stored as substrate, not a private UI store. The runtime is a confined renderer and a consumer of the sandbox contract, not a parallel execution architecture (`sandbox.consequences-for-later-specs`, File 23 §21).

### 9.4 Evidence, Claim, Citation, Observation, and Provenance Rendering

The entity layer renders through the `artifact.per-surface-projections` (File 09 §17.2) lenses: claims render as assertions with confidence and status; evidence and citations render as linked support with source span and trust; observations render through their viewers (a captured page, an accessibility-tree overlay, a screenshot series, a machine snapshot, a database result); provenance renders as the derived lineage view (File 09 §15) — why an output exists, what supports it, what it derives from. Validation and critique render as indications and units deriving the artifact's validation and review state (File 09 §14). The UI renders these as projections; it derives no confidence, status, or lineage of its own.

### 9.5 Version History, Comparison, and Forensic Reconstruction

History, comparison, and undo affordances render as projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24): a version timeline (a linear list and a branch-tree view, switchable as a rendering toggle), per-version operation summaries and diffs, the comparison board for parallel branches, runs, or agents, the read-only state-visualization overlay ("what the state was at this version"), and the forensic reconstruction ("what the model saw at this point," File 11's replay surface). Undo, redo, restore, revert, branch, and switch render the version-graph operations Files 04 and 11 define; the UI introduces no parallel checkpoint, snapshot, or undo store, and renders no per-tool-call version (`version.explicit-rejections`, File 11 §23).

### 9.6 Boundary

This section owns substrate rendering. Files 08, 09, 11 own the blocks, entities, and version graph; File 23 owns the sandbox the interactive runtime runs in; File 22 owns the secret and untrusted-content rules; File 38 owns contribution renderers and themes. This file renders them through the one registry.

### 9.7 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §9.3. The three prominence levels render as inline (a compact card with title, preview, and expand control in the transcript), side panel (a resizable region alongside the conversation, with multiple artifacts navigable within it), and fullscreen (the artifact fills the focus region with a back control).

**Coder surface.** Realizes: File 27 §7.4. A retrieval hit is highlightable where it was found.

**Coder surface.** Realizes: File 27 §8.3. The diff panel and diff viewer are the revert UI.

**Coder surface.** Realizes: File 27 §11.3. Diagnostics are highlighted in the editor and terminal panels.

**Coder surface.** Realizes: File 27 §12.2. Review findings render as inline comments anchored to code ranges in the diff and editor panels, and as a review summary.

**Web surface.** Realizes: File 28 §10.5. On the research canvas, queries, sources, extracts, claims, clusters, takeaways, and contradictions render as nodes, and their relations (cites, corroborates, refutes, derives) render as edges.

**Teacher surface.** Realizes: File 30 §7.4. Code in a lesson renders as syntax-highlighted code with inline execution over borrowed code execution.

## 10. Streaming and Live Presentation

Anchor: `ui.streaming-presentation`

### 10.1 Definition

Streaming presentation is the rendering of live substrate change as it happens: the event stream, the streamed partials, and the transition from partial to committed state. This section owns the rendering and its performance contract; File 10 owns the events and the partial-to-committed boundary.

### 10.2 Rule

- The presentation layer renders the live event stream (`ledger.event-stream`, File 10 §5) reactively and event-first: a view subscribes to the events scoped to its concern, demultiplexes by the envelope's identifiers (`ledger.event-envelope`, File 10 §5.2 — conversation, run, step, node, and where present worktree and backend identifiers), and re-renders on receipt. It never polls for live state. Reconnection after a transport interruption rebuilds the affected views from the durable substrate and execution ledger, resumes subscription from the latest available sequence, and re-syncs stale subscriptions against the substrate. If transient partial chunks were missed and cannot be reconstructed, the renderer shows a typed stream-gap presentation marker until committed blocks or final results replace the partial view. The marker is presentation state, not a durable block unless the event or execution system explicitly records it.
- Streaming renders typed partials, not only token text (`codex_recommendations.md` §10.2; `ledger.streaming-live-partials`, File 10 §12): text deltas, reasoning deltas (rendered distinctly from the response and at `Minimal` prominence by default, openable by the user), plan deltas, task-state deltas, artifact and diff previews, validation results, and observation snapshots each render through the renderer for their kind. A reasoning or thinking partial is presentation the user may open; it is presented distinctly from the response and is never asserted as the answer.
- The partial-to-committed transition is rendered as a single continuous view: the streamed partial renders incrementally as deltas arrive, and on the committed-block boundary (`ledger.streaming-live-partials`, File 10 §12) the view transitions the same element to the committed block without the user perceiving a rebuild. The UI treats the durable committed block as the source of truth and the partials as the live projection that converges to it; it never persists a partial as truth.
- High-frequency rendering is throttled and aggregated for performance without losing data: continuous position change is decoupled from re-render, a projection over a large ordered set materializes only the attended range, is stable under expansion, and never presents an empty view for content that exists, jump-to-item resolves by stable item identity rather than by any positional offset, streamed output is presented at a cadence bounded independently of its arrival rate and segmented at meaning boundaries, and high-frequency event categories are coalesced for display per the aggregation policy (`ledger.streaming-live-partials`, File 10 §12). These are rendering-performance requirements, not data policy; no rendered content is dropped, only its render cadence is bounded (realized in the windowed-desktop profile as virtualization, §10.6). A view that is not presented, and a presentation context that is not being attended, suspend their presentation work while preserving durable subscription and replay or sequence position, so presenting the view or attending the context again re-syncs against the substrate without a gap.

### 10.3 Attention Following

The transcript and live views follow the live edge while the user's attention is at it, stop following when the user moves attention away, and re-engage when the user returns to it. Following distinguishes a user-initiated position change from a renderer-initiated one: a renderer's own change never registers as a user action, so an arriving item never displaces content the user moved to in order to read it (`ui/14-3-streaming-ui.md`, `claude-code-frontend-addendum-part2.md` realized). An in-progress selection or an equivalent held engagement pauses following, because it is an attention the arrival must not break. The band around the live edge that counts as being at it, and the affordance that returns to it, are the medium's (§22, §10.6).

### 10.4 Parallel Presentation

Parallel activity renders readably and never as one forced flat stream (`intent.presentation`, File 02 §8.4). The shell renders the parallel shapes `intent.parallel-work` (File 02 §7) allows — concurrent runs, sibling responses, fan-out, multi-agent transcripts, comparison branches — as separately addressable, independently navigable projections over the runs and blocks involved, each with its own attention position and none serialized into the others. Activity outside primary focus is summarized with a live indication of its current operation and progress and an entry point that gives it focus; it never blocks primary focus and it is never dropped from the presentation because it is not focused (realized in the windowed-desktop profile as an orchestration board, §10.6).

### 10.5 Boundary

This section owns streaming and parallel presentation. File 10 owns the events, the envelope, the partial-to-committed boundary, and the aggregation policy; File 02 owns the parallel-work shapes and activity state; File 16/17 own the model and usage facts. This file renders them.

### 10.6 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §10.2. Long transcripts and lists are virtualized: only the visible window plus an overscan is mounted, with a stable list origin and clamped mount expansion so a jump to a distant entry never flashes blank.

Realizes: §10.2. Visual scroll is decoupled from re-render — scroll position updates the view directly and re-render is quantized to coarse bins — and text streams render at a paced, word-boundary-snapping cadence rather than per-token.

Realizes: §10.2. Windows that are minimized or fully occluded suspend their render loops.

Realizes: §10.3. The attention position is the scroll position and the live edge is the bottom of the scroll; auto-follow re-engages when the user returns to the bottom band, and text selection pauses it.

Realizes: §10.4. Parallel activity renders through grouped activity summaries, side-by-side or stacked panes (independently scrollable), a comparison board, a classroom or debate view, and an orchestration board; activity outside the focus surface renders as a badge or summary.

**Coder surface.** Realizes: File 27 §6.6. Streamed content appears live in the editor.

**Coder surface.** Realizes: File 27 §6.6. The partial-write event is what the editor panel consumes for incremental rendering; it introduces no progress bar.

**Coder surface.** Realizes: File 27 §15.3. Sub-agent activity renders as a collapsible group.

**Web surface.** Realizes: File 28 §14.3. Research sub-agent activity renders as a collapsible group.

**Data Processor surface.** Realizes: File 29 §16.3. The activity projection shows data results as table previews and charts inline, and renders batched approval requests and pipeline-node and child-run activity as collapsible groups.

**Teacher surface.** Realizes: File 30 §4.2. The `classroom` unit's shared transcript of the coordinator and role-differentiated agent runs is presented as one live stream.

**Teacher surface.** Realizes: File 30 §16.4. The activity projection shows lessons as rendered previews with figures inline, batched approval requests for bulk generation, and classroom and curriculum child-run activity as a collapsible region.

## 11. Control-Rail Presentation

Anchor: `ui.rail-presentation`

### 11.1 Definition

Control-rail presentation is the rendering of the control rails' surfaces and the routing of gestures into them. The presentation layer renders each rail; File 26 owns the rail primitive, the resolution contract, the gesture grammars and the binding map, the token grammar, the spoken session, and the steering contract.

### 11.2 Rule

- **The discovery rail.** The shell resolves the `Discovery` rail within the user's current context, without displacing or relocating it: it searches the available-capability list (`world.state-aware-capability-availability`, File 18 §9) filtered to the discovery lens (`surface.presentation-in-user-facing-surfaces`, File 07 §12.1), ranks by match quality, recency, and frequency as a presentation convenience, presents each entry's resolved effective-tier and availability indicators (read from File 06, never recomputed), and elicits missing required arguments before dispatch (§12). A quick-open variant searches a registered catalog (files, recent entities, artifacts) and resolves to an open or reveal invocation. The discovery surface renders the `controlrail.command-rail` (File 26 §6) surface; it composes no visibility and decides no authority (realized in the windowed-desktop profile as a command palette, §11.5).
- **Direct affordances.** Every action surface, in whatever form and at whatever origin, is a projection of the available-capability list filtered to the current `Selection`, policy state, surface binding, and user settings (`worksurface.actions-declaration`, File 25 §6.4; `controlrail.command-rail`, File 26 §6.4), and shows the same policy indicators the discovery surface shows. Copy, quote, explain, ask, cite, export, save-to-memory, and equivalent actions appear only when their capabilities are available and allowed. A selection-scoped action is reachable through every modality the context declares, never through one input device alone. Renderer-provided copy and export projections inherit sensitivity, provenance, and egress governance; raw secret or restricted content never bypasses File 22 filtering. An affordance the host platform provides bridges to the same capability invocation and gets no separate path (realized in the windowed-desktop profile as a menu, §11.5).
- **Gesture capture and the binding editor.** The shell captures the gestures its declared `GestureGrammar`s admit and resolves them through the binding map (`controlrail.keybinding-keymap`, File 26 §7): a binding context contributes itself to the active context stack as the surface, unit, or dialog that owns it becomes active, and the shell renders the binding editor (rebinding, conflict surfacing, unbind, and per-profile validity diagnostics) over File 26's binding model. Input capture, the active context stack, and any pending multi-step gesture state are per presentation context: a multi-step gesture begun in one context completes, aborts, or lapses only within that context, each context owns one rail session, and a context's context stack is contributed by the surfaces, units, and dialogs active in that context alone (`controlrail.keybinding-keymap`, File 26 §7.3, §7.4). Where a grammar declares a lapse condition on an incomplete gesture, it is a configurable convenience of that grammar and never a correctness condition (`core.event-first-by-default`, File 01 §7.15; §23). The resolver is File 26's and stateless; the capture, the per-context stack contribution from live presentation and focus, and the editor presentation are this file's (realized in the windowed-desktop profile as a keyboard capture, §11.5).
- **The spoken session and handsfree operation.** The shell renders the session over a speech `GestureGrammar` (`controlrail.voice-rail`, File 26 §9), over the capture, transcription, and consent File 19 owns and the session File 26 owns. A capture session is continuously and unambiguously indicated for as long as it is capturing; its interim interpretation and its confidence are inspectable; its output is presented in at least one non-auditory form; and confirmation precedes any consequential resolution. The shell renders the `Handsfree` `UiMode` and, where the declared profile provides a dedicated capture context, binds the session to it (§4.5). The UI renders the session; it owns no capture, transcription, or intent resolution (realized in the windowed-desktop profile as a recording indicator, §11.5).
- **Steering affordances.** The shell renders stop, cancel, pause, resume, interject, takeover, and barge-in as affordances resolving to `Steer` outcomes (`controlrail.steering-rail`, File 26 §10): the cancellation targets (run, child-run tree, specific child run, tool call, sandbox/process) with the default and expanded options, the cooperative-then-forceful state, and the queue-versus-interrupt choice for mid-execution input. A presented countdown is a configurable presentation of File 04's safety guard, never a correctness condition. The UI renders the affordance; File 04 carries out the intervention.
- **Token commands, mentions, and attachments.** The composition surface renders the token-command and mention completion affordance and the attachment surface (`controlrail.slash-command-rail`, File 26 §8; §8.4), resolving through the rail; the token's spelling is the grammar's, not this file's. Custom-command definitions render with source attribution and precedence; a prompt-template command's contributed text renders as attributed content, never as a hidden instruction.

### 11.3 Available-Action Enable/Disable

The shell renders an action's availability from the serialized availability predicate the action registry exposes (`cross-cutting/actions.md` realized; `world.state-aware-capability-availability`, File 18 §9), so an action becomes available or unavailable against the current `SurfaceState` and `UiMode` without round-tripping per state change. An unavailable action is presented as unavailable, with its typed reason, never as an action that fails on invocation; the unavailability is carried by text and structural semantics and never by one perceptual channel alone (§14; realized in the windowed-desktop profile as a greyed control, §11.5). Availability re-renders event-first on the recompute event (File 18 §12); the shell does not poll.

### 11.4 Boundary

This section owns rail rendering and the available-action enable/disable contract. File 26 owns the rails, the gesture grammars and the binding map, the token grammar, the spoken session, and the steering contract; File 07 owns the lens; File 18 owns availability; File 19 owns capture; File 05/06 own the capability and its policy. This file renders the rails.

### 11.5 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §11.2. The discovery rail renders as the command palette: an overlay, never a separate window, over the current focus surface.

Realizes: §11.2. Direct affordances render as menu items, toolbar buttons, context-menu entries, and selection-scoped floating actions; a native menu or tray item bridges to the same capability invocation.

Realizes: §11.2. Gesture capture is keyboard capture over the keyboard grammar's instance (`controlrail.keybinding-keymap`, File 26 §7's windowed-desktop profile); the pending multi-step gesture state is a pending chord, and the binding editor renders rebinding, conflict surfacing, unbind, and platform-validity diagnostics.

Realizes: §11.2. The spoken session renders as the recording indicator, the live transcription preview, the confidence and disambiguation surface, the spoken-output and caption presentation, and the confirmation step, with a companion-capture window (§4.7) where configured.

Realizes: §11.2. Token commands render as slash-prefixed tokens with inline type-ahead in the composer, and mentions the same way.

Realizes: §11.3. An unavailable control renders greyed with its reason, alongside the text and structural semantics §14 requires.

**GUI Control surface.** Realizes: File 31 §12.2. The take-over affordance and the active-control indicator are presented in the activity panel, beside the run's step stream.

**System Agent surface.** Realizes: File 32 §13.2. The take-over affordance and the active-control indicator are presented in the `activity` panel, beside the run's safe-operation lifecycle steps.

**Teacher surface.** Realizes: File 30 §24. The Teacher surface's rails render as the command palette and the keybinding contexts.

## 12. Dialog, Elicitation, and Attention Presentation

Anchor: `ui.dialog-elicitation-notification`

### 12.1 Definition

This section fixes how the system's requests for typed user input — approvals, clarifications, choices, corrections, interventions, credential and confirmation prompts — and its non-preemptive attention items are presented, and how the UI arbitrates which request currently holds focus.

### 12.2 The Focused-Dialog Selector

The pending-request set and its resolution are owned by the policy and elicitation systems (Files 06 and 26) and shared through the event bus. The focused-dialog selector is per presentation context, and every `Interactive` presentation context — whatever its medium — computes presentation focus over the same shared pending set. Answering a request in any compatible context emits the one typed response and resolves the request for all of them, so a request is never double-answered and never left stale in another context.

Blocking presentation of a request is a service-layer assignment, never a per-renderer inference: a transient `DialogPresentationAssignment { request_id, owner, assignment_generation }` grants blocking presentation to exactly one compatible presentation context — the context presenting the request's originating scope, else the attention target (§4.4) — under one logical ordering, and reassigns with an incremented generation when the owner closes, disconnects, or becomes incompatible while the request remains pending. Renderers render the assignment; they infer no ownership. Every other context presents the same request as a non-preemptive pending item, answerable in place or resolvable by a reveal action that leads to the assigned context; exactly one context holds preemptive presentation of a request at a time, and an answer from a superseded owner remains request-id validated without reviving stale presentation ownership. A blocking request and preemptive presentation are distinct: a request may block execution while being presented non-preemptively (§12.3); preemption is presentation only. The selector replaces per-request visibility flags with a single computed focus (`unit13-ui.md` D13.5; `unit15-ux-distribution-files-glossary.md` D15.UX.1 realized). It uses a deterministic priority tuple: blocking/security class, capability or policy severity, user-visible urgency metadata, dependency relationship to the active run, then enqueue sequence. Enqueue sequence is a logical sequence number, not a wall-clock correctness condition. Pending lower-priority requests stay presented as pending items (realized in the windowed-desktop profile as a modal, §12.6); dialogs revalidate before presentation and before action. Security, approval, credential, payment, destructive, and typed-confirmation dialogs never auto-approve, auto-deny, or silently expire because of UI timing.

### 12.3 Rendering the Contracts

- The presentation layer renders the `policy.approval-ui-surface-contract` (File 06 §13) data contract verbatim — `ApprovalRequest`, `LeaseOption`, `ApprovalResponse`, `BatchApprovalRequest`, `BatchApprovalResponse`, and `ContradictionResolutionRequest` — and the `controlrail.elicitation` (File 26 §13) contract — the `Elicitation` with its closed-canonical-plus-`Custom` kind set (approval, clarification, choice, correction, intervention); the credential, payment, confirmation, file-picker, and multi-step-wizard flows the sources name are rendering cases of these kinds or registered `Custom` kinds, not additional baseline members. It never invents a parallel approval or elicitation data shape (`policy.consequences-for-later-specs`, File 06 §18; the File 06 §13.6 rule that the policy layer emits typed events and the UI renders and responds). The approval and elicitation dialogs are baseline-only kinds: they render through the canonical baseline renderer only, and no surface, rail, or plugin contribution may override or shadow them (§3.3).
- An approval renders the capability identity, the resolved arguments (with declared-sensitivity redactions applied), the stated reason, the resolved tier and floor, the touched resources, the available lease options, and any contradictions; it offers the typed response options the contract defines (allow once and the lease-scope grants, deny once and the deny-scope grants, with the lease-narrowing affordance) and the typed-confirmation entry where required. A batched approval presents the constituent requests together as a set with per-item resolution and a set-level accept or deny, and does not preempt the rest of the presentation (`policy.batched-approval-flow`, File 06 §5.5; `unit04-routing-agents-prompt.md` D4.5). A change-review approval renders the before/after diff and per-change accept, reject, or modify where the producing surface supplies the diff.
- An elicitation maps its kind to the input affordance its medium provides — a choice to a selection among the offered options, a correction to an in-place amendment of what it concerns, an intervention to a steering handoff — while credential entry stays the one controlled write-only ingress in every medium (`security.process-ipc-trust-boundary`, File 22 §13.2; realized in the windowed-desktop profile as a masked field, §12.6), and is answerable through any compatible rail; the response flows back through the one typed response channel and is linked to the request identity, never issued as a new unrelated command (`controlrail.elicitation`, File 26 §13.2). A persistent request survives restart and re-renders.
- The response to any request is dispatched as the typed response event the contract defines; the presentation layer enforces no policy and grants no authority — it renders the request and returns the user's typed choice (File 06 §13.6).

### 12.4 Non-Preemptive Attention

Non-preemptive attention is projected over the event stream (§10) in three distinct classes, none of which preempts what the user is doing: **persistent pending state** (activity that is outstanding or unread, presented for as long as it is outstanding), **transient completion and recoverable conditions** (background work that finished, or a condition the user may recover from, presented once and not required to persist), and **provenance-carrying follow-up** (an item that declares where it came from so the user can act on it later). Each class declares its provenance and its resolution path, and the presented form of each is the frontend's (realized in the windowed-desktop profile as a badge, §12.6). An unresolved projection its owning spec classifies attention-requiring — File 33's current `AttentionRequired` items among them (`automation.observability`, File 33 §17.3) — is presented under the persistent class until its owning projection resolves; acknowledgement may change presentation state but not the circuit, and no acknowledgement, dismissal, or presented form retires an item its projection still holds.

Attention payloads are sensitivity-filtered summaries. An attention surface the host platform provides, outside this application's own presentation and outside its authentication state, exposes no secret, restricted, or policy-hidden content. Actions invoke capabilities through the rail and revalidate availability, policy, and substrate state. Owning specs own event/projection truth and external dispatch; this file owns in-shell rendering.

### 12.5 Boundary

This section owns the dialog, elicitation and attention rendering and the focus selector. File 06 owns the approval contract and the policy decision; File 26 owns the elicitation contract; File 04 owns the intervention; the event-owning specs own the attention events. This file renders the requests and returns typed responses, inventing no parallel shape.

### 12.6 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §12.2. Preemptive presentation renders as a modal in the assigned window; every other window renders the same request as a non-blocking queue or badge entry, with a reveal action that raises the owning window. A request never renders as a modal in more than one window at a time.

Realizes: §12.3. A choice renders as clickable or tappable options, a credential through the platform-native masked field, and a correction inline.

Realizes: §12.3. A batched approval renders as a non-modal surface that leaves the rest of the UI navigable.

Realizes: §12.4. The three attention classes render as a badge for persistent pending state, a toast for transient completion and recoverable conditions, and a notification carrying provenance for follow-up; the operating system's notification centre and lock screen are the external attention surfaces the sensitivity filter covers.

**Web surface.** Realizes: File 28 §17.3. A profile setup wizard guides the user through manual authentication for a profile.

## 13. Inspector and Management-Surface Presentation

Anchor: `ui.inspector-presentation`

### 13.1 Definition

A management surface is a user-facing presentation of a substrate service's data and capabilities — an inspector, a browser, a dashboard, or a console — presented under the `Inspection` role, by whatever context declares it. This section owns the rendering; the substrate-service specs own the content, and File 25 §14 classifies these as management surfaces, not work surfaces.

### 13.2 Rule

- The shell renders the substrate-service management surfaces as projections over their services (`worksurface.management-surfaces`, File 25 §14): the context inspector, the source and knowledge browsers, the memory browser, the world-model inspector, the settings surface, the capability-registry and source and connector managers, the storage-accounting view, and the automation and workflow dashboards. Each renders its service's state through the `RendererRegistry` and self-registers its unit state (§3, §6); none is a focus work surface, none registers a `SurfaceContract`, and presenting one gives the host run no new primary surface.
- The **context inspector** renders the assembled context as an explainable projection (`codex_recommendations.md` §10.9; `ui/context-management.md` realized): the block tree with per-block token counts, pin and lock state, and content previews; the budget projected per category with the live dry-run preview (`context.consequences-for-later-specs`, File 13 §22); and, per included or omitted element, why it is in or out, what replaced it if compacted, what it supports, and whether it is conversation, retrieved content, memory, or evidence. The user's block operations (pin, mask, drop, recover, reorder, edit, delete) render the operation vocabulary Files 08 and 11 define and resolve through the rail; the inspector is the surface for those user invocations (`cross-cutting/blocks.md` realized).
- The **observability surface** renders the execution and quality projections (`codex_recommendations.md` §8.12; `run.presentation`, File 04 §25): traces and execution timelines, validations, retrieval inspections, prompt and context reconstructions (the forensic "what the model saw," §9.5), policy decisions, run comparisons, evaluation results, and usage/cost/latency metrics, each a projection over the ledger and version graph. The **debug surface** renders the live event log (a bounded ring buffer with filtering, search, and high-frequency aggregation), the performance monitor, and the debug toggles (`ui/14-5-debug-and-performance.md` realized); it is reachable only through an explicit developer entry point; while inactive it installs no subscription, no capture and no retention, so it costs nothing; and while active its cost is a declared, settings-bounded budget (§22) rather than an unstated one. Debug and observability surfaces render filtered projections by default; raw payload inspection, copy, export, or sharing reuses File 22 egress governance, File 06 policy, and the relevant sensitivity labels. Enabling deeper capture is an explicit state change with visible scope and retention.
- A management surface renders only what its service exposes and computes nothing of its own; it honors sensitivity (a `Secret`-classified value renders masked, File 22) and emits the user's operations as capability invocations.

### 13.3 Boundary

This section owns management-surface rendering. The substrate-service specs (Files 06, 07, 12, 13, 14, 18, 20, 21, 33, 34, 35, 36, 40, and 41) own the content; File 25 §14 classifies them; File 11 owns the version-graph replay the reconstruction view renders; Files 40 and 41 own the data the observability surface renders. This file renders them.

## 14. Accessibility

Anchor: `ui.accessibility`

### 14.1 Definition

Accessibility is a first-class, dual-purpose invariant of the presentation layer: the UI must be operable and perceivable by human assistive technology and structurally legible to the agent and the world model. It is not an add-on (`codex_recommendations.md` §10.6; `ui/accessibility.md` realized).

### 14.2 Rule

- Every presented unit and affordance exposes the structural semantics `worksurface.explicit-rejections` (File 25 §20) requires — a stable semantic role, an accessible label and description, the interaction kinds it supports, focus behavior, and its state relationships — sufficient for the world model and control rails (so the agent can perceive and operate the UI through structure, not captures) and for assistive technology (so an assistive client operating in any modality can operate it). An affordance that cannot be represented structurally is invalid (the structural-invisibility rejection, File 25 §20; §6.2). This dual-purpose semantic layer is the same surface the self-registration contract (File 18 §8.1) and the accessibility tree consume.
- The medium-independent accessibility invariant is four obligations, and every frontend meets all four whatever its medium: **structural semantics on every unit and affordance**, as the bullet above requires, exposed for assistive technology and for the world model alike; **complete operability by at least one non-default modality**, so no operation is reachable only through the medium's primary input and readable, actionable language with input assistance and labelled inputs holds in each; **no capture the user cannot exit**, so any state that takes input exclusively declares and presents the way out of it, and preemptive presentation confines its capture to the presentation context that owns it and returns attention within that context when it closes, never transferring into another context because the attention target moved meanwhile (§12.2); and **a text equivalent for every non-text element**, so no information is carried only in a form a text channel cannot render and no state is carried by one perceptual channel alone. A live update is announced when the user must act on it, when it completes something they were waiting on, or when it failed; a high-frequency stream of deltas is never announced item by item but is announced as a bounded summary. Beyond the four, every frontend declares the accessibility conformance profile its medium admits and meets it — WCAG 2.1 Level AA is the windowed-desktop profile's (§14.4) — and the active profile may target newer WCAG AA versions, Section 508, ATAG, or equivalent jurisdictional or authoring profiles through settings and validation; it does not create a parallel accessibility architecture. A later or per-surface spec cites these four obligations and adds only the obligations its own subject creates; it does not restate them (realized in the windowed-desktop profile as a conformance profile, §14.4).
- The presentation layer honors the perceptual and motor preferences its medium exposes, as settings (§22): a reduced-motion preference suppresses non-essential transition (§6.2), an information-scale and density preference re-composes accordingly, a perceptual-emphasis preference selects the medium's highest-separation presentation, and reading-level and dyslexia-support preferences (carried in the learner persona where present, `unit11d-teacher.md`) adapt presentation; the visual axes are one medium's set of these and never the whole of them (realized in the windowed-desktop profile as a high-contrast preference, §14.4). Alternative-modality operation is an accessibility path, not a feature: every operable affordance is resolvable through each entry class the client session registers (`controlrail.registry`, File 26 §14), and a spoken utterance maps to an available capability the same way any other gesture does (§11.2).
- Accessibility is verified, not assumed: a conformant presentation passes the automated checks of its declared conformance profile and is operable end to end through at least one non-default modality, exercised end to end and not merely declared. The accessibility contract applies to every surface, unit, dialog, and state, including loading, empty, and error states (§17), projections over large ordered sets, alternatives to every direct-manipulation gesture, selection-action surfaces, focus restoration, and the structural semantics an assistive client consumes.

### 14.3 Boundary

This section owns the accessibility contract for the presentation layer, and states the four medium-independent obligations once for the whole corpus. File 18 owns the self-registration the structural layer feeds; File 26 §9 owns the spoken session accessibility composes; File 19 owns capture; the per-surface specs cite the four obligations and declare only the surface-specific accessibility obligations their own subject creates (a surface's accessibility concerns are this contract applied to its units). This file fixes that accessibility is a rendering invariant.

### 14.4 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §14.2. The declared conformance profile is WCAG 2.1 Level AA: text-alternative for non-text content; minimum contrast ratios with no color-only information (status carries an icon and text, not color alone); full keyboard operability with a logical focus order, a visible focus indicator, and no keyboard trap; pointer targets meeting the minimum size; readable, actionable language with input assistance and labeled fields; and semantic structure with correct roles. Modals trap focus, restore it on close, and are announced — within their own window only.

Realizes: §14.2. The perceptual preferences this medium exposes are a high-contrast preference selecting a high-contrast presentation and a font-scale and density preference that reflows accordingly; the non-default modalities this profile is verified against are keyboard operation and screen-reader operation, exercised end to end.

**Teacher surface.** Realizes: File 30 §16.4. The accommodations are keyboard and screen-reader operability, and the broader UI accessibility baseline the UI specs own.

**Teacher surface.** Realizes: File 30 §16.4, §17.3. Read-aloud of lessons and feedback uses the borrowed text-to-speech capability with the transcription always available alongside the audio (`controlrail.voice-rail`, File 26 §9).

## 15. Internationalization Presentation

Anchor: `ui.i18n`

### 15.1 Rule

- Every user-facing string the presentation layer renders is a localizable key, with no exceptions: UI copy, control labels and descriptions, error and notification messages, tooltips, accessible labels, and placeholder text (`atlas3-core/CONSTRAINTS.md` §2 realized; `cross-cutting/i18n.md`). The discipline extends to the strings the substrate exposes for rendering: capability display names, policy explanations, and provenance and validation strings render through the same localization discipline (`codex_recommendations.md` §10.7; `capability.display-fields`, File 05 §3.2's localizable-descriptor rule). A rendered string that is not a key, or a hardcoded user-facing literal in presentation logic, is invalid.
- The active locale is resolved from the settings system (the `ui.language` dimension, File 15), not from a renderer-private store; the renderer reads the locale reactively and re-renders on change. Locale resolution supports a fallback chain to a default locale, and the chain's terminal arm is a typed, visible miss outcome rather than a silent degradation: the fallback text still renders, the miss is typed and surfaced rather than swallowed, and development renders the diagnostic inline rather than a blank. The presentation layer renders right-to-left and locale-aware formatting (dates, numbers, week boundaries) per the resolved locale. Every client shares the same keys whatever its medium (§16).
- Localization is part of the rendering contract, not a per-surface concern: a surface, rail, or plugin that contributes a renderer or a control contributes its strings as keys, and translation completeness is verifiable.
- Localization keys do not replace source-copy discipline. User-facing copy follows one product-language contract across the shell, the surfaces, policies, errors (§16.3), attention items (§12.4), onboarding (§17.1), and help: one preferred term per product concept; the same action uses the same label; and an actionable message states what happened, any material consequence, and the available recovery. Context may alter tone, but must not obscure authority, risk, provenance, or who will act. A versioned term index and message-pattern guide are normative inputs to the string-key catalogue: they are shipped artifacts owned by the same source that owns the shipped catalogue, versioned with it so a catalogue always names the index revision it was written against, and a shipped catalogue is validated against that revision — one term per concept, one label per action, and the actionable-message pattern — as a release obligation. The validation runs with the override layer disabled, because a user override never satisfies it.
- Copy resolution consults the user's copy-override layer before the shipped catalogue: for the resolved locale, an override whose locale tag matches exactly supersedes the shipped string for that target, and every target with no override falls through to the shipped catalogue and its fallback chain unchanged, per key. An override supplies a message template, never an already-formatted instance, so placeholder, plural, and select contracts resolve after substitution exactly as they do for shipped copy. Overriding a label changes rendered copy and nothing else: capability identities, the token grammar, voice aliases, bindings, policy and audit semantics, and automation references are unchanged, and the discovery surface and search match both the custom and the canonical text while displaying the custom label. Resolution reserves a source-approved catalogue-provider layer between the override layer and the shipped catalogue, which the future translation packs fill (File 38 §3.4). This file owns the resolution order and the rendering; File 38 owns the override records and their persistence (`customize.customization-substrate`, File 38 §3.4).
- Copy customization never overrides the semantics of a baseline-only sensitive renderer (§3.3, §12.3). An approval, denial, masked-secret, or trust and provenance control renders its friendly label through the override layer like any other control, and renders alongside it an immutable semantic companion derived from typed state — the decision outcome and lease scope, the capability identity, tier, floor, and touched resources, the secret and redaction state, the trust and provenance indications, the typed-confirmation challenge and its response mapping, and the accessible role, state, and interaction behavior — that no override alters, conceals, or rewords (`policy.approval-ui-surface-contract`, File 06 §13; `secret.backend-boundary`, File 22 §4). The accessible name or description carries both the custom label and the canonical consequence, and the cue is text plus structural semantics and never color alone (§14). A protected control whose friendly label is customized says so and offers direct access to its canonical target and default. Every protected-flow record retains the effective override revision or reference used in presentation, so forensic reconstruction shows what the user saw.
- Shipped and user-authored copy are distinct provenance classes, and the product-language contract binds the shipped class. The Atlas-shipped catalogue satisfies completeness and that contract evaluated with the override layer disabled: a user override never supplies a missing translation, never satisfies or masks a completeness or terminology failure, and an imported catalogue never establishes that shipped copy is complete. User-authored overrides are the user's words and carry no terminology or style enforcement; they are validated structurally instead (`customize.customization-substrate`, File 38 §3.4), and terminology guidance may render as a non-blocking preview, never as a save prohibition.

### 15.2 Boundary

This section owns the internationalization rendering contract, including the resolution order that consults the copy-override layer. File 15 owns the `ui.language` definition and its settings resolution; File 05 owns the localizable display-field descriptors; File 38 owns the copy-override records, their validation, and their lifecycle; the contributing specs own their strings as keys. This file renders them localized.

## 16. The Renderer-to-Backend Boundary and Frontend Architecture

Anchor: `ui.renderer-boundary`

### 16.1 Definition

The renderer-to-backend boundary is the contract between the presentation layer and the service layer: the renderer is an adapter that calls the service layer and renders its outputs, holding no business logic and no durable state. This section fixes the boundary and the provider-invariant frontend architecture.

### 16.2 Rule — The UI Is an Adapter

- Business logic, durable state, and the source of truth live in the backend service layer; the renderer and the command handlers are adapters (`core.invariants`, File 01 §7.7; `core.explicit-rejections`, File 01 §8; `atlas3-core/CONSTRAINTS.md` §1; `cross-cutting/service-layer.md` realized). A presentation view computes presentation values only (§3.2); it never owns a capability's effect, a policy decision, a route, a model selection, an availability evaluation, or a substrate mutation. One service layer serves every client — a windowed shell, a terminal, a spoken surface, a spatial canvas, an embedding host, and a client with no attending user at all — so the service layer is rendering-agnostic and any renderer is one adapter among many over it. A client's medium changes which adapter it is, never what the service layer offers it (realized in the windowed-desktop profile as a webview, §16.8).
- The renderer communicates with the service layer over typed inter-process communication: a request-response invocation path for commands and queries, and a streaming channel for live events (`foundations/stack.md`; `core.stack-commitments`, File 01 §9 — "typed IPC"). The renderer opens no in-renderer network server and uses no network-style transport to reach its own backend. The boundary is statically typed: the command and event types are generated from the backend contract so a backend change that breaks the contract breaks the build, not the runtime.

### 16.3 Typed Errors at the Boundary

Cross-boundary failures are typed (`core.typed-errors`, File 01 §6.9; `cross-cutting/errors.md`) and drive presentation behavior, not only display: a retryable failure renders a retry affordance, a rate-limited failure renders a countdown and retry, a validation failure highlights the field with a corrective message, and an unrecoverable failure renders an actionable explanation. A failure is never rendered as a raw internal error string to the user; it renders through the typed-error renderer with a localized, actionable message (§15).

### 16.4 Ephemeral View State and No Private Store

The presentation layer holds only ephemeral view state — the live `SurfaceState` (the presented units and their prominence, focus, selection, in-progress composition, the attended position; File 18 §5) reconstructed from self-registration — plus client-only presentation preferences (the active theme reference, the active composition reference, the information-scale preference, and whatever situating value the client's declared profile carries) persisted through the settings system as syncable user preferences or device-local values per their declared locality (§19; File 15). The presentation layer maintains no private durable store, no parallel persistence, and no source-of-truth state; its loss is a rebuild (§3.2, `core.projection`, File 01 §6.11). Cross-context state is shared through the event bus and settings, never shared in-memory state (§4.5; realized in the windowed-desktop profile as a window placement, §16.8); an optimistic mutation envelope is context-local, applying, rolling back, or superseding only in the context that issued it while every other context observes only the authoritative outcome (`runtime.transports`, File 42 §10.3).

### 16.5 Semantic-Token Discipline

Every presentation property a renderer varies resolves from a named semantic token, never a literal (`customize.design-tokens`, File 38 §4; `cross-cutting/theming.md` realized), and each medium declares its own token families under the same discipline. This file owns the discipline (renderers consume only tokens); File 38 owns the token system and the themes that resolve the tokens. The discipline makes the presentation fully re-themeable, and adaptable to the perceptual preferences §14 carries, without renderer changes (realized in the windowed-desktop profile as its token-family declaration, §16.8).

### 16.6 Performance Contract

The presentation layer meets interactive-responsiveness budgets, and the invariant is checkable without freezing a number: every gesture is acknowledged in the medium before its result arrives, and continuous output remains continuous at the medium's own delivery rate. Each budget — gesture-to-acknowledgement, input-to-effect, continuous-output cadence — is a declared, tested, settings-carried value with a stated default, never a canonical constant and never an unstated one (`ux-input/design-principles.md`, `codex_recommendations.md`; §22). Performance is achieved through the projection, range-materialization, position-decoupling, aggregation, paced-rendering, and unattended-suspension techniques §10 requires, never by dropping substrate data (realized in the windowed-desktop profile as a refresh-rate budget, §16.8).

### 16.7 Boundary

This section owns the renderer boundary, the typed-error contract, the ephemeral-state rule, the semantic-token discipline, and the performance contract. File 01 §9 fixes the stack commitments; File 15 owns settings persistence; File 38 owns the token system; File 43 owns packaging and platform-window mechanics. This file fixes that the renderer is an adapter.

### 16.8 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §16.2. The shipped frontend of this profile is a browser-based webview over typed inter-process communication — a request-response invocation path and a streaming channel — with a compile-time type bridge between the backend service layer and the renderer, and no in-renderer network server (`core.stack-commitments`, File 01 §9), which is the committed realization the runtime records (`runtime.process-topology`, File 42 §4.3). The concrete library, bundler, and platform-window mechanics are the renderer implementation's and File 43's.

Realizes: §16.4. The client-only presentation values this profile carries are the active theme reference, the active composition reference, window position and size, and density and font scale.

Realizes: §16.5. The semantic-token families this medium declares are those its design-token declaration carries — surface, text, interactive, feedback, component radius and shadow, motion, typography, spacing, and the surface-density and information-density axes (`customize.design-tokens`, File 38 §4).

Realizes: §16.6. Scrolling holds the display refresh rate and streaming text renders smoothly; gesture-to-feedback is near-immediate and input latency imperceptible, against the tested defaults §22 carries.

## 17. UI States

Anchor: `ui.states`

### 17.1 Rule

- The presentation layer renders the full state space of every view, not only the populated state: a resolving projection is presented as resolving, an empty one guides the user toward the next action, a failed one renders through the typed-error contract (§16.3), and a degraded or offline one — a capability, sidecar, connection, or provider unavailable — is presented as a typed unavailability with the reason and a recovery path, never a silent failure and never a broken view. The presented form of each is the frontend's (realized in the windowed-desktop profile as a skeleton state, §17.3).
- First-run and onboarding render as presentation flows over substrate operations: a first-run flow that establishes the initial presentation (a profile or starting-point selection that applies a default `ViewPreset` and presentation preferences, §5.3), permission and capability setup surfaces (a capability unavailable for lack of a host permission is presented with its blocking reason and the action that clears it, `unit10-gui-control.md`, `conversation/05-voice-input.md`), and migration or recovery surfaces where a substrate operation requires user input (a workspace-recovery request, `workspace.relocation-recovery`, File 24 §6; `unit15-ux-distribution-files-glossary.md` D15.F.4). First-run and onboarding are per installation, not per presentation context: a context opened while a first-run flow is in progress joins the running application without restarting the flow. Onboarding may render as a guided conversation rather than as a dedicated step sequence where appropriate (realized in the windowed-desktop profile as a setup card, §17.3). Each onboarding step is a capability invocation rendered as a step; the flow owns no durable state of its own.
- Beyond first run, contextual guidance and searchable, revisitable help are presentation over existing capability, setting, registry, and built-in-content facts, not a second teaching substrate. Guidance is dismissible and revisitable; completion and dismissal state resolve through the settings system (§22; File 15), and the flow owns no private durable store (§16.4). Guidance inherits the localization (§15), accessibility (§14), product-language, provenance, and policy constraints, and cannot grant authority or enable a capability.

### 17.2 Boundary

This section owns UI state-space and product-education rendering. The owning specs own the underlying conditions (capability availability, connection state, permission state, workspace recovery) and the capability, setting, registry, and built-in-content facts the guidance projects; File 15 owns completion and dismissal state; File 38 owns onboarding customization. This file renders the states and the guidance.

### 17.3 Windowed-Desktop Profile

Windowed-desktop profile (`ui.frontend-profile`, File 37 §1.3); binds only a session declaring `desktop.windowed`.

Realizes: §17.1. A resolving projection renders as a loading or skeleton state; a capability blocked on a host permission renders as a setup card carrying the reason and the action; a workspace recovery renders as a dialog; and a first-run flow that is not a guided conversation renders as a wizard.

## 18. World-Model, Perception, and State-Awareness Integration

Anchor: `ui.world-state-integration`

### 18.1 Rule

- The presentation layer is both the renderer of `SurfaceState` and the producer of it: every unit self-registers its live state to the world model when it is activated and on focus, selection, and content change, and unregisters when it is deactivated (`world.observation-state-update`, File 18 §8.1), so the agent, the rails, and other views read the user's current context as structured data, never a capture (`world.chosen-model`, File 18 §1; `perception.tiered-sensing`, File 19 §5.4). A unit that fails to register its state is a blind spot the agent cannot use; registration is mandatory for every interactive unit, in every medium.
- Atlas's own presentation contexts and their elements may be represented in accessibility, world-model, and substrate projections for inspection, assistive technology, and Atlas-native UI capabilities. They are not valid targets for desktop GUI Control, whatever medium they present in and however the host exposes them. Actions that manage Atlas state must go through Atlas capabilities, control rails, approval policy, and settings, not through puppeting Atlas's own UI (`gui.action-execution`, File 31 §8.1).
- The presentation layer renders the available-action list the availability evaluator computes (`world.state-aware-capability-availability`, File 18 §9) and re-renders it event-first on recompute (§11.3); it maintains no private available-action store. It renders the world-model entities and observations through their viewers (§9.4) as projections; a surface that observes the unowned environment renders perception's observations (File 19), never a private observer.
- The presentation layer renders no interaction-shape, autonomy, participation, or execution-mode field in the world model, because none exists (`world.surface-state`, File 18 §5.5; §7.3). It renders `UiMode` as live interaction state, not an autonomy control.

### 18.2 Boundary

This section fixes the world-model and perception integration. File 18 owns the entities, the self-registration contract, the durability tiers, and the availability evaluator; File 19 owns capture and observations. This file renders them and feeds the self-registration.

## 19. Persistence, Locality, and Portability

Anchor: `ui.persistence-locality`

### 19.1 Rule

- The presentation layer persists no durable source-of-truth state. Its live state — the presented units and their prominence, focus, selection, in-progress composition, the attended position, the materialized presentation — is computed and rebuilt from self-registration and the substrate projections, never a durable fact (§3.2, §16.4; `world.persistence-contract`, File 18 §14.2). Its loss is a rebuild, never data loss (`core.projection`, File 01 §6.11).
- Client-only presentation preferences — the active theme reference, the active composition and view-preset references, the information-scale and density preferences, the reduced-motion preference, and equivalent — persist through the settings system as settings/customization records (File 15, File 38), each declaring its locality (`settings.locality-sync-export`, File 15 §18): a `SavedComposition` and a default-presentation preference are syncable user preferences, while device-bound presentation values — each full presentation context's restore key, presented-scope reference, composition reference, and profile-local realization payload, held in the one device-local presentation-context record (§4.5) — are device-local and never a per-context settings scope (`settings.scopes-profile-contexts-overlays`, File 15 §5.1). The presentation layer introduces no private persistence path.
- The presentation layer persists no raw secret in any rendered, cached, exported, or shared state (`secret.backend-boundary`, File 22 §4), and honors the sensitivity classification of what it renders in screenshots and exports (`ledger.sensitivity-aware-persistence-retention`, File 10 §10). Every hash a presentation record relies on is computed over a declared `CanonicalEncoding`, never physical bytes (`core.canonical-hash`, File 01 §7.14); this file defines no new canonical hash.

### 19.2 Boundary

This section fixes the presentation layer's persistence and locality. File 15 owns the settings persistence and locality; File 20 owns storage; File 21 owns sync and portability; File 22 owns the secret boundary; File 38 owns the saved-customization records. This file owns no durable store.

## 20. The UI Capability Surface

Anchor: `ui.capability-surface`

### 20.1 Rule

- The presentation layer's user-facing operations are canonical capabilities in the one Capability Registry (`capability.declaration`, File 05 §3), declared as built-ins, tier-gated by policy (File 06), surfaced through tool-surface composition (File 07), and invoked through the shared pipeline (`run.call-pipeline`, File 04 §8.2). Presentation capabilities declare touched resources and effect by kind:
  - inspecting the presentation context, its composition, its units, and its presentation state is `ReadOnly`
  - transient presentation operations — activate, deactivate, or focus a unit; alter the composition (its grouping, ordering, primacy, or a unit's prominence); relocate a unit between presentation contexts; create, focus, or close a presentation context; switch the active surface or apply a `ViewPreset`; move to or reveal a `NavigationTarget`; set the interaction-model lens; enter input capture on a declared rail — are UI-state writes scoped to the conversation, workspace, or session, with the effective tier resolved from touched resources and policy. Every context- or unit-targeting presentation operation carries an explicit transient presentation target — the presentation context or unit it acts on — as part of its invocation; a missing or stale target is a typed failure, never a fallback to the attention target (§4.4, §4.5)
  - saving or deleting a user presentation preference (a `SavedComposition`, a default view preset, the interaction-model lens default, an information-scale or theme reference) is a client-only presentation-preference write per scope, composed as a settings/customization write with File 15 and File 38, not duplicated
- Every presentation capability is the single source for all its invocation paths — discovery, binding, spoken gesture, direct affordance, agent tool, automation trigger, external protocol (`core.extension-planes`, File 01 §6.14); the presentation layer declares no out-of-band presentation operation. The agent invokes presentation capabilities the same way the user does — through the one capability system under policy — so an agent that arranges the presentation for a task (presenting a relevant unit, applying a view preset) does so through the same gated path, never through a private UI mutation. Custom presentation operations register through the proposal-first mechanism (File 05 §16.2) and never bypass policy.

### 20.2 Boundary

This section names the presentation capability families and their effect classes. File 05 owns the capability contract; File 06 owns tier resolution and approval; File 07 owns surfacing; File 04 owns execution; File 38 owns the customization capabilities that compose with these. This file declares the presentation capabilities as built-ins.

## 21. Events

Anchor: `ui.events`

### 21.1 Rule

- The presentation layer emits its own consequential presentation facts as `Custom { namespace: "ui", name, payload }` events (`ledger.custom-kind-registration`, File 10 §4.3) through the one event bus and ledger with the canonical envelope (`ledger.event-envelope`, File 10 §5.2): a role binding or presentation unit activated, deactivated, focused, or relocated; a unit's prominence changed; a composition altered; a `ViewPreset` applied; a `NavigationTarget` moved to; an interaction-model lens changed; a management surface activated; a presentation context opened or closed. Each declares its payload schema, cross-reference keys, default sensitivity, retention, and owner per File 10, and each carries the `PresentationContextRef` through the registered extension cross-reference key File 18 registers (`ledger.cross-references`, File 10 §3.6; `ledger.event-envelope`, File 10 §5.2) — no new envelope dimension and no new top-level event kind. Every payload field is medium-free, or optional with a declared meaning for its absence, so a fact only one medium can produce is never required of another: a diagnostic a profile emits about its own realization is a profile-local `Custom` kind under the same registration, never a canonical `ui` payload field. Live surface-state changes (unit registration, focus, selection, mode) are owned by `world.state-change-events-reactivity` (File 18 §12) and emitted by the world model from the presentation layer's self-registration; this file consumes them and does not duplicate them. Surface-lifecycle and tool-surface events are Files 25 and 07's; rail-resolution events are File 26's; this file emits only its own presentation facts.
- A presentation event is live coordination; a consequential fact (a preference saved, a presentation context opened) is committed to the durable record by the owning settings or registry path, never inferred from event observation (`core.durable-history-transient-coordination`, File 01 §7.3). Continuous and high-frequency presentation-input events, and the intermediate values of a composition in progress, are transient by default and not durable unless diagnostics are explicitly enabled with a retention class and sensitivity label (§13.2). There is no participation-level or autonomy-mode event (§7.3).

### 21.2 Boundary

This section reserves the `ui` event namespace and declares presentation-fact events only. File 10 owns the envelope, delivery, sensitivity, and custom registration; Files 18, 25, 07, 26 own the events this file consumes. This file emits through the shared bus.

## 22. Settings

Anchor: `ui.settings`

### 22.1 Rule

- Presentation behavior is configurable through the one settings system (`core.settings-system`, File 01 §6.8; File 15); this file names the dimensions, the settings system owns the cascade and storage. Presentation settings are namespaced keys resolved through the standard cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); the presentation layer is not a durable settings scope, and per-presentation variation is namespaced keys plus profile layers, never a new scope.
- The canonical presentation settings dimensions include at least: the default and per-scope `ViewPreset` and default surface for a new conversation or workspace (composed with File 25's settings); the default composition and whether saved compositions apply (composed with File 38); supporting-role auto-reveal per role and per reveal trigger class, with indication-only always selectable, and whether auto-reveal fans out across matching presentation contexts or confines to the origin or attention context (§4.3); whether the previous context set restores on launch and what a launch with no restorable set opens; whether losing the last full presentation context ends the process or leaves the application resident; the maximum concurrent full-context count (§4.5); the information-scale and density preferences; the default and active interaction-model lens, durably scope-pinned to Global, Workspace, or Conversation (`settings.scopes-profile-contexts-overlays`, File 15 §5.1) with any session-scoped lens riding the transient overlay; the reduced-motion preference and the transition-duration scale; the streaming render-pace and the high-frequency aggregation thresholds; the attention-follow re-engage rule (§10.3); the transcript-folding and grouping defaults; the conversation-list grouping and unread behavior; the queue-versus-interrupt default and the duplicate-handling and auto-continue conveniences (composed with Files 02, 13, 26); the detail each non-preemptive attention class carries, in-context and on any external attention surface; the active accessibility conformance profile; the debug-surface accessibility and retention controls (developer-only by default); and the active locale, theme reference, and perceptual-emphasis preference (composed with File 15 and File 38). Profiles carry per-profile presentation defaults (`settings.profiles`, File 15 §7).
- Each presentation setting declares its locality (`settings.locality-sync-export`, File 15 §18) — saved compositions, view-preset, information-scale, and locale preferences are syncable user preferences; a device-bound situating value a profile records is device-local — and its agent exposure (`policy.agent-exposure-policy-settings`, File 06 §16.4), so the agent cannot read or change security-sensitive presentation configuration without policy. No presentation behavior with meaningful variation is a hardcoded constant (`core.typed-configuration-failure`, File 01 §7.6; `settings.settings-over-constants`, File 15 §13).

### 22.2 Boundary

This section names the presentation settings dimensions and their layer. File 15 owns the settings object model, the cascade, locality, agent exposure, and profiles; Files 02, 06, 13, 25, 26, and 38 own the per-substrate settings the presentation composes with. This file names the presentation-relevant dimensions.

## 23. Explicit Rejections

Anchor: `ui.explicit-rejections`

The following are architecturally invalid for any later or per-surface spec:

- **Business logic in the renderer or command wrappers** — a presentation view computes presentation values only; policy, routing, model selection, availability evaluation, substrate mutation, and capability effects live in the service layer; the renderer and command handlers are adapters (§3, §16; `core.invariants`, File 01 §7.7; `core.explicit-rejections`, File 01 §8).
- **A private durable UI store or source-of-truth state** — every view is a projection rebuildable from the substrate; the presentation layer holds only ephemeral view state (the live `SurfaceState`) plus client-only preferences persisted through the settings system; no parallel persistence, no UI-owned durable fact (§3, §16.4, §19; `core.projection`, File 01 §6.11).
- **A participation-level, autonomy-mode, persona, agent-mode, plan-versus-build-mode, or phase field at any UI layer** — autonomy is the approval posture (permission tiers, leases, approval-posture preset) the policy layer resolves; progressive disclosure is which units are presented, at what prominence, under which view preset; interaction shape is a presentation lens; the UI renders the consequences, never a mode field (§7; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; File 25 §13; File 26 §17).
- **Conversation forced as the universal container or the mandatory primary presentation** — conversation is an always-available control rail and a role a context serves without being contained by it; primary focus is whatever the work needs (§4; `core.product-thesis`, File 01 §1; `intent.presentation`, File 02 §8; `worksurface.explicit-rejections`, File 25 §20).
- **A parallel renderer table, approval shape, dialog system, or available-action store** — there is one `RendererRegistry`, one approval and elicitation data contract rendered verbatim, one focused-dialog selector, and one availability evaluator; a surface or plugin contributes a renderer through the one registry and renders the one approval contract, never a parallel shape (§3, §11.3, §12; `policy.consequences-for-later-specs`, File 06 §18).
- **A view that polls a substrate on a timer for live state, or time-based correctness in presentation** — views are event-first; a periodic refresh is a flagged, configurable fallback only where a source emits no change events; auto-continue countdowns and animation timings are conveniences, never correctness conditions (§3.2, §10; `core.event-first-by-default`, File 01 §7.15).
- **A streamed partial persisted as truth, or a partial-to-committed transition the user perceives as a rebuild** — the durable committed block is the source of truth and the partial is the live projection that converges to it; the transition is a single continuous view (§10.2; `ledger.streaming-live-partials`, File 10 §12).
- **An external deep link that executes consequential work** — external-origin navigation is reveal-only and `ReadOnly`; any consequential action encoded in a link must enter through the normal rail, capability, policy, and approval path (§4.4; File 26 §12).
- **An interactive artifact event treated as trusted, authoritative, instructional, or system-owned** — artifact-runtime events use the registered `artifact.runtime` namespace, carry the artifact identity as data, and cannot impersonate system events or trigger security-category hooks (§9.3; File 10 §8.3).
- **Parallel work forced into one flat stream, or a single-active-stream assumption** — parallel activity is separately addressable and independently navigable, never serialized into one stream; the conversation may have multiple concurrent streams (§10.4; `intent.presentation`, File 02 §8.4; `intent.explicit-rejections`, File 02 §9).
- **A unit or affordance that cannot be represented structurally** — every unit and affordance exposes the semantic role, label, interaction kind, and state relationships sufficient for the world model, the rails, and assistive technology; rendering may vary, structural invisibility is invalid in every medium (§6.2, §14; `worksurface.explicit-rejections`, File 25 §20).
- **A hardcoded user-facing string, a raw value bypassing semantic tokens, or a presentation behavior hardcoded instead of a setting** — every user-facing string is a localizable key, every presentation property a renderer varies resolves from a semantic token, and every meaningful presentation variation is a setting (§15, §16.5, §22; `atlas3-core/CONSTRAINTS.md` §2/§3; `settings.explicit-rejections`, File 15 §20).
- **An in-renderer network server or network-style transport to reach the backend** — the renderer reaches the service layer over typed inter-process communication only (§16.2; `foundations/stack.md`; `core.stack-commitments`, File 01 §9).
- **Raw secret material rendered, cached, exported, or shared, or untrusted rendered content treated as instruction** — the renderer honors the secret boundary and the no-authority-from-untrusted-content rule; rendered foreign content is content, never instruction (§3.2, §9, §19; `secret.backend-boundary`, File 22 §4; `security.untrusted-content`, File 22 §12).
- **A presentation-focus change treated as an execution reroute** — presenting, focusing, or relocating a role binding or unit affects presentation and invocation context, but an active run's primary surface and execution context change only through File 03/File 04 reroute or explicit user override (§4.3; `worksurface.explicit-rejections`, File 25 §20).
- **A presentation context treated as a work-model identity** — a context presents; it binds no workspace, selects no `materialization_head`, owns no conversation, is no run's execution context, and is no settings scope. Opening, closing, or moving a context changes presentation and nothing else (§4.5; `workspace.conversation-binding`, File 24 §7.2; `workspace.materialization`, File 24 §10.3; `settings.scopes-profile-contexts-overlays`, File 15 §5.1; `worksurface.activation-shell`, File 25 §11.2).
- **A single, primary or privileged presentation context assumed by any presentation rule** — presentation contexts are peers; no rule resolves to "the" context, and a rule that reads correctly only where exactly one context exists is invalid. A rule that needs a destination uses the context-resolution rule (§4.4); a rule that needs a focus owner uses the presentation context (§12.2); the attention target is a presentation hint and never an authority, routing, or policy input (§4.4, §4.5).
- **The same request preemptively presented in more than one presentation context, or a reveal, attention action, or auto-reveal acting in a context not presenting its scope** — preemptive presentation is one service-layer assignment and every other context presents a non-preemptive item; a reveal trigger acts only where its scope is presented (§4.3, §12.2, §12.4).
- **A management surface treated as a focus work surface** — memory, context, knowledge, registry, settings, world-model, observability, and equivalent surfaces are presentations of always-on substrate services, not focus work surfaces; they register no `SurfaceContract` (§13; `worksurface.management-surfaces`, File 25 §14).
- **A presentation contribution, theme, design-token system, saved-composition flow, or plugin UI injection defined here** — those are File 38's; this file owns the shell, the composition model, the rendering contracts, the interaction models, and the semantic-token discipline they consume (§5.5; `worksurface.views-presets`, File 25 §7.6).

## 24. Consequences for Later Specs

Anchor: `ui.consequences-for-later-specs`

Later specs must follow these rules:

Every rule of this file that a later spec consumes has two layers, and a later spec states which one it is binding to: the **pattern** layer binds every frontend, and a **declared profile**'s clauses bind only a session that declares that profile (`ui.frontend-profile`, §1.3). A later spec satisfies this file by satisfying the pattern; it may additionally state clauses in a profile subsection of its own, and it never states a profile clause as though it were a pattern rule.

- The **UI Customization, Widgets, and Theming** spec (File 38) consumes this file's `Shell` role model, `PresentationComposition`, `RendererRegistry`, `PresentationUnitKind` rendering, built-in `ViewPreset` rendering, interaction models, and semantic-token discipline to define user-saved named compositions and the save/switch/customize flow, presentation contributions and their placement, the design-token system and themes, AI-assisted customization, and plugin UI placement, realizing the `customization_policy` (File 25 §7.4) without bypassing these contracts. It introduces no parallel shell, composition model, renderer table, or rendering path.
- The **per-surface specs** (27–32 and equivalent future surfaces) declare what their presentation units, view presets, inspections, and observation viewers contain (File 25); this file renders them. A per-surface spec contributes renderers and unit kinds through the one `RendererRegistry` and the one self-registration contract, declares no private rendering path, and renders its history, comparison, and reconstruction views as projections over the one version graph. Per-surface accessibility, internationalization, and streaming concerns are this file's contracts applied to the surface's units, and a per-surface spec cites this file's four accessibility obligations (§14.2) rather than restating them.
- The **Quality Control and Validation** spec validates presentation conformance — that the renderer holds no business logic and no private durable store, that every view is a projection, that every unit and affordance exposes structural semantics, that accessibility and internationalization hold, and that the approval and elicitation contracts render verbatim — through the registration validator and event and capability hooks, not a separate pipeline.
- The **Telemetry, Logging, and Observability** spec and the **Evaluation and Benchmarking** spec own the data the observability and debug surfaces (§13.2) render; this file owns the surfaces. The **Runtime Infrastructure and Lifecycle** spec (File 42) orchestrates the renderer's startup and the service-layer connection around the storage lifecycle, opens the restored set of presentation contexts at the front-end-open boot phase (File 42 §11.3), routes a single-instance handoff's target through this file's context-resolution rule (File 42 §4.4; §4.4), and treats the loss of a context as a shutdown signal only through this file's context-lifecycle resolution and its typed `QuitRequested` outcome (File 42 §12.3; §4.5); this file owns the shell rendering. A client session declares, for each presentation context it opens, the profiles that context implements and the roles it serves, at establishment (`runtime.transports`, File 42 §10.1; `world.surface-state`, File 18 §5).
- The **Packaging, Platform, and Distribution** spec (File 43) owns the installer, the auto-updater, the platform window-decoration and tray mechanics, and sidecar lifecycle; a `ProtocolHandler` deep link routes to the running instance and then into the presentation context this file's context-resolution rule resolves (File 43 §7.3; §4.4); this file owns the presentation roles, the multi-context model, and the presentation of a context's own state, and the windowed-desktop profile (§1.3) names which of them the frontend File 43 packages realizes as windows. The **MCP and External Integrations**, **Extension and Plugin System**, **Automation and Triggers**, and **Workflows, Templates, and Reuse** specs render their manager, dashboard, editor, and discovery surfaces (the connector manager, the plugin browser, the automation dashboard, the workflow editor) through this file's management-surface, inspector, and renderer contracts; they introduce no private UI shell or rendering path.

## 25. Canonical Rule Anchors

Anchor: `ui.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `ui.chosen-model`, `ui.disambiguation`, `ui.frontend-profile`, `ui.boundaries`, `ui.presentation-projection`, `ui.shell`, `ui.layout`, `ui.surface-presentation-morphing`, `ui.interaction-models`, `ui.conversation-presentation`, `ui.substrate-rendering`, `ui.streaming-presentation`, `ui.rail-presentation`, `ui.dialog-elicitation-notification`, `ui.inspector-presentation`, `ui.accessibility`, `ui.i18n`, `ui.renderer-boundary`, `ui.states`, `ui.world-state-integration`, `ui.persistence-locality`, `ui.capability-surface`, `ui.events`, and `ui.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
