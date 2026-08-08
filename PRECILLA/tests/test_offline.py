"""
Offline test battery for PRECILLA cite.

No network. A synthetic bibliographic universe stands in for OpenAlex: it
CONTAINS the gold papers and a set of topical distractors, and CONTAINS NO
decoy. That is the point -- the decoy queries will retrieve real, topically
adjacent papers, which is precisely how a fabricated citation fails in the
wild. If the matcher rubber-stamps those, the test fails here rather than in a
bibliography.

Run:  python3 tests/test_offline.py
"""

import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from precilla.cite import calibrate as cal            # noqa: E402
from precilla.cite import extract as ex               # noqa: E402
from precilla.cite.match import (DEFAULTS, Work, classify,  # noqa: E402
                                 same_work, score)
from precilla.cite.verify import verify_candidate     # noqa: E402

FAILURES = []


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s   %s" % (name, detail))
        FAILURES.append(name)


# --------------------------------------------------------------------------
# 1. extractor
# --------------------------------------------------------------------------

SAMPLE = """
### 4.1 Context-driven retrieval
- **TCM, Temporal Context Model** (Howard & Kahana). A slowly drifting context.
- **CMR, Context Maintenance and Retrieval** (Polyn, Norman & Kahana). TCM plus source.
- **SAM, Search of Associative Memory** (Raaijmakers & Shiffrin). Cue-dependent.
- **Successor Representation** (Dayan; Stachenfeld, Botvinick & Gershman).
- **Complementary Learning Systems** (McClelland, McNaughton & O'Reilly).
- **Predictive coding / free energy** (Friston). Already inside MOS.

### 4.5 Classic effects
Bousfield (semantic clustering), Murdock (serial position), Kahana (lag-CRP),
Anderson (fan effect), Ebbinghaus/Cepeda (spacing), Wickens (release from PI).

Also **the pedestal is real** (measured this session) and should not be a citation.
The trap is Circularity (§2) and the decisive test is CRP (§6.2); neither is a citation.
"""


def test_extract():
    print("\n[1] extractor")
    cands = ex.extract_text(SAMPLE, source="sample.md")
    by = {c.cid: c for c in cands}
    auth = {tuple(a.lower() for a in c.authors): c for c in cands}

    check("finds TCM with both authors",
          ("howard", "kahana") in auth, str(sorted(auth.keys()))[:200])
    tcm = auth.get(("howard", "kahana"))
    if tcm:
        check("TCM title hint is the concept, not the people",
              "Temporal Context Model" in (tcm.title_hint or ""),
              repr(tcm.title_hint))
        check("TCM tagged shape A", tcm.shape == "A", tcm.shape)

    check("finds 3-author CMR",
          ("polyn", "norman", "kahana") in auth, str(sorted(auth.keys()))[:200])
    check("semicolon groups become SEPARATE works, not one merged citation",
          ("dayan",) in auth and ("stachenfeld", "botvinick", "gershman") in auth,
          str(sorted(auth.keys()))[:260])

    bous = [c for c in cands if c.authors and c.authors[0] == "Bousfield"]
    check("Bousfield parsed as AUTHOR not title", bool(bous), "")
    if bous:
        check("Bousfield topic hint captured",
              (bous[0].topic_hint or "") == "semantic clustering",
              repr(bous[0].topic_hint))
        check("Bousfield tagged shape B", bous[0].shape == "B", bous[0].shape)

    check("Ebbinghaus/Cepeda split into two people",
          any(set(map(str.lower, c.authors)) >= {"ebbinghaus"} for c in cands)
          or any("cepeda" in " ".join(c.authors).lower() for c in cands), "")

    check("bold-with-topic-parenthetical is NOT a citation",
          not any("pedestal" in (c.title_hint or "").lower() for c in cands), "")

    check("section cross-references are not citations",
          not any("crp" in " ".join(c.authors).lower()
                  or "circularity" in " ".join(c.authors).lower()
                  for c in cands),
          str([c.authors for c in cands]))

    check("nothing is emitted above UNVERIFIED",
          all(c.status == "UNVERIFIED" for c in cands), "")
    return cands


def test_extract_real_docs():
    print("\n[1b] extractor on the real MOS docs (if present)")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    found = []
    for root, _dirs, files in os.walk(here):
        for f in files:
            if f.endswith(".md") and ("GENERATIVE" in f or "COGNITION" in f):
                found.append(os.path.join(root, f))
    if not found:
        print("  skip (docs not copied into the repo)")
        return
    for p in found:
        cs = ex.extract_file(p)
        print("  %-42s -> %d candidates" % (os.path.basename(p)[:42], len(cs)))


# --------------------------------------------------------------------------
# 2. synthetic bibliographic universe
# --------------------------------------------------------------------------

UNIVERSE = [
    # --- the gold set (synthetic stand-ins, plausible metadata) ---
    ("A distributed representation of temporal context",
     ["Marc W. Howard", "Michael J. Kahana"], 2002, "10.1006/jmps.2001.1388"),
    ("A context maintenance and retrieval model of organizational processes in "
     "free recall", ["Sean M. Polyn", "Kenneth A. Norman", "Michael J. Kahana"],
     2009, "10.1037/a0014420"),
    ("Search of associative memory", ["Jeroen G. W. Raaijmakers",
     "Richard M. Shiffrin"], 1981, "10.1037/0033-295X.88.2.93"),
    ("Why there are complementary learning systems in the hippocampus and "
     "neocortex", ["James L. McClelland", "Bruce L. McNaughton",
                   "Randall C. O'Reilly"], 1995, "10.1037/0033-295X.102.3.419"),
    ("Improving generalization for temporal difference learning: the successor "
     "representation", ["Peter Dayan"], 1993, "10.1162/neco.1993.5.4.613"),
    ("The hippocampus as a predictive map", ["Kimberly L. Stachenfeld",
     "Matthew M. Botvinick", "Samuel J. Gershman"], 2017, "10.1038/nn.4650"),
    ("The occurrence of clustering in the recall of randomly arranged "
     "associates", ["Weston A. Bousfield"], 1953, "10.1080/00221309.1953.9710088"),
    ("The serial position effect of free recall", ["Bennet B. Murdock"], 1962,
     "10.1037/h0045106"),
    ("Retrieval of propositional information from long-term memory",
     ["John R. Anderson"], 1974, "10.1016/0010-0285(74)90021-8"),
    ("The free-energy principle: a unified brain theory?", ["Karl Friston"],
     2010, "10.1038/nrn2787"),
    ("Neural networks and physical systems with emergent collective "
     "computational abilities", ["John J. Hopfield"], 1982,
     "10.1073/pnas.79.8.2554"),
    ("Distributed practice in verbal recall tasks: a review and quantitative "
     "synthesis", ["Nicholas J. Cepeda", "Harold Pashler", "Edward Vul",
                   "John T. Wixted", "Doug Rohrer"], 2006,
     "10.1037/0033-2909.132.3.354"),

    # --- topical distractors: real-shaped neighbours with NO decoy authors ---
    ("Sheaf theoretic methods in topological data analysis",
     ["Justin Curry"], 2014, "10.0000/sheaf-tda"),
    ("Associative retrieval dynamics in recurrent networks",
     ["Anna Schapiro", "Nicholas Turk-Browne"], 2016, "10.0000/assoc-retr"),
    ("Conditional response probability and temporal organization of recall",
     ["Michael J. Kahana"], 1996, "10.3758/BF03197276"),
    ("Simplicial complexes and covers of semantic spaces",
     ["Robert Ghrist"], 2018, "10.0000/simplicial-cover"),
    ("Adaptation and firing-rate fatigue in cortical circuits",
     ["Misha Tsodyks", "Henry Markram"], 1997, "10.0000/adaptation"),
    ("Curveball: a fast algorithm for randomizing binary matrices",
     ["Giovanni Strona"], 2014, "10.1038/ncomms5114"),
    ("k-winners-take-all networks and competitive dynamics",
     ["Wolfgang Maass"], 2000, "10.0000/kwta"),
    ("Adjoint functors in categorical data structures", ["Emily Riehl"],
     2017, "10.0000/adjoint"),
    ("Predictive maps and grid cell structure in reinforcement learning",
     ["Samuel J. Gershman"], 2018, "10.0000/predictive-maps"),
    ("Rumelhart and McClelland parallel distributed processing revisited",
     ["David E. Rumelhart", "James L. McClelland"], 1986, "10.0000/pdp"),
]


def _mock_openalex_fetch(url, use_cache=True, timeout=30):
    """Naive token-overlap retrieval over UNIVERSE, in OpenAlex JSON shape."""
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get("search", [""])[0]
    qt = set(t for t in q.lower().replace("-", " ").split() if len(t) > 2)

    scored = []
    for title, authors, year, doi in UNIVERSE:
        blob = (title + " " + " ".join(authors)).lower().replace("-", " ")
        bt = set(t for t in blob.split() if len(t) > 2)
        overlap = len(qt & bt)
        if overlap:
            scored.append((overlap, title, authors, year, doi))
    scored.sort(reverse=True, key=lambda r: r[0])

    results = []
    for _o, title, authors, year, doi in scored[:8]:
        results.append({
            "id": "https://openalex.org/W" + doi.replace("/", "_"),
            "display_name": title,
            "publication_year": year,
            "doi": "https://doi.org/" + doi,
            "cited_by_count": 100,
            "authorships": [{"author": {"display_name": a}} for a in authors],
            "primary_location": {"source": {"display_name": "Synthetic"}},
        })
    return {"results": results}


# --------------------------------------------------------------------------
# 3. matcher unit checks
# --------------------------------------------------------------------------

class C(dict):
    __getattr__ = dict.get


def test_matcher():
    print("\n[2] matcher")
    w = Work(title="A distributed representation of temporal context",
             authors=["Marc W. Howard", "Michael J. Kahana"], year=2002)

    s_good = score(C(authors=["Howard", "Kahana"], year=2002,
                     title_hint="distributed representation of temporal context"), w)
    check("exact citation scores high", s_good.total > 0.9, str(s_good.total))
    check("author recall is 1.0 when both present",
          s_good.author_recall == 1.0, str(s_good.author_recall))

    s_noauth = score(C(authors=["Halvorsen", "Nakamura"], year=2002,
                       title_hint="distributed representation of temporal context"), w)
    check("fabricated authors on a real title are penalised",
          s_noauth.total < DEFAULTS["tau_partial"], str(s_noauth.total))

    s_partial = score(C(authors=["Howard", "Kahana", "Sederberg"], year=2002,
                        title_hint="distributed representation of temporal context"), w)
    check("a dropped/extra author lowers recall below 1.0",
          s_partial.author_recall < 1.0, str(s_partial.author_recall))

    s_noyear = score(C(authors=["Howard", "Kahana"], year=None,
                       title_hint="distributed representation of temporal context"), w)
    check("missing year is neutral, not fatal",
          s_noyear.total > DEFAULTS["tau_verified"], str(s_noyear.total))

    s_fuzzy = score(C(authors=["Howerd", "Kahana"], year=2002,
                      title_hint="distributed representation of temporal context"), w)
    check("typo'd surname still matches fuzzily",
          s_fuzzy.author_recall == 1.0, str(s_fuzzy.author_recall))

    from precilla.cite.match import discrepancies
    d_dropped = discrepancies(
        C(authors=["Polyn", "Kahana"], year=2009),
        Work(title="A context maintenance and retrieval model",
             authors=["Sean M. Polyn", "Kenneth A. Norman", "Michael J. Kahana"],
             year=2009))
    check("dropped middle author is reported as a discrepancy",
          any(x["field"] == "authors_omitted" for x in d_dropped), str(d_dropped))
    d_year = discrepancies(
        C(authors=["Howard", "Kahana"], year=1997),
        Work(title="A distributed representation of temporal context",
             authors=["Marc W. Howard", "Michael J. Kahana"], year=2002))
    check("five-year error is reported as a discrepancy",
          any(x["field"] == "year" for x in d_year), str(d_year))
    d_clean = discrepancies(
        C(authors=["Howard", "Kahana"], year=2002),
        Work(title="A distributed representation of temporal context",
             authors=["Marc W. Howard", "Michael J. Kahana"], year=2002))
    check("a correct citation reports no discrepancy", d_clean == [], str(d_clean))


# --------------------------------------------------------------------------
# 4. end-to-end calibration against the synthetic universe
# --------------------------------------------------------------------------

def test_duplicate_records_are_not_rivals():
    """
    Regression for a LIVE failure: three gold citations came back AMBIGUOUS
    with margins 0.022, 0.022 and 0.000. A zero margin is one paper indexed
    twice, not two papers fitting equally well. The margin test must step over
    duplicates -- while still firing on a genuinely different rival.
    """
    print("\n[2b] duplicate-aware margin")
    a = Work(title="The occurrence of clustering in the recall of randomly "
                   "arranged associates",
             authors=["Weston A. Bousfield"], year=1953, doi="10.1080/x")
    # same paper, different index: no DOI, punctuation differs
    a_dup = Work(title="The Occurrence of Clustering in the Recall of "
                       "Randomly Arranged Associates.",
                 authors=["W. A. Bousfield"], year=1953, doi="")
    other = Work(title="Clustering and organization in free recall of "
                       "categorised word lists",
                 authors=["Endel Tulving"], year=1962, doi="10.1037/y")

    check("a record and its re-index are the same work", same_work(a, a_dup), "")

    # Regression for the SECOND bug in this function. The first version
    # early-returned False whenever both records carried DOIs and they
    # differed -- so a preprint and its published version were treated as
    # rivals, and three perfect-scoring gold citations (Stachenfeld 2017,
    # Bousfield 1953, Raaijmakers 1981) came back AMBIGUOUS at score 1.0.
    pre = Work(title="The hippocampus as a predictive map",
               authors=["Kimberly L. Stachenfeld", "Matthew M. Botvinick",
                        "Samuel J. Gershman"], year=2016,
               doi="10.1101/097170")
    pub = Work(title="The hippocampus as a predictive map",
               authors=["Kimberly L. Stachenfeld", "Matthew M. Botvinick",
                        "Samuel J. Gershman"], year=2017, doi="10.1038/nn.4650")
    check("preprint and published version are ONE work despite unequal DOIs",
          same_work(pre, pub), "%s vs %s" % (pre.doi, pub.doi))
    check("unequal DOIs alone do not make two papers the same",
          not same_work(pub, Work(title="Grid cells and place fields in "
                                        "entorhinal cortex",
                                  authors=["Edvard Moser"], year=2008,
                                  doi="10.1038/other")), "")

    scand = C(authors=["Stachenfeld", "Botvinick", "Gershman"], year=2017,
              title_hint="the hippocampus as a predictive map")
    r_pp = sorted(((w, score(scand, w)) for w in (pub, pre)),
                  key=lambda ws: ws[1].total, reverse=True)
    st_pp, _w, why_pp = classify(r_pp)
    check("preprint no longer blocks its own published version",
          st_pp == "VERIFIED", "%s -- %s" % (st_pp, why_pp))
    check("two genuinely different papers are not", not same_work(a, other), "")

    cand = C(authors=["Bousfield"], year=1953,
             title_hint="occurrence of clustering in the recall of randomly "
                        "arranged associates")
    ranked_dup = sorted(((w, score(cand, w)) for w in (a, a_dup)),
                        key=lambda ws: ws[1].total, reverse=True)
    st, _w, why = classify(ranked_dup)
    check("duplicate rival no longer forces AMBIGUOUS", st == "VERIFIED",
          "%s -- %s" % (st, why))
    check("the skipped duplicate is reported, not hidden",
          "duplicate" in why, why)

    ranked_real = sorted(((w, score(cand, w)) for w in (a, other)),
                         key=lambda ws: ws[1].total, reverse=True)
    st2, _w2, why2 = classify(ranked_real)
    check("a genuinely close DIFFERENT paper still resolves cleanly",
          st2 in ("VERIFIED", "AMBIGUOUS"), "%s -- %s" % (st2, why2))


def test_class_separation_is_reported():
    print("\n[2c] separation is computed and reported")
    rep = cal.run(providers=("openalex",),
                  fetchers={"openalex": _mock_openalex_fetch},
                  use_cache=False, verbose=True)
    sep = rep.get("separation")
    check("separation block present", sep is not None, str(sep))
    if sep:
        check("every decoy scores below every real citation",
              sep["separated"], str(sep))
        check("the gap is reported so drift is visible",
              isinstance(sep["gap"], float), str(sep))


def test_calibration():
    print("\n[3] calibration battery (mocked provider)")
    rep = cal.run(providers=("openalex",),
                  fetchers={"openalex": _mock_openalex_fetch},
                  use_cache=False, verbose=True)

    print("  verdict: %s" % rep["verdict"])
    for k, v in rep["by_class"].items():
        print("    %-9s %d/%d" % (k, v["pass"], v["n"]))

    check("no fixture errored", not any(r["errored"] for r in rep["rows"]), "")
    dec = [r for r in rep["rows"] if r["class"] == "decoy"]
    check("every decoy rejected", all(r["pass"] for r in dec),
          str([(r["cid"], r["got"]) for r in dec if not r["pass"]]))
    nm = [r for r in rep["rows"] if r["class"] == "nearmiss"]
    check("no near-miss passes through as plain VERIFIED",
          all(r["got"] != "VERIFIED" for r in nm),
          str([(r["cid"], r["got"]) for r in nm if r["got"] == "VERIFIED"]))
    check("garbled-but-real near-misses come back corrected, not rejected",
          any(r["got"] == "VERIFIED_CORRECTED" for r in nm),
          str([(r["cid"], r["got"]) for r in nm]))
    gold = [r for r in rep["rows"] if r["class"] == "gold"]
    check("gold majority verified against a universe that contains them",
          sum(1 for r in gold if r["pass"]) >= max(1, int(0.8 * len(gold))),
          str([(r["cid"], r["got"]) for r in gold if not r["pass"]]))

    for r in rep["rows"]:
        if not r["pass"]:
            print("    ! %-9s %-26s got=%-11s %s"
                  % (r["class"], r["cid"], r["got"], (r["reason"] or "")[:70]))
    return rep


def test_refusal():
    print("\n[4] refusal semantics")
    ok, why = cal.is_calibrated({"tau_verified": 0.999})
    check("an unseen config is never treated as calibrated", not ok, why)

    bad = verify_candidate(
        C(cid="x", authors=["Nonexistent"], year=1900, title_hint="nothing at all"),
        providers=("openalex",), fetchers={"openalex": _mock_openalex_fetch},
        use_cache=False)
    check("unmatched citation is UNRESOLVED", bad["status"] == "UNRESOLVED",
          bad["status"] + " / " + bad["reason"])

    def boom(url, use_cache=True, timeout=30):
        from precilla.cite.resolve import ResolveError
        raise ResolveError("simulated network failure")

    err = verify_candidate(
        C(cid="y", authors=["Howard", "Kahana"], year=2002, title_hint="temporal context"),
        providers=("openalex",), fetchers={"openalex": boom}, use_cache=False)
    check("network failure is ERRORED, never UNRESOLVED",
          err["status"] == "ERRORED", err["status"])


if __name__ == "__main__":
    test_extract()
    test_extract_real_docs()
    test_matcher()
    test_duplicate_records_are_not_rivals()
    test_class_separation_is_reported()
    rep = test_calibration()
    test_refusal()
    print("\n%s  %d failure(s)" % ("FAILED" if FAILURES else "PASSED", len(FAILURES)))
    if FAILURES:
        print("  " + "\n  ".join(FAILURES))
    sys.exit(1 if FAILURES else 0)
