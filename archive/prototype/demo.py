#!/usr/bin/env python3
"""
demo.py — end-to-end walkthrough, no browser required.

This is the rehearsal script for the video. It runs the three personas through
the engine, prints the verdict and the reasoning, then performs the real PayPal
call for each.

    python3 demo.py            # simulated PayPal (no credentials needed)
    PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=... python3 demo.py --live
"""

import sys

from agent import TemplateExplainer, explain, money
from agentic import MockChat, Toolbox, extract, make_approval_token, run_agent
from engine import decide
from ledger import Ledger
from llm import describe, model_from_env
from paypal import client_from_env
from personas import DEFAULT_POLICY, PERSONAS, TODAY

RULE = "─" * 74


def run(persona_key: str, client, ledger: Ledger, live: bool) -> None:
    fn, label, amount = PERSONAS[persona_key]
    cal = fn()

    print(f"\n{RULE}\n{label}\n{RULE}")
    decision = decide(cal, amount, policy=DEFAULT_POLICY)
    expl = explain(decision, {"merchant": "Northwind Audio"}, explainer=TemplateExplainer())

    print(f"  purchase        {money(amount)}")
    print(f"  cushion         {money(decision.buffer)}")
    print(f"  mode            {client.mode.upper()}")
    print(f"\n  VERDICT         {decision.verdict}   ({decision.reason_code})")
    print(f"  {expl['headline']}")
    print(f"  {expl['why']}")
    print(f"  → {expl['alternative']}")

    print("\n  options considered:")
    for o in decision.options:
        mark = "ok  " if o.feasible else "fail"
        extra = ""
        if o.invoice_due:
            extra = f"  invoice due {o.invoice_due.isoformat()}"
        if o.overdraws:
            extra += "  [OVERDRAWS]"
        print(f"    {mark} {o.kind:17s} lowest {money(o.min_balance):>10s} "
              f"on {o.min_date.isoformat()}{extra}")

    if decision.collision:
        print(f"\n  collision       {decision.collision} on {decision.collision_date.isoformat()}")
        print(f"  shortfall       {money(decision.shortfall)}")
        print(f"  safe amount     {money(decision.safe_amount)}")

    # --- the PayPal side ---
    print()
    if decision.verdict == "OFFER":
        order = client.create_order(amount, intent="AUTHORIZE", reference="DEMO-OFFER")
        auth = client.authorize_order(order["id"])
        auth_id = auth["purchase_units"][0]["payments"]["authorizations"][0]["id"]
        print(f"  PayPal          order {order['id']} → authorized {auth_id}")
        print(f"                  capture within 3 days, or void")
        if not live:
            ledger.record(persona_key, amount, "USD", "pay_in_4", auth_id, today=cal.today)

    elif decision.verdict == "DEFER":
        due = decision.recommended.invoice_due
        inv = client.create_invoice(amount, due.isoformat(),
                                    note="Scheduled to your payday.")
        print(f"  PayPal          invoice {inv['id']}, due {due.isoformat()}")
        print(f"                  {inv.get('href', '')}")
        if not live:
            ledger.record(persona_key, amount, "USD", "invoice",
                          inv["id"], today=cal.today)

    else:
        print("  PayPal          no action taken — the shopper can still override")
        print(f"                  safe amount today: {money(decision.safe_amount)}")

    exp = ledger.exposure(persona_key, cal.today)
    print(f"  our ledger      {exp['plans_open']} live plan(s), "
          f"{money(exp['open_amount'])} outstanding")


def ai_section(client) -> None:
    """The part a judge must see: the model reads prose, the engine does the maths."""
    model = model_from_env()
    info = describe(model)
    print(f"\n{RULE}")
    print(f"AI IN ACTION — engine: {info['engine']} · model: {info['model']}")
    print(RULE)
    if info["engine"] == "llm-mock":
        print("  No LLM_API_KEY set. This is a scripted stand-in on the identical code")
        print("  path. Export LLM_API_KEY (and LLM_MODEL) to run a real model here.")

    text = ("rent 1450 on the 28th; car loan 312 on the 20th, "
            "mum's medicine about 40 bucks whenever")
    print(f'\n  shopper types: "{text}"\n')

    if info["engine"] == "llm-mock":
        model = MockChat([MockChat.extract_script([
            {"label": "rent", "amount_minor": 145_000, "due": "2026-11-28",
             "essential": True, "confidence": 0.97},
            {"label": "car loan", "amount_minor": 31_200, "due": "2026-11-20",
             "essential": True, "confidence": 0.95},
            {"label": "mum's medicine", "amount_minor": 4_000, "due": "2026-11-08",
             "essential": True, "confidence": 0.41},
        ])])
    result = extract(text, TODAY, model)
    print(f"  extracted by {result.engine}:")
    for o in result.obligations:
        print(f"    • {o.label:<20s} {money(o.amount_minor):>9s}  due {o.due}"
              f"  confidence {o.confidence:.0%}")
    for w in result.warnings:
        print(f"    ! {w}")
    if any(o.confidence < 0.6 for o in result.obligations):
        print("    ! low-confidence items are surfaced to the shopper, never silently trusted")

    # ---- the agentic moment: propose, then a human approves, then it happens ----
    print(f"\n  the agent, working:")
    goal = "Can I buy $249 in 4 this month?"
    script = [MockChat.decide_script(24_900),
              MockChat.invoice_script("2026-11-06", 24_900)]
    agent_model = MockChat(script) if info["engine"] == "llm-mock" else model
    box = Toolbox(client, lambda a: decide(PERSONAS["dev"][0](), a,
                                           policy=DEFAULT_POLICY).to_dict())
    run = run_agent(agent_model, box, goal)
    for i, step in enumerate(run.steps, 1):
        print(f"    {i}. {step['tool']:<26s} -> {step['status']}")

    if run.pending_approval:
        pa = run.pending_approval
        print(f"\n  STOPPED FOR APPROVAL — the agent may not move money alone")
        print(f"    proposed: {pa['tool']} {pa['args']}")
        print(f"    token is bound to those exact arguments")

        approved = make_approval_token(pa["tool"], pa["args"])
        print(f"\n  shopper taps Approve ...")
        box2 = Toolbox(client, lambda a: {})
        done = box2.call(pa["tool"], pa["args"], approved)
        print(f"    {pa['tool']} -> {done.status} {done.data}")

        print(f"\n  and a token for a different amount does not work:")
        wrong = box2.call(pa["tool"], {**pa["args"], "amount_minor": 999_900}, approved)
        print(f"    {pa['tool']} (9999.00) -> {wrong.status}")


def main() -> None:
    live = "--live" in sys.argv
    client = client_from_env(force_simulated=not live)
    ledger = Ledger(path=None if not live else Ledger().path)

    print(f"\nSecond Thought — end-to-end rehearsal")
    print(f"PayPal mode: {client.mode.upper()}"
          + ("   (no credentials found — everything below is simulated)" if not live else ""))
    print("The engine's verdicts are deterministic. The PayPal calls are real REST calls")
    print("when credentials are present, and labelled simulated otherwise.")

    for key in ("maya", "dev", "sam"):
        run(key, client, ledger, live)

    ai_section(client)

    print(f"\n{RULE}")
    print("Three shoppers, three different answers. That is the product:")
    print("the verdict depends on where the collision falls relative to payday.")
    print(RULE)


if __name__ == "__main__":
    main()
