#!/usr/bin/env python3
"""
demo.py — V3: the real PayPal sandbox, local, one call at a time.

    python3 demo.py --live                    # all five checks, in order
    python3 demo.py --live --only invoice     # one check
    python3 demo.py --dry-run                 # same code path, fake transport

Pass condition (V3): every artifact is visible in the *actual* PayPal sandbox
dashboard, not merely in this terminal. So each check prints the PayPal ID it
received and the place in the dashboard where a judge can find it, and writes
`artifacts/v3/<timestamp>/` with the raw responses attached.

Two of the checks need a human: Orders v2 will not authorise an order the buyer
has not approved, and there is no server-side way to approve one. The demo
prints the approval URL and polls until you click it. That is not a limitation
to be worked around — it is the payment flow.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from secondthought.config import load                                   # noqa: E402
from secondthought.domain import CashCalendar, Obligation, Payday, Policy  # noqa: E402
from secondthought.domain.engine import decide                          # noqa: E402
from secondthought.infra.evidence import Recorder                      # noqa: E402
from secondthought.infra.fake_paypal import FakePayPal                 # noqa: E402
from secondthought.infra.paypal_live import PayPalLiveGateway, money   # noqa: E402

RULE = "─" * 76
MERCHANT = "Northwind Audio"


# --------------------------------------------------------------------------
# payday math — the due date is computed, never hardcoded
# --------------------------------------------------------------------------
def payday_calendar(today: date) -> CashCalendar:
    """The 'ben' shape, anchored to a real payday after today.

    Opening balance covers a car payment but not the purchase, so the verdict
    must be DEFER — which is the only verdict that produces an invoice.
    """
    payday = today + timedelta(days=(4 - today.weekday()) % 7 or 7)   # next Friday
    return CashCalendar(
        today=today,
        opening_balance=30_000,
        paydays=[Payday(due=payday, amount=260_000)],
        obligations=[
            Obligation(label="car loan", due=payday + timedelta(days=13), amount=31_200),
            Obligation(label="rent", due=payday + timedelta(days=21), amount=145_000),
        ],
    )


def invoice_due_date(today: date, amount_minor: int) -> tuple[date, dict]:
    """Run the real engine; refuse to invent a date it did not choose."""
    cal = payday_calendar(today)
    d = decide(cal, amount_minor, "USD", Policy())
    rec = d.recommended
    if d.verdict != "DEFER" or rec is None or rec.invoice_due is None:
        raise SystemExit(
            f"At {money(amount_minor)} this shopper gets {d.verdict}, not DEFER — so "
            f"there is no invoice to date.\n"
            f"That is the product answering correctly, not the tool failing. The "
            f"invoice check needs a purchase the shopper cannot pay for today; "
            f"use the default --amount 249.00.")
    return rec.invoice_due, {
        "verdict": d.verdict,
        "recommended_instrument": rec.kind,
        "due_date": rec.invoice_due.isoformat(),
        "next_payday": (cal.paydays[0].due.isoformat()),
        "days_out": (rec.invoice_due - today).days,
        "collision": d.collision,
        "reason_code": d.reason_code,
    }


# --------------------------------------------------------------------------
# the five checks
# --------------------------------------------------------------------------
def step_oauth(gw, rec, args) -> bool:
    data = gw.http.token(force=True)
    token = data.get("access_token", "")
    print(f"  token      {token[:16]}…{token[-6:]}   (full token not written to disk)")
    print(f"  expires in {data.get('expires_in')}s → "
          f"{date.fromtimestamp(__import__('time').time() + int(data.get('expires_in', 0)))}")
    print(f"  app_id     {data.get('app_id', '—')}")
    rec.check("oauth", "OAuth token issued", "PASS", {
        "token_prefix": token[:16], "token_length": len(token),
        "expires_in_seconds": data.get("expires_in"),
        "app_id": data.get("app_id"), "scope": data.get("scope"),
        "fetched_at": data.get("fetched_at", ""),
    }, notes="Full token printed above but deliberately not persisted: a 9-hour "
             "sandbox token in a git-committed transcript is a habit worth not forming.")
    return bool(token)


def _order_id_from_log(gw) -> str:
    for entry in reversed(gw.log):
        if entry["step"] == "create_order":
            return (entry["received"] or {}).get("id", "")
    return ""


def step_authorize(gw, rec, args, *, do_capture: bool = True) -> tuple[bool, str, str]:
    auth = gw.authorise(amount_minor=args.amount_minor, currency=args.currency,
                        reference=args.reference)
    order_id = _order_id_from_log(gw)
    print(f"  order      {order_id}  (approved)")
    print(f"  authorise  {auth.id}  status={auth.status}  expires {auth.expires_on}")
    evidence = {"order_id": order_id, "authorisation_id": auth.id,
                "authorisation_status": auth.status,
                "expires_on": auth.expires_on, "amount": money(args.amount_minor)}
    ok = bool(order_id and auth.id)
    if do_capture:
        cap = gw.capture_authorisation(auth.id)
        print(f"  capture    {cap.id}  status={cap.status}  {money(cap.amount_minor)}")
        evidence.update({"capture_id": cap.id, "capture_status": cap.status})
        ok = ok and cap.status == "COMPLETED"
    rec.last_auth = evidence
    return ok, order_id, auth.id


def step_capture(gw, rec, args) -> bool:
    ok, order_id, auth_id = step_authorize(gw, rec, args, do_capture=True)
    cap = rec.last_auth
    ok = ok and cap.get("capture_status") == "COMPLETED"
    rec.check("order", "Order AUTHORIZE → capture (orders v2)", "PASS" if ok else "FAIL",
              {"order_id": order_id, "authorisation_id": auth_id,
               "authorisation_status": cap.get("authorisation_status"),
               "capture_id": cap.get("capture_id"),
               "capture_status": cap.get("capture_status", "")})
    return ok


def step_void(gw, rec, args) -> bool:
    auth = gw.authorise(amount_minor=args.amount_minor, currency=args.currency,
                        reference=args.reference + "-void")
    order_id = _order_id_from_log(gw)
    print(f"  authorise  {auth.id}  status={auth.status}")
    gw.void_authorisation(auth.id)
    voided = gw.log[-1]
    print(f"  void       HTTP {voided['status']} → {voided['received'].get('status', 'VOIDED')}")
    ok = bool(order_id and voided["status"] in (200, 201, 204))
    rec.check("void", "Order AUTHORIZE → void", "PASS" if ok else "FAIL",
              {"order_id": order_id, "authorisation_id": auth.id,
               "void_http_status": voided["status"],
               "void_status": voided["received"].get("status", "VOIDED (204, no body)")})
    return ok


def step_invoice(gw, rec, args) -> bool:
    due, math_row = invoice_due_date(date.today(), args.amount_minor)
    print(f"  payday math  verdict={math_row['verdict']} → due {due} "
          f"({math_row['days_out']}d, next payday {math_row['next_payday']})")
    inv = gw.create_invoice(amount_minor=args.amount_minor, currency=args.currency,
                            due_date=due, reference=args.reference + "-inv")
    print(f"  invoice      {inv.id}  status={inv.status}  due {inv.due_date}")
    matched = inv.due_date == due
    print(f"  due date matches payday math: {'YES' if matched else 'NO'}")
    if args.buyer_email:
        gw.send_invoice(inv.id)
        print(f"  sent to      {args.buyer_email}  → status {gw.get_invoice(inv.id).status}")
    ok = matched and bool(inv.id)
    rec.check("invoice", "Invoice created with payment_term.due_date",
              "PASS" if ok else "FAIL",
              {"invoice_id": inv.id, "status": inv.status,
               "due_date": inv.due_date, "amount": money(inv.amount_minor),
               "due_date_matches_payday_math": matched, "payday_math": math_row,
               "recipient_view_url": inv.pay_url})
    return ok


def step_idempotency(gw, rec, args) -> bool:
    rid = f"st-idem-{args.reference}"
    first = gw.create_order(amount_minor=args.amount_minor, currency=args.currency,
                            reference=args.reference, request_id=rid)
    second = gw.create_order(amount_minor=args.amount_minor, currency=args.currency,
                             reference=args.reference, request_id=rid)
    third = gw.create_order(amount_minor=args.amount_minor, currency=args.currency,
                            reference=args.reference, request_id=rid + "-different")
    same = first["id"] == second["id"]
    differs = third["id"] != first["id"]
    print(f"  request id     {rid}")
    print(f"  POST #1        {first['id']}")
    print(f"  POST #2 (same) {second['id']}   → same order: {'YES' if same else 'NO'}")
    print(f"  POST #3 (new)  {third['id']}   → distinct:   {'YES' if differs else 'NO'}")
    ok = same and differs
    rec.check("idempotency", "Same PayPal-Request-Id → one order", "PASS" if ok else "FAIL",
              {"paypal_request_id": rid, "first_order_id": first["id"],
               "second_order_id": second["id"], "control_order_id": third["id"],
               "same_request_same_order": same, "different_request_new_order": differs})
    return ok


# --------------------------------------------------------------------------
STEPS = {"oauth": step_oauth, "capture": step_capture, "void": step_void,
         "invoice": step_invoice, "idempotency": step_idempotency}
ORDER = ["oauth", "idempotency", "capture", "void", "invoice"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="V3 — live PayPal sandbox checks")
    ap.add_argument("--live", action="store_true", help="talk to the real sandbox")
    ap.add_argument("--dry-run", action="store_true", help="fake transport, no network")
    ap.add_argument("--only", default="all", choices=["all", *STEPS])
    ap.add_argument("--amount", default="249.00")
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--buyer-email", default="", help="also send the invoice to this address")
    ap.add_argument("--reference", default="northwind-bt-001")
    ap.add_argument("--wait", type=int, default=300, help="seconds to wait for buyer approval")
    ap.add_argument("--out", default="artifacts/v3")
    args = ap.parse_args(argv)

    args.amount_minor = int(round(float(args.amount) * 100))
    settings = load().paypal

    live = args.live and not args.dry_run
    if not (args.live or args.dry_run):
        print("Choose --live (real sandbox) or --dry-run (fake transport).", file=sys.stderr)
        return 2

    print(f"\n{RULE}\nSecond Thought — V3 {'LIVE SANDBOX' if live else 'DRY RUN'}\n{RULE}")
    print(f"  client id    {'present' if settings.client_id else 'MISSING'}")
    print(f"  secret       {'present' if settings.client_secret else 'MISSING'}")
    print(f"  webhook id   {'present' if settings.webhook_id else 'absent (not used by V3)'}")
    print(f"  paypal env   {settings.env}   base {settings.base_url}")

    if live and not settings.configured:
        print("\nPAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set. V0.1 is red — "
              "V3 cannot run.", file=sys.stderr)
        return 2

    mode = ("LIVE SANDBOX — every ID below must also be findable in the PayPal dashboard"
            if live else
            "DRY RUN — fake transport. Proves the wiring, proves NOTHING about your account")
    rec = Recorder(args.out, mode)
    transport = None if live else FakePayPal()

    def on_approval(url: str) -> None:
        print(f"\n  ⟶ APPROVE THIS ORDER IN A BROWSER, as the sandbox personal buyer:\n"
              f"    {url}\n    (waiting up to {args.wait}s)")

    gw = PayPalLiveGateway(settings, transport=transport, on_approval=on_approval,
                           approve_timeout=args.wait, poll_every=2 if not live else 5)

    wanted = ORDER if args.only == "all" else [args.only]
    results: dict[str, bool] = {}
    for name in wanted:
        print(f"\n{RULE}\n{name.upper()}\n{RULE}")
        try:
            results[name] = bool(STEPS[name](gw, rec, args))
        except SystemExit:
            raise
        except Exception as exc:                      # noqa: BLE001 — every failure is evidence
            print(f"  ✗ {type(exc).__name__}: {exc}")
            rec.check(name, name, "FAIL", {"error": f"{type(exc).__name__}: {exc}"})
            results[name] = False

    out = rec.write({"amount": money(args.amount_minor), "currency": args.currency,
                     "checks_run": wanted, "gateway_calls": len(gw.log)})
    (out / "calls.json").write_text(json.dumps(gw.log, indent=2, default=str))

    print(f"\n{RULE}")
    for name in wanted:
        print(f"  {'✓' if results[name] else '✗'} {name}")
    print(f"\n  evidence  {out}/evidence.json")
    print(f"  calls     {out}/calls.json")
    if not live:
        print("\n  ⚠ DRY RUN. Nothing was sent to PayPal. Do not cite this as V3 evidence.")
    else:
        print("\n  Now open the dashboard and confirm each ID above is there. "
              "Terminal output is a claim; the dashboard is the proof.")
    print()
    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
