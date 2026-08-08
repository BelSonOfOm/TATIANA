"""
PRECILLA -- command line.

Contract, so that a human and an agent can drive the same tool:
  * every subcommand writes ONE json object to stdout
  * all commentary goes to stderr
  * exit code 0 = ran, 1 = ran and the answer is "no", 2 = usage/internal error

That contract is the whole reason this is a CLI and not a notebook: an agent
can `precilla cite verify doc.md | jq '.summary'` without a screenshot.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from . import budget as _budget
from . import ledger as _ledger
from .cite import calibrate as _cal
from .cite import extract as _ex
from .cite import resolve as _resolve
from .cite.match import DEFAULTS
from .check import run as _check
from .derive import client as _dclient
from .derive import run as _derive
from .cite.verify import to_bibtex, verify_candidate

__version__ = "0.1.0"

# Force UTF-8 on stdout/stderr regardless of platform.
#
# Without this, `precilla cite verify ... > bib.json` on Windows writes the
# console codepage (cp1252), because that is what sys.stdout defaults to there.
# `ensure_ascii=False` then emits a byte like 0xe8 for an accented author name,
# and every later reader -- which correctly assumes UTF-8 -- dies on it. That
# is exactly how a passing calibration still produced an unreadable
# bibliography and a silently failing dry run.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def _out(obj, code=0):
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return code


def _err(msg):
    sys.stderr.write(msg.rstrip() + "\n")


def _cfg_from_args(a):
    cfg = dict(DEFAULTS)
    for k in ("tau_verified", "tau_partial", "margin", "min_author_recall"):
        v = getattr(a, k, None)
        if v is not None:
            cfg[k] = v
    return cfg


# --------------------------------------------------------------------------
# cite extract
# --------------------------------------------------------------------------

def cmd_extract(a):
    cands = []
    for p in a.files:
        if not os.path.exists(p):
            _err("no such file: %s" % p)
            return 2
        cands.extend(_ex.extract_file(p))
    return _out({
        "command": "cite.extract",
        "n": len(cands),
        "candidates": [c.to_dict() for c in cands],
    })


# --------------------------------------------------------------------------
# cite verify
# --------------------------------------------------------------------------

def cmd_verify(a):
    cfg = _cfg_from_args(a)
    ok, why = _cal.is_calibrated(cfg)
    if not ok and not a.force:
        _err("REFUSING: %s" % why)
        _err("run `precilla cite calibrate` first, or pass --force to get "
             "downgraded output (VERIFIED becomes UNCALIBRATED).")
        return _out({"command": "cite.verify", "refused": True,
                     "reason": why}, code=1)

    cands = []
    for p in a.files:
        if not os.path.exists(p):
            _err("no such file: %s" % p)
            return 2
        cands.extend(_ex.extract_file(p))

    providers = tuple(a.providers.split(","))
    results = []
    for c in cands:
        r = verify_candidate(c, providers=providers, rows=a.rows, cfg=cfg,
                             use_cache=not a.no_cache)
        if not ok and r["status"] == "VERIFIED":
            r["status"] = "UNCALIBRATED"
            r["reason"] = "instrument not calibrated: " + why
        results.append(r)
        if a.log:
            _ledger.append("citation",
                           "MEASURED" if r["status"] == "VERIFIED" else "UNVERIFIED",
                           r)

    summary = {}
    for r in results:
        summary[r["status"]] = summary.get(r["status"], 0) + 1

    payload = {
        "command": "cite.verify",
        "calibrated": ok,
        "calibration_note": why,
        "n": len(results),
        "summary": summary,
        "results": results,
    }
    if a.bibtex:
        payload["bibtex"] = "\n\n".join(
            b for b in (to_bibtex(r) for r in results) if b)
    bad = summary.get("UNRESOLVED", 0) + summary.get("ERRORED", 0)
    return _out(payload, code=1 if bad else 0)


# --------------------------------------------------------------------------
# cite calibrate
# --------------------------------------------------------------------------

def cmd_calibrate(a):
    cfg = _cfg_from_args(a)
    rep = _cal.run(cfg=cfg, providers=tuple(a.providers.split(",")),
                   use_cache=not a.no_cache, verbose=True)
    if rep["verdict"] == "PASS":
        _cal.write_stamp(rep)
        _ledger.append("calibration", "MEASURED",
                       {k: rep[k] for k in ("verdict", "by_class",
                                            "config_hash", "note")})
        if a.promote:
            rep["promotion"] = _cal.promote(rep)
    else:
        _ledger.append("calibration", "MEASURED",
                       {k: rep[k] for k in ("verdict", "by_class",
                                            "config_hash", "note")})
    if a.report:
        with open(a.report, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=2, ensure_ascii=False)
        _err("full report -> %s" % a.report)
    if not a.verbose:
        rep["rows"] = [r for r in rep["rows"] if not r["pass"]]
    _err("verdict: %s -- %s" % (rep["verdict"], rep["note"]))
    if rep.get("separation"):
        sp = rep["separation"]
        _err("separation: min_gold=%.3f max_decoy=%.3f gap=%.3f separated=%s"
             % (sp["min_gold"], sp["max_decoy"], sp["gap"], sp["separated"]))
    return _out(rep, code=0 if rep["verdict"] == "PASS" else 1)


def cmd_status(a):
    cfg = _cfg_from_args(a)
    ok, why = _cal.is_calibrated(cfg)
    st = _cal.read_stamp()
    return _out({
        "command": "cite.status",
        "version": __version__,
        "calibrated": ok,
        "note": why,
        "stamp": {k: st[k] for k in ("verdict", "timestamp", "by_class",
                                     "config_hash")} if st else None,
        "cache_dir": os.environ.get("PRECILLA_CACHE"),
        "state_dir": _ledger.LEDGER_DIR,
    }, code=0 if ok else 1)




# --------------------------------------------------------------------------
# cite doctor -- preflight. The first thing to run on a machine with real
# network access, because "UNRESOLVED" and "cannot reach the internet" must
# never be confused.
# --------------------------------------------------------------------------

_PROBE = {"cid": "probe", "authors": ["Howard", "Kahana"], "year": 2002,
          "title_hint": "distributed representation of temporal context",
          "topic_hint": None, "raw": "probe"}


class _P(dict):
    __getattr__ = dict.get


def cmd_doctor(a):
    import time as _t
    checks = []
    for name in a.providers.split(","):
        fn = _resolve.PROVIDERS.get(name)
        if fn is None:
            checks.append({"provider": name, "ok": False,
                           "error": "unknown provider"})
            continue
        t0 = _t.time()
        try:
            works = fn(_P(_PROBE), rows=3, use_cache=False)
            ms = int((_t.time() - t0) * 1000)
            top = works[0] if works else None
            checks.append({
                "provider": name, "ok": bool(works), "latency_ms": ms,
                "n_results": len(works),
                "parsed_top": {
                    "title": top.title, "authors": top.authors[:4],
                    "year": top.year, "doi": top.doi} if top else None,
                "parser_sane": bool(top and top.title and top.authors
                                    and top.year),
            })
        except Exception as e:
            checks.append({"provider": name, "ok": False,
                           "latency_ms": int((_t.time() - t0) * 1000),
                           "error": "%s: %s" % (type(e).__name__, e)})

    reachable = [c for c in checks if c.get("ok")]
    sane = [c for c in reachable if c.get("parser_sane")]
    if not reachable:
        verdict = "NO NETWORK -- every provider unreachable. Calibration would " \
                  "report INCONCLUSIVE, which is correct and not a bug."
    elif not sane:
        verdict = "REACHABLE BUT UNPARSED -- the API answered in a shape this " \
                  "build does not understand. Fix resolve.py before calibrating."
    else:
        verdict = "OK -- %d/%d providers reachable and parsing. Run " \
                  "`precilla cite calibrate --verbose` next." % (
                      len(sane), len(checks))
    _err(verdict)
    return _out({"command": "cite.doctor", "verdict": verdict,
                 "mailto_set": bool(_resolve.DEFAULT_MAILTO),
                 "checks": checks}, code=0 if sane else 1)


def cmd_budget(a):
    rep = _budget.report(budget_usd=a.budget)
    if a.check:
        rep["price_sources"] = {k: v["src"]
                                for k, v in _budget.PROVIDERS.items()}
    rep["selftest"] = [{"check": n, "pass": ok, "value": str(v)}
                       for n, ok, v in _budget.budget_selftest()]
    failed = [c for c in rep["selftest"] if not c["pass"]]
    r = rep["recommendation"]
    _err("lead=%s  redteam=%s  $%.3f/cycle  %s cycles in $%.2f" % (
        r["lead_deriver"], r["red_team"], r["lead_plus_redteam_usd"],
        r["cycles_within_budget"], a.budget))
    return _out(rep, code=1 if failed else 0)


# --------------------------------------------------------------------------
# check -- job 3
# --------------------------------------------------------------------------

def cmd_check(a):
    if not os.path.exists(a.file):
        _err("no such file: %s" % a.file)
        return 2
    rep = _check.check_file(
        a.file, symbolic_seconds=a.symbolic_seconds,
        numeric_seconds=a.numeric_seconds, trials=a.trials,
        allow_unsafe=a.allow_unsafe)
    _err("gate: %s -- %s" % (rep["gate"], rep["reason"]))
    if a.log:
        _ledger.append("check", "MEASURED",
                       {"path": a.file, "gate": rep["gate"],
                        "tally": rep["tally"], "reason": rep["reason"]})
    return _out(rep, code=0 if rep["gate"] == "PASS" else 1)


# --------------------------------------------------------------------------
# derive -- job 2. The only thing here that costs money.
# --------------------------------------------------------------------------

def cmd_derive(a):
    if a.action == "models":
        try:
            rows = _dclient.list_models(filter_str=a.filter or "")
        except _dclient.ClientError as e:
            _err(str(e))
            return _out({"command": "derive.models", "error": str(e)}, code=1)
        return _out({"command": "derive.models", "n": len(rows),
                     "models": rows})

    if a.action == "spend":
        total, n = _derive.spent_so_far()
        return _out({"command": "derive.spend", "spent_usd": total,
                     "calls": n, "budget_usd": a.budget,
                     "remaining_usd": (round(a.budget - total, 4)
                                       if a.budget else None)})

    role = a.action  # lead | redteam
    try:
        rep, code = _derive.run_pass(
            role, a.prompt, a.out, model=a.model, docs=a.docs or (),
            bib=a.bib, draft=a.draft, digest=a.digest, note=a.note,
            expected_out=a.expected_out, max_usd=a.max_usd,
            budget_usd=a.budget, dry_run=a.dry_run,
            temperature=a.temperature)
    except (_dclient.ClientError, ValueError, FileNotFoundError) as e:
        _err("%s: %s" % (type(e).__name__, e))
        return _out({"command": "derive." + role, "error": str(e)}, code=2)

    if rep.get("verdict") == "REFUSED":
        _err("REFUSED: " + rep.get("reason", ""))
    elif rep.get("dry_run"):
        _err("dry run: %d input tokens, projected $%s (spent so far $%s)"
             % (rep["input_tokens_est"], rep["projected_usd"],
                rep["spent_so_far_usd"]))
    else:
        _err("wrote %s (%d chars) -- cost $%s [%s]"
             % (rep.get("out_path"), rep.get("output_chars", 0),
                rep.get("cost_usd"), rep.get("cost_note")))
    return _out(rep, code=code)


# --------------------------------------------------------------------------
# ledger
# --------------------------------------------------------------------------

def cmd_ledger(a):
    if a.action == "digest":
        txt = _ledger.digest()
        sys.stderr.write(txt + "\n")
        return _out({"command": "ledger.digest", "chars": len(txt),
                     "text": txt})
    if a.action == "add":
        rec = _ledger.append(a.kind, a.tag, {"text": a.text})
        return _out({"command": "ledger.add", "record": rec})
    recs = _ledger.read(limit=a.limit)
    return _out({"command": "ledger.show", "n": len(recs), "records": recs})


# --------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="precilla",
        description="PRECILLA -- Prior-art Resolution, Escalating Council, "
                    "Invariant Ledger, Literature Anchoring.")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="group", required=True)

    cite = sub.add_parser("cite", help="literature / prior-art job")
    cs = cite.add_subparsers(dest="cmd", required=True)

    def add_cfg(sp):
        sp.add_argument("--tau-verified", dest="tau_verified", type=float)
        sp.add_argument("--tau-partial", dest="tau_partial", type=float)
        sp.add_argument("--margin", type=float)
        sp.add_argument("--min-author-recall", dest="min_author_recall",
                        type=float)
        sp.add_argument("--providers", default="openalex,crossref")
        sp.add_argument("--no-cache", action="store_true")

    e = cs.add_parser("extract", help="pull citation candidates from markdown")
    e.add_argument("files", nargs="+")
    e.set_defaults(func=cmd_extract)

    v = cs.add_parser("verify", help="resolve candidates against real records")
    v.add_argument("files", nargs="+")
    v.add_argument("--rows", type=int, default=8)
    v.add_argument("--bibtex", action="store_true",
                   help="emit bibtex for VERIFIED entries only")
    v.add_argument("--log", action="store_true", help="write to the ledger")
    v.add_argument("--force", action="store_true",
                   help="run without a calibration stamp (downgrades output)")
    add_cfg(v)
    v.set_defaults(func=cmd_verify)

    c = cs.add_parser("calibrate", help="positive control; gold+nearmiss+decoy")
    c.add_argument("--verbose", action="store_true")
    c.add_argument("--report", help="write the FULL report json to this path")
    c.add_argument("--promote", action="store_true",
                   help="on PASS, write resolved DOIs back into fixtures")
    add_cfg(c)
    c.set_defaults(func=cmd_calibrate)

    s = cs.add_parser("status", help="is the instrument allowed to run?")
    add_cfg(s)
    s.set_defaults(func=cmd_status)

    d = cs.add_parser("doctor", help="preflight: can we reach the providers?")
    d.add_argument("--providers", default="openalex,crossref,arxiv")
    d.set_defaults(func=cmd_doctor)

    ck = sub.add_parser("check", help="verify a derivation draft; no model, no cost")
    ck.add_argument("file")
    ck.add_argument("--symbolic-seconds", dest="symbolic_seconds", type=int,
                    default=20)
    ck.add_argument("--numeric-seconds", dest="numeric_seconds", type=int,
                    default=20)
    ck.add_argument("--trials", type=int, default=200)
    ck.add_argument("--log", action="store_true")
    ck.add_argument("--allow-unsafe", dest="allow_unsafe", action="store_true",
                    help="run blocks that fail the static screen (do not)")
    ck.set_defaults(func=cmd_check)

    dv = sub.add_parser("derive", help="job 2: run a model pass (costs money)")
    dv.add_argument("action", choices=["lead", "redteam", "models", "spend"])
    dv.add_argument("--prompt", default="PROMPT.md")
    dv.add_argument("--docs", nargs="*", default=[])
    dv.add_argument("--bib")
    dv.add_argument("--draft")
    dv.add_argument("--digest")
    dv.add_argument("--note")
    dv.add_argument("--out", default="draft.md")
    dv.add_argument("--model")
    dv.add_argument("--filter", help="substring filter for `derive models`")
    dv.add_argument("--temperature", type=float, default=0.2)
    dv.add_argument("--expected-out", dest="expected_out", type=int,
                    default=40000, help="output tokens assumed when projecting")
    dv.add_argument("--max-usd", dest="max_usd", type=float, default=1.00,
                    help="refuse any single call projected above this")
    dv.add_argument("--budget", type=float, default=7.70,
                    help="cumulative ceiling across all derive calls")
    dv.add_argument("--dry-run", dest="dry_run", action="store_true",
                    help="assemble and price the call without sending it")
    dv.set_defaults(func=cmd_derive)

    bg = sub.add_parser("budget", help="financial + computational resources")
    bg.add_argument("--budget", type=float, default=8.50)
    bg.add_argument("--check", action="store_true",
                    help="include price-table source URLs to re-verify")
    bg.set_defaults(func=cmd_budget)

    lg = sub.add_parser("ledger", help="append-only audit + flat context")
    lg.add_argument("action", choices=["show", "add", "digest"])
    lg.add_argument("--kind", default="decision")
    lg.add_argument("--tag", default="DERIVED")
    lg.add_argument("--text", default="")
    lg.add_argument("--limit", type=int, default=50)
    lg.set_defaults(func=cmd_ledger)

    return p


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        _err("interrupted")
        return 2
    except Exception as e:                              # noqa: BLE001
        _err("%s: %s" % (type(e).__name__, e))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
