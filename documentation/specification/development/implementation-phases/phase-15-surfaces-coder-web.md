# Phase 15 — Surfaces Wave 1: Coder & Web (M3)

## 1. Goal & why now

The first two real work surfaces fill the P11 contract: **Coder** (the code-as-artifact engineering
environment — its confined code-execution capability is the most-borrowed export in the system) and
**Web** (the persistent-web-layer — its search/fetch/extract capabilities are the second-most-
borrowed). Wave order is dictated by the borrow graph: Teacher (P16) hard-depends on Coder's
execution and on Web/Data extraction. Coder is the best first surface — it exercises workspaces,
artifacts, versions, sandboxed processes, retrieval, validation, rails, and UI under real development
pressure, proving the substrate. Milestone **M3**: ATLAS3 is genuinely useful for real work.

## 2. Canonical scope & deferrals

- **File 27 — complete core**: the Coder `SurfaceContract` (`surface_id: coder`); **the code-editing
  contract** — read/create/edit/patch producing `FileAttachment`/`CodePatch` artifact revisions with
  read-before-edit staleness + atomic materialization; every edit format yields the same
  artifact-revision outcome, typed errors on ambiguity (§6); the codebase model +
  `ingested_codebase:` indexing — structural extraction event-first/incremental, expensive
  extraction on demand, file/symbol/import/call relations (§7); file-history-as-version-projection +
  revert-as-version-switch (§8); the `git.*` family as shared built-ins + git-safety policy —
  `git.push` approval-gated unconditionally; force-push-to-protected = `Denied` + typed-confirmation
  (§9); **confined code-execution + shell + terminals** over the P8 sandbox capability —
  pty `ManagedProcess`es (§10); tests/build/lint as `Validation` blocks + the completion floor (§11);
  review/critique flows (§12); multi-agent over worktrees (§13, over 04 §16 + 24 §15);
  panels/presets/keybindings/commands (§14–§16); session export as `.atlas/logs/` projections (§17);
  world entities + sensor registrations (Repository/Terminal richer contracts) (§19); coder events
  (§21). Semantic operations degrade to raw-file fallback where language intelligence is absent
  (§6.4); debugging/tracing adapter-gated (§5.2); forge/PR connectors → **P18**.
- **File 28 — complete core**: the Web `SurfaceContract` (`surface_id: web`); **the
  fetch–search–extract contract** — `web.search`/`web.fetch`/`web.extract_document` producing
  durable Observations with `StalenessFingerprint`s + Citations + `SourceExcerpt`s, indexed into
  `web_cache:` — explicitly functional without a browser backend (§5–§6); browser sessions over a
  sandboxed `ManagedProcess` + the `BrowserPage` sensor — Managed backend default; External backend
  later/opt-in with reduced isolation + stronger posture (§7); structured-first page representation
  (frame identity/origin preserved) + act/observe/extract (§8); research sessions — quick/standard
  strategies, deep = child-run workflow — as version-tree views (§9); **citation-grounded
  synthesis** — every factual claim cites a captured source, invented URLs invalid (§10); downloads
  + the `Macro` artifact shape (§11); page monitors as Automations over P14 (§12); credential
  handoff + challenge detection — assistance integrations disabled-by-default (§6.3, §16.4);
  **untrusted-content + exfiltration-via-redirect defenses live end-to-end** (§16); secret-filled
  form masking (§17); web events (§21). Vision-grounded interaction availability-gated on a vision
  model.
- **File 19 — additive sensors**: `BrowserPage`; richer `Repository`/`Terminal` capture contracts.

## 3. Prerequisites

P8 (sandbox/exec/chokepoint), P9 (artifacts/workspaces/worktrees), P10 (retrieval/world/perception),
P11 (contract + rails), P12 (shell/panels), P13 (validator machinery — both surfaces register
theirs), P14 (monitors alias the Scheduler).

## 4. Lanes

Coder and Web are **mutually independent parallel lanes** (no surface depends on another surface —
the widest lane in the plan). Within Coder: edit contract → exec/terminals → index → git +
worktrees → review. Within Web: fetch/search/extract → browser sessions → research/synthesis →
monitors. Surface validators + eval suites are thin closing lanes in each.

## 5. Build plan

1. **Coder edit slice**: the editing contract; staleness (`FileChangedSinceRead`); atomic streamed
   writes; revert-as-version-switch; patch preview/accept/reject/modify.
2. **Coder exec slice**: the P8 confined shell/exec capability surfaced; terminals as pty
   ManagedProcesses; tests/build/lint committing Validation blocks — the completion floor now bites
   on real engineering runs ("a coder run whose contract required action cannot complete on prose").
3. **Coder index slice**: event-first structural extraction; symbol/dependency/build-test graphs
   into File 12; code search; extraction-identity cache keying.
4. **Coder collaboration slice**: the git family + safety rules (the P5 seed rules go live);
   worktree-backed parallel child runs + merge + the comparison board projection.
5. **Web fetch slice**: search/fetch/extract with durable source records, fingerprints, citations;
   the `web_cache:` namespace; egress governance on every fetch; pluggable search backend.
6. **Web browser slice**: the Managed browser backend as a sandboxed process; `BrowserPage`
   structured capture; navigation/interaction with per-hop redirect re-validation; page-state cache
   invalidated event-first.
7. **Web research slice**: research sessions as version-tree views; citation-grounded synthesis with
   the grounding validators registered into 39 (citation-presence/grounding/source-credibility);
   monitors as Automations.
8. **Surface registrations**: both `SurfaceContract`s through the P11 validator; SubsystemSurfaceSpecs;
   keybinding contexts + slash commands; coder/web validators into 39; Coding + Research eval suites
   seeded into 40 from recorded runs.

## 6. Test obligations & acceptance evidence

- **No-private-architecture conformance** (both surfaces, the central family): pass the P11
  validator; no private index/history/browser-state/citation stores; history is the version graph;
  grep + validator.
- 27 — the conformance round-trips (§23), **replayed over recorded snapshots, never live disk or
  process state**: edit→artifact-revision→materialization→external-edit→version; code-search
  retrieval; test-and-validation gate; revert-as-version-switch; worktree multi-agent merge; session
  export. Plus: the edit-format harness (same outcome across formats, typed ambiguity — §6.3);
  kill-during-write leaves no partial (§6.6); concurrent-edit staleness (§6.5); **`git.push` held
  behind approval even under `agent.unrestricted_mode`**; force-push-protected carries the
  `Denied`-floor typed-confirmation (§9.3); terminal kill/reap; no unredacted secret in
  materialized/exported files (§22); no absolute host paths to the model by default.
- 28 — the conformance round-trips (§23), **replayed over recorded observations, never a live page
  or browser**: search→source-record; fetch→observation-with-fingerprint; extract→artifact;
  act/observe/extract; citation-grounded synthesis; research-session-as-version-tree; change-monitor
  trigger; credential handoff. Plus: **no instruction in untrusted web content escalates
  authority** — `browser.evaluate`/page-script results are `untrusted_source_data` regardless of
  script author (§16.2); **exfiltration-via-redirect** — an initially-allowed destination cannot
  redirect to a forbidden one, re-validated per hop (§16.3); page-change staleness →
  `StateChangedSinceObservation` (§8.3); **invented URLs are invalid extraction output** (§7.4);
  macro/historical replay never dispatches live browser actions (§11.4); secret-filled form values
  masked in feed/ledger/export/context (§17.4); `web.fetch` ConcurrencySafe parallel batches (§6.3).
- **Cross-surface borrow proven under policy**: a Coder run borrows `web.fetch` through
  `tool.borrow` — same declaration, same policy, same ledger (the P6 discovery capabilities
  exercised for real).
- **Closed-set pinning**: both surfaces' panel/selection/produced-kind sets; the coder event names;
  the web `ArtifactKind`s (BrowserExtract/WebDocument/ScreenshotSeries/Macro) + `ObservationKind`s
  (BrowserDom/NetworkResponseSnapshot/Screenshot).
- Conformance matrix gains: 27/28 anchors; Coding + Research eval families seeded.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: both surface contracts as registered declarations; shared types for the
  produced kinds; the extraction-identity and action-cache key schemas; recorded browser/page
  fixtures for deterministic web tests.
- **Docs**: coder surface doc (the code-as-artifact reframe + the edit contract); web surface doc
  (the persistent-web-layer reframe + the grounding rules); the borrow-graph note (what each surface
  exports/borrows); decision records: first search backend, Managed-browser realization.
- **CI/local commands**: the coder round-trip suite, web round-trip suite, git-safety suite,
  redirect/untrusted-content suite, and borrow-path suite as named CI jobs — all over recorded
  fixtures.

## 8. Exit criteria

- [ ] **M3-Coder**: a real multi-file refactor — plan, edit, run tests, fail, fix, validate,
      commit — performed end-to-end in the app; replayed from records in CI.
- [ ] **M3-Web**: a real research question — search, fetch, extract, synthesize with citations —
      every claim traceable to a captured source; replayed from records in CI.
- [ ] Both contracts pass the P11 conformance harness; cross-surface borrow green.
- [ ] M0–M2 still green.

## 9. Locked in this phase

- **Coder/Web produced-kind registrations**: coder event names + the index cache-key shape + the
  `ingested_codebase:` namespace; the web kinds + the `web_cache:` namespace + the action-cache key
  shape.
- **The `Macro` artifact shape** (shared with GUI Control + System Agent in P17 — capability-level
  steps, selectors, parameter slots, secret refs).
- `surface.coder.*`/`surface.web.*` settings namespaces; `ATLAS.coder.md`/`ATLAS.web.md` qualifiers;
  selection kinds; the structured-page wire shape (frame identity/origin preserved).
- The browser-backend enum Managed/External + External's reduced-isolation posture (§7.2).
