# Conversation, Intent, and Task — Operative Core

## 1. Chosen Model `intent.chosen-model`
- Five interaction objects: `Conversation`, `Message`, `RunIntent`, `IntentThread`, `Task`.

## 2. Conversation `intent.conversation`
### 2.3 Conversation State `intent.conversation-state`
- Activity state = priority-ordered reduction over active runs (first match wins): `streaming`, `processing`, `awaiting_user`, `idle`.
- Required orthogonal indicator: `compacting`.

## 3. Message `intent.message`
### 3.4 Message Submission Lifecycle
- Pre-dispatch processing MUST NOT mutate prior messages/blocks.
- Pre-dispatch processing MUST NOT bypass routing or execution-ledger recording.

## 4. RunIntent `intent.run-intent`
### 4.3 Fast-Path Rule
- Fast path MUST NOT skip: conversation attachment; work-line ownership; execution ledger recording.

## 5. IntentThread `intent.intent-thread`
### 5.1 Definition
- An intent thread does NOT span conversations.
### 5.3 Creation `intent.creation`
- A per-work-line summary, when present, MUST preserve enough to reconstruct continuity attachment without replaying raw history.
- Required minimum summary content: active goal/current line of work; relevant prior decisions + rationale; pending tasks/TODOs/commitments; last user request that advanced the work line; active assumptions and open questions.
### 5.4 Ownership
- Each incoming request attaches to exactly one primary intent thread; primary ownership MUST stay unambiguous.
### 5.5 Mid-Execution User Input
- The continuity choice MUST be deterministic and recorded.
- Mid-execution input MUST NOT silently abandon in-flight runs.
- Mid-execution input MUST NOT silently rewrite prior intent thread's history.
- Outcome of any displaced run MUST be recorded as cancellation or supersession.
- In-flight run behavior on new user message (interrupt/queue/summarize-and-continue/supersede) MUST be user-configurable with default + per-action override.

## 6. Task `intent.task`
### 6.2 Minimum Fields
- MUST carry: stable identity surviving revision/branching/renaming; goal; scope; constraints; assumptions; open questions; success criteria; typed lifecycle status; parent task if any; dependencies; monotonically increasing revision counter.
- Lifecycle status minimum: `pending`, `in_progress`, `awaiting_user`, `blocked`, `completed`, `failed`, `cancelled`, `superseded`.
### 6.3 Promotion Rule `intent.promotion-rule`
- Single-question/single-answer conversation MUST NOT require task ceremony.
- Hidden routing/execution heuristics MUST NOT silently promote work into a task.
### 6.4 Current Driver
- Driver transitions MUST be explicit and recorded; silent transitions forbidden.

## 7. Parallel Work `intent.parallel-work`
### 7.2 Constraints
- Every run MUST carry identity resolving: conversation, owning intent thread, task (if any), parent run (if any).
- Every block/message/event MUST carry identity resolving which run, intent thread, conversation, and (where applicable) workspace/worktree/agent/DAG node produced it.
- Revision-safe task updates: an update carries the revision it was based on and either succeeds against unchanged task, fails with typed conflict, or branches into a sibling revision.
- PROHIBITED: silent ownership ambiguity; flat-only transcript requirement; shared mutable task state overwritten in place.
- Later specs MUST define run objects, identifier schema, revision-safe task update mechanics, write-collision handling.

## 8. Presentation `intent.presentation`
### 8.1 Principle
- Surface set MUST be extensible.
### 8.2 Conversation-First
- User MUST be able to stay entirely in the conversation interface while runtime uses tools/surfaces/subsystems internally.
### 8.4 Parallel Presentation
- Parallel activity MUST remain readable.
- System MUST NOT require all parallel work to appear as one flat event stream in the main transcript.
### 8.5 Customization
- Customization MUST NOT change the underlying work model.

## 9. Explicit Rejections `intent.explicit-rejections`
- Conversation as only durable work model.
- Forcing every request to become a task.
- Mandatory intent-thread-creation tool call.
- Presentation choice as routing-owned backend truth.
- Second heavy continuity-analysis pass on top of routing.
- Collapsing routing output to one surface/subsystem pick.
- Presentation shape as separate execution architecture.
- Silent driver transitions.
- Silent abandonment of in-flight runs.
- Single-active-stream-per-conversation assumption.
- Presentation customization mutating the work model.
- Hardcoding configurable lifecycle/creation/promotion/presentation behavior.
