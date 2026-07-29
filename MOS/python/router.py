"""
TATIANA — the reasoning router (remote brain).

This machine cannot host a local LLM, so all reasoning is remote on Groq. The
legacy organs all call `router.query_frontier_brain(prompt, context, intent)`,
so that is the interface rebuilt here.

TIERED BRAIN (from the free-tier budget analysis)
-------------------------------------------------
Groq free tier: 30 RPM / 6,000 TPM / ~1,000 requests-per-day, and BOTH
llama-3.1-8b-instant and llama-3.3-70b-versatile are free at those limits. The
6,000 TPM ceiling (~12 pages/min of text, in + out combined) is the binding
constraint, so we spend deliberately:

    intent="triage"   -> 8B   cheap, high-frequency: classification, extraction,
                              routing, canonicalisation decisions
    intent="reason"   -> 70B  scarce, high-value: the actual mathematics

Budget is tracked per process and reported, because running out silently at
request 1,001 is exactly the kind of invisible failure this project exists to
avoid.

HONESTY RULES
-------------
Errors are RAISED or returned as explicit failures, never disguised as empty
content. A rate-limit is not the same as "the model had nothing to say".
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Both are free at the same limits; the difference is capability per call.
MODEL_CHEAP = os.environ.get("GROQ_MODEL_CHEAP", "llama-3.1-8b-instant")
MODEL_HEAVY = os.environ.get("GROQ_MODEL_HEAVY", "llama-3.3-70b-versatile")

CHEAP_INTENTS = {"triage", "classify", "extract", "canonicalize", "route"}


class RouterError(RuntimeError):
    """Raised when the remote brain cannot be reached or refuses the request."""


class RateLimited(RouterError):
    pass


@dataclass
class Budget:
    """Per-process accounting against the free tier."""
    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    by_model: Dict[str, int] = field(default_factory=dict)
    started: float = field(default_factory=time.time)

    def record(self, model: str, usage: dict) -> None:
        self.requests += 1
        self.by_model[model] = self.by_model.get(model, 0) + 1
        self.prompt_tokens += usage.get("prompt_tokens", 0) or 0
        self.completion_tokens += usage.get("completion_tokens", 0) or 0

    def summary(self) -> str:
        elapsed = time.time() - self.started
        # Only report a rate once enough time has passed for it to mean anything.
        # Dividing 2 requests by 0.9s yields "132 rpm" and falsely screams that the
        # 30 RPM cap is blown. A misleading metric is worse than no metric.
        if elapsed >= 30.0:
            rate = f"{self.requests / (elapsed / 60.0):.1f} rpm (30 cap)"
        else:
            rate = f"rate=n/a (only {elapsed:.0f}s elapsed)"
        return (f"requests={self.requests} (~1000/day cap) "
                f"tokens={self.prompt_tokens}+{self.completion_tokens} "
                f"{rate} models={self.by_model}")


class CloudRouter:
    """Async wrapper over Groq chat-completions with model tiering."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY", "")
        if not self.api_key:
            raise RouterError(
                "GROQ_API_KEY is not set. Set it with:  setx GROQ_API_KEY \"your_key\"  "
                "then open a new terminal.")
        self.timeout = timeout
        self.budget = Budget()

    @staticmethod
    def pick_model(intent: str) -> str:
        return MODEL_CHEAP if (intent or "").lower() in CHEAP_INTENTS else MODEL_HEAVY

    async def query_frontier_brain(self, prompt: str, context: str = "",
                                   intent: str = "reason",
                                   json_mode: bool = False,
                                   temperature: Optional[float] = None) -> str:
        """The interface every legacy organ calls. Returns the model's text.

        Raises RateLimited / RouterError rather than returning empty string, so a
        failure can never be mistaken for a genuine empty answer.
        """
        model = self.pick_model(intent)
        messages = []
        if context:
            messages.append({"role": "system", "content": context})
        messages.append({"role": "user", "content": prompt})

        # Default 0.2 preserved exactly; `temperature` is opt-in so existing
        # callers are byte-identical. E5 needs it: re-eliciting the same
        # judgement at temperature 0 would measure nothing about the
        # instrument's own stability, and stability is what separates a real
        # signal from noise there.
        payload = {"model": model, "messages": messages,
                   "temperature": 0.2 if temperature is None else float(temperature)}
        if json_mode:
            # Groq requires the literal word 'json' somewhere in the messages.
            payload["response_format"] = {"type": "json_object"}
            if "json" not in (prompt + context).lower():
                payload["messages"][-1]["content"] += "\n\nRespond only with valid json."

        def _call():
            return requests.post(
                GROQ_URL,
                headers={"Authorization": f"Bearer {self.api_key}",
                         "Content-Type": "application/json"},
                json=payload, timeout=self.timeout)

        # requests is blocking; keep the event loop free.
        resp = await asyncio.to_thread(_call)

        if resp.status_code == 429:
            raise RateLimited(
                f"Groq rate limit (30 RPM / 6k TPM / ~1k RPD). {self.budget.summary()}")
        if resp.status_code != 200:
            raise RouterError(f"Groq HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        self.budget.record(model, data.get("usage", {}) or {})
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise RouterError(f"Malformed Groq response: {e}") from e


if __name__ == "__main__":
    import console
    console.setup()  # math output contains Delta/rho/omega; cp1252 would crash

    async def main():
        r = CloudRouter()
        print("cheap model:", MODEL_CHEAP)
        print("heavy model:", MODEL_HEAVY)
        print("routing 'triage' ->", r.pick_model("triage"))
        print("routing 'reason' ->", r.pick_model("reason"))

        print("\n--- cheap tier (triage) ---")
        out = await r.query_frontier_brain(
            "Reply with exactly one word: OK", intent="triage")
        print("   ", out.strip()[:80])

        print("\n--- heavy tier (reason) ---")
        out = await r.query_frontier_brain(
            "In one sentence: what is the Hodge-de Rham Laplacian on 1-forms?",
            intent="reason")
        print("   ", out.strip()[:220])

        print("\nbudget:", r.budget.summary())

    asyncio.run(main())
