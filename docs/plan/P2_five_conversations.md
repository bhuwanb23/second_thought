# P2 — Tripwire 2: five conversations

**Status:** ⬜ **not started**
**Owner:** you · **Window:** 2–4 Nov, **in parallel with building** · **Hours:** 1.5
**Exit condition:** the table has rows; the pre-written decision rules are applied as written; the claim wording is updated

---

## Purpose

The only thing that can change the idea. Five people, twelve minutes each, across three evenings.

The claim at stake: today the evidence is **secondary** — surveys, CFPB data, complaint threads.
That is *research*. This phase either earns **"tested with five shoppers"** or fails to.

**It is "five shoppers". Not "validated".** Five people is directional, and calling it validation is exactly the
overstatement that [DECISION_LOG §D6](DECISION_LOG.md) exists to prevent.

Script and rules: [../research/07_concepts/VALIDATION_CONVERSATIONS.md](../research/07_concepts/VALIDATION_CONVERSATIONS.md)

---

## P2.1 — Recruit (evening of 2 Nov, 20 min)

Five people who have **actually used Pay Later / Pay in 4 / Klarna / Afterpay** in the last year —
**ideally in a US-market context**, because the statistics, the CFPB data and the sandbox behaviour all
describe that market. A conversation with someone who has never used BNPL tests nothing.

**Not** product people, and not people who will be kind to you. A message that works:

> "Can I ask you 12 minutes of questions about splitting payments? I'm not selling anything and I
> won't pitch you — I need to know if a problem I'm working on is real or if I made it up."

That last clause buys you honesty.

---

## P2.2 — Run them (12 min each)

Follow the script in order. **Do not describe the product first.** Rule zero: the moment you pitch,
you are measuring politeness.

| Step | Time | The one thing being tested |
|---|---|---|
| 1. The last time | 3 min | Does a timing problem get recalled **unprompted**? |
| 2. The explanation gap | 2 min | The "blacklisted with no reason" pattern |
| 3. The cold-start test | 3 min | Would they actually set up a payday profile? |
| 4. The two mechanics | 3 min | Is the decline helpful or patronising? Is pay-before-ship acceptable? |
| 5. Would you enable it? | 1 min | A yes/no, and why |

---

## P2.3 — Record (10 min total)

One row per conversation in the table in
[VALIDATION_CONVERSATIONS.md](../research/07_concepts/VALIDATION_CONVERSATIONS.md). **Verbatim
quotes only.** No paraphrase, no composite characters, no rounding.

---

## P2.4 — Apply the rules — as written, not as reinterpreted

| Result | Pre-committed response |
|---|---|
| **4–5 of 5** recall a timing problem unprompted | Claim: *"tested with five shoppers, four recalled this unprompted."* Ask permission to quote one, first name or descriptor only |
| **2–3 of 5** | The problem is real but not top-of-mind → **change the hook** to lead with the explanation gap, not timing |
| **0–1 of 5** | **Serious.** A C01 fallback is **not real** — there is no time to build it after 4 Nov. Reframe to **safe-amount-only**: keep the decline and the requote, drop the claim that timing is the hook. Do not soften the finding |
| **≥3 of 5** would not set up a profile | Cold-start risk confirmed → lead the demo with the **saved** profile; onboarding becomes stated roadmap |
| **≥3 of 5** call the decline patronising | The copy is wrong, not the mechanic → rewrite to "what fits"; `test_never_shames_or_blocks` already enforces direction |
| Anything else / ambiguous | **No change.** Proceed |

**Ambiguity is not a trigger.** If the result does not clearly meet a row, the plan does not change.

---

## P2.5 — Update the claim (15 min)

By count, and only by count:

| n actually run | What the submission says | Where |
|---|---|---|
| 5 | "tested with five shoppers" | README, video, [C02_THE_IDEA](../research/07_concepts/C02_THE_IDEA.md) header |
| 3 | "tested with three shoppers" | same, n stated |
| 2 | "two conversations" — do not generalise | same |
| 0 | **Delete every hint of user validation** from README and video; stay "researched" | same |

Then send me the table and I will update the wording in
[SUBMISSION_KIT.md](SUBMISSION_KIT.md) and the idea document so all three agree.

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| Cannot reach five people by 4 Nov | Run three. Report n = 3. **Never** invent or pad |
| A conversation turns into a pitch | Discard it and mark it discarded. It is not evidence |
| Someone describes a problem you did not anticipate | Log it. Do not redesign the product mid-phase — capture it for after submission |
| Result contradicts the idea | Apply the rule. Falling back to C01 on 4 Nov is survivable; discovering this on 10 Nov is not |
| You want to reinterpret a rule | **You may not.** That is the entire purpose of writing them down first |

---

## Exit criteria

- [ ] n conversations run, n recorded in the table
- [ ] Unprompted-recall count recorded per person
- [ ] One decision rule explicitly matched and applied
- [ ] Claim wording updated to match n, in all three places
- [ ] Permission asked if a quote will be used

**Time-box:** if the table is still empty on the evening of 4 Nov, close the phase at n = 0 and move
on. Do not spend 5 Nov on it.

---

## V7 — the table, as run

<!-- V7 TABLE START · generated by scripts/v7_verdict.py · do not edit -->

**Generated 0 row(s).** The only permitted claim: **“DELETE every hint of user validation; the product is researched, not tested”**

> no rows: n = 0


| # | Who (shape, not name) | Timing recalled unprompted? | No explanation given? | Would set up a profile? | Decline: helpful or patronising? | Ship-after-pay OK? | Would enable it? | Verbatim that matters most |
|---|---|---|---|---|---|---|---|---|

<!-- V7 TABLE END -->
