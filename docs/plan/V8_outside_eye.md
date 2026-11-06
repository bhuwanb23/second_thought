# V8 — Outside-eye rehearsal

> **Pass line (yours, kept verbatim):** *they reach a DECLINE or DEFER and can explain
> in their own words why, within ~2 minutes, unaided.*

Status: 🟡 **started, cannot finish alone.** A rehearsal needs a person and a URL. I have
one of those, and it is not the URL.

---

## The finding, before anything else

**There was no screen.** As of this morning the HTTP layer served JSON only: `/api/quote`,
`/api/extract`, `/healthz`, `/webhook`. Hand a stranger a laptop pointed at that and they
see `{"verdict":"DEFER",...}` in a browser — or an empty page, depending on the path. V8
could not have measured anything, and running it would have produced the most dangerous
kind of result: a fail that looks like the idea failed when in fact the front door did not
exist.

That is V8 doing its job one step early. It found a hole no other gate was looking at,
because every other gate was testing things I built to be tested.

So the first half of V8 happened already: **a stranger-facing page now exists**, and it
was built to the pass line rather than to my taste.

---

## What now exists

| Piece | Path | What it does |
|---|---|---|
| The page | `product/secondthought/interfaces/screens.py` | One self-contained HTML page, inline CSS, no external assets, no fonts, no CDN. Served at `/`. |
| The words | same file, `explain(q)` | Turns a quote into a title, a reason, and a button a shopper would press. |
| The route | `product/secondthought/interfaces/http.py` | `GET /` serves the page; `/api/quote` now carries `explain` alongside the raw quote. |
| The audit | `product/tests/test_screens.py` | 18 tests. Fails the build if internal vocabulary reaches a shopper. |
| The protocol | `product/scripts/v8_observer.py` | `--precheck`, `--record`, `--report`. Times the session, refuses to count one you narrated, and writes the results here. |

The page itself, top to bottom:

1. **Second Thought** — "A checkout that sometimes says *not yet* — and tells you why."
2. Both honesty badges. `AI · LLM-MOCK` and `PAYMENTS · SIMULATED`, with a hover detail.
   They read as mock until a key is set, whatever the pitch says.
3. **Pick someone's month** — three named months, each with its amount, visible without
   clicking. Ada, Ben, Cleo.
4. An answer card that replaces the placeholder on click.
5. **Or describe your own month** — a textarea. What it read back is listed line by line,
   and anything it was unsure about is flagged *"not sure, please check"* rather than
   silently accepted.
6. A footer: money is simulated, nothing is charged, what you type stays in the session.

What it does **not** do: it does not decide anything from free text. The textarea pulls
out dates and amounts and shows its work; the verdict still comes from the three fixed
months and from the engine. That is the V4 invariant on screen, not just in the code.

---

## The copy, and why it reads that way

A shopper never meets our nouns. Compare:

| Internal | What the shopper is told |
|---|---|
| `verdict: OFFER` | **You can spread this over four payments** — "Your balance stays above your safety floor every week until the last payment, so all four can go ahead. The first is today." Button: *Pay in four*. |
| `verdict: DEFER`, `invoice_due: 2026-11-07` | **Pay on Sat 7 Nov — and it ships once you've paid** — "Taking $249.00 today would leave you short before your next payday. Nothing is charged now, the price is held, and it goes out the door after your payment clears." Button: *Hold it, pay Sat 7 Nov*. |
| `verdict: DECLINE`, `collision: "instalment 4 of 4"`, `safe_amount: 14000` | **This one doesn't fit right now** — "Paying $249.00 today leaves you short — because the 4th payment on a plan you already have lands around Sun 13 Dec. Up to $140.00 would work today." Button: *Pick something smaller*. |

Two things I changed once I read them out loud, which is the cheapest V8 that exists:

- **"instalment 4 of 4" survived into the shopper sentence.** It is precise and it is our
  word. `plain_collision()` now renders it *"the 4th payment on a plan you already have"*.
  The audit test fails the build if it comes back.
- **"before you're next paid"** — a typo I wrote and did not see until it was printed. Now
  "before your next payday".

The canonical `DEFER` / `OFFER` / `DECLINE` word still appears, in small type, under the
answer. The pitch and the video use those words and the mapping has to be visible. It is
never the sentence you are asked to understand — a stranger can reach a verdict from the
title alone.

---

## The protocol — this is the part that is yours

Thirty to forty minutes, one person, once. Do it 9 or 10 Nov as planned, after the URL is
live. Not before — a rehearsal against a localhost server is a rehearsal against a laptop.

**Before they sit down**

```bash
python3 scripts/v8_observer.py --precheck --url https://<your-app>.onrender.com
```

Six checks: the page loads, three months on the first screen, no external network
dependency, both badges, the "nothing is charged" line, and `/healthz` answering with
booleans only. If `ai_mode` comes back `llm-mock` and a key is supposed to be set, that is
a pause, not a detail — the badge will tell the tester the AI is a mock and they will ask
about it.

**What you hand them, and nothing else**

1. The public URL.
2. The repo link.
3. The README.

Not the pitch. Not the deck. Not "it's a checkout that…" — that sentence is the thing being
tested. If you say it, you have tested your own narration.

**What you do**

Watch. Say nothing. Do not point at the buttons, do not say "try the second one". If they
ask a question, answer "what do you think it does?" and stop.

**What you time**

Clock starts when the laptop touches their hands. Clock stops at the first moment they
can tell you, in their own words, which answer they got and why. Under 120 seconds is the
pass line you set.

**What you write down**

Every hesitation, every re-read, every wrong guess — verbatim, while it happens. Those
notes are the video script's weak points. A confusion you reconstruct afterwards is
worthless, the same way a V7 decision table filled in retroactively is worthless.

```bash
python3 scripts/v8_observer.py --record --url https://<your-app>.onrender.com
```

It asks for the descriptor, the seconds, the answer they reached, whether they explained
it, what help you gave, what they said in their words, and the stuck points. Then it
scores the session against your pass line and appends it to
`docs/plan/v8_rehearsals.jsonl`. **A session where you helped is recorded as a fail** —
`help != none` cannot pass, whatever the timer says.

```bash
python3 scripts/v8_observer.py --report
```

Reads the log, prints the table and the median, and rewrites the block at the bottom of
this file. Exit 1 if any session failed.

---

## The rubric — fill this in live

| Field | What counts | Where it goes |
|---|---|---|
| Seconds to explain | wall clock, start = laptop handed over | record it as it happens |
| Answer reached | OFFER / DEFER / DECLINE — must be DEFER or DECLINE to pass | the log |
| Explained why, unaided | their sentence, quoted, not paraphrased | the `said` field |
| Help given | none / pointed / explained — anything but none is a fail | the log |
| Stuck points | verbatim, one per line, at the moment they happen | the `confusions` field |

Suggested testers, in order of usefulness: someone who uses BNPL; someone who has never
heard of it; someone who will tell you the truth. The third matters most.

---

## What I can check, and what I cannot

I can check that the page does not speak in our language. `tests/test_screens.py` does,
and it caught two live problems in the first hour. That is a real check and it is the
cheapest part of V8.

It is **not** the gate. A sentence can contain no banned word and still confuse someone;
a page can be jargon-free and still make a person hunt for the answer. Comprehension
lives in a human head and there is no way around asking one.

**Current state: n = 0.** No stranger has seen this. If it stays at zero, the V8 line
below stays open and the video is made without the reassurance it was supposed to give —
and the honest sentence in the pitch remains *"we wrote it to be understood, and we have
not yet watched anyone try."* Not *"we tested it with users."* That word is spoken for.

---

## Blocked on, in order

1. **The deploy (P5).** No public URL exists. Steps 1, 2 and 4 of your spec cannot start.
2. **A person who has never seen it.** Not delegable, not simulable, and not something a
   script can stand in for.
3. **Thirty minutes of silence** while they use it. This is the hard one.

If the URL goes live on the 9th, one rehearsal on the 10th is enough to close V8 — one,
not five. It is a copy check, not a study.

---

## What would make me mark V8 as failed even if the report says pass

- The tester was told what it does before they opened it.
- The tester was walked to a verdict, or asked a leading question ("did you understand the
  part about payday?").
- The stuck points were written down afterwards from memory.
- The test ran against `localhost` or a screenshot instead of the public URL.
- Only one happy path was tried and nobody was shown the DECLINE case, which is the one
  the whole pitch rests on.
- A pass was recorded and no confusion note exists. There is always at least one.

<!-- V8 RESULTS START · generated by scripts/v8_observer.py -->

**0 rehearsals.** No stranger has seen this yet. `docs/plan/v8_rehearsals.jsonl` does not
exist, because nothing happened. When a session is recorded, `--report` replaces this
block with the table, the median, the stuck points and the quotes.

<!-- V8 RESULTS END -->
