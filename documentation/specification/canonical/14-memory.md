# Memory

## Status

Canonical.

## Scope

This file defines:

- `Memory` as the always-available substrate service that stores learned state about the user, workspaces, preferences, procedures, commitments, mastery, and contextual facts
- the Memory-owned tier model: `CoreMemory` and `ArchivalMemory`
- `MemoryEntry` as the entity layer over `Memory`-kind blocks
- memory kinds, scopes, facets, provenance, confidence, salience features, validity, and retention policy
- explicit memory commands, implicit learning, proposal review, grounded update, and consolidation behavior
- memory retrieval as a consumer of File 12's retrieval substrate
- memory assembly as a consumer of File 13's model-request assembly contract
- natural memory use, inspectability, privacy, sensitivity, and user controls
- the memory capability families, custom event families, background work expectations, and settings dimensions

This file does not define:

- block schema, block lifecycle states, block content variants, or block commit validation; File 08 owns those
- claim, evidence, citation, artifact, and provenance identity; File 09 owns those
- execution ledger schema, event envelopes, hook dispatch, or background-worker mechanics; File 10 owns those
- version graph commits, materialized views, or lifecycle action logs; File 11 owns those
- retrieval indexes, chunking, embedding, graph projection storage, or ranking algorithms; File 12 owns those
- model-request assembly, context compaction, conversation-history management, or router context policy; File 13 owns those
- capability declaration fields, policy evaluation, approval UI, leases, or tool-surface loading; Files 05-07 own those
- model selection, provider failover, storage schema, sync, UI layout, or exact settings defaults

## Source Resolution

This file resolves memory, learning, context, retrieval, and self-improvement source material into one boundary: Memory stores durable learned state. It does not become a workspace-first surface, a model-request injection layer, a conversation-history manager, a private retrieval stack, or a parallel event/capability system.

Resolved design:

- Memory is one cross-cutting substrate service per File 01, always available to work surfaces but not shaped like a workspace-first surface.
- Memory entries are entity metadata over `Memory`-kind blocks. The block carries durable content; the entity carries memory-specific management state.
- Memory owns core and archival memory. Recent conversation turns are conversation history, managed by Files 12 and 13.
- Memory learning uses explicit user commands and policy-governed distillation proposals. Raw run history remains in the ledger.
- Memory retrieval reuses File 12 indexes and result contracts, adding memory-specific ranking signals through score-attributed policy.
- Memory contributes assembly sources to File 13. It never injects hidden instructions or bypasses authority, sensitivity, or budget rules.

## 1. Chosen Model

Anchor: `memory.chosen-model`

ATLAS3 has one Memory substrate.

Memory stores curated learned state that should survive beyond the immediate conversation. It is not raw transcript, not a knowledge base, not an instruction file, not a graph database, and not a private model-request layer.

Memory-owned tiers:

- `CoreMemory` - small, high-priority, editable memory blocks normally eligible for early model-request assembly.
- `ArchivalMemory` - durable indexed memory records searched on demand through the shared retrieval substrate.

Recent conversation turns are not a Memory tier. They are conversation blocks in the active materialized view, assembled through File 13's `ConversationHistory` region and searchable through File 12's `conversation:<conversation_id>` namespace. Memory may read those blocks as sources for learning when policy allows, but it does not own a sliding-window transcript store or recall index.

Memory is always integrated. Every work surface can read from and contribute to it through registered capabilities and policy. No surface receives a private memory model.

## 2. Adjacent Boundaries

Anchor: `memory.adjacent-boundaries`

### 2.1 Blocks

File 08 declares `Memory` as a block kind. A memory's durable content lives in a `Memory`-kind block. `MemoryEntry` is the entity layer over that block: it adds stable identity, scope, kind, provenance, salience features, validity, conflict state, and management metadata.

Observable memory edits create new blocks or versioned records according to Files 08 and 11. In-place mutation of block content is invalid.

### 2.2 Retrieval

Memory records are source records for File 12. Lexical, vector, graph, metadata, and structural indexes over memory are rebuildable projections, not memory identity.

Memory retrieval returns normalized `RetrievalHit` / `MemoryHit` results. It may add memory-specific ranking signals, but the retrieval substrate, indexes, namespaces, redaction rules, and graph projection contracts remain File 12 concerns.

### 2.3 Context Assembly

Memory outputs enter model requests as assembly parts under File 13.

Core memory has high priority and should normally fit because it is small by profile design. This is a governance rule, not a routine budget tradeoff: core memory is still subject to sensitivity gates, authority validation, provider constraints, and extreme model-window limits. Settings profiles should give core memory enough region priority that omission occurs only under extraordinary constraints.

Archival memories enter the `RetrievedContext` region when selected by retrieval or policy. Memory-derived instruction/profile proposals enter File 13 only as attributed `InstructionSource` blocks or equivalent approved sources; Memory itself does not inject hidden instruction text.

### 2.4 Execution, Capabilities, Policy, and Surfaces

Memory operations are capabilities registered through File 05, evaluated through File 06, exposed through File 07, executed through File 04, and recorded through File 10.

Memory-specific capability handlers do not implement private approval logic. Memory writes, deletes, exports, imports, consolidation, and derived instruction/profile proposals go through the shared capability and policy systems.

## 3. `MemoryEntry`

Anchor: `memory.memory-entry`

### 3.1 Definition

A `MemoryEntry` is the stable entity identity for one learned memory over one or more `Memory`-kind blocks.

The block is the content carrier. The entity is the management and retrieval identity.

### 3.2 Required Fields

A `MemoryEntry` must carry:

- `memory_id` - stable identifier, never reused
- `block_id` - current `Memory` block carrying the active content
- `kind` - `MemoryKind`
- `scope` - `MemoryScope`
- `facets` - typed optional facets used for retrieval, validity, and management
- `provenance` - `MemoryProvenance`
- `confidence` - confidence in the memory's current content
- `salience_features` - policy-readable feature values used by ranking and consolidation
- `validity` - whether the memory is current, time-bounded, stale, unresolved, contradicted, or source-limited
- `retention_policy` - whether the memory is durable, time-bounded, user-pinned, review-needed, or cleanup-eligible
- `conflict_state` - conflict projection when known
- `created_at` and `updated_at`
- `revision` - monotonic revision over the entry's in-place-mutable metadata; mutation goes only through a precondition-checked path that fails typed on staleness
- `entity_schema_version`

The entity may cache safe descriptions, derived summaries, or display labels, but those are projections. Durable memory content remains in the block.

### 3.3 Non-Identity Projections

The following are projections or policy-retained telemetry, not required identity fields:

- retrieval counts
- last retrieved time
- ranking strength
- embedding vectors
- graph entities and relationships
- index rows
- UI grouping state
- exact token counts

When retained, these values must be keyed by the policy, model, tokenizer, source version, or retrieval profile that produced them.

## 4. Kinds, Scopes, and Facets

Anchor: `memory.kinds-scopes-facets`

### 4.1 `MemoryKind`

Canonical memory kinds:

- `Preference` - stable or contextual user preference
- `Fact` - learned factual statement about the user, workspace, or operating context
- `Context` - situational or temporal context, including events, deadlines, active projects, and temporary circumstances
- `Pattern` - repeated behavior, tendency, or observed recurring structure
- `Style` - communication, formatting, visual, writing, or interaction style
- `Procedure` - learned way of doing something
- `Commitment` - promise, plan, deadline, follow-up, or obligation the system should track
- `Mastery` - learning state, concept mastery, misconception, SRS-relevant progress, or teacher-facing competence signal
- `Custom { namespace, name }` - registered extension

Kinds are behavioral categories. Scope is not encoded into kind. A global user fact and a workspace fact are both `Fact` at different scopes.

Relationship-like content is represented as a `Fact` or projected into File 12 entity-relationship records by an extraction capability. `Relationship` is not a flat memory kind.

Time-bound events are `Context` with temporal facets. `Event` is not a separate memory kind.

### 4.2 `MemoryScope`

Canonical memory scopes:

- `Global`
- `Workspace { workspace_id }`
- `Conversation { conversation_id }`
- `Custom { namespace, id }`

Task- or intent-thread-scoped memories may be represented through `Custom` or a future scope extension only when they are durable learned state. Transient task/run state remains in Files 02 and 04.

ATLAS3 is local-first single-user software. Memory scope is not `user_id`-based unless a future profile/sync spec introduces multi-profile identity.

### 4.3 Facets

Facets add structure without forcing every memory into a large schema.

Useful facets include:

- subject
- topic tags
- temporal fields: `when`, deadline, recurrence, valid-from, valid-until
- source authority
- extraction method
- source language or modality
- optional 5W1H fields: who, what, when, where, why, how
- confidence contributors
- sensitivity and redaction hints
- freshness requirements

Facets are typed. Prose-only facets are insufficient for policy-critical behavior.

Spaced-repetition scheduling is expressed through these temporal facets, not a separate scheduler: a `Mastery` memory's next-review time and review cadence are `when` and recurrence facets. A card scheduled for a future review is an active memory whose validity stays current; a pending next-review time is not an expiration and must not be treated as stale-toward-cleanup.

## 5. Core Memory

Anchor: `memory.core-memory`

Core memory is the high-priority memory subset intended to shape ordinary interaction without search.

Core memory blocks are:

- small by profile policy
- directly inspectable and editable through memory management surfaces
- source-attributed
- governed by File 13 assembly, sensitivity, authority, and budget rules
- configured through profiles and settings rather than fixed canonical labels

Core memory labels such as persona, human, workspace, project, communication style, or active commitments may be useful profile seeds, but they are not a hardcoded canonical set.

Core memory is not governing instruction text, not hidden instruction text, and not guaranteed to render in every model request. When omitted, redacted, externalized, or summarized, the assembly snapshot records the reason.

## 6. Archival Memory

Anchor: `memory.archival-memory`

Archival memory is durable learned state not normally assembled unless retrieved or selected by policy.

Archival memory:

- is stored as `Memory` blocks plus `MemoryEntry` metadata
- is indexed through File 12 namespaces such as `memory:<scope_id>`
- supports lexical, vector, graph, metadata, and structural projections as configured
- is retrieved progressively: compact hit first, expansion on demand
- remains inspectable and editable by the user

Indexes over archival memory are rebuildable from blocks and entity records. Loss or corruption of an index must not destroy memory content.

## 7. Validity, Retention, and Short-Term Memory

Anchor: `memory.validity-retention-short-term-memory`

Memory may be durable or time-bounded.

A time-bounded memory is still a normal memory entry, but its `validity` or `retention_policy` includes a semantic expiration condition such as "until exam date", "until project launch", or an explicit timestamp.

Expiration is a validity rule, not a polling correctness rule. After expiration:

- retrieval and assembly treat the memory as expired or stale by default
- the system may surface a cleanup proposal
- a maintenance worker may mask, drop, archive, or supersede the memory through normal capability and version rules
- hard deletion never happens silently

Example: "I have an exam on June 10; help me focus on exam prep until then" can create a `Context` or `Commitment` memory with `valid_until = 2026-06-10`. After that date it should not keep shaping normal responses unless the user extends or recovers it.

Settings decide whether expired memories are hidden, searchable only with archived/stale filters, proposed for cleanup, or automatically dropped from active memory projections.

## 8. Learning and Extraction

Anchor: `memory.learning-extraction`

### 8.1 Learning Paths

Memory has two learning paths:

- explicit memory commands, where the user directly asks the system to remember, forget, update, or recall something
- implicit learning, where the system proposes or commits memory based on conversations, actions, observations, outcomes, and tool results under policy

Explicit commands can create direct proposals or commits. Implicit learning must pass through extraction and distillation so raw conversation noise does not become durable memory.

### 8.2 Distillation Pipeline

The implicit learning pipeline should:

1. identify eligible source blocks or ledger facts
2. exclude ineligible sources by authority, sensitivity, recursion, or policy
3. classify whether the source contains meaningful learning or should be skipped
4. distill candidate memories by kind, scope, confidence, provenance, facets, and retention
5. compare candidates against existing memories
6. produce grounded `Add`, `Update`, `Delete`/`Forget`, or `None` decisions
7. route write proposals through capability policy
8. commit accepted changes as blocks and entity updates

Success and failure should distill differently. Successful work can produce procedures, preferences, or patterns. Failed work can produce warnings, anti-patterns, corrected approaches, or user-specific constraints.

### 8.3 Grounded Update Protocol

Memory updates use the 4-operation protocol:

- `Add`
- `Update`
- `Delete` / `Forget`
- `None`

The model must not invent target memory ids. When an update or delete decision is possible, the runtime supplies a bounded candidate set and maps real memory ids to temporary local identifiers in the model request. The model selects from that set. The runtime resolves the local identifier back to the real `memory_id`, validates it, and applies the mutation through revision-safe capability calls.

Updates carry an expected revision or equivalent precondition. Conflicting concurrent edits fail or rebase through an explicit policy path. Silent last-write-wins is invalid.

### 8.4 Proposal Policy

Extraction can produce proposals or direct commits depending on policy.

Policy may:

- require user review for all writes
- auto-commit selected low-risk categories
- batch proposals
- pause extraction for sensitive contexts
- disable implicit extraction while keeping explicit `remember` available
- require typed confirmation for deletion, export, or broad-scope promotion

File 14 does not define default values for these choices.

### 8.5 Recursion Prevention

Memory extraction must distinguish source authority.

Existing memory content included in a model request is not eligible as a new memory source unless the current turn adds new evidence. Retrieval snippets, web content, tool outputs, assistant summaries, and instruction sources each carry their own authority and extraction eligibility.

Memory must not self-amplify by re-memorizing memory-injected content.

## 9. Retrieval and Use

Anchor: `memory.retrieval-use`

### 9.1 Progressive Retrieval

Memory retrieval returns compact hits first.

A memory hit should carry:

- `memory_id`
- `block_id` or source ref
- kind, scope, sensitivity, and validity
- snippet or safe description
- provenance summary
- score attribution
- expansion handle
- redaction or omission state when applicable

Full memory content, source conversations, claim/evidence records, or related graph context are fetched only when the model, UI, or user requests expansion and policy permits it.

### 9.2 Ranking Signals

Memory ranking may combine:

- lexical relevance
- dense similarity
- graph proximity
- scope match
- source authority
- confidence
- salience features
- freshness and validity
- recurrence or commitment urgency
- user-pinned or protected state
- retrieval reinforcement
- custom registered signals

Combination policy is configurable and must be score-attributed. The canonical spec does not fix weights, top-k values, half-lives, rerank thresholds, or formulas.

### 9.3 Reinforcement and Usage

Retrieval reinforcement is optional policy-governed telemetry.

If a retrieval affects future ranking, the system must record the signal in a sensitivity-aware, inspectable, and policy-controlled way. It must not persist secret query text or hidden private model-request content.

## 10. Salience and Strength

Anchor: `memory.salience-strength`

Memory salience is represented by feature inputs, not a single canonical formula.

A default salience feature set may include:

- novelty
- relevance
- emotional or preference intensity
- predictive usefulness

Other features may be registered by profiles or subsystems. The active ranking/consolidation policy computes strength at query or maintenance time and records score attribution when strength affects behavior.

Strength is not stored as an unqualified mutable scalar on the memory entity.

## 11. Provenance, Confidence, and Conflict

Anchor: `memory.provenance-confidence-conflict`

Every memory must have provenance.

`MemoryProvenance` should record:

- source refs: message, block, ledger entry, file, tool result, observation, import, explicit command, or external source
- source authority
- extraction method
- actor: user, assistant, subsystem, automation, import, or plugin
- confidence and confidence contributors
- sensitivity and redaction state
- freshness requirements

Factual memories may publish or reference File 09 claims/evidence when useful; a memory that consolidates a claim must preserve that claim's identity and confidence class per File 09. Preference, style, procedure, commitment, and mastery memories do not need to become claims by default, but still need provenance.

Conflict handling:

- claim-like conflicts use File 09 semantics when applicable
- memory-local conflict state is a management projection
- equal-strength contradiction is unresolved, not silently overwritten
- resolution creates explicit records and may supersede, keep both, narrow scope, lower confidence, or ask the user

## 12. Consolidation

Anchor: `memory.consolidation`

Consolidation maintains memory quality. It may:

- merge duplicates
- supersede stale or contradicted memories
- lower confidence or mark stale
- drop expired or low-value memories from active projections
- create summaries or richer memories from several sources
- promote one or more claims into consolidated memory, preserving each source claim's identity and confidence class and linking the memory to the source claim blocks through a `consolidates` edge per File 09
- propose scope changes
- reinforce useful memories
- mark cleanup candidates

Consolidation is not hidden deletion. It writes through the block, version, capability, policy, and ledger systems.

Consolidation may be triggered by user action, source events, thresholds, policy decisions, app lifecycle events, or scheduled background workers. Time-based schedules are convenience triggers, not correctness conditions. The system must remain correct if a scheduled consolidation never runs.

Consolidation scope and disposition are orthogonal preset dimensions. The bounded single-conversation preset remains the default. A broad preset is opt-in and selects its scan scope from the closed vocabulary `Conversation { conversation_id } | Conversations { conversation_ids } | Workspace { workspace_id } | Global`; `Conversations` is non-empty and duplicate-free. A preset selecting multiple conversations, a workspace, or global memory has disposition `proposal_only`; no inherited or broader `auto_apply` setting may widen that disposition.

A broad sweep creates one durable `MemoryConsolidationProposal` for each surviving candidate and groups the records by `sweep_id`. Each proposal carries `proposal_id`, `sweep_id`, the selected scope, a typed proposed consolidation operation, the target `memory_id` values with their expected revisions, a proposed replacement or delta reference, provenance, rationale, sensitivity, source-run and source-automation references when present, creation and resolution facts, and `status` from the closed vocabulary `Pending | Accepted | Rejected | Stale`. Acceptance revalidates every expected revision. Drift of any target revision transitions the proposal to `Stale` and commits no mutation against the changed target.

A proposal is not memory truth before acceptance. `Pending`, `Rejected`, and `Stale` proposal records are excluded from ordinary memory recall, model-request assembly, and memory indexes; only the mutation produced by an accepted proposal enters those paths. Batch review groups proposals without coupling their outcomes.

Broad-sweep production resolves finite candidate-count, page-size, and review-batch bounds through settings and deduplicates equivalent pending proposals within a sweep and across repeated sweeps. After producing one or more pending proposals, an automation parks `AwaitingUser` with a batch-review elicitation. The parked run is orchestration state, not the durable source of truth for any proposal.

When consolidation rewrites, merges, supersedes, exports, broadly promotes, or removes user-visible memory, it follows File 06 policy and approval rules.

## 13. Natural Use and Inspectability

Anchor: `memory.natural-use-inspectability`

Memory should feel natural in ordinary assistant text. The assistant should not gratuitously frame normal answers as database retrieval or say "based on your stored memories" when simple contextual phrasing is better.

Attribution is allowed and sometimes required:

- when the user asks what is remembered
- when the user asks why an answer was personalized
- when editing, deleting, or resolving memory
- when memory confidence or freshness is uncertain
- when policy or UI requires inspectability

Natural use is not permission to hide influence. The user must be able to inspect, correct, disable, export, import, and delete memories, and to see which memories materially influenced an answer when the system records that influence.

Exact phrase bans, validators, and fail directions are quality-control/settings concerns, not hardcoded canonical text.

## 14. Memory-Derived Instructions, Profiles, and Skills

Anchor: `memory.memory-derived-instructions-profiles-skills`

Memory may inform future behavior, but it does not own hidden instruction injection.

If a learned preference, style, procedure, or pattern should guide future model behavior as an instruction, profile, workflow, skill, or reusable knowledge entry, Memory may propose that object through the appropriate layer. The resulting object must carry source attribution, authority, sensitivity, and policy approval.

Memory stores learned signals. Instruction sources instruct. Workflows orchestrate. Knowledge entries provide reference content. These are connected but separate primitives.

## 15. Knowledge Base and Graph Relationship

Anchor: `memory.knowledge-base-graph-relationship`

Memory and Knowledge Base differ by semantic role.

Knowledge is curated reference content the agent may cite, study, or retrieve. Memory is learned state about the user, workspace, preferences, procedures, commitments, mastery, and context. The same interaction can produce both.

Entity-relationship extraction is producer-populated. Memory may register extraction capabilities that project memory-derived entities and relationships into File 12's shared graph projection. Memory does not own the graph store, graph query algorithm, graph UI, or universal entity taxonomy.

Relationship-like memories can be represented as facts and also projected into File 12 records when useful.

## 16. Capability Families

Anchor: `memory.capability-families`

Memory must register capabilities through the canonical registry. Exact declarations belong to File 05-compatible capability specs, but the memory subsystem must cover these operation families:

- recall, search, read, and inspect
- explicit remember and forget
- proposal create, review, accept, reject, modify, and batch resolve
- memory add, update, supersede, merge, drop, recover, and hard-delete request
- core memory read and edit
- extraction and distillation
- consolidation and cleanup
- conflict detection and resolution
- scope promotion or narrowing
- import, export, and materialization
- history, provenance, and influence inspection

All memory capabilities declare touched resources, sensitivity, replay class, reversibility, output block kinds, event kinds, concurrency, cancellation behavior, and postconditions through File 05.

Write-like memory capabilities route through File 06. Hard deletion and secret/sensitive export require the strongest applicable confirmation path.

## 17. Events, Ledger, and Background Work

Anchor: `memory.events-ledger-background-work`

Memory emits events through File 10.

Memory-specific events and ledger entry kinds are `Custom { namespace, name, payload }` extensions under the `memory` namespace. File 14 reserves the namespace and expected event families; it does not add memory kinds to File 10's closed canonical catalogue.

Expected event families include:

- memory proposal lifecycle
- memory creation, update, supersession, drop, recovery, and deletion request
- retrieval execution
- extraction and distillation lifecycle
- consolidation lifecycle
- conflict detection and resolution
- core memory modification
- import, export, and materialization
- influence inspection

Consequential memory facts commit to the ledger. Live UI events are not the source of truth.

Background memory work, including extraction, distillation, consolidation, import/export, indexing coordination, and graph projection, is an execution unit governed by File 04. It must be cancellable as part of its parent run/subsystem and individually when exposed as an active process. Staged outputs commit only at safe proposal or commit boundaries.

## 18. Privacy, Sensitivity, and User Control

Anchor: `memory.privacy-sensitivity-user-control`

Memory content defaults to the sensitivity implied by its source. User-private context usually produces `Sensitive` memory. Raw secrets must not be stored in memory content, descriptions, indexes, events, exports, or telemetry.

Users must be able to:

- inspect memories
- search and filter memories
- edit memory content, kind, scope, facets, validity, and retention where policy allows
- pause or disable implicit extraction by scope
- keep explicit remember/forget available independently of implicit extraction
- review, batch-resolve, or auto-policy memory proposals
- delete or recover memories through non-destructive mechanisms
- request hard deletion through typed confirmation when allowed
- export and import memories
- inspect material memory influence on answers

UI layout is not defined here. These are required management capabilities and data contracts.

## 19. Import, Export, and Materialization

Anchor: `memory.import-export-materialization`

Blocks and `MemoryEntry` records are canonical. Markdown, JSON, workspace files, or other user-editable formats are projections or import sources unless committed back into the block pool.

Import flows through policy, deduplication, provenance, sensitivity classification, and proposal/commit rules.

Export must preserve source identity, scope, sensitivity markings, provenance, and enough structure for safe re-import. Secret content is never exported as raw payload.

File-backed or human-readable memory is valuable for portability and review, but it does not replace the block model.

## 20. Settings

Anchor: `memory.settings`

Memory behavior must be configurable through the settings system.

Settings dimensions include:

- implicit extraction enablement by scope
- explicit remember/forget availability
- proposal review and auto-commit policy
- extraction sensitivity gates
- memory kind and facet visibility
- core memory profile seeds, labels, size limits, and region priority
- archival retrieval policies, ranking signals, rerankers, result shapes, and score display
- reinforcement/usage telemetry retention
- validity and expiration behavior for time-bounded memories
- consolidation triggers and approval behavior
- import/export policy
- hard-delete confirmation requirements
- memory influence inspection visibility
- graph projection enablement for memory-derived entities
- per-scope overrides: global, workspace, conversation, profile, subsystem, surface, automation, and explicit invocation

Specific defaults belong to settings profiles and later settings specs, not this file.

## 21. Explicit Rejections

Anchor: `memory.explicit-rejections`

The following shapes are wrong for this layer:

- treating Memory as a workspace-first surface rather than one of the cross-cutting substrate services
- building a parallel memory store outside the block model
- storing mutable memory content on both entity and block as separate sources of truth
- creating `RecallMemory` as a Memory-owned conversation-history tier
- creating a parallel memory retrieval stack or graph store
- using legacy conversation identifiers as canonical terminology
- encoding scope into memory kind
- using relationship or event as flat memory kinds instead of facts/context plus facets/projections
- making core memory bypass File 13 assembly, authority, sensitivity, or budget reporting
- treating core memory as hidden governing instruction text
- hidden memory-owned model-request injection
- re-extracting memory-injected content as new memory without new evidence
- silent memory extraction with no inspect, disable, review, or policy path
- ungrounded model updates/deletes using hallucinated memory ids
- silent last-write-wins for memory updates
- fixed canonical ranking formulas, top-k values, decay intervals, phrase lists, character limits, or label sets
- hardcoded default settings in the canonical spec
- automatic hard deletion of expired or low-strength memories
- storing raw secrets in memory, descriptions, indexes, events, exports, telemetry, or model-request text
- memory-specific canonical event kinds outside File 10's `Custom` mechanism
- private approval logic inside memory capability handlers
- treating natural memory use as permission to hide memory influence from user inspection
- treating authored reference content and learned user/work-context state as the same primitive
- treating memory-derived procedures as hidden instructions instead of proposing the correct instruction, knowledge, workflow, or profile object when needed

## 22. Consequences for Later Specs

Anchor: `memory.consequences-for-later-specs`

Later specs must follow these rules:

- Settings and profiles must define memory defaults, scope precedence, and customization surfaces without hardcoding hidden branches.
- UI specs must present memory management, proposal review, influence inspection, and import/export as projections over the records defined here.
- Storage specs must persist `MemoryEntry` entity records, `Memory` blocks, provenance, validity, retention, and projection metadata without duplicating mutable content.
- Retrieval specs must treat memory indexes as rebuildable projections and return normalized hits with score attribution.
- Context specs must assemble memory through File 13 regions and authority classes, never through private model-request construction.
- Capability and policy specs must declare memory operations as ordinary capabilities with touched resources, approval behavior, leases, cancellation, postconditions, and output contracts.
- Teacher, Coder, Web, Data Processor, GUI Control, System Agent, automation, workflows, plugins, and MCP integrations may consume and contribute memory only through this substrate.
- Knowledge and graph specs must own curated reference content and graph projection mechanics while accepting memory-derived source records through the shared indexing pipeline.
- Evaluation specs should measure memory extraction accuracy, false-memory rate, retrieval relevance, source attribution, conflict handling, expiration behavior, consolidation quality, and natural-but-inspectable use.

## 23. Canonical Rule Anchors

Anchor: `memory.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `memory.chosen-model`, `memory.adjacent-boundaries`, `memory.memory-entry`, `memory.kinds-scopes-facets`, `memory.core-memory`, `memory.archival-memory`, `memory.validity-retention-short-term-memory`, `memory.learning-extraction`, `memory.retrieval-use`, `memory.salience-strength`, `memory.provenance-confidence-conflict`, `memory.consolidation`, `memory.natural-use-inspectability`, `memory.memory-derived-instructions-profiles-skills`, `memory.knowledge-base-graph-relationship`, `memory.capability-families`, `memory.events-ledger-background-work`, `memory.privacy-sensitivity-user-control`, `memory.import-export-materialization`, and `memory.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
