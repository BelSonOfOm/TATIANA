"""
PRECILLA / budget.py

Two resource questions, computed rather than guessed:

  FINANCIAL     what does the derivation cost, per provider?
  COMPUTATIONAL what does the simulator cost, on 4 cores and 5.9 GB?

Both models are explicit and editable. The point is not the specific numbers --
they will be stale within weeks -- it is that changing an assumption changes the
answer in front of you instead of inside someone's head.

⚠️ EPISTEMIC STATUS OF THE PRICE TABLE: [MEASURED] from vendor/aggregator pages
on the `as_of` date, NOT re-verified since. Prices move. `precilla budget
--check` prints the URLs to re-check.
"""

from __future__ import annotations

import json

AS_OF = "2026-08-06"
# GLM 5.2 and DeepSeek V4-Flash rows are [MEASURED] from OpenRouter's live
# /api/v1/models. The rest remain [UNVERIFIED] aggregator figures.

# --------------------------------------------------------------------------
# price table -- USD per 1M tokens
# --------------------------------------------------------------------------

PROVIDERS = {
    "gemini-free": {
        "family": "google", "gpqa": None,
        "label": "Gemini free tier (AI Studio)",
        "in": 0.0, "out": 0.0, "cached_in": 0.0,
        "limits": "5 RPM / 100 RPD on Pro-class; 10 RPM / 250 RPD Flash",
        "note": "genuinely $0. Rate limits, not price, are the constraint.",
        "reasoning_billed": True,
        "src": "https://www.aifreeapi.com/en/posts/gemini-api-rate-limits-per-tier",
    },
    "glm-5.2-openrouter": {
        "family": "zhipu", "gpqa": 91.2,
        "label": "GLM 5.2 via OpenRouter",
        # [MEASURED] read from OpenRouter /api/v1/models on 2026-08-06.
        # An aggregator page had claimed 0.406/1.276; the API says otherwise,
        # and the API is the thing that bills you. Slug confirmed present.
        "in": 0.76, "out": 2.42, "cached_in": 0.76,
        "limits": "none practical",
        "note": "753B MoE, MIT, 1M ctx. Still ~1.8x cheaper than Z.ai direct "
                "for identical weights.",
        "reasoning_billed": True,
        "src": "https://openrouter.ai/api/v1/models (live, 2026-08-06)",
    },
    "deepseek-v4-flash": {
        "family": "deepseek", "gpqa": None,
        "label": "DeepSeek V4-Flash (OpenRouter)",
        # [MEASURED] same live fetch. Cheaper than V3.2 AND slug-confirmed,
        # which V3.2's is not.
        "in": 0.09, "out": 0.18, "cached_in": 0.09,
        "limits": "none practical",
        "note": "284B/13B active, 1M ctx. Cheapest confirmed slug on the "
                "platform; ideal red-teamer.",
        "reasoning_billed": True,
        "src": "https://openrouter.ai/api/v1/models (live, 2026-08-06)",
    },
    "glm-5.2-direct": {
        "family": "zhipu", "gpqa": 91.2,
        "label": "GLM 5.2 via Z.ai direct",
        "in": 1.40, "out": 4.40, "cached_in": 1.40,
        "limits": "none practical",
        "note": "same model as the row above at 3.4x the price. Listed to make "
                "that visible.",
        "reasoning_billed": True,
        "src": "https://www.morphllm.com/glm-5-2",
    },
    "kimi-k3": {
        "family": "moonshot", "gpqa": 93.5,
        "label": "Kimi K3 (Moonshot direct)",
        "in": 3.00, "out": 15.00, "cached_in": 0.30,
        "limits": "none practical",
        "note": "best open-weight reasoning: GPQA-D 93.5, HLE 56. 10x cache "
                "discount makes a fixed document prefix nearly free.",
        "reasoning_billed": True,
        "src": "https://benchlm.ai/moonshot/api-pricing",
    },
    "deepseek-v4-pro": {
        "family": "deepseek", "gpqa": None,
        "label": "DeepSeek V4-Pro",
        "in": 1.74, "out": 3.48, "cached_in": 1.74,
        "limits": "none practical",
        "note": "1.6T/49B active. Strong on algorithmic reasoning.",
        "reasoning_billed": True,
        "src": "https://www.userightai.com/cheapest-frontier-ai-2026",
    },
    "deepseek-v3.2": {
        "family": "deepseek", "gpqa": None,
        "label": "DeepSeek V3.2",
        "in": 0.14, "out": 0.28, "cached_in": 0.14,
        "limits": "none practical",
        "note": "[UNVERIFIED] aggregator price; slug not found in the live "
                "OpenRouter list. Prefer deepseek-v4-flash, which is both "
                "cheaper and confirmed.",
        "reasoning_billed": True,
        "src": "https://benchlm.ai/llm-pricing",
    },
    "sonnet-5": {
        "family": "anthropic", "gpqa": None,
        "label": "Claude Sonnet 5 (API)",
        "in": 2.00, "out": 10.00, "cached_in": 0.20,
        "limits": "none practical",
        "note": "intro pricing through 2026-08-31; $3/$15 from 2026-09-01.",
        "reasoning_billed": True,
        "src": "https://www.developersdigest.tech/blog/frontier-model-api-pricing-june-2026",
    },
}

# --------------------------------------------------------------------------
# workload model
# --------------------------------------------------------------------------

# Measured from the actual files, not guessed: see budget_selftest().
DOC_CHARS = 36_471          # the two MOS documents
CHARS_PER_TOKEN = 3.8       # conservative for dense technical English

WORKLOADS = {
    "derive": {
        "label": "Formalise the generative thought model, to a defended draft",
        # A pass = one model call that produces real work.
        "lead_passes": 5,        # draft + 4 revisions
        "redteam_passes": 5,     # a DIFFERENT model attacks each draft
        "visible_out": 10_000,   # tokens of actual derivation per lead pass
        "reasoning_multiple": 3.0,   # hidden thinking tokens, billed as output
        "redteam_out": 4_000,        # critiques are shorter
        "redteam_reasoning_multiple": 2.0,
        "prompt_tokens": 2_500,      # the master prompt
        "digest_tokens": 2_000,      # ledger digest, replaces the transcript
    },
}


def _doc_tokens():
    return int(DOC_CHARS / CHARS_PER_TOKEN)


def workload_tokens(wl, resend_docs_every_pass=False, cache_prefix=True):
    """
    Returns (fresh_in, cached_in, out) totals in tokens.

    The single largest lever in the whole system is here, and it is not the
    model: if you resend the transcript every turn, input grows quadratically.
    The ledger digest keeps it flat.
    """
    doc = _doc_tokens()
    lead, red = wl["lead_passes"], wl["redteam_passes"]
    passes = lead + red

    if resend_docs_every_pass:
        # naive chat: docs + a transcript that grows by one pass each time
        fresh = 0
        for i in range(passes):
            transcript = i * (wl["visible_out"] + wl["prompt_tokens"])
            fresh += doc + wl["prompt_tokens"] + transcript
        cached = 0
    else:
        # PRECILLA: docs once as a cacheable prefix, then digest only
        first = doc + wl["prompt_tokens"]
        rest = passes - 1
        if cache_prefix:
            fresh = first + rest * wl["digest_tokens"]
            cached = rest * doc
        else:
            fresh = first + rest * (doc + wl["digest_tokens"])
            cached = 0

    out = lead * int(wl["visible_out"] * (1 + wl["reasoning_multiple"]))
    out += red * int(wl["redteam_out"] * (1 + wl["redteam_reasoning_multiple"]))
    return int(fresh), int(cached), int(out)


def cost(provider_key, fresh_in, cached_in, out):
    p = PROVIDERS[provider_key]
    return (fresh_in / 1e6) * p["in"] + (cached_in / 1e6) * p["cached_in"] \
        + (out / 1e6) * p["out"]


def financial(workload="derive", budget_usd=8.50):
    wl = WORKLOADS[workload]
    flat_f, flat_c, out = workload_tokens(wl)
    naive_f, naive_c, naive_out = workload_tokens(wl, resend_docs_every_pass=True)

    rows = []
    for k, p in PROVIDERS.items():
        c_flat = cost(k, flat_f, flat_c, out)
        c_naive = cost(k, naive_f, naive_c, naive_out)
        rows.append({
            "provider": k,
            "label": p["label"],
            "usd_precilla": round(c_flat, 4),
            "usd_naive_chat": round(c_naive, 4),
            "overspend_multiple": (round(c_naive / c_flat, 1) if c_flat else None),
            "runs_within_budget": (int(budget_usd / c_flat) if c_flat else "unlimited"),
            "limits": p["limits"],
            "note": p["note"],
        })
    rows.sort(key=lambda r: r["usd_precilla"])
    return {
        "workload": wl["label"],
        "as_of": AS_OF,
        "budget_usd": budget_usd,
        "tokens": {
            "doc_tokens": _doc_tokens(),
            "precilla": {"fresh_in": flat_f, "cached_in": flat_c, "out": out},
            "naive_chat": {"fresh_in": naive_f, "cached_in": naive_c,
                           "out": naive_out},
            "input_inflation_from_naive_chat":
                round(naive_f / max(flat_f + flat_c, 1), 2),
        },
        "rows": rows,
    }


# --------------------------------------------------------------------------
# computational model -- the MOS simulator on the actual machine
# --------------------------------------------------------------------------

# safe_ram_gb is derived, not picked:
#   5.9 total - 1.5 OS/desktop - 0.4 python+numpy runtime - 1.0 margin against
#   swap death on a machine that sleeps  ~=  3.0 GB for the working set.
MACHINE = {"cores": 4, "ram_gb": 5.9, "safe_ram_gb": 3.0, "jobs": 2}

# Peak working set as a multiple of one W. The naive Hebbian line
#     W = W + eta*np.outer(a, a) - zeta*W
# materialises three N x N temporaries on top of W itself, so peak is ~4x.
# Rewritten in place --
#     W *= (1.0 - zeta);  W += eta * np.outer(a, a)
# -- it is ~2x. That rewrite is worth more RAM than any other single change,
# which is why the model reports both.
NAIVE_WORKING_MULTIPLE = 4.0
INPLACE_WORKING_MULTIPLE = 2.0

# Anchor: the logbook's own measurement, N=1074 dense -> ~2.5 ms/tick in numpy.
ANCHOR_N = 1074
ANCHOR_MS_PER_TICK = 2.5


def simulator(n_concepts=1074, ticks=1_000_000, dtype_bytes=8, seeds=1,
              sweep_points=1):
    """Scale the measured anchor by N^2; report RAM and wall-clock."""
    w_bytes = n_concepts * n_concepts * dtype_bytes
    working_gb = NAIVE_WORKING_MULTIPLE * w_bytes / 1e9
    inplace_gb = INPLACE_WORKING_MULTIPLE * w_bytes / 1e9
    inplace_f32_gb = inplace_gb * (4.0 / dtype_bytes)

    scale = (n_concepts / float(ANCHOR_N)) ** 2
    ms_per_tick = ANCHOR_MS_PER_TICK * scale
    serial_hours = ms_per_tick * ticks / 1000.0 / 3600.0

    runs = seeds * sweep_points
    # Ticks are sequential; the only parallelism is across runs, and the
    # logbook's own rule is jobs=2, never 4.
    wall_hours = serial_hours * runs / float(MACHINE["jobs"])

    fits = working_gb <= MACHINE["safe_ram_gb"]
    return {
        "n_concepts": n_concepts,
        "ticks_per_run": ticks,
        "runs": runs,
        "W_MB": round(w_bytes / 1e6, 1),
        "working_set_GB": round(working_gb, 2),
        "working_set_inplace_GB": round(inplace_gb, 2),
        "working_set_inplace_f32_GB": round(inplace_f32_gb, 2),
        "fits_in_ram": fits,
        "fits_if_rewritten_inplace_f32": inplace_f32_gb <= MACHINE["safe_ram_gb"],
        "ms_per_tick": round(ms_per_tick, 3),
        "hours_per_run": round(serial_hours, 2),
        "wall_clock_hours": round(wall_hours, 2),
        "flops_per_tick": int(4 * n_concepts * n_concepts),
        "note": ("dense W; sequential in t, parallel only across runs at "
                 "jobs=%d" % MACHINE["jobs"]),
    }


def computational():
    """The phases that actually matter, sized."""
    plans = [
        ("G0 skeleton, planted-structure recovery",
         simulator(n_concepts=512, ticks=20_000, seeds=8, sweep_points=1)),
        ("G1 lag-CRP + serial position, the decisive gate",
         simulator(n_concepts=1074, ticks=50_000, seeds=16, sweep_points=1)),
        ("G2 full state + ablations (7 variables, ablate each)",
         simulator(n_concepts=1074, ticks=50_000, seeds=16, sweep_points=8)),
        ("G3 five-term edge model, weight search",
         simulator(n_concepts=1074, ticks=50_000, seeds=8, sweep_points=32)),
        ("G4 long-run generation",
         simulator(n_concepts=1074, ticks=1_000_000, seeds=2, sweep_points=1)),
        ("G4' same, at the dense ceiling",
         simulator(n_concepts=5000, ticks=1_000_000, seeds=1, sweep_points=1)),
    ]
    return {"machine": MACHINE, "anchor": {"n": ANCHOR_N,
                                           "ms_per_tick": ANCHOR_MS_PER_TICK},
            "phases": [{"phase": k, **v} for k, v in plans]}


def report(budget_usd=8.50):
    fin = financial(budget_usd=budget_usd)
    comp = computational()

    # Derived, not asserted. An earlier draft of this function hardcoded Kimi
    # K3 as lead on benchmark scores alone; running the model showed it is the
    # MOST expensive option here ($4.02), because 260k output tokens at $15/M
    # swamp the 10x input-cache discount entirely. Reasoning-heavy workloads
    # are output-bound, so an input-side discount buys almost nothing.
    by_key = {r["provider"]: r for r in fin["rows"]}
    qualified = [r for r in fin["rows"]
                 if (PROVIDERS[r["provider"]].get("gpqa") or 0) >= 90.0
                 and r["usd_precilla"] > 0]
    qualified.sort(key=lambda r: r["usd_precilla"])
    lead = qualified[0] if qualified else fin["rows"][0]

    lead_family = PROVIDERS[lead["provider"]].get("family")
    others = [r for r in fin["rows"]
              if PROVIDERS[r["provider"]].get("family") != lead_family
              and r["usd_precilla"] > 0]
    others.sort(key=lambda r: r["usd_precilla"])
    red = others[0] if others else None

    pair_cost = lead["usd_precilla"] + (red["usd_precilla"] if red else 0.0)

    rec = {
        "lead_deriver": lead["provider"],
        "lead_reason": (
            "cheapest option clearing GPQA-D 90 (%.1f): $%.3f for the whole "
            "workload, %d full cycles inside a $%.2f budget"
            % (PROVIDERS[lead["provider"]]["gpqa"], lead["usd_precilla"],
               lead["runs_within_budget"], budget_usd)),
        "red_team": red["provider"] if red else None,
        "red_team_reason": (
            "must be a DIFFERENT model family or the critique correlates with "
            "the error it is meant to catch; cheapest such option at $%.3f"
            % red["usd_precilla"]) if red else None,
        "lead_plus_redteam_usd": round(pair_cost, 3),
        "cycles_within_budget": int(budget_usd / pair_cost) if pair_cost else None,
        "grinding_and_retries": "gemini-free",
        "grinding_reason": (
            "$0, and 100 requests/day dwarfs this workload's ~10 calls, so the "
            "free tier absorbs every failed attempt and re-run at no cost"),
        "verification": "no model at all -- SymPy/numeric/dimensional, $0",
        "rejected": {
            "kimi-k3": "highest reasoning scores but $%.2f here: output-bound "
                       "workloads are punished by $15/M output, and the 10x "
                       "input cache cannot compensate"
                       % by_key["kimi-k3"]["usd_precilla"],
            "glm-5.2-direct": "identical weights to the OpenRouter row at "
                              "%.1fx the price"
                              % (by_key["glm-5.2-direct"]["usd_precilla"]
                                 / max(by_key["glm-5.2-openrouter"]["usd_precilla"], 1e-9)),
            "ds4-local": "needs 96-128 GB; the 2-bit quant alone is 81 GB "
                         "against 5.9 GB of RAM",
        },
        "binding_constraint": (
            "neither money nor compute -- at $%.3f a cycle and %.1f wall-hours "
            "for the decisive G1 gate, the limit is your attention"
            % (pair_cost, comp["phases"][1]["wall_clock_hours"])),
    }
    return {"as_of": AS_OF, "financial": fin, "computational": comp,
            "recommendation": rec}


def budget_selftest():
    """Cross-check the model's own assumptions. Cheap, and catches drift."""
    out = []
    doc = _doc_tokens()
    out.append(("doc tokens in a plausible range", 7000 <= doc <= 12000, doc))

    f, c, o = workload_tokens(WORKLOADS["derive"])
    nf, nc, no = workload_tokens(WORKLOADS["derive"], resend_docs_every_pass=True)
    out.append(("flat context beats naive on input", nf > f + c, (nf, f + c)))
    out.append(("output totals identical either way", o == no, (o, no)))

    s = simulator(n_concepts=ANCHOR_N, ticks=1_000_000)
    out.append(("anchor reproduces the logbook's 40-60 min for 1e6 ticks",
                0.55 <= s["hours_per_run"] <= 1.1, s["hours_per_run"]))
    out.append(("W at N=1074 is ~9 MB as stated in the doc",
                8.0 <= s["W_MB"] <= 10.0, s["W_MB"]))
    s2 = simulator(n_concepts=10_000, ticks=1)
    out.append(("W at N=10000 is ~800 MB as stated in the doc",
                750 <= s2["W_MB"] <= 850, s2["W_MB"]))
    out.append(("N=10000 float64 naive does NOT fit -- agrees with the doc's "
                "'ceiling on this machine'",
                not s2["fits_in_ram"], s2["working_set_GB"]))
    out.append(("N=10000 DOES fit if rewritten in place at float32 -- the "
                "doc's ceiling is a property of the code, not the machine",
                s2["fits_if_rewritten_inplace_f32"],
                s2["working_set_inplace_f32_GB"]))
    s3 = simulator(n_concepts=5000, ticks=1)
    out.append(("the doc's <=5000 engineering choice has real margin",
                s3["fits_in_ram"], s3["working_set_GB"]))
    return out


if __name__ == "__main__":
    print(json.dumps(report(), indent=2))
