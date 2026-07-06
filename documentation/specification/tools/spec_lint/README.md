# spec_lint

A single stdlib-only linter for the ATLAS canonical specification series
(Files 01–43 under `documentation/specification/canonical/`). It enforces the
canonical review's lint program and carries the D7 rule-anchor index generator.

No dependencies. Python 3.7+. The canon directory is resolved relative to the
script's own location, so it runs from any working directory.

## Run

```
python spec_lint.py                    # lint the corpus, human-readable output
python spec_lint.py --json             # lint, emit a JSON report to stdout
python spec_lint.py --strict          # new-text review mode (see severity policy)
python spec_lint.py --fix-anchors-index   # regenerate the D7 index section (writes files)
```

Findings print one per line, sorted by file then line:

```
file:line: CHECK-ID SEVERITY message
```

The trailing summary (counts per check and per severity) is written to stderr,
so `--json` / findings on stdout stay machine-parseable.

## Exit codes

| code | meaning |
|------|---------|
| `0`  | clean — no `WARN` or `ERROR` findings (advisory `INFO` may still print) |
| `1`  | one or more `WARN`/`ERROR` findings |
| `2`  | usage or internal error (e.g. canon directory not found) |

`INFO` findings never fail the gate; only `WARN`/`ERROR` do.

## Severity policy

Aligned with the converged review verdicts, three classes report as **INFO by
default** — the legacy prose stands and the lint enforces on *new* text:

- `BANNED-VOCAB` — P14-20: File 10's own uses were fixed; the downstream
  "event bus" prose stands (no corpus sweep).
- `SOURCES-PATH` (all findings) — P14-26: the legacy Class-B heritage glosses
  remain in place.
- `ANCHOR-REGISTRY` cross-namespace anchors — the `secret.*` / `process.*`
  namespaces in Files 22/23 are legitimate historic namespaces.
  Duplicate-anchor findings stay ERROR regardless.

`--strict` elevates all three classes back to their intrinsic severities
(WARN; `SOURCES-PATH` keeps its original WARN-vs-realized-gloss-INFO split) for
reviewing newly written spec text.

### Adjudicated-OBS allowlist

`OBS_ALLOWLIST` (in `spec_lint.py`, commented with the verdict source) carries
findings adjudicated as legal. They print as `INFO` with an
`(adjudicated OBS)` tag and never gate, with or without `--strict`. Seeded
with the three File 40 `qc.persistence-replay` TRIPLE sites (P14-14 correction
(iv): REFUTED → OBS under File 39's own coarse-anchor rule, File 39 §23 L712).

## Checks

| id | default severity | what it catches |
|----|------------------|-----------------|
| `ANCHOR-REGISTRY` | ERROR / INFO (WARN with `--strict`) | duplicate `Anchor:` names corpus-wide (ERROR, always); anchors whose namespace prefix differs from the file's majority family prefix (INFO by default) |
| `ANCHOR-REF` | ERROR | a `` `x.y` (File NN …) `` cross-reference whose anchor is not declared in File NN (or nowhere); a `(File NN §Z)` section that is not a heading in File NN |
| `TRIPLE` | WARN | an anchored+section reference whose anchor is declared in a *different* section of File NN than the one cited (a stale section number on a correct anchor) |
| `CLOSED-CATALOGUE` | WARN | a backticked PascalCase token asserted as a File 10 `LedgerEntryKind`/`AppEvent` kind (annotated as one, or listed in a "reserved … (File 10 §4.1)" enumeration) but absent from the §4.1/§5.3 catalogue |
| `DUP-LIST` | WARN | the File 06 §4 permission-tier ladder restated elsewhere in a divergent order; the File 07 §7.1 five-member discovery roster restated with different membership |
| `SOURCES-PATH` | INFO (WARN with `--strict`) | a source-tree citation (`CONSTRAINTS.md`, `codex_recommendations.md`, `unitNN`, `sources/…`) in the normative body, outside a `Source Resolution` section and outside a "Families reviewed" heritage paragraph |
| `SETTINGS-KEY` | INFO | a snake_case settings key (`family.key_name`) whose trailing key appears under more than one family prefix — a namespace-consistency census |
| `BANNED-VOCAB` | INFO (WARN with `--strict`) | prose use of "event bus" (the canonical primitive is `EventStream`), outside File 10's own supersession note |
| `ANCHORS-INDEX` | WARN | a file whose `## N. Canonical Rule Anchors` section carries no standard index sentence, or whose sentence lists missing/extra anchors versus the file's actual anchor set |

### Anchor model

An anchor is any rule identifier the file **owns**: a standalone `Anchor: \`x\``
line, or an inline self-family declaration `(\`family.multi-word-name\`)` (rule
anchors hyphenate their names; inline capability ids like `\`tool.borrow\`` do
not and are excluded). A standalone declaration positions the anchor even when an
inline mention precedes it. Cross-references (a token followed by `File NN`) are
not declarations.

## D7 rule-anchor index generator

`--fix-anchors-index` regenerates the `## N. Canonical Rule Anchors` section in
every file to match the hand-written exemplars (Files 39–43): a final numbered
section carrying `Anchor: \`family.canonical-rule-anchors\`` and the standard
sentence ("Load-bearing rules defined by this file carry stable anchors: …")
enumerating the file's owned anchors, in document order, in the exemplar voice.
Anchors for the three scaffolding sections (`*.explicit-rejections`,
`*.consequences-for-later-specs`, and the self `*.canonical-rule-anchors`) are
omitted, matching the exemplars.

Per-file behavior:

- **No existing section** — appends the full standard section (heading number =
  last top-level section + 1).
- **Plain-list section** (body is only the self-anchor plus the standard
  sentence — the Files 39–43 shape) — replaces the section with a freshly built
  one. Byte-identical on an already-correct file (verified against Files 40/41).
- **Section with any other prose** (File 01's *definitional* form, whose prose
  is normative canon) — **preserves every existing line**, removes only a
  previously generated standard index sentence if one exists, and appends the
  fresh standard sentence as the section's final paragraph. The definitional
  prose is never rewritten or deleted. Idempotent.

Without the flag, the `ANCHORS-INDEX` check reports staleness: it compares the
anchors listed in the section's standard sentence (only) against the file's
actual anchor set, and reports a section that has no standard sentence yet
(File 01's current state) as unlisted. Custom prose is never itself a finding.
