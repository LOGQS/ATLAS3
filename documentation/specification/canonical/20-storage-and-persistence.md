# Storage and Persistence

## Status

Canonical. This file defines the physical and logical storage substrate for ATLAS3. It realizes the persistence contracts that Files 01–19 previously delegated to the Storage and Persistence spec. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the storage substrate as a typed contract — an embedded relational store plus a content-addressed blob store plus a rebuildable projection store — and the rule that the concrete engine is a replaceable implementation behind that contract (`core.stack-commitments`, File 01 §9; `core.extension-integrity`, File 01 §7.10)
- the three storage planes and the source-of-truth split: the durable substrate (append-only and immutable source-of-truth records), the content-addressed blob store (large and binary payloads), and the projection store (rebuildable read-optimized views), per `core.projection` (File 01 §6.11)
- the durable-substrate contract — what every prior file's persistence contract becomes when realized: the substrate families, the per-record schema-version stamp, soft-reference discipline, and the rejection of unkeyed model-dependent scalars
- the storage engine and the connection model — single-writer / many-reader concurrency, write-ahead durability, the writer-serialization discipline, and streaming write-coalescing
- the transactional guarantees — atomicity, durability, crash-consistency, isolation, and the alignment of storage commits with the commit boundaries Files 04, 08, and 11 declare
- the content-addressed blob store — content addressing, deduplication, the inline-versus-external threshold, atomic blob writes, reference-counted garbage collection with a reconciliation sweep, and integrity verification
- the projection store and rebuild orchestration — projection registration, rebuild triggers, startup rebuild-and-verification, integrity checking, and rebuild-on-corruption
- the physical layout and the locality partition — the two-substrate split that makes File 15's `DeviceLocal` / `NeverSync` locality a structural property, the on-disk directory layout, and the device-local hash-chained audit overlay
- physical storage encoding and its strict separation from the `CanonicalEncoding` used for hashing (`core.canonical-encoding`, File 01 §6.15; `core.canonical-hash`, File 01 §7.14)
- schema evolution and migration — forward-only numbered migrations, the schema-version control record, stored-value normalization-on-load, the typed settings-migration kinds, the pre-migration backup safety rule, and the human-governed-schema rule
- retention, garbage collection, and storage accounting — the storage-side realization of the typed tombstone, compaction, and retention operations Files 08–11 define; the no-time-based-pruning rule; and storage-usage accounting with reclamation at every granularity (`core.non-destructive-by-default`, File 01 §7.13)
- backup, integrity detection, and the recovery hierarchy — consistent snapshots without pausing the writer, corruption detection, and the projection-rebuild-then-substrate-restore-then-quarantine recovery order
- lifecycle, startup, shutdown, and deterministic reconstruction — the startup phase order, projection rebuild and run/lease recovery, the shutdown flush, the single-instance lock, and orphan reconciliation
- the storage capability surface, the storage event vocabulary, and the settings dimensions
- the secret-vault and audit-overlay storage boundaries with File 22

This file does not define:

- the semantic durability contracts themselves — what is durable, computed, or reconstructable for each substrate is owned by that substrate's file (`block.block-persistence-contract`, File 08 §13; `artifact.persistence-contract`, File 09 §18; the ledger durability contract, `ledger.execution-ledger`, File 10 §3.5; `ledger.sensitivity-aware-persistence-retention`, File 10 §10; `version.persistence-contract`, File 11 §18; `context.persistence-settings`, File 13 §20; the memory persistence contract, File 14; `settings.logical-persistence`, File 15 §17; the provider usage/rate-limit durability rules, File 17; `world.persistence-contract`, File 18 §14; `perception.persistence`, File 19 §16). This file realizes them; it does not re-own them
- the sync transport, embedded-replica replication protocol, conflict-resolution semantics, import/export bundle format, or cross-device merge — File 21 owns those; this file owns only the physical partition the sync layer replicates and the per-device partition it never touches. The version-tree-aware merge semantics remain `version.cross-device-sync-conflict-resolution` (File 11 §19)
- the credential-vault internals, the encryption cryptography, key derivation, the OS-keyring integration, and trust state — File 22 owns those; this file owns only the vault file's existence, location, and the boundary that raw `Secret` material never enters the durable substrate (`secret.backend-boundary`, File 22 §4)
- workspace identity, materialized workspace directories, the disk-to-block materialization mirror, worktree management, and per-surface file layout — File 24 owns those; this file owns the content-addressed blob store those materializations resolve external content from, not the workspace mirror
- the row-and-column physical schema of any single table as a frozen artifact — this file specifies the substrate families, their source-of-truth-versus-projection classification, their locality, and their durability invariants; the concrete column layout is the migration-script realization governed by §10, not a canonical freeze
- block, artifact, ledger, version, settings, world, memory, retrieval, or provider semantics — the owning files define those; this file stores them
- UI rendering of storage-usage dashboards, backup managers, cleanup surfaces, or migration progress — File 37 and File 38 own those; this file specifies the data contracts they consume

## Source Resolution

This file resolves local-database, embedded-engine, blob-store, projection-store, transactional, migration, retention, backup, corruption-recovery, startup-and-shutdown, on-disk-layout, and physical-encoding material into one boundary: the substrate that realizes every prior file's persistence contract on local storage.

Resolved design:

- ATLAS3 has one storage substrate, expressed as a typed contract with three planes: a durable substrate (the append-only and immutable source of truth), a content-addressed blob store (large and binary payloads), and a projection store (rebuildable read-optimized views). The committed realization is an embedded relational engine (`SQLite` / `libsql`, `core.stack-commitments`, File 01 §9) plus a content-addressed file store; the engine is replaceable behind the contract and is never the semantic boundary (`core.extension-integrity`, File 01 §7.10).
- The source-of-truth split is load-bearing. Durable-substrate records and content-addressed blobs are authoritative; every projection — materialized views, indexes, hot tables, caches — is derived, declares its rebuild trigger, holds no durable fact, and is rebuilt rather than recovered when stale or corrupt (`core.projection`, File 01 §6.11). The cost of a corrupt projection is a rebuild; the cost of a corrupt substrate is a restore; neither is silent data loss.
- Durable history and live coordination are separate concerns (`core.durable-history-transient-coordination`, File 01 §7.3). The durable substrate persists; the event stream coordinates and is not stored as the source of truth.
- Storage is non-destructive by default (`core.non-destructive-by-default`, File 01 §7.13). Edits create siblings, compaction changes view state, retention runs only under explicit user or selected-profile opt-in, and the user can inspect, account for, and reclaim storage at every granularity.
- Physical storage encoding and canonical hash encoding are different concerns (`core.canonical-encoding`, File 01 §6.15; `core.canonical-hash`, File 01 §7.14). The substrate may use row tuples, JSON blobs, binary columns, or any layout; every hash is computed over a declared `CanonicalEncoding`, never over storage bytes.
- Locality is structural. Syncable durable state and device-local durable state live in physically separate substrates, so that "never sync" — for the hash-chained audit overlay, for secrets, for per-device caches and rate-limit state — is a property of where data lives, not a filter that could be misconfigured.
- The schema is human-governed. Agents read and write data through the service layer; they never alter the storage schema. Schema evolution is forward-only numbered migration, guarded by a pre-migration backup.

Resolved tensions:

- "one libsql database with per-table sync exclusion" (`infrastructure/database.md`, `infrastructure/sync.md`) versus "a two-database split separating syncable from device-local state" (`unit12-infrastructure.md` D12.13): resolved toward the locality partition. The storage layer physically separates the syncable substrate from the device-local substrate so that never-sync is structural. This realizes File 15's locality metadata (`settings.locality-sync-export`, File 15 §18), File 17's per-device `RateLimitState`, and File 10's per-device hash-chained audit log, and it is consistent with `version.cross-device-sync-conflict-resolution` (File 11 §19.2), which already excludes rebuildable caches, rate-limit state, and audit overlays from version-graph sync. Cross-partition references are soft identity references, resolved with typed states rather than enforced foreign keys.
- "per-conversation external content store" (`file-management.md`: `<conversation>/external/<sha>/<sha>`) versus "one workspace-wide or global content-addressed blob store with a reference count" (`unit15` D12.9): resolved toward a single content-addressed blob store keyed by content hash, deduplicating across all conversations, workspaces, and versions. This maximizes deduplication, gives one garbage-collection path, and matches the content-addressed export bundle. The per-conversation path is superseded.
- "mark-and-sweep blob GC over the full version tree" (`file-management.md`) versus "reference-counted blob GC" (`unit15` D12.9): resolved toward reference counting as the primary mechanism, with a full-reachability reconciliation pass as a self-healing check against reference-count drift. Reference counting is O(1) per mutation; reconciliation is invoked by explicit request, startup or integrity suspicion, low-space policy, or selected maintenance profile, never as a hidden correctness clock.
- "forward-only migrations; to downgrade, restore from backup" (`infrastructure/database.md`) versus "every migration paired with a reversible down migration" (`unit15` D15.D.5): resolved toward forward-only migration as the canonical model, with a mandatory pre-migration backup as the rollback failsafe. Hand-authored down migrations are an optional fast-rollback optimization for simple, reversible schema changes; they are never the safety guarantee, because data-lossy or complex migrations cannot be truly reversed. The backup-and-restore path always works.
- "on corruption, create a fresh database" (`infrastructure/lifecycle.md`) versus the non-destructive invariant and the projection-rebuild principle: resolved toward a recovery hierarchy. A corrupt projection rebuilds from the substrate with no data loss (`core.projection`, File 01 §6.11); a corrupt durable substrate restores from the most recent consistent backup or, when sync is enabled, re-pulls from the replica; only when no recoverable copy exists is the corrupt substrate quarantined and a fresh substrate created, with the loss surfaced as a typed event. A silent fresh-start over recoverable data is rejected.
- "the storage spec freezes the database schema" versus "the spec governs the schema without dictating every column": resolved toward contract-level definition. This file fixes the substrate families, their source-of-truth-versus-projection classification, their locality, their durability invariants, and the migration discipline; the concrete column layout is the migration realization governed by §10, free to evolve under that discipline.

## 1. Chosen Model

Anchor: `storage.chosen-model`

### 1.1 Definition

ATLAS3 has one storage substrate. It is a substrate service (`core.substrate-services`, File 01 §2.4) expressed as a typed `StorageEngine` contract with three planes:

- the **durable substrate** — the append-only and immutable source-of-truth records (§3)
- the **content-addressed blob store** — large and binary payloads, addressed by content hash (§6)
- the **projection store** — rebuildable read-optimized views derived from the other two planes (§7)

The committed realization of the durable substrate and projection store is an embedded relational engine (`SQLite` / `libsql`, `core.stack-commitments`, File 01 §9); the committed realization of the blob store is a content-addressed file store on local disk. Both sit behind the `StorageEngine` contract.

### 1.2 Purpose

Every primitive Files 01–19 define must be persisted, reconstructed across restart, and reclaimed under user control. Each of those files declares a persistence contract — what is durable, what is computed, what is reconstructable — and delegates the physical realization here. This file is the single place where those contracts become a concrete, transactional, recoverable, accountable substrate, so that no later spec invents a parallel storage path.

### 1.3 Rule

- The storage substrate is the only durable store. No subsystem, surface, or plugin may introduce a private durable store, a private database file, a browser local-storage or session-storage store, or a per-surface configuration file used as a live source of truth. All durable state flows through the `StorageEngine` contract.
- The `StorageEngine` contract is the semantic boundary; the concrete engine is a replaceable implementation (`core.extension-integrity`, File 01 §7.10). A canonical rule may name the committed engine for grounding but must not depend on an engine-specific capability that the contract does not expose.
- The three planes are non-negotiable: source-of-truth records are durable, blobs are content-addressed, and everything else is a projection that is rebuildable from the first two.

### 1.4 Boundary

This file owns the substrate and its contract. What each substrate record means — a `Block`, a `LedgerEntry`, a `ContextVersion`, a `Lease`, a `SettingDefinition` value, a `WorldEntity` durable fact, a `MemoryEntry`, an `Observation` — is owned by that primitive's file. The substrate stores typed bytes under an identity and a schema version; it does not interpret them.

## 2. The Three Storage Planes

Anchor: `storage.three-planes`

### 2.1 Definition

The storage substrate is partitioned by role into three planes:

- **Durable substrate** — the authoritative record of every consequential fact: the append-only execution ledger (`ledger.entry-kind-catalogue`, File 10 §4.1), the immutable block pool and edge set (`block.what-is-durably-stored`, File 08 §13.1), the version graph's `ContextVersion` rows and diffs (`version.persistence-contract`, File 11 §18.1), entity records (`artifact.persistence-contract`, File 09 §18.1), leases and policy events (`policy.persistence`, File 06 §11.6), borrow grants (`surface.persistence-reconstruction`, File 07 §14.1), settings values (`settings.logical-persistence`, File 15 §17), the durable world-state log (`world.persistence-contract`, File 18 §14.1), memory entries (File 14), curated knowledge entries (File 12), per-call token-usage records (File 17), and durable registry declarations for registered capabilities, custom kinds, sensors, processors, and extensions.
- **Content-addressed blob store** — the immutable payloads too large or too binary to live on a substrate row: external block content, captured perception payloads (`perception.persistence`, File 19 §16.4), artifact externalizations, and any value above the inline threshold (§6).
- **Projection store** — the read-optimized views derived from the first two planes: the materialized context view (`context_view`), per-version derived state maps, retrieval indexes (File 12), the knowledge-graph projection, search indexes, the token-count cache, the cost projection, conversation-list metadata, and any other view declared rebuildable.

### 2.2 Purpose

The split is what makes the substrate both fast and safe. Reads hit projections and are O(1) for the dominant access patterns; truth lives in the durable substrate and the blob store, which are append-only or immutable and therefore cheap to back up, replicate, and reason about. Corruption or staleness of a projection is repaired by rebuild, never by data recovery.

### 2.3 Rule

- A record is **source-of-truth** if and only if its owning file's persistence contract declares it durably stored. Every other stored value is a **projection** and must be reconstructable from source-of-truth records plus blobs.
- A projection must never be the only place a durable fact exists. If a value cannot be recomputed from the durable substrate and the blob store, it is not a projection — it is source-of-truth and belongs in the durable substrate.
- The durable substrate is append-oriented and immutable per record: ledger entries, blocks, version nodes, and entity-version records are written once and never mutated in place. Observable change is a new record (a sibling block, a new version, a superseding entry), never an in-place edit of an existing source-of-truth row (`block.what-is-durably-stored`, File 08 §13.1; `core.non-destructive-by-default`, File 01 §7.13). The narrow exceptions are explicit, typed, and recorded: hard delete (§11), tombstoning (§11), the per-conversation mutable pointer-and-buffer record (`current_version_id`, `pending_ops`, per `version.persistence-contract`, File 11 §18.1), which is the single mutable head over the immutable version history; the schema-version control record (§10.1), whose stored schema version advances in place as migrations apply; and the class of source-of-truth records that carry in-place-mutable metadata, which mutate only through the revision-checked path of §3.4.
- Hashes stored for identity, integrity, deduplication, or cache validation are computed over a declared `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14), never over the physical row or blob bytes (§9).

### 2.4 Boundary

This section classifies what lives in which plane. The blob-store mechanics are §6; the projection mechanics are §7; the durable-substrate contract is §3. The classification of any specific record is fixed by its owning file's persistence contract, not re-decided here.

## 3. The Durable Substrate Contract

Anchor: `storage.durable-substrate`

### 3.1 Definition

The durable substrate is the set of source-of-truth record families the storage layer must persist, indexed by the file that owns each. A substrate family is a named group of records — a "table family" at the contract level — with a stable identity scheme, a per-record schema version, and a durability invariant inherited from its owning file.

### 3.2 Purpose

Each prior file enumerates its durable field set and delegates realization here. The substrate contract is the consolidated obligation: the storage layer must persist every field set each persistence contract names, preserve every identity and cross-reference, and reconstruct every computed view those contracts declare derived.

### 3.3 Required

The storage layer must durably persist at least the following source-of-truth families, each per its owning file's field set:

- the **execution ledger** — append-only `LedgerEntry` records with their structural fields, cross-reference map, per-kind payload, and `entry_schema_version` (`ledger.execution-ledger`, File 10 §3.5)
- the **block pool and edge set** — immutable `Block` records and committed `BlockEdge` records with their content variant, content hash, metadata, and `block_schema_version` (`block.what-is-durably-stored`, File 08 §13.1)
- the **version graph** — `ContextVersion` rows with parentage, merge sources, `op_summary`, compact `diff`, labels, bookmarks, snapshot references, `diff_hash`, `expected_view_hash`, and `version_schema_version`; the per-conversation mutable head (`current_version_id`, `pending_ops`) (`version.persistence-contract`, File 11 §18.1)
- **conversation, intent, and task** — `Conversation`, `IntentThread`, and `Task` records with their stable identity and durable lifecycle through a tombstoned, auditable end state (`intent.conversation`, File 02 §2; `intent.intent-thread`, File 02 §5; `intent.task`, File 02 §6)
- the **entity layer** — artifact entity records, artifact-version metadata, claim records, evidence-link edge metadata, validation and critique records (`artifact.persistence-contract`, File 09 §18.1)
- the **policy layer** — `Lease` records, approval-policy templates, scope-level overrides, and policy event records (`policy.persistence`, File 06 §11.6)
- the **surface layer** — durable `BorrowGrant` records (`surface.persistence-reconstruction`, File 07 §14.1)
- **settings** — explicit scoped values, profile contexts and layer order, definition source/version references, orphaned values, overlay enablement metadata, and redaction-safe audit metadata (`settings.logical-persistence`, File 15 §17)
- the **world model** — the durable-tier world-state-change log and registered custom entity, relation, and check extensions (`world.persistence-contract`, File 18 §14.1)
- **memory** — memory entries and their tier, scope, provenance, salience, validity, and retention metadata (File 14)
- the **knowledge base** — curated knowledge entries (File 12)
- **model selection** — durable `ModelSelectionRecord`s explaining each selection invocation (`model.model-selection-record`, File 16 §8)
- **provider accounting** — per-call `TokenUsageRecord`s with full `(provider_id, model_id, tokenizer_id)` keying and their cross-references, and the durable provider-pricing family: `ModelPricing` rows (provider-reported and `UserSupplied` overrides) and the immutable `PricingSnapshot` captured at call time (File 17; `provider.cost-as-derived-projection`, File 17 §19)
- the **registry** — registered capabilities and their state, source-instance metadata, registered custom kinds, hook declarations, sensor and processor declarations, capture-consent leases, and approved configuration (Files 05, 10, 19)

### 3.4 Rule

- Every source-of-truth record carries a `*_schema_version` stamp identifying the schema under which it was written, so that normalization-on-load (§10) can interpret records written by an earlier schema without rewriting them.
- A source-of-truth record whose owning contract permits in-place-mutable metadata carries a monotonic revision — a revision counter or an equivalent causal anchor — alongside its `*_schema_version` stamp, and is mutated only through a precondition-checked path: a revision compare-and-swap, or a typed per-field mutation capability, that fails with a typed staleness error rather than silently overwriting a concurrent change (`core.explicit-rejections`, File 01 §8). This is the single sanctioned in-place mutation of a source-of-truth record (§2.3); it never supersedes the append-only history immutable records preserve. It backstops the mutable-metadata records the owning files define — `MemoryEntry` (File 14 §3.2), `KnowledgeEntity` (File 12 §10.3), and `WorkspaceRecord` (File 24).
- Every record identity is globally unique, stable, and never reused, within a single per-install identity namespace (no per-surface identity namespaces). Identities are device-independent and survive sync (`core.canonical-encoding`, File 01 §6.15).
- A model-dependent scalar — a token count, a cache statistic, a cost — is never stored as an unkeyed value on any source-of-truth row. It is keyed by `(provider_id, model_id, tokenizer_id)` (File 17) or `(block_id, tokenizer_id)` (`block.what-is-computed`, File 08 §13.2), or it is a projection computed on demand (`core.explicit-rejections`, File 01 §8; `ledger.forgery-guards`, File 10 §3.7). The forgery guards Files 10 and 04 define are enforced at the substrate write boundary, not only in the executor.
- A cross-partition reference (a device-local record referencing a syncable record, per §8) is a soft identity reference, not an enforced foreign key. Resolution returns a typed state: `Present`, `NotFetched`, `PolicyHidden`, `DeviceLocalUnavailable`, `DeletedOrTombstoned`, or `DanglingCorrupt`. Absence is tolerated only when the typed state is expected by locality, sync, lifecycle, or policy; an unexpected dangling source-of-truth reference is an integrity finding.
- Raw `Secret`-classified material never enters the durable substrate. Only a `safe_description` and an opaque vault reference persist (`ledger.sensitivity-aware-persistence-retention`, File 10 §10; `secret.backend-boundary`, File 22 §4).

### 3.5 Boundary

This section fixes what must be durable and the invariants over it. The physical table layout, column types, and indexes that realize each family are the migration realization governed by §10. The owning file remains the authority on each family's field set; where this file and an owning file appear to disagree, the owning file's persistence contract governs the field set and this file governs the physical realization.

## 4. Storage Engine and the Connection Model

Anchor: `storage.engine-connection-model`

### 4.1 Definition

The `StorageEngine` is the typed contract through which all durable-substrate and projection access flows. Its committed realization is an embedded relational engine opened against the local substrate files, with a connection model of one exclusive writer and a bounded pool of concurrent readers under write-ahead logging.

### 4.2 Purpose

The embedded engine permits exactly one concurrent writer and many concurrent readers. The connection model matches that exactly so that reads never block writes and writes never block reads, which is what keeps the streaming UI responsive while the writer commits.

### 4.3 Rule

- All mutations pass through a single serialized writer. Concurrent writes are serialized, not lost; silent last-write-wins over concurrent mutations of shared state is rejected (`core.explicit-rejections`, File 01 §8). The writer lock is held for the duration of an engine call, not for the duration of a business transaction; a long read-modify-write sequence holds the write lock at the engine's transaction level (an immediate-mode transaction) and releases the in-process lock between calls so readers are not starved.
- Reads are served from a bounded pool of read connections under write-ahead logging, so readers and the writer proceed concurrently. Read connections are opened read-only.
- Write-ahead logging is enabled for the local substrate, with full synchronous durability as the default (the §5.1 floor: an acknowledged commit survives process and power failure; the durable-through-checkpoint `NORMAL`-equivalent level is available only through §5.1's typed, user-surfaced opt-in), foreign-key enforcement within a single partition, and a bounded busy-timeout. A write-ahead checkpoint policy bounds the size of the log. These engine parameters are settings-tunable within ranges the contract declares safe; they are not hardcoded constants where meaningful variation exists (`settings.settings-over-constants`, File 15 §13).
- A high-frequency producer of substrate writes may route through a serialized writer queue that coalesces redundant projection writes, hot-table refreshes, latest-state summaries, and idempotent derived updates. Source-of-truth appends may be batched into one transaction, but coalescing never removes, merges, rewrites, or hides their semantic facts. Ledger entries, version commits, audit-chain entries, policy facts, and user-visible mutation records remain individually reconstructable.
- Streaming output is write-throttled, not written token by token. Between flushes, the in-flight content accumulates in memory and the UI renders from that buffer; the substrate catches up on each flush, and a final flush writes the complete record at the producer's commit boundary (`block.commit-boundary-set`, File 08 §7.6). The throttle profile is a setting-owned responsiveness policy, not a correctness condition.

### 4.4 Boundary

This section owns concurrency and durability mechanics. The commit boundaries that decide *when* a version or block is committed are owned by Files 04, 08, and 11; this file owns *how* that commit is made durable and crash-safe. The replication of the syncable substrate to other devices is File 21's; this file owns only that the syncable substrate is a database the replica layer can replicate.

## 5. Transactional Guarantees

Anchor: `storage.transactional-guarantees`

### 5.1 Definition

A storage transaction is an atomic, durable unit of substrate mutation. The storage layer guarantees that a committed transaction is all-or-nothing, survives process and power failure once acknowledged, and is isolated from concurrent readers. The durability floor is full synchronous durability: an acknowledged commit survives process and power failure. A lower synchronous level (a `NORMAL`-equivalent that survives process crash but leaves a bounded power-loss window) is available only as a typed, user-surfaced opt-in that formally downgrades this guarantee; it is never the silent default (§4.3, §16).

### 5.2 Purpose

The durable substrate is the source of truth; partial or torn writes would corrupt it. Transactional guarantees are what let every other file treat a committed record as a fact it can replay, audit, and reconstruct from.

### 5.3 Rule

- A substrate mutation that spans more than one record — a version commit that writes a `ContextVersion` row, updates the materialized view, and clears the pending-operations buffer; a capability-call pipeline step that writes several ledger entries; a blob write that records external-content metadata — commits as one transaction. A commit boundary (`block.commit-boundary-set`, File 08 §7.6; `version.persistence-contract`, File 11) maps to exactly one storage transaction; either the whole boundary is durable or none of it is.
- Durability is acknowledged only after the write-ahead log has been made durable to the degree the synchronous setting declares. A producer that has received commit acknowledgment may rely on the record surviving restart.
- A semantic commit boundary commits its source-of-truth records exactly once. Projection updates may be included in the same transaction only when their failure cannot compromise the source-of-truth commit. If a projection update cannot complete, the commit records a projection invalidation or stale marker; readers rebuild, read degraded, or fail with typed `ProjectionStale` rather than treating stale projection bytes as authoritative.
- Writes follow a write-ahead discipline: the durable substrate is written before, or in the same transaction as, the projection it feeds, never after. A projection is never acknowledged as durable independently of its source.
- On crash mid-transaction, recovery rolls the write-ahead log forward to the last committed transaction and discards the incomplete one; no partially committed boundary is ever visible (§12, §13).

### 5.4 Boundary

This section owns atomicity and durability. Cross-device conflict resolution is not a storage-transaction concern — concurrent commits on two devices are legitimate divergence resolved by the version-tree-aware merge (`version.cross-device-sync-conflict-resolution`, File 11 §19), not by transaction isolation. This file guarantees local transactional integrity; File 11 owns multi-device convergence.

## 6. The Content-Addressed Blob Store

Anchor: `storage.blob-store`

### 6.1 Definition

The `BlobStore` is the content-addressed store for payloads that do not belong on a substrate row. A blob is addressed by the hash of its content; the substrate holds a typed reference (`BlobRef`: content hash, locator, size, media type) and the bytes live in the blob store. The blob store is a single store shared across all conversations, workspaces, and versions; identical content stored anywhere deduplicates to one blob.

### 6.2 Purpose

External block content, captured perception payloads, artifact externalizations, and large tool outputs are too large for substrate rows and often identical across conversations and versions. Content addressing gives natural deduplication, a stable locator that survives sync, and a blob layer that backs up and replicates independently of the relational substrate.

### 6.3 Rule

- A payload is stored inline on its substrate record when it is below the inline threshold and externalized to the blob store above it. The threshold is a setting, per-kind-overridable (`blocks.inline_size_threshold_bytes`, `block.settings`, File 08 §14.1; `files.inline_text_threshold`); it is not a hardcoded constant. A producer choosing externalization records a `BlobRef`, not the bytes, on the substrate.
- A blob's address is the hash of its content computed over the declared `CanonicalEncoding` for blob addressing (`core.canonical-hash`, File 01 §7.14). The same content yields the same address on every device; cross-device address equality is a deduplication optimization, never the correctness basis for sync (`core.canonical-hash`, File 01 §7.14).
- Blob writes are staged before substrate commit. Content is written to a staging location in the same filesystem boundary, verified against its content hash, made durable, then promoted to its content-addressed location; the promotion is made durable before the substrate commit. The substrate transaction then writes the `BlobRef`, reference metadata, and owning source-of-truth record together. If the substrate transaction aborts after staging, the staged blob is orphaned and startup reconciliation may delete it; if the substrate commits and the addressed bytes are missing or hash-invalid, that is blob corruption.
- Blob lifetime is reference-counted. Each substrate record that references a blob contributes a reference; removing the last reference makes the blob eligible for garbage collection. Reference counts are substrate metadata maintained transactionally with the referencing records; blob bytes are immutable content-addressed payloads outside the relational transaction.
- Reference counting is backstopped by a full-reachability reconciliation pass that walks all live references (across the entire version tree, not just the active view, per `artifact.materialized-paths-provenance`, File 09 §7.4) and corrects reference-count drift. Reconciliation runs by explicit user request, startup or integrity suspicion, low-free-space trigger, or selected maintenance profile. Garbage collection never runs during normal interactive mutation and is non-destructive of any blob still reachable from any version, including tombstoned versions (§11).
- Blob integrity is verified lazily through startup maintenance, explicit verification, and on-access checks according to settings. A blob whose content no longer matches its address is a corruption event (§12), surfaced and re-fetchable only when a valid recovery source exists, never silently served.
- Blob availability is typed. `LocalPresent` means the bytes are readable and hash-valid. `DeferredRemoteFetch` means a syncable record references a blob that has not been fetched locally yet and may resolve to its description placeholder (`block.block-description`, File 08 §10.5). `IntentionallyEvictedWithSource` means local bytes were removed only after recording a recovery source. `MissingCorrupt` means a committed local blob is missing or invalid without a valid recovery source and enters §12 recovery.
- Sync, export, backup selection, and reclaim operations enumerate blobs from allowed source-of-truth references, never by scanning every blob file. A physically shared blob is transported only when at least one included record references it and no locality, sensitivity, or policy restriction blocks it. Deleting one reference never deletes the blob while another included or excluded reference still owns it.

### 6.4 Boundary

This section owns the blob store: addressing, deduplication, staged atomic write, reference-counted GC with reconciliation, availability states, and integrity. The decision of which content externalizes (the inline-versus-external policy per kind) is set by the owning file's settings; this file enforces the threshold and stores the result. The workspace directory that materializes blobs as files for the user is File 24's mirror, not the blob store.

## 7. Projections and Rebuild

Anchor: `storage.projection-store`

### 7.1 Definition

A projection is a read-optimized derived view of source-of-truth records, realized as substrate tables, indexes, or in-memory structures, and registered with the storage layer together with its rebuild trigger. The projection store is the set of all registered projections; the rebuild orchestrator is the component that builds, verifies, and repairs them.

### 7.2 Purpose

Responsive reads and query workloads require derived views — the materialized context view for O(1) "what is in the current view," retrieval and search indexes, the knowledge-graph projection, derived state maps, the token-count cache, and the cost projection. Treating them as rebuildable projections rather than source-of-truth is what makes corruption a rebuild and what lets the substrate stay append-only.

### 7.3 Required

The canonical projection set includes at least:

- the **materialized context view** (`context_view`) — the active version's block set with position, lifecycle state, and pin state, rebuilt by walking the version action log (`version.persistence-contract`, File 11 §18.2; `block.what-is-computed`, File 08 §13.2)
- **per-version derived state maps** — `BlockLifecycle`, `PinState`, `ArtifactLifecycle`, `ReviewState`, `ValidationState`, `ClaimStatus`, `TaskRevision`, derived from the version action log (`version.persistence-contract`, File 11 §18.2; File 09)
- **retrieval and search indexes** — vector indexes, full-text indexes, and the knowledge-graph projection, all rebuildable from blocks, observations, and knowledge entries (File 12); embedding vectors are keyed by their embedding-model identity and recomputed, never treated as source-of-truth (`core.explicit-rejections`, File 01 §8)
- the **token-count cache** — keyed by `(block_id, tokenizer_id)`, an in-memory cache rebuilt on demand, never a stored unkeyed scalar (`block.what-is-computed`, File 08 §13.2; File 13)
- the **cost projection** — computed from `TokenUsageRecord`s and pricing snapshots on demand (File 17; `ledger.execution-ledger`, File 10 §3.5)
- the **provider model-capability cache** — a device-local projection over provider-reported catalog data, adapter fallback, user overrides, and approved profile data, with provenance from File 17; historical reconstruction uses recorded model-selection and provider-call records, not live cache refresh
- **runtime-handle projections** — active subscriptions, live sensor streams, processor workers, watcher handles, subprocess handles, and other process-local handles reconstructed from durable declarations and settings during lifecycle startup
- **run and run-loop state** — the live and historical state of runs and their steps — status, structure, step lifecycle, and outcome — projected from the execution ledger, never stored as an authoritative run-state row (`ledger.execution-ledger`, File 10 §3.5; `run.run`, File 04 §2)
- **aggregate, hot-table, and summary projections** — conversation-list metadata, usage rollups, debug and telemetry views, and any secondary index used only for query acceleration (`ledger.execution-ledger`, File 10 §3.5)
- resolved **world snapshots** and resolved **lease state** — computed by walking the durable world-state log and policy events, never stored as copied rows (`world.persistence-contract`, File 18 §14.2; `policy.persistence`, File 06 §11.6)

### 7.4 Rule

- Every projection declares its rebuild trigger — event-driven, on-demand, startup, integrity-failure, or explicit maintenance policy — and is registered with the rebuild orchestrator (`core.projection`, File 01 §6.11).
- A projection holds no durable fact. Dropping the entire projection store and rebuilding it from the durable substrate and the blob store must reproduce identical projections, modulo explicitly-typed gaps (such as `Ephemeral` world facts, `world.persistence-contract`, File 18 §14.2).
- A projection is integrity-checked where its owning file defines an integrity hash: the materialized view is verified against `expected_view_hash` (`version.expected-view-hash`, File 11) at the points File 11 specifies; on mismatch, the projection rebuilds from the action log and emits the integrity-violation event File 11 declares.
- The rebuild orchestrator detects a stale or corrupt projection — by integrity-hash mismatch, by a poisoned-state guard, or by an explicit invalidation — and rebuilds it without touching the substrate. A projection write that cannot be repaired is rebuilt, never escalated to data loss.
- A projection rebuild is idempotent and resumable: an interrupted rebuild leaves the projection marked incomplete and restarts cleanly, and a known-bad projection state (for example, a zero-row index reporting completion) is refused at write time and healed at startup rather than persisted.
- A conforming storage realization must prove projection rebuild equivalence: deleting the projection store and rebuilding from the durable substrate plus blobs reproduces the same projections modulo explicitly-typed gaps.

### 7.5 Boundary

This section owns projection registration, rebuild orchestration, and integrity repair. What each projection means and when its owning file requires it is owned by that file; the materialized view's content is File 11's and File 08's, the indexes' content is File 12's. This file guarantees they are rebuildable and rebuilt.

## 8. Physical Layout and the Locality Partition

Anchor: `storage.physical-layout-locality`

### 8.1 Definition

The storage substrate is physically partitioned by locality into two durable substrates plus the blob store and the device-local audit overlay, laid out under one user-writable root directory.

### 8.2 Purpose

File 15 tags every setting with a locality (`Syncable`, `WorkspaceLocal`, `DeviceLocal`, `NeverSync`, and related, `settings.locality-sync-export`, File 15 §18); File 17 requires `RateLimitState` to be per-device and excluded from sync; File 10 requires the hash-chained audit log to be per-device and to never sync. A per-table sync filter could be misconfigured and leak device-local or never-sync data. Physically separating the partitions makes "never sync" a structural property of where data lives.

### 8.3 Rule

- The durable substrate is split into a **syncable substrate** and a **device-local substrate**. Syncable source-of-truth families — blocks, version graph, ledger entries that sync, entity records, memory, knowledge, settings tagged syncable, durable world facts that sync — live in the syncable substrate, which is the database File 21 replicates. Device-local source-of-truth families — the hash-chained audit overlay's durable records, local-only settings, per-device consent or capture state where declared, `RateLimitState`, per-device system-watch and scheduled-task state, and anything tagged `DeviceLocal` or `NeverSync` as source-of-truth — live in the device-local substrate, which is never replicated. Device-local projections and caches also live there, but remain rebuildable.
- The hash-chained audit overlay (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.5) is stored device-locally as an append-only, hash-chained log, separate from the syncable substrate, and never syncs. Its chain integrity is per-device; a chain-tamper detection halts sync of the affected device (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.5).
- Cross-partition references are soft identity references (§3.4): a device-local record may reference a syncable record by identity without an enforced foreign key, and resolves it by lookup to a typed resolution state.
- The blob store is a single content-addressed store on local disk, shared across both substrates and all scopes (§6).
- The on-disk layout lives under one user-writable root, resolvable through a bootstrap environment variable and platform conventions (the user data directory on each platform). The root contains the substrate database files and their write-ahead sidecars, the blob store with content-hash fan-out that bounds directory cardinality, reference-count metadata, per-conversation and per-workspace materialization directories (owned by File 24, referenced here), the per-subsystem user-declaration directories the owning subsystems place here (File 24's `commands/`, File 25's `surfaces/`), the plugin install directory and the device-local integration-definition files (owned by File 35 and File 36, placed here), the secret-vault file (§14), the audit overlay, logs, the read-only configuration overlay, a single-instance lock, and a clearly-delimited cache directory that is safe to delete and rebuilds on demand. The installation directory is read-only to the running application; only the data root is user-writable. The root location is overridable by setting.
- A cache directory is explicitly disposable: deleting it loses no source-of-truth, because everything in it is a projection or a re-fetchable blob (§7, §11).

### 8.4 Boundary

This section owns the physical partition and on-disk layout. The replication of the syncable substrate, the merge of divergent version trees, and the import/export bundle format are File 21's. The workspace and worktree directories are File 24's; this file places the blob store and substrate files and references the materialization directories without owning them. The secret-vault file's internals are File 22's (§14).

## 9. Physical Storage Encoding versus Canonical Encoding

Anchor: `storage.physical-encoding`

### 9.1 Definition

The physical storage encoding is how a record's bytes are laid out on disk — row tuples, JSON or binary blob columns, or any serialization the engine uses. A `CanonicalEncoding` (`core.canonical-encoding`, File 01 §6.15) is a declared, storage-independent byte encoding used wherever a value must hash, deduplicate, sync, or reconstruct identically across devices and time. These are different concerns.

### 9.2 Purpose

Storage formats change for performance and engine reasons; canonical hashes must be stable across devices, processes, and time. Conflating them would make a storage-layout change silently break every hash, identity, and deduplication guarantee.

### 9.3 Rule

- The physical storage encoding is free to use any layout the engine supports — relational rows, JSON blobs for complex values, binary columns for compact payloads, columnar layouts for analytics projections. The storage layer may re-encode physically — for compaction, migration, or performance — without affecting any canonical hash.
- Every hash used for identity, integrity, deduplication, sync, replay, cache validation, or audit — `content_hash`, `diff_hash`, `expected_view_hash`, blob addresses, audit-chain hashes, snapshot and integrity hashes — is computed over the value's declared `CanonicalEncoding`, never over the physical row or blob bytes (`core.canonical-hash`, File 01 §7.14). No storage rule conflates the two.
- Two records that are physically encoded differently but canonically equal hash identically; two records physically identical but canonically distinct do not. The storage layer never infers a `CanonicalEncoding` from the physical representation.

### 9.4 Boundary

This section owns the separation rule. The specific `CanonicalEncoding` for each hashed value is defined by the file that defines that hash (File 08 for `content_hash`, File 11 for `diff_hash` and `expected_view_hash`, File 10 for audit-chain hashes); this file only requires that storage never substitutes its physical bytes for that encoding.

## 10. Schema Evolution and Migration

Anchor: `storage.schema-migration`

### 10.1 Definition

A migration is a forward-only, numbered transformation of the substrate schema, applied in order at startup and recorded in a schema-version control record. Settings carry their own typed migration kinds for stored values. Per-record schema-version stamps allow records written under an older schema to be normalized on load.

### 10.2 Purpose

The substrate families evolve as later specs add fields and families. Migration is how the durable substrate moves from one schema version to the next without losing data, and normalization-on-load is how records written under an older version remain readable.

### 10.3 Rule

- Schema changes are forward-only, numbered, and ordered. At startup, the layer reads the stored schema version, compares it to the current schema version, and applies each pending migration in order, each in its own transaction with automatic rollback on failure. On migration failure, the transaction rolls back, the previous substrate is preserved, and startup stops with a typed error rather than proceeding on a half-migrated substrate.
- Every migration that alters a populated substrate is preceded by a consistent backup of the affected substrate (§12), taken before the first pending migration runs. The backup is the canonical rollback failsafe: to downgrade or to recover from a bad migration, the layer restores the pre-migration backup. Hand-authored reverse migrations are an optional fast-rollback optimization for simple, reversible schema changes and are never the safety guarantee, because data-lossy or complex migrations cannot be truly reversed.
- Migration operates over released Atlas storage schema versions, starting from the product's initial schema. It does not require compatibility code for old draft schemas, source-material table shapes, or nonexistent pre-product user data. Importing external or legacy-format data is an explicit import capability, not hidden storage migration.
- Records carry a per-record schema-version stamp (§3.4). A record written under an older schema is normalized to the current shape on load — without rewriting the stored record — so that the running schema can read every record the substrate holds. A record in an interrupted or known-bad state discovered on load is reset to a safe state and re-derived, not trusted.
- Settings values evolve through typed settings-migration kinds — renaming a key, coercing a stored value, substituting a choice, dropping a key — recorded so each runs once; after settings migration, a validation pass checks every settings row against its current definition, leaving invalid rows in place to fall through to defaults and notifying the user (`settings.definition-evolution-stored-value-normalization`, File 15 §11).
- The storage schema is human-governed. Agents read and write data through the service layer; no agent, plugin, or runtime extension may add a column, add a table, or alter the schema. Extensions persist their data within the substrate families and extension mechanisms the canonical files provide (custom kinds, namespaced settings, registered extensions), never by mutating the schema (`core.extension-planes`, File 01 §6.14).
- Long-running migrations surface progress from known phases, processed units, or resumable boundaries. Elapsed-time guards may be used only as configurable responsiveness safety guards; they are not correctness conditions.

### 10.4 Boundary

This section owns the migration mechanism and the schema-version control record. What fields each family gains is owned by the file that adds them; this file owns that the addition is a forward-only migration with a pre-migration backup. The settings-migration kinds are realized here; their semantics are File 15's.

## 11. Retention, Garbage Collection, and Storage Accounting

Anchor: `storage.retention-gc-accounting`

### 11.1 Definition

Retention is the storage-side realization of the typed tombstone, compaction, and payload-deletion operations Files 08–11 define. Garbage collection reclaims unreferenced blobs and prunes projection data. Storage accounting measures consumed storage and exposes it for inspection and reclamation at every granularity.

### 11.2 Purpose

The system is non-destructive by default but not unbounded (`core.non-destructive-by-default`, File 01 §7.13). The user must be able to see what storage is consumed — by conversation, workspace, task, artifact, version tree, ledger, cache, and blob store — and reclaim it at every granularity, under explicit control, without time-based behavior deciding for them.

### 11.3 Rule

- Retention executes only the typed operations the owning files define: version tombstoning, reconstruction-preserving compaction of linear version ranges, and explicit version-payload hard deletion (`version.garbage-collection-pruning`, File 11 §20); block hard delete (`block.hard-delete`, File 08 §6.6); artifact-version tombstoning (`artifact.artifact-tombstones`, File 09 §8); and ledger sensitivity-aware retention with summary consolidation (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.4). The storage layer realizes these operations; it never invents a destructive operation of its own.
- No retention or pruning is time-based without explicit user or selected-profile opt-in (`core.non-destructive-by-default`, File 01 §7.13; `version.garbage-collection-pruning`, File 11 §20.6). The default retention keeps everything. Bookmarked and labeled versions are exempt from policy-driven pruning regardless of policy. Every retention invocation is itself a durable, recorded fact; no layer silently prunes `Sensitive` or safe-description `Secret` records without a recorded policy transition (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.4).
- Retention holds are source-of-truth references that make otherwise reclaimable substrate ineligible for pruning while the hold is active. Evaluation `RecordedRunFixture`s, regression baselines, and replayable suites may hold ledger scopes, blocks, snapshots, blobs, and version references needed for reproducible replay (File 40). Holds are visible in storage accounting and reclamation previews. Releasing a hold is an explicit policy or user action; if release makes an evaluation fixture unreplayable, File 40 records the typed dangling-reference diagnostic and the fixture is never scored against partial data.
- Garbage collection of the blob store is reference-counted with a reconciliation sweep (§6) and never removes a blob reachable from any version in the tree, including tombstones. Projection data is freely pruned and rebuilt; the cache directory is disposable (§8.3).
- The storage layer exposes a physical-file reclamation operation — a VACUUM-class compaction that returns to the filesystem the free pages left by tombstoning, hard deletion, and blob garbage collection — through the `StorageEngine` contract, invoked by explicit user request, low-free-space policy, or selected maintenance profile, never on a hidden clock. It reclaims physical space only: it changes no source-of-truth fact and rebuilds any projection it disturbs (§7).
- Storage accounting tracks consumed storage as structured data, broken down by category — conversations, blocks, version trees, ledger, entity records, memory, knowledge, indexes and projections, blob store, caches, logs, per-workspace, per-task, per-run, per-artifact. The user can inspect, manage, constrain, and reclaim storage at every meaningful granularity through exposed capabilities and data contracts: full reset, per-category cleanup, per-workspace, per-conversation, per-task, per-run, per-artifact, and any later substrate family that owns storage. UI layout is outside this file; the backend accounting and management surface are not. Quotas, retention policies, and expiry rules are settings, not hardcoded limits.
- A destructive reclamation operation supports a dry run that reports what would be removed and what reconstruction would be lost, before anything is removed. A reclamation that crosses a reconstruction boundary (hard-deleting a version payload with descendants, hard-deleting a referenced block) requires the typed confirmation its owning file mandates and records the resulting provenance gap (`version.garbage-collection-pruning`, File 11 §20; `block.hard-delete`, File 08 §6.6).
- Run-scoped blocks accumulate durably — run termination deletes nothing (`block.block-scope`, File 08 §11.1) — so per-run accounting and reclamation are real, named, reachable operations: an explicit bulk reclaim-this-run's-blocks operation enumerates a run's blocks, runs the dry run above with a reference and retention-hold impact preview, and presents its candidates through the File 06 §5 approval flows (batched approval where eligible; an item requiring the File 08 §6.6 typed confirmation presents alone per `policy.batched-approval-flow`). The default remains keep-all; a selected profile may recommend or preselect candidates, but nothing converts block hard deletion into an automatic operation.

### 11.4 Boundary

This section owns the storage-side realization of retention, the blob and projection GC, and storage accounting. The semantics of each typed operation — what a tombstone preserves, what compaction must keep reconstructable — are owned by Files 08–11. This file executes them and measures the result. Cross-device propagation of a deletion is File 21's.

## 12. Backup, Integrity, and Recovery

Anchor: `storage.backup-integrity-recovery`

### 12.1 Definition

A backup is a consistent point-in-time copy of a substrate, taken without pausing the writer. Integrity detection finds corruption in the substrate, a projection, or a blob. Recovery is the ordered hierarchy by which the layer returns to a consistent state.

### 12.2 Purpose

The durable substrate is the source of truth; it must be backed up consistently, checked for corruption, and recovered without silent data loss. The recovery hierarchy is what turns the source material's "on corruption, start fresh" into a non-destructive, projection-aware repair.

### 12.3 Rule

- A backup is an engine-consistent online snapshot of the requested substrate scope, taken through the `StorageEngine` contract without pausing the writer. The committed SQLite/libsql realization uses its consistent backup mechanism, but write-ahead logging is not the semantic requirement. Backups may cover the syncable substrate, device-local substrate, both substrates, or an export bundle. The vault is excluded unless the user explicitly invokes vault backup. Backups are produced before every migration that can alter a populated substrate (§10) and on user request.
- A backup that captures substrate records also captures the blobs those records reference: it enumerates the referenced blobs into a backup manifest, which acts as a garbage-collection retention hold (§11.3) keeping those blobs reclamation-ineligible for the backup's lifetime, and it coordinates the blob-store capture with the substrate snapshot so the pair is point-in-time consistent. A restore whose substrate references a blob the backup did not carry surfaces the gap as a typed `RestoreInducedAbsence` through blob reconciliation (§6.3), never as silent corruption.
- Integrity is detected at three layers: a substrate integrity check at startup; projection integrity hashes where the owning file defines them (§7.4); and blob verification through startup maintenance, explicit verification, and on-access checks (§6.3). A settings-driven error policy over typed engine errors closes the substrate and forces recovery when needed; corruption-class errors escalate immediately. A generation counter prevents a stale handle from corrupting a freshly reopened substrate.
- Recovery follows a strict hierarchy, most-recoverable first:
  1. **Projection corruption** rebuilds from the durable substrate and blobs, with no data loss (`core.projection`, File 01 §6.11). Device-local projections and caches rebuild the same way.
  2. **Durable-substrate corruption** restores from the most recent consistent backup; when sync is enabled, the syncable substrate may instead re-pull from the replica, which holds the synced source-of-truth. Device-local source-of-truth restores from local backup or quarantine paths and is never recreated from cross-device sync.
  3. **Only when no recoverable copy exists** is the corrupt substrate quarantined under a timestamped name and a fresh substrate created — the last-resort failsafe, never the first response. The loss is surfaced as a high-severity typed event, never silent.
- A silent fresh-start over recoverable data is rejected. A corruption event is always typed, surfaced, and recorded; the user is never told all is well when data was lost.
- Successful startup after an update records a last-known-good marker; a startup that fails its self-checks (substrate schema integrity, settings loadable, core services startable, required extensions loadable) triggers rollback to the last-known-good state, including restoring the pre-migration backup.
- A conforming realization must prove restart and recovery equivalence: after clean shutdown, crash, interrupted rebuild, projection corruption, and substrate restore, the next run sees the same materialized durable state or an explicit typed recovery gap.

### 12.4 Boundary

This section owns backup, integrity, and local recovery. Cross-device restore and the portable export bundle are File 21's. The cryptographic verification of the audit chain is File 10's; this file stores the chain and surfaces its tamper events.

## 13. Lifecycle, Startup, and Deterministic Reconstruction

Anchor: `storage.lifecycle-reconstruction`

### 13.1 Definition

The storage lifecycle is the ordered sequence of startup phases that bring the substrate to a consistent, usable state, the shutdown sequence that flushes it, and the deterministic reconstruction guarantee that the state a new run sees after restart equals the state it would have seen before, modulo recorded offline changes.

### 13.2 Purpose

Every persistence contract requires deterministic reconstruction across restart, retry, edit, reroute, branch, and child-run (`block.reconstruction-across-restart`, File 08 §13.3; `version.persistence-contract`, File 11 §18.3; `surface.reconstruction-across-restart`, File 07 §14.2; `artifact.persistence-contract`, File 09 §18.3; `world.persistence-contract`, File 18 §14.3; `perception.persistence`, File 19 §16.3). The lifecycle is where those reconstructions are realized in one ordered sequence.

### 13.3 Rule

- Startup proceeds in order: acquire the single-instance lock; open and integrity-check the substrate (§12); run pending migrations after taking the pre-migration backup (§10); warm hot caches; rebuild and verify projections (§7); recover interrupted runs and reconcile orphans; clean up stale leases; then start services. A new run after startup sees the same materialized view, tool surface, world snapshot, and registry state a new run would have seen before restart, modulo changes recorded during the offline interval.
- A single-instance lock prevents two processes from opening the same substrate for writing; a stale lock from a crashed process is detected and reclaimed. Substrate-lock contention is retried with bounded backoff before failing with a typed error.
- Run, lease, and in-flight reconstruction follows the owning files: an interrupted run follows the orphan-run rules (`run.cancellation`, File 04 §17.3); the durable pending-operations buffer survives restart and is discarded with a typed event if inconsistent with the substrate (`version.persistence-contract`, File 11 §18.3); stale leases are revalidated or cleaned (`policy.persistence`, File 06 §11.6); staged partials from an orphaned run are promoted to partial-orphan blocks during restart recovery only where the producing capability declared `partial_output_meaningful` AND provided a recovery handler (`block.reconstruction-across-restart`, File 08 §13.3); already-committed blocks, partial orphans included, survive restart unconditionally (`block.what-is-durably-stored`, File 08 §13.1).
- Snapshot resolution is realized as a deterministic walk over the relevant durable log to the addressed anchor, with an optional baseline-or-checkpoint optimization that bounds the walk length; snapshots are addressing identities resolved over the durable log, never stored as copied rows (`version.snapshots`, File 11 §14; `world.persistence-contract`, File 18 §14.4, §17). Replay and historical reconstruction consume recorded snapshots and immutable references; they re-derive nothing from live mutable sources (`context.assembly-replay-snapshot`; `ledger.replay-semantics`, File 10 §11; `provider.token-source`, File 17).
- Shutdown flushes before exit: set a shutting-down flag, stop accepting new writes, request cooperative drain for in-flight storage work, commit or roll back pending transactions at safe boundaries, flush buffered events to the durable substrate, checkpoint the write-ahead log, close the substrate, and release the lock. If shutdown must force termination, eligible processes are cancelled or killed through File 04's killability contract; every acknowledged commit remains durable and staged partials are discarded, orphaned for reconciliation, or surfaced with typed recovery state.

### 13.4 Boundary

This section owns the storage lifecycle and reconstruction realization. The semantics of a recovered run, a revalidated lease, or a resolved snapshot are owned by Files 04, 06, 11, and 18; this file owns the ordered sequence and the determinism guarantee. The broader application lifecycle beyond storage — provider warmers, UI initialization — is File 42's; this file owns the storage phases within it.

## 14. The Secret-Vault and Audit-Overlay Storage Boundaries

Anchor: `storage.secret-vault-boundary`

### 14.1 Definition

The secret vault is a dedicated store for credentials, separate from the durable substrate and the settings store. The audit overlay is the device-local hash-chained log. Both have storage boundaries this file fixes and internals later files own.

### 14.2 Purpose

Credentials must never enter the durable substrate, sync, exports, logs, or agent context; the audit chain must be tamper-evident and per-device. This file owns where these stores live and the rule that secret material stays out of the substrate; the cryptography and chain verification belong to the Security and Ledger files.

### 14.3 Rule

- The secret vault is stored outside the durable substrate, backed by the operating-system keyring where available and by an encrypted vault file where not. The vault file's location is a storage fact (under the data root, overridable by bootstrap environment variable); its encryption, key derivation, and keyring integration are File 22's. The durable substrate holds only opaque vault references and `safe_description`s, never raw secret material (`secret.backend-boundary`, File 22 §4; `ledger.sensitivity-aware-persistence-retention`, File 10 §10).
- Secrets are excluded from backups, exports, sync, logs, events, snapshots, and agent context. A backup of the substrate does not back up the vault; vault backup is the user's explicit, separate action (`settings.locality-sync-export`, File 15 §18).
- The hash-chained audit overlay is stored device-locally (§8.3), append-only, never synced, and never disabled even when telemetry or logging is disabled (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.5). This file stores the chain and surfaces its tamper-detection events; the chain construction and verification are File 10's.
- Encryption-at-rest of the durable substrate, where enabled, is a storage-configuration boundary: this file declares that the substrate may be opened against an encrypted engine and that the encryption keying is File 22's; it defines no cryptography here.

### 14.4 Boundary

This file owns the existence, location, and substrate-exclusion boundary of the vault and the storage of the audit overlay. The Security spec owns vault cryptography, key management, and trust state; the Ledger file owns audit-chain construction and verification.

## 15. Storage Capability Surface and Events

Anchor: `storage.capability-surface`

### 15.1 Definition

The storage layer exposes canonical capabilities for storage inspection and management and emits typed storage events through the same canonical mechanisms every other substrate uses (`capability.registered-capability`, File 05 §10; `ledger.event-stream`, File 10 §5).

### 15.2 Rule

- Storage-management operations are canonical capabilities, declared like any other (File 05), tier-gated by policy (File 06), and surfaced uniformly (File 07): inspecting storage accounting, running a backup, restoring from a backup, running blob or projection garbage collection with dry-run, rebuilding a projection, applying a retention policy, setting quotas or limits, and reclaiming storage at a named granularity. Destructive or large-scope operations expose preview plans where meaningful, support cancellation or killability per File 04, and carry the typed-confirmation their owning files require.
- Storage emits through File 10's canonical bus, ledger envelope, sensitivity, retention, and custom-extension mechanisms. Cross-cutting facts already defined by File 10 use canonical kinds. Storage-specific facts — migration applied, migration progress, backup created, restore performed, corruption detected, projection rebuilt, projection integrity violated, blob garbage collected, blob verification failed, retention policy applied, storage reclaimed, and substrate-lock contention — are registered as `Custom { namespace: "storage", name, payload }` unless File 10 later promotes one to the closed catalogue. Consequential storage events declare retention class, sensitivity, cross-reference keys, and ledger participation at registration.
- The storage layer never exposes a raw query or schema-mutation capability to the agent. Data is reached through the owning subsystems' services; the schema is human-governed (§10.3).

### 15.3 Boundary

This section names the capability and event contracts. Their declaration field set is File 05's, their policy gating is File 06's, their surface composition is File 07's, and their envelope, ledger schema, and custom-event registration are File 10's. This file declares storage capabilities as canonical built-ins and emits storage events through that shared mechanism.

## 16. Settings

Anchor: `storage.settings`

### 16.1 Rule

Every storage mechanism with meaningful variation is configurable through the canonical settings system (`core.settings-system`, File 01 §6.8; File 15); this file names the dimensions, the settings system owns the cascade and storage. Settings use namespaced keys (`storage.*`) and declare scope, agent exposure, and locality per File 15.

Dimensions include: the data-root location and the substrate file locations (bootstrap-resolved, §8.3); the reader-pool size, busy-timeout, write-ahead checkpoint policy, and synchronous durability level (within contract-declared safe ranges, §4.3); the streaming write-throttle profile (§4.3); the inline-versus-external threshold per kind (§6.3); blob garbage-collection maintenance policy, low-free-space trigger, and verification policy (§6.3); projection rebuild and integrity-check strictness (§7.4); retention policies, quotas, and limits per category and scope, with the keep-everything default (§11.3); backup policy and retention (§12.3); and the cache directory's disposability and size bounds (§8.3).

Specific defaults belong to tested settings profiles, not to hardcoded constants in this layer (`settings.settings-over-constants`, File 15 §13). No storage behavior is a hidden hardcoded branch where a meaningful behavioral variation exists.

## 17. Explicit Rejections

Anchor: `storage.explicit-rejections`

The following shapes are wrong for this layer:

- a private durable store, database file, browser local-storage or session-storage store, or per-surface configuration file used as a live source of truth — there is one storage substrate behind one contract (§1.3; `settings.explicit-rejections`, File 15 §20)
- a projection treated as source-of-truth, or a durable fact that exists only in a projection — projections are rebuildable, never authoritative (§2.3, §7.4)
- in-place mutation of a source-of-truth record — blocks, ledger entries, version nodes, and entity-version records are append-only and immutable; observable change is a new record, with hard delete and tombstoning the only typed destructive exceptions (§2.3; `block.explicit-rejections`, File 08 §15)
- conflating physical storage encoding with the `CanonicalEncoding` used for hashing, or computing any hash over physical row or blob bytes (§9; `core.canonical-hash`, File 01 §7.14)
- storing a model-dependent scalar — token count, cache statistic, cost — as an unkeyed value on a source-of-truth row (§3.4; `core.explicit-rejections`, File 01 §8)
- silent last-write-wins over concurrent mutations of shared state (§4.3; `core.explicit-rejections`, File 01 §8)
- storing world snapshots, registry snapshots, or any snapshot as copied rows rather than resolving them as identities over a durable log (§13.3; `world.explicit-rejections`, File 18 §16; `version.snapshots`, File 11 §14)
- raw `Secret` material in the durable substrate, backups, exports, sync, logs, events, or agent context — only opaque references and safe descriptions persist (§3.4, §14.3; `secret.backend-boundary`, File 22 §4)
- syncing the hash-chained audit overlay, the per-device rate-limit state, or rebuildable caches — device-local data is physically isolated, not filtered (§8.3; `ledger.sensitivity-aware-persistence-retention`, File 10 §10.5)
- time-based retention or pruning without explicit user or selected-profile opt-in, or any time-based behavior driving storage correctness (§11.3; `core.non-destructive-by-default`, File 01 §7.13)
- maintenance schedules, elapsed-time guards, or polling treated as storage correctness mechanisms rather than settings-controlled, killable safety or convenience policies (§6.3, §7.4, §10.3, §13.3)
- a silent fresh-start over recoverable data on corruption — recovery is projection-rebuild, then substrate-restore, then quarantine-and-surface, never silent loss (§12.3)
- backward-data-lossy migration treated as safely reversible, or schema downgrade without a pre-migration backup (§10.3)
- migration/adaptation code for old draft schemas, source-material table shapes, or nonexistent pre-product user data (§10.3)
- agent or plugin alteration of the storage schema — the schema is human-governed; extensions use the canonical extension mechanisms, not schema mutation (§10.3; `core.extension-planes`, File 01 §6.14)
- a per-surface or per-conversation external content store, or a non-content-addressed blob store — there is one content-addressed blob store deduplicating across all scopes (§6; supersedes the per-conversation path)
- mark-and-sweep as the only blob-GC mechanism without reference counting, or reference counting without explicit reconciliation support — both are required (§6.3)
- exposing a raw query or schema-mutation capability to the agent (§15.2)

## 18. Consequences for Later Specs

Anchor: `storage.consequences`

Later specs must follow these rules:

- File 21 replicates the syncable substrate this file partitions, never the device-local substrate or the audit overlay; it ships content-addressed blobs separately with deferred fetch; it realizes the version-tree-aware merge (`version.cross-device-sync-conflict-resolution`, File 11 §19) over the substrate this file lays out; and it defines the portable export bundle over the content-addressed blobs and durable records this file stores. It introduces no parallel durability path.
- File 22 owns the secret-vault cryptography, key derivation, keyring integration, encryption-at-rest keying, and trust state; this file gives it the vault file's location and the substrate-exclusion boundary. Raw secrets never enter the substrate this file owns.
- File 24 owns the workspace and worktree directories and the disk-to-block materialization mirror; it resolves external content from the content-addressed blob store this file owns and references the materialization directories this file places, without introducing a second blob store.
- The **per-surface specs** (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) persist their durable state as substrate families and content-addressed blobs through this contract — never a private store — and tag each family's locality so the partition (§8) places it correctly. Per-surface caches are projections, rebuildable and disposable.
- The **Automation, Triggers, and Scheduling** spec persists schedules, watches, and trigger state through this contract, tags machine-bound state device-local (§8.3), and drives nothing from storage-layer clocks; retention of automation history is a recorded, opt-in policy (§11.3).
- The **Telemetry, Logging, and Observability** spec consumes the ledger and storage events this file emits and builds its views as rebuildable projections; it never makes a telemetry view a source of truth.
- The **Runtime Infrastructure and Lifecycle** spec owns the broader application lifecycle around the storage startup and shutdown phases this file defines; it invokes the storage lifecycle, it does not reimplement it.
- The **Evaluation and Benchmarking** spec reads the durable substrate and replays over the recorded snapshots this file reconstructs; it re-derives nothing from live mutable sources.
- Every later spec that produces durable state declares its substrate family, its source-of-truth-versus-projection classification, and its locality, and obeys the canonical-hash, no-unkeyed-scalar, immutable-source-of-truth, and human-governed-schema rules this file fixes.

## 19. Canonical Rule Anchors

Anchor: `storage.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `storage.chosen-model`, `storage.three-planes`, `storage.durable-substrate`, `storage.engine-connection-model`, `storage.transactional-guarantees`, `storage.blob-store`, `storage.projection-store`, `storage.physical-layout-locality`, `storage.physical-encoding`, `storage.schema-migration`, `storage.retention-gc-accounting`, `storage.backup-integrity-recovery`, `storage.lifecycle-reconstruction`, `storage.secret-vault-boundary`, `storage.capability-surface`, `storage.settings`, and `storage.consequences`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
