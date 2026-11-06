# V0 — Preconditions (do once)

**Status:** ⬜ **blocking** — nothing downstream starts until this is green
**Owner:** you · **Window:** 2 Nov, before P1 · **Hours:** ~45 min
**Exit condition:** `python3 scripts/v0_check.py` exits 0, and the manual rows are confirmed

---

## The rule

> **If any row fails, stop.** Everything downstream assumes these are real.

A fake precondition is worse than a missing one: it lets you spend a day recording a demo that is
actually running the simulator, and find out afterwards. So each row below is either **proved by a
script** or **marked MANUAL and listed as outstanding** — never assumed.

Run it from the product directory:

```bash
cd product
python3 scripts/v0_check.py            # all gates, including two live calls
python3 scripts/v0_check.py --offline  # skip the network, check the rest
```

Exit code `0` = every automatable gate passed. `1` = **stop**.

---

## The gates

| # | Precondition | Pass criteria | How it is verified |
|---|---|---|---|
| **V0.1** | Fresh PayPal sandbox app created today | Client ID + secret in hand, **not reused** from an old demo | Script confirms both are present and reports whether the id carries an `sb` marker. *Freshness is V0.8 — manual* |
| **V0.2** | Credentials actually work | OAuth returns `200` against `api-m.sandbox.paypal.com` | **Script makes the real OAuth call.** `401` = wrong pair or a Live app pointed at sandbox. `403` = missing scope; create a fresh app rather than fighting it |
| **V0.3** | LLM key active, spend cap confirmed | Key present, billing live, a **$1 test call succeeds and shows in usage** | Script confirms the key authenticates. The `$1 call + usage` is **MANUAL** — the script deliberately uses the free `/models` endpoint so it costs nothing |
| **V0.4** | LLM endpoint reachable | Authenticated call succeeds | Script calls `GET {LLM_BASE_URL}/models` with the key and reports whether `LLM_MODEL` is in the list |
| **V0.5** | `.env.example` matches every variable the code reads | No drift in either direction, and exactly one reader | **Script diffs all three**: the declared contract, `.env.example`, and every `os.environ` read in the package. Any environment read outside `config.py` fails the gate |
| **V0.6** | Render account + **paid Starter** instance | Dashboard shows "Starter", not "Free" | Script queries the Render API **if** `RENDER_API_KEY` is set; otherwise **MANUAL** |
| **V0.7** | Sandbox **personal (buyer)** + **business (merchant)** accounts, both **US** | Both visible in the developer dashboard, both country US | **MANUAL.** Pay Later eligibility is geo-scoped; a non-US pair fails for reasons unrelated to the code |
| **V0.8** | App created **today**, not reused | Creation date recorded next to the client id | **MANUAL.** Reusing an old app means an unknown history, and eligibility depends on business history |
| **V0.9** | Provider spend cap set | Hard monthly limit visible in the provider console | **MANUAL.** The in-app budget (`LLM_DAILY_CALL_BUDGET`, default 1500/day) is a backstop, **not** the protection |

---

## Why V0.5 is a script and not a `diff`

Your version said "`diff` the two manually". Manually diffing is where this drifts — someone adds
`PAYPAL_WEBHOOK_ID` to the code on a Thursday night and the example file is never touched.

The gate now enforces three things at once:

1. every variable in `ENV_CONTRACT` appears in `.env.example` (nothing documented is a lie)
2. every variable in `.env.example` is in the contract (nothing documented is unused)
3. **no file outside `config.py` reads the environment** (there is exactly one place the contract can change)

That third rule caught real drift the first time it ran: `approvals.py` was reading
`APPROVAL_SECRET` directly. It now goes through `config.py`.

---

## What each failure blocks

| Gate | If it fails | Can you proceed? |
|---|---|---|
| V0.1 / V0.2 | No real PayPal call is possible | **No.** P3 and the whole invoice story depend on it |
| V0.3 / V0.4 | The badge stays `AI · LLM-MOCK` | **No.** Stage 1 requires AI that is genuinely used |
| V0.5 | The documented environment is fiction | **Fix it — it is a five-minute change and it is the cheapest gate here** |
| V0.6 | Free instance sleeps; a cold start inside a judge's window costs Presentation | **Provision Starter before P5**, but P1–P4 can proceed |
| V0.7 | Pay Later eligibility may be unobtainable | **Proceed to P1 anyway** — a "not eligible" answer is still a valid result. Note it |
| V0.8 | Unknown business history changes eligibility | Proceed, but **say so** if eligibility is surprising |
| V0.9 | Nothing today; a runaway loop becomes a bill | Set it before P4 |

---

## Sequence

```
V0 ──all green──▶ P1 (Pay Later probe) ──▶ P3 ──▶ P5 ──▶ P7
      │
      └── any FAIL ──▶ stop, fix, re-run. Do not start P1.
```

**V0 comes before P1**, not in parallel, because P1's answer is only meaningful with a US sandbox
pair and a fresh app.

---

## Recording the result

When it passes, paste the final output into this file and date it. That is the evidence that the
demo you are about to record was standing on real credentials.

```text
$ python3 scripts/v0_check.py
(paste here, with the date)
```

> **Note:** the checker never prints a secret. It reports whether a value is present and whether the
> provider accepted it — never the value itself.
