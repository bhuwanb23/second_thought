# docs/ — what lives here

**Read the whole project in one file: [`Second-Thought-Dossier.pdf`](Second-Thought-Dossier.pdf)** —
twenty pages, research through to the working build, with the parts that did not work left in. It is
generated from [`DOSSIER.html`](DOSSIER.html) by `python3 tools/build_dossier.py`, so it can never
quietly drift from the repository.

Then, if you want the detail, two folders kept apart on purpose:

| Folder | Contains | Read it when |
|---|---|---|
| **[`research/`](research/)** | Everything we learned: the contest rules, what PayPal wants, the competitive field, the evidence of pain, API capability, sponsors, the concepts, and the idea itself | You want to know **why** the product is what it is |
| **[`plan/`](plan/)** | The master plan, eight phase documents, the lock, the decision log, and the submission kit | You want to know **what to do next** |

The code lives outside `docs/` at [`../product/`](../product/) — standard library only, 165 tests,
its own deploy config, and it is the thing that gets submitted.

---

## The shortest path

0. **[`plan/BRUTAL_REVIEW.md`](plan/BRUTAL_REVIEW.md)** — the honest benchmark against the field, the
   market and the rubric, and what is actually wrong with the idea
0b. **[`plan/JURY_10.md`](plan/JURY_10.md)** — the same project read by ten different judges, including
   the four who can end it; **[`plan/MARKET_AND_BENCHMARKS.md`](plan/MARKET_AND_BENCHMARKS.md)** — PayPal's
   Q3 2026 numbers, the product matrix, and a 10-dimension benchmark framework with filled scores
1. **[`research/07_concepts/C02_THE_IDEA.md`](research/07_concepts/C02_THE_IDEA.md)** — the product, in full
2. **[`plan/plan.md`](plan/plan.md)** — the master plan and the phase map
3. **[`plan/LOCK.md`](plan/LOCK.md)** — what is frozen, and the two tripwires that can still change things
4. **[`plan/P1_paylater_probe.md`](plan/P1_paylater_probe.md)** — the next thing to actually do

---

## Why research and plan are separate

A research folder that drifts into planning becomes a document nobody trusts. The split keeps one
rule enforceable: **research records what is true with sources; the plan records what we will do by
when.** When a fact changes, it changes in `research/` first, and the plan is updated to match.

Concretely, three times in this project a claim was found to be wrong or overstated — the
credit-bureau asymmetry, "volume preserved", and the word "validated". Each was corrected in
`research/` with a dated note, and the plan inherited the correction rather than the old claim.
