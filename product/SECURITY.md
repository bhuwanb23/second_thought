# Security model

Second Thought is a hackathon prototype, not a formal security audit. This
document describes the controls that are implemented and the limits that remain.

## What is protected

| Concern | Control | Implementation |
|---|---|---|
| Session isolation | Signed, HttpOnly session cookie; each session has its own approval key | `secondthought/interfaces/session.py` |
| Money approval | Single-use HMAC token bound to the exact tool and arguments, with expiry | `secondthought/app/approvals.py` |
| Replay and tampering | Used tokens are rejected; changing the amount, tool, or arguments invalidates the signature | `tests/test_checkout.py`, `tests/test_http_security.py` |
| Model abuse | Model-backed extraction is rate-limited per session and IP, with a call budget | `secondthought/interfaces/session.py` |
| Webhook forgery | Raw-body PayPal webhook signatures are checked with RSA-SHA256 and an allow-listed certificate host | `secondthought/infra/webhook.py`, `secondthought/infra/rsa.py` |
| Duplicate payment events | Webhook/payment handling is idempotent | `secondthought/domain/reservation.py`, `secondthought/infra/db.py` |
| Secret exposure | Secrets are environment variables; health and diagnostics responses are redacted or token-gated | `secondthought/config.py`, `secondthought/interfaces/badge.py` |
| Production payments | The PayPal adapter accepts Sandbox only and refuses `PAYPAL_ENV=live` | `secondthought/infra/paypal_live.py` |

## Threats deliberately tested

The test suite and `scripts/v5_two_jars.sh` cover foreign-session cookies,
approval replay, altered approval arguments, unknown money tools, rate-limit
boundaries, missing webhook signatures, malformed signatures, and duplicate
payment notifications. The preflight checks also scan configuration for
committed secrets and verify that the application binds to Render's `PORT` on
`0.0.0.0`.

Run the checks from `product/`:

```bash
python -m unittest discover -s tests -q
bash scripts/v5_two_jars.sh
python scripts/preflight_deploy.py
```

## Known limitations

- This is a prototype with in-memory sessions. A restart or redeploy logs users
  out; the configured SQLite data is not presented as durable storage.
- The browser demo uses simulated payments by default. Sandbox credentials are
  opt-in and must never be replaced with production credentials.
- The model reads free text but cannot decide money, approve an action, or call
  PayPal. Low-confidence or unusable extraction must be confirmed or rejected.
- Certificate fetching is restricted to PayPal hosts, but deployment still
  requires normal outbound-network and TLS controls.
- There is no collections service. A deferred reservation can expire or be
  released without shipment; a merchant must provide the human hardship or
  support path. `fulfil()` cannot run until payment is recorded.
- No formal penetration test, production threat assessment, or user study has
  been completed.

Report a reproducible security issue through the repository owner rather than
including credentials or personal payment data in an issue.
