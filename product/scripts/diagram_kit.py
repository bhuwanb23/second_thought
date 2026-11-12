"""
scripts/diagram_kit.py — shared canvas constants and the two composition helpers.

The diagrams are split across two scripts to keep every file in this repo under 300 lines:
`make_diagrams.py` draws the story (flow, verdicts, defer, clusters) and
`make_diagrams_tech.py` draws the system (architecture, boundary, gate).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from asset_kit import INK, MUTED, WHITE, Svg, text_width  # noqa: F401
from make_assets import PNG, SVG  # noqa: F401

W = 1400
M = 64


def head(svg: Svg, kicker: str, title: str) -> None:
    svg.text(M, 66, kicker.upper(), size=14, fill=MUTED, weight="700", mono=True,
             spacing="0.14em")
    svg.text(M, 112, title, size=34, fill=INK, weight="700", spacing="-0.02em")


def button(svg: Svg, x: float, y: float, label: str, size=15, pad=22, h=42) -> None:
    """A pill sized to its label, so a long action word cannot spill out of its card."""
    w = text_width(label, size, "700") + pad * 2
    svg.rect(x, y, w, h, fill=INK, r=9)
    svg.text(x + pad, y + h / 2 + size * 0.36, label, size=size, fill=WHITE, weight="700")


def run(registry: dict, argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--only", default="")
    args = ap.parse_args(argv)
    if args.list:
        for k, fn in registry.items():
            first = (fn.__doc__ or f"diagram-{k}").strip().splitlines()
            print(f"{k:<14} {first[0][:80] if first else f'diagram-{k}'}")
        return 0
    SVG.mkdir(parents=True, exist_ok=True)
    PNG.mkdir(parents=True, exist_ok=True)
    import cairosvg
    for name, fn in registry.items():
        if args.only and args.only != name:
            continue
        svg = fn()
        (SVG / f"diagram-{name}.svg").write_text(svg.render())
        cairosvg.svg2png(url=str(SVG / f"diagram-{name}.svg"),
                         write_to=str(PNG / f"diagram-{name}.png"), scale=1.6)
        print(f"  ✓ diagram-{name}")
    return 0
