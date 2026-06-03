# Sync, Import, Export, and Data Portability

## Status

Canonical. This file defines how a user's data moves: across the user's own devices, out of the system, into the system, and into recovery media. It realizes the cross-device and portability contracts Files 09, 10, 11, 14, 15, and 20 declare and delegate to this layer. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `SyncTransport` typed contract: a replaceable transport that replicates the syncable durable substrate File 20 partitions, with the committed realization being libsql embedded replicas against a user-controlled primary
- the local-first invariant: every write lands in local storage before sync, reads never wait for the network, and sync is opt-in
- what replicates and what does not: the realization of File 20's syncable-versus-device-local partition, File 15's per-setting locality, and File 10's per-entry sensitivity
- conflict resolution: delivery of File 11's version-tree-aware merge, additive sync, causal settings conflicts, and non-destructive recovery from bad sync checkpoints
- external-content replication: transport of content-addressed blobs separately from relational records with deferred fetch and hash verification
- device identity and pairing: the split between device-local private identity and syncable public pairing records
- cross-installation identity and provenance: UUID stability, content-addressed deduplication, import producers, and cross-installation provenance maps
- the `PortablePackage`: the canonical lossless package envelope for `SharePackage` and `RecoveryArchive`
- the import pipeline: validation, normalization, dependency closure, import staging, UUID-preserving remap, deduplication, sensitivity classification, source approval, collision handling, proposal-or-commit per substrate, and atomic visibility
- the movement application of egress governance: policy-gated movement of data, no raw secret egress at the movement boundary, and typed omissions/redactions
- backup, restore, and archival: full-substrate backup, portable recovery archive, and vault backup boundaries
- the sync/import/export capability surface, event vocabulary, settings dimensions, explicit rejections, and consequences later specs consume

This file does not define:

- the storage substrate, the physical syncable-versus-device-local partition, the on-disk layout, the content-addressed blob store, or the projection store - File 20 owns those
- the semantics of the version-tree-aware merge - File 11 owns "both branches survive, no last-write-wins"; this file transports the records that make those branches visible on each device
- the secret-vault internals, cryptography, key derivation, OS-keyring integration, or device trust state - File 22 owns those
- the egress policy semantics - the sensitivity-tier rules, the egress-destination inspector, the secret-egress exceptions, and the redaction-before-egress policy - File 22 owns those; this file applies them at the movement boundary
- workspace identity, materialized workspace directories, worktrees, and disk-to-block mirrors - File 24 owns those
- settings resolution or locality semantics - File 15 owns them; this file consumes their resolved locality and sensitivity metadata
- per-entity export capability declarations - File 09 declares artifact export, File 14 declares memory import/export, and per-surface specs declare their format exports
- lossy presentation-format exports such as Markdown, PDF, PPTX, Anki, Jupyter, and slide decks - those are surface-owned format capabilities that pass through this file's egress governance but do not use the `PortablePackage` envelope
- application installers, auto-update, release channels, sidecar binaries, executable plugin distribution, or connector runtime installation - data portability is not application distribution
- ledger row format, event envelope, sync entry-kind catalogue, or live-bus delivery - File 10 owns those
- UI rendering of sync-status panels, export wizards, import review surfaces, or conflict-resolution views

## Source Resolution

This file resolves cross-device sync, multi-device replication, conflict reconciliation, import, export, package format, backup/restore, blob transport, device pairing, and cross-installation identity into one boundary: the layer that moves user-owned data without re-owning any substrate's semantics.

Resolved design:

- ATLAS3 is local-first. Every write hits local storage first; reads never wait for the network; sync is opt-in; loss of the primary degrades to single-device operation with no lost write and no blocked read.
- Sync replicates the syncable durable substrate File 20 partitions and ships content-addressed blobs separately. It never replicates the device-local substrate, hash-chained audit overlay, per-device rate-limit state, TOML overlay, secret vault, projections, indexes, or rebuildable caches.
- Conflict is represented in the source-of-truth model, not solved by the transport. Version divergence becomes sibling branches per File 11. Settings conflicts use causal revision metadata. No timestamp or row-level last-write-wins rule is a conflict resolver.
- Export uses one canonical lossless envelope, `PortablePackage`, with two profiles: `SharePackage` and `RecoveryArchive`. Lossy presentation exports are governed egress capabilities outside that envelope.
- Import is staged, validated, source-approved, dependency-aware, sensitivity-aware, collision-classified, and atomically made visible. A failed import leaves no visible imported records and no authoritative blob references.
- Identities are portable. Durable record identities are UUIDs preserved across sync and import. Content hashes deduplicate blobs. Foreign provenance is recorded through import producers, source provenance records, and cross-installation maps.
- Export, sharing, publishing, sync to a primary, clipboard copy, and external format production are data egress. Raw `Secret` material never egresses; `Sensitive` movement is explicit and audited.

Resolved tensions:

- Whole-database sync with exclusion filters versus structural locality partition: resolved toward File 20's partition. The transport replicates the syncable substrate and never opens a replica against the device-local substrate.
- Per-conversation external-content paths versus one global content-addressed blob store: resolved toward File 20's global store. Blob replication enumerates referenced blobs from source-of-truth records and fetches by content hash.
- CRDT/operation-replay designs versus durable-state replication: resolved toward state replication over immutable records, version graph branches, and content-addressed blobs. Actions are not replayed across devices.
- Row-level transport reconciliation versus user-visible semantic conflict: resolved by substrate shape. Durable source-of-truth rows are immutable and append-only; genuinely mutable replicated settings use causal conflict detection.
- UUID remap on import versus UUID preservation: resolved toward preservation. Same-id/different-content collisions are typed safety events; they never silently overwrite.
- Fixed polling as correctness versus event-driven/local-first correctness: resolved by making cadence a configurable latency policy only. Correctness comes from local durability, checkpoints, hashes, and eventual convergence.

## 1. Chosen Model

Anchor: `portability.chosen-model`

### 1.1 Definition

ATLAS3 has one portability layer. It is a substrate service with four cohesive responsibilities over the storage substrate File 20 owns:

- **Sync**: optional replication of the syncable durable substrate across the user's devices through a replaceable `SyncTransport` contract
- **Conflict resolution delivery**: transport of the records that make File 11's version-tree divergence and per-device materialized-view pointer work across devices
- **Export**: production of the lossless `PortablePackage` envelope and governed egress through surface-owned format exporters
- **Import**: the validated, deduplicating, staged, atomic pipeline that brings a `PortablePackage`, another installation's data, or a foreign format handled by a registered import capability into the substrate

Cross-cutting all four: blob transport, device identity and pairing, cross-installation identity and provenance, backup/restore/archival, sensitivity policy, and source approval.

### 1.2 Purpose

The user owns their data. It must move with them across their devices, leave the system in a portable form, return without silent loss, and survive corruption of the live substrate. Files 09, 10, 11, 14, 15, and 20 each declare what is durable and delegate movement here. This file is the single place where that movement becomes concrete, so later specs do not invent parallel sync paths, private export formats, or private import pipelines.

### 1.3 Rule

- The portability layer moves only what the owning substrates declare durable and only as those substrates' contracts permit. It transports records; it does not redefine what those records mean.
- There is one sync transport contract, one canonical package envelope, and one import pipeline. No subsystem, surface, plugin, or connector may introduce a private replication mechanism, private cross-device store, private package format, or private import path.
- Sync is opt-in and local-first. Export, sharing, publishing, clipboard copy, and external format production are egress governed by policy. Import is validated, staged, deduplicating, and atomic. None may bypass File 06 policy, File 10 sensitivity, File 15 locality, File 20 storage boundaries, or the secret boundary.
- Replication and lossless packages transport source-of-truth records and content-addressed blobs only. Projections, indexes, and rebuildable caches are rebuilt on the receiving device.

### 1.4 Boundary

This file owns movement of data. File 20 owns the substrate the data lives in. File 11 owns version merge semantics. Files 08, 09, 10, 12, 14, 15, 17, 18, and 19 own what their records mean. File 22 owns encryption and trust internals; this file owns the boundary at which encryption attaches and the rule that raw secrets never move.

## 2. Boundaries with Adjacent Layers

Anchor: `portability.boundaries-with-adjacent-layers`

### 2.1 With File 01

`core.projection` means this file never moves projections as authoritative data. `core.canonical-encoding` and `core.canonical-hash` mean package hashes are computed over declared canonical encodings, never physical storage bytes. `core.non-destructive-by-default` means sync and import are additive unless a user explicitly accepts a destructive operation.

### 2.2 With File 06

Sync enablement, egress, source approval, import of foreign records, sensitive export, sharing, publishing, restore-over-live-data, and plugin/extension source approval are governed capabilities. This file declares where those gates apply; File 06 owns policy, leases, typed confirmation, and approval records.

### 2.3 With File 09

Artifacts and evidence are portable records when their locality and sensitivity permit. This file moves their records and blobs. File 09 owns artifact identity, versions, evidence, provenance, materialization, and per-artifact export capabilities.

### 2.4 With File 10

File 10 owns ledger entries, events, event envelopes, sensitivity-aware retention, and audit overlay. This file emits and records portability facts through those mechanisms. Imported source provenance may be carried as data, but foreign runtime history is not local execution history.

### 2.5 With File 11

File 11 owns version graph semantics: sibling divergence, no silent merge, no last-write-wins, per-device current pointer, and version commits. This file transports version records and makes divergence visible on every device.

### 2.6 With File 15

File 15 owns setting definitions, scope resolution, locality, profile layers, TOML overlay, and secret-reference boundaries. This file moves only settings values whose resolved locality and sensitivity permit movement.

### 2.7 With File 20

File 20 owns the physical storage planes, locality partition, blob store, projection store, transaction boundaries, backup primitives, orphan reconciliation, and storage encoding. This file consumes those contracts and introduces no parallel durable store.

### 2.8 With File 22 (Security), File 24 (Workspaces), Files 35 and 36 (Extension/Plugin, MCP), and File 43 (Packaging)

Security owns encryption, keys, device trust, vault backup internals, and credential handling. Workspaces own materialized workspace identity and file mirrors. Packaging owns application distribution and executable plugin/runtime installation. File 35 (Extension and Plugin System) and File 36 (MCP and External Integrations) own install/enable/update mechanics for executable integrations. This file may move registry metadata and inert dependency declarations; it does not install or execute code.

## 3. The Sync Transport Contract

Anchor: `portability.sync-transport`

### 3.1 Definition

`SyncTransport` is the typed contract through which the syncable durable substrate replicates across the user's devices. Its committed realization is libsql embedded replicas: each device runs against a local substrate file that optionally replicates with a user-controlled primary. The transport sits behind the contract; it is replaceable and is not the semantic boundary.

`SyncDestinationProfile` is the resolved settings object that binds a device to a sync target. It contains the transport kind/config reference, primary identity or fingerprint, credential reference, enabled scopes, sensitivity ceiling, blob replication policy, trust/encryption requirements delegated to Security, metered/network behavior, and event-driven/manual/cadence preferences.

### 3.2 Purpose

Multi-device users need work to appear on every device without an Atlas-operated server and without surrendering local-first guarantees. A transport contract gives this without tying canonical semantics to one wire protocol. A destination profile keeps all sync-target policy in one governable object instead of scattered settings.

### 3.3 Rule

- `SyncTransport` exposes at least: open local substrate with or without replication; push committed local state; pull committed remote state; report progress and typed outcomes; report connectivity and health; validate checkpoints; and expose transport-specific cursor payloads behind a canonical checkpoint envelope.
- The transport replicates the syncable substrate only. It never opens a replica against the device-local substrate, audit overlay, secret vault, TOML overlay, or any device-local file. "Never sync" is absence of a replica binding, not a row filter.
- The transport replicates committed source-of-truth records and content references, not projections or derived views.
- A canonical rule may name the committed transport for grounding, but must not depend on a transport-specific capability the contract does not expose.
- Sync credentials are `SecretRef`s. The credential material is never inline in settings, TOML, sync payloads, packages, logs, events, or agent context.

### 3.4 Sync Checkpoint

`SyncCheckpoint` is the common safety envelope for transport progress. It carries at least:

- sync destination profile id
- transport binding id
- local substrate identity and generation or fingerprint
- remote primary identity or fingerprint
- last acknowledged local cursor or revision
- last acknowledged remote cursor or revision
- pending blob references
- interrupted operation marker
- checkpoint validation status

A corrupt, mismatched, zeroed, or interrupted checkpoint produces a typed invalid-checkpoint state. Recovery revalidates from the last safe boundary or performs a non-destructive re-enumeration. It never truncates local data based on remote absence or a suspect cursor.

### 3.5 Boundary

This section owns the transport contract, destination profile, checkpoint envelope, and syncable-substrate-only rule. Section 6 owns conflict delivery. Section 7 owns blob transport. File 20 owns the substrate. Security owns stream encryption and credential internals.

## 4. The Local-First Invariant and Sync Enablement

Anchor: `portability.local-first`

### 4.1 Definition

The local-first invariant is the rule that every write is durable locally before sync and every read is served locally without waiting for the network. Sync enablement is the explicit act of binding the local syncable substrate to a `SyncDestinationProfile`.

### 4.2 Purpose

Local-first makes sync safe and optional. A single-device user sees no sync behavior. A multi-device user gains replication without waiting on the network for reads or writes and without losing work when the primary is unreachable.

### 4.3 Rule

- Every write is committed to the local substrate at its owning commit boundary before sync activity. Sync never sits on the write path; a write never waits for the primary.
- Reads are served from the local substrate and local projections; a read never waits for the network.
- Sync is disabled unless the user explicitly enables it. Disabled sync binds no replica, reads no credential, and emits no sync events.
- Enabling sync creates or selects a `SyncDestinationProfile`, records the primary reference and credential reference, validates policy, and begins replication.
- Disabling sync unbinds the replica and leaves the local substrate intact.
- When the primary is unreachable, writes and reads continue locally. Connectivity loss raises typed transport state and a `SyncFailed` event; it is not a failed write or blocked read.
- Sync cadence is a settings-owned latency policy, never a correctness condition. Event-driven push at commit boundaries is preferred where available. Polling or interval mechanisms are allowed only as transport-level latency mechanisms, configurable and killable, with no correctness property depending on elapsed time.

### 4.4 Boundary

This section owns local-first behavior and enablement. File 20 makes local writes durable. File 15 resolves settings. Section 3 owns the transport and destination profile.

## 5. What Replicates and What Does Not

Anchor: `portability.what-replicates`

### 5.1 Definition

Replication eligibility is the determination, per substrate family and setting, of whether a record participates in cross-device sync. It consumes File 20's structural partition, File 15's locality, and File 10's sensitivity.

### 5.2 Purpose

"Never sync" must be structural. Device-local integrity, device-bound accounting, raw secrets, and rebuildable derived data must not leave the device by a filter that can be misconfigured.

### 5.3 Rule

- **Replicates.** Syncable source-of-truth families File 20 places in the syncable substrate replicate when locality and sensitivity permit: block pool and edges, version graph and diffs, syncable ledger entries, artifacts, claims, evidence links, validations, critiques, memory entries, knowledge entries, settings tagged `Syncable`, source/registry metadata, cross-installation maps, pairing records, and other durable records their owning specs classify as syncable.
- **Blob bytes replicate separately.** Content-addressed blobs referenced by replicated source-of-truth records replicate through section 7, not as relational rows.
- **Registry and extension metadata.** Durable registry declarations, custom-kind schemas, capability declarations needed for inspection, source identities, approval records, and soft dependency references may replicate. Executable plugin code, binaries, scripts, connector runtimes, and installer payloads do not replicate as ordinary data.
- **World state default.** World-model records default to device-local unless their owning producer or spec declares a syncable, user-portable fact class. Displays, windows, processes, foreground state, browser sessions, sandboxes, capture state, device-specific observations, and `WorldView` projections never sync. Stable workspace definitions, portable user preferences, and approved source registrations may sync only when their owning specs declare them syncable.
- **Never replicates.** The device-local substrate, hash-chained audit overlay, per-device rate-limit state, TOML overlay, settings tagged `DeviceLocal` or `NeverSync`, per-device system-watch and scheduled-task execution state, machine-bound configuration, raw secret vault, projections, indexes, caches, provider-model cache, DAG node-output cache, and rebuildable derived views never replicate.
- **Per-conversation head.** `current_version_id` and pending operations are per-device conversation state unless a future shared-pointer mode explicitly defines otherwise.
- **Settings locality.** `Syncable` replicates. `WorkspaceLocal` replicates only within the shared workspace semantics that own it. `DeviceLocal`, `NeverSync`, and raw secret material do not replicate. `ExportOptIn` moves only when the user opts in. `SecretReferenceOnly` may replicate references, never secret material.
- **Sensitivity floor.** `Public` records replicate by default. `Sensitive` records replicate only when the user enables sensitive sync for the relevant scope. `Secret` payloads never replicate; only safe descriptions and opaque references may persist on each device.

### 5.4 Boundary

This section owns replication eligibility by consuming canonical classifications. File 20 owns structural partition. File 15 owns locality. File 10 owns sensitivity. File 18 owns world-model semantics. This file transports what those contracts permit and rebuilds the rest.

## 6. Conflict Resolution

Anchor: `portability.conflict-resolution`

### 6.1 Definition

Conflict resolution is how concurrent changes made on two devices reconcile when their substrates synchronize. The canonical rule is File 11's version-tree-aware merge: both branches survive, neither overwrites the other, and the user decides what to do with divergence.

### 6.2 Purpose

A user who edits the same conversation on two devices made two legitimate edits. Silent last-write-wins would destroy one. The version tree represents both; the transport delivers both.

### 6.3 Rule

- **Source-of-truth row conflict is impossible by construction.** Source-of-truth records are immutable, append-only, and UUID-keyed. Two devices create distinct records that union on sync; they do not contest the same durable row.
- **Version divergence becomes siblings.** Different children of the same parent version become siblings after sync. Neither overwrites the other. The remote child is appended to the local tree. `current_version_id` is unchanged. A `SyncVersionDiverged` event fires.
- **The per-device pointer is never yanked.** Pulling remote commits never moves the user's current view. The user switches or merges explicitly.
- **Sync is additive.** Remote absence never causes local deletion. Deletion propagates only as explicit tombstone records. Empty, partial, or failed remote responses are not authoritative absence.
- **Settings conflicts are causal.** Syncable setting values carry causal revision identity: `settings_value_revision_id`, `base_revision_id`, `device_id`, `actor_id`, and optional causal parents for merged values. A causally descendant write supersedes its ancestor. Concurrent writes to the same `(key, scope)` from the same base produce a typed settings conflict. No wall-clock or `updated_at` rule selects the winner.
- **Poisoned checkpoints self-heal non-destructively.** Bad checkpoints route through section 3.4. They never trigger destructive resync.
- **Unavailable references resolve to typed state.** A synced record referencing a missing capability, plugin, custom kind, blob, or connector remains preserved and resolves as unavailable until the dependency is installed, approved, or fetched.

### 6.4 Boundary

This section realizes File 11's merge semantics over the transport and adds settings-conflict, additive-sync, checkpoint-safety, and unavailable-reference behavior. Memory and knowledge keep their own proposal/revision mechanisms.

## 7. External-Content (Blob) Replication

Anchor: `portability.blob-replication`

### 7.1 Definition

External-content replication is the transport of content-addressed blobs separately from the relational substrate, with deferred fetch on the receiving device.

### 7.2 Purpose

Blobs are large, often duplicated, and not always needed immediately. Shipping references first and bytes on demand keeps sync fast, preserves deduplication, and respects metered devices.

### 7.3 Rule

- The relational substrate replicates `BlobRef` metadata: content hash, locator, size, media type, and availability facts. Blob bytes replicate separately.
- After a commit that references new blobs, the pushing device enumerates referenced blobs from source-of-truth records, never by scanning every blob file, then uploads only missing content hashes.
- On pull, referenced blob bytes are fetched on first access unless settings choose a broader fetch policy. Until fetched, the referencing block resolves to deferred availability and renders its description placeholder.
- A fetch failure does not discard the record. The placeholder remains and the user remains in control of refetch.
- Fetched bytes are verified against the content hash before they become locally present. Hash mismatch is a typed corruption signal handled through File 20 recovery.
- Blob endpoints and credentials are transport/destination-profile settings and secret references. Raw secrets never appear in blob locators.

### 7.4 Boundary

This section owns blob transport and deferred fetch. File 20 owns the blob store, content addressing, garbage collection, availability states, and orphan reconciliation. File 08 owns block description placeholders.

## 8. Device Identity and Pairing

Anchor: `portability.device-identity`

### 8.1 Definition

`DeviceIdentity` is device-local private identity material that anchors per-device state. `PairedDeviceRecord` is the syncable public record that represents an authorized device in the user's sync relationship. Pairing authorizes a device to replicate with the user's primary.

### 8.2 Purpose

Per-device state must be attributable without syncing private identity material. Users also need a synced device list and revocation propagation. Splitting identity from pairing record gives both.

### 8.3 Rule

- Each installation has a stable `DeviceIdentity`, assigned once and never reused. It keys the audit chain, rate-limit state, and per-device pointers. It is device-local and never synced, exported, or shared raw.
- Pairing is account-based against a user-controlled primary, with no Atlas-hosted server. The user points the device at a primary they control and authorizes it with credentials held in the secret vault.
- A `PairedDeviceRecord` is syncable metadata: device id or public fingerprint, display label, authorization status, capabilities, pairing source, revocation marker, and sensitivity/locality classification.
- Adding or removing a device is an explicit user action and a durable auditable fact. Removing a device writes a revocation record and unbinds its replica; it does not delete that device's local substrate. Other devices stop accepting future sync from a revoked device after seeing the revocation.
- Sync authorization credentials are secret-vault material. They never appear inline in settings, TOML, sync payloads, packages, logs, events, or agent context.
- ATLAS3 is local-first single-user software. Device pairing does not introduce multi-user identity, authentication principals, or per-user access control.

### 8.4 Boundary

This section owns per-device identity and pairing records. Security owns credential cryptography and trust proof. File 20 owns vault location boundaries. The primary is user-operated infrastructure outside Atlas.

## 9. Cross-Installation Identity and Provenance

Anchor: `portability.cross-installation-identity`

### 9.1 Definition

Cross-installation identity lets records move between distinct ATLAS installations while preserving identity, deduplicating content, and keeping provenance resolvable. `CrossInstallationMap` records how source installation identities relate to local identities.

### 9.2 Purpose

Importing data from another installation crosses a boundary. Identity must survive so references resolve. Content must deduplicate. Provenance must remain queryable without pretending foreign runtime history is local execution history.

### 9.3 Rule

- Durable identities are globally unique UUIDs preserved across sync and import. Within a logical installation, an identity is the same on every paired device.
- Foreign imports preserve identities by default. Same-id/different-content collisions are classified by section 11.3 and never silently merge or overwrite.
- Content-addressed blobs deduplicate by content hash.
- Import stamps an `Import { source_kind, source_ref }` producer record on every imported record and records `CrossInstallationMap` entries linking source installation identity, source record identity, and local identity.
- Originating runtime history is not imported as local execution history. A package may carry source provenance, source ledger references, source run summaries, or profile-specific source records; local import itself always creates new local ledger entries describing the import.
- `CrossInstallationMap` is durable syncable source-of-truth so imported provenance resolves identically on the user's paired devices.

### 9.4 Boundary

This section owns identity preservation, deduplication-on-import, and provenance maps. File 09 owns provenance query semantics. Section 11 owns import mechanics.

## 10. The Portable Package

Anchor: `portability.export-bundle`

### 10.1 Definition

`PortablePackage` is the canonical self-contained lossless package envelope: durable records encoded under declared `CanonicalEncoding`, content-addressed blobs those records reference, a `PackageManifest`, dependency declarations, and typed omission/redaction/provenance-gap records.

`PackageProfile` is closed here:

- `SharePackage`: safe portable exchange for selected data. Default inclusion is `Public`; `Sensitive` requires explicit opt-in; raw `Secret` never travels.
- `RecoveryArchive`: recovery-oriented package for selected source-of-truth scope. It includes the non-secret records needed for recovery, including `Sensitive` data after typed confirmation. Raw secret payloads still require the separate vault backup path.

Lossy presentation-format exports are surface-owned format capabilities outside the `PortablePackage` envelope. They pass through egress governance, sensitivity filtering, policy gating, and audit recording, but do not share the manifest, canonical encoding, integrity hash, or round-trip guarantee.

### 10.2 Purpose

The user needs a package that can be imported back without silent loss for the scope it claims to cover. One envelope with two profiles gives both safe sharing and recovery completeness without duplicating the import/export pipeline.

### 10.3 Required

A `PortablePackage` carries, for its selected scope and profile:

- source-of-truth records permitted by locality and sensitivity: blocks, edges, context versions, version diffs, artifact entities and versions, claims, evidence links, validations, critiques, settings values, memory entries, knowledge entries, syncable world facts, pairing records, cross-installation maps, and other included durable records
- profile-specific provenance records: `RecoveryArchive` carries in-scope run, ledger, route, model-selection, capability, policy, and provenance records needed for replay, inspection, and audit; `SharePackage` carries source provenance as referenced provenance, not as local execution history
- content-addressed blobs referenced by included records
- dependency declarations for custom block kinds, custom ledger/event kinds, capability declarations referenced by included records, plugin-owned settings definitions or profile layers, custom world/entity/observation kinds, and package schema extensions
- `PackageManifest`: source installation identity, package profile, creation anchor, included scopes, schema versions of included families, sensitivity floor, included blob content hashes and sizes, dependency declarations, omissions/redactions/provenance gaps, and integrity hash

Typed package gap records include:

- `PackageOmitted { source_id, source_kind, reason }`
- `PackageRedacted { source_id, source_kind, redaction_kind, reason }`
- `PackageProvenanceGap { source_id, gap_kind, reason }`

Cross-cutting reasons include `SensitivityRestriction`, `SecretPayloadExcluded`, `DeviceLocal`, `ProjectionExcluded`, `PolicyDenial`, `UserExcluded`, `UnavailableDependency`, `UnsupportedCustomKind`, and `CorruptOrMissingPayload`.

### 10.4 Canonical Encoding and Integrity

- Package records are encoded under declared `CanonicalEncoding`, never raw storage bytes.
- The physical container layout is independent of canonical encoding.
- The package integrity hash is computed over the canonical encoding of `PackageManifest` excluding the integrity-hash field itself, the sorted canonical encodings of included source-of-truth records, sorted blob content hashes and declared sizes, and sorted omission/redaction/provenance-gap records.
- Sorting is by canonical identity and kind before hashing.
- A package whose manifest, record, or blob hash does not verify is rejected before visible import.

### 10.5 Rule

- Export scope is selectable: single conversation, artifact, workspace, named substrate, settings/profile subset, memory/knowledge subset, view preset, workflow/automation definition, or full archive.
- Round-trip and lossless guarantees apply to the effective included scope after declared omissions and redactions. Nothing may be omitted silently.
- Recovery completeness is a property of `RecoveryArchive`, plus vault backup for raw secrets and optional full-substrate backup for same-installation recovery. A `SharePackage` is not a complete disaster-recovery set unless its selected scope and omissions make that true.
- Export preview returns the proposed manifest, included records, omitted/redacted/gap records, blob set, dependency declarations, sensitivity floor, package profile, and destination shape without writing a package.

### 10.6 Boundary

This section owns the lossless package envelope, profile set, required contents, manifest, gaps, dependency closure, and hash semantics. Per-surface format exporters own their lossy formats. Section 11 owns import. File 20 owns blob storage. File 06 owns policy.

## 11. The Import Pipeline

Anchor: `portability.import-pipeline`

### 11.1 Definition

The import pipeline is the validated, deduplicating, staged, atomic sequence that brings a `PortablePackage`, a foreign installation's data, or a foreign/external format handled by a registered import capability into the substrate. `ImportPlan` is the previewed typed decision object produced before any visible record is committed.

### 11.2 Purpose

Import must never corrupt the receiving substrate, silently overwrite user data, duplicate content, strip provenance, activate unapproved code, or admit raw secret material. A staged pipeline with a reviewable plan and atomic visibility keeps import safe.

### 11.3 Rule

The import pipeline proceeds in order:

1. **Validate source and manifest.** Manifest, schema versions, dependency declarations, canonical encodings, and integrity hashes are checked. Tampered, truncated, hash-mismatched, or structurally invalid packages are rejected before visible writes.
2. **Create staging area.** Blobs and materialized payloads write to an `ImportStagingArea`. Staged blob bytes are hash-verified before any record can reference them authoritatively.
3. **Normalize on load.** Package schema versions and per-record schema versions are normalized to current shapes through File 20/File 15/File 09 mechanisms. Foreign/external formats enter only through explicit registered import capabilities. This file does not require migration/adaptation paths for obsolete draft schemas or nonexistent deployed user data.
4. **Resolve dependencies.** Custom kinds, capability declarations, plugin-owned settings definitions, extension references, and connector references are resolved. Missing implementations are preserved as inert/unavailable dependency states; importing a package never installs, updates, enables, or executes plugin or connector code.
5. **Remap foreign references while preserving UUIDs.** Identities are preserved by default. Cross-references are resolved through a UUID-preserving pass. `CrossInstallationMap` entries are prepared.
6. **Deduplicate by content.** Existing blobs and content-equal records are referenced by content hash where safe.
7. **Classify sensitivity and locality.** Imported records carry source sensitivity. Unclassified content defaults upward toward `Sensitive`, never downward. Raw secret payloads are rejected or converted to allowed references/descriptions according to owning semantics.
8. **Pass source approval and policy.** Foreign records, settings, profiles, knowledge, custom kinds, and source-owned declarations pass source approval and policy gates before commit.
9. **Resolve collisions by class.** Collision classes are:
   - same id plus same canonical content hash: no-op or dedup
   - same id plus different content in the same source lineage: typed hard collision; default fail; user may import as fork/new identity only with explicit provenance-gap acknowledgement
   - same id plus different content where local record is structurally proven to descend from the import record through version parentage, supersedes edges, or revision history: `SupersededLocally { local_version_id, import_version_id }`; default skip; no user interaction required
   - different id plus same content hash: dedup/link where safe, never identity merge by default
   - semantic duplicate with different content: surface as possible duplicate; no automatic merge
10. **Propose or commit per substrate.** Substrates with proposal discipline, such as memory and knowledge, route imported records through their proposal path. Other records prepare direct commits.
11. **Commit atomically and promote staged payloads.** Durable records commit in one storage transaction. Staged blobs promote by atomic rename or content-addressed no-op. A failed import leaves no visible imported records and no authoritative blob references.
12. **Record import and rebuild projections.** Imported records receive `Import` producer records. Local import ledger entries record the operation. Projections and indexes rebuild from committed source-of-truth and blobs; they are never imported as authoritative data.

`ImportPlan` includes at least: included source records by kind and scope; dedup/no-op records; collision classes and selected actions; omissions, redactions, and provenance gaps; sensitivity changes and policy restrictions; required approvals and source approvals; dependency states; staged blobs and missing/corrupt/deferred blobs; projection rebuild plan; expected local ledger/provenance effects; and commit/staging behavior.

Import is non-destructive: it adds, proposes, skips, or forks under explicit rules. It never silently overwrites existing local data.

### 11.4 Boundary

This section owns import ordering, staging, `ImportPlan`, collision classes, and atomic visibility. File 20 owns transactions, blob writes, and orphan cleanup. Files 14 and 12 own proposal disciplines. Files 05 and 06 own capability registry and source approval. File 08 owns `Import` producer fields.

## 12. Sensitivity, Secrets, and Egress Governance

Anchor: `portability.sensitivity-egress`

### 12.1 Definition

Egress governance is the rule set applied whenever data leaves the device or installation: sync to a primary, export to a package, surface-owned format export, sharing, publishing, clipboard copy, or external destination transfer.

### 12.2 Purpose

Data leaving the device is the moment privacy and secrecy are at stake. Governance makes the safe default automatic and every widening explicit, policy-gated, and auditable.

### 12.3 Rule

- Raw `Secret` material never egresses. It never enters sync streams, packages, shares, publishes, clipboard copies, logs, events, agent context, or substrate backups. Only safe descriptions and opaque references may travel.
- Default egress is `Public` only. `Sensitive` egress requires explicit opt-in at the relevant scope and operation. `Secret` content never egresses as raw payload.
- Egress is a governed capability. Export to external destinations, publishing, external sharing, sensitive export, and restore/backup operations route through File 06 policy and typed confirmation where required.
- Redaction before egress is explicit and typed. Redaction produces manifest redaction records and provenance gaps where needed. A per-field override may raise effective sensitivity, never silently lower it.
- Egress is auditable. Every export, share, publish, sensitivity widening, import of foreign data, pairing change, backup, and restore is recorded. Security-sensitive local facts participate in the device-local audit overlay; the audit overlay itself does not egress.
- Surface-owned presentation-format exports share sensitivity filtering, policy gating, and audit recording with package exports. They do not receive package round-trip guarantees.

### 12.4 Boundary

This section owns the movement application of egress governance: where data leaves, how packages and sync streams omit or redact content, how movement is audited, and the no-raw-secret-egress invariant at the movement boundary. File 22 owns the egress security policy semantics — the sensitivity-tier rules, the egress-destination inspector, the secret-egress exceptions, and the redaction-before-egress policy (`security.egress-governance`, File 22 §11); File 10 owns the sensitivity taxonomy; File 06 owns the gate and the floor. This section consumes those and adds no egress rule beyond the movement boundary; cryptography and vault-backup internals stay File 22's.

## 13. Backup, Restore, and Archival

Anchor: `portability.backup-restore`

### 13.1 Definition

Backup is production of a recoverable copy. Restore returns the system to a backed-up state. Archival is long-term retention of a portable copy. This section distinguishes `FullSubstrateBackup`, `RecoveryArchive`, and `VaultBackup`.

### 13.2 Purpose

Different recovery needs require different artifacts. A full-substrate backup is fast same-installation recovery. A recovery archive is portable cross-installation recovery for non-secret source-of-truth. A vault backup handles raw secrets separately under Security.

### 13.3 Rule

- `FullSubstrateBackup` is a same-installation/local disaster recovery snapshot produced through File 20. It may include the device-local substrate only when explicitly selected. It is not a sync/share artifact.
- `RecoveryArchive` is a `PortablePackage` profile for cross-installation and long-term source-of-truth recovery. It is schema-resilient and content-addressed. Raw secrets require `VaultBackup`.
- `VaultBackup` is a separate explicit user action governed by File 22 and File 20's vault/storage boundary. Raw secrets never enter ordinary packages, sync streams, or full-substrate backups.
- Projection stores and caches are excluded or marked disposable acceleration. They are never authoritative recovery data.
- Restore over live data stages a pre-restore backup, quarantine, or rollback handle before replacing authoritative records. The consequence is surfaced before proceeding.
- When sync is enabled, the primary can be an additional recovery source for syncable source-of-truth. Device-local substrate is recovered only from local backup, not cross-device sync.
- Backup and restore are non-destructive and explicit. Time-based backup behavior may exist only as user-selected/profile-selected automation, not a hidden correctness condition.

### 13.4 Boundary

This section owns backup-family distinctions and their relationship to portability. File 20 owns substrate backup and corruption recovery. Security owns vault backup internals. Section 11 owns package restore through import.

## 14. Capability Surface

Anchor: `portability.capability-surface`

### 14.1 Definition

The portability layer exposes canonical capabilities for sync control, export, import, sharing, and backup/restore, declared and gated like every other capability.

### 14.2 Rule

- Canonical capabilities include enabling/disabling sync, editing destination profiles, pairing/unpairing devices, pushing/pulling, previewing and producing packages, previewing and producing surface-owned format exports, previewing and running imports, generating/revoking shares, creating backups, and restoring backups.
- Egress capabilities carry section 12 policy gates. Import that introduces foreign records carries source approval. Restore over live data and unpair-with-wipe-style operations expose preview plans and typed confirmation.
- Preview is first-class. Package export preview returns the proposed manifest and included/omitted/redacted/gap sets. Import preview returns `ImportPlan`. Format-export preview returns its own surface-owned preview plus egress classification.
- Long-running sync, export, import, backup, and restore operations are cancellable and killable per File 04. They report progress from durable boundaries, record counts, blob hashes, checkpoints, and typed outcomes, not elapsed time.
- No portability capability may bypass sensitivity filtering, no-secret-egress, source approval, dependency closure, or policy.

### 14.3 Boundary

This section names the capability surface. File 05 owns declarations. File 06 owns policy. File 07 owns loading. Surface specs own surface-specific exporters.

## 15. Events

Anchor: `portability.events`

### 15.1 Definition

The portability layer emits typed events through File 10's canonical bus and records consequential operations as ledger entries.

### 15.2 Rule

- The canonical sync events already in File 10 are emitted by this layer: `SyncPulled`, `SyncPushed`, `SyncVersionDiverged`, `SyncBlobFetched`, and `SyncFailed`.
- Import, export, sharing, pairing, backup, restore, checkpoint, collision, dependency, omission/redaction, and settings-conflict facts not already in File 10's catalogue are registered as `Custom { namespace: "portability", name, payload }`.
- Events that touch `Sensitive` or `Secret` content carry corresponding sensitivity. Raw secret payloads never appear in event payloads.
- Elapsed duration may be recorded as diagnostic metadata only. Sync/import/export correctness is determined by durable boundaries, cursors, record counts, hashes, checkpoints, and typed outcomes.
- Portability events flow only through the canonical bus. No side-channel sync, export, or import notification is permitted.

### 15.3 Boundary

This section names portability event behavior. File 10 owns envelopes, sequencing, delivery, hookability, persistence, and the closed sync entry kinds.

## 16. Settings

Anchor: `portability.settings`

### 16.1 Rule

Every portability mechanism with meaningful variation is configurable through File 15 settings. Settings use namespaced keys and declare scope, agent exposure, locality, and sensitivity.

Dimensions include:

- sync enablement
- `SyncDestinationProfile` selection and fields
- sync credential reference as `SecretRef`, never inline
- enabled sync scopes
- sensitivity floor for sync, package export, surface-owned format export, share, publish, and clipboard
- sync divergence notification and branch-switch preferences
- blob-fetch policy and metered-connection behavior
- package profile defaults and export scope defaults
- redaction policy for sensitive egress
- import source-approval strictness and collision defaults
- dependency handling defaults for missing custom kinds/plugins/connectors
- backup family, backup scope, restore preview behavior, and retention policy
- transport cadence/event-driven/manual preference as latency policy only

Specific defaults belong to tested settings profiles, not hardcoded constants. No portability behavior is a hidden branch where a meaningful behavioral variation exists.

## 17. Explicit Rejections

Anchor: `portability.explicit-rejections`

The following shapes are wrong for this layer:

- silent last-write-wins for concurrent shared state, including `if remote.updated_at > local.updated_at` logic
- clock-based settings conflict resolution
- implicit merge or squash of divergent branches at sync
- deleting local data because a record is absent from a remote pull
- treating an empty, corrupt, or failed remote response as authoritative absence
- per-table filters or per-row flags as the mechanism for "never sync"
- replicating the device-local substrate, audit overlay, rate-limit state, TOML overlay, secret vault, projections, indexes, or rebuildable caches
- raw `Secret` material in a sync stream, package, share, publish, clipboard copy, log, event, backup, or agent context
- default sync/export/share that includes `Sensitive` data without explicit opt-in
- egress as an ungoverned action
- private replication mechanisms, private cross-device stores, private package formats, or private import paths
- parallel durable stores or second blob stores introduced by sync/export/import
- replicating projections instead of rebuilding them
- integer autoincrement identity on replicated families
- identity remap during sync
- silent overwrite on import
- broad user choice on identity collisions without collision-class constraints
- importing without validation, normalization, staging, deduplication, sensitivity classification, source approval, dependency handling, collision handling, and atomic visibility
- importing or executing plugin/connector code as a side effect of data import
- package dependency on target tables or implementation-private stores
- package omission, redaction, or provenance gaps that are not declared in the manifest
- bundle integrity hashes over physical storage bytes rather than declared `CanonicalEncoding`
- sync cadence, blob-fetch interval, elapsed duration, or polling interval as a correctness condition
- remote action replay as the sync mechanism
- an Atlas-hosted sync server or Atlas-owned user-data server
- conflating data portability with application distribution
- hidden migration/adaptation paths for obsolete draft schemas or nonexistent deployed user data

## 18. Consequences for Later Specs

Anchor: `portability.consequences`

Later specs must follow these rules:

- File 22 owns stream/package encryption, sync-credential storage internals, key derivation, vault backup internals, and device trust. It must keep raw secrets out of sync streams, ordinary packages, substrate backups, logs, events, and agent context.
- File 24 persists workspace identity and materialized mirrors as substrate families. Workspace export/import uses `PortablePackage`, blob transport, and the import pipeline for lossless movement; surface-owned format exports remain lossy egress capabilities.
- The **per-surface specs** may declare lossy presentation-format exports, but every such export passes through egress governance, audit recording, and sensitivity filtering. Their durable state rides the syncable substrate and `PortablePackage`, never a private export path.
- The **Automation and Triggers** spec (File 33) tags machine-bound execution state device-local while replicating portable schedule, watch, and trigger definitions when allowed. It drives nothing from sync cadence.
- The **Extension and Plugin System** (File 35) and **MCP and External Integrations** (File 36) specs make synced/imported records referencing missing capabilities, plugins, custom kinds, connectors, or MCP servers resolve to unavailable/inert states. They own installation, execution, enablement, and update of code.
- The **UI Shell** spec (File 37) and the **UI Customization** spec (File 38) render sync status, destination profiles, export preview, import review, `ImportPlan`, divergence resolution, collision classes, dependency gaps, omissions/redactions, and backup/restore surfaces from the contracts this file defines.
- The **Telemetry, Logging, and Observability** spec (File 41) consumes portability events as data and builds views as projections. It never makes telemetry a source of truth and never egresses content this file excludes.
- The **Evaluation and Benchmarking** spec (File 40) verifies package export/import round-trip, import idempotence, interruption safety, tamper rejection, additive sync safety, causal settings conflicts, restore staging, golden canonical-encoding fixtures for package hashes, and replay equivalence over typed package contents. It replays over recorded snapshots and immutable references, not live sync state.
- Every later spec that produces durable state declares replication eligibility, export inclusion, import handling, dependency declarations, and sensitivity behavior. It obeys no-secret-egress, no-silent-last-write-wins, UUID preservation, content-addressed deduplication, additive sync, typed gaps, and package round-trip rules.
