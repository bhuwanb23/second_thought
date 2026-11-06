# START HERE

> ## 🔒 LOCKED — 1 November 2026
> The concept is frozen. See **`docs/plan/LOCK.md`**.
> Only two pre-committed tripwires can change anything: the **Pay Later probe** (run first — changes
> only how the OFFER branch is worded) and the **five conversations** (2–4 Nov, decision rules
> already written, not to be reinterpreted). Everything else is execution.
>
> **The plan is now structured:** → **[`docs/plan/plan.md`](docs/plan/plan.md)** (master, 8 phases)
> · research in [`docs/research/`](docs/research/) · active code in [`product/`](product/)

Two minutes. Then go build.

---

## Where you are

Ten days out from a hackathon where our scan found **549 public repositories** (registrants, not submissions — internal context only), and the best of them ship CI pipelines, threat models and recorded videos. The grand prize is $12,000; there are 23 prize slots worth roughly $100,000 in total.

You need to make **one decision** — what to build — and then eleven days of execution.

---

## Read these four files, in this order

| # | File | Why | Time |
|---|---|---|---|
| 1 | `docs/research/03_field/TEARDOWNS.md` | The single most decision-changing file. Shows how good the top of the field already is. | 6 min |
| 2 | `docs/research/02_intent/WHAT_THEY_WANT.md` | What PayPal admits is broken — the openings. | 4 min |
| 3 | `docs/research/07_concepts/EV_RANKING.md` | 24 concepts scored, 3 survivors, one recommendation. | 5 min |
| 4 | the one-pager for whichever concept you lean toward | `C01.md` / `C02.md` / `C06.md` | 5 min |

---

## The recommendation

> ### C02 — Second Thought  ✅ DECIDED
> **"The checkout that tells you the truth about your next four weeks."**
>
> Every BNPL tool is built to increase instalment take-up. This one decides whether an
> instalment is good for the person standing at the checkout — and is willing to say no,
> then route the sale to an instrument that actually fits.

**Validated and built.** Spec: `docs/research/07_concepts/C02_PRD.md`. Validation: `docs/research/07_concepts/C02_VALIDATION_REPORT.md`.
Canonical application (**154 tests passing**): [`product/`](product/).
Configuration template: [`product/.env.example`](product/.env.example).

**Read the idea itself: `docs/research/07_concepts/C02_THE_IDEA.md`** — customer, data provenance and the
pay-before-ship DEFER rule, all resolved.

**Then run `docs/research/07_concepts/VALIDATION_CONVERSATIONS.md`** — five 12-minute conversations. It is the
only way "validated" becomes a true word before 11 Nov.

**What remains is not building.** In order:

1. Run `product/PAYLATER_SANDBOX_TEST.md` — it decides how you word the OFFER branch.
2. Set `PAYPAL_CLIENT_ID`/`SECRET` and run `demo.py --live`.
3. Set `LLM_API_KEY` so the AI badge reads `LLM`, not `LLM-MOCK`, when a judge looks.
4. Deploy (Render starter, *not* free) and verify `/healthz` on 1 Dec.
5. Record the video by 10 Nov using `docs/plan/SUBMISSION_KIT.md`; submit by 11 Nov.

**The AG Grid call is 5 Nov. Decide and write it down. Do not rewrite the prototype.**

**Why it beats the alternatives:**

| | C02 | C01 | C06 |
|---|---|---|---|
| EV score | 64.5 | **68.3** | 48.6 |
| Competitors in cluster | **3** | 2 | **1** |
| Intent fit | **5** | 5 | 3 |
| Derivative risk | **none** | **high** | none |
| Feasibility in 10 days | **4** | 4 | 3 |
| Honest odds of a top-3 finish | **best** | good | risky |

C01 scores higher on paper but is a smaller version of a product PayPal's CTO demoed on 10 Aug 2026. C06 has the best story but the hardest demo and the weakest strategic fit.

**C02 has the best evidence (47% of BNPL users paid late; 63% stack loans), a named-in-public growth priority, an almost empty field, and a demo moment nobody else has — an agent that declines to sell.**

---

## Then do exactly this

1. **Today:** read the four files and the architecture overview.
2. **Run locally:** `cd product && python3 -m unittest discover -s tests -q`.
3. **Deploy from:** `product/render.yaml` using `python3 scripts/serve.py`.
4. **Follow `docs/plan/archive/BUILD_PLAN.md`** backwards from a recorded video on 10 Nov.
5. **Take the easy money:** AG Grid ($10,000, 5 slots) and APIMatic (3 slots, under an hour). See `docs/research/06_sponsors/SPONSOR_STRATEGY.md`.
6. **Walk the gates** in `docs/plan/GATES_AND_REDTEAM.md`. A failed gate means falling back, not pushing on.

---

## The five things that will actually determine your score

1. **A sentence a judge can repeat.** Same wording in the README, the video and the description.
2. **One sharp failure moment in the demo** — a declined authorization, a blocked oversized payment, a rejected webhook signature. It proves the build isn't a mockup.
3. **An explicit statement of what the model is not allowed to decide.** Every strong entry in the field does this.
4. **A test suite pasted into the README.** Technological Implementation is the first-ranked criterion and the tiebreaker.
5. **A demo that is still alive on 14 December.** The requirement runs to 15 Dec; free-tier sleeping dynos have cost people real placements.

---

## If you read nothing else

An unsourceable number is worse than no number. Every claim in the submission must trace to a file in this library — check the `evidence_strength` column in `docs/research/04_pain/PAIN_LEDGER.csv` before presenting anything as fact.
