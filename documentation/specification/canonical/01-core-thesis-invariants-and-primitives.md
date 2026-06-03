# Core Thesis, Invariants, and Primitives

## Status

Canonical. This file defines the foundational architecture for ATLAS3. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- product identity
- system layer boundaries
- canonical foundational abstractions
- current major-area classification
- non-negotiable architectural invariants
- primitive set that later specs must reuse

This file does not define:

- database schemas
- exact UI layouts
- exact provider lists
- per-surface tool catalogs
- exact execution-node grammar

## Source Resolution

This file resolves foundational product, architecture, primitive, and invariant material into one boundary: the canonical thesis and substrate vocabulary that later specs must consume.

Resolved design:

- ATLAS is a local-first intent operating environment, not a chat app with tools.
- The product is one shared runtime with multiple presentations, work surfaces, substrate services, and control rails.
- Participation levels are a UX design lens, not a backend primitive.
- Blocks, capabilities, execution, events, settings, world state, and versioned durable state are the foundational primitives later files reuse.
- Extensibility and customization are system-wide invariants, not optional subsystem features.

## 1. Product Thesis

Anchor: `core.product-thesis`

ATLAS is a local-first intent operating environment.

The user expresses intent. The system interprets that intent in context, attaches it to existing ongoing work or creates new ongoing work, selects the right capabilities, optionally materializes the right surfaces, executes and validates actions, produces durable outputs, and preserves enough structure for continuation, inspection, and reuse.

Important outputs become durable artifacts with evidence. Successful work patterns are eligible for crystallization into reusable knowledge, procedures, and automations. The system maintains a live structured model of the current environment — workspaces, files, processes, sessions, connections, and active work — so that capabilities can reason about the world, not just about conversation history.

The product goal is broad computer-mediated usefulness: learning, programming, research, data work, system operation, browsing, creation, and any other process where a user may want different degrees of help. ATLAS is not narrowly an automation product. It is a composable local work substrate where AI helps connect surfaces, substrate services, tools, memory, retrieval, workflows, and settings so the user can start simply and then scale to the complexity they choose. Defaults must be clean and safe; depth comes through progressive disclosure, reusable units, and typed customization rather than mandatory complexity.

ATLAS is not:

- a chat app with tools
- a set of disconnected mini-apps with an AI sidebar
- a single heavy agent loop used for every request

ATLAS is:

- one shared runtime
- many possible presentations of that runtime
- strong standalone work surfaces plus strong cross-surface composition

Conversation is always available, but it is not the root durable model.

## 2. System Layers

Anchor: `core.system-layers`

ATLAS has four architectural layers and one cross-cutting design lens.

### 2.1 Control Rails

Definition:
Universal entry and control mechanisms through which the user or system invokes capabilities.

Examples:

- conversation
- command palette
- keyboard shortcuts
- voice and handsfree input
- automation triggers

Boundary:
Control rails initiate or steer work. They are not themselves the work model.

### 2.2 Interaction Shapes / User Involvement

Anchor: `core.interaction-shapes`

Definition:
The degree and shape of user involvement in a running experience. An interaction shape is a presentation and interaction choice over the same underlying runtime.

Interpretation rule:
This is a conceptual design lens for reasoning about UX shape and user involvement. It is not a required backend primitive, not a mandatory stored enum, and not a separate execution architecture.

Examples:

- conversation-only
- inline assist
- sidecar workspace
- hands-on paired workspace
- orchestration desk / multi-agent control view

Boundary:

- not a subsystem or surface identity
- not a backend ontology requirement
- not a separate execution system
- not a rigid backend autonomy control
- can vary per surface, per request, and over time

### 2.3 Work Surfaces

Definition:
Primary user-facing work environments with substantial workflows and substantial UI.

Current examples:

- Coder
- Web
- Data Processor
- Teacher
- GUI Control
- System Agent

Boundary:
Work surfaces own user-facing workflows and specialized views. They do not own private architecture.

### 2.4 Substrate Services

Anchor: `core.substrate-services`

Definition:
Always-on or cross-cutting services that support all work surfaces and control rails.

Current examples:

- Memory
- routing and orchestration
- capability registry
- capability policy and approvals
- context assembly and retrieval
- knowledge and indexing
- world modeling
- versioning and history
- settings
- logging and evaluation

Boundary:
Substrate services may expose management UIs, inspectors, and tools, but they are not classified the same way as primary work surfaces.

### 2.5 Infrastructure

Definition:
The technical foundation that hosts and executes the runtime.

Examples:

- Rust service layer
- persistence
- projections
- filesystem and workspace services
- browser backends
- provider integration
- sync
- packaging
- security boundaries

## 3. Workspace Model

Anchor: `core.workspace-model`

### 3.1 Workspace

Definition:
A durable scoped environment for files, state, tools, history, and user-visible work materialization.

Rules:

- every conversation has a durable scoped context for storage, execution, settings, and materialization
- major work surfaces should support one or many workspaces
- workspace multiplicity is normal
- substrate services may be global, workspace-scoped, conversation-scoped, or mixed

Boundary:
A user-visible workspace is a system capability, not a mandatory UX doorway. A conversation's durable scoped context may be exposed as a visible workspace, or may remain latent while the user stays entirely in the conversation interface.

## 4. Canonical Abstractions

Anchor: `core.canonical-abstractions`

### 4.1 IntentThread

Definition:
The primary durable unit of ongoing work continuity. An intent thread groups related user intent across time, even when that work is informal, pauses, branches, resumes, or shifts presentation.

Contains:

- zero or more messages
- zero or more promoted tasks
- zero or more runs
- related artifacts and evidence

Does not require:

- explicit task formalization
- a dedicated workspace view
- one surface/subsystem only

### 4.2 Task

Definition:
A promoted, structured work object inside an intent thread. A task exists when the work benefits from explicit structure.

Minimum fields:

- goal
- scope
- constraints
- status
- assumptions
- open questions
- success criteria

Promotion rule:
Not every intent thread needs a task immediately. A task should exist when explicit decomposition, approvals, artifact tracking, automation, or deep execution management becomes useful.

### 4.3 Artifact

Anchor: `core.artifact`

Definition:
A durable output worth keeping, rendering, exporting, versioning, feeding into later work, or citing.

Examples:

- file
- code patch
- lesson
- curriculum
- chart
- browser extract
- notebook output
- whiteboard scene
- report

Boundary:
Artifacts are not file-only. Files are one artifact form.

### 4.4 Evidence

Anchor: `core.evidence`

Definition:
The support structure behind decisions, claims, and outputs.

Examples:

- source fragments
- tool results
- observations
- validations
- citations
- grounded claims

Purpose:
Evidence makes outputs inspectable, reviewable, and safer to reuse.

### 4.5 Execution

Definition:
The durable record of what the system attempted, proposed, ran, observed, validated, approved, rejected, and changed.

Boundary:
Execution is not the same as event streaming. Execution is history. Event streaming is live coordination.

### 4.6 Block

Definition:
The universal durable context-bearing unit used for cross-surface interoperability and context assembly.

Rules:

- block content is immutable after creation
- blocks are typed
- blocks are composable
- blocks are reusable across surfaces and services

Boundary:
Blocks are not the only top-level abstraction. They are the common context unit.

### 4.7 Run

Definition:
A durable record of one bounded attempt to progress work. A run may answer a simple request, perform tool-using work, execute a workflow, run a surface runtime, or coordinate child runs.

Boundary:
The full run lifecycle, structure, and semantics belong in the execution spec. This section establishes only that Run is a canonical abstraction referenced by other abstractions.

### 4.8 RunIntent

Definition:
The structured result of routing and dispatch planning for an incoming request or continuation step.

Minimum fields:

- target intent thread
- relevant surfaces and capability families
- execution depth
- model/tool strategy

Boundary:
RunIntent is not "pick one surface/subsystem." It is the runtime's decision envelope for how to proceed.

## 5. Current Major-Area Classification

Anchor: `core.current-major-area-classification`

This section classifies the current major areas so later specs do not drift on taxonomy.

### 5.1 Conversation

Classification:
Control rail.

Why:
Conversation is the always-available control and continuity surface. It can host rich experiences, but it is not the universal work model.

### 5.2 Coder

Classification:
Work surface.

Why:
Coder owns specialized workflows, views, tools, and workspace materialization for software engineering work.

### 5.3 Web

Classification:
Work surface.

Why:
Web owns specialized workflows, views, tools, and workspace materialization for browsing, research, and browser control.

### 5.4 Data Processor

Classification:
Work surface.

Why:
Data Processor owns specialized workflows, views, tools, and workspace materialization for extraction, transformation, analysis, and data outputs.

### 5.5 Teacher

Classification:
Work surface.

Why:
Teacher owns specialized workflows, views, tools, and outputs for lessons, curricula, assessments, and classroom-style educational experiences.

### 5.6 GUI Control

Classification:
Work surface.

Why:
GUI Control owns specialized workflows, views, and tools for desktop observation, interaction, automation, and control.

### 5.7 System Agent

Classification:
Work surface with heavy substrate dependencies.

Why:
System Agent owns user-facing workflows around watches, scheduled actions, system observation, rollback-oriented operations, and system-level automation, even though it depends strongly on shared execution, policy, and infrastructure services.

### 5.8 Cross-Cutting Substrate Services

Classification:
Substrate services with optional management surfaces.

Includes:

- Memory
- routing and orchestration
- context assembly and retrieval
- knowledge and indexing
- settings
- evaluation and logging
- capability registry and policy
- world modeling, perception, versioning, storage, and history

Why:

- always integrated
- serves every work surface
- coordinates or supports work across surfaces and control rails
- does not have the same shape as a primary workspace-first surface

What it may still expose:

- browsers
- inspectors
- proposal UIs
- graph views
- settings
- management actions

Boundary:
Management presentations over these services are not primary work surfaces, and no work surface receives a private version of any of them.

## 6. Primitive Set

Anchor: `core.primitive-set`

Every later spec must build on these primitives.

### 6.1 Rust Service Layer

Definition:
The authoritative backend contract layer where business logic lives.

Boundary:

- React is not a business-logic layer
- command handlers are adapters, not ownership boundaries

### 6.2 Capability Contract

Definition:
The typed declaration of an operation the system can perform.

Minimum responsibilities:

- input schema
- output schema
- touched-resource description
- permission class
- validation path

Purpose:
Unify agent invocation, UI invocation, policy, replay, and inspection.

### 6.3 Capability Policy

Definition:
The shared permission and approval system governing capability use.

Purpose:
Keep safety, approval, and allowed scope out of per-surface bespoke logic.

### 6.4 Execution Ledger

Anchor: `core.execution-ledger`

Definition:
A durable append-oriented record of execution facts.

Must record at least:

- proposals
- actions
- approvals
- observations
- validations
- mutations

Purpose:
Replay, audit, debugging, and trustworthy history.

### 6.5 Event Stream

Definition:
The typed live coordination stream for streaming UI, hooks, and runtime notifications.

Boundary:
The event stream is not the canonical history mechanism.

### 6.6 Block Graph

Definition:
The graph structure formed by blocks plus explicit relations between them.

Purpose:
Support context assembly, provenance, composition, and cross-surface interoperability.

Boundary:
Flat isolated block rows are insufficient as the long-term model.

### 6.7 World Model

Anchor: `core.world-model`

Definition:
The structured live model of what the system and user are currently interacting with.

Must be able to represent at least:

- active surface and owning subsystem
- mounted panels
- focused element
- available capabilities and control affordances
- active workspaces
- other relevant structured runtime state

Boundary:
Screenshot-driven self-perception is fallback, not foundation.

### 6.8 Settings System

Anchor: `core.settings-system`

Definition:
Centralized typed configuration governing intended product variation.

Rules:

- scoped: global, workspace, and conversation levels with clear resolution order
- reactive
- policy-aware
- progressive: simple surface by default, full depth available for users who want it
- agent-exposure-controlled: each setting declares whether it is hidden from, available on request to, or included in the model request
- not replaced by hardcoded behavior branches

### 6.9 Typed Errors

Anchor: `core.typed-errors`

Definition:
Typed cross-boundary failure values used across backend, UI, and provider boundaries.

Purpose:
Failure must drive behavior, not only display.

### 6.10 Versioned Durable State

Anchor: `core.versioned-durable-state`

Definition:
Versionable and reconstructable durable state for context and artifact-related history.

Purpose:
Undo, branching, inspection, and deterministic reconstruction.

### 6.11 Projection

Anchor: `core.projection`

Definition:
A read-optimized derived view of canonical state, required for responsive UI and query workloads.

Rules:

- every projection must be rebuildable from its source-of-truth data
- projections must declare their rebuild trigger (event-driven, on-demand, or periodic)
- projections are not the source of truth for any durable fact
- the cost of a stale or corrupted projection is a rebuild, never data loss

### 6.12 Routing and Dispatch Layer

Definition:
The shared decision layer that determines how a request should be handled.

Must separate:

- direct fast-path dispatch
- intent-thread attachment or creation
- surface and capability selection
- execution-strategy selection
- model-selection and tool-selection strategy

Boundary:
Domain selection alone is too weak to be the routing output.

### 6.13 Model Strategy Layer

Definition:
The workload-aware model selection and fallback system.

Must support:

- per-capability or per-surface preferred models
- specialized handling for image, math, coding, browsing, and similar workloads
- user-overridable defaults
- rate-limit-aware and availability-aware fallback
- direct tool-first flows when no model step is needed

Boundary:
There is no single universal model choice that should handle all requests the same way.

### 6.14 Extension Planes

Anchor: `core.extension-planes`

Definition:
The dimensions across which the system is extensible.

The system is extensible across: capabilities, instructions and knowledge, surfaces, integrations, automation, and configuration.

Rules:

- core features and external contributions register into the same shared systems through the same paths
- runtime registration is supported where appropriate, not only startup-time registration
- the cost of adding contribution N+1 is flat
- a single capability definition is the source for all invocation paths: command palette, shortcuts, voice, agent tools, automation triggers, and external protocol exposure
- extensions must not be able to override security-critical system state (environment variables controlling paths, linkers, or interpreters; credential storage; policy kernels)

### 6.15 Canonical Encoding

Anchor: `core.canonical-encoding`

Definition:
A `CanonicalEncoding` is a declared, storage-independent byte encoding of a typed value, used wherever a value must hash, compare, deduplicate, sync, or reconstruct identically across devices, processes, and time.

A `CanonicalEncoding` must define:

- field order
- enum tag encoding
- optional-field representation
- null-versus-omitted semantics
- integer, string, and boolean encoding
- map key ordering
- collection ordering
- a schema/version tag carried inside the encoded payload

Ordering rule:

- order-insensitive collections must be sorted by a stable key before encoding
- order-sensitive sequences must preserve their order and must be explicitly declared as order-sensitive

Boundary:
Physical storage encoding is a separate concern. Storage may use JSON, CBOR, MessagePack, Protobuf, row tuples, columnar formats, or any other layout. A `CanonicalEncoding` is never defined by, and never inferred from, the physical storage representation.

### 6.16 Closed Canonical Set

Anchor: `core.closed-canonical`

Definition:
A closed canonical set is a fixed enumeration — of kinds, variants, vocabulary, or states — that is closed for runtime interoperability within the current canonical specification version.

A closed canonical set may evolve only through:

- declared `Custom` or extension variants where the set explicitly permits them
- a future canonical specification revision
- explicit migration and compatibility rules when durable state is affected

Rule:
Implementations must not add ad-hoc variants outside a declared extension path. "Closed" constrains implementations, not the specification's own future revisions.

Boundary:
Closing a set is an interoperability guarantee, not a permanent freeze. Where a set is closed, a later spec that needs a new variant either uses the declared extension path or revises the canonical set explicitly with migration rules for any affected durable state.

## 7. Invariants

Anchor: `core.invariants`

Only load-bearing rules belong here. Definitions, taxonomy choices, and examples belong in earlier sections.

### 7.1 Shared Runtime

All user experiences are presentations of one shared runtime, not separate product architectures.

### 7.2 Shared Capability System

The user and the agent invoke the same underlying capability system through different control rails.

### 7.3 Durable History, Transient Coordination

Anchor: `core.durable-history-transient-coordination`

Durable history and live coordination are separate concerns. Execution history is durable; streaming/event coordination is not the source of truth.

### 7.4 Context Interoperability

Durable context-bearing content must remain interoperable through the shared context model. No subsystem may introduce a private incompatible context model.

### 7.5 Flexible Presentation

Presentation shape may vary by surface, interaction shape, and request complexity without changing the underlying runtime model.

### 7.6 Typed Configuration and Failure

Anchor: `core.typed-configuration-failure`

Intended product variation belongs in typed settings and policy. Cross-boundary failures must be typed and behaviorally meaningful.

### 7.7 Service-Layer Ownership

Business logic belongs to the backend service layer, not to UI components or command wrappers.

### 7.8 Local Extensibility

Anchor: `core.local-extensibility`

New surfaces, tools, and subsystems must be addable without broad rewrites across existing ones.

### 7.9 System-Wide Customization

Customization spans settings, profiles, layouts, themes, workflows, tools, model behavior, and integrations. When meaningful behavioral variations exist, the system should expose them as options rather than hardcoding one. The best overall option is the default. Progressive disclosure keeps the default experience simple while making deeper configuration reachable. The system must not gatekeep valid behavioral variations.

### 7.10 Extension Integrity

Extensions must be inspectable, reversible, toggleable, and policy-bound. AI-assisted customization must use the same system paths as manual customization. Plugins are cohesive contribution bundles, not synonymous with subsystems or surfaces and not a separate execution architecture.

Specific engines, libraries, adapters, providers, parsers, rankers, vector stores, and search backends are replaceable implementations behind typed contracts. A built-in implementation may be recommended, but no canonical subsystem may make that implementation the semantic boundary.

### 7.11 User Control and Killability

Atlas-managed long-running work must remain under user control.

Runs, child-run trees, processes, sandboxes, tool calls, and other long-running Atlas-managed units should be cancellable or killable both categorically and individually. Non-killable execution is an explicit exception that later specs must justify.

### 7.12 Evidence and Provenance

Anchor: `core.evidence-provenance`

Important outputs should preserve evidence of how they were produced. Artifacts, recommendations, and automations should be traceable to the sources, tool results, observations, and validations that informed them. The degree of provenance depends on the output's significance — not every conversation response requires a citation chain, but outputs the user may reuse, share, or build on should carry enough lineage to be trustworthy and reviewable. Later specs define where and how provenance applies per subsystem and surface.

### 7.13 Non-Destructive by Default

Anchor: `core.non-destructive-by-default`

Operations on user content, context, artifacts, execution history, and system state must be non-destructive by default. Compaction changes view state, not data. Edits create siblings, not mutations. Version switching is always available. Irreversible operations are explicit exceptions that later specs must justify.

Non-destructive does not mean unbounded storage. The system must track what storage it has consumed — workspaces, artifacts, execution history, cached data, version trees — and expose this as structured data the backend serves and the frontend renders. The user must be able to inspect, manage, and reclaim storage at every granularity: full reset, per-category cleanup, per-workspace, per-task, and per-artifact. Retention policies, quotas, and expiry rules are settings, not hardcoded limits.

### 7.14 Canonical Hashing

Anchor: `core.canonical-hash`

Every hash used for identity, integrity, deduplication, sync, replay, cache validation, or audit is computed over a declared `CanonicalEncoding` (§6.15), never over a physical storage encoding. Physical storage may use JSON, CBOR, MessagePack, Protobuf, SQLite rows, or another format; storage encoding is not hash encoding.

This applies without exception, including `content_hash`, `diff_hash`, `expected_view_hash`, block and content-address hashes, audit-chain hashes, snapshot and integrity hashes, and any future canonical hash.

Order-insensitive collections are sorted by a stable key before hashing; order-sensitive sequences preserve their order and are declared order-sensitive (§6.15). Two peers may rely on hash equality only when they share the same `CanonicalEncoding` version. Cross-device hash equality is an optimization for deduplication and duplicate-suppression, never the correctness basis for sync.

### 7.15 Event-First by Default

Anchor: `core.event-first-by-default`

Observation, reactivity, and projection rebuild are event-driven wherever a change source exists; a component that has a change-event source must consume it and must not poll. Time-based polling is never a correctness mechanism. Polling intervals, staleness timers, and periodic refresh are permitted only as flagged, configurable fallbacks for sources that emit no change events, or as explicit scheduler timers and safety guards owned by the relevant subsystem and computed as deadlines rather than evaluated as continuous conditions. Reading the current time as a world fact is grounding, not scheduling. Auto-continue countdowns, animation timings, and similar timed affordances are conveniences, never correctness conditions. Every exception is flagged and justified by the owning spec.

## 8. Explicit Rejections

Anchor: `core.explicit-rejections`

The following are architecturally invalid:

- chat-app-with-tools framing
- one-heavy-path-for-all-requests architecture
- single-surface/subsystem routing as the universal execution model
- coupling interaction shape to surface or subsystem identity
- coupling model choice to one universal router decision
- private per-surface context models
- normalizing non-killable long-running execution as an ordinary design choice
- business logic in React or command wrappers
- interaction shapes implemented as rigid backend autonomy controls in core architecture
- silent last-write-wins for concurrent mutations of shared state
- storing model-dependent values as unkeyed plain scalars (token counts, costs, capability flags must be keyed by model or provider identifier)

## 9. Stack Commitments

Anchor: `core.stack-commitments`

Locked enough to design around:

- Rust backend
- Tauri shell
- React + TypeScript frontend
- SQLite or libsql local persistence
- typed IPC
- MCP as the external extension and integration protocol

Everything else at this layer remains subordinate to the abstractions above.

## 10. Consequences for Later Specs

Anchor: `core.consequences-for-later-specs`

Any later spec is wrong if it:

- contradicts the definitions in sections 2 through 6
- violates any invariant in section 7
- reintroduces a rejected shape from section 8

## 11. Canonical Rule Anchors

Anchor: `core.canonical-rule-anchors`

Load-bearing canonical rules carry a stable semantic anchor in addition to their section number. An anchor is a lowercase dotted-namespace identifier (`core.canonical-hash`, `policy.effective-tier-resolution`) that names the rule independently of where it sits in the document.

Rules:

- a rule's anchor is stable across spec revisions; section numbers may be renumbered, anchors may not
- cross-references should prefer the anchor (`see core.canonical-hash`) and may cite the section number secondarily (`File 01 §7.14`)
- an anchor names exactly one canonical rule; two rules never share an anchor
- anchors are introduced as rules are formalized; a rule without an anchor is referenced by section number until one is assigned

Anchors defined or referenced by this specification series include `core.canonical-hash`, `core.canonical-encoding`, `core.closed-canonical`, `block.content-hash`, `version.diff-hash`, `version.expected-view-hash`, `context.assembly-replay-snapshot`, `policy.effective-tier-resolution`, `run.completion-contract`, `secret.backend-boundary`, and `provider.token-source`.
