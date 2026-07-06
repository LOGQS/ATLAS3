# Phase 18 — Extensions & Integrations (Plugins, MCP, External APIs)

## 1. Goal & why now

The system opens outward: File 35's `Plugin` bundle layer (install/trust/lifecycle over the one
substrate) and File 36's `Connector` layer (MCP client + server roles, external HTTP APIs, the
webhook transport). Reusable extension is only safe after the core operation path, policy, surfaces,
runtime, security, and UI are mature — otherwise plugins and connectors would create parallel
capability/trigger/execution universes. The File 06 source-approval flow — typed shapes since P5 —
becomes fully real here: **nothing externally sourced becomes invocable without completed user
review**. Both layers are optional to core function by spec ("a deployment with no registry
configured still installs from local sources"; "service zero is fine") — and that optionality is a
tested property.

## 2. Canonical scope & deferrals

- **File 06 — §9 completion**: the source-approval flow — `SourceRegistrationProposal`, the user
  option set (accept defaults / customize per capability / customize per source / deny /
  `DeferSourcePolicy` / `CancelRegistration`), trust-mapping defaults — rendered through P12's
  dialog contract; gates plugin install and connector first-connect.
- **File 35 — complete core**: the `Plugin`/`PluginManifest`/`Contribution` model + the manifest
  validator — **envelope recomputation: an understated `PluginPermissionManifest` is rejected**
  (§3–§6); bundle-granularity trust/integrity over 22's `SourceIntegrityRecord` — content mismatch
  is a tamper signal that re-gates + downgrades (§7); execution backends — **Wasm
  default/recommended constrained backend** (not an inherent safety grant), Shell higher-tier (§8);
  the `PluginRegistry` + the contribution-attribution index (runtime-source vs bundle-ownership) +
  the dependency-impact projection (§9); the install/activate lifecycle —
  acquire→validate→review→stage→entry-module→commit with **rollback leaving no partial activation**;
  enable/disable/quarantine (a distinct safety state)/uninstall with orphaned-settings + tombstone
  discipline (§10); distribution — local/packaged first, registry discovery optional, **updates
  opt-in default-off**, ship-with per-profile plugins seeded idempotent + tombstone-aware at first
  run (§11); custom-tool promotion reusing 34 §11.4's forgery guard (§12); `plugin.*` capabilities
  (§13); plugin events (§14). Registration phase 3 (Plugin) of 05 §16.1 activates in boot step 8.
- **File 36 — complete core**: the `Connector` primitive + `ConnectorRegistry` + `ConnectorContract`
  (§3); **the MCP client role**: `mcp.<connector_slug>.<remote_tool_name>` capability identity +
  `McpProxy` backends + deterministic schema translation incl. `ToolAnnotations` mapping (data, not
  authority) + deferred loading opt-in (§4); sessions — connect → handshake → `tools/list` →
  register; spawn-on-demand; disconnect/reconnect **preserving identity** so saved
  automations/workflows/shortcuts survive; atomic removal via the attribution index (§5); transports
  — `Stdio` first (sandboxed subprocess, env-denylist), `Http`/`Sse`/`StreamableHttp`/`WebSocket`;
  `NativeMessaging` lands with **P22**'s host registration (§6); the `ConnectionState` machine +
  circuit breaker + descriptor cache — health from call outcomes + notifications, **no scheduled
  pings, no clock-polled reconnect** (§7); resource/prompt bridging (§8); **the MCP server role** —
  off by default; an external client is an `Invoker` passing the identical policy/approval/ledger
  path, never the user (§10); the `ExternalApi` connector — `api.<service>.<endpoint>` +
  `HttpEndpoint` backends + closed auth/body/pagination sets + OAuth user-delegated flow; definitions
  load **after the vault**; literal secrets where refs belong are refused (§11); **the webhook
  receiver** → File 33 `Webhook` triggers with auth/freshness/idempotency, bound to a 42-owned
  dynamically-allocated loopback listener brought up with connector loading, independent of the
  frontend IPC bridge; localhost default, remote bind explicit (§13); remote workflow node
  kinds + retrieval adapters (§14); `mcp.*`/`connector.*` capabilities — `mcp.search` mechanics
  discharge the P6-reserved id (§16). Connector definitions are device-local and never sync;
  configuring elsewhere is a fresh local configure-and-approve (§17).
- **File 42 — §9.3/§10.3/§6 completion**: the `DynamicServiceRegistry` (plugin-backed services, §9.3);
  connection pools + the idle reaper (§10.3); the Stdio-process crash reaper (§6); the webhook route
  registration.

## 3. Prerequisites

P8 — trust model, integrity records, egress, Wasm/Shell sandboxing, env-denylist. P14 — the webhook
trigger target. P17 — the six surfaces stable (full contribution-point coverage for plugin
contributions). P5 — the registry's runtime-mutation path. P12 — the source-approval dialogs.

## 4. Lanes

(a) The source-approval flow completion; (b) the plugin layer; (c) the MCP client + transports;
(d) the ExternalApi connector + OAuth; (e) webhooks + the server role. (a) first — (b) and (c) gate
on it; (b) ∥ (c)/(d); (e) after (c). May overlap P19's built-in customization work and P20.

## 5. Build plan

1. **Source approval**: the proposal flow + option set + trust-mapping defaults; envelope-diff
   recomputation reused by approval, refresh, and `mcp.refresh`.
2. **Plugin model**: manifest parse/validate (duplicate/namespace-violating ids, unresolved artifact
   refs, understated envelopes, undeclared-capability entry modules, missing required deps,
   private-substrate reach — all rejected); staged install; the entry module under Wasm;
   contributions registering through their **owning** registries (capabilities→05, settings→15,
   surfaces→25, rails→26, workflows→34, validators→39, suites→40, renderers/themes→37/38) under
   runtime-source + bundle ownership; atomic rollback.
3. **Plugin lifecycle**: enable/disable; quarantine (cancels in-flight via 04); uninstall with
   attribution-index cleanup + dependency-impact typed-confirmation + tombstones; update re-review
   on envelope expansion.
4. **Ship-with seeding**: BuiltinBundled plugins copied from the read-only image at first run —
   idempotent, tombstone-aware (a user-uninstalled ship-with plugin is never silently re-seeded);
   the P22 manifest-verification chain readied.
5. **MCP client**: Stdio spawn-on-demand (ManagedProcess, env-denylist); handshake → register as
   capabilities; reconnect identity; removal atomicity; deferred loading; `tool.borrow`-driven late
   schema fetch (07 §4.6).
6. **External APIs**: declarative definition load after vault; closed auth/body/pagination sets;
   OAuth state/callback validation.
7. **Webhooks**: receiver route; signature verification via vault refs; `fire_id` idempotency into
   P14; unauthenticated deliveries dropped, never fired.
8. **MCP server role**: default-off; the external-Invoker policy path; `atlas://` resource URIs;
   per-client allowlisted ReadOnly resources.

## 6. Test obligations & acceptance evidence

- **One plugin layer / one connector layer / no private architecture** (the central family): no
  parallel contribution registry, no private plugin runtime, no per-plane stores; every contribution
  is an ordinary registration indistinguishable from a built-in once registered, source/ownership
  only metadata; a plugin reaching for a private store/parallel registry/security-critical state
  cannot register — grep + the owning validators.
- 35: the manifest-validator rejection matrix (§4.5); **envelope recomputation** — understatement
  rejected; registering an effect outside the approved envelope is a typed failure; the envelope
  never pierces a `permission_floor`; envelope-expanding updates re-review (§6); integrity mismatch
  = tamper → re-gate + downgrade (§7.3); **activation-rollback atomicity** — a required-contribution
  failure leaves no partial activation (§10.1); promotion forgery guard (§12.4); per-call policy
  intact under bundle approval (§6.4); dependency-impact typed-confirmation, never silent break
  (§9.4); inline-secret pre-dispatch rejection (§8.3); **user-only lifecycle** — the agent suggests
  but never installs/enables/updates; nothing silent; sensor consent never satisfied by plugin
  approval (§11/§12); seeding idempotent + tombstone-aware (§11.4); uninstall orphans settings
  non-destructively + preserves produced data + retains a tombstone (§10.4).
- 36: **replay over recorded descriptors/invocations, never live connections** (§20) — a proposed
  invocation binds to the descriptor snapshot at proposal time; translation determinism (§4.3);
  **reconnect identity preservation** — saved automations/workflows/shortcuts survive (§5.3); Fatal
  never converted to Transient; retry waits killable with finite ceilings (§7.2); **the
  source-approval gate** — never invocable without completed review (§9.1); **the server-role
  tier-bypass guard** — a user-only capability via an external client resolves to denial, not an
  approval prompt (§10.3); OAuth state/callback mismatch rejected (§11.3); webhook
  auth/freshness/idempotency — duplicates map to one identity, never re-fired (§13.3); per-hop
  egress revalidation + credential audience confinement; irreversible-write/credential egress carry
  the `Denied`-floor typed-confirmation (§15.2); env-denylist on spawned servers (§15.3); literal
  secrets refused at load (§11.3); no scheduled pings (§7.5).
- Boot: the full 05 §16.1 registration order (built-in → subsystem → plugin → MCP → API →
  user-defined) now exercised end-to-end with restart determinism.
- **Optionality proven**: the system functions with zero plugins and zero connectors — a permanent
  CI assertion.
- **Closed-set pinning**: ContributionKind, install sources, plugin lifecycle states,
  ConnectorKind, McpTransportKind, ConnectionState, auth/body/pagination sets.
- Conformance matrix gains: 35/36 anchors + 06 §9; the P5 source-approval and P6 `mcp.search` stub
  rows close.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `PluginManifest`/`Contribution`/`PluginPermissionManifest`,
  `Connector`/`ConnectorContract`/`McpSession`/`ConnectionState`; migrations for the
  plugin-registry/connector/attribution families (device-local where the canon says so); recorded
  MCP/HTTP fixtures for deterministic connector tests.
- **Docs**: the plugin model + contribution-point taxonomy doc; the source-approval flow doc; the
  connector + MCP client/server docs; the ExternalApi authoring doc; the webhook transport doc;
  decision record: the first MCP transport realization.
- **CI/local commands**: the manifest-validation, rollback-atomicity, envelope-honesty,
  reconnect-identity, source-approval-gate, server-role-bypass, webhook-idempotency, and
  zero-extension-optionality suites as named CI jobs.

## 8. Exit criteria

- [ ] A third-party-style test plugin: install (review → approve) → contribute a capability + slash
      command + validator → use → update (envelope diff re-review) → quarantine → uninstall clean.
      All atomic, all audited.
- [ ] A real MCP server (Stdio): connect → review → tools registered → invoked through the full
      pipeline → disconnect/reconnect with identity preserved → removal clean.
- [ ] An ExternalApi call + a webhook-triggered automation fire end-to-end (recorded transport in
      CI).
- [ ] Zero-extension optionality asserted; M0–M3 still green.

## 9. Locked in this phase

- **`plugin_id` identity + the `ContributionKind` taxonomy + the attribution-index shape**
  (runtime-source vs bundle-ownership — wired into 05 §10.1's registered-entry fields).
- **The `PluginPermissionManifest` envelope + the envelope-diff change-set** (update re-review
  depends on it); install-source and lifecycle-state enums.
- **Connector identity schemes** — `connector_id` slug stability; the `mcp.<slug>.<tool>` and
  `api.<service>.<endpoint>` capability-id formats (renames = aliases or remove/add, never silent
  mutation).
- **The closed transport/auth/body/pagination sets**; descriptor-snapshot replay keying; the
  `ConnectorContract` field set; webhook `fire_id` derivation; the `atlas://` resource URI scheme.
- The optionality guarantees themselves — core function with zero plugins/connectors is a permanent,
  tested property.
