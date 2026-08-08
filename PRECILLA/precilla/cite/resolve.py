"""
PRECILLA / cite / resolve.py

Turn a prose citation candidate into real bibliographic records.

Providers, all free, all keyless:
  * OpenAlex   -- best coverage + author disambiguation. Polite pool via mailto.
  * Crossref   -- DOI authority, good for journal articles.
  * arXiv      -- preprints OpenAlex sometimes lags on.

Everything is cached to disk. Two reasons, both from the MOS logbook:
  1. a long job whose partial progress is worth nothing is a bug in the job;
  2. a verification result must be reproducible months later, and these APIs
     are live. The cache IS the audit trail.

Network I/O is injected (`fetch_json`) so the matcher can be tested offline.

stdlib only.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from .match import Work

USER_AGENT_TMPL = "PRECILLA/0.1 (+https://github.com/; mailto:%s)"
DEFAULT_MAILTO = os.environ.get("PRECILLA_MAILTO", "")

CACHE_DIR = os.environ.get(
    "PRECILLA_CACHE", os.path.join(os.path.expanduser("~"), ".precilla", "cache")
)

# Be a good citizen; OpenAlex polite pool allows ~10/s but we do not need it.
_MIN_INTERVAL = 0.15
_last_call = [0.0]


class ResolveError(RuntimeError):
    pass


# --------------------------------------------------------------------------
# cache
# --------------------------------------------------------------------------


def _cache_path(url):
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    return os.path.join(CACHE_DIR, h + ".json")


def fetch_json(url, timeout=30, use_cache=True):
    """GET a JSON endpoint, with a permanent on-disk cache."""
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp):
        with open(cp, "r", encoding="utf-8") as fh:
            return json.load(fh)

    dt = time.time() - _last_call[0]
    if dt < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - dt)
    _last_call[0] = time.time()

    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT_TMPL % (DEFAULT_MAILTO or "anon"),
                      "Accept": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise ResolveError("HTTP %s for %s" % (e.code, url))
    except Exception as e:
        raise ResolveError("%s for %s" % (type(e).__name__, url))

    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        tmp = cp + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, cp)
    return data


def fetch_text(url, timeout=30, use_cache=True):
    """GET a text (XML) endpoint, cached as a JSON-wrapped string."""
    cp = _cache_path(url) + ".txt"
    if use_cache and os.path.exists(cp):
        with open(cp, "r", encoding="utf-8") as fh:
            return fh.read()

    dt = time.time() - _last_call[0]
    if dt < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - dt)
    _last_call[0] = time.time()

    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT_TMPL % (DEFAULT_MAILTO or "anon")}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read().decode("utf-8", "replace")
    except Exception as e:
        raise ResolveError("%s for %s" % (type(e).__name__, url))

    if use_cache:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cp, "w", encoding="utf-8") as fh:
            fh.write(data)
    return data


# --------------------------------------------------------------------------
# query construction
# --------------------------------------------------------------------------


def build_query(cand):
    """Free-text query from a candidate: authors + best available hint."""
    authors = getattr(cand, "authors", None)
    if authors is None:
        authors = cand.get("authors", [])
    th = getattr(cand, "title_hint", None) if hasattr(cand, "title_hint") else cand.get("title_hint")
    tp = getattr(cand, "topic_hint", None) if hasattr(cand, "topic_hint") else cand.get("topic_hint")
    bits = list(authors)
    if th:
        bits.append(th)
    elif tp:
        bits.append(tp)
    return " ".join(bits).strip()


# --------------------------------------------------------------------------
# providers -> list[Work]
# --------------------------------------------------------------------------


def _oa_authors(rec):
    out = []
    for a in rec.get("authorships") or []:
        nm = ((a.get("author") or {}).get("display_name")) or ""
        if nm:
            out.append(nm)
    return out


def openalex(cand, rows=8, fetch=None, use_cache=True):
    fetch = fetch or fetch_json
    q = build_query(cand)
    if not q:
        return []
    params = {"search": q, "per-page": str(rows)}
    if DEFAULT_MAILTO:
        params["mailto"] = DEFAULT_MAILTO
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    data = fetch(url, use_cache=use_cache)
    works = []
    for rec in (data.get("results") or []):
        works.append(Work(
            key=rec.get("id") or "",
            title=rec.get("display_name") or "",
            authors=_oa_authors(rec),
            year=rec.get("publication_year"),
            venue=(((rec.get("primary_location") or {}).get("source") or {})
                   .get("display_name") or ""),
            doi=(rec.get("doi") or "").replace("https://doi.org/", ""),
            url=rec.get("id") or "",
            cited_by=rec.get("cited_by_count") or 0,
            provider="openalex",
        ))
    return works


def crossref(cand, rows=8, fetch=None, use_cache=True):
    fetch = fetch or fetch_json
    q = build_query(cand)
    if not q:
        return []
    params = {"query.bibliographic": q, "rows": str(rows)}
    if DEFAULT_MAILTO:
        params["mailto"] = DEFAULT_MAILTO
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    data = fetch(url, use_cache=use_cache)
    works = []
    for rec in ((data.get("message") or {}).get("items") or []):
        title = (rec.get("title") or [""])[0]
        auth = []
        for a in rec.get("author") or []:
            nm = " ".join(x for x in [a.get("given"), a.get("family")] if x)
            if nm:
                auth.append(nm)
        yr = None
        for kk in ("published-print", "published-online", "issued", "created"):
            dp = (rec.get(kk) or {}).get("date-parts")
            if dp and dp[0] and dp[0][0]:
                yr = dp[0][0]
                break
        works.append(Work(
            key=rec.get("DOI") or title,
            title=title,
            authors=auth,
            year=yr,
            venue=(rec.get("container-title") or [""])[0],
            doi=rec.get("DOI") or "",
            url=rec.get("URL") or "",
            cited_by=rec.get("is-referenced-by-count") or 0,
            provider="crossref",
        ))
    return works


def _arxiv_parse(xml):
    import xml.etree.ElementTree as ET
    ns = {"a": "http://www.w3.org/2005/Atom"}
    works = []
    try:
        root = ET.fromstring(xml)
    except Exception:
        return works
    for e in root.findall("a:entry", ns):
        title = (e.findtext("a:title", default="", namespaces=ns) or "").strip()
        pub = (e.findtext("a:published", default="", namespaces=ns) or "")
        yr = int(pub[:4]) if pub[:4].isdigit() else None
        auth = [(a.findtext("a:name", default="", namespaces=ns) or "").strip()
                for a in e.findall("a:author", ns)]
        idu = (e.findtext("a:id", default="", namespaces=ns) or "").strip()
        works.append(Work(
            key=idu, title=title, authors=[a for a in auth if a], year=yr,
            venue="arXiv", doi="", url=idu, cited_by=0, provider="arxiv",
        ))
    return works


def arxiv(cand, rows=8, fetch=None, use_cache=True):
    fetch = fetch or fetch_text
    q = build_query(cand)
    if not q:
        return []
    url = ("http://export.arxiv.org/api/query?"
           + urllib.parse.urlencode({"search_query": "all:" + q,
                                     "max_results": str(rows)}))
    return _arxiv_parse(fetch(url, use_cache=use_cache))


PROVIDERS = {"openalex": openalex, "crossref": crossref, "arxiv": arxiv}


def gather(cand, providers=("openalex", "crossref"), rows=8,
           fetchers=None, use_cache=True):
    """
    Query providers in order, accumulating Works. Provider failure is recorded,
    never fatal -- a network hiccup must not silently downgrade a citation to
    UNRESOLVED without saying so.
    """
    fetchers = fetchers or {}
    works, errors = [], []
    for name in providers:
        fn = PROVIDERS.get(name)
        if fn is None:
            errors.append("unknown provider %s" % name)
            continue
        try:
            works.extend(fn(cand, rows=rows, fetch=fetchers.get(name),
                            use_cache=use_cache))
        except ResolveError as e:
            errors.append("%s: %s" % (name, e))
    return works, errors
