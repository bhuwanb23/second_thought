# 08 — Go/no-go gates and red-team

The purpose of this file is to make killing a weak idea cheap and early, and shipping a strong one boring and predictable.

---

## Gates

Each gate is **pass/fail** with a hard date. Failing a gate means falling back, not pushing on.

### G0 — Concept chosen
**By: 2 Nov.** One concept, named, with its one-pager written. If no decision by 2 Nov, take C02 by default (see `DECISION_LOG.md`).
☐ Passed

### G1 — PayPal sandbox call succeeds
**By: 4 Nov.** An OAuth token, an order created, an AUTHORIZE executed, and the transaction visible in the sandbox dashboard. If you cannot do this by 4 Nov, the concept is wrong or the environment is.
☐ Passed

### G2 — The core mechanic works end to end
**By: 7 Nov.** The single thing your product exists to do, running against sandbox, in whatever ugly form. Not the UI — the mechanic. C02's mechanic is the affordability decision plus an AUTHORIZE hold. C01's is reading a repo and producing a correct findings list.
☐ Passed

### G3 — Demo-able on a stranger's machine
**By: 9 Nov.** Someone who is not you runs it from your README and gets to the core mechanic. **If they need you to explain anything, the README is wrong**, not the person.
☐ Passed

### G4 — Video recorded
**By: 10 Nov.** Full 2:40 video, exported, uploaded, link working. Recorded while the AG Grid licence is live.
☐ Passed

### G5 — Submitted
**By: 11 Nov.** Everything in `../research/01_contest/SUBMISSION_REQUIREMENTS.md` ticked, submitted a day early. Deadline is 12 Nov 12:00 PT = **13 Nov 01:30 IST** — do not plan to work on the night of the 12th.
☐ Passed

---

## The red-team questions

Ask these out loud, ideally to someone who does not like your idea. Each has a specific answer you must have ready.

**On the concept**
1. "Which of the 549 repos in the field is closest to this, and why is yours different?" — Have a name and a sentence.
2. "Why would PayPal want this to exist?" — Not "it's cool." A strategic reason tied to something they said.
3. "What happens when PayPal ships this themselves?" — Every top concept here faces this. Have the escape route (`C01.md` §10).
4. "Who is the specific person, and what did they say?" — A quote, not a persona.

**On the technology**
5. "What is the model allowed to decide, and what is it not?" — The answer every strong entry states explicitly.
6. "Show me a failure." — A declined authorization, a forged webhook, a blocked oversized payment. If you cannot, the demo is a mockup.
7. "What happens if the model is wrong?" — Name the deterministic fallback.
8. "Which PayPal APIs, exactly?" — Endpoint paths, not product names.

**On the submission**
9. "Is your licence visible in the GitHub About panel?" — 17% of the field fails this.
10. "Will your demo be up on 14 December?" — The requirement runs to 15 Dec 08:00 PT.
11. "Is the video under 3:00 and public?" — Judges need not watch past 3:00.
12. "Where are the credentials?" — Scanned on full history, not just the working tree.

---

## The five ways this project fails

Ranked by how often they actually happen, based on what the field looks like.

**1. Scope.** Eleven days, an ambitious concept, and a half-working demo. This is the most common failure by a wide margin. The mitigation is G2: the core mechanic alone by 7 Nov, everything else is optional.

**2. The demo is dead during judging.** You deploy on a free tier, it sleeps, a judge opens it on 5 December and sees a timeout. Mitigation: always-on instance, plus a scheduled health check that fails loudly.

**3. Nobody knows what it is.** A technically excellent project whose README opens with architecture. Mitigation: the sentence in §1 of the one-pager goes in the first line of the README, the video, and the short description. Identical wording in all three.

**4. It looks like everything else.** The concept drifted into `mandate-guardrail`. Mitigation: G0 — the cluster is chosen deliberately and the differentiation is stated in the first fifteen seconds of the video.

**5. The build works but the story doesn't land.** Mitigation: `Presentation` is 20% of the score and the video is the only artefact every judge consumes. Budget a full day for it, not an hour.

---

## Standing rule

**Every claim in the submission must trace to a file in this library.**

- A number → `../research/04_pain/PAIN_LEDGER.csv` (check the `evidence_strength` column first)
- A competitor count → `../research/03_field/CLUSTERS.csv`, then read `TEARDOWNS.md` before relying on it
- A PayPal priority → `../research/02_intent/INTENT_SIGNALS.csv`, with the verbatim quote
- An API choice → `../research/05_capability/PAYPAL_API_MAP.csv`

If a claim cannot be traced, cut it. An unsourceable number in a submission is worse than no number.
