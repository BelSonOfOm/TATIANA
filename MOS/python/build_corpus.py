"""Build the concept/query corpus LOCALLY. Replaces colab_prepare_corpus.ipynb.

WHY THIS EXISTS. Colab was chosen (5ap) for ONE reason: not uploading DOCS/ to
Google. 5ap then changed the corpus to PUBLIC arXiv abstracts, which dissolved
that reason -- leaving Colab contributing only the file hand-off friction that
broke the 2026-08-03 session (5at). Everything here runs on the local machine:
no upload, no browser download, no npz hand-carry.

Emits the same three artefacts the notebook did, under the same names, so every
downstream consumer is unchanged:
    concepts.npz          names, texts, vectors   (the KB)
    queries.npz           texts, vectors          (one per tick)
    corpus_manifest.json  provenance + the stated limits

THE STATED LIMIT, CARRIED IN THE MANIFEST (5ap): query sentences are drawn from
the same abstracts that became concepts. Every query therefore retrieves its own
source abstract at rank 1. That inflates HOW MUCH is retrieved; it does not
decide the SHAPE of what is retrieved, which is what Tier 0 asks -- but it
belongs beside any verdict.

Cross-listing is recorded for inspection ONLY. It is never shown to any model and
never used as ground truth (5ap).

    python build_corpus.py --per-cat 190 --queries 3000
"""
from __future__ import annotations

# Thread cap BEFORE onnxruntime is imported -- it reads these at session
# creation, so setting them later does nothing. This is the fix from the ingest
# that pegged every core and lost a 10-minute run (5ap).
import os
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("ONNXRUNTIME_NUM_THREADS", "2")

import argparse
import json
import re
import sys
import time
import urllib.parse
from typing import Dict, List

import numpy as np
import requests

ARXIV_API = "http://export.arxiv.org/api/query"
CATEGORIES = ["math.AT", "math.DG", "math-ph", "quant-ph", "math.PR", "stat.ML"]
POLITE_DELAY = 3.0
PAGE = 100                      # arXiv's practical page size

_ENTRY = re.compile(r"<entry>(.*?)</entry>", re.DOTALL)
_ID = re.compile(r"<id>http://arxiv\.org/abs/([^<]+)</id>")
_SUMMARY = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
_TITLE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
_CAT = re.compile(r'<category term="([^"]+)"')


def clean(s: str) -> str:
    s = s.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    return re.sub(r"\s+", " ", s).strip()


def fetch_category(cat: str, n: int, session: requests.Session) -> List[Dict]:
    out: List[Dict] = []
    for start in range(0, n, PAGE):
        q = urllib.parse.urlencode({
            "search_query": f"cat:{cat}",
            "start": start,
            "max_results": min(PAGE, n - start),
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        })
        try:
            r = session.get(f"{ARXIV_API}?{q}", timeout=60)
            r.raise_for_status()
        except Exception as exc:
            print(f"    ! {cat} start={start}: {exc}", file=sys.stderr)
            time.sleep(POLITE_DELAY)
            continue
        for block in _ENTRY.findall(r.text):
            mid, msum = _ID.search(block), _SUMMARY.search(block)
            mtitle = _TITLE.search(block)
            if not (mid and msum):
                continue
            cats = _CAT.findall(block)
            out.append({"id": mid.group(1),
                        "title": clean(mtitle.group(1)) if mtitle else "",
                        "abstract": clean(msum.group(1)),
                        "primary": cat,
                        "categories": cats})
        time.sleep(POLITE_DELAY)
    return out


_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def sentences(text: str) -> List[str]:
    return [s.strip() for s in _SENT.split(text)
            if 40 <= len(s.strip()) <= 400]


def embed(texts: List[str], label: str, batch: int = 64) -> np.ndarray:
    from fastembed import TextEmbedding
    print(f"[corpus] embedding {len(texts)} {label} (bge-small, 2 threads)")
    model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5", threads=2)
    out = []
    for i in range(0, len(texts), batch):
        out.extend(model.embed(texts[i:i + batch]))
        print(f"\r[corpus]   {min(i+batch, len(texts))}/{len(texts)}",
              end="", flush=True)
    print()
    V = np.asarray(out, dtype=np.float64)
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    return V


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-cat", type=int, default=190)
    ap.add_argument("--queries", type=int, default=3000)
    ap.add_argument("--categories", default=",".join(CATEGORIES))
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "TATIANA-MOS/0.1 (research; contact via arXiv)"

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    papers: Dict[str, Dict] = {}
    for cat in cats:
        got = fetch_category(cat, args.per_cat, session)
        print(f"[corpus] {cat}: {len(got)} abstracts")
        for p in got:
            papers.setdefault(p["id"], p)          # dedupe cross-listed papers

    docs = list(papers.values())
    if not docs:
        print("[corpus] FATAL: no abstracts fetched", file=sys.stderr)
        return 1

    cross = sum(1 for d in docs if len(set(d["categories"]) & set(cats)) > 1)
    print(f"[corpus] {len(docs)} distinct abstracts, "
          f"{100.0*cross/len(docs):.1f}% cross-listed within our six categories")

    # Queries: sentences drawn from the abstracts, round-robin across papers so
    # no single paper dominates the tick stream.
    rng = np.random.default_rng(args.seed)
    pool: List[List[str]] = [sentences(d["abstract"]) for d in docs]
    order = rng.permutation(len(docs))
    qtexts, qsrc, depth = [], [], 0
    while len(qtexts) < args.queries:
        added = False
        for i in order:
            if depth < len(pool[i]):
                qtexts.append(pool[i][depth])
                qsrc.append(docs[i]["id"])
                added = True
                if len(qtexts) >= args.queries:
                    break
        if not added:
            break
        depth += 1
    print(f"[corpus] {len(qtexts)} query sentences (requested {args.queries})")
    if len(qtexts) < args.queries:
        print(f"[corpus] WARNING: only {len(qtexts)} distinct sentences available. "
              "Tier 0's power curve is quoted at T=1500/3000; fewer ticks means "
              "less power, and that belongs beside the verdict.")

    CV = embed([d["abstract"] for d in docs], "abstracts")
    QV = embed(qtexts, "query sentences")

    cpath = os.path.join(args.outdir, "concepts.npz")
    qpath = os.path.join(args.outdir, "queries.npz")
    np.savez_compressed(cpath,
                        names=np.array([d["id"] for d in docs], dtype=object),
                        texts=np.array([d["abstract"] for d in docs], dtype=object),
                        vectors=CV)
    np.savez_compressed(qpath,
                        texts=np.array(qtexts, dtype=object),
                        sources=np.array(qsrc, dtype=object),
                        vectors=QV)

    manifest = {
        "built": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "built_by": "build_corpus.py (LOCAL -- replaces colab_prepare_corpus.ipynb)",
        "model": "BAAI/bge-small-en-v1.5", "dim": int(CV.shape[1]),
        "categories": cats, "n_concepts": len(docs), "n_queries": len(qtexts),
        "cross_listed_frac": cross / len(docs),
        "per_category_requested": args.per_cat,
        "cross_listing_use": "RECORDED FOR INSPECTION ONLY -- never shown to a "
                             "model, never used as ground truth (5ap).",
        "stated_limit": "Query sentences are drawn from the same abstracts that "
                        "became concepts, so every query retrieves its own source "
                        "at rank 1. This inflates HOW MUCH is retrieved; it does "
                        "not decide the SHAPE, which is what Tier 0 asks. Report "
                        "it beside any verdict.",
        "papers": [{"id": d["id"], "primary": d["primary"],
                    "categories": d["categories"]} for d in docs],
    }
    mpath = os.path.join(args.outdir, "corpus_manifest.json")
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"[corpus] norms in [{np.linalg.norm(CV,axis=1).min():.4f}, "
          f"{np.linalg.norm(CV,axis=1).max():.4f}]")
    print(f"[corpus] wrote {cpath}, {qpath}, {mpath}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
