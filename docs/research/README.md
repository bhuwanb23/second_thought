# Research library

Everything this project knows, with sources. Seven numbered folders, each answering **one question**,
plus the framework used to gather it and the workbook holding the numbers.

Method and provenance: [RESEARCH_FRAMEWORK.md](RESEARCH_FRAMEWORK.md) ·
Data tables: [RESEARCH_WORKBOOK.xlsx](RESEARCH_WORKBOOK.xlsx)

---

## The map

| Folder | The question | Start with |
|---|---|---|
| [01_contest/](01_contest/) | What are the rules, dates and how is it scored? | [RULES_AND_DATES.md](01_contest/RULES_AND_DATES.md), then [JUDGING_MODEL.md](01_contest/JUDGING_MODEL.md) |
| [02_intent/](02_intent/) | What does PayPal actually want built? | [WHAT_THEY_WANT.md](02_intent/WHAT_THEY_WANT.md), [PAYPAL_TIMELINE.md](02_intent/PAYPAL_TIMELINE.md) |
| [03_field/](03_field/) | Who else is entering, and how good are they? | [METHOD.md](03_field/METHOD.md) → [FIELD_MAP.md](03_field/FIELD_MAP.md) → **[TEARDOWNS.md](03_field/TEARDOWNS.md)** |
| [04_pain/](04_pain/) | What is genuinely broken, with evidence? | [EVIDENCE_NOTES.md](04_pain/EVIDENCE_NOTES.md), [PAIN_LEDGER.csv](04_pain/PAIN_LEDGER.csv), [QUALITATIVE_QUOTES.md](04_pain/QUALITATIVE_QUOTES.md) |
| [05_capability/](05_capability/) | What can PayPal's APIs actually do? | [PAYPAL_API_MAP.csv](05_capability/PAYPAL_API_MAP.csv), [SANDBOX_AND_GOTCHAS.md](05_capability/SANDBOX_AND_GOTCHAS.md) |
| [06_sponsors/](06_sponsors/) | Where is the prize money? | [SPONSOR_STRATEGY.md](06_sponsors/SPONSOR_STRATEGY.md) |
| [07_concepts/](07_concepts/) | What should we build, and why this? | **[C02_THE_IDEA.md](07_concepts/C02_THE_IDEA.md)**, then [EV_RANKING.md](07_concepts/EV_RANKING.md) |

---

## What the research concluded

**1. The field is deep, not wide.** Our own scan found 549 public repositories on 1 Nov 2026 (this is
internal context — *registrants are not submissions*, and the count is not evidence for a judge).
The strongest entries are professional-grade: CI pipelines, passing test suites, threat models, live
demos, early videos. Six clusters are effectively closed, including `mandate-guardrail` (86) and
`invoice-ar` (60). `credit-bnpl` has 3. → [TEARDOWNS.md](03_field/TEARDOWNS.md)

**2. PayPal has said out loud what it cannot do.** Value-added services are under-monetised,
merchant integration takes weeks, agent trust is unresolved. One product-specific honourable mention
exists — *Best Use of Agentic Commerce*. → [WHAT_THEY_WANT.md](02_intent/WHAT_THEY_WANT.md)

**3. Three concepts survived both filters.**

| | Concept | EV | Why |
|---|---|---|---|
| 1 | C01 Integration doctor | 68.3 | Best aligned to the CTO's own demo; bounded by derivative risk |
| **2** | **C02 Second Thought** | **64.5** | **Chosen.** Strong evidence, intent fit 5, cluster of 3, no derivative risk |
| 3 | C06 Goal-bound remittance | 48.6 | Highest impact ceiling, weakest strategic fit |

→ [EV_RANKING.md](07_concepts/EV_RANKING.md)

**4. The decision.** C02, locked 1 Nov. → [C02_THE_IDEA.md](07_concepts/C02_THE_IDEA.md)

---

## Corrections on the record

Research documents are only worth reading if their errors are visible. Three claims were corrected
during review, each with a dated note left in place:

| Claim | Status |
|---|---|
| "PayPal reports missed BNPL payments to credit agencies where Affirm and Afterpay don't" | **Cut.** Affirm reports Pay in 4 to Experian (Apr 2025) and TransUnion (May 2025); PayPal does not publish its policy. The surviving argument needs no contested data: PayPal funds the merchant, so it bears the credit risk |
| "Volume preserved" | **Cut.** A DECLINE is lost Pay Later fee revenue. Replaced with the stated trade |
| "Validated" | **Cut.** The evidence is secondary. It is *researched*; [VALIDATION_CONVERSATIONS.md](07_concepts/VALIDATION_CONVERSATIONS.md) is how "tested with n shoppers" gets earned |

---

## Honesty rules this folder follows

- Every number has a source, a date and, where possible, a verbatim quote. → [04_pain/QUALITATIVE_QUOTES.md](04_pain/QUALITATIVE_QUOTES.md)
- Raw data and cleaned data are separate: `04_pain/raw/` holds what was fetched, `PAIN_LEDGER.csv` holds what was concluded.
- Generated files are generated: `EV_RANKING.md` is produced from `CONCEPT_PIPELINE.csv`, never hand-edited.
- A caveat travels with a number. The 1.83% formal charge-off sits beside the 47% self-reported lateness, every time.
- Where a figure cannot be verified, it is labelled unverified rather than dropped — a missing number that we needed is information too.
