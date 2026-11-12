#!/usr/bin/env python3
"""
scripts/v6_cold_check.py — is the deployed URL awake, and is it the same process?

    # right before walking away
    python3 scripts/v6_cold_check.py --url https://second-thought.onrender.com --record
    # 30+ minutes later
    python3 scripts/v6_cold_check.py --url https://second-thought.onrender.com --compare

A cold Render instance answers slowly once and then is fast. A Starter instance
should not have been asleep at all. Two numbers tell them apart:

  * **first-byte latency of the first request** — a spin-up is seconds; a warm
    instance is tens of milliseconds. A 30-minute gap that still answers in <1s
    means it never slept.
  * **the boot id** — `/api/session` reports the boot this process started with.
    If it changed, the service restarted, and any session a judge was holding is
    gone. That is not automatically bad, but it must be *seen*, not discovered.

`--record` writes state to `.v6_cold_state.json`; `--compare` reads it. Splitting
it in two is deliberate: the point is a real gap, and a script that sleeps for
thirty minutes is a script nobody runs.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

STATE = Path(".v6_cold_state.json")
FAST_MS = 1000          # a warm instance answers well under this
ok = fail = 0


def check(label: str, passed: bool, detail: str = "") -> None:
    global ok, fail
    if passed:
        ok += 1
        print(f"  ✓ {label}" + (f"  {detail}" if detail else ""))
    else:
        fail += 1
        print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def probe(url: str, path: str, tries: int = 1) -> tuple:
    """(status, body, ms) for `tries` attempts; ms is the first one."""
    times, body, status = [], b"", 0
    for _ in range(tries):
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(url.rstrip("/") + path, timeout=60) as r:
                status = r.status
                body = r.read()
        except urllib.error.HTTPError as exc:
            status, body = exc.code, exc.read()
        except urllib.error.URLError as exc:
            print(f"  ✗ cannot reach {url}{path}: {exc.reason}")
            raise SystemExit(2)
        times.append((time.perf_counter() - started) * 1000)
    return status, body, times


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="the public https URL")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--state", default=str(STATE))
    args = ap.parse_args()
    if not (args.record or args.compare):
        print("Choose --record (before the gap) or --compare (after it).", file=sys.stderr)
        return 2

    print(f"Second Thought — V6 cold check against {args.url}\n")

    # One cold-ish request, then a few warm ones.
    status, body, first = probe(args.url, "/healthz")
    _, _, warm = probe(args.url, "/healthz", tries=5)
    health = json.loads(body)
    check("/healthz answers", status == 200, f"HTTP {status}")
    check("first request was not a spin-up", first[0] < FAST_MS,
          f"{first[0]:.0f} ms (a cold boot is seconds)")
    check("it stays fast", statistics.mean(warm) < FAST_MS,
          f"median {statistics.median(warm):.0f} ms over 5")

    _, session_body, _ = probe(args.url, "/api/session")
    session = json.loads(session_body)
    boot = session.get("boot", "?")
    badges = [b["label"] for b in session.get("badges", [])]
    checks = health.get("checks", {})

    print(f"\n  boot        {boot}")
    print(f"  badges      {', '.join(badges) or '(none)'}")
    print(f"  ai_mode     {health.get('ai_mode')}")
    print(f"  paypal      {health.get('payments_mode')}")
    print()
    check("healthz exposes booleans only",
          not any(isinstance(v, str) and len(v) > 12 for v in checks.values()))

    if args.record:
        Path(args.state).write_text(json.dumps(
            {"url": args.url, "boot": boot, "at": time.time(),
             "first_ms": first[0], "badges": badges, "checks": checks}, indent=2))
        print(f"\n  recorded to {args.state}. Walk away for 30+ minutes, then --compare.")
        return 0

    previous = Path(args.state)
    if not previous.exists():
        print(f"\n  ✗ no state at {previous}; run --record first")
        return 2
    before = json.loads(previous.read_text())
    gap = (time.time() - before["at"]) / 60
    print(f"  gap         {gap:.0f} minutes since the recording")
    check("the gap was actually 30 minutes or more", gap >= 30, f"{gap:.0f} min")
    check("the same process answered (it did not sleep or restart)",
          boot == before["boot"], f"{before['boot']} → {boot}")
    check("still fast after the gap — no spin-up",
          first[0] < FAST_MS, f"{first[0]:.0f} ms")
    check("the badges did not change while we were away",
          badges == before["badges"], f"{before['badges']} → {badges}")

    print(f"\n{'-' * 60}\n  {ok} passed, {fail} failed\n{'-' * 60}\n")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
