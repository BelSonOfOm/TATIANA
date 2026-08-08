"""
Offline battery for `precilla derive` -- the module that spends money.

Nothing here touches the network. A fake transport stands in for OpenRouter and
returns a realistic response envelope, including reasoning tokens and a
provider-reported cost, so the accounting path is exercised end to end.

The rule this file enforces: an untested billing path is one you discover by
being charged for it.

Run:  python3 tests/test_derive.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from precilla import ledger as _ledger              # noqa: E402
from precilla.derive import client as _client       # noqa: E402
from precilla.derive import run as _run             # noqa: E402

FAILURES = []
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPT = os.path.join(ROOT, "PROMPT.md")


def check(name, cond, detail=""):
    if cond:
        print("  ok   %s" % name)
    else:
        print("  FAIL %s   %s" % (name, detail))
        FAILURES.append(name)


SENT = {}


def fake_transport(url, payload, headers, timeout=600):
    SENT["url"] = url
    SENT["payload"] = payload
    SENT["headers"] = headers
    return {
        "choices": [{"message": {"content": "# §0 VERDICT\nA draft.\n"}}],
        "usage": {
            "prompt_tokens": 12000,
            "completion_tokens": 9000,
            "completion_tokens_details": {"reasoning_tokens": 27000},
            "prompt_tokens_details": {"cached_tokens": 8000},
            "total_tokens": 48000,
            "cost": 0.0421,
        },
    }


def test_defaults_are_confirmed_slugs():
    print("\n[0] default model slugs")
    # Confirmed present in OpenRouter's live /api/v1/models on 2026-08-06.
    for role, slug in _run.DEFAULTS.items():
        check("%s default %r has a price row" % (role, slug),
              slug in _run.SLUG_TO_PRICE, slug)
    check("red team is a different family from lead",
          _run.SLUG_TO_PRICE[_run.DEFAULTS["lead"]].split("-")[0]
          != _run.SLUG_TO_PRICE[_run.DEFAULTS["redteam"]].split("-")[0],
          "%s vs %s" % (_run.DEFAULTS["lead"], _run.DEFAULTS["redteam"]))


def test_prompt_sections():
    print("\n[1] PROMPT.md section extraction")
    lead = _run.load_prompt(PROMPT, "THE PROMPT")
    red = _run.load_prompt(PROMPT, "THE RED TEAM PROMPT")
    check("lead prompt found", len(lead) > 500, len(lead))
    check("lead prompt carries the output contract",
          "OUTPUT CONTRACT" in lead or "§0" in lead, lead[:80])
    check("red team prompt found", len(red) > 200, len(red))
    check("red team prompt presupposes an error",
          "substantive error" in red.lower(), red[:120])
    check("the two are different", lead != red, "")


def test_assembly_and_flat_context():
    print("\n[2] message assembly + the flat-context saving")
    with tempfile.TemporaryDirectory() as td:
        d1 = os.path.join(td, "doc1.md")
        open(d1, "w").write("DOC BODY\n" * 400)
        bib = os.path.join(td, "bib.json")
        json.dump({"bibtex": "@article{x, title={T}}"}, open(bib, "w"))
        draft = os.path.join(td, "draft.md")
        open(draft, "w").write("DRAFT BODY\n" * 200)
        digest = os.path.join(td, "state.md")
        open(digest, "w").write("## settled decisions\n- [DERIVED] x\n")

        msgs, first = _run.build_messages(
            _run.ROLE_LEAD, PROMPT, docs=[d1], bib=bib, digest=digest)
        check("two messages, system + user", len(msgs) == 2, len(msgs))
        check("system role is the prompt", msgs[0]["role"] == "system", "")
        check("documents are in the user turn",
              "DOC BODY" in msgs[1]["content"], "")
        check("bibliography included with a cite-only instruction",
              "CITATION NEEDED" in msgs[1]["content"], "")

        # later pass: digest + draft, NO documents
        msgs2, later = _run.build_messages(
            _run.ROLE_REDTEAM, PROMPT, docs=[], bib=None, draft=draft,
            digest=digest)
        check("later pass omits the documents entirely",
              "DOC BODY" not in msgs2[1]["content"], "")
        check("later pass carries the draft under review",
              "draft_under_review" in msgs2[1]["content"], "")
        check("later pass is cheaper in input than the first",
              later["_total_in"] < first["_total_in"],
              (later["_total_in"], first["_total_in"]))


def test_dry_run_costs_nothing():
    print("\n[3] dry run")
    SENT.clear()
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "draft.md")
        rep, code = _run.run_pass(
            _run.ROLE_LEAD, PROMPT, out, model="z-ai/glm-5.2",
            dry_run=True, transport=fake_transport)
    check("dry run does not call the transport", "payload" not in SENT, "")
    check("dry run writes no output file", not os.path.exists(out), "")
    check("dry run still reports a projection",
          rep["projected_usd"] is not None, str(rep["projected_usd"]))
    check("dry run exits 0", code == 0, code)


def test_spend_guards():
    print("\n[4] spend guards")
    SENT.clear()
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "draft.md")
        rep, code = _run.run_pass(
            _run.ROLE_LEAD, PROMPT, out, model="z-ai/glm-5.2",
            expected_out=40000, max_usd=0.0001, transport=fake_transport)
        check("per-call ceiling refuses an over-budget call",
              rep["verdict"] == "REFUSED", rep.get("verdict"))
        check("refusal never called the transport", "payload" not in SENT, "")
        check("refusal exits 1", code == 1, code)
        check("refusal explains itself", "exceeds" in rep.get("reason", ""),
              rep.get("reason"))

        rep2, code2 = _run.run_pass(
            _run.ROLE_LEAD, PROMPT, out, model="z-ai/glm-5.2",
            expected_out=40000, max_usd=10.0, budget_usd=0.0001,
            transport=fake_transport)
        check("cumulative budget also refuses",
              rep2["verdict"] == "REFUSED", rep2.get("verdict"))


def test_accounting():
    print("\n[5] accounting on a real-shaped response")
    SENT.clear()
    with tempfile.TemporaryDirectory() as td:
        os.environ["PRECILLA_STATE"] = td
        # ledger module caches its path at import; point it explicitly
        old = _ledger.LEDGER
        _ledger.LEDGER = os.path.join(td, "ledger.jsonl")
        try:
            out = os.path.join(td, "draft.md")
            rep, code = _run.run_pass(
                _run.ROLE_LEAD, PROMPT, out, model="z-ai/glm-5.2",
                expected_out=40000, max_usd=5.0, transport=fake_transport)
            check("call succeeded", rep["verdict"] == "OK", rep.get("verdict"))
            check("output written", os.path.exists(out), "")
            check("reasoning tokens captured",
                  rep["usage"]["reasoning_tokens"] == 27000,
                  rep["usage"]["reasoning_tokens"])
            check("cached tokens captured",
                  rep["usage"]["cached_tokens"] == 8000, "")
            check("provider-reported cost preferred over the local table",
                  rep["cost_usd"] == 0.0421 and "reported" in rep["cost_note"],
                  "%s / %s" % (rep["cost_usd"], rep["cost_note"]))
            check("projection error recorded",
                  rep["projection_error"] is not None,
                  str(rep["projection_error"]))

            recs = _ledger.read(kind="derive", path=_ledger.LEDGER)
            check("call written to the ledger", len(recs) == 1, len(recs))
            total, n = _run.spent_so_far()
            check("running total reads back from the ledger",
                  abs(total - 0.0421) < 1e-9 and n == 1, (total, n))
        finally:
            _ledger.LEDGER = old
            os.environ.pop("PRECILLA_STATE", None)


def test_local_table_fallback():
    print("\n[6] cost falls back to the local table when unreported")
    usage = {"prompt_tokens": 12000, "completion_tokens": 9000,
             "reasoning_tokens": 27000, "cached_tokens": 0,
             "reported_cost_usd": None}
    cost, note = _run.actual_cost("z-ai/glm-5.2", usage)
    # Read the rates from the table rather than restating them: this test
    # verifies the ARITHMETIC, not the constants. An earlier version hardcoded
    # 0.406/1.276 and broke the moment the live OpenRouter price corrected it
    # to 0.76/2.42 -- a test failing because a fact improved is a bad test.
    from precilla.budget import PROVIDERS
    p = PROVIDERS[_run.SLUG_TO_PRICE["z-ai/glm-5.2"]]
    want = (12000 / 1e6) * p["in"] + (36000 / 1e6) * p["out"]
    check("computed cost matches the price table",
          abs(cost - want) < 1e-6, "%s vs %s" % (cost, want))
    check("reasoning tokens are billed as output",
          cost > (12000 / 1e6) * p["in"] + (9000 / 1e6) * p["out"], cost)
    check("note says it was computed locally", "local" in note, note)


def test_no_key_is_a_clean_error():
    print("\n[7] missing key")
    old = os.environ.pop(_client.KEY_ENV, None)
    try:
        try:
            _client.chat([{"role": "user", "content": "x"}], "z-ai/glm-5.2")
            check("missing key raises", False, "no exception")
        except _client.ClientError as e:
            check("missing key raises a clear ClientError",
                  "no API key" in str(e), str(e)[:80])
    finally:
        if old:
            os.environ[_client.KEY_ENV] = old


if __name__ == "__main__":
    test_defaults_are_confirmed_slugs()
    test_prompt_sections()
    test_assembly_and_flat_context()
    test_dry_run_costs_nothing()
    test_spend_guards()
    test_accounting()
    test_local_table_fallback()
    test_no_key_is_a_clean_error()
    print("\n%s  %d failure(s)" % ("FAILED" if FAILURES else "PASSED",
                                   len(FAILURES)))
    if FAILURES:
        print("  " + "\n  ".join(FAILURES))
    sys.exit(1 if FAILURES else 0)
