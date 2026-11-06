# 05 — Sandbox setup and the gotchas that cost people points

Everything here is a small thing that is individually forgivable and collectively the difference between a judge believing your demo and not.

---

## Sandbox credentials

1. [developer.paypal.com/dashboard](https://developer.paypal.com/dashboard) → **Apps & Credentials** → toggle to **Sandbox**.
2. Create an app. You get a **Client ID** and **Secret**.
3. The default sandbox account is usually a **US business** account. If your concept needs a consumer, Pay Later, Venmo, or a non-US merchant, go to **Testing Tools → Sandbox Accounts** and create the personas you need.
4. Base URL: `https://api-m.sandbox.paypal.com`. OAuth: `POST /v1/oauth2/token` with `grant_type=client_credentials`, Basic auth.

**Never commit credentials.** Put them in `.env`, add `.env` to `.gitignore`, ship a `.env.example`, and run a scanner over the full history before the final push — not just the working tree.

## The gotchas

### 1. Sandbox money is a real number, and it is a demo asset
US sandbox accounts start with a large simulated balance. **Log in during the demo and show the balance change.** Judges see dozens of fake checkouts; a visible sandbox transaction record is what makes it real.

### 2. AUTHORIZE expires in 3 days, not 29
An intent to capture is valid for **3 days** for most transaction types (up to 29 days only for certain eligible flows). If your concept holds funds for a month, you need re-authorisation logic — and *saying this out loud in the video* is a small credibility win.

### 3. Webhook signature verification has five headers
`PAYPAL-TRANSMISSION-ID`, `PAYPAL-TRANSMISSION-TIME`, `PAYPAL-TRANSMISSION-SIG`, `PAYPAL-CERT-URL`, `PAYPAL-AUTH-ALGO`. Verify with the `/v1/notifications/verify-webhook-signature` endpoint rather than rolling your own crypto. **26% of the field mentions webhooks; far fewer verify.** Do it and say so.

### 4. Webhooks need a public URL
Sandbox cannot reach your laptop. Use a tunnel or deploy. If you use a tunnel, **it will be dead on judging day** — deploy the demo or make the tunnel restart part of your run instructions.

### 5. Orders v2 has two separate steps and people conflate them
- `POST /v2/checkout/orders` with `intent: CAPTURE` or `AUTHORIZE`
- Then `POST /v2/checkout/orders/{id}/capture`, or `/authorize` then later `/authorize/{authId}/capture`

Passing `intent: AUTHORIZE` and then calling `/capture` fails. This is the most common silent bug in escrow-style projects.

### 6. Idempotency matters and is free credibility
Send `PayPal-Request-Id` on every POST. Demo a retry that does not double-charge. Only a minority of the field mentions idempotency; it is one line of code and one line of README.

### 7. Negative testing is where the depth shows
Sandbox has **negative testing** — trigger `INSTRUMENT_DECLINED`, `PAYER_ACTION_REQUIRED`, `ORDER_NOT_APPROVED`. Force one in the video. "Here is the failure path, and here is how we recover" is worth more than another happy-path screen.

### 8. Pay Later in sandbox is awkward
Pay Later/Pay in 4 availability in sandbox depends on buyer country and merchant setup and often is not offered at all. **Do not design a demo whose central moment requires a live Pay Later offer.** If your concept is BNPL, either mock the offer UI around real Orders v2 calls, or make the core mechanic something you *can* execute in sandbox (an AUTHORIZE hold, a capture schedule you control). Be upfront in the README about what is real and what is simulated **in the sandbox only** — this is normal and acceptable; claiming it is real is not.

### 9. Node 18+ and the v6 SDK
`@paypal/paypal-js` v6 has a different `createInstance` API. The old `paypal.Buttons({createOrder})` patterns in every blog post are v5. If you copy a tutorial, check the version. PayPal's own resources page links v6.

### 10. Braintree Drop-in is already deprecated
Deprecated **1 Oct 2026**, unsupported **1 Oct 2027**. If your concept involves Braintree, use the Android/iOS/JS SDKs, not Drop-in — and say in the README that you are aware of the deadline. That is a free signal that you read the docs.

### 11. Licence visibility
**17% of scanned repos have no licence detectable in the GitHub About panel.** A `LICENSE` file at the repo root, of a recognised type (MIT, Apache-2.0), committed to the default branch. Check the About panel actually shows it.

### 12. Availability through 15 Dec
The requirement is explicit. Cheapest reliable answer: deploy on Render (sponsor, credits available), plus a **scheduled health-check workflow** that fails loudly if the demo is down — the technique one of the top field entries uses. Restart free-tier services or keep a paid instance; a sleeping dyno that takes 50 seconds to wake during a judge's 3-minute window is a lost score.

---

## Pre-submission checklist

```
[ ] .env.example committed, .env gitignored, secret scan clean on full history
[ ] LICENSE file, and It shows in the repo About panel
[ ] README has literal API names: Orders v2, AUTHORIZE/CAPTURE, webhooks, Agent Toolkit
[ ] "PayPal APIs used" and "AI tools used" as their own sections
[ ] "New project" or "what changed after 1 Oct 2026" stated
[ ] Test suite output pasted in
[ ] Live demo reachable with no login, no keys, from a cold browser
[ ] Health-check workflow green
[ ] Availability statement through 15 Dec 2026
[ ] Video public, under 3:00, shows one failure path and one sandbox transaction
[ ] Sandbox-only confirmed in writing
[ ] Run instructions tested by someone who is not you
```
