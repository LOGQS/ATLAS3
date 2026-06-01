# Core Thesis, Invariants, and Primitives

## 1. Product Thesis {core.product-thesis}
- ATLAS is a local-first intent operating environment.
- ATLAS is NOT a chat app with tools, disconnected mini-apps with an AI sidebar, or a single heavy agent loop for every request.
- ATLAS IS one shared runtime, many possible presentations, strong standalone work surfaces plus cross-surface composition.
- Conversation is always available but is NOT the root durable model.

## 2. System Layers {core.system-layers}
### 2.1 Control Rails
- Rails initiate/steer work; they are not the work model.
### 2.2 Interaction Shapes / User Involvement {core.interaction-shapes}
- Interaction shapes are a conceptual design lens; NOT a required backend primitive, NOT a mandatory stored enum, NOT a separate execution architecture.
### 2.3 Work Surfaces
- Surfaces own user-facing workflows and views; do not own private architecture.
### 2.4 Substrate Services {core.substrate-services}
- Substrate services support all surfaces and rails; not classified as primary work surfaces.
### 2.5 Infrastructure

## 3. Workspace Model {core.workspace-model}
### 3.1 Workspace
- Every conversation must have a durable scoped context for storage/execution/settings/materialization.

## 4. Canonical Abstractions {core.canonical-abstractions}
### 4.1 `IntentThread`
### 4.2 `Task`
- Minimum fields: goal, scope, constraints, status, assumptions, open questions, success criteria.
### 4.3 `Artifact` {core.artifact}
- Artifacts are not file-only; files are one artifact form.
### 4.4 `Evidence` {core.evidence}
### 4.5 Execution
- Execution is history; event streaming is live coordination.
### 4.6 `Block`
- Block content is immutable after creation; typed; composable; reusable across surfaces+services.
### 4.7 `Run`
### 4.8 `RunIntent`
- Minimum fields: target intent thread, relevant surfaces and capability families, execution depth, model/tool strategy.

## 5. Current Major-Area Classification {core.current-major-area-classification}
- 5.1 Conversation → Control rail
- 5.2 Coder → Work surface
- 5.3 Web → Work surface
- 5.4 Data Processor → Work surface
- 5.5 Teacher → Work surface
- 5.6 GUI Control → Work surface
- 5.7 System Agent → Work surface with heavy substrate dependencies
- 5.8 Cross-Cutting Substrate Services (Memory, routing/orchestration, context assembly/retrieval, knowledge/indexing, settings, evaluation/logging, capability registry/policy, world modeling, perception, versioning, storage, history) → substrate services with optional management surfaces; not primary work surfaces; no work surface gets a private copy.

## 6. Primitive Set {core.primitive-set}
- Every later spec must build on these primitives.
### 6.1 Rust Service Layer
- Business logic lives in the Rust service layer; command handlers are adapters, not ownership boundaries.
### 6.2 Capability Contract
- Minimum responsibilities: input schema, output schema, touched-resource description, permission class, validation path.
### 6.3 Capability Policy
### 6.4 Execution Ledger {core.execution-ledger}
- Must record at least: proposals, actions, approvals, observations, validations, mutations.
### 6.5 Event Stream
- Not the canonical history mechanism.
### 6.6 Block Graph
### 6.7 World Model {core.world-model}
- Must represent at least: active surface and owning subsystem, mounted panels, focused element, available capabilities and control affordances, active workspaces, other relevant structured runtime state.
- Screenshot-driven self-perception is fallback, not foundation.
### 6.8 Settings System {core.settings-system}
- Scoped (global, workspace, conversation, with clear resolution order); reactive; policy-aware; progressive; agent-exposure-controlled; each setting declares hidden-from / available-on-request / included-in-model-request; not replaced by hardcoded behavior branches.
### 6.9 Typed Errors {core.typed-errors}
- Cross-boundary failures must be typed values across backend, UI, provider boundaries.
### 6.10 Versioned Durable State {core.versioned-durable-state}
### 6.11 Projection {core.projection}
- Every projection must be rebuildable from its source-of-truth; must declare rebuild trigger (event-driven, on-demand, or periodic); never the source of truth for any durable fact.
### 6.12 Routing and Dispatch Layer
- Must separate: direct fast-path dispatch, intent-thread attachment/creation, surface+capability selection, execution-strategy selection, model-selection+tool-selection strategy.
### 6.13 Model Strategy Layer
- Must support: per-capability/per-surface preferred models; specialized handling for image/math/coding/browsing workloads; user-overridable defaults; rate-limit-aware+availability-aware fallback; direct tool-first flows when no model step is needed.
### 6.14 Extension Planes {core.extension-planes}
- Extension dimensions: capabilities, instructions and knowledge, surfaces, integrations, automation, configuration.
- Core features and external contributions must register into the same shared systems through the same paths.
- Runtime registration supported where appropriate.
- A single capability definition is the source for all invocation paths (palette, shortcuts, voice, agent tools, automation triggers, external protocol).
- Extensions must not override security-critical system state (env vars controlling paths/linkers/interpreters; credential storage; policy kernels).
### 6.15 Canonical Encoding {core.canonical-encoding}
- A `CanonicalEncoding` must define: field order, enum tag encoding, optional-field representation, null-vs-omitted semantics, integer/string/boolean encoding, map key ordering, collection ordering, a schema/version tag inside the encoded payload.
- Order-insensitive collections must be sorted by a stable key before encoding; order-sensitive sequences must preserve order and be explicitly declared order-sensitive.
- A `CanonicalEncoding` is never defined by or inferred from physical storage.
### 6.16 Closed Canonical Set {core.closed-canonical}
- May evolve only through: declared `Custom`/extension variants where permitted, a future canonical spec revision, explicit migration+compatibility rules when durable state is affected.
- Implementations must not add ad-hoc variants outside a declared extension path.

## 7. Invariants {core.invariants}
- 7.1 Shared Runtime — all user experiences are presentations of one shared runtime.
- 7.2 Shared Capability System — user and agent invoke the same underlying capability system through different control rails.
- 7.3 Durable History, Transient Coordination {core.durable-history-transient-coordination} — execution history is durable; streaming/event coordination is not the source of truth.
- 7.4 Context Interoperability — no subsystem may introduce a private incompatible context model.
- 7.5 Flexible Presentation — presentation shape may vary without changing the underlying runtime model.
- 7.6 Typed Configuration and Failure {core.typed-configuration-failure} — intended product variation belongs in typed settings+policy; cross-boundary failures must be typed and behaviorally meaningful.
- 7.7 Service-Layer Ownership — business logic belongs to the backend service layer, not UI components or command wrappers.
- 7.8 Local Extensibility {core.local-extensibility} — new surfaces/tools/subsystems must be addable without broad rewrites.
- 7.9 System-Wide Customization — when meaningful behavioral variations exist, expose them as options rather than hardcoding one; must not gatekeep valid behavioral variations.
- 7.10 Extension Integrity — extensions must be inspectable, reversible, toggleable, policy-bound; AI-assisted customization uses the same system paths as manual; no canonical subsystem may make a built-in implementation the semantic boundary.
- 7.11 User Control and Killability — Atlas-managed long-running work must remain under user control; runs, child-run trees, processes, sandboxes, tool calls must be cancellable/killable categorically and individually; non-killable execution is an explicit exception later specs must justify.
- 7.12 Evidence and Provenance {core.evidence-provenance} — reusable/shareable outputs must carry enough lineage to be trustworthy+reviewable.
- 7.13 Non-Destructive by Default {core.non-destructive-by-default} — operations on user content/context/artifacts/execution history/system state must be non-destructive by default; compaction changes view state not data; edits create siblings not mutations; version switching always available; irreversible operations are explicit exceptions later specs must justify; system must track consumed storage and expose it as structured data; user must inspect/manage/reclaim storage at every granularity; retention policies/quotas/expiry are settings, not hardcoded limits.
- 7.14 Canonical Hashing {core.canonical-hash} — every hash used for identity/integrity/dedup/sync/replay/cache validation/audit must be computed over a declared `CanonicalEncoding`, never over physical storage encoding; applies without exception including `content_hash`, `diff_hash`, `expected_view_hash`, block+content-address hashes, audit-chain hashes, snapshot+integrity hashes; order-insensitive collections sorted by stable key before hashing; cross-device hash equality is never the correctness basis for sync.

## 8. Explicit Rejections {core.explicit-rejections}
- chat-app-with-tools framing
- one-heavy-path-for-all-requests architecture
- single-surface/subsystem routing as universal execution model
- coupling interaction shape to surface or subsystem identity
- coupling model choice to one universal router decision
- private per-surface context models
- normalizing non-killable long-running execution
- business logic in React or command wrappers
- interaction shapes as rigid backend autonomy controls
- silent last-write-wins for concurrent mutations of shared state
- storing model-dependent values as unkeyed plain scalars

## 9. Stack Commitments {core.stack-commitments}
- Locked: Rust backend, Tauri shell, React + TypeScript frontend, SQLite or libsql local persistence, typed IPC, MCP as external extension+integration protocol.

## 10. Consequences for Later Specs {core.consequences-for-later-specs}
- A later spec is wrong if it contradicts §§2–6, violates any §7 invariant, or reintroduces a §8 rejected shape.

## 11. Canonical Rule Anchors {core.canonical-rule-anchors}
- Load-bearing rules must carry a stable semantic anchor (lowercase dotted-namespace id).
- Anchors must be stable across revisions; an anchor names exactly one rule.
- Cross-references should prefer the anchor.
