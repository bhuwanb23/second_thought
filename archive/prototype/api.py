"""
api.py — the JSON API, independent of transport.

Every money-moving action is two steps: the engine or the agent proposes, a
human approves, and only then does the PayPal call happen. The approval token is
bound to the exact tool and the exact arguments, so nothing can be swapped
between approval and execution.

server.py owns only HTTP: routing, cookies and rate limits.
"""

from __future__ import annotations

import json

import paylater
from agent import TemplateExplainer, explain, money
from agentic import Toolbox, extract, make_approval_token, run_agent
from engine import HORIZON_DAYS, CashCalendar, Obligation, Payday, decide, simulate
from ledger import Ledger
from llm import MockChat, describe, model_from_env
from paypal import PayPalError, client_from_env
from personas import DEFAULT_POLICY, PERSONAS, TODAY
from profile import ProfileStore, answer_quality, from_extraction
from session import Session, SessionStore
from datetime import date

CLIENT = client_from_env()
SESSIONS = SessionStore()
DEFAULT = Session("_default")   # direct build_payload() calls (tests, demo.py)

LEDGER = DEFAULT.ledger
EXPLAINER = TemplateExplainer()
ELIGIBILITY = DEFAULT.eligibility
PROFILES = DEFAULT.profiles
MODEL = model_from_env()


# --------------------------------------------------------------------------
# payload
# --------------------------------------------------------------------------
def _persona(key: str):
    fn, label, amount = PERSONAS.get(key, PERSONAS["maya"])
    return (key if key in PERSONAS else "maya"), fn(), label, amount


def build_payload(persona_key: str, amount_minor: int | None = None,
                  calendar: CashCalendar | None = None,
                  session: Session | None = None) -> dict:
    """
    Personas are READ-ONLY. Anything a visitor saves lives in their own session,
    so one visitor can never change the verdict the next visitor sees.
    """
    sess = session or DEFAULT
    key, cal, label, default_amount = _persona(persona_key)
    profile = sess.profiles.get(key)
    if profile and calendar is None:
        cal = profile.to_calendar(cal.today)   # set up once, applied silently at checkout
    if calendar is not None:
        cal = calendar
    amount = amount_minor or default_amount

    decision = decide(cal, amount, policy=DEFAULT_POLICY)
    expl = explain(decision, {"merchant": "Northwind Audio"}, explainer=EXPLAINER)
    elig = sess.eligibility.get(key)
    instrument = paylater.choose_instrument(decision.verdict, elig)

    focus = decision.recommended or next(
        (o for o in decision.options if o.kind == "PAY_IN_4"), None)
    extra = [(d, -a, "x") for d, a in (focus.debits if focus else [])]
    _mn, _mdt, curve = simulate(cal, extra)

    events = [{"date": d.isoformat(), "amount": amt, "label": lab, "kind": kind}
              for d, amt, lab, kind in cal.events()]

    return {
        "persona": key,
        "persona_label": label,
        "today": cal.today.isoformat(),
        "amount": amount,
        "amount_display": money(amount),
        "mode": CLIENT.mode,
        "ai": describe(MODEL),
        "decision": decision.to_dict(),
        "explanation": expl,
        "buffer": decision.buffer,
        "buffer_display": money(decision.buffer),
        "curve": [{"date": d.isoformat(), "balance": b} for d, b in curve],
        "events": events,
        "focus": focus.kind if focus else None,
        "focus_debits": [{"date": d.isoformat(), "amount": a}
                         for d, a in (focus.debits if focus else [])],
        "ledger": sess.ledger.exposure(key, cal.today),
        "horizon_days": HORIZON_DAYS,
        "instrument": instrument,
        "instrument_doc": paylater.describe_instrument(instrument),
        "fulfilment": paylater.describe_instrument(instrument)["fulfilment"],
        "risk_bearer": paylater.describe_instrument(instrument)["risk_bearer"],
        "profile": profile.summary() if profile else None,
        "answer_quality": answer_quality(profile),
        "eligibility": elig.to_dict() if elig else None,
        "requires_approval": instrument in (paylater.INSTRUMENT_AUTHORIZE,
                                            paylater.INSTRUMENT_INVOICE),
    }


# --------------------------------------------------------------------------
# approval + execution
# --------------------------------------------------------------------------
def _money_action(payload: dict) -> tuple[str, dict] | None:
    """The (tool, args) pair a given payload implies. This is what gets approved."""
    inst = payload["instrument"]
    amount = payload["decision"]["amount"]
    if inst == paylater.INSTRUMENT_INVOICE:
        inv = next((o for o in payload["decision"]["options"]
                    if o["kind"] == "DEFER_TO_PAYDAY"), None)
        due = (inv or {}).get("invoice_due") or payload["today"]
        return "create_scheduled_invoice", {"amount_minor": amount, "due_date": due}
    if inst == paylater.INSTRUMENT_AUTHORIZE:
        return "authorize_payment", {"amount_minor": amount}
    return None


def approve(payload: dict) -> dict:
    """Issue the token a human approval grants. Bound to tool + exact arguments."""
    action = _money_action(payload)
    if not action:
        return {"ok": False, "message": "nothing to approve for this instrument"}
    tool, args = action
    return {"ok": True, "tool": tool, "args": args,
            "token": make_approval_token(tool, args),
            "granted_by": "shopper (demonstration approval)",
            "message": f"Approved: {tool} {json.dumps(args)} — now execute it."}


def execute(payload: dict, approval_token: str | None = None,
            session: Session | None = None) -> dict:
    inst = payload["instrument"]
    amount = payload["decision"]["amount"]
    cur = payload["decision"]["currency"]
    action = _money_action(payload)

    led = (session or DEFAULT).ledger
    try:
        # --- Pay Later: an order the storefront hands to the SDK button ---
        if inst == paylater.INSTRUMENT_PAYLATER:
            order = CLIENT.create_order(amount, cur, intent="CAPTURE",
                                        reference="SECONDTHOUGHT-PAYLATER")
            return {"ok": True, "action": "order_created_for_paylater",
                    "instrument": inst,
                    "paypal": {"order": order},
                    "message": ("Order created. The storefront passes this id to "
                                "<paypal-paylater-button> with the productCode from "
                                "findEligibleMethods().")}

        # --- authorisation hold: money action, needs approval ---
        if inst == paylater.INSTRUMENT_AUTHORIZE:
            tool, args = action
            box = Toolbox(CLIENT, lambda a: payload["decision"])
            res = box.call(tool, args, approval_token)
            if res.status == "approval_required":
                return {"ok": False, "action": "approval_required",
                        "instrument": inst, "proposal": args,
                        "token": res.data["required_token"],
                        "message": "A human must approve before money is held."}
            if res.status != "executed":
                return {"ok": False, "action": "error", "error": res.data}
            led.record(payload["persona"], amount, cur, "pay_in_4",
                       res.data.get("authorization_id", ""),
                          today=date.fromisoformat(payload["today"]))
            return {"ok": True, "action": "authorized", "instrument": inst,
                    "paypal": res.data,
                    "message": f"{money(amount)} authorised on sandbox. Capture on your schedule."}

        # --- scheduled invoice: money action, needs approval ---
        if inst == paylater.INSTRUMENT_INVOICE:
            tool, args = action
            box = Toolbox(CLIENT, lambda a: payload["decision"])
            res = box.call(tool, args, approval_token)
            if res.status == "approval_required":
                return {"ok": False, "action": "approval_required",
                        "instrument": inst, "proposal": args,
                        "token": res.data["required_token"],
                        "message": "A human must approve before an invoice is issued."}
            if res.status != "executed":
                return {"ok": False, "action": "error", "error": res.data}
            led.record(payload["persona"], amount, cur, "invoice",
                       res.data.get("invoice_id", ""),
                          today=date.fromisoformat(payload["today"]))
            return {"ok": True, "action": "invoice_created", "instrument": inst,
                    "paypal": res.data,
                    "message": f"Invoice created, due {args['due_date']}."}

        return {"ok": False, "action": "none", "instrument": inst,
                "message": "No PayPal action taken — the shopper can still override."}

    except PayPalError as e:
        return {"ok": False, "action": "error", "error": str(e)}


# --------------------------------------------------------------------------
# AI endpoints
# --------------------------------------------------------------------------
def do_extract(text: str, persona_key: str, session: Session | None = None) -> dict:
    """Turn the shopper's own words into a calendar the engine can use."""
    key, cal, _label, _amount = _persona(persona_key)
    result = extract(text, cal.today, MODEL)

    if result.obligations:
        obligations = [Obligation(o.label, o.due or cal.today, o.amount_minor,
                                  o.essential) for o in result.obligations]
        cal = CashCalendar(today=cal.today, opening_balance=cal.opening_balance,
                           paydays=cal.paydays, obligations=obligations,
                           instalments=cal.instalments)
    return {"extraction": result.to_dict(), "ai": describe(MODEL),
            "calendar": {"opening_balance": cal.opening_balance,
                         "events": [{"date": d.isoformat(), "amount": amt,
                                     "label": lab, "kind": kind}
                                    for d, amt, lab, kind in cal.events()]}}


def do_agent(persona_key: str, amount_minor: int | None = None,
             session: Session | None = None) -> dict:
    """Run the tool-calling loop so the trace can be shown on screen."""
    key, cal, _label, default_amount = _persona(persona_key)
    amount = amount_minor or default_amount
    decision = decide(cal, amount, policy=DEFAULT_POLICY)

    model = MODEL
    if isinstance(model, MockChat):
        from agentic import make_approval_token as _mk
        due = decision.collision_date or cal.today
        model = MockChat([
            MockChat.decide_script(amount),
            MockChat.invoice_script(due.isoformat(), amount),
        ])

    box = Toolbox(CLIENT, lambda a: decide(cal, a, policy=DEFAULT_POLICY).to_dict())
    run = run_agent(model, box, f"Can I buy {money(amount)} in 4 this month?")
    out = run.to_dict()
    out["ai"] = describe(MODEL)
    out["decision"] = decision.to_dict()
    return out


# --------------------------------------------------------------------------
# HTTP