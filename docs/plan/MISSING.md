# What is missing

*Every gap between what exists and what the submission claims. Written 5 Nov 2026.
Ordered by what would hurt most if it stayed missing.*

The distinction that matters: **code gaps** I can close, **account gaps** need a credential,
**evidence gaps** need the thing to have actually happened, and **people gaps** need someone
who is not us. Only the first column is mine.

---

## 1. Money has never moved

| Missing | Why it blocks | Close |
|---|---|---|
| Five live PayPal artifacts — OAuth, AUTHORIZE→capture, AUTHORIZE→void showing VOIDED, `INV2-…` invoice with `payment_term.due_date` from the engine's math, and a same-`PayPal-Request-Id` retry returning one order | V3's pass line is *"a judge could log into the dashboard and find them."* Today every one of those five is tested against a fake transport. The instrument exists and works; it has simply never been pointed at PayPal | `PAYPAL_CLIENT_ID` + `PAYPAL_CLIENT_SECRET`, then `python3 demo.py --live` |
| The real eligibility band from `findEligibleMethods` | V1 says confirm the band **from the response, never assume**. We currently assume | same creds; `product/probe/v1_probe.html` + `PAYLATER_SANDBOX_TEST.md` |
| Field-name and error-shape confirmation | Every PayPal field name in `paypal_live.py` is theory until the first 400 arrives. Expect two or three mismatches | the same run |
| A live webhook transmission | Verification is real crypto, proven over a socket with a 400 on a missing header — but no transmission from PayPal has ever been checked | `PAYPAL_WEBHOOK_ID` + the deployed URL |

**This is the single largest gap in the project.** Everything else is smaller than it looks
next to this.

---

## 2. The AI badge says MOCK

| Missing | Why it blocks | Close |
|---|---|---|
| A model behind the badge | The mandatory-AI rule is the one rule that cannot be waived. The badge is honest, which means it currently announces the gap | `LLM_API_KEY` (+ `LLM_MODEL`, `LLM_BASE_URL`), then `python3 demo_ai.py --live` |
| The quality half of V4 — three messy, realistic passages read correctly | The safety half is proven offline (nonsense degrades to `partial`, low confidence flagged, tampered approval refused). What is *not* proven is that a real model reads a real mess well | the same run |
| Cost behaviour under a real model | Token spend, latency and the fallback path are unmeasured | one live run, then read the evidence file |

---

## 3. Nothing is deployed

| Missing | Why it blocks | Close |
|---|---|---|
| A public URL | V5.6, all of V6, and V8 cannot start. V8 is the only gate that can tell us the pitch does not land *before* we record it | a Render account + the repo pushed |
| `/healthz` reading `SANDBOX · LIVE` + `AI · LLM` in production | Locally it correctly reads `SIMULATED` + `LLM-MOCK`. The switch has never been flipped anywhere else | with the URL |
| A real invoice created from the public URL and found in the dashboard | V6 item 3 | with the URL |
| The 30-minute cold-start test | Item 5. The instrument (`v6_cold_check.py --record/--compare`) exists and was smoke-tested; the sleep behaviour of a Starter plan is unobserved | with the URL, 40 minutes |
| Production isolation (V5.6) | Twenty-two checks pass against a local socket. Sessions are in memory, so a redeploy wipes them — that is a design choice, not a bug, but it is undemonstrated in production | with the URL |

---

## 4. The repo does not exist

Not a metaphor. `product/` is **not a git repository** — only the frozen prototype is.

| Missing | Why it matters | Close |
|---|---|---|
| `git init`, first commit, remote | There is no repo link to hand a V8 tester, no tag to submit, no push for Render to deploy from | 10 minutes |
| **`.gitignore`** | Without it the first commit takes `__pycache__/`, `artifacts/` and — if anyone slips — `.env`. A committed credential is unrecoverable | same commit |
| `LICENSE` | P7's own checklist says *"licence chip visible"* in an incognito window. There is no licence file to produce a chip | 2 minutes, MIT |
| A tagged submission commit | The rule is *no changes after the deadline*, `main` stable to 15 Dec | at submit |
| CI | Nothing runs the 152 tests on push. Optional, but it is what makes "green" mean something to a judge reading the repo | 20 minutes, GitHub Actions |

---

## 5. The README is missing two required lines

| Missing | Why it matters | Close |
|---|---|---|
| **The privacy line and the real data path** | It is a standing acceptance criterion, and `product/README.md` does not contain it. What we store: nothing personal beyond a session in memory; what we send: the free text to the model provider; what we keep: nothing after the session. Say it in the README, plainly | 15 minutes |
| **The rules checklist** | The contest rules mapped to where each is satisfied. It exists in the plan, not in the thing a judge reads | 20 minutes |
| Repo URL, deploy URL, and the video link | Currently the README describes how to run a local server | at deploy |

---

## 6. No evidence of people

| Missing | Why it matters | Close |
|---|---|---|
| V7: five BNPL conversations | Closed at **n = 0**. The instruments are built (`v7_capture.py`, `v7_verdict.py`, hash-chained log, rule engine). Nothing has been run | only you, time-boxed, or accept n = 0 |
| V8: one stranger, unaided, timed | The page, the protocol and the timer exist. No one has used it | only you, 9–10 Nov, 30 minutes |
| Resolution of the **3-of-5 contradiction** between `VALIDATION_CONVERSATIONS.md` and `P2_five_conversations.md` | One says "strongest available result", the other says "change the hook". If conversations run, this must be settled *before* the first one — the rule is no reinterpreting after | a decision, written down |

---

## 7. The submission package

| Missing | Why it matters | Close |
|---|---|---|
| **The video** — no script, no recording, no assets | Presentation is 20%, and the video is the only artefact every judge is guaranteed to see. A beat sheet exists; a shot list does not | after V8, so the stuck points write the script |
| **The Devpost form** — not opened | Two required fields (tagline *and* full description), and the live field list has not been re-read. Unknown U13 | open the draft today, against the rule that drafting before the deadline is allowed |
| Screenshots for the listing | Cold load, the three answers, the DECLINE case, a dashboard artifact | after deploy |
| Stage 2 readiness | Five equal criteria. Technological Implementation is the tiebreak, and it is the one we win on — worth knowing which artifact proves which criterion | 30 minutes of mapping |

---

## 8. Things that are accepted as true but not proven

- **A2**: research and decision documents stay out of the public submission repo. That is a
  choice, and it only holds while it is honoured.
- **"No adverse action"** is a two-mode framing, not a legal position. Production needs
  legal review and the pitch should say so in one clause.
- **The 549-repo count** stays out of the pitch or is hedged.
- **"Volume preserved"** is not claimed. The trade is named instead.
- **Session state is in memory.** A redeploy logs everyone out. Fine for a demo, and it
  should be said rather than discovered.

---

## The five that actually decide the outcome

1. **Live PayPal calls** — without them this is a well-argued prototype.
2. **A real model behind the badge** — the mandatory-AI rule has no fallback.
3. **A public URL** — three gates and the video all stand on it.
4. **The repo, with a licence and a `.gitignore`** — ten minutes, and it gates the deploy.
5. **One stranger using the page** — the only check that is not us grading our own homework.

Everything else on this page is smaller, and most of it I can do alone.
