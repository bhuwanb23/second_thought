# V7 — Human validation

**Status:** 🔴 **NOT RUN. This one cannot be delegated to me at all.**
**Pass:** five rows, filled in before you know whether you like the answer, and the pitch says the real n — "tested with five Pay Later users", never "validated".

---

## 1. Why there is nothing in the table

V7 is the one phase that validates the *idea*, and it needs five people who have actually used Pay Later, Afterpay or Klarna. I cannot recruit them, call them, or hear what they say. There is no honest way for me to produce a row in that table, and a fabricated one would be the single most damaging thing in this repository — far worse than an empty table, because the empty table is survivable and an invented quote is not.

So the table is empty, `n = 0`, and by the pre-committed rule that already exists in [P2 §P2.5](P2_five_conversations.md) that means: **delete every hint of user validation from the README and the video.** That is the current, correct state of the claim.

What I have done instead is make the phase mechanical, so that when you sit down with someone the rules cannot drift.

---

## 2. What is built

Two scripts, both stdlib, both tested against fixture data kept in `/tmp` — never in the repo.

### `product/scripts/v7_capture.py` — one conversation, immediately

```bash
python3 scripts/v7_capture.py
```

Eight fields, exactly the columns pre-committed in
[VALIDATION_CONVERSATIONS.md](../research/07_concepts/VALIDATION_CONVERSATIONS.md), plus the two gates that decide whether a row counts at all:

| Gate | Why |
|---|---|
| `eligible` — have they really used BNPL in the last year? | A conversation with someone who has not tests nothing |
| `described` — was the product described before the recall question? | Rule zero broken → the row is **discarded, not scored** |

It writes to `docs/plan/v7_conversations.jsonl`, one JSON object per line, **append-only and hash-chained**: each row carries the previous row's hash.

That chain is the answer to item 3 — "filled in during or immediately after, not retroactively." It cannot prove a conversation happened. It can show that the rows were not composed in one sitting afterwards, because the verdict script flags rows that arrive seconds apart.

### `product/scripts/v7_verdict.py` — the rules, applied by a machine

```bash
python3 scripts/v7_verdict.py --explain        # decide, and print the only permitted claim
python3 scripts/v7_verdict.py --write          # render the table into P2_five_conversations.md
```

It counts, matches a rule, and prints the one sentence the submission is allowed to use. There is no flag to soften a result.

Six scenarios, run against fixtures:

| Fixture | Output |
|---|---|
| No log at all | `n = 0` → "DELETE every hint of user validation" |
| 5 rows, 4 recalled unprompted | R1 fires → "tested with five shoppers, 4 recalled this unprompted" |
| 3 rows, 2 recalled | **R2 fires → "CHANGE THE HOOK to lead with the explanation gap"** |
| 3 of 5 won't set up a profile, 3 call it patronising | R4 + R5 fire → lead with the saved profile; rewrite the copy |
| One row pitched before asking | discarded → n = **4**, claim says "four shoppers" |
| A row edited after writing | **hash mismatch → exit 1, refuses to decide** |

That last one matters. If someone changes a `yes` to a `no` after the fact — in either direction — the script will not produce a verdict from that log.

---

## 3. Two things I got wrong, and what stops them now

**I contaminated the real document.** While testing `--write`, I pointed it at a fixture log and it rendered three rows reading `SYNTHETIC FIXTURE ROW 1 — not a real conversation` into `docs/plan/P2_five_conversations.md`. I caught it, removed the block, and verified the file is byte-identical to its 113-line original.

The fix is not "be more careful". `--write` now **refuses** to write if any record contains the word synthetic, unless `--force` is passed for a throwaway copy:

```
✗ REFUSING TO WRITE: the log contains rows marked synthetic.
  Fixture data must never reach the document that goes in the repo.
```

**There is a contradiction in the pre-committed rules.** [VALIDATION_CONVERSATIONS.md](../research/07_concepts/VALIDATION_CONVERSATIONS.md) says "If 3–5 of 5 recall it unprompted → strongest available result". [P2](P2_five_conversations.md) says "2–3 of 5 → change the hook". **At exactly 3 of 5 those two rows disagree**, and 3 is a very likely outcome.

I have not resolved it, because resolving it myself is precisely what pre-commitment is supposed to prevent. The script defaults to the **stricter** reading — 3 of 5 changes the hook — on the principle that the unflattering reading is the safe default. **If you want it the other way, say so before the first conversation, in writing.** After that, no.

---

## 4. The window has closed

The phase was time-boxed to 2–4 November, and today is 4 November. The pre-committed consequence is in P2 already:

> **Time-box:** if the table is still empty on the evening of 4 Nov, close the phase at n = 0 and move on. Do not spend 5 Nov on it.

Two options, and you own this decision:

| Option | Cost | Consequence |
|---|---|---|
| **Close at n = 0 tonight** (pre-committed) | Nothing | The claim becomes "researched, not tested". Five less-good sentences in the pitch. Zero risk |
| **Extend to 5–6 Nov** | ~1.5 h of your time, against build/rehearsal time | If it runs, the strongest claim available in this competition short of a survey |

A third option exists that changes nothing downstream: **run three instead of five.** P2's failure-mode table already authorises it — "Run three. Report n = 3. **Never** invent or pad" — and the verdict script handles it without modification.

Whatever you choose, the claim follows the count automatically. That is the whole point of the two scripts.

---

## 5. What I need from you

The log file, or the filled table. If you run even one conversation:

```bash
cd product
python3 scripts/v7_capture.py            # after each conversation, same evening
python3 scripts/v7_verdict.py --explain  # when done
python3 scripts/v7_verdict.py --write     # puts the table into P2
```

Then I update `C02_THE_IDEA.md`, `SUBMISSION_KIT.md` and the video script so all three carry the identical sentence. Until then all three stay silent on validation, which is what they say today.

**The word that must not appear anywhere: "validated."** Not with five people, not with ten.
