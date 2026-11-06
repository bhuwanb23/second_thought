# 09 — Build plan

> ## ⚠ Timeline revised after review — see `SUBMISSION_KIT.md` §5
> The authoritative schedule is now in `../SUBMISSION_KIT.md`. Three things changed:
> **no framework rewrite** (the Python prototype is the build, not a draft), **feature freeze
> on 9 Nov**, and the first three days are sandbox credentials → live AI → deploy, in that
> order. The day-by-day guidance below still applies to *how* to work, not *what* the order is.

---

Eleven days: **1 Nov → 12 Nov 2026, 12:00 PT (13 Nov 01:30 IST).** Plan backwards from a recorded video, not forwards from a repo.

Reference concept below is **C02 — Second Thought**, which is now decided, specified
(`../../research/07_concepts/C02_PRD.md`), validated (`../../research/07_concepts/C02_VALIDATION_REPORT.md`) and built
(`../../../09_build/prototype/.env.example`, 91 tests passing). The build days below are therefore mostly done;
what remains is credentials, deployment and the video.

---

## Backwards from the deadline

| When | What must be true |
|---|---|
| **11 Nov** | Submitted. One day of slack. |
| **10 Nov** | Video exported, uploaded, public, link works. AG Grid licence still live at time of recording. |
| **9 Nov** | A stranger can run it from the README. Deployed, health check green. |
| **7 Nov** | Core mechanic works against sandbox, ugly UI acceptable. |
| **4 Nov** | OAuth + first order + first AUTHORIZE executed on sandbox. |
| **2 Nov** | Concept chosen, one-pager written. |

If 7 Nov arrives without the core mechanic, **cut the concept down to its mechanic and demo only that.** A three-screen product that works beats an eight-screen product that half-works, on both *Design* and *Presentation*.

---

## Day-by-day

**Day 1 (1 Nov) — decide.** Read the three one-pagers. Pick one. Write its sentence. Do not start coding.

**Day 2 (2 Nov) — scaffold.** Repo, licence, `.env.example`, `.gitignore`, CI running a trivial test. Sandbox app created, credentials issued, OAuth working with a token in hand. Get the boring things out of the way while they are still cheap.

**Day 3 (3 Nov) — the primitive.** The single most important PayPal call, proven. C02: an AUTHORIZE on sandbox, visible in the dashboard, with the auth ID stored. C01: a live Orders v2 round-trip against a test repo. Nothing else this day.

**Day 4 (4 Nov) — deterministic core.** The rules engine / arithmetic. Integer cents. Unit tests. **This is the part that must be right**, because everything else is presentation. Gate G1 passes here.

**Day 5 (5 Nov) — the agent.** Model integration, constrained output schema, validation, deterministic fallback. Prove the failure path: what happens when the model returns garbage.

**Day 6 (6 Nov) — the data surface.** The screen a judge will remember. For C02: the exposure calendar and the projected balance curve, in AG Grid Studio. Take the sponsor prize here while the feature is still being built, rather than bolting it on later.

**Day 7 (7 Nov) — end to end.** The whole flow in one run. Gate G2. Record a rough screen capture even if it is ugly — you will want it if things break later.

**Day 8 (8 Nov) — harden.** Webhook signature verification, idempotency, error states and empty states, seeded demo data. Deploy. This is the day that moves *Technological Implementation* from 3 to 4.

**Day 9 (9 Nov) — the stranger test.** Gate G3. Someone else runs it. Fix the README, not their understanding. Set up the scheduled health check.

**Day 10 (10 Nov) — video.** Gate G4. Storyboard from the demo script in the one-pager. Record in one sitting if possible; the pacing is better. Re-record only the segments that are wrong.

**Day 11 (11 Nov) — submit.** Gate G5. Walk `../../research/01_contest/SUBMISSION_REQUIREMENTS.md` line by line. Secret scan on full history. Submit, then close the laptop.

**12 Nov — buffer.** For the thing that went wrong.

---

## What to build on

| Layer | Choice | Why |
|---|---|---|
| Framework | Next.js + TypeScript | Both official PayPal starter repos are this. `paypaldev/hackathon-paypal-ag-grid-boilerplate` |
| PayPal SDK | `@paypal/paypal-server-sdk` (Node) or `paypal-server-sdk` (Python) | **Not** `paypalrestsdk` — deprecated since Nov 2023, still 990k installs/month |
| Client | `@paypal/paypal-js` v6 | 1% of the field uses v6; PayPal's own resources page links it |
| Agent | Any framework; the choice is not scored, the boundary is | Constrain output with a schema, validate, fall back deterministically |
| Grid | AG Grid Studio | Sponsor prize; 5 slots, $10,000 |
| API tooling | APIMatic Context Plugin | Free, PayPal spec pre-enabled, ~1 hour, 3 slots |
| Hosting | Render | Credits, prize eligibility, and the "available until 15 Dec" requirement |

## Non-negotiables in the architecture

- **Credentials never in the repo.** `.env` gitignored, `.env.example` committed, scanned on full history.
- **Every POST carries `PayPal-Request-Id`.** One line, and it is a credibility signal.
- **Webhook signatures verified** via `/v1/notifications/verify-webhook-signature`, not hand-rolled.
- **The model cannot move money.** Propose → validate → approve → execute.
- **One failure path is demoable on demand.** Forced deliberately, not hoped for.
- **Tests exist and are pasted into the README.**

## What to cut if behind

In this order: multi-currency → settings/auth → onboarding flows → the second agent capability → polish on secondary screens.

**Never cut:** the core mechanic, the failure path, the data surface, the video. Those four are where the score lives.
