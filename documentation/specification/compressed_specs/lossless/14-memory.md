> Lossless render of canonical/14-memory.md — original 30654 chars

# Memory

Status: Canonical.

## Scope
- Defines: `Memory` as always-available substrate service storing learned state (user, workspaces, preferences, procedures, commitments, mastery, contextual facts); Memory-owned tier model `CoreMemory` and `ArchivalMemory`; `MemoryEntry` as entity layer over `Memory`-kind blocks; memory kinds/scopes/facets/provenance/confidence/salience features/validity/retention policy; explicit memory commands, implicit learning, proposal review, grounded update, consolidation; memory retrieval as consumer of File 12 substrate; memory assembly as consumer of File 13 assembly contract; natural memory use, inspectability, privacy, sensitivity, user controls; memory capability families, custom event families, background-work expectations, settings dimensions.
- Does NOT define: block schema/lifecycle/content variants/commit validation (File 08); claim/evidence/citation/artifact/provenance identity (File 09); execution ledger schema/event envelopes/hook dispatch/background-worker mechanics (File 10); version graph commits/materialized views/lifecycle action logs (File 11); retrieval indexes/chunking/embedding/graph projection storage/ranking algorithms (File 12); model-request assembly/context compaction/conversation-history management/router context policy (File 13); capability declaration fields/policy evaluation/approval UI/leases/tool-surface loading (Files 05-07); model selection, provider failover, storage schema, sync, UI layout, exact settings defaults.

## Source Resolution
- Memory stores durable learned state; not a workspace-first surface, model-request injection layer, conversation-history manager, private retrieval stack, or parallel event/capability system.
- Memory is a substrate service per File 01, always available to work surfaces but not shaped as workspace-first.
- Memory entries are entity metadata over `Memory`-kind blocks (block carries durable content; entity carries memory-specific management state).
- Memory owns core + archival memory. Recent conversation turns are conversation history (Files 12, 13).
- Learning uses explicit user commands + policy-governed distillation proposals. Raw run history stays in the ledger.
- Retrieval reuses File 12 indexes/result contracts, adding memory-specific ranking signals via score-attributed policy.
- Memory contributes assembly sources to File 13; never injects hidden instructions or bypasses authority/sensitivity/budget rules.

## 1. Chosen Model `memory.chosen-model`
- One Memory substrate. Stores curated learned state surviving beyond the immediate conversation. NOT raw transcript, knowledge base, instruction file, graph database, or private model-request layer.
- Memory-owned tiers:
  - `CoreMemory`: small, high-priority, editable memory blocks normally eligible for early model-request assembly.
  - `ArchivalMemory`: durable indexed memory records searched on demand via the shared retrieval substrate.
- Recent conversation turns are NOT a Memory tier — they are conversation blocks in the active materialized view, assembled via File 13's `ConversationHistory` region and searchable via File 12's `conversation:<conversation_id>` namespace. Memory MAY read those blocks as learning sources when policy allows, but does not own a sliding-window transcript store or recall index.
- Memory is always integrated: every work surface can read/contribute via registered capabilities + policy. No surface receives a private memory model.

## 2. Adjacent Boundaries `memory.adjacent-boundaries`
### 2.1 Blocks
- File 08 declares `Memory` as a block kind. A memory's durable content lives in a `Memory`-kind block. `MemoryEntry` is the entity layer adding stable identity, scope, kind, provenance, salience features, validity, conflict state, management metadata.
- Observable memory edits create new blocks or versioned records per Files 08/11. In-place mutation of block content is invalid.

### 2.2 Retrieval
- Memory records are source records for File 12. Lexical/vector/graph/metadata/structural indexes over memory are rebuildable projections, not memory identity.
- Retrieval returns normalized `RetrievalHit` / `MemoryHit` results; may add memory-specific ranking signals, but substrate/indexes/namespaces/redaction rules/graph projection contracts remain File 12 concerns.

### 2.3 Context Assembly
- Memory outputs enter model requests as assembly parts under File 13.
- Core memory has high priority and should normally fit (small by profile design). This is a governance rule, not a routine budget tradeoff: still subject to sensitivity gates, authority validation, provider constraints, extreme model-window limits. Settings profiles should give core memory enough region priority that omission occurs only under extraordinary constraints.
- Archival memories enter `RetrievedContext` region when selected by retrieval/policy. Memory-derived instruction/profile proposals enter File 13 only as attributed `InstructionSource` blocks or equivalent approved sources; Memory itself does not inject hidden instruction text.

### 2.4 Execution, Capabilities, Policy, Surfaces
- Memory operations are capabilities registered (File 05), evaluated (File 06), exposed (File 07), executed (File 04), recorded (File 10).
- Memory-specific handlers do NOT implement private approval logic. Memory writes/deletes/exports/imports/consolidation/derived instruction-profile proposals go through shared capability + policy systems.

## 3. `MemoryEntry` `memory.memory-entry`
### 3.1 Definition
- `MemoryEntry` = stable entity identity for one learned memory over one or more `Memory`-kind blocks. Block = content carrier; entity = management/retrieval identity.

### 3.2 Required Fields
- `memory_id`: stable identifier, never reused.
- `block_id`: current `Memory` block carrying active content.
- `kind`: `MemoryKind`.
- `scope`: `MemoryScope`.
- `facets`: typed optional facets for retrieval/validity/management.
- `provenance`: `MemoryProvenance`.
- `confidence`: confidence in current content.
- `salience_features`: policy-readable feature values used by ranking/consolidation.
- `validity`: whether current, time-bounded, stale, unresolved, contradicted, or source-limited.
- `retention_policy`: durable, time-bounded, user-pinned, review-needed, or cleanup-eligible.
- `conflict_state`: conflict projection when known.
- `created_at` and `updated_at`.
- `entity_schema_version`.
- Entity MAY cache safe descriptions/derived summaries/display labels (projections). Durable content stays in the block.

### 3.3 Non-Identity Projections (projections or policy-retained telemetry, not required identity)
- retrieval counts; last retrieved time; ranking strength; embedding vectors; graph entities/relationships; index rows; UI grouping state; exact token counts.
- When retained, MUST be keyed by the policy/model/tokenizer/source version/retrieval profile that produced them.

## 4. Kinds, Scopes, and Facets `memory.kinds-scopes-facets`
### 4.1 `MemoryKind` (canonical)
- `Preference`: stable or contextual user preference.
- `Fact`: learned factual statement about user/workspace/operating context.
- `Context`: situational/temporal context — events, deadlines, active projects, temporary circumstances.
- `Pattern`: repeated behavior/tendency/observed recurring structure.
- `Style`: communication, formatting, visual, writing, or interaction style.
- `Procedure`: learned way of doing something.
- `Commitment`: promise/plan/deadline/follow-up/obligation system should track.
- `Mastery`: learning state, concept mastery, misconception, SRS-relevant progress, teacher-facing competence signal.
- `Custom { namespace, name }`: registered extension.
- Kinds are behavioral categories; scope NOT encoded into kind (a global user fact and a workspace fact are both `Fact` at different scopes).
- Relationship-like content = `Fact` or projected into File 12 entity-relationship records by an extraction capability. `Relationship` is NOT a flat memory kind.
- Time-bound events = `Context` with temporal facets. `Event` is NOT a separate memory kind.

### 4.2 `MemoryScope` (canonical)
- `Global`; `Workspace { workspace_id }`; `Conversation { conversation_id }`; `Custom { namespace, id }`.
- Task-/intent-thread-scoped memories represented via `Custom` or future scope extension only when durable learned state. Transient task/run state stays in Files 02 and 04.
- ATLAS3 is local-first single-user; scope is NOT `user_id`-based unless a future profile/sync spec introduces multi-profile identity.

### 4.3 Facets
- Add structure without forcing every memory into a large schema. Useful facets: subject; topic tags; temporal fields (`when`, deadline, recurrence, valid-from, valid-until); source authority; extraction method; source language/modality; optional 5W1H (who, what, when, where, why, how); confidence contributors; sensitivity/redaction hints; freshness requirements.
- Facets are typed. Prose-only facets insufficient for policy-critical behavior.

## 5. Core Memory `memory.core-memory`
- High-priority subset shaping ordinary interaction without search. Core memory blocks are: small by profile policy; directly inspectable/editable via memory management surfaces; source-attributed; governed by File 13 assembly/sensitivity/authority/budget rules; configured through profiles/settings rather than fixed canonical labels.
- Labels (persona, human, workspace, project, communication style, active commitments) may be useful profile seeds but are NOT a hardcoded canonical set.
- Core memory is NOT governing/hidden instruction text and NOT guaranteed to render in every model request. When omitted/redacted/externalized/summarized, the assembly snapshot records the reason.

## 6. Archival Memory `memory.archival-memory`
- Durable learned state not normally assembled unless retrieved/selected by policy. Stored as `Memory` blocks + `MemoryEntry` metadata; indexed via File 12 namespaces such as `memory:<scope_id>`; supports lexical/vector/graph/metadata/structural projections as configured; retrieved progressively (compact hit first, expansion on demand); inspectable/editable by user.
- Indexes are rebuildable from blocks + entity records. Loss/corruption of an index MUST NOT destroy memory content.

## 7. Validity, Retention, and Short-Term Memory `memory.validity-retention-short-term-memory`
- Memory may be durable or time-bounded. A time-bounded memory is a normal entry whose `validity`/`retention_policy` includes a semantic expiration condition ("until exam date", "until project launch", explicit timestamp).
- Expiration is a validity rule, NOT a polling correctness rule. After expiration: retrieval/assembly treat memory as expired/stale by default; system MAY surface cleanup proposal; a maintenance worker MAY mask/drop/archive/supersede via normal capability + version rules; hard deletion never happens silently.
- Example: "exam on June 10; help me focus until then" can create `Context` or `Commitment` memory with `valid_until = 2026-06-10`; after that date it should not keep shaping normal responses unless extended/recovered.
- Settings decide whether expired memories are hidden, searchable only with archived/stale filters, proposed for cleanup, or auto-dropped from active projections.

## 8. Learning and Extraction `memory.learning-extraction`
### 8.1 Learning Paths
- Two paths: explicit memory commands (user directly asks to remember/forget/update/recall); implicit learning (system proposes/commits based on conversations/actions/observations/outcomes/tool results under policy).
- Explicit commands can create direct proposals or commits. Implicit learning MUST pass through extraction + distillation so raw conversation noise does not become durable memory.

### 8.2 Distillation Pipeline (implicit) — should:
1. identify eligible source blocks/ledger facts.
2. exclude ineligible sources by authority/sensitivity/recursion/policy.
3. classify whether source contains meaningful learning or should be skipped.
4. distill candidate memories by kind/scope/confidence/provenance/facets/retention.
5. compare candidates against existing memories.
6. produce grounded `Add`, `Update`, `Delete`/`Forget`, or `None` decisions.
7. route write proposals through capability policy.
8. commit accepted changes as blocks + entity updates.
- Success and failure distill differently: success → procedures/preferences/patterns; failure → warnings/anti-patterns/corrected approaches/user-specific constraints.

### 8.3 Grounded Update Protocol — 4-operation: `Add`, `Update`, `Delete`/`Forget`, `None`.
- Model MUST NOT invent target memory ids. When update/delete possible, runtime supplies a bounded candidate set and maps real memory ids to temporary local identifiers in the model request; model selects from that set; runtime resolves local identifier back to real `memory_id`, validates, applies mutation via revision-safe capability calls.
- Updates carry an expected revision/equivalent precondition. Conflicting concurrent edits fail or rebase through explicit policy path. Silent last-write-wins invalid.

### 8.4 Proposal Policy
- Extraction can produce proposals or direct commits depending on policy. Policy MAY: require user review for all writes; auto-commit selected low-risk categories; batch proposals; pause extraction for sensitive contexts; disable implicit extraction while keeping explicit `remember` available; require typed confirmation for deletion/export/broad-scope promotion.
- File 14 does not define default values for these choices.

### 8.5 Recursion Prevention
- Extraction MUST distinguish source authority. Existing memory content included in a model request is NOT eligible as a new memory source unless the current turn adds new evidence. Retrieval snippets, web content, tool outputs, assistant summaries, instruction sources each carry own authority + extraction eligibility.
- Memory MUST NOT self-amplify by re-memorizing memory-injected content.

## 9. Retrieval and Use `memory.retrieval-use`
### 9.1 Progressive Retrieval
- Returns compact hits first. A memory hit should carry: `memory_id`; `block_id` or source ref; kind/scope/sensitivity/validity; snippet or safe description; provenance summary; score attribution; expansion handle; redaction/omission state when applicable.
- Full content, source conversations, claim/evidence records, related graph context fetched only when model/UI/user requests expansion and policy permits.

### 9.2 Ranking Signals
- May combine: lexical relevance; dense similarity; graph proximity; scope match; source authority; confidence; salience features; freshness/validity; recurrence/commitment urgency; user-pinned/protected state; retrieval reinforcement; custom registered signals.
- Combination policy configurable and MUST be score-attributed. Canonical spec does not fix weights/top-k/half-lives/rerank thresholds/formulas.

### 9.3 Reinforcement and Usage
- Retrieval reinforcement = optional policy-governed telemetry. If a retrieval affects future ranking, system MUST record the signal in a sensitivity-aware, inspectable, policy-controlled way. MUST NOT persist secret query text or hidden private model-request content.

## 10. Salience and Strength `memory.salience-strength`
- Salience represented by feature inputs, not a single canonical formula. Default feature set may include: novelty; relevance; emotional/preference intensity; predictive usefulness. Other features may be registered by profiles/subsystems.
- Active ranking/consolidation policy computes strength at query/maintenance time and records score attribution when strength affects behavior. Strength is NOT stored as an unqualified mutable scalar on the memory entity.

## 11. Provenance, Confidence, and Conflict `memory.provenance-confidence-conflict`
- Every memory MUST have provenance. `MemoryProvenance` should record: source refs (message/block/ledger entry/file/tool result/observation/import/explicit command/external source); source authority; extraction method; actor (user/assistant/subsystem/automation/import/plugin); confidence + confidence contributors; sensitivity + redaction state; freshness requirements.
- Factual memories may publish/reference File 09 claims/evidence when useful. Preference/style/procedure/commitment/mastery memories need not become claims by default but still need provenance.
- Conflict handling: claim-like conflicts use File 09 semantics when applicable; memory-local conflict state is a management projection; equal-strength contradiction is unresolved, not silently overwritten; resolution creates explicit records and may supersede, keep both, narrow scope, lower confidence, or ask the user.

## 12. Consolidation `memory.consolidation`
- Maintains quality. May: merge duplicates; supersede stale/contradicted memories; lower confidence or mark stale; drop expired/low-value memories from active projections; create summaries or richer memories from several sources; propose scope changes; reinforce useful memories; mark cleanup candidates.
- NOT hidden deletion — writes through block/version/capability/policy/ledger systems.
- May be triggered by user action, source events, thresholds, policy decisions, app lifecycle events, or scheduled background workers. Time-based schedules are convenience triggers, not correctness conditions; system MUST remain correct if a scheduled consolidation never runs.
- When it rewrites/merges/supersedes/exports/broadly promotes/removes user-visible memory, it follows File 06 policy and approval rules.

## 13. Natural Use and Inspectability `memory.natural-use-inspectability`
- Memory should feel natural in ordinary assistant text. Assistant should not gratuitously frame normal answers as database retrieval or say "based on your stored memories" when simple contextual phrasing is better.
- Attribution allowed and sometimes required: when user asks what is remembered; when user asks why an answer was personalized; when editing/deleting/resolving memory; when confidence/freshness uncertain; when policy/UI requires inspectability.
- Natural use is NOT permission to hide influence. User MUST be able to inspect/correct/disable/export/import/delete memories and see which memories materially influenced an answer when the system records that influence.
- Exact phrase bans, validators, fail directions are quality-control/settings concerns, not hardcoded canonical text.

## 14. Memory-Derived Instructions, Profiles, and Skills `memory.memory-derived-instructions-profiles-skills`
- Memory may inform future behavior but does NOT own hidden instruction injection.
- If a learned preference/style/procedure/pattern should guide future model behavior as an instruction/profile/workflow/skill/reusable knowledge entry, Memory MAY propose that object through the appropriate layer. Resulting object MUST carry source attribution, authority, sensitivity, policy approval.
- Memory stores learned signals; instruction sources instruct; workflows orchestrate; knowledge entries provide reference content — connected but separate primitives.

## 15. Knowledge Base and Graph Relationship `memory.knowledge-base-graph-relationship`
- Memory vs Knowledge Base differ by semantic role: Knowledge = curated reference content the agent may cite/study/retrieve; Memory = learned state about user/workspace/preferences/procedures/commitments/mastery/context. Same interaction can produce both.
- Entity-relationship extraction is producer-populated. Memory may register extraction capabilities projecting memory-derived entities/relationships into File 12's shared graph projection. Memory does NOT own the graph store, graph query algorithm, graph UI, or universal entity taxonomy.
- Relationship-like memories represented as facts and also projected into File 12 records when useful.

## 16. Capability Families `memory.capability-families`
- Memory MUST register capabilities through canonical registry. Exact declarations belong to File 05-compatible specs, but memory subsystem MUST cover these operation families: recall/search/read/inspect; explicit remember/forget; proposal create/review/accept/reject/modify/batch-resolve; memory add/update/supersede/merge/drop/recover/hard-delete request; core memory read/edit; extraction/distillation; consolidation/cleanup; conflict detection/resolution; scope promotion/narrowing; import/export/materialization; history/provenance/influence inspection.
- All memory capabilities declare touched resources, sensitivity, replay class, reversibility, output block kinds, event kinds, concurrency, cancellation behavior, postconditions via File 05.
- Write-like capabilities route through File 06. Hard deletion and secret/sensitive export require the strongest applicable confirmation path.

## 17. Events, Ledger, and Background Work `memory.events-ledger-background-work`
- Memory emits events through File 10. Memory-specific events and ledger entry kinds are `Custom { namespace, name, payload }` extensions under the `memory` namespace. File 14 reserves the namespace + expected event families; does NOT add memory kinds to File 10's closed canonical catalogue.
- Expected event families: memory proposal lifecycle; memory creation/update/supersession/drop/recovery/deletion request; retrieval execution; extraction/distillation lifecycle; consolidation lifecycle; conflict detection/resolution; core memory modification; import/export/materialization; influence inspection.
- Consequential memory facts commit to the ledger. Live UI events are not the source of truth.
- Background memory work (extraction, distillation, consolidation, import/export, indexing coordination, graph projection) is an execution unit governed by File 04. MUST be cancellable as part of its parent run/subsystem and individually when exposed as an active process. Staged outputs commit only at safe proposal/commit boundaries.

## 18. Privacy, Sensitivity, and User Control `memory.privacy-sensitivity-user-control`
- Memory content defaults to sensitivity implied by its source. User-private context usually produces `Sensitive` memory. Raw secrets MUST NOT be stored in memory content, descriptions, indexes, events, exports, or telemetry.
- Users MUST be able to: inspect memories; search/filter; edit content/kind/scope/facets/validity/retention where policy allows; pause/disable implicit extraction by scope; keep explicit remember/forget available independently of implicit extraction; review/batch-resolve/auto-policy proposals; delete/recover via non-destructive mechanisms; request hard deletion via typed confirmation when allowed; export/import; inspect material memory influence on answers.
- UI layout not defined here. These are required management capabilities + data contracts.

## 19. Import, Export, and Materialization `memory.import-export-materialization`
- Blocks and `MemoryEntry` records are canonical. Markdown/JSON/workspace files/other user-editable formats are projections or import sources unless committed back into the block pool.
- Import flows through policy, deduplication, provenance, sensitivity classification, proposal/commit rules.
- Export MUST preserve source identity, scope, sensitivity markings, provenance, and enough structure for safe re-import. Secret content is never exported as raw payload.
- File-backed/human-readable memory valuable for portability/review but does not replace the block model.

## 20. Settings `memory.settings`
- Memory behavior MUST be configurable via settings. Dimensions: implicit extraction enablement by scope; explicit remember/forget availability; proposal review + auto-commit policy; extraction sensitivity gates; memory kind + facet visibility; core memory profile seeds/labels/size limits/region priority; archival retrieval policies/ranking signals/rerankers/result shapes/score display; reinforcement/usage telemetry retention; validity/expiration behavior for time-bounded memories; consolidation triggers + approval behavior; import/export policy; hard-delete confirmation requirements; memory influence inspection visibility; graph projection enablement for memory-derived entities; per-scope overrides (global, workspace, conversation, profile, subsystem, surface, automation, explicit invocation).
- Specific defaults belong to settings profiles / later settings specs, not this file.

## 21. Explicit Rejections `memory.explicit-rejections`
- Treating Memory as a workspace-first surface rather than a substrate service.
- Building a parallel memory store outside the block model.
- Storing mutable memory content on both entity and block as separate sources of truth.
- Creating `RecallMemory` as a Memory-owned conversation-history tier.
- Creating a parallel memory retrieval stack or graph store.
- Using legacy conversation identifiers as canonical terminology.
- Encoding scope into memory kind.
- Using `Relationship` or `Event` as flat memory kinds instead of facts/context plus facets/projections.
- Making core memory bypass File 13 assembly, authority, sensitivity, or budget reporting.
- Treating core memory as hidden governing instruction text.
- Hidden memory-owned model-request injection.
- Re-extracting memory-injected content as new memory without new evidence.
- Silent memory extraction with no inspect/disable/review/policy path.
- Ungrounded model updates/deletes using hallucinated memory ids.
- Silent last-write-wins for memory updates.
- Fixed canonical ranking formulas, top-k values, decay intervals, phrase lists, character limits, or label sets.
- Hardcoded default settings in the canonical spec.
- Automatic hard deletion of expired or low-strength memories.
- Storing raw secrets in memory, descriptions, indexes, events, exports, telemetry, or model-request text.
- Memory-specific canonical event kinds outside File 10's `Custom` mechanism.
- Private approval logic inside memory capability handlers.
- Treating natural memory use as permission to hide memory influence from user inspection.
- Treating authored reference content and learned user/work-context state as the same primitive.
- Treating memory-derived procedures as hidden instructions instead of proposing the correct instruction/knowledge/workflow/profile object when needed.

## 22. Consequences for Later Specs `memory.consequences-for-later-specs`
- Settings/profiles MUST define memory defaults, scope precedence, customization surfaces without hardcoding hidden branches.
- UI specs MUST present memory management, proposal review, influence inspection, import/export as projections over records defined here.
- Storage specs MUST persist `MemoryEntry` entity records, `Memory` blocks, provenance, validity, retention, projection metadata without duplicating mutable content.
- Retrieval specs MUST treat memory indexes as rebuildable projections and return normalized hits with score attribution.
- Context specs MUST assemble memory through File 13 regions and authority classes, never through private model-request construction.
- Capability/policy specs MUST declare memory operations as ordinary capabilities with touched resources, approval behavior, leases, cancellation, postconditions, output contracts.
- Teacher, Coder, Web, Data Processor, GUI Control, System Agent, automation, workflows, plugins, MCP integrations may consume/contribute memory only through this substrate.
- Knowledge/graph specs MUST own curated reference content + graph projection mechanics while accepting memory-derived source records through the shared indexing pipeline.
- Evaluation specs should measure memory extraction accuracy, false-memory rate, retrieval relevance, source attribution, conflict handling, expiration behavior, consolidation quality, natural-but-inspectable use.
