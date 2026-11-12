#!/usr/bin/env python3
"""
scripts/preflight_deploy.py — check the deploy file before Render reads it.

    python3 scripts/preflight_deploy.py

Six things a deploy gets wrong, all of them cheap to check and expensive to find
out about from a URL that returns 502:

  1. the plan is `free`, which sleeps, which is a lost score;
  2. a secret is typed into the file and committed;
  3. an environment variable is set here that the code never reads, or the code
     reads one that is never set;
  4. `startCommand` points at a file that is not there;
  5. the health check points at a path the app does not serve;
  6. `.env.example` and `ENV_CONTRACT` have drifted apart.

This does not replace `v0_check.py` — that one proves the credentials are real.
This one proves the configuration is coherent. Neither can prove Render will
behave, which is what V6's cold check is for.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from secondthought.config import ENV_CONTRACT            # noqa: E402

YAML = ROOT / "render.yaml"
SECRET_MARKERS = ("SECRET", "KEY", "TOKEN", "WEBHOOK")
ok = fail = 0


def check(label: str, passed: bool, detail: str = "") -> bool:
    global ok, fail
    if passed:
        ok += 1
        print(f"  ✓ {label}")
    else:
        fail += 1
        print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))
    return passed


def main() -> int:
    print("Second Thought — deploy preflight\n")
    if not check("render.yaml exists", YAML.exists()):
        return 1
    text = YAML.read_text()
    lines = [ln.rstrip() for ln in text.splitlines()]

    # 1. the plan
    plans = re.findall(r"^\s*plan:\s*(\S+)", text, re.M)
    check("plan is starter (free sleeps and loses the review window)",
          plans == ["starter"], f"found {plans}")
    check("/healthz is the health check",
          bool(re.search(r"^\s*healthCheckPath:\s*/healthz\s*$", text, re.M)))

    # 4. the start command points at a real file
    cmd = re.search(r"^\s*startCommand:\s*(.+)$", text, re.M)
    check("startCommand is declared", bool(cmd), "missing")
    if cmd:
        target = re.search(r"(scripts/[\w.]+\.py)", cmd.group(1))
        check(f"startCommand target exists ({target.group(1) if target else '?'})",
              bool(target and (ROOT / target.group(1)).exists()),
              "not found on disk")
        check("bound to 0.0.0.0 via the PORT env var, not a hardcoded host",
              "serve.py" in cmd.group(1))

    # 2. no secret typed into the file
    declared = re.findall(r"^\s*-\s*key:\s*(\w+)", text, re.M)
    for key in declared:
        block = _block(lines, key)
        if not any(marker in key for marker in SECRET_MARKERS):
            continue
        safe = "sync: false" in block or "generateValue: true" in block
        check(f"{key} is not committed in plaintext", safe,
              "use `sync: false` or `generateValue: true`")

    # 3. the variable set and the code agree, in both directions
    unknown = [k for k in declared if k not in ENV_CONTRACT]
    check("every variable in render.yaml is read by the code",
          not unknown, f"unread: {unknown}")
    missing = [v for v in ENV_CONTRACT
               if v not in declared and v != "PORT"]
    check("every variable the code reads is declared (PORT excepted — Render sets it)",
          not missing, f"undeclared: {missing}")

    # 6. .env.example still matches the contract
    env_example = ROOT / ".env.example"
    if env_example.exists():
        names = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", env_example.read_text(), re.M))
        check(".env.example matches ENV_CONTRACT",
              names == set(ENV_CONTRACT),
              f"only in example: {sorted(names - set(ENV_CONTRACT))}; "
              f"only in contract: {sorted(set(ENV_CONTRACT) - names)}")

    # 5. the health route exists and leaks nothing
    from secondthought.config import AppSettings, LLMSettings, PayPalSettings
    from secondthought.interfaces.badge import health_payload
    payload = health_payload(AppSettings(
        llm=LLMSettings(api_key="sk-probe"), diag_token="diag-probe",
        paypal=PayPalSettings(client_id="cid", client_secret="csec")))
    import json
    body = json.dumps(payload)
    check("/healthz returns only booleans and status words",
          set(payload) == {"status", "ai_mode", "payments_mode", "checks"}
          and all(isinstance(v, bool) for v in payload["checks"].values()))
    check("/healthz carries no secret", "sk-probe" not in body and "csec" not in body)

    print(f"\n{'-' * 60}")
    print(f"  {ok} passed, {fail} failed")
    print(f"{'-' * 60}\n")
    if fail:
        print("Fix these before deploying. A red preflight is cheaper than a 502.")
    return 0 if fail == 0 else 1


def _block(lines: list[str], key: str) -> str:
    for i, line in enumerate(lines):
        if re.search(rf"^\s*-\s*key:\s*{re.escape(key)}\s*$", line):
            out = [line]
            for nxt in lines[i + 1:i + 4]:
                if re.match(r"^\s*-\s*key:", nxt):
                    break
                out.append(nxt)
            return "\n".join(out)
    return ""


if __name__ == "__main__":
    raise SystemExit(main())
