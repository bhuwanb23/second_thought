# Whose data is this? — provenance, consent and privacy

This is the question that decides the **Potential Impact** score. It is also the honest weak
point of the prototype: a seeded persona is a demo device, not a data source. This file states
the real path.

---

## The short answer

**The shopper's data is the shopper's.** A merchant cannot see a buyer's income, rent or other
BNPL plans, and has no right to. So the engine is fed only by:

1. **What the shopper tells us** — once, in their own time, as a **payday profile**. Typed or
   spoken in their own words, extracted by the model (`/api/profile`), reviewed by them before it
   is used. *Not at checkout:* nobody types their bills at the till, so the checkout never asks a
   question — it applies the profile they already set up. Consent is the input mechanism, not a
   checkbox bolted on afterwards.
2. **What we originated ourselves** — every plan *this merchant* sold *this shopper*, held in
   our own ledger. This is the merchant's own transaction data, not borrowed data.
3. **What the shopper's own payment history shows us** — `Transaction Search` against the
   merchant account only.

Nothing else. There is no open banking, no credit bureau pull, no cross-merchant profile.

---

## Why the demo uses a persona, and what changes in production

| Demo | Production |
|---|---|
| Persona constants in `personas.py`, optionally overridden by a saved profile | The shopper sets their payday profile up once (`profile.py`); every later checkout applies it silently |
| Fixed opening balance | Shopper-declared "about how much is in your account right now", or absent |
| Obligations pre-seeded | Extracted from free text, each item shown back with a confidence score for confirmation |

**Say this on camera or in the README.** "The numbers here are a seeded persona; in production
the shopper enters them, and the model extracts them" is a sentence that costs two seconds and
buys credibility for everything else.

The future path is open banking (an account-information API), which would remove the manual
step. That is explicitly **not built**, and should be described as roadmap, never as a feature.

---

## The consent flow (what to build, and what the prototype already implies)

1. **Shopper is told what is needed and why**, in one sentence: *"To tell you whether this
   payment fits, we need to know your paydays and your essential bills."*
2. **Shopper enters it themselves** — free text is fine; the model structures it.
3. **Shopper sees what was extracted**, per line, with a confidence score, and can correct it.
   Unconfirmed lines are flagged and are never treated as settled fact.
   Low-confidence items (`< 0.6`) are visually flagged and never silently trusted. See
   `agentic.py::validate_extraction`.
4. **The verdict is advisory and overridable.** A "buy anyway" path exists and is one click.
5. **Consent is scoped to the decision**, not to a profile. We do not need it tomorrow to answer
   today's question.

---

## Privacy commitments (write these into the README verbatim)

- **No data sold, shared or brokered.** Not to the merchant in identifiable form, not to anyone.
- **No credit decision.** We do not score, rank, underwrite or report to any bureau. The engine
  does arithmetic on numbers the shopper supplied.
- **No adverse action.** Nothing is ever declined. A DECLINE verdict is the *merchant's* choice
  of which instrument to surface, and the shopper can override it.
- **Data minimisation.** We ask for paydays and essential bills only. Not spending categories,
  not a full transaction history, not an income figure we don't need.
- **Merchant sees aggregates only.** The merchant console shows counts — "14 shoppers would have
  collided this month, 11 took the invoice" — never one shopper's rent.
- **Deletable.** A shopper can clear their declared obligations at any time (`/api/reset` in the
  prototype; a real account-level delete in production).
- **Sandbox only.** No live credentials, no real money, no real personal data anywhere in this
  repository. The personas are fictional.

---

## The fair-lending note, for the judge who asks

A tool that tells someone a payment might not fit is adjacent to credit decisioning, and that
needs an answer ready:

- The engine uses **only** the numbers the shopper gave us. There is no model over personal
  characteristics, no proxy variables, no protected-class inference.
- The verdict is **not** an approval or a denial of credit. Pay Later eligibility is decided by
  PayPal, and we surface it rather than second-guess it — `findEligibleMethods()` is the only
  source of truth for that.
- Every outcome is **overridable by the shopper**, and the override is recorded as an override,
  not as a failure.
- We never present a verdict as a judgement of the person. The copy is deliberate: *"what
  doesn't fit"*, never *"you can't afford"*. There is a test for this —
  `tests/test_agent.py::test_never_shames_or_blocks`.

That combination — consented inputs, arithmetic only, no adverse action, always overridable —
is what makes this budgeting transparency rather than credit scoring. Say it in those words.
