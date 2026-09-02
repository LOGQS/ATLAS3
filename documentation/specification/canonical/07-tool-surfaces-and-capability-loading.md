# Tool Surfaces and Capability Loading

## Status

Canonical.

## Scope

This file defines:

- `ToolSurface` — the typed projection of the Capability Registry that a `Run`, a control rail, or any other invoker sees at a given moment
- the canonical zone model (`Primary`, `Borrowable`, `Deferred`, `Disabled`, `Unavailable`) and the meaning of each zone in model-request presentation, palette presentation, and policy interaction
- the loading semantics for each zone — what callable declarations are exposed to a model, what metadata is rendered into user-facing surfaces, and what is hidden until explicitly requested
- the per-subsystem default surface contract (`SubsystemSurfaceSpec`) that every work surface and substrate service that owns capabilities must declare
- the runtime composition algorithm that produces the effective surface from registered state, routing inputs, settings, active borrow grants, world-model state, and context budget
- the late-loading capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) as first-class registered capabilities and their scoping rules
- auto-shrink behavior under context pressure: priority order, deterministic mechanics, user visibility and override
- the unified invocation-path contract — model request, command palette, keyboard shortcut, voice, automation trigger, external protocol — all sourced from one `CapabilityDeclaration`
- the surface-relevant event vocabulary emitted into the execution ledger and event stream
- persistence and reconstruction rules across process restart, retry, edit, reroute, branch, and child-run spawn
- the boundary with the policy layer — loading is presentation, policy gates execution
- degradation and graceful-absence semantics when a registered capability becomes invocable, unavailable, or partially available mid-run
- inspection, filtering, and customization at every scope (global, profile, workspace, conversation, run) with the canonical data contract user-facing UIs consume
- settings dimensions consumed by surface composition; exact cross-scope settings precedence is owned by the settings layer

This file does not define:

- the `CapabilityDeclaration` field set, registry operations, identity, versioning, or backend binding lifecycle — File 05 owns those
- effective permission tier resolution, lease evaluation, approval flows, approval-policy templates, or contradiction-checking — File 06 owns those
- routing-frame composition, the route record, or how `tool_surface_strategy` is chosen by the router — File 03 owns those
- run lifecycle, the capability-call pipeline, hook execution, cancellation, streaming, or postcondition validation — File 04 owns those
- block schema, artifact lifecycle, evidence model, or the version graph — later specs own those
- the per-surface specifications themselves (Coder File 27, Web File 28, Data Processor File 29, Teacher File 30, GUI Control File 31, System Agent File 32) — those specs declare their `SubsystemSurfaceSpec` to the contract this file defines
- the storage schema for surface state, `BorrowGrant`s, policy leases, or settings — File 20 owns those
- UI rendering choices (palette layout, voice cadence, shortcut display) — File 07 specifies the data contract, File 37 and File 38 render
- MCP transport mechanics, plugin install lifecycle internals, provider rate limits, or sandbox primitives — File 36 (MCP and External Integrations), File 35 (Extension and Plugin System), and File 23 own those; File 17 owns provider concerns

## Source Resolution

This file resolves tool loading, tool search, borrowing, MCP discovery, subsystem surfaces, and model-request exposure material into one boundary: the runtime capability surface visible to a model or user.

Resolved design:

- A tool surface is a projection of the Capability Registry, not a second registry.
- Loaded, visible, callable, and permitted are separate states; permission remains owned by File 06.
- Primary, borrowable, and deferred zones control request size and discoverability without hiding the underlying registry.
- Search, borrow, inspect, revoke, and surface-change behavior are first-class capability interactions with events and snapshots.
- External tool descriptions are untrusted data rendered behind architectural instruction boundaries, not sanitized into trusted instructions.
- Subsystem defaults and user settings shape surfaces, but every loaded tool still follows the same capability and policy contracts.

## 1. Chosen Model

Anchor: `surface.chosen-model`

ATLAS3 has one Capability Registry (per File 05). The set of capabilities that a particular invoker — a `Run`'s executing model, a programmatic execution unit, the command palette, a voice command resolver, a keyboard-shortcut dispatcher, an automation trigger, or an external client speaking the MCP server protocol — sees at a given moment is a `ToolSurface`.

A `ToolSurface` is:

- a typed projection over the Capability Registry, with zone assignment computed per `(invoker, scope, context)`
- composed from the registered state (per `capability.registered-capability`, File 05 §10), the resolved settings snapshot (per File 15), active `BorrowGrant`s, the active routing decision (per `routing.tool-surface-strategy`, File 03 §8.3 `tool_surface_strategy`), the active world-model snapshot (per `core.world-model`, File 01 §6.7), and the active context budget (per `run.routing-influence`, File 04 §10.3 and File 13)
- a presentation surface, not a security gate — invocation authority is owned by File 06's policy layer, and a capability visible in a surface is still subject to effective tier resolution at proposal time
- inspectable, settable, and observable through the settings model: durable global/workspace/conversation scopes, active profile context, and non-durable run or per-call overlays

The same registered `Capability` appears in multiple `ToolSurface` projections concurrently. The model running inside a `Run` sees a model-request surface. The user looking at the command palette sees a palette surface. A voice listener sees a voice-invokable surface. A keyboard shortcut resolver sees a shortcut surface. An automation rule editor sees an automation-trigger surface. An external MCP client sees the externally exposed surface. Each is the same registry projected through a different invocation lens, and each composition step honors the same canonical algorithm.

`ToolSurface` is the canonical noun. Earlier source material uses "tool list", "tool catalog", "available tools", "action palette", "skill catalog", "action registry view", "function library", "tool inventory", and equivalent phrases. None of those survive as parallel primitives. The word "tool" remains an informal synonym for `Capability` per `capability.chosen-model` (File 05 §1); references like "tool-surface strategy" and "tool.borrow" preserve the established vocabulary where it is already canonical in earlier files.

This file supersedes any earlier shape that treated the agent's available capability list as a separate object from user-facing palettes, voice command grammars, shortcut maps, or automation editors. The shape is one — the projection lens differs.

## 2. `ToolSurface`

Anchor: `surface.tool-surface`

### 2.1 Definition

A `ToolSurface` is the typed projection of the Capability Registry that a specific invoker sees at a given moment. It is computed; it is not stored as an independent mutable record. Every call to render a surface — to the model request, to the palette UI, to the voice resolver, to a remote MCP client — runs the canonical composition algorithm (§9) over the same inputs and produces a `ResolvedToolSurface`.

A `ToolSurface` is not:

- a registry — capabilities live in the Capability Registry; surfaces project that registry
- a permission grant — visibility does not imply authority; File 06's policy layer evaluates every proposed call
- a separate mutable list per invoker — there is no per-invoker surface table that drifts from registry state; surface state is derived
- a stored UI configuration — what the user sees is rendered from the resolved surface plus presentation choices owned by later UI specs
- a per-capability flag — `Capability` declarations do not carry "current zone" as a field; zone assignment is computed runtime state

### 2.2 Invokers and Surface Kinds

A `ToolSurface` is always typed with an `invoker_kind` and an `invocation_lens`. The invocation-lens set is the invoker-kind set — this file names each lens by its invoker kind throughout (§3.2, §3.3, §3.4) — so the `<lens>` segment of `surface.lens_visibility.<lens>.<capability_id>` (§18.1) is the invoker kind's. Each canonical invoker kind declares an injective `settings_key_segment` matching `[a-z0-9]+(?:_[a-z0-9]+)*` (`settings.setting-definition`, File 15 §3.2); `ModelAgent` contributes `model_agent` and `Palette` contributes `palette`. The canonical invoker kinds are:

- `ModelAgent` — an executing model inside a `Run`; the surface renders into the model request as callable declarations and model-request text content
- `ProgrammaticUnit` — a deterministic execution unit (per `run.programmatic-execution`, File 04 §14) that resolves capabilities by id; the surface enumerates ids the unit may invoke. Unlike the tag-filtered lenses, the `ProgrammaticUnit` surface applies no display-tag filter — it enumerates exactly the ids in the unit's enumerated allowed set, and File 06 policy still gates each resolved invocation (§9.1 step 12)
- `Palette` — the command palette and equivalent quick-action surfaces (slash commands, palette overlays); the surface renders as a searchable user-facing list
- `Voice` — voice command resolver; the surface renders as a vocabulary-matchable set of voice-invokable capabilities with their aliases
- `Shortcut` — keyboard-shortcut dispatcher; the surface renders as a map from chord to capability id
- `AutomationTrigger` — automation rule editor and runtime trigger resolver; the surface renders as the capabilities a trigger may invoke
- `ExternalMcp` — external MCP client speaking to ATLAS3 as a server; the surface renders as the externally exposed capability catalog
- `Inspector` — the user-facing settings, plugin manager, source manager, and registry inspector; the surface renders as the full catalogue including disabled and unavailable entries

Each invoker kind consumes the same registry through a different lens. The composition algorithm (§9) takes `invoker_kind` as an input; per-kind filtering uses display tags and explicit invocation-path declarations on the capability (per `capability.display-fields`, File 05 §3.2, see §11 below).

### 2.3 Required Outputs

Anchor: `surface.required-outputs`

The composition algorithm produces a `ResolvedToolSurface` carrying at minimum:

- `surface_id` — stable identity for this composition for the duration of its validity (one model turn, one palette open, one voice session, etc.)
- `invoker_kind` and `invocation_lens` — what computed the surface
- `scope_context` — the snapshot of composition inputs that fed the composition; the canonical `scope_context` signature is the single one the composition algorithm consumes (§9.1): `run_id` (optional), `intent_thread_id`, `task_id`, `conversation_id`, `workspace_id`, `profile_id`, `primary_surface_id`, `supporting_surface_ids`, `routing_strategy`, `routing_metadata`, `tool_allowlist` (optional), `active_world_snapshot_id`, `active_settings_snapshot_id`, `active_borrow_grant_set_id`, `active_policy_snapshot_id`, `active_model_id`, `active_provider_id`, and `active_context_budget`. The zones a composition produces are outputs, never a `scope_context` input
- `zoned_entries` — typed per-capability records grouped by zone (per §3): `primary`, `borrowable`, `deferred`, `disabled`, `unavailable`
- `routing_inputs` — the `RunIntent.tool_surface_strategy` consulted (per File 03), the active routing decision facts (per §6), and any pre-existing `BorrowGrant`s honored
- `provider_name_map` — when rendered for a provider, a bijective map from every provider-visible tool name to `(capability_id, capability_version, declaration_version)`; invocation records store both the canonical id and the provider-visible name used for the call
- `context_budget` — the model context budget (per File 13) at composition time and the post-shrink budget actually consumed by tool definitions (per §8)
- `auto_shrink_record` — typed record of any auto-shrink performed: which capabilities moved between zones, the budget threshold that triggered shrink, the priority ordering applied, and a `cache_impact` classification (`none`, `preserved_prefix`, `changed_tool_surface_only`, `changed_instruction_or_region_order`, or `full_cache_break_likely`) describing how the shrink affected the cacheable model-request prefix (per §8.3)
- `composition_diagnostics` — typed diagnostic record naming, per capability ever considered, why it landed in its assigned zone (declared default, routing decision, settings override, active `BorrowGrant`, context-pressure shrink, availability state, trust narrowing); inspectable through the canonical inspector surface

Every `ResolvedToolSurface` is recorded as a surface snapshot in the execution ledger (per `run.execution-ledger`, File 04 §23.1) when it is consumed by an invoker, so replay and audit can reconstruct exactly which capabilities the model, palette, or other invoker saw at any prior moment.

### 2.4 Boundary

A `ToolSurface` is the projection layer over the Capability Registry. It owns no declarations of its own. The same canonical algorithm runs for every invoker kind; per-kind variation lives in the invocation-lens filter step (§11) and the presentation rendering owned by later UI specs.

File 20 owns durability of recorded surface snapshots and user-customization settings. File 37 and File 38 own how a `ResolvedToolSurface` is rendered to humans. File 07 specifies the data contract; storage and UI consume it.

## 3. The Zone Model

Anchor: `surface.zone-model`

### 3.1 Canonical Zones

Every entry in a `ResolvedToolSurface` lives in exactly one of five zones:

- `Primary` — full schema exposed as a provider-native callable declaration; full name and metadata present in user-facing surfaces; the capability is directly invokable by the model with no preparatory step
- `Borrowable` — name and `short_description` present in model-request text content; full metadata present in user-facing surfaces; the model can call `tool.borrow` to load the full schema for the current scope, after which the capability behaves as if it were `Primary` for that scope
- `Deferred` — not present in the model request at all; visible in user-facing surfaces only when the user explicitly chooses to reveal deferred entries (per §12.4); the model can locate the capability through `tool.search` or `mcp.search` and then call `tool.borrow` to bring it into the surface
- `Disabled` — not present in any invoker surface; appears only in the `Inspector` lens with a `Disabled` badge and the recorded `disable_reason`; remains in the registry as a registered entry per `capability.registered-capability` (File 05 §10.3); can be re-enabled through settings
- `Unavailable` — registered but currently not invocable because of `availability_status` (per `capability.registered-capability`, File 05 §10, e.g., `unavailable_platform`, `unavailable_handler`, `unavailable_prerequisite`); appears in the `Inspector` lens with the typed unavailability reason; never present in `ModelAgent` or `ProgrammaticUnit` surfaces because invocation would fail; may be present in `Palette` and `Inspector` lenses with a disabled-style indicator and an inspectable explanation per user-customization preference

The zone set is closed. `Disabled` and `Unavailable` are resolved presentation states, not declaration fields and not policy authority. Adding a sixth zone is an Explicit Rejection (§19).

### 3.2 Zone Semantics for the `ModelAgent` Invoker

The `ModelAgent` lens consumes zoned entries as follows:

- `Primary` entries render as provider-native callable declarations — the canonical `name`, `description`, `input_schema`, declared `error_vocabulary` summary, and any execution-semantic hints required by the active provider tool-call format (per `capability.declaration`, File 05 §3 and `run.hook-integration` (File 04 §23.3))
- `Borrowable` entries render as model-request text content — `name`, `family`, `short_description`, and a one-line note that the full schema is available via `tool.borrow(id)`; the model can recognize the capability and decide whether the borrow round-trip is worth its cost
- `Deferred` entries do not appear in the model request at all; the model discovers them through `tool.search` invocations or through capability hints injected by hooks or task context
- `Disabled` and `Unavailable` entries are not visible to the model — they cannot be invoked

The Primary catalog is the model's immediate action surface; the Borrowable catalog is its discoverable reach; the Deferred set is its searchable depth. The three together cover the model's full reach without overloading the model request.

### 3.3 Zone Semantics for the `Palette`, `Voice`, `Shortcut`, and `AutomationTrigger` Invokers

User-facing invokers consume zoned entries as follows:

- `Primary` and `Borrowable` entries are both shown by default in the canonical user view (palette list, voice grammar, shortcut map, automation trigger picker)
- `Deferred` entries are hidden by default but reachable through the inspector and through user search; advanced settings expose them inline (per §12.4)
- `Disabled` entries appear in the inspector with a disabled-style indicator; user can re-enable
- `Unavailable` entries appear in the inspector with the typed unavailability reason; user-customization decides whether they appear in palette/voice/shortcut with a disabled indicator or are hidden until they recover

The split between `Primary` and `Borrowable` is semantically meaningful for the `ModelAgent` invoker (it determines model-request cost); for user-facing invokers, the split is presented as visual grouping rather than as an action gate — the user does not need to "borrow" a capability to invoke it from the palette. User invocation through the palette, voice, or shortcut is direct; the palette resolver invokes the capability through the same `run.call-pipeline` (File 04 §8.2) pipeline that the model uses, and File 06 policy applies the same way.

### 3.4 Zone Semantics for the `ExternalMcp` Invoker

When ATLAS3 exposes capabilities to an external MCP client (per `capability.chosen-model`, File 05 §1's "agent and user invoke same underlying capability system through different control rails" and `core.extension-planes` (File 01 §6.14)), the surface filter applies the same way:

- `Primary` and `Borrowable` entries — visible in the external surface only if the capability is tagged for external exposure (per `capability.display-fields`, File 05 §3.2 tags) and the active source-approval policy permits external exposure (per `policy.source-approval-flow`, File 06 §9); a capability not tagged for external exposure is excluded from the `ExternalMcp` lens (a lens-local exclusion, not the registry `Disabled` zone) regardless of its zone in other lenses
- `Deferred`, `Disabled`, `Unavailable` — hidden from the external surface; external clients see only the externally exposed Primary + Borrowable set

The `tool.borrow` and `tool.search` capabilities are themselves first-class capabilities (§7); whether they are externally exposed is a user setting per source-approval and source policy.

### 3.5 Zone Membership is Computed

A `Capability` declaration carries no zone field. Zone membership is computed by the composition algorithm (§9) from:

- the capability's declared display tags (per `capability.display-fields`, File 05 §3.2, e.g., `agent-invokable`, `palette-invokable`, `voice-invokable`, `automation-trigger`, `external-exposed`)
- the capability's declared family and source (per `capability.display-fields` (File 05 §3.2) and `capability.capability-source` (File 05 §9.1))
- the capability's declared availability predicate (per `capability.availability-fields` (File 05 §3.9) and `capability.availability-predicate` (File 05 §15.2)) evaluated against the active world-model snapshot
- the active `SubsystemSurfaceSpec` for the run's current primary surface (per §5)
- the active `RunIntent.tool_surface_strategy` (per `routing.tool-surface-strategy` (File 03 §8.3) and `routing.routing-summaries` (File 03 §6))
- the resolved settings snapshot for per-capability zone overrides, per-family zone overrides, per-source zone overrides, and lens visibility (per §12 and §18)
- active `BorrowGrant`s for schema-visibility promotion and policy-resolved facts relevant to presentation (per §7.3 and File 06)
- the registered entry's `enabled` flag and `availability_status` (per `capability.registered-capability`, File 05 §10)
- the active context budget reported by the context assembly layer (per `run.routing-influence`, File 04 §10.3 and File 13) for auto-shrink decisions (per §8)
- the registered entry's trust state (per `capability.trust-source-approval-flow`, File 05 §9.2 and `policy.effective-tier-resolution` (File 06 §4)) for trust-driven narrowing

The composition is deterministic given the same inputs (§9.4). Two invokers with the same `scope_context` consuming the same registry state produce the same zoned entries.

### 3.6 Zones Are Not Authority

Zone membership controls visibility, model-request cost, and discovery. It does not grant or deny invocation authority. A capability in `Primary` may still be denied at proposal time by File 06 policy (effective tier reaches a Deny verdict, policy lease contradiction surfaces, `permission_floor` is violated). A capability in `Borrowable` undergoes the same policy evaluation when invoked. The `tool.borrow` capability is itself subject to policy — borrowing requires `ReadOnly` tier per its declaration (§7.2) and the borrowed capability's own tier still applies when the model later invokes it.

The split between visibility and authority is a load-bearing invariant. Earlier source material occasionally conflates "tool surface" with "permission set"; this file rejects that conflation. The surface answers "what can the invoker see?"; the policy layer answers "may this proposed call proceed?".

## 4. Loading Semantics

Anchor: `surface.loading-semantics`

### 4.1 What "Loaded" Means

A capability is "loaded" for the `ModelAgent` lens when its zone is `Primary`, which means its full schema, name, and description are exposed as provider-native callable declarations in the model request. A capability is "borrowable" when its zone is `Borrowable`, which means its name and short description are present in model-request text content but its callable schema is not. A capability is "deferred" when its zone is `Deferred` and it is not in the model request at all.

For the user-facing lenses (`Palette`, `Voice`, `Shortcut`, `AutomationTrigger`), "loaded" means "shown in the user's view"; the data shown is the full display metadata (name, short_description, family, tags, icon_key, default_shortcut) from `capability.display-fields` (File 05 §3.2) plus the resolved permission tier indicator from `policy.effective-tier-resolution` (File 06 §4) — the policy outcome a user invocation would face. The user-facing data is always available for any `Primary` or `Borrowable` entry; whether the user can also see `Deferred` entries is a customization setting.

### 4.2 Model-Request Rendering for `Primary`

The model request receives `Primary` entries as provider-native callable declarations in whatever native format the active model's provider expects (per `routing.capability-awareness`, File 03 §7.4 and `run.tool-calls` (File 04 §9)), normalized from the canonical capability declaration. The rendered fields:

- `name` — canonical `id` of the capability or a provider-safe visible name mapped back through `ResolvedToolSurface.provider_name_map`
- `description` — the localized `description` (per `capability.display-fields`, File 05 §3.2)
- `input_schema` — the declared `input_schema` (per `capability.input-schema`, File 05 §4.1) converted to the provider's native schema dialect
- `error_vocabulary` summary — a compact representation of recoverable and non-recoverable typed errors so the model can plan recovery (per `capability.error-vocabulary`, File 05 §4.3 and `run.denial-is-in-band` (File 04 §8.3) in-band denial)
- inline display hints — optional short notes derived from `tags` (e.g., a capability tagged `destructive` or `experimental` carries an inline note the model can use to decide when to call it)

Per `capability.display-fields` (File 05 §3.2) and the i18n discipline, the model sees localized text resolved against the active locale; literal defaults are present so the surface works before any localization is wired.

### 4.3 Model-Request Rendering for `Borrowable`

The model request receives `Borrowable` entries as model-request text content placed after the `Primary` declarations and before the conversation history. The block is structured so the model recognizes it as a borrow-eligible list:

- `family` grouping — entries are grouped by `family` (per `capability.family`, File 05 §13.2) so the model can scan by family
- per-entry one-liner — `name` and `short_description` (per `capability.display-fields`, File 05 §3.2)
- `borrow_invocation_hint` — a single hint line indicating that `tool.borrow(name)` loads the schema for the rest of the run (the default `BorrowGrant` scope, §7.3)

The block is deterministically ordered (alphabetical by family, then alphabetical by name within family) so the model-request prefix is cache-friendly where the provider supports caching (per `run.from-run-intent-to-run`, File 04 §3 cheap routing and File 13). If a `BorrowGrant` (per §7.3) is active, the borrowed capability is rendered in `Primary` for the duration of the grant and removed from the `Borrowable` catalog block to avoid duplication.

### 4.4 The Borrow Operation

`tool.borrow(capability_id)` is a first-class registered capability (§7.2). When the model invokes it, the executor (per `run.call-pipeline`, File 04 §8.2) runs the call through the full pipeline:

1. The capability is resolved and validated as any other call
2. Policy evaluates `tool.borrow` itself (declared at `ReadOnly` tier, per §7.2) — borrowing the metadata costs nothing in tier terms
3. The capability the model is borrowing is resolved against the registry to confirm it exists and is enabled and available; if not, `tool.borrow` returns a typed error in-band per `run.denial-is-in-band` (File 04 §8.3)
4. If the capability is found and in scope to be borrowable (per the active surface composition), the executor records a `BorrowGrant` (per §7.3) and returns the full capability schema as the tool result
5. The next composition of the `ToolSurface` for this run sees the active `BorrowGrant` and renders the borrowed capability in `Primary`
6. A surface-relevant event is emitted (`CapabilityBorrowed`, per §13)

If the capability the model is borrowing is in `Disabled`, `Unavailable`, or outside the borrow-eligible set for the current surface (for example, a capability whose source is not tagged as borrow-eligible per workspace settings), `tool.borrow` returns a typed denial result describing the reason. The model receives this in-band and may try `tool.search` to find an alternative.

### 4.5 Loading Across Turns

Within a single `Run` turn, borrowed capabilities are rendered as `Primary` from the moment the `BorrowGrant` is issued. Across turns within the same run, borrowed capabilities remain in `Primary` for the duration of the grant scope (per §7.3).

The default grant scope for `tool.borrow` is `run`. When a `Run` ends, run-scoped `BorrowGrant`s expire, and the next composition for any successor run starts from the unborrowed surface. The user or the agent can request a wider scope through `tool.borrow_persistent(capability_id, scope)` (a sibling capability, §7.2) at higher policy tier (`UserApproval` because it persists capability visibility across runs).

### 4.6 Late Schema Loading for MCP-Sourced Capabilities

Capabilities sourced from MCP servers (per `capability.capability-source`, File 05 §9.1) may carry larger schemas than registry-native capabilities. For large external registries, the registered entry carries a compact metadata cache and the full schema is fetched on-demand:

- The compact metadata (name, family, short_description, tags, declared tier) is fetched at MCP connect and cached in the registered entry
- The full schema is fetched on first `tool.borrow` or first invocation through the standard call pipeline
- The full schema is cached for the duration of the MCP server connection
- MCP server disconnect invalidates the cache and transitions the registered entry to `availability_status: unavailable_handler` per `capability.registered-capability` (File 05 §10)

This pattern lets ATLAS3 advertise large external surfaces (hundreds of tools from a complex MCP server) without bloating the registry's hot path or paying the full schema-load cost up front. The default loading policy is: MCP-sourced capabilities enter `Borrowable` zone for the `ModelAgent` lens of any run that does not explicitly route through the MCP-providing surface; they enter `Primary` only if the active `SubsystemSurfaceSpec` or settings places them there.

### 4.7 Boundary

Loading semantics define what fills the model request and what the user sees in the palette. They do not define how the model parses tool calls (`run.tool-calls`, File 04 §9 owns parser variation), how policy resolves the call (File 06 owns evaluation), or how the executor invokes the capability (`run.call-pipeline`, File 04 §8.2 owns the pipeline). Loading is the front-of-pipeline projection; everything else downstream is unchanged.

## 5. Subsystem Surface Defaults: `SubsystemSurfaceSpec`

Anchor: `surface.subsystem-surface-spec`

### 5.1 Required Shape

Every work surface and every capability-owning substrate service declares a `SubsystemSurfaceSpec` that the registry resolves at startup (per `capability.startup-registration`, File 05 §16.1). A `SubsystemSurfaceSpec` is the canonical contract for the default tool surface a subsystem contributes when it is the run's primary surface or a supporting surface.

A `SubsystemSurfaceSpec` carries:

- `subsystem_id` — the subsystem id from `capability.capability-source` (File 05 §9.1); matches the `primary_surface` value from `routing.run-intent` (File 03 §4.3) routing when this subsystem owns that surface
- `spec_version` — the declaration version of this `SubsystemSurfaceSpec` (per `capability.version`, File 05 §13.4); it increments on each update through the registration pipeline and is the `old_version`/`new_version` carried by `SubsystemSurfaceSpecUpdated` (§13)
- `display_name` — localized human-readable surface name (per `capability.display-fields`, File 05 §3.2)
- `primary_capability_ids` — the ordered list of capability ids (per `capability.id`, File 05 §13.1) that should be in `Primary` zone for a run whose primary surface is this subsystem
- `borrowable_capability_ids` — the ordered list of capability ids that should be in `Borrowable` zone for such a run; these are capabilities the subsystem expects the model to occasionally need but does not want consuming model-request budget by default
- `default_deferred_families` — optional list of capability families that should be `Deferred` rather than `Borrowable` for this subsystem; capabilities in these families are reachable only through search
- `forbidden_capability_ids` — optional list of capability ids that should be excluded from any zone for this subsystem even if other rules would include them; the executor still allows the model to attempt them through `tool.search` and `tool.borrow`, but the borrow returns a typed denial
- `spawnable_subagent_types` — optional list of subagent types this subsystem can spawn (per `run.child-runs-multi-agent-work`, File 04 §16); each subagent type names the `SubsystemSurfaceSpec` it will run under as a child run
- `surface_settings_namespace` — the settings namespace (per `capability.settings-key-convention`, File 05 §18.2) under which per-subsystem customization is keyed
- `availability_predicate` — optional subsystem-level predicate; if the predicate fails, the entire `SubsystemSurfaceSpec` is unavailable (e.g., a Web surface that requires a registered browser backend, a GUI Control surface that requires accessibility API access)

The `SubsystemSurfaceSpec` is declarative. It is a typed object the registering subsystem provides through the same proposal-first capability-registration pipeline that registers individual capabilities (per `capability.runtime-mutation`, File 05 §16.2). A subsystem's surface spec is updateable through that pipeline; updates emit `SubsystemSurfaceSpecUpdated` events (per §13).

Every ATLAS3 install ships one baseline `SubsystemSurfaceSpec` — the conversation surface — that is always present and is the active spec for any run whose `RunIntent.primary_surface` is `conversation` (per `routing.run-intent`, File 03 §4.3) or resolves to no subsystem-owned surface. Its `subsystem_id` is `conversation`; its `primary_capability_ids` are the discovery capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`, per §7.1) so that even a no-surface conversational run can discover and borrow; it declares no `forbidden_capability_ids` and no subsystem `availability_predicate`. The baseline surface guarantees that the composition algorithm's Step 1 (§9.1) always resolves an active `SubsystemSurfaceSpec`, so the no-surface case is a named baseline rather than an absent spec.

### 5.2 Capabilities Outside the Spec

A capability that is not listed in `primary_capability_ids`, `borrowable_capability_ids`, or `forbidden_capability_ids` is treated by the composition algorithm as `Deferred` for the `ModelAgent` lens of a run in that primary surface — the model does not see it in the model request but can reach it through `tool.search` and `tool.borrow`. The agent's full reach is still the registry; the surface is the discipline that keeps the model request focused.

For the `Palette`, `Voice`, `Shortcut`, and `AutomationTrigger` lenses, capabilities not in the spec are still surfaced if the capability is tagged appropriately (per §11) and the user has not disabled them. The user's palette is broader than the agent's model-request surface by default — `core.extension-planes` (File 01 §6.14)'s single-capability-multiple-invocation-paths invariant means the user can always invoke a capability through the palette even if the model request does not list it. The palette resolver invokes the capability through the same `run.call-pipeline` (File 04 §8.2) pipeline as the agent would, so File 06 policy still applies.

### 5.3 Routing-Time Strategy Selection

The router (per `routing.dispatch-pipeline`, File 03 §3) produces a `RunIntent` whose `tool_surface_strategy` field is one of:

- `use_current_surface_tools` — use the active `SubsystemSurfaceSpec`'s declared zones unchanged
- `borrow_foreign_capabilities` — start from the active `SubsystemSurfaceSpec` but pre-load capabilities from another subsystem's `primary_capability_ids` into the `Borrowable` zone before the model runs, so the model sees them as borrow-eligible without searching
- `load_deferred_capabilities` — start from the active `SubsystemSurfaceSpec` but promote specified deferred capabilities (typically named explicitly in `routing_metadata`) into `Primary` before the model runs, so the model sees them in the model request

`borrow_foreign_capabilities` and `load_deferred_capabilities` carry the specific foreign-subsystem or capability-id list in the `routing_metadata` field per `routing.run-intent` (File 03 §4.3). The composition algorithm (§9) consumes this strategy as one of its inputs.

### 5.4 Primary Surface Changes

Anchor: `surface.primary-surface-changes`

When a `Run`'s primary surface changes mid-execution — for example, through a mid-execution reroute per `routing.mid-execution-reroute` (File 03 §12) — the active `SubsystemSurfaceSpec` changes accordingly. The composition algorithm re-runs for subsequent model-request assembly; the next model turn sees the new primary surface. Capabilities that were borrowed before the transition retain their `BorrowGrant`s per the grant scope; a `run`-scoped `BorrowGrant` survives a primary-surface change within the same run.

A primary-surface change emits a `PrimarySurfaceChanged` event (per §13). The model's next request includes a typed notice (rendered as part of request assembly per File 13) describing the change so the model is aware its working surface changed.

### 5.5 Cross-Surface Reach Without Primary-Surface Change

Cross-surface capability access through `tool.borrow` does not require a primary-surface change. A run in the Coder surface that borrows `web.fetch` remains in the Coder surface; the borrowed capability becomes visible for the grant scope without changing `primary_surface`. The execution ledger records both the originating surface and the borrowed-capability source so audit can reconstruct cross-surface reach.

### 5.6 Boundary

`SubsystemSurfaceSpec` is a contract this file defines; the actual specs for the work surfaces (Coder, Web, Teacher, Data Processor, GUI Control, System Agent), the capability-owning substrate services, and any user-registered subsystems are declared in those subsystems' own canonical specs (the baseline work surfaces are Files 27–32). File 07 names the contract shape; later specs fill the contract for their subsystem.

## 6. Routing Influence

Anchor: `surface.routing-influence`

### 6.1 Consumed Inputs

The composition algorithm (§9) consumes the following routing-supplied inputs:

- `RunIntent.primary_surface` — the primary surface for the run, which selects the active `SubsystemSurfaceSpec` (§5)
- `RunIntent.supporting_surfaces` — additional surfaces routing identifies as relevant; their `primary_capability_ids` are promoted into the active surface's `Borrowable` zone by default
- `RunIntent.capability_families` — illustrative routing hints about which families matter; the composition uses these to prefer those families if zone slots are constrained by context budget
- `RunIntent.tool_surface_strategy` — `use_current_surface_tools` | `borrow_foreign_capabilities` | `load_deferred_capabilities` per `routing.tool-surface-strategy` (File 03 §8.3); consumed as in §5.3
- `RunIntent.model_route.resolved_model_id` — the resolved model identity; used to determine native tool-call format (per `run.tool-calls`, File 04 §9) and the model's context window (per File 17) for budget-aware shrinking
- `RunIntent.execution_entry` — `respond_inline` | `respond_with_tools` | `surface_runtime` | `multi_step_agent` per `run.execution-entry` (File 04 §4); affects whether tool surface is rendered at all (a `respond_inline` entry that needs no tools renders an empty surface)
- `routing_metadata` — observability fields per `routing.run-intent` (File 03 §4.3); surfaces use this for diagnostic display in the inspector lens

### 6.2 Routing-Time Pinning

Automations and user-invoked actions may pin `tool_surface_strategy` and specific capability lists at save time (per `routing.trigger-kinds-routing`, File 03 §2.1). The composition algorithm honors the pinned strategy the same way it honors a runtime router decision; the difference is provenance only, recorded in `routing_metadata` for audit.

### 6.3 Routing Inputs Are Inspectable

Per `routing.minimum-visible-information` (File 03 §10.2), the routing-frame inputs that informed the routing decision are surfaced to the user through the routing inspector. The `ResolvedToolSurface.composition_diagnostics` field (§2.3) extends this: the user can inspect any composed surface and see which routing inputs influenced which zone assignments, alongside settings, `BorrowGrant`s, policy-visible facts, and world-model state that contributed.

### 6.4 Routing Does Not Override Floors

Routing strategies cannot override safety floors. A capability whose `permission_floor` (per `capability.permission-floor`, File 05 §5.4 and `policy.permission-floor` (File 06 §7.1)) makes it `Denied` cannot be promoted into a zone by any routing strategy; the composition algorithm clamps the resulting zone to `Disabled` for the `ModelAgent` lens (the capability is still visible in the inspector to make the floor inspectable). Similarly, the source-trust narrowing rules from `policy.effective-tier-resolution` (File 06 §4.2) step 3 apply: a `Community`-trust capability that routing wants in `Primary` will be in `Primary` only if the user's source-approval permits it; otherwise the composition demotes it to `Borrowable` with an inspector note.

### 6.5 Boundary

Routing produces the `RunIntent`; the composition algorithm consumes its surface-relevant fields. Routing does not implement composition. The router does not directly mutate surface state; it produces inputs the algorithm consumes deterministically.

## 7. Late-Loading and Runtime Discovery

Anchor: `surface.late-loading-runtime-discovery`

### 7.1 Built-in Discovery Capabilities

Late-loading and runtime discovery are mediated by five canonical built-in capabilities registered in the Capability Registry per `capability.capability-source` (File 05 §9.1) (`Builtin` source) and resolved through the same call pipeline as any other capability per `run.call-pipeline` (File 04 §8.2):

- `tool.borrow` — load the full schema of a specific named capability into the active run's surface and grant a `BorrowGrant` per §7.3
- `tool.borrow_persistent` — variant of `tool.borrow` that grants a `BorrowGrant` at a wider scope (`intent_thread`, `task`, `conversation`, `workspace`, or another allowed scope); requires `UserApproval` tier
- `tool.search` — discover capabilities by name, family, description, or tag from the Capability Registry; returns a ranked list of matches with their zone assignment for the current surface
- `mcp.search` — discover capabilities specifically from connected MCP servers; returns a ranked list filtered to MCP-sourced entries
- `tool.inspect` — return metadata about a specific named capability without making it provider-callable; used by the model or the user to learn about a capability before borrowing or invoking

These five capabilities are themselves first-class registered capabilities. They appear in every default `SubsystemSurfaceSpec`'s `primary_capability_ids` by convention so every run can discover and borrow without preparatory steps; subsystems may move them to `Borrowable` if they want to conserve model-request tokens.

### 7.2 Declarations

The discovery capabilities carry the following declarations (per `capability.declaration`, File 05 §3, summarized here at the level of what File 07 must specify):

`tool.borrow`:

- `permission_tier`: `ReadOnly` — loading metadata is read-only and never grants invocation authority of the borrowed capability (the borrowed capability's own tier applies on invocation)
- `concurrency`: `ConcurrencySafe` — multiple borrows in parallel are safe; they each add to the `BorrowGrant` set
- `replay_class`: `deterministic_replayable` — same arguments and registry state produce same result
- `touched_resources`: `{ class: capability-registry, access: read }` — reads Capability Registry state to resolve and expose the borrowed capability's schema, with no external effects (per `capability.touched-resources`, File 05 §6 and the `capability-registry` resource class, File 05 §6.2)
- `idempotent`: true — borrowing twice is no-op the second time
- `preview_mode`: `none` — borrowing is metadata-only
- result: the full capability schema plus the granted `BorrowGrant` record

`tool.borrow_persistent(capability_id, scope)`:

- same as `tool.borrow` except `permission_tier`: `UserApproval` (granting wider scope persists capability presence across runs)
- `touched_resources`: `{ class: capability-registry, access: read }` to resolve the borrowed schema, plus a typed `{ class: capability-registry, access: write }` effect for the persistent surface-visibility grant it records — this cross-run visibility change is the typed, policy-gated effect that distinguishes `tool.borrow_persistent` from the read-only `tool.borrow`
- argument-aware: borrowing for `global` scope may trigger typed-confirmation if the borrowed capability's class is `ActionExternal` per `policy.risk-classification-trust-interaction` (File 06 §15)

`tool.search(query, family, source, top_k)`:

- `permission_tier`: `ReadOnly`
- `concurrency`: `ConcurrencySafe`
- `replay_class`: `deterministic_replayable` (with caveat: the registry is mutable, so results depend on registry state at search time; replay records the registry snapshot id)
- `touched_resources`: `{ class: capability-registry, access: read }` — reads registry state to rank matches; no external effects
- result: ranked list of capability metadata (name, family, short_description, source, current zone, declared tier)

`mcp.search(query, connector_id, top_k)`:

- same as `tool.search` (including `touched_resources`: `{ class: capability-registry, access: read }`) but filtered to MCP-sourced capabilities; optional connector_id (the connector's registry-assigned stable slug, `integration.connector`, File 36 §3.1) narrows to a specific connected server
- result: same shape as `tool.search` plus the MCP-server identity per match

`tool.inspect(capability_id)`:

- `permission_tier`: `ReadOnly`
- `concurrency`: `ConcurrencySafe`
- `replay_class`: `deterministic_replayable`
- `touched_resources`: `{ class: capability-registry, access: read }` — reads registry metadata only; no external effects
- result: declared metadata at the requested detail level without changing zone membership or making the capability callable in provider-native format

`tool.inspect` returns compact metadata by default: name, display metadata, source, family, current zone, declared tier, short input/output summary, and borrow eligibility. Full detail, including full schemas, is available only when requested and allowed by settings, policy, and context budget. Inspecting a capability never changes zone membership and never makes the capability callable.

These declarations are part of the canonical built-in set. They are not optional; an ATLAS3 install ships them registered in the `Builtin` source. Plugins or extensions may register adapter capabilities (per `capability.adapter-capabilities`, File 05 §17.4) that wrap them for specialized presentation, but the canonical ids are stable.

### 7.3 `BorrowGrant`

Anchor: `surface.borrow-grant`

A `tool.borrow` call grants a File 07-owned `BorrowGrant`, not a File 06 approval `Lease`. A `BorrowGrant` is a scoped surface-visibility record. It makes a capability's schema visible in `Primary`; it never authorizes execution. The borrowed capability's own policy tier still resolves at invocation time per `policy.effective-tier-resolution` (File 06 §4).

A `BorrowGrant` carries:

- `capability_match`: exact `(id, version)` of the borrowed capability
- `scope`: `run` by default; `tool.borrow_persistent` lets the user widen
- `invoker_kind`: `model_agent` if the borrow was emitted by the model; `user_direct` if invoked through the palette
- `schema_visible`: true
- `grant_origin`: `tool_borrow_call`
- `revocation_conditions`: standard scope expiry, explicit user revoke, capability unregistration, source unavailability, declaration-version incompatibility, or settings change that disables borrowing for the target

`BorrowGrant` uses the same scope vocabulary as File 06 leases where applicable (`run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`); the `reusable_policy_rule` scope is a policy-lease construct with no surface-visibility meaning and is not a `BorrowGrant` scope. A `BorrowGrant` is not selected by policy evaluation and is not a policy decision. It is stored and audited with surface state; File 20 may co-locate it physically with policy leases, but the semantics stay separate.

If the approval `Lease` for a `tool.borrow_persistent` call is later revoked, existing `BorrowGrant`s survive under their own revocation conditions. Revoking that approval `Lease` means future persistent borrow calls require re-approval; it does not retroactively remove already-granted `BorrowGrant`s.

Composition algorithms see active `BorrowGrant`s and place the borrowed capability in `Primary`. Grant revocation transitions the capability back to its base zone in the next composition.

### 7.4 Search Results

`tool.search` and `mcp.search` return ranked lists. The ranking algorithm is registry-side and combines:

- exact name match — highest weight
- family match
- tag overlap with the query
- description / short_description fuzzy match
- recency of successful invocations (per the execution ledger, optional and settings-controlled)
- declared `cost_model` weight (cheap capabilities preferred for searches with a `prefer_cheap` query flag)

Search results carry the canonical metadata (name, family, short_description, source, current zone in the active surface, declared tier) plus a `borrow_eligibility` flag indicating whether the active surface composition allows the model to borrow this capability. A capability that exists in the registry but is `Disabled`, `Unavailable`, or excluded by `forbidden_capability_ids` in the active `SubsystemSurfaceSpec` returns `borrow_eligibility: denied` with the typed denial reason; the model receives this in-band and may try a different capability or escalate to the user.

### 7.5 Discovery Is Auditable

Every `tool.search`, `mcp.search`, `tool.borrow`, `tool.borrow_persistent`, and `tool.inspect` call is recorded in the execution ledger per `run.execution-ledger` (File 04 §23.1). Audit reconstructs which capabilities the agent searched for, which it borrowed, and which it ultimately invoked. The Quality Control and Evaluation specs (Files 39 and 40) may inspect this trace for tool-use efficiency analysis.

### 7.6 Boundary

The discovery capabilities are the canonical mechanism for agent-initiated surface visibility changes. They are not the only surface-relevant input path: settings changes, plugin install, MCP server connect, `BorrowGrant`s created by other paths, policy changes, and routing decisions all affect composition (per §13). File 07 specifies the contract for agent-initiated discovery; other paths are described in their own sections.

## 8. Default Composition and Auto-Shrink

Anchor: `surface.default-composition-auto-shrink`

### 8.1 Default Composition

The default composition for a fresh `Run`:

1. Resolve the active `SubsystemSurfaceSpec` from `RunIntent.primary_surface` (§5)
2. Place every `primary_capability_ids` entry in `Primary` for the `ModelAgent` lens; the user-facing lenses also see them as `Primary`
3. Place every `borrowable_capability_ids` entry in `Borrowable`
4. Place every capability whose declared family is in `default_deferred_families` into `Deferred`
5. Exclude every capability in `forbidden_capability_ids` from any zone except the inspector (where it appears with a `Forbidden` indicator)
6. For `supporting_surfaces` from `RunIntent` (§6.1): promote their `primary_capability_ids` into the current surface's `Borrowable` zone
7. Apply `tool_surface_strategy` adjustments per §5.3
8. Apply the resolved settings snapshot (per §12.1 and §18) — per-capability zone overrides, per-family zone overrides, always-load marks, and never-load marks (ModelAgent-lens-scoped, §18.1)
9. Apply active `BorrowGrant`s — grants promote their target capabilities to `Primary` for the scope
10. Evaluate `enabled` flag — capabilities disabled at any active scope move to `Disabled`
11. Evaluate availability — capabilities whose `availability_status` is not `Available` move to `Unavailable` regardless of prior zone
12. Apply trust narrowing per `policy.effective-tier-resolution` (File 06 §4) — capabilities from `Community` or `Unverified` sources may shift between zones per source policy
13. Estimate model-request cost of the resulting `Primary` and `Borrowable` zones using provider-aware token counting (per `run.execution-ledger`, File 04 §23.1 and File 13) against the model's context budget
14. If estimated cost exceeds the configured tool-surface budget, run auto-shrink (§8.2)
15. If legal shrink cannot fit the surface, return `ToolSurfaceOverflow`
16. Render `composition_diagnostics` (§2.3) recording every assignment decision and its reason
17. Emit `ToolSurfaceComposed` event with the surface snapshot id (per §13)

### 8.2 Auto-Shrink Algorithm

Anchor: `surface.auto-shrink-algorithm`

When the assembled tool surface's estimated token cost exceeds the configured surface budget (a slice of the model's context window, per File 13), auto-shrink runs deterministically in this priority order:

**Step A — drop `default_deferred_families` already-deferred entries** from the `Borrowable` catalog block. These entries entered `Borrowable` only through `supporting_surfaces` promotion or routing; the subsystem explicitly deferred them.

**Step B — demote `Borrowable` entries beyond a configured `borrowable_cap_count` to `Deferred`**. The capacity cap is a setting (per §18); the default keeps roughly the active subsystem's natural borrowable size. Demoted entries leave the `Borrowable` catalog block in the model request.

**Step C — abbreviate `Borrowable` catalog block** by removing per-family grouping headers and per-entry family annotations, keeping only `name` and `short_description`.

**Step D — demote `Primary` entries that are tagged `experimental`, `low-frequency`, or carry a per-entry `auto_shrink_eligible` settings flag** to `Borrowable`. These entries lose their provider-native callable declarations but remain discoverable.

**Step E — demote `Primary` entries by declared priority** (capabilities with lower declared priority within the subsystem spec are demoted first; the spec may declare an ordering or fall back to alphabetical).

**Step F — emit a typed warning to the user surface** and to the next model request that the tool surface has been heavily shrunk; the model may proactively borrow specific capabilities it needs, and the user may relax the budget through settings or close other context consumers (compaction, attachments, history).

Auto-shrink never moves anything pinned by the user (per §12 always-load marks). It never demotes the discovery capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) below `Borrowable`. It records every demotion in `auto_shrink_record` (per §2.3) so the user can inspect what was shrunk and why.

If pinned `Primary` entries still exceed the provider or model limit after every legal shrink step, composition returns `ToolSurfaceOverflow` instead of demoting pinned capabilities or sending an invalid model request. The error names the pinned entries, estimated size, active limit, and recovery options: choose a larger-context model, unpin tools, move some tools to `Borrowable`, or rely on search/borrow.

### 8.3 Auto-Shrink is Non-Destructive and Always In-Band

Anchor: `surface.auto-shrink-non-destructive`

Auto-shrink does not require user approval. It runs deterministically. It is reversible: the next composition without the budget pressure produces the un-shrunk surface. The agent sees the post-shrink model request with the typed notice that shrink occurred so the agent can adjust its strategy (borrow specific capabilities, defer non-critical work). The user sees the shrink in the surface inspector and through the typed event `ToolSurfaceShrunk` (per §13).

Auto-shrink should preserve stable ordering and cacheable model-request prefixes when possible — demote from the tail of the cacheable prefix before disturbing it, and avoid reordering the stable region. Fitting within the context budget always wins over cache preservation, but the achieved `cache_impact` must be recorded on `auto_shrink_record` (per §2.3): `none` when nothing cacheable moved, `preserved_prefix` when only post-prefix entries moved, `changed_tool_surface_only` when the tool-surface block changed but instruction and region order did not, `changed_instruction_or_region_order` when stable-region ordering changed, and `full_cache_break_likely` when the change very likely invalidates the provider cache. The recorded value lets the user and the context layer see when shrink traded cache efficiency for fit.

The settings system (per §18) controls:

- `budget_token_count` per scope — the token budget the surface is allowed to consume
- `borrowable_cap_count` — the maximum number of `Borrowable` entries
- `shrink_priority` — per-capability or per-family override of the default priority order
- `auto_shrink_enabled` per scope — users may disable auto-shrink; if the resulting surface no longer fits, context assembly receives a typed overflow instead of an over-limit request

### 8.4 Shrink Does Not Affect User-Facing Surfaces

Auto-shrink applies to the `ModelAgent` lens. User-facing lenses (`Palette`, `Voice`, `Shortcut`, `AutomationTrigger`) are not budget-constrained the same way — the user is not paying token cost for a palette view. The user-facing surface always shows the full `Primary` and `Borrowable` set regardless of the agent-side shrink state, with an indicator that the model request is operating under shrink. The user may invoke any capability through the palette regardless of which zone the model sees it in.

### 8.5 Boundary

Auto-shrink is a tool-surface concern. It does not compact the conversation history (`run.boundary-rule`, File 04 §20.1 reports context pressure to the context layer; the context layer decides whether to compact). The two mechanisms cooperate: under context pressure, the context layer may compact history first, the surface composer may shrink the tool surface, or both may run in their own layers without coordination.

## 9. Visibility Composition Resolution Algorithm

Anchor: `surface.visibility-composition-resolution-algorithm`

### 9.1 Algorithm

The visibility composition resolution algorithm is the canonical deterministic function that produces a `ResolvedToolSurface` from inputs.

```
compose_surface(invoker_kind, invocation_lens, scope_context) -> ResolvedToolSurface

scope_context := {
  run_id (optional),
  intent_thread_id, task_id, conversation_id, workspace_id,
  profile_id, primary_surface_id, supporting_surface_ids,
  routing_strategy, routing_metadata,
  tool_allowlist (optional),
  active_world_snapshot_id, active_settings_snapshot_id,
  active_borrow_grant_set_id, active_policy_snapshot_id, active_model_id, active_provider_id,
  active_context_budget,
}

The scope_context's primary_surface_id and active_world_snapshot_id resolve
by invoker: ModelAgent composition uses RunIntent.primary_surface and the
run-resolved world snapshot; graphical Palette, Voice, Shortcut, and
Inspector composition uses the invoking renderer root's world snapshot and
root-resolved surface binding; AutomationTrigger, ExternalMcp, and other
noninteractive composition uses the typed noninteractive presentation
context with no graphical fallback (`world.surface-state`, File 18 §5.1;
`ui.shell`, File 37 §4.4 — never the attention target). The root-qualified
snapshot carries the presentation resolution; scope_context adds no
separate renderer-root input.

Step 1 — Resolve the active SubsystemSurfaceSpec from primary_surface_id.
  If primary_surface_id is conversation or resolves to no subsystem-owned
  surface, resolve the baseline conversation SubsystemSurfaceSpec (§5.1),
  which is always present.
Step 2 — Snapshot the registry:
  Materialize declaration view, enabled state, availability_status, source,
  and registration facts for every RegisteredCapability relevant to the lens.
  Inspector compositions include every registered capability, including
  disabled and unavailable entries.
Step 3 — For each registered capability, compute base_zone:
  a. If id in spec.forbidden_capability_ids => excluded (placed in Inspector only).
  b. Else if id in spec.primary_capability_ids => Primary.
  c. Else if id in spec.borrowable_capability_ids => Borrowable.
  d. Else if capability.family in spec.default_deferred_families => Deferred.
  e. Else => Deferred (the default for everything not declared).
Step 4 — Apply supporting-surface promotion:
  For each supporting_surface_id, collect supporting spec.primary_capability_ids
  and promote into the current surface's Borrowable zone (no change if already Primary).
Step 5 — Apply tool_surface_strategy:
  - use_current_surface_tools: no change.
  - borrow_foreign_capabilities: promote routing_metadata.foreign_caps to Borrowable.
  - load_deferred_capabilities: promote routing_metadata.deferred_caps to Primary.
Step 6 — Apply the resolved settings snapshot (per §18):
  - per-capability zone override: explicit zone assignment.
  - per-family zone override: applies to all capabilities in the family.
  - per-source zone override: applies to all capabilities from the source.
  - per-capability always-load mark: pin to Primary.
  - per-capability never-load mark: clamp to Disabled for the ModelAgent lens (§18.1 — the palette lens is untouched; palette hiding is the separate never-show mark).
  - per-capability never-show mark: hide from palette lens.
Step 7 — Apply active BorrowGrants:
  For each active BorrowGrant whose scope includes the current scope_context:
    The borrowed capability is promoted to Primary for the grant duration.
Step 8 — Evaluate enabled state:
  For each capability:
    - If disabled at any active scope, zone becomes Disabled.
Step 9 — Evaluate per-capability availability:
  For each capability:
    - If registry availability_status != Available, zone becomes Unavailable.
    - If availability_predicate fails against world snapshot, zone becomes
      Unavailable (with typed reason from the predicate evaluation).
    - If prerequisite_capabilities (per `capability.prerequisite-capabilities`, File 05 §15.3) are unsatisfied
      against the active scope, zone becomes Unavailable
      (with typed reason `prerequisite_unsatisfied`).
Step 10 — Apply trust narrowing:
  For capabilities with effective_trust in {Community, Unverified, Sideloaded}:
    Apply the source-approval policy resolution (per `policy.effective-tier-resolution` (File 06 §4.2), `policy.trust-mapping-defaults` (File 06 §9.6)).
    Result: zone may be demoted (Primary -> Borrowable, Borrowable -> Deferred)
    or marked with a trust-narrowing flag the inspector renders.
Step 11 — Apply floor enforcement:
  For each capability:
    Resolve effective tier (per `policy.effective-tier-resolution`, File 06 §4.2).
    If permission_floor is Denied and no typed-confirmation override is configured,
      zone is clamped to Disabled for the ModelAgent lens (agent cannot invoke);
      remains visible in palette and inspector per user customization.
Step 12 — Filter by invocation lens:
  The lens filter runs after every promotion path (supporting-surface
  promotion, tool_surface_strategy, active BorrowGrants, forced tool choice,
  and always-load pins); no promotion path overrides it, so a capability that
  lacks the lens's required tag is excluded even when a promotion placed it in
  a zone. Tag-based filtering obeys lens_filter_strictness (§9.4, default
  strict): under strict a capability must explicitly carry the lens tag to
  appear; under permissive it is eligible unless explicitly excluded.
  Apply per-lens filters:
    - ModelAgent: capability.tags must include 'agent-invokable'.
    - ProgrammaticUnit: no tag filter; resolve capabilities by id against the
                   unit's enumerated allowed set, and File 06 policy applies to
                   each resolved id.
    - Palette: capability.tags must include 'palette-invokable'.
    - Voice: capability.tags must include 'voice-invokable'.
    - Shortcut: capability has default_shortcut OR user-bound shortcut.
    - AutomationTrigger: capability.tags must include 'automation-trigger'.
    - ExternalMcp: capability.tags must include 'external-exposed'
                   AND source-approval permits external exposure.
    - Inspector: no filter; all entries surfaced (including Disabled, Unavailable).
  Capabilities filtered out for the lens are excluded from this lens's zoned
  entries — a lens-local exclusion, not the registry Disabled zone — with
  diagnostic note `lens_filter_excluded`.
Step 13 — Apply child-run tool_allowlist (if scope_context.tool_allowlist is present):
  Capabilities not in the allowlist are excluded from this composition
  (per `run.isolation` (File 04 §16.2)), with diagnostic note
  `child_allowlist_excluded`.
Step 14 — Estimate model-request cost (ModelAgent lens only):
  Sum estimated tokens for all Primary entries' full schemas + Borrowable
  catalog block + discovery capabilities catalog.
Step 15 — Apply auto-shrink if estimated cost > active_context_budget.tool_surface_budget:
  Run the auto-shrink algorithm (§8.2). Record every demotion in
  auto_shrink_record. The Primary and Borrowable sets after shrink are the
  rendered sets.
Step 16 — If legal shrink cannot fit the surface:
  Return ToolSurfaceOverflow with pinned entries, estimated size, active limit,
  and recovery options.
Step 17 — Produce ResolvedToolSurface:
  - surface_id = stable hash over (invoker_kind, invocation_lens,
    scope_context.snapshot, registry snapshot id, settings snapshot id,
    borrow-grant set id, post-shrink zones, provider_name_map).
  - zoned_entries grouped by zone.
  - provider_name_map if provider-visible names were rendered.
  - composition_diagnostics with per-capability reason for assignment.
  - auto_shrink_record (empty if no shrink).
Step 18 — Emit ToolSurfaceComposed event with surface_id and diagnostic facts
  for the inspector and the ledger.
```

### 9.2 Determinism

The algorithm is deterministic given the same inputs. Two compositions with the same `scope_context`, the same registry snapshot, the same settings snapshot, and the same `BorrowGrant` snapshot produce byte-identical `ResolvedToolSurface` outputs and byte-identical rendered model-request surface content. This is the load-bearing property for cache friendliness where supported (per `run.from-run-intent-to-run`, File 04 §3) and replay (per `run.ledger-events-commits`, File 04 §23 and File 10).

### 9.3 Caching

The algorithm's result is cached keyed by the input snapshot identifiers. A subsequent composition with the same inputs returns the cached `ResolvedToolSurface` without re-running every step. Cache invalidation is event-driven, not time-based — see §13 for the mutation events that invalidate cached compositions.

### 9.4 Algorithm Settings

The algorithm's behavior is configurable through settings (per §18):

- `auto_shrink_enabled` — whether auto-shrink runs at all
- `budget_token_count` — the model-request budget for tool definitions; default is a fraction of the model context window
- `borrowable_cap_count` — the maximum number of `Borrowable` entries before forced demotion
- `lens_filter_strictness` — `strict` (default; a capability must explicitly carry the lens tag to appear in the lens) or `permissive` (capabilities are eligible unless explicitly excluded). A capability that a `SubsystemSurfaceSpec` lists in `primary_capability_ids` or `borrowable_capability_ids` but that lacks the corresponding lens tag is silently excluded under `strict`; registration emits a validation warning for such spec-listed-but-untagged capabilities so the omission surfaces at registration rather than as an unexpectedly empty model-request surface at runtime
- `trust_narrowing_active` — whether trust narrowing affects zone assignment or only displays inspector-side flags
- `forbidden_visible_in_palette` — whether capabilities in `forbidden_capability_ids` for the active surface still appear in palette with a disabled indicator (default true for inspectability)
- `unavailable_visible_in_palette` — whether `Unavailable` entries appear in palette (default true with a "currently unavailable" indicator)
- `default_deferred_visible_in_palette` — whether `Deferred` entries appear in palette by default (default false; user can choose to reveal)

### 9.5 Boundary

The algorithm is the canonical contract. Implementations may use any data structure, any caching strategy, any concurrency model that produces byte-identical results from identical inputs. File 42 defines the implementation patterns; File 07 defines the contract.

## 10. Tool Surface and Capability Policy

Anchor: `surface.tool-surface-capability-policy`

### 10.1 Boundary

The boundary between surface and policy is sharp:

- Surface (File 07) controls **visibility** — whether the capability appears in the model request, in the palette, in the voice grammar, in the automation editor
- Policy (File 06) controls **authority** — whether a proposed invocation of a visible capability proceeds, requires user approval, requires typed confirmation, or is denied

A capability can be visible without being permitted. The model sees `git.push --force` in `Primary` (the capability is loaded into the surface) and, when the model proposes the call, the policy layer evaluates the effective tier. If the branch is in the protected-branch list (per `policy.built-in-reusable-policy-rules`, File 06 §11.5 built-in reusable-policy rules), the proposed call is denied at typed-confirmation; the agent receives a typed in-band denial per `run.denial-is-in-band` (File 04 §8.3).

A capability can be permitted without being visible. The user invokes a capability through the palette that is in `Deferred` for the model's surface — the policy layer evaluates the user-direct invocation the same way it evaluates an agent-direct invocation. The capability is invocable; the model just did not have it in its model request.

### 10.2 Visibility Customization Honors Policy

Users may choose to hide capabilities they cannot use anyway (capabilities at `Denied` floor without typed-confirmation override). Users may choose to show them anyway for transparency. The settings dimension `policy_blocked_visible` (per §18) controls this. The composition algorithm honors the setting; the result is the same effective denial behavior regardless of visibility, because policy is the authority layer.

### 10.3 Source-Approval Affects Surface

When a plugin, MCP server, external API, or user-defined capability registers (per `capability.runtime-mutation`, File 05 §16.2 and `policy.source-approval-flow` (File 06 §9)), the source-approval flow runs. Until the flow completes, the source's capabilities are in `Disabled` zone for all invokers. When the flow grants any policy state, the affected capabilities transition to their declared zones; transitions emit surface-relevant events (per §13). Source-approval revocation (the user denies the source or the source connection is lost) demotes the capabilities back to `Disabled` or `Unavailable` depending on the underlying state.

### 10.4 Policy Events Inform the Surface

The surface inspector lens surfaces policy-relevant facts the user may want to see: which capabilities are currently at floor `Denied`, which are subject to a `Sensitive` data classification (per `run.event-stream`, File 04 §23.2), which are typed-confirmation-required, which currently carry a `Stale` lease the user may want to re-grant. This information is read from File 06 policy state, not duplicated in File 07. The surface uses the read; it does not own the state.

### 10.5 Boundary

File 07 reads from File 06 to decide presentation. File 07 does not duplicate policy state. File 07 does not implement approval evaluation. The composition algorithm (§9) consumes policy-resolved facts as inputs to its surface-rendering decisions; the policy evaluation itself runs in File 06's layer.

## 11. Presentation in the Model Request

Anchor: `surface.presentation-in-model-request`

### 11.1 Position in the Model Request

Tool surface content occupies a deterministic position in the assembled model request:

- After the identity and core-instructions section (per File 13)
- Before the conversation history and current user message
- The `Primary` entries render first as provider-native callable declarations where the provider supports them
- The `Borrowable` catalog block renders next as model-request text content
- Optionally, a typed `auto_shrink_record` notice renders after the catalog if shrink occurred
- The discovery capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) render alongside other `Primary` entries — they are first-class registered capabilities, not a separate hint section

The position is stable across turns. Two consecutive turns with the same `ResolvedToolSurface` produce byte-identical surface content up to the moment the conversation history changes, enabling provider cache reuse where the provider supports it.

### 11.2 Per-Provider Format Normalization

The native tool-call format varies by provider (per `run.tool-calls`, File 04 §9 and `capability.schemas` (File 05 §4) `capability.discovery` (File 05 §15.1)). The composition algorithm produces a canonical `ResolvedToolSurface`; the provider adapter (per File 17) renders `Primary` entries as provider-native callable declarations when possible and records `provider_name_map` for any provider-visible renaming. File 07 specifies the canonical content; provider adapters render.

The native-format rendering preserves:

- `name` — capability id, primary alias, or provider-safe name with a recorded `provider_name_map` entry
- `description` — localized full description
- `input_schema` — declared JSON Schema converted to provider's schema dialect
- Optional hint fields — for providers that accept them, hints derived from `tags` or `cost_model` that help the model choose between capabilities

The native-format rendering omits:

- internal touched-resource expressions (per `capability.resource-expressions`, File 05 §6.4) — these are policy-side; the model does not need them
- backend descriptor (per `capability.backend-descriptor`, File 05 §3.12) — implementation detail
- per-call resolved facts (per `capability.invocation-record`, File 05 §11) — these belong to the invocation record, not the declaration

### 11.3 Tool Metadata Is Data, Not Instruction

Capability descriptions, schemas, MCP metadata, plugin metadata, external-API descriptors, and user-defined capability text are untrusted data when rendered into the model request. They do not gain instruction authority by appearing near callable declarations or catalog entries.

External or source-authored descriptions must have source attribution rendered alongside them, length limits per external description configurable by source class, and explicit instruction-boundary markers in the assembled model request. External descriptions are placed inside a clearly delineated data section, and the model's governing instructions identify that section as untrusted data, not instructions. Textual filtering of injection phrases is not a correctness mechanism; the boundary is architectural.

### 11.4 Borrowable Catalog Block Format

The `Borrowable` catalog block is rendered as a single text block (not as native tool declarations, which would consume too many tokens). Its format:

```
You can borrow additional tools at the cost of one round-trip via the
`tool.borrow(capability_id)` capability. Borrowed tools are available for the
active BorrowGrant scope.

Borrowable tools available:
- family/name — short_description
- family/name — short_description
- ...
```

The block is alphabetized by family then by name within family for cache-friendliness. The model can scan the list and emit `tool.borrow(family.name)` to load the full schema. The block is model-request text content, not a tool result.

### 11.5 Deferred Capabilities Are Not in the Model Request

`Deferred` entries are not rendered into the model request at all. The model knows about them only through:

- explicit hints injected by the user message ("use the data analysis tools")
- hooks that inject hints based on task context (per `run.hook-integration`, File 04 §23.3)
- the model's own decision to call `tool.search` to discover what is available

Keeping `Deferred` entries out of the model request is the load-bearing request-economy decision. A `Borrowable` catalog of fifty entries is cheap; a `Deferred` set of five hundred is too expensive to render — search-based discovery is the design.

### 11.6 Empty Model-Request Surface

If the composition algorithm produces no `Primary` entries (e.g., `execution_entry` is `respond_inline` and no surface or routing strategy contributed Primary capabilities), the model request's callable-declaration section is empty. The native provider format omits the tools field where appropriate (per `run.tool-calls`, File 04 §9 and File 17).

The full `tool_choice` enumeration and the interaction of an empty surface with each mode — including the `EmptyToolSurfaceWithRequiredChoice` failure and `specific_tool` promotion — are owned by Tool-Choice Mechanics (§16); this section specifies only the request-rendering consequence: an empty `Primary` set renders an empty callable-declaration section. `tool_choice` is set by `RunIntent.execution_entry` and the active model strategy per `run.execution-entry` (File 04 §4) and `routing.model-routing` (File 03 §7).

### 11.7 Cache-Friendly Ordering

Anchor: `surface.cache-friendly-ordering`

Within `Primary`, capabilities are rendered in a deterministic order:

1. Discovery capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) first — they are always present in `Primary` (unless explicitly demoted by settings) and their stable position makes them part of the cached prefix
2. Capabilities from the active `SubsystemSurfaceSpec.primary_capability_ids` in their declared order
3. Capabilities promoted from `supporting_surfaces` in their respective subsystem order
4. Capabilities promoted by `tool_surface_strategy` in the order specified in `routing_metadata`
5. Capabilities promoted by active `BorrowGrant`s in grant order

This order is the canonical cache-friendly ordering. Changing the order (for example, sorting alphabetically every turn) can invalidate cached request prefixes. The settings dimension `model_request_order_strategy` allows users to choose alternative orderings (alphabetical, frequency-based).

### 11.8 Boundary

File 07 specifies what surface content exists and in what order. The actual model-request assembly — combining the surface with the rest of the request sections, applying cache markers, and enforcing request-size invariants — is File 13's concern. File 07 hands the rendered surface content to context assembly; context assembly composes the full model request.

## 12. Presentation in User-Facing Surfaces

Anchor: `surface.presentation-in-user-facing-surfaces`

### 12.1 Palette Lens

The `Palette` lens renders the surface as a searchable user-facing list. The rendered data per entry:

- `display_name` (per `capability.display-fields`, File 05 §3.2) localized
- `description` and `short_description` localized
- `family` for grouping
- `tags` for filtering
- `icon_key` (per `capability.display-fields`, File 05 §3.2) for visual identification (the actual icon image is owned by File 37)
- `default_shortcut` (per `capability.display-fields`, File 05 §3.2) and any user-bound shortcut for inline display
- `source` for source filtering
- `effective_tier` (resolved per `policy.effective-tier-resolution` (File 06 §4)) for showing approval indicators ("requires approval", "typed-confirmation required", "blocked", "trusted")
- `availability_status` (per `capability.registered-capability`, File 05 §10) for showing currently-unavailable entries
- `zone` for visual grouping (Primary appears prominently; Borrowable appears slightly de-emphasized; Deferred appears only if user revealed)

The palette consumes this typed data and renders. File 07 specifies the data; File 37 specifies layout, color, animation, search behavior.

### 12.2 Voice Lens

The `Voice` lens filters capabilities tagged `voice-invokable` (per `capability.display-fields`, File 05 §3.2). Each entry carries:

- `display_name` and `description`
- `voice_aliases` — the spoken phrases that map to this capability (per `capability.display-fields`, File 05 §3.2); examples like "read the file", "open the project", "send an email"
- `argument_extraction_hints` — typed hints for the voice-to-arguments extraction (per File 26)
- `effective_tier` — voice invocation may produce a typed-confirmation request for high-tier capabilities (per `policy.approval-ui-surface-contract`, File 06 §13)

Voice invocation invokes the capability through the same `run.call-pipeline` (File 04 §8.2) pipeline as agent or user invocation. The voice resolver is just another invoker.

### 12.3 Shortcut Lens

The `Shortcut` lens renders a chord-to-capability map. Entries are capabilities with a declared `default_shortcut` or a user-bound shortcut. The chord format is per File 26 (the keymap); File 07 specifies that:

- A declaration collision — two capabilities declaring the same `default_shortcut` — is detected at registration time and produces a `ShortcutConflict` event (per §13); the registry rejects the second registration unless explicitly overridden, so no two declared defaults silently claim one chord
- A binding collision — a user-bound shortcut that lands on a chord already bound in the same keybinding context — is not a registration rejection; it resolves through the keymap's precedence rules (a user-bound shortcut overrides a capability's `default_shortcut`, and same-context collisions resolve through the declared priority order) per File 26 §7.5
- Shortcuts are keybinding-context-aware: the same chord may invoke different capabilities depending on the active keybinding context.

### 12.4 Inspector Lens

Anchor: `surface.inspector-lens`

The `Inspector` lens shows the full registry catalog with no filtering — every registered capability, in every zone (including `Disabled`, `Unavailable`, `Forbidden`). The inspector lens is the canonical management surface; File 38 renders the inspector as a tab or panel with:

- Per-source enable/disable toggle
- Per-family enable/disable
- Per-capability enable/disable
- Per-capability zone override (always-load, never-load, always-deferred, never-show-in-palette)
- Search and filter by family, source, tag, risk class, effective tier
- Group-by axis selection (family, source, risk class, integration-source, invocation-path)
- Per-source trust override (per `policy.risk-classification-trust-interaction`, File 06 §15)
- Per-capability shortcut binding
- Inspection of declared metadata (description, input/output schemas, touched_resources expressions, replay class, postconditions)
- Inspection of recent invocations (per File 10)

The inspector's data contract is the canonical surface customization surface. Users do not need to write settings files manually — the inspector renders the same data the resolved settings snapshot contains.

### 12.5 Automation Trigger Lens

The `AutomationTrigger` lens filters capabilities tagged `automation-trigger` and capabilities that can be invoked as automation actions. The lens carries:

- per-capability `automation_input_template` — typed structure naming which inputs are required, which are derived from trigger context (event payload, scheduled context, watch state), which are pinned at save time
- per-capability `automation_constraints` — typed constraints File 33 (Automation and Triggers) evaluates (e.g., automation cannot invoke capabilities with `replay_class: not_replayable`)

### 12.6 External MCP Lens

The `ExternalMcp` lens filters capabilities tagged `external-exposed` and renders them as MCP-protocol tool advertisements. The lens carries:

- `mcp_tool_name` — typically the canonical id, possibly with a per-source rename for protocol compatibility
- `mcp_description` and `mcp_input_schema` — JSON Schema as MCP expects
- `mcp_metadata` — per-tool metadata MCP clients may use

External MCP exposure is gated by source-approval (per `policy.source-approval-flow`, File 06 §9). Capabilities not approved for external exposure are filtered out of this lens.

### 12.7 Per-Lens Visibility Rules

Each lens enforces its own visibility rules in step 12 of the composition algorithm (§9.1). A capability with tags `[agent-invokable, palette-invokable]` appears in `ModelAgent` and `Palette` lenses but not in `Voice` or `Shortcut`. A capability with only `[agent-invokable]` appears only in the `ModelAgent` lens; the model can call it, but the user cannot invoke it through the palette. The visibility tags are part of the declared `tags` field per `capability.display-fields` (File 05 §3.2); users may customize per-capability through settings (per §18).

### 12.8 Boundary

File 07 specifies the per-lens data contract. File 37 and File 38 render those contracts into actual UI. File 26 (the Voice rail) specifies voice-to-arguments extraction. File 33 (Automation and Triggers) specifies trigger evaluation and action invocation. File 07 hands them the canonical lens data and the lens-filter algorithm.

## 13. Surface-Relevant Events

Anchor: `surface.surface-relevant-events`

### 13.1 Event Vocabulary

Every surface-relevant input change, grant change, source lifecycle change, or consumed composition emits a typed event through the canonical event bus with the standard envelope (per `run.event-stream`, File 04 §23.2): `conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`. The canonical surface-relevant events are:

- `ToolSurfaceComposed { surface_id, invoker_kind, scope_context_id, zone_counts, auto_shrink_record }` — a new surface composition produced
- `CapabilityBorrowed { surface_id, capability_id, capability_version, borrow_grant_id, grant_scope, borrowed_by }` — a `tool.borrow` granted a `BorrowGrant`
- `CapabilityBorrowReturned { surface_id, capability_id, borrow_grant_id, reason }` — a `BorrowGrant` was revoked or expired
- `CapabilityZoneChanged { surface_id, capability_id, old_zone, new_zone, reason }` — a zone reassignment for a capability across compositions (typically from settings change, grant change, availability change, trust change)
- `CapabilityRegistered { capability_id, capability_version, source, default_zone }` — a new capability registered (per `capability.events`, File 05 §12.2); the active composition incorporates it on next computation
- `CapabilityUnregistered { capability_id }` — a capability removed from the registry; active surfaces lose the entry
- `CapabilityEnabledChanged { capability_id, enabled, scope }` — enable/disable change at any scope
- `CapabilityAvailabilityChanged { capability_id, old_status, new_status, reason }` — `availability_status` transition (handler unresolved, MCP disconnect, platform mismatch detected, prerequisite satisfied/unsatisfied)
- `ToolSurfaceShrunk { surface_id, demoted_capability_ids, budget_consumed, budget_limit }` — auto-shrink demoted capabilities
- `ToolSurfaceOverflow { surface_id, pinned_capability_ids, estimated_size, active_limit, recovery_options }` — composition could not legally fit the required surface
- `SubsystemSurfaceSpecUpdated { subsystem_id, old_version, new_version, affected_surface_ids }` — a subsystem changed its declared default surface contract
- `PrimarySurfaceChanged { run_id, old_primary_surface_id, new_primary_surface_id, reason }` — the active `SubsystemSurfaceSpec` changed mid-run (typically through reroute per `routing.mid-execution-reroute` (File 03 §12))
- `SurfaceSettingsChanged { scope, settings_keys_changed }` — surface-relevant settings mutated; affected compositions recompose
- `SourceConnected { source_id, source_kind }` — a plugin loaded, MCP server connected, external-API definition imported; the surface incorporates the source's capabilities on next composition (subject to source-approval per `policy.source-approval-flow` (File 06 §9))
- `SourceDisconnected { source_id, source_kind, reason }` — a source disconnected; its capabilities transition to `Unavailable`
- `LensFilterChanged { lens, scope }` — per-lens visibility settings changed
- `ShortcutConflict { conflicting_capability_ids, chord }` — a shortcut collision was detected

### 13.2 Event Sensitivity

Surface-relevant events carry the canonical `sensitivity` tag (per `run.event-stream`, File 04 §23.2). Most surface events are `Public` (no secret content). Events that touch credentials or sensitive sources may be `Sensitive` (per the underlying capability's `data_sensitivity` declaration); events naming raw secrets are `Secret` and never persisted to the durable ledger.

### 13.3 Event Consumers

Surface-relevant events are consumed by:

- the model context — the next assembled model request for an active `Run` incorporates the change (recomposing the surface, emitting an in-band notice if the change is relevant to the model's plan)
- the UI — the palette, inspector, and other user-facing surfaces re-render on every relevant mutation
- the execution ledger — events relevant to audit and replay are persisted (per `run.execution-ledger`, File 04 §23.1)
- hooks subscribed to surface events — extensions, plugins, and user hooks may react to surface-relevant changes (per `run.hook-integration`, File 04 §23.3)

### 13.4 Mid-Run Change Notification to the Model

When a surface-relevant change occurs during an active `Run`'s execution (between model turns or between iterations of the model/tool loop per `run.model-tool-loop` (File 04 §7)), the next assembled model request includes a typed notice describing the change. Notices are short structured text lines:

- `[surface] Capability borrowed: web.fetch — now available in Primary.`
- `[surface] Capability went unavailable: gui.screenshot — accessibility permissions revoked.`
- `[surface] MCP server connected: linear-mcp — 18 new capabilities available in Borrowable.`
- `[surface] Auto-shrunk: 12 capabilities demoted from Primary to Borrowable — context budget tight.`
- `[surface] Primary surface changed: now using Web — tool surface recomposed.`

The notice format is a settings-controlled rendering choice; the canonical contract is that mid-run surface changes are visible to the model so it can adjust strategy. The model may also call `tool.inspect` or `tool.search` after a mutation to confirm what is available.

### 13.5 Event Stream Versus Durable Ledger

Per `run.ledger-events-commits` (File 04 §23), the event stream is the live coordination channel; the ledger is the durable history. Surface-relevant events flow through both: every event emits to the event stream so consumers react in real time, and consequential events (capability registrations, `BorrowGrant`s, surface compositions consumed by a model turn) are also recorded in the durable ledger so replay and audit work.

### 13.6 Boundary

File 07 specifies the event vocabulary and per-event payload. The event-bus implementation (delivery semantics, subscription mechanics, replay) is owned by `run.ledger-events-commits` (File 04 §23) and File 10. File 07 names what is emitted; those specs handle the channel.

## 14. Persistence and Reconstruction

Anchor: `surface.persistence-reconstruction`

### 14.1 What Persists Durably

The following are durable:

- the Capability Registry — registered capabilities and their `RegisteredCapability` state (per `capability.registered-capability`, File 05 §10) survive restart
- per-scope settings — per-workspace and per-conversation surface customization persists through the settings system; profile-specific defaults are profile layers; run and per-call changes are invocation overlays
- `BorrowGrant`s — durable grants at scopes `intent_thread`, `task`, `conversation`, `workspace`, `global` survive restart until their revocation conditions apply
- the execution ledger — every `ResolvedToolSurface` consumed by an invocation is recorded with surface_id, composition_diagnostics, and zoned_entries; replay can reconstruct the exact surface a past invocation saw

The following are not persisted as independent state:

- `ResolvedToolSurface` — surfaces are computed; they are not stored as a separate mutable record. The ledger records consumed surfaces, but the active surface for a running run is always re-derived from current inputs
- per-turn rendered model requests — the assembled model request for any specific turn is reconstructible by re-running composition with the recorded settings, `BorrowGrant`, and registry snapshots

### 14.2 Reconstruction Across Restart

Anchor: `surface.reconstruction-across-restart`

On process restart (per `run.cancellation`, File 04 §17.3 process restart and `capability.lifecycle` (File 05 §16.6) registry restart):

1. The Capability Registry re-registers its capabilities (built-in, subsystem, plugin, MCP, API, user-defined) in the order specified by `capability.startup-registration` (File 05 §16.1)
2. The settings system reloads per-scope settings
3. The `BorrowGrant` store reloads durable grants; grants that target unregistered capabilities revoke or become stale according to their recorded revocation conditions
4. Capability availability is re-evaluated against the active world-model snapshot
5. Source connections (MCP servers, plugins) re-establish per their own lifecycles; unavailable sources produce `Unavailable` capabilities until reconnect
6. Any `Run`s that were active at restart follow the orphan-run rules per `run.cancellation` (File 04 §17.3); their surfaces are not auto-resumed
7. New runs compose fresh surfaces from the restored state

The restored state is deterministic given the same registry state, settings, and `BorrowGrant` set. The surface a new run sees after restart is the same surface a new run would have seen before restart, modulo any changes that occurred during the offline interval (plugin updates, settings changes the user made through cold-edit tooling, etc.).

### 14.3 Reconstruction Across Retry, Edit, Reroute, Branch

Anchor: `surface.reconstruction-across-retry-edit-reroute-branch`

Per `run.retry-reroute-branch` (File 04 §19), retry, edit, reroute, and branch produce new runs linked to prior ones. The surface composition for each new run runs against the current inputs (which may differ from the prior run's inputs if settings or routing changed). The prior run's surface is preserved in the ledger; the new run's surface is freshly composed.

Run-scoped `BorrowGrant`s do not transfer across retry, edit, reroute, or branch — the new run is a fresh run, and the grant did not span runs. `BorrowGrant`s at wider scopes (`intent_thread`, `task`, `conversation`, etc.) do transfer per their scope rules.

### 14.4 Reconstruction in Child Runs

Per `run.child-runs-multi-agent-work` (File 04 §16), a child run runs with its own surface. The child's primary surface is determined by the child's `RunIntent` per File 03 routing; child runs may inherit the parent's primary surface or transition to a different surface.

The child run's surface is composed fresh from the resolved settings snapshot applicable to its scope, but it does not inherit the parent's run-scoped `BorrowGrant`s by default. A child run may borrow capabilities its parent had borrowed (the same capabilities are still in the registry), but the `BorrowGrant` is granted to the child's run id, not inherited from the parent.

The child run's tool surface is constrained by its declared `tool_allowlist` per `run.isolation` (File 04 §16.2) — if the parent run declares the child run can only use a subset, the child's surface composition applies the allowlist in the dedicated child-run allowlist step (§9.1 Step 13), carried on `scope_context.tool_allowlist`.

### 14.5 Reconstruction in Edit-Reroute

Per `routing.edit` (File 03 §11.2), editing a prior user message invalidates the prior route and the edited request must be rerouted. The rerouted request produces a new `RunIntent` whose `tool_surface_strategy` may differ from the original. The new run composes its surface from the new `RunIntent`; the prior run's surface remains in the ledger for inspectability.

### 14.6 Boundary

File 07 specifies what is computed versus what is durable, and how reconstruction works. The actual storage of `BorrowGrant`s, policy leases, settings, and ledger entries is owned by File 20. The actual replay machinery is owned by File 10. File 07 names the persistence contract; storage realizes it.

## 15. MCP and Plugin Tool Integration

Anchor: `surface.mcp-plugin-tool-integration`

### 15.1 Sourced Capabilities Enter the Single Registry

Per `capability.sourcing` (File 05 §9), capabilities sourced from MCP servers (`McpServer`), plugins (`Plugin`), external APIs (`Api`), or user definitions (`UserDefined`) enter the same Capability Registry through the same registration pipeline as built-in and subsystem capabilities. There is no parallel "MCP tool list" or "plugin tool catalog" — there is one registry, and source is metadata on the registered entry (per `capability.sourcing-equivalence`, File 05 §9.3).

File 07 surfaces consume this registry uniformly. The composition algorithm (§9) does not distinguish source kinds in its core logic; per-source filters and per-source trust narrowing are settings-driven options applied during the settings-override and trust-narrowing steps (§9.1 Steps 6 and 10), but the surface itself is built from the registry, not from per-source registries.

### 15.2 MCP Server Lifecycle and the Surface

MCP server connect → MCP server's tools register into the Capability Registry → next surface composition incorporates them, subject to source-approval (per `policy.source-approval-flow`, File 06 §9). MCP server disconnect → registered MCP-sourced capabilities transition to `availability_status: unavailable_handler`; next composition shows them as `Unavailable`. MCP server reconnect → capabilities transition back to `Available`; next composition restores them to their declared zones.

The reconnection should preserve identity (per `capability.trust-source-approval-flow`, File 05 §9.2): the same `mcp.<connector_slug>.<tool_name>` capability id is re-resolved to the same registered entry. The `connector_slug` segment is the registry-assigned stable slug for the MCP connector (per `capability.id`, File 05 §13.1), not the connector's mutable display name; renaming the connector's display name does not change the `connector_slug`, and therefore does not change capability identity or invalidate active `BorrowGrant`s. Re-registration is the normal path; the registry detects idempotent registration and updates the `resolved_backend_binding` without changing identity.

### 15.3 Plugin Lifecycle and the Surface

Plugin install → plugin's capabilities register; user reviews source-approval; surface incorporates approved capabilities. Plugin uninstall → capabilities unregister; surface loses them.

Plugin update → declared as a new declaration version (per `capability.version`, File 05 §13.4). If the new version is a minor or patch update, surfaces continue to load the new version transparently. If it is a major version with breaking changes (per `capability.version`, File 05 §13.4 semver), affected `BorrowGrant`s become stale or revoke per their revocation conditions; the model receives a typed notice on next turn that affected capabilities have a new version available.

### 15.4 Large MCP Registries

For MCP servers with large tool catalogs, the default loading behavior is conservative:

- All MCP-sourced capabilities default to `Borrowable` for the `ModelAgent` lens if the active `SubsystemSurfaceSpec` does not explicitly place them in `Primary`
- The `Borrowable` catalog block grows; auto-shrink (§8) may demote MCP-sourced entries first if budget pressure rises
- The model can use `mcp.search` to filter the MCP entries by family or query without rendering all of them in the model request
- Per-server enable/disable lets the user keep the registry without seeing every server's capabilities in every surface

A user who is actively working with a specific MCP server's tools can promote them to `Primary` through per-server settings (per §18); the workspace-level setting effectively makes that server's tools first-class for the workspace.

### 15.5 Source-Approval Affects Initial Zone

When a source registers and passes source-approval, the source-approval flow's outcome determines initial zone placement:

- `AcceptDefaults` — source's capabilities enter the registry at their declared default zones (per their declarations and the active `SubsystemSurfaceSpec`); if no `SubsystemSurfaceSpec` mentions them, they default to `Borrowable` for the `ModelAgent` lens
- `CustomizePerCapability` — per-capability zone is set explicitly by the user during source-approval
- `CustomizePerSource` — per-source trust override and default-zone preference is recorded; future capability registrations from this source apply the source-default
- `DenyOutright` — source's capabilities enter `Disabled` zone
- `DeferSourcePolicy` — source's capabilities enter `Unavailable` zone (`unavailable_handler` reason: "pending source policy"); each invocation falls through to ask-user per the fallback policy

### 15.6 External APIs and User-Defined Capabilities

External-API capabilities (declared in TOML or equivalent per `capability.capability-source` (File 05 §9.1)) load at startup or when the definition file is loaded; surface composition treats them like any other capability. User-defined capabilities registered through `tools.register_custom` (per `capability.runtime-mutation`, File 05 §16.2) enter at the declared scope (`conversation`, `workspace`, `global`). User-defined `conversation`-scoped capabilities are visible only to runs in that conversation; the composition algorithm filters by scope.

### 15.7 Boundary

File 07 specifies how source-derived capabilities surface. The actual MCP transport, plugin install lifecycle, external-API definition format are owned by File 36 (MCP and External Integrations) and File 35 (Extension and Plugin System). File 07 consumes their registered output through the unified registry contract from File 05.

## 16. Tool-Choice Mechanics

Anchor: `surface.tool-choice-mechanics`

### 16.1 `tool_choice` Settings

Per `run.execution-entry` (File 04 §4) and the active provider's tool-call format, every model invocation carries an explicit or implicit `tool_choice`:

- `auto` (default) — model decides whether to call a tool based on the rendered surface
- `none` — model produces text only; the surface is rendered without tool declarations or rendered with an explicit "tools disabled" indicator depending on the provider
- `required` — model must call at least one tool; the surface must contain at least one Primary entry
- `specific_tool(id)` — model must call the named tool; the surface must contain that tool in Primary or it is promoted by the routing layer

`tool_choice` is set by the routing layer per `RunIntent.execution_entry`:

- `respond_inline` typically maps to `tool_choice: none`
- `respond_with_tools` typically maps to `tool_choice: auto`
- `surface_runtime` may map to `tool_choice: auto` or `specific_tool` depending on the primary surface's entry pattern
- `multi_step_agent` typically maps to `tool_choice: auto`

### 16.2 Empty Surface Handling

If composition produces zero `Primary` entries and the active `tool_choice` is `auto` or `required`:

- `auto` — render the surface as empty (no tools advertised); model produces text only
- `required` — composition fails with typed error `EmptyToolSurfaceWithRequiredChoice`; the executor returns a typed denial to the routing layer; routing may downgrade to `respond_inline` and recompose, or surface the error

Empty surfaces happen rarely. They occur when:

- the active `SubsystemSurfaceSpec` declares no primary capabilities (a subsystem that exclusively delegates to subagents)
- routing chose `respond_inline` and no preparatory tool calls were registered (the typical conversation-only response)
- all primary capabilities are currently `Unavailable` and no auto-promotion fills the gap

### 16.3 Forced Tool Choice

When `tool_choice: specific_tool(id)` is set, the composition algorithm promotes the named capability to `Primary` regardless of its base zone, subject to:

- `enabled` is true at the active scope
- `availability_status` is `Available`
- the capability is not in `forbidden_capability_ids` for the active surface
- the effective tier (per `policy.effective-tier-resolution`, File 06 §4) does not yield `Denied`
- the capability carries the `agent-invokable` tag — forced tool choice promotes across zones but does not override the lens filter (§9.1 step 12)

If any of these conditions fails, the executor returns a typed denial `ForcedToolChoiceUnavailable { capability_id, reason }` — the `reason` names the failed condition, including `lens_tag_missing` when the capability lacks the `agent-invokable` tag. Routing handles the denial.

### 16.4 Boundary

`tool_choice` is set by routing and consumed by the active provider's tool-call format. File 07 specifies how the surface composition interacts with the chosen mode. File 03 owns routing's choice; `run.tool-calls` (File 04 §9) owns provider parser variation.

## 17. Degradation and Graceful Absence

Anchor: `surface.degradation-graceful-absence`

### 17.1 Availability Transitions Mid-Active

A capability's `availability_status` (per `capability.registered-capability`, File 05 §10) may transition during an active `Run`. Common triggers:

- the underlying handler became unresolvable (MCP server crashed, plugin module unloaded, sandboxed process exited)
- a prerequisite capability was unregistered or its required state lapsed
- a platform-dependent resource became unavailable (accessibility API permission was revoked, GPU device went offline)
- a credential expired or was revoked (per File 22)
- the world-model state changed such that an `availability_predicate` no longer evaluates true

Every transition emits `CapabilityAvailabilityChanged` (per §13). The next composition sees the new status. If the run's model request currently exposes the capability in `Primary` and the next composition transitions it to `Unavailable`, the next turn's model request:

- removes the capability from `Primary`
- includes a typed notice describing the transition
- the inspector lens still shows the capability with the typed unavailability reason

### 17.2 Capability Becomes Available Mid-Run

The reverse transition (`Unavailable` to `Available`) also emits an event. The next composition restores the capability to its declared zone. The next turn's model request includes a typed notice ("Capability X is now available again"). The model may use it from that point.

### 17.3 In-Flight Calls

If a capability transitions to `Unavailable` while a call is in flight, the executor (per `run.cancellation`, File 04 §17.3 and `policy.mid-execution-policy-re-evaluation` (File 06 §10)) handles the in-flight call per the capability's declared cancellation and partial-output semantics (per `capability.execution-semantic-fields`, File 05 §3.6). The surface change does not affect already-in-flight execution; new invocations after the transition will fail at the call pipeline's resolve-capability step.

### 17.4 Source Loss

If an MCP server, plugin, or external-API source disconnects entirely, all capabilities from that source transition to `Unavailable` in one batch. The composition algorithm renders them all as `Unavailable`. The model receives a typed notice: "Source X disconnected; N capabilities unavailable". The user inspector shows the source as disconnected with reconnection actions.

### 17.5 Permanent Disablement Is Event-Driven

A capability transitions from `Unavailable` to `Disabled` only through explicit state events: plugin uninstall, MCP server configuration removal, external-API definition deletion, capability unregistration, user disable, policy disablement, or platform conditioning that makes the capability permanently inactive for the current installation. No clock or settled-period rule decides this transition. Long-stale unavailable sources may produce cleanup recommendations in later UI/maintenance specs, but those recommendations are not correctness conditions.

### 17.6 Boundary

Surface degradation is the projection layer's response to underlying state changes. The actual handling of failed invocations, retry logic, and recovery strategies is owned by `run.error-handling` (File 04 §20) (error handling and recovery) and the provider layer for provider-side failures.

## 18. Settings

Anchor: `surface.settings`

### 18.1 Configurable Dimensions

Every surface mechanism in this file is configurable through settings (per File 15). File 07 consumes a resolved settings snapshot. Profiles contribute active profile layers to that snapshot; they are not capability registries, security principals, or separate surface-state stores.

File 07 names the dimensions and the layer that owns each resolution. Cross-scope precedence, profile layers, imports, exports, locality, and agent exposure belong to File 15. File 07 owns how an already-resolved surface setting affects composition.

Dimensions:

- `surface.zone_override.<capability_id>` — explicit per-capability zone assignment (`primary` | `borrowable` | `deferred` | `disabled` | `default`) — composition consumes
- `surface.zone_family_override.<family>` — per-family zone preference
- `surface.zone_source_override.<source_id>` — per-source zone preference (e.g., demote all MCP server X's tools to `Borrowable`)
- `surface.always_load.<capability_id>` — pin a capability to `Primary` regardless of subsystem spec; auto-shrink does not demote
- `surface.never_load.<capability_id>` — capability always `Disabled` for the `ModelAgent` lens
- `surface.never_show_in_palette.<capability_id>` — capability hidden from `Palette` lens
- `surface.lens_visibility.<lens>.<capability_id>` — per-lens visibility override
- `surface.shortcut_binding.<capability_id>` — user-bound shortcut for the capability (overrides `default_shortcut`)
- `surface.budget_token_count` — the tool-surface token budget; default is a percentage of the model's context window
- `surface.borrowable_cap_count` — maximum `Borrowable` entries
- `surface.auto_shrink_enabled` — whether auto-shrink runs
- `surface.shrink_priority.<capability_id>` — per-capability shrink priority override
- `surface.auto_shrink_eligible.<capability_id>` — per-capability flag marking the capability eligible for demotion in auto-shrink Step D (per §8.2)
- `surface.default_deferred_visible_in_palette` — show `Deferred` entries in palette
- `surface.unavailable_visible_in_palette` — show `Unavailable` entries in palette
- `surface.forbidden_visible_in_palette` — whether capabilities in `forbidden_capability_ids` for the active surface still appear in palette with a disabled indicator (default true for inspectability)
- `surface.policy_blocked_visible` — show capabilities currently blocked by policy
- `surface.borrow_grant_default_scope` — default scope for `tool.borrow` (typically `run`)
- `surface.cross_surface_borrow_enabled` — whether the model can borrow capabilities outside the active `SubsystemSurfaceSpec` (default true; some safety-conscious workspaces may disable)
- `surface.discovery_capabilities_zone` — zone for `tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect` (default `Primary`)
- `surface.mcp_default_zone` — default zone for newly registered MCP-sourced capabilities (default `Borrowable`)
- `surface.plugin_default_zone` — default zone for newly registered plugin-sourced capabilities (default `Borrowable`)
- `surface.model_request_order_strategy` — `cache_friendly` (default; preserves request prefix where supported) | `alphabetical` | `frequency_based`
- `surface.lens_filter_strictness` — `strict` (default) | `permissive`
- `surface.trust_narrowing_active` — whether trust narrowing affects zone or only inspector flags
- `surface.composition_diagnostic_verbosity` — what diagnostics are recorded per composition (default minimal; verbose for debugging)
- `surface.mutation_event_emit_level` — which surface-relevant events emit (default all consequential events; the user can suppress noisy ones like every recomposition under heavy churn)
- `surface.snapshot_in_ledger` — whether every composed surface snapshot is recorded in the ledger (default major snapshots only — those consumed by a model turn or persisted by grant/policy state)

### 18.2 Settings-Key Convention

Surface-related settings use the namespaced dotted-key convention `surface.<dimension>.<scope_or_id>` (per `capability.settings-key-convention`, File 05 §18.2). Plugin and MCP-source-supplied capabilities register their own settings keys at registration time; the keys are namespaced under the source identity (e.g., `surface.zone_source_override.mcp.linear_server`).

### 18.3 Agent Exposure of Surface Settings

Per `policy.agent-exposure-policy-settings` (File 06 §16.4) and the canonical settings agent-exposure rules (per `core.settings-system`, File 01 §6.8):

- `surface.zone_override.*`, `surface.always_load.*`, `surface.never_load.*` — `OnRequest`; the agent can read these on request through the canonical read-only settings capability; the agent never writes them
- `surface.budget_token_count`, `surface.auto_shrink_enabled` — `OnRequest`; the agent may want to know what the budget is
- `surface.shortcut_binding.*` — `Hidden`; the agent never sees user shortcut bindings (they are user UI concerns)
- The active `SubsystemSurfaceSpec` and resolved zone assignments for the current run — `InModelRequest`; the model request already includes the surface, so the agent knows by inspection

### 18.4 Settings Changes Are Surface-Relevant Events

A settings change that affects surface composition emits `SurfaceSettingsChanged` (per §13). Affected compositions invalidate their cache and recompose on next read. For an active `Run`, the next model turn sees the new surface.

### 18.5 Boundary

File 07 names the settings dimensions. Settings storage, validation, resolution, profile layers, and agent exposure are owned by File 15. File 07 specifies which dimensions are surface-relevant and how they compose into a `ResolvedToolSurface`.

## 19. Explicit Rejections

Anchor: `surface.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel registry per invocation lens — there is one Capability Registry; surfaces are projections, never alternate registries
- a per-lens capability declaration — a capability has one `CapabilityDeclaration` per File 05; per-lens variation lives in display tags and composition-time filters, never in declarations
- silent autoload of cross-surface capabilities into a primary surface's `Primary` zone — capabilities outside the active `SubsystemSurfaceSpec` are reachable through `tool.search` and `tool.borrow` only, never through hidden auto-promotion
- zone membership as a stored field on the capability declaration — zone is computed; storing it would force registration churn on every zone-affecting change
- a separate "tool surface state" mutable record per active run — surface state is computed; the ledger records consumed surfaces, but no independent mutable per-run surface table exists
- treating tool-surface visibility as a security gate — visibility is presentation; authority is policy (per File 06); a visible capability may be denied at invocation, an invisible capability may be invoked through the palette
- routing-driven surface visibility changes that bypass policy — routing strategies (`borrow_foreign_capabilities`, `load_deferred_capabilities`) may promote capabilities but they may not lower the floor; trust narrowing and `permission_floor` still apply
- auto-shrink that requires user approval — auto-shrink is deterministic, in-band, and recorded; requiring approval per shrink would make the algorithm too disruptive to be useful
- auto-shrink that silently drops capabilities without diagnostic record — every shrink is recorded; the user can inspect what was shrunk and why
- a "tool surface" object that has independent durable state diverging from the registry — surface state is computed from registry + settings + `BorrowGrant`s + world state; durability lives in those sources, not in a separate surface store
- per-subsystem capability registries — capabilities are registered globally; subsystem surface defaults are a presentation layer over the global registry, not separate registries per subsystem
- silent visibility differences across lenses — every lens-filter exclusion is recorded in `composition_diagnostics`; users can inspect why a capability does not appear in the lens they expected
- ordering tool definitions in the model request by anything other than the cache-friendly canonical order without explicit user opt-in — cache hit rate is load-bearing for ATLAS3's cost; reordering by frequency or recency on every turn would waste cached tokens where provider caching is available
- treating MCP-sourced capabilities as a parallel system — they enter the same registry through the same contract per `capability.sourcing-equivalence` (File 05 §9.3); the surface composition does not branch on source kind in its core logic
- treating plugin tools, user-defined tools, or external-API tools as parallel systems — same as MCP; they all enter through the unified contract
- forcing the model to use a specific tool when the composition produces an empty primary surface — `tool_choice: required` against an empty surface fails with a typed error; routing handles the degradation, not the composition algorithm
- denying the model the ability to discover capabilities that exist in the registry — `tool.search` and `mcp.search` are first-class registered capabilities; their presence in `Primary` is the default; user customization can demote them but not remove them from the registry
- composition that depends on time — composition consumes registry snapshot id, settings snapshot id, `BorrowGrant` snapshot id, policy snapshot id, world snapshot id; same inputs always produce same output; no implicit clock-based effects
- baking per-provider tool-call format into the canonical surface — the canonical `ResolvedToolSurface` is provider-agnostic; per-provider rendering is the provider adapter's concern
- unrecorded provider-side tool renaming — provider adapters may produce provider-safe names, but every provider-visible name must map back to canonical capability identity through `provider_name_map`
- treating external tool descriptions, schemas, MCP prompts, plugin metadata, or user-defined capability text as instructions — they are untrusted data rendered inside explicit boundaries
- collapsing `Borrowable` and `Deferred` into one zone — the cost gradient (full schema vs. name+description vs. hidden) is the load-bearing distinction; collapsing them removes model-request budget control
- hardcoding any of the dimensions in §18 instead of exposing them as settings — every variation a user might want must be a settings dimension at the right scope
- a special-case surface lens for "trusted users" or "developer mode" — lens distinctions are typed and stable; trust is a policy concern that affects zone assignment, not a separate lens
- mid-run surface-relevant input changes or consumed compositions that do not emit events — every consequential change is observable; silent surface changes corrupt the audit trail and confuse the model
- using auto-shrink as a hidden quota gate — auto-shrink is a token-budget mechanism; it is not a policy mechanism; capabilities removed by shrink are still policy-authorized to invoke through borrow

## 20. Consequences for Later Specs

Anchor: `surface.consequences-for-later-specs`

Every later spec that touches capability presentation, capability loading, capability discovery, automation, runtime behavior, UI presentation, storage, sync, telemetry, or evaluation consumes the `ToolSurface` projection as defined here.

The canonical principles later specs must follow:

- consume `ToolSurface` as a projection of the Capability Registry; never invent a parallel registry, never invent a parallel surface state model, never write directly to per-lens storage; if a later spec wants surface-relevant changes, it emits the canonical events from §13
- consume the `SubsystemSurfaceSpec` contract — every per-surface or capability-owning substrate-service spec declares its `SubsystemSurfaceSpec` to the shape this file defines (`primary_capability_ids`, `borrowable_capability_ids`, `default_deferred_families`, `forbidden_capability_ids`, `spawnable_subagent_types`, `surface_settings_namespace`, `availability_predicate`); per-surface specs and substrate-service specs fill the contract for their subsystem
- consume the zone model — `Primary`, `Borrowable`, `Deferred`, `Disabled`, `Unavailable` — as the closed set; never introduce a sixth zone; per-subsystem specs may declare which capabilities go into which zone in their `SubsystemSurfaceSpec` but may not extend the zone vocabulary
- consume the late-loading capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) as the canonical mechanism for agent-initiated surface visibility changes; never introduce a parallel borrow API; if a later spec wants a specialized borrow flow, it declares a capability that wraps the canonical primitives
- consume the composition algorithm (§9) as the single deterministic surface composition path; never write a parallel composition; if a later spec needs surface-relevant inputs, it adds them as canonical inputs to the algorithm through the settings or routing contracts
- consume the surface-relevant event vocabulary (§13) as the canonical event set; never introduce parallel surface events; new event kinds register through the canonical event bus per `run.ledger-events-commits` (File 04 §23) with the standard envelope
- consume the lens-filter discipline — capabilities declare which invocation paths they support through tags (`agent-invokable`, `palette-invokable`, `voice-invokable`, `automation-trigger`, `external-exposed`) per `capability.display-fields` (File 05 §3.2); new invocation paths register new lens kinds through the canonical extension mechanism (per `core.extension-planes`, File 01 §6.14 extension planes)
- consume the surface-vs-policy boundary (§10) — File 07 surfaces never grant invocation authority; capability invocations always pass through File 06 policy; the surface composition records visibility decisions, the policy layer records authority decisions, both flow through the ledger
- consume the auto-shrink mechanic (§8) as a deterministic, non-destructive, always-recorded token-budget mechanism; later specs may extend the priority order through the canonical settings dimension but may not introduce hidden shrink mechanisms
- consume the persistence contract (§14) — `ToolSurface` is computed; durable state lives in the registry, settings, `BorrowGrant` records, and consumed surface snapshots; later specs do not introduce a parallel durable surface store
- consume the discovery-capabilities ledger discipline — every `tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect` is recorded; later specs that perform discovery-like operations declare new capabilities through the canonical mechanism rather than bypassing the ledger
- File 13 consumes the rendered `Primary` and `Borrowable` outputs of the composition algorithm as part of the model request; it does not invent its own surface; it places the surface in the canonical request position (§11.1) and applies cache markers as appropriate
- File 20 stores `BorrowGrant`s, settings, ledger entries, and consumed surface snapshots per the contracts here; it does not introduce parallel durability paths
- File 15 implements settings resolution, profile contexts, profile layers, locality, and agent exposure for the dimensions in §18; it does not redefine the dimensions
- File 35 (Extension and Plugin System) and File 36 (MCP and External Integrations) hand their registered capabilities through the unified Capability Registry per `capability.sourcing` (File 05 §9); the surface composition picks them up automatically
- File 24 defines workspace boundaries; the surface composition consumes workspace_id from `scope_context` as one of the resolution inputs; workspace switching emits the appropriate `SurfaceSettingsChanged` event
- the per-surface specs (Coder File 27, Web File 28, Data Processor File 29, Teacher File 30, GUI Control File 31, System Agent File 32) and the capability-owning substrate-service specs declare their `SubsystemSurfaceSpec` and any specialized discovery capabilities or specialized auto-shrink priorities specific to their subsystem
- File 33 (Automation and Triggers) consumes the `AutomationTrigger` lens through the canonical contract; it pins surface strategies at save time through the same `tool_surface_strategy` field as runtime routing
- File 34 (Workflows, Templates, and Reuse) composes capabilities through the unified registry; workflow nodes reference capability ids; the surface composition for a workflow execution honors the workflow's declared capability list as an additional input
- File 37 (UI Shell, Layout, Presentation, and Interaction Models) renders the `Palette`, `Inspector`, `Voice`, `Shortcut`, `AutomationTrigger` lens data into UI; File 07 hands them the canonical data contract
- File 38 renders the surface inspector and the per-capability settings views; the data contract is what File 07 specifies
- the Quality Control and Validation spec (File 39) may consume the surface for static analysis (capability availability checks, lens consistency checks, shortcut conflict detection); it does so through the canonical inspector lens
- the Evaluation and Benchmarking spec (File 40) consumes the surface snapshot recorded in the ledger to evaluate tool-use efficiency; replay reconstructs the exact surface a past invocation saw
- the Telemetry, Logging, and Observability spec (File 41) captures surface-relevant events for monitoring; it consumes the canonical event vocabulary
- the Runtime Infrastructure and Lifecycle spec (File 42) implements the composition algorithm with deterministic semantics; File 07 specifies the contract, the runtime realizes it
- the Packaging, Platform, and Distribution spec (File 43) packages built-in `Capability` declarations including the canonical discovery capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`); they ship in every ATLAS3 install as the `Builtin` source

Specific integration contracts will be stated in those files. Until then, the canonical contract here is the load-bearing reference.

## 21. Canonical Rule Anchors

Anchor: `surface.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `surface.chosen-model`, `surface.tool-surface`, `surface.required-outputs`, `surface.zone-model`, `surface.loading-semantics`, `surface.subsystem-surface-spec`, `surface.primary-surface-changes`, `surface.routing-influence`, `surface.late-loading-runtime-discovery`, `surface.borrow-grant`, `surface.default-composition-auto-shrink`, `surface.auto-shrink-algorithm`, `surface.auto-shrink-non-destructive`, `surface.visibility-composition-resolution-algorithm`, `surface.tool-surface-capability-policy`, `surface.presentation-in-model-request`, `surface.cache-friendly-ordering`, `surface.presentation-in-user-facing-surfaces`, `surface.inspector-lens`, `surface.surface-relevant-events`, `surface.persistence-reconstruction`, `surface.reconstruction-across-restart`, `surface.reconstruction-across-retry-edit-reroute-branch`, `surface.mcp-plugin-tool-integration`, `surface.tool-choice-mechanics`, `surface.degradation-graceful-absence`, and `surface.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
