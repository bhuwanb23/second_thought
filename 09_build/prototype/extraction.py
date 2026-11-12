"""
extraction.py — job 1 of the AI: prose into structure.

"rent 1450 on the 1st, car loan 312 every second friday, mum's meds about 40
bucks whenever" becomes dated obligations with per-line confidence. A genuine
language task: regex alone fails on "every second friday" and "about 40".

Low-confidence lines are surfaced to the shopper for confirmation. They are
never silently trusted, and they never become settled fact without a human look.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta

from llm import ChatModel, MockChat, Reply, ToolCall

MAX_OBLIGATIONS = 12



# ==========================================================================
# 1. EXTRACTION
# ==========================================================================
@dataclass
class Draft:
    label: str
    amount_minor: int
    due: date | None
    essential: bool = True
    confidence: float = 0.5


@dataclass
class Extraction:
    obligations: list[Draft] = field(default_factory=list)
    income: list[Draft] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    engine: str = "rules"

    def to_dict(self) -> dict:
        def d(x: Draft) -> dict:
            return {"label": x.label, "amount_minor": x.amount_minor,
                    "due": x.due.isoformat() if x.due else None,
                    "essential": x.essential, "confidence": x.confidence}
        return {"obligations": [d(o) for o in self.obligations],
                "income": [d(i) for i in self.income],
                "warnings": self.warnings, "engine": self.engine}


EXTRACTION_SYSTEM = (
    "You turn a person's description of their month into structured data. "
    "Extract only what they actually said. Never invent an amount or a date. "
    "If an amount is vague ('about 40 bucks', 'roughly'), still extract it and set "
    "confidence below 0.6. Money is in minor units: $1,450.00 -> 145000. "
    "Resolve relative dates against the given today. Return JSON only."
)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "obligations": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "amount_minor": {"type": "integer"},
                "due": {"type": "string"},
                "essential": {"type": "boolean"},
                "confidence": {"type": "number"},
            },
            "required": ["label", "amount_minor", "due"],
        }},
        "income": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "label": {"type": "string"},
                "amount_minor": {"type": "integer"},
                "due": {"type": "string"},
            },
            "required": ["label", "amount_minor", "due"],
        }},
    },
    "required": ["obligations"],
}


def _parse_money(token: str) -> int | None:
    t = token.replace(",", "").replace("$", "").strip()
    try:
        if "." in t:
            return int(round(float(t) * 100))
        return int(t) * 100
    except ValueError:
        return None


_MONEY = re.compile(r"\$\s?\d[\d,]*(?:\.\d{1,2})?|(?<![\w.])\d[\d,]*(?:\.\d{1,2})?(?![\w%])")
_ORDINAL = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b", re.I)
_MONTHS = ("january february march april may june july august september october "
           "november december").split()


def rule_extract(text: str, today: date) -> Extraction:
    """
    Deterministic extractor. Weaker than a model on messy prose, but it never
    hallucinates and it is the fallback when no key is present.
    """
    out = Extraction(engine="rules")
    for raw_line in re.split(r"[;\n]|,\s*(?=[a-zA-Z])", text):
        line = raw_line.strip(" .")
        if not line:
            continue
        money = _MONEY.search(line)
        if not money:
            continue
        amount = _parse_money(money.group(0))
        if not amount or amount <= 0:
            continue
        label = re.sub(r"\$\s?\d[\d,]*(?:\.\d{1,2})?", "", line)
        label = re.sub(r"(?i)\b(on|every|the|about|roughly|around|due)\b", " ", label)
        label = re.sub(r"\b\d{1,2}(st|nd|rd|th)\b", "", label, flags=re.I)
        label = re.sub(r"\s+", " ", label).strip(" ,-")
        due = None
        ord_m = _ORDINAL.search(line)
        if ord_m:
            day = min(max(int(ord_m.group(1)), 1), 28)
            due = today.replace(day=day)
            if due <= today:
                due = (due.replace(day=28) + timedelta(days=7)).replace(day=day)
        for i, m in enumerate(_MONTHS, 1):
            if re.search(m, line, re.I):
                due = due or date(today.year if i >= today.month else today.year + 1, i, 1)
                break
        if not label:
            continue
        out.obligations.append(Draft(
            label=label[:40], amount_minor=amount, due=due or today, confidence=0.4))
        if len(out.obligations) >= MAX_OBLIGATIONS:
            break
    if not out.obligations:
        out.warnings.append("could not read any amounts — try 'rent 1450 on the 1st'")
    return out


def validate_extraction(payload: dict, today: date) -> Extraction:
    """Strict validation of model output. Anything malformed raises."""
    if not isinstance(payload, dict):
        raise ValueError("extraction must be an object")
    obls = payload.get("obligations")
    if not isinstance(obls, list) or not obls:
        raise ValueError("no obligations")
    if len(obls) > MAX_OBLIGATIONS:
        raise ValueError("too many obligations")

    out = Extraction(engine="llm")
    for item in obls:
        if not isinstance(item, dict):
            raise ValueError("obligation must be an object")
        label = str(item.get("label") or "").strip()
        amount = item.get("amount_minor")
        if not label:
            raise ValueError("obligation needs a label")
        if not isinstance(amount, int) or amount <= 0 or amount > 10_000_000:
            raise ValueError(f"bad amount_minor for {label}: {amount!r}")
        due_raw = item.get("due")
        try:
            due = date.fromisoformat(str(due_raw))
        except (ValueError, TypeError):
            raise ValueError(f"bad due date for {label}: {due_raw!r}")
        if not (today - timedelta(days=40) <= due <= today + timedelta(days=400)):
            raise ValueError(f"due date out of range for {label}")
        conf = item.get("confidence", 0.8)
        if not isinstance(conf, (int, float)) or not (0 <= conf <= 1):
            conf = 0.8
        out.obligations.append(Draft(label=label[:40], amount_minor=amount, due=due,
                                     essential=bool(item.get("essential", True)),
                                     confidence=float(conf)))
    for item in payload.get("income") or []:
        try:
            out.income.append(Draft(
                label=str(item.get("label", "income"))[:40],
                amount_minor=int(item["amount_minor"]),
                due=date.fromisoformat(str(item["due"])), confidence=0.8))
        except (KeyError, ValueError, TypeError):
            out.warnings.append("dropped an unreadable income entry")
    return out


def extract(text: str, today: date, model: ChatModel | None = None) -> Extraction:
    """
    Model extraction with a deterministic fallback.

    Any failure — no model, network error, malformed JSON, a fantasy date, a
    negative amount — falls back to the rule extractor rather than guessing.
    """
    if model is None or not model.available() or isinstance(model, MockChat):
        if isinstance(model, MockChat):
            return _extract_with_mock(text, today, model)
        return rule_extract(text, today)
    try:
        reply = model.complete([
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": json.dumps({"today": today.isoformat(),
                                                    "text": text})},
        ], temperature=0)
        payload = json.loads(reply.content) if reply.content else {}
        result = validate_extraction(payload, today)
        result.engine = "llm"
        return result
    except Exception as exc:                                    # noqa: BLE001
        fallback = rule_extract(text, today)
        fallback.warnings.append(f"model extraction failed ({type(exc).__name__}); used rules")
        return fallback


def _extract_with_mock(text: str, today: date, model: MockChat) -> Extraction:
    if model.script:
        reply = model.script.pop(0)
        if reply.tool_calls:
            payload = reply.tool_calls[0].arguments
        else:
            payload = json.loads(reply.content or "{}")
        try:
            result = validate_extraction(payload, today)
            result.engine = "llm-mock"
            return result
        except ValueError as exc:
            fb = rule_extract(text, today)
            fb.warnings.append(f"mock extraction invalid ({exc}); used rules")
            return fb
    return rule_extract(text, today)