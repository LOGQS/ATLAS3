# Capability Contracts and Registry — Operative Core

## 1. Chosen Model {capability.chosen-model}
One Capability Registry; every operation MUST be declared as `Capability` and registered.
Three layered views: `CapabilityDeclaration`, `RegisteredCapability`, `CapabilityInvocation`.
No second registry; no per-subsystem bespoke list; no `actions` vs `tools` split.
`Action` interface superseded; `Action` MUST NOT be preserved as parallel registry/adapter layer/alias.

## 2. `Capability` {capability.capability}
### 2.2 Required Properties (Declaration)
Every `CapabilityDeclaration` MUST have: stable identity; typed `input_schema`; typed `output_schema`; typed error vocabulary; touched-resource declaration as machine-parseable expressions; permission-tier declaration; capability class declaration; execution-semantic metadata + per-field `classification_mode`; `replay_class`; validation path; declared source; backend descriptor; declared display metadata.
A declaration lacking any of these MUST be rejected at registration.

## 3. Capability Declaration — Field Set {capability.declaration}
Immutable for given `(id, version)`; updates MUST go through `version` increment.
Registry-state mutations MUST live on registered entry, never on declaration.
### 3.1 Identity Fields
`id`, `version`, `schema_version`, `aliases`
### 3.2 Display Fields {capability.display-fields}
Dynamic declarations (MCP/plugin/external API/user-defined) MUST always provide safe literal defaults.
`name`, `description`, `short_description`, `i18n_key`, `translations`, `family`, `tags`, `icon_key`, `default_shortcut`
Tags: `agent-invokable`, `voice-invokable`, `palette-invokable`, `destructive`, `experimental`
Display fields MUST NOT be hardcoded into surface logic.
### 3.3 Schema Fields
`input_schema`, `output_schema`, `error_vocabulary`
### 3.4 Touched-Resource Fields
`touched_resources`
### 3.5 Permission and Policy Fields {capability.permission-policy-fields}
`permission_tier` (`TierResolver::Static(Tier)` | `TierResolver::Dynamic(resolver_id)`), `permission_floor`, `capability_class`, `approval_template_id`, `data_sensitivity`
`capability_class`: `InternalAnalysis`, `ActionExternal`, `UserArtifact`, `Unknown`
`data_sensitivity`: `Public`, `Sensitive`, `Secret`
### 3.6 Execution-Semantic Fields {capability.execution-semantic-fields}
`concurrency` (`ConcurrencySafe`, `SelfParallel`, `Exclusive`); `reversibility_class` (`none`, `compensable`, `reversible`); `idempotent`; `preview_mode` (`none`, `dry_run`, `structural_preview`, `diff_preview`); `partial_output_meaningful`; `cooperative_stop_deadline_ms`; `sibling_abort_on_failure`; `resume_on_restart`; `terminates_sequence`; `replay_class`; `classification_mode` (`Deterministic` | `ModelMediated { policy_model_request_template_id }`)
### 3.7 Validation Fields
`input_validators`, `postconditions`, `stale_state_revalidation`
### 3.8 Sourcing Fields
`source`
### 3.9 Availability Fields {capability.availability-fields}
`availability_predicate`, `platforms`, `prerequisite_capabilities`
`platforms`: `windows`, `macos`, `linux`, `mobile`
### 3.10 Composition Fields {capability.composition-fields}
`dependent_capabilities`, `output_block_kinds`, `output_event_kinds`
### 3.11 Cost and Telemetry Fields
`cost_model`, `telemetry_schema`
### 3.12 Backend Descriptor {capability.backend-descriptor}
`backend`: `ServiceMethod { service_id, method_name }`, `Wasm { module_id, entry_point }`, `Shell { program, args, cwd, env_overlay }`, `McpProxy { server_id, remote_tool_name }`, `HttpEndpoint { url_template, method, auth_ref }`, `Closure { closure_id }`
Handlers MUST NOT be serialized into declarations.
Declarations using `Closure { ... }` MUST declare `replay_class: not_replayable`.
### 3.13 Boundary
Extensions MUST be additive; MUST NOT change meaning of named fields.

## 4. Schemas {capability.schemas}
### 4.1 `input_schema` {capability.input-schema}
Required: every input parameter named with declared type, default value where applicable, validation constraints, description; required params distinguished from optional; enums declared explicitly; aliases declared in schema metadata.
Inputs MUST be validated against `input_schema` before execution.
### 4.2 `output_schema`
Required: principal return shape declared exhaustively; polymorphic union every variant declared with discriminator; relationship between produced blocks + return value made explicit.
### 4.3 `error_vocabulary` {capability.error-vocabulary}
Each variant: stable kind identifier, declared structured fields, `recoverable`, `retryable`, message template.
In-band tool-result errors MUST conform to this vocabulary.
Errors escaping as `AppError` MUST map to declared variants + typed-error envelope.
MUST NOT emit ad-hoc error kinds; adding one requires registry update + versioning.

## 5. Permission-Tier Declaration {capability.permission-tier-declaration}
### 5.1 Tier Set
`Denied`, `ReadOnly`, `WorkspaceWrite`, `UserApproval`, `Unrestricted`; `typed-confirmation` variant of `UserApproval`
### 5.2 `TierResolver` {capability.tier-resolver}
`TierResolver::Static(Tier)` | `TierResolver::Dynamic(resolver_id)`
Resolver behavior MUST be deterministic given same arguments + world-model snapshot.
### 5.3 Tier Composition With Leases
Leases MUST NOT escalate above declared tier, MUST NOT bypass `Denied`, MUST NOT lift `typed-confirmation`.
### 5.4 `permission_floor` {capability.permission-floor}
Runtime tier = higher of resolved `permission_tier`, `permission_floor`, any narrower active scope-level override.

## 6. `touched_resources` {capability.touched-resources}
### 6.1 Required Shape
Each entry: `class`, `access` (`read`, `write`, `read_write`, `invoke`, `observe`, `none`), `expression`.
Prose-only declarations INVALID for any capability with `access: write` or `access: read_write`.
### 6.2 Canonical Resource Classes
`filesystem`, `network`, `process`, `env`, `credential`, `setting`, `model-call`, `browser-session`, `ui-element`, `sub-agent`, `scheduler`
### 6.3 Extension Resource Classes {capability.extension-resource-classes}
Registered via subsystem-extension capability; entry carries `extension_id`, scope grammar, containment predicate.
### 6.4 Resource Expressions {capability.resource-expressions}
Argument-bound expressions MUST reference `args.*` by name; expression MUST resolve to concrete resources.
### 6.5 Purpose
Expressions MUST be honest + complete.

## 7. Execution-Semantic Metadata {capability.execution-semantic-metadata}
### 7.2 `classification_mode` {capability.classification-mode}
Per-field `Deterministic` | `ModelMediated { policy_model_request_template_id }`; default `Deterministic`.
### 7.3 `replay_class` {capability.replay-class}
`deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable`
Closure-backed declarations MUST declare `replay_class: not_replayable`.
### 7.4 Boundary
Any change after registration MUST be a version bump + new declaration alongside old.

## 8. Validation and Postconditions {capability.validation-postconditions}
### 8.1 `input_validators` {capability.input-validators}
Validators run in declared order; return `valid`, `invalid_with_correction`, or `invalid`.
`invalid` without correction MUST halt dispatch + produce typed validation error in-band.
### 8.2 `postconditions`
Failing postcondition MUST produce typed postcondition-failure variant in `error_vocabulary`.
### 8.3 `stale_state_revalidation`
Typed `StateChangedSinceObservation`-class error variant MUST be returned when metadata mismatches current state.

## 9. Sourcing {capability.sourcing}
### 9.1 `CapabilitySource` {capability.capability-source}
`Builtin`, `Subsystem { subsystem_id }`, `Plugin { plugin_id, plugin_version }`, `McpServer { server_id, server_uuid, server_version }`, `Api { api_name, api_definition_path }`, `UserDefined { backend, scope }`
A capability MUST have exactly one source.
### 9.2 Trust and Source-Approval Flow {capability.trust-source-approval-flow}
Trust is registry state, not declaration field.
Entry holds `declared_trust_hint`, `registry_trust_override`, `effective_trust` (`System`, `Verified`, `Community`, `Unverified`, `User`).
Trust MUST NOT rewrite declared fields.
### 9.3 Sourcing Equivalence {capability.sourcing-equivalence}
Capabilities from every source enter the same registry through the same contract; source distinction surfaces only as metadata; one registry, no parallel per-source tool lists.
### 9.4 Platform Conditioning
A declaration whose `platforms` omits current OS MUST still register, carrying `availability_status: unavailable_platform`.
A capability registered `Available` on one OS MUST NOT throw `PlatformUnsupported` on an unsupported OS.

## 10. `RegisteredCapability` — Registry State {capability.registered-capability}
### 10.1 Definition
`declaration`, `registered_at`, `enabled`, `availability_status`, `resolved_backend_binding`, `source_instance`, `trust_state`, `lifecycle_state`, `active_aliases`, `diagnostics`, `collision_state`
`availability_status`: `Available`, `UnavailablePlatform`, `UnavailableHandler`, `UnavailablePrerequisite`, `Disabled`, `Shadowed`
`lifecycle_state`: `Loading`, `Active`, `Updating`, `Disabled`, `Unregistering`
`collision_state`: `Active`, `Shadowed { shadowed_by }`, `Shadowing { shadows }`
`resolved_backend_binding` MUST never be serialized into declaration.
### 10.2 Mutation Rules
`(id, version)` MUST be immutable for entry's lifetime; new version MUST produce new entry. Mutations MUST emit registry events.
### 10.4 Backend Binding Lifecycle {capability.backend-binding-lifecycle}
`Closure` MUST declare `replay_class: not_replayable`.
`HttpEndpoint` auth MUST come from credential vault by reference; never inline secrets.

## 11. `CapabilityInvocation` — Per-Call Record {capability.invocation-record}
Per-call resolved facts: resolved `(id, version)`; invocation arguments; resolved permission tier; resolved touched resources; resolved model-mediated classifications; selected backend binding instance; policy decision; proposal id, ledger entry id, event sequence; call outcome.
Replay MUST read `(declaration_version, resolved_backend_binding_id_at_time)` from record, not from current registry state.

## 12. Capability Registry {capability.capability-registry}
### 12.1 Operations
MUST support: `register`, `unregister`, `update`, `enable`, `disable`, `get`, `lookup_alias`, `list`, `available`, `find_by_shortcut`, `subscribe`, `resolve_for_invocation`.
Registry MUST NOT own an `execute` primitive.
### 12.2 Events {capability.events}
`CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityUpdated`, `CapabilityEnabledChanged`, `CapabilityRegistryStateChanged`
### 12.3 Registration Mechanics
Registration: validate declaration; check id collision; resolve backend binding; normalize schema_version; compute registry state; insert entry; emit `CapabilityRegistered`; update derived projections.
Failure errors: `IdentifierCollision`, `InvalidDeclaration`, `HandlerUnresolved`, `SchemaTooNew`, `SourceConflict`, `UnparseableResourceExpression`.
Failed registrations MUST leave registry unchanged.

## 13. Identity, Namespacing, Versioning {capability.identity-namespacing-versioning}
### 13.1 `id` {capability.id}
Built-in/subsystem `<family>.<operation>`; plugin `plugin.<plugin_id>.<operation>`; MCP `mcp.<server_id>.<remote_tool_name>`; API `api.<service_name>.<endpoint_id>`; user-defined `custom.<scope>.<tool_id>`.
Ids MUST NOT contain whitespace, slashes, or separator chars (`.`, `:`, `__`); registry MUST reject non-conforming.
### 13.2 `family` {capability.family}
One family per capability.
### 13.4 `version` {capability.version}
Ledger MUST record `(id, version)`.
### 13.5 `schema_version`
Registry MUST validate current `schema_version`, MUST reject unknown.
### 13.6 Boundary
Wholesale id reuse for unrelated operations FORBIDDEN.

## 14. Override Resolution and Conflicts {capability.override-resolution-conflicts}
### 14.1 Identifier Collisions
Two declarations MUST NOT be active entry under same `id` simultaneously; collision rejected by default (`IdentifierCollision`).
Source declarations MUST NOT be mutated by collision resolution.
### 14.2 Source Priority
`UserDefined` > `Plugin` > `Subsystem` > `Builtin`; applies only on explicit user opt-in.
### 14.3 Layered Resources
Skills, instruction packs, fragments, workflow templates are NOT capabilities.

## 15. Discovery {capability.discovery}
### 15.1 Lookup Surface
All lookups MUST honor `availability_status` + `enabled`.
### 15.2 `availability_predicate` {capability.availability-predicate}
Parts: `requires`, `blocked_by`.
A capability whose availability rule can't be typed MUST extend the predicate vocabulary through registered availability checks; ad-hoc procedural availability rejected.
### 15.3 `prerequisite_capabilities` {capability.prerequisite-capabilities}
Each names capability id + `scope` (`run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`).
Violation MUST return typed `PrerequisiteUnsatisfied` error in-band.
### 15.4 Runtime Discovery Capabilities
`tool.search`, `tool.borrow`, `mcp.search`, `extensions.search_registry` MUST be first-class registered capabilities; declare `ReadOnly`.

## 16. Lifecycle {capability.lifecycle}
### 16.1 Startup Registration {capability.startup-registration}
Phases: Built-in, Subsystem, Plugin, MCP-sourced, External-API, User-defined.
Startup MUST NOT abort on single registration failure.
### 16.2 Runtime Mutation {capability.runtime-mutation}
Registration is a capability call flowing through the call-pipeline + policy layer; agent MUST NOT self-promote registration without user approval.
`tools.register_custom` MUST require `UserApproval`.
### 16.3 `enabled`
Registry state, not declaration field.
### 16.4 Update Mechanics
Major updates MUST invalidate existing leases.
### 16.5 Unregistration
New calls MUST be refused with typed `CapabilityUnregistered` error.
Unregistering a built-in FORBIDDEN; built-in may only be disabled.
### 16.6 Restart Behavior
Restart sequence MUST be deterministic: same declarations in same priority order → same registry state.

## 17. Composition Primitives at the Contract Level {capability.contract-composition}
### 17.1 `dependent_capabilities`
Declared dependents MUST be invoked through shared pipeline; hidden delegation invalid.
### 17.2 `output_block_kinds` and `output_event_kinds` {capability.output-kinds}
Emitting undeclared block/event kind is Explicit Rejection; adding one requires declaration update + version increment.
### 17.4 Adapter Capabilities {capability.adapter-capabilities}
Adapter declares `adapter_capability` naming target id+version; invokes target through shared pipeline.
Ledger MUST record both adapter id + resolved target id.

## 18. Settings {capability.settings}
### 18.1 Configurable Dimensions and Layer Ownership
Every mechanism MUST be configurable.
Dimensions: per-capability `enabled`; default `permission_tier` overrides (capped by `permission_floor`); `classification_mode` overrides; cost-model overrides + budget caps; telemetry enablement; per-source trust overrides; registry-wide collision behavior; discovery-capability enablement; alias deprecation enforcement; runtime-registration enablement; availability-predicate overrides; platform-availability visibility; source-approval risk thresholds.
### 18.2 Settings-Key Convention {capability.settings-key-convention}
`capabilities.<id>.enabled`, `capabilities.<id>.permission_tier`, `registry.collision_policy`, `registry.source_approval_threshold`, `sources.<source_id>.trust_override`
### 18.3 Boundary
Settings MUST degrade gracefully when an optional provider/platform capability is absent; MUST NOT become hidden hardcoded branches.

## 19. Explicit Rejections {capability.explicit-rejections}
- parallel registry per source
- silent registration by hidden mechanisms
- silent capability-id reuse for unrelated operations
- declarations omitting required metadata
- prose-only touched-resource for write access
- capability leakage outside declared scope
- source trust rewriting declared fields
- argument-aware tier as duplicate id variants
- model-request-only capability extension
- runtime registration bypassing user approval
- ids conflicting with namespace separators
- closure-backed with `replay_class` above `not_replayable`
- coalescing internal sub-mode dispatch into separate registrations
- registry hardcoding §18 variations
- `output_schema` inline content for durable-block outputs
- settings/leases/trust lowering below declared `permission_floor`
- platform mismatch silently dropping a capability
- implicit versioning (mutating behavior without version bump)
- treating registry state as declaration mutation
- hidden delegation
- treating Capability and skill/workflow/instruction-pack as same primitive
- preserving `Action` as parallel primitive

## 20. Consequences for Later Specs {capability.consequences-for-later-specs}
Later specs MUST: read declared metadata from `CapabilityDeclaration`; read live state from `RegisteredCapability`; record per-call resolved facts on `CapabilityInvocation` never on declaration; treat registry as resolution surface + File 04 as execution surface; not introduce parallel capability metadata/registries; consume the trust/source/declaration boundary; consume platform-as-availability-state; consume collision-as-registry-state.
