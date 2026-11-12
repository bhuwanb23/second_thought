#!/usr/bin/env python3
"""
docs/tools/build_dossier.py — render docs/DOSSIER.html to a PDF.

    python3 docs/tools/build_dossier.py
    python3 docs/tools/build_dossier.py --check

The dossier is authored as HTML (print CSS, A4, running page numbers) and rendered with
WeasyPrint. The HTML keeps relative <img> paths into `product/assets/png/`, so the PDF is
always built from the same generated diagrams the README and Devpost listing use — there is
no second copy of a diagram to fall out of date.

`--check` verifies every referenced asset exists and that the PDF would not ship with a
broken figure, without writing anything.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent
SRC = DOCS / "DOSSIER.html"
OUT = DOCS / "Second-Thought-Dossier.pdf"


def refs(html: str) -> list[Path]:
    found = re.findall(r'<img[^>]+src="([^"]+)"', html)
    return [(DOCS / src).resolve() for src in found]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    html = SRC.read_text()
    images = refs(html)
    missing = [p for p in images if not p.exists()]
    for p in images:
        print(f"  {'✓' if p.exists() else '✗'} {p.relative_to(DOCS.parent)}")
    if missing:
        print(f"\n{len(missing)} missing asset(s) — run the asset generators first")
        return 2
    print(f"\n  {len(images)} figures resolve · {len(html) // 1024} KB of HTML")
    if args.check:
        return 0

    try:
        from weasyprint import HTML
    except ImportError:
        print("weasyprint is not installed: pip install weasyprint")
        return 1

    HTML(string=html, base_url=str(DOCS)).write_pdf(str(OUT))
    size = OUT.stat().st_size
    print(f"  ✓ {OUT.relative_to(DOCS.parent)}  ({size / 1024:.0f} KB)")
    try:
        import pypdf
        pages = len(pypdf.PdfReader(str(OUT)).pages)
        print(f"  ✓ {pages} pages")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
