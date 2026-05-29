# Capability Policy, Approvals, and Leases

## 1. Chosen Model {policy.chosen-model}
- One Capability Policy layer; every consequential invocation must pass through it: `Run`-internal model-emitted tool calls, user-invoked actions, automation triggers, scheduled tasks, MCP-exposed external invocations, capability registrations.
- `Lease` is the canonical durable approval primitive; the scope field discriminates. No separate "always-allow record"/"approval policy entry"/"permission grant" type.
- `Approval Policy Template` is the canonical reusable rule set.
- `Source Approval Flow` is the canonical capability-source onboarding mechanism.
- No per-subsystem/per-surface bespoke approval logic; no separate MCP/plugin approval system.
- Canonical names: `approval-posture preset`, `approval mode`, `auto-decide`, `Lease`.

## 2. Boundaries with Adjacent Layers {policy.boundaries-with-adjacent-layers}
### 2.1 With File 05
- File 06 must read from declarations+registered state, never mutate either.
### 2.2 With File 04
- A denied call must produce a typed result block linked to the proposal, received in-band.
### 2.3 With Cross-Cutting Substrate
- Settings cascade: conversation → workspace → global → overlay → declared default; no parallel settings store.
### 2.4 Boundary

## 3. The Approval Router {policy.approval-router}
### 3.1 Definition
- A single blocking hook subscriber on `ToolCallProposed` at priority `+100`; emits one typed `ApprovalDecision`.
### 3.2 Position in Capability-Call Pipeline
1. Resolve capability
2. Validate input
3. Produce proposal
4. Run validators and policy checks
5. Determine denial, approval need, persisted decision, or active lease — the Approval Router
6. Execute with declared isolation+concurrency semantics
7. Stream partials when supported
8. Record observations+result
9. Validate postconditions
10. Commit or expose output
### 3.3 Internal Composition — Policy Inspectors {policy.internal-composition-policy-inspectors}
- Required built-in inspectors: `tier-resolution`, `template-evaluation`, `touched-resource-matching`, `contradiction-detection`, `classifier-mediation`, `risk-classification`.
- Template verdicts: `Allow`, `Deny`, `Ask`, `Escalate`, `NoOpinion`.
- Inspector authority classes: `observe_only`, `narrowing_only`, `allow_capable`, `substitute_capable`.
- Community/unverified/plugin/MCP/API/user-defined inspectors must default to `narrowing_only` until user explicitly upgrades authority.
- No inspector can bypass `permission_floor`, typed-confirmation, contradiction detection, or touched-resource constraints.
- Ordering: `tier-resolution` first, `template-evaluation`, `touched-resource-matching`, `risk-classification`, `classifier-mediation`, `contradiction-detection` last.
- A `Deny` from any required inspector wins immediately; user/plugin inspectors cannot be placed before `tier-resolution` or after `contradiction-detection`.
### 3.4 Output
- Four typed `ApprovalDecision` outcomes: `Continue`, `Substitute`, `Block`, `RedirectSuggestion`.
- `Substitute` valid only for declared constraint narrowing, sensitivity-preserving redaction, sandbox narrowing, or transparent redirect; semantic target/action changes require ask-user.
- Any other outcome is an Explicit Rejection.
### 3.5 Failure Mode
- Router fails closed on timeout/error → synthesized `Block`.
- Configuration errors do not retry, fail closed immediately, produce `PolicyConfigurationError`.
### 3.6 Boundary

## 4. Effective Tier Resolution {policy.effective-tier-resolution}
### 4.1 Definition
### 4.2 Algorithm (fixed order)
1. **Declared tier** — resolve `permission_tier` (`TierResolver::Static` or `TierResolver::Dynamic` deterministically).
2. **Floor enforcement** — result clamped from below by `permission_floor`; floor never lowered; any later step below floor produces `PolicyFloorViolated` and the floor's tier is used.
3. **Trust narrowing** — `System`/`Verified`/`User` no narrowing; `Community` minimum `UserApproval`; `Unverified` minimum `UserApproval` AND first invocation per conversation requires per-call ask-user. Trust narrowing never crosses the floor.
4. **Scope-level setting overrides** — per-capability+per-source tier ceilings from the cascade; never lower below floor.
5. **Lease lookup** — narrower scope wins; among same-scope deny-wins; matching `AlwaysAllow` → direct execution at lease tier (bounded by floor); matching `AlwaysDeny` → immediate `Block`.
6. **Decision selection** — resulting tier + verdicts → terminal decision per §5.
- Output: typed `EffectiveTierDecision` flows onto the invocation record.
### 4.3 Required Outcomes
- Exactly one terminal outcome per call: `direct_allow`, `direct_deny`, `ask_user`, `typed_confirmation`, `model_mediated`.
- Tier-to-outcome mapping: `Denied` → `direct_deny` always (only path is typed-confirmation override of `Denied`); `ReadOnly` → `direct_allow`; `WorkspaceWrite` contained → `direct_allow`; `WorkspaceWrite` escaping workspace → escalates to `UserApproval`; `UserApproval` → per leases/auto-decide/ask_user; `Unrestricted` → `direct_allow` only when `agent.unrestricted_mode` enabled, else `UserApproval` rule; typed-confirmation variant of `UserApproval` → `typed_confirmation` always.
- Any outcome outside this set is an Explicit Rejection.
### 4.4 Boundary
- Tier resolution must remain fast enough for every call.

## 5. Approval Flows {policy.approval-flows}
### 5.1 Definition
- Four flows: `ask-user`, `typed-confirmation`, `auto-decide`, `batched approval`.
### 5.2 Ask-User Flow
1. Construct an `ApprovalRequest` payload.
2. Emit `ApprovalRequested` with canonical envelope.
3. Await the typed `ApprovalResponse`; configured timeout fail direction applies (fail-closed as the safe profile).
4. If the choice creates a lease, persist it; emit `LeaseGranted`.
5. If `AllowOnce`/`DenyOnce`, no lease created.
6. Emit `ApprovalGranted`/`ApprovalDenied` + `PolicyDecisionMade`.
7. Return the typed `ApprovalDecision` to executor.
- Narrowed constraints must be typed+machine-checkable.
### 5.3 Typed-Confirmation Flow
### 5.4 Auto-Decide Flow
### 5.5 Batched Approval Flow {policy.batched-approval-flow}
- Natural boundaries: one model response, one programmatic step, one script/workflow step, one child-run spawn group, one executor dispatch batch.
- A typed-confirmation item must never participate in a batch.
- New groupers must be structural selectors, not timers; the runtime must never delay approval emission to collect future items.
### 5.6 Boundary

## 6. Touched-Resource Matching Against Lease Scope {policy.touched-resource-matching-against-lease-scope}
### 6.1 Definition
### 6.2 Resolution
### 6.3 Containment
- Containment checked per resource class: `filesystem`, `network`, `process`, `env`, `setting`, `credential`, `model-call`, `browser-session`, `ui-element`, `sub-agent`, `scheduler`, registered extension classes.
- A lease applies only when every resolved touched resource is contained within the lease's constraints for its class.
### 6.4 Lease Selection on Multiple Matches
1. Narrower scope wins. Ordering: `single_proposal < run < intent_thread < task < conversation < workspace < global < reusable_policy_rule`.
2. Among same-scope, `AlwaysDeny` wins over `AlwaysAllow`.
3. Among same-scope same-decision, most-recently-granted wins.
### 6.5 No-Match Fallthrough
### 6.6 Boundary

## 7. Permission Floor and Typed-Confirmation {policy.permission-floor-typed-confirmation}
### 7.1 Permission Floor {policy.permission-floor}
- Floor never lowers — settings, leases, trust upgrades, `agent.unrestricted_mode`, cross-scope overrides cannot lower it; any attempt produces `PolicyFloorViolated` and the floor wins.
### 7.2 Definition of Typed-Confirmation
- Requires the user to type an exact confirmation string before proceeding.
### 7.3 Properties
- Typed-confirmation always asks; never participates in batched approval; never fast-paths through `auto-decide`; emits a single-proposal policy event (no `AlwaysAllow` lease grantable).
### 7.4 The `Denied` Carve-Out {policy.denied-carve-out}
- Only path through `Denied` is the typed-confirmation override (`denied_override_via_typed_confirmation: Required`); single-proposal scope; no `AlwaysAllow` lease creatable.
### 7.5 Examples
### 7.6 Boundary
- On mismatch → `TypedConfirmationMismatch`; flow returns to ask again or cancel.

## 8. Auto-Decide Mode {policy.auto-decide-mode}
### 8.1 Definition
- Opt-in per capability or family; never the default.
### 8.2 Configuration
- Carries: `enabled`, `classifier_model_id`, `policy_model_request_template_id`, `confidence_threshold`, `consecutive_denial_fallback`, `consecutive_approval_check_in`, `escalation_path`.
### 8.3 Flow
1. Construct a classifier model request.
2. Classifier invoked as a policy-internal model step; must not emit a nested `ToolCallProposed`, cannot call tools, cannot recursively ask for approval.
3. Returns `ClassifierResult { decision, confidence, reasoning }`.
4. If `confidence >= confidence_threshold` and `Allow`/`Deny`, honored; emit `AutoDecideClassification` + `Continue`/`Block`.
5. If below threshold or `Ask`/`Escalate`, fall through per `escalation_path`.
6. Apply consecutive-denial-fallback + consecutive-approval-check-in counters; on threshold fall through to ask-user.
7. Classifier result always recorded on the invocation record.
### 8.4 Properties
- Classifier never lifts `permission_floor`, never bypasses `Denied`, never lifts `typed-confirmation`.
### 8.5 Boundary

## 9. The Source-Approval Flow {policy.source-approval-flow}
### 9.1 Definition
- Surfaces declared metadata before capabilities become invocable.
### 9.2 Trigger Threshold
### 9.3 Proposal Preview
- A `SourceRegistrationProposal` carries source identity (`Plugin`, `McpServer`, `Api`, `UserDefined`, `Subsystem`), declared capabilities, source risk summary, registered-entry trust state, backend kind summary, policy extension summary, optional linkage.
### 9.4 User Options
- Accept declared defaults; Customize per capability; Customize per source; Deny outright; `DeferSourcePolicy` (`ask_each_time`, `require_explicit_approval`, `ask_on_first_use`); `CancelRegistration`.
### 9.5 Persistence
### 9.6 Trust Mapping Defaults {policy.trust-mapping-defaults}
- `Verified`/`System` register at declared tiers; `Community` at `WorkspaceWrite` or below → effective `UserApproval`; `Unverified`/`Sideloaded` at `WorkspaceWrite` or below → `UserApproval` + per-call ask-user, at `UserApproval` or above → typed-confirmation on first use.
### 9.7 Properties
- Must never silently register an invocable source.
### 9.8 Boundary

## 10. Mid-Execution Policy Re-Evaluation {policy.mid-execution-policy-re-evaluation}
### 10.1 Lease Lifecycle States
- `Active`, `Stale`, `Revoked`.
### 10.2 Revocation Conditions
- Required canonical conditions: `workspace_switch`, `policy_change`, `grant_evidence_unavailable`, `capability_unregistration`, `trust_downgrade`, `expiry_deadline`, `manual`.
- Any condition not evaluable declaratively against typed state is rejected (ad-hoc procedural revocation is an Explicit Rejection).
### 10.3 Re-Evaluation Triggers
- Re-evaluation must be bounded — only for leases whose `revocation_conditions` could be affected.
- Ordinary context compaction must not stale a lease.
### 10.4 Stale Lease Handling
- On transition to `Stale`: `LeaseStale` emitted; next invocation produces ask-user with staleness reason; the lease must not be silently revoked.
### 10.5 Boundary
- Re-evaluation must be event-driven; the policy layer must not poll.

## 11. The `Lease` Primitive {policy.lease-primitive}
### 11.1 Definition
- Every persisted approval decision must be a `Lease`.
### 11.2 Required Fields
`lease_id`, `capability_match`, `scope`, `invoker_kind`, `invoker_context`, `decision`, `inherited_constraints`, `grant_reason`, `grant_context`, `granted_at`, `granted_by`, `expires_at`, `revocation_conditions`, `status`.
- `scope` one of: `single_proposal`, `run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule`.
- `invoker_kind` one of: `user_direct`, `model_agent`, `automation`, `scheduled_trigger`, `plugin_runtime`, `mcp_external`, `subagent`, `system_internal`.
- `decision` one of: `AlwaysAllow`, `NarrowedAllow { constraints }`, `AlwaysDeny`.
- `grant_origin` one of: `user_response_to_ask`, `source_approval_flow`, `automation_rule`, `built_in_template`, `policy_template_definition`.
- A lease lacking any required field is invalid+rejected at grant time.
### 11.3 Scope Semantics (8 scopes)
- `single_proposal` — never persisted as a `Lease`.
- `run` — revoked when run completes/fails/cancelled.
- `intent_thread` — revoked when it closes/superseded/manually revoked.
- `task` — revoked when task completes/fails/cancelled.
- `conversation` — revoked when archived/deleted/explicitly closed.
- `workspace` — revoked when workspace removed or manually revoked.
- `global` — across all workspaces/conversations/runs/tasks for the active user.
- `reusable_policy_rule` — pattern-based; canonical shape for built-in safety rules + user-authored policy templates expressed as leases.
### 11.4 Composition
- One lease applies per call, or none; leases never compose by averaging/majority.
### 11.5 Built-In Reusable Policy Rules {policy.built-in-reusable-policy-rules}
- `git.push --force` to a protected-branch-list branch → `AlwaysDeny` with typed-confirmation override.
- `system.shutdown` by an agent → `AlwaysDeny` with typed-confirmation override.
- `account.delete` by an agent → `AlwaysDeny` with typed-confirmation override.
- `credential.export` to any external destination → `AlwaysDeny` with typed-confirmation override.
- shell commands matching the dangerous-pattern set → `AlwaysDeny` with typed-confirmation override.
- `shell.exec` with a registered dedicated capability → `RedirectSuggestion` (`Strict`/`Warn`/`Off` modes).
- `shell.exec` network-fetch after a recent `web.fetch` denial → `AlwaysDeny` (`Forbidden`) / `UserConfirmed` / `Allowed`.
- Disabling/widening a rule protecting an irreversible op is itself a typed-confirmation flow.
### 11.6 Persistence {policy.persistence}
- Leases must be durable and survive process restarts; events are source of truth, the lease is the projection.
- Canonical default is indefinite retention, not fixed expiry.
### 11.7 Boundary

## 12. Approval-Policy Templates {policy.approval-policy-templates}
### 12.1 Definition
### 12.2 Required Properties
`template_id`, `display_name`, `description`, `short_description`, `family_applicability`, `scope_applicability`, `validators`, `typed_confirmation_required`, `denied_override_via_typed_confirmation`, `confirmation_string_pattern`, `approval_text_template`, `source` (`Builtin`, `Subsystem { id }`, `Plugin { id, version }`, `UserDefined { scope }`).
### 12.3 Validator Verdicts
- A validator produces one of: `Allow`, `Deny`, `Ask`, `Escalate`, `NoOpinion`.
- Aggregation severity: `Deny > Escalate > Ask > Allow > NoOpinion`.
- No non-system-source validator may declare itself terminal.
### 12.4 Built-In Templates
- Per-tier: `tier_default_readonly`, `tier_default_workspace_write`, `tier_default_user_approval`, `tier_default_unrestricted`, `tier_default_denied`.
- Per-class: `class_internal_analysis_default`, `class_action_external_default`, `class_user_artifact_default`.
- Behavioral: `clarify_first_for_multistep`, `todos_for_multistep`, `prefer_dedicated_tools`, `fetch_fallback_ban`.
- Safety: `git_protected_branch_force_push_denied`, `irreversible_op_typed_confirmation`, `dangerous_command_typed_confirmation`, `secret_export_denied`.
- Subsystem- and surface-default templates.
### 12.5 User-Authored Templates
- May not override floor-enforcement; attempting `Allow` for a `Denied`-floor capability produces `PolicyFloorViolated`, floor wins.
### 12.6 Composition
- Evaluator runs capability default first, scope-level overrides second, reusable-policy-rule leases last.
### 12.7 Boundary

## 13. Approval UI Surface Contract {policy.approval-ui-surface-contract}
### 13.1 Definition
- A data contract, not a UI spec.
### 13.2 `ApprovalRequest`
Fields: `request_id`, `flow_kind` (`ask_user`, `typed_confirmation`, `lease_grant_proposal`, `lease_stale_re_grant`, `contradiction_resolution`, `source_registration`), `invoker_kind`, `invoker_context`, `capability_id`, `capability_version`, `capability_display_name`, `capability_description`, `capability_short_description`, `capability_family`, `resolved_args`, `reason`, `resolved_tier`, `permission_floor`, `resolved_touched_resources`, `data_sensitivity`, `trust_state`, `available_options`, `classifier_result`, resolved proposal facts (`side_effect_class`, `reversibility_class`, `replay_class`, `postconditions`, `required_observations`, `expected_artifacts_or_outputs`), synthesized facts (`preview_payload`, `data_egress_summary`, `sandbox_or_isolation_summary`, `rollback_or_compensation_note`), `batch_id`, `contradictions_detected`, `lease_staleness`, `approval_text`, `confirmation_string_pattern`.
### 13.3 `LeaseOption` (16 kinds)
- `kind` one of: `AllowOnce`, `AllowForRun`, `AllowForIntentThread`, `AllowForTask`, `AllowForConversation`, `AllowForWorkspace`, `AllowGlobal`, `AlwaysAllowReusableRule`, `DenyOnce`, `DenyForRun`, `DenyForIntentThread`, `DenyForTask`, `DenyForConversation`, `DenyForWorkspace`, `DenyGlobal`, `AlwaysDenyReusableRule`.
- Each declares: `kind`, `scope_label`, `scope_description`, `default_constraints`, `user_customizable_constraints`, `typed_confirmation_required`.
- Options that would violate floor or pierce a deny lease must be excluded.
### 13.4 `ApprovalResponse`
- Fields: `request_id`, `choice` (a `LeaseOption` kind or `Cancel`), `customized_constraints`, `typed_confirmation_string`, `reason`.
### 13.5 `BatchApprovalRequest`
- Fields: `batch_id`, `items`, `batch_options` (`ApproveAll`, `DenyAll`, `PerItem`), `scope_summary`.
### 13.6 `ContradictionResolutionRequest`
- Fields: `request_id`, `contradictions`, `resolution_options`.
### 13.7 Required Surface Properties
- Any presentation surface must present `approval_text`, `resolved_args` (with redactions), `reason`, `resolved_tier`, `permission_floor`; present every `available_option`; validate the typed string against `confirmation_string_pattern` before submission; emit the `ApprovalResponse` through the bus; support keyboard navigation, voice control, screen-reader operation.
### 13.8 Boundary
- Policy layer must never invoke UI methods directly; it emits typed events.

## 14. Contradiction-Checking Across Scope Levels {policy.contradiction-checking-across-scope-levels}
### 14.1 Definition
### 14.2 Resolution Rules
- Tighter-narrower-deny wins (not a contradiction).
- Tighter-narrower-allow under broader-deny is a contradiction → emit `PolicyContradictionDetected` → route to resolution flow; runtime never silently weakens the broader deny.
- Floor never participates → `PolicyFloorViolated`, floor wins.
- Typed-confirmation never lifts → `TypedConfirmationCannotBeLifted`.
- Reusable-policy-rule leases compose with same precedence.
### 14.3 Detection Timing
- at lease grant time; at policy evaluation time; at re-evaluation time.
### 14.4 Resolution Outcomes
- Resolution persisted as `PolicyContradictionResolved`.
### 14.5 Boundary

## 15. Risk Classification and Trust Interaction {policy.risk-classification-trust-interaction}
### 15.1 Three-Class Capability Taxonomy (CT.20)
- `InternalAnalysis` — default tier `ReadOnly`.
- `ActionExternal` — default tier `UserApproval`.
- `UserArtifact` — default tier `WorkspaceWrite`.
### 15.2 Trust Interaction
### 15.3 Risk Classification of Unknown Capabilities
- A capability whose class is `Unknown` is treated as `ActionExternal` for trust escalation.
### 15.4 Per-Call Model-Mediated Risk Classification
### 15.5 Boundary

## 16. Settings Resolution for Policy {policy.settings-resolution-for-policy}
### 16.1 Configurable Dimensions and Layer Ownership
- Approval-posture preset: `Strict`, `Balanced`, `Permissive`, plus user-authored profiles.
- Dedicated-tool preference mode: `Strict`, `Warn`, `Off`.
- Fetch-fallback policy: `Forbidden`, `UserConfirmed`, `Allowed`.
- `DeferSourcePolicy` fallback: `ask_each_time`, `require_explicit_approval`, `ask_on_first_use`.
### 16.2 Resolution Algorithm
- Policy reads through File 15's source stack: invocation overlay, conversation, workspace, global, local explicit overlay, active profile layers, then definition default.
- Changing posture must not reset prior per-capability customizations.
### 16.3 Approval-Posture Presets
- `Strict` — every `UserApproval` produces ask-user; `auto-decide` off; typed-confirmation triggers more aggressively; dedicated-tool `Strict`; fetch-fallback `Forbidden`.
- `Balanced` — per-capability defaults apply; `auto-decide` opt-in; dedicated-tool `Strict`; fetch-fallback `Forbidden`; batched approval enabled.
- `Permissive` — `auto-decide` on for `ReadOnly` + contained `WorkspaceWrite`; dedicated-tool `Warn`; fetch-fallback `UserConfirmed`.
### 16.4 Agent Exposure of Policy Settings {policy.agent-exposure-policy-settings}
- approval-posture preset, `effective_trust` per source, per-capability tier overrides — `OnRequest`.
- typed-confirmation strings, lease grant contexts, source-approval proposals — `Hidden`.
- active approval-posture preset — `InModelRequest`.
### 16.5 Boundary

## 17. Explicit Rejections {policy.explicit-rejections}
- a parallel approval pipeline beside the canonical hook bus
- per-capability custom approval logic in capability handlers
- silent approval (every direct-execution path must emit `PolicyDecisionMade`)
- silent denial (a denied call must produce a typed `PermissionDenied`-class result block in-band + `PolicyDecisionMade`)
- silent contradiction resolution
- floor-piercing (`PolicyFloorViolated` records any attempt, floor wins)
- bypassing typed-confirmation
- model-mediated approval as the silent default
- recursive policy approval
- collapsing invoker classes
- untrusted inspectors silently allowing/rewriting policy outcomes
- silent semantic substitution
- ad-hoc procedural revocation conditions
- registering a lease whose `capability_match` references a missing/unregistered capability
- treating trust state as a declaration
- a single global approval policy overriding per-capability templates+per-scope overrides
- routing approval decisions through unrelated services/sidecars
- requiring the user to type a confirmation string without disclosing it
- silently auto-approving a typed-confirmation override
- producing approval decisions other than `Continue`, `Substitute`, `Block`, `RedirectSuggestion`
- approval flows depending on time-based polling
- hardcoded numeric policy defaults in this canonical layer
- registering policy-evaluation logic in capability handlers/palette wrappers/voice resolvers/UI surfaces
- preserving any earlier name for the same primitive as a parallel system

## 18. Consequences for Later Specs {policy.consequences-for-later-specs}
- read approval decisions through the typed event-bus contract; never invent a parallel approval mechanism.
- read effective tiers, lease state, contradiction state through the policy layer's read interface.
- record per-call resolved facts on the `CapabilityInvocation` record + policy events; never on the declaration/registered entry.
- treat `Lease` as the durable approval primitive.
- treat `Approval-Policy Template` as the canonical reusable rule set.
- treat `Source-Approval Flow` as the canonical capability-source onboarding mechanism.
- honor the four canonical approval flows as the closed set.
- honor the four direct-execution conditions as the closed set.
- honor floor enforcement; honor typed-confirmation as the only path through `Denied`; honor the contradiction-detection rule; honor the trust-driven narrowing rule.
- emit policy events through the canonical event bus with the standard envelope; the ledger is source of truth.
- consume the source-trust state from the registered entry.
- consume the canonical `capability_class` taxonomy (`InternalAnalysis`, `ActionExternal`, `UserArtifact`, `Unknown`).
- consume the canonical revocation conditions + re-evaluation triggers.
- consume the canonical `ApprovalRequest` / `LeaseOption` / `ApprovalResponse` / `BatchApprovalRequest` / `ContradictionResolutionRequest` data contract.
