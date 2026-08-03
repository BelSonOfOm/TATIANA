"""Generate a distinct task stream to drive accumulation. No API calls.

Tasks are SENTENCES drawn from the corpus, while the KB's concepts are
PARAGRAPHS from it. The asymmetry is deliberate: a query at the same grain as
the stored unit would mostly retrieve its own source chunk and little else, and
"every tick retrieves exactly one concept" produces no co-activation pair at all.
A sentence is a plausible query, and the paragraph containing it plus its
topical neighbours is a plausible retrieval.

WHAT THIS DOES AND DOES NOT BUY. The queries are drawn from the same corpus as
the concepts, so retrieval is easier than it would be against an outside
question. That inflates how MUCH is retrieved. It does not decide the SHAPE of
what is retrieved, which is what Tier 0 asks about -- whether the co-activation
sets overlap (cover) or partition. Still, it is a limit on the claim and belongs
next to any verdict computed from this stream.

    python make_tasks.py --out tasks.txt --n 3000
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

MIN_WORDS = 6      # shorter than this and the embedding is mostly noise
MAX_WORDS = 40


def sentences_from(path: str):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            raw = fh.read()
    except OSError:
        return
    raw = re.sub(r"\s+", " ", raw)
    for s in re.split(r"(?<=[.!?])\s+", raw):
        s = s.strip(" -*#|`>")
        # Markdown tables, code and rule lines embed badly and are not questions
        # anyone would ask; dropping them keeps the stream a stream of QUERIES.
        if not s or s.count("|") > 2 or s.count("=") > 3:
            continue
        words = s.split()
        if not (MIN_WORDS <= len(words) <= MAX_WORDS):
            continue
        if sum(c.isalpha() for c in s) < len(s) * 0.6:
            continue
        yield s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=os.path.join(os.path.dirname(HERE), "..", "DOCS"))
    ap.add_argument("--patterns", default="*.txt,*.md,*.tex")
    ap.add_argument("--out", default=os.path.join(HERE, "tasks.txt"))
    ap.add_argument("--n", type=int, default=3000)
    args = ap.parse_args()

    source = os.path.abspath(args.source)
    seen, tasks = set(), []
    for pat in (p.strip() for p in args.patterns.split(",")):
        for path in sorted(glob.glob(os.path.join(source, pat))):
            for s in sentences_from(path):
                key = s.lower()
                if key in seen:
                    continue
                seen.add(key)
                tasks.append(s)

    print(f"[tasks] distinct sentences found: {len(tasks)}")
    if len(tasks) < args.n:
        # Reported, never padded. Cycling is accumulate.py's decision to warn
        # about; silently repeating here would hide it one layer deeper.
        print(f"[tasks] WARNING: only {len(tasks)} available, {args.n} requested. "
              "Writing what exists -- accumulate.py will warn about cycling.")
    tasks = tasks[:args.n]

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(f"# {len(tasks)} distinct tasks from {source}\n")
        fh.write("# sentence-grain queries against paragraph-grain concepts\n")
        for t in tasks:
            fh.write(t + "\n")
    print(f"[tasks] wrote {len(tasks)} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
