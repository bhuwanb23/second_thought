"""
infra/evidence.py — the record a judge could audit.

V3's pass condition is not "it ran". It is: *every artifact is visible in the
actual PayPal dashboard*. So each check writes a row carrying (a) the ID PayPal
returned, (b) the exact place in the dashboard where that ID can be found, and
(c) the requests that produced it. Terminal output is a claim; the artifact is
the proof.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

DASHBOARD = {
    "oauth": "Developer Dashboard → Apps & Credentials → Sandbox → your app "
             "(the same client ID whose token you are holding)",
    "order": "sandbox.paypal.com/activities — sign in as the SANDBOX BUSINESS "
             "account, filter to today, find the transaction ID",
    "authorisation": "Same Activity row → the order's detail shows the "
                     "authorisation and its status",
    "void": "Same Activity row → status must read Voided, not Captured "
            "(also GET /v2/payments/authorizations/{id})",
    "invoice": "sandbox.paypal.com/invoice/manage/invoices — sign in as the "
               "sandbox business, status Draft or Unpaid, Due date column",
    "idempotency": "Activity shows ONE order for the shared PayPal-Request-Id; "
                   "the second POST must not add a row",
}


class Recorder:
    def __init__(self, out_dir: str | Path, mode: str):
        self.mode = mode
        self.rows: list[dict] = []
        self.started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        self.dir = Path(out_dir) / stamp
        self.dir.mkdir(parents=True, exist_ok=True)

    def check(self, key: str, title: str, status: str, evidence: dict,
              dashboard: str | None = None, notes: str = "") -> dict:
        row = {
            "check": key,
            "title": title,
            "status": status,                 # PASS | FAIL | SKIP
            "evidence": evidence,
            "where_to_verify": dashboard or DASHBOARD.get(key, ""),
            "notes": notes,
        }
        self.rows.append(row)
        return row

    # -- output -------------------------------------------------------------
    def write(self, extra: dict | None = None) -> Path:
        payload = {"mode": self.mode, "started": self.started,
                   "finished": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "checks": self.rows, "context": extra or {}}
        (self.dir / "evidence.json").write_text(json.dumps(payload, indent=2, default=str))
        (self.dir / "TRANSCRIPT.md").write_text(self._transcript(payload))
        return self.dir

    def _transcript(self, payload: dict) -> str:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️"}
        out = [f"# V3 evidence — {payload['mode']}", "",
               f"Run {payload['started']} → {payload['finished']}", "",
               "| # | Check | Result | Artifact | Where a judge finds it |",
               "|---|---|---|---|---|"]
        for i, r in enumerate(self.rows, 1):
            art = ", ".join(f"`{v}`" for k, v in r["evidence"].items()
                            if isinstance(v, (str, int)) and _looks_like_id(k, v))
            out.append(f"| {i} | {r['title']} | {icon.get(r['status'], '·')} "
                       f"{r['status']} | {art or '—'} | {r['where_to_verify']} |")
        for r in self.rows:
            out += ["", f"## {icon.get(r['status'], '·')} {r['title']}", "",
                    "```json", json.dumps(r["evidence"], indent=2, default=str), "```"]
            if r["notes"]:
                out += ["", r["notes"]]
        return "\n".join(out) + "\n"


_PREFIXES = ("INV2-", "ORD", "AUTH-", "CAP-", "A21", "PAY-", "PAYID", "8AA", "5O1")


def _looks_like_id(_key: str, value) -> bool:
    """Only PayPal-shaped identifiers reach the summary table."""
    if isinstance(value, (bool, int)) or not isinstance(value, str):
        return False
    return value.upper().startswith(_PREFIXES) or (
        len(value) >= 14 and value.replace("-", "").isalnum() and
        sum(ch.isdigit() for ch in value) >= 4)
