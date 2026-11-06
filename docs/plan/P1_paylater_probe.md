# P1 / V1 — Tripwire 1: the Pay Later probe

**Status:** ⬜ **not started** — needs your sandbox client ID (V0.1)
**Instrument:** [`serve_probe.py`](../../product/scripts/serve_probe.py) · **Record:** [`PAYLATER_SANDBOX_TEST.md`](../../product/PAYLATER_SANDBOX_TEST.md)
**Owner:** you · **Window:** 2 Nov · **Hours:** **0.5–1.0** (not two minutes — see P1.0)
**Exit condition:** a sandbox verdict recorded in the results table, and one of two video scripts chosen

---

## Purpose

One question decides how the OFFER branch is worded on camera:

> **Does Pay Later actually render for us in PayPal's sandbox?**

It **cannot change the idea**. It changes two sentences in the video and which of two scripts is used.

Why it matters: eligibility is only knowable **client-side**, via the JS SDK. The server never
guesses it. So if Pay Later will not render, the honest product falls back to a real `AUTHORIZE`
hold — and the pitch says so rather than showing a mocked button.

**Run this before anything else.** It is the cheapest unknown in the project and it gates the script.

---

## P1.0 — Why this is a 30-minute task, not a 2-minute one

Pay Later eligibility is **not a single yes/no** — it depends on the **amount**, the **buyer's country**,
the **business type** and the **business's history**, and it is decided **client-side**. So the probe may
legitimately answer differently for $249 and for $2,000, and differently for a US buyer and an Indian one.

Budget 30 minutes, and use:

- **Currency USD**, buyer country **US** — the market the statistics and the sandbox behaviour describe
- An **in-range amount** (a $249 purchase is more likely in-band than $2,000)
- **US-country sandbox accounts** for both business and buyer

**If you are in India:** sign-up and sandbox behaviour varies by country. Confirm your developer account
and sandbox accounts actually work **before** the recording day — ask on the PayPal Developer Discord
rather than debugging it alone. This is listed in [plan.md §2b](plan.md) as a this-week action.

---

## P1.1 — Get a sandbox client ID (5 min, only if you do not have one)

1. Go to `developer.paypal.com` → **Log in to Dashboard** → **Apps & Credentials**.
2. Make sure the toggle is on **Sandbox** (top right). Not Live.
3. **Create App**, name it `second-thought`, type *Merchant*.
4. Copy the **Client ID** — it starts with `sb`. Also copy the **Secret** (P3 needs it).

> Use a **US** sandbox business and a **US** buyer persona. Pay Later eligibility is scoped to buyer
> country, business type and business history. A non-US pair fails for reasons unrelated to this
> project and would push you to the fallback script for no reason.

---

## P1.2 — Run the probe (2 min)

1. Download `../../09_build/prototype/paylater_probe.html`.
2. **Double-click it** — it must open in Chrome or Safari directly. It will **not** work inside the
   workspace preview pane, which blocks network access.
3. Paste the `sb…` client ID. Amount is pre-filled at `249.00`.
4. Click **Load SDK & check eligibility**.

The page tries the SDK v6 path (`createInstance` → `findEligibleMethods` → `isEligible("paylater")`
→ `getDetails`), falls back to a v5-style call, and logs which step failed. It never guesses: no SDK
answer is treated as "not eligible", the same position `paylater.py` takes.

---

## P1.3 — Record the result (2 min)

Click **Copy result line**, then paste it into the results table in
`../../09_build/prototype/PAYLATER_SANDBOX_TEST.md` and fill in the row.

Expected shape: `probe | amount 249.00 US | sdk_loaded yes | findEligibleMethods returned | isEligible(paylater) true | codes XYZ / US`

---

## P1.4 — Choose the script

| Probe result | OFFER branch becomes | Video script | On camera |
|---|---|---|---|
| `isEligible("paylater") === true` | `paylater` — real `<paypal-paylater-button>` | **Script A** | Show the real button and the eligibility call |
| `false` | `authorize_hold` — real `AUTHORIZE` + approval | **Script B** | Say why; **the invoice becomes the hero** |
| SDK failed / no boolean | Same as `false` | **Script B** | Say the SDK did not answer — never fake a button |

Then tell me the result and I will lock the chosen script's wording into
[SUBMISSION_KIT.md](SUBMISSION_KIT.md) §3.

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| SDK will not load | Check the ID starts `sb`; try another browser; disable blockers. If it still fails, treat as `false` and say so |
| `createInstance is not a function` | Expected on some builds — the page falls back automatically; read the log |
| Answers `false` | **This is a successful result.** It closes the tripwire |
| Answers `false` but you expected `true` | Try a different US sandbox buyer and a fresh business. Two attempts maximum, then accept and record |
| Tempted to hard-code a Pay Later button | **Never.** A faked button is the one failure that destroys credibility in a live Q&A |

---

## Exit criteria

- [ ] Probe **served from localhost** and run against the sandbox client ID
- [ ] Three amounts run; full JSON pasted for all three
- [ ] Band **observed** from the sweep (or the assumption explicitly corrected)
- [ ] Button rendering recorded per amount, with a screenshot
- [ ] Session attempted at the first eligible amount, outcome recorded
- [ ] **Decision A or B written down, with the reason citing the evidence**

**If this slips past 2 Nov:** it does not block anything else. P3/P4/P5 proceed. It must be closed
before P7.2 (recording). Default if unresolved at recording: **Script B** and one honest sentence.
