> Lossless render of canonical/03-routing-and-dispatch.md — original 34742 chars

# Routing and Dispatch

## Status
Canonical.

## Scope
Defines: the routing layer; dispatch timing; router inputs; `RunIntent` as a concrete routing output; continuity attachment; fast path; route visibility+override; retry+edit rerouting rules.
Does not define: run schema; task schema; execution graph schema; approval mechanics; tool contract schema; storage schema.

## Source Resolution
Resolves routing, model selection, fast-path, workspace selection, dispatch into one boundary: incoming user/system input becomes a `RunIntent`. Resolved design: routing is a first-class runtime step, not hidden model-request logic; a `RunIntent` describes selected work line, execution entry, model route, context policy, capability surface (not merely a surface/subsystem label); router output may include fast-path results/failures but that work is visible to execution+ledgering; router context is compact, policy-governed, independently configurable from main-model context; presentation is a user-controllable projection (routing may inform it but does not own frontend participation mode); edits/retries/mid-execution reroutes create explicit routing transitions rather than silently mutating prior decisions.

## 1. Purpose `routing.purpose`
Routing decides how a new request enters the runtime. It does not produce the final answer. It decides: what the request belongs to; what kind of execution should happen; which capabilities are relevant; which work surface is primary (if any); which model strategy; whether trivial/preparatory work can be done immediately. Canonical output: `RunIntent`.

## 2. Routing Is a First-Class Dispatch Step `routing.routing-is-first-class-dispatch-step`
Not: hidden preprocessing; optional metadata generation; only a frontend concern. Must be: durably recorded; linked to its trigger; inspectable; replayable; overrideable by the user. Implementation may realize routing as a dedicated runtime node, dispatch-layer phase, or equivalent step — not the canonical concern. Canonical concern: every new run passes through routing before downstream execution begins, regardless of trigger kind, unless the trigger is a pure local UI action that does not ask the system to perform work.

### 2.1 Trigger Kinds and Routing `routing.trigger-kinds-routing`
Routing applies to every trigger kind: user request, retry, edit reroute, continuation, child run, automation, external event, user-invoked action. Pipeline shape same for all; trigger-kind rules govern which fields the trigger pre-fills vs router decides.
- automation triggers may pin primary surface, capability families, model route, or full `RunIntent` at save time; routing pass respects pinned fields, fills only unpinned ones
- child-run triggers inherit policy+capability snapshots from parent; child receives its own `RunIntent` that may narrow/pivot/fully replace inherited surface+capability selection
- external-event triggers route with the event payload as routing-frame trigger context
- user-invoked actions (capability palette, shortcut, voice-mapped action) may skip the router model when the action id deterministically resolves the route; routing record still created
- retry/edit reroute/continuation triggers follow §11 and §12
Pre-filling+inheritance constrain routing the same way an explicit user override does (§3.2); they do not bypass it. Per-trigger-kind enablement, pin-through behavior, inheritance scope are user-configurable through settings (§13).

## 3. Dispatch Pipeline `routing.dispatch-pipeline`
For each new user request, dispatch proceeds in order:
1. Build the routing frame.
2. Apply deterministic prechecks.
3. Run the router.
4. Materialize `RunIntent`.
5. Optionally execute router-owned fast-path work.
6. Persist the route result and attach it to the request.
7. Hand off to downstream execution.
The seven-step pipeline is the canonical logical contract. Implementations may compose additional steps (extension prechecks, validators, observers, gates) through the actions+events hook architecture [`run.hook-integration`, File 04 §23.3] without changing canonical step order or the routing decision contract.

### 3.1 Routing Frame `routing.routing-frame`
Structured input the routing layer reasons over; must contain enough state for a valid `RunIntent` while staying cheap enough for the active router context policy. File 13 owns assembly of the router's model request; this file owns the meaning of routing frame+result. Four input categories:
**Trigger context** — the triggering input (user message, automation event payload, external event, child-run request, retry/edit reference, or user-invoked action); `trigger_kind` discriminator (§2.1); active conversation id; current route override state (if any); explicit user-specified attachments/inputs.
**Work-state context** — current active intent thread (if any); current active task (if any); compact prior routing summaries / previous route records / selected history when the active router context policy uses them (§6, File 13); active world model snapshot (active surface, focused element, mounted panels, selection, available capabilities/control affordances, current ui_mode).
**Capability-and-policy context** — currently available capabilities+capability families; enabled work surfaces; active approval posture (equivalent of `GooseMode` / `AskForApproval` / active approval policy template).
**Model-and-provider context** — model-routing settings+available model profiles; relevant provider capability metadata (modality, tool-call format, streaming support, reasoning support, context window); relevant provider rate-limit state+provider health state; active per-scope budget state (token budgets primarily; cost-ceiling overlay is provider-dependent and may be absent); active model fallback policy.
Frame should not require raw replay of the full conversation as the fixed default. Frame is constructed by the active router context policy (configurable through settings, profiles, conversation overrides). Whatever the policy, frame must include enough from each of the four categories for a valid `RunIntent`. For user-request routing, the full current triggering input must be present directly or as a referenced externalized source per File 13.
Canonical default = `compact` policy: optimized for cheap, cache-friendly routing; includes trigger content plus the minimum from each required category, leaning on stable model-request parts (capability, model, surface catalogues) where provider caching supports them; may include a brief active-intent-thread/active-task summary when one is already maintained; does not require dedicated routing summaries (§6); aims for bounded cost through summaries+policy selection, not by ignoring relevant conversation length.
Richer policies selectable through settings/profiles/conversation overrides:
- `compact_with_summaries`: adds compact prior routing summaries (§6) for stronger work-line continuity
- `recent_blocks`: adds a small selected set of recent transcript blocks
- `pinned_and_referenced`: adds blocks the user has pinned, referenced, or attached
- `expanded_for_ambiguity`: increases included context when deterministic prechecks (§3.2) signal ambiguity
- custom policies registered by subsystems/plugins/users
Changing router context policy changes what the router sees. It must not change the meaning of `RunIntent`, bypass durable route recording, omit a category required for a valid `RunIntent`, or make full raw conversation replay the fixed default.
Trigger content consumed by the routing frame may be the result of deterministic pre-routing transformations (duplicate detection, attachment expansion, mention/slash-command macro expansion, other content normalizations). These are NOT deterministic prechecks (§3.2): they shape what the router sees, not whether/where the request is dispatched. Each transformation that altered trigger content must be recorded in the route record, incl. what was detected and what the user override (if any) decided.

### 3.2 Deterministic Prechecks
Run before the router model. A precheck = any deterministic function over the routing frame that may resolve, constrain, or no-op the routing decision; exist to avoid wasting model effort on cases already clear from runtime state. When a precheck fully resolves → router model step skipped. When it constrains/prefills (e.g., "must use coder primary surface", "force explicit-model-override to model X") → router model receives constraints, decides only unconstrained fields. When it no-ops → dispatch continues to router model unchanged.
Representative patterns: explicit user override of route/model/surface/capability strategy; retry of an unchanged routed request that preserves the prior route; explicit "back to X"/equivalent continuity reference; edit of a prior user message; exact capability invocation exposed by UI/palette (action id deterministically resolves route); active request clearly continuing the same work line; slash commands / namespace-scoped invocations mapping directly to actions/capabilities; deterministic state-flag routing (e.g., highlighted code selection unambiguously routes to code-edit capability); cached prior routing decision under identical inputs when cache key still valid.
Prechecks are ordered. Order+per-precheck enablement are settings; a precheck that resolves the route short-circuits later prechecks. Mechanism by which capabilities/plugins/subsystems/user config contribute additional prechecks is owned by the capability, settings, hooks specs, not this file.

### 3.3 Router
Typically model-driven. Job is narrower than inferring deep true intent: attach request to correct ongoing work line; choose appropriate execution entry shape; select relevant capability+surface targets; select model strategy; determine whether fast path is appropriate. Routing must be cheap enough to run on every relevant trigger — cheapness is a cost ceiling, not a prescribed mechanism (caching stable model-request parts e.g. capability/model/surface catalogues, native tool-call emission of the routing decision, substitution with a local classifier, or any equivalent). Any implementation achieving cheap, durable, replayable routing on every relevant trigger is valid.

### 3.4 Route Application
After router returns, runtime: creates/updates the primary work-line attachment; records the route result; prepares any router-owned fast-path outputs; initializes downstream execution with the resolved `RunIntent`.

### 3.5 Route Record `routing.route-record`
Route result recorded durably as part of the run record. Must preserve enough to: reconstruct the routing decision (resolved `RunIntent` + `routing_metadata`); replay the routing pass against same inputs; inspect the decision in UI; audit against routing-eval suites. Record references the policy snapshot, capability snapshot, world snapshot in effect at routing time (snapshot identities live in storage+version specs). Every precheck that fired (with verdict) and every pre-routing transformation that altered trigger content (§3.1) must be present.

## 4. `RunIntent` `routing.run-intent`
### 4.1 Definition
Concrete routing result for one request; short-lived as a dispatch object but its result is durably recorded.
### 4.2 Required Fields
`conversation_id`, `trigger_kind`, `trigger_id`, `parent_run_id`, `trace_context`, `primary_intent_thread_id`, `attachment_kind`, `primary_surface`, `supporting_surfaces`, `capability_families`, `execution_entry`, `model_route`, `tool_surface_strategy`, `fast_path`, `precheck_results`, `routing_metadata`, `reasoning_summary`.
### 4.3 Field Meanings
- `trigger_kind` — class of trigger. One of: `user_request`, `retry`, `edit_reroute`, `continuation`, `child_run`, `automation`, `external_event`, `user_invoked_action`. (§2.1)
- `trigger_id` — polymorphic identity. Resolves to `message_id` (user requests), `event_id` (external events), `automation_id` (automations), `parent_run_id` (child runs), `action_invocation_id` (user-invoked actions), equivalents for others.
- `parent_run_id` — id of parent run if any; set for child runs and for retry/edit-reroute/reroute branches descending from a prior run; null for top-level runs without parent.
- `trace_context` — optional propagation envelope for cross-run observability; carries a stable trace identifier across spawn/retry/reroute boundaries; wire format implementation-defined; later observability specs may standardize.
- `attachment_kind` — `continue_existing` | `start_new` | `start_parallel`. `start_parallel` covers both independent parallel work lines and decomposed sub-work lines sharing parent context; decomposition-vs-independence is task-layer state, not a routing-layer attachment kind.
- `primary_surface` — main work surface most relevant. Examples: `conversation`, `coder`, `web`, `teacher`, `data_processor`, `gui_control`, `system_agent`.
- `supporting_surfaces` — additional surfaces likely to matter (real requests often not single-surface).
- `capability_families` — main capability groups treated as relevant; names from the live capability registry (list illustrative, not canonical; varies with installed capabilities/plugins/extensions). Examples: `conversation_response`, `web_fetch`, `web_search`, `file_read`, `file_edit`, `browser_control`, `memory_recall`, `document_edit`, `planning`, `subagent_orchestration`.
- `execution_entry` — initial execution path. Allowed: `respond_inline` | `respond_with_tools` | `surface_runtime` | `multi_step_agent`.
- `model_route` — chosen model strategy. Must include: `profile_id`, `resolved_provider_id`, `resolved_model_id`, `fallback_policy_id`, `selection_record_id`. `selection_record_id` references the model-strategy selection record for the initial model-bound step; later model-bound steps in the same run may produce their own selection records without mutating this field.
- `tool_surface_strategy` — One of: `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`. (Enum mirrored in §8.3.)
- `fast_path` — whether router-owned fast path was used. Must include: `enabled`, `performed_capabilities`, `result_state`.
- `precheck_results` — ordered record of deterministic prechecks (§3.2) that fired + effect each had: `resolved`, `constrained`, or `no_op`. Empty when none fired.
- `routing_metadata` — observability fields: source of the decision (one of `precheck_chain_resolved`, `model_router_emitted`, `classifier_emitted`, `inherited_from_parent_run`), routing latency, any error if a recovery path was used.
### 4.4 What `RunIntent` Does Not Contain
Does not define: frontend posture; visible layout; whether a workspace panel must open; whether the user is in a conversation-first or workspace-first experience. Those are presentation concerns; routing may inform but does not own them as backend truth.

## 5. Continuity Attachment `routing.continuity-attachment`
### 5.1 Rule
Each new request attaches to exactly one primary intent thread; attachment decided in routing.
### 5.2 Decision Order
1. explicit user reference/override; 2. deterministic attachment from active state; 3. router model decision.
### 5.3 Intent Thread Creation
Routing creates a new intent thread only when needed. Common cases: request starts a distinct new line of work; request is parallel to current work; no prior work line cleanly owns the request; downstream work needs durable ownership. Routing must not create intent threads mechanically for every message.

## 6. Routing Summaries `routing.routing-summaries`
### 6.1 Purpose
Router context policies needing work-line continuity beyond active task+intent-thread state need a compact mechanism that does not require replaying raw conversation history. Routing summaries are that mechanism. The `compact` default policy does not require them; richer policies may use them as load-bearing continuity aid.
### 6.2 Chosen Mechanism
After each routed request, the system may persist a compact routing summary linked to its trigger; for future routing, not transcript display.
### 6.3 Requirements
A summary must be: short; source-linked to its trigger; specific to routing-relevant continuity; replaceable by later summaries. Should capture only what future routing needs: active work line identity; short restatement of current work line; route-relevant attachments/constraints; important explicit user preferences affecting future routing.
### 6.4 Limits
Not: user-visible plan objects; memory entries by default; substitutes for task state; required under the `compact` default policy. They are compact router-side continuity aids for richer policies. Whether summaries are produced + which policies consume them are settings (§13).

## 7. Model Routing `routing.model-routing`
### 7.1 Principle
Model routing is part of dispatch but not the whole router. Router chooses a model strategy in the context of the request, not just cheapest/strongest model in isolation.
### 7.2 Inputs
Must consider: user overrides; model profiles from settings; provider capabilities; modality requirements; tool-calling support; streaming behavior; rate-limit state; provider health state; fallback policy; task complexity; active approval posture (equivalent of `GooseMode`/`AskForApproval`/active approval policy template); active per-scope budget state (token budgets; cost-ceiling overlay provider-dependent and may be absent).
### 7.3 Required Shape
Must support: explicit user-selected model; explicit user-selected profile; router-selected profile; router-selected concrete model within that profile (required because model lists are dynamic+user-customizable). May be implemented as a single decision or an ordered chain of strategies each of which may resolve/constrain/pass to next (common: explicit user-override resolution, fallback-after-failure resolution, approval-posture-driven resolution, classifier-based complexity resolution, terminal default strategy). Strategy composition is an implementation pattern, not required. Canonical contract: the four shapes above remain supported and the inputs of §7.2 are considered.
### 7.4 Capability Awareness `routing.capability-awareness`
Model routing must be capability-aware. Examples: visual requests require a visual-capable model route; math-heavy requests may prefer a reasoning-oriented route; trivial search/fetch preparation may use the low-cost router profile; non-streaming models must not break the runtime because they are non-streaming.

## 8. Surface and Capability Selection `routing.surface-capability-selection`
### 8.1 Surfaces and Subsystems Are Not Hard Fences
Routing must not treat surfaces/subsystems as isolated silos. A request may: stay in conversation while using web capabilities; use coder capabilities without opening a coder workspace; use memory recall without entering a memory management surface; combine web/coder/teacher/document capabilities in one line of work.
### 8.2 Required Selection Shape
Routing must choose: one primary surface; zero or more supporting surfaces; relevant capability families. Stronger than single-surface/subsystem routing, simpler than full execution planning.
### 8.3 Tool Surface Strategy `routing.tool-surface-strategy`
Routing chooses a tool-surface strategy and records it in `tool_surface_strategy` (§4.2, §4.3). Allowed: `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`. Full mechanics of borrowing+deferred loading belong in later capability+tool specs.

## 9. Fast Path `routing.fast-path`
### 9.1 Definition
Router outcome where the router-owned phase performs trivial/preparatory work immediately. Typical: a direct weather lookup; fetching a requested page before the main responder; a simple search classification followed by one search call; resolving a simple resource lookup. The router phase is itself a model call — when a request needs only a trivial preparatory tool call, the router emits that call during routing and attaches the result, so downstream execution proceeds with the result already in context (no extra round-trip). Fast path is distinct from cheap routing: a router emitting its decision via a single native tool call over cached stable parts is cheap (§3.3), but cheapness alone does not put a request "on the fast path" — fast path requires the router phase to perform actual capability work whose results are handed into downstream execution.
### 9.2 What Fast Path Is Not
Not: skipping routing; skipping continuity attachment; skipping durable recording; skipping downstream execution when downstream work is still needed.
### 9.3 Allowed Behavior
When selected, router-owned phase may: call one or more trivial capabilities; attach results to the request; hand prepared results into the downstream response path. Downstream model must not need to repeat work already completed by fast path. Capabilities invoked during fast-path go through the same capability contract, capability policy, approval router as any other call — fast path is NOT a policy bypass: a capability whose normal execution would require approval still requires approval; capability-policy interceptors (destructive-action detection, sensitive-resource elevation, denied-action lists) still apply.
### 9.4 Failure Rule
If fast-path execution fails: failure recorded; attached to the routed request; downstream execution may continue with the failure context. Fast-path failure must not silently discard the route or request.

## 10. User Visibility and Override `routing.user-visibility-override`
### 10.1 Visibility
Each routing decision must be linked to the triggering user message and inspectable in UI; need not be rendered as a normal transcript message.
### 10.2 Minimum Visible Information `routing.minimum-visible-information`
UI must be able to show: what the request was routed to; whether fast path was used; which model route was chosen; the short routing explanation; whether the user overrode the route; the routing-frame inputs that informed the decision (which prechecks fired, which router context policy was active, which world-model snapshot was used).
### 10.3 Override
Any field in `RunIntent` may be overridden by the user, subject to validity (override must produce a valid `RunIntent` — e.g., cannot select a model the active provider cannot serve, cannot select an `attachment_kind` conflicting with active intent-thread state). Two shapes: value override (set a field directly, e.g. selecting a specific model); constraint (restrict the router's decision space, e.g. "only use providers in this list" / "only use approval posture X"; the router still routes, choosing within the constraint). Common overridable parts: primary surface, supporting surfaces, model route, capability families and `tool_surface_strategy`, active approval posture, fast-path enablement, intent-thread attachment (incl. reattaching to a different thread), router enablement itself, active router context policy. UI exposes overrides progressively (common ones as primary controls; full field set on demand). An override affects downstream execution for that request, is recorded in the route record (§3.5), and may inform later learned preferences.

## 11. Retry and Edit Rules `routing.retry-edit-rules`
### 11.1 Retry
Retry of the same request preserves the prior route by default. Does not automatically rerun route selection unless: user explicitly asks to reroute; prior route is now invalid; runtime detects route inputs materially changed.
### 11.2 Edit `routing.edit`
Editing a prior user message invalidates the prior route for that message; edited request must be rerouted.
### 11.3 Invalid Route Inputs
A prior route is invalid if any changed materially: triggering message content; explicit user override state; required capability availability; required model capability availability; provider or rate-limit state such that the prior route can no longer execute. When these arise mid-flight on an already-executing run, invalidation is handled through reroute mechanisms in §12. Whether they auto-trigger reroute or surface to user is governed by settings (§13).
### 11.4 Partial-Failure Retry
When a prior run produced partial failure (some units succeeded, others failed), retry of failed units only preserves the prior route by default; retry of the whole structure follows §11.1.
### 11.5 Intent-Thread Reattachment
If the user moves the triggering message to a different intent thread, the prior route is invalid; the reattached request must be rerouted with the new intent thread as the routing-frame attachment.

## 12. Mid-Execution Reroute `routing.mid-execution-reroute`
### 12.1 Definition
Changes the route of an in-flight run to a different surface/model/capability family/execution entry before the original route's work completes. May be triggered by:
- the executing model, when it determines it lacks the right surface/model/capability family/policy scope/surface runtime, emitting a reroute request with reasoning
- the runtime environment, when a watchdog, validator, monitor, stuck/loop detector, capability-availability change, provider-health change, rate-limit event, or other typed runtime signal triggers reroute
- the user, through explicit intervention (interject, takeover, override) during execution
Each trigger source produces the same shape: a target description (reasoning, suggested route fields if any) plus a trigger-source discriminator.
### 12.2 Resolution Paths
A reroute request resolves through one of three paths, regardless of trigger source:
- router-resolved (default): goes through the router, which evaluates the reasoning and decides whether+where to reroute
- self-routed: the trigger source supplies the new route directly through the router model, which validates and emits a `RunIntent`
- direct hand-back: the trigger source supplies a complete valid `RunIntent` and the runtime reroutes without invoking the router; permitted only when the supplying source is deterministic (a user-issued override, a watchdog with a registered direct-resolution profile, or equivalent), and the route record (§3.5) is still produced
Direct hand-back never operates on an unbounded-trust model output. A reroute request originating from the executing model always resolves through router-resolved or self-routed.
### 12.3 Configuration
Controlled by settings (§13): whether mid-execution rerouting is enabled, per trigger source (model, environment, user); whether the executing model may self-route or must go through the router; which environment signals are eligible to trigger reroute, and which may use direct hand-back; if self-routing is enabled, the model may choose per-request which resolution path via an extra parameter on the reroute request.
### 12.4 Boundary
This section defines the routing interface for reroute requests. Full execution mechanics (how the current run is suspended/handed off/merged) belong in the execution spec.

## 13. Settings `routing.settings`
Every routing mechanism here must be configurable through settings; scoped through the canonical settings system; user profiles compose them. At minimum settings must support:
- router enablement, incl. per-trigger-kind enablement (§2.1)
- router profile+router-model selection, incl. collapsing router work into the downstream model request when policy allows
- router context policy selection, with active profile-layer defaults plus per-conversation+per-workspace overrides
- per-precheck enablement+ordering (§3.2)
- model-routing strategy chain composition, profile preferences, per-surface model preferences
- fallback policy selection per scope
- active approval posture
- active per-scope budget state (token budgets; cost ceiling where the provider exposes it or the user supplied estimates)
- fast-path enablement, per surface+per capability family
- route visibility verbosity
- whether routing summaries are enabled (only meaningful under richer policies; §6.4)
- mid-execution reroute enablement per trigger source (§12.3) and self-routing enablement
- routing telemetry+routing-eval enablement
Settings whose mechanism depends on optional provider capability (accurate token counting, cost reporting, native tool-call streaming, similar) must degrade gracefully when absent and surface the degraded state; must not silently disable themselves, fail closed without notice, or block routing on a missing recoverable capability. Users must customize routing without changing core runtime shape. Settings define intended product variation; must not become hidden hardcoded branches [`core.typed-configuration-failure`, File 01 §7.6].

## 14. Explicit Rejections `routing.explicit-rejections`
Wrong for this layer:
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

## 15. Consequences for Later Specs `routing.consequences-for-later-specs`
- run schema must consume `RunIntent` cleanly
- execution schema must treat route outputs as the execution entry contract
- capability specs must support route-directed borrowing+deferred loading
- UI specs must expose route inspection+override
- storage specs must record routing summaries, route decisions, invalidation cleanly
- model/provider specs must expose enough capability metadata for model routing to remain dynamic
- automation/scheduling/external-event specs must accept the routing-pipeline contract for their trigger kinds and use the `trigger_kind`/`trigger_id` discriminator (§2.1, §4.3)
- capability+plugin specs must support precheck registration through the same hook system the approval router uses (§3.2)
- storage+ledger specs must record route record content per §3.5: resolved `RunIntent`, `routing_metadata`, applied prechecks, applied pre-routing transformations, snapshot references
- evaluation specs must include routing-evals as a first-class evaluation family, with the route record as the eval artefact
