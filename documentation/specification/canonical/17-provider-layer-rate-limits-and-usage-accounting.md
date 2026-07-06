# Provider Layer, Rate Limits, and Usage Accounting

## Status

Canonical.

## Scope

This file defines:

- `ProviderAdapter` as the typed provider-invariant contract every model/inference provider must implement
- `ProviderProfile` as the declarative description from which most adapters are realized
- request execution, parameter serialization, and the mapping from provider-invariant behavioral intents to provider-native parameters
- streaming transport, the canonical `ProviderStreamChunk` vocabulary plus registered extensions, cancellation, and partial-output semantics
- the closed canonical `ProviderError` taxonomy and `ErrorClassification` typed advice
- transport-level retry, backoff, and credential-pool rotation
- `ProviderHealth` and the runtime state machine
- `RateLimitState`, `RateLimitScope`, structural `RateLimitWindow`, and header-driven reconciliation
- `ProviderCredential`, `ProviderAccount`, and `CredentialPool` keyed addressability
- model list refresh, capability normalization, and `ModelCapabilityDescriptor` population
- cache-marker translation from `CacheMarker` candidates to provider-native syntax
- tokenizer dispatch, `TokenSource` accuracy hierarchy, and `(block_id, tokenizer_id)` keying
- per-call attribution through `TokenUsageRecord`
- cost computation as a derived projection over per-call records and pricing snapshots
- multimodal usage accounting
- `ProviderRuntimeSnapshot` and `ProviderOfferingProjection` exposure consumed by File 16
- provider-layer events emitted to the canonical bus and ledger
- the secret boundary, sensitivity classification, and redaction rules
- settings dimensions every mechanism in this file exposes

This file does not define:

- model selection, `ModelProfile` resolution, workload classification, or `FallbackPolicy` actions — File 16 owns those
- routing, `RunIntent` field meanings, or router context policy — File 03 owns those
- run lifecycle, the capability-call pipeline, cancellation primitives, or hook execution — File 04 owns those
- the `CapabilityDeclaration` field set, registry operations, or runtime registration — File 05 owns those
- policy evaluation, approvals, leases, or typed-confirmation — File 06 owns those
- tool-surface composition or zoning — File 07 owns those
- the `Block` schema, `BlockKind` catalogue, or commit boundary — File 08 owns those
- the `ExecutionLedger` row schema or the `EventEnvelope` field set — File 10 owns those; this file specifies what per-call attribution the ledger must record
- the version graph or `ContextVersion` mechanics — File 11 owns those
- retrieval indexes, knowledge-base construction, or retrieval-augmented generation — File 12 owns those
- the model-request assembly algorithm, token-counting budget, or the `CacheMarker` candidate-production rules — File 13 owns those; this file consumes those outputs
- memory recall, store, or consolidation — File 14 owns those
- the settings source stack, scope resolution, or profile layering — File 15 owns those
- credential vault internals, OS keyring integration, secret encryption, or trust-state cryptography — File 22 owns those; this file specifies the vault-reference contract and the namespace
- MCP transport mechanics for tool servers — File 36 (MCP and External Integrations) owns those; this file is for model/inference providers, not tool providers
- sandbox primitives, process isolation, or sandboxed-runtime details — File 23 owns those
- physical storage layout, on-disk schema, or index strategy — File 20 owns those
- cross-device sync transport — File 21 owns those
- UI rendering of provider lists, model pickers, usage dashboards, billing views, rate-limit indicators, or credential management surfaces — File 37 and File 38 own those
- packaging, installer behavior, or platform integration — File 43 owns those
- concrete provider names, model names, exact pricing values, exact tokenizer crate identifiers, or vendor-specific wire-format details outside the boundaries listed in §6.5

## Source Resolution

This file resolves provider-adapter mechanics, request execution, rate-limit state, usage accounting, provider error classification, transport-level retry, and provider-native capability exposure material into one boundary: how Atlas talks to external model providers without leaking provider-specific mechanics into the rest of the runtime.

Resolved design:

- `ProviderAdapter` is the only contract through which model-bound work crosses into provider transport. Routing, execution, model selection, context assembly, and the ledger consume this layer through provider-invariant primitives.
- `ProviderProfile` is a declarative shape that lets one transport implementation serve many providers that share a wire format. Hand-coded adapters remain valid; the profile is the recommended path, not the required path.
- Streaming, error classification, retry, health, rate limits, credentials, capability normalization, cache rendering, and tokenizer dispatch all carry typed cross-provider primitives so that File 16, File 04, File 10, File 13, and File 15 never branch on provider identity.
- Provider-specific wire syntax, header injection, model-list shape, error-code mapping, parameter clamping rules, and tokenizer libraries are adapter responsibilities. The canonical layer defines the contract these adapters meet.
- Per-call attribution is keyed by `(provider_id, model_id, tokenizer_id, role)` and stored as typed records. Cost is never a stored unkeyed scalar — it is derived from records and pricing snapshots at audit, projection, or display time. This obeys `core.explicit-rejections` (File 01 §8).
- Provider health, rate-limit state, and capability snapshots are runtime projections over the adapter's accumulated observations. File 16 reads them as `ProviderRuntimeSnapshot` and `ProviderOfferingProjection`; File 17 owns their content.
- Transport-level retry stays inside the provider layer. Model-level fallback to a different model returns through File 16's `FallbackPolicy`. The boundary is sharp: same `(provider_id, model_id)` retry happens here; switching `(provider_id, model_id)` is File 16's decision.

## 1. Provider Layer

Anchor: `provider.provider-layer`

Atlas has one Provider Layer between the runtime and external model/inference providers.

It owns:

- adapter contracts and the declarative profile shape that builds most of them
- request execution, parameter serialization, streaming transport, and response normalization
- typed provider error classification and transport-level retry
- credentials, accounts, and credential-pool rotation within an account
- rate-limit state, header-driven reconciliation, and pre-call admission control
- provider health, capability normalization, and model-list refresh
- cache-marker translation, tokenizer dispatch, and per-call usage records
- the runtime projections consumed by File 16

The layer has the following primitives:

- `WireFamily { family_id }` — the registry reference naming an adapter wire family without embedding provider-specific constants in canonical text

- `ProviderAdapter` — the typed contract every provider implementation must meet
- `ProviderProfile` — the declarative recipe most adapters are realized from
- `ProviderInstance` — a configured live binding of an adapter to credentials, account, base URL, and runtime overrides
- `ProviderRegistry` — the registry holding registered adapters, instances, and their runtime state
- `ProviderRequest`, `ProviderResponse`, and `ProviderCallOutcome` — the typed call envelopes and non-streaming outcome carried across the adapter boundary
- `ProviderStreamChunk` — the typed streaming-delta envelope
- `ProviderError` and `ErrorClassification` — the typed error vocabulary and per-error retry advice
- `ProviderHealth` — the runtime health state machine
- `RateLimitState` and `RateLimitSnapshot` — the canonical rate-limit accounting and reconciliation records
- `ProviderCredential`, `ProviderAccount`, and `CredentialPool` — the credential addressability model
- `ModelCatalogEntry` — the per-model record cached from `ProviderAdapter::refresh_models`
- `TokenSource`, `TokenizerId`, and `TokenCount` — the tokenizer dispatch and accuracy hierarchy
- `TokenUsageRecord` — the per-call attribution record
- `ModelPricing` and `PricingSnapshot` — the derived-cost inputs
- `ProviderRuntimeSnapshot` and `ProviderOfferingProjection` — the read-only projections exposed to File 16

These primitives carry the entire provider-invariant surface. Other specs consume them; they do not extend them with parallel constructs.

The file has two internal parts:

- Part A, Shared Provider Substrate: provider identity, profile and instance registration, credentials, accounts, credential pools, provider health, rate limits, retry, usage accounting, pricing snapshots, runtime and offering projections, events, settings, and source approval.
- Part B, Model-Call Adapter Family: `ProviderRequest`, `ProviderResponse`, `ProviderStreamChunk`, parameter serialization, cache-marker translation, tokenizer dispatch, model catalog, capability normalization, and model-call-specific events.

Future STT, TTS, image, embedding, video, and local-inference adapter families reuse Part A and define their own family-specific request and response contracts later; the deferred TTS adapter family is the named provider-layer home voice-synthesis output dispatches through. They are not forced into the model-call surface.

## 2. Boundaries with Adjacent Layers

Anchor: `provider.boundaries-with-adjacent-layers`

### 2.1 With File 16 (Model Strategy, Profiles, and Selection)

File 16 consumes three projections from this layer: `ModelCapabilityDescriptor` (per `(provider_id, model_id)`), `ProviderOfferingProjection` (provider/account availability, effective pricing, region, data handling), and `ProviderRuntimeSnapshot` (current health, rate-limit posture, in-flight capacity, credential state, known retryability). File 17 produces all three. File 17 does not select models, score candidates, or evaluate `ModelProfile`s.

File 16's `FallbackPolicy` consumes typed `ProviderError` variants defined in §10. Once a call exits this layer with one of those errors, model-level fallback is File 16's decision. Until then, transport-level retry against the same `(provider_id, model_id)` and credential-pool rotation within the same account stay inside this layer.

File 16's behavioral intents (`reasoning_posture`, `sampling_posture`, `output_length_posture`, `latency_posture`, and the resolved parameter values from §10.2 of that file) are consumed by `ProviderAdapter::build_request` and serialized to provider-native parameters per §8.

### 2.2 With File 04 (Execution and Run Model)

`run.call-pipeline` (File 04 §8.2) defines the capability-call pipeline; model-bound work that flows through that pipeline reaches this layer when a model invocation is dispatched. `run.cancellation` (File 04 §17.3) owns the cancellation primitive; this layer propagates the cancellation signal into adapter calls and stream consumers, and records partial usage on cancellation as specified in §9.4.

`run.boundary-rule` (File 04 §20.1) forbids provider retry and rate-limit handling in the execution layer. This file owns those mechanics. File 04 surfaces typed errors when transport-level retry exhausts; the execution layer chooses recovery from §20.2 of File 04.

### 2.3 With File 10 (Execution Ledger, Event Stream, and Hooks)

`ledger.entry-kinds` (File 10 §4) enumerates the canonical `LedgerEntryKind` catalogue; the model-call entries (`ModelCallStarted`, `ModelCallCompleted`, `ModelCallStreamingDelta`, `ModelCallFailed`, `ModelCallCancelled`, `ProviderHealthChanged`, `RateLimitSnapshotReconciled`) are canonical File 10 kinds, while the related provider-operational events (`ProviderModelsRefreshed`, `RateLimitHit`, `CapabilityProbed`, `CredentialRotated`, `ParameterClamped`, `CacheBreakDetected`, `TokenCountEstimationTelemetry`) register as `Custom { namespace: "provider" }` per §22.1 unless File 10 later promotes them; both sets are emitted by this layer. File 10 owns the entry shape; this file specifies what per-call attribution every model-call entry must carry (`TokenUsageRecord` per §18, cost computed from per-model pricing per §19, never an unkeyed scalar per `core.explicit-rejections`, File 01 §8).

`ledger.sensitivity-aware-persistence-retention` (File 10 §10)'s sensitivity classification (`Public`/`Sensitive`/`Secret`) governs persistence; this file specifies which provider-layer events carry which sensitivity, and the rule that raw credentials, raw request bodies, and resolved secret material never enter durable persistence.

### 2.4 With File 13 (Context Assembly and Compaction)

`context.token-counting` (File 13 §10) owns token counting at the assembly boundary (request-size estimation against the active model's request limits) and produces the `BudgetReport`. File 17 owns the tokenizer dispatch table, the per-model tokenizer identity, and the provider-exception list. The `(block_id, tokenizer_id)` LRU cache contract is shared: File 13 populates and consumes it for assembly; File 17 populates it during parse with provider-reported counts when available, which take precedence over local-tokenizer counts. The `tokenizer_id` namespace is defined here (§17).

`context.cache-marker-candidates` (File 13 §11) produces logical `CacheMarker` candidates with provider-invariant anchors, stability metadata, sensitivity eligibility, fingerprints, and source references. `provider.cache-marker-translation` (File 17 §16) translates those candidates to provider-native cache behavior, applies provider-declared marker limits and cache constraints, and reports cache hit accounting back through `TokenUsageRecord`. Minimum cacheable size and retention behavior belong to provider offering or adapter policy metadata, not `ModelCapabilityDescriptor`.

### 2.5 With File 15 (Settings, Profiles, and Scope Resolution)

All provider-layer settings (preferred providers, excluded providers, excluded models, custom provider configurations, per-account credential references, rate-limit budgets, retry caps, cache enablement and retention preference, tokenizer overrides, model-catalog maintenance policy, cost-tracking opt-in, unknown-cost policy, parameter clamping defaults) are declared as `SettingDefinition`s and resolved through File 15's source stack. File 17 reads resolved values; it does not implement a second cascade.

Secret material is stored in the vault per `settings.secret-boundary` (File 15 §10). This file specifies the vault namespace and the access pattern; vault internals belong to File 22.

### 2.6 With File 03 (Routing and Dispatch)

File 03 owns routing semantics, `RunIntent` field meanings, and `RouteRecord` production. The router consumes `ModelCapabilityDescriptor` and `ProviderRuntimeSnapshot` projections to inform routing decisions and to populate the initial `model_route`. The router itself, when it requires a model-bound call, reaches this layer through the same `ProviderAdapter` path as any other model-bound step.

### 2.7 Boundary Summary

This file owns the contract every provider implementation meets, the typed primitives every other layer consumes, the runtime state machine over health/rate-limits/credentials, the per-call attribution schema, the tokenizer dispatch table, the cache translation, and the settings dimensions every provider-layer behavior exposes. It does not own selection, routing, the ledger row shape, vault internals, retrieval, context assembly, sync, storage, or UI.

## 3. `ProviderAdapter`

Anchor: `provider.provider-adapter`

### 3.1 Definition

A `ProviderAdapter` is a typed binding that connects Atlas's runtime to one model/inference provider's transport surface. Every model-bound call exits the runtime through a `ProviderAdapter` and returns through one.

An adapter is:

- contract-driven — its method set is closed canonical
- inspectable — its `provider_id`, `display_name`, declared capabilities, registered models, and runtime state are queryable through the registry
- composable — adapter implementations may be hand-coded or realized from a `ProviderProfile`
- substitutable — two adapters that meet the contract are interchangeable for routing, selection, execution, and accounting purposes
- versionable — adapter implementations carry a `version` and a `compatibility` declaration; version updates pass through the source-approval flow defined by File 06 when the source is a plugin or extension

It is not:

- a model
- a credential
- a provider account
- an instance
- a registry
- a runtime state machine

### 3.2 Required Methods

Every `ProviderAdapter` must support the following typed operations. Method names below are canonical labels; implementation-language signatures are an implementation concern.

- `provider_id` — stable provider identifier
- `display_name` — human-readable name
- `wire_family` — `WireFamily { family_id }`, a provider-registry reference to the adapter wire family this implementation belongs to
- `validate_configuration` — verify the configured base URL, account, credential reference, and feature flags are coherent without performing a remote call
- `validate_credentials` — perform a minimal remote check (typically the model-list endpoint) and return success or a typed `ProviderError`
- `list_models` — return the current `ModelCatalogEntry` set from the registry's projection
- `refresh_models` — re-query the provider's model catalog and update the registry projection
- `capabilities` — return the `ModelCapabilityDescriptor` for one `(provider_id, model_id)` pair, populated from provider-reported facts, adapter-shipped fallback, and user-supplied overrides per §15
- `build_request` — transform the assembled `ProviderRequest` (carrying File 13 assembly output, File 16 behavioral intents, and File 17 cache-marker rendering) into the provider-native wire payload
- `complete` — execute a non-streaming model call, returning `ProviderCallOutcome::Completed { response }` or `ProviderCallOutcome::Cancelled { usage }`; genuine provider or transport failure returns `ProviderError`
- `stream` — execute a streaming model call, returning a typed stream of `ProviderStreamChunk` values with exactly one completed, cancelled, or error terminal
- `classify_error` — return the `ErrorClassification` for a provider-specific error value, including `retryable`, `rate_limited`, `retry_after_ms`, `error_code`, and `recovery_advice`
- `render_cache_markers` — translate File 13's logical `CacheMarker` candidates into provider-native cache annotations, capping to declared marker limits with typed diagnostics on overflow
- `count_tokens` — count tokens for a given content fragment, model, and tokenizer identity, using provider-native counting when available and falling back to the local hierarchy in §17
- `rate_limit_state` — return the current `RateLimitState` projection for the requested `RateLimitScope`
- `reconcile_rate_limits` — consume a `RateLimitSnapshot` parsed from response headers and update the per-scope state
- `runtime_snapshot` — return the `ProviderRuntimeSnapshot` projection consumed by File 16
- `offering_projection` — return the `ProviderOfferingProjection` consumed by File 16
- `close` — release any per-instance resources (HTTP clients, subprocesses for subscription wrappers, file watchers, OAuth refresh timers)

### 3.3 Optional Methods

Adapters may expose:

- `get_retry_advice` — provider-specific retry direction beyond the generic `ErrorClassification` (used when the provider's documentation differs materially from the canonical advice)
- `ping` — an explicit connectivity test invoked by user-triggered diagnostics (never as a scheduled health probe)
- `account_usage` — return a normalized `AccountUsageSnapshot` for providers that expose account-level usage endpoints
- `fetch_recommended_models` — return a curated subset of available models when the provider exposes such a recommendation
- `discover_capabilities` — perform probes the provider supports for capability normalization beyond the model list endpoint

### 3.4 Explicit Non-Fields

The adapter contract must not carry:

- raw credentials in any persistent field — credentials flow in at the point of use and leave with the request
- a `cost_cents` scalar — cost is derived per §19
- a free-form retry policy struct — retry is governed by `ErrorClassification` and §11
- a hardcoded model-name branching table — capability-driven dispatch is the canonical pattern per `core.explicit-rejections` (File 01 §8) and the constraint restated in §25 of this file
- provider-specific endpoint paths or wire-format identifiers as user-facing constants — they live in the adapter implementation, not the contract

### 3.5 Normalization Responsibility

Provider adapters are the only layer permitted to know provider-specific wire shapes, model-name conventions, response-field naming, error-code mapping, header injection rules, parameter clamping rules, and tokenizer-library bindings. Every other layer of Atlas reasons over the typed primitives this contract exposes. A request that reaches the adapter is provider-invariant; a request that leaves the adapter is provider-native. The reverse is true on the response path.

## 4. `ProviderProfile`

Anchor: `provider.provider-profile`

### 4.1 Definition

A `ProviderProfile` is a declarative description of a provider's transport behavior. It lets one transport implementation serve many providers that share a wire family.

A profile is:

- registered as provider-registry source artifacts; plugin, imported, or extension profiles pass through File 06 source approval before activation
- composable with adapter-shipped extensions for provider-specific quirks
- typed — every field is canonical or registered

A profile is not:

- a substitute for the `ProviderAdapter` contract — every adapter realized from a profile still implements the full contract
- a credential — it references the credential namespace, never the material
- a `ModelProfile` — File 16 owns that primitive

### 4.2 Required Fields

Every `ProviderProfile` must carry:

- `profile_id`
- `display_name`
- `wire_family` — `WireFamily { family_id }`, registered by an adapter implementation or approved profile source
- `base_url_default`
- `auth_kind` — `ApiKey`, `BearerToken`, `Oauth { flow }`, `SignedRequest { signer_id }`, `Subscription { wrapper_id }`, `NoAuth`, or `Custom { namespace, name }`
- `credential_namespace` — the vault namespace pattern used for credentials bound to instances of this profile
- `model_catalog_source` — provider-reported catalogue source descriptor, adapter-shipped static catalogue reference, user-supplied catalogue, or hybrid provider-then-fallback source; carries provenance and freshness diagnostics
- `streaming_transport` — `Sse`, `ChunkedHttp`, `WebSocket`, `Ndjson`, `Subprocess`, or `Custom { namespace, name }`
- `capability_query_strategy` — how `ModelCapabilityDescriptor` fields are populated when the provider does not report them natively
- `cache_marker_strategy` — registered strategy for translating logical cache candidates into provider-native behavior
- `parameter_mapping` — the rule set that maps provider-invariant behavioral intents to provider-native parameters

### 4.3 Optional Fields

Profiles may declare:

- `compatibility_flags` — typed feature toggles for provider-specific behavior categories such as role-field mapping, unsupported-parameter omission, cache-placement rules, model-id normalization, identity-header rules, and surrogate sanitization
- `default_request_headers` — static safe header names and non-secret literal values; secret-bearing values must be `SecretRef`s resolved only at request time
- `request_header_rules` — typed conditional header rules whose secret-bearing values are `SecretRef`s and whose diagnostics expose names and safe descriptions, never values
- `fixed_parameter_values` — provider-managed constants that must not be sent as user-controlled parameters
- `fallback_models` — adapter-default fallback chain inside the same provider, used only when File 16 authorizes same-provider fallback
- `error_code_map` — the typed mapping from provider-reported error codes to canonical `ProviderError` variants
- `tokenizer_binding` — the canonical `TokenizerId` to dispatch for this provider's models
- `extension_fields` — namespaced metadata that does not alter canonical field meaning

### 4.4 Profile-Driven and Hand-Coded Adapters

Most providers reduce to a profile-driven adapter: one registered `WireFamily { family_id }` plus base URL, authentication, headers, parameter mappings, and compatibility flags. Provider-specific behavior that cannot be expressed declaratively rides on registered transport hooks with diagnostics.

Hand-coded adapters remain valid for transports that do not fit any registered wire family, including subprocess subscription wrappers and custom signed-request stacks. Hand-coded adapters meet the same `ProviderAdapter` contract and produce the same projections.

## 5. `ProviderInstance` and `ProviderRegistry`

Anchor: `provider.provider-instance-provider-registry`

### 5.1 `ProviderInstance`

A `ProviderInstance` binds a `ProviderAdapter` (typically realized from a `ProviderProfile`) to:

- a `provider_id` namespaced for this install
- a `display_name`
- a `base_url`
- a `ProviderAccount` reference
- a `credential_ref` resolved through the vault
- per-instance overrides (custom headers, proxy, mTLS configuration, geographic region, model_id allowlist/blocklist, custom tokenizer override)
- a `runtime_environment` — the typed sandbox or process context for subscription wrappers

Two instances of the same profile with different `provider_id`s share no mutable runtime state. Their credentials, rate-limit accounting, health state, and usage records are addressed independently.

### 5.2 `ProviderRegistry`

The `ProviderRegistry` is the projection over registered adapters, profiles, instances, and their accumulated runtime state. It supports:

- adapter and profile registration and unregistration
- instance creation, reconciliation, and removal
- credential lookup through the vault namespace
- model-catalog lookup by `(provider_id, model_id)`
- capability lookup by `(provider_id, model_id)`
- rate-limit state lookup by `RateLimitScope`
- runtime-snapshot lookup by `provider_id`
- offering-projection enumeration consumed by File 16

Adapter and profile registration performs registration-time validation that the implementation meets the full `ProviderAdapter` contract, including the secret-scrubbing requirement in §23.4; an implementation that fails validation is rejected rather than activated.

The registry is event-driven. Registration, unregistration, credential rotation, model-catalog refresh, capability refresh, rate-limit reconciliation, and health transitions emit canonical events per §22.

The registry is not an independent source of provider truth. Capability data is provider-reported, adapter-fallback, or user-supplied; pricing data is provider-reported, user-supplied, or unknown; rate-limit data is header-reconciled or user-configured. The registry caches and exposes these facts with full provenance.

## 6. Provider Sourcing

Anchor: `provider.provider-sourcing`

### 6.1 Source Classes

Every provider instance is sourced from one of:

- `Builtin` — adapters shipped with Atlas
- `Plugin { plugin_id }` — adapters bundled in a plugin and subject to the source-approval flow from `policy.source-approval-flow` (File 06 §9)
- `UserDefined` — adapters configured by the user through the canonical `provider.register` capability surface
- `ImportedBundle { bundle_id }` — adapters carried inside a portable bundle import

### 6.2 Subscription Wrappers

Subscription-wrapper providers (CLI binaries or seat-based subscription APIs that wrap an underlying inference provider) implement `ProviderAdapter` like any other provider. They are not a separate tier, are not handled through a separate path, and use the same model-catalog refresh, capability normalization, rate-limit accounting, usage attribution, error classification, and credential addressability as direct-API providers.

Wrapper-specific behavior (subprocess lifecycle, stdio normalization, per-CLI usage-file scanning, session-resume conventions, multi-account isolation via shadow-home directories or `HOME` overrides) is implemented inside the adapter or its profile, not in the canonical layer.

### 6.3 Custom Providers and Registered Wire Families

Custom providers are registered through the canonical `provider.register` capability surface declared in §22.6. A custom provider may select an existing `WireFamily { family_id }` profile with a custom `base_url` or register a new profile. Unknown provider identifiers receive a synthesized `ModelCapabilityDescriptor` from adapter-shipped fallback only where the profile declares safe fallback behavior. The descriptor carries `Unknown` for capability facts the adapter cannot determine; selection and assembly treat `Unknown` per `model.normalization-refresh` (File 16 §3.4).

### 6.4 Gateway Compatibility

Third-party gateways and proxies that claim compatibility with a registered wire family may implement discovery while stubbing or partially implementing inference. Adapters must detect such gateway incompatibilities through typed signals and short-circuit retry rather than burning the configured retry budget. Gateway-incompatibility detection produces a typed `ProviderError::CapabilityMismatchDiscovered` per §10 so File 16 can fall back to a different model or instance.

### 6.5 Excluded Provider-Specific Material

This file does not embed concrete provider names, exact endpoint paths, exact wire field names, exact header strings, exact tokenizer crate identifiers, exact model identifiers, or exact pricing values in canonical text. Those facts live in adapter implementations, source references, and registered profile records. Canonical text uses provider-invariant language with backticked identifiers for canonical primitives.

## 7. `ProviderRequest`

Anchor: `provider.provider-request`

### 7.1 Definition

A `ProviderRequest` is the typed provider-invariant call envelope carried into `ProviderAdapter::build_request`.

It carries:

- the resolved `(provider_id, model_id, account_id)` identity
- the assembled model request from `context.model-request` (File 13 §2) with semantic regions preserved
- `assembly_snapshot_ref`, `sensitivity_summary`, `data_boundary_decision_ref`, and provider/account boundary requirements needed to prove the request is authorized before serialization
- the resolved behavioral intents from `model.behavioral-intent-parameter-resolution` (File 16 §10) (`reasoning_posture`, `sampling_posture`, `output_length_posture`, `latency_posture`, `cost_posture`, `cache_continuity_preference`, `structured_output_posture`, parameter overrides resolved per File 15)
- the rendered or pending `CacheMarker` candidates from `context.cache-marker-candidates` (File 13 §11)
- the `RunIntent` and `Run` cross-references required for ledger attribution per `ledger.boundaries-with-adjacent-layers` (File 10 §2.1)
- the active `policy_snapshot_ref`, `settings_snapshot_ref`, `world_snapshot_ref`, and `registry_snapshot_ref` per `ledger.cross-references` (File 10 §3.6)
- the role tag for usage attribution — one of the closed canonical workload roles enumerated in §18.3 (matching `model.model-workload-requirements` (File 16 §5.2)), or a registered `Custom { namespace, name }`
- the `cancellation_signal` propagated from File 04
- the `idempotency_key` for safe transport-level retry

The request must not carry resolved secret material. Credential resolution happens inside the adapter at the point of use through the vault reference per §14.

### 7.2 Parameter Resolution and Clamping

`ProviderAdapter::build_request` maps behavioral intents to provider-native parameters using the profile's `parameter_mapping` or the hand-coded equivalent. The adapter applies provider-specific clamping when the resolved value is incompatible with the target model (for example, when the target model requires a fixed parameter or rejects an unsupported parameter family). Every clamp emits a `ParameterClamped` event per §22 with the requested intent, the resolved value, the clamp applied, and the diagnostic reason. Clamping is observability, not silent rewriting.

When a required behavioral intent cannot be honored at all (the model does not support a required modality, structured-output mode, or reasoning posture), the adapter rejects the request with `ProviderError::CapabilityMismatchDiscovered` so File 16 can reselect.

### 7.3 Multimodal Payload Assembly

Multimodal inputs (images, audio, video, file attachments) cross the adapter boundary as typed references that the adapter serializes to the provider's expected payload form (inline base64, file IDs, URL references, multipart bodies). Adapters must preserve content sensitivity classifications per `ledger.event-envelope` (File 10 §5.2); sensitive material that the active provider must not see fails at the boundary with `ProviderError::PolicyOrDataBoundaryConflict` rather than being silently transmitted.

### 7.4 Tool and Callable Declarations

Provider-native callable declarations (the tool array carried with the model request) are serialized by the adapter from the `ToolSurface` snapshot per `surface.surface-relevant-events` (File 07 §13). The adapter must respect the model's declared `native_callable_support` per `model.model-capability-descriptor` (File 16 §3.2); when the model does not support native tool calling, the adapter either rejects the request or, if the active `ModelProfile` permits `parser_fallback`, emits a typed diagnostic and lets the response parser recover tool calls from model text per `model.model-capability-descriptor` (File 16 §3.2). The response parser is one shared component; the active parser format is a registered format identity resolved through settings per `model.settings` (File 16 §14), never a per-adapter fork. A resolved format that conflicts with the descriptor's declared `parser_tool_call_fallback_support` set fails as `ProviderError::CapabilityMismatchDiscovered` rather than dispatching silently.

## 8. Parameter Serialization

Anchor: `provider.parameter-serialization`

### 8.1 Rule

Every provider-native parameter is produced by `ProviderAdapter::build_request` from the resolved behavioral intent. No canonical Atlas-level layer above this one knows the provider's parameter names.

### 8.2 Mapping Discipline

The profile's `parameter_mapping` (or the hand-coded adapter equivalent) declares the per-parameter rule from one of:

- `Identity` — pass through with renaming only
- `Bounded { min, max }` — clamp to provider-declared bounds
- `Fixed { value }` — adapter overrides the requested value with a provider-required constant (records the substitution as a `ParameterClamped` diagnostic)
- `Omit` — adapter drops the parameter entirely (provider would reject it)
- `Mapped { table }` — adapter uses a typed lookup table (for example, the canonical `reasoning_effort` enum `Low|Medium|High|Max` to a provider-specific value set)
- `Synthesized { synthesizer_id }` — adapter computes the provider-native value from multiple inputs (for example, reasoning budget tokens from posture plus model class)
- `Conditional { conditions, branches }` — adapter selects among rules based on model identity or compatibility flags
- `RejectIfRequired` — adapter rejects the request with `CapabilityMismatchDiscovered` when the parameter is required and the provider cannot serve it

Rules are inspectable, replayable, and auditable. Hidden conditional logic outside the declared mapping is forbidden.

### 8.3 Sensitive Quirks

Provider-specific behavioral defaults that affect correctness (role-field mapping, surrogate sanitization, unsupported-parameter suppression, identity-header rules, model-id normalization) are part of the adapter's responsibility and must produce typed diagnostic events whenever they alter the user's apparent request.

## 9. Call Outcomes and Streaming

Anchor: `provider.streaming`

For non-streaming calls, `ProviderCallOutcome` is the closed non-error outcome envelope:

- `Completed { response: ProviderResponse }` — the provider finished and returned a normalized response.
- `Cancelled { usage: TokenUsageRecord }` — the caller cancelled before provider completion; usage is partial, carries `stop_reason = CancelledByUser`, and carries no `error_class`.

`ProviderError` remains the failure channel. Cancellation is therefore representable without fabricating an empty response or misclassifying caller intent as provider failure.

### 9.1 `ProviderStreamChunk`

`ProviderAdapter::stream` returns a typed stream of `ProviderStreamChunk` values. The canonical chunk variants, plus registered typed extensions, are:

- `StreamStarted { provider_request_id, started_at, cache_markers_sent }`
- `TextDelta { text }`
- `ReasoningDelta { text, signature }`
- `ToolUseStarted { tool_use_id, tool_name }`
- `ToolUseArgumentsDelta { tool_use_id, partial_arguments }`
- `ToolUseCompleted { tool_use_id, arguments }`
- `RateLimitHeadersObserved { snapshot }`
- `PartialUsageObserved { usage_delta }`
- `StopReasonObserved { stop_reason }`
- `CompletionReceived { usage, stop_reason, finish_metadata }`
- `StreamCancelled { usage }` — terminal: the caller cancelled the stream mid-flight (§9.3), carrying the partial usage accumulated before the stop. Cancellation is a deliberate caller action, neither provider completion nor provider failure, so it has its own terminal distinct from both `CompletionReceived` and `StreamError`. It carries no `ProviderError`.
- `StreamError { error }`
- `Custom { namespace, name, payload }` for registered extensions

Adapters that consume non-SSE transports (chunked HTTP, WebSocket, NDJSON, subprocess stdio) normalize their provider-native event vocabulary into canonical variants or registered typed extensions. Provider-specific raw chunks stay inside adapters; extension chunks are provider-invariant, sensitivity-tagged, and registered before leaving the adapter boundary.

### 9.2 Streaming Discipline

- Every stream begins with `StreamStarted` and terminates with exactly one of `CompletionReceived` (the provider finished), `StreamCancelled` (the caller cancelled, §9.3), or `StreamError` (the provider/transport failed). Adapters must guarantee one and only one terminal chunk per stream. Cancellation is never surfaced as `StreamError`; it is recorded through the cancellation channel (§9.3), not as a provider fault.
- `RateLimitHeadersObserved` chunks fire when the provider returns updated headers mid-stream or as a streaming usage event. Adapters must surface them at parse time and call `reconcile_rate_limits` per §13.
- `PartialUsageObserved` chunks fire when the provider streams running usage counts (when the provider emits running usage totals or per-chunk usage events). The canonical block-level token-attribution algorithm specified in §17.5 consumes these.
- Mid-stream errors must be surfaced as `StreamError` with a typed `ProviderError` and must not be silently swallowed. Partial output captured before the error is delivered to File 04 per §17.3 retention rules.

### 9.3 Cancellation

The `cancellation_signal` carried on every `ProviderRequest` propagates into the stream consumer. On cancellation, the adapter closes the underlying transport (cancels the SSE consumer, sends an explicit cancel frame for protocols that support it, terminates the subprocess for wrapper providers), records the partial usage as a `TokenUsageRecord` with stop reason `CancelledByUser` (§18.5), and emits a terminal `StreamCancelled { usage }` chunk so consumers can settle their state.

Cancellation is a deliberate caller action, not a provider failure, and is treated as a distinct outcome end-to-end: it is not a `StreamError` (reserved for provider/transport faults, §10) or `CompletionReceived` (the provider did not finish). It carries no `ProviderError`; it never enters transport retry (§11.5) or model fallback (File 16 §9.2); and it does not affect provider health or error trends (§12/§21). Run-level cancellation records the action through File 10's `CancellationRequested`, `StreamCancelled` where partial streaming output is involved, and eventual `CancellationCompleted` entries. The model-call lifecycle records `ModelCallCancelled` — never `ModelCallCompleted` or `ModelCallFailed`. A buffered call cancelled before completion returns `ProviderCallOutcome::Cancelled`; the error channel remains reserved for genuine provider failures.

### 9.4 Partial Outputs

The runtime records partial outputs per the capability semantics defined in `run.cancellation` (File 04 §17.3) (`partial_output_meaningful` declarations). At the provider-layer boundary, the adapter is responsible for delivering whatever partial output was generated before cancellation through the stream, not for deciding whether to keep it.

### 9.5 Streaming Aggregation

High-frequency streaming events (`TextDelta`, `ReasoningDelta`, `ToolUseArgumentsDelta`, `RateLimitHeadersObserved` when emitted per chunk) are subject to the aggregation policy declared per `ledger.streaming-live-partials` (File 10 §12.3). The ledger records the aggregated `ModelCallStreamingDelta` entry rather than every chunk. Live UI consumers receive every chunk through the event bus.

## 10. Provider Error Classification

Anchor: `provider.provider-error-classification`

### 10.1 Closed Canonical Error Variants

Every provider error is one of the following canonical variants. Every adapter must produce one of these variants for any provider failure that exits the adapter boundary.

- `AuthenticationFailed { provider_id, account_id, message }`
- `NotAuthenticated { provider_id, account_id }`
- `CredentialExhausted { provider_id, account_id, exhausted_until }` — used when every key in the active `CredentialPool` is rate-limited or revoked
- `ProviderUnavailable { provider_id, message, retry_advice }`
- `ProviderDegraded { provider_id, message, retry_advice }` — soft signal accompanying degraded responses without full failure
- `ModelUnavailable { provider_id, model_id, available_at }`
- `RateLimited { provider_id, model_id, scope, retry_after_ms, limit_type }`
- `ContextTooLargeForSelectedModel { provider_id, model_id, tokens_supplied, tokens_supported }`
- `RequestRejectedByProvider { provider_id, message, error_code }`
- `InvalidRequest { provider_id, field, message, details }`
- `CapabilityMismatchDiscovered { provider_id, model_id, required_capability, supported }`
- `PolicyOrDataBoundaryConflict { provider_id, model_id, reason }`
- `NetworkError { provider_id, message, retry_advice }`
- `TimeoutError { provider_id, phase, retry_advice }`
- `ServiceOverloaded { provider_id, retry_advice }`
- `StreamInterrupted { provider_id, phase, retry_advice }`
- `ProviderInternalError { provider_id, message }`
- `ProviderSpecificError { provider_id, provider_error_code, provider_error_class, scrubbed_message, http_status?, retry_after?, classified_as: ErrorClassification, classification_confidence }` — the declared escape hatch for a provider failure that maps cleanly to none of the named variants above (per the closed-canonical extension path, `core.closed-canonical` (File 01 §6.16)). It still carries a `classified_as: ErrorClassification`, so downstream behavior never depends on the raw provider strings. `scrubbed_message` is secret-scrubbed per §10.5; `provider_error_code` and `provider_error_class` are preserved for telemetry; `classification_confidence` records how certain the adapter's classification is.

This catalogue must align exactly with the typed error vocabulary `model.fallback-policy` (File 16 §9.2) consumes. `RateLimited`, `ModelUnavailable`, `CapabilityMismatchDiscovered`, `ContextTooLargeForSelectedModel`, `RequestRejectedByProvider`, `ProviderUnavailable`, and `PolicyOrDataBoundaryConflict` are the File 16 fallback inputs; the remaining variants are transport-level and stay inside this layer until they exhaust per §11. A `ProviderSpecificError` routes by its `classified_as.recovery_advice` like any other variant.

Fallback and retry logic consume the `ErrorClassification` (§10.2), never raw provider strings. Every variant — including `ProviderSpecificError` — yields one, so an unrecognized provider failure is classified, not passed through untyped.

### 10.2 `ErrorClassification`

Every typed error carries an `ErrorClassification` produced by `ProviderAdapter::classify_error`. It declares:

- `retryable` — boolean, authoritative for transport-level retry per §11
- `rate_limited` — boolean, true only when the error is a rate-limit error and the retry direction is to back off rather than to fail
- `retry_after_ms` — explicit delay before the next attempt when provider-suggested
- `error_code` — provider-reported code preserved for telemetry
- `recovery_advice` — typed enum from `BackoffAndRetry`, `RotateCredential`, `RefreshAuth`, `StripUnsupportedParameter`, `ReconcileRateLimits`, `WaitForReset`, `FailoverToDifferentModel`, `FailoverToDifferentProvider`, `RejectAndReturnToCaller`, or `Custom { namespace, name }`
- `severity` — `Fatal`, `Transient`, or `Unknown`. `Fatal` takes priority when patterns co-occur; an error matching both an authentication signal and a transient signal is `Fatal`. This prevents silent retries through authentication failures.

`ErrorClassification` is the only retry-direction signal the retry loop consults. Hidden classification outside the typed advice is forbidden.

### 10.3 HTTP Status and Provider Code Mapping

Adapters map provider-reported HTTP status codes and error codes to the canonical variants per the profile's `error_code_map`. The mapping is inspectable. Provider-specific quirks (in-band credit-exhaustion messages, gateway-stubbed responses with success codes, error bodies that disagree with HTTP status) are normalized inside the adapter.

### 10.4 Retry-After Extraction

Adapters extract `retry_after_ms` — the wait before the next attempt for the current response — from typed provider sources in priority order:

1. the canonical `Retry-After` header when present (typically on a `429`) — the provider's explicit instruction for this rejection, in either delta-seconds or HTTP-date form (an HTTP-date is reduced against the response `Date` to the wait, equivalently an absolute instant per §13.4, and range-clamped per §13.7); when both `Retry-After` and reset headers are present, `Retry-After` controls the immediate retry wait
2. provider-specific reset headers when the provider exposes typed reset hints
3. provider-reported retry hints in the error body
4. profile-declared policy for the error class
5. `None`, when no signal exists

This precedence governs the per-response retry/block wait only. Provider-specific reset headers still feed the proactive `(scope, window, dimension)` reset state (§13.4/§13.5): a normal response usually carries no `Retry-After`, so its reset headers are the reset signal; a `429` may carry `Retry-After` for the immediate block deadline (§13.6) and reset headers that reconcile the window state. Every extracted value is range-clamped (§13.7) so a hostile or absurd value cannot park or panic the retry path.

The runtime does not treat retry waits as correctness logic. Provider reset hints are respected unless the user cancels or policy permits explicit override.

### 10.5 Secret Scrubbing

`ProviderError` instances must not carry resolved credentials, raw request bodies, or unredacted user content. Adapters scrub provider-reported error payloads before producing the typed variant. The error message field is `Sensitive` per `ledger.sensitivity-aware-persistence-retention` (File 10 §10) by default; carrying `Secret`-classified content in an error rejects at the ledger boundary.

## 11. Transport-Level Retry and Backoff

Anchor: `provider.transport-level-retry-backoff`

### 11.1 Retry Boundary

Retry inside this layer covers the same `(provider_id, model_id, account_id)` identity. Switching `(provider_id, model_id)` is File 16's `FallbackPolicy` decision and exits the retry loop with the typed error.

### 11.2 Retry Discipline

Every transport-level retry obeys:

- the `retryable` field on the call's `ErrorClassification` is authoritative
- when `retry_after_ms` is provider-suggested, the runtime waits at least that long
- when no provider-suggested delay exists, the runtime computes the next delay through a typed strategy (`ExponentialBackoff { initial_ms, multiplier, cap_ms, jitter_pct }`, `Fixed { delay_ms }`, `DecorrelatedJitter { initial_ms, cap_ms }`, or `Custom { namespace, name }`)
- the per-error-class retry cap is configurable through settings per §24
- the active retry strategy and per-error-class caps are inspectable and recorded on the `ModelCallStarted` ledger entry for replay

### 11.3 Strategies by Error Class

- `RateLimited` — `WaitForReset` plus `BackoffAndRetry` when no concrete reset hint is available
- `ServiceOverloaded`, `NetworkError`, `TimeoutError`, `StreamInterrupted`, `ProviderInternalError` — `BackoffAndRetry` with a settings/profile-selected strategy
- `AuthenticationFailed`, `NotAuthenticated` — `RefreshAuth` once per call; if refresh fails or is unsupported, fail without retry
- `CredentialExhausted` — `RotateCredential` through the `CredentialPool`; if every credential is exhausted, fail with the typed variant for File 16 to consume
- `ContextTooLargeForSelectedModel` — non-retryable at the transport layer; surface to `run.boundary-rule` (File 04 §20.1) for context-layer recovery
- `InvalidRequest`, `RequestRejectedByProvider`, `CapabilityMismatchDiscovered`, `PolicyOrDataBoundaryConflict` — non-retryable; surface to caller
- `ModelUnavailable`, `ProviderUnavailable` — non-retryable at the transport layer in the sense of same-`(provider, model)`-retry; surface for File 16

### 11.4 Idempotency

The `idempotency_key` carried on every `ProviderRequest` lets the adapter coalesce duplicate retries against providers that support idempotency tokens. Adapters that do not support provider-side idempotency rely on the runtime's retry-safe semantics: the same `idempotency_key` produces the same `ledger_entry_id` for the eventual successful call.

### 11.5 Hard Stops

Retry never converts a `Fatal` `ErrorClassification` into a `Transient` one. Retry never proceeds when the cancellation signal is active. Retry never exceeds the configured cap. Retry never blocks indefinitely; every retry wait is an individually killable execution unit and every backoff has a finite configurable ceiling. A typed cancellation outcome (`ProviderCallOutcome::Cancelled` or the `StreamCancelled` terminal, §9.3) terminates the attempt sequence outright: it is not retried, does not carry a `Transient` classification, and does not escalate to model fallback (File 16 §9.2).

## 12. `ProviderHealth`

Anchor: `provider.provider-health`

### 12.1 Definition

`ProviderHealth` is the per-`provider_id` runtime state machine consumed by `ProviderRuntimeSnapshot` and ultimately by File 16's selection algorithm to deprioritize `Degraded` providers (still attempted, §12.2) and skip `Unhealthy` ones (disqualified by default, §12.2).

### 12.2 States

- `Healthy` — recent calls have succeeded
- `Degraded { since, contributing_failures }` — recent failures observed but the provider is still attempted with logging
- `Unhealthy { admission_block_reason, contributing_failures, last_failure, retry_after_hint }` — calls are disqualified by default with `ProviderUnavailable`, while explicit diagnostics or user-directed bypass may attempt one call where policy allows
- `Unknown` — no recent observations (newly registered, just reconnected, after restart before any call)

### 12.3 Transitions

- successful call → `Healthy` once the configured recovery threshold is met (a single success by default; the required consecutive-success count is a §24 recovery-hysteresis setting, not a hardcoded mandate), contributing_failures reset
- consecutive failures whose `ErrorClassification` (§10.2) marks them transient provider/transport availability faults — `NetworkError`, `TimeoutError`, `ProviderUnavailable`, `ServiceOverloaded`, `StreamInterrupted`, and `ProviderInternalError` — increment the contributing counter; the classification, not a hardcoded variant list, is authoritative, so any variant an adapter classifies into this availability class contributes
- crossing the configured `degraded_threshold` (per §24) transitions to `Degraded`
- crossing the configured unhealthy-failure policy transitions to `Unhealthy` with diagnostic retry guidance derived from provider hints and settings
- `RateLimited`, `ModelUnavailable`, `AuthenticationFailed`, `InvalidRequest`, `ContextTooLargeForSelectedModel`, `CapabilityMismatchDiscovered`, `PolicyOrDataBoundaryConflict`, and `RequestRejectedByProvider` do not contribute to health — they are accounted to rate-limit, model-availability, credential, request-shape, or compatibility concerns respectively
- a cancellation (a `StreamCancelled` terminal / `ModelCallCancelled` / buffered cancellation outcome, §9.3) is neither a successful call nor a contributing failure: it does not reset health to `Healthy` (a caller-initiated stop is not evidence the provider is healthy), does not increment the contributing counter, and leaves provider health unchanged
- health transitions are observed only at a genuine call outcome: a buffered call's returned result, or a stream's terminal chunk (`CompletionReceived` / `StreamError`). A streaming call's health is not recorded at stream-open before the terminal is known, so a stream cancelled or interrupted after opening cannot mark an otherwise-unhealthy provider `Healthy`
- recovery from `Unhealthy` is demand-triggered and single-flight, symmetric to admission-control probing (§13.6): when a required call finds no non-`Unhealthy` provider remaining, or once the `retry_after_hint` has elapsed on the monotonic baseline the runtime captured at the `Unhealthy` transition (§13.3 — never a wall-clock read), the runtime admits exactly one in-flight probe call past the disqualification; only its genuine terminal outcome transitions health (a success returns `Healthy` per the configured recovery threshold; a contributing failure keeps `Unhealthy` and re-seeds `retry_after_hint`), and no second probe is admitted while one is in flight
- explicit user reset through the `provider.reset_health` capability returns the state to `Healthy`

### 12.4 No Active Health Pings

The runtime does not poll providers for health on a schedule. Active probes (`ProviderAdapter::ping`) exist only as a user-triggered diagnostic. Scheduled health pings are explicitly rejected per §25. Model-catalog refresh is the implicit connectivity check for providers that expose a model-list endpoint.

### 12.5 Health Snapshot in `ProviderRuntimeSnapshot`

`ProviderRuntimeSnapshot` carries the current `ProviderHealth` value, the `contributing_failures` counter, the last typed error observed, and any provider retry hint when `Unhealthy`. File 16 consumes this snapshot during its selection hard-filters per `model.model-selection-algorithm` (File 16 §7.3).

## 13. `RateLimitState` and Header Reconciliation

Anchor: `provider.rate-limit-state-header-reconciliation`

### 13.1 `RateLimitScope`

The canonical scope set is closed:

- `Global`
- `Provider { provider_id }`
- `Account { provider_id, account_id }`
- `Key { provider_id, account_id, credential_id }`
- `Model { provider_id, model_id }`

Limits at every scope may be user-configured downward (more restrictive than the provider's). Provider-reported limits are the ceiling; user limits never exceed them. Multi-account configurations require per-account accounting because limits differ per account; multi-key pools require per-key accounting so the rotation logic in §14 can skip exhausted keys.

### 13.2 `RateLimitWindow`

`RateLimitWindow` is structural, not a small fixed enum. Canonical variants are:

- `FixedWindow { duration_class, anchor }`
- `RollingWindow { duration_class }`
- `CalendarWindow { calendar_unit, provider_clock }`
- `Concurrent { in_flight_max }`
- `ProviderReported { provider_window_id, reset_semantics }`
- `Custom { namespace, name }`

Each scope may hold multiple windows. Windows accumulate independently and are evaluated together when admitting a call.

### 13.3 `RateLimitState`

`RateLimitState` carries, per `(scope, window)` — and a window's identity includes the quota **dimension** it governs (§13.4), so a scope's independent limits (for example, separate request, input-token, and output-token limits with different reset boundaries) are separate states, accumulated independently and evaluated together at admission (§13.2/§13.6):

- `dimension` — the quota this window governs: `Requests`, `Tokens`, `InputTokens`, `OutputTokens`, or `Named { policy_id }` (an IETF `RateLimit` policy name or a provider window id).
- `used` and `limit` — the consumed count and the ceiling for that dimension. `limit` may be user-configured downward below the provider's (§13.1); the effective ceiling is the more restrictive.
- `reset` — the typed reset kept verbatim from reconciliation (§13.4 `ResetInfo`: `AbsoluteEpochMs` | `RelativeMs` | `Unknown`). The window's absolute `window_resets_at` is derived from it: an absolute reset yields it directly; a relative reset is anchored at reconcile by the runtime service's injected clock (§13.4/§13.5/§13.7 — `window_resets_at := received_at + duration_ms`, captured once when the snapshot is reconciled, never re-derived from a live read at admission), and it is not stored pre-anchored, so the encoded state stays clock-free and deterministic. The state's identity/key is `(scope, window, dimension)` — stable across reconciliations and never re-keyed from a wall-clock instant, which is how §13.7's skew-immunity is achieved here (keying on the limit identity, not on a clock value).
- `status` — `Ok`, `Warning { remaining_pct }` when above the configured warning threshold, `WillResetSoon` when within the configured pre-reset window, `Limited`, or `Unknown`.

`RateLimitState` is the durable, canonically encoded projection of a window's accounting (it appears in the §22 runtime snapshot), so it carries only stable provider-reported values — epoch-ms bounds and integer counts — and encodes deterministically. The "has the window rolled?" decision is not made from these wall-clock bounds: the runtime admission service (§13.6) holds a per-window monotonic baseline captured at reconcile and decides the roll from monotonic elapsed, which no NTP step, manual clock change, or sleep transition can corrupt (§13.7). That baseline is ephemeral runtime state — a monotonic instant has no stable encoding and does not survive a restart, so it is never a field of the encoded `RateLimitState`; after a restart a window is `Unknown` until the next reconcile re-seeds it (§13.5). `status` is thus derived over `used`, `limit`, and (in the service) monotonic elapsed for the roll/`Limited` decision, with `window_resets_at` driving only the `WillResetSoon` display countdown.

### 13.4 `RateLimitSnapshot`

`RateLimitSnapshot` is the typed envelope parsed from provider response headers. It carries the `RateLimitScope` the limits apply to, an optional `retry_after` (the explicit retry advice on a `429`, §10.4), and a set of independent per-limit **observations** — one per limit the provider reports. Providers may expose several independent limits at once (requests, input tokens, output tokens, total tokens, named windows, or policy-labelled windows), so a single `requests` + `tokens` pair cannot faithfully represent them.

Each observation carries:

- `dimension` — the quota the limit governs: `Requests`, `Tokens`, `InputTokens`, `OutputTokens`, or `Named { policy_id }` (the IETF `RateLimit` policy name or a provider window id). This is the limit's identity, taken from the provider's own labelling — never fabricated.
- `limit` and `remaining` — the provider-reported ceiling and headroom for that dimension.
- `reset` — typed reset information, never a bare epoch and never dropped:
  - `AbsoluteEpochMs { at }` — the provider gave an absolute instant (Anthropic's RFC 3339 `*-reset`, or an IETF reset already anchored to the response `Date`). Stored directly as `window_resets_at`.
  - `RelativeMs { duration_ms }` — the provider gave a relative duration (OpenAI/Groq `"6m0s"`; IETF `RateLimit` `t=` seconds). The snapshot carries the raw duration only — the codec/transport that parses headers reads no clock. The duration is anchored at reconcile (§13.5), where the runtime's injected clock supplies the receipt instant: `window_started_at := received_at`, `window_resets_at := received_at + duration_ms`, and that same reconcile seeds the service's monotonic roll baseline (§13.3/§13.6). A relative reset is mandatory input to reconciliation; dropping it removes the provider's recovery guidance and forces the blind send-then-429 posture (§13.5/§25).
  - `Unknown` — the provider sent counts but no reset; the limit is tracked, and recovery falls back to a conservative bounded probe (§13.6).

Every honored reset (and `retry_after`) is range-clamped on parse: a non-finite, negative, or absurdly large value beyond the configured `max_reset_horizon` (§24) is rejected to its clamp rather than honored, so a hostile or buggy provider value cannot park the limiter indefinitely or panic the duration arithmetic (§13.7).

Adapters produce snapshots from their provider's specific header set and emit them through `RateLimitHeadersObserved` chunks during streaming or attached to `CompletionReceived` for non-streaming calls.

### 13.5 Reconciliation Discipline

Provider-reported headers are authoritative for provider-reported windows. `ProviderAdapter::reconcile_rate_limits` consumes a `RateLimitSnapshot` and replaces the provider-sourced `RateLimitState` for that `(scope, window, dimension)` with the provider's view. Atlas does not fabricate provider usage for failures that carry no provider evidence. For providers without rate-limit headers (local model servers, custom endpoints), reconciliation is a no-op and the limiter relies entirely on user-configured local windows.

User-configured local windows are separate Atlas-owned guardrails unless they are explicitly declared as downward caps on a provider-reported window. Each local window declares a counting policy:

- `DispatchedAttempt` — default for `Requests` safety budgets. Count one logical provider call when dispatch begins, including provider rejection, timeout, transport failure after dispatch, and retry exhaustion. Do not count admission blocks or caller cancellation before dispatch.
- `ProviderAcceptedAttempt` — count only when provider evidence indicates the request reached or was accepted by the provider. If the provider cannot report this signal, the window follows its configured fallback (`DispatchedAttempt` or unavailable).
- `SuccessfulCall` — count only completed calls. This is valid for analytics and soft user dashboards, not as a safety limiter for outage or retry loops.

Token windows are reconciled from provider-reported usage or post-call measured usage, not from request-attempt counting. A provider response that shows no provider quota was consumed corrects the provider-sourced rows; it does not automatically refund an Atlas-local `DispatchedAttempt` window unless that window's own counting policy says so.

Header reconciliation runs on both successful responses and on `RateLimited` responses; the latter carry the most up-to-date reset information.

### 13.6 Admission Control

Before issuing a call, the runtime consults `RateLimitService::check_allowed(scope, estimated_tokens) → AllowanceDecision`. The service evaluates every applicable `(scope, window)` state — user-configured local windows and provider-reported windows of every dimension (§13.2/§13.3) — and returns the most restrictive:

- `Allow`
- `BlockUntil { reason, retry_after_ms }` when any applicable window would be exceeded. The block deadline is, in precedence order: an active `429` `Retry-After` (§10.4 — it controls the immediate wait on an error response); else the exhausted window's monotonic-anchored reset; else a finite conservative backoff. It is always finite (clamped, §13.7), never an indefinite park.
- `Warn { remaining, next_reset_at }` when admission succeeds but the call crosses a configured warning threshold.

Recovery from an exhausted window is a bounded **probe**, not a permanent block. When the deadline elapses (measured by monotonic elapsed, §13.3, plus a configured margin/jitter to avoid a thundering herd), the runtime admits one in-flight probe per exhausted `(scope, window)` and reconciles the response's fresh headers (§13.5); if still limited, the block is updated from the new headers and the wait repeats. A wrong-early probe costs at most one `429` and a fresh reconciliation — but rejected requests are not assumed free, which is why the probe is single-flight with a margin, not an open retry.

Admission lives in the runtime `RateLimitService`, which owns wait/retry/fallback decisions and the clock discipline. Provider adapters normalize provider headers into `RateLimitSnapshot`s and expose reconciled per-`(scope, window, dimension)` state through the provider layer; they do not make final admission decisions. A count-only adapter-side block with no window-roll logic would deadlock a scope that once hit `remaining == 0`.

Provider-reported quota and Atlas-local attempt budgets are evaluated independently and surfaced with their source. The same failed model call may consume an Atlas-local `DispatchedAttempt` request budget while provider-reported request quota remains unchanged; hiding that distinction would make both user controls and provider reconciliation misleading.

Pre-call estimation is sourced from `context.token-counting` (File 13 §10). Post-call recording uses provider-reported usage (Tier 1 per §17) and records the residual against the same `(scope, window, dimension)` rows.

### 13.7 Burst, Concurrency, and Clock Skew

Burst capacity may be modeled with a token-bucket overlay above the canonical windows when a setting enables it. A provider that replenishes continuously (a token bucket — e.g. Anthropic, whose limits refill rather than resetting at a fixed instant) is modeled as a `ProviderReported` window whose `reset` is the refill horizon of the currently-binding limit; admission treats it as a rolling allowance, not a discrete fixed-window reset. Concurrent in-flight call counts are tracked through the `Concurrent` window.

**Clock discipline (the no-time-based-correctness invariant for rate limits).** A window's row identity is `(scope, window, dimension)` (§13.3) — stable across reconciliations and never re-keyed from a clock. Its `window_started_at` is the anchored start value (from the provider's absolute reset, or anchored at receipt for a relative reset, §13.4), derived once at reconciliation and never re-derived from a live wall-clock read. Two distinct clock uses are separated:

- The "has the window rolled?" correctness decision uses monotonic elapsed from the per-window baseline the runtime admission service captures at reconcile (§13.3/§13.6 — ephemeral runtime state, never a field of the canonically-encoded `RateLimitState`). A monotonic clock is immune to NTP steps, manual clock changes, and sleep transitions, so it cannot double-charge or double-credit a window. This — not "never read a clock" — is the invariant: relative resets are kept and anchored, and the clock that decides correctness is monotonic.
- The wall clock is read only for non-correctness purposes: the user-facing reset countdown (`WillResetSoon`), and sizing a one-shot block delay from an absolute `window_resets_at` as `max(window_resets_at - now, 0)` — floored at zero so a backward skew degrades to "act now", never a negative or runaway wait.

**Bounds (anti-deadlock + panic-safety).** Every honored reset or `Retry-After` is clamped on parse: non-finite (NaN/Inf) and negative values are rejected; a value beyond `max_reset_horizon` (§24) is treated as that horizon and surfaces a typed limit diagnostic rather than parking the limiter. The duration arithmetic must not overflow or panic. After a process restart no monotonic baseline survives, so a window is `Unknown` until the next reconcile re-seeds it (§13.3/§13.5); `window_resets_at` may be persisted for display only, never used as a post-restart correctness baseline.

### 13.8 Cross-Device

`RateLimitState` is per-device and is excluded from cross-device sync per the locality declaration in the settings spec. Devices observe their own usage; provider-reported limits remain the authoritative ceiling regardless of how many devices the account is used from.

## 14. Credentials, Accounts, and Pools

Anchor: `provider.credentials-accounts-pools`

### 14.1 `ProviderAccount`

A `ProviderAccount` is a typed named identity within one `provider_id`. Multi-account per provider is canonical. Accounts carry:

- `provider_id`
- `account_id` (user-facing label and stable identifier)
- `is_default` (per-`provider_id` default selection for new instances)
- `created_at`, `last_validated`
- per-account configuration (region, organization id, plan tier, custom headers)

### 14.2 `ProviderCredential` and Vault Reference

A `ProviderCredential` is the typed reference to one secret used by an account. It carries:

- `provider_id`
- `account_id`
- `credential_id`
- `auth_kind` (matching the profile's `auth_kind`)
- `vault_ref` — the canonical namespace key `provider.<provider_id>.<account_id>.<credential_id>` resolved through the vault interface owned by File 22

Credentials never appear inline. Adapters call the vault at the point of use and discard the resolved material after the request leaves. Resolved credentials never appear in ledger entries, events, settings, exports, or sync payloads.

### 14.3 `CredentialPool`

A `CredentialPool` binds multiple `ProviderCredential` references to one `ProviderAccount` for providers and users where per-key rate limits warrant rotation. The pool supports:

- round-robin selection across credentials
- per-credential `rate_limited_until` flags that exclude exhausted credentials from rotation
- explicit credential marking through `mark_rate_limited` invoked by `ProviderAdapter` when a 429 or equivalent error is observed
- explicit reset on a per-credential basis through `provider.reset_credential` per §22.6

When every credential in a pool is `rate_limited_until` a future time, the runtime returns `ProviderError::CredentialExhausted` with `exhausted_until` set to the earliest reset. File 16 receives the typed error and may fall back to a different model, provider, or instance.

Pools are opt-in per account. A pool never crosses `ProviderAccount`, provider instance, organization, region, plan, data-boundary, or policy boundary. It cannot be used to bypass provider policy, user budget, File 06 approval, or data-boundary restrictions. Cross-account or cross-provider fallback exits through File 16 selection or explicit user configuration.

### 14.4 Credential Rotation Events

Vault updates emit `CredentialRotated` per §22. Adapters subscribe and refresh their cached resolution. Rotation never triggers an active health probe; the next call validates the new credential implicitly.

### 14.5 Account Usage Snapshots

For providers that expose account-level usage endpoints, `ProviderAdapter::account_usage` returns a normalized `AccountUsageSnapshot` carrying per-window usage percentages, reset timestamps, plan information, and remaining-budget hints. The snapshot is opt-in per account, surfaced to users through the canonical usage capability surface, and never used as a substitute for header-driven rate-limit reconciliation.

## 15. Model Catalog and Capability Normalization

Anchor: `provider.model-catalog-capability-normalization`

### 15.1 `ModelCatalogEntry`

Per `(provider_id, model_id)` the registry holds a `ModelCatalogEntry` carrying:

- `provider_id`, `model_id`, `display_name`
- the populated `ModelCapabilityDescriptor` consumed by `model.model-capability-descriptor` (File 16 §3)
- `source_provenance` — typed declaration of where each capability fact came from (`ProviderReported`, `AdapterShippedFallback`, `UserSupplied`, `Probed`, `Unknown`)
- `lifecycle_metadata` — provider-reported deprecation status, training cutoff hint, release date when reported
- `pricing_ref` — reference to the latest `ModelPricing` snapshot when known, or `Unknown`
- `last_refreshed_at` for audit/display only
- `freshness_state` and `freshness_diagnostics` derived from source events, provider signals, adapter updates, credential changes, explicit refresh, or user-enabled maintenance policy

### 15.2 `ModelCapabilityDescriptor` Population

File 16 owns the descriptor shape. File 17 populates every field:

- `request_limits`, `streaming_support`, `native_callable_support`, `parser_tool_call_fallback_support`, `multimodal_input_support`, `structured_output_support`, `reasoning_support`, `cache_candidate_support`, `token_accounting_support`, `lifecycle_metadata` are filled from the provider's capabilities endpoint when exposed, otherwise from adapter-shipped fallback, otherwise from user-supplied overrides, otherwise `Unknown`
- adapters must not derive `output_window` from `context_window` by ratio per `model.model-capability-descriptor` (File 16 §3.2); absent output limits remain `Unknown` and assembly handles them through reserved-output policy
- adapters must not invent capabilities — `Unknown` is a valid descriptor value

### 15.3 Refresh

`ProviderAdapter::refresh_models` is event-driven:

- on provider registration
- on provider reconnection or credential refresh
- on adapter update
- on explicit user invocation through `provider.refresh_models`
- on provider capability-change signal when the provider exposes one
- on local descriptor edit through `provider.set_descriptor_override`

Background maintenance refresh is permitted only as an opt-in setting and is never a correctness condition. Stale or uncertain catalogue entries remain usable only with visible freshness diagnostics and provenance.

### 15.4 Pricing Population

`ModelPricing` carries provider-reported pricing when available, user-supplied pricing when the provider does not expose it, and `Unknown` otherwise. Provider-reported pricing is preferred. Unknown pricing is never silently reclassified as free. Whether `Unknown`-pricing models are eligible for automatic selection is governed by the policy on `model.cost-budget-selection` (File 16 §11) plus the `unknown_cost_policy` setting per §24.

### 15.5 Capability Caching and Invalidation

Capability state is cached in the registry projection. Invalidation triggers: model-catalog refresh, explicit user override, adapter update, and credential change. The registry never caches resolved credentials.

## 16. Cache Marker Translation

Anchor: `provider.cache-marker-translation`

### 16.1 Boundary

`context.cache-marker-candidates` (File 13 §11) produces logical `CacheMarker` candidates with provider-invariant anchors, source references, fingerprints, stability reasons, and sensitivity eligibility. File 17 translates them to provider-native cache annotations through `ProviderAdapter::render_cache_markers`.

### 16.2 Translation Discipline

- Adapters apply the profile's `cache_marker_strategy` to render markers in the provider's expected wire form (annotation on a content block, separate cached-content resource, no-op for providers with automatic prefix matching)
- The number of markers is capped by the provider's declared `max_cache_markers` (when applicable); excess candidates are dropped from the lowest-priority end with a typed diagnostic per §22
- The minimum cacheable size (when the provider declares one) is enforced; candidates below the minimum are dropped with a diagnostic
- Sensitivity-ineligible content is excluded from caching per the rules in `context.cache-marker-candidates` (File 13 §11) and `ledger.sensitivity-aware-persistence-retention` (File 10 §10)
- requested retention preference, when present as a provider-layer setting or adapter policy, is mapped to supported provider behavior with diagnostics on drop or clamp

### 16.3 Cache Hit Accounting

Adapters extract `cache_creation_tokens` and `cache_read_tokens` from provider responses where reported and surface them through `TokenUsageRecord` per §18. Cache pricing multipliers from `ModelPricing` are consumed by cost computation per §19.

### 16.4 Cache Break Detection

Adapters that support pre-and-post call cache fingerprinting (governing-instruction hash, callable-declaration hash, marker placement hash) may detect unexpected cache breaks and emit `CacheBreakDetected` per §22 with the change vectors identified. Detection is opt-in.

### 16.5 No Cache Mechanics in Other Files

Provider-native cache syntax, retention behavior, minimum lengths, marker limits, pricing multipliers, and cache-hit accounting wire fields all live in this layer. File 13 produces candidates; File 17 translates and reports.

## 17. Tokenizers and Token Counting

Anchor: `provider.tokenizers-token-counting`

### 17.1 `TokenSource`

Anchor: `provider.token-source`

The canonical accuracy hierarchy is closed:

- `ProviderNative` — counts reported by the provider in the response usage payload; highest accuracy
- `ProviderCountEndpoint` — counts obtained from a provider's dedicated count endpoint where one exists; second-tier accuracy
- `LocalTokenizer` — counts from a local tokenizer library compatible with the model family (per-family BPE, SentencePiece, or equivalent)
- `CharacterApproximation` — character-based approximation; lowest accuracy; carries explicit uncertainty and adapter/settings-owned formula metadata

The hierarchy is consulted in priority order. Tier 1 always wins when available.

### 17.2 `TokenizerId`

`TokenizerId` is the canonical key for cache and attribution. Its concrete format is provider/adapter-owned but must uniquely identify the counting method, model family, and approximation policy where relevant. Adapters declare the `TokenizerId` they dispatch for each model. Other layers consume the identifier but do not interpret it.

### 17.3 Per-Model Dispatch

The dispatch table per `(provider_id, model_id)` lives in the adapter or its profile. Adapters must:

- prefer provider-native counts from the response when present
- use the provider's count endpoint when available for pre-call estimation
- fall back to a model-family-appropriate local tokenizer when no provider-native counting is available for that model
- fall back to character approximation only when no local tokenizer matches the model family
- never use a tokenizer whose accuracy is known to mismatch the target model family

### 17.4 `(block_id, tokenizer_id)` Cache

The runtime maintains an in-memory LRU cache keyed by `(block_id, tokenizer_id)`. The cache:

- holds typed `TokenCount` values carrying `count`, `source`, `tokenizer_id`, and `measured_at`
- is never persisted to durable storage
- has a configurable bound; eviction is LRU on pressure
- requires no invalidation on write because block content is immutable per `block.edit-semantics` (File 08 §6.2)
- is shared between this layer and `context.token-counting` (File 13 §10)

A separate `tokenizer_cache` projection persists frequently used token counts keyed by `(block_id, tokenizer_id)` only when the storage spec elects to do so for performance; the in-memory cache is the canonical layer.

### 17.5 Per-Block Attribution from Streaming Counts

When a streamed response carries running usage counts (`PartialUsageObserved` chunks per §9.1), the adapter attributes per-block deltas as the difference between the running total at the chunk that ended a block and the running total at the chunk that started the block. This produces tokenizer-keyed per-block counts at the highest accuracy class without an additional tokenizer call. The counts populate the `(block_id, tokenizer_id)` cache and become the source for the block's contribution to `TokenUsageRecord`.

### 17.6 Pre-Call Estimation Accuracy Telemetry

When the runtime estimated tokens pre-call (Tier 2 or Tier 3) and Tier 1 counts arrive post-call, the adapter emits `TokenCountEstimationTelemetry` per §22 with the estimated count, actual count, and percentage delta. The telemetry feeds the user-facing "your estimates have been averaging X% off" diagnostic and informs future tokenizer-dispatch settings.

### 17.7 Multimodal Counting

Multimodal content (images, audio, video, files) has provider-specific counting rules:

- adapters extract provider-reported multimodal usage from response payloads when available
- when the provider does not report per-modality usage but accepts multimodal input, adapters compute a typed estimate from declared per-modality constants (image dimensions to tokens, audio duration to tokens) declared in the adapter or profile
- estimates are accuracy-classed below provider-native counts and feed the same telemetry path

### 17.8 Live Counting Versus Replay

Provider token-count endpoints (`ProviderCountEndpoint`) and any other live counting path may be used for live assembly and pre-call estimation. Every count obtained this way must be recorded with its `provider_id`, `model_id`, `tokenizer_id`, and `TokenSource` on the call's `TokenUsageRecord` (§18) and in the consuming `AssemblySnapshot` (`context.assembly-replay-snapshot`, File 13 §19). Historical replay, audit, and deterministic reconstruction consume the recorded counts, never the provider endpoint, consistent with the replay-determinism rule `context.assembly-replay-snapshot`. A replay that re-queries a provider count endpoint is invalid.

## 18. `TokenUsageRecord`

Anchor: `provider.token-usage-record`

### 18.1 Required Fields

Every model-bound call produces one `TokenUsageRecord` carrying at minimum:

- `record_id`
- `request_id` — provider-reported when available, locally generated otherwise
- `run_id`, `step_id`, `conversation_id`, `intent_thread_id`, `workspace_id` per `ledger.cross-references` (File 10 §3.6)
- `provider_id`, `model_id`, `account_id`, `credential_id` (when relevant)
- `tokenizer_id` — the `TokenizerId` used for any counts in this record
- `role` — the workload role tag
- `started_at`, optional `completed_at`, optional `cancelled_at`, and optional `error_at`; a terminal record carries exactly one terminal timestamp matching its completed, cancelled, or failed outcome
- `prompt_tokens`, `completion_tokens`
- `cache_creation_tokens`, `cache_read_tokens`
- `reasoning_tokens` (optional, populated when the provider reports it)
- `multimodal_tokens` — typed sub-record carrying `image_tokens`, `audio_tokens`, `video_tokens`, `file_tokens`, each optional
- `stop_reason` — normalized provider-call stop reason recorded on File 10 model-call entries; execution-level stop reasons remain File 04-owned
- `error_class` — optional, the typed `ProviderError` discriminant when the call errored
- `pricing_snapshot_ref` — reference to the `PricingSnapshot` consumed for derived cost
- `policy_snapshot_ref`, `settings_snapshot_ref`, `world_snapshot_ref`, `registry_snapshot_ref` per `ledger.cross-references` (File 10 §3.6)
- `token_count_source` — typed `TokenSource` for each token count category (allowing different sources per category)
- `parameter_clamps` — list of typed `ParameterClamped` diagnostics applied to this call
- `idempotency_key`

The record is the canonical durable per-call attribution. File 10 references it from `ModelCallCompleted`, `ModelCallFailed`, and `ModelCallCancelled` ledger entries.

### 18.2 Explicit Non-Fields

The record must not carry:

- `cost_cents` or any unkeyed cost scalar — cost is derived per §19
- resolved credentials, raw request bodies, raw response bodies, or unredacted sensitive content
- a single combined token total — totals are derived projections over the typed fields
- estimated counts replacing actuals when actuals are available

### 18.3 Per-Role Attribution

`role` allows aggregation per work-role across a run, task, or conversation. The closed canonical roles match `model.model-workload-requirements` (File 16 §5.2): `router`, `responder`, `planner`, `summarizer`, `critic`, `validator`, `classifier`, `vision_grounding`, `completion_verifier`, `child_run_model`, or `Custom { namespace, name }`. New canonical role tags are added through canonical-spec change.

### 18.4 Multi-Model Per Run

A single run may emit many `TokenUsageRecord`s (router, responder, critic, validator, sub-agent calls, summarizer, completion verifier). Each call records independently keyed by its own `(provider_id, model_id, tokenizer_id, role)`. Aggregation per run is a projection over the records.

### 18.5 Streaming Updates

For streaming calls, a partial `TokenUsageRecord` is written on cancellation (the `StreamCancelled` terminal, §9.3) or on a mid-stream error (the `StreamError` terminal). Successful streams write the final record on `CompletionReceived`. A cancellation partial carries `stop_reason = CancelledByUser` and no `error_class`; it routes to `ModelCallCancelled` (File 10 §4), never `ModelCallFailed`. An error partial carries the typed `error_class`.

## 19. Cost as a Derived Projection

Anchor: `provider.cost-as-derived-projection`

### 19.1 Rule

Cost is never stored as an unkeyed scalar in any durable row. This obeys `core.explicit-rejections` (File 01 §8) and the ledger-side forgery guard in `ledger.forgery-guards` (File 10 §3.7).

### 19.2 `ModelPricing`

`ModelPricing` carries, per `(provider_id, model_id)`:

- `input_unit_price`, `output_unit_price` (per-unit, with unit declared)
- `currency` — the currency the per-unit prices are denominated in (provider-reported or user-supplied); prices in different currencies are never combined without an explicit, recorded conversion
- `cache_creation_price_multiplier`, `cache_read_price_multiplier` (relative to input price, where applicable)
- `reasoning_token_price` (when distinct from completion price)
- per-modality unit prices (image, audio, video, file) where the provider charges differently
- `inclusion_status` — `Standard`, `IncludedInActiveAccount`, `ZeroMarginalCostForActiveAccount`, or `Unknown`; this is an account/plan projection, not a stable model capability
- `pricing_version` and `pricing_source` (`ProviderReported`, `UserSupplied`, `AdapterShippedFallback` with adapter version and source provenance)
- `effective_from` timestamp for time-anchored pricing

### 19.3 `PricingSnapshot`

`PricingSnapshot` is the durable snapshot reference attached to a `TokenUsageRecord` at call time. It captures the `ModelPricing` row in effect at the moment of the call. Subsequent pricing changes do not retroactively alter historical cost projections.

### 19.4 Computation

Cost for one `TokenUsageRecord` is computed on demand by aggregating typed token counts against the referenced `PricingSnapshot`, applying the cache and modality multipliers, summing components. The result is `Some(cost)` or `Unknown` when any required price is `Unknown`. `Unknown` is never silently coerced to zero.

### 19.5 Aggregations

Per-conversation, per-run, per-task, per-day, per-workspace, per-role, per-account, per-provider, and per-model cost views are projections over `TokenUsageRecord`s. They are rebuildable from the canonical records and the pricing snapshots. Every aggregation groups by `currency`; a view spanning multiple currencies presents each currency's subtotal separately rather than summing across them.

### 19.6 Optional Cost Tracking

Cost tracking is opt-in per `run.budgets-limits` (File 04 §21) budget enforcement and per File 15 settings. When disabled, records still carry the structural fields needed to compute cost later if the user enables it. The system never silently disables tracking when records exist.

## 20. Multimodal Usage

Anchor: `provider.multimodal-usage`

### 20.1 Scope

Provider-reported multimodal usage flows through this layer alongside textual usage. Each modality has its own optional counter on `TokenUsageRecord` per §18 and its own optional pricing on `ModelPricing` per §19.

### 20.2 Adapter Responsibility

Adapters extract provider-reported per-modality counts when available, fall back to typed adapter-shipped estimation when the provider accepts multimodal input but does not report per-modality usage, and never silently fold multimodal usage into the textual counters. When the provider's response contains only an opaque total, adapters record the total under the closest matching counter and emit a `TokenCountEstimationTelemetry` event so the user can see the underlying ambiguity.

### 20.3 Output Modalities

For providers that produce non-text outputs (images, audio, structured artifacts), the same accounting principle applies: each output modality has its own counter on `TokenUsageRecord`, populated from provider-reported usage where exposed.

## 21. `ProviderRuntimeSnapshot` and `ProviderOfferingProjection`

Anchor: `provider.provider-runtime-snapshot-provider-offering-projection`

### 21.1 Definitions

`ProviderRuntimeSnapshot` is the typed projection consumed by `model.provider-inputs-consumed-by-model-strategy` (File 16 §2) carrying:

- per-`provider_id` `ProviderHealth`
- per-`(scope, window, dimension)` `RateLimitState` summary
- in-flight capacity per provider
- credential state (`Authenticated`, `ExpiringSoon`, `Expired`, `MissingFromVault`, `Rotating`)
- provider-reported error trends across the last reset window (provider/transport FAILURES only — a cancellation is a caller action, not a provider error, and is excluded from error trends, §9.3/§12.3)
- known-retryability hints from recent classifications, including whether an `Unhealthy` provider is currently eligible for a demand-triggered single-flight recovery probe (§12.3)

`ProviderOfferingProjection` is the typed projection consumed by `model.provider-inputs-consumed-by-model-strategy` (File 16 §2) carrying:

- enabled providers and accounts
- enabled and excluded models per account
- effective `ModelPricing` per `(provider_id, model_id)` for the active account
- account-plan availability
- region and data-handling metadata from the account configuration
- speed and latency observations across recent calls
- user-supplied accounting overrides

### 21.2 Read-Only From File 16

File 16 does not mutate either projection. Mutations flow only from runtime call outcomes, credential lifecycle, model-catalog refresh, capability changes, settings changes, and explicit user actions on the provider-management surfaces.

### 21.3 Freshness

Both projections are read-optimised. Their staleness is bounded by the events that drive them; consumers read at call time. Stale projections never substitute for the underlying state; cached projections invalidate on the relevant typed events per §22.

## 22. Events Emitted

Anchor: `provider.events-emitted`

### 22.1 Provider Event Vocabulary

This layer emits through the unified bus and ledger in File 10. Cross-cutting model-call entries use File 10 canonical kinds. Provider-specific operational events register as `Custom { namespace: "provider", name, payload }` unless File 10 later promotes them to canonical kinds:

- `ProviderRegistered`, `ProviderUnregistered`, `ProviderInstanceCreated`, `ProviderInstanceRemoved`, `ProviderInstanceReconciled`
- `ModelCallStarted`, `ModelCallStreamingDelta`, `ModelCallCompleted`, `ModelCallFailed`, `ModelCallCancelled`
- `ProviderHealthChanged` carrying prior and new `ProviderHealth`
- `RateLimitSnapshotReconciled` carrying the parsed `RateLimitSnapshot`
- `RateLimitHit` carrying `provider_id`, `model_id`, `scope`, `window`, `retry_after_ms`
- `ProviderModelsRefreshed` carrying `provider_id` and updated `ModelCatalogEntry` ids
- `CapabilityProbed` when capability normalization performs an explicit probe
- `CredentialRotated`, `CredentialExhaustionDetected`, `CredentialAuthRefreshed`
- `ParameterClamped` carrying requested intent, resolved value, applied clamp, and reason
- `CacheBreakDetected` carrying the cache fingerprint change vectors
- `TokenCountEstimationTelemetry` carrying estimated vs actual counts with configured diagnostic summary
- `GatewayIncompatibilityDetected`
- `ProviderTransportRetryAttempted` recording the typed strategy and attempt counter
- `Custom { namespace, name, payload }` for registered extensions

### 22.2 Event Envelope

Every event carries the canonical envelope from `ledger.event-envelope` (File 10 §5.2) with `conversation_id` where applicable, `context_refs` populated with `run_id` / `step_id` / `provider_id` / `account_id` / `credential_id` / `model_id` as appropriate, `sequence_scope` / `sequence` / `timestamp`, and `sensitivity` per §23.

### 22.3 Ledger Boundary

Consequential events also commit as typed ledger entries per `ledger.entry-kinds` (File 10 §4.3). `ModelCallStarted`, `ModelCallCompleted`, `ModelCallFailed`, `ModelCallCancelled`, `ProviderHealthChanged`, `RateLimitSnapshotReconciled`, `CredentialRotated`, and `ProviderModelsRefreshed` are durable. High-frequency events (`ModelCallStreamingDelta`, `TokenCountEstimationTelemetry`) are subject to aggregation per `ledger.streaming-live-partials` (File 10 §12.3).

### 22.4 Subscribers

Hooks, telemetry, evaluation, billing dashboards, debugging UIs, and the model-strategy layer all subscribe through the unified mechanism in `ledger.event-stream` (File 10 §5). This file emits; consumers subscribe.

### 22.5 Per-Call Cardinality

`ModelCallStarted` fires at most once per call. Exactly one terminal event — `ModelCallCompleted`, `ModelCallFailed`, or `ModelCallCancelled` — fires at most once for the same request id. `ModelCallStreamingDelta` aggregates per the active policy. `ModelCallFailed` may fire after retries are exhausted; intermediate retry attempts emit `ProviderTransportRetryAttempted` rather than a terminal model-call event.

### 22.6 Provider Capability Surface

This layer exposes the following capability families through the canonical registry per File 05:

- `provider.register` — register a new provider instance
- `provider.unregister`
- `provider.update_configuration` — update non-credential fields
- `provider.set_credential` — write a vault-backed credential reference
- `provider.rotate_credential`
- `provider.reset_credential` — reset a credential's rate-limit flag in a pool
- `provider.list`
- `provider.inspect` — full inspection of an instance's runtime state including health, rate-limit projections, credential state
- `provider.refresh_models`
- `provider.set_descriptor_override` — override descriptor fields for local/custom providers
- `provider.set_pricing_override` — override pricing where the provider does not expose it
- `provider.reset_health`
- `provider.set_rate_limits` — configure user-tightened limits below the provider's ceiling
- `provider.account_usage` — fetch normalized remote usage when the provider exposes it
- `provider.ping` — explicit user-triggered connectivity test
- `provider.classify_error` — explicit invocation of `ProviderAdapter::classify_error` for diagnostics
- `usage.read` — query `TokenUsageRecord`s and aggregated projections
- `usage.compute_cost` — compute derived cost for a query range against the relevant pricing snapshots

Exact declarations, permission tiers, touched-resource expressions, preview behavior, leases, and approval rules belong to Files 05 and 06. Write-like provider capabilities (set_credential, rotate_credential, register, unregister, update_configuration, set_descriptor_override, set_pricing_override, set_rate_limits) require typed approvals per File 06.

## 23. Sensitivity, Redaction, and the Secret Boundary

Anchor: `provider.sensitivity-redaction-secret-boundary`

### 23.1 Default Classification

Provider-layer events default to `Public` per `ledger.event-envelope` (File 10 §5.2) except where credentials or sensitive content are involved.

### 23.2 Sensitive Events

The following events default to `Sensitive`:

- credential-handling events (`CredentialRotated`, `CredentialAuthRefreshed`, `CredentialExhaustionDetected`)
- error events carrying provider-reported error bodies (`ModelCallFailed`)
- account-usage snapshots that reveal plan or billing detail
- gateway-incompatibility events when the gateway URL identifies a user-private endpoint

### 23.3 Secret Material

Resolved credentials, raw API keys, vault-decoded OAuth tokens, signed-request signatures, and unredacted user content explicitly marked `Secret` per `ledger.sensitivity-aware-persistence-retention` (File 10 §10) never enter durable persistence. The commit validator rejects ledger entries whose payload contains `Secret` material per `ledger.forgery-guards` (File 10 §3.7).

### 23.4 Adapter Responsibility

Adapters scrub provider-reported error bodies for known credential patterns and unredacted user content before producing typed `ProviderError` values. Profiles may declare typed scrubbing rules. Scrubbing is part of the contract; the adapter that ships without it fails the registration-time validation in §5.2.

### 23.5 Sync, Export, Telemetry

`RateLimitState` is per-device and excluded from sync per §13.8. `TokenUsageRecord`s sync per the settings spec's locality declarations. Credentials never sync. Exports redact `Sensitive` payloads unless the user explicitly includes them.

### 23.6 The Backend Secret Boundary

This section applies the backend secret boundary (`secret.backend-boundary`, File 22 §4) at the provider layer. File 22 §4 is the general, owning statement of the rule: it defines the forbidden destinations for raw `Secret` material, what may cross the boundary in its place (an opaque secret reference such as a `SecretRef` or vault namespace key, a redacted projection, a safe description, or a capability-scoped handle), the `SecretValue` wrapper, and the zeroization guarantee.

At the provider layer, raw `Secret` material — resolved credentials, API keys, vault-decoded OAuth tokens, request signatures, and unredacted user content marked `Secret` (`ledger.sensitivity-aware-persistence-retention`, File 10 §10) — is held only in backend-owned transient buffers and the vault/credential substrate, never crosses the boundary File 22 §4 defines, and is discarded after the request leaves.

`ledger.sensitivity-aware-persistence-retention` (File 10 §10) enforces the rule at the ledger, event, sync, export, and telemetry paths; `settings.secret-boundary` (File 15 §10) enforces it at the settings, TOML, and sync paths; File 22 owns the general statement and the vault internals.

## 24. Settings Dimensions

Anchor: `provider.settings-dimensions`

Every behavior in this file that is meaningful for users, workspaces, conversations, profiles, or installations to vary is declared as a `SettingDefinition` and resolved through File 15. The settings catalogue includes:

- preferred and excluded providers, accounts, and models
- per-account credential references (`SecretRef` only)
- per-instance configuration overrides (base URL, custom headers, proxy, region)
- model-catalog event-driven refresh and optional user-enabled maintenance policy
- per-error-class transport-retry caps, backoff strategies, and jitter parameters
- per-scope rate-limit budgets and burst overlays
- per-local-window counting policy (`DispatchedAttempt`, `ProviderAcceptedAttempt`, or `SuccessfulCall`) and fallback when provider acceptance evidence is unavailable
- rate-limit reset horizon, probe margin, and single-flight probe policy
- warning and pre-reset notification policies
- health admission, degradation, unhealthy-state, and retry-hint policies
- credential-pool enablement and rotation policy per account
- cache enablement and retention-preference policies per provider and per workspace
- tokenizer overrides per `(provider_id, model_id)`
- pre-call estimation strategy and accuracy thresholds for telemetry
- pricing-source preference (`provider_reported`, `user_supplied`, `adapter_fallback`) and the `unknown_cost_policy`
- cost tracking enablement and aggregation policy
- per-modality estimation constants where adapter defaults are user-overridable
- parameter-clamping behavior (`silent_with_diagnostic`, `surface_to_user`, `fail`) per parameter or globally
- header reconciliation behavior (when to trust provider headers above local-counter state)
- streaming aggregation policies inherited from `ledger.streaming-live-partials` (File 10 §12.3)
- subscription-wrapper subprocess defaults (sandbox profile, HOME override behavior, allowed CLI flags)
- gateway-incompatibility detection rule registration
- user-controlled `provider.refresh_models` maintenance policy beyond event-driven refresh
- per-provider event-sensitivity overrides for credential-handling events
- per-call observability fields beyond the canonical minimum
- account-usage refresh enablement per account

Exact default values belong to setting definitions and profile layers, not this file. Settings define intended product variation; they must not become hidden hardcoded branches.

## 25. Explicit Rejections

Anchor: `provider.explicit-rejections`

The following shapes are wrong for this layer:

- hardcoded provider-name branching outside provider adapter normalization
- provider-specific API names, model names, pricing constants, tokenizer crate names, or wire-format header strings embedded in canonical layer text
- model-name pattern matching in any layer above the adapter (the rule from `model.explicit-rejections`, File 16 §15 restated)
- treating subscription wrappers (CLI binaries, seat-based subscription APIs) as a separate tier outside the canonical `ProviderAdapter` contract
- treating MCP tool servers as model providers through this layer
- driver-kind crash on unknown — unknown drivers degrade to `Unknown` with diagnostic, not panic
- silent automatic provider-instance instantiation without registration through the canonical capability surface
- scheduled active health pings on a fixed interval (event-driven and user-triggered only)
- silent fallthrough on `AuthenticationFailed` — auth failures are not retryable
- silently retrying through `Fatal` `ErrorClassification`
- cost stored as an unkeyed scalar in any durable row
- token counts stored on `Block` rows or persisted without `(block_id, tokenizer_id)` keying
- tokenizer dispatch against a model family it is known to mismatch
- treating `Unknown` capability as `false` or `Unknown` pricing as `0`
- silently dropping `cache_creation_tokens` or `cache_read_tokens` when the provider reports them
- silently coercing multimodal usage into textual counters when the provider reports per-modality usage
- credentials inline in any adapter struct, ledger entry, event, sync payload, export, log, or agent context
- resolved credentials retained beyond the request lifecycle
- raw API keys in error messages or stack traces
- header reconciliation that ignores provider-reported reset times in favor of local backoff calculations
- rate-limit accounting that conflates the multiple windows of one scope into a single counter
- presenting provider-reported quota and Atlas-local attempt budgets as one indistinguishable "requests remaining" value
- silently refunding an Atlas-local `DispatchedAttempt` window because provider evidence showed no provider quota consumption, unless that local window explicitly configured that policy
- using `SuccessfulCall` counting as a safety limiter for provider outages or retry loops
- credential rotation through the canonical pool without typed `mark_rate_limited` and `reset_credential` operations
- transport-level retry that switches `(provider_id, model_id)` without exiting through File 16's `FallbackPolicy`
- per-provider parameter clamping without a typed `ParameterClamped` diagnostic
- silent provider-quirk handling that alters the user's apparent request without observability
- gateway incompatibility detection that burns the configured retry budget instead of short-circuiting
- secret material in events, ledger entries, exports, or sync payloads
- aggregate cost views that lose per-call source attribution
- terminal model-call entries (`ModelCallCompleted`, `ModelCallFailed`, or `ModelCallCancelled`) without per-call `TokenUsageRecord` attribution
- streaming pipelines that swallow mid-stream errors
- using stale or uncertain model-catalog facts without visible provenance and freshness diagnostics
- header-injection patterns hardcoded in canonical text outside the profile or hand-coded adapter
- forced cost projection to numeric `0` when pricing is `Unknown`
- silent cache marker dropping without diagnostic
- canonical Atlas-level layer above this one knowing provider parameter names
- credential pool selection that retries an exhausted credential before its `rate_limited_until` time
- treating provider-reported reset hints as optional when they are present, except where the user cancels or policy permits explicit override

## 26. Consequences for Later Specs

Anchor: `provider.consequences-for-later-specs`

Later specs must follow these rules:

- File 16 must consume `ModelCapabilityDescriptor`, `ProviderOfferingProjection`, and `ProviderRuntimeSnapshot` from this layer; it must not query provider-specific data directly
- File 16 must classify model-level fallback through the typed `ProviderError` variants this layer produces; it must not invent provider classifications
- File 04 must propagate the cancellation signal through `ProviderRequest` and consume partial `TokenUsageRecord`s on cancellation
- File 04 must surface `ContextTooLargeForSelectedModel` to the context layer per `run.boundary-rule` (File 04 §20.1) without retrying at the execution boundary
- File 10 must record `TokenUsageRecord`-attributed terminal model-call entries (`ModelCallCompleted`, `ModelCallFailed`, or `ModelCallCancelled`) with provider/model/account/credential/tokenizer/role keying and correlate them with `ModelCallStarted`; it must reject entries whose payload contains `Secret` material per the existing forgery guards
- File 13 must consume the `(block_id, tokenizer_id)` cache contract, produce logical `CacheMarker` candidates this layer translates, and source request-size limits from `ModelCapabilityDescriptor` provided here
- File 15 must register every provider-layer setting through the canonical source stack; it must not invent a parallel cascade
- The Security, Credentials, and Trust Boundaries spec implements the backend-only vault resolution interface this layer references through `resolve_for_use(SecretRef("provider.<provider_id>.<account_id>.<credential_id>"), purpose, invocation_context)` and emits `CredentialRotated` events consumed here
- File 20 must persist `TokenUsageRecord`s with their full keyed attribution and the cross-references this file enumerates; it must persist the durable provider-pricing family — `ModelPricing` (including `UserSupplied` overrides) per `(provider_id, model_id)` and the immutable `PricingSnapshot` each record references (§19.2/§19.3) — device-local; and it must persist `RateLimitState` per-device and exclude it from cross-device sync per §13.8
- File 21 must respect the per-event sensitivity classifications declared here and the per-`SettingDefinition` locality declarations the settings spec carries
- File 36 (MCP and External Integrations) must not subsume the model-provider layer; MCP for tools is a tool-provider concern with its own provider-adapter analogue, not a route through this layer
- File 23 must support subscription-wrapper subprocess lifecycle in the sandbox primitives declared there (process groups, HOME isolation, shadow homes)
- File 37 and File 38 must render per-call attribution, derived cost, rate-limit projections, credential states, provider health, and model-catalog freshness from the projections this layer produces; they must not maintain a parallel provider-state store
- The Telemetry, Logging, and Observability spec (File 41) must consume `ModelCallStarted` / `ModelCallCompleted` / `ModelCallFailed` / `ModelCallCancelled` / `TokenCountEstimationTelemetry` / `ProviderHealthChanged` / `RateLimitSnapshotReconciled` / `ParameterClamped` / `CacheBreakDetected` events without inventing parallel emission paths
- The Evaluation and Benchmarking spec (File 40) should use `TokenUsageRecord` and `PricingSnapshot` references as primary artifacts for cost-correctness, cache-effectiveness, and tokenizer-accuracy measurements
- Plugin and extension specs that register adapters or profiles must pass through the source-approval flow in `policy.source-approval-flow` (File 06 §9); they must implement the full `ProviderAdapter` contract and produce the same typed projections
- Domain specs that introduce siblings to model providers (STT, TTS, image, embedding) should adopt the same provider-adapter pattern with sibling traits sharing the credential, rate-limit, usage, and event infrastructure declared here, without forcing those siblings into the LLM-specific surface this file defines
