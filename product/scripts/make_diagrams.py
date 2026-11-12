#!/usr/bin/env python3
"""
scripts/make_diagrams.py — the four story diagrams.

    python3 scripts/make_diagrams.py            # write assets/svg + assets/png
    python3 scripts/make_diagrams.py --only flow

  flow       what the product does, in one read
  verdicts   the same $249, three different months, three different answers
  defer      the hero path — pay before ship, end to end
  clusters   where this idea sits in a field of 549 repos
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from asset_kit import DECLINE, DEFER, INK, LINE, MUTED, OFFER, PAPER, WHITE, Svg  # noqa: E402
from diagram_kit import M, W, button, head, run  # noqa: E402


def flow():
    svg = Svg(W, 700)
    head(svg, "the decision", "One extra question at the moment of the split")
    left = [("The shopper's month", "paydays, rent, the car loan — as of today", 210),
            ("This purchase", "$249.00 at Northwind Audio", 340)]
    for title, body, y in left:
        svg.card(M, y, 320, 110, title=title, body=body, width=34, title_size=19)
    svg.arrow(M + 322, 265, 466, 300)
    svg.arrow(M + 322, 395, 466, 348)

    svg.rect(470, 200, 310, 250, fill=WHITE, r=14, stroke=LINE)
    svg.text(492, 238, "45-day projection", size=19, weight="700")
    svg.para(492, 266, "Every payday against every bill, day by day.",
             width=34, size=15, leading=21)
    pts = [(492, 388), (520, 362), (548, 376), (576, 340), (604, 356), (632, 316),
           (660, 344), (688, 396), (716, 366), (752, 380)]
    svg.path("M " + " L ".join(f"{x},{y}" for x, y in pts), stroke=MUTED, sw=2.2)
    svg.line(492, 372, 752, 372, stroke=DECLINE, sw=1.6, dash="5 5")
    svg.text(492, 428, "floor", size=12, fill=DECLINE, mono=True)

    svg.arrow(782, 322, 858, 322)
    svg.rect(860, 246, 252, 152, fill=WHITE, r=14, stroke=LINE)
    svg.text(882, 284, "The floor test", size=19, weight="700")
    svg.para(882, 312, "max(10% of monthly income, $50)", width=25, size=15, leading=21)
    svg.text(882, 378, "never below it, not once", size=13, fill=MUTED, mono=True)

    svg.line(1112, 322, 1132, 322, stroke=MUTED, sw=1.8)
    svg.line(1132, 224, 1132, 544, stroke=MUTED, sw=1.8)
    outs = [("OFFER", "every instalment clears the floor", OFFER, 176),
            ("DEFER", "it fits — on payday", DEFER, 336),
            ("DECLINE", "not this month, and here is why", DECLINE, 496)]
    for word, note, colour, y in outs:
        svg.arrow(1132, y + 48, 1148, y + 48)
        svg.rect(1148, y, 188, 96, fill=WHITE, r=12, stroke=LINE)
        svg.rect(1148, y, 5, 96, fill=colour, r=2)
        svg.text(1166, y + 34, word, size=16, fill=colour, weight="700", spacing="0.06em")
        svg.para(1166, y + 58, note, width=22, size=13, leading=17)

    svg.text(M, 664, "Everything after the floor test is arithmetic. No model decides "
             "anything here.", size=15, fill=MUTED)
    return svg


def verdicts():
    svg = Svg(W, 700)
    head(svg, "three answers", "The same $249.00, three different months")
    cols = [
        ("OFFER", "Fits today", "You can spread this over four payments",
         "Your balance stays above your floor every week until the last payment. The first "
         "is today.", "Pay in four", OFFER),
        ("DEFER", "Fits on payday", "Pay on Sat 15 Nov — and it ships once you've paid",
         "Taking $249.00 today would leave you short before your next payday. Nothing is "
         "charged now and the price is held.", "Hold it, pay 15 Nov", DEFER),
        ("DECLINE", "Not this month", "This one doesn't fit right now",
         "Paying $249.00 today leaves you short — the 4th payment on a plan you already "
         "have lands around 22 Dec. Up to $140.00 would work today.", "Pick something "
         "smaller", DECLINE),
    ]
    for i, (word, kicker, title, why, action, colour) in enumerate(cols):
        x = M + i * 424
        svg.rect(x, 170, 400, 430, fill=WHITE, r=16, stroke=LINE)
        svg.rect(x, 170, 400, 5, fill=colour, r=2)
        svg.text(x + 26, 216, word, size=15, fill=colour, weight="700", mono=True,
                 spacing="0.12em")
        svg.text(x + 26, 250, kicker.upper(), size=13, fill=MUTED, weight="700",
                 spacing="0.1em")
        svg.para(x + 26, 296, title, width=27, size=22, fill=INK, weight="700", leading=30)
        svg.para(x + 26, 396, why, width=40, size=16, fill=MUTED, leading=24)
        button(svg, x + 26, 520, action)
    svg.para(M, 636, "These are the sentences the product actually renders. The words "
             "OFFER / DEFER / DECLINE stay in small type — a shopper reads the sentence.",
             width=110, size=15)
    return svg


def defer():
    svg = Svg(W, 600)
    head(svg, "the hero path", "DEFER is pay-before-ship. Nobody lends anybody anything.")
    steps = [("1", "Invoice dated to payday", "the engine's payday maths sets the due date",
              "POST /v2/invoicing/invoices"),
             ("2", "Shopper pays on the day", "a real PayPal invoice, a real payment",
              "recipient_view_url"),
             ("3", "PayPal says it is paid", "signature verified before anything moves",
              "INVOICING.INVOICE.PAID"),
             ("4", "The merchant ships", "and only now — the state must be PAID",
              "fulfil() raises otherwise")]
    for i, (n, title, body, api) in enumerate(steps):
        x = M + i * 322
        svg.rect(x, 176, 296, 250, fill=WHITE, r=14, stroke=LINE)
        svg.circle(x + 34, 214, 17, fill=INK)
        svg.text(x + 34, 220, n, size=16, fill=WHITE, weight="700", anchor="middle")
        svg.para(x + 24, 268, title, width=22, size=18, fill=INK, weight="700", leading=24)
        svg.para(x + 24, 326, body, width=34, size=15, fill=MUTED, leading=22)
        svg.text(x + 24, 398, api, size=12, fill=MUTED, mono=True)
        if i < 3:
            svg.arrow(x + 300, 300, x + 318, 300)
    svg.rect(M, 466, W - 2 * M, 96, fill=INK, r=14)
    svg.text(M + 28, 502, "No merchant credit. No receivable. No interest.", size=22,
             fill=WHITE, weight="700")
    svg.text(M + 28, 536, "The sale moves to a date the shopper can actually meet — the "
             "trade is timing, not volume.", size=16, fill="#c7ccd4")
    return svg


def clusters():
    svg = Svg(W, 720)
    head(svg, "the field", "Where this idea sits in 549 scanned repos")
    rows = [("mandate / guardrails", 86, False), ("invoice / accounts payable", 60, False),
            ("reconciliation & reporting", 51, False), ("dispute / chargeback", 49, False),
            ("shopping agent", 47, False), ("agent trust & identity", 38, False),
            ("payouts / gig work", 32, False), ("fraud & scams", 28, False),
            ("accessibility", 27, False), ("subscriptions", 21, False),
            ("credit / BNPL", 3, True)]
    x0, bar_x, bar_w = M, M + 330, 620
    for i, (label, n, ours) in enumerate(rows):
        y = 170 + i * 44
        colour = OFFER if ours else "#b6bec9"
        svg.text(x0, y + 18, label, size=16, fill=INK if ours else MUTED,
                 weight="700" if ours else "400")
        w = max(6, int(bar_w * n / 86))
        if ours:
            svg.rect(M - 12, y - 9, 990, 44, fill="#eef7f2", r=8)
        svg.rect(bar_x, y, bar_w, 26, fill="#e9ecf0", r=6)
        svg.rect(bar_x, y, w, 26, fill=colour, r=6)
        svg.text(bar_x + bar_w + 16, y + 19, str(n), size=16,
                 fill=OFFER if ours else MUTED, weight="700" if ours else "400", mono=True)
    svg.text(bar_x, 170 + len(rows) * 44 + 30,
             "entries per cluster, counted 1 Nov 2026", size=14, fill=MUTED, mono=True)
    svg.rect(M + 1000, 176, 336, 200, fill=WHITE, r=14, stroke=LINE)
    svg.text(M + 1022, 214, "Our cluster", size=13, fill=MUTED, weight="700",
             mono=True, spacing="0.1em")
    svg.text(M + 1022, 262, "3 entries", size=34, fill=OFFER, weight="700")
    svg.para(M + 1022, 292, "average depth 1.7 of 13 markers. The crowded clusters "
             "average 3.4–4.9 and have 30 to 80 entries.", width=34, size=15, leading=21)
    svg.para(M + 1000, 420, "Being early in a thin cluster is not the same as being good. "
             "It does mean a judge will not have seen this idea four times before lunch.",
             width=44, size=15, leading=22)
    return svg

DIAGRAMS = {"flow": flow, "verdicts": verdicts, "defer": defer, "clusters": clusters}

if __name__ == "__main__":
    raise SystemExit(run(DIAGRAMS))
