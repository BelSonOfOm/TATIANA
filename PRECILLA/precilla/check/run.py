"""
PRECILLA / check / run.py

Orchestrate: draft.md -> per-equation verdicts -> one gate decision.

The gate is deliberately harsh. `precilla check` returns clean only when every
extracted block PASSES and coverage is total. A draft with three beautiful
proofs and one unmechanised step is not 75% verified -- the unmechanised step
is exactly where the error lives, because it is the one the model could not
render.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

from . import blocks as _blocks
from .guard import screen

WORKER = [sys.executable, "-m", "precilla.check.worker"]

# Verdicts that do not block the gate.
GOOD = {"PASS"}


def run_block(b, symbolic_seconds=20, numeric_seconds=20, trials=200,
              hard_timeout=None, allow_unsafe=False):
    problems = screen(b.source)
    if problems and not allow_unsafe:
        return {"eq": b.eq, "line": b.line, "verdict": "REFUSED",
                "reason": "static screen: " + "; ".join(sorted(set(problems))),
                "violations": sorted(set(problems))}

    payload = json.dumps({"source": b.source,
                          "symbolic_seconds": symbolic_seconds,
                          "numeric_seconds": numeric_seconds,
                          "trials": trials})
    hard = hard_timeout or (symbolic_seconds + numeric_seconds + 30)
    env = dict(os.environ)
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    env["PYTHONPATH"] = root + os.pathsep + env.get("PYTHONPATH", "")
    try:
        p = subprocess.run(WORKER, input=payload, capture_output=True,
                           text=True, timeout=hard, env=env, cwd=root)
    except subprocess.TimeoutExpired:
        return {"eq": b.eq, "line": b.line, "verdict": "TIMEOUT",
                "reason": "worker exceeded %ds wall clock" % hard}
    if p.returncode != 0:
        return {"eq": b.eq, "line": b.line, "verdict": "ERROR",
                "reason": "worker exit %d: %s" % (p.returncode,
                                                  (p.stderr or "")[-400:])}
    try:
        res = json.loads(p.stdout.strip().splitlines()[-1])
    except Exception:
        return {"eq": b.eq, "line": b.line, "verdict": "ERROR",
                "reason": "unparseable worker output: %s" % p.stdout[-300:]}
    res.update({"eq": b.eq, "line": b.line})
    return res


def check_text(text, **kw):
    aud = _blocks.audit(text)
    results = []
    for b in _blocks.find_blocks(text):
        if b.declared_unchecked:
            results.append({"eq": b.eq, "line": b.line,
                            "verdict": "DECLARED_UNCHECKED",
                            "reason": "the draft itself marks this [UNCHECKED]"})
            continue
        results.append(run_block(b, **kw))

    tally = {}
    for r in results:
        tally[r["verdict"]] = tally.get(r["verdict"], 0) + 1

    failing = [r for r in results if r["verdict"] not in GOOD]
    missing = aud["missing_block"]

    if not results and not aud["mentioned"]:
        gate, why = "EMPTY", "no equations found -- is this the right file?"
    elif failing:
        gate = "FAIL"
        why = "%d of %d blocks did not pass: %s" % (
            len(failing), len(results),
            ", ".join("%s=%s" % (r["eq"], r["verdict"]) for r in failing[:8]))
    elif missing:
        # INCOMPLETE, not FAIL. Nothing checked is wrong; some things are
        # unchecked. Conflating the two was an error in the first version:
        # many numbered equations are DEFINITIONS ("let c_t = rho*c + beta*f"),
        # which have no identity to verify, so demanding a SymPy block for
        # every label guaranteed failure and told you nothing.
        gate = "INCOMPLETE"
        why = ("all %d present blocks verified, but %d labelled step(s) carry "
               "no checkable block: %s. Definitions need none; derivations do "
               "-- triage by hand."
               % (len(results), len(missing), ", ".join(missing[:10])))
    else:
        gate = "PASS"
        why = "all %d blocks verified symbolically and numerically" % len(results)

    return {"command": "check", "gate": gate, "reason": why,
            "tally": tally, "audit": {k: v for k, v in aud.items()
                                      if k != "blocks"},
            "results": results}


def check_file(path, **kw):
    with open(path, "r", encoding="utf-8") as fh:
        out = check_text(fh.read(), **kw)
    out["path"] = path
    return out
