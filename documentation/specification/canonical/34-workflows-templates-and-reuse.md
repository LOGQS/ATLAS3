# Workflows, Templates, and Reuse

## Status

Canonical. This file defines the `Workflow`, `WorkflowGraph`, `Template`, `Macro`, and `TemplateLibrary` primitives, and the contracts by which successful work is crystallized into reusable, parameterized, versioned, shareable, composable units that run over the one execution-graph model. It realizes the reusable-workflow body that `automation.consequences-for-later-specs` (File 33 §23) and `automation.automation-object` (File 33 §6.2) delegate here (an `Automation`'s `task_template` references a workflow by identity and parameterizes it at fire time), the reuse proposals that `run.automation-reuse` (File 04 §26) declares, the graph/workflow execution shape that `run.execution-structure` (File 04 §5.3) names but deliberately leaves schemaless, the `WorkflowTemplate`/`Macro`/`InstructionFragment`/`Adapter`/`Validator` artifact kinds that `artifact.artifact-kind` (File 09 §4.1) reserves, the `WorkflowNodeComplete` commit boundary that `version.version-op-summary-commit-boundary-set` (File 11 §5.2) records, and the per-surface pipeline, curriculum, classroom, macro, and saved-command reuse that the per-surface specs (Files 27–32) defer here. It is the second post-surface spec: horizontal and surface-neutral, the way `worksurface.work-surface` (File 25), `controlrail.chosen-model` (File 26), and `automation.chosen-model` (File 33) are. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `Workflow` — a durable, registered, versioned, parameterized reusable operation whose body is a `WorkflowGraph` over the one execution-graph model; the crystallization of successful multi-step work into a saved, inspectable, composable operator
- the `WorkflowGraph` — the canonical body grammar `run.execution-structure` (File 04 §5) declined to fix: a directed acyclic graph of typed `WorkflowNode`s connected by `WorkflowEdge`s with declared input bindings, declared input and output nodes, and the closed-canonical `NodeKind` catalogue (`Model`, `Tool`, `Merge`, `Branch`, `Loop`, `SubWorkflow`, `Programmatic`, plus `Custom`), mapping each node to the execution unit (`run.execution-structure`, File 04 §5.2) it runs as
- the **parameter contract** — typed parameter slots with type, default, constraint, requiredness, sensitivity, and description; the declared-slot binding rule by which fire-time or invocation-time values substitute into node arguments, model selections, instruction-fragment or model-request assembly references, and bodies; and the no-raw-interpolation invariant
- composition — `SubWorkflow` nesting, the bounded-recursion guard, workflow-as-operation exposure through an adapter capability, and block-level body composition over `block.cross-surface-interoperability` (File 08 §12)
- the `Macro` — a recorded, parameterized, replayable action-sequence reusable unit, its cross-surface contract, and the macro-to-workflow conversion path
- `Template` and the reusable-unit family — the unified treatment of `Workflow`, `Macro`, and content/instruction templates (document templates, prompt and instruction-fragment templates, workspace scaffolds, style templates) as members of one reuse layer sharing the library, parameterization, promotion, versioning, and sharing machinery; and the boundary with the reusable instruction fragment (`Skill`)
- identity, versioning, and source — the workflow definition as a versioned `WorkflowTemplate` entity over the block pool (File 08) and version graph (File 11), and the source taxonomy mirroring `capability.sourcing` (File 05 §9)
- the `TemplateLibrary` — the one catalog of reusable units, its scopes, the layered source precedence, discovery, the built-in and per-profile and plugin-bundled libraries, and sharing/import/export
- creation and the graduation path — crystallization from a successful run (primary), natural-language authoring, manual construction in the workflow editor, and promotion from a macro; the no-silent-creation rule; the promotion forgery guard; and provenance preservation
- validation, simulation, and reliability — validate-before-save, dry-run/simulation, output-drift detection, and the workflow validation policy
- workflow execution — how a workflow runs as an ordinary `Run` over the one executor, parameter binding at instantiation, the four-option retry vocabulary over the version graph, per-node output reuse, and partial execution
- invocation — how a workflow is invoked by identity from the conversation, the command and slash rails, an agent, or an `Automation`'s trigger binding; and the `workflow.*`/`template.*`/`macro.*` capability surface
- surface aliasing — the rule that data pipelines, notebooks, teacher curricula and classrooms, coder saved commands, and surface monitors realize as reusable units over the one library and the one executor
- the events, the persistence/locality/portability split, the settings dimensions, the explicit rejections, and the consequences for later specs

This file does not define:

- the executor, the run lifecycle, the capability-call pipeline, child-run isolation, cancellation, parallelism bounds, budgets, stuck detection, or the retry/reroute/branch run mechanics — File 04 owns those; this file owns the reusable body the executor runs and maps its node kinds onto File 04 execution units
- the trigger taxonomy, the `Scheduler`, the watch policy, missed-fire handling, eligibility gating, non-interactive-execution safety, overlap, or the trigger-to-run handoff — File 33 owns those; this file owns the workflow body an `Automation`'s `task_template` references and parameterizes
- routing, the `RunIntent` field set, deterministic prechecks, pin-through behavior, or reroute — File 03 owns those; invoking a workflow produces a `RouteRequest`/`RunIntent`, routing produces the decision
- the `CapabilityDeclaration` field set, the registry, capability identity/versioning, runtime registration, or adapter-capability mechanics — File 05 owns those; this file declares the `workflow.*` capabilities as canonical built-ins and exposes a workflow as an operation through an adapter capability
- policy evaluation, effective tier resolution, leases, approval flows, typed-confirmation, or source approval — File 06 owns those; a workflow run is gated by the one policy layer like any run, and a workflow node may carry a permission-tier override
- the `ToolSurface` zone model, composition, or borrowing — File 07 owns those; a node's `tool_allowlist` composes the node's surface, and a workflow exposed as an operation surfaces through the one lens
- the `Block` model, `BlockKind` catalogue, content variants, or composition operation mechanics — File 08 owns those; a workflow body and its node outputs are blocks
- the `Artifact` entity, the `ArtifactKind` catalogue, materialization, validation/critique blocks, or provenance queries — File 09 owns those; this file specifies the `WorkflowTemplate`/`Macro` reuse semantics over them
- the `ContextVersion`, `VersionDiff`, commit boundaries, replay modes, snapshot resolution, or sync conflict merge — File 11 owns those; a workflow definition and run are versioned entities over the graph
- context assembly, per-policy block selection, compaction, or instruction-source authority and rendering — File 13 owns those; this file names a node's default `ContextPolicy` and the loading of an instruction-fragment template by reference
- the settings object model, the cascade, profiles, locality, or agent exposure — File 15 owns those; this file names the dimensions
- the storage substrate, the on-disk layout, the `dag_configs`/`dag_presets`/`dag_node_output_cache` physical schema, replication, the conflict-resolution pipeline, or the portable bundle format — Files 20 and 21 own those; this file specifies what is durable, what is device-local, and what is portable
- the per-surface node libraries, recording mechanics, surface-specific runtimes, or surface workflows — the per-surface specs (Files 27–32) own those; this file owns the one body grammar, the one library, and the one reuse layer they realize over
- plugin packaging, contribution-point registration, and the plugin install lifecycle — File 35 (Extension and Plugin System) owns those; this file owns the workflow body a plugin bundles
- webhook and external-protocol transport for externally triggered workflows — File 33 and File 36 (MCP and External Integrations) own those
- the workflow-reliability evaluation harness, the validator catalogue, or completion-check internals — File 09, `run.termination` (File 04 §22), and the Quality Control and Evaluation specs (Files 39 and 40) own those; a workflow's validation policy selects among them
- UI rendering — the workflow editor canvas, the template-library browser, the parameter-entry form, the simulation view, and the reliability dashboard — File 37 and File 38 own those; this file specifies the data and resolution contracts they consume

## Source Resolution

Families reviewed: the prior ATLAS3 specbase execution-graph material (`conversation/06-chat-dag.md` — the one DAG service over four context kinds, the `DagConfig`/`DagNode`/`DagEdge`/`NodeKind` (`Model`/`Tool`/`Merge`/`Branch`/`SubDag`/`Custom`)/`ModelHint`/`EdgeCondition` grammar, the per-node output cache keyed by `(node_id, sha256(canonical input))`, the four-option retry vocabulary, `DagValidationIssue`, the `DagPreset` library and built-in presets, the `DagExecutor`/`DagService` traits, and the shared `ExecutionGraphCanvas`; `systems/19-scheduling-pipeline.md` §19.3 — workflows and pipelines as the unified DAG over `dag_configs` with `context_kind` `workflow`/`pipeline`, "nothing about workflows or pipelines needs a separate engine," the four-subsystem framing, the per-node timeout/concurrency/loop-iteration constraints; `systems/README.md` §19.3/§19.4 — the workflow engine, the visual pipeline builder, custom-operator wizard, and the design decisions; `infrastructure/database.md` §12–§14 — the `dag_configs` (`context_kind` ∈ `chat`/`agent_inner_loop`/`pipeline`/`workflow`), `dag_presets` (`category`, `scope` ∈ `global`/`workspace:<id>`/`user`), and `dag_node_output_cache` tables, and the deliberately-absent `tasks` table ("agent tasks are DAG executions"); `infrastructure/sync.md` — `dag_configs`/`dag_presets` sync, `dag_node_output_cache` device-local; `conversation/03-versioning-and-branching.md` and `ui/15-3-and-15-4-participation-levels-personas.md` — the `ViewPreset` carrying `dag_preset_id` + `default_skills`, `capture_current`/export/import, and `PresetScope`; `cross-cutting/composition.md` — composed-block `children_block_ids`, `group`/`ungroup`/`flatten`, cross-chat copy-vs-materialize; `cross-cutting/artifacts.md` — `WorkflowTemplate` as an artifact = file/block, schema-versioned, portable; `agents/domain-architecture.md` — `DomainSpec.default_dag_preset_id`, the `SkillSpec`/`SkillRegistry`, the built-in default DAGs, and "Skills are the only named-instruction primitive"; the `DomainSpec` `primary_dag_preset` and `spawnable_subagents` fields across `unit08-coder.md`/`unit09-web.md`/`unit10-gui-control.md`/`unit11a-memory.md`/`unit11b-data-processor.md`/`unit11c-system-agent.md`/`unit11d-teacher.md`); the unit recommendations (`unit14-systems.md` §19 — D14.SP.1 the ten per-profile default-workflow libraries and the `[[plugin.workflows]]` manifest with `path`/`name`/`description`/`category`/`agent_invocable`, D14.SP.2 single-scheduler alias, D14.SP.4 data nodes as `NodeKind::Custom` (`data.parse.*`/`data.transform.*`/`data.validate.*`/`data.output.*`), D14.SP.5 macro-to-workflow conversion and plugin-bundled workflows; D14.SM.2 the custom-tool→plugin promotion path bundling workflows; `unit04-routing-agents-prompt.md` D4.1 `NodeKind::Programmatic { agent_id, config }`, D4.3 `spawnable_subagents`, D4.7 `code.execute_with_tools` programmatic scripting; `unit11-cross-tool-learning.md` CT.9 `automations.create`/`ScheduleSpec`, CT.14 the `AtlasPlugin` bundle (`skills`/`commands`/`mcp_servers`/`persona`) and `SlashCommand { trigger, description, skill_id, args_template }`; `unit06-tools.md`/`unit11b-data-processor.md` D11.DP.7 notebook↔pipeline convertibility ("turn this notebook into a reusable pipeline"), D11.DP.12 "a pipeline is a macro" under the shared `cross-cutting/macros.md`, D11.DP.9 data lineage; `unit11c-system-agent.md` D11.SA.6 `TaskAction::RunMacro`/`SpawnChat { template }`, `sys.script.template_list`/`template_apply`; `unit11d-teacher.md` D11.T.4 the parameterizable `Classroom` agent-graph template and D11.T.6 `teacher.curriculum.from_document` as a reusable curriculum body; `unit13-ui.md` the deferred recipe system); the strategic target-state review (`codex_recommendations.md` §5.4 the `HierarchicalTaskGraph` node taxonomy and per-node declared contract, §8.11 the Workflow Studio surface, §9.3 "the best automation system is about crystallizing successful work into reusable operators," §9.4 AI-generated reusable units (workflow templates, custom tools, app adapters, extraction schemas, validators, prompt fragments, document templates) with approval/scoping/eval/provenance requirements, §14.2 `artifact_kind = workflow_template` with `produced_by_run_id`/`produced_by_node_id`/`derivation_summary`, §15.1 step 10 "commit outputs to … workflow candidates"); the ATLAS3 core (`atlas3-core/TODO.md` §19.3 "Workflows and pipelines collapse into one mechanism … Same executor … Same `ExecutionGraphCanvas` … No parallel runtime, no parallel editor, no parallel storage," the three creation paths (command palette, chat, promote-an-existing-chat-DAG), §19.4 AI-assisted construction and `dag_config_versions`, §15.3 view presets, §5.7 context recipes; `atlas3-core/CONSTRAINTS.md` §12 block-first (no parallel tables), §14 DAG config portable, §7b settings-over-constants, §11 the `node_id`/`worktree_id` event envelope; `GLOSSARY.md` `DAG`/`ExecutionGraphCanvas`/`Skill`/`View Preset`/`Checkpoint`, "Procedure → Skill"); the external workflow engines and reuse systems (`n8n` — the `WorkflowParameters`/`INode`/`IConnections` graph model, the typed `INodeProperties` property system and `resourceLocator` multi-mode parameters, pin-data for testing without upstream execution, the partial-execution "run from here" subgraph algorithm, waiting-execution for multi-input joins, the source-vs-destination dual connection index, the workflow checksum/diff, node `retryOnFail`/`maxTries`/`continueOnFail`/`alwaysOutputData`/`executeOnce`; `langflow` — the `Graph`/`Vertex`/`Edge` topological layer execution, `CycleEdge.honor()`, the `ConditionalRouter` and `Loop`-as-isolated-subgraph components, `SubFlow`/`RunFlow`/`FlowToolComponent` (a saved flow as a tool), and runtime `tweaks` overriding parameters while blocking the `code` field; `goose` — the `Recipe { version, title, description, instructions, prompt, extensions, settings, parameters, response, activities, author }` reusable-workflow body with structured-output enforcement and recipe-based scheduling; `archon` — the YAML DAG with seven node types (`command`/`prompt`/`bash`/`loop`/`approval`/`cancel`/`script`), per-node parameter overrides, `depends_on` edges, topological concurrent-layer execution, `$node.output` variable substitution, the bundled<global<project source precedence, the four trigger rules, the fifteen typed workflow events, and Zod validation with cycle detection; `swarms` — the `AgentRearrange` flow syntax (`->` sequential, `,` concurrent, `H` human node) and seventeen named orchestration strategies; `autogen` — `DiGraph` conditional edges with `activation_group`/`activation_condition`, composable termination, `SocietyOfMind` sub-team-as-node, and the declarative `_to_config`/`_from_config` component model; `storm`/`paper2video`/`ai-scientist-v2`/`cosight`/`deeptutor`/`ppt-master`/`openspec` — resumable multi-stage pipelines with per-stage skip/resume and node-output reuse, per-node model configuration, tree-search fan-out, compile-fix loops, the Kahn's-algorithm artifact dependency graph, the `spec_lock` re-read-before-each-output parameter contract and drift validator; `acontext`/`evolver`/`operator-use`/`opengame`/`hermes`/`autoresearch` — the crystallization-of-successful-work pipelines (distillation + skill-learner, the `Gene`/`Capsule`/`EvolutionEvent` triad with a promotion forgery guard rejecting empty traces/zero blast radius/missing exit codes, skill detection from repeated tool sequences, the meta-template evolution loop, the self-PR promotion gate chain, the `program.md` structured workflow body, the curator's library consolidation); the skill systems (`claude-code`/`qwen-code`/`deer-flow`/`open-cowork`/`cline`/`continue`/`opencode`/`open-webui`/`space-agent`/`pi`/`open-codesign`/`agent-zero`/`multica`/`codex_tool` — `SKILL.md` with YAML frontmatter, tiered discovery, progressive disclosure, parameterization via template variables, the `disable-model-invocation`/`user_invocable` flags, the meta-skills `skill-creator`/`skill-installer`); and the saved-operation surfaces (`workspace-management.md` and `domains/coder/` the `.atlas/commands/` YAML custom commands with typed `parameters`/`mode`/`prompt`/`shortcut` and the `copyTemplate` scaffolds; `domains/web/05-advanced-features.md` and `domains/gui-control/05-action-recording.md` the `Macro`/`MacroStep`/`MacroParameter` recording-parameterize-replay with `is_variable`/`sensitive` flags, the element-selector hierarchy, and the `~/.atlas/macros/` library with `success_rate` metadata; `chatgpt_tool`/`codex_tool`/`claude_code_tool` saved-prompt automations and `artifact_handoff`).

Resolution rule: this file realizes and introduces; it does not re-own. The executor, the run, child runs, parallelism, cancellation, budgets, retry/reroute/branch run mechanics, and the automation-reuse proposal stay File 04's; the node-kind grammar's *execution semantics* (a `Model` node runs as a model step, a `Tool` node as a capability call, a `SubWorkflow` node as a child run) stay File 04's, while this file owns the *body grammar* `run.execution-structure` (File 04 §5) declined to fix; the trigger taxonomy, scheduler, watch policy, eligibility, non-interactive safety, and trigger-to-run handoff stay File 33's; routing, `RunIntent`, and pin-through stay File 03's; the capability declaration, registry, identity, and adapter-capability mechanics stay File 05's; policy, leases, and approval stay File 06's; tool-surface composition stays File 07's; the block model and composition operations stay File 08's; the artifact entity, the `ArtifactKind` catalogue, and provenance queries stay File 09's; the version graph, commit boundaries, and replay stay File 11's; context assembly and instruction-source authority stay File 13's; settings and profiles stay File 15's; storage, the physical `dag_configs`/`dag_presets`/`dag_node_output_cache` layout, locality, sync, and the portable bundle stay Files 20 and 21's; per-surface node libraries and recording mechanics stay the per-surface specs'; plugin packaging stays File 35 (Extension and Plugin System)'s. This file owns the `Workflow` object, the `WorkflowGraph` body grammar and its closed `NodeKind` catalogue, the parameter contract, composition, the `Macro` reusable unit and macro-to-workflow conversion, the reusable-unit family and the `TemplateLibrary`, the creation-and-graduation paths, validation and simulation, invocation and workflow-as-operation, the surface-aliasing rule, and the `workflow.*`/`template.*`/`macro.*` capability surface.

Resolved tensions:

- **A workflow engine, or the one execution model.** The specbase scattered "workflow engine," "visual pipeline builder," and "agent inner loop" across `systems/19-scheduling-pipeline.md` and `06-chat-dag.md`, and `unit14-systems.md` D14.SP framed "four integrated but distinct subsystems." `atlas3-core/TODO.md` §19.3 is decisive: workflows and pipelines "collapse into one mechanism … Same executor … Same `ExecutionGraphCanvas` … No parallel runtime, no parallel editor, no parallel storage," and `run.explicit-rejections` (File 04 §28) rejects "making every request a heavy task graph" and "background work as a separate execution architecture." This file adopts the one-execution-graph-model rule absolutely: a `Workflow`'s body is a `WorkflowGraph`, and it runs as an ordinary `Run` over the one executor `run.execution-structure` (File 04 §5) defines. A pipeline is a workflow whose nodes are predominantly data nodes; a chat DAG, an agent inner loop, a pipeline, and a scheduled workflow are four context kinds of one graph. No second engine, editor, or store is introduced.
- **Where the graph schema lives.** `run.execution-structure` (File 04 §5) states "the canonical requirement is not a specific graph schema" and deliberately leaves the body grammar open; `06-chat-dag.md` is the source where the `DagConfig`/`NodeKind` grammar was sketched but is not itself canonical. This file resolves the gap exactly as `capability.chosen-model` (File 05 §1) is to `run.capability-execution` (File 04 §8): File 34 owns the reusable *body grammar* (`WorkflowGraph`, `NodeKind`, parameters), and File 04 owns the *executor* that runs each node as an execution unit. The boundary is the same body-versus-run split `automation.run` (File 33 §10.1) already fixed for the workflow a `task_template` references.
- **A workflow as a capability, or its own primitive.** `capability.explicit-rejections` (File 05 §19) forbids "treating `Capability` and 'skill' / 'workflow' / 'instruction-pack' as the same primitive — capabilities are typed executable contracts; skills are instruction modules; workflows are reusable orchestrations; each is its own primitive with its own registry." This file keeps `Workflow` a distinct primitive (a reusable orchestration body), not a `Capability`. To make a workflow invocable through the one capability pipeline (so it composes as a node, an agent tool, a palette entry, an automation target), the workflow is *exposed as an operation* through an adapter capability (`capability.adapter-capabilities`, File 05 §17.4) that delegates to the workflow executor; the workflow itself is never a capability declaration.
- **A parallel workflow store, or the shared substrate.** `infrastructure/database.md` deliberately omits a `tasks` table ("agent tasks are DAG executions, stored in `dag_configs` + `dag_node_output_cache`"), `atlas3-core/CONSTRAINTS.md` §12 forbids parallel tables for substrate-owned objects, and `automation.persistence` (File 33 §18) dissolved the `automations`/`scheduled_tasks` tables into versioned block-backed entities. This file follows the same posture: a `Workflow` definition is a versioned `WorkflowTemplate` entity over the block pool (File 08) and version graph (File 11), exposed physically as the `dag_configs`/`dag_presets` shared persistence the storage spec (File 20) realizes — not a private workflow table. The per-node output cache (`dag_node_output_cache`) is device-local execution state owned by the executor, never part of the definition.
- **Skills as this file's, or instruction modules elsewhere.** `agents/domain-architecture.md` states "Skills are the only named-instruction primitive" and the `GLOSSARY` fixes a `Skill` as a `block_type = "skill"` reusable instruction fragment loaded into context, with "Procedure → Skill" retired. A `Skill` is not a `Workflow` (an instruction module is not an execution graph). This file resolves the boundary by owning the *reuse layer* — a `Skill`/instruction-fragment is one reusable-unit kind that participates in the one `TemplateLibrary`, the parameter contract, the promotion path, and versioning/sharing — while its content carriage stays `block.block` (File 08), its `InstructionFragment` artifact kind stays `artifact.artifact-kind` (File 09 §4.1), and its loading and authority into a model request stay `context.instruction-sources-workspace-files` (File 13 §16). This file re-owns no context assembly and no instruction authority.
- **Macros as a per-surface feature, or a cross-cutting reuse primitive.** The specbase defined parallel `Macro` structs in `domains/gui-control/05-action-recording.md` and `domains/web/05-advanced-features.md`; `unit10-gui-control.md` D10.8 proposes one `cross-cutting/macros.md` with a `domain` discriminator and one library, and `unit11b-data-processor.md` D11.DP.12 states "a pipeline is a macro." This file adopts the unified posture: a `Macro` is a recorded-action reusable unit — the low-code, recorded form of a workflow body — owned by this file's reuse layer (one library, one parameter contract, one promotion-to-workflow conversion), while the recording mechanics and element-selector model stay the per-surface specs (Files 28 and 31). A macro graduates into a `Workflow` by node conversion; a data pipeline is a workflow, surfaced as a macro in the cross-surface library.
- **Crystallization as a graduation, or hand-authoring.** `codex_recommendations.md` §9.3 frames the central insight: "the best automation system is not mainly about time triggers; it is about crystallizing successful work into reusable operators," and §15.1 makes "workflow candidates" a first-class run output. This file makes graduation-from-a-successful-run the primary creation path (alongside natural-language authoring, manual construction, and macro promotion), gated by a promotion forgery guard (a run with no ledgered execution evidence cannot crystallize), the no-silent-creation rule (`automation.creation-and-graduation`, File 33 §15.2 and `systems/17-agent-self-modification.md`), and provenance preservation (`produced_by_run_id`/`produced_by_node_id`/`derivation_summary`).

## 1. Chosen Model

Anchor: `workflow.chosen-model`

### 1.1 Definition

A `Workflow` is a durable, registered, versioned, parameterized reusable operation. Its body is a `WorkflowGraph` — a directed acyclic graph of typed nodes over the one execution-graph model `run.execution-structure` (File 04 §5) names. A workflow is the saved, inspectable, composable, shareable crystallization of a multi-step operation: the operator the system runs when the same shape of work recurs, whether invoked directly by a user, by an agent, or by an `Automation`'s trigger binding.

A `Template` is the broader reusable unit. The reusable-unit family has three concrete kinds: the `Workflow` (the executable-body kind), the `Macro` (the recorded-action kind, §6), and content/instruction templates (document templates, prompt and instruction-fragment templates, workspace scaffolds, and style templates — the non-executable kinds, §7). All three share one library, one parameter contract, one promotion path, and one versioning-and-sharing machinery; they differ in what they carry and how they are applied.

The `TemplateLibrary` is the one catalog of reusable units across all kinds, scopes, and sources. It holds built-in presets, per-profile and plugin-bundled bundles, user-saved units, and graduated-from-run units, resolved through one layered precedence.

### 1.2 Purpose

The system's value compounds when successful work becomes reusable. A research session that produced a good report, a debugging sequence that fixed a class of error, a data pipeline that cleaned a dataset, a curriculum that taught a topic well, a recorded sequence of desktop actions — each is a transient `Run` whose structure is worth keeping. The reuse layer is how that structure becomes a durable, parameterized operator: authored once, run many times with different inputs, composed into larger operators, scheduled by an `Automation`, shared across devices and installations, and improved over its version history.

The reframe is load-bearing: a workflow is **not** a script bolted onto a separate engine. It is a saved body of the one execution graph, parameterized by a typed contract, stored in the one library, versioned by the one version graph, and run by the one executor under the one policy layer. Reuse is crystallized intent, not parallel architecture.

### 1.3 Rule

- There is one `Workflow` primitive, one `WorkflowGraph` body grammar, one `TemplateLibrary`, and one reuse layer. No subsystem, surface, or plugin introduces a parallel workflow engine, a parallel graph editor, a parallel workflow store, a private template registry, or a separate reusable-operation mechanism. Every workflow, pipeline, notebook-as-pipeline, curriculum body, classroom topology, saved command, and macro is a reusable unit over this layer.
- A `Workflow`'s body is a `WorkflowGraph` that runs as an ordinary `Run` over the one executor (`run.execution-structure`, File 04 §5; `run.chosen-model` File 04 §1). Each `WorkflowNode` runs as the execution unit (`run.execution-structure`, File 04 §5.2) its kind maps to. There is no parallel runtime; "graph or workflow execution" is one of the run's `run.structure-shapes` (File 04 §5.3).
- A `Workflow` is built over the shared substrate and reuses it without reimplementing it: its definition is a versioned `WorkflowTemplate` entity over `block.block` (File 08) and the version graph (File 11); it produces and consumes `Block`s (File 08); its nodes invoke `Capability`s (File 05) gated by the one policy layer (File 06); it is exposed as an invocable operation through an adapter capability (File 05 §17.4); it is scheduled by referencing it from an `Automation` (File 33); its library rides settings and profiles (File 15); its definition syncs and exports through the shared substrate (Files 20, 21).
- A `Workflow` is a distinct primitive from a `Capability` and a `Skill` (`capability.explicit-rejections`, File 05 §19): a capability is a typed executable contract, a skill is a reusable instruction fragment, and a workflow is a reusable orchestration body. Each has its own identity and registry; this file owns the reuse layer that unifies their library, parameterization, promotion, and sharing without merging the primitives.
- Reuse units are never created or enabled silently (§11). Crystallization from a successful run produces a proposal the user reviews; agent-initiated authoring passes the proposal-first source-approval path (`policy.source-approval-flow`, File 06 §9).

### 1.4 Boundary

This file owns the reusable workflow body, the graph grammar, the parameter contract, composition, macros and macro-to-workflow conversion, the template library, the creation-and-graduation paths, validation and simulation, invocation and workflow-as-operation, the surface-aliasing rule, and the reuse capability surface. It does not own the executor, the run, routing, the trigger binding, capabilities, policy, blocks, artifacts, the version graph, context assembly, settings, storage, sync, per-surface node libraries, or plugin packaging — those are realized through their owning files.

## 2. Boundaries with Adjacent Layers

Anchor: `workflow.boundaries`

### 2.1 With File 01 (Core Thesis)

This file realizes `core.product-thesis` (File 01 §1)'s "successful work patterns are eligible for crystallization into reusable knowledge, procedures, and automations." Reuse is one of the `core.extension-planes` (File 01 §6.14) planes (automation and configuration); the `NodeKind` and reusable-unit-kind sets are closed-canonical-plus-`Custom` per `core.closed-canonical` (File 01 §6.16). A workflow definition is `core.versioned-durable-state` (File 01 §6.10); its run history and node-output reuse are projections (`core.projection`, File 01 §6.11); its operations are non-destructive (`core.non-destructive-by-default`, File 01 §7.13 — editing a workflow creates a sibling version). `Workflow`, `WorkflowGraph`, `Template`, `Macro`, and `TemplateLibrary` are new canonical noun-objects.

### 2.2 With File 02 (Conversation, Intent, Task) and File 03 (Routing)

Invoking a workflow produces a `RouteRequest` that carries the workflow reference and its bound parameters and routes through `routing.dispatch-pipeline` (File 03 §3) into a `RunIntent` (`routing.run-intent`, File 03 §4.3). The `RunIntent` never carries the workflow body: its existing fields carry the pinned `model_route` and `tool_surface_strategy` and an `execution_entry` of `multi_step_agent` (or `surface_runtime` for a surface-bound body) under which the run takes the graph/workflow structure shape (`run.structure-shapes`, File 04 §5.3); the rest of the operation state enters as run-state snapshots at File 04 §6 step 3. Neither the `RunIntent` field set nor the execution-entry set is widened. Routing fills only unpinned fields, exactly as `routing.trigger-kinds-routing` (File 03 §2.1) pins automation fields. A workflow run attaches to a conversation, an intent thread, and an optional task (`intent.task`, File 02 §6); a workflow may itself be promoted from work spanning a task. This file owns the workflow body; File 03 owns the route the invocation produces.

### 2.3 With File 04 (Execution and Run Model)

`run.execution-structure` (File 04 §5) declines to fix the graph schema and lists "graph or workflow execution" among `run.structure-shapes` (File 04 §5.3); this file fixes that schema as the `WorkflowGraph`. Each node maps to an execution unit (`run.execution-structure`, File 04 §5.2): a `Model` node to a model step (`run.model-steps`, File 04 §13), a `Tool` node to a capability execution (`run.capability-execution`, File 04 §8), a `Programmatic` node to programmatic execution (`run.programmatic-execution`, File 04 §14), a `SubWorkflow` node to a child run (`run.child-runs-multi-agent-work`, File 04 §16). The executor, parallelism (`run.parallelism`, File 04 §15), cancellation (`run.cancellation`, File 04 §17.3), budgets (`run.budgets-limits`, File 04 §21), stuck detection (`run.stuck-detection`, File 04 §20.3), and the retry/reroute/branch run mechanics (`run.retry-reroute-branch`, File 04 §19) stay File 04's; this file's four-option retry vocabulary (§13.3) is a presentation over them. `run.automation-reuse` (File 04 §26)'s reuse-proposal trigger is the graduation path this file realizes (§11). The completion forgery guard (`run.termination`, File 04 §22) applies to a workflow run; the promotion forgery guard (§11.4) is its crystallization-time counterpart.

### 2.4 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces)

A `Tool` node invokes a `Capability` (`capability.declaration`, File 05 §3) through the one call pipeline (`run.call-pipeline`, File 04 §8.2). A workflow is exposed as an invocable operation through an adapter capability (`capability.adapter-capabilities`, File 05 §17.4), and the `workflow.*`/`template.*`/`macro.*` operations are canonical built-in capabilities (§15) registered through `capability.runtime-mutation` (File 05 §16.2). A node's `tool_allowlist` composes the node's `ToolSurface` (`surface.subsystem-surface-spec`, File 07 §5); a node may carry a `permission_tier_override`, and every node call is gated by `policy.effective-tier-resolution` (File 06 §4) like any call. A workflow run under an `Automation` honors the non-interactive park-and-notify posture (`automation.non-interactive-safety`, File 33 §11). Source approval (`policy.source-approval-flow`, File 06 §9) gates plugin-bundled and agent-authored reuse units. This file re-owns none of capability declaration, policy evaluation, or surface composition.

### 2.5 With Files 08, 09, 11 (Blocks, Artifacts, Version Graph)

A workflow body and its node outputs are `Block`s (`block.block`, File 08 §2.2); a composed body uses `children_block_ids` and the composition operations (`block.block-edge-block-graph`, File 08 §5; `cross-cutting/composition.md` realized). A `Workflow` definition is a `WorkflowTemplate`-kind `Artifact` (`artifact.artifact-kind`, File 09 §4.1) and a `Macro` is a `Macro`-kind `Artifact`; each `ArtifactVersion` is a sibling block (`artifact.version-creation`, File 09 §6.3) carrying `produced_by_run_id`/`produced_by_node_id`/`derivation_summary`. The definition is a versioned entity over the version graph (`version.chosen-model`, File 11 §1); a workflow-node completion is a `WorkflowNodeComplete` commit boundary (`version.version-op-summary-commit-boundary-set`, File 11 §5.2); a retry creates a version branch; provenance queries (`artifact.provenance`, File 09 §15) resolve a graduated workflow's origin run. Workflow validation produces `Validation`/`Critique` blocks (`artifact.validation-critique`, File 09 §14).

### 2.6 With File 13 (Context), File 15 (Settings), Files 20–21 (Storage, Sync)

A `Model` node names a default `ContextPolicy` (`context.context-policies`, File 13 §4); an instruction-fragment template loads into the `InstructionSources` region with its declared authority class (`context.instruction-sources-workspace-files`, File 13 §16). The template library's scopes and per-profile bundles ride the settings cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2) and profiles (`settings.profiles`, File 15 §7); every threshold and default is a setting (`settings.settings-over-constants`, File 15 §13). The workflow definition and library presets are durable and syncable substrate families (`storage.physical-layout-locality`, File 20 §8; `portability.what-replicates`, File 21 §5.3); the per-node output cache is device-local and never syncs (`infrastructure/sync.md` realized); a workflow definition is part of the `PortablePackage` (`portability.export-bundle`, File 21 §10).

### 2.7 With Files 25, 26, 33 and the per-surface specs

`worksurface.runtime-execution-declaration` (File 25 §9) lets a surface declare a default execution preset and a default DAG preset; that preset is a `Workflow`/`WorkflowGraph` in this file's library. `worksurface.consequences-for-later-specs` (File 25 §21) requires this spec to consume a surface's declared `surface_runtime`, default execution preset, and recorded `surface_contract_version`, and to pin a surface and its policies at save time the way routing does — this file honors that (§13.2). The command and slash rails (`controlrail.command-rail`, File 26 §6; `controlrail.slash-command-rail`, File 26 §8) invoke a workflow by identity; a `.atlas/commands/` custom command is a saved reusable operation in this layer. `automation.automation-object` (File 33 §6.2)'s `task_template` references a workflow by identity and parameterizes it at fire time; `automation.creation-and-graduation` (File 33 §15) graduates a successful run into an `Automation` that may reference a workflow this file owns. The per-surface specs (Files 27–32) own their node libraries and recording mechanics and realize their pipelines, curricula, classrooms, monitors, and saved commands as reusable units over this layer (§16).

### 2.8 Boundary

This file is the reuse layer. It owns the `Workflow`, the `WorkflowGraph` grammar, the parameter contract, composition, the `Macro`, the reusable-unit family, the `TemplateLibrary`, the creation-and-graduation paths, validation and simulation, invocation, and the surface-aliasing rule. It owns no executor, no run, no routing, no trigger binding, no capability or policy evaluation, no block or artifact or version mechanics, no context assembly, no settings model, no storage layout, and no per-surface node library. It feeds those layers; it does not replace them.

## 3. The `Workflow` Primitive and the `WorkflowGraph` Body

Anchor: `workflow.workflow`

### 3.1 Definition

A `Workflow` is the durable object binding a `WorkflowGraph` body to a fixed set of governing fields. The body is the reusable orchestration; the governing fields make it parameterizable, invocable, validatable, versioned, and library-managed.

### 3.2 The Field Set

A `Workflow` carries:

- `workflow_id` — stable identity; display name; optional description and the natural-language origin string when authored from one.
- `body` — the `WorkflowGraph` (§3.3): the typed node-and-edge graph that runs over the one executor.
- `parameters` — the typed parameter contract (§4): the declared slots a caller binds at invocation time.
- `context_kind` — the execution-graph context the body targets: `Workflow` (a general multi-step operation) or `Pipeline` (a predominantly data-processing graph). `Chat` and `AgentInnerLoop` are the executor's other context kinds and are not reusable library units; a saved chat topology becomes a `Workflow` when crystallized.
- `default_policy` — the default approval posture and capability-scope expectations a run of this workflow carries, declared over `policy.approval-policy-templates` (File 06 §12.4); the policy layer resolves the effective decision per node at run time.
- `declared_effect_envelope` — the workflow-level upper bound over the body's effects, derived from all nodes and sub-workflows: capability families, resolved or parameter-bound touched-resource expressions, permission floors, side-effect classes, replay classes, data egress, sandbox and isolation requirements, postconditions, and typed-confirmation requirements. Validation recomputes the envelope and rejects definitions that understate actual effects. The envelope feeds source approval, run preview, automation preauthorization, import diagnostics, and dependency analysis.
- `validation_policy` — the validators and completion checks a workflow run must satisfy to be considered successful (§12.3), selected over `artifact.validation-critique` (File 09 §14) and `run.termination` (File 04 §22).
- `output_contract` — what a successful run must produce and where the result is delivered (§12.4), composing the artifact, evidence, and event substrates.
- `kind_metadata` — kind-specific declarations the body's node kinds require (a per-node model-route pin, a surface binding, a sandbox profile by reference).
- `source` — the source taxonomy entry (§8.3): built-in, user-defined, plugin-bundled, or graduated-from-run, with its trust state.
- `enabled` — whether the workflow is available for invocation in its scope; archival and deprecation are enablement transitions (§9).

### 3.3 The `WorkflowGraph`

The `WorkflowGraph` is the canonical body grammar `run.execution-structure` (File 04 §5) declined to fix. It carries:

- `nodes` — a list of `WorkflowNode`s, each with a stable node id, a user-facing label, a `NodeKind` (§3.4), declared input bindings, and editor-canvas position metadata.
- `edges` — a list of `WorkflowEdge`s, each from one node to another, with an optional declarative `EdgeCondition` (`Always`, `OnSuccess`, `OnError`, a `DataPredicate` over a named output field, or a router-selected label). `EdgeCondition` keeps its control variants and uses the shared `DataPredicate` for its data arm. Edge conditions are declarative and data-level; a condition is never a closure.
- `input_node` — the node where invocation input and bound parameters enter.
- `output_nodes` — the nodes whose outputs constitute the workflow's result; `output_contract` (§12.4) is satisfied against them.
- `activation` per node — how a node's incoming edges trigger it: all incoming edges satisfied, or any one satisfied; and a node-level trigger rule (`all_success`, `one_success`, `none_failed_min_one_success`, `all_done`) governing how upstream outcomes gate the node. The trigger rules read the five typed upstream outcome classes a `Merge` node consumes (`Succeeded`, `Skipped`, `Failed`, `Blocked`, `Absent`; §3.4) through a coarser success/failed/done vocabulary: a *success* is `Succeeded`, a *failure* is `Failed` or `Blocked`, and *done* is any of the five terminal classes. `all_success` requires every contributing upstream to be a success, `one_success` at least one, `none_failed_min_one_success` no failure and at least one success, and `all_done` only that every upstream reached a terminal class. A node becomes ready when both conditions hold in conjunction — its edge quantifier (all incoming edges, or any one) and its trigger rule over those outcome classes. These map the multi-input join and fan-in semantics onto the declarative graph without an imperative scheduler.

The graph's structural composition is acyclic; a cycle in the node-and-edge structure is a validation error (§12.1). Bounded iteration is expressed by the `Loop` node kind (§3.4), which encapsulates repetition of a referenced sub-body (`sub_body: SubWorkflowRef`, §3.4) under a mandatory iteration guard; the node-level graph stays acyclic. This mirrors the structural-acyclicity rule of the block graph (`block.block-edge-block-graph`, File 08 §5.4).

The `DataPredicate` is the one declarative data-predicate taxonomy the graph's data-level conditions share, so a `Branch` (§3.4), an `EdgeCondition`'s data arm, and a `Loop`'s condition (§3.4) all decide by the same rules. Its variants are `Equals`, `NotEquals`, `Exists`, `LessThan`, `LessThanOrEqual`, `GreaterThan`, and `GreaterThanOrEqual`. Its operands are a named output field or a bound value under the §4.3 declared typed binding-and-substitution rule, never raw text. `Equals`, `NotEquals`, and `Exists` apply to any comparable typed value; the four ordering variants are valid only over finite numeric operands — a Boolean, a structured JSON value, a `NaN`, an infinity, or string collation is rejected at validation, and an `Int` is never silently normalized against a `Float`, so a mixed `Int`/`Float` comparison is forbidden rather than coerced. `Exists` decides presence: an absent referenced field is a decided `false`, never a failure — presence is the variant's whole subject. For every other variant, a missing referenced field or an operand type mismatch is a typed evaluation failure of the deciding node, never a consumer-defined or best-effort outcome.

### 3.4 The Closed `NodeKind` Catalogue

`NodeKind` is closed-canonical with the `Custom { namespace, name }` extension (`core.closed-canonical`, File 01 §6.16). Each kind maps to the execution unit (`run.execution-structure`, File 04 §5.2) it runs as:

- `Model` — a model step (`run.model-steps`, File 04 §13). Carries an optional model-route pin or `ModelProfile` reference (`model.model-profile`, File 16 §4), an optional instruction-fragment or model-request assembly reference, a default `ContextPolicy` (File 13 §4), a `tool_allowlist`, an optional `permission_tier_override`, and a role hint (`Normal`, `Router`, `Critic`, `Validator`). A router is a `Model` node with the `Router` role hint whose outgoing edges carry router-selected labels; there is no separate router node kind and no confidence-threshold layer — misrouting is recovered through the retry vocabulary (§13.3).
- `Tool` — a single capability invocation (`run.capability-execution`, File 04 §8). Carries the capability id and an arguments template whose placeholders bind from node inputs and workflow parameters (§4). The call passes the full pipeline and policy like any call.
- `Merge` — combines several upstream outcomes into one payload for a downstream node under a declared merge strategy. It consumes typed upstream outcomes (`Succeeded`, `Skipped`, `Failed`, `Blocked`, `Absent`) and declares whether each class is required, ignored, represented as a placeholder, collected as an error, or failed. Its fixed result is a provenance-preserving ordered envelope: the combined payload carries every consumed or skipped upstream input in declared upstream order, each tagged with its source node identity and typed outcome class, so the downstream node reads a deterministic, fully attributed combination. This `Merge` node envelope is distinct from a `Loop`'s `Merge` aggregation strategy, which folds per-iteration outputs through a `combiner_ref` (§3.4).
- `Branch` — routes input by a declarative `DataPredicate` (§3.3) over its input, for if/else flows without a model call. By default it selects exactly one outgoing edge; non-selected paths produce typed `Skipped { reason: BranchNotTaken }` outcomes, not failures.
- `Loop` — bounded iteration of a referenced sub-body, with a mandatory maximum-iterations guard (a setting, never an unbounded loop; `run.stuck-detection`, File 04 §20.3). Its `LoopKind` is closed: `Collection` (one iteration per element of a bound collection), `Count` (a bound integer count of iterations), or `Condition { predicate: DataPredicate }` (repeat until the shared `DataPredicate` (§3.3) holds). The sub-body is carried by reference, never inline: the node declares `sub_body: SubWorkflowRef` — the same reference-with-version-policy contract the `SubWorkflow` kind uses (`Pinned { workflow_version_id }` by default; `CurrentActive`/`LatestCompatible` only by the same explicit opt-in) — so all nested execution has one carriage model and the loop body participates in §5.2's reference-graph acyclicity, depth bounds, and floating-reference drift revalidation. The loop declares `iteration_bindings`: an item binding for `Collection`, or an index and an optional `state_binding` for `Count` and `Condition`. The referenced sub-body's input node receives those bindings as named typed inputs using the same binding mechanism as workflow parameters and node outputs; the `Collection` item type constrains the collection element type. Iteration is governed by a declared `failure_tolerance: LoopTolerance` and aggregates through a declared strategy (`Append`, `Merge`, `Reduce`, or a registered `Custom` combiner) into a versioned `LoopAggregateResult` that preserves per-iteration identity for provenance. The kind semantics and condition evaluation, the failure tolerance, the aggregate result, and the combiner are fixed below.
- `SubWorkflow` — nests another `Workflow` as a node (`run.child-runs-multi-agent-work`, File 04 §16). The reference is a `SubWorkflowRef` with an explicit version policy: `Pinned { workflow_version_id }` by default, or `CurrentActive` / `LatestCompatible` only by explicit user choice or source-approved policy. The referenced workflow's inputs map to the node's inputs and its outputs to the node's outputs. Recursion is bounded (§5.2).
- `Programmatic` — deterministic orchestration that controls a bounded sub-structure and calls model steps only where judgment is needed (`run.programmatic-execution`, File 04 §14). Carries a registered programmatic-agent identity and its configuration; it never bypasses the capability pipeline, policy, ledger, or version boundaries.
- `Custom { kind, payload }` — a node kind registered by a surface or plugin through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2). The data processor registers its `data.parse.*`/`data.transform.*`/`data.validate.*`/`data.output.*` nodes here; the GUI surface registers its action nodes. A `Custom` node kind must register a declaration with owner namespace, source and trust, schema version, input and output schemas, parameter-binding points, execution-unit mapping, required capability scope and effect envelope, touched-resource summary, `replay_class`, `preview_mode`, postconditions, cancellation/killability behavior, concurrency classification, sandbox requirements, availability predicate, and import/export identity. A `Custom` node may not introduce a parallel executor; it composes the one execution model.

**Loop iteration kinds and condition evaluation.** `Collection` and `Count` iterate a finite, known extent fixed before the loop runs. `Condition` evaluation is a post-iteration repeat-until: each iteration runs the sub-body over the current state, its output and state are committed, and only then is the `DataPredicate` evaluated over that committed iteration output and state; the loop repeats while the predicate is unsatisfied and stops when it holds. The predicate may name only output fields the sub-body's output contract declares, together with the current `state_binding`; naming an undeclared field is a validation error (§12.1), not a runtime miss. State advancement is explicit: after a successful iteration, the child output field the node declares as its state source becomes the next iteration's `state_binding` value, threading state across iterations. Reaching the maximum-iterations bound without the predicate becoming true is a typed `LoopConditionUnsatisfied` failure of the loop node — never a success and never a silent stop. A failed iteration that failure tolerance absorbs neither advances the state nor satisfies the predicate: the prior committed state stands, and the loop proceeds only while the bound and the tolerance still permit. Each iteration runs as a child run whose `ChildRunSpawned` records the matching zero-based `iteration_index` (`ledger.entry-kind-catalogue`, File 10 §4.1).

**Loop failure tolerance.** `failure_tolerance: LoopTolerance` is `FailFast` (the default — the first tolerable iteration failure fails the loop node), `ToleratedCount(n)` with `n > 0`, or `ToleratedPercent(p)` with `p` in `1..=100`. Zero-valued `ToleratedCount(0)` and `ToleratedPercent(0)` are non-canonical duplicates of `FailFast` and are rejected at validation, so each intent has exactly one spelling. `ToleratedPercent` is valid only for `Collection` and `Count`, where the denominator is known before the loop runs; on `Condition` it is a validation error. The tolerated allowance is `floor(total × p / 100)`, and the loop fails when `failed_count > allowed`. Only an ordinary typed iteration `Failed` outcome is tolerable: a `Parked` iteration parks the parent (an approval or human decision is never silently consumed), cancellation propagates to the loop and its parent, an integrity failure fails the loop, and an iteration that completes without its required output fails. A combiner failure is a failure of the loop node itself and is never absorbed by tolerance. A loop succeeds only when its source is exhausted or its condition is satisfied, its failures are within tolerance, its aggregate is committed, and its output contract is satisfied; any of these unmet is a typed loop-node failure.

**The `LoopAggregateResult`.** Aggregation yields a versioned `LoopAggregateResult`: an ordered list of per-iteration records — each carrying the zero-based iteration index, the child `run_id`, the typed terminal outcome, the output reference when one is present, a safe failure reference when the iteration failed, and a `tolerated` flag — plus the iteration counts, the tolerance actually consumed, the terminal reason, and, for `Merge` and `Reduce`, the combined output. Tolerated failures are always represented in the record (nothing silent): a caller inspecting the result sees every failed-but-absorbed iteration. The schema is versioned so later revisions extend it compatibly.

**The loop combiner.** The aggregation strategy resolves a `combiner_ref: Option<RegisteredCombinerRef>`. A `RegisteredCombinerRef` is a namespaced declaration pinned to an immutable version or content snapshot — never a mutable name — registered through the proposal-first mechanism (`capability.runtime-mutation`, File 05 §16.2). Its declaration specifies the ordered input and output schemas, the `Reduce` accumulator schema and its initializer (a missing initializer is a typed empty-source failure, never a silent default), the deterministic-replay class, the effect envelope and policy requirements, the cancellation and failure behavior, and the source and trust identity. The validator matrix binds strategy to `combiner_ref`: `Append` carries no combiner (`combiner_ref` absent), `Merge` and `Reduce` require one, and a `Custom` strategy carries no separate `combiner_ref` because its own registration owns the combination. Combination runs in ascending iteration-index order. A runtime registration, trust, or policy failure of the combiner is a typed loop-node failure. The combiner's declared effects fold into the workflow's derived `declared_effect_envelope` (§3.2), so a loop never hides effects its combiner performs.

### 3.5 Rule

- A `Workflow` carries exactly the governing fields above; its body is a `WorkflowGraph`, and the graph runs over the one executor with each node mapped to a File 04 execution unit.
- The `NodeKind` set is closed-canonical-plus-`Custom`; a new node kind is a registered extension over an existing execution unit, never a new runtime.
- The node-and-edge structure is acyclic; iteration is the `Loop` node's bounded sub-body, carried as `sub_body: SubWorkflowRef` (§3.4), never inline; an unbounded loop, a missing or unresolvable loop sub-body, or a structural cycle is a validation error.
- A workflow's `context_kind` is `Workflow` or `Pipeline`; the executor's `Chat` and `AgentInnerLoop` context kinds are not library units.
- The declared effect envelope must cover all node effects; validation fails when it understates the body.

### 3.6 Boundary

File 04 owns the executor and the per-node execution-unit semantics; File 16 owns model profiles; File 13 owns context policies; File 05 owns the capabilities a `Tool` node invokes; the per-surface specs own their `Custom` node libraries. This section owns the body grammar that binds them.

## 4. Parameterization and the Parameter Contract

Anchor: `workflow.parameters`

### 4.1 Definition

The parameter contract is a `Workflow`'s (or other reusable unit's) declared set of typed parameter slots. It is the typed surface a caller fills at invocation time, and the only surface through which fire-time, invocation-time, or instantiation-time values enter the body. A reuse unit with no parameters is a fully fixed operation; a parameterized unit is a family of operations sharing one body.

### 4.2 The Parameter Slot

Each parameter slot declares: a name; a type (string, number, boolean, enum with allowed values, a typed object or array, a resource reference such as a file, block, dataset, or url, or a credential reference); an optional default value; an optional constraint (range, length, pattern, or membership) expressed declaratively so it serializes, syncs, and replays (`settings.settings-over-constants`, File 15 §13's declarative-constraint discipline); whether the slot is required; a sensitivity class (`Public`, `Sensitive`, `Secret`; `block.sensitivity`, File 08 §9); an authority class for slots that carry instruction text (`context.authority-classes`, File 13 §2.3); and a human-readable description and optional argument hint.

A resource-reference slot may declare multiple input modes (a pasted id, a pasted url with an extraction rule, or an interactive pick from a list) so the same slot serves direct binding and interactive entry. A credential-reference slot resolves to a vault reference (`security.secret-vault`, File 22 §5), never an inline secret.

### 4.3 Binding and Substitution

- A caller binds values to declared slots only. Binding occurs at invocation (§13), at fire time when an `Automation` references the workflow (`automation.run`, File 33 §10.2), or at instantiation when a content template is applied. The bound values are validated against the slot types and constraints before the body runs; a missing required value, or a value failing its constraint, produces a typed validation error, never a best-effort run.
- A bound value substitutes into the body only at declared substitution points: a `Tool` node's arguments template, a `Model` node's `PinnedModelSelection` (`automation.automation-object`, File 33 §6.3.1), instruction-fragment or model-request assembly references, a `Branch` predicate's operand, a `Loop`'s collection or bound, a `SubWorkflow`'s parameter map, or a content template's slot. Substitution targets the parameter by name; it never interpolates raw caller text into prompts, capability arguments, policy inputs, or undeclared instructions. This is the workflow counterpart of the raw-payload-interpolation rejection (`automation.run`, File 33 §10.2).
- A node may reference an upstream node's output as an input binding (a named output field of a prior node). Upstream-output references and parameter slots are the two binding sources; both are typed and resolved before the node runs.
- Security-sensitive fields are never bindable by an arbitrary caller override: the executable body and the node-implementation reference are part of the definition, not a parameter; a caller parameterizes inputs, not the operation's code or capability identity. A `Secret`-class bound value is redacted in events and run history and is held transiently, never persisted to the durable record (`block.sensitivity`, File 08 §9; `automation.persistence`, File 33 §18.3).

### 4.4 Pinning Versus Parameterizing

A workflow definition pins the operation (its node kinds, capability ids, edge structure, and the `PinnedModelSelection`s and policies it was authored or graduated with) and parameterizes the inputs. Pinning makes a reuse unit reproducible: a later run does the same operation. Parameterizing makes it general: a later run does it on different inputs. This is the same pin-versus-parameterize split `automation.automation-object` (File 33 §6.3) fixes for an automation's pinned `task_template`; an `Automation` pins the operation at save time and binds its parameters at fire time. Pinning is a reproducibility snapshot, not an authority freeze: at run time the current registry, source trust, policy, and security rules revalidate the pinned operation, and a later stricter policy wins.

### 4.5 Rule

- Values enter a reuse unit only through declared, typed parameter slots; binding is validated before the body runs; substitution targets declared points by name, never raw interpolation.
- A reuse unit pins its operation and parameterizes its inputs; a caller cannot rebind the executable body, a capability identity, or a security-sensitive field through a parameter.
- All slot constraints are declarative; sensitivity and authority classes are declared per slot; credential slots are vault references.

### 4.6 Boundary

File 13 owns instruction authority for instruction-bearing slots; File 22 owns the vault for credential slots; File 08 owns block sensitivity; File 05 owns the capability arguments a `Tool` node's template fills. This section owns the parameter contract and the binding-and-substitution rule.

## 5. Composition and Sub-Workflows

Anchor: `workflow.composition`

### 5.1 Composition Forms

A reusable unit composes in three ways:

- **Sub-workflow nesting.** A `SubWorkflow` node embeds another `Workflow` as a unit (§3.4). The parent references the child through `SubWorkflowRef`, pinned to a workflow version by default. The parent maps its inputs to the sub-workflow's input node and reads its outputs from the sub-workflow's output nodes. The sub-workflow runs as a child run (`run.child-runs-multi-agent-work`, File 04 §16) with its own context policy, tool surface, budget, and output contract; its result returns through the declared merge path. This is the canonical way a large operator reuses smaller operators without copying their bodies.
- **Workflow-as-operation.** A saved workflow is exposed as an invocable operation through an adapter capability (`capability.adapter-capabilities`, File 05 §17.4) so a `Tool` node, an agent's tool surface, a command-rail entry, or an `Automation` can invoke it by identity. The adapter delegates to the workflow executor; the workflow itself remains a distinct primitive, never a capability declaration (`capability.explicit-rejections`, File 05 §19). The agent reaches an exposed workflow through the standard discovery and borrow path (`surface.late-loading-runtime-discovery`, File 07 §7), gated by policy.
- **Body-level block composition.** A workflow body and its constituent step blocks compose through the one block pool (`block.cross-surface-interoperability`, File 08 §12) and the composition operations (`block.block-edge-block-graph`, File 08 §5; group, ungroup, reorder, flatten). A composed body references its parts by block id; editing a part creates a sibling version (§9). Cross-installation copy uses the copy-versus-materialize choice (`portability.export-bundle`, File 21 §10): a copied workflow references library units by identity, a materialized export embeds them.

### 5.2 Bounded Recursion and Cycle Safety

- Sub-workflow nesting — a `SubWorkflow` node's reference and a `Loop` node's `sub_body` alike — is bounded by a maximum composition depth (a setting; `run.budgets-limits`, File 04 §21 composes per-stage budgets). A nesting that would exceed the depth, or that would re-enter the same workflow beyond a configured bound, is rejected at save time and at run time, mirroring the recursive-trigger cycle guard (`automation.eligibility`, File 33 §8.5).
- The sub-workflow reference graph — every `SubWorkflowRef`, whether a `SubWorkflow` node's reference or a `Loop` node's `sub_body` — must be acyclic; a workflow that transitively contains itself is a validation error (§12.1). The structural-acyclicity rule applies across nesting, not only within one body.
- `CurrentActive` and `LatestCompatible` sub-workflow policies are explicit floating-version opt-ins. Each run records the resolved child version and a drift notice when it differs from the version present at parent save time. Before executing a floating reference, the runtime revalidates the parent `declared_effect_envelope` against the resolved child envelope. If the child exceeds the parent envelope, the run records an `EffectEnvelopeDrift` event — the registered `Custom { namespace: "workflow" }` kind §17.2 declares, carrying the parent and referencing-node identity, the resolved child version and version policy, the declared and actual envelopes, the typed exceeded dimensions, and the bounded drift summary — and parks for user review. Pinned references are fixed at save time and need only ordinary validation.

### 5.3 Rule

- Composition is sub-workflow nesting (a child run), workflow-as-operation (an adapter capability), or body-level block composition; a workflow never embeds another's body by copy when reference suffices, and never becomes a capability declaration.
- Nesting depth and self-re-entry are bounded by settings; the sub-workflow reference graph is acyclic.
- Sub-workflow references are version-pinned by default; floating references are explicit and revalidated for effect-envelope drift before execution.

### 5.4 Boundary

File 04 owns the child run a `SubWorkflow` node spawns; File 05 owns the adapter capability mechanism; File 08 owns block composition; File 21 owns the copy-versus-materialize export. This section owns the composition forms and their safety bounds.

## 6. The `Macro` Reusable Unit and Macro-to-Workflow Conversion

Anchor: `workflow.macro`

### 6.1 Definition

A `Macro` is a recorded, parameterized, replayable action-sequence reusable unit — the low-code, recorded form of a workflow body. It is the artifact a user produces by recording a sequence of surface actions (browser actions in the Web surface, desktop actions in the GUI Control surface, or other surface action sequences), parameterizing the variable parts, and saving it for replay. A `Macro` is a `Macro`-kind `Artifact` (`artifact.artifact-kind`, File 09 §4.1) and participates in the one `TemplateLibrary` and the one parameter contract.

### 6.2 The Macro Contract

- A macro carries an ordered sequence of recorded steps, each naming an action and its operands; a typed parameter set with per-parameter variability and sensitivity flags (a recorded credential is a `Secret`-class parameter, a vault reference, never inline); a target-surface specification; and per-step failure and timeout handling. Replay binds the parameters (§4) and substitutes them into the variable step operands; the substitution is into declared variable slots only.
- A macro is replayed through its owning surface's executor (the Web or GUI Control surface), which resolves the recorded steps against the live environment with the surface's robustness strategy. This file owns the macro-as-reusable-unit contract (identity, parameters, library membership, versioning, success-rate metadata, conversion); the recording mechanics, the element-selector model, and the replay resolution stay the per-surface specs (Files 28 and 31).
- A macro carries reuse metadata over its versions — execution count, last execution, and success rate — used by the library for quality ranking (§10) and by the graduation path (§11) as evidence.

### 6.3 Macro-to-Workflow Conversion

- A recorded macro converts into a `Workflow` by node conversion: each recorded action becomes a `Tool` or `Custom` action node, the sequence becomes a chain of edges, and the macro's parameters become the workflow's parameter slots. The result is a `WorkflowGraph` the user edits in the workflow editor — adding `Branch`, `Loop`, `Merge`, and `Model` nodes, parameterizing further, and composing sub-workflows. This is the canonical "record me doing the task once, then let me generalize and schedule it" path.
- Conversion is non-destructive: it produces a new `Workflow` whose provenance links to the source macro (§11.5); the macro remains a reusable unit in its own right.
- A data pipeline is a `Workflow` of `context_kind` `Pipeline`; per the cross-surface reuse rule (§16), a pipeline is surfaced in the macro/reuse library as a saved data operation. "A pipeline is a macro" is realized as: both are reusable units in the one library; a data pipeline's body is a `WorkflowGraph`, and the library treats it uniformly with recorded macros.

### 6.4 Rule

- A `Macro` is a recorded-action reusable unit owned by this layer's reuse machinery; its recording and replay mechanics stay the per-surface specs.
- A recorded credential is a `Secret`-class vault-referenced parameter, never inline; replay binds declared variable slots only.
- A macro converts into a `Workflow` by node conversion, non-destructively, with provenance preserved.

### 6.5 Boundary

Files 28 and 31 own macro recording, the element/selector model, and replay resolution; File 09 owns the `Macro` artifact kind; File 22 owns the vault. This section owns the macro reusable-unit contract and the conversion path.

## 7. Templates, Instruction Packs, and the Reusable-Unit Family

Anchor: `workflow.template-family`

### 7.1 The Reusable-Unit Family

The reuse layer treats `Workflow`, `Macro`, and content/instruction templates as one family sharing the library, parameter contract, promotion path, and versioning/sharing machinery. Content/instruction templates are the non-executable kinds:

- **Document and artifact templates** — reusable parameterized artifact bodies (a report skeleton, a lesson or rubric shell, a slide-deck scaffold). The template's content carriage and rendering stay `artifact.artifact-kind` (File 09 §4) and the owning surface; this file owns its library membership, parameter slots, and promotion.
- **Prompt and instruction-fragment templates (`Skill`)** — reusable instruction fragments loaded into a model request. A `Skill`/`InstructionFragment` is a distinct named-instruction primitive (`agents/domain-architecture.md`; `GLOSSARY` "Procedure → Skill"), carried as a `block_type` block (File 08) and an `InstructionFragment` artifact kind (File 09 §4.1), and loaded into the `InstructionSources` region with its declared authority class (`context.instruction-sources-workspace-files`, File 13 §16). This file owns its participation in the one library, its parameter slots (template variables in the body), its promotion from repeated use, and its versioning/sharing; it re-owns no context assembly and no instruction authority.
- **Workspace scaffolds** — reusable starting-point file sets a new workspace copies (`workspace.materialization`, File 24). This file owns the scaffold's library membership; the workspace spec owns materialization.
- **Style templates** — named format/style instruction fragments applied when context matches. This file owns library membership and parameterization; instruction assembly (`context.instruction-sources-workspace-files`, File 13 §16) owns their application and matching, and Memory (File 14) may learn and propose the underlying style signals but owns no applied-instruction object.

### 7.2 The Boundary With Workflows

A `Workflow` is executable: its body runs over the executor and produces outputs. A content/instruction template is applied: its body is rendered, loaded, or copied into a target. The two are distinct kinds of reuse, unified only by the library and the reuse machinery. A `Skill` is never a `Workflow` and a `Workflow` is never a `Skill`; a workflow node may *reference* a skill as an instruction source, and a skill may *describe* a workflow, but they remain distinct primitives.

### 7.3 Rule

- The reuse layer owns the unified library, parameter contract, promotion, and versioning/sharing for the whole reusable-unit family; the content and application of each non-executable template kind stay its owning file.
- A `Skill`/instruction fragment is a distinct primitive from a `Workflow`; neither subsumes the other.

### 7.4 Boundary

File 09 owns the artifact kinds; File 13 owns instruction loading and authority, including style-template application and matching; File 14 may learn and propose the underlying style signals; File 24 owns scaffold materialization. This section owns the family's shared reuse machinery and the workflow-versus-template boundary.

## 8. Identity, Versioning, and Source

Anchor: `workflow.identity-versioning-source`

### 8.1 Identity and the Versioned Entity

- A `Workflow` (and every reusable unit) has a stable identity assigned at first save; the identity survives edits, retitling, scope promotion, and graduation. Other units reference a workflow by this identity — a `SubWorkflow` node, an adapter capability, an `Automation`'s `task_template`, a surface's default execution preset.
- A reusable-unit definition is a versioned entity: a `WorkflowTemplate`-kind (or `Macro`-kind, or `InstructionFragment`-kind) `Artifact` (`artifact.artifact-kind`, File 09 §4) whose content carries the body, over the block pool (File 08) and the version graph (File 11). Editing a unit creates a sibling version (`artifact.version-creation`, File 09 §6.3; `block.edit-semantics`, File 08 §6.2); the history is inspectable, the prior version remains addressable, and a unit is reconstructable. No private workflow table is introduced (`atlas3-core/CONSTRAINTS.md` §12); the `dag_configs`/`dag_presets` persistence is the shared substrate File 20 realizes.
- A `Workflow` definition carries a schema version so the storage layer can normalize an earlier saved-format definition on load (`artifact.artifact`, File 09 §3.2's schema-version discipline; `cross-cutting/artifacts.md`'s migration-hook pattern).

### 8.2 Version Branches and Reproducibility

- A reusable unit's version history is a branch in the one version graph; a retry of a workflow run, an edit of a definition, and a fork of a unit are version branches (`version.chosen-model`, File 11 §1). Switching to a prior version brings back that body; branches are permanent and explorable.
- A run records the exact `(workflow_id, workflow_version)` it executed, plus the pinned operation snapshot (§4.4), so a historical run reconstructs against the version it consumed (`version.snapshots`, File 11 §14), and a later definition version does not silently change a past run's behavior. A run against a different version surfaces a typed reproducibility notice, as a capability invocation does across versions (`capability.version`, File 05 §13.4).

### 8.3 Source Taxonomy

A reusable unit names its source, mirroring `capability.capability-source` (File 05 §9.1):

- `Builtin` — shipped with the application as a built-in preset.
- `UserDefined { scope }` — authored or saved by the user at conversation, workspace, or global scope.
- `Plugin { plugin_id, plugin_version }` — bundled in a plugin's workflow/template library (§10.3).
- `GraduatedFromRun { run_ref }` — crystallized from a successful run (§11).

Plugin-bundled and graduated-with-agent-authorship units register through the proposal-first source-approval path (`policy.source-approval-flow`, File 06 §9) and carry the trust state their source confers; trust influences the effective policy of the unit's runs at invocation, never the stored definition (`capability.trust-source-approval-flow`, File 05 §9.2).

### 8.4 Rule

- A reusable unit has stable identity and is a versioned entity over the block pool and version graph; edits create sibling versions; no private table.
- A run records the exact unit version and the pinned operation snapshot; historical runs reconstruct against the recorded version.
- A unit names its source; externally-sourced and agent-authored units pass source approval and carry trust.

### 8.5 Boundary

File 09 owns the artifact entity and version-creation; File 11 owns the version graph and snapshots; File 20 owns the physical persistence; File 06 owns source approval and trust. This section owns the reusable-unit identity, versioning, and source contract.

## 9. The `TemplateLibrary`, Scopes, and Source Precedence

Anchor: `workflow.library`

### 9.1 Definition

The `TemplateLibrary` is the one catalog of reusable units across all kinds, scopes, and sources. It is the discovery, scoping, precedence, and sharing surface the workflow editor, the command rail, the agent's discovery path, and an `Automation`'s authoring flow consume. There is no per-surface or per-kind parallel library.

### 9.2 Scopes and Layered Precedence

- A reusable unit is scoped `global`, `workspace`, or `user` — the settings-cascade scopes (`settings.scopes-profile-contexts-overlays`, File 15 §5.2), with the `user` scope profile-partitionable per that section's profile contexts. The library resolves a unit by identity through layered precedence so a more specific accepted source overrides a more general one without forking: workspace-scoped and user-scoped units override plugin and built-in defaults according to the configured source-precedence policy, the same layered-resolution discipline the canon uses for instruction files (`workspace.instruction-files`, File 24 §9) and capabilities (`capability.override-resolution-conflicts`, File 05 §14). A user may fork any built-in or plugin unit into a user- or workspace-scoped unit; the fork takes precedence, and the original remains addressable under its source namespace.
- Precedence selects which unit a name resolves to; it never upgrades source trust, instruction authority, permission floors, or policy treatment (`controlrail.slash-command-rail`, File 26 §8's precedence rule). A name collision surfaces source attribution or a disambiguation choice, never a silent winner; a plugin unit may not silently shadow a built-in or user unit, and policy may protect security-sensitive built-in names from shadowing.

### 9.3 Built-in, Per-Profile, and Plugin-Bundled Libraries

- The system ships built-in presets as starting points, not enabled operators: a simple single-`Model` workflow, a routed workflow, a draft-and-critique workflow, a parallel-brainstorm fan-out, a best-of-N propose-select workflow, and a data-pipeline starter. Built-in presets are templates until applied or saved; applying one is explicit.
- Active profiles may bundle default reusable-unit libraries (`settings.profiles`, File 15 §7): a developer-oriented profile may offer code-review, generate-tests, refactor-module, debug-error, and write-commit-message workflows; a researcher-oriented profile may offer literature-review, summarize-paper, and citation workflows; and so on. Profile selection creates an explicit acceptance record only for the exact profile-bundle version presented to the user. Later profile-bundle updates require source-approval review before new or changed executable units become enabled; profile updates must not silently expand a user's invocable library (§11.2).
- Plugins bundle workflow/template libraries declared in their manifest (a workflow entry naming a body file, a display name, a description, a category, and whether it is agent-invocable). On plugin activation, the bundled units register into the one library through the proposal-first source-approval path; on deactivation, they unregister. The plugin packaging mechanism is File 35 (Extension and Plugin System)'s; this file owns the workflow body a plugin bundles and its library membership.

### 9.4 Discovery and Sharing

- The library exposes lookup by identity (precedence-aware), by kind, by category, by scope, by source, and by text or semantic search over display fields; lookup honors enablement and availability. The agent discovers reusable units through the same discovery path it uses for capabilities (`surface.late-loading-runtime-discovery`, File 07 §7), gated by policy.
- A reusable unit is exportable and importable as self-contained data: a workflow exports as its body plus its parameter contract, its embedded or referenced sub-workflows, its referenced skills, and any referenced custom node definitions, through the one `PortablePackage` (`portability.export-bundle`, File 21 §10). Sharing across devices is sync (§18); sharing across installations is export/import. Lossy presentation-format exports pass through egress governance (`security.egress-governance`, File 22 §11).
- When import cannot resolve a required reference, the unit is created as `disabled` or `draft` with `UnresolvedReference { kind, source_id, requested_version_or_policy, reason }` diagnostics. It is inspectable and repairable, but not invocable until validation passes and source approval completes. Optional references may be omitted with typed placeholders only when the package marks them optional. Import never silently substitutes another node kind, skill, capability, profile bundle, or sub-workflow.

### 9.5 Dependency Projection

The library exposes a dependency projection derived from sub-workflow references, automation `task_template` references, workflow-as-operation adapter exposure, command and slash rail bindings, profile and library bundles, persistent template applications, and custom node-kind registrations. The projection is computed from canonical references, not stored as a separate dependency database.

Mutations that weaken a dependency — disabling, archiving, tombstoning, deleting, unaccepting, source-revoking, plugin-deactivating, failing import resolution, or unregistering a custom node kind — produce typed diagnostics listing affected workflows, automations, rails, bundles, and reusable units. Dangerous changes require typed-confirmation, create disabled unresolved references, or park affected dependents until the user repairs or accepts the change.

### 9.6 Rule

- There is one `TemplateLibrary`; every reusable unit lives in it, scoped and resolved through one layered precedence; precedence selects, never escalates trust or authority.
- Built-in presets are starting points; per-profile and plugin-bundled libraries are templates until explicitly accepted; no silent enablement.
- The library exposes precedence-aware discovery and self-contained export/import through the shared portability substrate.
- Dependency impact is surfaced through a projection over references; weakening a dependency is never silent.

### 9.7 Boundary

File 15 owns the settings scopes and profiles the library rides; File 24 owns the instruction-file precedence the library mirrors; File 35 (Extension and Plugin System) owns plugin packaging; File 21 owns the portable package; File 06 owns source approval. This section owns the one library, its scoping, precedence, discovery, and sharing.

## 10. Reuse Metadata and Quality Ranking

Anchor: `workflow.reuse-metadata`

### 10.1 Rule

- A reusable unit exposes derived reuse metadata computed from the execution ledger (File 10) and its run history (§17), never stored as durable definition fields: execution count, last execution, success rate against its validation policy (§12.3), recent failure modes, and average cost. These are projections (`core.projection`, File 01 §6.11), recomputed on read.
- The library uses reuse metadata for discovery ranking (a higher-success, more-recently-used unit ranks higher) and to inform the graduation proposal (§11) and the consolidation of overlapping units (§11.6). Ranking influences presentation order only; it never gates whether a unit may be invoked — policy decides that at invocation (`policy.effective-tier-resolution`, File 06 §4).
- A `Macro` carries its success-rate metadata over its versions the same way; a graduated workflow inherits the evidence of its origin run as initial metadata.

### 10.2 Boundary

File 10 owns the ledger and run records the metadata derives from; File 37 and File 38 render the ranking and reliability views. This section owns the derived reuse-metadata contract.

## 11. Creation and the Graduation Path

Anchor: `workflow.creation-and-graduation`

### 11.1 Creation Paths

A reusable unit is created through one of four paths, all producing the same versioned entity:

- **Graduation from a successful run — the primary path.** After a successful multi-step run, the runtime may propose crystallizing it into a `Workflow` (`run.automation-reuse`, File 04 §26; `codex_recommendations.md` §15.1's "workflow candidates"), derived from the run's structure: its execution graph (the nodes it ran, the capabilities it invoked, the model steps and their routes), the artifacts it produced, and the validation that passed. The proposal generalizes the run into a parameterized body — identifying the variable inputs as parameter slots and pinning the operation — for the user to review, edit, and accept. The proposal is generated from successful structure, not from text heuristics.
- **Natural-language authoring.** A capability parses an informal description ("a workflow that reviews a file, runs the tests, and drafts a commit message") into a candidate `WorkflowGraph` and parameter contract through a model-mediated or deterministic parser selected by the model-strategy and settings layers, presents the parsed structure for confirmation, and creates the workflow on acceptance. This file defines the parse-confirm-create contract; the parser is an implementation behind it.
- **Manual construction.** The user builds the body directly in the workflow editor — placing nodes, drawing edges, declaring parameters, attaching the policy/validation/output-contract fields, composing sub-workflows, and simulating runs (§12.2) before saving.
- **Promotion from a macro.** A recorded macro converts into a workflow (§6.3) for further editing.

### 11.2 No Silent Creation

- A reusable unit is never created or enabled silently. Graduation produces a proposal the user reviews and accepts; natural-language authoring requires explicit confirmation of the parsed structure; agent-initiated authoring (an agent crystallizing its own work) passes the proposal-first source-approval flow (`policy.source-approval-flow`, File 06 §9; `systems/17-agent-self-modification.md`'s no-silent-registration rule) and defaults to a `UserApproval` posture on first creation. This is the workflow counterpart of `automation.creation-and-graduation` (File 33 §15.2).
- Built-in, per-profile, and plugin-bundled units ship as templates and become enabled units only through explicit user acceptance, source approval that produces an accepted definition, or onboarding/profile selection that records acceptance for the exact bundle version shown to the user. Future changes to a profile bundle require review before new or changed executable units become enabled.
- Agent self-authoring reuses the same entity and governance; constraints such as a maximum number of active agent-created units are settings, not hardcoded limits.

### 11.3 Provenance

A graduated workflow preserves its origin: the producing run, the producing nodes, and a derivation summary describing what changed from the raw run to the generalized body (`artifact.version-creation`, File 09 §6.3's `produced_by_run_id`/`produced_by_node_id`/`derivation_summary`; `codex_recommendations.md` §14.2). Provenance queries (`artifact.provenance`, File 09 §15) resolve a unit's origin run, contributing capabilities, and version lineage. A macro-converted workflow links to its source macro; a forked unit links to its parent.

### 11.4 The Promotion Forgery Guard

A run may be crystallized into a reusable unit only when it carries real ledgered execution evidence: at least one recorded capability execution, committed artifact revision, committed workflow-node output block, or model-step output beyond plain text. A run with an empty execution trace, no produced outputs, or no recorded outcomes cannot graduate. This is the crystallization-time counterpart of the run-completion forgery guard (`run.termination`, File 04 §22; `ledger.forgery-guards`, File 10 §3.7): the system never promotes a hollow run into a reusable operator. The guard is deterministic and imposes no extra model call. The evidence floor is satisfied recursively, exactly as the run-completion floor is: a run whose action is delegated to child runs graduates when `grounded(run)` holds — direct action evidence, or a valid `ChildRunMerged(run, child)` edge (the child spawned by that parent, reached durable `Completed`, its output incorporated into the parent, the identities agreeing across the spawn, merge, and block entries, and the path captured in the parent's completion evidence) with `grounded(child)`. The recursion is bounded by the maximum child-run depth (`run.budgets-limits`, File 04 §21), not the composition depth (§5.2), with a visited set; a parent/child cycle is integrity corruption. As at the run floor, the transitive evidence clears only the generic anti-hollow bar — it is never a specific capability, artifact, validation, or output-contract match (`qc.completion-gate`, File 39 §14).

### 11.5 Editing and Re-Crystallization

Editing a unit creates a sibling version (§8). A later successful run of an existing workflow may propose a refinement to the workflow (a better default, an added recovery branch); the refinement is a proposed sibling version the user reviews, never a silent mutation. Re-crystallization preserves the version lineage.

### 11.6 Consolidation

The library may propose consolidating overlapping units — merging near-duplicate workflows or skills into one parameterized unit, or superseding a narrow unit with a broader one — as a reviewed proposal, never a silent merge; consolidation preserves the superseded units' history and updates references through the version graph. This realizes the curator/consolidation pattern over the canonical substrate.

### 11.7 Rule

- The four creation paths produce one versioned entity; graduation from a successful run is primary and is generated from successful structure.
- No unit is created or enabled silently; agent-initiated creation passes source approval; shipped units are templates until accepted.
- A run graduates only past the promotion forgery guard; provenance is preserved; edits and consolidations are reviewed sibling versions, never silent mutations.

### 11.8 Boundary

File 04 §26 owns the reuse-proposal trigger; File 06 owns source approval; File 09 owns provenance and version-creation; File 10 owns the ledger evidence the forgery guard reads. This section owns the creation-and-graduation contract.

## 12. Validation, Simulation, and Reliability

Anchor: `workflow.validation`

### 12.1 Validate-Before-Save

A reusable unit is validated before it is saved or enabled. The structural validator rejects a definition that is malformed: a cyclic node-and-edge structure, a node unreachable from the input node or unable to reach an output node, a reference to an unknown capability or model or node kind, an unbound required input, a `SubWorkflow` reference cycle, a `Loop` whose `sub_body` reference is missing or unresolvable, an unbounded `Loop`, a `Condition` loop whose `DataPredicate` names an output field the sub-body's output contract does not declare or whose operand binding is type-incompatible or applies an ordering variant to a non-finite-numeric or mixed `Int`/`Float` operand, a `LoopTolerance` that is zero-valued (a `ToleratedCount(0)` or `ToleratedPercent(0)` duplicate of `FailFast`) or a `ToleratedPercent` outside `1..=100` or applied to a `Condition` loop (no known denominator), a loop aggregation that violates the combiner matrix (an `Append` or `Custom` strategy carrying a `combiner_ref`, or a `Merge` or `Reduce` strategy missing one) or a `Reduce` combiner declared without an accumulator initializer, a parameter slot whose constraint is unparseable, or a `declared_effect_envelope` that understates the graph's derived effects. Structural errors block saving; non-blocking warnings (a referenced model not yet enabled) do not, so units can be authored before full environment setup. Reference-existence validation is scoped by version policy: every pinned `SubWorkflowRef`, and every `Loop` `sub_body` under any version policy, must resolve before the unit is saved — a pinned reference is fixed at save time (§5.2), and the loop sub-body clause above carries no version qualification. A floating reference on a `SubWorkflow` node may remain unresolved at save; its unresolved state is a non-blocking warning, and it must resolve and pass the §5.2 acyclicity, depth, and effect-envelope checks before the child executes. Validation runs in the editor and at registration, the same structural discipline `worksurface.registry` (File 25 §10.3) and `capability.capability-registry` (File 05 §12.3) apply.

### 12.2 Simulation and Dry-Run

A workflow can be simulated before it is enabled or scheduled: a dry-run executes the body against supplied or recorded inputs, using node-output reuse where available and dry-run-mode capability previews (`run.call-pipeline`, File 04 §8.2's `preview_mode`) where a node's effect should not be committed, and returns the predicted node outcomes, the parameter bindings, and the predicted result without committing external side effects. Simulation is the safe authoring and review surface; an `Automation` that references a workflow may simulate it before enabling (`automation.test_trigger`, File 33 §19.1).

Simulation is coverage-aware. Read-only and deterministic previewable nodes may execute under policy. A side-effecting node without usable preview mode returns `SimulationUnavailable` or `RequiresLiveExecution`; downstream nodes depending on its missing output become blocked, or estimated only from user-supplied recorded outputs. The simulation result carries per-node coverage metadata: executed, reused, previewed, estimated, unavailable, or blocked. A dry-run must not commit external side effects.

### 12.3 Validation Policy

A workflow's `validation_policy` declares which validators and completion checks a run must satisfy to count as successful, selecting among the existing validation substrate (`Validation`/`Critique` blocks, `artifact.validation-critique` File 09 §14; the completion-verification hook surface, `run.termination` File 04 §22; File 39's validators). A run that completes without satisfying its validation policy is recorded as a failed run, feeding the reuse metadata (§10) and any referencing automation's failure handling (`automation.failure-handling`, File 33 §13). The policy reuses the substrate; it defines no new validators.

### 12.4 Output Contract and Drift

- A workflow's `output_contract` declares what a successful run must produce (an artifact revision, a claim or report, a committed observation, a structured result) and how the result is delivered (a message into the target conversation, a write into the workspace, an emitted event, or a notification). A run that completes without satisfying its output contract is a failed run even if no node errored. The contract composes the existing artifact, evidence, and event substrates and introduces no new product type.
- A workflow may declare an output-drift check: a re-read-before-each-output parameter contract and a validator comparing the produced output against the declared constraints, flagging output that strays from the pinned parameters within a tolerance. This realizes the spec-lock-and-drift-detector pattern over the canonical validation substrate; it is a validation policy, not a new mechanism.

### 12.5 Reliability

A workflow's reliability — its success rate, its recurring failure modes, its cost profile — is derived from its run history (§10) and evaluated by File 40's harness, which this file's reliability metadata feeds. This file specifies the data contract a reliability evaluation consumes; the harness is File 40's.

### 12.6 Rule

- A unit validates structurally before save; structural errors block, warnings do not.
- A workflow can be simulated/dry-run without committing side effects before it is enabled or scheduled; simulation results expose coverage gaps instead of pretending unavailable side effects were previewed.
- The validation policy selects existing validators; the output contract names the product and delivery over existing substrates; a run that fails either is a failed run; drift detection is a validation policy, not a new mechanism.

### 12.7 Boundary

File 09 and File 04 §22 own the validators and completion checks; the Quality Control and Evaluation specs (Files 39 and 40) own the validator catalogue and the reliability harness; File 04 owns the preview modes simulation uses. This section owns the validate-before-save rule, the simulation contract, and the per-workflow validation/output declarations.

## 13. Workflow Execution

Anchor: `workflow.execution`

### 13.1 A Workflow Runs as a Run

Invoking a workflow executes its body as an ordinary `Run` over the one executor:

1. the invocation (§14) binds parameters (§4) and produces a `RouteRequest` (`controlrail.input-resolution`, File 26 §4);
2. routing materializes a `RunIntent`, respecting pinned fields and filling only unpinned ones (`routing.trigger-kinds-routing`, File 03 §2.1). The `RunIntent` never carries the workflow body: the workflow reference and bound parameters arrive on the `RouteRequest`; the `RunIntent`'s existing fields carry the pinned `model_route` and `tool_surface_strategy` and an `execution_entry` of `multi_step_agent` (or `surface_runtime` for a surface-bound body) under which the run takes the graph/workflow structure shape (`run.structure-shapes`, File 04 §5.3); the remaining operation state enters as run-state snapshots at File 04 §6 step 3 — neither the `RunIntent` field set nor the execution-entry set is widened;
3. execution proceeds as a `Run` (`run.run`, File 04 §2.3) over the executor, with each node running as its mapped execution unit (§3.4), under the run model, the policy layer, the ledger, and the version-commit boundaries.

There is no separate workflow runtime, session type, or background path (`run.explicit-rejections`, File 04 §28; `atlas3-core/TODO.md` §19.3). A workflow run fired by an `Automation` carries the non-interactive posture (`automation.non-interactive-safety`, File 33 §11); a workflow run invoked interactively resolves approvals interactively.

Nodes whose incoming edge conditions and trigger rules are satisfied become ready. Ready nodes may execute concurrently in topological waves subject to File 04's capability concurrency, resource ownership, cancellation, budget, and failure rules. Completion and presentation preserve deterministic graph order using topological position and stable `node_id`, even when physical completion order differs. The graph declares dependencies; File 04 schedules and executes.

### 13.2 Pinning at Save Time

A workflow definition pins the operation fields a run would otherwise recompute, so a later run is reproducible: the per-node `PinnedModelSelection`s (`automation.automation-object`, File 33 §6.3.1), the per-node context and compaction policies, the per-node tool allowlists and permission-tier overrides, the surface binding and recorded `surface_contract_version` (`worksurface.consequences-for-later-specs`, File 25 §21) where the workflow targets a surface, the sandbox profile by reference (`sandbox.contract`, File 23 §3), and the budget (`run.budgets-limits`, File 04 §21). Pinning is a reproducibility snapshot, not an authority freeze (§4.4): at run time the current registry, source trust, policy, sandbox availability, model availability, and security rules revalidate the pinned operation, and a later stricter policy wins. Workflow-global and per-workflow policy settings may grant or require approvals for the workflow's declared effect envelope, but they are File 06 policy records, not private workflow approval logic. This is the single realization, for all surfaces, of the pin-at-save rule each per-surface spec defers here and that `automation.automation-object` (File 33 §6.3) fixes for automation task templates.

### 13.3 Retry, Node-Output Reuse, and Partial Execution

- A workflow run reuses node outputs through `NodeExecutionFingerprint`, encoded with `CanonicalEncoding` (`core.canonical-encoding`, File 01 §6.15). The fingerprint includes at minimum `workflow_id`, `workflow_version_id`, `node_id`, the node-definition hash, node-kind declaration version, normalized bound parameters or redacted secret references, upstream output block ids and content hashes, relevant snapshot references for registry, settings, policy, model, world, and context state consumed by the node, resolved capability/model/provider versions, cache policy, and preview/replay mode. Non-deterministic nodes (any `Model` node) reuse a cached output only when explicitly requested by retry or when a deterministic-caching setting applies. The cache stores committed block references and safe summaries, never raw secrets; secret-bearing inputs are non-exportable, non-syncable, and may be non-cacheable by policy. The per-node output cache is execution state owned by the executor and is device-local (§18), never part of the definition.
- The retry vocabulary offers four scopes over a workflow run: this node only, this node and downstream (the default), the whole workflow, and from a chosen node. Each scope invalidates a set of cached node outputs, computes the cold set, and re-runs from there, reusing cached outputs for the unchanged upstream. Each retry is a version branch in the version graph (`run.retry-reroute-branch`, File 04 §19; `version.chosen-model`, File 11 §1); switching to a pre-retry version brings back the original output, and retry branches are permanent and explorable. The four-option retry vocabulary is a presentation over File 04's retry/branch run mechanics and File 11's branches; this file owns no new retry runtime.
- Partial execution — running a workflow from a chosen node with the upstream taken from a prior run's reused outputs — is the same mechanism: the cold set starts at the chosen node, and the upstream is read from reuse. This serves resumable multi-stage operations without a separate resume engine.

### 13.4 Failure and Recovery

A node failure produces a typed failure output; in-flight sibling nodes continue, downstream nodes that require the failed output are skipped or blocked, and the run records a partial-failure outcome rather than discarding completed work (`run.failure-in-parallel-work`, File 04 §15.3). A `Loop` node's iteration failures are governed by its declared `failure_tolerance` (§3.4) rather than this default: a tolerated iteration `Failed` outcome does not fail the loop and stays visible in the `LoopAggregateResult`, while an intolerable failure — tolerance exceeded, a `Parked` or cancelled or integrity-failed iteration, a missing required output, or a combiner failure — fails the loop node as a whole. Recovery is the run model's (`run.recovery`, File 04 §20.2) and the four-option retry. A workflow node may declare a per-node retry-on-failure policy over the canonical retry strategies (`provider.transport-level-retry-backoff`, File 17 §11; `run.error-handling`, File 04 §20); the policy declares attempts and backoff, never a hardcoded busy loop.

### 13.5 Rule

- A workflow runs as an ordinary `Run` over the one executor; each node runs as its mapped execution unit; ready nodes may run concurrently under File 04 constraints; there is no separate workflow runtime.
- A workflow pins its operation at save time and revalidates against current policy/registry/security at run time; later stricter policy wins.
- Node-output reuse, the four-option retry, and partial execution are presentations over the executor's caching and File 04's retry/branch mechanics; the node-output cache is device-local execution state.
- A node failure preserves useful work and recovers through the run model and retry; per-node retry is a policy over the canonical strategies.

### 13.6 Boundary

File 04 owns the executor, the run, retry/branch, parallelism, recovery, and budgets; File 11 owns the version branches; File 17 owns the retry strategies; File 03 owns the route the invocation produces; File 33 owns the non-interactive posture of an automation-fired run. This section owns how a workflow body executes over them.

## 14. Invocation and Workflow-as-Operation

Anchor: `workflow.invocation`

### 14.1 Invocation Paths

A workflow is invoked by identity through the shared rails and capability pipeline, never an out-of-band path:

- from the conversation, by reference or a natural-language request that routing resolves to the workflow;
- from the command rail or a slash command (`controlrail.command-rail`, File 26 §6; `controlrail.slash-command-rail`, File 26 §8), where a `.atlas/commands/` custom command or a library entry resolves to the workflow and collects its parameters through the elicitation contract (`controlrail.elicitation`, File 26 §13) when required parameters are unbound;
- by an agent, through the workflow-as-operation adapter capability (§5.1), discovered and borrowed through the standard path (`surface.late-loading-runtime-discovery`, File 07 §7);
- by an `Automation`, whose `task_template` references the workflow by identity and binds its parameters at fire time (`automation.automation-object`, File 33 §6.2);
- as a `SubWorkflow` node inside another workflow (§5.1).

Every invocation produces a `RouteRequest`/`RunIntent` and runs through §13; the user is an invoker whose direct invocation skips the agent's permission path but never skips policy floors, typed-confirmation, touched-resource checks, or ledger recording (`controlrail.input-resolution`, File 26 §4; `policy.effective-tier-resolution`, File 06 §4).

### 14.2 Parameter Collection

When an invocation does not supply all required parameters, the invoking rail collects them: the command and slash rails open a parameter-entry elicitation; a natural-language invocation may infer some bindings and elicit the rest; an automation binds from its declared parameters and trigger payload through declared slots only (§4.3). A workflow never runs with an unbound required parameter or an invalid binding.

### 14.3 Rule

- A workflow is invoked by identity through the shared rails, the capability pipeline, or a `SubWorkflow` node; every invocation routes and runs through §13.
- Unbound required parameters are collected through the elicitation contract; a workflow never runs with an unbound required parameter or an invalid binding.

### 14.4 Boundary

File 26 owns the rails and the elicitation contract; File 03 owns routing; File 05 owns the adapter capability; File 33 owns the automation reference. This section owns the invocation-by-identity contract and parameter collection.

## 15. The `workflow.*`, `template.*`, and `macro.*` Capability Surface

Anchor: `workflow.capability-surface`

### 15.1 Closed Canonical Capabilities

The reuse layer exposes its operations as built-in capabilities declared per `capability.declaration` (File 05 §3), flowing through the standard call pipeline (`run.call-pipeline`, File 04 §8.2) and policy (File 06):

- `workflow.create(definition)` — create a workflow from a complete definition; `UserApproval`.
- `workflow.create_from_description(description)` — the natural-language authoring path (§11.1), parsing and presenting for confirmation; `UserApproval`.
- `workflow.create_from_run(run_ref)` — graduate a successful run into a proposed workflow (§11.1, §11.4); `UserApproval`.
- `workflow.update(workflow_id, patch)` — edit a definition, producing a new version (§8); `UserApproval`.
- `workflow.run(workflow_id, parameters)` — invoke a workflow (§14); the effective tier reflects the workflow's operation, `declared_effect_envelope`, and pinned scope, resolved per node by policy, not a blanket low tier.
- `workflow.simulate(workflow_id, inputs)` — dry-run a workflow without committing side effects (§12.2); `ReadOnly` with respect to durable state.
- `workflow.validate(definition)` — structural validation (§12.1); `ReadOnly`.
- `workflow.list(filter)` / `workflow.get(workflow_id)` / `workflow.get_runs(workflow_id)` — read the library, a definition, and run history (§9, §17); `ReadOnly`, `ConcurrencySafe`.
- `workflow.enable(workflow_id)` / `workflow.disable(workflow_id)` / `workflow.archive(workflow_id)` — enablement transitions; settings/registry writes.
- `workflow.delete(workflow_id)` — tombstone a definition and preserve history; `UserApproval`, escalating to typed-confirmation only when deletion has high-risk consequences (a unit other automations or workflows depend on, or hard-deleting history beyond tombstoning).
- `workflow.export(workflow_id)` / `workflow.import(package)` — self-contained export/import (§9.4); import passes source approval.
- `macro.convert_to_workflow(macro_id)` — node-conversion of a macro into a workflow (§6.3); `UserApproval`. Macro recording/replay capabilities are the per-surface specs'.
- `template.list(filter)` / `template.get(template_id)` / `template.apply(template_id, target, parameters)` — read and apply content/instruction templates over the one library; application delegates to the owning surface.

### 15.2 Rule

- The reuse capabilities are built-in declarations under the one registry, carrying the touched-resource and tier metadata their effects warrant; creating, editing, enabling, deleting, and importing are tier-gated; reading, simulating, and validating are `ReadOnly`.
- An agent invokes these capabilities like any other, subject to policy and the no-silent-creation rule (§11.2). A workflow exposed as an operation is an adapter capability over `workflow.run`, never a separate primitive.

### 15.3 Boundary

File 05 owns the declaration and registry; File 06 owns the policy gating; the per-surface specs own macro recording/replay and template application. This section declares the canonical reuse capability set.

## 16. Surface Aliasing and Per-Surface Reuse

Anchor: `workflow.surface-aliasing`

### 16.1 The Aliasing Rule

Every per-surface reusable-operation concern realizes as a reusable unit over the one library and the one executor, never a parallel mechanism. The surface contributes the domain-specific node kinds, default policies, and presentation; the reuse layer contributes the body grammar, the parameter contract, the library, and the execution.

- **Data pipelines** (Data Processor surface) are `Workflow`s of `context_kind` `Pipeline` whose bodies use the surface's `Custom` data node kinds (`data.parse.*`/`data.transform.*`/`data.validate.*`/`data.output.*`); they run over the one executor, edit in the one workflow editor, and live in the one library with a data category.
- **Notebooks** (Data Processor surface) are composed artifacts whose cells map to graph nodes; a notebook converts into a reusable pipeline and a pipeline renders as a notebook over the same underlying graph (the notebook↔pipeline convertibility). The notebook artifact and cell semantics are the surface's; the reusable-pipeline body is this layer's.
- **Curricula and classrooms** (Teacher surface) are reusable units: a curriculum is a parameterized reusable body that produces lessons; a classroom is a parameterized multi-agent topology (a `WorkflowGraph` of `Model`/`SubWorkflow` nodes with a director). The educational artifact kinds and the agent roles are the surface's; the reusable body and its parameterization are this layer's.
- **Coder saved commands** (Coder surface) — the `.atlas/commands/` custom commands with typed parameters and an agent or shell mode — are reusable units invocable from the rails (§14); a built-in `/build`, `/test`, or `/lint` is a built-in workflow preset.
- **Surface monitors and scheduled operations** are `Automation`s (File 33) whose `task_template` references a workflow this layer owns; the trigger binding is File 33's, the workflow body is this layer's.
- **System operation sequences** (System Agent surface) — script templates and saved system operations — are reusable units; a `RunMacro` or `SpawnChat`-from-template system action references a unit in this library.

### 16.2 Rule

- A per-surface reusable operation is a reusable unit over the one library and the one executor; the surface contributes node kinds, policies, and presentation, never a parallel engine, editor, or store.
- A surface's monitor or scheduled operation is an `Automation` referencing a workflow this layer owns; the trigger binding stays File 33's.

### 16.3 Boundary

The per-surface specs own their node libraries, artifact kinds, and recording/application mechanics; File 33 owns the trigger binding. This file owns the one body grammar, library, and executor they realize over.

## 17. Run History and Observability

Anchor: `workflow.observability`

### 17.1 Rule

- A workflow run is an ordinary `Run` recorded in the execution ledger (`ledger.execution-ledger`, File 10) with its `(workflow_id, workflow_version)` attribution and its per-node outcomes; run history — past runs, their outcomes, durations, produced artifacts, and per-node outcomes — is a projection over the ledger, never a parallel workflow-run table.
- A workflow exposes derived state computed from the ledger and run history (§10): its reuse metadata, its recent runs, its reliability, and its current version. These are projections, recomputed on read.
- This file specifies the data contract user-facing surfaces consume (the library browser, the workflow editor's run history, the reliability view, the execution monitor); it specifies no rendering. File 37 and File 38 render it.

### 17.2 Workflow Event Extensions

Workflow-specific definition, library, validation, simulation, graduation, and workflow-reference safety facts evaluated at execution time use File 10's `Custom { namespace: "workflow", name, payload }` extension mechanism. The canonical workflow namespace includes: `WorkflowCreated`, `WorkflowUpdated`, `WorkflowEnabledChanged`, `WorkflowArchived`, `WorkflowTombstoned`, `WorkflowValidationCompleted`, `WorkflowSimulationCompleted`, `WorkflowGraduationProposed`, `WorkflowGraduationAccepted`, `WorkflowGraduationRejected`, `WorkflowConsolidationProposed`, `MacroConvertedToWorkflow`, `TemplateApplied`, and `EffectEnvelopeDrift`.

`EffectEnvelopeDrift` is a workflow-reference safety fact, not a run lifecycle event: it records that a floating sub-workflow reference resolved to a child whose effect envelope exceeds the parent's declared bound (§5.2), evaluated at execution time before the child runs. Its payload carries the parent workflow id and version, the referencing `node_id`, the referenced child workflow id, the resolved child version id, and the version policy in force; the declared and actual effect-envelope hashes or references together with their bounded human-safe summaries; the comparison schema and its version; and `exceeded_elements` as a typed structure of the drifted envelope dimensions and their differences (never free-form strings). When the drift detail is bounded, the payload follows the same truncation discipline as a `ValidationReport` (`qc.validation-report`, File 39 §12.2): a `truncated` flag, the total/included/omitted element counts, and an externalized reference to the full detail. As a registered `Custom { namespace: "workflow" }` kind it declares its durability, sensitivity, retention, allowed cross-reference keys, and schema version per File 10's custom-kind registration (`ledger.custom-kind-registration`, File 10 §4.3).

Workflow execution itself remains ordinary run-ledger data with `(workflow_id, workflow_version)` attribution. Per-node commits remain `WorkflowNodeComplete` per File 11. This section declares workflow lifecycle, library, and workflow-reference safety events; it does not duplicate run lifecycle events.

### 17.3 Boundary

File 10 owns the ledger and run records; File 37 and File 38 own the editor, library browser, monitor, and reliability rendering. This section owns the observability data contract.

## 18. Persistence, Locality, and Portability

Anchor: `workflow.persistence`

### 18.1 What Is Durable, Computed, and Device-Local

- **Durable and syncable:** a reusable unit's definition — its identity, body, parameter contract, governing fields, source, and enablement — as a versioned entity (§8) over the block pool and version graph (Files 08, 11), realized as the shared persistence the storage spec (File 20) owns. A unit definition is a logical object that syncs across a user's devices (`portability.what-replicates`, File 21 §5.3) so the user's workflows and library follow them. Run history is durable ledger state (§17).
- **Computed / device-local:** the per-node output cache and any in-flight execution state. The node-output cache is device-local and never syncs (a per-device cache, cheap to rebuild); its loss across a restart is a rebuild, never a loss of a definition, a version, or history. This is the same durable-definition-versus-device-local-execution-state split `automation.persistence` (File 33 §18) fixes for automations.
- **Reconstruction:** a unit definition and its version history reconstruct deterministically from the durable substrate; the node-output cache rebuilds on demand.

### 18.2 Portability and Security

- A reusable unit is part of the `PortablePackage` (`portability.export-bundle`, File 21 §10): exporting carries the definition, its parameter contract, its referenced sub-workflows, skills, and custom node definitions, by identity or materialized per the copy-versus-materialize choice (§9.4). Importing re-resolves references and passes source approval; unresolved required references produce disabled or draft units with typed diagnostics (§9.4).
- A unit definition contains no raw secret: a credential-reference parameter and any vault-backed value are references (`security.secret-vault`, File 22 §5), never inline; raw secrets never sync, export, or materialize (`portability.sensitivity-egress`, File 21 §12). A workflow run that uses credentials or mutates the system records into the device-local hash-chained audit overlay (`ledger.hash-chained-audit-log`, File 10 §16.4) where the per-surface spec requires it.
- Version-tree-aware sync applies: two devices that edit the same unit produce sibling versions that both survive, with no last-write-wins (`portability.what-replicates`, File 21; `version.chosen-model`, File 11). Every hash a unit relies on is computed over a declared `CanonicalEncoding`, never physical storage bytes (`core.canonical-hash`, File 01 §7.14); this file defines no new canonical hash and inherits each from its owning file.

### 18.3 Rule

- A unit definition is durable, versioned, and syncs; the per-node output cache and in-flight execution state are device-local and rebuilt; run history is ledger-durable.
- A unit is part of the portable package; references re-resolve on import under source approval; no raw secret is part of a definition.
- Concurrent cross-device edits produce sibling versions; no last-write-wins; hashes are over a declared canonical encoding.

### 18.4 Boundary

Files 20 and 21 own storage, locality, sync, and the portable bundle; File 22 owns the vault and audit cryptography; Files 08 and 11 own the entity and version graph. This section owns the durable-versus-device-local split for reusable units.

## 19. Settings

Anchor: `workflow.settings`

Reuse behavior is configurable through `settings.setting-definition` (File 15), with agent exposure governed by `policy.agent-exposure-policy-settings` (File 06 §16.4). At minimum, settings must support:

- the default library scope for new units and the per-profile and per-workspace active libraries;
- the enabled built-in presets, the per-profile default-workflow bundles, and profile-bundle review and acceptance behavior for exact bundle versions;
- workflow-global and per-workflow policy override scopes for approval posture, trusted effect envelopes, and reusable approval defaults, resolved by File 06 policy;
- the source-precedence and name-collision policy (disambiguate versus prefer-by-scope) and whether plugin units may shadow built-in or user names;
- the maximum sub-workflow nesting depth and self-re-entry bound (a `Loop`'s `sub_body` counts against the same depth), the per-`Loop` maximum-iterations default, and the per-`Loop` default `failure_tolerance` and default aggregation strategy (authoring defaults resolved into the node's explicit fields before save, so a saved loop never carries an implicit tolerance or strategy at run time);
- the node-output-reuse policy (off, on-for-deterministic-nodes, on-with-explicit-retry) and the default retry scope (this-node, this-node-and-downstream, whole-workflow, from-node);
- the default per-node and per-workflow budgets and warning thresholds, the default per-node timeout, and the executor concurrency bound, composed with `run.settings` (File 04 §27), not duplicated;
- the simulation defaults (which node kinds use preview mode in a dry-run) and the validation-policy and output-contract defaults per surface;
- the graduation-proposal policy (when the runtime proposes crystallizing a successful run), the agent-self-authoring bounds (maximum active agent-created units, default approval posture), and the consolidation-proposal policy;
- the library discovery ranking inputs (success-rate, recency, frequency weights) and result caps;
- the export/import policy and the per-scope sharing policy.

Settings define intended variation; they must not become hidden hardcoded branches (`run.settings`, File 04 §27; `settings.settings-over-constants`, File 15 §13).

Per-node and per-workflow timeouts are configurable killability safety guards composed with File 04 cancellation and deadlines. They are not correctness conditions and must not decide semantic success or failure except by producing a typed timeout or cancellation outcome. Loop bounds are structural safety settings; concrete values are never canonical.

## 20. Explicit Rejections

Anchor: `workflow.explicit-rejections`

The following shapes are wrong for this layer:

- a parallel workflow engine, a parallel graph editor, or a parallel workflow store — there is one executor, one body grammar, one editor surface, and one library; a workflow runs as a `Run` over the one execution-graph model (`run.explicit-rejections`, File 04 §28; `atlas3-core/TODO.md` §19.3);
- a separate workflow runtime, session type, or background execution path — a workflow run is an ordinary `Run` distinguished only by its body and invocation;
- a parallel `workflows`/`templates`/`macros` table — a unit definition is a versioned entity over the block pool and version graph, realized as the shared `dag_configs`/`dag_presets` persistence (`atlas3-core/CONSTRAINTS.md` §12);
- treating a `Workflow` as a `Capability` or a `Skill` — each is a distinct primitive; a workflow is exposed as an operation through an adapter capability, never as a capability declaration, and a skill is an instruction fragment, never a workflow (`capability.explicit-rejections`, File 05 §19);
- a cyclic node-and-edge structure or an unbounded `Loop` — the structure is acyclic, iteration is the bounded `Loop` node, and a cycle or unbounded loop is a validation error;
- raw interpolation of caller input into prompts, capability arguments, policy inputs, or undeclared instructions — values enter only through declared, typed, validated parameter slots and substitute only at declared points;
- a parameter that rebinds the executable body, a capability identity, or a security-sensitive field — a caller parameterizes inputs, not the operation;
- a private `Approval`, `Human`, or `ManualDecision` node kind, including through `Custom` nodes — approval-required calls park through File 06/File 04, missing or ambiguous user input is collected through File 26 elicitation, and artifact review uses artifact review or validation state;
- silent creation, enablement, mutation, or consolidation of a reusable unit — every creation path requires explicit acceptance, agent-initiated creation passes source approval, and edits and consolidations are reviewed sibling versions;
- crystallizing a hollow run into a reusable unit — a run with no ledgered execution evidence cannot graduate past the promotion forgery guard;
- a unit that runs without satisfying its declared validation policy or output contract being treated as successful — such a run is a failed run;
- a per-node output cache that syncs or is part of the definition — it is device-local execution state, rebuilt on demand;
- last-write-wins on concurrent cross-device unit edits — both edits survive as sibling versions;
- a raw secret in a unit definition, export, or sync — credentials are vault references;
- a per-surface private library, editor, or executor for pipelines, notebooks, curricula, classrooms, saved commands, or macros — each is a reusable unit over the one library and the one executor;
- silently substituting an unresolved imported reference with an available "similar" reference;
- hardcoding any nesting depth, loop bound, retry scope, budget, timeout, ranking weight, or graduation threshold outside settings.

## 21. Consequences for Later Specs

Anchor: `workflow.consequences-for-later-specs`

- The **Extension and Plugin System** spec owns plugin packaging and the contribution-point registration of plugin-bundled workflow/template libraries; it must register bundled units into the one `TemplateLibrary` through the proposal-first source-approval path and the `Custom` node-kind mechanism, and must introduce no parallel workflow store or engine. A plugin contributes workflow bodies, custom node kinds, and content templates; this file owns their library membership and reuse semantics.
- The **MCP and External Integrations** spec owns the transport for externally invoked or externally bundled workflows and the remote node kinds an external connector contributes; it must register them as `Custom` node kinds and reusable units, gated by source approval, and introduce no parallel detection or execution.
- The **UI Shell** and **UI Customization** specs render the workflow editor canvas, the template-library browser, the parameter-entry form, the simulation view, the run-history and reliability views, and the macro recorder/converter; they consume the data contracts (§9, §12, §17) and must not make the presentation the definition or run truth.
- The **Quality Control and Validation** and **Evaluation and Benchmarking** specs own the validators a workflow's validation policy selects and the reliability harness its metadata feeds; they must integrate through the validation, completion-verification, and reliability substrates this file references, not a parallel workflow-validation pipeline.
- The **Telemetry, Logging, and Observability** spec consumes the workflow run history and reuse metadata projections; it must not introduce a parallel workflow-run store.
- The **Runtime Infrastructure and Lifecycle** spec orchestrates the registration and reconstruction of the library at startup over the storage lifecycle File 20 owns, and the device-local rebuild of the per-node output cache; it must persist no node-output cache across sync and place no parallel workflow executor.
- The **per-surface specs** (Files 27–32) realize their pipelines, notebooks, curricula, classrooms, saved commands, monitors, and system operations as reusable units over the one `TemplateLibrary`, contributing their `Custom` node kinds, default policies, and presentation, and introducing no parallel engine, editor, or store; their recorded macros convert into workflows through this layer, and their scheduled operations reference a workflow body through an `Automation`.
- **File 33 (Automation and Triggers)** is the fixed counterpart: an `Automation`'s `task_template` references a workflow this file owns by identity and binds its parameters at fire time; the trigger binding, scheduling, eligibility, non-interactive safety, and overlap are File 33's, the reusable body and its parameterization are this file's.

## 22. Canonical Rule Anchors

Anchor: `workflow.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `workflow.chosen-model`, `workflow.boundaries`, `workflow.workflow`, `workflow.parameters`, `workflow.composition`, `workflow.macro`, `workflow.template-family`, `workflow.identity-versioning-source`, `workflow.library`, `workflow.reuse-metadata`, `workflow.creation-and-graduation`, `workflow.validation`, `workflow.execution`, `workflow.invocation`, `workflow.capability-surface`, `workflow.surface-aliasing`, `workflow.observability`, `workflow.persistence`, and `workflow.settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
