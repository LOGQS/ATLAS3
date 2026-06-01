# Artifacts, Claims, Evidence, and Provenance — Operative Core

## 1. Chosen Model {artifact.chosen-model}
Each `ArtifactVersion` MUST be an `Artifact`-kind `Block`.
The `Claim` block kind is a canonical extension to the File 08 catalogue declared here.
No parallel artifact/claim/evidence registry, no parallel observation pool, no parallel provenance database.

## 2. Boundaries with Adjacent Layers {artifact.boundaries-with-adjacent-layers}
### 2.1 With File 08
File 09 MUST NEVER invent a block kind outside its declared `Claim` extension, MUST NEVER invent edge kinds outside `EvidenceRelation`-decorated existing edges + registered extension edges, MUST NEVER introduce a parallel content carrier, MUST NEVER mutate a block's stored fields.

## 3. `Artifact` {artifact.artifact}
### 3.2 Required Fields
`artifact_id`, `artifact_kind`, `title`, `description`, `current_version_block_id`, `producing_run_id`, `producing_task_id`, `producing_intent_thread_id`, `producing_conversation_id`, `producing_workspace_id`, `materialization_policy`, `scope`, `tags`, `created_at`, `last_version_committed_at`, `entity_schema_version`
`artifact_id` MUST never be reused/reassigned/mutated.
`artifact_kind` declared at creation; immutable.
Every `current_version_block_id` pointer update MUST be a typed event + ledgered.

## 4. `ArtifactKind` {artifact.artifact-kind}
### 4.1 Closed Canonical Catalogue
`Document`, `Note`, `Report`, `Lesson`, `Curriculum`, `Quiz`, `ExerciseSet`, `FlashcardSet`, `Rubric`, `CodePatch`, `Macro`, `Dataset`, `Chart`, `Table`, `Image`, `Audio`, `Video`, `ScreenshotSeries`, `BrowserExtract`, `WebDocument`, `Notebook`, `Diagram`, `InstructionFragment`, `WorkflowTemplate`, `Adapter`, `Validator`, `ArtifactBundle`, `Custom { namespace, name }`
Every artifact MUST belong to exactly one kind.
### 4.2 Kind Composition Rules
`ArtifactBundle` MUST always be `Composed`.
`Dataset` exceeding inline-size threshold MUST use `External`.
`Image`/`Audio`/`Video`/`ScreenshotSeries` MUST use `External`.
### 4.3 Custom Extension
Declares: `allowed_content_variants` (`Inline`/`External`/`Composed`), `default_materialization_policy`, `default_review_state`, `default_validation_required`, `description`, `surface_renderer_hint`, `default_edges`.
Cannot violate canonical composition rules; structurally invalid declaration rejected.

## 5. Artifact Lifecycle and States {artifact.artifact-lifecycle-states}
### 5.1 `ArtifactLifecycle` {artifact.artifact-lifecycle}
`Draft`, `Active`, `Validated`, `Superseded`, `Archived`, `Discarded`
### 5.2 `ReviewState` {artifact.review-state}
`Unreviewed`, `AcceptedByUser`, `AcceptedByAgent`, `Rejected`, `NeedsRevision`
`AcceptedByAgent` MUST NOT lift typed-confirmation on downstream actions.
### 5.3 `ValidationState`
`NotValidated`, `PendingValidation`, `Passed`, `Failed`, `NeedsReview`
### 5.4 Per-Version vs Per-Entity Derivation {artifact.per-version-vs-per-entity-derivation}
`ArtifactLifecycle`/`ReviewState`/`ValidationState` MUST be derived per-`ContextVersion`, NEVER stored on entity record.
### 5.5 Lifecycle Transition Rules
No time-based transition permitted; no auto-archive at this layer.

## 6. `ArtifactVersion` {artifact.artifact-version}
### 6.2 Required Fields
`version_id`, `artifact_id`, `version_number`, `parent_version_id`, `derivation_summary`, `produced_by_run_id`, `produced_by_node_id`, `produced_by_capability_id`, `materialized_paths`, `validation_report_id`, `metadata`
`version_number` monotonically increasing; never reused.
### 6.3 Version Creation {artifact.version-creation}
New version created by: `artifact.create`, `artifact.commit_version`, `file.edit`/`file.create` on materialized path, `artifact.merge`.

## 7. Artifact Materialization {artifact.artifact-materialization}
### 7.2 `MaterializationPolicy`
`InWorkspace`, `ExternalRef`, `None`
Changing MUST require `artifact.update_materialization_policy` + audit-visible event.
### 7.4 Materialized Paths Provenance {artifact.materialized-paths-provenance}
Entry: `workspace_id`, `relative_path`, `resolved_absolute_path`, `is_principal`, `content_role` (`Primary`, `Asset`, `Sidecar`, `Companion`), `materialized_at`, `content_hash`
### 7.5 Disk→Entity Sync {artifact.disk-entity-sync}
External edit MUST commit a new sibling `Artifact`-kind block; `current_version_block_id` updates atomically; `ArtifactExternallyEdited` emits.

## 8. Artifact Tombstones {artifact.artifact-tombstones}
### 8.1 Hard Delete
`artifact.hard_delete_version` MUST be `UserApproval` with `permission_floor: Denied` + typed confirmation.
`artifact.hard_delete_entity` MUST require typed-confirmation.
### 8.2 Tombstone Fields {artifact.tombstone-fields}
`version_id`, `artifact_id`, `version_number`, `parent_version_id`, `produced_by_run_id`, `produced_by_node_id`, `produced_by_capability_id`, `deleted_at`, `deleted_by`, `deletion_reason`, `safe_description`
`deletion_reason`: `UserRequested`, `RetentionPolicy`, `CredentialExpungement`, `SourceUnavailable`, `MaintenanceCleanup`, `Custom { code, description }`
### 8.3 Lineage Preservation
Hard delete MUST never be automatic.

## 9. `Claim` {artifact.claim}
### 9.1 Definition
`Claim` block kind registered as canonical baseline, NOT `Custom` namespaced.
`allowed_content_variants`: `Inline` or `Composed`; `default_sensitivity`: `Public`; `transcript_anchorable`: false; `permitted_parent_kinds`: `Any`; `permitted_child_kinds`: `Claim`, `SourceExcerpt`, `Evidence`, `Citation`, `Observation`; `default_edges`: `cites`, `references`, `responds_to`, `supersedes`.
### 9.2 Required Fields
`claim_id`, `claim_text`, `claim_kind`, `confidence_class`, `confidence_score`, `scope`, `anchor`, `claim_schema_version`
Status, withdrawal, supersession, override MUST NOT be mutable claim-block fields.
### 9.3 `ClaimKind`
`Factual`, `Causal`, `Conditional`, `Recommendation`, `Prediction`, `Definition`, `Identity`, `Summary`, `Negation`, `Custom { namespace, name }`
### 9.4 `ClaimStatus` {artifact.claim-status}
`Candidate`, `Supported`, `Contradicted`, `Unresolved`, `Superseded`, `Withdrawn`
Explicit override reason + actor MUST be recorded in policy ledger.
### 9.5 `ClaimConfidenceClass`
`DirectlyObserved`, `VerifiedExternal`, `Inferred`, `Plausible`, `Speculative`, `Disputed`
`confidence_score` MUST never be sole policy input.
### 9.6 `ClaimAnchor`
`source_block_id`, `source_span`, `anchor_kind` (`Authored`, `Extracted`, `Annotated`, `Derived`)
### 9.7 Claim Lifecycle
Editing `claim_text`/`claim_kind`/`confidence_class` MUST commit a new sibling claim block via `supersedes`.

## 10. Claim Extraction {artifact.claim-extraction}
### 10.1 Explicit Publication
`claim.publish` declares `replay_class: deterministic_replayable`; `output_block_kinds`: `[Claim]`; `concurrency`: `SelfParallel`.
### 10.2 Automatic Extraction
Opt-in per scope, default off.
Extracted claims MUST default `Sensitive` until user review.
MUST always emit `ClaimAutoExtracted` events with extractor model identity.

## 11. `Evidence` {artifact.evidence}
### 11.1 The `Evidence` Block Kind
Content: `evidence_kind` (`DirectObservation`, `CitedSource`, `ToolResult`, `ValidationOutcome`, `DerivedReasoning`), `summary`, `originating_run_id`, `originating_capability_id`.
An `Evidence` block MUST reference ≥1 supporting block; evidence block with no supporting references is Explicit Rejection.
### 11.2 `EvidenceLink`
Edge metadata: `relation`, `confidence_class`, `confidence_score`, `applies_to_span`, `captured_at`, `captured_by_run_id`, `captured_by_capability_id`, `notes`
### 11.3 `EvidenceRelation`
`Supports`, `WeakSupports`, `Refutes`, `Contextualizes`, `Corroborates`, `Summarizes`, `Derives`, `Witnesses`, `IllustratesByExample`, `Custom { namespace, name }`
### 11.4 `EvidenceConfidenceClass`
`DirectlyObserved`, `VerifiedExternal`, `Inferred`, `Plausible`, `Speculative`, `Disputed`
### 11.5 Evidence Set Closure
Compaction policies MUST preserve evidence-set closure for any claim/artifact at `Supported`/`Validated` state by default.
Compaction MUST NEVER silently sever evidence chains.

## 12. `Citation` {artifact.citation}
### 12.1 The `Citation` Block Kind
Content: `reference_kind`, `reference_value`, `source_span`, `captured_at`, `captured_by_run_id`, `captured_by_capability_id`, `retrieval_strategy` (`DirectFetch`, `CachedFetch`, `SearchResult`, `UserAttached`, `AgentInferred`), `display_metadata`.
### 12.2 `CitationReferenceKind`
`Url`, `DocumentBlockSpan`, `FileRange`, `PriorBlock`, `McpResource`, `KnowledgeEntry`, `Repository`, `ExternalDoiUrn`, `ProvenanceRecord`, `Custom { namespace, name }`
`FileRange` `range_kind`: `LineRange`, `ByteRange`, `CharacterRange`
### 12.3 `SourceSpan` Grammar
`CharacterRange { start, end }`, `ByteRange { start, end }`, `LineRange { start_line, end_line, start_column, end_column }`, `PageRange { start_page, end_page }`, `TimeRange { start_seconds, end_seconds }`, `DomSelector { selector, occurrence_index }`, `XPath { xpath }`, `Composed { children }`

## 13. `Observation` {artifact.observation}
### 13.1 The `Observation` Block Kind
Content: `observation_kind`, `payload_reference`, `captured_at`, `captured_by_run_id`, `captured_by_capability_id`, `capture_context`, `staleness_fingerprint`, `observation_subject`.
### 13.2 `ObservationKind`
`FileSnapshot`, `AccessibilityTreeSnapshot`, `Screenshot`, `BrowserDom`, `NetworkResponseSnapshot`, `DatabaseQueryResult`, `TerminalOutput`, `ProcessState`, `EnvironmentSnapshot`, `RepositoryState`, `WorkspaceSnapshot`, `Custom { namespace, name }`
### 13.3 `StalenessFingerprint`
`ContentHash { hash }`, `Mtime { mtime_unix_seconds }`, `MtimeAndHash { mtime_unix_seconds, hash }`, `VersionId { version_id }`, `AccessibilityTreeHash { tree_hash }`, `DomSignature { url, signature }`, `EtagAndLastModified { etag, last_modified }`, `GitCommit { commit_hash, branch }`, `Composite { fingerprints }`, `Custom { namespace, name, value }`
Mismatch MUST produce typed `StateChangedSinceObservation` error in-band.

## 14. `Validation` and `Critique` {artifact.validation-critique}
### 14.1 The Block Kinds
`Validation` content: `validation_kind` (`Postcondition`, `TypeCheck`, `Lint`, `Test`, `EvaluatorScore`, `SchemaValidation`, `CitationCheck`, `FactualityCheck`, `ConsistencyCheck`, `SafetyCheck`, `Custom { namespace, name }`); `outcome` (`Passed`, `Failed`, `Inconclusive`); `validated_target_id`; `validator_kind` (`Deterministic`, `ModelMediated`, `UserManual`); `validator_reference`; `failure_details`; `inconclusive_reason`; `latency_ms`; `evidence_links`.
`Critique` content: `critique_kind` (`CodeReview`, `EditorialReview`, `PeerReview`, `DesignReview`, `Custom { namespace, name }`); `target_id`; `summary`; `findings`; `critic_kind` (`User`, `Agent`, `Subagent`, `External`); `critic_reference`; `recommended_action` (`AcceptAsIs`, `RevisionRecommended`, `RevisionRequired`, `RejectAndRestart`).
### 14.2 `ValidationState` Derivation {artifact.validation-state-derivation}
Any required validation `Failed` → `Failed`; all required `Passed` → `Passed`; any required `Inconclusive` + no failures → `NeedsReview`; missing required → `PendingValidation`; none linked → `NotValidated`. Recomputed on every read.
### 14.4 Critique vs Validation
Artifact `ValidationState` MUST derive only from `Validation` blocks; `Critique` MUST NOT contribute.

## 15. `Provenance` {artifact.provenance}
### 15.1 Definition
Derived view; computed on read. NOT a stored entity, parallel ledger, per-block field, or audit log.
### 15.2 Provenance Closure Rules
Block-level closure follows `parent_block_id`, `contains`, `derives_from`, `supersedes`.
Edge-level closure follows `cites`, `witnesses`, `validated_by`, `consolidates`, `responds_to`, `references`, `conditioned_on`, registered extension edges.
### 15.3 Canonical Query Surface
`provenance.query_lineage`, `provenance.query_evidence_set`, `provenance.query_contributing_runs`, `provenance.query_contributing_capabilities`, `provenance.query_replay_trace`, `provenance.query_derivation_chain`, `provenance.contradiction_check`, `provenance.query_artifact_versions`
Each MUST declare `permission_tier: ReadOnly`, `concurrency: ConcurrencySafe`, `replay_class: deterministic_replayable`.
### 15.4 Determinism and Reconstruction
Two queries with same target + same snapshots MUST return byte-identical results.
Cache invalidation MUST be event-driven.
### 15.5 Cross-Workspace and Cross-Installation Provenance
Import MUST commit an `Import` producer record on every imported block.

## 16. Capability Surface {artifact.capability-surface}
### 16.1 Closed Canonical Capabilities
Each MUST be a built-in capability registered at startup with `Builtin` source.
**Artifact:** `artifact.create`, `artifact.commit_version`, `artifact.set_review_state`, `artifact.update_materialization_policy`, `artifact.promote_scope`, `artifact.archive`, `artifact.restore`, `artifact.discard`, `artifact.merge`, `artifact.hard_delete_version`, `artifact.hard_delete_entity`, `artifact.preview_export`, `artifact.export`, `artifact.materialize_locally`
`artifact.hard_delete_version`/`artifact.hard_delete_entity` MUST be `UserApproval` + `permission_floor: Denied` + typed-confirmation.
**Claim:** `claim.publish`, `claim.update_status`, `claim.withdraw`, `claim.supersede`, `claim.attach_evidence`, `claim.detach_evidence`, `claim.review`
**Evidence/citation:** `evidence.link`, `citation.capture`
**Observation:** `observation.commit`
**Validation:** `validation.run`, `validation.attach`
**Critique:** `critique.publish`
**Provenance:** the eight `provenance.query_*` + `provenance.contradiction_check`; all `ReadOnly`, `ConcurrencySafe`, `deterministic_replayable`.
### 16.2 Capability Metadata Declarations
Extension resource classes: `artifact-pool`, `claim-pool`, `evidence-link-pool`, `provenance-cache`.

## 17. Cross-Surface Interoperability {artifact.cross-surface-interoperability}
### 17.1 Single Entity Pool
One artifact entity pool, one claim entity pool, one evidence-link edge set, one block pool.
### 17.2 Per-Surface Projections {artifact.per-surface-projections}
Each surface projects the entity pool through surface-specific filters (filter is a surface concern; entities/content remain in the unified pool unchanged):
- Coder: `CodePatch`, `Document`, `Notebook`, file-system view of materialized artifacts
- Web: `BrowserExtract`, `WebDocument`, `Image`, `Citation`
- Data Processor: `Dataset`, `Chart`, `Notebook`, `Table`
- Teacher: `Lesson`, `Curriculum`, `Quiz`, `ExerciseSet`, `FlashcardSet`, `Rubric`
- GUI Control: `Macro`, `ScreenshotSeries`, `Observation`
- memory management surface: `Memory`-kind blocks + knowledge-base projection over claims+citations
- inspector lens: every entity, filtered by kind/status/scope/source/validation/review/lifecycle
### 17.5 Boundary
No surface may introduce a private artifact pool, claim pool, or evidence-graph.

## 18. Persistence Contract {artifact.persistence-contract}
### 18.1 What Is Durably Stored
Artifact entity pool, claim entity pool, artifact version metadata records, `EvidenceLink` edge metadata, `Validation` + `Critique` blocks, `InWorkspace` materializations, entity-related ledger events.
### 18.2 What Is Computed
`ArtifactLifecycle`/`ReviewState`/`ValidationState`, `ClaimStatus` (when not overridden), `EvidenceSet` closure, provenance query results, materialized-path freshness.
### 18.4 Reconstruction Across Retry, Edit, Reroute, Branch
Run-scoped evidence-link edges MUST NOT transfer across retry/edit/reroute/branch by default.

## 19. Settings {artifact.settings}
### 19.1 Configurable Dimensions
Every mechanism MUST be configurable.
**Artifact:** `artifact.default_materialization_policy.<kind>`, `artifact.workspace_materialization_path_template`, `artifact.auto_accept_first_version`, `artifact.review_required.<kind>`, `artifact.validation_required.<kind>`, `artifact.archive_retention_policy`, `artifact.hard_delete_confirmation_threshold`, `artifact.bundle_export_includes_provenance`, `artifact.external_ref_local_cache_enabled`
**Claim:** `claim.evidence_threshold`, `claim.auto_extraction.enabled`, `claim.auto_extraction.model_id`, `claim.auto_extraction.model_request_template_id`, `claim.auto_extraction.minimum_confidence_class`, `claim.auto_extraction.review_required`, `claim.surface_display.confidence_class_filter`, `claim.contradiction_alert_enabled`, `claim.withdrawn_visibility`
**Evidence:** `evidence.closure_max_depth`, `evidence.closure_max_cardinality`, `evidence.relation.<relation>.transitive`, `evidence.compaction_preservation`
**Citation:** `citation.capture_display_metadata`, `citation.refresh_policy`, `citation.cache_retention_policy`
**Observation:** `observation.staleness_check_strictness` (`Strict`, `Permissive`, `Off`), `observation.payload_external_threshold_bytes`, `observation.screenshot_resolution_default`
**Validation:** `validation.run_on_commit.<kind>`, `validation.required_validators.<kind>`, `validation.model_mediated_enabled`, `validation.failure_action.<kind>` (`BlockCommit`, `MarkFailed`, `WarnOnly`)
**Critique:** `critique.surface_display_filter`, `critique.findings_max_count_per_block`
**Provenance:** `provenance.query.max_depth`, `provenance.query.max_cardinality`, `provenance.cache_enabled`, `provenance.query.include_tombstones_default`, `provenance.cross_installation_link_enabled`
**Agent exposure:** `artifact.kind_catalogue_visible_to_agent`, `claim.confidence_class_exposure`, `evidence.relation_exposure`, `provenance.query_exposure`

## 20. Events {artifact.events}
### 20.1 Event Vocabulary
Every committed entity-relevant change MUST emit a typed event through canonical bus.
**Artifact:** `ArtifactCreated`, `ArtifactVersionCommitted`, `ArtifactReviewStateChanged`, `ArtifactLifecycleChanged`, `ArtifactValidationStateChanged`, `ArtifactMaterializationPolicyChanged`, `ArtifactScopePromoted`, `ArtifactArchived`, `ArtifactRestored`, `ArtifactDiscarded`, `ArtifactExternallyEdited`, `ArtifactVersionHardDeleted`, `ArtifactHardDeleted`, `ArtifactExported`, `ArtifactMaterializedLocally`
**Claim:** `ClaimPublished`, `ClaimStatusChanged`, `ClaimStatusOverridden`, `ClaimWithdrawn`, `ClaimSuperseded`, `ClaimAutoExtracted`, `ClaimReviewCompleted`
**Evidence:** `EvidenceLinkAttached`, `EvidenceLinkDetached`, `ContradictionDetected`
**Citation:** `CitationCaptured`
**Observation:** `ObservationCommitted`, `ObservationStalenessDetected`
**Validation:** `ValidationStarted`, `ValidationCompleted`
**Critique:** `CritiquePublished`
**Provenance:** `ProvenanceQueryExecuted`, `ProvenanceCacheInvalidated`
### 20.2 Event Sensitivity
Raw secret payloads MUST never be persisted to durable ledger.

## 21. Explicit Rejections {artifact.explicit-rejections}
- parallel artifact/claim registry separate from block pool
- separate evidence storage layer outside block-graph edge set
- mutable artifact content on entity record
- mutable lifecycle/review/validation state on entity record
- claims as anonymous text fragments
- evidence chains without typed relations
- closing `EvidenceRelation` to support/refute only
- single numerical confidence score as only policy signal
- observations without staleness fingerprints backing a mutation
- silent claim-status changes
- silent evidence-link removal without recorded event
- automatic claim extraction enabled by default
- treating provenance as a stored entity
- hardcoded provenance query results
- artifact versions mutating prior version-block in place
- artifact identity tied to a materialization path
- time-based artifact lifecycle transitions
- time-based citation freshness as correctness condition
- `Critique` contributing to `ValidationState`
- claim-publish lifting `permission_floor: Denied` without typed-confirmation
- hard-delete floors weakening for discarded/only-version artifacts
- silent automatic claim promotion to `Supported`
- contradiction detection suppressing the contradiction
- entity capabilities operating outside canonical event bus
- claim entities anchored to `MessageUser` blocks user did not author
- materializing `InWorkspace` artifacts outside workspace root
- preserving earlier names as parallel systems
- treating `Artifact`/`Memory` as same primitive
- treating `Claim`/`Memory` as same primitive
- treating `Claim`/`MessageAssistant` as same primitive
- treating `Evidence`/`Citation` as same primitive
- treating `Observation`/`Citation` as same primitive

## 22. Consequences for Later Specs {artifact.consequences-for-later-specs}
Later specs MUST consume the entity + provenance contract: link ledger rows to entity ids without duplicating content; store per-version action logs driving derivation; treat `Claim`/`Evidence`/`SourceExcerpt`/`Citation`/`Observation` as first-class retrieval targets; preserve evidence-set closure for `Supported`/`Validated` entities; preserve claim identity in memory consolidation; produce `Observation` blocks conforming to §13 through canonical `observation.commit`; preserve artifact/claim/evidence/provenance identity across export/import; register validators as `Validator`-kind artifacts producing `Validation` blocks; render all entities through canonical data contracts; ship built-in declarations for every canonical entity capability, kind, relation, reference kind as `Builtin`.
