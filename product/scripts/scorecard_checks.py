"""
scripts/scorecard_checks.py — the proxies behind scorecard.py.

One function per judged criterion. Each `add(...)` line is a claim with the evidence
attached, so a score can always be traced back to something that ran. Split out of
scorecard.py only to keep both files under the house limit.
"""

from __future__ import annotations

import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
RESEARCH = REPO / "docs" / "research"

sys.path.insert(0, str(ROOT))

results: list[tuple[str, str, bool, float, str]] = []


def add(criterion, check, ok, weight, evidence):
    results.append((criterion, check, bool(ok), weight, evidence))


def tech(ctx):
    c = "Technological Implementation"
    try:
        out = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                             cwd=ROOT, capture_output=True, text=True, timeout=300)
        m = re.search(r"Ran (\d+) tests", out.stderr + out.stdout)
        n = int(m.group(1)) if m else 0
        add(c, "the test suite runs green", out.returncode == 0 and n > 0, 3,
            f"{n} tests, {'OK' if out.returncode == 0 else 'FAILING'}")
    except Exception as exc:
        add(c, "the test suite runs green", False, 3, str(exc))

    live, live_note = None, "no live run in artifacts/v3"
    for f in sorted((ROOT / "artifacts" / "v3").glob("*/evidence.json")) if (ROOT / "artifacts" / "v3").exists() else []:
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if "LIVE" in str(d.get("mode", "")):
            checks = d.get("checks", [])
            passed = all(x.get("status") == "PASS" for x in checks) and len(checks) >= 5
            live, live_note = passed, f"{f.parent.name}: {len(checks)} checks, " \
                                      f"{'all PASS' if passed else 'some failed'}"
    add(c, "a real PayPal sandbox run with every call PASS", live, 4, live_note)

    wh = bool(getattr(getattr(ctx.settings, "paypal", None), "webhook_id", ""))
    add(c, "webhook id configured, signature verification armed", wh, 1,
        "PAYPAL_WEBHOOK_ID set" if wh else "not set — a verified webhook is unproven")

    idem = False
    if live:
        for f in sorted((ROOT / "artifacts" / "v3").glob("*/evidence.json")):
            try:
                d = json.loads(f.read_text())
            except Exception:
                continue
            if "LIVE" in str(d.get("mode", "")) and any(
                    x.get("check") == "idempotency" and x.get("status") == "PASS"
                    for x in d.get("checks", [])):
                idem = True
    add(c, "idempotency proven against PayPal, not a fake", idem, 1,
        "same PayPal-Request-Id returned one order" if idem else "unproven live")

    try:
        out = subprocess.run([sys.executable, "-m", "unittest", "tests.test_personas", "-q"],
                             cwd=ROOT, capture_output=True, text=True, timeout=120)
        add(c, "the demo still works during the judging window", out.returncode == 0, 1,
            "60-day walk to January: all three verdicts" if out.returncode == 0
            else "a pinned date breaks the demo later")
    except Exception as exc:
        add(c, "the demo still works during the judging window", False, 1, str(exc))

    status = ctx.fetch("/proof")
    add(c, "a /proof page listing measured numbers", bool(status and status[0] == 200), 1,
        f"HTTP {status[0]}" if status else "no --url, or no /proof route")

    sec = (ROOT / "SECURITY.md").exists()
    add(c, "a threat model a judge can read", sec, 1,
        "SECURITY.md present" if sec else "no SECURITY.md — the top decile has one")


def design(ctx):
    c = "Design"
    body = b""
    if ctx.url:
        got = ctx.fetch("/")
        if got:
            body = got[1]
        ok = bool(got and got[0] == 200)
        ev = f"HTTP {got[0]}, {len(body)} bytes" if got else "unreachable"
    else:
        try:
            from secondthought.config import AppSettings
            from secondthought.interfaces.http import App
            app = App(AppSettings(approval_secret="scorecard"))
            out = {}

            def sr(s, h):
                out["s"] = s
                out["h"] = dict(h)

            environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/", "QUERY_STRING": "",
                       "CONTENT_LENGTH": "0", "wsgi.input": io.BytesIO(b""),
                       "REMOTE_ADDR": "198.51.100.7"}
            body = b"".join(app(environ, sr))
            ok = out.get("s") == "200 OK"
            ev = f"local WSGI: {out.get('s')}, {len(body)} bytes"
            app.close()
        except Exception as exc:
            ok, ev = False, str(exc)
    add(c, "a real screen a stranger can look at", ok, 3, ev)

    if body:
        text = body.decode("utf-8", "replace")
        add(c, "the three outcomes are visible without a login", text.count('data-persona="') == 3, 2,
            f"{text.count('data-persona=\"')} months on the first screen")
        add(c, "it loads nothing from the network", not any(x in text for x in
            ('src="http', 'href="http', "@import")), 1, "inline CSS/JS only")
        add(c, "an empty state and an error state exist", "Pick one of the three" in text, 1,
            "placeholder before any click" if "Pick one of the three" in text else "none")
        add(c, "it is usable on a phone", 'name="viewport"' in text, 1,
            "viewport meta present" if 'name="viewport"' in text else "missing")
    else:
        for label, w in (("the three outcomes are visible without a login", 2),
                         ("it loads nothing from the network", 1),
                         ("an empty state and an error state exist", 1),
                         ("it is usable on a phone", 1)):
            add(c, label, False, w, "no page to inspect")
    add(c, "a public URL a judge can open", bool(ctx.url and ctx.fetch("/")), 2,
        ctx.url or "not deployed — every design claim is unverifiable")


def impact(ctx):
    c = "Potential Impact"
    r = ctx.readme
    add(c, "a named audience in the README", bool(re.search(r"shopper|merchant|payday|BNPL", r, re.I)),
        2, "names who this is for")
    cited = len(re.findall(r"\b(CFPB|LendingTree|Pew|Federal Reserve|Bankrate|%)\b", r))
    add(c, "sourced pain, not adjectives", cited >= 3, 2, f"{cited} citation markers in README")
    add(c, "a privacy line and the real data path", bool(re.search(r"privacy|we store|we send|stays in", r, re.I)),
        2, "stated" if re.search(r"privacy|we store|we send|stays in", r, re.I) else "missing — a judge looks for it")
    try:
        from datetime import date
        from secondthought.app.approvals import ApprovalGate
        from secondthought.app.checkout import Checkout, CheckoutService
        from secondthought.domain.engine import Policy
        from secondthought.infra.db import Database, LedgerRepo, ProfileRepo, ReservationRepo
        from secondthought.infra.gateway import SimulatedGateway
        from secondthought.interfaces.personas import personas
        today = date.today()
        db = Database(":memory:")
        profiles = ProfileRepo(db)
        from datetime import datetime
        for key, persona in personas(today).items():
            profiles.save(key, persona["profile"], datetime.combine(today, datetime.min.time()))
        svc = CheckoutService(gateway=SimulatedGateway(), profiles=profiles,
                              reservations=ReservationRepo(db), ledger=LedgerRepo(db),
                              approvals=ApprovalGate(secret="s"), policy=Policy())
        verdicts = {}
        for key in ("ada", "ben", "cleo"):
            verdicts[key] = svc.quote(Checkout(key, "Northwind Audio", 24900, "USD"), today)["verdict"]
        db.close()
        add(c, "the refusal actually happens in the product", verdicts["cleo"] == "DECLINE", 3,
            f"today: " + ", ".join(f"{k} {v}" for k, v in verdicts.items()))
    except Exception as exc:
        add(c, "the refusal actually happens in the product", False, 3, f"{type(exc).__name__}: {exc}")
    add(c, "evidence that anyone outside the team has tried it", False, 2,
        "n = 0 — V7 and V8 both unrun. Say so; do not imply otherwise")


def innovation(ctx):
    c = "Innovation / Idea"
    r = ctx.readme
    add(c, "the difference is stated in one line", bool(re.search(r"not another|differs|only|no merchant credit|pay-before-ship", r, re.I)),
        2, "README carries the claim")
    field = RESEARCH / "03_field" / "FIELD_MAP.md"
    open_cluster = False
    if field.exists():
        m = re.search(r"\|\s*credit-bnpl\s*\|\s*(\d+)\s*\|", field.read_text())
        open_cluster = bool(m and int(m.group(1)) <= 10)
        ev = f"credit-bnpl: {m.group(1)} entries in the field scan" if m else "cluster row not found"
    else:
        ev = "no field scan on disk"
    add(c, "the cluster is measurably thin", open_cluster, 2, ev)
    has_copy = ("doesn't fit" in r.lower() or "does not fit" in r.lower()
                or "not this month" in r.lower())
    add(c, "the inversion is the demo, not a footnote", has_copy, 2,
        "the refusal copy is in the README" if has_copy
        else "the refusal is described, never shown — quote the screen")


def presentation(ctx):
    c = "Presentation"
    manifest = REPO / "docs" / "plan" / "video.json"
    data = {}
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
        except Exception:
            data = {}
    url = str(data.get("url", ""))
    add(c, "a public video exists", bool(url.startswith("http")), 3,
        url or "no docs/plan/video.json — nothing recorded")
    dur = data.get("duration_seconds")
    add(c, "it is under 3:00", bool(isinstance(dur, (int, float)) and 0 < dur <= 180), 2,
        f"{dur}s" if dur else "unknown")
    add(c, "it shows a failure path, not only a happy path", bool(data.get("shows_failure_path")), 2,
        "declared" if data.get("shows_failure_path") else "not declared")


