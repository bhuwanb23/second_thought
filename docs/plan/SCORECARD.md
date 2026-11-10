# Scorecard — where this actually stands, and what would make it win

*5 Nov 2026 (the workspace clock reads 10 Nov — see §9). Run `python3 product/scripts/scorecard.py`
to regenerate every number here. Nothing in this file is an opinion count; each line is
either a check that ran or a source that exists.*

---

## 1. How the score works

**Stage 1 — pass/fail, no score.** Two questions: does it fit the theme, and does it
*reasonably apply* the required APIs. A project that fails here is never scored.

**Stage 2 — five criteria, equally weighted.**

| Criterion | What is actually being asked |
|---|---|
| **Technological Implementation** | Is the PayPal and AI use thorough, skilful and *verifiable*, or is it a template with a logo? |
| **Design** | A complete, coherent product — not a technical proof of concept |
| **Potential Impact** | A specific problem, a real audience, and a demo that shows the solution working for them |
| **Innovation** | Novel, and not the same as the other entries |
| **Presentation** | Does the video show it working end to end, and explain who it is for |

**The tiebreak is Technological Implementation** — the first listed criterion. In a field
this size, ties are common, so when choosing between polish and depth, depth wins.

**Automated AI analysis is explicitly permitted.** The README and description get read by
a machine as well as a person, which is why the API names, the model and the endpoints are
written as literals rather than buried in prose.

---

## 2. The scorecard, right now

Anchors: 0 absent · 1 claimed only · 2 exists but unverifiable · 3 verifiable, one path ·
4 verifiable, multiple paths, visible depth · 5 what the top decile already does.

| Criterion | Now | After the 8-day plan | Why now is what it is |
|---|---|---|---|
| Technological Implementation | **1.7** | **4.5–5.0** | 165 tests, webhook crypto, idempotency, approval binding — all real, all verified against a *fake* transport. Zero PayPal calls. A judge cannot verify the integration, so by the anchors it is a 2. |
| Design | **4.0** | **5.0** | The screen is genuinely product-shaped: three months visible without a click, sentences instead of status codes, empty state, mobile, no external assets. It is not deployed, so nobody can see it. |
| Potential Impact | **4.1** | **4.5–5.0** | Sourced pain, a named audience, and a refusal that actually runs. The missing piece is that no human outside this room has used it: n = 0. |
| Innovation | **4.5** (script says 5.0 — discounted, self-scored) | **4.5–5.0** | The cluster is nearly empty: **3 entries** under `credit-bnpl` in a 549-repo scan, average depth 1.7/13. The inversion is memorable. |
| Presentation | **0.0** | **4.5** | Nothing recorded. Zero. This is the largest recoverable loss on the board. |
| **Mean** | **≈ 3.0** | **≈ 4.5** | |

**The honest sentence for today:** *a well-built product nobody can see, verified by
nobody, with no video.* Everything that is weak is weak for the same reason — nothing has
left this machine.

---

## 3. Stage 1 is the whole ballgame, and it is currently at risk

The pass/fail gate asks whether PayPal is *reasonably applied*. Today the answer a careful
judge would reach is: **the code is there, the proof is not.** `infra/paypal_live.py` is a
complete Orders v2 + Invoicing v2 adapter with server-side OAuth, but every artifact in
`artifacts/` is stamped `DRY RUN — fake transport` and every invoice id begins `INV2-SIM`.
A judge who opens the dashboard and searches for those ids finds nothing.

That is one command away from being resolved, and it is the highest-value two hours in the
project:

```bash
python3 demo.py --live        # five real calls, five ids a judge can look up
```

Until it runs, the honest self-description is "a working simulation of the integration",
and the rules are explicit that a mockup does not meet the requirement. **Fix this before
anything cosmetic.**

---

## 4. The field math

From the scan of 549 public repos (1 Nov) and the participant count:

| Number | What it means |
|---|---|
| **26,708** registered participants (2 Nov, reported) | Registrations, not submissions. A Devpost grand-prize hackathon typically converts a low single-digit to ~10% into submissions, so expect **hundreds to ~2,000** entries. Estimate, not a fact. |
| **230 / 549** repos have a live demo (42%) | A URL is table stakes, not a differentiator. |
| **95 / 549** have no detectable licence (17%) | A `LICENSE` file that GitHub detects is an eligibility item, and a chunk of the field fails it. |
| **7 / 549** score 10+ of 13 depth markers | That is the top 1.3% — the real bar for a prize, not the median. |
| **credit-bnpl: 3 entries, 1 live demo, depth 1.7** | Our cluster. Thin. Crowded clusters are mandate-guardrail (86), invoice-AR (60), reconciliation (51), dispute (49), shopping-agent (47). |

**Prizes on the table:** $12,000 / $8,000 / $5,000 overall, plus five **$5,000 honourable
mentions** — *Most Creative, Most Impactful, Best Demo Delivery, Best Use of PayPal + AI,
Best Use of Agentic Commerce* — plus sponsor prizes (AG Grid, APIMatic, Channel3 among
them; Render is a listed partner). Twenty cash positions.

That structure matters strategically. Three of those five mentions are within reach without
winning overall: **Most Impactful** (our strongest criterion), **Best Demo Delivery**, and
**Best Use of PayPal + AI**. Pick **Most Impactful** as the target and let the video serve
it — the impact case is the one thing here that no other cluster can copy quickly.

---

## 5. What the top decile does that we do not

Straight from the field scan, with our status:

| The bar | Us |
|---|---|
| CI badge and a passing suite advertised | ✅ 165 tests — **but no CI, and it is not in the repo yet** |
| Live demo, no login, no keys | ❌ no deploy |
| A `/proof` page listing every measured number | ❌ not built |
| A threat model (`SECURITY.md`) | ❌ not written |
| A red-team screen showing attacks blocked | 🟡 22 live checks exist, not shown anywhere a judge looks |
| Explicit "stays online until 15 Dec" | ❌ no URL to promise |
| Video recorded weeks early, 2:18–2:37 | ❌ nothing |

Six of seven missing. That is the gap between a good project and a scoring one, and all
six are mechanical.

---

## 6. Problems found — worst first

### Fixed today

1. **The demo was already broken, and would have stayed broken through judging.** The three
   demo months were pinned to November 2026 dates, and `/api/plan` passed a hardcoded
   `date(2026, 11, 1)`. On 10 November Ben's payday was in the past, so `/api/execute`
   raised `ReservationError` and returned **HTTP 500** — on the DEFER path, the hero of
   the pitch. In December, *every* persona would be stale and the demo a judge is required
   to be able to run would not run. Now the months are relative to today
   (`interfaces/personas.py`) and `tests/test_personas.py` walks sixty days forward
   asserting all three verdicts still appear. A lint fails the build if a literal 2026 date
   re-enters the demo path.
2. **`.env` was never read.** `.env.example` said "copy to `.env` and fill in" and only
   `v0_check.py` had a reader; the product, demos and server read the real environment
   only. Anyone following the instructions would set up credentials and be told they were
   missing. `config.py` now loads it — real environment wins, production ignores the file.
3. **`pay_on` was populated for OFFER**, telling an OFFER shopper to wait for a date that
   means nothing. Now only DEFER carries it.
4. **The README had no problem statement, no sources, no privacy line, no API names.**
   Judged on its own, it was a changelog. It now carries the 47% / 63% / 10,884 figures
   with sources, the endpoints by name, the refusal copy verbatim, and the data path.

### Open, in order of what they cost

| # | Problem | Cost | Fix |
|---|---|---|---|
| 5 | **No live PayPal calls** | Stage 1 risk; Tech capped at 2 | creds → `demo.py --live` |
| 6 | **No video** | 20% of the score, guaranteed to be watched | script after V8, record 10–11 Nov |
| 7 | **No deploy** | Design unverifiable, V6/V8 dead, "available until 15 Dec" unprovable | Render, 45 min |
| 8 | **No repo at all** — `product/` is not git | no repo link for the form, the tester, or the judges | `git init` + push, 15 min |
| 9 | **No `LICENSE`** | 17% of the field fails this; the checklist wants a licence chip | 2 min |
| 10 | **No AI key** | mandatory-AI rule has no fallback; badge reads `LLM-MOCK` | key → `demo_ai.py --live` |
| 11 | **No `/proof` page, no `SECURITY.md`** | the two cheapest top-decile markers we lack | 2 h total |
| 12 | **n = 0 on humans** (V7 and V8) | Impact capped at 4; the pitch must *say* n = 0 | conversations, or state it |
| 13 | **The 3-of-5 contradiction** between `VALIDATION_CONVERSATIONS.md` and `P2_five_conversations.md` | if conversations run, a post-hoc rule change looks like moving the goalposts | decide before the first one |
| 14 | **Deadline ambiguity** — sources disagree on **12:00 pm PT vs 2:00 pm PT** | two hours either way | re-read the live listing; plan for 12:00 |

---

## 7. The plan, ranked by points per hour

| Move | Hours | Criteria moved | Expected mean |
|---|---|---|---|
| **`demo.py --live`** — five real calls | 2 | Tech 1.7 → 3.5, Stage 1 saved | +0.4 |
| **Deploy + add `LICENSE` + `.gitignore` + push** | 1 | Design 4.0 → 5.0, eligibility | +0.3 |
| **`demo_ai.py --live`** — real model behind the badge | 1 | Tech → 4.5, the mandatory-AI rule | +0.2 |
| **Webhook id + one real transmission** | 0.5 | Tech → 5.0 | +0.1 |
| **`/proof` page** — every measured number, one URL | 1 | Tech, and it is a top-decile marker | +0.1 |
| **`SECURITY.md`** — threat model, six rows | 1 | Tech | +0.1 |
| **Video, 2:40**, built from V8's stuck points | 5 | Presentation 0 → 4.5 | **+0.9** |
| **V8 rehearsal** — one stranger, then fix the copy they tripped on | 1 | Design, Impact, and it writes the video | +0.2 |
| **V7 conversations** — five, or accept n = 0 | 8 | Impact 4.1 → 5.0 | +0.2 |

Two observations. **The video is worth more than everything technical that remains**, and
**the top three technical moves are all the same afternoon.** The 8-day plan is not
ambitious; it is two focused days and four days of things only you can do.

---

## 8. Three ways this loses anyway

1. **The safe path gets taken.** A lookalike entry — "AI shopping agent with a budget" —
   is in a cluster of 47 with average depth 2.3. Anything that reads as *responsible
   lending advice* will be scored as a lecture. The refusal must be shown as a feature
   with a number in it: *"$140 would work today"*. That sentence is the whole pitch.
2. **The claim outruns the evidence.** "Validated with users" with n = 0 is the fastest way
   to lose a judge who checks. Say "researched, built, and tested by us — we have not yet
   put it in front of users". Judges reward the honesty and it costs nothing.
3. **It is not there in December.** The requirement is availability until 15 Dec. Memory
   sessions, a sleeping free tier, or a stale demo data set each break it. The date bug
   fixed today was exactly this failure, found by luck.

**What a scorecard cannot promise:** a prize. 26,708 registered people, twenty cash
positions, and a judging panel that scores by impression. What it can say is that if
everything in §7 lands, this sits in the top decile *by the field's own depth markers* —
which is the only externally-measurable claim available. The rest is the video.

---

## 9. Daily ritual

```bash
cd product
python3 scripts/scorecard.py --url https://<app>.onrender.com   # the five criteria
python3 -m unittest discover -s tests -q                        # 165 and rising
python3 scripts/v0_check.py                                     # the credentials gate
```

Scores are written to `product/artifacts/scorecard/<timestamp>.json`, so the shape of the
week is visible instead of remembered. Anything that stays flat for two days is the thing
to work on next.

> **One caution on the clock:** the workspace clock reads **10 Nov 2026** while the plan
> has been counting from 5 Nov. Check `date` before scheduling anything with a deadline in
> it — if the 10th is right, the video is due in two days, not seven, and §7's order is
> still correct but the V7 conversations are no longer possible.
