"""
scripts/asset_kit.py — the palette, the type scale, and a very small SVG builder.

Hand-writing thirteen SVGs means thirteen sets of coordinates that drift apart. So the
assets are generated: one helper module, one script per asset family, and a contact sheet
so the whole set can be looked at together.

Everything is drawn with the same colours as the product page, because a judge sees the
logo, the diagrams and the screen side by side in a video and any drift reads as sloppiness.
"""

from __future__ import annotations

import html

INK = "#14181f"
PAPER = "#f6f7f9"
WHITE = "#ffffff"
MUTED = "#5b6472"
LINE = "#dfe3e9"
SOFT = "#e8eaee"
OFFER = "#0f7b4f"
DEFER = "#8a5a00"
DECLINE = "#8c2f39"

SANS = "DejaVu Sans, Verdana, Segoe UI, Helvetica, Arial, sans-serif"
MONO = "DejaVu Sans Mono, Consolas, Menlo, monospace"


_FONT_CACHE: dict = {}


def text_width(s: str, size: float, weight: str = "400") -> float:
    """Measure with the same font cairosvg will use, so nothing overflows a canvas.

    Falls back to a character-count estimate if PIL or the font is unavailable — a wrong
    logo is worse than a slightly conservative one.
    """
    try:
        from PIL import ImageFont
        bold = int(weight) >= 600
        path = ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
        key = (path, int(size))
        if key not in _FONT_CACHE:
            _FONT_CACHE[key] = ImageFont.truetype(path, int(size))
        return _FONT_CACHE[key].getlength(s)
    except Exception:
        return len(s) * size * (0.62 if int(weight) >= 600 else 0.56)


def esc(text: str) -> str:
    return html.escape(str(text), quote=False)


class Svg:
    """A canvas made of strings. Deliberately dumb: no layout engine, no surprises."""

    def __init__(self, w: int, h: int, bg: str | None = PAPER):
        self.w, self.h = w, h
        self.parts: list[str] = []
        if bg:
            self.rect(0, 0, w, h, bg)

    # -- primitives ---------------------------------------------------------
    def rect(self, x, y, w, h, fill=WHITE, r=0, stroke=None, sw=1.5, opacity=None,
             dash=None):
        a = f' x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"'
        if r:
            a += f' rx="{r}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        if opacity is not None:
            a += f' opacity="{opacity}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        self.parts.append(f"<rect{a}/>")

    def circle(self, cx, cy, r, fill=INK, stroke=None, sw=2):
        a = f' cx="{cx}" cy="{cy}" r="{r}" fill="{fill}"'
        if stroke:
            a += f' stroke="{stroke}" stroke-width="{sw}"'
        self.parts.append(f"<circle{a}/>")

    def line(self, x1, y1, x2, y2, stroke=LINE, sw=1.5, dash=None, arrow=False):
        a = (f' x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
             f'stroke-width="{sw}"')
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if arrow:
            a += ' marker-end="url(#arrow)"'
        self.parts.append(f"<line{a}/>")

    def path(self, d, fill="none", stroke=INK, sw=1.5, dash=None, arrow=False):
        a = f' d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if arrow:
            a += ' marker-end="url(#arrow)"'
        self.parts.append(f"<path{a}/>")

    def text(self, x, y, s, size=17, fill=INK, weight="400", family=SANS, anchor="start",
             spacing=None, mono=False):
        a = (f' x="{x}" y="{y}" font-family="{MONO if mono else family}" font-size="{size}" '
             f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"')
        if spacing:
            a += f' letter-spacing="{spacing}"'
        self.parts.append(f"<text{a}>{esc(s)}</text>")

    def para(self, x, y, s, width=42, size=16, fill=MUTED, leading=None, weight="400",
             family=SANS, anchor="start"):
        """Wrap by character count. Crude, predictable, and good enough for diagrams."""
        leading = leading or int(size * 1.45)
        for i, chunk in enumerate(_wrap(s, width)):
            self.text(x, y + i * leading, chunk, size=size, fill=fill, weight=weight,
                      family=family, anchor=anchor)

    # -- composites ---------------------------------------------------------
    def chip(self, x, y, label, fill=SOFT, fg=MUTED, size=13, padx=11, h=26, mono=True,
             weight="600"):
        w = int(len(label) * size * (0.62 if mono else 0.55)) + padx * 2
        self.rect(x, y, w, h, fill=fill, r=h // 2)
        self.text(x + padx, y + h // 2 + size * 0.36, label, size=size, fill=fg,
                  weight=weight, mono=mono, spacing="0.04em")
        return w

    def card(self, x, y, w, h, title=None, body=None, accent=None, fill=WHITE,
             stroke=LINE, title_size=20, body_size=15, pad=18, width=44):
        self.rect(x, y, w, h, fill=fill, r=14, stroke=stroke)
        ty = y + pad + title_size * 0.75
        if accent:
            self.rect(x, y, w, 4, fill=accent, r=2)
        if title:
            self.text(x + pad, ty, title, size=title_size, weight="700")
        if body:
            self.para(x + pad, ty + body_size + 8, body, width=width, size=body_size)

    def arrow(self, x1, y1, x2, y2, stroke=MUTED, sw=1.8, dash=None):
        self.line(x1, y1, x2, y2, stroke=stroke, sw=sw, dash=dash, arrow=True)

    # -- output -------------------------------------------------------------
    def render(self) -> str:
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" '
                f'height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                '<defs>'
                '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" '
                'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                f'<path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/>'
                '</marker>'
                '</defs>')
        return head + "".join(self.parts) + "</svg>"


def _wrap(s: str, width: int) -> list[str]:
    words, lines, cur = s.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines


def mark(svg: Svg, x: float, y: float, size: float, ink=INK, paper=None, sw=None):
    """The mark: the same moment, looked at twice — a solid thought and an open one.

    The right circle is filled with the background colour before it is stroked, so it
    cuts a clean lens out of the left one. That knockout is what keeps the mark legible
    at 16 pixels, where two overlapping strokes would turn into a smudge.
    """
    r = size * 0.185
    cy = y + size / 2
    sw = sw if sw is not None else size * 0.085
    cx1 = x + size * 0.28
    cx2 = x + size * 0.72
    svg.circle(cx1, cy, r, fill=ink)
    if paper:
        svg.circle(cx2, cy, r + sw / 2, fill=paper)
    svg.circle(cx2, cy, r, fill=paper if paper else "none", stroke=ink, sw=sw)
