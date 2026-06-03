# Control Rails

## Status

Canonical. This file defines the `ControlRail` primitive and the input-resolution contract by which a user or system gesture becomes a capability invocation, a routing decision, a conversation message, or a steering action on running work. It realizes the Control Rails system layer that `core.system-layers` (File 01 §2.1) declares, and introduces the net-new `ControlRail`, `RailResolution`, and keymap, slash-command, voice-session, steering, and elicitation contracts that prior files referenced without owning. It is horizontal and surface-neutral: it defines the rails through which every work surface's capabilities are invoked and steered, not any one surface's rail bindings. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `ControlRail` primitive — a durable, registered entry-and-control mechanism that resolves a user or system gesture into one of a closed set of `RailResolution` outcomes against the shared substrate; realizes `core.system-layers` (File 01 §2.1)'s control-rail layer and the "control rails initiate **or steer** work" boundary
- the closed-canonical `ControlRailKind` catalogue (`Conversation`, `CommandPalette`, `Keybinding`, `SlashCommand`, `Voice`, `Menu`, `Trigger`, `ExternalProtocol`) plus the `Custom { namespace, name }` extension
- the **input-resolution contract**: how a rail turns a gesture (a typed query, a key chord, a spoken utterance, a slash token, a menu selection, an inbound trigger payload) into a `RailResolution` — a route-recorded capability invocation through `run.call-pipeline` (File 04 §8.2), a `RunIntent` through routing (File 03), a conversation message, a steering action through `run.user-intervention` (File 04 §17.1) / `routing.mid-execution-reroute` (File 03 §12), an elicitation open/answer, or a pre-dispatch transformation — and the rule that no rail owns a private registry, approval, execution, or routing path
- the **unified-invocation-path invariant**: one `CapabilityDeclaration` (File 05) is the single source for every rail that can invoke it (command palette, shortcut, voice, agent tool, automation trigger, external protocol), realizing `core.extension-planes` (File 01 §6.14)
- the **Conversation rail** — the input surface as the always-available primary entry rail: composition, submission, mention/reference/attachment/paste/slash expansion, and the pre-dispatch transformation contract; conversation as a control rail, never the universal container
- the **Command rail** — the command palette: invocation, search over the available-capability list, argument elicitation, recency/frequency presentation, and execution; the `CommandPalette` `UiMode` (File 18 §5.5)
- the **Keybinding rail and the keymap** — the `KeyBinding` chord grammar, the keybinding-context resolution model (the context stack and the deterministic top-down resolver), conflict resolution, the unbind override, platform reality, and settings-backed user rebinding; discharges the keybinding spec `surface.presentation-in-user-facing-surfaces` (File 07 §12.3) delegated
- the **Slash-Command and Command-Definition rail** — the slash grammar, namespaced commands, custom command definitions resolved over `workspace.internal-layout` (File 24 §8.3)'s `.atlas/commands/`, argument templating, prompt-template-versus-capability-binding commands, and precedence
- the **Voice and Handsfree rail** — the rail session (activation, capture, transcription, registry-derived intent resolution, confirmation, execution, spoken output), the `Handsfree` `UiMode`, and the full-capability/different-modality rule; consuming `perception.sensor` (File 19 §4.3)'s audio capture and transcription and `world.surface-state` (File 18 §5.5)'s `UiMode`, never re-owning capture
- the **Steering rail** — the user-facing affordances (stop, cancel, pause, interject, takeover, redirect, barge-in) that resolve to `run.interruption-pause-cancellation` (File 04 §17) and `routing.mid-execution-reroute` (File 03 §12); the queue-versus-interrupt policy
- the **Trigger rail** — non-interactive entry from fired scheduler, event, webhook, or file-watch signals framed as a rail kind whose resolution is a `RunIntent` per `routing.trigger-kinds-routing` (File 03 §2.1); deep trigger mechanics delegated to File 33 (Automation and Triggers)
- the **External-Protocol rail** — invocation from outside the application (an external MCP client, the CLI, a deep link) over `surface.presentation-in-user-facing-surfaces` (File 07 §12.6)'s external-exposure lens and File 36 (MCP and External Integrations)
- the **Elicitation contract** — the rail through which the system requests typed user input mid-work (approval, clarification, choice, correction, intervention), of which `policy.approval-ui-surface-contract` (File 06 §13) is the policy-specific case
- rail availability over `world.state-aware-capability-availability` (File 18 §9), the `RailRegistry` and rail lifecycle, the shell relationship (`worksurface.activation-shell`, File 25 §11), the no-private-architecture invariant for rails, the deletion of any autonomy/participation/mode field on a rail, and the rail capability/event/settings/persistence surface

This file does not define:

- the `Capability` declaration, registry, identity, or versioning — File 05 owns those; a rail resolves to a capability id and never re-registers operations
- policy evaluation, approval flows, leases, permission tiers, or the approval router — File 06 owns those; a rail invocation passes through the one policy layer like any other
- the `ToolSurface` zone model, the visibility-composition algorithm, the invoker lenses, or `find_by_shortcut` — File 07 owns those; a rail consumes the lens projection and the available-capability list, it does not compose visibility
- routing, the `RunIntent` field set, deterministic prechecks, or reroute mechanics — File 03 owns those; a rail produces the trigger and trigger context, routing produces the decision
- the run lifecycle, the capability-call pipeline, intervention mechanics, cancellation primitives, or budgets — File 04 owns those; a rail issues a steering action, execution carries it out
- conversation, message, intent-thread, or task identity and the message-submission lifecycle — File 02 owns those; the Conversation rail is the entry behavior over them
- the live `SurfaceState`, `PanelState`, `Selection`, `UiMode`, or the availability evaluator — File 18 owns those; a rail reads them
- audio capture, voice-activity detection, wake-word detection, transcription, or capture consent — File 19 owns those; the Voice rail composes them into a session
- the settings cascade, profile layers, or locality resolution — File 15 owns those; a rail names its dimensions
- the `.atlas/commands/` directory, the `ATLAS.md` instruction hierarchy, or workspace identity — File 24 owns those; the Slash-Command rail resolves command definitions stored there
- the event envelope, ledger schema, or hook dispatch — File 10 owns those; a rail emits through the one bus
- automation scheduling, trigger observation, trigger eligibility, non-interactive-execution safety, or enablement — File 33 (Automation and Triggers) and the owning producer specs own those; this file frames the Trigger rail kind
- MCP transport, the plugin install lifecycle, or external-API definition formats — File 36 (MCP and External Integrations) and File 35 (Extension and Plugin System) own those
- whiteboard, canvas, drawing, or artifact-editing behavior — those are work-surface, UI, and artifact concerns; they enter this file only when a surface invokes a capability through Conversation, Command, Menu, or another rail
- UI rendering — palette layout, key-capture widgets, voice waveforms, shell geometry, theming, and accessibility presentation are owned by the UI specs; this file specifies the data and resolution contracts they consume

## Source Resolution

Families reviewed: the unified-action-registry material (`cross-cutting/actions.md`, `atlas3-core/CONSTRAINTS.md` §5, `GLOSSARY.md`, `cross-cutting/README.md`, `references/README.md`, `domains/README.md`, `foundations/architecture.md` Design Filter §8); the command-palette and quick-navigation material (`domains/coder/command-palette.md`, `domains/coder/ide-interface.md`, `ui/14-1-application-shell.md`, `suna-addendum.md`, `warp-compressed.md`, `archon-compressed.md`); the keybinding material (`unit13-ui.md` D13.5/D13.6, `ui/accessibility.md`, `open-webui-ux-addendum.md`, `claude-code-frontend-addendum.md`/`-part2.md`, `claude_code_tool.md`); the slash-command and custom-command material (`unit12-infrastructure.md` (`SlashCommand`), `unit11-cross-tool-learning.md` CT.14, `domains/coder/workspace-management.md` (`.atlas/commands/`), `hermes-agent-compressed.md`, `oh-my-codex-compressed.md`, `continue-compressed.md`, `deer-flow-compressed.md`, `open-cowork-compressed.md`); the voice/handsfree material (`ux-input/whiteboard-and-handsfree.md`, `conversation/05-voice-input.md`, `conversation/04-text-to-speech.md`, `conversation/README.md`, `unit15-ux-distribution-files-glossary.md` D15.UX.4, `voicebox-compressed.md`, `omi-compressed.md`, `windows-use-compressed.md`); the conversation-rail and pre-dispatch material (`conversation/01-core-chat.md`, `conversation/02-message-operations.md`, `kuzeys-context-duplicate-prompt-handling-addendum.md`, `cline-frontend-addendum.md`, `opencode-frontend-addendum.md`, `goose-frontend-addendum.md`); the steering/intervention material (`unit10-gui-control.md` and `unit11c-system-agent.md` (`Interject`, `control: USER|ASSISTANT`), `hermes-agent-addendum.md` (`/steer`, `/queue`, `interrupt_subagent`), `pi-compressed.md` (`steer`/`followUp`/`abort`), `codex-addendum.md` (`steer_input`, `AskForApproval`), `goose-compressed.md` (tool-confirmation router, `GooseMode`), `nanobrowser-compressed.md` (`addFollowUpTask`), `open-webui-compressed.md` (stop + message queue), `cipher-compressed.md`, `agent-zero-compressed.md`); the trigger-as-entry material (`systems/19-scheduling-pipeline.md`, `unit12-infrastructure.md` (`macros`/`system_scheduled_tasks`/`system_watches`/webhook), `multica-compressed.md`/`-2.md`, `n8n-compressed.md`, `chatgpt_tool.md` automations); the external-entry material (`infrastructure/mcp.md`, `operator-use-compressed.md` (ACP), `claude_cowork_tool.md`, `sidex-compressed.md` (native-menu bridge), `distribution/packaging.md` (global shortcut, tray)); the state-awareness/UiMode material (`cross-cutting/state-awareness.md`, `cross-cutting/events.md`); the strategic target-state review (`codex_recommendations.md` §10.1, §0, line 317); the elicitation material (`unit11-cross-tool-learning.md` CT.2 (`ui.elicit`), `unit15-ux-distribution-files-glossary.md` D15.UX.1); and the deleted-autonomy material (`ui/15-3-and-15-4-participation-levels-personas.md`, `cross-cutting/state-awareness.md`, `GLOSSARY.md`).

Resolution rule: this file realizes and introduces, it does not re-own. The capability and registry stay File 05's, policy stays File 06's, the tool-surface lens and `find_by_shortcut` stay File 07's, routing stays File 03's, execution and intervention stay File 04's, conversation and message stay File 02's, the live `UiMode` and availability evaluator stay File 18's, audio capture and transcription stay File 19's, settings stay File 15's, the `.atlas/commands/` store and instruction files stay File 24's, the event bus stays File 10's. This file owns the `ControlRail` primitive, the input-resolution contract, the keymap model, the slash-command grammar, the voice-session contract, the steering-rail contract, and the elicitation contract, and supplies each to the layer that consumes it.

Resolved tensions:

- **One rail layer, or one spec per modality.** The specbase scatters rail material across `actions.md` (the registry consumers), `command-palette.md`, `whiteboard-and-handsfree.md`, and a referenced-but-unwritten "future Keybinding spec" (`surface.presentation-in-user-facing-surfaces`, File 07 §12.3). This file unifies them into one Control Rails layer because every rail shares one contract — a gesture resolves to a `RailResolution` against the one capability system — and because `core.system-layers` (File 01 §2.1) already names them one layer. Per-modality fragmentation would re-scatter the unified-invocation-path invariant and leave the keymap and slash grammar unowned.
- **The registry, the lens, or the rail.** Source material conflates three layers. `cross-cutting/actions.md`'s "unified operation registry" is already realized canonically by `capability.chosen-model` (File 05 §1) — which superseded the specbase `Action` — plus `surface.chosen-model` (File 07 §1)'s lens projection (Palette/Voice/Shortcut/AutomationTrigger/ExternalMcp). A `ControlRail` is neither: it is the **input modality and the resolution contract** that consumes the File 07 lens and the File 18 available-capability list and dispatches a resolved capability through File 04 and File 06. The rail owns no operation declarations and no visibility composition.
- **Invocation layer, or guardrail layer.** An early planned scope named File 26 "guidance, constraints, policy prompts, user-configured guard behavior, system-controlled intervention patterns." Those are already discharged: behavioral steering as approval-policy templates (`policy.approval-policy-templates`, File 06 §12.4, including the CT.16 `clarify_first_for_multistep` / `prefer_dedicated_tools` / `fetch_fallback_ban` templates), guardrail hooks (`run.hook-integration`, File 04 §23.3), stuck-detection intervention (`run.stuck-detection`, File 04 §20.3), governing instructions (`context.instruction-sources-workspace-files`, File 13 §16 and the `GoverningInstructions` region File 13 §3), and settings-as-guard (File 15). This file resolves toward the invocation-and-steer reading of `core.system-layers` (File 01 §2.1) and File 25 §21's verbatim delegation: it owns the user-facing **steering rail** (the affordances through which a user interjects, takes over, pauses, or cancels) and references the guardrail mechanics; it never re-owns approval, hooks, or the intervention machinery.
- **Voice intents — a hardcoded enum or registry-derived.** `whiteboard-and-handsfree.md` declares a `SpokenIntent` enum (`Chat`/`Navigate`/`ExecuteAction`/`ReadContent`/`AdjustSetting`); `unit15-ux-distribution-files-glossary.md` D15.UX.4 deletes it, deriving voice intents from the live capability registry instead. This file adopts the deletion: a voice utterance resolves to a voice-invokable capability in the current available-capability list, the same `RailResolution` path every other rail uses. A fixed intent enum would gatekeep against `core.extension-planes` (File 01 §6.14) and duplicate the registry.
- **Conversation as the universal container, or a control rail.** `codex_recommendations.md` §0/§10.1 and `intent.presentation` (File 02 §8) reject chat-as-universal-container; `core.current-major-area-classification` (File 01 §5.1) classifies conversation as a control rail and continuity surface. This file keeps conversation a first-class control rail — the always-available primary entry — without making the transcript the work model or the forced primary pane (`worksurface.activation-shell`, File 25 §11.3).

## 1. Chosen Model

Anchor: `controlrail.chosen-model`

ATLAS3 has one `ControlRail` primitive and one `RailRegistry` over it.

A `ControlRail` is a registered entry-and-control mechanism: one identifiable way for a user or the system to **initiate or steer** work, by turning a gesture into a `RailResolution` against the shared substrate. The conversation input surface, the command palette, the keyboard, the voice and handsfree channel, slash commands, menus and toolbars, automation triggers, and external-protocol clients are each a `ControlRail`. They are the realization of the control-rail layer `core.system-layers` (File 01 §2.1) names — "universal entry and control mechanisms through which the user or system invokes capabilities" — and they honor that section's boundary: a control rail initiates or steers work; it is not itself the work model.

A `ControlRail` is a **projection over capability contracts and a resolver of gestures into invocations**, not a registry of operations and not a visibility composition. `codex_recommendations.md` line 317 states the principle directly: "command palette entries, voice commands, agent tools, buttons, shortcuts, and workflow nodes all become projections over capability contracts." The capability is owned by File 05; its visibility in a given lens is owned by File 07; its availability under the current world state is owned by File 18; its policy decision is owned by File 06; its execution is owned by File 04; its routing is owned by File 03. The rail's own responsibility is narrow and load-bearing: accept a gesture in its modality, resolve it to one of the closed `RailResolution` outcomes (§4), and dispatch that outcome through the shared pipelines those files own.

The **unified-invocation-path invariant** is the heart of the layer. A single `CapabilityDeclaration` (`capability.declaration`, File 05 §3) is the one source for every rail that can invoke the operation: the same `file.save` capability is reachable from the command palette, a keyboard chord, a spoken phrase, a slash command, a menu item, an automation trigger, and the agent's tool surface, with no parallel definitions and no per-rail operation logic (`core.extension-planes`, File 01 §6.14; `cross-cutting/actions.md`'s "one registry serves every path"; `foundations/architecture.md` Design Filter §8: "one registry entry for command palette, shortcuts, voice, agent tool list — two registries = bugs"). The agent and the user invoke the same capability system through different rails (`core.invariants`, File 01 §7.2).

`ControlRail` supersedes earlier vocabulary that named a rail or its mechanism: command bar, action bar, command-K, quick-open, hotkey system, keymap, accelerator table, voice command system, handsfree mode (as an architecture), trigger system (as an entry mechanism), command ingress, and input router. `RailResolution` supersedes "intent dispatch," "spoken intent," and "command resolution." Those names may persist as informal synonyms; the canonical noun is `ControlRail`, and the operation it reaches is always a `Capability`.

### 1.1 "Rail" and "Surface" Are Disambiguated

Anchor: `controlrail.disambiguation`

The words "rail," "surface," and "mode" are overloaded across the canon. This file fixes the `ControlRail` meaning and distinguishes it from adjacent concepts:

- a **control rail** (this file, `core.system-layers` File 01 §2.1) — an entry-and-control mechanism that resolves a gesture into a `RailResolution`. It initiates or steers work; it is not the work model and not a focus surface.
- a **work surface** (`worksurface.work-surface`, File 25 §3) — a primary user-facing work environment with specialized workflows and views. A rail invokes a work surface's capabilities and composes with the focus surface in the shell (`worksurface.activation-shell`, File 25 §11); it is not itself a work surface. Conversation is a control rail, not a work surface (`worksurface.surface-disambiguation`, File 25 §1.1).
- a **`ToolSurface`** (`surface.chosen-model`, File 07 §1) — the typed projection of the Capability Registry an invoker sees. A rail is an `invoker_kind`/`invocation_lens` (`surface.tool-surface`, File 07 §2.2): the `Palette`, `Voice`, `Shortcut`, `AutomationTrigger`, and `ExternalMcp` lenses are the visibility projections the corresponding rails consume. File 07 owns which capabilities a lens shows; File 26 owns how the rail turns a gesture into an invocation of one of them.
- a **presentation surface** (`intent.presentation`, File 02 §8) — a projection over the underlying work (a transcript, a comparison board, a trace). A rail is an input mechanism, not a view of work.
- a **`UiMode`** (`world.surface-state`, File 18 §5.5) — the live interaction mode (`Normal`, `CommandPalette`, `Modal`, `Fullscreen`, `Handsfree`, `Headless`). A rail's activation may set a `UiMode` (opening the command palette sets `CommandPalette`; entering handsfree sets `Handsfree`), but the `UiMode` is live state File 18 holds, not the rail. A `UiMode` is interaction state, never an autonomy control.
- an **interaction shape** (`core.interaction-shapes`, File 01 §2.2) — conversation-only, inline assist, sidecar, paired, orchestration desk — a presentation and involvement lens. It is a UX design lens, not a backend primitive, and not a rail.

### 1.2 Boundary

This file defines what a control rail is, how it resolves a gesture, and how it shares the substrate. It does not define what any capability does (File 05), whether a proposed invocation is permitted (File 06), what a lens shows (File 07), how the request routes (File 03), how a run executes or is interrupted (File 04), how live interaction state is held (File 18), how audio is captured (File 19), or how any rail is rendered (the UI specs).

## 2. Boundaries with Adjacent Layers

Anchor: `controlrail.boundaries`

### 2.1 With File 01 (Core Thesis)

This file realizes `core.system-layers` (File 01 §2.1)'s control-rail layer and honors `core.invariants` (File 01 §7): shared runtime (§7.1 — every rail is a presentation of one runtime), shared capability system (§7.2 — user and agent invoke the same capabilities through different rails), flexible presentation (§7.5), service-layer ownership (§7.7), local extensibility (§7.8 — new rails addable without rewrites), system-wide customization (§7.9), and user control and killability (§7.11 — the steering rail is the user-facing realization of "Atlas-managed long-running work must remain under user control"). Rails are one of the `core.extension-planes` (File 01 §6.14) planes; the `ControlRailKind` enum is closed-canonical-plus-`Custom` per `core.closed-canonical` (File 01 §6.16). `ControlRail`, `RailResolution`, and `KeyBinding` are new canonical noun-objects.

### 2.2 With File 02 (Conversation, Intent, Task)

The Conversation rail (§5) is the entry behavior over `intent.conversation` (File 02 §2.1)'s conversation and `intent.message` (File 02 §3)'s message; `intent.message` (File 02 §3.4)'s message-submission lifecycle owns the pre-dispatch processing (reference expansion, duplicate detection, hook invocation) that the Conversation rail surfaces. A rail gesture produces a `Message` commit or a `RunIntent` trigger; it never bypasses conversation attachment or work-line ownership (`intent.run-intent`, File 02 §4.1, `intent.intent-thread` File 02 §5). Conversation is a control rail and continuity surface, not the work model (`intent.presentation`, File 02 §8.2).

### 2.3 With File 03 (Routing and Dispatch)

Every rail resolution that asks the system to perform semantic work is route-recorded. `routing.trigger-kinds-routing` (File 03 §2.1) enumerates the trigger kinds a rail produces — `user_request` (Conversation), `user_invoked_action` (Command/Keybinding/Slash/Menu), `automation` and `external_event` (Trigger/External-Protocol), and `retry`/`edit_reroute` (steering). A user-invoked action whose capability id deterministically resolves the target uses File 03's deterministic-precheck path: the router model is skipped, the route record is still produced, and execution receives a route-linked direct invocation. `RouteRequest` is reserved for gestures whose route is not deterministic. The Steering rail's reroute and interject gestures resolve through `routing.mid-execution-reroute` (File 03 §12). This file produces the gesture, trigger context, and direct-invocation context; File 03 records or resolves the route.

### 2.4 With File 04 (Execution and Run Model)

A rail-invoked capability executes through `run.call-pipeline` (File 04 §8.2) like any other; the user is an `Invoker` whose direct invocation never requires the agent-autonomy permission path but still passes policy floors, typed-confirmation, touched-resource checks, and ledger recording (File 06). The Steering rail (§10) is the user-facing surface of `run.user-intervention` (File 04 §17.1) — continuation with new instruction, pause, cancellation, branch, reroute, approval, scope narrowing, and explicit takeover (the run's `control` field flips to `User` per `run.minimum-durable-reconstruction`, File 04 §2.6) — and of `run.cancellation` (File 04 §17.3)'s cooperative-then-forceful model. The queue-versus-interrupt behavior of mid-execution input is the `intent.intent-thread` (File 02 §5.5) / `run.retry-reroute-branch` (File 04 §19) setting this file's rails expose, not a new mechanism.

### 2.5 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces)

A rail resolves a gesture to a `Capability` id (`capability.id`, File 05 §13.1) and invokes it; it registers no operations. Display fields a rail consumes — `name`, `short_description`, `default_shortcut`, `icon_key`, and the `agent-invokable`/`palette-invokable`/`voice-invokable`/`automation-trigger`/`external-exposed` tags — are declared per `capability.display-fields` (File 05 §3.2). The set a rail may present is the lens File 07 composes (`surface.visibility-composition-resolution-algorithm`, File 07 §9) filtered to the rail's invocation lens (`surface.presentation-in-user-facing-surfaces`, File 07 §12); `find_by_shortcut` (`capability.discovery`, File 05 §15.1, surfaced by File 07) is File 05/07's, and the Keybinding rail consumes it. Every rail invocation's authority is decided by `policy.effective-tier-resolution` (File 06 §4) and the `policy.approval-router` (File 06 §3); the rail never approves, never bypasses `permission_floor`, never lifts typed-confirmation. The elicitation a rail renders for approval is `policy.approval-ui-surface-contract` (File 06 §13).

### 2.6 With File 10 (Ledger, Events, Hooks)

Rail facts flow through the one event bus and ledger with the canonical envelope (`ledger.event-stream`, File 10 §5, `ledger.event-envelope` File 10 §5.2); rail-specific events register as `Custom { namespace: "controlrail" }` extensions (`ledger.custom-kind-registration`, File 10 §4.3). Pre-dispatch decisions and consequential resolutions a rail makes are recorded as rail-resolution records linked to the downstream message, route, capability, run, policy, or steering facts. A rail never opens a side-channel notification path or a parallel bus.

### 2.7 With File 13 (Context Assembly)

A rail does not assemble model requests. A custom-command or slash-command rail whose definition contributes instruction text contributes it as an attributed `InstructionSources` part (`context.instruction-sources-workspace-files`, File 13 §16) with the correct authority class (`context.authority-classes`, File 13 §2.3), never as hidden model-request text. The duplicate-overlap detection a Conversation rail surfaces is `context.duplicate-overlap-handling` (File 13 §8); the rail invokes it, it does not re-own it.

### 2.8 With File 15 (Settings)

Every rail mechanism with meaningful variation is a setting (`settings.settings-over-constants`, File 15 §13) resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); a keybinding is a `KeyboardShortcut`-semantics value (`settings.types-semantics-constraints`, File 15 §4.2). Rails are not a durable settings scope; per-rail variation is namespaced keys plus profile layers, with declared locality (`settings.locality-sync-export`, File 15 §18). A rail is not a File 15 `Profile`, an autonomy control, or an execution mode (`settings.profiles`, File 15 §7.4).

### 2.9 With File 18 (World Model) and File 19 (Perception)

A rail reads the live `world.surface-state` (File 18 §5) to resolve context-dependent gestures (a voice "click the second tab" against the panel list, a keybinding against the active `UiMode`, a "format this" against the current `Selection`) and reads the available-capability list `world.state-aware-capability-availability` (File 18 §9) produces to know what it may present. Activating a rail may set a `UiMode` (`CommandPalette`, `Handsfree`) that File 18 holds. The Voice rail composes `perception.sensor` (File 19 §4.3)'s `Audio` sensor — microphone capture, voice-activity detection, wake-word detection — and the transcription processor and the `perception.transcribe` capability (`perception.capability-surface`, File 19 §14); File 19 owns capture, consent, wake-word gating, audio processing thresholds, and transcription, while the Voice rail owns the session that turns a transcript into a rail resolution. Spoken output is requested through the appropriate provider/audio/output capability path; the Voice rail does not own synthesis, caching, playback, or device routing. A rail is never screen-scraped to learn its own state; the surface it acts on self-registers (`world.observation-state-update`, File 18 §8.1).

### 2.10 With File 24 (Workspaces) and File 25 (Work Surface Contract)

The Slash-Command rail resolves custom command definitions stored in `workspace.internal-layout` (File 24 §8.3)'s `.atlas/commands/` — "each a declarative definition resolved through the capability system, never an out-of-band execution path" — and consults the `workspace.instruction-files` (File 24 §9) hierarchy for instruction-bearing commands. A work surface's `SurfaceContract` declares its control affordances (`worksurface.actions-declaration`, File 25 §6.4) as presentations of capabilities a rail invokes; the shell relationship is `worksurface.activation-shell` (File 25 §11). This file consumes the surface's declared control affordances and the command-rail-plus-focus-surface shell; it does not own surface identity or shell rendering.

### 2.11 With File 33 (Automation), File 36 (MCP), and the UI specs

The Trigger rail (§11) frames non-interactive entry from fired trigger events; File 33 (Automation and Triggers) owns scheduling, eligibility, non-interactive-execution safety, and enablement, and producer specs own source observation. The External-Protocol rail (§12) frames external invocation; File 36 (MCP and External Integrations) owns MCP transport and File 35 (Extension and Plugin System) owns external-API definitions and plugin-registered rails. File 37 and File 38 render every rail (palette layout, key-capture, voice waveform, shell geometry, theming, accessibility presentation); this file specifies the data and resolution contracts they consume.

### 2.12 Boundary

This file is the control-rail layer. It owns the `ControlRail` primitive, the input-resolution contract, the keymap, the slash grammar, the voice session, the steering contract, and the elicitation contract. It owns no capability declarations, no policy evaluation, no tool-surface composition, no routing decisions, no run mechanics, no live interaction state, no audio capture, no settings storage, and no UI rendering. It feeds those layers; it does not replace them.

## 3. The `ControlRail` Primitive

Anchor: `controlrail.control-rail`

### 3.1 Definition

A `ControlRail` is a durable, registered, identified entry-and-control mechanism that accepts a gesture in one input modality and resolves it to a `RailResolution` (§4) against the shared substrate. It is registered in the `RailRegistry` (§14), it declares the invocation lens (`surface.presentation-in-user-facing-surfaces`, File 07 §12) it consumes, and it presents the available-capability list filtered to that lens.

### 3.2 Purpose

The system is one shared runtime reachable through many modalities (`core.invariants`, File 01 §7.1). A user types, presses keys, speaks, clicks menus, runs CLI commands, and configures triggers; the system receives webhooks and OS events. Each of these is a distinct gesture in a distinct modality, but each must reach the same capabilities under the same policy through the same route-recorded invocation and execution contracts, with no per-modality operation logic and no parallel registries. The `ControlRail` primitive is the unit that carries one modality's gesture-handling while reusing everything underneath, so adding a new rail — a stream-deck, a gamepad, an ops-channel — is a registration, not a new architecture (`core.local-extensibility`, File 01 §7.8).

### 3.3 Required

- A `ControlRail` resolves a gesture to a `RailResolution` (§4) and never invents an operation: it reaches a registered `Capability` (File 05), produces a route-recorded direct invocation or `RunIntent` trigger (File 03), commits a `Message` (File 02), issues a steering action (File 04 §17 / File 03 §12), or opens/answers an elicitation. It owns no operation declarations, no approval logic, no visibility composition, and no routing decision.
- A `ControlRail` declares its `rail_id`, its `ControlRailKind` (§3.4), the invocation lens it consumes, the gestures it accepts, its `availability_predicate` (a `WorldPredicate` per `world.state-aware-capability-availability`, File 18 §9.2 — for example, the Voice rail requires audio capture consent and an enabled microphone; the Keybinding rail requires an interactive surface), and its settings namespace.
- Every rail invocation passes through the same policy layer (File 06) and the same ledger (File 10) as an agent-initiated invocation; a direct user invocation skips the agent's permission tier (the user has authority over their own session, `cross-cutting/actions.md`) but never skips floor enforcement, typed-confirmation, or the recorded policy decision.
- The set of capabilities a rail presents is the available-capability list (`world.state-aware-capability-availability`, File 18 §9) filtered to the rail's lens (File 07 §12); a rail never presents a capability the user cannot currently invoke without a typed unavailability indicator.

### 3.4 `ControlRailKind`

`ControlRailKind` is closed-canonical with the `Custom { namespace, name }` extension. The canonical baseline:

- `Conversation` — the always-available text input surface; the primary entry rail (§5)
- `CommandPalette` — the search-over-everything command rail (§6)
- `Keybinding` — the keyboard-chord rail (§7)
- `SlashCommand` — the slash-token and custom-command rail (§8)
- `Voice` — the voice and handsfree rail, including its handsfree session variant (§9)
- `Menu` — menus, context menus, toolbars, buttons, and selection-scoped floating actions as invocation surfaces (§6.4)
- `Trigger` — non-interactive entry from fired scheduler, event, webhook, and file-watch signals (§11)
- `ExternalProtocol` — invocation from outside the application: external MCP client, CLI, deep link (§12)

A registered extension rail declares `Custom { namespace, name }` where `namespace` matches the capability sourcing taxonomy (`capability.capability-source`, File 05 §9.1). Adding a canonical kind is a canonical-spec change; runtime extension uses `Custom`. `ControlRailKind` classifies the rail's modality; it never gates which capabilities the rail may reach — every rail reaches the one registry, filtered only by its lens and the available-capability list.

### 3.5 What a `ControlRail` Is Not

A `ControlRail` is not a `Capability` (it reaches one), a `ToolSurface` or its lens (it consumes one), a work surface (it invokes one), a presentation surface (it is an input mechanism), a `UiMode` (it may set one), an autonomy or participation mode (§17), or a private registry, approval, execution, or routing path (§16).

### 3.6 Boundary

This section fixes the rail primitive and its kind catalogue. The per-rail behavior is §§5–13; the registry and lifecycle are §14. Work-surface and subsystem specs declare which capabilities their control affordances bind to which rails; the UI specs render them.

## 4. The Input-Resolution Contract

Anchor: `controlrail.input-resolution`

### 4.1 Definition

The input-resolution contract is the rule that every rail turns a gesture into exactly one `RailResolution` outcome, and that the outcome is dispatched through the shared pipelines the owning files define. The `RailResolution` set is closed:

- `InvokeCapability { capability_id, args }` — the gesture deterministically names a capability; the rail dispatches it through `run.call-pipeline` (File 04 §8.2) as a route-recorded `user_invoked_action` (`routing.trigger-kinds-routing`, File 03 §2.1). The router model is not called unless the capability or run explicitly requests semantic routing.
- `RouteRequest { trigger, trigger_context }` — the gesture is a request to perform work whose route is not deterministic (a conversation message, an ambiguous voice utterance, an external request without a deterministic target); the rail produces the trigger and routing produces the `RunIntent` (File 03)
- `CommitMessage { message }` — the gesture is a transcript input that commits a `Message` (File 02 §3) and then routes per `RouteRequest`
- `Steer { steering_action, target_run }` — the gesture steers running work; the rail resolves it to a `run.user-intervention` (File 04 §17.1) action or a `routing.mid-execution-reroute` (File 03 §12) request (§10)
- `PreDispatchTransform { transform, pending_input }` — the gesture is resolved by a deterministic pre-dispatch transformation (reference/mention/slash/paste expansion, duplicate detection) before any of the above, per `intent.message` (File 02 §3.4) and the pre-routing transformations of `routing.routing-frame` (File 03 §3.1); the transform shapes what is dispatched, it does not decide where
- `OpenElicitation { elicitation }` — the system or rail needs typed user input before proceeding (§13)
- `AnswerElicitation { elicitation_id, response }` — the user answers an existing elicitation through any compatible rail (§13)
- `NoOp { reason }` — the gesture resolves to no work (a local UI action, an unbound chord, a cancelled palette); recorded where consequential, dispatched nowhere

### 4.2 Resolution Order

A rail resolves a gesture in a fixed order so resolution is deterministic and inspectable:

1. **Structural parse.** The rail parses the gesture into its structural parts: command token, selected menu item, key chord, spoken transcript, external source, arguments, references, and current surface context.
2. **Deterministic match.** If the parsed gesture deterministically names a capability or steering action (a capability id from a palette selection, a chord bound in the active keybinding context, a slash token resolving to a custom command, a stop button), the rail produces `InvokeCapability`, `Steer`, or the slash-command resolution directly. This is the deterministic-precheck path (File 03 §3.2): the router model is skipped, the route record is still produced.
3. **Schema resolution.** If the outcome invokes a capability, arguments resolve against the capability's `input_schema` (File 05 §4.1). Missing or ambiguous required arguments produce `OpenElicitation`; invalid arguments produce a typed validation failure or correction elicitation, never a best-effort call.
4. **Pre-dispatch transformation.** If the gesture's content carries references, mentions, slash macros, pasted tokens, or duplicate spans, the rail applies the declared transformations (`PreDispatchTransform`) to shape the content, recording each in the ledger.
5. **Route.** Otherwise the rail produces `RouteRequest` (or `CommitMessage` then `RouteRequest`) and routing decides (File 03).

The order is the same across rails; per-rail variation is which gestures are deterministically resolvable. A rail never silently performs work outside this contract.

### 4.3 Resolution Recording

Every consequential rail resolution produces a `RailResolutionRecord` linked to downstream facts rather than duplicating them. The record carries at least: `rail_id`, `rail_kind`, `invoker`, source surface or external source, sensitivity class, redacted gesture reference, resolved outcome kind, target capability/message/route/run id when present, and policy/routing/execution cross-references.

Raw gesture content is stored only when needed and allowed by sensitivity policy. High-volume intermediate input — key-down events, pending chord steps, partial voice activity, palette cursor movement, and partially typed command input — is transient by default and not durable unless diagnostics are explicitly enabled with a retention class and sensitivity label.

### 4.4 The Unified-Invocation-Path Invariant

A capability reached through any rail is the same capability with the same declaration, the same policy evaluation, the same touched-resource checks, the same ledger attribution, and the same execution pipeline. There is no per-rail operation handler, no "palette version" of a capability distinct from its "voice version," and no rail that executes outside `run.call-pipeline` (File 04 §8.2). The provider-facing agent tool list is generated from the registry (`surface.presentation-in-model-request`, File 07 §11), the palette/voice/shortcut surfaces are projections of the same registry (File 07 §12), and a user invocation and an agent invocation of the same capability differ only in the `Invoker` recorded and the permission-tier path taken (File 06 §4.3). This is the load-bearing invariant of the layer; a rail that violates it is an Explicit Rejection (§20).

### 4.5 Availability

A rail presents only the capabilities the availability evaluator (`world.state-aware-capability-availability`, File 18 §9) marks available for the current scope and world state, filtered to the rail's invocation lens (File 07 §12) and the rail's own `availability_predicate` (§3.3). A gesture that names an unavailable capability resolves to a typed `RailResolutionUnavailable` outcome surfaced in the rail's modality (a greyed palette entry, a spoken "that's not available right now," a chord that does not fire), never a silent failure or an invocation that fails downstream. Availability is recomputed event-first (`world.state-change-events-reactivity`, File 18 §12); a rail does not poll.

### 4.6 Boundary

This section owns the resolution contract and the closed outcome set. File 03 owns routing once a `RouteRequest` is produced, File 04 owns execution once an `InvokeCapability` or `Steer` is dispatched, File 06 owns the authority decision, File 18 owns availability. The rail produces the outcome; those files carry it out.

## 5. The Conversation Rail

Anchor: `controlrail.conversation-rail`

### 5.1 Definition

The Conversation rail is the text input surface through which the user composes and submits transcript input — the always-available primary entry rail. It is the entry behavior over `intent.conversation` (File 02 §2.1) and `intent.message` (File 02 §3); it commits a `Message` and produces a `RouteRequest`, applying pre-dispatch transformations first.

### 5.2 Rule

- The Conversation rail accepts composed input (multi-line text, attachments, pasted content, mentions, references, and inline slash tokens) and, on submission, produces `CommitMessage` followed by `RouteRequest` (§4.1). The submitted message commits as a `MessageUser` block (`block.kind-catalogue`, File 08 §3.1) through the canonical commit boundary; the rail does not bypass conversation attachment, work-line ownership, or routing (`intent.run-intent`, File 02 §4.3).
- The rail applies the **pre-dispatch transformation contract** before dispatch (`PreDispatchTransform`, §4.1): expansion of references (pasted-text tokens, attached files, mention or `@`-references, slash-command macro expansion), detection of conditions resolvable before routing (duplicate content already in context per `context.duplicate-overlap-handling` File 13 §8, repeated identical requests, references to prior blocks), and non-destructive presentation of resolution choices. Each transformation is recorded in the ledger with what was detected and what the user override (if any) decided (`intent.message`, File 02 §3.4). The transformations shape what the router sees; they are not deterministic prechecks and do not decide where the request dispatches (`routing.routing-frame`, File 03 §3.1).
- Duplicate handling follows `kuzeys-context-duplicate-prompt-handling-addendum.md` as realized in File 02 and File 13: the rail prefers referencing existing context over re-sending duplicated text, presents a fast, non-destructive, reversible, send-scoped choice (reference / drop-duplicate / include-anyway / edit), and records the decision. A short auto-continue countdown is a permitted convenience but never a correctness condition; correctness never depends on elapsed time (`core.event-first-by-default`, File 01 §7.15).
- The rail exposes **queue-versus-interrupt** behavior for input submitted while a run is executing: the new input attaches to the same or a new intent thread per `intent.intent-thread` (File 02 §5.5) and the in-flight run is interrupted, queued, summarized-and-continued, or superseded per the user-configurable setting (`run.retry-reroute-branch`, File 04 §19). Mid-execution input never silently abandons an in-flight run.
- The rail surfaces in-place transcript affordances — retry, edit, branch, and quote-back — as invocations of the capabilities `intent.message` (File 02 §3.1) and `run.retry-reroute-branch` (File 04 §19) define; they resolve through §4 like any other gesture.
- The Conversation rail is a control rail, never the universal container. The user may stay entirely in the conversation interface (`intent.presentation`, File 02 §8.2) or move to a work-surface focus; the transcript is not forced to occupy the primary pane (`worksurface.activation-shell`, File 25 §11.3).

### 5.3 Boundary

This section owns the conversation-rail entry behavior and the pre-dispatch transformation framing. File 02 owns conversation, message, and the submission lifecycle; File 03 owns the pre-routing transformations and routing; File 13 owns duplicate-overlap detection and context assembly; File 08 owns the committed message block. The rail invokes them.

## 6. The Command Rail

Anchor: `controlrail.command-rail`

### 6.1 Definition

The Command rail is the command palette: the unified search-over-everything surface through which the user discovers and invokes any available capability by name. It consumes the `Palette` lens (`surface.presentation-in-user-facing-surfaces`, File 07 §12.1) and the available-capability list (File 18 §9), and on selection produces `InvokeCapability` (§4.1).

### 6.2 Rule

- The Command rail is invoked by a keybinding (the canonical default chord is a settings value, not a canonical constant) and sets the `CommandPalette` `UiMode` (`world.surface-state`, File 18 §5.5) while open. It searches the available-capability list filtered to the `Palette` lens; any capability registered anywhere that is currently available and palette-invokable appears, with no per-surface palette. The palette is subsystem-neutral.
- Search is fuzzy over capability display fields (`capability.display-fields`, File 05 §3.2 — `name`, `short_description`, `id`, `tags`) and ranks by match quality, recency, and frequency, with category grouping and a recents section. Ranking is a presentation convenience, not authority: the ranking influences order only, never whether a capability may be invoked (`policy.effective-tier-resolution`, File 06 §4 decides that at invocation). Ranking thresholds, boosts, result caps, and history retention are settings, not canonical constants.
- On selection the rail produces `InvokeCapability`. When the capability's `input_schema` (`capability.input-schema`, File 05 §4.1) declares required arguments the gesture has not supplied, the rail opens an elicitation (§13) to collect them before dispatch, rather than dispatching an invalid call.
- The Command rail presents each entry's resolved effective tier indicator (`policy.effective-tier-resolution`, File 06 §4 — "requires approval," "typed-confirmation," "blocked," "trusted") and its `availability_status` (`capability.registered-capability`, File 05 §10) so the user sees the policy consequence before invoking; the indicator is read from File 06, never recomputed.
- A keybinding bound to more than one capability in the active context resolves through the keymap (§7); the Command rail may present a disambiguation elicitation listing the candidate capabilities.
- A quick-open variant of the Command rail searches a registered catalog or index (workspace files, recent entities, artifacts, indexed records) rather than the capability registry itself. Selection still resolves to `InvokeCapability` (open, reveal, attach, insert, or equivalent); the searchable catalog is owned by retrieval, workspace, artifact, or UI specs, never by a private command-rail store.

### 6.3 Slash-in-Palette and Slash-in-Conversation

A slash token typed into the Conversation rail or the Command rail resolves through the Slash-Command rail (§8); the Command rail is one presentation of the slash grammar, the Conversation rail another. The grammar and resolution are §8's; the presentation is the rail's.

### 6.4 Menus, Toolbars, and Buttons

The `Menu` rail kind covers menus, context menus, toolbars, buttons, and selection-scoped floating actions as invocation surfaces. A menu item, toolbar button, context-menu entry, or selected-text floating action is a presentation of a capability (`worksurface.actions-declaration`, File 25 §6.4, `cross-cutting/actions.md` consumers); selecting it produces `InvokeCapability` through §4 like a palette selection. Selection-scoped actions filter the available-capability list by the current `Selection` (File 18) and never use a private floating-action registry. A native operating-system menu or tray item bridges to a capability invocation through the same contract (`sidex-compressed.md`'s native-menu→event bridge; `distribution/packaging.md`'s global shortcut and tray item). The `Menu` rail presents only available capabilities (§4.5) and shows the same policy indicators (§6.2).

### 6.5 Boundary

This section owns the command-rail and menu-rail behavior — invocation, search-as-presentation, argument elicitation, and execution. File 07 owns the `Palette` lens and what is visible; File 18 owns availability and the `CommandPalette` `UiMode`; File 05/06 own the capability and its policy; the UI specs own layout, search rendering, and the details panel. The rail composes them.

## 7. The Keybinding Rail and the Keymap

Anchor: `controlrail.keybinding-keymap`

### 7.1 Definition

The Keybinding rail is the keyboard-chord rail: it parses keyboard input into a `KeyBinding` and resolves it, in the active keybinding context, to a capability or steering action. The keymap is the model of bindings, contexts, and resolution. This section is the realization of the keybinding spec `surface.presentation-in-user-facing-surfaces` (File 07 §12.3) delegated to this file.

### 7.2 `KeyBinding` and the Chord Grammar

A `KeyBinding` is an ordered sequence of one or more `Keystroke`s (a chord; multi-key sequences are supported). Each `Keystroke` carries a normalized key identifier and the modifier set (`ctrl`, `shift`, `alt`, `meta`). The binding maps to a `capability_id` or steering action, or to the null action — a binding whose action is null is an explicit **unbind** that overrides a built-in binding in the same context. `KeyBinding` values are `KeyboardShortcut`-semantics settings (`settings.types-semantics-constraints`, File 15 §4.2); a capability's `default_shortcut` (`capability.display-fields`, File 05 §3.2) is a default, never a contract, and the user may rebind it.

### 7.3 Keybinding Contexts and the Context Stack

A keybinding context is a named scope within which a binding is active (for example: a global context, the conversation input, an editor, a modal dialog, the command palette, a search overlay, a vim mode, a permission dialog, an elicitation panel). Contexts compose as a **stack** derived from live presentation and focus state: a surface, panel, or dialog that owns a context contributes it while active, so the active context set is the current stack with the most-recently-active context on top. The keybinding context is informed by the live `UiMode` and the active `SurfaceState`/`PanelState` (`world.surface-state`, File 18 §5) — opening the command palette contributes the palette context as it sets the `CommandPalette` `UiMode`, a modal contributes a modal context — but the context stack is the keymap's resolution input, not a field File 18 owns.

### 7.4 The Resolver

Keybinding resolution is a deterministic, pure function of the parsed input, the active context stack (top first), the registered bindings, and any pending chord. It walks the active contexts top-down and returns the first matching binding's outcome; the first binding that matches wins, so a context higher on the stack overrides a binding in a lower context (a modal's Escape binding wins over the global Escape). A multi-key chord extends non-durable pending-chord rail state and returns a chord-in-progress result until the sequence completes, is explicitly cancelled, receives incompatible input, loses its active context, or reaches a configurable safety guard. The resolver holds no state itself; the rail session owns pending-chord state. A resolved capability or steering action is dispatched through §4. This single resolver supersedes scattered per-component key listeners; conflicts are resolved by context-stack priority, not by registration order across components.

### 7.5 Conflict Resolution, Unbind, and Platform Reality

- Two capabilities bound to the same chord in the same context are a conflict. Registration detects it and emits `ShortcutConflict` (`surface.surface-relevant-events`, File 07 §12.3); the user resolves it through a declared priority order in settings, and the Command rail may present a disambiguation choice (§6.2). A user-bound shortcut overrides a capability's `default_shortcut`.
- The null-action unbind (§7.2) lets a user or a context suppress a built-in binding without rebinding it to something else.
- Modifier and platform reality is explicit: the meta modifier (Command on the relevant platform) is not available on every platform; a binding to a modifier the current platform does not expose simply never fires, and the keymap surfaces a typed validation diagnostic for it. User keybinding configurations are validated against the registered capability set; an unknown capability id produces a typed validation error with a suggestion, never a silently dropped binding.

### 7.6 Boundary

This section owns the keymap — the `KeyBinding` grammar, the context-stack model, the resolver, conflict resolution, the unbind, and the platform-reality and validation rules. File 05 owns the `default_shortcut` declaration and `find_by_shortcut`; File 15 owns the stored rebinding; File 18 owns the `UiMode`/`SurfaceState` the context is informed by; File 07 owns the `Shortcut` lens and `ShortcutConflict` event; the UI specs own key capture and the keybinding editor. The keymap resolves; those layers store, surface, and render.

## 8. The Slash-Command and Command-Definition Rail

Anchor: `controlrail.slash-command-rail`

### 8.1 Definition

The Slash-Command rail resolves a slash token (a leading-slash gesture in the Conversation or Command rail) to a command, where a command is either a registered capability or a user/workspace/plugin-authored command definition that expands to a capability invocation or a templated prompt. Custom command definitions are stored in `workspace.internal-layout` (File 24 §8.3)'s `.atlas/commands/`.

### 8.2 Rule

- A slash command is named with a namespaced grammar (`/command` for the default namespace, `/namespace:command` for a qualified one), aligning with the capability sourcing taxonomy (`capability.capability-source`, File 05 §9.1). The rail parses the token and its arguments, resolves the command, and produces `InvokeCapability` (when the command binds to a capability) or `CommitMessage`/`RouteRequest` (when the command expands to a templated prompt that becomes conversation input) per §4.
- A custom command definition is declarative — it carries a name, an optional default shortcut, optional argument parameters with templating, and either a capability binding or a prompt template — and is resolved through the capability system, never an out-of-band execution path (`workspace.internal-layout`, File 24 §8.3). A capability-binding command resolves directly to `InvokeCapability`; a prompt-template command expands its arguments into a message and resolves through `CommitMessage`/`RouteRequest`, with any instruction content it contributes attributed per `context.instruction-sources-workspace-files` (File 13 §16). Argument templating substitutes the gesture's arguments into the command's parameter slots before resolution. Prompt-template expansions are user-authored or source-authored content, never governing instructions by default.
- Custom command definitions register through the same proposal-first, source-approval-governed registration framework as other extension declarations (`policy.source-approval-flow`, File 06 §9); they are command declarations stored as durable workspace state (File 24 §8.3), not hidden rail behavior and not `CapabilityDeclaration`s unless they bind or define a capability. Command resolution follows a precedence order across sources (workspace over user over plugin over built-in, by the same layered-resolution discipline the canon uses); the resolved precedence is inspectable, and a name collision surfaces source attribution or disambiguation rather than a silent winner. Precedence chooses a definition; it never upgrades source trust, instruction authority, permission floors, or policy treatment. Plugin commands cannot silently shadow built-in or user-defined names, and policy may protect security-sensitive built-in names from shadowing.
- A slash command never confers authority a capability does not have: the resolved capability's effective tier (`policy.effective-tier-resolution`, File 06 §4) applies, and a prompt-template command that contributes instruction text is untrusted-or-user-authored data per its source (`context.authority-classes`, File 13 §2.3), never an authority grant.

### 8.3 Boundary

This section owns the slash grammar, command-definition resolution, argument templating, and precedence. File 24 owns the `.atlas/commands/` store; File 05 owns any capability a command binds to; File 06 owns source approval; File 02/File 13 own the message and instruction-source the prompt-template form produces. The rail resolves; those layers store, register, and execute.

## 9. The Voice and Handsfree Rail

Anchor: `controlrail.voice-rail`

### 9.1 Definition

The Voice rail is the spoken-input rail and its handsfree session variant: it composes audio capture and transcription, resolves the transcript to a capability or message against the available-capability list, optionally confirms, executes, and may request spoken presentation of the result. It composes `perception.sensor` (File 19 §4.3)'s `Audio` sensor and transcription; it sets the `Handsfree` `UiMode` (`world.surface-state`, File 18 §5.5) when operating as a continuous session.

### 9.2 Rule — the Voice Session

- The Voice rail session proceeds: optional wake-word activation, audio capture, voice-activity-gated transcription, registry-derived intent resolution, optional confirmation, execution through §4, and optional spoken output. Audio capture, voice-activity detection, wake-word detection, chunking, and transcription are owned by `perception.sensor` (File 19 §4.3) and the transcription capability (`perception.capability-surface`, File 19 §14); the rail consumes them and owns the session that turns a transcript into a `RailResolution`. Spoken output is requested through the appropriate text-to-speech, provider, audio, or presentation capability path; the rail does not own synthesis, caching, playback, or output-device routing.
- **Intent resolution is registry-derived.** A transcript resolves to a voice-invokable capability in the current available-capability list (`world.state-aware-capability-availability`, File 18 §9, filtered to the `Voice` lens, `voice-invokable` tag) using the live `SurfaceState` (File 18 §5) as context — "click the second tab" resolves against the panel list, "format this" against the current `Selection`. There is no fixed spoken-intent enumeration: the deletion of a hardcoded `SpokenIntent` set in favor of registry-derived intents (`unit15-ux-distribution-files-glossary.md` D15.UX.4) is canonical, because a fixed enum would gatekeep against `core.extension-planes` (File 01 §6.14) and duplicate the registry. When confidence is below the configured threshold, the rail falls back to a disambiguation elicitation (§13) — for the command palette, the top match highlighted — rather than guessing.
- **Full capability, different modality.** Voice is a different modality over the one capability system, not a degraded feature set (`ux-input/whiteboard-and-handsfree.md`). Any eligible operation can be exposed through voice using the same capability, policy, routing, and execution path, subject to the `Voice` lens, the `voice-invokable` declaration, availability, confidence, and confirmation requirements. Voice produces the same `RailResolution` outcomes and passes the same policy and routing.
- **Consent and wake-word gating are File 19's.** Audio capture is consent-gated, and wake-word detection requires standing audio-capture consent plus separate explicit enablement, never enabled by default, as a side effect of another grant, or by a profile or automation without typed-confirmation (`perception.consequences-for-later-specs`, File 19 §19 and File 19 §10.2). The rail honors these; it never captures or activates outside the granted scope.
- A confirmation step (spoken or visual) before executing a steering or high-tier action is a configurable rail behavior composing the policy elicitation (`policy.approval-ui-surface-contract`, File 06 §13); typed-confirmation and `permission_floor` are never lifted by voice.
- A companion-app form of the Voice rail (a lightweight quick-capture / quick-query / dictation entry invoked by a global shortcut) is the same rail over an external-entry transport (§12); it sends transcribed input to the runtime through the same resolution contract.

### 9.3 Boundary

This section owns the voice-session contract and the registry-derived intent resolution. File 19 owns audio capture, VAD, wake-word, transcription, and consent; File 18 owns the `Handsfree` `UiMode` and the available-capability list; File 06 owns confirmation; File 05 owns the voice-invokable capability. The rail composes them into a session.

## 10. The Steering Rail

Anchor: `controlrail.steering-rail`

### 10.1 Definition

The Steering rail is the set of user-facing affordances through which the user steers running work: stop, cancel, pause, resume, interject, take over, redirect, and barge-in. It resolves a steering gesture to a `Steer` outcome (§4.1) that dispatches to `run.interruption-pause-cancellation` (File 04 §17) or `routing.mid-execution-reroute` (File 03 §12). This is the user-facing realization of `core.invariants` (File 01 §7.11)'s "Atlas-managed long-running work must remain under user control."

### 10.2 Rule

- A steering gesture — a stop or cancel button, an Escape chord in the appropriate keybinding context (§7), a `/stop`-style slash command (§8), a spoken "stop" (§9), an interject or takeover control, or a follow-up message submitted while a run executes (barge-in) — resolves to a `Steer` outcome naming the steering action and the target run. The action is one of `run.user-intervention` (File 04 §17.1)'s set: continuation with new instruction, pause, cancellation, branch, reroute, approval grant or denial, scope narrowing, or explicit takeover (the run's `control` flips to `User`, File 04 §2.6 / §17.1). The rail issues the action; File 04 carries it out.
- Cancellation through the rail honors `run.cancellation` (File 04 §17.3): the rail offers, at minimum, cancel the run, cancel the run and its child-run tree, cancel a specific child run, cancel a specific tool call, and cancel a specific sandbox or process; the default action and the expanded options are user-customizable. The rail surfaces cooperative-stop state, forceful-escalation availability, affected targets, and user actions before escalation. If a countdown is shown, it is only a configurable presentation of File 04's safety guard, never a correctness condition. The rail never owns the cancellation mechanism; it selects the target and the cooperative-versus-forceful preference File 04 enforces.
- **Queue-versus-interrupt.** A follow-up submitted during execution resolves per the user-configurable mid-execution-input setting (`intent.intent-thread`, File 02 §5.5, `run.retry-reroute-branch` File 04 §19): interrupt, queue, summarize-and-continue, or supersede. A barge-in that the user configures as an interrupt resolves to a cancellation-or-reroute `Steer`; one configured as a queue attaches the input without disturbing the in-flight run. The rail exposes the choice; it never silently abandons an in-flight run.
- Takeover and interject are recorded as run inputs (`run.user-intervention`, File 04 §17.1): a takeover flips run `control` to `User` and records subsequent user actions as first-class blocks; on return of control the agent receives whatever summary the user supplies, with no flow blocking on it. The Steering rail surfaces takeover and interject as affordances; File 04 owns the mechanics.

### 10.3 Boundary

This section owns the steering-affordance contract — which gestures resolve to which intervention. File 04 owns the intervention and cancellation mechanics and the run `control` field; File 03 owns mid-execution reroute; File 02 owns the mid-execution-input continuity decision. The rail issues the steering action; those files carry it out.

## 11. The Trigger Rail

Anchor: `controlrail.trigger-rail`

### 11.1 Definition

The Trigger rail is non-interactive entry from a fired scheduler event, observed event, inbound webhook, or file-system change that invokes work without a human at the keyboard. It frames these as a rail kind whose resolution is a `RouteRequest` (§4.1) carrying the `automation` or `external_event` trigger kind (`routing.trigger-kinds-routing`, File 03 §2.1); the deep mechanics are delegated.

### 11.2 Rule

- A trigger gesture is an inbound fired signal (a scheduler-fired event, a watch threshold crossing, a webhook payload, a file-change notification) that the Trigger rail resolves to a `RouteRequest` with the trigger payload as the routing-frame trigger context (`routing.routing-frame`, File 03 §3.1). The resulting `RunIntent` may be pinned at save time (`routing.trigger-kinds-routing`, File 03 §2.1); routing fills the unpinned fields. The trigger-originated run uses the same run model as a user-originated run (`run.run`, File 04 §2.3); background execution is not a separate architecture.
- A trigger-originated run attaches to an owning intent thread that outlives its trigger (`intent.intent-thread`, File 02 §5.3); it passes the same policy (File 06) and produces the same ledger record as any other invocation. Triggers are observed event-first where the source emits events; a polling interval is a flagged, configurable fallback only where no change events exist, and never a correctness condition (`core.event-first-by-default`, File 01 §7.15).
- The Trigger rail frames the entry; it does not own trigger scheduling, source observation, eligibility, non-interactive-execution safety, enablement, or the trigger taxonomy. Those are owned by File 33 (Automation and Triggers) and the producer specs, which consume this rail's framing and the routing trigger-kind contract. A trigger that invokes a capability the policy layer would gate non-interactively follows the source-trust and approval rules of File 06; a non-interactive context cannot silently auto-approve a capability whose tier requires a human decision.

### 11.3 Boundary

This section frames the Trigger rail kind and its resolution to a `RouteRequest`. File 03 owns routing for the `automation`/`external_event` trigger kinds; File 04 owns the run model; File 33 (Automation and Triggers) owns scheduling, eligibility, enablement, and non-interactive-execution safety. This file names the rail; that spec realizes the triggers.

## 12. The External-Protocol Rail

Anchor: `controlrail.external-protocol-rail`

### 12.1 Definition

The External-Protocol rail is invocation from outside the application: an external client speaking the MCP server protocol, a command-line invocation, or a deep link or URL scheme. It resolves an external gesture to a `RailResolution` over the externally-exposed lens (`surface.presentation-in-user-facing-surfaces`, File 07 §12.6, the `external-exposed` tag and source-approval gate).

### 12.2 Rule

- An external gesture (an external MCP client invoking an exposed tool, a CLI subcommand, a deep link naming a capability and arguments) resolves to `InvokeCapability` or `RouteRequest` through §4, exposed only to the externally-exposed capability set the source-approval policy permits (`policy.source-approval-flow`, File 06 §9, `surface.presentation-in-user-facing-surfaces` File 07 §12.6). A capability not tagged for external exposure is unreachable through this rail regardless of its visibility in other rails.
- Every external gesture carries source identity, transport kind, origin metadata, and authenticated or locally trusted session context where applicable. A deep link or external call that supplies arguments for a consequential action resolves to preview, elicitation, or approval before mutation unless an explicit valid lease covers the exact action. External entry never turns an untrusted URL or client payload into silent mutation.
- The External-Protocol rail passes the same policy, routing, and ledger as any rail; an external invocation is an `Invoker` recorded with its source identity (`cross-cutting/actions.md`'s sync/external invoker distinction), and its permission tier and floor apply. The CLI form invokes the same service-layer capabilities the GUI rails reach (`core.invariants`, File 01 §7.7 — the CLI and the palette query the same registry); state awareness and availability resolve to a headless descriptor when no interactive surface is active (`world.surface-state`, File 18 §5.2).
- The External-Protocol rail frames the entry; it does not own MCP transport, the plugin install lifecycle, or external-API definition formats. File 36 (MCP and External Integrations) and File 35 (Extension and Plugin System) own those and consume this rail's framing.

### 12.3 Boundary

This section frames the External-Protocol rail and its resolution over the externally-exposed lens. File 07 owns the external-exposure lens; File 06 owns source approval; File 36 (MCP and External Integrations) and File 35 (Extension and Plugin System) own transport and definitions. This file names the rail; those specs realize the protocols.

## 13. The Elicitation Contract

Anchor: `controlrail.elicitation`

### 13.1 Definition

An elicitation is a typed request the system makes, through a rail, for user input it needs before proceeding: approval, clarification, a choice among options, a correction, or an intervention prompt. It opens through `OpenElicitation` and is answered through `AnswerElicitation` (§4.1). `policy.approval-ui-surface-contract` (File 06 §13)'s approval request is the policy-specific case of elicitation.

### 13.2 Rule

- An elicitation carries its kind (approval, clarification, choice, correction, intervention), the prompt, the typed options or input shape, and the rail-agnostic data the rendering rail consumes. The same elicitation may be answered through any rail capable of it — a modal in the GUI, a spoken confirmation in the Voice rail, an inline confirmation in the Command rail, a CLI prompt in the External-Protocol rail — and the answer flows back through one typed response channel (`policy.approval-ui-surface-contract`, File 06 §13.8's decoupling). A response is linked to the original elicitation id; it is not a new unrelated command. The kind set is closed-canonical-plus-`Custom`.
- An approval elicitation is exactly `policy.approval-ui-surface-contract` (File 06 §13)'s `ApprovalRequest`/`ApprovalResponse` — this file does not re-own approval; it places it as one elicitation kind. A clarification, choice, or correction elicitation is the agent-asks-user primitive (`unit11-cross-tool-learning.md` CT.2's `ui.elicit`, `unit15-ux-distribution-files-glossary.md` D15.UX.1's unified elicitation with an `Intervention` kind) through which a run requests input mid-work without a separate ad-hoc channel.
- An elicitation is non-blocking on rails that cannot answer it and never silently auto-resolves: a high-tier or typed-confirmation elicitation always asks (`policy.permission-floor-typed-confirmation`, File 06 §7); a clarification a run raises pauses that unit (`run.user-intervention`, File 04 §17.1) until answered or cancelled.

### 13.3 Boundary

This section owns the general elicitation contract and the rule that approval is one of its kinds. File 06 owns the approval request/response and its options; File 04 owns the run-side pause an unanswered clarification produces; the UI specs render each kind per rail. The rail opens or answers elicitations; those layers enforce the consequence.

## 14. The `RailRegistry` and Rail Lifecycle

Anchor: `controlrail.registry`

### 14.1 Definition

The `RailRegistry` is the one registry of registered control rails. It admits a rail declaration, pairs it with mutable registry state, and exposes lookup, enumeration, enable/disable, and the registration event stream. Built-in, plugin, and user-defined rails use the same declaration and lifecycle shape; their source trust, approval state, and default enablement remain source-specific.

### 14.2 Rule

- There is one `RailRegistry`. No subsystem, plugin, or surface introduces a parallel rail registry or a private rail store. Built-in rails (the `ControlRailKind` baseline) ship registered; plugin and user-defined rails (a stream-deck rail, an ops-channel, a gamepad rail) register through source-approved rail registration proposals, using the same proposal-first governance as other extension declarations (`policy.source-approval-flow`, File 06 §9). A source registration may include capabilities, rails, hooks, events, sensors, or other extension declarations, each with its own schema. A rail declaration is durable and reconstructs at startup; its live state (active sessions, the keybinding context stack, an open palette) is computed and re-derived, never a durable fact (`core.projection`, File 01 §6.11).
- Same path does not mean same trust: source class, trust level, approval state, declared authority, visibility defaults, and policy constraints remain source-specific. Built-in rails may ship enabled by default; plugin and user-defined rails enter through source approval and settings.
- A rail declaration carries its `rail_id`, `ControlRailKind`, the invocation lens it consumes, the gestures it accepts, its `availability_predicate`, its settings namespace, and the events it emits. Registration validates the declaration; a rail that reaches for a private registry, approval, execution, or routing path (§16) cannot register. Registry mutations emit events so the shell, the keymap, and availability react without polling.
- A disabled rail is preserved and inspectable but accepts no gestures; an unavailable rail (its `availability_predicate` fails — no microphone for the Voice rail, no interactive surface for the Keybinding rail in a headless context) presents its unavailability rather than failing silently.

### 14.3 Boundary

This section owns the rail registry and lifecycle. File 06 owns source approval; File 20 owns physical persistence; File 35 (Extension and Plugin System) owns the plugin rail's install lifecycle and cross-extension registration packaging. This file declares the rail registration contract; those files realize it.

## 15. The Shell Relationship

Anchor: `controlrail.shell-relationship`

### 15.1 Rule

- The application shell is a persistent command rail plus a primary focus surface, secondary inspectors, an execution console, and an artifact navigator, with conversation as an always-available view the user can expand or collapse (`worksurface.activation-shell`, File 25 §11.3, `codex_recommendations.md` §10.1). This file owns the rail side of that relationship — the always-available control rails (conversation, command palette, keyboard, voice) and their composition with the focus surface — and references File 25 for the shell relationship and the UI specs for rendering. The shell keeps command entry always close while the primary surface is whatever the work needs.
- Rails are global or surface-scoped: the conversation, command palette, keyboard, and voice rails are globally available; a rail or a binding may be scoped to a work surface or panel through its `availability_predicate` and the keybinding context (§7.3). A rail's availability and a binding's context are resolved against the live `SurfaceState` (`world.surface-state`, File 18 §5); opening or focusing a surface may change which rails and bindings are active for that scope without changing any active run's execution context (`worksurface.activation-shell`, File 25 §11.2).

### 15.2 Boundary

This section owns the rail side of the shell relationship. File 25 owns the shell relationship and the focus-surface composition; File 18 owns the live surface state rails resolve against; the UI specs own shell geometry, layout, and navigation. This file places the rails; those layers render them.

## 16. The No-Private-Architecture Invariant

Anchor: `controlrail.no-private-architecture`

### 16.1 Rule

A `ControlRail` owns only its modality's gesture-handling and resolution. It must reuse, never privately reimplement, all of the following through each one's canonical contract:

- **capabilities** — a rail reaches `Capability` ids in the one registry; no per-rail operation handler, no parallel registry (`capability.consequences-for-later-specs`, File 05 §20)
- **policy** — a rail invocation passes the one policy layer; no per-rail approval, no floor bypass, no typed-confirmation lift (`policy.consequences-for-later-specs`, File 06 §18)
- **tool surfaces** — a rail consumes the lens File 07 composes; no parallel visibility model, no per-rail capability list (`surface.consequences-for-later-specs`, File 07 §20)
- **routing** — a rail produces a trigger; routing produces the `RunIntent`; a rail does not route itself (`routing.consequences-for-later-specs`, File 03 §15)
- **execution** — a rail dispatches through the one capability-call pipeline and issues steering through the one intervention model; no private execution or cancellation path (`run.consequences-for-later-specs`, File 04 §29)
- **conversation** — the Conversation rail commits through the one message lifecycle; no private transcript model (`intent.consequences-for-later-specs`, File 02 §10)
- **world model and availability** — a rail reads the one `SurfaceState`, `UiMode`, and availability evaluator; no private state store, no screen-scraping of its own surface (`world.consequences-for-later-specs`, File 18 §17)
- **perception** — the Voice rail composes the one audio sensor and transcription; no private capture pipeline (`perception.explicit-rejections`, File 19 §18)
- **settings** — rail configuration is namespaced settings keys plus profile layers; no per-rail config store, no new durable scope (`settings.consequences-for-later-specs`, File 15 §21)
- **workspace** — the Slash-Command rail resolves command definitions in the one `.atlas/commands/` store; no parallel command store (`workspace.consequences-for-later-specs`, File 24 §24)
- **ledger and events** — rail facts flow through the one bus and ledger; no side-channel notification (`ledger.execution-ledger`, File 10 §3.8)
- **service-layer ownership** — a rail's resolution logic lives in the backend service layer; command wrappers and the renderer are adapters (`core.invariants`, File 01 §7.7)

### 16.2 Conformance Is Structural

The invariant is structural, not advisory: the one capability registry, one policy layer, one routing layer, and one execution pipeline make a private rail path unreachable by construction, and the registration validator (§14.2) rejects a rail declaration that reaches for one. A rail that resolves gestures to capabilities through §4 and reuses the substrate conforms by construction.

### 16.3 Boundary

This section consolidates the per-substrate reuse rules each owning file fixes and applies them to rails. The substrate files own each contract; this file requires the rail to reuse it.

## 17. Participation, Autonomy, and Mode Deletion

Anchor: `controlrail.no-autonomy-field`

### 17.1 Rule

- A `ControlRail`, its declaration, and its live session carry no `participation_level`, `autonomy_mode`, `interaction_shape`, `persona`, or phase field, in any form, at any layer. This is the unanimous, most-evolved position across the canon (`cross-cutting/state-awareness.md` "deleted … does not exist at any layer"; `worksurface.no-autonomy-field`, File 25 §13; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections`, File 01 §8; `world.surface-state`, File 18 §5.5; `settings.explicit-rejections`, File 15 §20). The residual `Drive`/`Supervise`/`Collaborate`/`Delegate` framing and the `GooseMode`/`AskForApproval`/`permission-mode`/agent-mode framing that some source rails attach to invocation are the retired pattern.
- **Autonomy** comes from capability permission tiers and leases plus the user's direct commands (Files 05, 06), never from a per-rail dial. The "auto-approve" or "YOLO" toggle some source rails expose is the `approval-posture preset` and `agent.unrestricted_mode` of `policy.settings-resolution-for-policy` (File 06 §16.3), evaluated by the policy layer; it is not a rail field.
- **Voice, command-palette, and handsfree are `UiMode`s** (`world.surface-state`, File 18 §5.5), live interaction state — not autonomy controls. A "plan mode," "agent mode," or "conversation/build mode" that a source rail presents as an invocation context is a presentation lens and an approval posture, never a backend autonomy primitive; the canon couples neither autonomy nor model choice to a rail (`core.explicit-rejections`, File 01 §8).
- **Progressive disclosure** — the simple-to-power-user spectrum — comes from which rails, panels, and view presets are available, not from a per-rail mode. There is no `ParticipationLevelChanged` event because there is no participation level to change.

### 17.2 Boundary

This section owns the deletion and its rationale for rails. File 06 owns the permission tiers, leases, and approval-posture preset that provide autonomy; File 18 owns the `UiMode` that provides interaction state; File 25 §13 fixes the same deletion at the surface layer. This file fixes that a rail carries no autonomy field.

## 18. Persistence, Locality, and Settings

Anchor: `controlrail.persistence-settings`

### 18.1 Rule

- A rail's durable state — its registered declaration, its enable state, its keybinding map and user rebindings, its voice and confirmation preferences, and its custom command definitions — persists as substrate families through the one storage contract and the settings system (`settings.logical-persistence`, File 15 §17; custom command definitions are workspace state per `workspace.internal-layout`, File 24 §8.3). A rail's live state — an open palette, a pending chord, an active voice session, the keybinding context stack — is computed and re-derived, never durable (`core.projection`, File 01 §6.11).
- Every rail mechanism with meaningful variation is a setting resolved through the canonical cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2), namespaced under the rail's settings namespace; the canonical rail-owned dimensions include at least: which rails are enabled per scope; the command-palette invocation chord, ranking thresholds, result caps, and history retention; the full keybinding map, per-context bindings, conflict-priority order, and unbinds; rail-level confirmation posture for direct invocations; queue-versus-interrupt default for mid-execution input; duplicate-handling default and auto-continue convenience; spoken-presentation preference; and per-profile rail defaults (`unit15-ux-distribution-files-glossary.md` D15.UX.5 — confirmations, keyboard-shortcut visibility, handsfree suggestion). Audio capture, VAD, silence thresholds, wake-word configuration, transcription provider settings, text-to-speech provider settings, voice profile, output device, caching, playback, cooperative-stop deadlines, kill escalation, and partial-output rules are settings owned by File 19, provider/audio specs, and File 04 rather than this file. Each setting declares its locality (`settings.locality-sync-export`, File 15 §18): keybinding maps and rail preferences are syncable user preferences, device-bound bindings (a platform-specific chord) are device-local. No rail behavior with meaningful variation is a hardcoded constant (`settings.settings-over-constants`, File 15 §13).
- Each rail-related setting declares its agent exposure (`core.settings-system`, File 01 §6.8); the agent cannot read or change security-sensitive rail configuration (a keybinding bound to a destructive capability, a wake-word enablement) without policy.

### 18.2 Boundary

This section names the rail persistence and settings dimensions. File 15 owns the settings object model, cascade, locality, and agent exposure; File 24 owns the command-definition store; File 20 owns the physical persistence. This file names the dimensions.

## 19. Events

Anchor: `controlrail.events`

### 19.1 Rule

- The control-rail layer emits typed events through the one event bus and ledger (`ledger.event-stream`, File 10 §5) with the canonical envelope (`ledger.event-envelope`, File 10 §5.2). Rail-resolution and lifecycle facts register as `Custom { namespace: "controlrail", name, payload }` extensions (`ledger.custom-kind-registration`, File 10 §4.3): a gesture resolved to a `RailResolution`, a rail enabled or disabled, a keybinding conflict, a custom command registered, a voice session started or ended, a steering action issued, an elicitation opened or answered. Each declares its payload schema, cross-reference keys, default sensitivity, retention, and owner per File 10. The downstream facts a rail produces — the capability invocation, the route record, the message commit, the intervention — are emitted by their owning layers (Files 04, 03, 02), not duplicated by the rail.
- A consequential rail fact (a resolved invocation, a steering action consumed by a run) is committed to the durable record by the executor or router, never inferred from event observation (`core.durable-history-transient-coordination`, File 01 §7.3). Raw key events, continuous voice frames, palette navigation changes, cursor movement, and partially typed command input are transient by default; diagnostic capture requires an explicit setting, retention class, and sensitivity label. Voice and audio-bearing rail events carry the sensitivity of their content (`ledger.sensitivity-aware-persistence-retention`, File 10 §10); raw secret content never persists. There is no `ParticipationLevelChanged` event (§17).

### 19.2 Boundary

This section reserves the `controlrail` event namespace and declares rail-resolution and lifecycle events only. File 10 owns the envelope, delivery, sensitivity, and custom registration; Files 02/03/04/06/07/18 own the downstream events a resolution produces. This file emits through the shared mechanism.

## 20. Explicit Rejections

Anchor: `controlrail.explicit-rejections`

The following are architecturally invalid for any later or per-surface spec:

- **A rail with a private operation handler, registry, approval, execution, or routing path** — a rail resolves a gesture to a capability in the one registry, dispatches through the one pipeline, and passes the one policy layer; a per-rail operation definition, a parallel registry, a rail-owned approval, or a rail-owned execution model is forbidden (§16; `capability.consequences-for-later-specs`, File 05 §20; `surface.consequences-for-later-specs`, File 07 §20).
- **A second source for an invocation path** — the command palette, shortcut, voice, slash, menu, automation, and external-protocol rails are all projections over one `CapabilityDeclaration`; a "palette version" of a capability distinct from its "voice version," or two registries for the same operation, is the canonical two-registries-equals-bugs rejection (§4.4; `core.extension-planes`, File 01 §6.14).
- **A participation-level, autonomy-mode, interaction-shape, persona, or agent-mode field on a rail** — autonomy is permission tiers, leases, and the approval-posture preset plus user direction; voice/palette/handsfree are `UiMode`s; "plan/build/conversation mode" is a presentation lens and an approval posture, never a rail autonomy primitive (§17; `core.explicit-rejections`, File 01 §8; `world.surface-state`, File 18 §5.5).
- **A hardcoded spoken-intent enumeration** — voice intents are derived from the available-capability list, not a fixed enum (§9.2; `unit15-ux-distribution-files-glossary.md` D15.UX.4).
- **A rail that bypasses routing, policy, or the ledger** — every gesture asking for work passes routing (or the deterministic-precheck path with a route record), every invocation passes policy, every consequential resolution is recorded; fast-path and deterministic resolution are not bypasses (§4; `routing.explicit-rejections`, File 03 §14; `policy.explicit-rejections`, File 06 §17).
- **A rail that re-owns audio capture, the keymap-as-scattered-listeners, or the duplicate-detection mechanics** — voice capture/STT/wake-word/consent is File 19's, the keymap is the one context-stack resolver (not per-component listeners), and duplicate detection is File 13's; the rail composes them (§7.4, §9, §5.2).
- **A keybinding model without contexts or conflict resolution** — bindings resolve through the context stack with deterministic top-down first-match and explicit conflict handling and unbind; ad-hoc per-component key handling with registration-order conflicts is rejected (§7).
- **Conversation forced as the universal container** — conversation is an always-available control rail and an expand/collapse view, not the forced primary pane or the work model (§5.2; `intent.presentation`, File 02 §8; `worksurface.activation-shell`, File 25 §11).
- **A rail that silently abandons an in-flight run on mid-execution input, or auto-approves a steering or high-tier action** — mid-execution input resolves through the user-configurable queue-versus-interrupt setting, and steering/high-tier actions honor typed-confirmation and the permission floor (§5.2, §10.2; `run.explicit-rejections`, File 04 §28).
- **A trigger or external-protocol rail that auto-approves non-interactively what policy requires a human to decide** — a non-interactive context cannot silently lift an approval requirement (§11.2, §12.2; `policy.auto-decide-mode`, File 06 §8).
- **Time-based rail behavior as a correctness condition** — auto-continue countdowns and polling fallbacks are flagged conveniences, never correctness; rail availability and trigger observation are event-first (§4.5, §5.2, §11.2; `core.event-first-by-default`, File 01 §7.15).
- **A rail as a durable settings scope, or rail behavior hardcoded instead of settings** — rail variation is namespaced settings keys plus profile layers (§18; `settings.explicit-rejections`, File 15 §20).
- **A parallel rail registry or a rail that escapes source approval** — there is one `RailRegistry`; built-in, plugin, and user-defined rails register through the one proposal-first, source-approval-gated path (§14; `policy.source-approval-flow`, File 06 §9).
- **A whiteboard, canvas, or editor surface promoted into a rail kind** — those are work surfaces or artifact-editing surfaces. Sending their content to the model is a `CommitMessage` with a block/artifact reference or a Menu/Command `InvokeCapability`; the surface does not own a private rail or registry.

## 21. Consequences for Later Specs

Anchor: `controlrail.consequences-for-later-specs`

Later specs must follow these rules:

- The **work-surface and subsystem specs** (Coder, Web, Data Processor, Teacher, GUI Control, System Agent, and equivalent future specs) declare their control affordances as capabilities (`worksurface.actions-declaration`, File 25 §6.4) reachable through these rails; they declare which capabilities bind to which default shortcuts, slash commands, voice phrases, and menu entries, and they register surface-scoped keybinding contexts (§7.3) and custom commands (§8); they introduce no private rail, no per-surface invocation registry, and no rail autonomy field.
- The **Automation and Triggers** spec consumes the Trigger rail framing (§11): it owns trigger scheduling, eligibility, enablement, and non-interactive-execution safety, and produces `RouteRequest`s with the `automation`/`external_event` trigger kinds through the routing contract (`routing.trigger-kinds-routing`, File 03 §2.1); it introduces no parallel non-interactive invocation path.
- The **Workflows, Templates, and Reuse** spec exposes workflows as capabilities reachable through the rails (a workflow is invocable from the palette, a slash command, or a trigger) and pins rail and surface strategy at save time the way routing does; it introduces no parallel invocation surface.
- The **Extension and Plugin System** and **MCP and External Integrations** specs contribute plugin and external rails and externally-exposed capabilities through the `RailRegistry` (§14) and the External-Protocol rail (§12), gated by source approval and trust; a plugin rail participates in the same registry, policy layer, routing, and ledger as a built-in rail, without inheriting built-in trust or default enablement.
- The **UI Shell, Layout, Presentation, and Interaction Models** spec renders the command rail plus focus surface (§15), the command palette, the keybinding capture and editor, the voice waveform and confirmation, the menus and toolbars, and the steering affordances, over the data and resolution contracts this file fixes; presentation may vary freely, the resolution contract may not. The **UI Customization, Widgets, and Theming** spec renders the keybinding editor, the per-rail settings views, and widget-as-invocation-surface placements through the customization policy without bypassing this contract.
- The **Quality Control and Validation** spec validates rail conformance — that a rail resolves through §4, reuses the substrate, declares no autonomy field, and introduces no private path — through the registration validator and event and capability hooks, not a separate pipeline.
- The **Telemetry, Logging, and Observability** spec consumes the `controlrail` events (§19); the **Evaluation and Benchmarking** spec may evaluate rail-resolution correctness (gesture → expected `RailResolution`) over recorded events; the **Runtime Infrastructure and Lifecycle** spec orchestrates rail registration at startup around the registry lifecycle.

Specific integration contracts will be stated in those files when they are written.
