# The video — 2:40, shot by shot

*The only artefact every judge is guaranteed to watch, and the one thing worth 20% of the score.
Record this before anything else tonight. If the recording goes badly, the fallback is a screen
recording with the same voiceover — not a slide deck.*

---

## Rules that are not negotiable

- **Under 3:00.** Stop at 2:45. Judges are not required to watch past 3:00 and will not.
- **Public on YouTube or Vimeo.** Not unlisted. Not a Drive link.
- **No music that needs a licence.** No music at all is better: the voice is the point.
- **No PayPal logo, wordmark or trade dress in any frame.** The word "PayPal" in body copy and in
  the sandbox dashboard is fine — that is the product, not a logo treatment.
- **Every number in the video exists in the repository.** $20.45, $10.80, 47%, 170 tests, $140.
  A judge who checks one of them must find it.
- **The DECLINE is in the first 15 seconds.** A video that opens on the offer is a video about a
  different, much more common product.

## Before you press record

| | |
|---|---|
| Machine | 1920×1080, browser at 110%, bookmarks bar hidden, notifications off, one tab |
| Windows | Terminal at 15 pt on a dark profile; browser on the page; PayPal sandbox dashboard in a third window |
| Data | `python3 scripts/serve.py` running; `demo.py --live` and `demo_ai.py --live` **already run once** so the artifacts and dashboard rows exist |
| Capture | OBS or QuickTime, 30 fps, mic close, room quiet, no keyboard clatter (use the mouse) |
| Method | one take per beat, cut on the beat, never narrate an error you then have to fix |

## The beats

| Time | On screen | On-screen text | Voiceover |
|---|---|---|---|
| 0:00 | The page, Cleo selected, DECLINE visible. Nothing is clicked for two seconds. | — | "This is a checkout saying no. It said no because of what is already in her month, not because of the amount." |
| 0:10 | Same screen, the sentence highlighted | `$249 → up to $140 would work today` | "Same shop, same price, same shopper. Smaller basket, and the answer changes to yes." |
| 0:20 | The arithmetic card (make it in the editor, 4 s) | `PayPal Pay in 4: $20.45 fee, paid day 0` / `Own plan book: $10.80 expected loss, paid day 45` / `the shop keeps $9.65 more` | "PayPal pays the shop today and charges 4.99%. Our plan book pays them in six weeks and costs about half that in expected loss. The shop keeps the difference — and keeps the sale." |
| 0:34 | Who pays / who uses card | `the shop buys it · the shopper meets it` | "The merchant pays for this. The shopper never sees a dashboard." |
| 0:40 | Ben selected → DEFER screen | `Pay on Sat 15 Nov — ships after payment` | "Ben's car payment lands before payday. So instead of a plan, he gets a date: nothing is charged now, the price is held, and it ships when the money arrives." |
| 0:58 | Terminal: `python3 demo.py --live`, the five calls scrolling | `OAuth · Orders v2 AUTHORIZE · capture · void · Invoicing v2` | "Five real calls against the PayPal sandbox — an authorisation hold, a capture, a void, and an invoice dated by the same payday arithmetic." |
| 1:14 | PayPal sandbox dashboard: the order and the invoice | `the same ids, in PayPal` | "These are the same orders in the PayPal dashboard. Not a mock — the sandbox, with the request ids we sent." |
| 1:26 | Terminal: `demo_ai.py --live`, free text typed | `"salary 2,400 on the 15th, rent 1,375 on the 1st, car loan 312 every second friday"` | "A shopper's month, typed the way people actually type it. A model reads it into dated amounts." |
| 1:42 | The extracted fields appear, with one flagged | `reads · flags what it is unsure about` | "It is allowed to be unsure. It is not allowed to decide — there is no code path from a model output to a verdict." |
| 1:56 | The tampered approval → `403` | `signature, amount, session — any change is refused` | "An approval is signed over one action and one amount. Change a digit and the call is refused before PayPal is ever reached." |
| 2:10 | The boundary diagram (2 s) | `the model supplies facts · the engine supplies the verdict` | "That sentence is the product. A language model that can say no to money is a liability; a rule engine that can is a merchant." |
| 2:18 | Two payments card | `2 instalments · 0% · 45 days — outside consumer-credit licensing` | "Two instalments, no interest, six weeks. That is why this is not lending, and why a shop can legally do it." |
| 2:30 | End card (`assets/png/devpost-thumbnail.png` or the logo on ink) | `Second Thought · 170 tests · 0 dependencies · MIT` / `one person, no users yet` | "Researched and built by one person. Not yet tested with users. The code is in the repo, the tests are in the repo, and the badge on screen tells you which mode it is in." |

**2:40 total.** If you overrun, cut the two-payments card to five seconds — do not cut the DECLINE
or the arithmetic.

## The voiceover, as one continuous read

Read it once out loud before recording. If a sentence is hard to say, it is hard to follow.

> This is a checkout saying no. It said no because of what is already in her month, not because of
> the amount. Same shop, same price, same shopper — smaller basket, and the answer changes to yes.
>
> PayPal pays the shop today and charges four point nine nine percent. Our plan book pays them in six
> weeks, and costs about half that in expected loss. The shop keeps the difference, and keeps the
> sale. The merchant pays for this; the shopper never sees a dashboard.
>
> Ben's car payment lands before payday, so instead of a plan he gets a date. Nothing is charged now,
> the price is held, and it ships when the money arrives.
>
> Five real calls against the PayPal sandbox: an authorisation hold, a capture, a void, and an invoice
> dated by the same payday arithmetic. These are the same orders in the PayPal dashboard — sandbox,
> not a mock, with the request ids we sent.
>
> A shopper's month, typed the way people actually type it. A model reads it into dated amounts, and
> is allowed to be unsure. It is not allowed to decide: there is no code path from a model output to
> a verdict. An approval is signed over one action and one amount — change a digit and the call is
> refused before PayPal is ever reached.
>
> That sentence is the product. A language model that can say no to money is a liability; a rule
> engine that can is a merchant. Two instalments, no interest, six weeks — which is why this is not
> lending, and why a shop can legally do it.
>
> Researched and built by one person. Not yet tested with users. The code is in the repo, the tests
> are in the repo, and the badge on screen tells you which mode it is in.

## After the take

1. Watch once with **sound off**: does the story read from the screens alone?
2. Watch once **looking away**: does the voiceover stand alone?
3. Check the runtime. If it is over 3:00, cut the middle, never the first 15 seconds.
4. Upload **public**, title `Second Thought — a checkout that sometimes says not yet`, description
   with the repo, the live URL and the dossier, thumbnail `assets/png/devpost-thumbnail.png`.
5. Paste the URL into the README's first screen and the Devpost form **in the same minute** — a video
   nobody can find scores nothing.

## If something breaks on camera

Do not debug on camera. Stop, fix, retake that beat. If `--live` fails because of credentials, say so
in one line — *"the sandbox run is in this recording from earlier"* — and use the earlier take. An
honest cut beats a fictional one, and a judge can tell.
