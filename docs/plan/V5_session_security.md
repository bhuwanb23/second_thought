# V5 — Session isolation & security

**Status:** 🟢 **1, 2, 3, 4, 5 PASS** (over a real socket, two real cookie jars) · 🟠 **6 PASS locally, pending a Render redeploy**
**Pass:** no cross-session leakage, no secret leakage, no unauthenticated money action.

The HTTP layer did not exist before this gate. `product/secondthought/interfaces/` was empty apart from a badge file. V5 is the reason it now exists — and it exists stdlib-only, because the point of it is that the security properties fit on one screen.

---

## 1. The result

```
bash scripts/v5_two_jars.sh        # 22 checks, real server, real curl, real jars
══════════════════════════════════════════════════════════════════════
  22 passed, 0 failed
══════════════════════════════════════════════════════════════════════
```

**Test suite: 79 → 110.** Every file under 300 lines.

| Item | Asked | Result |
|---|---|---|
| 1 | Two sessions, separate jars | ✅ two jars → two session ids, two distinct signing keys |
| 2 | A saves a profile and executes; B's Maya verdict unchanged | ✅ A executed (`AUTHORISED`), B still `DEFER`, still reading `persona-default` |
| 3 | 31 model calls in one session → 429; second session unaffected | ✅ call 30 = 200, call 31 = **429**, session B = 200 |
| 4 | `/healthz` logged out, no secrets | ✅ 200, four keys, all booleans, no secret value present |
| 5 | Money tool without a valid token | ✅ 403 from four different directions — see §4 |
| 6 | Restart, sessions gone cleanly | ✅ local process restart: old cookie → 200, profile gone, boot id changed, no crash |

---

## 2. The isolation rule, and where it is enforced

> A visitor's profile lives in their session object. There is no code path that
> writes it anywhere a second visitor can read.

| Mechanism | File | What it guarantees |
|---|---|---|
| Session-scoped profile | `interfaces/http.py::ScopedProfiles` | `get("me")` reads the session; `save` raises for any other id. Persona defaults are a separate store that this class never writes |
| Per-session approval key | `app/approvals.py` + `interfaces/session.py` | A token minted in browser A fails the HMAC in browser B — it is not merely rejected, it is unverifiable |
| Signed cookie | `SessionStore.issue_cookie` | `sid.boot.HMAC(sid)`. A forged signature gets a **new** session, never someone else's |
| Boot id in the cookie | `SessionStore.read_cookie` | Every cookie from before a restart is honestly dead, not secretly stale |
| In-memory sessions | `SessionStore._sessions` | A restart loses them. The alternative — a durable cookie pointing at vanished state — is the failure item 6 is asking about |

**Rate limiting uses two keys, because one is not a limit.** Session: 30 model-backed calls per 10 minutes. IP: 90 per 10 minutes. The IP cap is a cookie-cycling backstop, set at 3× one session so a second real visitor on the same network is not punished for the first one's consumption. Both tested:

- `test_the_thirty_first_model_call_is_refused_and_the_second_session_is_not`
- `test_clearing_the_cookie_does_not_buy_a_new_budget` — 100 requests, a fresh jar each time; the first refusal lands at exactly **90**, never earlier

The persona buttons never call a model, so they never consume the budget: `test_the_persona_buttons_never_consume_the_model_budget`. A rate limit that breaks the demo it protects is worse than no limit.

---

## 3. `/healthz` — what it does and does not say

```json
{"status": "ok", "ai_mode": "llm-mock", "payments_mode": "simulated",
 "checks": {"ai_key": false, "paypal_credentials": false,
            "approval_secret": false, "database": true}}
```

Four keys, all booleans under `checks`. Tested with a **fully populated** configuration — a real-looking `PAYPAL_CLIENT_SECRET`, `LLM_API_KEY`, `APPROVAL_SECRET` and `DIAG_TOKEN` — and asserted that none of those values appears anywhere in the response. The shell script repeats the check against a running server with a known secret value.

Also: `Cache-Control: no-store` and `X-Content-Type-Options: nosniff` on every response, and a 500 handler that returns `internal error` plus the exception *class* and nothing else — no paths, no messages, no stack.

---

## 4. No unauthenticated money action

The routes that can move money accept exactly two tool names: `create_reservation` and `authorise_hold`. The two names V5 uses — `create_scheduled_invoice` and `authorize_payment` — are **refused as unknown**, not quietly mapped onto a real one. A money tool that is not on the list is not guessed at.

| Attempt | Result |
|---|---|
| `create_scheduled_invoice` (V5's name) | **400** unknown tool |
| `authorize_payment` (V5's name) | **400** unknown tool |
| `../../etc/passwd` as a tool | **400** unknown tool |
| Real tool, no token | **403** `approval required` |
| Real tool, made-up token | **403** |
| Real tool, token with last character changed | **403** |
| Real tool, token from another session | **403** signature fails |
| Real tool, token, amount `+1` | **403** `does not match` |
| Real tool, token, due date altered | **403** |
| Real tool, token, replayed | **403** `already been used` |
| Real tool, expired token | **403** `expired` |
| Token for `create_reservation` used on `authorise_hold` | **403** |
| Real tool, correct token | **200** — and the gateway is called exactly once |

`test_the_gateway_is_not_called_until_a_real_token_arrives` is the one that matters: every refused attempt above leaves the gateway's call list untouched. The refusals happen before money is reachable, not after.

Every refusal is recorded in `App.attempts` with its reason, so a log can answer "did anyone try?".

---

## 5. Item 6 — restart

**Proven locally, twice:**

*In-process* (`tests/test_http_session.py::Restart`) — construct a second `App`, the way a new process looks from inside. Old cookie → 200 with a clean session, `has_profile: False`, different boot id, personas still answering.

*Over a socket* (`scripts/v5_two_jars.sh` §6) — the script kills the server by PID, starts a new one, and replays the old cookie jar:

```
old cookie does not crash the new process      200
the old profile is gone                        False
the boot id changed                            145bd6f1e39b → b977c5efd962
personas still answer after restart            DEFER
```

**What is not proven: a Render redeploy.** That needs the deploy, which is P5 and is blocked on credentials. The mechanism being tested — a new process, an empty session store, a dead cookie — is identical, but a judge checking this row on the deployed URL is checking something I have not yet run. The row stays 🟠 until P5.5.

---

## 6. What this gate changed, and what it cost

**Changed:**
- `app/approvals.py` — `ApprovalGate` now accepts a per-instance `secret`. This is the actual fix: without it, every session's tokens were signed with one process-wide key, so a token minted in browser A would verify in browser B. The unit tests did not catch this because nothing had ever had two sessions.
- `interfaces/` — four new files, first real content: `session.py`, `http.py`, plus the existing `badge.py`.
- `scripts/serve.py`, `scripts/v5_two_jars.sh`.

**Cost:** the per-session key means approvals are no longer portable across a restart. They never needed to be — an approval is a seconds-long handshake, and the durable record is the reservation. `ApprovalGate`'s docstring already said this; V5 made it true.

**Still open, deliberately:** no CSRF token (the cookie is `SameSite=Lax` and every mutating route needs a token that a cross-site request cannot obtain, which covers the realistic case); no HTTPS-only cookie flag locally (Render terminates TLS, `Secure` gets added there); no account system, because there are no accounts.

---

## 7. Run it

```bash
cd product
python3 scripts/serve.py --port 8123            # or: PORT=8123 python3 scripts/serve.py
python3 -m unittest discover -s tests -q        # 110 tests
bash scripts/v5_two_jars.sh                     # the 22 checks above, against a live server
```

The script starts and stops its own server and cleans up its jars. It exits non-zero on any failure and prints the server log when it does.
