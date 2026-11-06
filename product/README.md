# Second Thought — the product

**A payday-aware checkout that sometimes says "not yet".**

This is the canonical build, written from scratch around the locked idea
([`../docs/research/07_concepts/C02_THE_IDEA.md`](../docs/research/07_concepts/C02_THE_IDEA.md)).
The earlier prototype is preserved in `../archive/prototype/` for reference and is not deployed.

```bash
python3 -m secondthought.cli        # the whole product, in a terminal, no network
python3 demo.py --dry-run           # the five live PayPal calls, on a fake transport
python3 demo.py --live              # the same five, against the real sandbox
python3 demo_ai.py --offline        # the AI reader on unfamiliar text + a tampered approval
python3 demo_ai.py --live           # the same, with the real model
python3 scripts/serve.py            # the HTTP interface on :8000 — open / in a browser
bash scripts/v5_two_jars.sh         # 22 live checks: isolation, limits, /healthz, tokens
python3 scripts/preflight_deploy.py # 18 checks on root render.yaml
python3 scripts/v6_cold_check.py --url https://<app> --record|--compare   # did it sleep?
python3 -m unittest discover -s tests -q
```

**No third-party runtime dependencies. Python 3.11+. Every file under 300 lines.
155 tests, ~0.35 s.**

The HTTP runtime uses the configured `ST_DB_PATH`; Render maps this to its
paid persistent disk. It selects the simulated
gateway without PayPal credentials and the sandbox adapter when credentials are
configured. `PAYPAL_ENV=live` is rejected by the adapter.

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

---

## What it does, end to end

Three shoppers, three different answers, one promise:

| Shopper | Month | Verdict | What happens |
|---|---|---|---|
| **ada** | comfortable | **OFFER** | Pay Later. An `AUTHORIZE` hold is placed — funds reserved, valid 3 days |
| **ben** | a car payment lands before payday | **DEFER** | A **reservation**: invoice dated to payday, and the merchant **ships only after payment** |
| **cleo** | genuinely squeezed | **DECLINE** | Nothing offered. The collision is named, and **$140 would fit** — at $140 she gets OFFER |

The rule the product will not break:

> **Pay before ship.** `fulfil()` raises unless the reservation is `PAID`. There is no method that
> lets a caller skip the payment state, so a merchant integrating this cannot accidentally ship
> into unpaid credit.

---

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
├── interfaces/          HTTP + browser (next)
└── cli.py               runs the whole thing
```

**The dependency arrow points one way.** `domain/` never imports `app/` or `infra/`. That is what
makes "the engine decides, the model only phrases" checkable by reading a directory, rather than
trusting a claim.

---

## The four guarantees, and where each is enforced

| Guarantee | Enforced in | Test |
|---|---|---|
| **A merchant cannot ship before payment** | `reservation.fulfil()` requires `PAID` | `test_you_cannot_ship_before_payment` |
| **Nothing moves without human approval** | `approvals.redeem()` before any gateway call | `test_nothing_moves_without_approval` |
| **An approval is bound to one action** | HMAC over tool + exact arguments | `test_a_token_for_a_different_amount_is_refused` |
| **A retried webhook is harmless** | `pay()` is idempotent; `webhook_events` table | `test_a_retried_webhook_is_harmless` |

Two more that matter in production: authorisations expire after **3 days** (`_AUTH_VALID_DAYS`), and
capturing twice returns the first capture rather than charging again.

---

## Honest labels

`SimulatedGateway.mode == "simulated"`. Invoice ids begin `INV2-SIM`; authorisations begin
`AUTH-SIM`. The simulated gateway implements the **same protocol** as the live adapter — same shapes,
same failure modes — so switching to the real PayPal sandbox changes the `mode` string and nothing
else. A demo that hides which one it is running is the failure this design exists to prevent.

---

## What is built, and what is next

**Built:** the domain kernel, the reservation lifecycle, the approval gate, SQLite persistence,
webhook idempotency, the three outcomes, a CLI that exercises all of it, and **the live PayPal
adapter** — Orders v2 (AUTHORIZE/capture/void) and Invoicing v2 — behind the same protocol as the
simulated one, with a `demo.py` that drives the five calls V3 asks for.

**Next, in order:**

1. ~~**HTTP interface**~~ — done: `interfaces/http.py` + `interfaces/session.py`, a box per visitor,
   per-session approval keys, two-key rate limiting, and a `/healthz` that says booleans and nothing else.
2. **The three screens** — payday profile setup, the checkout verdict, the reservation/tracking view.
3. **Webhook signature verification** — the callback that marks a reservation paid.
4. ~~**The AI layer**~~ — done: `ai/extract.py` (model) and `ai/template.py` (fallback), with
   per-field confidence, `answer_quality`, and an agent whose model output can never become
   a verdict.

Each of those slots into an interface that already exists, which is the point of building this way
round: the rules were settled before the wire.
