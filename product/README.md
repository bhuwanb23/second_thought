<p align="center">
  <img src="assets/png/logo-primary.png" alt="Second Thought" width="380">
</p>

<h3 align="center">A checkout that sometimes says <em>not yet</em> — and tells you why.</h3>

<p align="center">
  <a href="https://github.com/OWNER/second-thought/actions/workflows/tests.yml"><img alt="tests" src="https://img.shields.io/badge/tests-173%20passing-0f7b4f"></a>
  <img alt="dependencies" src="https://img.shields.io/badge/dependencies-0-0f7b4f">
  <img alt="python" src="https://img.shields.io/badge/python-3.11%2B-14181f">
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-MIT-14181f"></a>
</p>

<p align="center">
  <b><a href="https://second-thought-h61b.onrender.com">Live demo</a></b> ·
  <b><a href="https://youtu.be/PLACEHOLDER">2:40 video</a></b> ·
  <b><a href="../docs/Second-Thought-Dossier.pdf">The dossier</a></b> ·
  <b><a href="https://second-thought-h61b.onrender.com/proof">/proof</a></b> ·
  <b><a href="SECURITY.md">security model</a></b>
</p>

Most BNPL is decided by the amount and the country. **Second Thought is decided by the month.**

Three shoppers, one $249 purchase, three different answers — and the answer that matters is the
one a BNPL provider never gives.

| Shopper | What is already in her month | Verdict | What the shop does |
|---|---|---|---|
| **Ada** | comfortable | **OFFER** | An `AUTHORIZE` hold: funds reserved, valid 3 days |
| **Ben** | a car payment lands before payday | **DEFER** | A reservation: invoice dated to payday, **ships after payment** |
| **Cleo** | genuinely squeezed | **DECLINE** | Nothing offered — the collision is named, and **$140 would fit** |

<p align="center">
  <img src="assets/png/diagram-verdicts.png" alt="Three verdicts from the same amount" width="820">
</p>

> **This one doesn't fit right now**
> Paying $249.00 today leaves you short — because the 4th payment on a plan you already have lands
> around Sun 22 Dec. **Up to $140.00 would work today.**
> *Pick something smaller*

**Who it is for:** a shopper about to split a payment, and the merchant who would rather keep the
sale in three weeks than lose it today — and who is currently paying a lender 5% to do it for them.

## Run it

```bash
python3 scripts/serve.py               # the page on :8000 — no login, no keys, no network
python3 -m secondthought.cli           # the whole product in a terminal
python3 demo.py --dry-run              # the five PayPal calls, fake transport (no credentials)
python3 demo.py --live                 # the same five, against the PayPal sandbox
python3 demo_ai.py --offline           # the AI reader on unfamiliar text + a tampered approval
bash scripts/v5_two_jars.sh            # 22 live security checks
python3 -m unittest discover -s tests -q   # 173 tests, 0.3 s
```

**No dependencies. Python 3.11+. Every file under 300 lines.**

## Why this is not BNPL — the arithmetic

PayPal's own Pay Later settles the merchant **immediately**, minus **4.99% + $0.49**. Ours collects
from the shopper in two instalments and pays the shop on day 45. For a shop with thin cash flow that
sounds worse, so here is the same $400 job both ways:

| | PayPal Pay in 4 | Second Thought |
|---|---|---|
| Merchant fee | **$20.45** (4.99% + $0.49) | **$0** |
| Money arrives | day 0 | day 45 |
| Expected loss at 2.7% (Affirm's 30+ delinquency) | borne by PayPal | **$10.80**, borne by the shop |
| Who gets declined | whoever PayPal's model declines | whoever **this month** says no — and they can come back |
| **Shop keeps** | $379.55, today | **$389.20**, in 45 days |

The shop keeps about **$9.65 more per $400** — but only if the underwriting is as good as a lender's,
which is why the engine is deterministic and a model cannot overrule it. And the 10–15% of customers
whom Sunbit and CareCredit decline are still customers if a shop can say *"yes, in three weeks"*.

**This does not replace PayPal's rail, it replaces the lender.** Both instalments are ordinary PayPal
payments, so PayPal earns on both; the deferral moves an order onto the rail that would otherwise have
gone to Klarna, or to nobody. At PayPal's current 1.58% take rate, PayPal is ahead as soon as **38%**
of deferred orders would not have used Pay Later anyway — and a shopper whose month does not fit is
exactly the shopper who leaves.

## PayPal developer platform used

| What | Endpoint | Where |
|---|---|---|
| OAuth 2 client credentials | `POST /v1/oauth2/token` | `infra/paypal_live.py` |
| Orders v2 — create, **AUTHORIZE**, capture, void | `POST /v2/checkout/orders`, `/v2/payments/authorizations/{id}/capture`, `…/void` | `infra/paypal_live.py` |
| Invoicing v2 — create, send, `payment_term.due_date` | `POST /v2/invoicing/invoices` | `infra/paypal_live.py` |
| Webhooks — **signature verification** | `PAYPAL-TRANSMISSION-*` headers, RSA-SHA256 over the raw body | `infra/webhook.py`, `infra/rsa.py` |
| Idempotency | `PayPal-Request-Id` on every mutating call | `infra/paypal_live.py` |

Server-side OAuth only: no client secret ever reaches the browser. Sandbox only — `PAYPAL_ENV=live`
is refused at runtime.

**Why no PayPal SDK.** There is no SDK for Python 3.13 without pulling in dependencies, and "zero
dependencies" is a promise this project keeps everywhere else: the webhooks module verifies PayPal's
RSA-SHA256 signature with a PKCS#1 v1.5 implementation written here (`infra/rsa.py`, 200 lines), so the
one security-critical path in the integration has no supply chain and 10 tests behind it. The cost is
real — the official SDKs are the most legible proof of platform familiarity — so here is the code
instead: `infra/paypal_live.py`, five endpoints, every failure mode tested with a fake transport.

## Two payments, on purpose

The plan is **two instalments at 0% over 45 days**. That is not a marketing choice: two interest-free
instalments keeps a merchant's own plan book outside consumer-credit licensing in the US, the UK's
incoming BNPL regime and India's digital-lending rules. Add a third instalment, or any fee, and the
product becomes regulated lending — which a merchant cannot do and this code will not pretend to.

## The problem, with sources

- **47%** of BNPL users reported paying late at least once in the past year, up from 41%
  in 2025 and 34% in 2024 — LendingTree, 2026. (Self-reported. The CFPB's dollar-weighted
  charge-off rate stays under 2%; both are true, and they measure different things.)
- **63%** of BNPL users held multiple simultaneous loans, and **33%** held them across
  multiple lenders — CFPB, January 2025.
- **10,884** BNPL complaints in 2026 to date against **7,412** in all of 2025 — **+47%**
  with two months still to run — CFPB complaint database.

The harm is not that the product exists. It is that it is offered indiscriminately, in small
repeated badly-timed payments — the exact pattern one extra question at checkout catches.

## AI used

An OpenAI-compatible chat endpoint (`POST {base_url}/chat/completions`, `temperature: 0`,
`response_format: json_object`) reads a shopper's free text — *"salary's 2,400 on the 15th,
rent's 1,375 on the 1st, car loan 312 every second friday"* — into dated amounts.

**The model supplies facts. The engine supplies the verdict.** There is no code path from
a model output to a decision: `Agent.profile_from` raises rather than pass a `demo`-grade
extraction into the engine, and a unit test asserts the verdict does not move when the
wording is junk. The badge on screen reads `AI · LLM-MOCK` until a real key is loaded,
then `AI · LLM`.

## Assets

`assets/` holds the logo, the app icon, the Devpost thumbnail and seven diagrams — SVG
source plus PNG, all generated from one palette (`scripts/asset_kit.py`) so nothing drifts
from the product page. Open `assets/index.html` to see the whole set at once.

| | |
|---|---|
| ![decision](assets/png/diagram-flow.png) | ![verdicts](assets/png/diagram-verdicts.png) |
| ![defer](assets/png/diagram-defer.png) | ![boundary](assets/png/diagram-ai-boundary.png) |

Regenerate with:

```bash
python3 scripts/make_assets.py && python3 scripts/make_diagrams.py && python3 scripts/make_asset_index.py
```

## The page

`/` is the one screen a stranger sees first
([`../docs/plan/V8_outside_eye.md`](../docs/plan/V8_outside_eye.md)). Three named months,
each with its amount, visible without clicking; click one and the answer arrives as a
sentence rather than a status code — *"Pay on Sat 7 Nov — and it ships once you've paid"*
— with the canonical verdict kept as a small label underneath. A textarea below it reads
free text and shows what it understood, flagging anything it is unsure about. Money is
simulated, nothing is charged, and both badges say so on the screen.

It is one self-contained HTML file with inline CSS and no external assets, so it renders
on a locked-down laptop with no network of its own. `tests/test_screens.py` fails the
build if internal vocabulary (verdict, collision, authorisation, token, api…) reaches a
sentence a shopper reads.

`demo_ai.py` is the V4 instrument ([`../docs/plan/V4_live_ai.md`](../docs/plan/V4_live_ai.md)):
the badge, three passages the reader was not written for, and the full
extraction → decide → propose → approve → invoice path — including a deliberately
tampered approval that must be refused.

`demo.py` is the V3 instrument ([`../docs/plan/V3_live_paypal.md`](../docs/plan/V3_live_paypal.md)):
OAuth, order AUTHORIZE → capture, AUTHORIZE → void, an invoice dated by the engine's
payday math, and a same-`PayPal-Request-Id` retry. `--dry-run` and `--live` run the same
code path — only the transport differs — so a dry run proves the wiring and nothing about
your account. Live runs write `artifacts/v3/<timestamp>/` with every raw response and the
dashboard location where each ID can be found.

## What happens on the DEFER path

DEFER is the hero, and it is the one screen a judge should remember:

> **Pay on Sat 15 Nov — and it ships once you've paid**
> Taking $249.00 today would leave you short before your next payday. Nothing is charged now, the
> price is held, and it goes out the door after your payment clears.

The rule the product will not break: **pay before ship.** `fulfil()` raises unless the reservation is
`PAID`, and there is no method that lets a caller skip the payment state — a merchant integrating
this cannot accidentally ship into unpaid credit.

## Architecture

```
secondthought/
├── domain/              pure rules — imports nothing outside itself
│   ├── cashflow.py      calendars, money, balance projection
│   ├── engine.py        the verdict, the floor, the safe amount
│   └── reservation.py   pay-before-ship as a state machine
├── app/                 use cases
│   ├── checkout.py      quote → propose → execute; three outcomes
│   ├── approvals.py     HMAC approval tokens: bound, expiring, single-use
│   └── ports.py         what the app needs from the outside world
├── infra/               the outside world
│   ├── db.py            SQLite: profiles, reservations, ledger, webhook idempotency
│   └── gateway.py       simulated PayPal, held to the real contract
├── interfaces/          HTTP + browser interface
└── cli.py               runs the whole thing
```

**The dependency arrow points one way.** `domain/` never imports `app/` or `infra/`, which is what
makes "the engine decides, the model only phrases" checkable by reading a directory.

## The four guarantees, and where each is enforced

| Guarantee | Enforced in | Test |
|---|---|---|
| **A merchant cannot ship before payment** | `reservation.fulfil()` requires `PAID` | `test_you_cannot_ship_before_payment` |
| **Nothing moves without human approval** | `approvals.redeem()` before any gateway call | `test_nothing_moves_without_approval` |
| **An approval is bound to one action** | HMAC over tool + exact arguments | `test_a_token_for_a_different_amount_is_refused` |
| **A retried webhook is harmless** | `pay()` is idempotent; `webhook_events` table | `test_a_retried_webhook_is_harmless` |

Two more: authorisations expire after **3 days** (`_AUTH_VALID_DAYS`), and capturing twice returns
the first capture rather than charging again.

## Tests

```
$ python3 -m unittest discover -s tests -q
Ran 173 tests in 0.335s
OK
```

173 tests, standard library only, no network. They include the invariants that matter:
you cannot ship before payment, nothing moves without a human approval, an approval is
bound to one action and cannot be replayed, a retried webhook is harmless, a foreign
session cannot spend another's budget, and **the demo still shows three different verdicts
on any day for the next sixty** — because judging runs 1–15 December and a pinned date
would have broken it.

## Privacy and the real data path

- **What we store:** nothing about a person. A session lives in memory, holds the profile
  you typed and dies with the process. A redeploy logs everyone out — by design.
- **What we send:** only the free text you type in the box, only when you press *Read this*. No
  name, no email, no account.
- **What we keep:** invoices and reservations in SQLite, keyed by the demo shopper id (`ada`, `ben`,
  `cleo`, `me`), so the pay-before-ship lifecycle can be demonstrated.
- **What we never touch:** real money, real accounts, or a live PayPal environment.

## Honest labels

`SimulatedGateway.mode == "simulated"`. Invoice ids begin `INV2-SIM`; authorisations begin
`AUTH-SIM`. The simulated gateway speaks the **same protocol** as the live adapter — same shapes, same
failure modes — so switching to the sandbox changes the `mode` string and nothing else. A demo that
hides which one it is running is the failure this design exists to prevent.

---

## Status, honestly

**Built and tested here:** the domain kernel (verdict, floor, safe amount), the reservation
lifecycle with pay-before-ship as a state machine, HMAC approval tokens bound to one action and one
amount, SQLite persistence, webhook signature verification and idempotency, the live PayPal adapter
(Orders v2 AUTHORIZE/capture/void, Invoicing v2), the AI reader with a template fallback, the HTTP
interface with per-session isolation and two-key rate limits, and the three screens.

**Not yet true — and the badge says so on screen:**

| Gate | State | What it needs |
|---|---|---|
| V3 — five real PayPal calls | PARTIAL | OAuth and idempotency passed; Invoicing requires the sandbox app permission, and capture/void require buyer approval |
| V4 — a real model behind the badge | BLOCKED | `python3 demo_ai.py --live` with `LLM_API_KEY`; the configured provider timed out during the run |
| V6 — deployed, hosted, still up on 15 Dec | OPEN | a Render deploy and a webhook id |
| V7 — a human has used it | OPEN | five conversations, or an honest n = 0 |

The distinction is the point. Every number in this README was produced in this repository; anything
that has not been run against PayPal or a real model is labelled PARTIAL, BLOCKED, or OPEN rather than claimed.

## Proof

`/proof` renders the measured numbers for the running build: test count and duration, the 22 security
checks, the 17 deploy preconditions, the constants the engine is configured with, and the timestamp of
the last recorded run — plus the exact commands to reproduce each line, because a number you cannot
re-run is a rumour.

```bash
python3 scripts/make_proof.py                      # writes artifacts/proof.json
python3 scripts/serve.py & curl -s localhost:8000/proof | head -40
```

The long version, with the research, five bugs that broke, gates and the eight-day plan, is
[`docs/Second-Thought-Dossier.pdf`](../docs/Second-Thought-Dossier.pdf).

## License

MIT — see [LICENSE](LICENSE). Use it, fork it, take it apart.
