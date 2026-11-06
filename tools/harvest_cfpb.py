#!/usr/bin/env python3
"""
harvest_cfpb.py — pull the CFPB public consumer complaint database for PayPal.

Why: it is the only large, public, dated, quantified record of what actually goes
wrong for real PayPal users. Judges score "Potentially Impactful" on whether the
problem is real and specific; this is the strongest citation available.

Outputs (04_pain/raw/):
  cfpb_products.csv        complaints by product / sub-product
  cfpb_issues.csv          complaints by issue
  cfpb_yearly.csv          complaints per year (shows trend)
  cfpb_responses.csv       how PayPal responded / timeliness
  cfpb_narratives.jsonl    published narratives (only ~1/3 of complaints have one)
  cfpb_sample.jsonl        200 full records across products

Public API, no key. Be polite: small sleep between calls.
"""
import csv
import json
import os
import time
import urllib.parse
import urllib.request

BASE = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "research", "pain_evidence", "raw")
os.makedirs(OUT, exist_ok=True)
COMPANY = "Paypal Holdings, Inc"


def get(params):
    params = dict(params)
    params.setdefault("company", COMPANY)
    u = BASE + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(u, timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def buckets(node):
    """Flatten a nested ES aggregation into (key, count) pairs."""
    out = []
    if isinstance(node, dict):
        if "buckets" in node:
            for b in node["buckets"]:
                out.append((b.get("key"), b.get("doc_count")))
        else:
            for v in node.values():
                out.extend(buckets(v))
    return out


def write_csv(name, header, rows):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"  {name:26s} {len(rows)} rows")


def main():
    print(f"Harvesting CFPB complaints for: {COMPANY}")

    # --- headline totals -------------------------------------------------
    d = get({"size": 1, "date_received_min": "2025-01-01"})
    total_since_2025 = d["hits"]["total"]["value"]
    d_all = get({"size": 1})
    total_all = d_all["hits"]["total"]["value"]
    print(f"  total complaints (all time): {total_all:,}")
    print(f"  total complaints since 2025-01-01: {total_since_2025:,}")

    # --- by product / sub-product ---------------------------------------
    d = get({"size": 1, "date_received_min": "2025-01-01",
             "aggs": "product"})
    rows = []
    for b in d["aggregations"]["product"]["product"]["buckets"]:
        rows.append([b["key"], b["doc_count"], ""])
        for sb in b.get("sub-product", {}).get("buckets", []):
            rows.append(["", "", 0])
            rows[-1] = [b["key"], "", f"{sb['key']} | {sb['doc_count']}"]
    write_csv("cfpb_products.csv", ["product", "count_2025plus", "sub_product | count"], rows)

    # --- by issue --------------------------------------------------------
    d = get({"size": 1, "date_received_min": "2025-01-01", "aggs": "issue"})
    rows = [(k, v) for k, v in buckets(d["aggregations"]["issue"])]
    rows.sort(key=lambda x: -x[1])
    write_csv("cfpb_issues.csv", ["issue", "count_2025plus"], rows)

    # --- yearly trend ----------------------------------------------------
    rows = []
    for y in range(2015, 2027):
        d = get({"size": 1, "date_received_min": f"{y}-01-01", "date_received_max": f"{y}-12-31"})
        rows.append([y, d["hits"]["total"]["value"]])
        time.sleep(0.3)
    # current year is partial — mark it
    write_csv("cfpb_yearly.csv", ["year", "complaints"], rows)

    # --- response / timeliness -------------------------------------------
    d = get({"size": 1, "date_received_min": "2025-01-01", "aggs": "company_response"})
    rows = sorted([(k, v) for k, v in buckets(d["aggregations"]["company_response"])],
                  key=lambda x: -x[1])
    write_csv("cfpb_responses.csv", ["company_response", "count_2025plus"], rows)

    d = get({"size": 1, "date_received_min": "2025-01-01", "aggs": "state"})
    rows = sorted([(k, v) for k, v in buckets(d["aggregations"]["state"])], key=lambda x: -x[1])[:20]
    write_csv("cfpb_top_states.csv", ["state_or_zip", "count_2025plus"], rows)

    # --- published narratives (the qualitative gold) ----------------------
    # has_narrative=1 restricts to complaints where the consumer consented to publication
    n_written = 0
    f = open(os.path.join(OUT, "cfpb_narratives.jsonl"), "w")
    for frm in range(0, 9000, 1000):
        d = get({"size": 100, "frm": frm, "date_received_min": "2025-01-01",
                 "has_narrative": "true", "sort": "created_date_desc"})
        hits = [h["_source"] for h in d["hits"]["hits"]]
        if not hits:
            break
        for h in hits:
            f.write(json.dumps(h) + "\n")
            n_written += 1
        time.sleep(0.3)
    f.close()
    print(f"  {'cfpb_narratives.jsonl':26s} {n_written} records")

    # --- a structured sample across products -----------------------------
    n = 0
    with open(os.path.join(OUT, "cfpb_sample.jsonl"), "w") as f:
        for prod in ["Checking or savings account", "Credit card", "Money transfer, virtual currency, or money service",
                     "Debt collection", "Prepaid card"]:
            d = get({"size": 40, "product": prod, "date_received_min": "2025-01-01",
                     "sort": "created_date_desc"})
            for h in d["hits"]["hits"]:
                f.write(json.dumps(h["_source"]) + "\n")
                n += 1
            time.sleep(0.3)
    print(f"  {'cfpb_sample.jsonl':26s} {n} records")

    with open(os.path.join(OUT, "cfpb_headline.json"), "w") as f:
        json.dump({"company": COMPANY, "total_all_time": total_all,
                   "total_since_2025_01_01": total_since_2025,
                   "harvested_on": time.strftime("%Y-%m-%d")}, f, indent=1)
    print("done")


if __name__ == "__main__":
    main()
