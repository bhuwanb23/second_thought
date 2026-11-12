#!/usr/bin/env python3
"""
scripts/scorecard.py — score this submission against the five judged criteria.

    python3 scripts/scorecard.py                    # offline, what exists in the repo
    python3 scripts/scorecard.py --url https://...  # + the deployed checks
    python3 scripts/scorecard.py --json             # machine-readable

The rules: five criteria, equally weighted, Stage 1 is a pass/fail gate on "genuinely
applies the required APIs". Every check below is a *proxy* for something a judge does
with their eyes, and the docstring of each says which. A high score here does not mean
a judge will like it; it means there is nothing left that a judge would find missing.

Anchors, so a number means something:
    0  absent
    1  claimed in prose only
    2  exists, but a judge cannot verify it
    3  verifiable, one path
    4  verifiable, multiple paths, depth a judge can see
    5  what the top decile of the field already does
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
RESEARCH = REPO / "docs" / "research"
OUT = ROOT / "artifacts" / "scorecard"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from scorecard_checks import (add, design, impact, innovation,  # noqa: E402
                              presentation, results, tech)

class Ctx:
    def __init__(self, url=""):
        self.url = url.rstrip("/")
        self.readme = (ROOT / "README.md").read_text() if (ROOT / "README.md").exists() else ""
        self.settings = None
        try:
            from secondthought.config import load
            self.settings = load()
        except Exception:
            pass

    def fetch(self, path):
        if not self.url:
            return None
        try:
            with urllib.request.urlopen(self.url + path, timeout=25) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()
        except Exception:
            return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    ctx = Ctx(args.url)

    for fn in (tech, design, impact, innovation, presentation):
        fn(ctx)

    crit: dict[str, list] = {}
    for c, name, ok, w, ev in results:
        crit.setdefault(c, []).append((name, ok, w, ev))

    scores, table = {}, {}
    for c, rows in crit.items():
        total = sum(w for *_x, w, _e in rows)
        earned = sum(w for _n, ok, w, _e in rows if ok)
        scores[c] = round(5 * earned / total, 1) if total else 0.0
        table[c] = rows

    if args.json:
        print(json.dumps({"scores": scores,
                          "checks": [{"criterion": c, "check": n, "pass": ok,
                                      "weight": w, "evidence": ev}
                                     for c, n, ok, w, ev in results]}, indent=1))
    else:
        print(f"\nSCORECARD · {time.strftime('%Y-%m-%d %H:%M')} · " +
              (args.url or "offline (no deployed URL)"))
        print("=" * 78)
        for c, rows in table.items():
            print(f"\n{c}  —  {scores[c]}/5")
            for name, ok, w, ev in rows:
                if w == 0:
                    continue
                mark = "✓" if ok else "✗"
                print(f"  {mark} {name:<52} {ev}")
        mean = round(sum(scores.values()) / len(scores), 2) if scores else 0
        print("\n" + "=" * 78)
        print(f"  mean {mean}/5   " + "   ".join(f"{c.split()[0][:12]} {v}" for c, v in scores.items()))
        stage1 = scores["Technological Implementation"] >= 3
        print(f"  Stage 1 (genuinely uses PayPal {chr(38)} AI): "
              f"{'likely pass' if stage1 else 'AT RISK — no verifiable PayPal call'}\n")

    OUT.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    (OUT / f"{stamp}.json").write_text(json.dumps(
        {"at": stamp, "url": args.url, "scores": scores,
         "checks": [{"criterion": c, "check": n, "pass": ok, "weight": w, "evidence": ev}
                    for c, n, ok, w, ev in results]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
