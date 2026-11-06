# Five conversations, three days

**Time-box: 2–4 November, in parallel with building — not in place of it.**
Three evenings is plenty. If they are not done by 4 Nov, they are done with fewer people and the
count gets reported as-is.

**Purpose:** test the idea with real shoppers, and earn the right to say **"tested with five
shoppers"**. Not "validated" — five people is directional evidence, and calling it validation would
be the same overstatement this document exists to avoid.

Right now the evidence for C02 is secondary — surveys, CFPB data, complaint threads. That is
research, and calling it validation would be a claim a sharp judge can puncture. This is the
shortest honest path to the real thing: **five conversations of twelve minutes each**, done before
recording.

**Budget:** 5 people × 12 minutes + 30 minutes of notes. Doable across three evenings, alongside build work.
**Who:** anyone who has actually used Pay Later / Pay in 4 / Klarna / Afterpay in the last year —
**ideally in a US-market context**, since the statistics, the CFPB data and the sandbox behaviour all
describe that market. Not friends who will be
kind to you — ideally not product people.

---

## Rule zero

**Do not pitch.** The moment you describe Second Thought, you are measuring politeness. Ask about
the last time a payment landed badly, shut up, and write down what they say. The verdict at the end
is one question, not a demo.

---

## The script

### 1. The last time (3 min) — the only question that matters

> "Think about the last time you split a payment into four. Walk me through it — what did you buy,
> and what happened over the next six weeks?"

Follow with silence. If they say "it was fine", ask: *"Was there a moment where a payment landed at
an awkward time?"*

**What you're testing:** does the problem exist in their memory unprompted, or are you supplying it?
If they never mention timing, that is a finding against the idea — write it down.

### 2. The explanation gap (2 min)

> "When a payment method isn't available to you, or the amount is lower than you expected — do you
> find out why?"

**What you're testing:** the "blacklisted with no explanation" pattern.
Recorded verbatim or not at all.

### 3. The cold-start test (3 min) — the biggest adoption risk

Describe the setup, *not* the product:

> "Imagine a thing that needs your paydays and your main bills, once, before it can help. Two
> minutes of typing, or one sentence you speak. Would you actually do that? What would make you
> not bother?"

**What you're testing:** whether a payday profile is a step people will take. This is the weakest
assumption in the whole idea, so push here: *"What if it took five minutes?"* and *"What if you had
to connect your bank instead?"*

**Listen for:** "only if it saved me from something" — that is the hook to use in the pitch, in
their words, not yours.

### 4. Reaction to the two mechanics (3 min)

Read these as statements, not questions, and ask for a reaction to each separately:

> "A checkout tells you: *this doesn't fit this month — the third payment lands the day after rent.
> Up to $200 would work.*"

> "Or: *this fits, but not today — reserve it, pay on Thursday the 6th, and it ships after you pay.*"

**What you're testing:** whether the safe amount feels helpful or patronising, and whether
pay-before-ship feels acceptable or like being told no twice. **Both are load-bearing mechanics.**
If four of five say the decline feels judgemental, the copy changes, not the idea.

### 5. The one question (1 min)

> "If this existed at a checkout you already use, would you turn it on? Why or why not?"

Get a yes/no and the reason. No hedging accepted.

---

## How to record it

Append one row per conversation to `VALIDATION_CONVERSATIONS.md` below. Verbatim quotes
only — no paraphrase, no rounding, and **no composite characters**.

| # | Who (shape, not name) | Timing problem recalled unprompted? | No explanation given? | Would set up a profile? | Decline feels helpful or patronising? | Ship-after-pay OK? | Would enable it? | Verbatim that matters most |
|---|---|---|---|---|---|---|---|---|
| 1 | | | | | | | | |
| 2 | | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | |

---

## Decision rules — decide these *before* you run them

Pre-committing to the interpretation is what makes the result honest.

| Result | What it means | What changes |
|---|---|---|
| **4–5 of 5 recall a timing problem unprompted** | The problem is real and they know it | Use their words in the video. Say **"tested with five shoppers, four recalled this unprompted"** |
| **2–3 of 5** | The problem is real but not top-of-mind | Keep the idea, **change the hook** to lead with the explanation gap instead of timing |
| **0–1 of 5** | We have invented a problem that surveys overstated | **Serious.** Reframe as the safe-amount-only product (a smaller sale that fits), or fall back to C01 |
| **If 3–5 of 5 recall it unprompted** | Strongest available result | Ask permission, quote one person (first name or descriptor only) in the video |
| **≥3 of 5 would not set up a profile** | The cold-start risk is real | Lead the demo with the *saved* profile and treat onboarding as a roadmap item, said openly |
| **≥3 of 5 call the decline patronising** | The copy is wrong, not the mechanic | Rewrite to "what fits" framing; the test `test_never_shames_or_blocks` already enforces the direction |

---

## If you cannot run conversations

A ten-question form sent to twenty people gives you counts instead of reasons, which is weaker but
still better than nothing. Ask only: their last BNPL purchase, whether a payment landed awkwardly,
whether they were ever refused without explanation, and whether they'd set up a payday profile.
**Report the n.** A judge will forgive "five people" and will not forgive an unsourced percentage.

---

## Then, and only then

Once the table has rows in it:

1. Change `C02_THE_IDEA.md`'s header to *tested with five shoppers, DD MMM* — and keep
   the count visible even when it is unflattering.
2. Add one line to the video script in `../../plan/SUBMISSION_KIT.md` — *"we asked five people, four
   of them described this exact situation without being prompted"* — and be ready to show this file
   if asked.
3. Keep the table in the repo. An empty-but-honest evidence table is survivable; an invented quote
   is not.
4. **Never "validated".** The reportable claim is "tested with five shoppers", the n is stated, and
   the conversation table goes in the repo as the backing.
