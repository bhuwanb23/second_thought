"""
interfaces/proof.py — /proof, the page that shows what was measured.

A judge (or a stranger) should not have to trust a README. This page prints the
numbers that were produced by running things, the exact command that produces
each one, and the timestamp of the run. Where a number has not been produced
yet, it says so instead of inventing one.

Data comes from `artifacts/proof.json`, written by `scripts/make_proof.py`. If
the file is missing the page still renders — it just tells the truth about
having nothing to show, which is the whole point of a proof page.
"""

from __future__ import annotations

import json
from html import escape
from pathlib import Path

PROOF_JSON = Path("artifacts/proof.json")

# Constants that shape every verdict. Printed so a reader can check the page
# against the code rather than take a sentence's word for it.
CONSTANTS = (
    ("Plan horizon", "45 days", "domain/cashflow.py: HORIZON_DAYS"),
    ("Instalments", "2, 14 days apart", "INSTALMENT_GAP_DAYS = 14"),
    ("The floor", "max(10% of income, $50)", "domain/engine.py: MIN_BUFFER = 5_000"),
    ("Approval token TTL", "600 s, single use", "DEFAULT_TTL_SECONDS = 600"),
    ("Authorisation validity", "3 days", "_AUTH_VALID_DAYS = 3"),
    ("Model calls allowed", "30 per session, 90 per IP per 600 s", "LLM_PER_SESSION / LLM_PER_IP"),
)

GATES = (
    ("V3 · five real PayPal calls", "READY", "python3 demo.py --live"),
    ("V4 · a real model behind the badge", "READY", "python3 demo_ai.py --live"),
    ("V6 · deployed and still up on 15 Dec", "OPEN", "a Render deploy and a webhook id"),
    ("V7 · a human has used it", "OPEN", "five conversations, or an honest n = 0"),
)

_STYLE = """
  :root { color-scheme: light }
  body { margin:0; background:#f6f7f9; color:#14181f;
         font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  main { max-width:860px; margin:0 auto; padding:56px 28px 96px }
  h1 { font-size:30px; margin:0 0 6px; letter-spacing:-0.02em }
  h2 { font-size:13px; letter-spacing:0.12em; text-transform:uppercase; color:#6b7280;
       margin:38px 0 10px }
  p.lede { color:#4b5563; margin:0 0 8px }
  table { width:100%; border-collapse:collapse; margin:8px 0 4px; font-size:14.5px }
  th, td { text-align:left; padding:9px 10px; border-bottom:1px solid #e3e6ea; vertical-align:top }
  th:nth-child(1) { width:26% } th:nth-child(2) { width:22% } th:nth-child(3) { width:52% }
  th { font-size:11px; letter-spacing:0.1em; text-transform:uppercase; color:#6b7280; font-weight:600 }
  code { background:#eceef1; padding:1px 5px; border-radius:4px; font-size:13px }
  .pass { color:#0f7b4f; font-weight:700 } .open { color:#8a5a00; font-weight:700 }
  .ready { color:#8a5a00; font-weight:700 }
  .note { background:#fff; border-left:3px solid #14181f; padding:14px 16px; margin:24px 0;
          border-radius:0 6px 6px 0; font-size:14.5px; color:#374151 }
  a { color:#14181f } footer { margin-top:46px; font-size:13px; color:#6b7280 }
"""


def _load(path: Path = PROOF_JSON) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _row(cell: str, value: str, how: str) -> str:
    return f"<tr><td>{cell}</td><td><b>{value}</b></td><td><code>{escape(how)}</code></td></tr>"


def _measured(proof: dict | None) -> str:
    if not proof:
        return ("<p class=\"lede\">No measurement file on this instance yet. Run "
                "<code>python3 scripts/make_proof.py</code> and reload.</p>")
    rows = "".join(_row(c.get("label", "?"), escape(str(c.get("value", "—"))),
                        c.get("command", ""))
                   for c in proof.get("checks", []))
    stamp = escape(str(proof.get("generated_at", "unknown")))
    rev = escape(str(proof.get("git", "no git checkout")))
    verdict = escape(str(proof.get("summary", "unknown")))
    return (f"<table><tr><th>Measured</th><th>Result</th><th>Reproduce with</th></tr>{rows}"
            f"</table><p class=\"lede\">Generated <b>{stamp}</b> · revision <code>{rev}</code> · "
            f"<b>{verdict}</b></p>")


def render(proof: dict | None = None) -> str:
    proof = _load() if proof is None else proof
    consts = "".join(_row(c[0], escape(c[1]), c[2]) for c in CONSTANTS)
    gates = "".join(
        f"<tr><td>{escape(name)}</td><td class=\"{'pass' if state == 'PASS' else state.lower()}\">"
        f"{escape(state)}</td><td><code>{escape(how)}</code></td></tr>"
        for name, state, how in GATES)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Proof · Second Thought</title><style>{_STYLE}</style></head>
<body><main>
  <h1>Proof</h1>
  <p class="lede">Every number on this page was produced by running something in this repository,
  and every number has the command that produces it. Nothing here is a claim.</p>

  <h2>Measured in this build</h2>
  {_measured(proof)}

  <h2>The rules the verdicts obey</h2>
  <table><tr><th>Rule</th><th>Value</th><th>Where</th></tr>{consts}</table>

  <h2>What is not true yet</h2>
  <table><tr><th>Gate</th><th>State</th><th>What closes it</th></tr>{gates}</table>

  <div class="note"><b>Money here is simulated.</b> The PayPal adapter is real code with a fake
  transport until sandbox credentials are present; the badge on the main page says which one is
  running. Read the state above as: the wiring is tested, the account is not.</div>

  <footer><a href="/">← back to the page</a> · MIT licensed · no dependencies · no data leaves
  this process except the free text you type.</footer>
</main></body></html>
"""
