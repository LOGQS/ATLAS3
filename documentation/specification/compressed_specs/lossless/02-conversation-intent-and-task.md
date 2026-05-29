> Lossless render of canonical/02-conversation-intent-and-task.md — original 21855 chars

# Conversation, Intent, and Task

Status: Canonical.

## Scope
- Defines: conversation; message; persisted work-line continuity; promoted task structure; per-request dispatch attachment.
- Does NOT define: block schema; run schema; execution graph grammar; storage schema; approval mechanics.

## Source Resolution
- Conversation is a control rail + continuity surface; intent threads and promoted tasks carry ongoing work structure.
- Conversation-first stays first-class without making transcript chronology the root durable model.
- `Message`, `Event`, blocks, intent threads, tasks, runs, versions stay separate primitives.
- Intent threads preserve continuity without requiring immediate task formalization.
- Tasks promoted only when explicit structure improves execution/inspection/automation/reuse.
- Pre-dispatch processing is non-destructive and recorded; does not bypass routing or ledgering.

## 1. Chosen Model `intent.chosen-model`
- Five distinct interaction objects at different levels:
  - `Conversation`: chronological user-facing continuity.
  - `Message`: one transcript entry.
  - `RunIntent`: what to do with this request now.
  - `IntentThread`: persisted work-line continuity when needed.
  - `Task`: promoted structured work when useful.

## 2. Conversation `intent.conversation`
### 2.1 Definition
- `Conversation` = durable user-facing container for an ongoing exchange. Provides: transcript chronology; conversation history and recall; default place for input/output; durable scoped context for storage, execution, settings, materialization.
- A conversation MAY be ephemeral (not persisted to history beyond active session) without changing active semantics; ephemeral status is a property of the conversation, not a separate kind.

### 2.2 Meaning
- Chronology container, not the full work model. One conversation MAY contain one/many: work lines, tasks, workspaces over time, concurrent runs.
- Chronology matters but is not enough for continuity ownership.
- Significant outputs become artifacts or typed durable objects with own identity/lifecycle; transcript may describe/cite/compose them but is not their primary home. Later specs define artifact identity/lifecycle.

### 2.3 Conversation State `intent.conversation-state`
- Coarse-grained activity state = priority-ordered reduction over active runs (first match wins):
  - `streaming`: ≥1 run producing user-visible output.
  - `processing`: ≥1 run active but none producing output.
  - `awaiting_user`: every active run blocked on explicit user input (approval/clarification/elicitation).
  - `idle`: no active work.
- A single run blocked on user input while another still produces output leaves conversation in `streaming`; blocked condition surfaced on that run's own UI element.
- Concurrent system operations surfaced as orthogonal indicators alongside activity state. Required indicator: `compacting` (continuity-summary or context-compaction operation in flight).
- Compaction is non-destructive, may run concurrently with any activity state. Later specs may add orthogonal indicators.
- Conversation activity state is distinct from per-run execution state (later execution specs define run states).

## 3. Message `intent.message`
### 3.1 Definition
- `Message` = one transcript block in the conversation timeline; user-visible conversational unit for: reading, writing, retrying, editing, branching (sibling at same parent), forking (new conversation seeded from a chosen message), deleting (soft by default; hard delete only on explicit user action), pinning, searching/filtering, scrolling history, bulk ops (copy, export, tag). Detailed semantics belong in later message/version-graph specs.

### 3.2 Boundary
- `Message` is NOT a task, run, artifact, or the universal context primitive. Those may relate to a message but are not the same object.

### 3.3 Messages and Events
- Transcript carries two content shapes:
  - `Message`: durable, addressable, retryable, editable, branchable transcript anchor. User messages + accepted agent turns are messages. Other subsystems link to message identity (memory provenance, evidence, version-graph nodes).
  - `Event`: live coordination marker projected into conversation surface — streaming partials, hook outputs, parallel-activity summaries, status timelines, dialog requests. Rendered inside/alongside transcript but NOT addressable/retryable/editable.
- Some content lives at the boundary (e.g., a tool-use proposal becomes a tool-result-bearing block on completion). Typed catalog of message/event kinds + promotion rules belong in later block/event specs.

### 3.4 Message Submission Lifecycle
- Between user submission and routing's `RunIntent`, system MAY perform pre-dispatch processing on the pending message. Allowed: expansion of references (pasted text tokens, attached files, slash-command resolution) into eventual body; detection of conditions resolvable before routing (duplicate content already in context, repeated identical requests, references to prior blocks); non-destructive presentation of resolution choices; hook invocation that may modify/annotate the pending message.
- Pre-dispatch processing is non-destructive, MUST NOT mutate prior messages/blocks, MUST NOT bypass routing or execution-ledger recording. Pre-dispatch decisions + resolutions are recorded in the ledger. Specific behaviors/defaults belong in later routing/settings/context-assembly specs.

## 4. RunIntent `intent.run-intent`
### 4.1 Definition
- `RunIntent` = the per-request dispatch decision. Answers: what work line this request belongs to; continue existing vs start parallel work; whether fast path suffices; whether richer execution needed; which capabilities/downstream subsystems relevant; which model/tool strategy.
- MAY originate from: user message, retry of prior request, edit of prior message, continuation of in-flight run, child-run request, scheduled task, automation, inbound external event (webhook/watch trigger/OS event), or user-invoked action. Per-origin routing rules belong in routing/dispatch spec; every `RunIntent` regardless of origin attaches to a primary intent thread under §5.4.

### 4.2 Source
- Produced by routing/dispatch layer; typically by the router model, with cheap deterministic checks where safe.
- Not a transcript object, but UI may surface the routing result, link it to the triggering user message, and allow override.
- Exact routing lifecycle (incl. retry/edit behavior) belongs in router spec. Complete `RunIntent` field schema, lifecycle, dispatch semantics defined in routing/dispatch spec.

### 4.3 Fast-Path Rule
- Fast path is a router outcome, not a separate pre-router system: request still goes through routing; if router decides work is trivial it MAY perform a simple tool/preparation step itself; downstream receives the prepared result and does not repeat it.
- Fast path MAY skip unnecessary downstream orchestration but MUST NOT skip: conversation attachment; work-line ownership; execution ledger recording.

## 5. IntentThread `intent.intent-thread`
### 5.1 Definition
- `IntentThread` = a persisted ongoing work line inside a conversation; exists when durable ownership stronger than raw chronology is needed.
- Intra-conversation by definition. Cross-conversation continuity (memory shared across conversations, automations spanning conversations, project-scoped state) is a workspace/substrate-service concern; later specs define. An intent thread does NOT span conversations.

### 5.2 Purpose
- Groups work belonging to the same continuing line: related messages, runs, artifacts, evidence, zero or more tasks.

### 5.3 Creation `intent.creation`
- Not required for every message. SHOULD be created/reused by routing/dispatch only when needed, especially when: request clearly continues existing work; starts a new parallel work line; user explicitly references a prior work line; a run/artifact/approval needs a durable owner; pause/resume continuity matters; task promotion is about to happen; conversation transitions between distinct phases (planning vs execution, exploration vs implementation) and prior phase should remain inspectable; a non-user origin (scheduled task/automation/external event) needs an owning work line outliving its trigger; a mid-execution reroute creates successor work that should not rewrite prior intent thread's state.
- Cheap deterministic attachment preferred first; model-assisted attachment only when ambiguity is real.
- Later router specs may maintain compact per-work-line summaries so continuity attachment stays cheap without replaying raw full history. A per-work-line summary, when present, MUST preserve enough to reconstruct continuity attachment without replaying raw history. Required minimum content: active goal/current line of work (in user's words where preserved); relevant prior decisions + rationale; pending tasks/TODOs/commitments; last user request that advanced the work line; active assumptions and open questions.
- Exact format/storage of work-line summaries belong in later context-assembly/compaction specs.

### 5.4 Ownership
- Each incoming request attaches to exactly one primary intent thread. MAY reference other work lines, but primary ownership MUST stay unambiguous. Exists so later specs can attach runs/artifacts/approvals/status cleanly.

### 5.5 Mid-Execution User Input
- New request while ≥1 runs still executing attaches either to same intent thread (extending) or a new intent thread (parallel/successor). Choice follows §5.3 attachment rules and MUST be deterministic and recorded.
- Mid-execution input MUST NOT silently abandon in-flight runs and MUST NOT silently rewrite prior intent thread's history; outcome of any displaced run MUST be recorded as cancellation or supersession. In-flight run behavior on new user message — interrupt, queue, summarize-and-continue, or supersede — MUST be user-configurable through settings, with default + per-action override. Detailed mechanics belong in execution spec; this file requires only that the continuity decision is unambiguous and durable.

## 6. Task `intent.task`
### 6.1 Definition
- `Task` = promoted structured work object inside an intent thread; exists when work benefits from explicit structure.

### 6.2 Minimum Fields
- MUST carry at least: stable identity surviving revision/branching/renaming; goal; scope; constraints; assumptions; open questions; success criteria; typed lifecycle status (min: `pending`, `in_progress`, `awaiting_user`, `blocked`, `completed`, `failed`, `cancelled`, `superseded`); parent task if any (null for root); dependencies (refs to other tasks whose outputs this task requires before start); a monotonically increasing revision counter supporting revision-safe concurrent updates.
- Later specs may extend; these fields required.

### 6.3 Promotion Rule `intent.promotion-rule`
- Appropriate when work needs: explicit multi-step structure; clearer progress tracking; stronger execution ownership; durable artifact attachment to a named goal; automation potential; pause/resume continuity beyond normal flow; structured handling of ambiguity (multiple plausible interpretations/stakeholders/conflicting constraints); escalation after repeated failure/unproductive iteration.
- NOT required for ordinary conversation or simple requests. Single-question/single-answer conversation MUST NOT require task ceremony.
- Promotion MAY be initiated by user explicitly creating a task, by agent via explicit capability invocation, or by a hook surfacing a promotion recommendation for user/agent to accept. Hidden routing/execution heuristics MUST NOT silently promote work into a task.

### 6.4 Current Driver
- A task carries a current driver — actor responsible for the next action. Driver MAY be user, agent, or shared across actors under explicit coordination rules. Driver transitions MUST be explicit and recorded; silent transitions forbidden. Later specs define handoff mechanics, multi-driver coordination, and relationship between task driver and its runs' drivers.

## 7. Parallel Work `intent.parallel-work`
### 7.1 Allowed Shapes (representative, not exhaustive)
- multiple work lines in one conversation; multiple tasks in one conversation; multiple concurrent runs in one conversation; multiple concurrent runs attached to one task (subject to later execution rules); multiple agents driving concurrent worktrees/child sessions/workspaces under one task; sibling responses by parallel models/strategies user may compare/merge; structured multi-agent presentations (classrooms, debates, coordinator-worker) where many agent runs share one transcript; parallel sub-runs spawned from a single agent turn (batch tool calls, fan-out research, multi-perspective synthesis); child runs spawned from a parent run for delegated work; non-user-originated runs (scheduled/automation/external) interleaved with user-originated.
- Later specs define concurrency/isolation/merge semantics per shape.

### 7.2 Constraints (required)
- Every run carries enough identity to resolve unambiguously: its conversation, owning intent thread, task (if any), parent run (if any).
- Every block/message/event a run produces carries enough identity to resolve which run, intent thread, conversation, and (where applicable) workspace/worktree/agent/DAG node produced it.
- No silent ambiguity about which work line owns a run; no silent ambiguity about which task a structured run progresses; no flat-only transcript requirement for parallel activity; no shared mutable task state model parallel runs overwrite in place.
- Revision-safe task updates: an update carries the revision counter it was based on and either succeeds against unchanged task, fails with typed conflict, or branches the task into a sibling revision.
- Later specs MUST define run objects, exact identifier schema, revision-safe task update mechanics, write-collision handling explicitly.

## 8. Presentation `intent.presentation`
### 8.1 Principle
- Same underlying work may render in many shapes without changing the work model. Examples (not exhaustive): conversation-first transcript; inline assistance on a non-conversation surface; workspace-primary views (editor/browser/terminal/document/canvas/whiteboard); notebook/pipeline view of structured tasks; comparison board for parallel branches/runs/agents; classroom/debate view for multi-agent transcripts; observability trace/status timeline/version-tree visualizer; artifact diff/draft preview/live render.
- A presentation surface = projection over underlying work, not part of the work model. Surface set MUST be extensible (new surfaces/compositions/user- or extension-supplied views addable without changing work model). Later specs define presentation surfaces, compositions, per-profile defaults.

### 8.2 Conversation-First
- First-class experience. User MUST be able to stay entirely in the conversation interface while runtime still uses tools/surfaces/subsystems internally.

### 8.3 Workspace-First
- Appropriate when direct inspection/participation matters more than transcript simplicity. Same work may move between conversation-first and workspace-first over time.

### 8.4 Parallel Presentation
- Parallel activity MUST remain readable. System MUST NOT require all parallel work to appear as one flat event stream in the main transcript. Grouped activity, summaries, expanded detail views, focused workspace views all valid projections.

### 8.5 Customization
- Presentation customizable per profile, per workspace, per conversation. Profile/workspace defaults are seeds, not contracts: user may switch shapes, recompose surfaces, save custom layouts, override at any time. Customization MUST NOT change the underlying work model. Later specs define profiles, view presets, per-conversation overrides, saved-layout mechanics.

## 9. Explicit Rejections `intent.explicit-rejections`
- Treating conversation as the only durable work model.
- Forcing every request to become a task.
- Making intent-thread creation a mandatory tool call.
- Treating presentation choice as routing-owned backend truth.
- Adding a second separate heavy continuity-analysis pass on top of normal routing.
- Collapsing routing output to one surface/subsystem pick.
- Treating presentation shape as a separate execution architecture.
- Silent driver transitions in tasks or runs.
- Silent abandonment of in-flight runs by mid-execution user input.
- Assuming a single active stream per conversation.
- Presentation customization that mutates the underlying work model.
- Hardcoding any conversation lifecycle state, intent-thread creation rule, task promotion criterion, or presentation shape that meaningful user variation should configure.

## 10. Consequences for Later Specs `intent.consequences-for-later-specs`
- Run objects MUST attach to conversations, intent threads, and optional tasks distinctly.
- Task specs MUST support revision-safe updates rather than shared in-place mutation.
- Routing specs MUST define continuity attachment as part of `RunIntent`.
- Execution specs MUST support safe parallel work without ownership ambiguity.
- UI specs MUST support both conversation-first and richer workspace presentations over the same underlying objects.
- Workspace specs MUST define cross-conversation continuity primitives (memory scope, project scope, automation scope) without redefining `IntentThread`.
- Conversation state MUST remain a coarse-grained projection of underlying runs + explicit pause requests; later specs MUST NOT collapse it into per-run execution state.
- Settings specs MUST define which pre-dispatch behaviors are enabled per profile/workspace/conversation.
- Ledger specs MUST record pre-dispatch decisions + resolutions alongside the eventual `RunIntent` and triggering message.
- Context-assembly/compaction specs MUST produce per-work-line summaries satisfying §5.3 minimum content and MUST NOT silently lose any of those fields during compaction.
- Task driver transitions MUST be recorded in the execution ledger and surfaced to UI; later specs define handoff mechanics.
- Storage/event specs MUST define the identifier schema satisfying §7.2 ownership-resolution; events spanning multiple ownership levels MUST carry every applicable identifier.
- Execution specs MUST define mid-execution user input handling (interrupt/queue/summarize-and-continue/supersede) with user-configurable default + per-action override; chosen behavior MUST produce a recorded continuity decision satisfying §5.5.
- Settings/UI specs MUST allow users to customize presentation shape per profile/workspace/conversation, with a profile default that does not lock the user out of switching.
- Automation/scheduling/trigger specs MUST define how non-user-originated `RunIntent`s attach to intent threads under §5.4.
