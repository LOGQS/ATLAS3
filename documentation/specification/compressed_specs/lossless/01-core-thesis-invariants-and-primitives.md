> Lossless render of canonical/01-core-thesis-invariants-and-primitives.md — original 26132 chars

# Core Thesis, Invariants, and Primitives

## Status
Canonical. Defines foundational architecture for ATLAS3. Later canonical files may refine, may not contradict.

## Scope
Defines: product identity; system layer boundaries; canonical foundational abstractions; current major-area classification; non-negotiable architectural invariants; primitive set later specs must reuse.
Does not define: database schemas; exact UI layouts; exact provider lists; per-surface tool catalogs; exact execution-node grammar.

## Source Resolution
Resolves foundational product/architecture/primitive/invariant material into the canonical thesis and substrate vocabulary. Resolved design: ATLAS is a local-first intent operating environment, not a chat app with tools; one shared runtime with multiple presentations, work surfaces, substrate services, control rails; participation levels are a UX design lens, not a backend primitive; Blocks, capabilities, execution, events, settings, world state, versioned durable state are foundational primitives later files reuse; extensibility/customization are system-wide invariants, not optional subsystem features.

## 1. Product Thesis `core.product-thesis`
- ATLAS is a local-first intent operating environment. User expresses intent → system interprets in context, attaches to existing/new ongoing work, selects capabilities, optionally materializes surfaces, executes+validates actions, produces durable outputs, preserves structure for continuation/inspection/reuse.
- Important outputs become durable artifacts with evidence. Successful patterns eligible for crystallization into reusable knowledge/procedures/automations. System maintains a live structured model of current environment (workspaces, files, processes, sessions, connections, active work) so capabilities reason about the world, not just conversation history.
- ATLAS is NOT: a chat app with tools; disconnected mini-apps with an AI sidebar; a single heavy agent loop for every request.
- ATLAS IS: one shared runtime; many possible presentations of it; strong standalone work surfaces plus strong cross-surface composition.
- Conversation is always available but is NOT the root durable model.

## 2. System Layers `core.system-layers`
Four architectural layers + one cross-cutting design lens.

### 2.1 Control Rails
Universal entry/control mechanisms through which user/system invokes capabilities. Examples: conversation, command palette, keyboard shortcuts, voice and handsfree input, automation triggers. Boundary: rails initiate/steer work; they are not the work model.

### 2.2 Interaction Shapes / User Involvement `core.interaction-shapes`
Degree/shape of user involvement in a running experience; a presentation+interaction choice over the same runtime. Interpretation rule: conceptual design lens for UX shape/user involvement — NOT a required backend primitive, NOT a mandatory stored enum, NOT a separate execution architecture. Examples: conversation-only, inline assist, sidecar workspace, hands-on paired workspace, orchestration desk / multi-agent control view. Boundary: not a subsystem/surface identity; not a backend ontology requirement; not a separate execution system; not a rigid backend autonomy control; can vary per surface, per request, over time.

### 2.3 Work Surfaces
Primary user-facing work environments with substantial workflows+UI. Current examples: Coder, Web, Data Processor, Teacher, GUI Control, System Agent. Boundary: own user-facing workflows and specialized views; do not own private architecture.

### 2.4 Substrate Services `core.substrate-services`
Always-on/cross-cutting services supporting all surfaces and rails. Current examples: Memory, routing and orchestration, capability registry, capability policy and approvals, context assembly and retrieval, knowledge and indexing, world modeling, versioning and history, settings, logging and evaluation. Boundary: may expose management UIs/inspectors/tools but are not classified the same as primary work surfaces.

### 2.5 Infrastructure
Technical foundation hosting+executing the runtime. Examples: Rust service layer, persistence, projections, filesystem and workspace services, browser backends, provider integration, sync, packaging, security boundaries.

## 3. Workspace Model `core.workspace-model`
### 3.1 Workspace
Durable scoped environment for files, state, tools, history, user-visible work materialization. Rules: every conversation has a durable scoped context for storage/execution/settings/materialization; major work surfaces should support one or many workspaces; workspace multiplicity is normal; substrate services may be global/workspace-scoped/conversation-scoped/mixed. Boundary: a user-visible workspace is a system capability, not a mandatory UX doorway — a conversation's durable scoped context may be exposed as a visible workspace or remain latent.

## 4. Canonical Abstractions `core.canonical-abstractions`
### 4.1 `IntentThread`
Primary durable unit of ongoing work continuity; groups related user intent across time, even when informal, paused, branched, resumed, or shifting presentation. Contains: zero+ messages, zero+ promoted tasks, zero+ runs, related artifacts and evidence. Does not require: explicit task formalization; a dedicated workspace view; one surface/subsystem only.

### 4.2 `Task`
Promoted, structured work object inside an intent thread; exists when work benefits from explicit structure. Minimum fields: goal, scope, constraints, status, assumptions, open questions, success criteria. Promotion rule: not every intent thread needs a task immediately; a task should exist when explicit decomposition, approvals, artifact tracking, automation, or deep execution management becomes useful.

### 4.3 `Artifact` `core.artifact`
Durable output worth keeping/rendering/exporting/versioning/feeding into later work/citing. Examples: file, code patch, lesson, curriculum, chart, browser extract, notebook output, whiteboard scene, report. Boundary: artifacts are not file-only; files are one artifact form.

### 4.4 `Evidence` `core.evidence`
Support structure behind decisions/claims/outputs. Examples: source fragments, tool results, observations, validations, citations, grounded claims. Purpose: makes outputs inspectable, reviewable, safer to reuse.

### 4.5 Execution
Durable record of what the system attempted, proposed, ran, observed, validated, approved, rejected, changed. Boundary: execution ≠ event streaming; execution is history, event streaming is live coordination.

### 4.6 `Block`
Universal durable context-bearing unit for cross-surface interoperability+context assembly. Rules: block content immutable after creation; typed; composable; reusable across surfaces+services. Boundary: not the only top-level abstraction; the common context unit.

### 4.7 `Run`
Durable record of one bounded attempt to progress work; may answer a simple request, perform tool-using work, execute a workflow, run a surface runtime, or coordinate child runs. Boundary: full run lifecycle/structure/semantics belong in the execution spec; this section establishes only that Run is a canonical abstraction.

### 4.8 `RunIntent`
Structured result of routing+dispatch planning for an incoming request/continuation step. Minimum fields: target intent thread, relevant surfaces and capability families, execution depth, model/tool strategy. Boundary: not "pick one surface/subsystem"; the runtime's decision envelope for how to proceed.

## 5. Current Major-Area Classification `core.current-major-area-classification`
- 5.1 Conversation → Control rail (always-available control+continuity surface; not the universal work model).
- 5.2 Coder → Work surface (software engineering workflows/views/tools/materialization).
- 5.3 Web → Work surface (browsing, research, browser control).
- 5.4 Data Processor → Work surface (extraction, transformation, analysis, data outputs).
- 5.5 Teacher → Work surface (lessons, curricula, assessments, classroom-style experiences).
- 5.6 GUI Control → Work surface (desktop observation, interaction, automation, control).
- 5.7 System Agent → Work surface with heavy substrate dependencies (watches, scheduled actions, system observation, rollback-oriented ops, system-level automation; depends strongly on shared execution/policy/infrastructure).
- 5.8 Memory → Substrate service with management surfaces (always integrated; serves every surface; not workspace-first shape). May still expose: browsers, inspectors, proposal UIs, graph views, settings, management actions.
- 5.9 Routing, Context, Knowledge, Settings, Evaluation → Substrate services (coordinate/support every surface; must not drift into per-surface private architecture).

## 6. Primitive Set `core.primitive-set`
Every later spec must build on these.

### 6.1 Rust Service Layer
Authoritative backend contract layer where business logic lives. Boundary: React is not a business-logic layer; command handlers are adapters, not ownership boundaries.

### 6.2 Capability Contract
Typed declaration of an operation the system can perform. Minimum responsibilities: input schema, output schema, touched-resource description, permission class, validation path. Purpose: unify agent invocation, UI invocation, policy, replay, inspection.

### 6.3 Capability Policy
Shared permission+approval system governing capability use. Purpose: keep safety/approval/allowed scope out of per-surface bespoke logic.

### 6.4 Execution Ledger `core.execution-ledger`
Durable append-oriented record of execution facts. Must record at least: proposals, actions, approvals, observations, validations, mutations. Purpose: replay, audit, debugging, trustworthy history.

### 6.5 Event Stream
Typed live coordination stream for streaming UI, hooks, runtime notifications. Boundary: not the canonical history mechanism.

### 6.6 Block Graph
Graph structure of blocks + explicit relations. Purpose: support context assembly, provenance, composition, cross-surface interoperability. Boundary: flat isolated block rows are insufficient as the long-term model.

### 6.7 World Model `core.world-model`
Structured live model of what system+user currently interact with. Must represent at least: active surface and owning subsystem; mounted panels; focused element; available capabilities and control affordances; active workspaces; other relevant structured runtime state. Boundary: screenshot-driven self-perception is fallback, not foundation.

### 6.8 Settings System `core.settings-system`
Centralized typed configuration governing intended product variation. Rules: scoped (global, workspace, conversation levels with clear resolution order); reactive; policy-aware; progressive (simple by default, full depth available); agent-exposure-controlled (each setting declares hidden-from / available-on-request / included-in-model-request); not replaced by hardcoded behavior branches.

### 6.9 Typed Errors `core.typed-errors`
Typed cross-boundary failure values across backend, UI, provider boundaries. Purpose: failure must drive behavior, not only display.

### 6.10 Versioned Durable State `core.versioned-durable-state`
Versionable+reconstructable durable state for context+artifact history. Purpose: undo, branching, inspection, deterministic reconstruction.

### 6.11 Projection `core.projection`
Read-optimized derived view of canonical state, required for responsive UI+query workloads. Rules: every projection rebuildable from its source-of-truth; must declare rebuild trigger (event-driven, on-demand, or periodic); not the source of truth for any durable fact; cost of stale/corrupted projection is a rebuild, never data loss.

### 6.12 Routing and Dispatch Layer
Shared decision layer determining how a request is handled. Must separate: direct fast-path dispatch; intent-thread attachment/creation; surface+capability selection; execution-strategy selection; model-selection+tool-selection strategy. Boundary: domain selection alone is too weak to be the routing output.

### 6.13 Model Strategy Layer
Workload-aware model selection+fallback. Must support: per-capability/per-surface preferred models; specialized handling for image, math, coding, browsing, similar workloads; user-overridable defaults; rate-limit-aware+availability-aware fallback; direct tool-first flows when no model step is needed. Boundary: no single universal model choice handles all requests the same way.

### 6.14 Extension Planes `core.extension-planes`
Dimensions across which the system is extensible: capabilities, instructions and knowledge, surfaces, integrations, automation, configuration. Rules: core features and external contributions register into the same shared systems through the same paths; runtime registration supported where appropriate (not only startup-time); cost of adding contribution N+1 is flat; a single capability definition is the source for all invocation paths (command palette, shortcuts, voice, agent tools, automation triggers, external protocol exposure); extensions must not override security-critical system state (env vars controlling paths/linkers/interpreters; credential storage; policy kernels).

### 6.15 Canonical Encoding `core.canonical-encoding`
A `CanonicalEncoding` is a declared, storage-independent byte encoding of a typed value, used wherever a value must hash/compare/deduplicate/sync/reconstruct identically across devices/processes/time. Must define: field order; enum tag encoding; optional-field representation; null-vs-omitted semantics; integer/string/boolean encoding; map key ordering; collection ordering; a schema/version tag inside the encoded payload. Ordering rule: order-insensitive collections sorted by a stable key before encoding; order-sensitive sequences preserve order and are explicitly declared order-sensitive. Boundary: physical storage encoding is separate (JSON/CBOR/MessagePack/Protobuf/row tuples/columnar/etc.); a `CanonicalEncoding` is never defined by or inferred from physical storage.

### 6.16 Closed Canonical Set `core.closed-canonical`
A fixed enumeration (kinds, variants, vocabulary, or states) closed for runtime interoperability within the current spec version. May evolve only through: declared `Custom`/extension variants where the set explicitly permits; a future canonical spec revision; explicit migration+compatibility rules when durable state is affected. Rule: implementations must not add ad-hoc variants outside a declared extension path; "Closed" constrains implementations, not the spec's own future revisions. Boundary: closing a set is an interoperability guarantee, not a permanent freeze.

## 7. Invariants `core.invariants`
Only load-bearing rules; definitions/taxonomy/examples belong in earlier sections.
- 7.1 Shared Runtime — all user experiences are presentations of one shared runtime, not separate product architectures.
- 7.2 Shared Capability System — user and agent invoke the same underlying capability system through different control rails.
- 7.3 Durable History, Transient Coordination `core.durable-history-transient-coordination` — durable history and live coordination are separate; execution history is durable; streaming/event coordination is not the source of truth.
- 7.4 Context Interoperability — durable context-bearing content must remain interoperable through the shared context model; no subsystem may introduce a private incompatible context model.
- 7.5 Flexible Presentation — presentation shape may vary by surface, interaction shape, request complexity without changing the underlying runtime model.
- 7.6 Typed Configuration and Failure `core.typed-configuration-failure` — intended product variation belongs in typed settings+policy; cross-boundary failures must be typed and behaviorally meaningful.
- 7.7 Service-Layer Ownership — business logic belongs to backend service layer, not UI components or command wrappers.
- 7.8 Local Extensibility `core.local-extensibility` — new surfaces/tools/subsystems must be addable without broad rewrites across existing ones.
- 7.9 System-Wide Customization — customization spans settings, profiles, layouts, themes, workflows, tools, model behavior, integrations. When meaningful behavioral variations exist, expose them as options rather than hardcoding one; best overall option is the default; progressive disclosure keeps default simple while making deeper config reachable; must not gatekeep valid behavioral variations.
- 7.10 Extension Integrity — extensions must be inspectable, reversible, toggleable, policy-bound; AI-assisted customization uses the same system paths as manual; plugins are cohesive contribution bundles, not synonymous with subsystems/surfaces, not a separate execution architecture. Specific engines, libraries, adapters, providers, parsers, rankers, vector stores, search backends are replaceable implementations behind typed contracts; a built-in implementation may be recommended, but no canonical subsystem may make that implementation the semantic boundary.
- 7.11 User Control and Killability — Atlas-managed long-running work must remain under user control; runs, child-run trees, processes, sandboxes, tool calls, other long-running Atlas-managed units should be cancellable/killable both categorically and individually; non-killable execution is an explicit exception later specs must justify.
- 7.12 Evidence and Provenance `core.evidence-provenance` — important outputs should preserve evidence of how they were produced; artifacts/recommendations/automations should be traceable to sources, tool results, observations, validations; degree of provenance depends on output significance (not every response needs a citation chain, but reusable/shareable outputs carry enough lineage to be trustworthy+reviewable); later specs define where/how per subsystem+surface.
- 7.13 Non-Destructive by Default `core.non-destructive-by-default` — operations on user content/context/artifacts/execution history/system state must be non-destructive by default; compaction changes view state not data; edits create siblings not mutations; version switching always available; irreversible operations are explicit exceptions later specs must justify. Non-destructive ≠ unbounded storage: system must track consumed storage (workspaces, artifacts, execution history, cached data, version trees) and expose it as structured data backend serves+frontend renders; user must inspect/manage/reclaim storage at every granularity (full reset, per-category cleanup, per-workspace, per-task, per-artifact); retention policies/quotas/expiry are settings, not hardcoded limits.
- 7.14 Canonical Hashing `core.canonical-hash` — every hash used for identity/integrity/dedup/sync/replay/cache validation/audit is computed over a declared `CanonicalEncoding` (§6.15), never over physical storage encoding. Applies without exception incl. `content_hash`, `diff_hash`, `expected_view_hash`, block+content-address hashes, audit-chain hashes, snapshot+integrity hashes, any future canonical hash. Order-insensitive collections sorted by stable key before hashing; order-sensitive sequences preserve order+declared order-sensitive. Two peers may rely on hash equality only when sharing same `CanonicalEncoding` version; cross-device hash equality is an optimization for dedup/duplicate-suppression, never the correctness basis for sync.

## 8. Explicit Rejections `core.explicit-rejections`
Architecturally invalid:
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

## 9. Stack Commitments `core.stack-commitments`
Locked enough to design around: Rust backend; Tauri shell; React + TypeScript frontend; SQLite or libsql local persistence; typed IPC; MCP as external extension+integration protocol. Everything else at this layer remains subordinate to the abstractions above.

## 10. Consequences for Later Specs `core.consequences-for-later-specs`
Any later spec is wrong if it: contradicts definitions in §§2–6; violates any invariant in §7; reintroduces a rejected shape from §8.

## 11. Canonical Rule Anchors `core.canonical-rule-anchors`
Load-bearing rules carry a stable semantic anchor (lowercase dotted-namespace id, e.g. `core.canonical-hash`, `policy.effective-tier-resolution`) naming the rule independently of its section. Rules: anchor stable across revisions (section numbers may be renumbered, anchors may not); cross-references should prefer the anchor (`see core.canonical-hash`) and may cite section number secondarily (`File 01 §7.14`); an anchor names exactly one rule (two rules never share); anchors introduced as rules are formalized (a rule without anchor referenced by section number until assigned). Anchors defined/referenced by this series include `core.canonical-hash`, `core.canonical-encoding`, `core.closed-canonical`, `block.content-hash`, `version.diff-hash`, `version.expected-view-hash`, `context.assembly-replay-snapshot`, `policy.effective-tier-resolution`, `run.completion-contract`, `secret.backend-boundary`, `provider.token-source`.
