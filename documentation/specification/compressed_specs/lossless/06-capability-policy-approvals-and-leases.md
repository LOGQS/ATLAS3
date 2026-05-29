> Lossless render of canonical/06-capability-policy-approvals-and-leases.md — original 101462 chars

# Capability Policy, Approvals, and Leases

## Status
Canonical.

## Scope
Defines: the `Capability Policy` layer (runtime evaluation system consuming File 05's declared metadata, producing approval decisions); effective tier resolution from declared `permission_tier`, `permission_floor`, source trust, settings, scope-level overrides, active leases; the `Approval Router` (dispatch component gating capability invocation); approval flows (immediate allow, immediate deny, ask-user, typed-confirmation, batched approval, denial in-band as tool result, model-mediated `auto-decide`); the `Lease` primitive (durable approval grants with scope hierarchy from [`run.approval-during-execution`, File 04 §11]); approval-policy templates (composable validator chains); contradiction-checking across scope levels + cross-scope conflict resolution; touched-resource matching against lease constraints incl. extension-class containment; permission-floor enforcement + carve-out for `Denied` via typed-confirmation; mid-execution policy re-evaluation, lease staleness, revoke-and-narrow recovery from [`run.recovery`, File 04 §20.2]; source-approval flow when plugins/MCP servers/external APIs/user-defined capabilities register; approval UI surface contract; policy event vocabulary into ledger+event stream; settings resolution for every policy-relevant dimension.
Does not define: the Capability Contract field set [File 05]; registry resolution/lookup/backend-binding lifecycle [`capability.registered-capability`, File 05 §10]–§16; tool-surface zones/model-request visibility/deferred loading/borrowing UX [File 07]; run lifecycle/execution graph/hook execution mechanics/typed hook-decision vocabulary [File 04] (File 06 reuses [`run.hook-integration`, File 04 §23.3]'s hook architecture); routing or `RunIntent` selection [File 03]; block schema/artifact lifecycle/evidence model [Files 08, 09]; ledger row format/event-stream wire format/storage projections [`run.ledger-events-commits`, File 04 §23] owns contract, later specs own schema; credential vault internals or trust-state cryptographic verification (future Security spec); sandbox/process isolation primitives (future Sandbox spec); provider rate-limit tracking/circuit breakers/polling intervals [File 17 / future MCP spec]; approval modal layout/colors/stacking/UI rendering (File 06 specifies data contract; UI specs own presentation).

## Source Resolution
Resolves permissions, approvals, leases, trust gates, confirmation, policy hooks, user override into one boundary: the shared capability policy system. Resolved design: every capability invocation passes through one policy layer (no agent/subsystem/surface/UI-specific approval system); policy evaluates declarations, invocation args, touched resources, caller/source trust, active leases, settings, previews, validators, user decisions; leases are the durable primitive for persisted allow/deny decisions, scoped authorization, revocation history; user approval/typed confirmation/policy-driven escalation/LLM-mediated approval judgment are policy behaviors, not execution-loop special cases; denials+approvals recorded as policy decisions, surfaced back in-band so execution can continue safely when possible.

## 1. Chosen Model `policy.chosen-model`
One Capability Policy layer. Every consequential invocation passes through it: `Run`-internal model-emitted tool calls, user-invoked actions (palette/shortcuts), automation triggers, scheduled tasks, MCP-exposed external invocations, capability registrations.
Policy layer reads: the `CapabilityDeclaration` [`capability.declaration`, File 05 §3] for `permission_tier`, `permission_floor`, `capability_class`, `approval_template_id`, `data_sensitivity`, `touched_resources` expressions, `replay_class`, execution-semantic metadata; the `RegisteredCapability` [`capability.registered-capability`, File 05 §10] for `effective_trust`, `enabled`, `availability_status`, `collision_state`, active aliases; the active execution context (active conversation/intent thread/task/run/workspace/surface/world-model snapshot/model route/provider rate-limit state, invoker kind+context); the active settings cascade (per-capability/per-source/scope-level overrides, approval-posture preset); the active lease set (matching by capability identity pattern, scope inclusion, inherited-constraint containment).
Policy layer produces: a typed `ApprovalDecision` consumed by the executor as `Continue`/`Substitute`/`Block`/`RedirectSuggestion` hook decision [`run.hook-integration`, File 04 §23.3]; per-call resolved facts on the `CapabilityInvocation` record [`capability.invocation-record`, File 05 §11] (resolved tier, resolved touched resources, lease used, contradictions detected, classifier result if model-mediated); typed policy events into ledger+event stream [`run.execution-ledger`, File 04 §23.1; `run.event-stream`, File 04 §23.2] (policy decision, lease grant, lease revoke, contradiction detected, floor violated, source registration approved).
The `Approval Router` is the policy layer's dispatch shape: a single blocking hook subscriber on `ToolCallProposed` at priority `+100` (post-validation, pre-execution); not a parallel pipeline; internally composes named policy inspectors emitting intermediate verdicts, merged into one hook decision.
`Lease` is the canonical durable approval primitive: a single record shape across the [`run.approval-during-execution`, File 04 §11] scope hierarchy; the scope field discriminates. No separate "always-allow record"/"approval policy entry"/"permission grant" type.
`Approval Policy Template` is the canonical reusable rule set: named, composable, registered, consulted by the evaluator. Built-in templates seed defaults; user-authored templates extend via the same registration.
`Source Approval Flow` is the canonical capability-source onboarding mechanism: when a plugin/MCP server/external-API definition/user-defined capability registers, the flow surfaces declared metadata, lets user accept defaults / customize per-capability / deny outright / defer source-level policy / cancel registration.
No per-subsystem/per-surface bespoke approval logic, no per-capability custom flow, no separate "MCP approval system", no parallel "plugin permission system". Every path goes through the same router consulting the same templates against the same lease set under the same settings cascade.
The layer supersedes per-tool ad-hoc gating shapes earlier called `goose mode`, `AskForApproval`, `auto-approve toggle`, `permission mode`, `YOLO classifier`, interaction-level controls, equivalents. Canonical names here: `approval-posture preset`, `approval mode`, `auto-decide`, `Lease`.

## 2. Boundaries with Adjacent Layers `policy.boundaries-with-adjacent-layers`
### 2.1 With File 05
File 05 owns: `CapabilityDeclaration` field set (incl. `permission_tier`, `permission_floor`, `capability_class`, `approval_template_id`, `data_sensitivity`, `touched_resources`, `classification_mode`, `replay_class`); `RegisteredCapability` runtime state (`effective_trust`, `enabled`, `availability_status`, `collision_state`); `CapabilityInvocation` record schema; registry operations (register, unregister, update, enable, disable, lookup, alias resolution, source-collision shadowing).
File 06 owns: the resolution algorithm (declared metadata + context + active leases + settings → effective decision); lease primitive/lifecycle/persistence; approval-policy template registration/composition/evaluation; approval router as blocking hook; source-approval flow at registration time; contradiction detection+resolution.
File 06 reads from declarations+registered state, never mutates either. Per-call resolved tier, touched resources, model-mediated classification result, lease used, policy decision written onto the invocation record [`capability.invocation-record`, File 05 §11], not back onto declaration/registered entry.
### 2.2 With File 04
[`run.call-pipeline`, File 04 §8.2] defines the call pipeline; approval router runs at step 5. [`run.approval-during-execution`, File 04 §11] establishes the permission-tier hierarchy, `Lease` with full scope hierarchy, named `auto-decide` mode, scope-based batching, contradiction-checking across scope levels. [`run.hook-integration`, File 04 §23.3] establishes typed hook decision vocabulary (`Continue`, `Substitute`, `Block`, `RedirectSuggestion`), priority convention, timeout-with-authority-based-fail-direction, per-error-class retry. File 06 inherits all; does not redefine tier set/lease scope hierarchy/hook decision shape/hook timeout semantics; specifies how each is applied in policy evaluation. The denial-in-band rule [`run.denial-is-in-band`, File 04 §8.3] is load-bearing: a denied call produces a typed result block linked to the proposal; the agent loop receives it as ordinary input and decides (ask user, narrow scope, try alternative, stop).
### 2.3 With Cross-Cutting Substrate
Approval router is a blocking subscriber on `ToolCallProposed` [`run.hook-integration`, File 04 §23.3 + canonical event-bus pattern]. Other policy events emit through the same bus. Envelope (`conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`) carries enough context to attribute across parallel runs+concurrent worktrees. Settings read through the settings system [`core.settings-system`, File 01 §6.8]; cascade is conversation → workspace → global → overlay → declared default; no parallel settings store. Typed errors flow through the typed-error envelope [`core.typed-errors`, File 01 §6.9]; policy denials, floor violations, contradiction errors, lease-stale signals are typed variants. State awareness consulted: active surface, focused element, primary panel, ui-mode, available-capability set from `availability_predicate` [`capability.availability-predicate`, File 05 §15.2]; state changes affecting lease validity (workspace switch, panel change, ui-mode transition) trigger lease revalidation per §10.
### 2.4 Boundary
File 06 is the runtime evaluation layer; owns no storage schema, no UI rendering, no execution mechanics, no capability declarations. Lease+policy-event storage = future Storage spec; approval-prompt/lease-management UI presentation = future UI specs; actual execution of approved calls = File 04.

## 3. The Approval Router `policy.approval-router`
### 3.1 Definition
The canonical dispatch component; a single blocking hook subscriber on `ToolCallProposed` at priority `+100`. Receives the proposed invocation; consults declaration metadata, registered state, active leases, settings, world-model snapshot, policy templates; emits one typed `ApprovalDecision`.
### 3.2 Position in Capability-Call Pipeline
[`run.call-pipeline`, File 04 §8.2] step 5:
1. Resolve capability (File 05 registry)
2. Validate input ([`capability.input-validators`, File 05 §8.1] validators)
3. Produce proposal
4. Run validators and policy checks
5. **Determine denial, approval need, persisted decision, or active lease — the Approval Router** (this section)
6. Execute with declared isolation+concurrency semantics
7. Stream partials when supported
8. Record observations+result
9. Validate postconditions
10. Commit or expose output
Router runs after structural validators (priority `0`) so it sees post-validation payload. Audit+logging hooks at priority `-100` capture pre-router state for forensic reconstruction.
### 3.3 Internal Composition — Policy Inspectors `policy.internal-composition-policy-inspectors`
Router composes named `policy inspectors`, each emitting an intermediate verdict; router merges+produces final decision. Inspector composition is a registry-managed list; built-ins register at startup, plugins/extensions register additional inspectors at load time (subject to source-approval per §9).
Required built-in inspectors:
- `tier-resolution`: computes effective tier from declared `permission_tier` (via `TierResolver` per [`capability.tier-resolver`, File 05 §5.2]), `permission_floor`, source trust, scope-level overrides, active leases — produces `EffectiveTierDecision`
- `template-evaluation`: consults `approval_template_id` + active reusable-policy-rule leases; runs the template's validator chain — produces template verdicts (`Allow`, `Deny`, `Ask`, `Escalate`, `NoOpinion`)
- `touched-resource-matching`: resolves declared `touched_resources` expressions against args, matches each against active lease constraints — produces matched-lease set or no-match
- `contradiction-detection`: compares verdicts across scope levels, flags conflicts — produces `Vec<Contradiction>`
- `classifier-mediation`: when `auto-decide` active or capability declares `ModelMediated` classification mode for relevant fields, invokes the configured classifier model — produces `ClassifierResult { decision, confidence, reasoning }` or skips
- `risk-classification`: applies CT.20-derived class defaults (`InternalAnalysis`/`ActionExternal`/`UserArtifact`) + trust-driven escalations — produces tier adjustments
Inspectors declare an authority class:
- `observe_only` — may emit notes, risk facts, explanations, but no verdict
- `narrowing_only` — may emit `Ask`/`Deny`/`Escalate`/stricter constraints, cannot produce an effective `Allow`
- `allow_capable` — may contribute `Allow` verdicts only when registered by built-in/subsystem/verified/explicitly user-approved policy sources
- `substitute_capable` — may propose `Substitute`, only for declared narrowing or transparent redirects
Community/unverified/plugin/MCP/API/user-defined inspectors default to `narrowing_only` until user explicitly upgrades authority via source approval/settings. No inspector can bypass `permission_floor`, typed-confirmation, contradiction detection, touched-resource constraints.
Inspector ordering convention: `tier-resolution` first, `template-evaluation` second, `touched-resource-matching` third, `risk-classification` fourth, `classifier-mediation` fifth (only when active), `contradiction-detection` last. Router accumulates verdicts; a `Deny` from any required inspector wins immediately; an `Ask` promotes to ask-user unless a later inspector escalates further. User/plugin-defined inspectors register with explicit priority; cannot be placed before `tier-resolution` or after `contradiction-detection`. Their verdicts compose the same way: `Deny` wins, `Ask` promotes, `Allow` permissive only when no other inspector dissents.
### 3.4 Output
Four typed `ApprovalDecision` outcomes mapped to [`run.hook-integration`, File 04 §23.3]:
- `Continue { reason, lease_used? }` — proceed with proposed payload; emit `PolicyDecisionMade { decision: Continue, ... }`
- `Substitute { new_payload, reason, substitution_kind }` — proceed with router-modified payload; valid only for declared constraint narrowing, sensitivity-preserving redaction, sandbox narrowing, or transparent redirect to a safer equivalent capability; policy event records original+substituted payloads with sensitivity redaction; semantic target/action changes require ask-user, not silent substitution
- `Block { reason, error_kind }` — abort; executor records denial; typed reason flows in-band per [`run.denial-is-in-band`, File 04 §8.3]; emit `PolicyDecisionMade { decision: Block, ... }`
- `RedirectSuggestion { capability_id, args, reason }` — abort and signal the agent should retry using a suggested capability (e.g. `shell.exec` with `find` redirected to `file.search` per CT.16); agent loop consumes as a typed retry signal
Router never invents new contract semantics; any other outcome is an Explicit Rejection (§17).
### 3.5 Failure Mode
Router is an authoritative blocking hook; timeout/error fails closed → synthesized `Block { reason: "approval router timeout" | "approval router error" }`; executor records timeout, emits standard `Block`, agent receives typed denial in-band. Per-error-class retry per [`run.hook-integration`, File 04 §23.3]: transient infrastructure errors may retry once within the timeout window before failing closed; configuration errors (missing template, unresolved classifier model, missing inspector) do not retry, fail closed immediately, produce a typed `PolicyConfigurationError` event. Router's blocking timeout default is configurable per-error-class through settings, not hardcoded.
### 3.6 Boundary
Router consumes typed proposals from `ToolCallProposed`, produces typed decisions back onto the hook bus. Owns no execution/sandbox selection/registration/ledger storage/UI rendering. Decisions requiring user interaction (ask-user, typed-confirmation) flow through the approval UI surface contract (§13); router awaits the user's typed response over the same bus, then emits its decision.

## 4. Effective Tier Resolution `policy.effective-tier-resolution`
### 4.1 Definition
`Effective Tier Resolution` is the deterministic algorithm producing the runtime tier for a given proposed call; canonical input to approval-flow selection and lease evaluation.
### 4.2 Algorithm (fixed order)
1. **Declared tier**. Resolve `permission_tier` [`capability.tier-resolver`, File 05 §5.2]. `TierResolver::Static(tier)` → static value. `TierResolver::Dynamic(resolver_id)` → registered argument-aware resolver evaluates proposal args + active world-model snapshot deterministically, returns a tier (stable given same inputs).
2. **Floor enforcement**. Result clamped from below by `permission_floor` [`capability.permission-floor`, File 05 §5.4]. If resolver returned weaker than floor, floor wins; floor never lowered by any subsequent step; any later step producing a tier below floor produces a `PolicyFloorViolated` event and the floor's tier is used.
3. **Trust narrowing**. Registered `effective_trust` [`capability.trust-source-approval-flow`, File 05 §9.2] applies a trust-driven minimum tier: `System`/`Verified`/`User` — no narrowing; `Community` — minimum effective tier `UserApproval` (one-tier escalation from `WorkspaceWrite` or below); `Unverified` — minimum effective tier `UserApproval` AND first invocation of each such capability per conversation additionally requires per-call ask-user (no `AlwaysAllow` lease honored without explicit user upgrade of the source's trust). Trust narrowing never crosses the floor in either direction (a `Community` cap whose floor is `Denied` stays `Denied`; a `Community` cap already at `UserApproval` unchanged).
4. **Scope-level setting overrides**. Per-capability+per-source tier ceilings from the cascade (conversation → workspace → global → overlay → default) apply. A user-set ceiling can never lower below the floor (floor wins) but can raise above declared tier.
5. **Lease lookup**. Active lease set consulted. A lease applies when: its `capability_match` covers the proposed id (exact, family glob, pattern); its `scope` includes the active execution context (`single_proposal`-scope never persist past one call; `reusable-policy-rule`-scope apply globally); its `invoker_kind` constraint (if present) matches; its `inherited_constraints` contain the resolved touched resources (§6); its `status` is `Active` (not `Stale`/`Revoked`); the call satisfies per-lease conditions (argument-shape match, idempotency, max-invocations). When multiple apply, narrower scope wins; among same-scope, deny-wins. A matching `AlwaysAllow` lease → direct execution at the lease's tier (still bounded by floor); a matching `AlwaysDeny` → immediate `Block`.
6. **Decision selection**. Resulting tier + lease/template verdicts → terminal decision: direct execution, ask-user, typed-confirmation, deny, or model-mediated escalation per §5.
Output: a typed `EffectiveTierDecision` carrying resolved tier, contributing scope level (conversation/workspace/global/lease/floor), lease used (if any), contradictions detected (if any), human-readable reason → flows onto the invocation record [`capability.invocation-record`, File 05 §11].
### 4.3 Required Outcomes
Exactly one terminal outcome per call:
- `direct_allow` — proceeds without user interaction; `PolicyDecisionMade` emitted with reason
- `direct_deny` — typed denial; agent receives in-band [`run.denial-is-in-band`, File 04 §8.3]
- `ask_user` — approval UI surface contract invoked (§13); awaits response
- `typed_confirmation` — typed-confirmation flow (§7); cannot be skipped/auto-resolved
- `model_mediated` — auto-decide classifier (§8); resolves to `direct_allow`/`direct_deny` or escalates to `ask_user` per classifier output+confidence
Canonical tier-to-outcome mapping:
- `Denied` → `direct_deny` always; only path to execution is the typed-confirmation override of `Denied` per §7.4 (routed through `typed_confirmation`)
- `ReadOnly` → `direct_allow`
- `WorkspaceWrite` with proposal contained within active workspace → `direct_allow`
- `WorkspaceWrite` escaping the workspace → effective tier escalates to `UserApproval`, rule re-applies
- `UserApproval` → `direct_allow` if matching `AlwaysAllow` lease active; `direct_deny` if matching `AlwaysDeny` active; `model_mediated` if `auto-decide` configured+active for this capability; otherwise `ask_user`
- `Unrestricted` → `direct_allow` only when invoker/settings enables `agent.unrestricted_mode`; otherwise the `UserApproval` rule applies [`run.approval-during-execution`, File 04 §11]; still policy-governed (emits events, honors source trust, floors, typed-confirmation, touched-resource constraints, user narrowing)
- typed-confirmation variant of `UserApproval` → `typed_confirmation` always; `auto-decide` and `AlwaysAllow` leases never lift it
Mapping deterministic; any outcome outside this set is an Explicit Rejection (§17).
### 4.4 Boundary
Tier resolution is purely a function of declared metadata, registered state, settings, leases, world-model snapshot; does not call external services beyond `TierResolver::Dynamic` resolvers + the model-mediated classifier; must remain fast enough for every call; expensive/speculative decisions live in classifier mediation (§8), off by default.

## 5. Approval Flows `policy.approval-flows`
### 5.1 Definition
An `Approval Flow` is the canonical sequence to reach a terminal decision when tier resolution produces an outcome other than `direct_allow`/`direct_deny`. Four flows: `ask-user`, `typed-confirmation`, `auto-decide`, `batched approval`.
### 5.2 Ask-User Flow
Executes when: effective tier `UserApproval` (incl. `Unrestricted` with `agent.unrestricted_mode` off) and no matching `AlwaysAllow` lease; a template emits `Ask`; a contradiction detected (user must resolve); a stale lease encountered (§10) and user must re-grant/revoke.
Required steps:
1. Construct an `ApprovalRequest` payload (§13.2) carrying capability identity, resolved args (with `data_sensitivity` redactions), reason, resolved tier, floor, resolved touched resources, available lease options, contradictions, invoker identity, resolved proposal facts, classifier result if model-mediated produced low-confidence verdict
2. Emit `ApprovalRequested { request_id, capability_id, ... }` with canonical envelope
3. Await the typed `ApprovalResponse`; no timeout required unless a settings profile configures one; if a configured timeout expires, configured fail direction applies (fail-closed as the safe profile)
4. If the choice creates a lease (any of `AlwaysAllow`, `AllowForRun`, `AllowForIntentThread`, `AllowForTask`, `AllowForConversation`, `AllowForWorkspace`, `AllowGlobal`, or any `Deny*` beyond `DenyOnce`), persist the lease per §11; emit `LeaseGranted`
5. If choice is `AllowOnce`/`DenyOnce`, no lease created; recorded as a single-proposal policy event
6. Emit `ApprovalGranted`/`ApprovalDenied` + corresponding `PolicyDecisionMade`
7. Return the typed `ApprovalDecision` (`Continue`/`Block`) to executor through hook bus
The `ApprovalResponse` allows narrowing the lease's `inherited_constraints` from defaults derived from declared touched resources (e.g., `AlwaysAllow` for `file.edit` defaults to "files within active workspace"; user may narrow to "files under `src/`"). Narrowed constraints typed+machine-checkable per [`capability.touched-resources`, File 05 §6].
### 5.3 Typed-Confirmation Flow
Executes when the template requires it, when a `Denied`-tier capability is invoked through the override carve-out, or when a registered template marks the call typed-confirmation regardless of tier. Per §7.
### 5.4 Auto-Decide Flow
Executes when capability or family is configured for model-mediated approval and config is active in current scope. Per §8.
### 5.5 Batched Approval Flow `policy.batched-approval-flow`
When a natural execution boundary already has multiple ask-user decisions pending, present them as one batched `BatchApprovalRequest` (§13.3) where possible. Natural boundaries: one model response, one programmatic step, one script/workflow step, one child-run spawn group, one executor dispatch batch. User resolves each item independently or accepts/denies the batch. A typed-confirmation item never participates in a batch — always presents alone; a batch including a `Denied`-tier item shows it as already-denied (the typed-confirmation override is a separate single-item flow). Batching granularity configurable by surface+policy profile: single turn, run, child run, agent group, conversation, workspace, or other registered grouping keys. New groupers must be structural selectors over already-pending approvals, not timers; the runtime never delays approval emission solely to collect future items. Maximum batch size is a settings dimension; overflow splits structurally.
### 5.6 Boundary
Approval flows produce typed decisions through the same hook bus. User-facing presentation (conversation-inline card, modal, voice confirmation request, command-palette inline confirmation) owned by future UI specs; policy specifies the data contract (§13), not rendering.

## 6. Touched-Resource Matching Against Lease Scope `policy.touched-resource-matching-against-lease-scope`
### 6.1 Definition
`Touched-Resource Matching` is the algorithm determining whether a proposed call's resolved touched resources fall within an active lease's `inherited_constraints`; a lease applies only when match succeeds.
### 6.2 Resolution
Declared `touched_resources` [`capability.touched-resources`, File 05 §6] are typed expressions referencing input-schema field paths (`args.path`, `args.command`, `args.url`, etc.). Policy resolves each expression against the call's args → concrete set of touched resources, each carrying `class`, `access`, resolved scope (concrete path, host, port, env-var name, settings key/scope, process group, credential vault key, sub-agent type id, etc.). For extension classes registered per [`capability.extension-resource-classes`, File 05 §6.3], the registered containment predicate produces the resolved scope.
### 6.3 Containment
Lease's `inherited_constraints` are typed predicates over the same resource classes. Containment checked per resource:
- `filesystem` — path subtree containment (call's resolved path canonicalized, must lie within the lease's subtree)
- `network` — host-set containment (call's resolved host must match the lease's set, e.g. `{api.example.com, *.example.org}`)
- `process` — process-group containment
- `env` — env-var-name allowlist containment
- `setting` — key, key-prefix, owner, category, scope, or profile-context containment
- `credential` — vault-key allowlist containment
- `model-call` — provider/model identity containment
- `browser-session` — session-id containment
- `ui-element` — element-id containment (typically run-scoped)
- `sub-agent` — sub-agent-type-id containment
- `scheduler` — schedule-id containment
- registered extension classes — registered containment predicate per the extension's declaration
A lease applies only when every resolved touched resource is contained within the lease's constraints for its class; if any escapes, the lease does not apply, the next matching lease is checked, falling through to ask-user if none.
### 6.4 Lease Selection on Multiple Matches
1. Narrower scope wins. Ordering: `single_proposal < run < intent_thread < task < conversation < workspace < global < reusable_policy_rule`.
2. Among same-scope, `AlwaysDeny` wins over `AlwaysAllow` (deny-wins).
3. Among same-scope same-decision, most-recently-granted wins.
Selected lease's identity recorded as `lease_used` [`capability.invocation-record`, File 05 §11].
### 6.5 No-Match Fallthrough
When no lease matches, tier resolution falls through to the default tier-driven outcome (§4.3). `UserApproval` with no matching lease → ask-user (or auto-decide if configured); `WorkspaceWrite` with no matching lease → direct allow (subject to workspace containment per §4.3).
### 6.6 Boundary
Touched-resource matching deterministic given resolved args + active lease set. Expression grammar lives in [`capability.resource-expressions`, File 05 §6.4] or future capability-schema appendix; File 06 specifies the matching algorithm+containment semantics. Extension-class registration includes a containment predicate; missing/unparseable predicates make leases referencing the extension class invalid (registration fails per [`capability.extension-resource-classes`, File 05 §6.3]'s proposal-first rule).

## 7. Permission Floor and Typed-Confirmation `policy.permission-floor-typed-confirmation`
### 7.1 Permission Floor `policy.permission-floor`
`permission_floor` [`capability.permission-floor`, File 05 §5.4] is the absolute minimum tier; canonical floor for irreversible high-blast-radius ops: account deletion, destructive publish, force-push to a protected branch, system shutdown, credential export, irreversible publishing, system file edits, machine-scope registry mutation, plus any user-marked operation per settings. Floor never lowers — settings, leases, trust upgrades, `agent.unrestricted_mode`, cross-scope overrides cannot lower it; any attempt produces `PolicyFloorViolated` and the floor wins.
### 7.2 Definition of Typed-Confirmation
`Typed-Confirmation` is a variant of the `UserApproval` tier requiring the user to type an exact confirmation string before proceeding. The string is a value the user recognizes as deliberate intent — action's target identifier, exact path, branch name, account name, explicit phrase. A capability declares typed-confirmation through its `approval_template_id` referencing a template carrying the requirement.
### 7.3 Properties
Typed-confirmation: always asks (no `AlwaysAllow` lease/scope override/settings preset/trust upgrade/`agent.unrestricted_mode` lifts it); never participates in batched approval (§5.5); never fast-paths through `auto-decide` (even high-confidence allow still shows the request); emits a single-proposal policy event regardless of choice (no `AlwaysAllow` lease grantable from it); the approval-text template carries confirmation-string pattern, human-readable warning, rendered preview of what the call will do.
### 7.4 The `Denied` Carve-Out `policy.denied-carve-out`
A capability with effective tier `Denied` is not invocable by default. Only path through `Denied` is the typed-confirmation override: the template may declare `denied_override_via_typed_confirmation: Required`, enabling a one-time override per invocation; user types exact string, call proceeds; recorded as a `Denied`-override event; single-proposal scope (no `AlwaysAllow` lease creatable). A capability whose `permission_floor` is `Denied` and whose template does not declare the override has no path to execution — agent or user (canonical shape for never-auto-approvable ops: force-push to a protected branch, account deletion, similar).
### 7.5 Examples
- `git.push --force` to a protected-branch-list branch: `permission_tier: WorkspaceWrite`; `permission_floor: Denied`; template requires typed-confirmation override; effective tier `Denied`; only path is type the branch name
- `system.shutdown`: `permission_tier: UserApproval`; `permission_floor: Denied`; typed-confirmation override
- `account.delete`: `permission_tier: UserApproval`; `permission_floor: Denied`; typed-confirmation override with account identifier as confirmation string
- `credential.export`: `permission_tier: UserApproval`; `permission_floor: Denied`; typed-confirmation override; exported credential sanitized in result per `data_sensitivity: Secret`
List illustrative. Canonical rule: any capability that is irreversible and whose impact extends beyond rapid in-workspace undo is a candidate for `Denied` floor with typed-confirmation override.
### 7.6 Boundary
Typed-confirmation is a policy-flow shape; UI rendering owned by future UI specs. File 06 specifies the data contract: approval-text template, confirmation-string pattern, preview payload, typed `TypedConfirmationResponse` carrying the user's typed string. Policy validates the string against the pattern; mismatch → typed `TypedConfirmationMismatch` decision; flow returns to ask again or cancel.

## 8. Auto-Decide Mode `policy.auto-decide-mode`
### 8.1 Definition
`Auto-Decide` is the model-mediated approval mode named in [`run.approval-during-execution`, File 04 §11]. A designated classifier model evaluates a proposed call against a configured policy model-request template, returns a typed `ClassifierResult` (decision, confidence, reasoning). Opt-in per capability or family; never the default.
### 8.2 Configuration
Settings-resolved (cascade conversation → workspace → global → overlay → default). Carries:
- `enabled` per capability or family — opt-in flag
- `classifier_model_id` — model used, resolved through model-strategy layer per File 04
- `policy_model_request_template_id` — configured model-request template the classifier evaluates against (registry-managed; user-authored templates permitted under proposal-first registration)
- `confidence_threshold` — minimum confidence for the verdict to be honored; defaults belong to settings profiles, must be tested not hardcoded
- `consecutive_denial_fallback` — count after which repeated auto-denials of the same capability in the same scope fall through to ask-user
- `consecutive_approval_check_in` — count after which repeated auto-approvals present a "still happy with this?" check-in
- `escalation_path` — when confidence below threshold: `ask_user`, `direct_deny`, or `direct_allow` (only valid when declared tier is `ReadOnly` or below)
### 8.3 Flow
1. Construct a classifier model request from `policy_model_request_template_id`, the declaration, proposal args, resolved touched resources, active context (run, intent thread, task, conversation, workspace, invoker), recent policy history (prior approvals/denials of the same capability), any user-authored guidance attached to the policy template
2. Classifier invoked as a policy-internal model step through the model-strategy layer; honors provider allowlists, data sensitivity, rate limits, model settings; does not emit a nested `ToolCallProposed`, cannot call tools, cannot recursively ask for approval through the same router
3. Returns `ClassifierResult { decision, confidence, reasoning }`
4. If `confidence >= confidence_threshold` and decision is `Allow`/`Deny`, honored; emit `AutoDecideClassification { request_id, decision, confidence, reasoning, fell_back: false }` + corresponding `Continue`/`Block`
5. If `confidence < confidence_threshold` or decision is `Ask`/`Escalate`, fall through per `escalation_path`
6. Apply consecutive-denial-fallback + consecutive-approval-check-in counters per capability per scope; on threshold fall through to ask-user
7. Classifier result always recorded on the invocation record [`capability.invocation-record`, File 05 §11]; below-threshold results recorded too (`fell_back: true`) for offline tuning
### 8.4 Properties
Classifier result advisory: when policy still requires a human decision (typed-confirmation, `Denied` floor, contradiction, lease re-grant), the classifier does not override. Classifier never lifts `permission_floor`, never bypasses `Denied`, never lifts `typed-confirmation`. The model-request template is registry-managed+inspectable; user can view/customize/replace per capability or family. Per-call cost is one extra model invocation per proposed call when active; settings let users limit cost (e.g. enable only for `ReadOnly`, or only when a low-cost classifier is available). Per scope: enable globally, per workspace, per conversation, per capability, per family.
### 8.5 Boundary
Auto-decide composes with the rest; does not replace tier resolution/lease lookup/contradiction detection/floor enforcement. Output is one verdict among the inspector chain (§3.3); router merges it. Classifier model+template are configurable resources, not hardcoded; a capability without an active config follows the default tier-driven flow.

## 9. The Source-Approval Flow `policy.source-approval-flow`
### 9.1 Definition
Runs when a capability source registers — plugin loads, MCP server connects, external-API definition loaded, user-defined capability added through the runtime-registration path [`capability.runtime-mutation`, File 05 §16.2]. Surfaces declared metadata before capabilities become invocable; lets user accept declared defaults / customize per capability or source / deny outright / defer source-level policy / cancel registration.
### 9.2 Trigger Threshold
Triggered when the source risk summary crosses the configured review threshold; declared tier is one input, not the whole trigger. Risk summary includes: highest declared tier, highest permission floor, source trust, touched-resource classes, data sensitivity, external network/credential access, model-call access, filesystem scope, process/sandbox access, browser/UI/scheduler/sub-agent access, capability count+families, backend kinds, whether the source registers policy inspectors/templates/settings. Users tune thresholds by source class+resource class.
### 9.3 Proposal Preview
A `SourceRegistrationProposal` carrying:
- source identity: kind (`Plugin`, `McpServer`, `Api`, `UserDefined`, `Subsystem`), id, version, install path/remote URL, declared author, declared trust hint
- declared capabilities: each capability's id, display name, description, declared `permission_tier` (with `TierResolver` shape if dynamic), declared `permission_floor`, declared `capability_class`, declared `touched_resources`, declared `replay_class`, declared `data_sensitivity`, declared `approval_template_id`
- source risk summary: computed review-trigger facts + why review is/isn't required
- registered-entry trust state: source-authored trust hint, verification evidence when present, user trust override when present, `effective_trust` (computed per [`capability.trust-source-approval-flow`, File 05 §9.2])
- backend kind summary: which `backend_kind` values appear (per [`capability.backend-binding-lifecycle`, File 05 §10.4])
- policy extension summary: any policy inspectors/templates/settings/source-level rules the source attempts to register, incl. inspector authority classes
- optional: a registered linkage to a pre-existing source-approval-policy lease (e.g. a previously-approved version of the same source — user can inherit prior decisions or review fresh)
Rendered as a typed `SourceRegistrationProposal` event for the UI (§13).
### 9.4 User Options
- **Accept declared defaults** — every declared capability registers at its declared tier with default trust-driven narrowing (per §4.2 step 3); no per-capability lease; trust state from source hint + verification evidence + any user override
- **Customize per capability** — per capability: set a per-capability tier ceiling (capped above by the floor), grant a pre-approval (`AlwaysAllow` reusable-policy-rule lease), or deny outright (`AlwaysDeny` reusable-policy-rule lease); composed with declared defaults
- **Customize per source** — set a user trust override or default policy behavior for the source (changes the trust-narrowing input without mutating the source-authored hint)
- **Deny outright** — capabilities register but not invocable; each effectively gets an `AlwaysDeny` reusable-policy-rule lease; user can revisit+approve later
- **DeferSourcePolicy** — register the source while each capability remains gated by the configured fallback policy (`ask_each_time`, `require_explicit_approval`, or `ask_on_first_use`)
- **CancelRegistration** — registration does not complete, or the source remains catalogued only with capabilities disabled until future review
### 9.5 Persistence
User decisions persist as: user trust override on the registered entry [`capability.registered-capability`, File 05 §10]; reusable-policy-rule leases (§11) for per-capability pre-approvals/denials; capability-specific tier overrides through the settings cascade; per-source default-behavior selection through the cascade. User may revisit/edit any through settings or the registry's source-management surface (future UI). Edits emit the same `LeaseGranted`/`LeaseRevoked`/`SourceRegistrationApproved` events for audit consistency.
### 9.6 Trust Mapping Defaults `policy.trust-mapping-defaults`
Default trust-driven escalation for sources whose risk summary requires review:
- `Verified` / `System` — register at declared tiers; trust narrowing does nothing
- `Community` — declared at `WorkspaceWrite` or below register with effective tier `UserApproval`; declared at `UserApproval` or above unchanged
- `Unverified` / `Sideloaded` — declared at `WorkspaceWrite` or below register with effective tier `UserApproval` + require per-call ask-user (no `AlwaysAllow` honored without explicit user upgrade); declared at `UserApproval` or above register with the typed-confirmation flow on first use
Settings-overridable per source. Proposal preview surfaces trust state + resulting escalations so the user decides explicitly.
### 9.7 Properties
The flow is itself a capability invocation: `policy.review_source_registration` (or equivalent canonical id registered at runtime), `UserApproval`-tier (or `typed_confirmation` for `Sideloaded` sources at the user's option). Produces standard policy events. Closing/dismissing/failing to complete is `CancelRegistration`, not `DeferSourcePolicy`; never silently registers an invocable source.
### 9.8 Boundary
UI rendering owned by future UI specs. File 06 specifies the data contract (proposal shape, user's response shape, persisted lease shape) + the resolution algorithm. Actual registration mechanics (admit declaration, resolve backend binding, emit `CapabilityRegistered`) owned by [`capability.registered-capability`, File 05 §10] and [`capability.lifecycle`, File 05 §16]; File 06 gates whether registration completes, not how it executes.

## 10. Mid-Execution Policy Re-Evaluation `policy.mid-execution-policy-re-evaluation`
### 10.1 Lease Lifecycle States
- `Active` — `revocation_conditions` do not match current state; applies during tier resolution
- `Stale` — at least one revocation condition matches; no longer applies but preserved for inspection+potential re-grant; the next invocation that would have used it produces ask-user with staleness reason surfaced
- `Revoked` — explicitly revoked (manually, via policy template change, or via capability unregistration); no longer applies; retained for audit unless user explicitly prunes through storage controls
Transitions driven by `revocation_conditions` evaluation + explicit revocation calls.
### 10.2 Revocation Conditions
Typed predicates over active state. Required canonical conditions:
- `workspace_switch` — active workspace differs from the lease's `grant_context.workspace_id`
- `policy_change` — a settings change, lease grant/revocation, or template change altered the policy state the lease's grant assumed; grant_context records the relevant policy snapshot id
- `grant_evidence_unavailable` — policy layer cannot load/resolve the lease's referenced grant evidence, policy snapshot, touched-resource constraints, source/capability identity, or required world-model/artifact reference
- `capability_unregistration` — a capability the lease applies to was unregistered or its source disconnected
- `trust_downgrade` — the source's `effective_trust` decreased since grant (for source-level leases)
- `expiry_deadline` — the lease's `expires_at` (if set) has passed
- `manual` — user explicitly revoked
Capabilities+templates may declare additional conditions via the same registry mechanism+evaluation pattern. Any condition not evaluable declaratively against typed state is rejected — ad-hoc procedural revocation is an Explicit Rejection (§17).
### 10.3 Re-Evaluation Triggers
Re-evaluates active leases when: active workspace changes (state-awareness events); a settings change affects a policy-relevant key; a lease is granted/narrowed/revoked (cascading); a context/storage event affects grant evidence availability; a capability is unregistered; a registered-entry trust override changes; on demand through `policy.revalidate_leases` (a `ReadOnly` capability). Re-evaluation is bounded — only for leases whose `revocation_conditions` could be affected, not the whole set. Each condition declares trigger affinity: trigger kinds, affected scope fields, affected resource classes, affected setting keys/prefixes, whether evaluation is synchronous or must enqueue bounded revalidation work. Ordinary context compaction does not stale a lease; only durable grant evidence becoming unavailable/unresolvable can.
### 10.4 Stale Lease Handling
On transition to `Stale`: `LeaseStale { lease_id, staleness_reason }` emitted with typed reason; lease remains in storage in `Stale` state; the next invocation that would have used it produces ask-user (or typed-confirmation if the original lease's tier required it) with staleness reason surfaced in the `ApprovalRequest` reason payload; user options include re-grant at same scope, re-grant at narrower scope, revoke fully, or `AllowOnce` for this call only without re-granting. This is the canonical implementation of revoke-and-narrow-lease recovery from [`run.recovery`, File 04 §20.2]; the lease is not silently revoked.
### 10.5 Boundary
Re-evaluation is event-driven; policy layer does not poll. Trigger set is closed; new triggers register through the same mechanism that registers revocation conditions (a typed declaration of which condition kinds the trigger affects). Lease state mutations are durable+emit standard policy events.

## 11. The `Lease` Primitive `policy.lease-primitive`
### 11.1 Definition
A durable, scoped, typed approval record; the canonical primitive for persisted approval decisions across the shared scope hierarchy. Every persisted approval decision is a `Lease`; trivial single-call decisions the user does not persist are recorded as policy events without a `Lease`.
### 11.2 Required Fields
- `lease_id` — stable identifier for revocation reference
- `capability_match` — capability identity pattern: exact `(id, version)`, exact id with version-pinning policy (`latest`, `compatible`, `pinned`), capability family glob, or a registered match expression
- `scope` — one of `single_proposal`, `run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule` (per [`run.approval-during-execution`, File 04 §11])
- `invoker_kind` — optional constraint over the invoker class (`user_direct`, `model_agent`, `automation`, `scheduled_trigger`, `plugin_runtime`, `mcp_external`, `subagent`, `system_internal`)
- `invoker_context` — optional matching data for source id, run id, parent run id, automation id, plugin id, external client id, surface id when applicable
- `decision` — one of `AlwaysAllow`, `NarrowedAllow { constraints }`, `AlwaysDeny`
- `inherited_constraints` — typed constraints over touched resources (§6) + other call shape (argument-shape match, idempotency requirement, max invocations within scope, expiry deadline if any)
- `grant_reason` — free-text rationale + a typed `grant_origin` (one of `user_response_to_ask`, `source_approval_flow`, `automation_rule`, `built_in_template`, `policy_template_definition`)
- `grant_context` — snapshot at grant time: granting user identity, active conversation id, active intent thread id, active task id, active run id, active workspace id, active surface, world-model snapshot id, model-route at grant time, settings snapshot id, policy template version
- `granted_at` — timestamp
- `granted_by` — actor identity (user, automation, built-in template registration, source-approval flow)
- `expires_at` — optional explicit expiry deadline (omitted = no time-based expiry; revocation_conditions still apply)
- `revocation_conditions` — typed predicates per §10.2
- `status` — `Active`, `Stale`, or `Revoked`
A lease lacking any required field is invalid+rejected at grant time.
### 11.3 Scope Semantics
- `single_proposal` — one proposed call; never persisted as a `Lease`; recorded as a single-proposal policy event
- `run` — duration of one `Run`; revoked when run completes/fails/cancelled
- `intent_thread` — one semantic line of work inside a conversation; revoked when it closes/superseded/manually revoked
- `task` — duration of one `Task`; revoked when task completes/fails/cancelled
- `conversation` — within one `Conversation`; revoked when archived/deleted/explicitly closed
- `workspace` — within the granting workspace; revoked when workspace removed or user manually revokes
- `global` — across all workspaces/conversations/runs/tasks for the active user
- `reusable_policy_rule` — applies globally and is pattern-based; canonical shape for built-in safety rules + user-authored policy templates expressed as leases (e.g. "always deny `git.push --force` to protected branches")
`reusable_policy_rule` distinguished from `global` by capability matching: `global` typically pins one or a small set of ids; `reusable_policy_rule` uses pattern-based `capability_match` and is the canonical representation of policy-templates-expressed-as-leases.
### 11.4 Composition
Multiple leases may apply; the lease selection rule (§6.4) chooses deterministically (narrower scope wins, deny-wins on tie, most-recently-granted on remaining ties). Leases never compose by averaging/majority; one lease applies per call, or none. A `single_proposal` lease never affects a future call.
### 11.5 Built-In Reusable Policy Rules `policy.built-in-reusable-policy-rules`
System ships built-in reusable policy rules as system defaults with stable ids; they project to effective reusable-policy-rule leases at evaluation time, after durable user override records are applied (avoids ambiguity on restart: defaults re-register, then user disables/narrows/widens/template edits/replacements/restore-default applied as separate audit-visible records).
Built-in default rules:
- `git.push --force` to a configured protected-branch-list branch → `AlwaysDeny` with typed-confirmation override per §7.4
- `system.shutdown` invoked by an agent → `AlwaysDeny` with typed-confirmation override
- `account.delete` invoked by an agent → `AlwaysDeny` with typed-confirmation override
- `credential.export` to any external destination → `AlwaysDeny` with typed-confirmation override
- shell commands matching the registered dangerous-pattern set (recursive deletes against absolute roots, formatting devices, raw block-device writes) → `AlwaysDeny` with typed-confirmation override
- `shell.exec` patterns where a registered dedicated capability exists (CT.16 "prefer dedicated tools") → `RedirectSuggestion` to the dedicated capability when configured at canonical `Strict` mode; `Warn` and `Off` modes per the dedicated-tool preference setting
- `shell.exec` network-fetch patterns after a recent `web.fetch` denial in the same run (CT.16 "fetch fallback ban") → `AlwaysDeny` when `Forbidden`; `UserConfirmed` (escalate to ask-user) when set to that mode; `Allowed` (no rule) when off
User-customizable: disable/narrow/widen/replace/restore through settings. Disabling/widening a rule protecting an irreversible op is itself a typed-confirmation flow per §7. Ledger records both the system default and the user override that changed effective behavior.
### 11.6 Persistence `policy.persistence`
Leases are durable, survive process restarts. Storage schema = future Storage spec; File 06 specifies the field set storage must support, the lease event vocabulary storage receives, the resolution rules the runtime applies on read. State changes (grant, narrow, revoke, transition to Stale) recorded as policy events with full envelope; the lease itself is the projection over those events; events are source of truth. Active+Stale leases not pruned by storage without a policy-layer state transition; Revoked leases retained for audit by default; retention user-controlled through explicit storage settings+destructive maintenance actions; pruning must warn that audit/replay/conversation continuation may lose policy history; canonical default is indefinite retention, not fixed expiry.
### 11.7 Boundary
Leases are an evaluation primitive owned by File 06. Persistence schema, storage-side projections, cross-device sync, import/export = future Storage and Sync specs.

## 12. Approval-Policy Templates `policy.approval-policy-templates`
### 12.1 Definition
A named, registered, composable validator chain consulted by the evaluator's `template-evaluation` inspector during tier resolution. A declaration's `approval_template_id` [`capability.permission-policy-fields`, File 05 §3.5] names the default template applied when policy evaluates that capability.
### 12.2 Required Properties
- `template_id` — stable namespaced identifier
- `display_name`, `description`, `short_description` — localizable per the canonical pattern (literal defaults + optional i18n keys)
- `family_applicability` — capability families the template applies to (`*` for any)
- `scope_applicability` — lease scopes at which it may be applied
- `validators` — ordered list of typed validator declarations
- `typed_confirmation_required` — bool; true means any call routed through it uses typed-confirmation flow
- `denied_override_via_typed_confirmation` — bool; for templates on `Denied`-floor capabilities, whether the override path is available
- `confirmation_string_pattern` — when typed-confirmation required, the pattern the user's string must match; may interpolate validated `args.*` field paths
- `approval_text_template` — localizable request text shown during ask-user/typed-confirmation flows
- `source` — `Builtin`, `Subsystem { id }`, `Plugin { id, version }`, `UserDefined { scope }`
### 12.3 Validator Verdicts
A validator produces one of: `Allow` (proceed); `Deny` (block); `Ask` (escalate to ask-user); `Escalate` (escalate to typed-confirmation); `NoOpinion` (pass to next). Chain runs in declared order, aggregates by severity: `Deny > Escalate > Ask > Allow > NoOpinion`. Every validator mandatory by default (runs unconditionally, verdict participates in severity max). `Allow` final only when no mandatory validator produces a stricter verdict. If every validator returns `NoOpinion`, the template's terminal default applies (configurable per template; canonical default is `NoOpinion`, in which case the other inspectors decide). A validator may be `terminal` only when the template explicitly marks it terminal and all built-in+system-source validators in the chain already produced verdicts; no non-system-source validator may declare itself terminal. Final aggregate verdict+decisive validators recorded in policy events. Validators may be deterministic (typed predicate over args+context) or model-mediated (per auto-decide §8); deterministic is default; model-mediated opt-in, inheriting auto-decide's confidence-thresholded fallback.
### 12.4 Built-In Templates
- per-tier defaults: `tier_default_readonly`, `tier_default_workspace_write`, `tier_default_user_approval`, `tier_default_unrestricted`, `tier_default_denied` — applied when a capability declares no explicit `approval_template_id`
- per-class defaults from CT.20: `class_internal_analysis_default` (defaults to ReadOnly tier-resolution behavior), `class_action_external_default` (defaults to UserApproval with batched-approval support), `class_user_artifact_default` (defaults to WorkspaceWrite with workspace-containment escalation)
- behavioral templates from CT.16: `clarify_first_for_multistep` (check whether a multi-step task started without prior clarification, emit `Ask` with clarify-first request text), `todos_for_multistep` (check the agent invoked the todo capability before non-trivial tool sequences), `prefer_dedicated_tools` (emit `RedirectSuggestion` when `shell.exec` is invoked with a pattern having a registered dedicated-tool equivalent), `fetch_fallback_ban` (emit `Deny` when shell network-fetch capabilities invoked after a recent same-run `web.fetch` denial)
- safety templates per the canonical reusable-policy-rule set (§11.5): `git_protected_branch_force_push_denied`, `irreversible_op_typed_confirmation`, `dangerous_command_typed_confirmation`, `secret_export_denied`
- subsystem- and surface-default templates: registered subsystems+work surfaces may ship default templates overridable per capability
Built-in templates settings-overridable per scope: disable any, customize request text, narrow applicability, or replace with a user-authored one.
### 12.5 User-Authored Templates
Registered through the runtime-registration capability [`capability.runtime-mutation`, File 05 §16.2] under the source-approval flow (§9); same field set as built-ins; enter as `UserDefined { scope }`; subject to the same pipeline. May not override the floor-enforcement step (§4.2 step 2); attempting to grant `Allow` for a `Denied`-floor capability produces `PolicyFloorViolated`, floor wins, template recorded as registered but policy-inert for that capability.
### 12.6 Composition
An invocation may have multiple templates applicable: capability's declared default + user-set per-capability/per-scope overrides + active reusable-policy-rule leases expressing templates. Evaluator runs each in order: capability default first, scope-level overrides second, reusable-policy-rule leases last. Verdicts aggregate by the §12.3 severity lattice; ordering affects deterministic explanation, not silent safety bypass.
### 12.7 Boundary
Templates are policy-evaluation declarations; storage schema, version evolution, import/export = future Storage+Sync specs; UI presentation (template editor, validator-chain visualizer, approval-text preview) = future UI specs. File 06 specifies field set, validator verdict semantics, composition order.

## 13. Approval UI Surface Contract `policy.approval-ui-surface-contract`
### 13.1 Definition
The `Approval UI Surface Contract` is the typed data contract the policy layer exposes for any user-facing approval surface; a data contract, not a UI spec. Multiple presentation surfaces consume the same typed payloads, respond through the same typed channel.
### 13.2 `ApprovalRequest`
Every ask-user/typed-confirmation/batched-approval/contradiction-resolution flow produces an `ApprovalRequest`:
- `request_id` — stable identifier for the round-trip
- `flow_kind` — one of `ask_user`, `typed_confirmation`, `lease_grant_proposal`, `lease_stale_re_grant`, `contradiction_resolution`, `source_registration` (the latter routes through §9)
- `invoker_kind`, `invoker_context` — who/what initiated (direct user action, model agent, automation, plugin runtime, external MCP client, subagent, system-internal process)
- `capability_id`, `capability_version`, `capability_display_name`, `capability_description`, `capability_short_description`, `capability_family`
- `resolved_args` — resolved invocation args with `data_sensitivity` redactions (`Sensitive` shown with reduced detail; `Secret` shown only as kind labels)
- `reason` — human-readable, combining model's stated intent (when available) + policy-supplied justification (e.g. "tier UserApproval, no active matching lease")
- `resolved_tier` — effective tier after resolution
- `permission_floor` — declared floor (so UI can communicate "cannot be lowered")
- `resolved_touched_resources` — concrete touched resources resolved per §6
- `data_sensitivity` — declared classification
- `trust_state` — registered entry's `effective_trust`
- `available_options` — typed `LeaseOption` set (§13.3)
- `classifier_result` — when auto-decide produced a below-threshold or `Ask`/`Escalate` verdict, the typed result is included
- resolved proposal facts projected from File 05: `side_effect_class`, `reversibility_class`, `replay_class`, `postconditions`, `required_observations`, `expected_artifacts_or_outputs`
- synthesized proposal facts: `preview_payload` from declared preview mode, `data_egress_summary` from resolved network/credential resources+sensitivity, `sandbox_or_isolation_summary` from active execution context, `rollback_or_compensation_note` when available
- `batch_id` — optional, present when part of a batched approval per §5.5
- `contradictions_detected` — typed `Contradiction` records when this is a contradiction-resolution flow per §14
- `lease_staleness` — typed reason when this is a lease-stale-re-grant per §10.4
- `approval_text` — localized request text from the active template
- `confirmation_string_pattern` — present only for typed-confirmation; the pattern the typed string must match per §7.4; template variables referencing validated `args.*` field paths resolve to concrete values (e.g. `force-push to {args.branch}` → `force-push to main`); static patterns remain valid; sensitive interpolations preserve redaction (`Secret` values use safe labels/typed surrogates, not raw values)
Flows through the canonical event bus carrying the standard envelope (`conversation_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `sequence`, `timestamp`, `sensitivity`).
### 13.3 `LeaseOption` (16 kinds)
`available_options` carry typed `LeaseOption` entries; each declares:
- `kind` — one of: `AllowOnce`, `AllowForRun`, `AllowForIntentThread`, `AllowForTask`, `AllowForConversation`, `AllowForWorkspace`, `AllowGlobal`, `AlwaysAllowReusableRule`, `DenyOnce`, `DenyForRun`, `DenyForIntentThread`, `DenyForTask`, `DenyForConversation`, `DenyForWorkspace`, `DenyGlobal`, `AlwaysDenyReusableRule`
- `scope_label`, `scope_description` — localized per the canonical descriptor pattern
- `default_constraints` — constraints created if selected without customization (typically derived from the proposed call's resolved touched resources)
- `user_customizable_constraints` — declarative description of which dimensions the user may narrow (e.g. path subtree for filesystem, host set for network); UI presents as editable fields
- `typed_confirmation_required` — bool; true for options granting a lease against a typed-confirmation-required capability (such options typically restricted to `AllowOnce` only, since persistent leases against typed-confirmation are forbidden per §7.3)
Available option set computed by policy from tier, floor, applicable templates, active leases, settings. Options that would violate floor or pierce a deny lease are excluded; UI never offers an unavailable option.
### 13.4 `ApprovalResponse`
- `request_id` — matches the request
- `choice` — one of the available `LeaseOption` kinds, or `Cancel`
- `customized_constraints` — when narrowed, the typed customized constraints
- `typed_confirmation_string` — for typed-confirmation flows, the user's typed string (validated against `confirmation_string_pattern`)
- `reason` — optional free-text rationale for audit
Flows back through the same bus. Policy awaits a response per `request_id`; on receipt validates choice+customization against available options, emits the corresponding `LeaseGranted` or `PolicyDecisionMade`.
### 13.5 `BatchApprovalRequest`
A batched approval (§5.5): `batch_id`; `items` (constituent `ApprovalRequest` payloads); `batch_options` (`ApproveAll`, `DenyAll`, `PerItem`); `scope_summary` (the batched scope). User response is a `BatchApprovalResponse` carrying a batch-level choice (`ApproveAll`/`DenyAll`) or per-item responses.
### 13.6 `ContradictionResolutionRequest`
A contradiction-resolution flow (§14): `request_id`; `contradictions` (typed `Contradiction` records describing conflicting policy elements — lease, scope-level override, template, source whose verdicts conflict); `resolution_options` (respect the narrower scope (default), respect the broader scope, revoke the conflicting lease, or modify a contradicting setting).
### 13.7 Required Surface Properties
Any presentation surface must: present `approval_text`, `resolved_args` (with sensitivity redactions intact), `reason`, `resolved_tier`, `permission_floor`; present invoker identity, resolved proposal facts, synthesized preview/egress/isolation facts, and absence of preview when preview unavailable for a mutating/high-risk call; present every `available_option` with scope label/description/default constraints; allow customizing `user_customizable_constraints` for any option declaring them; for typed-confirmation, present `confirmation_string_pattern` requirement+validate the typed string before submission; emit the `ApprovalResponse` through the bus; support keyboard navigation, voice control, screen-reader operation per canonical accessibility requirements. Contract does not specify modal-vs-inline rendering, color, layout, animation; multiple surfaces (conversation-inline, modal, voice confirmation, command-palette inline, batched review, automation pre-flight review) consume+render appropriately.
### 13.8 Boundary
Policy layer never invokes UI methods directly; it emits typed events. UI subscribes to `ApprovalRequested` and equivalents, renders, emits `ApprovalResponse`. Decoupling means the machinery works under any UI shell, headless CLI, voice-only, programmatic-test harness.

## 14. Contradiction-Checking Across Scope Levels `policy.contradiction-checking-across-scope-levels`
### 14.1 Definition
`Contradiction-Checking` is the policy layer's resolver for cross-scope conflicts in lease/settings/template state. The canonical rule from [`run.approval-during-execution`, File 04 §11] — contradictions across scope levels surface as policy errors, not silent wins — enforced here.
### 14.2 Resolution Rules
- **Tighter-narrower-deny wins**. A narrower-scope element producing `Deny` overrides a broader-scope `Allow`; natural deny-wins; not flagged as a contradiction.
- **Tighter-narrower-allow under broader-deny is a contradiction**. A narrower-scope `Allow` against a broader-scope `Deny` (e.g. a conversation-level `AlwaysAllow` lease for a globally denied capability) is a contradiction → emit `PolicyContradictionDetected { capability_id, contradicting_elements }` → route to a contradiction-resolution flow per §13.6; runtime never silently weakens the broader deny.
- **Floor never participates**. An element attempting to lower a tier below `permission_floor` → `PolicyFloorViolated`; floor wins; the violating element recorded as floor-violating but not a cross-scope contradiction; user may revoke through standard revocation paths.
- **Typed-confirmation never lifts**. An element attempting to skip typed-confirmation → `TypedConfirmationCannotBeLifted`; typed-confirmation wins; recorded similarly.
- **Reusable-policy-rule leases compose with same precedence**. A reusable-policy-rule lease producing `Deny` checked against narrower-scope `Allow` leases the same way; same contradiction-detection-and-surface rule.
### 14.3 Detection Timing
- at lease grant time — a new lease checked against existing leases/settings/templates; conflict surfaced before commit (user must resolve in the lease grant flow)
- at policy evaluation time — a proposed call's tier resolution checks active leases+settings for conflicts; surface as contradiction-resolution requests
- at re-evaluation time — when a state change triggers re-evaluation per §10.3, contradiction detection re-runs over affected leases
### 14.4 Resolution Outcomes
Resolved by one of: user picks a side (respect narrower/broader; conflicting element revoked/narrowed); user revokes both (call falls through to the default tier-driven flow); user creates a new lease that explicitly resolves the conflict (e.g. a workspace-scope `Allow` lease noting "overrides the global `Deny` for this workspace"). Resolution persisted as a `PolicyContradictionResolved` event linked to the originating contradiction; subsequent calls do not re-trigger the same contradiction.
### 14.5 Boundary
Contradiction-checking is policy-layer logic; UI renders the request per §13.6 and emits the typed response; policy applies the resolution+emits events. Contradictions detected in the source-approval flow during registration follow the same pattern, with resolution embedded in the source-approval flow's user options per §9.4.

## 15. Risk Classification and Trust Interaction `policy.risk-classification-trust-interaction`
### 15.1 Three-Class Capability Taxonomy (CT.20)
- `InternalAnalysis` — read-only ops supporting reasoning (file reads, searches, queries); default tier `ReadOnly`
- `ActionExternal` — ops mutating external state (sending email, file writes, database writes, browser navigation, GUI clicks); default tier `UserApproval`
- `UserArtifact` — ops producing user-visible deliverables (file create within workspace, document edit, image generation); default tier `WorkspaceWrite`
Class declared per capability through File 05's required `capability_class` field. Tags may mirror the class for discovery but are not policy truth. Class influences default `approval_template_id` selection but does not override an explicit declaration.
### 15.2 Trust Interaction
Trust-driven escalation (per §4.2 step 3) interacts with the taxonomy:
- `InternalAnalysis` from `Community`/`Unverified` — trust-driven escalation only when the resolved touched resources include `network`, `credential`, `sub-agent`, or registered extension classes carrying user-private data
- `ActionExternal` from `Community`/`Unverified` — always receive trust-driven escalation (canonical one-tier or two-tier per §9.6)
- `UserArtifact` from `Community`/`Unverified` — escalation when touched resources include filesystem paths outside the active workspace or external-credential references
Settings-overridable per source: user may set a user trust override changing effective trust (e.g. treating a `Community` source as verified for local policy) or explicitly tighten an `InternalAnalysis` capability beyond its class default.
### 15.3 Risk Classification of Unknown Capabilities
A capability whose class is `Unknown` is treated as if `ActionExternal` for trust escalation. The source-approval flow surfaces unknown classes as a customization opportunity; user may set a class manually or accept the conservative default.
### 15.4 Per-Call Model-Mediated Risk Classification
When a capability declares `classification_mode: ModelMediated` for relevant fields (per [`capability.classification-mode`, File 05 §7.2]), the per-call classifier produces typed values for those fields. Policy consumes them during tier resolution: a `shell.exec` classified `reversibility_class: none` + `partial_output_meaningful: false` resolves at a higher tier than the same classified `reversibility_class: compensable`. Classifier confidence threshold+fallback rules per §8.
### 15.5 Boundary
Risk classification is one input to tier resolution; classification comes from the declaration (`capability_class`, declared `replay_class`, declared `reversibility_class`) + registered trust state + per-call model-mediated classification when active. File 06 specifies how classification feeds into resolution; does not invent a separate risk-scoring mechanism.

## 16. Settings Resolution for Policy `policy.settings-resolution-for-policy`
### 16.1 Configurable Dimensions and Layer Ownership
File 15 owns settings resolution; File 06 owns how already-resolved settings compose into decisions. Dimensions:
- per-capability `permission_tier` overrides (capped above by `permission_floor`), per scope
- per-capability `approval_template_id` overrides, per scope
- per-source trust overrides (`registry_trust_override`), global only by default; settings may permit per-workspace overrides
- per-template enable/disable, per scope
- approval-posture preset — `Strict`, `Balanced`, `Permissive`, plus user-authored profiles
- per-flow timeouts (ask-user, typed-confirmation, batched approval) + timeout fall-through behavior; defaults belong to settings profiles
- auto-decide configuration (per capability/family) — enablement, classifier model, policy model-request template, confidence threshold, fallback rules per §8.2
- batched approval grouping keys + maximum batch size
- grant-evidence availability revalidation behavior
- per-source-class default `DeferSourcePolicy` fallback behavior (`ask_each_time`, `require_explicit_approval`, `ask_on_first_use`)
- source-approval flow risk thresholds per source class + resource class
- protected-branch seed list; consumed by git-related built-in safety rules per §11.5
- dedicated-tool preference mode (`Strict`, `Warn`, `Off`) per CT.16
- fetch-fallback policy (`Forbidden`, `UserConfirmed`, `Allowed`) per CT.16
- per-subsystem and per-surface approval-posture override
- approval-posture defaults contributed by active profile layers
### 16.2 Resolution Algorithm
Policy reads policy-relevant settings through File 15's source stack: invocation overlay, conversation, workspace, global, local explicit overlay, active profile layers, then definition default policy. Per-source overrides resolve through the same model, keyed by source identity. The approval-posture preset is a settings-resolved meta-setting: selecting a posture sets sensible defaults for all dimensions; advanced users can still override individual dimensions, and overrides persist across posture changes (changing posture does not reset prior per-capability customizations).
### 16.3 Approval-Posture Presets
- `Strict` — every `UserApproval` produces ask-user (no `AlwaysAllow` honored unless explicitly user-granted in strict mode); `auto-decide` off; typed-confirmation triggers more aggressively (any `Denied`-floor or any `reversibility_class: none`); `dedicated-tool preference: Strict`; `fetch-fallback: Forbidden`
- `Balanced` — per-capability defaults from declarations+built-in templates apply; `auto-decide` opt-in per capability/family; typed-confirmation only for declared cases; `dedicated-tool preference: Strict`; `fetch-fallback: Forbidden`; batched approval enabled
- `Permissive` — `auto-decide` on by default for `ReadOnly` + contained `WorkspaceWrite`; `UserApproval` defaults to ask-user but with one-click `AlwaysAllow` for the active workspace; typed-confirmation only for irreversible ops; `dedicated-tool preference: Warn`; `fetch-fallback: UserConfirmed`
Presets are starting points, not prescriptive; the user always retains explicit control through per-capability+per-source overrides.
### 16.4 Agent Exposure of Policy Settings `policy.agent-exposure-policy-settings`
- approval-posture preset, current `effective_trust` per source, per-capability tier overrides — `OnRequest` (agent reads on request through the read-only settings tool; agent never sees per-call ask-user history beyond conversation context)
- typed-confirmation strings, lease grant contexts, source-approval proposals — `Hidden` (agent never sees the user's typed confirmation strings or full grant-context snapshots)
- the active approval-posture preset — `InModelRequest` (model-request instructions include the active posture so the agent adjusts behavior, e.g. avoid proposing higher-tier capabilities in `Strict` mode)
### 16.5 Boundary
Settings resolution owned by File 15; File 06 specifies which dimensions are policy-relevant + how resolved values compose; does not reinvent settings storage/validation/profile layers/agent exposure/UI.

## 17. Explicit Rejections `policy.explicit-rejections`
Wrong for this layer:
- a parallel approval pipeline beside the canonical hook bus — every decision flows through the `ToolCallProposed` blocking hook subscriber + the typed event-bus contract; capabilities/plugins/MCP servers/subsystem extensions never invent their own approval mechanism
- per-capability custom approval logic baked into capability handlers — authors implement the operation; the policy layer evaluates approval; mixing creates "capability leakage" (rejected per [`capability.contract-composition`, File 05 §17] / [`capability.explicit-rejections`, File 05 §19], re-rejected here)
- silent approval: any direct-execution path must emit `PolicyDecisionMade` with reason; no call executes without a recorded decision event
- silent denial: a denied call always produces a typed `PermissionDenied`-class result block in-band per [`run.denial-is-in-band`, File 04 §8.3] + `PolicyDecisionMade`; the agent/user must always have a chance to react
- silent contradiction resolution: cross-scope conflicts surfaced as typed events + resolved through the user-facing flow; runtime never picks a winner that weakens an outer deny or pierces a `permission_floor`
- floor-piercing: settings, leases, trust upgrades, scope-level overrides, `agent.unrestricted_mode`, approval-policy templates can never lower below `permission_floor`; `PolicyFloorViolated` records any attempt, floor wins
- bypassing typed-confirmation: leases, settings, trust upgrades, `auto-decide`, batched approval, `agent.unrestricted_mode` can never lift it; only path through `Denied` is the explicit typed-confirmation override per §7.4
- model-mediated approval as the silent default: `auto-decide` is opt-in per capability/family; runtime never silently classifies away a user's approval requirement; below-threshold classifier results fall through to ask-user
- recursive policy approval: policy-internal auto-decide classifier calls do not emit nested `ToolCallProposed` events or recursively invoke the router
- collapsing invoker classes: direct user actions, model-agent calls, automation, plugin runtimes, external MCP clients, subagents, system-internal calls evaluated by one layer but retain distinct invoker meaning
- untrusted inspectors silently allowing/rewriting policy outcomes: inspector authority classes constrain what third-party code can decide
- silent semantic substitution: `Substitute` may only perform declared narrowing or transparent redirects; changing target/action semantics requires ask-user
- ad-hoc procedural revocation conditions: leases revoke through declared typed predicates only; runtime closures not eligible (cannot be inspected, replayed across devices, or evaluated against persisted state)
- registering a lease whose `capability_match` references a missing/unregistered capability — rejected at grant time; user informed; never silently activates if the capability later registers with a matching id
- treating trust state as a declaration: source trust is registered-entry state per [`capability.trust-source-approval-flow`, File 05 §9.2]; any mechanism mutating a declaration field based on trust is rejected; trust narrowing is policy-side
- a single global "approval policy" overriding per-capability templates+per-scope overrides — policy is composed not monolithic; built-in defaults + templates + leases + settings compose deterministically; no single setting silently overrides the composition
- routing approval decisions through unrelated services/sidecars (logging service, telemetry service, automation service) — the router is the canonical decision point; logging+telemetry observe but never decide
- requiring the user to type a confirmation string the system computes from arguments without disclosing the string — the request always shows the required string; the user types it as a deliberate-intent check, not a guess
- silently auto-approving a typed-confirmation override when the user previously typed-confirmed the same operation — typed-confirmation is per-call, never persists as an `AlwaysAllow` lease; every invocation requires fresh input
- producing approval decisions other than `Continue`, `Substitute`, `Block`, or `RedirectSuggestion` — the canonical hook decision vocabulary is closed
- approval flows depending on time-based polling rather than event-driven evaluation — re-evaluation triggers event-driven per §10.3; never polls
- hardcoded numeric policy defaults in this canonical layer — thresholds, counters, batch sizes, protected-branch seed lists, timeout behavior belong to tested settings profiles
- registering policy-evaluation logic in capability handlers, command-palette wrappers, voice intent resolvers, or any UI surface — every path ultimately passes through the canonical router; surfaces present+dispatch but never decide
- preserving any earlier name for the same primitive as a parallel system — `Lease` supersedes `AlwaysAllow record`/`approval policy entry`/`permission grant`/`auth lease`; `Approval Router` supersedes `permission inspector chain`/`approval pipeline`/`consent system`; `Approval Policy Template` supersedes `safety rule set`/`policy rule list`/`permission profile`; `Auto-Decide` supersedes `YOLO classifier`/`SmartApprove`/`auto-approve mode`; `Source-Approval Flow` supersedes `permission manifest negotiation`/`plugin install approval`/`MCP server connection approval`. None survive as a parallel primitive.

## 18. Consequences for Later Specs `policy.consequences-for-later-specs`
Every later spec touching capability invocation/registration/automation/runtime/UI/storage/sync/telemetry/evaluation consumes the Capability Policy layer as defined here. Canonical principles:
- read approval decisions from the policy layer through the typed event-bus contract; never invent a parallel approval mechanism, never inline policy logic into a capability handler/UI component
- read effective tiers, lease state, contradiction state through the policy layer's read interface; never compute these independently from declarations
- record per-call resolved facts on the `CapabilityInvocation` record per [`capability.invocation-record`, File 05 §11] + the policy events; never on the declaration/registered entry
- treat `Lease` as the durable approval primitive; persisted approval state lives as `Lease` records + the events that produce them; never as a parallel "always-allow"/"permission grant"
- treat `Approval-Policy Template` as the canonical reusable rule set; user-authored safety rules, subsystem/surface-specific policies, built-in patterns all register as templates; never a parallel rule registry
- treat `Source-Approval Flow` as the canonical capability-source onboarding mechanism; plugin install approval, MCP connection approval, external-API definition approval, user-defined capability registration all flow through it; never parallel install flows
- honor the four canonical approval flows (ask-user, typed-confirmation, auto-decide, batched approval) as the closed set; introduce new flows only by extension within these shapes (a "voice-confirmation" surface is a presentation of ask-user, not a fifth flow)
- honor the four direct-execution conditions (`ReadOnly` outcome, contained `WorkspaceWrite` with `direct_allow` mapping, active matching `AlwaysAllow` lease, `Unrestricted` with the relevant `agent.unrestricted_mode` setting on) as the closed set; never introduce another bypass
- honor floor enforcement: settings, leases, trust upgrades, `agent.unrestricted_mode`, approval-policy templates never lower below `permission_floor`
- honor typed-confirmation as the only path through `Denied`; never lift it through any combination of leases/settings/trust upgrades/modes
- honor the contradiction-detection rule: tighter-narrower-allow under broader-deny surfaces as a typed contradiction; never silently weaken the broader deny
- honor the trust-driven narrowing rule: `Community` and `Unverified` sources cause policy-side tier escalation; declarations not mutated; effective tier computed at evaluation time
- emit policy events through the canonical event bus with the standard envelope; never emit policy decisions through telemetry side channels/out-of-band logs as the source of truth — the ledger is source of truth, telemetry is a projection
- consume the source-trust state from the registered entry per [`capability.trust-source-approval-flow`, File 05 §9.2]; never rebuild trust state from declarations/out-of-band heuristics
- consume the canonical `capability_class` taxonomy (`InternalAnalysis`, `ActionExternal`, `UserArtifact`, `Unknown`); extension classes register through the same capability-class extension mechanism when such exists
- consume the canonical revocation conditions + re-evaluation triggers; new conditions register through the typed-declaration mechanism with explicit trigger affinity
- consume the canonical `ApprovalRequest` / `LeaseOption` / `ApprovalResponse` / `BatchApprovalRequest` / `ContradictionResolutionRequest` data contract for any user-facing approval surface; never invent a parallel approval data shape
Specific integration contracts stated in those files when written.
