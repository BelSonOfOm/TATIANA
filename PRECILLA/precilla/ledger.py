"""
PRECILLA / ledger.py

Append-only JSONL record of everything PRECILLA concluded.

Two jobs:

1. AUDIT. Every VERIFIED citation, every calibration verdict, every derivation
   step lands here with a timestamp and the config that produced it. "Log as
   decisions land, not at session end" -- MOS discipline rule 8.

2. FLAT CONTEXT. This is the file you resend to a model instead of a growing
   chat transcript. `ledger.digest()` emits a compact state block: current
   assumptions, notation, verified sources, open questions. Context stays flat
   instead of quadratic, which is the single largest cost lever in the whole
   system -- it matters more than which model you pick.
"""

from __future__ import annotations

import json
import os
import time

LEDGER_DIR = os.environ.get(
    "PRECILLA_STATE", os.path.join(os.path.expanduser("~"), ".precilla"))
LEDGER = os.path.join(LEDGER_DIR, "ledger.jsonl")

# Epistemic vocabulary, from the MOS convention. `append` rejects anything else
# so a claim cannot enter the record untagged.
TAGS = {"MEASURED", "DERIVED", "INFERRED", "ENGINEERING CHOICE",
        "OPEN HYPOTHESIS", "SPECULATION", "UNVERIFIED"}


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append(kind, tag, payload, path=None):
    if tag not in TAGS:
        raise ValueError("unknown epistemic tag %r; must be one of %s"
                         % (tag, sorted(TAGS)))
    path = path or LEDGER
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rec = {"ts": _now(), "kind": kind, "tag": tag, "payload": payload}
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read(path=None, kind=None, tag=None, limit=None):
    path = path or LEDGER
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if kind and rec.get("kind") != kind:
                continue
            if tag and rec.get("tag") != tag:
                continue
            out.append(rec)
    if limit:
        out = out[-limit:]
    return out


def digest(path=None, max_sources=40):
    """
    Compact, resendable state block. This is what goes into a model prompt --
    never the transcript.
    """
    recs = read(path)
    verified, open_q, decisions, notation = [], [], [], []
    for r in recs:
        p = r.get("payload") or {}
        if r["kind"] == "citation" and p.get("status") == "VERIFIED":
            b = p.get("best") or {}
            verified.append("%s (%s) %s%s" % (
                ", ".join((b.get("authors") or [])[:3]) or "?",
                b.get("year") or "n.d.",
                (b.get("title") or "")[:90],
                " doi:" + b["doi"] if b.get("doi") else ""))
        elif r["kind"] == "question":
            open_q.append("[%s] %s" % (r["tag"], p.get("text", "")))
        elif r["kind"] == "decision":
            decisions.append("[%s] %s" % (r["tag"], p.get("text", "")))
        elif r["kind"] == "notation":
            notation.append("%s := %s" % (p.get("symbol"), p.get("meaning")))

    lines = ["# PRECILLA STATE (resend this, not the transcript)",
             "generated %s" % _now(), ""]
    if notation:
        lines += ["## notation"] + ["- " + x for x in notation] + [""]
    if decisions:
        lines += ["## settled decisions"] + ["- " + x for x in decisions] + [""]
    if verified:
        lines += ["## verified sources (%d)" % len(verified)]
        lines += ["- " + x for x in verified[:max_sources]]
        if len(verified) > max_sources:
            lines.append("- ... %d more" % (len(verified) - max_sources))
        lines.append("")
    if open_q:
        lines += ["## open questions"] + ["- " + x for x in open_q] + [""]
    return "\n".join(lines)
