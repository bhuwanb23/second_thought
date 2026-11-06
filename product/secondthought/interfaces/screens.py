"""
interfaces/screens.py — the one page a stranger sees first.

V8 asks a person who has never seen this to reach a verdict and explain *why*, in
two minutes, with nobody talking. That is a copy problem before it is a design
problem, so the rule here is blunt:

  **Internal vocabulary never reaches the shopper.**

A shopper does not get a "DEFER" and a "collision". They get "Pay on Fri 6 Nov —
and it ships once you've paid" and a sentence about their car loan. The canonical
verdict name survives as a small label, because the pitch and the video use it,
but it is never the sentence you have to understand.

`tests/test_screens.py::PlainLanguage` fails the build if a banned term appears in
any sentence rendered for a shopper. That is a proxy for V8.4, not a substitute:
copy an audit can check is not the same as copy a stranger understands.
"""

from __future__ import annotations

from datetime import date
from html import escape

from .badge import badges

# Terms that must not appear in a shopper-facing *sentence*. The verdict label is
# exempt — it is a name, not an explanation.
BANNED_IN_EXPLANATION = (
    "verdict", "collision", "reservation", "authorisation", "authorize", "authorise",
    "instrument", "fulfilment", "risk_bearer", "answer_quality", "extraction",
    "overdraw", "buffer", "instalment", "installment", "minor units", "policy", "engine",
    "token", "null", "none", "api", "json", "def ", "()",
)

PLAIN_LABEL = {"OFFER": "OFFER · fits today",
               "DEFER": "DEFER · fits on payday",
               "DECLINE": "DECLINE · not this month"}


def money(minor) -> str:
    if minor is None:
        return "—"
    return f"${minor / 100:,.2f}"


def _day(iso) -> str:
    if not iso:
        return "your payday"
    try:
        return date.fromisoformat(str(iso)[:10]).strftime("%a %d %b").replace(" 0", " ")
    except ValueError:
        return "your payday"


def plain_collision(label) -> str:
    """The engine names a collision precisely. A shopper needs it in their words."""
    if not label:
        return ""
    text = str(label)
    if text.startswith("instalment"):
        # "instalment 4 of 4" -> "the 4th payment on a plan you already have"
        parts = text.replace("instalment", "").split("of")
        try:
            n = int(parts[0].strip())
            suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
            return f"the {n}{suffix} payment on a plan you already have"
        except (ValueError, IndexError):
            return "a payment on a plan you already have"
    return text


def explain(q: dict) -> dict:
    """The verdict in words a person would use. Never internal vocabulary."""
    verdict = q.get("verdict", "")
    amount = money(q.get("amount_minor"))
    if verdict == "OFFER":
        return {"label": PLAIN_LABEL["OFFER"],
                "title": "You can spread this over four payments",
                "why": ("Your balance stays above your safety floor every week until the "
                        "last payment, so all four can go ahead. The first is today."),
                "action": "Pay in four"}
    if verdict == "DEFER":
        pay_on = _day(q.get("pay_on"))
        return {"label": PLAIN_LABEL["DEFER"],
                "title": f"Pay on {pay_on} — and it ships once you've paid",
                "why": (f"Taking {amount} today would leave you short before you're next "
                        f"paid. Nothing is charged now, the price is held, and it goes out "
                        f"the door after your payment clears."),
                "action": f"Hold it, pay {pay_on}"}
    if verdict == "DECLINE":
        what, when = plain_collision(q.get("collision")), _day(q.get("collision_date"))
        safe = q.get("safe_amount_minor")
        because = (f"because {what} lands around {when}" if what
                   else "because it would take you past the point where you'd be short")
        fits = f" Up to {money(safe)} would work today." if safe else ""
        return {"label": PLAIN_LABEL["DECLINE"],
                "title": "This one doesn't fit right now",
                "why": f"Paying {amount} today leaves you short — {because}.{fits}",
                "action": "Pick something smaller"}
    return {"label": "no answer yet", "title": "Nothing to decide yet",
            "why": "Pick one of the three months above.", "action": ""}


def _card(persona_id: str, label: str, amount_minor: int) -> str:
    return ('<button class="who" data-persona="%s" data-amount="%d">'
            '<span class="who-name">%s</span>'
            '<span class="who-amount">%s</span></button>'
            % (escape(persona_id), amount_minor, escape(label), money(amount_minor)))


_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Second Thought - payday-aware checkout</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { margin:0; font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
         color:#14181f; background:#f6f7f9; }
  .wrap { max-width:760px; margin:0 auto; padding:32px 20px 64px; }
  h1 { font-size:26px; margin:0 0 6px; letter-spacing:-.01em; }
  .sub { color:#5b6472; margin:0 0 18px; }
  .badges { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:26px; }
  .badge { font:600 11px ui-monospace,monospace; letter-spacing:.06em; padding:4px 9px;
           border-radius:99px; background:#e8eaee; color:#5b6472; }
  .badge.on { background:#0f7b4f14; color:#0f7b4f; }
  h2 { font-size:13px; text-transform:uppercase; letter-spacing:.08em; color:#5b6472;
       margin:30px 0 10px; }
  .row { display:flex; gap:10px; flex-wrap:wrap; }
  .who { flex:1 1 190px; text-align:left; cursor:pointer; background:#fff;
         border:1px solid #dfe3e9; border-radius:12px; padding:14px 16px; font:inherit;
         display:flex; justify-content:space-between; align-items:center; gap:10px;
         color:inherit; }
  .who:hover { border-color:#b9c1cc; }
  .who[aria-pressed=true] { border-color:#14181f; box-shadow:0 0 0 2px #14181f11; }
  .who-name { font-size:14px; }
  .who-amount { font:600 13px ui-monospace,monospace; color:#5b6472; }
  #out { background:#fff; border:1px solid #dfe3e9; border-radius:14px; padding:22px 24px;
         margin-top:14px; min-height:96px; }
  #out h3 { margin:0 0 8px; font-size:20px; letter-spacing:-.01em; }
  #out p { margin:0 0 14px; color:#3b4453; }
  .act { display:inline-block; background:#14181f; color:#fff; border-radius:9px;
         padding:9px 16px; font-weight:600; font-size:14px; }
  .muted { color:#5b6472; font-size:14px; }
  textarea { width:100%; min-height:78px; border:1px solid #dfe3e9; border-radius:10px;
             padding:12px; font:inherit; resize:vertical; background:#fff; }
  .note { border-left:3px solid #dfe3e9; padding:2px 0 2px 12px; margin:8px 0;
          color:#3b4453; font-size:14px; }
  .flag { color:#8a5a00; }
  footer { margin-top:36px; color:#7a828f; font-size:13px; border-top:1px solid #e4e7ec;
           padding-top:14px; }
  @media (prefers-reduced-motion: no-preference) { .who { transition:border-color .12s; } }
</style></head>
<body><div class="wrap">
  <h1>Second Thought</h1>
  <p class="sub">A checkout that sometimes says <em>not yet</em> &mdash; and tells you why.</p>
  <div class="badges">__BADGES__</div>

  <h2>1 &middot; Pick someone's month</h2>
  <div class="row" id="who">__CARDS__</div>

  <div id="out"><p class="muted">Pick one of the three and the answer appears here.</p></div>

  <h2>2 &middot; Or describe your own month</h2>
  <textarea id="text" placeholder="e.g. salary 2,400 on the 15th, rent 1,375 on the 1st"></textarea>
  <div class="row" style="margin-top:10px">
    <button class="who" id="read" style="flex:0 0 auto"><span class="who-name">Read this</span></button>
    <span class="muted" style="align-self:center">It never decides anything &mdash; it only pulls
      out dates and amounts, and flags what it is unsure about.</span>
  </div>
  <div id="understood"></div>

  <footer>Money here is simulated. Nothing is charged and no real account is touched.
    What you type stays in this browser session.</footer>
</div>
<script>
var out = document.getElementById('out');
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
  });
}
function money(m) {
  return m == null ? '\\u2014' : '$' + (m / 100).toLocaleString(undefined,
    { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function show(d) {
  out.innerHTML = '<h3>' + esc(d.title) + '</h3><p>' + esc(d.why) + '</p>' +
    (d.action ? '<span class="act">' + esc(d.action) + '</span>' : '') +
    '<p class="muted" style="margin-top:16px">The answer: <b>' + esc(d.label) + '</b></p>';
}
var buttons = document.querySelectorAll('.who[data-persona]');
Array.prototype.forEach.call(buttons, function (b) {
  b.addEventListener('click', function () {
    Array.prototype.forEach.call(buttons, function (x) {
      x.setAttribute('aria-pressed', 'false');
    });
    b.setAttribute('aria-pressed', 'true');
    out.innerHTML = '<p class="muted">Working it out&hellip;</p>';
    fetch('/api/quote?persona=' + encodeURIComponent(b.dataset.persona))
      .then(function (r) { return r.json(); })
      .then(function (q) {
        if (q.error) { out.innerHTML = '<p class="muted">' + esc(q.error) + '</p>'; return; }
        show(q.explain || q);
      });
  });
});
document.getElementById('read').addEventListener('click', function () {
  var text = document.getElementById('text').value.trim();
  if (!text) { return; }
  var box = document.getElementById('understood');
  box.innerHTML = '<p class="muted">Reading&hellip;</p>';
  fetch('/api/extract', { method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text }) })
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.error) {
        box.innerHTML = '<p class="muted">' + esc(d.reason || d.error) + '</p>';
        return;
      }
      var e = d.extraction || {};
      var f = e.fields || {};
      var items = [];
      (f.obligations || []).forEach(function (o) { items.push(['bill', o]); });
      (f.paydays || []).forEach(function (o) { items.push(['payday', o]); });
      if (!items.length) {
        box.innerHTML = '<p class="muted">Nothing I could read as a dated amount. ' +
          'Nothing is decided from that.</p>';
        return;
      }
      var low = e.low_confidence || [];
      box.innerHTML = items.map(function (pair) {
        var o = pair[1];
        var unsure = low.some(function (x) { return x.indexOf(o.label) !== -1; });
        return '<div class="note">' + esc(pair[0]) + ' &middot; <b>' + esc(o.label) + '</b> ' +
          money(o.amount_minor) + ' on ' + esc(o.due) +
          (unsure ? '<span class="flag"> &mdash; not sure, please check</span>' : '') +
          '</div>';
      }).join('') + (e.needs_confirmation || []).map(function (q) {
        return '<div class="note flag">' + esc(q) + '</div>';
      }).join('');
    })
    .catch(function () {
      box.innerHTML = '<p class="muted">That request did not go through. Try again.</p>';
    });
});
</script>
</body></html>"""


def render_page(settings, personas: dict) -> str:
    badge_html = "".join(
        '<span class="badge%s" title="%s">%s</span>'
        % (" on" if b["live"] else "", escape(b["detail"]), escape(b["label"]))
        for b in badges(settings))
    cards = "".join(_card(k, v["label"], v["amount_minor"])
                    for k, v in personas.items())
    return _TEMPLATE.replace("__BADGES__", badge_html).replace("__CARDS__", cards)
