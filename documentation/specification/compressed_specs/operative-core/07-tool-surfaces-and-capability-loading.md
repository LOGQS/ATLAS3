# Tool Surfaces and Capability Loading

## 1. Chosen Model {surface.chosen-model}
- One Capability Registry. The set an invoker sees at a moment is a `ToolSurface`.
- A `ToolSurface` is a typed projection over the registry, not a second registry; a presentation surface, not a security gate.
- `ToolSurface` is the canonical noun; earlier names ("tool list", "tool catalog", "action palette", etc.) do not survive as parallel primitives.

## 2. `ToolSurface` {surface.tool-surface}
### 2.1 Definition
- Computed, not stored as an independent mutable record; every render runs the composition algorithm (§9) producing a `ResolvedToolSurface`.
### 2.2 Invokers and Surface Kinds
- Always typed with `invoker_kind` + `invocation_lens`. Canonical invoker kinds: `ModelAgent`, `ProgrammaticUnit`, `Palette`, `Voice`, `Shortcut`, `AutomationTrigger`, `ExternalMcp`, `Inspector`.
### 2.3 Required Outputs {surface.required-outputs}
- `ResolvedToolSurface` carries at minimum: `surface_id`, `invoker_kind`, `invocation_lens`, `scope_context`, `zoned_entries` (`primary`, `borrowable`, `deferred`, `disabled`, `unavailable`), `routing_inputs`, `provider_name_map`, `context_budget`, `auto_shrink_record`, `composition_diagnostics`.
- `auto_shrink_record.cache_impact` one of: `none`, `preserved_prefix`, `changed_tool_surface_only`, `changed_instruction_or_region_order`, `full_cache_break_likely`.
- Every `ResolvedToolSurface` must be recorded as a surface snapshot in the execution ledger when consumed by an invoker.
### 2.4 Boundary

## 3. The Zone Model {surface.zone-model}
### 3.1 Canonical Zones (5, closed)
- `Primary`, `Borrowable`, `Deferred`, `Disabled`, `Unavailable`.
- Zone set is closed; adding a sixth zone is an Explicit Rejection.
- `Unavailable` must never be present in `ModelAgent`/`ProgrammaticUnit` surfaces.
### 3.2 Zone Semantics for `ModelAgent`
- `Primary` → provider-native callable declarations; `Borrowable` → model-request text content with `tool.borrow` note; `Deferred` → not in the model request; `Disabled`/`Unavailable` → not visible.
### 3.3 Zone Semantics for `Palette`, `Voice`, `Shortcut`, `AutomationTrigger`
- User invocation through palette/voice/shortcut is direct; File 06 policy applies the same way.
### 3.4 Zone Semantics for `ExternalMcp`
- Visible only if tagged for external exposure AND source-approval permits.
### 3.5 Zone Membership is Computed
- A declaration carries no zone field; composition is deterministic given the same inputs.
### 3.6 Zones Are Not Authority
- Zone controls visibility, not invocation authority; `tool.borrow` requires `ReadOnly` tier; the borrowed capability's own tier still applies.

## 4. Loading Semantics {surface.loading-semantics}
### 4.1 What "Loaded" Means
### 4.2 Model-Request Rendering for `Primary`
- Rendered fields: `name`, `description`, `input_schema`, `error_vocabulary` summary, inline display hints.
### 4.3 Model-Request Rendering for `Borrowable`
- Rendered after `Primary` declarations and before conversation history; per-entry one-liner `name` + `short_description`; `borrow_invocation_hint`.
- Deterministically ordered (alphabetical by family, then by name within family).
### 4.4 The Borrow Operation
1. Capability resolved+validated.
2. Policy evaluates `tool.borrow` (`ReadOnly`).
3. The borrowed capability resolved against the registry; if not found, returns a typed error in-band.
4. If borrowable, executor records a `BorrowGrant` and returns the full schema.
5. Next composition renders the borrowed capability in `Primary`.
6. `CapabilityBorrowed` event emitted.
### 4.5 Loading Across Turns
- Default grant scope for `tool.borrow` is `run`; `tool.borrow_persistent` requires `UserApproval`.
### 4.6 Late Schema Loading for MCP-Sourced Capabilities
- MCP server disconnect must invalidate the cache and transition to `availability_status: unavailable_handler`.
### 4.7 Boundary

## 5. Subsystem Surface Defaults: `SubsystemSurfaceSpec` {surface.subsystem-surface-spec}
### 5.1 Required Shape
- Carries: `subsystem_id`, `display_name`, `primary_capability_ids`, `borrowable_capability_ids`, `default_deferred_families`, `forbidden_capability_ids`, `spawnable_subagent_types`, `surface_settings_namespace`, `availability_predicate`.
### 5.2 Capabilities Outside the Spec
- A capability not in the spec is `Deferred` for the `ModelAgent` lens.
### 5.3 Routing-Time Strategy Selection
- `tool_surface_strategy` one of: `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`.
### 5.4 Primary Surface Changes {surface.primary-surface-changes}
- Emits `PrimarySurfaceChanged`.
### 5.5 Cross-Surface Reach Without Primary-Surface Change
### 5.6 Boundary

## 6. Routing Influence {surface.routing-influence}
### 6.1 Consumed Inputs
- `RunIntent.primary_surface`, `supporting_surfaces`, `capability_families`, `tool_surface_strategy`, `model_route.resolved_model_id`, `execution_entry`, `routing_metadata`.
### 6.2 Routing-Time Pinning
### 6.3 Routing Inputs Are Inspectable
### 6.4 Routing Does Not Override Floors
- A capability whose `permission_floor` makes it `Denied` cannot be promoted; the algorithm clamps to `Disabled` for the `ModelAgent` lens.
### 6.5 Boundary

## 7. Late-Loading and Runtime Discovery {surface.late-loading-runtime-discovery}
### 7.1 Built-in Discovery Capabilities (5)
- `tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`.
- First-class registered capabilities; appear in every default spec's `primary_capability_ids` by convention.
### 7.2 Declarations
- `tool.borrow`: `permission_tier` `ReadOnly`; `concurrency` `ConcurrencySafe`; `replay_class` `deterministic_replayable`; `idempotent` true; `preview_mode` `none`.
- `tool.borrow_persistent(capability_id, scope)`: `permission_tier` `UserApproval`.
- `tool.search(query, family, source, top_k)`: `ReadOnly`; `ConcurrencySafe`; `deterministic_replayable`.
- `mcp.search(query, server_id, top_k)`: filtered to MCP-sourced.
- `tool.inspect(capability_id)`: `ReadOnly`; `ConcurrencySafe`; `deterministic_replayable`; must never change zone membership or make the capability callable.
- Canonical ids are stable.
### 7.3 `BorrowGrant` {surface.borrow-grant}
- A File 07-owned `BorrowGrant`, not a File 06 approval `Lease`; never authorizes execution.
- Carries: `capability_match`, `scope`, `invoker_kind`, `schema_visible`, `grant_origin` (`tool_borrow_call`), `revocation_conditions`.
### 7.4 Search Results
- A `Disabled`/`Unavailable`/forbidden capability returns `borrow_eligibility: denied` with the typed reason.
### 7.5 Discovery Is Auditable
- Every `tool.search`, `mcp.search`, `tool.borrow`, `tool.borrow_persistent`, `tool.inspect` call must be recorded in the ledger.
### 7.6 Boundary

## 8. Default Composition and Auto-Shrink {surface.default-composition-auto-shrink}
### 8.1 Default Composition (fresh `Run`)
1. Resolve the active `SubsystemSurfaceSpec` from `RunIntent.primary_surface`.
2. Place every `primary_capability_ids` entry in `Primary`.
3. Place every `borrowable_capability_ids` entry in `Borrowable`.
4. Place every capability whose family is in `default_deferred_families` into `Deferred`.
5. Exclude every capability in `forbidden_capability_ids` from any zone except the inspector.
6. Promote `supporting_surfaces` `primary_capability_ids` into `Borrowable`.
7. Apply `tool_surface_strategy` adjustments.
8. Apply the resolved settings snapshot.
9. Apply active `BorrowGrant`s.
10. Evaluate `enabled` flag — disabled move to `Disabled`.
11. Evaluate availability — non-`Available` move to `Unavailable`.
12. Apply trust narrowing.
13. Estimate model-request cost.
14. If cost exceeds budget, run auto-shrink.
15. If legal shrink cannot fit, return `ToolSurfaceOverflow`.
16. Render `composition_diagnostics`.
17. Emit `ToolSurfaceComposed` event.
### 8.2 Auto-Shrink Algorithm {surface.auto-shrink-algorithm}
- **Step A** — drop already-deferred entries from the `Borrowable` catalog block.
- **Step B** — demote `Borrowable` entries beyond `borrowable_cap` to `Deferred`.
- **Step C** — abbreviate `Borrowable` catalog block (remove family headers/annotations).
- **Step D** — demote `Primary` entries tagged `experimental`/`low-frequency`/`auto_shrink_eligible` to `Borrowable`.
- **Step E** — demote `Primary` entries by declared priority.
- **Step F** — emit a typed warning to the user surface + next model request.
- Auto-shrink must never move anything pinned by the user; must never demote the discovery capabilities below `Borrowable`; must record every demotion in `auto_shrink_record`.
- If pinned `Primary` entries still exceed the limit, composition must return `ToolSurfaceOverflow`.
### 8.3 Auto-Shrink is Non-Destructive and Always In-Band {surface.auto-shrink-non-destructive}
- Does not require user approval; runs deterministically; reversible; achieved `cache_impact` must be recorded.
### 8.4 Shrink Does Not Affect User-Facing Surfaces
### 8.5 Boundary

## 9. Visibility Composition Resolution Algorithm {surface.visibility-composition-resolution-algorithm}
### 9.1 Algorithm (17 steps)
`compose_surface(invoker_kind, invocation_lens, scope_context) -> ResolvedToolSurface`
1. Resolve the active `SubsystemSurfaceSpec` from `primary_surface_id`.
2. Snapshot the registry (Inspector compositions include disabled and unavailable entries).
3. For each registered capability compute `base_zone`: (a) in `forbidden_capability_ids` → excluded (Inspector only); (b) in `primary_capability_ids` → Primary; (c) in `borrowable_capability_ids` → Borrowable; (d) family in `default_deferred_families` → Deferred; (e) else → Deferred.
4. Apply supporting-surface promotion (each supporting spec's `primary_capability_ids` → Borrowable).
5. Apply `tool_surface_strategy` (`use_current_surface_tools` no change; `borrow_foreign_capabilities` promote `foreign_caps` to Borrowable; `load_deferred_capabilities` promote `deferred_caps` to Primary).
6. Apply the resolved settings snapshot (per-capability/per-family/per-source zone overrides; always-load → Primary; never-load → Disabled; never-show → hide from palette).
7. Apply active `BorrowGrant`s (promote to Primary for grant duration).
8. Evaluate enabled state (disabled at any active scope → Disabled).
9. Evaluate per-capability availability (`availability_status` != Available → Unavailable; `availability_predicate` fails → Unavailable; unsatisfied `prerequisite_capabilities` → Unavailable with `prerequisite_unsatisfied`).
10. Apply trust narrowing (for `Community`/`Unverified`/`Sideloaded`; may demote or flag).
11. Apply floor enforcement (resolve effective tier; if `permission_floor` is Denied with no typed-confirmation override → clamp to Disabled for ModelAgent lens; remains visible in palette and inspector).
12. Filter by invocation lens (ModelAgent: `agent-invokable`; Palette: `palette-invokable`; Voice: `voice-invokable`; Shortcut: has shortcut; AutomationTrigger: `automation-trigger`; ExternalMcp: `external-exposed` AND source-approval permits; Inspector: no filter; filtered-out → Disabled for this lens with `lens_filter_excluded`).
13. Estimate model-request cost (ModelAgent lens only).
14. Apply auto-shrink if estimated cost > `tool_surface_budget` (record every demotion in `auto_shrink_record`).
15. If legal shrink cannot fit, return `ToolSurfaceOverflow` with pinned entries, estimated size, active limit, recovery options.
16. Produce `ResolvedToolSurface` (`surface_id` = stable hash over inputs; `zoned_entries`; `provider_name_map`; `composition_diagnostics`; `auto_shrink_record`).
17. Emit `ToolSurfaceComposed` event with `surface_id` and diagnostic facts.
### 9.2 Determinism
- Two compositions with the same inputs must produce byte-identical `ResolvedToolSurface` and rendered model-request surface content.
### 9.3 Caching
- Invalidation must be event-driven, not time-based.
### 9.4 Algorithm Settings
- `auto_shrink_enabled`, `tool_surface_budget_token_count`, `borrowable_cap_count`, `lens_filter_strictness` (`strict`/`permissive`), `trust_narrowing_active`, `forbidden_visible_in_palette`, `unavailable_visible_in_palette`, `default_deferred_visible_in_palette`.
### 9.5 Boundary

## 10. Tool Surface and Capability Policy {surface.tool-surface-capability-policy}
### 10.1 Boundary
- Surface controls visibility; Policy controls authority. A capability can be visible without being permitted, and permitted without being visible.
### 10.2 Visibility Customization Honors Policy
### 10.3 Source-Approval Affects Surface
- Until source-approval completes, the source's capabilities must be in `Disabled` for all invokers.
### 10.4 Policy Events Inform the Surface
### 10.5 Boundary
- File 07 must not duplicate policy state or implement approval evaluation.

## 11. Presentation in the Model Request {surface.presentation-in-model-request}
### 11.1 Position in the Model Request
- After identity+core-instructions; before conversation history+current user message; `Primary` first, `Borrowable` catalog next, optional `auto_shrink_record` notice, discovery capabilities alongside `Primary`.
### 11.2 Per-Provider Format Normalization
- The provider adapter records `provider_name_map` for any provider-visible renaming.
### 11.3 Tool Metadata Is Data, Not Instruction
- Capability descriptions/schemas/MCP/plugin/external-API/user-defined text are untrusted data; they do not gain instruction authority.
- External/source-authored descriptions must have source attribution, length limits, explicit instruction-boundary markers; placed inside a delineated data section; the boundary is architectural, not textual filtering.
### 11.4 Borrowable Catalog Block Format
- Single text block, alphabetized by family then name.
### 11.5 Deferred Capabilities Are Not in the Model Request
### 11.6 Empty Surface Handling
- `tool_choice` semantics: `none`, `auto`, `required` (required against zero Primary fails with `EmptyToolSurfaceWithRequiredChoice`).
### 11.7 Cache-Friendly Ordering {surface.cache-friendly-ordering}
1. Discovery capabilities first.
2. Active spec `primary_capability_ids` in declared order.
3. `supporting_surfaces`-promoted capabilities.
4. `tool_surface_strategy`-promoted capabilities.
5. `BorrowGrant`-promoted capabilities in grant order.
### 11.8 Boundary

## 12. Presentation in User-Facing Surfaces {surface.presentation-in-user-facing-surfaces}
### 12.1 Palette Lens
### 12.2 Voice Lens
### 12.3 Shortcut Lens
- Conflicts detected at registration time produce `ShortcutConflict`; the registry rejects the second registration unless explicitly overridden.
### 12.4 Inspector Lens {surface.inspector-lens}
- Shows the full registry catalog with no filtering, every zone including `Disabled`, `Unavailable`, `Forbidden`.
### 12.5 Automation Trigger Lens
### 12.6 External MCP Lens
- Gated by source-approval; capabilities not approved for external exposure are filtered out.
### 12.7 Per-Lens Visibility Rules
### 12.8 Boundary

## 13. Surface-Relevant Events {surface.surface-relevant-events}
### 13.1 Event Vocabulary (16)
- `ToolSurfaceComposed`, `CapabilityBorrowed`, `CapabilityBorrowReturned`, `CapabilityZoneChanged`, `CapabilityRegistered`, `CapabilityUnregistered`, `CapabilityEnabledChanged`, `CapabilityAvailabilityChanged`, `ToolSurfaceShrunk`, `ToolSurfaceOverflow`, `SubsystemSurfaceSpecUpdated`, `PrimarySurfaceChanged`, `SurfaceSettingsChanged`, `SourceConnected`, `SourceDisconnected`, `LensFilterChanged`, `ShortcutConflict`.
- Every surface-relevant change must emit a typed event with the standard envelope (`conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`).
### 13.2 Event Sensitivity
- Events naming raw secrets are `Secret` and must never be persisted to the durable ledger.
### 13.3 Event Consumers
### 13.4 Mid-Run Change Notification to the Model
- Mid-run surface changes must be visible to the model.
### 13.5 Event Stream Versus Durable Ledger
### 13.6 Boundary

## 14. Persistence and Reconstruction {surface.persistence-reconstruction}
### 14.1 What Persists Durably
- Durable: the registry, per-scope settings, `BorrowGrant`s, the execution ledger.
- Not persisted as independent state: `ResolvedToolSurface`, per-turn rendered model requests.
### 14.2 Reconstruction Across Restart {surface.reconstruction-across-restart}
1. The registry re-registers its capabilities.
2. The settings system reloads per-scope settings.
3. The `BorrowGrant` store reloads durable grants.
4. Capability availability re-evaluated.
5. Source connections re-establish.
6. Runs active at restart follow orphan-run rules; their surfaces are not auto-resumed.
7. New runs compose fresh surfaces.
### 14.3 Reconstruction Across Retry, Edit, Reroute, Branch {surface.reconstruction-across-retry-edit-reroute-branch}
- Run-scoped `BorrowGrant`s must not transfer across retry/edit/reroute/branch.
### 14.4 Reconstruction in Child Runs
- The child's surface must be constrained by its declared `tool_allowlist` as an additional step at the end of step 12.
### 14.5 Reconstruction in Edit-Reroute
### 14.6 Boundary

## 15. MCP and Plugin Tool Integration {surface.mcp-plugin-tool-integration}
### 15.1 Sourced Capabilities Enter the Single Registry
- No parallel "MCP tool list"/"plugin tool catalog"; one registry, source is metadata.
### 15.2 MCP Server Lifecycle and the Surface
- Reconnection must preserve identity.
### 15.3 Plugin Lifecycle and the Surface
### 15.4 Large MCP Registries
### 15.5 Source-Approval Affects Initial Zone
- `AcceptDefaults` → declared default zones; `CustomizePerCapability`; `CustomizePerSource`; `DenyOutright` → `Disabled`; `DeferSourcePolicy` → `Unavailable`.
### 15.6 External APIs and User-Defined Capabilities
### 15.7 Boundary

## 16. Tool-Choice Mechanics {surface.tool-choice-mechanics}
### 16.1 `tool_choice` Settings
- `auto`, `none`, `required`, `specific_tool(id)`.
### 16.2 Empty Surface Handling
- `required` against zero Primary fails with `EmptyToolSurfaceWithRequiredChoice`.
### 16.3 Forced Tool Choice
- `specific_tool(id)` promotes the named capability to `Primary` subject to `enabled`, `Available`, not forbidden, effective tier not `Denied`; otherwise returns `ForcedToolChoiceUnavailable`.
### 16.4 Boundary

## 17. Degradation and Graceful Absence {surface.degradation-graceful-absence}
### 17.1 Availability Transitions Mid-Active
- Every transition emits `CapabilityAvailabilityChanged`.
### 17.2 Capability Becomes Available Mid-Run
### 17.3 In-Flight Calls
- The surface change must not affect already-in-flight execution.
### 17.4 Source Loss
### 17.5 Permanent Disablement Is Event-Driven
- A capability transitions `Unavailable` → `Disabled` only through explicit state events; no clock or settled-period rule decides this.
### 17.6 Boundary

## 18. Settings {surface.settings}
### 18.1 Configurable Dimensions
- `surface.zone_override.<capability_id>`, `surface.zone_family_override.<family>`, `surface.zone_source_override.<source_id>`, `surface.always_load.<capability_id>`, `surface.never_load.<capability_id>`, `surface.never_show_in_palette.<capability_id>`, `surface.lens_visibility.<lens>.<capability_id>`, `surface.shortcut_binding.<capability_id>`, `surface.budget_token_count`, `surface.borrowable_cap_count`, `surface.auto_shrink_enabled`, `surface.shrink_priority.<capability_id>`, `surface.default_deferred_visible_in_palette`, `surface.unavailable_visible_in_palette`, `surface.policy_blocked_visible`, `surface.borrow_grant_default_scope`, `surface.cross_surface_borrow_enabled`, `surface.discovery_capabilities_zone`, `surface.mcp_default_zone`, `surface.plugin_default_zone`, `surface.model_request_order_strategy` (`cache_friendly`/`alphabetical`/`frequency_based`), `surface.lens_filter_strictness`, `surface.trust_narrowing_active`, `surface.composition_diagnostic_verbosity`, `surface.mutation_event_emit_level`, `surface.snapshot_in_ledger`.
### 18.2 Settings-Key Convention
- Namespaced dotted-key convention `surface.<dimension>.<scope_or_id>`.
### 18.3 Agent Exposure of Surface Settings
- `surface.zone_override.*`, `surface.always_load.*`, `surface.never_load.*`, `surface.budget_token_count`, `surface.auto_shrink_enabled` — `OnRequest`.
- `surface.shortcut_binding.*` — `Hidden`.
- active `SubsystemSurfaceSpec` + resolved zone assignments — `InModelRequest`.
### 18.4 Settings Changes Are Surface-Relevant Events
- Emits `SurfaceSettingsChanged`.
### 18.5 Boundary

## 19. Explicit Rejections {surface.explicit-rejections}
- a parallel registry per invocation lens
- a per-lens capability declaration
- silent autoload of cross-surface capabilities into a primary surface's `Primary` zone
- zone membership as a stored field on the declaration
- a separate "tool surface state" mutable record per active run
- treating tool-surface visibility as a security gate
- routing-driven surface visibility changes that bypass policy
- auto-shrink that requires user approval
- auto-shrink that silently drops capabilities without diagnostic record
- a "tool surface" object with independent durable state diverging from the registry
- per-subsystem capability registries
- silent visibility differences across lenses
- ordering tool definitions by anything other than cache-friendly canonical order without explicit user opt-in
- treating MCP-sourced capabilities as a parallel system
- treating plugin/user-defined/external-API tools as parallel systems
- forcing the model to use a specific tool when composition produces an empty primary surface
- denying the model the ability to discover capabilities that exist in the registry
- composition that depends on time
- baking per-provider tool-call format into the canonical surface
- unrecorded provider-side tool renaming
- treating external tool descriptions/schemas/MCP prompts/plugin metadata/user-defined text as instructions
- collapsing `Borrowable` and `Deferred` into one zone
- hardcoding any §18 dimension instead of exposing it as settings
- a special-case surface lens for "trusted users" or "developer mode"
- mid-run surface-relevant changes or consumed compositions that do not emit events
- using auto-shrink as a hidden quota gate

## 20. Consequences for Later Specs {surface.consequences-for-later-specs}
- consume `ToolSurface` as a projection of the registry; never invent a parallel registry or surface state model.
- consume the `SubsystemSurfaceSpec` contract.
- consume the zone model as the closed set; never introduce a sixth zone.
- consume the late-loading capabilities (`tool.borrow`, `tool.borrow_persistent`, `tool.search`, `mcp.search`, `tool.inspect`) as canonical; never introduce a parallel borrow API.
- consume the composition algorithm (§9) as the single deterministic path.
- consume the surface-relevant event vocabulary (§13) as the canonical event set.
- consume the lens-filter discipline (tags: `agent-invokable`, `palette-invokable`, `voice-invokable`, `automation-trigger`, `external-exposed`).
- consume the surface-vs-policy boundary; File 07 surfaces never grant invocation authority.
- consume the auto-shrink mechanic as deterministic, non-destructive, always-recorded.
- consume the persistence contract; `ToolSurface` is computed.
- consume the discovery-capabilities ledger discipline.
- File 13 consumes the rendered `Primary`+`Borrowable` outputs; places the surface in the canonical request position; applies cache markers.
- the discovery capabilities ship in every install as the `Builtin` source.
