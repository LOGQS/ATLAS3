# World Model and State Awareness

## Status

Canonical.

## Scope

This file defines:

- `WorldModel` as the always-available substrate service that holds the structured, live model of what the system and user are currently interacting with — the canonical primitive named in `core.world-model` (File 01 §6.7)
- `WorldEntity` as the typed unit of the world model, the closed canonical `WorldEntityKind` catalogue, the relation edges between entities, and the registered-extension mechanism
- `SurfaceState` — the surface/interaction projection of the world model (active surface, mounted presentation units, focus target, selection, available capabilities/control affordances, ui mode)
- environment facts, temporal grounding, and connection/liveness facts as world-model content
- the durability tier model (`Ephemeral`, `Durable`, `Observed`) that determines which world facts are live-only, which are recorded for snapshot resolution, and which are committed as `Observation` blocks
- how state is observed and made available: the self-registration contract, the state-update (projector) contract, the freshness/staleness model, reconciliation, and the boundary with the perception sensor pipeline
- the state-aware capability/control-affordance availability evaluator delegated by `capability.availability-predicate` (File 05 §15.2) and File 07 — the `availability_predicate` (`requires` / `blocked_by`) and `prerequisite_capabilities` evaluation that produces the available-capability list
- `WorldSnapshot` and `world_snapshot_id` resolution — the world model's own durable substrate and replay path that `version.snapshots` (File 11 §14) references
- how the world model is exposed to routing, execution, policy, tool-surface composition, context assembly, and the UI, and the multi-session scoping rules
- `WorldView` as the query-time, consumer-specific projection over a world snapshot
- the world-model state-change event vocabulary, the transient-versus-durable split, and the reactivity contract (available-capability recomputation, lease revalidation, tool-surface recomposition)
- the world-model capability surface, the persistence contract, the settings dimensions, the explicit rejections, and the consequences for later specs

This file does not define:

- the perception sensor pipeline — screen capture, accessibility-tree traversal, OCR, audio capture, browser DOM extraction, screenshot diffing, and other observation-capture mechanics — File 19 owns those; this file owns the state model those observations update and the contract by which they update it
- the `Observation`, `Citation`, `Artifact`, `Claim`, `Evidence`, or `Block` schema — Files 08 and 09 own those; this file consumes them
- the execution ledger row format, event envelope, or hook dispatch — File 10 owns those; this file specifies which world facts flow through as transient events and which commit as durable ledger entries
- the version-graph commit, materialized view, or snapshot-resolution machinery itself — File 11 owns those; this file specifies what `world_snapshot_id` addresses and how the world model resolves it
- the `CapabilityDeclaration` field set, the registry, or the runtime tier-resolution algorithm — File 05 owns the declaration of `availability_predicate` and `prerequisite_capabilities`, File 06 owns policy evaluation; this file owns the predicate evaluator and the available-capability list it produces
- the tool-surface composition algorithm — File 07 owns it; this file supplies the world snapshot it consumes
- routing, `RunIntent`, run lifecycle, task lifecycle, or memory mechanics — Files 02, 03, 04, and 14 own those; the world model references their state without re-owning it
- retrieval, indexing, or knowledge-base curation — File 12 owns those
- workspace identity, materialization, or worktree lifecycle — File 24 owns those; the world model references active workspaces as entities
- sandbox primitives, process isolation, credential storage, trust state, or per-surface runtimes (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) — File 23, File 22, and the per-surface specs own those; they declare which world entities and observations they produce
- storage schema, sync transport, or UI rendering — File 20, File 21, File 37, and File 38 own those

## Source Resolution

This file resolves state-awareness, world-state, environment-grounding, observation-to-state, and capability-availability material into one boundary: the live structured model of the current environment and the service that maintains and exposes it.

Resolved design:

- The world model is one structured substrate of typed entities, surface state, environment facts, temporal grounding, and connection/liveness facts. Surface/UI awareness is one projection into it, not the whole of it.
- The world model is structured-data-first. The agent navigates the environment by reading structure, not by interpreting screenshots; screenshot-driven self-perception is fallback, not foundation.
- World facts carry a durability tier. Live-only ephemeral facts flow as transient events; replay-relevant facts are durably recorded; deliberately captured facts become `Observation` blocks. A `world_snapshot_id` resolves over the durable substrate.
- State is observed event-first and updated through a deterministic projection. The perception sensor pipeline is a sibling concern; the world model consumes its structured output.
- The world model owns the availability evaluator: it turns declared capability predicates and the current world snapshot into the available-capability list that surfaces, the agent, and policy consume.
- The world model is read-mostly for consumers and update-only through declared producers; it never silently mutates the substrates it projects (runs, tasks, blocks, memory, settings).

Resolved tensions:

- "State awareness" (the specbase surface-state service) versus "world graph" (a richer entity model proposed in the strategic review): unified — the world model is the entity-plus-relation model; surface state is its interaction-facing projection. The canonical noun is `WorldModel` per `core.world-model` (File 01 §6.7); the entity-graph content is adopted.
- "Maintain a durable substrate with a replay path" (`version.closed-canonical-snapshot-catalogue`, File 11 §14.2) versus "no stored snapshot rows; reconstruct from the log" (the storage design) versus "transient `Ui*` events" (`ledger.app-event-catalogue`, File 10 §5.3): resolved by the durability tier model — the durable tier is the replay substrate, the ephemeral tier is transient-only, and snapshots are addressing identities resolved by walking the durable log, not stored copies.
- "Never use time-based conditions or polling" (project constraint) versus pervasive polling/TTL patterns in source systems: resolved by making event-driven observation canonical, current-time a grounding fact rather than a behavior driver, and time-based polling or staleness TTL an explicitly flagged, configurable fallback that is never a correctness condition.

## 1. Chosen Model

Anchor: `world.chosen-model`

ATLAS3 has one `WorldModel`.

The world model is the substrate service that holds a structured, live representation of what the system and user are currently interacting with: the active surface and its presentation units, the focus target and selection, the workspaces, files, processes, sessions, connections, and active work, the environment and temporal facts that ground the agent, and the set of currently available capabilities/control affordances. It is a substrate service per `core.substrate-services` (File 01 §2.4) — always available to every work surface and control rail, not shaped like a workspace-first surface.

The world model is structured-data-first. Consumers reason over typed structure; screenshots and rendered-text parsing are a fallback for surfaces where structured state is unavailable (`core.world-model`, File 01 §6.7). Any surface that does not report its state to the world model is a blind spot the agent cannot use; reporting state is a system-wide invariant, not an optional feature (`core.extension-planes` (File 01 §6.14), `core.local-extensibility` (File 01 §7.8)).

The world model is composed of four kinds of content:

- `WorldEntity` records (§4): the typed things in the current environment — files, editors, terminals, browser sessions, desktop windows, processes, sandboxes, workspaces, connections, in-scope artifacts and claims, active runs and tasks, and registered surfaces and presentation units — with relations between them.
- `SurfaceState` (§5): the interaction projection — active surface, open units, primary unit, focus target, selection, available capabilities/control affordances, ui mode — that File 03, File 06, and File 07 already consume as the "active world-model snapshot."
- Environment, temporal, and connection/liveness facts (§6): operating-system and platform facts, working directory, display geometry, locale, network connectivity, foreground application, permission state, current wall-clock time, and the liveness of providers, sidecars, integrations, and sessions.
- Projections of state owned by adjacent layers (§2): active runs and tasks (Files 02 and 04), active leases and approval posture (File 06), the active model route and provider rate-limit state (Files 16 and 17). The world model references these by identity; it does not re-own them.

The world model elaborates the canonical `World Model` primitive from `core.world-model` (File 01 §6.7) and the customization-aware substrate-service framing of `core.substrate-services` (File 01 §2.4) into a full entity, projection, observation, snapshot, and availability contract. It honors `core.product-thesis` (File 01 §1)'s promise that the system "maintains a live structured model of the current environment … so that capabilities can reason about the world, not just about conversation history."

`WorldModel` supersedes earlier vocabulary that named the same primitive: state awareness service, app state awareness, world graph, world entities store, desktop state, browser state snapshot, element cache, element tree, screen state model, ambient context, environment state model, and reactive app-state store. Those names may persist as informal or specialized synonyms; the canonical noun is `WorldModel`, its typed unit is `WorldEntity`, and its interaction projection is `SurfaceState`. The runtime component that maintains and exposes it is the State Awareness service.

## 2. Boundaries with Adjacent Layers

Anchor: `world.boundaries-with-adjacent-layers`

### 2.1 With File 01 (Core Thesis)

`core.world-model` (File 01 §6.7) declares the `World Model` primitive and its minimum content; §2.4 classifies world modeling as a substrate service; §1 describes the live environment model. This file specifies that primitive in full. The world model honors `core.non-destructive-by-default` (File 01 §7.13) (non-destructive by default — the world model is read-mostly and reconstructable, never the sole source of truth for durable facts), §8 (no unkeyed model-dependent scalars — any model-dependent fact the world model carries is keyed by model or tokenizer identity), and the §3 constraint forbidding time-based behavior (§11 below).

### 2.2 With File 02 (Conversation, Intent, Task) and File 04 (Execution and Run Model)

Active conversations, intent threads, tasks, and runs are owned by Files 02 and 04. The world model projects their live state — which runs are in flight, which task is active, the conversation activity state (`streaming` / `processing` / `awaiting_user` / `idle` per `intent.conversation-state` (File 02 §2.3)), the run `control` field (`run.minimum-durable-reconstruction`, File 04 §2.6) — as `WorldEntity` records (§4) keyed by their canonical identifiers. The world model does not define run or task lifecycle; it observes and references it. Run records carry world-state snapshot references (`run.minimum-durable-reconstruction` (File 04 §2.6), `run.lifecycle` (File 04 §6) step 3); §10 defines what those references resolve to. Run resumption revalidates world-state freshness (`run.pause-resume`, File 04 §17.2) against §8's staleness model.

### 2.3 With File 03 (Routing and Dispatch)

The routing frame includes the active world-model snapshot — active surface, focus target, mounted presentation units, selection, available capabilities/control affordances, current ui mode (`routing.routing-frame`, File 03 §3.1). The route record references the world snapshot in effect at routing time (`routing.route-record`, File 03 §3.5), and the routing inspector surfaces which snapshot was used (`routing.minimum-visible-information`, File 03 §10.2). This file defines that snapshot's content (§5, §6), its identity and resolution (§10), and the availability list the router reads (§9). The world model does not make routing decisions; it supplies the state routing reads.

### 2.4 With File 05 (Capability Contracts) and File 06 (Capability Policy)

`capability.availability-fields` (File 05 §3.9) and `capability.availability-predicate` (File 05 §15.2) declare `availability_predicate` (`requires` / `blocked_by`) and §15.3 declares `prerequisite_capabilities`, and explicitly delegate the predicate evaluator to this file. §9 owns the evaluator that resolves declared predicates against the current world snapshot and produces the available-capability list. `capability.discovery` (File 05 §15.1)'s availability-filtered enumeration, File 05's `available(world_state)` and `resolve_for_invocation(id, args, world_state)` registry operations, and File 05's `TierResolver::Dynamic` all consume the world snapshot this file defines; the `PrerequisiteUnsatisfied` typed error (`capability.prerequisite-capabilities`, File 05 §15.3) originates from §9's evaluation. File 06's approval router, effective-tier resolution, and grant-context capture (`policy.approval-router` (File 06 §3), `policy.effective-tier-resolution` (File 06 §4), `policy.auto-decide-mode` (File 06 §8), `policy.lease-primitive` (File 06 §11)) read the active world-model snapshot; world-state changes that affect lease validity — workspace switch, presentation-unit change, ui-mode transition (`policy.mid-execution-policy-re-evaluation` (File 06 §10), `policy.persistence` (File 06 §11.6)) — are signaled by §12's events.

### 2.5 With File 07 (Tool Surfaces and Capability Loading)

Tool-surface composition consumes the active world-model snapshot (`surface.chosen-model` (File 07 §1), `surface.visibility-composition-resolution-algorithm` (File 07 §9)) and re-evaluates capability availability against it (`surface.visibility-composition-resolution-algorithm`, File 07 §9 step where the availability predicate is tested; §8.2). A world-model state change that flips an availability predicate is one of File 07's reactive recomposition triggers (File 07's degradation and graceful-absence rules). Composition is deterministic given the world snapshot id and carries no clock-based effects (File 07's persistence and reconstruction rules); §9 and §10 of this file preserve that determinism. The world model supplies the snapshot and the available-capability list; File 07 decides zone placement and rendering.

### 2.6 With File 08 (Blocks) and File 09 (Artifacts, Claims, Evidence, Provenance)

The world model is not a block pool and stores no block content. It references blocks by `block_id`. The `attaches_to` edge (`block.canonical-edge-kinds`, File 08 §5.2) anchors a block to a workspace path, conversation node, task, or run, and is consumed by the world model to know what content is anchored where. `Observation` blocks (`block.kind-catalogue`, File 08 §3.1, `artifact.observation` (File 09 §13)) are the durable, content-addressed, staleness-fingerprinted captures the world model consumes to update and ground its `Observed`-tier facts (§7). Per File 09's consequence for this file, the world model treats in-scope artifacts, claims, and observations as world entities (§4), and the availability evaluator filters entity-level capabilities by the presence of the entity they operate on (§9.4).

### 2.7 With File 10 (Execution Ledger, Event Stream, and Hooks)

The world model emits and consumes events through the canonical bus. The transient surface-state events `ledger.app-event-catalogue` (File 10 §5.3) reserves — `UiUnitRegistered`, `UiUnitUnregistered`, `UiPrimaryUnitChanged`, `UiSelectionChanged`, `UiModeChanged`, `UiAvailableCapabilitiesRecomputed` — are this file's `Ephemeral`-tier events (§7, §12). The durable `EnvironmentSnapshotCaptured` ledger entry (`ledger.entry-kind-catalogue`, File 10 §4.1) is a `Durable`-tier world fact. The `world_snapshot_id` cross-reference (`ledger.cross-references`, File 10 §3.6) addresses the state §10 defines, and the replay queries that reconstruct "what the agent saw at time t" (`ledger.replay-semantics`, File 10 §11) resolve the world snapshot through §10. Additional world-model event kinds register as `Custom { namespace: world }` extensions per `ledger.custom-kind-registration` (File 10 §4.3). `Secret`-tier world facts never persist to the durable ledger (`ledger.sensitivity-aware-persistence-retention`, File 10 §10).

### 2.8 With File 11 (Version Graph, Commits, and Projections)

`version.closed-canonical-snapshot-catalogue` (File 11 §14.2) names `world_snapshot_id` as addressing "the world-model state at the named version," resolved "through the world-model service's replay path," and §14.4 specifies the generic resolution as walking the substrate's durable event log to the anchor. §10 of this file defines that durable substrate, its event log, and the resolution contract. The world model is a `Projection` per `version.version-graph-backed-projections` (File 11 §16) over the durable world-state log plus the block and ledger substrates: it declares its substrate, its event-driven rebuild trigger, its rebuildability, and its corruption-triggers-rebuild tolerance.

### 2.9 With File 12 (Retrieval) and File 14 (Memory)

The boundary with Memory is sharp and load-bearing. Memory (File 14) stores durable learned state about the user, workspaces, preferences, procedures, commitments, mastery, and context — it is retrospective and learned. The world model holds live current state — it is present-tense and observed. A `Context`-kind memory ("exam on June 10") is durable learned state; the current wall-clock time and the active workspace are world facts. The world model does not store learned facts and does not consolidate; it may reference an active memory-recall operation as an active-work entity but does not own memory. Knowledge entries (File 12) are curated reference content, not world facts. Observations the world model consumes are indexed through File 12's `observation:<scope_id>` namespace; the world model does not own retrieval.

### 2.10 With File 13 (Context Assembly and Compaction)

Context assembly reads world-state snapshots as one of its sources (`context.chosen-model` (File 13 §1), `context.assembly-algorithm` (File 13 §6) step 3) and renders them into the `RuntimeState` region (`context.semantic-regions`, File 13 §3) as `trusted_runtime_fact` assembly parts (`context.authority-classes`, File 13 §2.3). §11 of this file defines how the world model is exposed to assembly: a compact world-snapshot part, refreshed per model-bound iteration, carrying a `world_snapshot_id` for replay, compactable to a one-line summary under budget pressure. The world model never performs model-request assembly itself; it supplies the source.

### 2.11 With Perception (File 19), Workspaces (File 24), Security (File 22), Sandbox (File 23), and the per-surface specs

The Perception and Observation Pipelines spec owns the sensor/capture mechanics — how a screenshot, accessibility tree, audio stream, browser DOM, or file-system change is captured. This file owns the state model those captures update and the contract by which they update it (§8). The boundary: perception produces structured observations and signals; the world model is the live projection those observations maintain. The Workspaces and Materialization spec owns workspace identity and materialization; the world model references active workspaces as entities. Per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) and the System Agent spec declare which world entities and observations they produce and which named availability checks they register; they consume and contribute to the one world model and never introduce a private state model. The Security spec owns secret material and the credential vault; the world model carries sensitivity tags and references, never secret payloads. The Sandbox spec owns process/sandbox isolation; the world model references active sandboxes and processes as entities and liveness facts.

### 2.12 Boundary

This file is the live-state-model layer. It owns the world-entity model, the surface-state projection, the environment/temporal/liveness facts, the durability tiers, the observation-to-state and self-registration contracts, the availability evaluator, the snapshot identity and resolution, the exposure and event contracts, and the settings dimensions. It does not own sensor capture, block content, run/task/memory lifecycle, the capability registry, policy evaluation, surface composition, routing decisions, or storage layout. It feeds those layers; it does not replace them.

## 3. `WorldModel`

Anchor: `world.world-model`

### 3.1 Definition

`WorldModel` is the live, structured, scoped representation of the current operating environment. It answers, for any consumer at any moment: what surface is active, what is focused and selected, what presentation units and resources are open, what work is in flight, what facts hold about the environment, what time it is, what is connected, and what capabilities/control affordances are currently available.

The world model is a projection. Its authoritative content is derived from declared producers (surface self-registration, capability results, perception observations, subsystem updates, durable ledger facts) and from the substrates it references (the block pool, the run/task records, the lease set, the registries). It is rebuildable from those sources; a corrupted or stale world model is a rebuild, never a loss of durable data (`core.projection`, File 01 §6.11, `version.version-graph-backed-projections` (File 11 §16)).

### 3.2 What the World Model Is Not

The world model is not:

- a durable source of truth for any fact another layer owns — runs, tasks, blocks, memory, settings, leases, and capabilities are owned elsewhere; the world model references their state
- a memory — it holds current observed state, not learned durable knowledge (§2.9)
- a block pool or a transcript — it references blocks and conversations by identity
- a screenshot or a pixel buffer — it is structured data; visual capture is a fallback observation source, not the model
- a per-surface or per-subsystem private store — there is one world model; surfaces and subsystems project and contribute to it
- a behavior engine — it supplies state to routing, policy, execution, and surfaces; it does not decide what they do

### 3.3 Boundary

The world model defines what is true about the environment now and how that truth is observed, recorded, and exposed. It does not define how the environment is sensed (File 19), how the truth is acted upon (Files 04, 06, 07), or how it is stored on disk (File 20).

## 4. `WorldEntity`

Anchor: `world.world-entity`

### 4.1 Definition

A `WorldEntity` is the typed unit of the world model: one identifiable thing in the current environment, with attributes, a liveness/status, a scope, a source, and relations to other entities. The set of entities plus their relations is the structured graph the strategic review called the "world graph"; this file keeps the canonical noun `WorldModel` and names its members `WorldEntity`.

### 4.2 Required Fields

Every `WorldEntity` carries at minimum:

- `entity_id` — stable identifier within the world model for the lifetime of the entity; reused only when the same real-world thing reappears with the same canonical identity (a reopened file path, a reconnected session)
- `kind` — the `WorldEntityKind` (§4.3), fixed for the entity's lifetime
- `canonical_ref` — the typed reference to the underlying primitive when one exists: a `block_id`, `run_id`, `task_id`, `workspace_id`, `conversation_id`, file path, session id, process id, window handle, connection id, or registered surface id. Two entities with the same `canonical_ref` and `kind` are the same entity
- `attributes` — typed per-kind attribute map (a file entity carries path, content hash, mtime, dirty flag; a browser-session entity carries url, title, viewport, navigation availability; a process entity carries command, pid, status)
- `status` — typed liveness/lifecycle status appropriate to the kind (§6.3); the canonical floor is `Active` | `Idle` | `Busy` | `Degraded` | `Unavailable` | `Terminated`, with per-kind refinements declared in the kind's registration
- `validity` — the freshness/availability interpretation of the current entity state: `Current`, `PotentiallyStale`, `Stale`, `Unavailable`, `Terminated`, or `Unknown`; `status` describes lifecycle, `validity` describes whether consumers can rely on the current attributes
- `scope` — the broadest scope at which the entity is addressable, drawn from the canonical block scope set less `reusable_policy_rule` (`run` | `intent_thread` | `task` | `conversation` | `workspace` | `global`; `reusable_policy_rule` scopes policy and workflow templates, not world entities), aligning with `block.block-scope` (File 08 §11) and `policy.lease-primitive` (File 06 §11)
- `durability` — the durability tier of the entity's existence and attribute changes (§7): `Ephemeral`, `Durable`, or `Observed`
- `durability_floor` — the minimum durability tier this entity kind or attribute family may use (§7.3)
- `owner_subsystem` — the registered subsystem, surface, or producer that has write authority for the entity or attribute family
- `revision` — the current entity revision or equivalent world-log sequence position used by update preconditions
- `source` — typed reference to what reported the entity: a self-registered surface, a capability result, a perception observation, a subsystem, or a durable ledger fact
- `sensitivity` — `Public` | `Sensitive` | `Secret` (`block.sensitivity`, File 08 §9, `ledger.sensitivity-aware-persistence-retention` (File 10 §10)); `Secret` entities carry a safe description, never raw secret content
- `observed_at` — the time the current attribute values were last observed or confirmed; provenance metadata only, never the primary freshness or behavior trigger
- `freshness_evidence` — the evidence that supports `validity`: producer event, dependency revision, staleness fingerprint, scope transition, observation fingerprint, session lifecycle, explicit invalidation, or degraded fallback

Attribute values that are model-dependent (token counts of an in-view block, embedding identities) are keyed by model or tokenizer identifier and never stored as unkeyed scalars (`core.explicit-rejections`, File 01 §8). `source` is provenance; `owner_subsystem` is write authority. Attribute-level ownership may override entity-level ownership when one entity aggregates facts from multiple producers.

### 4.3 Closed Canonical `WorldEntityKind` Catalogue

Every entity declares its `kind`. The canonical closed catalogue:

**Surface and interaction kinds:**

- `Surface` — an active work surface or control rail the user can be in (conversation, a work surface, the discovery rail); the active one is named in `SurfaceState.active_surface`
- `PresentationUnit` — a mounted, registered presentation unit within a surface, carrying the `PresentationUnitState` of §5.3
- `Selection` — the current selection within a presentation unit (§5.4); at most one focused selection per surface scope, with secondary selections permitted
- `FocusTarget` — the currently focused element or control within the primary unit

**Resource kinds:**

- `Workspace` — an active or open workspace, referencing a `workspace_id`; attributes include root path, profile binding, and dirty/branch facts where applicable
- `Directory` — an in-scope directory or folder, distinct from a file and addressable by path or connector-specific reference
- `File` — an open, attached, or in-view file; attributes include path, content hash, mtime, dirty flag, and git status when in a repository
- `EditorDocument` — an open editing buffer over a file, carrying caret position, selections, and viewport range distinct from the on-disk file entity
- `Terminal` — an active terminal or shell session; attributes include working directory, the currently running command if any, environment summary, and `canStop`
- `Process` — a managed background process or job; attributes include command, identifier, and status
- `Sandbox` — an active sandbox or isolated environment, referencing the isolation primitive
- `BrowserSession` — an active browser automation or browsing session; attributes include session id, lifecycle, profile/context identity, and associated pages
- `BrowserPage` — a page, tab, or browsing target within a browser session; attributes include url, title, viewport, navigation availability, and visibility
- `DesktopWindow` — a desktop window with title, application reference, bounds, focus/minimized state, and display reference where available
- `DesktopApplication` — a running desktop application distinct from its windows; attributes include process relation, bundle/executable identity, and lifecycle
- `Connection` — an external connection or integration (a model provider, an MCP server, a sidecar, a synced device, a user-defined API) with liveness status
- `Device` — a local, connected, input, output, capture, or remote device that can affect execution or perception
- `Display` — a physical monitor or display target with geometry, resolution, scale factor, orientation, and hardware/session identity (§6)
- `VirtualDesktop` — a logical workspace grouping with assignment state and references to associated displays (§6)

**Work kinds (projections of state owned elsewhere):**

- `Run` — an in-flight or recently completed run (File 04), referencing `run_id`, with status, control, and progress facts
- `Task` — an active task (File 02), referencing `task_id`, with lifecycle status
- `PendingApproval` — an open approval request or lease decision awaiting the user (File 06)
- `Automation` — an active or scheduled automation or watch (File 33)

**Content-in-scope kinds:**

- `ArtifactInScope` — an artifact (File 09) currently materialized, open, or referenced in the active context
- `ClaimInScope` — a claim (File 09) currently asserted in the active line of work
- `SourceInScope` — a knowledge source, document, or retrieval result currently attached or open

**Extension:**

- `Custom { namespace, name }` — a subsystem-, surface-, plugin-, or extension-specific entity kind registered through the proposal-first registration mechanism (`capability.runtime-mutation`, File 05 §16.2). The `namespace` matches the capability sourcing taxonomy (`capability.capability-source`, File 05 §9.1). The registration declares the kind's required attributes, its status enum refinement, its default durability tier, its default sensitivity, the relation edges it participates in, and the named availability checks it backs.

The closed catalogue is canonical for cross-cutting reasoning; the `Custom` extension is canonical for specialization. Every world entity belongs to exactly one of these. Adding a canonical kind is a canonical-spec change; runtime extension uses `Custom`.

### 4.4 Relations

Entities relate through typed directed edges. The canonical relation set:

- `contained_in` — a presentation unit contained in a surface, a file in a workspace, a tab in a browser session
- `focused_in` — a selection or focus target within a presentation unit
- `produced_by` — a file or artifact produced by a run, a process spawned by a run
- `bound_to` — a surface bound to a subsystem, a terminal bound to a workspace, a sandbox bound to a run
- `displayed_on` — a desktop window, presentation unit, or virtual desktop displayed on a `Display`; the relation exists only where the medium has displays, and its absence is not a defect
- `observes` — an entity whose current attributes derive from a referenced `Observation` block (§7, `artifact.observation` (File 09 §13))
- `depends_on` — an entity whose liveness depends on another (a tab depends on its browser session; an integration's tools depend on its connection)
- `Custom { namespace, name }` — registered extension relations

Relations are read-time projections derived from entity attributes and substrate references; the world model does not maintain a separate durable edge store beyond what the durable tier records (§7). Closure under structural relations (`contained_in`, `bound_to`) is acyclic; reference relations may form cycles.

### 4.5 Boundary

The entity model defines what things the world model reasons about. It does not define how those things are rendered, stored, isolated, or executed. Per-surface and infrastructure specs declare their `Custom` kinds; this file declares the canonical baseline.

## 5. `SurfaceState`

Anchor: `world.surface-state`

### 5.1 Definition

`SurfaceState` is the interaction projection of the world model — the structured description of what surface the user and system are currently working in and what is focused, selected, and available there. It is the content `routing.routing-frame` (File 03 §3.1), File 06, and File 07 already consume as the "active world-model snapshot."

`SurfaceState` is scope-addressable: it is resolved per conversation, run, or session, because multiple concurrent surfaces and sessions may be active (`run.parallelism`, File 04 §15, File 07's rejection of single-active-stream assumptions). There is no single global surface state when multiple sessions are live; consumers resolve surface state for their scope.

`SurfaceState` is additionally resolved per `PresentationContext`, because one scope may be presented through more than one context (`ui.shell`, File 37 §4.5). A `PresentationContext` is `Interactive { client_session_id, context_ref, declared_profiles, declared_roles }` — an attached client surface in any medium, declaring at establishment (`runtime.transports`, File 42 §10.1) the frontend profiles it implements in `declared_profiles` (`ui.frontend-profile`, File 37 §1.3) and, in `declared_roles`, the closed `PresentationRole` subset this context serves (`ui.shell`, File 37 §4); one session may open several contexts serving different role sets, so the roles are declared per context and never per session — or `NonInteractive { client_kind, reason }`, no attending client (a headless deployment, boot before front-open, a disconnected client, an automation or programmatic invocation). Interactive means capable of user interaction in any modality; it never implies a graphical renderer. Only the `Interactive` arm carries focus-, unit-, selection-, preemption-, or binding-bearing values; under `NonInteractive`, the focus-bearing fields are absent and the typed descriptor explains why, while capability availability still computes from the invocation, run, and workspace context rather than becoming empty (`controlrail.external-protocol-rail`, File 26 §12.2). Attachedness and the roles served are declared by the client session, never inferred from the medium. A consumer always names its presentation context; a named context that is missing or whose generation has closed is a typed failure, never a silent fallback. The resolved state carries only the named context's values — cross-context aggregation is a separate explicit query, never ordinary `SurfaceState`, and the set of open presentation contexts with their presented scopes is a world fact readable on request. Multiple contexts presenting one scope are concurrent producers of distinct per-context values, not disagreeing producers of one value; §8.2's conflict rule does not apply between them. The `PresentationContextRef { context_id, generation }` in durable world facts is historical correlation only: it is recorded through the presentation-context extension cross-reference key this file registers (`ledger.cross-references`, File 10 §3.6), and it never reconstructs a live handle or resolves to a later context (`runtime.persistence-replay`, File 42 §21.1).

### 5.2 Required Fields

A resolved `SurfaceState` carries:

- `active_surface` — the surface or control rail currently primary for the scope (conversation, a work surface, a control rail); references a `Surface` entity. Null when no attending client presents a surface (a headless deployment, an automation, a disconnected session), in which case a typed headless-environment descriptor is supplied instead
- `active_surface_binding` — the owning subsystem or surface binding of the active surface when the surface is bound to one, else null
- `open_units` — the set of mounted `PresentationUnit` entities and their `PresentationUnitState` (§5.3); a context may present no unit, and an empty set is a valid `Interactive` state — absence of units is not `NonInteractive`
- `primary_unit` — the unit that currently holds primary focus, when the context presents one
- `focus_target` — the focused element or control within the primary unit, when one is reported
- `selection` — the current `Selection` (§5.4), when present
- `available_capabilities` — the list of currently available capability identifiers and control affordances, produced by §9's evaluator and projected for this scope
- `ui_mode` — the current `UiMode` (§5.5)

The focus-bearing fields — `active_surface`, `active_surface_binding`, `open_units`, `primary_unit`, `focus_target`, `selection`, `ui_mode` — resolve within the named `PresentationContext` (§5.1): the resolved state carries the named context's units and values only, and `available_capabilities` is computed against that explicitly named context's snapshot, because its availability predicates inspect those context-local values (§9.2).

`SurfaceState` is compact by design: it carries identifiers, short summaries, and pointers, not resource bodies. A selection carries a short summary and bounds, not the selected text; a presentation unit carries its file path or url, not the file or page content; available capabilities/control affordances are identifiers, not full declarations. The compactness budget is a settings dimension (§15) bounded so the projection fits comfortably in a model request (the source material's sub-100-KB guidance is a tested default, not a canonical constant); the budget is per resolved `(scope, PresentationContext)` — a resolution never returns the union of open presentation contexts, so context count does not scale the projection.

### 5.3 `PresentationUnitState`

A presentation unit is an independently addressable projection of substrate or work state whose kind declares its content semantics, its compact state shape, the selection kinds it yields, and its structural semantics. It assumes no pane, tab, region, or simultaneity: a medium presents a unit with whatever affordance it has, and a medium that can present only one unit at a time presents one (realized in the windowed-desktop profile as a pane, `ui.layout`, File 37 §5).

A `PresentationUnitState` carries at minimum: `unit_id`, `unit_kind` (the typed surface-declared classifier of the material presented and the selection it yields: one of the canonical baseline kinds the cross-surface interoperability role catalogue declares (`worksurface.state-declaration`, File 25 §5.3) — editor, terminal, browser, inspector, document, canvas and list among them — or a registered `Custom` kind), `title`, the bound `subsystem` or `surface_binding` when applicable, `has_focus`, a `prominence` value from the closed `PresentationProminence` set (`Absent` | `Minimal` | `Present` | `Exclusive` — the share of the context's finite attention the unit holds; it says nothing about geometry; adjacency, side placement and inline placement are the windowed-desktop profile's realization of a composition (`ui.layout`, File 37 §5)), a `has_unsaved_changes` flag where meaningful, a compact `data` summary of the unit's current content (a file path, a url, a selected entry id), and a `current_operation` summary when the unit hosts in-flight work. Units are registered and unregistered by the surfaces that own them (§8.1); the world model does not invent units.

Every field of a durable presentation record is medium-free, or optional with a declared meaning for its absence: a client with no such fact omits the field, and the omission carries that declared meaning rather than a substituted value. `unit_id` is the unit's `WorldEntity` identity (§4.2): stable for the unit's lifetime, reused only when the same unit reappears with the same canonical identity. Where order matters, unit-state facts order within their resolved `(scope, PresentationContext)` in the durable substrate's sequence order (§10.3); no ordering is defined across contexts. Unit state carries device-local locality metadata (§14.4); File 21 decides what crosses devices. `unit_kind` is closed-canonical-plus-`Custom { namespace, name }`; `PresentationProminence` is closed with no extension — a new prominence value is a canonical-spec change. Retention follows the fact's declared durability tier (§7): an `Ephemeral` unit fact is never individually recorded, and a `Durable` one is retained by the world model's durable substrate (§10.2) under §7.3's floors. The honest bound: a resolved unit state is exactly as current as its producer's last accepted update (§8.5), and at replay an `Ephemeral` unit fact resolves to the nearest durable checkpoint or to a typed "unobserved at anchor" value (§10.3), never to an exact reconstruction.

### 5.4 `Selection` and `SelectionKind`

A `Selection` carries the `unit_id` it belongs to, a `SelectionKind`, a short human-readable `summary`, and a compact typed `payload` (bounds, ranges, identifiers — not full content). The canonical closed `SelectionKind` set: `Text`, `CodeRange`, `BlockRange`, `File`, `Element`, `Region`, plus `Custom { namespace, name }`. A surface reports at most one focused selection per scope and may report secondary selections.

### 5.5 `UiMode`

`UiMode` is the current interaction mode of the active surface. The canonical closed set: `Normal`, `InputCapture { rail_id }` (a rail has captured the context's input and ordinary resolution is suspended until it completes or aborts), `Preemptive { request_kind }` (a request holds the context until it is answered or dismissed; preemption is presentation only and grants no authority), `Immersive { unit_id }` (one unit holds the whole context), `Handsfree`, `Headless`, plus `Custom { namespace, name }`. `UiMode` is live interaction state. It is not an interaction-shape field, backend autonomy control, or execution mode (`core.interaction-shapes` (File 01 §2.2), `core.explicit-rejections` (File 01 §8)): the agent's autonomy is governed by capability permission tiers and leases (Files 05, 06), not by `UiMode`. There is no interaction-shape field in the world model.

### 5.6 Boundary

`SurfaceState` defines the live interaction projection. The Work Surface Contract spec (File 25) defines how a surface statically declares the presentation units, capabilities/control affordances, views, and context policies it can present; `SurfaceState` holds the live values those declarations take at runtime. The UI specs render `SurfaceState`; this file defines its content.

## 6. Environment, Temporal, and Connection Facts

Anchor: `world.environment-temporal-connection-facts`

### 6.1 Environment Facts

The world model carries the operating-environment facts that ground capabilities and the agent. The canonical baseline: operating system and platform, shell, current working directory, the active workspace root, display geometry (count, resolution, scale factor, orientation, virtual-desktop assignment), locale and timezone, network connectivity posture, sandbox mode and writable roots, the foreground application and window when the system observes desktop state, and the relevant permission states (for example, whether screen or accessibility observation is permitted). These are `WorldEntity` attributes (on `Display`, `Workspace`, `Sandbox`, and platform-scoped facts) or scope-level facts on the global and workspace scopes.

Environment facts are observed, not assumed. A display geometry change, a working-directory change, or a permission grant updates the corresponding fact through §8.

### 6.2 Temporal Grounding

The world model exposes the current wall-clock time and timezone as a world fact so the agent is temporally grounded ("today is …", "the deadline is in two days"). This is a deliberate, flagged use of time: current time is a *fact the agent reads*, not a *condition that drives system behavior*. The project constraint forbidding time-based behavior (`core.event-first-by-default`, File 01 §7.15) applies to control flow, scheduling, and correctness — it does not forbid exposing the clock as grounding. The world model and its consumers must not derive correctness or scheduling from elapsed time; that remains the scope of explicit triggers and events (§8.6, §11 of File 14, File 33).

### 6.3 Connection and Liveness Facts

The world model carries the liveness of the connections work depends on, as `Connection` entity status: model providers (online, degraded, rate-limited, unavailable — projected from File 17's `ProviderHealth` and `RateLimitState`, not re-derived here), MCP servers and integrations (connected, connecting, failed, disconnected), sidecars and local services (healthy, unavailable), synced devices, and active sessions (alive, stale, terminated). Liveness is observed event-first where the connection emits lifecycle signals, and otherwise through the freshness model (§8.5). Liveness gates capability availability (§9): a capability whose connection is `Unavailable` is not in the available set.

### 6.4 Boundary

Environment, temporal, and connection facts are world-model content. The mechanisms that capture them (platform queries, accessibility event streams, network probes, provider health tracking) belong to File 19, the per-surface specs, and File 17. This file abstracts over those mechanisms; it names no platform APIs.

## 7. Durability Tiers

Anchor: `world.durability-tiers`

### 7.1 Definition

Every world fact — entity existence, attribute value, surface-state field, environment fact — carries a durability tier that determines how it is recorded and how it participates in snapshots and replay. The closed canonical tiers:

- `Ephemeral` — live-only. The fact exists in the live world model and is broadcast as a transient event (§12, `ledger.app-event-catalogue` (File 10 §5.3)), but it is not individually recorded to a durable substrate. Cursor position, transient hover, fine-grained focus changes, and high-frequency attribute updates are `Ephemeral`. At replay, an `Ephemeral` fact resolves to the nearest durable checkpoint or to a typed "unobserved at anchor" value.
- `Durable` — recorded to the world model's own durable substrate (§10) as a world-state-change fact (a ledger entry under the `world` namespace, or one of File 10's canonical durable entries such as `EnvironmentSnapshotCaptured`). Workspace open/close, active-surface change, subsystem/surface-binding change, session lifecycle, connection lifecycle, and environment-snapshot captures are `Durable`. A `world_snapshot_id` resolves over the `Durable` log.
- `Observed` — captured as an `Observation` block (`block.kind-catalogue`, File 08 §3.1, `artifact.observation` (File 09 §13)), content-addressed and carrying a staleness fingerprint. A file-content snapshot, an accessibility-tree capture, a browser DOM extract, or a screenshot reference that the system commits for replay and precondition revalidation is `Observed`. `Observed` facts are the heavyweight, evidentiary tier; the world model references the `Observation` block and links the relevant entity by the `observes` relation.

### 7.2 Why Three Tiers

A single tier cannot satisfy the three constraints simultaneously: `version.snapshots` (File 11 §14) requires a durable substrate the world model resolves snapshots over; `ledger.app-event-catalogue` (File 10 §5.3) reserves high-frequency surface-state changes as transient events that must not flood the durable ledger; and the storage design reconstructs past state from logs and diffs rather than storing snapshot copies. The tier model satisfies all three: `Ephemeral` keeps high-frequency churn off the durable substrate, `Durable` is the replay log, and `Observed` is the deliberate evidentiary capture. The tier of each fact kind is a producer declaration with a settings override (§15); the defaults are tuned so that replay reconstructs the consequential world state without recording every transient flicker.

### 7.3 Tier Assignment Rules and Floors

- A fact whose change is consequential for replay, audit, policy, or continuity is `Durable` or `Observed`, never `Ephemeral`. Presentation continuity satisfies that rule through the normalized restore and presentation-step records its owning contracts define (`ui.shell`, File 37 §4) and (`ui.events`, File 37 §21), not by promoting the live `SurfaceState` values they summarize.
- A fact captured deliberately as evidence or as a mutation precondition is `Observed` (it becomes an `Observation` block).
- A fact that changes faster than it is consumed and whose individual values are not replay-relevant is `Ephemeral`.
- `Secret` facts are never `Durable` in raw form and never `Observed` in raw form; the durable or observed record carries a safe description (`ledger.sensitivity-aware-persistence-retention`, File 10 §10, `artifact.observation` (File 09 §13) sensitivity rules).
- Each entity kind, relation kind, producer declaration, and availability-check family declares a `durability_floor`. Settings may make facts more durable, or less durable down to that floor, but may not lower audit-, replay-, policy-, route-, lease-, version-, capability-availability-, or side-effect-relevant facts below their floor. Unsafe-mode exceptions, if a later policy spec permits them at all, require typed confirmation and must be audit-visible.

### 7.4 Boundary

The tier model defines what is recorded and how it resolves. The physical substrate (which table, which log) is File 20's concern; the observation-block mechanics are File 09's; the transient-event delivery is File 10's. This file defines the tier semantics.

## 8. Observation and State Update

Anchor: `world.observation-state-update`

### 8.1 Self-Registration

Every interactive surface, presentation unit, and subsystem that holds live state is responsible for reporting that state to the world model. A surface registers a unit when it is activated, updates focus and selection on change, updates content summaries on content change, and unregisters it when it is deactivated. A subsystem registers the entities it owns (a terminal subsystem registers its sessions; a browser subsystem registers its sessions and pages) and updates their status. There is no central observer that scrapes a rendered view; each producer self-registers. This is the cheap-to-add extensibility invariant (`core.extension-planes` (File 01 §6.14), `core.local-extensibility` (File 01 §7.8)): a new surface or subsystem declares its world-model contribution as part of registering, not by editing the world model.

Self-registration declares the entity kinds, canonical-reference patterns, relation kinds, attribute paths, durability floors, sensitivity defaults, freshness evidence, and normalization policy the producer may create or update. It is a producer responsibility enforced by the update pipeline: a surface that fails to register its state is a blind spot, while a producer that writes outside its declaration is rejected.

### 8.2 The State-Update Contract

The world model is updated by applying a typed signal to its current state, producing the next state — a deterministic projection `(world_model, signal) -> world_model`. Signals are: a self-registration or update from a surface or subsystem, a capability result that changed observable state, a perception observation (an `Observed`-tier capture), a durable world-state-change fact, a normalized context-change signal, or a connection/liveness lifecycle signal. The projection is deterministic: the same ordered signals applied to the same prior state produce the same world model. This determinism is what makes snapshot resolution (§10) and replay (`ledger.replay-semantics`, File 10 §11) reproducible. The live projection applies `Durable` facts in ledger-commit order — the order in which snapshot resolution replays the durable log (§10.3) — so the live world model and a `WorldSnapshot` resolved to the same anchor agree on `Durable` state.

The world model never applies a signal that mutates a substrate it does not own. Updating a `Run` entity's status reflects what File 04 reported; it does not change the run. Updating a `File` entity's dirty flag reflects an observed file change; the file-write itself is a capability call (`run.capability-execution`, File 04 §8). The world model is update-only through declared producers and read-mostly for everyone else.

Every mutating update carries producer identity, declared ownership, expected entity revision or snapshot anchor, and the affected entity/attribute paths. `world.update` rejects writes outside the producer's declaration unless policy grants explicit override authority. If the entity or attribute changed since the producer read it, the update fails with a typed conflict instead of last-write-wins. When authoritative producers disagree, the world model records a conflict fact or typed update failure; it does not choose a winner silently. Read-only producers may emit candidate observations, but they cannot mutate durable world state without registration and policy flow.

### 8.3 Producer Normalization

Producers must normalize noisy source signals before emitting world-state change events. Transient window-title changes from timers, counters, loading spinners, brief focus flickers during application switching, and similar unstable source artifacts must not produce world-state change events unless the producer's registered normalization policy classifies them as stable. Context-change events represent stable state transitions. Debouncing strategy, title normalization rules, and transient-state suppression policy are declared in the producer's self-registration and are configurable through settings. The world model rejects unregistered producers and may reject signals that violate the declared normalization contract.

### 8.4 Observation Boundary with Perception

Perception (File 19) is the sensor pipeline: it captures screenshots, traverses accessibility trees, extracts DOM, and detects file-system changes. The world model consumes perception's structured output — typically as `Observed`-tier `Observation` blocks or as typed signals — and projects it into entity attributes and surface state. The world model is structured-data-first: when structured observation is available (an accessibility tree, a DOM, a file content hash), the world model uses it; a raw screenshot or rendered-text capture is a fallback observation source for surfaces where structured state is unavailable (`core.world-model`, File 01 §6.7). The capture mechanics, the tiered sensing strategy, and the privacy controls of capture belong to File 19; the world model owns the resulting state and the contract by which observations update it.

### 8.5 Freshness and Staleness

A world fact carries `freshness_evidence` and `observed_at` (§4.2). `observed_at` is provenance metadata; freshness is derived from evidence. The world model marks a fact potentially stale when the system has reason to believe the environment changed since observation: a producer disconnected, a source emitted a change event, a dependent entity revision changed, a scope switched, an observation fingerprint mismatched, a sandbox/session terminated, or policy explicitly invalidated the fact. An observation that depends on prior state carries a staleness fingerprint (`artifact.observation`, File 09 §13), and a capability that mutates based on a prior observation revalidates currency before mutating, returning the typed `StateChangedSinceObservation` error on mismatch (`run.call-pipeline`, File 04 §8.2). The world model treats its last-known state as potentially stale, not as ground truth (`run.user-intervention`, File 04 §17.1).

Staleness is a hint, not a correctness gate, and not a polling loop. The world model does not poll to keep facts fresh; it observes changes through events and revalidates on use. A consumer that needs a guaranteed-fresh fact requests a re-observation (a fresh capability call or observation), which updates the world model through §8.2. Time-based staleness windows or refresh intervals are permitted only as an explicitly flagged, configurable fallback for facts whose source emits no change events (§8.6), never as a correctness condition.

### 8.6 Event-First Observation and the Polling Exception

Observation is event-driven by default: operating-system UI event streams, file-system change notifications, browser protocol events, and connection lifecycle signals drive state updates without polling. This is the canonical mechanism and the only one that satisfies the project constraint against time-based conditions.

Where a fact's source emits no change events — certain system metrics, some repository states, external services without push — a time-based poll or a staleness TTL is a permitted fallback. Every such use is an explicitly flagged exception: it is configurable (§15), it is never a correctness condition (the world model must remain correct if a scheduled poll never runs), and it must surface its cadence so the user can change it. The world model prefers an event source whenever one exists and treats polling as a degraded mode for sources that lack one.

### 8.7 Reconciliation

On process restart or after an offline interval, the world model reconstructs its live state from the durable substrate (§10) and from the current substrates it projects, then reconciles against reality: it re-observes the facts whose freshness matters, marks unreconcilable facts stale or unavailable, and drops entities whose underlying primitive no longer exists. Stale in-flight records left by a prior session (a `Run` that was running at restart, a session marked alive that did not survive) are reconciled to their typed terminal or orphan state per `run.cancellation` (File 04 §17.3). Reconciliation is the world model's startup-correctness mechanism; it does not silently present stale state as current.

### 8.8 Boundary

This file owns the update contract, the self-registration rule, the freshness/staleness model, and reconciliation. File 19 owns capture; File 09 owns observation blocks; File 04 owns stale-state revalidation and orphan reconciliation at the run level; File 20 owns the durable substrate's physical form.

## 9. State-Aware Capability Availability

Anchor: `world.state-aware-capability-availability`

### 9.1 Definition

The world model owns the availability evaluator: the deterministic function that takes the declared `availability_predicate` and `prerequisite_capabilities` of every capability (`capability.availability-predicate` (File 05 §15.2), `capability.prerequisite-capabilities` (File 05 §15.3)), evaluates them against the current world snapshot, and produces the available-capability list — the set of capabilities and control affordances that are currently invocable. `capability.availability-predicate` (File 05 §15.2) delegates this evaluator to this file; `capability.discovery` (File 05 §15.1)'s availability-filtered enumeration, `surface.visibility-composition-resolution-algorithm` (File 07 §9)'s composition, the discovery, direct-affordance, and binding rails' resolvers, and the agent's availability grounding all consume the produced list.

### 9.2 `WorldPredicate`

`availability_predicate` has two parts (`capability.availability-predicate`, File 05 §15.2): `requires` (state that must be present) and `blocked_by` (state that prevents invocation). Both are expressed as `WorldPredicate` clauses over the resolved `WorldSnapshot`. Common shorthands are allowed only as syntax sugar over these predicates.

The canonical predicate families:

- entity presence: a `WorldEntity` of a kind exists in scope, with optional canonical-reference or attribute match
- entity attribute match: a named attribute path equals, contains, or satisfies a typed comparison
- relation existence: a relation of a kind connects two entity selectors
- active surface/unit/focus/selection match: active surface binding, owning subsystem, primary unit kind, focus-target class, `SelectionKind`, or `UiMode`
- liveness status: a `Connection`, `Process`, `Sandbox`, `BrowserSession`, `BrowserPage`, or producer has an allowed status/validity
- scope match: required conversation, workspace, run, task, session, or headless scope properties are present
- sensitivity eligibility: the target resource/entity is eligible for the invoking consumer under policy
- named registered check: a pure named check declared per §9.3

Typical `requires` shorthands — required primary unit kind, active surface binding, owning subsystem, selection kind, active conversation, UI mode, entity presence, and connection liveness — lower to these predicates. Typical `blocked_by` shorthands — in-flight run, unsaved changes, blocking UI mode, blocking entity presence, and named custom check — do the same. A capability whose availability cannot be expressed as typed predicates registers a named availability check (§9.3); ad-hoc procedural availability is rejected (`capability.availability-predicate`, File 05 §15.2). The vocabulary is closed canonical plus the registered named-check extension. The family set is DELIBERATELY delta-free: every family is a pure function of one snapshot (§9.3, §16), so "changed since X" is not a predicate and cannot become one — a change is an event the perception layer commits and the automation layer consumes (`automation.event-and-webhook-triggers`, File 33 §5.1); a per-watcher change baseline cannot live in a grammar shared by capability availability and every watch.

### 9.3 Registered Availability Checks

A named availability check is a registered, inspectable predicate over the world snapshot that a subsystem, plugin, or surface declares (for example, the Coder surface registers a check that a workspace contains tests; the GUI Control surface registers a check that the foreground application is in an allowed category). A check is a pure function of the supplied world snapshot — it takes no hidden inputs and produces a stable boolean for the same snapshot. Checks register through the same proposal-first mechanism as capabilities and custom kinds (`capability.runtime-mutation`, File 05 §16.2) and are evaluated by the world model when a predicate names them. Procedural checks that read mutable hidden state outside the world snapshot are rejected; the determinism of §8.2 and §10 depends on checks being functions of the snapshot.

### 9.4 Prerequisite Capabilities

`prerequisite_capabilities` (`capability.prerequisite-capabilities`, File 05 §15.3) name capabilities that must have been invoked, with a successful outcome, within a named scope before the dependent capability becomes invocable. The world model evaluates prerequisites against ledger facts (the recorded successful invocations, File 10) and world facts (the resulting entities), not against hidden local flags. A capability invoked while a prerequisite is unsatisfied returns the typed `PrerequisiteUnsatisfied` error in-band (`capability.prerequisite-capabilities`, File 05 §15.3). Entity-presence requirements (§9.2) are the world-fact half of this: a capability that operates on an artifact requires the corresponding `ArtifactInScope` entity (`artifact.artifact`, File 09 §3).

### 9.5 The Evaluation Algorithm

To produce the available-capability list for a scope, the world model:

1. resolves the world snapshot for the scope (§10)
2. for each enabled, registered capability (`capability.registered-capability`, File 05 §10), evaluates its `requires` predicate against the snapshot; a capability whose requirements are unmet is excluded
3. evaluates its `blocked_by` predicate; a capability that is blocked is excluded
4. evaluates its `prerequisite_capabilities` against ledger and world facts; a capability with unsatisfied prerequisites is excluded (or included with a typed not-yet-available marker, per the consumer's request)
5. returns the resulting list, projected as `SurfaceState.available_capabilities` for the scope and consumed by File 05's enumeration, File 07's composition, the discovery lens, and the model request

The evaluation is deterministic given the world snapshot, the registry snapshot, and the ledger anchor — the same inputs always produce the same list, with no clock-based effects (File 07's determinism requirement). The evaluator is fast enough to run on every relevant state change and on every capability enumeration; expensive or speculative availability reasoning is not part of the evaluator (it belongs to model-mediated policy classification, `policy.auto-decide-mode` (File 06 §8), which is off by default).

### 9.6 Boundary

The world model produces the available-capability list. It does not decide approval (File 06), zone placement (File 07), or invocation (File 04). It supplies the list those layers consume. The capability author declares the predicates (File 05); the world model evaluates them.

## 10. `WorldSnapshot` and Replay

Anchor: `world.world-snapshot-replay`

### 10.1 Definition

A `WorldSnapshot` is the world-model state at a durable anchor, addressed by a `world_snapshot_id`. Per `version.snapshots` (File 11 §14), a snapshot is not a stored copy of the world model; it is a durable addressing identity that resolves to state by walking the world model's durable substrate to an anchor. Runs (`run.minimum-durable-reconstruction`, File 04 §2.6), route records (`routing.route-record`, File 03 §3.5), version commits (`version.artifact-version-chains`, File 11 §13), capability invocations, policy grants (`policy.persistence`, File 06 §11.6), and provider calls (File 17) carry `world_snapshot_id` references; replay and audit (`ledger.replay-semantics`, File 10 §11) resolve them.

### 10.2 The Durable Substrate

The world model maintains its own durable substrate (`version.closed-canonical-snapshot-catalogue`, File 11 §14.2): an append-only log of `Durable`-tier world-state-change facts (§7) — recorded as ledger entries under the `world` namespace plus the canonical durable entries File 10 names (`EnvironmentSnapshotCaptured` and the world-relevant lifecycle entries). The substrate is the projection source from which any `WorldSnapshot` is reconstructed. `Ephemeral` facts are not in the substrate; `Observed` facts are referenced by the `Observation` block they committed (`artifact.observation`, File 09 §13), which is itself durable.

### 10.3 Resolution

`resolve_world_snapshot(world_snapshot_id)` resolves by:

1. identifying the anchor: the commit boundary and corresponding world-substrate sequence position named by the snapshot id
2. walking the durable world-state log from a storage-owned baseline to that sequence anchor, applying each fact to the world-model projection (the deterministic projection of §8.2)
3. resolving `Observed`-tier facts to the `Observation` blocks current at the anchor
4. resolving `Ephemeral`-tier facts to the nearest durable checkpoint or to a typed "unobserved at anchor" value — these facts were never durably recorded and cannot be reconstructed exactly
5. returning the resolved `WorldSnapshot`

Resolution is deterministic given the durable log and the referenced observation blocks: two resolutions of the same snapshot id over the same log produce identical state, modulo the explicitly-typed `Ephemeral` gaps. A snapshot that cannot be resolved returns a typed error; the resolver never silently substitutes current state for a past anchor (`version.snapshot-resolution`, File 11 §14.4).

### 10.4 Determinism and the Projection Contract

The world model is a `Projection` per `version.version-graph-backed-projections` (File 11 §16): it declares its substrate (the durable world-state log, the block pool's observation blocks, and the referenced run/task/lease/registry state), its rebuild trigger (event-driven, with on-demand rebuild for snapshot resolution), its rebuildability (a full rebuild from the substrate reproduces the projection), and its corruption tolerance (a detected inconsistency triggers a rebuild, never data loss). The live world model and any resolved `WorldSnapshot` are rebuildable artifacts, not the source of truth for any durable fact.

### 10.5 Boundary

This file owns the snapshot identity, the durable substrate's logical content, and the resolution contract. File 11 owns the snapshot-catalogue placement and the generic resolution machinery; File 20 owns the substrate's physical layout and the baseline/checkpoint optimization; File 09 owns the observation blocks the `Observed` tier references.

## 11. Exposure and Consumption

Anchor: `world.exposure-consumption`

### 11.1 `WorldView` and the Query Interface

The world model exposes a read interface: a current-snapshot read for a scope, a per-entity query (by id, kind, relation, or attribute filter), a named-availability-check evaluation, an available-capability-list query for a scope, and a `world_snapshot_id` resolution. These are the operations consumers use; §13 declares them as capabilities.

`WorldView` is the consumer-specific projection returned by `world.get(scope, consumer_kind)` or equivalent. It is computed at query time over the one world model. It is never materialized as a separate store, never cached independently of the underlying world-model state, and never synced or persisted as its own substrate. The mechanism is parameterized querying with sensitivity filtering, not consumer-specific state.

Canonical `consumer_kind` values: `Routing`, `Policy`, `ToolSurface`, `ContextAssembly`, `UI`, `Audit`, and `Capability`, plus registered `Custom { namespace, name }` consumers. Policy views may see redaction-safe resource identities needed for enforcement. Context-assembly views receive summaries, source attribution, authority, sensitivity, and pointers, not secret payloads. UI and audit views may expose more detail only when the user and policy permit it.

### 11.2 Exposure to the Agent (Context Assembly)

The world model is exposed to the agent as a context-assembly source (File 13). Context assembly renders a compact world-snapshot part into the `RuntimeState` region (`context.semantic-regions`, File 13 §3) as a `trusted_runtime_fact` (`context.authority-classes`, File 13 §2.3): the active surface, open units, primary unit, selection, available capabilities/control affordances, ui mode, the grounding environment and temporal facts, and the relevant connection liveness. The part is assembled fresh for each model-bound iteration (`context.assembly-algorithm`, File 13 §6 step 3, `run.iteration` (File 04 §7.2)) so the agent sees current state, not stale state — the query-format-inject pattern, never permanently stored model-request text. The part resolves the iteration's `PresentationContext` (§5.1): a user-originated iteration uses the origin context captured with its trigger, a continuing run uses its run-resolved context, and a noninteractive run uses its typed noninteractive descriptor — the part never switches because the user's attention moved to an unrelated context after dispatch, and the cross-context inventory stays capability-queryable rather than injected by default. Under budget pressure, assembly compacts the world part to a one-line summary before dropping load-bearing context (`context.budget-overflow`, File 13 §9). The part carries the `world_snapshot_id` for replay. An `Ephemeral`-tier world fact (§7) may be included in a live model-bound assembly, but because it is never individually durably recorded it is reconstructable at replay only when the consuming `AssemblySnapshot` captured it or a durable snapshot reference covers it (`context.assembly-replay-snapshot`, File 13 §19); otherwise it resolves to the nearest durable checkpoint or a typed "unobserved at anchor" value (§10.3). The agent reads structured state; it is not shown raw screenshots when structured state exists (`core.world-model`, File 01 §6.7). State awareness tells the agent where it is, not how to behave (`core.interaction-shapes`, File 01 §2.2): autonomy is governed by permission tiers and leases, not by the world model.

### 11.3 Exposure to Routing, Policy, and Tool Surfaces

Routing reads the world snapshot in its frame (`routing.routing-frame`, File 03 §3.1) and records the snapshot reference in the route record (`routing.route-record`, File 03 §3.5). The approval router and tier resolver read the world snapshot (`policy.approval-router` (File 06 §3), `policy.effective-tier-resolution` (File 06 §4), File 05 `TierResolver::Dynamic`). Tool-surface composition reads the world snapshot and the available-capability list (`surface.visibility-composition-resolution-algorithm`, File 07 §9). Each consumer resolves the snapshot for its scope and for its invocation's `PresentationContext` (§5.1): an interactive trigger resolves its origin context, a run-internal iteration resolves its run context, and a noninteractive trigger resolves its typed noninteractive context. No consumer substitutes the attention target (`ui.shell`, File 37 §4.4) or a cross-context aggregate for that resolution — presentation attention never enters routing, policy, or any authority decision. The world model supplies the snapshot.

### 11.4 Exposure to the UI

The world model exposes reactive subscriptions so surfaces and inspectors stay synchronized with live state. A subscription is event-driven (the transient and durable events of §12), not polling. The transport is the canonical event bus and the platform's typed IPC channels (File 10, File 01 stack commitments); this file specifies the reactivity contract, not the transport. The UI both consumes the world model (presenting units, available capabilities/control affordances, liveness indicators) and contributes to it (self-registration, §8.1).

Subscriptions are cancellable resources. Each subscription has an identity, owner, scope, filter, sensitivity policy, and cancellation relationship. It can be killed individually and is also cancelled categorically when its owning run, child run, surface, session, sandbox, or subsystem is killed. If a subscription uses a polling fallback because no event source exists, that fallback is visible in diagnostics and configurable through settings.

### 11.5 Scoping and Multi-Session

The world model is multi-session and multi-scope. Surface state, focus, selection, and active-work facts are resolved per conversation, run, or session, and within a scope per `PresentationContext` (§5.1); environment, display, and connection facts are typically global or workspace-scoped; workspace and repository facts are workspace-scoped. There is no assumption of a single active stream (File 07's rejection of the single-active-stream anti-pattern, `run.parallelism` (File 04 §15)) and no assumption of a single presentation context (`ui.shell`, File 37 §4.5). A consumer always resolves world state for an explicit scope and, where surface state is concerned, an explicit presentation context; cross-scope and cross-context reads are explicit. Events carry the scope identifiers (conversation, run, workspace) so subscribers demultiplex correctly (`ledger.event-envelope`, File 10 §5.2).

### 11.6 Boundary

This file owns the exposure and query contract. The consumers own what they do with the state. The transport and the rendering belong to File 10 and the UI specs.

## 12. State-Change Events and Reactivity

Anchor: `world.state-change-events-reactivity`

### 12.1 Event Vocabulary

World-model state changes emit events on the canonical bus (File 10). The transient (`Ephemeral`-tier) surface-state events `ledger.app-event-catalogue` (File 10 §5.3) reserves are canonical: `UiUnitRegistered`, `UiUnitUnregistered`, `UiPrimaryUnitChanged`, `UiSelectionChanged`, `UiModeChanged`, `UiAvailableCapabilitiesRecomputed`. The durable (`Durable`-tier) world-state events — active-surface change, subsystem/surface-binding change, workspace open/close, session and connection lifecycle, environment-snapshot capture — flow through the bus and commit to the ledger; `EnvironmentSnapshotCaptured` is the canonical durable entry (`ledger.entry-kind-catalogue`, File 10 §4.1), and additional world events register as `Custom { namespace: world }` (`ledger.custom-kind-registration`, File 10 §4.3). This file registers the presentation-context extension cross-reference key (`ledger.cross-references`, File 10 §3.6), and every context-qualified world fact — durable or transient — carries it: on a durable fact the recorded `PresentationContextRef` is historical correlation only, never a live handle (§5.1; `runtime.persistence-replay`, File 42 §21.1). Fine-grained focus changes remain `Ephemeral` exactly as §7.1 assigns them. The `Observed`-tier produces `ObservationCommitted` events (File 09, File 10). There is no `InteractionShapeChanged` event; interaction shape is not world-model state (§5.5).

### 12.2 Transient versus Durable Delivery

`Ephemeral` events flow on the live bus only and are not individually recorded to the durable ledger (`ledger.app-event-catalogue`, File 10 §5.3) — high-frequency surface churn must not flood durable storage. `Durable` events flow on the live bus and commit to the ledger and the world model's durable substrate (§10.2). `Observed` events reference the committed `Observation` block. The tier (§7) determines delivery; consumers that need durable history read the ledger and the substrate, consumers that need live coordination subscribe to the bus.

### 12.3 Reactivity

A world-state change that affects capability availability triggers re-evaluation of the available-capability list (§9) and emits `UiAvailableCapabilitiesRecomputed`, batched so it does not fire on every keystroke (the source material's batching guidance; File 07's reactive recomposition). A world-state change that affects lease validity — workspace switch, presentation-unit or surface change, ui-mode transition — signals lease revalidation to the policy layer (`policy.mid-execution-policy-re-evaluation` (File 06 §10), `policy.persistence` (File 06 §11.6)); the world model emits the state-change event, and File 06 decides revalidation. A world-state change that flips a tool-surface availability predicate triggers File 07's recomposition. The world model emits the signals; the consuming layers react.

### 12.4 Boundary

This file owns the world-event vocabulary and the reactivity-signal contract. File 10 owns the envelope, the delivery, and the ledger commit; File 06 owns lease revalidation; File 07 owns recomposition.

## 13. Capability Surface

Anchor: `world.capability-surface`

### 13.1 Closed Canonical Capabilities

The world model exposes its operations through the canonical Capability Registry (File 05). Each is a built-in capability declared per `capability.declaration` (File 05 §3) and registered at startup with the `Builtin` source. The canonical world-model capability set:

- `world.get(scope, consumer_kind)` — returns the current `WorldSnapshot`, `WorldView`, or `SurfaceState` projection for a scope and consumer; `ReadOnly`, `ConcurrencySafe`
- `world.query(filter)` — returns world entities by kind, relation, attribute filter, or id; `ReadOnly`, `ConcurrencySafe`
- `world.watch(scope, filter)` — opens a reactive subscription to world-state changes for a scope and returns `world_subscription_id`; `ReadOnly`, subscription-producing
- `world.register_surface(surface_spec)` / `world.register_unit(unit_state)` / `world.unregister_unit(unit_id)` — surface and presentation-unit self-registration (§8.1); update-only producer operations scoped to the registering producer
- `world.update(patch)` — applies a typed partial update to the world model from a declared producer (§8.2); the producer may update only the entities and facts it owns
- `world.set_focus(unit_id)` / `world.set_selection(selection)` — focus and selection updates from the owning surface
- `world.ingest_observation(observation_ref, affected_entities, update_intent)` — consumes an existing `Observation` block or structured observation signal as an `Observed`-tier fact and links affected entities by `observes`; Observation block creation is owned by File 09 and File 19
- `world.evaluate_availability(scope)` — returns the available-capability list for a scope (§9); `ReadOnly`, `ConcurrencySafe`, deterministic over the snapshot
- `world.evaluate_check(check_name, scope)` — evaluates a named availability check (§9.3) against the scope's snapshot
- `world.resolve_snapshot(world_snapshot_id)` — resolves a snapshot identity to a `WorldSnapshot` (§10); `ReadOnly`, `deterministic_replayable`

### 13.2 Capability Metadata

Read capabilities (`world.get`, `world.query`, `world.evaluate_availability`, `world.evaluate_check`, `world.resolve_snapshot`) declare `ReadOnly` permission tier, `ConcurrencySafe` concurrency, and `deterministic_replayable` replay class. `world.watch` is read-only but creates a cancellable subscription resource, so it declares subscription ownership, cancellation, and cleanup semantics separately from one-shot reads. Producer capabilities (`world.update`, `world.register_*`, `world.set_*`, `world.ingest_observation`) declare touched resources over the world-model entity and surface-state pools (registered as extension resource classes per `capability.extension-resource-classes` (File 05 §6.3)), and a tier that reflects what they touch: surface self-registration and focus/selection updates are low-tier, while `world.ingest_observation` inherits the tier of the observation's touched resources and sensitivity (`artifact.capability-surface`, File 09 §16). World-model events emit per §12; world-model capabilities flow through the standard pipeline (`run.call-pipeline`, File 04 §8.2) and policy (File 06).

### 13.3 Boundary

Capabilities are declared per File 05, executed per File 04, policed per File 06, surfaced per File 07. This file specifies the canonical world-model capability set; per-surface and subsystem specs register additional producer capabilities through the same mechanism.

## 14. Persistence Contract

Anchor: `world.persistence-contract`

### 14.1 What Is Durable

- the `Durable`-tier world-state-change log (§10.2) — workspace, surface, subsystem/surface-binding, session, and connection lifecycle facts, and `EnvironmentSnapshotCaptured` entries — survives restart and is the snapshot-resolution substrate
- `Observed`-tier facts are durable as `Observation` blocks (`artifact.observation`, File 09 §13), referenced by the world model
- registered `Custom` entity kinds, relation kinds, and availability checks persist in the registry under the source-trust envelope (`capability.registered-capability`, File 05 §10, `policy.source-approval-flow` (File 06 §9))
- world-model settings (§15)

### 14.2 What Is Computed

- the live world model itself — a projection rebuildable from the durable substrate plus the referenced run/task/lease/registry/block state (§10.4)
- `Ephemeral`-tier facts — live-only, never durably recorded
- the available-capability list — computed per scope from the snapshot, the registry, and the ledger (§9)
- resolved `WorldSnapshot`s — computed on demand by resolution (§10.3)
- any model-dependent attribute (token counts of in-view content) — computed and keyed by model/tokenizer identity, never stored as an unkeyed scalar (`core.explicit-rejections`, File 01 §8)

### 14.3 Reconstruction

On restart, the live world model is reconstructed from the durable substrate and reconciled against reality (§8.7). On retry, edit, reroute, or branch (`run.retry-reroute-branch`, File 04 §19), a new run resolves its own world snapshot; the durable substrate is shared. Determinism of resolution (§10.3) guarantees that the world snapshot a replay sees matches the snapshot the original execution recorded, modulo typed `Ephemeral` gaps.

### 14.4 Boundary

This file specifies what is durable, computed, and reconstructable. File 20 realizes the physical substrate, the baseline/checkpoint optimization, and the table layout; File 21 decides which world facts cross devices (most are device-local: displays, processes, sandboxes, foreground application; few are syncable).

## 15. Settings

Anchor: `world.settings`

World-model behavior is configurable through the canonical settings system (File 15); this file names the dimensions, the settings system owns the cascade and storage. Settings use namespaced keys (`world.*`) and declare scope, agent exposure, and locality per File 15.

Settings dimensions include:

- which `WorldEntityKind`s are tracked, per scope and per surface, and per-kind enable/disable
- the durability tier per fact kind (§7), with the safe default per kind and a user override; the tier may be narrowed (more durable) or widened (more ephemeral) only within the durability floor rules of §7.3
- the compactness budget for the surface-state and world-snapshot assembly part (§5.2, §11.2)
- agent exposure of world-model parts (which entities, facts, and attributes appear in the agent's context, and at what rendering fidelity), per File 15 `agent_exposure`
- the available-capability recomputation batching behavior (§12.3)
- producer normalization policy: debounce strategy, title normalization, transient-state suppression policy, and source-specific stability rules (§8.3)
- the freshness/staleness policy per `Observed` fact kind, including whether a time-based staleness TTL or poll fallback is enabled for sources without change events (§8.6) — disabled by default in favor of event-driven observation, flagged when enabled
- reactive subscription behavior, cancellation defaults, and the transport selection where the platform offers choices
- world-snapshot retention and the durable-substrate baseline/checkpoint cadence (delegated in detail to Storage)
- per-scope overrides: global, workspace, conversation, profile, surface, and explicit invocation overlay

Settings define intended product variation; they are not hidden hardcoded branches (`core.typed-configuration-failure`, File 01 §7.6, `settings.settings-over-constants` (File 15 §13)). Specific defaults belong to settings profiles, not to this canonical layer.

## 16. Explicit Rejections

Anchor: `world.explicit-rejections`

The following shapes are wrong for this layer:

- screenshot-driven or rendered-text-parsing self-perception as the foundation of the world model — structured data is the foundation; visual capture is a fallback observation source (`core.world-model`, File 01 §6.7)
- treating the world model as a durable source of truth for facts another layer owns — runs, tasks, blocks, memory, settings, leases, and capabilities are owned elsewhere; the world model projects and references them
- conflating the world model with memory — the world model is live current state; memory is durable learned state (§2.9)
- an interaction-shape, backend-autonomy-control, or execution-mode field in the world model — autonomy is governed by permission tiers and leases (Files 05, 06); `UiMode` is interaction state, not an autonomy control (`core.interaction-shapes` (File 01 §2.2), `core.explicit-rejections` (File 01 §8))
- a single global surface state when multiple sessions are live — surface state is scope-resolved; the single-active-stream assumption is rejected (File 07)
- recording every transient surface change to the durable ledger — high-frequency surface churn is `Ephemeral` and transient-only (§7, `ledger.app-event-catalogue` (File 10 §5.3))
- storing world snapshots as copied rows — snapshots are addressing identities resolved over the durable log, not stored copies (`version.snapshots`, File 11 §14)
- silently substituting current state for a past anchor when a snapshot cannot be resolved — resolution returns a typed error (§10.3)
- ad-hoc procedural capability availability — availability is typed declarative predicates plus registered named checks that are pure functions of the world snapshot (§9, `capability.availability-predicate` (File 05 §15.2))
- a non-deterministic availability evaluator or one with clock-based effects — the evaluator is deterministic over the snapshot, registry, and ledger (§9.5, File 07)
- polling as the primary observation mechanism — observation is event-driven; polling and staleness TTLs are flagged, configurable fallbacks for sources without change events, never correctness conditions (§8.6, `core.event-first-by-default` (File 01 §7.15))
- deriving system behavior, scheduling, or correctness from elapsed time — current time is exposed as a grounding fact only (§6.2)
- a central observer that scrapes a rendered view — every producer self-registers its state (§8.1)
- a private per-surface or per-subsystem state store — there is one world model; surfaces and subsystems project and contribute to it
- a stored `WorldView` per consumer — `WorldView` is a query-time projection over the one world model, not a separate cache, sync object, or persistence substrate
- a generic `ConnectorResource` canonical kind — connector resources register specific `Custom` kinds through their owning integration; a vague umbrella kind has no stable cross-cutting attribute contract
- unnormalized foreground/context churn as world state — producers must suppress unstable source artifacts according to their registered normalization policy before emitting world-state changes
- raw secret content in any world fact, durable record, observation, or exposed snapshot — `Secret` facts carry safe descriptions only (§4.2, §7.3, `ledger.sensitivity-aware-persistence-retention` (File 10 §10))
- treating the world model as the perception sensor pipeline — capture mechanics belong to File 19; the world model owns the state those captures update (§8.4)
- creating `Observation` blocks through the world-model layer — File 09 and File 19 own observation creation; the world model ingests observation references and structured signals
- mutating a substrate the world model does not own through a world-model update — updates reflect what producers report; they never change runs, files, blocks, or memory (§8.2)

## 17. Consequences for Later Specs

Anchor: `world.consequences-for-later-specs`

Later specs must follow these rules:

- The Perception and Observation Pipelines spec (File 19) must produce structured observations and signals the world model consumes through §8's contract; it owns capture mechanics and privacy controls of capture, and must commit `Observed`-tier facts as `Observation` blocks per `artifact.observation` (File 09 §13). It must not define a parallel state model.
- Per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) and the System Agent spec must self-register their presentation units, entities, and observations into the one world model, declare their `Custom` entity kinds and named availability checks through the canonical registration mechanism, and must not introduce a private state store.
- The Workspaces and Materialization spec must own workspace identity and materialization while exposing active workspaces as `Workspace` entities; the world model references them.
- The Work Surface Contract spec (File 25) must define how surfaces statically declare presentation units, capabilities/control affordances, and context policies; the world model holds the live values those declarations take.
- The Automation and Triggers spec must drive triggers from explicit events and world-state changes, not from the world model's exposed clock; current time is grounding, not a scheduler.
- Storage specs must persist the durable world-state log, the registered extensions, and the settings, and must realize snapshot resolution as a walk over the durable log with an optional baseline/checkpoint optimization; they must not store world snapshots as copied rows.
- Sync specs must consume locality metadata: most world facts are device-local (displays, processes, sandboxes, foreground application, sessions) and do not sync; few are syncable.
- Security specs must treat `Secret` world facts as safe-description-only and own the credential and trust state the world model references by id.
- UI specs must render the world model as a projection and contribute to it through self-registration; they must consume the reactive subscription, not poll.
- Capability, policy, routing, tool-surface, execution, and context specs already depend on this layer (`capability.discovery`, File 05 §15, File 06, `routing.routing-frame` (File 03 §3.1), `surface.visibility-composition-resolution-algorithm` (File 07 §9), `run.minimum-durable-reconstruction` (File 04 §2.6)/`run.call-pipeline` (File 04 §8.2)/`run.pause-resume` (File 04 §17.2), `context.semantic-regions` (File 13 §3)) and must resolve world state for an explicit scope, consume the available-capability list and the world snapshot this file defines, and reference snapshots by `world_snapshot_id`.

## 18. Canonical Rule Anchors

Anchor: `world.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `world.chosen-model`, `world.boundaries-with-adjacent-layers`, `world.world-model`, `world.world-entity`, `world.surface-state`, `world.environment-temporal-connection-facts`, `world.durability-tiers`, `world.observation-state-update`, `world.state-aware-capability-availability`, `world.world-snapshot-replay`, `world.exposure-consumption`, `world.state-change-events-reactivity`, `world.capability-surface`, `world.persistence-contract`, and `world.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
