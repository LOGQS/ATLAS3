#!/usr/bin/env python3
"""
ATLAS canon spec-lint.

A single deep, stdlib-only linter for the canonical specification series
(Files 01-43 under ``documentation/specification/canonical/``). It enforces the
canonical review's lint program: anchor-registry integrity, cross-reference
resolution, the (anchor, section, concept) triple, the File 10 closed catalogue,
known duplicate-list surfaces, source-path leakage, settings-key namespace
consistency, and banned prose vocabulary. It also carries the D7 rule-anchor
index generator (``--fix-anchors-index``) and its check-mode staleness detector.

Runnable from any working directory: the canon directory is resolved relative to
this file's own location, not the caller's cwd.

    python spec_lint.py                 # lint the live corpus (human output)
    python spec_lint.py --json          # lint, emit a JSON report
    python spec_lint.py --strict        # elevate the prose-policy classes to WARN
    python spec_lint.py --fix-anchors-index   # regenerate the D7 index section

Severity policy (per the converged review): BANNED-VOCAB, SOURCES-PATH, and the
cross-namespace ANCHOR-REGISTRY class report as INFO by default (the legacy
prose stands; the lint enforces on new text) and elevate to WARN under
``--strict``. Adjudicated-OBS findings (see OBS_ALLOWLIST) are always INFO.

Exit codes:
    0   clean -- no WARN or ERROR findings (INFO census output may still print)
    1   one or more WARN/ERROR findings
    2   usage or internal error

Findings print one per line as::

    file:line: CHECK-ID SEVERITY message

sorted deterministically by (file, line, check-id).
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# --------------------------------------------------------------------------- #
# Location + constants
# --------------------------------------------------------------------------- #

# spec_lint.py lives at .../specification/tools/spec_lint/spec_lint.py;
# the canon is the sibling .../specification/canonical/ directory.
CANON_DIR = Path(__file__).resolve().parents[2] / "canonical"

# Trailing scaffolding sections that every canonical file carries but that the
# hand-written D7 index (Files 39-43) deliberately omits: they are document
# scaffolding, not "load-bearing rules defined by this file". The self-anchor of
# the index section is likewise excluded.
INDEX_EXCLUDED_SUFFIXES = (
    "explicit-rejections",
    "consequences-for-later-specs",
    "canonical-rule-anchors",
)

# The opening of the standard (generated) index sentence -- the exemplars'
# final paragraph. Used to recognise a previously generated index sentence
# inside an existing section so regeneration replaces IT and nothing else.
# File 01's definitional prose ("Load-bearing canonical rules carry a stable
# semantic anchor ...") deliberately does not match this prefix.
INDEX_SENTENCE_PREFIX = (
    "Load-bearing rules defined by this file carry stable anchors:"
)

# Adjudicated-legal findings (converged review verdicts). A finding matching an
# entry is reported as INFO with an "(adjudicated OBS)" tag and never gates,
# with or without --strict.
#
# P14-14 correction (iv): the three File 40 `qc.persistence-replay` TRIPLE
# sites were reclassified REFUTED -> OBS under File 39's own coarse-anchor rule
# (File 39 §23 L712) -- the anchor may legally be cited at the finer §10.5
# replay-keying site. Legal as written; kept visible as census output.
OBS_ALLOWLIST = (
    {"check": "TRIPLE", "file_prefix": "40-",
     "contains": "`qc.persistence-replay`"},
)

# The five permission tiers, in canonical restrictiveness order (File 06 sec 4).
# Derived live from File 06 at load time; this is the fallback ground truth used
# only if the chain cannot be located.
TIER_TOKENS = ("Unrestricted", "ReadOnly", "WorkspaceWrite", "UserApproval", "Denied")

# Structural type names that legitimately co-occur with catalogue citations but
# are NOT ledger/event kinds. Used to keep CLOSED-CATALOGUE free of noise.
CATALOGUE_NON_KIND_TYPES = {
    "LedgerEntry", "LedgerEntryKind", "AppEvent", "EventStream", "EventEnvelope",
    "ExecutionLedger", "HookDecision", "HookSubscription", "TokenUsageRecord",
    "AppError", "ProviderError", "ParsedResponse", "RunIntent", "Custom",
    "RunCompletionContract", "RegisteredCapability", "CapabilityInvocation",
    "ContextVersion", "VersionOpSummary", "VersionDiff", "EventBufferOverflow",
    "RateLimitSnapshot", "BorrowGrant", "SubsystemSurfaceSpec",
}

# --------------------------------------------------------------------------- #
# Regexes
# --------------------------------------------------------------------------- #

RE_ANCHOR = re.compile(r"^Anchor:\s+`([a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+)`\s*$")
RE_HEADING_NUM = re.compile(r"^(#{2,6})\s+(\d+(?:\.\d+)*)(?=[.\s])")
RE_HEADING_ANY = re.compile(r"^(#{2,6})\s+(.+?)\s*$")

# A cross-reference: an optional leading anchor token immediately before an
# inline "File NN" (parenthesised or comma-joined). The section list, if any, is
# parsed separately from the tail so compound "(File 01 §6.15, §7.14)" citations
# are handled in full.
RE_REF = re.compile(
    r"(?:`(?P<anchor>[a-z][a-z0-9-]*(?:\.[a-z0-9_-]+)+)`\s*,?\s*)?"
    r"\(?\bFiles?\s+(?P<file>\d{2})\b"
)
# The contiguous section list immediately following a 'File NN' match. Each
# subsequent section carries its own '§', so a stray number ("step 3") is not
# swallowed and a compound "(File 01 §6.15, §7.14)" is captured in full.
RE_SECTION_LIST = re.compile(
    r"^\s*(§\s*\d+(?:\.\d+)*(?:\s*[,/]?\s*(?:and\s+)?§\s*\d+(?:\.\d+)*)*)"
)
RE_SECTION_NUM = re.compile(r"\d+(?:\.\d+)*")

# An inline backticked dotted anchor token and, if present, the cross-reference
# tail ("(File NN" / ", File NN") that marks it as a citation rather than a fresh
# inline declaration.
RE_INLINE_TOKEN = re.compile(
    r"`([a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+)`(\s*,?\s*\(?Files?\s+\d{2})?"
)

# Backticked PascalCase token (opening backtick + a CamelCase word).
RE_PASCAL = re.compile(r"`([A-Z][A-Za-z0-9]+)")

# Settings-key candidate: a backticked dotted lowercase token whose key part
# carries an underscore (the `family.key_name` snake_case shape). This shape
# separates settings keys from anchors (hyphens) and capability ids (no
# underscore).
RE_SETTINGS_KEY = re.compile(r"`([a-z][a-z0-9]*(?:\.[a-z0-9_]+)+)`")

# Source-tree citation shapes.
RE_SOURCE_PATH = re.compile(
    r"CONSTRAINTS\.md|codex_recommendations\.md|\bunit\d{2}\b|(?<![\w/])sources/"
)
RE_REALIZED = re.compile(r"realized|source corpus", re.IGNORECASE)

RE_EVENT_BUS = re.compile(r"\bevent bus\b", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Corpus model
# --------------------------------------------------------------------------- #

class Finding:
    __slots__ = ("file", "line", "check", "severity", "message")

    def __init__(self, file, line, check, severity, message):
        self.file = file
        self.line = line
        self.check = check
        self.severity = severity
        self.message = message

    def sort_key(self):
        return (self.file, self.line, self.check, self.message)

    def format(self):
        return f"{self.file}:{self.line}: {self.check} {self.severity} {self.message}"

    def as_dict(self):
        return {
            "file": self.file,
            "line": self.line,
            "check": self.check,
            "severity": self.severity,
            "message": self.message,
        }


class SpecFile:
    """One canonical file, parsed once into the structures the checks consume."""

    def __init__(self, path):
        self.path = path
        self.name = path.name
        self.text = path.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()
        # File number prefix, e.g. "10". Canon files are NN-*.md.
        self.num = self.name[:2]

        # standalone_anchors: list of (name, line_no, section) for `Anchor: x`
        # lines, in document order.
        self.standalone_anchors = []
        # anchors: the file's OWNED anchor set -- standalone declarations plus
        # inline hyphenated self-family declarations -- ordered by declaration
        # line. Populated after the line scan (needs the family prefix).
        self.anchors = []
        # heading_nums: set of every numbered heading string, e.g. {"3","3.1"}.
        self.heading_nums = set()
        # max top-level (integer) section number, for append placement.
        self.max_top_section = 0
        # line index (0-based) of the "## N. Canonical Rule Anchors" heading, or None.
        self.index_heading_idx = None
        self.index_heading_num = None
        # per-line: is this line inside the front-matter "Source Resolution" section?
        self.in_source_resolution = [False] * len(self.lines)
        # per-line: is this line inside a paragraph containing "Families reviewed"?
        self.in_families_para = [False] * len(self.lines)

        self._parse()

    def _parse(self):
        cur_section = None          # nearest numbered heading above the line
        cur_h2_is_srcres = False    # inside "## Source Resolution"
        section_at_line = [None] * len(self.lines)
        for i, raw in enumerate(self.lines):
            line = raw.rstrip("\n")
            mh = RE_HEADING_ANY.match(line)
            if mh:
                level = len(mh.group(1))
                title = mh.group(2)
                mn = RE_HEADING_NUM.match(line)
                if mn:
                    cur_section = mn.group(2)
                    self.heading_nums.add(cur_section)
                    if "." not in cur_section:
                        self.max_top_section = max(
                            self.max_top_section, int(cur_section)
                        )
                    if title.strip().endswith("Canonical Rule Anchors"):
                        self.index_heading_idx = i
                        self.index_heading_num = cur_section
                if level == 2:
                    cur_h2_is_srcres = (title.strip() == "Source Resolution")
            self.in_source_resolution[i] = cur_h2_is_srcres
            section_at_line[i] = cur_section

            ma = RE_ANCHOR.match(line)
            if ma:
                self.standalone_anchors.append((ma.group(1), i + 1, cur_section))

        self._collect_owned_anchors(section_at_line)

        # Mark paragraphs (blank-line-delimited blocks) containing "Families reviewed".
        start = 0
        n = len(self.lines)
        for i in range(n + 1):
            if i == n or self.lines[i].strip() == "":
                block = self.lines[start:i]
                if any("Families reviewed" in b for b in block):
                    for j in range(start, i):
                        self.in_families_para[j] = True
                start = i + 1

    def _collect_owned_anchors(self, section_at_line):
        """Build the file's owned anchor list: standalone `Anchor:` declarations
        plus inline hyphenated self-family declarations, ordered by declaration
        line. A standalone declaration always positions the anchor (an inline
        mention that precedes it is ignored); an inline token that is a
        cross-reference or a non-hyphenated capability id is not an anchor."""
        prefixes = Counter(n.split(".")[0] for n, _, _ in self.standalone_anchors)
        self._family = prefixes.most_common(1)[0][0] if prefixes else None
        owned = list(self.standalone_anchors)
        seen = {n for n, _, _ in self.standalone_anchors}
        if self._family is not None:
            for i, raw in enumerate(self.lines):
                if RE_ANCHOR.match(raw.rstrip()):
                    continue
                for m in RE_INLINE_TOKEN.finditer(raw):
                    tok, xref_tail = m.group(1), m.group(2)
                    if xref_tail:
                        continue  # a cross-reference, not a fresh declaration
                    if tok in seen:
                        continue
                    if tok.split(".")[0] != self._family:
                        continue  # only self-family tokens are this file's anchors
                    if "-" not in tok.split(".", 1)[1]:
                        continue  # rule anchors hyphenate; capability ids do not
                    seen.add(tok)
                    owned.append((tok, i + 1, section_at_line[i]))
        owned.sort(key=lambda t: t[1])
        self.anchors = owned

    @property
    def family(self):
        return self._family

    def index_anchor_names(self):
        """Anchor names the D7 index should enumerate: body anchors in document
        order minus the scaffolding suffixes."""
        out = []
        for name, _, _ in self.anchors:
            if name.split(".", 1)[-1] in INDEX_EXCLUDED_SUFFIXES:
                continue
            out.append(name)
        return out


class Corpus:
    def __init__(self, files):
        self.files = files                # list[SpecFile], sorted by name
        self.by_num = {f.num: f for f in files}
        # anchor name -> (file_num, line, declared_section)
        self.anchor_home = {}
        self.anchor_dupes = defaultdict(list)  # name -> [(file_num, line)]
        for f in files:
            for name, line, section in f.anchors:
                self.anchor_dupes[name].append((f.num, line))
                # first declaration wins for the home map; dupes reported separately
                self.anchor_home.setdefault(name, (f.num, line, section))


def load_corpus(canon_dir):
    paths = sorted(canon_dir.glob("*.md"))
    if not paths:
        raise FileNotFoundError(f"no canonical files found under {canon_dir}")
    return Corpus([SpecFile(p) for p in paths])


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #

def parse_ref_sections(tail):
    """Given the text immediately after a 'File NN' match, return the contiguous
    list of section numbers it cites (e.g. '§6.15, §7.14' -> ['6.15','7.14'])."""
    m = RE_SECTION_LIST.match(tail)
    if not m:
        return []
    return RE_SECTION_NUM.findall(m.group(1))


def section_prefix_consistent(declared, cited):
    """True when declared and cited section numbers lie on the same heading
    branch (one is a dotted prefix of the other). Conservative: only diverging
    branches (e.g. 3.3 vs 3.7) are flagged as a stale citation."""
    if declared is None:
        return True
    a = declared.split(".")
    b = cited.split(".")
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def iter_refs(spec):
    """Yield (line_no, anchor_or_None, cited_file, [sections]) for every inline
    File reference in *spec*."""
    for i, line in enumerate(spec.lines, 1):
        for m in RE_REF.finditer(line):
            sections = parse_ref_sections(line[m.end():])
            yield i, m.group("anchor"), m.group("file"), sections


# --------------------------------------------------------------------------- #
# Check 1: ANCHOR-REGISTRY
# --------------------------------------------------------------------------- #

def check_anchor_registry(corpus):
    findings = []
    # Corpus-wide duplicate anchors.
    for name, locs in sorted(corpus.anchor_dupes.items()):
        if len(locs) > 1:
            where = ", ".join(f"File {fn}:{ln}" for fn, ln in locs)
            for fn, ln in locs:
                findings.append(Finding(
                    corpus.by_num[fn].name, ln, "ANCHOR-REGISTRY", "ERROR",
                    f"anchor `{name}` declared {len(locs)} times ({where}); "
                    f"anchors name exactly one rule",
                ))
    # Prefix does not match the file's own majority family prefix.
    for f in corpus.files:
        fam = f.family
        if fam is None:
            continue
        for name, line, _ in f.anchors:
            prefix = name.split(".")[0]
            if prefix != fam:
                findings.append(Finding(
                    f.name, line, "ANCHOR-REGISTRY", "WARN",
                    f"anchor `{name}` uses namespace `{prefix}` but file family "
                    f"prefix is `{fam}`",
                ))
    return findings


# --------------------------------------------------------------------------- #
# Check 2: ANCHOR-REF   (anchor<->file mapping + plain section existence)
# Check 3: TRIPLE       (anchor's declared section == cited section)
# --------------------------------------------------------------------------- #

def check_anchor_ref_and_triple(corpus):
    ref_findings = []
    triple_findings = []
    for f in corpus.files:
        for line_no, anchor, cited_file, sections in iter_refs(f):
            target = corpus.by_num.get(cited_file)
            # (a) section existence. The PRIMARY section of a citation must resolve
            # in the cited file — accepting a citing-file match there silently
            # passes stale targets whenever the citing file happens to share the
            # number (Codex checkpoint 2026-07-07, MAJOR). Only TRAILING sections
            # in a compound citation ("File 04 §14, §9.5") may be self-references
            # to the citing file's own sections.
            if target is not None:
                for i, sec in enumerate(sections):
                    in_target = sec in target.heading_nums
                    in_self = sec in f.heading_nums
                    ok = in_target or (i > 0 and in_self)
                    if not ok:
                        ref_findings.append(Finding(
                            f.name, line_no, "ANCHOR-REF", "ERROR",
                            f"section §{sec} not found in File {cited_file}",
                        ))
            # (b) anchor<->file mapping and (c) the triple -- anchored refs only.
            if anchor is None:
                continue
            if "_" in anchor:
                # settings key / capability id caught by the shared regex; not an anchor.
                continue
            home = corpus.anchor_home.get(anchor)
            if home is None:
                # Unknown token. Only a hyphenated dotted token is unambiguously a
                # (broken) anchor reference; a bare word.word is almost always a
                # capability/mechanism id, so it is left alone.
                if "-" in anchor:
                    ref_findings.append(Finding(
                        f.name, line_no, "ANCHOR-REF", "ERROR",
                        f"anchor `{anchor}` cited (File {cited_file}) but not "
                        f"declared anywhere in the corpus",
                    ))
                continue
            home_file, _, declared_section = home
            if home_file != cited_file:
                ref_findings.append(Finding(
                    f.name, line_no, "ANCHOR-REF", "ERROR",
                    f"anchor `{anchor}` cited as File {cited_file} but declared "
                    f"in File {home_file}",
                ))
                continue
            # TRIPLE: right anchor, right file -- is the cited section stale?
            if sections and declared_section is not None:
                if not any(section_prefix_consistent(declared_section, s)
                           for s in sections):
                    cited = ", ".join("§" + s for s in sections)
                    triple_findings.append(Finding(
                        f.name, line_no, "TRIPLE", "WARN",
                        f"anchor `{anchor}` is declared in File {cited_file} "
                        f"§{declared_section} but cross-referenced as {cited}",
                    ))
    return ref_findings, triple_findings


# --------------------------------------------------------------------------- #
# Check 4: CLOSED-CATALOGUE
# --------------------------------------------------------------------------- #

def _region(spec, start_num, stop_nums):
    """Return the (start_idx, end_idx) line span of the heading numbered
    *start_num*, ending at the next heading whose number is in *stop_nums* or at
    the next level-2 (``## ``) heading, whichever comes first."""
    start = None
    for i, line in enumerate(spec.lines):
        m = RE_HEADING_NUM.match(line)
        if m and m.group(2) == start_num:
            start = i
            break
    if start is None:
        return None
    for j in range(start + 1, len(spec.lines)):
        line = spec.lines[j]
        m = RE_HEADING_NUM.match(line)
        if m and m.group(2) in stop_nums:
            return (start, j)
        if line.startswith("## "):
            return (start, j)
    return (start, len(spec.lines))


def _catalogue_members(spec, section_num, stop):
    span = _region(spec, section_num, stop)
    members = set()
    if span is None:
        return members, span
    start, end = span
    for line in spec.lines[start:end]:
        if not line.lstrip().startswith("- "):
            continue
        head = line.split("—", 1)[0]  # text before the em-dash
        for tok in RE_PASCAL.findall(head):
            members.add(tok)
    return members, span


def check_closed_catalogue(corpus):
    findings = []
    f10 = corpus.by_num.get("10")
    if f10 is None:
        return findings
    entry_members, entry_span = _catalogue_members(f10, "4.1", {"4.2"})
    trans_members, trans_span = _catalogue_members(f10, "5.3", {"5.4"})
    catalogue = entry_members | trans_members | {"Custom"}
    if not catalogue:
        return findings

    # Lines in File 10 that constitute the catalogue itself are exempt.
    f10_exempt = set()
    for span in (entry_span, trans_span):
        if span:
            f10_exempt.update(range(span[0], span[1]))

    # A citation that pins a token to the File 10 closed catalogue specifically.
    cite_marker = re.compile(
        r"File 10 §4\.1|File 10 §5\.3"
        r"|`ledger\.entry-kind-catalogue`|`ledger\.app-event-catalogue`"
    )
    # Form 1: a token directly annotated as a kind ("a `Foo` LedgerEntryKind").
    direct = re.compile(
        r"`([A-Z][A-Za-z0-9]+)`\s+(?:is\s+)?(?:a\s+|an\s+|the\s+)?"
        r"(?:new\s+|canonical\s+|reserved\s+)?(?:`?LedgerEntryKind`?|`?AppEvent`?)\b"
        r"|(?:`?LedgerEntryKind`?|`?AppEvent`?)\s+`([A-Z][A-Za-z0-9]+)`"
    )

    def kind_shaped(tok):
        # Reject non-kind PascalCase tokens: known structural types, and
        # noun-form type names. Catalogue kinds read as event verbs (past
        # participles, -Changed / -Fired / -Chunk / -Overflow, etc.).
        if tok in catalogue or tok in CATALOGUE_NON_KIND_TYPES:
            return False
        return bool(re.search(
            r"(ed|ing|Changed|Fired|Detected|Requested|Completed|Failed|"
            r"Started|Stopped|Chunk|Overflow|Warning|Exhausted|Delta|Partial)$",
            tok))

    for f in corpus.files:
        for i, line in enumerate(f.lines, 1):
            if f.num == "10" and (i - 1) in f10_exempt:
                continue
            flagged = set()
            # Form 1: a token directly annotated as a kind.
            for m in direct.finditer(line):
                tok = m.group(1) or m.group(2)
                if tok and tok not in catalogue and tok not in CATALOGUE_NON_KIND_TYPES:
                    flagged.add(tok)
            # Form 2: a "reserved" enumeration pinned to the File 10 catalogue.
            # Lines that register `Custom` kinds legitimately name non-catalogue
            # kinds and are excluded.
            if ("reserved" in line and cite_marker.search(line)
                    and "Custom" not in line):
                for tok in RE_PASCAL.findall(line):
                    if kind_shaped(tok):
                        flagged.add(tok)
            for tok in sorted(flagged):
                findings.append(Finding(
                    f.name, i, "CLOSED-CATALOGUE", "WARN",
                    f"`{tok}` is asserted as a File 10 catalogue kind but is "
                    f"absent from the LedgerEntryKind/AppEvent catalogue",
                ))
    return findings


# --------------------------------------------------------------------------- #
# Check 5: DUP-LIST   (tier ladder + discovery roster)
# --------------------------------------------------------------------------- #

def _canonical_tier_order(corpus):
    f06 = corpus.by_num.get("06")
    chain_re = re.compile(
        r"(" + "|".join(TIER_TOKENS) + r")((?:\s*<\s*(?:" + "|".join(TIER_TOKENS) + r"))+)"
    )
    if f06:
        for line in f06.lines:
            m = chain_re.search(line)
            if m:
                toks = re.findall("|".join(TIER_TOKENS), m.group(0))
                if len(toks) >= 3:
                    return toks
    return list(TIER_TOKENS)


def check_dup_list(corpus):
    findings = []
    canonical = _canonical_tier_order(corpus)
    rank = {t: i for i, t in enumerate(canonical)}
    chain_re = re.compile(
        r"(?:" + "|".join(TIER_TOKENS) + r")(?:\s*[<>]\s*(?:"
        + "|".join(TIER_TOKENS) + r")){2,}"
    )
    tier_alt = re.compile("|".join(TIER_TOKENS))
    for f in corpus.files:
        for i, line in enumerate(f.lines, 1):
            for m in chain_re.finditer(line):
                seq = tier_alt.findall(m.group(0))
                ascending = seq if "<" in m.group(0) else list(reversed(seq))
                ranks = [rank[t] for t in ascending if t in rank]
                if ranks != sorted(ranks):
                    findings.append(Finding(
                        f.name, i, "DUP-LIST", "WARN",
                        f"permission-tier ladder restated as {' < '.join(ascending)} "
                        f"diverges from the canonical order "
                        f"{' < '.join(canonical)} (File 06 §4)",
                    ))

    # Discovery five-member roster (File 07 sec 7.1).
    f07 = corpus.by_num.get("07")
    roster = set()
    roster_line = None
    if f07:
        span = _region(f07, "7.1", {"7.2"})
        if span:
            start, end = span
            roster_line = start + 1
            for line in f07.lines[start:end]:
                if line.lstrip().startswith("- "):
                    m = re.match(r"\s*-\s+`((?:tool|mcp)\.[a-z_]+)`", line)
                    if m:
                        roster.add(m.group(1))
    if roster:
        id_re = re.compile(r"`((?:tool|mcp)\.[a-z_]+)`")
        for f in corpus.files:
            for i, line in enumerate(f.lines, 1):
                if f.num == "07" and roster_line and i == roster_line:
                    continue
                if "five" not in line.lower():
                    continue
                ids = set(id_re.findall(line))
                # A restatement: it enumerates several discovery ids and says "five".
                if len(ids & roster) >= 3 and ids != roster and ids - roster:
                    findings.append(Finding(
                        f.name, i, "DUP-LIST", "WARN",
                        f"discovery roster restated as {sorted(ids)} diverges "
                        f"from the canonical five {sorted(roster)} (File 07 §7.1)",
                    ))
    return findings


# --------------------------------------------------------------------------- #
# Check 6: SOURCES-PATH
# --------------------------------------------------------------------------- #

def check_sources_path(corpus):
    findings = []
    for f in corpus.files:
        for i, line in enumerate(f.lines, 1):
            if not RE_SOURCE_PATH.search(line):
                continue
            if f.in_source_resolution[i - 1] or f.in_families_para[i - 1]:
                continue
            severity = "INFO" if RE_REALIZED.search(line) else "WARN"
            names = sorted({m.group(0) for m in RE_SOURCE_PATH.finditer(line)})
            findings.append(Finding(
                f.name, i, "SOURCES-PATH", severity,
                f"source-tree citation ({', '.join(names)}) in normative body "
                f"outside Source Resolution / Families-reviewed heritage",
            ))
    return findings


# --------------------------------------------------------------------------- #
# Check 7: SETTINGS-KEY   (cross-family namespace census)
# --------------------------------------------------------------------------- #

def check_settings_key(corpus):
    findings = []
    # trailing-key -> set of family prefixes; and per-(file) occurrences.
    trailing_families = defaultdict(set)
    occurrences = defaultdict(list)  # fullkey -> [(spec, line)]
    for f in corpus.files:
        for i, line in enumerate(f.lines, 1):
            for m in RE_SETTINGS_KEY.finditer(line):
                tok = m.group(1)
                if tok.endswith(".md"):
                    continue
                segs = tok.split(".")
                if not any("_" in s for s in segs[1:]):
                    continue  # require the snake_case key signature
                trailing = ".".join(segs[1:])
                trailing_families[trailing].add(segs[0])
                occurrences[tok].append((f, i))
    # A collision: one trailing key under >1 family prefix.
    colliding = {t for t, fams in trailing_families.items() if len(fams) > 1}
    for fullkey, occ in occurrences.items():
        segs = fullkey.split(".")
        trailing = ".".join(segs[1:])
        if trailing not in colliding:
            continue
        families = sorted(trailing_families[trailing])
        for spec, line in occ:
            findings.append(Finding(
                spec.name, line, "SETTINGS-KEY", "INFO",
                f"settings key `{fullkey}`: trailing key `{trailing}` appears "
                f"under inconsistent namespaces {families}",
            ))
    return findings


# --------------------------------------------------------------------------- #
# Check 8: BANNED-VOCAB
# --------------------------------------------------------------------------- #

def check_banned_vocab(corpus):
    findings = []
    for f in corpus.files:
        for i, line in enumerate(f.lines, 1):
            if not RE_EVENT_BUS.search(line):
                continue
            # File 10's own supersession note (the one place the term is defined
            # as superseded vocabulary) is exempt.
            if f.num == "10" and "supersedes" in line:
                continue
            findings.append(Finding(
                f.name, i, "BANNED-VOCAB", "WARN",
                "prose uses \"event bus\"; the canonical primitive is `EventStream`",
            ))
    return findings


# --------------------------------------------------------------------------- #
# D7 rule-anchor index: generator + check-mode staleness
# --------------------------------------------------------------------------- #

def _join_anchor_list(names):
    """Render an anchor list in the exemplar voice: `a`, `b`, ..., and `z`."""
    ticked = [f"`{n}`" for n in names]
    if len(ticked) == 1:
        return ticked[0]
    if len(ticked) == 2:
        return f"{ticked[0]} and {ticked[1]}"
    return ", ".join(ticked[:-1]) + ", and " + ticked[-1]


def build_index_sentence(spec):
    """The standard index sentence -- the exemplars' final paragraph."""
    body = _join_anchor_list(spec.index_anchor_names())
    return (
        f"{INDEX_SENTENCE_PREFIX} {body}. "
        f"Cross-references should prefer the anchor and may cite the section "
        f"number secondarily. An anchor names exactly one canonical rule and is "
        f"stable across spec revisions."
    )


def build_index_section(spec, heading_num):
    """Return the full standard D7 section text (Files 39-43 template)."""
    family = spec.family or spec.num
    return (
        f"## {heading_num}. Canonical Rule Anchors\n"
        f"\n"
        f"Anchor: `{family}.canonical-rule-anchors`\n"
        f"\n"
        f"{build_index_sentence(spec)}\n"
    )


def _index_section_span(spec):
    """(start, end) half-open line-index span of the existing index section
    (heading line through EOF or the next '## ' heading)."""
    start = spec.index_heading_idx
    end = len(spec.lines)
    for j in range(start + 1, len(spec.lines)):
        if spec.lines[j].startswith("## "):
            end = j
            break
    return start, end


def _split_paragraphs(lines, lo, hi):
    """(start, end) half-open ranges of the non-blank blocks in lines[lo:hi]."""
    out = []
    ps = None
    for j in range(lo, hi):
        if lines[j].strip() == "":
            if ps is not None:
                out.append((ps, j))
                ps = None
        elif ps is None:
            ps = j
    if ps is not None:
        out.append((ps, hi))
    return out


RE_ANCHOR_SHAPE = re.compile(r"`([a-z][a-z0-9-]*(?:\.[a-z0-9-]+)+)`")


def _index_sentence_names(spec):
    """Anchor names enumerated in the section's standard index sentence, in
    listed order -- or None when the section carries no standard sentence
    (e.g. File 01's definitional form before generation)."""
    start, end = _index_section_span(spec)
    for ps, pe in _split_paragraphs(spec.lines, start + 1, end):
        text = " ".join(spec.lines[ps:pe]).strip()
        if text.startswith(INDEX_SENTENCE_PREFIX):
            names, seen = [], set()
            for tok in RE_ANCHOR_SHAPE.findall(text):
                if tok not in seen:
                    seen.add(tok)
                    names.append(tok)
            return names
    return None


def check_anchors_index(corpus):
    """Report files whose existing D7 index section is stale relative to the
    file's actual anchor set: no standard index sentence at all, or a sentence
    listing missing/extra anchors. Custom prose in the section (File 01's
    definitional form) is never itself a finding -- the generator preserves it
    and manages only the standard sentence."""
    findings = []
    for f in corpus.files:
        if f.index_heading_idx is None:
            continue  # no existing index section; generation handles absence
        expected = f.index_anchor_names()
        listed = _index_sentence_names(f)
        if listed is None:
            findings.append(Finding(
                f.name, f.index_heading_idx + 1, "ANCHORS-INDEX", "WARN",
                f"rule-anchor index section carries no standard index sentence; "
                f"{len(expected)} anchors unlisted (--fix-anchors-index appends "
                f"the sentence, preserving the section's existing prose)",
            ))
            continue
        listed_set, expected_set = set(listed), set(expected)
        missing = [n for n in expected if n not in listed_set]
        extra = [n for n in listed if n not in expected_set]
        if not missing and not extra:
            continue

        def cap(seq, k=6):
            if len(seq) <= k:
                return ", ".join(f"`{x}`" for x in seq)
            return ", ".join(f"`{x}`" for x in seq[:k]) + f", +{len(seq) - k} more"

        parts = []
        if missing:
            parts.append(f"missing {len(missing)} ({cap(missing)})")
        if extra:
            parts.append(f"extra {len(extra)} ({cap(extra)})")
        findings.append(Finding(
            f.name, f.index_heading_idx + 1, "ANCHORS-INDEX", "WARN",
            "rule-anchor index section is stale: " + "; ".join(parts),
        ))
    return findings


def run_fix_anchors_index(corpus):
    """Regenerate the '## N. Canonical Rule Anchors' section in every file.

    - No existing section: append the full standard section (heading number =
      last top-level section + 1).
    - Existing section whose body is only the self-anchor declaration plus
      standard index sentence(s) (the Files 39-43 shape): replace the section
      with the freshly built standard section. Idempotent on a correct file.
    - Existing section carrying ANY other content (File 01's definitional
      prose, which is normative canon): preserve every existing line, remove
      only a previously generated standard index sentence if one exists, and
      append the fresh standard index sentence as the section's final
      paragraph. The section's own prose is never rewritten or deleted.

    Returns a list of human-readable change summaries. Not invoked by the
    linting entry points; wired to --fix-anchors-index only.
    """
    summaries = []
    for f in corpus.files:
        if f.index_heading_idx is not None:
            start, end = _index_section_span(f)
            heading_num = f.index_heading_num
            # Classify the section body: standard-sentence paragraphs are
            # regenerable; a bare self-anchor line is standard scaffolding;
            # anything else is custom prose that must be preserved.
            sentence_line_idxs = set()
            has_custom_prose = False
            for ps, pe in _split_paragraphs(f.lines, start + 1, end):
                text = " ".join(f.lines[ps:pe]).strip()
                if text.startswith(INDEX_SENTENCE_PREFIX):
                    sentence_line_idxs.update(range(ps, pe))
                elif pe - ps == 1 and RE_ANCHOR.match(f.lines[ps].rstrip()):
                    pass  # the section's own `Anchor:` self-declaration
                else:
                    has_custom_prose = True
            if has_custom_prose:
                kept = [f.lines[j] for j in range(start, end)
                        if j not in sentence_line_idxs]
                while kept and kept[-1].strip() == "":
                    kept.pop()
                section_lines = kept + ["", build_index_sentence(f)]
                action = f"refreshed index sentence in section {heading_num} " \
                         f"(existing prose preserved)"
            else:
                section_lines = build_index_section(
                    f, heading_num).rstrip("\n").split("\n")
                action = f"regenerated section {heading_num}"
            if end < len(f.lines) and section_lines[-1].strip() != "":
                section_lines.append("")
            new_lines = f.lines[:start] + section_lines + f.lines[end:]
        else:
            heading_num = f.max_top_section + 1
            section_lines = build_index_section(
                f, heading_num).rstrip("\n").split("\n")
            trimmed = list(f.lines)
            while trimmed and trimmed[-1].strip() == "":
                trimmed.pop()
            new_lines = trimmed + [""] + section_lines
            action = f"appended section {heading_num}"
        out = "\n".join(new_lines)
        if not out.endswith("\n"):
            out += "\n"
        f.path.write_text(out, encoding="utf-8")
        summaries.append(
            f"{f.name}: {action} ({len(f.index_anchor_names())} anchors)"
        )
    return summaries


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #

ALL_CHECKS = [
    "ANCHOR-REGISTRY", "ANCHOR-REF", "TRIPLE", "CLOSED-CATALOGUE",
    "DUP-LIST", "SOURCES-PATH", "SETTINGS-KEY", "BANNED-VOCAB", "ANCHORS-INDEX",
]


def apply_severity_policy(findings, strict):
    """Apply the converged review's severity policy in place.

    Default (non-strict) downgrades to INFO:
    - BANNED-VOCAB    -- P14-20: File 10's own uses were fixed; the downstream
      "event bus" prose stands (no sweep); the ban is enforced on new text.
    - SOURCES-PATH    -- P14-26: the legacy Class-B heritage glosses remain;
      the lint enforces on new text.
    - ANCHOR-REGISTRY cross-namespace anchors (the WARN class) -- the
      secret.*/process.* namespaces in Files 22/23 are legitimate historic
      namespaces. Duplicate-anchor ERRORs are never downgraded.

    ``--strict`` restores the intrinsic severities of all three classes for
    new-text review. Adjudicated-OBS allowlisted findings are always INFO and
    tagged, strict or not.
    """
    for x in findings:
        if any(x.check == e["check"]
               and x.file.startswith(e["file_prefix"])
               and e["contains"] in x.message
               for e in OBS_ALLOWLIST):
            x.severity = "INFO"
            x.message += " (adjudicated OBS)"
            continue
        if strict:
            continue
        if x.check in ("BANNED-VOCAB", "SOURCES-PATH"):
            x.severity = "INFO"
        elif x.check == "ANCHOR-REGISTRY" and x.severity == "WARN":
            x.severity = "INFO"
    return findings


def run_all_checks(corpus, strict=False):
    findings = []
    findings += check_anchor_registry(corpus)
    ref, triple = check_anchor_ref_and_triple(corpus)
    findings += ref
    findings += triple
    findings += check_closed_catalogue(corpus)
    findings += check_dup_list(corpus)
    findings += check_sources_path(corpus)
    findings += check_settings_key(corpus)
    findings += check_banned_vocab(corpus)
    findings += check_anchors_index(corpus)
    apply_severity_policy(findings, strict)
    findings.sort(key=lambda x: x.sort_key())
    return findings


def exit_code_for(findings):
    return 1 if any(x.severity in ("ERROR", "WARN") for x in findings) else 0


def main(argv=None):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="ATLAS canon spec-lint (stdlib only).")
    parser.add_argument(
        "--fix-anchors-index", action="store_true",
        help="regenerate the '## N. Canonical Rule Anchors' section in all files")
    parser.add_argument(
        "--json", action="store_true",
        help="emit findings as a JSON report")
    parser.add_argument(
        "--strict", action="store_true",
        help="elevate BANNED-VOCAB, SOURCES-PATH, and cross-namespace "
             "ANCHOR-REGISTRY findings to WARN (new-text review mode)")
    args = parser.parse_args(argv)

    try:
        corpus = load_corpus(CANON_DIR)
    except Exception as exc:  # usage / internal error
        sys.stderr.write(f"spec_lint: error: {exc}\n")
        return 2

    if args.fix_anchors_index:
        try:
            summaries = run_fix_anchors_index(corpus)
        except Exception as exc:
            sys.stderr.write(f"spec_lint: error during index generation: {exc}\n")
            return 2
        if args.json:
            print(json.dumps({"regenerated": summaries}, indent=2))
        else:
            for s in summaries:
                print(s)
            print(f"\nRegenerated rule-anchor index in {len(summaries)} files.")
        return 0

    try:
        findings = run_all_checks(corpus, strict=args.strict)
    except Exception as exc:
        sys.stderr.write(f"spec_lint: internal error: {exc}\n")
        return 2

    counts = Counter(x.check for x in findings)
    sev_counts = Counter(x.severity for x in findings)

    if args.json:
        report = {
            "canon_dir": str(CANON_DIR),
            "files": len(corpus.files),
            "strict": args.strict,
            "summary": {
                "by_check": {c: counts.get(c, 0) for c in ALL_CHECKS},
                "by_severity": dict(sev_counts),
                "total": len(findings),
            },
            "findings": [x.as_dict() for x in findings],
        }
        print(json.dumps(report, indent=2))
    else:
        for x in findings:
            print(x.format())
        print("", file=sys.stderr)
        summary = "  ".join(f"{c}={counts.get(c, 0)}" for c in ALL_CHECKS)
        print(f"spec_lint: {len(findings)} findings across {len(corpus.files)} "
              f"files "
              f"(ERROR={sev_counts.get('ERROR', 0)} "
              f"WARN={sev_counts.get('WARN', 0)} "
              f"INFO={sev_counts.get('INFO', 0)})", file=sys.stderr)
        print(f"spec_lint: {summary}", file=sys.stderr)

    return exit_code_for(findings)


if __name__ == "__main__":
    sys.exit(main())
