# Retrieval, Indexing, and Knowledge Base

## Status

Canonical.

## Scope

This file defines the shared retrieval substrate for Atlas:

- retrieval indexes as rebuildable projections over blocks, versions, observations, knowledge entities, and registered external sources
- index namespaces, index kinds, index entries, chunking, embeddings, freshness, rebuild, and replay semantics
- the normalized query and result contracts used by local search, knowledge search, file search, web retrieval adapters, MCP resources, and domain retrieval
- the curated knowledge-base entity layer over `KnowledgeEntry` blocks
- sensitivity-aware indexing and retrieval
- retrieval-related capabilities, policy boundaries, events, settings, and extension points

This file does not define:

- block storage, block lifecycle, or the base `BlockKind` catalogue; File 08 owns those
- artifact, claim, evidence, citation, and provenance semantics; File 09 owns those
- event envelopes, ledger envelopes, hooks, and live-stream transport; File 10 owns those
- version graph mechanics and materialized views; File 11 owns those
- capability declarations and policy evaluation; Files 05 and 06 own those
- context assembly, memory, provider selection, plugin packaging, UI presentation, or storage schema; their owning specs consume this contract

## Source Resolution

This file resolves the retrieval and knowledge-base material from the existing canonical files, specbase retrieval and knowledge-base references, file/search/tool references, compressed repository notes, and existing ecosystem notes. Source-specific implementation details were evaluated but not copied into the canonical contract.

Resolved design:

- retrieval is one shared substrate with source-specific adapters, not one private index system per domain
- canonical specs define behavior and contracts, not permanent engines or libraries
- local retrieval, file search, web search, web fetch, MCP retrieval, knowledge search, and domain retrieval can have specialized capabilities while sharing normalized retrieval results
- knowledge-base curation is entity-layer state over `KnowledgeEntry` blocks, not metadata welded into every block
- graph extraction is domain-owned, but the graph projection and retrieval contract are shared
- time-based sweeps and TTLs may optimize maintenance, but correctness must come from events, version identity, fingerprints, and policy

## 1. Core Model

Anchor: `retrieval.core-model`

Retrieval has four layers:

- source records: blocks, materialized files, observations, knowledge entities, graph entities, external resources, and capability-produced records
- index projections: lexical, vector, graph, structural, metadata, and source-specific projections derived from source records
- query and result contracts: the typed request and normalized hit envelope every consumer sees
- knowledge-base entities: curated records that manage lifecycle, validation, tags, featured state, and governance over `KnowledgeEntry` blocks

Indexes are projections. They may be rebuilt from canonical source records, active versions, source fingerprints, and model identities. Index rows are not the canonical identity of user content.

Retrieval is source-aware. A file search result, knowledge result, web result, MCP result, memory result, and graph result may have different hit payloads, but all normalize into `RetrievalHit` so execution, context assembly, UI, and evaluation do not need private result formats.

## 2. Retrieval Index

Anchor: `retrieval.retrieval-index`

### 2.1 Definition

A `RetrievalIndex` is a named projection over one or more source pools.

Required logical fields:

- `index_id`
- `namespace_id`
- `kind`
- `source_scope`
- `embedding_model_identity` when dense vectors are stored
- `tokenizer_identity` when lexical tokenization is stored
- `version_anchor`
- `freshness_fingerprint`
- `created_at`
- `updated_at`
- `health`

Physical storage layout is not defined here.

### 2.2 Index Kinds

Canonical index kinds:

- `Lexical` - token or term based lookup
- `Vector` - embedding similarity lookup
- `Hybrid` - coordinated lexical plus vector lookup
- `Graph` - entity and relationship traversal projection
- `Structural` - path, symbol, heading, schema, or hierarchy lookup
- `Metadata` - field and facet lookup
- `ExternalAdapter` - normalized search over an external source
- `Custom { namespace, name }` - registered extension

An index kind defines observable retrieval behavior, not an engine. A built-in lexical or vector backend may use a specific library, but that library is an implementation behind the index contract.

### 2.3 Index Entry Identity

Index entries must have deterministic identities. The identity is derived from:

- namespace id
- source identity
- source version or source fingerprint
- index kind
- chunking or extraction strategy identity
- entry ordinal or structural address
- embedding model identity when vectorized

Rebuilds over unchanged inputs must preserve entry identity. This is required for replay, debugging, cache reuse, and stable citations.

### 2.4 Version Anchoring

Every index entry is anchored to the source state it was derived from:

- block entries anchor to block id plus block revision
- file entries anchor to workspace id plus path plus content hash
- versioned views anchor to `ContextVersion`
- web and external entries anchor to fetched snapshot id or source fingerprint
- graph entries anchor to the extraction capability, source identity, and extraction version

Retrieval during replay must use indexes compatible with the replayed version or rebuild compatible projections before answering.

## 3. Namespaces

Anchor: `retrieval.namespaces`

### 3.1 Definition

An `IndexNamespace` scopes entries by purpose and access boundary.

Required logical fields:

- `namespace_id`
- `owner_subsystem_id`
- `source_scope`
- `allowed_index_kinds`
- `sensitivity_policy`
- `freshness_policy`
- `rebuild_policy`

### 3.2 Canonical Namespaces

Canonical namespace families:

- `conversation:<conversation_id>`
- `workspace:<workspace_id>`
- `knowledge:<scope_id>`
- `memory:<scope_id>`
- `observation:<scope_id>`
- `ingested_codebase:<workspace_id>`
- `validator:<scope_id>`
- `evaluator:<scope_id>`
- `web_cache:<scope_id>`
- `mcp_resource:<server_id>`
- `custom:<namespace>:<name>`

The envelope term is `conversation_id`. Legacy `chat_id` terminology is not canonical.

### 3.3 Namespace Rules

Namespaces are access boundaries. A query may target multiple namespaces, but every namespace applies its own scope and sensitivity predicates before hits are returned.

Sensitive entries can be indexed only in namespaces whose scope matches the source scope. Secret payloads are never indexed.

## 4. Source Records

Anchor: `retrieval.source-records`

### 4.1 Canonical Source Families

Retrieval sources include:

- blocks from File 08
- active materialized views from File 11
- artifacts, claims, evidence, citations, observations, and provenance records from File 09
- knowledge-base entities and their `KnowledgeEntry` blocks
- graph entity and relationship records
- workspace files and codebase ingestion records
- memory records declared by the Memory spec
- web search and web fetch snapshots
- MCP resources and external integration records
- custom source records registered by subsystems

No domain may create a parallel retrieval substrate for these records. Domain-specific sources register adapters into this substrate.

### 4.2 Entity-Relationship Projection

Entity and relationship records are domain-populated projections. File 12 owns the index and retrieval contract over them; domain specs own extraction semantics.

Examples:

- codebase ingestion may extract files, modules, functions, classes, imports, calls, and references
- document ingestion may extract concepts, sections, prerequisites, citations, and glossary terms
- memory processing may extract factual triples and user preference relations
- data-processing domains may extract dataset, column, schema, and lineage entities

Each extraction capability commits records through the canonical indexing pipeline. No domain gets a private entity-relationship store.

### 4.3 External Sources

External retrieval sources enter through adapters. An adapter may call web search, web fetch, an MCP resource, a local service, or a plugin-provided source, but it must normalize results to the same `RetrievalResult` contract.

External adapters may share underlying fetchers, caches, parsers, ranking services, and credential handling. They remain distinct capabilities when their user-facing operation, policy profile, or result contract differs. Shared implementation is encouraged; duplicated substrate is not.

## 5. Chunking and Excerpts

Anchor: `retrieval.chunking-excerpts`

### 5.1 Chunking Strategy

Chunking turns source records into derived index entries. Canonical strategy families:

- `Structural` - source-defined boundaries such as headings, AST nodes, cells, pages, symbols, records, or sections
- `Semantic` - sentence, paragraph, topic, or embedding-aware boundaries
- `FixedWindow` - bounded size with optional overlap
- `Atomic` - one source record produces one entry
- `Custom { namespace, name }`

Strategy selection is based on source type, content type, user settings, subsystem profile, and capability declaration.

### 5.2 Derived Chunks

Derived chunks are not blocks. They are index entries.

If a chunk or excerpt must become durable conversation context, evidence, or user-visible material, it is committed as a `SourceExcerpt` block through File 08. `SourceExcerpt` describes what the content is; "RAG chunk" is not a canonical block kind.

### 5.3 Source Spans

When a hit comes from text-like content, it should carry a source span when the source supports stable location. Source spans allow citation, highlighting, excerpt promotion, and audit without copying whole source payloads into the transcript.

## 6. Embeddings and Model Identity

Anchor: `retrieval.embeddings-model-identity`

### 6.1 Embedding Identity

Every stored embedding vector must carry:

- model identity
- provider or backend identity
- dimension
- normalization semantics
- input preprocessing identity
- source content hash
- creation timestamp

Vectors produced by different model identities are not comparable unless an explicit compatibility adapter declares that comparison safe.

### 6.2 Backends

Canonical backend classes:

- `Local`
- `Api`
- `Plugin`
- `Mcp`
- `Custom { namespace, name }`

Backend class is not a library choice. Model strategy and provider specs decide which implementations are available, preferred, throttled, or failed over.

## 7. Query Contract

Anchor: `retrieval.query-contract`

### 7.1 Retrieval Query

A `RetrievalQuery` must carry:

- `query_id`
- `query_kind`
- `target_namespaces`
- `source_filters`
- `scope_context`
- `sensitivity_context`
- `ranking_policy`
- `result_shape`
- `budget`
- `caller_run_id` when invoked during execution
- `requested_by` capability or subsystem

Query kinds:

- `Text`
- `Vector`
- `Hybrid`
- `GraphTraversal`
- `StructuredLookup`
- `ById`
- `Custom { namespace, name }`

### 7.2 Filters

Filters are typed fields, not prose:

- source family
- block kind
- path or path pattern
- MIME/content type
- time range over source timestamps
- version anchor
- namespace
- scope
- sensitivity
- tags or curation facets from the knowledge entity layer
- graph entity or relationship type
- custom filter declared by the source adapter

### 7.3 Result Shape

Result shape controls:

- maximum hit count
- snippet or excerpt preference
- whether full content references may be returned
- whether score details are included
- whether redacted hits are included
- whether graph context is expanded

Specific numeric values are settings/profile choices, not canonical constants.

## 8. Retrieval Pipeline

Anchor: `retrieval.retrieval-pipeline`

### 8.1 Standard Pipeline

The standard retrieval pipeline:

1. validate query shape and policy
2. resolve namespaces and adapters
3. dispatch source-specific retrieval stages
4. normalize hits
5. apply scope and sensitivity filters
6. deduplicate
7. combine ranking signals
8. optionally rerank through configured local, API, plugin, or MCP rerankers
9. create snippets, source spans, and overflow markers
10. record policy-safe telemetry and return `RetrievalResult`

Each stage is replaceable behind the contract. The pipeline may skip stages that are irrelevant to the query.

### 8.2 Ranking Signals

Canonical ranking signal families:

- lexical relevance
- dense similarity
- graph proximity
- structural match
- source freshness
- provenance quality
- validation status
- featured or pinned curation state
- path or workspace relevance
- user or workspace preference
- custom registered signal

Combination policy is configurable. Canonical behavior requires score attribution, not a fixed formula.

### 8.3 Deduplication

Deduplication must preserve provenance. When multiple hits represent the same source content, the result may collapse them into one visible hit only if it records the contributing sources and score signals.

Deduplication must not hide contradictory evidence, policy restrictions, or materially different source versions.

### 8.4 External Retrieval

Live web search, web fetch, MCP retrieval, and remote plugin retrieval are explicit capability calls. They do not happen as a hidden side effect of local retrieval.

Cached external snapshots can be searched locally through their namespace when policy allows. Cache expiry is an optimization, not a correctness condition; source fingerprints and fetch snapshots define freshness.

## 9. Retrieval Result

Anchor: `retrieval.retrieval-result`

### 9.1 Result Envelope

A `RetrievalResult` must carry:

- `query_id`
- `status`
- `hits`
- `overflow`
- `applied_filters`
- `ranking_policy`
- `source_namespaces`
- `redaction_summary`
- `freshness_summary`
- `errors`

### 9.2 Hit Envelope

Every `RetrievalHit` must carry:

- `hit_id`
- `hit_kind`
- `source_ref`
- `scope`
- `sensitivity`
- `snippet`
- `source_span` when available
- `scores`
- `provenance`
- `freshness`
- `access_state`

Canonical hit kinds:

- `BlockHit`
- `KnowledgeEntryHit`
- `FileHit`
- `ArtifactHit`
- `ClaimHit`
- `EvidenceHit`
- `CitationHit`
- `ObservationHit`
- `MemoryHit`
- `GraphHit`
- `WebHit`
- `McpResourceHit`
- `RedactedHit`
- `Custom { namespace, name }`

### 9.3 Redacted Hits

A redacted hit may reveal that a relevant source exists only when policy permits safe disclosure. It must not include secret payload, credential material, or restricted snippets.

## 10. Knowledge Base

Anchor: `retrieval.knowledge-base`

### 10.1 Definition

The knowledge base is a curated entity layer over `KnowledgeEntry` blocks.

`KnowledgeEntry` is the block content carrier. The knowledge-base entity owns mutable curation state.

### 10.2 Knowledge Entry Block

A `KnowledgeEntry` block carries:

- title or display name
- description
- content or external content reference
- source references
- scope
- sensitivity
- provenance links

The block does not own mutable curation fields such as tags, featured state, validation status, lifecycle state, proposal state, or last-reference statistics.

### 10.3 Knowledge Entity

A knowledge entity must carry:

- `knowledge_entry_id`
- `block_id`
- `scope`
- `source`
- `validation_status`
- `lifecycle_status`
- `tags`
- `featured`
- `owner_subsystem_id`
- `governance_policy`
- `created_at`
- `updated_at`

`last_referenced_at`, usage counts, ranking feedback, and similar values are computed projections. They are not identity fields and are not required to be durable curation metadata.

### 10.4 Scope

Knowledge scopes:

- `Global`
- `User`
- `Workspace { workspace_id }`
- `Conversation { conversation_id }`
- `Plugin { plugin_id }`
- `Subsystem { subsystem_id }`
- `Custom { namespace, id }`

Scope controls visibility, retrieval namespace, approval requirements, and fork/import behavior.

### 10.5 Sources

Knowledge sources:

- `UserAuthored`
- `AssistantProposed`
- `ImportedDocument`
- `IngestedCodebase`
- `PluginBundled`
- `SystemGenerated`
- `ExternalSnapshot`
- `MemoryDerived`
- `Custom { namespace, name }`

Source affects governance and provenance. It does not bypass capability policy.

### 10.6 Lifecycle

Knowledge lifecycle states:

- `Proposed`
- `Approved`
- `Rejected`
- `Archived`
- `Superseded`
- `HardDeleted`

Proposal expiry, auto-archival, and cleanup are user-policy choices. Time-based expiry is never a correctness requirement.

## 11. Sensitivity

Anchor: `retrieval.sensitivity`

### 11.1 Core Rule

Secret payload never enters an index.

If a `KnowledgeEntry` or source block is Secret, its body is not indexed. A non-secret description may be indexed only if the description itself is safe under File 08 sensitivity rules.

### 11.2 Sensitive Content

Sensitive content may be indexed only inside the source's allowed scope. Retrieval outside that scope returns no hit or a redacted hit, depending on policy.

### 11.3 Per-Field Sensitivity

If a source has field-level sensitivity, indexers must exclude Secret fields and may index Public or Sensitive fields according to their scopes. A chunk that crosses into Secret material must be split or rejected; it must not carry the Secret segment.

## 12. Indexing Pipeline

Anchor: `retrieval.indexing-pipeline`

### 12.1 Commit Path

Indexing proceeds through:

1. source discovery
2. source fingerprinting
3. policy and sensitivity validation
4. strategy selection
5. chunk or entity projection
6. embedding or lexical processing when needed
7. deterministic entry id assignment
8. atomic index commit
9. health and freshness update
10. custom event and ledger recording when applicable

### 12.2 Incremental Updates

Incremental updates are based on source fingerprints, version anchors, and explicit change events. Timed sweeps may repair missed changes but must not be the primary correctness mechanism.

### 12.3 Rebuild

Rebuild must be deterministic over the same canonical source state, settings profile, strategy identities, and model identities. Rebuild may change physical storage but must preserve logical entry identity when source inputs did not change.

### 12.4 Corruption Handling

If an index is missing, stale, corrupted, or incompatible with the active version, retrieval must either rebuild, degrade with a typed warning, or fail with a typed error. Silent partial retrieval is forbidden.

## 13. Capability Surface

Anchor: `retrieval.capability-surface`

### 13.1 Capability Families

Retrieval-related capabilities include:

- knowledge search, read, propose, write, import, archive, and delete
- local file find, grep, and structural search
- block and artifact lookup
- graph search and traversal
- web search and web fetch
- MCP resource search and read
- index rebuild, inspect, and health check
- source ingestion and re-ingestion
- custom subsystem retrieval capabilities

Exact capability declarations belong to File 05. Policy behavior belongs to File 06.

### 13.2 Capability Metadata

Every retrieval capability declaration must identify:

- capability class
- source subsystem
- touched resources as machine-parseable resource expressions
- side-effect class
- reversibility class
- replay class
- data sensitivity
- output contract
- postconditions
- concurrency class

Retrieval capabilities must not use prose-only resource declarations for readable or writable resources.

### 13.3 Shared Implementation, Separate Capabilities

Capabilities may share lower-level services. For example, web search and web fetch may share URL normalization, network policy checks, snapshot storage, parser services, and cache lookup. They remain separate capabilities because their operations, approvals, outputs, and failure modes differ.

The same rule applies to local retrieval, file search, command palette search, knowledge search, and plugin search: specialized user-facing capabilities are allowed, duplicated private substrates are not.

## 14. Ingestion

Anchor: `retrieval.ingestion`

### 14.1 Definition

Ingestion converts external or workspace content into canonical source records, knowledge entries, graph records, and index entries.

### 14.2 Codebase Ingestion

Codebase ingestion may:

- materialize or reference the source
- fingerprint files
- dispatch to registered language and structure extractors
- commit file, symbol, and graph records
- create or update knowledge entries
- update retrieval indexes

Extraction semantics belong to the Coder or owning domain specs. File 12 owns only the shared indexing and retrieval contract.

### 14.3 Document Ingestion

Document ingestion may:

- extract text and structure through Data Processor capabilities
- dispatch to registered entity-extraction capabilities
- commit source spans, sections, concepts, citations, and knowledge entries
- update lexical, vector, graph, and metadata projections

Teacher, Data Processor, Memory, and other domain specs decide what entities are meaningful for their content.

### 14.4 Plugin-Bundled Knowledge

Plugins may contribute knowledge through registered capability and package metadata. Plugin-bundled entries still commit as `KnowledgeEntry` blocks plus knowledge entities and pass through policy, scope, sensitivity, and indexing rules.

Plugin updates must preserve user-forked or user-edited entries unless the user explicitly chooses replacement.

## 15. Workspace Instruction Files and ATLAS.md

Anchor: `retrieval.workspace-instruction-files-atlas-md`

Workspace-local instruction files such as `ATLAS.md` are portable user-authored sources. `ATLAS.md` is the default lookup name; the name, lookup order, enablement, and inclusion behavior are configurable.

File 12 owns indexing these files as source records and workspace-scoped knowledge entries when configured. Indexing makes them retrievable, inspectable, citeable, and provenance-preserving.

File 13 owns whether a resolved workspace instruction file is included in the model request as an instruction source. Knowledge indexing alone does not grant instruction authority, and instruction inclusion must still carry source attribution, authority, sensitivity, and budget metadata.

## 16. Events, Ledger, and Telemetry

Anchor: `retrieval.events-ledger-telemetry`

### 16.1 Custom Events

Retrieval and knowledge-base events are `Custom { namespace, name, payload }` extensions registered through File 10. File 12 reserves the retrieval and knowledge namespaces; it does not add domain-specific kinds to File 10's canonical event catalogue.

Expected event families:

- indexing lifecycle
- index entry upsert/delete
- index rebuild and corruption
- retrieval query execution
- knowledge entry proposal, approval, rejection, edit, archive, delete
- ingestion lifecycle
- adapter health

### 16.2 Query Privacy

Durable records of retrieval queries must apply the configured privacy policy:

- store full query text only when allowed
- otherwise store a redacted query, hashed query, structural query summary, or no query text
- always preserve enough metadata to debug policy, source, and index behavior without leaking restricted content

Telemetry is not the source of truth for content. Source records and index projections are.

## 17. Settings

Anchor: `retrieval.settings`

Retrieval and knowledge behavior is configurable through the canonical settings system.

Settings must cover:

- enabled index kinds per source and namespace
- backend selection for lexical, vector, graph, structural, and external adapter stages
- chunking strategies per source type
- embedding model and provider profiles
- ranking policy and signal weights
- reranker availability and thresholds
- result count and snippet limits
- cache and freshness policy
- indexing concurrency
- rebuild and repair behavior
- query telemetry privacy
- knowledge governance and proposal policy
- adapter-specific capability loading

Specific numbers are settings/profile values, not canonical constants.

## 18. Maintenance and Freshness

Anchor: `retrieval.maintenance-freshness`

Freshness is determined by source fingerprints, version anchors, provider identities, and policy state.

Timed sweeps, TTLs, and scheduled cleanup are allowed only as configurable maintenance aids. They must not be required for correctness and must not silently delete user-visible content.

Expired cache entries become stale. They do not become false. Retrieval may refetch, warn, degrade, or ask for approval depending on policy and capability settings.

## 19. Replay and Debugging

Anchor: `retrieval.replay-debugging`

Retrieval must be inspectable.

A retrieval result must be traceable to:

- query envelope
- namespaces searched
- indexes and adapters used
- source versions or fingerprints
- ranking policy
- filters applied
- redactions applied
- errors and degraded stages

Replay must be able to reconstruct either the same result or a typed explanation of why exact reconstruction is impossible.

## 20. Extension Rules

Anchor: `retrieval.extension-rules`

Subsystems may register:

- custom index kinds
- custom namespaces
- custom source adapters
- custom hit kinds
- custom ranking signals
- custom chunking strategies
- custom entity and relationship extraction capabilities

Extensions must use the shared capability, policy, event, block, version, and settings systems. They must not introduce parallel registries or bypass retrieval sensitivity enforcement.

## 21. Explicit Rejections

Anchor: `retrieval.explicit-rejections`

The following are rejected:

- treating a specific retrieval library, vector store, tokenizer, parser, or web-search engine as canonical semantics
- creating private per-domain retrieval substrates for content that should be retrievable through the shared contract
- indexing Secret payload
- storing embedding vectors without embedding model identity
- using unstable index entry ids across rebuilds
- treating derived chunks as blocks unless deliberately promoted to `SourceExcerpt`
- making query telemetry leak full private prompts by default
- relying on timed sweeps, TTL, polling, or elapsed time for correctness
- hardcoding ranking weights, snippet limits, rerank thresholds, cache TTLs, or retry counts into the canonical spec
- using `Chat` or `chat_id` as canonical terminology
- placing mutable knowledge curation fields directly on `KnowledgeEntry` blocks
- letting web search, web fetch, MCP retrieval, or plugin retrieval bypass capability policy
- duplicating graph stores per domain
- silently returning stale or partial retrieval results without typed warning

## 22. Consequences for Later Specs

Anchor: `retrieval.consequences-for-later-specs`

Later specs covering context assembly, memory, model strategy, providers, plugins, MCP integrations, web, coder, teacher, data processing, UI presentation, evaluation, telemetry, storage, sync, security, and packaging must consume this retrieval contract instead of defining incompatible search, index, graph, or knowledge primitives.

When a later spec needs new retrieval behavior, it registers an extension through the mechanisms defined here.
