# Memory — Operative Core

## 1. Chosen Model `memory.chosen-model`
- Memory-owned tiers: `CoreMemory`, `ArchivalMemory`.
- Recent conversation turns are NOT a Memory tier.

## 2. Adjacent Boundaries `memory.adjacent-boundaries`
### 2.1 Blocks
- In-place mutation of block content is invalid.
### 2.4 Execution, Capabilities, Policy, Surfaces
- Memory-specific handlers do NOT implement private approval logic.

## 3. `MemoryEntry` `memory.memory-entry`
### 3.2 Required Fields
- `memory_id`, `block_id`, `kind`, `scope`, `facets`, `provenance`, `confidence`, `salience_features`, `validity`, `retention_policy`, `conflict_state`, `created_at`, `updated_at`, `entity_schema_version`.
### 3.3 Non-Identity Projections
- retrieval counts; last retrieved time; ranking strength; embedding vectors; graph entities/relationships; index rows; UI grouping state; exact token counts.
- When retained, MUST be keyed by the policy/model/tokenizer/source version/retrieval profile that produced them.

## 4. Kinds, Scopes, and Facets `memory.kinds-scopes-facets`
### 4.1 `MemoryKind`
- `Preference`, `Fact`, `Context`, `Pattern`, `Style`, `Procedure`, `Commitment`, `Mastery`, `Custom { namespace, name }`.
- `Relationship` is NOT a flat memory kind.
- `Event` is NOT a separate memory kind.
### 4.2 `MemoryScope`
- `Global`, `Workspace { workspace_id }`, `Conversation { conversation_id }`, `Custom { namespace, id }`.
### 4.3 Facets
- Facets are typed; prose-only facets insufficient for policy-critical behavior.
- Facet fields: subject; topic tags; temporal (`when`, deadline, recurrence, valid-from, valid-until); source authority; extraction method; source language/modality; 5W1H (who, what, when, where, why, how); confidence contributors; sensitivity/redaction hints; freshness requirements.

## 5. Core Memory `memory.core-memory`
- Core memory blocks: small by profile policy; directly inspectable/editable; source-attributed; governed by File 13 assembly/sensitivity/authority/budget rules; configured via profiles/settings, not a fixed canonical label set.
- Core memory is NOT hidden governing instruction text and NOT guaranteed to render in every model request; on omission/redaction/externalization/summarization the assembly snapshot MUST record the reason.

## 6. Archival Memory `memory.archival-memory`
- Durable learned state not normally assembled unless retrieved/selected by policy; stored as `Memory` blocks + `MemoryEntry` metadata; indexed via File 12 namespaces (e.g. `memory:<scope_id>`); retrieved progressively.
- Indexes are rebuildable from blocks + entity records; loss/corruption of an index MUST NOT destroy memory content.

## 7. Validity, Retention, Short-Term `memory.validity-retention-short-term-memory`
- Hard deletion never happens silently.

## 8. Learning and Extraction `memory.learning-extraction`
### 8.1 Learning Paths
- Implicit learning MUST pass through extraction + distillation.
### 8.2 Distillation Pipeline steps
- identify eligible sources; exclude ineligible by authority/sensitivity/recursion/policy; classify meaningful learning vs skip; distill candidates by kind/scope/confidence/provenance/facets/retention; compare against existing; produce grounded `Add`/`Update`/`Delete`/`Forget`/`None`; route writes through capability policy; commit accepted changes as blocks + entity updates.
### 8.3 Grounded Update Protocol
- 4 operations: `Add`, `Update`, `Delete`/`Forget`, `None`.
- Model MUST NOT invent target memory ids.
- Updates carry an expected revision/precondition; silent last-write-wins invalid.
### 8.5 Recursion Prevention
- Extraction MUST distinguish source authority.
- Memory-injected content NOT eligible as a new memory source unless the current turn adds new evidence.
- Memory MUST NOT self-amplify by re-memorizing memory-injected content.

## 9. Retrieval and Use `memory.retrieval-use`
### 9.3 Reinforcement and Usage
- If retrieval affects future ranking, system MUST record the signal in a sensitivity-aware, inspectable, policy-controlled way.
- MUST NOT persist secret query text or hidden private model-request content.

## 10. Salience and Strength `memory.salience-strength`
- Strength is NOT stored as an unqualified mutable scalar on the memory entity.
- Default salience features: novelty; relevance; emotional/preference intensity; predictive usefulness.

## 11. Provenance, Confidence, Conflict `memory.provenance-confidence-conflict`
- Every memory MUST have provenance.
- Equal-strength contradiction is unresolved, not silently overwritten.
- `MemoryProvenance` fields: source refs; source authority; extraction method; actor; confidence + contributors; sensitivity + redaction state; freshness requirements.

## 12. Consolidation `memory.consolidation`
- Consolidation writes through block/version/capability/policy/ledger systems (NOT hidden deletion).
- System MUST remain correct if a scheduled consolidation never runs.

## 13. Natural Use and Inspectability `memory.natural-use-inspectability`
- User MUST be able to inspect/correct/disable/export/import/delete memories and see which memories materially influenced an answer when influence is recorded.

## 14. Memory-Derived Instructions/Profiles/Skills `memory.memory-derived-instructions-profiles-skills`
- Memory-proposed objects MUST carry source attribution, authority, sensitivity, policy approval.

## 15. Knowledge Base and Graph Relationship `memory.knowledge-base-graph-relationship`
- Knowledge = curated reference content the agent may cite/study/retrieve; Memory = learned state about user/workspace/preferences/procedures/commitments/mastery/context.
- Memory MAY register extraction capabilities projecting memory-derived entities/relationships into File 12's shared graph projection; Memory does NOT own the graph store, graph query algorithm, graph UI, or universal entity taxonomy.
- Relationship-like memories represented as facts and projected into File 12 records when useful.

## 16. Capability Families `memory.capability-families`
- Memory MUST register capabilities through the canonical registry.
- Operation families: recall/search/read/inspect; explicit remember/forget; proposal create/review/accept/reject/modify/batch-resolve; memory add/update/supersede/merge/drop/recover/hard-delete request; core memory read/edit; extraction/distillation; consolidation/cleanup; conflict detection/resolution; scope promotion/narrowing; import/export/materialization; history/provenance/influence inspection.
- All memory capabilities declare touched resources, sensitivity, replay class, reversibility, output block kinds, event kinds, concurrency, cancellation behavior, postconditions via File 05.
- Write-like capabilities route through File 06; hard deletion and secret/sensitive export require the strongest applicable confirmation path.

## 17. Events, Ledger, Background Work `memory.events-ledger-background-work`
- Memory-specific events/ledger kinds are `Custom { namespace, name, payload }` under `memory` namespace.
- Consequential memory facts commit to the ledger.
- Background memory work MUST be cancellable as part of its parent run/subsystem and individually when exposed.

## 18. Privacy, Sensitivity, User Control `memory.privacy-sensitivity-user-control`
- Raw secrets MUST NOT be stored in memory content, descriptions, indexes, events, exports, or telemetry.
- Users MUST be able to: inspect; search/filter; edit content/kind/scope/facets/validity/retention where policy allows; pause/disable implicit extraction by scope; keep explicit remember/forget independent of implicit extraction; review/batch-resolve/auto-policy proposals; delete/recover non-destructively; request hard deletion via typed confirmation when allowed; export/import; inspect material memory influence.

## 19. Import, Export, Materialization `memory.import-export-materialization`
- Export MUST preserve source identity, scope, sensitivity markings, provenance, and enough structure for safe re-import.
- Secret content is never exported as raw payload.

## 20. Settings `memory.settings`
- Memory behavior MUST be configurable via settings.

## 21. Explicit Rejections `memory.explicit-rejections`
- Memory as workspace-first surface.
- Parallel memory store outside block model.
- Mutable content on both entity and block.
- `RecallMemory` conversation-history tier.
- Parallel memory retrieval stack or graph store.
- Legacy conversation identifiers as canonical terminology.
- Encoding scope into memory kind.
- `Relationship`/`Event` as flat memory kinds.
- Core memory bypassing File 13 assembly/authority/sensitivity/budget.
- Core memory as hidden governing instruction text.
- Hidden memory-owned model-request injection.
- Re-extracting memory-injected content without new evidence.
- Silent extraction with no inspect/disable/review/policy path.
- Ungrounded updates/deletes using hallucinated memory ids.
- Silent last-write-wins.
- Fixed canonical ranking formulas/top-k/decay/phrase lists/limits/labels.
- Hardcoded default settings.
- Automatic hard deletion of expired/low-strength memories.
- Storing raw secrets anywhere.
- Memory-specific canonical event kinds outside `Custom`.
- Private approval logic inside memory handlers.
- Natural use as permission to hide influence.
- Treating reference content and learned state as same primitive.
- Memory-derived procedures as hidden instructions.
