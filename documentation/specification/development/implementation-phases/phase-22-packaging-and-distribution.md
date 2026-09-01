# Phase 22 — Packaging & Distribution Completion

## 1. Goal & why now

File 43 beyond the P0 first-commit set and the P4 installers, plus File 42 §18's apply-on-restart
relaunch: full installers honoring the read-only-image/data-root split, idempotent platform
integrations, the `BuiltinBundle` finalized (every ship-with item accumulated across the phases under
the signed item manifest), the update pipeline (check→download→verify→stage→relaunch→pre-stable
checks→last-known-good), the platform crash handler, native-messaging host registration, and the
`SidecarInventory`. Packaging comes last among the delivery layers because it ships what the runtime
and owning layers already define — building release mechanics earlier would freeze incomplete
assumptions about sidecars, ship-with content, trust, and platform integration. Packaging
**delivers; it never runs** (the static counterpart of 42).

## 2. Canonical scope & deferrals

- **File 43 — completion**: the `Installer` contract — read-only image vs runtime-owned data root,
  per-user default with no standing elevation, idempotent registrations + repair, non-destructive
  uninstall, **offline-capable core first run** (§6); the closed `PlatformIntegrationKind` set —
  ApplicationEntry/FileAssociation/ProtocolHandler/Notification/Tray/Autostart (off by
  default)/UninstallRegistration/window mechanics/environment reconstruction — ownership-recorded,
  reconciled, reversed on uninstall (§7); **native-messaging host** registration —
  write-on-first-use, extension-identity-bound, repair-aware; the browser extension separately
  published (§8) — completing 36's `NativeMessaging` transport; **the `SidecarInventory`** —
  `BundledBinary`/`RuntimeAsset` + the closed `BundlingStrategy` set (Eager only what every launch
  requires; LazyDownload/InstallOnDemand hash-verified before placement/load; SeparatelyPublished)
  (§9); **the `BuiltinBundle` finalized** — the signed item manifest covering every ship-with item
  (capability declarations, kind catalogues, surface contracts, default settings/profiles, ship-with
  plugins/themes, eval suites + golden fixtures, seed files); first-run registration through each
  owning layer's path in built-in-first order; install-plus-override + tombstone-aware re-seed;
  manifest mismatch = tamper, the item not registered as trusted (§10); the first-paint-cache
  concrete mechanism (§10.3, closing P19's partial); **the update pipeline** — `UpdateChannelKind`
  (one subscription at a time), signed-manifest check (flagged-cadence setting),
  **network-offered-downgrade rejection**, dual verification before staging, the `StagedUpdate`
  record, **pre-stable recovery checks** (substrate schema integrity, settings loadability,
  core-service startability, eager-binary presence, ship-with validity) gating last-known-good, the
  minimum-version gate preserving read/export/recovery access, `ATLAS_DISABLE_UPDATER` +
  package-manager suppression, updates opt-in default-off (§11); the `PlatformCrashHandler` —
  captures when the app loop is gone; the raw capsule restricted local staging, egress-eligible only
  after 22 redaction + 41 consent (§12); elevated-helper distribution — InstallOnDemand, mechanics
  from P17 (§13); `packaging.*` capabilities — install of the app itself is the Installer's, never
  an in-app capability (§14). OS notarization/Authenticode remain the declared funded-future
  extension of the existing signing scheme (§5.2) — wired as configuration, never a replacement.
- **File 42 — §18**: update relaunch — graceful shutdown → relaunch into the staged version →
  startup self-checks → record new last-known-good OR roll back (composing with 20 §12.3).

## 3. Prerequisites

P21 — the crash-capsule consent boundary. P18 — the native-messaging consumer + ship-with plugin
seeding path. P19 — the first-paint cache + ship-with themes. P17 — the elevated helper to
distribute. P0/P4 — the signing/identity scheme from P0 and the signed-bundle seam from P4; their
identities and verification contracts remain compatible while this phase completes the full delivery
pipeline.

## 4. Lanes

(a) Installers + platform integrations; (b) the BuiltinBundle closure + sidecar inventory; (c) the
update pipeline + 42 §18 relaunch; (d) crash handler + native-messaging host. Parallel after the
release-manifest/trust identity semantics are confirmed compatible with the P0 root; per-platform
work branches behind one packaging contract.

## 5. Build plan

1. **Installers**: per-platform bundles honoring the image/data-root split; install/uninstall hooks;
   uninstall preserves user data by default; idempotent repair.
2. **Platform integrations**: ownership records (kind/platform identity/artifact identity/
   registration path/payload hash); reconciliation; protocol-handler deep links resolve to typed
   `NavigationTarget`s — consequential actions enter the normal rails, never execute from OS
   payloads.
3. **BuiltinBundle closure**: inventory every ship-with item accumulated across P5–P21 into the
   signed manifest; first-run registration order = built-in-first (05 §16.1 / boot step 8); drift
   detection (image vs manifest) wired into the release pipeline.
4. **Sidecar inventory**: every helper binary/runtime asset (browser backend, analytical engine,
   language runtimes, the elevated helper, grounding models) as inventory entries with content
   hashes + compatibility metadata; lazy strategies hash-verify before first load; superseded
   payloads cleaned by state, not age.
5. **Update pipeline**: channel subscription; check → manifest signature → version comparison
   (network downgrade rejected) → artifact download + dual verification → stage → signal the
   runtime; 42 §18 relaunch; pre-stable checks gate last-known-good; the rollback path; delta
   delivery as an optimization (result still hash-verified).
6. **Crash handler**: registration at install/first-run; capsule → restricted staging → next-startup
   recovery (42 §13) + pre-stable-check input; consent-gated egress only.
7. **Native-messaging host**: per-platform manifest placement; extension-identity binding;
   update/repair reconciliation (a stale manifest pointing at a moved binary is surfaced, not used).

## 6. Test obligations & acceptance evidence

- **Update integrity** (§5.2/§18): an unsigned/bad-signature package is rejected, recorded, never
  staged; key rotation only via a transition record signed by an already-trusted key; a
  network-offered downgrade rejected absent explicit user-initiated rollback; only a complete
  verified `StagedUpdate` signals readiness.
- **The update E2E**: stage → relaunch → pre-stable checks pass → new last-known-good; a seeded
  failure (bad migration) → automatic rollback to last-known-good (composing with the P2 recovery
  hierarchy) — the full pipeline in CI against a local update server.
- The read-only-image/data-root boundary — the installer never writes substrate/lock/vault/durable
  data (§6.2); **offline first run** — a packaged release boots with no network (§6.2); the
  minimum-version gate preserves read/export/recovery access, never an unexplained lockout (§11.3).
- Integration idempotence/reversal — no orphaned/duplicate/stale registrations across
  install→update→uninstall (§7.3); autostart never default-on; deep-link payloads never execute
  directly.
- BuiltinBundle: manifest verification before trust; **tombstone-aware re-seed** — a user-removed
  item stays removed across updates; profile re-seed never overrides explicit user values (§10.2);
  golden encoding tests pin artifact/manifest/provenance/item-manifest/staged-update hash encodings
  (§16.2, extending the P0/P1 goldens).
- **Shipped-localization release admission** (43 §4.3): a candidate whose embedded shipped catalogue
  fails generated-artifact drift, completeness, or the product-language check is not release-eligible
  — a seeded missing key and a seeded terminology violation each fail the gate; the checks run with
  the copy-override layer disabled, and neither a user override nor an imported catalogue is a
  release input.
- Sidecars: a partial/unverifiable download is discarded, never run or loaded; an
  incompatible/downgraded payload marked unavailable, never used opportunistically; a missing
  optional payload degrades typed, never crashes (§9.3–9.5).
- Native-messaging: only the published extension identity connects; stale manifests surfaced +
  repaired (§8.2). Crash capsule: never egresses without redaction + consent (§12.2).
- **No silent delivery action**: every update applied/rolled back, recovery-check failure, payload
  download, integration registration/removal, host/helper install records a typed fact (§18).
- **Closed-set pinning**: `PlatformIntegrationKind`, `BundlingStrategy`, `UpdateChannelKind`, the
  pre-stable check list, the `StagedUpdate` record shape.
- Conformance matrix gains: 43 + 42 §18 anchors; the P0/P4/P19 packaging stub rows close.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: the `BuiltinBundle` item manifest (generated from the owning layers'
  registrations — drift-checked against the image); the `SidecarInventory`; shared types for
  `StagedUpdate`/`PlatformIntegration` ownership records; the release pipeline definitions.
- **Docs**: the installer + image/data-root doc; the platform-integration ownership doc; the update
  pipeline + rollback doc; the BuiltinBundle + ship-with doc; the crash-handler flow doc; the
  funded-future signing extension note.
- **CI/local commands**: `release` (the full pipeline), `verify-update` (local update-server
  harness); the update-integrity, downgrade-rejection, offline-first-run, integration-idempotence,
  bundle-drift, and sidecar-verification suites as named CI jobs; the fresh-machine matrix job.

## 8. Exit criteria

- [ ] The fresh-machine matrix (3 OSes): install → offline first run → onboarding (profile pick
      seeding plugins/themes/settings through the owning layers) → real work → update → rollback
      drill → uninstall (data preserved) — scripted and green.
- [ ] The BuiltinBundle manifest covers 100% of ship-with content; drift detection green.
- [ ] Crash → capsule → recovery → consent-gated report flow proven.
- [ ] M0–M3 still green.

## 9. Locked in this phase

- **The `StagedUpdate` record + the update handoff contract to 42**; the pre-stable recovery-check
  list (changing it changes rollback semantics).
- **The `PlatformIntegrationKind` + `BundlingStrategy` + `UpdateChannelKind` closed sets**; the
  sidecar-inventory entry contract; the `BuiltinBundle` item-manifest schema.
- Native-messaging manifest placement + identity binding; the device-local install-state set (never
  syncs — distribution is not portability).
- The funded-future boundary: OS notarization/Authenticode and store distribution extend the
  existing signing scheme, never replace it.
