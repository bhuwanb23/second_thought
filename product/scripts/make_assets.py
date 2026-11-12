#!/usr/bin/env python3
"""
scripts/make_assets.py — logos, cards and thumbnails, as SVG and PNG.

    python3 scripts/make_assets.py            # write assets/
    python3 scripts/make_assets.py --list     # what it would write

PNG is produced with cairosvg (scale 2, so every raster is 2x the layout size and stays
sharp on a retina screen). If cairosvg is missing the SVGs are still written and the script
says so instead of silently shipping a set of half-assets.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from asset_kit import (DECLINE, DEFER, INK, LINE, MUTED, OFFER, PAPER, SANS, SOFT,  # noqa: E402
                       WHITE, Svg, mark, text_width)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
SVG, PNG = OUT / "svg", OUT / "png"

NAME = "Second Thought"
TAGLINE = "A checkout that sometimes says not yet"
SUB = "payday-aware checkout"


def lockup(h=300, ink=INK, paper=None, sub=MUTED, size=104, show_sub=True, pad=90):
    """The horizontal logo: mark, name, one line under it. Width is measured, not guessed."""
    m = size * 1.40
    name_w = text_width(NAME, size, "700")
    sub_w = text_width(SUB, size * 0.30) if show_sub else 0
    text_w = max(name_w, sub_w)
    w = int(pad * 2 + m + size * 0.42 + text_w)
    svg = Svg(w, h, bg=paper)
    mx = pad
    my = h / 2 - m / 2
    mark(svg, mx, my, m, ink=ink, paper=paper)
    tx = mx + m + size * 0.42
    if show_sub:
        svg.text(tx, h / 2 + size * 0.10, NAME, size=size, fill=ink, weight="700",
                 spacing="-0.02em")
        svg.text(tx, h / 2 + size * 0.52, SUB, size=size * 0.30, fill=sub, weight="400",
                 spacing="0.01em")
    else:
        svg.text(tx, h / 2 + size * 0.28, NAME, size=size, fill=ink, weight="700",
                 spacing="-0.02em")
    return svg


def app_icon(size=512):
    svg = Svg(size, size, bg=INK)
    svg.rect(0, 0, size, size, fill=INK, r=0)   # square corners: stores round it
    mark(svg, size * 0.16, size * 0.16, size * 0.68, ink=WHITE, paper=INK)
    return svg


def og_card():
    """1200x630 — the shape every social card and Devpost preview wants."""
    svg = Svg(1200, 630, bg=PAPER)
    svg.rect(0, 0, 1200, 8, fill=INK)
    mark(svg, 84, 76, 104, ink=INK, paper=PAPER)
    svg.text(206, 132, NAME, size=44, fill=INK, weight="700", spacing="-0.02em")
    svg.text(206, 166, SUB, size=19, fill=MUTED)

    svg.text(84, 300, "A checkout that", size=64, fill=INK, weight="700", spacing="-0.03em")
    svg.text(84, 372, "sometimes says", size=64, fill=INK, weight="700", spacing="-0.03em")
    svg.text(84, 444, "not yet.", size=64, fill=DECLINE, weight="700", spacing="-0.03em")
    svg.para(84, 500, "It reads your month. If four payments would break it, PayPal "
             "invoices you on payday — and the merchant ships when you've paid.",
             width=52, size=20, fill=MUTED)

    # three answers, right hand side
    rows = [("OFFER", "pay in four today", OFFER),
            ("DEFER", "pay on payday, ship on payment", DEFER),
            ("DECLINE", "here's what would fit", DECLINE)]
    for i, (word, note, colour) in enumerate(rows):
        y = 214 + i * 86
        svg.rect(760, y, 356, 66, fill=WHITE, r=12, stroke=LINE)
        svg.rect(760, y, 5, 66, fill=colour, r=2)
        svg.text(784, y + 30, word, size=19, fill=colour, weight="700", spacing="0.04em")
        svg.text(784, y + 52, note, size=15, fill=MUTED)
    svg.text(84, 566, "PayPal sandbox · AI reads the month · it does not decide",
             size=15, fill=MUTED, family="DejaVu Sans Mono, monospace")
    return svg


def devpost_thumb():
    """1280x720. Devpost crops toward the centre, so the mark and the claim sit left."""
    svg = Svg(1280, 720, bg=INK)
    mark(svg, 96, 96, 96, ink=WHITE, paper=INK)
    svg.text(214, 164, NAME, size=42, fill=WHITE, weight="700", spacing="-0.02em")
    svg.text(96, 330, "A checkout that", size=66, fill=WHITE, weight="700", spacing="-0.03em")
    svg.text(96, 406, "sometimes says", size=66, fill=WHITE, weight="700", spacing="-0.03em")
    svg.text(96, 482, "not yet.", size=66, fill="#7fd1ab", weight="700", spacing="-0.03em")
    svg.para(96, 556, "Payday-aware checkout. Reads the month, then decides: pay in four, "
             "pay on payday, or here is what would fit.", width=58, size=21, fill="#c7ccd4")
    svg.text(96, 660, "PAYPAL SANDBOX  ·  AI · LLM-MOCK  ·  PAYMENTS · SIMULATED",
             size=15, fill="#7a828f", family="DejaVu Sans Mono, monospace")
    return svg


def favicon(size=256):
    return app_icon(size)


ASSETS = {
    "logo-primary": (lambda: lockup(paper=PAPER), 2, "logo lockup on paper"),
    "logo-primary-transparent": (lambda: lockup(paper=None), 2,
                                 "same lockup, no background (for white pages)"),
    "logo-mono-white": (lambda: lockup(ink=WHITE, sub="#c7ccd4", paper=INK), 2,
                        "reversed lockup for dark backgrounds"),
    "logo-wordmark-only": (lambda: lockup(show_sub=False, size=132), 2,
                           "name only, no mark"),
    "logo-mark": (lambda: _mark_only(), 3, "the mark alone, transparent"),
    "logo-mark-on-paper": (lambda: _mark_on_paper(), 2, "the mark on a paper tile"),
    "logo-mark-white": (lambda: _mark_white(), 2, "the mark in white, for dark covers"),
    "app-icon": (app_icon, 1, "512 square, for avatars and stores"),
    "favicon": (favicon, 1, "256 square, for a browser tab"),
    "og-card": (og_card, 2, "1200x630 social / link preview"),
    "devpost-thumbnail": (devpost_thumb, 2, "1280x720 listing thumbnail"),
}


def _mark_only():
    svg = Svg(256, 256, bg=None)
    mark(svg, 8, 8, 240, ink=INK, paper=None, sw=22)
    return svg


def _mark_white():
    svg = Svg(320, 320, bg=None)
    mark(svg, 20, 20, 280, ink=WHITE, paper=None, sw=26)
    return svg


def _mark_on_paper():
    svg = Svg(320, 320, bg=PAPER)
    mark(svg, 40, 40, 240, ink=INK, paper=PAPER, sw=22)
    return svg


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args(argv)
    if args.list:
        for name, (_f, scale, note) in ASSETS.items():
            print(f"{name:<20} {note}")
        return 0

    SVG.mkdir(parents=True, exist_ok=True)
    PNG.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg
    except ImportError:
        cairosvg = None

    for name, (fn, scale, _note) in ASSETS.items():
        svg = fn()
        (SVG / f"{name}.svg").write_text(svg.render())
        if cairosvg:
            cairosvg.svg2png(url=str(SVG / f"{name}.svg"),
                             write_to=str(PNG / f"{name}.png"), scale=scale)
        print(f"  {'✓' if cairosvg else '·'} {name}")
    if not cairosvg:
        print("\ncairosvg not installed — SVG written, PNG skipped. pip install cairosvg")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
