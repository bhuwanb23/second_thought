#!/usr/bin/env python3
"""
scan_field.py — daily competitive field scanner for the PayPal AI Hackathon.

Why: the Devpost gallery is hidden, but entrants publish public repos. This captures
the field as it actually is, tracks how it moves day to day, and classifies every
entry into a concept cluster so you can see which lanes are filling up.

Usage
-----
    python3 tools/scan_field.py                # scan, save snapshot, print report
    python3 tools/scan_field.py --diff-only    # report changes since last snapshot
    python3 tools/scan_field.py --queries      # list the queries used

Outputs (under 03_field/):
    snapshot_YYYY-MM-DD.json    raw repos from this run
    latest.md                   human-readable report
    clusters.csv                cluster density table
    new_entrants.csv            repos that appeared since the previous snapshot

No auth needed. GitHub search API allows ~10 req/min unauthenticated; the script
sleeps between queries. If you hit limits, set GITHUB_TOKEN in the environment.
"""

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPS = os.path.join(ROOT, "03_field", "snapshots")
REPORTS = os.path.join(ROOT, "03_field")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Multiple queries because entrants describe the same hackathon differently.
QUERIES = [
    '"PayPal AI Hackathon"',
    '"PayPal" hackathon 2026 in:description,readme',
    'paypal agentic commerce hackathon',
]

# Concept clusters as (name, strong_patterns, weak_patterns).
# Scoring is weighted (strong=3, weak=1) and the highest score wins, which is far
# more robust than first-match when descriptions are marketing prose.
CLUSTERS = [
    ("agent-trust-identity",
     [r"real (consumer|buyer|merchant)", r"agent (identity|attestation)", r"trust (layer|gateway|score)",
      r"verif(y|ies|ied) (the )?(buyer|merchant|agent)", r"proof of (human|intent)", r"flight recorder",
      r"can'?t be tricked|not be tricked|prompt injection"],
     [r"\btrust\b", r"\bidentit(y|ies)\b", r"\breal (user|customer)\b"]),

    ("mandate-guardrail",
     [r"\bmandate\b", r"spend(ing)? (cap|limit)", r"guardrail", r"policy engine", r"bounded (agent|spend)",
      r"agent (wallet|budget)", r"credential.{0,20}(never|not) (held|touch)"],
     [r"\bbudget\b", r"\bapproval gate\b", r"allowance"]),

    ("escrow-milestone",
     [r"\bescrow\b", r"milestone (release|payment|payout)", r"conditional release", r"staged payment",
      r"hold funds", r"funds? (are )?(held|frozen)"],
     [r"\bmilestone\b", r"\bdeposit\b"]),

    ("dispute-chargeback",
     [r"\bdispute\b", r"chargeback", r"evidence (pack|bundle|graph)", r"rebuttal"],
     [r"\bclaim\b"]),

    ("invoice-ar",
     [r"\binvoic", r"accounts.receivable", r"\bdunning\b", r"payment reminder", r"quote.and.pay"],
     [r"\bbilling\b", r"\bget paid\b"]),

    ("payout-gig",
     [r"\bpayout", r"\bcontractor\b", r"gig worker", r"\bbounty\b", r"marketplace split", r"mass ?pay"],
     [r"\bfreelanc"]),

    ("subscription-recurring",
     [r"subscription (plan|billing|tier)", r"\brecurring\b", r"\bchurn\b", r"\bmrr\b", r"renewal"],
     [r"subscription"]),

    ("shopping-agent",
     [r"shopping agent", r"shopping assistant", r"buy for me", r"product comparison", r"gift (finder|recommend)",
      r"price (watch|drop|alert)", r"finds? (the )?best (deal|price)", r"\badds? to cart\b"],
     [r"\bcart\b", r"\bshopping\b", r"\bcheckout\b"]),

    ("storefront-builder",
     [r"storefront", r"store builder", r"shop builder", r"social.only seller", r"catalog (sync|feed)",
      r"product feed", r"agent.ready (store|commerce)", r"makes? .{0,20}store buyable"],
     [r"\bcatalog\b", r"product photos"]),

    ("receipt-split",
     [r"split (the )?(bill|receipt|cost)", r"\breceipt\b", r"expense split", r"group (bill|dinner)"],
     [r"\bsplit\b"]),

    ("remittance-crossborder",
     [r"\bremit", r"cross.border (payment|transfer)", r"migrant", r"send money (home|abroad)",
      r"family (support|remittance)", r"\bfx\b|exchange rate"],
     [r"international transfer"]),

    ("insurance-parametric",
     [r"parametric", r"income (cover|protection)", r"\binsurance\b"],
     [r"\bcover(age)?\b"]),

    ("fraud-scam",
     [r"\bscam\b", r"\bfraud\b", r"phishing", r"risk scor", r"protect .{0,20}(senior|elder)"],
     [r"\brisk\b"]),

    ("credit-bnpl",
     [r"buy now pay later", r"\bbnpl\b", r"\binstallment", r"credit (line|readiness)", r"pay later"],
     [r"\bcredit\b"]),

    ("nonprofit-donation",
     [r"nonprofit", r"charit", r"donation", r"\bngo\b", r"treasury (agent|management)"],
     [r"\bdonor\b", r"fundrais"]),

    ("accessibility",
     [r"accessib", r"blind", r"low.vision", r"screen.reader", r"\bdisab"],
     []),

    ("reconciliation-reporting",
     [r"reconcil", r"anomal", r"transaction search", r"reporting api", r"insights dashboard"],
     [r"dashboard", r"analytics"]),

    ("a2a-agent-commerce",
     [r"agent.to.agent", r"\ba2a\b", r"agent procures", r"two agents", r"agents? (negotiat|haggle)"],
     [r"negotiat"]),

    ("merchant-integration",
     [r"integration agent", r"sdk upgrade", r"certif(y|ication)", r"reads? .{0,20}codebase"],
     []),

    ("education-fees",
     [r"tuition", r"school fee", r"\bcourse fee"],
     [r"\beducation\b", r"\bstudent"]),

    ("agriculture",
     [r"\bfarm", r"\bagri", r"\bcrop\b", r"\bharvest\b"],
     [r"\bmandi\b"]),

    ("gaming-esports",
     [r"esport", r"tournament", r"\bgaming\b", r"game prize"],
     []),
]

CLUSTER_STRONG = {n: [re.compile(p, re.I) for p in s] for n, s, w in CLUSTERS}
CLUSTER_WEAK = {n: [re.compile(p, re.I) for p in w] for n, s, w in CLUSTERS}

# Technical depth markers (13). Higher = more real implementation.
DEPTH = {
    "webhook":      r"webhook",
    "sigverify":    r"signature.{0,25}(verif|validat)|verify.{0,25}signature",
    "authorize":    r"intent\s*[=:]\s*[\"']?AUTHORIZE|authori[sz]e.{0,20}capture",
    "payouts":      r"payouts?/v1|create_payout|mass ?pay",
    "invoicing":    r"invoic",
    "disputes":     r"dispute",
    "subscriptions":r"subscription",
    "toolkit":      r"agent.toolkit|paypal_agent_toolkit|@paypal/",
    "mcp":          r"\bMCP\b",
    "aggrid":       r"ag-grid-community|ag-grid-react|@ag-grid|ag studio",
    "license":      r"##\s*license|MIT License|Apache License",
    "idempotency":  r"idempot",
    "liveurl":      r"https://[a-z0-9.-]+\.(vercel\.app|onrender\.com|railway\.app|netlify\.app|fly\.dev|workers\.dev|github\.io)",
}


def gh(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "hackathon-field-scanner")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect():
    seen = {}
    for q in QUERIES:
        for page in (1, 2, 3):
            url = ("https://api.github.com/search/repositories?q=" + urllib.parse.quote(q)
                   + f"&sort=updated&per_page=100&page={page}")
            try:
                data = gh(url)
            except Exception as e:
                print(f"  ! query failed ({q} p{page}): {e}", file=sys.stderr)
                break
            items = data.get("items", [])
            if not items:
                break
            for it in items:
                seen[it["full_name"]] = {
                    "full_name": it["full_name"],
                    "description": it.get("description") or "",
                    "language": it.get("language") or "",
                    "license": (it.get("license") or {}).get("spdx_id") or "NONE",
                    "homepage": it.get("homepage") or "",
                    "stars": it.get("stargazers_count", 0),
                    "created": (it.get("created_at") or "")[:10],
                    "pushed": (it.get("pushed_at") or "")[:10],
                    "topics": it.get("topics") or [],
                    "url": it.get("html_url", ""),
                }
            if len(items) < 100:
                break
            time.sleep(7 if not TOKEN else 0.5)
    return seen


def fetch_readme(full_name):
    for branch in ("main", "master"):
        for name in ("README.md", "readme.md"):
            u = f"https://raw.githubusercontent.com/{full_name}/{branch}/{name}"
            try:
                with urllib.request.urlopen(u, timeout=20) as r:
                    return r.read().decode("utf8", "ignore")
            except Exception:
                continue
    return ""


def classify(text, ):
    """Weighted argmax over cluster patterns. Strong hit = 3, weak hit = 1."""
    best, best_score = "other", 0
    for name in CLUSTER_STRONG:
        sc = 3 * sum(1 for p in CLUSTER_STRONG[name] if p.search(text))
        sc += sum(1 for p in CLUSTER_WEAK[name] if p.search(text))
        if sc > best_score:
            best, best_score = name, sc
    return best


def depth_score(text):
    hits = [k for k, p in DEPTH.items() if re.search(p, text, re.I)]
    return len(hits), hits


def scan(do_readmes=True):
    print("Querying GitHub…")
    repos = collect()
    print(f"  found {len(repos)} unique public repos")

    if do_readmes:
        print("Fetching READMEs for classification + depth…")
        import concurrent.futures
        fns = sorted(repos)
        with concurrent.futures.ThreadPoolExecutor(16) as ex:
            texts = list(ex.map(lambda f: (f, fetch_readme(f)), fns))
        for i, (fn, txt) in enumerate(texts, 1):
            r = repos[fn]
            blob = f"{r['description']} {' '.join(r['topics'])} {txt}"
            r["cluster"] = classify(blob)
            n, hits = depth_score(txt) if txt else (0, [])
            r["depth"] = n
            r["depth_hits"] = hits
            r["has_readme"] = bool(txt)
            r["live_url"] = r["homepage"] or (
                re.search(DEPTH["liveurl"], txt).group(0) if txt and re.search(DEPTH["liveurl"], txt, re.I) else ""
            )
        print(f"    {len(texts)} readmes processed")
    else:
        for r in repos.values():
            r["cluster"] = classify(f"{r['description']} {' '.join(r['topics'])}")
            r["depth"] = 0
            r["depth_hits"] = []
            r["has_readme"] = False
            r["live_url"] = r["homepage"]

    return repos


def load_previous(today_path):
    if not os.path.isdir(SNAPS):
        return {}
    snaps = sorted(f for f in os.listdir(SNAPS) if f.startswith("snapshot_") and f.endswith(".json"))
    snaps = [f for f in snaps if os.path.join(SNAPS, f) != today_path]
    if not snaps:
        return {}
    with open(os.path.join(SNAPS, snaps[-1])) as f:
        return json.load(f)


def write_report(repos, prev):
    os.makedirs(SNAPS, exist_ok=True); os.makedirs(REPORTS, exist_ok=True)
    today = date.today().isoformat()
    snap_path = os.path.join(SNAPS, f"snapshot_{today}.json")
    with open(snap_path, "w") as f:
        json.dump(repos, f, indent=1, sort_keys=True)

    prev = prev or load_previous(snap_path)
    new = {k: v for k, v in repos.items() if k not in prev}

    L = []
    L.append(f"# Field scan — {today}\n")
    L.append(f"- Public repos found: **{len(repos)}**"
             + (f"  (+{len(new)} since previous snapshot)" if prev else ""))
    live = sum(1 for r in repos.values() if r.get("live_url"))
    L.append(f"- With a live demo URL: **{live}** ({100*live/max(len(repos),1):.0f}%)")
    nolic = sum(1 for r in repos.values() if r["license"] == "NONE")
    L.append(f"- No license (disqualification risk): **{nolic}** ({100*nolic/max(len(repos),1):.0f}%)")
    L.append(f"- Languages: " + ", ".join(f"{k} {v}" for k, v in Counter(r['language'] for r in repos.values()).most_common(6)))
    dep = Counter(r["depth"] for r in repos.values())
    L.append(f"- Depth distribution (0–13 markers): " + " | ".join(f"{k}:{dep[k]}" for k in sorted(dep)))

    L.append("\n## Cluster density — where the crowd is\n")
    L.append("| Cluster | Entries | Live demos | Avg depth | Crowding |")
    L.append("|---|---|---|---|---|")
    by = defaultdict(list)
    for r in repos.values():
        by[r["cluster"]].append(r)
    rows = []
    for c, rs in by.items():
        lv = sum(1 for r in rs if r.get("live_url"))
        ad = sum(r["depth"] for r in rs) / len(rs)
        rows.append((c, len(rs), lv, ad))
    for c, n, lv, ad in sorted(rows, key=lambda x: -x[1]):
        flag = "RED — crowded" if n >= 30 else "AMBER" if n >= 10 else "GREEN — open"
        L.append(f"| {c} | {n} | {lv} | {ad:.1f} | {flag} |")

    L.append("\n## Strongest entries (read these, then build something else)\n")
    for r in sorted(repos.values(), key=lambda x: -x["depth"])[:12]:
        L.append(f"- **{r['depth']}/13** `{r['full_name']}` — {r['description'][:120]}")

    if new and prev:
        L.append(f"\n## New since last scan ({len(new)})\n")
        for k, v in sorted(new.items())[:40]:
            L.append(f"- `{k}` — {v['cluster']} — {v['description'][:100]}")

    md = "\n".join(L) + "\n"
    with open(os.path.join(REPORTS, "FIELD_MAP.md"), "w") as f:
        f.write(md)

    with open(os.path.join(REPORTS, "CLUSTERS.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["cluster", "entries", "live_demos", "avg_depth"])
        for c, n, lv, ad in sorted(rows, key=lambda x: -x[1]):
            w.writerow([c, n, lv, f"{ad:.1f}"])

    if new:
        with open(os.path.join(REPORTS, "NEW_ENTRANTS.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["full_name", "cluster", "depth", "description", "url"])
            w.writeheader()
            for k, v in sorted(new.items()):
                w.writerow({kk: v.get(kk, "") for kk in w.fieldnames})

    print(md)
    print(f"Saved: {snap_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--diff-only", action="store_true", help="no network readmes; report only")
    ap.add_argument("--queries", action="store_true", help="print queries and exit")
    a = ap.parse_args()
    if a.queries:
        print("\n".join(QUERIES))
        return
    repos = scan(do_readmes=not a.diff_only)
    write_report(repos, {})


if __name__ == "__main__":
    main()
