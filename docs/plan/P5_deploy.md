# P5 — Deploy & durability

**Status:** ⬜ **not started**
**Owner:** you · **Window:** 4 Nov · **Hours:** 2.0
**Exit condition:** the **hosted demo proves itself** — badge reads `SANDBOX · LIVE` and `AI · LLM`, a **real invoice is created from the public URL**, the webhook verifies live, and it all stays up through 15 Dec

---

## Purpose

Two separate obligations hide in one phase:

1. **The demo must be reachable** by a judge who will not clone a repo.
2. **It must stay up until 15 Dec 08:00 PT.** The rules are explicit: the project must remain
   available free of charge until judging ends. A demo that dies in December fails a stated
   requirement, no matter how good the video was.

Serves: **Presentation**, **Technological Implementation**, and rule compliance #10.

> **Correction (review):** a green `/healthz` proves almost nothing — a deployed instance can silently
> run the simulator while the README claims real PayPal calls. **P5.5** replaces "it is up" with
> "it is demonstrably doing the real thing from a URL a judge can open". That is the difference
> between a deployment and a claim.

---

## P5.1 — Pre-deploy sanity (15 min)

```bash
cd product
python3 -m unittest discover -s tests -q     # OK
python3 scripts/preflight_deploy.py              # ALL CHECKS PASSED
```

Confirm before shipping:

- [ ] `render.yaml` exists, with `sync: false` on every secret
- [ ] `APPROVAL_SECRET` uses `generateValue: true` (never a committed value)
- [ ] `.env` is **not** in the image (`.dockerignore` covers it)

---

## P5.2 — Deploy to Render (40 min)

1. Push the root repository to a **public** GitHub repo (P5.4 covers licensing).
2. Render → **New → Blueprint** → select the repo. It reads `render.yaml`.
3. Set the secrets marked `sync: false`: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`,
   `LLM_API_KEY`. `LLM_MODEL` and `APPROVAL_SECRET` are handled by the blueprint.
4. Deploy. Render installs the Python package and starts `product/scripts/serve.py`.

**The plan is `starter`, deliberately — not free.** Free instances sleep, and a cold start inside a
judge's three-minute window is a lost Presentation score. `$7/month for the judging window` is the
cheapest insurance in this project.

**Verify:**

```bash
curl -s https://<your-app>.onrender.com/healthz | python3 -m json.tool
```

Expected shape:

```json
{"status": "ok", "ai_mode": "llm", "payments_mode": "sandbox", "checks": {}}
```

The public response contains only booleans and short status words. It reveals nothing
that the on-screen badge does not already show, because it is on a public,
unauthenticated URL.

The internal detail lives behind a token:

```bash
curl -s -H "X-Diag-Token: $DIAG_TOKEN" \
  "https://<your-app>.onrender.com/diagnostics" | python3 -m json.tool
```

Without a token, or with the wrong one, `/diagnostics` returns **404** — it does not
advertise that it exists.

| Field | Meaning | If wrong |
|---|---|---|
| `paypal: "live"` | Real sandbox REST transport, not the simulator | A PayPal secret did not reach the service |
| `ai: "llm"` | A key is present; not `llm-mock`, not `rules` | `LLM_API_KEY` missing |
| `badge` | Exactly what the on-screen badge will read | — |
| `approval_secret` (diagnostics only) | `"env"` means the HMAC secret came from the environment | `"default"` means the shipped dev secret is in use — **fix before recording** |

---

## P5.3 — Keep-alive, and verify it for real (20 min)

Three layers, because GitHub cron is best-effort and unreliable on its own:

| Layer | What | Cost |
|---|---|---|
| 1 | Render **starter** plan — does not sleep | $7/mo |
| 2 | `.github/workflows/keepalive.yml` — pings every 10 min, **fails loudly** | free |
| 3 | An external monitor (e.g. UptimeRobot, 5-min interval) | free |

**Do not assume the workflow runs.** Verify it:

1. Actions tab → **Keep-alive** → run it manually once → green.
2. Wait for one scheduled run → confirm it appears in the log.
3. **Re-verify on 1 Dec**, the first day of judging. Put a calendar reminder in now.

> This is the one requirement that is satisfied on 10 Nov and broken on 12 Dec. Treat the December
> re-check as part of the work, not a note.

---

## P5.4 — Rate limits, spend cap, and the HMAC secret (20 min)

A public URL with an LLM behind it will be found by crawlers. Three protections, all verifiable:

| Protection | Where | Check |
|---|---|---|
| **Three limits** — 30/session, 90/IP, 1500/day per instance | `session.py`, enforced on `/api/extract`, `/api/agent`, `/api/profile` | 31 rapid calls on one cookie → `429`; **fresh cookies from one address stop at 90**; the global gate closes after 1500 |
| **Spend cap** — the real protection | Hard monthly limit in the LLM provider's console | Screenshot the setting. The in-app gates are a courtesy; the console cap is the backstop |
| **HMAC secret from the environment** | `APPROVAL_SECRET` in `render.yaml` via `generateValue: true` | `/healthz` → `approval_secret: "env"` |

The rate limit is **per session**, not global: one judge cannot exhaust another's budget, and a
crawler cannot drain the account.

## P5.4b — Public repo and visible licence (20 min)

A `LICENSE` file is **not** enough — GitHub must detect it and show it in the **About** panel, and
**17% of the scanned field fails this**.

- [ ] `LICENSE` (MIT) at the **repository root** — not in a subfolder
- [ ] Repo has a **description** and a **topic** or two
- [ ] The About panel shows a licence chip — check in an incognito window
- [ ] Repo is **public** — check the same way
- [ ] No `.env`, no `ledger.json`, no `profiles.json` committed (`git log --stat` scan)
- [ ] Secret scan clean (`grep -riE 'sk-|sb-|client_secret' --include=*.py --include=*.md .`)

---

## P5.5 — Clean-clone test (15 min) — this is the one people skip

In a **fresh directory**, with no `.env`:

```bash
git clone https://github.com/<you>/<repo>.git /tmp/clonetest && cd /tmp/clonetest/product
python3 -m unittest discover -s tests -q     # must pass with no credentials
python3 scripts/serve.py                      # must start
python3 -m secondthought.cli                 # must run simulated, labelled
```

If the clone fails without credentials, a judge fails it too. The build is designed for this: no
dependencies, no network needed, honest `SIMULATED` labelling.

---

## P5.6 — Webhook, verified live (20 min) — **this is why the webhook test lives here, not in P3**

A webhook needs two things that only exist after deploy: a **public HTTPS URL** and a **webhook ID
registered against that URL**. Testing it in P3 was impossible.

1. Render dashboard → copy the public URL.
2. PayPal Developer → your app → **Webhooks** → add `https://<app>.onrender.com/api/webhook`,
   subscribe to `PAYMENT.CAPTURE.COMPLETED` (and `INVOICING.INVOICE.PAID` if offered).
3. Copy the **webhook ID** into `PAYPAL_WEBHOOK_ID` on Render.
4. PayPal's **Webhooks simulator** → send a test event → expect a `200`, with the signature verified
   rather than accepted blindly.
5. Send a deliberately **bad signature** → expect a rejection. **Record this** — a rejected
   signature is the single best proof of non-trivial implementation available, and it takes 20 seconds
   on camera.

If verification fails, do **not** disable signature checking to make it pass. Log it as a known
limitation and say so; a webhook endpoint that accepts anything is worse than none.

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| Blueprint deploy fails | Deploy as a plain **Web Service → Python** using `product/render.yaml` and record the deviation in [DECISION_LOG](DECISION_LOG.md) |
| Build succeeds, app crashes | Read the Render log; almost always a missing env var. `/healthz` shows which subsystem is degraded |
| `paypal:"simulated"` in production | Secret missing. Fix before recording — a simulated public demo is fine *if labelled*, but the point of P5 is live |
| Free-plan sleeping (if you override to free) | Accept longer cold start, keep the keep-alive, and say it in the README |
| Hosted demo runs the simulator | **Never ship it.** `/healthz` shows `paypal:"simulated"` — find the missing secret. A public demo labelled honest is survivable; a public demo that contradicts the README is not |
| Actions cron never fires | Rely on the external monitor; verify manually on 1 Dec either way |

---

## Exit criteria

- [ ] Public URL live; `/healthz` reports **`payments_mode:"sandbox"`, `ai_mode:"llm"`, and configured checks**
- [ ] **A real `INV2-…` invoice created from the public URL** (not from localhost), visible in the sandbox merchant account
- [ ] Badge on the hosted page reads **`SANDBOX · LIVE`** and **`AI · LLM`**
- [ ] `/healthz` returns only status words and booleans
- [ ] `/diagnostics` returns **404** without the token, full detail with it
- [ ] 31 calls on one cookie → `429`; **fresh cookies from one IP stop at 90**
- [ ] Provider spend cap screenshotted
- [ ] Spend cap set in the provider console, screenshotted
- [ ] Webhook verified live, **and a bad signature rejected** (P5.6)
- [ ] **Render named in the submission** — prize eligibility is by tool use
- [ ] Starter plan (not free) or a documented, working alternative
- [ ] Keep-alive workflow **manually run once and green**
- [ ] External monitor configured
- [ ] **Calendar reminder for 1 Dec**
- [ ] Repo public, licence visible in About (checked incognito)
- [ ] Clean-clone test passes with no credentials
- [ ] No secrets in git history
