# P3 — Live PayPal credentials

**Status:** ⬜ **not started** — needs `PAYPAL_CLIENT_ID` + `PAYPAL_CLIENT_SECRET`
**Owner:** you · **Window:** 2–3 Nov · **Hours:** 1.5
**Exit condition:** `demo.py --live` creates a real `INV2-…` invoice on PayPal sandbox

---

## Purpose

Every PayPal call in the build is real REST code against a sandbox — but until a credential is set,
it runs through the simulated transport. This phase moves the **invoice** (the DEFER branch, the
hero of the story) and the **authorisation** (the OFFER fallback) onto real sandbox rails.

This is the phase that satisfies **Stage 1 pass/fail**: "does it reasonably apply the required
PayPal APIs". A simulated transport is honest, but a real sandbox invoice is *proof*.

Serves: **Technological Implementation** (the tiebreak criterion).

---

## P3.1 — Possession check (30 seconds)

```bash
cd product && ls -a | grep -q '^\.env$' && grep -c '^PAYPAL_CLIENT_ID=..' .env || echo "no .env yet"
```

**Yes** → skip to P3.2. **No** → do P1.1 (create the sandbox app) and copy both values.

---

## P3.2 — Set the credentials (5 min)

```bash
cd product
cp .env.example .env                       # .env is gitignored — verified by preflight
# edit .env and set:
#   PAYPAL_CLIENT_ID=sb...
#   PAYPAL_CLIENT_SECRET=...
```

Rules:

- **Never** commit `.env`. Preflight fails the build if it is not gitignored.
- **Never** use live credentials. The rules require sandbox, and the submission confirms sandbox-only.
- `PAYPAL_WEBHOOK_ID` stays **empty in this phase** — a webhook ID must be registered against a public
  URL, and there is no public URL until P5. Webhook verification is **P5.6**, not here.

---

## P3.3 — Prove the invoice is real (20 min)

```bash
cd product
python3 demo.py --live 2>&1 | tee /tmp/p3_live.log
```

Look for, in the DEFER section:

| Expected | Meaning |
|---|---|
| `PayPal mode: LIVE` | The real transport is in use, not the simulator |
| invoice id `INV2-XXXXXXXX` | A real sandbox invoice object |
| due date `2026-11-06` (Dev) | `payment_term.due_date` round-tripped correctly |

Then confirm it exists outside our own process:

1. Log in to `sandbox.paypal.com` with a sandbox **merchant** account.
2. **Pay & Get Paid → Invoicing.** The invoice should be listed.
3. Open it, screenshot it — this screenshot is usable in the video.

**Fail signature: any `401`.** That means a bad client/secret pair, or live credentials pointed at
sandbox.

---

## P3.4 — Prove the authorisation is real (20 min)

The OFFER branch, with eligibility *not* confirmed, resolves to `authorize_hold`:

```bash
curl -s -X POST localhost:8000/api/approve -H 'Content-Type: application/json' -d '{"persona":"sam"}'
# → {"ok":true,"token":"..."}
curl -s -X POST localhost:8000/api/execute -H 'Content-Type: application/json' \
     -d '{"persona":"sam","token":"<token>"}'
# → {"action":"authorized", "paypal":{"authorization_id":"AUTH-..."}}
```

| Expected | Meaning |
|---|---|
| `AUTH-…` id | A real AUTHORIZE object. Valid **3 days** — never promise longer |
| executed **without** a token → `approval_required` | The human-approval gate is live, not decorative |

Then prove the gate is bound to arguments, not just to intent:

```bash
# approve $249, then try to execute it against a different amount → must be refused
```

This is already covered by `tests/test_integration.py::test_forged_amount_token_is_rejected`. Quote
that test's name in the README.

---

> **Not in this phase:** live webhook verification. It needs a public HTTPS URL and a webhook ID bound
> to it, so it belongs after P5. Do not burn P3 time trying to receive a webhook on localhost.

## P3.5 — Record the evidence (10 min)

Add to `../../product/README.md`:

- the sandbox invoice id from your run, dated
- the `AUTH-…` id, dated
- "verified against PayPal sandbox on <date>" with the app name

A judge reading the README should be able to tell **which** calls were executed against PayPal's
real API and when. Do not claim live verification on a date you did not verify.

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| `401` on every call | Re-copy both values; check the app is a *Sandbox* app, not Live. Retry once |
| `403` / `PERMISSION_DENIED` | The app lacks the Invoicing scope → create a fresh app, do not fight the old one |
| Invoicing works, AUTHORIZE fails | Ship with invoice-only live paths; the simulated AUTHORIZE is labelled, so nothing is faked. Note it in the README |
| Sandbox is flaky | Retry twice, then run `demo.py` (simulated) for the recording and say on camera which is which. **Never** claim live |
| Runs out of time | P3 is not optional for the *invoice*. If only one thing goes live, it is the invoice |

---

## Exit criteria

- [ ] `.env` set, gitignored, never committed
- [ ] `demo.py --live` prints `PayPal mode: LIVE`
- [ ] A real `INV2-…` invoice exists in the sandbox merchant account (screenshot taken)
- [ ] A real `AUTH-…` authorisation returned
- [ ] Executing without a token returns `approval_required`
- [ ] Evidence dates added to the README
- [ ] Submission confirms **sandbox only, no real money**
