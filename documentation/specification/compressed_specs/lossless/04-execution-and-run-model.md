> Lossless render of canonical/04-execution-and-run-model.md — original 72887 chars

# Execution and Run Model

Status: Canonical.

## Scope
- Defines: `Run` as durable execution attempt; execution entry from `RunIntent`; execution lifecycle/structure; model/programmatic/workflow/surface-runtime/multi-agent execution shapes; capability/tool execution semantics; tool-surface management; approval/denial handling during execution; parallelism and child runs; task promotion and updates during execution; mid-execution reroute mechanics; interruption/cancellation/retry/recovery; budgets/ledger/events/outputs/version-commit boundaries.
- Does NOT define: full task schema; full capability contract schema; policy/approval UI; exact tool schemas; context assembly algorithm; compaction policy; provider failover internals; storage schema; model/provider registry schema; subsystem-/surface-specific tool catalogs; frontend layout behavior.

## Source Resolution
- Resolves how a `RunIntent` becomes durable execution.
- A run owns status, ledger linkage, budgets, cancellation, completion semantics.
- Model/tool loop = default shape for ordinary agentic work, not the universal core architecture.
- Programmatic execution, workflows, multi-agent, automation reuse the same run/ledger/capability/policy/versioning substrate.
- Parallel execution requires explicit ownership/isolation/merge/conflict handling; silent shared mutation forbidden.
- Planning/validation/reroute/task promotion are tool-visible execution behavior, not mandatory global phases.
- Every run + connected process MUST be cancellable as a group and killable individually at safe runtime boundaries.

## 1. Chosen Model `run.chosen-model`
- Defines what happens after routing produces a `RunIntent`. Execution consumes routing, context assembly, model strategy, capability registry, capability policy, blocks, artifacts, versioning, settings, typed errors; it does not replace them. Responsibility: create/resume the run, orchestrate, record, expose live state, commit accepted outputs through correct durable primitives.
- `Run` = durable record of one bounded attempt to progress work (simple conversation, tool work, workflow, surface runtime, or coordinating child runs).
- Chosen model: routing produces `RunIntent` → execution creates/resumes a `Run` → run executes a structured set of steps → every consequential action passes through capability contracts + policy → outputs become messages/blocks/artifacts/claims/memory proposals/task updates/workflow candidates → execution ledger records what happened → event stream projects live state to UI + hooks.

## 2. Run `run.run`
### 2.1 Definition
- `Run` = durable execution attempt. NOT: a message, task, conversation, frontend mode, raw tool call, raw model response, or a DAG by definition. May attach to all of them.

### 2.2 Required Attachments
- Every run MUST attach to: one conversation; one primary intent thread; one trigger; one route result or equivalent non-conversation trigger decision.
- MAY also attach to: a task; parent run; child runs; produced artifacts; evidence and claims; approvals and leases; workspace or world state snapshots.

### 2.3 Trigger Kinds (all use the same run model; background execution is not a separate architecture)
- user request; retry; edited request reroute; continuation; child run; automation; external event; user-invoked action.

### 2.4 Run Status (changes MUST be ledgered)
- `pending`: created but not started.
- `running`: actively executing.
- `awaiting_user`: waiting for approval/clarification/intervention.
- `paused`: intentionally suspended and resumable.
- `cancelling`: cancellation requested but cleanup not complete.
- `cancelled`: stopped by user/policy before completion.
- `failed`: ended without satisfying the execution contract.
- `completed`: ended with accepted outputs.
- `superseded`: replaced by edit/reroute/retry/branch.

### 2.5 Ownership
- Set at creation. Primary conversation, primary intent thread, trigger do not change during the run. Different work line/route → create a child/continuation/branch/superseding run rather than mutating ownership in place.

### 2.6 Minimum Durable Reconstruction `run.minimum-durable-reconstruction`
- A run record MUST preserve enough to reconstruct: stable run identity; conversation/intent thread/task/parent/child relationships; trigger and route linkage; status, stop reason, ordering of creation+completion; policy/capability/model/settings/world-state snapshot references used; produced output references; approval/denial/lease/interruption/reroute/cancellation facts; `control` of the run (default `Assistant`; set to `User` during explicit user takeover, with user's takeover actions recorded as first-class blocks attached to the run).
- Run `control` answers "who is producing the run's next blocks"; orthogonal to task ownership (ownership = responsible work-line owner at task level; control = present driver at run level). Control is NOT a gate on the user: user may act through any external surface (own editor/terminal/browser) at any time without first taking control; field tracks what the system knows is producing observable blocks, not what the user is permitted to do.
- Run record MUST also preserve its `RunCompletionContract` and the contract's authorized revision history (§2.7). Exact storage fields belong in the storage spec; this file requires reconstructability, not a DB schema.

### 2.7 Run Completion Contract `run.completion-contract`
- Every run has a `RunCompletionContract`, derived at creation from its `RunIntent` (§3) + requirements declared by capabilities/validators/policy in scope. Declares what the run MUST achieve to terminate as `completed`. Each requirement records what satisfies it and the authority that introduced it.
- Requirement kinds: plain-text response only; capability invocation; artifact commit; block commit; evidence or citation capture; validation result; approval or denial resolution; task-state update; external side-effect confirmation.
- Completion rule: run MAY be marked `completed` only when every active requirement of its latest authorized contract is satisfied by ledgered facts/committed blocks/committed artifacts/recorded policy decisions. A fluent assistant response satisfies only a plain-text-only contract; never one requiring artifact mutation/validation/approval/evidence capture. Enforced by §22 forgery guard and [`ledger.forgery-guards`] (File 10 §3.7).
- Revision authority: a contract is revised only through a ledgered `RunCompletionContractRevised` event ([`ledger.entry-kind-catalogue`], File 10 §4.1). Authority-gated:
  - Requirements MAY be added by reroute, policy escalation, validation, or explicit execution update.
  - Removing/weakening/marking-no-longer-required a requirement requires an authority at least as strong as the one that introduced it.
  - The run's executing agent may NEVER remove/weaken its own completion requirements; may only add.
  - User-introduced requirement removed/weakened only by explicit user action or equivalently user-authorized policy.
  - Policy-introduced requirement requires policy approval.
  - Router-introduced requirement requires a reroute or route override.
- Monotonicity: by default revisions are monotonic (add/narrow/clarify, never remove/weaken). A non-monotonic revision (any removal/weakening) requires explicit qualifying authority and records old contract, new contract, removed/weakened requirements, authority source, reason, approving actor/policy decision, ledger evidence. A non-monotonic revision is itself subject to the forgery guard: unauthorized weakening is rejected at the ledger boundary exactly as a forged completion ([`ledger.forgery-guards`], File 10 §3.7). Completion always verifies against the latest authorized contract, so weakening relocates nothing past the guard.

## 3. From `RunIntent` to Run `run.from-run-intent-to-run`
- Handoff MUST preserve: triggering message; selected intent thread; attachment kind; primary + supporting surfaces; capability families; execution entry; model route; tool-surface strategy if present; fast-path results or failures; routing explanation; user overrides.
- Fast-path work belongs to the run record. If the router performed a capability call before downstream execution, the created run MUST include that work as an initial execution record or attached preparation record. No fast-path result may be treated as invisible context.

## 4. Execution Entry `run.execution-entry`
- `RunIntent.execution_entry` selects the initial execution shape; does not create a separate backend architecture.
- Entry types:
  - `respond_inline`: direct response, usually one model step or deterministic answer.
  - `respond_with_tools`: standard model/tool loop when tools may be useful.
  - `surface_runtime`: enter a surface-specific runtime while still using shared execution semantics.
  - `multi_step_agent`: persistent multi-step structure until completion/pause/failure/user intervention.
- All entries share: run lifecycle; ledger; event stream; capability policy; model strategy; context compilation; cancellation and retry semantics.

## 5. Execution Structure `run.execution-structure`
### 5.1 Principle
- A run has an execution structure (as small as one model response or a rich hierarchical graph of deterministic steps, model steps, capability calls, validations, child runs). Canonical requirement: NOT a specific graph schema — execution is decomposable, inspectable, resumable, safely parallelizable.

### 5.2 Execution Unit
- Any bounded part of a run trackable independently. Common kinds: deterministic step; model step; model/tool loop iteration; capability proposal; capability execution; retrieval step; context compilation step; validation step; recovery step; user-ask step; artifact commit step; child run.
- Each unit MUST have: goal/purpose; inputs; outputs or explicit no-output result; status; owning run; ordering relationship; error state if any.

### 5.3 Structure Shapes `run.structure-shapes`
- Allowed: inline response; model-with-tools loop; deterministic orchestration with model steps where needed; graph/workflow execution; surface runtime execution; multi-agent parent run with child runs; automation run using a saved execution template. These shapes share the same run lifecycle + ledger.

## 6. Lifecycle `run.lifecycle`
- Standard lifecycle: 1) create/resume run; 2) attach route/trigger/conversation/intent thread/optional task; 3) snapshot relevant world/settings/policy/capability/model state; 4) build minimal execution structure needed; 5) compile context/deterministic inputs for next schedulable units; 6) execute schedulable units subject to policy/capability/concurrency rules; 7) record observations/partials/outputs/errors/approvals/validations; 8) commit accepted outputs to durable objects; 9) update projections for UI/search/task state/artifacts/observability; 10) decide whether to continue/pause/ask/branch/retry/reroute/fail/complete.
- Planning is NOT a mandatory phase. Plans are artifacts/task updates/execution units only when they improve the work.

### 6.1 No Mandatory Phases
- No required planning/execution/verification/reflection phases. Those behaviors happen when useful, expressed as ordinary execution units/model steps/capability calls/task updates/artifacts/validation results. A simple run MUST NOT pay phase machinery cost; a complex run MUST NOT be forced into a fixed phase sequence.

## 7. Model/Tool Loop `run.model-tool-loop`
### 7.1 Role
- Default shape for ordinary agentic work; not the only execution shape.

### 7.2 Iteration `run.iteration`
- Logical iteration: 1) compile context for current run + execution unit; 2) call selected model with available tools + instructions; 3) parse output into typed response, tool calls, reasoning, partial blocks; 4) execute proposed tool calls through the capability pipeline; 5) return tool results/denials/failures/observations to model context; 6) stop if no more tool calls needed or a termination condition applies.
- Context compiled for each model iteration, not only at run start. The context compiler decides overflow handling; execution observes result and continues/pauses/recovers/fails per typed outcomes.
- Model output MAY stream through the event stream during generation. Streaming = live projection; accepted blocks/artifacts/commits still follow normal capability/ledger/version rules.

### 7.3 Stop Conditions
- A loop may stop when: no tool calls proposed; an explicit finish capability invoked; run cancelled; run paused or awaits user input; a configured budget reached; an unrecoverable typed error occurs; the run reroutes or is superseded.

## 8. Capability Execution `run.capability-execution`
### 8.1 Rule
- All side effects MUST pass through capability contracts + policy. Applies equally to: user-triggered actions; model-triggered tool calls; workflow nodes; child runs; automation runs; system actions.

### 8.2 Call Pipeline `run.call-pipeline`
- Logical pipeline: 1) resolve capability; 2) validate input; 3) produce proposal if action can mutate state or cross a policy boundary; 4) run validators + policy checks; 5) determine denial/approval need/persisted decision/active lease; 6) execute with declared isolation + concurrency semantics; 7) stream partials when supported; 8) record observations + result; 9) validate postconditions when declared; 10) commit or expose output per capability semantics.
- "Active lease" in step 5 = the `Lease` object of §11; pipeline consults active leases before falling back to ad-hoc approval.
- Every capability declares minimum execution-relevant metadata beyond input/output schemas:
  - `concurrency` (§15.2): one of `ConcurrencySafe`, `SelfParallel`, `Exclusive`.
  - `reversibility_class`: `none` (cannot be reversed), `compensable` (a paired/related capability undoes the effect — file edits reversed via version graph; staged commits reversed via `git restore`), or `reversible` (capability owns a symmetric reverse operation invokable directly).
  - `idempotent`: whether calling twice with same args has same observable effect as once. Independent of reversibility class — `set_value(key, x)` is idempotent regardless of `compensable`/`none`. Drives safe retry on unknown-outcome timeouts, coalescing of duplicate concurrent calls (§15.4), recovery strategy choice (§20).
  - `preview_mode`: `none`, `dry_run` (execute against simulated state, return typed result of what would happen — `--dry-run` shell commands, simulated package install, automation deploy plans), `structural_preview` (return structured description without executing — parsed AST of an edit, planned subprocess pipeline, planned API request), or `diff_preview` (return diff between current and post-execution state — file edits, DOM mutations, database row changes).
  - `partial_output_meaningful` (§17.3), `cooperative_stop_deadline_ms` (§17.3), `sibling_abort_on_failure` (§15.3), `resume_on_restart` (§17.3) where applicable.
- Declarations MAY be deterministic (author classifies once at registration) or model-mediated per call where deterministic classification is impossible. `shell.exec` cannot declare a single `reversibility_class` for all bash commands: runtime supports a model-mediated classification mode where a designated model classifies the specific call against the configured policy model-request template before the pipeline proceeds. Classification mode is a setting per capability or family, not hardcoded.
- A capability whose mutation depends on prior observation SHOULD validate observation currency before mutating: prior observation captures state-defining metadata (file mtime + content hash, DOM tree fingerprint, screen element id + bounds, browser session cookie state); the mutating call carries `expected_*` fields checked against current state; a mismatch returns a typed `StateChangedSinceObservation` error rather than silently overwriting. Agent loop receives the typed error in-band and may re-observe + retry, branch, or stop. Capability-author responsibility; executor enforces nothing additional.
- Exact contract fields + approval UI belong in later capability/policy specs.
- Blocking hooks + validators MAY participate at proposal, pre-execution, pre-commit boundaries; part of the shared event/capability system, not a separate execution pipeline.

### 8.3 Denial Is In-Band `run.denial-is-in-band`
- A denied capability call does NOT crash the run by default. Executor records a denial result linked to the proposal; model/programmatic executor sees the denial as normal execution input and may ask the user, choose a different path, narrow scope, or stop. Policy MAY still terminate the run immediately for high-risk cases.

## 9. Tool Calls `run.tool-calls`
- Tool calls = one form of capability invocation. Executor MUST support: native provider tool calls; parsed text-pattern tool calls when provider lacks native tools; user-invoked actions; borrowed/deferred capability loading; partial tool blocks; failed tool results as first-class model context.
- Response parser may vary by provider; the execution pipeline after parsing MUST NOT vary.
- A capability handling input variants internally (a file-read dispatching between text/binary paths based on resolved file kind) is the same capability with sub-modes, NOT a separate capability call. Variant handling, default-value selection, progressive-fallback all live inside the capability and pass through one validation, one approval, one ledger entry.
- Cross-capability composition happens at a higher layer: model may emit one or more direct tool calls, and programmatic execution (§14) may chain capability calls deterministically (output of one call as input to the next within a single execution unit) without forcing the model to emit each as a separate model turn.

## 10. Tool Surface `run.tool-surface`
### 10.1 Definition
- Each run has a tool surface: the capability subset visible to the executing model/programmatic unit. It's a model-request visibility + availability strategy, NOT a security boundary. Policy still governs every call.

### 10.2 Zones `run.zones`
- Three zones: `primary` (full schemas available immediately); `borrowable` (names + short descriptions visible; full schema loaded only after borrow); `deferred` (not visible until explicitly loaded by route, user setting, or capability discovery).
- Borrowed tools scoped to the current run turn or execution unit unless a later capability spec grants wider scope.
- Zone model defines execution semantics, not a fixed product policy. Users MUST be able to customize which tools/capability groups appear in each zone, including aggressive (always-loaded primary) and conservative (mostly-deferred) policies.

### 10.3 Routing Influence `run.routing-influence`
- If `RunIntent` includes a tool-surface strategy, execution respects it: `use_current_surface_tools` (standard primary surface); `borrow_foreign_capabilities` (expand borrowable set); `load_deferred_capabilities` (load specified deferred groups before execution). When absent, uses active surface defaults + settings.
- Routing is not the only entry point for capability loading. Deferred capabilities may be discovered + loaded mid-execution by the model via canonical built-in capabilities — `tool.borrow` (already-named borrowable tools whose schemas need loading), `tool.search` or `mcp.search` (discover deferred capabilities by name/family/description). Discovery + borrow are themselves capability calls passing the full pipeline (§8); newly loaded tools become part of the run's tool surface for the rest of the turn or for the duration of the granting lease, whichever is longer.
- Default surface composition follows active model's context budget: when all primary + borrowable tools fit, they may be fully loaded; under context pressure, runtime auto-shrinks to selective loading and surfaces the trade-off via settings UI (with concrete recommendations) rather than silently dropping tools. Surface runtimes load their surface-scoped tools by default within the surface; capabilities outside the active surface/subsystem are reachable only via `tool.search` or `tool.borrow`, never via silent autoload.

### 10.4 User Customization
- Tool-surface behavior MUST be deeply customizable via settings. Users MUST be able to inspect available tools grouped (by subsystem/surface/capability family/risk class/integration source/etc.); settings UI may present collapsible groups but canonical requirement is grouped inspectability + fine-grained control.
- Min configurable: whether broad families are primary/borrowable/deferred by default; whether individual tools are primary/borrowable/deferred/disabled from model-request exposure; whether all tools are always-loaded/selectively-loaded/on-demand; per-surface, per-profile, per-workspace, per-conversation, per-run overrides where meaningful; whether routing may expand/preload tools automatically; whether the model may borrow foreign tools automatically or only from explicitly allowed sets.
- Best default should remain disciplined + efficient, but the system MUST NOT hardcode one tool-loading policy when users want a different one.

## 11. Approval During Execution `run.approval-during-execution`
- Execution uses the shared capability policy system; no agent-specific approval mechanism.
- Capabilities declare a permission tier: canonical tiers `Denied`, `ReadOnly`, `WorkspaceWrite`, `UserApproval`, `Unrestricted`. `Denied` = cannot be auto-approved by any lease; only path is `typed-confirmation` (below) or an equivalent policy-defined override path. Tiers compose with leases: a lease can lower friction within a tier (a `UserApproval` capability with an `AlwaysAllow` lease for the granted scope runs without prompting) but cannot escalate above the declared tier or below `Denied`. Permission tier + reversibility class (§8.2) together drive the default approval policy template.
- Approval behavior MUST support:
  - immediate allow; immediate deny; ask user.
  - typed-confirmation: a variant of "ask user" requiring the user to type a specific confirmation string (action's identifier, exact path, branch name) before proceeding. For irreversible high-blast-radius operations (force push to a protected branch, account deletion, bulk filesystem delete). NOT lifted by global trust toggles; always asks.
  - persisted approval as a `Lease`: has scope, duration, revocation conditions, inherited constraints, recorded grant reason. A trivial persisted approval = degenerate lease (full-capability scope, indefinite duration, no constraints). Lease scope is one of: `single-proposal` (no lease created — one-shot decision recorded as policy event), `run`, `intent-thread`, `task`, `conversation`, `workspace`, `global`, or `reusable-policy-rule` (a user-authored approval template applied as policy). `conversation` is the canonical persisted scope name; legacy UI wording is not a separate stored scope. Inherited constraints may narrow a lease to a path subtree/host set/session set; revocation conditions may include manual revoke, workspace switch, policy change, or grant evidence becoming unavailable.
  - model-mediated policy evaluation, including the named `auto-decide` mode, where a designated model classifies each proposed call against a configured policy template and returns allow/deny/ask user/escalate.
  - policy-driven escalation.
  - batched approval for multiple pending calls.
- When several approval-required calls are pending in the same scope (same run, same child run, same simultaneously dispatched batch), policy layer presents them as one batch where possible. User can approve/deny each item independently or accept the batch whole. Subsequently dispatched calls in the same scope start a fresh batch; calls in different scopes batch separately.
- Persisted decisions are policy records, not hidden execution state.
- Model-mediated policy evaluation = policy layer may use a designated model to interpret a configured approval policy template and classify a proposed action as allow/deny/ask user/escalate. Still part of the shared system: model evaluates against policy/audit rules/configured constraints, not ad hoc.
- System MUST support built-in approval policy templates + user-provided custom templates. A template may define how the evaluator reasons about risk classes/touched resources/reversibility/scope/prior approvals/workspace boundaries/etc. Tier overrides, lease grants, modes, templates compose across the scope hierarchy (single-proposal, run, intent-thread, task, conversation, workspace, global, reusable-policy-rule). Policy validation MUST reject contradictory combinations across scope levels rather than resolving silently — e.g., a conversation-level deny under a global-level lease MUST surface as a contradiction, not a silent denial of the lease.
- Model-mediated policy evaluation MUST NOT silently replace explicit user approval where policy still requires a human decision; it decides how the policy should classify the proposal, not erase the system-approved vs user-approved distinction.

## 12. Streaming and Partial Execution `run.streaming-partial-execution`
- Execution MAY stream: model text deltas; reasoning summaries where allowed; tool-input streaming (model still emitting a tool call's structured arguments; UI may render live — `Reading src/index.ts...` while path arg still generating); tool-output partials (capability emitting partial results — streaming text, growing diff, growing file content); file/artifact previews; command output; validation progress; child-run progress.
- Tool-input streaming and tool-output partials commit at different boundaries: input stream commits when model finishes the call and executor enters the capability pipeline; output stream commits at the capability's declared commit point.
- Partial streaming = live projection. A durable mutation is accepted only at the capability's commit point.
- For file/artifact writes, partial rendering MUST preserve atomicity: validate target before writing; write into temporary/staged materialization; commit only when the full call completes and passes policy/postconditions; delete/orphan staged partials on cancellation per block/version rules.
- Capabilities whose input is itself a content payload (full-replace file create/edit, document generation) may support live partial-write: as the model emits input, capability writes incrementally into the staged temp file, user sees content appearing live in the destination pane, atomic rename only on call completion + policy + postconditions pass; cancellation deletes the staged file before any rename. Preserves end-to-end atomicity (no destructive change to live target until commit), gives immediate feedback, never leaks partial corruption regardless of where the call fails.

## 13. Model Steps `run.model-steps`
- Model steps are execution units, not the whole execution model. A model step may: produce final text; request tool calls; update/propose a plan; request clarification; request reroute; summarize state; validate/critique output; delegate to child runs when allowed.
- Runtime owns orchestration, policy, retries, concurrency, persistence, merge semantics. Models own semantic judgment, synthesis, open-ended planning, extraction, natural-language interaction.

## 14. Programmatic Execution `run.programmatic-execution`
- First-class. Means deterministic orchestration controls the run structure and calls model steps only where judgment/generation is needed.
- May yield: capability calls; child-run requests; model-step requests; validation requests; recovery requests; finish signals.
- Use for: known workflows; context pruning; batch retrieval/aggregation; validation chains; multi-agent coordination; repeated transformations; automation templates.
- MUST still use the same run/ledger/capability/policy/artifact rules.

## 15. Parallelism `run.parallelism`
### 15.1 Rule
- Allowed when ownership + merge semantics explicit. Parallel units may run only when: required capabilities compatible; mutable resource scopes don't conflict; policy leases allow it; outputs have a defined merge/comparison path; cancellation + failure behavior defined.

### 15.2 Tool-Level Concurrency
- Canonical concurrency tag: `ConcurrencySafe` (safe to run concurrently with any unrelated call); `SelfParallel` (safe to run multiple instances of the same capability concurrently, executor enforcing disjoint resource scopes); `Exclusive` (runs alone within its declared resource scope).
- Default for newly declared capabilities = `Exclusive`. Executor MUST detect when two `Exclusive` calls have disjoint resource scopes and is permitted to schedule them in parallel; the tag declares the pessimistic case, executor refines. Backends/sessions/processes/external services MUST NOT be implicit single-instance locks: parallel runs + parallel calls against the same provider are first-class and MUST be addressable via the event envelope (§23.2).
- Executor MUST preserve stable result ordering even when work finishes out of order.

### 15.3 Failure in Parallel Work `run.failure-in-parallel-work`
- Parallel failure MUST preserve useful work unless policy requires immediate abort. Default: in-flight sibling units continue running when one fails (results retained on completion); failed units produce typed error outputs; downstream units requiring failed outputs are skipped/blocked; retry can target failed units, failed + downstream, or whole structure.
- Capabilities can opt into sibling abort via `sibling_abort_on_failure: true`: executor cancels in-flight siblings on first failure within the same batch — for first-wins-races, best-of-N selectors with early termination, tightly coupled coordinated batches. Parallel batches may declare per-call `depends_on` relationships at dispatch time; when a dependency fails, dependents are skipped/blocked (matches downstream-on-failure rule). Both per-capability declaration + per-call dependency are user-customizable.
- Silent absence is forbidden.

### 15.4 Mutation Rule `run.mutation-rule`
- Concurrent mutation of the same resource forbidden unless a capability explicitly owns a safe merge protocol. When safe merge unavailable, execution MUST choose one: serialize; isolate (separate branches/worktrees/documents/sessions/artifacts); ask for user direction; fail before mutation. Silent last-write-wins forbidden.
- For `SelfParallel` read capabilities and idempotent reads with deterministic results, coalescing concurrent identical calls is recommended: dispatch one and broadcast the result to all N callers. Capability declares a key function deriving a canonical request hash; runtime maintains an in-flight table keyed by that hash. Coalescing is NOT a correctness requirement — capabilities whose surface arguments mask semantic distinctions (timestamp-changing URLs, session state, live tickers) opt out explicitly. Fully customizable: users may override globally, per capability, per scope, or enable a model-mediated `auto-mode` where a designated model decides per call whether the cached result is acceptable or the call must execute fresh.

## 16. Child Runs and Multi-Agent Work `run.child-runs-multi-agent-work`
### 16.1 Definition
- A child run = run created by another run. Used for: subagents; parallel research branches; independent coding worktrees; isolated browser tasks; validator/critic passes; comparison runs (best-of-N with selector child run, arena-style ranked rounds, tournament-style pairwise comparison); delegated surface/subsystem execution.

### 16.2 Isolation `run.isolation`
- Each child run MUST declare: parent run; purpose; allowed capability scope; context-sharing policy; output contract; merge target; cancellation relationship to parent; lifecycle visibility.
- Context sharing MUST be explicit; a child run does NOT receive unrestricted parent context by default.
- Canonical isolation primitives = filesystem-or-resource-level copies sharing the underlying object store/image/kernel: git worktrees for code-touching work; isolated browser profiles for browser work; sandboxed VM instances or virtual desktops for GUI control work; isolated process groups for shell work. Runtime selects the primitive based on the child's declared capability scope + parent's host environment. Isolation is contextual, not always preferable: when child runs share a workspace non-destructively (a single codebase the user is also editing, a browser session preserving human-verification cookies, parallel non-interfering observations), running without isolation is the right choice and the runtime MUST permit it. Isolation decision = per-child-run policy; defaults follow capability scope; users may override per task/surface/call.

### 16.3 Isolated and Inline Work
- `isolated` child work gets its own context policy, tool surface, budget, output contract.
- `inline` work allowed only when better modeled as a nested execution unit inside the parent run. If it can independently pause/fail/retry/own tools, it should be a child run instead. Inline work MUST NOT bypass policy/ledgering/version boundaries.
- An inline child run's mutations land in the parent's pending-operations buffer (§23.4) and commit at the parent's version-commit boundary. An isolated child run does NOT contribute to the parent's pending buffer; its work is captured as a single tool result block (or sequence of blocks) returned to the parent under the declared output contract. Parent's incorporation step (§16.4) decides to apply returned work to its buffer, branch on it, or discard.

### 16.4 Merge `run.merge`
- Child run outputs do NOT automatically mutate parent state. They MUST return through one of: summary; artifact; patch; evidence set; validation report; proposed task update; proposed workflow step. Parent run decides how to incorporate per the declared merge target.

## 17. Interruption, Pause, and Cancellation `run.interruption-pause-cancellation`
### 17.1 User Intervention `run.user-intervention`
- User may intervene during execution. Intervention is a run input, not an out-of-band conversation hack; MUST be recorded and may cause: continuation with new instruction; pause; cancellation; branch; reroute; approval grant or denial; scope narrowing; explicit takeover of the run's surface (`control` flips to `User`).
- On takeover, subsequent user actions recorded as first-class blocks attached to the run, indistinguishable in the ledger from agent-produced blocks. When control returns to the agent, system OFFERS (not requires) a summary input: user may describe what they did or skip. Next agent iteration receives whatever summary the user supplied alongside any observable filesystem/workspace deltas the runtime detected; either, both, or neither may be present, no agent flow blocks on this input.
- External changes the user makes outside the run's observation surface (edit in own editor, command in own terminal, workspace modification via any other surface) are NOT required to be tracked exhaustively. Runtime records what it can observe via registered watchers, version-graph deltas, capability-mediated reads; capabilities whose mutation depends on prior observation revalidate currency before mutating (§8.2). The agent treats its last-known state as potentially stale, not ground truth. Resilience property, not a synchronization system.

### 17.2 Pause and Resume `run.pause-resume`
- A paused run MUST preserve enough state to resume safely or explain why it cannot. Resumption MUST revalidate: world state freshness; capability availability; policy leases; resource locks/scopes; model route validity; user-visible assumptions.

### 17.3 Cancellation `run.cancellation`
- MUST support both cooperative stop and forceful termination. Each active run MUST have a shared cancellation signal. All registered listeners (model/tool loop, child runs per declared relationship, active capability calls, sandbox/process operations, other long-running units) receive the signal simultaneously and respond cooperatively. Parent run stays in `cancelling` until all listeners acknowledge completion or the cooperative-stop deadline expires; on expiry, runtime escalates to forceful termination of remaining listeners and transitions to `cancelled`. Listeners reporting completion after the run is `cancelled` produce typed orphan-output ledger entries; their outputs are not committed.
- Default path = cooperative cancellation. Long-running capabilities MUST check the signal at safe cancellation points when possible; should stop cleanly, preserve committed outputs, discard/orphan staged partials per capability semantics, report a typed cancellation outcome.
- That alone is insufficient. Nearly every Atlas-managed long-running unit should be killable both categorically and individually.
- Categorical control e.g.: cancelling a run together with its child-run tree; killing a sandbox together with processes/sessions owned by it; aborting an automation/workflow branch/browser-control session as one target.
- Individual control e.g.: cancelling one child run without killing the whole parent; killing one specific sandbox; stopping one specific tool call/spawned process; cutting off one provider stream/remote operation when supported.
- Capabilities MUST declare enough cancellation semantics for the runtime/UI to know: whether cooperatively stoppable; whether forcefully killable; what cleanup/rollback may still happen after kill; what partial side effects may remain after kill; the cooperative-stop deadline before forceful escalation; whether partial outputs are meaningful (`partial_output_meaningful: bool`); whether the capability owns resumable infrastructure (`resume_on_restart: bool`).
- System should prefer clean cooperative stop first when fast enough for safety/control; MUST escalate to forceful termination when immediate stop is required or cooperative stop fails to complete promptly enough for the active policy.
- Cooperative-stop deadline declared per capability. If undeclared, runtime uses a configurable default (§27: cancellation default deadlines). Defaults MUST be set with long tolerance — a legitimate long-running command (24-hour build, slow shell pipeline on weak hardware) MUST succeed under the default rather than be cut off — but every cancellation path MUST carry a finite deadline. Model may override the deadline per call (raise for a specific operation), but every override MUST remain finite; timeoutless operations not permitted. Cancellation UI surfaces the deadline as a countdown so the user can intervene before forceful escalation.
- Cancellation choices user-customizable. Cancel UI MUST offer at minimum: cancel the run alone; cancel run + child-run tree; cancel a specific tool call without cancelling the run; cancel a specific child run without cancelling siblings/parent; cancel a specific sandbox/process. Default action of the cancel button is configurable; its expanded menu surfaces the rest. Every active long-running unit owned by the runtime MUST be wrappable into one of these targets and reliably cancellable.
- Non-killable execution is an explicit exception. If a process/operation cannot be killed, later specs MUST identify the limitation explicitly and define fallback control behavior.
- Cancellation MUST record: requester; affected run + child runs; cleanup performed; whether cooperative/escalated/forceful; partial outputs retained or discarded; final status.
- Each capability declares whether partial output is meaningful: when `partial_output_meaningful` is `true`, partials before cancellation kept by default; when `false`, discarded. If undeclared, runtime defaults to keep-on-cooperative-stop and discard-on-forceful-kill. User can override per cancellation via the cancellation UI; choice recorded in the ledger.
- Runs `running` or `cancelling` at process restart become `failed` with typed reason `process_restart_orphan` by default; their resources (worktrees, sandboxes, child processes, leases) reaped per each capability's declared post-kill cleanup. Runtime preserves the run's saved state across restart — most agentic progress lives in durable storage, so failure-on-restart loses work-in-flight, not committed work. Capabilities owning genuinely resumable infrastructure (long-lived browser sessions, scheduled tasks, durable workflows) may declare `resume_on_restart: true` and provide a resume handler; runtime calls the handler instead of marking failed. Handler MUST revalidate world state, re-acquire leases, and either continue or transition to `failed` with a more specific typed reason. Runs that fail-on-restart MUST be surfaced with a per-run resume-or-discard affordance — runtime MUST NOT auto-resume orphaned runs at startup, but user MUST be able to retry or resume any one on demand.

## 18. Task Promotion and Task Updates `run.task-promotion-task-updates`
- Task promotion happens through explicit capability invocation. Execution may create/update a task when work benefits from explicit structure, including: multi-step progress tracking; durable artifact ownership; automation potential; approvals tied to a goal; pause/resume continuity; success criteria + validation.
- Task promotion is NOT: automatic router behavior; required for ordinary conversation; a hidden heuristic.
- Task updates MUST be revision-safe: an update carries the revision it was based on and fails or branches if the task changed concurrently.

## 19. Retry, Reroute, and Branch `run.retry-reroute-branch`
- Retry/reroute/branch MUST NOT interfere with a prior in-flight run. Default: leave the prior run executing in parallel while creating the new run as a linked parallel attempt; both remain accessible as distinct versions. Configurable at general + per-action level — users may require cancellation of the prior run, prompting, or other resolutions. Explicit cancellation is always available as a separate action regardless of this setting.

### 19.1 Retry `run.retry`
- A retry creates a new run or execution branch linked to the prior attempt. MUST NOT mutate the historical ledger of the prior run.
- May reuse: same route, same task, same inputs, same artifacts, same policy snapshot. May change: model route, capability implementation, context compilation, recovery strategy, user-provided instruction.

### 19.2 Reroute `run.reroute`
- Mid-execution reroute allowed when current execution lacks the right surface/model route/capability family/policy scope/surface runtime. Happens at a safe boundary: after current model output is parsed; after current capability calls reach safe commit/cancellation/staged state; before new mutation begins under the new route.
- If accepted, execution MUST choose one: suspend and hand off; create a child or continuation run; branch; supersede current run. If rejected, the rejection is returned in-band to the current run.
- New run receives the reroute reason + prior run link; it does NOT inherit in-flight context state implicitly.

### 19.3 Branch `run.branch`
- Required when two plausible execution paths should be preserved rather than overwritten. Applies to: tasks; conversations; artifacts; workflows; child run strategies.

## 20. Error Handling, Recovery, and Stuck Detection `run.error-handling`
### 20.1 Boundary Rule `run.boundary-rule`
- Execution coordinates errors; does not absorb every subsystem's internal policy.
- Provider retries, rate-limit handling, credential refresh, retry timing belong to the provider layer. Model-level failover after a typed provider/model failure belongs to model strategy. Execution receives either a model response, a selected fallback model path, or a typed failure and records the outcome.
- Context overflow is NOT an execution-layer compaction trigger. Context assembly reports overflow/degraded assembly; context management decides whether to compact/adjust budget/ask the user/return a typed failure. Execution then retries the affected unit or follows the recovery path.
- Execution may signal observed context pressure to the context layer via a typed boundary (e.g., a `ContextPressureObserved { used_pct, kind }` event), but the choice of context strategy (which compaction policy, summarize vs paginate) stays in the context layer. Execution recovers by retrying the affected unit after the context layer responds.
- Capability failures produce typed result objects whenever the run can continue; the active model/programmatic executor receives the failure as execution input and may recover/ask/branch/stop.
- Budget exhaustion preserves partial outputs. Before a non-fatal hard stop, execution should surface a typed budget-warning input to the active model/deterministic unit so it can summarize, request extension, or hand off useful partial work.

### 20.2 Recovery `run.recovery`
- First-class execution behavior. Required strategies: retry same unit with corrected input; expose error to model as context; switch model profile; switch capability implementation; narrow capability scope; revoke stale leases + reacquire with narrower scope (when a long-lived lease's grant context — workspace, file subtree, network host set — has changed, revoke, narrow the new request, ask again for grant); request user clarification; branch strategy; restore or propose rollback of materialized output; stop with typed failure.

### 20.3 Stuck Detection `run.stuck-detection`
- Runtime MUST detect obvious stuck states: repeated identical tool calls without progress; repeated failed validations; repeated provider/tool errors; no new durable output after configured iteration limits (including single-iteration empty responses where the model produced neither tool calls nor committable text — these escalate per the soft-warning rule below); child runs waiting on each other cyclically; ping-pong between repeated tool/action patterns.
- Stuck detection MUST escalate in-band before hard-stopping. On detection, executor first injects a typed warning into the active model/programmatic unit's context — the model can self-correct/narrow scope/stop. Repeated detection within the same run escalates: warning → structured directive → hard stop with typed failure. Number of warnings before hard escalation, warning text templates, per-pattern overrides (some escalate immediately because the model cannot resolve them in-band — cyclic child waiting) are all settings, not hardcoded constants.
- Runtime MAY use a model-mediated stuck detector as an opt-in option (a designated model evaluates the stuck signal and decides continue/warn/stop). Carries an extra model call, off by default; users may enable globally or per pattern when the higher cost is justified by lower false-positive rate.

## 21. Budgets and Limits `run.budgets-limits`
- Runs MUST support configurable budgets. Dimensions: maximum model steps; maximum tool/capability calls; maximum child-run depth; maximum concurrent units; context budget; output budget; provider budget; artifact/resource budget.
- Elapsed-time guards MAY be used only as external-process safety guards when no reliable completion signal exists; not correctness conditions and MUST be configurable.
- Programmatic and graph/workflow execution may compose per-stage budgets within a single run (a research pipeline declares thinking, acting, and final-response budgets; a multi-stage pipeline declares per-stage budgets). When configured, runtime enforces both per-stage + run-level budgets; per-stage warning fires before per-stage limit, run-level warning before run-level limit (soft-warning escalation rule from §20.3 applies to both). Budgets NOT enforced by default — provider rate limits + model-internal stop conditions suffice for ordinary work — and the runtime MUST NOT silently impose hidden budget limits. Users opt into per-run + per-stage enforcement at the granularity they want (per turn, per task, per surface, per subsystem, per workspace, globally).
- Before a non-fatal budget limit is reached, execution should emit a budget warning through the ledger/event/context path appropriate to the active unit; the warning MUST be visible to the model/programmatic executor before wrap-up is expected.

## 22. Termination `run.termination`
- A run may terminate because: it produced the requested answer; task success criteria satisfied; user cancelled; policy blocked; required capability unavailable; validation failed unrecoverably; configured budget reached; execution superseded by edit/retry/reroute.
- A successful completion requires accepted output + satisfaction of every active requirement of the latest authorized `RunCompletionContract` (§2.7): any postconditions declared on executed capabilities validated + recorded in the ledger; the run has at least one ledger entry beyond the model's textual claim of success when the contract required action (a forgery guard — a run with no recorded capability executions, no committed artifact revisions, and no model-step outputs beyond plain text cannot terminate as `completed` if its contract required action).
- A fluent assistant response is not sufficient when the contract required artifact mutation/validation/approval/evidence capture. The contract verified at completion is the latest authorized revision; a revision that weakened/removed a requirement is honored only if it passed the authority-gated, ledgered revision path of §2.7, so completion cannot be reached by first weakening the contract.
- These checks are deterministic, impose no extra model call. Beyond them, a configurable completion-verification hook surface (§23.3) is available for stronger semantic checks on whether a run satisfied the user's request. Hook surface accepts deterministic checks (capability postconditions, structured output validators, evidence-set comparators) and model-mediated checks (a designated model evaluating whether outputs meet a per-task expected outcome). Runs at user-configured cadence (every N model steps, in parallel as a background observer, sequentially before completion, or only at explicit `verify_now` invocations) and supports per-task/per-surface/per-profile configuration. Default ships disabled — the deterministic forgery guard above is the canonical termination floor; the hook surface is opt-in extension.

## 23. Ledger, Events, and Commits `run.ledger-events-commits`
### 23.1 Execution Ledger `run.execution-ledger`
- Durable source of consequential execution history. Records: run creation + status changes; route attachment; execution unit starts/finishes; capability proposals; approvals/denials/leases/policy decisions; model calls (provider, model identifier, role [router, responder, critic, validator, etc.], input tokens, completion tokens, cache creation tokens, cache read tokens, cost estimate — per-call cost computed from per-model pricing, not stored as an unkeyed scalar — cf. [`core.explicit-rejections`] (File 01 §8) invariant); tool calls + tool results; observations; validation results; errors + recovery decisions; produced outputs; child run relationships; cancellation + intervention.
- The list is a minimum, not an exhaustive schema. Ledger MUST record full-granularity timestamps on every entry and any additional execution-relevant attribution the storage spec requires (request ids, trace context, attempt counters, classification metadata) without forcing the canonical to enumerate exhaustively. Storage spec extends the schema; this file specifies the minimum execution reasoning depends on.
- The ledger enforces a forgery guard at status transition: a transition from `running` to `completed` is rejected if the run has no recorded capability executions, no committed artifact revisions, and no model-step outputs beyond plain text — when the run contract required action. The storage-side counterpart to §22's run-completion contract.

### 23.2 Event Stream `run.event-stream`
- Live projection channel. Drives: streaming UI; hooks; inspectors; progress views; approvals; validators; logs.
- Every event carries the canonical envelope defined by File 10. At execution level this means at least: `conversation_id` when conversation-scoped; `context_refs` for applicable execution identities (`run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`); `sequence_scope`; `sequence`; `timestamp`; `sensitivity` (`Public`, `Sensitive`, or `Secret`; default `Public`). Sensitive events excluded from shareable conversation exports + copy-to-clipboard on the event log unless explicitly included by policy. Capabilities tag at emit time — a generic `shell.exec` event is `Public`, but the same call against a credentials path is `Sensitive`. Raw `Secret` payloads in flight (credentials, unredacted secrets, user-marked secret content) MUST never be persisted to the durable ledger.
- Events may be transient. Consequential events MUST also be represented in the ledger.

### 23.3 Hook Integration `run.hook-integration`
- The event stream is also the execution hook surface. Blocking hooks may run at safe boundaries such as capability proposal, iteration start, context assembly result, version commit. They return one of four typed decisions:
  - `Continue` — proceed with the original payload.
  - `Substitute { new_payload }` — proceed with a hook-modified payload (guardrail rewrites a path; transformer normalizes arguments).
  - `Block { reason }` — abort the proposed action; executor records a denial and the typed reason flows in-band as a tool result.
  - `RedirectSuggestion { tool_id, args, reason }` — abort the proposed action and signal that the agent should retry using the suggested tool. Agent loop consumes this as a typed retry signal.
- Multiple blocking hooks can subscribe to the same boundary; each declares a `priority: i16` (lower runs first). Convention: audit/logging hooks at `-100` (capture pre-validation state); transformers/validators at `0` (default); approval router at `+100` (sees post-validation payload last). Executor evaluates blocking hooks in priority order. `Substitute` decisions compose as staged proposal transformations so later hooks, including the approval router, inspect the final substituted proposal. `Block` and `RedirectSuggestion` are terminal for the current proposal.
- Each blocking hook subscription declares a timeout/deadline profile used as a safety guard for hung handlers, not correctness logic. If the hook does not return within its guard, executor synthesizes a default decision and records the timeout in the ledger. Fail-direction follows File 10's category-and-authority rule: security-category hooks fail closed by default; non-security observer/enricher/formatter hooks fail open with warning; non-security hooks that can allow or substitute a consequential pre-action proposal fail closed unless explicitly overridden within policy limits. Security-category hooks require typed confirmation before they may fail open. Per-error-class behavior is configurable; a hook that fails for a known transient cause may retry within its safety guard rather than fail immediately.
- Non-blocking hooks may observe model streaming, capability execution, status changes, iteration completion, validation results, produced outputs. They MUST NOT control execution flow.
- Quality control validators, logging, plugin hooks, user hooks, policy gates, the completion-verification hook surface (§22) integrate through this shared mechanism. MUST NOT create a second hidden execution path.

### 23.4 Version Commits `run.version-commits`
- Version commits are meaningful history boundaries, not every ledger event. Typical boundaries: user message; accepted agent turn; accepted artifact revision; accepted task revision; retry branch; edit branch; context edit; import/export operation.
- During a turn-like run, pending block + artifact operations accumulate in a pending-operations buffer. The accepted boundary commits that buffer as one durable net change. Tool-level checkpoints may exist inside that boundary without becoming separate version commits; rejecting a checkpoint updates the pending buffer before commit.
- The ledger explains how a commit was produced; the version graph records the accepted durable state.

## 24. Output Semantics `run.output-semantics`
- Runs may produce: conversation messages; blocks; artifact versions; file materializations; patches; claims; evidence links; memory proposals; task revisions; workflow candidates; validation reports; execution summaries.
- Important outputs should become artifacts or typed durable objects; transcript text may describe/cite them but should not be their only identity.
- Large outputs should be stored as referenced artifacts/blobs, not forced into the transcript or model context.

## 25. Presentation `run.presentation`
- Execution presentation is a projection. The same run may be shown as: a normal conversation answer; compact progress summary; expandable timeline; workspace activity; multi-agent board; artifact diff; workflow graph; observability trace. Changing presentation does not change backend execution semantics.
- UI MUST be able to show: current run status; active execution unit; pending approvals/questions; selected model route when relevant; capability calls + results; child runs; produced artifacts; failure + recovery path.

## 26. Automation and Reuse `run.automation-reuse`
- Successful runs should be eligible for reuse. Runtime may propose: workflow template; automation; custom capability wrapper; validation recipe; instruction fragment; retrieval recipe; document/artifact template.
- Promotion to automation MUST preserve: trigger shape; required inputs; capability scope; policy requirements; validation requirements; output contract; failure handling.
- Automation uses the same run model when executed.

## 27. Settings `run.settings`
- Execution behavior MUST be configurable. Min support:
  - default + per-surface run budgets; model-step limits; tool/capability concurrency caps; tool-surface policy selection; grouped + per-tool zone overrides; always-load/selective-load/on-demand-load policies; child-run depth limit; reroute enablement; programmatic execution availability; tool borrowing + deferred loading behavior; budget warning thresholds; stuck detection thresholds; partial-output retention behavior; approval persistence scopes; approval mode selection; approval policy template selection; custom approval policy templates + per-scope overrides.
  - prior-run resolution policy for retry/reroute/branch (general default + per-action overrides).
  - permission tier resolution and `Denied`-tier override paths, including `typed-confirmation` selection per capability or family.
  - lease scope hierarchy enablement (single-proposal, run, intent-thread, task, conversation, workspace, global, reusable-policy-rule) + policy-validation rules rejecting contradictory combinations across scope levels.
  - approval-policy mode selection, including model-mediated `auto-decide` + per-template prompts.
  - coalescing policy (off, recommended, auto-mode model-mediated) per capability or globally, including per-call cache-vs-fresh control.
  - sibling-abort and `depends_on` dispatch behavior per capability and per batch.
  - per-capability + category-default cancellation deadlines, partial-output retention overrides, resume-on-restart enablement, plus the cancel UI's default action + expanded-menu options.
  - stuck detection thresholds (per pattern), in-band soft-warning escalation rules, opt-in model-mediated stuck detection.
  - per-stage + per-run budget composition (off by default), warning thresholds, granularity (per turn/task/surface/subsystem/workspace/global).
  - completion-verification hook surface configuration: enablement, deterministic-vs-model-mediated mode, cadence (every N steps, parallel/background, sequential, on demand), per-task expected-outcome shape.
  - hook subscription configuration: priority, timeout, fail-direction overrides per hook category + per error class.
  - event sensitivity classification overrides per capability or family.
  - ledger-record retention granularity + additional attribution fields beyond the canonical minimum.
  - surface-scoped tool loading defaults, cross-surface/subsystem borrow restriction (search-only by default), context-pressure auto-shrink behavior.
  - isolation primitive defaults per child run kind, with per-task and per-call overrides for shared-workspace work.
  - classification mode per capability — deterministic declaration vs model-mediated per-call classification — for `reversibility_class`, `idempotent`, and other declarations where a single static value is not meaningful.
- Settings define intended product variation; MUST NOT become hidden hardcoded branches.

## 28. Explicit Rejections `run.explicit-rejections`
- Treating conversation message generation as the whole execution model.
- Making every request a heavy task graph.
- Making the linear agent loop the universal core architecture.
- Making planning a mandatory phase.
- Allowing side effects outside capability and policy flow.
- Treating background work as a separate execution architecture.
- Allowing child agents to mutate parent state directly.
- Using silent last-write-wins for concurrent mutations.
- Recording fast-path work only as hidden router context.
- Treating live events as durable execution truth.
- Treating frontend participation style as backend execution mode.
- Task promotion by hidden router or execution heuristic.
- Automatic merge of parallel outputs without an explicit merge path.
- Automatic compaction as an execution-layer side effect.
- Provider retry and failover logic implemented inside the execution layer.
- Hardcoding one tool-loading policy with no meaningful user override.
- Hardcoding one approval-policy interpretation mode or template with no meaningful user override.
- Hardcoding retry/loop/budget/stuck thresholds outside settings.
- Locking parallel runs or parallel calls against the same backend/session/sandbox/external service to single-instance access — full parallelism and multi-use of every service is the canonical posture, and the event envelope must carry enough demultiplexing identity for it.
- Accepting `completed` status without recorded execution evidence when the run contract required action.
- Treating a tool's internal handling of input variants as a separate capability call (binary vs text branches inside one read tool, fallback paths inside one write tool) — internal sub-handling is the same capability with sub-modes.
- Silently auto-resuming orphaned in-flight runs at process restart without user-surfaced affordance.
- Enforcing budgets by default — budgets must be opt-in.
- Requiring/imposing model-mediated checks where the deterministic floor is sufficient, and conversely silently relying on deterministic checks where the user configured semantic verification.

## 29. Consequences for Later Specs `run.consequences-for-later-specs`
- Task specs MUST define revision-safe task updates + success criteria.
- Capability specs MUST define proposals, leases, previews, reversibility, idempotency, postconditions, concurrency metadata, partial-output meaningfulness, cooperative-stop deadlines, sibling-abort behavior, resume-on-restart handlers, stale-state revalidation patterns, per-capability classification mode (deterministic vs model-mediated).
- Policy specs MUST define approval, denial, escalation, lease semantics, the permission tier hierarchy including `Denied`, `typed-confirmation`, the lease scope hierarchy, model-mediated `auto-decide` mode, contradiction-checking across scope levels.
- Provider specs MUST expose model role, tool support, modality, streaming, fallback metadata, and surface backend identity for parallel-run demultiplexing.
- Context specs MUST compile context from run/task/artifact/world/memory/evidence state and expose overflow/degraded-assembly outcomes without mutating state, including the typed context-pressure boundary execution signals through.
- Storage specs MUST separate ledger/version commits/artifacts/projections, record full per-call provider/model/role/token/cache/cost attribution keyed by model identifier, carry full-granularity timestamps + any extension attribution, enforce the ledger-side forgery guard at status transition, define the orphan-run reconciliation policy at process restart.
- Event specs MUST carry the File 10 envelope (`conversation_id` where applicable, `context_refs`, `sequence_scope`, `sequence`, `timestamp`, `sensitivity`) on every event, and keep raw `Secret` payloads out of durable persistence.
- UI specs MUST present runs without making presentation the execution truth, surface failed-on-restart runs with per-run resume-or-discard affordances, expose the cancel UI's default action + expanded-menu options (cancel run / run+children / specific child / specific tool call / specific sandbox).
- Automation specs MUST reuse the run model instead of creating a parallel scheduler runtime, and compose per-stage budgets within the run model.
- Surface/subsystem specs MUST declare default tool surfaces, context policies, budgets, child-run affordances, and default cross-surface/subsystem capability access to search-and-borrow rather than autoload.
- Quality-control specs MUST integrate through event/capability hooks instead of a separate execution pipeline; the completion-verification hook surface MUST support both deterministic and model-mediated checks at user-configured cadence.
- Workspace/isolation specs MUST define the canonical isolation primitives (git worktrees, isolated browser profiles, sandboxed VM instances, isolated process groups), the runtime selection policy, plus the shared-workspace exception.
