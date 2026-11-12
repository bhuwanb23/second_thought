#!/usr/bin/env python3
"""
scripts/make_diagrams_tech.py — the three system diagrams.

    python3 scripts/make_diagrams_tech.py
    python3 scripts/make_diagrams_tech.py --only gate

  architecture  four layers, one boundary, zero dependencies
  ai-boundary   the rule: the model supplies facts, the engine supplies the verdict
  gate          why a tampered approval cannot move money
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from asset_kit import DECLINE, INK, LINE, MUTED, SOFT, WHITE, Svg  # noqa: E402
from diagram_kit import M, W, head, run  # noqa: E402


def architecture():
    svg = Svg(W, 700)
    head(svg, "the system", "Four layers, one boundary, zero dependencies")

    layers = [("interfaces/", "http · sessions · screens · badges · webhook endpoint", 176),
              ("app/", "checkout · reservations · approvals · ports", 268),
              ("domain/", "cash flow · the verdict rules — deterministic, no I/O", 360),
              ("infra/", "PayPal adapter · simulated gateway · SQLite · RSA · webhooks", 470)]
    for name, note, y in layers:
        svg.rect(M, y, 580, 76, fill=WHITE, r=12, stroke=LINE)
        svg.text(M + 22, y + 32, name, size=17, fill=INK, weight="700", mono=True)
        svg.text(M + 22, y + 58, note, size=14, fill=MUTED)
    for i in range(2):
        svg.arrow(M + 290, 252 + i * 92, M + 290, 266 + i * 92)

    svg.text(700, 160, "BEHIND ONE PROTOCOL EACH", size=13, fill=MUTED, weight="700",
             mono=True, spacing="0.12em")
    adapters = [("PayPal sandbox", "Orders v2 · Invoicing v2 · webhooks · OAuth 2", 176),
                ("The model", "OpenAI-compatible · temp 0 · JSON mode", 292),
                ("SQLite + memory", "profiles, reservations, invoices", 408)]
    for title, note, y in adapters:
        svg.rect(700, y, 340, 96, fill=WHITE, r=12, stroke=LINE)
        svg.text(722, y + 34, title, size=17, fill=INK, weight="700")
        svg.text(722, y + 62, note, size=13, fill=MUTED)
    svg.arrow(M + 580, 508, 698, 508, dash="6 6")
    svg.text(M + 596, 496, "HTTPS", size=12, fill=MUTED, mono=True)

    svg.rect(1076, 176, 260, 156, fill=WHITE, r=12, stroke=LINE)
    svg.text(1098, 210, "The rule", size=17, fill=INK, weight="700")
    svg.para(1098, 238, "the model supplies facts. The engine supplies the verdict.",
             width=24, size=15, leading=21)
    svg.rect(1076, 348, 260, 156, fill=WHITE, r=12, stroke=LINE)
    svg.text(1098, 382, "Honest labels", size=17, fill=INK, weight="700")
    svg.para(1098, 410, "AI · LLM-MOCK and PAYMENTS · SIMULATED until real credentials "
             "load, on the screen.", width=24, size=15, leading=21)

    svg.rect(M, 596, 580, 60, fill=SOFT, r=12)
    svg.text(M + 20, 622, "165 tests · 0.7 seconds · standard library only", size=15,
             fill=INK, weight="700")
    svg.text(M + 20, 644, "no third-party packages, no build step, no network", size=13,
             fill=MUTED)
    return svg


def ai_boundary():
    svg = Svg(W, 640)
    head(svg, "the boundary", "A model that is not allowed to decide anything")
    svg.card(M, 176, 300, 180, title="What the shopper typed",
             body="\u201csalary's 2,400 on the 15th, rent's 1,375 on the 1st, car loan 312 "
                  "every second friday\u201d", width=30, title_size=18)
    svg.arrow(M + 304, 266, M + 352, 266)
    svg.card(M + 356, 176, 250, 180, title="The model",
             body="chat completions · temperature 0 · JSON mode", width=26, title_size=18)
    svg.arrow(M + 610, 266, M + 658, 266)
    svg.card(M + 662, 176, 300, 180, title="Dated amounts",
             body="with a confidence per field: payday $2,400 on the 15th · rent $1,375 "
                  "on the 1st · car loan $312, unsure which friday", width=32,
             title_size=18)

    wall_x = M + 996
    svg.line(wall_x, 160, wall_x, 372, stroke=DECLINE, sw=2, dash="7 6")
    svg.text(wall_x - 10, 144, "no code path crosses here", size=13, fill=DECLINE,
             mono=True, anchor="end")

    svg.card(M + 1016, 176, 254, 180, title="The engine",
             body="45-day projection, the floor test, one of three answers — the same "
                  "result every run", width=26, title_size=18)

    guards = [("low confidence", "flagged to the shopper, not trusted"),
              ("nothing readable", "answer degrades to partial, never a guess"),
              ("demo-grade input", "the agent raises; the engine never sees it"),
              ("junk wording", "the verdict does not move — there is a test for this")]
    for i, (left, right) in enumerate(guards):
        y = 420 + (i // 2) * 96
        x = M + (i % 2) * 636
        svg.rect(x, y, 600, 76, fill=WHITE, r=10, stroke=LINE)
        svg.text(x + 20, y + 30, left, size=15, fill=INK, weight="700")
        svg.text(x + 20, y + 56, right, size=15, fill=MUTED)
    return svg


def gate():
    svg = Svg(W, 600)
    head(svg, "the gate", "A tampered approval cannot move money")
    svg.card(M, 176, 300, 170, title="1 · A plan is proposed",
             body="the engine decides, the app builds the exact arguments", width=30,
             title_size=18)
    svg.arrow(M + 304, 261, M + 352, 261)
    svg.card(M + 356, 176, 330, 170, title="2 · A single-use token",
             body="HMAC over the tool name and every argument · short TTL · one redemption",
             width=34, title_size=18)
    svg.arrow(M + 690, 261, M + 738, 261)
    svg.card(M + 742, 176, 300, 170, title="3 · A human redeems it",
             body="nothing reaches PayPal until this happens", width=30, title_size=18)
    svg.arrow(M + 1046, 261, M + 1094, 261)
    svg.rect(M + 1096, 206, 176, 110, fill=WHITE, r=12, stroke=LINE)
    svg.text(M + 1116, 246, "PayPal", size=18, fill=INK, weight="700")
    svg.text(M + 1116, 274, "sandbox call", size=14, fill=MUTED)

    refuses = [("amount edited", "the signature no longer matches"),
               ("token replayed", "already used — one redemption only"),
               ("token expired", "TTL is measured, not assumed"),
               ("foreign session", "a token signed by another visitor's key")]
    svg.text(M, 402, "ALL FOUR ARE REFUSED WITH 403, BEFORE THE GATEWAY IS CALLED", size=14,
             fill=MUTED, weight="700", mono=True, spacing="0.08em")
    for i, (left, right) in enumerate(refuses):
        x = M + i * 322
        svg.rect(x, 428, 296, 96, fill=WHITE, r=10, stroke=LINE)
        svg.text(x + 18, 462, left, size=16, fill=DECLINE, weight="700")
        svg.para(x + 18, 488, right, width=30, size=14)
    return svg

DIAGRAMS = {"architecture": architecture, "ai-boundary": ai_boundary, "gate": gate}

if __name__ == "__main__":
    raise SystemExit(run(DIAGRAMS))
