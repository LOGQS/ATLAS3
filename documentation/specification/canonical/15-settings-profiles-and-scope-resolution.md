# Settings, Profiles, and Scope Resolution

## Status

Canonical.

## Scope

This file defines:

- `SettingDefinition` as the typed declaration of one configurable value
- the canonical setting value types, value semantics, and declarative constraints
- durable setting scopes and non-durable resolution overlays
- profile contexts and profile layers
- deterministic source-stack resolution
- agent exposure and redaction rules for settings
- setting-definition registration, ownership, and lifecycle
- the local TOML overlay boundary
- the settings/secret boundary
- settings schema evolution and stored-value normalization
- settings events, snapshots, and capability behavior
- the logical persistence contract for settings state

This file does not define:

- capability declaration fields or the capability-call pipeline - Files 05 and 04 own those
- policy evaluation, approvals, leases, or source approval - File 06 owns those
- tool-surface composition - File 07 owns that
- block schema, artifact lifecycle, evidence, version graph, or ledger row format - Files 08-11 own those
- retrieval indexes, context assembly, memory management, or model/provider routing - Files 12-14 and later provider specs own those
- settings-panel UI layout, storage table schema, sync transport, file locations, bootstrap variable names, credential storage internals, or encryption mechanics - later UI, storage, infrastructure, sync, and security specs own those

## Source Resolution

ATLAS3 has one settings substrate. Every user-configurable product variation - UI preference, model preference, routing policy, context policy, tool-surface override, budget, approval posture, shortcut, profile preference, memory policy, retrieval option, plugin option, and extension option - resolves through the same `SettingsService`.

The resolved design:

- Settings are typed, constrained, scoped, source-attributed, agent-exposure-controlled, reactive, and inspectable.
- Durable setting scopes are intentionally small: `Global`, `Workspace`, and `Conversation`.
- Profiles are named local setup contexts, similar to local accounts for configuration purposes. They are not authentication identities, security principals, autonomy modes, interaction shapes, or execution architectures.
- Profiles contribute ordered profile layers to resolution. They do not silently write setting rows just because they are selected.
- Runtime-specific variation uses explicit invocation overlays, not fake durable scopes.
- TOML is an optional local explicit layer, not a second settings system.
- Secrets live outside settings. Settings may store secret references, never secret material.
- Settings define intended product variation. They are not a dumping ground for protocol invariants, schema constants, or hidden implementation branches.

## 1. Chosen Model

Anchor: `settings.chosen-model`

Every setting is declared by a `SettingDefinition`, resolved through one source stack, and read or written through one settings service. No subsystem reads settings storage directly, parses the TOML overlay directly, stores settings in browser local storage, invents per-subsystem or per-surface config files, or creates a parallel settings hierarchy.

The model has four distinct concepts:

- `SettingDefinition` - the registered contract for a key
- `SettingValue` - an explicit stored value at an allowed durable scope
- `ProfileLayer` - an ordered set of default recommendations active for a profile context
- `SettingsOverlay` - a non-durable invocation-time override recorded with the run, automation, evaluation, or tool call that used it

The service answers "why is this active?" for every resolved value. The answer includes the winning source, shadowed sources, active profile layers, local overlay participation, definition version, sensitivity/redaction state, and any validation or availability diagnostics.

## 2. Boundaries with Adjacent Layers

Anchor: `settings.boundaries-with-adjacent-layers`

### 2.1 Core Invariants

File 01 defines the settings system as scoped, reactive, policy-aware, progressively presentable, agent-exposure-controlled, and not replaceable by hardcoded branches. This file specifies the substrate that fulfills those invariants.

Progressive presentation is a product and UI principle, not a stored scalar. Different surfaces may expose different depths and interaction shapes. The settings substrate provides metadata, search, categories, dependencies, provenance, and inspection data so UI specs can present simple defaults and deeper controls without turning the design principle into a backend variable.

### 2.2 Capabilities, Policy, and Tool Surfaces

Settings registration is infrastructure, not a capability invocation. The settings capabilities exposed to users and agents are normal capabilities and pass through Files 04-06.

Policy configuration is settings; policy evaluation is File 06. Tool-surface customization is settings; surface composition is File 07. Routing and context policies read settings snapshots; they do not implement their own setting cascade.

### 2.3 Storage, Sync, Security, and UI

This file defines logical durability and resolution behavior. Physical tables, indexes, sync transport, import/export bundles, storage quotas, visualization, and cleanup UI belong to storage/sync/UI specs. Credential storage and cryptography belong to the security spec.

## 3. `SettingDefinition`

Anchor: `settings.setting-definition`

### 3.1 Definition

A `SettingDefinition` is the typed, registered declaration of one configurable value. It is the contract enforced on reads, writes, validation, resolution, exposure, inspection, and evolution.

A definition is not:

- a stored value
- a UI control
- a capability
- a profile
- a storage row schema

### 3.2 Required Fields

Every `SettingDefinition` must carry:

- `key` - dotted, namespaced, lowercase identifier. The registered spelling is preserved for display; lookup is case-insensitive.
- `owner_subsystem_id` - registered owner of the setting.
- `source` - `Core`, `Plugin { plugin_id }`, `UserExtension { extension_id }`, or `ImportedBundle { bundle_id }`.
- `definition_version` - version of this definition contract.
- `value_type` - one canonical primitive type from section 4.1.
- `value_semantics` - semantic meaning consumed by validation, UI, policy, sync, or agent rendering; the field is always present and defaults to `Plain` (section 4.2) when no distinct semantics apply.
- `default_policy` - how the setting resolves when no stronger source provides a value.
- `category_key` - stable namespaced grouping key for search and UI organization.
- `label_key` and `description_key` - i18n keys.
- `constraint` - a declarative constraint set; the field is always present and may be empty when no constraints apply.
- `allowed_scopes` - durable scopes where explicit values may be stored.
- `mutability` - user/system mutability contract.
- `agent_exposure` - agent visibility class.
- `agent_rendering` - authorized representation when visible to the agent.
- `locality` - sync/export/device-local policy.
- `sensitivity` - sensitivity class for values, events, snapshots, and exports.

### 3.3 Optional Fields

Definitions may also carry:

- `deprecated` - successor key and removal guidance.
- `depends_on` - declarative UI dependency hints; these do not affect resolution.
- `tags` - typed tags for search and filtering.
- `display_hints` - non-semantic hints for the UI layer (File 37 and File 38).
- `extension_fields` - typed owner-registered metadata that cannot alter canonical field meaning.
- `profile_composition` - `Ordered` or `SingleActive`, governing how multiple active profile layers for this key combine during resolution (section 6.1); defaults to `Ordered`. `SingleActive` surfaces a typed conflict when more than one active profile layer provides a value, as described in section 7.3.

There is no canonical field for progressive disclosure level. UI specs may choose how much to show by default using categories, tags, search, dependencies, risk, complexity, profile context, and surface-specific presentation rules.

### 3.4 Registration and Collision Rules

Setting keys are globally unique among active definitions. Registration fails when:

- a different owner registers the same key
- the same owner registers an incompatible definition version for the same key
- the key is outside the owner's namespace without an explicit extension grant
- the default policy, constraints, value semantics, or locality are invalid
- a plugin or imported bundle attempts to replace a core definition

Unloading a plugin or extension does not delete user values by default. Values whose owning definition is unavailable become orphaned. Orphaned values are hidden from normal setting panels, inspectable in advanced management surfaces, exportable, removable by the user, and reclaimable if the owner returns with a compatible definition.

## 4. Types, Semantics, and Constraints

Anchor: `settings.types-semantics-constraints`

### 4.1 `SettingType`

The canonical primitive value types are closed:

- `Bool`
- `Int`
- `Float`
- `String`
- `Choice { options }`
- `Json`

`Choice` options may be static or registry-backed. `Json` must carry a schema when the structure affects behavior, policy, sync, or UI rendering.

### 4.2 `ValueSemantics`

Primitive type is storage shape; semantics describe meaning. The semantic set is extensible by canonical spec change or registered extension where safe. Initial canonical semantics include:

- `Plain`
- `Path`
- `Duration`
- `ByteSize`
- `TokenBudget`
- `ModelRef`
- `ProviderRef`
- `CapabilityRef`
- `SubsystemRef`
- `PolicyTemplateRef`
- `ProfileRef`
- `LanguageTag`
- `KeyboardShortcut`
- `ColorToken`
- `SecretRef`

`SecretRef` means the stored setting value is a reference to a secret, not the secret. The settings service never returns resolved secret material to the agent, logs, events, sync, export, TOML, or ordinary UI value display.

### 4.3 `DefaultPolicy`

`default_policy` is declarative. It may be:

- `Literal(value)` - static fallback.
- `ProfileOnly` - no fallback outside an active profile layer or explicit value.
- `NoDefaultRequiredConfiguration` - user/system configuration is required before use.
- `RegistryDerived { registry, selector }` - derived from a registered descriptor, such as enabled model or provider capabilities.
- `PlatformDerived { source }` - derived from approved runtime facts, such as locale or OS capability, without becoming a live environment-variable override.

When `default_policy` is `ProfileOnly` and no active profile layer provides a value, resolution returns `NoDefaultAvailable { key, requires: ProfileOrExplicitConfiguration }`. Consumers must treat this as a configuration-required state. The settings UI surfaces it as requiring configuration; the service must not substitute null, zero, empty string, or another meaningless sentinel.

### 4.4 `SettingConstraint`

Constraints are declarative, serializable, inspectable, and replayable. They include:

- `MinValue`
- `MaxValue`
- `Range`
- `MaxLength`
- `Pattern`
- `OneOf`
- `JsonSchema`
- `RegistryMember { registry }`
- `DynamicOptions { provider_capability }`
- `ResourcePath { root_policy }`
- `UnitRange { unit, min, max }`

No closure-backed, handler-private, or prose-only constraint is valid. If a validation rule affects correctness, policy, sync, or UI behavior, it must be represented as a typed constraint or by a registered validator capability declared by the owning subsystem.

## 5. Scopes, Profile Contexts, and Overlays

Anchor: `settings.scopes-profile-contexts-overlays`

### 5.1 Durable Scopes

Durable `SettingScope` values are:

- `Global` - installation-wide.
- `Workspace { workspace_id }` - workspace-specific.
- `Conversation { conversation_id }` - conversation-specific.

These are the only durable settings scopes. `run`, `task`, `intent_thread`, `capability_call`, `automation`, `policy_rule`, and `profile` are not durable setting scopes.

### 5.2 Profile Contexts

A profile context is the selected local setup/persona for the same installation. It behaves like a local account from a settings-resolution perspective: it selects active profile layers, explicit user preferences, layout defaults, tool-surface preferences, model preferences, and other defaults associated with that setup.

A profile context is not:

- an authentication account
- a security principal
- a permission boundary
- a backend autonomy control
- an interaction shape
- an execution mode

Profile contexts influence settings by activating profile layers and by selecting which explicit values are considered part of the active setup where the storage spec supports profile-partitioned user preference state. They do not change the capability or policy model by themselves.

### 5.3 Transient Overlays

`SettingsOverlay` is a non-durable resolution input for one invocation, run, automation execution, evaluation, or tool call. It is recorded with the operation that used it. It is not stored as a durable setting row unless the user explicitly saves it.

Transient overlays are the correct home for run-specific, automation-specific, test-harness, or per-call configuration. They prevent fake conversation-scope rows for background work that is not naturally conversation-owned.

## 6. Source-Stack Resolution

Anchor: `settings.source-stack-resolution`

### 6.1 Algorithm

For a key and scope context, the settings service walks a deterministic source stack and returns the first valid hit:

1. Invocation overlay values for the current operation.
2. Explicit `Conversation` value, when the context has a conversation and the definition allows it.
3. Explicit `Workspace` value, when the context has a workspace and the definition allows it.
4. Explicit `Global` value.
5. Enabled local explicit overlay value, such as the TOML overlay.
6. Active profile layers, in resolved order for the active profile context.
7. Definition default policy.

Every candidate source is validated against the active definition before it can win. Invalid values are skipped with typed diagnostics unless the invalidity itself must stop execution.

At step 6, the definition's `profile_composition` (section 3.3) governs how multiple active profile layers combine: the default `Ordered` takes the first profile layer that provides a valid value in resolved composition order, while `SingleActive` treats more than one active profile layer providing a value as a conflict surfaced through the resolution diagnostics rather than silently resolved by order, per the composition rule in section 7.3.

An explicit global row shadows the TOML overlay for that key. To restore TOML authority, the user removes the explicit row through `settings.reset(key, Global)` or the settings UI. This is deliberate: the TOML overlay provides portable defaults; explicit rows provide intentional overrides regardless of source.

### 6.2 Resolution Metadata

Every resolved value carries:

- `resolved_from`
- `winning_source_ref`
- `shadowed_sources`
- `active_profile_context`
- `active_profile_layers`
- `definition_ref`
- `validation_diagnostics`
- `provided_by_overlay`
- `shadowed_by_explicit_row`
- `locality`
- `sensitivity`
- `redaction_state`

This metadata powers inspection, audit, replay, debugging, and "why is this active?" UI.

### 6.3 Determinism and Caching

Resolution is deterministic for the same setting definitions, explicit values, enabled overlays, active profile layers, invocation overlays, and scope context. Caches are allowed only as projections over those inputs and are invalidated by typed change events, overlay reload, definition registration changes, profile activation changes, or owner lifecycle changes. Time-based polling is not a correctness mechanism.

## 7. Profiles

Anchor: `settings.profiles`

### 7.1 Definition

A `Profile` is a named, composable settings-default layer or group of layers. Profiles let different local setups use different defaults in the same app without changing the underlying runtime, policy, or data model.

A profile may include defaults for settings, view preferences, tool-surface preferences, model preferences, policy-template selections, context policies, routing preferences, and plugin-provided options. Each included key must reference a registered `SettingDefinition`.

### 7.2 Shape

A profile carries:

- `profile_id`
- `display_name_key`
- `description_key`
- `source` - `Builtin`, `Plugin { plugin_id }`, `UserDefined`, or `ImportedBundle { bundle_id }`
- `version`
- `settings_values`
- `activation_scope` metadata
- `composition_order`
- `tags`
- `trust/source_approval_state`

The exact shipped profile catalogue is not canonical. The system must support built-in, user-defined, plugin-provided, and imported profiles; exact product bundles belong to distribution and UI specs.

### 7.3 Activation and Composition

Activating a profile records active profile-layer metadata. It does not copy profile values into explicit setting rows. Explicit setting rows and stronger explicit layers always win over profile layers.

Multiple profile layers may be active. Composition order is explicit and inspectable. Layer conflicts are resolved by order unless the setting definition declares that only one profile-provided value may be active; conflict diagnostics are inspectable.

Built-in profile updates shipped with new Atlas versions take effect on next resolution for settings not provided by an explicit scoped row or stronger explicit local layer. Users who have not customized a value receive improved defaults automatically.

Plugin profile updates require source-approval review before the updated profile layer becomes active. A plugin cannot silently change resolved defaults without user acceptance.

If a user wants to freeze a profile's current resolved values against future updates, the settings UI can save those values as explicit scoped rows. Explicit rows take precedence over all profile layers.

### 7.4 Boundary

Profiles are settings-layer inputs. They do not grant permission, mutate capability contracts, create execution modes, or define interaction shapes. They can select policy templates and tool-surface preferences, but Files 06 and 07 still evaluate those systems.

## 8. Agent Exposure

Anchor: `settings.agent-exposure`

### 8.1 Exposure Classes

Every definition declares `agent_exposure`:

- `Hidden` - the agent cannot discover the key or value through settings capabilities, listings, errors, search, or model-request assembly.
- `OnRequest` - the agent may request an authorized representation through `settings.read` or `settings.inspect`.
- `InModelRequest` - context assembly may include an authorized representation in the model request.

### 8.2 Rendering Classes

Exposure determines whether the agent may see a setting. `agent_rendering` determines what representation is allowed:

- `FullValue`
- `RedactedValue`
- `SummaryOnly`
- `PolicyFactOnly`
- `NeverInline`

`InModelRequest` never means raw insertion by default. Context assembly renders settings as attributed assembly parts with the correct authority class and redaction state.

### 8.3 Write Boundary

The agent may propose settings changes through the canonical capability surface. It may not write settings silently. It may not write, reset, enumerate, or infer `Hidden` settings. Policy approval does not override `Hidden`; hidden means outside the agent-visible surface.

## 9. Local TOML Overlay

Anchor: `settings.local-toml-overlay`

The TOML overlay is an optional local explicit layer for power users who want file-backed configuration. It is:

- read-only from Atlas's side
- local to the device
- excluded from sync as a file
- validated against registered definitions
- unable to store secrets
- one input to the same source stack

File locations, bootstrap discovery, and platform path rules belong to infrastructure. The settings spec does not hardcode a path or environment-variable name.

Overlay reload is explicit or file-watch/event-driven. No time interval or polling cadence is a correctness condition. Invalid overlay keys or values produce typed diagnostics and do not prevent valid overlay entries from loading.

## 10. Secret Boundary

Anchor: `settings.secret-boundary`

Settings and secrets are separate concerns. Settings may store `SecretRef` values; the vault stores secret material. This is the settings/TOML/sync enforcement of the cross-cutting backend secret boundary (`secret.backend-boundary`, File 22 §4).

Required properties:

- secret material never appears in settings values, TOML, sync payloads, exports, logs, agent context, ordinary events, or ordinary UI value display
- secret references are redaction-aware and source-attributed
- resolving a secret reference requires an authorized backend path owned by the security/credentials layer
- secret rotation emits a typed event consumable by dependent services

Vault storage, keyring integration, encryption, fallback mechanics, and vault API shape belong to the security spec.

## 11. Definition Evolution and Stored Value Normalization

Anchor: `settings.definition-evolution-stored-value-normalization`

Settings definitions evolve. This file requires safe evolution behavior; it does not require migration machinery for a nonexistent current user base.

The settings system must support forward evolution of stored values through typed operations:

- rename key
- deprecate key
- coerce value shape
- substitute removed choice
- remove key
- mark owner unavailable

Storage decides how applied evolutions are recorded. Invalid stored values are not silently deleted. They become inactive for normal resolution, produce typed diagnostics, and remain user-inspectable and removable unless policy requires stronger cleanup.

Adding a new setting, adding a new choice, adding a profile layer, or adding a wider constraint-compatible definition is not a stored-value migration.

## 12. Bootstrap Boundary

Anchor: `settings.bootstrap-boundary`

Bootstrap configuration is read before the settings service exists. It may locate the app home, primary storage, local overlay, logging baseline, or other startup-only infrastructure.

Bootstrap configuration is not a runtime settings source. It does not override `ui.theme`, model preferences, policy settings, or other registered settings after startup. Exact bootstrap variable names, file locations, and discovery order belong to infrastructure.

## 13. Settings Over Constants

Anchor: `settings.settings-over-constants`

Intended product variation belongs in settings. A value should be a setting when it is meaningful for users, workspaces, conversations, profiles, policies, devices, plugins, or extensions to vary it.

Settings are not for:

- schema invariants
- protocol constants
- canonical enum membership
- security floors that must not be user-lowered
- test-only knobs
- implementation internals with no meaningful product control

If a value affects user-visible behavior, safety posture, cost, privacy, performance, automation, model behavior, or cross-device behavior, it should be evaluated as a setting. The best overall behavior remains the default policy.

## 14. Events and Snapshots

Anchor: `settings.events-snapshots`

### 14.1 Change Events

Successful changes emit redaction-aware setting events. A setting event must identify:

- key
- scope or overlay/profile source affected
- actor/source
- previous and new source class
- redacted previous and new representations when allowed
- sensitivity and redaction state
- definition version
- affected profile context or scope context

Events must not leak secret material or hidden values to unauthorized consumers.

A same-value re-write is a successful no-op, not a change: it emits no `SettingChanged`. It instead records the distinct `SettingWriteNoOp` diagnostic event (File 10 §4.1), carrying the same identification fields, which no subscription recomposes on. The event exists so a hidden repeat-writer — a polling or cycling defect re-applying an identical value — is visible in the event history rather than silent; a sustained stream of `SettingWriteNoOp` facts is that defect's signature.

### 14.2 Snapshots

Effective settings snapshots used by runs, routes, evaluations, and replay must capture:

- resolved values or redacted placeholders
- source metadata
- active profile context and layers
- overlay participation
- definition versions
- locality/sync policy
- validation diagnostics that affected resolution

The TOML file itself remains per-device and unsynced, but an operation that depended on a TOML-provided non-secret value must record the effective resolved value or a redaction-safe placeholder in its snapshot when replay or audit requires it.

### 14.3 Subscriptions

The settings service exposes subscription mechanisms for key-level, category-level, owner-level, and profile-context changes. Subscribers react to typed events. They do not poll.

## 15. Required Operations

Anchor: `settings.required-operations`

The settings service must provide operation families for:

- resolving one setting
- resolving one setting with metadata
- enumerating authorized definitions and values
- writing an explicit scoped value
- resetting an explicit scoped value
- registering and unregistering definition sources
- inspecting definitions, ownership, lifecycle, and resolution metadata
- activating, deactivating, and ordering profile layers
- loading and reloading the local overlay
- producing agent-visible projections
- producing redaction-aware event payloads and effective snapshots

This file does not require Rust-style generic method signatures, receiver types, IPC shapes, database queries, or frontend hooks. Those belong to implementation and infrastructure.

## 16. Settings Capabilities

Anchor: `settings.settings-capabilities`

The settings subsystem exposes a canonical capability surface:

- `settings.read` - returns an authorized resolved value or typed denial.
- `settings.list` - returns authorized definitions and values by owner, category, scope, profile context, or search query.
- `settings.inspect` - returns resolution metadata, source metadata, definition metadata, redaction state, and diagnostics.
- `settings.write` - proposes an explicit scoped value change.
- `settings.reset` - proposes removal of an explicit scoped value.
- `settings.reload_overlay` - reloads the local overlay.

These are behavioral requirements. Exact capability declarations, permission tiers, preview payloads, confirmation strings, and policy decisions belong to Files 05 and 06.

Settings capabilities touch `setting` resources, not `env` resources. The resource expression must identify the key, key prefix, category, owner, scope, or profile context affected. Settings writes and resets pass through validation before commit and through policy before execution.

## 17. Logical Persistence

Anchor: `settings.logical-persistence`

The settings substrate must durably preserve:

- explicit scoped values
- settings reset tombstones, each modeled as a causally-descendant unset/inherit revision of the value it clears rather than a physical row deletion (File 21 §6.3)
- active profile contexts and profile-layer order
- user-defined profiles
- imported profile metadata
- definition source/version references
- orphaned values for unavailable owners
- local overlay enablement/source metadata
- redaction-safe audit metadata
- user management actions such as reset, cleanup, import, export, and owner removal

Computed projections include resolved values, cache entries, authorized agent-visible views, "why active" explanations, and settings-management summaries.

Physical tables, indexes, timestamps, storage accounting, sync representation, cleanup UX, and visualizations belong to storage/sync/UI specs. The user must be able to inspect, manage, export, and clean up settings-owned durable state through later management surfaces.

## 18. Locality, Sync, and Export

Anchor: `settings.locality-sync-export`

Every definition declares locality:

- `Syncable`
- `WorkspaceLocal`
- `DeviceLocal`
- `NeverSync`
- `SecretReferenceOnly`
- `ExportOptIn`

Sync specs consume this metadata. They must not blindly sync all settings rows. Device-local values, local paths, machine capabilities, local model availability, overlay files, and secret references require different treatment from ordinary user preferences.

Exports must preserve provenance and redaction state. Importing settings from another source must go through source approval, validation, collision handling, and owner lifecycle rules.

## 19. Settings for the Settings System

Anchor: `settings.settings-for-settings-system`

The settings subsystem may declare settings for its own behavior, such as whether the local overlay is enabled, whether settings-resolution metadata is shown by default, import/export preferences, management-surface visibility, and cleanup behavior.

These self-settings are normal `SettingDefinition`s. Their exact keys and default policies are not canonical here. Overlay path discovery remains infrastructure/bootstrap, not an ordinary runtime setting unless a later infrastructure spec deliberately exposes it after boot.

## 20. Explicit Rejections

Anchor: `settings.explicit-rejections`

The following shapes are wrong for this layer:

- browser local storage or session storage as a settings store
- per-subsystem or per-surface config files as live settings sources
- environment variables as runtime settings overrides
- profiles implemented as backend autonomy controls, interaction shapes, or execution modes
- profile activation that silently copies defaults into explicit setting rows
- progressive disclosure implemented as a canonical stored level
- agent access to `Hidden` settings by listing, error inference, search, model-request rendering, or write proposal
- raw secret material in settings, TOML, sync, export, logs, events, snapshots, or agent context
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

## 21. Consequences for Later Specs

Anchor: `settings.consequences-for-later-specs`

Later specs must follow these rules:

- subsystem settings sections declare `SettingDefinition`s; they do not define parallel stores or cascades
- capability specs consume `setting` as a resource class for settings capabilities and policy checks
- policy specs consume settings as inputs but do not own settings resolution
- tool-surface, routing, context, memory, retrieval, automation, and provider specs consume effective settings snapshots and profile-layer resolution
- storage specs preserve logical state from section 17 and decide physical schema
- sync specs consume locality metadata instead of syncing all settings blindly
- UI specs render settings management from metadata, source attribution, search, profile context, validation diagnostics, redaction state, and ownership lifecycle; they do not rely on a canonical progressive-disclosure scalar
- evaluation and replay specs record effective settings snapshots, including redaction-safe overlay/profile/default source metadata
- security specs own secret storage internals and secret-reference resolution
- plugin and extension specs own install/uninstall UX but must preserve the registration, collision, source-approval, and orphaned-value rules in this file

## 22. Canonical Rule Anchors

Anchor: `settings.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `settings.chosen-model`, `settings.boundaries-with-adjacent-layers`, `settings.setting-definition`, `settings.types-semantics-constraints`, `settings.scopes-profile-contexts-overlays`, `settings.source-stack-resolution`, `settings.profiles`, `settings.agent-exposure`, `settings.local-toml-overlay`, `settings.secret-boundary`, `settings.definition-evolution-stored-value-normalization`, `settings.bootstrap-boundary`, `settings.settings-over-constants`, `settings.events-snapshots`, `settings.required-operations`, `settings.settings-capabilities`, `settings.logical-persistence`, `settings.locality-sync-export`, and `settings.settings-for-settings-system`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
