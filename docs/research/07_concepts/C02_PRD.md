# Second Thought — product spec

> **The checkout that tells you the truth about your next four weeks.**

**Name:** Second Thought · **Working subtitle:** payday-aware checkout
**Alt names:** Payday Gate, Collide, The Fifth
**Concept ID:** C02 · **EV #2 (64.5)** · intent fit 5/5 · 3 competitors in field · validated GO (`C02_VALIDATION_REPORT.md`)

---

## 1. The idea

Every BNPL tool in the world is built to increase take-up of instalments. **This one decides whether an instalment is good for the person standing at the checkout — and is willing to say no.**

Concretely: at the moment Pay Later would be offered, Second Thought projects the shopper's actual cash position across the next 45 days — their paydays, their rent, their existing instalments *with this merchant*, the obligations they've declared — and returns one of three verdicts:

| | |
|---|---|
| **OFFER** | It fits. Show Pay Later. |
| **DEFER** | It fits, but not today. **Pay before ship:** reserve the item and the price, invoice dated to payday, merchant ships only after payment clears. No merchant credit. |
| **DECLINE** | It would collide with something essential. Don't surface the instalment option. Explain exactly which bill, on which date, and how much room there actually is. |

The shopper can override any verdict with one click. That is the difference between a gate and a guardrail, and it must be visible in the demo.

### Why this wins the judging criteria

| Criterion | The answer |
|---|---|
| Technological Implementation | JS SDK v6 `findEligibleMethods` (1% field usage) + Orders v2 AUTHORIZE (9%) + Invoicing with due dates (0.5%) + signature-verified webhooks + Transaction Search + a deterministic engine with a real test suite |
| Design | A calendar, a balance curve, and a verdict. Not a chat window. |
| Potential Impact | 47% of BNPL users paid late; 63% stack loans; 11% hit overdraft. Two named audiences with sourced pain. |
| Innovation | The tool that talks you *out* of the sale. 2 of 549 repos mention BNPL at all. |
| Presentation | Two memorable moments: the refusal, and the invoice that saves the sale. |

---

## 2. Who it's for, and who pays

> **Resolved after review.** The earlier framing was merchant-side, which was wrong: under Pay
> Later, PayPal pays the merchant upfront and carries the credit risk, so a merchant gains little
> from reducing BNPL use. The customer is PayPal; the shopper is the beneficiary; the merchant is
> distribution. Full argument in `C02_THE_IDEA.md` §3.

| Party | Role | Pays? |
|---|---|---|
| **Shopper** | User and beneficiary. Owns the data. Can override everything. | No |
| **PayPal** | **The customer.** Holds the credit risk, the dispute exposure and the regulatory attention | **Yes** |
| **Merchant** | Distribution at checkout; pays only where late-payment and chargeback costs justify it | Sometimes |

**Primary — the shopper.** Someone paid twice a month with more BNPL plans than they can hold in their head. They are not financially reckless; they are badly served by a checkout that shows four instalments of $62 without telling them it lands three days before rent.

**Secondary — the merchant.** A mid-size DTC store where BNPL is 20–35% of revenue, and where the same repeat customers come back three times in a month. The merchant does not want the chargeback, the dispute, or the customer who gets silently blacklisted by PayPal and never returns. They want the sale *and* the customer.

**The merchant's actual incentive, stated honestly:** a decline costs them one sale. A late-fee cascade costs them a repeat customer worth many sales, plus a dispute. Second Thought is configured to be conservative only where the merchant chooses.

---

## 3. The mechanic

### Verdict rules (all deterministic)

Given a purchase of `A` minor units, a cash calendar `C` over the next 45 days, and a safety buffer `B`:

1. Build `C`: every payday (income), every declared essential obligation, every live instalment from our ledger.
2. Simulate the **baseline** balance day by day. Record the trough.
3. Simulate each candidate:
   - **PAY_NOW** — `A` debited today
   - **PAY_IN_4** — `⌈A/4⌉` at today, +14, +28, +42 (largest-remainder split, exact to the cent)
   - **DEFER_TO_PAYDAY** — nothing today; invoice due on the next payday
   - **PARTIAL_NOW** — the largest amount that keeps the buffer intact today, remainder invoiced
4. For each, compute the **minimum balance across all outflow dates**.
5. Recommend by policy: prefer the option with the highest minimum margin; require `min_balance ≥ B`.
6. If nothing satisfies `B` → **DECLINE**, and emit `safe_amount` = the largest `A` that would have passed.

### Buffer

`B = round(monthly_income × buffer_pct)`, default `buffer_pct = 0.10`, merchant-configurable. Never below one week's essentials.

### What makes it a product, not a calculator

The engine also emits **the collision**: the specific pair of dated amounts that break the plan, phrased as a sentence.

> "Paying $249 in 4 puts instalment 3 of $62.25 on 2 December. Rent of $1,450 is due 1 December. Your balance on 2 December would be −$83.40."

That sentence is the demo.

---

## 4. What we can and cannot see — the honesty contract

This is load-bearing. State it in the README, in the UI, and out loud in the video.

| Source | What it gives us | Status |
|---|---|---|
| **Our plan ledger** | Every Pay Later order we originated for this shopper, with their computed instalment schedule | Real, ours |
| **Shopper declarations** | Rent, other BNPL, childcare, whatever they enter on a one-screen consent form | Real, consented |
| **Transaction Search** (`/v1/reporting/transactions`) | Repeat purchase cadence against *this merchant* | Real, merchant-scoped |
| **PayPal's own BNPL plan data** | **Nothing. No API exposes a consumer's plans.** | **Cannot see — say so** |
| **Bank balances / open banking** | Nothing | Out of scope |

**The claim we make:** *"We know every instalment we created for this shopper, and they can add the ones we can't see. That's enough to catch the collision that actually happens — the same shopper buying three times at the same store in one month, which is where the late fees come from."*

**The claim we never make:** that we see someone's full financial life.

---

## 5. Deterministic engine

`../../../09_build/prototype/engine.py` — implemented, tested.

- **All money is integer minor units.** No floats anywhere. `$249.00` is `24900`.
- **Instalment split is exact.** Largest-remainder distribution so `sum(instalments) == amount` to the cent. (Tested: `10000/3`, `9999/4`.)
- **Dates are naive ISO dates** in the merchant's timezone, documented explicitly. No timezone arithmetic in the engine; the caller supplies `today`.
- **No randomness, no model.** Same inputs → byte-identical output. Tested.
- **Overridable.** Every verdict carries `overridable: true` and the shopper's override is recorded in the ledger with a reason — which is also a useful analytics artefact for the merchant.

### Red-team cases (all implemented as tests)

| Case | Expected |
|---|---|
| Zero / negative amount | `reject` — invalid input, not a verdict |
| Instalment lands before a payday but after rent | `DECLINE`, collision names rent |
| Payday on the 31st in a 30-day month | Next payday rolls to the last day of month |
| Instalment split not summing to the amount | `AssertionError` — exact split enforced |
| Buffer floor breached by 1 cent | `DECLINE`, not `DEFER` |
| Same-day instalment from an existing plan | Collision detected |
| Same input twice | Identical output |
| Merchant sets `buffer_pct = 0` | Still enforces one week of essentials — policy floor |

---

## 6. The agent boundary

**The model never decides anything about money.** This is the rule every strong entry in the field scan follows, and it is the one a PayPal judge will probe.

| Layer | Decides | Cannot |
|---|---|---|
| **Deterministic engine** | Every verdict, every amount, every date, every collision | Be overridden by the model |
| **Agent (LLM)** | How to *say* it — the sentence, the tone, the alternative framing | Change a verdict, an amount, or a date |

Implementation (`../../../09_build/prototype/agent.py`):
1. Engine returns structured findings.
2. Agent receives findings + a strict JSON schema for its output.
3. Output is validated. **Any** failure — malformed JSON, missing field, unknown verdict, a number that disagrees with the engine — falls back to a deterministic template.
4. The engine's verdict is re-read after generation and asserted unchanged. If it somehow changed, the response is discarded.

The LLM earns its place on exactly one input: **free-text obligations**. A shopper typing "rent 1450 on the 1st, mum's medicine ₹2400-ish whenever, car loan 312 every second friday" is genuinely ambiguous, and that is a real extraction job. Everything downstream of extraction is arithmetic.

---

## 7. PayPal surface

| # | API | Endpoint | Role |
|---|---|---|---|
| 1 | OAuth | `POST /v1/oauth2/token` | Credentials, all calls |
| 2 | Eligibility | JS SDK v6 `findEligibleMethods({currencyCode, countryCode, amount})` → `isEligible("paylater")`, `getDetails("paylater")` | **The gate.** Decides whether the Pay Later button renders at all |
| 3 | Pay Later session | `createPayLaterOneTimePaymentSession()` / `<paypal-paylater-button>` with `productCode` + `countryCode` | The financing flow |
| 4 | Orders v2 AUTHORIZE | `POST /v2/checkout/orders` `intent: AUTHORIZE` → `POST /v2/checkout/orders/{id}/authorize` | ≤3-day deferral: hold now, capture on payday |
| 5 | Capture / void | `POST .../authorize/{authId}/capture`, `.../void` | Settle or release the hold |
| 6 | Invoicing | `POST /v2/invoicing/invoices` with `detail.payment_term.due_date` | **The DEFER mechanic.** Invoice dated to payday |
| 7 | Webhooks | `/v1/notifications/webhooks` + `verify-webhook-signature` | `PAYMENT.CAPTURE.COMPLETED`, invoice paid, plan events |
| 8 | Transaction Search | `GET /v1/reporting/transactions` | Repeat-purchase cadence for the ledger |
| 9 | Idempotency | `PayPal-Request-Id` on every POST | Retry safety, demoed |
| 10 | AG Grid Studio | Grid + custom widgets | The exposure calendar and plan ledger view |

**Deliberately not used:** Subscriptions and vaulting — PayPal's own docs state Pay Later messaging is unavailable alongside them (`C02_VALIDATION_REPORT.md` V3).

---

## 8. Screens

1. **Storefront checkout** — the product, the price, the normal PayPal button.
2. **The verdict card** — appears where Pay Later would; OFFER / DEFER / DECLINE with one plain sentence.
3. **The four-week calendar** — income, rent, live instalments, this purchase's instalments. The collision highlighted.
4. **The balance curve** — inline SVG, projected balance across 45 days, buffer floor as a line. Nothing dips below it on a good verdict; the decline scenario visibly breaches it.
5. **The alternative** — "have it invoiced on the 5th" with the due-date invoice rendered.
6. **The override** — "buy it anyway", one click, always available.
7. **Merchant console** — the plan ledger in AG Grid: who has what live, what's about to collide, what got deferred and then paid.

---

## 9. Demo script (2:40)

| Time | Beat |
|---|---|
| 0:00–0:20 | Maya, $249 headphones, 14 days. "Four payments of $62.25. Nothing here tells her the third one lands the day after rent." |
| 0:20–0:40 | **Verdict: DECLINE.** "Instalment 3 would put you at −$83.40 on 2 December. Rent is due the 1st." |
| 0:40–1:05 | The calendar and the balance curve. The breach is visible, not asserted. |
| 1:05–1:25 | **The invoice that saves the sale.** Due 5 December. Merchant keeps it, Maya keeps her month. Real Invoicing call on sandbox. |
| 1:25–1:50 | Second shopper with room to spare → **OFFER**, `findEligibleMethods` returns `isEligible: true` with a `productCode`, Pay Later renders. |
| 1:50–2:10 | **The failure path.** Forged webhook rejected; a duplicate POST with the same `PayPal-Request-Id` does not double-charge. |
| 2:10–2:30 | Merchant console in AG Grid: "14 shoppers would have collided this month. 11 took the invoice and paid on time." |
| 2:30–2:40 | "Half of BNPL users paid late last year. Nobody at checkout tells them why. PayPal grows financial services on trust — this is what trust looks like at the moment of decision." |

---

## 10. Honesty contract — for the README and the video

```
Sandbox only. No live credentials, no real money.

What is live in this demo:
  - OAuth, Orders v2 AUTHORIZE/CAPTURE, Invoicing with due dates,
    webhook signature verification, idempotent retries
  - JS SDK v6 findEligibleMethods eligibility check

What is simulated:
  - The shopper's declared obligations (a seeded persona)
  - Instalment schedules we compute for our own ledger entries
    (PayPal does not expose a buyer's existing plans to a merchant)

What we do not claim:
  - A view of the shopper's finances beyond this merchant and
    what they have told us
  - Any credit decision. Every verdict is overridable by the shopper.
```

The UI renders the current mode as a badge — `SANDBOX · LIVE` or `SANDBOX · SIMULATED` — so no screenshot is ambiguous.

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Pay Later doesn't render in sandbox on the day | Eligibility metadata screenshot + the decision/calendar is the climax, not the button (V5) |
| Reads as paternalistic | Override always visible; copy is "here's the maths", never "you can't afford this" |
| Reads as credit scoring | Never word it as lending, underwriting or risk. Budgeting and timing only (V11) |
| Judge asks "why would PayPal reduce its own BNPL volume?" | Answer ready: PayPal reports missed payments to CRAs where Affirm/Afterpay don't (P13); a denied-then-explained shopper returns, a silently-blacklisted one churns; CEO calls financial services the growth engine, not the volume engine |
| Scope creep across 11 days | `../../plan/archive/BUILD_PLAN.md` gates; cut the merchant console before the calendar |
| LLM flakiness on stage | Deterministic template fallback, tested; the demo can run with the LLM disabled entirely |

---

## 12. Non-goals

- Not a credit score, not underwriting, not a lending decision engine.
- Not a bank-data aggregator. No open banking.
- Not a subscription manager (and see V3 — incompatible with Pay Later anyway).
- Not a rewards optimiser.
- Not multi-lender. It is merchant-scoped plus shopper-declared, and we say so.

---

## 13. What "working" means

| Signal | Target |
|---|---|
| Engine determinism | Same input → identical output, 100 runs |
| Instalment exactness | `sum == amount` for every case in the suite |
| Agent safety | 0 verdict changes across the adversarial suite |
| False-decline rate | < 5% on the seeded personas (a decline we can't justify is a bug) |
| Time to verdict | < 150 ms server-side, no network in the decision path |
| Demo | Runs end to end with the PayPal layer in simulated mode, no credentials, on a cold machine |
