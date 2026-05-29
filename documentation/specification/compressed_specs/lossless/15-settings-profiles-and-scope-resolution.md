> Lossless render of canonical/15-settings-profiles-and-scope-resolution.md — original 30399 chars

# Settings, Profiles, and Scope Resolution

## Status
Canonical.

## Scope
Defines: `SettingDefinition` (typed declaration of one configurable value); canonical setting value types, value semantics, declarative constraints; durable setting scopes + non-durable resolution overlays; profile contexts + profile layers; deterministic source-stack resolution; agent exposure + redaction rules; setting-definition registration/ownership/lifecycle; local TOML overlay boundary; settings/secret boundary; settings schema evolution + stored-value normalization; settings events/snapshots/capability behavior; logical persistence contract.

Does not define: capability declaration fields / capability-call pipeline (Files 05, 04); policy evaluation/approvals/leases/source approval (File 06); tool-surface composition (File 07); block schema/artifact lifecycle/evidence/version graph/ledger row format (Files 08-11); retrieval indexes/context assembly/memory management/model-provider routing (Files 12-14 + later provider specs); settings-panel UI layout, storage table schema, sync transport, file locations, bootstrap variable names, credential storage internals, encryption mechanics (later UI/storage/infrastructure/sync/security specs).

## Source Resolution
One settings substrate. Every user-configurable product variation (UI, model, routing policy, context policy, tool-surface override, budget, approval posture, shortcut, profile preference, memory policy, retrieval option, plugin/extension option) resolves through the same `SettingsService`. Resolved: settings typed, constrained, scoped, source-attributed, agent-exposure-controlled, reactive, inspectable. Durable setting scopes intentionally small: `Global`, `Workspace`, `Conversation`. Profiles are named local setup contexts (like local accounts for config), NOT authentication identities, security principals, autonomy modes, interaction shapes, or execution architectures. Profiles contribute ordered profile layers; don't silently write rows just because selected. Runtime-specific variation uses explicit invocation overlays, not fake durable scopes. TOML is an optional local explicit layer, not a second settings system. Secrets live outside settings (may store secret references, never secret material). Settings define intended product variation, not a dumping ground for protocol invariants/schema constants/hidden implementation branches.

## 1. Chosen Model `settings.chosen-model`
Every setting declared by a `SettingDefinition`, resolved through one source stack, read/written through one settings service. No subsystem reads settings storage directly, parses TOML overlay directly, stores settings in browser local storage, invents per-subsystem/per-surface config files, or creates a parallel hierarchy. Four concepts:
- `SettingDefinition` — registered contract for a key
- `SettingValue` — explicit stored value at an allowed durable scope
- `ProfileLayer` — ordered set of default recommendations active for a profile context
- `SettingsOverlay` — non-durable invocation-time override recorded with the run/automation/evaluation/tool call that used it

Service answers "why is this active?" for every resolved value: winning source, shadowed sources, active profile layers, local overlay participation, definition version, sensitivity/redaction state, validation/availability diagnostics.

## 2. Boundaries with Adjacent Layers `settings.boundaries-with-adjacent-layers`
### 2.1 Core Invariants
File 01 defines settings as scoped, reactive, policy-aware, progressively presentable, agent-exposure-controlled, not replaceable by hardcoded branches. Progressive presentation is a product+UI principle, not a stored scalar; substrate provides metadata, search, categories, dependencies, provenance, inspection data so UI specs present simple defaults + deeper controls without making the principle a backend variable.

### 2.2 Capabilities, Policy, and Tool Surfaces
Settings registration is infrastructure, not a capability invocation; settings capabilities exposed to users/agents are normal capabilities passing through Files 04-06. Policy configuration is settings, policy evaluation is File 06; tool-surface customization is settings, surface composition is File 07; routing+context policies read settings snapshots, don't implement own setting cascade.

### 2.3 Storage, Sync, Security, and UI
This file defines logical durability + resolution behavior. Physical tables, indexes, sync transport, import/export bundles, storage quotas, visualization, cleanup UI belong to storage/sync/UI specs. Credential storage + cryptography belong to security spec.

## 3. `SettingDefinition` `settings.setting-definition`
### 3.1 Definition
Typed registered declaration of one configurable value; contract enforced on reads/writes/validation/resolution/exposure/inspection/evolution. NOT a stored value, UI control, capability, profile, or storage row schema.

### 3.2 Required Fields:
- `key` — dotted, namespaced, lowercase identifier; registered spelling preserved for display; lookup case-insensitive
- `owner_subsystem_id` — registered owner
- `source` — `Core`, `Plugin { plugin_id }`, `UserExtension { extension_id }`, or `ImportedBundle { bundle_id }`
- `definition_version` — version of this definition contract
- `value_type` — one canonical primitive type (§4.1)
- `value_semantics` — optional semantic meaning consumed by validation/UI/policy/sync/agent rendering
- `default_policy` — how setting resolves when no stronger source provides a value
- `category_key` — stable namespaced grouping key for search+UI organization
- `label_key` and `description_key` — i18n keys
- `constraint` — optional declarative constraint set
- `allowed_scopes` — durable scopes where explicit values may be stored
- `mutability` — user/system mutability contract
- `agent_exposure` — agent visibility class
- `agent_rendering` — authorized representation when visible to agent
- `locality` — sync/export/device-local policy
- `sensitivity` — sensitivity class for values/events/snapshots/exports

### 3.3 Optional Fields:
- `deprecated` — successor key + removal guidance
- `depends_on` — declarative UI dependency hints (don't affect resolution)
- `tags` — typed tags for search+filtering
- `display_hints` — non-semantic hints for future UI specs
- `extension_fields` — typed owner-registered metadata that cannot alter canonical field meaning

No canonical field for progressive disclosure level; UI specs choose how much to show by default using categories, tags, search, dependencies, risk, complexity, profile context, surface-specific presentation rules.

### 3.4 Registration and Collision Rules
Keys globally unique among active definitions. Registration fails when: different owner registers same key; same owner registers incompatible definition version for same key; key outside owner's namespace without explicit extension grant; default policy/constraints/value semantics/locality invalid; plugin or imported bundle attempts to replace a core definition. Unloading a plugin/extension doesn't delete user values by default; values whose owning definition is unavailable become orphaned — hidden from normal panels, inspectable in advanced management surfaces, exportable, removable by user, reclaimable if owner returns with compatible definition.

## 4. Types, Semantics, and Constraints `settings.types-semantics-constraints`
### 4.1 `SettingType` — closed canonical primitives:
`Bool`, `Int`, `Float`, `String`, `Choice { options }`, `Json`. `Choice` options static or registry-backed. `Json` must carry a schema when structure affects behavior/policy/sync/UI rendering.

### 4.2 `ValueSemantics` — primitive type is storage shape, semantics describe meaning; set extensible by canonical spec change or registered extension where safe. Initial canonical:
`Plain`, `Path`, `Duration`, `ByteSize`, `TokenBudget`, `ModelRef`, `ProviderRef`, `CapabilityRef`, `SubsystemRef`, `PolicyTemplateRef`, `ProfileRef`, `LanguageTag`, `KeyboardShortcut`, `ColorToken`, `SecretRef`. `SecretRef` = stored value is a reference to a secret not the secret; settings service never returns resolved secret material to agent/logs/events/sync/export/TOML/ordinary UI value display.

### 4.3 `DefaultPolicy` — declarative; may be:
- `Literal(value)` — static fallback
- `ProfileOnly` — no fallback outside an active profile layer or explicit value
- `NoDefaultRequiredConfiguration` — user/system configuration required before use
- `RegistryDerived { registry, selector }` — derived from registered descriptor (enabled model/provider capabilities)
- `PlatformDerived { source }` — derived from approved runtime facts (locale, OS capability) without becoming a live env-variable override

When `ProfileOnly` + no active profile layer provides a value, resolution returns `NoDefaultAvailable { key, requires: ProfileOrExplicitConfiguration }`; consumers treat as configuration-required; UI surfaces it as requiring configuration; service must not substitute null/zero/empty string/another meaningless sentinel.

### 4.4 `SettingConstraint` — declarative, serializable, inspectable, replayable:
`MinValue`, `MaxValue`, `Range`, `MaxLength`, `Pattern`, `OneOf`, `JsonSchema`, `RegistryMember { registry }`, `DynamicOptions { provider_capability }`, `ResourcePath { root_policy }`, `UnitRange { unit, min, max }`. No closure-backed/handler-private/prose-only constraint valid; correctness/policy/sync/UI-affecting rules must be a typed constraint or a registered validator capability declared by the owning subsystem.

## 5. Scopes, Profile Contexts, and Overlays `settings.scopes-profile-contexts-overlays`
### 5.1 Durable Scopes — `SettingScope` values:
- `Global` — installation-wide
- `Workspace { workspace_id }` — workspace-specific
- `Conversation { conversation_id }` — conversation-specific

Only durable scopes. `run`,`task`,`intent_thread`,`capability_call`,`automation`,`policy_rule`,`profile` are NOT durable setting scopes.

### 5.2 Profile Contexts
A profile context = selected local setup/persona for the same installation; behaves like a local account for resolution (selects active profile layers, explicit user preferences, layout defaults, tool-surface preferences, model preferences, other defaults). NOT an authentication account, security principal, permission boundary, backend autonomy control, interaction shape, or execution mode. Influences settings by activating profile layers + selecting which explicit values are considered part of the active setup where the storage spec supports profile-partitioned user preference state; doesn't change the capability/policy model by itself.

### 5.3 Transient Overlays
`SettingsOverlay` = non-durable resolution input for one invocation/run/automation execution/evaluation/tool call; recorded with the operation that used it; not stored as durable setting row unless user explicitly saves it. Correct home for run-specific/automation-specific/test-harness/per-call config; prevent fake conversation-scope rows for background work not naturally conversation-owned.

## 6. Source-Stack Resolution `settings.source-stack-resolution`
### 6.1 Algorithm — for a key+scope context, walk deterministic source stack, return first valid hit:
1. Invocation overlay values for current operation
2. Explicit `Conversation` value (when context has a conversation + definition allows)
3. Explicit `Workspace` value (when context has a workspace + definition allows)
4. Explicit `Global` value
5. Enabled local explicit overlay value (e.g. TOML overlay)
6. Active profile layers, in resolved order for active profile context
7. Definition default policy

Every candidate validated against active definition before it can win; invalid values skipped with typed diagnostics unless invalidity itself must stop execution. An explicit global row shadows the TOML overlay for that key; to restore TOML authority, user removes the explicit row via `settings.reset(key, Global)` or settings UI (deliberate: TOML provides portable defaults, explicit rows provide intentional overrides regardless of source).

### 6.2 Resolution Metadata — every resolved value carries:
`resolved_from`, `winning_source_ref`, `shadowed_sources`, `active_profile_context`, `active_profile_layers`, `definition_ref`, `validation_diagnostics`, `provided_by_overlay`, `shadowed_by_explicit_row`, `locality`, `sensitivity`, `redaction_state`. Powers inspection/audit/replay/debugging/"why is this active?" UI.

### 6.3 Determinism and Caching
Resolution deterministic for the same setting definitions, explicit values, enabled overlays, active profile layers, invocation overlays, scope context. Caches allowed only as projections over those inputs, invalidated by typed change events / overlay reload / definition registration changes / profile activation changes / owner lifecycle changes. Time-based polling is not a correctness mechanism.

## 7. Profiles `settings.profiles`
### 7.1 Definition
A `Profile` = named composable settings-default layer or group of layers; lets different local setups use different defaults in the same app without changing underlying runtime/policy/data model. May include defaults for settings, view preferences, tool-surface preferences, model preferences, policy-template selections, context policies, routing preferences, plugin-provided options; each included key must reference a registered `SettingDefinition`.

### 7.2 Shape — a profile carries:
`profile_id`, `display_name_key`, `description_key`, `source` (`Builtin`, `Plugin { plugin_id }`, `UserDefined`, `ImportedBundle { bundle_id }`), `version`, `settings_values`, `activation_scope` metadata, `composition_order`, `tags`, `trust/source_approval_state`. Shipped profile catalogue not canonical; system must support built-in/user-defined/plugin-provided/imported profiles; exact product bundles belong to distribution+UI specs.

### 7.3 Activation and Composition
Activating records active profile-layer metadata; doesn't copy values into explicit setting rows; explicit rows + stronger explicit layers always win over profile layers. Multiple profile layers may be active; composition order explicit+inspectable; layer conflicts resolved by order unless definition declares only one profile-provided value may be active; conflict diagnostics inspectable. Built-in profile updates (new Atlas versions) take effect on next resolution for settings not provided by explicit scoped row / stronger explicit local layer (uncustomized values get improved defaults automatically). Plugin profile updates require source-approval review before active (a plugin cannot silently change resolved defaults without acceptance). To freeze a profile's resolved values against future updates, UI can save them as explicit scoped rows (explicit rows precede all profile layers).

### 7.4 Boundary
Profiles are settings-layer inputs; don't grant permission, mutate capability contracts, create execution modes, or define interaction shapes; can select policy templates + tool-surface preferences, but Files 06 and 07 still evaluate those.

## 8. Agent Exposure `settings.agent-exposure`
### 8.1 Exposure Classes — `agent_exposure`:
- `Hidden` — agent cannot discover key/value through settings capabilities, listings, errors, search, model-request assembly
- `OnRequest` — agent may request authorized representation via `settings.read` or `settings.inspect`
- `InModelRequest` — context assembly may include authorized representation in the model request

### 8.2 Rendering Classes — `agent_rendering` (what representation is allowed):
`FullValue`, `RedactedValue`, `SummaryOnly`, `PolicyFactOnly`, `NeverInline`. `InModelRequest` never means raw insertion by default; context assembly renders settings as attributed assembly parts with correct authority class + redaction state.

### 8.3 Write Boundary
Agent may propose settings changes through canonical capability surface; may not write silently; may not write/reset/enumerate/infer `Hidden` settings. Policy approval does not override `Hidden` (hidden = outside agent-visible surface).

## 9. Local TOML Overlay `settings.local-toml-overlay`
Optional local explicit layer for power users wanting file-backed config: read-only from Atlas's side; local to device; excluded from sync as a file; validated against registered definitions; unable to store secrets; one input to same source stack. File locations, bootstrap discovery, platform path rules belong to infrastructure; spec doesn't hardcode a path or env-variable name. Overlay reload explicit or file-watch/event-driven; no time interval/polling cadence is a correctness condition. Invalid overlay keys/values produce typed diagnostics + don't prevent valid entries loading.

## 10. Secret Boundary `settings.secret-boundary`
Settings + secrets separate. Settings may store `SecretRef` values; vault stores secret material. Settings/TOML/sync enforcement of cross-cutting backend secret boundary [`secret.backend-boundary`]. Required: secret material never appears in settings values/TOML/sync payloads/exports/logs/agent context/ordinary events/ordinary UI value display; secret references redaction-aware + source-attributed; resolving a secret reference requires authorized backend path owned by security/credentials layer; secret rotation emits a typed event consumable by dependent services. Vault storage/keyring integration/encryption/fallback mechanics/vault API shape belong to security spec.

## 11. Definition Evolution and Stored Value Normalization `settings.definition-evolution-stored-value-normalization`
Definitions evolve; file requires safe evolution behavior, not migration machinery for a nonexistent current user base. Must support forward evolution via typed operations: rename key; deprecate key; coerce value shape; substitute removed choice; remove key; mark owner unavailable. Storage decides how applied evolutions recorded. Invalid stored values not silently deleted — become inactive for normal resolution, produce typed diagnostics, remain user-inspectable + removable unless policy requires stronger cleanup. Adding a new setting / new choice / profile layer / wider constraint-compatible definition is NOT a stored-value migration.

## 12. Bootstrap Boundary `settings.bootstrap-boundary`
Bootstrap config read before settings service exists; may locate app home, primary storage, local overlay, logging baseline, other startup-only infrastructure. NOT a runtime settings source; doesn't override `ui.theme`, model preferences, policy settings, other registered settings after startup. Exact bootstrap variable names, file locations, discovery order belong to infrastructure.

## 13. Settings Over Constants `settings.settings-over-constants`
Intended product variation belongs in settings. A value should be a setting when meaningful for users/workspaces/conversations/profiles/policies/devices/plugins/extensions to vary it. NOT for: schema invariants; protocol constants; canonical enum membership; security floors that must not be user-lowered; test-only knobs; implementation internals with no meaningful product control. If a value affects user-visible behavior/safety posture/cost/privacy/performance/automation/model behavior/cross-device behavior, evaluate as a setting. Best overall behavior remains the default policy.

## 14. Events and Snapshots `settings.events-snapshots`
### 14.1 Change Events — successful changes emit redaction-aware setting events identifying:
key; scope or overlay/profile source affected; actor/source; previous + new source class; redacted previous + new representations when allowed; sensitivity + redaction state; definition version; affected profile context or scope context. Events must not leak secret material or hidden values to unauthorized consumers.

### 14.2 Snapshots — effective settings snapshots (runs, routes, evaluations, replay) must capture:
resolved values or redacted placeholders; source metadata; active profile context + layers; overlay participation; definition versions; locality/sync policy; validation diagnostics that affected resolution. TOML file itself remains per-device + unsynced, but an operation depending on a TOML-provided non-secret value must record the effective resolved value or a redaction-safe placeholder in its snapshot when replay/audit requires.

### 14.3 Subscriptions
Settings service exposes subscription mechanisms for key-level/category-level/owner-level/profile-context changes; subscribers react to typed events; don't poll.

## 15. Required Operations `settings.required-operations`
Operation families for: resolving one setting; resolving one setting with metadata; enumerating authorized definitions+values; writing an explicit scoped value; resetting an explicit scoped value; registering+unregistering definition sources; inspecting definitions/ownership/lifecycle/resolution metadata; activating/deactivating/ordering profile layers; loading+reloading local overlay; producing agent-visible projections; producing redaction-aware event payloads + effective snapshots. No Rust-style generic method signatures, receiver types, IPC shapes, DB queries, or frontend hooks (those belong to implementation+infrastructure).

## 16. Settings Capabilities `settings.settings-capabilities` — canonical capability surface:
- `settings.read` — returns authorized resolved value or typed denial
- `settings.list` — returns authorized definitions+values by owner/category/scope/profile context/search query
- `settings.inspect` — returns resolution metadata, source metadata, definition metadata, redaction state, diagnostics
- `settings.write` — proposes explicit scoped value change
- `settings.reset` — proposes removal of explicit scoped value
- `settings.reload_overlay` — reloads local overlay

Behavioral requirements; exact capability declarations/permission tiers/preview payloads/confirmation strings/policy decisions belong to Files 05+06. Settings capabilities touch `setting` resources, NOT `env` resources; resource expression must identify key/key prefix/category/owner/scope/profile context affected; writes+resets pass through validation before commit + policy before execution.

## 17. Logical Persistence `settings.logical-persistence` — must durably preserve:
explicit scoped values; active profile contexts + profile-layer order; user-defined profiles; imported profile metadata; definition source/version references; orphaned values for unavailable owners; local overlay enablement/source metadata; redaction-safe audit metadata; user management actions (reset, cleanup, import, export, owner removal). Computed projections: resolved values, cache entries, authorized agent-visible views, "why active" explanations, settings-management summaries. Physical tables/indexes/timestamps/storage accounting/sync representation/cleanup UX/visualizations belong to storage/sync/UI specs. User must be able to inspect/manage/export/clean up settings-owned durable state through later management surfaces.

## 18. Locality, Sync, and Export `settings.locality-sync-export` — every definition declares locality:
`Syncable`, `WorkspaceLocal`, `DeviceLocal`, `NeverSync`, `SecretReferenceOnly`, `ExportOptIn`. Sync specs consume this metadata; must not blindly sync all settings rows; device-local values, local paths, machine capabilities, local model availability, overlay files, secret references require different treatment from ordinary user preferences. Exports must preserve provenance + redaction state; importing from another source must go through source approval, validation, collision handling, owner lifecycle rules.

## 19. Settings for the Settings System `settings.settings-for-settings-system`
Settings subsystem may declare settings for its own behavior (whether local overlay enabled, whether settings-resolution metadata shown by default, import/export preferences, management-surface visibility, cleanup behavior). Normal `SettingDefinition`s; exact keys + default policies not canonical here. Overlay path discovery remains infrastructure/bootstrap, not an ordinary runtime setting unless a later infrastructure spec deliberately exposes it after boot.

## 20. Explicit Rejections `settings.explicit-rejections` — wrong for this layer:
- browser local/session storage as a settings store
- per-subsystem/per-surface config files as live settings sources
- environment variables as runtime settings overrides
- profiles implemented as backend autonomy controls / interaction shapes / execution modes
- profile activation that silently copies defaults into explicit setting rows
- progressive disclosure implemented as a canonical stored level
- agent access to `Hidden` settings by listing/error inference/search/model-request rendering/write proposal
- raw secret material in settings/TOML/sync/export/logs/events/snapshots/agent context
- settings capabilities modeled as environment-variable access
- time-based polling for settings correctness
- closure-backed constraints or handler-private validation for setting correctness
- monolithic registration of all settings
- hidden hardcoded branches where intended product variation belongs in settings
- pretending migration/adaptation code is needed for nonexistent persisted state
- physical storage schema embedded in this settings spec
- syncing all settings without locality metadata
- treating TOML as a locked authority over explicit user rows
- unkeyed model/provider-dependent settings values

## 21. Consequences for Later Specs `settings.consequences-for-later-specs`
- subsystem settings sections declare `SettingDefinition`s; no parallel stores or cascades
- capability specs consume `setting` as a resource class for settings capabilities + policy checks
- policy specs consume settings as inputs but don't own settings resolution
- tool-surface, routing, context, memory, retrieval, automation, provider specs consume effective settings snapshots + profile-layer resolution
- storage specs preserve logical state from §17 + decide physical schema
- sync specs consume locality metadata instead of syncing all settings blindly
- UI specs render settings management from metadata, source attribution, search, profile context, validation diagnostics, redaction state, ownership lifecycle; don't rely on a canonical progressive-disclosure scalar
- evaluation + replay specs record effective settings snapshots including redaction-safe overlay/profile/default source metadata
- security specs own secret storage internals + secret-reference resolution
- plugin + extension specs own install/uninstall UX but must preserve registration, collision, source-approval, orphaned-value rules in this file
