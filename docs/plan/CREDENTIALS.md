# Getting the credentials — step by step

*Written 5 Nov 2026. Four accounts, one file, about 45 minutes. Do them in this order:
the `.gitignore` before the `.env`, and the webhook **after** the deploy, because a
webhook needs a URL to point at.*

| What | Time | Unblocks |
|---|---|---|
| 0. Repo + `.gitignore` | 5 min | everything after it; keeps secrets out of git |
| 1. `PAYPAL_CLIENT_ID` + `PAYPAL_CLIENT_SECRET` | 10 min | V0, V1, V3, half of V6 |
| 2. Sandbox buyer and seller accounts | 5 min | V1 session, V3 dashboard confirmation |
| 3. `LLM_API_KEY` | 10 min | V4, the mandatory-AI rule, the badge flipping to `AI · LLM` |
| 4. `product/.env` | 5 min | all of the above at once |
| 5. `RENDER_API_KEY` + the deploy | 15 min | V5.6, V6, V8 |
| 6. `PAYPAL_WEBHOOK_ID` | 5 min | the live webhook transmission (P5.6) |

---

## 0. Before any secret exists: the repo and its `.gitignore`

`product/` is not a git repository yet. If the first commit happens after `.env` exists,
a secret can be committed, and a secret that reaches a remote is compromised the moment it
does — history rewriting does not un-leak it. So this goes first.

```bash
cd product

git init
git add .gitignore          # already written; ignores .env, artifacts/, __pycache__/
git commit -m "Second Thought: product, 159 tests, no credentials in tree"

git status                  # after adding the rest:
```

Then create the GitHub repo and push:

```bash
gh repo create second-thought --private --source=. --push
# or: git remote add origin git@github.com:<you>/second-thought.git && git push -u origin main
```

Keep it **private until the submission is ready** — it will contain no secrets, but it
will contain half-finished claims. Make it public before the Devpost form, because the V8
tester and the judges both need the repo link.

Add a licence while you are here — the P7 checklist wants a licence chip visible in an
incognito window, and there is no `LICENSE` file:

```bash
curl -s https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt \
  | sed "s/<year>/2026/; s/<copyright holders>/<your name>/" > LICENSE
git add LICENSE && git commit -m "MIT"
```

---

## 1. PayPal sandbox client ID and secret

You need a **PayPal account** (a normal personal one is fine — a developer account is no
longer separate) and the dashboard set to **Sandbox**.

1. Go to **https://developer.paypal.com/dashboard** and log in with your ordinary PayPal
   login.
2. Find the **Sandbox / Live** toggle — top right of the dashboard — and make sure
   **Sandbox** is selected. This is the step that most guides get wrong: the credentials
   page looks identical in both modes and the keys are completely different.
3. Left navigation → **Apps & Credentials**. Under **REST API apps** you should already
   have a **Default Application** that PayPal created for you.
   - Use it, or click **Create App**, name it `Second Thought`, type **Merchant**, save.
4. Open the app. Under **Sandbox API Credentials**:
   - **Client ID** — a long string, often starting `A...` or containing `sb`. Copy it.
   - **Secret** — click **Show**, then copy. It is revealed only on demand; treat it as a
     password even though it is a sandbox key.
5. Note the **Sandbox account** shown in the app header — that is the *merchant* the money
   lands in. You will need it in the dashboard when you go looking for your invoices.

**Verify before you go further.** This is exactly what `v0_check.py` does, but run it by
hand once so you know what success looks like:

```bash
curl -s -X POST "https://api-m.sandbox.paypal.com/v1/oauth2/token" \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" | head -c 300
```

You want `{"scope":"...","access_token":"A21...","token_type":"Bearer","expires_in":32400}`.
If you get `{"error":"invalid_client"}`, you almost always copied a **Live** key while the
dashboard was on Sandbox, or vice versa. Nothing else produces that error as often.

> **Sandbox only.** `PAYPAL_ENV=sandbox` is the default and the code refuses `live` at
> runtime by design. Do not create live keys for this project — there is no reason to, and
> a live key in a hackathon repo is a liability rather than a credential.

---

## 2. A sandbox buyer and seller, for the calls that need a human

Two of the gates need a person clicking **Log in with PayPal** inside the sandbox: V1
(session creation with the personal buyer) and V3 (finding the artifacts in a dashboard).

1. Dashboard → **Testing Tools** → **Sandbox Accounts**.
2. PayPal pre-creates one **Personal** and one **Business** account. If not, **Create
   account** → *Personal*, country **United States** (the shopper side needs a US buyer —
   Pay Later eligibility is country-sensitive), and give it a **balance** — $3,000 is
   plenty.
3. Click the **⋮** next to the account → **View/Edit Account** to reveal the generated
   **email** and **password**. Write them somewhere local, not in the repo.
4. Log in at **https://sandbox.paypal.com** with those to confirm they work.

---

## 3. An LLM key

The product speaks the OpenAI-compatible `POST {base_url}/chat/completions` shape, so any
provider that offers it works. It uses `temperature: 0` and
`response_format: {"type": "json_object"}`, so the model must support JSON mode.

| Provider | `LLM_BASE_URL` | `LLM_MODEL` | Notes |
|---|---|---|---|
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | needs a card; ~$5 of credit is far more than this project uses |
| Groq | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` | free tier, fast, JSON mode supported |
| OpenRouter | `https://openrouter.ai/api/v1` | any listed model | pay-as-you-go, one key for many models |

**OpenAI path:** platform.openai.com → sign in → **Settings → Billing** → add the minimum
credit → **API keys → Create new secret key** → name it `second-thought`, scope it to the
project → copy. It is shown **once**.

**Set the spend cap now, not later** — a judge cannot see it, but a runaway demo can cost
you real money:

- OpenAI: **Settings → Limits → Monthly budget**, set **$5**, and set a **hard limit**.
- Groq/OpenRouter: same idea in their billing pages; OpenRouter has per-key credit limits.

The in-app `LLM_DAILY_CALL_BUDGET=1500` is a backstop, not a budget — the provider-side cap
is the real protection.

**Verify:**

```bash
curl -s https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $LLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gpt-4o-mini","temperature":0,"response_format":{"type":"json_object"},
       "messages":[{"role":"user","content":"reply with {\"ok\":true}"}]}' | head -c 300
```

A `model_not_found` means the model name is wrong for that provider — fix `LLM_MODEL`
rather than the key. A `429` means no credit or a rate limit, not a bad key.

---

## 4. `product/.env`

Now the file the product actually reads. **It must live at `product/.env`** — the loader
resolves it relative to the package, so running from the repo root will not pick it up.

```bash
cd product
cp .env.example .env
chmod 600 .env
```

Fill in six lines (leave the rest as they are):

```ini
PAYPAL_CLIENT_ID=AY...your-client-id
PAYPAL_CLIENT_SECRET=EL...your-secret
PAYPAL_ENV=sandbox
LLM_API_KEY=sk-...your-key
LLM_MODEL=gpt-4o-mini
LLM_BASE_URL=https://api.openai.com/v1
APPROVAL_SECRET=<paste a long random string>
```

Generate a real `APPROVAL_SECRET` rather than inventing one:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

`PAYPAL_WEBHOOK_ID`, `DIAG_TOKEN` and `RENDER_API_KEY` can stay empty for now.

**How the file is read, precisely** — this was broken until today and is worth knowing:

- `secondthought/config.py` loads `product/.env` at import, filling only variables that are
  **not already set**. A real environment variable always wins, so the Render dashboard
  configures production and a stray `.env` can never override it.
- In `ST_ENV=production` the file is not read at all.
- Values are never printed. `settings.describe()` reports presence, not contents, and
  `/healthz` reports booleans.

Confirm it took, before running anything that costs money or makes a call:

```bash
python3 scripts/v0_check.py
```

Expect **14 rows**: V0.1–V0.6 PASS except V0.6 (Render plan) which needs an account, and
whichever of V0.3/V0.4 you have not done. If V0.2 fails, the credentials are wrong, not the
file — go back to the `curl` in step 1.

Then, and only then:

```bash
python3 demo.py --live       # V3: five real sandbox calls
python3 demo_ai.py --live    # V4: the badge should read AI · LLM
```

Both write `artifacts/v3/<timestamp>/` and `artifacts/v4/<timestamp>/` with every raw
response plus **where to find each ID in the dashboard**. That last part is the V3 pass
condition — go and find them, do not take the script's word for it.

---

## 5. Render, and the deploy

1. Sign up at **https://dashboard.render.com** with GitHub. **Add a payment method and
   pick the Starter plan** — the free tier sleeps after 15 minutes, which breaks V6 item 5
   and makes the first judge who clicks your link wait a minute. `preflight_deploy.py`
   enforces `plan: starter` for exactly this reason.
2. **New → Blueprint**, pick the `second-thought` repo. Render reads `render.yaml`, which
   already declares the service, the start command and the non-secret environment.
3. Before the first deploy, add the secret environment variables in the dashboard —
   *Environment* → add each: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `LLM_API_KEY`,
   `APPROVAL_SECRET`, `DIAG_TOKEN`. Never put them in `render.yaml`.
4. Deploy. You get `https://second-thought-xxxx.onrender.com`.
5. Verify from outside:

```bash
curl -s https://your-app.onrender.com/healthz
# {"status":"ok","ai_mode":"llm","payments_mode":"sandbox","checks":{...}}
```

If it still says `llm-mock` or `simulated`, the dashboard variables are missing or the
service did not restart after you added them.

6. **The API key** (`RENDER_API_KEY`) is only used by `v0_check.py` to prove the instance is
   paid rather than free: dashboard → **Account Settings → API Keys → Create API Key**,
   copy it (shown once, starts `rnd_`). Put it in your local `.env` only — never in the
   Render dashboard, it would be a key to the account inside the account.

---

## 6. The webhook — last, because it needs the URL

1. PayPal dashboard → **Apps & Credentials** (still on **Sandbox**) → open your app →
   scroll to **Webhooks** → **Add Webhook**.
2. **Payload URL:** `https://your-app.onrender.com/api/webhook`
3. **Event types** — tick these three; the handler acts on the first two and logs the third:

   - `INVOICING.INVOICE.SENT`
   - `INVOICING.INVOICE.PAID` ← the one that turns a DEFER into a shipment
   - `PAYMENT.CAPTURE.COMPLETED`

4. **Save**, then copy the **Webhook ID** (`WH-...`) shown on the webhook card.
5. Put it in both places: the Render dashboard variable `PAYPAL_WEBHOOK_ID`, and your local
   `product/.env`. Redeploy.

Verify without PayPal's help first — our own endpoint rejects a bad signature loudly:

```bash
curl -s -i -X POST https://your-app.onrender.com/api/webhook \
  -H 'Content-Type: application/json' -d '{"event_type":"INVOICING.INVOICE.PAID"}'
# expect HTTP 400, "missing header", PAYPAL-TRANSMISSION-ID
```

Then PayPal → your webhook → **Simulate** (or a real sandbox invoice payment) and check
`/diagnostics` with your `X-Diag-Token` to see it counted as verified.

---

## Troubleshooting, by symptom

| Symptom | Cause | Fix |
|---|---|---|
| `PAYMENTS · SIMULATED` after setting the creds | `.env` not at `product/.env`, or you exported variables in a different shell | `cd product && python3 -c "from secondthought.config import load; print(load().describe()['paypal'])"` |
| OAuth `invalid_client` | Sandbox key copied while the dashboard was on Live, or trailing whitespace | re-copy with the toggle on Sandbox; the loader strips whitespace but not stray quotes |
| V3 invoice created but not in the dashboard | you are looking at the wrong sandbox merchant | the app header names it; log into sandbox.paypal.com as *that* account |
| `403` on `/api/quote` in the browser | approval/session cookie from an earlier run | hard-refresh; sessions are in memory and a redeploy clears them |
| Webhook `400 missing header` from *PayPal* | URL wrong, or the webhook is on a different app than the keys | confirm the payload URL and that it is the sandbox app |
| Webhook arrives, signature fails | wrong `PAYPAL_WEBHOOK_ID`, or two apps in the account | the ID must be the one on the card for *that* URL |
| `model_not_found` | `LLM_MODEL` not offered by your provider | check the provider's model list; the key is probably fine |
| Badge stays `LLM-MOCK` locally but works deployed | local `.env` missing the key | same `describe()` command, `['llm']` |

---

## One thing about sharing them

Do not paste real keys into this chat, an issue, a commit, or a screenshot. If you want the
live runs executed **in this workspace** rather than on your own machine, put the values in
`product/.env` here — the sandbox keys and a spend-capped LLM key are low-risk, but they
would then exist in the conversation, so plan to **rotate or revoke them after the
submission**. If you would rather not, run the three commands locally and paste only the
**output**; that is enough for me to debug anything.
