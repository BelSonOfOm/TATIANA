"""
PRECILLA / cite / extract.py

Pull citation CANDIDATES out of markdown prose.

Design note (why this is not a bibtex parser):
The MOS documents cite from model knowledge, in prose, without years or venues:

    **TCM, Temporal Context Model** (Howard & Kahana).
    **Successor Representation** (Dayan; Stachenfeld, Botvinick & Gershman).
    Bousfield (semantic clustering), Murdock (serial position), Kahana (lag-CRP)

There are two shapes and they mean OPPOSITE things:

    shape A:  **<concept>** (<people>)      -> title_hint=concept, authors=people
    shape B:  <Person> (<topic>)            -> authors=[Person],  topic_hint=topic

Getting these backwards silently poisons every downstream query, so the
disambiguation is explicit, tested, and reported in the output.

stdlib only.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field, asdict

# --------------------------------------------------------------------------
# surname / person heuristics
# --------------------------------------------------------------------------

# Lowercase particles that legitimately appear inside surnames.
_PARTICLES = {"van", "von", "de", "der", "den", "del", "di", "da", "la", "le",
              "ter", "ten", "al"}

# Words that, if present in a parenthetical, mark it as a TOPIC not a person
# list. Deliberately conservative: words that essentially never appear in a
# surname list.
_TOPIC_MARKERS = {
    "effect", "effects", "curve", "position", "clustering", "spacing",
    "release", "coding", "energy", "memory", "recall", "learning", "model",
    "models", "theory", "and", "or", "the", "a", "an", "of", "for", "with",
    "from", "semantic", "serial", "temporal", "free", "predictive",
    "declarative", "primacy", "recency", "asymmetry", "latency", "capacity",
    "decay", "left", "right", "above", "below", "see", "cf", "eg", "ie",
}

_YEAR_RE = re.compile(r"\b(1[89]\d{2}|20[0-2]\d)([a-d])?\b")

# **Bolded concept** immediately followed by a parenthetical.
_SHAPE_A_RE = re.compile(
    r"\*\*(?P<title>[^*\n]{2,120}?)\*\*\s*\((?P<paren>[^()\n]{2,200}?)\)"
)

# Bare CapitalisedName(s) followed by a parenthetical, not preceded by '*'.
_SHAPE_B_RE = re.compile(
    r"(?<!\*)\b(?P<name>(?:[A-Z][A-Za-z'\-]+)(?:\s*/\s*[A-Z][A-Za-z'\-]+)?)"
    r"\s*\((?P<paren>[^()\n]{2,200}?)\)"
)

# Split a people-parenthetical into individual authors.
_AUTHOR_SPLIT_RE = re.compile(r"\s*(?:;|,|&|\band\b)\s*")


# Internal cross-references -- "(§6.2)", "(see below)", "(Fig. 3)". These look
# exactly like shape-B citations and were the only false positives the first
# run against the real MOS documents produced.
_XREF_RE = re.compile(
    r"^\s*(?:[§#]|see\b|cf\.?\b|fig\.?\b|table\b|eq\.?\b|sec\.?\b|ch\.?\b|"
    r"appendix\b|p{1,2}\.?\s*\d|\d)", re.I)


def _tokens(s):
    return [t for t in re.split(r"[^A-Za-z0-9'\-]+", s) if t]


def is_crossref(paren):
    """True if the parenthetical points inside the document, not outward."""
    if "§" in paren:
        return True
    return bool(_XREF_RE.match(paren))


def _is_acronymish(name):
    """CRP, MOS, TCM -- never a surname in shape B."""
    bare = name.replace("-", "").replace("'", "")
    return bare.isupper() and len(bare) <= 5


def looks_like_person_list(paren):
    """
    True if the parenthetical is a list of surnames rather than a topic.

    Rule: strip years; every remaining alphabetic token must be either
    Capitalised, an initial (J.), or a known particle -- and no token may be a
    topic marker.
    """
    body = _YEAR_RE.sub(" ", paren)
    toks = _tokens(body)
    if not toks:
        return False
    for t in toks:
        low = t.lower()
        if low in _TOPIC_MARKERS:
            return False
        if low in _PARTICLES:
            continue
        if re.fullmatch(r"[A-Z]\.?", t):          # initial
            continue
        if not t[0].isupper():
            return False
    return True


def split_authors(paren):
    """Split a people-parenthetical into surname strings, dropping initials."""
    body = _YEAR_RE.sub(" ", paren)
    out = []
    for chunk in _AUTHOR_SPLIT_RE.split(body):
        chunk = chunk.strip(" .,;&")
        if not chunk:
            continue
        parts = [p for p in chunk.split() if not re.fullmatch(r"[A-Z]\.?", p)]
        if not parts:
            continue
        out.append(" ".join(parts))
    seen = set()
    uniq = []
    for a in out:
        k = a.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(a)
    return uniq


def extract_year(s):
    m = _YEAR_RE.search(s)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------
# candidate record
# --------------------------------------------------------------------------


@dataclass
class Candidate:
    """One unverified citation lifted from prose."""

    cid: str
    authors: list
    year: int = None
    title_hint: str = None
    topic_hint: str = None
    shape: str = "A"
    raw: str = ""
    source: str = ""
    line: int = 0
    # Epistemic status, per the MOS convention. Extraction NEVER emits
    # anything stronger than UNVERIFIED -- only resolution can promote.
    status: str = "UNVERIFIED"
    notes: list = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


def _mk_cid(authors, year, hint):
    a = (authors[0].split()[-1].lower() if authors else "anon")
    a = re.sub(r"[^a-z0-9]", "", a) or "anon"
    y = str(year) if year else "nd"
    h = re.sub(r"[^a-z0-9]+", "-", (hint or "").lower()).strip("-")[:24] or "x"
    return "%s%s-%s" % (a, y, h)


def extract_text(text, source="<text>"):
    """Extract candidates from a markdown string."""
    cands = []
    seen_spans = []

    lines_start = [0]
    for ln in text.split("\n"):
        lines_start.append(lines_start[-1] + len(ln) + 1)

    def line_of(pos):
        lo, hi = 0, len(lines_start) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if lines_start[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    # ---- shape A: **concept** (people) ----
    for m in _SHAPE_A_RE.finditer(text):
        paren = m.group("paren")
        if not looks_like_person_list(paren):
            continue                      # **bold** (topic) -- not a citation
        title = m.group("title").strip()
        # "TCM, Temporal Context Model" -> keep the long form as title hint
        if "," in title:
            title = max((p.strip() for p in title.split(",")), key=len)
        year = extract_year(paren)

        # A semicolon inside a people-parenthetical separates DISTINCT works,
        # not co-authors: "(Dayan; Stachenfeld, Botvinick & Gershman)" is two
        # papers twenty-four years apart. Merging them into one four-author
        # citation would make it unresolvable, so each group becomes its own
        # candidate sharing the concept as its title hint.
        groups = [g for g in (g.strip() for g in paren.split(";")) if g]
        for g in groups:
            authors = split_authors(g)
            if not authors:
                continue
            gy = extract_year(g) or year
            cands.append(Candidate(
                cid=_mk_cid(authors, gy, title),
                authors=authors, year=gy, title_hint=title, shape="A",
                raw=m.group(0), source=source, line=line_of(m.start()),
                notes=(["one of %d works cited together for %r"
                        % (len(groups), title)] if len(groups) > 1 else []),
            ))
        seen_spans.append((m.start(), m.end()))

    # ---- shape B: Person (topic) ----
    for m in _SHAPE_B_RE.finditer(text):
        if any(s <= m.start() < e for s, e in seen_spans):
            continue
        paren = m.group("paren")
        name = m.group("name").strip()
        if is_crossref(paren) or _is_acronymish(name):
            continue
        if looks_like_person_list(paren):
            extra = split_authors(paren)
            authors = [name] + [a for a in extra if a.lower() != name.lower()]
            topic = None
        else:
            authors = [n.strip() for n in name.split("/") if n.strip()]
            topic = paren.strip()
        if not authors:
            continue
        if any(a.lower() in _TOPIC_MARKERS for a in authors):
            continue
        year = extract_year(paren)
        cands.append(Candidate(
            cid=_mk_cid(authors, year, topic),
            authors=authors, year=year, topic_hint=topic, shape="B",
            raw=m.group(0), source=source, line=line_of(m.start()),
        ))

    return _merge(cands)


def _merge(cands):
    """Collapse duplicates that share authors+year, keeping the richest hint."""
    by_key = {}
    order = []
    for c in cands:
        key = (tuple(a.lower() for a in c.authors), c.year)
        cur = by_key.get(key)
        if cur is None:
            by_key[key] = c
            order.append(key)
            continue
        if c.title_hint and not cur.title_hint:
            cur.title_hint = c.title_hint
        if c.topic_hint and not cur.topic_hint:
            cur.topic_hint = c.topic_hint
        note = "also at %s:%d" % (c.source, c.line)
        if note not in cur.notes:
            cur.notes.append(note)
    return [by_key[k] for k in order]


def extract_file(path):
    with open(path, "r", encoding="utf-8") as fh:
        return extract_text(fh.read(), source=path)


def main(argv):
    if not argv:
        sys.stderr.write("usage: extract.py FILE [FILE...]\n")
        return 2
    out = []
    for p in argv:
        out.extend(c.to_dict() for c in extract_file(p))
    json.dump({"candidates": out, "n": len(out)}, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
