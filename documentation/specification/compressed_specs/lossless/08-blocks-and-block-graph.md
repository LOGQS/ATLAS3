> Lossless render of canonical/08-blocks-and-block-graph.md — original 85780 chars

# Blocks and Block Graph

## Status
Canonical.

## Scope
Defines: `Block` (universal durable immutable typed composable context-bearing carrier); `BlockContent` (three durable variants `Inline`/`External`/`Composed`); the canonical closed `BlockKind` catalogue + registered-extension mechanism; block identity, addressability, content hashing, cross-reference rules; immutability + non-destructive edit/sibling-versioning model; staged-partial-write commit boundary turning streaming events into committed blocks; `BlockLifecycle` (`Raw`,`Active`,`Masked`,`Dropped`,`Recovered`) as derived view-state not block-stored; `PinState` (`Unpinned`,`Pinned`,`Protected`) as derived view-state; `BlockGraph` (typed directed graph; only structural composition subgraph must be acyclic); composition rules (`Composed` blocks reference children; sequence on the version not the block); sensitivity tagging (`Public`,`Sensitive`,`Secret`) at block + per-field granularity + projection independence; boundary `Block` vs `Event` (live coordination signal); boundary `Block` vs `Message` (transcript anchor pointing at one primary block, possibly composed); cross-surface interop (one block pool, surface-specific projections); per-block scope (`run`,`intent_thread`,`task`,`conversation`,`workspace`,`global`,`reusable_policy_rule`) + scope-promotion rules; capability↔block linkage (`output_block_kinds` from [`capability.output-kinds`] draws from this catalogue); persistence contract; settings dimensions for rendering/expansion/sensitivity-redaction/retention.

Does not define: ledger row format (File 10); version-graph commit storage/algorithms (File 11); artifact lifecycle/claims/evidence/provenance beyond block-relation surface (File 09); retrieval/indexing/KB (File 12); context assembly/compaction/token-budget (File 13); memory promotion/salience/lifecycle (File 14); run lifecycle/capability-call pipeline/hook execution (File 04); block-rendering UI choices (future UI specs); storage schema/sync/import/export (future specs).

## Source Resolution
Resolves messages, artifacts, tool results, notices, attachments, summaries, groups, committed model output into one boundary: durable block model + composition graph. Resolved: blocks are immutable durable content units; lifecycle/ordering/pinning/visibility are versioned projection state around them. Messages, artifacts, evidence handles, memory content, tool calls/results, failures, summaries, groups are block kinds or later entity layers over blocks. Events carry live/transient activity; blocks created only when content deliberately committed for audit/replay/context/inspection. Catalogue closed with `Custom` extension; subsystem/surface specs add kinds via registration. Composition explicit via parent/child/reference edges, not nested mutable message structures. Scope/sensitivity/provenance/lifecycle metadata determine safe visibility + retrieval.

## 1. Chosen Model `block.chosen-model`
One `Block` model + one `BlockGraph`. Every durable structured content (user message, accepted assistant turn, tool-call proposal, tool result, reasoning trace, file attachment, citation, memory entry, validation report, artifact handle, plan, execution trace, workflow step record, structured observation, evidence chain) is a `Block`; relations form the `BlockGraph`. Some kinds are also higher-level entities (message/artifact/memory/evidence/tool-call/validation): one primary block may carry specialized lifecycle/UI/management/export owned by its later spec; block is durable carrier, doesn't erase entity meaning.

A `Block`: immutable after creation (identity, kind, content (`Inline` payload / `External` ref / `Composed` children list), parent, content hash, source attribution, creation timestamp fixed at commit, never change); typed (`BlockKind` from closed catalogue §3, with `Custom { namespace, name }` extension registered through same extension plane as capabilities [`core.extension-planes`]); composable (a `Composed` block has no `Inline`/`External` payload, carries ordered `children_block_ids` resolving at read time; composition is what the block represents); durable (persists across run boundaries, conversation archival, restart, version-graph rewrites; only explicit user-initiated hard deletion destroys storage); addressable (stable `block_id` used by version graph, ledger, event stream [`run.event-stream`], capability invocations [`capability.invocation-record`], policy events [`policy.approval-policy-templates`], every surface (File 07)).

A `Block` is not: a UI element (same block rendered differently across surfaces without changing); a row in any single store; a transcript line (a `Message` [`intent.message`] is a presentation anchor over one primary block, possibly `Composed`); a live coordination signal (those are `Event`s [`run.event-stream`], never carry durable-history contract); mutable (every observable change is a new block in same pool, prior preserved, linked by typed edge).

A `BlockGraph`: typed directed graph, each registered block a node, each structural/explicit edge a labeled relation. Closed under canonical edge kinds (§5) + registered extension edges; acyclic only for structural composition subgraph (reference/citation/validation/knowledge edges may cycle unless declaration forbids); inspectable via canonical block-graph queries (closure by edge type, ancestor walks, sibling enumeration, content-addressed lookups); versioned in projection only (graph itself doesn't change with view switches; what changes is which subset is `Active` for a `ContextVersion`; single immutable structure, lifecycle per-version state over it); substrate for context assembly, retrieval, evidence chains, memory promotion, cross-surface interop.

No per-surface block registry, no per-capability private block format, no per-conversation isolated pool, no "events become blocks" silent promotion: every block enters via a declared producer (capability commit, user-message commit, inspector apply, workflow-node commit, import) and is referenced through stable identity.

`Block` supersedes earlier source vocabulary for the same primitive ("transcript block","content block","fragment","chunk","DAG node","history entry","node output","session entry","rich block","typed block","context entry","memory row"); informal synonyms may persist, canonical noun is `Block`.

## 2. `Block` `block.block`
2.1 Universal durable context-bearing carrier; typed structured content reasoned about across surfaces/executions/conversations/time.

2.2 Required fields (minimum):
- `block_id` — globally stable; never reused/reassigned/mutated
- `kind` — `BlockKind` (§3); fixed at creation
- `content` — `BlockContent` discriminated value (§4); fixed at creation
- `parent_block_id` — primary causal parent (optional; null for genesis like fresh user message); means "produced in response to / inside context of"; closure under `parent` = causal lineage
- `producer` — typed: `UserMessage { conversation_id, user_id }`, `CapabilityCommit { capability_id, capability_version, invocation_id }`, `RouterEmission { route_id }`, `InspectorApply { inspector_lens, user_id }`, `WorkflowNode { workflow_id, node_id }`, `Import { source_kind, source_ref }`, `Consolidation { policy_id, source_block_ids }`, `Subsystem { subsystem_id, reason }`
- `origin_run_id` — `Run` (File 04) under which committed; null when outside a run
- `conversation_id` — conversation committed under, when applicable; null for workspace/global-scope blocks without conversation anchor
- `created_at` — full-granularity commit timestamp
- `block_schema_version` — version of canonical block record shape interpreting `kind`,`content`,sensitivity maps,references,hashing
- `content_hash` — SHA-256 over canonical content representation (§4.5); fixed at creation
- `source_attribution` — typed source linkage to File 05 capability declaration + source instance when from a sourced capability (`Builtin`/`Subsystem`/`Plugin`/`McpServer`/`Api`/`UserDefined`); null for user-produced + system-internal blocks
- `default_sensitivity` — `Public`|`Sensitive`|`Secret` (§9); fixed at creation, per-field overrides via `sensitivity_field_map`
- `description` — short structured NL description from producer at commit (§10)
- `scope` — broadest visibility scope (§11): `run`|`intent_thread`|`task`|`conversation`|`workspace`|`global`|`reusable_policy_rule`

For `Composed`, ordered child list lives only inside `BlockContent.Composed { children_block_ids }`; storage may index it but canonical source of truth is the content payload not a duplicate top-level field. Every other field is derived (lifecycle, pin state, sequence-within-version), computed (token counts per tokenizer), or owned by adjacent layers (event linkage by ledger spec, version membership by version-graph spec).

2.3 Boundary: block defines durable substance; version graph decides which blocks active in any view; event stream [`run.event-stream`] coordinates streaming preceding commit; ledger records policy decision + capability execution producing the block. None invent new block semantics. Block model wire-stable through `block_schema_version`, `BlockKind`, `BlockContent` discriminators; adding a variant is a canonical-spec change not runtime registration — runtime registration of new kinds via `Custom { namespace, name }` (§3.4), not new top-level enum variants. Storage/import must validate supported block schema versions, explicitly upgrade or reject unsupported; silent reinterpretation invalid.

## 3. `BlockKind` `block.block-kind`
### 3.1 Closed Canonical Catalogue `block.kind-catalogue`
Every block declares `kind` at creation.

Message and instruction kinds:
- `InstructionSource` — durable instruction-source content (workspace rules, user rules, instruction fragments, committed policy notices); NOT the fully assembled model request
- `MessageUser` — user transcript input; by default message text is one primary block, attachments/mentions/quoted prior blocks/structured parts linked as children when structure needed
- `MessageAssistant` — accepted assistant turn; typically `Composed` over final text + tool-call/tool-result/reasoning/validation/failure children

Reasoning kinds:
- `ReasoningTrace` — model's reasoning content (when exposed + policy permits retention); defaults `Sensitive`

Capability execution kinds:
- `ToolCallProposal` — structured args executor parsed from model's tool-call emission, committed before execution; carries resolved capability id, version, arguments, policy decision reference
- `ToolResult` — typed result after execution; may be `Inline` (small), `External` (large output as artifact), `Composed` (wraps several sub-results)
- `ToolDenial` — typed denial when policy blocks a proposed call [`run.denial-is-in-band`]; contains policy reason, lease/floor that fired, proposed payload reference
- `Failure` — user-visible/context-relevant failed or skipped output; carries `{ source, error_code, retryable, skipped_vs_failed, references }`; capability execution failures use `Failure { source: capability }`; policy denials remain `ToolDenial`

Observation and evidence kinds:
- `Observation` — structured world observation (file content snapshot, accessibility tree snapshot, screenshot reference, status query result, browser DOM extract) committed for replay + policy revalidation [`run.call-pipeline`]
- `Evidence` — structured evidence record supporting a claim/output/action; carries citation references + typed claim it supports (full evidence semantics File 09)
- `Citation` — structured reference to external source (URL, document section, file range, prior block id, MCP resource); durable lookup key for provenance

Persistence-related kinds:
- `KnowledgeEntry` — curated knowledge-base content block; carries content, source references, sensitivity, scope, description; mutable curation state (tags, featured status, validation status, lifecycle, last-reference stats) belongs to KB entity layer
- `Memory` — memory entry promoted into durable cross-conversation knowledge; carries salience + decay metadata (full mechanics File 14)
- `Artifact` — block whose content is durable user-visible output (file, document, chart, notebook, lesson, code patch); `Inline` for small or `External` referencing artifact storage; identity/lifecycle/versioning/materialization/export belong to File 09; this kind is the block-level handle
- `FileAttachment` — block referring to a file in workspace; carries path, mtime, size, content hash, content-type; resolved against workspace state on read
- `SourceExcerpt` — deliberately committed excerpt from a source block/file/document/web page/retrieval result/graph traversal/direct lookup/manual selection; retrieval chunks, embedding segments, graph index nodes remain derived records unless intentionally committed as durable context

Planning and validation kinds:
- `Plan` — structured plan record (steps, subtasks, dependencies); used by execution + task promotion [`intent.task`]; plan revisions create siblings linked by `supersedes`
- `Validation` — structured validation result (postcondition check, type check, lint result, evaluator score); referenced from runs + completion-verification hook surface [`run.termination`]
- `Critique` — structured critique/review record (critic agent review, code-review comment, QC note); distinct from `Validation` because critiques are evaluative judgments not pass/fail checks

Coordination kinds:
- `Group` — `Composed` block whose only purpose is grouping children into a unit (user-defined groups, automatic groups for parallel calls, comparison-board groupings)
- `Consolidation` — summary block from compaction consolidating prior blocks into condensed view; references consolidated blocks via `consolidates` edge
- `ContextNotice` — committed guardrail/hook/system notice retained for audit/replay/inspection; hook-injected guardrails, model-request transformations, transient assembly content are `Event`s or request-assembly facts by default, become blocks only when deliberately committed

Extension:
- `Custom { namespace, name }` — specialized kind registered by subsystem/surface/plugin/user-defined extension; `namespace` is registered extension namespace (matching [`capability.capability-source`]); `name` is kind id within namespace; register via same proposal-first mechanism as capabilities [`capability.runtime-mutation`] and must declare: allowed `BlockContent` variants; default sensitivity; whether allowed in transcript-anchoring positions; canonical edge kinds the kind participates in

Closed catalogue canonical for cross-cutting reasoning; `Custom` canonical for specialization; every block belongs to exactly one — no block ever has unparseable kind.

### 3.2 Kind Declaration
Each capability declaration [`capability.composition-fields`] names `output_block_kinds` it can produce; names drawn from this catalogue (closed canonical + registered `Custom`). A capability emitting undeclared kind is an Explicit Rejection (§15).

### 3.3 Kind Composition Rules `block.kind-composition-rules`
- `MessageUser`/`MessageAssistant` are transcript-anchor kinds; transcript (File 02) renders these as message lines; message line references a single block of one of these kinds, itself possibly `Composed`
- Message composition rules are defaults not hard limits on later editing; user/model may split into smaller siblings, merge into new `Composed`, group, tag via registered metadata, or edit via sibling-creation; originals remain immutable
- `ToolCallProposal`/`ToolResult` always live as children of a `MessageAssistant` block (the turn producing the call) or standalone in non-conversation context (automation run, inspector-initiated invocation); never appear as transcript-anchor blocks directly
- `Evidence` blocks must reference ≥1 `Citation`/`Observation`/prior content block via `cites` edges; evidence block with no supporting references = Explicit Rejection (§15)
- `Artifact` blocks must reference durable backing storage via `External` content when content exceeds inline-size threshold; oversized `Artifact` with `Inline` content = Explicit Rejection
- `Composed` blocks must reference ≥1 child via `children_block_ids`; `Composed` with no children = Explicit Rejection
- `Group` blocks are by definition `Composed`
- `ReasoningTrace` defaults `Sensitive`, never defaults `Public`
- `Memory` defaults `Sensitive` when content originates from user-private context

Enforced at commit by block commit validator (§8.2); violations produce typed `BlockCommitRejected` error flowing through standard execution-failure path.

### 3.4 Custom Extension
`Custom { namespace, name }` registered via a capability call (matching [`capability.runtime-mutation`] proposal-first). Registration declares: `allowed_content_variants`; `default_sensitivity`; `transcript_anchorable` (default false); `permitted_parent_kinds` (closed list of `BlockKind`s or `Any`); `permitted_child_kinds` (closed list or `Any`); `default_edges` (canonical edges §5 typically participated in); `description`. Registered custom kinds persist in registry [`capability.registered-capability`] under same registered-state envelope as capabilities + same source-trust narrowing rules [`policy.source-approval-flow`]. A custom kind cannot violate composition rules; structurally invalid declaration is rejected.

### 3.5 Boundary
Kind catalogue defines what kinds of content the system reasons about; not how rendered/stored/retrieved. UI/storage/retrieval consume the catalogue, don't extend it.

## 4. `BlockContent` `block.block-content`
### 4.1 Required Shape — three discriminated variants chosen by producer at commit, fixed:
- `Inline { text }` — content is UTF-8 string in block record; for short content where indirection cost exceeds inline cost (text fragments, structured JSON under inline-size threshold, tool args, citations, descriptions)
- `External { storage_ref, size_bytes, content_type, external_content_hash }` — content lives outside block at registered storage reference; block stores only reference; for large content (attachments above threshold, screenshot images, archive blobs, generated artifacts); `storage_ref` names resolver kind, scope, identity, size, content type, integrity hash where available; remote URL is citation/source reference unless content captured into durable storage
- `Composed { children_block_ids }` — block has no own content; content is ordered concatenation (structural sense, not necessarily textual) of children; canonical mechanism for structured-content blocks built from typed sub-parts (`MessageAssistant` of text+tool calls+tool results; `MessageUser` of text+attachments+mentions; `Artifact` group of file revisions)

### 4.2 Inline-Size Threshold `block.inline-size-threshold`
Settings dimension (§14). Kinds whose `allowed_content_variants` include both: content below threshold = `Inline`, at/above = `External`. Decided at commit, fixed for lifetime; an `Inline`-committed block is not re-encoded to `External` if threshold later changes.

### 4.3 Composition Resolution
A `Composed` block resolves by reading `children_block_ids` in order, resolving each child recursively. Shallow at storage (stores ids), deep at read (resolved tree). Read-time operation; composed block doesn't cache resolved content. If a child is `Masked`/`Dropped` in current `ContextVersion`'s view (§6), resolution result for that child is the masked/dropped placeholder (typed sentinel with child's id, kind, description but not content); does not re-fetch dropped children's content silently.

### 4.4 Cross-Reference vs Containment `block.cross-reference-vs-containment`
`Composed` = containment (children are parts). A block may also reference others without containing (`Validation` references blocks it validated; `Critique` references block it critiques; `MessageAssistant` references prior messages it responds to). References = typed edges (§5), not composition. Load-bearing distinction: removing a child from `Composed` (forbidden by §2) would change what the composed block is; removing a referenced block doesn't change what the referencer is, only what context it can resolve.

### 4.5 Content Hash `block.content-hash`
Every block carries `content_hash` (SHA-256, 32 bytes) computed at creation over canonical content encoding (`CanonicalEncoding` per [`core.canonical-encoding`] + global hashing rule [`core.canonical-hash`]), not physical storage bytes. Encoding covers: block kind; content variant discriminator; inline payload or external reference descriptor; composed child references (child order preserved only where composition order is semantic, declared order-sensitive per [`core.canonical-encoding`]); the `block_schema_version`. `content_hash` is computed over full canonical content and must not omit `Sensitive` fields (identity+integrity hash; stripping fields would make materially different blocks hash identically and corrupt dedup; raw `Secret` material never appears in inline content per [`secret.backend-boundary`]). A redacted/rendered projection's own hash is a separate `projection_hash`; `projection_hash` must never be used for block identity/dedup/equality; only `content_hash` carries identity.

Hash domain by variant: `Inline { text }` = hash of canonical UTF-8 bytes of `text` + `Inline` discriminator; `External {…}` = hash of canonical storage reference identity, size, content type, external payload hash when known (future external-byte changes don't silently change identity); `Composed {…}` = structural hash over child sequence of `(child_block_id, child_content_hash)` pairs, order-sensitive (composition order semantic); lifecycle changes (mask/drop/recover) don't change hash, child content replacement does.

Supports cross-session/cross-device dedup (storage may share storage for identical content hashes when structurally equal), materialized-view integrity verification, model-request-prefix cache correlation [`run.ledger-events-commits`, `surface.cache-friendly-ordering`], replay-time content equality. Cross-device dedup/content-addressing requires same canonical content encoding version; hash equality across differing encoding versions not a correctness basis [`core.canonical-hash`]. Hash is `NOT NULL` and immutable.

### 4.6 Boundary
Content shape defines what a block contains; version graph decides which active; storage decides on-disk layout; retrieval decides indexing. None redefine content shape.

## 5. `BlockEdge` and the Block Graph `block.block-edge-block-graph`
### 5.1 Definition
A `BlockEdge` is a typed labeled directed relation between two blocks. Parent + composition relations are structural fields exposed as derived edge views; non-structural relations are explicit committed edge records. Structural views + explicit records form the `BlockGraph`. Every explicit edge: `edge_id` (optional in storage; derivable from `(from_block_id, to_block_id, edge_kind, sequence_in_kind)`); `from_block_id`; `to_block_id`; `edge_kind` (`BlockEdgeKind` §5.2); `metadata` (typed per edge kind — `attaches_to` may carry offset, `cites` a span reference, `derives_from` a transformation summary; schema part of edge kind declaration); `created_at`. Edges committed at same boundaries as blocks (§7.6); immutable like blocks (stale edge left in place, future changes commit new edges); graph append-only.

### 5.2 Canonical Edge Kinds `block.canonical-edge-kinds` — closed catalogue:
- `parent` — structural causal parent; block's `parent_block_id` is canonical truth, graph queries expose as derived edge; used by ancestor walks + conversation-context reconstruction
- `contains` — composition edge; a `Composed` block's `children_block_ids` are canonical truth, exposed as ordered derived edges; used by content resolution
- `supersedes` — non-destructive edit replacement; edit creates new block + `supersedes` edge from new to prior; version graph uses it to advance "current" pointer; closure = version chain
- `derives_from` — derivation provenance; new block's content produced by transforming/summarizing/translating/extracting from source; used by provenance queries, evidence chains, compaction
- `cites` — citation; source `Evidence`/`Claim` block, target `Citation`/`Observation`/external reference block; closure = evidence chain
- `witnesses` — observational provenance; content committed because source block was observed (screenshot triggered UI action; file-read triggered edit); used by replay + stale-state revalidation
- `references` — weak content reference; mentions/links/contextually depends without containing or deriving (`MessageAssistant`→prior message; `Plan`→`Task`); used by surface presentation + cross-block navigation
- `follows_in_transcript` — strict transcript ordering; source any transcript-anchorable block, target prior transcript-anchorable block in same conversation; used by transcript reconstruction independent of timestamp ordering; version graph determines active transcript chain, this edge encodes local "previous transcript message" link
- `consolidates` — compaction provenance; summary/compaction block consolidates prior blocks into condensed view; source = consolidation block, targets = consolidated blocks; used by compaction lifecycle + "expand to original" affordances
- `materialized_by` — composition fallback; when a `Composed` block's children hard-deleted (§6.6), runtime may materialize resolved content as new `Inline`/`External` block linked by `materialized_by` to now-dangling composed parent; preserves resolved-content history when children's storage destroyed
- `promotes_scope_of` — scope promotion; source broader-scope block/reference record, target original narrower-scope block; content intentionally made addressable in broader scope without treating original as obsolete
- `scope_projection_of` — scope projection; source scoped reference record, target original block; broader-scope object is addressability projection not content copy
- `attaches_to` — workspace anchor; source a block, target workspace path/conversation node/task/run; carries offset/position metadata when applicable; used by surface rendering + world-model state-awareness service [`core.world-model`]
- `validated_by` — block validation; source any block, target a `Validation`/`Critique` block whose target is the source; closure shows every validation recorded for a block
- `responds_to` — request/response chain; source produced in response to target, target the eliciting block; used in tool-call chains (`ToolResult` `responds_to` `ToolCallProposal`) + clarification dialogs
- `conditioned_on` — explicit dependency; source whose meaning depends on target being present (`Plan` step→preceding task; workflow node→predecessor)

### 5.3 Edge Extension
Subsystems/plugins may register edge kinds via same extension plane as `Custom` block kinds. Registered edge declares: `namespace`+`name` (matching [`capability.capability-source`]); `from_kinds` (closed list of `BlockKind`s or `Any`); `to_kinds` (closed list or `Any`); `metadata_schema`; `transitive` (whether closure is meaningful / ancestor walks follow it); `description`.

### 5.4 Graph Properties
- acyclic in structural composition + lineage (`parent`, `contains`, structural use of `supersedes`); cycles would violate content resolution/edit history/version-graph contract
- possibly cyclic in reference + provenance edges (`references`,`cites`,`witnesses`,`attaches_to`,`validated_by`,`responds_to`,`conditioned_on`,`derives_from`,`consolidates`,`materialized_by`) unless declaration explicitly forbids
- append-only; stale edge left in place, version graph determines active source/target
- inspectable via canonical block-graph queries: ancestor walk by edge kind, descendant walk by edge kind, sibling enumeration (same `parent_block_id`), supersession chain (closure under `supersedes`), citation network (closure under `cites`)

### 5.5 Boundary
Block graph defines structural relations; version graph defines which subset is "current"; ledger records committing events; retrieval indexes edges. File 08 owns edge catalogue + structural invariants.

## 6. Block Lifecycle and Non-Destructive Edits `block.block-lifecycle-non-destructive-edits`
### 6.1 Definition
`BlockLifecycle` = runtime view-state of a block within a `ContextVersion`:
- `Raw` — exists in pool, not yet activated in any view; transient between commit + first inclusion
- `Active` — part of current view; rendered, included in context assembly, eligible for retrieval
- `Masked` — hidden from current view but reachable via explicit "show masked" affordances / version-graph navigation; not in context assembly by default
- `Dropped` — hidden from current view + not eligible for retrieval; reachable only via explicit recovery; storage retained
- `Recovered` — previously dropped, brought back; semantically equivalent to `Active` but carries historical mark for inspector display

`PinState` = user's explicit retention preference within a view:
- `Unpinned` — default; subject to compaction by default policies
- `Pinned` — user requests preservation during compaction
- `Protected` — strongest; excluded from compaction algorithms entirely until explicitly unprotected

Lifecycle + pin state derived from version graph's action log over the block pool, not stored on block. Same block may be `Active` in one version, `Masked` in another; switching active version updates view without mutating any block record.

### 6.2 Edit Semantics `block.edit-semantics`
Editing observable content does not mutate the block; creates a new block in same pool linked to prior by `supersedes` edge (§5.2). New block: fresh `block_id`; new content under appropriate `BlockContent` variant; prior block's id as target of `supersedes`; new `content_hash`; fresh `created_at`; `producer` reflecting edit source (`UserMessage` edit, `InspectorApply`, automated transformation). Version graph advances "current" pointer; prior remains in pool immutable, reachable via version-graph navigation + `supersedes` chain. Editing a `Composed` block's children (add/remove/reorder) is itself an edit: new `Composed` block with new `children_block_ids` + `supersedes` edge to prior; children unchanged. Editing metadata (description, default sensitivity, source attribution) follows same rule: metadata part of identity at creation, observable change creates a new sibling.

### 6.3 Mask, Drop, Recover `block.mask-drop-recover` — version-graph operations changing view's lifecycle map without touching pool:
- `Mask(block_id)` — version's lifecycle map → `Masked`; remains stored + addressable; future versions branching inherit masked state until explicitly unmasked
- `Drop(block_id)` — → `Dropped`; same storage/addressability as masked; excluded from retrieval + default context assembly
- `Recover(block_id)` — `Masked`/`Dropped` → `Active` in current view; surface presentations resume; retrieval indexing re-enables

Committed as version-graph entries, not block mutations; emit `BlockLifecycleChanged` events [`run.event-stream`]; recorded in execution ledger.

### 6.4 Pin and Protect `block.pin-protect` — modify pin state in current version's pin map:
- `Pin(block_id)` — user-preferred for retention; compaction respects by default
- `Unpin(block_id)` — removes pin
- `Protect(block_id)` — strongest; compaction skips entirely
- `Unprotect(block_id)` — removes protection

Live on the version, emit `BlockPinChanged` events.

### 6.5 Group and Ungroup `block.group-ungroup`
`Group(block_ids)` creates a new `Group`-kind `Composed` block whose children are the named blocks; grouped blocks unchanged; group block is new container. `Ungroup(group_block_id)` is an edit: new version-graph entry dissolves the group's presence in current view; group block not destroyed; future versions may re-enable.

### 6.6 Hard Delete `block.hard-delete` — only operation physically destroying recoverable payload storage:
- explicitly user-initiated (no automatic; compaction never hard-deletes)
- typed-confirmation required when block referenced by `Composed` parent, non-superseded `supersedes` chain, `Evidence` chain, or any version other than current [`policy.permission-floor-typed-confirmation`]
- recorded in ledger as `BlockHardDeleted` event with deleting actor, block id, references that would be orphaned
- accompanied by minimal tombstone retaining `block_id`, deletion time, deletion actor/source, `conversation_id`, `scope`, `parent_block_id`, prior kind if safe, sensitivity-safe reason/description; payload bytes/secret fields/embeddings/indexed text/external blobs removed; references resolve to typed deleted-block placeholder
- composition-materialization: if a `Composed` block depends on deleted block as child, runtime materializes resolved content into new block (linked by `materialized_by`); if materialization fails (content not reconstructible from descriptions), composed block → typed `MaterializationOrphaned` state, surface shows missing-child placeholder
- reference-edge cleanup: edges from/to deleted block become orphan-marked; closure queries report dangling state explicitly

Canonical mechanism for honoring user storage-management requests [`core.non-destructive-by-default`'s "manage and reclaim storage at every granularity"] + credential/secret expungement; never automatic; tombstone retention safe default but deletion history user-manageable via explicit policy-governed cleanup.

### 6.7 Lifecycle Transition Rules `block.lifecycle-transition-rules` — explicit + deterministic:
`Raw → Active` (first inclusion); `Active → Masked` (explicit mask); `Active → Dropped` (explicit drop); `Masked → Active` (explicit unmask); `Masked → Dropped` (explicit drop while masked); `Dropped → Recovered` (explicit recover; `Recovered` is `Active`+historical mark); `Recovered → Active` (implicit, recovered is an `Active` variant); `Recovered → Masked`/`Recovered → Dropped` (explicit, same as `Active`). No time-based transition permitted; no auto-mask-after-N-turns at block layer (File 01 constraint). Compaction may invoke explicit `Mask`/`Drop`, but block layer enforces no implicit decay.

### 6.8 Boundary
Lifecycle is view-state owned by version graph; this file defines state set + transition rules; version-graph spec owns action log + per-version materialized view. Block pool remains append-only + lifecycle-agnostic.

## 7. Streaming and the Commit Boundary `block.streaming-commit-boundary`
### 7.1 Definition
Block streaming = producer (model generating text, executing capability emitting partials) commits output as a `Block` at producer's declared commit boundary. Streaming happens via `Event`s [`run.event-stream`]; blocks exist only at commit point.

### 7.2 Event-Then-Block Pattern:
1. Producer emits partial output; each partial flows as typed `Event` carrying standard envelope + `partial_block_handle` naming eventual block id
2. Surfaces consume events live (streaming UI, live tool-output rendering); events not durable history, live coordination
3. At declared commit boundary (model finishes, capability completes, executor accepts final structured payload), runtime commits a `Block` with accumulated content
4. Committed block carries same `block_id` named in partial-block handle for correlation
5. Surfaces switch from live-event to durable-block rendering on commit; visual transition implementation-defined; substantive: events discarded (or retained per [`run.event-stream`] sensitivity rules), block is durable record

### 7.3 Partial-Block Orphans `block.partial-block-orphans`
If producer fails before commit (cancellation/error/timeout/crash), no committed block yet. Runtime may retain staged partial records tied to run; staged partials cancellable, configurable, outside block pool until promoted through normal commit validator. Subject to: [`run.cancellation`] rules — `partial_output_meaningful` (declared on capability) determines preserve-as-orphan vs discard; if preserved, runtime may promote staged partial to a partial `Block` with kind matching producer's declared output kind, content reflecting what was streamed, typed `partial_orphan` marker in metadata (participates in graph normally, inspectable); if discarded, no block committed, partial events retained in event stream per standard retention but not promoted. Decision per capability at registration [`run.call-pipeline`], overridable at cancellation by user [`run.cancellation`].

### 7.4 Tool-Input vs Tool-Output Streaming
[`run.streaming-partial-execution`] distinguishes the two halves; committed same way: tool-input streaming — model still emitting tool-call args; at commit (model finishes call, executor enters pipeline) commit `ToolCallProposal` with final args. Tool-output streaming — executing capability emitting partial results; at commit (capability's declared commit point) commit `ToolResult` with final result. Two commits may happen at different times for same call; both produce blocks in same pool, linked by `responds_to` edges.

### 7.5 Live-Partial-Write Capabilities `block.live-partial-write-capabilities`
For capabilities supporting live partial-write into materialized state [`run.streaming-partial-execution` file-or-artifact write: stage in temp file, atomic rename at commit], block-layer commit aligns with executor's atomic-rename point; block committed when capability declares success; staged temp file becomes durable artifact at same boundary; `Artifact` block points to now-durable location. If live-write cancelled mid-stream, temp file deleted [`run.streaming-partial-execution`], no `Artifact` block committed; partial events retained/discarded per §7.3.

### 7.6 Commit Boundary Set `block.commit-boundary-set` — canonical block-commit boundaries:
- user submits message → `MessageUser` block (+ `Composed` children for attachments/mentions/quoted blocks)
- assistant turn reaches accepted final state → `MessageAssistant` + constituent `ToolCallProposal`/`ToolResult`/`ReasoningTrace`/text children
- capability invocation completes (success / typed failure / policy denial) → `ToolCallProposal` + `ToolResult`/`Failure`/`ToolDenial` blocks
- router emits route record → durable route/run record; blocks may reference it when history needs visible route inspection
- inspector applies state-changing operation (pin/drop/edit) → version-graph entry with associated block creates / edge updates
- workflow node completes → block matching node's declared output kind
- import operation succeeds → block(s) for imported content
- consolidation completes → `Consolidation`-related blocks + `consolidates` edges
- user explicitly commits a draft (manual block-commit affordance in inspector)
- subsystem internal commit (memory promotion, evidence-chain commit, equivalent) hits declared boundary

Each boundary = one version-graph commit + one ledger entry. Between boundaries, work staged in pending-operations buffer [`run.version-commits`] as events not blocks; buffer accumulates incremental work; block commit is atomic durable promotion.

### 7.7 Boundary
Streaming owned by File 04 + event stream; this file owns durability contract (where streaming becomes a block, what block looks like at commit, cancellation interaction); version-graph spec owns the version-graph entry recording the commit.

## 8. Identity, Validation, and Hashing `block.identity-validation-hashing`
### 8.1 Identity — a `block_id` is:
globally unique within installation; assigned at commit (or at first event emission for streaming blocks, handle reserved at stream start, commit promotes reserved id to durable block); never reused/reassigned/mutated; canonical cross-layer reference (events carry it, ledger records it, version-graph entries name it, capability invocations attribute output to it, surface projections render it); format-agnostic at this layer (UUID-v7, ULID, or equivalent with required uniqueness + orderability; storage spec picks wire format). Identity independent of content; two blocks with identical content have different ids; dedup uses `content_hash` as separate dimension (§4.5).

### 8.2 Block Commit Validator `block.block-commit-validator` — before admission to pool:
1. Identity validation: `block_id` well-formed, not already in use
2. Kind validation: `kind` canonical or registered `Custom { namespace, name }`
3. Content-variant validation: chosen `BlockContent` variant permitted by kind's `allowed_content_variants` (closed for canonical, declared for custom)
4. Composition validation: for `Composed`, `children_block_ids` non-empty, all child ids exist, no cycles in resulting structural graph
5. Edge validation: committed edges have `from_block_id`/`to_block_id` resolving to existing blocks (or just-committed block); kind-level edge constraints (§5) satisfied
6. Parent validation: `parent_block_id` (if set) resolves to existing block, parent's kind permits child's kind under `permitted_parent_kinds`
7. Producer validation: `producer` well-typed, corresponds to known producer source (capability registry for capability commits, conversation/user-id for user messages)
8. Sensitivity validation: `default_sensitivity` canonical; per-field map references valid field paths; composed blocks must not underreport max effective sensitivity of children unless policy-approved typed-confirmation override applies
9. Description validation: `description` non-empty for kinds requiring it (all canonical; custom may opt out only when declaration specifies)
10. Hash validation: content hash computable from content + variant discriminator + `block_schema_version`, matches supplied `content_hash`
11. Scope validation: declared `scope` canonical + compatible with producer (`run`-scoped needs `origin_run_id`; `workspace`-scoped needs workspace context)

Failed validation = typed `BlockCommitRejected` per [`run.denial-is-in-band`]'s in-band denial; producer receives typed error, may retry with corrected input/escalate/abort.

### 8.3 Hash Collision
SHA-256 makes practical collision negligible. No collision-recovery path beyond logging high-severity `ContentHashCollisionSuspected` event when two distinct blocks share a hash at storage. Storage may use hash for dedup only when blocks also structurally equal; hash match alone is not identity.

### 8.4 Cross-Reference Rules
References block→block (via `parent_block_id`, `children_block_ids`, edges, content embeddings) use `block_id` as canonical key. References to external resources use registered storage references or typed source references captured at commit; uncaptured remote URLs are citations not durable payload storage. References to capabilities use `(capability_id, capability_version)` [`capability.identity-namespacing-versioning`]. References to events use `(event_envelope, sequence)` [`run.event-stream`]. A block whose committed references resolve to non-existent targets at read time produces typed `BrokenBlockReference` event but doesn't corrupt the block — reference immutable, only target existence changed.

### 8.5 Boundary
Identity/validation/hashing are commit-time concerns owned here; storage of fields + propagation to surfaces owned by future storage + UI specs; indexing owned by File 12.

## 9. Sensitivity `block.sensitivity`
### 9.1 Definition — durable counterpart to event sensitivity [`run.event-stream`]; `default_sensitivity` values:
- `Public` — may appear in shareable exports, may be cached by external services handling public content (provider-side model-request caches when provider permits), persisted in durable ledger without redaction
- `Sensitive` — user-private/workspace-specific; excluded from shareable exports + clipboard-copy unless user explicitly overrides; persisted in durable ledger; subject to shorter default retention if settings configure
- `Secret` — credentials, raw API keys, OAuth tokens, password content, equivalent never-leak material; persisted to durable pool with redacted content (redaction at commit; original raw secret held only in transient memory, zeroed after use); `description` summarizes what without revealing (e.g. "AWS access key for production environment"); not retrievable through search, not in compaction content review, not exported under any standard share/export path

### 9.2 Per-Field Override `block.per-field-override`
Optional `sensitivity_field_map` overrides default per JSON-path-style field reference into content. Example: `ToolResult` content `{ stdout, stderr, credential_used }` may declare `default_sensitivity: Sensitive` + override `$.credential_used: Secret`. Rendering/export/retrieval respect the map.

### 9.3 Inheritance Through Composition
A `Composed` block's effective sensitivity = max of declared `default_sensitivity` and max effective sensitivity of children. `Public`-declared composed containing `Secret` child → effective `Secret`. Commit validator must prevent persisted underreporting: when effective is deterministically higher, validator auto-escalates declared to effective max + records inspectable warning event; if producer explicitly requested unsafe lowering, commit rejected unless policy allows typed-confirmation override. Rendering/export/indexing/caching always use effective sensitivity, never lower declared.

### 9.4 Producer-Seeded Defaults
Each `BlockKind` declares default sensitivity in its kind declaration (canonical + registered `Custom`). When a capability commits, executor uses capability's `data_sensitivity` [`capability.permission-policy-fields`] as producer-seeded value → block's `default_sensitivity`. Producer may override seed by emitting explicit value, subject to policy (cannot lower `Secret`-seeded to `Public` without typed-confirmation policy override).

### 9.5 Projection Independence
Sensitivity independent of presentation; a surface consumes effective sensitivity to decide rendering/export/copy; doesn't modify stored sensitivity; sensitivity is a property of durable content not presentation.

### 9.6 Boundary
Sensitivity is durable property; policy layer (File 06) decides what to do at policy boundaries based on it; event stream [`run.event-stream`] uses same value set for transient coordination; surface rendering consumes it to gate displays; none redefine the value set.

## 10. Block Description `block.block-description`
### 10.1 Definition
`description` — short structured NL description of contents, emitted by producer at commit; fixed at commit; future references use it for compaction, retrieval ranking, surface previews, discovery.

### 10.2 Producer Responsibility — at commit; for canonical kinds:
- `MessageUser`/`MessageAssistant` — derived from content (first N words / model-generated summary if configured); producer (conversation engine / executor) emits as part of commit
- `ToolCallProposal` — one-line `"<capability_id>(<argument_summary>)"`
- `ToolResult` — one-line: success/failure tag, key field values, byte count for large outputs
- `Observation` — one-line summary of what was observed
- `Artifact` — title/filename + one-line content summary
- `Memory`,`Plan`,`Evidence`,`Citation`,`Validation`,`Critique`,`ReasoningTrace`,`SourceExcerpt`,`Failure`,`ContextNotice` — kind-specific summary templates declared in kind's metadata

For `Custom` kinds, registration declares the description template, producer follows it.

### 10.3 Why Descriptions Are Committed Fields — live on block not in compaction service / retrieval index because:
compaction reads descriptions not full content to decide what to evict/summarize (description survives compaction); retrieval uses descriptions for low-cost first-pass filtering (full-content embeddings computed separately); surfaces render descriptions in collapsed/list/preview views; inspector lenses [`surface.inspector-lens`] render in catalogue displays; when content is `External`/`Composed`, description is the only inline content available (otherwise every preview requires full resolution).

### 10.4 Description Immutability `block.description-immutability`
Fixed at creation; inadequate description is edited (creates sibling per §6.2), not patched in place.

### 10.5 Boundary
Description owned by block; compaction/retrieval/surfaces consume it, don't modify it; richer description requested via capability call producing edit-sibling block.

## 11. Block Scope `block.block-scope`
### 11.1 Definition — `scope` = broadest context block is visible + addressable:
- `run` — visible only within originating `Run`; transient internal-coordination blocks; pruned with the run
- `intent_thread` — visible within originating intent thread, across runs sharing the thread
- `task` — visible within originating task, across runs advancing it
- `conversation` — visible within originating conversation; default for transcript-related blocks
- `workspace` — visible across conversations within workspace; default for workspace artifacts + workspace-scoped memory
- `global` — visible across workspaces; reserved for global memory entries, global settings blocks, equivalent
- `reusable_policy_rule` — matches lease scope from [`policy.lease-primitive`]; reserved for blocks expressing reusable policy/workflow templates

Scope declared at commit by producer; determines which surfaces/runs can address by id, which retrieval indices include it, which compaction policies eligible to evict, which export/share operations include it.

### 11.2 Scope Promotion `block.scope-promotion`
A block may be promoted to broader scope via explicit operation (pin `run`-scoped observation into `conversation`; agent promotes `task`-scoped plan into `workspace`). Promotion creates new immutable block / reference record at broader scope, linked to original by `promotes_scope_of` or `scope_projection_of`; original remains valid at original scope; `supersedes` reserved for content/version replacement not visibility broadening. Scope demotion (down to narrower) not permitted as direct operation; a workspace block later judged conversation-specific is left at workspace scope (retrieval/surface may filter it out, but declared scope fixed at commit).

### 11.3 Cross-Scope References `block.cross-scope-references`
A narrower-scope block may reference (via edges) a broader-scope block (`run`-scoped `ToolResult` may `references` a `workspace`-scoped `Memory`). A broader-scope block may reference a narrower-scope block only if references remain meaningful when narrower block no longer in scope (`workspace`-scoped `Plan` referencing `task`-scoped block must tolerate task's blocks being GC'd). Edge resolution at read time honors scope rules; unresolvable reference produces `BrokenBlockReference` event without corrupting referencer.

### 11.4 Boundary
Scope durable property; storage uses it to organize physical layout; retrieval uses it to bound queries; future workspace spec defines workspace boundary; this file uses workspaces as a scope label without redefining workspace semantics.

## 12. Cross-Surface Interoperability `block.cross-surface-interoperability`
### 12.1 Definition
One block pool. Every work surface (Coder, Web, Data Processor, Teacher, GUI Control, System Agent), every substrate service (Memory, Routing, Context Assembly, Retrieval, Knowledge, Settings, Evaluation, Policy, World Model, Perception, Storage), every control rail (Conversation, Palette, Voice, Shortcut, Automation), every external integration (MCP server, plugin, external API) reads/writes the same pool through the same block model.

### 12.2 Per-Surface Projections — each surface projects through surface-specific filters:
Coder filters for `FileAttachment`, `Artifact` (code), `ToolCallProposal`+`ToolResult` for code capabilities, `Validation` (tests), `Critique` (review comments); Web filters for `Observation` (page extracts), `Artifact` (downloads), `Citation` (URLs), `ToolCallProposal` for browser capabilities; conversation transcript filters for transcript-anchorable kinds (`MessageUser`,`MessageAssistant`, + child kinds); inspector lens [`surface.inspector-lens`] presents every block, filtered by user-chosen axes. Filter is a surface concern; blocks remain unchanged. A block produced by Coder but referenced by Memory is visible in both.

### 12.3 Cross-Surface Composition `block.cross-surface-composition`
A block may compose blocks from multiple surfaces; e.g. a `MessageAssistant` answering a research question composes: text children (conclusion); `Citation` children (web sources, committed by Web); `Artifact` children (generated code, committed by Coder); `Observation` children (files inspected, committed by File operations); `Evidence` children supporting the claim. Single `Composed` block in pool; each child at its appropriate scope; renders correctly in any surface supporting constituent kinds; surfaces not supporting some child kinds render typed placeholders ("[unsupported kind: …]") + link to inspector lens.

### 12.4 Boundary
Cross-surface interop is a property of the unified pool; this file establishes invariants; per-surface specs declare projection/filter/composition; no surface may introduce a private block pool, private kind catalogue, or private edge catalogue.

## 13. Block Persistence Contract `block.block-persistence-contract`
### 13.1 What Is Durably Stored `block.what-is-durably-stored`
block pool (every committed block survives restart/archive/version-graph ops until explicit hard delete); edge set (every committed edge survives); per-block metadata (`block_id`,`kind`,`content`,`parent_block_id`,`producer`,`origin_run_id`,`conversation_id`,`created_at`,`block_schema_version`,`content_hash`,`source_attribution`,`default_sensitivity`,`sensitivity_field_map`,`description`,`scope`); version graph (version nodes, lifecycle action logs, pin maps; survives restart); block-related ledger events (every block commit, lifecycle transition, edge commit → ledger entry).

### 13.2 What Is Computed `block.what-is-computed`
per-version lifecycle maps (derived from version-graph action log; rebuilt on demand from durable action records); per-version pin maps (same); materialized view of "blocks active in current view, in render order" (derived from version graph + surface projection filter); per-tokenizer token counts (computed on demand per `(block_id, tokenizer_id)`, never cached as plain scalar [`core.explicit-rejections`]); per-block retrieval relevance scores (retrieval service); per-block embedding vectors (indexing service, model-keyed identifiers).

### 13.3 Reconstruction Across Restart `block.reconstruction-across-restart`
On restart, block pool re-emerges from durable storage; version graph reloads; per-version lifecycle + pin maps rebuild from action log; in-flight uncommitted streaming events follow orphan-run rules of [`run.cancellation`] — partial events whose producing run was orphaned don't become blocks unless capability declared `partial_output_meaningful` + recovery handler. Active view a new run sees after restart = same view it would have seen before, modulo offline-interval changes. Determinism required for replay.

### 13.4 Reconstruction Across Retry, Edit, Reroute, Branch `block.reconstruction-across-retry-edit-reroute-branch`
Per [`run.retry-reroute-branch`], retry/edit/reroute/branch produce new runs linked to prior; block pool shared (new run's blocks join same pool); version graph records the branch; lifecycle maps may diverge across branches (one masks a block another keeps active); block records remain singular.

### 13.5 Boundary
Persistence is storage layer's responsibility; this file specifies what must be persisted (field set above) + reconstructed (computed views); schema/replication/sync/import/export owned by future storage/sync/import/export specs.

## 14. Settings `block.settings`
### 14.1 Configurable Dimensions — every block-presentation/retention/discovery mechanism configurable via settings [`core.settings-system`]; File 08 names dimensions, settings system owns cascade+storage:

Surface-presentation:
- `blocks.inline_size_threshold_bytes` — boundary between `Inline`/`External` for kinds permitting both; default settings-profile-dependent
- `blocks.description_visibility` — descriptions render in collapsed views (always/hover/never)
- `blocks.expansion_default` — `Composed` blocks render expanded/collapsed by default in transcript+inspector
- `blocks.cross_surface_render_strategy` — when surface encounters non-native kind: generic typed placeholder / link to inspector / kind-specific fallback

Retention:
- `blocks.hard_delete_confirmation_threshold` — typed-confirmation requirements for hard delete [`policy.permission-floor-typed-confirmation`]; per-kind override allowed
- `blocks.orphan_retention_policy` — keep partial orphans / discard / per-kind override (default keep when `partial_output_meaningful: true`)
- `blocks.compaction_default_policy` — default compaction policy for non-pinned blocks; File 13 owns policy set

Sensitivity:
- `blocks.export_sensitivity_filter` — minimum sensitivity excluded from exports (default: `Sensitive` excluded; `Secret` always excluded)
- `blocks.copy_to_clipboard_sensitivity_filter` — same set, clipboard
- `blocks.redaction_strategy` — how `Secret` content rendered (kind-only label / structured surrogate / fully omitted)

Custom-kind:
- `blocks.allow_custom_kinds_from_source.<source_id>` — per-source toggle for accepting custom kind registrations
- `blocks.custom_kind_review_threshold` — source-approval flow threshold for new custom kinds [`policy.source-approval-flow`]

Description:
- `blocks.description_max_length_chars` — soft cap at commit; producers above cap emit truncated description
- `blocks.description_regeneration_enabled` — whether user may request regenerated description (creates sibling edit)

Agent-exposure [`policy.agent-exposure-policy-settings`]:
- `blocks.kind_catalogue_visible_to_agent` — whether model sees full canonical kind catalogue in model-request text content (default `InModelRequest` for canonical kinds; custom kinds `OnRequest`)
- `blocks.sensitivity_exposure` — whether sensitivity visible to agent (`InModelRequest` for `Public`/`Sensitive`/`Secret` indicators; `Hidden` for `sensitivity_field_map` detail)
- `blocks.description_visible_to_agent` — whether other blocks' descriptions appear in agent's compaction-eligible content (`InModelRequest`)

### 14.2 Settings-Key Convention
`blocks.<dimension>`; per-kind `blocks.<dimension>.kind.<kind_name>`; per-source `blocks.<dimension>.source.<source_id>`; plugin/subsystem-registered custom kinds may register own kind-specific keys.

### 14.3 Boundary
This file names dimensions; settings system owns cascade resolution + storage + inspector UI; per-dimension defaults belong to tested settings profiles not hardcoded constants.

## 15. Explicit Rejections `block.explicit-rejections`
- mutable block content — every observable content change is a new block linked by `supersedes`; in-place mutation of `content`/`kind`/`parent_block_id`/`created_at`/`content_hash`/`producer` invalid
- in-place lifecycle storage on block row — `BlockLifecycle`+`PinState` live on version-graph per-version maps not the block; storing on block would force every mask/drop/pin to mutate block row + break immutability
- private per-surface or per-capability block models — one pool + one model; surface/capability specs project, don't own private pools
- implicit inferred edges from content patterns — parent+composition are structural fields exposed as derived edge views; every non-structural relation is an explicit committed edge record
- open block kinds without canonical baseline — kind set closed canonical + registered `Custom`; unparseable kind invalid; adding to baseline requires canonical spec update
- silent kind shadowing — two extensions registering `Custom` kinds with same `(namespace, name)`: registry rejects second; no silent override
- live events as durable history — events are coordination not the block; block committed at producer's declared boundary; treating events as source of truth bypasses durability+immutability
- block IDs lacking global uniqueness/stable ordering/that get reassigned — every id unique, stable, never reused
- per-surface block-id namespaces — every block has one id in one namespace
- silent hard delete — always explicit, typed-confirmation-gated when references depend, always recorded in ledger
- automatic mask-after-time-window — time-based block lifecycle transitions forbidden (File 01); compaction may invoke explicit `Mask`/`Drop`, block layer enforces no implicit decay
- forcing every event into a block — streaming model commits blocks at boundaries; not every event becomes durable
- block content carrying a token-count scalar — token counts model-dependent, keyed by tokenizer id [`core.explicit-rejections`]; blocks store content not unkeyed scalars
- block content carrying a cost scalar — same rule; cost computed per-model [`core.explicit-rejections`]
- `Composed` blocks whose children list mutates — children list immutable like content; add/remove a child creates a sibling composed block
- `Composed` blocks with no children — invalid composition
- `Evidence` blocks without any supporting `cites` edges — invalid evidence
- mixed-sensitivity blocks where declared underreports effective — commit validation must auto-escalate when deterministic or reject when unsafe lowering explicitly requested without policy approval
- block descriptions regenerated in place — descriptions immutable like content; new description = new sibling block
- treating `Block` and `Message` as same primitive — `Message` is a transcript anchor (File 02); `Block` is durable structured content; one message anchors one primary block (possibly composed); one block may participate in many messages or none
- treating `Block` and `Event` as same primitive — events live coordination, blocks durable history; commit boundary separates them
- treating `Block` and `Artifact` as same primitive — artifact-kind blocks are block-level handles; artifact identity/lifecycle/versioning/materialization/export/UI owned by artifacts/provenance layer; same boundary for Evidence, Memory, equivalents
- treating `Block` and `Capability` as same primitive — capabilities are typed operations (File 05); blocks are durable content those operations produce
- treating `Block` and `Ledger Entry` as same primitive — ledger is durable execution-history record, block is durable content-bearing record; both durable, record different things; a `ToolResult` block + the ledger entry coexist + link through cross-references not a canonical join-table block kind
- silent compaction without ledger record — every mask/drop/consolidation emits corresponding `BlockLifecycleChanged`/`BlockConsolidated` event into ledger
- forcing block storage layout into the canonical model — canonical model defines durable contract; storage chooses physical layout; no claim about row vs document vs columnar
- claiming "the block kind catalogue must remain unchanged forever" — catalogue evolves through canonical-spec updates; `Custom` covers runtime extension, canonical evolution covers structural growth
- using block ordering as sequence truth — sequence within a view owned by version graph; blocks not ordered by `created_at` alone

## 16. Consequences for Later Specs `block.consequences-for-later-specs`
- Artifacts/claims/evidence/provenance spec must define entity-level lifecycle over `Artifact`,`Evidence`,`Citation`, claim-related blocks without an incompatible content carrier.
- Ledger/event-stream/hooks spec must record block commits, edge commits, lifecycle transitions, hard deletes, tombstones, policy-related block events; ledger rows may reference `block_id`, must not duplicate block content.
- Version-graph spec must store per-version lifecycle/pin/ordering/action-log state over the pool; must not store block content.
- Retrieval/indexing/KB spec must treat vector/BM25/graph/embedding indexes as rebuildable projections over blocks; retrieval may return committed `SourceExcerpt` blocks only when excerpts deliberately promoted to durable context.
- Context-assembly/compaction spec must assemble from active block projection, respecting pin state, sensitivity, scope, committed descriptions; compaction invokes explicit block lifecycle operations, never mutates content.
- Memory spec must treat memory entries as `Memory`-kind blocks while owning salience/decay/recall/management.
- Provider + model-strategy specs must render blocks into provider-native model requests without treating assembled request text as ordinary durable blocks.
- Storage/sync/import/export/portability specs must preserve block identity, schema version, content, structural fields, edges, tombstones, sensitivity; physical layout subordinate to this contract.
- Security/credential specs must treat `Secret` sensitivity + per-field sensitivity maps as hard policy inputs; raw secrets redacted/transient per security spec, never leaked through descriptions/indexes/exports/telemetry.
- Workspaces/materialization/surface specs must project the shared pool; no surface/workspace/plugin/MCP integration/automation/workflow/QC/telemetry/runtime service/packaging layer may introduce a parallel block model, private pool, parallel capability metadata, or capability-like primitive bypassing Files 05-08 contracts.

Specific integration contracts stated in those files when written.
