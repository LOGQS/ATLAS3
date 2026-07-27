# ATLAS3 Implementation Phases — Overview

## Status

Authoritative implementation-phase series: this overview, `phase-00` … `phase-23`, and the
`99-edge-audit.md` verification companion. The canonical specifications (Files 01–43) define **what**
ATLAS3 is; `../development-process-invariants.md` defines **how** it is built (commits, testing
discipline, CI, agent workflow); this series defines **what gets built when** — the dependency-ordered
build plan, one file per phase.

Phase specs turn canonical contracts into implementation order, slices, lanes, gates, and evidence —
they do not restate the product specs. Read the owning canonical file before implementing a slice; the
phase file names what to build and how to prove it, not what the primitive means.

## 1. Design principles of this ordering

1. **Retrofit-risk first.** The most expensive things to change after dependent code exists are built
   and frozen earliest: `CanonicalEncoding` + canonical hashes (File 01), the storage three-plane split
   + locality partition (20), the ledger/block/version schemas + the three forgery guards (10/08/11),
   the secret-boundary chokepoints (22 §4), the filesystem chokepoint + managed-process model (23).
   Every phase carries a "Locked in this phase" list.
2. **Walking skeleton early, alive forever.** P4 produces a booting, installable app with one durable
   round trip (**M0**); P6 closes the full governed loop against a mock model (**M1** — the design
   de-risking milestone). From P4 onward, **every phase exits with the app booting and the 3-OS CI matrix green** — no
   phase leaves the system non-functional.
3. **Spec-stated stub points, honored contracts.** The canon documents exactly where stubs are legal
   (policy returning recorded permissive decisions, all-Primary tool surface, in-memory leases, large
   context budget, mock `ModelStep`). Stubs sit *behind the canonical contract shape* — field sets,
   enums, and reference forms are real from day one even when the implementation behind them is a
   stub. Stub internals, never stub schemas. Every stub names the phase that matures it (§5).
4. **Build order ≠ spec order.** The sequence is the dependency-and-testability order, not file
   numbering.
5. **Each phase is independently gated.** Exit criteria are checkable (spec-mandated test obligations),
   not vibes. Tests land in the same phase as the code they verify; the conformance matrix grows
   monotonically and never regresses.
6. **Boot graph as spine.** File 42 §11.3's 15-step boot graph is the single runtime ordering
   authority; the phase order tracks it (storage → projections → bus → services → registration →
   settings → vault → warmers → workers → recovery → bridge).
7. **Lanes inside phases.** A phase is a merge-order unit, not a serialization of all its work: each
   phase file names its parallelizable lanes (isolated git worktrees, one writer per lane, review at
   the merge boundary). The trunk P0→P6 is strictly serial; from P7 onward lanes within and across
   adjacent phases may overlap wherever the named prerequisites of the specific lane are already
   merged.

## 2. Phase sequence

| # | Phase | Canonical scope | The system can now… |
|---|-------|-----------------|---------------------|
| P0 | [Process & toolchain bootstrap](phase-00-process-and-toolchain-bootstrap.md) | 43 (first-commit subset) | build, test, and hash/signature-verify on 3 OSes from one command surface |
| P1 | [Kernel contracts](phase-01-kernel-contracts.md) | 01 | encode/hash/identify anything, deterministically, forever |
| P2 | [Storage substrate](phase-02-storage-substrate.md) | 20; 22 (boundary forms) | persist durably with rebuild/recovery equivalence proven |
| P3 | [Data spine](phase-03-data-spine.md) | 10, 08, 11 | record immutable history that cannot be forged |
| P4 | [Runtime skeleton & settings](phase-04-runtime-skeleton-and-settings.md) | 15, 42 (core); 37 (thin IPC) | boot, configure, round-trip UI→service→SQLite→UI, install signed (**M0**) |
| P5 | [Capability & policy kernel](phase-05-capability-and-policy-kernel.md) | 05, 06, 02 | declare operations and gate them through one policy layer |
| P6 | [Routing, run & context](phase-06-routing-run-and-context.md) | 03, 04, 13 (read), 07 | route a message into a governed, ledgered, completable run (**M1**) |
| P7 | [Providers, models & vault](phase-07-providers-models-and-vault.md) | 17, 16, 22 (vault), 13 (full) | hold a real model conversation with real credentials (**M2**) |
| P8 | [Sandbox & security completion](phase-08-sandbox-and-security-completion.md) | 23, 22 (complete) | spawn, confine, and kill processes; trust and egress enforced |
| P9 | [Entities & workspaces](phase-09-entities-and-workspaces.md) | 09, 24 | produce durable artifacts/evidence and mirror them to disk |
| P10 | [Substrate services](phase-10-substrate-services.md) | 18, 19, 12, 14 | see the world, sense change, search everything, remember |
| P11 | [Surface contract & rails](phase-11-surface-contract-and-rails.md) | 25, 26 | register surfaces; invoke anything via one resolution path |
| P12 | [UI shell](phase-12-ui-shell.md) | 37 (full) | render the whole substrate, accessibly, as pure projection |
| P13 | [Quality machinery](phase-13-quality-machinery.md) | 39; 40 (minimal) | validate inline and replay-score recorded runs |
| P14 | [Automation & workflows](phase-14-automation-and-workflows.md) | 33, 34; 42 (workers) | crystallize and schedule work safely, unattended |
| P15 | [Surfaces: Coder & Web](phase-15-surfaces-coder-web.md) | 27, 28 | do real engineering and real web research (**M3**) |
| P16 | [Surfaces: Data & Teacher](phase-16-surfaces-data-teacher.md) | 29, 30 | process data and teach, over borrowed capabilities |
| P17 | [Surfaces: GUI & System](phase-17-surfaces-gui-system.md) | 31, 32; 23 §11; 19 (desktop/system sensors) | control the desktop and operate the OS, safely |
| P18 | [Extensions & integrations](phase-18-extensions-and-integrations.md) | 35, 36 | install plugins and connect MCP/external services |
| P19 | [UI customization](phase-19-ui-customization.md) | 38 | theme, lay out, and widget-ize the shell |
| P20 | [Sync & portability](phase-20-sync-and-portability.md) | 21 | export/import losslessly; sync across devices, no LWW |
| P21 | [Evaluation & observability](phase-21-evaluation-and-observability.md) | 40 (full), 41; 42 §16 | benchmark, regress-test, and observe everything |
| P22 | [Packaging & distribution](phase-22-packaging-and-distribution.md) | 43 (full); 42 §18 | update itself safely; integrate with each platform |
| P23 | [Conformance closure & 1.0](phase-23-conformance-closure.md) | cross-cutting | prove the whole canon holds (**M4 / 1.0**) |

**Milestones:** **M0** first light — installable signed app, durable round trip (P4). **M1** loop
closed — full governed run loop vs mock model; the design-risk retirement gate (P6). **M2** real
conversation (P7). **M3** first surfaces genuinely useful (P15). **M4** 1.0 (P23).

## 3. Phase dependency graph

```
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → P9 → P10 → P11 → P12 → P13 → P14 → P15 → P16 → P17
                                                                              ├──────→ P18 → P19
                                                                              ├──────→ P20
                                                                              └──────→ P21 → P22 → P23
```

The trunk P0–P17 is the merge order. Genuine lane overlaps (verified in `99-edge-audit.md`): P8's
sandbox-core lane may start in parallel with P7 (its hard prerequisites are P5/P6; only the
trust/egress lane waits on P7's vault); P13 may run in parallel with P11/P12 (its prerequisites are
P6/P9); P18 needs P14 (webhook trigger target) + P8; P19's built-in slice needs only P12 (plugin
placement waits for P18); P20 needs P9 (+P8 egress); P21 needs P13 + P14 (+ surface corpus for
breadth) and consumes P20's sink-credential patterns by reference — a soft edge, not a hard
prerequisite, so P20 and P21 may overlap. P22 needs P18 + P19 + P21 outputs. P23 closes everything.

## 4. Coverage matrix (every canonical file → phase(s))

| File | Phase(s) | File | Phase(s) | File | Phase(s) |
|------|----------|------|----------|------|----------|
| 01 | P1 | 16 | P7 | 31 | P17 |
| 02 | P5 | 17 | P7 | 32 | P17 |
| 03 | P6 | 18 | P10 | 33 | P14 |
| 04 | P6 (+P8 §15) (+P9 §16) | 19 | P10 (+P15/P17 sensors) | 34 | P14 |
| 05 | P5 | 20 | P2 | 35 | P18 |
| 06 | P5 (+P18 source-approval full) | 21 | P20 | 36 | P18 |
| 07 | P6 | 22 | P2 (boundary) / P7 (vault) / P8 (trust+egress) | 37 | P4 (thin IPC) / P12 (full) |
| 08 | P3 | 23 | P8 (+P17 elevated helper) | 38 | P19 |
| 09 | P9 | 24 | P9 (+P20 export/import) | 39 | P13 |
| 10 | P3 | 25 | P11 | 40 | P13 (min) / P21 (full) |
| 11 | P3 | 26 | P11 | 41 | P21 (baseline logging in P4 via 42) |
| 12 | P10 | 27 | P15 | 42 | P4 (core) / P14 (workers) / P21 (§16) / P22 (§18) |
| 13 | P6 (read) / P7 (full) | 28 | P15 | 43 | P0 (first-commit set) / P22 (full) |
| 14 | P10 (+P14 implicit learning) | 29 | P16 | | |
| 15 | P4 | 30 | P16 | | |

No file is orphaned. Where a file is split, each phase file states which sections land there and where
the rest goes.

## 5. Maturation chains (every stub names its closing phase)

The established pattern: an early phase lands a contract with a stub behind it; a later phase matures
the implementation behind the unchanged seam. A stub's conformance rows are marked partial until its
closing phase; nothing is reported complete prematurely.

| Stub / seed (phase) | Matured by | Seam |
|---|---|---|
| Hash/signature scheme proven on bare artifacts (P0) | P4 installers; P22 full pipeline | content-hash + embedded-key verification |
| `BuiltinBundle` item-manifest skeleton (P0) | P22 finalized bundle | signed item manifest |
| Secret-boundary forms + detector skeleton (P2) | P7 vault internals; P8 trust/egress | `SecretRef`/`vault:<key>`/`SecretValue`, `resolve_for_use` |
| Forgery-guard engine vs contract *type* (P3) | P6 full completion-contract integration | ledger commit boundary |
| Snapshot-reference resolvers (P3) | P7 settings/pricing; P10 world/registry | `Snapshot` catalogue, resolution contract |
| Replay contract + `Inspect` data (P3) | P13 Inspect engine; P21 Simulate/FullRerun | File 10 §11 replay semantics |
| Thin IPC window + raw transcript (P4) | P12 full shell | typed IPC + `context_view` projection |
| Logging/tracing baseline (P4) | P21 full observability | boot step 3, redacting sink |
| Headless approval harness (P5) | P12 dialog rendering | 06 §13 approval data contract (verbatim) |
| Source-approval typed shapes (P5) | P18 full flow | `SourceRegistrationProposal` |
| Availability predicates always-true (P5) | P10 world-model evaluator | 05 §15.2 evaluator delegation |
| Mock `ModelStep` + recorded fixtures (P6) | P7 real `ProviderAdapter` | `capability.backend-descriptor` seam |
| Conservative token estimator (P6) | P7 provider-keyed counting tiers | 13 §10 counting contract |
| Auto-shrink registered as no-op (P6) | P7 real budgets | 07 §8 behind its setting |
| Discovery-capability ids registered (P6) | P18 `mcp.search` mechanics | 07 §7 Builtin declarations |
| Derived lifecycle/state evaluators trivial (P3/P6) | P9 entity-layer derivations | 09 §5/§9/§14 derivation rules |
| World-snapshot refs recorded, unresolvable (P6) | P10 world model | `world_snapshot_id` |
| In-process cooperative cancellation only (P6) | P8 forceful kill over processes | 04 §17.3 / 23 §10 |
| Trigger-rail + external-protocol framing (P11) | P14 scheduler; P18 transports | 26 §11/§12 |
| Voice rail availability-gated off (P11) | P17 audio sensor + consent | 26 §9 |
| Elevated helper absent (P8) | P17 install-on-first-privileged-use | 23 §11 |
| Sensors: FileSystem/Env/Repo/Process (P10) | P15 BrowserPage; P17 desktop/system | additive sensor registrations |
| Device-trust shapes (P8) | P20 pairing | 22 §10 |
| Settings locality declared (P4) | P20 enforcement | 15 §18 / 21 §5 |
| Workspace export/import deferred (P9) | P20 `PortablePackage` | 24 §16 |
| Eval families seeded per producer (P13+) | P21 full family set + gates | 40 §8.2 |
| 42 §16 health orchestration absent (P14 builds the watchdog + §6.5 supervision) | P21 route-around/degrade/surface | 41↔42 observe/operate seam |
| Update relaunch absent (P4 runtime) | P22 staged-update handoff | 42 §18 / 43 §11 |

## 6. Cross-phase rules (binding for every phase)

1. **No filesystem-mutating capability before P8.** The File 23 §7.2 chokepoint must be THE single
   path for Atlas file access; building file-touching capabilities against raw OS I/O and retrofitting
   the chokepoint is spec-forbidden. (The P2 StorageEngine's own data-root I/O is the controlled
   exception — trusted infrastructure beneath the sandbox, not capability-mediated access. Clean
   boundary, no tension.)
2. **Secret-boundary forms from P2 onward.** `SecretRef`/`vault:<key>`/`SecretValue` reference forms,
   the redacting formatter, and forbidden-destination rejection at persist/transmit chokepoints exist
   before any sink does — vault *internals* arrive in P7 (22 §4.3: structural enforcement, "not
   per-call-site discipline").
3. **Execution-metadata fields are designed in P5, consumed in P6.** File 04 §8.2.2's required
   capability fields (`concurrency`, `reversibility_class`, `idempotent`, `preview_mode`,
   `partial_output_meaningful`, `cooperative_stop_deadline_ms`, `sibling_abort_on_failure`,
   `resume_on_restart`) are schematized in the File 05 declaration up front — the documented break of
   the 04↔07 chicken-and-egg cluster. Likewise the typed `capability_class` lands in P5's declaration
   before policy resolves on it.
4. **Closed enums freeze at first durable write.** Any closed-canonical enum (01 §6.16) that reaches
   the substrate is locked; widening afterward is a spec revision + migration. Each phase's "Locked"
   list is reviewed before the phase exits, and every closed set carries a **closed-set pinning test**.
5. **CI never calls a live provider.** Model-dependent tests run over recorded provider
   snapshots/fixtures (17 §17.8, 40 §4.3). Live-model smoke tests are local, manual, opt-in.
6. **Sensors, validators, suites, renderers register additively.** Perception sensors (19), QC
   validators (39), eval suites (40), and renderers (37) are registrations over substrates built once —
   later phases add registrations, never new substrates.
7. **Every phase exits with:** all prior exit criteria still green (no regression), the app booting on
   3 OSes, the conformance matrix updated with the phase's anchors (stubs marked partial with their
   closing phase), and docs current per the invariants doc's same-commit rule. Phase exit is 3-OS
   mandatory: the phase does not close until the full CI matrix is green on Windows, macOS, and Linux.
   A slice inside a phase exits on local-parity green; the 3-OS dispatch is batched at phase,
   dependency, and filesystem/keyring/crypto boundaries and is mandatory on any platform-behavioral
   change (`devproc.ci-local-parity`, invariants §12). A phase may exit with a named partial-completion tail
   only when every tail names the phase or task that closes it, is not a prerequisite of any lane
   proceeding from this phase, and is enumerated as an explicit exception in the phase's exit
   criteria; otherwise the phase's work is complete at exit.
8. **No time-based correctness anywhere, including tests** — drain/receipt synchronization and
   injected clocks per the invariants doc; flagged-timer exceptions only where the canon itself flags
   them (wall-clock safety guard 23 §9.3, missed-heartbeat watchdog 42 §6.4, resource-gauge sampling
   41 §8.5, metric-sampling watches 32 §12.2, rate-limit reset anchoring 17 §13.7).
9. **Frontend discipline from the first component.** Semantic tokens only (no raw colors/radii/fonts),
   i18n keys only (no hardcoded user-facing strings), no durable/consequential state in browser
   storage — the banned-pattern greps for all three are active from P0 even while vacuous.
10. **Superseded vocabulary is banned vocabulary.** When a canonical file supersedes legacy names
    (checkpoints, `MessageVersion`, goose mode, YOLO classifier, audit log, tool list, …), the owning
    phase adds them to the banned-vocabulary grep so they cannot reappear in code or schema.

## 7. Per-phase template

Every phase file uses the same nine sections:

1. **Goal & why now** — what exists at the end that didn't before, and why this position in the order.
2. **Canonical scope & deferrals** — owning files + anchor-level scope; every deferral names its
   destination phase.
3. **Prerequisites** — phases + the specific contracts consumed.
4. **Lanes** — parallelizable work within the phase (worktree-isolated, one writer per lane) and any
   cross-phase overlap permitted.
5. **Build plan** — ordered work items with internal staging and the stub contracts to honor.
6. **Test obligations & acceptance evidence** — spec-cited; named test families; what the conformance
   matrix gains.
7. **Artifacts, docs & CI surface** — generated artifacts + drift checks, documentation deliverables
   (module docs, decision records, glossary/banned-vocabulary updates), CI/local command additions.
8. **Exit criteria** — the checkable gate.
9. **Locked in this phase** — the retrofit-risk decisions frozen here.
