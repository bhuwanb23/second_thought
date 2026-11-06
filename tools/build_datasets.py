#!/usr/bin/env python3
"""
build_datasets.py — writes every structured dataset in the research library.

Single source of truth for the tables. Edit here, re-run, and the CSVs regenerate.
(The workbook is regenerated separately by build_workbook.py.)

Outputs
  01_contest/PRIZES.csv
  02_intent/INTENT_SIGNALS.csv
  03_field/REPOS.csv                  (from the newest field snapshot)
  05_capability/PAYPAL_API_MAP.csv
  06_sponsors/SPONSORS.csv
  07_concepts/CONCEPT_PIPELINE.csv
"""
import csv
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def write(path, header, rows):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", newline="") as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {path:42s} {len(rows)} rows")


# ----------------------------------------------------------------------
# 01 — PRIZES
# ----------------------------------------------------------------------
PRIZES = [
    ("1st Place", "Grand Prize", 12000, "cash", 1, "All eligible submissions"),
    ("2nd Place", "Grand Prize", 8000, "cash", 1, "All eligible submissions"),
    ("3rd Place", "Grand Prize", 5000, "cash", 1, "All eligible submissions"),
    ("Most Creative", "Honorable Mention", 5000, "cash", 1, "All eligible submissions"),
    ("Most Impactful", "Honorable Mention", 5000, "cash", 1, "All eligible submissions"),
    ("Best Demo Delivery", "Honorable Mention", 5000, "cash", 1, "All eligible submissions"),
    ("Best Use of PayPal + AI", "Honorable Mention", 5000, "cash", 1, "All eligible submissions"),
    ("Best Use of Agentic Commerce", "Honorable Mention", 5000, "cash", 1, "All eligible submissions"),
    ("Best Use of AG Grid - 1st", "Sponsor Prize", 5000, "cash", 1, "Submissions using AG Grid"),
    ("Best Use of AG Grid - 2nd", "Sponsor Prize", 2000, "cash", 1, "Submissions using AG Grid"),
    ("Best Use of AG Grid - 3rd", "Sponsor Prize", 1000, "cash", 3, "Submissions using AG Grid"),
    ("Best Use of APIMatic", "Sponsor Prize", 1000, "cash + 6mo Business", 3, "Submissions using APIMatic"),
    ("Best Use of Bryntum", "Sponsor Prize", 1000, "cash", 3, "Submissions using Bryntum"),
    ("Best Use of Channel3", "Sponsor Prize", 1500, "cash", 1, "Submissions using Channel3"),
    ("Best Use of Render - 1st", "Sponsor Prize", 0, "1000 Render credits", 1, "Submissions using Render"),
    ("Best Use of Render - 2nd", "Sponsor Prize", 0, "750 Render credits", 1, "Submissions using Render"),
    ("Best Use of Render - 3rd", "Sponsor Prize", 0, "500 Render credits", 1, "Submissions using Render"),
]

# ----------------------------------------------------------------------
# 02 — INTENT SIGNALS
# ----------------------------------------------------------------------
SIGNALS = [
    ("S01", "2026-10-27", 5, "Executive", "CEO names trust as PayPal's role in agentic commerce",
     "Q3'26 earnings call (Lores)",
     "\"both will have to validate that this is a real consumer that can pay, this is a real merchant that has the product... it's really all about trust and about the security\"",
     "Verification and trust layers for agent-initiated transactions, not just 'an agent buys a thing'."),
    ("S02", "2026-10-27", 5, "Executive", "CEO admits value-added services are under-monetised",
     "Q3'26 earnings call (Lores)",
     "\"Services like payouts or risk as a service or invoicing... either we have not been able to attach them properly, or we have not been able to monetize them properly. That's going to be a key priority\"",
     "A product that attaches payouts, invoicing or risk to a commerce flow answers the CEO's stated priority."),
    ("S03", "2026-10-27", 4, "Executive", "VAS attach is a named growth initiative",
     "Q3'26 earnings call",
     "\"We grew our attach from 5% to 6%... specialised sales force that will be driving attach\"",
     "An attach engine recommending and enabling the right service per merchant from their own transaction data."),
    ("S04", "2026-10-27", 4, "Executive", "Financial services are 20% of transaction margin, double-digit growth",
     "Q3'26 earnings call",
     "\"More than 20% of 2026 transaction margin dollars come from financial services, now growing double digits\"",
     "BNPL and installments at the moment of checkout. Only ~3 hackathon entries touch this."),
    ("S05", "2026-10-27", 3, "Executive", "Venmo monetisation and merchant acceptance is a top-5 priority",
     "Q3'26 earnings call",
     "\"6.7 million Venmo debit-card monthly active accounts, up more than 55%\"",
     "Venmo rail and social P2P ideas. US-facing, which limits the demo audience."),
    ("S06", "2026-09-23", 4, "Product", "PayPal supports Meta's Muse personal AI agent",
     "Press / trade coverage",
     "Muse can search and execute transactions on a consumer's behalf across PayPal merchants worldwide",
     "Agent-facing authorisation, tokenisation and consent for a consumer-side agent."),
    ("S07", "2026-10-15", 4, "Product", "Agentic commerce reaches Glance (AI shopping on 60M+ devices)",
     "Trade coverage (VP Agentic Commerce Mike Edmonds)",
     "Real-time product data plus native checkout inside a third-party AI surface, AI avatar try-on",
     "Agentic checkout embedded in a non-web surface; SMB plug-and-play into AI channels."),
    ("S08", "2026-08-10", 5, "Executive", "CTO demos a Merchant AI Integration Agent",
     "Ai4 2026 (CTO Srini Venkatesan)",
     "An agent that reads a merchant's codebase, then upgrades, validates and certifies its PayPal integration - weeks to hours",
     "A hackathon-scale version is a bullseye. Field scan: only 2 entries in this cluster."),
    ("S09", "2026-03-18", 5, "Executive", "Head of Agentic Commerce states the SMB mission",
     "NVIDIA GTC 2026 (Farhad Farahani)",
     "\"let small businesses plug and play their products and services into the agentic commerce world\"",
     "SMB agent-readiness tooling: catalog to feed to discoverable to payable."),
    ("S10", "2026-02-05", 4, "M&A", "Cymbio acquisition closes (store sync infrastructure)",
     "Press release / 10-K",
     "Multi-channel catalog orchestration; brands live on Copilot and Perplexity by Jan 2026",
     "Catalog and product-data plumbing is strategic. Channel3-style product data fits this narrative."),
    ("S11", "2026-01-08", 4, "Product", "PayPal powers Microsoft Copilot Checkout",
     "Press",
     "Store sync for inventory, branded and guest checkout and card payments inside Copilot",
     "Multi-surface agentic checkout; protocol-agnostic payment layer."),
    ("S12", "2025-10-28", 4, "Product", "Agentic commerce services launch (Agent Ready + Store Sync)",
     "PayPal Newsroom",
     "Agent Ready = accept payments on AI surfaces with fraud detection, buyer protection, dispute resolution, zero lift",
     "The strategic frame judges will recognise. Align your narrative to it explicitly."),
    ("S13", "2026-10-29", 4, "Docs", "Agent tools reference updated two weeks before deadline",
     "developer.paypal.com/ai-tools/agent-tools",
     "Remote MCP server now exposes search_product, create_cart, checkout_cart (PayPal catalog shopping tools)",
     "PayPal's own tooling is moving toward in-agent product search, cart and checkout."),
    ("S14", "2026-10-13", 4, "Docs", "Agent Ready docs updated: ACP and UCP both documented",
     "developer.paypal.com/agent-ready/overview",
     "UCP-with-PayPal path = Google Pay handler to PayPal Orders v2 API; ACP via delegated payment tokens through Braintree",
     "A faithful reference implementation of either path is legitimate, impressive and rare."),
    ("S15", "2026-10-13", 3, "Docs", "Store Sync is gated and narrow",
     "docs.paypal.ai",
     "Limited availability, access request required, US physical goods in USD only",
     "The mid-market, SMB and non-US supply side is the unsolved gap. Build the bridge they have not shipped."),
    ("S16", "2025-10-28", 4, "Standards", "PayPal contributed the 'Mandates' concept to AP2",
     "AP2 spec / trade coverage",
     "Cryptographically signed records of user intent anchoring each transaction to verifiable evidence",
     "Mandate primitives are PayPal's own idea - but 86 entries already occupy this space."),
    ("S17", "2026-04-23", 3, "Product", "Natural-language data agent for 24,000 employees",
     "Google Cloud Next '26",
     "Query company data in natural language, no SQL, encrypted credentials, audited interactions; 7.5B records migrated",
     "NL analytics over payment data resonates with leadership. Pairs with the AG Grid sponsor prize."),
    ("S18", "2026-10-27", 3, "Executive", "24M customer-service contacts resolved by AI across 190 countries",
     "Q3'26 earnings call",
     "Multilingual AI support is proven internally at scale (6 languages)",
     "Multilingual or voice AI in a payments context is culturally legible to PayPal."),
    ("S19", "2026-03-18", 3, "Product", "NVIDIA partnership: Nemotron SLM fine-tuned for commerce search",
     "GTC 2026 / NEMO-4-PAYPAL paper",
     "Product search is over 50% of agent response time; synthetic data used to train commerce agents",
     "A demo that grounds recommendations in real product data lands well."),
    ("S20", "2026-10-01", 5, "Contest", "Award design: only ONE product-specific honourable mention",
     "Devpost rules section 8",
     "'Best Use of Agentic Commerce' - $5,000, single winner. The other four HMs are generic.",
     "Agentic commerce is the single concept they chose to reward by name."),
    ("S21", "2026-10-01", 3, "Contest", "Sponsor mix skews to dashboards, timelines and product data",
     "Devpost sponsor pages",
     "AG Grid (Studio + Agent Framework), Bryntum (Gantt/Scheduler/Calendar), Channel3 (100M+ products)",
     "They expect commerce products with a real data surface. Plan one dashboard-grade view."),
    ("S22", "2026-10-12", 3, "Contest", "Webinar includes 'Build a payments dashboard without building a dashboard'",
     "Devpost resources",
     "Dedicated AG Grid session; boilerplate repo published Oct 12, 2026",
     "Payments analytics is an endorsed, low-risk surface that doubles as the sponsor-prize path."),
    ("S23", "2026-10-01", 3, "Contest", "Both official starter repos are Next.js/TypeScript plus agent context plugins",
     "github.com/paypaldev",
     "hackathon-paypal-ag-grid-boilerplate; server-sdk-context-plugin-preview (generated SDK skills in 6 languages)",
     "Following the official stack reduces integration risk and matches reviewer expectations."),
    ("S24", "2026-07-28", 3, "Executive", "Management says agentic payments matter materially 'from 2028'",
     "Q2'26 call (via PYMNTS)",
     "Near-term AI value to PayPal is cost and speed, not agent revenue",
     "Judges will not demand a 2028 business case. Favour technical depth over market-size slides."),
]

# ----------------------------------------------------------------------
# 05 — PAYPAL API MAP   (field usage % measured across 549 repos, 1 Nov 2026)
# ----------------------------------------------------------------------
API_MAP = [
    ("Orders - CAPTURE", "/v2/checkout/orders", "Standard checkout", 95, "none", 4,
     "The floor. Every entry does this. Necessary, never differentiating."),
    ("Orders - AUTHORIZE + late capture", "/v2/checkout/orders/.../authorize + /capture",
     "Hold funds, capture on proof, void on failure", 9, "BIG", 4,
     "Correct primitive for escrow, deposits, milestones and pay-per-use. Most self-described 'escrow' projects do not use it."),
    ("Webhooks + signature verification", "/v1/notifications/webhooks", "Event-driven state machines", 26, "medium", 4,
     "48% mention webhooks, only 26% verify signatures. Verification is cheap credibility."),
    ("Subscriptions", "/v1/billing/subscriptions", "Recurring revenue, plan changes", 3, "BIG", 4,
     "3% of the field. Nearly virgin territory with real strategic fit."),
    ("Invoicing - recurring series / QR / conditional rules", "/v2/invoicing/invoices",
     "Repeatable billing, in-person pay, discounts, auto-cancel", 0.5, "BIG", 3,
     "Recurring series and conditional rules are essentially unused by entrants."),
    ("Payouts (batch outbound)", "/v1/payments/payouts", "Pay N recipients at once", 29, "low", 5,
     "Named by the CEO as under-monetised. Crowded as a headline, strong as act two."),
    ("Disputes - evidence workflow", "/v1/customer/disputes", "Provide evidence, escalate, accept", 9, "medium", 4,
     "Cluster is crowded (49) but the real evidence API is seldom used."),
    ("Transaction Search / Reporting", "/v1/reporting/transactions + merchant insights",
     "Reconciliation, anomaly detection, analytics", 9, "BIG", 4,
     "Underused and pairs perfectly with the AG Grid sponsor prize."),
    ("Donations SDK", "sdk/donate", "Nonprofit giving with preset amounts", 0, "TOTAL", 3,
     "Zero entrants. Their own 'social impact' inspiration category."),
    ("Pay Later / BNPL messaging", "Pay Later SDK", "Installments at checkout", 4, "BIG", 5,
     "Named strategic priority; almost nobody touches it."),
    ("Multi-currency / FX", "currency_code across APIs", "Cross-border pricing and settlement", 3, "BIG", 4,
     "The under-built axis of nearly every concept."),
    ("JS SDK v6", "paypal.com/sdk/js", "Current client SDK", 1, "BIG", 3,
     "PayPal's own resources page links to v6; 1% of entrants use it."),
    ("Venmo rail", "JS SDK funding source", "US social payments", 3, "medium", 3,
     "Named strategic priority (Venmo monetisation)."),
    ("Agent Toolkit (~30 tools)", "@paypal/agent-toolkit", "LLM-driven PayPal operations", 22, "low", 4,
     "Common but usually shallow - one domain enabled, not a real workflow."),
    ("MCP (local or remote)", "npx @paypal/mcp or hosted", "Tool exposure to any MCP host", 16, "medium", 4,
     "Remote MCP shopping tools (search_product/create_cart/checkout_cart) are barely known."),
    ("Store Sync / Agent Ready", "agentic commerce services", "Catalog discovery + AI-surface payments", 2, "TOTAL", 5,
     "Gated, but the docs are public - a faithful reference implementation is rare and on-message."),
]

# ----------------------------------------------------------------------
# 06 — SPONSORS
# ----------------------------------------------------------------------
SPONSORS = [
    ("AG Grid", "5 prizes: $5,000 / $2,000 / 3x $1,000", 5, "Yes - $10,000 cash",
     "Use AG Studio: custom widgets, theming, layout tools, and ideally the Studio Agent Framework. Boilerplate: paypaldev/hackathon-paypal-ag-grid-boilerplate. 45-day trial.",
     "Medium - 1-2 days for a genuinely polished dashboard",
     "Trial expiry (45 days from signup) could break the judge's run before 15 Dec. Ship a licence-free fallback.",
     "BEST CASH EV. 5 slots, $10k, and every money product needs a data surface."),
    ("APIMatic", "3 x $1,000 + 6 months Business tier", 3, "Yes - $3,000 cash + subscriptions",
     "Use the Context Plugin (free, PayPal already enabled) while building; winners used it. Everyone who uses it gets 1 month Basic.",
     "Very low - under an hour",
     "Judges reward 'best use'; a dev-time-only plugin may look thin unless you also generate an SDK or portal.",
     "CHEAPEST SECOND POOL. Nearly free to qualify; ~6-10% odds of $1k."),
    ("Bryntum", "3 x $1,000", 3, "Yes - $3,000 cash",
     "Gantt / Scheduler / Calendar must be central. Trial npm packages: @bryntum/scheduler-trial.",
     "High - needs a genuine time dimension in the product",
     "Trial builds watermark and can expire; on a judge's machine that is worse than no prize.",
     "BEST RATIO IF IT FITS. Only ~23 entrants mention it, but only worth it if your product really has a timeline."),
    ("Channel3", "1 x $1,500", 1, "Yes - $1,500 cash",
     "Must actually call the API (or MCP) for search/enrichment/recommendation. Referencing it without calling fails. Promo PAYPAL-HACKATHON-2026 for 20,000 credits.",
     "Low - one API integration",
     "Single winner, so odds are worse than AG Grid's five slots despite similar effort.",
     "GOOD SUPPORTING TOOL. Natural for any commerce concept; weak as a standalone prize target."),
    ("Render", "3 prizes: $1,000 / $750 / $500 credits", 3, "Credits only - no cash",
     "Deploy on Render and use Render Workflows to orchestrate agents. $50 credits via the hackathon portal.",
     "Low - it is hosting you need anyway",
     "Zero cash. Value is the hosted demo URL, which satisfies a hard requirement.",
     "USE IT REGARDLESS of the prize: a live URL until 15 Dec is a submission requirement."),
    ("Zapier", "None", 0, "No",
     "Zapier MCP lets agents act across 9,000+ apps. 14-day Pro trial on new accounts.",
     "Low", "No prize exists. Do not spend time here for prize reasons.",
     "SKIP unless it genuinely accelerates something."),
    ("Elastic", "None", 0, "No",
     "Elasticsearch + Jina embeddings for retrieval; 14-day trial, extendable 30 days.",
     "Medium", "No prize. Trial expiry risk.",
     "SKIP. Note: 0% of entrants use it, but there is nothing to win."),
    ("KERNEL", "None", 0, "No",
     "$50 credits for cloud browsers (sub-30ms spin-up, headful Chromium, session replay).",
     "Medium", "No prize.",
     "OPTIONAL TOOL if you need browser automation in the demo."),
    ("Postman", "None", 0, "No",
     "API design/testing; PayPal collection available on Postman.",
     "Very low", "No prize.",
     "Use for your own testing if you like. Not a prize path."),
    ("Astropods", "None", 0, "No",
     "Agent operating system: declarative spec, CLI build/push, deploy via API or dashboard.",
     "Medium", "No prize.",
     "SKIP for prizes. Interesting runtime if you want managed agent hosting."),
]

# ----------------------------------------------------------------------
# 07 — CONCEPT PIPELINE
# ----------------------------------------------------------------------
CONCEPTS = [
    ("C01", "Merchant PayPal-integration doctor: reads a repo or store, finds the PayPal integration, upgrades to SDK v6 + Orders v2, validates in sandbox, certifies with a report",
     "merchant-integration", 2, 5, 5, 4, 4, 4, 5, 4),
    ("C02", "BNPL decision agent: decides at checkout whether Pay Later genuinely helps this buyer, with affordability evidence and a repayment plan",
     "credit-bnpl", 3, 5, 4, 4, 5, 5, 4, 4),
    ("C03", "SMB agent-ready kit: product feed to agent-discoverable to agent-checkoutable to order in their system, with an agent readiness score",
     "storefront-builder", 12, 5, 5, 4, 4, 4, 5, 3),
    ("C04", "VAS attach engine: reads a merchant's transactions, identifies which of payouts/invoicing/BNPL/risk to attach next, and provisions it",
     "reconciliation-reporting", 51, 5, 4, 4, 4, 4, 4, 4),
    ("C05", "Agent-transaction trust gateway: verifies a real consumer and real merchant behind each agent purchase using PayPal history signals and signed mandates",
     "agent-trust-identity", 38, 5, 5, 4, 4, 4, 4, 3),
    ("C06", "Goal-bound family remittance: voice note from recipient, itemised needs, bill verification, sender approves, split cross-border payment",
     "remittance-crossborder", 1, 3, 4, 5, 5, 5, 5, 3),
    ("C07", "A2A procurement with AUTHORIZE hold, arbiter verification and capture-or-void settlement",
     "a2a-agent-commerce", 9, 5, 5, 3, 3, 5, 3, 3),
    ("C08", "Nonprofit field-payout agent: donor-restricted funds to verified field partners via Payouts, with impact reporting and the Donations SDK",
     "nonprofit-donation", 5, 3, 4, 4, 5, 4, 4, 4),
    ("C09", "Subscription rescue for micro-merchants: spots repeat buyers in transaction history, creates the plan, manages failed renewals",
     "subscription-recurring", 21, 4, 4, 4, 4, 3, 4, 4),
    ("C10", "Accessible checkout: voice and screen-reader-first buying agent for blind and low-vision shoppers, with PayPal checkout",
     "accessibility", 27, 2, 3, 4, 5, 4, 4, 3),
    ("C11", "Parametric income cover for outdoor trades: weather trigger, automatic Payouts, funded by Subscriptions",
     "insurance-parametric", 2, 3, 4, 4, 4, 4, 4, 3),
    ("C12", "Dispute evidence agent that assembles proof from payment, delivery and message data and files it via the Disputes API",
     "dispute-chargeback", 49, 4, 5, 4, 4, 3, 4, 4),
    ("C13", "Freelancer multi-currency AR: invoices across currencies, FX-aware reminders, reconciliation",
     "invoice-ar", 60, 3, 3, 3, 4, 3, 3, 4),
    ("C14", "Gaming/esports prize distribution: verified match results to Payouts to players, entry fees via Orders",
     "gaming-esports", 2, 2, 3, 4, 3, 5, 4, 4),
    ("C15", "Farm-gate selling agent: photo to grade to fair price, buyer pays via PayPal, farmer paid same day",
     "agriculture", 6, 2, 3, 4, 5, 4, 4, 3),
    ("C16", "Education fee splitting: term fees split across guardians, reminders, school-side reconciliation",
     "education-fees", 1, 2, 3, 3, 4, 3, 3, 4),
    ("C17", "Shopping agent with a signed spend mandate and an approval gate", "mandate-guardrail", 86, 4, 3, 3, 3, 2, 4, 5),
    ("C18", "Receipt-splitting agent that invoices each friend", "receipt-split", 19, 2, 2, 3, 3, 2, 3, 5),
    ("C19", "Generic 'AI dashboard for your PayPal sales'", "reconciliation-reporting", 51, 3, 2, 3, 2, 2, 3, 5),
    ("C20", "Escrow for freelance milestones (no AUTHORIZE)", "escrow-milestone", 21, 4, 2, 3, 4, 2, 3, 4),
    ("C21", "Scam shield for seniors' P2P payments", "fraud-scam", 28, 3, 3, 4, 5, 3, 4, 3),
    ("C22", "Agent-ready storefront for social-only sellers: photos to catalog to agent-buyable", "storefront-builder", 12, 5, 4, 5, 4, 4, 5, 3),
    ("C23", "Internal-style NL analytics agent over payment data, shipped with AG Grid Studio widgets", "reconciliation-reporting", 51, 4, 4, 5, 3, 3, 4, 4),
    ("C24", "Open-source PayPal MCP server extension: exposes Invoicing/Payouts/Subscriptions as agent tools with policy enforcement", "merchant-integration", 2, 4, 5, 3, 3, 5, 3, 4),
]


def main():
    print("Writing structured datasets:")
    write("01_contest/PRIZES.csv",
          ["prize", "tier", "cash_usd", "award_kind", "winners", "eligibility"], PRIZES)
    write("02_intent/INTENT_SIGNALS.csv",
          ["id", "date", "strength_1_5", "source_type", "signal", "source", "verbatim_or_detail", "implication"], SIGNALS)
    write("05_capability/PAYPAL_API_MAP.csv",
          ["capability", "endpoint_or_package", "what_it_unlocks", "field_usage_pct", "gap", "intent_fit_1_5", "notes"], API_MAP)
    write("06_sponsors/SPONSORS.csv",
          ["sponsor", "prize", "winner_slots", "cash", "what_you_must_do", "effort", "risk", "verdict"], SPONSORS)

    # concept pipeline with computed EV
    rows = []
    for cid, name, cluster, comp, intent, tech, design, impact, innov, pres, feas in CONCEPTS:
        js = round((tech + design + impact + innov + pres) / 5, 2)
        cf = round(1 / (1 + comp / 15), 3)
        ev = round(js / 5 * cf * (0.6 + 0.1 * intent) * (feas / 5) * 100, 1)
        rows.append([cid, name, cluster, comp, intent, tech, design, impact, innov, pres, feas, js, cf, ev])
    ranked = {ev: i + 1 for i, ev in enumerate(sorted({r[13] for r in rows}, reverse=True))}
    for r in rows:
        r.append(ranked[r[13]])
        r.append("AVOID - crowded" if r[3] >= 30 else ("STRONG" if r[13] >= 30 else "possible"))
    rows.sort(key=lambda r: r[14])
    write("07_concepts/CONCEPT_PIPELINE.csv",
          ["id", "concept", "cluster", "competing_entries", "intent_fit", "tech_impl", "design", "impact",
           "innovation", "presentation", "feasibility", "judge_score", "crowd_factor", "ev_index", "rank", "verdict"], rows)

    # repos from newest snapshot
    snaps = sorted(glob.glob(os.path.join(ROOT, "03_field", "snapshots", "snapshot_*.json")))
    if snaps:
        data = json.load(open(snaps[-1]))
        rrows = []
        for r in sorted(data.values(), key=lambda x: -x.get("depth", 0)):
            rrows.append([r.get("full_name", ""), r.get("cluster", ""), r.get("depth", 0),
                          "|".join(r.get("depth_hits", [])), r.get("language", ""), r.get("license", ""),
                          r.get("live_url", ""), r.get("stars", 0), r.get("created", ""), r.get("pushed", ""),
                          (r.get("description") or "").replace("\n", " ")[:220], r.get("url", "")])
        write("03_field/REPOS.csv",
              ["repo", "cluster", "depth_0_13", "depth_markers", "language", "license", "live_url",
               "stars", "created", "pushed", "description", "url"], rrows)


if __name__ == "__main__":
    main()
