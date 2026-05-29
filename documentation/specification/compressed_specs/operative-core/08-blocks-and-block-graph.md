# Blocks and Block Graph

## 1. Chosen Model {block.chosen-model}
One `Block` model + one `BlockGraph`.
Every durable structured content MUST be a `Block`; relations form the `BlockGraph`.
A `Block` MUST be immutable after creation.
A `Block` MUST be typed with a `BlockKind` from the closed catalogue (§3); `Custom { namespace, name }` extension registered through the same extension plane as capabilities.
A `Composed` block MUST have no `Inline`/`External` payload and MUST carry ordered `children_block_ids`.
A `Block` MUST be addressable by stable `block_id`.
Every observable change MUST be a new block in the same pool, prior preserved, linked by typed edge; in-place mutation PROHIBITED.
The structural composition subgraph MUST be acyclic.
Every block MUST enter via a declared producer; "events become blocks" silent promotion PROHIBITED.
Canonical noun MUST be `Block`.

## 2. `Block` {block.block}
Required fields (minimum): `block_id`, `kind`, `content`, `parent_block_id`, `producer`, `origin_run_id`, `conversation_id`, `created_at`, `block_schema_version`, `content_hash`, `source_attribution`, `default_sensitivity`, `description`, `scope`.
`producer` variants: `UserMessage`, `CapabilityCommit`, `RouterEmission`, `InspectorApply`, `WorkflowNode`, `Import`, `Consolidation`, `Subsystem`.
For `Composed`, ordered child list MUST live only inside `BlockContent.Composed { children_block_ids }`.
Block model MUST be wire-stable through `block_schema_version`, `BlockKind`, `BlockContent` discriminators.
Adding a top-level enum variant MUST be a canonical-spec change, not runtime registration.
Storage/import MUST validate supported block schema versions and explicitly upgrade or reject unsupported; silent reinterpretation PROHIBITED.

## 3. `BlockKind` {block.block-kind}
### 3.1 Closed Canonical Catalogue {block.kind-catalogue}
Every block MUST declare `kind` at creation.
Catalogue: `InstructionSource`, `MessageUser`, `MessageAssistant`, `ReasoningTrace`, `ToolCallProposal`, `ToolResult`, `ToolDenial`, `Failure`, `Observation`, `Evidence`, `Citation`, `KnowledgeEntry`, `Memory`, `Artifact`, `FileAttachment`, `SourceExcerpt`, `Plan`, `Validation`, `Critique`, `Group`, `Consolidation`, `ContextNotice`, `Custom { namespace, name }`.
Every block MUST belong to exactly one kind; no block may have an unparseable kind.

### 3.2 Kind Declaration {block.kind-declaration}
Each capability declaration MUST name `output_block_kinds` drawn from this catalogue.
A capability emitting an undeclared kind is an Explicit Rejection.

### 3.3 Kind Composition Rules {block.kind-composition-rules}
`ToolCallProposal`/`ToolResult` MUST live as children of a `MessageAssistant` block or standalone in non-conversation context; they MUST NOT appear as transcript-anchor blocks directly.
`Evidence` blocks MUST reference ≥1 `Citation`/`Observation`/prior content block via `cites` edges.
`Artifact` blocks MUST reference durable backing storage via `External` content when content exceeds inline-size threshold; oversized `Inline` `Artifact` PROHIBITED.
`Composed` blocks MUST reference ≥1 child via `children_block_ids`.
`Group` blocks MUST be `Composed`.
`ReasoningTrace` MUST NOT default `Public`.
Violations MUST produce typed `BlockCommitRejected` error.

### 3.4 Custom Extension {block.custom-extension}
`Custom { namespace, name }` MUST be registered via a capability call (proposal-first).
Registration MUST declare: `allowed_content_variants`, `default_sensitivity`, `transcript_anchorable`, `permitted_parent_kinds`, `permitted_child_kinds`, `default_edges`, `description`.
A custom kind MUST NOT violate composition rules; structurally invalid declaration MUST be rejected.

## 4. `BlockContent` {block.block-content}
### 4.1 Required Shape {block.content-required-shape}
Three discriminated variants, chosen at commit, fixed: `Inline { text }`, `External { storage_ref, size_bytes, content_type, external_content_hash }`, `Composed { children_block_ids }`.

### 4.2 Inline-Size Threshold {block.inline-size-threshold}
Variant MUST be decided at commit and fixed for lifetime; an `Inline`-committed block MUST NOT be re-encoded to `External` if the threshold later changes.

### 4.3 Composition Resolution {block.composition-resolution}
A `Composed` block MUST resolve by reading `children_block_ids` in order, resolving each child recursively at read time.
A `Masked`/`Dropped` child MUST resolve to a typed masked/dropped placeholder; dropped children's content MUST NOT be silently re-fetched.

### 4.4 Cross-Reference vs Containment {block.cross-reference-vs-containment}
References MUST be typed edges (§5), not composition.

### 4.5 Content Hash {block.content-hash}
Every block MUST carry `content_hash` (SHA-256, 32 bytes) computed at creation over canonical content encoding, fixed at creation.
`content_hash` MUST be computed over full canonical content and MUST NOT omit `Sensitive` fields.
Raw `Secret` material MUST NOT appear in inline content.
`projection_hash` MUST NEVER be used for block identity/dedup/equality; only `content_hash` carries identity.
`content_hash` MUST be `NOT NULL` and immutable.

## 5. `BlockEdge` and the Block Graph {block.block-edge-block-graph}
### 5.1 Definition {block.block-edge-definition}
Every explicit edge MUST carry: `from_block_id`, `to_block_id`, `edge_kind`, `metadata`, `created_at` (`edge_id` optional/derivable).
Edges MUST be committed at the same boundaries as blocks and MUST be immutable; the graph MUST be append-only.

### 5.2 Canonical Edge Kinds {block.canonical-edge-kinds}
Closed catalogue: `parent`, `contains`, `supersedes`, `derives_from`, `cites`, `witnesses`, `references`, `follows_in_transcript`, `consolidates`, `materialized_by`, `promotes_scope_of`, `scope_projection_of`, `attaches_to`, `validated_by`, `responds_to`, `conditioned_on`.

### 5.3 Edge Extension {block.edge-extension}
Registered edge kinds MUST be registered via the same extension plane as `Custom` block kinds, declaring `namespace`+`name`, `from_kinds`, `to_kinds`, `metadata_schema`, `transitive`, `description`.

### 5.4 Graph Properties {block.graph-properties}
The graph MUST be acyclic in structural composition + lineage (`parent`, `contains`, structural `supersedes`).
The graph MUST be append-only; stale edges MUST be left in place.

## 6. Block Lifecycle and Non-Destructive Edits {block.block-lifecycle-non-destructive-edits}
### 6.1 Definition {block.lifecycle-definition}
`BlockLifecycle`: `Raw`, `Active`, `Masked`, `Dropped`, `Recovered`.
`PinState`: `Unpinned`, `Pinned`, `Protected`.
Lifecycle + pin state MUST be derived from the version graph's action log, not stored on the block.

### 6.2 Edit Semantics {block.edit-semantics}
Editing observable content MUST NOT mutate the block; it MUST create a new block with fresh `block_id`, new content, prior block as target of `supersedes`, new `content_hash`, fresh `created_at`, edit-source `producer`.
Editing a `Composed` block's children MUST create a new `Composed` block with `supersedes` edge to prior; children unchanged.
Editing metadata MUST create a new sibling.

### 6.3 Mask, Drop, Recover {block.mask-drop-recover}
`Mask(block_id)`, `Drop(block_id)`, `Recover(block_id)` MUST be committed as version-graph entries, not block mutations; MUST emit `BlockLifecycleChanged` events; MUST be recorded in the execution ledger.

### 6.4 Pin and Protect {block.pin-protect}
`Pin`, `Unpin`, `Protect`, `Unprotect` MUST live on the version and emit `BlockPinChanged` events.

### 6.5 Group and Ungroup {block.group-ungroup}
`Group(block_ids)` MUST create a new `Group`-kind `Composed` block; grouped blocks unchanged.
`Ungroup(group_block_id)` MUST be an edit (new version-graph entry); the group block MUST NOT be destroyed.

### 6.6 Hard Delete {block.hard-delete}
Hard delete MUST be explicitly user-initiated; never automatic; compaction MUST NOT hard-delete.
Typed-confirmation REQUIRED when block referenced by a `Composed` parent, non-superseded `supersedes` chain, `Evidence` chain, or any non-current version.
MUST be recorded in the ledger as `BlockHardDeleted`.
A minimal tombstone MUST be retained (`block_id`, deletion time, actor/source, `conversation_id`, `scope`, `parent_block_id`, prior kind if safe, sensitivity-safe reason); payload/secret/embeddings/indexed text/external blobs MUST be removed.
If a `Composed` parent's child is deleted and materialization fails, the parent MUST transition to typed `MaterializationOrphaned`.

### 6.7 Lifecycle Transition Rules {block.lifecycle-transition-rules}
Transitions MUST be explicit + deterministic: `Raw→Active`, `Active→Masked`, `Active→Dropped`, `Masked→Active`, `Masked→Dropped`, `Dropped→Recovered`, `Recovered→Active`, `Recovered→Masked`, `Recovered→Dropped`.
No time-based transition PERMITTED; no auto-mask-after-N-turns at block layer.

## 7. Streaming and the Commit Boundary {block.streaming-commit-boundary}
### 7.1 Definition {block.streaming-definition}
Streaming MUST happen via `Event`s; blocks MUST exist only at the commit point.

### 7.2 Event-Then-Block Pattern {block.event-then-block-pattern}
Each partial MUST flow as a typed `Event` carrying the standard envelope + `partial_block_handle`.
At the declared commit boundary the runtime MUST commit a `Block` carrying the same `block_id` named in the partial-block handle.

### 7.3 Partial-Block Orphans {block.partial-block-orphans}
On pre-commit failure, no committed block MUST exist yet.
`partial_output_meaningful` MUST determine preserve-as-orphan vs discard; preserved orphans MUST carry a typed `partial_orphan` marker.

### 7.4 Tool-Input vs Tool-Output Streaming {block.tool-input-output-streaming}
Tool-input streaming MUST commit `ToolCallProposal` with final args at commit; tool-output streaming MUST commit `ToolResult` with final result; both linked by `responds_to` edges.

### 7.5 Live-Partial-Write Capabilities {block.live-partial-write-capabilities}
Block-layer commit MUST align with the executor's atomic-rename point.
If live-write is cancelled mid-stream, the temp file MUST be deleted and no `Artifact` block committed.

### 7.6 Commit Boundary Set {block.commit-boundary-set}
Canonical boundaries: user message → `MessageUser`; accepted assistant turn → `MessageAssistant` + children; capability invocation complete → `ToolCallProposal` + `ToolResult`/`Failure`/`ToolDenial`; router route record; inspector state-changing op; workflow node complete; import success; consolidation complete; explicit draft commit; subsystem internal commit.
Each boundary MUST be one version-graph commit + one ledger entry.

## 8. Identity, Validation, and Hashing {block.identity-validation-hashing}
### 8.1 Identity {block.identity}
A `block_id` MUST be globally unique within the installation, assigned at commit, never reused/reassigned/mutated.
Identity MUST be independent of content; dedup MUST use `content_hash` as a separate dimension.

### 8.2 Block Commit Validator {block.block-commit-validator}
Before admission to the pool the validator MUST check: (1) identity well-formed and unused; (2) kind canonical or registered `Custom`; (3) content variant permitted by kind; (4) `Composed` children non-empty, all exist, no structural cycles; (5) edges resolve and satisfy kind constraints; (6) `parent_block_id` resolves and permits child kind; (7) `producer` well-typed and known; (8) sensitivity canonical, composed blocks MUST NOT underreport children's max effective sensitivity; (9) `description` non-empty for kinds requiring it; (10) hash recomputes and matches; (11) `scope` canonical and producer-compatible.
Failed validation MUST return typed `BlockCommitRejected`.

### 8.3 Hash Collision {block.hash-collision}
Two distinct blocks sharing a hash MUST log a high-severity `ContentHashCollisionSuspected` event; hash match alone MUST NOT be treated as identity.

### 8.4 Cross-Reference Rules {block.cross-reference-rules}
Block→block references MUST use `block_id` as canonical key; capability references MUST use `(capability_id, capability_version)`; event references MUST use `(event_envelope, sequence)`.
A reference resolving to a non-existent target MUST produce a typed `BrokenBlockReference` event without corrupting the block.

## 9. Sensitivity {block.sensitivity}
### 9.1 Definition {block.sensitivity-definition}
`default_sensitivity`: `Public`, `Sensitive`, `Secret`.
`Secret` content MUST be persisted with redacted content; the raw secret MUST be held only in transient memory and zeroed after use; MUST NOT be retrievable through search, compaction content review, or any standard share/export path.

### 9.2 Per-Field Override {block.per-field-override}
An optional `sensitivity_field_map` MUST override the default per field path; rendering/export/retrieval MUST respect the map.

### 9.3 Inheritance Through Composition {block.sensitivity-inheritance}
A `Composed` block's effective sensitivity MUST be the max of its declared sensitivity and children's max effective sensitivity.
The commit validator MUST auto-escalate when effective is deterministically higher; explicit unsafe lowering MUST be rejected unless policy allows a typed-confirmation override.
Rendering/export/indexing/caching MUST always use effective sensitivity.

### 9.4 Producer-Seeded Defaults {block.producer-seeded-defaults}
A capability commit MUST seed `default_sensitivity` from the capability's `data_sensitivity`; lowering a `Secret`-seeded value to `Public` MUST require a typed-confirmation policy override.

### 9.5 Projection Independence {block.projection-independence}
A surface MUST consume effective sensitivity to gate rendering/export/copy and MUST NOT modify stored sensitivity.

## 10. Block Description {block.block-description}
### 10.1 Definition {block.description-definition}
`description` MUST be emitted by the producer at commit and fixed at commit.

### 10.2 Producer Responsibility {block.producer-responsibility}
The producer MUST emit a description at commit per the kind's template; `Custom` kinds MUST follow the registered template.

### 10.4 Description Immutability {block.description-immutability}
A description MUST be fixed at creation; an inadequate description MUST be edited via a sibling, not patched in place.

## 11. Block Scope {block.block-scope}
### 11.1 Definition {block.scope-definition}
`scope`: `run`, `intent_thread`, `task`, `conversation`, `workspace`, `global`, `reusable_policy_rule`.
`scope` MUST be declared at commit by the producer.

### 11.2 Scope Promotion {block.scope-promotion}
Promotion MUST create a new immutable block/reference record at the broader scope, linked by `promotes_scope_of`/`scope_projection_of`; the original MUST remain valid.
`supersedes` MUST NOT be used for visibility broadening.
Scope demotion MUST NOT be permitted as a direct operation.

### 11.3 Cross-Scope References {block.cross-scope-references}
A broader-scope block MAY reference a narrower-scope block only if the reference stays meaningful when the narrower block leaves scope.
An unresolvable reference MUST produce a `BrokenBlockReference` event without corrupting the referencer.

## 12. Cross-Surface Interoperability {block.cross-surface-interoperability}
### 12.1 Definition {block.interop-definition}
There MUST be one block pool read/written by every surface, substrate service, control rail, and external integration through the same block model.

### 12.2 Per-Surface Projections {block.per-surface-projections}
Filtering MUST be a surface concern; blocks MUST remain unchanged.

### 12.3 Cross-Surface Composition {block.cross-surface-composition}
A block MAY compose blocks from multiple surfaces; surfaces not supporting a child kind MUST render typed placeholders.

### 12.4 Boundary {block.interop-boundary}
No surface MAY introduce a private block pool, private kind catalogue, or private edge catalogue.

## 13. Block Persistence Contract {block.block-persistence-contract}
### 13.1 What Is Durably Stored {block.what-is-durably-stored}
MUST durably store: the block pool; the edge set; per-block metadata (`block_id`, `kind`, `content`, `parent_block_id`, `producer`, `origin_run_id`, `conversation_id`, `created_at`, `block_schema_version`, `content_hash`, `source_attribution`, `default_sensitivity`, `sensitivity_field_map`, `description`, `scope`); the version graph; block-related ledger events.

### 13.2 What Is Computed {block.what-is-computed}
Per-version lifecycle/pin maps, materialized active view, per-tokenizer token counts, relevance scores, embedding vectors MUST be computed/derived.
Token counts MUST NEVER be cached as a plain scalar.

### 13.3 Reconstruction Across Restart {block.reconstruction-across-restart}
On restart, the pool, version graph, and per-version lifecycle/pin maps MUST re-emerge from durable storage.
Reconstruction MUST be deterministic for replay.

### 13.4 Reconstruction Across Retry, Edit, Reroute, Branch {block.reconstruction-across-retry-edit-reroute-branch}
Retry/edit/reroute/branch MUST share the block pool; the version graph MUST record the branch; block records MUST remain singular.

## 14. Settings {block.settings}
### 14.1 Configurable Dimensions {block.configurable-dimensions}
Surface-presentation: `blocks.inline_size_threshold_bytes`, `blocks.description_visibility`, `blocks.expansion_default`, `blocks.cross_surface_render_strategy`.
Retention: `blocks.hard_delete_confirmation_threshold`, `blocks.orphan_retention_policy`, `blocks.compaction_default_policy`.
Sensitivity: `blocks.export_sensitivity_filter`, `blocks.copy_to_clipboard_sensitivity_filter`, `blocks.redaction_strategy`.
Custom-kind: `blocks.allow_custom_kinds_from_source.<source_id>`, `blocks.custom_kind_review_threshold`.
Description: `blocks.description_max_length_chars`, `blocks.description_regeneration_enabled`.
Agent-exposure: `blocks.kind_catalogue_visible_to_agent`, `blocks.sensitivity_exposure`, `blocks.description_visible_to_agent`.

### 14.2 Settings-Key Convention {block.settings-key-convention}
Keys MUST follow `blocks.<dimension>`; per-kind `blocks.<dimension>.kind.<kind_name>`; per-source `blocks.<dimension>.source.<source_id>`.

## 15. Explicit Rejections {block.explicit-rejections}
- mutable block content
- in-place lifecycle storage on block row
- private per-surface or per-capability block models
- implicit inferred edges from content patterns
- open block kinds without canonical baseline
- silent kind shadowing
- live events as durable history
- block IDs lacking global uniqueness/stable ordering or reassigned
- per-surface block-id namespaces
- silent hard delete
- automatic mask-after-time-window
- forcing every event into a block
- block content carrying a token-count scalar
- block content carrying a cost scalar
- `Composed` blocks whose children list mutates
- `Composed` blocks with no children
- `Evidence` blocks without supporting `cites` edges
- mixed-sensitivity blocks where declared underreports effective
- block descriptions regenerated in place
- treating `Block` and `Message` as same primitive
- treating `Block` and `Event` as same primitive
- treating `Block` and `Artifact` as same primitive
- treating `Block` and `Capability` as same primitive
- treating `Block` and `Ledger Entry` as same primitive
- silent compaction without ledger record
- forcing block storage layout into the canonical model
- claiming the block kind catalogue must remain unchanged forever
- using block ordering as sequence truth

## 16. Consequences for Later Specs {block.consequences-for-later-specs}
- Artifacts/evidence spec MUST define entity-level lifecycle over `Artifact`/`Evidence`/`Citation`/claim blocks without an incompatible content carrier.
- Ledger spec MUST record block commits/edge commits/lifecycle transitions/hard deletes/tombstones; ledger rows MUST NOT duplicate block content.
- Version-graph spec MUST store per-version lifecycle/pin/ordering state; MUST NOT store block content.
- Retrieval spec MUST treat indexes as rebuildable projections over blocks.
- Context-assembly/compaction spec MUST assemble from the active block projection and MUST NOT mutate content.
- Memory spec MUST treat memory entries as `Memory`-kind blocks.
- Provider/model-strategy specs MUST NOT treat assembled request text as ordinary durable blocks.
- Storage/sync/portability specs MUST preserve block identity, schema version, content, structural fields, edges, tombstones, sensitivity.
- Security/credential specs MUST treat `Secret` sensitivity + per-field maps as hard policy inputs; raw secrets MUST NEVER leak through descriptions/indexes/exports/telemetry.
- No surface/workspace/plugin/MCP/automation/workflow/QC/telemetry/runtime/packaging layer MAY introduce a parallel block model, private pool, or capability-like primitive bypassing Files 05-08.
