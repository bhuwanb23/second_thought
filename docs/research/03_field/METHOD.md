# 03 — How the field scan works

`tools/scan_field.py` → `docs/research/03_field/snapshots/snapshot_YYYY-MM-DD.json` → `FIELD_MAP.md`, `CLUSTERS.csv`, `REPOS.csv`

Re-runnable and idempotent. Each run adds a snapshot; diffs between snapshots become `NEW_ENTRANTS.csv`.

---

## What it collects

Queries the GitHub search API for Devpost-linked PayPal hackathon repos, combining terms like `paypal hackathon 2026`, `paypalaihackathon`, `paypal agentic commerce`. For each repo it records: name, description, language, licence, stars, created/pushed dates, homepage, and the README.

**Latest snapshot:** 549 repos (1 Nov 2026 15:10 UTC). Of these, 373 have a readable description, 230 have a live demo URL, 363 READMEs archived to `competitor_readmes_2026-11-01.tar.gz`.

## The depth score (0–13)

A keyword score over the README + description for evidence of real PayPal integration rather than a mention:

| Marker | Points | Why it counts |
|---|---|---|
| `webhook` | 1 | Server-side event handling |
| `sigverify` | 1 | Signature verification — a real security step |
| `authorize` | 1 | Uses AUTHORIZE, not just CAPTURE |
| `payouts` | 1 | Outbound money |
| `invoicing` | 1 | Second product surface |
| `subscriptions` | 1 | Recurring billing |
| `disputes` | 1 | Post-transaction |
| `toolkit` | 1 | Agent Toolkit |
| `mcp` | 1 | Model Context Protocol |
| `aggrid` | 1 | Sponsor integration |
| `license` | 1 | Licence visible — a submission requirement |
| `idempotency` | 1 | Production-thinking |
| `liveurl` | 1 | Actually deployed |

**This is a proxy, not a measurement.** A repo can score 0 and be excellent; a repo can score 8 by listing keywords it does not implement. Treat depth as a sorting signal for who to read, not a ranking of quality.

**Distribution:** most repos cluster at 2–5. Roughly 40 score ≥ 7. Fourteen score ≥ 9.

## The clusters

Each repo is assigned one cluster by keyword priority. Cluster assignment is single-label and rule-based, so a repo doing two things appears once.

| Cluster | Count | Read |
|---|---|---|
| `mandate-guardrail` | 86 | **Saturated.** Consent gates, spend limits, approval UIs |
| `invoice-ar` | 60 | Dense |
| `reconciliation-reporting` | 51 | Dense — the "dashboard" default |
| `dispute-chargeback` | 49 | Dense |
| `shopping-agent` | 47 | Dense |
| `agent-trust-identity` | 38 | Dense |
| `fraud-scam` | 28 | Moderate |
| `accessibility` | 27 | Moderate, but low technical depth |
| `subscription-recurring` | 21 | Moderate |
| `escrow-milestone` | 21 | Moderate |
| `receipt-split` | 19 | Moderate |
| `payout-gig` | 17 | Moderate |
| `storefront-builder` | 12 | **Thin — and the 12 include some of the best repos in the field** |
| `a2a-agent-commerce` | 9 | Thin but occupied by excellent entries |
| `agriculture` | 6 | Thin |
| `nonprofit-donation` | 5 | Thin |
| `credit-bnpl` | 3 | **Very thin — and it is a named strategic priority** |
| `merchant-integration` | 2 | **Very thin — and the CTO built a product for it** |
| `insurance-parametric` | 2 | Thin |
| `gaming-esports` | 2 | Thin |
| `education-fees` | 1 | Thin |
| `remittance-crossborder` | 1 | **Thinnest cluster with the largest underlying market** |

## Caveats — state these whenever you quote a number

1. **Coverage is incomplete.** Only repos that GitHub search surfaces and that mention the hackathon/Devpost are counted. Private repos and unlinked projects are invisible.
2. **Cluster counts are keyword-derived**, so they over-count casual mentions and under-count anything described unusually.
3. **Many entrants will still pivot.** The final submission count will differ.
4. **A thin cluster is not automatically good.** `remittance-crossborder` has 1 repo partly because remittance is hard and the narrative fit to PayPal's developer stack is weaker than for agent shopping.
