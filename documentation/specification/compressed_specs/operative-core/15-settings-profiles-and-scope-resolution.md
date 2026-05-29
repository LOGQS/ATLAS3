# Settings, Profiles, and Scope Resolution

## 1. Chosen Model {settings.chosen-model}
Every setting MUST be declared by a `SettingDefinition`, resolved through one source stack, read/written through one settings service.
No subsystem MUST read settings storage directly, parse the TOML overlay directly, store settings in browser local storage, invent per-subsystem/per-surface config files, or create a parallel hierarchy.
Four concepts: `SettingDefinition`, `SettingValue`, `ProfileLayer`, `SettingsOverlay`.
The service MUST answer "why is this active?" for every resolved value.

## 2. Boundaries with Adjacent Layers {settings.boundaries-with-adjacent-layers}
### 2.1 Core Invariants {settings.core-invariants}
Settings MUST NOT be replaceable by hardcoded branches.
Progressive presentation MUST NOT be a stored scalar.

### 2.2 Capabilities, Policy, and Tool Surfaces {settings.capabilities-policy-surfaces}
Settings registration MUST be infrastructure, not a capability invocation.
Settings capabilities exposed to users/agents MUST pass through Files 04-06.
Routing+context policies MUST read settings snapshots and MUST NOT implement their own setting cascade.

### 2.3 Storage, Sync, Security, and UI {settings.storage-sync-security-ui}
Credential storage + cryptography MUST belong to the security spec.

## 3. `SettingDefinition` {settings.setting-definition}
### 3.1 Definition {settings.setting-definition-definition}
A typed registered declaration of one configurable value; NOT a stored value, UI control, capability, profile, or storage row schema.

### 3.2 Required Fields {settings.required-fields}
`key`, `owner_subsystem_id`, `source`, `definition_version`, `value_type`, `value_semantics`, `default_policy`, `category_key`, `label_key`, `description_key`, `constraint`, `allowed_scopes`, `mutability`, `agent_exposure`, `agent_rendering`, `locality`, `sensitivity`.
`source` variants: `Core`, `Plugin { plugin_id }`, `UserExtension { extension_id }`, `ImportedBundle { bundle_id }`.

### 3.3 Optional Fields {settings.optional-fields}
`deprecated`, `depends_on`, `tags`, `display_hints`, `extension_fields`.
There MUST be no canonical field for a progressive disclosure level.

### 3.4 Registration and Collision Rules {settings.registration-collision-rules}
Keys MUST be globally unique among active definitions.
Registration MUST fail when: a different owner registers the same key; the same owner registers an incompatible definition version; the key is outside the owner's namespace without an explicit extension grant; default policy/constraints/value semantics/locality are invalid; a plugin or imported bundle attempts to replace a core definition.
Unloading a plugin/extension MUST NOT delete user values by default; orphaned values MUST remain inspectable, exportable, removable, reclaimable.

## 4. Types, Semantics, and Constraints {settings.types-semantics-constraints}
### 4.1 `SettingType` {settings.setting-type}
Closed canonical primitives: `Bool`, `Int`, `Float`, `String`, `Choice { options }`, `Json`.
`Json` MUST carry a schema when structure affects behavior/policy/sync/UI rendering.

### 4.2 `ValueSemantics` {settings.value-semantics}
Initial canonical: `Plain`, `Path`, `Duration`, `ByteSize`, `TokenBudget`, `ModelRef`, `ProviderRef`, `CapabilityRef`, `SubsystemRef`, `PolicyTemplateRef`, `ProfileRef`, `LanguageTag`, `KeyboardShortcut`, `ColorToken`, `SecretRef`.
For `SecretRef` the settings service MUST NEVER return resolved secret material to agent/logs/events/sync/export/TOML/ordinary UI value display.

### 4.3 `DefaultPolicy` {settings.default-policy}
`Literal(value)`, `ProfileOnly`, `NoDefaultRequiredConfiguration`, `RegistryDerived { registry, selector }`, `PlatformDerived { source }`.
When `ProfileOnly` and no layer provides a value, resolution MUST return `NoDefaultAvailable` and MUST NOT substitute null/zero/empty-string/any meaningless sentinel.

### 4.4 `SettingConstraint` {settings.setting-constraint}
Declarative, serializable, inspectable, replayable: `MinValue`, `MaxValue`, `Range`, `MaxLength`, `Pattern`, `OneOf`, `JsonSchema`, `RegistryMember { registry }`, `DynamicOptions { provider_capability }`, `ResourcePath { root_policy }`, `UnitRange { unit, min, max }`.
No closure-backed/handler-private/prose-only constraint is valid; correctness/policy/sync/UI-affecting rules MUST be a typed constraint or a registered validator capability.

## 5. Scopes, Profile Contexts, and Overlays {settings.scopes-profile-contexts-overlays}
### 5.1 Durable Scopes {settings.durable-scopes}
`SettingScope`: `Global`, `Workspace { workspace_id }`, `Conversation { conversation_id }`.
`run`, `task`, `intent_thread`, `capability_call`, `automation`, `policy_rule`, `profile` MUST NOT be durable setting scopes.

### 5.2 Profile Contexts {settings.profile-contexts}
A profile context MUST behave like a local account for resolution; it MUST NOT be an authentication account, security principal, permission boundary, backend autonomy control, interaction shape, or execution mode.

### 5.3 Transient Overlays {settings.transient-overlays}
A `SettingsOverlay` MUST be a non-durable resolution input for one invocation/run/automation/evaluation/tool call, recorded with the operation, not stored as a durable row unless the user explicitly saves it.

## 6. Source-Stack Resolution {settings.source-stack-resolution}
### 6.1 Algorithm {settings.resolution-algorithm}
For a key+scope context, the service MUST walk the deterministic source stack and return the first valid hit:
1. Invocation overlay values
2. Explicit `Conversation` value
3. Explicit `Workspace` value
4. Explicit `Global` value
5. Enabled local explicit overlay value (TOML)
6. Active profile layers in resolved order
7. Definition default policy
Every candidate MUST be validated against the active definition before it can win; invalid values MUST be skipped with typed diagnostics unless the invalidity must stop execution.
An explicit global row MUST shadow the TOML overlay for that key.

### 6.2 Resolution Metadata {settings.resolution-metadata}
Every resolved value MUST carry: `resolved_from`, `winning_source_ref`, `shadowed_sources`, `active_profile_context`, `active_profile_layers`, `definition_ref`, `validation_diagnostics`, `provided_by_overlay`, `shadowed_by_explicit_row`, `locality`, `sensitivity`, `redaction_state`.

### 6.3 Determinism and Caching {settings.determinism-caching}
Resolution MUST be deterministic for the same inputs.
Caches MUST be allowed only as projections, invalidated by typed change events.
Time-based polling MUST NOT be a correctness mechanism.

## 7. Profiles {settings.profiles}
### 7.1 Definition {settings.profile-definition}
Each included key MUST reference a registered `SettingDefinition`.

### 7.2 Shape {settings.profile-shape}
A profile MUST carry: `profile_id`, `display_name_key`, `description_key`, `source` (`Builtin`, `Plugin { plugin_id }`, `UserDefined`, `ImportedBundle { bundle_id }`), `version`, `settings_values`, `activation_scope`, `composition_order`, `tags`, `trust/source_approval_state`.

### 7.3 Activation and Composition {settings.activation-composition}
Activation MUST record profile-layer metadata and MUST NOT copy values into explicit rows.
Explicit rows + stronger explicit layers MUST always win over profile layers.
Plugin profile updates MUST require source-approval review before active.

### 7.4 Boundary {settings.profile-boundary}
Profiles MUST NOT grant permission, mutate capability contracts, create execution modes, or define interaction shapes.

## 8. Agent Exposure {settings.agent-exposure}
### 8.1 Exposure Classes {settings.exposure-classes}
`agent_exposure`: `Hidden`, `OnRequest`, `InModelRequest`.

### 8.2 Rendering Classes {settings.rendering-classes}
`agent_rendering`: `FullValue`, `RedactedValue`, `SummaryOnly`, `PolicyFactOnly`, `NeverInline`.
`InModelRequest` MUST NOT mean raw insertion by default.

### 8.3 Write Boundary {settings.write-boundary}
The agent MUST NOT write silently and MUST NOT write/reset/enumerate/infer `Hidden` settings.
Policy approval MUST NOT override `Hidden`.

## 9. Local TOML Overlay {settings.local-toml-overlay}
The TOML overlay MUST be read-only from Atlas's side, local to the device, excluded from sync as a file, validated against registered definitions, unable to store secrets, and one input to the same source stack.
No time interval/polling cadence MUST be a correctness condition.
Invalid overlay keys/values MUST produce typed diagnostics and MUST NOT prevent valid entries loading.

## 10. Secret Boundary {settings.secret-boundary}
Secret material MUST NEVER appear in settings values/TOML/sync payloads/exports/logs/agent context/ordinary events/ordinary UI value display.
Secret references MUST be redaction-aware + source-attributed.
Resolving a secret reference MUST require an authorized backend path owned by the security/credentials layer.
Secret rotation MUST emit a typed event.

## 11. Definition Evolution and Stored Value Normalization {settings.definition-evolution-stored-value-normalization}
The system MUST support forward evolution via typed operations: rename key; deprecate key; coerce value shape; substitute removed choice; remove key; mark owner unavailable.
Invalid stored values MUST NOT be silently deleted; they MUST become inactive for normal resolution, produce typed diagnostics, and remain inspectable + removable.

## 12. Bootstrap Boundary {settings.bootstrap-boundary}
Bootstrap config MUST NOT be a runtime settings source and MUST NOT override registered settings after startup.

## 13. Settings Over Constants {settings.settings-over-constants}
Intended product variation MUST belong in settings.
Settings MUST NOT be used for: schema invariants; protocol constants; canonical enum membership; security floors that must not be user-lowered; test-only knobs; implementation internals with no meaningful product control.

## 14. Events and Snapshots {settings.events-snapshots}
### 14.1 Change Events {settings.change-events}
Successful changes MUST emit redaction-aware events identifying key, scope/overlay/profile source affected, actor/source, previous + new source class, redacted representations when allowed, sensitivity + redaction state, definition version, affected profile/scope context.
Events MUST NOT leak secret material or hidden values to unauthorized consumers.

### 14.2 Snapshots {settings.snapshots}
Effective settings snapshots MUST capture resolved values or redacted placeholders, source metadata, active profile context + layers, overlay participation, definition versions, locality/sync policy, and validation diagnostics that affected resolution.

### 14.3 Subscriptions {settings.subscriptions}
The service MUST expose subscription mechanisms; subscribers MUST react to typed events and MUST NOT poll.

## 15. Required Operations {settings.required-operations}
Operation families REQUIRED for: resolving one setting; resolving with metadata; enumerating authorized definitions+values; writing an explicit scoped value; resetting an explicit scoped value; registering+unregistering definition sources; inspecting definitions/ownership/lifecycle/resolution metadata; activating/deactivating/ordering profile layers; loading+reloading local overlay; producing agent-visible projections; producing redaction-aware event payloads + effective snapshots.

## 16. Settings Capabilities {settings.settings-capabilities}
Canonical capability surface: `settings.read`, `settings.list`, `settings.inspect`, `settings.write`, `settings.reset`, `settings.reload_overlay`.
Settings capabilities MUST touch `setting` resources, NOT `env` resources.
Writes + resets MUST pass through validation before commit and policy before execution.

## 17. Logical Persistence {settings.logical-persistence}
MUST durably preserve: explicit scoped values; active profile contexts + profile-layer order; user-defined profiles; imported profile metadata; definition source/version references; orphaned values for unavailable owners; local overlay enablement/source metadata; redaction-safe audit metadata; user management actions.
The user MUST be able to inspect/manage/export/clean up settings-owned durable state.

## 18. Locality, Sync, and Export {settings.locality-sync-export}
Every definition MUST declare locality: `Syncable`, `WorkspaceLocal`, `DeviceLocal`, `NeverSync`, `SecretReferenceOnly`, `ExportOptIn`.
Sync MUST NOT blindly sync all settings rows.
Exports MUST preserve provenance + redaction state; imports MUST go through source approval, validation, collision handling, owner lifecycle rules.

## 19. Settings for the Settings System {settings.settings-for-settings-system}
The settings subsystem MAY declare normal `SettingDefinition`s for its own behavior; overlay path discovery MUST remain infrastructure/bootstrap.

## 20. Explicit Rejections {settings.explicit-rejections}
- browser local/session storage as a settings store
- per-subsystem/per-surface config files as live settings sources
- environment variables as runtime settings overrides
- profiles as backend autonomy controls / interaction shapes / execution modes
- profile activation that silently copies defaults into explicit rows
- progressive disclosure as a canonical stored level
- agent access to `Hidden` settings by listing/error inference/search/model-request rendering/write proposal
- raw secret material in settings/TOML/sync/export/logs/events/snapshots/agent context
- settings capabilities modeled as environment-variable access
- time-based polling for settings correctness
- closure-backed constraints or handler-private validation
- monolithic registration of all settings
- hidden hardcoded branches where product variation belongs in settings
- pretending migration/adaptation code is needed for nonexistent persisted state
- physical storage schema embedded in this spec
- syncing all settings without locality metadata
- treating TOML as a locked authority over explicit user rows
- unkeyed model/provider-dependent settings values

## 21. Consequences for Later Specs {settings.consequences-for-later-specs}
- Subsystem settings sections MUST declare `SettingDefinition`s; no parallel stores or cascades.
- Capability specs MUST consume `setting` as a resource class.
- Policy specs MUST consume settings as inputs but MUST NOT own settings resolution.
- Tool-surface/routing/context/memory/retrieval/automation/provider specs MUST consume effective snapshots + profile-layer resolution.
- Storage specs MUST preserve logical state from §17.
- Sync specs MUST consume locality metadata instead of syncing all settings blindly.
- UI specs MUST render settings management from metadata and MUST NOT rely on a canonical progressive-disclosure scalar.
- Evaluation + replay specs MUST record effective settings snapshots including redaction-safe overlay/profile/default source metadata.
- Security specs MUST own secret storage internals + secret-reference resolution.
- Plugin + extension specs MUST preserve registration, collision, source-approval, orphaned-value rules.
