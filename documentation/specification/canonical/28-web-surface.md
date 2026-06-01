# Web Surface

## Status

Canonical. This file defines the `Web` work surface — the specialized environment for browsing, web research, content extraction, browser automation, and page monitoring. It is the second per-surface specification: it fills the `SurfaceContract` that `worksurface.surface-contract` (File 25 §4) delegates to each per-surface spec, and declares the web-specific workflows, panels, capabilities, and policies the Web surface contributes over the shared substrate. It owns user-facing web workflows and specialized views; it owns no private architecture. It composes blocks, capabilities, execution, the world model, perception, the version graph, workspaces, the sandbox, retrieval, context, artifacts, security, providers, and every other substrate through the same contracts every surface uses. Later canonical files may refine it, but may not contradict it.

## Scope

This file defines:

- the `Web` `WorkSurface` and its `SurfaceContract` (`worksurface.work-surface`, File 25 §3, `worksurface.surface-contract` (File 25 §4)): identity, declared panels and selection kinds, the `SubsystemSurfaceSpec` and contributed capabilities, view presets and inspectors, and default context, model, execution, sandbox, and workspace policies
- the **persistent-web-layer reframe**: the Web surface is one substrate in which search, browsing, extraction, citation, automation, and page monitoring share state — gathered web content is a durable, citable, validatable `Observation`, `Artifact`, or `Claim` with `Evidence` and `Citation`, not transient transcript prose, and a browser session is a `WorldEntity` over a `Sandbox`-confined `ManagedProcess`, observed through `Perception`, not a private state model
- the fetch-search-extract contract: `web.search`, `web.fetch`, `web.search_academic`, and `web.extract_document` as capabilities whose tiered fetch, content-extraction, and search-backend strategies are replaceable implementations behind the capability, producing durable source blocks with freshness fingerprints over the shared retrieval, blob, and citation substrates
- browser sessions, pages, and automation: the `BrowserSession` and `BrowserPage` world entities, the `Managed`-versus-`External` backend behind a replaceable contract, the low-level browser command family and the high-level act/observe/extract layer, and the multi-action safety discipline
- page state and observation: the structured-data-first tiered sensing of a web page (the structured accessibility-and-document representation before grounded element detection before a raw screenshot) realized through `Perception`'s `BrowserPage` sensor and `BrowserDom`/`NetworkResponseSnapshot`/`Screenshot` `Observation` blocks, with DOM fingerprints and staleness revalidation
- web research and the research session: the research-depth strategies (quick, standard, deep), the deep-research workflow as a child-run structure over shared execution, and the research session as a view over the version tree rather than a parallel store
- evidence, citation, and source trust: web research producing `Claim` blocks with `Evidence` links and `Citation`s, source credibility and trust metadata, citation-grounded synthesis, and the research-canvas projection
- web artifacts, downloads, and macros: the `BrowserExtract`, `WebDocument`, `Report`, and `Document` artifact kinds, downloads materialized as file artifacts, captured pages, screenshot series, and replayable action macros
- page and site monitoring and reactive session health: change monitors as `Trigger`-rail entries over perception change-detection and version-graph diffing, and the web-specific reactive monitoring behaviors mapped to their canonical owners (perception sensors, event-bus hooks, stuck/loop detection, sandbox resource limits, egress policy, and the elicitation handoff) rather than a private watchdog subsystem
- the web rails: slash and custom commands, the browser and researcher keybinding contexts, the palette and quick-open, URL and page mentions, the change-monitor trigger, and voice — bound to capabilities through the control-rail layer (File 26)
- untrusted web content and injection defense, credentials and authentication and egress governance, cross-surface composition, the web world-model and perception integration, and the web capability, event, and settings surface

This file does not define:

- the `WorkSurface` primitive, the `SurfaceContract` field set, the `SurfaceRegistry`, the `SubsystemSurfaceSpec` reference, the `PanelKind`/`ViewPreset` model, the no-private-architecture invariant, or the deletion of autonomy fields — File 25 owns those; this file fills the contract
- the `Sandbox` contract, `SandboxProfile`, `ManagedProcess`, `ProcessGroup`, `NetworkPolicy`, `FilesystemPolicy`, `ResourceLimits`, killability, or the per-hop redirect re-validation enforcement — File 23 owns those; this file declares the browser profiles and runs confined browsing through them
- the `Perception` sensor pipeline, the `SensingTier` strategy, the capture pipeline, sensor capture mechanics, or capture privacy/consent — File 19 owns those; this file declares which sensors it exposes and consumes their structured output
- the `WorldModel`, the `WorldEntity` catalogue (`BrowserSession`, `BrowserPage`, `Connection`), the durability tiers, the availability evaluator, or snapshot resolution — File 18 owns those; this file self-registers its panels and contributes the world entities its work produces
- the `Block`, `Artifact` (`BrowserExtract`/`WebDocument`/`Report`), `Claim`, `Evidence`, `Citation`, `Observation` (`BrowserDom`/`NetworkResponseSnapshot`/`Screenshot`), `SourceSpan`, `StalenessFingerprint`, or `EvidenceRelation` model — Files 08 and 09 own those; this file declares which kinds the surface primarily produces and the web workflows over them
- the retrieval index, the `web_cache` namespace, chunking, embedding, hybrid search, ranking, or knowledge-base mechanics — File 12 owns those; this file owns web-extraction semantics and consumes the shared retrieval contract
- the version graph, `ContextVersion`, sibling-block versioning, branching, the materialized view, or snapshot resolution — File 11 owns those; this file projects research and page history over them
- context assembly, the `ContextPolicy`/`CompactionPolicy` families, token budgets, the `untrusted_source_data` authority class, or model-request rendering — File 13 owns those; this file names the surface defaults
- model selection, `ModelProfile`, the vision-model route, or fallback — File 16 owns those; this file names the surface's default profile and role preferences
- the `SecretVault`, credential lifecycle, the trust model, encryption, the egress-tier policy semantics, the untrusted-content structural rule, or the injection classifier — File 22 owns those; this file consumes them for web credentials, untrusted page content, and egress
- the run lifecycle, the capability-call pipeline, child-run isolation, programmatic execution, the `plan` capability, budgets, cancellation, the approval flow, leases, permission tiers, the tool-surface composition, the control-rail mechanics, the `Trigger` rail and automation, or MCP transport — Files 03–07 and 26 own the written contracts, and future Automation and External Integration specs own their deeper mechanics; this file declares the web contributions and references the rules
- the storage substrate, sync, the provider/HTTP transport, the ledger row format, or UI rendering (browser-viewport chrome, canvas layout, source-card geometry, the browser engine, the search backend, the content extractor) — Files 20, 21, 17, 10 and the UI specs and infrastructure own those; this file specifies only the data and behavior contracts they consume
- the other per-surface specs (Coder, Data Processor, Teacher, GUI Control, System Agent) — those declare their own `SurfaceContract`s; this file borrows the GUI Control desktop-automation surface only by reference and never re-owns it

## Source Resolution

Families reviewed: the authoritative web unit spec (`unit09-web.md` with the D9.1–D9.15 decisions); the specbase web source family (`domains/web/{README, 00-overview, 01-browser-session, 02-browser-commands, 03-researcher-mode, 04-ui-and-modes, 05-advanced-features}.md`); the planned web pipeline (`atlas3-core/atlas3_planned_web_pipeline.md`, the 5-stage tiered-fetch technical reference) and the web inventory (`atlas3-core/TODO.md` §8); the cross-cutting web tool and RAG references (`tools/web-search-and-rag.md`, `tools/README.md`, `infrastructure/screen-share.md`, `infrastructure/external-apis.md`, `infrastructure/stack.md`, `infrastructure/database.md`); the cross-unit decisions touching web (`unit04-routing-agents-prompt.md` borrow/spawn, `unit06-tools.md` `web.fetch`, `unit11-cross-tool-learning.md` CT.1/CT.4/CT.5/CT.8/CT.16/CT.21, `unit13-ui.md` web panels and presets, `unit14-systems.md` `fetch_fallback_ban`/`atlas-research`, `unit15-ux-distribution-files-glossary.md` `BrowserBackend`/`KnowledgeGraphCanvas`/`CaptchaChallenge`/`CredentialInput`/sidecars); the strategic target-state review (`codex_recommendations.md` §8.3, §1.x, §10.1, plus the `browser_session`/`browser_page`/`browser_element` entity kinds, the `browser_extract` artifact kind, the browser-surface lease scope, and the web/page-cache retrieval index it names); and the browser-automation, research, and extraction ecosystems for cross-tool design-space corroboration (`browser-use`(+addendum), `stagehand`, `nanobrowser`, `agent-browser`, `dev-browser`, `operator-use`, `tlbrowse`, `cua`, `ui-tars`, `bytebot`, `windows-use`, `space-agent`, `llm-scraper`, `vane`, `storm`, `deer-flow`, `deepagents`, `cosight`, `deeptutor`, `autoresearch`(research-agent loops), `suna`, `openmanus`, `agentic-seek`, `open-webui`, `chatgpt_tool`, `claude_code_tool`, `claude_cowork_tool`, `claude_tool`, `gemini-cli`, `hermes-agent`, `graphify`, `ml-intern`, `ai-scientist-v2`, and others).

Resolution rule: this file realizes the Web surface by filling File 25's `SurfaceContract` and declaring web-specific workflows; it re-owns no substrate. Every substrate's semantics stay with its owning file. Where the source material describes a web mechanism the canon has already settled horizontally (page observation, browser sandboxing, the world-entity model, the version graph, artifacts and evidence, retrieval, the secret vault, the trust and egress model, the trigger rail), this file consumes the settled contract and adds only the web-specific presentation and workflow. The implementation groundings the sources lock — a browser engine and its `Managed`/`External` backends, a metasearch backend, challenge-detection and handoff implementations, fetchers, reader-mode and document extractors, a content-cache library, a secret backend, and a graph-canvas renderer — are named in the sources for grounding but are kept out of the canonical body as replaceable implementations behind their contracts, per the project rule against provider- and library-specific detail in canonical specs.

Resolved tensions:

- **Search-and-control split versus one persistent web layer.** The specbase splits the Web surface into a passive researcher mode and an active controller mode as separate execution paths; the target-state sources resolve toward one persistent web layer where search, browsing, extraction, citation, automation, and page memory share state. This file adopts the unified layer (§1, §6–§11): search, fetch, browse, extract, cite, monitor, and synthesize all compose one substrate; researcher and controller are view presets (§14), not separate architectures or autonomy modes.
- **Web content as transcript prose versus durable evidentiary records.** The simplest framing returns a fetched page as text in the transcript. File 09's artifact, evidence, and citation model makes gathered web content durable: a captured page is an `Observation` with a `StalenessFingerprint`, a structured extract is a `BrowserExtract`/`WebDocument` `Artifact`, a research finding is a `Claim` with `Evidence` and a `Citation`, and a source's trust is `Evidence` confidence and source credibility (§6, §8, §10). Artifact- and evidence-grade web content is never stored only as an assistant message (§22).
- **Page state: screenshot-primary versus structured-first.** The specbase communicates page state to the model via screenshots; `unit09-web.md` D9.4 and the browser-automation corpus (stagehand, browser-use, agent-browser, llm-scraper) consistently use a hybrid accessibility-and-document representation as the primary input, with the screenshot as a fallback for vision models. This is exactly `perception.tiered-sensing` (File 19 §5)'s structured-data-first invariant. This file resolves toward structured-first (§8): the page's structured representation is the `Structured` tier, element detection and optical-character recognition over a screenshot is the `Grounded` tier, and the screenshot itself is the `Raw` tier — realized through `Perception`'s `BrowserPage` sensor, not a private state model.
- **Reactive monitoring: a private watchdog subsystem versus mapping to canonical owners.** `unit09-web.md` D9.5 proposes a 15-watchdog reactive monitoring subsystem (health, navigation timeout, captcha, popups, downloads, security, storage, DOM, network, crash, resource, loop, auth-expiry, console, print). Each of those behaviors already has a canonical owner: event-first observation and change detection is `Perception` (File 19); the event bus and non-blocking observers are `ledger.hook` (File 10 §7); loop and stagnation detection is `run.stuck-detection` (File 04 §20.3) and `perception.output-contract` (File 19 §9.6); resource thresholds are `sandbox.resource-limits` (File 23 §9); the navigation/URL allowlist and per-hop redirect re-validation are `security.egress-governance` (File 22 §11) and `sandbox.network-enforcement` (File 23 §8); credential-needed and captcha handoffs are the elicitation rail (File 26 §13) under `perception.capture-privacy` (File 19 §10) and `policy.approval-ui-surface-contract` (File 06 §13); storage/download persistence is the version graph and workspace materialization. This file resolves toward mapping each monitoring behavior to its canonical owner (§12): the Web surface declares the web-specific monitoring behaviors and the entities and sensors they observe, and introduces no private watchdog subsystem, no private event bus, and no private monitoring store.
- **Research session: parallel tables versus a version-tree view.** `unit09-web.md` D9.14 deletes the parallel `research_sessions`/`search_results`/`fetched_pages` table family — exactly as `unit08-coder.md` D8.4 deleted the parallel session-log write paths — in favor of "a research session is a view over the version tree." This file adopts the version-tree-view model (§9.4), consistent with `version.chosen-model` (File 11 §1) and `version.explicit-rejections` (File 11 §23): search results, fetched content, and synthesized findings are blocks; a research session is the query over the blocks tagged with its session identity, never a private store.
- **Credentials and cookies: plaintext or app-encrypted storage versus the secret vault.** The specbase stores cookies, local storage, and session tokens in plaintext (or app-encrypted) SQLite; `unit09-web.md` D9.9 flags this as the same hazard as the coder session-log concern and moves the values to the OS keychain. `security.secret-vault` (File 22 §5) is the canonical owner — the `SecretVault` with OS-keyring and encrypted-file backends behind one contract. This file resolves toward the vault (§17): web credentials, cookies, and tokens are vault-held and referenced by `SecretRef`; only redaction-safe metadata persists to the durable substrate, and the sensitive-data-masking pattern is `secret.backend-boundary` (File 22 §4) plus `Secret` sensitivity (File 10 §10).
- **Modes and planning: autonomy modes and a planner/navigator phase machine versus view presets and a run structure.** The specbase carries a `Researcher`/`Controller`/`Planner` `WebMode` enum, residual `Drive`/`Supervise`/`Collaborate`/`Delegate` participation levels (`domains/web/00-overview.md`), and a periodic planner/navigator split. `worksurface.no-autonomy-field` (File 25 §13), `world.surface-state` (File 18 §5.5), and `coder.policy-declaration` (File 27 §14.5) delete the autonomy field at every layer and resolve planning to the optional `plan` capability over the shared run lifecycle. This file carries no autonomy field (§22): the researcher and controller modes are view presets (§14), autonomy is capability permission tiers, leases, and approval posture plus user direction, progressive disclosure is which panels and view preset are open, and the periodic-planning interval is a default execution-preset structure (`run.execution-entry`, File 04 §4), not a phase machine.
- **Anti-detection versus capture ethics.** `unit09-web.md` D9.8 specifies an aggressive anti-detection surface (fingerprint spoofing, mouse humanization), while `perception.capture-privacy` (File 19 §10.7) fixes a capture-ethics floor: perception "does not defeat the protections of the sources it observes — it does not bypass bot-detection challenges and treats consent-and-cookie surfaces conservatively." This file resolves toward both, with the ethics floor canonical (§16, §17): browser-fingerprint normalization and interaction pacing serve legitimate access (the user's own authenticated sessions, ordinary automation) and are per-profile-configurable; the baseline challenge response is detection plus user handoff; any challenge-assistance integration is a separately declared, disabled-by-default, policy-governed capability with explicit enablement, standing, site-posture compliance, and spending authorization; and hidden or unauthorized bypass is rejected.
- **Browser backend and fetch/search engines: name the library versus a replaceable contract.** The sources lock specific browser, search, challenge-handling, fetch, and extraction implementations. The criteria forbid library-specific detail in canonical specs (`spec_creation_criteria.md` §6) and `core.local-extensibility` (File 01 §7.10) makes implementations replaceable. This file keeps them out of the body as replaceable implementations behind the browser-session, fetch, search, and extraction capabilities (§6, §7), grounded in this Source Resolution. The `Managed` (Atlas-spawned, isolated, no user context) versus `External` (the user's own already-authenticated browser, reduced isolation) backend distinction is a per-conversation setting whose `External` choice carries a stronger approval posture (§7, §17), not a separate architecture.

## 1. Chosen Model

Anchor: `web.chosen-model`

ATLAS3 has one `Web` `WorkSurface`. It is the specialized environment for the open web — searching, browsing, navigating, extracting, citing, automating, monitoring, and synthesizing — and it is one instance of the `WorkSurface` primitive `worksurface.work-surface` (File 25 §3) defines, classified `Web` by `core.current-major-area-classification` (File 01 §5.3).

The Web surface owns user-facing web workflows and specialized web views; it owns no private architecture (`worksurface.no-private-architecture`, File 25 §12). It is declared by one `SurfaceContract` (§3) registered in the `SurfaceRegistry` (`worksurface.registry`, File 25 §10), and it composes the shared substrate — blocks, capabilities, capability policy, tool surfaces, execution, the world model, perception, the version graph, workspaces, context assembly, retrieval, memory, routing, artifacts, storage, sync, security, the sandbox, providers, and the ledger — through each one's canonical contract.

The load-bearing model of the Web surface is the **persistent-web-layer reframe**: the Web surface is one substrate in which search, browsing, extraction, citation, automation, and page monitoring share state, not a search tool sitting beside an unrelated browser-control tool. Three consequences follow:

- **Gathered web content is durable evidence, not transient prose.** A captured page is an `Observation` block (`BrowserDom`, `NetworkResponseSnapshot`, or `Screenshot`) carrying a `StalenessFingerprint` (`artifact.observation`, File 09 §13); a structured extract is a `BrowserExtract`, `WebDocument`, `Report`, or `Document` `Artifact` revision (`artifact.artifact-kind`, File 09 §4); a research finding is a `Claim` with `Evidence` links and a `Citation` carrying the source URL and span (`artifact.claim` (File 09 §9), `artifact.evidence` (File 09 §11), `artifact.citation` (File 09 §12)); a source's reliability is `Evidence` confidence and source-credibility metadata (§10). Artifact- and evidence-grade web content is never stored only as an assistant message (§22).
- **A browser is a world entity over a confined process, observed through perception.** A browser session is a `BrowserSession` `WorldEntity` (`world.world-entity`, File 18 §4.3) bound to a `Sandbox`-confined `ManagedProcess` (`sandbox.contract`, File 23 §3); each tab or page is a `BrowserPage` entity; the page's state is read through `Perception`'s `BrowserPage` sensor (`perception.sensor`, File 19 §4.3) structured-first (§8). The Web surface owns no private state model and is never screen-scraped to learn its own panels' state (`world.observation-state-update`, File 18 §8.1).
- **History and research are version-graph projections, not parallel stores.** Page-capture history, research sessions, and saved findings are projections over the one version graph and the one block pool (`version.consequences-for-later-specs`, File 11 §24); the surface introduces no parallel research, page-cache, session, or history store.

`Web` is the canonical surface name; the `surface_id` is `web` and equals the subsystem id (`capability.capability-source`, File 05 §9.1, `worksurface.work-surface` (File 25 §3.3)). Earlier vocabulary that named the same surface — "web domain", "browser mode", "researcher mode" and "controller mode" as architectures, "web layer" — is source vocabulary only and does not survive as canonical terminology or as a parallel primitive. The anchor namespace for this file is `web.*`, deliberately distinct from File 07's `surface.*` (tool surfaces), File 25's `worksurface.*`, File 26's `controlrail.*`, and File 27's `coder.*`. The capability families `web.*` and `browser.*` are capability ids in the one registry, not anchors.

### 1.1 Boundary

This file defines what the Web surface is and what it declares and contributes. It does not define how the `SurfaceContract` is registered or composed (File 25), how its tool surface composes (File 07), how its live state is held (File 18), how a page is captured (File 19), how its files materialize (File 24), how its browsing runs confined (File 23), how its history is versioned (File 11), how its credentials are stored (File 22), or how its views render (the UI specs).

## 2. Boundaries with Adjacent Layers

Anchor: `web.boundaries`

### 2.1 With File 25 (Work Surface Contract)

This file fills the `SurfaceContract` `worksurface.surface-contract` (File 25 §4) defines: identity (§3), state and panels (§4), the `SubsystemSurfaceSpec` and contributed capabilities (§5), views and presets (§14), and default context/model/execution/sandbox/workspace policies (§13). It obeys the no-private-architecture invariant (`worksurface.no-private-architecture`, File 25 §12), the static-versus-live split (`worksurface.state-declaration`, File 25 §5 — this file declares the shape, File 18 holds the values), the hint-not-fence rule (`worksurface.actions-declaration`, File 25 §6.3), and the deletion of autonomy/participation/interaction-shape fields (`worksurface.no-autonomy-field`, File 25 §13). The Web surface registers as a `Subsystem`-class source through the proposal-first path (`worksurface.registry`, File 25 §10).

### 2.2 With File 18 (World Model) and File 19 (Perception)

The boundary is sharp and load-bearing, because the Web surface's subject is the unowned external environment. File 18 owns the `BrowserSession`, `BrowserPage`, and `Connection` `WorldEntity` kinds (`world.world-entity`, File 18 §4.3), the durability tiers, the availability evaluator, and snapshot resolution; this file contributes those entities and self-registers its panels (`world.observation-state-update`, File 18 §8.1). File 19 owns the `BrowserPage`, `Screen`, and `Network` sensors (`perception.sensor`, File 19 §4.3), the `SensingTier` strategy (`perception.tiered-sensing`, File 19 §5), the capture pipeline, the stagnation signal (`perception.output-contract`, File 19 §9.6), and the capture-privacy and consent contract (`perception.capture-privacy`, File 19 §10); this file consumes the `BrowserPage` sensor's structured output and the `BrowserDom`/`NetworkResponseSnapshot`/`Screenshot` observations (§8), and never owns a private capture pipeline (`perception.explicit-rejections`, File 19 §18). The open web is the canonical externally-mutable, non-self-registering source perception captures (`perception.tiered-sensing`, File 19 §5.4).

### 2.3 With File 23 (Sandbox, Process Control, and Isolation)

The Web surface runs all browser execution through the one `Sandbox` contract (`sandbox.consequences-for-later-specs`, File 23 §21). A browser is a `ManagedProcess` in a `ProcessGroup` under a web `SandboxProfile` (`sandbox.contract`, File 23 §3), killable categorically and individually (`process.killability`, File 23 §10). The browser's outbound access is governed by the `NetworkPolicy` and the application-layer destination check and per-hop redirect re-validation (`sandbox.network-enforcement`, File 23 §8); its filesystem access (profile directory, downloads directory) is confined by the `FilesystemPolicy` and the service-trait chokepoint (`sandbox.filesystem-enforcement`, File 23 §7); its memory and process budget are `ResourceLimits` event-driven thresholds (`sandbox.resource-limits`, File 23 §9). The surface extends the base contract only with its browser-navigation and page-observation capability surface and redefines no enforcement or kill semantics.

### 2.4 With Files 08, 09, and 11 (Blocks, Artifacts, Version Graph)

Web content flows as `Block`s through the one pool (`block.cross-surface-interoperability`, File 08 §12). A captured page is an `Observation` block (`BrowserDom`/`NetworkResponseSnapshot`/`Screenshot`, `artifact.observation` (File 09 §13)) with a `StalenessFingerprint` (`DomSignature`, `EtagAndLastModified`, `ContentHash`); a structured extract or report is a `BrowserExtract`/`WebDocument`/`Report`/`Document` `Artifact` revision (`artifact.artifact-kind`, File 09 §4) with materialization, validation, and provenance (`artifact.provenance`, File 09 §15); a finding is a `Claim` with `Evidence` and a `Citation` (Url, DomSelector span, `artifact.citation` (File 09 §12)). Page-capture history and research sessions are projections over the one version graph (`version.consequences-for-later-specs`, File 11 §24); the surface introduces no parallel page-cache, research, or history store (`version.explicit-rejections`, File 11 §23).

### 2.5 With File 12 (Retrieval) and File 13 (Context Assembly)

The Web surface owns web-extraction semantics — the page-to-structured-content and search-result-to-source-record extraction (`retrieval.ingestion`, File 12 §14.2 delegates extraction to the owning surface) — and consumes File 12's shared index, query, and namespace contract: it indexes captured pages and search results into the `web_cache:<scope_id>` namespace (`retrieval.namespaces`, File 12 §3.2) and consumes the normalized `RetrievalHit`/`WebHit` envelope (`retrieval.retrieval-result`, File 12 §9), introducing no private web-index substrate (`retrieval.explicit-rejections`, File 12 §21). It assembles every model request through the one `ContextAssemblyService` (`context.chosen-model`, File 13 §1): fetched and extracted content enters the `RetrievedContext` region as `untrusted_source_data` (`context.authority-classes`, File 13 §2.3), the active page state is a `RuntimeState` part, and large pages are referenced rather than flooded into context (`context.current-input-oversize-handling`, File 13 §7). It builds no private model-request path (`context.consequences-for-later-specs`, File 13 §22).

### 2.6 With Files 05, 06, 07 (Capabilities, Policy, Tool Surfaces) and File 16 (Model Strategy)

Web capabilities are `Capability` declarations in the one registry (`capability.chosen-model`, File 05 §1) with `source: Subsystem { subsystem_id: web }`; web-specialized presentations of shared capabilities use adapter capabilities (`capability.adapter-capabilities`, File 05 §17.4). Approval flows through the one policy layer (`policy.chosen-model`, File 06 §1); the surface contributes a web approval posture and references the egress, untrusted-content, and credential rules but evaluates no policy itself. Its tool surface composes through `surface.visibility-composition-resolution-algorithm` (File 07 §9). It declares a default web-and-vision-capable `ModelProfile` and role preferences including the vision route for grounded page sensing (`model.model-profile`, File 16 §4), and implements no private model selection (`model.consequences-for-later-specs`, File 16 §16).

### 2.7 With File 22 (Security, Credentials, and Trust Boundaries)

File 22 owns the `SecretVault` (`security.secret-vault`, File 22 §5), the credential lifecycle (`security.credentials`, File 22 §6), the untrusted-content structural rule and injection defense (`security.untrusted-content`, File 22 §12), the egress-governance tiers and destination policy (`security.egress-governance`, File 22 §11), and the trust model (`security.trust-model`, File 22 §9). This file consumes all of them: web credentials and cookies are vault-held `SecretRef`s (§17), fetched and extracted web content is the canonical untrusted-content vector (§16), outbound fetches and navigations are egress-governed (§17), and source trust composes the trust model with source-credibility metadata (§10). The surface introduces no private secret store, trust authority, or egress path.

### 2.8 With File 04 (Execution), File 26 (Control Rails), and Future Automation

Web runs use the shared run lifecycle, ledger, cancellation, budgets, programmatic execution, and child-run model (`run.consequences-for-later-specs`, File 04 §29); the deep-research workflow and parallel browsing are run structures over shared semantics, never private execution. The surface's control affordances are capabilities reachable through the rails (`controlrail.consequences-for-later-specs`, File 26 §21); it registers surface-scoped keybinding contexts and custom commands and owns no private rail. A page or feed change monitor is a `Trigger`-rail entry (`controlrail.chosen-model`, File 26 §1, the `Trigger` rail kind) whose firing produces a `RunIntent` (`routing.trigger-kinds-routing`, File 03 §2.1); the deep monitoring and scheduling mechanics belong to the future Automation and Triggers spec, and this file frames the web monitor as one consumer (§12).

### 2.9 With Files 10, 15, 20, 21, 24, 17

A surface emits events through the one ledger and bus with web facts as `Custom { namespace: "web" }` (`ledger.custom-kind-registration`, File 10 §4.3); web settings are namespaced `surface.web.*` keys plus profile layers (`settings.consequences-for-later-specs`, File 15 §21); durable web state persists as substrate families with page and download blobs in the content-addressed store (`storage.consequences`, File 20 §18) and the locality split (`worksurface.persistence-locality`, File 25 §16); durable web state rides the syncable substrate and the `PortablePackage` (`portability.consequences`, File 21 §18); the surface renders over a bound `Workspace`, materializes downloads and extracts through the disk↔substrate mirror (`workspace.materialization`, File 24 §10), and uses the `ATLAS.web.md` instruction qualifier (`workspace.instruction-files`, File 24 §9); model calls reach providers only through model strategy and the provider layer (`provider.consequences-for-later-specs`, File 17 §26).

### 2.10 Boundary

This file is the Web work-surface declaration and workflow layer. It owns no substrate semantics. It feeds the substrate layers their web contributions and consumes their contracts.

## 3. The Web `SurfaceContract`

Anchor: `web.surface-contract`

### 3.1 Definition

The Web `SurfaceContract` is the one typed, source-authored declaration of the Web surface, admitted to the `SurfaceRegistry` (`worksurface.surface-contract`, File 25 §4). It carries the required `SurfaceContract` sections — Identity (§3.2), State (§4), Actions (§5), Views (§14), and Context-and-execution policy (§13) — each filled with web-specific content and declaring by reference every field whose contract lives in another file.

### 3.2 Identity

The Web surface declares:

- `surface_id`: `web`, equal to its `subsystem_id`; the value `routing.run-intent` (File 03 §4.3)'s `primary_surface` resolves to for browsing, search, and research work, the prefix of its settings namespace (`surface.web.*`) and its instruction-file qualifier (`ATLAS.web.md`)
- `surface_kind`: `Web` (`worksurface.surface-contract`, File 25 §4.4)
- `display_name`, `description`, `short_description`: localized per the canonical descriptor discipline (`capability.display-fields`, File 05 §3.2); never hardcoded into surface logic
- `keywords`: the routing- and palette-relevant terms the surface is discovered by (representative: web, browse, search, research, fetch, scrape, extract, cite, source, page, browser, monitor)
- `availability_predicate`: a world predicate (`world.state-aware-capability-availability`, File 18 §9.2) — the Web surface is activatable in any workspace; the browser-automation capabilities additionally require a registered browser backend (a named availability check per `world.state-aware-capability-availability`, File 18 §9.3), so a device without a browser backend keeps search and fetch available while the browser-control affordances report unavailable rather than the whole surface failing to activate

### 3.3 The Required-Section Map

The remaining required sections are filled as: State by §4, Actions by §5, Views by §14, Context-and-execution policy by §13. The web-specific workflow semantics (§6–§12, §16–§17) elaborate what those sections produce; they are surface workflows over the declared capabilities, not additional contract sections. The declaration is immutable for a registered `surface_contract_version`; contract updates create a new version (`worksurface.surface-contract`, File 25 §4.2). Registry state (trust, scoped enable, availability) lives on the registered entry, not the declaration.

### 3.4 Boundary

This section fixes the contract's web content at the section level. File 25 owns the contract shape and the registry; the per-section web semantics are §§4–21.

## 4. State Declaration — Panels and Selection

Anchor: `web.state-declaration`

### 4.1 Definition

The Web surface declares the panels it can mount and the selection kinds it produces. This is the static counterpart of the live `SurfaceState` (`world.surface-state`, File 18 §5): this file declares the shape, File 18 holds the live values. Panels self-register their live state to the world model on mount and update on focus, selection, and content change (`world.observation-state-update`, File 18 §8.1); a panel the surface fails to register is a blind spot the agent cannot use.

### 4.2 Declared Panel Kinds

The Web surface declares the following panel kinds, drawn from the canonical baseline (`worksurface.state-declaration`, File 25 §5.3) plus web `Custom` kinds registered through the proposal-first mechanism. Each declares the typed shape of its compact state-field summary (a url, a query, a selected source id — never the resource body, `world.surface-state` (File 18 §5.2)), the selection kinds it produces, and its control affordances:

- `browser` — the browser viewport over a `BrowserPage`; carries the active session and page id, the current url and title, navigation availability (back/forward/reload), and a `canStop` affordance; produces `Element` and `Region` selections; the browser-engine rendering is a replaceable implementation behind the panel
- `search` — the web-search view: the active query, the result set, and the academic-versus-web scope toggle; produces `File`-equivalent source selections and `Region` selections over result snippets
- `sources` — the source-management projection over the captured `Citation`, `Observation`, and source blocks of the active line of work: per-source url, title, captured-at, freshness state (fresh, cached, stale), and trust metadata; produces source selections; honors per-source include/exclude
- `reader` — the article/reader view of a fetched-and-extracted page: the clean extracted content with its source span addressable for citation; produces `Region` and `Text` selections
- `canvas` — the research canvas: a graph projection over the research session's blocks and entities (queries, sources, extracts, claims, clusters, takeaways, contradictions), a presentation of the block and entity graph, not a private store
- `report` — the research-report view of a `Report`/`WebDocument`/`BrowserExtract` artifact under construction, with per-section navigation and per-claim citation drill-down
- `activity` — the web activity feed: the run's browsing, fetching, extraction, and synthesis progress, a projection over the ledger and event stream (`run.presentation`, File 04 §25), not a private log
- `network` — a diagnostics projection over the `NetworkResponseSnapshot` observations and the session's logged requests
- `monitors` — the change-monitor list: the page and feed watches the surface has registered as `Trigger`-rail entries (§12), each with its target, its last-checked and last-changed facts, and its enable state

A panel kind a web panel declares is a shared substrate projection, not a private widget: the `browser`, `canvas`, `search`, and `reader` kinds are cross-surface roles (`worksurface.state-declaration`, File 25 §5.4), and another surface may embed a web panel without changing its primary surface (a Teacher surface embedding a `browser` panel for a source).

### 4.3 Selection Kinds

The Web surface produces selections of canonical kind `Element` (an addressed page element, by structured node reference or selector), `Region` (a screen or content region), `Text`, and `File` (a fetched source or download) (`world.surface-state`, File 18 §5.4), plus a registered `Custom` source-reference selection kind where a selection addresses a captured source by its citation identity. A selection carries a short summary and typed bounds (a node reference, a span, a url), not the selected content.

### 4.4 The Static-versus-Live Split

The declaration is the static shape; the live values — which panels are open, which is primary, what is focused and selected, the current `UiMode`, the active browser session and page, and the available-capability list — are the live `SurfaceState` File 18 holds. The Web surface declares no participation, autonomy, or interaction-shape field on its state (§22); `UiMode` (`Normal`, `CommandPalette`, `Modal`, `Fullscreen`, `Handsfree`, and the surface's registered modes) is interaction state, never an autonomy control (`world.surface-state`, File 18 §5.5). The researcher-versus-controller distinction is a view preset (§14), not a state-machine mode.

### 4.5 Boundary

This section declares the web panel and selection shape. File 18 holds the live values and owns the self-registration contract; the UI specs own panel presentation; the browser engine, the canvas renderer, and the reader extractor are replaceable implementations behind the panels.

## 5. Actions Declaration — the Web `SubsystemSurfaceSpec`

Anchor: `web.actions-declaration`

### 5.1 Definition

The Web surface's actions declaration is its `SubsystemSurfaceSpec` (`surface.subsystem-surface-spec`, File 07 §5) plus the artifact, observation, and sensor kinds it primarily produces or exposes and the approval posture it contributes. This file references the `SubsystemSurfaceSpec` contract; it owns no zone, composition, or borrowing mechanics, which are File 07's.

### 5.2 Contributed Capabilities and Zones

The Web surface contributes its capabilities to the one registry with `source: Subsystem { subsystem_id: web }`, declared per `capability.declaration` (File 05 §3) and registered through the proposal-first path (`capability.runtime-mutation`, File 05 §16.2). The capability families the surface contributes or relies on, and their default zone (`run.zones`, File 04 §10.2, `surface.zone-model` (File 07 §3)):

- **Search and fetch** (`Primary`): `web.search` (web and academic search over a replaceable search backend), `web.search_academic`, `web.fetch` (the tiered fetch-and-extract capability), and `web.extract_document` (text, structured, and markdown extraction modes) (§6); the foundation for any web research
- **Browser session lifecycle** (`Primary` when a browser backend is available): create, list, show/hide, and terminate a session; profile create/list/switch/delete (§7); session lifecycle gated by the browser-backend availability check (§3.2)
- **Browser navigation and interaction** (`Primary` when a browser backend is available): `browser.navigate`, `browser.back`, `browser.forward`, `browser.reload`, `browser.click`, `browser.click_at`, `browser.click_by_vision`, `browser.type`, `browser.fill_form`, `browser.key`, `browser.set_value`, `browser.scroll`, `browser.drag`, `browser.hover`, `browser.focus`, `browser.upload_file`, tab and frame list/switch/new/close, `browser.wait_for_selector`, `browser.wait_for_navigation`, `browser.wait_for_function`, and `browser.wait_for_load_state` (§7); the low-level browser command set
- **High-level page interaction** (`Primary` when a browser backend is available): the act, observe, and extract layer — natural-language action, candidate-action observation, and schema-driven structured extraction over the structured page representation (§7.4)
- **Page state and observation** (`Primary`): get the structured page state, the accessibility-and-document representation, the network responses, and a screenshot; print a page to a document; evaluate page script (§8); the state queries gated by the page-observation and policy rules
- **Cookie, storage, and network** (`Primary` when a browser backend is available, with elevated approval): cookie get/set/clear, storage get/set, network request listing and interception (§7, §17); arbitrary script evaluation and network interception carry an elevated tier (§5.5)
- **Research** (`Primary`): start/continue a research session, add a finding, generate an outline, write a section, and synthesize (§9); the research-workflow capabilities over the version-tree-view session
- **Evidence and citation** (`Primary`): capture a citation, capture a source excerpt, publish a claim with evidence, link evidence to a claim, and set source trust (§10), declared as web-surface presentations of the canonical `claim.*`/`evidence.*`/`citation.*` capabilities (`artifact.claim-extraction` (File 09 §10), `artifact.evidence` (File 09 §11), `artifact.citation` (File 09 §12))
- **Monitoring** (`Primary`): register, list, pause, and remove a page or feed change monitor (§12), each resolving to a `Trigger`-rail entry
- **Discovery and orchestration** (`Primary`): the shared `plan` capability (§13.5), the discovery capabilities (`tool.search`, `tool.borrow`, `mcp.search`, `surface.late-loading-runtime-discovery` (File 07 §7)), and the sub-agent-spawn capability for parallel research (§9)
- **Borrowable** capabilities: file read/create/edit/list (to save findings and downloads), memory recall and store (to pin and recall research), knowledge search (to consult the local knowledge base before the web), image generation (for research diagrams), and the coder code-execution capability (to process scraped data) — present in the `Borrowable` zone for occasional cross-surface reach
- **Forbidden-by-default** (excluded from the surface's default zones, still reachable by explicit borrow with a typed denial where policy forbids): the GUI-control desktop-automation, data-processor spreadsheet, and teacher capability families, which are out of scope for default web composition; desktop control is the GUI Control surface's, and the Web surface drives only the browser, not arbitrary desktop applications

The capability lists are representative hints, not a closed fence (§5.4). The full set varies with installed capabilities, plugins, the active workspace's per-workspace zone overrides, and the active browser backend.

### 5.3 Produced Kinds and Exposed Sensors

The Web surface declares the artifact, observation, and sensor kinds it primarily produces or exposes (`worksurface.actions-declaration`, File 25 §6.2):

- **Primary `ArtifactKind`s**: `BrowserExtract` (a structured extract from one or more pages), `WebDocument` (a self-contained captured or composed web document), `Report` (a synthesized research report with sections and citations), and `Document` (research-adjacent prose) (`artifact.artifact-kind`, File 09 §4); a download is a file `Artifact`; a recorded action sequence is a `Macro`; a captured page series is a `ScreenshotSeries`; web-specialized kinds register through the canonical mechanism
- **Primary `ObservationKind`s**: `BrowserDom` (the captured structured page representation), `NetworkResponseSnapshot` (captured request/response), and `Screenshot` (`artifact.observation`, File 09 §13.2), produced through the canonical `observation.commit` path; an extracted page that backs a citation also captures a `SourceExcerpt` block (`block.kind-catalogue`, File 08 §3.1)
- **Exposed sensors**: the `BrowserPage` sensor (the page's structured accessibility-and-document representation, console, and network responses), the `Screen` sensor (a page screenshot for the grounded and raw tiers and for the guided-browsing view), the `Network` sensor (request/response capture for replayable automation), and the `Filesystem` sensor for the downloads directory (`perception.sensor`, File 19 §4.3), each with its declared privacy class; the surface consumes these sensors' structured output and owns no capture mechanics

### 5.4 The Hint-not-Fence Rule

The Web surface's `primary_capability_ids` are a hint about what is most relevant for web work, not a fence around what the agent may invoke (`worksurface.actions-declaration`, File 25 §6.3). The agent reaches any capability in the one registry through the discovery and borrow capabilities, subject to policy; a web run that needs `file.create` to save an extract, or the coder code-execution capability to parse scraped data, borrows it and remains in the Web surface, with the ledger recording both the originating surface and the borrowed-capability source. Cross-surface access defaults to search-and-borrow, never silent autoload (`run.consequences-for-later-specs`, File 04 §29).

### 5.5 Contributed Approval Posture and Named Availability Checks

The Web surface contributes a default approval posture and references the policy templates and rules File 06, File 22, and File 23 own; it evaluates no policy itself:

- **Untrusted-content posture**: all fetched, searched, and extracted web content enters the model request as `untrusted_source_data` (`context.authority-classes`, File 13 §2.3) and carries no capability or policy authority (`security.untrusted-content`, File 22 §12); this is the surface's default and is non-negotiable (§16)
- **Egress posture**: outbound fetches and navigations are checked against the egress-destination policy and the per-hop redirect re-validation (`security.egress-governance` (File 22 §11), `sandbox.network-enforcement` (File 23 §8)); a destination outside the allowlist (or inside the denylist) escalates to ask-user or denies
- **External-backend escalation**: when the active backend is `External` (the user's own already-authenticated browser), state-changing browser actions carry a stronger approval posture than in `Managed` mode, because the actions occur in the user's real session with real authentication and real history (§7.2); a destructive or irreversible page action (a purchase, a delete, a send) in `External` mode is gated accordingly
- **Elevated browser primitives**: arbitrary page-script evaluation and network interception carry `UserApproval` because they execute or alter traffic the application did not author; sensitive form input is masked (§17)
- **Multi-action batches**: a batch of browser actions presents through the shared batched-approval flow (`policy.batched-approval-flow`, File 06 §5.5), not a private approval flow
- **Credential and payment handoffs**: a login, a payment, or an auth-expiry mid-session is an elicitation handoff to the user (§16, §17); a captcha follows handoff by default and may use challenge assistance only when a separately enabled governed capability is explicitly invoked

The Web surface registers named availability checks (`world.state-aware-capability-availability`, File 18 §9.3) the world model evaluates against the current snapshot — representative: browser-backend-available, browser-session-active, page-loaded, vision-model-available, and research-session-active — each a pure function of the world snapshot that gates the availability of specific capabilities and affordances.

Arbitrary page-script evaluation, generated extraction scripts, and reusable site extractors are capability-mediated operations. Host-side generated code runs under the sandbox and policy contracts; page-context execution declares touched resources, approval posture, and output validation. A generated extractor that proves useful may be promoted to a reusable workflow or capability artifact, but it never becomes hidden script execution outside the registry, policy layer, sandbox, and ledger.

### 5.6 Boundary

This section declares the web actions by reference. File 05 owns the capability declarations and adapter mechanism; File 06 owns the policy evaluation and templates; File 07 owns the `SubsystemSurfaceSpec` and composition; File 22 owns the untrusted-content, egress, and credential rules; File 23 owns the network enforcement; Files 09 and 19 own the artifact, observation, and sensor kinds. This file names what the surface contributes; those files own how.

## 6. The Fetch-Search-Extract Contract

Anchor: `web.fetch-search-extract`

### 6.1 Definition

The fetch-search-extract contract is the set of rules by which the Web surface acquires and structures web content: search returns ranked source records, fetch acquires a page's content, extraction structures it, and every acquired source is a durable, citable, freshness-fingerprinted block over the shared retrieval, blob, and citation substrates. Search, fetch, and extract are distinct capabilities that may share lower-level fetchers, caches, and extractors (`retrieval.capability-surface`, File 12 §13.3); their operation, approval, and output differ, so they remain distinct.

### 6.2 Web Search

`web.search` (and the `web.search_academic` variant) issues a query to a replaceable search backend and returns a ranked set of source records normalized to the `RetrievalHit`/`WebHit` envelope (`retrieval.retrieval-result`, File 12 §9): url, title, snippet, and source metadata. Search is an explicit capability call, never a hidden side effect of local retrieval (`retrieval.retrieval-pipeline`, File 12 §8.4). The query may be reformulated, scoped by an allowed/blocked egress destination set, and scoped to web or academic sources; that destination set is the egress-destination policy (`security.egress-governance`, File 22 §11.4), not a private allowlist. The search backend (a metasearch sidecar, a provider search API, a connector) is a replaceable implementation behind the capability and runs as a `ManagedProcess` or a connector where it is a local service; the surface owns no private search engine. The local knowledge base is consulted before the web where the workflow prefers it (the borrowable knowledge-search capability), per the dedicated-tool and fetch-fallback discipline (`policy.built-in-reusable-policy-rules`, File 06 §11.5).

### 6.3 Web Fetch

`web.fetch` acquires a single page's content and is the canonical fetch capability `unit06-tools.md` and `tools/web-search-and-rag.md` define. Its multiple acquisition strategies — HTTP fetch, smart crawling, rendered-browser acquisition, in-application browser acquisition, and challenge detection with user handoff — are capability sub-modes within one capability, not separate model-facing calls (`capability.capability`, File 05 §2.3, `run.tool-calls` (File 04 §9)). The invocation record contains ordered acquisition-attempt subrecords: strategy class, resolved destination, backend class, policy decision when escalation changes risk, result or typed failure, and the final selected content source. If escalation changes touched resources, backend authority, credential posture, or egress class, policy may re-enter approval before that attempt proceeds. The canonical contract is the durable outcome (§6.5), the freshness fingerprint (§6.4), the egress check (§5.5), and a typed error when acquisition fails; the specific fetch tiers and their order are a capability-declaration and implementation concern the canon keeps out of the body. `web.fetch` is `ConcurrencySafe` for distinct urls, so a batch of fetches runs in parallel (`run.parallelism`, File 04 §15); a batch of many fetches that process into a comparison is the canonical programmatic-execution use case (`run.programmatic-execution`, File 04 §14) rather than many separate model-emitted calls.

Challenge-assistance integrations are not hidden fetch strategies. They may exist only as separately declared, disabled-by-default capabilities or plugins under the capture-ethics, egress, and typed-confirmation rules: the user must have standing to proceed, the site posture must be respected by policy, spending requires explicit authorization, and the result remains a handoff or governed capability outcome rather than an invisible bypass. The baseline Web surface treats bot-detection challenges as detection plus handoff (§16.4).

### 6.4 Content Extraction and Freshness

Extraction turns acquired page content into structured form. `web.extract_document` supports text, structured (schema-driven), and markdown extraction modes as capability sub-modes; the boilerplate-stripping reader-mode and HTML-to-markdown extractors are replaceable implementations behind the capability. A repeated schema extraction may be promoted to a reusable site extractor or workflow through the same capability, sandbox, policy, validation, and ledger path (§5.5, §11.4). An extracted page is a durable block; when it backs a claim or is pinned, it is a `SourceExcerpt` block (`retrieval.chunking-excerpts`, File 12 §5.2) or a `BrowserExtract`/`WebDocument` artifact (§11). Freshness is determined by source fingerprints, not a clock (`retrieval.maintenance-freshness`, File 12 §18): a captured page records a `StalenessFingerprint` (`EtagAndLastModified`, `DomSignature`, or `ContentHash`, `artifact.observation` (File 09 §13.3)); an expired cache entry is stale, not false, and the surface refetches, warns, or proceeds per policy (`retrieval.retrieval-pipeline`, File 12 §8.4). Cached pages are searchable through the `web_cache:<scope_id>` namespace (`retrieval.namespaces`, File 12 §3.2); the cache is a content-addressed blob projection over the storage substrate (`storage.blob-store`, File 20 §6), never a private store. A cache time-to-live is an optimization, never a correctness condition.

### 6.5 The Persistent-Content Outcome

Every acquired source produces durable, citable content: a search result is a source record, a fetched page is an `Observation` (`BrowserDom` for a rendered page, `NetworkResponseSnapshot` for a captured response) with a `StalenessFingerprint`, and a structured extract is a `BrowserExtract`/`WebDocument` artifact. Each carries provenance — the acquiring run, capability, query or url, and capture time (`artifact.provenance`, File 09 §15) — and a `Citation` with the source url and span (`artifact.citation`, File 09 §12) so the content is citable and re-findable. A captured source span is addressable for highlighting, excerpt promotion, and citation without copying the whole page into the transcript (`retrieval.chunking-excerpts`, File 12 §5.3). The surface produces durable evidence; it never returns artifact- or evidence-grade web content as transcript prose alone (§22).

### 6.6 Boundary

This section defines the fetch-search-extract contract. File 12 owns the retrieval index, namespace, query, ranking, and the cache projection; File 09 owns the observation, citation, source-excerpt, and artifact contracts; File 20 owns the blob store; File 22 owns the egress destination policy. The search backend, the fetch tiers, and the content extractors are replaceable implementations behind the surface's capabilities.

## 7. Browser Sessions, Pages, and Automation

Anchor: `web.browser-sessions`

### 7.1 Definition

A browser session is a persistent, identified browsing context the Web surface drives; a page is a tab or target within it. A session is a `BrowserSession` `WorldEntity` (`world.world-entity`, File 18 §4.3) bound to a `Sandbox`-confined `ManagedProcess` (`sandbox.contract`, File 23 §3); each page is a `BrowserPage` entity carrying its url, title, viewport, and navigation availability. Sessions are persistent (resumable across pauses, restartable on crash, terminable), and commands are transient operations against them; this separation lets a session resume after restart, switch presentation without re-authenticating, and run in parallel with other sessions.

### 7.2 Backend: Managed and External

The browser backend is a replaceable implementation behind the session contract, with two backend kinds selected by a per-conversation setting (`surface.web.backend`):

- `Managed` (the default): Atlas spawns and owns an isolated headless browser process under a web `SandboxProfile` (§13.4), with no user context and no authentication state from the user's regular browser. This is the primary path for agent-driven browsing, automation, and the tiered fetch pipeline.
- `External`: Atlas drives the user's already-running browser through a browser extension over a local control channel, operating on pages the user is already authenticated to. The tradeoff is reduced isolation — the agent's actions appear in the user's real browser, history, and sessions — so `External`-backend state-changing actions carry the stronger approval posture of §5.5, and the surface surfaces that the session is the user's real browser.

The logical browser capability family is shared across both modes; resolved availability, touched resources, approval posture, isolation guarantees, and ledger attribution differ by backend. `External` does not satisfy the managed-browser sandbox guarantee: it is a local-control integration over user session state and carries an explicit reduced-isolation marker consumed by policy and execution records.

The local control channel between Atlas and an External browser extension is authenticated and localhost-only. The extension validates the identity and origin of every control message against a session-established credential before executing any command. A control message from an unauthenticated or non-local source is rejected. The concrete authentication mechanism is an implementation choice; the behavioral requirement is that no entity other than the local Atlas runtime can issue commands through this channel.

The concrete browser engine, the extension transport, and the native-messaging bridge are replaceable implementations behind the contract; the surface owns no private browser process or control channel (`sandbox.consequences-for-later-specs`, File 23 §21).

### 7.3 The Browser Command Set

The Web surface contributes a browser command family covering session lifecycle, navigation, interaction, tabs and frames, waits, and state queries (§5.2). The interaction primitives address elements through the structured page representation's stable node references (§8) with a coordinate fallback and a vision fallback (§7.4); selectors are validated and escaped before any page-script evaluation (`security.local-posture`, File 22 §13.4). Waits are explicit conditions (a selector appears, navigation completes, a page-lifecycle event fires, a script predicate becomes true) driven by browser-protocol events, not fixed delays — a fixed post-action sleep is rejected as racy (§22), and event-first readiness detection is the canonical mechanism (`perception.triggers`, File 19 §8). A script-predicate wait is allowed only as an explicit, bounded, killable wait mode that returns a typed failure when the condition is not met; it is a safety guard around a condition, never a hidden polling correctness rule. A file upload reads a workspace-relative path through the filesystem boundary (`sandbox.filesystem-enforcement`, File 23 §7); a download is materialized as a file artifact (§11). Each browser command's concurrency is declared: a session is stateful, so its mutating commands are `Exclusive` within the session's resource scope, while read-only state queries are `ConcurrencySafe` (`run.parallelism`, File 04 §15.2); a navigation or a state-changing click declares `terminates_sequence` so queued sibling commands in the same batch that observed the prior page state are invalidated (`capability.execution-semantic-fields`, File 05 §7.1), with the runtime URL-change detection as defense-in-depth.

### 7.4 The High-Level Act/Observe/Extract Layer

Above the low-level commands, the Web surface contributes three high-level capabilities that encapsulate the structured-snapshot → model → execute pattern:

- **act** — a natural-language instruction ("click the login button") resolved against the page's structured representation (§8): the surface captures the structured state, the model selects the target node and intended effect, the surface executes the appropriate low-level command, and a post-action structured snapshot diff confirms the effect. If the page changed or the expected effect did not occur, the operation returns a typed mismatch/no-effect outcome or re-enters the normal loop for re-observation. The resolved action is cached so a repeated instruction on the same page state replays without a fresh model call (§7.5).
- **observe** — find candidate actions for an instruction without executing, for previews and confirmation
- **extract** — schema-driven structured extraction from the page's structured representation into a typed result, validated against the requested schema. URL and reference fields must ground to captured anchors, requests, source spans, or page-graph references when the schema asks for them; invented URLs are invalid extraction output.

The three primitives are the agent's preferred surface; the low-level commands remain available as escape hatches. The model used for act and extract is selected through the Model Strategy layer (`model.model-selection-algorithm`, File 16 §7), defaulting to the conversation's model with a vision-capable route where grounded sensing is needed; the surface invokes no model directly (§5.5).

### 7.5 Action Caching

A resolved act-target for a given instruction and equivalent page state is cached so a repeated instruction can replay without a fresh model call. The cache is keyed by instruction, normalized page identity, frame identity, structured-state fingerprint, relevant viewport or layout fingerprint, capability/schema version, structured extractor version, and resolver model/profile class where it affects target selection. Sensitive argument values are never stored as plain cache keys; variable shapes or redacted placeholders are used where needed. Replay revalidates the target node, frame, and stale-state fingerprint before execution. Policy, capability-version, extractor-version, or meaningful page-structure changes invalidate affected entries. Action caching is an optimization over the act primitive, never a correctness condition; a cache miss falls back to fresh model resolution. The cache is a rebuildable projection, not a durable source of truth.

### 7.6 Boundary

This section owns the browser-session and automation workflow. File 18 owns the `BrowserSession`/`BrowserPage` entities; File 23 owns the `Sandbox`, the `ManagedProcess`, the network and filesystem enforcement, and killability; File 19 owns the page sensor and capture; File 16 owns the model selection for act and extract. The browser engine, the extension transport, and the action-cache implementation are replaceable implementations behind the surface's capabilities.

## 8. Page State and Observation

Anchor: `web.page-observation`

### 8.1 Definition

Page state is the Web surface's structured model of a browser page, the input to every page interaction and extraction. The Web surface is structured-data-first: it reads a page through `Perception`'s `BrowserPage` sensor (`perception.sensor`, File 19 §4.3) and the `SensingTier` strategy (`perception.tiered-sensing`, File 19 §5), and never through screenshots when a structured representation is available (`core.world-model`, File 01 §6.7). The surface owns no private page-state model; it consumes the sensor's structured output and projects it into the `BrowserPage` world entity and the `browser` panel.

### 8.2 The Tiered Page Representation

A page is sensed at one or more tiers, mapped onto the canonical `SensingTier` order (`perception.tiered-sensing`, File 19 §5.1):

- **`Structured`** (the default and primary representation): the page's own machine-readable structure — its accessibility tree, document structure, frame tree, stable per-node references, semantic roles, accessible names, and frame/origin provenance where available. This is the primary input to the model: it is precise, semantically rich, far cheaper in tokens than a screenshot, works with any text model, and gives each interactable element a stable reference the surface resolves to the actual element without selector ambiguity. A model-facing projection may flatten the representation for readability, but the underlying representation preserves frame identity, origin, and action context; selectors and actions do not silently cross frame boundaries.
- **`Grounded`** (when the structured tier is absent or insufficient): element detection and optical-character recognition over a screenshot, for a canvas-rendered page, a poorly-accessible page, or vision-based clicking when a structured reference cannot resolve. The grounded tier is a `Perception` processor over a `Screenshot` capture, keyed by the processor invocation (`perception.output-contract`, File 19 §9.4), and merges with the structured tier where their regions correspond (`perception.tiered-sensing`, File 19 §5.3). Structured state wins by default for semantic and actionability attributes such as role, name, state, and interaction affordance. Geometry and visual attributes use the per-modality authority rule declared by the producing sensor; disagreements are typed conflict facts or action-precondition warnings, never silently resolved.
- **`Raw`** (when the capture need requires pixels): the screenshot itself, for a vision model, for visual evidence, for coordinate grounding, or for the guided-browsing presentation. The screenshot is a `Screenshot` `Observation` captured only when needed.

The surface must not skip an available cheaper tier when that tier satisfies the need (`perception.tiered-sensing`, File 19 §5.2): the structured representation is read first, grounded detection is added when structure is insufficient, and a screenshot is captured only for a vision consumer, visual evidence, or coordinate grounding.

### 8.3 Observations, Fingerprints, and Staleness

A deliberately captured page state is an `Observation` block: the structured representation is a `BrowserDom` observation, a captured response is a `NetworkResponseSnapshot`, and a screenshot is a `Screenshot` observation (`artifact.observation`, File 09 §13.2), each carrying a `StalenessFingerprint` (`DomSignature` for the structured page, `EtagAndLastModified` for a cached response, `ContentHash` for content). Console output and network responses are diagnostic observations, not part of the primary structured page tree; they are included only when requested, relevant, or committed for audit. A browser action that depends on a prior page observation revalidates currency before acting and returns a typed `StateChangedSinceObservation` error on mismatch (`run.call-pipeline`, File 04 §8.2), so the agent re-observes and retries rather than acting on a stale page. The structured page state is cached per page and invalidated event-first on a document-change or navigation event (§12), so repeated reads of an unchanged page hit the cache; the cache is a projection, never a durable fact. Page memory — what the surface knows of a page across captures — is the version-graph and observation history, not a private store.

### 8.4 Boundary

This section owns the web page-observation workflow. File 19 owns the sensor, the tier strategy, the capture pipeline, and the stagnation signal; File 09 owns the observation kinds, the staleness fingerprint, and the source excerpt; File 18 owns the `BrowserPage` entity the observation projects into. The structured-representation extractor, the element-grounding model, and the optical-character-recognition processor are replaceable implementations behind the sensor.

## 9. Web Research and the Research Session

Anchor: `web.research`

### 9.1 Definition

Web research is the Web surface's workflow for gathering, organizing, and synthesizing web content into a durable, cited output. It composes search, fetch, extraction, evidence capture, and synthesis (§6, §10) into a strategy whose depth scales with the task, and it records its work as a research session that is a view over the version tree, not a parallel store.

### 9.2 Research Strategies

The Web surface declares three research strategies, scaled by task and selectable per request and by setting:

- **quick** — a single search, returning ranked source records and snippets without deep fetching or synthesis; for a direct lookup. Its output is search-result-only unless a follow-up fetch or capture creates durable evidence; snippets are not promoted to evidence-bearing claims by themselves.
- **standard** — search, fetch the top sources, extract, and synthesize into a short cited summary; the common research path
- **deep** — a perspective-guided, iterative, outline-driven workflow producing a comprehensive cited report (§9.3)

These are built-in strategy profiles, not the closed universe. Users, workspaces, and plugins may register custom research strategies through the settings, capability, and workflow registration paths, declaring budgets, source-quality policy, allowed capability families, child-run roles, validation requirements, and output contract. Every strategy reuses the same evidence, citation, policy, and ledger contracts. A strategy sets a tool and iteration budget (`run.budgets-limits`, File 04 §21) as an advisory ceiling, not a hidden hard limit; the user may override the strategy and its budget per scope. The strategy is a research-workflow parameter, not an autonomy mode and not a phase machine (§22).

### 9.3 The Deep-Research Workflow

The deep-research strategy is a run structure over the shared execution substrate (`run.execution-entry`, File 04 §4, `run.programmatic-execution` (File 04 §14)), composed of child runs (`run.child-runs-multi-agent-work`, File 04 §16), not a private orchestration engine. Its representative stages: discover diverse perspectives on the topic; for each perspective, spawn a research child run that iteratively searches, fetches, reads, extracts cited findings, identifies gaps, and reformulates queries until its iteration budget or a done signal; filter sources by quality (§10); generate an outline; for each outline section, spawn a section-writing child run that drafts the section from the relevant findings under the citation rule; cross-validate claims across sources, flag contradictions, and surface uncertainty; and polish into the final report. Each stage writes durable stage outputs — queries, source records, captured excerpts, claims, outline sections, contradiction notes, validation results, and child-run outputs — so resume reconstructs state from blocks and ledger entries rather than private checkpoints or silent live refetch. Fresh live refetch is an explicit capability call governed by freshness policy. The surface declares the spawnable research sub-agent kinds (a perspective researcher, a source validator, a section writer) as `spawnable_subagent_types` in its `SubsystemSurfaceSpec` (`worksurface.runtime-execution-declaration`, File 25 §9.2); child runs return through the canonical output contracts (`run.merge`, File 04 §16.4) and never mutate the coordinator's state directly. Each child run records its own selection and budget; the coordinator and the user incorporate results through the normal pipeline. Per-perspective child runs may share a cached model-request prefix (the topic and outline) for cost (`context.cache-marker-candidates`, File 13 §11).

### 9.4 The Research Session as a Version-Tree View

A research session is a named query over the conversation's version tree that gathers the blocks tagged with the session's identity — its search results, captured pages, source excerpts, citations, claims, evidence links, and synthesized sections. The session has no separate row storage: listing what a session gathered is a query over the blocks carrying the session annotation, not a join across parallel tables. The prior parallel research-session, search-results, and fetched-pages table family is superseded (§22); recovering "what did this research find" is a version-tree query (`version.consequences-for-later-specs`, File 11 §24), exactly as the coder session log is an export projection (`coder.session-logging`, File 27 §17). A research session is created with the research capability, returns a session identity, and the subsequent search, fetch, extraction, and synthesis operations tag their output blocks with it; the runtime `ResearchSession` view is populated from the version-tree query.

### 9.5 Boundary

This section owns the web research workflow. File 04 owns the run, child-run, programmatic-execution, and budget contracts; File 11 owns the version tree the session views; File 09 owns the claim, evidence, and citation records the synthesis produces; File 16 owns the model selection per research role. The synthesis and outline-generation prompts are model-request contributions assembled through File 13, never private model requests.

## 10. Evidence, Citation, and Source Trust

Anchor: `web.evidence-citation-trust`

### 10.1 Definition

Web research is the canonical evidence-bearing workflow: its load-bearing outputs are `Claim`s grounded in `Evidence` linked to captured `Citation`s and source excerpts, with source trust as evidence confidence and source-credibility metadata. The Web surface produces these records through the canonical capabilities (`artifact.claim-extraction` (File 09 §10), `artifact.evidence` (File 09 §11), `artifact.citation` (File 09 §12)); it owns no parallel claim, evidence, or citation store.

### 10.2 Citation Capture

A citation captures an external source as a durable, addressable reference: the source url, the captured-at time, the retrieval strategy, and an optional `SourceSpan` narrowing to the cited portion of the page — a character range, a structured-node selector, or a content span (`artifact.citation`, File 09 §12). A url-only citation is a reference, not durable content; evidence-bearing or high-impact use links to captured support content — a `SourceExcerpt`, a `BrowserDom` observation, or a `BrowserExtract` artifact version — so the cited material survives the source changing (`artifact.citation`, File 09 §12.1). The Web surface's search, fetch, and extraction capabilities produce citations as a matter of course (`artifact.citation`, File 09 §12.4); the surface enforces a citation discipline on synthesized output (§10.4).

### 10.3 Source Trust and Credibility

Source trust composes the File 22 trust model with web-specific source-credibility metadata. A source carries attributed credibility signals — configured source reputation, recency and freshness, author or publication authority, corroboration across independent sources, and user, workspace, plugin, or curated preference/block signals — recorded as `Evidence` confidence (`artifact.evidence`, File 09 §11.4) and surfaced in the `sources` panel. There is no hidden canonical reputation list: credibility inputs are explainable metadata resolved through settings, source approval, and evidence policy. Source quality filtering bounds a research workflow to credible sources, prefers a user's preferred sources, and caps how much any one source dominates the findings; a research finding marked disputed or contradicted is surfaced, not silently dropped (`artifact.claim-status`, File 09 §9.4). Source trust is evidentiary metadata, never a substitute for the structural untrusted-content rule (§16): a high-credibility source's content still holds no capability or policy authority.

### 10.4 Citation-Grounded Synthesis

The Web surface's synthesis workflow requires every factual claim in a deep- or standard-research output to cite a source: a claim that cannot be supported by a captured source is surfaced as unsupported and excluded rather than asserted, and citations are never invented. Each synthesized claim is a `Claim` block with `Evidence` links to its supporting sources and `Citation`s carrying the source url and span; the synthesized output renders the citations as resolvable references. The citation discipline is a contributed approval-and-validation posture (`artifact.validation-critique`, File 09 §14) over the synthesis capability, not a hardcoded prompt string; the exact requirement text is a model-request contribution assembled through File 13.

### 10.5 The Research Canvas

The research canvas (the `canvas` panel, §4.2) is a graph projection over the research session's blocks and entities: queries, sources, extracts, claims, clusters, takeaways, and contradictions render as nodes, and their relations (cites, corroborates, refutes, derives) render as edges, drawn from the block graph and the evidence links (`block.block-edge-block-graph` (File 08 §5), `artifact.evidence` (File 09 §11.3)). The canvas is a presentation over the shared substrate, not a private store; pinning a canvas node to memory, composing it into a report, or exporting it operates on the underlying blocks. The graph-layout renderer is a replaceable UI implementation behind the panel.

### 10.6 Boundary

This section owns the web evidence, citation, and source-trust workflow. File 09 owns the claim, evidence, citation, and source-excerpt contracts and the validation-state derivation; File 22 owns the trust model the source credibility composes with; File 08 owns the block graph the canvas projects. This file owns the web workflow over them and the source-credibility metadata.

## 11. Web Artifacts, Downloads, and Macros

Anchor: `web.artifacts`

### 11.1 Definition

The Web surface's durable user-visible outputs are `Artifact`s: structured extracts, captured documents, research reports, downloads, captured page series, and replayable action macros. Each is an `Artifact` entity over the shared substrate (`artifact.chosen-model`, File 09 §1) with versioning, materialization, validation, review, and provenance; the surface owns no parallel artifact store.

### 11.2 Artifact Kinds

The Web surface primarily produces:

- `BrowserExtract` — a structured extract from one or more pages: text, structured sections, and citations; the canonical artifact for a captured-and-structured page
- `WebDocument` — a self-contained captured or composed web document (a saved page or a generated standalone document) the user may keep, embed, or share
- `Report` — a synthesized research report with sections, claims, and citations, composed over its constituent blocks
- `Document` — research-adjacent prose
- a file `Artifact` — a download (§11.3)
- `ScreenshotSeries` — an ordered set of captured page screenshots with optional annotations
- `Macro` — a recorded, parameterized, replayable browser action sequence

Each is an `ArtifactKind` from the canonical catalogue or a registered web `Custom` kind (`artifact.artifact-kind`, File 09 §4); media artifacts use `External` content per the catalogue's composition rules.

### 11.3 Downloads

A download triggered by a browser action is materialized as a file `Artifact`: the surface routes the download through a staged or quarantined location under the sandbox/workspace boundary, normalizes the network-provided filename, prevents path traversal, classifies MIME/content where possible, atomically materializes the accepted file into the workspace downloads directory through the filesystem boundary (`sandbox.filesystem-enforcement`, File 23 §7), registers the downloaded file as a file block in the version tree (`workspace.materialization`, File 24 §10), and surfaces a download record with its workspace-relative path and progress through the activity panel (`run.streaming-partial-execution`, File 04 §12). Downloads to the workspace downloads directory are `WorkspaceWrite`; a web-scoped download policy may tighten this (§17). Downloaded content is untrusted source material: executables, scripts, archives, and unknown file types are never auto-opened or executed, and unsafe or unknown downloads remain visible with policy warnings until the user or policy accepts the next step. A download is a durable file artifact, never an untracked file outside the workspace.

### 11.4 Macros

A macro is a recorded browser action sequence the user may parameterize and replay. A macro is a `Macro` artifact (`artifact.artifact-kind`, File 09 §4) carrying capability-level steps, stable node references or selectors where available, required page/session preconditions, parameter slots, and secret references; it is not blind coordinate replay. Macro playback is fresh execution over the saved artifact: it invokes the steps through current browser capabilities, policy, and ledger recording, with parameter substitution and sensitive values masked (§17). Playback revalidates the page/fingerprint before each dependent step and pauses or fails typed when preconditions do not hold. Coordinate-only steps are fallback steps and require stronger revalidation. Historical ledger replay reconstructs a prior macro execution for audit and debugging and must not dispatch live browser actions (`ledger.replay-semantics`, File 10 §11); the surface introduces no separate session-recording store, and the macro covers the reuse case that a full deterministic event recording would otherwise require. Promoting a successful browsing sequence to a reusable macro or workflow is the Workflows-and-Reuse path (`run.automation-reuse`, File 04 §26).

### 11.5 Boundary

This section owns the web artifact, download, and macro workflow. File 09 owns the artifact kinds, materialization, validation, and provenance; File 24 owns the downloads directory and the disk mirror; File 23 owns the filesystem boundary; File 10 owns historical ledger replay without side effects; File 11 owns the version graph. The macro format is a capability-declaration concern; this file owns the workflow.

## 12. Page Monitoring and Reactive Session Health

Anchor: `web.monitoring`

### 12.1 Definition

The Web surface watches the web in two registers: deliberate change monitors (a user watches a page or feed for changes) and reactive session health (the surface reacts to navigation, downloads, dialogs, crashes, resource pressure, security events, and loops while a browsing run proceeds). Both are realized over canonical owners — perception, the event bus, stuck and stagnation detection, the sandbox, the egress policy, and the elicitation rail — and introduce no private watchdog subsystem, no private event bus, and no private monitoring store.

### 12.2 Change Monitors

A change monitor watches a page or feed and acts when it changes. A monitor is a `Trigger`-rail entry (`controlrail.chosen-model`, File 26 §1, the `Trigger` rail kind): registering a monitor declares the target, the change condition, and the action; the monitor's firing produces a `RunIntent` (`routing.trigger-kinds-routing`, File 03 §2.1) that runs the action. Change detection is event-first where the source emits change signals (a feed update, a page-change event) and otherwise a configurable polling cadence that is a flagged fallback, never a correctness condition (`perception.triggers`, File 19 §8.2) — the system remains correct if a scheduled check never runs. Change detection diffs the page's captured state against its prior captured state using the page's `StalenessFingerprint` and the version-graph history of its `BrowserDom` observations (§8.3); a detected change is a durable fact. The deep scheduling, eligibility, enablement, and non-interactive-execution-safety mechanics of monitors belong to the future Automation and Triggers spec; this file frames the web monitor as a `Trigger` consumer and the `monitors` panel as its projection (§4.2). A monitor that observes the user's authenticated session uses the `External` backend and its stronger posture (§7.2).

### 12.3 Reactive Session Health — Mapped to Canonical Owners

The web-specific reactive monitoring behaviors the source material gathered into a watchdog subsystem are each declared here and mapped to their canonical owner; the Web surface owns the behaviors and the entities and sensors they observe, not a private monitoring layer:

- **page-load readiness, document-change, and network-response observation** — `Perception`'s `BrowserPage` and `Network` sensors, event-first (`perception.sensor` (File 19 §4.3), `perception.triggers` (File 19 §8)); these invalidate the cached page state (§8.3) and drive re-observation
- **session crash and process liveness** — the `ManagedProcess` and `Sandbox` liveness facts and kill/reap contract (`process.killability`, File 23 §10); a crashed session is reaped or restarted per its declaration, and the `BrowserSession` entity's liveness reflects it (`world.environment-temporal-connection-facts`, File 18 §6.3)
- **resource pressure** — the browser `SandboxProfile`'s `ResourceLimits` event-driven thresholds (`sandbox.resource-limits`, File 23 §9); a memory or process threshold crossing raises a typed event and triggers tab cleanup or session restart, never a timer
- **navigation security and redirect drift** — the egress-destination policy and per-hop redirect re-validation (`security.egress-governance` (File 22 §11.4), `sandbox.network-enforcement` (File 23 §8)); a navigation to a disallowed destination is blocked with a typed error
- **loop and page stagnation** — `run.stuck-detection` (File 04 §20.3) over repeated identical actions and `perception.output-contract` (File 19 §9.6)'s stagnation signal over consecutive identical page captures; a detected loop injects an in-band corrective signal to the model and escalates to a hard stop after repeated detection, never silently
- **captcha, login, payment, and auth-expiry handoff** — the elicitation rail (§16, `controlrail.chosen-model` File 26 §13) under the capture-consent and privacy contract (`perception.capture-privacy`, File 19 §10); a challenge is a handoff by default, with challenge assistance available only through a separately enabled governed capability
- **JS-dialog handling, console capture, and download tracking** — non-blocking observers on the event bus (`ledger.hook`, File 10 §7) and the download materialization of §11.3; console errors surface to the agent as observations, and a blocking native dialog is handled rather than left to stall the run

The Web surface declares which of these behaviors it monitors and the events and entities each observes; the mechanism, the thresholds, and the enable flags are the owning files' settings composed through the surface's settings namespace (§21).

### 12.4 Boundary

This section owns the web monitoring workflow and its mapping to canonical owners. File 19 owns the sensors and stagnation signal; File 10 owns the event bus and observers; File 04 owns stuck detection; File 23 owns resource limits and process liveness; File 22 owns egress; File 26 owns the trigger and elicitation rails; the future Automation and Triggers spec owns the deep monitor scheduling. This file declares the behaviors; those files own the mechanisms.

## 13. Context, Model, Execution, Sandbox, and Workspace Policy

Anchor: `web.policy-declaration`

### 13.1 Definition

The Web surface declares its default context, compaction, model, execution, budget, sandbox, and workspace policies by reference (`worksurface.context-model-declaration` (File 25 §8), `worksurface.runtime-execution-declaration` (File 25 §9)). It names which policies it defaults to; the policy mechanics stay with their owning files, and every default is overridable through the settings cascade (`settings.scopes-profile-contexts-overlays`, File 15 §5.2).

### 13.2 Default Context and Compaction Policy

The Web surface declares a default web-aware `ContextPolicy` and `CompactionPolicy` from the canonical families (`context.context-policies`, File 13 §4, `context.compaction` (File 13 §12)): the context policy assembles fetched and extracted page content as `RetrievedContext` marked `untrusted_source_data` (§16), prefers source excerpts and structured representations over full raw pages and screenshots for large content, protects the current input and the active page state, and prefers a structured page representation over a screenshot in the model request (§8); the compaction policy preserves the evidence and citation chains of accepted claims and reports (`artifact.evidence` (File 09 §11.5), `context.continuity-summaries` (File 13 §14)), and pages out captured page content to the searchable `web_cache` namespace and references rather than flooding context with full pages (`context.virtual-paging`, File 13 §13). Every model request assembles through the one `ContextAssemblyService`; the surface creates no private model-request path.

### 13.3 Default Model Profile

The Web surface declares a default web-and-vision-capable `ModelProfile` and per-role preferences (`model.model-profile`, File 16 §4): the profile prefers a model with provider-native tool calling and a large request-size window for research synthesis, prefers a vision-capable route where grounded page sensing or screenshot input is needed (§8), and prefers a lower-cost route for search classification, query reformulation, and routine extraction. Per-role preferences distinguish the responder, the research perspective and section roles, the source validator, and the page-interaction model. The surface implements no private model-selection logic; selection stays the Model Strategy layer's, and the user may override the profile per scope.

### 13.4 Default Sandbox Profile and Network Policy

The Web surface declares its default browser `SandboxProfile` (`sandbox.contract`, File 23 §3): a browser-session profile confining the browser process to the operating-system-confined isolation tier, the workspace filesystem region plus redaction-safe profile declarations and downloads directories (`FilesystemPolicy`), a `NetworkPolicy` that permits outbound web access subject to the egress-destination policy and per-hop redirect re-validation (`sandbox.network-enforcement` (File 23 §8), `security.egress-governance` (File 22 §11)), and a bounded memory and process budget with event-driven thresholds. Secret-bearing browser runtime state is device-local (§17, §20), not a syncable workspace artifact. The `External` backend operates against the user's own browser and carries the stronger approval posture and reduced-isolation marker of §5.5 and §7.2 rather than a managed-browser sandbox guarantee. The surface extends the base contract only with its browser-navigation and page-observation capability surface; it redefines no enforcement or kill semantics and opens no private sandbox. Untrusted ingested or downloaded content is treated as carrying no authority (§16) and, where executed or rendered, runs at the isolation tier its trust class requires (`sandbox.isolation-tiers`, File 23 §4.3).

### 13.5 Default Execution Preset and the Plan Capability

The Web surface declares a default execution preset — the surface-runtime structure its browsing and research runs start from (`run.execution-entry`, File 04 §4) — as a model-and-tool agent loop over the shared run lifecycle: observe the page, decide and act, fetch and extract, and synthesize, iterating until completion, pause, or user intervention. For autonomous browsing and deep research, the preset may run strategic planning at an interval rather than every step (a planning review every several navigation steps, validating completion before stopping) as a default execution-preset structure for cost and oversight; this is a run structure over shared semantics, not a planner-versus-navigator phase machine and not a per-surface mode (§22). Planning is the optional shared `plan` capability (`run.task-promotion-task-updates`, File 04 §18): the agent may call it to produce an editable `Plan` block when a research task's complexity warrants it. The surface declares default run budgets as advisory ceilings overridable per scope, never hidden hard limits (`run.budgets-limits`, File 04 §21), and declares the parallel-research sub-agent kinds it spawns (§9.3).

### 13.6 Instruction-File Qualifier and Contribution

The Web surface declares its instruction-file qualifier — the `ATLAS.web.md` variant of the `ATLAS.md` hierarchy (`workspace.instruction-files`, File 24 §9.2) — and its model-request instruction contribution: the surface's identity, the web-environment facts, the untrusted-content discipline, and the web guidance, assembled by context assembly into the `InstructionSources` region with the correct authority class (`context.instruction-sources-workspace-files`, File 13 §16). The surface's instruction contribution is one attributed assembly part among many, never a private prompt the surface owns. Instructions found inside fetched or extracted web content are untrusted data with no instruction authority, regardless of any familiar instruction-file name they bear (§16); only the workspace `ATLAS.md`/`ATLAS.web.md` hierarchy carries instruction authority, resolved through File 24.

### 13.7 Workspace Relationship

The Web surface's views render over the bound `Workspace` (`workspace.conversation-binding`, File 24 §7); its downloads, extracts, captured documents, and reports materialize through the disk↔substrate mirror and File 23's filesystem boundary (§11); its per-surface working convention is a `web/` subdirectory (representatively `research/`, `findings/`, and `downloads/`) projected against the workspace mirror (`workspace.materialization`, File 24 §10). Workspace `.atlas/` may contain web settings, command definitions, and redaction-safe browser-profile declarations or bindings; actual browser profile directories, cookies, local storage, session tokens, absolute profile paths, browser process handles, and extension/native-host handles are device-local (§20.3) and never sync or export. The surface owns no workspace identity, disk-history store, or parallel materialization path.

### 13.8 Boundary

This section declares the web defaults by reference. File 13 owns context and compaction; File 16 owns the model profile and selection; File 04 owns the run, the `plan` capability, and budgets; File 23 owns the sandbox and network enforcement; File 22 owns the egress policy; File 24 owns the workspace and instruction files; File 15 owns the settings resolution.

## 14. Views, View Presets, and the Web Shell

Anchor: `web.views-presets`

### 14.1 Definition

The Web surface declares the presentation shapes it offers: the view presets a user can switch between, the default inspectors, the customization policy, and the activity-feed and shell affordances. A view preset is a named startup presentation shape; it is not an autonomy mode and does not silently change backend policy (`worksurface.views-presets`, File 25 §7).

### 14.2 View Presets

The Web surface ships built-in view presets — representatively a default preset (browser, search, sources, and conversation), a researcher preset (search, sources, reader, and the research canvas, for passive research), a controller preset (the browser viewport, the control affordances, and the activity feed, for active browsing), a research-synthesis preset (the report and canvas with sources, for composing a cited report), and a monitors preset (the monitor list and activity). A view preset declares the panel set, arrangement, and presentation-only startup state; applying it changes presentation only. The researcher and controller presets are the canonical resolution of the prior `WebMode` — they are presentation shapes, never autonomy or participation modes (§22): switching from the researcher to the controller preset opens the browser viewport and the control affordances; it does not change how autonomous the agent is, which model is selected, the context policy, the execution entry, the budget, the sandbox profile, or the approval posture. Selecting a richer preset is progressive disclosure (the user sees more state and asks different questions), never a mode change. The user may save custom presets and override the default per scope (`settings.profiles`, File 15 §7).

### 14.3 The Activity Feed and Inspectors

The Web surface presents an activity feed — the conversational execution display of the browsing or research run — that renders the run's progress through the shared execution-presentation contracts (`run.presentation`, File 04 §25): search and fetch progress, the act/observe/extract steps (with page actions shown against the captured page and extractions shown as structured results), batched approval requests (§5.5), research sub-agent activity (§9.3, collapsible), download progress (§11.3), and streaming synthesis. The feed is a projection over the ledger and event stream, not a private log. The surface declares default inspectors (context, source/citation, network, and execution inspection) as inspector-panel projections over substrate state.

### 14.4 Customization, Morphing, and the Shell

The Web surface declares a customization policy (`worksurface.views-presets`, File 25 §7.4) describing which kinds of customization it permits — panel rearrangement, the browser-and-canvas split, custom panel registration, and widget placement — resolved by the UI customization layer; the surface owns what kinds are allowed, not the concrete placement mechanics. Surface morphing — projecting the web panels and active view preset when the Web surface becomes the active presentation surface — is a UI projection driven by the `SurfaceContract`, the live `SurfaceState`, and the routing decision (`worksurface.views-presets`, File 25 §7.3); it changes presentation, not the work model. Conversation is an always-available control rail and an expand/collapse view, never forced to occupy the primary pane during browsing or research (`worksurface.activation-shell`, File 25 §11.3); a research conversation may move between conversation-first and a web-surface focus over time without changing the work model.

### 14.5 Boundary

This section declares the web view presets and customization policy. The UI Shell and UI Customization specs own shell, panel, morphing, browser-viewport, and canvas-rendering presentation; File 04 owns the execution presentation the activity feed projects; File 15 owns the settings and profiles for saved presets.

## 15. Rails and Control Affordances

Anchor: `web.rails`

### 15.1 Definition

The Web surface declares its control affordances — the user-facing ways to invoke its capabilities — and binds them to the control rails (`controlrail.consequences-for-later-specs`, File 26 §21). It declares which capabilities bind to which default shortcuts, slash commands, and menu entries, registers surface-scoped keybinding contexts and custom commands, and introduces no private rail, invocation registry, or rail autonomy field.

### 15.2 Slash, Custom Commands, and Mentions

The Web surface's control affordances include slash commands resolved through the slash-command rail (`controlrail.consequences-for-later-specs`, File 26 §21) — representatively research, deep-research, browse, search, and monitor commands — and workspace-local custom commands stored in the workspace `.atlas/commands/` directory (`workspace.internal-layout`, File 24 §8.3), each a declarative definition resolved through the capability system, never an out-of-band execution path. Web mentions — a pasted or typed url, a page reference, or a source reference — resolve through the conversation rail's pre-dispatch transformation (`controlrail.boundaries`, File 26 §2.2, `intent.message` (File 02 §3.4)) into attributed context attachments: a pasted url may be offered for fetch-and-attach, and a referenced source resolves to its citation; mentions are attributed context, not hidden model-request text (§16).

### 15.3 Keybinding Contexts and the Palette

The Web surface registers surface-scoped keybinding contexts the keymap resolves chords against (`controlrail.consequences-for-later-specs`, File 26 §21): representatively a browser context (navigate, back, forward, reload, scroll, find-in-page), a researcher context (new search, pin source, capture citation), and a reader context. A keybinding binds a chord to a capability; the chord grammar, the context stack, and the resolver are the control-rail layer's. The surface's capabilities and custom commands surface in the command palette and a quick-open url/source search through the command rail's palette lens; the palette is subsystem-neutral and searches the available-capability list. The surface declares the default web workflow commands — representatively research a topic, summarize a page, extract structured data, monitor a page, and compose a cited report — as capabilities and command definitions reachable through every rail. Voice and external-protocol invocation of web capabilities are the rail layer's.

### 15.4 Boundary

This section declares the web rail bindings and control affordances. File 26 owns the rail primitive, the input-resolution contract, the keymap, the slash grammar, the palette, the mention resolution, the voice session, and the trigger and elicitation rails; File 24 owns the `.atlas/commands/` store; File 05 owns the capabilities the affordances invoke.

## 16. Untrusted Web Content and Injection Defense

Anchor: `web.untrusted-content`

### 16.1 Definition

The open web is the canonical untrusted-content vector: every page, search result, fetched document, feed item, and network response the Web surface gathers is content the system did not author and cannot vouch for. The Web surface's defense is the structural rule File 22 owns: untrusted content holds no authority.

### 16.2 The Structural Rule

All fetched, searched, extracted, evaluated, and page-script-returned web content enters model-request assembly as `authority_class: untrusted_source_data` (`context.authority-classes`, File 13 §2.3) and can never, by its own text, widen a lease, lift a permission floor, lift a typed-confirmation requirement, lower a sensitivity classification, raise a source's trust, or authorize an egress (`security.untrusted-content`, File 22 §12.2). The return value of `browser.evaluate` and any page-script execution is `untrusted_source_data` regardless of who authored the script: the script may be agent-authored, but its return value is content from the page, which the system did not author. An instruction found inside a page — including a page bearing a familiar instruction-file name — reaches the runtime as data the user or policy still gates, never as a command. This rule is the Web surface's default and is non-negotiable; the surface declares no path by which page content gains authority.

### 16.3 Boundary Rendering and Redirect Re-Validation

Web content is rendered into the model request behind explicit instruction-boundary markers as untrusted source data (`context.authority-classes`, File 13 §2.3). Textual cleanup of known injection carriers, such as invisible or tag-channel characters, is defense-in-depth only and never changes authority class, trust, or policy outcome (`security.untrusted-content`, File 22 §12.3). Where a fetch or navigation can be redirected by untrusted content, the destination is re-validated against the egress-destination policy on every hop (`security.untrusted-content` (File 22 §12.5), `sandbox.network-enforcement` (File 23 §8)), so an initially-allowed destination cannot redirect to a forbidden one — the canonical exfiltration-via-redirect defense, which the Web surface is the primary consumer of. The advisory injection classifier (`security.untrusted-content`, File 22 §12.4) may inspect web content and escalate a proposed action to ask-user; it is advisory and never substitutes for the structural rule.

### 16.4 Capture Ethics

The Web surface observes the web; it does not defeat the protections of the sources it observes (`perception.capture-privacy`, File 19 §10.7). The default response to a bot-detection challenge — a captcha or equivalent — is handoff to the user (§17). Challenge-assistance integrations, including any paid service, are valid only as separately declared, disabled-by-default, policy-governed capabilities requiring explicit user enablement, standing to proceed, site-posture compliance, and typed confirmation where risk demands it. Consent and cookie surfaces are treated conservatively, and browser-fingerprint normalization and interaction pacing serve legitimate access (the user's own authenticated sessions, ordinary automation) rather than defeating a challenge the user has no standing to pass. Incidental capture of people or faces in a screenshot raises sensitivity and is subject to redaction; biometric identification is forbidden absent an explicit authorized capability, policy approval, and user consent (`perception.capture-privacy`, File 19 §10.7).

### 16.5 Boundary

This section owns the web untrusted-content posture. File 22 owns the structural rule, boundary rendering, the injection classifier, and the egress destination policy; File 13 owns the authority class and the boundary markers; File 23 owns the redirect re-validation enforcement; File 19 owns the capture ethics. This file declares the Web surface as the primary untrusted-content consumer and fixes the posture as its non-negotiable default.

## 17. Credentials, Authentication, and Egress Governance

Anchor: `web.credentials-egress`

### 17.1 Definition

The Web surface handles web authentication — logins, cookies, tokens, and sessions — and outbound web access. Web credentials are vault-held and never plaintext; outbound access is egress-governed; sensitive input is masked; and authentication that requires the user is a handoff, not an automated capture.

### 17.2 Credentials in the Vault

Web credentials, cookies, local storage, session tokens, and OAuth tokens are held in the `SecretVault` (`security.secret-vault`, File 22 §5) and referenced by `SecretRef`; only redaction-safe metadata (the domain, the name, the expiry, the security flags) persists to the durable substrate, and the credential values never enter the durable ledger, the model context, an event, a log, an export, or a sync stream (`secret.backend-boundary`, File 22 §4). A browser profile's stored authentication state binds to vault-held values, not plaintext on disk; the prior plaintext or app-encrypted profile-credential storage is superseded (§22). Credential lifecycle — store, resolve at point of use, rotate, expire, revoke, and multi-account — is the File 22 contract (`security.credentials`, File 22 §6); the surface resolves a credential only inside backend service code at the point of use, never exposing a value to the agent.
Where a browser engine requires disk-backed authenticated state, that state is encrypted device-locally with vault-held or operating-system-protected key material and represented durably only by redaction-safe metadata. This does not weaken the boundary: raw cookies, tokens, passwords, and equivalent secret-bearing values still never enter the durable substrate, model context, ledger, export, or sync stream.

### 17.3 Authentication Handoff

The Web surface does not programmatically capture credentials. A login, a multi-factor prompt, a payment, or a mid-session auth expiry is an elicitation handoff (`controlrail.chosen-model`, File 26 §13) to the user, who completes the authentication in the browser; the surface then proceeds with the established session. A captcha or equivalent challenge follows the same handoff path unless a separately enabled challenge-assistance capability is explicitly invoked under §16.4. A credential the user does choose to provide for storage enters through a credential-input elicitation that is never-logged and never-stored outside the vault (`security.credentials`, File 22 §6). A profile setup wizard guides the user through manual authentication for a profile; it respects user privacy and handles multi-factor and challenge flows through handoff rather than credential capture.

### 17.4 Sensitive-Data Masking

When a browser action fills a form with a credential or other secret, the value is supplied from the vault and masked in every observable surface: the activity feed, the ledger, the session export, and the model context show a redacted placeholder, never the value (`ledger.sensitivity-aware-persistence-retention`, File 10 §10, `secret.backend-boundary` (File 22 §4)). A `Secret`-classified value never persists raw; a captured page or network response that contains a secret is redacted at capture per the perception secret-redaction contract (`perception.capture-privacy`, File 19 §10.4).

### 17.5 Egress Governance

Every outbound fetch, search, and navigation is egress: it resolves its destination and checks it against the egress-destination policy before connecting (`security.egress-governance` (File 22 §11), `sandbox.network-enforcement` (File 23 §8.3)), with a destination allowlist and denylist (the search and fetch egress destination scope of §6) and a default-deny floor for credential and secret destinations. Server-side-request-forgery vectors — a fetch redirected to an internal or local address — are defended by the network enforcement and the per-hop redirect re-validation (§16.3), and a fetch to a forbidden destination is blocked with a typed error. Exporting or sharing research output that contains `Sensitive` source content is governed egress requiring explicit opt-in, and raw secrets never egress (`security.egress-governance`, File 22 §11.2); the Web surface's exports pass through governed egress and sensitivity filtering (§20).

### 17.6 Boundary

This section owns the web credential, authentication, and egress workflow. File 22 owns the vault, the credential lifecycle, the secret boundary, and the egress-tier policy; File 23 owns the network enforcement; File 26 owns the elicitation handoff; File 10 owns the sensitivity classification and redaction. This file declares the web workflow over them.

## 18. Cross-Surface Composition

Anchor: `web.cross-surface`

### 18.1 Definition

Cross-surface composition is how the Web surface composes with other surfaces: the web capabilities other surfaces borrow, the web content that composes into other surfaces' outputs, and the capabilities the Web surface borrows in place.

### 18.2 Web Capabilities Borrowed by Other Surfaces

The Web surface exposes its search, fetch, and extraction capabilities as registry capabilities other surfaces borrow in place (`worksurface.actions-declaration`, File 25 §6.3, `surface.subsystem-surface-spec` (File 07 §5.5)): the Coder surface borrows `web.fetch` to read documentation, the Data Processor surface borrows web extraction to pull a table from a page, and the Teacher surface borrows web search to gather sources for a lesson. A borrowing surface remains in its own surface; the Web surface owns the capability, the borrowing surface's workflow is its own, and the ledger records the cross-surface reach.

### 18.3 Web Content Composes Across Surfaces

Web extracts, reports, citations, and source blocks compose into other surfaces' outputs through the one block and entity pools (`block.cross-surface-composition`, File 08 §12.3, `artifact.cross-surface-interoperability` (File 09 §17.3)): a research report composed in conversation may carry code children the Coder surface produced and chart children the Data Processor surface produced, and a web extract's table flows into a Data Processor dataset (`retrieval.source-records`, File 12 §4.2). Cross-surface composition is a property of the shared pools, not a web-private integration.

### 18.4 Borrowing in Place and the GUI Control Boundary

A web run that needs a capability outside the surface — file create to save an extract, the coder code-execution capability to parse scraped data, memory recall of a source preference, image generation for a diagram — borrows it in place and remains in the Web surface (§5.4). The Web surface drives the browser, not arbitrary desktop applications; driving a non-browser desktop application is the GUI Control surface's, reached through a routing reroute or explicit user override (`routing.mid-execution-reroute`, File 03 §12), never by silent surface change, and the GUI Control surface's desktop-automation and accessibility capabilities are forbidden by default in the Web surface (§5.2).

### 18.5 Boundary

This section owns the web cross-surface composition. File 07 owns borrowing; Files 08 and 09 own the shared pools; File 03 and File 04 own reroute; the future GUI Control spec owns desktop automation. The borrowing surfaces own their own workflows.

## 19. World-Model, Perception, and Observation Integration

Anchor: `web.world-perception`

### 19.1 Definition

The Web surface integrates with the world model and perception by self-registering its panels and state, contributing the world entities the agent reasons over, exposing the sensors it consumes, and producing the observations its runs depend on — all through the canonical contracts (`worksurface.world-perception-integration`, File 25 §15).

### 19.2 Self-Registration and World Entities

The Web surface self-registers its panels, focus, and selection to the one world model on mount, focus, and content change, and unregisters on unmount (`world.observation-state-update`, File 18 §8.1); a panel it fails to register is a blind spot. It contributes the world entities its work produces — `BrowserSession` (the session id, the backend kind, the profile binding, and the sandbox/process binding), `BrowserPage` (the page id, the url, the title, the viewport, the navigation availability, and the visibility), and `Connection` (the search backend, the browser backend, and any web connector, with liveness) (`world.world-entity`, File 18 §4) — related by the canonical relations. These are the canonical entity kinds File 18 already declares; web-specialized entities register as `Custom` kinds through the proposal-first mechanism. The surface maintains no private state store and is never screen-scraped to learn its own panels' state (`world.explicit-rejections`, File 18 §16). A `BrowserSession`, its pages, its profile, and the absolute browser-profile path are device-local and never sync (§20); the model-facing url is the page url, never a host filesystem path.

### 19.3 Sensors and Observations

The Web surface declares the sensors it exposes — the `BrowserPage` sensor (the structured page representation), the `Console`/diagnostic observation path, the `Screen` sensor (a page screenshot for the grounded and raw tiers), the `Network` sensor (request/response capture), and the `Filesystem` sensor for the downloads directory — and consumes their structured output (`perception.consequences-for-later-specs`, File 19 §19); perception owns the capture mechanics, and the surface owns no private capture pipeline (`perception.explicit-rejections`, File 19 §18). It is structured-data-first: it navigates and extracts through the page's structured representation, not through screenshots, capturing a screenshot only for a vision consumer, visual evidence, or coordinate grounding (§8). It produces `BrowserDom`, `NetworkResponseSnapshot`, and `Screenshot` observations through the canonical `observation.commit` path (§5.3) where a run depends on them for revalidation or replay; transient page captures remain transient until a captured span or page is deliberately committed as an observation or source excerpt.

### 19.4 Availability

The Web surface's available-action list is the available-capability list the world model's availability evaluator computes for the surface's scope (`world.state-aware-capability-availability`, File 18 §9), filtered by the active surface state; the surface registers the named availability checks of §5.5 (browser-backend-available, browser-session-active, page-loaded, vision-model-available, research-session-active) and maintains no private available-action store.

### 19.5 Boundary

This section owns the web world-model and perception integration. File 18 owns the entity catalogue, self-registration, durability tiers, and availability evaluator; File 19 owns the sensors and capture; File 09 owns the observation blocks. This file integrates through them.

## 20. Persistence, Locality, and Portability

Anchor: `web.persistence-locality`

### 20.1 Definition

The Web surface's durable state persists as substrate families through the one storage contract, splits by locality the way a workspace's does, and moves cross-installation through the canonical portability mechanisms. The surface introduces no private durable store.

### 20.2 What Persists and Where

The surface's durable state — its registered `SurfaceContract` versions, its registered `Custom` kinds, its scoped enable state and settings, its registered monitors, and the blocks, artifacts, versions, captured-page observations, source excerpts, citations, claims, evidence, and research-session-tagged blocks its work produces — persists as substrate families and content-addressed blobs through the storage contract (`storage.durable-substrate`, File 20 §3, `storage.consequences` (File 20 §18)); captured pages and downloads resolve from the content-addressed blob store (`storage.blob-store`, File 20 §6). The surface's live state — active panels, focus, selection, the active browser session and its pages, browser process and sandbox handles, the structured-page cache, and the action cache — is computed and rebuilt from self-registration and the version-graph projection, never a durable fact (`worksurface.persistence-locality`, File 25 §16.1); its loss is a rebuild, never data loss. The `web_cache` index, embedding shards, and search caches are rebuildable projections over the durable captured-page blocks and observations (`retrieval.indexing-pipeline`, File 12 §12.3).

### 20.3 Locality

The Web surface's identity splits by locality the way a workspace's does (`worksurface.persistence-locality`, File 25 §16.2, `workspace.locality` (File 24 §4)): the surface's logical declaration, the research artifacts, reports, claims, evidence, citations, and monitor definitions sync, while device-bound runtime state — active browser sessions and pages, browser profiles and their authentication state, browser process and sandbox handles, extension/native-host handles, and absolute browser-profile paths — is device-local and rebuilds or re-authenticates per device and never syncs. A monitor that depends on authenticated session state, a local browser profile, a local extension/native-host, or an `External` backend syncs as a definition, not as an active local binding; activation on another device revalidates backend, credentials, egress policy, sandbox/profile availability, and trigger eligibility. World facts the surface produces (`BrowserSession`, `BrowserPage`, `Connection`) are device-local by default (`portability.what-replicates`, File 21 §11). Vault-held web credentials never sync as raw material (§17, `security.egress-governance` File 22 §11.5).

### 20.4 Portability

The surface's durable research state rides the syncable substrate and the `PortablePackage` for cross-device and cross-installation movement (`portability.consequences`, File 21 §18); a research report, its claims, its evidence, and its citations export losslessly with the captured support content required to verify those claims: source excerpts, captured observations, artifact versions, citation spans, and the content-addressed blobs they reference, unless policy or sensitivity filtering omits them with typed provenance gaps. Search caches, derived indexes, embedding shards, and transient page-cache projections are rebuilt on receive rather than transported. The surface may declare a lossy convenience export (a rendered report document or a saved page), but it passes through egress governance, audit recording, and sensitivity filtering (§17.5) and uses no private export path. The surface persists no unredacted secret or raw credential in any materialized, exported, or synced state, and exposes no absolute host directory layout to the model by default (`secret.backend-boundary`, File 22 §4). Every hash the surface relies on — a captured-page content hash, a blob address, a staleness fingerprint, an export-bundle hash — is computed over a declared `CanonicalEncoding`, never physical bytes (`core.canonical-hash`, File 01 §7.14); the surface defines no new canonical hash.

### 20.5 Boundary

This section declares the web persistence and locality classification. File 20 owns the storage substrate, the blob store, and rebuild orchestration; File 21 owns replication and the package; File 22 owns the secret and egress boundaries; File 24 owns the workspace locality split; File 11 and File 12 own the version-graph and index projections.

## 21. Capability, Event, and Settings Surface

Anchor: `web.capability-event-settings`

### 21.1 Capabilities

The Web surface contributes its capabilities to the one Capability Registry as `Subsystem`-sourced built-ins or web adapters over neutral capabilities (`capability.declaration` (File 05 §3), `capability.adapter-capabilities` (File 05 §17.4)), tier-gated by policy (File 06), surfaced through tool-surface composition (File 07), and invoked through the shared pipeline (`run.call-pipeline`, File 04 §8.2). The capability families are enumerated in §5.2. Each capability declares its touched resources (notably `network` and `browser-session` resources, `capability.touched-resources` (File 05 §6.2)), permission tier and floor, reversibility, concurrency, replay class, validation path, and produced block and observation kinds; the surface introduces no parallel capability registry and no out-of-band action path, and every web capability is the single source for all its invocation paths (`core.extension-planes`, File 01 §6.14). A browser action that depends on a prior page observation declares the stale-state revalidation pattern (§8.3); a fetch or capture declares its `replay_class` so a recorded page replays from its observation rather than a live refetch (`capability.replay-class`, File 05 §7.3).

### 21.2 Events

The Web surface emits its events through the one event bus and ledger with the canonical envelope (`ledger.event-stream`, File 10 §5). Surface-lifecycle and tool-surface events are owned by Files 25, 07, and 18 and flow through their vocabularies; world-entity, observation, version, artifact, claim, evidence, and citation events are owned by Files 18, 09, and 11 and flow through theirs. Web-specific facts that no canonical or owning-file vocabulary already defines register as `Custom { namespace: "web", name, payload }` extensions (`ledger.custom-kind-registration`, File 10 §4.3) — representatively the browser-session lifecycle, navigation, the page-readiness and document-change signals, the download lifecycle, the research-session lifecycle, the synthesis lifecycle, the monitor-fired signal, and the handoff-triggered signal — each declaring its payload schema, cross-reference keys, default sensitivity (a navigation event is `Public`; a credential-handling event is `Sensitive`; a captured page from a sensitive source is classified accordingly), and retention. The surface opens no side-channel store or notification path; events that touch credentials or secrets never carry raw secret material (`ledger.sensitivity-aware-persistence-retention`, File 10 §10).

### 21.3 Settings

The Web surface's behavior is configurable through the one settings system (`core.settings-system`, File 01 §6.8, File 15) as namespaced keys under `surface.web.*`, resolved through the standard cascade and composed with the per-substrate settings the owning files own (the sandbox and network settings of File 23, the egress allowlist and credential settings of File 22, the perception sensor and capture-consent settings of File 19, the retrieval and cache settings of File 12, the context and compaction settings of File 13, the model and vision-route settings of File 16, the policy settings of File 06, the trigger and automation settings of File 26 and the future Automation spec). Representative web settings dimensions: the browser backend (`Managed`/`External`) per conversation, the built-in and custom research strategy profiles and their perspective and iteration budgets, the search backend and the destination allowlist/blocklist, the vision-fallback model, the fetch and cache freshness policy, the anti-detection profile within the capture-ethics floor (§16), disabled-by-default challenge-assistance capability enablement where policy permits it, the download policy and directory, the monitor cadence fallback, the per-monitor enable flags, and the default view preset. The surface is not a durable settings scope (`settings.scopes-profile-contexts-overlays`, File 15 §5.1); per-surface variation is namespaced keys plus profile layers. Settings whose values are security-sensitive (the backend choice, the anti-detection profile, challenge-assistance enablement, the egress allowlist, and the credential and download policies) declare conservative agent exposure (`policy.agent-exposure-policy-settings`, File 06 §16.4); no web behavior with meaningful variation is a hardcoded constant (`settings.settings-over-constants`, File 15 §13).

### 21.4 Boundary

This section names the web capability, event, and settings surface. File 05 owns the capability contract; File 06 owns policy; File 10 owns the event bus and custom-kind registration; File 15 owns the settings model and cascade; the owning substrate files own the per-substrate settings the surface composes with.

## 22. Explicit Rejections

Anchor: `web.explicit-rejections`

The following are architecturally invalid for the Web surface and for any later spec that extends it:

- **Splitting the Web surface into an unrelated search tool and browser-control tool** — search, browsing, extraction, citation, automation, and monitoring share one persistent web substrate; researcher and controller are view presets, not separate architectures (§1, §14).
- **Web content stored only as transcript prose** — gathered web content is a durable `Observation`, `Artifact`, `Claim`, `Evidence`, or `Citation`; storing artifact- or evidence-grade web content only as an assistant message is message inflation (`artifact.consequences-for-later-specs`, File 09 §22) and is rejected (§6.5, §10).
- **A private page-state model, screenshot-primary page sensing, or a private capture pipeline** — page state is read structured-first through `Perception`'s `BrowserPage` sensor and the tier strategy; a screenshot is the raw fallback tier, never the primary representation, and the surface owns no capture mechanics (§8; `perception.tiered-sensing`, File 19 §5, `perception.explicit-rejections` (File 19 §18)).
- **A private watchdog/monitoring subsystem, a private event bus, or a private monitoring store** — reactive session health is mapped to its canonical owners (perception sensors, event-bus observers, stuck/stagnation detection, sandbox resource limits, egress policy, the elicitation handoff), and change monitors are `Trigger`-rail entries (§12; `world.explicit-rejections`, File 18 §16, `ledger.explicit-rejections` (File 10 §18)).
- **A parallel research-session, search-results, fetched-pages, or page-cache store** — a research session is a view over the version tree, search results and fetched pages are blocks, and the page cache is a rebuildable retrieval/blob projection (§9.4, §6.4; `version.explicit-rejections`, File 11 §23, `retrieval.explicit-rejections` (File 12 §21)).
- **Plaintext or app-encrypted web credentials, cookies, or tokens** — web credentials are vault-held `SecretRef`s with only redaction-safe metadata persisted; no credential value enters the durable substrate, the ledger, the model context, an export, or a sync stream (§17.2; `secret.backend-boundary`, File 22 §4, `security.secret-vault` (File 22 §5)).
- **Authority granted by web content** — an instruction inside a page, a search result, a fetched document, a feed item, or a familiar-named instruction file on the web holds no capability or policy authority; all web content is `untrusted_source_data` (§16; `security.untrusted-content`, File 22 §12).
- **Hidden auto-solving or auto-bypassing a bot-detection challenge, or spending to defeat one** — a captcha or equivalent is a handoff to the user by default; any challenge-assistance integration must be a separately declared, disabled-by-default, policy-governed capability requiring explicit user enablement and typed confirmation where risk demands it. The surface treats consent and cookie surfaces conservatively, respects a site's machine-access posture as a configurable default, and never spends to solve a challenge without explicit authorization (§16.4; `perception.capture-privacy`, File 19 §10.7).
- **A web autonomy, participation, interaction-shape, persona, or `WebMode` autonomy field** — at any layer, in any form; web autonomy is capability permission tiers, leases, and approval posture plus user direction, progressive disclosure is which panels and view preset are open, researcher/controller are view presets, and the periodic planning interval is a run structure, not a phase machine (§13.5, §14.2; `worksurface.no-autonomy-field`, File 25 §13). There is no planner-versus-navigator phase machine, no `Drive`/`Supervise`/`Collaborate`/`Delegate` dial, and no per-surface "research mode enabled" autonomy toggle.
- **A private browser process, sandbox, network path, or kill path** — all browsing runs through the one `Sandbox` contract and the `ManagedProcess`/`ProcessGroup` model under a web `SandboxProfile`; outbound access is egress-governed and redirect-revalidated; the surface extends the base contract only with its navigation and observation capability surface (§7, §13.4; `sandbox.explicit-rejections`, File 23 §20).
- **A fixed post-action delay as the page-readiness mechanism, or time-based monitoring as a correctness condition** — page readiness, document-change, and network observation are event-first; a change-monitor cadence is a flagged fallback only where a source emits no change events; the only permitted timer is a finite, configurable, killable wall-clock safety guard on a browser operation with no completion signal (§7.3, §8.3, §12.2; `perception.triggers`, File 19 §8, `world.explicit-rejections` (File 18 §16)).
- **A view preset that silently changes backend policy** — applying a web layout preset (researcher, controller, synthesis) changes presentation only and never silently changes model selection, context policy, execution entry, budget, sandbox profile, backend, or approval posture (§14.2; `worksurface.views-presets`, File 25 §7.2).
- **A private model-request assembly path or private model-selection logic** — every web model request assembles through the one `ContextAssemblyService` with web content marked untrusted, and the surface declares a default `ModelProfile` (including the vision route) without implementing selection (§13.2, §13.3; `context.consequences-for-later-specs`, File 13 §22, `model.consequences-for-later-specs` (File 16 §16)).
- **A url-only citation treated as captured evidence, or invented citations** — evidence-bearing use links to captured support content, and synthesized claims cite real captured sources or are excluded as unsupported (§6.5, §10.2, §10.4; `artifact.citation`, File 09 §12).
- **Exposing the host's absolute directory or browser-profile paths to the model by default, or materializing an unredacted secret or credential** — absolute host and profile paths are device-local sensitive data, model-facing content uses urls and workspace-relative paths, and no unredacted secret is written to a materialized, exported, or synced file (§17.4, §20.4; `secret.backend-boundary`, File 22 §4).
- **Naming a specific browser engine, search sidecar, challenge-handling implementation, fetch tier, content extractor, secret backend, or canvas renderer as the canonical semantics** — these are replaceable implementations behind the surface's capabilities and panels; the canonical contract is the behavior, never the library (Source Resolution; `core.local-extensibility`, File 01 §7.10).

## 23. Consequences for Later Specs

Anchor: `web.consequences-for-later-specs`

Later specs must follow these rules:

- The other **per-surface specs** (Data Processor, Teacher, GUI Control, System Agent) declare their own `SurfaceContract`s to File 25's shape, the same way this file does for Web; they may borrow the Web surface's search, fetch, and extraction capabilities (§18.2) but introduce no private web mechanism. The Web surface borrows their capabilities in place, never by silent surface change, and drives only the browser — desktop automation is the GUI Control surface's (§18.4).
- The **Automation and Triggers** spec owns the deep mechanics of the web change monitors this file frames as `Trigger`-rail entries (§12.2): scheduling, eligibility, enablement, change-detection cadence, and non-interactive-execution safety for a web monitor, confined to the narrowest web sandbox profile and pinning the Web surface and its policies at save time the way routing does; it introduces no parallel web execution path.
- The **Workflows, Templates, and Reuse** spec treats the web default workflows (§15.3), custom commands (§15.2), and recorded macros (§11.4) as reusable workflow and command definitions, and treats a successful research or browsing run as a promotable workflow; web workflow outputs that warrant durable identity become artifact versions through the canonical mechanism.
- The **Extension and Plugin System** and **MCP and External Integrations** specs may contribute web capabilities, search and fetch backends, content extractors, site adapters, browser backends, and research-tool connectors through the proposal-first registration and source-approval path; a plugin-contributed web capability or external search/browse backend participates in the one registry, policy layer, sandbox, egress governance, and ledger exactly as a built-in does, and a connector-supplied url is re-validated against the egress policy on every hop.
- The **UI Shell, Layout, Presentation, and Interaction Models** and **UI Customization, Widgets, and Theming** specs render the web panels, the browser viewport, the research canvas, the sources and reader panels, the activity feed, the command palette, the keybinding contexts, and the view presets over the data and behavior contracts this file fixes; presentation may vary freely, the work model cannot. The browser engine, the canvas renderer, the reader extractor, and the search backend are their implementation choices behind the panels and capabilities.
- The **Quality Control and Validation** spec registers web validators (citation-presence and citation-grounding checks, source-credibility checks, extraction-schema validation, and research completeness checks) producing `Validation`/`Critique`/`Observation` blocks and integrating through the completion-verification hook surface and the event and capability hooks, not a separate pipeline; it consumes the web evidence and citation discipline (§10).
- The **Telemetry, Logging, and Observability** spec consumes the web events and the per-call attribution this file and File 10 emit; it renders the web research and browsing inspector from the version graph, ledger, and observation handles, never by re-fetching a page or re-driving a browser for a historical view.
- The **Runtime Infrastructure and Lifecycle** spec orchestrates web surface, browser sandbox, session, and search-backend-sidecar startup and reconstruction around the storage lifecycle File 20 owns, reaping orphaned browser processes and sandboxes at restart rather than reconnecting (`process.killability`, File 23 §10.3) and rebuilding the page cache as a projection; it reimplements no web execution, capture, or indexing.
- The **Evaluation and Benchmarking** spec verifies the web round-trips — search-to-source-record, fetch-to-observation-with-fingerprint, extract-to-artifact, the act/observe/extract page interaction, citation-grounded synthesis, the research-session-as-version-tree-view, the change-monitor trigger, and the credential-handoff and untrusted-content defenses — replaying over recorded observations and immutable references, not a live page or browser, and verifying that no instruction in untrusted web content escalated authority and that no captured page or action replay re-queried a live source.
- The **Packaging, Platform, and Distribution** spec ships the built-in declarations for the canonical web capabilities, the Web `SurfaceContract`, the web `Custom` event and observation kinds, and the default web settings as the `Builtin` source in every install, and packages the browser engine, the search backend, challenge-detection and handoff implementations, the content extractors, and the browser extension behind their contracts, with the browser-automation capabilities desktop-only and search-and-fetch available in the mobile subset.

Specific integration contracts will be stated in those files when they are written.
