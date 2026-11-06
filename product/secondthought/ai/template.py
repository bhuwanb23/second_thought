"""
ai/template.py — the deterministic reader. The lesser mode, and it says so.

Kept apart from `extract.py` because the two differ in exactly one way that
matters: one is a model, one is regexes. Sharing the *validation* is what makes
the comparison fair — the model does not get trusted more than the regex, and
neither gets trusted more than a human confirmation.

It reads what is written plainly. "rent 1450 on the 28th" it gets. "twenty nine
dollars" it does not, and it records that it could not rather than guessing.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from .extract import (CONFIDENCE_FLOOR, MAX_MINOR, Extraction, _grade,
                      _next_dom, _next_weekday)

# --------------------------------------------------------------------------
# the template reader: segment by segment, because a person writes clause by clause
# --------------------------------------------------------------------------
_NUM = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)|(\d[\d,]*(?:\.\d{1,2})?)")
_ORD = re.compile(r"(\d{1,2})(?:st|nd|rd|th)\b", re.I)
_SPLIT = re.compile(r",(?!\d)|;|\.(?:\s|$)")

_CADENCE = (("every second", "fortnightly"), ("every other", "fortnightly"),
            ("fortnightly", "fortnightly"), ("every two weeks", "fortnightly"),
            ("every week", "weekly"), ("weekly", "weekly"),
            ("a month", "monthly"), ("per month", "monthly"), ("monthly", "monthly"),
            ("/mo", "monthly"))

_STOPWORDS = {"is", "are", "was", "were", "my", "the", "a", "an", "s", "it", "its",
              "and", "oh", "so", "like", "just", "then", "there", "i", "on", "of",
              "for", "due", "comes", "out", "lands", "pay", "paid", "about",
              "roughly", "around", "automatically", "every", "second", "month",
              "week", "dollars", "bucks", "usd", "s"}


def _dollars_to_minor(raw: str) -> int | None:
    """A number written by a human is dollars. A number from the model is cents.

    Mixing the two is the classic hundred-fold error, so they use different
    functions and neither one guesses.
    """
    cleaned = raw.strip().replace(",", "").replace("$", "")
    try:
        if "." in cleaned:
            whole, _, frac = cleaned.partition(".")
            return int(whole or 0) * 100 + int((frac + "00")[:2] or 0)
        return int(cleaned) * 100
    except ValueError:
        return None


_ORDINAL_JUNK = {"st", "nd", "rd", "th"}


def _label(chunk: str) -> str:
    words, seen = [], set()
    for w in re.split(r"[^A-Za-z']+", chunk.lower()):
        w = w.strip("'")
        if not w or w in _STOPWORDS or w in _ORDINAL_JUNK or w.isdigit() or w in seen:
            continue
        seen.add(w)
        words.append(w)
    return (" ".join(words[:3]) or "item").strip()


class TemplateExtractor:
    """Deterministic, honest, and clearly the lesser mode."""

    mode = "template"
    _INCOME = re.compile(r"\b(salary|wages?|income|payday|paycheck|deposit|pension)\b"
                         r"|\bpay\b|\bgets? paid\b|\blands\b", re.I)

    def _segments(self, text: str) -> list[dict]:
        segs = []
        for chunk in _SPLIT.split((text or "").replace(" and ", ", ")):
            chunk = chunk.strip()
            if not chunk:
                continue
            amounts, day = [], None
            for m in _NUM.finditer(chunk):
                raw = (m.group(1) or m.group(2) or "").strip()
                if not raw:
                    continue
                ordinal = _ORD.match(chunk[m.start():])
                if ordinal and 1 <= int(ordinal.group(1)) <= 31:
                    day = day or int(ordinal.group(1))
                    continue
                value = _dollars_to_minor(raw)
                if value is not None and 0 < value <= MAX_MINOR:
                    amounts.append(value)
            segs.append({"text": chunk, "amounts": amounts, "day": day,
                         "label": _label(chunk), "day_label": _label(chunk) if day else "",
                         "approx": bool(re.search(r"[~≈]|\babout\b|\broughly\b|"
                                                  r"\baround\b", chunk, re.I))})
        # a clause often splits as "pay lands on the 15th, 2,400 a month":
        # carry the day, and its subject, into the half that has the number
        for i in range(len(segs) - 1):
            if segs[i]["day"] and not segs[i]["amounts"] \
                    and not segs[i + 1]["day"] and segs[i + 1]["amounts"]:
                segs[i + 1]["day"] = segs[i]["day"]
                segs[i + 1]["day_label"] = segs[i]["day_label"]
                segs[i]["carried"] = True
        return segs

    def extract(self, text: str, today: date) -> Extraction:
        out = Extraction(mode="template", raw=text)
        obligations, paydays = [], []
        for seg in self._segments(text):
            if not seg["amounts"]:
                if seg["day"] and not seg.get("carried"):
                    out.dropped.append({"field": "obligation", "label": seg["day_label"],
                                        "reason": "a date with no amount I can read",
                                        "value": seg["text"][:70]})
                continue
            amount = max(seg["amounts"])
            low = seg["text"].lower()
            cadence = next((c for word, c in _CADENCE if word in low), "once")
            label = seg["day_label"] or seg["label"]
            if self._INCOME.search(seg["text"]) or (
                    seg["day_label"] and self._INCOME.search(seg["text"] + " "
                                                             + seg["day_label"])):
                kind = "payday"
            else:
                kind = "obligation"
            conf = 0.9
            if seg["day"]:
                due = _next_dom(today, seg["day"])
            elif cadence != "once" and re.search(r"\bfriday\b", low):
                due, conf = _next_weekday(today, 4), 0.45
                out.needs_confirmation.append(
                    f"The date for '{label}' was inferred from a fortnightly Friday "
                    f"cadence — which Friday anchors it?")
            elif cadence != "once":
                due, conf = _next_dom(today, today.day), 0.5
                out.needs_confirmation.append(
                    f"'{label}' repeats {cadence} but no day of the month was given.")
            else:
                due, conf = today + timedelta(days=30), 0.3
                out.needs_confirmation.append(
                    f"'{label}' has an amount but no date I can read.")
            if seg["approx"]:
                conf = min(conf, 0.5)
                out.needs_confirmation.append(
                    f"'{label}' is approximate — confirm the exact amount.")
            rec = {"label": label or kind, "due": due.isoformat(),
                   "amount_minor": amount, "cadence": cadence}
            (paydays if kind == "payday" else obligations).append(rec)
            out.confidence[f"{kind}:{label}"] = conf
            if conf < CONFIDENCE_FLOOR:
                out.low_confidence.append(f"{kind}:{label}")
        if paydays:
            out.fields["paydays"] = paydays
        if obligations:
            out.fields["obligations"] = obligations
        if not paydays:
            out.needs_confirmation.append(
                "No income or payday was mentioned. Without it the product cannot "
                "judge what fits — it can only see money going out.")
        return _grade(out)


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
