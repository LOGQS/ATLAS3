# Phase 7 — Providers, Models & Vault (M2: Real Conversation)

## 1. Goal & why now

The mock seam gets its real implementation: the File 22 SecretVault holds real credentials, the
File 17 provider layer speaks to a real model API behind the `ProviderAdapter` seam (complete first,
streaming second), the File 16 model-strategy layer selects deterministically and records why, and
File 13 completes with provider-keyed token counting, real budgets, cache markers, and the compaction
write-side. The vault must precede the provider (credentials resolve at point of use through it) —
the load-bearing ordering edge "secret boundary before any credential." Milestone **M2**: a real,
durable, attributed, replayable conversation.

## 2. Canonical scope & deferrals

- **File 22 — vault + credentials** (§5–§8 partial): the `SecretVault` typed contract — OS-keyring
  backend (default where available) + encrypted-file backend (Argon2id-class derivation,
  AES-256-GCM-class cipher), identical behavior across both; dotted owner-scoped namespace;
  `SecretRef` + inert `vault:<key>` config form; the unlock model + typed `VaultLocked` degradation;
  **backend-only `resolve_for_use(SecretRef, purpose, invocation_context)`** — never a
  capability/IPC/tool; agent/renderer invisibility by construction; credential lifecycle
  (store/rotate/expire/revoke) + `SecretRotated`; the secret detector completed (registered patterns
  + reverse-env scan + entropy, golden fixtures); audit-chain crypto binding (§14 with P3's chain);
  vault unlock as boot step 10. Trust model/egress/injection (§9–§13) → **P8**.
- **File 17 — complete core**: the closed-method `ProviderAdapter` contract — the only layer that
  knows provider wire shapes/model names/error codes/tokenizer bindings (§3);
  `ProviderProfile`/`ProviderInstance`/`ProviderRegistry` (§4–§5); request execution + parameter
  serialization (§7–§8); streaming `ProviderStreamChunk` with one-and-only-one terminal chunk (§9);
  the closed `ProviderError` taxonomy + `ErrorClassification` (§10); transport retry inside the
  layer — never switching `(provider, model)`, that exits to 16's fallback (§11); event-driven
  `ProviderHealth`, no scheduled pings (§12); `RateLimitState` + header-authoritative reconciliation
  + `(scope, window, dimension)` keying with `window_started_at` as the anchored start value,
  per-device storage (§13); accounts/credentials via vault refs +
  `CredentialPool` rotation (§14); model-catalog → descriptor population, `Unknown` allowed, never
  invented (§15); cache-marker translation (§16); tokenizer dispatch + the `TokenSource` hierarchy +
  the shared `(block_id, tokenizer_id)` count cache (§17); `TokenUsageRecord` per call (§18);
  pricing snapshots + **cost as a derived projection, `Unknown` never coerced to 0** (§19);
  runtime/offering projections for 16 (§21). Subscription-wrapper subprocesses (§6.2) → **P8**
  (needs 23).
- **File 16 — complete core**: `ModelCapabilityDescriptor` consumption — capability-driven dispatch,
  never model-name branching, `Unknown` never treated as false (§3); `ModelProfile` + selectors
  (§4); `ModelWorkloadRequirements` + role tags (§5); the `ModelRegistry` computed projection (§6);
  the **deterministic selection algorithm** — hard filters never converted to weighted scores, pins
  never silently fall through (§7); the durable `ModelSelectionRecord` per model-bound step (§8);
  `FallbackPolicy` — model-level recovery only, never silently relaxing hard requirements, full
  revalidation after any model change (§9); `ResolvedModelBehavior` + reasoning posture (§10);
  cost/budget hard-filtering (§11); data-boundary ordering — sensitivity analysis before selection,
  reselect on stricter discovery (§5.3). Multi-model plans (§13) → first consumer (P16 classrooms /
  P21 comparisons).
- **File 13 — completion**: provider-keyed token-counting tiers (exact → compatible-local →
  conservative, recorded accuracy class) (§10); cache-marker candidates (§11); real `BudgetReport`
  driving 07 auto-shrink (cache-impact classes aligned 13 §9 ↔ 07 §8.3); the **CompactionService
  write-side** — `DescriptionDriven` default + FullSummarisation families, `context.archive`/
  `recall` ops, continuity-summary blocks, revision-safe commits through the version graph, never
  mutating content (§12–§14); the typed context-pressure boundary (§15); instruction-source
  inclusion authority (§16 — ATLAS.md indexing joins in P10).

## 3. Prerequisites

P6 — the loop, the mock seam, assembly read-side, `model_route` consumers. P2's `SecretRef` forms now
get real resolution.

## 4. Lanes

Serial spine: vault → provider → model strategy (each consumes the prior). The 13-completion lane
(counting/budgets/compaction) joins after the provider's tokenizer/descriptor contracts exist.
Cross-phase overlap: P8's sandbox-core lane may start in parallel (its prerequisites are P5/P6).

## 5. Build plan

1. **Vault first**: both backends behind one contract; unlock flow at boot step 10
   (eager/on-demand/deferred); lock zeroizes session keys + invalidates handles + cancels
   secret-dependent ops at safe boundaries; invisibility — reading a secret value is never a
   capability.
2. **One real provider adapter** (profile-driven over one wire family): `complete` →
   `classify_error` → usage extraction → then `stream`. **A second, wire-different provider follows
   to prove the abstraction** (the cross-model-review workflow needs two providers anyway).
3. **Mock-seam swap (the headline)**: the P6 loop drives real provider calls behind the
   backend-descriptor seam; the loop is unchanged; CI keeps running the recorded fixtures, a local
   `live-smoke` target hits the real API.
4. **Model strategy**: descriptors from adapter catalogs + user overrides; `Pinned`/`ByCapability`
   profiles; selection phases; per-step selection records; fallback with full revalidation;
   `NoModelAvailable` with concrete recovery options; data-boundary ordering.
5. **Token economy**: tokenizer dispatch (never against a known-mismatched family); the block-keyed
   count cache (immutable blocks ⇒ no invalidation); `TokenUsageRecord` per call — the P3
   unkeyed-scalar guard now enforced on real data; pricing snapshots + the cost projection.
6. **Real budgets**: 13 budget reports activate 07 auto-shrink (deterministic, non-destructive,
   fully recorded); ReservedOutput honored.
7. **Compaction**: explicit ContextOps through the version graph; evidence-closure preservation
   noted for P9 (09 §11.5); revision-safe (declares the view revision read, rebases/fails safely).
8. **Routing integration**: `model_route` becomes real; transport-retry vs model-fallback boundary
   exercised (17 §11.1 ↔ 16 §9 ↔ 04 §20.1).

## 6. Test obligations & acceptance evidence

- **Vault/secret suite**: golden secret-shape detector fixtures; raw `Secret` reaches none of the
  forbidden destinations that now exist (ledger/settings/events/IPC/logs); `VaultLocked` degrades
  typed, never silent-fail or proceed-without-secret; backend parity (keyring ≡ encrypted-file);
  zeroization; rotation → `CredentialRotated`; a literal secret where a `vault:<key>` belongs is
  detected and refused.
- **Provider suite**: every failure classified into the closed taxonomy (17 §10.1);
  Fatal-beats-transient — auth failures never retried (§10.2); retry hard-stops — never converts
  Fatal→Transient, never exceeds cap, never blocks indefinitely, never switches `(provider, model)`
  (§11.5); stream-terminal invariant + mid-stream errors surfaced never swallowed (§9.2);
  header-reconciliation authoritative, windows keyed by `(scope, window, dimension)` with
  `window_started_at` an anchored start value never re-keyed from a clock — roll decisions read a
  monotonic baseline (§13.3/§13.5/§13.7); **replay never re-queries a count endpoint** (§17.8); `TokenUsageRecord` carries no
  `cost_cents`/combined-total/resolved-credentials (§18.2); cost `Unknown` never coerced to 0
  (§19.4); adapter scrub validated at registration (§23.4); credentials resolve at point of use and
  never appear in any adapter struct/ledger/event/log/error trace; **no provider constants above the
  adapter** (grep); no scheduled health pings (§12.4).
- **Model-strategy suite**: **hard-filters-never-weighted**; pinned-unavailable → typed result,
  never silent fall-through (16 §7.3–7.4); selection determinism over frozen inputs; fallback never
  silently relaxes + full revalidation + new selection record (§9); per-step selection — each
  model-bound role records its own `ModelSelectionRecord`; data-boundary enforcement (§5.3); no
  output-window-by-ratio (§3.2); provider-invariance of selection logic.
- **Context completion**: token counts keyed by content identity + tokenizer (13 §10); sensitive
  parts cache-ineligible unless policy allows (§11); compaction versioned + non-destructive + never
  bypasses history (§12); virtual paging introduces no new lifecycle state or archive store (§13).
- **E2E (recorded)**: a real-adapter conversation with a tool call, attribution, cost projection,
  and a compaction trigger under a small context window — green in CI from recorded snapshots.
- **Closed-set pinning**: `ProviderError`, `ErrorClassification`, `ProviderStreamChunk`,
  `TokenSource`, role tags, selector kinds, compaction-policy families.
- Conformance matrix gains: `provider.token-source`, 17 core, 16 selection, 22 vault, 13 completion
  anchors; the P2 secret-boundary rows flip from partial to implemented for the vault scope.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `ProviderRequest`/`Response`/`StreamChunk`,
  `ProviderError`/`ErrorClassification`, `ModelCapabilityDescriptor`, `ModelProfile`/
  `ModelWorkloadRequirements`/`ModelSelectionRecord`/`FallbackPolicy`, `ModelPricing`/
  `PricingSnapshot`; migrations for usage/pricing/rate-limit (device-local) + credential-metadata
  families; **recorded provider fixtures** for deterministic adapter tests.
- **Docs**: vault contract + backends + unlock doc; the secret-boundary forbidden-destination list +
  enforcement points; provider-layer doc (Part A substrate / Part B adapter family) + the
  `ProviderProfile` authoring doc + tokenizer/token-source hierarchy doc + cost-as-projection doc;
  model-strategy selection-algorithm reference + fallback/revalidation doc; decision record for the
  first concrete adapter; glossary (ModelProfile ≠ settings profile).
- **CI/local commands**: the secret-boundary golden suite, no-unkeyed-scalar/cost-derived suite,
  error-classification suite, tokenizer-hierarchy suite, hard-filters-not-weighted suite,
  fallback-revalidation suite, and the no-provider-constants grep as named CI jobs; the local-only
  `live-smoke` target.

## 8. Exit criteria

- [ ] **M2**: a live conversation works locally against a real provider; the identical flow runs in
      CI from recorded snapshots.
- [ ] Two wire-different providers behind one adapter contract; switching changes only the selection
      record.
- [ ] The secret-boundary leak-scan suite green across all existing sinks.
- [ ] M0/M1 still green.

## 9. Locked in this phase

- **The vault namespace key format** (`provider.<provider_id>.<account_id>.<credential_id>`), the
  `resolve_for_use` signature + resolution-state enum (22 §5) — shared with 17/36.
- **The `ProviderError` taxonomy** (17 §10.1) — must align exactly with 16 §9.2 forever; the
  **`ProviderAdapter` method set**; **`ProviderStreamChunk` variants**.
- **The `TokenUsageRecord` keyed schema + `TokenSource` hierarchy + `(block_id, tokenizer_id)` cache
  keying**; **cost-as-derived-projection**.
- **`ModelCapabilityDescriptor` shape + the capability/offering/runtime split** (16 §2–§3);
  **`ModelSelectionRecord` contents** (the replay/eval artifact).
- Token-count keying + the `cache_impact` enum alignment across 13/07.
