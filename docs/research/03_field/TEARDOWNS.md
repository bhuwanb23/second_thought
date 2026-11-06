# 03 — Head-to-head teardowns

The highest-depth repos in the field, read properly. This is the part of the scan that actually changes decisions: cluster *counts* tell you where the crowd is, teardowns tell you **how good the crowd is**.

All facts below come from the repos' own READMEs, retrieved 1 Nov 2026.

---

## The uncomfortable headline

The top ~12 entries are not hobby projects. They ship CI pipelines, passing test suites, threat models, red-team screens, live demos with no login, `/proof` pages listing measured numbers, and 2–3 minute videos recorded weeks before the deadline. Several explicitly state their demo is "kept online until Dec 15, 2026" — they read the judging rules.

**Consequence:** in any cluster where one of these lives, "a good idea, working" is not competitive. `../07_concepts/EV_RANKING.md` already discounts crowded clusters; these teardowns are the reason the discount should be believed rather than treated as a formality.

---

## 1. Speedyzyzz/sentinel-prooflayer — depth 11/13

> *"The Unified Agent Mandate Control Plane & Causal Pre-Dispute Evidence Graph for Autonomous B2B Commerce on PayPal"*
> *"Policy-governed AI payments before they happen. Dispute-ready evidence graphs after they happen."*

**What it is:** two halves — a pre-payment policy gate over agent-initiated payments, and a causal evidence graph assembled *before* a dispute can be filed, so a merchant has proof ready.

**Craft signals:** live command centre on Render; separate live FastAPI with Swagger docs; **55/55 pytest passing in 0.90s**, advertised as a badge; MIT. Markers hit: webhook, sigverify, authorize, invoicing, disputes, toolkit, mcp, aggrid, license, idempotency, liveurl — all 11 non-trivial.

**Verdict:** this is the strongest entry in the field and it sits across `dispute-chargeback` + `mandate-guardrail` (86 + 49 repos). **Do not enter either cluster.**

---

## 2. antonmareo10/supplora-pay — depth 11/13

> *"The accounts-payable agent for independent restaurants… Claude reads each invoice. Deterministic rules check it in integer cents against the signed delivery note and the price history."*

**What it is:** a restaurant's weekly supplier payments. An LLM reads the invoice; **deterministic integer-cent arithmetic** validates it against the signed delivery note and price history; a planning agent proposes the week inside a cash cap; the owner approves; PayPal moves money. The signature demo moment is an invoice asking to be paid to a **new PayPal address** — a fraud attempt, caught.

**Craft signals:** live demo with no login and *no keys required*; 2:18 video; `SECURITY.md` threat model; GitHub Actions CI; MIT. Explicitly states the boundary: *"No agent can pay on its own: the owner's approval only authorizes a card, and PayPal captures what the signed delivery note confirms."*

**Why it wins:** hyper-specific audience (independent restaurants), a real Mediterranean business artefact (*albarán*), one sharp fraud moment, and a crisp deterministic/LLM boundary. This is the template for what a high-scoring entry looks like.

**Verdict:** occupies `invoice-ar` + agent-payments-with-guardrails. Note the pattern, do not copy the domain.

---

## 3. Ash-projects-personal/pact-agentic-commerce — depth 10/13

> *"Two software agents agree a deal for a digital service, write the contract checks themselves, put real money behind the deal through PayPal, and let a third agent judge the delivered work… If the work fails, the buyer is refunded and the seller loses a performance bond on top."*

**Craft signals:** explicitly addresses "the hiring reader" (PayPal engineer) in the README; **275 checks across 55 deliveries, zero errors** in its accuracy battery; money moves only on a deterministic verifier's verdict, with the LLM restricted to *wording*; a performance bond so cheating costs money.

**Verdict:** **this is C07 (A2A procurement) and C20 (escrow), done at a level that closes both.** The `a2a-agent-commerce` cluster only has 9 repos — but one of them is this.

---

## 4. MrNahadi/CounterSign — depth 9, MLH-style craft

> *"Agents can draft any payment. Only your rules can sign it. A money firewall for AI agents that hold PayPal and M-Pesa powers."*

**What it is:** sits between an agent and the rails. Every proposed money action (refund, payout, accepting a dispute, M-Pesa transfer) is checked against (1) **the rails' own records** — PayPal captures, orders, carrier tracking, disputes, audit log — and (2) **a signed, versioned merchant mandate** ("refund lost parcels up to $80 on their own, ask me first above that"). Returns **allow / step-up / deny**.

**Verdict:** this is the mature form of C05 (agent-trust gateway). Notable technique: **validating against the payment rail's own records rather than the agent's claims.** Worth stealing as a design principle wherever you land.

---

## 5. ayusharyakashyap/Covenant — depth 9

> *"Write the deal in a sentence. PayPal holds the money. AI checks the work."*

**What it is:** plain-English agreement → compiled into milestones, checkable conditions, deadlines, capped penalties → **PayPal authorization holds the client's money** → freelancer uploads proof → Gemini/Claude checks each condition → milestone captured on verification → an AI arbiter splits funds on disagreement.

**Verdict:** C20 done correctly *with AUTHORIZE* (which only 9% of the field uses). `escrow-milestone` is closed.

---

## 6. Thinkelution/paypal-retrofit — depth 10 — **the one that overlaps C01**

> *"Give any existing business a PayPal brain. An open-source SDK, CLI and console that lets an AI agent wire PayPal into a business system that already exists: its own database, its own invoice numbers, its own customers. Then it keeps both sides reconciled, with an agent that never moves money without a rule the owner set."*

Plus: no-code setup wizard, morning digest by email/Slack with one-click approvals, MCP server, customer self-service portal with statements and autopay, late fees and early-payment discounts as owner rules, a bookkeeper multi-client screen, plain-English rules with preview, and a "money trail" per invoice.

**Why this matters to us:** this is `merchant-integration` + `invoice-ar`, and it is the closest thing in the field to a "read the business, then connect PayPal" product — which is C01's premise.

**But note the difference, which is real:** paypal-retrofit connects PayPal to a business that **does not have it yet**. C01 diagnoses, **upgrades and certifies a PayPal integration that already exists** — the SDK-v6 / Orders-v2 / deprecated-Drop-in migration problem. Different task, different user, different artefact (a certification report, not a working ledger). The overlap is in *flavour*, not function.

Still: two repos in the entire field touch merchant integration, and one of them is this good. C01's thin-cluster advantage is real but thinner than the count of 2 suggests.

---

## 7. rohith1005H/AgentBaazar — depth 10 — **the one that overlaps C03/C22**

> *"Agent-ready commerce for every small store, on PayPal… PayPal's agentic commerce stack lets an agent platform talk to a merchant through one contract: the **Cart API v1** (the 'Store Sync' merchant contract). Big retailers will implement it. A sari shop with a Google Merchant feed will not. AgentBaazar is that missing merchant side, open source."*

It gives a small store a spec-conformant Cart API from a product feed, with **buyer charged only when the merchant ships** (authorization + late capture).

**Verdict:** this is the Store Sync gap, identified and filled at protocol level, by someone who read the docs carefully. C03 and C22 (agent-ready storefront) are effectively **closed** as differentiators. The `storefront-builder` cluster count of 12 undersells it badly.

The remaining sliver: AgentBaazar still needs the merchant to *have* a product feed. Sellers with only photos are addressed by #8.

---

## 8. RAK2315/shopfront-agent — depth 9

> *"Turn a social-only seller's product photos into a PayPal-backed store that AI shopping agents can buy from… The agent picks products, the server sets [the price]"*

Live demo, video, threat model, MCP server so you can shop it from your own agent. Covers the photos-only seller that AgentBaazar's feed requirement excludes.

---

## 9. longtt-marketing/paid-signal — depth 10

> *"PayPal payments matched to the ad clicks behind them; a Claude agent inside AG Studio drafts the next move, a person approves."*

**Craft signals worth copying regardless of your concept:** a dedicated **`/proof` page where every measured number is listed**; a "money trail" view from ad click → PayPal → Meta; CI plus a scheduled *live demo health check* workflow. That last one is a direct, cheap answer to the "must stay available until 15 Dec" rule.

---

## 10. KaraAliOsman/paylet — depth 9

> *"Fair drops for the agent era: one PayPal hold per account, agents welcome via MCP, AI-collapsed reseller networks, verifiable draw."*
> *"Agents can enter. Only people can pay."*

Sneaker-drop lottery where every entry is an authorization hold, one per PayPal account, losers never charged. Real sandbox e2e badge, unit tests, coverage, CI.

---

## 11. Thanatos9404/leash — depth 9

> *"Enforceable spending mandates… compiled into a signed policy, a PayPal Orders v2 authorization as the hard ceiling, per-cart rule [checks], and a signed receipt chain you can hand to a dispute."*

Notable: a **"red team: eight attacks blocked"** screen. Shipping an adversarial test screen is a strong, cheap Technological Implementation signal.

---

## 12. Fu93/tradeos — depth 9

> *"PayPal moves the money. TradeOS moves the work… Use AI where language is ambiguous. Use code where money is at stake."*

Cross-border merchant operations inbox — customer messages, refund decisions, a human approval gate, and a demo GIF showing *0 refunds approved by an AI agent*. The "AI declined to act" demo moment is a distinctive framing.

---

## What the teardowns change

| Concept | Was | Now |
|---|---|---|
| C01 integration doctor | thin cluster of 2, strong | still best-aligned; differentiate hard from paypal-retrofit on *upgrade/certify*, not *connect* |
| C03 / C22 agent-ready store | cluster 12, thought thin | **effectively closed** by AgentBaazar (protocol-level) + shopfront-agent (photos) |
| C05 agent-trust gateway | cluster 38 | closed at the mature end by CounterSign |
| C07 A2A | cluster 9, thought thin | **closed** by Pact's 275-check verifier |
| C20 escrow | cluster 21 | **closed** by Covenant (uses AUTHORIZE correctly) |
| C17 mandate | cluster 86 | hopeless |
| **C02 BNPL decision agent** | cluster 3 | **no deep competitor found in the top 12.** Strengthened. |
| **C06 remittance** | cluster 1 | **no deep competitor.** Strengthened, but intent fit stays 3. |

## The pattern to imitate, whatever you build

1. A sentence a judge could repeat, naming a **specific** audience.
2. One sharp fraud/abuse/failure moment in the demo that the product catches.
3. An explicit statement of **what the model is not allowed to decide**.
4. A test suite you paste into the README.
5. A `/proof` or `/redteam` page listing measured numbers.
6. Live, no-login, no-keys demo, with a scheduled health check.
7. Availability statement through 15 Dec.
