# Coder Surface

## Status

Canonical. This file defines the `Coder` work surface — the specialized engineering environment for software work. It is the first per-surface specification: it fills the `SurfaceContract` that `worksurface.surface-contract` (File 25 §4) delegates to each per-surface spec, and it declares the coding-specific workflows, panels, capabilities, and policies the Coder surface contributes over the shared substrate. It owns user-facing coding workflows and specialized views; it owns no private architecture. It composes blocks, capabilities, execution, the version graph, workspaces, the sandbox, retrieval, context, world model, perception, and every other substrate through the same contracts every surface uses. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `Coder` `WorkSurface` and its `SurfaceContract` (`worksurface.work-surface`, File 25 §3, `worksurface.surface-contract` (File 25 §4)): identity, declared panels and selection kinds, the `SubsystemSurfaceSpec` and contributed capabilities, view presets and inspectors, and default context, model, execution, sandbox, and workspace policies
- the **code-as-artifact reframe**: a code change is an `Artifact` revision with validation and review state (`CodePatch` and the file `Artifact`/`FileAttachment` block per `artifact.artifact-kind` (File 09 §4) and `block.kind-catalogue` (File 08 §3.1)), not a file write accompanied by transcript prose
- the code-editing contract: the edit and patch capabilities, their multi-format edit sub-modes, read-before-edit staleness revalidation, atomic streaming materialization, and the semantic code operations (rename-symbol, move-symbol, update-imports) that compile down to audited file/artifact version changes
- codebase context and indexing: the coder codebase model (file, symbol, import, call, and build/test relations), codebase ingestion of mounted projects, the workspace-qualified retrieval namespace it indexes into, and the code-search and reference-attachment surface the agent and user consume — all over the shared retrieval substrate (File 12)
- coder file-history, undo, and "checkpoint" semantics as a projection over the one version graph (File 11), and the `coder.file_reverted` operation
- the coder Version-Control workflow as the surface presentation over the domain-neutral `git.*` capability family: status surfacing, diff, commit, branch, blame, stash, the comparison board, and the worktree-backed multi-agent workflow
- the integrated terminal and code-execution model: terminal sessions as `ManagedProcess` work on pseudo-terminals, and test/build/lint/run/preview as confined `ManagedProcess` work under a coder `SandboxProfile` (File 23)
- tests, build, lint, type-check, format-check, format-apply, debugging, tracing, and diagnostics as coder capabilities producing `Validation`, `Critique`, `Observation`, or artifact revisions through the shared substrates
- code review: review mode, per-change accept/reject/modify, and the validation-and-critique semantics that gate artifact lifecycle
- multi-agent and parallel coding over child runs (File 04 §16) and worktrees (File 24 §15), and the comparison-board projection
- the coder rails: slash commands, the keybinding contexts, the command palette and quick-open, code-aware mentions, and the default coder workflow set — bound to capabilities through the control-rail layer (File 26)
- coder session export as a projection over the version graph and ledger, and its privacy posture
- cross-surface composition (the coder execution surface other surfaces borrow), the coder world-model and perception integration, and the coder capability/event/settings surface

This file does not define:

- the `WorkSurface` primitive, the `SurfaceContract` field set, the `SurfaceRegistry`, the `SubsystemSurfaceSpec` reference, the `PanelKind`/`ViewPreset` model, the no-private-architecture invariant, or the deletion of autonomy fields — File 25 owns those; this file fills the contract
- the `Workspace`, `WorkspaceRecord`, materialization mirror, materialized-path resolution, disk↔substrate sync loop, the `.atlas/` internal layout, the `ATLAS.md` instruction-file hierarchy, the worktree identity and lifecycle, or codebase-ingestion identity — File 24 owns those; this file consumes them and projects them into coder views
- the `Sandbox` contract, `SandboxProfile`, `ManagedProcess`, `ProcessGroup`, pseudo-terminal spawning, filesystem/network/resource enforcement, killability, or the elevated helper — File 23 owns those; this file declares the coder profiles and runs confined work through them
- the version graph, `ContextVersion`, `VersionDiff`, sibling-block versioning, branching, forking, the materialized view, or snapshot resolution — File 11 owns those; this file projects coder history and revert over them
- the `Block`, `Artifact`, `CodePatch` kind, `Claim`, `Evidence`, `Observation`, `Validation`, `Critique`, materialization policy, or provenance — Files 08 and 09 own those; this file declares which kinds the surface primarily produces
- the retrieval index, namespace, chunking, embedding, hybrid-search, or knowledge-base mechanics — File 12 owns those; this file owns coder extraction semantics and consumes the shared index/retrieval contract
- context assembly, the `ContextPolicy`/`CompactionPolicy` families, token budgets, or model-request rendering — File 13 owns those; this file names the surface defaults
- model selection, `ModelProfile`, or fallback — File 16 owns those; this file names the surface's default profile and role preferences
- the run lifecycle, the capability-call pipeline, child-run isolation selection, the approval flow, leases, the permission tiers, the git-safety reusable-policy rules, the tool-surface composition, or the control-rail mechanics — Files 03–07 and 26 own those; this file declares the coder contributions and references the rules
- the world-entity catalogue, the availability evaluator, the perception sensors and capture, the storage substrate, sync, the secret vault, or the provider layer — Files 18, 19, 20, 21, 22, 17 own those; this file integrates through them
- UI rendering — editor/terminal/diff chrome, panel geometry, theming, the concrete editor engine, terminal renderer, content-search engine, or version-control library — the UI specs and infrastructure own those; this file specifies only the data and behavior contracts they consume
- the other per-surface specs (Web, Data Processor, Teacher, GUI Control, System Agent) — those declare their own `SurfaceContract`s

## Source Resolution

Families reviewed: the authoritative coder unit spec (`unit08-coder.md` with the D8.1–D8.6 decisions); the specbase coder domain (`domains/coder/INDEX.md`, `README.md`, `ide-interface.md`, `command-palette.md`, `workspace-management.md`, `checkpoints-undo.md`, `terminal.md`, `agent-execution.md`, `git-integration.md`, `session-logging.md`); the file, shell, and git infrastructure (`tools/file-operations.md`, `tools/shell-operations.md`, `tools/web-search-and-rag.md`, `files/file-management.md`, `infrastructure/git.md`, `cross-cutting/actions.md`, `cross-cutting/state-awareness.md`); the cross-cutting coder decisions in the unit specs (`unit04-routing-agents-prompt.md` D4.1/D4.3/D4.4/D4.7, `unit06-tools.md`, `unit11-cross-tool-learning.md` CT.16/CT.17, `unit12-infrastructure.md` D12.8 git safety, `unit13-ui.md` coder panels and keybinding contexts, `unit14-systems.md` D14.KB.5/D14.QC.3/D14.QC.4/D14.SP.1/D14.SM.3, `unit15-ux-distribution-files-glossary.md` worktree layout and view presets); the strategic target-state review (`codex_recommendations.md` §7.1/§7.2/§7.3, §8.2, §10.1/§10.3, §14.2/§14.10); the project IDE/workspace/RAG vision (`atlas3-core/TODO.md` §4/§5/§6/§7/§15, `ai-era-engineering-principles.md`, `foundations/stack.md`); and the existing-ecosystem and compressed-repo coding tools (`claude_code_tool.md`, `codex_tool.md`, `claude_tool.md`, `claude_cowork_tool.md`, `chatgpt_tool.md`, plus `claude-code`, `codex`, `cline`, `continue`, `kilocode`, `qwen-code`, `serena`, `warp`, `opencode`, `gemini-cli`, `aider`-style, `archon`, `graphify`, `claude-context`, `context-mode`, `forgecode`, `t3code`, `oh-my-codex`, `codebuff`, `space-agent`, `bolt-diy`, `fragments`, `onlook`, `suna`, `rtk`, and others) for cross-tool design-space corroboration.

Resolution rule: this file realizes the Coder surface by filling File 25's `SurfaceContract` and declaring coding-specific workflows; it re-owns no substrate. Every substrate's semantics stay with its owning file. Where the source material describes a coder mechanism the canon has already settled horizontally (file history, worktrees, sandboxes, the version graph, the policy layer), this file consumes the settled contract and adds only the coder-specific presentation and workflow. Implementation groundings the sources lock (a code-editor engine, a pseudo-terminal stack, a version-control library, a content-search engine, a language-structure parser) are named in the sources for grounding but are kept out of the canonical body as replaceable implementations behind their contracts, per the project rule against provider- and library-specific detail in canonical specs.

Resolved tensions:

- **Code change as file write versus artifact revision.** The earliest coder material treats an edit as a `file.write` plus chat text; `codex_recommendations.md` §8.2 reframes it: "code changes are artifact revisions with validation state, not just file writes accompanied by chat text," and the target is "a serious engineering surface with agent-native artifact, review, execution, and provenance semantics." This file adopts the artifact reframe (§6): a coder edit produces a versioned, validatable, reviewable, citable `Artifact`/file block, consistent with `artifact.chosen-model` (File 09 §1) and `block.chosen-model` (File 08 §1).
- **Checkpoints as a shadow store versus a version-graph projection.** Eight specbase coder files described a `file_checkpoints` table and `.atlas/checkpoints/<session>/<file>.snap` shadow directories; `unit08-coder.md` D8.2, `checkpoints-undo.md`, `version.chosen-model` (File 11 §1), and `workspace.explicit-rejections` (File 24 §23) delete them in favor of "the version tree is the single file-history mechanism; disk state is the materialized view." This file adopts the projection model (§8) and introduces no parallel checkpoint store.
- **Git as a coder-private feature versus a domain-neutral service with a coder UI.** `infrastructure/git.md` establishes git as a domain-neutral infrastructure service ("Coder domain adds the UI layer on top"); other surfaces call the service directly. This file resolves toward that split (§9): the Coder surface presents the version-control workflow over the shared `git.*` capability family and the worktree primitive File 24 owns, and the git-safety rules `policy.built-in-reusable-policy-rules` (File 06 §11.5) fixes; it owns no private git mechanism.
- **Session logging as a parallel write path versus an export projection.** `session-logging.md` originally wrote `tool-calls.jsonl`, `checkpoints.jsonl`, and `git-operations.jsonl` as live parallel logs that duplicate the version tree and ledger; `unit08-coder.md` D8.4 deletes those as parallel write paths and makes session logging an export view over the version tree and ledger, with prompt capture default-off for privacy. This file adopts the export-projection model (§17).
- **A coder autonomy/participation dial versus permission tiers.** Some coder overviews carried a `Drive`/`Supervise`/`Collaborate`/`Delegate` participation level, a `plan`/`act` mode, or a per-tool auto-approve toggle as an autonomy field; `worksurface.no-autonomy-field` (File 25 §13), `policy.chosen-model` (File 06 §1), and `world.surface-state` (File 18 §5.5) delete the autonomy field at every layer. This file carries no autonomy field (§22): coder autonomy is capability permission tiers, leases, and approval posture (File 06) plus the user's direction; progressive disclosure is which panels and view preset are open; the optional `plan` capability is a tool the agent may call, not a phase machine.
- **Editor/terminal/search/version-control engine choice.** `foundations/stack.md` locks specific implementations. This file keeps those out of the canonical body as replaceable implementations behind contracts (the editor panel, the pseudo-terminal of File 23, the content-search capability, the version-control service), per the source-resolution rule.

## 1. Chosen Model

Anchor: `coder.chosen-model`

ATLAS3 has one `Coder` `WorkSurface`. It is the specialized engineering environment for software work — reading, navigating, editing, reviewing, testing, building, running, and version-controlling code in one or more workspaces — and it is one instance of the `WorkSurface` primitive `worksurface.work-surface` (File 25 §3) defines, classified `Coder` by `core.current-major-area-classification` (File 01 §5.2).

The Coder surface owns user-facing coding workflows and specialized coding views; it owns no private architecture (`worksurface.no-private-architecture`, File 25 §12). It is declared by one `SurfaceContract` (§3) registered in the `SurfaceRegistry` (`worksurface.registry`, File 25 §10), and it composes the shared substrate — blocks, capabilities, capability policy, tool surfaces, execution, the world model, the version graph, workspaces, context assembly, retrieval, memory, routing, artifacts, storage, sync, security, the sandbox, providers, and the ledger — through each one's canonical contract.

The load-bearing model of the Coder surface is the **code-as-artifact reframe**: a code change is an `Artifact` revision carrying validation, review, and provenance state, not a transient file write accompanied by transcript prose. A coder edit produces a versioned file/`CodePatch` block (`block.kind-catalogue` (File 08 §3.1), `artifact.artifact-kind` (File 09 §4)); tests and type checks attach `Validation` blocks; review attaches `Critique` blocks; the version graph carries the history; the ledger carries the execution provenance; and the workspace mirror materializes the active version to disk. Everything a previous IDE-centric design treated as a separate feature — checkpoints, file history, diff, review, run output, codebase index — is a projection over these shared substrates, not a coder-private store.

`Coder` is the canonical surface name; the `surface_id` is `coder` and equals the subsystem id (`capability.capability-source`, File 05 §9.1, `worksurface.work-surface` (File 25 §3.3)). Earlier vocabulary that named the same surface — "coder domain", "coding mode", "IDE", "code workspace", "developer mode" — does not survive as a parallel primitive; "domain" survives only as an informal synonym for the work surface. The anchor namespace for this file is `coder.*`, deliberately distinct from File 07's `surface.*` (tool surfaces), File 25's `worksurface.*`, and File 26's `controlrail.*`.

### 1.1 Boundary

This file defines what the Coder surface is and what it declares and contributes. It does not define how the `SurfaceContract` is registered or composed (File 25), how its tool surface composes (File 07), how its live state is held (File 18), how its files materialize (File 24), how its confined work runs (File 23), how its history is versioned (File 11), or how its views render (the UI specs).

## 2. Boundaries with Adjacent Layers

Anchor: `coder.boundaries`

### 2.1 With File 25 (Work Surface Contract)

This file fills the `SurfaceContract` `worksurface.surface-contract` (File 25 §4) defines: identity (§3), state and panels (§4), the `SubsystemSurfaceSpec` and contributed capabilities (§5), views and presets (§15), and default context/model/execution/sandbox/workspace policies (§14). It obeys the no-private-architecture invariant (`worksurface.no-private-architecture`, File 25 §12), the static-versus-live split (`worksurface.state-declaration`, File 25 §5 — this file declares the shape, File 18 holds the values), the hint-not-fence rule (`worksurface.actions-declaration`, File 25 §6.3), and the deletion of autonomy/participation/interaction-shape fields (`worksurface.no-autonomy-field`, File 25 §13). The Coder surface registers as a `Subsystem`-class source through the proposal-first path (`worksurface.registry`, File 25 §10).

### 2.2 With File 24 (Workspaces and Materialization)

The Coder surface renders over a bound `Workspace` (`workspace.conversation-binding`, File 24 §7); it owns no workspace identity, no disk-history store, and no parallel materialization path (`workspace.explicit-rejections`, File 24 §23). File edits commit sibling blocks that materialize through the disk↔substrate mirror (`workspace.materialization`, File 24 §10); external edits enter through the disk→substrate sync loop (`workspace.disk-sync-loop`, File 24 §12). The coder worktree comparison board, file tree, and history panel are projections over File 24's `WorktreeRecord`s and the version tree (`workspace.consequences-for-later-specs`, File 24 §24). Coder instruction files use the `ATLAS.md` hierarchy and the `ATLAS.coder.md` qualifier (`workspace.instruction-files`, File 24 §9); codebase ingestion uses File 24's mounting and ingestion modes (`workspace.mounted-projects`, File 24 §14). The `.atlas/` internal directory's `commands/`, `settings.json`, and `.env`/`.env.local` are File 24's (`workspace.internal-layout`, File 24 §8).

### 2.3 With File 23 (Sandbox, Process Control, and Isolation)

The Coder surface runs all confined execution through the one `Sandbox` contract (`sandbox.consequences-for-later-specs`, File 23 §21). It declares coder `SandboxProfile`s (`sandbox.contract`, File 23 §3) — a code-execution profile and a preview profile — and extends the base contract only with its language-runtime and preview capability surface; it redefines no lifecycle, filesystem or network enforcement, or kill semantics. The integrated terminal is a `ManagedProcess` on a pseudo-terminal (`process.spawning`, File 23 §5.4); tests, builds, and dev servers are `ManagedProcess`es in `ProcessGroup`s (`process.groups`, File 23 §6), killable categorically and individually (`process.killability`, File 23 §10). Worktree directories are filesystem boundaries File 23 confines (`sandbox.filesystem-enforcement`, File 23 §7).

### 2.4 With File 11 (Version Graph) and Files 08/09 (Blocks, Artifacts)

Coder file history, undo, "checkpoints", and revert are projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24); file edits are sibling `FileAttachment`/`Artifact` blocks linked by `supersedes` (`version.sibling-block-versioning-over-block-pool`, File 11 §12), and revert is `coder.file_reverted` over `version.version-switching` (File 11 §8). The surface introduces no parallel history, checkpoint, undo, or fork store (`version.explicit-rejections`, File 11 §23). Code changes are `Artifact` revisions: the `CodePatch` and file `Artifact` kinds (`artifact.artifact-kind`, File 09 §4), with materialization (`artifact.artifact-materialization`, File 09 §7), validation and critique (`artifact.validation-critique`, File 09 §14), and provenance (`artifact.provenance`, File 09 §15). Everything flows as `Block`s through the one pool (`block.cross-surface-interoperability`, File 08 §12).

### 2.5 With File 12 (Retrieval) and File 13 (Context Assembly)

The Coder surface owns codebase extraction semantics — the language- and structure-extraction that produces file, symbol, import, and call records (`retrieval.ingestion`, File 12 §14.2 delegates extraction to the owning surface) — and consumes File 12's shared index, query, and namespace contract; it indexes into the `ingested_codebase:<workspace_id>` namespace (`retrieval.namespaces`, File 12 §3.2) and introduces no private code-index substrate (`retrieval.explicit-rejections`, File 12 §21). It declares a default `ContextPolicy` and `CompactionPolicy` (`context.context-policies`, File 13 §4) and assembles every model request through the one `ContextAssemblyService` (`context.chosen-model`, File 13 §1); codebase context is the `RetrievedContext` region, the active file and selection are `CurrentInput`, and the `ATLAS.coder.md` contribution is an `InstructionSources` part (`context.instruction-sources-workspace-files`, File 13 §16). It builds no private model-request path (`context.consequences-for-later-specs`, File 13 §22).

### 2.6 With Files 05/06/07 (Capabilities, Policy, Tool Surfaces) and File 16 (Model Strategy)

Coder capabilities are `Capability` declarations in the one registry (`capability.chosen-model`, File 05 §1) with `source: Subsystem { subsystem_id: coder }`; coder-specialized presentations of shared capabilities use adapter capabilities (`capability.adapter-capabilities`, File 05 §17.4 — for example, a `coder.git_commit` adapter over `git.commit`). Approval flows through the one policy layer (`policy.chosen-model`, File 06 §1); the surface references the git-safety reusable-policy rules and templates (`policy.built-in-reusable-policy-rules`, File 06 §11.5, `policy.approval-policy-templates` (File 06 §12)) and contributes a coder approval posture, but evaluates no policy itself. Its tool surface composes through `surface.visibility-composition-resolution-algorithm` (File 07 §9). It declares a default code-capable `ModelProfile` and role preferences (`model.model-profile`, File 16 §4) and implements no private model selection (`model.consequences-for-later-specs`, File 16 §16).

### 2.7 With File 04 (Execution), File 18 (World Model), File 19 (Perception), File 26 (Control Rails)

Coder runs use the shared run lifecycle, ledger, cancellation, budgets, and child-run model (`run.consequences-for-later-specs`, File 04 §29); the coder agent loop and multi-agent coding are run structures over shared semantics, never private execution. The surface self-registers its panels and contributes `File`, `EditorDocument`, `Terminal`, `Process`, and `Workspace` world entities and named availability checks (`world.consequences-for-later-specs`, File 18 §17) and is never screen-scraped to learn its own state (`perception.tiered-sensing`, File 19 §5.4); it consumes the filesystem, repository, terminal, process, debugger, trace, and environment sensors (`perception.sensor`, File 19 §4.3) and never owns a private capture pipeline. Its control affordances are capabilities reachable through the rails (`controlrail.consequences-for-later-specs`, File 26 §21); it registers surface-scoped keybinding contexts and custom commands and owns no private rail.

### 2.8 Boundary

This file is the Coder work-surface declaration and workflow layer. It owns no substrate semantics. It feeds the substrate layers their coder contributions and consumes their contracts.

## 3. The Coder `SurfaceContract`

Anchor: `coder.surface-contract`

### 3.1 Definition

The Coder `SurfaceContract` is the one typed, source-authored declaration of the Coder surface, admitted to the `SurfaceRegistry` (`worksurface.surface-contract`, File 25 §4). It carries the required `SurfaceContract` sections — Identity (§3.2), State (§4), Actions (§5), Views (§15), and Context-and-execution policy (§14) — each filled with coding-specific content and declaring by reference every field whose contract lives in another file.

### 3.2 Identity

The Coder surface declares:

- `surface_id`: `coder`, equal to its `subsystem_id`; the value `routing.run-intent` (File 03 §4.3)'s `primary_surface` resolves to for code work, the prefix of its settings namespace (`surface.coder.*`) and its instruction-file qualifier (`ATLAS.coder.md`)
- `surface_kind`: `Coder` (`worksurface.surface-contract`, File 25 §4.4)
- `display_name`, `description`, `short_description`: localized per the canonical descriptor discipline (`capability.display-fields`, File 05 §3.2); never hardcoded into surface logic
- `keywords`: the routing- and palette-relevant terms the surface is discovered by (representative: code, programming, edit, refactor, debug, test, build, repository, terminal, diff, review)
- `availability_predicate`: a permissive world predicate (`world.state-aware-capability-availability`, File 18 §9.2) — the Coder surface is activatable in any workspace and does not require a repository; repository-, test-, and branch-dependent conditions are expressed as named availability checks (§5.5) that gate individual capabilities and affordances, not the surface's activation

### 3.3 The Required-Section Map

The remaining required sections are filled as: State by §4, Actions by §5, Views by §15, Context-and-execution policy by §14. A coder edit's specialized semantics (§6–§13) elaborate what those sections produce; they are surface workflows over the declared capabilities, not additional contract sections. The declaration is immutable for a registered `surface_contract_version`; contract updates create a new version (`worksurface.surface-contract`, File 25 §4.2). Registry state (trust, scoped enable, availability) lives on the registered entry, not the declaration.

### 3.4 Boundary

This section fixes the contract's coder content at the section level. File 25 owns the contract shape and the registry; the per-section coder semantics are §§4–18.

## 4. State Declaration — Panels and Selection

Anchor: `coder.state-declaration`

### 4.1 Definition

The Coder surface declares the panels it can mount and the selection kinds it produces. This is the static counterpart of the live `SurfaceState` (`world.surface-state`, File 18 §5): this file declares the shape, File 18 holds the live values. Panels self-register their live state to the world model on mount and update on focus, selection, and content change (`world.observation-state-update`, File 18 §8.1); a panel the surface fails to register is a blind spot the agent cannot use.

### 4.2 Declared Panel Kinds

The Coder surface declares the following panel kinds, drawn from the canonical baseline (`worksurface.state-declaration`, File 25 §5.3) plus coder `Custom` kinds registered through the proposal-first mechanism. Each declares the typed shape of its compact state-field summary (a path, a working directory, a selected entry — never the resource body, `world.surface-state` (File 18 §5.2)), the selection kinds it produces, and its control affordances:

- `editor` — a code buffer over a `FileAttachment`/`Artifact` block; carries the active file path, caret position, selections, viewport range, and dirty state; produces `CodeRange` and symbol selections; the editor engine is a replaceable UI implementation behind the panel
- `terminal` — a pseudo-terminal session (§10); carries the working directory, the running command if any, and a `canStop` affordance
- `file_tree` — a workspace directory projection; carries expanded directories and selected files, with per-file version-control status surfaced from the repository observation (§9); produces `File` selections; honors the workspace ignore file
- `diff` — a change view between two versions (working-vs-staged, working-vs-head, or two `ContextVersion`s); supports per-chunk navigation and revert; produces `CodeRange` selections
- `search` — a workspace content-search projection; carries the active query and its scope; produces `File` and `CodeRange` selections
- `problems` — a diagnostics projection over `Validation` blocks and language-intelligence results (§11)
- `context_inspector` — the files currently in the model context, with per-`(block, tokenizer)` token counts and index-progress state; an inspector projection over context-assembly and retrieval state, not a private store
- `preview` — a render of a running application or build output (§10), carrying the spawn context and the captured output
- `worktree_comparison` — a side-by-side comparison of parallel-agent results, a projection over `WorktreeRecord`s and the version tree (§13)
- `history` — a version-tree projection (§8), carrying the timeline and per-version metadata

A panel kind a coder panel declares is a shared substrate projection, not a private widget: the `editor` and `terminal` kinds are cross-surface roles (`worksurface.state-declaration`, File 25 §5.4), and another surface may embed a coder panel without changing its primary surface.

### 4.3 Selection Kinds

The Coder surface produces selections of canonical kind `CodeRange`, `File`, and `BlockRange` (`world.surface-state`, File 18 §5.4), plus a registered `Custom` symbol-selection kind where a selection addresses a named code symbol rather than a character range. A selection carries a short summary and typed bounds, not the selected text.

### 4.4 The Static-versus-Live Split

The declaration is the static shape; the live values — which panels are open, which is primary, what is focused and selected, the current `UiMode`, and the available-capability list — are the live `SurfaceState` File 18 holds. The Coder surface declares no participation, autonomy, or interaction-shape field on its state (§22); `UiMode` (`Normal`, `CommandPalette`, `Modal`, `Fullscreen`, and the surface's registered modes) is interaction state, never an autonomy control (`world.surface-state`, File 18 §5.5).

### 4.5 Boundary

This section declares the coder panel and selection shape. File 18 holds the live values and owns the self-registration contract; the UI specs own panel presentation; the editor engine, terminal renderer, and content-search engine are replaceable implementations behind the panels.

## 5. Actions Declaration — the Coder `SubsystemSurfaceSpec`

Anchor: `coder.actions-declaration`

### 5.1 Definition

The Coder surface's actions declaration is its `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5) plus the artifact, observation, and sensor kinds it primarily produces or exposes and the approval-policy posture it contributes. This file references the `SubsystemSurfaceSpec` contract; it owns no zone, composition, or borrowing mechanics, which are File 07's.

### 5.2 Contributed Capabilities and Zones

The Coder surface contributes its capabilities to the one registry with `source: Subsystem { subsystem_id: coder }`, declared per `capability.declaration` (File 05 §3) and registered through the proposal-first path (`capability.runtime-mutation`, File 05 §16.2). The capability families the surface contributes or relies on, and their default zone (`run.zones`, File 04 §10.2, `surface.zone-model` (File 07 §3)), are:

- **File operations** (`Primary`): read, create, edit, patch, delete, move, copy, list, stat, and content-search capabilities over workspace files; the universal fallback for any code change (§6)
- **Semantic code operations** (`Primary`, with callable availability gated by language-intelligence checks): rename-symbol, move-symbol, update-imports, and equivalent structure-aware edits that compile down to audited file/artifact version changes (§6.4)
- **Code execution and shell** (`Primary`): command execution, background-process spawning, status, wait, signal, job listing, and pseudo-terminal capabilities; and the programmatic-execution capability that chains tool calls deterministically (§10), each running confined (§14.4)
- **Tests, build, lint, type-check, and format-check** (`Primary`): capabilities that run a project's checks and produce `Validation`/`Critique` blocks (§11)
- **Format-apply** (`Primary`): formatting capabilities that mutate files; they are edit/artifact-revision operations routed through the same policy, staleness, atomic-write, and version-commit path as other code changes (§11)
- **Debugging and tracing** (`Primary` when a registered adapter is available, otherwise unavailable): breakpoints, stack frames, variable inspection, process attach/launch, traces, and debugger-derived observations, all mediated through capabilities, sandbox/process controls, policy, and the observation/provenance substrate (§10–§11)
- **Version control** (`Primary`): the `git.*` status, diff, log, blame, stage, unstage, commit, branch, checkout, stash, fetch, pull, push, and worktree capabilities (§9), declared domain-neutral and surfaced through the coder UI projection
- **Codebase context** (`Primary`): codebase ingestion, code search across the index modes (§7), and the reference-attachment capability that brings files and symbols into context
- **Planning, review, discovery, and orchestration** (`Primary`): the shared `plan` capability (§14.5), the review/critique capabilities (§12), the discovery capabilities (`tool.search`, `tool.borrow`, `surface.late-loading-runtime-discovery` (File 07 §7)), and the sub-agent-spawn capability (§13)
- **Borrowable** capabilities: web search and fetch, memory recall and store, and image generation and editing — present in the `Borrowable` zone for occasional cross-surface reach
- **Default-deferred families** (the surface's `default_deferred_families`, `surface.subsystem-surface-spec` (File 07 §5.1) — deferred out of the surface's default zones into the `Deferred` zone, still reachable by explicit borrow with a typed denial where policy forbids): GUI-control, data-processor, teacher, and system-agent capability families, which are out of scope for default coder composition

The capability lists are representative hints, not a closed fence (§5.4). The full set varies with installed capabilities, plugins, and the active workspace's per-workspace zone overrides (`workspace.settings`, File 24 §21).

### 5.3 Produced Kinds and Exposed Sensors

The Coder surface declares the artifact, observation, and sensor kinds it primarily produces or exposes (`worksurface.actions-declaration`, File 25 §6.2):

- **Primary `ArtifactKind`s**: `CodePatch` (a structured patch over one or more files), the file `Artifact`, and `Document` (for code-adjacent prose such as design notes and generated reports) (`artifact.artifact-kind`, File 09 §4); coder-specialized kinds register through the canonical mechanism
- **Primary `ObservationKind`s**: `RepositoryState`, `TerminalOutput`, `FileSnapshot`, `ProcessState`, `EnvironmentSnapshot`, `WorkspaceSnapshot`, and coder-registered debugger-state and trace-excerpt observations (`artifact.observation`, File 09 §13.2), produced through the canonical `observation.commit` path
- **Exposed sensors**: the filesystem, repository, terminal, process, debugger, trace, and environment sensors (`perception.sensor`, File 19 §4.3), each with its declared privacy class; the surface consumes these sensors' structured output and owns no capture mechanics

### 5.4 The Hint-not-Fence Rule

The Coder surface's `primary_capability_ids` are a hint about what is most relevant for code work, not a fence around what the agent may invoke (`worksurface.actions-declaration`, File 25 §6.3). The agent reaches any capability in the one registry through the discovery and borrow capabilities, subject to policy; a coder run that needs `web.fetch` to read a library's documentation borrows it and remains in the Coder surface, with the ledger recording both the originating surface and the borrowed-capability source. Cross-surface access defaults to search-and-borrow, never silent autoload (`run.consequences-for-later-specs`, File 04 §29).

### 5.5 Contributed Approval Posture and Named Availability Checks

The Coder surface contributes a default approval posture and references the policy templates and reusable-policy rules File 06 owns; it evaluates no policy itself:

- the git-safety reusable-policy rules (`policy.built-in-reusable-policy-rules`, File 06 §11.5): a force-push to a branch in the configured protected-branch list resolves to `AlwaysDeny` with typed-confirmation override; `git.push`, `git.pull`, and `git.fetch` default to `UserApproval` and `git.push` is never lifted by `agent.unrestricted_mode`; file edits proposed against a protected branch surface a redirect to a branch-creating capability
- the dedicated-tool-preference and fetch-fallback templates (`policy.approval-policy-templates`, File 06 §12.4): a shell capability invoked with a pattern that has a registered dedicated equivalent (a status, log, diff, list, read, content-search, or fetch operation) is redirected to the dedicated capability at the configured strictness, so coder tool use stays inspectable and audited; an explicit raw-shell bypass remains possible where policy allows it, with the bypass reason and policy decision recorded
- shell and custom-command execution preview: mutating shell work carries touched-resource, preview, and expected-postcondition metadata where inferable or declared by the command profile; when no reliable preview is available, approval presentation says so explicitly rather than implying the command was understood
- a cross-workspace file-access escalation: a file capability whose resolved path lies in another workspace escalates to `UserApproval` and surfaces which workspace is targeted (`workspace.conversation-binding`, File 24 §7.2)

The Coder surface registers named availability checks (`world.state-aware-capability-availability`, File 18 §9.3) the world model evaluates against the current snapshot — representative: workspace-is-a-repository, has-staged-changes, has-unsaved-changes, on-a-protected-branch, tests-present, and language-intelligence-available — each a pure function of the world snapshot that gates the availability of specific capabilities and affordances.

### 5.6 Boundary

This section declares the coder actions by reference. File 05 owns the capability declarations and adapter mechanism; File 06 owns the policy evaluation, templates, and reusable-policy rules; File 07 owns the `SubsystemSurfaceSpec` and composition; Files 09 and 19 own the artifact, observation, and sensor kinds. This file names what the surface contributes; those files own how.

## 6. The Code-Editing Contract

Anchor: `coder.code-editing`

### 6.1 Definition

The code-editing contract is the set of rules by which the Coder surface changes code: a code change is an `Artifact` revision, produced by edit and patch capabilities whose multiple edit formats are capability sub-modes, applied with read-before-edit revalidation and atomic materialization, and recorded as a versioned, validatable, reviewable, citable block.

### 6.2 Code Change as Artifact Revision

A coder file is a `FileAttachment`/`Artifact` block whose content is the source of truth (`block.kind-catalogue`, File 08 §3.1, `artifact.artifact-version` (File 09 §6)). An edit creates a new sibling block linked by `supersedes` and advances the active reference in the materialized view (`version.sibling-block-versioning-over-block-pool`, File 11 §12.2); the materializer rewrites the file on disk (`workspace.materialization`, File 24 §10). A coherent set of changes across one or more files is a `CodePatch` artifact version (`artifact.artifact-kind`, File 09 §4) carrying its diff content and target paths, with the derivation summary and producing context recorded on the version (`artifact.version-creation`, File 09 §6.3). A code change therefore carries validation state (§11), review state (§12), and provenance (`artifact.provenance`, File 09 §15) — it is never only transcript prose, and artifact-grade content is never stored only as an assistant message (§22).

### 6.3 Edit-Format Sub-Modes

The Coder surface's edit and patch capabilities support multiple edit formats as capability sub-modes within one capability, not as separate capability calls (`capability.capability`, File 05 §2.3, `run.tool-calls` (File 04 §9)). The canonical edit-format design space the surface supports through its capabilities includes targeted string replacement (a unique old-string-to-new-string substitution, validated to match exactly once), structured diff application (a context-matched patch with add/update/delete/move operations across one or more files), whole-file replacement (for new files or extensive change), and tolerant matching (a graduated exact-then-normalized match that may absorb insignificant formatting only where a registered language-aware matcher, parser, or formatter declares semantic equivalence). Quote changes, escaping changes, raw-string changes, interpolation changes, and other syntax-affecting normalization are never treated as generally benign; if equivalence cannot be established for the file's language and mode, the capability returns a typed ambiguity or no-match error. The capability resolves the appropriate sub-mode internally and passes through one validation, one approval, and one ledger entry; the specific format syntax is a capability-declaration and implementation concern, not a canonical body concern. The contract this file fixes is: every edit format produces the same artifact-revision outcome, validates uniqueness or context where the format requires it, and surfaces a typed error rather than silently mis-applying when a match is ambiguous or absent.

### 6.4 Semantic Code Operations

The Coder surface contributes semantic code operations — rename-symbol, move-symbol, update-imports, and equivalent structure-aware transformations (`codex_recommendations.md` §7.1) — as capabilities that operate over the codebase symbol and import model (§7) and **compile down to audited file and artifact version changes**: a semantic operation resolves the affected files, produces the edits, and commits them as ordinary artifact revisions through the same pipeline as a raw edit, so policy, validation, history, and provenance apply identically. Semantic operations are callable only where the language intelligence to resolve symbols and references is present (the named availability check of §5.5). Where it is absent, the capability remains a Coder-owned primary affordance but returns a typed unavailable or degraded result, and the agent and user fall back to the raw file-operation capabilities, which remain the universal fallback. Optional plugin-provided semantic providers register as their own capabilities and may be discovered, borrowed, or loaded through File 07; absence of language intelligence is not a zone transition for the Coder-owned operation.

### 6.5 Read-before-Edit and Staleness

A coder mutation that depends on a prior read revalidates currency before mutating (`run.call-pipeline`, File 04 §8.2, `artifact.observation` (File 09 §13)): the prior read records the file's modification time and content hash, the edit carries the expected values, and a mismatch returns a typed staleness error (`FileChangedSinceRead`/`StateChangedSinceObservation`, `workspace.atomic-write` (File 24 §13.2)) rather than overwriting an intervening change. The agent receives the typed error in-band and may re-read and retry, branch, or stop. This is the coder realization of the canonical stale-state revalidation; the surface enforces no separate mechanism.

### 6.6 Atomic and Streaming Materialization

Every coder write is staged and atomically promoted through File 23's atomic-write chokepoint (`sandbox.filesystem-enforcement`, File 23 §7.3, `workspace.atomic-write` (File 24 §13.2)): content is written to a temporary path in the same filesystem boundary, made durable, then renamed over the destination, so a cancelled or failed write never leaves a partially written file. A capability whose input is a content payload may stream the content into the staged file as the model emits it — the user sees the content appearing live in the editor — with the atomic rename and the artifact-version commit only at the call's commit point (`run.streaming-partial-execution`, File 04 §12, `block.live-partial-write-capabilities` (File 08 §7.5)). If the stream fails or is killed before commit, the destination remains unchanged and the staged partial is discarded by default; a capability may retain the staged partial only as a non-materialized orphan draft when it declares recovery safe and policy allows explicit user adoption. The Coder surface emits a `coder.file_partial_write` event the editor panel consumes for incremental rendering (§21); it introduces no progress-bar or partial-state store, and no partial write is silently promoted.

### 6.7 Boundary

This section defines the coder editing contract. File 08 owns the block and content hash; File 09 owns the artifact and materialization; File 11 owns the version commit; File 23 owns the atomic-write primitive and filesystem boundary; File 24 owns the disk mirror. This file owns the codebase symbol and import model the semantic operations resolve against (§7.2); File 12 owns the index, query, namespace, chunking, and ranking over it (`retrieval.ingestion`, File 12 §14.2 delegates code-extraction semantics to the owning surface). This file owns the coder workflow over them.

## 7. Codebase Context and Indexing

Anchor: `coder.codebase-context`

### 7.1 Definition

Codebase context is the structured model of a workspace's code the Coder surface maintains so the agent and user can navigate, search, and reason over a codebase rather than over conversation history alone. The Coder surface owns the **extraction semantics** — what entities and relations a codebase yields — and consumes the shared retrieval substrate for indexing, query, and namespace (`retrieval.ingestion`, File 12 §14.2 delegates code-extraction semantics to the owning surface; `retrieval.core-model` (File 12 §1) owns the index and query contract).

### 7.2 The Coder Codebase Model

The Coder surface declares the codebase entity and relation model it extracts: files and directories; symbols (functions, classes, methods, types, modules, and equivalents); imports and exports; call and reference relations; and the project's declared build and test units where a manifest declares them. These compose, per `codex_recommendations.md` §8.2, into a symbol graph, a dependency (import) graph, and a build/test graph the surface and the agent reason over. The extraction is language- and structure-aware: a language-structure parser produces the per-language symbol and relation set, and a content-search engine produces lexical matches; both are replaceable implementations behind the surface's extraction capability. Extraction commits its records through the canonical indexing pipeline (`retrieval.indexing-pipeline`, File 12 §12); the surface may supply query-intent hints such as symbol lookup, reference search, or impact analysis, but File 12 owns ranking, fusion, lifecycle filtering, and the retrieval result envelope. The surface maintains no private code-entity store (`retrieval.explicit-rejections`, File 12 §21).

### 7.3 Indexing and Freshness

Codebase indexing is event-first and incremental (`retrieval.maintenance-freshness`, File 12 §18, `world.observation-state-update` (File 18 §8.6)): the filesystem and repository sensors (§5.3) drive re-indexing of changed files through the disk→substrate sync loop and repository observations, coalesced through the watcher's debounce. Re-indexing of unchanged inputs is avoided through a resolved extraction-identity cache keyed by the file content hash plus the declared extraction inputs that can affect output: extractor identity and version, language mode, relevant project configuration, extraction settings, and path only where path affects semantics. Extractor or configuration changes invalidate affected entries through File 12's indexing pipeline. Indexing distinguishes the cheap deterministic structural extraction (symbols, imports, calls) from any expensive model-mediated extraction, performing the cheap path on every change and the expensive path on demand or at a declared thoroughness. The current-edit file and open files take indexing and search priority over background files. A polling or scheduled re-scan is a flagged, configurable fallback only where a source emits no change events, never a correctness condition.

### 7.4 The Retrieval Namespace and Index Modes

The Coder surface indexes a workspace's code into the workspace-qualified retrieval namespace `ingested_codebase:<workspace_id>` (`retrieval.namespaces`, File 12 §3.2) and queries it through the shared retrieval contract using the index modes the substrate provides (`retrieval.retrieval-index`, File 12 §2.2): structural (symbol, path, and signature lookup), lexical (content and term search), graph (call- and import-relation traversal), and dense (semantic similarity), combined through the substrate's hybrid ranking. The surface's code-search capability is the agent- and user-facing operation over these modes; it contributes code-aware query intent, then receives the normalized retrieval hit envelope (`retrieval.retrieval-result`, File 12 §9) with source spans so results are citable, highlightable, and promotable to durable context without copying whole files into the transcript.

### 7.5 Mounted Projects and Ingestion

A coder workspace may bind an existing external codebase through File 24's mounting and ingestion modes (`workspace.mounted-projects`, File 24 §14): the surface presents the ingestion as a previewed operation, indexes the mounted source into the workspace namespace, and treats instructions embedded in ingested code as untrusted content with no capability or policy authority (`security.untrusted-content`, File 22 §12, `workspace.mounted-projects` (File 24 §14.3)). The surface owns no ingestion identity or copy policy, which are File 24's.

### 7.6 Code-Aware Context Assembly

The Coder surface declares a code-aware default `ContextPolicy` (§14.2) that assembles codebase context as the `RetrievedContext` region (code-search results and the symbol/relation context for the active work), the active file and selection and code-aware mentions as `CurrentInput`, recent selected terminal/build/debug output where relevant, and the `ATLAS.coder.md` instruction contribution as an `InstructionSources` part — all through the one `ContextAssemblyService` (`context.assembly-algorithm`, File 13 §6). Code-aware mentions (a file, folder, symbol, problem, or repository reference the user types) resolve to attributed context parts with source attribution; they are not hidden model-request text. Long build, test, trace, and command output is redirected to referenced sources rather than flooded into context, selected ranges are attributed, and the model receives enough metadata to request more (`context.current-input-oversize-handling`, File 13 §7).

### 7.7 Boundary

This section owns the coder codebase model and the surface's extraction and search workflow. File 12 owns the index, query, namespace, chunking, and ranking; File 24 owns ingestion identity and mounting; File 13 owns context assembly; File 18 and File 19 own the observations and sensors that drive freshness. The language-structure parser and content-search engine are replaceable implementations behind the surface's extraction capability.

## 8. File History, Undo, and Checkpoints

Anchor: `coder.file-history`

### 8.1 Definition

Coder file history, undo, and "checkpoints" are the user-facing presentation of the workspace's code evolution. They are a projection over the one version graph (`version.consequences-for-later-specs`, File 11 §24); the version tree is the single file-history mechanism, and the on-disk workspace is its materialized view (`workspace.materialization`, File 24 §10). The Coder surface introduces no parallel checkpoint, snapshot, or undo store.

### 8.2 The History Panel as a Version-Tree Projection

The history panel renders the conversation's version tree: each commit boundary (`version.version-op-summary-commit-boundary-set`, File 11 §5) — an accepted agent turn, a context edit, an external edit, an artifact-version commit — is a point in the timeline, and switching to a version restores all workspace files to their state at that point (`version.version-switching`, File 11 §8), with the materialized view and the on-disk files and open editor tabs updating to match. The panel supports multi-level navigation, all derived from version diffs rather than a per-chunk store: feature-level (an agent turn), tool-call level (an individual edit within a turn), and chunk level (a line range within an edit). A "checkpoint" in coder vocabulary is exactly one version-graph node; the prior "one checkpoint per tool call" and shadow-directory models are superseded (§22).

### 8.3 Undo, Revert, and Restore

Within an in-progress turn, undo of an uncommitted operation walks the pending-operations buffer (`version.pending-operations-buffer`, File 11 §6); after a turn commits, the way to undo is to switch to or branch from a prior version. Reverting a single file is `coder.file_reverted` (`version.sibling-block-versioning-over-block-pool`, File 11 §12.2), resolved by one of two paths: a forward revert that commits a new context-edit version swapping the active file block back to a historical sibling (advancing the current branch), or a switch revert that moves the conversation's active version to one where the historical sibling was active (both branches surviving). The editor's undo and save affordances hand off to this version mechanism; the editor maintains no separate file-history store. The diff panel and diff viewer are the revert UI: a chunk-level revert is a forward edit that swaps the affected lines.

### 8.4 Boundary

This section owns the coder history and revert workflow. File 11 owns the version graph, the materialized view, version switching, branching, and the pending buffer; File 24 owns the disk mirror the switch updates; File 08 owns the sibling-block edit. This file projects them into the coder history and diff UI.

## 9. Version-Control Workflow

Anchor: `coder.version-control`

### 9.1 Definition

The coder version-control workflow is the surface presentation over the domain-neutral version-control capability family. Until a dedicated version-control or external-integration spec exists, this file declares the default `git.*` family as shared built-in capabilities (`capability.sourcing`, File 05 §9) surfaced primarily through the Coder surface; a later spec may refine the transport and provider details — remote authentication, hosted-forge integration — without changing the capability contract. Version control is an infrastructure service exposed as the `git.*` capabilities, callable by any surface; the Coder surface adds the user-facing workflow and views — status surfacing, diff, commit, branch, blame, stash, the comparison board, and the worktree-backed multi-agent workflow. The surface owns no private version-control mechanism, store, or path; the version-control library behind the `git.*` capabilities is a replaceable implementation, and worktree identity and lifecycle are File 24's (`workspace.worktree`, File 24 §15).

### 9.2 The Version-Control UI Projection

The Coder surface projects version-control state from the repository observation (§5.3) and the `git.*` capabilities into its panels: the file tree carries per-file status (modified, added, deleted, unmerged, renamed, untracked) surfaced from the repository status; the diff panel renders the change for a file against the working tree, the staged index, the head, or a remote; the status bar carries the current branch, ahead/behind counts where a remote is tracked, and a change summary. Repository status updates are driven event-first from the repository and filesystem sensors, with a flagged polling fallback only where the platform emits no change signal.

### 9.3 Commit, Branch, Blame, and Stash

The Coder surface presents the commit workflow (propose a message, show the staged change, stage and commit through the `git.*` capabilities), branch management (list, create, switch, delete, rename), blame (per-line authorship with drill-down to the commit), and stash (save, list, apply) as views over the version-control capabilities. The capabilities carry the permission tiers their blast radius warrants (`policy.effective-tier-resolution`, File 06 §4): read operations (status, log, diff, blame, list) at `ReadOnly`; staging, committing, branching, and stashing at `WorkspaceWrite`; destructive operations (branch deletion, worktree removal) and network operations (push, pull, fetch) at `UserApproval`; and `git.push` is held behind approval unconditionally — it is not lifted by `agent.unrestricted_mode`, and a force-push to a protected branch carries the `Denied`-floor typed-confirmation rule (`policy.built-in-reusable-policy-rules`, File 06 §11.5). A coder-specialized commit presentation may be an adapter capability over the neutral `git.commit` (`capability.adapter-capabilities`, File 05 §17.4), recording both the adapter and the resolved target in the ledger.

### 9.4 The Comparison Board and Worktrees

The comparison board is a projection that presents multiple branches or parallel-agent results side by side — their diffs, change counts, and previews — with a select-for-merge affordance. It reads `WorktreeRecord`s (`workspace.worktree`, File 24 §15) and the version tree; it is not a new primitive (`workspace.consequences-for-later-specs`, File 24 §24). Selecting a result does not mutate the target workspace by itself. Applying the selected result is a capability invocation — a git merge, cherry-pick, squash, patch adoption, or file-level adoption — that produces a preview, passes policy, records the decision and outcome in the ledger, and handles conflicts explicitly. The multi-agent worktree workflow (§13) creates a worktree per parallel agent through File 24's worktree capabilities, runs each agent confined to its worktree, presents the results on the comparison board, and applies selected results only through that capability path. The surface owns the comparison and selection presentation; the worktree directory identity, placement, and lifecycle are File 24's, and File 23 confines the directory.

### 9.5 Boundary

This section owns the coder version-control workflow and views. The `git.*` capabilities are declared per File 05 and gated per File 06; worktree identity and lifecycle are File 24's; the version-control library is a replaceable implementation. Hosted-platform integration (pull-request review and merge through a remote forge) is a connector concern for a later integration spec, reached through the borrowable external-integration capabilities, not a coder-private mechanism.

## 10. Terminal and Code Execution

Anchor: `coder.terminal-execution`

### 10.1 Definition

The Coder surface's terminal and code-execution model is how it runs commands, processes, tests, builds, dev servers, debugger sessions, trace captures, and previews. Terminal sessions are `ManagedProcess` work on pseudo-terminals (`process.spawning`, File 23 §5.4); all other code execution is `ManagedProcess` work in a `ProcessGroup` confined by a coder `SandboxProfile` (`sandbox.contract`, File 23 §3). The surface owns no private process spawner, sandbox, or kill path (`sandbox.consequences-for-later-specs`, File 23 §21).

### 10.2 The Terminal Panel

The terminal panel presents one or more pseudo-terminal sessions: the runtime spawns each shell as an explicit program on a pseudo-terminal, with the working directory defaulting to the workspace root, and with an environment resolved through the allowlist policy that excludes path-, linker-, and interpreter-controlling variables by default (`process.spawning`, File 23 §5.3). Workspace environment files are discovered as environment sources, not blindly injected; variables from them enter a terminal or process only through `EnvPolicy`, explicit user approval, profile settings, or `SecretRef` binding, and raw secret values are never materialized into prompts, logs, or exports. Each terminal's output is captured into a bounded rolling buffer so a late-attaching observer can catch up; the buffer is a transient projection, not a durable record. A selected output range, failed-test excerpt, stack trace, or command-output span that a run depends on is committed as an attributed `TerminalOutput` observation or source excerpt linked to the process, command, artifact, or validation result. Each terminal session is a distinct `Terminal` world entity carrying its working directory, running command, sandbox/process binding, buffer identity, and stop affordance (§19); terminal sessions are killable individually and categorically through the run or process group they belong to. The surface auto-detects and activates common language and toolchain environments where present, and assists the user in configuring an unfamiliar stack; environment detection is observed, not assumed.

### 10.3 Code Execution, Tests, Builds, and Dev Servers

A coder run executes code — a test run, a build, a lint, a script, a dev server, a debugger session, or a trace capture — as a `ManagedProcess` in a `ProcessGroup` confined by the coder `SandboxProfile` (§14.4), killable categorically and individually (`process.killability`, File 23 §10). Long-running jobs (installs, builds, test suites, watch processes, preview servers, debugger sessions) run with finite wall-clock safety guards that are configurable per profile, workspace, and run, never correctness conditions (`sandbox.resource-limits`, File 23 §9.3). Defaults must be generous enough for normal long-running development work, and the user or policy may extend a guard before termination where allowed; the spec defines no concrete duration. Process, debugger, trace, and resource events drive the surface's status, problems, and observation projections. Mutating shell work carries touched-resource, preview, and postcondition metadata where inferable or declared; when unavailable, the approval UI states that no reliable preview exists. The programmatic-execution capability (`run.programmatic-execution`, File 04 §14) lets a coder run chain capability calls deterministically — iterating over files, transforming, and editing in one execution unit — with each inner call passing through the full pipeline, approval, and ledger.

### 10.4 The Preview

The preview panel renders a running application or build output: the surface spawns the run command as a confined `ManagedProcess` under a preview `SandboxProfile` (§14.4), captures its output (a served page, a rendered window, or command output), and displays it in a resizable view with optional device-frame simulation. The preview runs with the narrowest filesystem and network policy its work needs — workspace-only filesystem and no network by default, widened only by explicit opt-in through policy — and a bounded resource and time guard. Preview is a presentation of a confined process; it owns no sandbox mechanism.

### 10.5 Boundary

This section owns the coder terminal and execution workflow. File 23 owns the `Sandbox` contract, the `ManagedProcess` and `ProcessGroup` model, the pseudo-terminal, the filesystem/network/resource enforcement, and killability; File 04 owns the run, programmatic execution, budgets, and cancellation; File 19 owns the terminal and process sensors. The terminal renderer is a replaceable UI implementation behind the panel.

## 11. Validation, Formatting, and Runtime Diagnostics

Anchor: `coder.validation`

### 11.1 Definition

The Coder surface treats tests, build, lint, type-check, format-check, debugger observations, and trace checks as validation or diagnostic inputs: capabilities that run a project's checks or inspect its runtime state and produce `Validation`, `Critique`, or `Observation` blocks (`artifact.validation-critique`, File 09 §14), which derive the validation state of the code artifacts they target and feed the problems projection. A formatter mode that mutates files is not validation-only: it is a code edit that produces artifact revisions through the editing pipeline, and may also attach a validation result after the formatted files satisfy the formatting rule.

### 11.2 Validation Capabilities and State

A coder validation capability runs a check — a test suite, a build, a linter, a type-checker, a format-checker, a debugger-derived assertion, or a trace check — as confined execution (§10.3), captures its result, and commits a `Validation` block of the appropriate kind (test, build, type-check, lint, format, runtime-check, trace, or equivalent) linked to the target artifact version by the validation edge (`artifact.validation-state-derivation`, File 09 §14.2); test, type-check, and lint map to the canonical `validation_kind` enum, while build, format, runtime-check, and trace register as coder `Custom { namespace: "coder", name }` kinds beyond File 09 §14.1's base enum (`artifact.validation-critique`, File 09 §14.1). A mutating formatter runs as `format-apply`: it proposes and applies file edits through §6, then may produce a format validation block over the resulting artifact version. A passing required validation moves the artifact version toward `Validated` lifecycle; a failing required validation derives a failed state and surfaces the failure. This realizes `codex_recommendations.md` §8.2's "code changes are artifact revisions with validation state": a code change is not done because the agent says so; it carries the recorded outcome of its checks. The deterministic completion floor (`run.termination`, File 04 §22) still applies — a coder run whose contract required action cannot complete on prose alone.

### 11.3 Diagnostics and the Problems Projection

The problems panel projects diagnostics from the structured results of validation capabilities, language-intelligence diagnostics where available, debugger observations, trace checks, and selected runtime output. This includes the edit-then-diagnose feedback loop in which an edit's resulting errors are surfaced back to the agent and user. Diagnostics are a projection over `Validation`, `Critique`, and `Observation` records, not a private store; they carry per-file, per-range, process, or trace locations so the editor and terminal panels can highlight them and the agent can act on them in-band.

### 11.4 Test Impact and Critique

Where the codebase model (§7) supports it, the surface may scope a test run to the impact of a change (the tests reachable from the changed symbols) rather than the whole suite, recording the scoping as part of the validation's metadata. A review pass (§12) produces `Critique` blocks — evaluative findings — that do not themselves gate validation state but inform the user and the agent; only `Validation` blocks contribute to validation state (`artifact.validation-critique`, File 09 §14.4).

### 11.5 Boundary

This section owns the coder validation workflow. File 09 owns the `Validation`/`Critique`/`Observation` contracts and the validation-state derivation; File 04 §22 owns the completion floor and the verification hook surface; File 10 owns the events. The test, build, lint, type-check, format-check, format-apply, debugger, and trace runners are project- and language-specific implementations behind the capability declarations.

## 12. Code Review

Anchor: `coder.review`

### 12.1 Definition

Code review is the Coder surface workflow for evaluating a change before it is accepted: a review pass produces evaluative findings as `Critique` blocks and per-change accept/reject/modify decisions, and the change's validation and review state gate its artifact lifecycle. Review is a first-class coder concern, consistent with `codex_recommendations.md` §8.2's "review mode" and the agent-native-review framing.

### 12.2 The Review Workflow

A review may be performed by the user, by a reviewer sub-agent (§13), or by an external reviewer. It produces a `Critique` block of kind code-review (`artifact.validation-critique`, File 09 §14) carrying findings with severity, location, description, and an optional suggested resolution, and a recommended action (accept as is, revision recommended, revision required, or reject and restart). Review findings render as inline comments anchored to code ranges in the diff and editor panels, and as a review summary; they are advisory and do not by themselves gate state.

### 12.3 Per-Change Accept, Reject, and Modify

The Coder surface presents proposed code changes for per-change decision: the user may accept a change, reject it (removing the proposed edit from the pending buffer before commit, `version.pending-operations-buffer` (File 11 §6)), or modify it (editing the proposed content before accepting). Multiple pending changes in one execution boundary are presented through the shared batched-approval flow (`policy.batched-approval-flow`, File 06 §5.5), which lists the proposed file edits, creations, and commands together with allow/deny decisions; the surface owns no parallel approval flow. Acceptance commits the change as an artifact revision; rejection and modification reshape the pending buffer before commit.

### 12.4 Review and Validation Gate Lifecycle

A code artifact's lifecycle (`artifact.artifact-lifecycle`, File 09 §5.1) is gated by review and validation: a change moves toward `Validated` when its required validations pass, and toward accepted when the user (or an authorized reviewer) accepts it. The surface presents the change's lifecycle and review state in the inspector; it derives them from the version graph and the validation and review blocks, not from a private state field.

### 12.5 Boundary

This section owns the coder review workflow. File 09 owns the `Critique` and `Validation` contracts and the artifact lifecycle; File 06 owns the batched-approval flow; File 11 owns the pending buffer and version commit. Hosted pull-request review through a remote forge is a connector concern (§9.5).

## 13. Multi-Agent and Parallel Coding

Anchor: `coder.multi-agent`

### 13.1 Definition

Multi-agent and parallel coding is the Coder surface workflow for running multiple agents on a codebase concurrently — parallel attempts at the same task, a division of labor across a task, or a reviewer-and-implementer split. It composes child runs (`run.child-runs-multi-agent-work`, File 04 §16) and worktrees (`workspace.worktree`, File 24 §15); the surface owns no private orchestration, isolation, or merge mechanism.

### 13.2 Worktree-Isolated Parallel Work

When parallel agents would conflict on the same files, each runs in its own worktree: a coordinating run spawns a child run per worktree, each confined to its worktree directory (`run.isolation`, File 04 §16.2, `sandbox.filesystem-enforcement` (File 23 §7)), working on its own branch. The canonical isolation primitive for code-touching child runs is the git worktree (`run.isolation`, File 04 §16.2); the worktree directory identity, data-root placement, and lifecycle are File 24's. When child runs share the workspace non-destructively — a single codebase the user is also editing, parallel non-interfering reads — the shared-workspace exception applies and no worktree is created (`run.isolation`, File 04 §16.2); the isolation decision is File 04's per-child-run policy, and the surface presents whichever the runtime selected.

### 13.3 Spawnable Sub-Agents and Merge

The Coder surface declares the sub-agent types it can spawn (`worksurface.runtime-execution-declaration`, File 25 §9.2) — representative: a read-only explorer, an implementer, a reviewer, and a tester — each running under the coder surface defaults as a child run. Parallel results return through the canonical child-run output contracts (`run.merge`, File 04 §16.4): a child run does not mutate the coordinator's state directly; its result returns as a patch, summary, artifact, evidence set, or validation report, and the coordinator or user selects which result to apply. Applying a selected result is a normal capability invocation with preview, policy, conflict handling, ledger recording, and version commits (§9.4), never a silent comparison-board mutation. Best-of-N coding (parallel attempts at one task, the best selected), arena-style comparison, and reviewer-and-implementer splits are run structures over this model. The surface owns the comparison and selection presentation; the child-run lifecycle, isolation, and merge contracts are File 04's.

### 13.4 Boundary

This section owns the coder multi-agent presentation and the sub-agent declaration. File 04 owns the child-run model, isolation selection, parallelism, and merge; File 24 owns the worktree; File 23 confines the worktree directory. The surface introduces no parallel scheduler.

## 14. Context, Model, Execution, Sandbox, and Workspace Policy

Anchor: `coder.policy-declaration`

### 14.1 Definition

The Coder surface declares its default context, compaction, model, execution, budget, sandbox, and workspace policies by reference (`worksurface.context-model-declaration` (File 25 §8), `worksurface.runtime-execution-declaration` (File 25 §9)). It names which policies it defaults to; the policy mechanics stay with their owning files, and every default is overridable through the settings cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2).

### 14.2 Default Context and Compaction Policy

The Coder surface declares a default code-aware `ContextPolicy` and `CompactionPolicy` from the canonical families (`context.context-policies`, File 13 §4, `context.compaction` (File 13 §12)): the context policy assembles codebase context (§7.6) as `RetrievedContext`, prefers retrieval and source excerpts over raw history for large codebases, and protects the current input, active file, and selection; the compaction policy preserves the evidence and validation chains of accepted code artifacts (`artifact.evidence` (File 09 §11.5), `context.continuity-summaries` (File 13 §14)) and redirects oversized build, test, trace, and terminal output to referenced sources with selected ranges where needed. Every model request assembles through the one `ContextAssemblyService`; the surface creates no private model-request path.

### 14.3 Default Model Profile

The Coder surface declares a default code-capable `ModelProfile` and per-role preferences (`model.model-profile`, File 16 §4): the profile requires provider-native callable support, prefers a large request-size window for codebase context, and prefers a reasoning-capable route for complex code work, while preferring a lower-cost route for planning, search, and routine edits. Per-role preferences distinguish the responder, planner, critic, validator, and child-run roles. The surface implements no private model-selection logic; selection stays the Model Strategy layer's, and the user may override the profile per scope.

### 14.4 Default Sandbox Profiles

The Coder surface declares its default `SandboxProfile`s (`sandbox.contract`, File 23 §3): a code-execution profile confining tests, builds, scripts, debugger sessions, traces, and terminal sessions to the operating-system-confined isolation tier, the workspace filesystem region, no network by default (widened only by explicit opt-in through policy), and an environment allowlist; and a preview profile confining a previewed application to the workspace filesystem, no network by default, a bounded memory and process budget, and a finite wall-clock guard. The environment allowlist governs both direct environment variables and variables discovered from workspace environment files; values enter through `EnvPolicy` or `SecretRef` resolution, not automatic raw injection. Untrusted ingested code (§7.5) runs at the stronger isolation tier its trust class requires (`sandbox.isolation-tiers`, File 23 §4.3). The surface extends the base contract only with its language-runtime, debugger, tracing, and preview capability surface; it redefines no enforcement or kill semantics and opens no private sandbox.

### 14.5 Default Execution Preset and the Plan Capability

The Coder surface declares a default execution preset — the surface-runtime structure its coding runs start from (`run.execution-entry`, File 04 §4) — as a model-and-tool agent loop over the shared run lifecycle: read and search the codebase, propose and apply edits, run tests and checks, and fix on failure, iterating until completion, pause, or user intervention. Planning is the optional shared `plan` capability (`run.task-promotion-task-updates`, File 04 §18): the agent may call it to produce a `Plan` block — a structured, editable card of steps the user may edit, discard, or continue past — when a task's complexity warrants it. There is no planning phase, no planner-versus-executor model split, no phase state machine, and no per-surface "planning enabled" toggle; the `plan` capability is a normal block-producing tool any surface may use, and plan blocks live in the version tree (§22). The surface declares default run budgets as advisory ceilings overridable per scope, never hidden hard limits (`run.budgets-limits`, File 04 §21).

### 14.6 Instruction-File Qualifier and Contribution

The Coder surface declares its instruction-file qualifier — the `ATLAS.coder.md` variant of the `ATLAS.md` hierarchy (`workspace.instruction-files`, File 24 §9.2) — and its model-request instruction contribution: the surface's identity, the coding-environment facts, and the coder guidance, assembled by context assembly into the `InstructionSources` region with the correct authority class (`context.instruction-sources-workspace-files`, File 13 §16). The surface recognizes the workspace `ATLAS.md` and `ATLAS.coder.md` files and the common external coding-instruction file conventions as candidate instruction sources, resolved through File 24's hierarchy; filename recognition is not authority recognition. In the trusted bound workspace, accepted instruction files contribute under File 13's authority classes. In mounted, ingested, dependency, archive, or remote sources, files with familiar instruction names remain untrusted source data until explicitly accepted or policy-classified (§7.5), and authority-boundary markers render accordingly. The agent may propose additions to a coder instruction file only through the same proposal-and-approval path as any user content, committing as a sibling block (`workspace.instruction-files`, File 24 §9.2); it never edits an instruction file out of band.

### 14.7 Workspace Relationship

The Coder surface's views render over the bound `Workspace` (`workspace.conversation-binding`, File 24 §7); its files materialize through the disk↔substrate mirror and File 23's filesystem boundary (§6.6); its parallel work uses worktrees (§13.2); its instruction, command, settings, and environment state live in the workspace `.atlas/` directory (`workspace.internal-layout`, File 24 §8). The surface owns no workspace identity, disk-history store, or parallel materialization path.

### 14.8 Boundary

This section declares the coder defaults by reference. File 13 owns context and compaction; File 16 owns the model profile and selection; File 04 owns the run, the `plan` capability, and budgets; File 23 owns the sandbox; File 24 owns the workspace and instruction files; File 15 owns the settings resolution.

## 15. Views, View Presets, and the Coder Shell

Anchor: `coder.views-presets`

### 15.1 Definition

The Coder surface declares the presentation shapes it offers: the view presets a user can switch between, the default inspectors, the customization policy, and the activity-feed and shell affordances. A view preset is a named startup presentation shape; it is not an autonomy mode and does not silently change backend policy (`worksurface.views-presets`, File 25 §7).

### 15.2 View Presets

The Coder surface ships built-in view presets — representatively a minimal preset (a focused editor with conversation), a default preset (editor, terminal, file tree, conversation, and context inspector), and a worktree preset (editor, terminal, the worktree comparison board, and context inspector for multi-agent parallel sessions). A view preset declares the panel set, arrangement, and presentation-only startup state; applying it changes presentation only. View presets are presentation seeds, not autonomy controls: selecting a richer preset is progressive disclosure (the user sees more state and asks different questions), never a mode change, and switching presets mid-run never silently changes model selection, context policy, execution entry, budget, sandbox profile, or approval posture (§22). The user may save custom presets and override the default per scope (`settings.profiles`, File 15 §7).

### 15.3 The Activity Feed and Inspectors

The Coder surface presents an activity feed — the conversational execution display of the coding run — that renders the run's progress through the shared execution-presentation contracts (`run.presentation`, File 04 §25): tool calls and results (with code edits shown as diffs and command runs shown as terminal output), batched approval requests (§12.3), sub-agent activity (§13, collapsible), programmatic-execution inner calls, and the streaming file-write rendering (§6.6). The feed is a projection over the ledger and event stream, not a private log. The surface declares default inspectors (context, execution, and registry inspection) as inspector-panel projections over substrate state.

### 15.4 Customization and Morphing

The Coder surface declares a customization policy (`worksurface.views-presets`, File 25 §7.4) describing which kinds of customization it permits — panel rearrangement, custom panel registration, and widget placement — resolved by the UI customization layer; the surface owns what kinds are allowed, not the concrete placement mechanics. Surface morphing — projecting the coder panels and active view preset when the Coder surface becomes the active presentation surface — is a UI projection driven by the `SurfaceContract`, the live `SurfaceState`, and the routing decision (`worksurface.views-presets`, File 25 §7.3); it changes presentation, not the work model. Conversation is an always-available control rail and an expand/collapse view, never forced to occupy the primary pane during coding (`worksurface.activation-shell`, File 25 §11.3).

### 15.5 Boundary

This section declares the coder view presets and customization policy. The UI Shell and UI Customization specs own shell, panel, morphing, and placement rendering; File 04 owns the execution presentation the activity feed projects; File 15 owns the settings and profiles for saved presets.

## 16. Rails and Control Affordances

Anchor: `coder.rails`

### 16.1 Definition

The Coder surface declares its control affordances — the user-facing ways to invoke its capabilities — and binds them to the control rails (`controlrail.consequences-for-later-specs`, File 26 §21). It declares which capabilities bind to which default shortcuts, slash commands, and menu entries, registers surface-scoped keybinding contexts and custom commands, and introduces no private rail, invocation registry, or rail autonomy field.

### 16.2 Slash Commands and Custom Commands

The Coder surface's control affordances include slash commands resolved through the slash-command rail (`controlrail.consequences-for-later-specs`, File 26 §21), and workspace-local custom commands stored in the workspace `.atlas/commands/` directory (`workspace.internal-layout`, File 24 §8.3): each a declarative command definition resolved through the capability system — a prompt-template command that expands to model-facing instruction, or a capability-binding command that invokes a coder capability with templated arguments — never an out-of-band execution path. Custom commands carry their parameters, preview and expected-postcondition metadata where declared, and an optional shortcut, and are invocable from the command rail, the palette, and the agent through the unified invocation path.

### 16.3 Keybinding Contexts

The Coder surface registers surface-scoped keybinding contexts the keymap resolves chords against (`controlrail.consequences-for-later-specs`, File 26 §21): representatively an editor context (save, find, format, go-to-definition, rename, stage-hunk), a terminal context, a diff context (next/previous change, revert chunk), and an optional modal-editing context for users who prefer it. A keybinding binds a chord to a capability; the chord grammar, the context stack, the conflict resolution, and the resolver are the control-rail layer's. The surface declares which capabilities carry a default shortcut; user-bound shortcuts override the defaults through settings.

### 16.4 Command Palette, Quick-Open, and Mentions

The Coder surface's capabilities and custom commands surface in the command palette and the quick-open file search through the command rail's palette lens (`controlrail.consequences-for-later-specs`, File 26 §21); the palette is subsystem-neutral and searches the available-capability list. Code-aware mentions (a file, folder, symbol, problem, repository, terminal, or open-file reference) resolve through the conversation rail's pre-dispatch transformation into attributed context attachments (§7.6). The surface declares the default coder workflow commands — representatively code review, test generation, refactoring, codebase explanation, debugging assistance, and commit-message generation from staged changes — as capabilities and command definitions reachable through every rail.

### 16.5 Boundary

This section declares the coder rail bindings and control affordances. File 26 owns the rail primitive, the input-resolution contract, the keymap, the slash grammar, the palette, and the mention resolution; File 24 owns the `.atlas/commands/` store; File 05 owns the capabilities the affordances invoke. Voice and external-protocol invocation of coder capabilities are the rail layer's.

## 17. Session Logging and Export

Anchor: `coder.session-logging`

### 17.1 Definition

Coder session logging is the export view of a coding session — its history, decisions, changes, and outcomes — produced as a projection over the version graph and the execution ledger, not as a parallel live write path. It serves inspection, hand-off, and reproducibility without duplicating the substrate.

### 17.2 Export as a Projection

A coder session export is generated on demand or at task completion by walking the version range and the ledger: it produces a human-readable summary, a per-version change narrative, and a rendered activity view, materialized under the workspace `.atlas/logs/<task-id>/` projection directory (`workspace.internal-layout`, File 24 §8.3 — the logs directory is a session-export projection, not a source of truth). The tool-call, version-commit, and version-control facts the export presents already live durably in the ledger and version graph; the export references them and re-derives the view, and introduces no parallel `tool-calls`, `checkpoints`, or `git-operations` write path (§22).

### 17.3 Prompt Capture and Privacy

Capturing the full assembled model request of each step (the prompt) into the export is a privacy-sensitive operation and is off by default: an assembled coder prompt may include pasted credentials, file contents with secrets, and proprietary source. The Coder surface declares distinct settings for prompt capture and raw-prompt capture: redacted prompt capture materializes only the redacted form to disk, with redaction occurring before export files are written; raw prompt capture is a separate high-risk setting requiring explicit user authorization and workspace policy allowance. Sensitive workspaces may force prompt capture off, and an inline indicator is shown while any prompt capture is active. No unredacted secret is written to an exported or synced log (`secret.backend-boundary`, File 22 §4); a session export passes through egress governance and sensitivity filtering on any share or export (`portability.consequences`, File 21 §18, `security.egress-governance` (File 22 §11)).

### 17.4 Boundary

This section owns the coder session-export projection and its privacy posture. File 11 owns the version graph the export walks; File 10 owns the ledger; File 24 owns the `.atlas/logs/` projection directory; File 22 owns the secret boundary; File 21 owns the egress-governed export.

## 18. Cross-Surface Composition

Anchor: `coder.cross-surface`

### 18.1 Definition

Cross-surface composition is how the Coder surface composes with other surfaces: the coder execution capabilities other surfaces borrow, the code content that composes into other surfaces' outputs, and the capabilities the Coder surface borrows in place.

### 18.2 The Coder Execution Surface as a Borrowable Capability

The Coder surface exposes its confined code-execution capability — running code with test cases and reporting structured results — as a registry capability other surfaces borrow (`worksurface.actions-declaration`, File 25 §6.3, `surface.subsystem-surface-spec` (File 07 §5.5)). The Teacher surface, for example, borrows the coder execution capability to run a learner's code against test cases and report graded results; the capability runs confined under the coder sandbox profile and returns a structured outcome. The Coder surface owns the execution capability; the borrowing surface's workflow is its own.

### 18.3 Code Content Composes Across Surfaces

Code blocks, `CodePatch` artifacts, and file blocks compose into other surfaces' outputs through the one block and entity pools (`block.cross-surface-composition`, File 08 §12.3, `artifact.cross-surface-interoperability` (File 09 §17.3)): a research report composed in conversation may carry code children the Coder surface produced, rendered correctly in any surface that supports the kind and as typed placeholders elsewhere. Cross-surface composition is a property of the shared pools, not a coder-private integration.

### 18.4 Borrowing in Place

A coder run that needs a capability outside the surface — web fetch to read documentation, memory recall of a project convention, image generation for a diagram — borrows it in place and remains in the Coder surface (§5.4), with the ledger recording the cross-surface reach. A coder run reaches another surface's workflow only through a routing reroute or explicit user override (`routing.mid-execution-reroute`, File 03 §12, `worksurface.activation-shell` (File 25 §11)), not by silent surface change.

### 18.5 Boundary

This section owns the coder cross-surface composition. File 07 owns borrowing; Files 08 and 09 own the shared pools; File 03 and File 04 own reroute. The borrowing surfaces own their own workflows.

## 19. World-Model, Perception, and Observation Integration

Anchor: `coder.world-perception`

### 19.1 Definition

The Coder surface integrates with the world model and perception by self-registering its panels and state, contributing the world entities the agent reasons over, exposing the sensors it consumes, and producing the observations its runs depend on — all through the canonical contracts (`worksurface.world-perception-integration`, File 25 §15).

### 19.2 Self-Registration and World Entities

The Coder surface self-registers its panels, focus, and selection to the one world model on mount, focus, and content change, and unregisters on unmount (`world.observation-state-update`, File 18 §8.1); a panel it fails to register is a blind spot. It contributes the world entities its work produces — `File` (path, content hash, modification time, dirty flag, and version-control status), `EditorDocument` (the open buffer with caret, selections, and viewport, distinct from the on-disk file), `Terminal` (working directory, running command, sandbox/process binding, buffer identity, and stop affordance), `Process`, `Sandbox`, and `Workspace` (root, profile binding, dirty and branch facts) — related by the canonical relations (`world.world-entity`, File 18 §4). These are mostly the canonical entity kinds; coder-specialized entities register as `Custom` kinds through the proposal-first mechanism. The surface maintains no private state store and is never screen-scraped to learn its own state (`world.explicit-rejections`, File 18 §16). Absolute host paths are device-local sensitive data: context-assembly and plugin views receive workspace-relative paths and aliases unless policy and consumer authorization allow more (§20).

### 19.3 Sensors and Observations

The Coder surface declares the sensors it exposes — filesystem, repository, terminal, process, debugger, trace, and environment — and consumes their structured output (`perception.consequences-for-later-specs`, File 19 §19); perception owns the capture mechanics, and the surface owns no private capture pipeline (`perception.explicit-rejections`, File 19 §18). It is structured-data-first: it navigates code through file content, symbols, repository state, process state, debugger state, and selected output ranges, not through screenshots. It produces `RepositoryState`, `TerminalOutput`, `FileSnapshot`, `ProcessState`, `EnvironmentSnapshot`, and `WorkspaceSnapshot` observations through the canonical `observation.commit` path (§5.3) where a capability run depends on them for revalidation or replay. Terminal and build output buffers remain transient by default; selected ranges become durable only when committed as attributed observations or source excerpts.

### 19.4 Availability

The Coder surface's available-action list is the available-capability list the world model's availability evaluator computes for the surface's scope (`world.state-aware-capability-availability`, File 18 §9), filtered by the active surface state; the surface registers the named availability checks of §5.5 and maintains no private available-action store.

### 19.5 Boundary

This section owns the coder world-model and perception integration. File 18 owns the entity catalogue, self-registration, durability tiers, and availability evaluator; File 19 owns the sensors and capture; File 09 owns the observation blocks; File 23 owns the process and sandbox snapshots.

## 20. Persistence, Locality, and Portability

Anchor: `coder.persistence-locality`

### 20.1 Definition

The Coder surface's durable state persists as substrate families through the one storage contract, splits by locality the way a workspace's does, and moves cross-installation through the canonical portability mechanisms. The surface introduces no private durable store.

### 20.2 What Persists and Where

The surface's durable state — its registered `SurfaceContract` versions, its registered `Custom` kinds, its scoped enable state and settings, and the blocks, artifacts, versions, codebase source records, committed extraction records, index projection metadata, and observations its work produces — persists as substrate families and content-addressed blobs through the storage contract (`storage.durable-substrate`, File 20 §3, `storage.consequences` (File 20 §18)); code file content resolves from the content-addressed blob store (`storage.blob-store`, File 20 §6). The surface's live state — active panels, focus, selection, the materialized presentation, terminal buffers, debugger attachments, process handles, and sandbox handles — is computed and rebuilt from self-registration and the version-graph projection, never a durable fact (`worksurface.persistence-locality`, File 25 §16.1); its loss is a rebuild, never data loss. Physical index rows, embedding shards, search caches, and denormalized lookup tables are rebuildable projections over the durable blocks, extraction records, and observations (`retrieval.indexing-pipeline`, File 12 §12.3).

### 20.3 Locality

The Coder surface's identity splits by locality the way a workspace's does (`worksurface.persistence-locality`, File 25 §16.2, `workspace.locality` (File 24 §4)): the surface's logical declaration and the workspace's logical identity sync, while device-bound runtime state — open panels, terminal buffers, process and sandbox handles, worktree directories, and absolute host paths — is device-local and rebuilds per device and never syncs. World facts the surface produces (open files, running processes, sandboxes) are device-local by default (`portability.what-replicates`, File 21 §5).

### 20.4 Portability

The surface's durable state rides the syncable substrate and the `PortablePackage` for cross-device and cross-installation movement (`portability.consequences`, File 21 §18); a coder workspace exports losslessly through File 24's workspace export over the `PortablePackage`, with the disk mirror and code index rebuilt on receive rather than transported. The surface may declare a lossy convenience export (a plain archive of the materialized tree), but it passes through egress governance, audit recording, and sensitivity filtering and uses no private export path. The surface persists no unredacted secret in any materialized, exported, or synced state, and exposes no absolute host directory layout to the model by default (`secret.backend-boundary`, File 22 §4, `workspace.atomic-write` (File 24 §13.2)). Every hash the surface relies on is computed over a declared `CanonicalEncoding`, never physical bytes (`core.canonical-hash`, File 01 §7.14); the surface defines no new canonical hash.

### 20.5 Boundary

This section declares the coder persistence and locality classification. File 20 owns the storage substrate, the blob store, and rebuild orchestration; File 21 owns replication and the package; File 22 owns the secret and egress boundaries; File 24 owns the workspace locality split; File 11 and File 12 own the version-graph and index projections.

## 21. Capability, Event, and Settings Surface

Anchor: `coder.capability-event-settings`

### 21.1 Capabilities

The Coder surface contributes its capabilities to the one Capability Registry as `Subsystem`-sourced built-ins or coder adapters over neutral capabilities (`capability.declaration` (File 05 §3), `capability.adapter-capabilities` (File 05 §17.4)), tier-gated by policy (File 06), surfaced through tool-surface composition (File 07), and invoked through the shared pipeline (`run.call-pipeline`, File 04 §8.2). The capability families are enumerated in §5.2. Each capability declares its touched resources, permission tier and floor, reversibility, concurrency, replay class, validation path, and produced block and observation kinds; the surface introduces no parallel capability registry and no out-of-band action path, and every coder capability is the single source for all its invocation paths (`core.extension-planes`, File 01 §6.14).

### 21.2 Events

The Coder surface emits its events through the one event bus and ledger with the canonical envelope (`ledger.event-stream`, File 10 §5). Surface-lifecycle and tool-surface events are owned by Files 25, 07, and 18 and flow through their vocabularies; workspace, version, validation, artifact, and version-control events are owned by Files 24, 11, 09, and the `git.*` capabilities and flow through theirs. Coder-specific facts that no canonical or owning-file vocabulary already defines register as `Custom { namespace: "coder", name, payload }` extensions (`ledger.custom-kind-registration`, File 10 §4.3) — representatively the file-revert operation (`coder.file_reverted`), the streaming file-write signal (`coder.file_partial_write`), the code-index lifecycle, the validation-run lifecycle, and the review lifecycle — each declaring its payload schema, cross-reference keys, default sensitivity, and retention. The surface opens no side-channel store or notification path.

### 21.3 Settings

The Coder surface's behavior is configurable through the one settings system (`core.settings-system`, File 01 §6.8, File 15) as namespaced keys under `surface.coder.*`, resolved through the standard cascade and composed with the per-substrate settings the owning files own (the sandbox settings of File 23, the workspace and instruction-file settings of File 24, the context and compaction settings of File 13, the model settings of File 16, the policy and git-safety settings of File 06, the retrieval settings of File 12, the perception settings of File 19). The surface is not a durable settings scope (`settings.scopes-profile-contexts-overlays`, File 15 §5.1); per-surface variation is namespaced keys plus profile layers. Settings whose values are security-sensitive (the prompt-capture setting, the sandbox-profile overrides, the protected-branch list) declare conservative agent exposure (`policy.agent-exposure-policy-settings`, File 06 §16.4); no coder behavior with meaningful variation is a hardcoded constant (`settings.settings-over-constants`, File 15 §13).

### 21.4 Boundary

This section names the coder capability, event, and settings surface. File 05 owns the capability contract; File 06 owns policy; File 10 owns the event bus and custom-kind registration; File 15 owns the settings model and cascade; the owning substrate files own the per-substrate settings the surface composes with.

## 22. Explicit Rejections

Anchor: `coder.explicit-rejections`

The following are architecturally invalid for the Coder surface and for any later spec that extends it:

- **A code change stored only as transcript prose** — a coder code change is an `Artifact` revision carrying validation, review, and provenance state; storing artifact-grade code only as an assistant message is message inflation (`artifact.consequences-for-later-specs`, File 09 §22, `codex_recommendations.md` §2.3) and is rejected (§6.2).
- **A separate file-history, checkpoint, or snapshot store** — no `file_checkpoints` table, no `.atlas/checkpoints/` shadow directory, no per-file snapshot, no per-tool-call version, and no checkpoint primitive parallel to the version graph; coder file history, undo, and revert are projections over the one version graph, and the disk tree is its materialized view (§8; `version.explicit-rejections`, File 11 §23, `workspace.explicit-rejections` (File 24 §23)).
- **A private workspace identity, disk-history store, or materialization path** — the Coder surface renders over a bound `Workspace`, materializes through the disk↔substrate mirror and File 23's filesystem boundary, and owns no workspace identity or parallel disk-history store (§14.7; `workspace.explicit-rejections`, File 24 §23).
- **A private sandbox, process spawner, terminal mechanism, or kill path** — all coder confined execution runs through the one `Sandbox` contract and the `ManagedProcess`/`ProcessGroup` model; the surface extends the base contract only with its language-runtime and preview capability surface and redefines no enforcement or kill semantics (§10, §14.4; `sandbox.explicit-rejections`, File 23 §20).
- **A private version-control mechanism, store, or path** — version control is the domain-neutral `git.*` capability family; the Coder surface adds the UI projection and references the git-safety rules, and owns no private git store or path (§9; `policy.built-in-reusable-policy-rules`, File 06 §11.5).
- **A private code-index, symbol, or graph store** — codebase extraction commits through the canonical indexing pipeline into the workspace-qualified namespace; the surface owns extraction semantics, not a parallel retrieval substrate (§7; `retrieval.explicit-rejections`, File 12 §21).
- **A private model-request assembly path or private model-selection logic** — every coder model request assembles through the one `ContextAssemblyService`, and the surface declares a default `ModelProfile` without implementing selection (§14.2, §14.3; `context.consequences-for-later-specs` (File 13 §22), `model.consequences-for-later-specs` (File 16 §16)).
- **A coder autonomy, participation, interaction-shape, persona, or phase field** — at any layer, in any form; coder autonomy is capability permission tiers, leases, and approval posture plus user direction, progressive disclosure is which panels and view preset are open, and the `plan` capability is a tool, not a phase machine (§14.5, §15.2; `worksurface.no-autonomy-field`, File 25 §13). There is no planner-versus-executor model split, no two-phase execution machinery, no "planning phase enabled" toggle, and no `Drive`/`Supervise`/`Collaborate`/`Delegate` dial.
- **A parallel session-logging write path** — coder session logging is an export projection over the version graph and ledger; the prior `tool-calls`, `checkpoints`, and `git-operations` live logs that duplicate the substrate are deleted, and prompt capture defaults off for privacy (§17; `unit08-coder.md` D8.4).
- **A view preset that silently changes backend policy** — applying a coder layout preset changes presentation only and never silently changes model selection, context policy, execution entry, budget, sandbox profile, or approval posture (§15.2; `worksurface.views-presets`, File 25 §7.2).
- **A private code-execution surface borrowed without the shared capability and sandbox contracts** — the coder execution capability other surfaces borrow runs confined under the coder sandbox profile and is reached through the one registry and tool-surface contract, never a private cross-surface integration (§18.2).
- **A command-name blocklist as the shell-safety boundary, automatic environment-file injection, or a coder-private approval flow** — shell safety comes from the permission tier, machine-readable command inspection, `EnvPolicy`, touched-resource/previews/postconditions where available, and the dedicated-tool-preference and git-safety rules; coder approvals flow through the one policy layer and the shared batched-approval flow (§5.5, §10, §12.3; `sandbox.explicit-rejections`, File 23 §20, `policy.consequences-for-later-specs` (File 06 §18)).
- **Exposing the host's absolute directory layout to the model by default, or materializing an unredacted secret** — absolute host paths are device-local sensitive data and model-facing content uses workspace-relative paths and aliases; no unredacted secret is written to a materialized, exported, or synced file (§19.2, §20.4; `secret.backend-boundary`, File 22 §4).
- **A `git push` lifted by a global trust toggle, or a force-push to a protected branch without typed confirmation** — `git.push` is held behind approval unconditionally and is not lifted by `agent.unrestricted_mode`, and a force-push to a protected branch carries the `Denied`-floor typed-confirmation rule (§9.3; `policy.built-in-reusable-policy-rules`, File 06 §11.5).
- **Naming a specific editor engine, terminal renderer, content-search engine, version-control library, or language-structure parser as the canonical semantics** — these are replaceable implementations behind the surface's panels and capabilities; the canonical contract is the behavior, never the library.
- **Time-based or polling coder behavior as a correctness condition** — codebase indexing, repository status, and file-change capture are event-first with flagged polling fallback only where a source emits no change events; the only permitted timer is the finite, configurable, killable wall-clock safety guard (`sandbox.resource-limits`, File 23 §9.3 — decisive only without a completion signal, otherwise a last-resort backstop) (§7.3, §9.2, §10.3; `world.explicit-rejections`, File 18 §16, `sandbox.explicit-rejections` (File 23 §20)).

## 23. Consequences for Later Specs

Anchor: `coder.consequences-for-later-specs`

Later specs must follow these rules:

- The other **per-surface specs** (Web, Data Processor, Teacher, GUI Control, System Agent) declare their own `SurfaceContract`s to File 25's shape, the same way this file does for Coder; they may borrow the coder execution capability (§18.2) but introduce no private coder mechanism. The Coder surface borrows their capabilities in place, never by silent surface change.
- The **Automation and Triggers** spec may drive coder workflows non-interactively (a scheduled test run, a watch-triggered build, a commit-triggered review) through the coder capabilities and the shared trigger-and-routing contract, confined to the narrowest coder sandbox profile, and pinning the coder surface and its policies at save time the way routing does; it introduces no parallel coder execution path.
- The **Workflows, Templates, and Reuse** spec treats the coder default workflows (§16.4) and custom commands (§16.2) as reusable workflow and command definitions, and treats a successful coding run as a promotable workflow; coder workflow outputs that warrant durable identity become artifact versions through the canonical mechanism.
- The **Extension and Plugin System** and **MCP and External Integrations** specs may contribute coder capabilities, custom commands, instruction-file conventions, language-intelligence backends, ingestion sources, and hosted-forge connectors (pull-request review and merge, §9.5) through the proposal-first registration and source-approval path; a plugin-contributed coder capability participates in the one registry, policy layer, sandbox, and ledger exactly as a built-in does.
- The **UI Shell, Layout, Presentation, and Interaction Models** and **UI Customization, Widgets, and Theming** specs render the coder panels, activity feed, diff and comparison views, history panel, command palette, keybinding editor, and view presets over the data and behavior contracts this file fixes; presentation may vary freely, the work model cannot. The concrete editor engine, terminal renderer, and search engine are their implementation choices behind the panels.
- The **Quality Control and Validation** spec registers coder validators (test, build, lint, type-check, format-check, runtime/debugger/trace checks, and review checks) producing `Validation`/`Critique`/`Observation` blocks and integrating through the completion-verification hook surface and the event and capability hooks, not a separate pipeline; it consumes the coder validation-state derivation (§11). Formatter modes that mutate files consume the coder edit pipeline rather than validation-only semantics.
- The **Telemetry, Logging, and Observability** spec consumes the coder events and the per-call attribution this file and File 10 emit; it renders the coder session inspector from the version graph, ledger, and observation handles, never by re-walking the disk or re-spawning a process for a historical view.
- The **Runtime Infrastructure and Lifecycle** spec orchestrates coder surface, sandbox, terminal, and index startup and reconstruction around the storage lifecycle File 20 owns, reaping orphaned coder processes, sandboxes, and worktrees at restart and rebuilding the code index as a projection; it reimplements no coder execution, materialization, or indexing.
- The **Evaluation and Benchmarking** spec verifies the coder round-trips — edit-to-artifact-revision-to-materialization-to-external-edit-to-version, code-search retrieval, the test-and-validation gate, the revert-as-version-switch, the worktree-backed multi-agent merge, and the session-export projection — replaying over recorded snapshots and immutable references, not live disk or process state.
- The **Packaging, Platform, and Distribution** spec ships the built-in declarations for the canonical coder capabilities, the coder `SurfaceContract`, the coder `Custom` event and observation kinds, and the default coder settings as the `Builtin` source in every install, and packages the editor, terminal, search, and version-control implementations behind their contracts.

## 24. Canonical Rule Anchors

Anchor: `coder.canonical-rule-anchors`

Load-bearing rules defined by this file carry stable anchors: `coder.chosen-model`, `coder.boundaries`, `coder.surface-contract`, `coder.state-declaration`, `coder.actions-declaration`, `coder.code-editing`, `coder.codebase-context`, `coder.file-history`, `coder.version-control`, `coder.terminal-execution`, `coder.validation`, `coder.review`, `coder.multi-agent`, `coder.policy-declaration`, `coder.views-presets`, `coder.rails`, `coder.session-logging`, `coder.cross-surface`, `coder.world-perception`, `coder.persistence-locality`, and `coder.capability-event-settings`. Cross-references should prefer the anchor and may cite the section number secondarily. An anchor names exactly one canonical rule and is stable across spec revisions.
