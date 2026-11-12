# Second Thought — payday-aware checkout

**The checkout that tells you the truth about your next four weeks.**

At the moment Pay Later would be offered, Second Thought projects the shopper's next 45 days
and answers one of three ways:

- **OFFER** — it fits, show Pay Later
- **DEFER** — it fits, but not today → a PayPal invoice dated to their payday
- **DECLINE** — it collides with an essential bill → don't surface it, name the bill and the date, quote a safe amount

**Public-demo safety:** every visitor gets a cookie-scoped session (`session.py`). Personas are
read-only, saved profiles and ledgers are in-memory and disposable, state is bounded to 400 sessions,
and LLM-backed endpoints are rate-limited to 30 calls per session per 10 minutes. Verified over HTTP
with two cookie jars: one visitor saving a profile cannot change another's verdict.

**What the product admits:** with no payday profile, the answer is labelled `answer_quality: demo` —
"not your real data". With unconfirmed lines, it says how many. A confidence badge that only ever
says "confident" is not a confidence badge.

**The DEFER rule:** *pay before ship*. The merchant reserves the item and the price, but ships only
after payment clears. The merchant never extends credit and never carries the risk PayPal carries
under Pay Later. Enforced in `paylater.describe_instrument()` and asserted by a test.

The shopper can always override. **Nothing is ever blocked.**

PayPal AI Hackathon 2026 · sandbox only, no real money.

---

## Run it

Python 3.11+, no dependencies.

```bash
python3 -m unittest discover -s tests -q   # 119 tests
python3 demo.py                            # end-to-end walkthrough, no credentials
python3 server.py                          # http://localhost:8000
bash scripts/preflight.sh                  # submission checks
```

With sandbox credentials it makes real REST calls, and says so:

```bash
cp .env.example .env    # fill in PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET
set -a; . ./.env; set +a
python3 demo.py --live
```

---

## What the AI does — and how to see it live

There are **two real jobs**, both visible in the demo and on screen:

**1. Reading prose into a calendar.** The shopper types or says *"rent 1450 on the 28th, car loan
312 on the 20th, mum's meds about 40"*. The model extracts structured obligations with a
confidence score per line; low-confidence items are flagged for the shopper to confirm, never
silently trusted. Try it in the UI card **"Anything else in your month?"**, or:

```bash
curl -s -X POST localhost:8000/api/extract -H 'Content-Type: application/json' \
  -d '{"persona":"dev","text":"rent 1450 on the 28th; car loan 312 on the 20th"}'
```

**2. An agent with a tool surface, gated by human approval.** The agent can read freely
(`extract_obligations`, `decide_purchase`) and may *propose* money actions
(`create_scheduled_invoice`, `authorize_payment`). A money action executes only with an
approval token **bound by HMAC to that exact tool and those exact arguments** — so an approval
for $249 cannot pay $999. Watch it in the UI with **"Show the agent working"**, or:

```bash
curl -s -X POST localhost:8000/api/agent -H 'Content-Type: application/json' -d '{"persona":"dev"}'
```

> **Before you record:** set `LLM_API_KEY` (and optionally `LLM_MODEL`) or the AI badge reads
> `LLM-MOCK` instead of `LLM`. The mock runs the *identical* code path so nothing else changes,
> but a judge should see a real model doing the extraction. Name the model in the submission's
> "Tools used" field either way.

### The rule that does not bend

> **The model never decides whether money moves.**

`engine.decide()` produces every verdict, amount and date from arithmetic — integer cents, no
network, no model, no randomness. The agent layer may phrase it and may propose actions, but:
- `LLMExplainer._validate()` rejects any output whose verdict differs from the engine's
- `explain()` re-checks the verdict after generation and discards the model's words on mismatch
- money tools require a human approval token
- `tests/test_agent.py::TestVerdictCannotBeChanged` proves all of this with a deliberately rogue explainer

---

## Architecture

```
engine.py     THE DECISION. Integer cents. No model, no network, no randomness.  32 tests
agent.py      THE WORDS.    Template fallback + optional LLM. Cannot change a verdict.
llm.py        THE MODEL.    OpenAIChat (real tool calling) | MockChat (labelled stand-in).
agentic.py    THE AGENT.    Extraction + a tool loop with an HMAC approval gate.
paylater.py   THE INSTRUMENT. Resolves OFFER into paylater | authorize_hold | invoice.
paypal.py     THE RAILS.    Live REST or simulated transport, one interface.
ledger.py     THE MEMORY.   Every plan we originated — because PayPal won't tell us.
profile.py    THE SHOPPER.  Payday profile, set up once, applied silently at checkout.
session.py    PER VISITOR.  Cookie-scoped state, so one judge cannot change the next judge's verdict.
server.py     THE DEMO.     Stdlib HTTP, JSON API, approval endpoint.
web/index.html THE PRODUCT. Self-contained: inline CSS, inline SVG, no external requests.
```

---

## Test output

```
$ python3 -m unittest discover -s tests -q
Ran 119 tests in 0.212s
OK
```

| Area | Guarantee |
|---|---|
| Instalment split | `sum(parts) == amount` exactly, largest-remainder, no cent invented or lost |
| Determinism | Same input → identical output, 20 consecutive runs |
| Overdraw | An option that leaves the balance negative is never feasible, even at `buffer_pct=0` |
| Safe amount | The exact boundary — one minor unit more must fail |
| Verdict safety | A rogue explainer cannot change a verdict |
| Extraction | Malformed model output (bad amount, fantasy date, no label, >12 items) is rejected and falls back to rules |
| Approval gate | Money tools refuse without a token; a token for $249 is rejected for $999; a token for one tool is rejected for another |
| Agent loop | Bounded at 8 steps; stops for approval; executes only after approval |
| Idempotency | Same `PayPal-Request-Id` never creates two orders |
| Webhooks | Valid signature accepted, missing transmission id rejected |
| Offline decision | `engine.py` imports no network module — asserted by reading its source |
| Sandbox only | The live PayPal host is a named constant never used in a call |

---

## The three demo personas

Run `python3 demo.py`. They are the three branches of the product, not decoration.

| Persona | Situation | Verdict | Why |
|---|---|---|---|
| **Maya** | $400 left, paid fortnightly, rent on the 29th | **DECLINE** | Instalment 3 lands the same day as rent. Lowest point $113 against a $150 cushion — $36.75 short. Safe amount $200. |
| **Dev** | The 1st, $280 left, paid on the 6th | **DEFER** | Timing, not affordability. An invoice due the 6th fits with $280 to spare. |
| **Sam** | $2,100 on hand, comfortable | **OFFER** | Never dips below $1,925. The tool is not a naysayer. |

A fourth case — Maya buying the $158 option — flips to **OFFER**. That is why the safe amount
matters: it turns a refusal into a smaller sale.

**A structural finding worth keeping in the pitch:** an invoice can only rescue a *front*-of-month
timing problem. If the collision is a big bill *later* in the month, deferring makes that date
worse, so the engine refuses to pretend otherwise. That is why Maya declines and Dev defers —
same product, different month shapes.

---

## What is live, what is simulated

| | Status |
|---|---|
| OAuth, Orders v2 AUTHORIZE/capture/void, Invoicing with due dates, webhook signature verification, idempotent retries | **Live** when credentials are set |
| Model extraction and the agent tool loop | **Live** when `LLM_API_KEY` is set; otherwise a labelled mock on the same code path |
| Pay Later eligibility | **Client-side only.** See `PAYLATER_SANDBOX_TEST.md` — the server never guesses it |
| Shopper's obligations and opening balance | **Simulated persona, or a saved payday profile** (`POST /api/profile`). In production the shopper sets it up once; see `DATA_AND_PRIVACY.md` |
| A real Pay Later *plan* | **Not simulated and not faked.** No offer screen is mocked |

The UI renders `SANDBOX · LIVE|SIMULATED` and `AI · LLM|LLM-MOCK|RULES` as badges, so no
screenshot is ever ambiguous.

---

## Deployment

```bash
docker build -t second-thought . && docker run -p 8000:8000 second-thought
```

`render.yaml` is set to the **starter** plan, not free: a free instance sleeps, and a 50-second
cold start inside a judge's three-minute window is a lost score. The submission must stay up
until **15 Dec 2026 08:00 PT**.

Keep-alive is belt and braces — `.github/workflows/keepalive.yml` pings `/healthz` every 10
minutes and fails loudly. GitHub's scheduler is best-effort and gets disabled on inactive
repos, so use a paid instance or UptimeRobot (5-minute interval) as the primary mechanism and
the workflow as a backstop. Verify it on **1 December**, not on 14 December.

---

## Production notes — deliberately small

The prototype is Python stdlib plus one HTML page. **Do not rewrite it.** Rewriting working,
tested code in ten days is how hackathon entries die. The plan:

| Priority | Work | Why |
|---|---|---|
| 1 | Keep this service as the decision API; polish the existing UI | Zero migration risk, all 119 tests keep passing |
| 2 | Set `LLM_API_KEY` on the host; record the extraction on screen | The AI must be visible, not claimed |
| 3 | Record the video by 10 Nov | See `../../docs/plan/SUBMISSION_KIT.md` |
| 4 | AG Grid — **conditional, decide by 5 Nov** | See the honest note below |
| 5 | APIMatic | Only if genuinely used while building |

### AG Grid — the honest position

AG Studio needs React, and the prize is judged on polish plus **Studio Agent Framework** use. A
bolt-on table will not win it. So:

- **If** you can wrap just the merchant-ledger view as a small React island by **5 November**, do
  it — five winner slots and $10,000 is the best value in the contest, and the ledger is a real
  decision surface (who is about to collide, what to do about it).
- **If not**, skip it. A half-integrated grid risks the demo, and the core prize is worth more
  than a sponsor prize. *Decide on 5 Nov and write the decision down.*

### APIMatic — not "free"

It is a tool for your coding agent. To claim it honestly you must **actually use it while
building** and document what it did — for example, generating the typed PayPal client that
`paypal.py` hand-rolls today. That is a reasonable half-day task. Naming it in the README
without having used it is worse than not mentioning it.

### The AG Grid caveat applies to the whole plan

**Freeze features on 9 November.** Everything after that is video, README and buffer.

---

## Data, consent, privacy

Read `DATA_AND_PRIVACY.md`. In one line: **the shopper's data is the shopper's** — the engine is
fed only by what they type, what we originated ourselves, and their history with this merchant.
No credit bureau, no open banking, no cross-merchant profile, no data sold, no adverse action,
every verdict overridable.

---

## Claims used in this build — and where they come from

Only cite these with their sources:

| Claim | Figure | Source | Caveat to state |
|---|---|---|---|
| BNPL users who paid late in the past year | 47% (34%→41%→47%, 2024–26) | LendingTree, 2026 | Survey self-report |
| Say BNPL caused overspending | 68% | LendingTree, 2026 | Survey self-report |
| Hold multiple simultaneous BNPL loans | 63% (33% cross-lender) | CFPB, Jan 2025 | — |
| Triggered an overdraft or NSF fee | 11% | CFPB, Jan 2025 | — |
| Late fee incidence / average fee | 4.1% of loans / $9.99 | CFPB BNPL report, Dec 2025 | Report names PayPal |
| **Charge-off rate** | **1.83% (2023)** | CFPB, Dec 2025 | **Must be stated next to the late figures** |
| PayPal financial services share of transaction margin | >20%, growing double digits | Q3 2026 earnings call | — |

The last row of the first block is the integrity test: self-reported lateness (47%) and formal
charge-off (1.83%) measure different things. State both, then make the argument the data
supports — **the harm is small, repeated, badly-timed payments, not catastrophic default.**

---

## Licensing

MIT. See `LICENSE`. It must be visible in the repository's About panel, not merely present as a
file — 17% of the 549 repos in this field get that wrong.
