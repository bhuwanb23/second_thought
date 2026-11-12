#!/usr/bin/env python3
"""Run everything that can be run here and write artifacts/proof.json.

`/proof` reads this file. The rule is the same one the rest of the project runs
on: a number that was not produced by a command is not written down.

  python3 scripts/make_proof.py            # measure, write, print a summary
  python3 scripts/make_proof.py --quiet    # write only
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "proof.json"

TESTS = "unittest discover -s tests -q"
CHECKS = [
    ("Unit tests", [sys.executable, "-m", *TESTS.split()],
     r"Ran (\d+) tests in ([\d.]+)s", "python3 -m unittest discover -s tests -q"),
    ("Security checks", ["bash", "scripts/v5_two_jars.sh"],
     r"(\d+) passed, (\d+) failed", "bash scripts/v5_two_jars.sh"),
    ("Deploy preconditions", [sys.executable, "scripts/preflight_deploy.py"],
     r"(\d+) passed, (\d+) failed", "python3 scripts/preflight_deploy.py"),
]


def run(cmd: list[str]) -> tuple[int, str]:
    done = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
    return done.returncode, (done.stdout or "") + (done.stderr or "")


def one(label: str, cmd: list[str], pattern: str, how: str) -> dict:
    code, out = run(cmd)
    hit = re.search(pattern, out)
    if not hit:
        return {"label": label, "value": "did not run", "command": how, "ok": False}
    nums = [int(g) if g.isdigit() else float(g) for g in hit.groups()]
    if "failed" in pattern:
        passed, failed = nums[0], nums[1]
        ok = code == 0 and failed == 0
        value = f"{passed} passed, {failed} failed"
    else:
        count, seconds = nums[0], nums[1]
        ok = code == 0
        value = f"{count} tests OK in {seconds:.2f} s"
    return {"label": label, "value": value, "command": how, "ok": ok}


def dependencies() -> dict:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    declared = re.search(r"dependencies\s*=\s*\[(.*?)\]", text, re.S)
    deps = [d for d in re.findall(r'"([^"]+)"', declared.group(1))] if declared else []
    return {"label": "Third-party dependencies", "value": f"{len(deps)}", "ok": not deps,
            "command": "python3 -c \"import tomllib;print(tomllib.load(open('pyproject.toml','rb')))\""}


def git() -> str:
    code, out = run(["git", "rev-parse", "--short", "HEAD"])
    return out.strip() if code == 0 and out.strip() else "no git checkout"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    checks = [one(*c) for c in CHECKS] + [dependencies()]
    failed = [c["label"] for c in checks if not c["ok"]]
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "git": git(),
        "checks": checks,
        "summary": "all measured checks passed" if not failed
                   else "failing: " + ", ".join(failed),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if not args.quiet:
        print(f"\n  wrote {OUT.relative_to(ROOT)}")
        for c in checks:
            print(f"  {'ok ' if c['ok'] else 'FAIL'} {c['label']:<24} {c['value']}")
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
