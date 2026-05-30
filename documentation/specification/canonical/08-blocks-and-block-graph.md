# Blocks and Block Graph

## Status

Canonical.

## Scope

This file defines:

- `Block` as the universal, durable, immutable, typed, composable context-bearing carrier
- `BlockContent` shape — the three durable content variants (`Inline`, `External`, `Composed`)
- the canonical closed `BlockKind` catalogue plus the registered-extension mechanism
- block identity, addressability, content hashing, and cross-reference rules
- block immutability and the non-destructive edit/sibling-versioning model
- the staged-partial-write commit boundary that turns streaming events into committed blocks
- `BlockLifecycle` state (`Raw`, `Active`, `Masked`, `Dropped`, `Recovered`) as derived view-state, not block-stored state
- `PinState` (`Unpinned`, `Pinned`, `Protected`) as derived view-state
- `BlockGraph` as a typed directed graph over blocks; only the structural composition subgraph must be acyclic
- composition rules (`Composed` blocks reference children; sequence lives on the version, not on the block)
- sensitivity tagging (`Public`, `Sensitive`, `Secret`) at block and per-field granularity, and the projection independence it enables
- the boundary between `Block` (durable structured content) and `Event` (live coordination signal)
- the boundary between `Block` and `Message` (the transcript anchor that points at one primary block, which may be composed)
- cross-surface interoperability — one block pool, surface-specific projections
- per-block scope (`run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule`) and the rules for scope promotion
- the capability ↔ block declaration linkage (`output_block_kinds` from `capability.output-kinds` (File 05 §17.2) draws from this catalogue)
- the persistence contract — what is durably stored, what is computed, what is reconstructable
- settings dimensions consumed by block rendering, expansion, sensitivity-redaction, and retention

This file does not define:

- the execution ledger row format — File 10 owns the ledger schema; this file specifies which block events flow through it
- the version-graph commit storage or version tree algorithms — File 11 owns version graph mechanics; this file specifies the commit boundary contract
- artifact lifecycle, claims, evidence-set membership, or provenance algorithms beyond the block-relation surface — File 09 owns those
- retrieval, indexing, or knowledge-base construction mechanics — File 12 owns those
- context assembly, compaction algorithms, or token-budget mechanics — File 13 owns those
- memory promotion, salience scoring, or memory lifecycle — File 14 owns those
- run lifecycle, the capability-call pipeline, or hook execution — File 04 owns those
- block-rendering UI choices (collapsible cards, syntax highlighting, hover states) — the future UI presentation and customization specs own those
- storage schema, sync, or import/export — File 20 and the future Sync, Import, Export, and Data Portability spec own those

## Source Resolution

This file resolves messages, artifacts, tool results, notices, attachments, summaries, groups, and committed model output into one boundary: the durable block model and composition graph.

Resolved design:

- Blocks are immutable durable content units; lifecycle, ordering, pinning, and visibility are versioned projection state around them.
- Messages, artifacts, evidence handles, memory content, tool calls, tool results, failures, summaries, and groups are block kinds or later entity layers over blocks.
- Events carry live/transient activity; blocks are created only when content is deliberately committed for audit, replay, context, or user inspection.
- The canonical kind catalogue is closed with a `Custom` extension path; subsystem and surface specs add specialized kinds through registration.
- Composition is explicit through parent/child/reference edges, not nested mutable message structures.
- Scope, sensitivity, provenance, and lifecycle metadata determine safe visibility and retrieval behavior.

## 1. Chosen Model

Anchor: `block.chosen-model`

ATLAS3 has one `Block` model and one `BlockGraph` over it. Every durable structured content the system produces — a user message, an accepted assistant turn, a tool call proposal, a tool result, a reasoning trace, a file attachment, a citation, a memory entry, a validation report, an artifact handle, a plan, an execution trace, a workflow step record, a structured observation, an evidence chain — is carried as a `Block`. The relations between blocks form the `BlockGraph`.

Some block kinds are also higher-level entities. A message, artifact, memory, evidence record, tool call, or validation may be represented by one primary block while still having specialized lifecycle, UI, management, and export behavior owned by its later spec. The block is the durable context carrier; it does not erase the entity-level meaning.

A `Block`:

- is immutable after creation: identity, kind, content (`Inline` payload, `External` reference, or `Composed` children list), parent, content hash, source attribution, and creation timestamp are fixed at the moment the block is committed and never change
- is typed: its `BlockKind` is drawn from the canonical closed catalogue (§3), with a `Custom { namespace, name }` extension for subsystem-, surface-, plugin-, or user-defined kinds registered through the same extension plane as capabilities (`core.extension-planes`, File 01 §6.14)
- is composable: a `Composed` block has no `Inline` or `External` payload of its own; it carries an ordered list of `children_block_ids` that resolve at read time, and the composition itself is what the block represents
- is durable: blocks persist across run boundaries, conversation archival, process restart, and version-graph rewrites; the only operation that destroys a block's storage is explicit user-initiated hard deletion
- is addressable: it has a stable `block_id` used by the version graph, the execution ledger, the event stream (`run.event-stream`, File 04 §23.2), capability invocations (`capability.invocation-record`, File 05 §11), policy events (`policy.approval-policy-templates`, File 06 §12), and every surface presentation (File 07)

A `Block` is not:

- a UI element — the same block may be rendered differently in the conversation interface, in the inspector, in a workspace panel, in a comparison board, in an artifact preview, or in a voice transcript without changing the block
- a row in any single store — storage and projection layers shape how blocks land on disk, but the canonical block model is independent of schema
- a transcript line — a `Message` in the transcript (`intent.message`, File 02 §3) is a presentation anchor over one primary block; that block may be `Composed` over attachments, mentions, tool calls, results, or other child blocks
- a live coordination signal — those are `Event`s on the event stream (`run.event-stream`, File 04 §23.2) and never carry the durable-history contract
- mutable — every observable change is a new block in the same pool, with the prior block preserved and linked by a typed edge

A `BlockGraph` is the typed directed graph formed by every registered block as a node and every structural or explicit edge as a labeled relation between blocks. The graph is:

- closed under canonical edge kinds (§5) plus registered extension edges
- acyclic only for the structural composition subgraph; reference, citation, validation, and knowledge edges may form cycles unless their edge declaration forbids it
- inspectable through canonical block-graph queries (closure by edge type, ancestor walks, sibling enumeration, content-addressed lookups)
- versioned in projection only: the `BlockGraph` itself does not change with view switches; what changes is which subset of nodes is `Active` for a given `ContextVersion`. The graph is a single immutable structure; lifecycle is per-version state over it
- the substrate for context assembly, retrieval, evidence chains, memory promotion, and cross-surface interoperability

There is no per-surface block registry, no per-capability private block format, no per-conversation isolated block pool, and no "events become blocks" silent promotion: every block enters the canonical pool through a declared producer (a capability commit, a user message commit, an inspector apply, a workflow node commit, an import) and is referenced through stable identity from that point.

`Block` supersedes any earlier vocabulary in source material that named the same primitive: "transcript block", "content block", "fragment", "chunk", "DAG node", "history entry", "node output", "session entry", "rich block", "typed block", "context entry", "memory row". Those words may persist as informal synonyms in surface vocabulary; the canonical noun is `Block`.

## 2. `Block`

Anchor: `block.block`

### 2.1 Definition

A `Block` is the universal durable context-bearing carrier. It carries typed structured content that the system reasons about across surfaces, executions, conversations, and time.

### 2.2 Required Fields

Every block must carry at minimum:

- `block_id` — globally stable identifier; never reused, never reassigned, never mutated
- `kind` — the `BlockKind` (§3); fixed at creation
- `content` — the `BlockContent` discriminated value (§4); fixed at creation
- `parent_block_id` — the primary causal parent (optional; null for genesis blocks like a fresh user message). The parent expresses the semantic "this block was produced in response to / inside the context of" relation. Closure under `parent` produces the block's causal lineage
- `producer` — typed reference to what produced the block: `UserMessage { conversation_id, user_id }`, `CapabilityCommit { capability_id, capability_version, invocation_id }`, `RouterEmission { route_id }`, `InspectorApply { inspector_lens, user_id }`, `WorkflowNode { workflow_id, node_id }`, `Import { source_kind, source_ref }`, `Consolidation { policy_id, source_block_ids }`, `Subsystem { subsystem_id, reason }`
- `origin_run_id` — the `Run` (File 04) under which the block was committed; null when committed outside a run (user message, manual import, inspector apply outside a run)
- `conversation_id` — the conversation the block was committed under, when applicable; null for blocks committed under workspace or global scope without a conversation anchor
- `created_at` — full-granularity timestamp of commit
- `block_schema_version` — version of the canonical block record shape used to interpret `kind`, `content`, sensitivity maps, references, and hashing
- `content_hash` — SHA-256 over the block's canonical content representation (§4.5); fixed at creation
- `source_attribution` — typed source linkage to the File 05 capability declaration and the source instance when the block came from a sourced capability (`Builtin`/`Subsystem`/`Plugin`/`McpServer`/`Api`/`UserDefined`); null for user-produced blocks and for system-internal blocks
- `default_sensitivity` — `Public` | `Sensitive` | `Secret` (§9); fixed at creation, with per-field overrides expressible through `sensitivity_field_map`
- `description` — short structured natural-language description emitted by the producer at commit time (§10)
- `scope` — broadest visibility scope (§11): `run` | `intent_thread` | `task` | `conversation` | `workspace` | `global` | `reusable_policy_rule`

For `Composed` content, the ordered child list lives only inside `BlockContent.Composed { children_block_ids }`. Storage may index that list for query performance, but the canonical source of truth is the content payload, not a duplicate top-level field. Every other field is derived (lifecycle, pin state, sequence within a version), computed (token counts per tokenizer), or owned by adjacent layers (event linkage by the ledger spec, version membership by the version graph spec).

### 2.3 Boundary

The block defines durable substance. The version graph decides which blocks are active in any given view. The event stream (`run.event-stream`, File 04 §23.2) coordinates the streaming that may precede a block's commit. The ledger records the policy decision and capability execution that produced the block. None of those layers may invent new block semantics; they consume what this file defines.

The block model is wire-stable through `block_schema_version`, `BlockKind`, and `BlockContent` discriminators. Adding a new variant to either discriminator is a canonical-spec change, not a runtime registration — runtime registration of new kinds happens through the `Custom { namespace, name }` extension mechanism (§3.4), not by introducing new top-level enum variants. Storage and import flows must validate supported block schema versions and explicitly upgrade or reject unsupported versions; silent reinterpretation is invalid.

## 3. `BlockKind`

Anchor: `block.block-kind`

### 3.1 Closed Canonical Catalogue

Anchor: `block.kind-catalogue`

Every block declares its `kind` at creation. The canonical closed catalogue:

**Message and instruction kinds:**

- `InstructionSource` — durable instruction-source content such as workspace rules, user rules, instruction fragments, or committed policy notices. It is not the fully assembled model request.
- `MessageUser` — a user's transcript input. By default, the message text is one primary block; attachments, mentions, quoted prior blocks, and other structured parts are linked as children when structure is needed.
- `MessageAssistant` — an accepted assistant turn; typically `Composed` over final text plus tool-call, tool-result, reasoning, validation, or failure child blocks

**Reasoning kinds:**

- `ReasoningTrace` — the model's reasoning content (when the model exposes it and policy permits its retention); defaults to `Sensitive`

**Capability execution kinds:**

- `ToolCallProposal` — the structured arguments the executor parsed from the model's tool-call emission, committed before execution; carries the resolved capability id, version, arguments, and the policy decision reference
- `ToolResult` — the typed result returned by the capability after execution; may be `Inline` (small structured payload), `External` (large output stored as artifact), or `Composed` (a result that wraps several sub-results)
- `ToolDenial` — the typed denial record produced when policy blocks a proposed call (`run.denial-is-in-band`, File 04 §8.3 in-band denial); contains the policy reason, the lease/floor that fired, and the proposed payload reference
- `Failure` — a user-visible or context-relevant failed or skipped output. Carries `{ source, error_code, retryable, skipped_vs_failed, references }`. Capability execution failures use `Failure { source: capability }`; policy denials remain `ToolDenial`.

**Observation and evidence kinds:**

- `Observation` — a structured observation of the world (file content snapshot, accessibility tree snapshot, screenshot reference, status query result, browser DOM extract) committed for replay and policy revalidation (`run.call-pipeline`, File 04 §8.2 stale-state revalidation)
- `Evidence` — a structured evidence record supporting a claim, an output, or an action; carries citation references and the typed claim it supports (full evidence semantics belong to File 09)
- `Citation` — a structured reference to an external source (URL, document section, file range, prior block id, MCP resource); the durable lookup key for provenance

**Persistence-related kinds:**

- `KnowledgeEntry` - a curated knowledge-base content block. The block carries content, source references, sensitivity, scope, and description; mutable curation state such as tags, featured status, validation status, lifecycle, and last-reference statistics belongs to the knowledge-base entity layer.

- `Memory` — a memory entry promoted into durable cross-conversation knowledge; carries the salience and decay metadata (full memory mechanics belong to File 14)
- `Artifact` — a block whose content is a durable user-visible output (a file, a document, a chart, a notebook, a lesson, a code patch). May be `Inline` for small artifacts or `External` referencing artifact storage. Artifact identity, lifecycle, versioning, materialization, and export mechanics belong to File 09; this kind is the block-level handle.
- `FileAttachment` — a block referring to a file in the workspace; carries the path, mtime, size, content hash, and content-type; resolved against workspace state on read
- `SourceExcerpt` — a deliberately committed excerpt from a source block, file, document, web page, retrieval result, graph traversal, direct lookup, or manual selection. Retrieval chunks, embedding segments, and graph index nodes remain derived records unless intentionally committed as durable context.

**Planning and validation kinds:**

- `Plan` — a structured plan record (steps, subtasks, dependencies); used by execution and task promotion (`intent.task`, File 02 §6); plan revisions create siblings linked by `supersedes`
- `Validation` — a structured validation result (postcondition check, type check, lint result, evaluator score); referenced from runs and from the completion-verification hook surface (`run.termination`, File 04 §22)
- `Critique` — a structured critique or review record (a critic agent's review, a code-review comment, a quality-control note); semantically distinct from `Validation` because critiques are evaluative judgments rather than pass/fail checks

**Coordination kinds:**

- `Group` — a `Composed` block whose only purpose is to group children into a unit (user-defined groups, automatic groups for parallel calls, comparison-board groupings)
- `Consolidation` — a summary block produced by compaction that consolidates several prior blocks into a condensed view; references the consolidated blocks via the `consolidates` edge
- `ContextNotice` — a committed guardrail, hook, or system notice retained for audit, replay, or user inspection. Hook-injected guardrails, model-request transformations, and transient assembly content are `Event`s or request-assembly facts by default; they become blocks only when deliberately committed.

**Extension:**

- `Custom { namespace, name }` — specialized kind registered by a subsystem, surface, plugin, or user-defined extension. The `namespace` is a registered extension namespace (matching the capability sourcing taxonomy of `capability.capability-source` (File 05 §9.1)); the `name` is the kind id within that namespace. Custom kinds register through the same proposal-first registration mechanism that registers capabilities (`capability.runtime-mutation`, File 05 §16.2) and must declare:
  - allowed `BlockContent` variants
  - default sensitivity
  - whether the kind is allowed in transcript-anchoring positions
  - the canonical edge kinds the kind participates in

The closed catalogue is canonical for cross-cutting reasoning. The `Custom` extension is canonical for specialization. Every block at runtime belongs to exactly one of these — no block ever has an unparseable kind.

### 3.2 Kind Declaration

Each capability declaration (`capability.composition-fields`, File 05 §3.10) names the `output_block_kinds` it can produce. The names are drawn from this catalogue (closed canonical kinds and registered `Custom` kinds). A capability that emits an undeclared kind is an Explicit Rejection (§15).

### 3.3 Kind Composition Rules

Anchor: `block.kind-composition-rules`

The catalogue is not free-form. The following composition rules apply:

- `MessageUser` and `MessageAssistant` are transcript-anchor kinds. The transcript (File 02) renders these as message lines; the message line references a single block of one of these kinds, which itself may be `Composed` over children
- Message composition rules are defaults, not hard limits on later editing. A user or model may split a block into smaller sibling blocks, merge content into a new `Composed` block, group blocks, tag them through registered metadata, or edit them through the standard sibling-creation model; the original blocks remain immutable.
- `ToolCallProposal` and `ToolResult` always live as children of a `MessageAssistant` block (the turn that produced the call) or as standalone blocks in a non-conversation context (an automation run, an inspector-initiated capability invocation). They never appear as transcript-anchor blocks directly
- `Evidence` blocks must reference one or more `Citation`, `Observation`, or prior content blocks via `cites` edges; an evidence block with no supporting references is an Explicit Rejection (§15)
- `Artifact` blocks must reference a durable backing storage location through `External` content when their content exceeds the inline-size threshold; an oversized `Artifact` block with `Inline` content is an Explicit Rejection
- `Composed` blocks must reference at least one child via `children_block_ids`; a `Composed` block with no children is an Explicit Rejection
- `Group` blocks are by definition `Composed`
- `ReasoningTrace` blocks default to `Sensitive` and never default to `Public`
- `Memory` blocks default to `Sensitive` when their content originates from user-private context

These rules are enforced at commit time by the block commit validator (§8.2). Violations produce a typed `BlockCommitRejected` error that flows through the standard execution-failure path.

### 3.4 Custom Extension

A `Custom { namespace, name }` block kind is registered by a subsystem, plugin, or user-defined extension through a capability call (matching `capability.runtime-mutation` (File 05 §16.2) proposal-first registration). The registration declares:

- `allowed_content_variants` — which `BlockContent` variants the kind permits
- `default_sensitivity` — the initial sensitivity tagging for blocks of this kind
- `transcript_anchorable` — whether blocks of this kind may anchor a transcript message (default false)
- `permitted_parent_kinds` — closed list of `BlockKind`s a block of this kind may have as its `parent_block_id` (or `Any` for unrestricted)
- `permitted_child_kinds` — closed list of `BlockKind`s a `Composed` block of this kind may have in its `children_block_ids` (or `Any`)
- `default_edges` — the canonical edges (§5) blocks of this kind typically participate in; used by surface rendering and provenance queries
- `description` — human-readable description shown in the inspector and surface catalogues

Registered custom kinds persist in the registry (`capability.registered-capability`, File 05 §10) under the same registered-state envelope used for capabilities and follow the same source-trust narrowing rules (`policy.source-approval-flow`, File 06 §9). A custom kind cannot violate the composition rules above; if its declaration permits a structurally invalid combination, the registration is rejected.

### 3.5 Boundary

The kind catalogue defines what kinds of content the system reasons about. It does not define how those kinds are rendered, stored, or retrieved. UI, storage, and retrieval layers consume the catalogue; they do not extend it.

## 4. `BlockContent`

Anchor: `block.block-content`

### 4.1 Required Shape

Every block carries content as one of three discriminated variants. The variant is chosen by the producer at commit time and is fixed:

- `Inline { text }` — the block's content is a UTF-8 string carried directly in the block record. Used for short content where the cost of indirection exceeds the cost of inline storage (text fragments, structured JSON payloads under the inline-size threshold, tool arguments, citations, descriptions)
- `External { storage_ref, size_bytes, content_type, external_content_hash }` — the block's content lives outside the block record at a registered storage reference; the block stores only the reference. Used for large content (file attachments above the inline threshold, screenshot images, archive blobs, generated artifacts). The `storage_ref` names resolver kind, scope, identity, size, content type, and integrity hash where available. A remote URL is a citation/source reference unless the content has been captured into durable storage.
- `Composed { children_block_ids }` — the block has no content of its own; its content is the ordered concatenation (in the structural sense, not necessarily textual concatenation) of its children. `Composed` blocks are the canonical mechanism for representing structured-content blocks built from typed sub-parts: a `MessageAssistant` composed of text + tool calls + tool results, a `MessageUser` composed of text + attachments + mentions, an `Artifact` group composed of multiple file revisions

### 4.2 Inline-Size Threshold

Anchor: `block.inline-size-threshold`

The inline-size threshold is a settings dimension (§14). Block kinds whose declared `allowed_content_variants` include both `Inline` and `External` use the threshold to decide: content below the threshold is `Inline`, content at or above is `External`. The decision is made at commit time and is fixed for the block's lifetime; a block that was committed as `Inline` does not get re-encoded to `External` if the threshold later changes.

### 4.3 Composition Resolution

A `Composed` block resolves to its content by reading its `children_block_ids` in order and resolving each child recursively. The composition is shallow at the storage layer (the block stores only ids) and deep at the read layer (consumers see the resolved tree).

Resolution is a read-time operation. The composed block does not cache resolved content. If a child block is `Masked` or `Dropped` in the current `ContextVersion`'s view (§6), the resolution result for that child is the masked/dropped placeholder (a typed sentinel value with the child block's id, kind, and description but not its content). The composition operation does not re-fetch dropped children's content silently.

### 4.4 Cross-Reference vs Containment

Anchor: `block.cross-reference-vs-containment`

`Composed` blocks express **containment**: the children are parts of the composed block. A block may also **reference** other blocks without containing them (a `Validation` block references the blocks it validated; a `Critique` block references the block it critiques; a `MessageAssistant` references prior messages it responds to). References are expressed as typed edges in the block graph (§5), not as composition.

The distinction is load-bearing: removing a child from a `Composed` block (a hypothetical operation forbidden by §2) would change what the composed block is; removing a referenced block does not change what the referencer is, only what context it can resolve.

### 4.5 Content Hash

Anchor: `block.content-hash`

Every block carries a `content_hash` (SHA-256, 32 bytes) computed at creation over the block's canonical content encoding (a `CanonicalEncoding` per `core.canonical-encoding` (File 01 §6.15) and the global hashing rule `core.canonical-hash`), not over the physical storage bytes. The canonical content encoding covers:

- the block kind
- the content variant discriminator
- the inline payload or external reference descriptor
- composed child references, with child order preserved only where composition order is semantic (declared order-sensitive per `core.canonical-encoding` (File 01 §6.15))
- the `block_schema_version` that determines interpretation

`content_hash` is computed over the full canonical content and must not omit `Sensitive` fields: it is an identity and integrity hash, and stripping fields would make two materially different blocks hash identically and corrupt deduplication. (Raw `Secret` material never appears in inline block content per `secret.backend-boundary`, so there is nothing to strip.) When a redacted or rendered projection of a block needs its own hash, that is a separate `projection_hash` over the projection; a `projection_hash` must never be used for block identity, deduplication, or equality. Only `content_hash` carries identity.

The hash domain depends on the content variant:

- `Inline { text }` — hash of the canonical UTF-8 bytes of `text` plus the `Inline` discriminator
- `External { storage_ref, size_bytes, content_type, external_content_hash }` — hash of the canonical storage reference identity, size, content type, and external payload hash when known; future changes to external bytes do not silently change the block's identity
- `Composed { children_block_ids }` — structural hash over the child sequence of `(child_block_id, child_content_hash)` pairs, order-sensitive because composition order is semantic. Lifecycle changes (mask/drop/recover) do not change the hash; child content replacement does, because the composed block committed to those child identities and hashes

The hash supports cross-session and cross-device block deduplication (the storage layer may share storage for blocks with identical content hashes when structurally equal), materialized-view integrity verification, model-request-prefix cache correlation (`run.ledger-events-commits`, File 04 §23 cache-friendly ordering, `surface.cache-friendly-ordering` (File 07 §11.7)), and replay-time content equality checks. When `content_hash` is used for cross-device deduplication or content addressing, peers must use the same canonical content encoding version; hash equality across peers on differing encoding versions is not a correctness basis (`core.canonical-hash`). The hash is `NOT NULL` and immutable.

### 4.6 Boundary

The content shape defines what a block contains. The version graph decides which blocks are active. The storage layer decides how content is laid out on disk. The retrieval layer decides how content is indexed. None of those layers redefines the content shape; they consume it.

## 5. `BlockEdge` and the Block Graph

Anchor: `block.block-edge-block-graph`

### 5.1 Definition

A `BlockEdge` is a typed labeled directed relation between two blocks. Parent and composition relations are structural fields exposed as derived edge views; non-structural relations are explicit committed edge records. The set of structural edge views plus explicit edge records forms the `BlockGraph` over the block pool. Every explicit edge has:

- `edge_id` — stable identifier (optional in storage; derivable from `(from_block_id, to_block_id, edge_kind, sequence_in_kind)` when not separately persisted)
- `from_block_id` — the source block
- `to_block_id` — the target block
- `edge_kind` — the `BlockEdgeKind` (§5.2)
- `metadata` — typed metadata appropriate to the edge kind (an `attaches_to` edge may carry an offset; a `cites` edge may carry a span reference; a `derives_from` edge may carry a transformation summary); the metadata schema is part of the edge kind declaration
- `created_at` — when the edge was committed

Edges are committed at the same boundaries as blocks (§7.6). Edges are immutable in the same sense blocks are: an edge that needs to change is left in place; future changes commit new edges. The graph is append-only.

### 5.2 Canonical Edge Kinds

Anchor: `block.canonical-edge-kinds`

The closed canonical edge catalogue:

- `parent` — structural causal parent. The block's `parent_block_id` field is the canonical source of truth; graph queries expose it as a derived edge. Used by ancestor walks and conversation-context reconstruction
- `contains` — composition edge. A `Composed` block's `children_block_ids` are the canonical source of truth; graph queries expose them as ordered derived edges. Used by content resolution
- `supersedes` — non-destructive edit replacement. When a block is edited, the edit creates a new block and a `supersedes` edge from the new block to the prior. The version graph uses this edge to advance the "current" pointer. Closure under `supersedes` produces the version chain
- `derives_from` — derivation provenance. The new block's content was produced by transforming, summarizing, translating, or extracting from the source block. Used by provenance queries, evidence chains, and compaction
- `cites` — citation. Source: an `Evidence` or `Claim` block; target: a `Citation`, `Observation`, or external reference block. Closure under `cites` produces the evidence chain
- `witnesses` — observational provenance. The block's content was committed because the source block was observed (a screenshot triggered a UI action; a file-read triggered an edit). Used by replay and stale-state revalidation
- `references` — weak content reference. The block mentions, links to, or contextually depends on the target without containing or deriving from it (a `MessageAssistant` referencing a prior message it responded to; a `Plan` block referencing a `Task`). Used by surface presentation and cross-block navigation
- `follows_in_transcript` — strict transcript ordering. Source: any transcript-anchorable block; target: the prior transcript-anchorable block in the same conversation. Used by transcript reconstruction independent of timestamp ordering. The version graph determines the active transcript chain; this edge encodes the local "previous transcript message" link
- `consolidates` — compaction provenance. A summary or compaction block consolidates several prior blocks into a single condensed view. Source: the consolidation block; targets: the consolidated blocks. Used by compaction lifecycle and by surface displays that need to show "expand to original" affordances
- `materialized_by` — composition fallback. When a `Composed` block's children are hard-deleted (§6.6), the runtime may materialize the composed block's resolved content as a new `Inline` or `External` block linked by `materialized_by` to the now-dangling composed parent. Used to preserve resolved-content history when children's storage is destroyed
- `promotes_scope_of` — scope promotion. Source: a broader-scope block or reference record; target: the original narrower-scope block. Used when content is intentionally made addressable in a broader scope without treating the original as obsolete
- `scope_projection_of` — scope projection. Source: a scoped reference record; target: the original block. Used when the broader-scope object is an addressability projection rather than a content copy
- `attaches_to` — workspace anchor. Source: a block; target: a workspace path, conversation node, task, or run. Carries an offset or position metadata when applicable. Used by surface rendering and by the world-model state-awareness service (`core.world-model`, File 01 §6.7)
- `validated_by` — block validation. Source: any block; target: a `Validation` or `Critique` block whose target is the source. Closure under `validated_by` shows every validation that has been recorded for a block
- `responds_to` — request/response chain. Source: a block produced in response to the target; target: the eliciting block. Used in tool-call chains (a `ToolResult` `responds_to` a `ToolCallProposal`) and in clarification dialogs
- `conditioned_on` — explicit dependency. Source: a block whose meaning depends on the target being present (a `Plan` step `conditioned_on` a preceding task; a workflow node `conditioned_on` its predecessor)

### 5.3 Edge Extension

Subsystems and plugins may register additional edge kinds through the same extension plane that registers `Custom` block kinds. A registered edge kind declares:

- `namespace` and `name` — the edge's stable id, matching the capability sourcing taxonomy (`capability.capability-source`, File 05 §9.1)
- `from_kinds` — closed list of `BlockKind`s the source block may be (or `Any`)
- `to_kinds` — closed list of `BlockKind`s the target block may be (or `Any`)
- `metadata_schema` — declared structured shape of the edge's metadata field
- `transitive` — whether closure under this edge is meaningful (whether ancestor walks should follow it)
- `description` — human-readable description

### 5.4 Graph Properties

The block graph is:

- **acyclic in structural composition and lineage** (`parent`, `contains`, and the structural use of `supersedes`). Cycles among these would violate content resolution, edit history, or the version-graph contract
- **possibly cyclic in reference and provenance edges** (`references`, `cites`, `witnesses`, `attaches_to`, `validated_by`, `responds_to`, `conditioned_on`, `derives_from`, `consolidates`, `materialized_by`) unless an edge declaration explicitly forbids cycles
- **append-only**: edges, like blocks, are committed at boundaries and never mutated. An edge that becomes stale is left in place; the version graph determines whether the source/target blocks are active
- **inspectable** through canonical block-graph queries: ancestor walk by edge kind, descendant walk by edge kind, sibling enumeration (siblings = blocks with the same `parent_block_id`), supersession chain (closure under `supersedes`), citation network (closure under `cites`)

### 5.5 Boundary

The block graph defines structural relations between blocks. The version graph defines which subset of these relations is "current" for a given view. The execution ledger records the events that committed each block and edge. The retrieval layer indexes these edges for query. File 08 owns the edge catalogue and the graph's structural invariants; later specs consume them.

## 6. Block Lifecycle and Non-Destructive Edits

Anchor: `block.block-lifecycle-non-destructive-edits`

### 6.1 Definition

`BlockLifecycle` names the runtime view-state of a block within a particular `ContextVersion`. The states are:

- `Raw` — the block exists in the pool but has not been activated in any context view yet; transient state between commit and first inclusion
- `Active` — the block is part of the current view; rendered, included in context assembly, eligible for retrieval
- `Masked` — the block is hidden from the current view but reachable through explicit "show masked" affordances or through version-graph navigation; not included in context assembly by default
- `Dropped` — the block is hidden from the current view and not eligible for retrieval; reachable only through explicit recovery; storage is retained
- `Recovered` — the block was previously dropped and has been brought back into the current view; semantically equivalent to `Active` but carries the historical mark for inspector display

`PinState` names the user's explicit retention preference within a view:

- `Unpinned` — default; subject to compaction by default policies
- `Pinned` — the user has requested this block be preserved during compaction
- `Protected` — strongest form; the block is excluded from compaction algorithms entirely until explicitly unprotected

Lifecycle state and pin state are **derived from the version graph's action log over the block pool**, not stored on the block. The same block may be `Active` in one version and `Masked` in another; switching the active version updates the lifecycle view without mutating any block record.

### 6.2 Edit Semantics

Anchor: `block.edit-semantics`

Editing a block's observable content does not mutate the block. Edits create a new block in the same pool, linked to the prior by a `supersedes` edge (§5.2). The new block has:

- a fresh `block_id`
- the new content under the appropriate `BlockContent` variant
- the prior block's `block_id` as the target of a `supersedes` edge
- a new `content_hash`
- a fresh `created_at`
- a `producer` field reflecting the edit source (a `UserMessage` edit, an `InspectorApply`, an automated transformation)

The version graph advances the "current" pointer to the new block. The prior block remains in the pool, immutable, reachable through version-graph navigation and through the `supersedes` chain.

Editing a `Composed` block's children (adding, removing, reordering) is itself an edit: it creates a new `Composed` block with the new `children_block_ids` and a `supersedes` edge to the prior. The children themselves are not changed.

Editing a block's metadata (description, default sensitivity, source attribution) follows the same rule: the metadata is part of the block's identity at creation; observable metadata changes create a new sibling block.

### 6.3 Mask, Drop, Recover

Anchor: `block.mask-drop-recover`

`Mask`, `Drop`, and `Recover` are version-graph operations that change the view's lifecycle map without touching the block pool:

- `Mask(block_id)` — the version's lifecycle map for the block transitions to `Masked`. The block remains stored and addressable. Future versions branching from this one inherit the masked state until explicitly unmasked
- `Drop(block_id)` — the version's lifecycle map transitions to `Dropped`. Same storage and addressability as masked. Dropped blocks are excluded from retrieval and from default context assembly
- `Recover(block_id)` — transitions a `Masked` or `Dropped` block back to `Active` in the current view. The block's appearance in surface presentations resumes; retrieval indexing re-enables

These operations are committed as version-graph entries, not as block mutations. They emit `BlockLifecycleChanged` events through the event stream (`run.event-stream`, File 04 §23.2) and are recorded in the execution ledger.

### 6.4 Pin and Protect

Anchor: `block.pin-protect`

`Pin`, `Unpin`, and `Protect` modify the pin state in the current version's pin map:

- `Pin(block_id)` — marks the block as user-preferred for retention; compaction policies respect pinned status by default
- `Unpin(block_id)` — removes the pin
- `Protect(block_id)` — strongest retention preference; compaction skips protected blocks entirely
- `Unprotect(block_id)` — removes the protection

Like lifecycle changes, pin operations live on the version, not the block. They emit `BlockPinChanged` events.

### 6.5 Group and Ungroup

Anchor: `block.group-ungroup`

`Group(block_ids)` creates a new `Group`-kind `Composed` block whose children are the named blocks. The grouped blocks remain in the pool unchanged; the group block is a new container.

`Ungroup(group_block_id)` is an edit: a new version-graph entry adjusts the view to dissolve the group's presence in the current view. The group block itself is not destroyed; future versions may re-enable it.

### 6.6 Hard Delete

Anchor: `block.hard-delete`

Hard deletion is the only operation that physically destroys recoverable block payload storage. It is:

- explicitly user-initiated (no automatic hard delete; compaction never hard-deletes)
- typed-confirmation required when the block is referenced by a `Composed` parent, by a non-superseded `supersedes` chain, by an `Evidence` chain, or by any version other than the current one (`policy.permission-floor-typed-confirmation`, File 06 §7 typed-confirmation flow)
- recorded in the execution ledger as a `BlockHardDeleted` event with the deleting actor, the block id, and the references that would be orphaned
- accompanied by a minimal tombstone retaining `block_id`, deletion time, deletion actor/source, `conversation_id`, `scope`, `parent_block_id`, prior kind if safe, and a sensitivity-safe reason or description. Payload bytes, secret fields, embeddings, indexed text, and external blobs are removed. References resolve to a typed deleted-block placeholder, not an unexplained missing row
- accompanied by composition-materialization: if any `Composed` block depends on the deleted block as a child, the runtime materializes the composed block's resolved content into a new block (linked by `materialized_by`, §5.2) so the composed block's previously-resolvable content survives the deletion. If the materialization fails (content is not reconstructible from descriptions alone), the composed block transitions to a typed `MaterializationOrphaned` state and surface rendering shows the missing-child placeholder
- accompanied by reference-edge cleanup: edges originating from or terminating at the deleted block become orphan-marked; closure queries report the dangling state explicitly

Hard delete is the canonical mechanism for honoring user storage-management requests (`core.non-destructive-by-default`, File 01 §7.13's "manage and reclaim storage at every granularity") and for honoring credential or secret expungement. It is never automatic. Tombstone retention is the safe default, but deletion history itself remains user-manageable through explicit policy-governed cleanup.

### 6.7 Lifecycle Transition Rules

Anchor: `block.lifecycle-transition-rules`

The lifecycle state transitions are explicit and deterministic:

- `Raw → Active` — block is included in the current view for the first time
- `Active → Masked` — explicit mask operation
- `Active → Dropped` — explicit drop operation
- `Masked → Active` — explicit unmask
- `Masked → Dropped` — explicit drop while masked
- `Dropped → Recovered` — explicit recover; `Recovered` is semantically `Active` with the historical mark
- `Recovered → Active` — implicit (recovered is just an `Active` variant)
- `Recovered → Masked` / `Recovered → Dropped` — explicit (same as `Active`)

No time-based transition is permitted. No auto-mask-after-N-turns rule lives at the block layer (per File 01 constraint: never use time-based conditions unless unavoidable). Compaction policies may invoke `Mask` or `Drop` as explicit operations driven by their own logic, but the block layer enforces no implicit decay.

### 6.8 Boundary

Lifecycle is a view-state concern owned by the version graph. This file defines the state set and the transition rules; the version graph spec owns the version action log and the materialized view that tracks state per version. The block pool itself remains append-only and lifecycle-agnostic.

## 7. Streaming and the Commit Boundary

Anchor: `block.streaming-commit-boundary`

### 7.1 Definition

Block streaming is the process by which a producer (a model generating text, an executing capability emitting partials) commits its output as a `Block` at the producer's declared commit boundary. Streaming itself happens through `Event`s on the event stream (`run.event-stream`, File 04 §23.2). Blocks come into existence only at the commit point.

### 7.2 Event-Then-Block Pattern

The canonical pattern:

1. The producer begins emitting partial output. Each partial flows as a typed `Event` on the event stream, carrying the standard event envelope plus a `partial_block_handle` that names the eventual block id
2. Surface presentations consume the events live (live streaming UI, live tool-output rendering). The events are not durable history; they are live coordination
3. When the producer reaches its declared commit boundary (model finishes generating, capability completes, executor accepts the final structured payload), the runtime commits a `Block` containing the accumulated content
4. The committed block carries the same `block_id` that was named in the partial-block handle, so consumers that recorded the handle can correlate
5. Surface presentations switch from live-event rendering to durable-block rendering on commit; the visual transition is implementation-defined, but the substantive transition is: events are discarded (or retained per `run.event-stream` (File 04 §23.2) sensitivity rules), the block is the durable record

### 7.3 Partial-Block Orphans

Anchor: `block.partial-block-orphans`

If the producer fails before commit (cancellation, error, timeout, crash), no committed block exists yet. The runtime may retain staged partial records tied to the run; staged partials are cancellable, configurable, and outside the block pool until promoted through the normal commit validator. Partial events and staged records are subject to:

- `run.cancellation` (File 04 §17.3) cancellation rules — `partial_output_meaningful` declared on the capability determines whether the runtime preserves the partial as an orphan block or discards it
- if preserved as orphan: the runtime may promote the staged partial to a partial `Block` with kind matching the producer's declared output kind, content reflecting what was streamed before failure, and a typed `partial_orphan` marker in its metadata. The orphan block participates in the block graph normally and may be inspected
- if discarded: no block is committed; the partial events are retained in the event stream per the standard event-retention rules but are not promoted into the block pool

The decision is made per capability at registration time (`run.call-pipeline`, File 04 §8.2) and may be overridden at cancellation time by the user (`run.cancellation`, File 04 §17.3).

### 7.4 Tool-Input vs Tool-Output Streaming

`run.streaming-partial-execution` (File 04 §12) distinguishes the two stream halves; this file commits them to blocks the same way:

- **Tool-input streaming**: the model is still emitting a tool call's structured arguments. The events carry partial arguments. At commit (the model finishes the call and the executor enters the capability pipeline), the runtime commits a `ToolCallProposal` block with the final structured arguments
- **Tool-output streaming**: the executing capability is emitting partial results. The events carry partial output. At commit (the capability's declared commit point), the runtime commits a `ToolResult` block with the final structured result

The two commits may happen at different times for the same call. Both produce blocks in the same pool and are linked by `responds_to` edges.

### 7.5 Live-Partial-Write Capabilities

Anchor: `block.live-partial-write-capabilities`

For capabilities that support live partial-write into materialized state (`run.streaming-partial-execution`, File 04 §12 file-or-artifact write pattern: stage in temp file, atomic rename at commit), the block-layer commit aligns with the executor's atomic-rename point. The block is committed when the capability declares success; the staged temp file becomes the durable artifact at the same boundary; the `Artifact` block points to the now-durable location.

If the live-write is cancelled mid-stream, the temp file is deleted per `run.streaming-partial-execution` (File 04 §12), and no `Artifact` block is committed. The partial events are retained or discarded per §7.3.

### 7.6 Commit Boundary Set

Anchor: `block.commit-boundary-set`

The canonical block-commit boundaries are:

- a user submits a message → `MessageUser` block (and any `Composed` children for attachments, mentions, quoted blocks)
- an assistant turn reaches accepted final state → `MessageAssistant` block plus its constituent `ToolCallProposal`, `ToolResult`, `ReasoningTrace`, and text children blocks
- a capability invocation completes (success, typed failure, or policy denial) → `ToolCallProposal` and `ToolResult`, `Failure`, or `ToolDenial` blocks
- the router emits a route record → durable route/run record; blocks may reference that record when conversation history needs visible route inspection
- an inspector applies a state-changing operation (e.g., user pins, drops, edits) → version-graph entry with associated block creates or edge updates
- a workflow node completes → block matching the node's declared output kind
- an import operation succeeds → block(s) representing the imported content
- a consolidation operation completes → `Consolidation`-related blocks plus `consolidates` edges
- a user explicitly commits a draft (a manual block-commit affordance in the inspector)
- a subsystem's internal commit (memory promotion, evidence-chain commit, or equivalent) hits its declared boundary

Each boundary corresponds to a version-graph commit and to a ledger entry. Between boundaries, work is staged in the pending-operations buffer (`run.version-commits`, File 04 §23.4) as events, not as blocks. The buffer accumulates incremental work; the block commit is the atomic durable promotion.

### 7.7 Boundary

Streaming is owned by File 04 and the event stream. This file owns the durability contract: where streaming becomes a block, what the block looks like at commit, and how cancellation interacts with the commit. The version graph spec owns the version-graph entry that records the commit.

## 8. Identity, Validation, and Hashing

Anchor: `block.identity-validation-hashing`

### 8.1 Identity

A `block_id` is:

- globally unique within the ATLAS3 installation
- assigned at commit time (or at first event emission for streaming blocks, where the handle is reserved at stream start; commit promotes the reserved id to a durable block)
- never reused, never reassigned, never mutated
- the canonical cross-layer reference: events carry `block_id` references; ledger entries record `block_id`; version graph entries name `block_id`; capability invocations attribute output to `block_id`; surface projections render `block_id`
- format-agnostic at this layer (UUID-v7, ULID, or any equivalent identifier with the required uniqueness and orderability properties is acceptable; the storage spec picks the wire format)

A block's identity is independent of its content. Two blocks with identical content have different ids. Deduplication uses `content_hash` as a separate dimension (§4.5).

### 8.2 Block Commit Validator

Anchor: `block.block-commit-validator`

Before a block is admitted to the pool, the block commit validator runs:

1. **Identity validation**: `block_id` is well-formed, not already in use
2. **Kind validation**: `kind` is a canonical kind or a registered `Custom { namespace, name }`
3. **Content-variant validation**: the chosen `BlockContent` variant is permitted by the kind's `allowed_content_variants` (closed for canonical kinds, declared for custom kinds)
4. **Composition validation**: for `Composed`, `children_block_ids` is non-empty, all referenced child ids exist in the pool, no cycles in the resulting structural graph
5. **Edge validation**: any committed edges have `from_block_id` and `to_block_id` resolving to existing blocks (or to the just-committed block); kind-level edge constraints (§5) are satisfied
6. **Parent validation**: `parent_block_id` (if set) resolves to an existing block, and the parent's kind permits the child's kind under the kind's `permitted_parent_kinds` declaration
7. **Producer validation**: `producer` is well-typed and corresponds to a known producer source (capability registry for capability commits, conversation/user-id for user messages, etc.)
8. **Sensitivity validation**: `default_sensitivity` is one of the canonical values; the per-field map (if present) references valid field paths; composed blocks must not underreport the maximum effective sensitivity of their children unless a policy-approved typed-confirmation override applies
9. **Description validation**: `description` is non-empty for kinds that require it (all canonical kinds; custom kinds may opt out only when their declaration specifies)
10. **Hash validation**: the content hash is computable from the content, variant discriminator, and `block_schema_version`, and matches the supplied `content_hash`
11. **Scope validation**: the declared `scope` is one of the canonical values and is compatible with the producer (a `run`-scoped block must have an `origin_run_id`; a `workspace`-scoped block must have a workspace context)

A failed validation produces a typed `BlockCommitRejected` error per `run.denial-is-in-band` (File 04 §8.3)'s in-band denial. The producer (a capability handler, the executor, a subsystem) receives the typed error and may retry with corrected input, escalate, or abort.

### 8.3 Hash Collision

SHA-256's collision resistance makes practical content hash collision negligible. The system does not encode a collision-recovery path beyond logging a high-severity `ContentHashCollisionSuspected` event when two distinct blocks with the same hash are detected at storage. The storage layer may use the hash for deduplication only when blocks are also structurally equal; a hash match alone is not used as identity.

### 8.4 Cross-Reference Rules

References from blocks to blocks (via `parent_block_id`, `children_block_ids`, edges, or content embeddings) use `block_id` as the canonical reference key. References to external resources use registered storage references or typed source references captured at commit time; uncaptured remote URLs are citations, not durable payload storage. References to capabilities use `(capability_id, capability_version)` per `capability.identity-namespacing-versioning` (File 05 §13). References to events use `(event_envelope, sequence)` per `run.event-stream` (File 04 §23.2).

A block whose committed references resolve to non-existent targets at read time produces a typed `BrokenBlockReference` event but does not corrupt the block — the reference itself is immutable; only the target's existence has changed.

### 8.5 Boundary

Identity, validation, and hashing are commit-time concerns owned by this file. Storage of these fields and propagating them to surface displays are owned by File 20 and the future UI specs; indexing is owned by File 12.

## 9. Sensitivity

Anchor: `block.sensitivity`

### 9.1 Definition

Block sensitivity is the durable counterpart to event sensitivity (`run.event-stream`, File 04 §23.2). Every block carries a `default_sensitivity` field with values:

- `Public` — the block may appear in shareable exports, may be cached by external services that handle public content (provider-side model-request caches when the provider permits), and may be persisted in the durable ledger without redaction
- `Sensitive` — the block contains user-private or workspace-specific data; excluded from shareable exports and clipboard-copy operations unless the user explicitly overrides; persisted in the durable ledger; subject to shorter default retention if settings configure it
- `Secret` — the block contains credentials, raw API keys, OAuth tokens, password content, or equivalent never-leak material. Secret blocks are persisted to the durable block pool with redacted content (the redaction is applied at commit; the original raw secret is held only in transient memory and zeroed after use). The block's `description` field summarizes what the secret is without revealing it (e.g., "AWS access key for production environment"). Secret blocks are not retrievable through search, not included in compaction algorithms' content review, and not exported under any standard share/export path

### 9.2 Per-Field Override

Anchor: `block.per-field-override`

A block's content may contain mixed-sensitivity material. The block carries an optional `sensitivity_field_map` that overrides the default per JSON-path-style field reference into the block's content. Example: a `ToolResult` block whose content is `{ stdout: "ok", stderr: "...", credential_used: "aws-prod-key" }` may declare `default_sensitivity: Sensitive` plus an override mapping `$.credential_used: Secret`. Rendering, export, and retrieval respect the per-field map.

### 9.3 Inheritance Through Composition

A `Composed` block's effective sensitivity is the maximum of its declared `default_sensitivity` and the maximum effective sensitivity of its children. If a `Composed` block declares `Public` but contains a `Secret` child, the composed block's effective sensitivity is `Secret`.

The commit validator must prevent persisted underreporting. When the effective sensitivity is deterministically higher than the producer-declared value, the validator auto-escalates the declared sensitivity to the effective maximum and records an inspectable warning event. If the producer explicitly requested unsafe lowering, the commit is rejected unless policy allows a typed-confirmation override. Rendering, export, indexing, and caching always use effective sensitivity, never a lower declared value.

### 9.4 Producer-Seeded Defaults

Each `BlockKind` declares a default sensitivity in its kind declaration (the canonical kinds and the registered `Custom` kinds both do this). When a capability commits a block, the executor uses the capability's `data_sensitivity` declaration (`capability.permission-policy-fields`, File 05 §3.5) as the producer-seeded value, which then becomes the block's `default_sensitivity`. The producer may override the seed by emitting an explicit `default_sensitivity` value, subject to policy constraints (a capability cannot lower a `Secret`-seeded block to `Public` without a typed-confirmation policy override).

### 9.5 Projection Independence

Sensitivity is independent of presentation. A surface that renders a block consumes its effective sensitivity to decide rendering, export, and copy behavior. The surface does not modify the block's stored sensitivity; the sensitivity is a property of the durable content, not of the presentation.

### 9.6 Boundary

Sensitivity is a durable property of the block. The policy layer (File 06) decides what to do at policy boundaries based on sensitivity. The event stream (`run.event-stream`, File 04 §23.2) uses the same value set for transient coordination. Surface rendering consumes sensitivity to gate displays. None of those layers redefines the value set.

## 10. Block Description

Anchor: `block.block-description`

### 10.1 Definition

Every block carries a `description` field — a short structured natural-language description of what the block contains, emitted by the producer at commit time. The description is fixed at commit; future references to the block use this description for compaction, retrieval ranking, surface previews, and discovery.

### 10.2 Producer Responsibility

The producer chooses the description at the moment of commit. For canonical kinds:

- `MessageUser` and `MessageAssistant` — derived from the message content (the first N words, or a model-generated summary if configured); the producer (the conversation engine or the executor) emits the description as part of the commit
- `ToolCallProposal` — a one-line summary of the call: `"<capability_id>(<argument_summary>)"`
- `ToolResult` — a one-line summary of the result: success/failure tag, key field values, byte count for large outputs
- `Observation` — a one-line summary of what was observed
- `Artifact` — the artifact's title or filename plus a one-line content summary
- `Memory`, `Plan`, `Evidence`, `Citation`, `Validation`, `Critique`, `ReasoningTrace`, `SourceExcerpt`, `Failure`, `ContextNotice` — kind-specific summary templates declared in the kind's metadata

For `Custom` kinds, the kind's registration declares the description template and the producer follows it.

### 10.3 Why Descriptions Are Committed Fields

Descriptions live on the block, not in a compaction service or in a retrieval index, because:

- compaction algorithms read descriptions, not full content, to decide what to evict or summarize. A description that lives on the block survives compaction itself
- retrieval uses descriptions for low-cost first-pass filtering; full-content embeddings are computed separately
- surface presentations render descriptions in collapsed views, list views, and previews
- inspector lenses (`surface.inspector-lens`, File 07 §12.4) render descriptions in catalogue displays
- when a block's content is `External` or `Composed`, the description is the only inline content available; without it, every preview operation would require full content resolution

### 10.4 Description Immutability

Anchor: `block.description-immutability`

The description is fixed at creation. A block whose description proves inadequate is edited (which creates a sibling per §6.2), not patched in place.

### 10.5 Boundary

The description is owned by the block. The compaction service, retrieval service, and surface presentations consume it. None of those layers modifies the description; if they need a richer description, they request a regeneration through a capability call that produces an edit-sibling block.

## 11. Block Scope

Anchor: `block.block-scope`

### 11.1 Definition

Every block has a `scope` denoting the broadest context within which the block is visible and addressable:

- `run` — the block is visible only within the originating `Run`; transient blocks used for internal coordination; pruned with the run
- `intent_thread` — the block is visible within the originating intent thread, across runs that share the thread
- `task` — the block is visible within the originating task, across runs that advance it
- `conversation` — the block is visible within the originating conversation; the default for transcript-related blocks
- `workspace` — the block is visible across conversations within the workspace; the default for workspace artifacts and workspace-scoped memory
- `global` — the block is visible across workspaces; reserved for global memory entries, global settings blocks, and equivalent
- `reusable_policy_rule` — matches the lease scope from `policy.lease-primitive` (File 06 §11); reserved for blocks that express reusable policy or workflow templates

The scope is declared at commit by the producer. Scope determines:

- which surfaces and runs can address the block by id
- which retrieval indices include the block
- which compaction policies are eligible to evict the block
- which export/share operations include the block in their output

### 11.2 Scope Promotion

Anchor: `block.scope-promotion`

A block may be promoted to a broader scope through an explicit operation (a user pins a `run`-scoped observation into `conversation` scope; an agent promotes a `task`-scoped plan into `workspace` scope). Promotion creates a new immutable block or reference record at the broader scope, linked to the original by `promotes_scope_of` or `scope_projection_of`. The original remains valid at the original scope. `supersedes` is reserved for content/version replacement, not visibility broadening.

Scope demotion (broadening down to narrower scope) is not permitted as a direct operation; a workspace block whose content is later judged conversation-specific is left at the workspace scope. The retrieval and surface layers may filter it out of broader contexts, but the block's declared scope is fixed at commit.

### 11.3 Cross-Scope References

Anchor: `block.cross-scope-references`

A block at a narrower scope may reference (via edges) a block at a broader scope (a `run`-scoped `ToolResult` may `references` a `workspace`-scoped `Memory`). A block at a broader scope may reference a block at a narrower scope only if the references remain meaningful when the narrower block is no longer in scope (a `workspace`-scoped `Plan` referencing a `task`-scoped block must tolerate the task's blocks being garbage-collected). Edge resolution at read time honors the scope rules: a reference that cannot be resolved produces a `BrokenBlockReference` event but does not corrupt the referencer.

### 11.4 Boundary

Scope is a durable property of the block. Storage uses scope to organize physical layout. Retrieval uses scope to bound queries. The future workspace spec defines the workspace boundary; this file uses workspaces as a scope label without redefining workspace semantics.

## 12. Cross-Surface Interoperability

Anchor: `block.cross-surface-interoperability`

### 12.1 Definition

ATLAS3 has one block pool. Every work surface (Coder, Web, Data Processor, Teacher, GUI Control, System Agent), every substrate service (Memory, Routing, Knowledge), every control rail (Conversation, Palette, Voice, Shortcut, Automation), and every external integration (MCP server, plugin, external API) reads from and writes to the same pool through the same block model.

### 12.2 Per-Surface Projections

Each surface projects the pool through surface-specific filters:

- a Coder surface presentation filters for `FileAttachment`, `Artifact` (code), `ToolCallProposal` and `ToolResult` for code-related capabilities, `Validation` (tests), `Critique` (review comments)
- a Web surface presentation filters for `Observation` (page extracts), `Artifact` (downloads), `Citation` (URLs), `ToolCallProposal` for browser capabilities
- the conversation transcript filters for transcript-anchorable kinds: `MessageUser`, `MessageAssistant`, and the kinds that appear as their children
- the inspector lens (`surface.inspector-lens`, File 07 §12.4) presents every block in the pool, filtered by user-chosen axes

The filter is a surface concern; the blocks remain in the pool unchanged. A block produced by the Coder surface but referenced by the Memory subsystem is visible in both.

### 12.3 Cross-Surface Composition

Anchor: `block.cross-surface-composition`

A block may compose blocks from multiple surfaces. A `MessageAssistant` answering a research question may compose:

- text children describing the conclusion
- `Citation` children pointing to web sources (committed by Web)
- `Artifact` children pointing to generated code (committed by Coder)
- `Observation` children referencing files inspected (committed by File operations)
- `Evidence` children supporting the claim

The composition is a single `Composed` block in the pool. Each child block lives at its appropriate scope. The composition renders correctly in any surface that supports the constituent kinds; surfaces that do not support some child kinds render those as typed placeholders ("[unsupported kind: …]") and link to the inspector lens for full inspection.

### 12.4 Boundary

Cross-surface interoperability is a property of the unified pool. This file establishes the pool's invariants; later per-surface specs declare how each surface projects, filters, and composes blocks. No surface is permitted to introduce a private block pool, private kind catalogue, or private edge catalogue.

## 13. Block Persistence Contract

Anchor: `block.block-persistence-contract`

### 13.1 What Is Durably Stored

Anchor: `block.what-is-durably-stored`

The following block-related facts are durable:

- the block pool — every committed block survives process restart, conversation archive, and version-graph operations until explicit hard delete
- the edge set — every committed edge survives
- per-block metadata — `block_id`, `kind`, `content`, `parent_block_id`, `producer`, `origin_run_id`, `conversation_id`, `created_at`, `block_schema_version`, `content_hash`, `source_attribution`, `default_sensitivity`, `sensitivity_field_map`, `description`, `scope`
- the version graph — version nodes, lifecycle action logs, pin maps; survives restart
- block-related events recorded in the ledger — every block commit, every lifecycle transition, every edge commit produces a ledger entry

### 13.2 What Is Computed

Anchor: `block.what-is-computed`

The following are computed, not stored:

- per-version lifecycle maps — derived from the version-graph action log; rebuilt on demand from durable action records
- per-version pin maps — same as lifecycle
- the materialized view of "blocks active in the current view, in render order" — derived from the version graph plus the surface's projection filter
- per-tokenizer token counts — computed on demand per `(block_id, tokenizer_id)`, never cached as plain scalar on the block (per `core.explicit-rejections`, File 01 §8 invariant rejecting unkeyed model-dependent scalars)
- per-block retrieval relevance scores — computed by the retrieval service
- per-block embedding vectors — computed by the indexing service using model-keyed identifiers

### 13.3 Reconstruction Across Restart

Anchor: `block.reconstruction-across-restart`

On process restart, the block pool re-emerges from durable storage. The version graph reloads. Per-version lifecycle and pin maps rebuild from the action log. In-flight streaming events that were not committed at restart follow the orphan-run rules of `run.cancellation` (File 04 §17.3) — partial events whose producing run was orphaned do not become blocks unless the capability declared `partial_output_meaningful` and a recovery handler.

The active view a new run sees after restart is the same view a new run would have seen before restart, modulo any changes recorded during the offline interval. Determinism is required for replay.

### 13.4 Reconstruction Across Retry, Edit, Reroute, Branch

Anchor: `block.reconstruction-across-retry-edit-reroute-branch`

Per `run.retry-reroute-branch` (File 04 §19), retry, edit, reroute, and branch produce new runs linked to prior ones. The block pool itself is shared: the new run's blocks join the same pool. The version graph records the branch; lifecycle maps may diverge across the version branches (one branch may mask a block another branch keeps active). The block records themselves remain singular.

### 13.5 Boundary

Persistence is the storage layer's responsibility. This file specifies what the storage layer must persist (the field set above) and what it must reconstruct (the computed views). The storage schema, replication, sync, and import/export mechanics are owned by File 20 and the future Sync, Import, Export, and Data Portability spec.

## 14. Settings

Anchor: `block.settings`

### 14.1 Configurable Dimensions

Every block-presentation, retention, and discovery mechanism in this file is configurable through settings (per `core.settings-system`, File 01 §6.8). File 08 names the dimensions; the settings system owns the cascade and storage.

Surface-presentation dimensions:

- `blocks.inline_size_threshold_bytes` — boundary between `Inline` and `External` content variants for kinds that permit both; default settings-profile-dependent
- `blocks.description_visibility` — whether block descriptions render in collapsed views (always / hover / never)
- `blocks.expansion_default` — whether `Composed` blocks render expanded or collapsed by default in transcript and inspector
- `blocks.cross_surface_render_strategy` — when a surface encounters a kind it does not natively render: render with a generic typed placeholder, link to inspector, or show kind-specific fallback

Retention dimensions:

- `blocks.hard_delete_confirmation_threshold` — the typed-confirmation requirements for hard delete (per `policy.permission-floor-typed-confirmation`, File 06 §7); per-kind override allowed
- `blocks.orphan_retention_policy` — whether to keep partial orphans, discard them, or per-kind override (default: keep when `partial_output_meaningful: true`)
- `blocks.compaction_default_policy` — the default compaction policy for non-pinned blocks; File 13 owns the policy set

Sensitivity dimensions:

- `blocks.export_sensitivity_filter` — minimum sensitivity excluded from exports (default: `Sensitive` excluded; `Secret` always excluded)
- `blocks.copy_to_clipboard_sensitivity_filter` — same set, for clipboard operations
- `blocks.redaction_strategy` — how `Secret` content is rendered (kind-only label, structured surrogate, fully omitted)

Custom-kind dimensions:

- `blocks.allow_custom_kinds_from_source.<source_id>` — per-source toggle for accepting custom kind registrations
- `blocks.custom_kind_review_threshold` — the source-approval flow threshold for new custom kinds (per `policy.source-approval-flow`, File 06 §9 source-approval flow)

Description dimensions:

- `blocks.description_max_length_chars` — soft cap on description length at commit; producers above the cap emit a truncated description
- `blocks.description_regeneration_enabled` — whether the system permits the user to request a regenerated description for a block (which creates a sibling edit)

Agent-exposure dimensions (per `policy.agent-exposure-policy-settings`, File 06 §16.4):

- `blocks.kind_catalogue_visible_to_agent` — whether the model sees the full canonical kind catalogue in model-request text content (default `InModelRequest` for the canonical kinds; custom kinds `OnRequest`)
- `blocks.sensitivity_exposure` — whether sensitivity is visible to the agent (`InModelRequest` for `Public`/`Sensitive`/`Secret` indicators; `Hidden` for `sensitivity_field_map` detail)
- `blocks.description_visible_to_agent` — whether other blocks' descriptions appear in the agent's compaction-eligible content (`InModelRequest`)

### 14.2 Settings-Key Convention

Block-related settings use the dotted-key convention `blocks.<dimension>`. Per-kind overrides use `blocks.<dimension>.kind.<kind_name>`. Per-source overrides use `blocks.<dimension>.source.<source_id>`. Plugin- or subsystem-registered custom kinds may register their own kind-specific settings keys.

### 14.3 Boundary

This file names the settings dimensions. The settings system owns cascade resolution, storage, and the inspector UI. Per-dimension defaults belong to tested settings profiles, not to hardcoded constants in this canonical layer.

## 15. Explicit Rejections

Anchor: `block.explicit-rejections`

The following shapes are wrong for this layer:

- mutable block content — every observable content change is a new block in the same pool, linked by `supersedes`. In-place mutation of `content`, `kind`, `parent_block_id`, `created_at`, `content_hash`, or `producer` is invalid
- in-place lifecycle storage on the block row — `BlockLifecycle` and `PinState` live on the version-graph's per-version maps, not on the block. Storing them on the block would force every mask/drop/pin to mutate the block row and would break the immutability invariant
- private per-surface or per-capability block models — there is one block pool with one model; surface and capability specs project the pool, they do not own private pools
- implicit inferred edges from content patterns — parent and composition are structural fields exposed as derived edge views; every non-structural relation is an explicit committed edge record
- open block kinds without canonical baseline — the kind set is closed canonical plus registered `Custom`; a producer that emits an unparseable kind is invalid. Adding to the canonical baseline requires a canonical spec update
- silent kind shadowing — when two extensions register `Custom` kinds with the same `(namespace, name)`, the registry rejects the second; there is no silent override
- live events as durable history — events on the event stream are coordination; they do not become the block. The block is committed at the producer's declared boundary. Treating events as the source of truth bypasses the durability and immutability invariants
- block IDs that lack global uniqueness, lack stable ordering, or get reassigned — every block id must be unique, stable, and never reused
- per-surface block-id namespaces — every block has one id in one namespace
- silent hard delete — hard delete is always explicit, always typed-confirmation-gated when references depend on the block, and always recorded in the ledger
- automatic mask-after-time-window — time-based block lifecycle transitions are forbidden (File 01 constraint). Compaction may invoke explicit `Mask`/`Drop` operations, but the block layer enforces no implicit decay
- forcing every event into a block — events are not blocks. The streaming model commits blocks at boundaries; not every event becomes durable
- block content carrying a token-count scalar — token counts are model-dependent and must be keyed by tokenizer identifier (`core.explicit-rejections`, File 01 §8); blocks store content, not unkeyed scalars
- block content carrying a cost scalar — same rule; cost is computed per-model per `core.explicit-rejections` (File 01 §8)
- `Composed` blocks whose children list mutates — children list is immutable like content. Adding or removing a child creates a sibling composed block
- `Composed` blocks with no children — invalid composition
- `Evidence` blocks without any supporting `cites` edges — invalid evidence
- mixed-sensitivity blocks where declared sensitivity underreports effective sensitivity — commit validation must auto-escalate when deterministic or reject when unsafe lowering was explicitly requested without policy approval
- block descriptions that are regenerated in place — descriptions are immutable like content. A new description means a new sibling block
- treating `Block` and `Message` as the same primitive — a `Message` is a transcript anchor (File 02); a `Block` is the durable structured content. One message anchors one primary block, which may be composed over children; one block may participate in many messages or in no message at all
- treating `Block` and `Event` as the same primitive — events are live coordination; blocks are durable history. The commit boundary separates them
- treating `Block` and `Artifact` as the same primitive — artifact-kind blocks are the block-level handles for artifacts. Artifact identity, lifecycle, versioning, materialization, export mechanics, and artifact-specific UI are owned by the artifacts/provenance layer. The same boundary applies to Evidence, Memory, and equivalent higher-level primitives: blocks carry their content; later specs define their specialized identity.
- treating `Block` and `Capability` as the same primitive — capabilities are typed operations the system can perform (File 05); blocks are the durable content those operations may produce
- treating `Block` and `Ledger Entry` as the same primitive — the ledger is the durable execution-history record; the block is the durable content-bearing record. Both are durable; they record different things. A `ToolResult` block and the ledger entry recording the tool call coexist and link through cross-references, not through a canonical join-table block kind
- silent compaction without ledger record — every mask, drop, or consolidation emits the corresponding `BlockLifecycleChanged` or `BlockConsolidated` event into the ledger; silent compaction would defeat audit and replay
- forcing block storage layout into the canonical model — the canonical model defines the durable contract; storage chooses its physical layout. This file makes no claim about row vs document vs columnar storage
- claiming "the block kind catalogue must remain unchanged forever" — the canonical catalogue evolves through canonical-spec updates; new kinds are added when the design space warrants. The `Custom` extension covers runtime extension; canonical evolution covers structural growth
- using block ordering as sequence truth — sequence within a view is owned by the version graph; blocks are not ordered by `created_at` alone

## 16. Consequences for Later Specs

Anchor: `block.consequences-for-later-specs`

Later specs must follow these rules:

- The artifacts, claims, evidence, and provenance spec must define entity-level lifecycle over `Artifact`, `Evidence`, `Citation`, and claim-related blocks without introducing an incompatible content carrier.
- The ledger, event stream, and hooks spec must record block commits, edge commits, lifecycle transitions, hard deletes, tombstones, and policy-related block events. Ledger rows may reference `block_id`; they must not duplicate block content.
- The version graph spec must store per-version lifecycle, pin, ordering, and action-log state over the block pool. It must not store block content.
- The retrieval, indexing, and knowledge-base spec must treat vector, BM25, graph, and embedding indexes as rebuildable projections over blocks. Retrieval may return committed `SourceExcerpt` blocks only when excerpts are deliberately promoted to durable context.
- The context assembly and compaction spec must assemble context from the active block projection, respecting pin state, sensitivity, scope, and committed descriptions. Compaction invokes explicit block lifecycle operations; it never mutates block content.
- The memory spec must treat memory entries as `Memory`-kind blocks while owning salience, decay, recall, and management behavior.
- Provider and model-strategy specs must render blocks into provider-native model requests without treating assembled request text as ordinary durable blocks.
- Storage, sync, import, export, and portability specs must preserve block identity, schema version, content, structural fields, edges, tombstones, and sensitivity. Physical layout choices remain implementation details subordinate to this contract.
- Security and credential specs must treat `Secret` sensitivity and per-field sensitivity maps as hard policy inputs; raw secrets are redacted or kept transient according to the security spec, never leaked through descriptions, indexes, exports, or telemetry.
- Workspaces, materialization, and surface specs must project the shared block pool. No surface, workspace, plugin, MCP integration, automation, workflow, quality-control system, telemetry system, runtime service, or packaging layer may introduce a parallel block model, private block pool, parallel capability metadata, or capability-like primitive that bypasses the contracts defined in Files 05-08.

Specific integration contracts will be stated in those files when they are written.
