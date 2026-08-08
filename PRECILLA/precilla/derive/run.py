"""
PRECILLA / derive / run.py

Job 2. Assemble a pass, guard the spend, call, log what it actually cost.

THE FLAT-CONTEXT RULE, ENFORCED HERE
    Pass 1 sends the documents. Every later pass sends the ledger digest plus
    the specific artefact under discussion (the draft, or the critique) -- never
    the transcript. `budget.py` says naive chat inflates input 5.9x for
    identical output; this module is where that saving is actually taken, and
    `--dry-run` prints the token count so you can see it happening.

THE SPEND RULE
    Every call is refused unless its projected cost is under `--max-usd`, and
    the running total is read back from the ledger so a loop cannot quietly
    drain the account. Dry-run is free and prints the projection.
"""

from __future__ import annotations

import json
import os
import re

from .. import budget as _budget
from .. import ledger as _ledger
from . import client as _client

ROLE_LEAD = "lead"
ROLE_REDTEAM = "redteam"

# Both slugs [MEASURED] present in OpenRouter's live model list, 2026-08-06.
# An earlier draft guessed "deepseek/deepseek-chat", which is NOT in the list;
# a typo'd slug is a failed call, so these are confirmed rather than assumed.
DEFAULTS = {
    ROLE_LEAD: "z-ai/glm-5.2",
    ROLE_REDTEAM: "deepseek/deepseek-v4-flash-0731",
}

# Map an OpenRouter slug onto a row of the local price table, for projection
# only. Actual cost is taken from the provider's reported figure when present.
SLUG_TO_PRICE = {
    "z-ai/glm-5.2": "glm-5.2-openrouter",
    "moonshotai/kimi-k3": "kimi-k3",
    "moonshotai/kimi-k2.7-code": "kimi-k3",
    "deepseek/deepseek-v4-flash-0731": "deepseek-v4-flash",
    "deepseek/deepseek-v4-flash-latest": "deepseek-v4-flash",
    "deepseek/deepseek-v3.2": "deepseek-v3.2",
}

_SECTION_RE = re.compile(r"^##\s+(.*?)\s*$", re.M)


def load_prompt(path, which="THE PROMPT"):
    """Pull one '## <NAME>' section out of PROMPT.md."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    marks = [(m.start(), m.end(), m.group(1).strip().upper())
             for m in _SECTION_RE.finditer(text)]
    for i, (_s, e, name) in enumerate(marks):
        if name == which.upper():
            end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
            body = text[e:end]
            # strip a leading blockquote-free horizontal rule if present
            return body.strip().strip("-").strip()
    raise ValueError("section %r not found in %s (found: %s)"
                     % (which, path, [m[2] for m in marks]))


def est_tokens(s):
    return int(len(s) / _budget.CHARS_PER_TOKEN)


def _read(path):
    """
    Read as UTF-8, but never die on a file some other tool mis-encoded.

    A mojibake byte in a bibliography is a cosmetic problem; refusing to run
    because of one is not. Falls back to cp1252 (the usual Windows culprit),
    then to lossy UTF-8.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    for enc in ("utf-8", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def build_messages(role, prompt_path, docs=(), bib=None, draft=None,
                   digest=None, extra_note=None):
    """
    Returns (messages, breakdown).

    Ordering matters for prefix caching: the invariant material (system prompt,
    documents) goes first and identically every time, so a provider that caches
    prefixes can charge the discounted rate for it.
    """
    if role == ROLE_LEAD:
        system = load_prompt(prompt_path, "THE PROMPT")
    else:
        system = load_prompt(prompt_path, "THE RED TEAM PROMPT")

    parts, breakdown = [], {}
    breakdown["system"] = est_tokens(system)

    for d in docs:
        body = _read(d)
        parts.append("<document name=%r>\n%s\n</document>" % (os.path.basename(d), body))
        breakdown["doc:" + os.path.basename(d)] = est_tokens(body)

    if bib:
        body = _read(bib)
        # bib.json is a verify report; pass only the bibtex if it is there
        try:
            j = json.loads(body)
            body = j.get("bibtex") or body
        except Exception:
            pass
        parts.append("<verified_bibliography>\n%s\n</verified_bibliography>\n"
                     "Cite ONLY from this list. Anything else: "
                     "[CITATION NEEDED: <author> <topic>]." % body)
        breakdown["bibliography"] = est_tokens(body)

    if digest:
        body = _read(digest) if os.path.exists(digest) else digest
        if body.strip():
            parts.append("<state>\n%s\n</state>" % body)
            breakdown["digest"] = est_tokens(body)

    if draft:
        body = _read(draft)
        tag = "draft_under_review" if role == ROLE_REDTEAM else "previous_draft"
        parts.append("<%s>\n%s\n</%s>" % (tag, body, tag))
        breakdown[tag] = est_tokens(body)

    if extra_note:
        parts.append("<instruction>\n%s\n</instruction>" % extra_note)
        breakdown["note"] = est_tokens(extra_note)

    user = "\n\n".join(parts)
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": user}]
    breakdown["_total_in"] = breakdown["system"] + est_tokens(user)
    return messages, breakdown


def project_cost(model, in_tokens, expected_out_tokens):
    key = SLUG_TO_PRICE.get(model)
    if not key or key not in _budget.PROVIDERS:
        return None, "no local price row for %r -- projection unavailable" % model
    p = _budget.PROVIDERS[key]
    usd = (in_tokens / 1e6) * p["in"] + (expected_out_tokens / 1e6) * p["out"]
    return round(usd, 4), "projected from local table (%s)" % key


def actual_cost(model, usage):
    if usage.get("reported_cost_usd") is not None:
        try:
            return round(float(usage["reported_cost_usd"]), 6), "provider-reported"
        except (TypeError, ValueError):
            pass
    key = SLUG_TO_PRICE.get(model)
    if not key:
        return None, "unknown model, no cost computed"
    p = _budget.PROVIDERS[key]
    fresh = max(usage["prompt_tokens"] - usage.get("cached_tokens", 0), 0)
    out = usage["completion_tokens"] + usage.get("reasoning_tokens", 0)
    usd = ((fresh / 1e6) * p["in"]
           + (usage.get("cached_tokens", 0) / 1e6) * p["cached_in"]
           + (out / 1e6) * p["out"])
    return round(usd, 6), "computed from local table"


def spent_so_far():
    total = 0.0
    n = 0
    for rec in _ledger.read(kind="derive"):
        c = (rec.get("payload") or {}).get("cost_usd")
        if isinstance(c, (int, float)):
            total += c
            n += 1
    return round(total, 4), n


def run_pass(role, prompt_path, out_path, model=None, docs=(), bib=None,
             draft=None, digest=None, note=None, expected_out=40_000,
             max_usd=1.00, budget_usd=None, dry_run=False, transport=None,
             temperature=0.2, base_url=None):
    model = model or DEFAULTS[role]
    messages, breakdown = build_messages(role, prompt_path, docs=docs, bib=bib,
                                         draft=draft, digest=digest,
                                         extra_note=note)
    in_tok = breakdown["_total_in"]
    proj, proj_note = project_cost(model, in_tok, expected_out)
    spent, ncalls = spent_so_far()

    report = {
        "command": "derive." + role,
        "model": model,
        "input_tokens_est": in_tok,
        "breakdown": breakdown,
        "projected_usd": proj,
        "projection_note": proj_note,
        "spent_so_far_usd": spent,
        "calls_so_far": ncalls,
        "dry_run": bool(dry_run),
    }

    if dry_run:
        report["messages_preview"] = {
            "system_head": messages[0]["content"][:300],
            "user_head": messages[1]["content"][:300],
            "user_tail": messages[1]["content"][-300:],
        }
        report["verdict"] = "DRY RUN -- nothing sent, nothing charged"
        return report, 0

    if proj is not None and proj > max_usd:
        report["verdict"] = "REFUSED"
        report["reason"] = ("projected $%.4f exceeds --max-usd $%.2f"
                            % (proj, max_usd))
        return report, 1
    if budget_usd is not None and proj is not None and spent + proj > budget_usd:
        report["verdict"] = "REFUSED"
        report["reason"] = ("spent $%.4f + projected $%.4f would exceed the "
                            "$%.2f budget" % (spent, proj, budget_usd))
        return report, 1

    text, usage, _raw = _client.chat(messages, model, transport=transport,
                                     temperature=temperature, base_url=base_url)
    cost, cost_note = actual_cost(model, usage)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)

    report.update({
        "verdict": "OK",
        "out_path": out_path,
        "output_chars": len(text),
        "usage": usage,
        "cost_usd": cost,
        "cost_note": cost_note,
        "projection_error": (round(cost - proj, 4)
                             if (cost is not None and proj is not None) else None),
    })
    _ledger.append("derive", "MEASURED",
                   {k: report[k] for k in
                    ("command", "model", "out_path", "usage", "cost_usd",
                     "input_tokens_est", "projected_usd")})
    return report, 0
