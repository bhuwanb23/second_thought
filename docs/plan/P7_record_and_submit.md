# P7 — Record & submit

**Status:** ⬜ **not started**
**Owner:** you · **Window:** 10–11 Nov · **Hours:** 6.0
**Exit condition:** a public video ≤3:00 uploaded, and the Devpost form submitted on **11 Nov**

---

## Purpose

Presentation is 20% of the score, and the video is the **only artefact every judge is guaranteed to
consume**. It is also the thing most likely to slip, which is why it gets two full days and why the
build is frozen before it starts.

Deadline: **12 Nov 12:00 PT = 13 Nov 01:30 IST.** We submit on **11 Nov**, leaving a day of slack.

---

## P7.1 — Recording setup (60 min, evening of 9 or 10 Nov)

- [ ] Screen recorder at **1080p, 30 fps** (OBS, QuickTime, Loom)
- [ ] Microphone tested; record 15 s and play it back before the real take
- [ ] Browser at 100% zoom, one tab, no bookmarks bar, no notifications
- [ ] Notifications off (macOS Focus / Windows Do Not Disturb)
- [ ] Demo state reset: stop the local server and remove the development SQLite file
      configured by `ST_DB_PATH`, then restart the server
- [ ] **Warm the hosted demo** — hit the URL five minutes before recording so nothing cold-starts on camera

**Fallback if a bad recording day:** generated narration can be laid over the same capture. Ask me
and I will produce timed clips. Own voice is stronger; the fallback protects the deadline.

---

## P7.2 — Record (2 hours, two takes)

Follow the shot-by-shot script in [SUBMISSION_KIT.md](SUBMISSION_KIT.md) §3, with the **P1** script
variant (A or B) that the probe selected.

| Time | Content | Serves |
|---|---|---|
| 0:00–0:15 | Who it's for, and the pain in one sentence. A real shopper, a real number | Impact |
| 0:15–0:35 | The problem *shown*: the instalment that lands two days before payday | Impact |
| 0:35–2:20 | **Live product, end to end, unedited.** Maya declines with a safe amount → Dev defers → **real `INV2-` invoice** → the agent proposes → **human approves** → it executes | Tech Impl + Design |
| 2:20–2:45 | How it's built: PayPal APIs by name, the engine/model split, the approval gate | Tech Impl |
| 2:45–3:00 | Why PayPal specifically, one line | Innovation + Impact |

**Non-negotiables:**

- **Show money moving.** The sandbox invoice appearing in the merchant account beats any diagram.
- **Show one failure path** — the forged-token rejection, or a $9,999 payment refused by the gate.
  It proves the implementation is non-trivial.
- **≤3:00.** Aim for **2:40** so the last seconds are never cut.
- **No PayPal logo, no trademarks, generic personas.** Say "PayPal Pay Later" as a product name only.
- **Say `sandbox` out loud** at least once.
- If a shopper quote from P2 is used: first name or descriptor only, with permission.

---

## P7.3 — Thumbnail and upload (45 min)

- [ ] Thumbnail: the verdict screen, readable at 320 px wide. No trademark imagery
- [ ] Upload to **YouTube or Vimeo**, visibility **Public** (not unlisted)
- [ ] Title and description name the project and the APIs used — this is indexable text
- [ ] Play it back on a **different device** to confirm audio and framing
- [ ] Confirm the URL works in a private window

---

## P7.4 — The submission form (60 min, 11 Nov)

Re-read the **live Devpost listing** — do not work from memory (unknown **U13**).

**The draft was opened in week one** ([plan.md §2b](plan.md)) so the real required fields are known —
use the draft, not a remembered checklist, and note anything it asks for that is not listed below.

| Field | Source |
|---|---|
| Project name | Second Thought |
| Short description (tagline) | [SUBMISSION_KIT §2](SUBMISSION_KIT.md) |
| **Full text description — features and functionality** | **Required by the rules and distinct from the tagline.** Write 150–250 words covering the three verdicts, pay-before-ship, the safe amount, the AI's two jobs, the approval gate, and the sandbox-only fact. Name the PayPal APIs |
| Thumbnail | P7.3 |
| Video link | P7.3 |
| Repository URL | P5.4 — public, licence visible |
| **PayPal developer tools and AI tools used** | [SUBMISSION_KIT §1](SUBMISSION_KIT.md) — paste verbatim |
| Sandbox confirmation | Explicit: sandbox only, no real money |
| New vs existing | New, built after 1 Oct 2026 |
| Setup instructions | README, clean-clone verified in P5.5 |

---

## P7.5 — Final verification, in this order (30 min)

1. **Incognito window**, logged out: repo public · licence chip visible · video public
2. `curl https://<app>.onrender.com/healthz` → `ok:true, paypal:live, ai:llm`
3. Clean clone in `/tmp` → tests pass with no credentials
4. Every claim on the listing page has a source, or is gone
5. `python3 scripts/preflight_deploy.py` → **ALL CHECKS PASSED**
6. Video is ≤3:00 (check the actual runtime, not the plan)
7. Read the short description aloud — if it sounds like a pitch deck, rewrite it plainly

---

## P7.6 — Submit, 11 Nov

- [ ] Submit the form
- [ ] **Screenshot the confirmation page** with the timestamp
- [ ] Copy the confirmation email
- [ ] Record the submission URL in `DECISION_LOG.md`
- [ ] **Tag the submitted commit** (`git tag v1.0-submitted && git push --tags`)
- [ ] **Freeze `main` until 15 Dec** — the rules bar changes after the deadline. After submission, only
      a break-fix is permissible, and a break-fix means re-tagging and re-verifying the full suite
- [ ] Dec 1 check is **read-only**: `curl /healthz`, open the page, create nothing. Do not modify,
      redeploy or "improve" anything during judging

Then, and only then:

- [ ] Calendar reminder **1 Dec**: re-verify `/healthz` and the keep-alive
- [ ] Do not touch the repo after submission except for a break-fix, re-verified with the full suite

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| Recording is bad on 10 Nov | Re-record on 11 **morning**. Still submit on 11 Nov evening. Never submit late to get a better take |
| Video over 3:00 | Cut the architecture section first; keep the live product and the approval gate |
| Hosted demo down on recording day | Record locally with `python3 scripts/serve.py`, say "running locally, sandbox", and keep the hosted URL in the submission. Honest and survivable |
| Form asks for something unavailable | Submit what exists; do not invent. Missing a field is better than a false claim |
| It is 11 Nov 23:00 and the video is not uploaded | Upload the best take you have. A finished 2:30 beats a perfect 0:00 |
| Temptation to claim live when it is simulated | The badge is on screen. It will be caught |
| Nothing to do on 1 Dec and you feel like improving something | **Do not.** Judging is live. Read-only checks only — a change during judging invalidates the submitted state |

---

## Exit criteria

- [ ] Video public, ≤3:00, shows the live product and money moving
- [ ] Thumbnail set
- [ ] Form submitted **11 Nov**
- [ ] Confirmation screenshotted
- [ ] 1 Dec re-verification reminder set
- [ ] Post-submission rule understood: only break-fixes, each re-tested
