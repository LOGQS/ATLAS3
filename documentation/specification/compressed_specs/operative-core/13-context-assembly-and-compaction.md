# Context Assembly and Compaction — Operative Core

## 1. Chosen Model {context.chosen-model}
`ContextAssemblyService` is READ-ONLY; NEVER mutates blocks/lifecycle/indexes/versions.
`CompactionService` is WRITE-SIDE; does NOT hard-delete source content and does NOT bypass version history.
Every model-bound invocation MUST use `ContextAssemblyService`; no separate instruction assembler, router request assembler, per-surface private request builder, or ad-hoc concatenation path.

## 2. Model Request {context.model-request}
### 2.2 Assembly Parts
Each `AssemblyPart` MUST carry: `part_id`, `region`, `content_kind`, `source_ref`, `authority_class`, `sensitivity`, `inclusion_reason`, budget estimate/count, lifecycle visibility, omission/redaction/externalization metadata.
### 2.3 Authority Classes {context.authority-classes}
`governing_instruction`, `user_instruction`, `trusted_runtime_fact`, `untrusted_source_data`, `provider_native_callable_declaration`, `diagnostic_notice`
External descriptions/retrieval snippets/tool outputs/user files MUST be marked as data unless source explicitly grants instruction authority.
### 2.4 Sensitivity
Every part MUST carry sensitivity resolved from source+policy.
Assembly MUST fail safely when policy cannot decide whether a sensitive part may be included.

## 3. Semantic Regions {context.semantic-regions}
`GoverningInstructions`, `InstructionSources`, `CallableDeclarations`, `RuntimeState`, `CurrentInput`, `ConversationHistory`, `RetrievedContext`, `DiagnosticNotices`, `ReservedOutput`
Custom regions MUST obey same authority/sensitivity/budget/traceability rules.

## 4. Context Policies {context.context-policies}
`Full`, `Summarised`, `Minimal`, `Router`, `Custom`
Policies MUST NOT change source authority, sensitivity policy, capability approval rules, or routing semantics.

## 5. Router Context Assembly {context.router-context-assembly}
Router context policy MUST include full current triggering input unless input cannot be carried directly; then assembly MUST externalize/reference full input + include enough visible structure.
Current user request MUST NOT be replaced by a summary as normal path.
All router policies MUST produce durable route records per File 03.

## 6. Assembly Algorithm {context.assembly-algorithm}
Resolve invocation kind/model/provider/settings/policy; resolve regions/order/budgets/default authority; gather candidates; convert to assembly parts; apply sensitivity/policy/capability gates; count/estimate size; fit under budget; externalize/omit/summarize/reference oversize; produce cache-marker candidates; emit `AssemblyOutput` + snapshot reference.
Assembly MUST be deterministic for same durable inputs, settings snapshot, provider/model descriptor, policy snapshot.

## 7. Current Input and Oversize Handling {context.current-input-oversize-handling}
When current input too large to carry directly, assembly MUST preserve access to full input by externalizing as referenced source/searchable file/source block/equivalent durable object.
Rejection allowed ONLY when system cannot safely externalize/reference/inspect input.

## 8. Duplicate and Overlap Handling {context.duplicate-overlap-handling}
Duplicate handling MUST NOT mutate prior blocks, hide user's new instruction, or bypass routing/ledger records.
Correctness MUST NOT depend on elapsed time.

## 9. Budget and Overflow {context.budget-overflow}
`BudgetReport` MUST describe target model/profile + provider snapshot; total/reserved/rendered budget; per-region allocation+usage; omitted/redacted/summarized/externalized/overflowed parts; material policy decisions; token-counting accuracy class; cache-marker candidate summary; `cache_impact` classification.
`cache_impact`: `none`, `preserved_prefix`, `changed_tool_surface_only`, `changed_instruction_or_region_order`, `full_cache_break_likely`
Overflow is non-destructive; assembly MUST NOT compact/delete/mutate/silently discard durable content.

## 10. Token Counting {context.token-counting}
Model descriptor MUST expose: context window/request-size limit; tokenizer/counting identity; whether exact provider-native counting available; whether compatible local estimator available; which parts count toward which limits; special accounting for callable declarations/cached prefixes/images/files/multimodal.
Chosen accuracy class MUST be recorded in `BudgetReport`.
Token counts MUST NOT be stored as unqualified block fields; any reusable count MUST be keyed by content identity, content version/hash, tokenizer/counting identity.

## 11. Cache Marker Candidates {context.cache-marker-candidates}
A candidate records boundary, covered parts, source stability basis, sensitivity eligibility, provider/model capability snapshot, requesting policy.
Assembly does NOT define provider cache syntax, minimum lengths, retention, billing.
Fitting within context budget WINS over cache preservation; resulting `cache_impact` MUST be recorded.
Sensitive/secret content MUST be cache-ineligible unless policy explicitly allows.

## 12. Compaction {context.compaction}
`DescriptionDriven`, `FullSummarisation`, `IncrementalSummarisation`, `VirtualPaging`, `SimpleTruncation`, `Custom`
Any model-generated summary MUST preserve source links + sensitivity constraints.
Operations MUST be revision-safe: a pass declares the view revision it read + fails or rebases safely if view changed before commit.

## 13. Virtual Paging {context.virtual-paging}
`context.archive` applies `Drop`; `context.recall` applies `Recover`.
Retrieval results MUST surface lifecycle metadata.
No new lifecycle state, no parallel retrieval mechanism, no private archive database.

## 14. Continuity Summaries {context.continuity-summaries}
Continuity summaries MUST be durable blocks linked to compacted source blocks; subject to authority/sensitivity/budget rules.

## 15. Context Pressure {context.context-pressure}
Causes: assembly overflow, provider rejection, budget warning, tool-surface saturation, retrieval result expansion, user/automation request.
Time-based triggers MUST NOT be correctness mechanisms or defaults.

## 16. Instruction Sources and Workspace Files {context.instruction-sources-workspace-files}
Indexing a file does NOT by itself grant instruction authority.

## 17. Tool-Surface Coordination {context.tool-surface-coordination}
Tool-surface shrinkage MUST NOT remove a callable the execution contract requires unless policy explicitly permits reroute/pause/failure.

## 18. Capabilities {context.capabilities}
Context assembly+compaction MUST expose capabilities through canonical Capability Registry.
Write-like context capabilities MUST declare touched resources + revision preconditions.

## 19. Events, Ledger, and Snapshots
Context events MUST be `Custom { namespace, name, payload }` extensions registered through File 10.
Durable records MUST reference `AssemblySnapshot`s rather than storing raw model-request dumps by default.
An `AssemblySnapshot` MUST record/reference enough to reconstruct what was sent without re-querying any live source.
Replay determinism {context.assembly-replay-snapshot}: Replay MUST NOT re-derive inclusion/omission/ranking/token counts/memory outputs/retrieval results/tool-surface contents/runtime-world facts from live mutable sources; historical replay uses recorded snapshot + immutable source references only.

## 20. Persistence and Settings {context.persistence-settings}
Durable: context+compaction policy selections; continuity summary blocks; compaction commits; source externalization records; assembly snapshot references; duplicate-handling decisions.
Settings MUST cover: context policy by invocation kind; router context policy; region order+budget allocation; current-input+attachment overflow behavior; duplicate detection+resolution defaults; token-counting strategy; cache-marker candidate behavior; compaction policy+triggers; virtual paging lifecycle-filter behavior; instruction-file lookup/enablement/inclusion; sensitivity handling+snapshot retention; whether time-based convenience triggers enabled.

## 21. Explicit Rejections {context.explicit-rejections}
- mutating blocks/indexes/lifecycle/versions during assembly
- compaction as hidden model-request trimming
- overflow as permission to silently drop user content
- replacing current user request with a summary as normal routing path
- separate router/instruction/surface/validator request builders
- assigning authority only at region level
- treating external tool descriptions/retrieval snippets/web content as instructions
- hardcoding tokenizers/endpoints/context limits/cache durations/numeric thresholds
- storing token counts as unqualified block fields
- making provider cache behavior part of canonical assembly semantics
- requiring fixed region order solely for cache efficiency
- creating a virtual-paging archive store or lifecycle state
- time-based triggers as correctness conditions
- duplicate detection mutating prior blocks
- bypassing File 05-07 capability+policy contracts
- bypassing File 10/11 records for compaction/snapshots/durable context history
- treating `ATLAS.md`/workspace file as hidden model-request text without source attribution + policy control

## 22. Consequences for Later Specs {context.consequences-for-later-specs}
Memory specs MUST expose memory outputs as assembly sources with authority/sensitivity/budget/provenance metadata.
Settings specs MUST define exact scope precedence for context/router-context/compaction/instruction-file/duplicate-detection/cache-candidate settings.
Model strategy+provider specs MUST expose request-size/tokenizer/cache/callable-declaration/multimodal accounting without leaking provider specifics.
Storage specs MUST persist assembly snapshot references/continuity summaries/compaction commits/externalized source records without parallel context tables.
UI specs MUST present context inspection/duplicate handling/overflow/compaction history/source externalization as projections over records defined here.
Surface specs MUST declare default context+compaction policies without private model-request assembly paths.
Automation+workflow specs MUST reuse same assembly/compaction/pressure/snapshot contracts.
