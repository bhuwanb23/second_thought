#!/usr/bin/env python3
"""
analyze_cfpb.py — derive headline statistics from the harvested CFPB data.

Reads the raw CSVs written by harvest_cfpb.py and writes:
  04_pain/cfpb_summary.json   machine-readable headline stats
  04_pain/cfpb_summary.md     human-readable summary with the numbers
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "04_pain", "raw")
OUT = os.path.join(ROOT, "04_pain")


def read_csv(name):
    with open(os.path.join(RAW, name)) as f:
        return list(csv.DictReader(f))


def main():
    yearly = {int(r["year"]): int(r["complaints"]) for r in read_csv("cfpb_yearly.csv")}
    issues = [(r["issue"], int(r["count_2025plus"])) for r in read_csv("cfpb_issues.csv")]
    products = [(r["product_or_subproduct"], int(r["count"]), r["window"])
                for r in read_csv("cfpb_products.csv") if r["window"] == "2025+"]
    responses = [(r["company_response"], int(r["count_2025plus"])) for r in read_csv("cfpb_responses.csv")]
    states = [(r["state_or_zip"], int(r["count_2025plus"])) for r in read_csv("cfpb_top_states.csv")]
    headline = json.load(open(os.path.join(RAW, "cfpb_headline.json")))

    total_2025plus = headline["total_since_2025_01_01"]
    n_issues = sum(c for _, c in issues)

    # 2026 vs 2025 growth
    y25, y26 = yearly.get(2025, 0), yearly.get(2026, 0)
    growth_pct = 100 * (y26 - y25) / y25 if y25 else 0

    # money-access / unauthorised / scam share
    key_terms = ("Unauthorized transactions", "Trouble accessing funds",
                 "Fraud or scam", "Other transaction problem")
    access_share = sum(c for i, c in issues if i.startswith(key_terms)) / n_issues * 100

    monetary = sum(c for r, c in responses if r.lower().strip() == "closed with monetary relief")
    monetary_pct = 100 * monetary / sum(c for _, c in responses)
    explanation = sum(c for r, c in responses if "explanation" in r.lower())
    nonmonetary = sum(c for r, c in responses if "non-monetary" in r.lower())
    explanation_pct = 100 * explanation / sum(c for _, c in responses)

    top5 = issues[:5]
    top5_share = 100 * sum(c for _, c in top5) / n_issues

    summary = {
        "harvested_on": headline["harvested_on"],
        "company": headline["company"],
        "complaints_all_time": headline["total_all_time"],
        "complaints_since_2025_01_01": total_2025plus,
        "complaints_2025_full_year": y25,
        "complaints_2026_ytd": y26,
        "yoy_growth_2026_vs_2025_pct": round(growth_pct, 1),
        "top_issues_2025plus": [{"issue": i, "count": c, "share_pct": round(100 * c / n_issues, 1)}
                                for i, c in issues[:10]],
        "top5_issues_share_pct": round(top5_share, 1),
        "money_access_or_unauthorised_share_pct": round(access_share, 1),
        "products_2025plus": [{"product": p, "count": c} for p, c, _ in products],
        "response_mix_pct": {"monetary_relief": round(monetary_pct, 1),
                             "closed_with_explanation": round(explanation_pct, 1),
                             "closed_with_non_monetary_relief": round(100 * nonmonetary / sum(c for _, c in responses), 1)},
        "top_states": [{"state": s, "count": c} for s, c in states[:8]],
        "trend": yearly,
    }

    json.dump(summary, open(os.path.join(OUT, "cfpb_summary.json"), "w"), indent=1)

    L = []
    L.append("# CFPB complaint data — PayPal Holdings, Inc\n")
    L.append(f"Harvested {summary['harvested_on']} from the CFPB public Consumer Complaint "
             "Database (consumerfinance.gov). Every figure below is reproducible with "
             "`python3 tools/harvest_cfpb.py && python3 tools/analyze_cfpb.py`.\n")
    L.append("## Headline\n")
    L.append(f"- **{total_2025plus:,}** complaints since 1 Jan 2025; **{headline['total_all_time']:,}** all-time.")
    L.append(f"- **{y26:,}** complaints in 2026 to date vs **{y25:,}** in all of 2025 — "
             f"**+{growth_pct:.0f}%**, with roughly two months of 2026 still to run.")
    L.append(f"- The top five issues account for **{top5_share:.0f}%** of everything filed.")
    L.append(f"- **{explanation_pct:.0f}%** are closed with explanation; only **{monetary_pct:.0f}%** "
             "result in monetary relief.\n")
    L.append("## Top issues (since 2025-01-01)\n")
    L.append("| Issue | Complaints | Share |")
    L.append("|---|---|---|")
    for i in summary["top_issues_2025plus"]:
        L.append(f"| {i['issue']} | {i['count']:,} | {i['share_pct']}% |")
    L.append("")
    L.append("## Products\n")
    L.append("| Product | Complaints since 2025 |")
    L.append("|---|---|")
    for p in summary["products_2025plus"]:
        L.append(f"| {p['product']} | {p['count']:,} |")
    L.append("")
    L.append("## Yearly trend\n")
    L.append("| Year | Complaints |")
    L.append("|---|---|")
    for y in sorted(summary["trend"]):
        note = " (partial — YTD)" if y == 2026 else ""
        L.append(f"| {y} | {summary['trend'][y]:,}{note} |")
    L.append("")
    L.append("## Response mix\n")
    L.append(f"- Closed with explanation: **{explanation_pct:.0f}%**")
    L.append(f"- Closed with monetary relief: **{monetary_pct:.0f}%**")
    L.append("")
    L.append("## Top states\n")
    L.append(", ".join(f"{s['state']} ({s['count']:,})" for s in summary["top_states"]))
    L.append("")
    L.append("## Caveats you must state if you cite this\n")
    L.append("- CFPB complaints are **self-selected**: they show what motivates people to file, "
             "not the base rate of failure. Never present a complaint count as a failure rate.")
    L.append("- They cover **US consumers only**.")
    L.append("- Complaint volume partly tracks account growth, not just product quality.")
    L.append("- Published narratives are not exposed by the search API; only the structured "
             "fields are available programmatically.")
    open(os.path.join(OUT, "cfpb_summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:26]))
    print(f"\nwrote {OUT}/cfpb_summary.{{json,md}}")


if __name__ == "__main__":
    main()
