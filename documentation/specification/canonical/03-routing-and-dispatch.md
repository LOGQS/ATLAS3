# Routing and Dispatch

## Status

Canonical.

## Scope

This file defines:

- the routing layer
- dispatch timing
- router inputs
- `RunIntent` as a concrete routing output
- continuity attachment
- fast path
- route visibility and override
- retry and edit rerouting rules

This file does not define:

- run schema
- task schema
- execution graph schema
- approval mechanics
- tool contract schema
- storage schema

## Source Resolution

This file resolves routing, model selection, fast-path, workspace selection, and dispatch material into one boundary: incoming user or system input becomes a RunIntent.

Resolved design:

- Routing is a first-class runtime step, not hidden model-request logic.
- A RunIntent describes the selected work line, execution entry, model route, context policy, and capability surface; it is not merely a surface/subsystem label.
- Router output may include fast-path results or failures, but that work is visible to execution and ledgering.
- Router context is compact, policy-governed, and independently configurable from main-model context.
- Presentation is a user-controllable projection; routing may inform it but does not own frontend participation mode.
- Edits, retries, and mid-execution reroutes create explicit routing transitions rather than silently mutating prior decisions.

## 1. Purpose

Anchor: `routing.purpose`

Routing decides how a new request should enter the runtime.

It does not produce the final answer. It decides:

- what the request belongs to
- what kind of execution should happen
- which capabilities are relevant
- which work surface is primary, if any
- which model strategy to use
- whether trivial or preparatory work can be done immediately

The canonical output of routing is `RunIntent`.

## 2. Routing Is a First-Class Dispatch Step

Anchor: `routing.routing-is-first-class-dispatch-step`

Routing is a first-class dispatch step in request handling.

It is not:

- hidden preprocessing
- optional metadata generation
- only a frontend concern

It must be:

- durably recorded
- linked to its trigger
- inspectable
- replayable
- overrideable by the user

Implementation may realize routing as a dedicated runtime node, a dispatch-layer phase, or an equivalent execution step. That is not the canonical concern of this file.

The canonical concern is that every new run passes through routing before downstream execution begins, regardless of trigger kind, unless the trigger is a pure local UI action that does not ask the system to perform work.

### 2.1 Trigger Kinds and Routing

Anchor: `routing.trigger-kinds-routing`

Routing applies to every trigger kind enumerated in the run spec: user request, retry, edit reroute, continuation, child run, automation, external event, and user-invoked action. The pipeline shape is the same for all trigger kinds; trigger-kind-specific rules govern which fields the trigger pre-fills and which the router still decides.

- automation triggers may pin primary surface, capability families, model route, or the full `RunIntent` at save time; the routing pass respects pinned fields and fills only the unpinned ones
- child-run triggers inherit policy and capability snapshots from the parent run; the child receives its own `RunIntent` that may narrow, pivot, or fully replace the inherited surface and capability selection
- external-event triggers route with the event payload as the routing-frame trigger context
- user-invoked actions (capability palette, shortcut, voice-mapped action) may skip the router model when the action id deterministically resolves the route; the routing record is still created
- retry, edit reroute, and continuation triggers follow §11 and §12

Pre-filling and inheritance constrain routing the same way an explicit user override does (§3.2); they do not bypass it. Per-trigger-kind enablement, pin-through behavior, and inheritance scope are user-configurable through settings (§13).

## 3. Dispatch Pipeline

Anchor: `routing.dispatch-pipeline`

For each new user request, dispatch proceeds in this order:

1. Build the routing frame.
2. Apply deterministic prechecks.
3. Run the router.
4. Materialize `RunIntent`.
5. Optionally execute router-owned fast-path work.
6. Persist the route result and attach it to the request.
7. Hand off to downstream execution.

The seven-step pipeline is the canonical logical contract. Implementations may compose additional steps — extension prechecks, validators, observers, gates — through the actions and events hook architecture (per `run.hook-integration`, File 04 §23.3) without changing the canonical step order or the routing decision contract.

A crash between step 5 and step 6 can leave fast-path ledger entries written with no route record yet persisted and no run adopting them; those entries are a reclaimable orphan, never a live reference, and the crash residue is safe to reclaim.

### 3.1 Routing Frame

Anchor: `routing.routing-frame`

The routing frame is the structured input the routing layer reasons over. It must contain enough state for the router to produce a valid `RunIntent` while staying cheap enough for the active router context policy. File 13 owns assembly of the router's model request; this file owns the meaning of the routing frame and routing result.

The frame inputs are organized into four categories.

**Trigger context**

- the triggering input (user message, automation event payload, external event, child-run request, retry/edit reference, or user-invoked action)
- `trigger_kind` discriminator (per §2.1)
- the active conversation id
- current route override state, if any
- explicit user-specified attachments or inputs

**Work-state context**

- current active intent thread, if any
- current active task, if any
- compact prior routing summaries, previous route records, or selected history when the active router context policy uses them (per §6 and File 13)
- active world model snapshot (active surface, focused element, mounted panels, selection, available capabilities/control affordances, current ui_mode) — resolved from the trigger's `PresentationContext` (`world.surface-state`, File 18 §5.1): an interactive trigger uses its origin renderer root; a noninteractive trigger (automation, child run, CLI, external) uses its typed noninteractive context. Routing never substitutes the attention target or a cross-root aggregate (`ui.shell`, File 37 §4.4)

**Capability-and-policy context**

- currently available capabilities and capability families
- enabled work surfaces
- active approval posture

**Model-and-provider context**

- model-routing settings and available model profiles
- relevant provider capability metadata (modality, tool-call format, streaming support, reasoning support, context window)
- relevant provider rate-limit state and provider health state
- active per-scope budget state (token budgets primarily; cost-ceiling overlay is provider-dependent and may be absent)
- active model fallback policy

The frame should not require raw replay of the full conversation as the fixed default.

The frame is constructed by the active router context policy. The policy is configurable through settings, profiles, and conversation overrides. Whatever the policy, the frame must include enough from each of the four categories above for the router to produce a valid `RunIntent`. For user-request routing, the full current triggering input must be present directly or as a referenced externalized source per File 13.

The canonical default is the `compact` policy: optimized for cheap, cache-friendly routing. It includes the trigger content plus the minimum from each of the four required categories, leaning on stable model-request parts such as capability, model, and surface catalogues where provider caching supports them. The compact policy may include a brief active-intent-thread or active-task summary when one is already maintained as part of work-state context; it does not require dedicated routing summaries (§6). It aims for bounded cost through summaries and policy selection, not by ignoring relevant conversation length.

Richer policies may be selected through settings, profiles, or conversation overrides. Representative policies:

- `compact_with_summaries`: adds compact prior routing summaries (per §6) for stronger work-line continuity
- `recent_blocks`: adds a small selected set of recent transcript blocks
- `pinned_and_referenced`: adds blocks the user has pinned, referenced, or attached
- `expanded_for_ambiguity`: increases the included context when deterministic prechecks (§3.2) signal ambiguity
- custom policies registered by subsystems, plugins, or users

Changing router context policy changes what the router sees. It must not change the meaning of `RunIntent`, bypass durable route recording, omit a category required for a valid `RunIntent`, or make full raw conversation replay the fixed default.

The trigger content consumed by the routing frame may be the result of deterministic pre-routing transformations — duplicate detection, attachment expansion, mention or slash-command macro expansion, or other content normalizations. These transformations are not deterministic prechecks (§3.2): they shape what the router sees, not whether or where the request is dispatched. Each transformation that altered the trigger content must be recorded as part of the route record, including what was detected and what the user override (if any) decided.

### 3.2 Deterministic Prechecks

Anchor: `routing.deterministic-prechecks`

Deterministic prechecks run before the router model. A precheck is any deterministic function over the routing frame that may resolve, constrain, or no-op the routing decision. They exist to avoid wasting model effort on cases that are already clear from runtime state.

When a precheck fully resolves the route, the router model step is skipped. When a precheck constrains or prefills routing (for example, "the request must use the coder primary surface" or "force the explicit-model-override to model X"), the router model receives the constraints and decides only the unconstrained fields. When a precheck no-ops, dispatch continues to the router model unchanged.

Representative precheck patterns:

- explicit user override of route, model, surface, or capability strategy
- retry of an unchanged routed request that preserves the prior route
- explicit "back to X" or equivalent continuity reference
- edit of a prior user message
- exact capability invocation exposed by the UI or palette (the action id deterministically resolves the route)
- active request that is clearly continuing the same work line
- slash commands or other namespace-scoped invocations that map directly to actions or capabilities
- deterministic state-flag routing (e.g., a highlighted code selection unambiguously routes to a code-edit capability)
- cached prior routing decision under identical inputs when the cache key is still valid

Prechecks are ordered. Order and per-precheck enablement are settings; a precheck that resolves the route short-circuits later prechecks in the chain. The mechanism by which capabilities, plugins, subsystems, or user configuration contribute additional prechecks is owned by the capability, settings, and hooks specs, not this file.

### 3.3 Router

The router is typically a model-driven component.

Its job is not to infer the deep true intent of the user. Its job is narrower:

- attach the request to the correct ongoing work line
- choose the appropriate execution entry shape
- select relevant capability and surface targets
- select model strategy
- determine whether fast path is appropriate

Routing must be cheap enough to run on every relevant trigger. Cheapness is a cost ceiling, not a prescribed mechanism: implementations may achieve it through caching stable model-request parts such as capability, model, and surface catalogues, native tool-call emission of the routing decision, substitution of the model-driven router with a local classifier, or any equivalent technique. Any implementation that achieves cheap, durable, replayable routing on every relevant trigger is valid.

### 3.4 Route Application

After the router returns, the runtime:

- creates or updates the primary work-line attachment
- records the route result
- prepares any router-owned fast-path outputs
- initializes downstream execution with the resolved `RunIntent`

### 3.5 Route Record

Anchor: `routing.route-record`

The route result is recorded durably as part of the run record. The record must preserve enough information to:

- reconstruct the routing decision (the resolved `RunIntent` plus `routing_metadata`)
- replay the routing pass against the same inputs
- inspect the decision in the UI
- audit the decision against routing-eval suites

The record references the policy snapshot, capability snapshot, and world snapshot in effect at routing time; snapshot identities live in the storage and version specs. Every precheck that fired (with its verdict) and every pre-routing transformation that altered trigger content (§3.1) must be present in the record.

### 3.6 Routing Failure

Anchor: `routing.routing-failure`

Routing can fail: the router step may error, time out, hit a provider outage, or emit a malformed decision that cannot be materialized into a valid `RunIntent`. Routing failure is a typed outcome — `RoutingFailed` — never a silent drop.

On `RoutingFailed`, dispatch takes one of two deterministic paths, selected by settings (§13):

- safe-default route: the runtime materializes a minimal valid `RunIntent` from the default model profile, a `respond_inline` or `respond_with_tools` execution entry, and — when the routing frame's interactive presentation context names a work surface — that context's root-resolved `active_surface_binding` as `primary_surface` (else no primary surface; `world.surface-state`, File 18 §5.2). `model_route` may be null when no provider could be resolved (§4.3), leaving model selection to downstream fallback.
- surface-to-user: the runtime does not dispatch and surfaces the failure to the user for an explicit decision.

Either way, the `RoutingFailed` outcome is recorded in `routing_metadata` and the route record (§3.5), with enough detail to inspect and replay the failure. A routing failure must not silently discard the route or the request.

## 4. `RunIntent`

Anchor: `routing.run-intent`

### 4.1 Definition

`RunIntent` is the concrete routing result for one request.

It is short-lived as a dispatch object, but its result is durably recorded.

### 4.2 Required Fields

`RunIntent` must include:

- `conversation_id`
- `trigger_kind`
- `trigger_id`
- `parent_run_id`
- `trace_context`
- `primary_intent_thread_id`
- `attachment_kind`
- `primary_surface`
- `supporting_surfaces`
- `capability_families`
- `execution_entry`
- `model_route`
- `initial_model_selection_record_id`
- `tool_surface_strategy`
- `fast_path`
- `precheck_results`
- `routing_metadata`
- `reasoning_summary`

`primary_surface` is optional: a request with no single primary work surface omits it (§4.3). `model_route` may be null when the route enters no model-bound step, or when a safe-default route produced under a routing failure (§3.6) defers model selection to downstream fallback; the valid pairings of `model_route` and `initial_model_selection_record_id` are fixed by the three-shape invariant (§4.3).

### 4.3 Field Meanings

`trigger_kind`

The class of trigger that produced this `RunIntent`. One of: `user_request`, `retry`, `edit_reroute`, `continuation`, `child_run`, `automation`, `external_event`, `user_invoked_action`. Per §2.1.

`trigger_id`

Polymorphic identity of the trigger. Resolves to a `message_id` for user requests, an `event_id` for external events, an `automation_id` for automations, a `parent_run_id` for child runs, an `action_invocation_id` for user-invoked actions, the `message_id` of the edited message for edit reroutes, the `run_id` of the retried run for retries, and the `run_id` of the continued run for continuations.

`parent_run_id`

The id of the parent run, if any. Set for child runs spawned from another run and for retry, edit-reroute, and reroute branches that descend from a prior run. Null for top-level runs that have no parent.

`trace_context`

Optional propagation envelope for cross-run observability. Carries a stable trace identifier across spawn, retry, and reroute boundaries so descendant runs remain correlatable with their origin. The wire format is implementation-defined; later observability specs may standardize on a particular convention.

`attachment_kind`

- `continue_existing`
- `start_new`
- `start_parallel`

`start_parallel` covers both independent parallel work lines and decomposed sub-work lines that share parent context. The decomposition-vs-independence distinction is task-layer state and is not a routing-layer attachment kind.

`primary_surface`

The main work surface most relevant to the request, if any. Optional: a request may resolve to no primary surface — for example, discovery, capability-level, or conversation-baseline work that runs against the always-present baseline subsystem surface (`SubsystemSurfaceSpec`, File 07 §5, §9) rather than a specific work surface. When `primary_surface` is absent, downstream surface fallback follows File 25 §2.3, §11.2.

Examples:

- `coder`
- `web`
- `teacher`
- `data_processor`
- `gui_control`
- `system_agent`

`supporting_surfaces`

Additional surfaces likely to matter.

This exists because real requests are often not single-surface.

`capability_families`

The main capability groups the runtime should treat as relevant. Family names come from the live capability registry; the list below is illustrative, not canonical, and the runtime set varies with installed capabilities, plugins, and extensions.

Examples:

- `conversation_response`
- `web_fetch`
- `web_search`
- `file_read`
- `file_edit`
- `browser_control`
- `memory_recall`
- `document_edit`
- `planning`
- `subagent_orchestration`

`execution_entry`

The initial execution path.

Allowed values:

- `respond_inline`
- `respond_with_tools`
- `surface_runtime`
- `multi_step_agent`

`model_route`

The `ModelRoute` chosen for the request: the effective execution result naming the model strategy the initial model-bound step runs under. May be null when the route enters no model-bound step, or when a safe-default route produced under a routing failure (§3.6) could not resolve a provider and defers model selection to downstream fallback — the safe-default's `respond_inline`/`respond_with_tools` entry is itself model-bound; what is absent is the resolved selection, not the step.

When present, it must include:

- `profile_id`
- `resolved_provider_id`
- `resolved_model_id`
- `fallback_policy_id`

`ModelRoute` is the effective execution result only. It does not carry the selection-record reference: the record that explains the decision is referenced by the sibling `initial_model_selection_record_id`, never by the route. A `ModelRoute` produced in memory is paired with its record as a `ResolvedModelSelection { route, selection_record_id }` (`model.model-selection-algorithm`, File 16 §7.2); routing records the pair by placing the route in `model_route` and the record reference in `initial_model_selection_record_id`.

`initial_model_selection_record_id`

References the `ModelSelectionRecord` (`model.model-selection-record`, File 16 §8) produced when model selection was invoked for the initial model-bound step. It is the sole identity channel for that decision: the route does not carry it and the human-readable `reasoning_summary` never encodes it. Later model-bound steps inside the same run produce their own selection records, reached forward through their durable model-call-start facts (`ledger.entry-kinds`, File 10 §4.2), not through this field.

`model_route` and `initial_model_selection_record_id` are constrained by a three-shape invariant: of the four combinations the two nullable fields admit, exactly three are valid, and a `RunIntent` carrying the fourth is rejected rather than materialized or recorded:

- **selected** — `model_route` present, `initial_model_selection_record_id` present: selection ran and returned a route; the route is the effective result and the record explains it.
- **no-model** — `model_route` null, `initial_model_selection_record_id` present: selection ran and returned a typed no-model result (`NoModelAvailable`, `model.model-selection-algorithm`, File 16 §7.2, §7.6); the record explains why no route was produced.
- **selection-never-invoked** — `model_route` null, `initial_model_selection_record_id` null: selection was never called — either the route genuinely enters no model-bound step, or a safe-default route under a routing failure (§3.6) deferred model selection to downstream fallback (its model-bound entry runs under fallback resolution, so no initial selection record exists).

The fourth combination — `model_route` present, `initial_model_selection_record_id` null — is never a shape a recorded `RunIntent` can hold: a route without its originating selection record is a forgery tell.

`tool_surface_strategy`

The tool surface strategy chosen for the request; always present, defaulting to `use_current_surface_tools` when nothing signals borrowing or deferred loading (§8.3). One of: `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`. Enumeration mirrored in §8.3.

`fast_path`

Describes whether router-owned fast path was used.

It must include:

- `enabled`
- `performed_capabilities`
- `result_state`

`result_state` is one of: `not_performed` (no fast-path work ran), `completed` (all fast-path capabilities succeeded), or `failed` (at least one fast-path capability failed, per §9.4).

`precheck_results`

The ordered record of deterministic prechecks (§3.2) that fired during dispatch and the effect each had on the route: `resolved`, `constrained`, or `no_op`. Empty when no prechecks fired.

`routing_metadata`

Observability fields for the routing decision: the source of the decision (one of: `precheck_chain_resolved`, `model_router_emitted`, `classifier_emitted`, `inherited_from_parent_run`, `direct_hand_back`), routing latency, and any error if a recovery path was used. The `direct_hand_back` source records a route supplied whole by a deterministic trigger source without invoking the router (§12.2).

`reasoning_summary`

A short natural-language explanation of the routing decision — why this work line, surface, capability set, and model route were chosen. It is a human explanation field, not an identity channel: it carries no record reference, and the model-selection decision it describes is referenced only by `initial_model_selection_record_id`. It is the short routing explanation surfaced in the UI (§10.2). It is distinct from a routing summary (§6): the `reasoning_summary` explains one routing decision for inspection, while a routing summary is a compact router-side continuity aid for future routing.

### 4.4 What `RunIntent` Does Not Contain

`RunIntent` does not define:

- frontend posture
- visible layout
- whether a workspace panel must open
- whether the user is in a conversation-first or workspace-first experience

Those are presentation concerns.

Routing may inform them, but it does not own them as backend truth.

## 5. Continuity Attachment

Anchor: `routing.continuity-attachment`

### 5.1 Rule

Each new request attaches to exactly one primary intent thread.

That attachment is decided in routing.

### 5.2 Decision Order

Continuity attachment is decided in this order:

1. explicit user reference or override
2. deterministic attachment from active state
3. router model decision

### 5.3 Intent Thread Creation

Routing creates a new intent thread only when needed.

Common cases:

- the request starts a distinct new line of work
- the request is parallel to current work
- no prior work line cleanly owns the request
- downstream work needs durable ownership

Routing must not create intent threads mechanically for every message.

## 6. Routing Summaries

Anchor: `routing.routing-summaries`

### 6.1 Purpose

Router context policies that need work-line continuity beyond what active task and intent-thread state already carry need a compact mechanism that does not require replaying raw conversation history. Routing summaries are that mechanism. The `compact` default policy does not require routing summaries; richer policies may use them as a load-bearing continuity aid.

### 6.2 Chosen Mechanism

After each routed request, the system may persist a compact routing summary linked to its trigger.

That summary is for future routing, not for transcript display.

### 6.3 Requirements

A routing summary must be:

- short
- source-linked to its trigger
- specific to routing-relevant continuity
- replaceable by later summaries

It should capture only what future routing needs, such as:

- active work line identity
- short restatement of the current work line
- route-relevant attachments or constraints
- important explicit user preferences affecting future routing

### 6.4 Limits

Routing summaries are not:

- user-visible plan objects
- memory entries by default
- substitutes for task state
- required under the `compact` default router context policy

They are compact router-side continuity aids used by richer router context policies. Whether summaries are produced, and which policies consume them, are settings (§13).

## 7. Model Routing

Anchor: `routing.model-routing`

### 7.1 Principle

Model routing is part of dispatch, but it is not the whole router.

The router chooses a model strategy in the context of the request, not just the cheapest or strongest model in isolation.

### 7.2 Inputs

Model routing must consider:

- user overrides
- model profiles from settings
- provider capabilities
- modality requirements
- tool-calling support
- streaming behavior
- rate-limit state
- provider health state
- fallback policy
- task complexity
- active approval posture
- active per-scope budget state (token budgets; cost-ceiling overlay is provider-dependent and may be absent)

### 7.3 Required Shape

Model routing must support:

- explicit user-selected model
- explicit user-selected profile
- router-selected profile
- router-selected concrete model within that profile

This is required because model lists are dynamic and user-customizable.

Model routing may be implemented as a single decision or as an ordered chain of strategies in which each strategy may resolve, constrain, or pass to the next. Common strategies include explicit user-override resolution, fallback-after-failure resolution, approval-posture-driven resolution, classifier-based complexity resolution, and a terminal default strategy. Strategy composition is an implementation pattern; this file does not require it. The canonical contract is that the four shapes above must remain supported and the inputs of §7.2 must be considered.

### 7.4 Capability Awareness

Anchor: `routing.capability-awareness`

Model routing must be capability-aware.

Examples:

- visual requests require a visual-capable model route
- math-heavy requests may prefer a reasoning-oriented route
- trivial search or fetch preparation may use the low-cost router profile
- non-streaming models must not break the runtime because they are non-streaming

To stay capability-aware, model routing derives a `ModelWorkloadRequirements` descriptor for the request — modality, reasoning depth, tool-calling needs, streaming needs, and context-window pressure — from the trigger content and work-state, and matches it against provider capability metadata (§7.2) so the selected route is capability-valid. `ModelWorkloadRequirements` is a routing-time derivation, not a durable field of `RunIntent`.

## 8. Surface and Capability Selection

Anchor: `routing.surface-capability-selection`

### 8.1 Surfaces and Subsystems Are Not Hard Fences

Routing must not treat surfaces or subsystems as isolated silos.

A request may:

- stay in conversation while using web capabilities
- use coder capabilities without opening a coder workspace
- use memory recall without entering a memory management surface
- combine web, coder, teacher, and document capabilities in one line of work

### 8.2 Required Selection Shape

Routing must choose:

- one primary surface
- zero or more supporting surfaces
- relevant capability families

This is stronger than single-surface/subsystem routing and simpler than full execution planning.

### 8.3 Tool Surface Strategy

Anchor: `routing.tool-surface-strategy`

Routing always chooses a tool-surface strategy for the request and records it in the `tool_surface_strategy` field of `RunIntent` (§4.2, §4.3). The field is always present: when the request gives no signal to borrow foreign capabilities or defer loading, the strategy defaults to `use_current_surface_tools`, so downstream execution has no absent case to handle.

Allowed strategies:

- `use_current_surface_tools`
- `borrow_foreign_capabilities`
- `load_deferred_capabilities`

The full mechanics of borrowing and deferred loading belong in later capability and tool specs.

## 9. Fast Path

Anchor: `routing.fast-path`

### 9.1 Definition

Fast path is a router outcome where the router-owned phase performs trivial or preparatory work immediately.

Typical cases:

- a direct weather lookup
- fetching a requested page before the main responder runs
- a simple search classification followed by one search call
- resolving a simple resource lookup

The router phase is itself a model call. When a request needs only a trivial preparatory tool call, the router emits that tool call during routing and attaches the result to the request, so downstream execution proceeds with the result already in context — no extra round-trip. Fast path is distinct from cheap routing as an implementation property: a router that emits its decision through a single native tool call over cached stable model-request parts is a cheap router (§3.3), but cheapness alone does not put a request "on the fast path." Fast path requires the router phase to perform actual capability work whose results are handed into downstream execution.

### 9.2 What Fast Path Is Not

Fast path is not:

- skipping routing
- skipping continuity attachment
- skipping durable recording
- skipping downstream execution when downstream work is still needed

### 9.3 Allowed Behavior

When fast path is selected, the router-owned phase may:

- call one or more trivial capabilities
- attach the results to the request
- hand the prepared results into the downstream response path

The downstream model must not need to repeat work already completed by fast path.

Capabilities invoked during fast-path execution go through the same capability contract, capability policy, and approval router as any other capability call. Fast path is not a policy bypass: a capability whose normal execution would require approval still requires approval when invoked from the fast-path phase, and capability-policy interceptors (destructive-action detection, sensitive-resource elevation, denied-action lists) still apply.

### 9.4 Failure Rule

If fast-path execution fails:

- the failure is recorded
- the failure is attached to the routed request
- downstream execution may continue with the failure context

Fast-path failure must not silently discard the route or request.

## 10. User Visibility and Override

Anchor: `routing.user-visibility-override`

### 10.1 Visibility

Each routing decision must be linked to the triggering user message and be inspectable in the UI.

It does not need to be rendered as a normal transcript message.

### 10.2 Minimum Visible Information

Anchor: `routing.minimum-visible-information`

The UI must be able to show:

- what the request was routed to
- whether fast path was used
- which model route was chosen
- the short routing explanation
- whether the user has overridden the route
- the routing-frame inputs that informed the decision (which prechecks fired, which router context policy was active, which world-model snapshot was used)

### 10.3 Override

Any field in `RunIntent` may be overridden by the user, subject to validity: the override must produce a valid `RunIntent` (for example, the user cannot select a model the active provider cannot serve, and cannot select an `attachment_kind` that conflicts with the active intent-thread state).

Overrides take two shapes:

- value override: the user sets a field directly (for example, selecting a specific model)
- constraint: the user restricts the router's decision space (for example, "only use providers in this list" or "only use approval posture X"); the router still routes, choosing within the constraint

Common overridable parts include the primary surface, supporting surfaces, model route, capability families and `tool_surface_strategy`, the active approval posture, fast-path enablement, intent-thread attachment (including reattaching to a different thread), router enablement itself, and the active router context policy.

The UI exposes overrides progressively — common overrides surface as primary controls; the full field set is available on demand. A route override changes the `RunIntent` for the current request only; it is not a settings change. Persisting a choice as a new default is a separate settings action (§13). An override affects downstream execution for that request, is recorded as part of the route record (§3.5), and may inform later learned preferences.

## 11. Retry and Edit Rules

Anchor: `routing.retry-edit-rules`

### 11.1 Retry

Retry of the same request preserves the prior route by default.

It does not automatically rerun route selection unless:

- the user explicitly asks to reroute
- the prior route is now invalid
- the runtime detects that route inputs materially changed

### 11.2 Edit

Anchor: `routing.edit`

Editing a prior user message invalidates the prior route for that message.

The edited request must be rerouted.

### 11.3 Invalid Route Inputs

A prior route is invalid if any of the following changed materially:

- the triggering message content
- explicit user override state
- required capability availability
- required model capability availability
- provider or rate-limit state such that the prior route can no longer execute

When the conditions above arise mid-flight on a run that is already executing, invalidation is handled through the reroute mechanisms in §12. Whether such conditions automatically trigger reroute or surface to the user is governed by settings (§13).

### 11.4 Partial-Failure Retry

When a prior run produced partial failure (some execution units succeeded, others failed), retry of failed units only preserves the prior route by default. Retry of the whole structure follows §11.1.

### 11.5 Intent-Thread Reattachment

If the user moves the triggering message to a different intent thread, the prior route is invalid. The reattached request must be rerouted with the new intent thread as the routing-frame attachment.

## 12. Mid-Execution Reroute

Anchor: `routing.mid-execution-reroute`

### 12.1 Definition

A mid-execution reroute changes the route of an in-flight run to a different surface, model, capability family, or execution entry before the original route's work is complete. Reroute may be triggered by:

- the executing model, when it determines it lacks the right surface, model, capability family, policy scope, or surface runtime for the current work, and emits a reroute request with reasoning
- the runtime environment, when a watchdog, validator, monitor, stuck or loop detector, capability-availability change, provider-health change, rate-limit event, or other typed runtime signal triggers a reroute
- the user, through explicit intervention (interject, takeover, override) during execution

Each trigger source produces the same shape of reroute request: a target description (reasoning, suggested route fields if any) plus a trigger-source discriminator. Resolution paths are described in §12.2.

### 12.2 Resolution Paths

A mid-execution reroute request resolves through one of three paths, regardless of trigger source:

- router-resolved (default): the request goes through the router, which evaluates the reasoning and decides whether and where to reroute
- self-routed: the trigger source supplies the new route directly through the router model, which validates and emits a `RunIntent`
- direct hand-back: the trigger source supplies a complete valid `RunIntent` and the runtime reroutes without invoking the router; permitted only when the supplying source is deterministic (a user-issued override, a watchdog with a registered direct-resolution profile, or equivalent), and the route record (§3.5) is still produced

Direct hand-back never operates on an unbounded-trust model output. A reroute request originating from the executing model always resolves through router-resolved or self-routed.

### 12.3 Configuration

Mid-execution rerouting is controlled by settings (§13):

- whether mid-execution rerouting is enabled, per trigger source (model, environment, user)
- whether the executing model may self-route or must go through the router
- which environment signals are eligible to trigger reroute, and which may use direct hand-back
- if self-routing is enabled, the model may choose per-request which resolution path to use via an extra parameter on the reroute request

### 12.4 Boundary

This section defines the routing interface for mid-execution reroute requests. Full execution mechanics, including how the current run is suspended, handed off, or merged, belong in the execution spec.

## 13. Settings

Anchor: `routing.settings`

Every routing mechanism described in this file must be configurable through settings. Settings are scoped through the canonical settings system; user profiles compose them.

At minimum, settings must support:

- router enablement, including per-trigger-kind enablement (§2.1)
- router profile and router-model selection, including collapsing router work into the downstream model request when policy allows it
- router context policy selection, with active profile-layer defaults plus per-conversation and per-workspace overrides
- per-precheck enablement and ordering (§3.2)
- model-routing strategy chain composition, profile preferences, and per-surface model preferences
- fallback policy selection per scope
- active approval posture
- active per-scope budget state (token budgets; cost ceiling where the provider exposes it or the user has supplied estimates)
- fast-path enablement, per surface and per capability family
- route visibility verbosity
- whether routing summaries are enabled (only meaningful under richer router context policies; §6.4)
- mid-execution reroute enablement per trigger source (§12.3) and self-routing enablement
- routing-failure handling: safe-default route versus surface-to-user (§3.6)
- routing telemetry and routing-eval enablement

Settings whose mechanism depends on optional provider capability — accurate token counting, cost reporting, native tool-call streaming, and similar — must degrade gracefully when the capability is absent and must surface the degraded state to the user. They must not silently disable themselves, fail closed without notice, or block routing on a missing capability whose absence is recoverable.

Users must be able to customize routing without changing the core runtime shape. Settings define intended product variation; they must not become hidden hardcoded branches (per `core.typed-configuration-failure`, File 01 §7.6).

## 14. Explicit Rejections

Anchor: `routing.explicit-rejections`

The following shapes are wrong for this layer:

- single-surface/subsystem routing as the only route output
- treating frontend presentation as router-owned backend truth
- requiring a separate heavy continuity-analysis pass on top of normal routing
- making intent-thread creation a mandatory tool call
- defining fast path as routing bypass
- making full raw conversation replay the default router context
- hardcoding one router context policy with no user override
- forcing user-visible workspace opening as part of route truth
- treating model routing as only "pick the cheapest model" or only "pick the strongest model"
- confidence-threshold-driven routing as a canonical mechanism (strategies may use confidence internally to pick between paths or fall back; routing's external decision is one route, not a probability distribution)
- treating fast path as a capability-policy bypass
- bypassing routing for automation, child-run, external-event, or user-invoked-action triggers
- silently discarding the route or request when routing fails instead of applying a safe-default route or surfacing the failure (§3.6)

## 15. Consequences for Later Specs

Anchor: `routing.consequences-for-later-specs`

Later specs must follow these rules:

- run schema must consume `RunIntent` cleanly
- execution schema must treat route outputs as the execution entry contract
- capability specs must support route-directed borrowing and deferred loading
- UI specs must expose route inspection and override
- storage specs must record routing summaries, route decisions, and invalidation cleanly
- model/provider specs must expose enough capability metadata for model routing to remain dynamic
- automation, scheduling, and external-event specs must accept the routing-pipeline contract for their trigger kinds and use the `trigger_kind`/`trigger_id` discriminator (§2.1, §4.3)
- capability and plugin specs must support precheck registration through the same hook system the approval router uses (§3.2)
- storage and ledger specs must record route record content per §3.5: resolved `RunIntent`, `routing_metadata`, applied prechecks, applied pre-routing transformations, and snapshot references
- evaluation specs must include routing-evals as a first-class evaluation family, with the route record as the eval artefact

## 16. Canonical Rule Anchors

Anchor: `routing.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `routing.purpose`, `routing.routing-is-first-class-dispatch-step`, `routing.trigger-kinds-routing`, `routing.dispatch-pipeline`, `routing.routing-frame`, `routing.deterministic-prechecks`, `routing.route-record`, `routing.routing-failure`, `routing.run-intent`, `routing.continuity-attachment`, `routing.routing-summaries`, `routing.model-routing`, `routing.capability-awareness`, `routing.surface-capability-selection`, `routing.tool-surface-strategy`, `routing.fast-path`, `routing.user-visibility-override`, `routing.minimum-visible-information`, `routing.retry-edit-rules`, `routing.edit`, `routing.mid-execution-reroute`, and `routing.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
