# V4 — Live AI

**Status:** 🔴 **BLOCKED at V0.3. No `LLM_API_KEY`.** Instrument built; the safety half of V4 is proven, the quality half is not.
**Pass:** the model handles input it wasn't written for without producing a wrong **verdict** — wording may be rough, the engine's decision must not move.

---

## 1. What is blocked and what is not

Four questions, and they do not have the same answer:

| # | Question | Answerable without a key? |
|---|---|---|
| 1 | Badge reads `AI · LLM`, not `LLM-MOCK`, with the key set | **No.** By definition. Without a key the badge correctly reads `AI · LLM-MOCK`, which is the honest result, not a pass |
| 2 | Three messy passages go through the reader | **Partly.** The template reader runs on them for real; the model reader cannot |
| 3 | Low confidence flagged; nonsense degrades to `partial`/`demo` | **Yes, fully.** This is validation logic, not model behaviour |
| 4 | extract → decide → propose → approve → invoice, tampered approval refused | **Yes, fully.** The whole path runs, and the tamper is a real HMAC check |

So V4 splits cleanly. **Question 3 and 4 are the ones that protect a shopper; question 1 and the model half of 2 are the ones that impress a judge.** The second pair needs the key. The first pair does not, and it is now done.

---

## 2. The invariant, stated once

> The model supplies **facts**. The engine supplies **the verdict**. There is no code path from one to the other.

Enforced structurally, not by prompt:

| Layer | File | What it is allowed to do |
|---|---|---|
| Reader | `ai/extract.py`, `ai/template.py` | Produce dated facts, each with a confidence. **No verdict field exists in its output schema** |
| Validator | `ai/extract.py::_validate` | Drop anything out of band and **name** it. Never coerce |
| Engine | `domain/engine.py` | The only thing that produces `OFFER` / `DEFER` / `DECLINE` |
| Agent | `ai/agent.py` | Hands the engine's verdict to the model to *phrase*, and discards any verdict the model hands back |
| Approval | `app/approvals.py` | HMAC over tool + exact args. A tampered amount cannot be spent |

The agent's `explain()` is the only place a model output touches the answer. It is given the verdict as an **input it may not return**, and every disagreement is recorded in `ignored_model_verdicts` rather than resolved.

---

## 3. The three passages — what the reader actually does

Run on 2 Nov 2026, `python3 demo_ai.py --offline`, template reader:

**Passage 1 — the messy one.** *"rent's 1450 on the 28th, car loan 312 every second friday, oh and mum's meds ~40 a month"*

```
⚠ quality=partial  facts=3  low=2
  obligation rent's            1,450.00  2026-11-28  once         conf=0.90
  obligation car loan friday     312.00  2026-11-06  fortnightly  conf=0.45  ← ASK
  obligation mum's meds           40.00  2026-12-02  monthly      conf=0.50  ← ASK
  question   "car loan" was inferred from a fortnightly Friday cadence — which Friday anchors it?
  question   "mum's meds" repeats monthly but no day of the month was given
  question   "mum's meds" is approximate — confirm the exact amount
  question   No income or payday was mentioned
```

Both inferred items are flagged, not trusted. The fourth question is the one that matters most: **the passage names no income, so the product cannot judge what fits — it can only see money going out.** Any verdict from this input alone would be a guess, so the quality grade is capped at `partial` whenever no payday was found.

**Passage 2 — no amounts at all.** *"things have been tight since the shop cut my hours…"*

```
✗ quality=demo  facts=0
→ verdict: NO_DECISION — nothing is decided, nothing moves
```

Not a crash, not a hallucinated verdict. A named refusal with a question attached. `Agent.profile_from()` raises on a `demo` extraction, so the engine is never even asked.

**Passage 3 — different phrasing.** *"Salary lands on the 15th, 2,400 a month. Rent is due the 1st and it's 1,375. Gym comes out automatically, twenty nine dollars, on the 3rd."*

```
⚠ quality=partial  facts=2  low=0  dropped=1
  payday     salary   2,400.00  2026-11-15  monthly  conf=0.90
  obligation rent     1,375.00  2026-12-01  once     conf=0.90
  DROPPED    gym — a date with no amount I can read
```

**A real finding, kept rather than smoothed over:** the template cannot read *"twenty nine dollars"*. It sees the date and no amount, so it records the miss. A model reads that sentence easily. **That gap is exactly why the badge exists** — and it is the honest argument for the model being in the product rather than a decoration.

The clause-splitting had to learn one thing to get here: *"Salary lands on the 15th, 2,400 a month"* is one thought split by a comma. The day is carried forward into the half that has the number. Without that, the salary loses its date and the rent loses its label.

---

## 4. The tool call, end to end

```
text         “Salary's 2,400 on the 15th, rent's 1,375 on the 1st, car loan 312 every second friday”
extraction   ⚠ quality=partial  facts=3  low=1
decide_purchase → DEFER  reason=fits_on_payday  instrument=DEFER_TO_PAYDAY
proposes     create_reservation  249.00  due 2026-11-15
approval     required — token 156a259d947b…
tamper       amount 24900 → 74900: REFUSED  "this approval does not match these arguments"
approved     state=RESERVED  invoice=INV2-SIM… due 2026-11-15
```

`$600` opening balance is what makes this a DEFER rather than an OFFER — at `$300` the same text is a DECLINE, at `$900` an OFFER. The verdict moves with the calendar and only with the calendar.

### One deviation, declared

V4 calls the invoice tool **`create_scheduled_invoice`**. The signed action in the product is **`create_reservation`**, and the two are the same call.

The reason is that an invoice on its own holds nothing: it is a request for money, not a claim on the item. The reservation is what makes `fulfil()` refuse until the state is `PAID` — the pay-before-ship guarantee lives in the reservation, and it creates the `INV2-…` on the way through. Two names for one action would also mean two HMAC-signed tools for one capability, which is the thing the approval gate exists to prevent. The name with the guarantee in it wins.

---

## 5. What is proven by tests, not by demonstration

**49 new tests** (`tests/test_ai.py`, `tests/test_ai_pipeline.py`). Total 79.

The model in these tests is *hostile*, because "the model is well behaved" is not a guarantee:

| Test | What a bad model tries | Result |
|---|---|---|
| `test_a_model_supplied_verdict_is_dropped_and_named` | returns `{"verdict": "OFFER"}` | dropped, reason names the engine as the decider |
| `test_the_engine_verdict_differs_from_the_one_the_model_asked_for` | insists on OFFER while the calendar says no | engine returns **DECLINE**; the claim never surfaces |
| `test_a_model_that_changes_its_mind_in_the_wording_changes_nothing` | explainer returns OFFER for a DEFER | verdict unchanged, disagreement logged |
| `test_an_invented_amount_of_the_wrong_type_is_dropped` | `"lots"`, `-31200` | both dropped, one survivor, quality → partial |
| `test_an_unparseable_date_is_dropped_not_guessed` | `"the 28th"` | dropped, quality → demo |
| `test_a_field_with_no_confidence_counts_as_zero_confidence` | omits confidence entirely | treated as **0.0**, flagged. Silence ≠ certainty |
| `test_a_millions_of_dollars_typo_is_out_of_band` | `999000000` | dropped as out of band |
| `test_a_model_returning_prose_instead_of_json_degrades_to_demo` | returns a friendly sentence | `demo`, no crash |
| `test_a_profile_cannot_be_built_from_a_demo_extraction` | — | raises before the engine is asked |
| `test_when_the_model_fails_the_fallback_says_so` | 401 from the provider | template fallback, labelled as such |
| `test_the_daily_budget_stops_rather_than_overspends` | third call over a budget of 2 | raises, does not continue silently |
| `test_a_tampered_amount_is_refused` | +$500 on the approved amount | `ApprovalError` |
| `test_a_tampered_due_date_is_refused` | due date moved to 2027 | `ApprovalError` |
| `test_a_token_for_one_tool_cannot_be_used_for_another` | replayed as `authorise_hold` | `ApprovalError` |
| `test_nothing_moves_before_approval` | — | gateway call list is empty until approval |

---

## 6. What only the key can answer

| Unknown | Why it matters | If it fails |
|---|---|---|
| Does the model return valid JSON on unfamiliar text? | The whole reader depends on `response_format: json_object` holding | The validation layer already covers it: `demo`, no verdict, a question to the user. Degrades, does not break |
| Does it invent plausible amounts? | This is the real risk, and no amount of offline testing touches it | `confidence` and `_validate` catch type and band errors, not plausible lies. **This is the one to watch in the live run** |
| Does it find the fortnightly cadence and leave the anchor ambiguous? | The honest answer is "which Friday?" | The prompt requires ≤ 0.5 confidence and a `needs_confirmation` entry |
| Wording quality | Presentation criterion | Cosmetic; the verdict is unaffected by construction |

**The line to hold in the live run:** if the model produces a *plausible* wrong amount — right shape, wrong number — the validators will not catch it. Only the confidence flag and the user's confirmation stand between that and a bad calendar. That is why `answer_quality: partial` is surfaced in the UI rather than buried.

---

## 7. Run it

```bash
cd product
python3 demo_ai.py --offline                 # template reader + adversarial models
export LLM_API_KEY=... LLM_MODEL=gpt-4o-mini
python3 demo_ai.py --live                    # badge must read AI · LLM
python3 scripts/v0_check.py                  # V0.3 and V0.4 green
```

`--live` exits with code 2 rather than pretending if the key is missing: the badge is never allowed to be staged.
