# Model Strategy, Profiles, and Selection

## Status

Canonical.

## Scope

This file defines:

- `ModelCapabilityDescriptor`: the provider-invariant descriptor of what a model can do
- provider offering and runtime snapshots as inputs consumed from the Provider Layer
- `ModelProfile`: the named model-use configuration selected through settings
- `ModelWorkloadRequirements`: the typed hard requirements and preferences used for selection
- `ModelRegistry`: the computed query projection over descriptors, profiles, settings, and provider snapshots
- the model selection algorithm and `ModelSelectionRecord`
- fallback between compatible model candidates
- model behavioral intents, parameter resolution, and reasoning posture
- cost, budget, privacy, and data-boundary selection semantics
- explicit multi-model selection plans when requested by execution structure

This file does not define:

- provider adapter contracts, wire formats, credentials, streaming transport, provider health state machines, provider retry, rate-limit windows, pricing ingestion, or usage ledgers - File 17 owns those
- routing semantics, intent-thread state, or `RunIntent` field meanings - File 03 owns those
- execution lifecycle, run graph, child-run orchestration, cancellation, or provider-call execution - File 04 owns those
- capability declarations, approval policy, leases, tool surfaces, or capability loading - Files 05-07 own those
- model-request assembly, token counting implementation, cache-marker rendering, or compaction - File 13 owns those
- settings source-stack resolution, profile contexts, TOML overlays, or durable setting scopes - File 15 owns those
- ledger/event row schemas - File 10 owns those
- concrete provider names, model names, pricing quirks, tokenizer libraries, cache-control syntax, or API parameter names

## Source Resolution

This file resolves model-selection material into one boundary: runtime components ask the Model Strategy layer which model configuration to use for a specific model-bound step. The Provider Layer reports model capabilities and provider/account/runtime facts; Model Strategy interprets them against workload requirements, settings, policy, cost posture, and fallback policy.

Resolved design:

- Stable model facts, provider/account offerings, and runtime state are separate inputs. Model Strategy consumes all three but owns only selection semantics.
- `ModelCapabilityDescriptor` is provider-invariant and capability-focused. Pricing, free-tier status, speed, rate limits, availability, credentials, provider health, and retry timing are not descriptor fields.
- `ModelProfile` is a registered model-use configuration. It is not a File 15 `Profile`, execution mode, interaction shape, provider configuration, or user account.
- Workload selection is expressed as hard requirements plus preferences, not a single task label or confidence threshold.
- Selection is deterministic, explainable, replayable, and recorded per model-bound step.
- Fallback never relaxes hard requirements silently. Compatibility is revalidated after model change and after final context assembly.
- Provider-specific behavior is normalized by provider adapters and consumed through provider-invariant records.

## 1. Model Strategy Layer

Anchor: `model.model-strategy-layer`

ATLAS3 has one Model Strategy layer between routing/execution and providers.

It answers:

- which `ModelProfile` applies
- which concrete provider/model should serve this model-bound step
- which behavioral intents should be applied to the request
- what to do if the chosen model cannot serve the request
- why the decision was made

The layer has five primitives:

- `ModelCapabilityDescriptor` - stable, normalized model capability facts
- `ModelProfile` - named model-use configuration selected through settings
- `ModelWorkloadRequirements` - hard requirements and preferences for one model-bound step
- `ModelSelectionRecord` - durable explanation of one selection
- `FallbackPolicy` - model-level recovery by selecting a different compatible candidate

The initial `RunIntent.model_route` governs the first model-bound step of a run. Later model-bound steps may invoke the same selection algorithm again with their own workload requirements, settings snapshot, and provider/runtime snapshot. A run may therefore contain several model selections: router, planner, responder, critic, validator, summarizer, completion verifier, child-run model, or other role-specific steps.

## 2. Provider Inputs Consumed by Model Strategy

Anchor: `model.provider-inputs-consumed-by-model-strategy`

Model Strategy consumes three categories of provider-derived information.

`ModelCapabilityDescriptor`

Stable provider-invariant facts about a model's request and output capabilities.

`ProviderOfferingProjection`

Provider/account facts that affect selection but are not model capabilities: provider access, enabled/disabled provider state, effective pricing projection, account plan availability, data handling metadata, region or locality facts, speed or latency observations, and user-supplied accounting overrides.

`ProviderRuntimeSnapshot`

Runtime facts reported by the Provider Layer: temporary unavailability, rate-limit posture, provider health, known retryability, in-flight capacity, credential state, and provider-reported errors. File 16 consumes this snapshot; it does not mutate or own it.

This split is load-bearing. A model can be vision-capable even when the user's account cannot access it, a model can be low-cost under one provider and expensive under another, and a normally fast model can be slow under current provider load. Selection must see all of those facts without pretending they are the same kind of data.

## 3. `ModelCapabilityDescriptor`

Anchor: `model.model-capability-descriptor`

### 3.1 Definition

A `ModelCapabilityDescriptor` is the normalized provider-invariant capability description for one `(provider_id, model_id)` pair.

It is:

- read-only from the user's perspective
- produced by provider adapter normalization
- source-attributed and inspectable
- allowed to contain `Unknown` for facts the provider cannot report
- keyed by provider and model identity

It is not:

- a pricing record
- an availability record
- a provider health record
- a runtime latency record
- a generation-parameter profile
- a fallback policy

### 3.2 Required Fields

Every descriptor must carry:

- `provider_id`
- `model_id`
- `display_name`
- `descriptor_version`
- `source_provenance`
- `request_limits`
- `streaming_support`
- `native_callable_support`
- `parser_tool_call_fallback_support`
- `multimodal_input_support`
- `structured_output_support`
- `reasoning_support`
- `cache_candidate_support`
- `token_accounting_support`
- `lifecycle_metadata`

`request_limits`

The maximum request-size and output-size facts the provider reports. Unknown limits remain unknown. The descriptor must not derive `output_window` from `context_window` by ratio. If output limits are absent, context assembly reserves output through policy and provider validation.

`streaming_support`

Whether streamed model output is supported and any provider-invariant constraints relevant to execution.

`native_callable_support`

Whether the model/provider supports provider-native callable declarations. This is the only support kind that satisfies a hard requirement for native tool calling.

`parser_tool_call_fallback_support`

Whether the response parser can recover tool calls from model text for this model/profile, and which registered parser-format identities are known to work for it. The field carries a format set (possibly empty or `Unknown`) with an optional recommended format, not a bare boolean. Format identities are provider-invariant registered identities; provider- or vendor-native format names are adapter normalization inputs, never canonical identities. This is a parser fallback, not native tool support. It requires explicit profile or policy allowance and stricter validation.

`multimodal_input_support`

Supported input modalities and provider-invariant limits, such as image support and file-like inputs where the provider exposes them.

`structured_output_support`

Whether the model/provider supports native schema enforcement, structured JSON-like output without strict schema enforcement, or no structured-output mode.

`reasoning_support`

The provider-invariant reasoning capability record. It describes whether the model can expose reasoning/thinking behavior and what semantic posture the adapter can map. It does not contain provider API field names.

`cache_candidate_support`

Whether logical cache-marker candidates from File 13 can be meaningful for this model/provider. Provider-native cache syntax, cache retention, cache pricing, and cache hit accounting belong to File 17.

`token_accounting_support`

Whether exact provider-native token counting, estimated counting, multimodal accounting, callable-declaration accounting, and cache-token attribution are available. Tokenizer libraries and provider exceptions belong to File 17.

`lifecycle_metadata`

Optional provider-reported lifecycle facts such as deprecation state and informational training cutoff. These are source-attributed facts, not selection policy by themselves.

### 3.3 Explicit Non-Fields

The descriptor must not contain:

- per-token pricing
- cache read/write price multipliers
- `is_free_tier`
- `cost_class`
- `speed_class`
- provider health
- rate-limit state
- retry-after or backoff data
- credential state
- account entitlement
- current availability
- concurrency counters
- hardcoded provider-specific generation defaults

Those facts are provider offering, provider runtime, accounting, or profile/policy facts consumed by selection.

### 3.4 Normalization and Refresh

Anchor: `model.normalization-refresh`

Provider adapters normalize provider-native capability data into `ModelCapabilityDescriptor`.

Normalization may use:

- provider capability APIs
- provider model-list data
- adapter-shipped static descriptors
- explicit probes where a provider supports them
- user-supplied descriptors for local, proxy, or custom providers

Unknown facts remain explicitly unknown. The adapter must not invent default capabilities to make selection easier.

Descriptor refresh is event-driven: provider registration, provider reconnection, adapter update, explicit user action, provider capability-change signal where available, or local descriptor edit. Optional scheduled maintenance refresh may exist as a user setting, but it is not a correctness condition and has no canonical interval. Stale descriptors may remain usable only with visible provenance/staleness diagnostics.

## 4. `ModelProfile`

Anchor: `model.model-profile`

### 4.1 Definition

A `ModelProfile` is a registered model-use configuration. It binds selection intent, behavioral intents, and fallback policy into a reusable unit.

It is not the same as File 15 `Profile`. File 15 profiles are settings-default layers. They may select or configure a `ModelProfile`, but they do not replace it.

A `ModelProfile` is not:

- a model
- a provider account
- a provider transport configuration
- an execution mode
- an interaction shape
- a frontend presentation state

### 4.2 Required Fields

Every `ModelProfile` must carry:

- `profile_id`
- `display_name`
- `description`
- `source` - `Builtin`, `Subsystem { subsystem_id }`, `Plugin { plugin_id }`, or `UserDefined`
- `version`
- `model_selector`
- `required_capabilities`
- `preferred_capabilities`
- `behavioral_intents`
- `fallback_policy_id`

### 4.3 Model Selectors

Allowed selector shapes:

- `Pinned { provider_id, model_id }`
- `PinnedModel { model_id }`
- `ByCapability { required, preferred }`
- `ByRole { role_tags }`
- `LowestCostCompatible`
- `HighestQualityCompatible`
- `Inherited`
- `CustomStrategy { strategy_id }`

`LowestCostCompatible` never means "cheapest even if weaker." It selects the lowest-cost candidate that satisfies all hard requirements and policy constraints.

`CustomStrategy` is the extension point for pluggable routing and selection strategies, including embedding-based routers, learned routers, pairwise preference routers, arena/evaluation strategies, and RouteLLM-like threshold strategies. These strategies may use internal scores, but their external output is the same typed selection result and must obey hard filters.

### 4.4 Behavioral Intents

Profiles may declare semantic behavioral intents:

- sampling posture
- output length posture
- reasoning posture
- structured-output posture
- latency posture
- cost posture
- cache-continuity preference
- model-request/style template reference consumed by File 13
- parser-format preference for parser-fallback tool calling
- stop-sequence preference

These are intents, not provider wire fields. Provider adapters map resolved intents to provider-native request parameters in File 17.

### 4.5 Settings Boundary

File 15 resolves which model-related setting values are active. File 16 interprets those resolved values.

File 16 must not define a second source stack for profiles. Invocation overlays, conversation/workspace/global settings, local overlays, and File 15 profile layers all resolve through File 15 before model selection reads them.

## 5. `ModelWorkloadRequirements`

Anchor: `model.model-workload-requirements`

### 5.1 Definition

`ModelWorkloadRequirements` is the typed description of what one model-bound step needs.

It contains:

- `role_tags`
- `hard_requirements`
- `preferences`
- `input_modalities`
- `output_contract`
- `request_size_needs`
- `reasoning_posture`
- `structured_output_posture`
- `native_tool_calling_requirement`
- `parser_fallback_allowed`
- `streaming_requirement`
- `latency_posture`
- `cost_posture`
- `data_boundary_requirements`
- `source_context`

It is not a single label. A step may be both responder and validator, vision and structured-output, local-only and high-reasoning, or low-cost and native-tool-required.

### 5.2 Roles

Canonical role tags include:

- `router`
- `responder`
- `planner`
- `summarizer`
- `critic`
- `validator`
- `classifier`
- `vision_grounding`
- `completion_verifier`
- `child_run_model`
- `custom { namespace, name }`

Roles are selection signals. They do not create execution phases.

### 5.3 Data-Boundary Ordering

Content sensitivity analysis over the raw input blocks and relevant conversation context runs before model selection. Sensitivity is a property of content, not of the selected model.

The ordering is:

1. Pre-assembly sensitivity analysis produces `data_boundary_requirements`.
2. Model selection treats those requirements as hard filters.
3. Context assembly uses the selected descriptor and provider/account snapshot to build the full model request.
4. The final assembled request is revalidated before dispatch.

If full assembly adds stricter sensitivity through retrieved context, memory, tool results, files, or system state, the runtime must reselect, reroute, ask the user, or fail. It must not send a request that exceeds the selected provider/model boundary.

### 5.4 Producer

File 03 produces initial workload requirements as part of routing. File 04 and later execution structures may produce new requirements for later model-bound steps in the same run. File 16 owns the vocabulary and selection semantics.

Confidence scores, if used internally by a custom strategy, are diagnostic. They are not the canonical selection contract.

## 6. `ModelRegistry`

Anchor: `model.model-registry`

### 6.1 Definition

`ModelRegistry` is a computed, read-optimized projection over:

- normalized `ModelCapabilityDescriptor`s
- registered `ModelProfile`s
- resolved model-strategy settings
- provider offering projections
- provider runtime snapshots

It is not an independent mutable store of provider truth.

### 6.2 Operations

The registry must support:

- descriptor lookup by `(provider_id, model_id)`
- profile lookup by `profile_id`
- model listing with typed filters
- profile listing with typed filters
- candidate enumeration for a `ModelWorkloadRequirements`
- profile resolution for a scope context
- model selection for one model-bound step
- explanation lookup for prior `ModelSelectionRecord`s

### 6.3 Projection Changes

Registry-relevant events may report descriptor changes, profile registration/update, offering changes, runtime availability changes, and selection results. The event stream and ledger record these facts per File 10; File 16 defines the selection meaning, not the storage schema.

Provider health, rate-limit counters, retry-after values, credential state, and provider connection state remain Provider Layer state.

## 7. Model Selection Algorithm

Anchor: `model.model-selection-algorithm`

### 7.1 Inputs

Each selection invocation consumes:

- `ModelWorkloadRequirements`
- resolved model-strategy settings from File 15
- relevant `ModelProfile`s
- normalized model descriptors
- provider offering projections
- provider runtime snapshot
- capability and policy constraints relevant to provider/model use
- budget and cost posture
- prior selection context when the invocation is a fallback or rerun

### 7.2 Output

Selection returns either:

- `SelectedModel { profile_id, provider_id, model_id, fallback_policy_id, selection_record_id }`
- `ModelSelectionPlan { selections, topology_hint, selection_record_id }`
- `NoModelAvailable { reasons, recovery_options, selection_record_id }`

Ordinary requests return one selected model. Explicit comparison, ensemble, best-of-N, arena, critic-selector, or mixture-of-agents work may request a `ModelSelectionPlan`. Each selection inside a plan must satisfy the hard requirements for its role.

### 7.3 Algorithm

Selection proceeds in deterministic phases:

1. Resolve explicit user constraints and profile preferences from settings.
2. Resolve candidate profiles.
3. Enumerate candidate provider/model pairs through the registry projection.
4. Apply hard filters: user-pinned identity, capability requirements, data-boundary requirements, provider/account access, policy constraints, current provider-runtime disqualification, and active budget ceilings.
5. Resolve profile selectors over the surviving candidates.
6. Apply preferences: preferred capabilities, role suitability, quality/evaluation signals, provider preference, cost posture, latency posture, cache-continuity preference, and recent successful use where applicable.
7. Apply configured tie-breakers.
8. Create a `ModelSelectionRecord`.
9. Return the selected model, selection plan, or typed no-model result.

Hard filters are never converted into weighted scores. Tie-breakers are inspectable settings, not hidden constants.

### 7.4 Explicit User Choices

`model.override` is a concrete model pin. It is a hard identity constraint. If the pinned model is unavailable, inaccessible, policy-disallowed, or incapable of the workload's hard requirements, selection returns a typed `UserPinnedModelUnavailable`, `UserPinnedModelCapabilityMismatch`, or equivalent no-model result. It does not silently fall through to lower-precedence settings.

`model.profile` is a criteria preference. If the selected profile cannot resolve to an available compatible model, the active fallback policy determines whether to try the next compatible profile/candidate or surface the failure to the user.

### 7.5 Multiple Selections Per Run

The initial route-selected model does not freeze every later model call in the run.

Each model-bound step may invoke selection independently when it has distinct workload requirements: cheap planning, high-quality execution, independent critique, validation, summarization, completion verification, child-run execution, or automation stages. Each invocation records its own `ModelSelectionRecord` linked to the parent run and step.

### 7.6 No-Model Results

When no candidate satisfies the requirements, the result must identify why:

- no provider enabled
- no model has required capability
- pinned model unavailable
- profile unresolved
- data-boundary conflict
- policy denial
- budget conflict
- provider runtime unavailable
- context/request size incompatible
- unknown required capability

Recovery options should be concrete: select another model, enable provider, relax a budget, change data-boundary policy, use local-only mode, allow parser fallback, disable a hard requirement, or ask for user direction.

## 8. `ModelSelectionRecord`

Anchor: `model.model-selection-record`

Every selection invocation produces a durable `ModelSelectionRecord`.

It must record:

- selection id
- invocation kind and source
- parent run, route, step, or model-call reference
- workload requirements
- resolved settings snapshot reference
- profile candidates considered
- provider/model candidates considered, with redacted rejection reasons where needed
- hard filters applied
- selected profile/provider/model or no-model result
- fallback lineage when applicable
- effective behavioral intents
- provider/runtime snapshot reference
- budget/cost projection reference
- data-boundary decision reference
- final tie-breaker explanation

The record stores enough to replay and inspect the decision without dumping raw provider/account secrets or full model-request contents. Route records and ledger entries reference the selection record rather than duplicating the full decision.

## 9. Fallback Policy

Anchor: `model.fallback-policy`

### 9.1 Definition

`FallbackPolicy` governs model-level recovery when the selected model cannot serve the request and a different compatible model may.

It does not govern:

- retrying the same request against the same model
- provider transport retry
- provider retry-after delays
- provider health backoff
- rate-limit state machines
- credential refresh

Those belong to File 17.

### 9.2 Error Classes

Fallback consumes typed provider/model failures from File 17:

- `ProviderUnavailable`
- `ModelUnavailable`
- `RateLimited`
- `CapabilityMismatchDiscovered`
- `RequestRejectedByProvider`
- `ContextTooLargeForSelectedModel`
- `PolicyOrDataBoundaryConflict`

File 17 may retry the same model before surfacing one of these failures. Once File 16 is asked to act, fallback means selecting a different compatible candidate or surfacing the failure.

Cancellation is not in this set and is never a fallback input. A user-initiated stop surfaces as File 17's `ProviderCallOutcome::Cancelled` or `StreamCancelled`, followed by File 10's durable `ModelCallCancelled` entry. It carries no `ProviderError` and ends the attempt sequence without candidate selection. Fallback selects an alternative only for a genuine provider/model failure; cancellation is the caller declining the work, not the model failing it.

### 9.3 Fallback Responses

Allowed fallback responses:

- `RetryWithModel { provider_id, model_id }`
- `RetryWithProfile { profile_id }`
- `RetryWithNextCompatibleCandidate`
- `RetryWithLowestCostCompatible`
- `RetryWithHighestQualityCompatible`
- `SurfaceToUser { options }`
- `StopWithTypedFailure { reason }`

Fallback responses must preserve all hard workload requirements unless the user or an explicit policy authorizes relaxation. Relaxation must be visible and recorded.

### 9.4 Revalidation

Any fallback that changes the model/provider requires:

- rerunning selection against current provider offering/runtime snapshots
- revalidating request-size and output reserve
- revalidating native callable declarations and parser fallback allowance
- revalidating multimodal, structured-output, reasoning, streaming, and data-boundary requirements
- rerunning or adjusting context assembly for the selected descriptor
- recording a new selection record and fallback ledger entry

If compatibility cannot be preserved, fallback surfaces the issue instead of silently degrading.

## 10. Behavioral Intent and Parameter Resolution

Anchor: `model.behavioral-intent-parameter-resolution`

### 10.1 Purpose

Different providers expose different parameter names and constraints. Model Strategy defines provider-invariant behavioral intents; File 17 serializes them.

### 10.2 Resolution

For each model request, behavioral intent resolution consumes:

- invocation overlay
- resolved settings
- selected `ModelProfile`
- provider-declared model constraints
- provider offering projection
- workload requirements

The output is a `ResolvedModelBehavior` record carrying:

- requested intent
- resolved value
- source of each resolved value
- provider/model constraint applied
- diagnostic when a value is clamped, omitted, injected, or rejected

Unsupported preferred parameters may be omitted with a diagnostic. Unsupported required behavior must fail selection or request preparation.

### 10.3 Reasoning Posture

Reasoning is represented by provider-invariant posture:

- `Required`
- `Preferred`
- `Auto`
- `Forbidden`

Reasoning effort or budget is semantic. Providers may expose reasoning as separate response fields, inline thinking tags, multiple thinking spans, a single hidden budget, or no explicit control. File 17 maps the semantic posture to provider-native behavior.

If reasoning is required and unsupported, selection must reselect or fail with typed `ReasoningRequirementUnsatisfied`. If reasoning is preferred and unsupported, the request may proceed only when policy permits and must record a diagnostic.

## 11. Cost and Budget Selection

Anchor: `model.cost-budget-selection`

Cost-aware selection consumes effective accounting projections from File 17 and settings. It does not read pricing from `ModelCapabilityDescriptor`.

Cost projections may include:

- provider-reported pricing
- user-supplied pricing
- local or self-hosted cost model
- subscription/account inclusion status
- cache-adjusted projected cost
- unknown-cost state

Unknown cost remains unknown. It is never reclassified as free. Whether unknown-cost models are eligible for automatic selection is a setting/policy choice.

Budget filtering is opt-in per File 04. When active, budget constraints are hard filters. If budget constraints exclude every model that satisfies hard workload requirements, selection returns a typed conflict rather than silently choosing an incapable model.

Cost class may exist as a user-facing projection for settings and UI, but its derivation thresholds are settings/profile/provider-accounting concerns, not canonical constants.

## 12. Cache Semantics

Anchor: `model.cache-semantics`

Model-request caching affects model selection only through provider-invariant inputs:

- descriptor cache-candidate support
- context assembly's logical cache-marker candidates
- provider/account cache availability projection
- cost/latency projection from File 17

File 16 does not define provider cache syntax, cache retention duration, cache marker limits, cache billing multipliers, or cache hit accounting.

Cache continuity may be a tie-breaker after hard requirements, policy, data boundary, and budget are satisfied. It must not cause selection to violate correctness.

## 13. Multi-Model Selection Plans

Anchor: `model.multi-model-selection-plans`

A `ModelSelectionPlan` is allowed only when the caller requests a topology that needs multiple model selections: comparison, best-of-N, arena, mixture-of-agents, critic-selector, validator/responder split, or explicit multi-agent work.

The plan must declare:

- role of each selected model
- workload requirements satisfied by each selection
- whether selections run in parallel or sequence
- aggregation or selection responsibility
- budget and data-boundary constraints per selection
- selection records for each model-bound step

Multi-model fan-out is not a hidden automatic fallback. It is an explicit execution structure consumed by File 04.

## 14. Settings

Anchor: `model.settings`

Model-strategy behavior must be configurable through File 15 settings.

Settings dimensions include:

- default and per-scope `ModelProfile`
- default and per-scope concrete model override
- fallback policy selection
- per-role profile preferences
- per-role concrete model overrides
- preferred and excluded providers
- excluded models
- reasoning posture and effort preference
- behavioral parameter preferences
- data-boundary posture
- cost posture and unknown-cost policy
- named selection strategy or tie-breaker policy
- parser-fallback allowance
- parser-format selection, keyed globally, per provider, per model, and per profile
- multi-model plan enablement for explicit comparison/ensemble flows

Provider health backoff, descriptor refresh mechanics, rate-limit windows, retry timing, cache billing, provider pricing ingestion, and usage accounting are File 17 settings. Exact default values belong to setting definitions and profile layers, not this file.

## 15. Explicit Rejections

Anchor: `model.explicit-rejections`

The following shapes are wrong for this layer:

- hardcoded model-name branching outside provider adapter normalization
- provider-specific API names, model names, pricing, tokenizer rules, or cache syntax in canonical selection logic
- treating pricing, free-tier status, speed, rate limits, or provider health as stable model capabilities
- boolean-only capability descriptors for complex capabilities
- treating parser-recovered text tool calls as equivalent to native provider callables
- deriving missing output limits from context-window ratios
- time-based descriptor refresh or provider polling as correctness logic
- model registry as an independent source of provider truth
- provider retry, retry-after delay, provider backoff, or credential refresh implemented in Model Strategy
- fallback that silently relaxes hard requirements
- weighted scores that allow soft preferences to override hard filters
- confidence-threshold-driven selection as the canonical external contract
- silent fallthrough from a concrete user-pinned model
- silently dropping required reasoning, structured output, native tools, modality, or privacy constraints
- storing model-dependent values as unkeyed scalars
- treating `ModelProfile` as a File 15 profile layer, execution mode, autonomy level, or interaction shape
- freezing one selected model for every model-bound step in a run
- hidden automatic multi-model fan-out

## 16. Consequences for Later Specs

Anchor: `model.consequences-for-later-specs`

Later specs must follow these rules:

- File 17 must expose normalized model descriptors, provider offering projections, provider runtime snapshots, effective pricing/accounting projections, provider health, rate limits, retry semantics, cache accounting, and provider-native parameter serialization without leaking provider-specific mechanics into File 16.
- File 03 must produce initial model workload requirements and a model route for the first model-bound step; route records should reference the corresponding `ModelSelectionRecord`.
- File 04 must allow model selection to be invoked per model-bound step, must record selection records and fallback attempts, and must treat multi-model plans as explicit execution structure.
- File 07 must consume native callable support and parser-fallback support without treating tool-surface visibility as model-selection authority.
- File 10 must record selection, fallback, model-call attribution, provider/runtime snapshot references, and cache/usage attribution through durable ledger/event records.
- File 13 must consume descriptor request limits, capability records, behavioral intents, and cache-candidate support; it owns assembly, token counting, cache-marker candidates, and final pre-dispatch data-boundary revalidation.
- File 15 must resolve all model-strategy settings through the canonical source stack; File 16 must not create a second profile or override cascade.
- Surface and subsystem specs may declare default `ModelProfile`s and role preferences, but must not implement private model-selection logic.
- Automation and workflow specs may pin a `ModelProfile`, concrete model, or full selection plan at save time; execution still records the effective selection used at runtime.
- Evaluation specs should measure model-selection correctness, fallback correctness, cost prediction, cache effectiveness, data-boundary filtering, and role-specific model quality using `ModelSelectionRecord`s as primary artifacts.
