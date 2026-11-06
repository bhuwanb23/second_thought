# V6 — Deployment & durability

**Status:** 🔴 **CANNOT RUN. There is no public URL, because nothing is deployed.**
**Pass:** everything in V3 and V4 is reproducible through the public URL, cold, with no local dependency.

---

## 1. The honest position

V6 begins "from the public URL only, not localhost." I do not have a public URL, because I cannot deploy: that needs a Render account, PayPal sandbox credentials and an LLM key, and I have none of the three. V0 is still 4 FAILED.

So four of the six items cannot be attempted at all, one is half-built, and one is a calendar — which is the one item that genuinely did not need a deploy:

| # | Item | Status |
|---|---|---|
| 1 | Full walkthrough against the deployed URL | 🔴 **Cannot start.** No URL |
| 2 | `/healthz` reads `SANDBOX · LIVE` + `AI · LLM` | 🔴 **Cannot start.** Locally it correctly reads `SIMULATED` + `LLM-MOCK` |
| 3 | Real invoice from the public URL, verified in the dashboard | 🔴 **Cannot start** — though the *call* is built and proven on a fake transport (V3) |
| 4 | Webhook with a bad signature, rejection logged and visible | 🟠 **Machine built and tested; the deployed route is unproven** — §3 |
| 5 | 30+ minutes away, then a cold hit, Starter did not sleep | 🔴 **Cannot start** — but the instrument is built and works: §4 |
| 6 | Calendar the repeat for Dec 1 and ~Dec 10 | ✅ **Done** — `V6_repeat_calendar.ics`, two events, reminder an hour before |

Filling in a green row here without a deployment would be a fabrication in a document that is meant to be evidence. The rows stay red.

---

## 2. What V6 forced me to build anyway

Deployment is where a webhook arrives from a stranger, so P5.6 came forward. This is the part of V6 that was never really about the host.

### P5.6 — webhook signature verification

`infra/webhook.py` + `infra/rsa.py` + `infra/webhook_api.py`. **24 tests** (`tests/test_rsa.py`, `tests/test_webhook.py`).

Anyone can POST to a public URL. An unverified webhook is not a notification, it is an instruction from an anonymous party to ship goods. So:

| Attack | Result |
|---|---|
| Signature that does not verify | **400**, `signature does not verify`, logged |
| Signature valid for a *different* body | 400 |
| Replayed transmission (captured, resent forever) | 400, `replayed transmission` |
| Missing header | 400, names which header |
| Cert URL on `evil.example` | 400 — **refused before any fetch** |
| Cert URL over plain `http` | 400 |
| Cert fetch times out | 400, fail closed — never "skip verification" |
| `PAYPAL_WEBHOOK_ID` unset | 400, everything refused |
| Correctly signed event | 200, applied, remembered |

Three details that are usually the holes, all of them deliberate here:

- **The raw bytes are signed, not the parsed JSON.** Re-serialising before verifying changes the message. `canonical()` takes `raw_body: bytes`, and `plumbing.raw_body()` reads the socket once. A test asserts `{"a":1}` and `{"a": 1}` produce different signed strings.
- **The cert URL is attacker-controlled input.** HTTPS-only, host allowlist, and — the bug my own test caught — the check lives in `_key()` rather than only in the default fetcher, so an injected lookup cannot skip it.
- **RSA in the stdlib.** No dependency, so `pow()`, PKCS#1 v1.5 padding and a minimal DER walk. The tests sign with a real private exponent and verify with the public one — real cryptography, a deliberately small 512-bit key.

The subtlest bug in that file: a certificate contains **two** RSA algorithm identifiers, and the first one (`signature`) is not the key. `_from_certificate()` walks `[0] version, serial, signature, issuer, validity, subject, SPKI` and skips it. The test builds a certificate whose signature algorithm uses *SHA256-with-RSA* and whose key uses *rsaEncryption*, so a naive "first OID wins" parser fails.

### Visibility of a rejection

`/diagnostics` with no token configured → **404** (an endpoint that does not exist beats one that says "you need a token"). With a token configured: counts are **public**, the last five events need `X-Diag-Token`.

That split is a judgement call. V6.4 asks for the rejection to be *visible*; a counter a visitor cannot see is not visible. Transmission ids and event types stay behind the token. If that trade is wrong, it is one line to close.

### Already true, from V5

`/healthz` returns four keys, all booleans, proven against a fully-populated configuration. The badge is computed from config and nothing else — so when the deployed service *does* have the keys, the labels change themselves and there is no flag to forget to flip.

---

## 3. The deploy configuration

Root `render.yaml` (with `rootDir: product`), checked by
`product/scripts/preflight_deploy.py` — **18 checks, all green.**

```
✓ plan is starter (free sleeps and loses the review window)
✓ /healthz is the health check
✓ startCommand target exists (scripts/serve.py)
✓ PAYPAL_CLIENT_SECRET is not committed in plaintext
✓ LLM_API_KEY is not committed in plaintext          (and 4 more)
✓ every variable in render.yaml is read by the code
✓ every variable the code reads is declared (PORT excepted — Render sets it)
✓ .env.example matches ENV_CONTRACT
✓ /healthz returns only booleans and status words
```

**The preflight was mutation-tested** — set `plan: free`, inline a fake client secret, add an env var the code never reads:

```
✗ plan is starter                                    [found ['free']]
✗ PAYPAL_CLIENT_SECRET is not committed in plaintext  [use sync: false]
✗ every variable in render.yaml is read by the code  [unread: ['LLM_TEMPERATURE']]
14 passed, 3 failed
```

The root Blueprint and canonical `rootDir` check are included in the current 18/18 result.

`starter`, not `free`, for the reason already recorded: free instances sleep after 15 minutes idle, and a judge arriving cold would wait through a spin-up inside a three-minute review window. `numInstances: 1` because sessions are in memory on purpose.

---

## 4. Item 5 — the cold check instrument

`scripts/v6_cold_check.py`, two-phase because a script that sleeps for thirty minutes is a script nobody runs:

```bash
python3 scripts/v6_cold_check.py --url https://<app>.onrender.com --record
# … walk away for 30+ minutes …
python3 scripts/v6_cold_check.py --url https://<app>.onrender.com --compare
```

It measures first-byte latency on the first request (a spin-up is seconds, a warm instance is tens of milliseconds), then compares the **boot id** from `/api/session` — a changed boot means the process restarted and any session a judge was holding is gone. That is not automatically bad; it just must be *seen*.

Smoke-tested against a local server, including the negative case:

```
✓ /healthz answers                                     HTTP 200
✓ first request was not a spin-up                       14 ms
✓ it stays fast                                         median 0 ms over 5
  boot    6f4c6b2057a0
  ✗ the gap was actually 30 minutes or more             [0 min]
  ✓ the same process answered                           6f4c6b2057a0 → 6f4c6b2057a0
```

The gap check fails on purpose in that run, which is the point: the instrument is willing to say no.

---

## 5. Item 6 — the calendar

`docs/plan/V6_repeat_calendar.ics` — import it into any calendar application.

| Event | When (IST) | UTC |
|---|---|---|
| V6 repeat — public URL durability check | **Tue 1 Dec 2026, 10:00–11:30** | 04:30–06:00Z |
| V6 repeat 2 — durability + final freeze check | **Thu 10 Dec 2026, 10:00–11:30** | 04:30–06:00Z |

Each carries a 60-minute reminder and a nine-step checklist in the event body: cold load timed, `--record`/`--compare`, three personas, `/healthz` badges, two-browser isolation, invoice found in the dashboard, bad webhook refused and counted, boot id compared against last time.

Validated: CRLF line endings, no physical line over 75 octets, no UTF-8 split across a fold, balanced `VEVENT`/`ENDVEVENT`.

**Why these two dates:** the graded requirement is durability through 15 Dec 08:00 PT, not a single check on submission day. 1 Dec is two weeks after the 12 Nov deadline — long enough for a free-tier service to have slept, a generated secret to have rotated, or a key to have expired unnoticed. 10 Dec is the last check with time left to fix anything.

---

## 6. The results table — to be filled after the deploy

Nothing here is filled in. This is the sheet to complete, not a record of work done.

| # | Check | Command | Result |
|---|---|---|---|
| 1 | Cold load, fresh profile | browser, stopwatch | ⬜ |
| 2 | Three personas render (Ada OFFER, Ben DEFER, Cleo DECLINE) | browser | ⬜ |
| 3 | Profile save in one browser, personas unchanged in another | two browsers | ⬜ |
| 4 | `/healthz` reads `SANDBOX · LIVE` + `AI · LLM` | `curl …/healthz` | ⬜ |
| 5 | One real invoice from the URL, found in the dashboard | `curl …/api/plan` + dashboard | ⬜ |
| 6 | Bad-signature webhook → 400, counted at `/diagnostics` | `curl -X POST …/api/webhook` | ⬜ |
| 7 | 30-minute gap, no sleep | `v6_cold_check.py --record` / `--compare` | ⬜ |
| 8 | Boot id unchanged since the last check | same script | ⬜ |

---

## 7. What has to happen, in order

```
V0.1 PayPal keys ─┐
V0.3 LLM key ─────┼→ V0 green → P5 deploy → V6 items 1–5 → V6 repeat on 1 Dec and 10 Dec
Render account ───┘
```

Fifteen minutes of someone else's time:

```bash
cd product
python3 scripts/preflight_deploy.py          # 17 green, then:
# push to a repo, connect it in Render, paste the four values,
# set RENDER_API_KEY on the service, deploy.
export PAYPAL_CLIENT_ID=… PAYPAL_CLIENT_SECRET=… LLM_API_KEY=…
python3 scripts/v0_check.py                  # credentials are real (proves the keys, not the host)
curl -s https://<app>.onrender.com/healthz   # the host agrees: sandbox + llm, both true
python3 scripts/v6_cold_check.py --url https://<app>.onrender.com --record
```

Then 31 minutes later, `--compare`. That is the whole gate, once the keys exist.
