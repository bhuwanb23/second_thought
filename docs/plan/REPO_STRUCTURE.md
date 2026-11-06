# Repository structure

The active code follows one structural rule:

**One job per file.** A file that needs "and" in its name is two files. Modules
are kept small where practical, but line count is not a deployment gate.

```text
paypal-hackathon/
├── README.md                  # orientation, three parts, verify-in-3-commands
├── START_HERE.md              # the lock banner and where to go next
├── docs/                      # NOT the submission — working documents
│   ├── research/              # what is true, with sources (26 docs)
│   └── plan/                  # what to do by when (plan.md + P0…P7)
├── product/                   # THE ACTIVE APPLICATION
└── archive/prototype/         # FROZEN REFERENCE IMPLEMENTATION
```

---

## The code — `../../product/`

| Layer | Files | Job |
|---|---|---|
| **Domain** | `secondthought/domain/cashflow.py`, `engine.py`, `reservation.py` | Calendar projection, deterministic verdicts, and pay-before-ship state |
| **Application** | `secondthought/app/checkout.py`, `approvals.py`, `ports.py` | Quotes, proposals, HMAC approval, gateway orchestration |
| **AI** | `secondthought/ai/extract.py`, `template.py`, `agent.py` | Validated facts and model-independent decision flow |
| **Infrastructure** | `secondthought/infra/db.py`, `gateway.py`, `paypal_live.py`, `webhook.py`, `rsa.py` | SQLite, simulated/sandbox PayPal, webhook and signature verification |
| **Interfaces** | `secondthought/interfaces/http.py`, `session.py`, `screens.py`, `webhook_api.py` | WSGI routes, session isolation, browser UI, webhook endpoint |
| **Harness** | `cli.py`, `demo.py`, `demo_ai.py`, `scripts/` | Local acceptance flows, deployment checks, and rehearsal tools |

The browser page is rendered by `secondthought/interfaces/screens.py` as one
self-contained HTML response. The Pay Later probe is
`probe/v1_probe.html`.

### Why this shape

- **`cashflow.py` vs `engine.py`.** Representation and judgement are different jobs.
  Only `engine.py` can produce a verdict, which makes "the model never decides money"
  checkable by looking at one file.
- **`extract.py` vs `agent.py`.** Fact extraction and decision orchestration are
  separate, so model uncertainty cannot become a verdict.
- **`session.py`** exists because a shared demo is hostile to judges (see
  [plan.md §6a](plan.md)).

---

## Tests — `../../product/tests/`

**155 tests, no third-party runtime dependencies, no network.**

| File | Covers |
|---|---|
| `test_checkout.py` | Three outcomes, approval, reservation lifecycle, pay-before-ship |
| `test_ai.py`, `test_ai_pipeline.py` | Extraction, validation, model isolation, token binding |
| `test_http_session.py` | **Cross-session isolation**, rate limits, persistence path |
| `test_http_security.py` | Money-route protection, amount validation, health and cookie behavior |
| `test_paypal_live.py` | Sandbox adapter requests, idempotency, protocol parity |
| `test_webhook.py`, `test_rsa.py` | Signature verification, replay handling, and RSA parsing |
| `test_screens.py` | Shopper-facing plain-language output |

Two tests are worth reading before a Q&A: `test_one_visitor_cannot_change_anothers_verdict`
and `test_a_token_for_a_different_amount_is_rejected`.

---

## Rules for adding anything

- A new file needs a one-line docstring saying what it is **for**, not what it does.
- Nothing in `secondthought/domain/` may import `secondthought/ai/` or
  `secondthought/infra/`. The
  dependency arrow points one way: judgement never depends on the model.
- Any new endpoint that can call an LLM must go through `SESSIONS.allow_llm`.
- Any new public endpoint must return booleans or already-visible data only.
- Run `python3 scripts/preflight_deploy.py` before every commit — it checks the
  Render manifest, licence/secret hygiene, environment-variable contract, and health response.
