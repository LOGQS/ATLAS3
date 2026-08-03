# Automation and Triggers

## Status

Canonical. This file defines the `Automation` and `Trigger` primitives, the one `Scheduler`, and the contracts by which non-interactive work is defined, fired, gated, executed, and observed. It realizes the Trigger rail kind that `controlrail.trigger-rail` (File 26 §11) frames and delegates, the automation-reuse path that `run.automation-reuse` (File 04 §26) declares, the intent-thread attachment that `intent.intent-thread` (File 02 §5.4) and `intent.consequences-for-later-specs` (File 02 §10) require for non-user-originated runs, the `AutomationTrigger` tool-surface lens that `surface.presentation-in-user-facing-surfaces` (File 07 §12) pins, and the scheduling, watch, eligibility, enablement, missed-trigger, and non-interactive-execution-safety mechanics that every per-surface spec (Files 27 §23, 28 §12, 29 §17.4, 30 §17.4, 31 §2.8/§23, 32 §12/§23) defers here. It introduces the net-new primitives those files reference without owning: the `Trigger`, the closed `TriggerKind` taxonomy, the `Automation` object, the `Scheduler`, the `WatchPolicy`, and the non-interactive-execution posture. It is the first post-surface spec: horizontal and surface-neutral, the way `worksurface.work-surface` (File 25) and `controlrail.chosen-model` (File 26) are. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `Automation` — a durable, registered, versioned, parameterized binding of one or more `Trigger`s to a pinned task template, with a world selector, capability scope, policy and approval requirements, validation policy, failure handling, and output contract; the crystallization of a reusable operation, realizing `run.automation-reuse` (File 04 §26)'s preservation set and `codex_recommendations.md` §9.3's automation-object contract
- the `Trigger` — the durable, typed firing-condition object the `Scheduler` and the world model detect, and whose firing flows into the system through the Trigger rail (`controlrail.trigger-rail`, File 26 §11)
- the closed-canonical `TriggerKind` taxonomy (`Schedule`, `Event`, `WorldCondition`, `Webhook`, `Manual`) plus the `Custom { namespace, name }` extension, and its mapping to the routing `trigger_kind` discriminator (`routing.trigger-kinds-routing`, File 03 §2.1)
- the `RecurrenceRule` contract and the **event-first timing rule**: a `Schedule` trigger computes its next-fire instant as a pure function and arms a single timer to that instant; it never busy-polls a clock, honoring `core.event-first-by-default` (File 01 §7.15) and `world.consequences-for-later-specs` (File 18) — current time is grounding, not a scheduler
- watch evaluation: the `WatchPolicy` (edge-versus-level firing, reset condition, deduplication, debounce/coalescing, hysteresis), event-first over `world.watch` (File 18 §13.1) and perception change signals (File 19 §8), with a flagged polling fallback only where a source emits no change events
- the one `Scheduler` substrate service — arming, next-fire computation, atomic claim, overlap arbitration, and missed-fire reconciliation — realized as the canonical scheduler and watch-poller background workers (`ledger.app-event-catalogue`, File 10 §5), owning detection and never execution
- the **automation run model**: a fired trigger resolves to a `RouteRequest` (`controlrail.input-resolution`, File 26 §4), routes through `routing.dispatch-pipeline` (File 03 §3), and executes as an ordinary `Run` (`run.run`, File 04 §2.3) — background execution is not a separate architecture; the intent-thread attachment for non-user-originated runs; the automation target conversation
- eligibility and enablement: the deterministic gate chain, the world selector as the availability evaluator (`world.state-aware-capability-availability`, File 18 §9) evaluated at fire time, rate limiting, cooldown, cold-start guarding, and the recursive-trigger cycle guard
- **non-interactive execution safety**: the stronger-not-weaker posture — a fire that needs a human decision parks and notifies rather than auto-approving; typed-confirmation and `Denied`-floor capabilities never execute unattended (`policy.permission-floor-typed-confirmation`, File 06 §7)
- overlap and concurrency (`OverlapPolicy`), failure handling and retry (declared over `provider.transport-level-retry-backoff`, File 17 §11 and `run.error-handling`, File 04 §20), validation policy and output contract (declared over `artifact.validation-critique`, File 09 §14 and `run.termination`, File 04 §22)
- the creation paths — graduation from a successful run (primary), natural-language creation, manual construction, and promotion from a macro or workflow template — and the no-silent-creation rule
- run history and the observability/consumption contract the dashboard and widgets read; the surface-aliasing rule that makes `sys.schedule.*`/`sys.monitor.*`, web page monitors, teacher review-due/scheduled-study monitors, GUI scheduled tasks, and data-source monitors `Automation`s over the one scheduler
- the `automation.*` capability surface, the automation event vocabulary, the persistence/locality/portability contract, the settings dimensions, the explicit rejections, and the consequences for later specs

This file does not define:

- the Trigger rail kind, the `RailResolution` set, or the rail-to-`RouteRequest` resolution mechanics — File 26 owns those; this file owns the `Trigger` object the rail carries and the detection that produces a fired signal
- routing, the `RunIntent` field set, deterministic prechecks, pin-through behavior, or reroute mechanics — File 03 owns those; an automation produces a `RouteRequest` and pins fields, routing produces the decision
- the run lifecycle, the capability-call pipeline, child-run isolation, intervention, cancellation, budgets, stuck detection, or the `run.automation-reuse` proposal trigger — File 04 owns those; this file specifies the automation object the proposal yields and how a fired run is built
- the event envelope, the `AppEvent` catalogue, hook dispatch, the durable ledger, the audit overlay, background-worker registration, or which events become durable entries — File 10 owns those; this file names the automation events and consumes the bus and workers
- the `WorldModel`, `WorldEntity`, `world.watch`, the durability tiers, the availability evaluator, or `WorldSnapshot` resolution — File 18 owns those; this file consumes the watch subscription and the availability predicate as the world selector
- the perception sensors, the capture pipeline, the change-detection signals, or the capture trigger model — File 19 owns those; this file consumes perception change signals and introduces no parallel watcher layer
- the policy evaluation algorithm, effective tier resolution, leases, approval flows, typed-confirmation, `auto-decide`, or reusable-policy rules — File 06 owns those; this file specifies how an automation pre-authorizes capability scope and how a fire that needs a human decision behaves
- the capability declaration field set, the registry, identity, versioning, or runtime registration — File 05 owns those; this file declares the `automation.*` capabilities as canonical built-ins
- the reusable workflow or template **body**, parameterization grammar, template composition, or the template library — File 34 (Workflows, Templates, and Reuse) owns those; an `Automation` references a task template (a pinned `RunIntent`, a workflow identity, or an inline prompt), it does not own the workflow body
- the version graph, sibling-block versioning, the materialized view, or snapshot resolution — File 11 owns those; an automation definition is a versioned entity over them
- the storage substrate, on-disk layout, the syncable-versus-device-local partition, the sync transport, conflict resolution, or the portable bundle format — Files 20 and 21 own those; this file specifies what is durable, what is device-local, and what is portable
- the secret vault, credential lifecycle, the trust model, encryption, egress governance, the untrusted-content rule, or webhook/MCP transport mechanics — Files 22 and File 36 (MCP and External Integrations) own those; this file specifies the trust posture of an inbound trigger and references the vault
- the sandbox, isolation tiers, process control, killability, or the elevated helper — File 23 owns those; an automation declares a sandbox profile by reference
- per-surface workflows, the surface-specific monitor presentations, or the per-surface capability families — the per-surface specs (27–32) own those; this file owns the one scheduler they alias over
- UI rendering — the automations dashboard layout, the schedule editor, the trigger-config pane, widget chrome, notification presentation, and accessibility — File 37 and File 38 own those; this file specifies the data and resolution contracts they consume
- quality-control validators, evaluation harnesses, or completion-check internals — File 09, File 04 §22, and File 39 own those; an automation's validation policy selects among them

## Source Resolution

Families reviewed: the prior ATLAS3 scheduling specbase (`systems/19-scheduling-pipeline.md` §19.1–§19.4 — `TimeTrigger`/`FileChangeTrigger`, `ScheduleAction`, `schedule_create`/`_list`/`_delete`/`_test_trigger`, `SessionKind::Automated`, `ScheduledExecutionLog`, self-invocation with the max-10/min-1-hour governance, workflows-as-unified-DAG, the every-1-minute scheduler check and debounce/loop constraints; `systems/README.md`); the unit recommendations (`unit14-systems.md` D14.SP.1 per-profile default workflows, D14.SP.2 single-scheduler alignment with `sys.schedule.create` as alias and the `system_scheduled_tasks`→`scheduled_tasks` rename, D14.SP.3 the `automations.create` natural-language alias with parsing examples, D14.SP.4 data-processor nodes as `NodeKind::Custom`, D14.SP.5 macro-to-workflow conversion and plugin-bundled workflows; `unit11-cross-tool-learning.md` CT.9 the `automations.create`/`ScheduleSpec { VEVENT | RelativeOffset | NaturalLanguage }` alias, CT.16 the verification-step policy, CT.21 thoroughness propagation; `unit11c-system-agent.md` the `ScheduledTask`/`TaskTrigger { Cron | Interval | Once | OnEvent | OnMetric | Manual }`/`TaskAction { RunScript | InvokeTool | SpawnChat | RunMacro }` model, `sys.schedule.*`/`sys.monitor.*` families, `system_watches`, the `system_monitor` poller, default watches, `ThresholdCrossed` events, the eleven-stage pipeline, recursive trigger chaining; `unit11a-memory.md`/`domains/memory/overview.md` the sleeptime `AgentTurnCompleted` event trigger and consolidation cadence with idle-trigger and debounce; `unit11b-data-processor.md`/`unit11d-teacher.md` the data-source monitor and the spaced-repetition review-due trigger; `unit12-infrastructure.md` the `system_scheduled_tasks`/`system_watches` SQL schema, the `macros.trigger_kind`, the watch-poller and scheduled-task-runner background workers, the per-device-versus-opt-in-sync classification, and the webhook receiver; `unit13-ui.md` the `SystemScheduledTasksPanel` and the `sys.schedule` tool-display entry); the strategic target-state review (`codex_recommendations.md` §9.3 the automation-object contract and the "crystallize successful work" framing, §8.11 Workflow Studio, §12 step 13 "automation suggestions from successful structure," §14.6 `ExecutionRun.trigger_kind`, §8.10 the System Agent inspector, §13.1 `AutomationService`); the ATLAS3 core (`atlas3-core/TODO.md` §19 the `scheduled_triggers`-points-at-`dag_configs` architecture, the three creation paths, file-system monitoring, execution hooks; `atlas3-core/CONSTRAINTS.md` §7b settings-over-constants, §11 the event contract, §12 block-first/no-parallel-tables, §14 portable-everything; `conversation/06-chat-dag.md` `DagContext::ScheduledWorkflow` and the one-DAG-executor statement; `infrastructure/database.md` `dag_configs`/`dag_presets`/`dag_node_output_cache`/`hooks`/`approval_policy` and the deliberately-absent `tasks` table; `infrastructure/lifecycle.md` background-task spawning; `cross-cutting/events.md` the `AppEvent`/`SubscriptionMode`/`hooks.toml` bus; `infrastructure/errors-and-retry.md` the retry strategies and circuit breaker; `systems/18-quality-control.md` the `QualityControlPolicy` and blocking validators; `systems/17-agent-self-modification.md` the no-silent-registration rule; `domains/system-agent/overview.md` the scheduled-tasks capability, process-restart watch, save-as-template, and rate-limiting-against-loops; `domains/web/05-advanced-features.md`/`unit09-web.md` the `ScreenShareSession` interval monitor, the `Macro`/`MacroParameter` recording-and-parameterization, and the fifteen-watchdog `BrowserWatchdog { listens_to, emits }` catalogue with coalescing/loop-detection/threshold patterns; `domains/data-processor/overview.md` the save-as-template graduation and the batch timeout; `kuzeys-ui-customization-and-widgets-addendum.md` §8 widgets as ambient interfaces to automation output); the external ecosystems (`chatgpt_tool.md` the `automations` tool with iCal VEVENT+RRULE and relative-offset, create/update/list, `enabled`/`disabled`, cross-conversation persistence, and the explicit "cannot do arbitrary background labor" boundary; `codex_tool.md` the `rrule` automation directive, TOML-per-automation storage, supported schedule shapes, and "run timing state lives elsewhere"; `claude_code_tool.md` the `CronCreate`/`CronDelete`/`CronList` five-field-cron/recurring/durable/idle-only-firing/auto-expiry/jitter model and `RemoteTrigger`; `claude_cowork_tool.md` `create_scheduled_task`/`list`/`update` with local-time cron, one-shot `fireAt`, `enabled`, and `notifyOnCompletion`; `claude_tool.md` `ask_user_input_v0` and the Google-Calendar surface); and the wider repository corpus on schedulers, watchers, daemons, retry, and overlap (`n8n` Triggers/Pollers/Webhooks, `ScheduledTaskManager` leader-only firing with jitter, the `ConcurrencyControlService`, the `DataDeduplicationService`, waiting-webhook resume, and the missed-trigger startup check; `multica`/`multica-2` the `autopilot`/`autopilot_trigger`/`autopilot_run` schema, the `concurrency_policy { skip, queue, replace }`, the `create_issue`/`run_only` execution modes, the 30-second claim-and-advance scheduler, and the retryable-reason set; `agent-zero` the cron/planned/ad-hoc task types and the debounced file-watchdog; `bytebot` the `IMMEDIATE`/`SCHEDULED` task lifecycle, `scheduledFor`, the `control` field, and the `isProcessing` skip flag; `open-cowork` the `ScheduledTaskRow` daily/weekly/interval config; `goose` the `SchedulerTrait` and `SessionType::Scheduled`/`SessionExecutionMode::Background`; `gemini-cli` the scheduler state machine, the `ApprovalMode`, the `interactive` policy-rule field, and the confirmation bus that parks headless; `archon` the DAG workflow engine with loop/approval nodes, trigger rules, the fail-closed `when:` evaluator, and the `FATAL`/`TRANSIENT`/`UNKNOWN` retry tiers; `open-swe` the message-queue park/defer and the after-agent output safety-net; `evolver` the idle-state-aware scheduler, the typed-backoff retry state machine, signal deduplication/saturation, the failure-streak circuit, and the multi-gate self-action eligibility; `operator-use`/`hermes` the cron subsystem, file-based lock ownership, the `[SILENT]`/`no_agent` watchdog mode, the unattended-context hint, the kanban dispatcher with stale-lock reclaim and `task_runs` attempt history, and watch-pattern rate limiting; `warp` the passive-suggestion world-state triggers and the file-change debounce; `langflow`/`deer-flow`/`cosight`/`swarms`/`autogen` loop/condition/concurrency/cycle-exit patterns; `grepai`/`memsearch`/`files/file-management.md` the debounced file watcher; `space-agent` the adaptive-cooldown debounce ladder).

Resolution rule: this file realizes and introduces; it does not re-own. The run model, child runs, intervention, cancellation, budgets, and the automation-reuse proposal stay File 04's; routing, `RunIntent`, and pin-through stay File 03's; the Trigger rail, the rail resolution, and the elicitation rail stay File 26's; the policy engine, leases, approval flows, typed-confirmation, and reusable-policy rules stay File 06's; the world model, `world.watch`, and the availability evaluator stay File 18's; the perception sensors and change signals stay File 19's; the event bus, the ledger, the audit overlay, and the background-worker registration stay File 10's; the capability declaration and registry stay File 05's; the version graph stays File 11's; storage, locality, sync, and portability stay Files 20 and 21's; the secret vault, trust, and egress stay File 22's; the sandbox stays File 23's; the reusable workflow body stays File 34 (Workflows, Templates, and Reuse)'s; webhook and MCP transport stay File 36 (MCP and External Integrations)'s. This file owns the `Automation` object, the `Trigger` object and its closed taxonomy, the one `Scheduler`, the `WatchPolicy`, the eligibility-and-enablement gate chain, the non-interactive-execution-safety posture, the overlap and failure-handling and validation/output-contract declarations on an automation, the creation-and-graduation paths, and the surface-aliasing rule.

Resolved tensions:

- **A cron scheduler, a workflow-trigger system, or an automation-graduation path.** `codex_recommendations.md` §9.3 names exactly these three options and resolves toward graduation: "the best automation system is not mainly about time triggers; it is about crystallizing successful work into reusable operators." A cron-only system is too narrow — the corpus is unanimous that triggers are multi-kind (time, event, condition, webhook, manual) and that the durable object is a saved, parameterized, policy-bound operation, not a shell line on a clock. A workflow-trigger system captures the binding but misses the graduation insight. This file adopts the unified `Automation` object that subsumes all three: the object preserves exactly the seven fields `run.automation-reuse` (File 04 §26) lists; graduation from a successful run is the primary creation path; and the trigger taxonomy and scheduler are the mechanics underneath. No option's value is lost.
- **One scheduler, or a scheduler per surface.** The specbase scattered scheduling across `sys.schedule.*` (System Agent), web page monitors (File 28 §12), teacher review-due/scheduled-study (File 30 §17.4), GUI scheduled tasks (File 31 §2.8/§23), data-source monitors (File 29 §17.4), and memory consolidation cadence. `unit14-systems.md` D14.SP.2 already collapses these onto one scheduler with `sys.schedule.create` as a thin alias, and every per-surface spec's Consequences defers the deep mechanics here with the explicit instruction that those surface schedulers are aliases over the one scheduler and the Trigger rail, never a parallel path. This file adopts the single-scheduler rule absolutely: there is one `Scheduler` and one Trigger rail; every surface scheduling concern is an `Automation` over them.
- **The Trigger object, or the Trigger rail.** `controlrail.trigger-rail` (File 26 §11) frames the Trigger rail as the non-interactive entry that resolves a fired signal to a `RouteRequest`, and delegates the deep mechanics here. The two layers are distinct and do not contradict: File 33 owns the `Trigger` definition and its detection (the `Scheduler` arming a timer, a watch subscription crossing true, a webhook arriving); when a trigger fires, the fired signal flows through the File 26 Trigger rail, which resolves it to a `RouteRequest`. The rail is the entry path; the trigger is what fires and why.
- **Polling versus event-first under a wall-clock trigger.** `core.event-first-by-default` (File 01 §7.15) forbids time-based polling unless unavoidable, and `world.consequences-for-later-specs` (File 18) requires that triggers be driven from explicit events and world-state changes, not from the world model's clock — current time is grounding, not a scheduler. Source schedulers poll on tight loops (one-second, thirty-second, one-minute). The resolution: `Event`, `WorldCondition`, and `Webhook` triggers are inherently event-first (they ride the event bus, `world.watch`, and inbound requests, with no polling). A `Schedule` trigger is the one case with no event to subscribe to, but it is still not a busy poll: the `Scheduler` computes the trigger's next-fire instant as a pure function and arms a single timer to that instant; the clock is read once to compute the deadline, not evaluated continuously as a condition. A periodic scan is a flagged, configurable fallback for coarse resolution or where a timer cannot be armed, never the default and never a correctness condition.
- **Automated runs as a separate execution architecture, or the one run model.** `systems/19-scheduling-pipeline.md` proposes `SessionKind::Automated`; `run.explicit-rejections` (File 04 §28) rejects "treating background work as a separate execution architecture," and `conversation/06-chat-dag.md` states that scheduled and event-triggered workflows that run headless "use the same DAG." This file resolves toward the one run model: a fired trigger produces a `RouteRequest` that routes and executes as an ordinary `Run` with `trigger_kind` `automation` or `external_event`; there is no automated session type and no parallel scheduler runtime.
- **A parallel automation/watch/run store, or the shared substrate.** `infrastructure/database.md` rejects a separate `tasks` table ("agent tasks are DAG executions") and `atlas3-core/CONSTRAINTS.md` §12 forbids parallel tables for substrate-owned objects; File 32 dissolves `system_scheduled_tasks`/`system_watches`/`system_audit_log` into the canonical substrate. This file follows the same posture: the `Automation` definition is a durable, versioned, block-backed entity (like an `Artifact` or a `MemoryEntry`), not a private table; automation runs are ordinary ledger runs; run history is a ledger projection; the firing state is device-local runtime state, never durable. No `automations`, `scheduled_tasks`, `system_watches`, `autopilot`, or `automation_runs` table is introduced.
- **Auto-approve unattended, or park-and-notify.** Source systems split: some auto-approve everything in a headless mode, others park. `policy.permission-floor-typed-confirmation` (File 06 §7) and the System Agent's stronger-not-weaker non-interactive posture (File 32 §12) are decisive: a non-interactive context cannot silently auto-approve a capability whose tier requires a human decision, and typed-confirmation and `Denied`-floor capabilities are never lifted by a lease or by `auto-decide`. This file adopts park-and-notify as the canonical posture, with auto-execution confined to exactly the capability scope the user pre-authorized for the automation through the ordinary lease mechanism.

## 1. Chosen Model

Anchor: `automation.chosen-model`

### 1.1 Definition

An `Automation` is a durable, registered, versioned, parameterized binding of one or more `Trigger`s to a pinned task template, together with a world selector, a capability scope, policy and approval requirements, a validation policy, a failure-handling policy, and an output contract. It is the canonical primitive for non-interactive work: the saved, reusable, inspectable operation the system performs when a firing condition is met, without a human at the keyboard.

A `Trigger` is the durable, typed firing-condition object attached to an `Automation`. The `Scheduler` and the world model detect when a `Trigger`'s condition is met; the firing flows into the system through the Trigger rail (`controlrail.trigger-rail`, File 26 §11) as a `RouteRequest`.

The `Scheduler` is the one substrate service that arms timers for `Schedule` triggers, subscribes watch and event triggers to their sources, claims due triggers atomically, arbitrates overlap, and reconciles missed fires. It owns detection; it never owns execution.

### 1.2 Purpose

The system's value compounds when successful work becomes reusable. A user who has the agent summarize their unread mail once should be able to crystallize that into a recurring operation; a research session that succeeded should be promotable to a watch that re-runs when a source changes; a system-maintenance sequence that worked should become a scheduled task. The automation layer is how transient runs become durable operators, and how the system acts on the user's behalf while unattended — safely, observably, and under exactly the authority the user granted.

The reframe is load-bearing: automation is **not** primarily a clock that runs scripts. It is the crystallization of intent into a saved, policy-bound, validatable operation, fired by a small closed set of trigger kinds, executed through the one run model, gated by the one policy layer, and grounded in the one world model.

### 1.3 Rule

- There is one `Automation` primitive, one `Trigger` primitive, and one `Scheduler`. No subsystem, surface, or plugin introduces a parallel scheduler, a private watch store, a private trigger taxonomy, a private automation table, or a separate non-interactive execution path. Every scheduling, monitoring, and reactive-automation concern across the system is an `Automation` over this layer.
- An `Automation` is built over the shared substrate and reuses it without reimplementing it: its definition is a versioned entity over `block.block` (File 08) and the version graph (File 11); its triggers fire through the Trigger rail (File 26) and route through `routing.dispatch-pipeline` (File 03); each fire executes as a `Run` (File 04); its capability scope is granted and enforced through the policy layer (File 06); its world selector is the availability evaluator (File 18 §9); its event-driven and watch triggers ride the event bus and `world.watch` (Files 10 and 18); its history is a ledger projection (File 10).
- Background and non-interactive execution is not a separate architecture (`run.explicit-rejections`, File 04 §28). A trigger-originated run uses the same run model, the same policy, and the same ledger as a user-originated run; the only differences are the `trigger_kind`, the absence of an interactive human, and the pinned, pre-authorized scope under which it runs.
- Detection is event-first. The only legitimate time-driven mechanism is a single armed timer per `Schedule` trigger's computed next-fire instant; tight clock-polling is rejected, and a periodic scan exists only as a flagged configurable fallback (§3).

### 1.4 Boundary

This file owns the `Automation`, the `Trigger` and its taxonomy, the `Scheduler`, the `WatchPolicy`, eligibility and enablement, non-interactive safety, overlap, failure handling, validation/output-contract declarations, the creation and graduation paths, and the surface-aliasing rule. It does not own the run model, routing, the rail, policy, the world model, perception, the event bus, the version graph, storage, the workflow body, or webhook transport — those are realized through their owning files.

## 2. The `Trigger` Primitive and the `TriggerKind` Taxonomy

Anchor: `automation.trigger`

### 2.1 Definition

A `Trigger` is a typed firing-condition object. Each `Trigger` declares its `TriggerKind`, the kind-specific condition fields, an `enabled` flag, a `missed_fire_policy` (§3.4), and the optional `WatchPolicy` (§4) for condition triggers. An `Automation` carries one or more `Trigger`s; firing any enabled trigger initiates the automation's run, subject to the eligibility gate chain (§8).

### 2.2 The Closed `TriggerKind` Catalogue

The canonical `TriggerKind` set is closed, with a registered-extension mechanism:

- `Schedule` — fires at a computed instant. Carries a `RecurrenceRule` (§3). Subsumes one-shot timestamps, elapsed intervals, daily/weekly schedules, cron expressions, and recurrence rules.
- `Event` — fires when a typed event matching a declared filter is observed on the event bus (`ledger.event-stream`, File 10 §5). The event may be an internal `AppEvent` (a run completing, a file changing on disk per `block.streaming-commit-boundary` File 08 §7, an agent turn completing, a setting changing) or a perception change signal (`perception.output-contract`, File 19 §9). Subsumes file-change events, session-lifecycle triggers, the sleeptime post-turn trigger, and "when X happened" reactive triggers.
- `WorldCondition` — fires when a `WorldPredicate` over the resolved `WorldSnapshot` crosses into satisfaction (a watch or monitor). Carries the predicate and a `WatchPolicy` (§4). Subsumes metric thresholds, resource and liveness monitors, page-changed and data-source-changed monitors, file-exists conditions, and review-due conditions.
- `Webhook` — fires when an authenticated inbound request arrives at a registered endpoint (§5.2). Subsumes external-system callbacks and integration triggers.
- `Manual` — fires only on explicit invocation (run-now). An `Automation` whose only trigger is `Manual` is a saved, parameterized, policy-bound operation invoked on demand (§7.2).
- `Custom { namespace, name }` — a source-registered trigger kind, admitted through the proposal-first source-approval path (`policy.source-approval-flow`, File 06 §9), declaring how its condition is detected over an existing substrate (the event bus, `world.watch`, or an inbound channel). A `Custom` trigger kind may not introduce a parallel detection mechanism; it composes the existing ones.

A `Custom` trigger-kind registration must declare its owning source and trust state; detection substrate; event or predicate schema; payload authority class and default sensitivity; idempotency and `fire_id` derivation; locality requirements; consumed settings keys; whether it can arm device-local resources; and the capability scope required to register and enable it. A registration that cannot express detection through an existing substrate is rejected.

Every `Automation` is implicitly invocable through a manual run-now path regardless of its declared triggers; the `Manual` kind names the case where manual invocation is the *only* firing condition.

### 2.3 Mapping to the Routing `trigger_kind`

The `routing.trigger-kinds-routing` (File 03 §2.1) discriminator is coarser than the `TriggerKind` taxonomy and the two are distinct layers. When a `Trigger` fires, the resulting `RouteRequest` carries the routing `trigger_kind`:

- `Schedule`, `Event` (internal `AppEvent`), `WorldCondition`, and `Manual` map to routing `trigger_kind` `automation`.
- `Webhook`, and `Event` triggers bound to an external operating-system or integration event, map to routing `trigger_kind` `external_event`.

The fired-trigger frame carries `automation_id`, the automation-owned `trigger_id`, `fire_id`, `source_event_id` when the source supplied one, and the routing `trigger_kind`. `trigger_id` always identifies the automation's trigger; `source_event_id` identifies the inbound event or delivery.

A manual run-now fired by the user is attributed to the user invoker (`cross-cutting/actions.md`'s invoker distinction) while still routing as `automation` against the automation's pinned template.

### 2.4 Rule

- The `TriggerKind` set is closed-canonical-plus-`Custom`. A new trigger kind is a registered extension over an existing detection substrate, never a new detection mechanism.
- A `Trigger` declares its condition declaratively; the `Scheduler` and the world model detect satisfaction. A `Trigger` does not embed execution; firing produces a `RouteRequest`, and execution is the run model's (§10).
- Each `Trigger` carries its own `enabled` flag independent of the owning `Automation`'s enablement, so a multi-trigger automation may have some triggers active and some paused.

### 2.5 Boundary

This section owns the `Trigger` object and its taxonomy. File 26 owns the rail the fired trigger flows through; File 03 owns the routing discriminator; Files 10, 18, and 19 own the detection substrates a trigger composes.

## 3. `Schedule` Triggers, Recurrence, and the Event-First Timing Contract

Anchor: `automation.schedule-trigger`

### 3.1 Definition

A `Schedule` trigger fires at a computed instant. It carries a `RecurrenceRule`: `Once { at }`, `CalendarLocal { rule, timezone, dst_policy }`, or `ElapsedDuration { duration, anchor }`. The `rule` is a typed, provider-format-invariant recurrence specification. If a user omits timezone for a calendar-local schedule, creation resolves the user's current timezone to a concrete timezone identifier and stores it.

### 3.2 The `RecurrenceRule` Contract

- The canonical contract is the typed recurrence and its next-fire semantics, not any concrete grammar. Cron expressions, iCalendar recurrence rules, structured daily/weekly specifications, and relative offsets are encodings behind the contract.
- `CalendarLocal { rule, timezone, dst_policy }` is for human schedules such as weekdays at 9am. Nonexistent local times and repeated local times resolve by `dst_policy`.
- `ElapsedDuration { duration, anchor }` is for intervals such as every six hours after the prior fire or after completion. It is elapsed-duration semantics, not wall-clock recurrence.
- A natural-language description, when an automation is created from one (§15), is preserved as display metadata alongside the typed rule so the user sees "every weekday at 9am," not the encoded form. The natural-language-to-rule conversion is a creation-time convenience (§15.1), never the runtime representation.

### 3.3 The Event-First Timing Rule

- A `Schedule` trigger does not busy-poll a clock. The `Scheduler` computes the trigger's next-fire instant and arms a single timer to that instant; when the timer elapses, the trigger fires and the next instant is recomputed and re-armed. The clock is read to compute a deadline, not evaluated continuously as a condition. This honors `core.event-first-by-default` (File 01 §7.15) and `world.consequences-for-later-specs` (File 18) — current time is grounding, not a scheduler.
- A periodic scan of due schedules is a flagged, configurable fallback, used only where the platform cannot arm a precise timer or where coarse resolution is acceptable. The fallback is never the default and is never a correctness condition; missing a scan must never silently drop a fire (§3.4).
- Jitter is permitted and recommended for recurring schedules to avoid synchronized firing of many automations at round instants; the jitter window is a setting. Jitter shifts the armed instant; it does not turn the timer into a poll.

### 3.4 Missed-Fire Handling

The machine may be off or the application closed when a `Schedule` trigger was due. There is no guaranteed delivery while powered down. Each trigger declares a `missed_fire_policy`:

- `RunOnce` — on the next startup, fire once for the missed window, coalescing multiple missed recurring occurrences into a single catch-up fire. The default for `Once` triggers and the default for recurring triggers.
- `Skip` — do not fire for the missed window; compute and arm the next future instant. An override for a recurring trigger whose repeated catch-up firing would be redundant or harmful, where `RunOnce`'s single coalesced catch-up is unwanted.
- `RunAll` — fire once per missed occurrence. Gated behind a setting and a per-automation opt-in, because it can produce a burst; subject to the rate limit and overlap policy (§12, §8.4).

On startup, the `Scheduler` reconciles: it computes which triggers were due during the downtime, applies each trigger's `missed_fire_policy`, and records each reconciled or skipped fire with its original due instant for audit. A cold-start guard (§8.4) bounds the startup burst.

### 3.5 Rule

- Next-fire is a pure deterministic function of the rule, its time semantics, timezone when applicable, and last-fire instant; it is recomputed after each fire and after any edit to the rule.
- A `Schedule` trigger arms a single timer; it does not poll. The periodic-scan fallback is flagged and configurable.
- Missed fires are reconciled at startup per the declared policy and recorded, never silently dropped.

### 3.6 Boundary

This section owns the recurrence contract, the timer-arming rule, and missed-fire reconciliation. The wall-clock and timezone facts are world-model grounding (File 18 §6); the timer primitive and background-worker placement are the `Scheduler`'s (§9) over the background-worker task model realized by Files 10 and 42.

## 4. `WorldCondition` Triggers and Watch Evaluation

Anchor: `automation.watch`

### 4.1 Definition

A `WorldCondition` trigger — a watch or monitor — fires when a `WorldPredicate` over the resolved `WorldSnapshot` (`world.world-snapshot-replay`, File 18 §10) crosses into satisfaction. The predicate is the same `requires`/`blocked_by` clause grammar the availability evaluator uses (`world.state-aware-capability-availability`, File 18 §9), evaluated against world-model facts: a metric crossing a threshold, a process or session liveness fact, a file or workspace state, an observed page or data-source fingerprint, a temporal-or-resource condition, or a registered custom world fact.

### 4.2 Event-First Watch Evaluation

- A watch subscribes to the change events of the facts its predicate references, through `world.watch(scope, filter)` (File 18 §13.1) and the perception change signals (`perception.triggers`, File 19 §8). It re-evaluates its predicate when a referenced fact changes; it does not poll. This consumes the world model's reactivity contract (`world.state-change-events-reactivity`, File 18 §12) and introduces no parallel watcher layer (`perception.consequences-for-later-specs`, File 19).
- A watch whose source emits no change events may declare a flagged, configurable poll interval, consistent with perception's capture-on-interval fallback (File 19 §8). The interval is a setting, never a hardcoded constant (`settings.explicit-rejections`, File 15 §20), and never a correctness condition.

### 4.3 The `WatchPolicy`

A `WorldCondition` trigger carries a `WatchPolicy` governing how predicate satisfaction translates to fires:

- `firing_mode` — `Edge` (fire once when the predicate crosses from unsatisfied to satisfied; the default) or `Level` (fire on each evaluation while the predicate remains satisfied; gated, because it can fire repeatedly).
- `reset_condition` — when an edge-mode watch re-arms: when the predicate returns to unsatisfied, or after a cooldown, or on an explicit reset event. An edge watch does not fire again until it has reset.
- `hysteresis` — for metric predicates, separate arm and reset thresholds, so a value oscillating around one threshold does not produce a burst of fires.
- `dedupe_key` and dedupe window — a key derived from the firing context; fires with the same key within the window are suppressed as duplicates.
- `debounce` window — a coalescing delay; change events arriving within the window collapse into a single fire, so a burst of underlying changes (a build touching many files, a rapid sequence of storage writes) produces one run rather than many. Debounce coalesces the candidate fires produced by per-change evaluations; it does not replace those evaluations with trailing end-state sampling — a crossing observed at its change position is coalesced, never erased by a later state inside the window.

All thresholds, intervals, windows, and cooldowns are settings (`settings.explicit-rejections`, File 15 §20), resolvable per automation, per surface, and globally through `settings.source-stack-resolution` (File 15 §6).

### 4.4 Rule

- A watch is event-first over `world.watch` and perception change signals; the poll interval is a flagged fallback only where no change events exist.
- The default firing mode is `Edge` with a reset condition; `Level` mode is gated and explicitly opted into.
- Bursty change sources are coalesced through the `debounce` window and deduplicated through the `dedupe_key`; a watch never produces an unbounded fire stream from a single underlying change.
- Predicate evaluation is the world model's; the watch composes the evaluator and the subscription, it does not re-derive world state.

### 4.5 Boundary

This section owns the `WatchPolicy` and the watch-firing semantics. File 18 owns the predicate grammar, the `world.watch` subscription, and the availability evaluator; File 19 owns the perception change signals; File 10 owns the bus the watch subscribes to.

## 5. `Event` and `Webhook` Trigger Detail

Anchor: `automation.event-and-webhook-triggers`

### 5.1 `Event` Triggers

- An `Event` trigger declares an event filter over the `AppEvent` catalogue and registered `Custom` events (`ledger.app-event-catalogue`, File 10 §5.3 and §4.3) and optionally over perception change signals. When a matching event is observed, the trigger fires with the event payload as the routing-frame trigger context (`routing.routing-frame`, File 03 §3.1).
- An `Event` trigger subscribes through the canonical event bus as a non-blocking subscriber (`ledger.event-stream`, File 10); it never blocks the emitter and never becomes a hook that gates other work. The distinction from a hook is firm: a hook participates in an in-flight decision; an `Event` trigger launches new work in response to an observed event.
- File-change triggers are `Event` triggers over the filesystem-watcher events (`workspace.disk-sync-loop`, File 24 §12 and `block.streaming-commit-boundary`, File 08 §7), carrying the path-glob and the change-kind filter, and inheriting that loop's debounce-as-coalescing; this file declares no parallel file watcher.

### 5.2 `Webhook` Triggers

- A `Webhook` trigger registers an inbound endpoint. The binding is local-only by default; remote binding is opt-in and requires authentication. The supported authentication shapes (a signature scheme, a bearer token, basic credentials) verify the request before the trigger fires; the verifying secret is a vault reference (`security.secret-vault`, File 22 §5), never an inline value.
- An inbound payload becomes the routing-frame trigger context with routing `trigger_kind` `external_event`. The payload is untrusted content and carries no authority (`security.untrusted-content`, File 22 §12): it may parameterize the run, but it can never escalate the automation's capability scope or auto-approve a gated capability.
- A `Webhook` trigger declares how source deliveries produce a `source_event_id` and freshness or idempotency signal: provider event id, signed timestamp plus nonce, delivery id, or deterministic content key. Duplicate source deliveries map to the same `fire_id` and are recorded as duplicates, not re-run. Remote bindings require freshness validation appropriate to their authentication scheme. File 36 (MCP and External Integrations) owns concrete signature protocols; this file owns the no-duplicate-fire behavior.
- The endpoint binding and its verifying secret are device-local (§18). The transport mechanics — the listener, the protocol surface, the connector lifecycle — are File 36 (MCP and External Integrations)'s; this file owns the trigger's existence, its authentication requirement, and its trust posture.

### 5.3 Rule

- An `Event` trigger is a non-blocking bus subscriber that launches work; it is not a hook and never gates in-flight execution.
- `Webhook` triggers authenticate, validate freshness/idempotency, treat payloads as untrusted, and never grant authority from inbound content.
- File-change and perception-change triggers compose the existing watcher and sensor signals; no parallel watcher is introduced.

### 5.4 Boundary

File 10 owns the bus and the event catalogue; File 24 owns the filesystem watcher; File 19 owns perception signals; File 22 owns the trust and secret contracts; File 36 (MCP and External Integrations) owns webhook transport. This section owns how those signals become trigger fires.

## 6. The `Automation` Object

Anchor: `automation.automation-object`

### 6.1 Definition

An `Automation` is the durable object binding triggers to a pinned task template under a fixed set of governing fields. It is the realization of `run.automation-reuse` (File 04 §26)'s preservation set and `codex_recommendations.md` §9.3's automation-object contract.

### 6.2 The Field Set

An `Automation` carries:

- `automation_id` — stable identity; display name; optional description and the natural-language origin string.
- `triggers` — one or more `Trigger`s (§2), each independently enableable.
- `task_template` — the pinned task template (§6.3): the operation the automation performs when fired. It references a workflow through `SubWorkflowRef` (File 34 §3.4's reference-with-version-policy contract — `Pinned { workflow_version_id }` by default; `CurrentActive`/`LatestCompatible` only by explicit user opt-in or source-approved policy) or carries an inline prompt, with parameter slots. A task template never embeds a workflow body, and the fire-time `RunIntent` never carries one (File 34 §13.1's carriage split).
- `parameters` — typed parameter slots with source allowance, validation, default behavior, sensitivity policy, and authority class. Fire-time values bind only through declared slots.
- `world_selector` — the `WorldPredicate` (`world.state-aware-capability-availability`, File 18 §9) that must hold for a fire to proceed (§8.2): the conditions under which the automation is eligible to run at all (a workspace, a power state, a foreground application, a connection liveness).
- `capability_scope` — the capability families and touched-resource bounds the automation may use, expressed in the declared touched-resource grammar (`capability.touched-resources`, File 05 §6); the run's authority is confined to this scope.
- `policy` — the approval and lease requirements (§11): the pre-authorization the automation runs under and the posture for capabilities that exceed it.
- `validation_policy` — which validators and completion checks a run must satisfy to count as successful (§14.1).
- `output_contract` — what the run must produce and how the result is delivered (§14.2).
- `failure_handling` — the retry policy, the circuit-breaker policy, and the failure-notification policy (§13).
- `overlap_policy` — how a fire behaves when a prior run of this automation is still in flight (§12).
- `rate_limit` — the minimum interval and per-window fire cap (§8.4).
- `target` — the conversation or workspace a fired run attaches to (§10.3).
- `run_locality` — which device may fire and run this automation (§18.2).
- `enabled` — the master enablement flag; the source, trust state, and creation provenance.

### 6.3 Pin-at-Save-Time

- An `Automation`'s `task_template` is a saved execution template (`run.execution-structure`, File 04 §5.3's "automation run using a saved execution template") captured at save time. It pins the fields that routing would otherwise compute at fire time, so a later run is reproducible and not subject to drift: the primary surface and the recorded `surface_contract_version` (`worksurface.consequences-for-later-specs`, File 25), the `tool_surface_strategy` (`surface.presentation-in-user-facing-surfaces`, File 07 §12), the pinned model selection as a `PinnedModelSelection` (§6.3.1), the context and compaction policy (`context.context-policies`, File 13 §4), the sandbox profile (`sandbox.contract`, File 23 §3), and the budget (`run.budgets-limits`, File 04 §21).
- At fire time, the trigger produces a `RouteRequest` carrying the pinned template; routing respects the pinned fields and fills only the unpinned ones (`routing.trigger-kinds-routing`, File 03 §2.1). This is the single realization, for all surfaces, of the "pin the surface and its policies at save time the way routing does" rule that each per-surface spec defers here.
- Pinning is a snapshot for reproducibility, not an authority freeze. At fire time, the current capability registry, source trust, policy templates, leases, sandbox availability, model/provider availability, settings overlays, and security rules revalidate the pinned template. Later stricter policy wins. A pinned value may prevent silent rebinding, but it cannot preserve authority the user or policy revoked. Editing the automation re-pins; enabling after material policy drift may require review.
- A floating workflow reference (`CurrentActive`/`LatestCompatible`) is additionally revalidated at fire time for effect-envelope drift (File 34 §5.2): the runtime records the resolved workflow version and a drift notice when it differs from the save-time resolution, and recomputes the resolved workflow's declared effect envelope. When the resolved envelope exceeds the scope this automation was pre-authorized under (§11.2), the fire records the `EffectEnvelopeDrift` fact and parks for user review (§11.3), never running under stale authorization.

#### 6.3.1 `PinnedModelSelection`

A `PinnedModelSelection` is the constraint shape a saved template pins in place of a resolved model route. It records *what* was pinned, not an effective execution result: a `ModelRoute` (`routing.run-intent`, File 03 §4.3) is the effective result routing produces, and a `ResolvedModelSelection` (`model.model-selection-algorithm`, File 16 §7.2) is the in-memory pairing of a route with its selection record — a `PinnedModelSelection` is neither, but the saved constraint that model selection re-resolves into a route at fire time.

It carries:

- `provider_id` — optional
- `model_id` — optional
- `profile_id` — optional
- `fallback_policy_id` — optional
- `origin_selection_record_id` — provenance-only lineage: the `ModelSelectionRecord` (`model.model-selection-record`, File 16 §8) the pin was captured from, recorded for audit and never used as a live route reference or an identity channel

Its invariants:

- a `profile_id` or a `model_id` must be present; a pin that constrains neither is invalid.
- `provider_id` is never present without `model_id`.

At fire time the pinned selection is re-resolved through model selection (`model.model-selection-algorithm`, File 16 §7) into an effective `ModelRoute` under current availability, policy, and budget, exactly as any other pinned field is revalidated (§6.3): a pin cannot preserve a route the current registry, trust state, or policy no longer permits.

### 6.4 Identity, Versioning, and Source

- An `Automation`'s durable definition is a versioned entity over the registered `Custom { namespace: "automation", name: "definition" }` block/entity kind. File 33 owns the entity semantics; File 08 owns custom-kind registration and validation. Edits produce sibling versions, history is inspectable, and the definition is reconstructable. No private automation table is introduced.
- Automations have a source taxonomy mirroring capabilities (`capability.sourcing`, File 05 §9): built-in, user-defined, plugin-bundled (`unit14-systems.md` D14.SP.1/D14.SP.5 per-profile and plugin-bundled workflows), and graduated-from-run. Plugin-bundled and otherwise externally-sourced automations register through the proposal-first source-approval path (`policy.source-approval-flow`, File 06 §9) and carry the trust state their source confers.
- The source decides the invocation PRINCIPAL an autonomous fire carries into policy (`invoker_kind`, File 06 §11.2): a graduated-from-run body executes as `model_agent`, a plugin-bundled body as `plugin_runtime`, a user-defined or built-in body as `automation` — for every trigger kind alike (Schedule, Event, WorldCondition, Webhook, autonomous Custom; the trigger kind is fire provenance carried on the fired-trigger frame, §2.3, never a principal). A child workflow invoked within the fire takes the MORE RESTRICTIVE of the inherited parent principal and its own source-derived principal, the source-derived one winning ties — authority is never laundered upward through a wrapping automation or a parent body.

### 6.5 Rule

- An `Automation` carries exactly the governing fields above; the seven preservation fields of `run.automation-reuse` (File 04 §26) — trigger shape, required inputs, capability scope, policy requirements, validation requirements, output contract, failure handling — are all present and durable.
- The task template is pinned at save time and re-pinned on edit; fire-time routing fills only unpinned fields.
- The definition is a versioned entity, not a private table; the firing state is never part of the durable definition (§18).

### 6.6 Boundary

File 04 owns the `RunIntent` field set and the automation-reuse proposal; File 03 owns pin-through routing; File 07 owns the tool-surface strategy; File 34 (Workflows, Templates, and Reuse) owns the workflow body the template may reference; File 08 and File 11 own the block and version graph the definition lives in. This section owns the automation object that binds them.

## 7. Manual Invocation and Saved Operations

Anchor: `automation.manual`

### 7.1 Run-Now

Every `Automation`, regardless of its declared triggers, is invocable through a manual run-now path: the command rail, a slash command, a menu, an automation-dashboard control, or the `automation.run_now` capability (§19). A user-initiated run-now is attributed to `user_direct` and can resolve approvals interactively. A model, plugin, external protocol, or automation invoking run-now is attributed to its actual invoker kind and follows the non-interactive posture when no human is present. An AUTONOMOUS fire — any trigger kind firing without a human invoker — is attributed per the §6.4 source-derived principal rule; there is no separate invoker class per trigger kind. Run-now is the execution path for manual test fires.

### 7.2 The `Manual`-Only Automation

An `Automation` whose only trigger is `Manual` is a saved, named, parameterized, policy-bound operation with no automatic firing — a reusable operator invoked on demand. `Manual` names the absence of automatic firing, not a fixed authority level. The invocation's actual source determines approval posture; the pinned automation policy constrains the run in all cases.

### 7.3 Boundary with the Slash-Command and Menu Rails

A `Manual`-only `Automation` is distinct from a prompt-template slash command (`controlrail.slash-command-rail`, File 26 §8). A slash command is a prompt expansion or a direct capability binding with no governing policy of its own; an `Automation` carries a pinned scope, policy, validation policy, and output contract, and produces a managed run. A slash command or menu entry may invoke an `Automation` (the rail resolves to `automation.run_now`); the rail is the entry, the automation is the governed operation.

## 8. Eligibility, Enablement, and the World Selector

Anchor: `automation.eligibility`

### 8.1 The Eligibility Gate Chain

When a `Trigger` fires, the automation is evaluated against a deterministic gate chain before any run is built. The fire proceeds only if every gate passes:

1. the `Automation`'s `enabled` flag is set;
2. the firing `Trigger`'s own `enabled` flag is set;
3. the `world_selector` predicate is satisfied against the current `WorldSnapshot` (§8.2);
4. the `capability_scope` is still grantable — the automation's leases are valid and the pinned surface and capabilities are available (`world.state-aware-capability-availability`, File 18 §9), else the fire resolves to a typed unavailability;
5. the `target` conversation exists and accepts new runs, or can be auto-created (§10.3);
6. the `overlap_policy` permits a new run given any in-flight run (§12);
7. the `rate_limit`, cooldown, and global automation budget permit a new fire (§8.4);
8. the recursive-trigger cycle guard permits the fire (§8.5).

A fire blocked by any gate is recorded with the gate and reason as a skipped fire; it is never silently dropped (`perception.consequences-for-later-specs`, File 19's no-silent-cap discipline). The skipped-fire record carries the trigger, the gate, and the firing context for the dashboard (§17).

If the default dedicated automation conversation was deleted, the target gate recreates it. If a user-specified conversation is deleted, tombstoned, or otherwise unable to accept runs, the fire fails with `TargetConversationUnavailable { automation_id, target }`, records the typed reason, and notifies the user.

For every fire, the recorded firing context includes trigger-satisfaction evidence. For `WorldCondition`, that includes the predicate, transition direction, source change event, and `WorldSnapshot` used to decide the trigger fired. Eligibility then records the gate-evaluation snapshot used for the `world_selector`. If the trigger snapshot and gate snapshot differ, both are preserved and linked by `fire_id`.

### 8.2 The World Selector

- The `world_selector` is the automation's eligibility predicate over world state, expressed in the `requires`/`blocked_by` grammar of the availability evaluator (`world.state-aware-capability-availability`, File 18 §9). It is evaluated when the run is built: at fire time for an immediately dispatched fire, and re-evaluated against a fresh `WorldSnapshot` whenever the build is deferred — a fire dequeued from `Queue` after an in-flight run completes (§12.1), or a missed fire reconciled at startup (§3.4) — so a deferred build never runs against stale world state. The snapshot identity used for the deciding evaluation is recorded for replay (`version.snapshots`, File 11 §14).
- The world selector is how an automation declares the conditions under which it should run at all — on a particular workspace, on battery or AC power, when a connection is live, when a foreground application matches, when a device is idle. It is distinct from a `WorldCondition` trigger: the trigger fires on a condition crossing; the world selector gates whether any fire (from any trigger) proceeds. An automation may have both.

### 8.3 Enablement

- An `Automation` may be enabled, disabled (paused), or archived. Disabling preserves the definition and its history; it stops firing without deleting. Each `Trigger` may be independently disabled.
- Enablement and per-trigger enablement are user-controlled and agent-proposable (subject to policy); enablement state is durable and synced as part of the definition, while the armed timer and active subscriptions it implies are device-local runtime state (§18).

### 8.4 Rate Limiting, Cooldown, and Cold-Start

- Each `Automation` declares a `rate_limit`: a minimum interval between fires and an optional per-window fire cap. Rate-limit and cooldown accounting counts only fires admitted past the full gate chain (§8.1) — a fire that proceeds to build a run; a fire any gate blocks is recorded as a skipped fire (§8.1) and consumes neither the minimum interval nor the per-window cap. A system-wide automation budget bounds the total concurrent automation runs and the total fire rate across all automations; both are settings (`settings.explicit-rejections`, File 15 §20). These guard against runaway firing, consistent with the "rate limiting to guard against loops" posture (`domains/system-agent/overview.md`).
- A cold-start guard bounds the burst of fires at startup (from missed-fire reconciliation and re-armed schedules), so a long downtime or a clock jump does not produce a stampede.

### 8.5 The Recursive-Trigger Cycle Guard

An `Event` trigger may fire on an event that the automation's own run emits, producing a cycle. A cycle guard bounds this: an automation run that was itself trigger-originated carries its trigger lineage, and a fire whose lineage would exceed a configurable depth, or that would re-enter the same automation within a window, is blocked and recorded. Every event-trigger chain must have a bounding condition; an unbounded self-retriggering automation is rejected at save time.

### 8.6 Rule

- Eligibility is a deterministic gate chain; a blocked fire is recorded with its reason, never silently dropped.
- Trigger-satisfaction evidence and world-selector gate evidence are both recorded for replay and audit.
- The world selector is the availability evaluator at fire time, evaluated against a recorded snapshot for replay.
- Rate limits, cooldowns, the global budget, the cold-start guard, and the cycle guard are all settings-driven and enforced before a run is built.

### 8.7 Boundary

File 18 owns the predicate evaluator and the snapshot; File 06 owns lease validity; File 04 §21 owns the run budget the global automation budget composes with. This section owns the gate chain and the firing guards.

## 9. The `Scheduler`

Anchor: `automation.scheduler`

### 9.1 Definition

The `Scheduler` is the one substrate service that detects trigger firings and emits fired-trigger signals into the Trigger rail. It is realized as the canonical scheduler and watch-poller background workers (`ledger.app-event-catalogue`, File 10 §5's `BackgroundWorkerSpawned` set), spawned at startup within the application lifecycle and stopped gracefully at shutdown. It owns detection and arbitration; it never executes a run.

### 9.2 Responsibilities

- **Arming.** For each enabled `Schedule` trigger, compute the next-fire instant and arm a single timer (§3.3). For each enabled `WorldCondition` and `Event` trigger, establish the world-model subscription `world.watch` (`world.capability-surface`, File 18 §13.1) or bus subscription (File 10). For each `Webhook` trigger, register the inbound endpoint (§5.2).
- **Fire identity.** Every trigger occurrence has a deterministic `fire_id`. `Schedule` derives it from `automation_id`, `trigger_id`, scheduled due instant, and recurrence occurrence index. `Event` and `Webhook` derive it from `automation_id`, `trigger_id`, source event identity, and source-delivery idempotency data. `WorldCondition` derives it from `automation_id`, `trigger_id`, transition identity, and the recorded world snapshot or change-event identity.
- **Atomic claim.** When a trigger's condition is met, the `Scheduler` claims the `fire_id` atomically before emitting it, so a single fire is never dispatched twice. The claim also enforces the overlap policy's skip-if-running check (§12).
- **Next-fire advance.** After a `Schedule` trigger fires, recompute and re-arm the next instant; after a `WorldCondition` trigger fires, apply its reset condition before re-arming (§4.3).
- **Missed-fire reconciliation.** At startup, reconcile schedules that were due during downtime per each trigger's `missed_fire_policy` (§3.4), bounded by the cold-start guard (§8.4).
- **Emission.** Emit the fired-trigger signal — `automation_id`, `trigger_id`, `fire_id`, optional `source_event_id`, firing context, and routing `trigger_kind` — into the Trigger rail (`controlrail.trigger-rail`, File 26 §11), which resolves it to a `RouteRequest`.

### 9.3 Rule

- There is one `Scheduler`. No surface or plugin runs a parallel scheduler, watch poller, or daemon. The System Agent's `sys.schedule.*`/`sys.monitor.*`, web page monitors, teacher review-due and scheduled-study monitors, GUI scheduled tasks, data-source monitors, and memory consolidation cadence are all triggers and automations the one `Scheduler` arms (§16, §18.4).
- The `Scheduler` detects and arbitrates; it does not execute. Emission hands off to the rail, routing, and the run model.
- A claimed fire is recorded using `fire_id` as the idempotency key. Duplicate `fire_id`s link to the original recorded fire rather than producing a second run. Transient arming state — timers, subscription handles, active claims, next-fire and last-fire projections — is device-local runtime state, reconstructed at startup (§18).

### 9.4 Boundary

File 10 owns the background-worker registration and lifecycle, and the event bus emission flows through; File 26 owns the rail; File 18 owns the subscriptions; File 42 owns the worker scheduling primitives. This section owns the detection-and-arbitration service over them.

## 10. The Automation Run

Anchor: `automation.run`

### 10.1 Trigger to Run

A fired trigger becomes a run through the canonical path, with no parallel architecture:

1. the `Scheduler` emits the fired-trigger signal (§9.2);
2. the Trigger rail resolves it to a `RouteRequest` carrying the pinned `task_template` and the firing context (`controlrail.trigger-rail`, File 26 §11; `controlrail.input-resolution`, File 26 §4);
3. routing materializes a `RunIntent`, respecting the pinned fields and filling only the unpinned ones (`routing.trigger-kinds-routing`, File 03 §2.1), with the routing `trigger_kind` plus the fired-trigger identity tuple;
4. execution proceeds as an ordinary `Run` (`run.run`, File 04 §2.3), under the run model, the policy layer, the ledger, and the version-commit boundaries.

If the `task_template` references a workflow or pipeline, the run executes it through the one execution-graph model (`run.execution-structure`, File 04 §5 and `conversation/06-chat-dag.md`'s scheduled-workflow context), not a separate engine. The workflow body is File 34 (Workflows, Templates, and Reuse)'s; the run that executes it is File 04's.

### 10.2 No Separate Architecture

A trigger-originated run is an ordinary run distinguished only by its fired-trigger identity, non-interactive context, and pinned pre-authorized scope. There is no automated session type, no parallel scheduler runtime, and no separate background execution path (`run.explicit-rejections`, File 04 §28). Fire-time values bind into declared parameter slots (§6.2); raw payload interpolation is invalid.

Payload-derived values from `Webhook` and external events carry `untrusted_source_data` regardless of source trust. Invalid or missing required parameters resolve by the automation's non-interactive posture: park, skip, or fail with a typed reason. Trigger payloads cannot widen `capability_scope`, lower sensitivity, change policy, or inject undeclared instructions.

### 10.3 Intent-Thread Attachment and Target

- Every trigger-originated `RunIntent` attaches to exactly one primary intent thread that outlives its trigger (`intent.creation`, File 02 §5.3 and `intent.intent-thread`, File 02 §5.4), discharging `intent.consequences-for-later-specs` (File 02 §10)'s obligation for non-user-originated runs.
- Because an intent thread is intra-conversation by definition (`intent.intent-thread`, File 02 §5.2), an `Automation` declares a `target` conversation that owns its runs. The default `target` is a dedicated, auto-created automation conversation bound to the automation's identity; the user may instead bind the automation to an existing conversation or to a workspace, whose fired runs attach to a dedicated automation conversation bound to that workspace (the workspace's `default_conversation_id`, File 24 §3.3). Each fire attaches to an intent thread within the target: either a fresh intent thread per fire (the default, keeping fires independent) or a persistent automation intent thread that accumulates fires (configurable, for an automation whose runs form a continuing work line). This realizes the persistent-versus-transient distinction (a run that creates a durable owned conversation versus a fire-and-forget run) over the canonical intent-thread model.
- The target gate (§8.1) runs before routing. A fired signal never routes into a nonexistent or tombstoned conversation.

### 10.4 Rule

- A fired trigger routes and executes through the one run model; there is no separate automated execution architecture.
- Every trigger-originated run attaches to an owning intent thread within the automation's target conversation, per fire or accumulating, configurably.
- Workflow and pipeline task templates execute through the one execution-graph model, not a parallel engine.

### 10.5 Boundary

File 03 owns routing; File 04 owns the run model and the execution-graph; File 02 owns conversations and intent threads; File 34 (Workflows, Templates, and Reuse) owns the workflow body. This section owns the trigger-to-run handoff and the target binding.

## 11. Non-Interactive Execution Safety

Anchor: `automation.non-interactive-safety`

### 11.1 Definition

Non-interactive execution safety is the posture under which a trigger-originated run executes when no human is present to make decisions. It is the stronger-not-weaker rule: an automation run never auto-approves a capability whose tier requires a human decision, and it executes only within the authority the user pre-authorized.

### 11.2 Pre-Authorized Scope and Leases

- An `Automation` runs under a pre-authorized `capability_scope` and the leases the user granted it, expressed through the ordinary lease mechanism (`policy.lease-primitive`, File 06). The pre-authorization is granted explicitly at save or enable time through the ordinary approval flow, bound to the automation's identity and confined to its declared capability families and touched-resource bounds. A capability call within this pre-authorized scope resolves to direct-allow at fire time, like any leased call (`policy.effective-tier-resolution`, File 06 §4.3).
- A pre-authorization is never broader than the user granted, and never standing beyond what the lease scope permits; lease staleness and revocation apply to automation leases exactly as to any lease (`policy.mid-execution-policy-re-evaluation`, File 06 §10).
- The automation layer maintains a preauthorization dependency projection from leases to affected automations. When a lease covering an automation's `capability_scope` is revoked, staled, or narrowed, the policy event is joinable to affected `automation_id`s; when known at event time, it carries them as diagnostic metadata. The dashboard surfaces automations whose preauthorization was weakened. A later gate-4 failure records the specific `lease_id`, lease state-change event id, and reason, not a generic scope-unavailable error.

### 11.3 The Park-and-Notify Posture

- When a fired run reaches a capability call whose resolution would GRANT authority beyond the pre-authorized scope without a human — an `ask-user` outcome with no covering lease, a typed-confirmation requirement, a `Denied`-floor capability, or a model-mediated allow (File 06 §4.3, absent the typed opt-in below) — the run does not proceed and does not auto-approve. It enters a parked state, emits an elicitation through the elicitation rail (`controlrail.elicitation`, File 26 §13) and a notification, and waits. The user resolves the elicitation later; the run resumes from the parked point with the user's decision injected. There is no timeout-based auto-resolution: a parked run waits indefinitely (subject to the user cancelling it) rather than silently proceeding or silently failing. A direct-deny — and a model-mediated DENY — is honored unattended: it is authority-reducing, produces the typed in-band denial, and parking it would make the user adjudicate something policy already refused.
- Typed-confirmation and `Denied`-floor capabilities are never lifted by a lease, by `auto-decide`, or by an unattended context (`policy.permission-floor-typed-confirmation`, File 06 §7; `policy.denied-carve-out`, File 06 §7.4). A non-interactive context is strictly weaker in authority than an interactive one, never stronger (`controlrail.trigger-rail`, File 26 §11.2). This is the canonical realization of the System Agent's stronger-not-weaker posture (File 32 §12) for all surfaces.
- An automation may be configured, per its `policy`, to fail or skip a fire that would need a human decision instead of parking — for a true fire-and-forget automation that should never accumulate parked runs. The default is park-and-notify.
- An automation may additionally opt in, per its `policy`, to `unattended_auto_decide: permit_resolved_allow` — default OFF (park) — under which a high-confidence, terminal model-mediated ALLOW (File 06 §8) continues unattended. The opt-in admits the mediated-allow outcome ONLY and inherits every File 06 §8.4 property (never lifts `permission_floor`, never bypasses `Denied`, never lifts typed-confirmation; `PolicyDecisionMade` + `AutoDecideClassification` still recorded, the resolved policy/template version audit-visible). It is mechanically INAPPLICABLE to any fire whose trigger carried untrusted external payload — a `Webhook`, an external `Event`, or a `Custom` trigger over an external substrate — which is §5.2's no-escalation rule made structural: attacker-influenceable content never reaches a classifier whose verdict could grant unattended authority.

### 11.4 Mid-Run Intervention

A parked or running automation accepts mid-run intervention through the steering rail (`controlrail.steering-rail`, File 26 §10) and the run intervention contract (`run.user-intervention`, File 04 §17): the user can answer the elicitation, redirect, take over, or cancel. Messages that arrive while a run is in flight are delivered into the run without blocking it, consistent with the intervention model.

### 11.5 Rule

- An automation run executes only within its pre-authorized capability scope; a call needing a human decision parks and notifies, it never auto-approves.
- Typed-confirmation and `Denied`-floor capabilities never execute unattended; the non-interactive context is never stronger than the interactive one.
- A model-mediated DENY is honored unattended; a model-mediated ALLOW parks unless the automation carries the typed `permit_resolved_allow` opt-in, which is never applicable to a fire whose trigger carried untrusted external payload.
- A parked run waits without timeout-based auto-resolution; the default posture is park-and-notify, with fail/skip a per-automation option.

### 11.6 Boundary

File 06 owns the tier resolution, leases, typed-confirmation, and the `Denied` floor; File 26 owns the elicitation and steering rails; File 04 owns the run pause and intervention. This section owns the unattended posture composed from them.

## 12. Overlap and Concurrency

Anchor: `automation.overlap`

### 12.1 The `OverlapPolicy`

Each `Automation` declares an `OverlapPolicy` governing a fire that arrives while a prior run of the same automation is still in flight:

- `Skip` — do not start a new run; record the skipped fire. The default.
- `Queue { max_depth }` — enqueue the fire; run it after the current run completes, bounded by a maximum queue depth beyond which further fires are dropped-with-record.
- `Replace` — cancel the in-flight run (`run.interruption-pause-cancellation`, File 04 §17) and start a fresh run for the new fire.
- `Parallel { max_concurrent }` — allow up to a bounded number of concurrent runs of the same automation.

### 12.2 Rule

- The in-flight check is enforced by the `Scheduler`'s atomic claim (§9.2), so the overlap policy is honored deterministically and a single trigger never spawns a duplicate run unintentionally.
- Concurrency is always bounded: `Queue` has a maximum depth, `Parallel` a maximum count; an unbounded run pile-up is rejected. The global automation budget (§8.4) bounds total concurrency across automations independently of any single automation's policy.
- The full-parallelism posture of the run model (`run.explicit-rejections`, File 04 §28's rejection of single-instance locking) applies: an automation's overlap policy is a per-automation choice, not a system-imposed serialization; the substrate supports concurrent automation runs with full demultiplexing identity on every event (`ledger.event-envelope`, File 10 §5.2).
- Before an automation run mutates resources, the standard capability touched-resource and policy conflict machinery applies. If two automation runs would concurrently mutate the same resource and no capability-owned merge protocol exists, execution serializes, isolates, parks for user direction, or fails before mutation, per `run.mutation-rule` (File 04 §15.4). `OverlapPolicy` handles same-automation overlap; touched-resource conflict detection handles cross-automation conflict.
- A fire accepted into `Queue`, parked for approval, or converted into a `Run` is represented by durable ledger/run state keyed by `fire_id`. On restart, the scheduler rebuilds transient arming state and the execution layer resumes or surfaces accepted queued/parked fires from the ledger/run state. If recovery cannot resume one, it records a typed skipped or cancelled outcome rather than silently dropping it.

### 12.3 Boundary

File 04 owns cancellation, parallelism, and mutation conflict handling; File 10 owns the event demultiplexing identity. This section owns the per-automation overlap declaration and its enforcement at claim time.

## 13. Failure Handling and Retry

Anchor: `automation.failure-handling`

### 13.1 The `failure_handling` Declaration

Each `Automation` declares how a failed run is handled, as a policy over the canonical retry and error machinery, not a reimplementation of it:

- **Retry policy** — the maximum attempts and the backoff, declared over the canonical typed retry strategies (`provider.transport-level-retry-backoff`, File 17 §11) and the per-error `retryable` classification (`run.error-handling`, File 04 §20). The automation declares the policy; the run model and provider layer execute the backoff. No time-based busy-retry loop is introduced.
- **Retryable classification** — which failures retry: transient and infrastructure failures (a provider being briefly unavailable, a transient network error, a runtime not yet ready) retry; policy-denied, validation-failed, and otherwise terminal failures do not. The `retryable` flag on the error is authoritative; the automation never second-guesses it.
- **Circuit breaker** — after a configurable number of consecutive failed runs, the automation auto-disables itself and notifies the user, rather than re-firing into a failing condition indefinitely. Recovery is driven by explicit user reset, relevant source-recovery events, capability/provider health recovery, or a declared validation probe. A configurable minimum cooldown may bound retry frequency and prevent flapping, but elapsed time alone does not prove recovery. A half-open probe, if allowed, is bounded, policy-gated, recorded, and no broader than the automation's pre-authorized scope.
- **Failure notification** — how a failed run (after retries are exhausted) is surfaced: a notification, an entry in the dashboard, or an event other automations may watch.

### 13.2 Rule

- Failure handling is a per-automation policy over the canonical retry strategies and error classification; backoff is the provider and run layers', never a hardcoded busy loop.
- Only retryable failures retry; the `retryable` flag is authoritative.
- A repeatedly-failing automation trips its circuit breaker and auto-disables with notification; recovery is event-, state-, probe-, or user-driven, with cooldown only as a configurable safety guard.

### 13.3 Boundary

File 17 owns the retry strategies and backoff; File 04 owns the error classification and run-level retry; File 10 owns the failure events. This section owns the per-automation failure policy declared over them.

## 14. Validation Policy and Output Contract

Anchor: `automation.validation-and-output`

### 14.1 Validation Policy

An `Automation`'s `validation_policy` declares which validators and completion checks a run must satisfy to be considered successful, selecting among the existing validation substrate — `Validation` and `Critique` blocks (`artifact.validation-critique`, File 09 §14), the completion-verification hook surface (`run.termination`, File 04 §22), and File 39's validators. A run that completes without satisfying its validation policy is recorded as a failed (not successful) run and is subject to the failure-handling policy (§13). The validation policy reuses the substrate; it does not define new validators.

### 14.2 Output Contract

An `Automation`'s `output_contract` declares what a successful run must produce and how the result is delivered:

- the expected product — an `Artifact` revision, a `Claim` or report, a committed `Observation`, a notification, or a structured result;
- the delivery — a notification to the user, a message into the target conversation, a write into the workspace, or an emitted event other automations may watch.

A run that completes without satisfying its output contract is a failed run, even if its execution did not error — mirroring the after-run safety-net that ensures the terminal output step actually happened. The output contract is the automation's promise about what it produces; it composes the existing artifact, evidence, and event substrates and introduces no new product type.

### 14.3 Rule

- The validation policy selects among existing validators and completion checks; a run that fails validation is a failed run.
- The output contract names the expected product and its delivery over existing substrates; a run that does not satisfy it is a failed run.
- Both compose existing substrates; neither introduces a new validator or product type.

### 14.4 Boundary

File 09 owns the validation and artifact contracts; File 04 §22 owns completion verification; File 39 owns the validator catalogue; File 10 owns the delivery events. This section owns the per-automation validation and output declarations.

## 15. Creation and the Graduation Path

Anchor: `automation.creation-and-graduation`

### 15.1 Creation Paths

An `Automation` is created through one of four paths, all producing the same object:

- **Graduation from a successful run** — the primary path. After a successful run, the runtime may propose crystallizing it into an `Automation` (`run.automation-reuse`, File 04 §26), derived from the run's structure — its `RunIntent`, the capabilities it used, the artifacts it produced, the validation that passed — capturing the seven preservation fields. The proposal is generated from successful structure, not from text heuristics (`codex_recommendations.md` §12). Graduation is grounded in the run's committed ledger evidence (`ledger.forgery-guards`, File 10 §3.7): a proposal derives only from recorded run structure and a recorded successful, validation-satisfying outcome, never from a producer's self-report, so a run with an empty trace or no committed successful outcome cannot be crystallized into an `Automation`.
- **Natural-language creation** — the `automation.create_from_description` capability (§19.1; `automation.create` is the separate complete-definition path) parses an informal description ("every weekday at 9am, summarize my unread mail") into a trigger and a task template through a model-mediated or deterministic parser selected by the model strategy and settings layers, presents the parsed structure for the user to confirm, and creates the automation on confirmation (`unit14-systems.md` D14.SP.3, `unit11-cross-tool-learning.md` CT.9). This file defines the parse-confirm-create contract; the parser is an implementation behind it.
- **Manual construction** — the user builds the automation directly in the automation editor or the workflow studio (`codex_recommendations.md` §8.11): defining triggers, selecting or building the task template, attaching policies and capability scope, defining the world selector, and simulating runs before enabling.
- **Promotion** — a recorded macro (`web.artifacts`, File 28 §11; `gui.macros`, File 31 §10) or a workflow template (File 34) is promoted into an `Automation` by binding a trigger and the governing fields.

### 15.2 No Silent Creation

- An `Automation` is never created or enabled silently. Graduation produces a proposal the user reviews and accepts; natural-language creation requires explicit confirmation of the parsed structure; agent-initiated creation (an agent crystallizing its own work, or self-scheduling) passes the proposal-first source-approval and approval flows (`policy.source-approval-flow`, File 06 §9; `systems/17-agent-self-modification.md`'s no-silent-registration rule) and defaults to a `UserApproval` tier on first creation. Automation is an explicit, user-confirmed capability, consistent with the external-ecosystem boundary that scheduled automation is created only when the user asks.
- Built-in, profile-bundled, and plugin-bundled automations ship as templates or presets. They become enabled automations only through explicit user acceptance, onboarding/profile selection recorded as acceptance, or source-approval that produces an accepted definition. Built-in default watches are default templates; enablement remains explicit and inspectable.
- Self-scheduling — an agent creating an automation during a run — reuses the same `Automation` object and the same creation governance; constraints such as a maximum number of active agent-created automations and a minimum recurring interval are settings, not hardcoded limits.

### 15.3 Rule

- The four creation paths produce one `Automation` object; graduation from successful structure is primary.
- No automation is created or enabled silently; every path requires explicit user acceptance, and agent-initiated creation passes source-approval.
- Shipped automations are templates or presets until accepted.
- Self-scheduling reuses the object and the governance; its bounds are settings.

### 15.4 Boundary

File 04 §26 owns the reuse proposal trigger; File 06 owns the approval and source-approval flows; File 34 (Workflows, Templates, and Reuse) owns the template the automation may be promoted from; Files 28 and 31 own the macros. This section owns the automation-creation contract.

## 16. Surface Aliasing

Anchor: `automation.surface-aliasing`

### 16.1 The Aliasing Rule

Every per-surface scheduling, monitoring, and reactive-automation concern is an `Automation` over the one `Scheduler`, the Trigger rail, and the world model — never a parallel mechanism. The surface contributes the domain-specific task template, capability scope, and default policies; the automation layer contributes the trigger, the scheduler, the eligibility chain, the non-interactive posture, and the run.

- The System Agent's `sys.schedule.*` and `sys.monitor.*` families (File 32 §12) are thin aliases: `sys.schedule.create` is an automation with a `Schedule` trigger and a system task template; a `sys.monitor.*` watch is an automation with a `WorldCondition` trigger over the System Agent's `SystemMetric`/`Process`/`Liveness` facts (`unit14-systems.md` D14.SP.2). Default OS-level watches (disk full, battery low, memory pressure, thermal throttle) ship as built-in system automation templates, not silently enabled automations.
- Web page monitors (File 28 §12) are automations with a `WorldCondition` trigger over a page's observation fingerprint (`web.monitoring`, File 28 §12), with the event-first change detection and the flagged polling fallback realized as the watch policy (§4).
- Teacher review-due and scheduled-study monitors (File 30 §17.4) are automations: the review-due signal is a `WorldCondition` trigger over `Mastery` memory validity (`teacher.practice-srs`, File 30), and scheduled study is a `Schedule` trigger.
- GUI scheduled tasks and event-triggered automations (File 31 §2.8/§23) are automations with `Schedule` or `Event` triggers and a GUI task template, confined to the GUI sandbox profile.
- Data-source change monitors (File 29 §17.4) are automations with a `WorldCondition` or `Event` trigger over a dataset or connection fingerprint.
- Memory consolidation cadence (`memory.consolidation`, File 14) is an automation with a `Schedule` trigger and an `Event` trigger on agent-turn-completion (the sleeptime pattern), with its idle-and-debounce behavior realized as the watch and schedule policies.

### 16.2 Rule

- A surface scheduling concern is an `Automation`; the surface contributes the template and policy, the automation layer contributes the trigger, scheduler, and run. No surface runs a private scheduler, watch poller, or non-interactive execution path.
- A surface's monitor is confined to the narrowest surface sandbox profile and pins the surface and its policies at save time the way routing does (§6.3), exactly as each per-surface spec's Consequences requires.

### 16.3 Boundary

The per-surface specs own their task templates, capability scopes, and default policies; this file owns the one scheduler and automation layer they alias over.

## 17. Run History, Observability, and the Consumption Contract

Anchor: `automation.observability`

### 17.1 Runs as Ledger Records

An automation run is an ordinary `Run` recorded in the execution ledger (`ledger.execution-ledger`, File 10) with `producer` `Automation { trigger_id }` (`ledger.execution-ledger`, File 10 §3.2) and the `automation_id` + `fire_id` canonical cross-reference keys required on every automation-originated entry and propagated across the fired run's entries (`ledger.cross-references`, File 10 §3.6). Run history — past fires, their outcomes, their durations, their produced artifacts — is a projection over those keys; there is no parallel automation-run table. A skipped, duplicate, queued, or parked fire is recorded with its reason (§8.1, §11.3, §12.2).

### 17.2 Derived Automation State

An `Automation` exposes derived state computed from the ledger, run records, and device-local arming state, never stored as durable definition fields: the last fire and its outcome, the next computed fire, recent fire count and success rate, accepted queued or parked state, current run, circuit-breaker state, and preauthorization-weakened diagnostics. These are projections, recomputed on read.

### 17.3 The Consumption Contract

This file specifies the data contract that user-facing surfaces consume; it specifies no rendering. The contract exposes, per automation and across all automations: the definition and its triggers, enablement and per-trigger enablement, derived state (§17.2), run history projection, target availability, preauthorization dependency diagnostics, and the run-now and enable/disable controls. The automations dashboard and inspector (`codex_recommendations.md` §8.10/§8.11) and widgets that surface automation output as ambient interfaces (`kuzeys-ui-customization-and-widgets-addendum.md` §8) read this contract; File 37 and File 38 render it.

### 17.4 Rule

- Automation runs are ledger records; run history is a ledger projection; no parallel run table exists.
- Derived automation state is computed, never durable.
- This file specifies the consumption data contract; UI specs render it.

### 17.5 Boundary

File 10 owns the ledger and the run records; File 37 and File 38 own the dashboard, inspector, and widget rendering. This section owns the observability data contract.

## 18. Persistence, Locality, and Portability

Anchor: `automation.persistence`

### 18.1 What Is Durable, Computed, and Device-Local

- **Durable:** the `Automation` definition — its identity, triggers, task template, parameters, world selector, capability scope, policy, validation policy, output contract, failure handling, overlap policy, rate limit, target, run locality, and enablement — as a versioned entity (§6.4) over the block pool and version graph (Files 08, 11). Automation leases are durable policy state (`policy.persistence`, File 06 §11.6). Run history and accepted queued/parked fires are durable ledger/run state keyed by `fire_id` (§17.1).
- **Computed / device-local runtime state:** the armed timers, active watch and event subscriptions, registered webhook endpoints, in-flight claims, next-fire and last-fire projections, and cross-device firing authority handles. This arming state is never durable; it is reconstructed at startup from durable definitions and the ledger.
- **Reconstruction:** at startup, the `Scheduler` reads the enabled automation definitions, re-arms their triggers, reconciles missed fires (§3.4), and rebuilds transient arming state. The execution layer resumes or surfaces accepted queued/parked fires from ledger/run state. The loss of arming state across a restart is a rebuild, never a loss of automation identity, accepted work, or history.

### 18.2 Locality and Sync

- An `Automation` definition is a logical object and syncs across a user's devices (`storage.physical-layout-locality`, File 20 §8; `portability.what-replicates`, File 21 §5), so the user's automations follow them. Arming state is device-local and never syncs (`portability.what-replicates`, File 21 §5).
- An enabled automation's `run_locality` must resolve to one firing authority before the scheduler arms it: `DevicePinned { device_id }`, `CurrentDeviceOnly { device_id }` resolved at enable time, or `CrossDeviceClaimed` only when the sync/transport layer provides an atomic cross-device claim contract. If no claim contract is available, `any-device` is a placement preference, not an executable firing mode; the automation remains unarmed and surfaces a typed locality-unresolved state until the user picks a device or a future claim mechanism is available.

### 18.3 Portability and Security

- An `Automation` definition is part of the portable bundle (`portability.export-bundle`, File 21 §10): exporting carries the definition; importing re-resolves firing authority and device-local arming state per the importing device. The definition references its capability scope and pinned surface symbolically, so it re-resolves on import.
- No raw secret is part of an automation definition: a `Webhook` trigger's verifying secret and any credential the task template uses are vault references (`security.secret-vault`, File 22 §5), never inline; raw secrets never sync, export, or materialize (`portability.sensitivity-egress`, File 21 §12). Security-sensitive automation runs (system mutation, credential use) record into the device-local hash-chained audit overlay (`ledger.hash-chained-audit-log`, File 10 §16.4), which never syncs.

### 18.4 Rule

- The definition is durable, versioned, and syncs; arming state is device-local and rebuilt at startup; accepted work and run history are ledger-durable.
- `run_locality` must resolve to one firing authority before arming; cross-device firing requires an atomic claim contract.
- No raw secret is part of a definition; security-sensitive runs record to the device-local audit overlay.

### 18.5 Boundary

Files 20 and 21 own storage, locality, sync, and the portable bundle; File 22 owns the vault and the audit cryptography; File 08 and File 11 own the entity and version graph. This section owns the durable-versus-device-local split for automations.

## 19. The `automation.*` Capability Surface

Anchor: `automation.capability-surface`

### 19.1 Closed Canonical Capabilities

The automation layer exposes its operations as built-in capabilities declared per `capability.declaration` (File 05 §3), flowing through the standard call pipeline (`run.call-pipeline`, File 04 §8.2) and policy (File 06):

- `automation.create(definition)` — create an automation from a complete definition; `UserApproval`.
- `automation.create_from_description(description)` — the natural-language creation path (§15.1), parsing and presenting for confirmation; `UserApproval`.
- `automation.create_from_run(run_ref)` — graduate a successful run into a proposed automation (§15.1); `UserApproval`.
- `automation.update(automation_id, patch)` — edit a definition, producing a new version and re-pinning (§6.3); `UserApproval`.
- `automation.enable(automation_id)` / `automation.disable(automation_id)` — toggle enablement; `automation.enable_trigger`/`automation.disable_trigger` for per-trigger enablement; at minimum `UserApproval`.
- `automation.delete(automation_id)` — tombstone an automation definition and preserve history; default tier `UserApproval`. Typed confirmation or a `Denied` floor applies only when deletion itself has high-risk consequences: active queued/parked/in-flight runs, externally depended-on webhook bindings, policy-critical safety automations, or hard-deleting payload/history beyond tombstoning. The task template's destructive scope does not by itself make deletion destructive.
- `automation.run_now(automation_id, parameters)` — fire an automation manually (§7.1); the tier reflects the automation's task template, not a blanket low tier.
- `automation.list(filter)` / `automation.get(automation_id)` / `automation.get_runs(automation_id)` — read the definitions, derived state, and run history (§17); `ReadOnly`, `ConcurrencySafe`.
- `automation.test_trigger(trigger_ref)` — simulate whether a trigger would fire and return matched context, next-fire or due information, predicate result, and proposed `RouteRequest` preview. It is `ReadOnly` and never creates a run.

### 19.2 Rule

- The automation capabilities are built-in declarations under the one registry; they carry the touched-resource and tier metadata their effects warrant (the `scheduler` resource class, `capability.touched-resources` File 05 §6). Creating, editing, enabling, deleting, and running an automation are tier-gated; reading is `ReadOnly`.
- An agent invokes these capabilities like any other, subject to policy and the no-silent-creation rule (§15.2).

### 19.3 Boundary

File 05 owns the declaration and registry; File 06 owns the policy gating. This section declares the canonical automation capability set.

## 20. Events

Anchor: `automation.events`

### 20.1 Event Vocabulary

The automation layer emits through the one event bus (`ledger.event-stream`, File 10 §5), reusing the reserved automation entries and registering the rest as `Custom { namespace: "automation" }`:

- `AutomationTriggerFired` (reserved, `ledger.entry-kind-catalogue`, File 10 §4) — a trigger fired and emitted a run; payload carries `automation_id`, `trigger_id`, `fire_id`, optional `source_event_id`, trigger kind, routing `trigger_kind`, and firing context.
- `WebhookReceived` and `OsEventReceived` (reserved, File 10 §4) — inbound external triggers.
- `AutomationCreated` / `AutomationUpdated` / `AutomationEnabled` / `AutomationDisabled` / `AutomationDeleted` — definition lifecycle.
- `AutomationRunSkipped` / `AutomationRunParked` — fire-level facts, carrying the gate or approval reason for a fire a gate blocked or a fire that parked for a human decision.
- `AutomationFireRunBound` — a fire-level progress/idempotency fact binding one `fire_id` to one allocated `run_id`; it may precede `RunCreated`, does not assert that the run exists or started, and a second run id for the same fire is a conflict.
- `WatchArmed` / `WatchFired` / `WatchReset` and `ScheduleArmed` / `ScheduleFired` / `ScheduleMissed` — trigger-level firing-state events for the dashboard.
- `AutomationCircuitOpened` — an automation tripped its failure circuit breaker and auto-disabled (§13.1).

A fired run's start, completion, and failure are not separate automation events: the trigger firing is the reserved `AutomationTriggerFired`, and the run itself is carried by `RunCreated` and `RunStatusChanged` in the execution ledger (`ledger.execution-ledger`, File 10 §3). This section declares automation lifecycle events and fire-level facts; it does not duplicate run lifecycle events — a binding fact such as `AutomationFireRunBound` records the fire-to-run allocation, not the run's start, completion, or failure, so it is a progress/idempotency record rather than a run lifecycle event.

### 20.2 Rule

- Automation events carry the canonical envelope (`ledger.event-envelope`, File 10 §5.2) with full demultiplexing identity, so concurrent automation runs are distinguishable. Their sensitivity is derived from trigger context and produced payloads. `Webhook` and external-event payloads default to untrusted and at least the sensitivity declared by trigger registration; secret-bearing fields are redacted or referenced through vault/transient handles per File 22. Dashboard projections may show structural facts, safe descriptions, ids, status, and redacted summaries, but not raw secret payloads.
- Transient arming-state events flow on the live bus; consequential events (fires, definition lifecycle, accepted queued/parked fires) commit to the ledger per the durability rules (`ledger.event-stream`, File 10). A fired run's outcome is carried by its own ledger run records (`ledger.execution-ledger`, File 10), not a duplicate automation run-outcome event.
- Domain-specific automation events (a system watch crossing, a page-change monitor firing) are the owning surface's `Custom` events; this file reserves the cross-cutting automation vocabulary.

### 20.3 Boundary

File 10 owns the envelope, the catalogue, the durability split, and the reserved entries. This section names the automation event vocabulary.

## 21. Settings

Anchor: `automation.settings`

Automation behavior is configurable through `settings.setting-definition` (File 15), with agent-exposure governed by `policy.agent-exposure-policy-settings` (File 06 §16.4). At minimum, settings must support:

- per-automation and global enablement defaults, and the default `target` conversation policy;
- the default `missed_fire_policy` keyed on `Once` versus recurring schedules, and the `RunAll` opt-in gate;
- the schedule timer-versus-scan mode and the periodic-scan fallback interval (flagged), recurring-schedule jitter window, and calendar-local DST policy defaults;
- the default `OverlapPolicy` and its bounds (queue max-depth, parallel max-concurrent);
- the watch defaults: `firing_mode`, `reset_condition`, `dedupe` window, `debounce` window, hysteresis margins, and the no-event poll-interval fallback (flagged), per automation, per surface, and globally;
- the per-automation `rate_limit` (minimum interval, per-window cap) and the global automation budget (maximum concurrent runs, maximum fire rate), and the cold-start guard bound;
- the recursive-trigger cycle-guard depth and re-entry window;
- the default `failure_handling` (max attempts, backoff selection over the canonical strategies, circuit-breaker threshold, recovery triggers, probe policy, and cooldown safety bound), per automation and globally;
- the non-interactive posture default (park-and-notify versus fail/skip), the `unattended_auto_decide` opt-in default (`park` unless a scope explicitly selects `permit_resolved_allow`, §11.3), and the notification channels for completion, failure, and parked-needing-approval;
- the agent self-scheduling bounds (maximum active agent-created automations, minimum recurring interval) and the default approval tier for agent-initiated creation;
- the webhook binding policy (local-only default, remote opt-in, authentication, freshness, and idempotency requirements);
- the run-history retention granularity for the automation projection;
- per-automation `run_locality` defaults and locality-unresolved surfacing;
- dashboard thresholds and notification policy for weakened automation preauthorization.

Settings define intended variation; they must not become hidden hardcoded branches (`run.settings`, File 04 §27).

## 22. Explicit Rejections

Anchor: `automation.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel scheduler, watch poller, daemon, or cron runtime per surface — there is one `Scheduler` and one Trigger rail; surface scheduling is an `Automation` over them;
- a separate background or automated execution architecture — a trigger-originated run is an ordinary `Run` (`run.explicit-rejections`, File 04 §28);
- a parallel `automations`, `scheduled_tasks`, `system_watches`, `autopilot`, or `automation_runs` table — the definition is a versioned entity, the runs are ledger records, the firing state is device-local;
- tight clock-polling as the firing mechanism — a `Schedule` trigger arms a single timer; a periodic scan is a flagged fallback, never the default and never a correctness condition;
- driving triggers from the world model's exposed clock as a behavior condition — current time is grounding, not a scheduler (`world.consequences-for-later-specs`, File 18);
- a parallel watcher layer over perception or the filesystem — watches subscribe to `world.watch` and existing change signals and the filesystem watcher;
- auto-approving a gated capability in an unattended context — typed-confirmation and `Denied`-floor capabilities never execute unattended; a fire needing a human decision parks and notifies;
- a non-interactive context with broader authority than an interactive one — unattended is strictly weaker, confined to the pre-authorized scope;
- timeout-based auto-resolution of a parked approval — a parked run waits for the user, it does not silently proceed or fail;
- silently dropping a blocked, missed, duplicate, queued, or parked fire — every accepted or rejected occurrence is recorded with its reason;
- silent automation creation or enablement — every creation path requires explicit user acceptance, and agent-initiated creation passes source-approval;
- an unbounded self-retriggering automation, an unbounded overlap pile-up, or a hardcoded firing interval, cooldown, retry count, or watch threshold outside settings;
- reimplementing retry, backoff, or circuit-breaking inside the automation layer instead of declaring a policy over the canonical strategies;
- treating an `Event` trigger as a blocking hook that gates in-flight work — a trigger launches new work, it does not gate other work;
- granting authority from an untrusted inbound webhook payload;
- raw trigger-payload interpolation into prompts, capability arguments, policy inputs, or undeclared instructions;
- treating `any-device` as an executable locality mode without an atomic cross-device claim contract;
- letting `automation.test_trigger` create a run;
- silently weakening an automation when a lease is revoked, staled, or narrowed;
- routing a fired automation into a nonexistent or tombstoned target conversation.

## 23. Consequences for Later Specs

Anchor: `automation.consequences-for-later-specs`

- The **Workflows, Templates, and Reuse** spec owns the reusable workflow and template body an `Automation`'s task template may reference; it must accept that the automation layer owns the trigger binding, the pinning at save time, and the run, and must expose its templates so an automation can reference one by identity and parameterize it at fire time. A workflow is the body; an automation is the trigger-bound, policy-bound, scheduled operator over it.
- The **Extension and Plugin System** and **MCP and External Integrations** specs own the transport for `Webhook` and external-event triggers and the lifecycle of plugin-bundled automations and trigger kinds; they must register triggers and automations through the proposal-first source-approval path and the `Custom` trigger-kind mechanism, provide freshness/idempotency data for external deliveries, and introduce no parallel detection or execution.
- The **UI Shell** and **UI Customization** specs render the automations dashboard, the schedule and trigger editors, the parked-approval notifications, target-unavailable state, preauthorization-weakened diagnostics, locality-unresolved state, and the automation widgets; they consume the observability and consumption data contract (§17) and the run-now and enable/disable controls, and must not make the presentation the firing or run truth.
- The **Quality Control and Validation** and **Evaluation** specs own the validators an automation's validation policy selects; they must integrate through the validation and completion-verification substrates an automation references, not a parallel automation-validation pipeline.
- The **Telemetry, Logging, and Observability** spec consumes the automation event vocabulary and the run-history projection; it must not introduce a parallel automation-run store.
- The **Runtime Infrastructure and Lifecycle** spec owns the background-worker scheduling primitives the `Scheduler` and watch poller run on, the startup ordering that re-arms triggers and reconciles missed fires, and the graceful shutdown that stops the workers and cancels in-flight evaluations; it must place the one `Scheduler` in the startup graph and must reconstruct firing state from durable definitions, never persist it.
- The **per-surface specs** that defer scheduling, monitoring, and reactive automation here (Files 27–32) realize their monitors and scheduled tasks as `Automation`s over the one `Scheduler`, contributing their task templates, capability scopes, and default policies, confined to their narrowest sandbox profiles, pinning their surface and policies at save time, and introducing no parallel scheduler, watcher, or non-interactive execution path.

## 24. Canonical Rule Anchors

Anchor: `automation.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `automation.chosen-model`, `automation.trigger`, `automation.schedule-trigger`, `automation.watch`, `automation.event-and-webhook-triggers`, `automation.automation-object`, `automation.manual`, `automation.eligibility`, `automation.scheduler`, `automation.run`, `automation.non-interactive-safety`, `automation.overlap`, `automation.failure-handling`, `automation.validation-and-output`, `automation.creation-and-graduation`, `automation.surface-aliasing`, `automation.observability`, `automation.persistence`, `automation.capability-surface`, `automation.events`, and `automation.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
