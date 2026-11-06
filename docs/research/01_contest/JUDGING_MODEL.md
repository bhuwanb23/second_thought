# 01 — How judging actually works

Source: Official Rules §6, plus what the field scan shows about how people lose.

---

## Two stages

**Stage 1 — pass/fail.** Two gates only:
1. Does the project reasonably fit the theme?
2. Does it reasonably apply the required APIs/SDKs — i.e. is PayPal genuinely, verifiably used?

Nothing else matters at this stage. A beautiful project with a decorative PayPal button fails here.

**Stage 2 — five equally weighted criteria.** Scored per submission by a panel.

| Criterion | Exact wording | What it means operationally |
|---|---|---|
| **Technological Implementation** | "How thoroughly and skillfully does the project use PayPal Developer Platform and AI tool(s)? Does the project reflect genuine effort and a working, non-trivial implementation?" | Multiple PayPal products, server-side auth, verified webhooks, idempotency, error paths. Non-trivial = a judge can see it wasn't a template. |
| **Design** | "Does the project deliver a complete, coherent product experience — not just a technical proof of concept?" | Real screens, empty/loading/error states, populated demo data, consistent visuals. |
| **Potential Impact** | "Does the project make a credible, specific case for solving a real problem for a real audience — and does the solution actually address that problem based on what's demonstrated?" | Named audience, sourced pain, and the demo shows the solution working for that audience. |
| **Innovation/Idea** | "How creative and novel is the concept and does the project differ from existing concepts?" | Distinct from the other submissions (549 repos in the field) and from existing products. |
| **Presentation** | "Does the video clearly demonstrate the project working end-to-end? Does the pitch communicate what problem is solved, who it's for, and why it matters?" | Storyboarded, under 3:00, problem → audience → live product → how → why. |

## The tiebreak rule — read this twice

> "If two or more Submissions are tied, the tied Submission with the highest score in **the first applicable criterion** listed above will be considered the higher scoring Submission."

The first criterion is **Technological Implementation**. In a field of 500–1,000 entries, score clustering makes ties common. **When you have to choose between more polish and more technical depth, depth wins the tie.**

## Automated analysis is explicitly permitted

> "This process may utilize expert panels, peer review, **automated AI-driven analysis**, or any combination thereof."

Practical consequence: your README and description are read by a machine as well as a human. Include the literal names — `Orders v2`, `AUTHORIZE`, `webhooks`, `Agent Toolkit`, `MCP`, the model you used — and a "Tools used" section. Do not bury them in prose.

## Judges

Not individually listed on the site, and the panel may change during the judging period. Assume PayPal employees (product, developer relations, agentic commerce) plus Devpost administrators. Assume they have seen every shopping-agent-with-a-budget entry.

---

## What the top of the field already does (the real bar)

From the highest-depth repos in the 549-repo scan:

- **CI badges and passing test suites** — one leading entry advertises 55/55 pytest, another 275 deterministic checks across 55 deliveries
- **Live demo with no login and no keys required**
- **A `/proof` page** listing every measured number
- **A threat model** (`SECURITY.md`) and a red-team screen showing attacks blocked
- **An explicit statement that the demo stays online until 15 Dec 2026**
- **A 2:18–2:37 demo video, already recorded, weeks before the deadline**

That is the standard at the top decile. It is not the standard across the field — but if your concept lands in a crowded cluster, that is who you are being compared against.
