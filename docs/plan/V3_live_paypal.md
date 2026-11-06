# V3 — Live PayPal, local

**Status:** 🔴 **CANNOT RUN — BLOCKED at V0.1. Instrument built and verified offline.**
**Pass criterion:** every artifact below is **visible in the actual PayPal sandbox dashboard**, not just in the terminal. A judge could log in and find them.

---

## 1. Why this is not green, stated plainly

V3 begins with `export PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=...`. I do not have them, and I am not going to fake output that looks like a live run — a plausible-looking transcript is worth less than no transcript, because it would go into the submission as evidence.

`python3 scripts/v0_check.py` is **4 FAILED, exit 1**. V0 is the gate that says *stop* when a row fails. So V3's status is **blocked**, and everything below is the instrument waiting for the key, plus an honest statement of what has and has not been proven.

```
python3 demo.py --live
→ client id    MISSING
→ secret       MISSING
→ PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are not set. V0.1 is red — V3 cannot run.
→ exit 2
```

---

## 2. The five rows V3 asks for

| # | Call | Evidence to capture | Where a judge finds it | Status |
|---|---|---|---|---|
| 1 | **OAuth token** | Token printed/logged, expiry visible | Developer dashboard → Apps & Credentials → Sandbox → the app whose client ID issued it | ⬜ PENDING |
| 2 | **Order AUTHORIZE → capture** | Order ID in the sandbox dashboard → Activity | `sandbox.paypal.com/activities` as the **business** account, filtered to today | ⬜ PENDING |
| 3 | **Order AUTHORIZE → void** | Status changes to **VOIDED** in the dashboard | Same Activity row; also `GET /v2/payments/authorizations/{id}` | ⬜ PENDING |
| 4 | **Invoice with `payment_term.due_date`** | `INV2-…` ID, due date matches payday math, visible in Invoicing | `sandbox.paypal.com/invoice/manage/invoices` as the business account | ⬜ PENDING |
| 5 | **Idempotency** | Same `PayPal-Request-Id` twice → only one order exists | Activity shows one order, not two | ⬜ PENDING |

**Rule for filling this in: the row goes green when the screenshot exists, not when the terminal prints OK.** A terminal line proves a request was sent; only the dashboard proves PayPal accepted it.

---

## 3. The instrument

| File | Lines | What it is |
|---|---|---|
| `product/demo.py` | 284 | The five checks, in order, with `--only` to run one. Prints each PayPal ID and writes `artifacts/v3/<timestamp>/` |
| `product/secondthought/infra/paypal_live.py` | 290 | `PayPalLiveGateway` — orders v2 authorize/capture/void + Invoicing v2, behind **the same `PaymentGateway` protocol** as `SimulatedGateway` |
| `product/secondthought/infra/fake_paypal.py` | 165 | A transport that answers like the sandbox. Used by `--dry-run` and by the tests. **Never reachable from `--live`** |
| `product/secondthought/infra/evidence.py` | 92 | Writes `evidence.json` + `TRANSCRIPT.md`: ID, dashboard location, raw request/response |
| `product/tests/test_paypal_live.py` | 219 | **21 tests.** Request bodies, headers, 204 handling, idempotency, live-env refusal, protocol parity |

### Run it

```bash
cd product
export PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=... PAYPAL_WEBHOOK_ID=...
python3 demo.py --dry-run     # proves the wiring — proves nothing about your account
python3 demo.py --live        # the real thing; asks you to approve two orders in a browser
python3 demo.py --live --only invoice --buyer-email you@example.com
```

`--dry-run` and `--live` run **the same code path**; only the transport differs. That is the point: if the dry run passes and the live run fails, the fault is in the account or the credentials, not in the wiring.

### Why two of the checks need you in a browser

Orders v2 will not authorise an order the buyer has not approved, and there is no server-side endpoint to approve one. So `demo.py` prints the `payer-action` URL and polls `GET /v2/checkout/orders/{id}` until the status reads `APPROVED` (default 300 s, `--wait` to change). Sign in as the **sandbox personal** buyer.

This is the same honest limit V1 hit: the buyer is a human, and the tool must not pretend otherwise. Two approvals are needed — one for the capture row, one for the void row. The idempotency check needs none: creating an order does not require approval.

---

## 4. What is already proven, offline

```
python3 -m unittest discover -s tests  →  Ran 51 tests ... OK   (30 → 51; +21 new)
python3 demo.py --dry-run → 5/5 checks pass on the fake transport
```

Specifically asserted, not assumed:

- OAuth sends `Basic base64(client_id:client_secret)` with `grant_type=client_credentials`, and **caches** the token — a second call does not refetch, and the reuse window is deliberately shortened by 60 s so a slow call never carries a dying token.
- Order creation sends `intent: AUTHORIZE`, `amount.value: "249.00"` (integer minor units → string, never floating point), and the `PayPal-Request-Id` header.
- The authorisation ID is read from `purchase_units[0].payments.authorizations[0].id` — the nesting that catches people out.
- Capture sends `{"final_capture": true}` with `Prefer: return=representation`, and parses `"249.00"` back to `24900`.
- **Void accepts a bare 204** (v2 returns no body by default) and rejects anything that does not report VOIDED.
- The invoice body carries `detail.payment_term.term_type = DUE_ON_DATE_SPECIFIED` and `detail.payment_term.due_date`.
- The invoice ID is parsed from an **`href`**, because Invoicing v2 returns a link rather than an `id` on create.
- Same `PayPal-Request-Id` → same order; different ID → different order. Both directions, because one direction alone proves nothing.
- `PAYPAL_ENV=live` raises before the first request. A mis-set variable stops the process instead of spending money.
- `PayPalLiveGateway` satisfies every attribute of the `PaymentGateway` protocol, same as `SimulatedGateway`.

**The due date is computed, not typed.** `demo.py` builds the calendar from today, runs the real engine, and requires the verdict to be `DEFER` before it will date an invoice:

```
payday math  verdict=DEFER → due 2026-11-06 (4d, next payday 2026-11-06)
invoice      INV2-…  status=DRAFT  due 2026-11-06
due date matches payday math: YES
```

Two tests police this: `test_the_invoice_due_date_is_the_payday_the_engine_chose`, and `test_it_moves_when_today_moves_so_it_is_not_hardcoded` — the same call a week later must produce a different date. If someone ever pastes a constant in, the second test fails.

A side effect worth knowing: `--amount 89.50` **refuses to produce an invoice**, because at that price the shopper gets `OFFER` and there is nothing to defer. The tool says so instead of inventing a due date.

---

## 5. What is still unproven — and only the live run answers it

These are the ways V3 can still fail with the instrument working perfectly. Each has a fix, so none is a cliff:

| Unknown | Why it might bite | If it does |
|---|---|---|
| The sandbox **business** account's payment capabilities | Some fresh sandbox business accounts have Invoicing or card/bank funding disabled | Enable in the sandbox business profile; the error surfaces as a 4xx with a named issue in `calls.json` |
| Whether the **personal** buyer can approve an AUTHORIZE order | Buyer country/currency mismatch — the same trap V1 documents | Change the buyer's country in the sandbox dashboard; `--currency` is a flag |
| **Invoicing** write scope on the app | The sandbox app needs the Invoicing feature enabled | Toggle it on the app's features page; re-run `--only invoice` |
| Authorization **expiry** | v2 authorisations last ~3 days; a void run days later fails | Expected, and correct. Re-authorise |
| Approval URL rel name | PayPal has used both `payer-action` and `approve` | Handled: `_approval_url()` accepts either. If a third name appears, the printed order JSON in `calls.json` shows it |

---

## 6. What goes green in the plan when this passes

| Row | Unblocks |
|---|---|
| 1 (OAuth) | V0.2 — the gate's own OAuth row |
| 2 (capture) | P3 live payments; the OFFER path in the demo video |
| 3 (void) | The claim that we *release* a hold rather than leave it — the honest half of "no merchant credit" |
| 4 (invoice) | **The hero.** DEFER → a real `INV2-…` dated to the payday. Without this there is no submission |
| 5 (idempotency) | P5.6 webhook retries; the safety claim in the README |

---

## 7. The moment the key arrives

```bash
cd product
export PAYPAL_CLIENT_ID=… PAYPAL_CLIENT_SECRET=… PAYPAL_WEBHOOK_ID=…
python3 scripts/v0_check.py            # must be 0 FAILED before anything else
python3 demo.py --live                # approve both orders when prompted
python3 demo.py --live --only invoice --buyer-email <sandbox buyer email>
```

Then fill §2 from the dashboard, attach the screenshots, and change the status line at the top of this file from 🔴 to 🟢 — or to 🟠 with the exact failing row, which is more useful than a green lie.
