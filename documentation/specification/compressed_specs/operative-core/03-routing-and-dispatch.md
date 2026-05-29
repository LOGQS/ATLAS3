# Routing and Dispatch

## 1. Purpose {routing.purpose}
- Canonical output: `RunIntent`.

## 2. Routing Is a First-Class Dispatch Step {routing.routing-is-first-class-dispatch-step}
- Routing must be: durably recorded, linked to its trigger, inspectable, replayable, overrideable by the user.
- Every new run must pass through routing before downstream execution begins, unless the trigger is a pure local UI action not asking the system to perform work.

### 2.1 Trigger Kinds and Routing {routing.trigger-kinds-routing}
- Routing applies to every trigger kind: user request, retry, edit reroute, continuation, child run, automation, external event, user-invoked action.
- Routing pass must respect pinned fields and fill only unpinned ones.
- Child-run triggers inherit policy+capability snapshots from parent; child receives its own `RunIntent`.
- Pre-filling+inheritance must not bypass routing.

## 3. Dispatch Pipeline {routing.dispatch-pipeline}
1. Build the routing frame.
2. Apply deterministic prechecks.
3. Run the router.
4. Materialize `RunIntent`.
5. Optionally execute router-owned fast-path work.
6. Persist the route result and attach it to the request.
7. Hand off to downstream execution.

### 3.1 Routing Frame {routing.routing-frame}
- Four input categories: Trigger context, Work-state context, Capability-and-policy context, Model-and-provider context.
- Frame must include enough from each of the four categories for a valid `RunIntent`.
- For user-request routing, the full current triggering input must be present directly or as a referenced externalized source.
- Canonical default = `compact` policy.
- Richer policies: `compact_with_summaries`, `recent_blocks`, `pinned_and_referenced`, `expanded_for_ambiguity`, custom policies.
- Changing router context policy must not change the meaning of `RunIntent`, bypass durable route recording, omit a required category, or make full raw conversation replay the fixed default.
- Each pre-routing transformation that altered trigger content must be recorded in the route record.

### 3.2 Deterministic Prechecks
- A precheck runs before the router model; may resolve, constrain, or no-op the routing decision.
- Prechecks are ordered; order+per-precheck enablement are settings; a resolving precheck short-circuits later prechecks.

### 3.3 Router
- Routing must be cheap enough to run on every relevant trigger.

### 3.4 Route Application

### 3.5 Route Record {routing.route-record}
- Route result must be recorded durably as part of the run record.
- Must preserve enough to reconstruct, replay, inspect, and audit the routing decision.
- Must reference the policy snapshot, capability snapshot, world snapshot in effect at routing time.
- Every precheck that fired and every pre-routing transformation that altered trigger content must be present.

## 4. `RunIntent` {routing.run-intent}
### 4.1 Definition
### 4.2 Required Fields
`conversation_id`, `trigger_kind`, `trigger_id`, `parent_run_id`, `trace_context`, `primary_intent_thread_id`, `attachment_kind`, `primary_surface`, `supporting_surfaces`, `capability_families`, `execution_entry`, `model_route`, `tool_surface_strategy`, `fast_path`, `precheck_results`, `routing_metadata`, `reasoning_summary`.
### 4.3 Field Meanings
- `trigger_kind` — one of: `user_request`, `retry`, `edit_reroute`, `continuation`, `child_run`, `automation`, `external_event`, `user_invoked_action`.
- `trigger_id` — resolves to `message_id`, `event_id`, `automation_id`, `parent_run_id`, `action_invocation_id`, or equivalents.
- `parent_run_id`
- `trace_context`
- `attachment_kind` — `continue_existing` | `start_new` | `start_parallel`.
- `primary_surface` — e.g. `conversation`, `coder`, `web`, `teacher`, `data_processor`, `gui_control`, `system_agent`.
- `supporting_surfaces`
- `capability_families` — names from the live registry; e.g. `conversation_response`, `web_fetch`, `web_search`, `file_read`, `file_edit`, `browser_control`, `memory_recall`, `document_edit`, `planning`, `subagent_orchestration`.
- `execution_entry` — `respond_inline` | `respond_with_tools` | `surface_runtime` | `multi_step_agent`.
- `model_route` — must include `profile_id`, `resolved_provider_id`, `resolved_model_id`, `fallback_policy_id`, `selection_record_id`.
- `tool_surface_strategy` — one of `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`.
- `fast_path` — must include `enabled`, `performed_capabilities`, `result_state`.
- `precheck_results` — each effect one of `resolved`, `constrained`, `no_op`.
- `routing_metadata` — source one of `precheck_chain_resolved`, `model_router_emitted`, `classifier_emitted`, `inherited_from_parent_run`.
- `reasoning_summary`
### 4.4 What `RunIntent` Does Not Contain
- Does not define frontend posture, visible layout, panel opening, or conversation-first/workspace-first experience.

## 5. Continuity Attachment {routing.continuity-attachment}
### 5.1 Rule
- Each new request must attach to exactly one primary intent thread.
### 5.2 Decision Order
1. explicit user reference/override
2. deterministic attachment from active state
3. router model decision
### 5.3 Intent Thread Creation
- Routing must not create intent threads mechanically for every message.

## 6. Routing Summaries {routing.routing-summaries}
### 6.1 Purpose
### 6.2 Chosen Mechanism
### 6.3 Requirements
### 6.4 Limits
- Not required under the `compact` default policy.

## 7. Model Routing {routing.model-routing}
### 7.1 Principle
### 7.2 Inputs
- Must consider: user overrides, model profiles, provider capabilities, modality requirements, tool-calling support, streaming behavior, rate-limit state, provider health state, fallback policy, task complexity, active approval posture, active per-scope budget state.
### 7.3 Required Shape
- Must support: explicit user-selected model, explicit user-selected profile, router-selected profile, router-selected concrete model within that profile.
### 7.4 Capability Awareness {routing.capability-awareness}
- Model routing must be capability-aware.
- Non-streaming models must not break the runtime.

## 8. Surface and Capability Selection {routing.surface-capability-selection}
### 8.1 Surfaces and Subsystems Are Not Hard Fences
- Routing must not treat surfaces/subsystems as isolated silos.
### 8.2 Required Selection Shape
- Routing must choose one primary surface, zero or more supporting surfaces, relevant capability families.
### 8.3 Tool Surface Strategy {routing.tool-surface-strategy}
- Routing must record `tool_surface_strategy`. Allowed: `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`.

## 9. Fast Path {routing.fast-path}
### 9.1 Definition
### 9.2 What Fast Path Is Not
- Not: skipping routing, continuity attachment, durable recording, or needed downstream execution.
### 9.3 Allowed Behavior
- Downstream model must not need to repeat work already completed by fast path.
- Fast path is NOT a policy bypass; capabilities go through the same capability contract, policy, and approval router; calls requiring approval still require approval.
### 9.4 Failure Rule
- Fast-path failure must be recorded, attached to the routed request; must not silently discard the route or request.

## 10. User Visibility and Override {routing.user-visibility-override}
### 10.1 Visibility
- Each routing decision must be linked to the triggering user message and inspectable in UI.
### 10.2 Minimum Visible Information {routing.minimum-visible-information}
- UI must be able to show: what the request was routed to, whether fast path was used, which model route was chosen, the short routing explanation, whether the user overrode the route, the routing-frame inputs that informed the decision.
### 10.3 Override
- Any field in `RunIntent` may be overridden by the user, subject to validity (override must produce a valid `RunIntent`).
- An override must be recorded in the route record.

## 11. Retry and Edit Rules {routing.retry-edit-rules}
### 11.1 Retry
- Retry of the same request preserves the prior route by default.
### 11.2 Edit {routing.edit}
- Editing a prior user message invalidates the prior route; the edited request must be rerouted.
### 11.3 Invalid Route Inputs
- A prior route is invalid if any changed materially: triggering message content, explicit user override state, required capability availability, required model capability availability, provider/rate-limit state.
### 11.4 Partial-Failure Retry
- Retry of failed units only preserves the prior route by default.
### 11.5 Intent-Thread Reattachment
- Moving the triggering message to a different intent thread invalidates the prior route; the reattached request must be rerouted.

## 12. Mid-Execution Reroute {routing.mid-execution-reroute}
### 12.1 Definition
- Trigger sources: the executing model, the runtime environment, the user.
### 12.2 Resolution Paths
- router-resolved (default)
- self-routed
- direct hand-back — permitted only when the supplying source is deterministic; the route record must still be produced.
- A reroute request originating from the executing model must always resolve through router-resolved or self-routed.
### 12.3 Configuration
### 12.4 Boundary

## 13. Settings {routing.settings}
- Every routing mechanism must be configurable through settings, scoped through the canonical settings system.
- Settings depending on optional provider capability must degrade gracefully when absent and surface the degraded state; must not silently disable themselves, fail closed without notice, or block routing on a missing recoverable capability.

## 14. Explicit Rejections {routing.explicit-rejections}
- single-surface/subsystem routing as the only route output
- treating frontend presentation as router-owned backend truth
- requiring a separate heavy continuity-analysis pass
- making intent-thread creation a mandatory tool call
- defining fast path as routing bypass
- making full raw conversation replay the default router context
- hardcoding one router context policy with no user override
- forcing user-visible workspace opening as part of route truth
- treating model routing as only cheapest/strongest model
- confidence-threshold-driven routing as a canonical mechanism
- treating fast path as a capability-policy bypass
- bypassing routing for automation, child-run, external-event, or user-invoked-action triggers

## 15. Consequences for Later Specs {routing.consequences-for-later-specs}
- run schema must consume `RunIntent` cleanly
- execution schema must treat route outputs as the execution entry contract
- capability specs must support route-directed borrowing+deferred loading
- UI specs must expose route inspection+override
- storage specs must record routing summaries, route decisions, invalidation cleanly
- model/provider specs must expose enough capability metadata for dynamic model routing
- automation/scheduling/external-event specs must accept the routing-pipeline contract and use the `trigger_kind`/`trigger_id` discriminator
- capability+plugin specs must support precheck registration through the same hook system the approval router uses
- storage+ledger specs must record route record content per §3.5
- evaluation specs must include routing-evals as a first-class evaluation family
