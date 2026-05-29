# Execution and Run Model — Operative Core

## 1. Chosen Model `run.chosen-model`

## 2. Run `run.run`
### 2.2 Required Attachments
- Every run MUST attach to: one conversation; one primary intent thread; one trigger; one route result or equivalent non-conversation trigger decision.
### 2.3 Trigger Kinds
- user request; retry; edited request reroute; continuation; child run; automation; external event; user-invoked action.
### 2.4 Run Status
- `pending`, `running`, `awaiting_user`, `paused`, `cancelling`, `cancelled`, `failed`, `completed`, `superseded`.
- Status changes MUST be ledgered.
### 2.5 Ownership
- Primary conversation, primary intent thread, trigger MUST NOT change during the run.
### 2.6 Minimum Durable Reconstruction `run.minimum-durable-reconstruction`
- A run record MUST preserve enough to reconstruct: stable run identity; conversation/intent thread/task/parent/child relationships; trigger and route linkage; status, stop reason, ordering of creation+completion; policy/capability/model/settings/world-state snapshot references; produced output references; approval/denial/lease/interruption/reroute/cancellation facts; `control` (default `Assistant`, set `User` on takeover with takeover actions recorded as first-class blocks).
- Run record MUST also preserve its `RunCompletionContract` and the contract's authorized revision history.
### 2.7 Run Completion Contract `run.completion-contract`
- Every run has a `RunCompletionContract` derived at creation; declares what the run MUST achieve to terminate as `completed`.
- Requirement kinds: plain-text response only; capability invocation; artifact commit; block commit; evidence or citation capture; validation result; approval or denial resolution; task-state update; external side-effect confirmation.
- Run MAY be marked `completed` only when every active requirement of its latest authorized contract is satisfied by ledgered facts/committed blocks/committed artifacts/recorded policy decisions.
- A contract is revised only through a ledgered `RunCompletionContractRevised` event.
- Removing/weakening/marking-no-longer-required a requirement REQUIRES authority at least as strong as the one that introduced it.
- The run's executing agent MUST NEVER remove/weaken its own completion requirements; may only add.
- User-introduced requirement removed/weakened only by explicit user action or user-authorized policy.
- Policy-introduced requirement requires policy approval; router-introduced requires reroute or route override.
- A non-monotonic revision REQUIRES explicit qualifying authority and records old/new contract, removed/weakened requirements, authority source, reason, approving actor/policy decision, ledger evidence.

## 3. From `RunIntent` to Run `run.from-run-intent-to-run`
- Handoff MUST preserve: triggering message; selected intent thread; attachment kind; primary + supporting surfaces; capability families; execution entry; model route; tool-surface strategy if present; fast-path results or failures; routing explanation; user overrides.
- The created run MUST include any router-performed capability call as an initial execution/preparation record.
- No fast-path result may be treated as invisible context.

## 4. Execution Entry `run.execution-entry`
- Entry types: `respond_inline`, `respond_with_tools`, `surface_runtime`, `multi_step_agent`.

## 5. Execution Structure `run.execution-structure`
### 5.2 Execution Unit
- Unit kinds: deterministic step; model step; model/tool loop iteration; capability proposal; capability execution; retrieval step; context compilation step; validation step; recovery step; user-ask step; artifact commit step; child run.
- Each unit MUST have: goal/purpose; inputs; outputs or explicit no-output result; status; owning run; ordering relationship; error state if any.
### 5.3 Structure Shapes `run.structure-shapes`

## 6. Lifecycle `run.lifecycle`
### 6.1 No Mandatory Phases
- A simple run MUST NOT pay phase machinery cost; a complex run MUST NOT be forced into a fixed phase sequence.

## 7. Model/Tool Loop `run.model-tool-loop`
### 7.2 Iteration `run.iteration`
### 7.3 Stop Conditions

## 8. Capability Execution `run.capability-execution`
### 8.1 Rule
- All side effects MUST pass through capability contracts + policy.
### 8.2 Call Pipeline `run.call-pipeline`
- Pipeline steps: resolve capability; validate input; produce proposal if mutating/policy-crossing; run validators + policy checks; determine denial/approval/persisted decision/active lease; execute with declared isolation + concurrency; stream partials when supported; record observations + result; validate postconditions when declared; commit or expose output.
- Every capability declares: `concurrency` (`ConcurrencySafe`, `SelfParallel`, `Exclusive`); `reversibility_class` (`none`, `compensable`, `reversible`); `idempotent`; `preview_mode` (`none`, `dry_run`, `structural_preview`, `diff_preview`); and `partial_output_meaningful`, `cooperative_stop_deadline_ms`, `sibling_abort_on_failure`, `resume_on_restart` where applicable.
- A state-changed mismatch returns a typed `StateChangedSinceObservation` error rather than silently overwriting.
### 8.3 Denial Is In-Band `run.denial-is-in-band`
- A denied capability call does NOT crash the run by default.

## 9. Tool Calls `run.tool-calls`
- Executor MUST support: native provider tool calls; parsed text-pattern tool calls; user-invoked actions; borrowed/deferred capability loading; partial tool blocks; failed tool results as first-class model context.
- The execution pipeline after parsing MUST NOT vary by provider.
- A capability handling input variants internally is the same capability with sub-modes, NOT a separate capability call.

## 10. Tool Surface `run.tool-surface`
### 10.2 Zones `run.zones`
- Zones: `primary`, `borrowable`, `deferred`.
- Users MUST be able to customize which tools/capability groups appear in each zone.
### 10.3 Routing Influence `run.routing-influence`
- Strategies: `use_current_surface_tools`, `borrow_foreign_capabilities`, `load_deferred_capabilities`.
- Mid-execution discovery/borrow capabilities: `tool.borrow`, `tool.search`, `mcp.search`.
- Capabilities outside the active surface/subsystem reachable only via `tool.search`/`tool.borrow`, never via silent autoload.
### 10.4 User Customization
- Tool-surface behavior MUST be deeply customizable via settings.
- Users MUST be able to inspect available tools grouped.
- System MUST NOT hardcode one tool-loading policy when users want a different one.

## 11. Approval During Execution `run.approval-during-execution`
- Permission tiers: `Denied`, `ReadOnly`, `WorkspaceWrite`, `UserApproval`, `Unrestricted`.
- `Denied` cannot be auto-approved by any lease; only path is `typed-confirmation` or equivalent policy override.
- Leases cannot escalate above the declared tier or below `Denied`.
- Approval behavior MUST support: immediate allow; immediate deny; ask user; typed-confirmation; persisted approval as a `Lease`; model-mediated `auto-decide`; policy-driven escalation; batched approval.
- Lease scopes: `single-proposal`, `run`, `intent-thread`, `task`, `conversation`, `workspace`, `global`, `reusable-policy-rule`.
- typed-confirmation NOT lifted by global trust toggles; always asks.
- System MUST support built-in approval policy templates + user-provided custom templates.
- Policy validation MUST reject contradictory combinations across scope levels rather than resolving silently.
- Model-mediated policy evaluation MUST NOT silently replace explicit user approval where policy still requires a human decision.

## 12. Streaming and Partial Execution `run.streaming-partial-execution`
- For file/artifact writes, partial rendering MUST preserve atomicity: validate target; write into temporary/staged materialization; commit only on full call completion + policy/postconditions; delete/orphan staged partials on cancellation.
- A durable mutation is accepted only at the capability's commit point.

## 13. Model Steps `run.model-steps`

## 14. Programmatic Execution `run.programmatic-execution`
- MUST still use the same run/ledger/capability/policy/artifact rules.

## 15. Parallelism `run.parallelism`
### 15.1 Rule
- Parallel units may run only when: capabilities compatible; mutable resource scopes don't conflict; policy leases allow it; outputs have a defined merge/comparison path; cancellation + failure behavior defined.
### 15.2 Tool-Level Concurrency
- Tags: `ConcurrencySafe`, `SelfParallel`, `Exclusive`.
- Default for newly declared capabilities = `Exclusive`.
- Backends/sessions/processes/external services MUST NOT be implicit single-instance locks.
- Executor MUST preserve stable result ordering even when work finishes out of order.
### 15.3 Failure in Parallel Work `run.failure-in-parallel-work`
- Parallel failure MUST preserve useful work unless policy requires immediate abort.
- `sibling_abort_on_failure: true` opt-in; per-call `depends_on` relationships.
- Silent absence is forbidden.
### 15.4 Mutation Rule `run.mutation-rule`
- Concurrent mutation of the same resource forbidden unless a capability explicitly owns a safe merge protocol.
- When safe merge unavailable, execution MUST choose one: serialize; isolate; ask for user direction; fail before mutation.
- Silent last-write-wins forbidden.

## 16. Child Runs and Multi-Agent Work `run.child-runs-multi-agent-work`
### 16.2 Isolation `run.isolation`
- Each child run MUST declare: parent run; purpose; allowed capability scope; context-sharing policy; output contract; merge target; cancellation relationship to parent; lifecycle visibility.
- Context sharing MUST be explicit; a child run does NOT receive unrestricted parent context by default.
- Isolation primitives: git worktrees; isolated browser profiles; sandboxed VM/virtual desktops; isolated process groups.
- The runtime MUST permit running without isolation when child runs share a workspace non-destructively.
### 16.3 Isolated and Inline Work
- Inline work MUST NOT bypass policy/ledgering/version boundaries.
### 16.4 Merge `run.merge`
- Child run outputs do NOT automatically mutate parent state; MUST return through: summary; artifact; patch; evidence set; validation report; proposed task update; proposed workflow step.

## 17. Interruption, Pause, Cancellation `run.interruption-pause-cancellation`
### 17.1 User Intervention `run.user-intervention`
- Intervention MUST be recorded.
- On takeover, subsequent user actions recorded as first-class blocks indistinguishable in the ledger from agent-produced blocks.
- No agent flow blocks on the post-takeover summary input.
### 17.2 Pause and Resume `run.pause-resume`
- A paused run MUST preserve enough state to resume safely or explain why it cannot.
- Resumption MUST revalidate: world state freshness; capability availability; policy leases; resource locks/scopes; model route validity; user-visible assumptions.
### 17.3 Cancellation `run.cancellation`
- MUST support both cooperative stop and forceful termination.
- Each active run MUST have a shared cancellation signal received by all listeners simultaneously.
- Listeners reporting completion after `cancelled` produce typed orphan-output ledger entries; outputs not committed.
- Capabilities MUST declare: whether cooperatively stoppable; whether forcefully killable; post-kill cleanup/rollback; residual partial side effects; cooperative-stop deadline; `partial_output_meaningful`; `resume_on_restart`.
- MUST escalate to forceful termination when immediate stop required or cooperative stop fails to complete promptly.
- Every cancellation path MUST carry a finite deadline; every override MUST remain finite; timeoutless operations not permitted.
- Cancel UI MUST offer: cancel run alone; cancel run + child-run tree; cancel a specific tool call; cancel a specific child run; cancel a specific sandbox/process.
- Every active long-running unit owned by the runtime MUST be wrappable into a cancel target and reliably cancellable.
- Non-killable execution: later specs MUST identify the limitation explicitly and define fallback control.
- Cancellation MUST record: requester; affected run + child runs; cleanup performed; cooperative/escalated/forceful; partial outputs retained or discarded; final status.
- Runs `running`/`cancelling` at process restart become `failed` with typed reason `process_restart_orphan` by default unless `resume_on_restart: true`.
- Resume handler MUST revalidate world state, re-acquire leases, and either continue or transition to `failed`.
- Runtime MUST NOT auto-resume orphaned runs at startup; user MUST be able to retry/resume any one on demand.
- Failed-on-restart runs MUST be surfaced with a per-run resume-or-discard affordance.

## 18. Task Promotion and Task Updates `run.task-promotion-task-updates`
- Task updates MUST be revision-safe.

## 19. Retry, Reroute, Branch `run.retry-reroute-branch`
- Retry/reroute/branch MUST NOT interfere with a prior in-flight run.
### 19.1 Retry `run.retry`
- A retry MUST NOT mutate the historical ledger of the prior run.
### 19.2 Reroute `run.reroute`
- If accepted, execution MUST choose one: suspend and hand off; create child/continuation run; branch; supersede current run.
- New run does NOT inherit in-flight context state implicitly.
### 19.3 Branch `run.branch`

## 20. Error Handling, Recovery, Stuck Detection `run.error-handling`
### 20.1 Boundary Rule `run.boundary-rule`
- Capability failures produce typed result objects whenever the run can continue.
- Budget exhaustion preserves partial outputs.
### 20.2 Recovery `run.recovery`
- Required strategies: retry same unit with corrected input; expose error to model; switch model profile; switch capability implementation; narrow capability scope; revoke stale leases + reacquire with narrower scope; request user clarification; branch strategy; restore or propose rollback; stop with typed failure.
### 20.3 Stuck Detection `run.stuck-detection`
- Runtime MUST detect: repeated identical tool calls; repeated failed validations; repeated provider/tool errors; no new durable output after iteration limits; cyclic child waiting; ping-pong patterns.
- Stuck detection MUST escalate in-band before hard-stopping: warning → structured directive → hard stop.

## 21. Budgets and Limits `run.budgets-limits`
- Runs MUST support configurable budgets: max model steps; max tool/capability calls; max child-run depth; max concurrent units; context budget; output budget; provider budget; artifact/resource budget.
- Elapsed-time guards MUST be configurable and used only as external-process safety guards.
- The runtime MUST NOT silently impose hidden budget limits.
- Budget warning MUST be visible to the model/programmatic executor before wrap-up is expected.

## 22. Termination `run.termination`
- A successful completion REQUIRES accepted output + satisfaction of every active requirement of the latest authorized `RunCompletionContract`.
- A run with no recorded capability executions, no committed artifact revisions, and no model-step outputs beyond plain text MUST NOT terminate as `completed` if its contract required action (forgery guard).
- Completion verifies against the latest authorized contract revision.

## 23. Ledger, Events, Commits `run.ledger-events-commits`
### 23.1 Execution Ledger `run.execution-ledger`
- Ledger records: run creation + status changes; route attachment; execution unit starts/finishes; capability proposals; approvals/denials/leases/policy decisions; model calls (provider, model id, role, input/completion/cache-creation/cache-read tokens, cost estimate computed from per-model pricing — never unkeyed scalar); tool calls + results; observations; validation results; errors + recovery decisions; produced outputs; child run relationships; cancellation + intervention.
- Ledger MUST record full-granularity timestamps on every entry.
- The ledger enforces a forgery guard at status transition (`running → completed` rejected without recorded action when contract required action).
### 23.2 Event Stream `run.event-stream`
- Every event carries the File 10 envelope: `conversation_id` when conversation-scoped; `context_refs` (`run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`); `sequence_scope`; `sequence`; `timestamp`; `sensitivity` (`Public`/`Sensitive`/`Secret`, default `Public`).
- Consequential events MUST also be represented in the ledger.
- Raw `Secret` payloads in flight MUST never be persisted to the durable ledger.
### 23.3 Hook Integration `run.hook-integration`
- Blocking hooks return one of four typed decisions: `Continue`, `Substitute { new_payload }`, `Block { reason }`, `RedirectSuggestion { tool_id, args, reason }`.
- Each blocking hook declares `priority: i16` (lower runs first).
- Non-blocking hooks MUST NOT control execution flow.
- Quality control validators, logging, plugin/user hooks, policy gates, completion-verification MUST NOT create a second hidden execution path.
- Fail-direction: security-category hooks fail closed by default; non-security observer/enricher/formatter fail open with warning; non-security hooks that can allow/substitute a consequential pre-action proposal fail closed unless overridden; security-category hooks require typed confirmation before failing open.
### 23.4 Version Commits `run.version-commits`
- The accepted boundary commits the pending-operations buffer as one durable net change.

## 24. Output Semantics `run.output-semantics`
- Run outputs: conversation messages; blocks; artifact versions; file materializations; patches; claims; evidence links; memory proposals; task revisions; workflow candidates; validation reports; execution summaries.

## 25. Presentation `run.presentation`
- UI MUST be able to show: current run status; active execution unit; pending approvals/questions; selected model route when relevant; capability calls + results; child runs; produced artifacts; failure + recovery path.

## 26. Automation and Reuse `run.automation-reuse`
- Promotion to automation MUST preserve: trigger shape; required inputs; capability scope; policy requirements; validation requirements; output contract; failure handling.

## 27. Settings `run.settings`
- Execution behavior MUST be configurable.
- Settings MUST NOT become hidden hardcoded branches.

## 28. Explicit Rejections `run.explicit-rejections`
- Conversation message generation as whole execution model.
- Every request a heavy task graph.
- Linear agent loop as universal core architecture.
- Planning as mandatory phase.
- Side effects outside capability and policy flow.
- Background work as separate execution architecture.
- Child agents mutating parent state directly.
- Silent last-write-wins for concurrent mutations.
- Fast-path work recorded only as hidden router context.
- Live events as durable execution truth.
- Frontend participation style as backend execution mode.
- Task promotion by hidden router/execution heuristic.
- Automatic merge of parallel outputs without explicit merge path.
- Automatic compaction as execution-layer side effect.
- Provider retry/failover inside the execution layer.
- Hardcoding one tool-loading policy with no override.
- Hardcoding one approval-policy mode/template with no override.
- Hardcoding retry/loop/budget/stuck thresholds outside settings.
- Locking parallel runs/calls against same backend/session/sandbox/service to single-instance.
- `completed` status without recorded execution evidence when contract required action.
- Input-variant sub-handling as separate capability call.
- Silently auto-resuming orphaned in-flight runs at restart.
- Enforcing budgets by default.
- Imposing model-mediated checks where deterministic floor sufficient; silently relying on deterministic where user configured semantic verification.
