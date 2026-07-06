# Phase 20 — Sync, Import/Export & Data Portability

## 1. Goal & why now

File 21's four responsibilities over the P2 locality partition: lossless `PortablePackage` export,
the validated/staged/atomic import pipeline, optional cross-device sync via a replaceable
`SyncTransport` (committed realization: libsql embedded replicas against a user-controlled primary —
no Atlas-hosted server), and conflict-resolution delivery riding File 11's both-children-survive
semantics built in P3. Two largely independent slices, built in order: **export/import first, sync
second** — recovery and portability matter before multi-device. Placed after the surfaces so there is
a populated system worth porting; its prerequisites (P9 identity split, P8 egress, P3 merge
semantics) have been ready since mid-trunk, so this phase may overlap P18/P19.

## 2. Canonical scope & deferrals

- **File 21 — complete**: the `SyncTransport` contract + `SyncDestinationProfile` + the
  `SyncCheckpoint` safety envelope — a corrupt/interrupted checkpoint self-heals non-destructively,
  never truncates local data on remote absence (§3); **the local-first invariant** — every write
  durable locally before sync; sync never on the write path; reads never wait on the network; sync
  opt-in and disabled by default (§4); replication eligibility — structural by partition + locality
  + sensitivity (`Public` replicates, `Sensitive` opt-in per scope, raw `Secret` never; executable
  code never replicates as data; world facts default device-local) (§5); **conflict delivery** —
  source-of-truth rows union (immutable/append-only/UUID-keyed); **version divergence becomes
  siblings** (remote child appended, per-device pointer never yanked); **additive sync** (remote
  absence never deletes; deletion only via explicit tombstones); **causal settings conflict**
  (revision/base/device/actor metadata — **no wall-clock/`updated_at` winner ever**) (§6);
  content-addressed blob replication — deferred fetch, hash-verified before locally-present (§7);
  `DeviceIdentity` (device-local, never synced, never reused) + `PairedDeviceRecord` + pairing over
  22 §10 (§8); cross-installation identity — UUIDs preserved, content-hash dedup,
  `CrossInstallationMap`, `Import` producer records; foreign runtime history is provenance, not
  local execution history (§9); **the `PortablePackage`** — the lossless envelope; closed
  `PackageProfile` (SharePackage / RecoveryArchive); records under CanonicalEncoding +
  content-addressed blobs + the `PackageManifest` + **typed omission/redaction/provenance-gap
  records — nothing omitted silently**; the integrity hash over CanonicalEncoding, never physical
  container bytes (§10); **the import pipeline** — the 12-step staged/atomic/deduplicating sequence
  with `ImportPlan` preview, collision classes, sensitivity-classified-upward, source-approval
  gates, **a failed import leaves no visible records and no authoritative blob references**;
  importing never installs/executes code (§11); egress governance at the movement boundary (§12,
  the P8 gate); backup families — vault backup a separate `Denied`+typed-confirmation path (§13).
- **File 24 — §16**: workspace export/import riding the package; `root_path` never imported as
  authoritative (arrives Unbound or asks).
- **File 22 — §8 attachment points**: sync-stream encryption required; export-package encryption
  optional; **encryption never changes identity/hashes/replication semantics** (attached over
  plaintext canonical encodings).

## 3. Prerequisites

P9 — the workspace identity/path split; entities to port. P8 — the egress gate, device-trust shapes,
encryption. P3 — the version-graph merge semantics (implemented then, transported now). P2 — the
locality partition (structural since day one, paying off here). P14/P18 — automation/connector
sync-eligibility declarations (definitions inert, activation local).

## 4. Lanes

(a) Export — the package + manifest + integrity hash; (b) import — the 12-step pipeline; (c) sync —
transport + checkpoints + conflict delivery; (d) device identity + pairing. (a) → (b); (c)/(d)
independent of (a)/(b). May overlap P18/P19.

## 5. Build plan

1. **Export**: scope selection → records under CanonicalEncoding + referenced blobs + manifest +
   integrity hash; declared typed gaps; profile-gated sensitivity (SharePackage Public-default;
   RecoveryArchive + Sensitive behind typed confirmation); optional encryption envelope.
2. **Import**: validate manifest/hashes → stage blobs (hash-verify) → normalize-on-load → resolve
   deps (missing → inert states) → UUID-preserving remap → content dedup → sensitivity-upward
   classification → source-approval/policy gates → collision-class resolution → propose/commit per
   substrate → atomic promote → record + rebuild projections. `ImportPlan` preview before any
   visible write.
3. **Sync**: the transport over libsql embedded replicas (replicating only the syncable substrate —
   never device-local/audit/vault/TOML); enablement flow (destination profile, credentials via
   vault, policy validation); push after local commit boundaries; pull → remote commits appended as
   siblings; checkpoint self-healing; blob deferred fetch.
4. **Settings conflicts**: causal metadata (`settings_value_revision_id`/`base_revision_id`/
   `device_id`/`actor_id`) on syncable values; a reset-to-inherit/unset is itself a causally
   descendant unset revision (the settings tombstone, never a row delete); concurrent same-(key,scope)
   writes from the same base produce a typed conflict — each device's local value stays effective,
   neither revision auto-wins, and the user resolves it with an ordinary `settings.write` recording
   both revisions as causal parents (no new capability), surfaced through the settings-conflict
   notification (21 §6).
5. **Device pairing**: DeviceIdentity assignment; pairing records; revocation; the 22 §10 trust
   hooks realized.
6. **Receiving-device rebuilds**: projections/indexes/caches rebuilt locally, never transported as
   authoritative (the P2 rebuild orchestrator's payoff).
7. **Workspace + definition portability**: workspace packages (binding device-local — Unbound +
   explicit rebind on arrival); automation/workflow definitions sync inert, activation revalidates
   locally (33 §18.2); connector/plugin code never moves as sync data.

## 6. Test obligations & acceptance evidence

- **No-silent-last-write-wins** (the headline family): no `if remote.updated_at > local.updated_at`
  anywhere (grep + tests); version divergence → both siblings + `SyncVersionDiverged`, the
  per-device pointer never yanked; settings conflicts resolve by causal revision identity, never
  clock — neither revision auto-wins, each device's value stays effective, resolution is a user
  `settings.write` recording both as causal parents (21 §6), and a reset is a causally descendant
  unset revision, never a row delete; concurrent same-base writes → typed conflict surfaced with
  notification.
- **Additive sync**: remote absence never causes local deletion; deletion only as explicit
  tombstones; empty/corrupt/failed remote responses are not authoritative absence.
- **Local-first**: every write durable locally before any sync activity; reads never wait on the
  network; disabled sync binds no replica and reads no credential; loss of the primary degrades to
  single-device with no lost write and no blocked read.
- **Secret-never-egresses**: raw `Secret` never enters a sync stream/package/share/clipboard/backup;
  sync credentials are `SecretRef`s; the P8 encryption-identity-unchanged test now exercised on real
  packages and streams.
- **Canonical-hash package integrity**: the integrity hash over CanonicalEncoding (manifest + sorted
  record encodings + sorted blob hashes + sorted gap records); a non-verifying package rejected
  before visible import; **golden canonical-encoding fixtures pin the package encoding**.
- **Round-trip losslessness + typed gaps**: export → import reproduces the effective included scope;
  idempotent re-import; nothing omitted silently.
- **Import staged/atomic/non-destructive**: a failed/interrupted import leaves nothing visible; the
  collision-class matrix (same-id+same-hash → no-op; same-id+different-content → hard collision
  default-fail; descend-proven → superseded auto-skip; different-id+same-hash → dedup, never
  identity-merge); UUID preservation; **no code execution on import**.
- Blob fetch hash-verified before locally-present; checkpoint safety — a suspect cursor never
  truncates local data; projection-rebuild on receive; no sync cadence as a correctness condition;
  no Atlas-hosted server (architectural assertion).
- **Closed-set pinning**: `PackageProfile`, the collision classes, the typed gap-record kinds,
  replication-eligibility classes.
- Conformance matrix gains: 21 anchors + 24 §16 + 22 §8 attachments; the P9 workspace-export and P8
  device-trust stub rows close.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `SyncTransport`/`SyncDestinationProfile`/`SyncCheckpoint`,
  `PortablePackage`/`PackageManifest`/`PackageProfile` + gap records, `ImportPlan` + collision
  classes, `CrossInstallationMap`/`DeviceIdentity`/`PairedDeviceRecord`; golden package-encoding
  fixtures; migrations for the pairing/cross-installation families.
- **Docs**: the local-first + what-replicates doc; the conflict-resolution doc (siblings + causal
  settings); the package + integrity doc; the import-pipeline + collision-class doc; the
  egress-at-movement doc; the device-pairing doc.
- **CI/local commands**: `export-package`, `import-package` (with `--plan`); the
  no-last-write-wins, additive-sync, local-first, secret-never-egresses, package-integrity (golden),
  round-trip-lossless, and import-atomicity suites as named CI jobs; the **two-instance sync
  harness** (two data roots + a local primary) as a permanent CI fixture.

## 8. Exit criteria

- [ ] Export → wipe → import: full-fidelity recovery (RecoveryArchive) proven on a populated
      instance, including workspaces (Unbound + rebind) and rebuilt indexes/projections.
- [ ] The two-instance harness: divergent edits on both sides → both children survive on both
      devices; settings conflict surfaced typed; blob deferred-fetch verified.
- [ ] The tamper/fault matrix green (corrupted package, poisoned checkpoint, interrupted import,
      partial blob).
- [ ] M0–M3 still green.

## 9. Locked in this phase

- **The `PortablePackage` envelope + `PackageManifest` contents + the closed `PackageProfile` set +
  the integrity-hash computation** — the portability wire format; cross-version import depends on it
  forever.
- **The `SyncTransport`/`SyncCheckpoint`/`SyncDestinationProfile` contract surfaces** (the transport
  is replaceable; the contract is the boundary).
- **The causal settings-conflict metadata schema**; the collision-class set; the
  `CrossInstallationMap` + `Import` producer shapes; the `DeviceIdentity`/`PairedDeviceRecord`
  split (DeviceIdentity never reused, never synced).
- The replication-eligibility rules ("never sync" is structural); **no Atlas-hosted user-data
  server** — permanent.
