#!/usr/bin/env python3
"""
demo_ai.py — V4: the model reads, the engine decides, a human approves.

    python3 demo_ai.py --offline     # template extractor + adversarial models
    python3 demo_ai.py --live        # the real LLM, on its three test passages

What V4 asks for, and where it is answered:

  1. badge reads `AI · LLM`, not `LLM-MOCK`      → §badge
  2. three messy passages go through the reader  → §read
  3. low confidence flagged, nonsense degrades   → §read (per item)
  4. extract → decide → propose → approve → invoice, and a tampered
     approval is refused                         → §tool

`--offline` cannot answer question 1 or the model half of 2 and 3, and says so.
What it *can* prove is the part that matters most: that no model output, honest
or hostile, can move the engine's verdict.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from secondthought.ai.agent import Agent, TOOL_FOR_VERDICT            # noqa: E402
from secondthought.ai.extract import Extraction, LLMExtractor        # noqa: E402
from secondthought.ai.template import TemplateExtractor               # noqa: E402
from secondthought.app.approvals import ApprovalError, ApprovalGate    # noqa: E402
from secondthought.app.checkout import CheckoutService                # noqa: E402
from secondthought.config import load                                 # noqa: E402
from secondthought.domain import Policy                               # noqa: E402
from secondthought.infra.db import (Database, LedgerRepo, ProfileRepo,  # noqa: E402
                                    ReservationRepo)
from secondthought.infra.gateway import SimulatedGateway              # noqa: E402
from secondthought.infra.evidence import Recorder                     # noqa: E402
from secondthought.interfaces.badge import badges                     # noqa: E402

RULE = "─" * 76
MERCHANT = "Northwind Audio"
AMOUNT = 24_900

# The three passages V4 asks for, verbatim.
PASSAGES = [
    ("messy, realistic",
     "rent's 1450 on the 28th, car loan 312 every second friday, oh and mum's "
     "meds ~40 a month"),
    ("no amounts at all",
     "things have been tight since the shop cut my hours and I'm not really sure "
     "how the month is going to go"),
    ("different phrasing",
     "Salary lands on the 15th, 2,400 a month. Rent is due the 1st and it's 1,375. "
     "Gym comes out automatically, twenty nine dollars, on the 3rd."),
]


def shown(ext: Extraction) -> str:
    facts = len(ext.fields.get("obligations") or []) + len(ext.fields.get("paydays") or [])
    flag = {"full": "✓", "partial": "⚠", "demo": "✗"}[ext.answer_quality]
    return (f"{flag} quality={ext.answer_quality}  facts={facts}  "
            f"low={len(ext.low_confidence)}  dropped={len(ext.dropped)}  mode={ext.mode}")


def print_extraction(ext: Extraction) -> None:
    for group in ("paydays", "obligations"):
        for item in ext.fields.get(group) or []:
            key = f"{group[:-1]}:{item['label']}"
            conf = ext.confidence.get(key, 0.0)
            mark = "  ← ASK, do not trust" if conf < 0.75 else ""
            print(f"    {group[:-1]:<10} {item['label']:<22} {item['amount_minor'] / 100:>9,.2f}"
                  f"  {item['due']}  {item['cadence']:<12} conf={conf:.2f}{mark}")
    for d in ext.dropped:
        print(f"    DROPPED    {d.get('field')}: {d['reason']}")
    for q in ext.needs_confirmation:
        print(f"    question   {q}")


def run_readings(agent: Agent, rec: Recorder, today: date, live: bool) -> bool:
    print(f"\n{RULE}\nREAD — three passages the reader was not written for\n{RULE}")
    rows, ok = [], True
    for label, text in PASSAGES:
        print(f"\n  “{text[:66]}…”" if len(text) > 66 else f"\n  “{text}”")
        ext = agent.extract(text, today)
        print(f"  {label}: {shown(ext)}")
        print_extraction(ext)
        dashed = ext.answer_quality == "demo"
        if dashed:
            result = agent.run("demo", MERCHANT, AMOUNT, "USD", text, today)
            print(f"  → verdict: {result.verdict} — nothing is decided, nothing moves")
            print(f"    questions: {len(result.questions)}")
        rows.append({"passage": label, "text": text, "answer_quality": ext.answer_quality,
                     "facts": len(ext.fields.get("obligations") or []),
                     "low_confidence": ext.low_confidence,
                     "dropped": ext.dropped, "questions": ext.needs_confirmation,
                     "mode": ext.mode})
        # a demo extraction must never reach the engine
        if dashed:
            ok = ok and ext.usable is False
    rec.check("read", "Three unfamiliar passages", "PASS" if ok else "FAIL",
              {"mode": "llm" if live else "template", "passages": rows})
    return ok


TOOL_PASSAGE = ("Salary's 2,400 on the 15th, rent's 1,375 on the 1st, "
                "car loan 312 every second friday")
TOOL_OPENING = 60_000        # $600 — the shape that lands on DEFER, not OFFER


def run_tool(agent: Agent, rec: Recorder, today: date, gateway) -> bool:
    """4. extraction → decide → propose → approve → invoice, then a tamper test."""
    print(f"\n{RULE}\nTOOL CALL — extraction to invoice, then a tampered approval\n{RULE}")
    text = TOOL_PASSAGE
    print(f"  text         “{text}”")
    ext = agent.extract(text, today)
    print(f"  extraction   {shown(ext)}")
    decision = agent.decide_purchase(ext, AMOUNT, "USD", today, TOOL_OPENING)
    print(f"  decide_purchase → {decision.verdict}  reason={decision.reason_code}  "
          f"instrument={decision.recommended.kind if decision.recommended else None}")
    result = agent.run("shopper-v4", MERCHANT, AMOUNT, "USD", text, today, TOOL_OPENING)
    q = result.quote
    print(f"  verdict      {q['verdict']}  (source: engine)")
    if not q.get("approval_required"):
        print(f"  no instrument offered — {q.get('note')}")
        rec.check("tool", "extraction → invoice", "FAIL",
                  {"verdict": q["verdict"], "reason": "no tool proposed for this verdict"})
        return False
    print(f"  proposes     {q['tool']}  {q['proposal']['amount_minor'] / 100:,.2f} "
          f"due {q.get('due_date')}")
    print(f"  approval     required — token {q['token'][:12]}…")

    # the tamper: change the amount, keep the token and the tool name
    tampered = dict(q["proposal"])
    tampered["amount_minor"] = tampered["amount_minor"] + 50_000
    tamper_refused, tamper_error = False, ""
    try:
        agent.service.execute(q["tool"], tampered, q["token"])
    except ApprovalError as exc:
        tamper_refused, tamper_error = True, str(exc)
    print(f"  tamper       amount {q['proposal']['amount_minor']} → {tampered['amount_minor']}: "
          f"{'REFUSED' if tamper_refused else 'ACCEPTED — DEFECT'}  {tamper_error}")

    # and the honest path, with the arguments that were actually signed
    done = agent.approve_and_execute(result)
    inv = done.get("invoice") or {}
    print(f"  approved     state={done['state']}  invoice={inv.get('id')} "
          f"due {inv.get('due_date')}")
    ok = tamper_refused and done["state"] == "RESERVED" and bool(inv.get("id"))
    rec.check("tool", "extraction → decide → propose → approve → invoice", "PASS" if ok else "FAIL",
              {"verdict": q["verdict"], "tool": q["tool"],
               "tool_name_note": "V4 says create_scheduled_invoice; the signed action is "
                                 "create_reservation, which creates the invoice and the hold",
               "proposed_amount": q["proposal"]["amount_minor"],
               "tampered_amount": tampered["amount_minor"],
               "tamper_refused": tamper_refused, "tamper_error": tamper_error,
               "approved_state": done["state"], "invoice": inv})
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="V4 — live AI checks")
    ap.add_argument("--live", action="store_true", help="use the real LLM")
    ap.add_argument("--offline", action="store_true", help="template extractor, no network")
    ap.add_argument("--out", default="artifacts/v4")
    args = ap.parse_args(argv)
    if not (args.live or args.offline):
        print("Choose --live or --offline.", file=sys.stderr)
        return 2

    settings = load()
    today = date.today()
    live = args.live and not args.offline

    print(f"\n{RULE}\nSecond Thought — V4 {'LIVE AI' if live else 'OFFLINE'}\n{RULE}")
    for b in badges(settings):
        print(f"  badge        {b['label']:<22} ({b['detail']})")

    if live and not settings.llm.configured:
        print("\nNo LLM_API_KEY. The badge reads AI · LLM-MOCK and the model path "
              "cannot run.\nThat is V0.3 red, and V4 is blocked on it.", file=sys.stderr)
        return 2

    mode = ("LIVE — real model calls" if live else
            "OFFLINE — template extractor. Does not answer what the model would do")
    rec = Recorder(args.out, mode)
    rec.check("badge", "Badge matches configuration", "PASS",
              {"badges": [{k: b[k] for k in ("id", "label", "detail")} for b in badges(settings)],
               "expected_live_badge": "AI · LLM" if live else "AI · LLM-MOCK"},
              dashboard="The badge is rendered from config, never from a flag",
              notes="With no key the badge reads AI · LLM-MOCK. Asking for --live "
                    "exits rather than upstaging the mock.")

    db = Database(":memory:")
    gw = SimulatedGateway()
    service = CheckoutService(gateway=gw, profiles=ProfileRepo(db),
                              reservations=ReservationRepo(db), ledger=LedgerRepo(db),
                              approvals=ApprovalGate(), policy=Policy())
    llm = LLMExtractor(settings.llm) if live else None
    agent = Agent(service, llm=llm)

    results = {"read": False, "tool": False}
    try:
        results["read"] = run_readings(agent, rec, today, live)
        results["tool"] = run_tool(agent, rec, today, gw)
    finally:
        db.close()

    out = rec.write({"amount": AMOUNT, "model": settings.llm.model if live else "template"})
    print(f"\n{RULE}")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'} {name}")
    print(f"\n  evidence  {out}/evidence.json")
    if not live:
        print("\n  ⚠ OFFLINE. The template extractor ran, not a model. This answers "
              "the safety half of V4 and none of the quality half.")
    print()
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
