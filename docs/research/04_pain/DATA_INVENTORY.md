# Data inventory — everything collected so far

**Purpose:** so that any later summary can be written from files, not from memory. Every dataset here has a refresh command.

Last updated: 1 Nov 2026 · deadline 12 Nov 2026 12:00 PT = 13 Nov 01:30 IST

---

## A. Contest facts (stable — do not refresh)

| File | What's in it |
|---|---|
| `../01_contest/DOSSIER.md` | Rules, dates, prize table, judging mechanics, hard requirements, PayPal API surface, submission checklist |
| `../RESEARCH_FRAMEWORK.md` | The 7-phase method, decision rules, the intent answer, 48-hour sprint |

---

## B. Phase 1 — Intent signals

| File | What's in it | Refresh |
|---|---|---|
| `../RESEARCH_WORKBOOK.xlsx` → `01_Intent_Signals` | 24 dated, sourced signals of what PayPal is asking for (earnings calls, CTO talks, product launches, docs changelog, award design), each with a strength score and an implication | Quarterly earnings; docs changelog weekly |

Key signals, if you only remember three: **S01/S02** (CEO: trust is our role in agentic commerce; our own services are under-attached and under-monetised) and **S08** (CTO built a Merchant AI Integration Agent that cuts certification from weeks to hours).

---

## C. Phase 2 — Competitive field

| File | What's in it | Refresh |
|---|---|---|
| `../03_field/FIELD_MAP.md` | Cluster density report: 549 public repos across 22 concept clusters, with live-demo counts and average depth per cluster | `python3 tools/scan_field.py` (~90s) |
| `../03_field/CLUSTERS.csv` | Same data, machine-readable | same |
| `../03_field/snapshots/snapshot_2026-11-01.json` | Raw per-repo metadata + classification + depth score | same, creates a new dated snapshot |
| `../03_field/competitor_map_373_repos.csv` | Earlier, deeper pass: 373 repos with licence, language, live URL, depth score, description | superseded by the above but has extra columns |
| `../03_field/repos_oneliners.txt` | One line per repo — fastest way to eyeball the whole field | static |
| `../03_field/competitor_readmes_2026-11-01.tar.gz` | All 373 READMEs, for keyword mining without re-fetching | static |

**Headline:** 549 repos. RED clusters: mandates/guardrails 86, invoicing/AR 60, reconciliation 51, disputes 49, shopping agents 47, agent trust 38, payouts 32. GREEN: a2a 9, agriculture 6, nonprofit 5, credit/BNPL 3, merchant-integration 2, insurance 2, gaming 2, remittance 1, education 1.

---

## D. Phase 3 — Pain evidence (new)

| File | What's in it | Refresh |
|---|---|---|
| `PAIN_LEDGER.csv` | **20 sourced pains**, each with audience, source, date, quantity, frequency, matching PayPal APIs and an evidence-strength score (1–5) | append as you find more |
| `EVIDENCE_NOTES.md` | The synthesis: what each dataset supports, what it does *not* support, the derivative risk on C01, and the revised ranking | rewrite after any new evidence |
| `cfpb_summary.md` / `.json` | Headline CFPB statistics with caveats | `python3 tools/analyze_cfpb.py` |
| `raw/cfpb_issues.csv` | All 65 complaint issues with counts since 2025 | `python3 tools/harvest_cfpb.py` (~2 min) |
| `raw/cfpb_products.csv` | Complaints by product, 2025+ and 2026 | same |
| `raw/cfpb_yearly.csv` | 2015→2026 trend | same |
| `raw/cfpb_responses.csv` | How PayPal resolved them (monetary / explanation) | same |
| `raw/cfpb_top_states.csv` | Geographic concentration | same |
| `raw/cfpb_sample.jsonl` | 200 full complaint records across five products | same |
| `raw/npm_downloads.json` | Monthly installs for 11 PayPal SDK packages, legacy vs current | re-query npm/pypistats |
| `raw/github_sdk_repos.json` | Archive status, last push, stars, open issues for the SDK repos | monthly |

### The four numbers worth memorising

1. **18,296** PayPal CFPB complaints since Jan 2025; **+47%** in 2026 vs all of 2025.
2. **57.3%** of them are money not accessible or not authorised; only **17.1%** end in monetary relief.
3. **~1.2M/month** legacy PayPal Python SDK installs vs **31k/month** on the replacement — the migration has not happened.
4. **Braintree Drop-in SDK deprecated 1 Oct 2026, unsupported 1 Oct 2027.**

### What is NOT available

- **CFPB published narratives** — the search API no longer returns free-text complaint narratives, only structured fields. For quotes, use the CFPB website UI per complaint, or PayPal Community / Reddit.
- **Devpost project gallery** — unpublished; `project-gallery` returns "managers haven't published this gallery yet". The GitHub scrape is the substitute.
- **PayPal Discord** — the channel where organisers answer questions. Not scraped; join manually.
- **Any primary interviews** — the highest-value evidence still missing.

---

## E. Phase 4 — Capability gaps

| File | What's in it |
|---|---|
| `../RESEARCH_WORKBOOK.xlsx` → `03_Capability_Gap` | 16 PayPal capabilities × field usage %, with gap size and intent fit |

Under-10% band worth building on: **AUTHORIZE + late capture (9%)**, **Subscriptions (3%)**, **Dispute evidence workflow (9%)**, **Transaction Search (9%)**, **Pay Later/BNPL (4%)**, **multi-currency (3%)**, **JS SDK v6 (1%)**, **Donations SDK (0%)**, **recurring invoice series (~0%)**.

---

## F. Phases 5–7 — Decision instruments

| File | What's in it |
|---|---|
| `../RESEARCH_WORKBOOK.xlsx` → `05_Concept_Pipeline` | 24 concepts, scored on the five judging criteria, with crowding and intent factors producing an EV index and rank |
| `../RESEARCH_WORKBOOK.xlsx` → `06_Gates` | 10 pass/fail gates, 6 kill criteria, 5 red-team prompts |
| `../RESEARCH_WORKBOOK.xlsx` → `07_Decision_Log` | Empty; fill from here on |
| `../RESEARCH_WORKBOOK.xlsx` → `08_Anti_Lame` | 12 default ideas with competitor counts |

Regenerate the whole workbook after editing scores: `python3 tools/build_workbook.py`.

---

## G. Reproducibility

```
python3 tools/scan_field.py        # field map    (~90s,  writes ../03_field/METHOD.md)
python3 tools/harvest_cfpb.py      # CFPB raw     (~2min, writes raw/npm_downloads.json/)
python3 tools/build_datasets.py    # all CSVs     (<1s,   writes 01/02/03/05/06/07)
python3 tools/analyze_cfpb.py      # CFPB stats   (<1s,   writes cfpb_summary.*)
python3 tools/build_workbook.py    # workbook     (<1s,   writes RESEARCH_WORKBOOK.xlsx)
```

All four are dependency-free Python 3 (standard library + openpyxl for the workbook).
