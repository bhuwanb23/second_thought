# Pay Later sandbox test — 20 minutes, decides how you word the OFFER branch

**Why this matters.** Pay Later is the one part of the product that depends on something you
cannot control from the server. If it renders in your sandbox, the OFFER branch can show a real
Pay Later button. If it doesn't, the OFFER branch must visibly fall back to an authorisation
hold — and you must say so on camera rather than implying a feature that isn't there.

Run this **before** you record. It changes the script.

---

## What you need

- A PayPal developer account and a sandbox **business** app (client ID)
- A sandbox **personal** buyer account in the **US** (Pay Later eligibility is country-scoped)
- 20 minutes

```bash
export PAYPAL_CLIENT_ID=...      # sandbox business app
export PAYPAL_CLIENT_SECRET=...
export PAYPAL_WEBHOOK_ID=...
```

---

## Test A — server side (2 min)

Confirm the server half works and is genuinely calling PayPal.

```bash
curl -s localhost:8000/healthz
# {"ok": true, "paypal": "live", "ai": "..."}      <- "live" means real REST calls

python3 demo.py --live
```

**Pass:** `PayPal mode: LIVE`, and the invoice id in the output starts `INV2-` and resolves at
`sandbox.paypal.com`. **Fail:** any `401` — the client id/secret pair is wrong or you're using a
live app's credentials against sandbox.

---

## Test B — does Pay Later render? (10 min)

This is the actual question, and it should take **two minutes**, not ten.

**`paylater_probe.html` is already written and in this folder.** No editing required:

1. Download `paylater_probe.html` and open it in **Chrome or Safari directly** — double-click the
   file. It will not work in a workspace preview pane, which blocks network access.
2. Paste your **sandbox client ID** (`sb…`) into the field. The amount is pre-filled at 249.00.
3. Click **Load SDK & check eligibility**.
4. It prints a plain-English verdict — eligible / not eligible / inconclusive — plus the raw SDK
   responses, and a **Copy result line** button.

The page tries the SDK v6 path (`createInstance` → `findEligibleMethods` → `isEligible("paylater")`
→ `getDetails`) and falls back to a v5-style call, logging every step so a failure tells you *which*
step failed. It never guesses: no SDK answer means "treat as not eligible", which is the same
position `paylater.py` takes on the server.

> **Use a US sandbox business account with a US buyer.** Pay Later eligibility is scoped to the
> buyer's country, the business type and the business's history. A non-US pair fails for reasons
> that have nothing to do with this project, and would send us to the fallback script for no reason.

### Reading the result

| Result | What it means | What you do |
|---|---|---|
| `paylater eligible: true`, details show a `productCode` | **Best case.** Pay Later works. | Show the eligibility call and the button on screen. OFFER branch demonstrates the real thing. |
| `paylater eligible: false` but the call succeeds | Eligibility is working; you're just not eligible (wrong country, amount below the threshold, or the account isn't enabled) | Try a different amount (Pay Later has min/max thresholds — try `60.00` and `900.00`) and confirm your buyer account is US. If still false, go to the fallback wording. |
| The SDK fails to load, or `createInstance` throws | Sandbox/account configuration problem | Do not spend more than 10 minutes. Go to the fallback wording. |
| Works locally but not on the deployed URL | Domain allowlisting / geo | Record locally. Don't ship a broken button. |

---

## Test C — the fallback path (5 min)

This is the one you must have working regardless, because it is what runs outside the US and
for most sandbox accounts.

```bash
# no eligibility posted -> the OFFER branch falls back to an authorisation hold
curl -s "localhost:8000/api/decide?persona=sam" | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print(d['instrument'], d['requires_approval'])"
# authorize_hold True

TOKEN=$(curl -s -X POST localhost:8000/api/approve -H 'Content-Type: application/json' \
  -d '{"persona":"sam"}' | python3 -c "import json,sys;print(json.load(sys.stdin)['token'])")

curl -s -X POST localhost:8000/api/execute -H 'Content-Type: application/json' \
  -d "{\"persona\":\"sam\",\"token\":\"$TOKEN\"}"
```

**Pass:** `order … → authorized AUTH-…` and the authorisation is visible in the sandbox account.

---

## The two scripts, depending on the outcome

### If Pay Later works (Test B = true)

> "PayPal's SDK tells us Pay Later is available for this shopper at this amount — here's the
> eligibility call, and here's the `productCode` it returned. We only render the button when
> that comes back true. If it comes back false, we don't show a button that does nothing; we
> fall back to an authorisation hold, which works everywhere."

### If Pay Later does not work (Test B = false)

Say it plainly, on camera, in one sentence:

> "Pay Later availability depends on the shopper's country and the merchant account, and it
> isn't enabled in this sandbox — so we gate on `findEligibleMethods()` and fall back to a
> real authorisation hold. The decision, the calendar and the scheduled invoice are all live
> PayPal calls either way."

Then **make the invoice the hero.** It is your strongest and most reliable PayPal path:

- `POST /v2/invoicing/invoices` with `detail.payment_term.due_date`
- A real invoice id (`INV2-…`) that opens on sandbox
- 0.5% of the field uses Invoicing at all
- It is the mechanism no other entrant has, and it is the DEFER verdict — your best story

**Never fake a Pay Later offer screen.** A mock of someone else's checkout is the fastest way
to lose a PayPal judge's trust. Eligibility metadata is honest; a painted button is not.

---

## Record the result here

| Test | Date | Result | Notes |
|---|---|---|---|
| A — server live | | | |
| B — Pay Later renders | | | `productCode`: |
| C — fallback authorisation | | | |

Whichever way B goes, the submission must state it. Ambiguity about a payment method is the
one thing a PayPal engineer will check first.
