# LOCKED — 1 November 2026

**Concept C02, "Second Thought", is locked.** The idea, the scope and the pitch are frozen.
From this point the work is execution, not revision.

Locked at **103 tests passing**, preflight clean, five rounds of review incorporated.

---

## 1. What "locked" means here

| Frozen | Not frozen |
|---|---|
| The idea: payday-aware checkout that sometimes says "not yet" | Bug fixes, copy fixes, UI polish |
| The three verdicts: OFFER / DEFER / DECLINE | How the OFFER branch is *worded* on camera (tripwire 1 decides this) |
| **Pay before ship** as the DEFER rule | Which sandbox credentials work |
| The safe amount, and the one-click override | The exact recording date, within the freeze window |
| The customer answer: *PayPal pays, the shopper benefits, the merchant embeds* | Whether AG Grid is used (decision due 5 Nov) |
| The split: model phrases and proposes, engine decides | |
| The claims, as corrected — no credit-bureau asymmetry, no "volume preserved", no "validated" | |

**The rule:** nothing in the left column gets re-opened. If a new objection appears, it goes in the
"after submission" list, not into the build.

---

## 2. The two tripwires, pre-committed

Both are decided in advance so they cannot be renegotiated after the results are in. That is the
whole point of writing them down now.

### Tripwire 1 — Pay Later sandbox probe

**Run first. Before anything else.**

| | |
|---|---|
| **Question** | Does Pay Later render for us in sandbox? |
| **Tool** | `../../09_build/prototype/paylater_probe.html` — open in a real browser, paste the `sb…` client ID |
| **Changes** | **Only the wording of the OFFER branch.** Nothing else |
| **Does not change** | The idea, the verdicts, the DEFER rule, the safe amount, the pitch |

| Result | Pre-committed response |
|---|---|
| **Eligible** | Record with video **script A**. Show the real `<paypal-paylater-button>`. OFFER → `paylater` |
| **Not eligible** | Video **script B**, said openly. OFFER → `authorize_hold` (a real AUTHORIZE). **The invoice becomes the hero** |
| **SDK fails / no clear answer** | Same as not eligible, and say that on camera. Never hard-code a fake button |

A probe that returns "not eligible" **closes the tripwire**. An unanswered one does not.

### Tripwire 2 — Five conversations

**Time-boxed: 2–4 November, in parallel with building, not instead of it.**
Script and pre-written decision rules: `../research/07_concepts/VALIDATION_CONVERSATIONS.md`.

The only results that can change the plan:

| Result | Pre-committed response |
|---|---|
| **0–1 of 5 recall a timing problem unprompted** | The problem is not as we claim. Reframe to safe-amount-only, or fall back to C01 |
| **≥3 of 5 would not set up a payday profile** | Cold-start risk is real: lead the demo with the saved profile, treat onboarding as roadmap, say so |
| **≥3 of 5 call the decline patronising** | The copy is wrong, not the mechanic. Rewrite to "what fits" |
| **Anything else** | No change. Proceed |

**These rules are not to be reinterpreted afterwards.** If the result is ambiguous, it is not a
trigger, and we proceed.

---

## 3. How the conversations get reported

Set by the reviewer, and binding:

- **"Tested with five shoppers."** Not "validated". Five people is directional evidence, and the
  submission will say exactly what it is.
- **Don't lead.** Ask about the last time a payment landed badly. Describe the product second, or
  not at all if the conversation runs out of time. The result only counts if the timing problem is
  recalled unprompted.
- **If 3–5 of 5 recall it unprompted**, ask permission and quote one person — first name or
  descriptor only, in the video.

---

## 4. Execution order from here

| # | Task | Owner | When |
|---|---|---|---|
| 1 | **Pay Later probe** | User (needs `sb…` client ID) | 2 Nov |
| 2 | **Five conversations** | User | 2–4 Nov, parallel |
| 3 | Sandbox client ID + secret → `demo.py --live` | User | 2 Nov |
| 4 | `LLM_API_KEY` → AI badge reads `LLM`, not `LLM-MOCK` | User | 3 Nov |
| 5 | Deploy to Render starter; verify `/healthz`; re-verify keep-alive | User | 4 Nov |
| 6 | AG Grid in/out, written down | User | 5 Nov |
| 7 | Polish UI + README only | Agent | 6–8 Nov |
| 8 | **Feature freeze** | — | 9 Nov |
| 9 | Record the 2:40 video | User | 10 Nov |
| 10 | Submit | User | 11 Nov |

Deadline: **Thu 12 Nov 2026, 12:00 PT** = 13 Nov 01:30 IST. Submitting 11 Nov leaves a day of slack.

---

## 5. What is already done, so nothing gets re-litigated

- ✅ Idea, customer, data provenance, DEFER rule, legal framing — reviewed and corrected
- ✅ All claims checked; the credit-bureau asymmetry claim **removed as outdated**
- ✅ "Volume preserved" replaced with the honest trade
- ✅ "No adverse action" replaced with the two-mode framing
- ✅ 103 tests, preflight passes, demo runs offline and is labelled honestly
- ✅ Probe page built and self-contained
- ✅ Video script, tools-used text, judge Q&As in `SUBMISSION_KIT.md`

## 6. Not to be touched

Framework rewrite · new features after 9 Nov · mock data presented as live · the mode badge ·
the pay-before-ship rule · quoting a statistic whose source has not been read · any claim about
PayPal's credit-bureau reporting.
