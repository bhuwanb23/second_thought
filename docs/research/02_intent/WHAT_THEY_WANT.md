# 02 — What PayPal actually wants

The single most useful thing you can do before choosing a concept: separate what PayPal says to **investors** (where they admit weaknesses) from what PayPal says in **marketing** (where they claim strengths). The admissions are the openings.

Data: `INTENT_SIGNALS.csv` (24 signals, each dated and sourced). This file interprets them.

---

## 1. The three things they admit are broken

**a) Value-added services are not monetised.** Q3 2026 call, CEO Enrique Lores:
> "Services like payouts or risk as a service or invoicing… either we have not been able to attach them properly, or we have not been able to monetize them properly. That's going to be a key priority."

Attach rate went 5% → 6% and is being pushed by a "specialised sales force." A product that demonstrates *automated* attach — reading a merchant's own transaction data and provisioning the right service — is answering the CEO's stated priority directly.

**b) Merchant integration is slow and painful.** The CTO built an agent for it. At Ai4 (10 Aug 2026) Srini Venkatesan demoed a **Merchant AI Integration Agent** that "reads a merchant's codebase, understands its PayPal integration, and automatically upgrades, validates, and certifies compliance with the latest version" — cutting certification from "weeks" to "hours."

Building this at hackathon scale is the single best-aligned technical concept in the entire space. It also carries the most risk: you would be shipping a small version of something PayPal just announced it has. See `../07_concepts/one_pagers/C01.md` for the three escape routes.

**c) Agent trust is unresolved.** Q3 2026, on agentic commerce:
> "both will have to validate that this is a real consumer that can pay, this is a real merchant that has the product… it's really all about trust and about the security."

This is the frame the whole hackathon sits inside.

---

## 2. The single prize that tells you what they want to see

Eight honourable mentions worth $5,000 each. Seven are generic — *Most Creative, Most Impactful, Best Demo Delivery, Best Use of PayPal + AI…*

Exactly one names a product area: **"Best Use of Agentic Commerce" — one winner, $5,000.**

They had space to name eight themes and named one. That is the theme. It should appear in your submission narrative explicitly, even if your product serves a different surface.

---

## 3. The strategic narrative to align with (use their words)

PayPal's public story since **28 Oct 2025** is **Agentic Commerce Services**, in two halves:

- **Agent Ready** — merchants accept payments on AI surfaces with fraud detection, buyer protection, dispute resolution, "zero lift."
- **Store Sync** — push catalog and inventory to agent platforms.

Then the agent surfaces landed in sequence: Microsoft Copilot Checkout (8 Jan 2026), Cymbio acquisition (5 Feb 2026), Meta Muse (23 Sep 2026), Glance/InMobi across 60M+ devices (15 Oct 2026). Merchant-side: Ai4 Merchant AI Integration Agent (10 Aug 2026). Protocol-side: remote MCP + Agent Toolkit (29 Apr 2025), A2A/AP2 contribution including the **Mandates** concept (Oct 2025), OpenAI ACP (Oct 2025).

Full dated timeline: `PAYPAL_TIMELINE.md`.

**How to use this:** your closing line should be "this is a missing piece of Agent Ready / Store Sync / the mandates work," not "this is a cool use of AI."

---

## 4. Where the stated priorities are NOT the real priorities

Management said on the Q2 2026 call that agentic payments become material **"from 2028."** Near-term, AI's value to PayPal is cost and speed: 24M customer-service contacts resolved by AI across 190 countries, 6 languages.

**Consequence for you:** do not build a market-size slide for 2028. Judges will not be impressed by TAM. They will be impressed by a working, deep, safe implementation of something their roadmap already contains.

---

## 5. The intent-fit scores used across this library

Each concept in `../07_concepts/CONCEPT_PIPELINE.csv` carries an `intent_fit` score 1–5, meaning *how directly does this answer something PayPal said out loud*:

| Score | Meaning | Examples |
|---|---|---|
| 5 | Answers a named executive admission | C01 (integration), C04 (VAS attach), C02 (financial services growth) |
| 4 | Answers a shipped product or announced initiative | C03 (Store Sync), C05 (agent trust) |
| 3 | Adjacent to the narrative, plausible but not named | C06 (remittance), C14 (payouts for gaming) |
| 2 | Generic "AI + payments" | C10, C15, C16 |
| 1 | Would not register | — |

Note the trap: **intent fit and field coverage are inversely correlated here.** The things PayPal talks about most are exactly the things 50+ other entrants are building. That is what `../07_concepts/EV_RANKING.md` resolves.
