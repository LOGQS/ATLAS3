# Retrieval, Indexing, and Knowledge Base — Operative Core

## 1. Core Model {retrieval.core-model}
Four layers: source records; index projections; query/result contracts; knowledge-base entities.
Index rows are NOT canonical identity of user content.
All hits MUST normalize into `RetrievalHit`.

## 2. Retrieval Index {retrieval.retrieval-index}
### 2.1 Definition
`RetrievalIndex` required logical fields: `index_id`, `namespace_id`, `kind`, `source_scope`, `embedding_model_identity`, `tokenizer_identity`, `version_anchor`, `freshness_fingerprint`, `created_at`, `updated_at`, `health`.
### 2.2 Index Kinds
`Lexical`, `Vector`, `Hybrid`, `Graph`, `Structural`, `Metadata`, `ExternalAdapter`, `Custom { namespace, name }`
### 2.3 Index Entry Identity
MUST be deterministic, derived from namespace id, source identity, source version/fingerprint, index kind, chunking/extraction strategy identity, entry ordinal/structural address, embedding model identity.
Rebuilds over unchanged inputs MUST preserve entry identity.
### 2.4 Version Anchoring
Every entry MUST be anchored to source state.
Retrieval during replay MUST use indexes compatible with replayed version or rebuild compatible projections before answering.

## 3. Namespaces {retrieval.namespaces}
### 3.1 Definition
`IndexNamespace` required fields: `namespace_id`, `owner_subsystem_id`, `source_scope`, `allowed_index_kinds`, `sensitivity_policy`, `freshness_policy`, `rebuild_policy`.
### 3.2 Canonical Namespaces
`conversation:<conversation_id>`, `workspace:<workspace_id>`, `knowledge:<scope_id>`, `memory:<scope_id>`, `observation:<scope_id>`, `ingested_codebase:<workspace_id>`, `validator:<scope_id>`, `evaluator:<scope_id>`, `web_cache:<scope_id>`, `mcp_resource:<server_id>`, `custom:<namespace>:<name>`
### 3.3 Namespace Rules
Each namespace MUST apply own scope + sensitivity predicates before returning hits.
Sensitive entries MUST be indexed only in namespaces whose scope matches source scope.
Secret payloads MUST NEVER be indexed.

## 4. Source Records {retrieval.source-records}
### 4.1 Canonical Source Families
No subsystem/surface may create a parallel retrieval substrate; specialized sources MUST register adapters.
### 4.2 Entity-Relationship Projection
No private entity-relationship store.
### 4.3 External Sources
External sources MUST normalize to `RetrievalResult` contract.

## 5. Chunking and Excerpts {retrieval.chunking-excerpts}
### 5.1 Chunking Strategy
`Structural`, `Semantic`, `FixedWindow`, `Atomic`, `Custom { namespace, name }`
### 5.2 Derived Chunks
Derived chunks are NOT blocks. Durable promotion MUST commit as `SourceExcerpt` block.

## 6. Embeddings and Model Identity {retrieval.embeddings-model-identity}
### 6.1 Embedding Identity
Every stored vector MUST carry model identity, provider/backend identity, dimension, normalization semantics, input preprocessing identity, source content hash, creation timestamp.
Vectors of different model identities NOT comparable unless explicit compatibility adapter declares it safe.
### 6.2 Backends
`Local`, `Api`, `Plugin`, `Mcp`, `Custom { namespace, name }`

## 7. Query Contract {retrieval.query-contract}
### 7.1 Retrieval Query
`RetrievalQuery` MUST carry: `query_id`, `query_kind`, `target_namespaces`, `source_filters`, `scope_context`, `sensitivity_context`, `ranking_policy`, `result_shape`, `budget`, `caller_run_id`, `requested_by`.
Query kinds: `Text`, `Vector`, `Hybrid`, `GraphTraversal`, `StructuredLookup`, `ById`, `Custom { namespace, name }`
### 7.2 Filters
MUST be typed fields, not prose.

## 8. Retrieval Pipeline {retrieval.retrieval-pipeline}
### 8.1 Standard Pipeline
validate; resolve namespaces+adapters; dispatch source-specific stages; normalize hits; apply scope+sensitivity filters; deduplicate; combine ranking signals; rerank; create snippets/spans/overflow markers; record telemetry + return `RetrievalResult`.
### 8.3 Deduplication
MUST preserve provenance; MUST NOT hide contradictory evidence, policy restrictions, or materially different source versions.
### 8.4 External Retrieval
Live web search, web fetch, MCP retrieval, remote plugin retrieval MUST be explicit capability calls; not hidden side effects.

## 9. Retrieval Result {retrieval.retrieval-result}
### 9.1 Result Envelope
`RetrievalResult` MUST carry: `query_id`, `status`, `hits`, `overflow`, `applied_filters`, `ranking_policy`, `source_namespaces`, `redaction_summary`, `freshness_summary`, `errors`.
### 9.2 Hit Envelope
`RetrievalHit` MUST carry: `hit_id`, `hit_kind`, `source_ref`, `scope`, `sensitivity`, `snippet`, `source_span`, `scores`, `provenance`, `freshness`, `access_state`.
Hit kinds: `BlockHit`, `KnowledgeEntryHit`, `FileHit`, `ArtifactHit`, `ClaimHit`, `EvidenceHit`, `CitationHit`, `ObservationHit`, `MemoryHit`, `GraphHit`, `WebHit`, `McpResourceHit`, `RedactedHit`, `Custom { namespace, name }`
### 9.3 Redacted Hits
MUST NOT include secret payload, credential material, or restricted snippets.

## 10. Knowledge Base {retrieval.knowledge-base}
### 10.2 Knowledge Entry Block
Block does NOT own mutable curation fields.
### 10.3 Knowledge Entity
MUST carry: `knowledge_entry_id`, `block_id`, `scope`, `source`, `validation_status`, `lifecycle_status`, `tags`, `featured`, `owner_subsystem_id`, `governance_policy`, `created_at`, `updated_at`.
### 10.4 Scope
`Global`, `User`, `Workspace { workspace_id }`, `Conversation { conversation_id }`, `Plugin { plugin_id }`, `Subsystem { subsystem_id }`, `Custom { namespace, id }`
### 10.5 Sources
`UserAuthored`, `AssistantProposed`, `ImportedDocument`, `IngestedCodebase`, `PluginBundled`, `SystemGenerated`, `ExternalSnapshot`, `MemoryDerived`, `Custom { namespace, name }`
Source MUST NOT bypass capability policy.
### 10.6 Lifecycle
`Proposed`, `Approved`, `Rejected`, `Archived`, `Superseded`, `HardDeleted`

## 11. Sensitivity {retrieval.sensitivity}
### 11.1 Core Rule
Secret payload MUST NEVER enter an index.
### 11.2 Sensitive Content
Sensitive content MUST be indexed only inside source's allowed scope.
### 11.3 Per-Field Sensitivity
Indexers MUST exclude Secret fields.
A chunk crossing into Secret material MUST be split or rejected; MUST NOT carry the Secret segment.

## 12. Indexing Pipeline {retrieval.indexing-pipeline}
### 12.1 Commit Path
source discovery; fingerprinting; policy+sensitivity validation; strategy selection; chunk/entity projection; embedding/lexical processing; deterministic entry id assignment; atomic index commit; health+freshness update; event + ledger recording.
### 12.2 Incremental Updates
Timed sweeps MUST NOT be primary correctness mechanism.
### 12.3 Rebuild
MUST be deterministic over same canonical source state, settings profile, strategy identities, model identities.
MUST preserve logical entry identity when source inputs unchanged.
### 12.4 Corruption Handling
On stale/corrupted/incompatible index, retrieval MUST rebuild, degrade with typed warning, or fail with typed error.
Silent partial retrieval FORBIDDEN.

## 13. Capability Surface {retrieval.capability-surface}
### 13.2 Capability Metadata
Every retrieval capability declaration MUST identify: capability class, source subsystem, touched resources as machine-parseable expressions, side-effect class, reversibility class, replay class, data sensitivity, output contract, postconditions, concurrency class.
MUST NOT use prose-only resource declarations for readable/writable resources.

## 14. Ingestion {retrieval.ingestion}
### 14.4 Plugin-Bundled Knowledge
Bundled entries MUST commit as `KnowledgeEntry` blocks + knowledge entities and pass through policy/scope/sensitivity/indexing rules.
Plugin updates MUST preserve user-forked/user-edited entries unless user explicitly chooses replacement.

## 15. Workspace Instruction Files and ATLAS.md {retrieval.workspace-instruction-files-atlas-md}
Knowledge indexing alone does NOT grant instruction authority.
Instruction inclusion MUST carry source attribution, authority, sensitivity, budget metadata.

## 16. Events, Ledger, and Telemetry {retrieval.events-ledger-telemetry}
### 16.1 Custom Events
Retrieval/knowledge-base events MUST be `Custom { namespace, name, payload }` extensions registered through File 10.
### 16.2 Query Privacy
Durable retrieval-query records MUST apply configured privacy policy.

## 17. Settings {retrieval.settings}
MUST cover: enabled index kinds; backend selection; chunking strategies; embedding model+provider profiles; ranking policy+signal weights; reranker availability+thresholds; result count+snippet limits; cache+freshness policy; indexing concurrency; rebuild+repair behavior; query telemetry privacy; knowledge governance+proposal policy; adapter-specific capability loading.

## 18. Maintenance and Freshness {retrieval.maintenance-freshness}
Timed sweeps/TTLs/scheduled cleanup MUST NOT be required for correctness; MUST NOT silently delete user-visible content.

## 19. Replay and Debugging {retrieval.replay-debugging}
Retrieval MUST be inspectable.
A result MUST be traceable to query envelope, namespaces searched, indexes+adapters used, source versions/fingerprints, ranking policy, filters applied, redactions applied, errors+degraded stages.
Replay MUST reconstruct same result or typed explanation of why exact reconstruction is impossible.

## 20. Extension Rules {retrieval.extension-rules}
Extensions MUST use shared capability/policy/event/block/version/settings systems; MUST NOT introduce parallel registries or bypass retrieval sensitivity enforcement.

## 21. Explicit Rejections {retrieval.explicit-rejections}
- treating a specific library/store/tokenizer/parser/engine as canonical semantics
- private per-subsystem retrieval substrates
- indexing Secret payload
- storing embedding vectors without embedding model identity
- unstable index entry ids across rebuilds
- derived chunks as blocks unless promoted to `SourceExcerpt`
- query telemetry leaking private model-request content by default
- relying on timed sweeps/TTL/polling for correctness
- hardcoding ranking weights/snippet limits/thresholds/TTLs/retry counts
- legacy conversation identifiers as canonical terminology
- mutable curation fields directly on `KnowledgeEntry` blocks
- web/MCP/plugin retrieval bypassing capability policy
- duplicating graph stores per subsystem/surface
- silently returning stale/partial results without typed warning

## 22. Consequences for Later Specs {retrieval.consequences-for-later-specs}
Later specs MUST consume this retrieval contract instead of defining incompatible search/index/graph/knowledge primitives.
New retrieval behavior MUST be registered as an extension through mechanisms defined here.
