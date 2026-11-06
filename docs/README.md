# docs/ — what lives here

Two things only, kept apart on purpose:

| Folder | Contains | Read it when |
|---|---|---|
| **[`research/`](research/)** | Everything we learned: the contest rules, what PayPal wants, the competitive field, the evidence of pain, API capability, sponsors, the concepts, and the idea itself | You want to know **why** the product is what it is |
| **[`plan/`](plan/)** | The master plan, eight phase documents, the lock, the decision log, and the submission kit | You want to know **what to do next** |

The active code lives outside `docs/` at [`../product/`](../product/). The earlier implementation is
preserved separately in [`../archive/prototype/`](../archive/prototype/) and is not deployed.

---

## The shortest path

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
