# Phase 1 — Kernel Contracts (Canonical Encoding, Identity, Errors)

## 1. Goal & why now

The constitutional type layer every later crate imports: a frozen `CanonicalEncoding`, canonical
hashing, typed errors, stable identity, the closed-enum machinery, and the shared vocabularies (scope,
sensitivity). Every major layer depends on stable primitive types; implementing storage, ledger,
settings, or capabilities before this vocabulary exists forces rewrites and invites parallel types.
This is the single highest-leverage retrofit-risk phase in the plan — File 01 §6.15/§7.14 underpin
every identity, integrity, dedup, sync, and replay operation in Files 08–43.

## 2. Canonical scope & deferrals

- **File 01 — complete**: `core.canonical-encoding` (§6.15), `core.canonical-hash` (§7.14),
  `core.closed-canonical` (§6.16), `core.typed-errors` (§6.9, §7.6), the canonical abstractions (§4)
  as types where they are pure data, the primitive set (§6) as contracts, the invariants (§7) as
  enforced library behavior where mechanizable, the explicit rejections (§8) as lint/review entries,
  the rule-anchor convention (§11).
- Deferred: File 01's runtime primitives (ledger, blocks, settings, …) are *defined* by later files
  and *built* in their owning phases — this phase builds only what File 01 itself owns.

## 3. Prerequisites

P0 (toolchain, CI, golden-test harness slots).

## 4. Lanes

Rust primitive types, the TypeScript mirrors (generated where the generator exists, documented manual
mirrors otherwise), and the golden-fixture structure in parallel; redaction-safe wrappers and typed
error envelopes independently, folded into the shared crate at the end.

## 5. Build plan

1. **`CanonicalEncoding`** (01 §6.15): declared field order; enum tag encoding; optional-field
   representation; null-vs-omitted; integer/string/bool encoding; map key ordering;
   order-insensitive collections sorted by stable key; order-sensitive sequences declared; embedded
   schema/version tag. Implemented as a derive/trait so every future durable type opts in
   declaratively, with explicit versioning and storage-independent byte output.
2. **Canonical hashing** (01 §7.14): SHA-256 over CanonicalEncoding only — helpers that refuse to
   hash physical storage bytes unless the value implements the declared encoding. One helper for
   every later hash (`block.content-hash`, `version.diff-hash`, `version.expected-view-hash`, audit
   chain, capture encodings, package/release hashes), with hash-domain separation support (File 08
   §4.5 needs per-variant domains).
3. **Typed errors** (01 §6.9): the `AppError` foundation — typed, in-band-representable, carrying the
   error-kind taxonomy hooks later files extend, with retryability classification and
   user-facing-safe message boundaries. No stringly errors anywhere, ever.
4. **Identity**: UUID-based stable-identity helpers — never reused, never path-derived,
   device-independent (File 20 §3.4 consumes this contract).
5. **Closed-enum machinery** (01 §6.16): the pattern for closed-canonical-plus-`Custom{namespace,
   name}` enums with serde + CanonicalEncoding support, exhaustive-switch helpers for the TS mirrors,
   and registration hooks for runtime `Custom` variants (consumed by 05/08/10/12/18/19/33/34…).
6. **Shared vocabularies**: the scope set `{run, intent_thread, task, conversation, workspace,
   global, reusable_policy_rule}` (one set shared by 06/08/09/10/11) and sensitivity
   `{Public, Sensitive, Secret}` (shared by 08/09/10/22). Defined once, here.
7. **Rejection-list mechanization** (01 §8): extend P0's banned-pattern greps with what is now
   lintable (`updated_at`-LWW patterns, unkeyed model-dependent scalar field names); the rest joins
   the review checklist.
8. **Anchor tooling v2**: the matrix tool validates anchor references in code/test annotations so
   tests link to anchors mechanically.

## 6. Test obligations & acceptance evidence

- **Golden canonical-encoding fixtures** (01 §6.15/§7.14; restated by 19 §6.4, 21 §18, 43 §16.2): a
  fixed typed input encodes to a fixed byte sequence and a fixed hash — pinning the encoding against
  drift forever. The most important tests in the repository; they never change without a
  schema-version bump. **Byte-identical across all 3 OSes** — this is the cross-platform determinism
  check.
- Property tests: encode/decode round-trip; ordering determinism (shuffled insertion → identical
  bytes); **hash-equality follows canonical encoding, not storage layout** — physically-different-
  but-canonically-equal inputs hash identically, and the converse (pre-stating 20 §9.3).
- Null-vs-omitted distinction; enum-tag stability; schema-version-tag presence; closed-set
  exhaustiveness (compile-time where possible).
- Typed-error serialization/deserialization round-trip; redaction test — secret-like wrapper types
  never display raw content.
- Conformance matrix gains: `core.canonical-encoding`, `core.canonical-hash`,
  `core.closed-canonical` (machinery), `core.typed-errors`, identity/vocabulary anchors.

## 7. Artifacts, docs & CI surface

- **Generated artifacts**: shared Rust↔TS type bindings for the kernel vocabulary (break-the-build on
  drift); the canonical-encoding fixture set (registered, never hand-edited).
- **Docs**: kernel-crate module doc; the CanonicalEncoding reference (the eight encoding rules); the
  typed-error conventions doc; glossary seeded with the canonical noun-objects.
- **CI/local commands**: the golden-encoding suite as a named CI job; duplicate-definition grep-guard
  (no later crate may define parallel encoding/error/identity/enum machinery).

## 8. Exit criteria

- [ ] Golden fixtures committed and green cross-OS; a deliberate encoding-rule mutation breaks a
      golden (verified once).
- [ ] Property suites green; kernel crates published; the duplicate-definition guard active.
- [ ] Canonical hashing is impossible to bypass accidentally in any code path that opts into
      identity/hash behavior.

## 9. Locked in this phase

- **The entire CanonicalEncoding contract** — field order, enum tagging, null-vs-omitted, ordering,
  version-tag placement. Changing any of it after P3 is a system-wide breaking retrofit (the
  highest-risk anchor in the canon).
- SHA-256 as the canonical hash; the hash-domain separation scheme.
- UUID identity scheme; the scope and sensitivity vocabularies.
- The closed-enum + `Custom{namespace, name}` representation (its encoding is durable in every later
  enum-bearing record).
