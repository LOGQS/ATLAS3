> Lossless render of canonical/12-retrieval-indexing-and-knowledge-base.md — original 27450 chars

# Retrieval, Indexing, and Knowledge Base

## Status
Canonical.

## Scope
Defines shared retrieval substrate: retrieval indexes as rebuildable projections over blocks/versions/observations/knowledge entities/registered external sources; index namespaces, kinds, entries, chunking, embeddings, freshness, rebuild, replay; normalized query/result contracts used by local search, knowledge search, file search, web retrieval adapters, MCP resources, specialized retrieval; curated knowledge-base entity layer over `KnowledgeEntry` blocks; sensitivity-aware indexing/retrieval; retrieval capabilities, policy boundaries, events, settings, extension points.
Does NOT define: block storage/lifecycle/base `BlockKind` catalogue [File 08]; artifact/claim/evidence/citation/provenance [File 09]; event envelopes/ledger/hooks/live-stream transport [File 10]; version graph mechanics/materialized views [File 11]; capability declarations/policy [Files 05,06]; context assembly/memory/provider selection/plugin packaging/UI/storage schema (owning specs consume this).

## Source Resolution
- retrieval is one shared substrate with source-specific adapters, not per-subsystem/per-surface private index systems.
- canonical specs define behavior/contracts, not permanent engines/libraries.
- local retrieval, file search, web search, web fetch, MCP retrieval, knowledge search, specialized retrieval can have specialized capabilities while sharing normalized retrieval results.
- knowledge-base curation is entity-layer state over `KnowledgeEntry` blocks, not metadata welded into every block.
- graph extraction is producer-owned; graph projection + retrieval contract are shared.
- time-based sweeps/TTLs may optimize maintenance, but correctness comes from events, version identity, fingerprints, policy.

## 1. Core Model `retrieval.core-model`
Four layers: source records (blocks, materialized files, observations, knowledge entities, graph entities, external resources, capability-produced records); index projections (lexical, vector, graph, structural, metadata, source-specific); query/result contracts (typed request + normalized hit envelope); knowledge-base entities (curated records managing lifecycle/validation/tags/featured/governance over `KnowledgeEntry` blocks).
- Indexes are projections; rebuildable from canonical source records, active versions, source fingerprints, model identities. Index rows are NOT canonical identity of user content.
- Retrieval is source-aware; different hit payloads but all normalize into `RetrievalHit`.

## 2. Retrieval Index `retrieval.retrieval-index`
### 2.1 Definition
`RetrievalIndex` = named projection over one or more source pools. Required logical fields: `index_id`, `namespace_id`, `kind`, `source_scope`, `embedding_model_identity` (when dense vectors stored), `tokenizer_identity` (when lexical tokenization stored), `version_anchor`, `freshness_fingerprint`, `created_at`, `updated_at`, `health`. Physical storage layout not defined here.
### 2.2 Index Kinds
- `Lexical` - token/term-based lookup
- `Vector` - embedding similarity lookup
- `Hybrid` - coordinated lexical+vector lookup
- `Graph` - entity/relationship traversal projection
- `Structural` - path/symbol/heading/schema/hierarchy lookup
- `Metadata` - field/facet lookup
- `ExternalAdapter` - normalized search over external source
- `Custom { namespace, name }` - registered extension
Index kind defines observable behavior, not an engine; built-in lexical/vector backend may use a library, but library is implementation behind index contract.
### 2.3 Index Entry Identity
MUST be deterministic, derived from: namespace id, source identity, source version/fingerprint, index kind, chunking/extraction strategy identity, entry ordinal/structural address, embedding model identity (when vectorized). Rebuilds over unchanged inputs MUST preserve entry identity (required for replay, debugging, cache reuse, stable citations).
### 2.4 Version Anchoring
Every entry anchored to source state: block entries → block id + block revision; file entries → workspace id + path + content hash; versioned views → `ContextVersion`; web/external → fetched snapshot id/source fingerprint; graph entries → extraction capability + source identity + extraction version. Retrieval during replay MUST use indexes compatible with replayed version or rebuild compatible projections before answering.

## 3. Namespaces `retrieval.namespaces`
### 3.1 Definition
`IndexNamespace` scopes entries by purpose/access boundary. Required fields: `namespace_id`, `owner_subsystem_id`, `source_scope`, `allowed_index_kinds`, `sensitivity_policy`, `freshness_policy`, `rebuild_policy`.
### 3.2 Canonical Namespaces
`conversation:<conversation_id>`, `workspace:<workspace_id>`, `knowledge:<scope_id>`, `memory:<scope_id>`, `observation:<scope_id>`, `ingested_codebase:<workspace_id>`, `validator:<scope_id>`, `evaluator:<scope_id>`, `web_cache:<scope_id>`, `mcp_resource:<server_id>`, `custom:<namespace>:<name>`. Envelope term is `conversation_id`; legacy conversation-identifier terminology not canonical.
### 3.3 Namespace Rules
Namespaces are access boundaries. A query may target multiple namespaces, but each applies own scope + sensitivity predicates before returning hits. Sensitive entries indexed only in namespaces whose scope matches source scope. Secret payloads NEVER indexed.

## 4. Source Records `retrieval.source-records`
### 4.1 Canonical Source Families
blocks [File 08]; active materialized views [File 11]; artifacts/claims/evidence/citations/observations/provenance [File 09]; knowledge-base entities + `KnowledgeEntry` blocks; graph entity/relationship records; workspace files + codebase ingestion records; memory records [Memory spec]; web search/web fetch snapshots; MCP resources + external integration records; custom source records. No subsystem/surface may create a parallel retrieval substrate; specialized sources register adapters.
### 4.2 Entity-Relationship Projection
Entity/relationship records are producer-populated projections. File 12 owns index+retrieval contract; producing subsystem/surface owns extraction semantics. Examples: codebase ingestion (files/modules/functions/classes/imports/calls/references); document ingestion (concepts/sections/prerequisites/citations/glossary); memory processing (factual triples/user preference relations); data-processing (dataset/column/schema/lineage). Each extraction capability commits records through canonical indexing pipeline; no private entity-relationship store.
### 4.3 External Sources
Enter through adapters (web search, web fetch, MCP resource, local service, plugin source) but MUST normalize to `RetrievalResult` contract. Adapters may share fetchers/caches/parsers/ranking/credential handling; remain distinct capabilities when user-facing operation/policy profile/result contract differs. Shared implementation encouraged; duplicated substrate not.

## 5. Chunking and Excerpts `retrieval.chunking-excerpts`
### 5.1 Chunking Strategy
Canonical families: `Structural` (source-defined boundaries: headings, AST nodes, cells, pages, symbols, records, sections); `Semantic` (sentence/paragraph/topic/embedding-aware boundaries); `FixedWindow` (bounded size + optional overlap); `Atomic` (one source record → one entry); `Custom { namespace, name }`. Selection based on source type, content type, user settings, subsystem profile, capability declaration.
### 5.2 Derived Chunks
Derived chunks are NOT blocks; they are index entries. If a chunk/excerpt must become durable conversation context/evidence/user-visible material, committed as `SourceExcerpt` block [File 08]. `SourceExcerpt` describes content; retrieval implementation terminology is not a canonical block kind.
### 5.3 Source Spans
Text-like hits SHOULD carry source span when source supports stable location; enables citation, highlighting, excerpt promotion, audit without copying whole payloads.

## 6. Embeddings and Model Identity `retrieval.embeddings-model-identity`
### 6.1 Embedding Identity
Every stored vector MUST carry: model identity, provider/backend identity, dimension, normalization semantics, input preprocessing identity, source content hash, creation timestamp. Vectors of different model identities NOT comparable unless explicit compatibility adapter declares it safe.
### 6.2 Backends
`Local`, `Api`, `Plugin`, `Mcp`, `Custom { namespace, name }`. Backend class is not a library choice; model strategy/provider specs decide available/preferred/throttled/failed-over implementations.

## 7. Query Contract `retrieval.query-contract`
### 7.1 Retrieval Query
`RetrievalQuery` MUST carry: `query_id`, `query_kind`, `target_namespaces`, `source_filters`, `scope_context`, `sensitivity_context`, `ranking_policy`, `result_shape`, `budget`, `caller_run_id` (when invoked during execution), `requested_by` (capability/subsystem). Query kinds: `Text`, `Vector`, `Hybrid`, `GraphTraversal`, `StructuredLookup`, `ById`, `Custom { namespace, name }`.
### 7.2 Filters
Typed fields, not prose: source family, block kind, path/path pattern, MIME/content type, time range over source timestamps, version anchor, namespace, scope, sensitivity, tags/curation facets (knowledge entity layer), graph entity/relationship type, custom filter declared by source adapter.
### 7.3 Result Shape
Controls: max hit count, snippet/excerpt preference, whether full content references returned, whether score details included, whether redacted hits included, whether graph context expanded. Numeric values are settings/profile choices, not canonical constants.

## 8. Retrieval Pipeline `retrieval.retrieval-pipeline`
### 8.1 Standard Pipeline
1. validate query shape+policy; 2. resolve namespaces+adapters; 3. dispatch source-specific retrieval stages; 4. normalize hits; 5. apply scope+sensitivity filters; 6. deduplicate; 7. combine ranking signals; 8. optionally rerank through configured local/API/plugin/MCP rerankers; 9. create snippets, source spans, overflow markers; 10. record policy-safe telemetry + return `RetrievalResult`. Each stage replaceable behind contract; pipeline may skip irrelevant stages.
### 8.2 Ranking Signals
Families: lexical relevance, dense similarity, graph proximity, structural match, source freshness, provenance quality, validation status, featured/pinned curation state, path/workspace relevance, user/workspace preference, custom registered signal. Combination policy configurable; canonical behavior requires score attribution, not fixed formula.
### 8.3 Deduplication
MUST preserve provenance; may collapse multiple hits of same content into one visible hit only if records contributing sources + score signals. MUST NOT hide contradictory evidence, policy restrictions, or materially different source versions.
### 8.4 External Retrieval
Live web search, web fetch, MCP retrieval, remote plugin retrieval are explicit capability calls; not hidden side effects of local retrieval. Cached external snapshots searchable locally through their namespace when policy allows. Cache expiry is optimization, not correctness; source fingerprints + fetch snapshots define freshness.

## 9. Retrieval Result `retrieval.retrieval-result`
### 9.1 Result Envelope
`RetrievalResult` MUST carry: `query_id`, `status`, `hits`, `overflow`, `applied_filters`, `ranking_policy`, `source_namespaces`, `redaction_summary`, `freshness_summary`, `errors`.
### 9.2 Hit Envelope
`RetrievalHit` MUST carry: `hit_id`, `hit_kind`, `source_ref`, `scope`, `sensitivity`, `snippet`, `source_span` (when available), `scores`, `provenance`, `freshness`, `access_state`. Canonical hit kinds: `BlockHit`, `KnowledgeEntryHit`, `FileHit`, `ArtifactHit`, `ClaimHit`, `EvidenceHit`, `CitationHit`, `ObservationHit`, `MemoryHit`, `GraphHit`, `WebHit`, `McpResourceHit`, `RedactedHit`, `Custom { namespace, name }`.
### 9.3 Redacted Hits
May reveal that a relevant source exists only when policy permits safe disclosure; MUST NOT include secret payload, credential material, or restricted snippets.

## 10. Knowledge Base `retrieval.knowledge-base`
### 10.1 Definition
Curated entity layer over `KnowledgeEntry` blocks. `KnowledgeEntry` = block content carrier; knowledge-base entity owns mutable curation state.
### 10.2 Knowledge Entry Block
Carries: title/display name, description, content/external content reference, source references, scope, sensitivity, provenance links. Block does NOT own mutable curation fields (tags, featured state, validation status, lifecycle state, proposal state, last-reference statistics).
### 10.3 Knowledge Entity
MUST carry: `knowledge_entry_id`, `block_id`, `scope`, `source`, `validation_status`, `lifecycle_status`, `tags`, `featured`, `owner_subsystem_id`, `governance_policy`, `created_at`, `updated_at`. `last_referenced_at`, usage counts, ranking feedback are computed projections (not identity fields, not required durable curation metadata).
### 10.4 Scope
`Global`, `User`, `Workspace { workspace_id }`, `Conversation { conversation_id }`, `Plugin { plugin_id }`, `Subsystem { subsystem_id }`, `Custom { namespace, id }`. Scope controls visibility, retrieval namespace, approval requirements, fork/import behavior.
### 10.5 Sources
`UserAuthored`, `AssistantProposed`, `ImportedDocument`, `IngestedCodebase`, `PluginBundled`, `SystemGenerated`, `ExternalSnapshot`, `MemoryDerived`, `Custom { namespace, name }`. Source affects governance + provenance; does NOT bypass capability policy.
### 10.6 Lifecycle
`Proposed`, `Approved`, `Rejected`, `Archived`, `Superseded`, `HardDeleted`. Proposal expiry, auto-archival, cleanup are user-policy choices; time-based expiry never a correctness requirement.

## 11. Sensitivity `retrieval.sensitivity`
### 11.1 Core Rule
Secret payload NEVER enters an index. If `KnowledgeEntry`/source block is Secret, body not indexed; non-secret description indexed only if safe under File 08 sensitivity rules.
### 11.2 Sensitive Content
Indexed only inside source's allowed scope; retrieval outside that scope returns no hit or redacted hit per policy.
### 11.3 Per-Field Sensitivity
Indexers MUST exclude Secret fields; MAY index Public/Sensitive fields per scopes. A chunk crossing into Secret material MUST be split or rejected; MUST NOT carry the Secret segment.

## 12. Indexing Pipeline `retrieval.indexing-pipeline`
### 12.1 Commit Path
1. source discovery; 2. source fingerprinting; 3. policy+sensitivity validation; 4. strategy selection; 5. chunk/entity projection; 6. embedding/lexical processing when needed; 7. deterministic entry id assignment; 8. atomic index commit; 9. health+freshness update; 10. custom event + ledger recording when applicable.
### 12.2 Incremental Updates
Based on source fingerprints, version anchors, explicit change events. Timed sweeps may repair missed changes but MUST NOT be primary correctness mechanism.
### 12.3 Rebuild
MUST be deterministic over same canonical source state, settings profile, strategy identities, model identities. May change physical storage but MUST preserve logical entry identity when source inputs unchanged.
### 12.4 Corruption Handling
If index missing/stale/corrupted/incompatible with active version, retrieval MUST rebuild, degrade with typed warning, or fail with typed error. Silent partial retrieval FORBIDDEN.

## 13. Capability Surface `retrieval.capability-surface`
### 13.1 Capability Families
knowledge search/read/propose/write/import/archive/delete; local file find/grep/structural search; block+artifact lookup; graph search+traversal; web search+web fetch; MCP resource search+read; index rebuild/inspect/health check; source ingestion+re-ingestion; custom subsystem retrieval capabilities. Exact declarations [File 05]; policy behavior [File 06].
### 13.2 Capability Metadata
Every retrieval capability declaration MUST identify: capability class, source subsystem, touched resources as machine-parseable resource expressions, side-effect class, reversibility class, replay class, data sensitivity, output contract, postconditions, concurrency class. MUST NOT use prose-only resource declarations for readable/writable resources.
### 13.3 Shared Implementation, Separate Capabilities
Capabilities may share lower-level services (web search/web fetch may share URL normalization, network policy checks, snapshot storage, parser services, cache lookup) but remain separate because operations/approvals/outputs/failure modes differ. Same rule for local retrieval, file search, command palette search, knowledge search, plugin search: specialized user-facing capabilities allowed; duplicated private substrates not.

## 14. Ingestion `retrieval.ingestion`
### 14.1 Definition
Converts external/workspace content into canonical source records, knowledge entries, graph records, index entries.
### 14.2 Codebase Ingestion
May: materialize/reference source; fingerprint files; dispatch to registered language/structure extractors; commit file/symbol/graph records; create/update knowledge entries; update retrieval indexes. Extraction semantics belong to Coder/owning subsystem/surface specs; File 12 owns only shared indexing+retrieval contract.
### 14.3 Document Ingestion
May: extract text+structure through Data Processor capabilities; dispatch to registered entity-extraction capabilities; commit source spans/sections/concepts/citations/knowledge entries; update lexical/vector/graph/metadata projections. Teacher, Data Processor, Memory, other producing specs decide meaningful entities.
### 14.4 Plugin-Bundled Knowledge
Plugins contribute knowledge through registered capability + package metadata; bundled entries still commit as `KnowledgeEntry` blocks + knowledge entities and pass through policy/scope/sensitivity/indexing rules. Plugin updates MUST preserve user-forked/user-edited entries unless user explicitly chooses replacement.

## 15. Workspace Instruction Files and ATLAS.md `retrieval.workspace-instruction-files-atlas-md`
`ATLAS.md`-style files are portable user-authored sources; `ATLAS.md` is default lookup name; name/lookup order/enablement/inclusion configurable. File 12 owns indexing these as source records + workspace-scoped knowledge entries when configured (makes them retrievable/inspectable/citeable/provenance-preserving). File 13 owns whether a resolved workspace instruction file is included in model request as instruction source; knowledge indexing alone does NOT grant instruction authority; instruction inclusion must carry source attribution, authority, sensitivity, budget metadata.

## 16. Events, Ledger, and Telemetry `retrieval.events-ledger-telemetry`
### 16.1 Custom Events
Retrieval/knowledge-base events are `Custom { namespace, name, payload }` extensions registered through File 10; File 12 reserves retrieval+knowledge namespaces, doesn't add specialized kinds to File 10's canonical event catalogue. Expected families: indexing lifecycle; index entry upsert/delete; index rebuild+corruption; retrieval query execution; knowledge entry proposal/approval/rejection/edit/archive/delete; ingestion lifecycle; adapter health.
### 16.2 Query Privacy
Durable retrieval-query records MUST apply configured privacy policy: store full query text only when allowed; otherwise store redacted/hashed query, structural query summary, or no query text; always preserve enough metadata to debug policy/source/index behavior without leaking restricted content. Telemetry is NOT source of truth for content; source records + index projections are.

## 17. Settings `retrieval.settings`
Configurable through canonical settings system. MUST cover: enabled index kinds per source/namespace; backend selection for lexical/vector/graph/structural/external adapter stages; chunking strategies per source type; embedding model+provider profiles; ranking policy+signal weights; reranker availability+thresholds; result count+snippet limits; cache+freshness policy; indexing concurrency; rebuild+repair behavior; query telemetry privacy; knowledge governance+proposal policy; adapter-specific capability loading. Specific numbers are settings/profile values, not canonical constants.

## 18. Maintenance and Freshness `retrieval.maintenance-freshness`
Freshness determined by source fingerprints, version anchors, provider identities, policy state. Timed sweeps, TTLs, scheduled cleanup allowed ONLY as configurable maintenance aids; MUST NOT be required for correctness; MUST NOT silently delete user-visible content. Expired cache entries become stale, not false; retrieval may refetch/warn/degrade/ask for approval per policy.

## 19. Replay and Debugging `retrieval.replay-debugging`
Retrieval MUST be inspectable. A result MUST be traceable to: query envelope, namespaces searched, indexes+adapters used, source versions/fingerprints, ranking policy, filters applied, redactions applied, errors+degraded stages. Replay MUST reconstruct same result or typed explanation of why exact reconstruction is impossible.

## 20. Extension Rules `retrieval.extension-rules`
Subsystems MAY register: custom index kinds, namespaces, source adapters, hit kinds, ranking signals, chunking strategies, entity/relationship extraction capabilities. Extensions MUST use shared capability/policy/event/block/version/settings systems; MUST NOT introduce parallel registries or bypass retrieval sensitivity enforcement.

## 21. Explicit Rejections `retrieval.explicit-rejections`
- treating a specific retrieval library/vector store/tokenizer/parser/web-search engine as canonical semantics
- creating private per-subsystem/per-surface retrieval substrates for content that should be retrievable through shared contract
- indexing Secret payload
- storing embedding vectors without embedding model identity
- using unstable index entry ids across rebuilds
- treating derived chunks as blocks unless deliberately promoted to `SourceExcerpt`
- making query telemetry leak private model-request content by default
- relying on timed sweeps/TTL/polling/elapsed time for correctness
- hardcoding ranking weights/snippet limits/rerank thresholds/cache TTLs/retry counts into canonical spec
- using legacy conversation identifiers as canonical terminology
- placing mutable knowledge curation fields directly on `KnowledgeEntry` blocks
- letting web search/web fetch/MCP retrieval/plugin retrieval bypass capability policy
- duplicating graph stores per subsystem/surface
- silently returning stale/partial retrieval results without typed warning

## 22. Consequences for Later Specs `retrieval.consequences-for-later-specs`
Later specs (context assembly, memory, model strategy, providers, plugins, MCP integrations, web, coder, teacher, data processing, UI presentation, evaluation, telemetry, storage, sync, security, packaging) MUST consume this retrieval contract instead of defining incompatible search/index/graph/knowledge primitives. New retrieval behavior is registered as an extension through mechanisms defined here.
