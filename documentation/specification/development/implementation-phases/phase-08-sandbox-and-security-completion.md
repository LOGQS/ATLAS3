# Phase 8 — Sandbox, Process Control & Security Completion

## 1. Goal & why now

The execution-containment substrate and the rest of the data-plane security layer: one `Sandbox`
contract owning all process spawning and killability, the filesystem service-trait chokepoint as THE
single path for capability-mediated file access, network/resource enforcement, and File 22's trust
model, egress governance, and injection defense. Killability becomes real here: the run model defined
cancellation cooperatively, but with the mock/provider loop there were no arbitrary OS processes to
kill. After this phase — and only after it — capabilities may touch the filesystem or spawn
processes. This unblocks workspaces (P9), real parallelism keying (04 §15), and every surface.

## 2. Canonical scope & deferrals

- **File 23 — core**: the `Sandbox` contract + `SandboxSpec` + per-consumer `SandboxProfile` (the
  shell/code-exec/preview/custom-tool sandboxes are profiles of one contract) + the `SandboxRegistry`
  — an unavailable tier is typed `SandboxUnavailable`, never a silent downgrade (§3); the closed
  `IsolationTier` ordinal + trust-to-strictness mapping — `None`/`OsConfined` realized now,
  `RuntimeConfined`/`Virtualized` registered-as-unavailable until built; presentational separation is
  not a tier (§4); the `ManagedProcess` model — explicit program + argv (never a shell-interpreted
  string from agent fragments), the `EnvPolicy` allowlist excluding path/linker/interpreter/
  secret-bearing vars, interpreter-payload inspection before spawn, pty mode (§5); `ProcessGroup`
  categorical ownership (§6); the **filesystem boundary** — the service-trait chokepoint
  (canonicalize → contain → deny-overlay, symlink-resolved-before-check, canonical real path as
  mutation identity, deny overlay unconditional even under `Unrestricted`) plus OS-level confinement
  of spawned processes (§7); the **network boundary** — app-layer egress-destination check + OS-level
  confinement where the platform supports it, per-hop redirect re-validation, `LoopbackOnly` for
  sidecars, no-network the confined default (§8); `ResourceLimits` as event-driven thresholds —
  output-byte cap kills as output accumulates; **the wall-clock guard is the sole time dimension**, a
  finite/configurable/killable safety guard, never a correctness condition (§9); **killability** —
  cooperative → forceful → reap; killing a sandbox kills its `ProcessGroup` + descendants; `KillFailed`
  typed, never silent success; orphans reaped at restart, not reconnected (§10); subprocess wrappers +
  per-instance home isolation (§12, unblocks 17 §6.2); declared-vs-observed enforcement + the typed
  violation set (§13); transient handles + snapshot shapes (§14 — Observation commits complete in P9);
  cross-platform realization behind the contract, first realization per platform with typed gaps
  (§15). **The elevated helper (§11) → P17** (lazily installed; System Agent is its consumer).
- **File 22 — completion**: the trust model — six closed classes, `source_trust_evidence` vs
  `user_trust_override` vs computed `effective_trust`, `SourceIntegrityRecord` over CanonicalEncoding
  + tamper downgrade, capability-manifest review shapes (§9); device-trust shapes (§10 — pairing
  realized in P20); **egress governance** — tier semantics, the `Denied`-floor + typed-confirmation
  gate for credential/secret export, the narrowing-only destination inspector,
  redaction-before-egress (§11); **untrusted-content injection defense** — the structural
  no-authority rule composed with 13's authority classes + sanitization + destination re-validation
  (§12); local posture — process/IPC trust boundary, CSP, input validation (§13); security-settings
  safety-direction classification (§17).
- **File 04 — §15 completion**: filesystem mutation keyed by the canonical real path via the 23
  chokepoint; alias spellings share one mutation identity.

## 3. Prerequisites

Hard: P5/P6 (policy gates spawn/escalation; the pipeline containment enforces; cancellation contract
to enforce over processes). P7 for the trust/egress lane (vault for spawn-time credential rules,
`resolve_for_use` at point of use). The **sandbox-core lane may start in parallel with P7** — its
prerequisites are P5/P6 only.

## 4. Lanes

(a) Sandbox core — contract + tiers + registry, ManagedProcess + groups + kill, filesystem +
network enforcement, resource limits (can overlap P7); (b) trust model + integrity records;
(c) egress governance + injection defense (joins after the vault). The first sandboxed capability
(confined shell/code-exec) is the integration lane at the end.

## 5. Build plan

1. **Filesystem chokepoint first** (23 §7.2–7.3): the service trait all capability-mediated file
   access flows through — "impossible to reach the OS file interface without passing the check."
   Wire 04 §15.2 mutation keying through it immediately. (The P2 StorageEngine remains trusted
   infrastructure beneath the sandbox — clean boundary.)
2. **ManagedProcess/ProcessGroup**: explicit program+argv; env allowlist; platform-native grouping
   (job objects / process groups); every spawn tracked from the first one — an untracked process is
   an unkillable process.
3. **Killability**: shared cancellation signal → cooperative deadline → forceful → reap; integrated
   with the P4 global token and 04 §17.3; reap-at-restart joins boot step 13.
4. **OsConfined tier per platform**: 3-OS realizations behind the contract (kernel confinement /
   sandbox profile / restricted-token+job-object); unenforceable scopes recorded as typed gaps,
   caught at the app layer, never silently treated as enforced.
5. **Resource limits**: output-byte cap; memory/CPU where the platform allows; gaps typed.
6. **Network enforcement**: app-layer destination check consuming 22's egress policy; per-hop
   redirect re-validation; DNS part of policy; OS-level confinement where available.
7. **Trust + egress + injection (22)**: trust-class computation + integrity records (consumed by
   P18's source approval); the egress gate at every existing egress point; `untrusted_source_data`
   enforced end-to-end (13 authority → 04 results → no instruction authority); sanitization strips
   tag-channel carriers and records it.
8. **Subprocess wrappers + home isolation** (23 §12): the 17 §6.2 wrapper lifecycle lands.
9. **First real sandboxed capability**: a confined shell/code-exec capability (becomes Coder's core
   in P15) as the integration proof.

## 6. Test obligations & acceptance evidence

The two mandatory canonical suites, in full:

- **File 23 §21 suite**: filesystem boundary — no path escapes, including via symlink
  (resolved-before-check) and alias spellings (one canonical mutation identity); TOCTOU closed where
  the platform supports it, residual windows declared; deny overlay holds under `Unrestricted`;
  network boundary — no destination outside policy, including via redirect (per-hop) and DNS;
  sidecars `LoopbackOnly`; resource limits — a runaway process is bounded and killed event-driven
  (deterministic fault injection, not timing); **killability** — categorical (sandbox → group →
  descendants, even if the owning process panics) + individual; `KillFailed` typed/quarantined; **no
  orphan survives restart** (reaped, not reconnected); no intentionally non-killable unit exists;
  tier selection — untrusted code never below its required tier, downgrade never silent;
  presentational separation classified `None`; **secret-across-spawn** — no raw secret crosses by
  default, injection is policy-gated + audited, sandboxed output is untrusted content; **no
  shell-string injection** — explicit program+argv only, interpreter payloads inspected, no
  blocklist-as-boundary; env allowlist excludes hijack vars; atomic mutation — a cancelled/failed
  write never leaves a partial destination; handles transient — replay consumes recorded snapshots,
  never a live process; platform-availability — a capability never appears available where its
  mechanism cannot enforce.
- **File 22 §19 suite (now complete)**: secret boundary across every persisted/transmitted path
  built so far; redaction golden fixtures; audit-chain tamper detection; **egress gate** — no
  `Sensitive` without recorded opt-in, no raw `Secret` ever, destination inspector narrows never
  widens; **encryption-identity-unchanged** (prepared for P20 — hashes/identity computed over
  plaintext canonical encodings); **no-authority-from-untrusted-content** — an injected "approve
  this" in a tool result reaches policy as data, never as an approval; never widens a lease, lifts a
  floor, lowers sensitivity, raises trust, or authorizes egress; trust-evidence-vs-override — a user
  cannot mint evidence-based `Verified`; integrity mismatch re-gates + downgrades; imported trust is
  inert; settings safety-direction — widening requires typed confirmation, structural invariants are
  not settings.
- 04 §15: path-aliasing serialization; concurrent-mutation guard over real files.
- **Closed-set pinning**: `IsolationTier`, `FilesystemPolicy`, `NetworkPolicy`, `EnvPolicy`,
  resource dimensions, the typed violation set, trust classes.
- Conformance matrix gains: `sandbox.*`/`process.*` anchors, remaining `security.*` anchors, 04 §15;
  the killability invariant (01 §7.11) and the secret-boundary family flip to implemented
  system-wide for existing sinks.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared types for `Sandbox`/`SandboxSpec`/`SandboxProfile`,
  `IsolationTier`/policies/`ResourceLimits`, `ManagedProcess`/`ProcessGroup`/`ProcessHandle`, the
  typed violation set, `SourceIntegrityRecord` + trust-class enum; migrations for trust-state +
  credential-metadata families; the sandbox/process + security event catalogues.
- **Docs**: sandbox contract + profiles + registry doc; isolation-tier + trust-mapping doc;
  managed-process + env-allowlist + interpreter-inspection doc; the two-layer filesystem/network
  enforcement doc; killability/escalation/reaping doc; trust-model, egress-governance, and
  injection-defense docs; cross-platform realization doc (per-platform mechanisms + typed gaps).
- **CI/local commands**: the killability, filesystem-boundary, network-boundary, resource-limit,
  tier-selection, secret-across-spawn, egress-gate, and no-authority-from-untrusted suites as named
  CI jobs (3-OS, platform-conditional assertions where mechanisms differ); the architectural
  grep-guard — no Atlas file I/O outside the chokepoint, no process spawn outside `ManagedProcess`.

## 8. Exit criteria

- [ ] Both mandatory suites green on all 3 OSes (typed platform gaps recorded, none silent).
- [ ] The confined shell capability: spawn → stream → cancel → kill → restart-reap, all ledgered.
- [ ] The structural grep-guards active (chokepoint + ManagedProcess exclusivity).
- [ ] M0–M2 still green.

## 9. Locked in this phase

- **The filesystem chokepoint as the single capability-mediated file-access path** and the
  **canonical mutation identity** shared with 04 — retrofitting either is spec-forbidden and a
  security hole.
- **The ManagedProcess/ProcessGroup model + EnvPolicy allowlist** — every future spawn (providers,
  browsers, engines, MCP servers, sidecars) rides this.
- **The IsolationTier ordinal + trust-to-tier mapping**; killability-contract semantics.
- **The trust-class set + evidence/override/effective split + `SourceIntegrityRecord` hash
  composition** (P18 source approval depends on it).
- **Egress-governance tier semantics + the narrowing-only destination inspector**; the structural
  no-authority-from-untrusted-content rule (load-bearing for every surface).
