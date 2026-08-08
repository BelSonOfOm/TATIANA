"""
PRECILLA / cite / verify.py

candidate -> providers -> scored works -> epistemic status.

Status vocabulary is deliberately the MOS one, extended:

    VERIFIED     a record exists, all named authors present, unambiguous
    PARTIAL      a record plausibly matches but something did not check out
    AMBIGUOUS    two records fit equally well -- a human must look
    UNRESOLVED   nothing matched.  NOT the same as "does not exist".
    ERRORED      the providers could not be reached

UNRESOLVED vs ERRORED matters more than it looks: a network failure that
silently reads as "citation is fake" would be exactly the class of instrument
artefact the MOS logbook keeps catching.
"""

from __future__ import annotations

from . import resolve as _resolve
from .match import DEFAULTS, Work, classify, discrepancies, score


def dedupe(works):
    """Collapse the same paper arriving from two providers (DOI, else title)."""
    seen, out = {}, []
    for w in works:
        k = (w.doi or "").lower() or ("t:" + " ".join(sorted(
            (w.title or "").lower().split()))[:120])
        if k in seen:
            prev = seen[k]
            if w.cited_by > prev.cited_by:
                prev.cited_by = w.cited_by
            if not prev.doi and w.doi:
                prev.doi = w.doi
            continue
        seen[k] = w
        out.append(w)
    return out


def verify_candidate(cand, providers=("openalex", "crossref"), rows=8,
                     cfg=None, fetchers=None, use_cache=True, keep=3):
    cfg = dict(DEFAULTS, **(cfg or {}))
    works, errors = _resolve.gather(cand, providers=providers, rows=rows,
                                    fetchers=fetchers, use_cache=use_cache)
    works = dedupe(works)

    ranked = sorted(((w, score(cand, w, cfg)) for w in works),
                    key=lambda ws: ws[1].total, reverse=True)

    if not works and errors:
        status, best, reason = "ERRORED", None, "; ".join(errors)
    else:
        status, best, reason = classify(ranked, cfg)

    # The record may be right while the prose is wrong. Say so explicitly
    # rather than folding it into a pass or a fail.
    diffs = discrepancies(cand, best, cfg) if best is not None else []
    if status == "VERIFIED" and diffs:
        status = "VERIFIED_CORRECTED"
        reason = "%s; prose disagrees with record in %s" % (
            reason, ", ".join(d["field"] for d in diffs))

    cid = getattr(cand, "cid", None) or (
        cand.get("cid") if isinstance(cand, dict) else None)
    raw = getattr(cand, "raw", None) or (
        cand.get("raw") if isinstance(cand, dict) else "")

    return {
        "cid": cid,
        "raw": raw,
        "status": status,
        "reason": reason,
        "discrepancies": diffs,
        "n_works": len(works),
        "errors": errors,
        "best": best.to_dict() if best else None,
        "top": [{"work": w.to_dict(), "score": s.to_dict()}
                for w, s in ranked[:keep]],
    }


def to_bibtex(result):
    """
    BibTeX for confirmed results only. Refuses anything weaker, by design.

    VERIFIED_CORRECTED is included -- the entry is built from the RECORD, which
    is exactly why the prose discrepancy does not matter here -- but it carries
    a comment naming the correction so the prose gets fixed too.
    """
    if result.get("status") not in ("VERIFIED", "VERIFIED_CORRECTED"):
        return None
    if not result.get("best"):
        return None
    b = result["best"]
    authors = " and ".join(b.get("authors") or [])
    fields = [
        ("author", authors),
        ("title", b.get("title") or ""),
        ("year", str(b.get("year") or "")),
        ("journal", b.get("venue") or ""),
        ("doi", b.get("doi") or ""),
        ("url", b.get("url") or ""),
    ]
    body = ",\n".join("  %s = {%s}" % (k, v) for k, v in fields if v)
    entry = "@article{%s,\n%s\n}" % (result["cid"], body)
    if result.get("discrepancies"):
        note = "; ".join("%s cited as %r, record says %r"
                         % (d["field"], d.get("cited"), d.get("record"))
                         for d in result["discrepancies"])
        entry = "%% CORRECTED: %s\n%s" % (note[:400], entry)
    return entry
