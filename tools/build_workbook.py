#!/usr/bin/env python3
"""
build_workbook.py — regenerates research/RESEARCH_WORKBOOK.xlsx

The workbook is the operating instrument for the hackathon research funnel.
It is pre-filled with everything established on 1 Nov 2026 (intent signals,
field map, capability gaps) and contains live formulas so that as you add
candidates and scores, the ranking updates itself.

Run:  python3 tools/build_workbook.py
"""

import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "RESEARCH_WORKBOOK.xlsx")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ---------- styling helpers ----------
H1 = Font(bold=True, size=14, color="FFFFFF")
H2 = Font(bold=True, size=11, color="FFFFFF")
BOLD = Font(bold=True)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
THIN = Border(*[Side(style="thin", color="D9D9D9")] * 4)


def header(ws, row, cols, fill="1F3864", height=34):
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.font = H2
        cell.fill = PatternFill("solid", fgColor=fill)
        cell.alignment = CENTER
        cell.border = THIN
    ws.row_dimensions[row].height = height


def widths(ws, spec):
    for col, w in spec.items():
        ws.column_dimensions[col].width = w


def title(ws, text, sub=""):
    ws["A1"] = text
    ws["A1"].font = H1
    ws["A1"].fill = PatternFill("solid", fgColor="1F3864")
    ws.merge_cells("A1:H1")
    ws.row_dimensions[1].height = 26
    if sub:
        ws["A2"] = sub
        ws["A2"].font = Font(italic=True, size=10, color="555555")
        ws.merge_cells("A2:H2")


wb = Workbook()

# =====================================================================
# 00 — HOW TO USE
# =====================================================================
ws = wb.active
ws.title = "00_How to use"
title(ws, "PayPal AI Hackathon 2026 — Research Workbook",
      "Instrument set for the 7-phase funnel. Sheet order = the order you use them.")
rows = [
    ("The one-line rule", "", ""),
    ("", "A hackathon win = (what the sponsor is asking for) × (nobody has answered it well) × (you can demo it in 90 seconds). "
         "Most entrants optimise only the third term. This workbook is built to stop you doing that.", ""),
    ("", "", ""),
    ("Sheet", "What it holds", "When you use it"),
    ("01_Intent_Signals", "24 dated, sourced signals of what PayPal is demonstrably asking for — earnings calls, CTO talks, product launches, docs changelog, and the hackathon's own award design.",
     "Phase 1. Read before generating any idea. Score anything you invent against this sheet."),
    ("02_Field_Map", "Live competitor density by concept cluster, scraped from public repos. Rebuilt by tools/scan_field.py.",
     "Phase 2. Run the scanner daily. Never enter a RED cluster without a segment-level reason."),
    ("03_Capability_Gap", "Every PayPal product/API against how much of the field actually uses it.",
     "Phase 4. Pick 2–3 products, at least one in the under-10% band, so 'Technological Implementation' scores high."),
    ("04_Pain_Ledger", "Where to find documented, quantified pain — and the schema for recording it.",
     "Phase 3. You need 3 credible pains with numbers before you commit. Impact is 20% of the score."),
    ("05_Concept_Pipeline", "24 candidate concepts pre-scored, with a live EV formula and ranking. Add your own; the rank recalculates.",
     "Phases 5–6. This is where a winner gets picked."),
    ("06_Gates", "Stage-1 pass/fail gate, kill criteria, red-team questions.",
     "Phase 6–7. Apply to your top 3 before you write a line of code."),
    ("07_Decision_Log", "One row per decision, with the reason. Protects you from re-litigating on day 8.",
     "Continuously."),
    ("08_Anti_Lame", "The 12 ideas that will arrive in your head first, with the number of people who already built them.",
     "Phase 5, as a filter. If your idea is on this list, name the specific reason yours is different."),
    ("", "", ""),
    ("EV formula (in 05)", "JudgeScore/5 × CrowdingFactor × IntentFactor × Feasibility/5 × 100, where CrowdingFactor = 1/(1+Competitors/15) and IntentFactor = 0.6+0.1×IntentFit",
     "It deliberately punishes crowded spaces harder than most people are comfortable with. That is the point."),
]
r = 4
for a, b, c in rows:
    ws.cell(row=r, column=1, value=a).font = BOLD if a and not b else Font()
    ws.cell(row=r, column=2, value=b).alignment = WRAP
    ws.cell(row=r, column=3, value=c).alignment = WRAP
    if a == "Sheet":
        for i in (1, 2, 3):
            ws.cell(row=r, column=i).font = H2
            ws.cell(row=r, column=i).fill = PatternFill("solid", fgColor="2E5496")
    r += 1
widths(ws, {"A": 24, "B": 95, "C": 55})

# =====================================================================
# 01 — INTENT SIGNALS
# =====================================================================
ws = wb.create_sheet("01_Intent_Signals")
title(ws, "Phase 1 — Intent archaeology: what PayPal is demonstrably asking for",
      "Rule: primary source > blog > third-party summary. A shippped product or an exec's own words outrank a press release.")
cols = ["ID", "Date", "Signal (what happened)", "Source", "Verbatim / detail", "Strength (1-5)", "What it implies we should build"]
header(ws, 4, cols)
S = [
    ("S01", "2026-10-27", "CEO names trust as PayPal's role in agentic commerce", "Q3'26 earnings call (Lores)",
     "\"both will have to validate that this is a real consumer that can pay, this is a real merchant that has the product… it's really all about trust and about the security\"",
     5, "Verification / trust layers for agent-initiated transactions — not just 'an agent buys a thing'."),
    ("S02", "2026-10-27", "CEO admits value-added services are under-monetised", "Q3'26 earnings call (Lores)",
     "\"Services like payouts or risk as a service or invoicing… either we have not been able to attach them properly, or we have not been able to monetize them properly. That's going to be a key priority\"",
     5, "A product that ATTACHES payouts / invoicing / risk to a commerce flow is answering the CEO's stated priority."),
    ("S03", "2026-10-27", "VAS attach is a named growth initiative", "Q3'26 earnings call",
     "\"We grew our attach from 5% to 6%… specialised sales force that will be driving attach\"",
     4, "An 'attach engine' — recommending and enabling the right VAS per merchant from their own transaction data."),
    ("S04", "2026-10-27", "Financial services (BNPL, debit, credit) = 20% of transaction margin, double-digit growth", "Q3'26 earnings call",
     "\"More than 20% of 2026 transaction margin dollars come from financial services, now growing double digits\"",
     4, "BNPL / installments at the moment of checkout. Only ~3 hackathon entries touch this."),
    ("S05", "2026-10-27", "Venmo monetisation + merchant acceptance is a top-5 priority", "Q3'26 earnings call",
     "\"6.7 million Venmo debit-card monthly active accounts, up more than 55%\"",
     3, "Venmo rail / social P2P ideas. US-facing, so it limits the demo audience."),
    ("S06", "2026-09-23", "PayPal supports Meta's Muse personal AI agent", "Press / trade coverage",
     "Muse can search and execute transactions on a consumer's behalf across PayPal merchants worldwide",
     4, "Agent-facing authorisation, tokenisation and consent for a consumer-side agent."),
    ("S07", "2026-10-15", "Agentic commerce reaches Glance (AI shopping on 60M+ devices)", "Trade coverage (VP Agentic Commerce Mike Edmonds)",
     "Real-time product data + native checkout inside a third-party AI surface, AI avatar try-on",
     4, "Agentic checkout embedded in a non-web surface; SMB plug-and-play into AI channels."),
    ("S08", "2026-08-10", "CTO demos a Merchant AI Integration Agent", "Ai4 2026 (CTO Srini Venkatesan)",
     "An agent that reads a merchant's codebase, then upgrades, validates and certifies its PayPal integration — weeks to hours",
     5, "A hackathon-scale version of this is a bullseye. Field scan: only 2 entries in this cluster."),
    ("S09", "2026-03-18", "Head of Agentic Commerce states the SMB mission", "NVIDIA GTC 2026 (Farhad Farahani)",
     "\"let small businesses plug and play their products and services into the agentic commerce world\"",
     5, "SMB agent-readiness tooling: catalog → feed → discoverable → payable."),
    ("S10", "2026-02-05", "Cymbio acquisition closes (store sync infrastructure)", "Press release / 10-K",
     "Multi-channel catalog orchestration; brands live on Copilot and Perplexity by Jan 2026",
     4, "Catalog/product-data plumbing is strategic. Channel3-style product data fits this narrative."),
    ("S11", "2026-01-08", "PayPal powers Microsoft Copilot Checkout", "Press",
     "Store sync for inventory, branded + guest checkout and card payments inside Copilot",
     4, "Multi-surface agentic checkout; protocol-agnostic payment layer."),
    ("S12", "2025-10-28", "Agentic commerce services launch (Agent Ready + Store Sync)", "PayPal Newsroom",
     "Agent Ready = accept payments on AI surfaces with fraud detection, buyer protection, dispute resolution, zero lift",
     4, "The strategic frame judges will recognise. Align your narrative to it explicitly."),
    ("S13", "2026-10-29", "Agent tools reference updated 2 weeks before deadline", "developer.paypal.com/ai-tools/agent-tools",
     "Remote MCP server now exposes search_product, create_cart, checkout_cart (PayPal catalog shopping tools)",
     4, "PayPal's own agent tooling is moving toward in-agent product search + cart + checkout. A demo using these is on-message."),
    ("S14", "2026-10-13", "Agent Ready docs updated: ACP + UCP both documented", "developer.paypal.com/agent-ready/overview",
     "UCP-with-PayPal path = Google Pay handler → PayPal Orders v2 API; ACP via delegated payment tokens through Braintree",
     4, "A faithful reference implementation of either path is legitimate, impressive and rare."),
    ("S15", "2026-10-13", "Store Sync is gated and narrow", "docs.paypal.ai",
     "Limited availability, access request required, US physical goods in USD only",
     3, "The mid-market/SMB and non-US supply side is the unsolved gap. Build the bridge they haven't shipped."),
    ("S16", "2025-10-28", "PayPal contributed the 'Mandates' concept to AP2", "AP2 spec / trade coverage",
     "Cryptographically signed records of user intent anchoring each transaction to verifiable evidence",
     4, "Mandate/consent primitives are PayPal's own idea — BUT see crowding warning: 86 entries. Differentiate by segment or depth, not concept."),
    ("S17", "2026-04-23", "Natural-language data agent for 24,000 employees", "Google Cloud Next '26",
     "Query company data in natural language, no SQL, encrypted credentials, audited interactions; 7.5B records migrated",
     3, "NL analytics over payment data resonates with leadership. Pairs with the AG Grid sponsor prize."),
    ("S18", "2026-10-27", "24M customer-service contacts resolved by AI, 190 countries, 6 languages", "Q3'26 earnings call",
     "Multilingual AI support is proven internally at scale",
     3, "Multilingual/voice AI in a payments context is culturally legible to PayPal."),
    ("S19", "2026-03-18", "NVIDIA partnership: Nemotron SLM fine-tuned for commerce search", "GTC 2026 / NEMO-4-PAYPAL paper",
     "Product search is >50% of agent response time; synthetic data used to train commerce agents",
     3, "Search/recommendation latency as an explicit concern. A demo that shows grounding in real product data lands."),
    ("S20", "2026-10", "Award design: only ONE product-specific honourable mention", "Devpost rules §8",
     "'Best Use of Agentic Commerce' — $5,000, single winner. The other four HMs are generic (creative, impactful, demo, PayPal+AI).",
     5, "Agentic commerce is the single concept they chose to reward by name. Every idea should connect to it."),
    ("S21", "2026-10", "Sponsor mix skews to dashboards, timelines and product data", "Devpost sponsor pages",
     "AG Grid (Studio + Agent Framework), Bryntum (Gantt/Scheduler/Calendar), Channel3 (100M+ products)",
     3, "They expect commerce products with a real data surface. Plan one dashboard-grade view."),
    ("S22", "2026-10", "Webinar line-up includes 'Build a payments dashboard without building a dashboard'", "Devpost resources",
     "Dedicated AG Grid session; boilerplate repo published Oct 12, 2026",
     3, "Payments analytics is an endorsed, low-risk surface — and it doubles as the sponsor-prize path."),
    ("S23", "2026-10", "Both official starter repos are Next.js/TypeScript + agent context plugins", "github.com/paypaldev",
     "hackathon-paypal-ag-grid-boilerplate; server-sdk-context-plugin-preview (APIMatic-generated SDK skills for 6 languages)",
     3, "Following the official stack reduces integration risk and matches what reviewers expect to see."),
    ("S24", "2026-07-28", "Management says agentic payments matter materially 'from 2028'", "Q2'26 call (via PYMNTS)",
     "Near-term AI value to PayPal is cost and speed, not agent revenue",
     3, "Judges will not demand a 2028 business case. They want proof you understand the mechanics — so favour technical depth over market-size slides."),
]
for i, row in enumerate(S, start=5):
    for j, v in enumerate(row, 1):
        c = ws.cell(row=i, column=j, value=v)
        c.alignment = WRAP
        c.border = THIN
    st = int(row[5])
    ws.cell(row=i, column=6).fill = PatternFill("solid", fgColor={5: "C6EFCE", 4: "E2EFDA", 3: "FFF2CC"}[st])
    ws.cell(row=i, column=6).alignment = CENTER
widths(ws, {"A": 6, "B": 12, "C": 44, "D": 26, "E": 70, "F": 11, "G": 62})
ws.freeze_panes = "A5"

# =====================================================================
# 02 — FIELD MAP
# =====================================================================
ws = wb.create_sheet("02_Field_Map")
title(ws, "Phase 2 — Field map: how crowded each concept cluster is",
      "Source: tools/scan_field.py, snapshot 2026-11-01, 549 public repos. Re-run daily; the field grows ~20-35 repos/day.")
cols = ["Cluster", "Entries", "Live demos", "Avg depth (0-13)", "Crowding", "Intent fit (1-5)", "Read", "Where the opening is"]
header(ws, 4, cols)
F = [
    ("mandate-guardrail", 86, 33, 3.9, 5, "RED", "Everyone found this. Human-approval-before-payment is table stakes now, not differentiation."),
    ("invoice-ar", 60, 25, 3.4, 4, "RED", "Saturated with freelancer AR copilots. Only escape: a segment nobody serves (e.g. multi-currency B2B)."),
    ("reconciliation-reporting", 51, 22, 3.8, 4, "RED", "Crowded at the surface, but mostly shallow 'AI dashboard' plays. Depth (real Transaction Search + AG Grid) still rare."),
    ("dispute-chargeback", 49, 22, 4.9, 4, "RED", "Highest average depth of any cluster — the strong entrants are here. Avoid head-on."),
    ("shopping-agent", 47, 16, 2.3, 4, "RED", "Lowest average depth of the big clusters: lots of thin demos. Win by being the only complete product."),
    ("agent-trust-identity", 38, 20, 3.9, 5, "RED", "Max intent fit AND strong crowding. Enter only with a segment-level wedge."),
    ("payout-gig", 32, 10, 2.9, 4, "RED", "Crowded and mostly undemoed. Payouts belong as the second act, not the headline."),
    ("fraud-scam", 28, 18, 3.5, 3, "AMBER", "Consumer-protection angle; medium crowding, decent intent fit (trust)."),
    ("accessibility", 27, 13, 3.4, 2, "AMBER", "Very high Impact score potential, low strategic intent fit. Strong for 'Most Impactful'."),
    ("escrow-milestone", 21, 11, 4.2, 4, "AMBER", "Most entrants get escrow technically wrong (no AUTHORIZE). Correctness alone differentiates."),
    ("subscription-recurring", 21, 8, 3.9, 4, "AMBER", "Only 21 entries and real strategic fit (recurring revenue). Underexploited."),
    ("receipt-split", 19, 7, 2.6, 2, "AMBER", "Tired concept, shallow execution. Avoid."),
    ("storefront-builder", 12, 7, 4.7, 5, "AMBER", "High depth, low count, maximum intent fit — the SMB agent-ready story. Strongest quadrant member."),
    ("a2a-agent-commerce", 9, 3, 4.3, 5, "GREEN", "On-message and empty. Risk: abstract to demo, easy to look like a terminal."),
    ("agriculture", 6, 5, 4.2, 2, "GREEN", "Genuine white space; Impact case is easy to make, strategic fit to PayPal is weaker."),
    ("nonprofit-donation", 5, 2, 2.2, 3, "GREEN", "Donations SDK used by 0% of the field. Their own 'social impact' inspiration category is underserved."),
    ("credit-bnpl", 3, 1, 1.7, 5, "GREEN", "Almost untouched AND a named strategic priority (financial services). Best intent-to-crowding ratio on the board."),
    ("merchant-integration", 2, 1, 2.0, 5, "GREEN", "PayPal's CTO built one internally in Aug 2026. Two entries. This is the purest 'they are waiting for this' signal."),
    ("insurance-parametric", 2, 1, 1.5, 2, "GREEN", "Unusual, demo-friendly, weak strategic fit."),
    ("gaming-esports", 2, 2, 3.0, 1, "GREEN", "Probably the 'Most Creative' lane. Low intent fit."),
    ("remittance-crossborder", 1, 1, 1.0, 3, "GREEN", "Empty. Best 'Most Impactful' lane. Needs care on regulatory framing."),
    ("education-fees", 1, 0, 2.0, 2, "GREEN", "Empty but small."),
]
for i, (cl, n, lv, ad, intent, crowd, read) in enumerate(F, start=5):
    ws.cell(row=i, column=1, value=cl).font = BOLD
    ws.cell(row=i, column=2, value=n)
    ws.cell(row=i, column=3, value=lv)
    ws.cell(row=i, column=4, value=ad)
    ws.cell(row=i, column=5, value=crowd).fill = PatternFill(
        "solid", fgColor={"RED": "FFC7CE", "AMBER": "FFEB9C", "GREEN": "C6EFCE"}[crowd])
    ws.cell(row=i, column=6, value=intent)
    ws.cell(row=i, column=7, value=read).alignment = WRAP
    ws.cell(row=i, column=8, value="")
    for j in range(1, 9):
        ws.cell(row=i, column=j).border = THIN
widths(ws, {"A": 26, "B": 9, "C": 11, "D": 15, "E": 11, "F": 12, "G": 70, "H": 40})
ws.freeze_panes = "A5"

# =====================================================================
# 03 — CAPABILITY GAP
# =====================================================================
ws = wb.create_sheet("03_Capability_Gap")
title(ws, "Phase 4 — PayPal capability × field usage: where the technical white space is",
      "% = share of the 549 scanned repos whose README shows real use. Pick at least one product from the under-10% band.")
cols = ["PayPal capability", "Endpoint family", "What it unlocks", "Field usage %", "Gap", "Intent fit", "Notes"]
header(ws, 4, cols)
C = [
    ("Orders — CAPTURE", "/v2/checkout/orders", "Standard checkout", 95, "none", 4, "The floor. Every entry does this. Necessary, never differentiating."),
    ("Orders — AUTHORIZE + late capture", "/v2/checkout/orders/.../authorize|/capture", "Hold funds, capture on proof, void on failure", 9, "BIG", 4, "Correct primitive for escrow, deposits, milestones, pay-per-use. Most self-described 'escrow' projects do not use it."),
    ("Webhooks + signature verification", "/v1/notifications/webhooks", "Event-driven state machines", 26, "medium", 4, "48% mention webhooks, only 26% verify signatures. Verification is cheap credibility."),
    ("Subscriptions", "/v1/billing/subscriptions", "Recurring revenue, plan changes", 3, "BIG", 4, "3% of the field. Nearly virgin territory with real strategic fit."),
    ("Invoicing — recurring series / QR / conditional rules", "/v2/invoicing/invoices", "Repeatable billing, in-person pay, discounts, auto-cancel", 0.5, "BIG", 3, "Recurring series and conditional rules are essentially unused by entrants."),
    ("Payouts (batch outbound)", "/v1/payments/payouts", "Pay N recipients at once", 29, "low", 5, "Named explicitly by the CEO as under-monetised. Crowded as a headline, strong as act two."),
    ("Disputes — evidence workflow", "/v1/customer/disputes", "Provide evidence, escalate, accept", 9, "medium", 4, "Cluster is crowded (49) but the real evidence API is seldom used."),
    ("Transaction Search / Reporting", "/v1/reporting/transactions, merchant insights", "Reconciliation, anomaly detection, analytics", 9, "BIG", 4, "Underused and pairs perfectly with the AG Grid sponsor prize."),
    ("Donations SDK", "sdk/donate", "Nonprofit giving with preset amounts", 0, "TOTAL", 3, "Zero entrants. Their own 'social impact' inspiration category."),
    ("Pay Later / BNPL messaging", "Pay Later SDK", "Installments at checkout", 4, "BIG", 5, "Named strategic priority; almost nobody touches it."),
    ("Multi-currency / FX", "currency_code across APIs", "Cross-border pricing and settlement", 3, "BIG", 4, "The under-built axis of nearly every concept."),
    ("JS SDK v6", "paypal.com/sdk/js", "Current client SDK", 1, "BIG", 3, "PayPal's own resources page links to v6; 1% of entrants use it."),
    ("Venmo rail", "JS SDK funding source", "US social payments", 3, "medium", 3, "Named strategic priority (Venmo monetisation)."),
    ("Agent Toolkit (~30 tools)", "@paypal/agent-toolkit", "LLM-driven PayPal operations", 22, "low", 4, "Common but usually shallow — one domain enabled, not a real workflow."),
    ("MCP (local or remote)", "npx @paypal/mcp / hosted", "Tool exposure to any MCP host", 16, "medium", 4, "Remote MCP shopping tools (search_product/create_cart/checkout_cart) are barely known."),
    ("Store Sync / Agent Ready", "agentic commerce services", "Catalog discovery + AI-surface payments", 2, "TOTAL", 5, "Gated, but the docs are public — a faithful reference implementation is rare and on-message."),
]
for i, (name, ep, unlocks, pct, gap, intent, note) in enumerate(C, start=5):
    ws.cell(row=i, column=1, value=name).font = BOLD
    ws.cell(row=i, column=2, value=ep)
    ws.cell(row=i, column=3, value=unlocks).alignment = WRAP
    c = ws.cell(row=i, column=4, value=pct)
    c.alignment = CENTER
    c.fill = PatternFill("solid", fgColor="C6EFCE" if pct <= 10 else ("FFEB9C" if pct <= 30 else "FFC7CE"))
    ws.cell(row=i, column=5, value=gap).alignment = CENTER
    ws.cell(row=i, column=6, value=intent).alignment = CENTER
    ws.cell(row=i, column=7, value=note).alignment = WRAP
    for j in range(1, 8):
        ws.cell(row=i, column=j).border = THIN
widths(ws, {"A": 38, "B": 40, "C": 40, "D": 12, "E": 9, "F": 10, "G": 66})
ws.freeze_panes = "A5"

# =====================================================================
# 04 — PAIN LEDGER
# =====================================================================
ws = wb.create_sheet("04_Pain_Ledger")
title(ws, "Phase 3 — Pain ledger: documented, quantified pain beats invented pain",
      "Fill at least 5 rows before committing to a concept. 'Impact' is 20% of the score and is judged on how specific and evidenced it is.")
cols = ["ID", "Concept", "Pain (one sentence)", "Who exactly (segment, geography)", "Evidence source + date",
        "Quantified", "Frequency", "PayPal APIs", "Strength (1-5)"]
header(ws, 4, cols)

# Source of truth is 04_pain/PAIN_LEDGER.csv — edit that file, then re-run this script.
LEDGER = os.path.join(ROOT, "04_pain", "PAIN_LEDGER.csv")
pains = []
if os.path.exists(LEDGER):
    import csv as _csv
    with open(LEDGER) as f:
        for r in _csv.DictReader(f):
            pains.append((r["id"], r["concept"], r["pain"], r["audience"],
                          f'{r["evidence_source"]} ({r["evidence_date"]})',
                          r["quantified"], r["frequency"], r["paypal_apis_that_could_address_it"],
                          int(r["evidence_strength"])))
for i, row in enumerate(pains, start=5):
    for j, v in enumerate(row, 1):
        c = ws.cell(row=i, column=j, value=v)
        c.alignment = WRAP
        c.border = THIN
    st = row[-1]
    ws.cell(row=i, column=9).fill = PatternFill("solid", fgColor={5: "C6EFCE", 4: "E2EFDA", 3: "FFF2CC", 2: "FCE4D6", 1: "FFC7CE"}.get(st, "FFFFFF"))
    ws.cell(row=i, column=9).alignment = CENTER

r = 5 + len(pains) + 2
ws.cell(row=r, column=1, value="Open gaps — close these before you commit").font = BOLD
gaps = [
    "No qualitative merchant quotes: the CFPB API no longer returns complaint narratives. Pull 5-10 threads from PayPal Community and r/webdev on SDK migration, with dates.",
    "No primary interviews: one 15-minute call with a real merchant or remittance sender beats every secondary source in the video.",
    "C02 has no PayPal-specific BNPL complaint data — the CFPB pool spans multiple lenders.",
    "PayPal Discord not yet mined: organisers answer questions there and competitors telegraph intent.",
    "Field map is one snapshot; re-run tools/scan_field.py daily (field grows ~20-35 repos/day).",
]
for g in gaps:
    r += 1
    ws.cell(row=r, column=1, value="→").alignment = CENTER
    ws.cell(row=r, column=2, value=g).alignment = WRAP
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=9)

r += 2
ws.cell(row=r, column=1, value="Where to mine further pain (best → worst)").font = BOLD
srcs = [
    "1. PayPal Community forums — real users describing real failures, searchable by product.",
    "2. CFPB Consumer Complaint Database — already harvested here; refresh with tools/harvest_cfpb.py.",
    "3. App Store / Play Store reviews of PayPal, Venmo, Xoom and Braintree-powered apps, sorted newest.",
    "4. G2 / Capterra reviews of PayPal Braintree and rival PSPs — merchants describe what they wish existed.",
    "5. Reddit: r/freelance, r/smallbusiness, r/ecommerce, r/paypal — unprompted complaints.",
    "6. PayPal job postings for AI/commerce roles — a company hires for what it cannot yet do.",
    "7. World Bank / BIS / CFI for the social-impact angle when you need a global number.",
]
for src in srcs:
    r += 1
    ws.cell(row=r, column=1, value=src).alignment = WRAP
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)

widths(ws, {"A": 7, "B": 8, "C": 52, "D": 28, "E": 40, "F": 46, "G": 14, "H": 26, "I": 10})

# =====================================================================
# 05 — CONCEPT PIPELINE  (the core instrument)
# =====================================================================
ws = wb.create_sheet("05_Concept_Pipeline")
title(ws, "Phases 5–6 — Concept pipeline with live EV ranking",
      "Score 1-5 like a judge would; EV = JudgeScore/5 x CrowdFactor x IntentFactor x Feasibility/5 x 100. Impact scores on C01/C02 reflect the sourced Phase-3 evidence. See 04_pain/EVIDENCE_NOTES.md section 6 for the risk adjustment the formula cannot express.")
cols = ["ID", "Concept", "Cluster", "Competing entries", "Intent fit", "Tech impl", "Design", "Impact",
        "Innovation", "Presentation", "Feasibility", "Judge score", "Crowd factor", "EV index", "Rank", "Verdict"]
header(ws, 4, cols)

K = [
    # id, concept, cluster, competitors, intent, tech, design, impact, innov, present, feas
    ("C01", "Merchant PayPal-integration doctor: reads a repo/store, finds the PayPal integration, upgrades to SDK v6 + Orders v2, validates in sandbox, certifies with a report", "merchant-integration", 2, 5, 5, 4, 4, 4, 5, 4),
    ("C02", "BNPL decision agent: decides at checkout whether Pay Later genuinely helps this buyer, with affordability evidence and a repayment plan", "credit-bnpl", 3, 5, 4, 4, 5, 5, 4, 4),
    ("C03", "SMB agent-ready kit: product feed → agent-discoverable → agent-checkoutable → order lands in their system, with an 'agent readiness score'", "storefront-builder", 12, 5, 5, 4, 4, 4, 5, 3),
    ("C04", "VAS attach engine: reads a merchant's transactions, identifies which of payouts/invoicing/BNPL/risk to attach next, and provisions it", "reconciliation-reporting", 51, 5, 4, 4, 4, 4, 4, 4),
    ("C05", "Agent-transaction trust gateway: verifies a real consumer + real merchant behind each agent purchase, using PayPal history signals and signed mandates", "agent-trust-identity", 38, 5, 5, 4, 4, 4, 4, 3),
    ("C06", "Goal-bound family remittance: voice note from recipient → itemised needs → bill verification → sender approves → split cross-border payment", "remittance-crossborder", 1, 3, 4, 5, 5, 5, 5, 3),
    ("C07", "A2A procurement with AUTHORIZE hold, arbiter verification and capture-or-void settlement", "a2a-agent-commerce", 9, 5, 5, 3, 3, 5, 3, 3),
    ("C08", "Nonprofit field-payout agent: donor-restricted funds → verified field partners → Payouts with impact reporting, using the Donations SDK", "nonprofit-donation", 5, 3, 4, 4, 5, 4, 4, 4),
    ("C09", "Subscription rescue for micro-merchants: spots repeat buyers in transaction history, creates the plan, manages failed renewals", "subscription-recurring", 21, 4, 4, 4, 4, 3, 4, 4),
    ("C10", "Accessible checkout: voice + screen-reader-first buying agent for blind and low-vision shoppers, with PayPal checkout", "accessibility", 27, 2, 3, 4, 5, 4, 4, 3),
    ("C11", "Parametric income cover for outdoor trades: weather trigger → automatic Payouts, funded by Subscriptions", "insurance-parametric", 2, 3, 4, 4, 4, 4, 4, 3),
    ("C12", "Dispute evidence agent that assembles proof from payment + delivery + message data and files it via the Disputes API", "dispute-chargeback", 49, 4, 5, 4, 4, 3, 4, 4),
    ("C13", "Freelancer multi-currency AR: invoices across currencies, FX-aware reminders, reconciliation", "invoice-ar", 60, 3, 3, 3, 4, 3, 3, 4),
    ("C14", "Gaming/esports prize distribution: verified match results → Payouts to players, with entry fees via Orders", "gaming-esports", 2, 2, 3, 4, 3, 5, 4, 4),
    ("C15", "Farm-gate selling agent: photo → grade → fair price → buyer pays via PayPal, farmer paid same day", "agriculture", 6, 2, 3, 4, 5, 4, 4, 3),
    ("C16", "Education fee splitting: term fees split across guardians, reminders, school-side reconciliation", "education-fees", 1, 2, 3, 3, 4, 3, 3, 4),
    ("C17", "Shopping agent with a signed spend mandate and an approval gate", "mandate-guardrail", 86, 4, 3, 3, 3, 2, 4, 5),
    ("C18", "Receipt-splitting agent that invoices each friend", "receipt-split", 19, 2, 2, 3, 3, 2, 3, 5),
    ("C19", "Generic 'AI dashboard for your PayPal sales'", "reconciliation-reporting", 51, 3, 2, 3, 2, 2, 3, 5),
    ("C20", "Escrow for freelance milestones (no AUTHORIZE)", "escrow-milestone", 21, 4, 2, 3, 4, 2, 3, 4),
    ("C21", "Scam shield for seniors' P2P payments", "fraud-scam", 28, 3, 3, 4, 5, 3, 4, 3),
    ("C22", "Agent-ready storefront for social-only sellers (photos → catalog → agent-buyable)", "storefront-builder", 12, 5, 4, 5, 4, 4, 5, 3),
    ("C23", "Internal-style NL analytics agent over payment data, shipped with AG Grid Studio widgets", "reconciliation-reporting", 51, 4, 4, 5, 3, 3, 4, 4),
    ("C24", "Open-source PayPal MCP server extension: exposes Invoicing/Payouts/Subscriptions as agent tools with policy enforcement", "merchant-integration", 2, 4, 5, 3, 3, 5, 3, 4),
]
r = 5
evs = []
for (cid, name, cluster, comp, intent, tech, design, impact, innov, present, feas) in K:
    ws.cell(row=r, column=1, value=cid)
    ws.cell(row=r, column=2, value=name).alignment = WRAP
    ws.cell(row=r, column=3, value=cluster)
    ws.cell(row=r, column=4, value=comp)
    for j, v in enumerate([intent, tech, design, impact, innov, present, feas], start=5):
        c = ws.cell(row=r, column=j, value=v)
        c.alignment = CENTER
    # computed in Python so the sheet always displays correctly (no cached formulas)
    js = round((tech + design + impact + innov + present) / 5, 2)
    cf = round(1 / (1 + comp / 15), 3)
    ev = round(js / 5 * cf * (0.6 + 0.1 * intent) * (feas / 5) * 100, 1)
    ws.cell(row=r, column=12, value=js)
    ws.cell(row=r, column=13, value=cf)
    ws.cell(row=r, column=14, value=ev)
    evs.append(ev)
    for j in range(1, 17):
        ws.cell(row=r, column=j).border = THIN
    r += 1

# rank (descending EV) and verdict
ranked = {ev: i + 1 for i, ev in enumerate(sorted(set(evs), reverse=True))}
for i, ev in enumerate(sorted(evs, reverse=True)[:0]):  # placeholder, no-op
    pass
for i in range(5, r):
    ev = ws.cell(row=i, column=14).value
    ws.cell(row=i, column=15, value=ranked[ev]).alignment = CENTER
    comp_v = ws.cell(row=i, column=4).value
    ws.cell(row=i, column=16, value=("AVOID — crowded" if comp_v >= 30 else ("STRONG" if ev >= 30 else "possible"))).alignment = CENTER
    ws.cell(row=i, column=15).font = BOLD if ranked[ev] <= 5 else Font()
    ws.cell(row=i, column=14).font = BOLD if ranked[ev] <= 5 else Font()

# conditional formatting on EV index
from openpyxl.formatting.rule import ColorScaleRule
ws.conditional_formatting.add(f"N5:N{r-1}",
                              ColorScaleRule(start_type="min", start_color="FFC7CE",
                                             mid_type="percentile", mid_value=50, mid_color="FFEB9C",
                                             end_type="max", end_color="C6EFCE"))
widths(ws, {"A": 6, "B": 62, "C": 26, "D": 11, "E": 9, "F": 9, "G": 8, "H": 8, "I": 9, "J": 11, "K": 11,
            "L": 11, "M": 11, "N": 10, "O": 7, "P": 17})
ws.freeze_panes = "C5"

r += 3
ws.cell(row=r, column=1, value="Scoring guide").font = BOLD
guide = [
    ("Intent fit", "How directly does it answer a signal in 01_Intent_Signals? 5 = a CEO/CTO said it out loud. 1 = unrelated."),
    ("Tech impl", "Will the PayPal usage look non-trivial? Count products, not endpoints."),
    ("Design", "Can this become a coherent product with real screens, not a demo script?"),
    ("Impact", "Is there a named audience with a documented problem?"),
    ("Innovation", "Distinct from the 549 repos and from the 12 in 08_Anti_Lame."),
    ("Presentation", "Can a stranger understand it in 90 seconds of video?"),
    ("Feasibility", "Solo, ~10 days, with sandbox only."),
    ("EV index", "JudgeScore/5 × CrowdFactor × IntentFactor × Feasibility/5 × 100. Max ~110."),
]
for k, v in guide:
    r += 1
    ws.cell(row=r, column=1, value=k).font = BOLD
    ws.cell(row=r, column=2, value=v).alignment = WRAP
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)

# =====================================================================
# 06 — GATES
# =====================================================================
ws = wb.create_sheet("06_Gates")
title(ws, "Phases 6–7 — Gates, kill criteria and red team",
      "Apply to your top 3 concepts. A concept must pass EVERY Stage-1 gate and have zero unexplained kill criteria.")
header(ws, 4, ["Gate", "Question", "Pass condition", "C01", "C02", "C03"])
G = [
    ("G1 — Stage 1", "Is PayPal API usage central, not decorative?", "Removing PayPal would break the product. A judge sees the call in the demo.", "", "", ""),
    ("G2 — Stage 1", "Is the AI doing real work?", "A model reads unstructured input or makes a decision. Not a hardcoded string.", "", "", ""),
    ("G3 — Stage 1", "Does it run in sandbox end to end?", "A full loop completes: create → approve → capture → webhook → confirm.", "", "", ""),
    ("G4 — Stage 2", "Is there a named audience with a documented pain?", "Pain ledger has ≥1 sourced, quantified row.", "", "", ""),
    ("G5 — Stage 2", "Is it visibly different from the 549 repos?", "You can name the closest 3 repos and the exact difference.", "", "", ""),
    ("G6 — Stage 2", "Can it be demoed in 90 seconds?", "You can storyboard the clicks right now, without building it.", "", "", ""),
    ("G7 — Risk", "Are you blocked by gated access?", "No dependency on Store Sync, ACP credentials, or production approval.", "", "", ""),
    ("G8 — Risk", "Does a trial licence break the judge's run?", "App works with a licence-free fallback.", "", "", ""),
    ("G9 — Risk", "Is the regulatory framing safe?", "No licence implied, no claim to move money you cannot move.", "", "", ""),
    ("G10 — Risk", "Can one person finish it in 10 days?", "Every feature maps to a day in the plan.", "", "", ""),
]
for i, row in enumerate(G, start=5):
    for j, v in enumerate(row, 1):
        c = ws.cell(row=i, column=j, value=v)
        c.alignment = WRAP
        c.border = THIN
widths(ws, {"A": 16, "B": 46, "C": 60, "D": 8, "E": 8, "F": 8})

r = 17
ws.cell(row=r, column=1, value="Kill criteria — any ONE of these should end the concept").font = BOLD
kills = [
    "You cannot name the closest three competitor repos and say precisely how you differ.",
    "The demo requires a licence, an approval, or a partner you don't have.",
    "The 'AI' step could be replaced by three if-statements without anyone noticing.",
    "You need more than one PayPal product to work before anything is visible on screen.",
    "Explaining the value takes longer than 30 seconds of speech.",
    "The concept only makes sense if the judge reads the README.",
]
for k in kills:
    r += 1
    ws.cell(row=r, column=1, value="✕").alignment = CENTER
    ws.cell(row=r, column=2, value=k).alignment = WRAP
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)

r += 2
ws.cell(row=r, column=1, value="Red team — ask an LLM these, verbatim, about your top concept").font = BOLD
red = [
    "You are a PayPal product manager judging this hackathon. Here is the concept and the video script. Give me the three sentences you would write in your scoring notes to justify a low score.",
    "List every way this product could appear to use PayPal meaningfully but actually be superficial. Be specific and unkind.",
    "What is the most likely way this demo fails live in front of a judge?",
    "Which of the 549 competitor repos would a judge consider a near-duplicate, and why?",
    "Rewrite my one-line pitch as a sceptical judge would say it back to me. If it sounds generic, say so.",
]
for q in red:
    r += 1
    ws.cell(row=r, column=1, value="→").alignment = CENTER
    ws.cell(row=r, column=2, value=q).alignment = WRAP
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)

# =====================================================================
# 07 — DECISION LOG
# =====================================================================
ws = wb.create_sheet("07_Decision_Log")
title(ws, "Decision log", "One row per decision. On day 8 you will want to know why you chose this, and you will not remember.")
header(ws, 4, ["Date", "Decision", "Alternatives considered", "Reason", "Reversible?", "Revisit on"])
for i in range(5, 25):
    for j in range(1, 7):
        ws.cell(row=i, column=j).border = THIN
widths(ws, {"A": 12, "B": 40, "C": 40, "D": 60, "E": 12, "F": 12})

# =====================================================================
# 08 — ANTI-LAME
# =====================================================================
ws = wb.create_sheet("08_Anti_Lame")
title(ws, "The anti-lame filter", "These 12 ideas will arrive in your head first, because they are the ones everyone else had. Built already:")
header(ws, 4, ["Idea you will think of", "Already built", "Why it fails to differentiate"])
A = [
    ("AI shopping agent that buys things for you within a budget", 86, "Mandate/guardrail is the single most crowded cluster. Your version will be the 87th."),
    ("Agent that chases unpaid invoices and sends reminders", 60, "Saturated, and the demo is a list of emails. Nothing visibly happens."),
    ("Escrow for freelance milestones", 21, "Most entrants don't even use AUTHORIZE, so it demos as 'we took the money and gave it back'."),
    ("Dispute/chargeback defence copilot", 49, "Highest average depth cluster — the strong entrants already live here."),
    ("Receipt photo → split between friends → invoice each", 19, "Tired, and it makes PayPal look like a payments utility rather than a platform."),
    ("AI dashboard for your PayPal sales", 51, "'Generic dashboard' scores low on Innovation no matter how pretty. Only wins as a secondary surface for a specific decision."),
    ("Tipping / creator payout page", 32, "Crowded, and payout-only projects under-use the platform."),
    ("Scam shield for elderly relatives", 28, "Noble, but usually demos as a warning banner."),
    ("Parametric weather insurance", 2, "Rare, but the AI is thin and the regulatory framing is risky."),
    ("A2A agents that haggle then pay", 9, "On-message but abstract; risks looking like a terminal window for 3 minutes."),
    ("Accessible checkout for blind users", 27, "High Impact potential, but needs genuine accessibility expertise to avoid looking patronising."),
    ("Invoice a client from a WhatsApp chat", 60, "The single most-repeated demo in the field."),
]
for i, row in enumerate(A, start=5):
    for j, v in enumerate(row, 1):
        c = ws.cell(row=i, column=j, value=v)
        c.alignment = WRAP
        c.border = THIN
    ws.cell(row=i, column=2).alignment = CENTER
widths(ws, {"A": 52, "B": 14, "C": 80})

wb.save(OUT)
print(f"wrote {OUT}")
