"""Extract GROUND-TRUTH relatedness labels from arXiv LaTeX source.

WHY THIS EXISTS. Every claim about retrieval quality in DOCS/THE_RETRIEVAL_PROBLEM.md
rested on ONE hand-checked pair. That makes every proposed fix unfalsifiable: we
cannot tell a good retrieval rule from a bad one. This script manufactures labels
at scale, for free, with no hand-annotation and no LLM budget.

THE IDEA. A paper's own cross-references ARE relatedness labels. When a proof
writes "by Lemma 3.2", the author has asserted that this block depends on that
block. `\\label` / `\\ref` pairs in the LaTeX source give an explicit dependency
graph over text blocks.

WHAT THE LABELS ARE AND ARE NOT -- stated so no one over-reads them:
  * HIGH PRECISION. If a proof cites Lemma 3.2, they really are related.
  * LOW RECALL. Most real dependencies are implicit and never get a \\ref.
  => They are excellent POSITIVES and unusable NEGATIVES. A retrieval rule that
     ranks \\ref targets highly is good; one that ranks a non-referenced block
     highly is NOT thereby wrong. Every metric downstream must be recall-style
     (where does the known-positive land?), never precision-style.

BLOCK DEFINITION (a choice, not a discovery):
  * theorem-like labelled environments (theorem/lemma/proposition/corollary/
    definition/remark/example/conjecture) -- their bodies are well-delimited and
    are prose, which is what an embedding model can represent.
  * labelled \\section / \\subsection -- prose up to the next sectioning command,
    truncated.
  * Equation labels are EXCLUDED. Their content is pure math; bge-small has no
    meaningful representation of it, so including them would measure the
    tokenizer rather than the retrieval rule.

    python extract_refs.py --per-cat 12 --out refs_corpus.json
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import os
import re
import sys
import tarfile
import time
import urllib.parse
from typing import Dict, List, Optional, Tuple

import requests

ARXIV_API = "http://export.arxiv.org/api/query"
EPRINT = "https://arxiv.org/e-print/{}"

# Same six deliberately-overlapping categories as the concept corpus (5ap), so
# this labelled set and that corpus describe the same population.
CATEGORIES = ["math.AT", "math.DG", "math-ph", "quant-ph", "math.PR", "stat.ML"]

THEOREM_ENVS = ("theorem", "lemma", "proposition", "corollary", "definition",
                "remark", "example", "conjecture", "claim", "fact", "problem")

# arXiv asks for >=3s between programmatic requests. Respected, not worked around.
POLITE_DELAY = 3.0


# ----------------------------------------------------------------- fetching --

def list_papers(category: str, n: int, session: requests.Session) -> List[str]:
    """Recent arXiv ids in a category."""
    q = urllib.parse.urlencode({
        "search_query": f"cat:{category}",
        "start": 0,
        "max_results": n,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    r = session.get(f"{ARXIV_API}?{q}", timeout=30)
    r.raise_for_status()
    ids = re.findall(r"<id>http://arxiv\.org/abs/([^<]+)</id>", r.text)
    return ids


def fetch_source(arxiv_id: str, cache_dir: str,
                 session: requests.Session) -> Optional[bytes]:
    """The e-print tarball, cached so re-runs cost nothing."""
    safe = arxiv_id.replace("/", "_")
    path = os.path.join(cache_dir, f"{safe}.bin")
    if os.path.exists(path):
        with open(path, "rb") as fh:
            return fh.read()
    try:
        r = session.get(EPRINT.format(arxiv_id), timeout=60)
        if r.status_code != 200 or not r.content:
            return None
        with open(path, "wb") as fh:
            fh.write(r.content)
        time.sleep(POLITE_DELAY)
        return r.content
    except Exception as exc:                                   # network, not logic
        print(f"    ! fetch failed {arxiv_id}: {exc}", file=sys.stderr)
        return None


def tex_from_source(blob: bytes) -> str:
    """Concatenate every .tex in the e-print. Handles the three shapes arXiv
    actually serves: a tar.gz, a bare gzipped .tex, and a PDF-only submission
    (which has no source and is skipped)."""
    if blob[:4] == b"%PDF":
        return ""
    # tar.gz
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
            parts = []
            for m in tf.getmembers():
                if m.isfile() and m.name.lower().endswith(".tex"):
                    f = tf.extractfile(m)
                    if f:
                        parts.append(f.read().decode("utf-8", errors="ignore"))
            if parts:
                return "\n".join(parts)
    except Exception:
        pass
    # bare .gz of a single .tex
    try:
        return gzip.decompress(blob).decode("utf-8", errors="ignore")
    except Exception:
        pass
    try:
        return blob.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# ------------------------------------------------------------------ parsing --

_COMMENT = re.compile(r"(?<!\\)%.*?$", re.MULTILINE)
_LABEL = re.compile(r"\\label\s*\{([^}]*)\}")
_REF = re.compile(r"\\(?:auto|c|C|eq|page)?ref\s*\*?\s*\{([^}]*)\}")
_INPUT = re.compile(r"\\(?:input|include)\s*\{[^}]*\}")


def strip_latex(s: str) -> str:
    """Reduce LaTeX to something an English embedding model can read. This is
    lossy ON PURPOSE -- maths becomes a placeholder rather than tokeniser noise."""
    s = _COMMENT.sub("", s)
    s = re.sub(r"\\begin\{(equation|align|gather|multline|eqnarray)\*?\}.*?"
               r"\\end\{\1\*?\}", " MATH ", s, flags=re.DOTALL)
    s = re.sub(r"\$\$.*?\$\$", " MATH ", s, flags=re.DOTALL)
    s = re.sub(r"\$[^$]{1,200}\$", " MATH ", s)
    s = _LABEL.sub("", s)
    s = _REF.sub(" REF ", s)
    s = re.sub(r"\\cite[tp]?\s*\*?\s*(\[[^\]]*\])?\s*\{[^}]*\}", " CITE ", s)
    s = re.sub(r"\\(?:emph|textit|textbf|text|mathrm|mathbf|mathcal)\s*\{([^{}]*)\}",
               r"\1", s)
    s = re.sub(r"\\begin\{[^}]*\}(\[[^\]]*\])?", " ", s)
    s = re.sub(r"\\end\{[^}]*\}", " ", s)
    s = re.sub(r"\\[a-zA-Z]+\s*", " ", s)
    s = re.sub(r"[{}\\&~^_]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def find_environments(tex: str) -> List[Tuple[str, int, int, str]]:
    """(env_name, body_start, body_end, body) for theorem-like environments.
    Nesting is handled by counting begin/end of the SAME environment name."""
    out = []
    for env in THEOREM_ENVS:
        pat = re.compile(r"\\begin\{(" + env + r"\*?)\}", re.IGNORECASE)
        for m in pat.finditer(tex):
            name = m.group(1)
            depth, pos = 1, m.end()
            begin_re = re.compile(r"\\begin\{" + re.escape(name) + r"\}")
            end_re = re.compile(r"\\end\{" + re.escape(name) + r"\}")
            while depth > 0 and pos < len(tex):
                nb, ne = begin_re.search(tex, pos), end_re.search(tex, pos)
                if ne is None:
                    break
                if nb is not None and nb.start() < ne.start():
                    depth += 1
                    pos = nb.end()
                else:
                    depth -= 1
                    pos = ne.end()
                    if depth == 0:
                        out.append((env.lower(), m.end(), ne.start(),
                                    tex[m.end():ne.start()]))
    return out


def find_sections(tex: str, max_chars: int) -> List[Tuple[str, int, int, str]]:
    """Labelled sectioning commands, with prose up to the next sectioning command."""
    sec = re.compile(r"\\(sub)?(sub)?section\s*\*?\s*\{([^}]*)\}")
    marks = [(m.start(), m.end(), m.group(3)) for m in sec.finditer(tex)]
    out = []
    for i, (s0, s1, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(tex)
        body = tex[s1:end][:max_chars]
        out.append(("section", s1, end, f"{title}. {body}"))
    return out


def parse_paper(arxiv_id: str, tex: str, max_chars: int) -> Tuple[List[Dict], List[Dict]]:
    """Blocks (labelled, prose-bearing) and the \\ref edges between them."""
    tex = _INPUT.sub(" ", tex)
    candidates = find_environments(tex) + find_sections(tex, max_chars)

    blocks: List[Dict] = []
    label_to_block: Dict[str, str] = {}

    for kind, b0, b1, body in candidates:
        lab = _LABEL.search(body)
        if not lab:
            continue                       # unlabelled: nothing can point at it
        label = lab.group(1).strip()
        if not label or label in label_to_block:
            continue                       # duplicate label: ambiguous, drop
        text = strip_latex(body)[:max_chars]
        if len(text.split()) < 12:
            continue                       # too short to embed meaningfully
        bid = f"{arxiv_id}::{label}"
        label_to_block[label] = bid
        # `pos` and `doclen` are kept so a STRUCTURAL bridging label can be built
        # later: a block cited from two DISTANT parts of a paper serves two parts
        # of the argument. That label must not be computed from the embeddings,
        # or it would be circular with the score it is used to validate.
        blocks.append({"id": bid, "paper": arxiv_id, "kind": kind,
                       "label": label, "text": text,
                       "pos": int(b0), "doclen": int(len(tex)),
                       "_span": (b0, b1)})

    edges: List[Dict] = []
    for blk in blocks:
        b0, b1 = blk.pop("_span")
        for m in _REF.finditer(tex[b0:b1]):
            tgt = label_to_block.get(m.group(1).strip())
            if tgt and tgt != blk["id"]:
                # src_pos travels with the edge so a target's citers can be
                # located in the document without a second lookup.
                edges.append({"src": blk["id"], "dst": tgt, "src_pos": int(b0)})

    seen, uniq = set(), []
    for e in edges:
        k = (e["src"], e["dst"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    return blocks, uniq


# --------------------------------------------------------------------- main --

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-cat", type=int, default=12)
    ap.add_argument("--categories", default=",".join(CATEGORIES))
    ap.add_argument("--max-chars", type=int, default=1200)
    ap.add_argument("--cache", default=os.path.join(os.path.dirname(__file__),
                                                    ".arxiv_src_cache"))
    ap.add_argument("--out", default="refs_corpus.json")
    args = ap.parse_args()

    os.makedirs(args.cache, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "TATIANA-MOS/0.1 (research; contact via arXiv)"

    cats = [c.strip() for c in args.categories.split(",") if c.strip()]
    all_blocks: List[Dict] = []
    all_edges: List[Dict] = []
    stats = []

    for cat in cats:
        print(f"[refs] {cat}: listing {args.per_cat} papers")
        try:
            ids = list_papers(cat, args.per_cat, session)
        except Exception as exc:
            print(f"    ! listing failed: {exc}", file=sys.stderr)
            continue
        time.sleep(POLITE_DELAY)
        nb = ne = npapers = 0
        for aid in ids:
            blob = fetch_source(aid, args.cache, session)
            if not blob:
                continue
            tex = tex_from_source(blob)
            if not tex.strip():
                continue
            blocks, edges = parse_paper(aid, tex, args.max_chars)
            if not blocks:
                continue
            for b in blocks:
                b["category"] = cat
            all_blocks.extend(blocks)
            all_edges.extend(edges)
            nb += len(blocks)
            ne += len(edges)
            npapers += 1
        stats.append({"category": cat, "papers": npapers, "blocks": nb, "edges": ne})
        print(f"    -> {npapers} papers, {nb} blocks, {ne} ref-edges")

    ids_seen = {b["id"] for b in all_blocks}
    all_edges = [e for e in all_edges
                 if e["src"] in ids_seen and e["dst"] in ids_seen]

    payload = {"blocks": all_blocks, "edges": all_edges, "stats": stats,
               "note": "ref-edges are HIGH-PRECISION POSITIVES ONLY; absence of "
                       "an edge is NOT evidence of unrelatedness."}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)

    kinds: Dict[str, int] = {}
    for b in all_blocks:
        kinds[b["kind"]] = kinds.get(b["kind"], 0) + 1
    print(f"\n[refs] TOTAL {len(all_blocks)} blocks, {len(all_edges)} edges")
    print(f"[refs] block kinds: {dict(sorted(kinds.items(), key=lambda x: -x[1]))}")
    print(f"[refs] wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
