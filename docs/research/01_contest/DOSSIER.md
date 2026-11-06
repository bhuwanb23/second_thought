# PayPal AI Hackathon 2026 — Full Research Dossier
**"Build What's Next with PayPal and AI"** · prepared 1 Nov 2026 · deadline in ~11 days

Everything below is from primary sources (Devpost listing, Official Rules, all 10 sponsor pages, PayPal developer docs, and a scrape of 373 public competitor repos), cross-checked against the notes you already had. Where your notes were slightly off, it's flagged.

---

## 0. The 60-second version

- **The contest is won on two separate tables.** Table 1 = 8 main awards (3 grand + 5 honorable mentions) contested by everyone. Table 2 = 15 sponsor awards contested only by people who use that sponsor's tool. You may win one from each table. **Table 2 has ~10–20× better odds per entrant.** Almost nobody is optimizing for it.
- **The field is large but shallow-ish and highly clustered.** 26,065 registered. I could already identify **373 public repos** claiming this hackathon 11 days before the deadline. **Only 80 (21%) have a live demo URL. 38 (10%) have no license at all** — i.e. already disqualified on a hard requirement.
- **The concept space is saturated in exactly one place:** "AI shopping agent + budget/mandate + PayPal checkout." ~72 repos. If you build that, you are competing with 70 other people for judges' attention and for the single "Best Use of Agentic Commerce" award.
- **The white space is in recurring money.** Subscriptions API appears in **3.3%** of entries, Pay Later/BNPL **3.6%**, PayPal's Donations SDK **0%**, recurring invoice series **0%**, multi-currency/FX **2.8%**, QR-code invoicing **3%**. Everyone is doing one-shot `create_order → pay_order`.
- **Design and Presentation are 40% of the score**, and "Best Demo Delivery" is its own $5,000 prize. Most entries are unstyled prototypes with a 4-minute screen recording. This is the cheapest place to buy points.
- **Recommended play:** one product with a real audience, using 3–4 PayPal products including at least two of the under-used ones, plus **one** sponsor tool chosen for prize odds (AG Grid is the best cash/odds trade; APIMatic is nearly free to add as a second pool), shipped live on a URL that stays up until **15 Dec**.

---

## 1. Corrections & confirmations vs. the notes you had

| Your note | Verified reality |
|---|---|
| Deadline Nov 12, 12:00 pm PT ≈ 1:30 AM IST Nov 13 | ✅ Correct. Rules: Submission Period **Thu 1 Oct 2026 9:15 am PT → Thu 12 Nov 2026 12:00 pm PT**. Devpost displays this as "Nov 12 @ 3:00pm EST". IST = **13 Nov, 01:30**. |
| ~26,000 registrants | ✅ **26,065** on the listing today. |
| $67,500 cash + $2,250 Render credits = $69,750 | ✅ Exactly right. Prize table sums: 25,000 main + 25,000 HM + 10,000 AG Grid + 3,000 APIMatic + 3,000 Bryntum + 1,500 Channel3 = **$67,500 cash**, + $2,250 Render credits. |
| APIMatic = 3 × $1k + 6 months Business | ✅ 3 winners × $1,000. Also: **every** participant who uses the Context Plugin gets **1 month of Basic free** (claim form on the sponsor page). |
| Bryntum = 3 × $1k | ✅ |
| Channel3 = 1 × $1.5k | ✅ single winner, $1,500 |
| Render = credits only | ✅ $1,000 / $750 / $500 Render credits. No cash. |
| No prizes for Zapier, Elastic, Postman, KERNEL, Astropods | ✅ Confirmed against §8 Prizes. They are resource/credit partners only (Zapier 14-day Pro trial, KERNEL $50 credits, Elastic 14-day trial + 30-day extension). **Using them wins you nothing directly.** |
| Project gallery hidden | ✅ Still hidden ("managers haven't published this gallery yet"). **But the competitor set is partially recoverable from GitHub** — see §6. |
| Stage 1 pass/fail, Stage 2 five equally weighted criteria, AI-driven analysis possible | ✅ Verbatim in rules §6. Tie-break: highest score on the **first** criterion = Technological Implementation. |
| Stacking: one grand/HM + one sponsor | ✅ Exact wording: "up to one (1) Grand Prize and one (1) Sponsor Prize **OR** one (1) Honorable Mention Prize and one (1) Sponsor Prize." |

Two things your notes didn't have, both important:

1. **"The Project must be available free of charge and without any restriction, for testing, evaluation and use by Sponsor, Administrator and Judges until the Judging Period ends."** Judging ends **15 Dec 2026, 8:00 am PT**. Your hosted demo and your sandbox credentials must still work on 15 December. Trials that expire (AG Studio 45-day, Bryntum 45-day, Elastic 14-day) are a real hazard — plan a license-free fallback.
2. **Multiple submissions are allowed** ("each Submission must be unique and substantially different"). Almost nobody does this. It is a legitimate way to enter a second, differently-targeted project into a different sponsor pool. Only worth it if you have a second person.

---

## 2. Prize economics — where the money actually is

### 2.1 The full table (23 award slots)

| Award | Cash | Winners | Pool contested by |
|---|---|---|---|
| 1st Place | $12,000 | 1 | everyone |
| 2nd Place | $8,000 | 1 | everyone |
| 3rd Place | $5,000 | 1 | everyone |
| Most Creative | $5,000 | 1 | everyone |
| Most Impactful | $5,000 | 1 | everyone |
| Best Demo Delivery | $5,000 | 1 | everyone |
| Best Use of PayPal + AI | $5,000 | 1 | everyone |
| Best Use of Agentic Commerce | $5,000 | 1 | everyone |
| AG Grid 1st / 2nd / 3rd | $5,000 / $2,000 / $1,000 ×3 | 5 | AG Grid users only |
| APIMatic | $1,000 ×3 (+6mo Business) | 3 | APIMatic users only |
| Bryntum | $1,000 ×3 | 3 | Bryntum users only |
| Channel3 | $1,500 | 1 | Channel3 users only |
| Render | $1,000 / $750 / $500 credits | 3 | Render users only |

**Main table: 8 slots. Sponsor table: 15 slots.**

### 2.2 Rough odds (my estimate, with reasoning)

Public repos referencing the hackathon: **373 as of today**, growing maybe 20–35/day → likely **600–800 repos by the deadline**. Not every submission has a public repo tied to the name, and not every repo becomes a submission. My working estimate for **valid submissions: 700–1,200**. Of those, a meaningful slice fails Stage 1 (no real PayPal call, mockup-only, no license).

| Target | Slots | Est. eligible pool | Rough odds |
|---|---|---|---|
| Any main award | 8 | ~900 | ~0.9% |
| 1st Place | 1 | ~900 | ~0.1% |
| Any sponsor award | 15 | tool users only | — |
| AG Grid any prize | 5 | est. 60–90 real users | **~6–8%** |
| Bryntum any prize | 3 | est. 25–40 real users | **~8–12%** |
| APIMatic any prize | 3 | est. 30–50 real users | **~6–10%** |
| Channel3 | 1 | est. 40–60 real users | ~2% |
| Render | 3 | est. 80–120 users | credits only |

Note the AG Grid numbers are the most attractive *cash*: $10,000 spread over 5 slots, and the tool is genuinely useful for any money product. Bryntum/APIMatic have better ratios but 5× smaller prizes.

### 2.3 The optimal stacking

Max realistic outcome: **one main award + one sponsor award**. So:

> **A single project should be aimed at: (a) 1–2 specific main awards, and (b) exactly one sponsor pool, chosen by odds — not by enthusiasm.**

Do not try to satisfy four sponsors. Multiple sponsor tools do not multiply prizes, they only multiply your *eligibility*, and each one costs build time and dilutes the narrative. Two is the practical ceiling (one primary for prize, one nearly-free).

---

## 3. Judging, decoded

**Stage 1 (pass/fail).** "Reasonably fits the theme and reasonably applies the required APIs/SDKs." Translated: they will open your repo/README looking for an actual PayPal API call and an actual model call. Two failure modes kill people here: (a) PayPal integration is a decorative "Buy" button that never calls the API in the demo, (b) the "AI" is a hardcoded string.

**Stage 2 (five criteria, equal weight).**

| Criterion | What it rewards | How to actually score it |
|---|---|---|
| **Technological Implementation** | Depth and skill across PayPal + AI. "non-trivial implementation." **Also the tiebreaker.** | Multiple PayPal products, not just Orders. Server-side token handling. Webhooks with signature verification. Idempotency keys. Real auth (OAuth client_credentials), not hardcoded tokens. Error/retry paths. |
| **Design** | "complete, coherent product experience — not just a technical proof of concept" | Consistent visual system, empty states, loading states, a settings/setup path, seeded demo data so a judge sees a populated product in 5 seconds. This is 20% of your score and the cheapest 20% to earn. |
| **Potential Impact** | "credible, specific case for solving a real problem for a real audience" | Name the audience precisely ("UK sole-trader roofers who invoice 3–8 clients/month"), cite a number, show the product doing the thing for that audience. Vague "helps everyone" = low. |
| **Innovation** | Novelty vs. existing concepts and vs. other entries | Hard to get in the crowded lane (§6). Easy in white space. |
| **Presentation** | Video shows it working end-to-end; problem/who/why; clarity | Storyboard it. 2:45 max. Problem (20s) → who (10s) → live product (100s) → how it works / PayPal products used (30s) → why it matters (15s). No music with copyright. |

**Why "Technological Implementation" being the tiebreaker matters:** scores in a large field cluster heavily. Ties are common. The team with real webhooks, real signature verification, and two PayPal products beats the team with one Orders call on identical scores.

**Automated AI analysis is explicitly permitted.** So does your README contain the words a classifier is looking for — API names, tool names, architecture? Write for both a human and a machine: an explicit "PayPal integration" section listing every endpoint and every AI tool, and a "Tools used" section.

---

## 4. Hard requirements — the disqualification checklist

| # | Requirement | Failure mode I observed in the wild |
|---|---|---|
| 1 | PayPal **sandbox** integration, **central** to the product | A "powered by" badge with no API call |
| 2 | Real AI functionality | Prompt hardcoded / mock responses |
| 3 | **Public repo**, all source + assets + run instructions | Missing `.env.example`, secrets committed |
| 4 | **Open-source license visible in the About section** (repo sidebar) | 38 of 373 repos have **no license** → auto-fail. Adding `LICENSE` file is not enough; GitHub must detect it and show it in About. |
| 5 | **Working demo** — hosted URL *or* run instructions good enough for a judge to run it | Mockup/Figma/static screenshots = explicit fail |
| 6 | **Available free, unrestricted, until 15 Dec 2026** | Trial expiry, key rotation, credit exhaustion |
| 7 | **YouTube video, public, < 3 min**, shows the app running on its real device | Unlisted link, 3:40, no product footage |
| 8 | **No third-party trademarks / copyrighted music** without permission | A pop song in the background is the classic killer |
| 9 | **Document the AI tools** and how they're used | Missing "Tools" field on the form |
| 10 | English throughout | — |
| 11 | Existing projects: **significant updates after 1 Oct 2026** | Reused old repo with no changelog evidence |
| 12 | No financial or preferential support from PayPal/Devpost | — |
| 13 | Eligibility: not Brazil, Quebec, Russia, Crimea, Cuba, Iran, NK, or OFAC-sanctioned | India (you) is fine |

**Practical note for you in India:** use the sandbox only. Create your sandbox **business** account with country United States and currency USD (sandbox onboarding lets you pick), and a separate **personal** sandbox buyer account in the US — PayPal will not let an account pay itself, and a currency/country mismatch makes sandbox checkout fail in confusing ways. Never point a demo at production.

---

## 5. The PayPal surface map — what you can actually build in sandbox

This is the part most entrants get wrong. They use `create_order` + `pay_order` and stop. Here is the full menu, with a note on how much of the field is using each one (measured across the 373 repos).

### 5.1 Core REST APIs (all sandbox-available)

| Capability | Endpoint family | What it unlocks | Field usage |
|---|---|---|---|
| Orders (intent=CAPTURE) | `/v2/checkout/orders` | Standard checkout. Server create → approval link/JS SDK → capture | universal |
| **Orders (intent=AUTHORIZE)** | `/v2/checkout/orders` + `/authorize` + `/capture` | **Hold funds now, capture later, void on failure.** The correct primitive for escrow, deposits, milestones, pay-per-answer, agent guardrails | **8.6%** ← differentiator |
| Payments / refunds | `/v2/payments/captures/{id}/refund` | Refunds, partial refunds | common |
| Subscriptions | `/v1/billing/products`, `/v1/billing/subscriptions` | Recurring revenue, plan changes, cancel flows | **3.3%** ← big gap |
| Invoicing | `/v2/invoicing/invoices` | Invoices, **reminders**, **QR codes**, **conditional rules** (early-payment discount, auto-cancel), **recurring invoice series** | 33% mention, but recurring series/QR ≈ **0–3%** ← gap |
| Payouts | `/v1/payments/payouts` | Batch outbound payments to N recipients — contractors, gig workers, refunds, splits | 29% |
| Disputes | `/v1/customer/disputes` | List, get, **provide evidence**, accept claim, escalate | 30% mention; evidence workflows ~9% |
| Transaction Search / Reporting | `/v1/reporting/transactions` | Reconciliation, analytics, anomaly detection | **9.4%** ← gap |
| Webhooks | `/v1/notifications/webhooks` | Real event-driven behaviour + signature verification | 48% mention, 26% verify signatures |
| Donations SDK | `sdk/donate` | Nonprofit giving button with amounts | **0%** ← total white space |
| Pay Later messaging / BNPL | Pay Later SDK | Installments messaging at checkout | **3.6%** / 1.7% |
| JS SDK v6 | `paypal.com/sdk/js` | Current client SDK | **0.8%** ← almost nobody uses v6 |
| Venmo | via JS SDK | US consumer rail | 3% |
| Payment Links / Buttons, QR | low-code | Merchant onboarding, in-person | ~8% |

### 5.2 PayPal's AI layer

**Agent Toolkit** (`@paypal/agent-toolkit` on npm, `paypal-agent-toolkit` on PyPI) — ~30 prebuilt function-calling tools across 7 domains, with adapters for OpenAI Agents SDK, Vercel AI SDK, LangChain, CrewAI, Bedrock, and MCP. Tool domains:

- **Payments**: `create_order`, `get_order`, `pay_order`, `create_refund`, `get_refund`
- **Catalog**: `create_product`, `list_product`, `show_product_details`
- **Invoicing**: `create_invoice`, `list_invoices`, `get_invoice`, `send_invoice`, `send_invoice_reminder`, `cancel_sent_invoice`, `generate_invoice_qr_code`
- **Subscriptions**: plans + subscriptions (create/list/show/update/cancel)
- **Disputes**: `list_disputes`, `get_dispute`, `accept_dispute_claim`
- **Shipment tracking**: create/get/update
- **Reporting**: `get_merchant_insights`, `list_transaction`

Used by **21.5%** of repos. Config is explicit about which actions you enable — a nice "least privilege for the agent" story if you surface it in the UI.

**MCP server** — local (`npx -y @paypal/mcp`) or PayPal's hosted remote server. Beyond the toolkit tools, the **remote** MCP server adds three shopping tools: `search_product` (gift-card catalog), `create_cart`, `checkout_cart`. That is a *ready-made agentic-commerce loop inside PayPal itself* — very few entrants know these exist. 15.7% of repos mention MCP.

**Agentic commerce (Store Sync / Agent Ready)** — the strategic story PayPal wants told:

- **Store Sync**: push your product catalog to PayPal so AI surfaces (Perplexity, Copilot, ChatGPT, PayPal's own shopping agent) can discover it and drop orders into your fulfillment system. **Limited availability, access request, US physical goods in USD only.** Not a 10-day build. Can't be the core of your project; can absolutely be a slide.
- **Agent Ready**: merchants accept payments from AI assistants via **ACP** (OpenAI/ChatGPT) or **UCP** (Google AI Mode/Gemini). UCP-with-PayPal path = Google Pay payment handler → **PayPal Orders v2 API**. Public docs, updated 13 Oct 2026. Public docs mean you can build a faithful *reference implementation* of the merchant side, which is legitimate and impressive.
- Field usage: `store sync` 2.2%, `agent ready` 1.9%, `ACP` 1.1%, `UCP` 1.1%, `AP2` 3%.

### 5.3 What "meaningful use" looks like to a PayPal judge

Tiered, from the Stage-1 bar upward:

1. `create_order` → redirect → `capture` (the floor, and ~70% of the field)
2. + webhook-driven state machine with signature verification
3. + a second, *deliberately chosen* product (AUTHORIZE/capture, Subscriptions, Invoicing, Payouts)
4. + Agent Toolkit or MCP so an LLM drives the API rather than your hand-written calls
5. + reporting/reconciliation loop closing the story (money in → insight → action)

Aim for 4–5. Tier 5 is where "Best Use of PayPal + AI" lives.

---

## 6. Competitive landscape — I reconstructed the field

The Devpost gallery is unpublished, but **373 public GitHub repos** already reference this hackathon. I scraped them all (repository metadata + 362 READMEs) and scored each on 13 technical markers. Appendix: `competitor_map.csv` (sorted by depth).

### 6.1 Shape of the field

| Signal | Value |
|---|---|
| Public repos | 373 |
| Repos created in Oct 2026 | 360 |
| Live demo URL | **80 (21%)** |
| **No license at all** | **38 (10%)** — already disqualified |
| Median README length | 7.1 KB |
| Max GitHub stars | 3 — **no frontrunner has emerged** |
| Language | TypeScript 153, Python 99, JS 63, HTML 14, Java 7, Go 5 |
| Webhook usage | 48% mention, 26% signature-verify |
| Agent Toolkit | 21.5% · MCP 15.7% · JS SDK v6 **0.8%** |

Depth distribution (0–13 markers): 34 repos score 0, 46 score 1, 41 score 2, 59 score 3, 51 score 4, 57 score 5, then a thin tail — 22 at 6, 22 at 7, 12 at 8, 10 at 9, 5 at 10, 2 at 11, **1 at 12**. **The top ~5% is genuinely competent; the median is a weekend prototype.**

### 6.2 Concept clusters (saturation map)

| Cluster | Est. count | Verdict |
|---|---|---|
| AI shopping agent / buy-for-me / spend mandate | **~72** | 🔴 Brutal. Do not enter without a hard differentiator. |
| Invoicing, AR, freelancer billing | 44 | 🔴 Crowded |
| Storefront / checkout builder | 42 | 🟠 Crowded but room for a specific niche |
| Payouts / gig / contractor pay | 29 | 🟠 Crowded |
| Spend caps, budget mandates, guardrails | 25 | 🔴 Very crowded (overlaps #1) |
| Disputes / chargeback defence | 24 | 🟠 Crowded and hard to demo convincingly |
| Escrow / milestone release | 17 | 🟠 Crowded; nearly all do it wrong (no AUTHORIZE) |
| Receipt splitting | 16 | 🟠 |
| Insurance / parametric cover | 14 | 🟢 Thin, unusual |
| Fraud / scam shield | 16 | 🟠 |
| Healthcare cost sharing | 7 | 🟢 Thin |
| Churn-save / subscription rescue | 6 | 🟢 Thin |
| Accessibility (blind/low-vision buyers) | 6 | 🟢 Thin, high Impact score |
| Nonprofit treasury / charity | 4 | 🟢 **Thin** |
| **Agent-to-agent (A2A) commerce** | 2 | 🟢 **Very thin** |
| Cross-border remittance / FX | **~1** | 🟢 **Empty** |
| Education / tuition / school fees | 2 | 🟢 Empty |
| Agriculture | 1 | 🟢 Empty |
| Tax / GST set-aside | 1 | 🟢 Almost empty |
| **Gaming / esports prize distribution** | **0** | 🟢 **Empty** |

### 6.3 What the strongest existing entries look like

These are real repos, named so you can study the bar:

- `Speedyzyzz/sentinel-prooflayer` — "agent mandate control plane + causal pre-dispute evidence graph" (12 depth markers, the most complete I found)
- `antonmareo10/supplora-pay` — accounts-payable agent: reads supplier invoices with Claude, verifies against delivery note + price history, pays via PayPal after owner approval
- `Chinorab/mandate` — signed purchase mandates, consent gate before every payment, merchant dispute evidence
- `rohith1005H/AgentBaazar` — "agent-ready commerce for every small store, on PayPal"
- `RAK2315/shopfront-agent` — social-only seller's photos → PayPal-backed store that AI agents can buy from
- `KaraAliOsman/paylet` — fair limited drops, one PayPal hold per account, agents welcome via MCP
- `ma-za-kpe/stood` — evidence-gated release for staged payments
- `JacobEGarcia/allowance` — spending mandate, Channel3 search, AG Grid ledger, static GitHub Pages demo (this is the quality of a *typical* competent entry: no backend, keys in localStorage)
- `Thomas-Wood-Eng/sightline` — voice/keyboard-first shopping for blind and low-vision buyers
- `yijigao/proofpay` — escrow for agent work, funds captured only when objective checks pass

**Reading the field:** the words *mandate*, *escrow*, *evidence*, *guardrail*, *approval gate* appear in a large fraction of entries. 77% of READMEs mention an approval step. **"Human-in-the-loop approval before payment" is no longer a differentiator — it is table stakes.** Your innovation has to come from somewhere else.

### 6.4 Therefore: three ways to be differentiated

1. **Domain white space** — go where there are 0–4 competitors (remittance, recurring/subscription money, nonprofit treasury, A2A, education fees, gaming payouts, accessibility) and do the boring craft well.
2. **Technically under-used primitives** — AUTHORIZE + delayed capture, webhook state machines with signature verification, Subscription plan changes, recurring invoice series, Transaction Search reconciliation, Payouts batches, JS SDK v6. 8% or less of the field touches most of these.
3. **Product completeness** — real auth-free but *scoped* demo, seeded data, populated dashboard, empty/error/loading states, mobile layout. "Design" is 20% and 70% of entries are shadcn-default prototypes.

---

## 7. Concept directions, scored

Four concepts built from the gap analysis. Each is scored 1–5 on the five criteria (equal weight), with prize paths and build cost.

### A. "Kin" — cross-border family remittance with goal-bound money
*Remitter in the Gulf/US sends money that is *earmarked*: school fees, medicine, rent, a shop restock. Recipient records a 20-second voice note in Tamil/Hindi ("Amma's BP tablets are out, school fees due on the 5th, ₹4,000"). The agent transcribes, itemises, cross-checks against a photo of the bill, proposes an allocation inside the sender's monthly cap, the sender approves on their phone, and PayPal moves the money — split, currency-aware, with a durable receipt both sides can see. Recurring support runs as a PayPal Subscription; one-off extras as an invoice with a QR code.*

| Criterion | Score | Why |
|---|---|---|
| Technological Implementation | 4 | Orders v2 (multi-currency) + Subscriptions + Invoicing (QR, recurring series) + Payouts + webhooks + multimodal AI (voice + vision). 4 PayPal products, 3 of them under-used. |
| Design | 4 | Chat-plus-ledger product; strong visual story (two phones, two languages) |
| Potential Impact | **5** | ~$900B/yr remittance market, India is the #1 recipient, fees + FX opacity + scam risk are documented harms. Extremely credible, specific audience. |
| Innovation | **5** | ~1 competitor in 373. |
| Presentation | 5 | Emotionally legible in 90 seconds; a real human in the video makes it memorable. |

Prize paths: **Most Impactful**, Best Use of PayPal + AI, maybe Most Creative. Sponsor: AG Grid for the sender's spend ledger, Render for hosting. Real risk: judges may question regulatory framing — solve by positioning as a *goal-and-evidence layer on top of PayPal*, not a money transmitter, and never simulating a license you don't have.

### B. "Khata" — recurring revenue agent for micro-merchants *(renamed: "Tab")*
*Subscriptions and recurring invoice series are used by 3.3% and 0% of the field respectively. A merchant tool that turns one-off customers into recurring ones: agent reads a merchant's PayPal transaction history (Transaction Search), identifies repeat buyers, proposes a membership plan, creates the PayPal product + plan, drafts the message, and manages churn — with a dashboard showing MRR, failed renewals, and recoverable revenue.*

| Criterion | Score | Why |
|---|---|---|
| Tech | 4 | Subscriptions API + Transaction Search + Payouts for refunds + webhooks (`BILLING.SUBSCRIPTION.PAYMENT.FAILED`) |
| Design | 5 | A real MRR dashboard is a natural AG Grid showcase → strong Design + AG Grid prize |
| Impact | 4 | Micro-merchants live on repeat revenue; concrete and measurable |
| Innovation | 3 | Churn-save niche exists (6 repos) but the *create-the-plan-from-history* angle is fresh |
| Presentation | 4 | Dashboard demos read well on video |

Prize paths: AG Grid (stacked with a main award), Best Use of PayPal + AI.

### C. "Agent-Ready Store" reference implementation — the merchant side of agentic commerce
*Everyone built the shopping agent. Almost nobody built the store. Ship a drop-in "make my shop buyable by any AI assistant" service: generates a machine-readable product feed from a merchant's existing catalog, exposes an agent-facing checkout session API modelled on the public ACP/UCP docs, settles with PayPal Orders v2 (AUTHORIZE → capture), and reports what agents bought and what they abandoned. Demo two agents (one shopping, one merchant-side) negotiating a purchase.*

| Criterion | Score | Why |
|---|---|---|
| Tech | **5** | Protocol implementation + Orders v2 + token-delegation model + MCP server exposing the store |
| Design | 4 | Merchant console + agent transcript view |
| Impact | 4 | Long-tail merchants are invisible in AI channels — the exact problem Store Sync exists to solve |
| Innovation | 4 | Directly on PayPal's strategic roadmap; 2–4 competitors |
| Presentation | 5 | "Two agents transacting" demos beautifully |

Prize paths: **Best Use of Agentic Commerce** (the most on-message project in the field), Best Use of PayPal + AI, AG Grid. Risk: the lane's most obvious read ("shopping agent") is crowded, so the *merchant-side* framing must be unmistakable in the first 15 seconds of the video.

### D. "A2A settlement" — agent-to-agent procurement with verifiable settlement
*Two agents transact: a buyer agent (needs 10,000 synthetic labelled images) and a seller agent (generates them). Negotiation, an AUTHORIZE hold, deliverable verification by a third "arbiter" agent, capture on pass / void on fail, evidence trail. Uses Orders AUTHORIZE + capture + void, which only 8.6% of the field touches.*

| Criterion | Score | Why |
|---|---|---|
| Tech | **5** | Genuinely hard, correct primitives, and the ONLY project type where "agentic commerce" is literal |
| Design | 4 | Needs careful UI to not look like a terminal |
| Impact | 3 | Real (agent economies are coming) but harder to make visceral |
| Innovation | **5** | 2 competitors |
| Presentation | 3 | Abstract; risk of a boring video |

Prize paths: Best Use of Agentic Commerce, Most Creative. **Highest ceiling, highest risk, worst demo-per-hour.**

### Recommendation

**Ship A or C.** They are near-opposite risks:

- **A (remittance) has the highest expected value** because "Most Impactful" is a *whole $5k award* that a specific, human, well-researched story can win outright, and Impact is also 20% of the general score. The empty competitive lane means Innovation scores high for free. Downside: requires the AI to do real work (multilingual voice, bill vision) and you must not fumble the regulatory framing.
- **C (agent-ready store) has the highest floor** because it is the most on-message project possible for a PayPal-hosted hackathon and the technical work is squarely in your control. Downside: the lane is conceptually crowded, so execution and framing must be sharp.

**Either way, hedge with a sponsor:** AG Grid is the highest-EV sponsor ($10k across 5 slots, and both concepts naturally produce a ledger/analytics surface). APIMatic costs you ~1 hour for a second pool — install the Context Plugin during the build, screenshot it in the README, and claim the free month. **Do not touch Bryntum unless the product genuinely has a timeline** — trial watermarks on a judge's machine are worse than the $1k.

---

## 8. Eleven-day build plan

Two-track: build first, *submission artifacts second*, and never let the artifacts be the last thing you do.

| Day | Date | Objective |
|---|---|---|
| 0 | Sat 1 Nov | Decide concept. Register on Devpost. Create PayPal developer app, sandbox business (US/USD) + sandbox personal buyer. Claim Channel3 key + Render $50 credits. Verify a curl `create_order` → capture round-trip works. |
| 1 | Sun 2 Nov | Repo skeleton, MIT LICENSE (verify it shows in About), `.env.example`, CI-less one-command run. Deploy "hello world" to Render **today** — the URL must exist before the code. |
| 2–3 | Mon–Tue 3–4 Nov | Core PayPal integration: OAuth, order creation, capture, webhook endpoint with signature verification, idempotency, retry. Get a real sandbox transaction through it and screenshot it. |
| 4–5 | Wed–Thu 5–6 Nov | The AI layer: tool-calling loop over the Agent Toolkit, or a custom tool schema. Log every step in a trace you can show in the UI — the trace *is* your Technological Implementation evidence. |
| 6 | Fri 7 Nov | Second PayPal product (AUTHORIZE/capture, Subscriptions, or Invoicing). Payouts if it fits. |
| 7 | Sat 8 Nov | **Design day.** Visual system, seeded demo data, empty/loading/error states, the AG Grid surface, mobile layout. Do not code logic today. |
| 8 | Sun 9 Nov | Cold-start test: a stranger runs it from the README alone. Fix every gap. Rotate keys, scrub secrets, check the license badge. |
| 9 | Mon 10 Nov | Record the video. 2:45. Script first, record second. Re-record twice. Upload to YouTube **public**. |
| 10 | Tue 11 Nov | Write the Devpost description, the Tools section, the "how it was built" section. Second reviewer reads it cold. |
| 11 | Wed 12 Nov | **Submit by 8:00 PM IST.** Leave 5 hours of buffer before the 01:30 IST cutoff on the 13th. Devpost + traffic spikes at deadlines; edits lock at close. |

**Absolute deadline discipline:** the last 6 hours before a Devpost close are when the site struggles. Submit on the 12th, in your evening, not at 1 AM.

---

## 9. The video is worth $5,000 on its own

"Best Demo Delivery" is a *separate* $5k award, and Presentation is 20% of every other score. Storyboard:

| Time | Beat | Notes |
|---|---|---|
| 0:00–0:15 | The problem, stated as a fact with a number | No logo intro, no "hi my name is". Start mid-sentence. |
| 0:15–0:25 | Who it's for — one specific person | Ideally show them, or their name and their work |
| 0:25–0:35 | What you built, one sentence | "X is a Y that does Z using PayPal and [model]." |
| 0:35–1:55 | **The product, live, unedited** | Real clicks. Real PayPal checkout. Real sandbox confirmation. Real webhook arriving. |
| 1:55–2:15 | Under the hood: the architecture shot | Show the PayPal endpoints + tools you called. Judges screenshot this. |
| 2:15–2:35 | Impact + the ask | Who benefits, how much |
| 2:35–2:45 | Close | Repo + live URL on screen |

Rules: no copyrighted music (use a royalty-free track or none), no other companies' logos, no unlicensed movie clips. Screen-record at 1080p minimum, zoom the UI so text is legible on a laptop screen at 720p, cursor highlights on. Caption the key claims — judges may watch muted.

---

## 10. Risk register

| Risk | Likelihood | Mitigation |
|---|---|---|
| Trial license (AG Studio/Bryntum/Elastic) expires before judges run it | Medium | Ship a license-free fallback; make the trial-only feature optional behind an env var; document it |
| Hosted demo dies between now and 15 Dec | Medium | Deploy on Render with the $50 credits; add a `/health` endpoint; set a calendar reminder for 1 Dec to verify |
| Sandbox credentials leak in the repo | Medium | Only ever in env vars; run a secret scan before the final push; rotate once |
| Buyer/seller sandbox account conflict breaks checkout | High on first attempt | Separate business (seller) and personal (buyer) sandbox accounts, matching currency/country |
| Webhooks can't reach localhost | Certain | ngrok/cloudflared tunnel, or use the Webhooks Simulator to fire events by hand |
| Project looks like the other 70 shopping agents | High if you ignore §6 | Pick from the white space, or nail the merchant-side/agent-to-agent framing |
| Video over 3 min or accidentally unlisted | Medium | Hard cut at 2:45; check the link in a private browser window |
| Scope creep kills the design day | High | Freeze features on day 7. Design and artifacts are worth 40% of the score. |

---

## 11. Pre-submission checklist (pin this)

- [ ] PayPal sandbox call visible in the live demo, not just in code
- [ ] AI model call visible in the live demo, not just in code
- [ ] `LICENSE` file present **and** licence visible in the repo's About sidebar
- [ ] Repo public, README has: what it is, screenshot, live URL, architecture, setup in ≤5 commands, `.env` var list, "PayPal APIs used", "AI tools used"
- [ ] No secrets in git history
- [ ] Hosted demo URL works in a fresh incognito window, no login wall, seeded with data
- [ ] Demo works from the README alone (test with someone who hasn't seen the code)
- [ ] YouTube link public + < 3:00 + shows the app running
- [ ] No copyrighted music, no third-party logos
- [ ] Devpost "Tools" field lists every model/service and what it did
- [ ] Description names the audience and the problem in the first two sentences
- [ ] Submitted with ≥5 hours of buffer
- [ ] Calendar reminder: verify the live demo on 1 Dec (judging opens) and 14 Dec (judging closes)

---

## Appendix

- `competitor_map.csv` — all 373 public repos with language, license, live URL, creation date, README depth score (0–13) and description. Sorted by depth. Rebuild the picture any day by re-scraping; the field grows ~20–35 repos/day.

**Sources:** Devpost listing, Official Rules (§1 dates, §3 eligibility, §4 requirements, §5 modifications, §6 judging, §8 prizes), all 10 sponsor detail pages, PayPal developer docs (`ai-tools/agent-tools`, updated 29 Oct 2026; `agent-ready/overview`, updated 13 Oct 2026; agentic-commerce overview), `github.com/paypal/agent-toolkit`, `github.com/paypaldev/hackathon-paypal-ag-grid-boilerplate`, `github.com/paypaldev/server-sdk-context-plugin-preview`, PayPal newsroom agentic-commerce announcement, plus the GitHub scrape described in §6.
