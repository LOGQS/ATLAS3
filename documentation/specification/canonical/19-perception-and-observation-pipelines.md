# Perception and Observation Pipelines

## Status

Canonical.

## Scope

This file defines:

- `Perception` as the always-available substrate service that senses the parts of the operating environment the system does not already know through self-registration, and produces the structured observations and signals that the world model (`world.observation-state-update`, File 18 §8) and the `Observation` block layer (`artifact.observation`, File 09 §13) consume
- `Sensor` as the typed, registered capture source — the perception primitive — and the closed canonical `SensorKind` catalogue plus the registered-extension mechanism
- the tiered sensing strategy (`SensingTier`: `Structured`, `Grounded`, `Raw`) that every modality maps to, the structured-data-first invariant from `core.world-model` (File 01 §6.7), the merge-not-just-cascade rule, and the boundary between surface self-registration (`world.observation-state-update`, File 18 §8.1) and external/opaque-source capture
- the capture pipeline contract — `CaptureRequest`, `Capture`, `CaptureResult` — and the deterministic `acquire → process → normalize → structure → attribute → emit` stages, including producer normalization, change-detection/diff, and content-addressed deduplication
- the per-modality capture contracts (screen/window/display, desktop accessibility/automation tree, browser page DOM, audio with voice-activity and wake-word gating, file-system and repository state, process/system-metric/environment/network/liveness) and the processor contract for optical-character recognition, visual grounding, transcription, captioning, and equivalent analyzers
- the trigger model: capture-on-demand and capture-on-event as canonical, capture-on-interval as a flagged configurable fallback for sources that emit no change events
- the output contract: the transient `PerceptionSignal` consumed by the world model and the bus, the deliberate `Observed`-tier capture committed as an `Observation` block, the staleness-fingerprint computation, and the stagnation/no-effect signal
- capture privacy, consent, and safety: permission state and operating-system permission flows, the consent gate, sensitive-source detection and redaction, secret/PII redaction before commit, capture-scope bounding, sensitivity classification, recording transparency, and the capture-ethics rules
- capture cost and fidelity management: compression, resolution presets, lazy/gated analysis, capture caching as a flagged fallback, coordinate-space and scale-factor fidelity
- robustness: graceful tier degradation, capture failure classes, dead-sensor circuit-breaking, and re-observation
- the `perception.*` capability surface, the perception event vocabulary, the persistence contract, the settings dimensions, the explicit rejections, and the consequences for later specs

This file does not define:

- the world-state model, the entity/surface-state schema, the durability-tier semantics, the observation-to-state update (projector) contract, the availability evaluator, or snapshot resolution — `world.chosen-model` (File 18) owns those; this file produces the observations and signals `world.observation-state-update` (File 18 §8) consumes and must not define a parallel state model
- the `Observation`, `Citation`, `Evidence`, `Block`, or `BlockEdge` schema — Files 08 and 09 own those; this file commits `Observation` blocks (`artifact.observation`, File 09 §13) conforming to that contract and computes their staleness fingerprints
- the execution ledger row format, the event envelope, hook dispatch, or which events become durable ledger entries — File 10 owns those; this file specifies the perception events that flow through the canonical bus
- the version graph, materialized view, or `world_snapshot_id` resolution — Files 11 and 18 own those
- the `CapabilityDeclaration` field set, the registry, policy evaluation, approval flows, or leases — Files 05 and 06 own those; this file declares the `perception.*` capabilities as canonical built-ins and specifies which are tier-gated and how capture consent is requested
- tool-surface composition — File 07 owns it
- model selection and provider integration — Files 16 and 17 own those; a grounding, optical-character-recognition, or transcription backend that routes to a model declares its workload and consumes a selected model/provider; provider health and rate limits are File 17's and are referenced, never re-derived
- retrieval, indexing, or knowledge-base curation — File 12 owns those; observations are indexed through File 12's `observation:<scope_id>` namespace, not re-owned here
- context-assembly, compaction, token budgets, or trajectory-image retention in the model request — File 13 owns those; this file produces compact, deduplicated captures that File 13 assembles and retains
- action execution — clicking, typing, navigating, mutating files — is not perception; the per-surface action executors own it; this file owns only sensing and observation
- credential storage, the secret vault, trust state, or sandbox/process isolation — File 22 and File 23 own those; this file carries sensitivity tags and references, never secret payloads, and references active sandboxes/devices without owning their isolation
- workspace identity and materialization, storage layout, sync transport, or UI rendering — File 24, File 20, File 21, File 37, and File 38 own those
- the per-surface runtimes themselves (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) — those specs declare their specific sensors and consume this substrate; this file declares the cross-cutting baseline

## Source Resolution

This file resolves screen-capture, accessibility/automation-tree, optical-character-recognition, visual-grounding, browser-DOM, audio/voice, file-system-watching, system/process/environment-observation, perception-pipeline-architecture, capture-privacy, and observation-output material into one boundary: the sensor layer that turns externally mutable or non-self-registering sources into structured observations and signals.

Resolved design:

- Perception is one substrate service of typed `Sensor`s and registered `PerceptionProcessor`s. It is the sensor sibling of the world model (`core.world-model`, File 01 §6.7): the world model holds the live structured state; perception is how externally mutable, opaque, or non-self-registering source state enters that model.
- Perception is structured-data-first, not structured-only. Every modality maps to the same tier order — `Structured` (the source's own machine-readable structure) before `Grounded` (structure inferred from pixels or audio by a processor) before `Raw` (the captured medium itself). Raw capture is never the foundation, but it is valid when the declared capture need requires visual evidence, human review, multimodal model input, coordinate grounding, replay evidence, or when lower tiers are unavailable or insufficient.
- Capture is event-first. Observation is driven by change events from the source; time-based polling and staleness windows are explicitly flagged, configurable fallbacks for sources that emit no change events, never correctness conditions.
- Perception produces, the canonical block path commits, and the world model projects. Perception emits typed signals and creates deliberate observation-commit requests; committed `Observation` blocks are created through the canonical block/capability path and then consumed by the world model (`world.durability-tiers`, File 18 §7; `world.observation-state-update`, File 18 §8). Perception never owns a parallel state model.
- Capture privacy is first-class. Permission, consent, sensitive-source redaction, secret masking, and scope bounding are part of the capture contract, not an afterthought.
- Perception is read-only with respect to the world. It senses; it never acts. Action is a separate, per-surface concern.

Resolved tensions:

- "screen-capture infrastructure" (the specbase `ScreenCaptureService` in the infrastructure layer) versus "perception pipeline" (the GUI Control source material's three-tier element-detection pipeline): unified — there is one `Perception` substrate with a `Sensor` model, a processor model, and a tier strategy; the screen-capture service is the screen sensor, grounding is a registered processor over a capture, and the GUI three-tier pipeline is one instantiation of the canonical tier model. The per-surface specs instantiate; this file defines the shared substrate.
- "structured state exposure is stronger than screenshot self-perception" (the first-party invariant and the strategic review) versus the pervasive screenshot-first patterns in external capture systems: resolved by the tiered sensing strategy — structured is the foundation, grounded is the bridge, raw is deliberate evidence or fallback, and raw media is exposed only when the capture need requires it or lower tiers are insufficient.
- "never use time-based conditions or polling" (project constraint, `core.event-first-by-default`, File 01 §7.15) versus the pervasive polling/TTL patterns in source systems (periodic screenshots, git-status polling, screen-capture TTL caches, metric watch intervals): resolved exactly as `world.observation-state-update` (File 18 §8.6) resolves it — event-driven capture is canonical; every polling or staleness-TTL pattern surfaced in the sources is treated as a flagged, configurable fallback for sources without change events, never a default mechanism and never a correctness condition.
- "every producer self-registers; there is no central observer that scrapes a rendered view" (`world.observation-state-update`, File 18 §8.1) versus the need to observe applications, pages, files, audio, and the system: resolved by source-of-truth boundary — Atlas-owned surfaces self-register their structured state to the world model (`world.observation-state-update`, File 18 §8.1) and are never screen-scraped to learn Atlas state; perception captures externally mutable or non-self-registering sources such as other applications, the open web, workspace files, repositories, terminals, processes, audio devices, OS windows, and system state.
- "maintain a durable replay substrate" versus "high-frequency surface churn must stay transient": resolved by deferring durability to `world.durability-tiers` (File 18 §7) — perception emits both transient signals and deliberate `Observation` captures, and the world model classifies each into the `Ephemeral` / `Durable` / `Observed` tiers.

## 1. Chosen Model

Anchor: `perception.chosen-model`

ATLAS3 has one `Perception` substrate service.

`Perception` is the substrate service that senses the operating environment and produces structured observations and signals. It is always available to every work surface and control rail (`core.substrate-services`, File 01 §2.4) and is the sensor sibling of the world model: where the world model (`world.chosen-model`, File 18) holds the live structured state, perception is the mechanism by which externally mutable, opaque, or non-self-registering source state is captured and turned into the observations and signals the world model consumes through `world.observation-state-update` (File 18 §8).

Perception is composed of:

- `Sensor` records (§4): the typed, registered capture sources — screen, accessibility/automation tree, browser page, audio, file system, repository, process, system metrics, environment, network, and liveness — each declaring its modality, capabilities, supported tiers, privacy class, change-event sources, and the observation kinds it produces.
- `PerceptionProcessor` records (§4.5): registered analyzers over captures — optical-character recognition, visual grounding, transcription, captioning, and equivalent processors — each declaring its input kinds, output contract, backend identity, model/provider requirements where applicable, and replay keying.
- the tiered sensing strategy (§5): the closed `SensingTier` order (`Structured` → `Grounded` → `Raw`) every sensor maps to, with the structured-data-first invariant and the merge-not-just-cascade rule.
- the capture pipeline (§6): the deterministic stages that turn a `CaptureRequest` into a normalized, attributed, structured `Capture`, and the rules for debouncing, change-detection, and deduplication.
- the output contract (§9): the transient `PerceptionSignal` and the deliberate `Observation` capture, aligned with the world model's durability tiers.
- the capture-privacy layer (§10): permission, consent, sensitive-source redaction, secret masking, scope bounding, and recording transparency.

`Perception` elaborates the future-Perception delegation named throughout `world.consequences-for-later-specs` (File 18 §17) and the boundary in `world.observation-state-update` (File 18 §8.4) into a full sensor, capture, output, and privacy contract. It honors `core.product-thesis` (File 01 §1)'s commitment to "a live structured model of the current environment … so that capabilities can reason about the world, not just about conversation history" by owning the mechanics that feed that model.

`Perception` and `Sensor` supersede earlier vocabulary that named the same primitives: screen-capture service, screen share, perception pipeline, element detection, grounding backend, world-feed, observer, watchdog, and capture service. Those names may persist as informal or specialized synonyms; the canonical layer is `Perception`, its typed unit is `Sensor`, and its outputs are the `PerceptionSignal` and the `Observation` block. The runtime component that maintains and runs sensors is the Perception service.

### 1.1 Boundary

Perception defines how externally mutable or non-self-registering sources are sensed and how that sensing becomes structured output. It does not define what the resulting state means (File 18), what content the output is carried by (Files 08, 09), how the output is recorded or replayed (Files 10, 11), how it is acted upon (the per-surface action executors), or how it is stored on disk (File 20).

## 2. Boundaries with Adjacent Layers

Anchor: `perception.boundaries-with-adjacent-layers`

### 2.1 With File 01 (Core Thesis)

`core.world-model` (File 01 §6.7) declares that screenshot-driven self-perception is fallback, not foundation; §5 of this file makes that the tiered sensing strategy. Perception honors `core.non-destructive-by-default` (File 01 §7.13) (capture is read-only with respect to the world; it never mutates the source), `core.canonical-hash` (File 01 §7.14) and `core.canonical-encoding` (File 01 §6.15) (every capture hash and fingerprint is computed over a declared encoding, §6.4), `core.explicit-rejections` (File 01 §8) (model-derived capture results — grounding, optical-character-recognition, transcription — are keyed by model identity and never stored as unkeyed scalars, §9.4), and the `core.event-first-by-default` (File 01 §7.15) constraint forbidding time-based behavior (§8).

### 2.2 With File 18 (World Model and State Awareness)

The boundary is sharp and load-bearing. File 18 owns the world-state model, the entity and surface-state schema, the durability tiers (`world.durability-tiers`, File 18 §7), the observation-to-state update (projector) contract (`world.observation-state-update`, File 18 §8.2), the availability evaluator (`world.state-aware-capability-availability`, File 18 §9), and snapshot resolution (`world.world-snapshot-replay`, File 18 §10). This file owns the capture mechanics. Perception produces structured observations and typed `PerceptionSignal`s; `world.observation-state-update` (File 18 §8.2) applies them to the world model. `world.observation-state-update` (File 18 §8.4) states the contract: "perception produces structured observations and signals; the world model is the live projection those observations maintain." `world.observation-state-update` (File 18 §8.1)'s self-registration is for Atlas's own surfaces and is not perception; this file captures externally mutable or non-self-registering sources (§5.4). `world.environment-temporal-connection-facts` (File 18 §6.4) explicitly delegates the capture of environment, temporal, connection, and liveness facts to this file. The world facts perception emits never decide their own durability tier — `world.durability-tiers` (File 18 §7) classifies them.

### 2.3 With File 09 (Artifacts, Claims, Evidence, and Provenance) and File 08 (Blocks)

`artifact.observation` (File 09 §13) defines the `Observation` block kind, the closed `ObservationKind` catalogue, and the `StalenessFingerprint` typed value. This file produces capture results and deliberate observation-commit requests; committed `Observation` blocks conforming to File 09 are created through the canonical block/capability path, with the staleness-fingerprint value computed at capture time (§9.3). The `observes` relation (`world.world-entity`, File 18 §4.4) links the observation to the entity it describes; the `witnesses` edge (`block.canonical-edge-kinds`, File 08 §5.2) links it to the work that depended on it. Large capture payloads use `External` block content (`block.block-content`, File 08 §4); the content hash follows `block.content-hash` (File 08 §4.5) computed over the canonical media encoding (§6.4). This file never invents a block kind or an observation kind outside File 09's catalogue and its registered extensions.

### 2.4 With File 10 (Execution Ledger, Event Stream, and Hooks)

Perception emits events on the canonical bus (`ledger.event-envelope`, File 10 §5.2). Perception-specific lifecycle, permission, consent, degradation, and stagnation events register as `Custom { namespace: "perception", name, payload }` (`ledger.custom-kind-registration`, File 10 §4.3). Deliberate observation commits are recorded through the canonical observation/block/ledger path; any perception-owned notification about that commit is a custom event linked to the committed block. `EnvironmentSnapshotCaptured` records a durable environment capture where File 10 declares it. `Secret`-class capture payloads never persist to the durable ledger (`ledger.sensitivity-aware-persistence-retention`, File 10 §10). Replay and audit consume recorded observations through `ledger.replay-semantics` (File 10 §11); they never re-capture live sensors (§9.5).

### 2.5 With File 04 (Execution and Run Model)

A capability whose mutation depends on a prior observation revalidates currency before mutating and returns the typed `StateChangedSinceObservation` error on mismatch (`run.call-pipeline`, File 04 §8.2); this file owns the staleness-fingerprint computation that revalidation checks (§9.3). Streaming captures follow `run.streaming-partial-execution` (File 04 §12). Capture subscriptions are cancellable resources killed when their owning run, child run, session, or sandbox is killed (`run.cancellation`, File 04 §17.3, killability per `core.invariants`, File 01 §7.11). Concurrent captures across sessions follow `run.parallelism` (File 04 §15); there is no single-active-capture assumption.

### 2.6 With Files 05, 06, 07 (Capability Contracts, Policy, Tool Surfaces)

Every perception operation is a `Capability` declared per `capability.declaration` (File 05 §3) and registered with the `Builtin` source (§14). Capture consent and the tier-gating of sensitive captures flow through the policy layer (File 06): a capture that touches a sensitive source escalates its tier, and the capture-consent request (§10.2) is a policy-gated approval. Sensors register through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2) with the source-trust envelope of `capability.capability-source` (File 05 §9.1). Perception capabilities surface uniformly through tool-surface composition (`surface.visibility-composition-resolution-algorithm`, File 07 §9), and a sensor's availability is expressed through the declared `availability_predicate` (`capability.availability-predicate`, File 05 §15.2) evaluated by the world model (`world.state-aware-capability-availability`, File 18 §9) — for example, a screen sensor whose capture permission is `Denied` is not in the available set.

### 2.7 With Files 16 and 17 (Model Strategy, Provider Layer)

A model-mediated perception processor — a cloud vision grounder, optical-character-recognition service, transcription provider, captioner, or equivalent analyzer — declares its perception workload and consumes a model selected through File 16 and executed through File 17; a local bundled processor does not. Processor-derived results are keyed by full invocation identity and recorded for replay (§9.4, `provider.token-source`, File 17). Provider health and rate-limit state are File 17's and are referenced as connection liveness (`world.environment-temporal-connection-facts`, File 18 §6.3), never re-derived here. Transcription and other audio-capable provider contracts are the provider layer's; this file owns the audio capture and gating that feed them (§7.5).

### 2.8 With File 12 (Retrieval) and File 13 (Context Assembly)

Observations are indexed through File 12's `observation:<scope_id>` namespace; this file does not own retrieval. Context assembly renders captures into the model request: a structured observation enters as a `trusted_runtime_fact` (`context.authority-classes`, File 13 §2.3) in the `RuntimeState` region (`context.semantic-regions`, File 13 §3), and a raw image capture enters as a multimodal part when a vision model consumes it. Trajectory-image retention in the model request — which captures to keep, which to drop under budget — is File 13's; this file produces compact, deduplicated, content-addressed captures and the diff data File 13 uses (§11).

### 2.9 With Workspaces (File 24), Security (File 22), Sandbox (File 23), and the per-surface specs

The Workspaces and Materialization spec owns workspace identity; perception captures workspace files and repository state without owning materialization. The Security spec owns the credential vault and trust state; perception carries sensitivity tags and references, never secret payloads, and applies redaction before commit (§10). The Sandbox spec owns process and sandbox isolation; perception captures process and system state and references active sandboxes/devices without owning their isolation. The per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) declare their specific sensors and named availability checks and consume this substrate; the GUI Control surface's desktop perception, the Web surface's browser perception, and the System Agent surface's system observation are instantiations of the sensor kinds, processor model, and tier strategy defined here.

### 2.10 Boundary

This file is the sensor and capture layer. It owns sensors, the tier strategy, the capture pipeline, the output contract, the capture-privacy layer, the perception event and capability surfaces, and the settings dimensions. It does not own world state, block or observation schemas, the ledger or event envelope, snapshot resolution, model or provider selection, retrieval, context assembly, action execution, storage layout, or credential and isolation primitives. It feeds those layers; it does not replace them.

## 3. `Perception` Service

Anchor: `perception.perception-service`

### 3.1 Definition

The `Perception` service is the runtime component that registers sensors, performs captures, runs the capture pipeline, applies the capture-privacy layer, and emits perception output. It is a substrate service per `core.substrate-services` (File 01 §2.4): always available, cross-cutting, and shared by every surface and control rail rather than shaped as a workspace-first surface.

### 3.2 Purpose

The service exists so that externally mutable or non-self-registering state — other applications, the open web, workspace files, repositories, terminals, processes, audio devices, OS windows, and system state — can enter the world model and the agent's context as structured, attributed, privacy-respecting observations, rather than as ad-hoc per-surface scraping. It is the one place capture mechanics, the tier strategy, and capture privacy are defined, so that adding a new sensor or processor is a registration, not a rewrite (`core.local-extensibility`, File 01 §7.8).

### 3.3 What Perception Is Not

The `Perception` service is not:

- a world-state model — it produces observations; the world model (File 18) holds and projects state
- a block pool, a transcript, or a memory — it references and commits blocks by identity and never stores learned durable knowledge (memory is File 14)
- an action executor — it senses; clicking, typing, navigating, and mutating are the per-surface action executors' concern
- a central scraper of Atlas's own rendered UI — Atlas's surfaces self-register their state to the world model (`world.observation-state-update`, File 18 §8.1); perception captures externally mutable or non-self-registering sources
- a model or provider layer — it consumes models and providers for grounded-tier backends; it does not select or integrate them (Files 16, 17)
- a durable source of truth — captures are reconstructable records, never the sole authority for any durable fact

### 3.4 Boundary

The service defines how sensing is organized and run. It does not define the meaning of the sensed state, the schema of the output, or the on-disk form of recorded captures.

## 4. `Sensor` and the `SensorKind` Catalogue

Anchor: `perception.sensor`

### 4.1 Definition

A `Sensor` is the typed, registered capture source: one identifiable way of sensing one modality of the environment, with declared capabilities, supported tiers, a privacy class, change-event sources, and the observation kinds it produces. A `Sensor` is the logical capture source; the physical hardware it may use (a camera, a microphone, a capture card) is a `Device` world entity (`world.world-entity`, File 18 §4.3). One sensor may use zero or more devices.

### 4.2 Required Fields

Every `Sensor` declares at minimum:

- `sensor_id` — stable identifier for the lifetime of the registration
- `kind` — the `SensorKind` (§4.3), fixed for the sensor's lifetime
- `modality` — the broad sense category: `Visual`, `UiStructure`, `Audio`, `Filesystem`, `System`, or `Network`
- `supported_tiers` — the `SensingTier`s (§5) this sensor can operate at, in preference order for each declared capture need
- `produces_observation_kinds` — the `ObservationKind`s (`artifact.observation`, File 09 §13.2) a deliberate capture from this sensor commits
- `change_event_sources` — the kinds of change signals that drive event-first capture for this sensor (operating-system UI event stream, file-system change notification, browser protocol event, connection lifecycle signal, voice-activity onset), or the typed `NoChangeEvents` marker that makes this sensor eligible for the polling fallback (§8.2)
- `privacy_class` — the default capture sensitivity (`Public` | `Sensitive` | `Secret`, `block.sensitivity`, File 08 §9) and the permission the sensor requires (§10)
- `capabilities` — typed capability descriptor: whether the sensor produces structure, pixels, audio, or text; whether it supports region/scoped capture; whether it supports streaming; and the freshness model it supports
- `scope` — the broadest scope at which the sensor is addressable (`run` | `intent_thread` | `task` | `conversation` | `workspace` | `global`), aligning with `world.world-entity` (File 18 §4.2)
- `owner_subsystem` — the registered subsystem, surface, or producer that owns the sensor
- `coordinate_space` — for visual sensors, the declared coordinate space and scale-factor model of its captures (§6.5); null otherwise
- `processor_refs` — processors allowed to analyze this sensor's captures when the capture plan requires derived structure

Model-dependent capabilities (a grounding backend's coordinate space, a tokenizer for transcription cost) are keyed by model or backend identity, never stored as unkeyed scalars (`core.explicit-rejections`, File 01 §8).

### 4.3 Closed Canonical `SensorKind` Catalogue

Every sensor declares its `kind`. The canonical closed catalogue, grouped by modality:

**Visual capture:**

- `Screen` — captures a display, window, or region as pixels; declares per-display geometry and scale factors (§6.5); produces `Screenshot` observations
- `Camera` — captures from a physical or virtual camera device; produces `Custom { namespace: "perception", name: "ImageCapture" }` observations unless File 09 adds a canonical image-observation kind

**UI structure:**

- `DesktopAccessibilityTree` — traverses the operating system's accessibility/automation interface to capture the structured element tree of a desktop application (role, name, bounds, state, available interaction patterns); produces `AccessibilityTreeSnapshot` observations
- `BrowserPage` — captures a web page's structured state through the browser's automation/debugging interface: the accessibility tree, the document structure, viewport metadata, console output, and network responses; produces `BrowserDom` and `NetworkResponseSnapshot` observations

**Audio:**

- `Audio` — captures microphone or system-loopback audio, gates it with voice-activity detection and explicitly enabled wake-word detection, buffers and chunks it, and hands chunks to a transcription processor; produces `Custom { namespace: "perception", name: "AudioCapture" }` observations, and may produce transcript evidence through the processor path (§7.5)

**Filesystem:**

- `FileSystem` — observes file and directory changes through the operating system's change-notification interface and captures file content snapshots; produces `FileSnapshot` and `WorkspaceSnapshot` observations
- `Repository` — captures version-control state (branch, commit, working-tree status, diffs); produces `RepositoryState` observations

**System:**

- `Process` — captures running-process state (command, identifier, status, resource use); produces `ProcessState` observations
- `SystemMetric` — captures system metrics (processor, memory, disk, network throughput, battery, thermal) and idle state; produces `ProcessState`/`Custom` observations
- `Environment` — captures operating-environment facts (operating system and platform, shell, working directory, display geometry, locale and timezone, network connectivity posture, sandbox writable roots, foreground application, and the relevant permission states); produces `EnvironmentSnapshot` observations consumed by `world.environment-temporal-connection-facts` (File 18 §6)
- `Terminal` — captures terminal/shell session output and command boundaries; produces `TerminalOutput` observations

**Network and connection:**

- `Network` — captures network requests and responses for replayable automation; produces `NetworkResponseSnapshot` observations
- `Liveness` — observes the connection/liveness lifecycle of integrations, sidecars, sessions, and devices through their lifecycle signals; produces liveness signals consumed by `world.environment-temporal-connection-facts` (File 18 §6.3) (provider health is File 17's and is referenced, not re-derived)

**Extension:**

- `Custom { namespace, name }` — a subsystem-, surface-, plugin-, or extension-specific sensor kind registered through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2). The `namespace` matches the capability sourcing taxonomy (`capability.capability-source`, File 05 §9.1). The registration declares the kind's modality, supported tiers, produced observation kinds, change-event sources, privacy class, and allowed processors. A surface-specific sensor — for example, a Coder-surface debugger or execution-trace sensor — registers here rather than expanding the closed catalogue.

The closed catalogue is canonical for cross-cutting reasoning; the `Custom` extension is canonical for specialization. Adding a canonical kind is a canonical-spec change; runtime extension uses `Custom`.

### 4.4 Sensor Registration

A sensor registers through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2) and persists in the registry under the source-trust envelope (`capability.registered-capability`, File 05 §10, `policy.source-approval-flow`, File 06 §9). Registration declares all of §4.2. Registration is the cheap-to-add extensibility path (`core.extension-planes`, File 01 §6.14): a new surface or plugin contributes a sensor by registering, not by editing the Perception service.

### 4.5 `PerceptionProcessor`

A `PerceptionProcessor` is a registered analyzer over one or more captures. It is not a source and does not acquire data by itself. Processors include `Ocr`, `VisualGrounding`, `Transcription`, `Captioning`, document parsing, and `Custom { namespace, name }` analyzers.

Every processor declares its accepted input observation kinds, output contract, confidence or uncertainty shape where applicable, privacy effects, backend binding, workload classification for File 16 when model-mediated, and replay class. Processor output metadata includes `input_capture_hash`, `processor_id`, `processor_version`, `backend_binding_id`, `model_id` where applicable, `provider_id` where applicable, `model_request_template_id` where applicable, and the decoding, normalization, and prompt-profile identifiers that affect output. Re-processing the same capture with a different processor invocation creates a new derived output linked by provenance, not an in-place replacement.

### 4.6 Boundary

The sensor and processor model defines what the system can sense and how captures can be analyzed. It does not define the operating-system or browser interfaces the sensors use, the concrete processor implementations, how captures are stored, or how the sensed state is interpreted.

## 5. The Tiered Sensing Strategy

Anchor: `perception.tiered-sensing`

### 5.1 `SensingTier` and `CaptureNeed`

Every capture operates at one or more of three closed canonical tiers. Selection is driven by the declared `CaptureNeed`: `StateUpdate`, `MutationPrecondition`, `VisualEvidence`, `HumanReview`, `MultimodalModelInput`, `CoordinateGrounding`, `ReplayRecord`, or `Custom { namespace, name }`.

- `Structured` — the source exposes its own machine-readable structure, captured directly: the accessibility/automation tree of a desktop application, the document and accessibility tree of a web page, file content and its hash, repository status, process and metric tables, environment facts, and network responses. The structured tier is deterministic, precise, semantically rich, cheap, and the default state source.
- `Grounded` — the source's structure is inferred from a captured medium by a processor: visual grounding and optical-character recognition over a screenshot, element detection over pixels, or transcription over audio. The grounded tier is used when the structured tier is absent or insufficient (a canvas-rendered application, a poorly-accessible app, an image-only document, spoken input). It is more expensive and less precise than structured and is keyed by the processor invocation that produced it (§9.4).
- `Raw` — the captured medium itself — screenshot pixels, camera frames, or audio waveform — handed to a downstream consumer without inferred structure. Raw is used only when required by the capture need, when lower tiers cannot satisfy the need, or as deliberate evidence alongside structured output.

### 5.2 The Structured-Data-First Invariant

Perception is structured-first, not structured-only. A structured accessibility tree, document tree, file snapshot, repository status, or system table is the default state source (`core.world-model`, File 01 §6.7). Grounded and raw captures are included only when requested by the capture plan, required by the consumer contract, needed for validation or replay evidence, needed for human or multimodal review, needed for coordinate grounding, or needed because structured capture is unavailable or insufficient.

This invariant is the cost and reliability rationale for the whole strategy: structured captures are cheaper, more reliable, and more semantic than pixel or waveform interpretation. It does not forbid deliberate raw evidence when the work requires it.

### 5.3 Merge, Not Just Cascade

The tiers merge as well as cascade. When both structured and grounded captures are available for the same source, perception fuses them deterministically given the inputs.

Structured capture takes precedence by default for semantic and actionability attributes: role, name, state, and interaction patterns. For geometry and visual attributes — bounds, coordinates, and visual appearance — the producing sensor's declared per-modality authority rule determines precedence. Grounded capture adds elements not present in the structured tier. Disagreements between tiers become typed conflict facts on the merged result, never silent resolution.

Per-surface specs define the modality-specific merge implementation: how to match structured elements to grounded regions, what counts as the same element across tiers, and which surface-specific conflict-resolution heuristics are valid. A sensor must not skip an available lower-cost tier when that tier can satisfy the declared capture need.

### 5.4 Self-Registration Versus Capture

Atlas's own surfaces report their structured state to the world model by self-registration (`world.observation-state-update`, File 18 §8.1); that is not perception and uses no sensor. Perception captures externally mutable or non-self-registering sources: other applications (including applications Atlas drives through GUI control), the open web, workspace files, repositories, terminals, processes, audio devices, OS windows, and system state. The boundary is source of truth: a self-reporting Atlas surface is never screen-scraped to learn Atlas state; an opaque or externally mutable source is sensed through the tiered strategy.

### 5.5 Boundary

The tier strategy defines the order and combination of capture approaches. The concrete operating-system, browser, model, and audio interfaces each tier uses are implementation and per-surface concerns; model selection for model-mediated processors is File 16's.

## 6. The Capture Pipeline

Anchor: `perception.capture-pipeline`

### 6.1 `CaptureRequest`, `Capture`, `CaptureResult`

A capture is initiated by a `CaptureRequest` carrying the target `sensor_id`, an optional scope or region, the requested tier(s), the declared `CaptureNeed`, a freshness directive, output mode (`SignalOnly`, `StagePayload`, `CommitObservation`, `ReplayEvidence`), and the requesting scope context. A `Capture` is the structured result: the produced observation or signal, its tier, its coordinate space where applicable, its sensitivity, its staleness fingerprint (§9.3), its canonical encoding identifiers (§6.4), its `capture_context` (§6.6), and a reference to any external payload. A `CaptureResult` wraps the `Capture` or a typed capture error (§12.2).

### 6.2 The Pipeline Stages

A capture proceeds through deterministic stages:

1. **Acquire** — the sensor captures the source: the structured tier reads the source's structure; the raw tier captures the medium; the grounded tier starts from a captured medium.
2. **Process** — registered processors turn captured payloads into derived structure where the capture plan requires it: optical-character recognition, visual grounding, document parsing, transcription, captioning, or diff against a prior capture.
3. **Normalize** — noisy and transient source signals are suppressed before any output (§6.3).
4. **Structure** — the result is shaped into the typed observation or signal, including coordinate normalization (§6.5).
5. **Attribute** — `capture_context`, source, sensitivity, and freshness evidence are attached (§6.6).
6. **Emit or commit** — a transient `PerceptionSignal` is broadcast to the world model and the bus, or a deliberate observation-commit request is sent through the canonical observation/block capability path (§9).

The stages are deterministic in the sense that matters for replay: a recorded `Observation` plus its fingerprint reconstructs the same observation, and a re-capture of an unchanged source produces the same content hash. The world itself is not deterministic; the record of a capture is immutable and replay-stable (§9.5).

### 6.3 Producer Normalization

Producers must normalize noisy source signals before emitting. Transient window-title changes from timers and counters, loading spinners, brief focus flickers during application switching, progress animations, and similar unstable artifacts must not produce output unless the producer's registered normalization policy classifies them as stable. Normalization includes same-source event coalescing, transient-pattern suppression, and stability gating. The normalization policy, suppression patterns, and stability rules are declared in the sensor's registration and configurable through settings (§17). This is the producer-normalization requirement `world.observation-state-update` (File 18 §8.3) places on every world-state producer, realized at the capture layer.

### 6.4 Change-Detection, Diff, and Deduplication

Perception captures and emits change, not churn:

- **Content-addressed deduplication** — a capture's payload is content-addressed; a re-capture whose content hash matches the prior capture is recognized as identical and is not re-emitted or re-committed. The hash is computed over a declared, versioned `CanonicalEncoding` (`core.canonical-hash`, File 01 §7.14): every capture records `capture_encoding_id` and `capture_encoding_version`; custom staleness fingerprints record `fingerprint_schema_version`; structured captures hash over the canonical form of their typed structure; opaque medium captures hash over their declared canonical media encoding, never raw container bytes. Physical storage of the payload is independent of the hash encoding (`block.content-hash`, File 08 §4.5). Each canonical capture encoding requires golden conformance fixtures so encoder revisions cannot silently change replay identity.
- **Diff-based re-capture** — when only part of a source changed, perception re-captures only the changed part (only the changed windows of a desktop tree, only the changed region of a page) and preserves the unchanged parts from the prior capture.
- **Delta emission** — where a consumer needs only what changed, perception emits the delta against a recorded baseline rather than the full capture.

### 6.5 Coordinate-Space and Fidelity

A visual capture records its coordinate space and fidelity so any consumer maps it correctly:

- the per-display geometry, resolution, scale factor, and orientation, and the multi-display arrangement, captured by the `Environment` sensor and attached to visual captures (a logical point on a high-density display is not a physical pixel; the conversion is declared, not assumed)
- the capture's own coordinate space (`ScreenPixels`, a normalized space, or a tile grid) where the capture or processor produces coordinates in a model-specific space
- the scale factors needed to map between the capture space and a consumer space

Perception owns recording the coordinate space and producing observation coordinates in a declared space. Mapping a model-produced coordinate back to a screen action is the per-surface action executor's concern, not perception's.

### 6.6 Capture Attribution

Every capture carries `capture_context`: the active scope context at capture (`run_id`, `step_id`, `node_id`, `worktree_id`, `backend_binding_id`, per `ledger.event-envelope`, File 10 §5.2), the `sensor_id`, the tier, the `CaptureNeed`, the `observation_subject` (the identity of what was observed — a window handle, a path, a url, a device id), processor invocation identity for derived captures (§9.4), and the capture time as provenance metadata (never as a behavior trigger, §8). Attribution is what makes a capture traceable to its source and replayable (`core.evidence-provenance`, File 01 §7.12).

### 6.7 Boundary

The pipeline defines how a capture is produced and shaped. It does not define the source interfaces, the processor implementations, the block content carriage, or the durability tier of the output.

## 7. Per-Modality Capture Contracts

Anchor: `perception.per-modality-contracts`

Each modality conforms to the tier strategy (§5) and the pipeline (§6). This section defines the cross-cutting contract per modality; the per-surface specs define their concrete sensors against it.

### 7.1 Screen and Display Capture

The `Screen` sensor captures a display, window, or region as pixels and records the coordinate space and per-display scale factors (§6.5). Window and display enumeration is part of the contract. Capture is on-demand or on-event by default; periodic capture is the flagged fallback (§8.2). Screen capture is the raw tier of visual sensing: it is used when the capture need requires pixels, visual evidence, coordinate grounding, or supplementary visual context, or when structured sources are unavailable or insufficient. Screen capture is permission-gated and privacy-classed (§10).

### 7.2 Desktop Accessibility/Automation Tree

The `DesktopAccessibilityTree` sensor captures the structured element tree of a desktop application through the operating system's accessibility/automation interface: element role, name, bounds, state, and available interaction patterns, captured with batched property retrieval to minimize cross-process round-trips. The contract requires modal-scope restriction (when a modal element is present, only its subtree is interactable and other elements are excluded), structured separation of embedded web content (handing it to the `BrowserPage` sensor where available), element-cache invalidation driven by operating-system UI events (§8.1), and diff-based re-traversal of only changed windows (§6.4). This is the structured tier of desktop sensing.

### 7.3 Browser Page

The `BrowserPage` sensor captures a web page's structured state through the browser's automation/debugging interface: the accessibility tree and document structure (the primary, structured representation), viewport metadata, console output, and network responses, with a screenshot only as the supplementary raw tier for vision consumers. The contract requires page-readiness and stability detection driven by browser protocol events rather than fixed delays (§8.1), reactive invalidation of the cached tree on document-change events, and capture of the page's identifying context (session, tab, frame, url, title). This is the structured tier of web sensing.

### 7.4 Optical-Character Recognition and Visual Grounding

Optical-character recognition and visual grounding are `PerceptionProcessor`s over image captures, not sensors. Optical-character recognition produces text plus bounding regions and per-region confidence; visual grounding produces interactable-element regions plus captions and confidence. A processor may be local or model-routed; model-routed processors declare their workload to File 16, execute through File 17, and record full processor invocation identity (§9.4). Grounded processor outputs merge with structured captures where their regions correspond (§5.3).

### 7.5 Audio

The `Audio` sensor captures microphone or system-loopback audio, gates it with voice-activity detection, may filter it with separately enabled wake-word detection, buffers and chunks it, and hands chunks to a transcription processor. Voice-activity detection and wake-word detection are local capture-side gates that determine when audio is forwarded; they are not transcription. Provider-routed transcription execution is a provider-layer contract (File 17); this file owns the capture, the gating, the buffering, and the capture-to-transcription handoff, and emits the transcription result as a processor-derived perception output (§9). Audio capture is permission-gated, device-aware (§7.9), and privacy-classed (§10). Audio output (synthesis, playback) is not perception and is out of scope.

### 7.6 File System and Repository

The `FileSystem` sensor observes file and directory changes through the operating system's change-notification interface (the event-first mechanism) and captures file content snapshots with content hashes for freshness (§9.3). Change events are normalized (§6.3); rename is tracked structurally where the platform supports it; ignore patterns bound the observed scope (§10.5). On startup or after an offline interval, a content-hash reconciliation re-establishes the current state before live watching resumes. The `Repository` sensor captures version-control state — branch, commit, working-tree status, diffs — preferring the structured tier (the version-control system's own status output) and observing change through file-system events where the platform does not push repository-change signals. Repository state is a structured capture; repository polling is a settings-controlled fallback only for sources declaring `NoChangeEvents` (§8.2).

### 7.7 Process and System

The `Process`, `SystemMetric`, and `Terminal` sensors capture system state structurally: running-process state, system metrics (processor, memory, disk, network, battery, thermal, idle), and terminal/shell output with command-boundary detection. Process and metric sources may expose no change-event interface; for those, a settings-controlled fallback cadence is permitted only when the sensor declares `NoChangeEvents` (§8.2), and the system remains correct if a fallback capture never runs. Terminal output is captured as a bounded rolling buffer with backpressure, streamed where the consumer subscribes.

### 7.8 Environment, Network, and Liveness

The `Environment` sensor captures operating-environment facts that ground the agent (§4.3) and feeds them to `world.environment-temporal-connection-facts` (File 18 §6); environment facts are observed, not assumed, and a change to display geometry, working directory, or a permission grant updates the corresponding fact. The `Network` sensor captures network requests and responses for replayable automation. The `Liveness` sensor observes the connection lifecycle of integrations, sidecars, sessions, and devices through their lifecycle signals; model-provider health and rate-limit state are File 17's and are referenced through `world.environment-temporal-connection-facts` (File 18 §6.3), not re-derived.

### 7.9 Devices and Streams

Capture devices — cameras, microphones, capture cards, screen-share targets — are enumerable, permission-gated, and referenced as `Device` world entities (`world.world-entity`, File 18 §4.3). A sensor may capture in a streaming mode (a continuous screen-share, camera, or audio stream) with backpressure: when a consumer cannot keep pace, the producer follows its declared sampling and coalescing policy rather than unbounded buffering. Stream lifecycle (start, pause, stop) is a cancellable capture subscription (§2.5).

### 7.10 Boundary

These contracts define what each modality captures and at which tier. They do not define the concrete platform interfaces, the per-surface tool catalogs, the action executors, or the model backends.

## 8. Triggers and the Event-First Model

Anchor: `perception.triggers`

### 8.1 Event-First Capture

Capture is event-driven by default. The canonical triggers are:

- **on-demand** — a consumer requests a fresh capture (a capability call, a re-observation request); the most common trigger for deliberate captures
- **on-event** — a change signal from the source drives re-capture: an operating-system UI event (focus, structure, window create/destroy), a file-system change notification, a browser protocol event (document changed, navigation completed, network response), a connection lifecycle signal, or a voice-activity onset

Event-first capture is the only mechanism that satisfies the project constraint against time-based conditions (`core.event-first-by-default`, File 01 §7.15). A sensor that has a change-event source must use it and must not poll.

### 8.2 The Polling Exception

Where a source emits no change events — certain system metrics, some repository states, external services without push — a settings-controlled fallback cadence or staleness-cache policy is permitted. Every such use is an explicitly flagged exception (the sensor declares `NoChangeEvents`, §4.2): it is configurable (§17), it surfaces its policy so the user can change it, and it is never a correctness condition — the system must remain correct if a fallback capture never runs. Perception prefers an event source whenever one exists and treats polling as a degraded mode for sources that lack one. Time-based capture caches are likewise flagged fallbacks, not defaults, and use source-lifecycle signals where the platform exposes them.

### 8.3 Time as a Fact, Not a Driver

Capture time is recorded as provenance metadata only (§6.6). Perception does not derive capture cadence, correctness, or scheduling from elapsed time except through the flagged polling fallback of §8.2. The current wall-clock time is a world fact the agent reads (`world.environment-temporal-connection-facts`, File 18 §6.2), not a behavior driver in this layer.

### 8.4 Boundary

This file owns the trigger model for capture. Scheduled and event automation that drives work (as opposed to capture) is File 33 (Automation and Triggers)'s; that spec consumes perception's change signals.

## 9. Output Contract

Anchor: `perception.output-contract`

### 9.1 The Two Output Forms

Perception produces two forms of output, aligned with the world model's durability tiers (`world.durability-tiers`, File 18 §7):

- a transient `PerceptionSignal` (§9.2): a typed signal broadcast to the world model and the canonical bus, consumed by `world.observation-state-update` (File 18 §8.2)'s projector. Most live perception output is a signal.
- a deliberate `Observation` capture (§9.3): a content-addressed, staleness-fingerprinted observation-commit request sent through the canonical observation/block capability path when a capture must be durable, evidentiary, or a mutation precondition.

Perception emits the output; deliberate observation commits pass through File 04 execution, File 05 declaration metadata, File 06 policy, File 08 block commit, File 09 observation contract, and File 10 ledger/event recording. The world model (`world.durability-tiers`, File 18 §7) classifies consumed facts into the `Ephemeral`, `Durable`, or `Observed` tier and projects them. Perception never owns the durable substrate.

### 9.2 `PerceptionSignal`

A `PerceptionSignal` is a typed transient signal carrying the affected source identity, the change kind, a compact structured payload (identifiers and short summaries, not resource bodies), the sensitivity, and the `capture_context`. Signals conform to the signal vocabulary `world.observation-state-update` (File 18 §8.2) consumes. A signal is a live coordination message: it is not, by itself, durably recorded (the world model decides, `world.durability-tiers`, File 18 §7). Where a detected change feeds an automation `Event` trigger (`automation.event-and-webhook-triggers`, File 33 §5.1), the change is COMMITTED as a durable observation-change event carrying the source identity, the change kind, and the diff/change identity (File 28 §12.2's detected-change-is-a-durable-fact is the exemplar) — the transient signal alone never fires an automation, because an automation fire needs the durable identity deduplication and `fire_id` derivation stand on.

### 9.3 The `Observed` Capture and the Staleness Fingerprint

A deliberate capture produces an observation-commit request for an `Observation` block (`artifact.observation`, File 09 §13) carrying the observation kind, the payload (inline for small payloads, `External` for large ones), the `capture_context`, the `observation_subject`, and a `StalenessFingerprint` (`artifact.observation`, File 09 §13.3). This file computes the fingerprint value at capture time: a content hash over the versioned canonical capture encoding (§6.4), a modification-time or version identifier for file captures, a canonical accessibility-tree hash, a canonical document signature, a cache-validator pair for network captures, or a composite of these. The runtime checks the fingerprint before any mutation that declared the observation as a precondition and returns `StateChangedSinceObservation` on mismatch (`run.call-pipeline`, File 04 §8.2). A capture whose mutation depends on it must carry a content-derived fingerprint — a content hash, a modification-time-and-hash pair, an accessibility-tree hash, a document signature, a git commit, a version identifier, a cache validator whose entity-tag is present, or a composite containing at least one of these; a bare modification-time or last-modified-only fingerprint, like the absence of a fingerprint, stays valid as evidence or a freshness hint but cannot back a mutation (`artifact.observation`, File 09 §13.3).

### 9.4 Model-Derived Results Are Keyed

A processor-derived result — an optical-character-recognition transcript, a visual-grounding element set, an audio transcription, or a caption — is a model- or backend-dependent value. It is recorded as a derived record keyed by the full processor invocation identity: input capture hash, processor id and version, backend binding id, model id where applicable, provider id where applicable, model request template id where applicable, and relevant decoding or normalization profile ids (`core.explicit-rejections`, File 01 §8, `provider.token-source`, File 17). Historical reconstruction reads the recorded keyed result; it never re-runs the processor against a live source (§9.5). Two processor results from different invocation identities are distinct records. A processor-derived output's committed sensitivity is at least the maximum sensitivity of its input captures; the derivation may raise sensitivity but never lower it. `perception.ocr`, `perception.transcribe`, and `perception.ground`, and the observation-commit of any derived output, apply this floor (§10.6).

### 9.5 Replay and Audit

Replay, audit, and reconstruction consume recorded observations, signals, and processor outputs; they never re-capture live sensors and never re-run processors against live sources (`ledger.replay-semantics`, File 10 §11). A recorded `Observed` capture replays deterministically through its content hash and staleness fingerprint. A committed processor output replays by reading the recorded derived output keyed by the original invocation identity. A live `PerceptionSignal` is `Ephemeral` and is reconstructable at replay only when the consuming assembly snapshot captured it or a durable reference covers it (`context.assembly-replay-snapshot`, File 13 §19); otherwise it resolves to the nearest durable checkpoint or a typed "unobserved at anchor" value (`world.world-snapshot-replay`, File 18 §10.3). This is the live-input-versus-replay determinism boundary: capture is non-deterministic at the source, but the record of a capture is immutable and replay-stable.

### 9.6 The Stagnation Signal

Perception fingerprints successive captures of the same source and emits a typed stagnation signal when consecutive captures of that source are identical (capture equality over the recorded fingerprints). The signal reports capture equality only; correlating it with an intervening action to conclude "no observed effect," and the response to that conclusion — pausing or correcting an agent loop — belong to `run.stuck-detection` (File 04 §20.3) and the per-surface specs, not to perception. Perception is fed no acted signal; it compares only recorded captures.

### 9.7 Boundary

This file owns the output forms, the fingerprint computation, and the keying and replay rules. File 09 owns the `Observation` block schema; File 18 owns durability classification and signal projection; File 10 owns the event envelope and ledger commit.

## 10. Capture Privacy, Consent, and Safety

Anchor: `perception.capture-privacy`

### 10.1 Permission State

A sensor that captures a permission-gated source carries a `PermissionState`: `Granted`, `Denied { reason }`, `NotYetRequested`, or `PermissionRequestInProgress`. Screen capture, accessibility-tree capture, audio capture, and camera capture require the corresponding operating-system permission. Permission acquisition is explicit: `perception.request_permission` starts the OS/platform permission flow, while ordinary capture returns `PermissionRequired { sensor_id, permission_kind, remediation }` when permission is missing unless the invocation explicitly requested permission acquisition. A sensor is unavailable for capture while permission is `Denied`, `NotYetRequested`, or `PermissionRequestInProgress`, except for permission-request operations themselves.

### 10.2 The Consent Gate

Beyond operating-system permission, capture of the user's screen, audio, camera, or external applications is gated by user consent scoped to what is captured and why. A consent request declares the sources, the reason, and the duration or scope of the grant; consent is a policy-gated approval (File 06) and is durable as a lease where the user grants standing consent. Capture proceeds only within the granted scope.

Camera capture requires typed-confirmation for each capture session. Standing consent leases for camera capture carry mandatory scope and duration limits, the recording-transparency indicator is prominent and always visible during camera capture, and camera consent is never inherited from screen or audio consent.

Wake-word detection requires standing audio capture consent and separate explicit enablement through settings. It is never enabled by default, never enabled as a side effect of another permission or consent grant, and never enabled by a profile or automation without prior typed-confirmation authorization.

### 10.3 Sensitive-Source Detection and Redaction

Perception detects sensitive capture sources and redacts before any persistence:

- sensitive-application detection (password managers, banking, medical, payment, and user-defined categories) raises the capture's sensitivity and may suppress persistence — a capture of a sensitive application is held in memory for the immediate operation and not committed as a durable observation unless the user permits it
- user-defined region redaction and per-source capture rules mask declared regions or sources before persistence
- the user may exclude sources entirely from capture

### 10.4 Secret and PII Redaction

Captured text — from optical-character recognition, file content, terminal output, environment snapshots, or accessibility-tree values — is subject to secret and personally-identifiable-information redaction before it becomes a durable `Observation`. A capture classified `Secret` (`block.sensitivity`, File 08 §9) never persists raw to the durable ledger or an observation; it carries a safe description only (`ledger.sensitivity-aware-persistence-retention`, File 10 §10). Password-marked fields and credential-bearing values are masked at capture. The credential vault is File 22's; perception references credentials by identity and never stores secret payloads.

### 10.5 Capture-Scope Bounding

File-system and repository capture respect declared exclusion lists (credential and key paths, configuration secrets) and the workspace boundary; a sensor must not capture content outside its declared and consented scope. Symlink resolution occurs before the boundary check. Capture scope is a registered, inspectable property of each sensor.

### 10.6 Sensitivity Classification

Every capture carries a sensitivity (`Public` | `Sensitive` | `Secret`, `block.sensitivity`, File 08 §9, `ledger.sensitivity-aware-persistence-retention`, File 10 §10). Sensitivity drives persistence, export, sync, and telemetry filtering. Screen and audio captures of sensitive sources are at least `Sensitive`. The default sensitivity is the sensor's declared `privacy_class` (§4.2), raised by sensitive-source detection. A processor-derived output's committed sensitivity is at least the maximum sensitivity of its input captures — raisable, never lowerable (§9.4).

### 10.7 Recording Transparency and Capture Ethics

Active capture is transparent and revocable: when a sensor is capturing continuously (a screen-share, camera, or audio stream), the user sees an indicator, can inspect what is being captured, and can revoke capture at any time. Perception observes; it does not defeat the protections of the sources it observes — it does not bypass bot-detection challenges and treats consent-and-cookie surfaces conservatively. Consented visual capture may incidentally include people or faces, but biometric identification, face recognition, emotion inference, or identity extraction is forbidden unless a registered capability, policy approval, and explicit user consent authorize that exact processing. Incidental faces raise sensitivity according to policy and may require redaction before persistence, export, or sync. These capture-ethics rules are part of the contract, not optional policy.

### 10.8 Boundary

This file owns the capture-privacy contract: permission, consent, sensitive-source redaction, secret masking, scope bounding, sensitivity classification, and recording transparency. The credential vault, trust state, and the policy-engine mechanics are File 22's and File 06's; this file specifies what perception must do before a capture becomes durable.

## 11. Capture Cost and Fidelity Management

Anchor: `perception.cost-fidelity`

### 11.1 Cost Controls

Perception minimizes the cost of capture:

- structured-first (§5.2) is the primary cost control — a structured capture is far cheaper in tokens than a pixel capture
- image captures are compressed through a declared pipeline (quality reduction, format conversion, resolution reduction) bounded by a configurable maximum payload size, and downscaled to a configurable resolution preset
- grounded analysis (optical-character recognition, visual grounding, transcription, captioning) is lazy: it runs only when requested, when the capture plan requires it, or when the structured tier is insufficient, and may be gated by declared sampling, power, privacy, and cost policies
- content-addressed deduplication (§6.4) prevents re-processing identical captures
- capture caching through a staleness-cache policy is a flagged time-based fallback (§8.2), not a default

### 11.2 Fidelity

A capture's fidelity (resolution, color depth, compression) is a declared, configurable property bounded so the capture is adequate for its consumer (a vision model, an optical-character-recognition engine, a human reviewer) without waste. The coordinate-space and scale-factor fidelity of §6.5 is preserved through compression so coordinates remain correct.

### 11.3 Boundary

This file owns capture-side cost and fidelity. Which captures are retained in a model request, and how trajectory images are pruned under context budget, is File 13's; perception supplies the compact, deduplicated captures and the diff data File 13 uses.

## 12. Robustness, Degradation, and Reconciliation

Anchor: `perception.robustness`

### 12.1 Graceful Tier Degradation

When a higher tier fails — the accessibility interface is unavailable, the required processor is unavailable, a permission is denied — perception degrades to the next available tier and records the degradation as freshness evidence on the capture. A capture that falls all the way through returns a typed capture error rather than fabricating structure.

### 12.2 Capture Error Classes

Capture errors are typed (`core.typed-errors`, File 01 §6.9): `PermissionDenied`, `PermissionRequired`, `SourceUnavailable`, `CaptureFailed`, `ProcessingFailed`, `StaleElement`, and `BackendUnavailable`. A capture error drives behavior — fall to a lower tier, request permission, surface to the user — rather than only displaying.

### 12.3 Dead-Sensor Circuit-Breaking

A sensor or processor backend that fails repeatedly is circuit-broken: after a settings-controlled failure threshold, perception marks it degraded, stops automatic attempts, and surfaces the degradation through the available-sensor set (`world.state-aware-capability-availability`, File 18 §9) and the bus. Recovery is primarily event-driven: source recovery signals, connection-lifecycle events, backend health recovery, or explicit user reset trigger re-attempts. A configurable minimum cooldown between recovery attempts is retained as a killable safety guardrail against flapping; it is configurable, cancellable through File 04's killability contract, and never a correctness condition. A per-source failure does not crash the Perception service; failures are isolated per sensor or processor.

### 12.4 Reconciliation and Re-Observation

On process restart or after an offline interval, perception re-establishes current state by re-observing the sources whose freshness matters (a content-hash reconciliation for file systems, a fresh capture for active surfaces) before resuming live watching; it does not present prior-session captures as current. A consumer that needs a guaranteed-fresh fact requests a re-observation (a fresh capture), which produces a new capture through the pipeline (§6). Reconciliation of the world model's own state is `world.observation-state-update` (File 18 §8.7)'s; perception owns the re-observation that feeds it.

### 12.5 Boundary

This file owns capture robustness and re-observation. World-model reconciliation, run-orphan recovery, and provider failover are Files 18, 04, and 17.

## 13. Exposure and Consumption

Anchor: `perception.exposure`

### 13.1 To the World Model

The primary consumer is the world model. Perception emits `PerceptionSignal`s and produces committed `Observation`s through the canonical observation/block path; `world.observation-state-update` (File 18 §8.2) projects them into entity attributes and surface state and links the entity to the observation by the `observes` relation (`world.world-entity`, File 18 §4.4). Perception supplies the structured output; the world model owns the state.

### 13.2 To Context Assembly

A structured observation is exposed to the agent through context assembly as a `trusted_runtime_fact` in the `RuntimeState` region (`context.semantic-regions`, File 13 §3, `context.authority-classes`, File 13 §2.3); a raw image, camera, or audio capture is exposed as a multimodal part only when the selected model and declared capture need require it (§5.2). Perception never performs model-request assembly; it supplies the source.

### 13.3 Reactive Subscriptions

Perception exposes reactive, event-driven capture subscriptions (`perception.watch`, §14): a subscription has a `perception_subscription_id`, owner, scope, sensor set, capture plan, sensitivity policy, consent lease references, output mode, cancellation relationship, and fallback diagnostics. It is individually cancellable and is cancelled categorically when its owning run, child run, session, sandbox, surface, or subsystem is killed (§2.5). A subscription that uses a polling fallback because no event source exists surfaces that fallback in diagnostics and is configurable (§8.2).

### 13.4 Multi-Session Scoping

Perception is multi-session and multi-scope; a consumer resolves captures and subscriptions for an explicit scope (`run.parallelism`, File 04 §15). There is no single-active-capture assumption. Captures and signals carry the scope identifiers so consumers demultiplex correctly (`ledger.event-envelope`, File 10 §5.2).

### 13.5 Boundary

This file owns the exposure and subscription contract. The transport and rendering belong to File 10 and the UI specs; what consumers do with captures belongs to those consumers.

## 14. Capability Surface

Anchor: `perception.capability-surface`

### 14.1 Closed Canonical Capabilities

Perception exposes its operations through the canonical Capability Registry (File 05). Each is a built-in capability declared per `capability.declaration` (File 05 §3) and registered at startup with the `Builtin` source:

- `perception.capture(sensor_id, request)` — performs one capture for the declared `CaptureNeed`; returns a transient `CaptureResult` and may stage a payload, but does not commit an `Observation` unless the request's output mode explicitly requires it. `ReadOnly` for non-sensitive sources; escalates to an approval tier when the source is sensitive or permission-gated
- `perception.observe(sensor_id, request, update_intent)` — performs a deliberate capture and invokes the canonical observation-commit path (§9.3); inherits the tier of the captured source and its sensitivity (`artifact.capability-surface`, File 09 §16)
- `perception.watch(sensor_id, filter, scope)` — opens a reactive capture subscription and returns a `perception_subscription_id`; `ReadOnly`, subscription-producing, cancellable
- `perception.list_sensors(scope)` / `perception.sensor_status(sensor_id)` — enumerate available sensors and their capabilities and permission state; `ReadOnly`, `ConcurrencySafe`
- `perception.request_permission(sensor_id, reason, scope)` — requests operating-system or platform permission acquisition (§10.1); distinct from Atlas consent
- `perception.request_consent(sources, reason, scope)` — requests capture consent (§10.2); produces a policy approval and, on grant, a lease
- `perception.check_permission(sensor_id)` — returns the `PermissionState` (§10.1); `ReadOnly`
- `perception.transcribe(audio_ref, params)` — invokes a transcription processor over captured audio; provider-routed processors execute through File 17
- `perception.ocr(image_ref, params)` / `perception.ground(image_ref, params)` — invoke processors over image captures to produce text or element structure (§7.4)
- `perception.register_sensor(sensor_spec)` / `perception.register_processor(processor_spec)` — sensor and processor registration (§4.4, §4.5); update-only producer operations under the source-trust envelope

### 14.2 Capability Metadata

Read and capture capabilities declare `deterministic_replayable` where they read a recorded observation and `snapshot_replayable` where their replay requires the recorded capture and fingerprint (`artifact.observation`, File 09 §13.4). Processor capabilities declare replay keying over the full invocation identity (§9.4). Capture and observe capabilities declare touched resources over the sensed source and the capture-payload store (registered as extension resource classes per `capability.extension-resource-classes`, File 05 §6.3), and a tier reflecting the source's sensitivity and permission requirement. Subscription-producing capabilities declare subscription ownership, cancellation, and cleanup separately from one-shot reads. Perception capabilities flow through the standard pipeline (`run.call-pipeline`, File 04 §8.2) and policy (File 06) and emit per §15.

### 14.3 Boundary

Capabilities are declared per File 05, executed per File 04, policed per File 06, surfaced per File 07. This file specifies the canonical perception capability set; per-surface and subsystem specs register additional sensors and capture capabilities through the same mechanism.

## 15. Events

Anchor: `perception.events`

### 15.1 Event Vocabulary

Perception emits on the canonical bus (File 10). Perception-specific events are registered custom events: `Custom { namespace: "perception", name, payload }`. This includes capture lifecycle events (`CaptureStarted`, `CaptureCompleted`, `CaptureFailed`), permission and consent transitions (`CapturePermissionChanged`, `CaptureConsentGranted`, `CaptureConsentRevoked`), degradation events (`SensorDegraded`, `SensorRecovered`), subscription lifecycle events, and `StagnationDetected`. `EnvironmentSnapshotCaptured` records a durable environment capture where File 10 declares that canonical ledger entry. A deliberate observation commit is recorded through the canonical observation/block/ledger path; a perception-specific `CaptureCommitted` notification, if emitted, is a custom event linked to the committed block.

### 15.2 Sensitivity and Delivery

A perception event that carries captured content carries the capture's sensitivity; `Secret` content never appears in a durably persisted event (§10.4, `ledger.sensitivity-aware-persistence-retention`, File 10 §10). High-frequency capture events are aggregated and normalized (§6.3) so they do not flood the bus or the durable ledger; the world model (`world.durability-tiers`, File 18 §7) decides which become durable.

Cross-sensor deduplication inside perception is a best-effort efficiency optimization: it may suppress duplicate signals when source identity and change signatures match. Cross-producer integration in the world model is the correctness mechanism. File 18's deterministic projection must handle overlapping and conflicting signals from any source whether or not perception deduplicated them; the world model must not depend on perception-layer deduplication for correctness.

### 15.3 Boundary

This file owns the perception event vocabulary. File 10 owns the envelope, delivery, aggregation, and ledger-commit contract.

## 16. Persistence Contract

Anchor: `perception.persistence`

### 16.1 What Is Durable

- `Observed`-tier captures are durable as `Observation` blocks (`artifact.observation`, File 09 §13) after the canonical observation-commit path, referenced by the world model and indexed through File 12
- registered `Sensor`s, `PerceptionProcessor`s, and `Custom` sensor kinds persist in the registry under the source-trust envelope (`capability.registered-capability`, File 05 §10, `policy.source-approval-flow`, File 06 §9)
- capture consent grants persist as leases (File 06)
- perception settings (§17)

### 16.2 What Is Computed

- the live capture stream and every `PerceptionSignal` — transient, never durably recorded by perception (the world model decides, `world.durability-tiers`, File 18 §7)
- the available-sensor set — computed per scope from registered sensors, permission state, and the world snapshot (`world.state-aware-capability-availability`, File 18 §9)
- staleness fingerprints — computed at capture time (§9.3)
- any processor-derived capture result — keyed by full processor invocation identity and recorded when committed, never stored as an unkeyed scalar (§9.4)

### 16.3 Reconstruction

A recorded `Observed` capture reconstructs deterministically through its content hash and fingerprint (§9.5). On restart, live perception is re-established by re-observation (§12.4). Replay consumes recorded captures, never re-capturing live sensors.

### 16.4 Boundary

This file specifies what is durable, computed, and reconstructable. File 20 realizes the capture-payload blob store and the physical layout; File 21 decides which captures cross devices (most are device-local — screens, audio, processes, displays; few are syncable).

## 17. Settings

Anchor: `perception.settings`

Perception behavior is configurable through the canonical settings system (File 15); this file names the dimensions, the settings system owns the cascade and storage. Settings use namespaced keys (`perception.*`) and declare scope, agent exposure, and locality per File 15.

Settings dimensions include:

- which sensors and processors are enabled, per scope and per surface, and per-sensor or per-processor enable/disable
- per-sensor capture tier preference, per-capture-need planning policy, processor selection, and processor fallback chain
- producer normalization policy per sensor: event coalescing, transient-pattern suppression, and stability rules (§6.3)
- the trigger policy per sensor: event sources, and — only for sensors that declare `NoChangeEvents` — the fallback-cadence and staleness-cache policies, disabled by default in favor of event-driven capture and flagged when enabled (§8.2)
- capture cost and fidelity: resolution presets, maximum payload size, compression policy, sampling policy, power policy, and grounded-analysis gating (§11)
- capture caching: whether a staleness-cache policy is enabled as a flagged fallback (§8.2)
- capture-privacy: sensitive-source categories and detection rules, region-redaction and per-source capture rules, secret/PII redaction patterns, biometric-processing gates, capture-scope exclusion lists, and the default sensitivity per sensor (§10)
- camera capture session confirmation, camera scope/duration lease limits, wake-word enablement, recording transparency, and the indicator behavior for continuous capture (§10.2, §10.7)
- reactive subscription behavior, cancellation defaults, and transport selection where the platform offers a choice
- circuit-breaking thresholds, event-driven recovery sources, and cooldown guardrails per sensor or processor (§12.3)
- agent exposure of perception output (which sensors, captures, and attributes appear in the agent's context, and at what fidelity), per File 15 `agent_exposure`
- per-scope overrides: global, workspace, conversation, profile, surface, and explicit-invocation overlay

Settings define intended product variation; they are not hidden hardcoded branches (`core.typed-configuration-failure`, File 01 §7.6, `settings.settings-over-constants`, File 15 §13). Specific defaults belong to settings profiles, not to this canonical layer.

## 18. Explicit Rejections

Anchor: `perception.explicit-rejections`

The following shapes are wrong for this layer:

- screenshot-driven or raw-media capture as the foundation of perception — structured capture is the foundation; raw capture is used only when the declared capture need requires it, lower tiers are insufficient, or deliberate evidence/human review/multimodal input is needed (`core.world-model`, File 01 §6.7, §5.2)
- skipping an available, cheaper tier or escalating to a higher-cost tier when a lower tier already yields the needed structure (§5.3)
- a central observer that screen-scrapes Atlas's own rendered UI — owned surfaces self-register their structured state (`world.observation-state-update`, File 18 §8.1); perception captures externally mutable or non-self-registering sources (§5.4)
- defining a parallel state model — perception produces observations and signals; the world model (File 18) holds and projects state (§2.2)
- polling as the primary capture mechanism — capture is event-first; polling and staleness-cache policies are flagged, configurable fallbacks for sources without change events, never correctness conditions (§8, `core.event-first-by-default`, File 01 §7.15)
- deriving capture cadence, scheduling, or correctness from elapsed time except through the flagged polling fallback — capture time is provenance only (§8.3)
- a non-deterministic record of a capture — the world is non-deterministic, but a recorded capture is immutable and replay-stable, and replay never re-captures live sensors or re-runs processors against live sources (§9.5)
- storing a processor-derived capture result (optical-character recognition, grounding, transcription, captioning) as an unkeyed scalar — such results are keyed by full processor invocation identity (§9.4, `core.explicit-rejections`, File 01 §8)
- hashing a capture over its raw container bytes — capture hashes and fingerprints are computed over a declared `CanonicalEncoding`: structured captures over the canonical structure, opaque media over a declared canonical media encoding (§6.4, `core.canonical-hash`, File 01 §7.14)
- capturing a permission-gated source without permission, or capturing a consented source outside its consented scope (§10.1, §10.2)
- persisting raw secret content in any capture, observation, or event — `Secret` captures carry safe descriptions only (§10.4, `ledger.sensitivity-aware-persistence-retention`, File 10 §10)
- defeating the protections of a sensed source — bypassing bot-detection, performing biometric identification without explicit capability and consent, or treating consent surfaces non-conservatively (§10.7)
- perception acting on the world — perception senses; clicking, typing, navigating, and mutating are the per-surface action executors' concern (§3.3)
- inventing a block kind or observation kind outside File 09's catalogue or registered extension mechanism, or deciding a capture's durability tier — File 09 owns the observation schema and `world.durability-tiers` (File 18 §7) owns durability classification (§2.2, §2.3)
- a private per-surface perception substrate — there is one Perception service; surfaces register sensors into it (§4.4)
- unnormalized capture churn as output — producers must suppress unstable source artifacts before emitting (§6.3, `world.observation-state-update`, File 18 §8.3)

## 19. Consequences for Later Specs

Anchor: `perception.consequences-for-later-specs`

Later specs must follow these rules:

- Per-surface specs (Coder, Web, Data Processor, Teacher, GUI Control, System Agent) must declare their specific sensors, processors, and named availability checks against this substrate, instantiate the tier model rather than inventing a parallel capture pipeline, and consume the capture contract; the GUI Control surface's desktop perception, the Web surface's browser perception, the Data Processor surface's document capture, and the System Agent surface's system observation are instantiations of the sensor kinds, processor model, and tier strategy defined here.
- The Work Surface Contract spec (File 25) must let surfaces declare which sensors they expose and the privacy class of each; perception holds the live capture mechanics behind those declarations.
- The Automation and Triggers spec must drive automation from explicit events and perception change signals, not from a capture clock; it consumes perception's change signals and must not introduce a parallel watcher layer.
- The Security spec must own the credential vault and trust state perception references by identity, must treat `Secret` captures as safe-description-only, and must own the policy mechanics behind capture consent.
- The Sandbox spec must own process and sandbox isolation; perception captures process and system state and references active sandboxes and devices without owning their isolation.
- The Workspaces and Materialization spec must own workspace and repository identity; perception captures their state as file-system and repository observations.
- Storage specs must persist `Observation` capture payloads in a content-addressed blob store, persist registered sensors, processors, and settings, and realize the capture-payload layout; they must not conflate the storage encoding with the hash encoding.
- Sync specs must consume locality metadata: most captures are device-local (screens, audio, processes, displays, environment) and do not sync; few are syncable.
- Files 16 and 17 must own model and provider selection for model-mediated processors; perception declares the workload and consumes the selected model/provider, and provider health is referenced, not re-derived.
- UI specs must render captures and capture indicators as projections, consume the reactive subscription rather than polling, and surface the recording-transparency indicator for continuous capture.
- The world model, block, ledger, version, capability, policy, tool-surface, execution, and context specs already depend on this layer: perception produces the observations and signals `world.observation-state-update` (File 18 §8) consumes, invokes the `Observation` block path `artifact.observation` (File 09 §13) defines, emits perception-owned custom events through File 10, and supplies the staleness fingerprints `run.call-pipeline` (File 04 §8.2) revalidates.

## 20. Canonical Rule Anchors

Anchor: `perception.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `perception.chosen-model`, `perception.boundaries-with-adjacent-layers`, `perception.perception-service`, `perception.sensor`, `perception.tiered-sensing`, `perception.capture-pipeline`, `perception.per-modality-contracts`, `perception.triggers`, `perception.output-contract`, `perception.capture-privacy`, `perception.cost-fidelity`, `perception.robustness`, `perception.exposure`, `perception.capability-surface`, `perception.events`, `perception.persistence`, and `perception.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
