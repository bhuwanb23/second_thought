# CFPB complaint data — PayPal Holdings, Inc

Harvested 2026-11-01 from the CFPB public Consumer Complaint Database (consumerfinance.gov). Every figure below is reproducible with `python3 tools/harvest_cfpb.py && python3 tools/analyze_cfpb.py`.

## Headline

- **18,296** complaints since 1 Jan 2025; **44,036** all-time.
- **10,884** complaints in 2026 to date vs **7,412** in all of 2025 — **+47%**, with roughly two months of 2026 still to run.
- The top five issues account for **68%** of everything filed.
- **61%** are closed with explanation; only **17%** result in monetary relief.

## Top issues (since 2025-01-01)

| Issue | Complaints | Share |
|---|---|---|
| Unauthorized transactions or other transaction problem | 3,509 | 19.2% |
| Trouble accessing funds in your mobile or digital wallet | 3,153 | 17.2% |
| Fraud or scam | 2,536 | 13.9% |
| Managing an account | 1,688 | 9.2% |
| Managing, opening, or closing your mobile wallet account | 1,611 | 8.8% |
| Other transaction problem | 1,282 | 7.0% |
| Problem with a purchase shown on your statement | 605 | 3.3% |
| Money was not available when promised | 568 | 3.1% |
| Problem with a lender or other company charging your account | 485 | 2.7% |
| Other service problem | 309 | 1.7% |

## Products

| Product | Complaints since 2025 |
|---|---|
| Money transfer, virtual currency, or money service | 13,817 |
| Checking or savings account | 2,539 |
| Credit card | 870 |
| Debt collection | 396 |
| Prepaid card | 311 |
| Payday loan, title loan, personal loan, or advance loan | 207 |
| Credit reporting or other personal consumer reports | 120 |
| Debt or credit management | 36 |

## Yearly trend

| Year | Complaints |
|---|---|
| 2015 | 1,040 |
| 2016 | 1,157 |
| 2017 | 870 |
| 2018 | 987 |
| 2019 | 1,628 |
| 2020 | 2,497 |
| 2021 | 5,411 |
| 2022 | 3,381 |
| 2023 | 3,834 |
| 2024 | 4,143 |
| 2025 | 7,412 |
| 2026 | 10,884 (partial — YTD) |

## Response mix

- Closed with explanation: **61%**
- Closed with monetary relief: **17%**

## Top states

CA (2,315), TX (1,502), FL (1,434), NY (1,214), PA (718), GA (651), IL (578), NC (537)

## Caveats you must state if you cite this

- CFPB complaints are **self-selected**: they show what motivates people to file, not the base rate of failure. Never present a complaint count as a failure rate.
- They cover **US consumers only**.
- Complaint volume partly tracks account growth, not just product quality.
- Published narratives are not exposed by the search API; only the structured fields are available programmatically.
