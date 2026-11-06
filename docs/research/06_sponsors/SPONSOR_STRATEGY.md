# 06 — Sponsor prizes: the actual money math

Ten sponsors listed. Only **four pay cash**. Data: `SPONSORS.csv`.

---

## The ranked truth

| Sponsor | Cash on offer | Winner slots | Realistic cost | Verdict |
|---|---|---|---|---|
| **AG Grid** | **$10,000** ($5k/$2k/3×$1k) | **5** | 1–2 days | **Take it.** Best ratio in the contest. |
| Bryntum | $3,000 | 3 | 3–5 days, needs a real timeline | Only if your product genuinely has a schedule |
| APIMatic | $3,000 + subs | 3 | **under an hour** | **Take it.** Cheapest qualifying entry. |
| Channel3 | $1,500 | **1** | half a day | Good supporting tool, weak standalone target |
| Render | $2,250 in **credits** | 3 | ~0 (you need hosting anyway) | Use it for hosting; not for the prize |
| Zapier, Elastic, KERNEL, Postman, Astropods | **$0** | — | — | No prize exists. Tooling only. |

**Read the column that matters: winner slots × effort.** AG Grid offers five chances at five figures for a day or two of work. APIMatic offers three chances at $1,000 for an hour. Nothing else comes close.

---

## AG Grid — the one that matters

**Why it is a natural fit rather than a bolt-on:** every payments product in this library has a data surface. A merchant needs to see transactions. A marketplace needs to see payouts. A family remitter needs to see their lifetime transfers. You are going to build a table anyway — build it in AG Grid and the prize is nearly free.

**What they actually require:** use **AG Studio** — theme builder, custom widgets, layout tools — not raw AG Grid Community. Ideally also the **Studio Agent Framework**, since "Agent" is the hackathon's theme. Boilerplate: `github.com/paypaldev/hackathon-paypal-ag-grid-boilerplate`. 45-day trial.

**The risk that will bite you:** the trial expires. Judges look at the project between 1 and 15 December. If your demo renders a watermark or an expired-licence error on the judge's machine, you have turned a prize into a liability. **Mitigation:** keep a licence-free fallback view, and make the AG Grid path the enhanced one. Also record the video while the licence is live — the video is permanent, the live demo is not.

**How to not look like a bolt-on:** the grid must be where a *decision* happens, not just where data appears. A grid where a merchant selects rows and approves payouts, or where disputed transactions are triaged inline, is a decision surface. A read-only table of the last 50 orders is not.

---

## APIMatic — the cheapest points in the contest

Free plan for the hackathon, PayPal's OpenAPI spec is already enabled, and the **Context Plugin** gives your AI coding tool the full PayPal API surface. Winners used it. Everyone who uses it gets a free month of Basic.

Under an hour of work; three winner slots; the only cost is naming it in your README and using a generated SDK or portal somewhere visible. If you do nothing else with sponsors, do this.

**Caveat:** "best use" implies more than dev-time convenience. Generating a real typed client for the endpoints you call, or a docs portal from your own spec, makes it substantive rather than incidental.

---

## Bryntum — conditional on your concept

Genuinely excellent *if* your product has a time axis: payment schedules, delivery timelines, subscription renewal calendars, milestone plans, dispute deadlines, remittance goal tracking. If your product has no timeline, do not bend the product to fit it.

Only roughly 23 repos in the field even mention it, so the competition is thin — but the trial-package watermark risk is worse here than with AG Grid, because a Gantt chart is a central visual, not a side panel.

---

## Channel3

Must **actually call the API or MCP** for search, enrichment or recommendation. Referencing it in the README without calling it fails. Promo code `PAYPAAL-HACKATHON-2026` (check the spelling on the sponsor page — it has been listed inconsistently) for 20,000 credits.

Natural for any commerce concept: product search, enrichment, recommendations. But **one winner only**, so despite similar effort it is a worse bet than AG Grid.

---

## Render

Not a prize target — a **requirement satisfier**. You must be available until 15 Dec. Render gives $50 credits via the hackathon portal and "Render Workflows" for agent orchestration, which also counts toward the prize. Free tier sleeps; a cold start during a judge's three-minute window is a real risk. Budget for the cheapest always-on instance.

---

## No-prize sponsors — do not spend time here

Zapier (agent actions across 9,000 apps, 14-day Pro trial), Elastic (search/embeddings, 14-day trial), KERNEL (cloud browsers, $50 credits), Postman (API testing), Astropods (agent OS). All useful tools; none with a prize attached. If one genuinely accelerates your build, use it. Do not build a feature to use one.

---

## Recommended combination

**AG Grid (primary) + APIMatic (free) + Render (hosting).** Bryntum only if the concept has a genuine timeline. Channel3 only if the concept needs product data anyway.

This yields five AG Grid chances, three APIMatic chances, the hosting requirement satisfied, and no architecture compromises. Expected value on the sponsor axis alone is better than most teams' chances at the grand prize.
