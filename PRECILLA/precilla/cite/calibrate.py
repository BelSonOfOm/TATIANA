"""
PRECILLA / cite / calibrate.py

The positive control for the citation instrument.

MOS discipline rule 3, applied verbatim: an instrument is used only after it
passes gold + nearmiss + decoy AT ONE SHARED PARAMETER SETTING. Tuning a
threshold per class is the same error as reading an optimum off a flat sweep.

`precilla cite verify` refuses to promote anything to VERIFIED unless a passing
calibration stamp exists for the current config hash. Change a weight, and the
stamp is invalidated -- you must re-earn it.
"""

from __future__ import annotations

import hashlib
import json
import os
import time

from .match import DEFAULTS
from .verify import verify_candidate

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures.json")
STAMP_DIR = os.environ.get(
    "PRECILLA_STATE", os.path.join(os.path.expanduser("~"), ".precilla"))
STAMP = os.path.join(STAMP_DIR, "cite_calibration.json")

# What each class is allowed to produce. One shared config, three acceptance
# criteria -- the criteria differ, the PARAMETERS do not.
ACCEPT = {
    # Gold must verify CLEANLY: right record, and prose that agrees with it.
    "gold": {"VERIFIED"},
    # A near-miss must never pass through unremarked. It may be rejected, or
    # accepted-with-a-correction, but it may not come back plain VERIFIED.
    "nearmiss": {"VERIFIED_CORRECTED", "PARTIAL", "AMBIGUOUS", "UNRESOLVED"},
    # A fabricated citation must never reach a status that produces BibTeX.
    #
    # This was {"UNRESOLVED"} until a live run: the constructed citation
    # "Marchetti (2018), curveball randomization for cognitive co-activation
    # graphs" scored 0.664 and landed in PARTIAL. Inspection showed why -- a
    # REAL author named Marchetti has REAL papers in an adjacent area. There is
    # no honest way to call that "nothing matched": something did match, it just
    # is not the cited work.
    #
    # PARTIAL is therefore the correct answer, and it is safe: `to_bibtex`
    # refuses anything below VERIFIED, so a PARTIAL can never enter a
    # bibliography. Raising tau_partial past 0.664 instead would have been
    # fitting a threshold to a single example -- rule 7 -- and would have
    # dragged genuine citations down with it.
    #
    # The teeth are preserved by SEPARATION below: an instrument that answers
    # PARTIAL to everything now fails, because gold must still reach VERIFIED
    # and every decoy must score strictly below every gold.
    "decoy": {"UNRESOLVED", "PARTIAL"},
}

# Statuses that can put an entry in a bibliography. A decoy reaching any of
# these is a total failure of the instrument, not a tuning problem.
FATAL_FOR_DECOY = {"VERIFIED", "VERIFIED_CORRECTED", "AMBIGUOUS"}


def config_hash(cfg):
    s = json.dumps(cfg, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def load_fixtures(path=None):
    with open(path or FIXTURES, "r", encoding="utf-8") as fh:
        return json.load(fh)


class _F(dict):
    """Fixture rows are dicts; give them attribute access like Candidate."""
    __getattr__ = dict.get


def run(cfg=None, providers=("openalex", "crossref"), fixtures_path=None,
        fetchers=None, use_cache=True, verbose=False):
    cfg = dict(DEFAULTS, **(cfg or {}))
    fx = load_fixtures(fixtures_path)

    rows, counts = [], {}
    for cls in ("gold", "nearmiss", "decoy"):
        for item in fx.get(cls, []):
            cand = _F(item)
            cand["raw"] = item.get("cid", "")
            res = verify_candidate(cand, providers=providers, cfg=cfg,
                                   fetchers=fetchers, use_cache=use_cache)
            ok = res["status"] in ACCEPT[cls]
            counts[(cls, res["status"])] = counts.get((cls, res["status"]), 0) + 1
            top = (res.get("top") or [{}])[0]
            rows.append({
                "class": cls,
                "cid": item.get("cid"),
                "expected": sorted(ACCEPT[cls]),
                "got": res["status"],
                "pass": ok,
                "score": (top.get("score") or {}).get("total"),
                "author_recall": (top.get("score") or {}).get("author_recall"),
                "title_sim": (top.get("score") or {}).get("title_sim"),
                "reason": res["reason"],
                "best_title": (res["best"] or {}).get("title"),
                "best_doi": (res["best"] or {}).get("doi"),
                "best_year": (res["best"] or {}).get("year"),
                "errored": res["status"] == "ERRORED",
            })

    by_class = {}
    for cls in ("gold", "nearmiss", "decoy"):
        sub = [r for r in rows if r["class"] == cls]
        n = len(sub)
        p = sum(1 for r in sub if r["pass"])
        by_class[cls] = {"n": n, "pass": p,
                         "rate": round(p / n, 3) if n else None}

    errored = [r for r in rows if r["errored"]]
    decoy_fail = [r for r in rows if r["class"] == "decoy" and not r["pass"]]
    gold_fail = [r for r in rows if r["class"] == "gold" and not r["pass"]]
    decoy_fatal = [r for r in rows
                   if r["class"] == "decoy" and r["got"] in FATAL_FOR_DECOY]

    # SEPARATION: the real discrimination test. Every fabricated citation must
    # score strictly below every real one. This is a property of the ordering,
    # not of any threshold, so it cannot be satisfied by moving a constant --
    # which is exactly why it replaces the absolute decoy cutoff.
    def _scores(cls):
        return [r["score"] for r in rows
                if r["class"] == cls and isinstance(r["score"], (int, float))]

    gold_scores, decoy_scores = _scores("gold"), _scores("decoy")
    sep = None
    if gold_scores and decoy_scores:
        sep = {
            "min_gold": round(min(gold_scores), 4),
            "max_decoy": round(max(decoy_scores), 4),
            "gap": round(min(gold_scores) - max(decoy_scores), 4),
            "separated": min(gold_scores) > max(decoy_scores),
        }

    # A run with network errors is INCONCLUSIVE, never a pass and never a fail.
    if errored:
        verdict = "INCONCLUSIVE"
        note = ("%d fixtures could not reach a provider; a network failure is "
                "not evidence about a citation" % len(errored))
    elif decoy_fatal:
        verdict = "FAIL"
        note = ("%d/%d fabricated citations reached a bibliography-producing "
                "status (%s) -- the instrument MUST NOT be used"
                % (len(decoy_fatal), by_class["decoy"]["n"],
                   ", ".join(sorted({r["got"] for r in decoy_fatal}))))
    elif decoy_fail:
        verdict = "FAIL"
        note = ("%d/%d decoys were not rejected -- the instrument accepts "
                "fabricated citations and MUST NOT be used"
                % (len(decoy_fail), by_class["decoy"]["n"]))
    elif sep and not sep["separated"]:
        verdict = "FAIL"
        note = ("classes overlap: a fabricated citation scored %.3f, above the "
                "weakest real one at %.3f. No threshold can fix an ordering "
                "failure." % (sep["max_decoy"], sep["min_gold"]))
    elif gold_fail:
        verdict = "FAIL"
        note = ("%d/%d gold citations did not verify; ambiguous between a bad "
                "seed fixture and a bad resolver -- inspect before tuning"
                % (len(gold_fail), by_class["gold"]["n"]))
    elif by_class["nearmiss"]["rate"] not in (None, 1.0):
        verdict = "FAIL"
        note = "a garbled citation reached VERIFIED"
    else:
        verdict = "PASS"
        note = ("gold verified, near-misses caught, decoys held below every "
                "real citation at one shared setting"
                + (" (separation gap %.3f)" % sep["gap"] if sep else ""))

    report = {
        "verdict": verdict,
        "note": note,
        "separation": sep,
        "config_hash": config_hash(cfg),
        "config": cfg,
        "providers": list(providers),
        "by_class": by_class,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "rows": rows if verbose else [r for r in rows if not r["pass"]],
        "n_rows": len(rows),
    }
    return report


def write_stamp(report):
    os.makedirs(STAMP_DIR, exist_ok=True)
    with open(STAMP, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return STAMP


def read_stamp():
    if not os.path.exists(STAMP):
        return None
    try:
        with open(STAMP, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def is_calibrated(cfg=None):
    """(bool, explanation) -- may this instrument emit VERIFIED right now?"""
    cfg = dict(DEFAULTS, **(cfg or {}))
    st = read_stamp()
    if st is None:
        return False, ("no calibration stamp; run `precilla cite calibrate` "
                       "before trusting any VERIFIED result")
    if st.get("verdict") != "PASS":
        return False, "last calibration verdict was %s: %s" % (
            st.get("verdict"), st.get("note"))
    if st.get("config_hash") != config_hash(cfg):
        return False, ("config changed since calibration (%s -> %s); the stamp "
                       "does not transfer" % (st.get("config_hash"),
                                              config_hash(cfg)))
    return True, "calibrated %s" % st.get("timestamp")


def promote(report, fixtures_path=None):
    """
    After a PASS, write the resolved DOI/year back into the gold fixtures and
    flip seed_status UNVERIFIED SEED -> MEASURED. This is the only mechanism by
    which model-knowledge citations in this repo become authoritative.
    """
    if report.get("verdict") != "PASS":
        return {"promoted": 0, "reason": "refusing to promote a non-PASS run"}
    path = fixtures_path or FIXTURES
    fx = load_fixtures(path)
    got = {r["cid"]: r for r in report.get("rows", []) if r.get("pass")}
    n = 0
    for item in fx.get("gold", []):
        r = got.get(item.get("cid"))
        if not r:
            continue
        if r.get("best_doi"):
            item["doi"] = r["best_doi"]
        if r.get("best_year"):
            item["year"] = r["best_year"]
        item["seed_status"] = "MEASURED"
        item["resolved_title"] = r.get("best_title")
        n += 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fx, fh, indent=2)
    return {"promoted": n, "path": path,
            "note": "promotion requires --verbose rows to be present"}
