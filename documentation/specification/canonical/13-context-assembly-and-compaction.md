# Context Assembly and Compaction

## Status

Canonical.

## Scope

This file defines:

- context assembly for every model-bound invocation, including routing, execution, validation, child runs, programmatic model steps, and completion checks
- the structured model request as assembly parts grouped into semantic regions
- per-part authority, sensitivity, source attribution, and instruction-boundary handling
- `ContextPolicy` and router context policy behavior
- budget management, overflow reporting, duplicate detection, and oversize input handling
- token counting as a provider/model-capability contract
- logical cache-marker candidate production
- compaction as the write-side counterpart to read-only assembly
- continuity summaries, virtual paging, context pressure signaling, events, persistence, settings, and explicit rejections

This file does not define:

- block schema, block kinds, block lifecycle states, or block commit validation; File 08 owns those
- artifact, evidence, claim, citation, or provenance identity; File 09 owns those
- execution ledger row schema, event dispatch mechanics, or hook execution; File 10 owns those
- version graph schema, `ContextOp` vocabulary, materialized-view reconstruction, or commit mechanics; File 11 owns those
- retrieval algorithms, indexing backends, entity extraction, or knowledge governance; File 12 owns those
- capability declaration schema, policy evaluation, approval flows, leases, or tool-surface composition; Files 05-07 own those
- routing decision semantics or `RunIntent`; File 03 owns those
- execution lifecycle, run status, cancellation, or recovery mechanics; File 04 owns those
- provider-specific tokenizers, provider wire formats, cache-control syntax, model selection, rate limits, or usage accounting
- storage schema, sync mechanics, UI layout, or exact settings precedence

## Source Resolution

This file resolves prompt construction, context windows, compaction, memory/context retrieval, authority separation, and model-request rendering material into one boundary: how runtime state becomes a model request.

Resolved design:

- Context assembly is a per-iteration read operation over canonical state; it does not mutate blocks, tasks, memory, or routing state.
- Assembly is region-based and part-based: regions provide ordering and budgets, while each included part carries its own source, authority, scope, sensitivity, and lifecycle facts.
- Compaction creates explicit durable outputs or lifecycle actions through existing block/version systems; it is not hidden prompt loss.
- Retrieval, virtual paging, and recall use canonical indexes and lifecycle filters rather than separate archive stores.
- The rendered model request must preserve instruction boundaries, source attribution, and provider-native callable declarations without collapsing all content into one system prompt.

## 1. Chosen Model

ATLAS3 has two cooperating context services.

`ContextAssemblyService` is read-only. It turns active runtime state into a structured model request for a specific invocation. It reads blocks, materialized views, retrieval outputs, tool-surface snapshots, instruction sources, memory outputs, world-state snapshots, settings, and provider/model descriptors. It never mutates blocks, lifecycle state, indexes, or versions.

`CompactionService` is write-side. It reduces active context by committing versioned operations through the block and version graph systems. It may drop, recover, mask, group, or consolidate content, but it does not hard-delete source content and does not bypass version history.

The services communicate through durable state and typed pressure signals. Assembly reports what fits and what overflows. Compaction decides, under policy, what should change. The next assembly sees the updated materialized view.

Every model-bound invocation uses `ContextAssemblyService`. There is no separate instruction assembler, router request assembler, per-surface private request builder, or ad-hoc concatenation path.

## 2. Model Request

### 2.1 Definition

A model request is the complete provider-bound input produced for one model invocation.

It may contain:

- model-request text content
- provider-native callable declarations
- provider parameters
- references to externalized content
- logical cache-marker candidates
- diagnostic notices

The model request is not equivalent to instruction text. Instruction text is too narrow because callable declarations may travel outside text, provider parameters are not model-request text content, and many assembly parts are not instructions.

### 2.2 Assembly Parts

The assembled request is a sequence of `AssemblyPart` records.

Each part must carry:

- `part_id`
- `region`
- `content_kind`
- `source_ref`
- `authority_class`
- `sensitivity`
- `inclusion_reason`
- budget estimate or count
- lifecycle visibility used during selection
- omission, redaction, or externalization metadata when applicable

`source_ref` points to the durable source when one exists: block, ledger entry, route record, capability declaration, provider descriptor, settings snapshot, file source, retrieval result, or synthetic runtime record.

### 2.3 Authority Classes

Authority is per assembly part.

Allowed authority classes:

- `governing_instruction`
- `user_instruction`
- `trusted_runtime_fact`
- `untrusted_source_data`
- `provider_native_callable_declaration`
- `diagnostic_notice`

Semantic regions declare default authority, but the default is only a fallback. A web-fetched tool result inside conversation history remains `untrusted_source_data`. A user-authored instruction source inside an instruction region remains `user_instruction`. A callable declaration remains `provider_native_callable_declaration` even if rendered near instructions.

Instruction-boundary markers render at authority transitions between adjacent assembly parts, not merely at region boundaries. External descriptions, retrieval snippets, tool outputs, and user-provided files are marked as data unless their source explicitly grants instruction authority.

### 2.4 Sensitivity

Every assembly part carries sensitivity metadata resolved from the source and policy layer.

Sensitivity governs:

- whether the part may be included for the target model/provider
- whether the part may be cached
- whether the part may be logged, snapshotted, or displayed
- whether redaction, summary, reference-only inclusion, or omission is required

Assembly must fail safely when policy cannot decide whether a sensitive part may be included.

## 3. Semantic Regions

Semantic regions are structural buckets used to budget and order assembly parts. They are not authority boundaries, storage tables, or frontend panes.

The canonical region set:

- `GoverningInstructions` - Atlas runtime instructions, policy notices, and non-user governing constraints
- `InstructionSources` - user, workspace, project, plugin, and profile instruction sources
- `CallableDeclarations` - primary tool schemas and callable declarations
- `RuntimeState` - route, run, task, world-state, capability-state, and policy-state facts
- `CurrentInput` - the triggering message, event, selected content, and directly attached inputs
- `ConversationHistory` - active materialized conversation blocks and continuity summaries
- `RetrievedContext` - retrieval results, knowledge entries, memory outputs, and source excerpts selected for this invocation
- `DiagnosticNotices` - budget warnings, omission notices, denial notices, and assembly diagnostics meant for the model
- `ReservedOutput` - reserved capacity for the model response, not rendered content

Profiles may add custom regions, but custom regions still emit ordinary assembly parts and obey the same authority, sensitivity, budget, and traceability rules.

Region order is policy-selected. The default should preserve cache-stable and semantically stable prefixes when useful, but users and profiles may choose alternate orderings. Alternate orderings are valid when recorded in the assembly snapshot and checked against provider/model constraints.

## 4. Context Policies

`ContextPolicy` is the fidelity and selection policy for an invocation.

Canonical policy families:

- `Full` - include all eligible active context that fits
- `Summarised` - prefer summaries, descriptions, and source excerpts over raw history
- `Minimal` - include only the required invocation frame and directly relevant state
- `Router` - assemble a routing frame for File 03
- `Custom` - user, plugin, workspace, or subsystem policy composed from the same primitives

Policies are configurable through settings and profiles. They may differ by invocation kind, model profile, conversation, workspace, subsystem, surface, capability family, automation, or user override.

Policies choose inclusion, ordering, budget allocation, summarization preference, retrieval scope, duplicate handling, cache-marker preference, and overflow behavior. They do not change source authority, sensitivity policy, capability approval rules, or routing semantics.

## 5. Router Context Assembly

File 03 defines routing semantics and `RunIntent`. This file defines how the model request for a router invocation is assembled.

A router context policy must include the full current triggering input unless the input cannot be carried directly; in that case assembly must externalize or reference the full input and include enough visible structure for the router to understand the request. The current user request must not be replaced by a summary as the normal path.

Router policies may include:

- active intent-thread and task state
- previous route records, route decisions, and route reasoning summaries
- router-generated intent summaries for prior user messages
- continuity summaries
- selected recent blocks, pinned blocks, attached blocks, or referenced blocks
- capability, surface, model, provider, and approval-state summaries
- workspace instruction files and instruction sources when the policy grants them relevance to routing
- retrieval results when an agentic router profile explicitly requests them

Router context is expected to stay cheap, but cheapness is achieved by policy design, summaries, provider caching, prechecks, retrieval, and optional agentic inspection. It is not guaranteed by pretending conversation length is irrelevant.

Router summaries are distinct from continuity summaries. Router summaries optimize future routing decisions; continuity summaries preserve work-line continuity for downstream model calls. A router policy may consume continuity summaries, but they are not the same object.

Router context policies are user-configurable. Valid implementations may offer compact routing, summary-rich routing, recent-history routing, pinned/reference routing, ambiguity-expanded routing, agentic inspect-and-route, or custom policies. All must produce durable route records per File 03.

## 6. Assembly Algorithm

Each assembly invocation proceeds in this order:

1. Resolve invocation kind, target model/profile, provider capabilities, active settings, and policy snapshots.
2. Resolve the semantic region set, region order, budget allocation, and default authority classes.
3. Gather candidate sources from instructions, current input, materialized conversation state, task/run state, tool surface, retrieval, memory, world state, policy state, and diagnostics.
4. Convert candidates into assembly parts with source references, authority, sensitivity, lifecycle visibility, inclusion reason, and estimated budget cost.
5. Apply sensitivity, policy, and capability gates.
6. Count or estimate request size through the token-counting contract.
7. Fit the request under the target budget by applying the active policy's priority and overflow rules.
8. Externalize, omit, summarize, or reference oversize content according to policy.
9. Produce logical cache-marker candidates when the target model/provider supports them.
10. Emit `AssemblyOutput` and record the snapshot reference required for replay and audit.

Assembly is deterministic for the same durable inputs, settings snapshot, provider/model descriptor, and policy snapshot.

## 7. Current Input and Oversize Handling

Current input has special protection because it is the user's immediate request.

The retention priority is:

1. minimal governing Atlas instructions required for safe operation
2. the current triggering input
3. direct attachments or selected sources referenced by the current input
4. active task/run state needed to answer the current input
5. optional instruction sources, retrieval, memory, history, and diagnostics

When the current input itself is too large to carry directly, assembly must preserve access to the full input by externalizing it as a referenced source, searchable file, source block, or equivalent durable object. The rendered request should include the most useful directly visible representation selected by policy, such as structural outline, top-and-bottom excerpts, extracted explicit instruction, or source map. Rejection is allowed only when the system cannot safely externalize, reference, or inspect the input.

Attachments follow the same principle. Large attachments become referenced, searchable, and readable sources rather than silent omissions. The model receives enough metadata to know what exists, how to request more, and what was not directly included.

## 8. Duplicate and Overlap Handling

Before dispatch or assembly, the system may detect when a pending input duplicates content already present in the active context.

Detection may use:

- exact content identity
- normalized text identity
- source identity
- large substring overlap
- structured selection identity
- semantic similarity when deterministic checks are insufficient and policy justifies the cost

Resolution choices must preserve user intent:

- include as a reference to existing context
- drop the duplicated span while preserving new instruction
- include anyway
- edit before sending
- apply a configured default with visible notice and undo

The decision is recorded with the triggering input. Duplicate handling must not mutate prior blocks, hide the user's new instruction, or bypass routing/ledger records. Timing-based auto-continue may be offered as a user-interface convenience, but correctness must not depend on elapsed time.

## 9. Budget and Overflow

Assembly treats the context window as a shared budget across all rendered parts and reserved output.

`BudgetReport` must describe:

- target model/profile and provider capability snapshot
- total budget, reserved output budget, and rendered input budget
- per-region allocation and usage
- omitted, redacted, summarized, externalized, and overflowed parts
- policy decisions that materially affected inclusion
- token-counting accuracy class
- cache-marker candidate summary

Overflow is non-destructive. Assembly reports pressure; it does not compact, delete, mutate, or silently discard durable content.

Budget values, warning thresholds, region floors, region ceilings, reserved-output strategy, and overflow behavior are settings/profile concerns. This file defines the required behavior, not numeric defaults.

## 10. Token Counting

Token counting is a provider/model capability consumed by assembly.

The model descriptor must expose enough information for assembly to determine:

- context window or equivalent request-size limit
- tokenizer identity or counting identity
- whether exact provider-native counting is available
- whether a compatible local estimator is available
- which request parts count toward which limits
- whether callable declarations, cached prefixes, images, files, or multimodal payloads have special accounting rules

Assembly may use exact counting, compatible local counting, or conservative estimation. The chosen accuracy class is recorded in `BudgetReport`.

Token counts must not be stored as unqualified block fields. Any reusable count is keyed by content identity, content version/hash, and tokenizer/counting identity. Counts for pending uncommitted input use content hashes or snapshot references instead of block ids.

Provider-specific tokenizer libraries, endpoint names, and model-family exceptions belong to provider/model specs, not this file.

## 11. Cache Marker Candidates

Assembly may produce logical cache-marker candidates because it sees the full model-request structure and stable prefixes.

A cache-marker candidate records:

- candidate boundary
- covered assembly parts
- source stability basis
- sensitivity eligibility
- provider/model capability snapshot used
- policy that requested the marker

Provider adapters decide whether and how candidates become provider-native cache controls. Assembly does not define provider syntax, minimum lengths, retention duration, billing behavior, or cache APIs.

Cache preservation is a strong default preference when it does not harm correctness, but it is not absolute. Users and profiles may choose orderings or inclusion policies that reduce cache efficiency. The system should surface the consequence when a policy meaningfully harms caching.

Sensitive or secret content is cache-ineligible unless policy explicitly allows caching at the appropriate sensitivity level.

## 12. Compaction

Compaction reduces active context by committing versioned operations. It is not prompt trimming, hidden deletion, or an assembly side effect.

Canonical compaction policy families:

- `DescriptionDriven` - select and compact using block descriptions, structure, and source metadata
- `FullSummarisation` - create summaries over larger spans when raw content cannot remain active
- `IncrementalSummarisation` - update existing continuity summaries as new spans age out
- `VirtualPaging` - drop active visibility while preserving searchable recall through the standard retrieval path
- `SimpleTruncation` - remove lowest-priority active visibility only when policy explicitly allows it
- `Custom` - user, workspace, plugin, or subsystem policy composed from the same operations

Compaction may use model steps, deterministic selectors, retrieval, block descriptions, and validators. Any model-generated summary must preserve source links and sensitivity constraints.

Compaction operations must be revision-safe. A compaction pass declares the view revision it read and fails or rebases safely if the view changed before commit.

## 13. Virtual Paging

Virtual paging is a compaction policy, not a separate archive store.

`context.archive` applies `Drop` to the target blocks, removing them from active assembly. `context.recall` applies `Recover`, restoring them to active assembly.

Because dropped blocks are excluded from default active retrieval, a VirtualPaging policy configures its conversation namespace or retrieval profile to include `Active`, `Recovered`, and `Dropped` lifecycle states for recall/search performed by that policy. Retrieval results must surface lifecycle metadata so the agent can distinguish archived material from active material.

Virtual paging introduces no new lifecycle state, no parallel retrieval mechanism, and no private archive database.

## 14. Continuity Summaries

Continuity summaries preserve semantic continuity when raw blocks leave active context.

A continuity summary should preserve:

- the user's goal and wording where materially important
- decisions and rationale
- constraints, assumptions, and open questions
- pending tasks and commitments
- important evidence and source references
- what was omitted, summarized, or externalized

Continuity summaries are durable blocks linked to the compacted source blocks. They may be superseded incrementally as work continues. They are included by policy like any other context source and remain subject to authority, sensitivity, and budget rules.

## 15. Context Pressure

Context pressure is the typed coordination boundary between execution, tool surfaces, retrieval, provider handling, and compaction.

Pressure may be caused by:

- assembly overflow
- provider rejection
- budget warning
- tool-surface saturation
- retrieval result expansion
- user or automation request for compaction

The context layer responds through policy. It may request tool-surface shrink, run compaction, externalize large inputs, ask the user, or report that no safe reduction exists. Execution coordinates retries and cancellation; it does not own compaction choices.

Time-based triggers are optional user-configured conveniences, not correctness mechanisms and not defaults. Event-driven and state-driven triggers are preferred.

## 16. Instruction Sources and Workspace Files

Instruction sources may come from user settings, workspace files, project files, plugin metadata, committed `InstructionSource` blocks, or runtime policy.

`ATLAS.md` is the default workspace instruction-file name. The name, lookup order, enablement, and inclusion policy are settings. When a resolved workspace instruction file is active, it participates in `InstructionSources` with `user_instruction` or other policy-resolved authority, source attribution, sensitivity metadata, and budget governance.

File 12 may index the same file as knowledge for retrieval and provenance. Indexing does not by itself grant instruction authority; instruction inclusion is decided by this file's policy.

## 17. Tool-Surface Coordination

Callable declarations consume context budget.

File 07 owns surface composition and loading. This file owns how the resolved surface enters the model request, how much budget it consumes, and how context pressure is reported back to the tool-surface layer.

Under pressure, assembly may request shrinkage, deferred loading, borrowable-catalog reduction, or reference-only descriptions according to File 07. Tool-surface shrinkage must not remove a callable that the execution contract requires unless policy explicitly permits reroute, pause, or failure.

## 18. Capabilities

Context assembly and compaction expose capabilities through the canonical Capability Registry.

Capability families should cover:

- inspecting the current budget report and assembled structure
- dry-running assembly for pending input
- listing omitted, redacted, externalized, or overflowed sources
- triggering compaction under the active policy
- masking, dropping, recovering, pinning, protecting, archiving, and recalling context sources
- changing context policy or compaction policy through settings-governed paths

Exact declarations, permission tiers, touched-resource expressions, preview behavior, leases, and approval rules belong to Files 05 and 06. Write-like context capabilities must declare touched resources and revision preconditions.

## 19. Events, Ledger, and Snapshots

Context events are `Custom { namespace, name, payload }` extensions registered through File 10 unless a later File 10 revision promotes a cross-cutting kind.

Expected event families:

- assembly completed
- budget warning
- context pressure observed
- duplicate or overlap detected
- compaction started, completed, failed, or low-yield
- continuity summary updated
- context source externalized, omitted, redacted, dropped, recovered, or recalled
- cache-marker candidates produced
- router context assembled

Durable records must reference assembly snapshots rather than storing raw prompt dumps by default. A snapshot stores enough to reconstruct what was sent: part ids, source refs, policy snapshot, provider/model descriptor identity, budget report, omission/redaction metadata, sensitivity-safe hashes, and rendered content references where retention policy allows.

Transient streaming and UI inspection are not the source of truth. The ledger, block graph, version graph, and referenced assembly snapshots are.

## 20. Persistence and Settings

Durable state includes:

- context and compaction policy selections
- continuity summary blocks
- compaction commits
- source externalization records
- assembly snapshot references required for replay, audit, or debugging
- duplicate-handling decisions tied to the triggering input

Computed state includes:

- rendered model requests
- token counts and estimates
- budget reports
- overflow lists
- cache-marker candidates
- provider-adapter-specific request forms

Settings must cover:

- context policy by invocation kind
- router context policy
- region order and region budget allocation
- current-input and attachment overflow behavior
- duplicate detection and resolution defaults
- token-counting strategy
- cache-marker candidate behavior
- compaction policy and compaction triggers
- virtual paging lifecycle-filter behavior
- instruction-file lookup, enablement, and inclusion
- sensitivity handling and snapshot retention
- whether time-based convenience triggers are enabled

Settings use File 15's model: durable global/workspace/conversation scopes, active profile context and profile layers, plus non-durable invocation overlays for run, automation, evaluation, or per-call overrides. Subsystem, surface, and capability-family variation is represented by namespaced setting keys and constraints, not by inventing additional durable scopes.

## 21. Explicit Rejections

The following shapes are wrong for this layer:

- mutating blocks, indexes, lifecycle state, or versions during assembly
- treating compaction as hidden prompt trimming
- treating overflow as permission to silently drop user content
- replacing the current user request with a summary as the normal routing path
- maintaining separate router, instruction, surface, or validator request builders
- assigning authority only at region level
- treating external tool descriptions, retrieval snippets, or web content as instructions
- hardcoding tokenizer libraries, provider endpoints, context limits, cache retention durations, ratio defaults, or numeric thresholds in this spec
- storing token counts as unqualified block fields
- making provider cache behavior part of canonical assembly semantics
- requiring a fixed region order solely for cache efficiency
- creating a virtual-paging archive store or lifecycle state
- using time-based triggers as correctness conditions
- making duplicate detection mutate prior blocks
- bypassing File 05-07 capability and policy contracts for context operations
- bypassing File 10/11 records for compaction, snapshots, or durable context history
- treating `ATLAS.md` or any workspace file as hidden prompt text without source attribution and policy control

## 22. Consequences for Later Specs

Later specs must follow these rules:

- memory specs must expose memory outputs as assembly sources with authority, sensitivity, budget, and provenance metadata
- settings specs must define exact scope precedence for context, router-context, compaction, instruction-file, duplicate-detection, and cache-candidate settings
- model strategy and provider specs must expose request-size, tokenizer/counting, cache, callable-declaration, and multimodal accounting capabilities without leaking provider specifics into this file
- storage specs must persist assembly snapshot references, continuity summaries, compaction commits, and externalized source records without creating parallel context tables
- UI specs must present context inspection, duplicate handling, overflow, compaction history, and source externalization as projections over the records defined here
- surface specs must declare their default context and compaction policies without creating private prompt assembly paths
- automation and workflow specs must reuse the same assembly, compaction, pressure, and snapshot contracts
- evaluation specs should measure context correctness, continuity preservation, duplicate handling, overflow recovery, cache effectiveness, and compaction quality
