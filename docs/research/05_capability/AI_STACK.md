# 05 — The AI stack and what to actually build with

Which agent stack to use, and how it interacts with PayPal's own tooling. Data: `PAYPAL_API_MAP.csv`, `tools/`, and the field scan.

---

## The three integration layers, in order of how impressed a judge will be

**Layer 1 — PayPal's own agent tooling.** `@paypal/agent-toolkit` (~30 tools) and the remote MCP server (`search_product`, `create_cart`, `checkout_cart`). Used by **22%** and **16%** of the field respectively. Fast to wire up, but almost everyone uses it shallowly — enabling one tool and letting the model call it. Using it *deeply* (multi-step workflows, policy enforcement between tool calls, approval gates) is still differentiating.

**Layer 2 — a general agent framework.** Any of LangGraph, CrewAI, the Vercel AI SDK, Claude Agent SDK, OpenAI Agents SDK, Google ADK. Judges do not score framework choice. They score whether the agent architecture is *legible* — can you point at the screen and say "this is the model, this is the deterministic core, this is the boundary."

**Layer 3 — direct REST integration.** Orders v2 over HTTPS with your own OAuth. The lowest-level and most credible. Only **9%** of the field uses `AUTHORIZE`; only 26% verify webhook signatures.

---

## The rule that separates high scores from mid scores

> **Never let the model decide whether money moves.**

Every strong entry in the field scan states this explicitly:

- supplora-pay: *"No agent can pay on its own: the owner's approval only authorizes a card, and PayPal captures what the signed delivery note confirms."* Arithmetic in **integer cents**, deterministic.
- pact: money moves on the deterministic verifier's verdict; the LLM only rewrites wording. 275 checks, zero errors.
- tradeos: *"Use AI where language is ambiguous. Use code where money is at stake."*
- covenant: plain English in, compiled to typed conditions and capped penalties, then enforced deterministically.

Practically: **the LLM produces a proposal plus a rationale; a deterministic function validates it against rules and API facts; a human approves above a threshold; PayPal executes.** Put that diagram on screen in the video.

## Measured field usage — where the room is empty

From 549 repos (1 Nov 2026):

| Capability | Usage | Gap |
|---|---|---|
| Orders — CAPTURE | **95%** | floor, mandatory, not differentiating |
| Payouts | 29% | crowded as headline, strong as act two |
| Webhooks | 26% | but only 26% verify signatures |
| Agent Toolkit | 22% | usually shallow |
| MCP | 16% | |
| **AUTHORIZE + late capture** | **9%** | **the single most underused correct primitive** |
| Transaction Search | 9% | pairs with AG Grid |
| Disputes | 9% | |
| Pay Later / BNPL | 4% | named strategic priority |
| Subscriptions | 3% | nearly virgin |
| Multi-currency | 3% | under-built axis |
| JS SDK v6 | **1%** | PayPal's own recommended SDK |
| Invoicing (recurring series) | **0.5%** | essentially unused |
| Store Sync / Agent Ready | 2% | gated, but docs are public |
| Donations SDK | **0%** | zero entrants |

## AUTHORIZE is the most valuable underused primitive

An authorization holds funds without capturing. That single mechanic is the honest way to build:

- escrow and milestone payments
- deposits and partial fulfilment
- pay-on-delivery (charge only when the merchant ships)
- metered or usage-based billing with a ceiling
- lotteries and drops (hold for all, capture only winners)
- insurance and dispute bonds

**9% of the field uses it.** Every project that self-describes as "escrow" but only calls CAPTURE is doing it wrong — and a judge who knows the API will notice. If your concept can use AUTHORIZE, using it correctly is nearly free Technological Implementation credit.

## Model choice

Irrelevant to scoring, with one exception: **if your product's credibility depends on reading documents, images or messy input, use a strong vision/reasoning model and say which one.** supplora-pay names Claude because Claude reading Spanish delivery notes is the demo. A judged demo where the model misreads something is worse than a narrower demo where it is always right.

**Determinism beats cleverness.** Constrain the model's output with a schema, validate it, and fall back to a deterministic path when it fails. Show that fallback.

## SDK and packaging hygiene

- **Node/TypeScript:** `@paypal/paypal-server-sdk` (618k installs/month). The official boilerplate is Next.js + TypeScript.
- **Python:** `paypal-server-sdk` — only **31k installs/month** vs **990k for the deprecated `paypalrestsdk`**. If you reach for `paypalrestsdk`, you are using an SDK last released in Nov 2023. Judges from PayPal developer relations will know immediately.
- The `server-sdk-context-plugin-preview` repo generates SDK "skills" in six languages for agent use — a legitimate shortcut.

## Browser-facing rule for this environment

Your preview is served from a sandboxed iframe with no network access. Anything the *user-facing demo* needs must be served by your own backend through relative URLs — never have the browser call `localhost` or an external CDN. Server-side calls to PayPal are unaffected.
