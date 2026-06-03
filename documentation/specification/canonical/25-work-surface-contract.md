# Work Surface Contract

## Status

Canonical. This file defines the `WorkSurface` primitive and the `SurfaceContract` every work surface declares. It realizes the surface-declaration contracts that Files 01–24 delegated to the Work Surface Contract spec, and introduces the net-new `WorkSurface`, `SurfaceContract`, and `SurfaceRegistry` primitives those files referenced without owning. It is horizontal and surface-neutral: it defines the shared shape every work surface fills, not any one surface's workflows. The per-surface specs fill this contract. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `WorkSurface` primitive — a primary user-facing work environment with substantial specialized workflows and substantial specialized views, declared once and composing the shared substrate (realizes `core.system-layers`, File 01 §2.3 and `core.current-major-area-classification`, File 01 §5)
- the precise disambiguation of "surface": a `WorkSurface` distinguished from a control rail (File 01 §2.1), an interaction shape (File 01 §2.2), a presentation surface (`intent.presentation`, File 02 §8), a substrate service (File 01 §2.4), the `ToolSurface` capability projection (File 07), and the live `SurfaceState` (File 18 §5)
- the `SurfaceContract` — the typed static declaration every work surface registers: its identity, the state it presents, the actions and control affordances it contributes, the views and view presets it offers, the context and execution policies it defaults to, and the sensors, confinement, and workspace relationship it declares
- how the static `SurfaceContract` relates to the live `SurfaceState` (`world.surface-state`, File 18 §5): this file owns the declaration, `world.surface-state` (File 18) holds the live values those declarations take at runtime
- how the `SurfaceContract`'s actions section is the surface's `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5), and how its context section names the surface's default `ContextPolicy` and `CompactionPolicy` (`context.context-policies`, File 13 §4) and default `ModelProfile` (`model.model-profile`, File 16 §4) — referenced, never re-owned
- the `PanelKind` catalogue and the `ViewPreset` — the surface's declared panels and startup presentation presets — and the rule that a view preset changes presentation only, never autonomy, model choice, context policy, execution policy, approval posture, or sandbox policy
- the `SurfaceRegistry` and surface lifecycle: one registry over built-in, plugin, and user-defined surfaces; registration, activation, enable/disable, and event-first discovery
- surface activation and the application shell: how routing selects the primary surface, the command-rail-plus-focus-surface shell relationship, and multi-surface composition
- the no-private-architecture invariant: the closed list of substrate primitives a work surface must reuse and may never privately reimplement
- the deletion of participation levels, autonomy modes, and interaction-shape fields from the surface declaration, and where that effect comes from instead
- the boundary between work surfaces and substrate-service management surfaces
- the surface world-model, perception, and observation integration; the surface persistence, locality, and portability contract; and the surface capability, event, and settings surface

This file does not define:

- the per-surface specifications themselves (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) — those specs declare their `SurfaceContract` to the shape this file defines and own their specialized capabilities, panels, runtimes, and workflows
- the `ToolSurface` zone model, the composition algorithm, capability borrowing, auto-shrink, or the `SubsystemSurfaceSpec` field set — File 07 owns those; this file references the `SubsystemSurfaceSpec` as the surface's actions declaration
- the live `SurfaceState`, `PanelState`, `Selection`, `UiMode`, the world-entity catalogue, the durability tiers, the availability evaluator, or snapshot resolution — File 18 owns those; this file declares the static shape whose live values File 18 holds
- the `ContextPolicy`/`CompactionPolicy` families, the assembly algorithm, token budgets, or model-request rendering — File 13 owns those; this file names which a surface defaults to
- the `ModelProfile`, model selection, or fallback — File 16 owns those; this file names the surface's default `ModelProfile` and role preferences
- the run lifecycle, the capability-call pipeline, the `surface_runtime` execution-entry mechanics, child-run isolation selection, cancellation, or budgets — File 04 owns those; this file declares the surface's default execution preset and budgets
- the `CapabilityDeclaration` field set, the registry, policy evaluation, approval flows, or leases — Files 05 and 06 own those; this file declares the surface's contributed capabilities and default approval-policy templates by reference
- routing, `RunIntent`, `primary_surface` selection, or reroute — File 03 owns those; this file defines what the `primary_surface` value resolves to and how a surface activates
- workspace identity, materialization, worktrees, or the disk mirror — File 24 owns those; this file declares the surface's workspace relationship without owning workspace identity
- block, artifact, evidence, version-graph, retrieval, memory, perception, sandbox, storage, sync, or security mechanics — the owning files define those; this file requires surfaces to reuse them and never privately reimplement them
- UI rendering — application-shell layout, panel chrome, concrete widget runtime, theming, saved-layout editor behavior, morphing animation, and accessibility presentation are owned by the UI specs; this file specifies only the data contracts they consume

## Source Resolution

Families reviewed: the domain/surface-architecture material (`agents/domain-architecture.md`, `domains/README.md`, `foundations/architecture.md`, `atlas3-core/TODO.md` domain catalogue and design filter); the per-surface `DomainSpec` instantiations (`unit08-coder.md`, `unit09-web.md`, `unit10-gui-control.md`, `unit11a-memory.md`, `unit11b-data-processor.md`, `unit11c-system-agent.md`, `unit11d-teacher.md`, and the `domains/coder`, `domains/web`, `domains/data-processor`, `domains/teacher`, `domains/system-agent`, `domains/gui-control` reference files); the state-awareness and panel-self-registration material (`cross-cutting/state-awareness.md`, `ui/14-1-application-shell.md`, `ui/14-6-to-14-8-...md`); the view-preset, morphing, and layout material (`ui/15-1-layout-customizability.md`, `ui/15-2-domain-based-workspace-morphing.md`, `ui/15-3-and-15-4-participation-levels-personas.md`, `ui/README.md`, `unit13-ui.md`); the action and prompt material (`cross-cutting/actions.md`, `agents/prompt-engineering.md`, `agents/agent-execution.md`, `unit04-routing-agents-prompt.md`); the extensibility material (`unit11-cross-tool-learning.md`, `kuzeys-ui-customization-and-widgets-addendum.md`, `cross-cutting/service-layer.md`, `cross-cutting/composition.md`); the strategic target-state review (`codex_recommendations.md` §1, §8, §10.1, §13.1, §14.10); and the cross-surface declaration patterns in existing ecosystems (`claude_tool.md`, `opencode-compressed.md`, `continue-compressed.md`, `warp-compressed.md`, `terax-ai-compressed.md`, `operator-use-compressed.md`).

Resolution rule: this file realizes and introduces, it does not re-own. The tool-surface contract stays File 07's, the live surface state stays File 18's, context policies stay File 13's, model profiles stay File 16's, execution stays File 04's, capabilities stay File 05's, policy stays File 06's, workspaces stay File 24's, and every substrate stays its owning file's. This file owns the `WorkSurface` primitive, the `SurfaceContract` declaration, the `SurfaceRegistry`, and the no-private-architecture invariant, and supplies each to the layer that consumes it.

Resolved tensions:

- **Naming — "domain" versus "surface."** The specbase calls these primitives `Domain` with a `DomainSpec` and a `DomainRegistry`; `codex_recommendations.md` §14.10 deliberately renames the same primitive `SurfaceSpec` with a `SurfaceRegistry`, observing that the "domain spec idea" must be formalized "without letting them become architecture snowflakes." Every prior canonical file (Files 01–24) uses "work surface" and "surface," never "domain," and `workspace.consequences-for-later-specs` (File 24 §24) names this file "the Work Surface Contract" spec. This file resolves toward `WorkSurface`/`SurfaceContract`/`SurfaceRegistry` and supersedes the `Domain`/`DomainSpec`/`DomainRegistry` vocabulary, exactly as `capability.chosen-model` (File 05 §1) superseded `Action` and `block.chosen-model` (File 08 §1) superseded "fragment." The word "domain" survives only as an informal synonym.
- **Participation levels and autonomy modes.** Early specbase drafts and several surviving domain overviews (`domains/memory/overview.md`, `domains/teacher/overview.md`, `domains/gui-control/...`) carry a per-surface `Drive`/`Supervise`/`Collaborate`/`Delegate` "participation level." The most-evolved sources delete it unanimously: `cross-cutting/state-awareness.md` ("that whole category of state is deleted from this spec; it does not exist at any layer"), `agents/domain-architecture.md` ("No Phases, No Participation Levels … removing these fields is deliberate"), and the `GLOSSARY` (which lists `Participation Level` as a deleted term). This file adopts the deletion (§13), consistent with `core.interaction-shapes` (File 01 §2.2), `core.explicit-rejections` (File 01 §8), `world.surface-state` (File 18 §5.5), `model.explicit-rejections` (File 16 §15), and `settings.explicit-rejections` (File 15 §20): the surface declaration carries no autonomy field; autonomy is capability permission tiers and leases plus user direction, and progressive disclosure is which panels and view preset are open.
- **The surface set — closed or open.** `core.current-major-area-classification` (File 01 §5) names six current work surfaces; `codex_recommendations.md` §1/§8 proposes additional surfaces (Documents, Media Studio, Workflow Studio, Observatory). This file resolves toward an open, extensible set (§3, §10): the six named verticals are the canonical baseline of the `SurfaceKind` enum, with `Custom { namespace, name }` for registered extensions per `core.closed-canonical` (File 01 §6.16). Surfaces are one of the canonical extension planes (`core.extension-planes`, File 01 §6.14), and "new surfaces must be addable without broad rewrites" (`core.local-extensibility`, File 01 §7.8). A closed six-surface set would gatekeep valid surfaces against `core.explicit-rejections` (File 01 §8)'s customization rule.
- **The shell — command-rail-plus-focus-surface.** The resolved shell relationship is a persistent command rail plus a primary focus surface, where conversation is an always-available control rail and presentation view, not the universal container. This is consistent with `core.product-thesis` (File 01 §1), `core.system-layers` (File 01 §2.1 and §2.3), and `intent.presentation` (File 02 §8). The UI specs own rendering; this file owns the relationship.

## 1. Chosen Model

Anchor: `worksurface.chosen-model`

ATLAS3 has one `WorkSurface` primitive and one `SurfaceRegistry` over it.

A `WorkSurface` is a primary user-facing work environment with substantial specialized workflows and substantial specialized views — the primitive `core.system-layers` (File 01 §2.3) names "work surface" and `core.current-major-area-classification` (File 01 §5) classifies (Coder, Web, Data Processor, Teacher, GUI Control, System Agent). A work surface owns its user-facing workflows and its specialized views; it does not own private architecture (`core.system-layers`, File 01 §2.3). It composes the shared substrate — blocks, capabilities, execution, world model, version graph, workspaces, context, settings, memory, routing — through the same contracts every other consumer uses.

Each work surface is declared by versioned `SurfaceContract` records (§4): typed static declarations of what state the surface presents, what actions it contributes, what views it offers, what customization it permits, and what context, execution, sensor, confinement, and workspace defaults it names. The `SurfaceRegistry` (§10) holds the registered surfaces; built-in, plugin, and user-defined surfaces register through the same path and are treated identically.

A `WorkSurface` is one kind of *subsystem*. The `Subsystem { subsystem_id }` capability source (`capability.capability-source`, File 05 §9.1) already spans "work surface or substrate service"; the work-surface flavor is the one that owns user-facing workflows and presents as a focus surface, and the substrate-service flavor (Memory, routing, context assembly, retrieval, knowledge, settings, evaluation, world model, perception, storage, capability registry, policy, versioning, and history) is always-on and cross-cutting and may expose management surfaces but is not a focus surface (§14). A surface's `surface_id` is its `subsystem_id`; the value `routing.run-intent` (File 03 §4.3)'s `primary_surface` resolves to, the source a `Subsystem`-sourced capability declares, and the key a surface's settings namespace and instruction-file qualifier are keyed by, are all this one identity.

`WorkSurface` supersedes earlier vocabulary that named the same primitive: domain, mode, vertical, sub-app, mini-app, workspace mode, and product surface. `SurfaceContract` supersedes "domain spec," `DomainSpec`, and `SurfaceSpec`. `SurfaceRegistry` supersedes `DomainRegistry`. Those names may persist as informal synonyms; the canonical noun is `WorkSurface`, its declaration is the `SurfaceContract`, and its registry is the `SurfaceRegistry`.

### 1.1 "Surface" Is Disambiguated

Anchor: `worksurface.surface-disambiguation`

The word "surface" is overloaded across the canon. This file fixes the `WorkSurface` meaning and distinguishes it from six adjacent concepts that are not work surfaces:

- a **control rail** (`core.system-layers`, File 01 §2.1) — conversation, the command palette, keyboard shortcuts, voice and handsfree input, and automation triggers, through which the user or system invokes capabilities. A control rail initiates or steers work; it is not the work model. Conversation is always available and may be the active surface, but it is a control rail and continuity surface (`intent.conversation`, File 02 §2.1, `core.current-major-area-classification` (File 01 §5.1)), not a work surface.
- an **interaction shape** (`core.interaction-shapes`, File 01 §2.2) — conversation-only, inline assist, sidecar workspace, paired workspace, orchestration desk — a presentation and involvement lens over the same runtime. It is a UX design lens, not a backend primitive, not a stored field, and not a surface declaration field (§13).
- a **presentation surface** (`intent.presentation`, File 02 §8) — a projection over the underlying work: a conversation-first transcript, a comparison board, a notebook view, an observability trace, an artifact diff. Presentation surfaces are an extensible set of views over work; a `WorkSurface` is a declared work environment, not a single view.
- a **substrate service** (`core.system-layers`, File 01 §2.4) — Memory, routing, context assembly, retrieval, knowledge, settings, evaluation, world model, perception, storage, capability registry, policy, versioning, and history. A substrate service may expose a management or inspector surface (§14) but is not a focus-presenting work surface.
- a **`ToolSurface`** (`surface.chosen-model`, File 07 §1) — the typed projection of the Capability Registry an invoker sees at a given moment. The `ToolSurface` is the capability-visibility projection a `WorkSurface` contributes its `SubsystemSurfaceSpec` to (§6); it is not the work environment.
- the live **`SurfaceState`** (`world.surface-state`, File 18 §5) — the runtime values of a work surface's declaration: the active surface, open panels, focused element, selection, available capabilities, and ui mode. `SurfaceState` holds the live values; the `SurfaceContract` declares the static shape (§5).

Where a prior file's `Surface` world entity (`world.world-entity`, File 18 §4.3) names "an active work surface or control rail the user can be in," that entity projects from a `WorkSurface` when the active surface is a work surface, and from a control rail when it is conversation or the palette.

### 1.2 Boundary

This file defines what a work surface is, how it declares itself, and how it shares the substrate. It does not define what any one surface does (the per-surface specs), how its tool surface composes (File 07), how its live state is held (File 18), how its context assembles (File 13), how its runtime executes (File 04), or how its views render (the UI specs).

## 2. Boundaries with Adjacent Layers

Anchor: `worksurface.boundaries`

### 2.1 With File 01 (Core Thesis)

This file realizes `core.system-layers` (File 01 §2.3)'s work-surface layer and `core.current-major-area-classification` (File 01 §5)'s surface classification. It honors `core.invariants` (File 01 §7): shared runtime (§7.1 — surfaces are presentations of one runtime), shared capability system (§7.2 — user and agent invoke the same capabilities), context interoperability (§7.4 — no private incompatible context model), flexible presentation (§7.5 — presentation varies without changing the runtime), service-layer ownership (§7.7 — business logic in the backend), local extensibility (§7.8 — surfaces addable without rewrites), system-wide customization (§7.9), and the extension-integrity and replaceable-implementation rules (§7.10). Surfaces are one of the `core.extension-planes` (File 01 §6.14) planes. `WorkSurface`, `SurfaceContract`, and `SurfaceRegistry` are new canonical noun-objects.

### 2.2 With File 02 (Conversation, Intent, Task)

Conversation is a control rail and continuity surface (`intent.conversation`, File 02 §2.1, `core.current-major-area-classification` (File 01 §5.1)), not a work surface; a conversation binds to a workspace (`workspace.conversation-binding`, File 24 §7) over which a work surface's views render. `intent.presentation` (File 02 §8) establishes that a presentation surface is a projection over work, that conversation-first and workspace-first are both first-class, and that presentation customization never changes the work model; §11 of this file consumes those rules for the shell and the work-surface-versus-presentation-surface boundary.

### 2.3 With File 03 (Routing and Dispatch)

`routing.run-intent` (File 03 §4.3) carries `primary_surface` and `supporting_surfaces`; `routing.surface-capability-selection` (File 03 §8) establishes that surfaces and subsystems are not hard fences and that routing selects one primary surface plus zero or more supporting surfaces. This file defines what the `primary_surface` value resolves to (a registered `WorkSurface`), and distinguishes run execution binding from user-facing presentation focus (§11). Routing selects the run's execution surface; File 18 owns live focus and presentation state.

### 2.4 With File 04 (Execution and Run Model)

`run.execution-entry` (File 04 §4) names `surface_runtime` — "enter a surface-specific runtime while still using shared execution semantics." This file declares the surface's default execution preset and budgets (§9) consumed by that entry; the run, ledger, policy, cancellation, and budget mechanics stay File 04's. `run.consequences-for-later-specs` (File 04 §29) requires "surface and subsystem specs … declare default tool surfaces, context policies, budgets, and child-run affordances, and … default cross-surface/subsystem capability access to search-and-borrow rather than autoload"; §6, §8, and §9 of this file discharge that.

### 2.5 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces)

A work surface is a `Subsystem`-class capability source (`capability.capability-source`, File 05 §9.1); the surface's contributed capabilities are declared per `capability.declaration` (File 05 §3) and registered through `capability.runtime-mutation` (File 05 §16.2)'s proposal-first path. The surface's actions section is its `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5), and its tool surface composes through `surface.visibility-composition-resolution-algorithm` (File 07 §9). The surface may declare default approval-policy templates and a per-surface approval posture (`policy.approval-policy-templates`, File 06 §12.4, `policy.settings-resolution-for-policy` (File 06 §16.1)); policy evaluation stays File 06's. This file references these contracts; it never re-owns the tool-surface composition or the policy evaluation.

### 2.6 With File 08 (Blocks) and File 09 (Artifacts)

A surface's input and output flow as `Block`s through the one block pool (`block.cross-surface-interoperability`, File 08 §12); a surface projects the pool through surface-specific filters and introduces no private block pool, kind catalogue, or edge catalogue (`block.consequences-for-later-specs`, File 08 §16). A surface declares the `ArtifactKind`s and `ObservationKind`s it primarily produces (`artifact.consequences-for-later-specs`, File 09 §22, §6 of this file) and projects the one entity pool through surface-specific lenses (`artifact.per-surface-projections`, File 09 §17.2).

### 2.7 With File 11 (Version Graph)

A surface's history, comparison, and rollback views are projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24); a surface introduces no parallel history, checkpoint, undo, fork, or versioning store, and "per-surface version trees" are an explicit rejection (`version.explicit-rejections`, File 11 §23). The coder history panel, the system-agent rollback view, and the comparison board are projections of the unified tree.

### 2.8 With File 13 (Context Assembly) and File 16 (Model Strategy)

`context.context-policies` (File 13 §4) defines the `ContextPolicy` families and `context.compaction` (File 13 §12) the `CompactionPolicy` families; `context.consequences-for-later-specs` (File 13 §22) requires "surface specs … declare their default context and compaction policies without creating private model-request assembly paths." §8 of this file declares which a surface defaults to, by reference. `model.model-profile` (File 16 §4) defines the `ModelProfile`; `model.consequences-for-later-specs` (File 16 §16) permits "surface and subsystem specs … declare default `ModelProfile`s and role preferences, but must not implement private model-selection logic." §8 names the surface's default `ModelProfile`.

### 2.9 With File 18 (World Model) and File 19 (Perception)

`world.surface-state` (File 18 §5.6) and `world.consequences-for-later-specs` (File 18 §17) previously delegated this static surface-declaration boundary — how a surface declares the panels, capabilities/control affordances, views, and context policies it can present — to the Work Surface Contract spec; this file realizes it. §5 of this file is that static declaration; `SurfaceState` holds the live values those declarations take at runtime, and File 18 holds those live values. A surface self-registers its panels and state to the world model (`world.observation-state-update`, File 18 §8.1) and is never screen-scraped to learn its own state (`perception.tiered-sensing`, File 19 §5.4). A surface declares which sensors it exposes and the privacy class of each (`perception.consequences-for-later-specs`, File 19 §19); perception holds the capture mechanics behind those declarations.

### 2.10 With File 15 (Settings) and File 24 (Workspaces)

A surface declares settings through the canonical settings system as namespaced keys under its `surface_settings_namespace` (`settings.consequences-for-later-specs`, File 15 §21); a surface is not a durable settings scope (`settings.scopes-profile-contexts-overlays`, File 15 §5.1), and per-surface variation is namespaced keys plus profile layers (`settings.profiles`, File 15 §7), not a new scope. A surface's views render over a workspace — "the workspace is the durable scoped context a surface's views render over" (`workspace.consequences-for-later-specs`, File 24 §24) — and the surface declares its workspace relationship (§9) without owning workspace identity, which stays `workspace.workspace` (File 24 §3)'s.

### 2.11 With Files 10, 12, 14, 17, 20, 21, 22, 23

A surface emits events through the one bus and ledger (`ledger.event-stream`, File 10 §5); a surface consumes retrieval through the shared substrate (`retrieval.consequences-for-later-specs`, File 12 §22) and memory through the Memory substrate (`memory.consequences-for-later-specs`, File 14 §22); a surface reaches model providers only through model strategy and the provider layer (`provider.consequences-for-later-specs`, File 17 §26); a surface persists durable state as substrate families through the storage contract and never a private store (`storage.consequences`, File 20 §18); a surface's durable state rides the syncable substrate and the `PortablePackage`, never a private export path (`portability.consequences`, File 21 §18); a surface consumes the secret vault, trust model, and egress governance and never a private secret store, trust authority, or egress path (`security.consequences-for-later-specs`, File 22 §19); a surface runs all confined execution through the one `Sandbox` contract and never a private sandbox (`sandbox.consequences-for-later-specs`, File 23 §21). §12 of this file consolidates these into the no-private-architecture invariant.

### 2.12 Boundary

This file is the work-surface-declaration layer. It owns the `WorkSurface` primitive, the `SurfaceContract` declaration, the `SurfaceRegistry`, the activation and shell relationship, and the no-private-architecture invariant. It owns no tool-surface composition, no live surface state, no context-assembly algorithm, no model selection, no run mechanics, no capability or policy evaluation, no workspace identity, and no UI rendering. It defines the contract; the per-surface specs fill it and the owning substrates realize it.

## 3. The `WorkSurface` Primitive

Anchor: `worksurface.work-surface`

### 3.1 Definition

A `WorkSurface` is a durable, registered, identified work environment that owns specialized user-facing workflows and specialized views for one kind of work, and that composes the shared substrate to do so. It is declared by a `SurfaceContract` (§4), registered in the `SurfaceRegistry` (§10), and presented as the focus surface of the application shell (§11) when it is the active surface.

### 3.2 Purpose

The system is one shared runtime with many presentations (`core.invariants`, File 01 §7.1). Coding, browsing and research, data work, teaching, computer-use, and system operations each benefit from a specialized environment — specialized panels, a specialized default tool surface, specialized default context and execution policies — without becoming a separate product. The `WorkSurface` primitive is the unit that carries that specialization while reusing everything underneath, so that adding a new surface is a declaration and a registration, not a new architecture (`core.local-extensibility`, File 01 §7.8).

### 3.3 Required

- A `WorkSurface` owns user-facing workflows and specialized views; it does not own private architecture (`core.system-layers`, File 01 §2.3). It composes the shared substrate through the contracts §12 enumerates and never privately reimplements any of them.
- A `WorkSurface` is a kind of subsystem: its `surface_id` is its `subsystem_id` (`capability.capability-source`, File 05 §9.1), and the capabilities it contributes are `Subsystem`-sourced (§6). A work surface is the subsystem flavor that owns user-facing workflows and a focus presentation; a substrate service is the other flavor (§14).
- The set of work surfaces is open. The current canonical baseline is Coder, Web, Data Processor, Teacher, GUI Control, and System Agent (`core.current-major-area-classification`, File 01 §5); new surfaces — built-in, plugin, or user-defined — register through the same path (§10) at flat cost (`core.extension-planes`, File 01 §6.14). The `SurfaceKind` enum is closed-canonical-plus-`Custom` per `core.closed-canonical` (File 01 §6.16).
- A `WorkSurface`'s identity, declaration, and contributed capabilities are durable and registered; its live state, active panels, and runtime handles are computed (§5, §16). The surface's existence does not require it to be currently active, materialized, or even available on the current platform (an unavailable surface remains registered and inspectable, §10).

### 3.4 What a `WorkSurface` Is Not

A `WorkSurface` is not a control rail, an interaction shape, a presentation surface, a substrate service, a `ToolSurface`, or a `SurfaceState` (§1.1). It is not a workspace (`workspace.workspace`, File 24 §3 — a workspace is the durable scoped context a surface's views render over; one workspace may host conversations across surfaces, and one surface may render over many workspaces over time). It is not a private runtime, a private store, or a private context model — it composes the shared ones.

### 3.5 Boundary

The `WorkSurface` defines the work-environment unit. The per-surface specs define each surface's specialized content. The substrate files own what the surface reuses. The UI specs own presentation choices over this contract. None of those layers may invent a work-surface primitive that bypasses this contract.

## 4. The `SurfaceContract`

Anchor: `worksurface.surface-contract`

### 4.1 Definition

A `SurfaceContract` is the typed, source-authored static declaration of one work surface. It is the single object the registry admits, the routing layer resolves `primary_surface` against, the shell reads to present the surface, and the conformance validator checks. It formalizes the specbase's "domain spec" and `codex_recommendations.md` §14.10's `SurfaceSpec` into one canonical contract, so a surface becomes pluggable without becoming an architecture snowflake.

### 4.2 Required Sections

Every `SurfaceContract` carries at minimum the following declaration sections. Each section's semantics are defined in the named later section; fields whose owning contract lives in another file are declared by reference, never duplicated.

- **Identity** (§4.3): `surface_id` (the `subsystem_id`), `surface_contract_version`, `surface_kind`, localized `display_name` and `description`, `icon_key`, `keywords`, and the `availability_predicate` that determines whether the surface can be activated or presented on the current world state.
- **State** (§5): the `PanelKind`s the surface can mount, the typed selection kinds it produces, and the static shape of the surface-state fields whose live values `world.surface-state` (File 18 §5) holds.
- **Actions** (§6): the surface's `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5) — its primary, borrowable, deferred, and forbidden capability ids, spawnable subagent types, settings namespace, and availability predicate — plus its registered control affordances, and the `ArtifactKind`s, `ObservationKind`s, and sensors it primarily produces or exposes.
- **Views** (§7): the `ViewPreset`s the surface offers, the default inspectors it declares, its `customization_policy`, and the cross-cutting affordances (teaching, observability) it declares.
- **Context and execution policy** (§8, §9): the surface's default `ContextPolicy`, `CompactionPolicy`, `ModelProfile` and role preferences, default execution preset (`surface_runtime` / default DAG preset), default budget, instruction-file qualifier, model-request instruction contribution, default sandbox profile, and workspace relationship.

A `SurfaceContract` lacking any required section is invalid and must be rejected at registration (§10.3), exactly as `capability.declaration` (File 05 §3) rejects an incomplete capability declaration. The declaration is source-authored and immutable for a registered version; contract updates create a new `surface_contract_version`, never mutate the prior version. Registry-state mutations (enable/disable, trust override, availability) live on the registered entry (§10), never on the declaration.

### 4.3 Identity Fields

- `surface_id` — stable, namespaced, lowercase identifier; equal to the surface's `subsystem_id` (`capability.capability-source`, File 05 §9.1); the value `routing.run-intent` (File 03 §4.3)'s `primary_surface` and `supporting_surfaces` resolve to, the key `world.surface-state` (File 18 §5.2)'s `active_surface_binding` carries, and the prefix the surface's settings namespace (`surface.<surface_id>.*`) and instruction-file qualifier (`ATLAS.<surface_id>.md`) use. Assigned once, never reused.
- `surface_contract_version` — immutable version identifier for this declaration. Runs, tool-surface compositions, automations, saved view presets, ledger records, and replay snapshots that depend on a contract record the version or snapshot they consumed. The registry resolves the latest valid version only for new composition.
- `surface_kind` — a value from the closed-canonical-plus-`Custom` `SurfaceKind` enum (§4.4).
- `display_name`, `description`, `short_description` — localized display text per the `capability.display-fields` (File 05 §3.2) localizable-descriptor discipline (literal default plus optional i18n key); user-facing strings are never hardcoded into surface logic.
- `icon_key` — optional icon identifier for shell presentation; the icon image is the UI spec's.
- `keywords` — optional list of typed keywords the router (`routing.surface-capability-selection`, File 03 §8) and the command palette consume for surface discovery and selection.
- `availability_predicate` — a declarative world predicate (`world.state-aware-capability-availability`, File 18 §9.2) evaluated by the world model's availability evaluator (`world.state-aware-capability-availability`, File 18 §9): when it fails, the surface is unavailable for activation or presentation (a Web surface requiring a registered browser backend, a GUI Control surface requiring accessibility-API access). An unavailable surface stays registered and inspectable. This predicate gates surface availability; the `SubsystemSurfaceSpec.availability_predicate` (§6.2) may further narrow capability-default projection for a specific tool-surface composition, but cannot make an unavailable surface active.

### 4.4 `SurfaceKind`

`SurfaceKind` is closed-canonical with the `Custom { namespace, name }` extension. The canonical baseline names the current work surfaces (`core.current-major-area-classification`, File 01 §5): `Coder`, `Web`, `DataProcessor`, `Teacher`, `GuiControl`, `SystemAgent`. A registered extension surface declares `Custom { namespace, name }` where `namespace` matches the capability sourcing taxonomy (`capability.capability-source`, File 05 §9.1). Adding a canonical kind is a canonical-spec change; runtime extension uses `Custom`. `SurfaceKind` is for cross-cutting classification and shell presentation; it never gates which capabilities a surface may declare or which substrate it may reuse.

### 4.5 Registry State Versus Declaration

The `SurfaceContract` version is the immutable declaration. Mutable runtime classifications live on the registered entry (§10): the surface's `registration_source` or `installation_source` (`BuiltinPackage`, `InstalledPlugin`, `UserDefinedPackage`, `ImportedPackage`, or registered extension source), its `trust_state` (`security.trust-model`, File 22 §9), its scoped `enabled` flag, its `availability_status`, and its `lifecycle_state`. This source field records where the surface declaration came from; it is distinct from capability ownership, where contributed capabilities still declare `source: Subsystem { subsystem_id }` (File 05 §9.1). Trust does not rewrite declared fields; a `Community`-trust surface from a plugin retains its declared capabilities, and policy resolves an escalated effective tier at invocation (`policy.effective-tier-resolution`, File 06 §4.2). This is the same declaration-versus-registry-state split `capability.registered-capability` (File 05 §10) fixes for capabilities.

### 4.6 Boundary

This section fixes the contract's sections and identity. The per-section semantics are §§5–9. The per-surface specs fill the contract for their surface. File 20 owns the contract's physical storage; File 18 owns the live state the State section's shape describes; File 07 owns the `SubsystemSurfaceSpec` the Actions section references.

## 5. State Declaration and the Static-Versus-Live Split

Anchor: `worksurface.state-declaration`

### 5.1 Definition

The state declaration is the surface's static description of the panels it can mount, the selection kinds it produces, and the shape of the surface-state fields it presents. It is the static counterpart of the live `SurfaceState` (`world.surface-state`, File 18 §5): this file declares the shape, File 18 holds the values.

### 5.2 Required

- A `SurfaceContract` declares the `PanelKind`s its surface can mount (§5.3), the `SelectionKind`s it can produce (drawn from the canonical `Selection`/`SelectionKind` set `world.surface-state` (File 18 §5.4) fixes, plus the surface's registered `Custom` selection kinds), and the typed state-field shape of each panel kind.
- The declaration is the *static shape*; the live values — which panels are open, which is primary, what is focused and selected, the current `UiMode`, and the available-capability list — are the live `SurfaceState` (`world.surface-state`, File 18 §5.2) the world model holds and projects. A surface's panels self-register their live state to the world model on mount and update it on focus, selection, and content change (`world.observation-state-update`, File 18 §8.1); the declaration tells the world model what kinds of panels and state to expect, and the runtime self-registration tells it the current values.
- A surface declares no interaction-shape, autonomy, or participation field on its state (§13); `UiMode` is interaction state, not an autonomy control (`world.surface-state`, File 18 §5.5).

### 5.3 `PanelKind`

A `PanelKind` is a semantic classifier of a panel a surface can mount, aligning with the `panel_type` field of `PanelState` (`world.surface-state`, File 18 §5.3). The canonical baseline panel kinds are cross-surface interoperability roles — `editor`, `terminal`, `browser`, `inspector`, `document`, `canvas`, `list`, `board`, `timeline`, `graph`, `diff`, `preview`, and equivalent control-rail/presentation panel roles — plus `Custom { namespace, name }` for surface-specific panel kinds registered through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2). The baseline is not a complete UI component taxonomy and does not force any panel to render in any surface.

A `PanelKind` declaration carries the kind id, the typed shape of the panel's compact state-field `data` summary (a file path, a url, a selected entry id — never the resource body, `world.surface-state` (File 18 §5.2)), the selection kinds the panel produces, the control affordances available in the panel, and structural semantics consumed by the world model and control rails: stable semantic role, accessible label/description key, interaction kinds, focus behavior, and parent/child relationship hints. Renderer families and visual presentation are UI-owned. Two surfaces may declare the same baseline panel kind; the shared editor, terminal, browser, inspector, and canvas roles are shared substrate projections (`block.cross-surface-interoperability`, File 08 §12), not per-surface reimplementations (§12).

### 5.4 Cross-Surface Panel Sharing

A panel kind a surface declares is a projection over shared substrate, not a private widget. A Coder editor panel and a Data Processor query panel both render `Block`s from the one pool (`block.cross-surface-interoperability`, File 08 §12) and self-register through the one state-awareness contract (`world.observation-state-update`, File 18 §8.1). A surface may borrow another surface's panel — a Coder surface opening a browser panel — without changing its primary surface (§11.4, `surface.subsystem-surface-spec` (File 07 §5.5)). The embedded panel carries its own `surface_binding` in `PanelState`; user-invoked controls inside that panel resolve against the panel binding for capability availability and ledger attribution, without changing the host surface or any active run's execution context unless File 03/File 04 reroute occurs. A surface that needs a genuinely new panel kind registers it; it never forks a parallel rendering of an existing kind.

### 5.5 Boundary

This section declares the static panel and state shape. File 18 owns the live `SurfaceState`, `PanelState`, `Selection`, and `UiMode` and the self-registration contract; UI specs own panel presentation. This file names the kinds; File 18 holds the values.

## 6. Actions Declaration

Anchor: `worksurface.actions-declaration`

### 6.1 Definition

The actions declaration is the surface's static description of the capabilities and control affordances it contributes, the cross-surface capabilities it expects to borrow, and the artifact, observation, and sensor kinds it primarily produces or exposes. Its tool-surface portion is the surface's `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5); this file references that contract rather than redefining it.

### 6.2 Required

- A `SurfaceContract`'s actions section declares the surface's `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5): `primary_capability_ids`, `borrowable_capability_ids`, `default_deferred_families`, `forbidden_capability_ids`, `spawnable_subagent_types`, `surface_settings_namespace`, and `availability_predicate`. The `SubsystemSurfaceSpec` is the surface's contribution to tool-surface composition; this file owns no zone, composition, or borrowing mechanics — those are File 07's. Its availability predicate governs capability-default projection for a tool-surface composition and is layered under the surface-level availability predicate (§4.3).
- The capabilities a surface contributes are declared per `capability.declaration` (File 05 §3) with `source: Subsystem { subsystem_id }` (`capability.capability-source`, File 05 §9.1) and registered through the proposal-first registration path (`capability.runtime-mutation`, File 05 §16.2). A surface introduces no parallel capability registry; capabilities enter the one registry (`capability.chosen-model`, File 05 §1).
- A surface's contributed capabilities are the same capabilities its control affordances, the command palette, voice, shortcuts, automation triggers, and external protocol resolve — one declaration, all invocation paths (`core.extension-planes`, File 01 §6.14). A surface declares no out-of-band action path.
- A surface declares the `ArtifactKind`s and `ObservationKind`s it primarily produces (`artifact.consequences-for-later-specs`, File 09 §22), and registers any `Custom` artifact, observation, block, or selection kinds through the canonical mechanism. A surface declares the sensors it exposes and the privacy class of each (`perception.consequences-for-later-specs`, File 19 §19).
- A surface may declare default approval-policy templates and a per-surface approval posture (`policy.approval-policy-templates`, File 06 §12.4, `policy.settings-resolution-for-policy` (File 06 §16.1)); the policy evaluation stays File 06's.

### 6.3 The Hint-Not-Fence Rule

A surface's `primary_capability_ids` are a hint about what is most relevant for the surface, not a fence around what the agent may invoke. The agent reaches any capability in the one registry through the canonical discovery and borrow capabilities (`tool.search`, `tool.borrow`, `mcp.search` per `surface.late-loading-runtime-discovery`, File 07 §7), subject to policy (File 06). A run in the Coder surface that needs `web.fetch` borrows it and remains in the Coder surface (`surface.subsystem-surface-spec`, File 07 §5.5); there is no hand-off ceremony and no per-surface capability sandbox. Cross-surface access defaults to search-and-borrow rather than autoload (`run.consequences-for-later-specs`, File 04 §29). The `forbidden_capability_ids` a surface declares exclude a capability from the surface's default zones but the agent may still attempt it through borrow, where it receives a typed denial (`surface.subsystem-surface-spec`, File 07 §5.1).

### 6.4 Control Affordances

A control affordance is a user-facing way to invoke one of the surface's capabilities — a panel control, menu item, command-palette entry, keyboard shortcut, voice phrase, slash command, or equivalent invocation lens. Control affordances are presentations of capabilities (`capability.capability`, File 05 §2.1), not a separate primitive; their availability is the available-capability list the world model computes (`world.state-aware-capability-availability`, File 18 §9) filtered by the active surface state. A surface declares which capabilities it surfaces as control affordances, the invocation lenses where they may appear (`surface.presentation-in-user-facing-surfaces`, File 07 §12), and the same structural semantics as panels where applicable: role, accessible label/description key, interaction kind, focus behavior, and source capability id. Rendering is UI-owned. A surface's "available actions" are the available-capability list for its scope (`world.surface-state`, File 18 §5.2), never a per-surface action store.

### 6.5 Boundary

This section declares the surface's actions by reference. File 07 owns the `SubsystemSurfaceSpec` field set, the tool-surface composition, and the borrow mechanics; File 05 owns the capability declarations; File 06 owns policy; File 09 and File 19 own the artifact and observation kinds. This file names what a surface contributes; those files own how it is contributed, composed, gated, and produced.

## 7. Views and View Presets

Anchor: `worksurface.views-presets`

### 7.1 Definition

A view declaration is the surface's static description of the presentation shapes it offers: the `ViewPreset`s the user can switch between, the default inspectors it declares, the customization policy it permits, and the cross-cutting affordances it declares. A `ViewPreset` is a named startup presentation shape; it is not an autonomy mode and does not silently change backend policy (§13).

### 7.2 `ViewPreset`

A `ViewPreset` is a named, registered presentation preset a surface offers. It declares the panel set, arrangement, focus shape, visible inspectors, and presentation-only startup state. It may reference an associated `SurfaceDefaultProfile` or settings/profile bundle, but applying the `ViewPreset` changes presentation only unless the user explicitly applies the associated settings/profile changes through the settings and policy paths. A surface ships built-in view presets; the user may save custom presets and override the default per scope (`settings.profiles`, File 15 §7).

A `ViewPreset` is a settings/profile/customization record or built-in declaration, not a backend autonomy control. It supersedes the specbase "participation level," "persona," and "personality preset" framing where those named a startup shape: a view preset names which presentation shape opens, never how autonomous the agent is (§13). Selecting a richer view preset is progressive disclosure — the user sees more state and asks different questions — not a mode change (`cross-cutting/state-awareness.md` realized; `world.surface-state` (File 18 §5.5)). Switching layouts mid-run never silently changes model selection, context policy, execution entry, budget, sandbox profile, approval posture, or instruction-source authority.

### 7.3 Surface Morphing Is a Projection

When a work surface becomes the active presentation surface, the application shell may project that surface's declared panels and active view preset (§11). Morphing is a UI projection driven by three inputs this file and adjacent files own: the surface's `SurfaceContract` (the declared panels and presets, this file), the live `SurfaceState` (the open panels and primary panel, `world.surface-state` File 18 §5), and, for runs, the routing decision (the `primary_surface`, `routing.surface-capability-selection` File 03 §8). The UI specs own any transition, layout, animation, or navigation behavior. Morphing changes presentation, not the work model (`intent.presentation`, File 02 §8.1, `intent.presentation` (File 02 §8.5)).

### 7.4 Customization Policy

A `SurfaceContract` declares a `customization_policy`, not concrete slot identifiers or geometry. The policy declares which kinds of customization the surface permits — panel rearrangement, widget placement, custom panel registration, per-panel extension regions, and equivalent future extension classes — the maximum extension density or safety bound where needed, and whether user, plugin, or AI placement is allowed per kind. The policy is intentionally capability-like and extensible: a technically capable user should be able to customize any behavior or presentation facet for which a safe capability, policy gate, reversible commit, and source-trust boundary can be defined.

Specific slot identifiers, region geometry, renderer constraints, widget runtime, and placement algorithms belong to the UI Customization, Widgets, and Theming spec that consumes this policy. `SurfaceContract` owns what kinds of customization are allowed; the UI customization layer owns where and how they render. AI-assisted surface, view-preset, widget, or layout mutation is a capability flow: inspect current declaration/state, propose a diff or preview, pass policy, commit reversibly where possible, and record provenance. Direct mutation of Atlas core UI code, a surface manifest, or runtime state outside that flow is invalid.

### 7.5 Default Inspectors and Cross-Cutting Affordances

A `SurfaceContract` declares default inspector affordances (for example context, schema, influence, execution, or registry inspection) as `PanelKind: inspector` projections over substrate state, not private stores. A surface declares cross-cutting affordances it offers so the shell, control rails, and other surfaces can consume them uniformly: teaching affordances and observability affordances. These affordances are declarations that UI and substrate layers may consume; they introduce no surface-private behavior and force no particular UI rendering.

### 7.6 Boundary

This section declares the surface's view presets and customization policy. UI Shell/Layout/Presentation specs own shell, panel, and morphing presentation; UI Customization/Widgets/Theming specs define concrete placement and widget mechanics; File 15 owns the settings and profile layers for saved presets and defaults. This file declares the shape and policy; settings resolve it.

## 8. Context and Model Policy Declaration

Anchor: `worksurface.context-model-declaration`

### 8.1 Definition

The context-and-model-policy declaration is the surface's static naming of the default `ContextPolicy`, `CompactionPolicy`, and `ModelProfile` its runs use, its instruction-file qualifier, and its model-request instruction contribution. The surface names which policies it defaults to; the policy mechanics stay with their owning files.

### 8.2 Required

- A `SurfaceContract` declares the surface's default `ContextPolicy` and default `CompactionPolicy` from the canonical families (`context.context-policies`, File 13 §4, `context.compaction` (File 13 §12)). The surface creates no private model-request assembly path (`context.consequences-for-later-specs`, File 13 §22); every model-bound invocation in the surface assembles through the one `ContextAssemblyService` (`context.chosen-model`, File 13 §1). Surface defaults may be overridden by settings/profile layers (`settings.scopes-profile-contexts-overlays`, File 15 §5.2); a `ViewPreset` does not override them unless the user explicitly applies an associated settings/profile bundle (§7.2).
- A `SurfaceContract` declares the surface's default `ModelProfile` and per-role model preferences (`model.model-profile`, File 16 §4, `model.consequences-for-later-specs` (File 16 §16)). The surface implements no private model-selection logic; selection stays the Model Strategy layer's (`model.model-strategy-layer`, File 16 §1).
- A `SurfaceContract` declares the surface's instruction-file qualifier — the `ATLAS.<surface_id>.md` variant (`workspace.instruction-files`, File 24 §9.2) — and its model-request instruction contribution: the surface's identity, environment, and guidance content that context assembly renders into the `InstructionSources` region (`context.instruction-sources-workspace-files`, File 13 §16) with the correct authority class (`context.authority-classes`, File 13 §2.3). The contribution carries source attribution, sensitivity, and budget behavior. Plugin or external surface descriptions are untrusted data unless policy promotes a specific source to instruction authority; they are never hidden model-request text and never grant the surface authority it could not declare.

### 8.3 The Surface Contribution Is Assembled, Not Owned

A surface's model-request instruction contribution is one attributed assembly part among many, not a private prompt the surface owns. Context assembly composes the surface's identity, the surface's declared tool surface (`context.tool-surface-coordination`, File 13 §17), the live world-state and surface-state runtime facts (`world.exposure-consumption`, File 18 §11.2), the active instruction sources, and the conversation history into one model request (`context.assembly-algorithm`, File 13 §6). The surface declares its contribution; assembly composes the request; the surface never builds the request itself.

### 8.4 Boundary

This section declares the surface's default policies by name. File 13 owns the `ContextPolicy`/`CompactionPolicy` families and the assembly; File 16 owns the `ModelProfile` and selection; File 15 owns the settings resolution; File 24 owns the instruction-file identity. This file names the defaults; those files realize them.

## 9. Surface Runtime, Execution, Confinement, and Workspace Declaration

Anchor: `worksurface.runtime-execution-declaration`

### 9.1 Definition

The runtime-and-execution declaration is the surface's static naming of its default execution preset, default budgets, default sandbox profile, and workspace relationship. The surface names its defaults; the run, sandbox, and workspace mechanics stay with their owning files.

### 9.2 Required

- A `SurfaceContract` declares the surface's default execution preset — the `surface_runtime` entry's default structure (`run.execution-entry`, File 04 §4 `surface_runtime` — "enter a surface-specific runtime while still using shared execution semantics") and the default execution-graph or DAG preset the surface's runs start from. A surface runtime uses the shared run lifecycle, ledger, event stream, capability policy, model strategy, context assembly, and cancellation (`run.execution-entry`, File 04 §4); it is a surface-specific *structure* over the shared semantics, never a private execution model.
- A `SurfaceContract` declares the surface's default run budgets (`run.budgets-limits`, File 04 §21, `run.settings` (File 04 §27)) and its spawnable subagent types (the `spawnable_subagent_types` of its `SubsystemSurfaceSpec`, §6, `run.child-runs-multi-agent-work` (File 04 §16)). Budgets are advisory ceilings overridable per scope, never hidden hard limits (`run.budgets-limits`, File 04 §21).
- A `SurfaceContract` declares the surface's default `SandboxProfile` (`sandbox.contract`, File 23 §3.1) for its confined execution — a code-execution profile, a browser profile, a graphical-control profile. The surface runs all confined execution through the one `Sandbox` contract and extends the base contract only with its capability surface; it redefines no lifecycle, filesystem or network enforcement, or kill semantics, and opens no private sandbox (`sandbox.consequences-for-later-specs`, File 23 §21). Graphical-control presentational isolation (virtual desktops, window cloaking) is a presentation facet, not a security tier (`sandbox.isolation-tiers`, File 23 §4.3).
- A `SurfaceContract` declares the surface's workspace relationship: that its views render over the bound workspace (`workspace.conversation-binding`, File 24 §7, `workspace.consequences-for-later-specs` (File 24 §24)) and any surface-specific materialization convention (a per-surface working subdirectory) the surface projects against the workspace mirror (`workspace.materialization`, File 24 §10). The surface owns no workspace identity, no disk-history store, and no parallel materialization path (`workspace.explicit-rejections`, File 24 §23); it materializes only through the workspace mirror and File 23's filesystem boundary.

### 9.3 Boundary

This section declares the surface's runtime, budget, sandbox, and workspace defaults by reference. File 04 owns the run, the `surface_runtime` entry, budgets, and child runs; File 23 owns the sandbox; File 24 owns the workspace and materialization. This file names the defaults; those files realize them.

## 10. The `SurfaceRegistry` and Surface Lifecycle

Anchor: `worksurface.registry`

### 10.1 Definition

The `SurfaceRegistry` is the one registry of registered work surfaces. It admits a `SurfaceContract`, pairs it with mutable registry state, and exposes lookup, enumeration, enable/disable, and the registration-mutation event stream. Built-in, plugin, and user-defined surfaces register through the same path and are treated identically.

### 10.2 Required

- There is one `SurfaceRegistry`. No subsystem, plugin, or surface introduces a parallel surface registry, a private surface store, or a per-surface registration side door. Surfaces register as subsystems through the proposal-first registration mechanism (`capability.runtime-mutation`, File 05 §16.2 — the `subsystems.register` path) and are gated by source approval (`policy.source-approval-flow`, File 06 §9) and trust establishment (`security.trust-model`, File 22 §9).
- The registry supports: list registered surfaces, get a surface by id and version, register a surface from a `SurfaceContract`, update a surface by registering a new contract version, unregister or tombstone a surface, enable or disable a surface at a scope, and refresh from the user-defined surface directory. Registration validates the contract (§10.3); a registered surface's mutable state (`registration_source`, trust, scoped enable, availability status, lifecycle state, §4.5) lives on the registered entry, not the declaration.
- Built-in surfaces (the canonical baseline) ship registered from `BuiltinPackage`. Plugin surfaces register when their plugin loads and unregister when it unloads (`capability.lifecycle`, File 05 §16). User-defined surfaces are discovered from a user-writable surface directory under the data root (the canonical default `<data-root>/surfaces/<surface_id>/`, placed by `storage.physical-layout-locality` (File 20 §8) and named here), each carrying a `SurfaceContract` manifest and its optional contributed skills, capabilities, panels, settings definitions, and instruction sources; discovery is event-first (a file-system watcher, `perception.triggers` File 19 §8) with a flagged polling fallback only where no change events exist (`core.event-first-by-default`, File 01 §7.15). The shipped surfaces live alongside user surfaces and load the same way; the registry distinguishes them by `registration_source` and `trust_state`.
- Registry mutations emit surface-relevant events (§18) so the shell, the command palette, the router's enabled-surface list, and the world model react without polling. A surface registered, unregistered, enabled, disabled, or whose availability changed updates the routing frame's enabled-surface input (`routing.routing-frame`, File 03 §3.1) and the tool-surface composition (`surface.surface-relevant-events`, File 07 §13) on next computation.

### 10.3 Registration Validation

Registration validates the `SurfaceContract`: every required section present (§4.2), the `surface_id` well-formed and not colliding with an active registered surface, the `surface_contract_version` unique for that surface, the `surface_kind` canonical or a registered `Custom`, required referenced capability ids resolvable in the registry or the same registration transaction, the declared `PanelKind`s and `SelectionKind`s canonical or registered, the surface-level `availability_predicate` and the `SubsystemSurfaceSpec.availability_predicate` parseable as pure `WorldPredicate`s or registered named checks (`world.state-aware-capability-availability`, File 18 §9.3), and the contract introducing no private substrate that §12 forbids.

Plugin and user-defined surfaces may register as an atomic package containing the `SurfaceContract`, contributed capabilities, custom kinds, panels, widgets, settings definitions, and instruction sources. Required references must resolve against the existing registry or the same package transaction. Optional references may enter an `Unavailable` diagnostic state. If required validation fails, no partial registration is committed. Material contract updates from plugin or user-defined sources pass through source approval when they change capabilities, panels, model-request contributions, sensors, sandbox profile, policy defaults, or other security-relevant declarations.

The validation is the structural realization of the cross-cutting conformance contract (§12): a surface that omits a required section or reaches for a private substrate cannot register.

### 10.4 Surface Lifecycle and Reconstruction

A surface's registration is durable and reconstructs on restart in the registry's startup phase (`capability.startup-registration`, File 05 §16.1, `storage.lifecycle-reconstruction` (File 20 §13)): built-in surfaces re-register, plugin surfaces re-register when their plugins load, user-defined surfaces re-load from the surface directory, and each surface's availability is re-evaluated against the world snapshot. A surface's live state — active panels, focus, selection, runtime handles — is not durable; it is computed and re-derived from self-registration on activation (§16).

Disabling a surface prevents new activation and new tool-surface composition for the disabled scope, but preserves history. Unregistering a surface leaves historical references resolvable through the recorded contract version or a tombstoned contract summary. Old runs, ledger records, automations, packages, and saved presets that consumed a contract version remain replayable from their recorded snapshots. Saved layouts, automations, or defaults referencing missing panels or capabilities become unavailable with typed diagnostics and recovery actions; they are never silently deleted or rewritten. Updating a surface creates a new contract version; existing consumers continue to reference the version they recorded unless a migration capability explicitly updates them.

### 10.5 Boundary

This section owns the surface registry and lifecycle. File 05 owns the proposal-first registration mechanism and the subsystem-registration path; File 06 owns source approval; File 22 owns trust establishment; File 20 owns the physical persistence and the surface-directory placement; File 35 (Extension and Plugin System) owns the plugin install lifecycle a plugin surface rides; File 42 orchestrates the startup registration. This file declares the registry contract; those files realize it.

## 11. Surface Activation, the Shell, and Multi-Surface Composition

Anchor: `worksurface.activation-shell`

### 11.1 Definition

Surface activation has two meanings that must stay separate: presentation activation, where the user focuses or opens a surface in the shell, and execution binding, where a run uses the `primary_surface` selected by routing or explicit reroute. The application shell is the relationship between the always-available control rails, the focus surface, and the supporting inspectors and consoles. Multi-surface composition is how supporting surfaces and borrowed capabilities compose without changing a run's bound primary surface.

### 11.2 Activation

- Routing selects the run's `primary_surface` (`routing.run-intent`, File 03 §4.3, `routing.surface-capability-selection` File 03 §8). That execution binding selects the run's active `SubsystemSurfaceSpec` for tool-surface composition (`surface.subsystem-surface-spec`, File 07 §5), plus the surface defaults consumed by context, model, execution, and sandbox layers. Changing that binding during execution requires File 03/File 04 reroute or explicit user override; opening or focusing a different surface in the UI does not silently change an existing run.
- User presentation activation opens or focuses a work surface for a conversation, workspace, or session. It updates live `SurfaceState` and shell presentation (File 18), and may influence future routing or user-invoked capability resolution, but it does not rewrite existing run binding. Invocation lenses such as command palette, shortcuts, voice, or UI controls may resolve against the currently focused surface for that invocation without changing the active run's execution context.
- Activation is scope-resolved. Surface state, focus, selection, and run binding are resolved per conversation, run, or session, because multiple surfaces and sessions may be active concurrently (`world.surface-state`, File 18 §5.1, `world.exposure-consumption` (File 18 §11.5)); there is no single global active surface. A consumer resolves the relevant surface for an explicit scope and purpose.
- A mid-execution primary-surface change — through a reroute when the run lacks the right surface (`routing.mid-execution-reroute`, File 03 §12) — changes the run's active `SubsystemSurfaceSpec` and emits `PrimarySurfaceChanged` (`surface.primary-surface-changes`, File 07 §5.4); the next model turn sees the recomposed surface and a typed notice. Run-scoped borrow grants survive a primary-surface change within the same run (`surface.primary-surface-changes`, File 07 §5.4).

### 11.3 The Application Shell

The application shell is the relationship: persistent control rails (conversation, command palette, voice, shortcuts — always available, `core.system-layers` File 01 §2.1), a focus surface, secondary inspectors, execution observability projections (`run.presentation` File 04 §25), and artifact-pool projections (`artifact.per-surface-projections` File 09 §17.2). Conversation is available as a control rail and presentation view; it is not the universal container. The same work may move between conversation-first and a work-surface focus over time without changing the work model (`intent.presentation`, File 02 §8). This file owns the shell relationship; UI specs own rendering, layout, and navigation.

### 11.4 Multi-Surface Composition

- A supporting surface's capabilities are promoted into the active surface's borrowable zone (`surface.routing-influence`, File 07 §6.1) without changing the run's primary surface. A run in one surface that borrows another surface's capability remains in the originating surface (§6.3, `surface.subsystem-surface-spec` File 07 §5.5); the ledger records both the originating surface and the borrowed-capability source.
- A surface's output composes with other surfaces' output through the one block pool (`block.cross-surface-composition`, File 08 §12.3) and the one entity pool (`artifact.cross-surface-interoperability`, File 09 §17.3): a research report composed in conversation may carry citation children from the Web surface, chart children from the Data Processor surface, and code children from the Coder surface, rendered correctly in any surface that supports the constituent kinds and as typed placeholders elsewhere. Cross-surface composition is a property of the shared pools, not a per-surface integration.
- A surface may embed another surface's panel as a borrowed view (a Coder surface embedding a browser panel) without a primary-surface change; the embedded panel self-registers its state to the one world model (§5.4). An invocation from an embedded panel carries the panel's `surface_binding` as invocation context for capability resolution and ledger attribution, but does not change the active run's execution context. The run's primary surface, context policy, model profile, budget, and sandbox profile remain the host surface's unless a formal reroute occurs through File 03/File 04. The panel binding affects which capabilities are available for that invocation; it does not affect how the run executes.

### 11.5 Boundary

This section owns the activation relationship, the shell relationship, and the composition rules. File 03 owns routing and run binding; File 07 owns tool-surface recomposition and borrowing; File 18 owns live focus and surface state; UI specs own shell presentation. This file defines the relationships; those files realize them.

## 12. The No-Private-Architecture Invariant

Anchor: `worksurface.no-private-architecture`

### 12.1 Definition

The no-private-architecture invariant is the load-bearing rule that a work surface owns user-facing workflows and specialized views but reuses every shared substrate primitive through its canonical contract, and may never privately reimplement, fork, or bypass any of them. It is the structural realization of the cross-cutting conformance contract every surface must satisfy.

### 12.2 Rule — What a Surface Must Reuse

A `WorkSurface` owns only its user-facing workflows, its specialized panels and views, its contributed capabilities, and its declared defaults. It must reuse, never privately reimplement, all of the following, through each one's canonical contract:

- **blocks** — input and output flow as `Block`s through the one block pool; no private block pool, kind catalogue, or edge catalogue (`block.consequences-for-later-specs`, File 08 §16). Results are blocks that compose across surfaces ("block-first I/O").
- **capabilities** — operations are `Capability` declarations in the one registry; no parallel capability registry, no `actions`-versus-`tools` split (`capability.consequences-for-later-specs`, File 05 §20).
- **capability policy** — approval flows through the one policy layer; no per-surface bespoke approval logic (`policy.consequences-for-later-specs`, File 06 §18).
- **tool surfaces** — capability visibility composes through the one `ToolSurface` algorithm; no parallel surface state model (`surface.consequences-for-later-specs`, File 07 §20).
- **execution** — runs use the shared run lifecycle, ledger, and cancellation; a `surface_runtime` is a structure over shared semantics, not a private execution model (`run.consequences-for-later-specs`, File 04 §29).
- **world model and state awareness** — the surface self-registers its panels and state to the one world model; no private state store, no screen-scraping of its own state (`world.consequences-for-later-specs`, File 18 §17).
- **version graph** — history, comparison, and rollback views are projections over the one version graph; no private history, checkpoint, or undo store (`version.consequences-for-later-specs`, File 11 §24).
- **context assembly** — model requests assemble through the one `ContextAssemblyService`; no private model-request assembly path (`context.consequences-for-later-specs`, File 13 §22).
- **settings** — configuration is namespaced settings keys plus profile layers; no per-surface config file as a live source of truth, no new durable scope (`settings.consequences-for-later-specs`, File 15 §21).
- **memory, retrieval, knowledge** — learned state, retrieval, and knowledge are the shared substrates; no private memory model, retrieval stack, or graph store (`memory.consequences-for-later-specs`, File 14 §22, `retrieval.consequences-for-later-specs` (File 12 §22)).
- **routing** — the surface is selected by the one router; it does not route itself (`routing.consequences-for-later-specs`, File 03 §15).
- **artifacts and evidence** — durable outputs are `Artifact` entities and `Evidence` blocks in the shared pools (`artifact.consequences-for-later-specs`, File 09 §22).
- **workspaces and materialization** — files materialize through the one workspace mirror and File 23's filesystem boundary; no private workspace identity or disk-history store (`workspace.consequences-for-later-specs`, File 24 §24).
- **storage** — durable state is substrate families and content-addressed blobs through the one storage contract; no private store (`storage.consequences`, File 20 §18).
- **sync and portability** — durable state rides the syncable substrate and the `PortablePackage`; lossy presentation-format exports pass through egress governance but use no private export path (`portability.consequences`, File 21 §18).
- **security** — credentials use the one vault, trust uses the one trust model, egress uses the one egress governance; no private secret store, trust authority, or egress path (`security.consequences-for-later-specs`, File 22 §19).
- **sandbox** — confined execution runs through the one `Sandbox` contract; no private sandbox (`sandbox.consequences-for-later-specs`, File 23 §21).
- **providers** — model calls reach providers only through model strategy and the provider layer (`provider.consequences-for-later-specs`, File 17 §26).
- **ledger, events, hooks** — facts flow through the one ledger and event bus; no side-channel store or notification (`ledger.execution-ledger`, File 10 §3.8).
- **service-layer ownership** — the surface's business logic lives in the backend service layer; command wrappers and the renderer are adapters, not ownership boundaries (`core.invariants`, File 01 §7.7).

### 12.3 Rule — Typed Errors, i18n, Cost Attribution

A surface returns typed cross-boundary failures (`core.typed-errors`, File 01 §6.9); its user-facing strings are i18n keys, never hardcoded, and its styles use semantic tokens (the i18n-and-theming discipline owned by UI specs); its capability invocations carry per-call attribution keyed by model and provider identity (`ledger.per-call-model-call-attribution`, File 10 §6), so a surface's cost is accounted through the one mechanism, never a private scalar.

### 12.4 Conformance Is Structural

The no-private-architecture invariant is enforced structurally, not by review: the registration validator (§10.3) rejects a `SurfaceContract` that omits a required section or declares a private substrate; the one registry, one pool, one policy layer, and one storage contract make a private path unreachable by construction; and §20 enumerates the private-architecture shapes as explicit rejections. A surface that satisfies the required `SurfaceContract` sections and reuses the substrate through the canonical contracts conforms by construction.

### 12.5 Boundary

This section owns the invariant and consolidates the per-substrate reuse rules each owning file already fixed. The substrate files own each contract; this file requires the surface to reuse it. The conformance validation is the registry's (§10.3); the structural enforcement is each substrate's single-contract design.

## 13. Participation, Interaction Shape, and the Deleted Autonomy Fields

Anchor: `worksurface.no-autonomy-field`

### 13.1 Definition

This section fixes that a `SurfaceContract`, a `ViewPreset`, and the live `SurfaceState` carry no participation-level, autonomy-mode, interaction-shape, or phase field, and names where the effect those fields once described comes from instead.

### 13.2 Rule

- A surface declaration carries no `participation_level`, `autonomy_mode`, `interaction_shape`, `persona`, or phase-machine field, in any form, at any layer. This is the unanimous, most-evolved position: it does not exist as a stored field, a settable enum, a model-request section, an engine that mutates it, or an event that changes it (`cross-cutting/state-awareness.md` realized; `agents/domain-architecture.md` realized; `world.surface-state` (File 18 §5.5); `core.interaction-shapes` (File 01 §2.2); `core.explicit-rejections` (File 01 §8)).
- **Autonomy** comes from capability permission tiers and leases (Files 05, 06) plus the user's direct commands, never from a per-surface autonomy dial. An action that should require approval requires it because its capability declares a tier and the policy layer evaluates it (`policy.effective-tier-resolution`, File 06 §4), not because a surface is in a "supervise" mode. The residual `Drive`/`Supervise`/`Collaborate`/`Delegate` framing in some surviving surface overviews is the retired pattern; its migration target is the permission-tier system.
- **Progressive disclosure** — the simple-to-power-user spectrum — comes from which panels, views, and affordances are available in the current presentation (§7), not from a per-surface mode. The agent adapts to what is asked and to the live `SurfaceState`, not to a pre-declared mode (`cross-cutting/state-awareness.md` realized).
- **Interaction shape** — conversation-only, inline assist, sidecar, paired, orchestration desk — is a presentation and involvement lens over the same runtime, varied freely by the UI and the user (`core.interaction-shapes`, File 01 §2.2, `intent.presentation` (File 02 §8.5)). It is not a backend primitive, not coupled to surface identity (`core.explicit-rejections`, File 01 §8), and not a `SurfaceContract` field.
- A `ViewPreset` (§7.2) is a startup layout shape, explicitly not an autonomy mode. There is no `ParticipationLevelChanged` event because there is no participation level to change (`world.state-change-events-reactivity`, File 18 §12).

### 13.3 Boundary

This section owns the deletion and its rationale. File 06 owns the permission tiers and leases that provide autonomy; File 18 owns the live `SurfaceState` and `UiMode` that provide progressive disclosure; UI specs own interaction-shape presentation. This file fixes that the surface declaration carries no autonomy field.

## 14. Substrate-Service Management Surfaces

Anchor: `worksurface.management-surfaces`

### 14.1 Definition

A substrate-service management surface is a user-facing presentation of a substrate service's data and capabilities — a memory browser, routing inspector, context-assembly inspector, settings inspector, knowledge-base browser, evaluation dashboard, capability-registry inspector, source manager, MCP manager, storage-accounting view, or world-model inspector. It is not a primary work surface; it is a management presentation of an always-on substrate service.

### 14.2 Rule

- Substrate services (Memory, routing, context assembly, retrieval, knowledge, settings, evaluation, world model, perception, storage, capability registry, policy, versioning, and history) are the subsystem flavor that is always available to every work surface and not shaped like a focus-presenting work surface (`core.system-layers`, File 01 §2.4; `core.current-major-area-classification`, File 01 §5.8). A substrate service may expose management, inspector, browser, proposal, dashboard, and graph presentations; those are management surfaces, not work surfaces.
- A management surface presents panels, views, and control affordances and, where it does, follows the same declaration discipline this file fixes — its panels are `PanelKind` projections that self-register to the one world model (§5), its actions are capabilities in the one registry (§6), its outputs are blocks (§12) — but it is classified as a substrate-service management presentation, not a `WorkSurface`. It does not register a `SurfaceContract`, does not enter the `SurfaceRegistry`, does not claim the focus-surface or workspace-first shape, does not register a `surface_kind` from the work-surface baseline, and a conversation never "binds to" a management surface the way it binds to a workspace. If a UI presentation spec (File 37) defines a separate presentation-surface declaration, management surfaces may declare through that UI-owned contract; this file creates no second management-surface registry.
- Memory browser/proposal review, routing inspection, context-assembly inspection, knowledge-base browsing, settings inspection, evaluation dashboards, and registry/source managers are all instances of the same rule: a substrate service may expose user-facing management presentations while remaining shared substrate. Opening, embedding, or invoking one of those presentations does not give the host run a new primary work surface or a private version of the service.

### 14.3 Boundary

This section fixes the management-surface-versus-work-surface boundary. Substrate-service specs and management lenses (including Memory, routing, context assembly, retrieval/knowledge, settings, evaluation, capability registry, world model, perception, storage, policy, versioning, and history) own their management presentations' content; UI specs own their rendering. This file classifies them and applies the shared substrate discipline where they present panels; it does not make them work surfaces.

## 15. World-Model, Perception, and Observation Integration

Anchor: `worksurface.world-perception-integration`

### 15.1 Rule

- A `WorkSurface` and its mounted panels are `WorldEntity`s in the one world model (`world.world-entity`, File 18 §4.3 — `Surface` and `Panel` entity kinds). A surface self-registers its panels, focus, selection, and state to the world model on mount, focus, selection, and content change, and unregisters on unmount (`world.observation-state-update`, File 18 §8.1); a surface that fails to register its state is a blind spot the agent cannot use (`world.chosen-model`, File 18 §1). A surface's own state is learned through self-registration, never through perception screen-scraping (`perception.tiered-sensing`, File 19 §5.4).
- A surface declares the sensors it exposes and the privacy class of each (`perception.consequences-for-later-specs`, File 19 §19); perception holds the live capture mechanics behind those declarations, and the surface's sensors are instantiations of the canonical sensor kinds (`perception.sensor`, File 19 §4.3), never a private capture pipeline (`perception.explicit-rejections`, File 19 §18). A surface that drives or observes the unowned environment (the Web surface's browser pages, the GUI Control surface's foreign applications, the Data Processor surface's external documents) does so through perception's sensors and the world model's entities, not a private observer.
- A surface declares the `ObservationKind`s it produces (`artifact.observation`, File 09 §13.2); process and sandbox snapshots a surface's runtime depends on are `Observation` blocks through the canonical path (`process.observation`, File 23 §14, `artifact.consequences-for-later-specs` (File 09 §22)). The active surface, focused element, panels, selection, available capabilities, and ui mode are the world snapshot routing, policy, tool-surface composition, and context assembly already consume (`world.exposure-consumption`, File 18 §11.3).
- A surface's available-capability and available-action list is the one the world model's availability evaluator computes for the surface's scope (`world.state-aware-capability-availability`, File 18 §9), filtered by the active surface state; a surface registers named availability checks (`world.state-aware-capability-availability`, File 18 §9.3) for surface-specific conditions and never maintains a private available-action store.

### 15.2 Boundary

This section fixes the surface's world-model and perception integration. File 18 owns the entities, the self-registration contract, the durability tiers, and the availability evaluator; File 19 owns the sensors and capture; File 09 owns the observation blocks; File 23 owns the process and sandbox snapshots. This file requires the surface to integrate through them.

## 16. Persistence, Locality, and Portability

Anchor: `worksurface.persistence-locality`

### 16.1 Rule

- A surface's durable state — its registered `SurfaceContract` versions, registered custom kinds, scoped enable state, scoped settings, and the blocks, artifacts, versions, and entities its work produces — persists as substrate families and content-addressed blobs through the one storage contract (`storage.durable-substrate`, File 20 §3, `storage.consequences` (File 20 §18)). Built-in view presets are contract declarations; user-saved layouts, widget placements, default preset choices, and customization records are settings/profile/customization records that reference `surface_id`, `surface_contract_version` where needed, `panel_kind`, and policy-owned placement identifiers. A surface introduces no private durable store. A surface's live state — active panels, focus, selection, runtime handles, the materialized presentation — is computed and rebuilt from self-registration and the version-graph projection, never a durable fact (§15, `world.persistence-contract` (File 18 §14.2)); its loss is a rebuild, never data loss (`core.projection`, File 01 §6.11).
- A surface's identity splits by locality the way a workspace's does (`workspace.locality`, File 24 §4, `storage.physical-layout-locality` (File 20 §8), `settings.locality-sync-export` (File 15 §18)): the surface's *logical* declaration and identity — its `surface_id`, contract versions, `surface_kind`, contributed capabilities, built-in view presets, and syncable settings — are portable and may sync when their owning specs classify them syncable (`portability.what-replicates`, File 21 §5.3); the surface's *device-local runtime* state — its active panels, live handles, materialized presentation, and device-bound facts — is device-local and rebuilds per device and never syncs. World facts a surface produces are device-local by default (`portability.what-replicates`, File 21 §5.3 — displays, windows, sandboxes, browser sessions, capture state never sync).
- A surface's durable state rides the syncable substrate and the `PortablePackage` for cross-device and cross-installation movement (`portability.export-bundle`, File 21 §10, `portability.consequences` (File 21 §18)); a surface may declare lossy presentation-format exports, but those pass through egress governance, audit recording, and sensitivity filtering (`security.egress-governance`, File 22 §11) and use no private export path. A surface persists no raw secret in any materialized, exported, or synced state (`secret.backend-boundary`, File 22 §4).
- Every hash a surface relies on is computed over a declared `CanonicalEncoding`, never physical storage bytes (`core.canonical-hash`, File 01 §7.14); this file defines no new canonical hash and inherits each from its owning file.

### 16.2 Boundary

This section declares which surface state is durable source-of-truth, which is device-local, and which is a rebuildable projection. File 20 owns the storage substrate, the partition, and the rebuild orchestration; File 21 owns the replication and the package; File 22 owns the secret and egress boundaries; File 15 owns the settings locality. This file declares the surface's persistence and locality classification; those files realize it.

## 17. The Surface Capability Surface

Anchor: `worksurface.capability-surface`

### 17.1 Rule

- The work-surface layer exposes canonical capabilities through the one Capability Registry (`capability.declaration`, File 05 §3), declared as built-ins in the `Builtin` source, tier-gated by policy (File 06), surfaced through tool-surface composition (File 07), and invoked through the shared pipeline (`run.call-pipeline`, File 04 §8.2). Surface-management capabilities declare touched resources and permission floors by effect:
  - reading registered surfaces, contract versions, and live state is `ReadOnly`
  - transient open, focus, arrange, and presentation activation operations are UI-state writes scoped to conversation/workspace/session; File 06 resolves the effective tier from touched resources and policy
  - saving or deleting user view presets, layouts, widget placements, and customization preferences is a settings/profile/customization write
  - enabling or disabling a surface is a settings/registry-state write
  - registering, updating, unregistering, or tombstoning a surface from plugin, imported, or user-defined sources is source-approval and trust governed, escalating by contributed capabilities, executable code, sensors, sandbox profile, secrets, model-request contribution, and policy defaults
  - refreshing the user-defined surface directory is read-only discovery unless it proposes registration changes
- Every surface-management capability is the single source for all its invocation paths — command palette, shortcut, agent tool, automation trigger, external protocol (`core.extension-planes`, File 01 §6.14); this file declares no out-of-band surface operation. Custom surface operations register through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2) and never bypass the policy layer.

### 17.2 Boundary

This section names the surface capability families and effect classes. File 05 owns the capability contract and registration; File 06 owns effective-tier resolution and approval; File 07 owns surfacing; File 04 owns execution. This file declares the capabilities as canonical built-ins without re-owning policy.

## 18. Events

Anchor: `worksurface.events`

### 18.1 Rule

- The work-surface layer emits typed events through the one event bus and ledger (`ledger.event-stream`, File 10 §5) with the canonical envelope (`ledger.event-envelope`, File 10 §5.2). Surface-relevant tool-surface events (`ToolSurfaceComposed`, `PrimarySurfaceChanged`, `SubsystemSurfaceSpecUpdated`, `SourceConnected`, `SourceDisconnected`) are owned by `surface.surface-relevant-events` (File 07 §13) and flow through that vocabulary; this file emits them when a surface's tool surface changes. Live surface-state events (`UiPanelRegistered`, `UiPanelUnregistered`, `UiPrimaryPanelChanged`, `UiSelectionChanged`, `UiModeChanged`, `UiAvailableCapabilitiesRecomputed`) are owned by `world.state-change-events-reactivity` (File 18 §12) and emitted by the world model from a surface's self-registration; this file consumes them.
- Surface-lifecycle facts this file owns register as `Custom { namespace: "surface", name, payload }` extensions (`ledger.custom-kind-registration`, File 10 §4.3): `SurfaceRegistered`, `SurfaceUnregistered`, `SurfaceTombstoned`, `SurfaceEnabledChanged`, `SurfaceAvailabilityChanged`, `SurfaceContractVersionRegistered`, `ViewPresetSaved`, `ViewPresetDeleted`, and `ViewPresetApplied` when applying the preset commits a durable setting or preference. Each declares its payload schema, cross-reference keys, default sensitivity, retention, and owner per File 10. This file reserves the `surface` namespace and declares these kinds. Run primary-surface changes use File 07 `PrimarySurfaceChanged`; live shell focus and panel changes use File 18 state events; this file does not duplicate them.
- Surface events are live coordination; a consequential surface fact (a registration, a primary-surface change consumed by a run) is committed to the durable record by the executor or registry, never inferred from event observation (`core.durable-history-transient-coordination`, File 01 §7.3). There is no `ParticipationLevelChanged` event (§13).

### 18.2 Boundary

This section reserves the `surface` namespace and declares registry/contract lifecycle events only. File 10 owns the envelope, delivery, sensitivity, and custom registration; File 07 owns tool-surface and run primary-surface events; File 18 owns live surface-state events. This file emits through that shared mechanism.

## 19. Settings

Anchor: `worksurface.settings`

### 19.1 Rule

- Work-surface behavior is configurable through the one settings system (`core.settings-system`, File 01 §6.8, File 15); this file names the dimensions, the settings system owns the cascade and storage. Surface settings are namespaced keys under the surface's `surface_settings_namespace` (`capability.settings-key-convention`, File 05 §18.2, the `surface.<surface_id>.*` convention) resolved through the standard cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2 — conversation → workspace → global → overlay → declared default). A surface is not a durable settings scope (`settings.scopes-profile-contexts-overlays`, File 15 §5.1); per-surface variation is namespaced keys and profile layers, never a new scope.
- The canonical surface settings dimensions include at least: which surfaces are enabled, per scope; the default surface for a new conversation or workspace, and whether the router may auto-switch the primary surface for future runs; the default and per-scope `ViewPreset` per surface; user-saved layouts, widget placements, and customization preferences permitted by the surface's `customization_policy`; the surface's default `ContextPolicy`, `CompactionPolicy`, and `ModelProfile` overrides; the surface's default budget overrides; the surface's default `SandboxProfile` overrides (composed with File 23's sandbox settings, not duplicated); the surface's instruction-file qualifier and enablement (composed with File 24's and File 13's instruction-file settings); the surface's approval-policy template and posture overrides (composed with File 06's policy settings); and the surface's sensor enablement and privacy class overrides (composed with File 19's perception settings). Profiles carry per-profile surface, view-preset, customization, and surface-default preferences (`settings.profiles`, File 15 §7).
- Each setting declares its locality (`settings.locality-sync-export`, File 15 §18) — saved view presets and the default-surface preference are syncable user preferences; device-bound surface runtime state is device-local — and its agent exposure (`core.settings-system`, File 01 §6.8, `policy.agent-exposure-policy-settings` (File 06 §16.4)), so the agent cannot read or change security-sensitive surface configuration without policy. No surface behavior with meaningful variation is a hardcoded constant (`core.typed-configuration-failure`, File 01 §7.6, `settings.settings-over-constants` (File 15 §13)).

### 19.2 Boundary

This section declares the surface settings dimensions and their layer. File 15 owns the settings object model, the cascade, locality, agent exposure, and profiles; Files 06, 13, 16, 19, 23, and 24 own the per-substrate settings the surface composes with. This file names the surface-relevant dimensions.

## 20. Explicit Rejections

Anchor: `worksurface.explicit-rejections`

The following are architecturally invalid for any later or per-surface spec:

- **A work surface that owns private architecture** — any surface that privately reimplements, forks, or bypasses the block pool, the capability registry, the policy layer, the tool-surface composition, the run model, the world model and self-registration, the version graph, the context-assembly path, the settings substrate, memory, retrieval, routing, the artifact and entity pools, the workspace mirror, the storage substrate, the sync and export path, the secret vault and trust model, the sandbox, the provider layer, or the ledger and event bus. A surface owns user-facing workflows and specialized views; it reuses everything underneath (§12; `core.system-layers`, File 01 §2.3).
- **A parallel surface registry, surface store, or surface state model** — there is one `SurfaceRegistry`, one block pool, one world model holding live surface state, and no per-surface durable state model diverging from the registry, the pools, and the version graph (§10; `surface.consequences-for-later-specs`, File 07 §20; `version.explicit-rejections`, File 11 §23).
- **A participation-level, autonomy-mode, interaction-shape, persona, or phase field on a surface, view preset, or surface state** — autonomy is permission tiers and leases plus user direction, progressive disclosure is which panels and view preset are open, and interaction shape is a presentation lens varied freely by the UI (§13; `core.interaction-shapes`, File 01 §2.2; `core.explicit-rejections` (File 01 §8); `world.surface-state` (File 18 §5.5)).
- **Coupling interaction shape to surface identity, or coupling the model choice to surface identity** — a surface presents at any interaction shape, and model selection is the Model Strategy layer's, not the surface's (`core.explicit-rejections`, File 01 §8; `model.consequences-for-later-specs` (File 16 §16)).
- **A closed, ungrowable surface set, or gatekeeping a valid surface** — the surface set is open; built-in, plugin, and user-defined surfaces register through the same path at flat cost, and the `SurfaceKind` enum is closed-canonical-plus-`Custom` (§3, §10; `core.extension-planes`, File 01 §6.14; `core.explicit-rejections` (File 01 §8)).
- **A surface that builds its own model request or its own prompt outside context assembly** — every model-bound invocation in a surface assembles through the one `ContextAssemblyService`; the surface declares an attributed prompt contribution, never a private model-request path (§8; `context.consequences-for-later-specs`, File 13 §22).
- **A surface as a durable settings scope, or a per-surface config file as a live source of truth** — surface variation is namespaced settings keys plus profile layers, never a new scope or a private config store (§19; `settings.explicit-rejections`, File 15 §20).
- **A surface that screen-scrapes its own rendered state, or maintains a private available-action store** — a surface self-registers its structured state to the one world model, and its available actions are the world model's computed available-capability list (§15; `world.explicit-rejections`, File 18 §16; `perception.explicit-rejections` (File 19 §18)).
- **A surface that opens a private sandbox, a private secret store, a private trust authority, or a private execution model** — confined execution runs through the one `Sandbox` contract, secrets and trust through the one security layer, and a `surface_runtime` is a structure over shared execution semantics (§9, §12; `sandbox.consequences-for-later-specs`, File 23 §21; `security.consequences-for-later-specs` (File 22 §19)).
- **Plugin, user, or AI UI injection outside declared customization policy** — customization is allowed broadly, but it must pass through declared `customization_policy`, capability policy, source trust, proposal-first mutation, and reversible or recoverable commit semantics (§7.4). Direct UI injection, direct Atlas core UI mutation, or untracked widget/panel placement is invalid.
- **Visual-only panels or controls that cannot be represented structurally** — panels and control affordances must expose semantic roles, labels, interaction kinds, and state relationships sufficient for the world model and control rails (§5.3, §6.4). Rendering may vary; structural invisibility is invalid.
- **A `ViewPreset` that silently changes backend policy** — presentation presets may reference settings/profile bundles, but applying a layout must not silently change model selection, context policy, execution entry, budget, sandbox profile, approval posture, or instruction-source authority (§7.2).
- **A presentation-focus change treated as execution reroute** — opening, focusing, or embedding a surface or panel may affect presentation and invocation context, but an active run's primary surface and execution context change only through File 03/File 04 reroute or explicit user override (§11).
- **Business logic in command wrappers, the renderer, or a per-surface bespoke service** — the surface's logic lives in the backend service layer; command handlers and the renderer are adapters (§12; `core.invariants`, File 01 §7.7).
- **Treating a substrate-service management surface as a primary work surface** — memory, routing, context, knowledge, settings, evaluation, registry, storage, world-model, and equivalent management surfaces are presentations of always-on substrate services, not focus-presenting work surfaces (§14; `core.current-major-area-classification`, File 01 §5.8).
- **Presentational isolation presented as a security tier** — a surface's window cloaking or virtual-desktop placement is presentation, not containment; untrusted code runs at the isolation tier its trust class requires (§9; `sandbox.isolation-tiers`, File 23 §4.3).
- **Conversation forced as the primary pane, or chat treated as the universal container** — conversation is an always-available control rail and a view the user can expand or collapse; the primary focus surface is whatever the work needs (§11; `core.product-thesis`, File 01 §1; `intent.presentation` (File 02 §8)).

## 21. Consequences for Later Specs

Anchor: `worksurface.consequences-for-later-specs`

Later specs must follow these rules:

- The **per-surface specs** each declare a complete `SurfaceContract` to the shape this file fixes (§4): identity and `surface_kind`, `PanelKind`s and selection kinds (§5), `SubsystemSurfaceSpec` and contributed capabilities and artifact, observation, and sensor kinds (§6), `ViewPreset`s, customization policy, and inspectors (§7), and default context, model, execution, budget, sandbox, and workspace policies (§8, §9). They own specialized workflows, panels, runtimes, and capabilities, reuse every substrate through its canonical contract (§12), introduce no private architecture, and declare no participation-level or autonomy field (§13). Their history, comparison, and rollback views are projections over the one version graph; their files materialize through the one workspace mirror; their confined execution runs through the one `Sandbox` contract.
- The **Control Rails** spec defines the control rails — conversation, command palette, voice, shortcuts, automation triggers — that invoke a surface's capabilities and compose with the focus surface in the shell (§11), consuming the `WorkSurface` and `SurfaceContract` this file defines without redefining them.
- The **Automation and Triggers** spec and the **Workflows, Templates, and Reuse** spec consume a surface's declared `surface_runtime`, default execution preset, spawnable subagents, and recorded `surface_contract_version` (§9, §10) and pin a surface and its policies at save time the way routing pins them (`routing.trigger-kinds-routing`, File 03 §2.1); they introduce no parallel surface activation.
- The **Extension and Plugin System** spec and the **MCP and External Integrations** spec contribute plugin and user-defined surfaces through the `SurfaceRegistry` and the proposal-first registration path (§10), gated by source approval and trust; a plugin surface participates in the one registry, policy layer, block pool, world model, and version substrate exactly as a built-in surface does.
- The **UI Shell, Layout, Presentation, and Interaction Models** spec consumes the `SurfaceContract`, live `SurfaceState`, and routing decision to define shell presentation and surface morphing; presentation may vary freely, the work model cannot. The **UI Customization, Widgets, and Theming** spec consumes `ViewPreset`, `customization_policy`, `PanelKind`, control-affordance semantics, and settings/profile records to define concrete customization mechanics without bypassing this contract.
- The **Quality Control and Validation** spec validates surface conformance — that a surface declares a complete `SurfaceContract`, reuses the substrate, self-registers its state, exposes structural semantics, and introduces no private store — through the registration validator and event and capability hooks, not a separate pipeline.
- The **Telemetry, Logging, and Observability** spec consumes the surface events and the per-call attribution this file and File 10 emit; the **Runtime Infrastructure and Lifecycle** spec orchestrates surface startup registration around the storage lifecycle File 20 owns; the **Evaluation and Benchmarking** spec verifies surface activation, cross-surface composition, the no-private-architecture invariant, and the morphing-as-projection round-trip over recorded snapshots, not live state.

Specific integration contracts will be stated in those files when they are written.
