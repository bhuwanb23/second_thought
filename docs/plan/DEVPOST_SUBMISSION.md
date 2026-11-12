# Devpost — submission copy, field by field

*Everything below is written to be pasted straight in. Anything in ⟨angle brackets⟩ is a
fact only you can supply — the repo URL, the deployed URL, the video link. Nothing else is
a placeholder.*

**Read §12 before you submit.** Two of those checks are the difference between an entry
that scores and an entry that gets skipped.

---

## 1. Project name

```
Second Thought
```

## 2. Elevator pitch (≤ 200 characters)

```
A checkout that says not yet. Our AI reads the shopper's month; if a plan would break it, PayPal invoices on payday instead — the shop keeps the sale on PayPal's rail and ships after payment.
```

*191 characters, including spaces — leaves 9. The second half used to say "skips the 5% lender fee".
It no longer does: read `JURY_10.md` §1 and §A.3 of `MARKET_AND_BENCHMARKS.md`, then never write that
sentence again. "On PayPal's rail" is the same truth with no target on your back.*

## 3. Built with (tags, max 25)

```
Python, PayPal, PayPal Orders API v2, PayPal Invoicing API, PayPal Webhooks, PayPal Sandbox,
OAuth 2.0, SQLite, AI, Large Language Models, OpenAI API, JSON Mode, HTML, CSS, JavaScript,
Render, GitHub, unittest
```

---

## 4. About the project

> Paste everything between the rules. The headings are the ones the form asks for.

---

## Inspiration

Every buy-now-pay-later checkout asks the same two questions: **how much**, and **what
country are you in**. Neither of them is "can you carry this".

That gap is not a secret. LendingTree found **47%** of BNPL users paid late at least once
in the past year, up from 34% two years earlier. The CFPB found **63%** of BNPL users
carrying several loans at once. And BNPL complaints in the CFPB database went from **7,412
in all of 2025** to **10,884 by November 2026** — with two months of the year still to run.

None of that says the product is bad. It says the decision is being made without
information the checkout already has. It knows the amount, the merchant, the device, the
time of day. It just doesn't know that rent comes out on the 28th.

Before writing code we scanned 549 public repos in this hackathon's field to see how many
people were answering that question. Under a "credit / BNPL" cluster we found **three**.

## What it does

Second Thought sits at the moment of the split and answers one question: *is this good for
this person, this week?* It projects the shopper's next 45 days — paydays against the bills
they already have — and returns one of three answers.

```
 shopper's month ──┐
                   ├──▶  45-day cash-flow projection  ──▶  the floor test  ──┬──▶ OFFER
 this purchase ────┘                                   (never below a       │    pay in four
                                                        safety floor)       ├──▶ DEFER
                                                                            │    invoice on payday,
                                                                            │    ship on payment
                                                                            └──▶ DECLINE
                                                                                 name it, quote a
                                                                                 smaller number
```

The floor is `max(10% of monthly income, $50)`. Not a credit score. Not a spending limit.
Just: don't let this week break you.

| Shopper | Their month | The answer | What actually happens |
|---|---|---|---|
| **Ada** | comfortable | **OFFER** | PayPal `AUTHORIZE` hold, funds reserved, valid 3 days |
| **Ben** | a car payment lands before payday | **DEFER** | An **invoice dated to his payday**, and the merchant **ships only after it clears** |
| **Cleo** | genuinely squeezed | **DECLINE** | Nothing offered. The collision is named, and the largest amount that *would* work is quoted |

The three screens, verbatim from the build:

> **Pay on Sat 15 Nov — and it ships once you've paid**
> Taking $249.00 today would leave you short before your next payday. Nothing is charged
> now, the price is held, and it goes out the door after your payment clears.

> **This one doesn't fit right now**
> Paying $249.00 today leaves you short — because the 4th payment on a plan you already
> have lands around Sun 22 Dec. **Up to $140.00 would work today.**

That second one is the product. A checkout that only ever says yes is an advertisement.

**DEFER is the part worth arguing about.** The merchant extends no credit and waits on no
receivable — PayPal pays, the shopper never borrows, and the goods ship when the money
arrives. Compare that with a card decline, where a good customer is simply lost. Here the
sale moves to a date the shopper can actually meet. That is the trade, and it is the whole
idea: *volume is not preserved, timing is*.

## How we built it

Four layers, no third-party dependencies, Python standard library only. Every file under
300 lines, because a judge has ten minutes and we would rather they could read it.

```
secondthought/
├── domain/      the verdict rules and the cash-flow projection — pure, deterministic, no I/O
├── app/         checkout orchestration, the reservation lifecycle, approvals, ports
├── ai/          the model reader, the template fallback, the agent that fuses them
├── infra/       PayPal adapter, simulated gateway, SQLite, RSA, webhooks
└── interfaces/  the HTTP layer, sessions, badges, and the one page a shopper sees
```

**PayPal side.** Server-side OAuth 2 client credentials, then Orders v2 (`AUTHORIZE`,
capture, void) for OFFER, and Invoicing v2 for DEFER — the invoice's `payment_term.due_date`
is computed by the same payday arithmetic that produced the verdict, not typed in. Webhook
signatures are verified with RSA-SHA256 PKCS#1 v1.5 implemented against the standard
library, over the raw request bytes. Every order and invoice carries a `PayPal-Request-Id`
so a retry is never a second charge.

**AI side.** An OpenAI-compatible chat endpoint reads free text — *"salary's 2,400 on the
15th, rent's 1,375 on the 1st, car loan 312 every second friday"* — into dated amounts, at
`temperature: 0`, JSON mode on. The design rule is a hard boundary:

> **The model supplies facts. The engine supplies the verdict.**
> There is no code path from a model output to a decision. `Agent.profile_from` raises
> rather than pass a low-grade extraction into the engine.

Anything the reader can't resolve is **flagged, not guessed** — an inferred date gets a
confidence cap and a question back to the shopper. Nonsense input degrades the answer to
`partial` or `demo`; it never crashes and never invents a judgement.

**Safety.** Money moves only through a single-use HMAC approval token bound to the exact
tool and arguments, so an edited amount or a replayed token is refused before any gateway
call. Sessions live in memory, one per visitor, each with its own signing key. Rate limits
are two-key (per session, per IP) and there is a call budget on the model. And the product
tells the truth about itself: the badge reads `AI · LLM-MOCK` and `PAYMENTS · SIMULATED`
until real credentials are loaded, because a demo that hides which mode it is in is the
failure this design exists to prevent.

**173 tests, 0.7 seconds, no network.** They include the things we would want a judge to
try to break: you cannot ship before payment, nothing moves without a human approval, an
approval cannot be replayed or re-pointed, a retried webhook is harmless, and one visitor
cannot spend another visitor's budget.

## Challenges we ran into

**The sandbox can't give you a real Pay Later plan.** Eligibility is decided client-side
from the amount and the buyer's country, which means you cannot reliably originate a
genuine four-instalment plan as a merchant. So we stopped trying to stage one and moved the
mechanic onto primitives we control end to end: an `AUTHORIZE` hold for today, an Invoicing
invoice dated to a payday for later. That turned out to be the better architecture anyway —
"pay before ship" is a stronger promise than "borrow from us".

**The demo broke by itself, and that was the best bug.** Our three demo months were pinned
to November 2026 dates. Nothing in the code changed, but the calendar moved: Ben's payday
passed, the reservation refused a date in the past, and the DEFER path — the hero of the
pitch — started returning HTTP 500. Judging runs 1–15 December, when every one of those
dates would be stale. The months are now generated relative to today, and a test walks
sixty days forward asserting all three verdicts still appear. There is also a lint that
fails the build if a literal date ever comes back into the demo path.

**Money, twice.** Dollars versus minor units is a hundred-fold error waiting to happen, so
every amount in the system is an integer of cents and there is exactly one place that
converts. Payday arithmetic was the other one: a fortnightly cadence with no anchor date
must not borrow today's date at high confidence, so it caps the confidence and asks.

**Webhook verification with no dependencies.** The signed string is
`transmissionId|transmissionTime|webhookId|crc32(rawBody)` over the *raw* bytes, and getting
any part of that wrong fails closed with no useful error. Ours fails closed too, and says
which of the four parts was missing.

## Accomplishments that we're proud of

**The promise is enforced in code, not in a paragraph.** `fulfil()` raises unless the
reservation is `PAID`. There is no method that lets a caller skip the payment state, so a
merchant integrating this cannot accidentally ship into unpaid credit.

**The refusal has a number in it.** "Up to $140.00 would work today" is warmer and more
useful than "declined", and it is the line that took the longest to get right.

**A model that is not allowed to decide anything.** Reading a messy month correctly and
then having no vote in the outcome is the least fashionable use of an LLM here, and the
reason we trust the thing at all.

**A demo that will still work in December** — including on a laptop with no network, since
the page carries no external assets.

**And one thing we are not proud of, but will say:** we have not put this in front of real
BNPL users yet. This was researched, built, and tested by us — 173 tests, and a stranger-free
demo. The conversations are scheduled, not done. We would rather write that here than have
someone find it out later.

## What we learned

**The payment is not the decision.** By the time money moves, the interesting judgement has
already happened. Most of the engineering here went into the second before the first
request.

**Deterministic money, fluent language.** An LLM is excellent at turning a human sentence
into structured facts, and a bad instrument for deciding whether someone can afford
something. Keeping those two jobs apart made both easier.

**Fake transports beat mocks.** Our simulated PayPal gateway implements the same protocol
as the live adapter, same shapes, same failure modes. Every bug it caught offline was a bug
that would otherwise have surfaced in front of a judge.

**Nobody reads status codes.** The first version of the screen said `DEFER`. A person
reading it does not know what that means. "Pay on Sat 15 Nov, and it ships once you've
paid" is the same fact, and it is a product.

## What's next for Second Thought

**Real users, this month.** Five conversations with people who actually use BNPL, written
up as they happen rather than afterwards. If the answer is that the refusal reads as a
lecture, we want to hear it from them and not from a judge.

**A merchant view.** The engine already knows what was deferred and what came back. A
merchant wants one number: how much of my month moved instead of dying.

**Close the loop on the real plan.** Once we can originate a genuine Pay Later plan in
sandbox, OFFER becomes a native PayPal plan rather than an authorisation hold, and the
verdict drives PayPal's own instalment product.

**Twelve weeks of dates.** A payday model that has never seen a holiday-shifted payday is
half a model. This one is honest about that: when it doesn't know, it says so and asks.

---

## 5. How the project meets the main technology requirement

```
PayPal developer platform (sandbox) — what each piece does:

• OAuth 2 client credentials — POST /v1/oauth2/token. Server-side only; no client
  secret ever reaches the browser. Every PayPal call below is made with that token.

• Orders v2 — POST /v2/checkout/orders with intent AUTHORIZE, then
  POST /v2/payments/authorizations/{id}/capture or .../void.
  This is what an OFFER becomes: funds are reserved for a fixed window, captured on
  the approved date, or released.

• Invoicing v2 — POST /v2/invoicing/invoices, then send.
  This is what a DEFER becomes. detail.payment_term.due_date is set to the shopper's
  next payday, computed by the same engine that produced the verdict. The merchant
  ships when INVOICING.INVOICE.PAID arrives.

• Webhooks — the endpoint verifies PAYPAL-TRANSMISSION-ID / -TIME / -SIG and the
  webhook id by recomputing a CRC32 of the raw body and checking an RSA-SHA256
  signature against PayPal's certificate. Unverified calls are rejected with 400 and
  never reach the money paths.

• PayPal-Request-Id — sent on order and invoice creation so a retried call cannot
  create a second charge.

AI tool — an OpenAI-compatible chat completions endpoint (model configured by
environment, temperature 0, response_format json_object). Its only job is reading a
shopper's unstructured description of their month into dated amounts with a confidence
per field. It does not decide, rank, or approve anything: the verdict comes from
deterministic arithmetic in domain/engine.py, and the agent raises rather than pass a
low-confidence extraction into it. A template-based fallback runs when no key is
configured, and the on-screen badge says which mode is active.

Everything runs against the PayPal sandbox. The live adapter raises before its first call
if PAYPAL_ENV is anything but sandbox, so a misconfigured deploy fails loudly instead of
moving real money.
```

## 6. Additional sponsor tools

**Render** — the app is deployed on Render from a `render.yaml` blueprint at
`https://second-thought-h61b.onrender.com`. It currently uses the free plan and may sleep after
15 minutes of inactivity; upgrade to Starter before submission if continuous availability is
required. Secrets are set in the dashboard rather than in the repository. No other sponsor tool is used; the remaining
options were not part of the build and we would rather leave them blank than claim them.

## 6b. Assets and the thumbnail

Everything is in `product/assets/` — SVG source, PNG raster, one palette.

| Upload / paste | File |
|---|---|
| **Devpost thumbnail** | `product/assets/png/devpost-thumbnail.png` (1280×720) |
| Repo logo (GitHub social preview, 1280×640) | `product/assets/png/og-card.png` (1200×630, it will crop) |
| Story illustrations, in this order | `diagram-flow.png` → `diagram-verdicts.png` → `diagram-defer.png` → `diagram-ai-boundary.png` → `diagram-gate.png` |
| Video title card | `logo-mono-white.png` on `#14181f` |
| Video lower third / end card | `logo-primary.png` |
| Innovation beat | `diagram-clusters.png` — the 3-entry bar is the whole argument, in one picture |

Open `product/assets/index.html` to see all seventeen at once.

Two notes. The thumbnail is the only image most judges will see before deciding whether to
click, so it leads with the claim, not the logo — *"a checkout that sometimes says not yet"*
in three lines, with the three verdicts stacked on the right. And **no PayPal logo, wordmark
or trade dress appears in any of these**; the brand is ours and the only reference to PayPal
is the word, in body copy.

## 7. Public code repository

```
⟨https://github.com/<you>/second-thought⟩
```

*Before pasting this, make sure: it is public, GitHub shows a licence chip in the About
box, and the README renders the sections a judge reads first (what it does, PayPal APIs by
name, AI tools by name, how to run it, tests, privacy). See §12.*

## 8. Working demo / hosted application

```
https://second-thought-h61b.onrender.com
```

*No login, no keys, no signup. This is a Render free service, so it may sleep after inactivity;
open it once before judging to wake it. Upgrade to Starter if continuous availability is required.*

## 9. Testing instructions for judges

```
Open the link. There is no login and nothing to install.

1. The first screen shows three months, with the amounts visible before you click
   anything: Ada (comfortable), Ben (a car payment lands before payday), Cleo
   (genuinely squeezed). Click each one. You should get three different answers in
   about a second: OFFER, DEFER, DECLINE.
2. DEFER is the one that matters. Ben's answer names the day he should pay and says
   the item ships only after the money arrives. Nothing is charged today.
3. DECLINE is the other one worth your time. Cleo is told what collides, and the
   largest amount that would fit today.
4. Type your own month into the box at the bottom — for example
   "salary 2400 on the 15th, rent 1375 on the 1st, car loan 312 every second friday"
   — and press "Read this". It shows what it read and flags anything it was unsure
   about. It deliberately decides nothing from free text: the verdict still comes
   from the fixed months and from deterministic code.
5. The badges at the top say exactly which mode is live (AI · LLM vs LLM-MOCK,
   PAYMENTS · SANDBOX vs SIMULATED). We would rather you know than guess.

Money is simulated. All PayPal calls run against the sandbox with test accounts; no
real account, no real money, no live credentials.

To run it locally:
  git clone <repo> && cd second-thought/product
  python3 scripts/serve.py            # http://localhost:8000
  python3 -m unittest discover -s tests -q      # 173 tests, ~0.7s, no network

Sandbox PayPal credentials are optional for browsing the demo — without them the app
runs the same code path against a simulated gateway and says so on the badge.
```

## 10. Overall experience integrating PayPal

**Rating: 8 / 10**

```
The parts that are genuinely good: the Orders v2 and Invoicing v2 APIs are consistent,
the sandbox behaves like production, and the OAuth flow is a two-line curl. Invoicing in
particular is underrated — getting an invoice with a due date we computed, sent to a real
sandbox recipient, with a payment link we could hand to a human, took an afternoon.

Where it costs time:

1. Pay Later eligibility is decided client-side from the amount and the buyer's country,
   so as a merchant you cannot reliably originate a genuine four-instalment plan in
   sandbox. That pushed us onto AUTHORIZE + Invoicing. It ended up better for the product,
   but it is the kind of thing you only discover by trying.

2. Several v2 endpoints return 204 No Content by default (void, capture, authorize). The
   answer is `Prefer: return=representation`, and it is easy to spend an hour wondering
   why a successful call returns nothing.

3. The OAuth token endpoint answers form-encoded, not JSON, which breaks naive clients.

4. Invoices are created as DRAFT and do nothing until sent. Correct, and initially
   surprising.

5. Webhook signature verification has a lot of moving parts — four fields, a CRC32 over
   the raw body, and a certificate fetched from a URL inside the event. It fails closed
   with no explanation when one piece is wrong. A reference implementation in each SDK
   would save everyone this afternoon.

None of this is a complaint about the platform. It is the tax on any system that moves
money, and the sandbox is the right place to pay it.
```

## 11. Remaining fields

**Open to being contacted for feedback:** **Yes**

**APIMatic / AG Grid experience fields:** leave blank. We did not use them, and an empty
field is better than a fabricated one.

**Which AI tools have you leveraged while working on this project?**

```
In the product: a large language model behind an OpenAI-compatible chat completions
endpoint (temperature 0, JSON mode) reads the shopper's description of their month into
dated amounts, with per-field confidence. A deterministic template reader is the fallback
when no key is configured, and the on-screen badge reports which of the two is running.

While building: an AI coding assistant for review passes, test scaffolding, and editing
documentation — used the way a linter is used, with every suggestion read before it went
in. The verdict arithmetic, the approval model and the PayPal adapter were written and
reviewed by hand, because they are the parts we would have to defend.
```

**Level of learning derived from the project:** **Significant**

**Did you gain AI value you can use in your career?** *(if it asks for text)*

```
Yes, and it is a narrower kind of value than the hype suggests.

The useful lesson was learning where a model belongs and where it does not. Ours reads a
messy human sentence into structured facts better than any regex I could have written, and
that saved days. It is also completely unfit to decide whether someone can afford a
purchase, and building the boundary — the model proposes, deterministic code decides —
changed how I think about every "AI feature" I will build afterwards.

Second: the failure modes are the work. Low confidence, missing fields, contradictory
dates, text that is not a month at all. A model that is right 90% of the time needs a
design for the other 10% before it is a product.
```

---

## 12. Before you hit submit — five checks

1. **The repo exists, is public, and shows a licence chip.** GitHub must *detect* the
   licence in the About box. 17% of the repos in this field fail this, and the requirement
   is explicit. `product/` is not even a git repository yet.
2. **The demo URL answers cold, logged out, in under three seconds.** Same for a judge on
   1 December, which means a paid instance that does not sleep.
3. **No secret is in the tree.** `.env` is gitignored; check `git log -p` for a
   `PAYPAL_CLIENT_SECRET` before you push, not after.
4. **The video is public, under 3:00, and shows the DECLINE case.** The refusal is the
   pitch. A video that only shows an offer is a video of a different, more common product.
5. **Nothing in this copy outruns the repo.** Three sentences to re-read after the live
   runs: the badges, the "173 tests" number, and the paragraph that says we have not
   tested with users. If a number changes, change it here too — a judge who finds one
   overstatement stops believing the rest, and we have a genuinely good story without one.
