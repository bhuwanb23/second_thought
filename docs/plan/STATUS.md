# STATUS — 5 Nov 2026

*Written for you to work from, not to show a judge. Everything below was re-run or
re-read today; anything I could not verify says so.*

**Eight days to the deadline (Thu 12 Nov, 12:00 PT / 13 Nov 01:30 IST).**

---

## 1. The system in one paragraph

The product is a working, tested, offline-capable checkout engine with a real HTTP
interface, a live screen, and five PayPal call sites. **It has never spoken to PayPal and
never spoken to a model.** Everything money-shaped runs against a simulated gateway that
implements the same interface as the live one; the AI is a deterministic template reader
that stands in for a model behind the same interface. The swap is one environment
variable in each case. That is the whole risk in the project: the wiring is proven, the
*accounts* are not. Three credentials and one deploy turn this from a demonstration into
a submission.

---

## 2. The idea, and what is actually different about it

**At the moment a shopper is about to split a payment into four, ask a question nobody
else asks: is this good for this person?**

The engine projects the next 45 days of cash flow — their paydays against the bills they
already have — and returns one of three answers:

| Answer | What it means | What happens |
|---|---|---|
| **OFFER** | Every one of the four payments leaves them above their floor | Pay in four, today |
| **DEFER** | It works, but only if the first payment waits for a payday | A dated invoice for the payday. **The merchant ships when that invoice is paid.** |
| **DECLINE** | Not even that works | Named collision, and the largest amount that *would* work today |

The floor is `max(buffer% × monthly income, $50)` — not a credit score, not a limit, just
"don't let this week break you."

**Why it is not another BNPL app.** Three things, in order of how much they matter to a
judge:

1. **DEFER is pay-before-ship.** The merchant is never extending credit and never waiting
   on a receivable it funded. The shopper is never borrowing. Compare with a card decline,
   where a *good* customer is simply lost — here the merchant keeps the sale at a later
   date with no credit risk transferred to them. PayPal pays; the shopper benefits; the
   merchant embeds. *(Careful: say the trade, never "volume preserved" — we do not know that.)*
2. **The AI supplies facts, never the verdict.** The model's only job is reading a messy,
   unstructured month — "salary's 2,400 on the 15th, rent 1,375 on the 1st, car loan 312
   every second friday" — into dated amounts. `Agent.profile_from` raises rather than
   guess. The decision comes from deterministic arithmetic and is unit-tested to stay put
   even when the wording is nonsense. This is the answer to "did you just wrap an LLM?"
3. **It says no.** The DECLINE path is the pitch. A system that only ever says yes is an
   ad; this one hands a shopper a smaller number they can actually afford.

**Where it sits against the rules:** PayPal pays (Pay Later / Invoicing are the rails),
the merchant embeds (a checkout snippet), the shopper benefits. It is a checkout, not a
wallet, not a lender, not a budgeting app.

---

## 3. What runs today, right now, with no credentials

```bash
cd product

python3 -m secondthought.cli         # the whole engine in a terminal, three people, three answers
python3 demo.py --dry-run            # all five PayPal calls, on a fake transport, writes evidence
python3 demo_ai.py --offline         # messy text → DEFER → reservation → tampered approval REFUSED
python3 scripts/serve.py             # the web page on :8000 — open / in a browser
bash scripts/v5_two_jars.sh          # 22 live checks against a real socket: isolation, limits, tokens
python3 scripts/preflight_deploy.py  # 18 checks on root render.yaml
python3 -m unittest discover -s tests -q   # 154 tests, ~0.32 s
```

All seven are green as of today except the two that need the outside world (`demo.py
--live` exits 2 without credentials; `preflight_deploy.py` passes 18/18 offline).

The page is real and self-contained: three named months with amounts visible before any
click, answers rendered as sentences ("Pay on Sat 7 Nov — and it ships once you've paid"),
a free-text box that shows what it read and flags what it is unsure about, both honesty
badges, no external assets. A static copy is at `product/artifacts/screens/index.html`.

**Scale:** 7,672 lines across 52 Python files under `product/`, no file over 299 lines,
zero third-party dependencies, stdlib only, Python 3.11+.

---

## 4. Real vs simulated — the table a judge would want

This is the honest ledger. The right-hand column is what the next eight days are for.

| Component | Today | To become real | Who |
|---|---|---|---|
| Cash-flow engine, verdict rules, floor | ✅ **Real**, unit-tested, deterministic | — | done |
| PayPal Orders AUTHORIZE → capture | 🟡 Written, tested against a fake transport, **never run against PayPal** | run `demo.py --live` | needs 2 creds |
| PayPal AUTHORIZE → void | 🟡 same | same | needs 2 creds |
| Invoicing invoice dated by the engine's payday math | 🟡 same — 201, `INV2-…`, `payment_term.due_date` asserted offline | same | needs 2 creds |
| Idempotency (`PayPal-Request-Id` → one order) | 🟡 same | same | needs 2 creds |
| Webhook signature verification (RSA, stdlib) | ✅ **Real crypto**, verified over a live socket with a 400 on a missing header | needs one real PayPal transmission | needs webhook id after deploy |
| AI extraction | 🟡 `LLM-MOCK` — a template reader behind the model interface | `demo_ai.py --live` | needs 1 key |
| AI decision isolation (model cannot move the verdict) | ✅ **Real** and tested — the invariant holds whatever the model says | — | done |
| Sessions, rate limits, spend cap, token signing | ✅ **Real**, 22 checks over a live socket, per-session secrets | — | done |
| The public URL | 🔴 **Does not exist** | deploy to Render | needs an account |
| Version control for the workspace | 🟡 **Root git repo initialized** | Review and commit the consolidated tree | you |
| Human validation | 🔴 **n = 0** | 5 conversations, or accept n = 0 | only you |
| Outside-eye rehearsal | 🔴 **n = 0**, page is ready | one stranger, 30 minutes, 9–10 Nov | only you |

Two things that are *more* solid than they look: the security layer and the crypto. Both
were tested over real sockets rather than mocked, and the tampered-approval refusal is a
genuine HMAC rejection, not a scenario.

Two things that are *less* solid than they look: nothing has touched PayPal's servers, so
field names, error shapes and sandbox quirks are still theory until `--live` runs; and the
whole thing has been reviewed only by the person who built it.

---

## 5. The gate board

| Gate | Status | What closes it |
|---|---|---|
| **V0** preconditions (14 vars) | 🔴 4 failed | 3 credentials + a Render account |
| **V1** Pay Later sandbox probe | 🔴 not started | the PayPal creds; confirms the band from the response, never assumed |
| **V2** code correctness | ✅ 155 tests, preflight 18/18, mutation 14/3 | done |
| **V3** five live PayPal calls | 🔴 instrument ready, exits 2 | `PAYPAL_CLIENT_ID` + `PAYPAL_CLIENT_SECRET`, then `demo.py --live` |
| **V4** live AI | 🔴 safety half proven offline, quality half blocked | `LLM_API_KEY`, then `demo_ai.py --live` |
| **V5** session isolation & security | 🟢 22/22, one item pending deploy | a redeploy to prove it in production |
| **V6** deployment & durability | 🔴 no URL | deploy; item 6 (calendar, 1 + 10 Dec) is done |
| **V7** human validation | 🔴 closed at **n = 0** | 5 real BNPL users, or state n = 0 in the pitch |
| **V8** outside-eye rehearsal | 🟡 page, protocol and timer built; **n = 0** | one stranger + the URL, 9–10 Nov |

The critical path is **credentials → V3/V4 → deploy → V6 → record → submit.** Every other
row is either done or is yours.

---

## 6. Three things unblock almost everything

**a. The PayPal sandbox pair** — `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`.
Unblocks V0, V1, V3, and the money half of V6. This is the largest single jump in the
project's credibility: five artifacts a judge can find in the dashboard.

**b. An LLM key** — `LLM_API_KEY` (plus `LLM_MODEL`, `LLM_BASE_URL` if not OpenAI).
Unblocks V4's quality half and turns the on-screen badge from `LLM-MOCK` to `LLM` with a
real call behind it. The mandatory-AI-usage rule is the one rule that cannot be waived.

**c. A Render account, with the repo pushed.** Unblocks V5.6, all of V6, and V8 — and V8
is the only gate left that can tell us the pitch does not land before we record it.

Put them in `product/.env` (git-ignored, never committed) or in the Render dashboard. Then:

```bash
python3 scripts/v0_check.py           # the gate: if any row fails, stop
python3 demo.py --live                # V3 — expect artifacts/v3/<timestamp>/ + five dashboard locations
python3 demo_ai.py --live             # V4 — expect the badge to flip and three messy passages
```

If a command fails, that is a finding, not a setback — send me the output and I will fix
the code rather than the story.

---

## 7. Calendar

| Date | What |
|---|---|
| 5 Nov (today) | Status. Page exists. Waiting on three things above |
| 6–7 Nov | The moment creds land: V0 → V1 → V3 → V4, back to back |
| 8 Nov | Deploy; V5.6 and V6 cold checks; V7 conversations if any are running |
| **9–10 Nov** | **V8 rehearsal** — one stranger, the public URL, the repo, the README. Nothing else |
| 9–10 Nov | Script the video from the stuck points V8 produces, not from the pitch |
| **11 Nov** | Internal submit. Tag the commit. Freeze `main` |
| 12 Nov 12:00 PT | Deadline. No changes after |

Spare capacity, if any: the README's "how it works" section and the Devpost draft, both of
which exist and can be tightened.

---

## 8. Map of the workspace

| Path | What it is |
|---|---|
| `docs/research/` | 50 documents. Contest rules and dates, PayPal's intent, the field, the pain, the sandbox gotchas, and the C02 concept pack. This is where "sourced" lives |
| `docs/plan/plan.md` | The plan of record: fixed decisions, assumption register, phase map, contingency ladder, definition of done |
| `docs/plan/V0…V8` | One document per gate: what was checked, what the result was, what is blocked |
| `docs/plan/V7_human_validation.md` | n = 0, the two scripts, and the reason it cannot be delegated |
| `docs/plan/V8_outside_eye.md` | The protocol, the copy before/after, and what would make me mark it failed anyway |
| `docs/plan/SUBMISSION_KIT.md` | The Devpost fields, the pitch, the video beat sheet |
| `product/` | The real build. `secondthought/domain/` decides, `app/` orchestrates, `ai/` reads, `infra/` talks to PayPal, `interfaces/` is the outside |
| `product/secondthought/interfaces/screens.py` | The page a stranger sees — and `explain()`, the plain-language layer |
| `product/scripts/` | The instruments: V0 check, V5 two jars, V6 cold check, V7 capture/verdict, V8 observer, preflight |
| `product/` | **Canonical active build.** 154 tests, root Git repository |
| `archive/prototype/` | **Frozen reference.** Original prototype files and history bundle |

---

## 9. Weakest points, honestly

1. **Nothing has touched PayPal.** Field names, error envelopes and sandbox behaviour are
   still assumptions. `--live` will probably surface two or three schema mismatches. Budget
   an afternoon for that afternoon, not the deadline.
2. **No stranger has tried to use it.** We wrote the copy to be understood and we have not
   watched anyone try. That is a sentence in the pitch, not a footnote.
3. **n = 0 on users.** The claim we are allowed to make is "researched and built," never
   "validated." The pitch should say so out loud, early — a judge who finds it later
   stops believing the rest.
4. **The AI is a mock until a key lands.** If the key never lands, the honest options are:
   ship it clearly labelled as a mock (and accept the penalty on the mandatory-AI rule), or
   drop out. There is no third option that involves the word "simulated" being quiet.
5. **The 3-of-5 contradiction** between `VALIDATION_CONVERSATIONS.md` and
   `P2_five_conversations.md` is unresolved by design. If conversations do run, resolve it
   *before* the first one, not after.
6. **`product/` is not a git repo.** No history, no tag, no repo link for V8 or Devpost.
   Ten minutes of work, and it is on the critical path.

---

## 10. If time runs out, cut in this order

1. Human conversations (V7) → n = 0, stated plainly. Already the position.
2. The outside-eye rehearsal (V8) → write the copy carefully, say it was not tested.
3. The cold-start durability checks (V6 items 4–5) → note "undemonstrated," not "working."
4. **Never cut:** live PayPal calls, live AI, the DECLINE path, the badges, or the
   statement of what is not real. Those are the submission.

---

*Next action, whichever you can do first: push the repo to Render, or paste the three
credentials. Either one moves more than anything else I can do alone.*
