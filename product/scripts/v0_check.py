#!/usr/bin/env python3
"""
v0_check.py — the V0 precondition gate.

    python3 scripts/v0_check.py           # all gates
    python3 scripts/v0_check.py --offline # skip the two network calls

Exit code 0 only if every automatable gate passes. MANUAL rows do not fail the
run, but they are printed as outstanding because a human must confirm them.

The point of this file is that five rows in a table are things a person can
convince themselves about. These are things a script can prove.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "secondthought"
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

PASS, FAIL, WARN, MANUAL = "PASS", "FAIL", "WARN", "MANUAL"
results: list[tuple[str, str, str, str]] = []   # id, title, status, detail


def record(gate: str, title: str, status: str, detail: str) -> None:
    results.append((gate, title, status, detail))


def load_env() -> dict[str, str]:
    """Real environment wins; .env fills the gaps. Values are never printed."""
    env = dict(os.environ)
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env.setdefault(k.strip(), v.strip())
    return env


# --------------------------------------------------------------------------
# 1. the env contract: code and .env.example must not drift
# --------------------------------------------------------------------------
def gate_env_contract(env: dict[str, str]) -> None:
    declared = set()
    if ENV_EXAMPLE.exists():
        for line in ENV_EXAMPLE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                declared.add(line.split("=", 1)[0].strip())

    # the contract is declared in config.py
    contract_src = (PKG / "config.py").read_text()
    m = re.search(r"ENV_CONTRACT = \((.*?)\)", contract_src, re.S)
    contract = set(re.findall(r'"([A-Z0-9_]+)"', m.group(1))) if m else set()

    # any environment read outside config.py is drift by definition
    strays = []
    for py in PKG.rglob("*.py"):
        if py.name == "config.py":
            continue
        for hit in re.finditer(r"(?:os\.environ(?:\.get)?[\[(]|getenv\()\s*[\"']([A-Z0-9_]+)",
                               py.read_text()):
            strays.append(f"{py.relative_to(ROOT)}:{hit.group(1)}")

    problems = []
    if contract - declared:
        problems.append(f"read by code, missing from .env.example: {sorted(contract - declared)}")
    if declared - contract:
        problems.append(f"in .env.example, never read: {sorted(declared - contract)}")
    if strays:
        problems.append(f"environment read outside config.py: {strays}")

    if problems:
        record("V0.5", ".env.example matches what the code reads", FAIL, "; ".join(problems))
    else:
        record("V0.5", ".env.example matches what the code reads", PASS,
               f"{len(contract)} variables, declared and used, one reader")


# --------------------------------------------------------------------------
# 2. PayPal: credentials present, and a real OAuth call succeeds
# --------------------------------------------------------------------------
def gate_paypal(env: dict[str, str], offline: bool) -> None:
    cid, secret = env.get("PAYPAL_CLIENT_ID", "").strip(), env.get("PAYPAL_CLIENT_SECRET", "").strip()
    if not (cid and secret):
        record("V0.1", "PayPal sandbox app credentials", FAIL,
               "PAYPAL_CLIENT_ID / SECRET not set — nothing downstream can be real")
        record("V0.2", "PayPal credentials actually work", FAIL, "skipped: no credentials")
        return
    hint = "looks like a sandbox id" if "sb" in cid.lower() else "no 'sb' marker — verify it is the Sandbox app"
    record("V0.1", "PayPal sandbox app credentials", PASS, f"present ({hint})")

    if offline:
        record("V0.2", "PayPal credentials actually work", MANUAL, "--offline: not called")
        return

    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    creds = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    req = urllib.request.Request(
        url, data=b"grant_type=client_credentials",
        headers={"Authorization": f"Basic {creds}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read())
        record("V0.2", "PayPal credentials actually work", PASS,
               f"OAuth 200, token_type={body.get('token_type')}, "
               f"expires_in={body.get('expires_in')}s (expiry {body.get('expires_in')})")
    except urllib.error.HTTPError as e:
        detail = {401: "401 — wrong client id/secret, or a Live app used against sandbox",
                  403: "403 — app lacks a required scope; create a fresh sandbox app"}.get(
                      e.code, f"HTTP {e.code}: {e.read()[:120]!r}")
        record("V0.2", "PayPal credentials actually work", FAIL, detail)
    except Exception as e:                                    # noqa: BLE001
        record("V0.2", "PayPal credentials actually work", FAIL, f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------
# 3. LLM: key present, and a free authenticated call succeeds
# --------------------------------------------------------------------------
def gate_llm(env: dict[str, str], offline: bool) -> None:
    key = env.get("LLM_API_KEY", "").strip()
    base = (env.get("LLM_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
    model = env.get("LLM_MODEL") or "gpt-4o-mini"
    if not key:
        record("V0.3", "LLM API key", FAIL, "LLM_API_KEY not set — the badge would read LLM-MOCK")
        record("V0.4", "LLM key actually works", FAIL, "skipped: no key")
        return
    record("V0.3", "LLM API key", PASS, f"present ({len(key)} chars), model={model}")

    if offline:
        record("V0.4", "LLM key actually works", MANUAL, "--offline: not called")
        return
    req = urllib.request.Request(f"{base}/models",
                                 headers={"Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = json.loads(r.read())
        names = [m.get("id") for m in body.get("data", [])][:3]
        ok = any(model in (n or "") for n in [m.get("id") for m in body.get("data", [])])
        record("V0.4", "LLM key actually works", PASS,
               f"authenticated; {len(body.get('data', []))} models; "
               f"configured model {'available' if ok else 'NOT in the list'}; e.g. {names}")
    except urllib.error.HTTPError as e:
        detail = {401: "401 — key rejected", 403: "403 — key lacks permission",
                  429: "429 — rate limited or no credit"}.get(e.code, f"HTTP {e.code}")
        record("V0.4", "LLM key actually works", FAIL, detail)
    except Exception as e:                                    # noqa: BLE001
        record("V0.4", "LLM key actually works", FAIL, f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------
# 4. Render: a paid Starter instance, if an API key is supplied
# --------------------------------------------------------------------------
def gate_render(env: dict[str, str]) -> None:
    key = env.get("RENDER_API_KEY", "").strip()
    if not key:
        record("V0.6", "Render paid Starter instance", MANUAL,
               "no RENDER_API_KEY — check the dashboard shows 'Starter', not 'Free'")
        return
    req = urllib.request.Request("https://api.render.com/v1/services?limit=20",
                                 headers={"Authorization": f"Bearer {key}",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            services = json.loads(r.read())
        plans = []
        for item in services:
            s = item.get("service", item)
            plans.append(f"{s.get('name')}:{s.get('serviceDetails', {}).get('plan') or s.get('plan')}")
        starter = [p for p in plans if "starter" in str(p).lower()]
        record("V0.6", "Render paid Starter instance",
               PASS if starter else FAIL,
               f"{'starter plan found' if starter else 'no starter plan'} — {plans or 'no services'}")
    except urllib.error.HTTPError as e:
        record("V0.6", "Render paid Starter instance", FAIL, f"HTTP {e.code} from Render API")
    except Exception as e:                                    # noqa: BLE001
        record("V0.6", "Render paid Starter instance", MANUAL, f"{type(e).__name__}: {e}")


# --------------------------------------------------------------------------
# 5. accounts that only a human can confirm
# --------------------------------------------------------------------------
def gate_manual(env: dict[str, str]) -> None:
    record("V0.7", "Sandbox business + personal (US) accounts exist", MANUAL,
           "developer.paypal.com → Sandbox → Accounts; both must show country US")
    record("V0.8", "App created today, not reused from an old demo", MANUAL,
           "record the creation date next to the client id in your notes")
    record("V0.9", "Provider spend cap set", MANUAL,
           f"set a hard monthly limit; in-app budget is "
           f"{env.get('LLM_DAILY_CALL_BUDGET', '1500')} calls/day as a backstop only")


def main(argv: list[str]) -> int:
    offline = "--offline" in argv
    env = load_env()
    print("\nV0 — preconditions. If any row FAILS, stop: everything downstream "
          "assumes these are real.\n")
    gate_env_contract(env)
    gate_paypal(env, offline)
    gate_llm(env, offline)
    gate_render(env)
    gate_manual(env)

    width = max(len(t) for _, t, _, _ in results)
    for gate, title, status, detail in results:
        mark = {PASS: "✓", FAIL: "✗", WARN: "!", MANUAL: "?"}[status]
        print(f"  {mark} {gate:5s} {title:<{width}}  {status}")
        if detail:
            for i, chunk in enumerate(str(detail).split("; ")):
                print(f"        {'  ' if i == 0 else '  '}{chunk}")

    fails = [r for r in results if r[2] == FAIL]
    manual = [r for r in results if r[2] == MANUAL]
    print()
    if fails:
        print(f"  {len(fails)} FAILED. Do not start P1 until these pass.\n")
        return 1
    if manual:
        print(f"  All automatable gates passed. {len(manual)} row(s) need your "
              f"confirmation by hand.\n")
        return 0
    print("  V0 complete. Proceed to P1.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
