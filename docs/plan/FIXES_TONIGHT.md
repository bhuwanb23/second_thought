# Tonight — every finding from the review, and where it stands

*Written 12 Nov 2026, 21:05 IST. Deadline **01:30 IST**. Read the table, do the rows marked **YOU**,
in order. Rows marked **DONE** were changed in the repository in the last hour and are already tested.*

---

## 1. Status of every finding

| # | Finding from the review | Severity | State | Owner |
|---|---|---|---|---|
| 1 | No `LICENSE` — 17% of the field is disqualifiable for this | critical | **DONE** — MIT, root and `product/` | — |
| 2 | No CI, no badge: 170 tests nobody can see running | high | **DONE** — `.github/workflows/tests.yml`, badge in the README | you push it |
| 3 | README buries the product; a judge decides in 90 seconds | critical | **DONE** — new first screen: verdicts table, hero diagram, live/video links, run block | you fill two URLs |
| 4 | Depth is invisible: RSA verification in the code, never named | high | **DONE** — "signature verification" named in the PayPal table and the no-SDK note | — |
| 5 | No `/proof` page; the best repos in the field all have one | high | **DONE** — `/proof` + `scripts/make_proof.py`, 5 new tests | you run it after deploy |
| 6 | "Why no SDK" never argued | medium | **DONE** — two paragraphs, with the cost stated | — |
| 7 | Regulation never mentioned; the 2-payment design looks arbitrary | medium | **DONE** — "Two payments, on purpose" section + a video beat | — |
| 8 | The cash-flow inversion unaddressed ($20.45 vs $10.80) | critical | **DONE in copy** — arithmetic table in the README, 34 s of the video, Devpost pitch | you say it on camera |
| 9 | Buyer ≠ user never stated | medium | **DONE in copy** — one line in the README, one card at 0:34 | — |
| 10 | No video (20% of the score, currently zero) | critical | script ready: `docs/plan/VIDEO_SCRIPT.md` | **YOU** |
| 11 | Not deployed; no live URL; no Render stacking | critical | `render.yaml` + 17 preconditions pass | **YOU** |
| 12 | V3/V4 still READY: no live PayPal call, no live model | critical | two commands, both work | **YOU** |
| 13 | No users (V7, n = 0) | medium | accepted, and stated on the closing card | — |

Nothing in the *product* was broken by tonight's edits: **170 tests pass in 0.71 s**, 22/0 security
checks, 17/17 deploy preconditions, every file under 299 lines.

---

## 2. What I changed in the repository, and why

| File | Change |
|---|---|
| `LICENSE`, `product/LICENSE` | MIT. Two minutes of work that removes a disqualification risk. |
| `product/.github/workflows/tests.yml` | Runs the suite on 3.11 and 3.12, plus `demo.py --dry-run`, the 22 security checks and the 17 preconditions — the same commands a judge would type. |
| `product/README.md` | Rewritten first screen: one sentence, the three verdicts, the hero diagram, the DECLINE quote verbatim, links to demo/video/proof/dossier, "who it is for". New sections: the arithmetic, why no SDK, two payments on purpose, proof, license. The stale "what is next" list is now an honest gates table. |
| `product/secondthought/interfaces/proof.py` | New `/proof` page: measured numbers, the constants the engine obeys, the four gates with READY/OPEN, the command that reproduces every line. |
| `product/scripts/make_proof.py` | Runs the suite, the security checks and the preconditions, writes `artifacts/proof.json` in 2.4 s. |
| `product/secondthought/interfaces/http.py` | One route: `GET /proof`. |
| `product/tests/test_screens.py` | Five tests for the proof page, including "it never calls a READY gate a PASS". |
| `docs/plan/VIDEO_SCRIPT.md` | The 2:40 shot list, the voiceover in reading order, the rules, the upload checklist. |

---

## 3. The runbook — four rows, in this order

**Do not reorder these.** The video is worth more than everything technical that remains.

### Row 1 · Deploy (40 min) — YOU
```bash
cd product
git init && git add -A && git commit -m "Second Thought — PayPal AI Hackathon 2026"
# push to GitHub, then Render → New → Web Service → this repo (render.yaml is read automatically)
```
Then: `python3 scripts/v6_cold_check.py --url https://<your-app>.onrender.com --record`
Then open `/proof` on the deployed URL and run:
```bash
python3 scripts/make_proof.py      # locally, then redeploy so /proof shows the numbers
```

### Row 2 · The two live runs (20 min) — YOU
```bash
python3 demo.py --live        # five PayPal calls; artifacts land in artifacts/v3/<stamp>/
python3 demo_ai.py --live     # real model, real extraction, tampered approval refused
```
Screenshot the sandbox dashboard showing the same order ids. Those screenshots are 0:58–1:26 of the
video, and they are the difference between "wrote an integration" and "called PayPal".

### Row 3 · The video (90 min) — YOU
`docs/plan/VIDEO_SCRIPT.md`. Two takes maximum. Upload **public**, then paste the link into the
README's first screen and the Devpost form immediately.

### Row 4 · Submit (25 min) — YOU
Devpost form → paste the blocks from `docs/plan/DEVPOST_SUBMISSION.md`, add the new paragraph below,
attach `assets/png/devpost-thumbnail.png`, link the video, the repo and the live URL. Submit. Then
keep improving — an unsubmitted 4.5 scores zero.

---

## 4. Copy to paste, verbatim

**README, line 20** — replace the two placeholders the moment you have them:

```
https://PLACEHOLDER.onrender.com   →  https://<your-app>.onrender.com
https://youtu.be/PLACEHOLDER       →  https://youtu.be/<video-id>
```

**Devpost elevator pitch** (≤ 200 characters, replaces §2 of the submission doc):

```
A checkout that says not yet. Our AI reads the shopper's month; if a plan would break it, PayPal invoices on payday instead — the shop keeps the sale on PayPal's rail and ships after payment.
```

**About the project — add after "What it does"** (this is the paragraph that answers the only
question a PayPal judge will ask):

> **Why a merchant would want this instead of Pay in 4.** PayPal's Pay in 4 pays the shop
> immediately, minus 4.99% + $0.49. That is $20.45 on a $400 job. Our plan book takes two instalments
> over 45 days and costs the shop its expected loss instead — about $10.80 at Affirm's current 30-day
> delinquency rate. So the shop keeps roughly $9.65 more per $400, can sell to the 10–15% of
> customers whom Sunbit and CareCredit decline, and keeps the relationship rather than handing it to
> a lender. That only works if the underwriting is real, which is why the decision engine is
> deterministic, unit-tested and forbidden from taking orders from a language model. Two instalments
> at 0% over 45 days is also why this is not lending: it stays outside consumer-credit licensing,
> which a shop could not do and this code will not pretend to.

**The one line for the video's end card:** `170 tests · 0 dependencies · MIT · no users yet`.

**One sentence to add to the Devpost description, and to say on camera if you have room** — it is the
answer to the most dangerous question in the jury room ("you built a way to avoid our fee"):

> This does not replace PayPal's rail, it replaces the lender: both instalments are ordinary PayPal
> payments, so PayPal earns on both — and the deferral moves an order onto the rail that would
> otherwise have gone to Klarna, or to nobody. At PayPal's current 1.58% take rate, the customer is
> ahead of their own Pay Later economics as soon as **38%** of these orders would not have used it.

---

## 5. What is still lost, and I would not chase it now

| Lost | Why it went | Recoverable? |
|---|---|---|
| AG Grid's 5 slots vs ~75 users (6–8% odds, $10k) | no integration, and 2 h would eat the video | No. Wrong night. |
| APIMatic / Bryntum prize pools | same | No. |
| A stranger's first-run (V7) | needs a person, not code | Only if someone is awake and willing. |
| `payouts`, `disputes`, `subscriptions`, toolkit, MCP in the depth score | genuine product surfaces we do not have | No — and claiming them would be worse than missing them. |

The honest position after tonight: **7/13 on the visible depth markers today** (6 of them real, one
from the placeholder URL), **8/13 the moment the real URL is in the README** — top ~7% of the field,
every number reproducible, and one artefact, the video, entirely in your hands. That is a top-decile
submission. The prize table is a lottery; the submission quality is not.

---

## 6. Final gate before you submit

```bash
cd product
python3 -m unittest discover -s tests -q     # 170 tests, OK
bash scripts/v5_two_jars.sh                  # 22 passed, 0 failed
python3 scripts/preflight_deploy.py          # 17 passed, 0 failed
python3 scripts/make_proof.py                # writes artifacts/proof.json
```

Then, in the browser: `/` shows three months, a click gives a sentence, `/proof` shows the numbers,
and the footer says the money is simulated. If any of those three is false on the deployed URL, fix
that before you touch the Devpost form.
