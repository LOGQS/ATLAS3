# Phase 4 — Runtime Skeleton & Settings (M0: First Light)

## 1. Goal & why now

The system becomes a **running, installable application**: the File 42 runtime boots the §11.3 graph
(steps 1–9 + 15), the SettingsService resolves deterministically, a typed-IPC bridge connects a
minimal window, and one user gesture round-trips UI → service layer → block commit in SQLite → event
back to UI — surviving restart with deterministic reconstruction. The first signed installable
bundle seam re-anchors here from P0: M0's exit is *installing the signed bundle* on all 3 OSes. The
full installer, update, sidecar, crash-handler, and platform-integration pipeline remains P22-owned.
From this phase onward, every phase ends with a booting app. This is milestone **M0 (first light)**.

## 2. Canonical scope & deferrals

- **File 15 — complete core**: `SettingDefinition` registration (§3); closed `SettingType` +
  `ValueSemantics` + `DefaultPolicy` (incl. `NoDefaultAvailable`) + declarative `SettingConstraint`
  (§4); durable scopes Global/Workspace/Conversation ONLY + transient `SettingsOverlay` (§5); the
  deterministic 7-step source-stack resolution + "why is this active?" metadata (§6); profiles +
  layers (§7); agent-exposure/rendering classes (§8 — `Hidden` enforced locally; `InModelRequest`
  rendering → **P6** with File 13); TOML overlay (§9); secret boundary via `SecretRef` (§10, forms
  from P2); definition evolution (§11); bootstrap boundary (§12); logical persistence over P2 (§17);
  locality classes declared (§18 — enforced → **P20**).
- **File 42 — core**: `BootstrapConfig` read-once (§14); single-instance acquisition +
  owner-identity verification (§4.4, lock file from P2); async-execution substrate + concurrency
  caps + no-detached-spawn (§5); `ServiceGraph` static wiring (§9) + headless/CLI parity (§9.4);
  transports `InProcessBus` + `FrontendBridge` incl. the three-state-class bridge contract +
  optimistic-mutation envelope (§10); **boot graph steps 1–9 and 15** (§11.3); graceful shutdown +
  admission classes (§12); the global intervention cancellation token (§15). Deferred:
  workers/queues/timers (§6–§8 → **P14**, with the first real workers), sidecars/multi-process
  (§4 → **P15+**), crash-recovery completeness (→ **P6** orphan rules), remediation (§16 → **P21**),
  update relaunch (§18 → **P22**).
- **File 37 — thin slice only**: the typed IPC contract (§16.2, compile-time type bridge) + one
  minimal window (message input + transcript rendered from `context_view`). The full shell → **P12**;
  this minimal surface is *real* — it is matured, never rebuilt.
- **File 41 — logging baseline only** (§4 via 42 boot step 3): structured tracing init,
  `ATLAS_LOG_LEVEL` bootstrap var, the redacting formatter from P2. Full observability → **P21**.
- **File 43 — installer re-anchor**: per-OS installable signed bundles (the P0 hash/signature scheme
  applied to real bundles); the per-platform installer-size budget asserted (seed value from the
  initial development profile, invariants doc §27; settings-tunable per File 43 §15 — never a
  hardcoded canonical number).

## 3. Prerequisites

P3 — the round trip commits a real block + ledger entry + version commit and renders from the real
`context_view`. The skeleton exercises the real spine, not a toy table.

## 4. Lanes

Four lanes: (a) SettingsService over P2; (b) runtime host — bootstrap, lock, boot graph, shutdown,
cancellation token; (c) typed IPC bridge + the minimal window (Rust and TS sides separable once the
IPC contract is fixed); (d) installer/signing job. Lanes (a) and (b) converge at boot step 9; (c)
lands after (b)'s bridge transport exists.

## 5. Build plan

1. **SettingsService**: definition registry (registration is infrastructure, pre-capability — 15
   §2.2); resolution over Global/Workspace/Conversation + profile layers + literal defaults + TOML
   overlay; resolution metadata from day one ("why is this active?" is core, not deferred); invalid
   values skipped with typed diagnostics, never deleted; settings-change events.
2. **Runtime host**: `BootstrapConfig` (data root, storage path, vault path, log level, overlay
   path, updater-disable, debug flag — read exactly once, never a runtime settings source); boot
   steps 1–9 in order with per-step failure behavior (storage/migration failure = typed stop;
   registration failure = record + continue); `AppStarted`/`AppShuttingDown`/`AppStopped` entries
   with settings + registry snapshot identities.
3. **ServiceGraph**: static typed wiring of settings/storage/ledger/bus/version services; **headless
   parity** — a CLI entry performs the same round trip with no UI (42 §9.4: no capability or service
   depends on a UI being present).
4. **Frontend bridge**: typed IPC (request-response + streaming channel); compile-time generated TS
   types (a backend contract change breaks the build); event subscription from the renderer; the
   optimistic-mutation envelope (confirmed/rejected/superseded; the shell never becomes a second
   source of truth).
5. **Walking-skeleton UI**: minimal window — text input commits a `MessageUser` block (block +
   ledger + `UserMessage` version commit), transcript renders from `context_view` (a projection, not
   state), a scripted echo streams as events then commits a `MessageAssistant` block at the boundary.
   Semantic tokens + i18n keys + no-browser-storage discipline from the first component.
6. **Shutdown + cancellation**: global token; cooperative drain; acknowledged-durable guarantee
   (42 §12.4).
7. **Installers**: wire the desktop bundler per OS; sign bundles with the P0 key; the M0 CI job
   installs, launches, round-trips, restarts, and verifies.

## 6. Test obligations & acceptance evidence

- **Boot determinism/idempotence** (42 §11.4): re-running startup over the same substrate produces
  the same steady state; the UI never opens against a half-migrated/unverified substrate.
- Settings: resolution determinism over frozen inputs (15 §6.1/§6.3); source-stack-order goldens
  (overlay → conversation → workspace → global → TOML → profile layers → default); explicit-global-
  row-shadows-TOML + reset restores TOML authority; `NoDefaultAvailable` never sentinel-substituted
  (§4.3); Hidden-leak guard across listings/errors/search (§8.3); registration collision guards
  (§3.4); caches invalidated by typed events, never polling.
- Single-instance: lock owner verified before reclaim; unverifiable ownership → typed failure, no
  racing (42 §4.4).
- Shutdown: forced shutdown loses no acknowledged durable fact and never reports clean completion of
  abandoned work (42 §12.4) — fault-injection, not timing.
- Bridge: optimistic-mutation rollback on rejection/supersession; Secret never crosses the bridge
  raw (sensitivity filtering); the compile-time type-bridge break test; envelope preservation across
  the transport.
- **Full-loop integration + restart**: the round trip runs green asserting a block in the pool, a
  version commit, the `context_view` projection, and the ledger entries; **restart reproduces the
  transcript exactly or surfaces a typed recovery gap** — the skeleton's headline guarantee.
- **UI-is-projection**: no durable/consequential UI state in browser storage; token + i18n greps
  active and non-vacuous from here.
- Headless parity: the CLI round trip produces identical durable records to the UI round trip.
- Conformance matrix gains: `settings.*` core, 42 boot/shutdown/bridge/cancellation anchors, the
  end-to-end round-trip family for the skeleton scope.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: the typed IPC bindings (Rust↔TS, break-the-build on drift); shared types
  for `SettingDefinition`/`SettingValue`/`ProfileLayer`/`SettingsOverlay` + resolution metadata;
  migrations for the settings/profile families.
- **Docs**: the skeleton walkthrough (the round trip + how to run it); the IPC-boundary doc; the
  settings source-stack reference + settings-over-constants guidance; the boot-graph doc; decision
  record: the minimal surface is the real shell, matured in P12, never thrown away.
- **CI/local commands**: `dev` (run the app); the M0 install-launch-roundtrip-restart job per OS;
  boot-idempotence + shutdown fault-injection suites; the no-browser-storage grep.

## 8. Exit criteria

- [ ] **M0**: green 3-OS CI job that installs the signed bundle, launches, performs the round trip,
      restarts, and finds the data. Installer within the seeded per-platform size budget.
- [ ] Boot idempotence + shutdown fault-injection suites green; headless CLI parity proven.
- [ ] Settings resolution goldens green; `settings.read/write/inspect/reset` usable from UI and CLI.

## 9. Locked in this phase

- **Boot-graph phase ordering** (42 §11.3) — the single runtime ordering authority every later phase
  composes into (step 8's registration order built-in→subsystem→plugin→MCP→API→user-defined is
  reserved now).
- **`SettingType` closed set; durable-scope set (Global/Workspace/Conversation only); source-stack
  ordering; the dotted key-namespacing rule** — every later spec's settings depend on these.
- **`BootstrapConfig` variable set** (42 §14) — bootstrap vars are never live-reloadable.
- **The typed-IPC wire contract + three state classes + optimistic-mutation outcomes** (42 §10.3,
  37 §16.2) — the renderer/backend boundary.
- Settings-over-constants becomes enforceable: from now on, any tunable hardcoded numeric is a review
  rejection (01 §7.9, 15 §13).
