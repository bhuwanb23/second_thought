# Phase 3 — Pain evidence: what the data actually says
*Harvested 1 Nov 2026. All figures reproducible with the scripts in `tools/`.*

This is the evidence file. It is deliberately blunt about what the data supports and what it doesn't, because the fastest way to lose a judging round is to overstate a number you half-understood.

---

## 1. What was collected

| Source | What it is | Volume | Where |
|---|---|---|---|
| **CFPB Consumer Complaint Database** | Every formal US consumer complaint against PayPal Holdings, structured by product/issue/response/state/date | **44,036 all-time; 18,296 since Jan 2025** | `raw/cfpb_*.csv`, `cfpb_summary.md` |
| **npm + PyPI registry statistics** | Live install volume for every PayPal SDK, legacy vs current | 11 packages | `raw/npm_downloads.json` |
| **GitHub SDK repositories** | Archive status, last push, stars, open issues for the SDK families | 15 repos | `raw/github_sdk_repos.json` |
| **PayPal's own statements** | CTO's description of the Merchant AI Integration Agent; Braintree deprecation schedule | 2 primary sources | `PAIN_LEDGER.csv` P03/P04 |
| **World Bank RPW + RBI** | Remittance costs by corridor; India inflow totals | Issue 54 (Q3 2025); FY2025-26 | `PAIN_LEDGER.csv` P14–P17 |
| **BNPL research** | CFPB, Federal Reserve, LendingTree late-payment and loan-stacking data | 2024–2026 | `PAIN_LEDGER.csv` P07–P13 |

**20 pains, each with a source, a date and a number.** Full ledger: `PAIN_LEDGER.csv`.

---

## 2. The macro finding (applies to every concept)

PayPal's formal US complaint volume is accelerating and the pain is extremely concentrated:

- **10,884 complaints in 2026 to date** vs **7,412 in all of 2025** — **+47%**, with two months of the year still to run.
- **The top five issues are 68% of everything filed.**
- **57.3%** of complaints are one of: unauthorised transaction, cannot access funds in wallet, fraud/scam, or other transaction problem.
- Only **17.1%** end in monetary relief. **61.4%** are "closed with explanation".

**What this supports:** the "trust and access" framing PayPal's CEO uses is not marketing — it is where the complaints are. If your product touches disputes, evidence, access-to-funds or fraud, you have real ground under you.

**What it does not support:** any claim about *rates*. Complaints are self-selected; they measure what motivates people to file, not how often PayPal fails. Cite counts and shares, never "X% of users are affected." A judge who works in risk will catch that instantly.

---

## 3. C01 — Merchant PayPal-integration doctor

### The evidence is unusually strong

| Finding | Number | Source |
|---|---|---|
| Legacy `paypalrestsdk` (PyPI, labelled **Deprecated**) | **990,808 downloads/month** | pypistats.org, 1 Nov 2026 |
| `paypalhttp` transport (legacy stack) | **971,282/month** | pypistats.org |
| Legacy `@paypal/checkout-server-sdk` (npm) | **234,050/month** | npm registry |
| New `@paypal/paypal-server-sdk` (npm) | 618,851/month | npm registry |
| New **Python** Server SDK (APIMatic-generated) | **30,749/month** | pypistats.org |
| Replacement SDK family | 6 languages, created 2026, 7–70 GitHub stars each | github.com/paypal |
| Braintree Drop-in SDK | **deprecated 1 Oct 2026, unsupported 1 Oct 2027** | PayPal Braintree docs |

Roughly **1.2 million legacy Python installs a month against 31 thousand on the replacement.** The migration wave has not started yet, and Braintree has just put a date on it.

### And PayPal has already described the product

From PayPal's own newsroom, 10 August 2026, on the CTO's Ai4 keynote:

> "PayPal's Merchant AI Integration Agent, which **reads a merchant's codebase, understands its PayPal integration, and automatically upgrades, validates, and certifies compliance with the latest version.** For years, that kind of upgrade required a developer or integration specialist to compete with a merchant's own product roadmap; with the integration agent, the same certification **now takes hours rather than weeks.**"

That is a problem statement *and* a solution shape, in PayPal's own words, four months before the deadline.

### ⚠️ The risk this creates — read this before committing to C01

**PayPal already built this.** A judge in that room may have worked on it. If your project reads as a hackathon reimplementation of an internal product, the reaction is not "how clever" — it is "we shipped that in August."

Three ways to not be derivative, in increasing order of safety:

1. **Open-source + self-serve version for the long tail.** Theirs runs "on the merchant's own computing infrastructure" — it is an enterprise motion. The 990k-downloads-a-month long tail of small integrators has no such tool.
2. **Extend to the dimension they did not claim: agentic readiness.** Not just "does it use the current SDK" but "can an AI agent safely transact through this integration" — does it support AUTHORIZE, verified webhooks, idempotency, mandates? That is a different report, and it lands squarely on the "Best Use of Agentic Commerce" award.
3. **Make the output an artefact, not a task.** Their agent performs an upgrade; yours produces a portable certification report that the merchant can hand to a client, a marketplace, or an acquirer. Different buyer.

If none of those three feels like a real product to you, C01 is the wrong choice despite the evidence.

---

## 4. C02 — BNPL decision agent

### The evidence

| Finding | Number | Source |
|---|---|---|
| BNPL users who paid late in the past year | **47%** (2026), up from 41% (2025), 34% (2024) | LendingTree 2026 |
| Held multiple simultaneous BNPL loans | **63%** (33% across multiple lenders) | CFPB, Jan 2025 |
| Say BNPL caused them to overspend | **68%** | LendingTree 2026 |
| Say BNPL was the only way they could afford it | **54–59%** | LendingTree / Motley Fool |
| Say a BNPL payment triggered an overdraft or NSF fee | **11%** | Federal Reserve SHED 2025 |
| Total BNPL lending, 2025 | **~$160B**; pay-in-4 up ~80% | Federal Reserve, Jun 2026 |
| PayPal's exposure | one of five firms CFPB ordered to produce BNPL data; **reports missed payments to CRAs** where Affirm/Afterpay do not | CFPB 2021; FRBP |

### What this supports

There is a clean, defensible product thesis here: **the decision to offer Pay Later is currently made with no model of whether this specific buyer can carry it.** The harm numbers are not about the product existing — they are about it being offered indiscriminately. An agent that answers "should this person use Pay Later for this purchase, and what does the repayment look like against their actual cash flow" is:

- a **financial-services** story (20% of PayPal's transaction margin, double-digit growth)
- an **innovation** story (3 of 549 entrants)
- and a genuinely uncomfortable, credible impact story.

**Caveat to state honestly:** the 47% figure is self-reported; the CFPB's dollar-weighted charge-off rate is under 2%. Both are true and they measure different things. If your video says "47% of BNPL users default", you are wrong and a judge may know it. The correct sentence is: *"47% of BNPL users report paying late at least once, while dollar-weighted losses stay under 2% — the harm is concentrated in small, repeated, badly-timed payments, which is exactly the pattern a per-purchase affordability check could prevent."*

That single sentence is probably worth more than the rest of your impact slide.

---

## 5. C06 — Goal-bound family remittance

### The evidence

| Finding | Number | Source |
|---|---|---|
| Global average cost to send $200 | **6.36%** vs SDG target **3%** | World Bank RPW Issue 54, Q3 2025 |
| Banks vs digital | **14.99%** vs **4.59%** | World Bank RPW |
| Cost to send $200 to India | **5.30%** average | World Bank RPW |
| Cheapest three services in the same corridor | **3.29%** (SmaRT) | World Bank RPW |
| India inflows, FY2025-26 | **$144.8B**, +16% YoY, record | RBI |
| Source countries | US **27.7%**, UAE **19.2%** | RBI |
| A $400/month sender's exposure | ~**$147/year** lost to the average-vs-best gap | derived from RPW |

### What this supports

The sharpest version of the impact argument is **not** "remittances are expensive". It is:

> **The good price already exists in every corridor — 3.29% — and the average person pays 6.36%. The gap is not a technology problem, it is a delivery problem.**

That is a genuinely interesting thesis, and it is untouched in the field (1 of 549).

### Where it is weak

- **Intent fit is only 3.** Remittances are not in PayPal's stated 2026 priorities; agentic commerce, financial services and VAS attach are.
- **Regulatory framing.** You are not a money transmitter. Position it as an intent-and-evidence layer over PayPal, never as a remittance licence.
- **The AI is doing less work** than in C01/C02 unless you commit to multilingual voice + bill verification.

---

## 6. Revised ranking, with the new evidence

| Concept | Evidence strength | Judging ceiling | Key risk | Verdict |
|---|---|---|---|---|
| **C02 — BNPL decision agent** | 4/5 (strong, but self-report caveats) | High | Must resist moralising; must be genuinely useful at checkout | **Now the best balance.** On-message, thin field, strong harm data, no derivative risk |
| **C01 — Integration doctor** | **5/5** (the best-evidenced idea on the board) | High (tiebreak-friendly) | **PayPal built it in August.** Derivative risk is real | Keep only if you take one of the three escape routes in §3 |
| **C06 — Goal-bound remittance** | 5/5 on impact, 2/5 on intent | **Highest** (Impact 5, Innovation 5) | Intent fit 3; regulatory framing; hardest AI work | The "Most Impactful" play. Choose it only if story and craft are your edge |

**What would change my mind:** if you can put the C01 certification output in front of a real merchant's broken integration and generate a report they'd actually pay for, the derivative risk evaporates and C01 wins outright. That's a one-day test, and it's worth doing before you commit.

---

## 7. What is still missing

| Gap | Why it matters | How to close it |
|---|---|---|
| No *qualitative* merchant quotes | The CFPB API no longer exposes published narratives; numbers without voices read dry in a video | Pull 5–10 threads from PayPal Community + r/webdev on SDK migration; quote them with dates |
| No primary interviews | One 15-minute call with a merchant or a migrant worker outperforms any secondary source in the video | Someone you know who runs a store, or a freelancer with clients abroad |
| C02 has no PayPal-specific complaint data | The CFPB BNPL complaints are pooled across lenders | Check whether PayPal's 6-month plan appears in the CFPB product "Payday loan…" bucket; else rely on the Fed/LendingTree data |
| Nothing yet from the PayPal Discord | Organisers and sponsors answer questions there; it is also where competitors telegraph intent | Join, read the hackathon channels, ask one question about sandbox limits |
| Field map is a single snapshot | 549 repos today, growing ~20–35/day | Re-run `tools/scan_field.py` daily |
