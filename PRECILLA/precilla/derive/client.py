"""
PRECILLA / derive / client.py

A minimal OpenAI-compatible chat client.

Deliberately generic: it speaks `/v1/chat/completions` and nothing else, so
OpenRouter, Moonshot, DeepSeek direct, a local `ds4-server`, or anything else
with that endpoint are all the same code path. The base URL is the only thing
that changes.

Transport is injected (`transport=`) so the whole pipeline can be tested
without spending money. That is not a nicety -- an untested billing path is how
you discover a bug by being charged for it.

stdlib only.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_BASE = os.environ.get("PRECILLA_BASE_URL",
                              "https://openrouter.ai/api/v1")
KEY_ENV = "OPENROUTER_API_KEY"


class ClientError(RuntimeError):
    pass


class SpendRefused(RuntimeError):
    pass


def _key():
    k = os.environ.get(KEY_ENV, "").strip()
    if not k:
        raise ClientError(
            "no API key: export %s=... (get one at openrouter.ai/keys)" % KEY_ENV)
    return k


def http_transport(url, payload, headers, timeout=600):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"), headers=headers,
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8")[:600]
        except Exception:
            pass
        raise ClientError("HTTP %s: %s" % (e.code, body))
    except Exception as e:
        raise ClientError("%s: %s" % (type(e).__name__, e))


def chat(messages, model, base_url=None, temperature=0.2, max_tokens=None,
         transport=None, timeout=600, extra=None):
    """
    Returns (text, usage, raw).

    usage is normalised to include reasoning tokens, which every provider in
    the price table bills as output. Omitting them was the single largest error
    in the first cost estimate, so they are surfaced explicitly here.
    """
    base = (base_url or DEFAULT_BASE).rstrip("/")
    url = base + "/chat/completions"
    payload = {"model": model, "messages": messages,
               "temperature": temperature}
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if extra:
        payload.update(extra)

    headers = {"Content-Type": "application/json"}
    if transport is None:
        headers["Authorization"] = "Bearer " + _key()
        headers["HTTP-Referer"] = "https://github.com/precilla"
        headers["X-Title"] = "PRECILLA"
        transport = http_transport

    t0 = time.time()
    raw = transport(url, payload, headers, timeout)
    elapsed = time.time() - t0

    if isinstance(raw, dict) and raw.get("error") and not raw.get("choices"):
        raise ClientError(str(raw["error"])[:500])

    try:
        text = raw["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError):
        raise ClientError("no content in response: %s" % str(raw)[:400])

    u = raw.get("usage") or {}
    details = u.get("completion_tokens_details") or {}
    prompt_details = u.get("prompt_tokens_details") or {}
    usage = {
        "prompt_tokens": int(u.get("prompt_tokens") or 0),
        "completion_tokens": int(u.get("completion_tokens") or 0),
        "reasoning_tokens": int(details.get("reasoning_tokens") or 0),
        "total_tokens": int(u.get("total_tokens") or 0),
        "cached_tokens": int(prompt_details.get("cached_tokens") or 0),
        "elapsed_s": round(elapsed, 1),
        # OpenRouter reports actual charged cost here when available. Trust it
        # over our own price table whenever it is present.
        "reported_cost_usd": u.get("cost"),
    }
    return text, usage, raw


def list_models(base_url=None, transport=None, timeout=60, filter_str=""):
    """
    Model slugs change. Rather than hardcode a guess, ask.

    `precilla derive models glm` finds the exact slug before you spend anything
    on a typo'd one.
    """
    base = (base_url or DEFAULT_BASE).rstrip("/")
    url = base + "/models"
    if transport is not None:
        data = transport(url, None, {}, timeout)
    else:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.loads(r.read().decode("utf-8"))
        except Exception as e:
            raise ClientError("%s: %s" % (type(e).__name__, e))

    out = []
    for m in (data.get("data") or []):
        mid = m.get("id") or ""
        if filter_str and filter_str.lower() not in mid.lower():
            continue
        pr = m.get("pricing") or {}
        try:
            pin = round(float(pr.get("prompt") or 0) * 1e6, 4)
            pout = round(float(pr.get("completion") or 0) * 1e6, 4)
        except (TypeError, ValueError):
            pin = pout = None
        out.append({"id": mid, "context": m.get("context_length"),
                    "usd_per_m_in": pin, "usd_per_m_out": pout})
    out.sort(key=lambda r: r["id"])
    return out
