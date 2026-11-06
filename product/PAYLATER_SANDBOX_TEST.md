# V1 — Pay Later sandbox probe

**Goal:** know, with evidence, whether Pay Later renders — and therefore what the **OFFER** branch
may say on camera.

**Pass:** a decision is written down with evidence, not a guess.
**Fails if:** the decision is written from memory, or from a number we assumed.

> This supersedes `../09_build/prototype/PAYLATER_SANDBOX_TEST.md`. That file described a one-amount
> probe; this one runs the three amounts and the band sweep, and captures a machine-readable report.

---

## Setup (3 minutes)

```bash
cd product
python3 scripts/serve_probe.py            # prints http://localhost:8099/v1_probe.html
```

Open that URL. **Do not open the HTML file directly** — the PayPal JS SDK will not load from a
`file://` path, and the workspace preview pane blocks the network entirely.

Have ready:

- The **sandbox client ID** from V0.1 (the `sb…` / `AX…` value — never the secret)
- Confirm the sandbox **business** and **personal (buyer)** accounts are both **US** (V0.7)

---

## Run it

The probe is pre-filled with the three amounts that answer the question, plus a band sweep:

| Field | Default | Why |
|---|---|---|
| Amounts to test | `10, 500, 2500` | **below / inside / above** the likely range |
| Band sweep | `25, 50, 100, 200, 400, 800, 1200, 1500` | finds the **actual** band instead of assuming $30–$1,500 |

For each amount the probe records:

1. the **full `findEligibleMethods` response** (not a summary)
2. `isEligible("paylater")` and `isEligible("paypal")`
3. `getDetails("paylater")` — the `productCode` / `countryCode` pair the button would need
4. whether the **button actually renders** — element mounted, then measured with
   `getBoundingClientRect()` and computed `display`. A button in the DOM with zero size is *not*
   a rendered button
5. **a real session attempt** at the first eligible amount —
   `createPayLaterOneTimePaymentSession()` then `start()`, which opens the buyer flow. This is the
   difference between "the SDK says yes" and "a session can actually be created"

Then it prints a **decision (A or B)** and enables **Copy JSON report**.

---

## If a session opens: log in as the sandbox buyer

The session attempt opens PayPal's buyer flow. Complete it with the sandbox **personal** account:

- It will ask for the sandbox buyer email and password (from developer.paypal.com → Sandbox → Accounts)
- If it completes, the `onApprove` callback logs the payload into the step log — **copy that**
- If it refuses, the error message is the evidence; paste it too

**Do not fake this step.** "Eligible" without a created session is a weaker result, and must be
recorded as such.

---

## Record it here

### 1. Raw eligibility JSON, all three amounts

Paste the full `findEligibleMethods` responses. Do not summarise — a judge may ask what the response
looked like.

```json
// $10
{ }

// $500
{ }

// $2500
{ }
```

### 2. The band, as observed (not as assumed)

| Band edge | Observed | Evidence |
|---|---|---|
| Lowest eligible amount | | from the sweep |
| Highest eligible amount | | from the sweep |
| Matches the $30–$1,500 assumption? | ☐ yes ☐ no | if no, **the assumption was wrong and we quote the observation** |

### 3. Button rendering

| Amount | Rendered? | Size | Notes |
|---|---|---|---|
| $10 | | | |
| $500 | | | |
| $2500 | | | |

Screenshot of the mount area: `probe-screenshot-YYYY-MM-DD.png` (drop it in `probe/`)

### 4. Session attempt

| Amount attempted | Session created? | Buyer flow outcome | Payload / error |
|---|---|---|---|
| | | | |

### 5. The decision

> **Script A** — Pay Later renders → OFFER shows the real `<paypal-paylater-button>`, and the
> eligibility call is shown on camera.
>
> **Script B** — it does not → OFFER falls back to a real `AUTHORIZE` hold, and **the invoice becomes
> the hero**.

**Decision:** ☐ **A** ☐ **B**

**Reason (one sentence, citing the evidence above):**

**Date:**

---

## How the decision changes the video — and nothing else

| | Script A | Script B |
|---|---|---|
| OFFER branch shows | real Pay Later button | real `AUTHORIZE` hold |
| On camera | "the SDK confirms eligibility, here is the call" | "Pay Later would not render for us — here is the authorisation instead" |
| Hero moment | Pay Later + the invoice | **the invoice** |
| The idea | unchanged | unchanged |

**This tripwire never changes the product.** It changes two sentences and which screen leads.

---

## Failure modes → what they actually mean

| Symptom | Meaning | Response |
|---|---|---|
| SDK will not load | CSP, network, a blocking extension, or a bad client ID | Fix the load first. This is **inconclusive**, not an answer |
| `401` / `invalid_client` | Wrong ID, or a Live app used against sandbox | Regenerate from the Sandbox app (V0.1) |
| Every amount returns `false` | The sandbox business is not eligible — common | **Script B.** Report it plainly |
| Eligible but button is zero-size | Pay Later messaging is disabled in this context | **Script B**, and say why |
| Eligible but session creation throws | Session needs a buyer login first | Log in as the sandbox buyer, retry once |
| Sweep shows a band narrower than expected | Our $30–$1,500 assumption was wrong | Quote the observed band, and drop the assumption from the script |

---

## Result

```text
$ python3 scripts/serve_probe.py
(paste the JSON report here, with the date and the decision)
```
