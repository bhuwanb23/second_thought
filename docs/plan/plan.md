# Master plan — Second Thought (C02)

**Project:** payday-aware checkout that sometimes says "not yet"
**Status:** 🔒 concept locked 1 Nov 2026 · 155 tests passing · build complete, *verification and submission remain*
**Hard deadline:** Thu 12 Nov 2026, 12:00 PT = **13 Nov 01:30 IST**
**Internal deadline:** **11 Nov** — one day of slack, non-negotiable
**Builder:** solo · **budget:** ~25 hours across 10 days (~2.5 h/day)

This file is the index. Each phase has its own document with the full end-to-end detail.

---

## 1. What is fixed — do not re-open

| Fixed | Detail |
|---|---|
| The idea | Payday-aware checkout; three verdicts OFFER / DEFER / DECLINE |
| The DEFER rule | **Pay before ship.** Merchant never extends credit |
| The customer answer | *PayPal pays for it, the shopper benefits, the merchant embeds it* |
| The split | Model reads and proposes; **engine decides every money call**; human approves |
| The safe amount | A decline always quotes a number that would fit |
| The claims | No credit-bureau asymmetry, no "volume preserved", no "validated" |
| The mode badge | Never faked. `LLM-MOCK` and `SIMULATED` are named strengths |
| **Personas read-only; per-visitor state disposable** | Every visitor gets a cookie-scoped session. Nothing a visitor saves can change what the next visitor sees — §6a |

Rationale and history: [LOCK.md](LOCK.md) · [DECISION_LOG.md](DECISION_LOG.md) · [../research/07_concepts/C02_THE_IDEA.md](../research/07_concepts/C02_THE_IDEA.md)

---

## 2. Assumption register — decided by default, changeable on request

The five questions I asked went unanswered, so I made these calls rather than stall the plan. **Any of these can be reversed in one message and I will re-issue the affected phase.**

| # | Assumption | Why I chose it | Reversal cost |
|---|---|---|---|
| **A1** | All research and concept docs now live under `../research/`; decisions, submission kit and phases under `` | Matches the structure requested. 117 references rewritten and verified — 103 resolve, 0 broken | Nil; moving back is the same script in reverse |
| **A2** | The active code stays at `../../product/`, inside one root repository | The product build is the current source of truth; the earlier implementation is archived separately | Closed by repository consolidation |
| **A3** | Credential status is **unknown**, so P3/P4/P5 each open with a 30-second possession check and carry the acquisition steps inline | Cheapest assumption to be wrong about; costs one check, not a rewrite | Nil |
| **A4** | Conversations may not happen, so P2 defines pre-agreed wording for n = 5, n = 3 and n = 0 | The claim is the thing that must not be improvised on 10 Nov | Nil |
| **A5** | Video is **self-recorded**; generated narration exists as a fallback | Own voice is stronger on Presentation; the fallback protects a bad recording day | Nil |

---

## 2b. Immediate actions — this week, before the phases

Two things remain that V0 does not cover:

| Do | Why | Time |
|---|---|---|
| **Open a Devpost draft now** | Drafts are allowed before the deadline. The draft shows the **real required fields**, which beats planning from a remembered checklist (closes **U13**) | 15 min |
| **Confirm your PayPal developer account works from India** | Sign-up and sandbox behaviour varies by country. Ask on the PayPal Developer Discord rather than debugging it on 3 Nov | 15 min |

Credentials, hosting and the env contract are no longer a checklist — they are **V0**, a script that
either passes or stops the build.

---

## 3. Phase map

| Phase | Name | Window | Hours | Exit condition (checkable) | Serves |
|---|---|---|---|---|---|
| **[V2](V2_code_correctness.md)** | **Code correctness — automated** | 2 Nov | **0.5** | ✅ **Green.** 155 tests, both suites; 2 test defects found and fixed |
| **[V3](V3_live_paypal.md)** | **Live PayPal, local** | 2 Nov | **2.0** | 🔴 **Blocked at V0.1.** Instrument built; 21 tests; `--dry-run` 5/5. Needs the key |
| **[V4](V4_live_ai.md)** | **Live AI** | 2 Nov | **2.0** | 🔴 **Blocked at V0.3.** AI layer built; safety half proven by 49 tests; quality half needs the key |
| **[V5](V5_session_security.md)** | **Session isolation & security** | 2 Nov | **2.5** | 🟢 **5 of 6 PASS** over a real socket — 22/22 checks. Item 6 proven locally, pending the Render redeploy |
| **[V6](V6_deployment.md)** | **Deployment & durability** | 4 Nov | **2.0** | 🔴 **No public URL — nothing deployed.** Webhook verification built (P5.6, 24 tests), deploy config green (18 checks), cold-check instrument works, calendar filed |
| **[V7](V7_human_validation.md)** | **Human validation** | 4 Nov | **1.5** | 🔴 **Not run — n = 0.** Cannot be delegated. Capture + verdict scripts built and tested; the pre-commitment is now mechanical |
| **[V0](V0_preconditions.md)** | **Preconditions — do once** | 2 Nov | **0.75** | **`python3 scripts/v0_check.py` exits 0**, and the four manual rows are confirmed | Tech Impl + Stage 1 |
| **[P0](P0_lock_and_foundation.md)** | Lock & foundation | 1 Nov | ✅ 0 | Concept frozen; canonical product build and root repository established | all |
| **[P1](P1_paylater_probe.md)** | Tripwire 1 — Pay Later probe | 2 Nov | 0.5 | A sandbox verdict recorded in the results table; OFFER wording chosen | Tech Impl |
| **[P2](P2_five_conversations.md)** | Tripwire 2 — five conversations | 2–4 Nov | 1.5 | Table has rows; decision rules applied **as written**; claim wording updated | Impact |
| **[P3](P3_live_paypal.md)** | Live PayPal credentials | 2–3 Nov | 1.5 | `demo.py --live` creates a real `INV2-…` invoice on sandbox | Tech Impl |
| **[P4](P4_live_ai.md)** | Live AI | 3 Nov | 1.0 | Badge reads `AI · LLM`; extraction runs against the provider | Tech Impl + Innovation |
| **[P5](P5_deploy.md)** | Deploy & durability | 4 Nov | 2.0 | **Hosted badge reads `SANDBOX · LIVE` + `AI · LLM`, and a real invoice is created from the public URL**; keep-alive verified; webhook verified live | Tech Impl + Presentation |
| **[P6](P6_polish_and_freeze.md)** | Polish & freeze | 5–9 Nov | 8.0 | AG Grid decided in writing; **feature freeze 9 Nov** | Design |
| **[P7](P7_record_and_submit.md)** | Record & submit | 10–11 Nov | 6.0 | Video ≤3:00 uploaded public; form submitted 11 Nov | Presentation |

**Total: 20.5 h planned + ~4 h buffer = ~25 h.**

## 4. Dependencies

```
V0 (preconditions) ──▶ P1, P3, P4, P5        ← hard gate, nothing runs before it
P0 ✅ ──┬─→ P1 (probe) ──────────────┐
        ├─→ P2 (conversations) ──────┤
        ├─→ P3 (PayPal live) ─→ P4 (AI live) ─→ P5 (deploy) ─→ P6 ─→ P7
        └────────────────────────────────────────────────────────────┘
```

**Critical path: V0 → P1 → P3 → P5 → P7.** Everything else is parallel or slack.

> **Ordering correction (review):** live **webhook** verification cannot happen in P3. It needs a
> public URL and a webhook ID registered against it, so it belongs **after P5**. P3 covers REST calls
> from a local machine; **P5.6** covers the webhook end to end.
**P1 runs first even though it is the smallest** — it is the only thing that changes what gets recorded, and it takes two minutes.

---

## 5. Unverified register — every unknown, its closer, and what happens if it comes back badly

This is the table that makes the plan safe. **Every response is pre-committed, so nothing gets argued about later.**

| # | Unknown | Closed by | If it comes back badly |
|---|---|---|---|
| U1 | Does Pay Later render in sandbox? | P1 | **Script B**; OFFER → `authorize_hold`; the invoice becomes the hero |
| U2 | Do shoppers recall a timing problem unprompted? | P2 | 0–1/5 → reframe to safe-amount-only, or fall back to C01 |
| U3 | Will they set up a payday profile? | P2 | ≥3/5 no → lead the demo with the *saved* profile, onboarding as roadmap, stated openly |
| U4 | Does the decline read as helpful or patronising? | P2 | ≥3/5 patronising → rewrite to "what fits"; mechanic unchanged |
| U5 | Does the user have a **working** PayPal sandbox app? | **V0.1–V0.2** | The gate makes the real OAuth call. `401` stops the build |
| U5b | Is the sandbox pair **US**, and is the app **fresh**? | **V0.7–V0.8** | Manual rows; if not US, Pay Later may be unobtainable — which P1 reports honestly |
| U6 | Does the user have a working LLM key **and a spend cap**? | **V0.3–V0.4, V0.9** | No key = **submission at risk**, not a fallback. No cap = set it before P4 |
| U7 | Does the chosen model tool-call reliably? | P4.2 | One validated call; if it fails twice, keep the mock and say so |
| U8 | Does Render's starter plan stay awake? | P5.3 | Keepalive workflow + external pinger; re-verify **1 Dec** |
| U9 | Does `render.yaml` deploy as-is? | P5.2 | Fallback: manual Docker deploy, documented in the README |
| U10 | AG Grid in or out? | P6.1 | **Out** unless it fits in ≤3 h and does not risk the freeze |
| U11 | Is APIMatic worth it? | P6.2 | Out. Not free, and unused sponsor tools earn nothing |
| U12 | Can the video be recorded cleanly? | P7.1 | Fallback narration + two takes; the recording day is not the only day |
| U13 | Does the submission form ask for anything unexpected? | P7.4 | Re-read the live listing on 11 Nov, not from memory |
| U14 | Are all judge-visible claims sourced? | P6.5 | Any claim without a source gets deleted, not softened |

---

## 6a. Session isolation — a defect found and fixed

A shared demo is hostile to judges. Originally a saved profile was **global**, so one visitor's save
changed the verdict the next visitor saw — making the three personas non-reproducible. Hosted
filesystems are ephemeral anyway: a redeploy or spin-down wipes them.

**Fixed in code, not prose:**

| Now | Effect |
|---|---|
| `session.py` — cookie-scoped `Session` per visitor | Judge A's profile, ledger and eligibility cannot leak to judge B |
| Personas are **read-only** | The three demo verdicts are reproducible for everyone, forever |
| Durable state is SQLite; sessions and approvals are **in-memory** | Reservations and webhook state survive a process restart when the configured database path is durable; session cookies are invalidated on restart |
| Bounded to 400 sessions, oldest evicted | Memory cannot grow without limit |
| **Two session/network limit gates**: 30/session and **90/IP**, plus the provider budget | A cookie-scoped limit alone is bypassable by clearing cookies, so the IP gate survives that; the provider-side budget is the real spend backstop |
| `test_one_visitor_cannot_change_anothers_verdict` | The defect cannot silently return |
| **`/healthz` returns booleans and status words only** | No paths, keys, versions, session counts, or internal details on a public unauthenticated URL |
| **`/diagnostics` is operator-only** | Returns 404 without a matching `DIAG_TOKEN`, so it does not advertise itself |
| `155 tests` | Canonical product suite, no network required |

Verified over HTTP with two cookie jars: judge B sees `DEFER` while judge A, who saved a profile,
sees `DECLINE`.

---

## 6. Contingency ladder — what gets cut, in this order

If the schedule slips, cut **downward**. Do not improvise.

| Cut | Loses | When to cut |
|---|---|---|
| 1. APIMatic | nothing scored | Immediately — already decided out |
| 2. AG Grid | a sponsor prize we would not win anyway | If P6 is behind on 6 Nov |
| 3. Conversation count | a stronger Impact claim | If fewer than 5 are reachable by 4 Nov — **report the n** |
| 4. UI polish items | some Design points | If P6 has under 4 h left on 8 Nov |
| 5. Nice extras (webhook demo, extra personas) | Tech Impl depth | Only after 4 |

**Never cut:** the live LLM key · the deploy · the video · the README checklist · the probe ·
the canonical test suite · the honest mode badge.

> **Correction (review):** this ladder said "never cut the live LLM key" while **U6** allowed shipping
> `LLM-MOCK`. Those contradicted each other. Stage 1 requires AI that is genuinely used, and a mock is
> not that. **The key is mandatory** — a few dollars of credit. If it cannot be obtained, that is not
> a fallback, it is **submission at risk**, escalated the same day rather than absorbed.

---

## 7. Definition of done — mapped to the rules

The submission is done when every row is true. Items marked ✅ are already satisfied.

| # | Requirement (from the rules) | State |
|---|---|---|
| 0 | **V0 preconditions green** — real PayPal sandbox app, live LLM key, `.env.example` contract, paid host | ⬜ [V0](V0_preconditions.md) |
| 1 | Project name | ✅ Second Thought |
| 2 | Short description ≤2 sentences | ✅ [SUBMISSION_KIT §2](SUBMISSION_KIT.md) |
| 2b | **Full text description** of features and functionality — the rules require it; the tagline is not enough | ⬜ P7.4 |
| 3 | Thumbnail image | ⬜ P7.3 — **confirm it is required** from the Devpost draft (2b) |
| 4 | Demo video, public, ≤3:00 | ⬜ P7 |
| 5 | **Public repo with license visible in the About section** (17% of scanned repos fail this) | ⬜ P5.4 |
| 6 | PayPal tools + AI tools written out explicitly | ✅ §1 |
| 7 | **Sandbox-only confirmation**, no live credentials | ✅ adapter refuses `PAYPAL_ENV=live` |
| 8 | New vs existing project stated | ⬜ P7.4 |
| 9 | Setup/run instructions that work on a clean clone | ✅ README, re-tested P6.3 |
| 10 | **Available until 15 Dec 08:00 PT** | ⬜ P5.3 + read-only re-verify 1 Dec |
| 11 | **Submitted commit tagged; `main` frozen until 15 Dec** — the rules bar changes after the deadline | ⬜ P7.6 |

Plus the internal bar: `python3 -m unittest discover -s tests -q` → **OK**,
`python3 scripts/preflight_deploy.py` → **ALL CHECKS PASSED**, no secrets in git.

---

## 8. Rules that shape every phase

| Constraint | Consequence for the work |
|---|---|
| Stage 1 is pass/fail on "PayPal reasonably applied" | PayPal must be central, not decorative. Every phase keeps PayPal on the critical path |
| **Tiebreak = Technological Implementation** | When choosing polish vs depth, **depth wins**. This is why the invoice flow stays live and the webhook path stays distinct |
| Presentation is 20%, and the video is the only guaranteed artefact | Never let the video become the last thing done badly. P7 is two days |
| Automated analysis is explicitly permitted | Literal names in the README: `Orders v2`, `AUTHORIZE`, `Invoicing`, `webhooks`, the model used |
| Judging runs to 15 Dec | The demo must survive December, not just 10 Nov |
| No trademarks/logos in the video | Generic personas, no PayPal logo, no implied endorsement |
| Everything in English | Including commit messages and the README |
| Original work only | The 549-repo scan was to avoid duplication, not to copy |

---

## 9. Daily ritual — 10 minutes, every day until submission

```bash
cd product
python3 -m unittest discover -s tests -q     # must say OK (155 tests)
python3 scripts/preflight_deploy.py          # must say ALL CHECKS PASSED
git -C .. status                              # nothing uncommitted, no .env
```

Then update the phase file's status line. **A day where these three fail is a day that does not get recorded.**

---

## 10. Phase documents

| | File | One line |
|---|---|---|
| V0 | [V0_preconditions.md](V0_preconditions.md) | **The gate: prove the credentials are real before anything else** |
| V2 | [V2_code_correctness.md](V2_code_correctness.md) | ✅ The suites, and whether the tests assert what they claim |
| V3 | [V3_live_paypal.md](V3_live_paypal.md) | 🔴 Five real sandbox calls, each verifiable in the dashboard — instrument ready, credentials absent |
| V4 | [V4_live_ai.md](V4_live_ai.md) | 🔴 Live AI: badge, messy input, confidence flags, tampered approval — model runner waiting on the key |
| V5 | [V5_session_security.md](V5_session_security.md) | 🟢 Isolation, rate limits, `/healthz`, and no unauthenticated money action — 22 live checks |
| V6 | [V6_deployment.md](V6_deployment.md) · [calendar](V6_repeat_calendar.ics) | 🔴 Deploy blocked; P5.6 webhook verification done; repeats filed for 1 and 10 Dec |
| V7 | [V7_human_validation.md](V7_human_validation.md) | 🔴 n = 0. Hash-chained capture + rule engine built; the conversations are yours to run |
| V8 | [V8_outside_eye.md](V8_outside_eye.md) | 🟡 There was no screen at all — now there is one, plus the protocol and the timer. Needs a stranger and the URL |
| P0 | [P0_lock_and_foundation.md](P0_lock_and_foundation.md) | What is already done, and the evidence |
| P1 | [P1_paylater_probe.md](P1_paylater_probe.md) | Two minutes that decide the OFFER wording |
| P2 | [P2_five_conversations.md](P2_five_conversations.md) | The only thing that can change the idea |
| P3 | [P3_live_paypal.md](P3_live_paypal.md) | Real sandbox money on screen |
| P4 | [P4_live_ai.md](P4_live_ai.md) | The badge must say `LLM`, not `LLM-MOCK` |
| P5 | [P5_deploy.md](P5_deploy.md) | A URL that still works in December |
| P6 | [P6_polish_and_freeze.md](P6_polish_and_freeze.md) | Decide AG Grid, stop adding, freeze |
| P7 | [P7_record_and_submit.md](P7_record_and_submit.md) | 2:40 of video and a submitted form |

How the code is organised — one job per file, every file under 300 lines, enforced by preflight:
**[REPO_STRUCTURE.md](REPO_STRUCTURE.md)**

Reference material: [LOCK.md](LOCK.md) · [DECISION_LOG.md](DECISION_LOG.md) · [GATES_AND_REDTEAM.md](GATES_AND_REDTEAM.md) · [SUBMISSION_KIT.md](SUBMISSION_KIT.md) · [../research/README.md](../research/README.md)
