> Lossless render of canonical/07-tool-surfaces-and-capability-loading.md — original 120731 chars

# Tool Surfaces and Capability Loading

## Status
Canonical.

## Scope
Defines: `ToolSurface` (typed projection of the Capability Registry a `Run`/control rail/any invoker sees at a moment); the canonical zone model (`Primary`, `Borrowable`, `Deferred`, `Disabled`, `Unavailable`) + each zone's meaning in model-request/palette presentation+policy interaction; loading semantics per zone; the per-subsystem default surface contract (`SubsystemSurfaceSpec`); the runtime composition algorithm producing the effective surface from registered state, routing inputs, settings, active borrow grants, world-model state, context budget; the late-loading capabilities (`tool.borrow`, `tool.search`, `mcp.search`, `tool.inspect`) as first-class registered capabilities + scoping; auto-shrink behavior under context pressure (priority order, deterministic mechanics, user visibility+override); the unified invocation-path contract (model request, command palette, keyboard shortcut, voice, automation trigger, external protocol — all from one `CapabilityDeclaration`); the surface-relevant event vocabulary into ledger+event stream; persistence+reconstruction across process restart/retry/edit/reroute/branch/child-run spawn; the boundary with the policy layer (loading is presentation, policy gates execution); degradation+graceful-absence semantics; inspection/filtering/customization at every scope (global, profile, workspace, conversation, run); settings dimensions consumed by composition (exact cross-scope precedence owned by the settings layer).
Does not define: the `CapabilityDeclaration` field set/registry operations/identity/versioning/backend binding lifecycle [File 05]; effective permission tier resolution/lease evaluation/approval flows/templates/contradiction-checking [File 06]; routing-frame composition/route record/how `tool_surface_strategy` is chosen [File 03]; run lifecycle/call-pipeline/hook execution/cancellation/streaming/postcondition validation [File 04]; block schema/artifact lifecycle/evidence model/version graph [later specs]; the per-surface specs themselves (Coder, Web, Teacher, Data Processor, GUI Control, System Agent) which declare their `SubsystemSurfaceSpec`; storage schema for surface state/`BorrowGrant`s/policy leases/settings [future Storage spec]; UI rendering choices [future UI Shell+UI Customization specs]; MCP transport mechanics/plugin install lifecycle internals/provider rate limits/sandbox primitives [future MCP+Plugin+Sandbox specs; File 17 owns provider concerns].

## Source Resolution
Resolves tool loading, tool search, borrowing, MCP discovery, subsystem surfaces, model-request exposure into one boundary: the runtime capability surface visible to a model or user. Resolved design: a tool surface is a projection of the Capability Registry, not a second registry; loaded/visible/callable/permitted are separate states (permission owned by File 06); Primary/borrowable/deferred zones control request size+discoverability without hiding the registry; search/borrow/inspect/revoke/surface-change are first-class capability interactions with events+snapshots; external tool descriptions are untrusted data rendered behind architectural instruction boundaries, not sanitized into trusted instructions; subsystem defaults+user settings shape surfaces, but every loaded tool still follows the same capability+policy contracts.

## 1. Chosen Model `surface.chosen-model`
One Capability Registry [File 05]. The set a particular invoker sees at a given moment is a `ToolSurface`. Invokers: a `Run`'s executing model, a programmatic execution unit, the command palette, a voice command resolver, a keyboard-shortcut dispatcher, an automation trigger, or an external client speaking the MCP server protocol.
A `ToolSurface` is: a typed projection over the registry, zone assignment computed per `(invoker, scope, context)`; composed from registered state [`capability.registered-capability`, File 05 §10], resolved settings snapshot [File 15], active `BorrowGrant`s, active routing decision [`routing.tool-surface-strategy`, File 03 §8.3], active world-model snapshot [`core.world-model`, File 01 §6.7], active context budget [`run.routing-influence`, File 04 §10.3 + File 13]; a presentation surface, not a security gate (invocation authority owned by File 06; a visible capability still subject to effective tier resolution at proposal time); inspectable/settable/observable through the settings model (durable global/workspace/conversation scopes, active profile context, non-durable run or per-call overlays).
The same registered `Capability` appears in multiple `ToolSurface` projections concurrently (model-request surface, palette surface, voice-invokable surface, shortcut surface, automation-trigger surface, externally exposed surface). Each is the same registry projected through a different invocation lens; each composition step honors the same canonical algorithm.
`ToolSurface` is the canonical noun. Earlier material: "tool list", "tool catalog", "available tools", "action palette", "skill catalog", "action registry view", "function library", "tool inventory" — none survive as parallel primitives. "tool" remains an informal synonym for `Capability` per [`capability.chosen-model`, File 05 §1]; references like "tool-surface strategy" and "tool.borrow" preserve established canonical vocabulary. Supersedes any earlier shape treating the agent's available capability list as a separate object from user-facing palettes/voice grammars/shortcut maps/automation editors — the shape is one; the projection lens differs.

## 2. `ToolSurface` `surface.tool-surface`
### 2.1 Definition
Typed projection of the registry a specific invoker sees at a moment; computed, not stored as an independent mutable record. Every render runs the canonical composition algorithm (§9) over the same inputs, producing a `ResolvedToolSurface`.
Not: a registry (capabilities live in the registry; surfaces project it); a permission grant (visibility ≠ authority; File 06 evaluates every proposed call); a separate mutable list per invoker (no per-invoker surface table drifting from registry state; surface state is derived); a stored UI configuration (rendered from the resolved surface + presentation choices owned by later UI specs); a per-capability flag (declarations carry no "current zone" field; zone assignment is computed runtime state).
### 2.2 Invokers and Surface Kinds
Always typed with `invoker_kind` + `invocation_lens`. Canonical invoker kinds:
- `ModelAgent` — an executing model inside a `Run`; renders into the model request as callable declarations + model-request text content
- `ProgrammaticUnit` — a deterministic execution unit [`run.programmatic-execution`, File 04 §14] resolving capabilities by id; enumerates invokable ids
- `Palette` — command palette + equivalent quick-action surfaces (slash commands, palette overlays); renders as a searchable user-facing list
- `Voice` — voice command resolver; renders as a vocabulary-matchable set of voice-invokable capabilities with aliases
- `Shortcut` — keyboard-shortcut dispatcher; renders as a map from chord to capability id
- `AutomationTrigger` — automation rule editor + runtime trigger resolver; renders as capabilities a trigger may invoke
- `ExternalMcp` — external MCP client speaking to ATLAS3 as a server; renders as the externally exposed catalog
- `Inspector` — user-facing settings/plugin manager/source manager/registry inspector; renders the full catalogue incl. disabled+unavailable entries
Composition algorithm (§9) takes `invoker_kind` as input; per-kind filtering uses display tags + explicit invocation-path declarations [`capability.display-fields`, File 05 §3.2; §11].
### 2.3 Required Outputs `surface.required-outputs`
`ResolvedToolSurface` carries at minimum:
- `surface_id` — stable identity for the duration of validity (one model turn, one palette open, one voice session, etc.)
- `invoker_kind`, `invocation_lens` — what computed the surface
- `scope_context` — snapshot of (`run_id`, `intent_thread_id`, `task_id`, `conversation_id`, `workspace_id`, `surface_zone`, `profile_id`, world-model snapshot id, settings snapshot id, borrow-grant set id) that fed composition
- `zoned_entries` — typed per-capability records grouped by zone (§3): `primary`, `borrowable`, `deferred`, `disabled`, `unavailable`
- `routing_inputs` — `RunIntent.tool_surface_strategy` consulted [File 03], active routing decision facts (§6), any pre-existing `BorrowGrant`s honored
- `provider_name_map` — when rendered for a provider, a bijective map from every provider-visible tool name to `(capability_id, capability_version, declaration_version)`; invocation records store both canonical id and provider-visible name used
- `context_budget` — model context budget [File 13] at composition time + post-shrink budget actually consumed by tool definitions (§8)
- `auto_shrink_record` — typed record of any auto-shrink: which capabilities moved between zones, the budget threshold that triggered shrink, the priority ordering applied, and a `cache_impact` classification (`none`, `preserved_prefix`, `changed_tool_surface_only`, `changed_instruction_or_region_order`, `full_cache_break_likely`) describing how shrink affected the cacheable prefix (§8.3)
- `composition_diagnostics` — typed diagnostic naming, per capability ever considered, why it landed in its zone (declared default, routing decision, settings override, active `BorrowGrant`, context-pressure shrink, availability state, trust narrowing); inspectable through the inspector surface
Every `ResolvedToolSurface` recorded as a surface snapshot in the execution ledger [`run.execution-ledger`, File 04 §23.1] when consumed by an invoker, so replay+audit reconstruct exactly which capabilities each invoker saw.
### 2.4 Boundary
Projection layer over the registry; owns no declarations. Same canonical algorithm for every invoker kind; per-kind variation in the invocation-lens filter step (§11) + presentation rendering owned by later UI specs. Future Storage spec owns durability of recorded snapshots+customization settings; future UI Shell+Customization specs own rendering. File 07 specifies the data contract; storage+UI consume it.

## 3. The Zone Model `surface.zone-model`
### 3.1 Canonical Zones (5, closed)
- `Primary` — full schema exposed as a provider-native callable declaration; full name+metadata in user-facing surfaces; directly invokable by the model with no preparatory step
- `Borrowable` — name+`short_description` in model-request text content; full metadata in user-facing surfaces; the model can call `tool.borrow` to load the full schema for the current scope, after which it behaves as `Primary` for that scope
- `Deferred` — not present in the model request at all; visible in user-facing surfaces only when the user explicitly reveals deferred entries (§12.4); model locates via `tool.search`/`mcp.search` then calls `tool.borrow`
- `Disabled` — not present in any invoker surface; appears only in the `Inspector` lens with a `Disabled` badge + recorded `disable_reason`; remains in the registry [`capability.registered-capability`, File 05 §10.3]; re-enableable through settings
- `Unavailable` — registered but currently not invocable because of `availability_status` [`capability.registered-capability`, File 05 §10] (e.g. `unavailable_platform`, `unavailable_handler`, `unavailable_prerequisite`); appears in `Inspector` with typed unavailability reason; never present in `ModelAgent`/`ProgrammaticUnit` surfaces (invocation would fail); may appear in `Palette`/`Inspector` with a disabled-style indicator+inspectable explanation per user-customization preference
Zone set is closed. `Disabled` and `Unavailable` are resolved presentation states, not declaration fields, not policy authority. Adding a sixth zone is an Explicit Rejection (§19).
### 3.2 Zone Semantics for `ModelAgent`
- `Primary` → provider-native callable declarations (canonical `name`, `description`, `input_schema`, declared `error_vocabulary` summary, any execution-semantic hints required by the active provider tool-call format [`capability.declaration`, File 05 §3; `run.hook-integration`, File 04 §23.3])
- `Borrowable` → model-request text content: `name`, `family`, `short_description`, one-line note that the full schema is available via `tool.borrow(id)`; model decides whether the borrow round-trip is worth its cost
- `Deferred` → not in the model request; discovered via `tool.search` or hints injected by hooks/task context
- `Disabled`, `Unavailable` → not visible to the model (cannot be invoked)
The Primary catalog is the model's immediate action surface; Borrowable is its discoverable reach; Deferred is its searchable depth — together covering full reach without overloading the model request.
### 3.3 Zone Semantics for `Palette`, `Voice`, `Shortcut`, `AutomationTrigger`
- `Primary` + `Borrowable` both shown by default in the canonical user view (palette list, voice grammar, shortcut map, automation trigger picker)
- `Deferred` hidden by default but reachable through inspector+user search; advanced settings expose inline (§12.4)
- `Disabled` appears in inspector with a disabled-style indicator; user can re-enable
- `Unavailable` appears in inspector with the typed reason; user-customization decides palette/voice/shortcut visibility (disabled indicator vs hidden until recovery)
Primary/Borrowable split is semantically meaningful for `ModelAgent` (determines model-request cost); for user-facing invokers it is visual grouping, not an action gate — the user does not need to "borrow" to invoke from the palette. User invocation through palette/voice/shortcut is direct; the resolver invokes through the same [`run.call-pipeline`, File 04 §8.2], and File 06 policy applies the same way.
### 3.4 Zone Semantics for `ExternalMcp`
When ATLAS3 exposes capabilities to an external MCP client [`capability.chosen-model`, File 05 §1; `core.extension-planes`, File 01 §6.14]:
- `Primary` + `Borrowable` — visible in the external surface only if tagged for external exposure [`capability.display-fields`, File 05 §3.2] AND active source-approval policy permits external exposure [`policy.source-approval-flow`, File 06 §9]; a capability not tagged for external exposure is filtered to `Disabled` for the `ExternalMcp` lens regardless of its zone elsewhere
- `Deferred`, `Disabled`, `Unavailable` — hidden; external clients see only the externally exposed Primary + Borrowable set
`tool.borrow` and `tool.search` are first-class capabilities (§7); whether externally exposed is a user setting per source-approval+source policy.
### 3.5 Zone Membership is Computed
A declaration carries no zone field. Zone computed by the algorithm (§9) from:
- declared display tags [`capability.display-fields`, File 05 §3.2] (e.g. `agent-invokable`, `palette-invokable`, `voice-invokable`, `automation-trigger`, `external-exposed`)
- declared family+source [`capability.display-fields`, File 05 §3.2; `capability.capability-source`, File 05 §9.1]
- declared availability predicate [`capability.availability-fields`, File 05 §3.9; `capability.availability-predicate`, File 05 §15.2] evaluated against the active world-model snapshot
- the active `SubsystemSurfaceSpec` for the run's current primary surface (§5)
- the active `RunIntent.tool_surface_strategy` [`routing.tool-surface-strategy`, File 03 §8.3; `routing.routing-summaries`, File 03 §6]
- resolved settings snapshot for per-capability/per-family/per-source zone overrides + lens visibility (§12, §18)
- active `BorrowGrant`s for schema-visibility promotion + policy-resolved facts relevant to presentation (§7.3, File 06)
- the registered entry's `enabled` flag + `availability_status` [`capability.registered-capability`, File 05 §10]
- the active context budget reported by context assembly [`run.routing-influence`, File 04 §10.3; File 13] for auto-shrink (§8)
- the registered entry's trust state [`capability.trust-source-approval-flow`, File 05 §9.2; `policy.effective-tier-resolution`, File 06 §4] for trust-driven narrowing
Composition deterministic given same inputs (§9.4): two invokers with the same `scope_context` consuming the same registry state produce the same zoned entries.
### 3.6 Zones Are Not Authority
Zone controls visibility, model-request cost, discovery; does not grant/deny invocation authority. A `Primary` capability may still be denied at proposal time by File 06 (effective tier reaches Deny, policy lease contradiction, `permission_floor` violated). A `Borrowable` capability undergoes the same evaluation when invoked. `tool.borrow` is itself subject to policy — borrowing requires `ReadOnly` tier (§7.2); the borrowed capability's own tier still applies when invoked. Visibility-vs-authority is load-bearing: surface answers "what can the invoker see?"; policy answers "may this proposed call proceed?".

## 4. Loading Semantics `surface.loading-semantics`
### 4.1 What "Loaded" Means
For `ModelAgent`: "loaded" = zone `Primary` (full schema/name/description exposed as provider-native callable declarations); "borrowable" = zone `Borrowable` (name+short description in model-request text, callable schema not present); "deferred" = zone `Deferred` (not in the model request at all). For user-facing lenses (`Palette`, `Voice`, `Shortcut`, `AutomationTrigger`): "loaded" = "shown in the user's view"; data shown is the full display metadata (name, short_description, family, tags, icon_key, default_shortcut from [`capability.display-fields`, File 05 §3.2]) + the resolved permission tier indicator from [`policy.effective-tier-resolution`, File 06 §4]. User-facing data always available for any `Primary`/`Borrowable` entry; whether the user sees `Deferred` is a customization setting.
### 4.2 Model-Request Rendering for `Primary`
`Primary` entries render as provider-native callable declarations in whatever native format the active model's provider expects [`routing.capability-awareness`, File 03 §7.4; `run.tool-calls`, File 04 §9], normalized from the canonical declaration. Rendered fields:
- `name` — canonical `id` or a provider-safe visible name mapped back through `ResolvedToolSurface.provider_name_map`
- `description` — localized `description` [`capability.display-fields`, File 05 §3.2]
- `input_schema` — declared `input_schema` [`capability.input-schema`, File 05 §4.1] converted to the provider's native schema dialect
- `error_vocabulary` summary — compact representation of recoverable+non-recoverable typed errors so the model can plan recovery [`capability.error-vocabulary`, File 05 §4.3; `run.denial-is-in-band`, File 04 §8.3]
- inline display hints — optional short notes derived from `tags` (e.g. `destructive`/`experimental` carries an inline note)
Per i18n discipline, the model sees localized text resolved against the active locale; literal defaults present so the surface works before localization is wired.
### 4.3 Model-Request Rendering for `Borrowable`
Rendered as model-request text content after `Primary` declarations and before conversation history; structured so the model recognizes it as borrow-eligible:
- `family` grouping [`capability.family`, File 05 §13.2] so the model scans by family
- per-entry one-liner — `name` + `short_description`
- `borrow_invocation_hint` — single line indicating `tool.borrow(name)` loads the schema for the rest of the turn
Deterministically ordered (alphabetical by family, then by name within family) for cache friendliness where the provider supports caching [`run.from-run-intent-to-run`, File 04 §3.3; File 13]. If a `BorrowGrant` (§7.3) is active, the borrowed capability renders in `Primary` for the grant duration and is removed from the `Borrowable` catalog block to avoid duplication.
### 4.4 The Borrow Operation
`tool.borrow(capability_id)` is a first-class registered capability (§7.2). When the model invokes it, the executor [`run.call-pipeline`, File 04 §8.2] runs the full pipeline:
1. Capability resolved+validated as any other call
2. Policy evaluates `tool.borrow` itself (declared at `ReadOnly`, §7.2) — borrowing metadata costs nothing in tier terms
3. The capability being borrowed is resolved against the registry to confirm exists+enabled+available; if not, returns a typed error in-band [`run.denial-is-in-band`, File 04 §8.3]
4. If found and in scope to be borrowable, executor records a `BorrowGrant` (§7.3) and returns the full schema as the tool result
5. Next composition for this run sees the active `BorrowGrant` and renders the borrowed capability in `Primary`
6. A surface-relevant event emitted (`CapabilityBorrowed`, §13)
If the capability is in `Disabled`/`Unavailable`/outside the borrow-eligible set (e.g. source not tagged borrow-eligible per workspace settings), `tool.borrow` returns a typed denial result; the model receives it in-band and may try `tool.search`.
### 4.5 Loading Across Turns
Within a single `Run` turn, borrowed capabilities render as `Primary` from the moment the `BorrowGrant` is issued; across turns within the same run, they remain in `Primary` for the grant scope (§7.3). Default grant scope for `tool.borrow` is `run`; when a `Run` ends, run-scoped grants expire, and the next composition for any successor run starts unborrowed. The user/agent can request a wider scope through `tool.borrow_persistent(capability_id, scope)` (§7.2) at higher policy tier (`UserApproval` because it persists capability visibility across runs).
### 4.6 Late Schema Loading for MCP-Sourced Capabilities
MCP-sourced capabilities [`capability.capability-source`, File 05 §9.1] may carry larger schemas; for large external registries, the registered entry carries a compact metadata cache, the full schema fetched on-demand: compact metadata (name, family, short_description, tags, declared tier) fetched at MCP connect+cached; full schema fetched on first `tool.borrow` or first invocation through the standard pipeline; cached for the duration of the MCP server connection; MCP server disconnect invalidates the cache and transitions to `availability_status: unavailable_handler` [`capability.registered-capability`, File 05 §10]. Lets ATLAS3 advertise large external surfaces (hundreds of tools) without bloating the registry's hot path. Default loading policy: MCP-sourced capabilities enter `Borrowable` for the `ModelAgent` lens of any run not explicitly routing through the MCP-providing surface; enter `Primary` only if the active `SubsystemSurfaceSpec`/settings places them there.
### 4.7 Boundary
Loading semantics define what fills the model request + what the user sees in the palette. Do not define how the model parses tool calls ([`run.tool-calls`, File 04 §9]), how policy resolves the call (File 06), or how the executor invokes the capability ([`run.call-pipeline`, File 04 §8.2]). Loading is the front-of-pipeline projection; everything downstream is unchanged.

## 5. Subsystem Surface Defaults: `SubsystemSurfaceSpec` `surface.subsystem-surface-spec`
### 5.1 Required Shape
Every work surface + every capability-owning substrate service declares a `SubsystemSurfaceSpec` resolved at startup [`capability.startup-registration`, File 05 §16.1]; the canonical contract for the default tool surface a subsystem contributes when it is the run's primary or supporting surface. Carries:
- `subsystem_id` — from [`capability.capability-source`, File 05 §9.1]; matches the `primary_surface` value from [`routing.run-intent`, File 03 §4.3] when this subsystem owns that surface
- `display_name` — localized [`capability.display-fields`, File 05 §3.2]
- `primary_capability_ids` — ordered list of capability ids [`capability.id`, File 05 §13.1] in `Primary` zone for a run whose primary surface is this subsystem
- `borrowable_capability_ids` — ordered list in `Borrowable` zone (capabilities the subsystem expects the model to occasionally need but does not want consuming budget by default)
- `default_deferred_families` — optional list of families that should be `Deferred` rather than `Borrowable`; capabilities in these families reachable only through search
- `forbidden_capability_ids` — optional list excluded from any zone for this subsystem even if other rules would include them; the executor still allows attempts through `tool.search`/`tool.borrow`, but borrow returns a typed denial
- `spawnable_subagent_types` — optional list of subagent types this subsystem can spawn [`run.child-runs-multi-agent-work`, File 04 §16]; each names the `SubsystemSurfaceSpec` it will run under as a child run
- `surface_settings_namespace` — the settings namespace [`capability.settings-key-convention`, File 05 §18.2] under which per-subsystem customization is keyed
- `availability_predicate` — optional subsystem-level predicate; if it fails, the entire spec is unavailable (e.g. Web surface requiring a registered browser backend, GUI Control surface requiring accessibility API access)
Declarative; a typed object provided through the same proposal-first capability-registration pipeline [`capability.runtime-mutation`, File 05 §16.2]; updateable through that pipeline; updates emit `SubsystemSurfaceSpecUpdated` events (§13).
### 5.2 Capabilities Outside the Spec
A capability not in `primary_capability_ids`/`borrowable_capability_ids`/`forbidden_capability_ids` is `Deferred` for the `ModelAgent` lens (not in the model request but reachable through `tool.search`/`tool.borrow`). The agent's full reach is still the registry; the surface keeps the model request focused. For `Palette`/`Voice`/`Shortcut`/`AutomationTrigger`, capabilities not in the spec are still surfaced if tagged appropriately (§11) and the user has not disabled them. The palette is broader than the agent's model-request surface by default — [`core.extension-planes`, File 01 §6.14]'s single-capability-multiple-invocation-paths invariant means the user can always invoke through the palette even if the model request omits it. The palette resolver invokes through the same [`run.call-pipeline`, File 04 §8.2], so File 06 policy still applies.
### 5.3 Routing-Time Strategy Selection
The router [`routing.dispatch-pipeline`, File 03 §3] produces a `RunIntent` whose `tool_surface_strategy` is one of:
- `use_current_surface_tools` — use the active spec's declared zones unchanged
- `borrow_foreign_capabilities` — start from the active spec but pre-load capabilities from another subsystem's `primary_capability_ids` into `Borrowable` before the model runs, so the model sees them as borrow-eligible without searching
- `load_deferred_capabilities` — start from the active spec but promote specified deferred capabilities (typically named in `routing_metadata`) into `Primary` before the model runs
`borrow_foreign_capabilities` and `load_deferred_capabilities` carry the specific foreign-subsystem/capability-id list in `routing_metadata` [`routing.run-intent`, File 03 §4.3]. The algorithm (§9) consumes this strategy as an input.
### 5.4 Primary Surface Changes `surface.primary-surface-changes`
When a `Run`'s primary surface changes mid-execution (e.g. mid-execution reroute [`routing.mid-execution-reroute`, File 03 §12]), the active spec changes; the algorithm re-runs for subsequent model-request assembly; the next turn sees the new primary surface. Capabilities borrowed before the transition retain their `BorrowGrant`s per scope; a `run`-scoped grant survives a primary-surface change within the same run. Emits `PrimarySurfaceChanged` (§13); the model's next request includes a typed notice (rendered as part of request assembly per File 13) describing the change.
### 5.5 Cross-Surface Reach Without Primary-Surface Change
Cross-surface access through `tool.borrow` does not require a primary-surface change. A run in Coder that borrows `web.fetch` remains in Coder; the borrowed capability becomes visible for the grant scope without changing `primary_surface`. The ledger records both originating surface + borrowed-capability source so audit reconstructs cross-surface reach.
### 5.6 Boundary
`SubsystemSurfaceSpec` is a contract this file defines; the actual specs for Coder/Web/Teacher/Data Processor/GUI Control/System Agent/Memory + user-registered subsystems are declared in those subsystems' own canonical specs once written.

## 6. Routing Influence `surface.routing-influence`
### 6.1 Consumed Inputs
The algorithm (§9) consumes:
- `RunIntent.primary_surface` — selects the active `SubsystemSurfaceSpec` (§5)
- `RunIntent.supporting_surfaces` — additional relevant surfaces; their `primary_capability_ids` promoted into the active surface's `Borrowable` zone by default
- `RunIntent.capability_families` — illustrative routing hints; composition prefers those families if zone slots are constrained by budget
- `RunIntent.tool_surface_strategy` — `use_current_surface_tools` | `borrow_foreign_capabilities` | `load_deferred_capabilities` [`routing.tool-surface-strategy`, File 03 §8.3]; consumed per §5.3
- `RunIntent.model_route.resolved_model_id` — resolved model identity; determines native tool-call format [`run.tool-calls`, File 04 §9] + the model's context window [File 17] for budget-aware shrinking
- `RunIntent.execution_entry` — `respond_inline` | `respond_with_tools` | `surface_runtime` | `multi_step_agent` [`run.execution-entry`, File 04 §4]; affects whether tool surface is rendered at all (a `respond_inline` entry needing no tools renders an empty surface)
- `routing_metadata` — observability fields [`routing.run-intent`, File 03 §4.3]; used for diagnostic display in the inspector lens
### 6.2 Routing-Time Pinning
Automations+user-invoked actions may pin `tool_surface_strategy`+specific capability lists at save time [`routing.trigger-kinds-routing`, File 03 §2.1]. The algorithm honors the pinned strategy like a runtime decision; difference is provenance only, recorded in `routing_metadata`.
### 6.3 Routing Inputs Are Inspectable
Per [`routing.minimum-visible-information`, File 03 §10.2], routing-frame inputs are surfaced through the routing inspector. `ResolvedToolSurface.composition_diagnostics` (§2.3) extends this: the user can inspect any composed surface and see which routing inputs influenced which zone assignments, alongside settings/`BorrowGrant`s/policy-visible facts/world-model state.
### 6.4 Routing Does Not Override Floors
Routing strategies cannot override safety floors. A capability whose `permission_floor` [`capability.permission-floor`, File 05 §5.4; `policy.permission-floor`, File 06 §7.1] makes it `Denied` cannot be promoted into a zone by any strategy; the algorithm clamps the resulting zone to `Disabled` for the `ModelAgent` lens (still visible in inspector to make the floor inspectable). Source-trust narrowing from [`policy.effective-tier-resolution`, File 06 §4.2] step 3 applies: a `Community`-trust capability routing wants in `Primary` is `Primary` only if source-approval permits; otherwise the algorithm demotes to `Borrowable` with an inspector note.
### 6.5 Boundary
Routing produces the `RunIntent`; the algorithm consumes its surface-relevant fields. Routing does not implement composition; the router does not directly mutate surface state.

## 7. Late-Loading and Runtime Discovery `surface.late-loading-runtime-discovery`
### 7.1 Built-in Discovery Capabilities (5)
Mediated by five canonical built-in capabilities registered [`capability.capability-source`, File 05 §9.1] (`Builtin` source), resolved through the same call pipeline [`run.call-pipeline`, File 04 §8.2]:
- `tool.borrow` — load the full schema of a specific named capability into the active run's surface + grant a `BorrowGrant` (§7.3)
- `tool.borrow_persistent` — variant granting a `BorrowGrant` at a wider scope (`intent_thread`, `task`, `conversation`, `workspace`, or another allowed scope); requires `UserApproval` tier
- `tool.search` — discover capabilities by name/family/description/tag from the registry; returns a ranked list of matches with zone assignment for the current surface
- `mcp.search` — discover capabilities specifically from connected MCP servers; returns a ranked list filtered to MCP-sourced entries
- `tool.inspect` — return metadata about a specific named capability without making it provider-callable
These five are first-class registered capabilities; appear in every default `SubsystemSurfaceSpec`'s `primary_capability_ids` by convention so every run can discover+borrow without preparatory steps; subsystems may move them to `Borrowable` to conserve tokens.
### 7.2 Declarations
`tool.borrow`: `permission_tier`: `ReadOnly` (loading metadata is read-only, never grants invocation authority of the borrowed capability; the borrowed capability's own tier applies on invocation); `concurrency`: `ConcurrencySafe` (multiple parallel borrows safe); `replay_class`: `deterministic_replayable`; `touched_resources`: meta-resource declaration over the registry (registry-state-read, no external effects); `idempotent`: true (borrowing twice is no-op); `preview_mode`: `none`; result: full capability schema + the granted `BorrowGrant` record.
`tool.borrow_persistent(capability_id, scope)`: same as `tool.borrow` except `permission_tier`: `UserApproval`; argument-aware: borrowing for `global` scope may trigger typed-confirmation if the borrowed capability's class is `ActionExternal` [`policy.risk-classification-trust-interaction`, File 06 §15].
`tool.search(query, family, source, top_k)`: `permission_tier`: `ReadOnly`; `concurrency`: `ConcurrencySafe`; `replay_class`: `deterministic_replayable` (caveat: registry is mutable, so results depend on registry state at search time; replay records the registry snapshot id); result: ranked list of capability metadata (name, family, short_description, source, current zone, declared tier).
`mcp.search(query, server_id, top_k)`: same as `tool.search` but filtered to MCP-sourced capabilities; optional server_id narrows to a specific connected server; result: same shape + MCP-server identity per match.
`tool.inspect(capability_id)`: `permission_tier`: `ReadOnly`; `concurrency`: `ConcurrencySafe`; `replay_class`: `deterministic_replayable`; result: declared metadata at the requested detail level without changing zone membership or making the capability callable in provider-native format. Returns compact metadata by default (name, display metadata, source, family, current zone, declared tier, short input/output summary, borrow eligibility); full detail incl. full schemas only when requested+allowed by settings/policy/context budget. Inspecting never changes zone membership, never makes the capability callable.
Part of the canonical built-in set; not optional; ship registered in `Builtin` source. Plugins/extensions may register adapter capabilities [`capability.adapter-capabilities`, File 05 §17.4] wrapping them for specialized presentation, but the canonical ids are stable.
### 7.3 `BorrowGrant` `surface.borrow-grant`
A `tool.borrow` call grants a File 07-owned `BorrowGrant`, not a File 06 approval `Lease`. A scoped surface-visibility record: makes a capability's schema visible in `Primary`; never authorizes execution. The borrowed capability's own policy tier still resolves at invocation time [`policy.effective-tier-resolution`, File 06 §4]. Carries:
- `capability_match`: exact `(id, version)` of the borrowed capability
- `scope`: `run` by default; `tool.borrow_persistent` lets the user widen
- `invoker_kind`: `model_agent` if emitted by the model; `user_direct` if invoked through the palette
- `schema_visible`: true
- `grant_origin`: `tool_borrow_call`
- `revocation_conditions`: standard scope expiry, explicit user revoke, capability unregistration, source unavailability, declaration-version incompatibility, or settings change disabling borrowing for the target
Uses the same scope vocabulary as File 06 leases where applicable (`run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule`), but is not selected by policy evaluation and is not a policy decision; stored+audited with surface state (a future storage spec may co-locate it physically with policy leases, but the semantics stay separate). If the approval `Lease` for a `tool.borrow_persistent` call is later revoked, existing `BorrowGrant`s survive under their own conditions; revoking that lease means future persistent borrow calls require re-approval but does not retroactively remove already-granted `BorrowGrant`s. Algorithms see active grants and place the borrowed capability in `Primary`; grant revocation transitions it back to its base zone in the next composition.
### 7.4 Search Results
`tool.search` and `mcp.search` return ranked lists. Registry-side ranking combines: exact name match (highest weight); family match; tag overlap with the query; description/short_description fuzzy match; recency of successful invocations (per the ledger, optional+settings-controlled); declared `cost_model` weight (cheap capabilities preferred for searches with a `prefer_cheap` query flag). Results carry canonical metadata (name, family, short_description, source, current zone in the active surface, declared tier) + a `borrow_eligibility` flag indicating whether the active composition allows the model to borrow. A capability that exists but is `Disabled`/`Unavailable`/excluded by `forbidden_capability_ids` returns `borrow_eligibility: denied` with the typed reason; the model receives it in-band and may try a different capability or escalate.
### 7.5 Discovery Is Auditable
Every `tool.search`, `mcp.search`, `tool.borrow`, `tool.borrow_persistent`, `tool.inspect` call recorded in the ledger [`run.execution-ledger`, File 04 §23.1]. Audit reconstructs which capabilities the agent searched for/borrowed/invoked. The future Quality Control+Evaluation spec may inspect this trace for tool-use efficiency analysis.
### 7.6 Boundary
Discovery capabilities are the canonical mechanism for agent-initiated surface visibility changes; not the only surface-relevant input path (settings changes, plugin install, MCP connect, `BorrowGrant`s created by other paths, policy changes, routing decisions all affect composition, §13).

## 8. Default Composition and Auto-Shrink `surface.default-composition-auto-shrink`
### 8.1 Default Composition (fresh `Run`)
1. Resolve the active `SubsystemSurfaceSpec` from `RunIntent.primary_surface` (§5)
2. Place every `primary_capability_ids` entry in `Primary` for `ModelAgent` lens; user-facing lenses also see them as `Primary`
3. Place every `borrowable_capability_ids` entry in `Borrowable`
4. Place every capability whose declared family is in `default_deferred_families` into `Deferred`
5. Exclude every capability in `forbidden_capability_ids` from any zone except the inspector (where it appears with a `Forbidden` indicator)
6. For `supporting_surfaces` from `RunIntent` (§6.1): promote their `primary_capability_ids` into the current surface's `Borrowable` zone
7. Apply `tool_surface_strategy` adjustments per §5.3
8. Apply the resolved settings snapshot (§12.1, §18) — per-capability zone overrides, per-family zone overrides, always-load and never-load marks
9. Apply active `BorrowGrant`s — grants promote their targets to `Primary` for the scope
10. Evaluate `enabled` flag — capabilities disabled at any active scope move to `Disabled`
11. Evaluate availability — capabilities whose `availability_status` is not `Available` move to `Unavailable` regardless of prior zone
12. Apply trust narrowing per [`policy.effective-tier-resolution`, File 06 §4] — capabilities from `Community`/`Unverified` sources may shift between zones per source policy
13. Estimate model-request cost of the resulting `Primary`+`Borrowable` zones using provider-aware token counting [`run.execution-ledger`, File 04 §23.1; File 13] against the model's context budget
14. If estimated cost exceeds the configured tool-surface budget, run auto-shrink (§8.2)
15. If legal shrink cannot fit the surface, return `ToolSurfaceOverflow`
16. Render `composition_diagnostics` (§2.3) recording every assignment decision+reason
17. Emit `ToolSurfaceComposed` event with the surface snapshot id (§13)
### 8.2 Auto-Shrink Algorithm `surface.auto-shrink-algorithm`
When the assembled surface's estimated token cost exceeds the configured surface budget (a slice of the model's context window, per File 13), auto-shrink runs deterministically in priority order:
- **Step A** — drop `default_deferred_families` already-deferred entries from the `Borrowable` catalog block. These entered `Borrowable` only through `supporting_surfaces` promotion or routing; the subsystem explicitly deferred them.
- **Step B** — demote `Borrowable` entries beyond a configured `borrowable_cap` to `Deferred`. The cap is a setting (§18); default keeps roughly the active subsystem's natural borrowable size. Demoted entries leave the `Borrowable` catalog block in the model request.
- **Step C** — abbreviate `Borrowable` catalog block by removing per-family grouping headers+per-entry family annotations, keeping only `name`+`short_description`.
- **Step D** — demote `Primary` entries tagged `experimental`, `low-frequency`, or carrying a per-entry `auto_shrink_eligible` settings flag to `Borrowable`. These lose provider-native callable declarations but remain discoverable.
- **Step E** — demote `Primary` entries by declared priority (lower declared priority within the subsystem spec demoted first; the spec may declare an ordering or fall back to alphabetical).
- **Step F** — emit a typed warning to the user surface + to the next model request that the surface has been heavily shrunk; the model may proactively borrow; the user may relax the budget or close other context consumers (compaction, attachments, history).
Auto-shrink never moves anything pinned by the user (§12 always-load marks); never demotes the discovery capabilities (`tool.borrow`, `tool.search`, `mcp.search`, `tool.inspect`) below `Borrowable`; records every demotion in `auto_shrink_record` (§2.3). If pinned `Primary` entries still exceed the provider/model limit after every legal shrink step, composition returns `ToolSurfaceOverflow` instead of demoting pinned capabilities or sending an invalid request. The error names the pinned entries, estimated size, active limit, and recovery options: choose a larger-context model, unpin tools, move some tools to `Borrowable`, or rely on search/borrow.
### 8.3 Auto-Shrink is Non-Destructive and Always In-Band `surface.auto-shrink-non-destructive`
Does not require user approval; runs deterministically; reversible (the next composition without budget pressure produces the un-shrunk surface). The agent sees the post-shrink model request with the typed notice; the user sees the shrink in the surface inspector + through `ToolSurfaceShrunk` (§13). Should preserve stable ordering+cacheable model-request prefixes when possible — demote from the tail of the cacheable prefix before disturbing it, avoid reordering the stable region. Fitting within budget always wins over cache preservation, but the achieved `cache_impact` must be recorded on `auto_shrink_record` (§2.3): `none` when nothing cacheable moved; `preserved_prefix` when only post-prefix entries moved; `changed_tool_surface_only` when the tool-surface block changed but instruction+region order did not; `changed_instruction_or_region_order` when stable-region ordering changed; `full_cache_break_likely` when the change very likely invalidates the provider cache.
Settings (§18) control: `tool_surface_budget` per scope; `borrowable_cap` (max `Borrowable` entries); `shrink_priority_override` (per-capability/family override of the default priority order); `shrink_enabled` per scope (users may disable; if the resulting surface no longer fits, context assembly receives a typed overflow instead of an over-limit request).
### 8.4 Shrink Does Not Affect User-Facing Surfaces
Auto-shrink applies to `ModelAgent` lens. User-facing lenses (`Palette`, `Voice`, `Shortcut`, `AutomationTrigger`) are not budget-constrained the same way (no token cost for a palette view); always show the full `Primary`+`Borrowable` set regardless of agent-side shrink state, with an indicator that the model request is under shrink. The user may invoke any capability through the palette regardless of which zone the model sees it in.
### 8.5 Boundary
Auto-shrink is a tool-surface concern; does not compact conversation history ([`run.boundary-rule`, File 04 §20.1] reports context pressure to the context layer; the context layer decides whether to compact). The two mechanisms cooperate: under context pressure, the context layer may compact history first, the surface composer may shrink, or both may run in their own layers without coordination.

## 9. Visibility Composition Resolution Algorithm `surface.visibility-composition-resolution-algorithm`
### 9.1 Algorithm (17 steps)
The canonical deterministic function producing a `ResolvedToolSurface` from inputs.
```
compose_surface(invoker_kind, invocation_lens, scope_context) -> ResolvedToolSurface

scope_context := {
  run_id (optional),
  intent_thread_id, task_id, conversation_id, workspace_id,
  profile_id, primary_surface_id, supporting_surface_ids,
  routing_strategy, routing_metadata,
  active_world_snapshot_id, active_settings_snapshot_id,
  active_borrow_grant_set_id, active_policy_snapshot_id, active_model_id, active_provider_id,
  active_context_budget,
}

Step 1 — Resolve the active SubsystemSurfaceSpec from primary_surface_id.
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
  - per-capability never-load mark: clamp to Disabled.
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
  Apply per-lens filters:
    - ModelAgent: capability.tags must include 'agent-invokable'.
    - Palette: capability.tags must include 'palette-invokable'.
    - Voice: capability.tags must include 'voice-invokable'.
    - Shortcut: capability has default_shortcut OR user-bound shortcut.
    - AutomationTrigger: capability.tags must include 'automation-trigger'.
    - ExternalMcp: capability.tags must include 'external-exposed'
                   AND source-approval permits external exposure.
    - Inspector: no filter; all entries surfaced (including Disabled, Unavailable).
  Capabilities filtered out for the lens are placed in Disabled for this lens,
  with diagnostic note `lens_filter_excluded`.
Step 13 — Estimate model-request cost (ModelAgent lens only):
  Sum estimated tokens for all Primary entries' full schemas + Borrowable
  catalog block + discovery capabilities catalog.
Step 14 — Apply auto-shrink if estimated cost > active_context_budget.tool_surface_budget:
  Run the auto-shrink algorithm (§8.2). Record every demotion in
  auto_shrink_record. The Primary and Borrowable sets after shrink are the
  rendered sets.
Step 15 — If legal shrink cannot fit the surface:
  Return ToolSurfaceOverflow with pinned entries, estimated size, active limit,
  and recovery options.
Step 16 — Produce ResolvedToolSurface:
  - surface_id = stable hash over (invoker_kind, invocation_lens,
    scope_context.snapshot, registry snapshot id, settings snapshot id,
    borrow-grant set id, post-shrink zones, provider_name_map).
  - zoned_entries grouped by zone.
  - provider_name_map if provider-visible names were rendered.
  - composition_diagnostics with per-capability reason for assignment.
  - auto_shrink_record (empty if no shrink).
Step 17 — Emit ToolSurfaceComposed event with surface_id and diagnostic facts
  for the inspector and the ledger.
```
### 9.2 Determinism
Deterministic given same inputs. Two compositions with the same `scope_context`, registry snapshot, settings snapshot, `BorrowGrant` snapshot produce byte-identical `ResolvedToolSurface` outputs+byte-identical rendered model-request surface content. Load-bearing for cache friendliness where supported [`run.from-run-intent-to-run`, File 04 §3.3] + replay [`run.ledger-events-commits`, File 04 §23; File 10].
### 9.3 Caching
Result cached keyed by input snapshot identifiers; a subsequent composition with the same inputs returns the cached `ResolvedToolSurface` without re-running every step. Invalidation is event-driven, not time-based — see §13 for mutation events that invalidate cached compositions.
### 9.4 Algorithm Settings
Configurable through settings (§18):
- `auto_shrink_enabled` — whether auto-shrink runs at all
- `tool_surface_budget_token_count` — the model-request budget for tool definitions; default a fraction of the model context window
- `borrowable_cap_count` — max `Borrowable` entries before forced demotion
- `lens_filter_strictness` — `strict` (must explicitly carry the lens tag) or `permissive` (eligible unless explicitly excluded)
- `trust_narrowing_active` — whether trust narrowing affects zone or only displays inspector-side flags
- `forbidden_visible_in_palette` — whether `forbidden_capability_ids` still appear in palette with a disabled indicator (default true for inspectability)
- `unavailable_visible_in_palette` — whether `Unavailable` entries appear in palette (default true with a "currently unavailable" indicator)
- `default_deferred_visible_in_palette` — whether `Deferred` entries appear in palette by default (default false; user can reveal)
### 9.5 Boundary
The algorithm is the canonical contract; implementations may use any data structure/caching strategy/concurrency model producing byte-identical results from identical inputs. Future runtime infrastructure spec defines implementation patterns; File 07 defines the contract.

## 10. Tool Surface and Capability Policy `surface.tool-surface-capability-policy`
### 10.1 Boundary
Sharp: Surface (File 07) controls **visibility** (whether the capability appears in the model request/palette/voice grammar/automation editor); Policy (File 06) controls **authority** (whether a proposed invocation proceeds, requires user approval, requires typed confirmation, or is denied). A capability can be visible without being permitted: the model sees `git.push --force` in `Primary`, and on proposal the policy layer evaluates the effective tier; if the branch is in the protected-branch list [`policy.built-in-reusable-policy-rules`, File 06 §11.5], the proposed call is denied at typed-confirmation; the agent receives a typed in-band denial [`run.denial-is-in-band`, File 04 §8.3]. A capability can be permitted without being visible: the user invokes through the palette a capability `Deferred` for the model's surface — the policy layer evaluates the user-direct invocation the same way; the capability is invocable, the model just did not have it in its request.
### 10.2 Visibility Customization Honors Policy
Users may hide capabilities they cannot use anyway (capabilities at `Denied` floor without typed-confirmation override) or show them for transparency; the settings dimension `policy_blocked_visible` (§18) controls this. The algorithm honors the setting; the result is the same effective denial behavior regardless of visibility, because policy is the authority layer.
### 10.3 Source-Approval Affects Surface
When a plugin/MCP server/external API/user-defined capability registers [`capability.runtime-mutation`, File 05 §16.2; `policy.source-approval-flow`, File 06 §9], the source-approval flow runs. Until it completes, the source's capabilities are in `Disabled` for all invokers. When the flow grants any policy state, affected capabilities transition to their declared zones; transitions emit surface-relevant events (§13). Source-approval revocation (user denies the source or connection lost) demotes them back to `Disabled`/`Unavailable` depending on underlying state.
### 10.4 Policy Events Inform the Surface
The inspector lens surfaces policy-relevant facts: which capabilities are currently at floor `Denied`, which are subject to a `Sensitive` data classification [`run.event-stream`, File 04 §23.2], which are typed-confirmation-required, which currently carry a `Stale` lease. Read from File 06 policy state, not duplicated in File 07.
### 10.5 Boundary
File 07 reads from File 06 to decide presentation; does not duplicate policy state, does not implement approval evaluation. The algorithm (§9) consumes policy-resolved facts as inputs; the evaluation itself runs in File 06's layer.

## 11. Presentation in the Model Request `surface.presentation-in-model-request`
### 11.1 Position in the Model Request
Deterministic position: after the identity+core-instructions section [File 13]; before conversation history+current user message; `Primary` entries render first as provider-native callable declarations where the provider supports them; the `Borrowable` catalog block renders next as model-request text content; optionally a typed `auto_shrink_record` notice renders after the catalog if shrink occurred; the discovery capabilities (`tool.borrow`, `tool.search`, `mcp.search`, `tool.inspect`) render alongside other `Primary` entries (first-class registered capabilities, not a separate hint section). Position stable across turns: two consecutive turns with the same `ResolvedToolSurface` produce byte-identical surface content up to the moment conversation history changes, enabling provider cache reuse where supported.
### 11.2 Per-Provider Format Normalization
Native tool-call format varies by provider [`run.tool-calls`, File 04 §9; `capability.schemas`, File 05 §4; `capability.discovery`, File 05 §15.1]. The algorithm produces a canonical `ResolvedToolSurface`; the provider adapter [File 17] renders `Primary` entries as provider-native callable declarations when possible and records `provider_name_map` for any provider-visible renaming. Native-format rendering preserves: `name` (capability id, primary alias, or provider-safe name with a recorded `provider_name_map` entry); `description` (localized full); `input_schema` (declared JSON Schema converted to the provider's dialect); optional hint fields (for providers accepting them, hints derived from `tags`/`cost_model`). Omits: internal touched-resource expressions [`capability.resource-expressions`, File 05 §6.4] (policy-side); backend descriptor [`capability.backend-descriptor`, File 05 §3.12] (implementation detail); per-call resolved facts [`capability.invocation-record`, File 05 §11] (belong to the invocation record).
### 11.3 Tool Metadata Is Data, Not Instruction
Capability descriptions, schemas, MCP metadata, plugin metadata, external-API descriptors, user-defined capability text are untrusted data when rendered into the model request; they do not gain instruction authority by appearing near callable declarations or catalog entries. External/source-authored descriptions must have source attribution rendered alongside them, length limits per external description configurable by source class, explicit instruction-boundary markers in the assembled request; placed inside a clearly delineated data section; the model's governing instructions identify that section as untrusted data, not instructions. Textual filtering of injection phrases is not a correctness mechanism; the boundary is architectural.
### 11.4 Borrowable Catalog Block Format
Rendered as a single text block (not native tool declarations, which would consume too many tokens):
```
You can borrow additional tools at the cost of one round-trip via the
`tool.borrow(capability_id)` capability. Borrowed tools are available for the
active BorrowGrant scope.

Borrowable tools available:
- family/name — short_description
- family/name — short_description
- ...
```
Alphabetized by family then by name within family for cache-friendliness. The model scans the list and emits `tool.borrow(family.name)` to load the full schema. Model-request text content, not a tool result.
### 11.5 Deferred Capabilities Are Not in the Model Request
`Deferred` entries not rendered into the request at all. The model knows about them only through: explicit hints injected by the user message ("use the data analysis tools"); hooks injecting hints based on task context [`run.hook-integration`, File 04 §23.3]; the model's own decision to call `tool.search`. Keeping `Deferred` out is the load-bearing request-economy decision (a `Borrowable` catalog of fifty entries is cheap; a `Deferred` set of five hundred is too expensive — search-based discovery is the design).
### 11.6 Empty Surface Handling
If the algorithm produces no `Primary` entries (e.g. `execution_entry` is `respond_inline` and no surface/routing strategy contributed Primary capabilities), the request's callable-declaration section is empty; the native provider format omits the tools field where appropriate [`run.tool-calls`, File 04 §9; File 17]. `tool_choice` semantics: `none` (model produces text only; the surface is rendered as if empty for this turn); `tool_choice: auto` (default; model uses tools or not at its discretion); `required` (model must call a tool; the rendered surface must have at least one Primary entry, otherwise composition fails with `EmptyToolSurfaceWithRequiredChoice`; routing/execution recovery may intentionally downgrade to `respond_inline`, but that decision is recorded). `tool_choice` set by `RunIntent.execution_entry` + active model strategy [`run.execution-entry`, File 04 §4; `routing.model-routing`, File 03 §7].
### 11.7 Cache-Friendly Ordering `surface.cache-friendly-ordering`
Within `Primary`, deterministic order:
1. Discovery capabilities (`tool.borrow`, `tool.search`, `mcp.search`, `tool.inspect`) first — always present in `Primary` (unless explicitly demoted by settings); stable position makes them part of the cached prefix
2. Capabilities from the active `SubsystemSurfaceSpec.primary_capability_ids` in their declared order
3. Capabilities promoted from `supporting_surfaces` in their respective subsystem order
4. Capabilities promoted by `tool_surface_strategy` in the order specified in `routing_metadata`
5. Capabilities promoted by active `BorrowGrant`s in grant order
Canonical cache-friendly ordering; changing it (e.g. sorting alphabetically every turn) can invalidate cached prefixes. The setting `model_request_order_strategy` allows alternatives (alphabetical, frequency-based).
### 11.8 Boundary
File 07 specifies what surface content exists+in what order; the actual model-request assembly (combining surface with the rest, applying cache markers, enforcing request-size invariants) is File 13's concern. File 07 hands rendered surface content to context assembly; context assembly composes the full request.

## 12. Presentation in User-Facing Surfaces `surface.presentation-in-user-facing-surfaces`
### 12.1 Palette Lens
Renders the surface as a searchable user-facing list. Per-entry data: `display_name` [`capability.display-fields`, File 05 §3.2] localized; `description`+`short_description` localized; `family` for grouping; `tags` for filtering; `icon_key` [`capability.display-fields`, File 05 §3.2] (actual icon image owned by future UI spec); `default_shortcut` [`capability.display-fields`, File 05 §3.2] + any user-bound shortcut; `source` for source filtering; `effective_tier` (resolved per [`policy.effective-tier-resolution`, File 06 §4]) for approval indicators ("requires approval", "typed-confirmation required", "blocked", "trusted"); `availability_status` [`capability.registered-capability`, File 05 §10]; `zone` for visual grouping (Primary prominent; Borrowable slightly de-emphasized; Deferred only if user revealed). The palette consumes this typed data+renders; future UI spec specifies layout/color/animation/search behavior.
### 12.2 Voice Lens
Filters capabilities tagged `voice-invokable` [`capability.display-fields`, File 05 §3.2]. Per entry: `display_name`+`description`; `voice_aliases` (spoken phrases mapping to the capability, e.g. "read the file", "open the project", "send an email"); `argument_extraction_hints` (typed hints for voice-to-arguments extraction per future Voice spec); `effective_tier` (voice invocation may produce a typed-confirmation request for high-tier capabilities [`policy.approval-ui-surface-contract`, File 06 §13]). Voice invocation invokes through the same [`run.call-pipeline`, File 04 §8.2]; the resolver is just another invoker.
### 12.3 Shortcut Lens
Renders a chord-to-capability map; entries are capabilities with a declared `default_shortcut` or a user-bound shortcut. Chord format per future Keybinding spec; File 07 specifies: conflicts detected at registration time (two capabilities with the same shortcut produce a `ShortcutConflict` event per §13; the registry rejects the second registration unless explicitly overridden); user-bound shortcuts override `default_shortcut` declarations; shortcuts are keybinding-context-aware (the same chord may invoke different capabilities depending on the active keybinding context).
### 12.4 Inspector Lens `surface.inspector-lens`
Shows the full registry catalog with no filtering — every registered capability in every zone (incl. `Disabled`, `Unavailable`, `Forbidden`). The canonical management surface; future UI Customization spec renders it as a tab/panel with: per-source enable/disable toggle; per-family enable/disable; per-capability enable/disable; per-capability zone override (always-load, never-load, always-deferred, never-show-in-palette); search+filter by family/source/tag/risk class/effective tier; group-by axis selection (family, source, risk class, integration-source, invocation-path); per-source trust override [`policy.risk-classification-trust-interaction`, File 06 §15]; per-capability shortcut binding; inspection of declared metadata (description, input/output schemas, touched_resources expressions, replay class, postconditions); inspection of recent invocations [File 10]. The inspector's data contract is the canonical surface customization surface; users do not need to write settings files manually.
### 12.5 Automation Trigger Lens
Filters capabilities tagged `automation-trigger` + capabilities invocable as automation actions. Carries: per-capability `automation_input_template` (typed structure naming which inputs are required, which are derived from trigger context (event payload, scheduled context, watch state), which are pinned at save time); per-capability `automation_constraints` (typed constraints the future Automation spec evaluates, e.g. automation cannot invoke capabilities with `replay_class: not_replayable`).
### 12.6 External MCP Lens
Filters capabilities tagged `external-exposed`, renders them as MCP-protocol tool advertisements. Carries: `mcp_tool_name` (typically the canonical id, possibly with a per-source rename for protocol compatibility); `mcp_description`+`mcp_input_schema` (JSON Schema as MCP expects); `mcp_metadata` (per-tool metadata MCP clients may use). External MCP exposure gated by source-approval [`policy.source-approval-flow`, File 06 §9]; capabilities not approved for external exposure are filtered out.
### 12.7 Per-Lens Visibility Rules
Each lens enforces its own rules in step 12 of the algorithm (§9.1). A capability with tags `[agent-invokable, palette-invokable]` appears in `ModelAgent`+`Palette` lenses but not `Voice`/`Shortcut`. A capability with only `[agent-invokable]` appears only in `ModelAgent`; the model can call it but the user cannot invoke it through the palette. Visibility tags are part of declared `tags` [`capability.display-fields`, File 05 §3.2]; users may customize per-capability through settings (§18).
### 12.8 Boundary
File 07 specifies the per-lens data contract; future UI Shell+Customization specs render those into actual UI; future Voice spec specifies voice-to-arguments extraction; future Automation spec specifies trigger evaluation+action invocation. File 07 hands them the canonical lens data+lens-filter algorithm.

## 13. Surface-Relevant Events `surface.surface-relevant-events`
### 13.1 Event Vocabulary (16)
Every surface-relevant input change/grant change/source lifecycle change/consumed composition emits a typed event through the canonical event bus with the standard envelope [`run.event-stream`, File 04 §23.2]: `conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`. Canonical events:
- `ToolSurfaceComposed { surface_id, invoker_kind, scope_context_id, zone_counts, auto_shrink_record }` — a new composition produced
- `CapabilityBorrowed { surface_id, capability_id, capability_version, borrow_grant_id, grant_scope, borrowed_by }` — a `tool.borrow` granted a `BorrowGrant`
- `CapabilityBorrowReturned { surface_id, capability_id, borrow_grant_id, reason }` — a `BorrowGrant` revoked/expired
- `CapabilityZoneChanged { surface_id, capability_id, old_zone, new_zone, reason }` — a zone reassignment across compositions (typically settings change, grant change, availability change, trust change)
- `CapabilityRegistered { capability_id, capability_version, source, default_zone }` — a new capability registered [`capability.events`, File 05 §12.2]; incorporated on next computation
- `CapabilityUnregistered { capability_id }` — removed from the registry; active surfaces lose the entry
- `CapabilityEnabledChanged { capability_id, enabled, scope }` — enable/disable change at any scope
- `CapabilityAvailabilityChanged { capability_id, old_status, new_status, reason }` — `availability_status` transition (handler unresolved, MCP disconnect, platform mismatch detected, prerequisite satisfied/unsatisfied)
- `ToolSurfaceShrunk { surface_id, demoted_capability_ids, budget_consumed, budget_limit }` — auto-shrink demoted capabilities
- `ToolSurfaceOverflow { surface_id, pinned_capability_ids, estimated_size, active_limit, recovery_options }` — composition could not legally fit the required surface
- `SubsystemSurfaceSpecUpdated { subsystem_id, old_version, new_version, affected_surface_ids }` — a subsystem changed its declared default surface contract
- `PrimarySurfaceChanged { run_id, old_primary_surface_id, new_primary_surface_id, reason }` — the active spec changed mid-run (typically reroute [`routing.mid-execution-reroute`, File 03 §12])
- `SurfaceSettingsChanged { scope, settings_keys_changed }` — surface-relevant settings mutated; affected compositions recompose
- `SourceConnected { source_id, source_kind }` — a plugin loaded, MCP server connected, external-API definition imported; incorporated on next composition (subject to source-approval [`policy.source-approval-flow`, File 06 §9])
- `SourceDisconnected { source_id, source_kind, reason }` — a source disconnected; its capabilities transition to `Unavailable`
- `LensFilterChanged { lens, scope }` — per-lens visibility settings changed
- `ShortcutConflict { conflicting_capability_ids, chord }` — a shortcut collision was detected
### 13.2 Event Sensitivity
Carry the canonical `sensitivity` tag [`run.event-stream`, File 04 §23.2]. Most surface events are `Public` (no secret content); events touching credentials/sensitive sources may be `Sensitive` (per the underlying capability's `data_sensitivity`); events naming raw secrets are `Secret` and never persisted to the durable ledger.
### 13.3 Event Consumers
- the model context — the next assembled request for an active `Run` incorporates the change (recomposing the surface, emitting an in-band notice if relevant to the model's plan)
- the UI — palette, inspector, other surfaces re-render on every relevant mutation
- the execution ledger — events relevant to audit+replay persisted [`run.execution-ledger`, File 04 §23.1]
- hooks subscribed to surface events — extensions/plugins/user hooks may react [`run.hook-integration`, File 04 §23.3]
### 13.4 Mid-Run Change Notification to the Model
When a surface-relevant change occurs during an active `Run`'s execution (between model turns or between iterations of the model/tool loop [`run.model-tool-loop`, File 04 §7]), the next assembled request includes a typed notice. Short structured text lines, e.g.:
- `[surface] Capability borrowed: web.fetch — now available in Primary.`
- `[surface] Capability went unavailable: gui.screenshot — accessibility permissions revoked.`
- `[surface] MCP server connected: linear-mcp — 18 new capabilities available in Borrowable.`
- `[surface] Auto-shrunk: 12 capabilities demoted from Primary to Borrowable — context budget tight.`
- `[surface] Primary surface changed: now using Web — tool surface recomposed.`
Notice format is a settings-controlled rendering choice; the canonical contract is that mid-run surface changes are visible to the model so it can adjust strategy. The model may also call `tool.inspect`/`tool.search` after a mutation to confirm what is available.
### 13.5 Event Stream Versus Durable Ledger
Per [`run.ledger-events-commits`, File 04 §23], the event stream is the live coordination channel; the ledger is durable history. Surface-relevant events flow through both: every event emits to the event stream so consumers react in real time, and consequential events (capability registrations, `BorrowGrant`s, surface compositions consumed by a model turn) are also recorded in the durable ledger.
### 13.6 Boundary
File 07 specifies the event vocabulary+per-event payload; the event-bus implementation (delivery semantics, subscription mechanics, replay) owned by [`run.ledger-events-commits`, File 04 §23] + File 10.

## 14. Persistence and Reconstruction `surface.persistence-reconstruction`
### 14.1 What Persists Durably
Durable: the Capability Registry (registered capabilities + their `RegisteredCapability` state [`capability.registered-capability`, File 05 §10] survive restart); per-scope settings (per-workspace+per-conversation surface customization persists through the settings system; profile-specific defaults are profile layers; run+per-call changes are invocation overlays); `BorrowGrant`s (durable grants at scopes `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule` survive restart until revocation conditions apply); the execution ledger (every `ResolvedToolSurface` consumed by an invocation recorded with surface_id, composition_diagnostics, zoned_entries; replay reconstructs the exact surface a past invocation saw).
Not persisted as independent state: `ResolvedToolSurface` (computed, not stored as a separate mutable record; the ledger records consumed surfaces, but the active surface for a running run is always re-derived from current inputs); per-turn rendered model requests (reconstructible by re-running composition with the recorded settings, `BorrowGrant`, registry snapshots).
### 14.2 Reconstruction Across Restart `surface.reconstruction-across-restart`
On process restart [`run.cancellation`, File 04 §17.3; `capability.lifecycle`, File 05 §16.6]:
1. The registry re-registers its capabilities (built-in, subsystem, plugin, MCP, API, user-defined) in the order specified by [`capability.startup-registration`, File 05 §16.1]
2. The settings system reloads per-scope settings
3. The `BorrowGrant` store reloads durable grants; grants targeting unregistered capabilities revoke or become stale per recorded revocation conditions
4. Capability availability re-evaluated against the active world-model snapshot
5. Source connections (MCP servers, plugins) re-establish per their own lifecycles; unavailable sources produce `Unavailable` capabilities until reconnect
6. Any `Run`s active at restart follow the orphan-run rules [`run.cancellation`, File 04 §17.3]; their surfaces are not auto-resumed
7. New runs compose fresh surfaces from the restored state
Restored state deterministic given the same registry state, settings, `BorrowGrant` set; the surface a new run sees after restart equals what it would have seen before, modulo changes during the offline interval (plugin updates, settings changes via cold-edit tooling, etc.).
### 14.3 Reconstruction Across Retry, Edit, Reroute, Branch `surface.reconstruction-across-retry-edit-reroute-branch`
Per [`run.retry-reroute-branch`, File 04 §19], retry/edit/reroute/branch produce new runs linked to prior ones. Composition for each new run runs against current inputs (which may differ if settings/routing changed). The prior run's surface is preserved in the ledger; the new run's is freshly composed. Run-scoped `BorrowGrant`s do not transfer across retry/edit/reroute/branch (the new run is fresh, the grant did not span runs); grants at wider scopes (`intent_thread`, `task`, `conversation`, etc.) do transfer per their scope rules.
### 14.4 Reconstruction in Child Runs
Per [`run.child-runs-multi-agent-work`, File 04 §16], a child run runs with its own surface; the child's primary surface is determined by the child's `RunIntent` per File 03 routing (may inherit the parent's or transition to a different surface). The child's surface is composed fresh from the resolved settings snapshot applicable to its scope but does not inherit the parent's run-scoped `BorrowGrant`s by default; a child run may borrow capabilities its parent had borrowed (still in the registry), but the `BorrowGrant` is granted to the child's run id, not inherited. The child's surface is constrained by its declared `tool_allowlist` [`run.isolation`, File 04 §16.2] — if the parent declares the child can only use a subset, the child's composition filters by the allowlist as an additional step at the end of step 12 of §9.1.
### 14.5 Reconstruction in Edit-Reroute
Per [`routing.edit`, File 03 §11.2], editing a prior user message invalidates the prior route, the edited request must be rerouted; the rerouted request produces a new `RunIntent` whose `tool_surface_strategy` may differ. The new run composes its surface from the new `RunIntent`; the prior run's surface remains in the ledger for inspectability.
### 14.6 Boundary
File 07 specifies what is computed vs durable + how reconstruction works; actual storage of `BorrowGrant`s/policy leases/settings/ledger entries owned by future Storage spec; actual replay machinery owned by File 10.

## 15. MCP and Plugin Tool Integration `surface.mcp-plugin-tool-integration`
### 15.1 Sourced Capabilities Enter the Single Registry
Per [`capability.sourcing`, File 05 §9], capabilities sourced from MCP servers (`McpServer`), plugins (`Plugin`), external APIs (`Api`), or user definitions (`UserDefined`) enter the same registry through the same pipeline as built-in+subsystem capabilities. No parallel "MCP tool list"/"plugin tool catalog" — one registry, source is metadata on the registered entry [`capability.sourcing-equivalence`, File 05 §9.3]. File 07 surfaces consume this registry uniformly; the algorithm (§9) does not distinguish source kinds in core logic; per-source filters+trust narrowing are settings-driven options applied during step 10, but the surface is built from the registry, not from per-source registries.
### 15.2 MCP Server Lifecycle and the Surface
MCP server connect → tools register → next composition incorporates them, subject to source-approval [`policy.source-approval-flow`, File 06 §9]. MCP server disconnect → registered MCP-sourced capabilities transition to `availability_status: unavailable_handler`; next composition shows them `Unavailable`. MCP server reconnect → transition back to `Available`; next composition restores declared zones. Reconnection should preserve identity [`capability.trust-source-approval-flow`, File 05 §9.2]: the same `mcp.server_id.tool_name` id re-resolves to the same registered entry; re-registration is the normal path; the registry detects idempotent registration and updates `resolved_backend_binding` without changing identity.
### 15.3 Plugin Lifecycle and the Surface
Plugin install → capabilities register; user reviews source-approval; surface incorporates approved capabilities. Plugin uninstall → capabilities unregister; surface loses them. Plugin update → a new declaration version [`capability.version`, File 05 §13.4]; minor/patch update loads transparently; a major version with breaking changes [`capability.version`, File 05 §13.4 semver] makes affected `BorrowGrant`s stale or revoke per their conditions; the model receives a typed notice on next turn that affected capabilities have a new version available.
### 15.4 Large MCP Registries
Default loading conservative: all MCP-sourced capabilities default to `Borrowable` for `ModelAgent` if the active `SubsystemSurfaceSpec` does not explicitly place them in `Primary`; the `Borrowable` catalog block grows; auto-shrink (§8) may demote MCP-sourced entries first under budget pressure; the model can use `mcp.search` to filter MCP entries by family/query without rendering all; per-server enable/disable lets the user keep the registry without seeing every server's capabilities in every surface. A user actively working with a specific server's tools can promote them to `Primary` through per-server settings (§18); the workspace-level setting effectively makes that server's tools first-class for the workspace.
### 15.5 Source-Approval Affects Initial Zone
When a source registers+passes source-approval, the outcome determines initial zone:
- `AcceptDefaults` — capabilities enter at their declared default zones (per declarations + active spec); if no spec mentions them, default to `Borrowable` for `ModelAgent`
- `CustomizePerCapability` — per-capability zone set explicitly during source-approval
- `CustomizePerSource` — per-source trust override+default-zone preference recorded; future registrations from this source apply the source-default
- `DenyOutright` — capabilities enter `Disabled` zone
- `DeferSourcePolicy` — capabilities enter `Unavailable` zone (`unavailable_handler` reason: "pending source policy"); each invocation falls through to ask-user per the fallback policy
### 15.6 External APIs and User-Defined Capabilities
External-API capabilities (declared in TOML or equivalent [`capability.capability-source`, File 05 §9.1]) load at startup or when the definition file is loaded; composition treats them like any other capability. User-defined capabilities registered through `tools.register_custom` [`capability.runtime-mutation`, File 05 §16.2] enter at the declared scope (`conversation`, `workspace`, `global`); user-defined `conversation`-scoped capabilities visible only to runs in that conversation; the algorithm filters by scope.
### 15.7 Boundary
File 07 specifies how source-derived capabilities surface; actual MCP transport, plugin install lifecycle, external-API definition format owned by their respective later specs (MCP and External Integrations, Extension and Plugin System). File 07 consumes their registered output through the unified registry contract from File 05.

## 16. Tool-Choice Mechanics `surface.tool-choice-mechanics`
### 16.1 `tool_choice` Settings
Per [`run.execution-entry`, File 04 §4] + the active provider's tool-call format, every model invocation carries an explicit/implicit `tool_choice`:
- `auto` (default) — model decides whether to call a tool based on the rendered surface
- `none` — model produces text only; the surface rendered without tool declarations or with an explicit "tools disabled" indicator depending on the provider
- `required` — model must call at least one tool; the surface must contain at least one Primary entry
- `specific_tool(id)` — model must call the named tool; the surface must contain it in Primary or it is promoted by the routing layer
Set by routing per `RunIntent.execution_entry`: `respond_inline` typically → `tool_choice: none`; `respond_with_tools` → `auto`; `surface_runtime` → `auto` or `specific_tool` depending on the primary surface's entry pattern; `multi_step_agent` → `auto`.
### 16.2 Empty Surface Handling
If composition produces zero `Primary` entries and active `tool_choice` is `auto`/`required`: `auto` → render the surface as empty (no tools advertised); model produces text only. `required` → composition fails with typed error `EmptyToolSurfaceWithRequiredChoice`; the executor returns a typed denial to routing; routing may downgrade to `respond_inline` and recompose, or surface the error. Empty surfaces occur when: the active spec declares no primary capabilities (a subsystem that exclusively delegates to subagents); routing chose `respond_inline` and no preparatory tool calls were registered (typical conversation-only response); all primary capabilities are currently `Unavailable` and no auto-promotion fills the gap.
### 16.3 Forced Tool Choice
When `tool_choice: specific_tool(id)` is set, the algorithm promotes the named capability to `Primary` regardless of base zone, subject to: `enabled` true at the active scope; `availability_status` is `Available`; the capability not in `forbidden_capability_ids` for the active surface; the effective tier [`policy.effective-tier-resolution`, File 06 §4] does not yield `Denied`. If any fails, the executor returns a typed denial: `ForcedToolChoiceUnavailable { capability_id, reason }`; routing handles the denial.
### 16.4 Boundary
`tool_choice` set by routing+consumed by the active provider's tool-call format; File 07 specifies how composition interacts with the chosen mode; File 03 owns routing's choice; [`run.tool-calls`, File 04 §9] owns provider parser variation.

## 17. Degradation and Graceful Absence `surface.degradation-graceful-absence`
### 17.1 Availability Transitions Mid-Active
`availability_status` [`capability.registered-capability`, File 05 §10] may transition during an active `Run`. Common triggers: the underlying handler became unresolvable (MCP server crashed, plugin module unloaded, sandboxed process exited); a prerequisite capability unregistered or its required state lapsed; a platform-dependent resource became unavailable (accessibility API permission revoked, GPU device offline); a credential expired/revoked (future Security spec); world-model state changed such that an `availability_predicate` no longer evaluates true. Every transition emits `CapabilityAvailabilityChanged` (§13); the next composition sees the new status. If the run's request currently exposes the capability in `Primary` and the next composition transitions it to `Unavailable`, the next turn's request: removes the capability from `Primary`; includes a typed notice describing the transition; the inspector lens still shows it with the typed reason.
### 17.2 Capability Becomes Available Mid-Run
Reverse transition (`Unavailable` → `Available`) also emits an event; the next composition restores the declared zone; the next turn's request includes a typed notice ("Capability X is now available again"); the model may use it from that point.
### 17.3 In-Flight Calls
If a capability transitions to `Unavailable` while a call is in flight, the executor [`run.cancellation`, File 04 §17.3; `policy.mid-execution-policy-re-evaluation`, File 06 §10] handles it per the capability's declared cancellation+partial-output semantics [`capability.execution-semantic-fields`, File 05 §3.6]. The surface change does not affect already-in-flight execution; new invocations after the transition fail at the call pipeline's resolve-capability step.
### 17.4 Source Loss
If an MCP server/plugin/external-API source disconnects entirely, all its capabilities transition to `Unavailable` in one batch; the algorithm renders them all `Unavailable`; the model receives a typed notice ("Source X disconnected; N capabilities unavailable"); the user inspector shows the source as disconnected with reconnection actions.
### 17.5 Permanent Disablement Is Event-Driven
A capability transitions from `Unavailable` to `Disabled` only through explicit state events: plugin uninstall, MCP server configuration removal, external-API definition deletion, capability unregistration, user disable, policy disablement, or platform conditioning making it permanently inactive for the current installation. No clock or settled-period rule decides this. Long-stale unavailable sources may produce cleanup recommendations in later UI/maintenance specs, but those are not correctness conditions.
### 17.6 Boundary
Surface degradation is the projection layer's response to underlying state changes; actual handling of failed invocations/retry logic/recovery strategies owned by [`run.error-handling`, File 04 §20] + the provider layer for provider-side failures.

## 18. Settings `surface.settings`
### 18.1 Configurable Dimensions
Every surface mechanism configurable through settings [File 15]; File 07 consumes a resolved settings snapshot; profiles contribute active profile layers (not capability registries, security principals, or separate surface-state stores). File 07 names the dimensions + the layer that owns each resolution; cross-scope precedence/profile layers/imports/exports/locality/agent exposure belong to File 15; File 07 owns how an already-resolved surface setting affects composition. Dimensions:
- `surface.zone_override.<capability_id>` — explicit per-capability zone assignment (`primary` | `borrowable` | `deferred` | `disabled` | `default`)
- `surface.zone_family_override.<family>` — per-family zone preference
- `surface.zone_source_override.<source_id>` — per-source zone preference (e.g. demote all MCP server X's tools to `Borrowable`)
- `surface.always_load.<capability_id>` — pin to `Primary` regardless of subsystem spec; auto-shrink does not demote
- `surface.never_load.<capability_id>` — always `Disabled` for `ModelAgent` lens
- `surface.never_show_in_palette.<capability_id>` — hidden from `Palette` lens
- `surface.lens_visibility.<lens>.<capability_id>` — per-lens visibility override
- `surface.shortcut_binding.<capability_id>` — user-bound shortcut (overrides `default_shortcut`)
- `surface.budget_token_count` — tool-surface token budget; default a percentage of the model's context window
- `surface.borrowable_cap_count` — max `Borrowable` entries
- `surface.auto_shrink_enabled` — whether auto-shrink runs
- `surface.shrink_priority.<capability_id>` — per-capability shrink priority override
- `surface.default_deferred_visible_in_palette` — show `Deferred` entries in palette
- `surface.unavailable_visible_in_palette` — show `Unavailable` entries in palette
- `surface.policy_blocked_visible` — show capabilities currently blocked by policy
- `surface.borrow_grant_default_scope` — default scope for `tool.borrow` (typically `run`)
- `surface.cross_surface_borrow_enabled` — whether the model can borrow capabilities outside the active spec (default true; some safety-conscious workspaces may disable)
- `surface.discovery_capabilities_zone` — zone for `tool.borrow`, `tool.search`, `mcp.search`, `tool.inspect` (default `Primary`)
- `surface.mcp_default_zone` — default zone for newly registered MCP-sourced capabilities (default `Borrowable`)
- `surface.plugin_default_zone` — default zone for newly registered plugin-sourced capabilities (default `Borrowable`)
- `surface.model_request_order_strategy` — `cache_friendly` (default; preserves request prefix where supported) | `alphabetical` | `frequency_based`
- `surface.lens_filter_strictness` — `strict` | `permissive`
- `surface.trust_narrowing_active` — whether trust narrowing affects zone or only inspector flags
- `surface.composition_diagnostic_verbosity` — what diagnostics are recorded per composition (default minimal; verbose for debugging)
- `surface.mutation_event_emit_level` — which surface-relevant events emit (default all consequential events; user can suppress noisy ones like every recomposition under heavy churn)
- `surface.snapshot_in_ledger` — whether every composed surface snapshot is recorded in the ledger (default major snapshots only — those consumed by a model turn or persisted by grant/policy state)
### 18.2 Settings-Key Convention
Surface-related settings use the namespaced dotted-key convention `surface.<dimension>.<scope_or_id>` [`capability.settings-key-convention`, File 05 §18.2]. Plugin and MCP-source-supplied capabilities register their own settings keys at registration time, namespaced under the source identity (e.g. `surface.zone_source_override.mcp.linear_server`).
### 18.3 Agent Exposure of Surface Settings
Per [`policy.agent-exposure-policy-settings`, File 06 §16.4] + canonical settings agent-exposure rules [`core.settings-system`, File 01 §6.8]:
- `surface.zone_override.*`, `surface.always_load.*`, `surface.never_load.*` — `OnRequest` (agent reads on request through the canonical read-only settings capability; never writes)
- `surface.budget_token_count`, `surface.auto_shrink_enabled` — `OnRequest`
- `surface.shortcut_binding.*` — `Hidden` (agent never sees user shortcut bindings; UI concern)
- The active `SubsystemSurfaceSpec` + resolved zone assignments for the current run — `InModelRequest` (the request already includes the surface, so the agent knows by inspection)
### 18.4 Settings Changes Are Surface-Relevant Events
A settings change affecting composition emits `SurfaceSettingsChanged` (§13); affected compositions invalidate their cache and recompose on next read; for an active `Run`, the next model turn sees the new surface.
### 18.5 Boundary
File 07 names the settings dimensions; settings storage/validation/resolution/profile layers/agent exposure owned by File 15; File 07 specifies which dimensions are surface-relevant + how they compose into a `ResolvedToolSurface`.

## 19. Explicit Rejections `surface.explicit-rejections`
Wrong for this layer:
- a parallel registry per invocation lens — one registry; surfaces are projections, never alternate registries
- a per-lens capability declaration — one `CapabilityDeclaration` per File 05; per-lens variation lives in display tags+composition-time filters, never in declarations
- silent autoload of cross-surface capabilities into a primary surface's `Primary` zone — capabilities outside the active spec are reachable through `tool.search`/`tool.borrow` only, never hidden auto-promotion
- zone membership as a stored field on the declaration — zone is computed; storing it would force registration churn on every zone-affecting change
- a separate "tool surface state" mutable record per active run — surface state is computed; the ledger records consumed surfaces, but no independent mutable per-run surface table exists
- treating tool-surface visibility as a security gate — visibility is presentation; authority is policy [File 06]; a visible capability may be denied at invocation, an invisible capability may be invoked through the palette
- routing-driven surface visibility changes that bypass policy — `borrow_foreign_capabilities`/`load_deferred_capabilities` may promote capabilities but may not lower the floor; trust narrowing+`permission_floor` still apply
- auto-shrink that requires user approval — deterministic, in-band, recorded; requiring approval per shrink would make it too disruptive
- auto-shrink that silently drops capabilities without diagnostic record — every shrink recorded; the user can inspect what was shrunk and why
- a "tool surface" object with independent durable state diverging from the registry — surface state is computed from registry + settings + `BorrowGrant`s + world state; durability lives in those sources
- per-subsystem capability registries — capabilities registered globally; subsystem surface defaults are a presentation layer over the global registry
- silent visibility differences across lenses — every lens-filter exclusion recorded in `composition_diagnostics`
- ordering tool definitions in the request by anything other than the cache-friendly canonical order without explicit user opt-in — cache hit rate is load-bearing for cost; reordering by frequency/recency every turn would waste cached tokens where provider caching is available
- treating MCP-sourced capabilities as a parallel system — they enter the same registry through the same contract [`capability.sourcing-equivalence`, File 05 §9.3]; the composition does not branch on source kind in core logic
- treating plugin tools, user-defined tools, or external-API tools as parallel systems — same as MCP; all enter through the unified contract
- forcing the model to use a specific tool when composition produces an empty primary surface — `tool_choice: required` against an empty surface fails with a typed error; routing handles the degradation, not the algorithm
- denying the model the ability to discover capabilities that exist in the registry — `tool.search`/`mcp.search` are first-class registered capabilities; their presence in `Primary` is the default; user customization can demote but not remove them from the registry
- composition that depends on time — composition consumes registry snapshot id, settings snapshot id, `BorrowGrant` snapshot id, policy snapshot id, world snapshot id; same inputs always produce same output; no implicit clock-based effects
- baking per-provider tool-call format into the canonical surface — the canonical `ResolvedToolSurface` is provider-agnostic; per-provider rendering is the provider adapter's concern
- unrecorded provider-side tool renaming — provider adapters may produce provider-safe names, but every provider-visible name must map back to canonical capability identity through `provider_name_map`
- treating external tool descriptions/schemas/MCP prompts/plugin metadata/user-defined capability text as instructions — they are untrusted data rendered inside explicit boundaries
- collapsing `Borrowable` and `Deferred` into one zone — the cost gradient (full schema vs name+description vs hidden) is the load-bearing distinction; collapsing removes model-request budget control
- hardcoding any of the dimensions in §18 instead of exposing them as settings — every variation a user might want must be a settings dimension at the right scope
- a special-case surface lens for "trusted users" or "developer mode" — lens distinctions are typed+stable; trust is a policy concern affecting zone assignment, not a separate lens
- mid-run surface-relevant input changes or consumed compositions that do not emit events — every consequential change is observable; silent surface changes corrupt the audit trail+confuse the model
- using auto-shrink as a hidden quota gate — auto-shrink is a token-budget mechanism, not a policy mechanism; capabilities removed by shrink are still policy-authorized to invoke through borrow

## 20. Consequences for Later Specs `surface.consequences-for-later-specs`
Every later spec touching capability presentation/loading/discovery/automation/runtime/UI/storage/sync/telemetry/evaluation consumes the `ToolSurface` projection as defined here. Canonical principles:
- consume `ToolSurface` as a projection of the registry; never invent a parallel registry, parallel surface state model, or write directly to per-lens storage; if a later spec wants surface-relevant changes, it emits the canonical events from §13
- consume the `SubsystemSurfaceSpec` contract — every per-surface/substrate-service spec owning capabilities declares its spec to the shape this file defines (`primary_capability_ids`, `borrowable_capability_ids`, `default_deferred_families`, `forbidden_capability_ids`, `spawnable_subagent_types`, `surface_settings_namespace`, `availability_predicate`); the per-surface specs (Work Surface Contract, Coder, Web, Data Processor, Teacher, GUI Control, System Agent, + the Memory substrate-service spec) fill the contract
- consume the zone model (`Primary`, `Borrowable`, `Deferred`, `Disabled`, `Unavailable`) as the closed set; never introduce a sixth zone; per-subsystem specs may declare which capabilities go into which zone but may not extend the zone vocabulary
- consume the late-loading capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) as the canonical mechanism for agent-initiated surface visibility changes; never introduce a parallel borrow API; a specialized borrow flow declares a capability that wraps the canonical primitives
- consume the composition algorithm (§9) as the single deterministic path; never write a parallel composition; surface-relevant inputs are added as canonical inputs through the settings/routing contracts
- consume the surface-relevant event vocabulary (§13) as the canonical event set; never introduce parallel surface events; new event kinds register through the canonical event bus [`run.ledger-events-commits`, File 04 §23] with the standard envelope
- consume the lens-filter discipline — capabilities declare which invocation paths they support through tags (`agent-invokable`, `palette-invokable`, `voice-invokable`, `automation-trigger`, `external-exposed`) [`capability.display-fields`, File 05 §3.2]; new invocation paths register new lens kinds through the canonical extension mechanism [`core.extension-planes`, File 01 §6.14]
- consume the surface-vs-policy boundary (§10) — File 07 surfaces never grant invocation authority; invocations always pass through File 06 policy; surface composition records visibility decisions, the policy layer records authority decisions, both flow through the ledger
- consume the auto-shrink mechanic (§8) as a deterministic, non-destructive, always-recorded token-budget mechanism; later specs may extend the priority order through the canonical settings dimension but may not introduce hidden shrink mechanisms
- consume the persistence contract (§14) — `ToolSurface` is computed; durable state lives in the registry, settings, `BorrowGrant` records, consumed surface snapshots; no parallel durable surface store
- consume the discovery-capabilities ledger discipline — every `tool.borrow`, `tool.search`, `mcp.search`, `tool.inspect` is recorded; later specs performing discovery-like operations declare new capabilities through the canonical mechanism rather than bypassing the ledger
- File 13 consumes the rendered `Primary`+`Borrowable` outputs as part of the request; does not invent its own surface; places the surface in the canonical request position (§11.1) and applies cache markers as appropriate
- the future Storage and Persistence spec stores `BorrowGrant`s, settings, ledger entries, consumed surface snapshots per the contracts here; no parallel durability paths
- File 15 implements settings resolution, profile contexts, profile layers, locality, agent exposure for the dimensions in §18; does not redefine them
- the future Extension and Plugin System spec + MCP and External Integrations spec hand their registered capabilities through the unified registry [`capability.sourcing`, File 05 §9]; the composition picks them up automatically
- the future Workspaces and Materialization spec defines workspace boundaries; composition consumes workspace_id from `scope_context`; workspace switching emits the appropriate `SurfaceSettingsChanged` event
- the future per-surface specs (Coder, Web, Teacher, Data Processor, GUI Control, System Agent) + File 14 for Memory declare their `SubsystemSurfaceSpec` and any specialized discovery capabilities or specialized auto-shrink priorities
- the future Automation and Triggers spec consumes the `AutomationTrigger` lens through the canonical contract; pins surface strategies at save time through the same `tool_surface_strategy` field as runtime routing
- the future Workflows, Templates, and Reuse spec composes capabilities through the unified registry; workflow nodes reference capability ids; composition for a workflow execution honors the workflow's declared capability list as an additional input
- the future UI Shell, Layout, Presentation, and Interaction Models spec renders the `Palette`, `Inspector`, `Voice`, `Shortcut`, `AutomationTrigger` lens data into UI; File 07 hands them the canonical data contract
- the future UI Customization, Widgets, and Theming spec renders the surface inspector + per-capability settings views; the data contract is what File 07 specifies
- the future Quality Control and Validation spec may consume the surface for static analysis (capability availability checks, lens consistency checks, shortcut conflict detection) through the canonical inspector lens
- the future Evaluation and Benchmarking spec consumes the surface snapshot recorded in the ledger to evaluate tool-use efficiency; replay reconstructs the exact surface a past invocation saw
- the future Telemetry, Logging, and Observability spec captures surface-relevant events for monitoring; consumes the canonical event vocabulary
- the future Runtime Infrastructure and Lifecycle spec implements the composition algorithm with deterministic semantics; File 07 specifies the contract, the runtime realizes it
- the future Packaging, Platform, and Distribution spec packages built-in `Capability` declarations incl. the canonical discovery capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`); they ship in every ATLAS3 install as the `Builtin` source
Specific integration contracts stated in those files when written; until then, the canonical contract here is the load-bearing reference.
