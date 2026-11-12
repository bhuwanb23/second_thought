"""
agent.py — the language layer.

The engine decides. This module only chooses words. It is structurally
incapable of changing a verdict: every path re-reads the engine's verdict
after generation and rejects the output if it disagrees.

Two implementations:
  TemplateExplainer  deterministic, always available, used as the fallback
  LLMExplainer       calls an OpenAI-compatible endpoint if configured

Both must satisfy the same contract, and the contract has a test.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from engine import Decision

REQUIRED_KEYS = ("headline", "why", "alternative", "verdict")


class ExplainerError(RuntimeError):
    pass


def money(minor: int, currency: str = "USD") -> str:
    symbol = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}.get(currency, "")
    sign = "-" if minor < 0 else ""
    major, cents = divmod(abs(minor), 100)
    return f"{sign}{symbol}{major:,}.{cents:02d}"


def _date(d) -> str:
    return d.strftime("%-d %b") if d else ""


# --------------------------------------------------------------------------
# deterministic
# --------------------------------------------------------------------------
class TemplateExplainer:
    """No model. Never fails. This is the floor of the product experience."""

    name = "template"

    def explain(self, decision: Decision, context: dict | None = None) -> dict:
        cur = decision.currency
        amt = money(decision.amount, cur)
        ctx = context or {}
        merchant = ctx.get("merchant", "this store")

        if decision.verdict == "OFFER":
            headline = f"{amt} in 4 works for you."
            why = (
                f"After every payment, your lowest balance over the next six weeks "
                f"stays at {money(_min_of(decision), cur)}. "
                f"We keep a {money(decision.buffer, cur)} cushion for you."
            )
            alternative = "Nothing to change. Pay in 4 if you want to."

        elif decision.verdict == "DEFER":
            due = decision.recommended.invoice_due if decision.recommended else None
            if decision.reason_code == "partial_now_rest_on_payday":
                part = money(decision.recommended.partial_now, cur)
                headline = f"Pay {part} now, the rest when you're paid."
                why = (
                    f"Taking the full {amt} today would drop you below your cushion. "
                    f"An invoice for the balance, due {_date(due)}, fits."
                )
            else:
                headline = f"Wait until {_date(due)} — we'll invoice it."
                why = (
                    f"Your money is at its lowest right now and you're paid on {_date(due)}. "
                    f"One invoice on that date fits comfortably; four payments starting today do not."
                )
            alternative = (
                f"We'll send an invoice due {_date(due)}. Same {amt}, better timing."
            )

        else:  # DECLINE
            own, ext = _collision_sides(decision)
            if own and ext:
                headline = f"{own.capitalize()} lands the same day as {ext}."
            elif own:
                headline = f"{own.capitalize()} doesn't fit this month."
            elif ext:
                headline = f"This collides with {ext}."
            else:
                headline = "This doesn't fit your next six weeks."
            why = (
                f"Paying {amt} in 4 would put you {money(decision.shortfall, cur)} "
                f"below your {money(decision.buffer, cur)} cushion on {_date(decision.collision_date)}. "
                f"Your lowest point would be {money(_min_of(decision), cur)}."
            )
            if decision.safe_amount > 0:
                alternative = (
                    f"Up to {money(decision.safe_amount, cur)} would work at {merchant} today. "
                    f"You can still buy it in full — this is advice, not a block."
                )
            else:
                alternative = (
                    "Nothing at this size works this month. We'd rather say so than "
                    "hand you a late fee. You can still buy it — this is advice, not a block."
                )

        return {
            "headline": headline,
            "why": why,
            "alternative": alternative,
            "verdict": decision.verdict,
            "engine": self.name,
        }


def _collision_sides(decision: Decision) -> tuple[str | None, str | None]:
    """The two sides of the collision, taken from the option that matters."""
    for kind in ("PAY_IN_4", "DEFER_TO_PAYDAY", "PAY_NOW"):
        for o in decision.options:
            if o.kind == kind and (o.collision_own or o.collision_external):
                return o.collision_own, o.collision_external
    return None, None


def _min_of(decision: Decision) -> int:
    """Lowest projected balance across the options that matter for this verdict."""
    if decision.verdict == "OFFER" and decision.recommended:
        return decision.recommended.min_balance
    p4 = next((o for o in decision.options if o.kind == "PAY_IN_4"), None)
    if decision.recommended:
        return decision.recommended.min_balance
    return p4.min_balance if p4 else 0


# --------------------------------------------------------------------------
# model-backed
# --------------------------------------------------------------------------
SYSTEM = (
    "You explain a budgeting decision to a shopper in plain, kind, concrete English. "
    "You are given the result of a deterministic calculation. You must not change it: "
    "not the verdict, not any amount, not any date. Explain the numbers you are given. "
    "Never shame the shopper. Never say they cannot afford something; say what does not fit. "
    "Return JSON with exactly these keys: headline, why, alternative, verdict. "
    "The verdict must be copied verbatim from the input."
)


class LLMExplainer:
    """Calls an OpenAI-compatible /chat/completions endpoint. Falls back on any failure."""

    name = "llm"

    def __init__(self, base_url: str | None = None, model: str | None = None,
                 api_key: str | None = None, timeout: int = 20):
        self.base_url = (base_url or os.environ.get("LLM_BASE_URL")
                         or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        self.api_key = api_key or os.environ.get("LLM_API_KEY", "")
        self.timeout = timeout
        self.fallback = TemplateExplainer()

    def available(self) -> bool:
        return bool(self.api_key)

    def explain(self, decision: Decision, context: dict | None = None) -> dict:
        if not self.available():
            return self.fallback.explain(decision, context)

        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(
                    {"decision": decision.to_dict(), "context": context or {}}, default=str)},
            ],
        }
        try:
            req = urllib.request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {self.api_key}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode())
            raw = body["choices"][0]["message"]["content"]
            parsed = json.loads(raw)
            return self._validate(parsed, decision)
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError,
                json.JSONDecodeError, ExplainerError, ValueError):
            out = self.fallback.explain(decision, context)
            out["fallback_reason"] = "model_unavailable_or_invalid"
            return out

    @staticmethod
    def _validate(parsed: dict, decision: Decision) -> dict:
        if not isinstance(parsed, dict):
            raise ExplainerError("model did not return an object")
        for key in REQUIRED_KEYS:
            if key not in parsed:
                raise ExplainerError(f"missing key {key}")
            if not isinstance(parsed[key], str) or not parsed[key].strip():
                raise ExplainerError(f"empty key {key}")
        if parsed["verdict"] != decision.verdict:
            raise ExplainerError(
                f"model changed the verdict: {parsed['verdict']} != {decision.verdict}")
        out = {k: parsed[k].strip() for k in REQUIRED_KEYS}
        out["engine"] = "llm"
        return out


# --------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------
def explain(decision: Decision, context: dict | None = None,
            explainer=None) -> dict:
    """
    Explain a decision, then verify the verdict survived the explanation.

    The assertion is the safety property the whole product rests on: the model
    may phrase a decision, it may never make one.
    """
    expl = explainer or LLMExplainer()
    before = decision.verdict
    out = expl.explain(decision, context)
    if out.get("verdict") != before:  # belt and braces — LLMExplainer already checks
        fb = TemplateExplainer().explain(decision, context)
        fb["fallback_reason"] = "verdict_changed_after_explanation"
        return fb
    assert decision.verdict == before, "engine verdict changed during explanation"
    return out


if __name__ == "__main__":
    from personas import DEFAULT_POLICY, PERSONAS
    from engine import decide

    for key, (fn, label, amount) in PERSONAS.items():
        d = decide(fn(), amount, policy=DEFAULT_POLICY)
        e = explain(d, {"merchant": "Northwind Audio"}, explainer=TemplateExplainer())
        print(f"\n{label}  [{d.verdict}]")
        print(f"  {e['headline']}")
        print(f"  {e['why']}")
        print(f"  {e['alternative']}")
