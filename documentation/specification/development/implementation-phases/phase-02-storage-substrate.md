# Phase 2 — Storage Substrate

## 1. Goal & why now

The one durable store: `StorageEngine` over SQLite/libsql with the three-plane model (durable
substrate / content-addressed blob store / projection store), bootstrap-from-empty, transactions
mapped to commit boundaries, forward-only migrations, and the recovery hierarchy — plus the File 22
secret-boundary *forms* wired at the write chokepoints before any sink exists. Most canonical
primitives are durable or reconstructable; nothing above this layer can be built honestly until it
exists. The two foundational equivalence harnesses (projection-rebuild, restart/recovery) are built
here and run for the life of the project.

## 2. Canonical scope & deferrals

- **File 20 — core**: three planes + source-of-truth-vs-projection classification (§2); durable
  substrate with `*_schema_version` stamping + global never-reused identity + typed soft
  cross-partition reference states (§3); single-writer/many-reader WAL connection model (§4);
  transaction = commit boundary + write-ahead discipline (§5); content-addressed `BlobStore` —
  staged atomic writes, reference-counted GC + reachability reconciliation, availability states
  (§6); projection store + rebuild orchestrator (§7); **locality partition: physically separate
  syncable vs device-local substrates** (§8); physical-vs-canonical encoding separation (§9);
  forward-only migrations + mandatory pre-migration backup + normalization-on-load (§10); retention
  defaults (keep-everything) + accounting + dry-run (§11); backup/integrity/recovery hierarchy +
  last-known-good (§12); startup/shutdown lifecycle + single-instance lock placement + deterministic
  reconstruction (§13); vault-file location + substrate-exclusion (§14, boundary only).
- **File 22 — boundary forms only** (§4, §5.4, §7 skeleton): `SecretRef` / `vault:<key>` reference
  forms; the `SecretValue` wrapper (redacting Debug/Display, `expose` accessor, zeroization);
  forbidden-destination rejection at the substrate write boundary (per 20 §3.4); the secret-detector
  skeleton + redacting log formatter. Vault internals → **P7**; trust/egress → **P8**.
- Deferred from 20: sync-transport realization → **P20** (File 21); workspace materialization mirror
  → **P9** (File 24); encryption-at-rest enablement → **P7/P8** (the config boundary is laid now);
  eval retention holds → **P13**.

## 3. Prerequisites

P1 — CanonicalEncoding, hashes, identity, typed errors. The kernel crate is what makes "hashes
computed over canonical encoding ONLY" (20 §9) possible from the first row.

## 4. Lanes

Once the `StorageEngine` contract trait is defined: the libsql binding, the `BlobStore`, the
projection registry/rebuild orchestrator, and the migration framework are separable lanes — the
migration framework gates the others (they register schema through it). Secret-boundary forms are a
thin independent lane.

## 5. Build plan

1. **Engine bring-up**: open/create against an empty data root (bootstrap env var + platform
   user-data-dir, 20 §8.3); lock-file placement (acquisition contract finalized with 42 in P4);
   migrations 0..N from the **initial product schema** — no migration code for pre-product data
   (20 §10.3); the schema-version control record.
2. **Durable-substrate write path**: one generic family writer (typed bytes under identity + schema
   version, 20 §1.4) so later phases add families without touching the engine; **write-boundary
   guards**: unkeyed model-dependent scalars and raw `Secret` payloads rejected at the substrate
   boundary, "not only in the executor" (20 §3.4).
3. **BlobStore**: content-hash addressing over CanonicalEncoding; staged write → verify-against-hash
   → atomic promote; reference counting + full-reachability reconciliation sweep (explicit/startup/
   low-space triggers, never a hidden clock); the four availability states.
4. **Projection store + rebuild orchestrator**: register-projection API (substrate + rebuild trigger
   declared — File 11 §16 formalizes the consumer contract in P3); drop-and-rebuild path; rebuild
   markers (interrupted rebuilds restart cleanly); the integrity-hash verification hook (consumes
   `expected_view_hash` from P3).
5. **Locality partition**: two physically separate substrates from day one — "never sync" is
   *structural* (absence of a replica binding), not a row filter (20 §8.3). Device-local hosts the
   audit overlay (P3), RateLimitState (P7), runtime caches.
6. **Transactions & crash safety**: commit boundary ↔ exactly one transaction; write-ahead discipline
   (substrate before/with projection); crash roll-forward to the last committed boundary.
7. **Recovery hierarchy**: projection-rebuild → substrate-restore → quarantine (never the first
   response); startup self-checks + last-known-good rollback; pre-migration backup mandatory.
8. **Secret-boundary forms** (22 §4): the kernel-adjacent crate exporting `SecretRef`/`SecretValue`;
   the redacting `tracing` formatter installed globally; the detector skeleton (registered patterns +
   entropy stub) feeding sensitivity stamping later.
9. **Shutdown**: flag → stop writes → cooperative drain → commit/rollback at safe boundaries → flush
   → WAL checkpoint → close → release lock (20 §13.3).

## 6. Test obligations & acceptance evidence

- **PROJECTION-REBUILD EQUIVALENCE harness** (20 §7.4): delete the projection store, rebuild from
  substrate + blobs, byte-compare modulo typed gaps. Permanent CI fixture; every later projection
  registers into it.
- **RESTART/RECOVERY EQUIVALENCE harness** (20 §12.3): clean shutdown / crash-injection /
  interrupted-rebuild / projection-corruption (rebuild) / substrate-corruption (restore) → next run
  sees the same materialized state or an explicit typed recovery gap; **no silent fresh-start over
  recoverable data**. Permanent CI fixture.
- Atomicity: a multi-record commit boundary is all-or-nothing across crash mid-write (20 §5.3) —
  deterministic fault injection, not timing.
- Migration suite: apply-all-from-scratch; upgrade fixture; failed migration rolls back and halts
  typed (never half-migrated); backup taken before the first pending migration; normalization-on-load
  reads an older `*_schema_version` record without rewriting it (20 §10.3).
- BlobStore: staged-write crash orphan cleanup; GC never removes a blob reachable from any version
  including tombstones; refcount-drift correction; a corrupted blob is never silently served (§6.3).
- **Encoding separation** (20 §9.3): physically-different/canonically-equal rows hash identically;
  golden canonical-encoding tests for blob addressing.
- Write-boundary guards: unkeyed-scalar write rejected; raw-secret write rejected — even with vault
  internals stubbed (20 §3.4).
- Concurrency: concurrent writes serialized, never lost (20 §4.3). Retention: nothing pruned without
  explicit opt-in; dry-run reports before destructive reclamation (20 §11.3).
- `SecretValue` Debug/Display renders the redaction marker; buffers zeroize; the redacting formatter
  leaks nothing (golden secret-shape fixtures, seeded set).
- Conformance matrix gains: `storage.*` core anchors; `secret.backend-boundary` (forms, partial —
  closes P7/P8); the projection-rebuild and canonical-hash obligation families flip to implemented
  for storage's scope.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: migration files (generator documented, reproducible, never hand-edited);
  canonical-encoding fixtures for blob addressing; shared types for the reference-state and
  availability-state enums.
- **Docs**: storage architecture doc (three planes, partition, engine boundary); schema/migration
  doc; recovery-hierarchy doc; decision record for the locality-partition realization (two physical
  substrates vs per-table filter).
- **CI/local commands**: `db-migrate`, `db-backup`, `storage-rebuild`, `storage-verify`; the two
  equivalence harnesses as named permanent CI jobs.

## 8. Exit criteria

- [ ] Both equivalence harnesses green on 3 OSes and wired as permanent CI jobs.
- [ ] Crash-injection suite green; empty-install boot works; a second instance is locked out.
- [ ] Secret forms exported; write-boundary rejections demonstrably firing.
- [ ] No raw secret can enter the durable substrate (only refs + safe descriptions), proven by test.

## 9. Locked in this phase

- **Three-plane split + source-of-truth-vs-projection classification** (20 §2) — the foundational
  invariant.
- **Locality partition as physically separate substrates** (20 §8.3) — retrofitting a partition split
  after data exists is prohibitive.
- On-disk directory layout under one data root (20 §8.3) — referenced later by 24 (materialization),
  22 (vault file), 10 (audit overlay), 42 (lock).
- Blob content-addressing scheme; `*_schema_version` stamping; the global identity namespace.
- Forward-only migration discipline; **schema is human-governed** — no raw-query or schema-mutation
  capability to the agent, ever (20 §10.3/§15.2).
- `SecretRef`/`vault:<key>`/`SecretValue` forms (22 §4/§5.4) — the wire contract shared with
  15/17/21/23/36.
