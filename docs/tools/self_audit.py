#!/usr/bin/env python3
"""Score our own repo on the same 13 markers used on the field of 549.

Three readings, because they are three different things:

  visible  what a scanner or a judge skimming GitHub sees: README only
  code     what the repository actually does: every .py and .md
  claimed  what the submission will say once we deploy and add a licence

Usage:  python3 docs/tools/self_audit.py [--json]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT = ROOT / "product"
FIELD = ROOT / "docs" / "research" / "03_field" / "REPOS.csv"

sys.path.insert(0, str(ROOT / "tools"))
from scan_field import DEPTH  # noqa: E402  the same rules, not a copy

MARKERS = {k: re.compile(v, re.I | re.S) for k, v in DEPTH.items()}
# markers that a deploy and a licence file would switch on, tonight
CHEAP = ("license", "liveurl")


def read_text(paths) -> str:
    out = []
    for p in paths:
        try:
            out.append(p.read_text(encoding="utf-8", errors="ignore"))
        except OSError:
            pass
    return "\n\n".join(out)


PLACEHOLDER = re.compile(r"https://[^\s)\"']*<(?:your-app|url|host)[^\s)\"']*")


def hit(text: str) -> list[str]:
    """A placeholder URL is not a deployment; strip those before scoring."""
    return [k for k, rx in MARKERS.items() if rx.search(PLACEHOLDER.sub("", text))]


def field_distribution() -> tuple[dict[int, int], int]:
    counts: dict[int, int] = {}
    total = 0
    with FIELD.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            raw = (row.get("depth_0_13") or "").strip()
            if not raw.isdigit():
                continue
            counts[int(raw)] = counts.get(int(raw), 0) + 1
            total += 1
    return counts, total


def percentile(score: int, counts: dict[int, int], total: int) -> float:
    """Share of the field at or below this score."""
    if not total:
        return 0.0
    return 100.0 * sum(n for d, n in counts.items() if d <= score) / total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    readme = PRODUCT / "README.md"
    visible = hit(read_text([readme]))
    code = hit(read_text(sorted(PRODUCT.rglob("*.py")) + sorted(PRODUCT.rglob("*.md"))))
    claimed = sorted(set(code) | set(CHEAP))
    missing_from_code = sorted(set(MARKERS) - set(code))
    counts, total = field_distribution()

    rows = [
        ("visible (README)", visible),
        ("code (whole repo)", code),
        ("claimed (after deploy + licence)", claimed),
    ]

    if args.json:
        print(json.dumps({
            "visible": visible, "code": code, "claimed": claimed,
            "missing": missing_from_code,
            "percentiles": {n: round(percentile(len(v), counts, total), 1) for n, v in rows},
            "field": {"repos": total, "counts": counts},
        }, indent=2))
        return 0

    flat = sorted(d for d, n in counts.items() for _ in range(n))
    print(f"field: {total} repos, median depth {flat[len(flat) // 2]}\n")
    print(f"{'reading':34} {'score':>5} {'top %':>7}  markers")
    for name, got in rows:
        pct = 100.0 - percentile(len(got), counts, total)
        print(f"{name:34} {len(got):>2}/13 {pct:>6.1f}%  {' '.join(got)}")
    armed = [m for m in missing_from_code if m not in CHEAP]
    print(f"\nswitched on by 12 minutes of work: {', '.join(m for m in CHEAP if m in claimed)}")
    print(f"still missing after tonight:        {', '.join(armed) or 'nothing that matters'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
