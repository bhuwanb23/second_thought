# C02 — End-to-end validation report

**Verdict: GO, with four design corrections.** The concept survives validation, but not in the shape the one-pager originally described. Four checks failed and forced changes; eight passed.

Validated 1 Nov 2026 against PayPal developer documentation, the JS SDK v6 reference, platform integration constraints, the 549-repo field scan, and the existing evidence base.

---

## Summary table

| # | Check | Result | Consequence |
|---|---|---|---|
| V1 | Can we read a buyer's other BNPL plans from PayPal? | **FAIL** | Own ledger + consented declarations. Reshapes the product. |
| V2 | Is Pay Later eligibility queryable, server- or client-side? | **PASS** | `findEligibleMethods()` is the product's hook. 1% field usage. |
| V3 | Does Pay Later work alongside Subscriptions/vaulting? | **FAIL** | Subscriptions must be removed from the mechanic. |
| V4 | Can we modify PayPal's BNPL instalment schedule? | **FAIL** | The "alternative schedule" must be a different instrument, not a reshaped plan. |
| V5 | Does Pay Later render in sandbox? | **PARTIAL** | Design the demo so it is a supporting shot, never the climax. |
| V6 | How long does AUTHORIZE hold funds? | **PASS (constrained)** | 3 days. Limits deferral-by-hold to short windows. |
| V7 | Is there a mechanism for "pay on my payday"? | **PASS** | Invoicing with a due date. 0.5% field usage. |
| V8 | Is the field actually open? | **PASS** | 2 of 549 repos mention BNPL; neither is affordability. |
| V9 | Does the evidence base hold? | **PASS** | With the charge-off caveat stated alongside. |
| V10 | Is it on PayPal's stated priorities? | **PASS** | Financial services >20% of TGM, growing double digits. |
| V11 | Regulatory and ethical exposure | **PASS (conditioned)** | Not credit decisioning. Positioning is load-bearing. |
| V12 | Buildable and demoable in 10 days? | **PASS** | Proven — see the working prototype. |

---

## V1 — FAIL: consumer BNPL plan data is not exposed

**What I checked.** Every PayPal API that could plausibly return a buyer's existing instalment obligations: Orders v2 (create / get / authorize / capture / confirm), the JS SDK v6 session methods, Pay Later messaging, and the vault/payment-token APIs.

**What I found.** Orders v2 is merchant-scoped and order-scoped. `findEligibleMethods()` returns *eligibility and product metadata*, not plan history. Vaulting stores a *payment instrument*, not a repayment schedule. There is **no endpoint that returns a consumer's other Pay Later plans**, and none that spans multiple merchants or lenders.

**Why it matters.** The original concept said the agent would assemble "existing open plans" including those across lenders. It cannot. Building that would require fabricating data — which is exactly the kind of thing that collapses under a judge's question.

**The correction — and it makes the product better.**

The product owns a **plan ledger**: every Pay Later order *we* originated for that shopper, plus obligations the shopper declares on a one-screen consent form (rent, other BNPL, childcare). We also mine the merchant's own transaction history via **Transaction Search** to catch repeat behaviour.

This is not a weaker product, it is a sharper one. The harm documented in `../04_pain/QUALITATIVE_QUOTES.md` §E–F is precisely *repeat* purchase at the *same* merchant — "they usually let me take 3k joining all pay-in-4 plans", "I used it way past what I think my limit was $2500". That is entirely visible inside a single merchant's ledger. **We solve the collision that actually happens, and we say plainly what we cannot see.**

Phrase it in the submission exactly that way. A judge who hears "here is the data we can see, here is what we cannot" trusts the rest of the demo more, not less.

---

## V2 — PASS: eligibility is queryable, and it is the integration hook

**Found.** JS SDK v6 exposes:

```js
const methods = await sdk.findEligibleMethods({ currencyCode: "USD", countryCode: "US", amount: "249.00" });
if (methods.isEligible("paylater")) {
  const { productCode, countryCode } = methods.getDetails("paylater");
}
```

The `amount` parameter exists specifically because **different financing options have minimum and maximum amount thresholds** — which means eligibility is genuinely amount-dependent, not a fixed flag.

**Why this is the hook.** Only **1%** of the 549-repo field uses JS SDK v6. `paylater` is used by **4%**. So this is a documented, first-class, load-bearing API that almost nobody in the competition touches. It is the single cleanest "deep integration" signal available to this concept.

Also present: `createPayLaterOneTimePaymentSession()` for the financing flow itself, and the `<paypal-message>` / `<paypal-paylater-button>` web components with `productCode` + `countryCode` from eligibility.

---

## V3 — FAIL: Pay Later is incompatible with vaulting and subscriptions

**Found, in PayPal's own platform docs:**

> "Promoting Pay Later offers is not available if you're using vaulted payments or subscriptions."

**Why it matters.** The original one-pager had restructured plans running on **Subscriptions** (3% field usage — I flagged it as a gap). That is invalid in the same merchant context as Pay Later messaging. Shipping it would have produced a demo where one feature silently disables another.

**Correction.** Subscriptions are **out** of the mechanic. The restructure path becomes Invoicing (V7). Keep Subscriptions out of the README too — do not claim an API you cannot coherently use.

---

## V4 — FAIL: we cannot rewrite PayPal's instalment schedule

**What I checked.** Whether a merchant-side API can alter the number or dates of a buyer's Pay in 4 instalments.

**What I found.** No. The instalment plan is a credit product between PayPal and the buyer. A merchant creates a one-time order; PayPal finances it. The merchant has no handle on the repayment schedule.

**Why it matters.** "We offer a cheaper 4-payment schedule that fits your paydays" was the original RESHAPE action. It is not implementable, and a PayPal judge would know within seconds.

**The correction — reframe from *reshape the plan* to *choose the right moment*.**

Three verdicts, each with a mechanism we actually control:

| Verdict | When | Mechanism |
|---|---|---|
| **OFFER** | The purchase fits comfortably | Show Pay Later via `findEligibleMethods` gating + the standard session |
| **DEFER** | It fits, but not today | **Invoice with a due date on their payday** (`/v2/invoicing/invoices`) — merchant-controlled, honest, and the buyer simply pays when the money is there |
| **DECLINE** | It would collide with something essential | Do not surface Pay Later. Explain the specific collision. Offer the safe amount or the deferral. |

A secondary path, for deferrals of **three days or less**, is a true `AUTHORIZE` hold that captures on the payday. Beyond three days that is not available (V6), so it is a short-deferral optimisation, not the main mechanic.

This is a better product than the original: instead of pretending to renegotiate someone else's credit contract, it **routes the transaction to the instrument that actually fits the shopper's month.**

---

## V5 — PARTIAL: Pay Later in sandbox is conditional

**Found.** Sandbox *can* render Pay Later — the documented pattern is `client-id=sb&components=buttons,messages&enable-funding=paylater`. But real eligibility depends on merchant country and account type, payer country, and amount thresholds. PayPal's own docs scope Pay Later messaging to **US merchants with US-facing sites and a one-time payment integration**. A live Pay Later *plan* is not something a hackathon demo can count on.

**Correction — structural, not cosmetic.** Build the demo so that:

1. The **climax is the affordability decision and the calendar**, both fully ours and fully deterministic.
2. The **Pay Later button is a supporting shot** — show it rendering (or show the eligibility call returning `isEligible: true` with a `productCode`), and have a fallback shot ready if it does not render on the day.
3. The **README states plainly** which parts are live PayPal sandbox calls and which are simulated, and the **UI shows a mode badge** (`SANDBOX · LIVE` / `SANDBOX · SIMULATED`) so no screenshot is ever ambiguous.

Never fake a Pay Later offer screen. Show eligibility metadata instead.

---

## V6 — PASS, constrained: AUTHORIZE holds for three days

An authorization is valid for **3 days** for most transaction types (up to 29 only for specific eligible flows). So:
- ≤3-day deferral → `AUTHORIZE` now, `CAPTURE` on payday. Correct and demonstrable.
- \>3-day deferral → invoice with a due date. Not a hold.

Document this in the README. It is the kind of detail that reads as competence.

---

## V7 — PASS: Invoicing gives us the honest "pay on payday" path

`POST /v2/invoicing/invoices` with `detail.payment_term.due_date`, plus reminders and QR payment. Used by **0.5%** of the field.

This is the mechanism that turns a DEFER verdict from a lecture into an action: the merchant issues an invoice dated to the shopper's payday, the shopper pays when the money is actually there, the merchant still makes the sale. Both sides better off than either a declined BNPL or a late fee.

---

## V8 — PASS: the field is genuinely open

From `../03_field/REPOS.csv` (549 repos, 1 Nov 2026):

- **2 repos out of 549** mention BNPL, Pay in 4, instalments or "affordability" in their description at all.
- Neither is an affordability product: one is a merchant shopping agent, the other is medical-bill imaging that happens to accept Pay Later.
- `credit-bnpl` cluster = **3 repos**, and **none** of the 12 highest-depth repos in the field touch it.

Compare with `mandate-guardrail` at 86. This is the thinnest meaningful cluster in the competition that also has a strong intent fit.

---

## V9 — PASS, with the caveat stated

| Claim | Number | Safe to use as |
|---|---|---|
| BNPL users who paid late in the past year | 47% (34%→41%→47%, 2024–26) | LendingTree survey — cite as survey self-report |
| Say BNPL caused overspending | 68% | same |
| Hold multiple simultaneous BNPL loans | 63% (33% cross-lender) | CFPB Jan 2025 |
| Triggered overdraft/NSF | 11% | CFPB |
| Late fee incidence / average fee | 4.1% of loans / $9.99 | CFPB Dec 2025, covers PayPal by name |
| **Charge-off rate** | **1.83% (2023)** | **must be stated alongside the late-payment figures** |

The last row is the integrity test. Self-reported late payment (47%) and formal charge-off (1.83%) measure different things, and a judge who knows the CFPB report will notice if only the alarming number appears. State both, then make the argument the data actually supports: **the harm is small, repeated, badly-timed payments — not catastrophic default.**

---

## V10 — PASS: squarely on PayPal's stated priorities

From `../02_intent/INTENT_SIGNALS.csv`:

> "More than 20% of 2026 transaction margin dollars come from financial services, now growing double digits." — Q3 2026 earnings call

Plus: PayPal funds the merchant upfront and therefore carries the credit risk on every instalment (ledger P13) — so PayPal has the most to lose from a badly-timed one, and the most to gain from getting the timing right. **Correction (1 Nov): the earlier version of this line claimed PayPal reports missed payments to credit reference agencies where Affirm and Afterpay do not. That is out of date — Affirm reports Pay in 4 to Experian since Apr 2025 and TransUnion since May 2025 — and has been removed.** That is a real, specific, non-generic answer to "why would PayPal want this?"

---

## V11 — PASS, conditioned: this is not credit decisioning

**The exposure.** A product that tells someone not to borrow is adjacent to regulated credit activity.

**The firewall, which must hold in the code and the copy:**

| We do | We do not |
|---|---|
| Arithmetic over data the shopper gave us or that we originated | Score, rank or underwrite a person |
| Explain a collision between two dated amounts | Use ML on personal characteristics |
| Let the shopper override any verdict | Deny a payment method the shopper is entitled to |
| Show the merchant a display policy | Report anything to a credit bureau |

Every verdict is **overridable by the shopper** — the engine recommends, and the UI must show a plain "buy anyway" path. That single design choice moves the product from "paternalistic credit gate" to "budget transparency", which is both ethically and rhetorically correct.

Word the submission as **budgeting and timing transparency**, never as "responsible lending" or "credit risk".

---

## V12 — PASS: proven, not asserted

A working prototype now exists in `../../../product/.env.example`: a deterministic integer-cents engine, a plan ledger, an invoice/authorize execution path with a live/simulated PayPal adapter, an agent layer that cannot alter the verdict, and a test suite including red-team cases.

Run it:

```bash
cd ../../../product/.env.example && python3 -m pytest tests -q   # or: python3 tests/run_tests.py
python3 demo.py                                       # CLI end-to-end
python3 server.py                                     # UI at :8000
```

The engine, the verdicts, the calendar and the tests are real. The PayPal layer runs live when credentials are present and simulates otherwise, always labelled.

---

## What the concept is now

**Original:** an agent that sees all your BNPL plans and builds you a better repayment schedule.

**Validated:** an agent that decides, at checkout, whether *this* purchase fits *this* shopper's next four weeks — and routes the sale to the right instrument when it doesn't: **Pay Later** when the timing is fine, **an invoice dated to payday** when it isn't, **nothing** when it would push them into an essential bill.

Same thesis, honest mechanism. Four checks failed and the product is better for it.
