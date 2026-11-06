#!/usr/bin/env python3
"""
scripts/v7_capture.py — record one conversation, immediately, without editing prose.

V7 item 3 asks for the decision table to be filled in *during or immediately after*
each conversation, not retroactively. The only way to have evidence of that is to
write a row at the time, so this appends to an append-only, hash-chained log:

    python3 scripts/v7_capture.py                      # one conversation, prompted

Each record carries the previous record's hash. Back-filling is therefore visible:
if two rows arrive seconds apart, `v7_verdict.py` says so. It cannot prove a
conversation happened — nothing can — but it can show that the rows were not
composed later in one sitting.

Fields are exactly the eight columns pre-committed in VALIDATION_CONVERSATIONS.md,
plus the two gates that decide whether a row counts at all:

  * `eligible`      — have they actually used BNPL in the last year? A conversation
                      with someone who has not tests nothing.
  * `described`     — was the product described before the recall question? If yes,
                      rule zero was broken and the row is *discarded*, not scored.

No paraphrase. No composite characters. Verbatim only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

LOG = Path(__file__).resolve().parent.parent.parent / "docs" / "plan" / "v7_conversations.jsonl"

FIELDS = [
    ("who", "Who — shape, not name (e.g. '31, warehouse shift lead, used Klarna twice')"),
    ("recall", "Did they recall a timing problem UNPROMPTED? [yes/no]"),
    ("explained", "Were they refused without an explanation? [yes/no]"),
    ("profile", "Would they set up a payday profile? [yes/no]"),
    ("decline", "The decline felt: [helpful/patronising]"),
    ("ship", "Ship-after-pay acceptable? [yes/no]"),
    ("enable", "Would they enable it? [yes/no]"),
    ("verbatim", "The line that matters most, word for word"),
]


def _chain(records: list[dict]) -> str:
    return records[-1]["hash"] if records else "genesis"


def _hash(record: dict) -> str:
    body = json.dumps({k: v for k, v in record.items() if k != "hash"},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            raise SystemExit(f"{path}:{i} is not valid JSON — refusing to append to a "
                             f"log I cannot read") from None
    return out


def ask(label: str, options: list[str] | None = None, min_len: int = 0,
        default: str | None = None) -> str:
    while True:
        suffix = f" [{'/'.join(options)}]" if options else ""
        hint = f" (blank = {default})" if default else ""
        raw = input(f"  {label}{suffix}{hint}\n  > ").strip()
        if not raw and default is not None:
            return default
        if options:
            low = raw.lower()
            if low in options:
                return low
            print(f"    → one of: {', '.join(options)}")
            continue
        if len(raw) < min_len:
            print(f"    → at least {min_len} characters. Verbatim, not a summary.")
            continue
        return raw


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(LOG))
    ap.add_argument("--eligible", choices=["yes", "no"], default="yes",
                    help="have they really used BNPL in the last year?")
    ap.add_argument("--described-first", action="store_true",
                    help="did you describe the product before the recall question?")
    args = ap.parse_args(argv)

    path = Path(args.log)
    records = load(path)
    n = len(records)

    print(f"\nSecond Thought — V7 conversation {n + 1}")
    print("─" * 68)
    print("  Rule zero: no pitching. If you have already described the product,")
    print("  stop and mark this row discarded — a pitched conversation is not evidence.\n")

    entry: dict = {"seq": n + 1,
                   "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                   "eligible": args.eligible == "yes",
                   "described": bool(args.described_first)}
    for key, label in FIELDS:
        if key == "verbatim":
            entry[key] = ask(label, min_len=15)
        elif key == "who":
            entry[key] = ask(label, min_len=5)
        elif key in ("recall", "explained", "profile", "ship", "enable"):
            entry[key] = ask(label, ["yes", "no"])
        elif key == "decline":
            entry[key] = ask(label, ["helpful", "patronising"])

    entry["discarded"] = (not entry["eligible"]) or entry["described"]
    entry["prev"] = _chain(records)
    entry["hash"] = _hash(entry)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")

    print("\n" + "─" * 68)
    if entry["discarded"]:
        why = ("they have not used BNPL" if not entry["eligible"]
               else "the product was described before the recall question")
        print(f"  ✗ DISCARDED — {why}.")
        print("    The row is kept so the count is honest; it is not scored.")
    else:
        print(f"  ✓ recorded as conversation {entry['seq']}.")
        print(f"    chain {entry['prev'][:8]} → {entry['hash']}")
    print(f"\n  {len(records) + 1} of 5 in {path.name}.")
    print("  Do not edit this file by hand — the chain will not match.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
