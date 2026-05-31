# Capability Policy, Approvals, and Leases

## Status

Canonical.

## Scope

This file defines:

- the `Capability Policy` layer — the runtime evaluation system that consumes File 05's declared metadata and produces approval decisions
- effective tier resolution from declared `permission_tier`, `permission_floor`, source trust, settings, scope-level overrides, and active leases
- the `Approval Router` — the dispatch component that gates capability invocation
- approval flows: immediate allow, immediate deny, ask-user, typed-confirmation, batched approval, denial in-band as tool result, model-mediated `auto-decide`
- the `Lease` primitive — durable approval grants with the scope hierarchy from `run.approval-during-execution` (File 04 §11)
- approval-policy templates — composable validator chains the policy evaluator consults per call
- contradiction-checking across scope levels and the rules for resolving cross-scope conflicts
- touched-resource matching against lease constraints, including extension-class containment
- permission-floor enforcement and the carve-out for `Denied` via typed-confirmation
- mid-execution policy re-evaluation, lease staleness, and the revoke-and-narrow recovery from `run.recovery` (File 04 §20.2)
- the source-approval flow that runs when plugins, MCP servers, external APIs, or user-defined capabilities register
- the approval UI surface contract — the data the policy layer exposes for the UI to render approval prompts, batched approvals, lease grants, and contradiction resolution
- the policy event vocabulary emitted into the execution ledger and event stream
- settings resolution for every policy-relevant dimension

This file does not define:

- the Capability Contract field set itself — File 05 owns declaration
- the registry's resolution, lookup, or backend-binding lifecycle — `capability.registered-capability` (File 05 §10)–§16 own those
- tool-surface zones, model-request visibility, deferred loading, or capability-borrowing UX — File 07 owns those
- run lifecycle, execution graph, hook execution mechanics, or the typed hook-decision vocabulary — File 04 owns those (File 06 reuses `run.hook-integration` (File 04 §23.3)'s hook architecture)
- routing or `RunIntent` selection — File 03 owns those
- block schema, artifact lifecycle, evidence model — Files 08 and 09 own those
- ledger row format, event-stream wire format, and storage projections — `run.ledger-events-commits` (File 04 §23) owns the contract; later ledger and storage specs own the schema
- credential vault internals or trust-state cryptographic verification — File 22 owns those
- sandbox or process isolation primitives — File 23 owns those
- specific provider rate-limit tracking, circuit breakers, or polling intervals — File 17 owns provider concerns; the future MCP/External Integrations spec owns MCP and external tool-provider concerns
- approval modal layout, color palettes, modal stacking, or any UI rendering choices — File 06 specifies the data contract; UI specs own presentation

## Source Resolution

This file resolves permissions, approvals, leases, trust gates, confirmation, policy hooks, and user override material into one boundary: the shared capability policy system.

Resolved design:

- Every capability invocation passes through one policy layer; there is no agent-specific, subsystem-specific, surface-specific, or UI-specific approval system.
- Policy evaluates declarations, invocation arguments, touched resources, caller/source trust, active leases, settings, previews, validators, and user decisions.
- Leases are the durable primitive for persisted allow/deny decisions, scoped authorization, and revocation history.
- User approval, typed confirmation, policy-driven escalation, and LLM-mediated approval judgment are policy behaviors, not execution-loop special cases.
- Denials and approvals are recorded as policy decisions and surfaced back in-band so execution can continue safely when possible.

## 1. Chosen Model

Anchor: `policy.chosen-model`

ATLAS3 has one Capability Policy layer. Every consequential capability invocation passes through it — `Run`-internal model-emitted tool calls, user-invoked actions through the command palette or shortcuts, automation triggers, scheduled tasks, MCP-exposed external invocations, and capability registrations themselves.

The policy layer reads:

- the `CapabilityDeclaration` (`capability.declaration`, File 05 §3) for `permission_tier`, `permission_floor`, `capability_class`, `approval_template_id`, `data_sensitivity`, `touched_resources` expressions, `replay_class`, and execution-semantic metadata
- the `RegisteredCapability` (`capability.registered-capability`, File 05 §10) for `effective_trust`, `enabled`, `availability_status`, `collision_state`, and active aliases
- the active execution context (active conversation, active intent thread, active task, active run, active workspace, active surface, active world-model snapshot, active model route, active provider rate-limit state, invoker kind, and invoker context)
- the active settings cascade (per-capability overrides, per-source overrides, scope-level overrides, approval-posture preset)
- the active lease set (matching by capability identity pattern, scope inclusion, and inherited-constraint containment)

The policy layer produces:

- a typed `ApprovalDecision` consumed by the executor as a `Continue`, `Substitute`, `Block`, or `RedirectSuggestion` hook decision (`run.hook-integration`, File 04 §23.3 vocabulary)
- per-call resolved facts written onto the `CapabilityInvocation` record (`capability.invocation-record`, File 05 §11): resolved tier, resolved touched resources, lease used, contradictions detected, classifier result if model-mediated
- typed policy events into the execution ledger and event stream (`run.execution-ledger` (File 04 §23.1), `run.event-stream` (File 04 §23.2)): policy decision, lease grant, lease revoke, contradiction detected, floor violated, source registration approved

The `Approval Router` is the policy layer's dispatch shape. It registers as a single blocking hook subscriber on `ToolCallProposed` at convention priority `+100` (post-validation, pre-execution). It is not a parallel pipeline. Internally it composes named policy inspectors that emit intermediate verdicts; the router merges them and emits one hook decision.

`Lease` is the canonical durable approval primitive. It is a single record shape used across the `run.approval-during-execution` (File 04 §11) scope hierarchy; the scope field discriminates. There is no separate "always-allow record," "approval policy entry," or "permission grant" type.

`Approval Policy Template` is the canonical reusable rule set. Templates are named, composable, registered, and consulted by the policy evaluator. Built-in templates seed common defaults; user-authored templates extend them through the same registration mechanism.

`Source Approval Flow` is the canonical capability-source onboarding mechanism. When a plugin, MCP server, external-API definition, or user-defined capability registers, the flow surfaces declared metadata to the user, lets the user accept defaults, customize per-capability, deny outright, defer source-level policy, or cancel registration.

There is no per-subsystem or per-surface bespoke approval logic, no per-capability custom approval flow, no separate "MCP approval system," and no parallel "plugin permission system." Every approval path goes through the same router consulting the same templates against the same lease set under the same settings cascade.

The policy layer supersedes the per-tool ad-hoc gating shapes that earlier source material described as `goose mode`, `AskForApproval`, `auto-approve toggle`, `permission mode`, `YOLO classifier`, interaction-level controls, and equivalent terms. Those are vocabulary variants for one or more aspects of the system this file defines; the canonical names here are `approval-posture preset`, `approval mode`, `auto-decide`, and `Lease`.

## 2. Boundaries with Adjacent Layers

Anchor: `policy.boundaries-with-adjacent-layers`

### 2.1 With File 05 (Capability Contracts and Registry)

The boundary is sharp. File 05 owns:

- the `CapabilityDeclaration` field set, including `permission_tier`, `permission_floor`, `capability_class`, `approval_template_id`, `data_sensitivity`, `touched_resources`, `classification_mode`, `replay_class`
- the `RegisteredCapability` runtime state, including `effective_trust`, `enabled`, `availability_status`, `collision_state`
- the `CapabilityInvocation` record schema for per-call resolved facts
- registry operations: register, unregister, update, enable, disable, lookup, alias resolution, source-collision shadowing

File 06 owns:

- the resolution algorithm that turns declared metadata plus context plus active leases plus settings into an effective decision
- the lease primitive, lease lifecycle, and lease persistence
- approval-policy template registration, composition, and evaluation
- the approval router as a blocking hook
- the source-approval flow that runs at registration time
- contradiction detection and resolution

File 06 reads from declarations and registered state. It never mutates either. The per-call resolved tier, resolved touched resources, model-mediated classification result, lease used, and policy decision are written onto the invocation record (`capability.invocation-record`, File 05 §11), not back onto the declaration or the registered entry.

### 2.2 With File 04 (Execution and Run Model)

`run.call-pipeline` (File 04 §8.2) defines the capability-call pipeline. The approval router runs at step 5 ("Determine denial, approval need, persisted decision, or active lease"). `run.approval-during-execution` (File 04 §11) establishes the permission-tier hierarchy, the `Lease` definition with full scope hierarchy, the named `auto-decide` mode, scope-based batching, and contradiction-checking across scope levels. `run.hook-integration` (File 04 §23.3) establishes the typed hook decision vocabulary (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`), priority convention, timeout-with-authority-based-fail-direction, and per-error-class retry behavior.

File 06 inherits all of those. It does not redefine the tier set, the lease scope hierarchy, the hook decision shape, or the hook timeout semantics. It specifies how each is applied in policy evaluation.

The denial-in-band rule (`run.denial-is-in-band`, File 04 §8.3) is a load-bearing invariant. A denied capability call produces a typed result block linked to the proposal; the agent loop receives it as ordinary execution input and decides what to do (ask the user, narrow scope, try an alternative, stop). File 06's typed errors and approval-decision events conform to this contract.

### 2.3 With Cross-Cutting Substrate

The approval router is a blocking subscriber on `ToolCallProposed` (per `run.hook-integration`, File 04 §23.3 and the canonical event-bus pattern). Other policy events emit through the same bus. The event envelope (`conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`) carries enough context for policy decisions to attribute correctly across parallel runs and concurrent worktrees.

Settings are read through the settings system (per `core.settings-system`, File 01 §6.8). The settings cascade is the canonical conversation → workspace → global → overlay → declared default order. File 06 does not introduce a parallel settings store.

Typed errors flow through the typed-error envelope (per `core.typed-errors`, File 01 §6.9). Policy denials, floor violations, contradiction errors, and lease-stale signals are typed variants the agent and UI consume by exhaustive pattern match.

State awareness is consulted for context: the active surface, focused element, primary panel, ui-mode, and the available-capability set produced by `availability_predicate` evaluation (`capability.availability-predicate`, File 05 §15.2) all participate in policy decisions. State changes that affect lease validity (workspace switch, panel change, ui-mode transition) trigger lease revalidation per §10.

### 2.4 Boundary

File 06 is the runtime evaluation layer. It owns no storage schema, no UI rendering, no execution mechanics, and no capability declarations. Storage of leases and policy events is File 20's concern; presentation of approval prompts and lease management UIs is the future UI Shell and UI Customization specs' concern; the actual execution of approved capability calls is File 04's concern.

## 3. The Approval Router

Anchor: `policy.approval-router`

### 3.1 Definition

The `Approval Router` is the canonical dispatch component of the Capability Policy layer. It is a single blocking hook subscriber on the `ToolCallProposed` event at convention priority `+100`. It receives the proposed capability invocation, consults declaration metadata, registered state, active leases, settings, world-model snapshot, and policy templates, and emits one typed `ApprovalDecision` to the executor.

### 3.2 Position in the Capability-Call Pipeline

The router sits at `run.call-pipeline` (File 04 §8.2) step 5 of the capability-call pipeline:

1. Resolve capability (File 05 registry)
2. Validate input (`capability.input-validators`, File 05 §8.1 validators)
3. Produce proposal
4. Run validators and policy checks
5. **Determine denial, approval need, persisted decision, or active lease — the Approval Router** *(this section)*
6. Execute with declared isolation and concurrency semantics
7. Stream partials when supported
8. Record observations and result
9. Validate postconditions
10. Commit or expose output

The router runs after structural validators (priority `0`) so its evaluation sees the post-validation payload. Audit and logging hooks at priority `-100` capture pre-router state for forensic reconstruction.

### 3.3 Internal Composition — Policy Inspectors

Anchor: `policy.internal-composition-policy-inspectors`

The router internally composes named `policy inspectors`, each emitting an intermediate verdict. The router merges verdicts and produces the final decision. Inspector composition is a registry-managed list; built-in inspectors register at startup, plugins and extensions register additional inspectors at load time through the same registration mechanism (subject to the source-approval flow per §9).

Required built-in inspectors:

- `tier-resolution`: computes the effective tier from declared `permission_tier` (via `TierResolver` per `capability.tier-resolver` (File 05 §5.2)), `permission_floor`, source trust, scope-level overrides, and active leases — produces `EffectiveTierDecision`
- `template-evaluation`: consults the capability's `approval_template_id` and any active reusable-policy-rule leases; runs the template's validator chain — produces template verdicts (`Allow`, `Deny`, `Ask`, `Escalate`, `NoOpinion`)
- `touched-resource-matching`: resolves declared `touched_resources` expressions against arguments and matches each against active lease constraints — produces matched-lease set or no-match
- `contradiction-detection`: compares verdicts across scope levels and flags conflicts — produces `Vec<Contradiction>`
- `classifier-mediation`: when `auto-decide` is active or the capability declares a `ModelMediated` classification mode for relevant fields, invokes the configured classifier model — produces `ClassifierResult { decision, confidence, reasoning }` or skips
- `risk-classification`: applies the canonical CT.20-derived class defaults (`InternalAnalysis`/`ActionExternal`/`UserArtifact`) and trust-driven escalations — produces tier adjustments

Inspectors declare an authority class:

- `observe_only` — may emit notes, risk facts, and explanations, but no verdict
- `narrowing_only` — may emit `Ask`, `Deny`, `Escalate`, or stricter constraints, but cannot produce an effective `Allow`
- `allow_capable` — may contribute `Allow` verdicts only when registered by built-in, subsystem, verified, or explicitly user-approved policy sources
- `substitute_capable` — may propose `Substitute`, but only for declared narrowing or transparent redirects

Community, unverified, plugin, MCP, API, and user-defined inspectors default to `narrowing_only` until the user explicitly upgrades their authority through source approval or settings. No inspector can bypass `permission_floor`, typed-confirmation, contradiction detection, or touched-resource constraints.

Inspector ordering is convention: `tier-resolution` first, `template-evaluation` second, `touched-resource-matching` third, `risk-classification` fourth, `classifier-mediation` fifth (only when active), `contradiction-detection` last. The router accumulates verdicts; a `Deny` verdict from any required inspector wins immediately. An `Ask` verdict promotes the decision to ask-user unless a later inspector escalates further.

User-defined and plugin-defined inspectors register with explicit priority within the inspector chain. They cannot be placed before `tier-resolution` (the floor-and-trust ground truth must run first) or after `contradiction-detection` (contradictions must be the last word). Their verdicts compose the same way: `Deny` wins, `Ask` promotes, `Allow` is permissive only when no other inspector dissents.

### 3.4 Output

The router emits one of four typed `ApprovalDecision` outcomes, mapped to the `run.hook-integration` (File 04 §23.3) hook decision vocabulary:

- `Continue { reason, lease_used? }` — proceed with the proposed payload; emit `PolicyDecisionMade { decision: Continue, ... }`
- `Substitute { new_payload, reason, substitution_kind }` — proceed with a router-modified payload; valid only for declared constraint narrowing, sensitivity-preserving redaction, sandbox narrowing, or transparent redirect to a safer equivalent capability. The policy event records original and substituted payloads with sensitivity redaction. Semantic target or action changes require ask-user, not silent substitution.
- `Block { reason, error_kind }` — abort the proposed action; the executor records a denial and the typed reason flows in-band as a tool result per `run.denial-is-in-band` (File 04 §8.3); emit `PolicyDecisionMade { decision: Block, ... }`
- `RedirectSuggestion { capability_id, args, reason }` — abort the proposed action and signal that the agent should retry using a suggested capability (e.g., `shell.exec` with `find` redirected to `file.search` per CT.16's dedicated-tool preference); the agent loop consumes this as a typed retry signal per `run.hook-integration` (File 04 §23.3)

The router never invents new contract semantics. Its decision is one of these four shapes. Any other outcome is an Explicit Rejection (§17).

### 3.5 Failure Mode

The approval router is an authoritative blocking hook (per `run.hook-integration`, File 04 §23.3 fail-direction rules). A timeout or error fails closed: the synthesized decision is `Block { reason: "approval router timeout" | "approval router error" }`. The executor records the timeout, emits the standard `Block` event, and the agent receives the typed denial in-band.

Per-error-class retry behavior follows `run.hook-integration` (File 04 §23.3): transient infrastructure errors (typed as such in the policy-event vocabulary) may retry once within the configured timeout window before failing closed. Configuration errors (missing template, unresolved classifier model, missing inspector) do not retry; they fail closed immediately and produce a typed `PolicyConfigurationError` event for diagnostics.

The router's blocking timeout default is configurable per-error-class through settings. It is not a hardcoded constant.

### 3.6 Boundary

The router consumes typed proposals from `ToolCallProposed` and produces typed decisions back onto the hook bus. It does not own execution, sandbox selection, capability registration, ledger storage, or UI rendering. Decisions that require user interaction (ask-user, typed-confirmation) flow through the approval UI surface contract (§13); the router awaits the user's typed response over the same event bus and then emits its decision.

## 4. Effective Tier Resolution

Anchor: `policy.effective-tier-resolution`

### 4.1 Definition

`Effective Tier Resolution` is the deterministic algorithm that produces the runtime tier for a given proposed call. It is the canonical input to the approval flow selection and the lease evaluation step.

### 4.2 Algorithm

The resolution proceeds in fixed order:

1. **Declared tier**. Resolve the capability's declared `permission_tier` (`capability.tier-resolver`, File 05 §5.2). For `TierResolver::Static(tier)`, the result is the static value. For `TierResolver::Dynamic(resolver_id)`, the registered argument-aware resolver evaluates the proposal arguments and the active world-model snapshot deterministically and returns a tier. The resolver's behavior is stable given the same inputs (per `capability.tier-resolver`, File 05 §5.2).
2. **Floor enforcement**. The result is clamped from below by the capability's `permission_floor` (`capability.permission-floor`, File 05 §5.4). If the resolver returned a tier weaker than the floor, the floor wins. The floor is never lowered by any subsequent step. Any later step that would produce a tier below the floor produces a `PolicyFloorViolated` event and the floor's tier is used instead.
3. **Trust narrowing**. The registered entry's `effective_trust` (`capability.trust-source-approval-flow`, File 05 §9.2) applies a trust-driven minimum tier:
   - `System`, `Verified`, `User` — no trust-driven narrowing
   - `Community` — minimum effective tier is `UserApproval` (one-tier escalation from `WorkspaceWrite` or below)
   - `Unverified` — minimum effective tier is `UserApproval` and the first invocation of each such capability in a given conversation additionally requires per-call ask-user (no `AlwaysAllow` lease honored without an explicit user upgrade of the source's trust)
   Trust narrowing never crosses the floor in either direction. A `Community` capability whose floor is `Denied` remains `Denied`; a `Community` capability whose declared tier is already `UserApproval` is unchanged.
4. **Scope-level setting overrides**. Per-capability and per-source tier ceilings from the settings cascade (conversation → workspace → global → overlay → default) apply. A user-set tier ceiling can never lower below the floor (the floor wins) but can raise above the declared tier (the user can require approval for a normally `WorkspaceWrite` capability within a specific conversation or workspace).
5. **Lease lookup**. The active lease set is consulted. A lease applies when:
   - its `capability_match` covers the proposed capability id (exact match, family glob, or pattern)
   - its `scope` includes the active execution context (the call's run, intent thread, task, conversation, workspace, or globally; `single_proposal`-scope leases never persist past one call; `reusable-policy-rule`-scope leases apply globally)
   - its `invoker_kind` constraint, if present, matches the call's invoker kind and context
   - its `inherited_constraints` contain the proposed call's resolved touched resources (per §6)
   - its `status` is `Active` (not `Stale` or `Revoked`)
   - the call satisfies any per-lease conditions (argument-shape match, idempotency requirement, max-invocations limit)
   When multiple leases apply, narrower scope wins; among same-scope leases, deny-wins. A matching `AlwaysAllow` lease produces direct execution at the lease's tier (still bounded by the floor); a matching `AlwaysDeny` lease produces immediate `Block`.
6. **Decision selection**. The resulting tier and the lease/template verdicts produce the terminal decision: direct execution, ask-user, typed-confirmation, deny, or model-mediated escalation per §5.

The output of resolution is a typed `EffectiveTierDecision` carrying the resolved tier, the contributing scope level (conversation/workspace/global/lease/floor), the lease used (if any), the contradictions detected (if any), and the human-readable reason. This record flows onto the invocation record per `capability.invocation-record` (File 05 §11).

### 4.3 Required Outcomes

For every proposed capability invocation, effective tier resolution produces exactly one terminal outcome:

- `direct_allow` — the call proceeds without user interaction; `PolicyDecisionMade` emitted with the contributing reason
- `direct_deny` — the call produces a typed denial; the agent receives in-band per `run.denial-is-in-band` (File 04 §8.3)
- `ask_user` — the approval UI surface contract is invoked (§13); the call awaits user response
- `typed_confirmation` — the typed-confirmation flow is invoked (§7); cannot be skipped or auto-resolved
- `model_mediated` — the auto-decide classifier is invoked (§8); the result either resolves to `direct_allow`, `direct_deny`, or escalates to `ask_user` per the classifier's output and confidence

The tier-to-outcome mapping is canonical:

- `Denied` → `direct_deny` always; the only path to execution is the typed-confirmation override of `Denied` per §7.4 (also routed through `typed_confirmation`)
- `ReadOnly` → `direct_allow`
- `WorkspaceWrite` with proposal contained within the active workspace → `direct_allow`
- `WorkspaceWrite` with proposal escaping the workspace → effective tier escalates to `UserApproval` and the rule re-applies
- `UserApproval` → `direct_allow` if a matching `AlwaysAllow` lease is active; `direct_deny` if a matching `AlwaysDeny` lease is active; `model_mediated` if `auto-decide` is configured for this capability and active; otherwise `ask_user`
- `Unrestricted` → `direct_allow` only when the relevant invoker/settings context enables `agent.unrestricted_mode`; otherwise the rule for `UserApproval` applies (per `run.approval-during-execution`, File 04 §11). `Unrestricted` is still policy-governed: it emits events, honors source trust, floors, typed-confirmation, touched-resource constraints, and user narrowing.
- typed-confirmation variant of `UserApproval` → `typed_confirmation` always; `auto-decide` and `AlwaysAllow` leases never lift it

The mapping is deterministic. Any policy decision that produces an outcome outside this set is an Explicit Rejection (§17).

### 4.4 Boundary

Tier resolution is purely a function of declared metadata, registered state, settings, leases, and the world-model snapshot. It does not call out to external services beyond what is already required by `TierResolver::Dynamic` resolvers and the model-mediated classifier. Tier resolution must remain fast enough to run on every proposed call; expensive or speculative decisions live in the classifier mediation step (§8) and are off by default.

## 5. Approval Flows

Anchor: `policy.approval-flows`

### 5.1 Definition

An `Approval Flow` is the canonical sequence of steps the policy layer executes to reach a terminal decision when tier resolution produces an outcome other than `direct_allow` or `direct_deny`. There are four flows: `ask-user`, `typed-confirmation`, `auto-decide`, and `batched approval`.

### 5.2 Ask-User Flow

The `ask-user` flow executes when:

- effective tier is `UserApproval` (including `Unrestricted` with `agent.unrestricted_mode` off) and no matching `AlwaysAllow` lease is active
- a policy template emits an `Ask` verdict
- a contradiction is detected and the user must resolve it
- a stale lease is encountered (per §10) and the user must re-grant or revoke

Required steps:

1. Construct an `ApprovalRequest` payload (§13.2) carrying the capability identity, resolved arguments (with declared `data_sensitivity` redactions applied), reason, resolved tier, floor, resolved touched resources, available lease options, contradictions, invoker identity, resolved proposal facts, and classifier result if model-mediated produced a low-confidence verdict
2. Emit `ApprovalRequested { request_id, capability_id, ... }` through the event bus with the canonical envelope
3. Await the typed `ApprovalResponse` over the same bus; no timeout is required unless a settings profile explicitly configures one. If a configured timeout expires, the configured fail direction applies, with fail-closed as the safe profile.
4. If the user's choice creates a lease (any of `AlwaysAllow`, `AllowForRun`, `AllowForIntentThread`, `AllowForTask`, `AllowForConversation`, `AllowForWorkspace`, `AllowGlobal`, or any `Deny*` variant beyond `DenyOnce`), persist the lease per §11; emit `LeaseGranted` event
5. If the user's choice is `AllowOnce` or `DenyOnce`, no lease is created; the decision is recorded as a single-proposal policy event
6. Emit `ApprovalGranted` or `ApprovalDenied` and the corresponding `PolicyDecisionMade`
7. Return the typed `ApprovalDecision` (`Continue` or `Block`) to the executor through the hook bus

The `ApprovalResponse` payload allows the user to narrow the lease's `inherited_constraints` from the defaults derived from the capability's declared touched resources. For example, an `AlwaysAllow` for `file.edit` defaults to "files within the active workspace"; the user may narrow to "files under `src/` within the active workspace." Narrowed constraints are typed and machine-checkable per `capability.touched-resources` (File 05 §6).

### 5.3 Typed-Confirmation Flow

The `typed-confirmation` flow executes when the capability's approval template requires it, when a `Denied`-tier capability is invoked through the override carve-out, or when a registered policy template explicitly marks the call as typed-confirmation regardless of tier. Per §7.

### 5.4 Auto-Decide Flow

The `auto-decide` flow executes when the capability or its capability family is configured for model-mediated approval and the configuration is active in the current scope. Per §8.

### 5.5 Batched Approval Flow

Anchor: `policy.batched-approval-flow`

When a natural execution boundary already has multiple ask-user decisions pending, the policy layer presents them as one batched `BatchApprovalRequest` (§13.3) where possible. Natural boundaries include one model response, one programmatic step, one script or workflow step, one child-run spawn group, or one executor dispatch batch. The user resolves each item independently or accepts/denies the batch.

A typed-confirmation item never participates in a batch — typed-confirmation always presents alone. A batched approval that includes a `Denied`-tier item shows the item as already-denied (the typed-confirmation override path is a separate single-item flow).

Batching granularity is configurable by surface and policy profile: single turn, run, child run, agent group, conversation, workspace, or other registered grouping keys. New groupers must be structural selectors over already-pending approvals, not timers. The runtime never delays approval emission solely to collect future items. Maximum batch size is a settings dimension; overflow splits structurally.

### 5.6 Boundary

Approval flows produce typed decisions through the same hook bus. The user-facing presentation of each flow (conversation-inline approval card, modal dialog, voice confirmation request, command-palette inline confirmation) is owned by the future UI specs; the policy layer specifies the data contract (§13), not the rendering.

## 6. Touched-Resource Matching Against Lease Scope

Anchor: `policy.touched-resource-matching-against-lease-scope`

### 6.1 Definition

`Touched-Resource Matching` is the algorithm that determines whether a proposed call's resolved touched resources fall within an active lease's `inherited_constraints`. A lease applies to a call only when match succeeds.

### 6.2 Resolution

The capability's declared `touched_resources` (`capability.touched-resources`, File 05 §6) are typed expressions referencing input-schema field paths (`args.path`, `args.command`, `args.url`, etc.). The policy layer resolves each expression against the proposed call's arguments to produce a concrete set of touched resources, each carrying its `class`, `access`, and resolved scope (concrete path, host, port, env-var name, settings key/scope, process group, credential vault key, sub-agent type id, etc.).

For extension classes registered per `capability.extension-resource-classes` (File 05 §6.3), the registered containment predicate is invoked to produce the resolved scope.

### 6.3 Containment

The lease's `inherited_constraints` are typed predicates over the same resource classes. Containment is checked per resource:

- `filesystem` — path subtree containment (the lease constrains "paths under workspace root with subdir `src/`"; the call's resolved path must be canonicalized and lie within that subtree)
- `network` — host-set containment (the lease constrains "hosts in the set `{api.example.com, *.example.org}`"; the call's resolved host must match)
- `process` — process-group containment (the lease constrains "processes in the run-scoped group"; the call's resolved process must belong to that group)
- `env` — env-var-name allowlist containment
- `setting` — key, key-prefix, owner, category, scope, or profile-context containment
- `credential` — vault-key allowlist containment
- `model-call` — provider/model identity containment
- `browser-session` — session-id containment
- `ui-element` — element-id containment (typically run-scoped)
- `sub-agent` — sub-agent-type-id containment
- `scheduler` — schedule-id containment
- registered extension classes — registered containment predicate per the extension's declaration

A lease applies only when every resolved touched resource is contained within the lease's constraints for its class. If any resolved resource escapes the lease's constraints, the lease does not apply and the next matching lease is checked, falling through to ask-user if no lease applies.

### 6.4 Lease Selection on Multiple Matches

When multiple leases match a proposed call, the policy layer selects the active lease by:

1. Narrower scope wins. The scope ordering is `single_proposal < run < intent_thread < task < conversation < workspace < global < reusable_policy_rule`. A lease at `conversation` scope wins over one at `workspace` scope for the same capability and constraints.
2. Among same-scope matches, `AlwaysDeny` wins over `AlwaysAllow`. This is the deny-wins rule.
3. Among same-scope, same-decision matches, the most-recently-granted lease wins.

The selected lease's identity is recorded on the invocation record as `lease_used` per `capability.invocation-record` (File 05 §11).

### 6.5 No-Match Fallthrough

When no lease matches a proposed call, tier resolution falls through to the default tier-driven outcome (§4.3). A capability declared at `UserApproval` with no matching lease produces ask-user (or auto-decide if configured); a capability declared at `WorkspaceWrite` with no matching lease produces direct allow (subject to workspace containment per §4.3).

### 6.6 Boundary

Touched-resource matching is deterministic given the resolved arguments and the active lease set. The expression grammar lives in `capability.resource-expressions` (File 05 §6.4) (current illustrative shapes) or the future capability-schema appendix; File 06 specifies the matching algorithm and the containment semantics. Extension-class registration includes a containment predicate per the extension's declaration; missing or unparseable predicates make leases referencing the extension class invalid (the registration fails per `capability.extension-resource-classes` (File 05 §6.3)'s proposal-first rule).

## 7. Permission Floor and Typed-Confirmation

Anchor: `policy.permission-floor-typed-confirmation`

### 7.1 Permission Floor

Anchor: `policy.permission-floor`

The `permission_floor` declared on a capability (`capability.permission-floor`, File 05 §5.4) is the absolute minimum tier. It is the canonical floor for irreversible high-blast-radius operations: account deletion, destructive publish, force-push to a protected branch, system shutdown, credential export, irreversible publishing operations, system file edits, machine-scope registry mutation, plus any user-marked operation per settings.

The floor never lowers. Settings cannot lower it. Leases cannot bypass it. Trust upgrades cannot lower it. `agent.unrestricted_mode` does not lower it. Cross-scope policy overrides cannot lower it. Any attempt to lower it produces a `PolicyFloorViolated` event and the floor wins.

### 7.2 Definition of Typed-Confirmation

`Typed-Confirmation` is a variant of the `UserApproval` tier that requires the user to type an exact confirmation string before the call proceeds. The string is a value the user can recognize as a deliberate intent — the action's target identifier, the exact path, the branch name, the account name, an explicit phrase tied to the operation. A capability declares typed-confirmation through its `approval_template_id` referencing a template that carries the typed-confirmation requirement.

### 7.3 Properties

Typed-confirmation:

- always asks; no `AlwaysAllow` lease, scope-level override, settings preset, trust upgrade, or `agent.unrestricted_mode` lifts it
- never participates in batched approval (§5.5); a typed-confirmation call always presents alone
- never fast-paths through `auto-decide`; even if the classifier returns high-confidence allow, the typed-confirmation request still appears
- emits a single-proposal policy event regardless of user choice; no `AlwaysAllow` lease can be granted from a typed-confirmation flow
- the typed-confirmation approval-text template carries the confirmation-string pattern, the human-readable warning, and the rendered preview of what the call will do

### 7.4 The `Denied` Carve-Out

Anchor: `policy.denied-carve-out`

A capability with effective tier `Denied` is not invocable by default. The only path through `Denied` is the typed-confirmation override: the capability's approval template may declare `denied_override_via_typed_confirmation: Required`, which enables a one-time override per invocation. The user types the exact confirmation string and the call proceeds; this is recorded as a `Denied`-override event in the policy ledger and is single-proposal scope (no `AlwaysAllow` lease can be created from a `Denied`-override flow).

A capability whose `permission_floor` is `Denied` and whose template does not declare the typed-confirmation override has no path to execution — agent or user. This is the canonical shape for operations the system declares as never-auto-approvable: force-push to a protected branch, account deletion, and similar.

### 7.5 Examples

- `git.push --force` to a branch name in the configured protected-branch list: `permission_tier: WorkspaceWrite`; `permission_floor: Denied`; approval template requires typed-confirmation override. Effective tier `Denied`; only path is type the branch name to confirm.
- `system.shutdown`: `permission_tier: UserApproval`; `permission_floor: Denied`; approval template requires typed-confirmation override.
- `account.delete`: `permission_tier: UserApproval`; `permission_floor: Denied`; approval template requires typed-confirmation override with the account identifier as confirmation string.
- `credential.export`: `permission_tier: UserApproval`; `permission_floor: Denied`; approval template requires typed-confirmation override; the exported credential is sanitized in the resulting tool result per `data_sensitivity: Secret` declaration.

The list is illustrative. The canonical rule is: any capability that is irreversible and whose impact extends beyond what the user can rapidly undo within the active workspace is a candidate for a `Denied` floor with typed-confirmation override.

### 7.6 Boundary

Typed-confirmation is a policy-flow shape. The actual rendering of the typed-confirmation UI (the modal, the input field, the preview, the cancel button) is owned by the future UI specs. File 06 specifies the data contract: the approval-text template, the confirmation-string pattern, the preview payload, and the typed `TypedConfirmationResponse` carrying the user's typed string. The policy layer validates the typed string against the pattern; mismatch produces a typed `TypedConfirmationMismatch` decision and the flow returns to ask the user again or cancel.

## 8. Auto-Decide Mode

Anchor: `policy.auto-decide-mode`

### 8.1 Definition

`Auto-Decide` is the model-mediated approval mode named in `run.approval-during-execution` (File 04 §11). A designated classifier model evaluates a proposed call against a configured policy model-request template and returns a typed `ClassifierResult` carrying decision, confidence, and reasoning. Auto-decide is opt-in per capability or per family and never the default.

### 8.2 Configuration

Auto-decide configuration is a settings-resolved value with the standard cascade (conversation → workspace → global → overlay → default). Configuration carries:

- `enabled` per capability or per family — opt-in flag
- `classifier_model_id` — the model used for classification, resolved through the model-strategy layer per File 04
- `policy_model_request_template_id` — the configured model-request template the classifier evaluates against (registry-managed per File 05's broader registry-of-typed-resources pattern; user-authored templates permitted under proposal-first registration)
- `confidence_threshold` — minimum confidence for the classifier's verdict to be honored; exact defaults belong to settings profiles and must be tested, not hardcoded here
- `consecutive_denial_fallback` — configurable count after which repeated auto-denials of the same capability in the same scope fall through to ask-user
- `consecutive_approval_check_in` — configurable count after which repeated auto-approvals of the same capability in the same scope present a "still happy with this?" check-in to the user
- `escalation_path` — what to do when classifier confidence is below threshold: `ask_user`, `direct_deny`, or `direct_allow` (only valid when the capability's declared tier is `ReadOnly` or below)

### 8.3 Flow

When auto-decide is active for a proposed call:

1. The policy layer constructs a classifier model request from the configured `policy_model_request_template_id`, the capability declaration, the proposal arguments, the resolved touched resources, the active context (run, intent thread, task, conversation, workspace, invoker), the recent policy history (prior approvals/denials of the same capability), and any user-authored guidance attached to the policy template
2. The classifier model is invoked as a policy-internal model step through the model-strategy layer. It honors provider allowlists, data sensitivity, rate limits, and model settings, but does not emit a nested `ToolCallProposed`, cannot call tools, and cannot recursively ask for approval through the same approval router.
3. The classifier returns a `ClassifierResult { decision, confidence, reasoning }`
4. If `confidence >= confidence_threshold` and the decision is `Allow` or `Deny`, the result is honored; emit `AutoDecideClassification { request_id, decision, confidence, reasoning, fell_back: false }` and produce the corresponding `Continue` or `Block`
5. If `confidence < confidence_threshold` or the decision is `Ask` or `Escalate`, fall through per `escalation_path`
6. Apply the consecutive-denial-fallback and consecutive-approval-check-in counters per capability per scope; on threshold, fall through to ask-user
7. The classifier result is always recorded on the invocation record per `capability.invocation-record` (File 05 §11); below-threshold results are recorded as well (with `fell_back: true`) for offline policy tuning

### 8.4 Properties

- the classifier result is advisory: when policy still requires a human decision (typed-confirmation, `Denied` floor, contradiction, lease re-grant), the classifier does not override
- the classifier never lifts `permission_floor`, never bypasses `Denied`, never lifts `typed-confirmation`
- the classifier model-request template is registry-managed and inspectable; the user can view, customize, or replace the template for any capability or family through settings
- per-call cost is one extra model invocation per proposed call when active; settings let users limit cost (e.g., enable auto-decide only for `ReadOnly` capabilities, or only when the model-strategy layer has a low-cost classifier available)
- auto-decide is per scope: the user may enable it globally, per workspace, per conversation, per capability, or per family

### 8.5 Boundary

Auto-decide composes with the rest of the policy machinery. It does not replace tier resolution, lease lookup, contradiction detection, or floor enforcement. Its output is one more verdict among the policy inspector chain (§3.3); the router merges it with the rest. The classifier model and policy model-request template are configurable resources, not hardcoded dependencies; a capability without an active auto-decide configuration follows the default tier-driven flow.

## 9. The Source-Approval Flow

Anchor: `policy.source-approval-flow`

### 9.1 Definition

The `Source-Approval Flow` runs when a capability source registers — a plugin loads, an MCP server connects, an external-API definition is loaded, or a user-defined capability is added through the runtime-registration capability path (`capability.runtime-mutation`, File 05 §16.2). The flow surfaces the source's declared metadata to the user before its capabilities become invocable, lets the user accept declared defaults, customize per capability or source, deny outright, defer source-level policy, or cancel registration.

### 9.2 Trigger Threshold

The flow is triggered when the source risk summary crosses the configured review threshold. Declared tier is one input, not the whole trigger. The risk summary includes highest declared tier, highest permission floor, source trust, touched-resource classes, data sensitivity, external network or credential access, model-call access, filesystem scope, process/sandbox access, browser/UI/scheduler/sub-agent access, capability count and families, backend kinds, and whether the source registers policy inspectors, templates, or settings. Users can tune thresholds by source class and resource class.

### 9.3 Proposal Preview

When triggered, the policy layer constructs a `SourceRegistrationProposal` carrying:

- source identity: kind (`Plugin`, `McpServer`, `Api`, `UserDefined`, `Subsystem`), id, version, install path or remote URL, declared author, declared trust hint
- declared capabilities: each capability's id, display name, description, declared `permission_tier` (with `TierResolver` shape if dynamic), declared `permission_floor`, declared `capability_class`, declared `touched_resources`, declared `replay_class`, declared `data_sensitivity`, declared `approval_template_id`
- source risk summary: the computed review trigger facts and why review is or is not required
- registered-entry trust state: source-authored trust hint, verification evidence when present, user trust override when present, and `effective_trust` (computed per `capability.trust-source-approval-flow` (File 05 §9.2))
- backend kind summary: which `backend_kind` values appear (per `capability.backend-binding-lifecycle`, File 05 §10.4)
- policy extension summary: any policy inspectors, templates, settings, or source-level rules the source attempts to register, including inspector authority classes
- optional: a registered linkage to a pre-existing source-approval-policy lease (e.g., a previously-approved version of the same source — the user can choose to inherit the prior decisions or review fresh)

The proposal is rendered as a typed `SourceRegistrationProposal` event for the UI to consume per §13.

### 9.4 User Options

The user resolves the flow by choosing one of:

- **Accept declared defaults** — every declared capability registers at its declared tier with default trust-driven narrowing (per §4.2 step 3); no per-capability lease is created; trust state is computed from source-authored trust hint, verification evidence, and any user trust override
- **Customize per capability** — for each declared capability, the user may set a per-capability tier ceiling (capped above by the floor), grant a pre-approval (an `AlwaysAllow` reusable-policy-rule lease for the capability), or deny outright (an `AlwaysDeny` reusable-policy-rule lease); the policy layer composes these with the declared defaults
- **Customize per source** — set a user trust override or default policy behavior for the source; this changes the trust-narrowing input without mutating the source-authored trust hint
- **Deny outright** — the source's capabilities register but are not invocable; effectively each capability gets an `AlwaysDeny` reusable-policy-rule lease at registration time; the user can revisit and approve later through settings
- **DeferSourcePolicy** — explicit choice to register the source while each capability remains gated by the configured fallback policy (`ask_each_time`, `require_explicit_approval`, or `ask_on_first_use`)
- **CancelRegistration** — registration does not complete, or the source remains catalogued only with capabilities disabled until future review

### 9.5 Persistence

User decisions persist as:

- user trust override on the registered entry per `capability.registered-capability` (File 05 §10)
- reusable-policy-rule leases (per §11) for any per-capability pre-approvals or denials
- capability-specific tier overrides through the settings cascade
- per-source default-behavior selection through the settings cascade

The user may revisit and edit any of these through settings or through the capability registry's source-management surface (the future UI specs render the management surface). Edits emit the same `LeaseGranted`/`LeaseRevoked`/`SourceRegistrationApproved` events for audit consistency.

### 9.6 Trust Mapping Defaults

Anchor: `policy.trust-mapping-defaults`

The default trust-driven escalation for sources whose risk summary requires review is:

- `Verified` / `System` — declared capabilities register at declared tiers; trust narrowing does nothing
- `Community` — declared capabilities at `WorkspaceWrite` or below register with effective tier `UserApproval`; declared capabilities at `UserApproval` or above are unchanged
- `Unverified` / `Sideloaded` — declared capabilities at `WorkspaceWrite` or below register with effective tier `UserApproval` and require per-call ask-user (no `AlwaysAllow` lease honored without explicit user upgrade); declared capabilities at `UserApproval` or above register with the typed-confirmation flow on first use

The trust mapping is settings-overridable per source. The proposal preview surfaces the trust state and the resulting effective-tier escalations so the user can decide explicitly.

### 9.7 Properties

The source-approval flow is itself a capability invocation: `policy.review_source_registration` (or equivalent — the canonical id is registered at runtime), with a `UserApproval`-tier requirement (or `typed_confirmation` for `Sideloaded` sources at the user's option through settings). The flow's invocation produces standard policy events. Closing, dismissing, or failing to complete the flow is `CancelRegistration`, not `DeferSourcePolicy`; it never silently registers an invocable source.

### 9.8 Boundary

The flow's UI rendering (the source-approval modal, the per-capability customization controls, the trust override toggle, the deny-outright button) is owned by the future UI specs. File 06 specifies the data contract — the proposal shape, the user's response shape, the persisted lease shape — and the resolution algorithm. The flow's actual capability registration mechanics (admit declaration, resolve backend binding, emit `CapabilityRegistered`) are owned by `capability.registered-capability` (File 05 §10) and `capability.lifecycle` (File 05 §16); File 06 gates whether registration completes, not how it executes.

## 10. Mid-Execution Policy Re-Evaluation

Anchor: `policy.mid-execution-policy-re-evaluation`

### 10.1 Lease Lifecycle States

A `Lease` transitions through three states:

- `Active` — the lease's `revocation_conditions` do not match the current state; the lease applies during effective tier resolution
- `Stale` — at least one revocation condition matches; the lease no longer applies but is preserved for inspection and potential re-grant; the next invocation that would have used the lease produces ask-user with the staleness reason surfaced
- `Revoked` — the lease has been explicitly revoked (manually by the user, via policy template change, or via capability unregistration); the lease no longer applies and is retained for audit unless the user explicitly prunes it through storage controls

State transitions are driven by `revocation_conditions` evaluation and by explicit revocation calls.

### 10.2 Revocation Conditions

A lease's `revocation_conditions` are typed predicates over the active state. Required canonical conditions:

- `workspace_switch` — the active workspace differs from the lease's `grant_context.workspace_id`
- `policy_change` — a settings change, lease grant or revocation, or template change has altered the policy state in a way the lease's grant assumed; the lease's grant_context records the relevant policy snapshot id
- `grant_evidence_unavailable` — the policy layer cannot load or resolve the lease's referenced grant evidence, policy snapshot, touched-resource constraints, source/capability identity, or required world-model/artifact reference
- `capability_unregistration` — a capability the lease applies to has been unregistered or its source has disconnected
- `trust_downgrade` — the source's `effective_trust` has decreased since the lease was granted (for source-level leases)
- `expiry_deadline` — the lease's `expires_at` (if set) has passed
- `manual` — the user has explicitly revoked the lease

Capabilities and policy templates may declare additional revocation conditions specific to their semantics; the conditions register through the same registry mechanism and follow the same evaluation pattern. Any condition that cannot be evaluated declaratively against typed state is rejected — ad-hoc procedural revocation is an Explicit Rejection (§17).

### 10.3 Re-Evaluation Triggers

The policy layer re-evaluates active leases when:

- the active workspace changes (per state-awareness events)
- a settings change affects a policy-relevant key
- a lease is granted, narrowed, or revoked (state changes can cascade)
- a context or storage event affects grant evidence availability
- a capability is unregistered
- a registered-entry trust override changes
- on demand through `policy.revalidate_leases` (a `ReadOnly` capability)

Re-evaluation is bounded — it runs only for leases whose `revocation_conditions` could be affected by the trigger, not for the whole lease set. Each revocation condition declares trigger affinity: trigger kinds, affected scope fields, affected resource classes, affected setting keys or prefixes, and whether evaluation is synchronous or must enqueue bounded revalidation work. Ordinary context compaction does not stale a lease; only durable grant evidence becoming unavailable or unresolvable can do that.

### 10.4 Stale Lease Handling

When a lease transitions to `Stale`:

- `LeaseStale { lease_id, staleness_reason }` event emitted with the typed reason
- the lease remains in storage, in `Stale` state
- the next invocation that would have used the lease produces ask-user (or typed-confirmation if the original lease's tier required it) with the staleness reason surfaced as part of the `ApprovalRequest` reason payload
- the user's response options include re-grant at the same scope, re-grant at a narrower scope, revoke fully, or `AllowOnce` for this call only without re-granting

This is the canonical implementation of the revoke-and-narrow-lease recovery from `run.recovery` (File 04 §20.2). The lease is not silently revoked; the staleness is surfaced so the user can decide whether the original grant intent still holds.

### 10.5 Boundary

Re-evaluation is event-driven. The policy layer does not poll. The trigger set is closed; new triggers register through the same mechanism that registers revocation conditions (a typed declaration of which condition kinds the trigger affects). Lease state mutations are durable and emit standard policy events.

## 11. The `Lease` Primitive

Anchor: `policy.lease-primitive`

### 11.1 Definition

A `Lease` is a durable, scoped, typed approval record. It is the canonical primitive for persisted approval decisions across the shared scope hierarchy. Every persisted approval decision is a `Lease`; trivial single-call decisions that the user does not choose to persist are recorded as policy events without creating a `Lease`.

### 11.2 Required Fields

A `Lease` must carry at minimum:

- `lease_id` — stable identifier for revocation reference
- `capability_match` — the capability identity pattern the lease applies to: exact `(id, version)`, exact id with version-pinning policy (`latest`, `compatible`, `pinned`), capability family glob, or a registered match expression
- `scope` — one of `single_proposal`, `run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule` (per `run.approval-during-execution`, File 04 §11)
- `invoker_kind` — optional constraint over the invoker class (`user_direct`, `model_agent`, `automation`, `scheduled_trigger`, `plugin_runtime`, `mcp_external`, `subagent`, `system_internal`)
- `invoker_context` — optional matching data for source id, run id, parent run id, automation id, plugin id, external client id, and surface id when applicable
- `decision` — one of `AlwaysAllow`, `NarrowedAllow { constraints }`, `AlwaysDeny`
- `inherited_constraints` — typed constraints over touched resources (per §6) and other call shape (argument-shape match, idempotency requirement, max invocations within scope, expiry deadline if any)
- `grant_reason` — free-text rationale plus a typed `grant_origin` (one of `user_response_to_ask`, `source_approval_flow`, `automation_rule`, `built_in_template`, `policy_template_definition`)
- `grant_context` — snapshot of the active context at grant time: granting user identity, active conversation id, active intent thread id, active task id, active run id, active workspace id, active surface, world-model snapshot id, model-route at grant time, settings snapshot id, policy template version
- `granted_at` — timestamp
- `granted_by` — actor identity (user, automation, built-in template registration, source-approval flow)
- `expires_at` — optional explicit expiry deadline (omitted means no time-based expiry; revocation_conditions still apply)
- `revocation_conditions` — typed predicates per §10.2
- `status` — `Active`, `Stale`, or `Revoked`

A lease lacking any required field is invalid and is rejected at grant time.

### 11.3 Scope Semantics

Scope determines lease applicability and revocation defaults:

- `single_proposal` — applies to one proposed call; never persisted as a `Lease`; recorded as a single-proposal policy event with the same shape as a one-call decision
- `run` — applies for the duration of one `Run`; revoked when the run completes, fails, or is cancelled
- `intent_thread` — applies to one semantic line of work inside a conversation; revoked when that intent thread closes, is superseded, or is manually revoked
- `task` — applies for the duration of one `Task`; revoked when the task completes, fails, or is cancelled
- `conversation` — applies within one `Conversation`; revoked when the conversation is archived, deleted, or explicitly closed
- `workspace` — applies within the granting workspace; revoked when the workspace is removed or when the user manually revokes
- `global` — applies across all workspaces, conversations, runs, and tasks for the active user
- `reusable_policy_rule` — applies globally and is pattern-based; the canonical shape for built-in safety rules and user-authored policy templates expressed as leases (e.g., "always deny `git.push --force` to protected branches" is a reusable-policy-rule lease)

The `reusable_policy_rule` scope is distinguished from `global` by capability matching: `global` typically pins one or a small set of capability ids; `reusable_policy_rule` uses pattern-based `capability_match` and is the canonical representation of policy-templates-expressed-as-leases.

### 11.4 Composition

Multiple leases may apply to the same call. The lease selection rule (§6.4) chooses the active lease deterministically: narrower scope wins, deny-wins on tie, most-recently-granted on remaining ties. Leases never compose by averaging or by majority vote; one lease applies per call, or no lease applies.

A `single_proposal` lease never affects a future call; its scope is one decision.

### 11.5 Built-In Reusable Policy Rules

Anchor: `policy.built-in-reusable-policy-rules`

The system ships built-in reusable policy rules as system defaults with stable ids. They project to effective reusable-policy-rule leases at evaluation time, after durable user override records are applied. This avoids ambiguity on restart: defaults re-register, then user disables, narrows, widens, template edits, replacements, and restore-default actions are applied as separate audit-visible records.

Built-in default rules include:

- `git.push --force` to a branch in the configured protected-branch list → `AlwaysDeny` with typed-confirmation override per §7.4
- `system.shutdown` invoked by an agent → `AlwaysDeny` with typed-confirmation override
- `account.delete` invoked by an agent → `AlwaysDeny` with typed-confirmation override
- `credential.export` to any external destination → `AlwaysDeny` with typed-confirmation override
- shell commands matching the registered dangerous-pattern set (recursive deletes against absolute roots, formatting devices, raw block-device writes) → `AlwaysDeny` with typed-confirmation override
- `shell.exec` patterns where a registered dedicated capability exists (the CT.16 "prefer dedicated tools" pattern) → `RedirectSuggestion` to the dedicated capability when configured at the canonical `Strict` mode; `Warn` and `Off` modes per the dedicated-tool preference setting
- `shell.exec` network-fetch patterns after a recent `web.fetch` denial in the same run (the CT.16 "fetch fallback ban" pattern) → `AlwaysDeny` when configured at `Forbidden`; `UserConfirmed` (escalate to ask-user) when set to that mode; `Allowed` (no rule) when off

Built-in rules are user-customizable: the user may disable, narrow, widen, replace, or restore them through settings. Disabling or widening a rule that protects an irreversible operation is itself a typed-confirmation flow per §7. The ledger records both the system default and the user override that changed effective behavior.

### 11.6 Persistence

Anchor: `policy.persistence`

Leases are durable. They survive process restarts. The storage schema is File 20's concern; File 06 specifies the field set the storage schema must support, the lease event vocabulary the storage receives, and the resolution rules the runtime applies on read.

A lease's state changes (grant, narrow, revoke, transition to Stale) are recorded as policy events with full envelope. The lease itself is the projection over those events; the events are the source of truth.

Active and Stale leases are not pruned by storage without a policy-layer state transition. Revoked leases are retained for audit by default. Retention is user-controlled through explicit storage settings and destructive maintenance actions; pruning must warn that audit, replay, and conversation continuation may lose policy history. The canonical default is indefinite retention, not a fixed expiry.

### 11.7 Boundary

Leases are an evaluation primitive owned by File 06. Their persistence schema, storage-side projections, sync behavior across devices, and import/export semantics are owned by File 20 and File 21.

## 12. Approval-Policy Templates

Anchor: `policy.approval-policy-templates`

### 12.1 Definition

An `Approval-Policy Template` is a named, registered, composable validator chain consulted by the policy evaluator's `template-evaluation` inspector during effective tier resolution. A capability declaration's `approval_template_id` (`capability.permission-policy-fields`, File 05 §3.5) names the default template applied when policy evaluates that capability.

### 12.2 Required Properties

Every template carries:

- `template_id` — stable namespaced identifier
- `display_name`, `description`, `short_description` — localizable per the canonical pattern (literal defaults plus optional i18n keys)
- `family_applicability` — the capability families the template applies to (`*` for any)
- `scope_applicability` — the lease scopes at which the template may be applied
- `validators` — ordered list of typed validator declarations
- `typed_confirmation_required` — bool; true means any call routed through this template uses the typed-confirmation flow
- `denied_override_via_typed_confirmation` — bool; for templates attached to `Denied`-floor capabilities, whether the typed-confirmation override path is available
- `confirmation_string_pattern` — when typed-confirmation is required, the registered pattern the user's typed string must match; may interpolate validated `args.*` field paths from the proposed call
- `approval_text_template` — the localizable request text shown to the user during ask-user or typed-confirmation flows from this template
- `source` — `Builtin`, `Subsystem { id }`, `Plugin { id, version }`, `UserDefined { scope }` per the canonical sourcing taxonomy

### 12.3 Validator Verdicts

A template validator is a typed declaration that produces one of:

- `Allow` — proceed
- `Deny` — block
- `Ask` — escalate to ask-user
- `Escalate` — escalate to typed-confirmation
- `NoOpinion` — pass to the next validator

The validator chain runs in declared order and aggregates by severity: `Deny > Escalate > Ask > Allow > NoOpinion`. Every validator in the registered chain is mandatory by default: it runs unconditionally and its verdict participates in the severity maximum. `Allow` is final only when no mandatory validator produces a stricter verdict. If every validator returns `NoOpinion`, the template's terminal default applies (configurable per template; canonical default is `NoOpinion` itself, in which case the policy evaluator's other inspectors decide).

A validator may be declared `terminal` only when the template explicitly marks it terminal and all built-in and system-source validators in the chain have already produced their verdicts. No non-system-source validator may declare itself terminal. The final aggregate verdict and decisive validators are recorded in policy events.

Validators may be deterministic (typed predicate over arguments and context) or model-mediated (per the auto-decide pattern §8). Deterministic validators are the default; model-mediated validators are opt-in and inherit auto-decide's confidence-thresholded fallback rules.

### 12.4 Built-In Templates

The system ships with built-in templates seeded from the canonical patterns:

- per-tier defaults: `tier_default_readonly`, `tier_default_workspace_write`, `tier_default_user_approval`, `tier_default_unrestricted`, `tier_default_denied` — applied when a capability declares no explicit `approval_template_id`
- per-class defaults from CT.20: `class_internal_analysis_default` (defaults to ReadOnly tier-resolution behavior), `class_action_external_default` (defaults to UserApproval with batched-approval support), `class_user_artifact_default` (defaults to WorkspaceWrite with workspace-containment escalation)
- behavioral templates from CT.16: `clarify_first_for_multistep` (validators check whether a multi-step task has been initiated without prior clarification and emit `Ask` with clarify-first request text), `todos_for_multistep` (validators check that the agent has invoked the todo capability before non-trivial tool sequences), `prefer_dedicated_tools` (validator emits `RedirectSuggestion` when `shell.exec` is invoked with a pattern that has a registered dedicated-tool equivalent), `fetch_fallback_ban` (validator emits `Deny` when shell network-fetch capabilities are invoked after a recent same-run `web.fetch` denial)
- safety templates per the canonical reusable-policy-rule set (§11.5): `git_protected_branch_force_push_denied`, `irreversible_op_typed_confirmation`, `dangerous_command_typed_confirmation`, `secret_export_denied`
- subsystem- and surface-default templates: registered subsystems and work surfaces may ship default templates that can be overridden per capability

Built-in templates are settings-overridable per scope. The user may disable any built-in template, customize its request text, narrow its applicability, or replace it with a user-authored template.

### 12.5 User-Authored Templates

Users may register templates through the runtime-registration capability (`capability.runtime-mutation`, File 05 §16.2) under the source-approval flow (§9). User-authored templates carry the same field set as built-ins; they enter the registry as `UserDefined { scope }` and are subject to the same evaluation pipeline.

User-authored templates may not override the floor-enforcement step (§4.2 step 2). A user-authored template that attempts to grant `Allow` for a `Denied`-floor capability produces a `PolicyFloorViolated` event and the floor wins. The template is recorded as registered but is policy-inert for that capability.

### 12.6 Composition

A capability invocation may have multiple templates applicable: the capability's `approval_template_id` declared default plus any user-set per-capability or per-scope template overrides plus any active reusable-policy-rule leases that express templates. The policy evaluator runs each in order: capability default first, scope-level overrides second, reusable-policy-rule leases last. Verdicts aggregate by the severity lattice in §12.3; ordering affects deterministic explanation, not silent safety bypass.

### 12.7 Boundary

Templates are policy-evaluation declarations. Their storage schema, version evolution, and import/export behavior are owned by File 20 and File 21. Their UI presentation (the template editor, the validator-chain visualizer, the approval-text preview) is owned by the future UI specs. File 06 specifies the field set, the validator verdict semantics, and the composition order.

## 13. Approval UI Surface Contract

Anchor: `policy.approval-ui-surface-contract`

### 13.1 Definition

The `Approval UI Surface Contract` is the typed data contract the policy layer exposes for any user-facing approval surface. It is a data contract, not a UI specification. Multiple presentation surfaces consume the same typed payloads and respond through the same typed channel.

### 13.2 `ApprovalRequest`

Every ask-user, typed-confirmation, batched-approval, or contradiction-resolution flow produces an `ApprovalRequest` carrying:

- `request_id` — stable identifier for the approval round-trip
- `flow_kind` — one of `ask_user`, `typed_confirmation`, `lease_grant_proposal`, `lease_stale_re_grant`, `contradiction_resolution`, `source_registration` (the latter routes through §9)
- `invoker_kind`, `invoker_context` — who or what initiated the proposal, such as direct user action, model agent, automation, plugin runtime, external MCP client, subagent, or system-internal process
- `capability_id`, `capability_version`, `capability_display_name`, `capability_description`, `capability_short_description`, `capability_family`
- `resolved_args` — the resolved invocation arguments with `data_sensitivity` redactions applied (`Sensitive` fields shown with reduced detail; `Secret` fields shown only as kind labels)
- `reason` — the human-readable reason combining the model's stated intent (when available) and the policy-supplied justification (e.g., "tier UserApproval, no active matching lease")
- `resolved_tier` — the effective tier after resolution
- `permission_floor` — the declared floor (so the UI can communicate "this cannot be lowered")
- `resolved_touched_resources` — the concrete touched resources resolved from declared expressions per §6
- `data_sensitivity` — the capability's declared sensitivity classification
- `trust_state` — the registered entry's `effective_trust`
- `available_options` — typed `LeaseOption` set (§13.3)
- `classifier_result` — when auto-decide ran and produced a below-threshold or `Ask`/`Escalate` verdict, the typed result is included so the UI can surface "the classifier suggested X with confidence Y"
- resolved proposal facts projected from File 05 declaration/invocation records: `side_effect_class`, `reversibility_class`, `replay_class`, `postconditions`, `required_observations`, and `expected_artifacts_or_outputs`
- synthesized proposal facts: `preview_payload` from declared preview mode, `data_egress_summary` from resolved network/credential resources and sensitivity, `sandbox_or_isolation_summary` from the active execution context, and `rollback_or_compensation_note` when available
- `batch_id` — optional, present when this request is part of a batched approval per §5.5
- `contradictions_detected` — typed `Contradiction` records when the request is a contradiction-resolution flow per §14
- `lease_staleness` — typed reason when the request is a lease-stale-re-grant per §10.4
- `approval_text` — the localized request text from the active approval-policy template
- `confirmation_string_pattern` — present only for typed-confirmation flows; the pattern the user's typed string must match per §7.4. Template variables referencing validated `args.*` field paths resolve to concrete argument values (for example, `force-push to {args.branch}` resolves to `force-push to main`). Static patterns remain valid. Sensitive interpolations must preserve redaction; `Secret` values use safe labels or typed surrogates, not raw secret values.

The payload flows through the canonical event bus carrying the standard envelope (`conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`).

### 13.3 `LeaseOption`

The `available_options` carry typed `LeaseOption` entries. Each option declares:

- `kind` — one of `AllowOnce`, `AllowForRun`, `AllowForIntentThread`, `AllowForTask`, `AllowForConversation`, `AllowForWorkspace`, `AllowGlobal`, `AlwaysAllowReusableRule`, `DenyOnce`, `DenyForRun`, `DenyForIntentThread`, `DenyForTask`, `DenyForConversation`, `DenyForWorkspace`, `DenyGlobal`, `AlwaysDenyReusableRule`
- `scope_label` and `scope_description` — localized per the canonical descriptor pattern
- `default_constraints` — the constraints that would be created if the user selects this option without customization (typically derived from the proposed call's resolved touched resources)
- `user_customizable_constraints` — declarative description of which dimensions the user may narrow (e.g., the path subtree for filesystem touched resources, the host set for network resources); the UI presents these as editable fields
- `typed_confirmation_required` — bool; true for options that grant a lease against a typed-confirmation-required capability (such options are typically restricted to `AllowOnce` only, since persistent leases against typed-confirmation are forbidden per §7.3)

The set of available options is computed by the policy layer based on the capability's tier, floor, applicable templates, active leases, and the user's settings. Options that would violate floor or pierce a deny lease are excluded from the available set; the UI never offers an unavailable option.

### 13.4 `ApprovalResponse`

The user's response carries:

- `request_id` — matches the request
- `choice` — one of the available `LeaseOption` kinds, or `Cancel`
- `customized_constraints` — when the user narrowed the lease scope, the typed customized constraints
- `typed_confirmation_string` — for typed-confirmation flows, the user's typed string (validated against `confirmation_string_pattern`)
- `reason` — optional free-text rationale the user supplies for audit

Responses flow back through the same event bus. The policy layer awaits a response per `request_id`; on receipt, it validates the choice and customization against the available options and emits the corresponding `LeaseGranted` or `PolicyDecisionMade` events.

### 13.5 `BatchApprovalRequest`

A batched approval (§5.5) presents as a `BatchApprovalRequest` carrying:

- `batch_id`
- `items` — the constituent `ApprovalRequest` payloads
- `batch_options` — `ApproveAll`, `DenyAll`, `PerItem`
- `scope_summary` — describes the batched scope (the run, the task, the dispatch batch)

The user response is a `BatchApprovalResponse` carrying either a batch-level choice (`ApproveAll` or `DenyAll`) or per-item responses.

### 13.6 `ContradictionResolutionRequest`

A contradiction-resolution flow (§14) presents as a request carrying:

- `request_id`
- `contradictions` — typed `Contradiction` records describing the conflicting policy elements (the lease, scope-level override, template, and source whose verdicts conflict)
- `resolution_options` — typed options the user may pick: respect the narrower scope (default), respect the broader scope, revoke the conflicting lease, or modify a contradicting setting

### 13.7 Required Surface Properties

Any presentation surface implementing the contract must:

- present the `approval_text`, `resolved_args` (with sensitivity redactions intact), `reason`, `resolved_tier`, and `permission_floor`
- present invoker identity, resolved proposal facts, synthesized preview/egress/isolation facts, and absence of preview when preview is unavailable for a mutating or high-risk call
- present every `available_option` with its scope label, description, and default constraints
- allow the user to customize `user_customizable_constraints` for any option that declares them
- for typed-confirmation flows, present the `confirmation_string_pattern` requirement and validate the user's typed string before submission
- emit the `ApprovalResponse` through the canonical event bus
- support keyboard navigation, voice control, and screen-reader operation per the canonical accessibility requirements (the future UI Shell and Accessibility specs detail these, but the policy layer's contract here requires that the UI honor them)

The contract does not specify modal vs inline rendering, color, layout, animation, or any other presentation choice. Multiple surfaces (conversation-inline approval, modal dialog, voice confirmation, command-palette inline confirmation, batched approval review, automation pre-flight review) consume the contract and render appropriately for their context.

### 13.8 Boundary

The contract is the policy layer's exposed surface. The policy layer never invokes UI methods directly; it emits typed events. The UI layer subscribes to `ApprovalRequested` and equivalent events, renders requests, and emits `ApprovalResponse` events back. This decoupling means the same policy machinery works under any UI shell, headless CLI, voice-only, or programmatic-test harness.

## 14. Contradiction-Checking Across Scope Levels

Anchor: `policy.contradiction-checking-across-scope-levels`

### 14.1 Definition

`Contradiction-Checking` is the policy layer's resolver for cross-scope conflicts in the lease, settings, and template state. The canonical rule from `run.approval-during-execution` (File 04 §11) — contradictions across scope levels surface as policy errors, not silent wins — is enforced here.

### 14.2 Resolution Rules

The canonical resolution:

- **Tighter-narrower-deny wins**. A narrower-scope lease, setting, or template producing `Deny` overrides a broader-scope `Allow`. This is the natural deny-wins rule and is not flagged as a contradiction.
- **Tighter-narrower-allow under broader-deny is a contradiction**. A narrower-scope lease, setting, or template producing `Allow` against a broader-scope `Deny` (e.g., a conversation-level `AlwaysAllow` lease for a capability the user has globally denied) is a contradiction. The policy layer emits `PolicyContradictionDetected { capability_id, contradicting_elements }` and routes to a contradiction-resolution flow per §13.6. The runtime never silently weakens the broader deny.
- **Floor never participates**. A lease, setting, template, or trust override that attempts to lower a tier below `permission_floor` produces `PolicyFloorViolated`; the floor wins and the violating element is recorded as floor-violating but not as a cross-scope contradiction. The user may revoke the floor-violating element through the standard revocation paths.
- **Typed-confirmation never lifts**. A lease, setting, template, or trust override that attempts to skip a typed-confirmation requirement produces `TypedConfirmationCannotBeLifted`; typed-confirmation wins. Recorded similarly.
- **Reusable-policy-rule leases compose with same precedence**. A reusable-policy-rule lease producing `Deny` is checked against narrower-scope `Allow` leases the same way; the same contradiction-detection-and-surface rule applies.

### 14.3 Detection Timing

Contradiction detection runs:

- at lease grant time — a new lease is checked against existing leases, settings, and templates; any conflict is surfaced before the new lease is committed (the user must resolve the conflict in the lease grant flow)
- at policy evaluation time — a proposed call's effective tier resolution checks active leases and settings for conflicts; conflicts surface as contradiction-resolution requests
- at re-evaluation time — when a state change triggers lease re-evaluation per §10.3, contradiction detection re-runs over the affected leases

### 14.4 Resolution Outcomes

A contradiction is resolved by one of:

- the user picks a side (respect the narrower or broader element); the conflicting element is revoked or narrowed accordingly
- the user revokes both conflicting elements (the call falls through to the default tier-driven flow)
- the user creates a new lease that explicitly resolves the conflict (e.g., a workspace-scope `Allow` lease that explicitly notes "overrides the global `Deny` for this workspace")

The resolution is persisted as a `PolicyContradictionResolved` event linked to the originating contradiction. Subsequent calls do not re-trigger the same contradiction.

### 14.5 Boundary

Contradiction-checking is policy-layer logic. The UI's role is to render the contradiction-resolution request per §13.6 and emit the user's typed response. The policy layer applies the resolution and emits the resulting events. Contradictions detected in the source-approval flow during initial registration follow the same pattern, with resolution embedded in the source-approval flow's user options per §9.4.

## 15. Risk Classification and Trust Interaction

Anchor: `policy.risk-classification-trust-interaction`

### 15.1 Three-Class Capability Taxonomy

Capabilities classify into three canonical capability classes, drawn from the CT.20 taxonomy:

- `InternalAnalysis` — read-only operations supporting reasoning (file reads, searches, queries); default tier `ReadOnly`
- `ActionExternal` — operations that mutate external state (sending email, file writes, database writes, browser navigation, GUI clicks); default tier `UserApproval`
- `UserArtifact` — operations that produce user-visible deliverables (file create within workspace, document edit, image generation); default tier `WorkspaceWrite`

The class is declared per capability through File 05's required `capability_class` field. Tags may mirror the class for discovery, but are not policy truth. The class influences default `approval_template_id` selection but does not override an explicit declaration.

### 15.2 Trust Interaction

Trust-driven escalation (per §4.2 step 3) interacts with the class taxonomy:

- `InternalAnalysis` capabilities from `Community` or `Unverified` sources receive trust-driven escalation only when the call's resolved touched resources include `network`, `credential`, `sub-agent`, or registered extension classes carrying user-private data
- `ActionExternal` capabilities from `Community` or `Unverified` sources always receive trust-driven escalation (the canonical one-tier or two-tier escalation per §9.6)
- `UserArtifact` capabilities from `Community` or `Unverified` sources receive trust-driven escalation when the call's touched resources include filesystem paths outside the active workspace or external-credential references

These rules are settings-overridable per source. The user may set a user trust override that changes effective trust (for example, treating a `Community` source as verified for local policy purposes) or explicitly tighten an `InternalAnalysis` capability beyond its class default.

### 15.3 Risk Classification of Unknown Capabilities

A capability whose class is `Unknown` is treated as if it were `ActionExternal` for trust escalation purposes. The source-approval flow surfaces unknown classes as a customization opportunity; the user may set a class manually or accept the conservative default.

### 15.4 Per-Call Model-Mediated Risk Classification

When a capability declares `classification_mode: ModelMediated` for relevant fields (per `capability.classification-mode`, File 05 §7.2), the per-call classifier produces typed values for those fields. The policy layer consumes the classified values during effective tier resolution: a `shell.exec` whose call is classified as `reversibility_class: none` and `partial_output_meaningful: false` resolves at a higher tier than the same capability classified as `reversibility_class: compensable`. The classifier's confidence threshold and fallback rules apply per §8.

### 15.5 Boundary

Risk classification is one input to effective tier resolution. The classification itself comes from the capability declaration (`capability_class`, declared `replay_class`, declared `reversibility_class`) plus the registered trust state plus the per-call model-mediated classification when active. File 06 specifies how classification feeds into resolution; it does not invent a separate risk-scoring mechanism.

## 16. Settings Resolution for Policy

Anchor: `policy.settings-resolution-for-policy`

### 16.1 Configurable Dimensions and Layer Ownership

Every policy mechanism in this file is configurable through settings (per File 15). File 15 owns settings resolution; File 06 owns how already-resolved policy settings compose into policy decisions. The dimensions are:

- per-capability `permission_tier` overrides (capped above by `permission_floor`), per scope
- per-capability `approval_template_id` overrides, per scope
- per-source trust overrides (`registry_trust_override`), global only by default; settings may permit per-workspace overrides
- per-template enable/disable, per scope
- approval-posture preset — `Strict`, `Balanced`, `Permissive`, plus user-authored profiles
- per-flow timeouts (ask-user, typed-confirmation, batched approval) and timeout fall-through behavior; exact defaults belong to settings profiles
- auto-decide configuration (per capability or family) — enablement, classifier model, policy model-request template, confidence threshold, fallback rules per §8.2
- batched approval grouping keys and maximum batch size
- grant-evidence availability revalidation behavior
- per-source-class default `DeferSourcePolicy` fallback behavior (`ask_each_time`, `require_explicit_approval`, `ask_on_first_use`)
- source-approval flow risk thresholds per source class and resource class
- protected-branch seed list; customizable and consumed by git-related built-in safety rules per §11.5
- dedicated-tool preference mode (`Strict`, `Warn`, `Off`) per CT.16
- fetch-fallback policy (`Forbidden`, `UserConfirmed`, `Allowed`) per CT.16
- per-subsystem and per-surface approval-posture override
- approval-posture defaults contributed by active profile layers

### 16.2 Resolution Algorithm

Policy reads policy-relevant settings through File 15's source stack: invocation overlay, conversation, workspace, global, local explicit overlay, active profile layers, then definition default policy. Per-source overrides resolve through the same settings model, keyed by source identity.

The approval-posture preset is a settings-resolved meta-setting. Selecting a posture sets sensible defaults for all the dimensions above; advanced users can still override individual dimensions, and overrides persist across posture changes (changing posture does not reset prior per-capability customizations).

### 16.3 Approval-Posture Presets

The canonical presets:

- `Strict` — every `UserApproval` produces ask-user (no `AlwaysAllow` leases honored unless explicitly user-granted within that strict mode); `auto-decide` off; typed-confirmation triggers more aggressively (any `Denied`-floor capability or any capability with declared `reversibility_class: none`); `dedicated-tool preference: Strict`; `fetch-fallback: Forbidden`
- `Balanced` — per-capability defaults from declarations and built-in templates apply; `auto-decide` opt-in per capability or family; typed-confirmation only for declared cases; `dedicated-tool preference: Strict`; `fetch-fallback: Forbidden`; batched approval enabled
- `Permissive` — `auto-decide` on by default for `ReadOnly` and contained `WorkspaceWrite` capabilities; `UserApproval` defaults to ask-user but with one-click `AlwaysAllow` for the active workspace; typed-confirmation only for irreversible operations; `dedicated-tool preference: Warn`; `fetch-fallback: UserConfirmed`

Posture presets are starting points, not prescriptive. The user always retains explicit control through per-capability and per-source overrides.

### 16.4 Agent Exposure of Policy Settings

Anchor: `policy.agent-exposure-policy-settings`

Per the canonical settings exposure rules:

- approval-posture preset, current `effective_trust` per source, per-capability tier overrides — `OnRequest` exposure (the agent can read these on request through the read-only settings tool); the agent never sees per-call ask-user history beyond what the conversation context already carries
- typed-confirmation strings, lease grant contexts, and source-approval proposals — `Hidden`; the agent never sees the user's typed confirmation strings or the full grant-context snapshots
- the active approval-posture preset — `InModelRequest` (the model-request instructions include the active posture so the agent can adjust its behavior — for example, avoid proposing capabilities at higher tiers when the user is in `Strict` mode)

### 16.5 Boundary

Settings resolution is owned by File 15. File 06 specifies which dimensions are policy-relevant and how resolved values compose into a decision; it does not reinvent settings storage, validation, profile layers, agent exposure, or UI.

## 17. Explicit Rejections

Anchor: `policy.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel approval pipeline beside the canonical hook bus — every approval decision flows through the `ToolCallProposed` blocking hook subscriber and the typed event-bus contract; capabilities, plugins, MCP servers, and subsystem extensions never invent their own approval mechanism
- per-capability custom approval logic baked into capability handlers — capability authors implement the operation; the policy layer evaluates approval; mixing the two creates "capability leakage" and is rejected per `capability.contract-composition` (File 05 §17) / `capability.explicit-rejections` (File 05 §19) and re-rejected here
- silent approval: any direct-execution path must emit `PolicyDecisionMade` with the contributing reason; no capability call may execute without a recorded policy decision event
- silent denial: a denied call always produces a typed `PermissionDenied`-class result block in-band per `run.denial-is-in-band` (File 04 §8.3) plus a `PolicyDecisionMade` event; the agent or user must always have the chance to react
- silent contradiction resolution: cross-scope conflicts are surfaced as typed events and resolved through the user-facing flow; the runtime never picks a winner that weakens an outer deny or pierces a `permission_floor`
- floor-piercing: settings, leases, trust upgrades, scope-level overrides, `agent.unrestricted_mode`, and approval-policy templates can never lower an effective tier below `permission_floor`; `PolicyFloorViolated` events record any attempt and the floor wins
- bypassing typed-confirmation: leases, settings, trust upgrades, `auto-decide`, batched approval, and `agent.unrestricted_mode` can never lift a typed-confirmation requirement; the only path through `Denied` is the explicit typed-confirmation override per §7.4
- model-mediated approval as the silent default: `auto-decide` is opt-in per capability or family; the runtime never silently classifies away a user's approval requirement; classifier results below the configured confidence threshold fall through to ask-user
- recursive policy approval: policy-internal auto-decide classifier calls do not emit nested `ToolCallProposed` events or recursively invoke the approval router
- collapsing invoker classes: direct user actions, model-agent calls, automation, plugin runtimes, external MCP clients, subagents, and system-internal calls are evaluated by one policy layer but retain distinct invoker meaning
- untrusted inspectors silently allowing or rewriting policy outcomes: inspector authority classes constrain what third-party policy code can decide
- silent semantic substitution: `Substitute` may only perform declared narrowing or transparent redirects; changing the target/action semantics requires ask-user
- ad-hoc procedural revocation conditions: leases revoke through declared typed predicates only; runtime closures are not eligible because closure-backed conditions cannot be inspected, replayed across devices, or evaluated against persisted state
- registering a lease whose `capability_match` references a missing or unregistered capability — the lease is rejected at grant time; the user is informed; the lease never silently activates if the capability later registers with a matching id
- treating trust state as a declaration: source trust is registered-entry state per `capability.trust-source-approval-flow` (File 05 §9.2); any policy mechanism that mutates a declaration field based on trust is rejected; trust narrowing is policy-side
- a single global "approval policy" that overrides per-capability templates and per-scope overrides — policy is composed, not monolithic; built-in defaults plus templates plus leases plus settings compose deterministically; no single setting silently overrides the composition
- routing approval decisions through unrelated services or sidecars (logging service, telemetry service, automation service) — the approval router is the canonical decision point; logging and telemetry observe but never decide
- requiring the user to type a confirmation string the system computes from arguments without disclosing the string — the typed-confirmation request always shows the required string; the user types it as a deliberate-intent check, not as a guess
- silently auto-approving a typed-confirmation override when the user has previously typed-confirmed the same operation — typed-confirmation is per-call; it never persists as an `AlwaysAllow` lease; every typed-confirmation invocation requires fresh user input
- producing approval decisions that include other than `Continue`, `Substitute`, `Block`, or `RedirectSuggestion` — the canonical hook decision vocabulary is closed
- approval flows that depend on time-based polling rather than event-driven evaluation — re-evaluation triggers are event-driven per §10.3; the policy layer never polls
- hardcoded numeric policy defaults in this canonical layer — thresholds, counters, batch sizes, protected-branch seed lists, and timeout behavior belong to tested settings profiles
- registering policy-evaluation logic in capability handlers, in command-palette wrappers, in voice intent resolvers, or in any UI surface — every approval path ultimately passes through the canonical router; surfaces present and dispatch but never decide
- preserving any earlier name for the same primitive as a parallel system — `Lease` supersedes any earlier `AlwaysAllow record`, `approval policy entry`, `permission grant`, `auth lease`; `Approval Router` supersedes any earlier `permission inspector chain`, `approval pipeline`, `consent system`; `Approval Policy Template` supersedes any earlier `safety rule set`, `policy rule list`, `permission profile`; `Auto-Decide` supersedes any earlier `YOLO classifier`, `SmartApprove`, `auto-approve mode`; `Source-Approval Flow` supersedes any earlier `permission manifest negotiation`, `plugin install approval`, `MCP server connection approval`. None of those earlier names survive as a parallel primitive.

## 18. Consequences for Later Specs

Anchor: `policy.consequences-for-later-specs`

Every later spec that touches capability invocation, capability registration, automation, runtime behavior, UI presentation, storage, sync, telemetry, or evaluation consumes the Capability Policy layer as defined here.

The canonical principles later specs must follow:

- read approval decisions from the policy layer through the typed event-bus contract; never invent a parallel approval mechanism, never inline policy logic into a capability handler or UI component
- read effective tiers, lease state, and contradiction state through the policy layer's read interface; never compute these values independently from capability declarations
- record per-call resolved facts on the `CapabilityInvocation` record per `capability.invocation-record` (File 05 §11) and the policy events emitted by File 06; never on the declaration or on the registered entry
- treat `Lease` as the durable approval primitive; persisted approval state lives as `Lease` records and the events that produce them; never as a parallel "always-allow" or "permission grant" primitive
- treat `Approval-Policy Template` as the canonical reusable rule set; user-authored safety rules, subsystem/surface-specific approval policies, and built-in safety patterns all register as templates; never as a parallel rule registry
- treat `Source-Approval Flow` as the canonical capability-source onboarding mechanism; plugin install approval, MCP connection approval, external-API definition approval, and user-defined capability registration all flow through it; never as parallel install flows
- honor the four canonical approval flows (ask-user, typed-confirmation, auto-decide, batched approval) as the closed set; introduce new flows only by extension within these shapes (e.g., a "voice-confirmation" surface is a presentation of ask-user, not a fifth flow)
- honor the four direct-execution conditions (`ReadOnly` outcome, contained `WorkspaceWrite` with `direct_allow` mapping, active matching `AlwaysAllow` lease, `Unrestricted` with the relevant `agent.unrestricted_mode` setting on) as the closed set; never introduce another bypass
- honor the floor enforcement: settings, leases, trust upgrades, `agent.unrestricted_mode`, and approval-policy templates never lower below `permission_floor`
- honor typed-confirmation as the only path through `Denied`; never lift typed-confirmation through any combination of leases, settings, trust upgrades, or modes
- honor the contradiction-detection rule: tighter-narrower-allow under broader-deny surfaces as a typed contradiction; never silently weaken the broader deny
- honor the trust-driven narrowing rule: `Community` and `Unverified` sources cause policy-side tier escalation; declarations are not mutated; effective tier is computed at evaluation time
- emit policy events through the canonical event bus with the standard envelope; never emit policy decisions through telemetry side channels or out-of-band logs as the source of truth — the ledger is the source of truth, telemetry is a projection
- consume the source-trust state from the registered entry per `capability.trust-source-approval-flow` (File 05 §9.2); never rebuild trust state from declarations or from out-of-band heuristics
- consume the canonical `capability_class` taxonomy (`InternalAnalysis`, `ActionExternal`, `UserArtifact`, `Unknown`) for capability classification; extension classes register through the same capability-class extension mechanism when such a mechanism exists
- consume the canonical revocation conditions and re-evaluation triggers; new conditions register through the typed-declaration mechanism with explicit trigger affinity
- consume the canonical `ApprovalRequest` / `LeaseOption` / `ApprovalResponse` / `BatchApprovalRequest` / `ContradictionResolutionRequest` data contract for any user-facing approval surface; never invent a parallel approval data shape

Specific integration contracts will be stated in those files when they are written.
