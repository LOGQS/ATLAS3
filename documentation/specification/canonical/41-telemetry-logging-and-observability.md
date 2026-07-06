# Telemetry, Logging, and Observability

## Status

Canonical.

## Scope

This file defines:

- the `Observatory` — the always-available observability substrate service and the management surface that projects the system's logs, traces, metrics, and execution facts into inspectable views; the surface `core.substrate-services` (File 01 §2.4) names as "logging and evaluation"
- `LogRecord` and the closed `LogLevel` set — the structured, span-correlated, sensitivity-tagged log record, its emission as the `DebugLog` event (`ledger.app-event-catalogue`, File 10 §5.3), its device-local rotating persistence, and the redaction-before-write rule
- `Span`, `Trace`, and `TraceContext` — the trace model that gives semantics to the `trace_context` envelope field `ledger.event-envelope` (File 10 §5.2) delegates here, with a trace defined as a projection over causally-linked events and ledger entries
- `MetricInstrument`, the closed metric-kind set, and `MetricSeries` — metrics as rebuildable aggregate projections over the ledger and declared event sources, keyed never-unkeyed, accuracy-classed by source delivery, with no continuous-score verdicts
- the correlation model that links a log, a span, a metric sample, a ledger entry, and an audit entry to one execution fact
- privacy-preserving telemetry and egress — the local-first zero-egress default, `TelemetrySink`, `TelemetryConsent`, redaction and anonymization before egress, the optional standard export protocol, and the opt-in crash-report path, all under `secret.backend-boundary` (File 22 §4) and `portability.sensitivity-egress` (File 21 §12)
- the debug surface data contract — the bounded live event-log ring buffer, the performance-monitor projection, and the debug toggles, developer-gated and carrying no additional active debug-capture, render, subscription, or export overhead when inactive beyond baseline instrumentation
- observability retention as policy and settings over the storage-side garbage collection `storage.retention-gc-accounting` (File 20 §11) realizes, with no time-based pruning as a correctness mechanism
- the sharp boundary between observability (opt-out-able diagnostic visibility) and the hash-chained audit overlay (`ledger.hash-chained-audit-log`, File 10 §16; never disabled, never synced)
- operational-health observability — the health-status data contract, background-worker liveness surfacing, and the resource-metric sampling that is the one flagged periodic exception
- per-surface and per-subsystem observability aliasing and the instrumentation-declaration contract through which a capability or subsystem registers custom metrics, spans, and log categories
- the `observability.*` capability surface (surface-and-service duality), the observability events, the settings dimensions, the persistence/locality/replay contract, the operating constraints, the explicit rejections, and the consequences for later specs

This file does not define:

- the `ExecutionLedger`, the `EventStream`, the `EventEnvelope`, the closed `AppEvent`/`LedgerEntryKind` catalogues, the `Hook` primitive, the `DebugLog`/`Heartbeat`/`EventBufferOverflow` event kinds, the delivery classes and aggregation policies, per-call `TokenUsageRecord` attribution, replay semantics, or the hash-chained audit-overlay construction and membership — File 10 owns those; this file consumes them and projects them
- the `ProviderAdapter`, `ProviderHealth`, `RateLimitState`, `PricingSnapshot`, cost computation, or the per-call estimation-accuracy telemetry record — File 17 owns those; this file surfaces usage, cost, health, and rate-limit facts as metrics without recomputing them
- the storage engine, the projection store, the content-addressed blob store, the on-disk layout, the device-local-versus-syncable partition, garbage-collection mechanics, or the audit-overlay storage — File 20 owns those; this file specifies the retention policy and the rebuildable-projection discipline storage realizes
- the secret vault, the secret-detection and redaction primitives, the egress-governance policy semantics, encryption, the trust model, or the audit-chain cryptography — File 22 owns those; this file calls the redaction primitive before any log, trace, metric, or egress, and honors the egress policy
- the `Validator`, the validation gate, or the inline quality-control layer — File 39 owns those; this file computes the quality-metric projections File 39 §17.2 hands here
- offline evaluation suites, benchmarks, scoring aggregation, the replay engine, or judge optimization — File 40 owns those; this file owns the live-metric layer of the same quality discipline
- the `Shell`, the renderer registry, the Observatory's and debug surface's rendering, panel layout, or accessibility presentation — Files 37 and 38 own those; this file owns the data contracts they render
- the run lifecycle, the capability-call pipeline, cancellation, context assembly, token counting, or the version graph — Files 04, 13, and 11 own those; this file observes and projects them
- process lifecycle, startup and shutdown orchestration, background-worker scheduling, queues, service supervision, or operational remediation — the Runtime Infrastructure and Lifecycle spec (File 42) owns those; this file observes their facts and exposes health projections, and it operates nothing
- crash-reporter bundling into the installer, update-channel telemetry distribution, platform crash-handler registration, or release-channel analytics — the Packaging, Platform, and Distribution spec (File 43) owns those; this file owns the in-app diagnostic-bundle export and the consent boundary
- the settings cascade, scope resolution, profiles, the TOML overlay, or bootstrap environment variables — File 15 owns those; this file names the dimensions it exposes

## Source Resolution

This file resolves logging, tracing, metrics, telemetry, usage and cost dashboards, debug tooling, performance monitoring, error and crash aggregation, observability surfaces, and observability retention material into one boundary: the read-and-project observability layer over the one ledger, the one event stream, and the one storage substrate, plus the privacy-governed egress boundary.

Resolved design:

- Observability is not a parallel store. There is no telemetry database, no metrics time-series store of record, no separate tracing backend, and no second log of consequential facts beside the ledger. Logs, traces, and metrics are a structured-log event family plus rebuildable projections over the `ExecutionLedger` and `EventStream` (File 10) and the storage substrate (File 20). The `Observatory` is the surface that renders them; logging is one component of the Observatory.
- The source of truth for what happened is the ledger. Diagnostic logs carry finer granularity than the ledger (debug- and trace-level detail the ledger never records) but never carry authority: a log line is never the durable proof of a consequential fact, and the loss of a log never loses a consequential fact.
- Local-first and zero-egress by default. No log, trace, metric, or diagnostic leaves the device unless the user explicitly opts in per category and, by default, per device. There is no built-in dependency on a hosted telemetry service.
- Privacy is structural. Raw `Secret` material never reaches a log, a trace payload, a metric label, a projection, a debug panel, or an egress path; redaction runs before write, not before display. Sensitivity gates retention, export, sync, and egress with the same `Public`/`Sensitive`/`Secret` classification the ledger uses.
- Observability is event-first. Metric projections rebuild on event commit, traces assemble from causally-linked events, and logs stream by push. Periodic sampling is permitted only where a metric source emits no change event, and it is flagged and configurable, never a correctness mechanism.
- Live observability (this file) and offline evaluation (File 40) are two layers of one quality discipline that share the ledger and the validation results; neither introduces a parallel store. The audit overlay (File 10 §16) is a security-integrity tier, not telemetry: it is never disabled when telemetry is disabled, never synced, and this file surfaces it without owning it.

## 1. Chosen Model

Anchor: `observability.chosen-model`

ATLAS3 has one observability layer. Everything a developer or user needs in order to see what the system is doing, has done, how well, how fast, and at what cost is a projection over the canonical execution substrate, a structured-log event, or a privacy-governed egress of one of those — never a parallel record store.

The layer has one surface and three projection families over two substrates, plus an egress boundary:

- the **`Observatory`** — the always-available observability substrate service and its management surface, the single place the projections are queried, correlated, and rendered (the surface `core.substrate-services` (File 01 §2.4) names "logging and evaluation"; the surface `codex_recommendations` §8.12 calls "the Observatory" and §10.8 makes "logging one component of")
- **logs** — `LogRecord`s, the structured, span-correlated, sensitivity-tagged diagnostic records emitted as `DebugLog` events (`ledger.app-event-catalogue`, File 10 §5.3) over the one bus and persisted to a bounded, device-local, rotating diagnostic stream
- **traces** — `Span`s composed into `Trace`s, the causal projection over the events and ledger entries a logical operation produced, giving semantics to the `trace_context` envelope field `ledger.event-envelope` (File 10 §5.2) delegates here
- **metrics** — `MetricSeries`, the rebuildable aggregate projections over the ledger (latency, throughput, usage, cost, error rate, cache rate, quality, resource, health), each a `core.projection` (File 01 §6.11) keyed by model or provider identifier where the value is model-dependent, never an unkeyed scalar (`core.explicit-rejections`, File 01 §8)
- the **telemetry egress boundary** — `TelemetrySink` and `TelemetryConsent`, the opt-in, per-category, revocable, redacted, sensitivity-gated path by which any observability data may leave the device, defaulting to no egress at all

The substrates are the `ExecutionLedger` and `EventStream` (File 10) and the storage substrate (File 20). The observability layer adds one durable artifact of its own — the device-local diagnostic log stream — and that stream is bounded, rotating, redacted, never synced, and never the source of truth for a consequential fact. Metrics and traces add no durable record: they are projections, rebuildable from the durable substrate, whose stale or corrupt cost is a rebuild, never data loss (`core.projection`, File 01 §6.11).

The net-new noun-objects this file introduces are minimal: `Observatory`, `LogRecord` (+ `LogLevel`), `Span` / `Trace` (+ `TraceContext`), `MetricInstrument` (+ the closed metric-kind set) / `MetricSeries`, `TelemetrySink` (+ `TelemetryConsent`), and `DiagnosticBundle`. Everything else is consumed: the ledger and events from File 10, usage and cost from File 17, retention and projection rebuild from File 20, redaction and egress from File 22, quality metrics from File 39, and the offline measurement layer from File 40.

`Observatory` supersedes any earlier vocabulary that named the same surface: "telemetry dashboard", "metrics dashboard", "usage dashboard", "billing view", "trace viewer", "performance monitor", "observability panel", "diagnostics view", "system health panel", "LLM calls overview". `LogRecord` supersedes "log entry", "log line", "operation span", "diagnostic record", "trace log row", "structured log event". `Span` and `Trace` supersede "operation span", "trajectory span", "agent span", "turn span", "task span", "flow log", "execution trace". `MetricInstrument` and `MetricSeries` supersede "counter", "gauge", "histogram", "telemetry metric", "usage record rollup", "analytics metric", "scorecard figure". `TelemetrySink` supersedes "telemetry exporter", "analytics sink", "crash reporter", "OTLP exporter", "log sink". These are the canonical typed shapes the rest of this file uses; earlier names from source material map into them.

This model elaborates `core.execution-ledger` (File 01 §6.4) (the ledger is the record this layer queries), `core.projection` (File 01 §6.11) (metrics and traces are projections), `core.event-first-by-default` (File 01 §7.15) (observation is event-driven), `core.non-destructive-by-default` (File 01 §7.13) (retention is bounded, accounted, and reclaimable, never silent loss), and the substrate-service classification `core.current-major-area-classification` (File 01 §5.8) (logging and evaluation are cross-cutting substrate services with optional management surfaces, never private per-surface versions). It discharges the `trace_context` semantics `ledger.event-envelope` (File 10 §5.2) defers here, the quality-metric projection `qc.events-metrics` (File 39 §17.2, §22) hands here, the telemetry-view-as-rebuildable-projection rule `storage.consequences` (File 20 §18) states, and the live-metric layer of the seam `40↔41` (File 40 §2.7) fixes.

## 2. Boundaries with Adjacent Layers

Anchor: `observability.boundaries-with-adjacent-layers`

### 2.1 With File 10 (Execution Ledger, Event Stream, and Hooks)

File 10 is the substrate this layer reads. File 10 owns the `ExecutionLedger` (the durable source of truth for consequential facts), the `EventStream` (live coordination), the `EventEnvelope` (including `sequence_scope`, `sequence`, `parent_event_id`, `causal_event_ids`, `timestamp`, `sensitivity`, and the `trace_context` field), the closed `AppEvent` and `LedgerEntryKind` catalogues, the `DebugLog` / `Heartbeat` / `EventBufferOverflow` / `BackgroundWorkerHeartbeat` event kinds, the delivery classes (`lossless_consequential`, `coalescible`, `latest_only`, `sampled_diagnostic`) and the aggregation policies (`ledger.event-stream`, File 10 §5.5), the per-call `TokenUsageRecord` and `TokenCountEstimationTelemetry` (`ledger.per-call-model-call-attribution`, File 10 §6), the replay contract (`ledger.replay-semantics`, File 10 §11), the sensitivity-aware persistence and retention rules (`ledger.sensitivity-aware-persistence-retention`, File 10 §10), and the hash-chained audit overlay (`ledger.hash-chained-audit-log`, File 10 §16). File 10 also names two built-in hooks this file owns the behavior of: the structured-logging audit hook (`logging.audit_recorder`, priority `-100`) and the telemetry collector (`telemetry.metrics_collector`, observe-only). File 41 specifies what those hooks do: capture log records and compute metric projections. File 41 invents no parallel bus, no parallel ledger, no parallel hook system, and no new top-level event or ledger-entry kind; it consumes the catalogue and registers `Custom { namespace: "observability" }` extensions where it needs specialization. The `trace_context` envelope field is File 10's slot; this file owns its meaning (`observability.tracing`, §5).

### 2.2 With File 17 (Provider Layer, Rate Limits, and Usage Accounting)

File 17 owns the per-call usage record (`TokenUsageRecord`), the `PricingSnapshot`, cost as a derived projection (`provider.cost-as-derived-projection`), the `ProviderHealth` state machine, `RateLimitState`, and the pre-call estimation-accuracy telemetry. File 17 emits these facts to the canonical bus and ledger; "this file emits; consumers subscribe." File 41 is a consumer. The usage, cost, latency, provider-health, rate-limit, and estimation-accuracy metric families (§6) are projections over File 17's records. File 41 surfaces and aggregates them; it never recomputes a cost (it reads File 17's `Some(cost)`/`Unknown` result and never coerces `Unknown` to zero), never stores an unkeyed model-dependent scalar, and never re-derives a token count.

### 2.3 With File 20 (Storage and Persistence)

File 20 owns the storage engine, the projection store, the device-local-versus-syncable partition, the content-addressed blob store, garbage-collection mechanics, storage accounting, and the audit-overlay storage. File 20 states the rule this file obeys: the Telemetry, Logging, and Observability layer "consumes the ledger and storage events this file emits and builds its views as rebuildable projections; it never makes a telemetry view a source of truth." File 41's metric and trace projections register with the projection store and are rebuildable. The device-local diagnostic log stream and the debug ring buffer are device-local data (physically isolated, never synced, per `storage.physical-layout-locality`, File 20 §8.3). Observability retention (§9) is the policy layer over File 20's garbage collection and accounting; File 41 declares what to keep and under which recorded bounds as settings; File 20 reclaims it, with dry-run and per-granularity accounting, never on a time-based correctness clock.

### 2.4 With File 22 (Security, Credentials, and Trust Boundaries)

File 22 owns the backend secret boundary (`secret.backend-boundary`, File 22 §4), whose forbidden destinations explicitly include "a log, an event payload, a ledger entry, telemetry, ... a projection"; the secret-detection and redaction primitives (redaction "before any log, event, persistence, or egress"); the `SecretValue` wrapper whose debug and display forms render a redaction marker; egress governance (the `Public` default / `Sensitive` opt-in / `Secret`-never-raw tiers, the `Denied`-floor-plus-typed-confirmation gate for credential or secret export and irreversible publication, and the egress-destination inspector); and the audit-chain cryptography. File 41 calls the redaction primitive before any log write, trace-payload capture, metric label, or egress; routes every telemetry egress and diagnostic-bundle export through the egress policy; and never emits raw `Secret` material to any observability path. The privacy guarantees of this file are the application of File 22's one boundary at the logging, tracing, metric, debug, and telemetry-egress layers.

### 2.5 With File 39 (Quality Control and Validation)

File 39 owns the inline `Validator` layer that gates live execution and the `Validation`/`Critique` results it produces. File 39 §17.2 and §22 hand this file the quality-metric projections: validator-accuracy, false-positive rate, latency distribution, pass-rate over a window, and most-common violation kinds, computed "as projections over the quality-control ledger entries and validation blocks named here ... without introducing a parallel quality store." File 41 computes those as a metric family (§6) over the reserved quality-control ledger entries (`QualityControlValidatorRan`, `QualityControlViolationDetected`, `ValidationCompleted`, `CritiquePublished`, `CompletionVerificationFired`, `ArtifactValidationStateChanged`) and the `Validation`/`Critique` blocks. It never re-runs a validator, never redefines a `Validation`, and surfaces no continuous-score verdict (the quality figures are aggregates of binary outcomes, per `qc.judge-discipline`, File 39 §6.2).

### 2.6 With File 40 (Evaluation and Benchmarking)

The `40↔41` seam is fixed (File 40 §2.7). File 40 owns the **offline** layer — suites, benchmarks, judge optimization, scoring over recorded and fixture inputs, and the replay engine. File 41 owns the **live** layer — the metric projections that observe execution as it happens. Both consume the same ledger and events; neither introduces a parallel store. The live metrics this file computes are inputs an evaluation may consume (a latency-regression suite reads recorded latency facts); the offline scores File 40 computes are data the Observatory may surface. The Observatory surface renders both: its evaluation data is owned by File 40, its live-metric and trace data by this file, and its version-graph replay by File 11.

### 2.7 With Files 37 and 38 (UI Shell and UI Customization)

File 37 owns the rendering of the Observatory surface and the debug surface (`ui.inspector-presentation`, File 37 §13.2): "traces and execution timelines, validations, retrieval inspections, prompt and context reconstructions ..., policy decisions, run comparisons, evaluation results, and usage/cost/latency metrics, each a projection over the ledger and version graph," and "the live event log (a bounded ring buffer with filtering, search, and high-frequency aggregation), the performance monitor, and the debug toggles," reachable behind a developer affordance, rendering with bounded overhead and no additional active debug-capture, render, subscription, or export overhead when inactive beyond baseline instrumentation, with raw-payload inspection or export gated by File 22 egress, File 06 policy, and sensitivity labels. File 41 owns the **data contracts** behind every one of those: the log query result, the trace projection, the metric series, the ring-buffer event-log contract, the performance-monitor projection, the debug-toggle set, and the diagnostic-bundle. File 38 contributes observability widgets (a usage widget, a context-budget widget, a sync-status widget) over these data contracts. File 41 computes; Files 37 and 38 render; the Observatory and the debug surface are management surfaces (File 25 §14), not work surfaces, and register no `SurfaceContract`.

### 2.8 With Files 04, 11, and 13 (Run Model, Version Graph, Context Assembly)

File 04 owns the run lifecycle, the capability-call pipeline, child runs, cancellation, budgets, and the run presentation (`run.presentation`, File 04 §25) the Observatory's execution timeline projects. File 11 owns the version graph and the forensic reconstruction the Observatory's "what the model saw" view renders. File 13 owns context assembly, token counting, the `BudgetReport`, and the context-pressure boundary (`context.context-pressure`, File 13) the Observatory's context-budget metric surfaces; the `ContextPressureObserved` fact that boundary raises is catalogued in the ledger and run-boundary catalogues (`ledger.entry-kind-catalogue`, File 10 §4.1; `run.boundary-rule`, File 04 §20.1), not owned here. File 41 observes and projects all three; it owns none of their mechanics, computes no token count of its own, and re-derives nothing from live mutable state at replay or reconstruction time (`context.assembly-replay-snapshot`).

### 2.9 With File 42 (Runtime Infrastructure and Lifecycle) and File 43 (Packaging, Platform, and Distribution)

File 42 owns process lifecycle, startup and shutdown orchestration, background-worker scheduling, queues, service supervision, liveness-state classification, and operational remediation. The `41↔42` boundary is: File 41 **observes** operational facts and exposes health projections (§11); File 42 **operates** and remediates. A background worker's `BackgroundWorkerSpawned` / `BackgroundWorkerHeartbeat` / `BackgroundWorkerStopped` / `BackgroundWorkerFailed` facts are emitted by their owning subsystem (`ledger.lifecycle-integration`, File 10 §17.2); File 41 surfaces them as a health projection and operates nothing. File 43 owns crash-handler registration at the platform layer, crash-reporter bundling into the installer, update-channel telemetry distribution, and release-channel analytics. File 41 owns the in-app `DiagnosticBundle` export and the `TelemetryConsent` boundary; the platform crash handler that File 43 registers feeds the same redaction and consent boundary this file defines.

### 2.10 Boundary

This file is the observability layer over execution. It owns: the `Observatory` surface-and-service, the `LogRecord` and `LogLevel`, the `Span`/`Trace`/`TraceContext` model, the `MetricInstrument`/`MetricSeries` model, the correlation model, the telemetry-egress boundary and consent, the debug-surface data contracts, the observability retention policy, the audit/telemetry boundary, the health-observability data contract, the instrumentation-declaration contract, the `observability.*` capability surface, the settings dimensions, and the consequences other specs consume. It does not own the ledger, the event bus, the hook primitive, usage and cost computation, storage and garbage-collection mechanics, secret and egress primitives, the inline validator, the offline evaluation engine, the UI rendering, the run and version mechanics, or the operational and packaging layers.

## 3. The `Observatory`

Anchor: `observability.observatory`

### 3.1 Definition

The `Observatory` is the always-available observability substrate service and its management surface. The service computes and serves the observability projections (logs, traces, metrics) and the egress and bundle operations; the management surface is the projection of that service the user opens to inspect them. The `Observatory` realizes the substrate-service entry `core.substrate-services` (File 01 §2.4) names "logging and evaluation."

The Observatory is:

- a **substrate service**, always on, serving every work surface and control rail; it is not a work surface and registers no `SurfaceContract` (`worksurface.management-surfaces`, File 25 §14)
- a **read-and-project layer**: it queries the ledger and event stream, computes the projections, and serves them; it produces no consequential fact of its own except the device-local diagnostic log stream, which carries no authority
- a **management surface** when presented: an inspector and dashboard rendered into the inspector dock or a secondary window by File 37, classified as a management surface, never a focus work surface
- a **service face** for the agent: the agent invokes the Observatory's read capabilities to inspect its own traces, metrics, and logs (`observability.capability-surface`, §13), subject to the standard agent-exposure rules

The Observatory is not:

- a parallel store of consequential facts — the ledger is the source of truth; the Observatory reads it
- the version graph or the forensic reconstruction engine — File 11 owns those; the Observatory surfaces them
- the evaluation engine — File 40 owns offline suites; the Observatory surfaces their results alongside live metrics
- the audit authority — File 10 and File 22 own the audit overlay; the Observatory surfaces it read-only and never controls whether it runs

### 3.2 The Observatory Panes

The Observatory presents a closed-canonical-plus-`Custom` set of panes, each a projection with an event-first rebuild trigger; the rendering is File 37's, the data contract is this file's:

- **Logs** — the structured-log query and live tail (§4)
- **Traces** — the span/trace tree and execution timeline for a run, turn, or operation (§5)
- **Metrics** — the metric series: latency, throughput, usage, cost, error rate, cache rate, quality, resource, health (§6)
- **Usage and Cost** — the usage and cost projection over `TokenUsageRecord` and `PricingSnapshot` (File 17), per conversation, run, task, day, workspace, role, account, provider, and model
- **Reconstruction** — the "what the model saw at time `t`" forensic view, rendering File 11's version-graph reconstruction and File 13's assembled context (a projection, not owned here)
- **Comparisons and Evaluation** — run comparisons and evaluation-suite results, owned by File 40, surfaced here
- **Policy and Validation** — policy decisions and validation outcomes, owned by Files 06 and 39, surfaced here
- **Audit** — the read-only view of the hash-chained audit overlay (§10), owned by Files 10 and 22, surfaced here
- **Custom** — a registered pane contributed by a subsystem or plugin through the instrumentation-declaration contract (§12.2)

A pane computes nothing the substrate does not already record or that this file does not project from it. A pane honors sensitivity: a `Secret`-classified value renders masked, a `Sensitive` value renders behind the per-surface sensitivity gate, and raw payload inspection or export passes File 22 egress governance and File 06 policy (`ui.inspector-presentation`, File 37 §13.2).

### 3.3 Boundary

The Observatory is the surface and service over the projections. The projections themselves are §§4–6; the rendering is Files 37 and 38; the underlying facts are owned by the substrate specs (Files 04, 06, 10, 11, 13, 17, 39, 40). This file owns the projection contracts and the surface-and-service classification.

## 4. Structured Logging

Anchor: `observability.logging`

### 4.1 Definition

A `LogRecord` is the structured, span-correlated, sensitivity-tagged diagnostic record a service or component emits to report a significant operation, a state transition, a warning, or an error at a chosen verbosity. Logging is the finest-granularity observability family: it carries debug- and trace-level detail the ledger never records, and it is the developer's primary instrument for "find the log line, then trace upward" debugging.

A `LogRecord` is not:

- a ledger entry — the ledger records consequential facts at commit boundaries (`ledger.execution-ledger`, File 10 §3); a log record is diagnostic and carries no authority. A consequential fact is durably the ledger's; a log line about it is supplementary detail correlated to it.
- the source of truth for anything — losing a log record loses diagnostic detail, never a consequential fact (the ledger holds the fact)
- a place for raw secrets — redaction runs before write (§4.5)

### 4.2 The `LogRecord` Shape

Every `LogRecord` carries at minimum: `level` (the `LogLevel`, §4.3); `operation` (the named operation, e.g. the instrumented function or capability step); `service` (the owning service or subsystem); `message` (the human-readable diagnostic text); `fields` (the typed structured key-value detail); `tags` (free labels such as `critical_path`, `compaction`); `timestamp` (full-granularity, for display and ordering fallback, never the correctness basis per `ledger.event-envelope`, File 10 §5.2); `duration_ms` (computed for span-bracketed operations); the `TraceContext` (§5.3) linking the record to its span (`trace_id`, `span_id`, `parent_span_id`); the canonical correlation references (`conversation_id`, `run_id`, `step_id`, `node_id`, `worktree_id`, `backend_id`, `workspace_id`) where applicable, absent rather than null-padded when not; and `sensitivity` (`Public` / `Sensitive` / `Secret`, defaulting up). The structured-tracing substrate the stack commits to (the instrumentation layer `ledger.boundaries-with-adjacent-layers` (File 10 §2.7) names) is the realization behind the contract; the contract is implementation-invariant.

### 4.3 `LogLevel`

`LogLevel` is the closed canonical enum: `Trace`, `Debug`, `Info`, `Warn`, `Error`. `Trace` is verbose flow detail, default-off in production; `Debug` is detailed diagnostics; `Info` is operation start and success; `Warn` is recoverable or degraded conditions (retries, timeouts, degraded modes); `Error` is operation failure. The active minimum level is resolved from the `ATLAS_LOG_LEVEL` bootstrap environment variable (`runtime.bootstrap-config`, File 42 §14) and per-module and per-scope settings overlays. The level filter is a presentation and retention concern, never a correctness one: lowering the level drops diagnostic detail, never a consequential fact.

### 4.4 Emission and the `DebugLog` Event

A `LogRecord` is emitted as a `DebugLog` event (`ledger.app-event-catalogue`, File 10 §5.3) onto the one event bus, `Sensitive` by default. The debug surface (§8) and the Observatory's Logs pane subscribe to it live. A log record does not commit to the durable ledger as a consequential fact; the consequential facts a log line describes are committed by their owning subsystem as ledger entries with the same `TraceContext`, and the log line correlates to them. Backend components emit through the structured-tracing substrate; frontend components emit through a matching logger that batches records into a `log_events` batch (a size threshold and a flush-interval threshold, with `Error`-level records bypassing the queue) — the batch sizes and interval are settings, not hardcoded constants, and the single-record path remains for one-off non-hot-path use.

### 4.5 Redaction Before Write

Redaction runs before any log write, never before display. The secret-detection and redaction primitives (`security.secret-detection-redaction`, File 22) scan every `LogRecord`'s message and fields, the `SecretValue` wrapper guarantees that accidental formatting of secret material renders only a redaction marker, and raw `Secret` material never reaches a log record, the `DebugLog` event payload, the diagnostic stream, or the debug panel (`secret.backend-boundary`, File 22 §4). A `Secret`-classified field persists only as a `safe_description`. Where a log surfaces user-private content, its `sensitivity` is at least `Sensitive`, and export, sync, and egress honor it (§9, §7).

### 4.6 The Device-Local Diagnostic Stream

Beyond the live `DebugLog` events, log records persist to a bounded, device-local, rotating diagnostic stream — the developer- and support-facing log files under the data root's log directory, written in a line-delimited structured format, partitioned by day, run, or conversation as configured. The stream is device-local (never synced, `storage.physical-layout-locality`, File 20 §8.3), bounded (rotation at a configured size threshold, with archived segments pruned per the retention policy, §9), redacted (§4.5), and disposable (its loss costs diagnostic history, never a consequential fact). Session-scoped diagnostic logs (the per-run or per-task execution, prompt, and tool-call records a work surface exposes) are an export projection over the version graph and ledger, not a parallel write path (`coder.session-logging`, the pattern File 27 realizes): the durable facts live in the ledger and version graph, and the session log is a view, written for inspection and export with prompt capture default-off and redaction-on-export.

### 4.7 Internationalization

Operator- and developer-facing diagnostic log messages are written in the project's development language and need not be localized; they are diagnostic instruments, not user-facing copy. Any log-derived string surfaced to the user through the Observatory or a notification is a localizable key resolved through the internationalization system (`ui.i18n`, File 37 §15). Log `fields` carry structured values, not interpolated user strings, so that filtering and correlation operate on typed data.

### 4.8 Boundary

This section owns the `LogRecord`, the `LogLevel`, the emission-as-`DebugLog` contract, the redaction-before-write rule, the device-local diagnostic stream, and the session-log-as-projection rule. The `DebugLog` event kind and the bus are File 10's; the redaction primitive is File 22's; the structured-tracing crate and the frontend transport are realizations File 42 orchestrates; the log-viewer rendering is File 37's; the storage of the diagnostic stream is File 20's.

## 5. Tracing and Spans

Anchor: `observability.tracing`

### 5.1 Definition

A `Span` is the record of one bounded operation's start, end, duration, status, and attributes; a `Trace` is the causal tree of spans that one logical operation produced — a run, a turn, a tool-call chain, a child-run subtree, a workflow execution. Tracing gives the developer and the agent the "what happened, in what order, nested how, taking how long" view that logs and metrics alone do not.

A `Trace` is a **projection**, not a parallel store. The spans of a trace are computed from the causally-linked events and ledger entries the operation already produced: the `EventEnvelope`'s `parent_event_id`, `causal_event_ids`, `sequence`, `sequence_scope`, and `trace_context` (File 10 §5.2), the pipeline events (`ToolCallProposed` → `ToolCallExecuted` → `ToolCallCompleted` / `ToolCallFailed`), the model-call events (`ModelCallStarted` → `ModelCallCompleted` / `ModelCallFailed` / `ModelCallCancelled`), the block-stream events, the routing and child-run events, and the `duration_ms` and `latency_ms` the entries carry. The trace adds no durable record; it is rebuildable from the ledger, and its loss costs a rebuild (`core.projection`, File 01 §6.11). A trace assembled while an operation is still in flight, crashed, or missing a terminating event is marked partial or in-progress; partial traces are never presented as complete records.

### 5.2 The `Span` Shape

A `Span` carries: `span_id` (stable within the trace); `parent_span_id` (the enclosing span, absent for a root span); `trace_id` (the trace it belongs to); `operation` (the named operation); `kind` (the span category — model call, tool call, agent step, capability invocation, retrieval, child run, validation, or a registered extension); `start` and `end` (full-granularity timestamps for display, ordering by sequence); `duration_ms`; `duration_accuracy` (`Exact` when computed within one monotonic clock domain or from a recorded source duration, `Approximate` when start and end cross backend, renderer, sandbox, or external-client clock domains); `status` (`Ok`, `Error`, `Cancelled`, `Incomplete`, `Unknown`, derived from the terminating event when one exists); `attributes` (typed structured fields, sensitivity-tagged); and the correlation references (`run_id`, `step_id`, `node_id`, `backend_id`, `conversation_id`). A span with no recorded terminating event is `Incomplete` or `Unknown`, never defaulted to `Ok` and never silently dropped. A span's boundaries align with the existing event boundaries; the tracing layer does not introduce new instrumentation points beyond those events plus the structured-tracing substrate's function-level spans.

### 5.3 `TraceContext` and Propagation

`TraceContext` is the propagation envelope `ledger.event-envelope` (File 10 §5.2) carries on every event and the error-recording ledger entries `ledger.boundaries-with-adjacent-layers` (File 10 §2.7) carry optionally on every recorded `AppError`: `trace_id` (the logical operation), `span_id` (the current span), and `parent_span_id` (the enclosing span). A span identity is recorded in `TraceContext` when available; when older or partial instrumentation omits it, replay derives a deterministic fallback `span_id` from the canonical source event or ledger-entry identities and the declared operation-boundary rules. Projection-time random span ids are invalid because they make trace replay unstable. The shape is compatible with the standard distributed-trace-context format so that an optional export (§7) interoperates. Propagation rules:

- a root operation (a user-originated run, an automation fire, an external-protocol invocation) opens a root `trace_id`
- a child operation (a child run per `run.child-runs-multi-agent-work`, File 04 §16; a sub-workflow node; a model or tool call within a step) inherits the `trace_id` and opens a child span whose `parent_span_id` is the enclosing span
- cross-process and cross-tab coordination (`ledger.streaming-live-partials`, File 10 §12.6) preserves the `trace_context` across the transport, so a trace spans the backend, the renderer, a sandboxed process, and a connected external client
- a typed error carries the `TraceContext` of the span where it originated, so the debug surface can jump from an error to the full span history that produced it

Ordering inside a trace is sequence-first. Full-granularity timestamps and durations support display and diagnostics, but wall-clock order across clock domains is never the canonical order.

### 5.4 Trace Privacy

Span attributes default to metadata only. Prompt text, model completions, tool arguments, tool results, and retrieved content are not captured into span attributes by default; capturing them is an explicit, scoped, settings-gated opt-in, and even when enabled the capture passes redaction (§4.5) and carries the source content's sensitivity. The default mode records that an operation happened and how long it took, not what private content flowed through it. This is the trace-layer realization of `secret.backend-boundary` (File 22 §4) and the local-first privacy posture.

### 5.5 Boundary

This section owns the `Span`, the `Trace`, the `TraceContext` semantics, the trace-as-projection rule, the propagation rules, and the trace-privacy default. The envelope field and the causal-link fields are File 10's; the run and child-run structure is File 04's; the version-graph reconstruction the timeline also renders is File 11's; the trace-tree rendering is File 37's; the offline replay that re-runs a trace is File 40's.

## 6. Metrics

Anchor: `observability.metrics`

### 6.1 Definition

A `MetricInstrument` is the typed declaration of a measured quantity; a `MetricSeries` is the rebuildable aggregate projection of that quantity over scope and dimensions. Metrics give the "how much, how fast, how often, at what cost, how well" numerical view. Every authoritative metric is a projection over lossless ledger entries or other source-of-truth records. Diagnostic-stream-derived metrics are allowed only as best-effort diagnostics, marked `DiagnosticOnly`, and visibly unavailable when the disposable stream has rotated or been pruned. No metric is a source-of-truth time series, and no metric stores a model-dependent value as an unkeyed scalar.

### 6.2 The `MetricInstrument` and Closed Metric Kinds

A `MetricInstrument` declares: `name` (the namespaced metric name); `kind` (the closed metric kind); `unit`; `dimensions` (the typed labels by which the series is broken down — provider, model, role, surface, capability, workspace, scope, error class, where applicable); the `source` (the ledger query, source-of-truth record, or event subscription that feeds it); `accuracy_class` (`Exact` or `Approximate`, derived from the source delivery class); `authority_class` (`Authoritative` or `DiagnosticOnly`); aggregation/window semantics; retention/default visibility; replay behavior; owner/source; and `sensitivity`. The closed canonical metric-kind set:

- `Counter` — a monotonic count (calls, errors, cache hits, tokens, fires)
- `Gauge` — a point-in-time value (active runs, queue depth, memory, context-window fraction)
- `Histogram` — a distribution (latency, duration, token-count distribution), summarizable to percentiles

plus `Custom { namespace, name }` for a subsystem- or plugin-declared instrument registered through the instrumentation-declaration contract (§12.2). A metric value that depends on a model or provider is always keyed by `(provider_id, model_id, tokenizer_id)` where applicable (`core.explicit-rejections`, File 01 §8); an unkeyed model-dependent metric is rejected at registration.

Metric dimensions are cardinality-governed. A dimension is one of: a bounded label suitable for aggregation; a high-cardinality exemplar or correlation reference (request id, trace id, file path, URL, raw user id) that may be stored for drill-down but is not a default aggregate label; or a forbidden raw value (`Secret`, raw user content, untrusted payload text, credential material). Custom instruments declare each dimension's class at registration.

### 6.3 Metric Families

The canonical baseline metric families, each a projection over the named substrate:

- **Latency and duration** — model-call `latency_ms` and `inference_time_ms`, tool-call duration, capability-step timings, render-frame timing, database-query timing, retrieval `took_ms`, time-to-first-token; over `ModelCallCompleted`, `ToolCallCompleted`, and the `duration_ms` fields entries and spans carry
- **Throughput** — tokens per second during streaming, calls per interval; over the streaming and model-call events
- **Usage and cost** — input, output, cache-creation, cache-read, reasoning, and multimodal token counts, and the derived cost; over File 17's `TokenUsageRecord` and `PricingSnapshot` (cost is read from File 17's `provider.cost-as-derived-projection`, never recomputed, never coerced from `Unknown` to zero); broken down per conversation, run, task, day, workspace, role, account, provider, and model
- **Error and crash rate** — typed-error counts by class, provider-error counts, tool-failure counts, parse-failure counts, panic and crash counts; over `TypedErrorRaised`, `ModelCallFailed`, `ToolCallFailed`, and the typed-error taxonomy, using the per-error-class classification the entries already carry
- **Cache rate** — cache hit and miss rates over the model-request cache markers, retrieval cache, fetch cache, and capability output cache; over the cache-token fields and the cache-outcome events
- **Quality** — validator-accuracy, false-positive rate, latency distribution, pass-rate, and most-common violation kinds (`qc.events-metrics`, File 39 §17.2); over the quality-control ledger entries and `Validation`/`Critique` blocks; expressed as aggregates of binary outcomes, never as per-validation continuous scores
- **Provider health and rate limit** — provider health-state transitions and rate-limit consumption (`ProviderHealthChanged`, `RateLimitSnapshotReconciled`); over File 17's records
- **Resource** — process memory, CPU, disk, and equivalent host-resource usage as observed values (§8), the observability of resource consumption, not its control
- **Custom** — a registered family contributed by a subsystem or plugin (§12.2)

Metrics projected over `lossless_consequential` sources may be `Exact` and authoritative. Metrics projected over `coalescible` or `sampled_diagnostic` event sources may be exact about the delivered/coalesced stream, but are `Approximate` about the underlying raw activity and must surface that status. Gating, quality, cost, billing, policy, and evaluation metrics must derive from lossless source-of-truth records, never from a coalesced, sampled, or disposable diagnostic stream.

### 6.4 Metrics Are Aggregates, Never Verdict Scores

A metric is a count, a rate, a distribution, or a gauge. It is never a one-to-five or zero-to-one quality verdict on a single item: per-item verdicts are `Validation` outcomes (`Passed`/`Failed`/`Inconclusive`) owned by File 39, and a continuous quality figure is the aggregate of those binary outcomes over a window (`qc.judge-discipline`, File 39 §6.2; the named anti-pattern in File 40 §"Scorer"). The Observatory surfaces pass rates, false-positive rates, and accuracy distributions; it never surfaces a fabricated continuous "quality score" for one output.

### 6.5 Boundary

This section owns the `MetricInstrument`, the closed metric-kind set, the `MetricSeries` projection contract, the baseline metric families, and the no-verdict-score rule. The records the metrics aggregate are owned by their producing specs (Files 04, 06, 10, 17, 39); cost computation is File 17's; the metric-dashboard rendering is Files 37 and 38's; offline metric aggregation over recorded runs is File 40's.

## 7. Privacy-Preserving Telemetry and Egress

Anchor: `observability.telemetry-egress`

### 7.1 The Local-First Zero-Egress Default

No log, trace, metric, or diagnostic leaves the device by default. ATLAS3 is local-first (`core.product-thesis`, File 01 §1), there is no Atlas-hosted telemetry server, and there is no built-in dependency on a third-party telemetry or analytics service. All observability data is, by default, computed, stored, and inspected entirely on the device. Every egress is opt-in, per-category, per-device by default, and revocable.

### 7.2 `TelemetrySink` and `TelemetryConsent`

A `TelemetrySink` is a typed, registered, off-by-default egress destination: a standard open-telemetry export endpoint (an OpenTelemetry-protocol collector the user runs or trusts), an opt-in crash-report destination, or an opt-in usage-analytics destination. Each sink declares its category, its destination, the data classes it would export, and its credential reference (vault-held, never inline). A sink does not activate until the user grants a `TelemetryConsent`: a per-category, durable, revocable, audit-visible record (settings, File 15) stating which observability data classes the user permits to leave the device, to which destination. Active consent is per-device/per-installation by default. Syncable settings may carry inactive sink templates and preferences, but a different device must activate egress locally; cross-device active consent is allowed only by explicit typed-confirmed user action naming the device or scope and still satisfying local credential and egress policy. Revoking consent deactivates the sink. No lease, no `auto-decide` mode, no profile, and no automation may grant telemetry consent on the user's behalf (the same direct-user-governed rule `security.egress-governance` (File 22) applies to credential and secret egress).

### 7.3 Redaction, Anonymization, and Sensitivity Before Egress

Every export through a `TelemetrySink` passes the egress pipeline:

- redaction runs first (§4.5; `security.secret-detection-redaction`, File 22): no raw `Secret` material ever egresses — it is a forbidden destination (`secret.backend-boundary`, File 22 §4)
- sensitivity gates the class: `Public` data may egress under consent; `Sensitive` data egresses only when the consent explicitly includes the `Sensitive` class; `Secret` never egresses raw (only safe descriptions), and credential or secret export and irreversible publication carry the `Denied` floor plus typed confirmation (`portability.sensitivity-egress`, File 21 §12; `security.egress-governance`, File 22)
- anonymization applies to any opt-in egress that includes identifiers: stable identifiers are pseudonymized with a keyed function over a declared canonical input, scoped to the sink, bundle, or consent scope; the secret salt/key is vault-held or export-context-held, and rotation occurs when the user resets that telemetry identity. Content-addressed hashes are for integrity, package verification, and deduplication, not privacy pseudonymization.
- the egress is a policy-gated capability (§13) recorded in the ledger and the audit overlay (an egress is a security-relevant operation, File 10 §16.4), and it passes the egress-destination inspector (`security.egress-governance`, File 22) and per-hop redirect re-validation

### 7.4 The Diagnostic Bundle

A `DiagnosticBundle` is a user-initiated, redacted, sensitivity-filtered export of recent logs, traces, metrics, and selected ledger excerpts, assembled for the user to inspect or share when reporting a problem. It is the in-app diagnostics export, distinct from the platform crash handler File 43 registers. The bundle passes the same egress pipeline (§7.3): redaction first, sensitivity filtering with `Public`-only by default and `Sensitive` only on typed confirmation, `Secret` never. It is a governed diagnostic export with a manifest, integrity record, dependency list, and redaction/omission records, but it is not a `PortablePackage` profile unless File 21 explicitly adds such a profile; it has no import, recovery, or round-trip guarantee. Assembling a bundle records a ledger entry; sharing it is an egress the user explicitly performs.

### 7.5 The Optional Export Protocol

The export protocol behind a `TelemetrySink` is the standard open telemetry protocol, implemented behind the sink contract as a replaceable backend with a no-op fallback when no collector is configured. Naming the protocol fixes interoperability, not a dependency: ATLAS3 ships no collector and requires none; the export path exists for a user or operator who chooses to run one. The provider-specific wire details of any collector, crash service, or analytics backend live in the sink's adapter, never in this contract.

### 7.6 Boundary

This section owns the zero-egress default, the `TelemetrySink` and `TelemetryConsent` contracts, the egress pipeline (redaction, anonymization, sensitivity gating), the `DiagnosticBundle`, and the optional-export-protocol framing. The redaction primitive, the egress policy semantics, and the secret boundary are File 22's; governed movement and egress mechanics are File 21's; the policy gate is File 06's; the audit recording is File 10's; the platform crash handler and update-channel distribution are File 43's.

## 8. The Debug Surface and Developer Observability

Anchor: `observability.debug-surface`

### 8.1 Definition

The debug surface is the developer- and advanced-user-facing observability surface that renders the live event flow, the performance monitor, and the diagnostic toggles. File 41 owns its data contracts; File 37 renders it (`ui.inspector-presentation`, File 37 §13.2). It is reachable behind a developer affordance (a bootstrap environment flag or a keyboard shortcut), renders with bounded overhead, and adds no additional active debug-capture, render, subscription, or export overhead when inactive beyond baseline instrumentation.

### 8.2 The Live Event Log Ring Buffer

The live event-log data contract is a bounded in-memory ring buffer of recent `AppEvent`s with their envelopes, filterable by event kind, scope (conversation, run, session), sequence range, event id, and optional display time range. Free-text search runs only over redacted fields visible to the current viewer after sensitivity filtering; the ring buffer must not build an index over raw hidden event content. The buffer capacity is a setting (a bounded number of recent events; the canonical default keeps it small enough for negligible memory and large enough to span a typical operation). Overflow is observable: the buffer reports its dropped count (the `EventBufferOverflow` signal, File 10 §5.5) rather than silently losing events without trace. High-frequency event kinds reach the buffer already aggregated under the delivery-class and aggregation policies File 10 §5.5 owns (token deltas batched, cursor and scroll coalesced, mouse moves suppressed below a threshold) — the debug surface consumes that aggregation; it does not re-implement it. The buffer is device-local, never synced, and disposable.

### 8.3 The Performance Monitor

The performance-monitor data contract is a projection of recent operation timings and resource usage: agent-step duration with its phase breakdown, model-call and tool-call latencies, database-query timings with a slow-query threshold, streaming throughput, and host-resource gauges (memory and CPU). The thresholds (the slow-query threshold, the resource-warning thresholds) are settings, not hardcoded constants. The performance monitor surfaces observed timing and resource facts; it does not throttle, kill, or remediate (that is the run model's and File 42's). Resource gauges are sampled (§8.5).

### 8.4 Debug Toggles

The debug-toggle data contract is a typed set of developer diagnostics the user can enable or disable at runtime without restart: verbose-event logging, high-frequency aggregation on or off, performance-bottleneck highlighting, state-awareness tracing, transport-call logging, and render diagnostics. Toggles persist as settings (File 15). Enabling a deeper-capture toggle is an explicit state change with visible scope and retention (`ui.inspector-presentation`, File 37 §13.2): the user sees what is being captured and for how long, and the capture passes redaction and sensitivity. The debug surface activates behind a developer affordance (the `ATLAS_DEBUG` bootstrap flag (`runtime.bootstrap-config`, File 42 §14) or its equivalent and a keyboard shortcut); in production with the affordance off, debug-specific capture, subscriptions, rendering, and export work do not run beyond baseline instrumentation.

### 8.5 Resource-Metric Sampling — the Flagged Periodic Exception

Most observability is event-first (§11; `core.event-first-by-default`, File 01 §7.15): metric projections rebuild on event commit, traces assemble from events, and logs stream by push. The one legitimate periodic case is the sampling of a host-resource gauge — process memory, CPU, disk, and equivalent — that has no change-event source. A resource gauge is sampled at a configured interval as the flagged, configurable fallback `core.event-first-by-default` (File 01 §7.15) permits "for sources that emit no change events." The sampling interval is a setting; sampling is never a correctness condition (no decision depends on the sample arriving); and the sampling is the explicit exception this file flags, not a hidden poll. Every other observability cadence — a flush interval that batches a high-frequency stream, an aggregation window, a refresh of a rendered projection — is a delivery convenience owned by File 10 §5.5 or a presentation convenience, never a correctness mechanism.

### 8.6 Boundary

This section owns the debug-surface data contracts: the ring-buffer event log, the performance-monitor projection, the debug toggles, and the resource-sampling exception. The aggregation and delivery classes are File 10's; the rendering, the keyboard activation, and the panel layout are File 37's; the storage of the buffer is device-local per File 20; the resource-control mechanics (limits, kills) are the run model's and File 42's.

## 9. Observability Retention

Anchor: `observability.retention`

### 9.1 Retention Is Policy Over the One Garbage Collector

Observability retention is the policy layer over the storage-side garbage collection `storage.retention-gc-accounting` (File 20 §11) realizes. This file declares what observability data to keep as settings; File 20 reclaims it, with a dry-run that reports what would be removed before anything is, and storage accounting at every granularity (`core.non-destructive-by-default`, File 01 §7.13). There is no parallel retention engine and no observability-owned deletion path.

### 9.2 Retention by Data Class

- **The diagnostic log stream** is bounded device-local rotating storage: rotation at configured size/count/storage-accounting limits by default, archived-segment time horizons only when explicitly chosen by the user or an active profile, and the live ring buffer capped at a configured event count. All thresholds, caps, and opt-in horizons are settings; the canonical defaults are state-driven and chosen to bound disk and memory while preserving a useful diagnostic window.
- **Traces and metrics** are rebuildable projections (`core.projection`, File 01 §6.11): their retention is the retention of the underlying ledger entries (`ledger.sensitivity-aware-persistence-retention`, File 10 §10.4) they project, and a pruned or stale projection costs a rebuild, never data loss. Older metric series may be downsampled into coarser rollups (a documented retention strategy) rather than dropped, preserving long-horizon trends at lower resolution.
- **Sensitivity gates retention**: `Sensitive` observability data may carry stricter storage limits or an explicit shorter horizon than `Public`, with summarize-on-trim where a long-horizon summary is useful; `Secret` raw content is never retained (only safe descriptions, which follow the `Sensitive` policy).

### 9.3 No Time-Based Pruning as Correctness

Size, count, and storage-accounting bounds are the default retention shape. Time horizons are settings the user or selected profile explicitly chooses, applied by the storage layer as recorded, opt-in policy, never as a hidden time-based correctness clock (`core.event-first-by-default`, File 01 §7.15; `storage.retention-gc-accounting`, File 20 §11.3). A retention or pruning action is itself a recorded fact; no observability data disappears without a recorded policy transition. The user inspects and reclaims observability storage at every granularity (per category, per workspace, per run) through the storage-accounting surface, never being silently capped.

### 9.4 Boundary

This section owns the observability retention policy and the rebuildable-projection-versus-bounded-stream classification. The garbage-collection mechanics, the storage accounting, and the dry-run are File 20's; the sensitivity classes and the per-class ledger retention are File 10's; the cross-device propagation of any retention decision is File 21's.

## 10. The Audit Boundary

Anchor: `observability.audit-boundary`

The boundary between observability and the hash-chained audit overlay is sharp and load-bearing. Observability (logs, traces, metrics, telemetry) is diagnostic visibility: it is opt-out-able, bounded, redacted, retention-governed, and may be disabled. The hash-chained audit overlay (`ledger.hash-chained-audit-log`, File 10 §16; cryptography `security.audit-crypto`, File 22) is tamper-evident security integrity: it is per-device, never synced, never disabled even when telemetry and logging are disabled, and pruned only through a recorded policy transition.

File 41 **surfaces** the audit overlay and **owns** none of it. The Observatory's Audit pane (§3.2) renders the audit log read-only through a `ReadOnly` capability (§13) over Files 10 and 22; it presents the chain, its verification state, and the security-relevant operations it records (approvals, leases, typed confirmations, floor violations, source approvals, credential and secret operations, system mutations, hard deletes, denied-floor overrides). Disabling telemetry never disables audit. Lowering the log level never affects the audit chain. An `AuditChainTamperDetected` event (File 10 §16.5) surfaces in the Observatory with the same severity File 10 assigns and halts the affected device's sync, but the detection, the chain construction, the membership, and the verification are File 10's and File 22's; File 41 renders and alerts, and changes nothing.

## 11. Operational-Health Observability

Anchor: `observability.health`

### 11.1 The Health-Status Data Contract

File 41 owns the observability data contract for system health: a composite, projection-derived health snapshot (host resources, background-worker liveness, provider health, storage health, sync status, connector connection state) assembled from the facts the owning subsystems emit. The snapshot is a projection; it computes nothing the substrate does not record and remediates nothing.

### 11.2 The Observe-Not-Operate Boundary (41↔42)

File 41 observes operational facts and exposes them; it operates nothing. Background workers (the memory consolidator, the scheduler, the watch poller, the audit writer, the lineage tracker) emit `BackgroundWorkerSpawned` / `BackgroundWorkerHeartbeat` / `BackgroundWorkerStopped` / `BackgroundWorkerFailed` (`ledger.lifecycle-integration`, File 10 §17.2); File 41 surfaces their liveness as a health projection. Provider health transitions (`ProviderHealthChanged`, File 17), connector connection states (`integration.mcp-lifecycle`, File 36 §5), and storage integrity events (File 20) surface the same way. File 42 owns the worker scheduling, the restart, the queue, the supervision, and the remediation; File 41 owns the health view over them. There is no File 41 watchdog that restarts, kills, or remediates anything.

### 11.3 Liveness Is Event-First; Resource Is the Sampled Exception

Worker and connection liveness are event-first: the owning runtime, worker, provider, connector, or subsystem emits typed lifecycle and liveness-state facts (`Healthy`, `Degraded`, `Stalled`, `Failed`, or equivalent, from the closed `WorkerState` set File 42 §6.2 owns), and the health projection consumes them. File 41 does not infer staleness from missing heartbeats and owns no liveness timeout, cooldown, restart, or remediation policy; those belong to File 42 or the owning subsystem. The scheduled-health-ping anti-pattern (`provider.provider-health` File 17 §12.4's rejected scheduled ping; `integration.connection-recovery` File 36 §7.5's no-scheduled-health-ping rule for connectors) is rejected here too. The one sampled signal is the host-resource gauge (§8.5), flagged and configurable because it has no change-event source.

### 11.4 Boundary

This section owns the health-status data contract and the observe-not-operate boundary. The worker, queue, and supervision mechanics are File 42's; the provider-health state machine is File 17's; the connector connection state is File 36's; the storage health is File 20's; the rendering of the health card is File 37's.

## 12. Per-Surface and Per-Subsystem Observability

Anchor: `observability.surface-aliasing`

### 12.1 Surface Affordances Are Presentations of the One Service

A work surface presents observability under its own vocabulary — a Coder activity feed and session log, a Web activity panel and network log, a Data Processor lineage view, a System Agent health card and audit viewer, a usage-and-cost panel, an LLM-calls-overview window — and each is a presentation of the one Observatory service over the one substrate, not a parallel observability store. The surface's affordance aliases the canonical projections (§§4–6) and the canonical capabilities (§13); it introduces no private telemetry database, no private metrics store, and no private trace backend. A surface-specific "activity feed" is a filtered projection of the event stream scoped to the surface's run; a "cost panel" is the usage-and-cost metric family filtered to a scope; a "session log" is the diagnostic-stream-and-version-graph projection (§4.6).

### 12.2 The Instrumentation-Declaration Contract

A capability, surface, or subsystem may declare custom observability — custom metric instruments, custom span kinds, custom log categories — through one path: the instrumentation declaration. A capability's declaration may carry a telemetry schema naming the metrics and spans it emits (the field lives in the `CapabilityDeclaration`, File 05); a subsystem registers custom metric instruments and `Custom` span and log kinds as `Custom { namespace, name }` event and ledger-entry extensions through the one proposal-first registration path (`capability.runtime-mutation`, File 05 §16.2; `ledger.custom-kind-registration`, File 10 §4.3), gated by source approval and trust (`policy.source-approval-flow`, File 06 §9). A custom metric instrument must declare source query/subscription, kind, unit, dimension classes, aggregation/window semantics, sensitivity, retention/default visibility, replay behavior, authority class, accuracy class, and owner. Custom metric-sample events are observation facts, not consequential truth; consequential facts must be committed by the owning subsystem's ledger entries. There is no parallel instrumentation registry: a custom metric is a registered instrument over registered events, a custom span is a registered span kind, and a custom log category is a tagged `DebugLog`. A registered custom instrument that would store an unkeyed model-dependent scalar, an undeclared source, unbounded hidden dimensions, or a custom export that would bypass redaction or egress governance, is rejected at registration.

### 12.3 Boundary

This section owns the surface-aliasing rule and the instrumentation-declaration contract. The capability-declaration field set is File 05's; the custom-event and custom-ledger-kind registration is File 10's; the source-approval gate is File 06's; the per-surface affordance rendering is Files 37 and 38's; each surface's specific feeds, panels, and logs are owned by that surface's spec, which aliases this layer.

## 13. The Capability Surface

Anchor: `observability.capability-surface`

The `observability.*` capability family is the single invocation path for every observability operation, exposed uniformly to the agent, the user, the command rail, automations, and external clients (`core.extension-planes`, File 01 §6.14), surface-and-service in nature with no observability-mode field. The capabilities (declared as canonical built-ins per File 05, gated per File 06):

- `observability.query_logs(filter)` / `observability.tail_logs(filter)` — query or live-tail the diagnostic stream and `DebugLog` events under a sensitivity-aware filter (`ReadOnly`; replay class depends on selected source: ledger/session-log projections are `deterministic_replayable`, diagnostic-stream queries are availability-bound and may return typed pruned/unavailable results)
- `observability.query_traces(filter)` / `observability.get_trace(trace_id)` — query traces or resolve one trace's span tree (`ReadOnly`)
- `observability.query_metrics(instrument, dimensions, window)` / `observability.get_metric(instrument)` — compute a metric series (`ReadOnly`; `deterministic_replayable` for authoritative lossless sources, availability-bound for `DiagnosticOnly` diagnostic-stream sources)
- `observability.query_health()` — the composite health snapshot (`ReadOnly`)
- `observability.query_audit(filter)` — read-only view of the audit overlay through Files 10 and 22 (`ReadOnly`)
- `observability.set_log_level(scope, level)` / `observability.set_debug_toggle(toggle, enabled)` — adjust diagnostic verbosity and toggles as `settings.write` adapters (`capability.adapter-capabilities`, File 05 §17.4) over the settings dimensions (§15), so the write goes through the one settings path (`WorkspaceWrite`)
- `observability.register_metric(instrument)` / `observability.register_log_category(declaration)` — register a custom instrument or log category through the instrumentation-declaration contract (§12.2; source-approval-gated for non-builtin sources)
- `observability.export_diagnostics(scope, options)` — assemble and export a `DiagnosticBundle` through the egress pipeline (§7.4; egress-governed, policy-gated, and explicitly user-shared)
- `observability.set_telemetry_consent(category, destination, classes)` / `observability.list_sinks()` — grant, revoke, or inspect telemetry consent and sinks (user-only, never agent-initiated; consent grant carries the egress gate)

Reads are `ReadOnly` and agent-invocable under the standard agent-exposure rules; the agent may inspect its own traces, metrics, and logs to reason about its behavior. Exports and consent changes are gated: a diagnostic-bundle export passes egress governance, and a telemetry-consent grant is user-only and policy-gated (`security.egress-governance`, File 22). Surface- and subsystem-specific observability affordances expose family-namespaced adapter capabilities over these (a Coder session-log export, a Web network-log query, a System Agent health query) per `capability.adapter-capabilities` (File 05 §17.4); the underlying projection is always the canonical one.

## 14. Events

Anchor: `observability.events`

Observability emits and consumes through the canonical event and ledger kinds already reserved; it introduces no new top-level `AppEvent` or `LedgerEntryKind`. It consumes the full catalogue (`ledger.entry-kind-catalogue`, File 10 §4.1) as its data source, and it emits through `DebugLog` (the structured log record), `Heartbeat` and `BackgroundWorkerHeartbeat` (liveness facts it surfaces but does not classify), `EventBufferOverflow` (buffer drop it reports), and `TokenCountEstimationTelemetry` (the estimation-accuracy fact File 17 emits and File 41 aggregates). Observability-specific specialization — a custom metric-sample event, a telemetry-egress lifecycle event, a diagnostic-bundle-assembled event — is registered as `Custom { namespace: "observability" }` through the one mechanism (`ledger.custom-kind-registration`, File 10 §4.3). Custom metric-sample events are diagnostic observations unless backed by an owning subsystem ledger entry. A telemetry-egress operation and a diagnostic-bundle export are security-relevant and record into the audit overlay (`ledger.hash-chained-audit-log`, File 10 §16.4), defaulting to `Sensitive`. There is no parallel observability bus.

## 15. Settings, Profiles, and Customization

Anchor: `observability.settings`

### 15.1 Configurable Dimensions

Every observability mechanism is configurable through the canonical settings system (`core.settings-system`, File 01 §6.8) resolved through the canonical source stack (`settings.scopes-profile-contexts-overlays`, File 15 §5.2). At minimum, settings support:

- the active `LogLevel` per scope and per module, and the `ATLAS_LOG_LEVEL` bootstrap default (`runtime.bootstrap-config`, File 42 §14)
- the diagnostic-stream rotation size/count/storage bounds, any explicitly selected archived-segment time horizon, and the live ring-buffer event-count cap
- the frontend log-batch size threshold and flush interval, and the `Error`-bypasses-the-queue rule
- the trace-payload capture policy (metadata-only by default; prompt, completion, tool-argument, and tool-result capture explicitly opt-in and scoped)
- per-metric-instrument enablement, dimensions and cardinality classes, accuracy/authority visibility, and downsampling-rollup horizon
- the performance-monitor thresholds (slow-query, resource-warning) and the resource-sampling interval
- the debug toggles and the developer-affordance gate
- per-class observability retention limits (`Public`, `Sensitive`), optional explicit horizons, and the summarize-on-trim behavior
- the registered `TelemetrySink` set, each off by default; inactive sink templates and preferences; and the per-category, per-device active `TelemetryConsent`
- the per-event-kind delivery-class and aggregation overrides this layer consumes (owned by File 10 §5.5; named here as the dimensions observability reads)

### 15.2 The No-Hidden-Branch Rule

Observability behavior is product variation expressed in settings, never hidden hardcoded branches. The log level, rotation thresholds, ring-buffer cap, batch and flush parameters, sampling interval, retention limits and explicit horizons, trace-capture policy, and telemetry consent are all configurable; the canonical defaults are the best overall option (local-first, privacy-first, low-overhead, bounded), and progressive disclosure keeps the default experience clean while making depth reachable. A duration, threshold, cap, or interval that source material expresses as a constant (a rotation size, a buffer count, a sampling interval, a flush cadence) is a configurable default here, never a frozen constant.

### 15.3 Agent Exposure

Per `policy.agent-exposure-policy-settings` (File 06 §16.4): the log-level, retention, and aggregation settings are `OnRequest` (the agent reads them on demand); the registered `TelemetrySink` set, inactive sink templates, and `TelemetryConsent` records are `OnRequest` to read but their mutation is user-only; the active debug-toggle set is `OnRequest`. The agent never silently enables an egress, never grants consent, and never lowers a sensitivity classification.

### 15.4 Boundary

The settings cascade, profiles, overlay resolution, and bootstrap variables are File 15's; the delivery-class and aggregation defaults are File 10's; this file names the dimensions and the no-hidden-branch discipline.

## 16. Persistence, Locality, and Replay

Anchor: `observability.persistence-replay`

### 16.1 What Is Durable, Device-Local, and Computed

The durable, device-local observability state is the bounded rotating diagnostic log stream, the device-local audit-overlay view's source (owned by File 10/20, surfaced here), the live ring buffer (in-memory, device-local), and the registered metric-instrument and log-category declarations (settings and capability declarations). The computed, rebuildable state is every trace and every authoritative metric series — projections over the ledger (`core.projection`, File 01 §6.11), rebuildable, whose stale or corrupt cost is a rebuild, never data loss. `DiagnosticOnly` metric projections over the disposable diagnostic stream are availability-bound and never required for reconstructing consequential facts. There is no durable parallel store of consequential facts; the ledger holds those.

### 16.2 Locality

The diagnostic log stream, the live ring buffer, the debug toggles' device state, the resolved metric caches, active `TelemetryConsent`, and the audit overlay are device-local and never sync (`storage.physical-layout-locality`, File 20 §8.3; `ledger.hash-chained-audit-log`, File 10 §16.3). Telemetry-sink templates and inactive preferences may sync as ordinary settings under their locality and sensitivity rules (File 15, File 21), but each device activates egress locally, and the credential a sink holds is vault-referenced and never replicates (`secret.backend-boundary`, File 22 §4). No raw secret and no unredacted `Sensitive` observability content is materialized, exported, or synced.

### 16.3 Replay

Replay re-derives observability from recorded facts, never from live mutable sources (`context.assembly-replay-snapshot`). A trace reconstructed during replay is rebuilt from the recorded ledger entries and events of the replayed run, reproducing the original span tree and span identities from recorded `TraceContext` or deterministic fallback identity rules; a metric series reconstructed during replay aggregates the recorded entries deterministically. Diagnostic-stream queries are availability-bound: if the local stream has rotated or been pruned, replay returns a typed unavailable/pruned result rather than inventing data. Observability re-queries no live endpoint and re-derives no model-dependent value at replay time; it reads what was recorded, exactly as `provider.token-source` (File 17) reconstructs usage from the recorded record rather than re-querying the provider. Wherever an observability identity or an export integrity depends on a hash, the hash is computed over a declared `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14), never over physical storage bytes; this file defines no new hash and reuses the ledger, block, and package hashes of Files 10, 08, and 21. Privacy pseudonyms are separate keyed values and are not content-addressed hashes.

### 16.4 Boundary

Storage realization is File 20's; sync and the portable bundle are File 21's; the audit-overlay storage and verification are Files 10 and 22's; the replay engine is File 40's. This file specifies what observability is durable, what is device-local, what is computed, and the replay-equivalence and canonical-hash contracts.

## 17. Operating Constraints

Anchor: `observability.operating-constraints`

The observability layer operates under these constraints; the tunable parameters within them are configurable as settings (§15) with the stated canonical defaults:

- **Bounded overhead.** Observability instrumentation is cheap and asynchronous: event logging and metric projection impose bounded baseline overhead on the active path, the diagnostic stream writes asynchronously, the live buffer is bounded, and debug-specific capture, subscriptions, rendering, and export work do not run when the developer affordance is inactive. Observability never becomes the bottleneck it measures.
- **Never blocks observed execution.** Observability is observe-only: a log write, metric update, or span close never blocks, gates, or alters the operation it observes. User-invoked diagnostic export runs as its own governed, cancellable operation; it must not block the observed operation. The observe-only authority of the logging and telemetry hooks (`ledger.authority-classes`, File 10 §7.4) is structural — a non-`Continue` decision from an observe-only hook is downgraded to `Continue` plus a warning.
- **Event-first.** Observation, projection rebuild, and reactivity are event-driven; the only sampled signal is the host-resource gauge that has no change-event source (§8.5), flagged and configurable, never a correctness condition.
- **Privacy-first.** Local-first and zero-egress by default; redaction before write and before egress; sensitivity gates retention, export, sync, and egress; raw `Secret` never reaches any observability path; egress is opt-in, per-category, per-device by default, revocable, and user-only.
- **Transparency.** Every observability surface shows what it is capturing and at what retention; enabling deeper capture is an explicit, scoped, recorded state change; the user inspects and reclaims observability storage at every granularity.
- **No authority.** A log, a trace, or a metric is never the source of truth for a consequential fact; the ledger is. Losing observability data loses diagnostic detail, never a fact.
- **Backpressure is diagnostic.** If diagnostic delivery cannot keep up, the system degrades or drops diagnostic data with `EventBufferOverflow`; it never blocks the observed operation to preserve diagnostic detail.

## 18. Explicit Rejections

Anchor: `observability.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel telemetry store, a metrics time-series store of record, a separate tracing backend, or a second log of consequential facts beside the ledger — logs are `DebugLog` events plus a bounded device-local stream, traces and metrics are projections over the one ledger and event stream, and the ledger is the one source of truth
- a metric, trace, or log treated as the source of truth for a consequential fact — observability data carries no authority; the ledger holds consequential facts and observability projects them
- a diagnostic-stream-derived metric treated as authoritative — disposable diagnostic logs may feed `DiagnosticOnly` projections, never gates, quality figures, cost/billing figures, policy decisions, evaluation scores, or user-facing source-of-truth summaries
- a metric projected over a `coalescible` or `sampled_diagnostic` source presented as exact about underlying raw activity, or used as an authoritative gating, quality, cost, billing, policy, or evaluation figure
- an unkeyed model-dependent scalar in any metric — token counts, costs, and cache statistics are keyed by `(provider_id, model_id, tokenizer_id)` (`core.explicit-rejections`, File 01 §8); recomputing a cost or a token count instead of reading File 17's record
- high-cardinality, content-bearing, untrusted, or secret values used as default metric labels — such values are exemplars/correlation references or forbidden raw values, not aggregate dimensions
- a one-to-five or zero-to-one continuous quality score for a single output surfaced as a metric — per-item verdicts are File 39 `Validation` outcomes; continuous quality figures are aggregates of binary outcomes (`qc.judge-discipline`, File 39 §6.2)
- raw `Secret` material in a log, a trace payload, a metric label, a projection, a debug panel, a diagnostic bundle, or a telemetry egress — redaction runs before write and before egress (`secret.backend-boundary`, File 22 §4); `Secret` is a forbidden destination
- unkeyed content hashes used as an anonymization mechanism for stable identifiers — privacy pseudonyms are keyed and scoped; content-addressed hashes are for integrity and deduplication
- treating `DiagnosticBundle` as a `PortablePackage` profile, recovery archive, import substrate, or round-trip artifact — it is a governed diagnostic export with manifest/integrity/redaction records and no round-trip guarantee
- any observability data leaving the device by default, a built-in dependency on a hosted telemetry or analytics service, or an egress without explicit per-category, per-device user consent — local-first and zero-egress is the default, every egress is opt-in, redacted, sensitivity-gated, device-local by default, and user-only
- an agent, lease, profile, or automation granting telemetry consent or enabling an egress — telemetry consent and egress are user-only and policy-gated, like credential and secret egress
- time-based polling as an observability correctness mechanism — observation is event-first; the host-resource gauge sampling is the one flagged, configurable exception for a source with no change event; a scheduled health ping is rejected (`provider.provider-health` File 17 §12.4)
- silent loss or silent capping of observability data — buffer overflow reports its dropped count, retention is recorded policy with dry-run and accounting, and nothing disappears without a recorded transition
- ring-buffer search indexing raw hidden event content — live debug search operates only over redacted, currently visible fields
- File 41 inferring stale liveness from missing heartbeats or owning liveness timeouts, cooldowns, restarts, or remediation — the owning runtime or subsystem classifies liveness and emits typed facts; File 41 projects them
- a span with no terminating event silently rendered `Ok`, dropped, or included in a complete-looking trace — incomplete spans and partial traces are explicit
- cross-clock-domain wall-clock deltas presented as exact span duration, or wall-clock ordering used as canonical trace ordering — sequence is canonical, and cross-clock durations are approximate
- disabling, weakening, or rerouting the hash-chained audit overlay through the observability layer — audit is never disabled when telemetry is disabled, is never synced, and is surfaced read-only here; observability owns none of it
- observability that blocks, gates, throttles, kills, or remediates the operation it observes — observability is observe-only; remediation is the run model's and File 42's
- a per-surface or per-subsystem private telemetry store, metrics database, or trace backend — surface affordances are presentations of the one Observatory service; custom instruments register through the one instrumentation-declaration path
- a new top-level `AppEvent` or `LedgerEntryKind` for observability, or a parallel observability bus — observability consumes the closed catalogue and registers `Custom { namespace: "observability" }` extensions on the one bus
- a hardcoded log level, rotation size, buffer cap, sampling interval, flush cadence, or retention horizon — every one is a configurable setting with a canonical default; time-based retention is opt-in, not the hidden default shape
- a log message interpolating raw user content into its text instead of structured `fields`, or a user-surfaced observability string that is not a localizable key
- re-deriving a token count, a cost, a provider-health state, or any model-dependent value at replay or reconstruction time — replay reads the recorded record, re-querying no live endpoint
- projection-time random span identity — replay-stable span identity is recorded in `TraceContext` or deterministically derived from canonical source identities and operation boundaries

## 19. Consequences for Later Specs

Anchor: `observability.consequences-for-later-specs`

Every later spec that emits a fact, produces a metric source, needs a diagnostic view, or exposes a health signal consumes this layer as defined here. The canonical principles later specs follow:

- emit facts through the canonical ledger and bus (File 10); do not invent a parallel telemetry store, metrics database, or trace backend — observability projects what you already record
- never store an unkeyed model-dependent scalar; key every model-dependent metric by model or provider identity
- declare every custom metric's source, dimensions, cardinality classes, accuracy class, authority class, replay behavior, sensitivity, retention/default visibility, and owner; do not use coalesced, sampled, or disposable diagnostic sources as authoritative gates
- surface no continuous quality score for a single item; per-item verdicts are File 39 outcomes and continuous figures are aggregates
- honor the secret boundary and egress governance for every log, trace, metric, and export; raw `Secret` never reaches an observability path, and every egress is opt-in, redacted, sensitivity-gated, and user-only
- register custom metrics, spans, and log categories through the one instrumentation-declaration path under source approval; introduce no parallel instrumentation registry

Specific integration contracts:

- the **Runtime Infrastructure and Lifecycle** spec (File 42) owns process lifecycle, background-worker scheduling, queues, supervision, liveness-state classification, and operational remediation; it emits the worker, queue, and lifecycle facts this file surfaces as health projections, and it owns the operation while this file owns the observation. The observe-not-operate boundary (§11.2) is fixed: this file remediates nothing and infers no stale liveness state.
- the **Packaging, Platform, and Distribution** spec (File 43) owns the platform crash-handler registration, the crash-reporter bundling, the update-channel telemetry distribution, and the release-channel analytics; the platform crash handler feeds the redaction and consent boundary this file defines, and the in-app `DiagnosticBundle` and `TelemetryConsent` remain this file's.
- the **per-surface specs** (Files 27–32) present observability under their own vocabulary (activity feeds, session logs, network logs, lineage views, health cards, cost panels) as presentations of the one Observatory service, register their custom instruments and log categories through the one path, and own no private telemetry store.
- the **storage and sync specs** (Files 20, 21) — already written — realize observability retention as recorded policy over the one garbage collector with dry-run and accounting, use size/count/storage-accounting bounds by default and time horizons only as explicit policy, keep trace and metric projections rebuildable, hold the diagnostic stream, ring buffer, active telemetry consent, and audit overlay device-local, and never sync raw secret or unredacted `Sensitive` observability content.
- the **UI specs** (Files 37, 38) — already written — render the Observatory and debug surfaces and the observability widgets from the data contracts this file defines, gate raw-payload inspection and export behind File 22 egress and File 06 policy, and present observability as management surfaces, never as work surfaces.
- the **quality-control and evaluation specs** (Files 39, 40) — already written — hand this file the live quality-metric projections (File 39) and share the ledger and validation results with the offline measurement layer (File 40), and this file computes the live metrics without a parallel quality or evaluation store.
- the **model-strategy, provider, automation, workflow, plugin, and MCP specs** (Files 16, 17, 33, 34, 35, 36) emit the usage, cost, health, rate-limit, automation-run, workflow-reliability, plugin-lifecycle, and connector-connection facts this file projects, and consume the metric and trace projections without re-owning them.

## 20. Canonical Rule Anchors

Anchor: `observability.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `observability.chosen-model`, `observability.boundaries-with-adjacent-layers`, `observability.observatory`, `observability.logging`, `observability.tracing`, `observability.metrics`, `observability.telemetry-egress`, `observability.debug-surface`, `observability.retention`, `observability.audit-boundary`, `observability.health`, `observability.surface-aliasing`, `observability.capability-surface`, `observability.events`, `observability.settings`, `observability.persistence-replay`, and `observability.operating-constraints`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
