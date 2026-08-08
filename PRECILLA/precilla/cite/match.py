"""
PRECILLA / cite / match.py

Score a candidate citation against a retrieved bibliographic Work.

The whole point of PRECILLA's cite module is to distinguish

    (a) a real paper the model correctly remembered,
    (b) a real paper the model garbled,
    (c) a paper that does not exist.

(c) is the dangerous one and it is the reason this module exists as a separate,
testable unit with an explicit threshold rather than as an "ask the LLM if it
looks right" step. A fabricated citation typically produces a plausible TOPICAL
match with the wrong or missing authors -- so author agreement is weighted
hard, and a high topical score with weak author agreement is treated as
evidence AGAINST, not for.

stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from difflib import SequenceMatcher

# Tunable, but a SINGLE shared setting must pass the calibration battery
# (gold + decoy + near-miss) or the instrument is not used. See calibrate.py
# and MOS discipline rule 3.
DEFAULTS = {
    "tau_verified": 0.72,
    "tau_partial": 0.50,
    "min_author_recall": 0.99,   # every named author must appear, for VERIFIED
    "margin": 0.08,              # gap to runner-up, else AMBIGUOUS
    "w_author": 0.55,
    "w_title": 0.30,
    "w_year": 0.15,
    # 0.90 rejects Howerd/Howard (ratio 0.833), which is the single commonest
    # way a model garbles a surname. 0.85 admits it. Calibrated jointly with
    # everything else -- decoys must still be rejected at this value.
    "fuzzy_surname": 0.85,
}

_STOP = {
    "a", "an", "the", "of", "for", "and", "or", "in", "on", "to", "with",
    "from", "by", "as", "at", "is", "are", "be", "model", "models", "theory",
    "approach", "study", "analysis", "using", "via", "towards", "toward",
    "new", "novel", "general",
}


def norm_tokens(s):
    if not s:
        return []
    toks = re.split(r"[^A-Za-z0-9]+", s.lower())
    return [t for t in toks if t and t not in _STOP and len(t) > 2]


def norm_surname(s):
    if not s:
        return ""
    s = s.strip().lower()
    s = re.sub(r"[^a-z\s'\-]", "", s)
    parts = [p for p in s.split() if p]
    return parts[-1] if parts else ""


def _levenshtein_le1(a, b):
    """True if a and b are within one edit. O(n), no allocation of a matrix."""
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if a == b:
        return True
    if la == lb:                       # one substitution
        diff = 0
        for x, y in zip(a, b):
            if x != y:
                diff += 1
                if diff > 1:
                    return False
        return True
    # one insertion/deletion
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = j = 0
    skipped = False
    while i < la and j < lb:
        if a[i] == b[j]:
            i += 1
            j += 1
        elif skipped:
            return False
        else:
            skipped = True
            j += 1
    return True


def _match_surname(name, pool, thresh):
    """
    Return "exact", "fuzzy", or None.

    A single-character typo in a surname of length >= 5 is admitted as fuzzy.
    SequenceMatcher alone rejects Howerd/Howard (ratio 0.833), which is the
    commonest way a model garbles a name -- but simply dropping the threshold
    to 0.83 would be fitting the constant to one example. The edit-distance
    rule is a statement about typos, not a tuned number.

    Fuzzy matches are NOT silently accepted: they are reported upward and end
    up as an author_spelling discrepancy, i.e. VERIFIED_CORRECTED.
    """
    if not name:
        return None
    if name in pool:
        return "exact"
    for p in pool:
        if not p:
            continue
        if SequenceMatcher(None, name, p).ratio() >= thresh:
            return "fuzzy"
        if len(name) >= 5 and len(p) >= 5 and _levenshtein_le1(name, p):
            return "fuzzy"
    return None


def _fuzzy_in(name, pool, thresh):
    return _match_surname(name, pool, thresh) is not None


# --------------------------------------------------------------------------


@dataclass
class Work:
    """A normalised bibliographic record from any provider."""

    key: str = ""
    title: str = ""
    authors: list = field(default_factory=list)   # surnames, any order
    year: int = None
    venue: str = ""
    doi: str = ""
    url: str = ""
    cited_by: int = 0
    provider: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Score:
    total: float = 0.0
    author_recall: float = 0.0
    title_sim: float = 0.0
    year_sim: float = 0.0
    detail: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


def author_recall(cand_authors, work_authors, thresh, detail=None):
    """Fraction of the CANDIDATE's named authors present on the work."""
    if not cand_authors:
        return 0.0
    pool = [norm_surname(a) for a in work_authors]
    pool = [p for p in pool if p]
    if not pool:
        return 0.0
    hits = 0
    for a in cand_authors:
        kind = _match_surname(norm_surname(a), pool, thresh)
        if kind is not None:
            hits += 1
        if kind == "fuzzy" and detail is not None:
            detail.append(a)
    return hits / float(len(cand_authors))


def title_similarity(hint, work_title):
    """
    Asymmetric containment: how much of the short prose hint is present in the
    (usually longer) real title. Falls back to sequence ratio.
    """
    h = set(norm_tokens(hint))
    w = set(norm_tokens(work_title))
    if not h or not w:
        return 0.0
    contain = len(h & w) / float(len(h))
    seq = SequenceMatcher(None, " ".join(sorted(h)), " ".join(sorted(w))).ratio()
    return max(contain, seq)


def year_similarity(cand_year, work_year):
    if cand_year is None or work_year is None:
        return 0.5           # neutral: prose citations often omit the year
    d = abs(int(cand_year) - int(work_year))
    if d == 0:
        return 1.0
    if d == 1:
        return 0.85          # preprint/journal offset is extremely common
    if d <= 3:
        return 0.4
    return 0.0


def score(cand, work, cfg=None):
    """cand: dict-like with .authors/.year/.title_hint/.topic_hint"""
    c = dict(DEFAULTS)
    if cfg:
        c.update(cfg)

    ca = getattr(cand, "authors", None)
    if ca is None:
        ca = cand.get("authors", [])
    cy = getattr(cand, "year", None) if hasattr(cand, "year") else cand.get("year")
    th = getattr(cand, "title_hint", None) if hasattr(cand, "title_hint") else cand.get("title_hint")
    tp = getattr(cand, "topic_hint", None) if hasattr(cand, "topic_hint") else cand.get("topic_hint")

    fuzzy = []
    ar = author_recall(ca, work.authors, c["fuzzy_surname"], detail=fuzzy)
    # A prose citation may carry a concept name ("Temporal Context Model") or
    # only a topic ("serial position"). Both are weak-but-real title evidence.
    ts_title = title_similarity(th, work.title) if th else 0.0
    ts_topic = title_similarity(tp, work.title) if tp else 0.0
    ts = max(ts_title, 0.85 * ts_topic)
    ys = year_similarity(cy, work.year)

    total = c["w_author"] * ar + c["w_title"] * ts + c["w_year"] * ys

    # Fabrication guard: strong topical match with weak author agreement is the
    # signature of a hallucinated citation landing on a real neighbouring
    # paper. Penalise rather than reward it.
    if ar < 0.5 and ts > 0.6:
        total *= 0.55

    return Score(
        total=round(total, 4),
        author_recall=round(ar, 4),
        title_sim=round(ts, 4),
        year_sim=round(ys, 4),
        detail={"used_title_hint": bool(th), "used_topic_hint": bool(tp),
                "fuzzy_surnames": fuzzy},
    )


def same_work(w1, w2, title_jaccard=0.85):
    """
    Are these two records the SAME paper?

    This exists because of a live failure: three gold citations came back
    AMBIGUOUS with margins of 0.022, 0.022 and 0.000. A margin of exactly zero
    is not two papers fitting equally well -- it is one paper indexed twice.
    OpenAlex and Crossref routinely return the same work with differently
    punctuated titles or a DOI on only one of them, and dedupe by exact key
    misses that.

    Treating a duplicate as a rival is a discrimination failure invented by the
    instrument, so the margin test must skip over duplicates rather than be
    defeated by them.
    """
    d1 = (w1.doi or "").strip().lower()
    d2 = (w2.doi or "").strip().lower()
    if d1 and d2 and d1 == d2:
        return True
    # DO NOT return False on a DOI mismatch. That was the bug in the first
    # version of this function and it is why three perfect-scoring gold
    # citations still came back AMBIGUOUS: a preprint and its published
    # version have DIFFERENT DOIs and are the same work for citation purposes.
    # bioRxiv/Nature (Stachenfeld 2017) and journal/reprint pairs (Bousfield
    # 1953, Raaijmakers 1981) are exactly that case. Distinct DOIs are weak
    # evidence of distinctness, so fall through to the content comparison.
    t1, t2 = set(norm_tokens(w1.title)), set(norm_tokens(w2.title))
    if not t1 or not t2:
        return False
    inter = len(t1 & t2)
    union = len(t1 | t2)
    if union and inter / float(union) >= title_jaccard:
        return True
    # A short title fully contained in a longer one, same first author.
    smaller, larger = (t1, t2) if len(t1) <= len(t2) else (t2, t1)
    if smaller and inter / float(len(smaller)) >= 0.95:
        a1 = [norm_surname(a) for a in (w1.authors or [])][:1]
        a2 = [norm_surname(a) for a in (w2.authors or [])][:1]
        if a1 and a2 and a1[0] == a2[0]:
            return True
    return False


def discrepancies(cand, work, cfg=None):
    """
    Ways the PROSE disagrees with the RECORD, once the record is identified.

    This is a separate question from "is the citation real", and conflating
    them was the first bug this module's own test battery caught: citing
    Polyn, Norman & Kahana (2009) as "Polyn & Kahana" identifies the right
    paper with the wrong author list. Rejecting it would be wrong; accepting it
    silently would put a malformed entry in the bibliography. So it is
    reported, and the status becomes VERIFIED_CORRECTED.
    """
    c = dict(DEFAULTS)
    if cfg:
        c.update(cfg)

    ca = getattr(cand, "authors", None)
    if ca is None:
        ca = cand.get("authors", [])
    cy = getattr(cand, "year", None) if hasattr(cand, "year") else cand.get("year")

    out = []
    if cy is not None and work.year is not None and abs(int(cy) - int(work.year)) > 1:
        out.append({"field": "year", "cited": cy, "record": work.year})

    pool = [norm_surname(a) for a in work.authors if norm_surname(a)]
    missing, misspelt = [], []
    for a in ca:
        kind = _match_surname(norm_surname(a), pool, c["fuzzy_surname"])
        if kind is None:
            missing.append(a)
        elif kind == "fuzzy":
            misspelt.append(a)
    if missing:
        out.append({"field": "authors_not_on_record", "cited": missing,
                    "record": work.authors})
    if misspelt:
        out.append({"field": "author_spelling", "cited": misspelt,
                    "record": work.authors})
    if len(pool) > len(ca):
        out.append({"field": "authors_omitted", "cited": list(ca),
                    "record": work.authors})
    return out


def classify(ranked, cfg=None):
    """
    ranked: list of (Work, Score) sorted desc by Score.total
    returns (status, best_work_or_None, reason)
    """
    c = dict(DEFAULTS)
    if cfg:
        c.update(cfg)

    if not ranked:
        return "UNRESOLVED", None, "no candidate works returned"

    best_w, best_s = ranked[0]

    # Margin against the best DISTINCT rival, not merely the next row. A
    # duplicate record is not a competing interpretation.
    runner = 0.0
    n_dupes = 0
    rival = None
    for w, s in ranked[1:]:
        if same_work(best_w, w):
            n_dupes += 1
            continue
        runner = s.total
        rival = w
        break
    margin = best_s.total - runner
    dupe_note = (" (%d duplicate record(s) skipped)" % n_dupes) if n_dupes else ""

    if best_s.total < c["tau_partial"]:
        return "UNRESOLVED", None, (
            "best score %.3f below tau_partial %.2f" % (best_s.total, c["tau_partial"])
        )

    if best_s.total < c["tau_verified"]:
        return "PARTIAL", best_w, (
            "score %.3f in [%.2f, %.2f) -- plausible but not confirmed"
            % (best_s.total, c["tau_partial"], c["tau_verified"])
        )

    if best_s.author_recall < c["min_author_recall"]:
        return "PARTIAL", best_w, (
            "author recall %.2f < %.2f -- named author(s) missing from record"
            % (best_s.author_recall, c["min_author_recall"])
        )

    if margin < c["margin"]:
        # Name the rival. An AMBIGUOUS verdict that does not say WHAT it is
        # ambiguous with is unactionable -- and in practice the rival is
        # usually a duplicate the dedupe missed, which you cannot diagnose
        # without seeing its title.
        rival_note = ""
        if rival is not None:
            rival_note = " -- rival: %r (%s, doi:%s)" % (
                (rival.title or "")[:70], rival.year or "n.d.",
                rival.doi or "none")
        return "AMBIGUOUS", best_w, (
            "margin %.3f < %.2f -- two DIFFERENT records fit equally well%s%s"
            % (margin, c["margin"], dupe_note, rival_note)
        )

    return "VERIFIED", best_w, ("score %.3f, margin %.3f%s"
                                % (best_s.total, margin, dupe_note))
