# Capability Contracts and Registry

## Status

Canonical.

## Scope

This file defines:

- `Capability` as the typed, named, registered operation the system can perform
- the three layered views of every capability — `CapabilityDeclaration` (durable source-authored contract), `RegisteredCapability` (live registry entry), `CapabilityInvocation` (per-call record)
- the Capability Declaration field set — what every capability's source-authored contract carries
- input, output, and error schemas
- declared metadata that drives execution, policy, and surface decisions
- touched-resource description as machine-parseable typed expressions
- permission-tier declaration as part of the declaration
- replay-class declaration alongside execution semantics
- validation paths and postcondition declarations
- sourcing taxonomy (built-in, subsystem-owned, plugin-bundled, MCP-server, user-defined, external-API)
- capability identity, namespacing, aliasing, and versioning
- registry-state ownership of platform availability, enable state, source-collision resolution, backend binding lifecycle, and trust state
- the Capability Registry — operations, lifecycle, discovery, mutation
- composition primitives expressible at the contract level, including adapter capabilities

This file does not define:

- the policy engine, lease evaluation, approval UI, or runtime tier resolution mechanics — File 06 owns those
- tool-surface zones, model-request visibility, deferred loading, or capability-borrowing UX — File 07 owns those
- run lifecycle, execution graph, hook execution mechanics, or runtime input coercion mechanics — File 04 owns those
- routing or `RunIntent` selection — File 03 owns those
- block schema, artifact lifecycle, evidence model — Files 08 and 09 own those
- specific provider integration internals, rate-limit tracking, circuit-breaker mechanics, or polling intervals — File 17 owns provider concerns; the future MCP/External Integrations spec owns MCP and external tool-provider concerns
- specific subsystem-runtime designs (Coder, Web, Teacher, Memory, etc.) — the per-surface specs own those (Coder is File 27, Web is File 28; Memory is the substrate-service File 14; Teacher and the remaining surfaces are future)

## Source Resolution

This file resolves action, tool, MCP, plugin, command, workflow-step, and subsystem-operation material into one boundary: the canonical Capability contract and registry.

Resolved design:

- Capability is the single operation primitive; earlier Action-style interfaces are superseded by the full Capability contract.
- The registry stores immutable, versioned declarations with identity, schema, touched resources, effects, risk, preview, postcondition, and presentation metadata.
- Work surfaces, substrate services, plugins, MCP servers, workflows, scripts, and user-defined operations all register capabilities through the same contract.
- Capability declarations are metadata, not approval decisions, model-request surfaces, execution records, or UI widgets.
- Later policy, tool-surface, execution, automation, and plugin specs consume this contract instead of inventing parallel operation metadata.

## 1. Chosen Model

Anchor: `capability.chosen-model`

ATLAS3 has one Capability Registry. Every operation the system can perform — file read, shell exec, web fetch, browser click, memory recall, image generation, MCP-server tool, plugin tool, user-authored Wasm tool, external-API endpoint, automation invocation, sub-agent spawn, capability-discovery call — is declared as a `Capability` and registered in that registry.

A `Capability` exists in three layered views:

- `CapabilityDeclaration` — the durable, source-authored contract; identity, schemas, touched-resource expressions, permission-tier declaration, execution-semantic metadata (including replay class), validation paths, source attribution, observability declarations
- `RegisteredCapability` — the live registry entry that pairs a declaration with mutable registry state: resolved backend binding, source-instance reference, trust state, enable state, platform availability, lifecycle state, registration timestamp, diagnostics, alias activations, collision resolution
- `CapabilityInvocation` — the per-call record produced when the executor dispatches a capability through the `run.call-pipeline` (File 04 §8.2) pipeline; resolved tier, resolved touched resources, resolved model-mediated classifications, selected backend binding instance, policy decision, ledger linkage, call outcome

The same declaration drives:

- agent-tool exposure (the model sees the capability with its declared description and input schema)
- user-invocation paths (command palette, keyboard shortcuts, voice, menu)
- automation triggers (scheduled tasks, watches, webhooks invoke capabilities by id)
- MCP-server exposure (Atlas advertises selected capabilities to external MCP clients)
- workflow and DAG node references (workflow steps reference capabilities by id)
- approval routing (the policy layer reads the declaration's metadata)
- ledger attribution (the executor records the resolved capability id and version with each call)

There is no second registry, no per-subsystem bespoke capability list, and no `actions` vs `tools` split. The single Capability Registry is the source of truth for what the system can do.

`Capability` is the canonical noun. "Tool" is a synonym used informally where the agent-tool framing is dominant; the word does not denote a separate primitive. A capability may or may not be currently exposed as a tool surface item — surface zoning is a separate concern owned by File 07.

The `Capability` declaration defined here supersedes the `Action` interface in `atlas3-core/CONSTRAINTS.md` section 5. `Action` was a simplified prototype of the same invariant: one registered operation, multiple invocation paths. `Capability` fulfills that invariant with full contract metadata. The old `Action` shape maps into the declaration: `id` to identity (§3.1), `label` to display (§3.2), `shortcut` to `default_shortcut` (§3.2), `when` to `availability_predicate` (§9.2), `execute` to the backend descriptor (§3.12). `Action` is not preserved as a parallel registry, adapter layer, or alias.

Capabilities and policy compose: every declaration carries enough metadata for the policy layer to evaluate without re-inspecting the implementation. Capabilities and surfaces compose: every capability is identifiable by a stable id that the surface layer can load, hide, or borrow without changing the declaration.

## 2. `Capability`

Anchor: `capability.capability`

### 2.1 Definition

A `Capability` is a typed, named, registered, versioned operation the system can perform.

A `Capability` is not:

- a UI button or menu item (those are presentations of one or more capabilities)
- a conversation message kind (capability invocations produce typed blocks; the message is the transcript carrier)
- model-request text content (the model request may describe a capability, but the capability exists in the registry independent of any rendered request)
- a transient runtime concept (capabilities have durable identity and version)
- a single function pointer (the contract is the declaration; the resolved handler binding is one field of the registered entry)

A capability may or may not be currently exposed to an agent's tool surface, command palette, voice, or shortcut layer; presentation membership is owned by the surface layer (File 07) and does not change the underlying capability.

### 2.2 Required Properties (Declaration)

Every `CapabilityDeclaration` must have:

- a stable identity (§3.1, §13)
- a typed input schema (§4.1)
- a typed output schema (§4.2)
- a typed error vocabulary (§4.3)
- a touched-resource declaration as machine-parseable expressions (§6)
- a permission-tier declaration (§5)
- a capability class declaration (§3.5)
- the execution-semantic metadata declared in `run.call-pipeline` (File 04 §8.2) plus the per-field `classification_mode` directive (§3.6, §7)
- a `replay_class` declaration (§3.6, §7.3)
- a validation path (§8)
- a declared source (§9.1)
- a backend descriptor — a serializable reference the registry can resolve (§3.12, §10.4)
- declared display metadata sufficient for any invocation surface (§3.2)

A declaration lacking any of these fields is invalid and must be rejected at registration.

### 2.3 Boundary

The declaration defines the contract. The registered entry holds the runtime state. The handler implements the operation. The policy layer evaluates per call. The surface layer presents. The executor invokes. None of those layers may invent new contract semantics; they consume what the declaration provides and project the registry state accordingly.

A capability whose handler implementation needs to choose between input variants (binary vs text branches inside one read; different shell parsers inside one shell exec) handles those variants internally as one capability with sub-modes; this is not a separate capability call. The single registry entry covers the full input-shape distribution. Cross-capability composition is a higher-layer concern (§17).

## 3. Capability Declaration — Field Set

Anchor: `capability.declaration`

The declaration is the durable, source-authored contract. Every field is required unless explicitly marked optional. Field semantics are defined in the sections below.

The declaration is immutable for a given `(id, version)`. Updates go through `version` increment (§13.4). Registry-state mutations (enable/disable, source-collision shadowing, trust override, backend rebinding) live on the registered entry (§10), never on the declaration.

### 3.1 Identity Fields

- `id`: stable, namespaced string (§13.1)
- `version`: semantic version of the declaration (§13.4)
- `schema_version`: format version of the declaration itself, so the registry can normalize supported declaration formats during registration (§13.5)
- `aliases`: optional list of prior identities the capability has been known as, with declared deprecation timing (§13.3)

### 3.2 Display Fields

Anchor: `capability.display-fields`

Display fields use a localizable descriptor: a literal default carries the canonical text; an optional i18n key and translation reference enable localization. Built-in declarations should provide an i18n key alongside the literal default; dynamic declarations (MCP, plugin, external API, user-defined) must always provide safe literal defaults so the surface and discovery layers can render even before localization is wired.

- `name`: required default human-readable name
- `description`: required default model-facing and user-facing description
- `short_description`: required one-line default for compact discovery and the borrowable surface zone (per `run.zones`, File 04 §10.2)
- `i18n_key`: optional i18n key resolving to translated `name`/`description`/`short_description`
- `translations`: optional translation map or source localization reference
- `family`: capability family identifier (§13.2)
- `tags`: optional list of typed tags (`agent-invokable`, `voice-invokable`, `palette-invokable`, `destructive`, `experimental`, plus user-extensible tags)
- `icon_key`: optional icon identifier for surface presentation
- `default_shortcut`: optional keyboard shortcut for direct user invocation; user-overridable through settings

Display fields are declarative only. Surface presentation is owned by File 07 and the future UI specs. Display fields must not be hardcoded into surface logic — surfaces read from the declaration.

### 3.3 Schema Fields

- `input_schema`: typed input contract (§4.1)
- `output_schema`: typed output contract (§4.2)
- `error_vocabulary`: typed error variants (§4.3)

### 3.4 Touched-Resource Fields

- `touched_resources`: typed list of machine-parseable resource expressions describing every resource the capability may read or write (§6)

### 3.5 Permission and Policy Fields

Anchor: `capability.permission-policy-fields`

- `permission_tier`: `TierResolver::Static(Tier)` or `TierResolver::Dynamic(resolver_id)` (§5)
- `permission_floor`: optional minimum tier that global settings cannot lower (§5.4)
- `capability_class`: `InternalAnalysis`, `ActionExternal`, `UserArtifact`, or `Unknown`; policy-critical class consumed by File 06 for default template selection and trust escalation. Tags may mirror this value for discovery, but tags are not the source of truth.
- `approval_template_id`: optional identifier for the default approval-policy template used when policy escalates (template definitions live in File 06)
- `data_sensitivity`: default sensitivity class for events and outputs the capability emits (`Public`, `Sensitive`, `Secret`); per `run.event-stream` (File 04 §23.2)

### 3.6 Execution-Semantic Fields

Anchor: `capability.execution-semantic-fields`

These fields are declared in `run.call-pipeline` (File 04 §8.2) and referenced here as part of the declaration:

- `concurrency`: `ConcurrencySafe`, `SelfParallel`, `Exclusive`
- `reversibility_class`: `none`, `compensable`, `reversible`
- `idempotent`: bool
- `preview_mode`: `none`, `dry_run`, `structural_preview`, `diff_preview`
- `partial_output_meaningful`: bool
- `cooperative_stop_deadline_ms`: u64 with policy default
- `sibling_abort_on_failure`: bool
- `resume_on_restart`: bool with optional resume handler reference

Plus declaration-owned additions:

- `terminates_sequence`: optional bool — when true, signals to batch-execution callers that this capability changes external state in ways that invalidate queued sibling calls; used for safe sequencing of state-mutating capabilities
- `replay_class`: `deterministic_replayable`, `snapshot_replayable`, `effect_replayable_with_policy`, `not_replayable` (§7.3)
- `classification_mode`: per-field directive that names how each of the above fields is determined — `Deterministic` (declared once, fixed) or `ModelMediated { policy_model_request_template_id }` (a designated model classifies per call against a configured policy model-request template) — applied to fields that cannot be statically declared for all calls (`reversibility_class` for shell-style capabilities). The declaration names the mode; the per-call resolved value lives on the invocation record (§11).

### 3.7 Validation Fields

- `input_validators`: declared list of pre-execution validation steps (§8.1)
- `postconditions`: declared list of post-execution checks (§8.2)
- `stale_state_revalidation`: optional declaration of the stale-state revalidation pattern (§8.3)

### 3.8 Sourcing Fields

- `source`: typed `CapabilitySource` (§9.1) — names which source kind the declaration came from and carries source-version identifiers (`plugin_version`, `server_version`, definition file hash) as immutable metadata of the source artifact

Trust state and registration timestamp are not declaration fields; they live on the registered entry (§10) because they are mutable runtime classifications.

### 3.9 Availability Fields

Anchor: `capability.availability-fields`

- `availability_predicate`: declarative requirements and blockers evaluated against world-model state (§15.2)
- `platforms`: optional platform constraint list (`windows`, `macos`, `linux`, `mobile`, etc.); a capability whose platforms list omits the current platform is catalogued as `availability_status: unavailable_platform` on the registered entry rather than absent (§9.4, §10)
- `prerequisite_capabilities`: optional list of scoped prerequisites that must have been invoked previously before this capability becomes invocable (§15.3)

The `enabled` flag is registry state, not a declaration field; it lives on the registered entry (§10). The settings system scopes enable state per workspace, conversation, or globally without mutating the declaration.

### 3.10 Composition Fields

Anchor: `capability.composition-fields`

- `dependent_capabilities`: optional list of capability ids this capability may invoke internally — for transparency to policy and surface layers (§17.1). Declaration is not an execution bypass; declared dependents are still invoked through the shared capability-call pipeline.
- `output_block_kinds`: declared block kinds the capability produces (§17.2)
- `output_event_kinds`: declared event kinds the capability emits (§17.2)

### 3.11 Cost and Telemetry Fields

- `cost_model`: optional cost-prediction declaration (per-call expected cost; per-token, per-byte, per-second, or fixed)
- `telemetry_schema`: declared event types the capability emits beyond the canonical execution events; File 20 extends the schema, the canonical declaration names the minimum

### 3.12 Backend Descriptor

Anchor: `capability.backend-descriptor`

- `backend`: serializable backend descriptor — kind plus the parameters the registry needs to resolve a live binding at registration (`ServiceMethod { service_id, method_name }`, `Wasm { module_id, entry_point }`, `Shell { program, args, cwd, env_overlay }`, `McpProxy { server_id, remote_tool_name }`, `HttpEndpoint { url_template, method, auth_ref }`, `Closure { closure_id }`)

The descriptor is declarative. The resolved live binding (the actual service method handle, loaded Wasm module instance, MCP client adapter, HTTP client, in-process closure) is registry state on the registered entry (§10.4). Handlers are never serialized into declarations; the descriptor names enough for the registry to bind them at registration time. Closures, by definition, are not portable across processes and therefore declarations using `Closure { ... }` must declare `replay_class: not_replayable` (§7.3).

### 3.13 Boundary

The declaration field set above is the canonical minimum. File 20 and File 06 may attach additional metadata (telemetry attribution beyond the minimum, per-capability rate-limit scopes, capability-specific configuration). Such extensions must be additive and must not change the meaning of fields named here.

The declaration is wire-stable through `schema_version`. Where a registry encounters a supported earlier declaration format, it normalizes the declaration to the current format at registration. Because ATLAS3 is local-only with no existing user base or persisted third-party declarations, no migration framework is required at present (per project constraints); when external declarations begin to persist, normalization-on-load applies and is a concern of the registry, not of the caller.

## 4. Schemas

Anchor: `capability.schemas`

### 4.1 `input_schema`

Anchor: `capability.input-schema`

`input_schema` is a JSON Schema describing the capability's input arguments. Required:

- every input parameter named, with a declared type, default value where applicable, validation constraints, and a human-readable description
- required parameters distinguished from optional parameters
- enums declared explicitly with their allowed values
- nested objects, arrays, and discriminated unions supported
- input parameter aliases declared in the schema's metadata when alternative names are accepted (used when MCP- or LLM-supplied arguments commonly use synonyms; the registry resolves aliases before calling validators)

The wire format is JSON Schema; in capability-author code, generation from typed source structs is recommended (using a Rust-side schema generator). The wire format is the contract; the source-code form is an authoring convenience.

`input_schema` must be sufficient for:

- the model to emit a syntactically valid call from the description alone
- the registry to validate inputs against the schema before dispatch
- the surface layer to render input forms when the capability is user-invoked
- the policy layer to inspect arguments for tier resolution and lease scope matching
- the ledger to record inputs in a typed, replayable form

Inputs are validated against `input_schema` before execution. The runtime decision of how to handle schema mismatches (strict reject, safe coercion, model repair, user correction) is execution policy and belongs to File 04 / the future capability-runtime spec; the declaration's role is to require that schemas exist and are honest.

### 4.2 `output_schema`

`output_schema` is a JSON Schema describing the capability's output value. Required:

- the principal return shape declared exhaustively
- when the output is a polymorphic union, every variant declared with its discriminator
- typed sub-objects for handles, references, citations, and any structured output the capability produces
- the relationship between produced blocks and the return value made explicit (whether the value contains a block id, the block content inline, or a reference to artifacts)

Capabilities whose output is principally one or more durable blocks (file edits, artifact creation, document edits) declare a return value that references the produced block ids, not the inline content. Inline content in returns is reserved for short structured data and small text outputs.

### 4.3 `error_vocabulary`

Anchor: `capability.error-vocabulary`

`error_vocabulary` declares the typed errors the capability may produce. Each variant has:

- a stable kind identifier (string)
- declared structured fields (typed)
- a `recoverable` boolean — whether the agent loop should attempt recovery in-band (per `run.denial-is-in-band`, File 04 §8.3 in-band denial)
- a `retryable` classification — whether the same call may be retried as-is, retried with a backoff, or must not be retried
- a human-readable message template

Errors that flow as in-band tool results to the agent loop must conform to this vocabulary. Errors that escape the capability boundary as `AppError` cross-boundary failures (per `core.typed-errors`, File 01 §6.9) must map to declared variants in `error_vocabulary` plus the system's typed-error envelope.

A capability must not emit ad-hoc error kinds; every produced error must correspond to a declared variant. Adding an error kind requires a registry update and follows the versioning rules in §13.4.

## 5. Permission-Tier Declaration

Anchor: `capability.permission-tier-declaration`

### 5.1 Tier Set

The permission-tier set is canonical (`run.approval-during-execution`, File 04 §11): `Denied`, `ReadOnly`, `WorkspaceWrite`, `UserApproval`, `Unrestricted`, with the `typed-confirmation` mode as a variant of `UserApproval`.

### 5.2 `TierResolver`

Anchor: `capability.tier-resolver`

`permission_tier` is declared as one of:

- `TierResolver::Static(Tier)` — the tier is fixed and known at registration time; no per-call evaluation is needed; this is the default
- `TierResolver::Dynamic(resolver_id)` — the tier depends on the specific arguments at call time; a registered argument-aware resolver examines the input arguments and current world state to return a tier

The dynamic case exists because some capabilities are inherently argument-sensitive: a `file.edit` whose path is inside the workspace is `WorkspaceWrite`, the same capability called with a path outside the workspace is `UserApproval`. Splitting one capability into many id variants for each tier is rejected; the resolver pattern keeps the registry coherent.

Argument-aware resolvers are themselves registered, named, and inspectable. A capability declares the resolver by id; the resolver's behavior must be deterministic given the same arguments and world-model snapshot. Resolvers are not capabilities (they do not execute work) but they are registry-managed declarations; the resolver registry is colocated with the Capability Registry.

The resolver declaration belongs to the declaration. The resolved tier for a given call belongs to the invocation record (§11). File 06 computes the final effective tier and approval path.

### 5.3 Tier Composition With Leases

The capability's declared tier is the baseline. The policy layer may grant a `Lease` that lowers per-call friction (an `AlwaysAllow` lease for a `UserApproval` capability auto-resolves the next call within the lease scope). Leases cannot escalate above the declared tier, cannot bypass `Denied`, and cannot lift `typed-confirmation`. Tier composition follows the lease-scope hierarchy in `run.approval-during-execution` (File 04 §11); contradictions across scope levels surface as policy errors, not silent wins.

### 5.4 `permission_floor`

Anchor: `capability.permission-floor`

A capability may declare a `permission_floor` — a minimum tier that global settings (including `agent.unrestricted_mode`) cannot lower. Used for capabilities whose risk is high enough that no global toggle should make them frictionless: account deletion, destructive publish, force-push to a protected branch, system shutdown, credential export, irreversible publishing operations.

`permission_floor` and `permission_tier` are distinct declarations. The floor names the minimum; the tier names the default. The runtime tier for a call is the higher of (a) the resolved `permission_tier`, (b) the `permission_floor`, (c) any narrower tier imposed by an active scope-level policy override.

### 5.5 Boundary

The declaration carries tiers, floors, and resolvers. The policy layer evaluates them against active leases, scope-level overrides, source trust, and approval templates, and returns the runtime decision. File 05 owns the declaration and the registered trust state; File 06 owns the evaluation.

## 6. `touched_resources`

Anchor: `capability.touched-resources`

### 6.1 Required Shape

`touched_resources` is a typed list. Each entry declares:

- `class`: the resource class — drawn from the canonical set in §6.2 or from a registered extension class (§6.3)
- `access`: the access mode (`read`, `write`, `read_write`, `invoke`, `observe`, `none`)
- `expression`: a machine-parseable typed expression that resolves the concrete resource scope; not a prose string

Touched resources are declared as expressions, not as concrete enumerations of every value the capability might touch. Argument-dependent expressions reference input-schema field paths by name (`args.path`, `args.command`, `args.url`) so policy can resolve concrete resources from invocation arguments without inspecting handler internals. Static expressions name fixed resources directly.

Prose-only resource declarations are invalid for any capability with `access: write` or `access: read_write`. Read-only capabilities may declare prose clarifications alongside expressions for documentation purposes; the expression remains the contract.

### 6.2 Canonical Resource Classes

The canonical top-level resource classes are a closed enumerable set:

- `filesystem`
- `network`
- `process`
- `env`
- `credential`
- `setting`
- `model-call`
- `browser-session`
- `ui-element`
- `sub-agent`
- `scheduler`

These cover the resource kinds the canonical execution, policy, isolation, settings, and ledger layers reason about. The closed set keeps policy-side resource matching, lease-scope inclusion checks, and conflict detection deterministic.

### 6.3 Extension Resource Classes

Anchor: `capability.extension-resource-classes`

Subsystems and plugins may register additional resource classes through a registered subsystem-extension capability (per §16.2 runtime mutation). An extension class entry carries an `extension_id` namespacing the class, a structured scope grammar, and a containment predicate so policy can decide lease-scope inclusion without inspecting subsystem internals. Examples a subsystem might register: `video-feed` for a vision subsystem, `ble-device` for an IoT plugin, `vector-index` for a retrieval subsystem.

Extension classes are first-class once registered: leases, audit, conflict detection, and routing reason about them the same way they reason about canonical classes. The registration itself is a capability call and is subject to policy and proposal-first rules (§16.2).

### 6.4 Resource Expressions

Anchor: `capability.resource-expressions`

Expressions are structured terms over the input schema and registered ambient values (workspace root, current process group id, run id, conversation id, current credential vault keys). Indicative shapes:

- static: `network:{ host: "api.openai.com" }`
- argument-bound: `filesystem.path(args.path).within(workspace_root)`
- derived: `shell.parse(args.command).filesystem_writes`
- external account: `connector.account(args.account_id).mailbox(args.mailbox_id)`
- setting key: `setting.key(args.key).scope(args.scope)`
- process group: `process.group(run_id)`

File 05 owns the canonical resource-expression grammar used in `CapabilityDeclaration.touched_resources`; this file requires that expressions are machine-parseable, that argument-bound expressions reference `args.*` field paths by name, and that the expression resolves to the concrete resources policy must check. File 06 consumes resolved expressions for policy evaluation, containment, lease matching, and approval decisions; it does not define the grammar.

### 6.5 Purpose

Machine-readable touched-resource expressions make the declaration inspectable by:

- the policy layer for lease-scope matching (a workspace-scope lease covers capabilities whose resolved touched-resource scope is contained in the workspace)
- the audit ledger for forensic reconstruction (what resources did this run touch, derived from the resolved expressions of every executed capability)
- the routing layer for capability selection (a request requiring web access selects only capabilities whose touched-resource expressions include `network`)
- the user for explicit understanding of what a capability will affect before approval (the surface previews resolved resources, not just classes)
- replay for predicted-vs-observed comparison (predicted resources from the expression, observed resources from the runtime sandbox)

Touched-resource declarations must be honest and complete. A capability that quietly reads credentials, mutates env vars, or contacts hosts outside its declared expression is an Explicit Rejection (§19).

### 6.6 Boundary

The declaration names what the capability may touch. The policy layer resolves expressions against arguments to produce the concrete resource set per call (§11). The runtime sandbox enforces what is actually touched (per `run.child-runs-multi-agent-work`, File 04 §16). A declared scope that the runtime cannot enforce is still the contract; the runtime catches violations and emits typed errors.

## 7. Execution-Semantic Metadata

Anchor: `capability.execution-semantic-metadata`

The fields named in §3.6 are settled in `run.call-pipeline` (File 04 §8.2) and are part of the declaration. This section names declaration-owned additions:

### 7.1 `terminates_sequence`

A capability may declare `terminates_sequence: true` when its execution is known to invalidate any in-flight sibling calls within the same dispatch batch. Browser-state-changing actions (navigation, click on a link), sandbox-state-changing operations, and other capabilities that change the world the siblings observe must declare this flag.

The executor honors `terminates_sequence` by aborting queued siblings in the same batch when the capability completes. Combined with the runtime detection mechanisms in `run.failure-in-parallel-work` (File 04 §15.3), this provides defense-in-depth against silent corruption from out-of-order parallel execution.

### 7.2 `classification_mode`

Anchor: `capability.classification-mode`

For declaration fields where a single static value is not meaningful (a `shell.exec` cannot declare one `reversibility_class` for all bash commands), the declaration carries a per-field `classification_mode`:

- `Deterministic` — the declared static value applies for every call
- `ModelMediated { policy_model_request_template_id }` — a designated classifier model evaluates the specific call against the configured policy model-request template and returns a per-call value; the template is registry-managed and inspectable

`classification_mode` is per-field, not per-capability. A capability may declare `reversibility_class` as model-mediated while declaring `concurrency` as static. The model-mediated mode pays an extra model-call cost per dispatch and is therefore used selectively; the default is `Deterministic`.

The declaration names the mode. The per-call resolved value (the tier returned by `Dynamic` resolution, the class returned by `ModelMediated` classification) lives on the invocation record (§11), not the declaration.

### 7.3 `replay_class`

Anchor: `capability.replay-class`

Every declaration carries a `replay_class`:

- `deterministic_replayable` — same inputs and same referenced state produce same result; pure local reads and pure transforms qualify
- `snapshot_replayable` — replay requires recorded snapshots or materialized observations the executor captured during the original call (file content at a path, web-page snapshot, accessibility-tree fingerprint); without the snapshot, replay is undefined
- `effect_replayable_with_policy` — the call causes external effects (sending an email, calling a payment API, mutating a database) and may be reissued only through policy; the contract names the policy hook the replay must consult before reissuing
- `not_replayable` — cannot be reproduced across process/device/session boundaries; closure-backed capabilities, capabilities depending on transient runtime handles, and inherently uncontrolled side-effects fall here

The author classifies based on the call shape, not on per-call state — whether the file referenced by `args.path` still exists at replay time is a snapshot/policy concern, not a declaration concern. The replay layer (per `run.execution-ledger`, File 04 §23.1 and File 10) consumes `replay_class` to decide what evidence to record, what to require for replay, and what to refuse to reproduce.

Closure-backed declarations (§3.12) must declare `replay_class: not_replayable`. Declaring otherwise is an Explicit Rejection (§19).

### 7.4 Boundary

These fields drive execution behavior. They are declared by the capability author at registration; they are read by the executor and ledger at dispatch and replay. Any change to an execution-semantic field after registration follows the versioning rules (§13.4): bumping `version` and registering the new declaration alongside the old.

## 8. Validation and Postconditions

Anchor: `capability.validation-postconditions`

### 8.1 `input_validators`

Anchor: `capability.input-validators`

Beyond schema validation against `input_schema`, a capability may declare additional pre-execution input validators:

- structural validators (parsed-AST checks for shell commands, regex pattern compilation for grep tools, JSON-schema verification for capabilities whose input contains a sub-schema)
- workspace-boundary validators (path normalization, symlink resolution, workspace-root containment)
- argument-coercion steps (string-to-number, empty-string-to-null, alias-name resolution) declared as part of the input contract for tolerance to LLM output noise
- registered hook validators (the quality-control validators in `run.hook-integration` (File 04 §23.3) attach at the `ToolCallProposed` boundary; the capability declares which hook categories it expects)

Validators run in declared order. A validator may return `valid`, `invalid_with_correction`, or `invalid`. The executor honors corrections (where the validator supplies a normalized argument), records the correction in the ledger, and proceeds. An `invalid` result without correction halts dispatch and produces a typed validation error in-band to the agent.

The policy for how aggressively the runtime should attempt coercion and repair on schema mismatches (strict reject vs safe coerce vs model repair vs user correction) is execution policy and lives in File 04 / the future capability-runtime spec; the declaration's role is to require validators exist, name their order, and surface their corrections.

### 8.2 `postconditions`

A capability may declare structural postconditions: deterministic checks the runtime evaluates after execution to confirm declared effects. Declared postconditions:

- declared output-schema conformance — a structural validation of the produced output against `output_schema`
- declared resource-state checks — for capabilities that promised to produce a file, the existence of the file at the declared path; for capabilities that promised to write to a database, the row count delta
- declared ledger evidence — referenced through `run.termination` (File 04 §22)'s deterministic forgery guard; a capability whose contract required action cannot terminate `completed` without ledger evidence of action

Postconditions are deterministic by default. The configurable completion-verification hook surface in `run.termination` (File 04 §22) supports model-mediated semantic checks (whether the run satisfied the user's intent) at user-configured cadence; the deterministic floor declared in `postconditions` is the canonical minimum.

A failing postcondition produces a typed postcondition-failure variant in `error_vocabulary` and may trigger declared compensation (per `reversibility_class`).

### 8.3 `stale_state_revalidation`

For capabilities whose mutation depends on a prior observation (file edit after a read, GUI click after a tree snapshot, browser action after a page snapshot), the declaration carries the stale-state revalidation pattern from `run.call-pipeline` (File 04 §8.2):

- the prior-observation metadata the capability records (file mtime and content hash, accessibility-tree fingerprint, DOM snapshot id)
- the `expected_*` fields the capability accepts on its input schema (the caller must supply the recorded observation metadata)
- the typed `StateChangedSinceObservation`-class error variant the capability returns when the metadata mismatches current state

The executor enforces nothing additional; the capability author is responsible for revalidating before mutating. The declaration makes the revalidation pattern visible and inspectable.

### 8.4 Boundary

Validation belongs to the capability and the registered validator hooks. Approval belongs to the policy layer. Postcondition reporting belongs to the ledger (per `run.ledger-events-commits`, File 04 §23 and File 10). Capability authors do not implement their own approval flow; they implement validation and rely on the shared policy layer.

## 9. Sourcing

Anchor: `capability.sourcing`

### 9.1 `CapabilitySource`

Anchor: `capability.capability-source`

Every declaration names its source. The source is one of:

- `Builtin` — compiled into the application binary; ships with every install; cannot be unregistered without an update
- `Subsystem { subsystem_id }` — owned by a registered subsystem (work surface or substrate service such as Memory, Routing, Context Assembly, Retrieval, Knowledge Indexing, Settings, Evaluation, Policy); registered when the subsystem registers; loaded as part of the subsystem. A subsystem is any registered work surface or substrate service that owns capabilities. New subsystems may be added or removed through the subsystem-registration capability (proposal-first per §16.2), so subsystem composition itself is first-class and customizable.
- `Plugin { plugin_id, plugin_version }` — bundled in a plugin (per `core.extension-planes`, File 01 §6.14 extension planes; see the future Extension and Plugin System spec); registered when the plugin loads; unregistered when the plugin unloads
- `McpServer { server_id, server_uuid, server_version }` — sourced from an external Model Context Protocol server; registered when the server connects; unregistered when the server disconnects
- `Api { api_name, api_definition_path }` — sourced from a user-authored external-API TOML or equivalent declarative definition; registered when the definition file is loaded
- `UserDefined { backend, scope }` — registered at runtime by the user or, with explicit user approval, by the agent through a capability-registration capability; backend is `Wasm` or `Shell` (per `run.interruption-pause-cancellation`, File 04 §17 self-modification); scope is `conversation`, `workspace`, or `global`

A capability has exactly one source. A capability cannot be both built-in and plugin-bundled; a plugin that wishes to override a built-in capability must register a distinct id and the user must explicitly select the override (§14).

### 9.2 Trust and Source-Approval Flow

Anchor: `capability.trust-source-approval-flow`

Trust is registry state, not a declaration field. The declared source carries source-version identifiers; the registered entry (§10) holds:

- `declared_trust_hint`: the trust class the source asserts (for plugins, the plugin manifest's claim; for MCP servers, the configured server trust)
- `registry_trust_override`: any explicit user override applied through settings
- `effective_trust`: `System` (Builtin/Subsystem), `Verified`, `Community`, `Unverified`, or `User` (UserDefined/Api), computed from the hint and any override

Trust does not rewrite declared fields. A capability declaring `permission_tier: WorkspaceWrite` from a `Community`-trust MCP server retains the declared `WorkspaceWrite` in the registered entry. The policy layer reads declaration plus trust and resolves an effective tier of at least `UserApproval` by default for `Community` and `Unverified` sources; the user may explicitly upgrade trust per source. This keeps declarations honest and lets policy change when trust settings change without mutating capability versions.

When a source registers (plugin install, MCP server connect, external-API definition load, user-defined capability registration) the runtime surfaces the declared permission tiers, declared touched resources, declared replay class, declared trust hint, source provenance, and computed source-risk summary before activation when policy requires review. The user accepts declared defaults, configures policy, denies the source, explicitly defers source-level policy to per-call fallback, or cancels registration. Review triggering is risk-summary based; declared tier is one input, not the whole rule. The exact trigger and fallback behavior are owned by File 06 and user settings.

### 9.3 Sourcing Equivalence

Anchor: `capability.sourcing-equivalence`

Capabilities from every source enter the same registry through the same contract. Once registered, the source distinction surfaces as metadata: the agent sees the same agent-tool list whether the underlying source is `Builtin` or `McpServer`. The policy layer reads the same declaration fields. The ledger records the resolved capability id with its source attached.

There is no parallel "MCP tool list," "plugin tool list," or "user-tool list." A surface or settings UI may filter by source for clarity, but the registry is one.

### 9.4 Platform Conditioning

Platform mismatch is registry availability state, not a registration filter. A declaration whose `platforms` list omits the current OS still registers; the registered entry carries `availability_status: unavailable_platform` and no resolved backend binding. Such capabilities are visible in settings, plugin inspection, dependency diagnostics, automation validation, and cross-device transparency, but are not invocable on the current platform.

A surface or discovery layer may hide unavailable capabilities from default views; advanced settings can reveal them so users understand why an automation that works on one device does not work on another. Equivalent semantic capabilities for different platforms (a Windows registry-write capability and a macOS plist-write capability) may share the same family and be selected by the routing layer based on the platform; capability ids remain platform-disambiguated.

A capability that is registered as `Available` on Windows must not throw `PlatformUnsupported` on Linux; the executor never has to discover the mismatch by crashing a handler. The registered entry on Linux is `unavailable_platform` from registration onward.

## 10. `RegisteredCapability` — Registry State

Anchor: `capability.registered-capability`

### 10.1 Definition

A `RegisteredCapability` is the live registry entry produced when a `CapabilityDeclaration` is admitted. It pairs the declaration with mutable registry state:

- `declaration`: the registered `CapabilityDeclaration` (immutable for the version)
- `registered_at`: timestamp of registration
- `enabled`: runtime enable flag distinct from existence; settings-scoped per workspace, conversation, or globally (§16.3)
- `availability_status`: `Available` | `UnavailablePlatform` | `UnavailableHandler` | `UnavailablePrerequisite` | `Disabled` | `Shadowed`
- `resolved_backend_binding`: the live resolved handler reference (service-method handle, loaded Wasm module instance, MCP client adapter, HTTP client, in-process closure); never serialized into the declaration
- `source_instance`: the registered source-instance reference (which loaded plugin, which connected MCP server, which loaded API definition file)
- `trust_state`: `{ declared_trust_hint, registry_trust_override, effective_trust }` (§9.2)
- `lifecycle_state`: `Loading` | `Active` | `Updating` | `Disabled` | `Unregistering`
- `active_aliases`: the alias entries currently honored for lookup (per §13.3 declared aliases with their version range and deprecation timing)
- `diagnostics`: registration diagnostics, last-error trace, last-successful-resolve timestamp, registration-failure reason if any
- `collision_state`: `Active` | `Shadowed { shadowed_by }` | `Shadowing { shadows }` for capabilities involved in source-collision resolution (§14)

### 10.2 Mutation Rules

Registry state mutates. Settings changes, plugin updates, MCP server reconnection, platform changes, and trust overrides update the registered entry without changing the declaration. A declaration's `(id, version)` is immutable for the registered entry's lifetime; producing a new declaration version produces a new registered entry that supersedes the old (per §16.4 update semantics).

Mutations emit registry events (§12.2) so surfaces, settings, and the capability-discovery projection react.

### 10.3 Inactive Entries Remain Inspectable

Disabled, shadowed, and `unavailable_platform` entries remain in the registry as inspectable catalogue records. They are not invocable but they appear in settings, diagnostics, plugin inspection, and dependency analysis. A user can see why a capability is unavailable, when it became unavailable, and what would re-enable it. Removal from the catalogue happens only through `unregister` (§16.5).

### 10.4 Backend Binding Lifecycle

Anchor: `capability.backend-binding-lifecycle`

The declaration carries the serializable backend descriptor (§3.12). The registered entry carries the resolved live binding. Each backend kind has its own resolution and lifecycle rules:

- `ServiceMethod` — resolved against the Rust service registry (static-typed services compile-time wired; dynamic services runtime-registered for plugin-loaded capabilities); persists across restarts when the service persists
- `Wasm` — resolved against the loaded Wasm module registry; module sandboxed per `run.child-runs-multi-agent-work` (File 04 §16); persists across restarts when the module is re-loaded
- `Shell` — resolved against a configured subprocess invocation; sandboxed per the shell-operations spec
- `McpProxy` — resolved against the active MCP client pool; client invokes the remote tool through MCP and adapts the response; deregisters when the MCP server disconnects, re-resolves on reconnect
- `HttpEndpoint` — resolved against the HTTP client; auth comes from the credential vault by reference (never inline secrets)
- `Closure` — for runtime-registered closures (test fixtures, in-process plugins); not serializable; deregisters at process exit; declarations using `Closure` must declare `replay_class: not_replayable` (§7.3)

The declaration is the contract. The binding is registry state. Diagnostics about binding failure (handler unresolved, MCP server unreachable, Wasm module load error) live on the registered entry; they do not invalidate the declaration.

## 11. `CapabilityInvocation` — Per-Call Record

Anchor: `capability.invocation-record`

A `CapabilityInvocation` is the per-call record produced when the executor dispatches a capability through the `run.call-pipeline` (File 04 §8.2) pipeline. The invocation record is owned by File 04 (proposal/execution) and File 10; File 05 names the schema only to draw the layer boundary and to identify which facts are per-call resolved (and therefore not declaration fields).

Per-call resolved facts that are not declaration fields:

- the resolved `(id, version)` of the capability
- invocation arguments (after schema validation and any declared input-validator corrections per §8.1)
- resolved permission tier (the value returned by `TierResolver` per §5.2)
- resolved touched resources (the concrete resources produced by evaluating typed expressions against the arguments per §6)
- resolved model-mediated classifications (per-field values produced by `ModelMediated { policy_model_request_template_id }` classifiers per §7.2)
- selected backend binding instance (which MCP server connection, which Wasm module instance) at the moment of dispatch
- policy decision (lease consulted, approval mode chosen, contradiction-checks performed) — per File 06
- proposal id, ledger entry id, event sequence
- call outcome (typed result, typed error, blocks produced, events emitted)

The invocation record is durable in the ledger (per `run.execution-ledger`, File 04 §23.1). Replay reads `(declaration_version, resolved_backend_binding_id_at_time)` from the invocation record; it does not infer them from current registry state.

## 12. Capability Registry

Anchor: `capability.capability-registry`

### 12.1 Operations

The Capability Registry must support:

- `register(declaration) -> Result<RegisteredCapability, RegistrationError>` — admit a new capability
- `unregister(id) -> Result<(), RegistrationError>` — remove an existing capability (typically on plugin unload, MCP disconnect, user uninstall)
- `update(declaration) -> Result<RegisteredCapability, RegistrationError>` — replace an existing capability with a new version (subject to compatibility rules in §13)
- `enable(id, scope)` and `disable(id, scope)` — toggle the enabled flag without changing existence (§10, §16.3)
- `get(id) -> Option<RegisteredCapability>` — direct lookup
- `lookup_alias(name) -> Option<RegisteredCapability>` — alias-aware lookup
- `list(filter) -> Vec<RegisteredCapability>` — enumerate registered entries, optionally filtered by family, source, tag, platform, enable state, availability status, or availability predicate match
- `available(world_state) -> Vec<RegisteredCapability>` — return entries whose `availability_predicate` matches the supplied world-model snapshot and whose `availability_status` is `Available` and whose `enabled` is true
- `find_by_shortcut(shortcut)` — for keyboard-driven invocation
- `subscribe(events) -> Stream<RegistryEvent>` — registry mutation event stream
- `resolve_for_invocation(id, args, world_state) -> Result<InvocationDescriptor, ResolutionError>` — resolve identity, version, alias, source-collision active winner, and prepare the invocation descriptor the executor consumes

The registry resolves; the executor invokes. The registry owns: registration, lookup, version resolution, alias resolution, source-collision active-entry selection, declaration validation, availability projection, and backend-binding resolution. The executor (`run.call-pipeline`, File 04 §8.2) owns: proposal, approval, tool-call execution, hooks, cancellation, streaming, ledger entries, and result blocks. The registry does not own an `execute` primitive; convenience facades that combine the two are explicit delegations to the execution runtime, not registry-owned execution.

### 12.2 Events

Anchor: `capability.events`

Registration emits `CapabilityRegistered`, unregistration emits `CapabilityUnregistered`, update emits `CapabilityUpdated`, enable/disable emits `CapabilityEnabledChanged`, registry-state mutations (binding rebound, trust override applied, collision resolved, availability changed) emit `CapabilityRegistryStateChanged`. Subscribers (surfaces, settings, the capability-discovery projection for agents) react to these events.

### 12.3 Registration Mechanics

Registration is declarative and idempotent. A subsystem, plugin, or runtime registration capability calls `register(declaration)` with a complete contract. The registry:

1. Validates the declaration (every required field present, schemas well-formed, identifiers conform to namespacing rules, source declaration valid, expressions parseable for write-capable touched-resource entries)
2. Checks for id collision and applies the collision policy (§14.1)
3. Resolves the backend binding (the named service, Wasm module, MCP server, etc. exists)
4. Normalizes the declaration to the current `schema_version` if needed (§13.5)
5. Computes registry state (registered_at, declared_trust_hint, source_instance reference)
6. Inserts the registered entry into the live registry
7. Emits `CapabilityRegistered`
8. Updates derived projections (capability-discovery for the agent, command-palette index, voice-command map, automation trigger-target list)

Registration may fail with typed errors: `IdentifierCollision`, `InvalidDeclaration`, `HandlerUnresolved`, `SchemaTooNew`, `SourceConflict`, `UnparseableResourceExpression`. Failed registrations leave the registry unchanged.

Unregistration runs in reverse: emit pre-unregister event, transition lifecycle to `Unregistering`, allow in-flight calls to complete, drop projections, remove the registered entry, refuse new calls.

## 13. Identity, Namespacing, Versioning

Anchor: `capability.identity-namespacing-versioning`

### 13.1 `id`

Anchor: `capability.id`

A capability id is a stable, namespaced, lowercase, dotted string. The first segment names the source class; the remaining segments name the family and operation:

- Built-in / subsystem capabilities: `<family>.<operation>` (e.g., `file.read`, `shell.exec`, `web.fetch`, `memory.recall`, `gui.click`, `teacher.explain`, `data.pdf.extract_text`)
- Plugin-bundled capabilities: `plugin.<plugin_id>.<operation>` (or the plugin's declared namespace if it ships with one — `<plugin_namespace>:<operation>` is also accepted; the registry stores both forms and resolves equivalently)
- MCP-sourced capabilities: `mcp.<server_id>.<remote_tool_name>` (the server_id is the user-visible server name, not the server UUID; the UUID is in the registered source instance)
- Registry-bridged external API capabilities: `api.<service_name>.<endpoint_id>`
- User-defined capabilities: `custom.<scope>.<tool_id>` where scope is `conversation`, `workspace`, or `global`

Ids are case-insensitive at lookup (registered case is preserved for display) and may not contain whitespace, slashes, or characters that conflict with the namespace separators (`.`, `:`, `__`). The registry rejects ids that do not conform.

### 13.2 `family`

Anchor: `capability.family`

`family` is a free-form identifier that groups related capabilities for surface organization, routing, and policy templating. Common families: `file`, `shell`, `web`, `browser`, `memory`, `data`, `gui`, `system`, `code`, `image`, `audio`, `video`, `agent`, `plugin`, `mcp`. Capabilities in the same family may share approval-policy templates and surface presentation defaults.

A capability declares one family. Family membership is for grouping; it does not affect dispatch.

### 13.3 `aliases`

A capability declaration may declare aliases — alternative ids it has been known as. Aliases support:

- registry-level renames without breaking saved automations or user-pinned shortcuts
- MCP tool name conventions where remote servers expose tools under different naming styles
- backwards compatibility across `version` increments where the operation moved to a new family or operation name

Each alias entry carries the alias string, the version range during which the alias is honored, and an optional deprecation timestamp after which the registry warns or refuses lookups by the alias. Aliases are inspectable; the registry does not silently rewrite ids. The active alias projection lives on the registered entry (§10).

The `aliases` field is for identity compatibility only. Declaring a separate registered capability whose handler delegates to another capability is a distinct mechanism, the adapter capability (§17.4), and uses its own declaration.

### 13.4 `version`

Anchor: `capability.version`

`version` is a semantic version of the capability declaration. Increments follow standard semver semantics:

- patch (1.0.0 → 1.0.1): no observable change to the contract; documentation, internal handler refactor
- minor (1.0.0 → 1.1.0): backwards-compatible contract additions (new optional input field, new error variant, new tag)
- major (1.0.0 → 2.0.0): breaking change (removed input field, output schema change, permission-tier change, removed error variant, family change, behavior change incompatible with prior version)

The registry may hold multiple versions of the same id concurrently when callers reference them explicitly (saved automations may pin a version). The default resolved version is the latest registered. Major-version bumps are explicit registrations; the older version is not implicitly removed.

The version is part of the wire identity for replay and reproducibility: a ledger entry records `(id, version)` and a replay against a different version surfaces a typed reproducibility warning.

### 13.5 `schema_version`

`schema_version` is the format version of the declaration itself, distinct from the capability's `version`. Increments allow the declaration field set to evolve (new metadata fields added, deprecated fields removed) without breaking older declarations: at registration the registry normalizes supported earlier `schema_version` declarations forward to the current format.

ATLAS3 is in initial development; no third-party persisted declarations exist yet. A migration framework with chained migrations is therefore not required at present (per project constraints — no migration code for things that don't exist). The registry validates the current `schema_version` and rejects unknown versions; once external declarations begin to persist (plugins shipping declarations across releases, MCP adapters surviving Atlas upgrades), normalization-on-load will apply at that boundary.

### 13.6 Boundary

Identity is stable across runs; `version` is the explicit mutation knob. Renames go through aliases. Replacement is `update()` with a new declaration whose `version` honors semver semantics. Wholesale id reuse for unrelated operations is forbidden — it produces silent reproducibility breakage.

## 14. Override Resolution and Conflicts

Anchor: `capability.override-resolution-conflicts`

### 14.1 Identifier Collisions

Two declarations may not be the active entry under the same `id` simultaneously. The registry's collision policy is:

- a registration whose id collides with an existing active registered entry is rejected by default (`IdentifierCollision` error)
- the registering source must use a different id (the typical resolution for plugin-defined capabilities)
- the registering source declares the existing id as an alias and offers itself as a replacement under a new id; this is an explicit user-facing choice (the user accepts the migration)
- a higher-priority source (per §14.2), with explicit user opt-in, registers; the registry stores both declarations, marks the existing entry `collision_state: Shadowed { shadowed_by: <new_entry> }`, marks the new entry `collision_state: Shadowing { shadows: <prior_entry> }`, and resolves lookups to the new entry

The registry stores all colliding declarations that pass validation. The collision policy selects the active entry. Inactive (shadowed) entries remain inspectable through registry diagnostics and can be reactivated by removing or disabling the shadowing entry. Source declarations are never mutated by collision resolution; the active-vs-shadowed selection is registry state on the registered entries.

The default behavior is rejection. Replacement is opt-in and surfaced. Replay can pin the exact `(id, version, source_instance)` of the registered entry that was active at call time so collision history does not break reproducibility.

### 14.2 Source Priority

When a user explicitly opts into a capability override, source priority resolves:

`UserDefined` overrides `Plugin` overrides `Subsystem` overrides `Builtin`. `McpServer` and `Api` capabilities live in their own source-prefixed namespaces (`mcp.*`, `api.*`) and do not collide with other sources by id alone.

Source priority does not auto-override. A user-defined capability that wishes to take over a built-in id must declare the override and the user must accept it; the registry then shadows the built-in registration. Shadowing is reversible: removing or disabling the user-defined capability restores the built-in.

### 14.3 Layered Resources

Skills, instruction packs, instruction fragments, and workflow templates are not capabilities; they are separate primitives with their own layered resolution (per File 04 and the future capability-extension and skill specs). File 05 does not specify layering for those resources. Where a capability ingests such a layered resource, the capability declares the layer policy (`project > workspace > user > plugin > builtin` or equivalent) and consumes the resolved value.

### 14.4 Cross-Source Coexistence

Multiple sources commonly contribute non-colliding capabilities to the same family. A `web.fetch` built-in and a `mcp.web_fetcher.fetch` MCP-server capability coexist; the routing layer (File 03) decides which to use per request. Coexistence is the default; collision is the exception.

## 15. Discovery

Anchor: `capability.discovery`

### 15.1 Lookup Surface

The registry exposes lookup along several axes:

- direct id lookup (alias-aware)
- family enumeration
- source enumeration
- tag-filtered enumeration
- availability-filtered enumeration (over a supplied world-model snapshot)
- text search over `name`, `description`, and `tags` for command palette and natural-language matching
- semantic search over `description` (if an embedding index is configured) for richer matching at higher cost

All lookup surfaces honor `availability_status` and `enabled` from the registered entry; surfaces may opt to reveal unavailable entries explicitly through advanced settings.

### 15.2 `availability_predicate`

Anchor: `capability.availability-predicate`

`availability_predicate` declares when the capability is invocable. Required parts:

- `requires`: a typed declaration of state the capability needs (active surface, focused element class, selection presence, present capability prerequisites, present credentials, present provider with required model capability)
- `blocked_by`: a typed declaration of state that prevents invocation (a destructive capability blocked while a prior destructive call is still committing; a publish-capability blocked while the workspace has unsaved changes)

The state-awareness service evaluates predicates against the current world-model snapshot and produces the available-capability list (per `core.world-model`, File 01 §6.7 World Model). Surfaces consume that list — the command palette shows the available subset; the agent sees the available subset filtered further by surface-loading rules in File 07.

Predicates are declarative. A capability whose availability rule cannot be expressed as a typed declaration must extend the predicate vocabulary through registered availability checks (a named function that the registry evaluates). Ad-hoc procedural availability is rejected.

### 15.3 `prerequisite_capabilities`

Anchor: `capability.prerequisite-capabilities`

A capability may declare `prerequisite_capabilities` — a list of scoped prerequisites. Each prerequisite entry names a capability id and a `scope`:

- `run`
- `intent_thread`
- `task`
- `conversation`
- `workspace`
- `global`

A prerequisite is satisfied when the named capability has been invoked (with a successful outcome) within the named scope before this capability becomes invocable. Prerequisites are evaluated against the ledger and world-model facts, not against hidden local flags. Used for capabilities whose contract requires sequencing (an `artifact_handoff`-style capability that must precede certain content-generation calls; a guide-must-be-read prerequisite that gates source-tools until onboarding has been performed).

The registry encodes the dependency declaration with its scope. The detailed predicate evaluator lives in the future world-state / availability spec; File 05 names the contract. A capability invocation that violates the prerequisite returns a typed `PrerequisiteUnsatisfied` error variant in-band.

### 15.4 Runtime Discovery Capabilities

Discovery is itself a capability surface. The canonical built-in discovery capabilities (per `run.routing-influence`, File 04 §10.3) — `tool.search`, `tool.borrow`, `mcp.search`, `extensions.search_registry` — are first-class registered capabilities. The agent invokes them through the same call pipeline, and their outputs flow as typed blocks that the agent loop consumes.

The built-in discovery capability set is canonical; surface tools and presentations may add subsystem-specific or family-specific discovery shortcuts. Discovery capabilities themselves declare `ReadOnly` permission tiers and declare the registry projections they read.

## 16. Lifecycle

Anchor: `capability.lifecycle`

### 16.1 Startup Registration

Anchor: `capability.startup-registration`

At application startup, the registry is populated in declared phases:

1. Built-in capabilities register first (compiled into the binary; declared statically by every subsystem during `AppState` initialization)
2. Subsystem capabilities register when subsystem runtimes load (per the subsystem registry referenced in File 03 routing-and-dispatch)
3. Plugin capabilities register as plugins load (per the future Extension and Plugin System spec)
4. MCP-sourced capabilities register as configured MCP servers connect (per the future MCP and External Integrations spec)
5. External-API capabilities register as TOML definitions are loaded
6. User-defined capabilities register from their persisted declarations (per `run.interruption-pause-cancellation`, File 04 §17 self-modification storage and the future user-defined capability storage spec)

The phases are sequenced because later phases may register capabilities that override or alias earlier ones; the registry reaches a stable state when all phases complete.

A capability that fails to register (handler unresolved, declaration invalid, source unavailable) is recorded as registration-failed in the registry diagnostics; later sources may proceed. Startup does not abort on a single failed registration.

### 16.2 Runtime Mutation

Anchor: `capability.runtime-mutation`

Capabilities may register, update, and unregister at runtime:

- a plugin install adds capabilities mid-session; the user approves the plugin's permission manifest at install time; the capabilities become available immediately to subsequent agent iterations
- an MCP server connection adds capabilities mid-session; the connection itself is approved by the user at server-add time; reconnection after a crash retains the prior approvals
- a user invocation of `tools.register_custom` adds a user-defined capability; the call requires `UserApproval` regardless of other approvals; registration scope (`conversation`, `workspace`, `global`) is declared in the call
- a subsystem extension capability registers a new subsystem (or removes one), by the same proposal-first approval rules

Registration is a capability call. Capability registration, plugin installation, MCP connection, external-API definition import, user-script registration, and subsystem registration are themselves capabilities. They flow through the `run.call-pipeline` (File 04 §8.2) execution pipeline and the policy layer like any other call. Runtime registration APIs are not privileged side doors; the agent cannot self-promote registration without user approval.

Registration proposals preview source, declared permissions, declared touched resources, declared replay class, declared trust hint, persistence scope, and backend kind so the user can make an informed accept/configure/deny decision. The exact proposal shape and approval mode is configurable per source class. The default behavior must keep ATLAS3 safe; users can override the default per source (auto-approve trusted sources, ask-each-time for untrusted, deny outright) so customizability and safety co-exist.

### 16.3 `enabled`

`enabled` is registry state, not a declaration field. A disabled capability remains in the registry (it appears in the catalogue with disabled status; `availability_status: Disabled`) but is not invocable. Disabling a capability is a settings-level operation; enabling restores invocability.

Use cases for disable rather than unregister:

- the user wants to temporarily shut off a noisy or expensive capability without losing its declaration or scoped settings
- a plugin is suspected of misbehaving; disabling its capabilities is reversible while diagnosis proceeds
- the plugin is being upgraded; old capabilities are disabled while new ones register, then the disabled capabilities are unregistered atomically

`enabled` may be scoped: a capability may be globally enabled but disabled within a specific workspace or conversation. The settings system (per `core.settings-system`, File 01 §6.8) holds the scoped enable state.

### 16.4 Update Mechanics

`update(declaration)` replaces the active registered entry for the named id with a new declaration. Compatibility rules:

- patch-version updates do not require re-approval of existing leases
- minor-version updates preserve existing leases (the new contract is a backwards-compatible superset)
- major-version updates invalidate existing leases (the contract changed meaningfully); leases must be re-granted; the user is surfaced the change at next invocation

The update is atomic from the caller's perspective: in-flight calls against the prior declaration complete under the prior contract; new calls go through the new contract. Both versions are durably recorded in the ledger so prior calls remain interpretable.

### 16.5 Unregistration

`unregister(id)` removes a capability. In-flight calls complete; new calls are refused with a typed `CapabilityUnregistered` error. Persisted leases for the unregistered capability transition to a "stale" state and are pruned per the policy spec's lease-cleanup rules.

Unregistering a built-in capability is forbidden (the binary defines what built-in means); a built-in may only be disabled. Unregistering a subsystem capability happens implicitly when the subsystem unregisters. Plugin capabilities unregister on plugin unload. MCP capabilities unregister on server disconnect. User-defined and API capabilities unregister on user action.

### 16.6 Restart Behavior

Capabilities whose registrations are persisted (built-in, subsystem, installed plugin, configured MCP server, loaded API definition, user-defined with persistent scope) re-register on restart. Capabilities that were enabled before restart remain enabled. In-flight calls that did not complete before restart follow the orphan-run rules in `run.cancellation` (File 04 §17.3) (default `process_restart_orphan`; capabilities declaring `resume_on_restart: true` may resume per their handler).

The registry's restart sequence is deterministic: the same set of declarations registered in the same priority order, producing the same registry state, modulo new plugin updates and MCP-server availability changes. Determinism is required for replay and reproducibility.

## 17. Composition Primitives at the Contract Level

Anchor: `capability.contract-composition`

### 17.1 `dependent_capabilities`

A capability whose handler internally invokes other capabilities declares `dependent_capabilities` — the list of capability ids it may call. Used by:

- the policy layer to evaluate transitive risk (a capability declared `WorkspaceWrite` that internally calls a `UserApproval` capability surfaces both approvals, not just the outer one)
- the audit layer to attribute internal calls to the outer capability invocation
- the surface layer to display capability composition transparently to the user

`dependent_capabilities` is honest. Declaration is not an execution bypass: a capability that declares a dependent must invoke that dependent through the shared capability-call pipeline so policy, leases, resource checks, hooks, cancellation, and ledger recording all apply. Direct hidden delegation is invalid even when the dependency is declared. A capability that quietly delegates to another capability without declaring it is an Explicit Rejection (§19). Internal sub-mode dispatch within a single capability (per `run.tool-calls`, File 04 §9) is not a dependent-capability call and need not be declared.

### 17.2 `output_block_kinds` and `output_event_kinds`

Anchor: `capability.output-kinds`

A capability declares the block kinds it produces and the event kinds it emits. Block kinds are drawn from the canonical block catalogue (per File 08); event kinds are drawn from the canonical event catalogue (per File 10). The declarations enable:

- the surface layer to know how to render the output without inspecting the runtime value
- the context-assembly layer to budget tokens for expected outputs
- the validation layer to check that produced blocks match declared kinds

A capability that emits an undeclared block or event kind is an Explicit Rejection. Adding a new emission requires declaration update and version increment.

### 17.3 Cross-Capability Programmatic Composition

Cross-capability composition is one of three shapes (per `run.tool-calls` (File 04 §9), `run.programmatic-execution` (File 04 §14)):

- the model emits multiple capability calls in one turn; they execute concurrently subject to declared concurrency rules (§7)
- programmatic execution (`code.execute_with_tools` or equivalent) chains capability calls deterministically within a single execution unit, passing one call's output as the next call's input; each call still goes through the full pipeline (validation, policy, dispatch, ledger)
- a workflow step references a capability id and invokes it with templated inputs; the workflow runtime is itself a capability that orchestrates other capabilities

None of these shapes require new contract field set: they are runtime composition of capabilities whose declarations are already present. The declaration supplies what each call needs; the executor handles the composition.

### 17.4 Adapter Capabilities

Anchor: `capability.adapter-capabilities`

A registered declaration may be an adapter capability — a separate registered capability that delegates to a target capability while changing presentation, defaults, constraints, or surface ownership. The adapter declares its own id, display, and any narrowed input/output schema, plus an `adapter_capability` field naming the target capability id and version. The adapter's handler invokes the target through the shared capability-call pipeline (so policy, leases, resource checks, hooks, and ledger all apply to the inner call as well as the outer adapter).

Adapters serve subsystem-specialized presentations (a `coder.git_commit` capability that adapts `git.commit` with a coder-subsystem display and a constrained input schema), default constraints, and tighter touched-resource scopes without duplicating implementation. The ledger records both the adapter id and the resolved target id, so audit and replay see the full call shape.

`adapter_capability` is distinct from the `aliases` field (§13.3). `aliases` preserves a single capability under multiple id strings; an adapter is a separate registered capability whose handler is the underlying target. Both are inspectable and explicit.

### 17.5 Boundary

Composition primitives at the contract level make capability use inspectable. The runtime mechanics of dispatch, batching, dependency tracking, and parallel execution belong to File 04. The block and event catalogs belong to Files 08 and 10. File 05 declares the surface area; later specs operate on it.

## 18. Settings

Anchor: `capability.settings`

### 18.1 Configurable Dimensions and Layer Ownership

Every capability mechanism in this file must be configurable through settings (per `core.settings-system`, File 01 §6.8). File 05 names the dimensions and the layer that owns the resolution algorithm; resolution algorithms themselves live in their owning layers.

Dimensions and ownership:

- per-capability `enabled` state, scoped global, workspace, and conversation — owned by registry and the settings system
- per-capability default `permission_tier` overrides (capped by `permission_floor`), scoped through the same hierarchy — declaration carries the dimension; resolution lives in File 06
- per-capability `classification_mode` overrides (deterministic vs model-mediated) for fields that support per-call classification — declaration carries the dimension; the policy/runtime layer resolves
- per-capability cost-model overrides and budget caps — declaration carries the dimension; budget enforcement lives in the runtime/budget layer
- per-capability telemetry enablement and verbosity — declaration carries the dimension; resolution lives in the future Telemetry spec
- per-source user trust overrides — registered entry carries the override separately from source-authored trust; effective trust is resolved by File 06
- registry-wide collision behavior (warn vs reject vs ask-on-override) — registry-owned
- discovery-capability enablement (`tool.search`, `mcp.search`, `extensions.search_registry`) — registry-owned
- alias deprecation enforcement (warn vs refuse on use of deprecated aliases) — registry-owned
- runtime-registration enablement: whether the agent is permitted to invoke `tools.register_custom`, `extensions.install`, `subsystems.register`, and equivalent registration capabilities at all (off, ask-each-time, allowlist of trusted sources, allow) — declaration carries the dimension; resolution lives in File 06 and the future Extension/Plugin specs
- per-capability availability-predicate overrides for users who want to expose normally-hidden capabilities at their own risk — declaration carries the dimension; resolution lives in the future world-state spec
- platform-availability surface visibility (whether `unavailable_platform` entries appear in the default discovery view or only in advanced settings) — registry/surface-owned
- source-approval risk thresholds and defer/cancel fallback behavior — registered entry carries the relevant source state; resolution lives in File 06

### 18.2 Settings-Key Convention

Anchor: `capability.settings-key-convention`

Capability-related configuration follows File 15's namespaced dotted-key convention: `capabilities.<id>.enabled`, `capabilities.<id>.permission_tier`, `registry.collision_policy`, `registry.source_approval_threshold`, `sources.<source_id>.trust_override`, etc. Plugin-supplied capabilities register their own settings keys at plugin install time per the future Extension and Plugin System spec.

### 18.3 Boundary

File 05 stores the declared and registry state for every configurable capability mechanism. Policy and surface specs resolve runtime behavior from those values. Settings whose mechanism depends on optional provider or platform capability must degrade gracefully when the capability is absent (per `routing.settings`, File 03 §13). Settings define intended product variation; they must not become hidden hardcoded branches.

## 19. Explicit Rejections

Anchor: `capability.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel registry for any capability source — every capability enters one registry through one contract regardless of source
- silent registration of capabilities by hidden mechanisms — every registration is observable through the registry's mutation event stream
- silent capability-id reuse for unrelated operations — id stability and version semver are the contract for evolution
- capability declarations that omit touched-resource expressions, declared error vocabulary, declared replay class, or execution-semantic metadata — every required field must be present
- prose-only touched-resource declarations for any capability with `access: write` or `access: read_write` — write-capable capabilities require machine-parseable expressions
- capability handlers that touch resources or invoke other capabilities outside their declared scope — this is "capability leakage" and violates the contract
- source trust rewriting declared fields — the registered declaration is the contract; trust state is separate registry metadata; effective tier is computed by policy at call time
- argument-aware permission-tier expressed as duplicate id variants — use `TierResolver::Dynamic` instead
- model-request-only capability extension (extending agent behavior by injecting instructions into model-request instructions without registering a capability) — agent-invokable behavior must register
- runtime registration that bypasses the user's approval — the user must explicitly approve the registration capability invocation; the agent cannot self-promote without that approval
- capability ids that conflict with the namespace separators or the source-prefix conventions
- declaring a closure-backed capability with `replay_class` above `not_replayable` — closures are not portable across processes and breaking that invariant breaks reproducibility
- coalescing internal sub-mode dispatch into separate capability registrations (a `file.read` that internally branches on text vs binary remains one capability, not two — per `run.explicit-rejections` (File 04 §28))
- registry mechanisms that hardcode any of the variations in §18 settings instead of exposing them as configuration
- capability declarations whose `output_schema` returns inline content for outputs that should be durable blocks — durable outputs reference blocks; inline returns are reserved for short structured data
- allowing settings, leases, or trust upgrades to lower irreversible high-blast-radius operations below their declared `permission_floor` — a `permission_floor` for account deletion, destructive publish, force-push to a protected branch, system shutdown, or credential export is the absolute lower bound; no toggle, lease, or trust override may pierce it
- platform mismatch silently dropping a capability from the registry — platform-incompatible capabilities are catalogued as `availability_status: unavailable_platform`, not absent
- treating capability versioning as implicit (mutating a registered capability's behavior without bumping `version`) — every observable change is a version increment
- treating registry state (enable, trust override, collision shadowing, backend binding) as a declaration mutation — declarations are immutable for `(id, version)`; runtime changes live on the registered entry
- hidden delegation (a capability invoking another capability without declaring it as a dependent and without going through the shared call pipeline) — declaration of dependents is required and is not a bypass
- treating `Capability` and "skill" / "workflow" / "instruction-pack" as the same primitive — capabilities are typed executable contracts; skills are instruction modules; workflows are reusable orchestrations; each is its own primitive with its own registry (per the future Workflows, Templates, and Reuse spec)
- preserving `Action` as a parallel registry, adapter layer, or alias for `Capability` — `Action` has been superseded; legacy `Action` shapes map into the declaration field set (per §1) and are not preserved as a second primitive

## 20. Consequences for Later Specs

Anchor: `capability.consequences-for-later-specs`

Every later spec that touches capabilities consumes the `CapabilityDeclaration` and the `RegisteredCapability` defined here as their operation primitive. Later specs covering capability policy and approvals, tool surfaces and capability loading, blocks and the block graph, artifacts and evidence, the execution ledger and event stream, version graph and projections, retrieval and indexing, context assembly and compaction, memory, model strategy and provider integration, world model and state awareness, settings and profiles, storage and persistence, sync and portability, security and credentials, sandboxes and isolation, workspaces and materialization, the per-surface specs (work surface contract, control rails, coder, web, data processor, teacher, GUI control, system agent), automation and triggers, workflows and templates, the extension and plugin system, MCP and external integrations, the UI shell and customization, quality control and validation, evaluation and benchmarking, telemetry and observability, runtime infrastructure and lifecycle, and packaging and distribution must:

- read declared metadata from `CapabilityDeclaration` (identity, schemas, touched-resource expressions, permission tier and floor, capability class, execution-semantic metadata including replay class, validation paths, postconditions, source attribution, display, availability predicate, prerequisites, composition declarations, cost model, telemetry schema, backend descriptor)
- read live state from `RegisteredCapability` (enable state, availability status, resolved backend binding, source instance, trust state, lifecycle state, active aliases, collision state, diagnostics)
- record per-call resolved facts on `CapabilityInvocation` (resolved tier, resolved touched resources, resolved model-mediated classifications, selected backend binding instance, policy decision, ledger linkage, call outcome) — never on the declaration
- treat the registry as the resolution surface and File 04 as the execution surface — never embed parallel execution pipelines
- not introduce parallel capability metadata, parallel registries, or capability-like primitives that bypass the contract defined here
- consume the trust/source/declaration boundary established in §9 — trust influences policy, never the declaration
- consume the platform-as-availability-state model from §9.4 and §10 — platform-incompatible capabilities are inspectable, not absent
- consume the collision-as-registry-state model from §14.1 — colliding declarations remain inspectable; the active entry is registry state

Specific integration contracts will be stated in those files when they are written.
