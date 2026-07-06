# Phase 0 — Process & Toolchain Bootstrap

## 1. Goal & why now

A repository that builds, tests, lints, and integrity-verifies an empty-but-compileable ATLAS3 shell
on Windows, macOS, and Linux on every commit — with every process guardrail from the
development-process invariants mechanized before any product code exists. The repo starts with no
implementation; building feature code before the command surface, CI, drift checks, and conformance
tracking exist would create manual debt every later phase inherits. No product behavior is implemented
here beyond the thinnest compileable shell.

## 2. Canonical scope & deferrals

- **File 43 — first-commit subset** (§3.2, §4.3, §5.2, §10.2): the build pipeline producing a
  per-target build artifact with **content-hash identity**; the **mandatory free update-signature
  scheme** (signing keypair generated, public key embedded, signature over content hash) proven
  against bare build artifacts; pinned-input `ReleaseProvenance` recording
  (reproducible-to-degree-toolchain-allows); the `BuiltinBundle` signed item-manifest *skeleton*
  (empty manifest, verification path wired); channel-as-build-configuration.
- The development-process invariants (`devproc.*` anchors) — this phase implements their machinery.
- Deferred: per-OS installable signed *bundles* → **P4** (M0's exit requires installing the signed
  bundle, so the obligation lands exactly where it is first needed); installers proper, platform
  integrations, update channels, crash handler → **P22**.

## 3. Prerequisites

None — first phase.

## 4. Lanes

Rust workspace scaffold, frontend scaffold, and the command/CI surface in parallel; the
conformance-matrix tooling and agent-instruction files land last because they reference the others.
The signing/provenance job is its own thin lane once the build job exists.

## 5. Build plan

1. **Repo scaffold** — Cargo workspace, **decided: one crate per major architectural layer,
   conservative granularity** — kernel/contracts, storage, ledger/events, settings, security/vault,
   capability registry, policy, execution/runs, context, providers, sandbox/process, substrate
   services, UI bridge, runtime/app shell — wired as a strict downward dependency DAG.
   kernel/contracts is the bottom shared-vocabulary crate (ID newtypes, canonical-encoding/hash
   traits, error envelopes, sensitivity labels, event envelopes, typed references): **kernel holds
   shapes, owning layers hold machinery** (the event-envelope type lives in kernel; the bus and
   stream live in ledger/events). Surfaces start as modules/registrations inside their owning
   layer; a layer is sub-split only when a real seam proves it (independent reuse, or
   compile-time/ownership pressure). The enforcement is the dependency graph — the compiler
   rejects illegal cross-layer dependencies. Tauri v2 shell crate; React+TypeScript frontend
   (pnpm) with the semantic-token base and i18n-key convention present from the first component;
   typed-IPC codegen (tauri-specta) wired but minimal; committed lockfiles + pinned toolchains.
2. **Zero-spend CI path** — **decided: GitHub Actions on the public repo** (`devproc.zero-spend`,
   invariants doc §27): free hosted minutes with all three OSes provided, zero infrastructure to
   maintain, lives where the code already is. On record: the free tier is tied to the repo staying
   public — going private inherits a monthly minute cap. CI must never depend on paid services or
   live-provider availability.
3. **One command surface** — **decided: `cargo xtask`** (decision-recorded: Rust-first project,
   tasks written in Rust behave identically on all three OSes — no cross-platform shell divergence,
   nothing extra to install) wired to `fmt`, `lint`, `test`, `docs`, `gen-check`,
   `banned-patterns`, `conformance-check` — with `typecheck` as an inner-loop-only leg (a fast local
   `cargo check` for development feedback; the `lint` leg's clippy `-D warnings` over `--all-targets`
   plus the full compile under `test` are the authoritative type-correctness gate, so `typecheck` is
   not a separate gate leg CI runs). CI calls the same entry points (CI/local parity).
4. **CI (GitHub Actions)** — 3-OS matrix from the first commit (compile + test + lint per OS);
   banned-pattern greps (invariants doc §28, `devproc.banned-patterns` — checks vacuous until code
   exists are registered as no-ops); gitleaks; cargo-deny (licenses + advisories); coverage capture with ratchet baseline;
   CI artifact upload for test logs / drift reports.
5. **Test harnesses wired** — cargo test + proptest; Vitest + RTL; Playwright with a single
   launch-and-screenshot smoke; deterministic-test scaffolding (injected-clock utility, drain/receipt
   helpers) as present-but-empty modules. Typed-error scaffolding (`AppError` family,
   `Result`-everywhere, no `unwrap`/`expect` in production paths) and the tracing scaffold
   (structured spans, redaction-by-default sink) — matured by P1/P2/P21.
6. **Build + integrity job** — tag-triggered: build per-target artifacts, compute content hashes,
   emit `ReleaseManifest` + `ReleaseProvenance` (pinned toolchain + lockfiles recorded). Signing
   with the update key is a local manual release step (custody policy, step 7). P0 proves the
   mechanism with a pre-signed golden fixture that CI verifies against the embedded public key; CI
   does not sign, and does not require access to the private key.
7. **Signing-key custody** — **decided policy**: P0 locks the signing scheme, embedded public key,
   verification path, and rotation contract. The private key remains offline; CI verifies only.
   Moving signing into CI later requires an explicit P4/P22 custody decision and threat review.
   The File 43 §5.2 key-rotation path (transition record signed by an already-trusted key)
   documented in-repo.
8. **Conformance-matrix tooling** — extracts every rule anchor from
   `documentation/specification/canonical/` and emits the traceability matrix (anchor → owning spec →
   module → test/evidence → phase → status); accepts not-yet-built anchors as explicit `planned`
   rows, never silent gaps; a CI check keeps the matrix structurally valid and in sync with the
   corpus.
9. **Generated-artifact registry** — one file listing each generator, inputs, outputs, and drift
   command; the drift check (`gen-check`) fails CI on stale artifacts. First entries: the
   agent-instruction projection, the IPC type bindings (when they appear).
10. **Agent instructions** — one source of truth projected to `AGENTS.md`/`CLAUDE.md` with a drift
    check; encodes the invariants doc, this phase plan, and the overview §6 cross-phase rules.
11. **Docs skeleton** — repo README, developer setup doc (commands, toolchain, run/test), docs index
    for the canonical corpus + this series, decision records (command surface = `cargo xtask`,
    CI = GitHub Actions on the public repo, signing-custody policy).

## 6. Test obligations & acceptance evidence

- CI itself is the test: one commit → green pipeline on windows/macos/ubuntu runners.
- **Guards demonstrably fire**: a deliberately introduced banned pattern (a raw color, an `unwrap` in
  a production path) fails the grep harness, and removing it passes; a deliberately stale generated
  artifact fails `gen-check`; a known-bad license fixture fails cargo-deny (run once, then removed).
- **Integrity golden**: a pre-signed golden fixture (signed locally) verifies against the embedded
  public key in CI; a tampered artifact fails verification. A local signing drill signs a sample
  content hash and verifies it locally. The private key never enters CI.
- Conformance matrix: structurally valid; all anchors present as `planned`; the matrix-sync check is
  able to fail on a missing anchor.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: agent-instruction projection (drift-checked); conformance-matrix scaffold;
  the generated-artifact registry itself.
- **Docs**: README; developer setup; decision records (command surface, CI path, signing custody);
  conformance-matrix usage doc; key-custody/rotation doc.
- **CI/local commands**: `fmt`, `lint`, `test`, `docs`, `gen-check`, `banned-patterns`,
  `conformance-check`, `build-artifact`, `verify-signature`; `typecheck` as an inner-loop-only local
  leg (not a CI gate — clippy `-D warnings` over `--all-targets` and `test`'s compile are the
  authoritative type check).

## 8. Exit criteria

- [ ] One documented local command gives a new contributor/agent a meaningful green result; CI runs
      the same checks on all 3 OSes.
- [ ] Tag → content-hashed build artifact per target; `ReleaseProvenance` records pinned inputs.
      CI verifies the pre-signed golden fixture against the embedded public key; a local offline
      signing drill signs and verifies a sample content hash. The per-platform installer-size budget
      check is wired (seed value in the initial development profile — invariants doc §27;
      settings-tunable per File 43 §15 — asserted once bundles exist in P4).
- [ ] Banned-pattern, gitleaks, cargo-deny, coverage-ratchet, gen-check, and matrix-sync jobs all
      active and demonstrably able to fail.
- [ ] Agent-instruction drift check green; later phases have a stable directory + naming convention.

## 9. Locked in this phase

- **Update-signing scheme + embedded public key + verification path + rotation contract** (43 §5.2)
  — the v1 integrity root; a wrong rotation design strands clients forever. Private-key custody is
  deliberately *not* frozen here: offline at P0 (CI verifies only), revisited by an explicit
  P4/P22 custody decision + threat review (build plan step 7).
- **Content-hash artifact identity across channels/mirrors** (43 §3.2).
- **Channel-as-build-configuration** (43 §4.3) — feature-flag arrays, not forks.
- Workspace/crate layout — one crate per major architectural layer, kernel/contracts as the bottom
  shared-vocabulary crate, strict downward DAG; the command surface (`cargo xtask`); CI job names.
- **Core first run is offline-capable** (43 §6.2) — nothing in the build may assume a live
  distribution host at first launch.
