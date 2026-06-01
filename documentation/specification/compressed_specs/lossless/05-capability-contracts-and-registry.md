> Lossless render of canonical/05-capability-contracts-and-registry.md — original 86752 chars

# Capability Contracts and Registry

## Status
Canonical.

## Scope
Defines: `Capability` as typed/named/registered operation; three layered views — `CapabilityDeclaration` (durable source-authored contract), `RegisteredCapability` (live registry entry), `CapabilityInvocation` (per-call record); Capability Declaration field set; input/output/error schemas; declared metadata driving execution/policy/surface decisions; touched-resource as machine-parseable typed expressions; permission-tier declaration; replay-class declaration; validation paths + postcondition declarations; sourcing taxonomy (built-in, subsystem-owned, plugin-bundled, MCP-server, user-defined, external-API); capability identity/namespacing/aliasing/versioning; registry-state ownership of platform availability/enable state/source-collision resolution/backend binding lifecycle/trust state; the Capability Registry (operations, lifecycle, discovery, mutation); composition primitives including adapter capabilities.
Does NOT define: policy engine/lease evaluation/approval UI/runtime tier resolution [File 06]; tool-surface zones/model-request visibility/deferred loading/capability-borrowing UX [File 07]; run lifecycle/execution graph/hook execution/runtime input coercion [File 04]; routing/`RunIntent` selection [File 03]; block schema/artifact lifecycle/evidence model [Files 08,09]; provider integration internals/rate-limit tracking/circuit-breaker/polling intervals [File 17 provider; future MCP/External Integrations spec for MCP+external tool-provider]; specific subsystem-runtime designs (Coder/Web/Teacher/Memory) [future per-surface specs].

## Source Resolution
Resolves action/tool/MCP/plugin/command/workflow-step/subsystem-operation material into one boundary: canonical Capability contract+registry.
- Capability is single operation primitive; earlier Action-style interfaces superseded by full Capability contract.
- Registry stores immutable, versioned declarations with identity/schema/touched resources/effects/risk/preview/postcondition/presentation metadata.
- Work surfaces, substrate services, plugins, MCP servers, workflows, scripts, user-defined operations all register through same contract.
- Declarations are metadata, not approval decisions/model-request surfaces/execution records/UI widgets.
- Later policy/tool-surface/execution/automation/plugin specs consume this contract instead of inventing parallel operation metadata.

## 1. Chosen Model `capability.chosen-model`
One Capability Registry. Every operation (file read, shell exec, web fetch, browser click, memory recall, image generation, MCP-server tool, plugin tool, user-authored Wasm tool, external-API endpoint, automation invocation, sub-agent spawn, capability-discovery call) is declared as `Capability` and registered.
Three layered views:
- `CapabilityDeclaration` — durable source-authored contract: identity, schemas, touched-resource expressions, permission-tier, execution-semantic metadata (incl replay class), validation paths, source attribution, observability declarations
- `RegisteredCapability` — live entry pairing declaration with mutable registry state: resolved backend binding, source-instance reference, trust state, enable state, platform availability, lifecycle state, registration timestamp, diagnostics, alias activations, collision resolution
- `CapabilityInvocation` — per-call record produced when executor dispatches through [`run.call-pipeline`, File 04 §8.2]: resolved tier, resolved touched resources, resolved model-mediated classifications, selected backend binding instance, policy decision, ledger linkage, call outcome
Same declaration drives: agent-tool exposure; user-invocation paths (command palette, keyboard shortcuts, voice, menu); automation triggers; MCP-server exposure; workflow/DAG node references; approval routing; ledger attribution.
No second registry, no per-subsystem bespoke list, no `actions` vs `tools` split. `Capability` is canonical noun; "Tool" is informal synonym (not a separate primitive); surface zoning is separate [File 07]. The `Capability` declaration supersedes the `Action` interface in `atlas3-core/CONSTRAINTS.md` §5: `id`→identity (§3.1), `label`→display (§3.2), `shortcut`→`default_shortcut` (§3.2), `when`→`availability_predicate` (§9.2), `execute`→backend descriptor (§3.12). `Action` NOT preserved as parallel registry/adapter layer/alias. Capabilities+policy compose (declaration carries enough metadata for policy without re-inspecting implementation); capabilities+surfaces compose (stable id surface can load/hide/borrow without changing declaration).

## 2. `Capability` `capability.capability`
### 2.1 Definition
Typed, named, registered, versioned operation. NOT: a UI button/menu item; a conversation message kind; model-request text content; a transient runtime concept; a single function pointer. May/may not be currently exposed to tool surface/command palette/voice/shortcut; presentation membership owned by [File 07].
### 2.2 Required Properties (Declaration)
Every `CapabilityDeclaration` MUST have: stable identity (§3.1,§13); typed `input_schema` (§4.1); typed `output_schema` (§4.2); typed error vocabulary (§4.3); touched-resource declaration as machine-parseable expressions (§6); permission-tier declaration (§5); capability class declaration (§3.5); execution-semantic metadata declared in [`run.call-pipeline`, File 04 §8.2] plus per-field `classification_mode` directive (§3.6,§7); `replay_class` declaration (§3.6,§7.3); validation path (§8); declared source (§9.1); backend descriptor (§3.12,§10.4); declared display metadata (§3.2). A declaration lacking any of these is invalid and MUST be rejected at registration.
### 2.3 Boundary
Declaration=contract; registered entry=runtime state; handler=implements operation; policy=evaluates per call; surface=presents; executor=invokes. Handler choosing between input variants (binary vs text inside one read; different shell parsers inside one shell exec) handles them internally as one capability with sub-modes; single registry entry covers full input-shape distribution. Cross-capability composition is higher-layer (§17).

## 3. Capability Declaration — Field Set `capability.declaration`
Durable source-authored contract; every field required unless marked optional. Immutable for given `(id, version)`; updates go through `version` increment (§13.4). Registry-state mutations live on registered entry (§10), never on declaration.
### 3.1 Identity Fields
- `id`: stable, namespaced string (§13.1)
- `version`: semantic version of declaration (§13.4)
- `schema_version`: format version of declaration itself, so registry can normalize supported formats during registration (§13.5)
- `aliases`: optional list of prior identities with declared deprecation timing (§13.3)
### 3.2 Display Fields `capability.display-fields`
Localizable descriptor: literal default carries canonical text; optional i18n key + translation reference enable localization. Built-in should provide i18n key + literal default; dynamic declarations (MCP/plugin/external API/user-defined) MUST always provide safe literal defaults.
- `name`: required default human-readable name
- `description`: required default model-facing + user-facing description
- `short_description`: required one-line default for compact discovery + borrowable surface zone [`run.zones`, File 04 §10.2]
- `i18n_key`: optional i18n key resolving translated name/description/short_description
- `translations`: optional translation map / source localization reference
- `family`: capability family identifier (§13.2)
- `tags`: optional typed tags (`agent-invokable`, `voice-invokable`, `palette-invokable`, `destructive`, `experimental`, plus user-extensible)
- `icon_key`: optional icon identifier
- `default_shortcut`: optional keyboard shortcut; user-overridable through settings
Display fields declarative only; presentation owned by File 07+future UI specs; MUST NOT be hardcoded into surface logic.
### 3.3 Schema Fields
- `input_schema` (§4.1); `output_schema` (§4.2); `error_vocabulary` (§4.3)
### 3.4 Touched-Resource Fields
- `touched_resources`: typed list of machine-parseable resource expressions describing every resource the capability may read/write (§6)
### 3.5 Permission and Policy Fields `capability.permission-policy-fields`
- `permission_tier`: `TierResolver::Static(Tier)` or `TierResolver::Dynamic(resolver_id)` (§5)
- `permission_floor`: optional minimum tier global settings cannot lower (§5.4)
- `capability_class`: `InternalAnalysis`, `ActionExternal`, `UserArtifact`, or `Unknown`; policy-critical, consumed by File 06 for default template selection + trust escalation. Tags may mirror but are not source of truth.
- `approval_template_id`: optional identifier for default approval-policy template used when policy escalates (templates in File 06)
- `data_sensitivity`: default sensitivity class for events/outputs (`Public`, `Sensitive`, `Secret`); per [`run.event-stream`, File 04 §23.2]
### 3.6 Execution-Semantic Fields `capability.execution-semantic-fields`
Declared in [`run.call-pipeline`, File 04 §8.2], referenced here:
- `concurrency`: `ConcurrencySafe`, `SelfParallel`, `Exclusive`
- `reversibility_class`: `none`, `compensable`, `reversible`
- `idempotent`: bool
- `preview_mode`: `none`, `dry_run`, `structural_preview`, `diff_preview`
- `partial_output_meaningful`: bool
- `cooperative_stop_deadline_ms`: u64 with policy default
- `sibling_abort_on_failure`: bool
- `resume_on_restart`: bool with optional resume handler reference
Declaration-owned additions:
- `terminates_sequence`: optional bool — true signals to batch-execution callers this capability changes external state invalidating queued sibling calls
- `replay_class`: `deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable` (§7.3)
- `classification_mode`: per-field directive naming how each field determined — `Deterministic` (declared once, fixed) or `ModelMediated { policy_model_request_template_id }` (designated model classifies per call against configured policy model-request template); applied to fields that can't be statically declared (`reversibility_class` for shell-style). Declaration names mode; per-call resolved value on invocation record (§11).
### 3.7 Validation Fields
- `input_validators`: declared pre-execution validation steps (§8.1)
- `postconditions`: declared post-execution checks (§8.2)
- `stale_state_revalidation`: optional declaration of stale-state revalidation pattern (§8.3)
### 3.8 Sourcing Fields
- `source`: typed `CapabilitySource` (§9.1) — names source kind + carries source-version identifiers (`plugin_version`, `server_version`, definition file hash) as immutable source-artifact metadata. Trust state + registration timestamp are NOT declaration fields (mutable runtime classifications on registered entry §10).
### 3.9 Availability Fields `capability.availability-fields`
- `availability_predicate`: declarative requirements+blockers evaluated against world-model state (§15.2)
- `platforms`: optional platform constraint list (`windows`, `macos`, `linux`, `mobile`, etc.); a capability whose list omits current platform is catalogued `availability_status: unavailable_platform` on registered entry, not absent (§9.4,§10)
- `prerequisite_capabilities`: optional list of scoped prerequisites that must have been invoked previously (§15.3)
The `enabled` flag is registry state, not a declaration field (§10); settings scope enable state per workspace/conversation/globally without mutating declaration.
### 3.10 Composition Fields `capability.composition-fields`
- `dependent_capabilities`: optional list of capability ids this capability may invoke internally — for transparency to policy+surface (§17.1); not an execution bypass; declared dependents still invoked through shared pipeline
- `output_block_kinds`: declared block kinds produced (§17.2)
- `output_event_kinds`: declared event kinds emitted (§17.2)
### 3.11 Cost and Telemetry Fields
- `cost_model`: optional cost-prediction declaration (per-call expected cost; per-token/per-byte/per-second/fixed)
- `telemetry_schema`: declared event types emitted beyond canonical execution events; future storage spec extends, canonical declaration names minimum
### 3.12 Backend Descriptor `capability.backend-descriptor`
- `backend`: serializable backend descriptor — kind + params registry needs to resolve a live binding: `ServiceMethod { service_id, method_name }`, `Wasm { module_id, entry_point }`, `Shell { program, args, cwd, env_overlay }`, `McpProxy { server_id, remote_tool_name }`, `HttpEndpoint { url_template, method, auth_ref }`, `Closure { closure_id }`
Descriptor is declarative; resolved live binding (service method handle, loaded Wasm module, MCP client adapter, HTTP client, in-process closure) is registry state (§10.4). Handlers never serialized into declarations. Closures not portable across processes → declarations using `Closure { ... }` MUST declare `replay_class: not_replayable` (§7.3).
### 3.13 Boundary
Field set above is canonical minimum. Future storage spec + File 06 may attach additional metadata (telemetry beyond minimum, per-capability rate-limit scopes, capability-specific config); extensions MUST be additive, MUST NOT change meaning of named fields. Declaration is wire-stable through `schema_version`; registry normalizes supported earlier formats at registration. Local-only, no existing user base → no migration framework required now; when external declarations persist, normalization-on-load applies (registry concern, not caller).

## 4. Schemas `capability.schemas`
### 4.1 `input_schema` `capability.input-schema`
JSON Schema describing input arguments. Required: every input parameter named with declared type, default value where applicable, validation constraints, human-readable description; required params distinguished from optional; enums declared explicitly with allowed values; nested objects/arrays/discriminated unions supported; input parameter aliases declared in schema metadata when alternative names accepted (registry resolves aliases before calling validators). Wire format is JSON Schema; generation from typed source structs (Rust-side schema generator) recommended; wire format is contract, source-code form is authoring convenience. MUST be sufficient for: model emitting syntactically valid call from description alone; registry validating inputs before dispatch; surface rendering input forms when user-invoked; policy inspecting arguments for tier resolution + lease scope matching; ledger recording inputs in typed replayable form. Inputs validated against `input_schema` before execution; runtime decision on schema-mismatch handling (strict reject/safe coercion/model repair/user correction) is execution policy [File 04 / future capability-runtime spec]; declaration's role is to require schemas exist + are honest.
### 4.2 `output_schema`
JSON Schema describing output value. Required: principal return shape declared exhaustively; polymorphic union → every variant declared with discriminator; typed sub-objects for handles/references/citations/structured output; relationship between produced blocks + return value made explicit (whether value contains block id, content inline, or reference to artifacts). Capabilities whose output is principally durable blocks (file edits, artifact creation, document edits) declare return value referencing produced block ids, not inline content; inline content reserved for short structured data + small text outputs.
### 4.3 `error_vocabulary` `capability.error-vocabulary`
Declares typed errors. Each variant: stable kind identifier (string); declared structured fields (typed); `recoverable` boolean (whether agent loop attempts in-band recovery — per [`run.denial-is-in-band`, File 04 §8.3]); `retryable` classification (retried as-is / with backoff / must not retry); human-readable message template. In-band tool-result errors MUST conform to this vocabulary. Errors escaping the capability boundary as `AppError` cross-boundary failures [`core.typed-errors`, File 01 §6.9] MUST map to declared variants + system's typed-error envelope. MUST NOT emit ad-hoc error kinds; adding an error kind requires registry update + versioning (§13.4).

## 5. Permission-Tier Declaration `capability.permission-tier-declaration`
### 5.1 Tier Set
Canonical [`run.approval-during-execution`, File 04 §11]: `Denied`, `ReadOnly`, `WorkspaceWrite`, `UserApproval`, `Unrestricted`, with `typed-confirmation` mode as variant of `UserApproval`.
### 5.2 `TierResolver` `capability.tier-resolver`
`permission_tier` is one of: `TierResolver::Static(Tier)` (fixed, known at registration, no per-call eval — default); `TierResolver::Dynamic(resolver_id)` (tier depends on call-time arguments; registered argument-aware resolver examines input arguments + current world state to return tier). Dynamic exists for argument-sensitive capabilities (`file.edit` inside workspace = `WorkspaceWrite`; same outside = `UserApproval`); splitting into id variants per tier is rejected. Resolvers are registered/named/inspectable; capability declares resolver by id; resolver behavior MUST be deterministic given same arguments + world-model snapshot. Resolvers are not capabilities (no work) but registry-managed declarations; resolver registry colocated with Capability Registry. Resolver declaration belongs to declaration; resolved tier (the value returned by `Dynamic` resolution) per call belongs to invocation record (§11); File 06 computes final effective tier + approval path.
### 5.3 Tier Composition With Leases
Declared tier is baseline. Policy may grant a `Lease` lowering per-call friction (`AlwaysAllow` lease for `UserApproval` capability auto-resolves next call within lease scope). Leases cannot escalate above declared tier, cannot bypass `Denied`, cannot lift `typed-confirmation`. Composition follows lease-scope hierarchy [`run.approval-during-execution`, File 04 §11]; cross-scope contradictions surface as policy errors, not silent wins.
### 5.4 `permission_floor` `capability.permission-floor`
Minimum tier global settings (incl `agent.unrestricted_mode`) cannot lower. For high-risk: account deletion, destructive publish, force-push to protected branch, system shutdown, credential export, irreversible publishing. `permission_floor` + `permission_tier` are distinct (floor=minimum, tier=default). Runtime tier = higher of (a) resolved `permission_tier`, (b) `permission_floor`, (c) any narrower tier from an active scope-level policy override.
### 5.5 Boundary
Declaration carries tiers/floors/resolvers; policy layer evaluates against active leases, scope-level overrides, source trust, approval templates → runtime decision. File 05 owns declaration + registered trust state; File 06 owns evaluation.

## 6. `touched_resources` `capability.touched-resources`
### 6.1 Required Shape
Typed list. Each entry: `class` (from §6.2 canonical set or registered extension class §6.3); `access` (`read`, `write`, `read_write`, `invoke`, `observe`, `none`); `expression` (machine-parseable typed expression resolving concrete resource scope, NOT prose). Declared as expressions, not concrete enumerations. Argument-dependent expressions reference input-schema field paths by name (`args.path`, `args.command`, `args.url`); static expressions name fixed resources. Prose-only declarations INVALID for any capability with `access: write` or `access: read_write`; read-only capabilities may add prose clarifications alongside expressions (expression remains contract).
### 6.2 Canonical Resource Classes
Closed enumerable set: `filesystem`, `network`, `process`, `env`, `credential`, `setting`, `model-call`, `browser-session`, `ui-element`, `sub-agent`, `scheduler`. Cover resource kinds canonical execution/policy/isolation/settings/ledger reason about; closed set keeps policy resource matching, lease-scope inclusion, conflict detection deterministic.
### 6.3 Extension Resource Classes `capability.extension-resource-classes`
Subsystems/plugins may register additional classes through a registered subsystem-extension capability (§16.2). Entry carries `extension_id` namespacing class, a structured scope grammar, a containment predicate so policy decides lease-scope inclusion without inspecting internals. Examples: `video-feed`, `ble-device`, `vector-index`. First-class once registered (leases/audit/conflict detection/routing reason about them like canonical). Registration is a capability call subject to policy + proposal-first (§16.2).
### 6.4 Resource Expressions `capability.resource-expressions`
Structured terms over input schema + registered ambient values (workspace root, current process group id, run id, conversation id, current credential vault keys). Indicative shapes: static `network:{ host: "api.openai.com" }`; argument-bound `filesystem.path(args.path).within(workspace_root)`; derived `shell.parse(args.command).filesystem_writes`; external account `connector.account(args.account_id).mailbox(args.mailbox_id)`; setting key `setting.key(args.key).scope(args.scope)`; process group `process.group(run_id)`. Exact grammar in File 06 / capability-schema appendix; this file requires expressions machine-parseable, argument-bound expressions reference `args.*` by name, expression resolves to concrete resources policy must check.
### 6.5 Purpose
Machine-readable expressions make declaration inspectable by: policy (lease-scope matching); audit ledger (forensic reconstruction); routing (capability selection — request requiring web access selects only capabilities whose expressions include `network`); user (explicit understanding before approval, surface previews resolved resources not just classes); replay (predicted-vs-observed). MUST be honest+complete; quiet reading of credentials/mutating env vars/contacting undeclared hosts is an Explicit Rejection (§19).
### 6.6 Boundary
Declaration names what may be touched; policy resolves expressions against arguments → concrete per-call set (§11); runtime sandbox enforces actually touched [`run.child-runs-multi-agent-work`, File 04 §16]. A declared scope the runtime can't enforce is still the contract; runtime catches violations + emits typed errors.

## 7. Execution-Semantic Metadata `capability.execution-semantic-metadata`
§3.6 fields settled in [`run.call-pipeline`, File 04 §8.2]; declaration-owned additions:
### 7.1 `terminates_sequence`
Declare `terminates_sequence: true` when execution invalidates in-flight sibling calls in same dispatch batch (browser-state-changing nav/click, sandbox-state-changing operations). Executor aborts queued siblings when capability completes. With runtime detection [`run.failure-in-parallel-work`, File 04 §15.3] = defense-in-depth against silent corruption from out-of-order parallel execution.
### 7.2 `classification_mode` `capability.classification-mode`
For fields where single static value isn't meaningful (`shell.exec` can't declare one `reversibility_class` for all bash commands): per-field `classification_mode` = `Deterministic` (declared static value applies every call) or `ModelMediated { policy_model_request_template_id }` (classifier model evaluates specific call against configured policy model-request template, returns per-call value; template registry-managed + inspectable). Per-field not per-capability (may declare `reversibility_class` model-mediated while `concurrency` static). `ModelMediated` pays extra model-call cost per dispatch, used selectively; default `Deterministic`. Declaration names mode; per-call resolved value (the class returned by `ModelMediated` classification) on invocation record (§11).
### 7.3 `replay_class` `capability.replay-class`
Every declaration carries:
- `deterministic_replayable` — same inputs+referenced state → same result; pure local reads + pure transforms qualify
- `snapshot_replayable` — replay requires recorded snapshots/materialized observations executor captured (file content at path, web-page snapshot, accessibility-tree fingerprint); without snapshot, replay undefined
- `effect_replayable_with_policy` — call causes external effects (email send, payment API, DB mutation), reissued only through policy; contract names policy hook replay must consult before reissuing
- `not_replayable` — cannot reproduce across process/device/session boundaries; closure-backed, transient-runtime-handle-dependent, inherently uncontrolled side-effects
Author classifies based on call shape, not per-call state (whether file at `args.path` still exists at replay is snapshot/policy concern). Replay layer [`run.execution-ledger`, File 04 §23.1 + File 10] consumes `replay_class` to decide what evidence to record, what to require, what to refuse. Closure-backed declarations (§3.12) MUST declare `replay_class: not_replayable`; otherwise Explicit Rejection (§19).
### 7.4 Boundary
These fields drive execution behavior; declared by author at registration; read by executor+ledger at dispatch+replay. Any change after registration → version bump + new declaration alongside old (§13.4).

## 8. Validation and Postconditions `capability.validation-postconditions`
### 8.1 `input_validators` `capability.input-validators`
Beyond schema validation, capability may declare additional pre-execution validators: structural (parsed-AST checks for shell commands, regex compilation for grep tools, JSON-schema verification for sub-schemas); workspace-boundary (path normalization, symlink resolution, workspace-root containment); argument-coercion (string-to-number, empty-string-to-null, alias-name resolution) declared as part of input contract for LLM-noise tolerance; registered hook validators (QC validators [`run.hook-integration`, File 04 §23.3] attach at `ToolCallProposed` boundary; capability declares which hook categories it expects). Validators run in declared order; may return `valid`, `invalid_with_correction`, or `invalid`. Executor honors corrections (validator supplies normalized argument), records correction in ledger, proceeds. `invalid` without correction halts dispatch + produces typed validation error in-band. Aggressiveness of coercion/repair on schema mismatches is execution policy [File 04 / future capability-runtime spec]; declaration's role is to require validators exist, name order, surface corrections.
### 8.2 `postconditions`
Capability may declare structural postconditions (deterministic checks runtime evaluates after execution to confirm declared effects): declared output-schema conformance (structural validation against `output_schema`); declared resource-state checks (file existence at declared path for file-producers; row count delta for DB writes); declared ledger evidence (referenced through [`run.termination`, File 04 §22] deterministic forgery guard — a capability whose contract required action cannot terminate `completed` without ledger evidence of action). Deterministic by default; configurable completion-verification hook [`run.termination`, File 04 §22] supports model-mediated semantic checks at user-configured cadence; deterministic floor in `postconditions` is canonical minimum. Failing postcondition → typed postcondition-failure variant in `error_vocabulary` + may trigger declared compensation (per `reversibility_class`).
### 8.3 `stale_state_revalidation`
For capabilities whose mutation depends on prior observation (file edit after read, GUI click after tree snapshot, browser action after page snapshot): declaration carries stale-state revalidation pattern from [`run.call-pipeline`, File 04 §8.2]: prior-observation metadata recorded (file mtime + content hash, accessibility-tree fingerprint, DOM snapshot id); `expected_*` fields accepted on input schema (caller supplies recorded observation metadata); typed `StateChangedSinceObservation`-class error variant returned when metadata mismatches current state. Executor enforces nothing additional; author responsible for revalidating before mutating; declaration makes pattern visible+inspectable.
### 8.4 Boundary
Validation belongs to capability + registered validator hooks; approval to policy layer; postcondition reporting to ledger [`run.ledger-events-commits`, File 04 §23 + File 10]. Authors do not implement own approval flow.

## 9. Sourcing `capability.sourcing`
### 9.1 `CapabilitySource` `capability.capability-source`
Every declaration names source, one of:
- `Builtin` — compiled into binary; ships with every install; cannot unregister without update
- `Subsystem { subsystem_id }` — owned by a registered subsystem (work surface or substrate service: Memory, Routing, Context Assembly, Retrieval, Knowledge Indexing, Settings, Evaluation, Policy); registered/loaded with the subsystem. New subsystems added/removed through subsystem-registration capability (proposal-first §16.2); subsystem composition is first-class+customizable.
- `Plugin { plugin_id, plugin_version }` — bundled in a plugin [`core.extension-planes`, File 01 §6.14; future Extension and Plugin System spec]; registered on plugin load; unregistered on unload
- `McpServer { server_id, server_uuid, server_version }` — from external MCP server; registered on connect; unregistered on disconnect
- `Api { api_name, api_definition_path }` — from user-authored external-API TOML/equivalent; registered when definition file loaded
- `UserDefined { backend, scope }` — registered at runtime by user or (with explicit user approval) the agent through a capability-registration capability; backend is `Wasm` or `Shell` [`run.interruption-pause-cancellation`, File 04 §17 self-modification]; scope `conversation`/`workspace`/`global`
A capability has exactly one source; cannot be both built-in + plugin; a plugin overriding a built-in must register a distinct id + user must explicitly select override (§14).
### 9.2 Trust and Source-Approval Flow `capability.trust-source-approval-flow`
Trust is registry state, not declaration field. Declared source carries source-version identifiers; registered entry (§10) holds: `declared_trust_hint` (class source asserts — plugin manifest claim, configured MCP server trust); `registry_trust_override` (explicit user override via settings); `effective_trust` (`System` for Builtin/Subsystem, `Verified`, `Community`, `Unverified`, or `User` for UserDefined/Api, computed from hint + override). Trust does NOT rewrite declared fields: a capability declaring `permission_tier: WorkspaceWrite` from a `Community`-trust MCP server retains declared `WorkspaceWrite`; policy reads declaration+trust → resolves effective tier of at least `UserApproval` by default for `Community`+`Unverified` sources; user may explicitly upgrade trust per source. Keeps declarations honest; policy changes when trust settings change without mutating versions. When a source registers (plugin install, MCP connect, external-API load, user-defined registration), runtime surfaces declared permission tiers, touched resources, replay class, trust hint, source provenance, computed source-risk summary before activation when policy requires review; user accepts defaults / configures policy / denies source / explicitly defers source-level policy to per-call fallback / cancels. Review triggering is risk-summary based (declared tier is one input, not whole rule); exact trigger+fallback owned by File 06 + user settings.
### 9.3 Sourcing Equivalence `capability.sourcing-equivalence`
Capabilities from every source enter same registry through same contract; source distinction surfaces as metadata (agent sees same tool list whether `Builtin` or `McpServer`); policy reads same fields; ledger records resolved id with source attached. No parallel "MCP tool list"/"plugin tool list"/"user-tool list"; surface/settings UI may filter by source for clarity, but registry is one.
### 9.4 Platform Conditioning
Platform mismatch is registry availability state, not registration filter. A declaration whose `platforms` omits current OS still registers; registered entry carries `availability_status: unavailable_platform` + no resolved backend binding. Visible in settings, plugin inspection, dependency diagnostics, automation validation, cross-device transparency; not invocable on current platform. Surface/discovery may hide unavailable from default views; advanced settings reveal them. Equivalent semantic capabilities for different platforms (Windows registry-write vs macOS plist-write) may share family + be selected by routing based on platform; ids remain platform-disambiguated. A capability registered `Available` on Windows MUST NOT throw `PlatformUnsupported` on Linux; registered entry on Linux is `unavailable_platform` from registration onward.

## 10. `RegisteredCapability` — Registry State `capability.registered-capability`
### 10.1 Definition
Live entry produced when a `CapabilityDeclaration` admitted; pairs declaration with mutable state:
- `declaration`: registered `CapabilityDeclaration` (immutable for version)
- `registered_at`: timestamp
- `enabled`: runtime enable flag distinct from existence; settings-scoped per workspace/conversation/globally (§16.3)
- `availability_status`: `Available` | `UnavailablePlatform` | `UnavailableHandler` | `UnavailablePrerequisite` | `Disabled` | `Shadowed`
- `resolved_backend_binding`: live resolved handler reference (service-method handle, loaded Wasm module, MCP client adapter, HTTP client, in-process closure); never serialized into declaration
- `source_instance`: registered source-instance reference (which loaded plugin, connected MCP server, loaded API definition file)
- `trust_state`: `{ declared_trust_hint, registry_trust_override, effective_trust }` (§9.2)
- `lifecycle_state`: `Loading` | `Active` | `Updating` | `Disabled` | `Unregistering`
- `active_aliases`: alias entries currently honored for lookup (§13.3)
- `diagnostics`: registration diagnostics, last-error trace, last-successful-resolve timestamp, registration-failure reason if any
- `collision_state`: `Active` | `Shadowed { shadowed_by }` | `Shadowing { shadows }` (§14)
### 10.2 Mutation Rules
Registry state mutates (settings changes, plugin updates, MCP reconnection, platform changes, trust overrides) without changing declaration. `(id, version)` immutable for entry's lifetime; new declaration version → new entry superseding old (§16.4). Mutations emit registry events (§12.2).
### 10.3 Inactive Entries Remain Inspectable
Disabled/shadowed/`unavailable_platform` entries remain in registry as inspectable catalogue records; not invocable but appear in settings/diagnostics/plugin inspection/dependency analysis. User can see why unavailable, when, what would re-enable. Removal from catalogue only through `unregister` (§16.5).
### 10.4 Backend Binding Lifecycle `capability.backend-binding-lifecycle`
Declaration carries serializable backend descriptor (§3.12); registered entry carries resolved live binding. Per kind:
- `ServiceMethod` — resolved against Rust service registry (static-typed services compile-time wired; dynamic services runtime-registered for plugin-loaded); persists across restarts when service persists
- `Wasm` — resolved against loaded Wasm module registry; sandboxed [`run.child-runs-multi-agent-work`, File 04 §16]; persists across restarts when module re-loaded
- `Shell` — resolved against configured subprocess invocation; sandboxed per shell-operations spec
- `McpProxy` — resolved against active MCP client pool; invokes remote tool through MCP + adapts response; deregisters on MCP disconnect, re-resolves on reconnect
- `HttpEndpoint` — resolved against HTTP client; auth from credential vault by reference (never inline secrets)
- `Closure` — runtime-registered closures (test fixtures, in-process plugins); not serializable; deregisters at process exit; MUST declare `replay_class: not_replayable` (§7.3)
Declaration=contract; binding=registry state. Binding-failure diagnostics (handler unresolved, MCP unreachable, Wasm load error) live on entry, don't invalidate declaration.

## 11. `CapabilityInvocation` — Per-Call Record `capability.invocation-record`
Per-call record produced when executor dispatches through [`run.call-pipeline`, File 04 §8.2]. Owned by File 04 (proposal/execution) + File 10; File 05 names schema only to draw layer boundary + identify per-call resolved facts (not declaration fields):
- resolved `(id, version)`
- invocation arguments (after schema validation + declared input-validator corrections §8.1)
- resolved permission tier (`TierResolver` return §5.2)
- resolved touched resources (concrete resources from evaluating expressions against arguments §6)
- resolved model-mediated classifications (per-field values from `ModelMediated { policy_model_request_template_id }` §7.2)
- selected backend binding instance (which MCP connection, which Wasm module) at dispatch
- policy decision (lease consulted, approval mode chosen, contradiction-checks) — File 06
- proposal id, ledger entry id, event sequence
- call outcome (typed result, typed error, blocks produced, events emitted)
Durable in ledger [`run.execution-ledger`, File 04 §23.1]. Replay reads `(declaration_version, resolved_backend_binding_id_at_time)` from record; does NOT infer from current registry state.

## 12. Capability Registry `capability.capability-registry`
### 12.1 Operations
MUST support: `register(declaration) -> Result<RegisteredCapability, RegistrationError>`; `unregister(id) -> Result<(), RegistrationError>` (on plugin unload, MCP disconnect, user uninstall); `update(declaration) -> Result<RegisteredCapability, RegistrationError>` (replace with new version per §13); `enable(id, scope)` + `disable(id, scope)` (toggle enabled flag §10,§16.3); `get(id) -> Option<RegisteredCapability>`; `lookup_alias(name) -> Option<RegisteredCapability>`; `list(filter) -> Vec<RegisteredCapability>` (filter by family/source/tag/platform/enable state/availability status/predicate match); `available(world_state) -> Vec<RegisteredCapability>` (entries whose `availability_predicate` matches snapshot + `availability_status: Available` + `enabled: true`); `find_by_shortcut(shortcut)`; `subscribe(events) -> Stream<RegistryEvent>`; `resolve_for_invocation(id, args, world_state) -> Result<InvocationDescriptor, ResolutionError>` (resolve identity/version/alias/source-collision active winner + prepare invocation descriptor executor consumes). Registry resolves; executor invokes. Registry owns: registration, lookup, version resolution, alias resolution, source-collision active-entry selection, declaration validation, availability projection, backend-binding resolution. Executor [`run.call-pipeline`, File 04 §8.2] owns: proposal, approval, tool-call execution, hooks, cancellation, streaming, ledger entries, result blocks. Registry does NOT own an `execute` primitive; convenience facades are explicit delegations to execution runtime, not registry-owned execution.
### 12.2 Events `capability.events`
Registration → `CapabilityRegistered`; unregistration → `CapabilityUnregistered`; update → `CapabilityUpdated`; enable/disable → `CapabilityEnabledChanged`; registry-state mutations (binding rebound, trust override applied, collision resolved, availability changed) → `CapabilityRegistryStateChanged`. Subscribers (surfaces, settings, capability-discovery projection) react.
### 12.3 Registration Mechanics
Declarative + idempotent; a subsystem/plugin/runtime registration capability calls `register(declaration)` with a complete contract. Registry: 1. Validate declaration (every required field present, schemas well-formed, identifiers conform to namespacing, source declaration valid, expressions parseable for write-capable touched-resource entries). 2. Check id collision + apply collision policy (§14.1). 3. Resolve backend binding (named service/Wasm module/MCP server exists). 4. Normalize to current `schema_version` if needed (§13.5). 5. Compute registry state (registered_at, declared_trust_hint, source_instance). 6. Insert entry. 7. Emit `CapabilityRegistered`. 8. Update derived projections (capability-discovery, command-palette index, voice-command map, automation trigger-target list). Failure typed errors: `IdentifierCollision`, `InvalidDeclaration`, `HandlerUnresolved`, `SchemaTooNew`, `SourceConflict`, `UnparseableResourceExpression`. Failed registrations leave registry unchanged. Unregistration reverse: emit pre-unregister event, transition lifecycle `Unregistering`, allow in-flight calls to complete, drop projections, remove entry, refuse new calls.

## 13. Identity, Namespacing, Versioning `capability.identity-namespacing-versioning`
### 13.1 `id` `capability.id`
Stable, namespaced, lowercase, dotted string; first segment names source class:
- Built-in/subsystem: `<family>.<operation>` (`file.read`, `shell.exec`, `web.fetch`, `memory.recall`, `gui.click`, `teacher.explain`, `data.pdf.extract_text`)
- Plugin: `plugin.<plugin_id>.<operation>` (or plugin's declared namespace `<plugin_namespace>:<operation>`; registry stores both, resolves equivalently)
- MCP: `mcp.<server_id>.<remote_tool_name>` (server_id is user-visible name not UUID; UUID in registered source instance)
- Registry-bridged external API: `api.<service_name>.<endpoint_id>`
- User-defined: `custom.<scope>.<tool_id>` (scope `conversation`/`workspace`/`global`)
Ids case-insensitive at lookup (registered case preserved for display); may not contain whitespace, slashes, or namespace-separator chars (`.`, `:`, `__`); registry rejects non-conforming.
### 13.2 `family` `capability.family`
Free-form identifier grouping related capabilities for surface organization, routing, policy templating. Common: `file`, `shell`, `web`, `browser`, `memory`, `data`, `gui`, `system`, `code`, `image`, `audio`, `video`, `agent`, `plugin`, `mcp`. Same-family capabilities may share approval-policy templates + surface defaults. One family per capability; membership for grouping, doesn't affect dispatch.
### 13.3 `aliases`
Alternative ids the capability has been known as. Support: registry-level renames without breaking saved automations/pinned shortcuts; MCP naming-style conventions; backwards compat across `version` increments. Each entry: alias string, version range honored, optional deprecation timestamp after which registry warns/refuses lookups. Inspectable; registry doesn't silently rewrite ids; active alias projection on entry (§10). `aliases` for identity compatibility only; delegating handler is the distinct adapter capability mechanism (§17.4).
### 13.4 `version` `capability.version`
Semantic version of declaration; semver: patch (1.0.0→1.0.1, no observable contract change, docs/internal refactor); minor (1.0.0→1.1.0, backwards-compatible additions: new optional input field, new error variant, new tag); major (1.0.0→2.0.0, breaking: removed input field, output schema change, permission-tier change, removed error variant, family change, incompatible behavior). Registry may hold multiple versions concurrently when callers reference explicitly (saved automations may pin); default resolved = latest registered; major bumps explicit, old version not implicitly removed. Version is part of wire identity for replay: ledger records `(id, version)`; replay against different version surfaces typed reproducibility warning.
### 13.5 `schema_version`
Format version of declaration itself, distinct from capability `version`. Increments allow field set to evolve (new metadata fields, deprecated removed) without breaking older declarations; registry normalizes supported earlier `schema_version` forward to current at registration. Initial development, no third-party persisted declarations → no migration framework with chained migrations required now; registry validates current `schema_version`, rejects unknown; when external declarations persist (plugins across releases, MCP adapters surviving upgrades), normalization-on-load applies at that boundary.
### 13.6 Boundary
Identity stable across runs; `version` is explicit mutation knob; renames via aliases; replacement is `update()` with new declaration honoring semver. Wholesale id reuse for unrelated operations FORBIDDEN (silent reproducibility breakage).

## 14. Override Resolution and Conflicts `capability.override-resolution-conflicts`
### 14.1 Identifier Collisions
Two declarations may not be active entry under same `id` simultaneously. Collision policy: a registration colliding with existing active entry rejected by default (`IdentifierCollision`); registering source must use different id (typical for plugins); OR declare existing id as alias + offer itself as replacement under new id (explicit user-facing migration acceptance); OR higher-priority source (§14.2) with explicit user opt-in registers, registry stores both, marks existing `collision_state: Shadowed { shadowed_by: <new_entry> }` + new `collision_state: Shadowing { shadows: <prior_entry> }`, resolves lookups to new entry. Registry stores all colliding declarations that pass validation; collision policy selects active entry; shadowed entries remain inspectable through diagnostics + reactivatable by removing/disabling shadowing entry. Source declarations never mutated by collision resolution; active-vs-shadowed selection is registry state. Default = rejection; replacement opt-in + surfaced; replay pins exact `(id, version, source_instance)` active at call time so collision history doesn't break reproducibility.
### 14.2 Source Priority
When user explicitly opts into override: `UserDefined` overrides `Plugin` overrides `Subsystem` overrides `Builtin`. `McpServer` + `Api` live in own source-prefixed namespaces (`mcp.*`, `api.*`), don't collide with other sources by id alone. Source priority does NOT auto-override; user-defined wishing to take over a built-in id must declare override + user must accept; registry then shadows built-in. Reversible: removing/disabling user-defined restores built-in.
### 14.3 Layered Resources
Skills, instruction packs, instruction fragments, workflow templates are NOT capabilities; separate primitives with own layered resolution [File 04 + future capability-extension+skill specs]. File 05 doesn't specify layering for those. Where a capability ingests such a layered resource, it declares the layer policy (`project > workspace > user > plugin > builtin` or equivalent) + consumes resolved value.
### 14.4 Cross-Source Coexistence
Multiple sources commonly contribute non-colliding capabilities to same family (a `web.fetch` built-in + `mcp.web_fetcher.fetch` coexist; routing [File 03] decides per request). Coexistence default; collision exception.

## 15. Discovery `capability.discovery`
### 15.1 Lookup Surface
Axes: direct id lookup (alias-aware); family enumeration; source enumeration; tag-filtered enumeration; availability-filtered enumeration (over supplied world-model snapshot); text search over `name`/`description`/`tags`; semantic search over `description` (if embedding index configured) at higher cost. All honor `availability_status` + `enabled`; surfaces may reveal unavailable explicitly through advanced settings.
### 15.2 `availability_predicate` `capability.availability-predicate`
Declares when invocable. Required parts: `requires` (typed state needed: active surface, focused element class, selection presence, present capability prerequisites, present credentials, present provider with required model capability); `blocked_by` (typed state preventing invocation: destructive capability blocked while prior destructive call still committing; publish blocked while workspace has unsaved changes). State-awareness service evaluates predicates against current world-model snapshot → available-capability list [`core.world-model`, File 01 §6.7]. Surfaces consume that list (command palette shows available subset; agent sees available subset filtered further by File 07 loading). Declarative; a capability whose availability rule can't be a typed declaration MUST extend the predicate vocabulary through registered availability checks (named function registry evaluates); ad-hoc procedural availability rejected.
### 15.3 `prerequisite_capabilities` `capability.prerequisite-capabilities`
List of scoped prerequisites; each names a capability id + `scope`: `run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`. Satisfied when named capability invoked (successful outcome) within named scope before this becomes invocable. Evaluated against ledger + world-model facts, not hidden local flags. Used for sequencing (an `artifact_handoff`-style capability preceding content-generation; guide-must-be-read prerequisite gating source-tools until onboarding performed). Registry encodes dependency declaration + scope; detailed predicate evaluator [future world-state/availability spec]; violation returns typed `PrerequisiteUnsatisfied` error in-band.
### 15.4 Runtime Discovery Capabilities
Discovery is itself a capability surface. Canonical built-in discovery [`run.routing-influence`, File 04 §10.3] — `tool.search`, `tool.borrow`, `mcp.search`, `extensions.search_registry` — are first-class registered capabilities; agent invokes through same pipeline; outputs flow as typed blocks. Built-in discovery set canonical; surface tools may add subsystem/family-specific shortcuts. Discovery capabilities declare `ReadOnly` tiers + declare registry projections they read.

## 16. Lifecycle `capability.lifecycle`
### 16.1 Startup Registration `capability.startup-registration`
Declared phases: 1. Built-in (compiled in binary; declared statically by every subsystem during `AppState` init). 2. Subsystem (when subsystem runtimes load, per subsystem registry in File 03). 3. Plugin (as plugins load, future Extension/Plugin spec). 4. MCP-sourced (as configured MCP servers connect, future MCP+External Integrations spec). 5. External-API (as TOML definitions loaded). 6. User-defined (from persisted declarations, [`run.interruption-pause-cancellation`, File 04 §17] + future user-defined capability storage spec). Phases sequenced because later phases may override/alias earlier; registry stable when all complete. A capability failing to register (handler unresolved, declaration invalid, source unavailable) recorded as registration-failed in diagnostics; later sources proceed; startup does NOT abort on single failure.
### 16.2 Runtime Mutation `capability.runtime-mutation`
May register/update/unregister at runtime: plugin install adds capabilities mid-session (user approves plugin permission manifest at install time; available immediately to subsequent iterations); MCP connection adds capabilities mid-session (connection approved at server-add time; reconnection after crash retains prior approvals); user invocation of `tools.register_custom` adds user-defined capability (requires `UserApproval` regardless of other approvals; scope `conversation`/`workspace`/`global` declared in call); subsystem extension capability registers/removes a subsystem (same proposal-first rules). Registration is a capability call: capability registration, plugin installation, MCP connection, external-API import, user-script registration, subsystem registration all flow through [`run.call-pipeline`, File 04 §8.2] + policy layer like any call; not privileged side doors; agent cannot self-promote registration without user approval. Registration proposals preview source, declared permissions, touched resources, replay class, trust hint, persistence scope, backend kind → informed accept/configure/deny. Proposal shape + approval mode configurable per source class; default keeps ATLAS3 safe; users override per source (auto-approve trusted, ask-each-time untrusted, deny outright).
### 16.3 `enabled`
Registry state, not declaration field. A disabled capability remains in registry (appears with disabled status; `availability_status: Disabled`) but not invocable; disabling is settings-level; enabling restores invocability. Use cases over unregister: temporarily shut off noisy/expensive capability without losing declaration/scoped settings; suspected-misbehaving plugin disabled reversibly during diagnosis; plugin upgrade (old disabled while new register, then disabled unregistered atomically). May be scoped (globally enabled but disabled in a workspace/conversation); settings system [`core.settings-system`, File 01 §6.8] holds scoped enable state.
### 16.4 Update Mechanics
`update(declaration)` replaces active entry for named id. Compatibility: patch updates do NOT require re-approval of existing leases; minor updates preserve existing leases (backwards-compatible superset); major updates invalidate existing leases (contract changed; re-granted; user surfaced change at next invocation). Atomic from caller's perspective: in-flight calls against prior declaration complete under prior contract; new calls use new; both versions durably recorded in ledger so prior calls remain interpretable.
### 16.5 Unregistration
`unregister(id)` removes a capability; in-flight complete; new calls refused with typed `CapabilityUnregistered` error; persisted leases transition "stale" + pruned per policy spec lease-cleanup. Unregistering a built-in FORBIDDEN (binary defines built-in); built-in may only be disabled. Subsystem capability unregisters implicitly when subsystem unregisters; plugin capabilities on plugin unload; MCP on server disconnect; user-defined+API on user action.
### 16.6 Restart Behavior
Persisted registrations (built-in, subsystem, installed plugin, configured MCP, loaded API definition, user-defined with persistent scope) re-register on restart; enabled-before-restart remain enabled. In-flight calls that didn't complete follow orphan-run rules [`run.cancellation`, File 04 §17.3] (default `process_restart_orphan`; capabilities declaring `resume_on_restart: true` may resume per handler). Restart sequence deterministic: same declarations in same priority order → same registry state, modulo new plugin updates + MCP availability changes; determinism required for replay+reproducibility.

## 17. Composition Primitives at the Contract Level `capability.contract-composition`
### 17.1 `dependent_capabilities`
A capability whose handler internally invokes others declares `dependent_capabilities`. Used by: policy (transitive risk — a `WorkspaceWrite` calling a `UserApproval` capability surfaces both approvals); audit (attribute internal calls to outer invocation); surface (display composition transparently). Honest; NOT execution bypass: declared dependents MUST be invoked through shared pipeline so policy/leases/resource checks/hooks/cancellation/ledger all apply. Direct hidden delegation invalid even when declared; quiet undeclared delegation is Explicit Rejection (§19). Internal sub-mode dispatch within a single capability [`run.tool-calls`, File 04 §9] is NOT a dependent-capability call + need not be declared.
### 17.2 `output_block_kinds` and `output_event_kinds` `capability.output-kinds`
Block kinds from canonical block catalogue [File 08]; event kinds from canonical event catalogue [File 10]. Enable: surface rendering output without inspecting runtime value; context-assembly budgeting tokens for expected outputs; validation checking produced blocks match declared kinds. Emitting undeclared block/event kind is Explicit Rejection; adding a new emission requires declaration update + version increment.
### 17.3 Cross-Capability Programmatic Composition
Three shapes [`run.tool-calls`, File 04 §9; `run.programmatic-execution`, File 04 §14]: model emits multiple calls in one turn (execute concurrently subject to declared concurrency §7); programmatic execution (`code.execute_with_tools` or equivalent) chains calls deterministically within a single execution unit passing output→input (each call still full pipeline: validation/policy/dispatch/ledger); workflow step references a capability id + invokes with templated inputs (workflow runtime is itself a capability orchestrating others). None require new contract field set; runtime composition of capabilities whose declarations already present.
### 17.4 Adapter Capabilities `capability.adapter-capabilities`
A registered declaration may be an adapter — a separate registered capability delegating to a target while changing presentation/defaults/constraints/surface ownership. Declares own id, display, narrowed input/output schema, plus `adapter_capability` field naming target capability id+version. Adapter handler invokes target through shared pipeline (policy/leases/resource checks/hooks/ledger apply to inner + outer). Serves subsystem-specialized presentations (`coder.git_commit` adapting `git.commit` with coder display + constrained input), default constraints, tighter touched-resource scopes without duplicating implementation. Ledger records both adapter id + resolved target id. `adapter_capability` distinct from `aliases` (§13.3): `aliases` preserves single capability under multiple id strings; adapter is separate registered capability whose handler is the underlying target. Both inspectable+explicit.
### 17.5 Boundary
Contract-level composition makes capability use inspectable; runtime dispatch/batching/dependency-tracking/parallel execution [File 04]; block+event catalogs [Files 08,10]. File 05 declares surface area; later specs operate on it.

## 18. Settings `capability.settings`
### 18.1 Configurable Dimensions and Layer Ownership
Every mechanism MUST be configurable [`core.settings-system`, File 01 §6.8]. File 05 names dimensions + owning layer; resolution algorithms live in owning layers:
- per-capability `enabled` (global/workspace/conversation) — registry + settings system
- per-capability default `permission_tier` overrides (capped by `permission_floor`), same hierarchy — declaration carries dimension; resolution File 06
- per-capability `classification_mode` overrides (deterministic vs model-mediated) — declaration carries; policy/runtime resolves
- per-capability cost-model overrides + budget caps — declaration carries; enforcement runtime/budget layer
- per-capability telemetry enablement + verbosity — declaration carries; resolution future Telemetry spec
- per-source user trust overrides — entry carries override separately from source-authored trust; effective trust resolved by File 06
- registry-wide collision behavior (warn vs reject vs ask-on-override) — registry-owned
- discovery-capability enablement (`tool.search`, `mcp.search`, `extensions.search_registry`) — registry-owned
- alias deprecation enforcement (warn vs refuse on deprecated aliases) — registry-owned
- runtime-registration enablement (whether agent permitted to invoke `tools.register_custom`, `extensions.install`, `subsystems.register`, equivalent: off / ask-each-time / allowlist of trusted sources / allow) — declaration carries; resolution File 06 + future Extension/Plugin specs
- per-capability availability-predicate overrides (expose normally-hidden capabilities at own risk) — declaration carries; resolution future world-state spec
- platform-availability surface visibility (whether `unavailable_platform` entries in default discovery view or only advanced settings) — registry/surface-owned
- source-approval risk thresholds + defer/cancel fallback — entry carries relevant source state; resolution File 06
### 18.2 Settings-Key Convention `capability.settings-key-convention`
File 15's namespaced dotted-key convention: `capabilities.<id>.enabled`, `capabilities.<id>.permission_tier`, `registry.collision_policy`, `registry.source_approval_threshold`, `sources.<source_id>.trust_override`, etc. Plugin-supplied capabilities register own settings keys at install per future Extension/Plugin spec.
### 18.3 Boundary
File 05 stores declared+registry state for every configurable mechanism; policy+surface specs resolve runtime behavior. Settings whose mechanism depends on optional provider/platform capability MUST degrade gracefully when absent [`routing.settings`, File 03 §13]. Settings define intended product variation; MUST NOT become hidden hardcoded branches.

## 19. Explicit Rejections `capability.explicit-rejections`
- a parallel registry for any capability source — one registry, one contract regardless of source
- silent registration by hidden mechanisms — every registration observable through mutation event stream
- silent capability-id reuse for unrelated operations — id stability + version semver are the evolution contract
- declarations omitting touched-resource expressions, error vocabulary, replay class, or execution-semantic metadata
- prose-only touched-resource declarations for `access: write` or `access: read_write`
- handlers touching resources/invoking other capabilities outside declared scope ("capability leakage")
- source trust rewriting declared fields — registered declaration is contract; trust is separate metadata; effective tier computed by policy at call time
- argument-aware permission-tier expressed as duplicate id variants — use `TierResolver::Dynamic`
- model-request-only capability extension (injecting instructions without registering a capability) — agent-invokable behavior must register
- runtime registration bypassing user approval — user must explicitly approve registration invocation; no self-promote
- ids conflicting with namespace separators or source-prefix conventions
- declaring a closure-backed capability with `replay_class` above `not_replayable`
- coalescing internal sub-mode dispatch into separate registrations (a `file.read` branching text vs binary remains one capability — [`run.explicit-rejections`, File 04 §28])
- registry mechanisms hardcoding any §18 variations instead of exposing as configuration
- declarations whose `output_schema` returns inline content for outputs that should be durable blocks
- allowing settings/leases/trust upgrades to lower irreversible high-blast-radius operations below declared `permission_floor` (account deletion, destructive publish, force-push to protected branch, system shutdown, credential export are absolute lower bounds; no toggle/lease/trust may pierce)
- platform mismatch silently dropping a capability — platform-incompatible catalogued as `availability_status: unavailable_platform`, not absent
- treating capability versioning as implicit (mutating registered behavior without bumping `version`)
- treating registry state (enable, trust override, collision shadowing, backend binding) as a declaration mutation
- hidden delegation (invoking another capability without declaring it as dependent + without shared pipeline)
- treating `Capability` and "skill"/"workflow"/"instruction-pack" as same primitive — capabilities are typed executable contracts; skills are instruction modules; workflows are reusable orchestrations; each its own primitive with own registry [future Workflows, Templates, and Reuse spec]
- preserving `Action` as a parallel registry/adapter layer/alias for `Capability` — superseded; legacy `Action` shapes map into field set (§1), not a second primitive

## 20. Consequences for Later Specs `capability.consequences-for-later-specs`
Every later spec touching capabilities consumes `CapabilityDeclaration` + `RegisteredCapability` as operation primitive. Later specs (capability policy/approvals, tool surfaces/loading, blocks/block graph, artifacts/evidence, execution ledger/event stream, version graph/projections, retrieval/indexing, context assembly/compaction, memory, model strategy/provider integration, world model/state awareness, settings/profiles, storage/persistence, sync/portability, security/credentials, sandboxes/isolation, workspaces/materialization, per-surface specs [work surface contract, control rails, coder, web, data processor, teacher, GUI control, system agent], automation/triggers, workflows/templates, extension/plugin system, MCP/external integrations, UI shell/customization, quality control/validation, evaluation/benchmarking, telemetry/observability, runtime infrastructure/lifecycle, packaging/distribution) MUST:
- read declared metadata from `CapabilityDeclaration` (identity, schemas, touched-resource expressions, permission tier+floor, capability class, execution-semantic metadata incl replay class, validation paths, postconditions, source attribution, display, availability predicate, prerequisites, composition declarations, cost model, telemetry schema, backend descriptor)
- read live state from `RegisteredCapability` (enable state, availability status, resolved backend binding, source instance, trust state, lifecycle state, active aliases, collision state, diagnostics)
- record per-call resolved facts on `CapabilityInvocation` (resolved tier, resolved touched resources, resolved model-mediated classifications, selected backend binding instance, policy decision, ledger linkage, call outcome) — never on declaration
- treat registry as resolution surface + File 04 as execution surface — never embed parallel execution pipelines
- not introduce parallel capability metadata, parallel registries, or capability-like primitives bypassing this contract
- consume the trust/source/declaration boundary in §9 — trust influences policy, never the declaration
- consume the platform-as-availability-state model from §9.4 + §10 — platform-incompatible inspectable, not absent
- consume the collision-as-registry-state model from §14.1 — colliding declarations inspectable; active entry is registry state
Specific integration contracts stated in those files when written.
