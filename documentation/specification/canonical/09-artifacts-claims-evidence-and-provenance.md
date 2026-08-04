# Artifacts, Claims, Evidence, and Provenance

## Status

Canonical.

## Scope

This file defines:

- `Artifact` — the durable, identifiable, versionable user-visible product of the system as an entity layer over one or more `Artifact`-kind `Block`s
- `ArtifactVersion` — the durable per-version snapshot, materialized as the `Artifact`-kind `Block` already declared by `block.kind-catalogue` (File 08 §3.1)
- the closed canonical `ArtifactKind` catalogue plus the registered-extension mechanism
- `ArtifactLifecycle` — derived per-`ContextVersion` artifact-version view-state (`Draft`, `Active`, `Validated`, `Superseded`, `Archived`, `Discarded`)
- `ReviewState` and `ValidationState` per artifact version, with artifact-level state exposed as the active version's projection
- artifact materialization, materialized paths, and the `MaterializationPolicy` set (`InWorkspace`, `ExternalRef`, `None`)
- artifact tombstones for hard-deleted versions and lineage preservation
- `Claim` — a typed factual assertion, canonical extension to `block.kind-catalogue` (File 08 §3.1)'s block-kind catalogue, with stable identity, immutable assertion content, confidence class, scope, and anchor reference
- `ClaimKind`, `ClaimStatus`, `ClaimConfidenceClass`, and the optional numerical-confidence field
- claim publication, extraction, lifecycle, withdrawal, and supersession projection
- `Evidence` — the `Evidence` block-kind contract from File 08, extended with the `EvidenceLink` typed-edge metadata
- `EvidenceRelation` — closed canonical relation enum (`Supports`, `WeakSupports`, `Refutes`, `Contextualizes`, `Corroborates`, `Summarizes`, `Derives`, `Witnesses`, `IllustratesByExample`) plus the registered-extension mechanism
- evidence-link confidence, evidence-set closure rules, and the evidence-graph query surface
- `Citation` — the citation block-kind contract from File 08, extended with the `CitationReferenceKind` enum and `SourceSpan` grammar
- `Observation` — the observation block-kind contract from File 08, extended with the `ObservationKind` enum and the staleness-fingerprint contract
- `Validation` and `Critique` — the block-kind contracts from File 08, with `ValidationState` derivation rules from `validated_by` edges and integration with the `run.termination` (File 04 §22) completion-verification hook surface
- `Provenance` — a derived view (not a stored primitive) over the block graph, the version graph, and the execution ledger, with a closed canonical query surface
- the closed canonical capability surface for entity-level operations, enumerated in full in §16.1 (the principal operations include `artifact.create`, `artifact.commit_version`, `artifact.preview_export`, `artifact.export`, `artifact.set_review_state`, `artifact.archive`, `artifact.discard`, `artifact.hard_delete_version`, `claim.publish`, `claim.update_status`, `claim.withdraw`, `claim.attach_evidence`, `evidence.link`, `citation.capture`, `observation.commit`, `validation.run`, `validation.attach`, `provenance.query_lineage`, `provenance.query_evidence_set`, `provenance.query_replay_trace`, `provenance.contradiction_check`)
- cross-surface interoperability (one entity pool projected through surface-specific lenses)
- the persistence contract — what is durable, what is computed, what is reconstructable
- settings dimensions that govern artifact, claim, evidence, and provenance behavior

This file does not define:

- the `Block`, `BlockEdge`, or `BlockGraph` model itself — File 08 owns those; this file consumes them
- block immutability, sibling versioning, lifecycle state machinery, pin states, scope, sensitivity, or descriptions — File 08 owns those
- the execution ledger row format, event stream wire format, or storage projections — `run.ledger-events-commits` (File 04 §23) owns the contract, File 10 owns the ledger and event schemas, and File 20 owns storage schemas
- the version-graph commit storage or version-tree action-log shape — File 11 owns those; this file specifies which entity transitions emit version-commit boundaries
- retrieval, indexing, knowledge-base, retrieval-augmented generation mechanics, or hybrid-search algorithms — File 12 owns those
- context-assembly, compaction algorithms, token-budget mechanics, or per-policy block selection — File 13 owns those, though this file requires that compaction preserve evidence chains as specified in §11.5
- memory promotion, salience scoring, recall, decay, or consolidation — File 14 owns those, though this file requires that memory entries whose content originates from a Claim, Artifact, or Evidence record preserve their entity identity
- run lifecycle, the capability-call pipeline, hook execution, cancellation, streaming, or postcondition validation — File 04 owns those
- the `CapabilityDeclaration` field set, registry operations, or backend bindings — File 05 owns those; this file declares the entity-level capabilities listed above as canonical built-in capability declarations
- the policy evaluation algorithm, approval flows, leases, or contradiction-checking — File 06 owns those; this file specifies which entity mutations are tier-gated and how
- tool-surface zones, surface composition, or zone semantics — File 07 owns those; this file requires that artifact, claim, evidence, and provenance capabilities surface uniformly
- UI rendering choices for artifact previews, claim cards, evidence panels, citation chips, observation viewers, provenance trees, or validation badges — File 37 and File 38 own those; this file specifies the canonical data contracts those surfaces consume
- storage of credentials referenced by an artifact, claim, or evidence record — File 22 owns those
- sandbox primitives, isolation policy, or rendering-runtime details — File 23 owns those
- per-surface specifications (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) — those specs declare which artifact kinds and observation kinds they primarily produce; File 09 declares the canonical baseline

## Source Resolution

This file resolves artifact, claim, evidence, citation, observation, validation, critique, export, and provenance material into one boundary: durable semantic entities layered over blocks, versions, runs, and ledger facts.

Resolved design:

- Artifact, evidence, claim, observation, validation, and critique content is carried by blocks; this file defines their higher-level identity and lifecycle where needed.
- Claim tracking is opt-in structured semantics, not an obligation to turn every sentence into a claim.
- Evidence links carry relation, confidence, provenance, and applicability; balanced or conflicting evidence remains unresolved unless one side is stronger.
- Provenance is derived from the canonical graph of blocks, versions, runs, capability calls, and ledger entries, not from a parallel provenance store.
- Artifact materialization, export, and external representation are projections of durable artifact identity, not the identity itself.

## 1. Chosen Model

Anchor: `artifact.chosen-model`

ATLAS3 has one entity layer for produced outputs (`Artifact`), one entity layer for first-class factual assertions (`Claim`), one substrate for support records (`Evidence` + `Citation` + `Observation` + `Validation` + `Critique`, all of which are blocks per File 08), and one derived query surface for provenance.

The chosen model:

- significant produced outputs become `Artifact` entities — durable, versioned, materializable, validated, reviewable, citable, exportable products of the system. An artifact may be one inline object, one file, many files, a composed bundle, or a dynamic product rendered through a surface. Each `ArtifactVersion` is an `Artifact`-kind `Block` per `block.kind-catalogue` (File 08 §3.1); the entity record adds stable cross-version identity.
- the system's load-bearing assertions become `Claim` entities — durable, identifiable, status-tracked, evidence-linked, supersedable. The `Claim` block kind is a canonical extension to `block.kind-catalogue` (File 08 §3.1)'s catalogue declared here.
- support for claims, artifacts, and decisions flows through `Evidence`, `Citation`, `Observation`, `Validation`, and `Critique` blocks already canonical per File 08, plus the `EvidenceLink` typed-edge metadata declared here.
- the causal chain back from any block, edge, version, artifact, or claim to the producing run, capability, route, intent thread, conversation, and ledger entries is a queryable projection — `Provenance` — over the existing canonical substrates. There is no parallel provenance store.

There is no parallel artifact registry, no parallel claim registry, no parallel evidence registry, no parallel observation pool, and no parallel provenance database. Every entity participates in the unified `Block` pool (per `block.chosen-model`, File 08 §1) and the unified Capability Registry (per `capability.chosen-model`, File 05 §1); entity-level identity sits over those substrates as a thin record layer where strictly required.

`Artifact` supersedes any earlier vocabulary in source material that named the same primitive: "deliverable", "produced output", "generated file as entity", "work product", "drafts as named outputs", "artifact registry record". `Claim` supersedes any earlier vocabulary that named the same primitive: "assertion", "factual statement entity", "knowledge claim", "grounded fact", "agent answer as record". `Evidence` and `Citation` and `Observation` and `Validation` and `Critique` retain the names `block.kind-catalogue` (File 08 §3.1) already gave them. `Provenance` supersedes any earlier vocabulary that named the same projection: "lineage record", "audit chain", "origin trace", "derivation history record". The word "artifact" remains an informal synonym for an `Artifact`-kind block when the entity layer is not load-bearing; references like the `Artifact` block kind from `block.kind-catalogue` (File 08 §3.1) keep that vocabulary where it is already canonical.

The model elaborates the canonical abstractions from `core.artifact` (File 01 §4.3) (`Artifact`), `core.evidence` (File 01 §4.4) (`Evidence`), and `core.evidence-provenance` (File 01 §7.12) (Evidence and Provenance) into full entity and query primitives. It honors `run.output-semantics` (File 04 §24)'s listing of artifact versions, claims, evidence links, and validation reports among run outputs by giving each its canonical shape.

## 2. Boundaries with Adjacent Layers

Anchor: `artifact.boundaries-with-adjacent-layers`

### 2.1 With File 08 (Blocks and Block Graph)

The boundary is sharp. File 08 owns:

- the `Block` model, the closed canonical `BlockKind` catalogue (including `Artifact`, `Evidence`, `Citation`, `Observation`, `Validation`, `Critique`), and the `Custom { namespace, name }` extension mechanism
- the `BlockContent` discriminated enum, the `BlockEdge` model and the closed canonical edge catalogue (including `cites`, `witnesses`, `derives_from`, `supersedes`, `validated_by`, `consolidates`, `references`, `responds_to`)
- per-block fields `producer`, `origin_run_id`, `created_at`, `content_hash`, `source_attribution`, `default_sensitivity`, `description`, `scope`
- block lifecycle as per-version derived state, sibling-versioning via `supersedes`, hard-delete tombstones and composition materialization
- the block commit validator and the commit-boundary set in `block.commit-boundary-set` (File 08 §7.6)
- the persistence contract for blocks and edges in `block.block-persistence-contract` (File 08 §13)

File 09 owns:

- the `Artifact` entity record (the thin mapping from stable artifact_id to artifact-version projections, plus lifecycle/review derivation rules)
- the closed canonical `ArtifactKind`, `ArtifactLifecycle`, `ReviewState`, and `MaterializationPolicy` enums and the corresponding extension mechanism
- the `Claim` block kind as a canonical extension to File 08's `BlockKind` catalogue, plus `ClaimKind`, `ClaimStatus`, `ClaimConfidenceClass`
- the `EvidenceLink` typed-edge metadata and the `EvidenceRelation` enum, attached to edges of kinds `cites`, `witnesses`, `validated_by`, and the registered extension edges in §11.3
- the `CitationReferenceKind` enum and the `SourceSpan` grammar for `Citation` blocks
- the `ObservationKind` enum and the staleness-fingerprint contract for `Observation` blocks
- the `ValidationState` derivation rules over `validated_by` edges and the integration with `run.termination` (File 04 §22) completion-verification
- the `Provenance` derived query surface
- the closed canonical entity capability set in §16 and its required metadata

File 09 never invents a new block kind outside its declared `Claim` extension, never invents new edge kinds outside the `EvidenceRelation`-decorated variants of File 08's existing edges plus the explicitly-registered extension edges in §11.3, never introduces a parallel content carrier, and never mutates a block's stored fields. Every entity transition that requires durable record commits a new block (via File 08 commit) plus, where applicable, a new entity-record row (via File 20).

### 2.2 With File 04 (Execution and Run Model)

File 04 owns run lifecycle, the capability-call pipeline, hook execution, streaming, cancellation, and the canonical commit-boundary set. File 09 consumes these boundaries:

- artifact versions commit at the same boundaries `block.commit-boundary-set` (File 08 §7.6) enumerates (user message, accepted assistant turn, capability completion, router emission, inspector apply, workflow node complete, import, consolidation, manual draft commit, subsystem-internal boundary). An `ArtifactVersion` is created at the moment the producing capability commits the `Artifact`-kind block.
- live partial-write semantics (`run.streaming-partial-execution`, File 04 §12) apply to artifact materialization: the staged file becomes the durable artifact file at the atomic rename, which corresponds to the artifact-version commit.
- the `Validation` block-kind contract integrates with the `run.termination` (File 04 §22) completion-verification hook surface (§14.3 below).
- the completion-forgery guard in `run.termination` (File 04 §22) reads from the entity layer: a run whose contract required artifact creation cannot terminate `completed` if no `ArtifactVersion` was committed in the run's scope.
- per-call ledger attribution from `run.execution-ledger` (File 04 §23.1) records the `(artifact_id, version_id)`, `(claim_id)`, `(evidence_link_edge_id)` produced by each capability invocation.

### 2.3 With File 05 (Capability Contracts and Registry) and File 06 (Capability Policy)

Every entity-level operation in §16 is a `Capability` declared per `capability.declaration` (File 05 §3). The Capability Registry is the unified registry per `capability.chosen-model` (File 05 §1); File 09 introduces no parallel registry for entity operations. The declared `output_block_kinds` for each entity capability (per `capability.composition-fields`, File 05 §3.10) draws from File 08's canonical catalogue plus the `Claim` extension this file declares.

`policy.effective-tier-resolution` (File 06 §4) effective-tier resolution, §5 approval flows, §6 touched-resource matching, §7 permission floors and typed-confirmation, §11 leases, §12 approval-policy templates, and §14 contradiction-checking all apply to entity capabilities. File 09 specifies the required `permission_tier` and `permission_floor` per entity capability in §16; the policy machinery is unchanged.

### 2.4 With File 07 (Tool Surfaces and Capability Loading)

Entity capabilities appear in tool surfaces per the standard composition algorithm (`surface.visibility-composition-resolution-algorithm`, File 07 §9). The `Inspector` lens (`surface.inspector-lens`, File 07 §12.4) surfaces the artifact, claim, evidence, observation, and provenance management surfaces. Subsystem `SubsystemSurfaceSpec` declarations (per `surface.subsystem-surface-spec`, File 07 §5) name entity capabilities (specifically the artifact-producing and observation-committing ones) in their `primary_capability_ids` or `borrowable_capability_ids` lists. File 09 does not introduce a parallel surface model.

### 2.5 With File 02 (Conversation, Intent, and Task) and File 03 (Routing and Dispatch)

`RunIntent.capability_families` (per `routing.run-intent`, File 03 §4.3) may name an `artifact-producing` or `evidence-gathering` family when routing identifies that intent. Artifacts produced inside a conversation are surfaced through the conversation's transcript-projection lens (per `intent.presentation`, File 02 §8) but live in the unified entity pool — moving an artifact between conversations is reference, not copy. Intent threads and tasks (`intent.intent-thread` (File 02 §5) and `intent.task` (File 02 §6)) may own one or more artifacts; the artifact entity records its `producing_task_id` and `producing_intent_thread_id` for cross-referencing.

### 2.6 With Cross-Cutting Substrate

Entity events emit through the canonical event bus per `run.event-stream` (File 04 §23.2) with the standard envelope (`conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`). Settings are read through the canonical settings system (per `core.settings-system`, File 01 §6.8). Typed errors flow through the typed-error envelope (per `core.typed-errors`, File 01 §6.9). State awareness (per `core.world-model`, File 01 §6.7) consumes the artifact and claim catalogues for state-aware capability availability.

### 2.7 Boundary

File 09 is the entity and provenance-query layer. It owns no storage schema, no event-bus implementation, no UI rendering, no capability execution mechanics, and no block content carriage. Storage of entity records is File 20's concern; presentation of entity surfaces is File 37 and File 38's concern; the actual execution of entity-mutating capability calls is `run.call-pipeline` (File 04 §8.2)'s pipeline.

## 3. `Artifact`

Anchor: `artifact.artifact`

### 3.1 Definition

An `Artifact` is a durable, identifiable, versionable user-visible product of the system. It is the entity that persists across edits, supersessions, validations, and reviews while one or more `Artifact`-kind blocks carry its content per version.

An artifact does not need to be a single file. It may be an inline object, one file, multiple files, a composed bundle, a generated report, a dynamic product rendered through a sandbox or surface, or a non-visual reusable object. File materialization is one way an artifact appears in the local workspace; it is not the artifact's identity.

An `Artifact`:

- has stable identity (`artifact_id`); this identity survives version changes, edits, retitling, scope promotion, and review-state changes
- carries a typed `ArtifactKind` (§4) drawn from the closed canonical catalogue plus the `Custom { namespace, name }` extension
- has a default/latest version pointer for non-branch-specific reads, while active surfaces resolve the effective version through the active `ContextVersion`
- accumulates an ordered version chain reachable through the `supersedes` edge closure starting from the selected version block
- has a producing context — `producing_run_id`, `producing_task_id`, `producing_intent_thread_id`, `producing_conversation_id`, `producing_workspace_id` — captured at first-version commit
- carries a declared `MaterializationPolicy` and, per version, a `materialized_paths` list (§10)
- carries review and validation policy defaults; effective review, lifecycle, and validation state are derived per artifact version and per `ContextVersion` (§5)
- is `scope`-bound (per `block.block-scope`, File 08 §11): an artifact is visible to surfaces and addressable within its scope; cross-scope visibility uses the `promotes_scope_of` / `scope_projection_of` edges from `block.canonical-edge-kinds` (File 08 §5.2)

An `Artifact` is not:

- a `Block` — the block is the version's content carrier; the artifact is the cross-version identity. A trivial single-version artifact still has an entity record; the cost is one row.
- a workspace file — workspace files are one materialization shape (per `MaterializationPolicy: InWorkspace`); the artifact identity does not require disk materialization and may span multiple files or no files.
- a transcript entry — transcripts may reference artifacts as children of `MessageAssistant` blocks, but the artifact identity is independent of the transcript.
- a UI element — the same artifact may be rendered in a conversation card, an inspector pane, a gallery thumbnail, a comparison board, or an artifact-specific viewer without changing the artifact.
- a stored projection — the artifact entity is the source of truth for its identity and its cross-version metadata. Materialized paths, retrieval indices, and surface projections are derived.

### 3.2 Required Fields

Every `Artifact` entity record carries at minimum:

- `artifact_id` — globally stable identifier; assigned at first version commit; never reused, never reassigned, never mutated
- `artifact_kind` — typed `ArtifactKind` (§4); declared at creation; immutable
- `title` — short user-visible title; may be edited (edits create a new sibling artifact-version block whose description and inline metadata reflect the new title; the entity's denormalized title field updates atomically with the new version)
- `description` — short user-visible description (distinct from the per-version block-level description per `block.block-description` (File 08 §10)); summarizes what the artifact is across versions
- `current_version_block_id` — default/latest `block_id` of the artifact version for non-branch-specific reads; branch-aware surfaces resolve the current version through the active `ContextVersion`
- `producing_run_id` — `run_id` of the run under which the first version was committed; null when the artifact was created outside a run (manual import, inspector apply outside a run)
- `producing_task_id` — `task_id` of the task that owned the producing run, if any; null otherwise
- `producing_intent_thread_id` — `intent_thread_id` of the producing run's primary intent thread, if any; null when committed outside a conversation
- `producing_conversation_id` — `conversation_id` of the producing run's conversation, if any; null otherwise
- `producing_workspace_id` — workspace id when the artifact materialized into a workspace; null when materialization is `None` or external
- `materialization_policy` — closed enum value (§10); declared at creation; mutable only through the `artifact.update_materialization_policy` capability
- `scope` — broadest visibility scope (per `block.block-scope`, File 08 §11); declared at creation; mutable only through the `artifact.promote_scope` capability (which creates a typed promotion record per `block.canonical-edge-kinds` (File 08 §5.2) `promotes_scope_of` rather than mutating the original)
- `tags` — optional list of typed tags (`agent-invokable-output`, `user-published`, `validated-required`, `archival`, plus user-extensible tags)
- `created_at` — full-granularity timestamp of first-version commit; immutable
- `last_version_committed_at` — denormalized timestamp of the latest version's commit; updated atomically with each version commit
- `entity_schema_version` — version of the entity record shape, so File 20 can normalize supported earlier shapes during registration

The entity record's `current_version_block_id` is a default/latest projection pointer updated through `artifact.commit_version` for non-branch-specific reads. Branch-specific currentness lives in the version graph projection. The denormalized entity-row fields — `current_version_block_id`, `last_version_committed_at`, and the denormalized `title` — are creation-time seed values thereafter refreshed at each commit; their live authoritative value is always the projection over the version chain and the version graph, which the entity row denormalizes for O(1) non-branch-specific reads, never the reverse. Every pointer update is recorded as a typed event (§20) and ledgered per `run.execution-ledger` (File 04 §23.1). All other fields above are either immutable or carry their own specific mutation capability.

### 3.3 Boundary

The entity record defines cross-version identity and review/lifecycle/materialization metadata. The version's content is owned by the `Artifact`-kind block (per `block.kind-catalogue`, File 08 §3.1). The version chain lives in the block graph. The execution ledger records the policy decision and capability execution that produced each version commit. File 11 records which version is active in each `ContextVersion`. None of those layers may invent new entity semantics; they consume what this file defines.

The entity record is wire-stable through `entity_schema_version`. ATLAS3 is in initial development; no third-party persisted entity records exist yet, so no migration framework is required at present (per project constraints). When external records begin to persist (artifacts shared across installations, exported and re-imported), normalization-on-load applies at that boundary.

## 4. `ArtifactKind`

Anchor: `artifact.artifact-kind`

### 4.1 Closed Canonical Catalogue

Every artifact declares its `artifact_kind` at creation. The canonical closed catalogue:

**Textual and structured documents:**

- `Document` — a textual document: markdown, plain text, structured rich-text, prose report
- `Note` — a short note or memo distinct from a full document; the entity layer is minimal
- `Report` — a structured report combining text, charts, citations; typically composed over child blocks
- `Lesson` — a Teacher-surface lesson with sections, examples, exercises (per Teacher surface spec)
- `Curriculum` — a Teacher-surface ordered lesson sequence with prerequisites and progress affordances
- `Quiz` — an assessment artifact with prompts, answer keys, grading policy, and feedback rules
- `ExerciseSet` — a set of practice tasks with expected outputs or solution guidance
- `FlashcardSet` — a spaced-repetition or study-card collection with fronts, backs, tags, and optional media
- `Rubric` — an evaluation rubric with criteria, levels, scoring rules, and feedback guidance

**Code and patches:**

- `CodePatch` — a structured patch over one or more files; carries diff content and target paths
- `Macro` — a recorded action sequence (GUI, web, or system-operation) replayable via the owning surface's macro executor; the owning surface's format defines the step vocabulary (File 34 §6 owns the reusable-unit contract)

**Data and tables:**

- `Dataset` — structured tabular or columnar data (per Data Processor surface spec); may reference external storage for large datasets
- `Chart` — a generated chart, plot, or visualization; typically inline data plus a renderer hint
- `Table` — structured tabular data presented inline; small-row count distinguishes from `Dataset`

**Media:**

- `Image` — a generated or captured image
- `Audio` — a generated or captured audio clip
- `Video` — a generated or captured video clip
- `ScreenshotSeries` — an ordered set of screenshots with optional annotations (typically GUI Control or Web surface output)

**Web and browser:**

- `BrowserExtract` — a structured extract from one or more web pages (per Web surface spec); typically includes text, structured sections, citations
- `WebDocument` — a self-contained HTML/CSS/JS document the user may want to keep, embed, or share

**Notebooks and computational artifacts:**

- `Notebook` — a notebook-style ordered set of cells (per Data Processor surface spec): SQL, transform, chart, code, text, AI cells
- `Diagram` — a structured diagram (Mermaid, Tldraw, hand-drawn, or rendered): system architecture, flowchart, whiteboard scene
- `InstructionFragment` — reusable instruction-source content authored by user or agent; persisted as artifact for cross-conversation reuse

**Workflow and reuse:**

- `WorkflowTemplate` — a reusable workflow declaration (per File 34)
- `Adapter` — a registered adapter capability authored by user or agent (per `capability.adapter-capabilities`, File 05 §17.4)
- `Validator` — a registered validation rule authored by user or agent (typically pairs with the QC subsystem)

**Composed:**

- `ArtifactBundle` — a `Composed`-content artifact whose children are themselves artifacts (e.g., a project export containing code + report + chart); used for bundle export, gallery presentation, and reuse

**Extension:**

- `Custom { namespace, name }` — specialized artifact kind registered by a subsystem, surface, plugin, or user-defined extension through the proposal-first registration mechanism (per `capability.runtime-mutation`, File 05 §16.2). The `namespace` matches the canonical sourcing taxonomy (per `capability.capability-source`, File 05 §9.1). The `name` is the kind id within that namespace.

The closed catalogue is canonical for cross-cutting reasoning. The `Custom` extension is canonical for specialization. Every artifact at runtime belongs to exactly one of these — no artifact ever has an unparseable kind.

### 4.2 Kind Composition Rules

The catalogue is not free-form. The following composition rules apply:

- `ArtifactBundle` artifacts are always `Composed`; their content version block resolves to a `Composed` block per `block.block-content` (File 08 §4) whose children are other artifact-version blocks
- `Dataset` artifacts whose row count or byte size exceeds the inline-size threshold (per `block.inline-size-threshold`, File 08 §4.2) must use `External` content; small datasets may use `Inline`
- `Image`, `Audio`, `Video`, `ScreenshotSeries` artifacts must use `External` content (per the file-management spec's image/audio/video size considerations); inline payloads for these kinds are an Explicit Rejection (§21)
- `CodePatch` artifacts may use `Inline` for small patches; large patches default to `External` and carry the diff format hint in metadata
- `Macro` artifacts use `Inline` content for the macro DSL (per the owning surface's macro format — GUI Control, Web, or System Agent) regardless of size, because macros are inspected and edited as structured records
- `WorkflowTemplate`, `Adapter`, `Validator`, `InstructionFragment` artifacts are typically `Inline` for inspectability; they may use `External` only when the payload genuinely exceeds practical inline storage
- `Custom` artifacts inherit their composition rules from the kind's registration declaration

These rules are enforced at version-commit time by the artifact commit validator.

### 4.3 Custom Extension

A `Custom { namespace, name }` artifact kind is registered by a subsystem, plugin, or user-defined extension through a capability call (matching `capability.runtime-mutation` (File 05 §16.2) proposal-first registration). The registration declares:

- `allowed_content_variants` — which `BlockContent` variants the kind permits at the version-block level (`Inline`, `External`, `Composed`)
- `default_materialization_policy` — initial `MaterializationPolicy` for new artifacts of this kind
- `default_review_state` — initial `ReviewState`
- `default_validation_required` — whether validation runs by default before the artifact moves out of `Draft`
- `description` — human-readable description shown in the inspector and surface catalogues
- `surface_renderer_hint` — typed hint for the UI's renderer-selection algorithm (interactive-sandbox runtime tag, type-specific-renderer name, or `None` for generic rendering)
- `default_edges` — the canonical edges (per `block.canonical-edge-kinds`, File 08 §5.2) artifacts of this kind typically participate in (e.g., a custom audio-narration kind might default to `consolidates` edges from underlying transcript blocks)

Registered custom kinds persist in the registry (`capability.registered-capability`, File 05 §10) under the same registered-state envelope used for capabilities and follow the same source-trust narrowing rules (`policy.source-approval-flow`, File 06 §9). A custom kind cannot violate the canonical composition rules above; if its declaration permits a structurally invalid combination, the registration is rejected.

### 4.4 Boundary

The artifact-kind catalogue defines what categories of artifact the system reasons about. It does not define how those kinds are rendered, stored, or retrieved. UI, storage, and retrieval layers consume the catalogue; they do not extend it (only the registered Custom extension does).

## 5. Artifact Lifecycle and States

Anchor: `artifact.artifact-lifecycle-states`

### 5.1 `ArtifactLifecycle`

Anchor: `artifact.artifact-lifecycle`

`ArtifactLifecycle` names the runtime view-state of an artifact version within a particular `ContextVersion`. The artifact's effective lifecycle is the projection of the version selected by that context; entity-axis `Archived` and `Discarded` states mask this version-axis projection (§5.4). The closed canonical states:

- `Draft` — the artifact has at least one committed version but has not been accepted by the user or the agent as ready; surface displays mark it as in-progress; retrieval may deprioritize draft artifacts
- `Active` — the artifact's current version is the accepted, current output; default state for artifacts whose review process does not gate them or whose first version was committed with `auto_accept_first_version: true`
- `Validated` — the artifact's current version has at least one `Validation` block linked via `validated_by` whose `ValidationOutcome` is `Passed` (per §14); when validation requirements specify multiple checks, all required checks must pass
- `Superseded` — this version has been superseded by a sibling version through `supersedes`; the prior version remains in the block pool, addressable through the version chain
- `Archived` — the artifact is preserved but moved out of default surface views; archived artifacts remain inspectable, retrievable, and exportable but do not surface in primary palette or panel views by default
- `Discarded` — the artifact's current version has been explicitly discarded by user or by policy; the entity record remains for audit; the discarded version remains in the block pool unless hard-deleted

### 5.2 `ReviewState`

Anchor: `artifact.review-state`

`ReviewState` names the user-or-agent reviewer's explicit acceptance of the artifact version:

- `Unreviewed` — default for new versions; surface displays mark it as pending review
- `AcceptedByUser` — the user has explicitly accepted this version through the `artifact.set_review_state` capability or the equivalent UI affordance
- `AcceptedByAgent` — an agent (typically a reviewer subagent) has accepted this version; weaker than user acceptance and does not lift typed-confirmation requirements on downstream actions
- `Rejected` — explicitly rejected; the version remains in the pool but is not the artifact's current version unless explicitly restored
- `NeedsRevision` — explicitly marked as requiring further work; agent may produce a new version superseding this one

### 5.3 `ValidationState`

`ValidationState` names the artifact version's validation outcome:

- `NotValidated` — no validation has been run for this version
- `PendingValidation` — one or more required validations have not yet committed a `Validation` block (a run may have been requested and be in progress, or a required validation is simply missing); the meaning is the §14.2 derivation's missing-required case
- `Passed` — the §14.2 `Passed` rung applies: no required validation is `Failed`, `Inconclusive`, or missing, and at least one linked `Validation` block carries `ValidationOutcome: Passed`
- `Failed` — at least one required `Validation` block carries `ValidationOutcome: Failed`
- `NeedsReview` — at least one required `Validation` block carries `ValidationOutcome: Inconclusive` and no required validation is `Failed` (per the §14.2 derivation); a model-mediated validator that declines to validate commits that decline as an `Inconclusive` outcome carrying its `inconclusive_reason` (§14.1), never as a fourth outcome

### 5.4 Per-Version vs Per-Entity Derivation

Anchor: `artifact.per-version-vs-per-entity-derivation`

`ArtifactLifecycle`, `ReviewState`, and `ValidationState` are **derived per-`ContextVersion` from the version-graph action log, from the `validated_by` edges on each version, and from the entity transition log** (the entity record's own review, lifecycle, and materialization transition records, §5.5), never stored on the entity record. The same artifact may be `Active` in one version and `Superseded` in another without any entity-record mutation. Entity-axis state takes precedence over the version-axis projection: when the entity is `Archived` or `Discarded` (§5.1), that state masks the version-selected `ArtifactLifecycle` in the effective projection — the version chain and its per-version states remain intact and inspectable, but the effective lifecycle a surface renders is `Archived` or `Discarded`.

Storage may cache derived state in a materialized view (per `block.what-is-computed`, File 08 §13.2's pattern) for O(1) reads, but the materialized view is rebuildable from the source action log. The entity record's denormalized `current_version_block_id` is only the default/latest pointer; branch-aware surfaces read the active version from the version graph projection.

### 5.5 Lifecycle Transition Rules

The lifecycle state transitions are explicit and deterministic:

- new artifact, first version committed → `Draft` (or `Active` if creation-time setting `auto_accept_first_version: true`)
- user/agent calls `artifact.set_review_state(AcceptedByUser)` → entity's per-version review state transitions; if no validation is required, lifecycle becomes `Active`; if validation is required and passes, becomes `Validated`; if validation is required but has not yet passed, lifecycle remains `Draft` while `ValidationState` is `PendingValidation` (§14.2), until a `Passed` validation commits
- a `Validation` block with `Passed` outcome commits and links via `validated_by` → if review state is `AcceptedByUser` or `AcceptedByAgent`, lifecycle becomes `Validated`
- the entity's `current_version_block_id` updates to a new sibling block (via `artifact.commit_version`) → the prior version's lifecycle becomes `Superseded`
- user/agent calls `artifact.archive` → lifecycle becomes `Archived`
- user/agent calls `artifact.discard` → lifecycle becomes `Discarded`; the version remains until hard-deleted
- user/agent calls `artifact.restore` → lifecycle returns to the appropriate prior state (`Active`, `Validated`, or `Draft`) per the action log

No time-based transition is permitted. No auto-archive-after-N-days rule lives at this layer (per File 01 constraint: never use time-based conditions unless unavoidable). Retention policies may invoke `archive` as an explicit operation driven by their own logic, but the entity layer enforces no implicit decay.

### 5.6 Boundary

Lifecycle, review, and validation are view-state concerns owned by the version graph plus the entity record's transition log. This file defines the state set, the derivation rules, and the transition rules; the version-graph spec owns the action log and the materialized view that tracks state per version.

## 6. `ArtifactVersion`

Anchor: `artifact.artifact-version`

### 6.1 Definition

An `ArtifactVersion` is the durable per-version snapshot of an artifact. Every version is an `Artifact`-kind block per `block.kind-catalogue` (File 08 §3.1); the version-block carries the content per `block.block-content` (File 08 §4) and the per-block fields per `block.block` (File 08 §2.2). The entity layer adds a per-version metadata record where the version requires fields the block does not natively carry (validation report reference, materialization paths, derivation summary).

An `ArtifactVersion` is not:

- a separate block kind from the canonical `Artifact` kind — every version is an `Artifact`-kind block
- mutable — like every block, the version is immutable; observable changes commit new sibling blocks linked by `supersedes`
- decoupled from its content — the version IS the block; the entity record points to it but does not duplicate content

### 6.2 Required Fields

Every `ArtifactVersion` metadata record carries at minimum (in addition to the canonical block fields the version-block already carries per `block.block` (File 08 §2.2)):

- `version_id` — for cross-spec reference, the same value as the version-block's `block_id`
- `artifact_id` — the owning entity's `artifact_id`
- `version_number` — monotonically increasing integer per artifact; assigned at commit; never reused
- `parent_version_id` — the prior version's `version_id` (i.e., the target of the `supersedes` edge); null for the first version
- `derivation_summary` — short structured natural-language description of what changed from the parent version; emitted by the producer at commit time, fixed thereafter; null for the first version
- `produced_by_run_id` — the `run_id` under which the version-block was committed; null only for inspector-applied versions committed outside a run
- `produced_by_node_id` — the DAG node id (per `run.event-stream`, File 04 §23.2 envelope) that produced the version; null when production was not DAG-structured
- `produced_by_capability_id` — the capability id (per `capability.id`, File 05 §13.1) that committed the version-block; for example, `file.create`, `file.edit`, `data.notebook.export`, `teacher.lesson.compose`
- `materialized_paths` — list of paths where the version's content is materialized (empty when `MaterializationPolicy: None`)
- `validation_report_id` — the `block_id` of the most recent linked `Validation` block, when one exists; null until the first validation runs
- `metadata` — typed extension map for kind-specific fields (chart-specific axis configuration, dataset-specific schema, macro-specific replay parameters); declared per artifact kind

The version metadata record is fixed at commit; observable changes commit a new version per §5.5's `current_version_block_id` update flow.

### 6.3 Version Creation

Anchor: `artifact.version-creation`

A new `ArtifactVersion` is created when one of the following capability invocations commits a new `Artifact`-kind block:

- `artifact.create` — first version of a new artifact; assigns `artifact_id`, `version_number = 1`, `parent_version_id = null`
- `artifact.commit_version` — subsequent versions; takes the new content (Inline / External / Composed), the artifact_id, an optional derivation summary, and optional title, description, and tags updates; commits the new `Artifact`-kind block, sets `parent_version_id` to the version current in the committing `ContextVersion` (the branch-active current per `version.artifact-version-chains` (File 11 §13.3), which for non-branch-specific commits is the entity's `current_version_block_id`), advances `version_number`, updates the entity's `current_version_block_id`
- `file.edit` or `file.create` on a path that maps to an existing `Artifact: InWorkspace` materialization — the file-management subsystem (per File 08's file-block contract and the Coder surface's code-editing contract, File 27 §6) commits a sibling `Artifact`-kind block as the new version; the entity record updates to point at the new version
- `artifact.merge` — produces a new version composed over two or more existing versions (typically for best-of-N selection or for explicit version merges); the new version's `parent_version_id` is set to one parent (the merge's principal parent), and additional parents are linked through `derives_from` edges per `block.canonical-edge-kinds` (File 08 §5.2)

Version commit boundaries match `block.commit-boundary-set` (File 08 §7.6) — `accepted assistant turn`, `capability completion`, `inspector apply`, `workflow node complete`, `import`, `consolidation`, `manual draft commit`, or a subsystem-internal boundary that the capability declares.

### 6.4 Boundary

Version creation is a capability concern; version content is a block concern; cross-version chronology is a version-graph concern. This file specifies the metadata record and the creation rules; File 20 realizes persistence and File 11 realizes chronology.

## 7. Artifact Materialization

Anchor: `artifact.artifact-materialization`

### 7.1 Definition

`Materialization` is the process by which an artifact version's content becomes addressable on the local filesystem or in external storage. Materialization is a separate concern from artifact identity: artifacts have identity whether materialized or not.

### 7.2 `MaterializationPolicy`

`MaterializationPolicy` is declared per artifact at creation and is a closed canonical enum:

- `InWorkspace` — the artifact version's content is written to a workspace path resolved by File 24's two-target model (`workspace.materialized-path-resolution`, File 24 §11.2): an artifact whose materialization is a principal user-facing file resolves to its **natural workspace-relative path** and is rewritten in place across versions; an artifact with no natural user-facing location resolves to the **Atlas-internal** path computed from `(workspace_id, artifact_id, artifact_kind, version_id)` (the canonical default places it under `<workspace>/.atlas/artifacts/<artifact_id>/<version_id>/` with a kind-typed leaf filename). Default for `Document`, `CodePatch`, `Notebook`, `Image`, `Audio`, `Video`, `Chart` artifact kinds whose containing scope is workspace or narrower.
- `ExternalRef` — the artifact version's content lives in external storage (cloud bucket, content-addressed external store, MCP-server-hosted resource). The version-block uses `BlockContent::External` with the appropriate storage_ref. Materialization is the act of binding the external reference; no local file is written by default. The user may opt to cache an external artifact locally; cache state is per-installation and does not change the artifact's identity.
- `None` — the artifact has no materialization beyond the version-block itself. Used for `Note`, `InstructionFragment`, `Validator`, `Adapter` artifacts whose content is fully consumed inline. The version-block's `BlockContent::Inline` payload is the artifact.

The `MaterializationPolicy` is part of the entity record. Changing it requires the `artifact.update_materialization_policy` capability and creates an audit-visible event (§20). Changes apply to new versions; existing versions retain their original policy.

### 7.3 Materialization Mechanics

For `InWorkspace`:

- materialization happens at the same boundary the version-block commits — atomically with the block commit; each `InWorkspace` materialization emits an `ArtifactMaterialized` event (§20) carrying the version and the resolved `materialized_paths`
- live-partial-write capabilities (per `run.streaming-partial-execution`, File 04 §12) stage the file under a temp path during streaming and atomic-rename at the version-commit boundary; if the streaming run is cancelled, the staged file is deleted before the artifact version commits, and no `ArtifactVersion` is created
- the `materialized_paths` list on the version metadata records the resolved paths; for multi-file artifacts (e.g., a `Notebook` with auxiliary assets), the list carries every path materialized by this version
- subsequent version commits differ by target: an **Atlas-internal** artifact materializes to a new version-keyed path (computed from the new `version_id`) and the prior version's materialized paths remain on disk by default (subject to retention policy); a **natural user-facing** artifact is rewritten in place at its natural path, so version-keyed on-disk retention applies only to the Atlas-internal target (the prior on-disk content of a natural path is superseded, while every version's block remains in the pool). In both cases the entity record points at the new version's `materialized_paths`.

For `ExternalRef`:

- the version-block's `BlockContent::External { storage_ref, size_bytes, content_type, external_content_hash }` carries the binding
- no local file is written at version commit by default; the user may invoke `artifact.materialize_locally` to fetch a local cache
- the `materialized_paths` list is empty unless local cache is materialized

For `None`:

- no materialization step runs; `materialized_paths` is empty
- the version-block carries the full content inline (or as a composed structure)

### 7.4 Materialized Paths Provenance

Anchor: `artifact.materialized-paths-provenance`

A `materialized_paths` entry carries:

- `workspace_id` — workspace whose root resolves the path
- `relative_path` — canonical path relative to that workspace root
- `resolved_absolute_path` — optional runtime projection for local display; not canonical identity
- `is_principal` — true for the single primary file of the artifact (the user's default-open target); false for auxiliary files
- `content_role` — typed enum: `Primary`, `Asset`, `Sidecar`, `Companion`; used by surfaces to render the artifact with structure rather than as a flat file list
- `materialized_at` — full-granularity timestamp at materialization
- `content_hash` — the content hash of the file content at materialization time, computed under the version-block's declared canonical encoding (per `block.content-hash` (File 08 §4.5); the hash algorithm is a declared property, SHA-256 by canonical default per §7.6, not fixed at this field); allows freshness checking against the version-block's `content_hash`, and a mismatch indicates external modification — handled per the disk→block sync loop (`workspace.disk-sync-loop`, File 24 §12)
- `collision_policy` — the closed collision-policy value resolution recorded for the path (per `workspace.materialized-path-resolution` (File 24 §11.3)): `ExplicitPathRequiresDecision`, `GeneratedPathDeterministicSuffix`, `OverwriteAllowedByPolicy`, or `VersionedPathTemplate`

Workspace-root relinking is explicit: if a workspace directory is moved, updating the workspace root re-resolves all relative materialized paths. If individual files are moved or deleted outside ATLAS, the system reports unresolved materializations and offers relink or re-materialize actions; it does not pretend to track arbitrary filesystem moves.

### 7.5 Disk→Entity Sync

Anchor: `artifact.disk-entity-sync`

External modifications to materialized files are detected by the filesystem watcher per the disk→substrate sync loop (`workspace.disk-sync-loop`, File 24 §12). When an external edit is detected:

- a new sibling `Artifact`-kind block is committed as the new version (per `block.block`, File 08 §2.2 producer typed `UserMessage` when the edit was user-driven, or `Subsystem { subsystem_id: filesystem_watcher, reason: "external_edit" }` when the source is not directly attributable)
- the entity record's `current_version_block_id` updates atomically
- a `ArtifactExternallyEdited` event emits (§20)
- the new version's `derivation_summary` is auto-populated with a short description identifying the file system as the source

### 7.6 Boundary

Materialization mechanics for the workspace tree are owned by File 24 and the file-management subsystem (per `block.streaming-commit-boundary`, File 08 §7). This file specifies the policy enum, the path-on-version metadata, and the disk→entity sync contract. Implementation choices (path templates, hash algorithms beyond SHA-256, materialization atomicity primitives, watcher backends) belong to those specs.

## 8. Artifact Tombstones

Anchor: `artifact.artifact-tombstones`

### 8.1 Hard Delete

Hard deletion of an artifact version follows `block.hard-delete` (File 08 §6.6)'s hard-delete contract for the underlying `Artifact`-kind block. File 09 specifies the entity-record consequences:

- `artifact.hard_delete_version(version_id)` is a `UserApproval`-tier capability with `permission_floor: Denied` and a policy template that requires denied-override via typed confirmation. Discarded or only-version state may change preview text and warnings, but never lowers the floor.
- the version-block is hard-deleted per `block.hard-delete` (File 08 §6.6) (a live composed parent follows §6.6's disposition-bound preservation plan — currently fail-closed unsupported; tombstone retains identity)
- the `ArtifactVersion` metadata record transitions to a tombstone shape (below); the row is retained
- if the deleted version was the artifact's `current_version_block_id`, the entity transitions to the most recent non-deleted version; if no non-deleted version remains, the entity becomes orphaned and is marked for explicit user resolution (rename, hard-delete the entity itself, or commit a fresh version)
- `artifact.hard_delete_entity(artifact_id)` is a separate capability with `permission_floor: Denied` requiring typed-confirmation; it tombstones every version and the entity record

### 8.2 Tombstone Fields

Anchor: `artifact.tombstone-fields`

A version tombstone retains:

- `version_id` — preserved for provenance lookup
- `artifact_id` — preserved
- `version_number` — preserved
- `parent_version_id` — preserved (so lineage chains continue to resolve)
- `produced_by_run_id`, `produced_by_node_id`, `produced_by_capability_id` — preserved
- `deleted_at` — timestamp of hard delete
- `deleted_by` — actor identity (user, agent, automation, subsystem)
- `deletion_reason` — typed enum: `UserRequested`, `RetentionPolicy`, `CredentialExpungement`, `SourceUnavailable`, `MaintenanceCleanup`, plus `Custom { code, description }`
- `safe_description` — the version's `description` field (per `block.block-description`, File 08 §10) at deletion time, retained for inspection; sensitive content is redacted per the version's `default_sensitivity`

An entity tombstone retains the same set of entity-record fields at deletion time, with content fields redacted to safe descriptions.

### 8.3 Lineage Preservation

Provenance queries (§15) continue to resolve tombstoned versions:

- `provenance.lineage(target)` returns the version chain including tombstoned versions, with each tombstoned link rendered as a typed `Tombstoned` placeholder
- `provenance.contributing_runs(target)` resolves to the producing runs of every version including tombstoned ones
- `provenance.replay_trace(target)` returns the ledger entries that produced the tombstoned version, with tombstoned content references resolving to redacted-description placeholders

Hard delete is the canonical mechanism for honoring user storage-reclamation requests, credential expungement, and right-to-erasure requirements (per `core.non-destructive-by-default`, File 01 §7.13). It is never automatic. Tombstone retention is the safe default; explicit policy-governed pruning of tombstones is itself a typed-confirmation user operation.

## 9. `Claim`

Anchor: `artifact.claim`

### 9.1 Definition

A `Claim` is a typed, identified factual assertion the system or an agent has made or proposes to make. Claims make load-bearing assertions inspectable, supersedable, and explicitly tied to evidence.

Claims are for source-dependent or load-bearing assertions, not for forcing every task into a neat evidence chain. Web research, knowledge-heavy reports, validations, policy decisions, and reusable factual outputs benefit most. Ordinary conversational text remains message content unless explicit publication or opt-in extraction promotes an assertion to a claim.

A `Claim` block is a canonical extension to `block.kind-catalogue` (File 08 §3.1)'s `BlockKind` catalogue declared by this file. The extension shape:

- block kind: `Claim` (registered as a canonical baseline, not as a `Custom` namespaced extension; the canonical catalogue evolves through canonical-spec updates per `block.explicit-rejections` (File 08 §15))
- `allowed_content_variants`: `Inline` (the canonical case carrying the claim text and structured metadata) or `Composed` (when the claim is composed over sub-claims for compound assertions)
- `default_sensitivity`: `Public`; overridden to `Sensitive` when the claim originates from user-private context per the producer's `data_sensitivity` declaration (`capability.permission-policy-fields`, File 05 §3.5)
- `transcript_anchorable`: false; `Claim` blocks may be referenced from transcripts but do not themselves anchor transcript messages
- `permitted_parent_kinds`: `Any` (claims may be produced under any logical parent — typically `MessageAssistant` for agent-produced claims, `MessageUser` for user-asserted claims, or `WorkflowNode` for workflow-produced claims)
- `permitted_child_kinds`: `Claim`, `SourceExcerpt`, `Evidence`, `Citation`, `Observation` (when the claim is `Composed`)
- `default_edges`: `cites` (claims typically link to evidence), `references` (claims may reference prior claims or content blocks), `responds_to` (claims may respond to user questions), `supersedes` (claims may supersede prior claims)

A `Claim` is not:

- a fact — the claim is the assertion that something is the case; whether the assertion is supported is a separate matter resolved through evidence linking
- a conversation message — a `MessageAssistant` block may contain text that asserts something; the assertion only becomes a `Claim` entity when explicitly published via `claim.publish` or automatically extracted under settings opt-in
- a memory entry — `Memory` blocks (per `block.kind-catalogue`, File 08 §3.1) may consolidate claims into long-term knowledge; the memory mechanics are File 14's concern
- a knowledge-base entry — File 12 defines knowledge entries; they may reference claims through `cites` or `references`, but a claim is not by default a knowledge entry

### 9.2 Required Fields

Every `Claim` block carries at minimum (in addition to the canonical block fields per `block.block` (File 08 §2.2)):

- `claim_id` — globally stable identifier; the same value as the block's `block_id`
- `claim_text` — the assertion text (UTF-8); the canonical content stored as `Inline { text }` in the block's `BlockContent`
- `claim_kind` — typed `ClaimKind` (§9.3)
- `confidence_class` — typed `ClaimConfidenceClass` (§9.5); declared by the producer
- `confidence_score` — optional ranking score: a fixed-point integer in [0, 1000] milli-units (the canonical encoding carries no float, `core.canonical-encoding` §6.15); declared by the producer when meaningful; used for ranking, never for policy. When committed on the claim block, it is deterministically encoded and hash-protected like any committed field; changing it later requires a new block or a separate projection fact, never in-place mutation.
- `scope` — broadest visibility scope (per `block.block-scope`, File 08 §11)
- `anchor` — optional typed `ClaimAnchor` (§9.6) pointing to a source block plus an optional span
- `claim_schema_version` — version of the claim-block extension shape

Effective `ClaimStatus`, withdrawal, supersession, and explicit override reason are projection/action-log facts, not mutable claim-block fields. The claim block carries immutable assertion content; lifecycle interpretation is derived from evidence links and status records.

### 9.3 `ClaimKind`

`ClaimKind` is closed canonical with the standard `Custom { namespace, name }` extension:

- `Factual` — asserts that something is empirically the case ("the build passes on commit abc", "this file has 1234 lines")
- `Causal` — asserts a causal relationship ("removing this guard caused the test failure")
- `Conditional` — asserts a conditional ("if X then Y", "this works on macOS only")
- `Recommendation` — asserts a recommended action or choice ("we should switch to library X")
- `Prediction` — asserts a future or counterfactual state ("running the migration will take ~10 minutes")
- `Definition` — asserts a definitional equivalence or naming ("by `widget` we mean an instance of the Widget class")
- `Identity` — asserts identity or non-identity ("commit a and commit b have the same effect", "file X is unrelated to file Y")
- `Summary` — asserts that a longer body of evidence summarizes to a given claim
- `Negation` — asserts that something is not the case
- `Custom { namespace, name }` — specialized kind

### 9.4 `ClaimStatus`

Anchor: `artifact.claim-status`

`ClaimStatus` is closed canonical:

- `Candidate` — newly created; no evidence has been evaluated; default for first publication
- `Supported` — at least one `Supports` or `Corroborates` evidence link is active above the configured threshold and no stronger refuting evidence is active
- `Contradicted` — at least one `Refutes` evidence link is active with confidence strictly greater than the strongest supporting link
- `Unresolved` — both supporting and refuting evidence is active with comparable confidence; explicit user resolution required
- `Superseded` — the claim has been replaced by a newer claim through a supersession projection record
- `Withdrawn` — the claim has been explicitly retracted by its author or by user through a withdrawal record

Status is **derived from the evidence-link set when not explicitly overridden**. The derivation rule:

1. If a withdrawal record exists → `Withdrawn`
2. If a supersession projection record exists → `Superseded`
3. Else compute support/refute aggregation per §11.4 confidence rules:
   - any `Refutes` link with confidence strictly greater than max(supporting confidence), treating absent support as below all confidence classes → `Contradicted`
   - any active `Supports` or `Corroborates` link with confidence above the `claim.evidence_threshold` setting and no refuting link of comparable confidence → `Supported`
   - both supporting and refuting links with comparable confidence → `Unresolved`
   - no active evidence links of meaningful confidence → `Candidate`
4. An explicit status override record created by `claim.update_status` overrides the derived value until superseded or withdrawn; the override reason and actor are recorded in the policy ledger.

### 9.5 `ClaimConfidenceClass`

`ClaimConfidenceClass` is the canonical policy-grade confidence enum (drawn from the cosight five-level model and the graphify three-level model, harmonized):

- `DirectlyObserved` — the claim describes something the system directly observed (a file read, a tool output, a postcondition validation). Highest policy-grade confidence; no further support required for routine use.
- `VerifiedExternal` — the claim is supported by external authoritative evidence (a cited paper, an official documentation page, a passing test); the evidence link must reference an external source
- `Inferred` — the claim is derived by reasoning from other supported claims; the evidence link must reference the premises
- `Plausible` — the claim is a reasonable conclusion from available context but not derived rigorously; appropriate for ordinary conversational answers
- `Speculative` — the claim is offered as a hypothesis or guess; surfaces should render with explicit speculative marking
- `Disputed` — the claim is asserted but with awareness of significant contradicting evidence; explicit acknowledgment of disagreement

The classes form a total order for aggregation and comparison: `DirectlyObserved` > `VerifiedExternal` > `Inferred` > `Plausible` > `Speculative`. `Disputed` is excluded from ordinal comparison — it marks awareness of contradicting evidence rather than a strength rung. Two links (or two claims) are **comparable** only when they share the same class; within a class, the optional `confidence_score` is a display and ranking tiebreak, never an ordinal promotion across classes. This is the single ordering both the §9.4 claim-status derivation and the §11.4 evidence aggregation consult.

`confidence_class` is the primary policy-grade signal: typed-confirmation requirements, automation gating, retrieval ranking weights, and validation pipeline routing read from this enum. The optional `confidence_score` fixed-point ranking value (milli-units, §6.15) supplements for ranking and comparison but is never the sole policy input.

### 9.6 `ClaimAnchor`

When a claim originates from content within a source block (typically a `MessageAssistant`), the `anchor` field captures the source:

- `source_block_id` — the originating block's id
- `source_span` — optional typed `SourceSpan` per §12.3 grammar; points to the character range, line range, byte range, or composed-child index within the source block
- `anchor_kind` — typed enum: `Authored` (the claim was published from text the producer wrote), `Extracted` (the claim was auto-extracted from existing text), `Annotated` (the claim was attached as commentary to existing content), `Derived` (the claim summarizes or derives from the source)

The anchor lets surfaces highlight the source span when displaying a claim and lets retrieval index the claim against its source location.

### 9.7 Claim Lifecycle

The claim block is immutable per File 08. Observable claim-content changes commit new sibling blocks linked by `supersedes`; status changes are projection records:

- editing `claim_text`, `claim_kind`, or `confidence_class` → new sibling claim block via `claim.publish` with `supersedes` edge to the prior
- updating `status` through derivation → no new block; the derivation is computed on read
- explicit `status` override (e.g., user marks `Unresolved`) → emits `ClaimStatusOverridden` and stores an override record with reason
- explicit `claim.withdraw` → commits a withdrawal record and emits `ClaimWithdrawn`; the claim block itself is unchanged, but every projection treats it as withdrawn

A withdrawn claim remains addressable for provenance queries but is excluded from retrieval, surface display, and evidence-link computation by default.

### 9.8 Boundary

Claims are blocks; their identity, content, and immutability follow File 08. This file adds the `Claim` canonical kind, the `ClaimStatus` derivation, the `ClaimConfidenceClass` policy-grade enum, and the anchor reference contract. Retrieval, ranking, surface presentation of claims, and memory consolidation of claims into long-term knowledge are downstream concerns.

## 10. Claim Extraction

Anchor: `artifact.claim-extraction`

### 10.1 Explicit Publication

`claim.publish(claim_text, claim_kind, confidence_class, anchor?, scope?, evidence_links?)` is the canonical capability for explicit claim publication. The capability:

- declares dynamic permission tier from scope, sensitivity, and downstream use: routine conversation/task/workspace claims are usually `WorkspaceWrite`; global, reusable, external-publication, automation-gating, policy, security, medical, legal, financial, high-impact, or user-configured sensitive claims escalate to `UserApproval` or stronger
- declares `replay_class`: `deterministic_replayable`
- declares `output_block_kinds`: `[Claim]`
- declares `touched_resources`: meta-resource declaration over the claim entity pool
- declares `concurrency`: `SelfParallel` (independent claim publications are parallel-safe)

Publication commits a new `Claim`-kind block per `block.commit-boundary-set` (File 08 §7.6)'s commit boundaries and creates the entity-record row.

### 10.2 Automatic Extraction

Automatic claim extraction is opt-in per scope (default off) and task-specific. It is strongest for web research, source-dependent reports, knowledge-base work, validation output, and other flows where cited assertions are valuable; it is not a default requirement for ordinary task execution. When enabled:

- a designated extractor model runs post-commit on accepted `MessageAssistant` blocks within the configured scope; the extractor's input is File-22-redacted content (per `security.secret-detection-redaction`, File 22 §7), never raw secret-bearing text
- candidate claims are identified by the extractor against a configured extraction model-request template (registry-managed per `policy.agent-exposure-policy-settings` (File 06 §16.4)'s pattern); each candidate is a tuple `(claim_text, claim_kind, confidence_class, source_span)`
- each candidate is committed as a `Claim` block via the same `claim.publish` capability, with derived status initially resolving to `Candidate` and the extracted source-span as anchor
- extracted claims take `max(Sensitive, source_block.effective_sensitivity)` until user review; extraction refuses outright on `Secret`-sensitivity source blocks (a claim is never extracted from secret-bearing content); the `claim.review` UI surfaces them for explicit acceptance or rejection

The settings governing extraction (per §19):

- `claim.auto_extraction.enabled` per scope (default false)
- `claim.auto_extraction.model_id` — the extractor model
- `claim.auto_extraction.model_request_template_id` — the extraction model-request template
- `claim.auto_extraction.minimum_confidence_class` — discard candidates below this class
- `claim.auto_extraction.review_required` — when true, extracted claims wait in `Candidate` status until explicit user review; when false, they proceed to derived status immediately

Automatic extraction always emits per-extraction `ClaimAutoExtracted` events with the extractor model identity, the model-request template id, the source block reference, and the extracted candidate.

### 10.3 Boundary

Extraction is a content-analysis operation that produces `Claim` blocks through the normal capability pipeline. The extractor model selection, model-request template registration, and confidence-threshold tuning are settings concerns. The retrieval and memory subsystems may consume extracted claims as inputs, but those mechanics are owned by Files 12 and 14.

## 11. `Evidence`

Anchor: `artifact.evidence`

### 11.1 The `Evidence` Block Kind

`Evidence` is already canonical per `block.kind-catalogue` (File 08 §3.1): "a structured evidence record supporting a claim, an output, or an action; carries citation references and the typed claim it supports". File 09 specifies the content shape and the typed-edge metadata that make evidence chains queryable.

An `Evidence` block's content is structured `Inline` carrying:

- `evidence_kind` — typed enum: `DirectObservation` (the evidence is itself an `Observation` block or wraps one), `CitedSource` (the evidence is a `Citation` or `SourceExcerpt` block or wraps one), `ToolResult` (the evidence is a captured tool result, referenced by `witnesses` edge to a `ToolResult` block), `ValidationOutcome` (the evidence is a `Validation` block), `DerivedReasoning` (the evidence is a chain of reasoning blocks the producer captured)
- `summary` — short structured summary of what the evidence asserts and why it supports the claim
- `originating_run_id` — the run under which the evidence was committed
- `originating_capability_id` — the capability that produced the evidence

An `Evidence` block must reference at least one supporting block via `cites`, `witnesses`, or registered evidence-relation edges (per §11.3); an evidence block with no supporting references is an Explicit Rejection (§21) — `block.kind-composition-rules` (File 08 §3.3) already established this rule.

### 11.2 `EvidenceLink`

An `EvidenceLink` is the typed metadata attached to a directed edge between a `Claim` (or other supported target) and a supporting block (`Evidence`, `SourceExcerpt`, `Citation`, `Observation`, `Validation`, or any prior block the producer captures as evidence). The edge itself is one of `block.canonical-edge-kinds` (File 08 §5.2)'s canonical edges (`cites`, `witnesses`, `validated_by`) or a registered extension edge per §11.3. The edge is directed from the supported target to the supporting block: `supported_target_id` names the edge's `from_block` and `supporting_block_id` names the edge's `to_block` (per `block.canonical-edge-kinds`, File 08 §5.2) — a `Claim` that `cites` an `Evidence` block, for instance, is the `from_block` and the evidence is the `to_block`.

`EvidenceLink` carries on the edge metadata (per `block.block-edge-block-graph`, File 08 §5.1's edge `metadata` field):

- `relation` — typed `EvidenceRelation` (§11.3)
- `confidence_class` — typed `EvidenceConfidenceClass` (§11.4), independent of the claim's own confidence
- `confidence_score` — optional ranking score: a fixed-point integer in [0, 1000] milli-units (the canonical encoding carries no float, `core.canonical-encoding` §6.15); evidence-link metadata, not part of the edge's identity (§5.2 edge identity excludes metadata)
- `applies_to_span` — optional `SourceSpan` indicating which portion of the source block the evidence specifically supports (when the source block is large and the evidence only addresses a portion)
- `captured_at` — timestamp the link was committed
- `captured_by_run_id` — the run under which the link was committed
- `captured_by_capability_id` — the capability that committed the link
- `notes` — optional free-text rationale

### 11.3 `EvidenceRelation`

`EvidenceRelation` is closed canonical with the standard `Custom { namespace, name }` extension:

- `Supports` — the source block supports the target claim or artifact
- `WeakSupports` — the source block weakly supports the target (suggestive but not conclusive)
- `Refutes` — the source block contradicts the target
- `Contextualizes` — the source block provides context relevant to the target without directly supporting or refuting
- `Corroborates` — the source block independently confirms what another source already supports
- `Summarizes` — the source block is a summary of the target's underlying material
- `Derives` — the target was derived (transformed, computed, or inferred) from the source
- `Witnesses` — the source block was the observation that triggered the target (used for capability postconditions and stale-state revalidation per `run.call-pipeline` (File 04 §8.2))
- `IllustratesByExample` — the source block illustrates the target through a concrete example

Registered extension relations use the `Custom { namespace, name }` form, registered through the proposal-first capability mechanism (`capability.runtime-mutation`, File 05 §16.2). An extension relation declares its own confidence-aggregation semantics and its containment under the canonical relations (so retrieval and provenance queries continue to compose).

### 11.4 `EvidenceConfidenceClass`

`EvidenceConfidenceClass` reuses the `ClaimConfidenceClass` enum from §9.5 but applies to the strength of the supporting relation rather than to the assertion's grounding:

- `DirectlyObserved` — the link is grounded in a directly observed event captured by the system
- `VerifiedExternal` — the link references an external authoritative source the system has captured
- `Inferred` — the link is justified by reasoning over other linked evidence
- `Plausible` — the link is reasonable but not rigorously justified
- `Speculative` — the link is offered as a hypothesis
- `Disputed` — the link is offered with awareness of contradicting evidence

The optional `confidence_score` provides numerical ranking within the class.

**Support/refute aggregation** is the canonical rule the §9.4 claim-status derivation and the `provenance.contradiction_check` (§15.3) both consult. The **supporting set** of a target is exactly its active `Supports` and `Corroborates` links; a `WeakSupports` link contributes suggestive, sub-threshold support that surfaces alongside the target but never on its own raises it to `Supported`. Aggregation compares classes by the §9.5 total order: a `Refutes` link overrides support when its class is strictly greater than the greatest supporting class (absent support ranks below every class → `Contradicted`); support holds when the greatest supporting class is at or above the `claim.evidence_threshold` setting and no refuting link is of comparable class → `Supported`; a supporting and a refuting link of comparable class → `Unresolved`. `confidence_score` breaks ties only within one class for display and ranking; it is never a cross-class promotion or a policy input.

### 11.5 Evidence Set Closure

The `EvidenceSet` of a claim or artifact is the set of blocks reachable from the target by following `cites`, `witnesses`, `validated_by`, and registered evidence-relation edges. Closure rules:

- direct closure: every block linked by an `EvidenceLink` from the target is in the set
- transitive closure: every block linked from any block in the set is in the set only when that edge's relation declares `transitive: true`. Canonical defaults: `Supports`, `Corroborates`, `Derives`, and `Witnesses` are transitive; `Refutes`, `Contextualizes`, `WeakSupports`, `Summarizes`, and `IllustratesByExample` are not. Extension relations declare their own.
- closure traversal is breadth-first from the target and is ordered by a stable composite key — edge-relation rank, then `captured_at`, then the supporting `block_id`; closure is bounded by a configurable maximum depth (default 4) and a configurable maximum cardinality (default 100), and when a bound is exceeded truncation is applied only after this ordering, so the retained prefix is deterministic and replay-stable. The truncated set is reported with a `truncated: true` flag and the user may request expansion

Compaction policies must preserve evidence-set closure for any claim or artifact at `Supported` or `Validated` state by default; File 13 implements this. Removing an evidence link is an explicit capability operation; compaction never silently severs evidence chains.

### 11.6 Boundary

Evidence blocks are blocks; evidence links are edges. The closure mechanics are graph queries over the existing canonical block-graph. This file specifies the relation enum, the confidence class enum, and the closure rules; File 20 and File 12 implement the indexes that make these queries fast.

## 12. `Citation`

Anchor: `artifact.citation`

### 12.1 The `Citation` Block Kind

`Citation` is canonical per `block.kind-catalogue` (File 08 §3.1): "a structured reference to an external source (URL, document section, file range, prior block id, MCP resource); the durable lookup key for provenance".

File 09 specifies the content shape:

- `reference_kind` — typed `CitationReferenceKind` (§12.2)
- `reference_value` — the canonical reference value for the kind (e.g., URL string, document handle, file path, prior block id, MCP resource URI)
- `source_span` — optional typed `SourceSpan` (§12.3) narrowing to a portion of the referenced source
- `captured_at` — timestamp the citation was committed (provides freshness context)
- `captured_by_run_id` — the run under which the citation was committed
- `captured_by_capability_id` — the capability that committed the citation
- `retrieval_strategy` — typed enum: `DirectFetch` (the source was fetched directly), `CachedFetch` (returned from local cache), `SearchResult` (retrieved through a search service), `UserAttached` (the user provided the reference manually), `AgentInferred` (an agent inferred the reference without retrieval)
- `display_metadata` — optional typed map carrying title, author, published date, language, and other surface-rendering fields the producer captured from the source

A URL-only citation is a durable reference, not durable source content. Evidence-bearing or high-impact use must link to captured support content such as a `SourceExcerpt`, `Observation`, `BrowserExtract` artifact version, or equivalent block that preserves the relevant source material.

### 12.2 `CitationReferenceKind`

`CitationReferenceKind` is closed canonical with the standard `Custom { namespace, name }` extension:

- `Url` — a stable URL
- `DocumentBlockSpan` — a reference to a block within a document already present in the block pool (e.g., a previously-captured `BrowserExtract` artifact's section); `reference_value` is a `block_id` plus optional span
- `FileRange` — a reference to a range within a workspace file; `reference_value` is `(file_path, range_kind, range_value)` where `range_kind` is one of `LineRange`, `ByteRange`, `CharacterRange`
- `PriorBlock` — a reference to any block in the pool by `block_id`
- `McpResource` — a reference to an MCP server resource by `(connector_id, resource_uri)` (`connector_id` per `integration.connector`, File 36 §3.1)
- `MemoryRecord` — a reference to a memory record (a `MemoryEntry` per File 14) by `(memory_id, recalled_block_id)`, where `memory_id` is the stable entity id and `recalled_block_id` pins the specific `Memory`-kind block recalled (the entry's active block may advance across revisions, so the citation records the block actually recalled)
- `KnowledgeEntry` — a reference to a File 12 knowledge-base entry by its stable id
- `Repository` — a reference to a code repository commit or path (`repo_url`, `commit_hash`, optional `path`)
- `ExternalDoiUrn` — a reference to a DOI, URN, ISBN, or other stable scholarly identifier
- `ProvenanceRecord` — a reference to a ledger entry by `(run_id, ledger_entry_id)` for self-referential provenance

### 12.3 `SourceSpan` Grammar

`SourceSpan` is a typed discriminated value:

- `CharacterRange { start: usize, end: usize }` — half-open Unicode-character range over text content
- `ByteRange { start: usize, end: usize }` — half-open byte range over binary or text content
- `LineRange { start_line: usize, end_line: usize, start_column: Option<usize>, end_column: Option<usize> }` — line-based range with optional column granularity
- `PageRange { start_page: usize, end_page: usize }` — for paginated content (PDFs, books)
- `TimeRange { start_micros: u64, end_micros: u64 }` — for audio/video sources (integer microseconds since the source start; the canonical encoding carries no float, `core.canonical-encoding` §6.15; `end_micros >= start_micros`, enforced by the typed constructor)
- `DomSelector { selector: String, occurrence_index: Option<usize> }` — CSS selector against a referenced HTML source
- `XPath { xpath: String }` — XPath against a referenced XML or HTML source
- `Composed { children: Vec<SourceSpan> }` — composed span over multiple non-contiguous regions

A `SourceSpan` is canonical-form; surfaces and retrieval consume the typed shape rather than parsing strings.

### 12.4 Capture Mechanics

Citations commit at the boundary their producing capability declares. The canonical citation-producing capabilities include:

- `web.fetch`, `web.search`, `web.extract_document`, `data.extract_*` capabilities — produce `Url` and `DocumentBlockSpan` citations
- `file.read`, `file.search`, `file.grep` — produce `FileRange` citations
- `memory.recall` — produces `MemoryRecord` citations; `knowledge.search`, `knowledge.read` — produce `KnowledgeEntry` citations
- `mcp.<server>.<tool>` capabilities that fetch resources — produce `McpResource` citations
- `citation.capture` — the explicit user-or-agent citation-capture capability for any reference kind

`citation.capture` may also commit a `SourceExcerpt` when a selected span or retrieved source fragment is promoted to durable evidence. Every committed citation or excerpt flows through the standard capability-call pipeline (`run.call-pipeline`, File 04 §8.2) and is recorded in the execution ledger (`run.execution-ledger`, File 04 §23.1).

### 12.5 Boundary

Citations are blocks; their identity, immutability, content hash, and graph participation follow File 08. This file specifies the typed reference-kind catalogue and the source-span grammar. Surface-rendering choices (citation card layout, hover previews, click-to-open behavior) are owned by the UI specs.

## 13. `Observation`

Anchor: `artifact.observation`

### 13.1 The `Observation` Block Kind

`Observation` is canonical per `block.kind-catalogue` (File 08 §3.1): "a structured observation of the world (file content snapshot, accessibility tree snapshot, screenshot reference, status query result, browser DOM extract) committed for replay and policy revalidation".

File 09 specifies the content shape and the staleness-fingerprint contract:

- `observation_kind` — typed `ObservationKind` (§13.2)
- `payload_reference` — for small inline payloads, the content lives inline; for large payloads (screenshots, accessibility trees, DOM extracts), the payload is `External` referencing the block's external content store
- `captured_at` — full-granularity timestamp at capture
- `captured_by_run_id` — the run under which the observation was committed
- `captured_by_capability_id` — the capability that produced the observation
- `capture_context` — typed map carrying the active scope context at capture (`run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`)
- `staleness_fingerprint` — typed `StalenessFingerprint` (§13.3) identifying what the observation depended on; the runtime checks this fingerprint before any mutation declaring the observation as a precondition (per `run.call-pipeline`, File 04 §8.2 stale-state revalidation)
- `observation_subject` — typed map identifying the observed entity (e.g., file path for file snapshots, window handle for accessibility trees, URL for DOM extracts)

### 13.2 `ObservationKind`

`ObservationKind` is closed canonical with the standard `Custom { namespace, name }` extension:

- `FileSnapshot` — content snapshot of a file at a path; payload includes content hash, mtime, byte length
- `AccessibilityTreeSnapshot` — captured accessibility tree from a desktop application (per GUI Control surface spec); payload includes role-based filtered tree
- `Screenshot` — pixel-data screenshot; payload references the external image blob; metadata includes scale factor, capture region, optional OCR text
- `BrowserDom` — captured DOM extract from a web page; payload includes URL, captured HTML, optional viewport metadata
- `NetworkResponseSnapshot` — captured HTTP response (status, headers, body); used for replayable web automation
- `DatabaseQueryResult` — captured result set from a database query; payload includes the query, the result schema, and the data
- `TerminalOutput` — captured terminal session output; payload includes the command, the stdout/stderr stream, and the exit code
- `ProcessState` — captured process state snapshot (running processes, ports listening, etc.)
- `EnvironmentSnapshot` — captured environment variables, current working directory, shell version, OS version
- `RepositoryState` — captured git state (branch, commit, working-tree status, staged changes)
- `WorkspaceSnapshot` — captured workspace state (open files, materialized artifacts, active settings)
- `Custom { namespace, name }` — specialized observation kind

### 13.3 `StalenessFingerprint`

`StalenessFingerprint` is a typed value the capability commits with the observation so future calls can revalidate currency:

- `ContentHash { hash: String }` — SHA-256 (or registered alternative) of the observed content
- `Mtime { mtime_unix_nanos: i64 }` — POSIX mtime of the observed file as integer nanoseconds since the Unix epoch (the canonical encoding carries no float, `core.canonical-encoding` §6.15; integer is also exact for the §13.4 replay-equality check, which `f64` seconds is not at large epochs)
- `MtimeAndHash { mtime_unix_nanos: i64, hash: String }` — both fields, for robustness
- `VersionId { version_id: BlockId }` — for observation-of-block scenarios, the block_id whose content the observation captures
- `AccessibilityTreeHash { tree_hash: String }` — hash of the canonical-form accessibility tree
- `DomSignature { url: String, signature: String }` — a hash over the DOM structure (typically the tag tree without text content)
- `EtagAndLastModified { etag: Option<String>, last_modified: Option<String> }` — HTTP cache validators
- `GitCommit { commit_hash: String, branch: String }` — git state when the observation was captured
- `Composite { fingerprints: Vec<StalenessFingerprint> }` — multiple fingerprints combined, all must match for currency
- `Custom { namespace, name, value }` — extension fingerprint for kinds whose currency check requires a registered evaluator

The runtime checks the fingerprint against current state when a capability declares this observation as a precondition (per `run.call-pipeline`, File 04 §8.2 `stale_state_revalidation`); a mismatch produces a typed `StateChangedSinceObservation` error in-band.

A fingerprint that backs a mutation precondition must be **content-derived**: `ContentHash`, `MtimeAndHash`, `AccessibilityTreeHash`, `DomSignature`, `GitCommit`, `VersionId`, `EtagAndLastModified` with the `etag` present, or a `Composite` containing at least one content-derived member. A bare `Mtime` (or an `EtagAndLastModified` carrying only `last_modified`) remains valid as evidence or as a freshness hint but cannot by itself back a mutation precondition, because wall-clock modification time is not a content signal. `observation.staleness_check_strictness` (§19.1) keys its `Permissive` mode on this same content-derived set, and File 19 §9.3 mirrors the rule for perception-side fingerprints.

### 13.4 Replay Use

Observations participate in replay (per `run.ledger-events-commits`, File 04 §23 and File 10): a `snapshot_replayable` capability whose original execution depended on an observation requires the same observation (or a re-captured equivalent) at replay time. The observation's `staleness_fingerprint` and `content_hash` (per `block.content-hash`, File 08 §4.5) enable replay-time equality checks.

### 13.5 Boundary

Observations are blocks; their content carriage is File 08's concern. This file specifies the kind catalogue, the staleness-fingerprint contract, and the replay use. Surface- and subsystem-specific observation production rules (e.g., GUI Control's three-tier perception, Web's fetch tiers) are owned by those specs; their committed observations conform to the canonical contract here.

## 14. `Validation` and `Critique`

Anchor: `artifact.validation-critique`

### 14.1 The Block Kinds

`Validation` is canonical per `block.kind-catalogue` (File 08 §3.1): "a structured validation result (postcondition check, type check, lint result, evaluator score); referenced from runs and from the completion-verification hook surface (`run.termination`, File 04 §22)".

`Critique` is canonical per `block.kind-catalogue` (File 08 §3.1): "a structured critique or review record (a critic agent's review, a code-review comment, a quality-control note); semantically distinct from Validation because critiques are evaluative judgments rather than pass/fail checks".

File 09 specifies the content shapes and the integration with `run.termination` (File 04 §22).

A `Validation` block's content carries:

- `validation_kind` — typed enum: `Postcondition` (the capability's declared postcondition check), `TypeCheck`, `Lint`, `Test`, `EvaluatorScore`, `SchemaValidation`, `CitationCheck`, `FactualityCheck`, `ConsistencyCheck`, `SafetyCheck`, `Custom { namespace, name }`
- `outcome` — typed `ValidationOutcome` enum: `Passed`, `Failed`, `Inconclusive`
- `validated_target_id` — `block_id` (or `artifact_id` plus version reference, or `claim_id`) of the target being validated
- `validator_kind` — typed enum: `Deterministic`, `ModelMediated`, `UserManual`
- `validator_reference` — for `Deterministic`, the validator capability id; for `ModelMediated`, the validator model id plus policy model-request template id; for `UserManual`, the user id
- `failure_details` — when `outcome` is `Failed`, structured details (rule violated, expected value, actual value)
- `inconclusive_reason` — when `outcome` is `Inconclusive`, structured reason
- `latency_ms` — runtime spent validating
- `evidence_links` — optional list of `EvidenceLink` references pointing to supporting blocks (e.g., the test output block that the validation depended on)
- `reasoning` — the validator's natural-language justification for the `outcome`; **required when `validator_kind` is `ModelMediated`** and decode-rejected when absent for that kind (the same required-iff-present constructor discipline `failure_details` carries for `Failed`); optional for `Deterministic` and `UserManual` validators
- `confidence` — optional validator-reported confidence in the outcome, a fixed-point integer in [0, 1000] milli-units (the canonical encoding carries no float, `core.canonical-encoding` §6.15); a ranking and display signal only — the `outcome` enum is the verdict, and `confidence` never substitutes for it
- `evaluator_class` — optional typed evaluator class recording the grade of evaluator that produced the verdict; a typed class, never a numeric score, and it does not stand in for `outcome` (it stays inside the no-numeric-verdict rule)
- `replay_key` — for `ModelMediated` validators, the reference set that makes the verdict replayable: `model_selection_record_id` (the recorded model-selection decision), the model-request template version, the validator-declaration version, and the model-request assembly reference; null for `Deterministic` and `UserManual` validators

A `Critique` block's content carries:

- `critique_kind` — typed enum: `CodeReview`, `EditorialReview`, `PeerReview`, `DesignReview`, `Custom { namespace, name }`
- `target_id` — `block_id` or entity id of the critiqued target
- `summary` — short critique summary
- `findings` — structured list of finding records (each with severity, location reference, description, optional suggested resolution)
- `critic_kind` — typed enum: `User`, `Agent`, `Subagent`, `External`
- `critic_reference` — actor identifier
- `recommended_action` — optional typed enum: `AcceptAsIs`, `RevisionRecommended`, `RevisionRequired`, `RejectAndRestart`

### 14.2 `ValidationState` Derivation

Anchor: `artifact.validation-state-derivation`

The `ValidationState` of an artifact version (per §5.3), a claim, or any other target with a `validated_by` edge is derived from the linked `Validation` blocks:

1. Collect all `Validation` blocks linked from the target by `validated_by` edges
2. Filter to validations whose `validation_kind`, when combined with applicable settings, are considered required for the target's kind (e.g., a `Validator`-kind artifact may require both `SchemaValidation` and `TypeCheck` validations)
3. Compute outcome aggregation (rules apply in order; a non-required validation's adverse outcome never gates a rung — a non-required `Passed` may satisfy the linked-`Passed` floor, and only the last rule turns on adverse non-required outcomes):
   - any required validation with `outcome: Failed` → `ValidationState::Failed`
   - every required validation kind present with `outcome: Passed`, and at least one linked validation carries `outcome: Passed` → `ValidationState::Passed`
   - any required validation with `outcome: Inconclusive` and no required failures → `ValidationState::NeedsReview`
   - missing required validations → `ValidationState::PendingValidation`
   - no validations linked at all → `ValidationState::NotValidated`
   - otherwise — validations are linked but none is required and none passed → `ValidationState::NeedsReview`; an all-adverse non-required record is reviewable signal, never a silent `Passed`

The derivation is recomputed on every read of the target's validation state. Caching is a storage optimization; the derivation rules are the contract.

### 14.3 Hook Surface Integration

The `run.termination` (File 04 §22) completion-verification hook surface produces `Validation` blocks. The integration:

- a deterministic check (postcondition validator) registered through `run.hook-integration` (File 04 §23.3)'s hook mechanism commits a `Validation` block with `validator_kind: Deterministic`, `validator_reference` set to the validator capability id, and `outcome` set to the check's result
- a model-mediated check (designated model evaluating the target against an expected outcome) commits a `Validation` block with `validator_kind: ModelMediated`, `validator_reference` set to the model id and policy model-request template id, and `outcome` set to the model's verdict
- a user-applied validation (the user clicking "Mark validated" on an artifact) commits a `Validation` block with `validator_kind: UserManual`

`validation.run(target_id, validation_kind?)` is the canonical capability for explicit validation invocation. Its tier is resolved from the validator capability and touched resources: pure read validators that only produce `Validation`/`Evidence` blocks are `ReadOnly`; validators that execute code, mutate files, use credentials, publish externally, or change sandbox state inherit the appropriate write or approval tier.

### 14.4 Critique vs Validation

`Validation` produces pass/fail/inconclusive outcomes against well-defined checks. `Critique` produces evaluative findings that may include recommendations but do not themselves gate state transitions. The separation is load-bearing:

- artifact `ValidationState` derives only from `Validation` blocks; `Critique` blocks do not contribute to validation state
- automation that depends on validation outcome reads validation state, not critique findings
- critiques surface in inspectors, comparison boards, and review panels as advisory content

A critique may produce a validation (by recommending the validator be run); the validator's outcome is what counts for state.

### 14.5 Boundary

Validation and critique are block-level records; this file specifies their content, the validation-state derivation, and the hook-surface integration. Surface- and subsystem-specific validators (Coder's type checkers, Data Processor's data-validation framework, Teacher's quiz graders) register through the canonical mechanism and produce the canonical block shapes.

## 15. `Provenance`

Anchor: `artifact.provenance`

### 15.1 Definition

`Provenance` is a derived view over the unified block graph (File 08), the version graph (File 11), the execution ledger (`run.execution-ledger`, File 04 §23.1), the capability registry (File 05), and the entity records (this file). It is the answer to questions like "what produced this artifact?", "which evidence supports this claim?", "what runs touched this block?", "what is the derivation chain of this version?".

A `Provenance` is not:

- a stored entity — provenance is computed on read from the underlying substrates
- a parallel ledger — the execution ledger is the durable source-of-truth for run-level facts; provenance queries project over it
- a per-block field — blocks have producer, origin_run_id, and source_attribution per File 08; provenance is the transitive closure over those plus the graph edges plus the entity records
- an audit log — audit logs are a downstream consumer of provenance queries; the canonical layer is the query

### 15.2 Provenance Closure Rules

The closure rules for provenance queries:

- **Block-level closure**: starting from a `block_id`, follow `parent_block_id` for causal lineage, `contains` (via `children_block_ids` resolution) for composition lineage, `derives_from` for derivation lineage, `supersedes` for edit lineage. Each step yields the next ancestor or component.
- **Edge-level closure**: starting from a `block_id` or entity, follow `cites`, `witnesses`, `validated_by`, `consolidates`, `responds_to`, `references`, `conditioned_on`, and registered extension edges to assemble the evidence and dependency network.
- **Run-level closure**: every block's `producer` and `origin_run_id` resolve to a producing run; every run has a `RunIntent`, a producing route, a producing intent thread (or `parent_run_id` for child runs); closure under these resolves the causal chain back to the originating user request, automation, or external event.
- **Capability-level closure**: every run's ledger entries reference the resolved `(capability_id, capability_version)` per `capability.invocation-record` (File 05 §11); closure resolves to declarations and to registered entries.
- **Entity-level closure**: artifact and claim entities reference their producing run and contributing capabilities directly; closure resolves to producing intent thread, conversation, task, workspace.

Closure is bounded in depth and cardinality per the settings in §19 to keep queries tractable.

### 15.3 Canonical Query Surface

The canonical provenance-query capability set:

- `provenance.query_lineage(target_id, max_depth?, edge_filter?)` — returns the typed lineage tree (parent-axis closure) of the target. Result: ordered list of `(block_id_or_entity_id, kind, relation, distance)` tuples plus a `truncated: bool` flag when bounds were hit.
- `provenance.query_evidence_set(claim_or_artifact_id, max_depth?, relation_filter?, confidence_floor?)` — returns the evidence-set closure per §11.5. Result: ordered list of `(supporting_block_id, EvidenceRelation, confidence_class, confidence_score, captured_at)` tuples.
- `provenance.query_contributing_runs(target_id)` — returns the set of `run_id`s that produced, edited, validated, or critiqued the target across its full lineage.
- `provenance.query_contributing_capabilities(target_id, distinct_versions?)` — returns the set of `(capability_id, capability_version)` invoked across the target's lineage; with `distinct_versions: true`, distinguishes between versions; without, collapses to capability ids.
- `provenance.query_replay_trace(target_id)` — returns the ordered set of execution-ledger entries that produced and modified the target, suitable for replay or forensic reconstruction.
- `provenance.query_derivation_chain(artifact_id_or_version_id)` — for artifacts, returns the version chain (`parent_version_id` closure) plus the `derives_from` graph closure; the result is a typed DAG of `(version_id, derivation_summary, produced_by_run_id, produced_by_capability_id)` nodes.
- `provenance.contradiction_check(claim_id)` — runs over the claim's `EvidenceLink` set, returns any `Refutes`-relation supporting blocks whose confidence class exceeds the strongest `Supports` or `Corroborates` link (the canonical supporting set per §11.4), and separately reports comparable-class conflicts as unresolved. Used by the QC subsystem and by the `claim.update_status` automatic derivation per §9.4.
- `provenance.query_artifact_versions(artifact_id, include_tombstones?)` — returns the ordered version chain, including tombstones when requested.

Each query capability declares `permission_tier: ReadOnly`, `concurrency: ConcurrencySafe`, `replay_class: deterministic_replayable` (the target's state at query time determines the result; replay records the snapshot id).

### 15.4 Determinism and Reconstruction

Provenance queries are deterministic given the same registry, version-graph, block-pool, and ledger snapshots. Two queries with the same target and the same snapshots return byte-identical results. This is the load-bearing property for replay, audit, and reproducibility.

Caching of provenance results is a storage optimization; the underlying substrates are the source-of-truth. Cache invalidation is event-driven (when a new block commits, a new edge commits, a version commits, or a ledger entry is recorded, any cached query result whose closure includes the affected substrate is invalidated).

### 15.5 Cross-Workspace and Cross-Installation Provenance

When an artifact, claim, or supporting block is imported from another workspace or installation (via File 21), the import operation commits an `Import` producer record on every imported block per `block.block` (File 08 §2.2). Provenance queries on imported blocks resolve to the import record; further closure into the originating installation's run and capability history requires File 21's cross-installation mapping table.

### 15.6 Boundary

Provenance is a query surface over existing substrates. This file specifies the closure rules, the canonical query set, the determinism contract, and the cross-installation boundary. Implementation choices (graph traversal algorithms, caching layers, index structures) belong to File 20 and File 12.

## 16. Capability Surface

Anchor: `artifact.capability-surface`

### 16.1 Closed Canonical Capabilities

File 09 declares the following canonical entity-level capabilities. Each is a built-in capability declared per `capability.declaration` (File 05 §3) and registered at startup per `capability.startup-registration` (File 05 §16.1) with the `Builtin` source.

**Artifact capabilities:**

- `artifact.create(artifact_kind, content, title, description?, materialization_policy?, scope?, tags?)` — first-version artifact creation; `WorkspaceWrite` tier; produces an `Artifact`-kind block (the first version) plus the entity record; for high-impact kinds (`WorkflowTemplate`, `Adapter`, `Validator`) at `global` scope the tier escalates to `UserApproval`; this kind-specific call-out states a minimum effective tier for those kinds at `global` scope; it does not exempt other kinds. Any `artifact.create` proposal naming a broader-than-`workspace` scope remains subject to the per-call workspace-containment rule (`policy.effective-tier-resolution`, File 06 §4.3): a `WorkspaceWrite` proposal not contained within the active workspace escalates to `UserApproval`. Consequently, creation at `global` scope cannot bypass the `artifact.promote_scope` approval rule (this section; scope-promotion semantics: `block.scope-promotion`, File 08 §11.2)
- `artifact.commit_version(artifact_id, content, derivation_summary?, title_update?, description_update?, tags_update?)` — subsequent version commit; `WorkspaceWrite` tier; produces a new `Artifact`-kind block linked by `supersedes` and updates the entity's `current_version_block_id`
- `artifact.set_review_state(artifact_id, version_id, new_state)` — explicit review state mutation; `WorkspaceWrite` tier; emits `ArtifactReviewStateChanged` event
- `artifact.update_materialization_policy(artifact_id, new_policy)` — `WorkspaceWrite` tier when narrowing materialization; `UserApproval` when broadening (e.g., `None` → `InWorkspace` materializes file content to disk)
- `artifact.promote_scope(artifact_id, new_scope)` — explicit scope promotion; tier scales with target scope per `block.scope-promotion` (File 08 §11.2) (workspace and below: `WorkspaceWrite`; `global` and `reusable_policy_rule`: `UserApproval`). A `reusable_policy_rule` target routes through §11.2's dedicated kind- and schema-validating admission even under this command name — the tier here is the approval cost, not a containment edge
- `artifact.archive(artifact_id)` — `WorkspaceWrite` tier; transitions artifact lifecycle to `Archived`
- `artifact.restore(artifact_id)` — `WorkspaceWrite` tier; transitions out of `Archived` or `Discarded`
- `artifact.discard(artifact_id)` — `WorkspaceWrite` tier; transitions to `Discarded`
- `artifact.merge(parent_artifact_ids, content, derivation_summary)` — merges two or more artifact versions into a new version; `WorkspaceWrite` tier; commits a new version with multiple `derives_from` edges
- `artifact.hard_delete_version(version_id)` — irreversible; `UserApproval` tier with `permission_floor: Denied` requiring typed-confirmation; emits `ArtifactVersionHardDeleted` event
- `artifact.hard_delete_entity(artifact_id)` — irreversible; `UserApproval` tier with `permission_floor: Denied` requiring typed-confirmation per artifact id; emits `ArtifactHardDeleted` event
- `artifact.preview_export(artifact_id, format?, include_versions?, include_provenance?)` — `ReadOnly` tier; returns the proposed export manifest, included versions, destination shape, and provenance inclusion without writing a bundle
- `artifact.export(artifact_id, format?, include_versions?, include_provenance?, destination?)` — dynamic tier: `WorkspaceWrite` when materializing inside the active workspace, `UserApproval` when writing outside the workspace, publishing externally, or exporting sensitive content; produces a portable artifact bundle as a new `ArtifactBundle` artifact or external package
- `artifact.materialize_locally(artifact_id, version_id?)` — for `ExternalRef` artifacts; fetches the external content and caches locally; `WorkspaceWrite` tier

**Claim capabilities:**

- `claim.publish(claim_text, claim_kind, confidence_class, anchor?, scope?, evidence_links?)` — explicit claim publication; tier per §10.1; commits a `Claim`-kind block per `artifact.claim` (File 09 §9)
- `claim.update_status(claim_id, new_status, reason)` — explicit status override; `WorkspaceWrite` tier
- `claim.withdraw(claim_id, reason)` — irreversible at the entity level (the claim remains addressable but is marked withdrawn); `WorkspaceWrite` tier
- `claim.supersede(prior_claim_id, new_claim_text, new_claim_kind, new_confidence_class, derivation_summary)` — commits a new claim block superseding the prior; `WorkspaceWrite` tier
- `claim.attach_evidence(claim_id, supporting_block_id, evidence_relation, confidence_class?, confidence_score?, applies_to_span?, notes?)` — commits an `EvidenceLink` edge; `WorkspaceWrite` tier
- `claim.detach_evidence(claim_id, supporting_block_id, evidence_relation)` — records evidence-edge detachment in the active projection; the claim block remains unchanged; `WorkspaceWrite` tier
- `claim.review(claim_id, decision, reviewer_notes?)` — for claims in `Candidate` status; `WorkspaceWrite` tier; transitions status per the decision

**Evidence and citation capabilities:**

- `evidence.link(supporting_block_id, supported_target_id, evidence_relation, confidence_class?, confidence_score?, applies_to_span?, notes?)` — generic evidence-link capability covering claims, artifacts, and any other target; tier is dynamic: run-local evidence results may be `ReadOnly`, while persistent catalogue/entity links are `WorkspaceWrite` or stronger by scope
- `citation.capture(reference_kind, reference_value, source_span?, retrieval_strategy?, display_metadata?, capture_excerpt?)` — explicit citation commit; tier is dynamic: run-local citations may be `ReadOnly`, persistent reusable citations are `WorkspaceWrite`, and sensitive/external publication escalates by policy; may commit a `Citation` and optional `SourceExcerpt`

**Observation capabilities:**

- `observation.commit(observation_kind, payload, observation_subject, staleness_fingerprint?, capture_context?)` — explicit observation commit; usually `ReadOnly` when recording a read result, but escalates when the observation is published to a reusable catalogue or touches sensitive resources
- the surface- and subsystem-specific observation-producing capabilities (file.read, web.fetch, gui.snapshot, browser.snapshot, data.profile, etc.) commit `Observation` blocks as part of their normal execution per their declared `output_block_kinds`

**Validation capabilities:**

- `validation.run(target_id, validation_kind, validator_reference?)` — invoke a registered validator on the target; tier resolves from the validator's declared touched resources and side effects
- `validation.attach(validation_block_id, target_id)` — link a pre-computed `Validation` block to a target via `validated_by`; `WorkspaceWrite` tier

**Critique capabilities:**

- `critique.publish(target_id, critique_kind, summary, findings, recommended_action?)` — commits a `Critique` block; `WorkspaceWrite` tier

**Provenance capabilities:**

- the eight `provenance.query_*` and `provenance.contradiction_check` capabilities from §15.3; all `ReadOnly`, all `ConcurrencySafe`, all `deterministic_replayable`

### 16.2 Capability Metadata Declarations

Anchor: `artifact.capability-metadata-declarations`

Every capability above declares the canonical `capability.declaration` (File 05 §3) field set. Key declarations specific to File 09:

- `output_block_kinds` declarations name the block kinds the capability produces, drawn from File 08's canonical catalogue plus the `Claim` extension this file declares
- `touched_resources` declarations name the entity pools the capability reads or writes; this file declares extension resource classes (`artifact-pool`, `claim-pool`, `evidence-link-pool`, `provenance-cache`) registered through `capability.extension-resource-classes` (File 05 §6.3)'s extension mechanism
- `replay_class` declarations follow `capability.replay-class` (File 05 §7.3): most artifact/claim/evidence operations are `effect_replayable_with_policy` because re-publishing identical content would create duplicate entities; provenance queries are `deterministic_replayable`
- durable result blocks produced by a read-only capability do not by themselves raise the tier; explicit publication to reusable entity pools, external destinations, or broader scopes does
- `data_sensitivity` defaults to `Public` for entity capabilities; subsystems may declare narrower defaults per their surface or specialization (e.g., a Teacher surface's `lesson.publish` may default to `Sensitive` when the lesson contains learner-private content)

### 16.3 Boundary

Capabilities are declared per File 05; their execution flows through `run.call-pipeline` (File 04 §8.2)'s pipeline; their approval flows through File 06's policy machinery; their surfacing follows File 07's composition algorithm. This file specifies the canonical entity-capability set as built-in declarations; surface- and subsystem-specific extensions register additional capabilities through the same canonical mechanism.

## 17. Cross-Surface Interoperability

Anchor: `artifact.cross-surface-interoperability`

### 17.1 Single Entity Pool

ATLAS3 has one artifact entity pool, one claim entity pool, one evidence-link edge set, and one block pool (per `block.cross-surface-interoperability`, File 08 §12). Every surface reads from and writes to these substrates through the canonical capability set.

### 17.2 Per-Surface Projections

Anchor: `artifact.per-surface-projections`

Each surface projects the entity pool through surface-specific filters:

- the Coder surface presents `CodePatch`, `Document` (markdown), `Notebook` (when surface-relevant), and the file-system view of materialized artifacts; the inspector shows artifact lifecycle and review state
- the Web surface presents `BrowserExtract`, `WebDocument`, `Image` (page screenshots), `Citation` (cited sources), and the Research Canvas projection of evidence-link graphs
- the Data Processor surface presents `Dataset`, `Chart`, `Notebook`, `Table`, plus the data-lineage projection of `derives_from` edges
- the Teacher surface presents `Lesson`, `Curriculum`, `Quiz`, `ExerciseSet`, `FlashcardSet`, `Rubric`, plus custom Teacher-surface artifact kinds for specialized pedagogy and learner-progress projections
- the GUI Control surface presents `Macro`, `ScreenshotSeries`, `Observation` (UI tree snapshots), plus action-replay projections
- the System Agent surface presents change records as artifact-like outputs with rollback projections (File 32 declares its specific kinds)
- the memory management surface presents `Memory`-kind blocks (per `block.kind-catalogue`, File 08 §3.1) and the knowledge-base projection over claims and citations
- the conversation transcript filters for transcript-anchorable kinds and resolves artifact references to inline cards or sidecar panes
- the inspector lens (per `surface.inspector-lens`, File 07 §12.4) presents every entity in the pool, filtered by user-chosen axes (kind, status, scope, source, validation state, review state, lifecycle state)

The filter is a surface concern; the entities and their content remain in the unified pool unchanged. An artifact produced by the Coder surface but referenced from the Memory subsystem is visible in both.

### 17.3 Cross-Surface Composition

An artifact may be composed of content from multiple surfaces. A research report (`Document` artifact kind) produced in a conversation may compose:

- text sections describing conclusions
- `Citation` children pointing to web sources captured by the Web surface
- `Chart` children pointing to charts generated by the Data Processor surface
- `Observation` children referencing files inspected by the Coder surface
- `Evidence` children with `Supports` and `Refutes` evidence-link metadata

The composition is a single artifact version block (composed) whose children are the constituent blocks. Each child lives at its appropriate scope. The composition renders correctly in any surface that supports the constituent kinds; surfaces that do not support some child kinds render those as typed placeholders ("[unsupported kind: …]") and link to the inspector lens for full inspection (matching `block.cross-surface-composition` (File 08 §12.3)).

### 17.4 Cross-Conversation Reference

Artifacts at `workspace` scope (or broader) are addressable from any conversation in the same workspace. Cross-conversation reference uses the canonical capability path: a conversation references an artifact by `artifact_id`; the surface resolves to the current version's block and renders. The artifact identity is independent of any conversation.

### 17.5 Boundary

Cross-surface interoperability is a property of the unified entity pool. This file establishes the pool's invariants; later per-surface specs declare how each surface projects, filters, and composes entities. No surface is permitted to introduce a private artifact pool, private claim pool, or private evidence-graph.

## 18. Persistence Contract

Anchor: `artifact.persistence-contract`

### 18.1 What Is Durably Stored

The following entity-related facts are durable:

- the artifact entity pool — every artifact entity record (per §3.2) survives process restart, conversation archive, and version-graph operations until explicit `artifact.hard_delete_entity`
- the claim entity pool — every `Claim` block (and its block-level fields per File 08) survives until explicit hard delete; the claim's content is in the block, the derived status is recomputed
- the artifact version metadata records (per §6.2) — durable, survive restart, removed only on hard-delete tombstoning (which retains a tombstone row)
- `EvidenceLink` edge metadata — durable as part of the block-graph edge set (per `block.what-is-durably-stored`, File 08 §13.1's edge set)
- `Validation` and `Critique` blocks — durable per File 08
- the file-system materializations of `InWorkspace` artifacts — durable on disk per the workspace-materialization contract
- entity-related events recorded in the ledger — every artifact-version commit, every review-state change, every claim publication, every evidence-link commit produces a ledger entry

### 18.2 What Is Computed

The following are computed, not stored:

- `ArtifactLifecycle`, `ReviewState`, `ValidationState` per `ContextVersion` — derived from the version-graph action log and the `validated_by` edges, rebuilt on demand
- `ClaimStatus` when not explicitly overridden — derived from the evidence-link set per §9.4
- `EvidenceSet` closure — computed on demand from the block-graph edges per §11.5
- Provenance query results — computed on demand from the underlying substrates per §15
- Materialized paths' current freshness — computed by comparing the version-block's content hash to the file's current content hash under the same declared canonical encoding (per §7.4)

### 18.3 Reconstruction Across Restart

On process restart:

- the artifact entity pool reloads from storage
- artifact-version metadata records reload
- the block pool re-emerges per `block.reconstruction-across-restart` (File 08 §13.3)
- evidence-link edges reload as part of the block-graph edge set
- lifecycle, status, evidence-set, and provenance derivations rebuild on first read of each target

In-flight artifact versions whose producing run was orphaned at restart follow `run.cancellation` (File 04 §17.3) orphan rules: if the capability declared `partial_output_meaningful: true` and provided a resume handler, the version may be recovered as a partial-orphan version-block (per `block.partial-block-orphans`, File 08 §7.3); otherwise the staged file is discarded and no version commits.

### 18.4 Reconstruction Across Retry, Edit, Reroute, Branch

Per `run.retry-reroute-branch` (File 04 §19), retry / edit / reroute / branch produce new runs linked to prior ones. The artifact entity pool and the version chain are shared across these operations: a retried run may commit a new artifact version superseding the prior; the prior version's block remains; the version chain branches in the version graph.

Run-scoped evidence-link edges (e.g., evidence-links a run produced to support its claims) do not transfer across retry/edit/reroute/branch by default — the new run is a fresh run and produces its own evidence. Workspace-scoped and broader-scoped evidence-links do transfer per their scope rules (matching `block.cross-scope-references` (File 08 §11.3) and `policy.lease-primitive` (File 06 §11.3)).

### 18.5 Cross-Conversation and Cross-Workspace

Artifacts and claims at `workspace` scope are visible across all conversations in the workspace. Provenance queries on workspace-scoped artifacts return references to runs and conversations spanning the workspace lifetime. Cross-workspace reference requires File 21; the canonical contract here is that artifact identity is portable through the import mechanism, with the import operation producing the `Import` producer record per File 08.

### 18.6 Boundary

Persistence is the storage layer's responsibility. This file specifies what the storage layer must persist (the entity-record field sets, the version metadata records, the evidence-link edge metadata) and what it must reconstruct (the derived states, the closures, the provenance results). The storage schema, replication, sync, and import/export mechanics are owned by File 20 and File 21.

## 19. Settings

Anchor: `artifact.settings`

### 19.1 Configurable Dimensions

Every entity mechanism in this file is configurable through settings (per `core.settings-system`, File 01 §6.8). File 09 names the dimensions; the settings system owns the cascade and storage.

**Artifact dimensions:**

- `artifact.default_materialization_policy.<kind>` — per-kind default `MaterializationPolicy`
- `artifact.workspace_materialization_path_template` — path template for `InWorkspace` materializations
- `artifact.auto_accept_first_version` — whether first-version creation auto-transitions to `Active` (default false; user must accept)
- `artifact.review_required.<kind>` — per-kind whether review is required before lifecycle leaves `Draft` (default false for routine kinds, true for `WorkflowTemplate`, `Adapter`, `Validator`)
- `artifact.validation_required.<kind>` — per-kind whether validation is required (default false for most, true for `Validator` and `Adapter` kinds)
- `artifact.archive_retention_policy` — how long archived artifacts remain inspectable before being eligible for automated retention recommendations (the recommendations are user-actionable, not automatic; default indefinite)
- `artifact.hard_delete_confirmation_threshold` — typed-confirmation requirements for hard delete per kind
- `artifact.bundle_export_includes_provenance` — whether `artifact.export` includes provenance closure by default (default true)
- `artifact.external_ref_local_cache_enabled` — whether `ExternalRef` artifacts cache locally on first access (default false)

**Claim dimensions:**

- `claim.evidence_threshold` — minimum aggregate confidence required for `Supported` status (default `Plausible`)
- `claim.auto_extraction.enabled` per scope
- `claim.auto_extraction.model_id`
- `claim.auto_extraction.model_request_template_id`
- `claim.auto_extraction.minimum_confidence_class` (default `Plausible`)
- `claim.auto_extraction.review_required` (default true)
- `claim.surface_display.confidence_class_filter` — minimum class to surface by default
- `claim.contradiction_alert_enabled` — whether `Contradicted` status triggers user notification (default true for `DirectlyObserved` and `VerifiedExternal` confidence classes)
- `claim.withdrawn_visibility` — whether withdrawn claims appear in surfaces by default (default false)

**Evidence dimensions:**

- `evidence.closure_max_depth` — maximum depth for evidence-set closure (default 4)
- `evidence.closure_max_cardinality` — maximum count for evidence-set closure (default 100)
- `evidence.relation.<relation>.transitive` — per-relation transitive-closure enablement (canonical default: `Supports`, `Corroborates`, `Derives`, `Witnesses` are transitive; `Refutes`, `Contextualizes`, `WeakSupports`, `Summarizes`, `IllustratesByExample` are not)
- `evidence.compaction_preservation` — whether compaction preserves evidence chains by default (default true)

**Citation dimensions:**

- `citation.capture_display_metadata` — whether to capture title/author/date by default on `Url` citations (default true)
- `citation.refresh_policy` — when URL-backed citations should be rechecked by explicit refresh, source fingerprint mismatch, user action, or consuming workflow requirement
- `citation.cache_retention_policy` — how cached source fetches are retained for storage management; retention values are storage hints, not freshness or correctness conditions

**Observation dimensions:**

- `observation.staleness_check_strictness` — `Strict` (any fingerprint mismatch produces `StateChangedSinceObservation` error), `Permissive` (only a content-derived fingerprint mismatch — per the content-derived set in §13.3 — produces error; bare-mtime drift is a warning), `Off` (no staleness checks; off by default for any mutating capability)
- `observation.payload_external_threshold_bytes` — when observation payload exceeds this size, use `External` content (default 64 KB)
- `observation.screenshot_resolution_default` — per `ObservationKind: Screenshot` default capture resolution

**Validation dimensions:**

- `validation.run_on_commit.<kind>` — per artifact kind, whether validation runs automatically on commit (default false; user must invoke `validation.run`)
- `validation.required_validators.<kind>` — per artifact kind, list of validation kinds required for `Validated` state
- `validation.model_mediated_enabled` — whether model-mediated validators are enabled (per `run.termination`, File 04 §22 and `policy.settings-resolution-for-policy` (File 06 §16); off by default; opt-in per scope)
- `validation.failure_action.<kind>` — on validation failure, action to take (typed enum: `BlockCommit` — commit fails; `MarkFailed` — version committed but state is Failed; `WarnOnly`)

**Critique dimensions:**

- `critique.surface_display_filter` — minimum severity to surface by default
- `critique.findings_max_count_per_block` — soft cap on findings per `Critique` block; producers above the cap split into multiple blocks

**Provenance dimensions:**

- `provenance.query.max_depth` — global default closure depth for provenance queries (default 8)
- `provenance.query.max_cardinality` — global default closure cardinality (default 4096)
- `provenance.cache_enabled` — whether provenance query results cache
- `provenance.query.include_tombstones_default` — default for `include_tombstones?` parameter
- `provenance.cross_installation_link_enabled` — whether import operations preserve cross-installation provenance hooks (default true)

**Agent exposure dimensions** (per `policy.agent-exposure-policy-settings`, File 06 §16.4 and `block.settings` (File 08 §14)):

- `artifact.kind_catalogue_visible_to_agent` — whether the agent sees the canonical and custom artifact kinds in model-request text (default `InModelRequest` for canonical, `OnRequest` for custom)
- `claim.confidence_class_exposure` — whether `ClaimConfidenceClass` is part of model-request rendering of claims (default `InModelRequest`)
- `evidence.relation_exposure` — whether `EvidenceRelation` and confidence appear in model-request rendering of evidence-link edges (default `InModelRequest`)
- `provenance.query_exposure` — whether provenance queries are surfaced to the agent as primary or borrowable capabilities (default `Borrowable`)

### 19.2 Settings-Key Convention

Entity-related settings use the dotted-key convention `artifact.<dimension>`, `claim.<dimension>`, `evidence.<dimension>`, `citation.<dimension>`, `observation.<dimension>`, `validation.<dimension>`, `critique.<dimension>`, `provenance.<dimension>`. Per-kind overrides use `<entity>.<dimension>.kind.<kind_name>`. Per-source overrides use `<entity>.<dimension>.source.<source_id>`.

### 19.3 Boundary

This file names the settings dimensions. The settings system owns cascade resolution, storage, and the inspector UI. Per-dimension defaults belong to tested settings profiles, not to hardcoded constants in this canonical layer.

## 20. Events

Anchor: `artifact.events`

### 20.1 Event Vocabulary

Every committed entity-relevant input change, mutation, or query emits a typed event through the canonical event bus per `run.event-stream` (File 04 §23.2) with the standard envelope. Pure read-time recomputation of derived lifecycle, validation, or claim status does not emit events by itself; events emit when a committed block, edge, version-graph action, ledger fact, or settings change causes a visible projection change. The canonical entity-relevant events:

**Artifact events:**

- `ArtifactCreated { artifact_id, artifact_kind, producing_run_id, scope }`
- `ArtifactVersionCommitted { artifact_id, version_id, prior_version_id, produced_by_run_id, produced_by_capability_id }`
- `ArtifactReviewStateChanged { artifact_id, version_id, old_state, new_state, actor }`
- `ArtifactLifecycleChanged { artifact_id, version_id, old_lifecycle, new_lifecycle, reason }`
- `ArtifactValidationStateChanged { artifact_id, version_id, old_state, new_state, validation_block_id }`
- `ArtifactMaterializationPolicyChanged { artifact_id, old_policy, new_policy }`
- `ArtifactScopePromoted { artifact_id, old_scope, new_scope, promotion_record_block_id }`
- `ArtifactArchived { artifact_id }`
- `ArtifactRestored { artifact_id, restored_to_lifecycle }`
- `ArtifactDiscarded { artifact_id }`
- `ArtifactExternallyEdited { artifact_id, version_id, source: "filesystem_watcher" | other }`
- `ArtifactVersionHardDeleted { artifact_id, version_id, reason }`
- `ArtifactHardDeleted { artifact_id, reason }`
- `ArtifactExported { artifact_id, bundle_block_id, includes_provenance }`
- `ArtifactMaterialized { artifact_id, version_id, materialized_paths }`
- `ArtifactMaterializedLocally { artifact_id, version_id, local_paths }`

**Claim events:**

- `ClaimPublished { claim_id, claim_kind, confidence_class, scope, anchor_block_id }`
- `ClaimStatusChanged { claim_id, old_status, new_status, derivation_reason }`
- `ClaimStatusOverridden { claim_id, new_status, reason, actor }`
- `ClaimWithdrawn { claim_id, reason, actor }`
- `ClaimSuperseded { prior_claim_id, new_claim_id, derivation_summary }`
- `ClaimAutoExtracted { claim_id, source_block_id, extractor_model_id, model_request_template_id }`
- `ClaimReviewCompleted { claim_id, decision, reviewer_id }`

**Evidence events:**

- `EvidenceLinkAttached { supporting_block_id, supported_target_id, relation, confidence_class }`
- `EvidenceLinkDetached { supporting_block_id, supported_target_id, relation }`
- `ContradictionDetected { claim_id, refuting_block_id, supporting_block_id, confidence_comparison }`

**Citation events:**

- `CitationCaptured { citation_block_id, reference_kind, captured_by_run_id }`

**Observation events:**

- `ObservationCommitted { observation_block_id, observation_kind, observation_subject }`
- `ObservationStalenessDetected { observation_block_id, current_fingerprint, captured_fingerprint }`

**Validation events:**

- `ValidationStarted { target_id, validation_kind, validator_reference }`
- `ValidationCompleted { target_id, validation_block_id, outcome, latency_ms }`

**Critique events:**

- `CritiquePublished { critique_block_id, target_id, critique_kind, finding_count, recommended_action }`

**Provenance events:**

- `ProvenanceQueryExecuted { query_kind, target_id, result_size, truncated }` — recorded at lower verbosity by default; used for analytics and replay
- `ProvenanceCacheInvalidated { cache_key, invalidation_reason }` — internal observability event

### 20.2 Event Sensitivity

Entity events carry the canonical `sensitivity` tag per `run.event-stream` (File 04 §23.2). Most events are `Public`. Events that touch `Secret`-sensitivity blocks (e.g., a citation to a credentials file, an observation containing raw secrets) are `Sensitive`; raw secret payloads in flight remain `Secret` per `run.event-stream` (File 04 §23.2) and are never persisted to the durable ledger.

### 20.3 Boundary

This file specifies the event vocabulary and per-event payload shape. The event-bus implementation (delivery semantics, subscription mechanics, replay) is owned by `run.ledger-events-commits` (File 04 §23) and File 10.

## 21. Explicit Rejections

Anchor: `artifact.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel artifact registry or parallel claim registry separate from the block pool — there is one block pool (per File 08); artifacts are entities over `Artifact`-kind blocks; claims are `Claim`-kind blocks; no second pool
- a separate evidence storage layer outside the block-graph edge set — evidence is structured through `Evidence` blocks and edge-typed `EvidenceLink` metadata; introducing a parallel evidence database corrupts the unified graph
- mutable artifact content carried on the entity record — content lives in the version-block per File 08; the entity record carries metadata, never content
- mutable artifact lifecycle, review, or validation state stored on the entity record — these are derived per-`ContextVersion`; storing them on the entity row would force re-writes on every version transition and break replay determinism
- claims as anonymous text fragments — every `Claim` has stable identity (`claim_id`), explicit confidence class, and status derived or overridden through projection records; free-floating claim-like text in `MessageAssistant` blocks is not a `Claim` entity
- evidence chains without typed relations — every evidence link carries an `EvidenceRelation` (canonical or registered extension); untyped `cites` edges that purport to support a claim are an Explicit Rejection
- closing the `EvidenceRelation` set to support/refute only — the closed canonical set includes `Contextualizes`, `Corroborates`, `Summarizes`, `Derives`, `Witnesses`, `IllustratesByExample` because the design space genuinely contains these relations; a too-narrow set forces evidence into misclassification
- a single numerical confidence score as the only policy signal — `ConfidenceClass` is the policy-grade enum; numerical scores are fixed-point ranking metadata (§6.15); policy decisions never read the numerical score in isolation
- observations without staleness fingerprints when the observation backs a mutation — capabilities whose mutation depends on a prior observation must consume the observation's `staleness_fingerprint` and revalidate currency per `run.call-pipeline` (File 04 §8.2); observations with no fingerprint are valid as evidence but cannot back mutations
- silent claim-status changes caused by committed substrate changes — when a committed block, edge, action-log record, or settings change alters visible status, a `ClaimStatusChanged` event emits with the derivation reason; pure read recomputation is not an event source
- silent evidence-link removal without a recorded event — every link removal emits `EvidenceLinkDetached`; compaction never silently removes evidence-link edges
- automatic claim extraction enabled by default — auto-extraction is opt-in per scope; default off; explicit user enablement required
- treating provenance as a stored entity — provenance is a derived query surface; storing provenance results as durable rows creates a parallel ledger and is rejected
- hardcoded provenance query results not derived from the canonical substrates — every provenance query returns results derived from blocks, edges, versions, runs, and ledger entries; surfaces that fabricate provenance content are invalid
- artifact versions that mutate the prior version-block in place — versions are sibling blocks linked by `supersedes` per File 08; in-place mutation is an Explicit Rejection at the block layer and is re-rejected here
- artifact identity tied to a specific materialization path — the path is per-version metadata; renaming the materialized file does not change the artifact's identity, only its current materialized path
- artifact lifecycle transitions driven by time rather than explicit actions — time-based transitions are forbidden (per File 01 constraint); retention policies invoke explicit `archive` operations driven by their own logic
- time-based citation freshness as a correctness condition — source currency is based on fingerprints, validators, explicit refresh, and consuming-workflow requirements; retention timing is storage policy only
- `Critique` blocks contributing to `ValidationState` derivation — critiques are advisory; only `Validation` blocks contribute to validation state
- claim-publish capability lifting `permission_floor: Denied` claims (none currently exist canonically) without typed-confirmation — the floor enforcement from `policy.permission-floor-typed-confirmation` (File 06 §7) applies; no entity capability bypasses the floor
- hard-delete floors that weaken for discarded or only-version artifacts — those states may change warnings and typed-confirmation text, but not the denied floor
- silent automatic claim status promotion to `Supported` without meeting the configured `claim.evidence_threshold` — derivation rules are deterministic; settings define the threshold; surfaces never override the derivation without an explicit override record
- contradiction detection that suppresses the contradiction silently — `ContradictionDetected` events emit when stronger refuting evidence is committed; equal-confidence conflicts resolve to `Unresolved` and emit the corresponding status-change event
- entity capabilities operating outside the canonical event bus — every entity transition emits the appropriate canonical event; surfaces and policy consume the events; no entity capability has a private out-of-band notification channel
- claim entities anchored to `MessageUser` blocks the user did not author — anchors must reference the actual originating block; misattribution is invalid
- materializing `InWorkspace` artifacts outside the workspace root — materialization paths are constrained to the workspace per the security boundary in the file-management contract
- preserving any earlier name for the same primitive as a parallel system — `Artifact` (entity) supersedes any earlier "deliverable record" / "produced output entity" / "work product registry"; `Claim` supersedes any earlier "assertion record" / "knowledge claim" / "agent answer entity"; `Provenance` (derived view) supersedes any earlier "lineage record" / "audit chain table" / "origin trace store"; `EvidenceLink` supersedes any earlier "support edge type" / "citation relation column"; none of those earlier names survive as parallel primitives
- treating `Artifact` and `Memory` as the same primitive — memory entries are `Memory`-kind blocks per File 08; the Memory subsystem owns memory salience, decay, recall, consolidation; artifacts are entity-level identifiable produced outputs; the two may compose (a memory entry may cite an artifact) but they are distinct
- treating `Claim` and `Memory` as the same primitive — a memory entry may consolidate one or more claims into long-term knowledge, but a claim has its own identity, status, and confidence; collapsing them removes claim-level status tracking
- treating `Claim` and `MessageAssistant` as the same primitive — most assistant utterances are not load-bearing claims; explicit publication is required for an utterance to become a `Claim` entity
- treating `Evidence` and `Citation` as the same primitive — citations are typed source references; evidence is the structured assertion that the source supports a claim; the two compose but are distinct kinds
- treating `Observation` and `Citation` as the same primitive — observations are first-party captures (the system observed this); citations are references to external sources; the two compose (a citation may reference an observation) but are distinct kinds

## 22. Consequences for Later Specs

Anchor: `artifact.consequences-for-later-specs`

Later specs must follow these rules:

- The execution ledger, event stream, and hooks spec must record entity-relevant events through the canonical envelope, link ledger rows to `artifact_id`, `version_id`, `claim_id`, and `evidence_link_edge_id` where applicable, and not duplicate entity content; ledger rows reference entities, never carry their content.
- The version graph, commits, and projections spec must store per-version action logs that drive `ArtifactLifecycle`, `ReviewState`, and `ValidationState` derivation per §5 and §14.2; per-version diffs must include artifact-version commits, evidence-link edge commits, and review-state changes alongside block lifecycle and pin changes; the materialized view must support the derivation rules deterministically.
- The retrieval, indexing, and knowledge-base spec must treat `Claim`, `Evidence`, `SourceExcerpt`, `Citation`, and `Observation` blocks as first-class retrieval targets; claim retrieval must surface confidence class and status; evidence retrieval must surface the relation type; knowledge-base entries may cite claims and artifacts through the canonical edges.
- The context assembly and compaction spec must preserve evidence-set closure for `Supported` and `Validated` claims and artifacts by default per §11.5; compaction must invoke explicit block-lifecycle operations on supporting blocks rather than silently severing evidence chains; per-policy preservation rules belong to the compaction spec but must respect the canonical preservation requirement here.
- The memory spec must treat memory entries that consolidate one or more claims as `consolidates`-edge-linked to the source claim blocks; memory promotion of a claim must preserve the claim's identity and confidence class.
- The model strategy, profiles, and selection spec must allow per-claim-confidence-class model selection (e.g., low-confidence claim publication may use a cheaper model, high-confidence requires the user's primary model).
- The provider layer, rate limits, and usage accounting spec must record per-call provider/model attribution that the provenance layer consumes through `provenance.query_replay_trace`.
- The world model and state-awareness spec must treat artifacts, claims, and observations as part of the world state available to agents; the available-capability set must filter entity capabilities based on the entity catalogue (e.g., `artifact.commit_version` requires the artifact entity to exist).
- The perception and observation pipelines spec must produce `Observation` blocks conforming to §13's contract (kind, payload, staleness fingerprint) and route observations through the canonical `observation.commit` path for cross-surface/subsystem inspection.
- The storage and persistence spec must store the entity-record field sets, the version metadata records, the evidence-link edge metadata, the materialized-paths records, and the tombstone rows per the contracts in §18; it must rebuild derived state (lifecycle, status, evidence-set closure) deterministically from the source action log and graph.
- The sync, import, export, and data portability spec must preserve artifact identity, claim identity, evidence-link relations, and provenance chains across export and import; imported entities receive `Import` producer records per `block.block` (File 08 §2.2) and continue to participate in provenance queries through the cross-installation identity mapping (File 21).
- The security, credentials, and trust boundaries spec must treat `Secret`-sensitivity citations, observations, and evidence with the same redaction discipline `block.sensitivity` (File 08 §9) establishes for `Secret` blocks; raw secrets in observations must be redacted at commit.
- The sandbox, process control, and isolation spec must commit `Observation` blocks (per §13) for sandboxed-process snapshots that capability runs depend on for revalidation per `run.call-pipeline` (File 04 §8.2).
- The workspaces and materialization spec must implement the `InWorkspace` materialization path-resolution algorithm and the disk→entity sync loop per §7.3 and §7.5.
- The work surface contract spec and the per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) must declare which `ArtifactKind`s and `ObservationKind`s they primarily produce, and must register any `Custom` extension kinds through the canonical mechanism; their `SubsystemSurfaceSpec` declarations (per `surface.subsystem-surface-spec`, File 07 §5) must include the relevant artifact-producing and observation-committing capabilities.
- The automation and triggers spec must use artifact and claim entities as automation triggers (e.g., "when a new `Validation`-failed artifact commits, run X") and produce artifacts and claims as automation outputs through the canonical capabilities.
- The workflows, templates, and reuse spec must treat `WorkflowTemplate` artifacts as the canonical workflow-template store; workflow node outputs that warrant durable identity become artifact versions; per-step evidence becomes `Evidence` blocks linked to the workflow's output claim or artifact.
- The extension and plugin system spec must allow plugin-registered `Custom` artifact kinds and `Custom` observation kinds through the proposal-first registration mechanism; the registered kinds participate in the canonical entity layer the same way built-in kinds do.
- The MCP and external integrations spec must route MCP-sourced citations and observations through the canonical `citation.capture` and `observation.commit` paths; MCP-server-hosted artifacts use `ExternalRef` materialization with the `McpResource` reference kind.
- The UI shell, layout, presentation, and interaction models spec and the UI customization, widgets, and theming spec must render artifacts, claims, evidence, citations, observations, validations, critiques, and provenance results through canonical data contracts; no UI surface may invent a parallel entity shape.
- The quality control and validation spec must register validators as `Validator`-kind artifacts (or as built-in capabilities), produce `Validation` blocks per §14, and integrate with the `run.termination` (File 04 §22) completion-verification hook surface.
- The evaluation and benchmarking spec must consume artifact, claim, and evidence data as evaluation targets and as evaluation grounds; benchmarks that test factuality consume claims and their evidence sets.
- The telemetry, logging, and observability spec must consume entity-relevant events for monitoring; analytics over artifact-creation rates, claim-status distributions, evidence-link-confidence distributions, and provenance-query latency are first-class observability concerns.
- The runtime infrastructure and lifecycle spec must orchestrate startup-time registration of canonical artifact kinds, the `Claim` block-kind extension, canonical evidence relations, canonical citation reference kinds, canonical observation kinds, and the canonical entity capabilities.
- The packaging, platform, and distribution spec must ship built-in declarations for every canonical entity capability, the canonical artifact kinds, the canonical observation kinds, the canonical evidence relations, and the canonical citation reference kinds; these declarations ship in every ATLAS3 install as the `Builtin` source.

## 23. Canonical Rule Anchors

Anchor: `artifact.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `artifact.chosen-model`, `artifact.boundaries-with-adjacent-layers`, `artifact.artifact`, `artifact.artifact-kind`, `artifact.artifact-lifecycle-states`, `artifact.artifact-lifecycle`, `artifact.review-state`, `artifact.per-version-vs-per-entity-derivation`, `artifact.artifact-version`, `artifact.version-creation`, `artifact.artifact-materialization`, `artifact.materialized-paths-provenance`, `artifact.disk-entity-sync`, `artifact.artifact-tombstones`, `artifact.tombstone-fields`, `artifact.claim`, `artifact.claim-status`, `artifact.claim-extraction`, `artifact.evidence`, `artifact.citation`, `artifact.observation`, `artifact.validation-critique`, `artifact.validation-state-derivation`, `artifact.provenance`, `artifact.capability-surface`, `artifact.capability-metadata-declarations`, `artifact.cross-surface-interoperability`, `artifact.per-surface-projections`, `artifact.persistence-contract`, `artifact.settings`, and `artifact.events`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
