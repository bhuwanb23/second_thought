# P0 — Lock & foundation

**Status:** ✅ **complete** (1 November 2026)
**Owner:** agent · **Window:** up to 1 Nov · **Hours:** 0 remaining
**Exit condition:** concept frozen · 155 tests passing · preflight passes · repo committed

---

## Purpose

P0 is finished. This document exists so that nothing in it gets re-litigated, and so a reader can
verify the foundation in sixty seconds without trusting a summary.

---

## 0.1 The idea is locked

| Fact | Where |
|---|---|
| Concept frozen, with a frozen/not-frozen table | [LOCK.md](LOCK.md) |
| The customer answer, DEFER rule, legal posture, claim corrections | [../research/07_concepts/C02_THE_IDEA.md](../research/07_concepts/C02_THE_IDEA.md) |
| Why each correction was made, dated | [DECISION_LOG.md](DECISION_LOG.md) §D6 |

**Only two things may change anything from here:** [P1](P1_paylater_probe.md) (OFFER wording) and
[P2](P2_five_conversations.md) (the idea, only under pre-written rules).

---

## 0.2 Verify the build in 60 seconds

```bash
cd product
python3 -m unittest discover -s tests -q     # expect: Ran 155 tests … OK
python3 scripts/preflight_deploy.py                     # expect: ALL CHECKS PASSED
python3 demo.py                               # expect: three personas, three verdicts
```

Then open a browser at the demo server (`python3 scripts/serve.py`).

| Check | Expected |
|---|---|
| Maya | **DECLINE** — instalment 3 collides with rent 2026-11-29, $36.75 short, safe amount **$200** |
| Dev | **DEFER** — invoice due **2026-11-06**, `fulfilment` = PAY BEFORE SHIP, `risk_bearer` = nobody |
| Sam | **OFFER** — lowest balance $1,801.00, floor $428.57 |
| Badge with no key | `AI · LLM-MOCK` — honest, by design |
| Answer quality with no profile | `demo` — *"not your real data"* |

---

## 0.3 What was built

| File | Job | Tests |
|---|---|---|
| `engine.py` | Deterministic decision engine, integer minor units | 32 |
| `personas.py` | Three shoppers, three month shapes | — |
| `agentic.py` | Extraction + tool loop + HMAC approval gate | ✓ |
| `llm.py` | Real tool-calling model; labelled scripted stand-in | ✓ |
| `paylater.py` | Resolves OFFER/DEFER/DECLINE → instrument, **with fulfilment rule** | ✓ |
| `profile.py` | Payday profile, set up once, `answer_quality` | ✓ |
| `paypal.py` | Sandbox REST or simulated transport, always labelled | ✓ |
| `ledger.py` | Every plan we originated | ✓ |
| `server.py` | `/decide /profile /extract /agent /approve /execute /paylater` | ✓ |
| `web/index.html` | Verdict, calendar, balance curve, approve step, disclaimer | manual |
| `paylater_probe.html` | The P1 tripwire tool | manual |

---

## 0.4 What was deliberately *not* built

Recorded so absence reads as a decision, not an oversight:

- **No framework.** Stdlib only, no dependencies, no build step. A judge can run `python3 scripts/serve.py`.
- **No Subscriptions or vaulting.** PayPal's docs say Pay Later messaging is unavailable alongside
  them; mixing them would produce a demo where one feature silently disables another.
- **No APIMatic.** Not free, and an unused sponsor tool earns nothing.
- **No AG Grid** — deferred to [P6.1](P6_polish_and_freeze.md), decision due 5 Nov.
- **No live money.** Sandbox only; the rules require it and the badge says so.

---

## 0.5 Foundation risks carried forward

| Risk | Carried into |
|---|---|
| Pay Later may not render in sandbox | **P1** |
| AI badge reads `LLM-MOCK` until a key is set | **P4** |
| Demo is only reachable on localhost | **P5** |
| AG Grid decision unmade | **P6** |
| Recorded video does not exist | **P7** |

---

## Exit criteria

- [x] Concept locked with a written frozen/not-frozen table
- [x] 155 tests, `OK`, no dependencies, no network needed
- [x] Preflight `ALL CHECKS PASSED` (license, `.env` hygiene, secrets, README claims, health check)
- [x] Offline demo rehearses the whole arc honestly
- [x] Git committed with no secrets
- [x] All five review rounds' corrections applied and dated
