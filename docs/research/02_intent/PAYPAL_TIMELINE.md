# 02 — PayPal AI and agentic commerce timeline

Every dated signal, newest first. Use this to write the "why now" section of any one-pager, and to spot which direction they are heading next.

---

## 2026

| Date | Event | Why it matters to you |
|---|---|---|
| **29 Oct 2026** | Agent tools reference updated: remote MCP server now exposes `search_product`, `create_cart`, `checkout_cart` | PayPal's own tooling is closing the loop from discovery to payment inside an agent |
| **27 Oct 2026** | **Q3 2026 earnings call** — revenue $8.58B, ~$15.7B transaction margin dollars, attach 5%→6%, VAS under-monetised, agent trust framing | The best single source of executive admissions — see `WHAT_THEY_WANT.md` |
| 15 Oct 2026 | **Glance / InMobi** partnership: AI shopping and native checkout across 60M+ lock-screen devices; AI avatar try-on | Agentic commerce reaching non-web surfaces with mass consumer reach |
| 13 Oct 2026 | Agent Ready docs updated — **both ACP and UCP** documented; UCP path = Google Pay handler → PayPal Orders v2 | Two reference implementations are now formally specified and almost nobody has built one |
| 13 Oct 2026 | Store Sync docs: **limited availability, access request, US physical goods in USD only** | The gated/narrow scope is the single clearest gap in their own stack |
| 1 Oct 2026 | **Hackathon submission period opens** | Projects must show progress after this date |
| 1 Oct 2026 | **Braintree Drop-in SDK deprecated** | Live, dated migration pressure — drop-in still processes until 1 Oct 2027 |
| 23 Sep 2026 | **Meta Muse** — PayPal supports Meta's personal AI agent across PayPal merchants worldwide | Consumer-side agent with consent and tokenised payment |
| 10 Aug 2026 | **Ai4: Merchant AI Integration Agent** demo by CTO Srini Venkatesan | Reads a merchant's codebase, upgrades and certifies it; "hours rather than weeks"; self-learning; runs on the merchant's own infrastructure |
| 10 Aug 2026 | Ai4: one-tap purchasing mentioned as already launched | Fast checkout is table stakes, not an innovation |
| 23 Apr 2026 | **Google Cloud Next**: natural-language data agent for 24,000 employees; 7.5B records migrated | Signals appetite for NL analytics over payment data — pairs with AG Grid |
| 18 Mar 2026 | **NVIDIA GTC**: Head of Agentic Commerce Farhad Farahani on letting small businesses "plug and play" into agentic commerce; NEMO-4-PAYPAL SLM; product search >50% of agent response time | SMB agent-readiness is a stated mission, not an inference |
| 1 Mar 2026 | Enrique Lores becomes CEO | New CEO, under pressure to show AI progress — good for AI-themed pitches |
| 5 Feb 2026 | **Cymbio acquisition** — store sync / multi-channel catalog orchestration | Catalog plumbing is strategic enough to buy |
| 8 Jan 2026 | **Microsoft Copilot Checkout** powered by PayPal: Store Sync, branded + guest checkout, cards | First major third-party agent surface live |

## 2025

| Date | Event | Why it matters |
|---|---|---|
| **28 Oct 2025** | **Agentic Commerce Services launch** — Agent Ready + Store Sync; "zero lift" acceptance on AI surfaces with PayPal's fraud detection, buyer protection and dispute resolution | The narrative frame judges will recognise. Align to it. |
| Oct 2025 | OpenAI **Agentic Commerce Protocol** (ACP) with PayPal support; PayPal contributes **Mandates** to **AP2** | PayPal authored the mandate concept — pushing into it is on-strategy but crowded |
| Jun–Sep 2025 | Trustly, Hyperwallet, Pay Later expansions; ~40% BNPL user growth | BNPL is a growth engine |
| 29 Apr 2025 | **Remote MCP server + Agent Toolkit** launch | The hackathon's most-used technical surface (22% of the field) |
| 2025 | **PayPal-PHP-SDK archived** (22 Aug 2025) | Legacy SDKs are being explicitly retired |

## 2024 and earlier

| Date | Event |
|---|---|
| 2024 | PayPal begins "fastlane" and guest checkout push |
| 2023 | `paypalrestsdk` last release (1 Nov 2023) — still 990k installs/month |
| 2021–2022 | Deprecation of checkout-server-sdk in favour of Orders v2 direct REST |

---

## The pattern worth noticing

Three things are moving at once:

1. **Discovery → payment inside agents** (MCP shopping tools, Copilot, Muse, Glance)
2. **Merchant-side plumbing** being automated (Cymbio, Store Sync, the Integration Agent)
3. **Trust and mandates** as the settlement layer (AP2, ACP, buyer protection extended to agent orders)

The gap in the middle **is the long tail of merchants who cannot implement any of it.** PayPal's own Store Sync is US-only, physical-goods-only, invitation-gated. Their Integration Agent is aimed at merchants with a codebase and a developer. Neither reaches a sari shop with a Google Merchant feed, a restaurant with a paper invoice book, or a seller who only has product photos and an Instagram account.

That gap is where a hackathon project can be genuinely useful, genuinely on-message, and not a duplicate of a shipped product.
