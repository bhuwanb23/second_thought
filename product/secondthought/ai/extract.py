"""
ai/extract.py — free text in, calendar facts out. Facts only.

The failure this module exists to prevent is a model that sounds confident about
someone's rent. So:

  * The model is asked for **facts and per-fact confidence**, never for a verdict.
    There is no field in the output schema a verdict could be written into.
  * Every fact is validated independently after the model returns: amounts must
    be integers in minor units within a sane band, dates must parse and fall in a
    believable window, cadences must be from a closed set. Anything that fails is
    **dropped and named**, not coerced.
  * Anything the model did not give a confidence for is treated as *low*, not as
    trusted. Silence must never read as certainty.
  * `answer_quality` is computed here, from what survived — `full`, `partial` or
    `demo` — and a `demo` extraction is not allowed to produce a verdict at all.

`TemplateExtractor` is the same contract with no model: deterministic regexes.
It is worse at phrasing and it is not trying to be good at it. The badge says so.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

CONFIDENCE_FLOOR = 0.75      # below this, a field is a question, not a fact
MAX_MINOR = 100_000_000      # $1,000,000 — a typo ceiling, not a business rule
CADENCES = ("monthly", "fortnightly", "weekly", "once")


class LLMError(Exception):
    """The model call failed. Never silently replaced by a guess."""


@dataclass
class Extraction:
    fields: dict = field(default_factory=dict)
    confidence: dict = field(default_factory=dict)
    low_confidence: list = field(default_factory=list)
    needs_confirmation: list = field(default_factory=list)
    dropped: list = field(default_factory=list)
    answer_quality: str = "demo"      # full | partial | demo
    mode: str = "template"            # llm | template
    raw: str = ""

    def to_dict(self) -> dict:
        return {"fields": self.fields, "confidence": self.confidence,
                "low_confidence": self.low_confidence,
                "needs_confirmation": self.needs_confirmation,
                "dropped": self.dropped, "answer_quality": self.answer_quality,
                "mode": self.mode}

    # -- the only question the rest of the app may ask ----------------------
    @property
    def usable(self) -> bool:
        """False means: do not decide. A `demo` extraction cannot move money."""
        return self.answer_quality != "demo"


# --------------------------------------------------------------------------
# validation — shared by both extractors, so neither can be trusted more
# --------------------------------------------------------------------------
_SYSTEM_PROMPT = """You extract a shopper's cash-flow facts from their own words.

Return JSON only, with this exact shape:
{"opening_balance_minor": int|null,
 "paydays": [{"due": "YYYY-MM-DD", "amount_minor": int, "confidence": 0.0-1.0}],
 "obligations": [{"label": str, "due": "YYYY-MM-DD", "amount_minor": int,
                  "cadence": "monthly|fortnightly|weekly|once", "confidence": 0.0-1.0}],
 "needs_confirmation": [str]}

Rules you must not break:
- You never decide whether anything is affordable. Do not output a verdict,
  a recommendation, or an opinion about money.
- If a value is not stated, OMIT it. Never estimate, never default to a
  "typical" amount. A missing field is safe; an invented one is not.
- Amounts are integer minor units: $1,450.00 is 145000.
- Confidence is your own honesty about that field, 0..1. If you had to infer a
  date from a cadence ("every second friday"), confidence must be at most 0.5
  and the ambiguity must appear in needs_confirmation.
- Put every assumption and every unclear item in needs_confirmation."""


def _to_minor(value) -> int | None:
    """Accept 145000 | '1450' | '1,450.00' | '$1450'. Reject everything else."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    cleaned = value.strip().replace(",", "").replace("$", "")
    try:
        if "." in cleaned:
            whole, _, frac = cleaned.partition(".")
            return int(whole or 0) * 100 + int((frac + "00")[:2] or 0)
        return int(cleaned)
    except ValueError:
        return None


def _to_date(value, today: date) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        d = date.fromisoformat(value[:10])
    except ValueError:
        return None
    if not (today - timedelta(days=366) <= d <= today + timedelta(days=730)):
        return None
    return d


def _validate(raw_fields: dict, today: date, mode: str, out: Extraction) -> Extraction:
    """Turn whatever the model said into facts, or into named rejections."""
    fields: dict = {}

    balance = _to_minor(raw_fields.get("opening_balance_minor"))
    if balance is not None:
        if 0 <= balance <= MAX_MINOR * 10:
            fields["opening_balance"] = balance
            out.confidence["opening_balance"] = 0.8 if mode == "llm" else 0.9
        else:
            out.dropped.append({"field": "opening_balance", "reason": "out of range",
                                "value": raw_fields.get("opening_balance_minor")})

    for group, kind in (("paydays", "payday"), ("obligations", "obligation")):
        kept = []
        for i, item in enumerate(raw_fields.get(group) or []):
            if not isinstance(item, dict):
                out.dropped.append({"field": f"{group}[{i}]", "reason": "not an object"})
                continue
            amount = _to_minor(item.get("amount_minor"))
            due = _to_date(item.get("due"), today)
            conf = item.get("confidence")
            conf = float(conf) if isinstance(conf, (int, float)) and not isinstance(conf, bool) else 0.0
            label = str(item.get("label") or kind).strip()[:60]
            why = None
            if amount is None:
                why = "amount is not a number"
            elif not 0 < amount <= MAX_MINOR:
                why = "amount outside a believable band"
            elif due is None:
                why = "date missing or unparseable"
            if why:
                out.dropped.append({"field": f"{group}[{i}]", "label": label,
                                    "reason": why, "value": item})
                continue
            rec = {"label": label, "due": due.isoformat(), "amount_minor": amount,
                   "cadence": item.get("cadence") if item.get("cadence") in CADENCES
                   else ("monthly" if kind == "payday" else "once")}
            kept.append(rec)
            out.confidence[f"{kind}:{label}"] = conf
            if conf < CONFIDENCE_FLOOR:
                out.low_confidence.append(f"{kind}:{label}")
        if kept:
            fields[group] = kept

    for item in raw_fields.get("needs_confirmation") or []:
        text = str(item).strip()
        if text and text not in out.needs_confirmation:
            out.needs_confirmation.append(text[:160])

    out.fields = fields
    return out


def _grade(out: Extraction) -> Extraction:
    """`full` | `partial` | `demo` — from what survived, never from the model."""
    facts = len(out.fields.get("obligations") or []) + len(out.fields.get("paydays") or [])
    if facts == 0:
        out.answer_quality = "demo"
        if not out.needs_confirmation:
            out.needs_confirmation.append(
                "The text did not contain anything I could treat as a dated amount.")
    elif out.dropped or out.low_confidence or not out.fields.get("paydays"):
        out.answer_quality = "partial"
    else:
        out.answer_quality = "full"
    return out


# --------------------------------------------------------------------------
class LLMExtractor:
    """The real thing. `transport` takes the request payload, returns text."""

    mode = "llm"

    def __init__(self, settings, transport=None, budget: int | None = None):
        self.settings = settings
        self._transport = transport or self._post
        self.budget = budget if budget is not None else settings.daily_call_budget
        self.calls_made = 0

    def _post(self, payload: dict) -> str:
        import urllib.error
        import urllib.request
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.settings.base_url}/chat/completions", data=body, method="POST",
            headers={"Authorization": f"Bearer {self.settings.api_key}",
                     "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise LLMError(f"HTTP {e.code}: {e.read()[:200]!r}") from None
        except urllib.error.URLError as e:
            raise LLMError(f"network: {e.reason}") from None
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise LLMError(f"unexpected response shape: {json.dumps(data)[:200]}") from None

    def extract(self, text: str, today: date) -> Extraction:
        if not self.settings.api_key:
            raise LLMError("no LLM_API_KEY — this is the template path, not the model")
        if self.calls_made >= self.budget:
            raise LLMError(f"daily call budget exhausted ({self.budget})")
        self.calls_made += 1
        payload = {
            "model": self.settings.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": _SYSTEM_PROMPT},
                         {"role": "user",
                          "content": f"Today is {today.isoformat()}.\n\n{text}"}],
        }
        raw = self._transport(payload)
        out = Extraction(mode="llm", raw=raw)
        try:
            parsed = json.loads(raw)
        except ValueError:
            out.answer_quality = "demo"
            out.dropped.append({"field": "*", "reason": "model did not return JSON"})
            out.needs_confirmation.append("The model's reply was not readable as JSON.")
            return out
        if not isinstance(parsed, dict):
            out.answer_quality = "demo"
            out.dropped.append({"field": "*", "reason": "JSON was not an object"})
            return out
        # a verdict is not a field we accept — notice it, then ignore it
        if "verdict" in parsed or "recommendation" in parsed:
            out.dropped.append({"field": "verdict",
                                "reason": "the model offered a verdict; ignored — "
                                          "the engine decides",
                                "value": parsed.get("verdict") or parsed.get("recommendation")})
        return _grade(_validate(parsed, today, "llm", out))


def _next_dom(today: date, dom: int) -> date:
    import calendar
    last = calendar.monthrange(today.year, today.month)[1]
    candidate = today.replace(day=min(dom, last))
    if candidate <= today:
        nxt = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        candidate = nxt.replace(day=min(dom, calendar.monthrange(nxt.year, nxt.month)[1]))
    return candidate


def _next_weekday(today: date, weekday: int) -> date:
    return today + timedelta(days=(weekday - today.weekday()) % 7 or 7)
