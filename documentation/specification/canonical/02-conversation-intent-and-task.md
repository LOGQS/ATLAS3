# Conversation, Intent, and Task

## Status

Canonical.

## Scope

This file defines the interaction-level work model for:

- conversation
- message
- persisted work-line continuity
- promoted task structure
- per-request dispatch attachment

This file does not define:

- block schema
- run schema
- execution graph grammar
- storage schema
- approval mechanics

## Source Resolution

This file resolves conversation, message, intent-thread, task, branch, and transcript material into one boundary: conversation is a control rail and continuity surface, while intent threads and promoted tasks carry ongoing work structure.

Resolved design:

- Conversation-first use remains first-class without making transcript chronology the root durable model.
- Messages, events, blocks, intent threads, tasks, runs, and versions stay separate primitives.
- Intent threads preserve continuity without requiring immediate task formalization.
- Tasks are promoted only when explicit structure improves execution, inspection, automation, or reuse.
- Pre-routing processing is non-destructive and recorded; it does not bypass routing or ledgering.

## 1. Chosen Model

Anchor: `intent.chosen-model`

ATLAS should use five distinct interaction objects:

- `Conversation`
- `Message`
- `RunIntent`
- `IntentThread`
- `Task`

They exist at different levels:

- `Conversation`: chronological user-facing continuity
- `Message`: one transcript entry
- `RunIntent`: what to do with this request now
- `IntentThread`: persisted work-line continuity when needed
- `Task`: promoted structured work when useful

This keeps normal conversation fluid while still supporting long-running, parallel, and structured work.

## 2. Conversation

Anchor: `intent.conversation`

### 2.1 Definition

`Conversation` is the durable user-facing container for an ongoing exchange with ATLAS.

It provides:

- transcript chronology
- conversation history and recall
- the default place for input and output
- a durable scoped context for storage, execution, settings, and materialization

A conversation may be ephemeral (not persisted to history beyond the active session) without changing its active semantics; ephemeral status is a property of the conversation, not a separate kind.

`Conversation`, `IntentThread` (§5), and `Task` (§6) are durable primitives: each has stable identity and a durable lifecycle with a tombstoned end state that remains auditable rather than physically erased. Their source-of-truth persistence families are owned by the storage layer (`storage.durable-substrate` (File 20 §3.3)); this file defines their interaction-level semantics, not their storage schema.

An ephemeral conversation's durable byproducts outlive its presence in ordinary history. Ledger entries, committed blocks, artifacts, and lease records the conversation produced remain persisted and auditable after ephemeral-end; ending an ephemeral conversation tombstones its record and excludes it from ordinary history recall without deleting those byproducts or invalidating references to them.

### 2.2 Meaning

Conversation is a chronology container, not the full work model.

One conversation may contain:

- one or many work lines
- one or many tasks
- one or many workspaces over time
- one or many concurrent runs

Chronology matters, but chronology alone is not enough for continuity ownership.

Important outputs do not live only as transcript content. Significant outputs become artifacts or typed durable objects with their own identity and lifecycle; the transcript may describe, cite, or compose them, but the transcript is not their primary home. Artifact identity and lifecycle are defined in `artifact.artifact` (File 09 §3).

### 2.3 Conversation State

Anchor: `intent.conversation-state`

A conversation has a coarse-grained activity state, computed as a priority-ordered reduction over its active runs. A run is actively executing when it is making progress and not blocked on user input; a run blocked on explicit user input is active but not actively executing:

- `streaming`: at least one run is producing user-visible output
- `processing`: at least one run is actively executing but none is producing user-visible output
- `awaiting_user`: at least one run is active and every active run is blocked on explicit user input (approval, clarification, elicitation response)
- `idle`: no active runs

The first matching state wins. A single run blocked on user input while another run is still producing output leaves the conversation in `streaming`; the blocked condition is surfaced on that run's own UI element.

Concurrent system operations are surfaced as orthogonal indicators alongside the activity state. The required indicator is:

- `compacting`: a continuity-summary or context-compaction operation is in flight

Compaction is non-destructive and may run concurrently with any activity state. Later specs may define additional orthogonal indicators.

Conversation activity state is distinct from per-run execution state; run states are defined in `run.run` (File 04 §2.4).

## 3. Message

Anchor: `intent.message`

### 3.1 Definition

`Message` is one transcript block in the conversation timeline.

It is the user-visible conversational unit for:

- reading
- writing
- retrying
- editing
- branching (creating a sibling at the same parent)
- forking (creating a new conversation seeded from a chosen message)
- deleting (soft by default; hard delete only on explicit user action)
- pinning
- searching and filtering
- scrolling through history
- bulk operations such as copy, export, and tag

Detailed semantics for these operations belong in later message and version-graph specs.

### 3.2 Boundary

`Message` is not:

- a task
- a run
- an artifact
- the universal context primitive

Those may relate to a message, but they are not the same object.

### 3.3 Messages and Events

The transcript carries two content shapes:

- `Message`: durable, addressable, retryable, editable, branchable transcript anchor. User messages and accepted agent turns are messages. Other subsystems link to message identity (memory provenance, evidence, version-graph nodes).
- `Event`: live coordination marker projected into the conversation surface — streaming partials, hook outputs, parallel-activity summaries, status timelines, dialog requests. Events render inside or alongside the transcript but are not addressable, retryable, or editable as messages are.

Some content lives at the boundary; for example, a tool-use proposal becomes a tool-result-bearing block when the call completes. The typed catalog of message kinds is defined in `block.block-kind` (File 08 §3), the typed catalog of event kinds in `ledger.event-stream` (File 10 §5), and the promotion rules between them in those block and event specs.

### 3.4 Message Submission Lifecycle

Between the user's submission of a message and the routing layer's production of a `RunIntent`, the system may perform pre-routing processing on the pending message.

Allowed operations include:

- expansion of references (pasted text tokens, attached files, slash-command resolution) into the eventual message body
- detection of conditions resolvable before routing (duplicate content already present in context, repeated identical requests, references to prior blocks)
- non-destructive presentation of resolution choices to the user
- hook invocation that may modify or annotate the pending message

Pre-routing processing is non-destructive, must not mutate prior messages or blocks, and must not bypass routing or execution-ledger recording. Pre-routing decisions and their resolutions are recorded in the ledger. Specific behaviors and their defaults belong in later routing, settings, and context-assembly specs.

## 4. RunIntent

Anchor: `intent.run-intent`

### 4.1 Definition

`RunIntent` is the per-request dispatch decision.

It answers:

- what line of work this request belongs to
- whether this should continue existing work or start parallel work
- whether fast path is sufficient
- whether richer execution is needed
- which capabilities or downstream subsystems are relevant
- which model/tool strategy should be used

A `RunIntent` may originate from a user message, a retry of a prior request, an edit of a prior message, a continuation of an in-flight run, a child-run request, a scheduled task, an automation, an inbound external event (webhook, watch trigger, OS event), or a user-invoked action. Per-origin routing rules belong in `routing.trigger-kinds-routing` (File 03 §2.1); every `RunIntent`, regardless of origin, attaches to a primary intent thread under §5.4.

### 4.2 Source

`RunIntent` is produced by the routing and dispatch layer.

It is typically produced by the router model, with cheap deterministic checks used where safe.

It is not a transcript object, but the UI may surface the routing result, link it to the triggering user message, and allow the user to override it.

Exact routing lifecycle rules, including retry and edit behavior, belong in the router spec. The complete `RunIntent` field schema, lifecycle, and dispatch semantics are defined in `routing.run-intent` (File 03 §4).

### 4.3 Fast-Path Rule

Fast path is a router outcome, not a separate pre-router system.

Meaning:

- the request still goes through routing
- if the router decides the work is trivial, it may perform a simple tool step or preparation step itself
- downstream handling receives that prepared result and does not need to repeat it

Fast path may skip unnecessary downstream orchestration, but it must not skip:

- conversation attachment
- work-line ownership
- execution ledger recording

## 5. IntentThread

Anchor: `intent.intent-thread`

### 5.1 Definition

`IntentThread` is a persisted ongoing work line inside a conversation.

It exists when the system needs durable ownership stronger than raw chronology.

An intent thread is intra-conversation by definition. Cross-conversation continuity (memory shared across conversations, automations that span conversations, project-scoped state) is a workspace and substrate-service concern; later specs define those primitives. An intent thread does not span conversations.

### 5.2 Purpose

It is used to group together work that belongs to the same continuing line, including:

- related messages
- related runs
- related artifacts
- related evidence
- zero or more tasks

### 5.3 Creation

Anchor: `intent.creation`

Every dispatched `RunIntent` has exactly one primary intent thread (§5.4). That thread may be created implicitly and cheaply, so no dispatched request lacks an owning work line; explicit, durable formalization of an intent thread is not required for every message.

An intent thread should be explicitly created or reused by routing/dispatch only when needed, especially when:

- the request clearly continues existing work
- the request starts a new parallel work line
- the user explicitly references a prior work line
- a run, artifact, or approval needs a durable owner
- pause/resume continuity matters
- task promotion is about to happen
- the conversation transitions between distinct phases (planning vs execution, exploration vs implementation) and the prior phase should remain inspectable
- a non-user origin (scheduled task, automation, external event) needs an owning work line that outlives its trigger
- a mid-execution reroute creates successor work that should not rewrite the prior intent thread's state

Cheap deterministic attachment should be preferred first.

Model-assisted attachment should be used only when ambiguity is real.

The context-assembly and compaction layer (`context.continuity-summaries` (File 13 §14)) owns per-work-line summaries; routing consumes a summary for cheap continuity attachment without replaying raw full history rather than maintaining its own. A per-work-line summary, when present, must preserve enough information to reconstruct continuity attachment without replaying raw history. Required minimum content:

- the active goal or current line of work, in the user's words where preserved
- the relevant prior decisions and their rationale
- any pending tasks, TODOs, or commitments
- the last user request that advanced the work line
- active assumptions and open questions

Exact format and storage of work-line summaries belong in later context-assembly and compaction specs.

### 5.4 Ownership

Each incoming request attaches to exactly one primary intent thread.

It may reference other work lines, but primary ownership must stay unambiguous.

That rule exists so later specs can attach runs, artifacts, approvals, and status cleanly.

### 5.5 Mid-Execution User Input

When the user sends a new request while one or more runs in the conversation are still executing, the new request attaches either to the same intent thread (extending the work line) or to a new intent thread (starting a parallel or successor work line). The choice follows the same attachment rules as §5.3 and must be deterministic and recorded.

Mid-execution input must not silently abandon in-flight runs and must not silently rewrite the prior intent thread's history; the outcome of any displaced run must be recorded as cancellation or supersession. The behavior of in-flight runs in response to a new user message — interrupt, queue, summarize-and-continue, or supersede — must be user-configurable through settings, with both a default and per-action override available. Detailed mechanics belong in the execution spec; this file requires only that the continuity decision is unambiguous and durable.

## 6. Task

Anchor: `intent.task`

### 6.1 Definition

`Task` is a promoted structured work object inside an intent thread.

It exists when the work benefits from explicit structure.

### 6.2 Minimum Fields

A task must carry at least:

- stable identity that survives revision, branching, and renaming
- goal
- scope
- constraints
- assumptions
- open questions
- success criteria
- typed lifecycle status (at minimum: `pending`, `in_progress`, `awaiting_user`, `blocked`, `completed`, `failed`, `cancelled`, `superseded`)
- parent task, if any (null for root tasks)
- dependencies — references to other tasks whose outputs this task requires before it can start
- a monotonically increasing revision counter that supports revision-safe concurrent updates

Later specs may extend the task schema, but these fields are required.

### 6.3 Promotion Rule

Anchor: `intent.promotion-rule`

Task promotion is appropriate when the work needs:

- explicit multi-step structure
- clearer progress tracking
- stronger execution ownership
- durable artifact attachment to a named goal
- automation potential
- pause/resume continuity beyond normal conversation flow
- structured handling of ambiguity (multiple plausible interpretations, multiple stakeholders, conflicting constraints)
- escalation after repeated failure or unproductive iteration

Task promotion is not required for ordinary conversation or simple requests. Single-question, single-answer conversation must not require task ceremony.

Promotion may be initiated by the user explicitly creating a task, by the agent through explicit capability invocation, or by a hook that surfaces a promotion recommendation for the user or agent to accept. Hidden routing or execution heuristics must not silently promote work into a task.

### 6.4 Current Driver

A task carries a current driver — the actor responsible for the next action. The driver may be the user, the agent, or shared between multiple actors under explicit coordination rules. Driver transitions must be explicit and recorded; silent transitions are forbidden. Later specs define the mechanics of driver handoff, multi-driver coordination, and the relationship between a task's driver and the drivers of its runs.

## 7. Parallel Work

Anchor: `intent.parallel-work`

### 7.1 Allowed Shapes

This model allows the following shapes; the list is representative, not exhaustive:

- multiple work lines inside one conversation
- multiple tasks inside one conversation
- multiple concurrent runs inside one conversation
- multiple concurrent runs attached to one task, subject to later execution rules
- multiple agents driving concurrent worktrees, child sessions, or workspaces under one task
- sibling responses produced by parallel models or strategies that the user may compare or merge
- structured multi-agent presentations (classrooms, debates, coordinator-worker patterns) where many agent runs share one transcript
- parallel sub-runs spawned from a single agent turn (batch tool calls, fan-out research, multi-perspective synthesis)
- child runs spawned from a parent run for delegated work
- non-user-originated runs (scheduled tasks, automations, external events) interleaved with user-originated runs

Later specs define the concurrency, isolation, and merge semantics for each shape.

### 7.2 Constraints

This file does not define full concurrency mechanics, but it does require:

- every run carries enough identity to resolve, without ambiguity, the conversation it belongs to, the intent thread that owns it, the task (if any) it advances, and the parent run (if any) that spawned it
- every block, message, and event the run produces carries enough identity to resolve which run, intent thread, conversation, and (where applicable) workspace, worktree, agent, or DAG node produced it
- no silent ambiguity about which work line owns a run
- no silent ambiguity about which task a structured run is progressing
- no flat-only transcript requirement for parallel activity
- no shared mutable task state model that parallel runs overwrite in place
- revision-safe task updates: a task update carries the revision counter it was based on and either succeeds against an unchanged task, fails with a typed conflict, or branches the task into a sibling revision

Later specs must define run objects, the exact identifier schema, revision-safe task update mechanics, and write-collision handling explicitly.

## 8. Presentation

Anchor: `intent.presentation`

### 8.1 Principle

The same underlying work may be rendered in many shapes without changing the work model. Examples include but are not limited to:

- conversation-first transcript
- inline assistance overlaid on a non-conversation surface
- workspace-primary views (editor, browser, terminal, document, canvas, whiteboard)
- notebook or pipeline view of structured tasks
- comparison board for parallel branches, runs, or agents
- classroom or debate view for multi-agent transcripts
- observability trace, status timeline, or version-tree visualizer
- artifact diff, draft preview, or live render

A presentation surface is a projection over the underlying work, not part of the work model. The set of presentation surfaces must be extensible: new surfaces, new compositions, and user- or extension-supplied views must be addable without changing the work model. Presentation surfaces, their compositions, and per-profile defaults are defined in `ui.presentation-projection` (File 37 §3).

### 8.2 Conversation-First

Conversation-first is a first-class experience.

The user must be able to stay entirely in the conversation interface while the runtime still uses tools, surfaces, and subsystems internally.

### 8.3 Workspace-First

Workspace-first is appropriate when direct inspection or participation matters more than transcript simplicity.

The same work may move between conversation-first and workspace-first over time.

### 8.4 Parallel Presentation

Parallel activity must remain readable.

The system must not require all parallel work to appear as one flat event stream in the main transcript.

Grouped activity, summaries, expanded detail views, and focused workspace views are all valid projections.

### 8.5 Customization

Presentation is customizable per profile, per workspace, and per conversation. Profile and workspace defaults are seeds, not contracts: the user may switch presentation shapes, recompose surfaces, save custom layouts, and override presentation choices at any time. Presentation customization must not change the underlying work model. Later specs define profiles, view presets, per-conversation overrides, and the mechanics of saved layouts.

## 9. Explicit Rejections

Anchor: `intent.explicit-rejections`

The following shapes are wrong for this layer:

- treating conversation as the only durable work model
- forcing every request to become a task
- making intent-thread creation a mandatory tool call
- treating presentation choice as routing-owned backend truth
- adding a second separate heavy continuity-analysis pass on top of normal routing
- collapsing routing output to one surface/subsystem pick
- treating presentation shape as a separate execution architecture
- silent driver transitions in tasks or runs
- silent abandonment of in-flight runs by mid-execution user input
- assuming a single active stream per conversation
- presentation customization that mutates the underlying work model
- hardcoding any conversation lifecycle state, intent-thread creation rule, task promotion criterion, or presentation shape that meaningful user variation should configure

## 10. Consequences for Later Specs

Anchor: `intent.consequences-for-later-specs`

Later specs must follow these rules:

- run objects must attach to conversations, intent threads, and optional tasks distinctly
- task specs must support revision-safe updates rather than shared in-place mutation
- routing specs must define continuity attachment as part of `RunIntent`
- execution specs must support safe parallel work without ownership ambiguity
- UI specs must support both conversation-first and richer workspace presentations over the same underlying objects
- workspace specs must define cross-conversation continuity primitives (memory scope, project scope, automation scope) without redefining `IntentThread`
- conversation state must remain a coarse-grained projection of underlying runs and explicit pause requests; later specs must not collapse conversation state into per-run execution state
- settings specs must define which pre-routing behaviors are enabled per profile, per workspace, and per conversation
- ledger specs must record pre-routing decisions and their resolutions alongside the eventual `RunIntent` and triggering message
- context-assembly and compaction specs must produce per-work-line summaries that satisfy §5.3's minimum content requirement and must not silently lose any of those fields during compaction
- task driver transitions must be recorded in the execution ledger and surfaced to the UI; later specs define handoff mechanics
- storage and event specs must define the identifier schema that satisfies §7.2's ownership-resolution requirement; events that span multiple ownership levels must carry every applicable identifier
- execution specs must define mid-execution user input handling (interrupt, queue, summarize-and-continue, supersede) with a user-configurable default and per-action override; the chosen behavior must produce a recorded continuity decision that satisfies §5.5
- settings and UI specs must allow users to customize presentation shape per profile, per workspace, and per conversation, with a profile default that does not lock the user out of switching
- automation, scheduling, and trigger specs must define how non-user-originated `RunIntent`s attach to intent threads under §5.4

## 11. Canonical Rule Anchors

Anchor: `intent.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `intent.chosen-model`, `intent.conversation`, `intent.conversation-state`, `intent.message`, `intent.run-intent`, `intent.intent-thread`, `intent.creation`, `intent.task`, `intent.promotion-rule`, `intent.parallel-work`, and `intent.presentation`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
