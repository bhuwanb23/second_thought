# Repository structure

Two rules, both enforced rather than intended:

1. **No file exceeds 300 lines.** Preflight fails the build if one does.
2. **One job per file.** A file that needs "and" in its name is two files.

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

| Layer | File | Lines | Job |
|---|---|---|---|
| **Engine** | `cashflow.py` | 228 | Calendars, money, balance projection. Decides nothing |
| | `engine.py` | 238 | The verdict: OFFER / DEFER / DECLINE, the safe amount |
| **AI** | `extraction.py` | 233 | Job 1 — prose into dated obligations with confidence |
| | `agentic.py` | 208 | Job 2 — agent loop, tool surface, HMAC approval gate |
| | `llm.py` | 156 | Real tool-calling model, or a labelled scripted stand-in |
| | `agent.py` | 250 | Explainer that re-reads the verdict and discards model drift |
| **PayPal** | `paypal.py` | 295 | Sandbox REST or simulated transport, one interface, labelled |
| | `paylater.py` | 160 | Resolves a verdict into an instrument, with the fulfilment rule |
| **State** | `profile.py` | 172 | Payday profile; `answer_quality` |
| | `ledger.py` | 121 | Plans we originated |
| | `session.py` | 150 | Per-visitor isolation and the three rate-limit gates |
| **Surface** | `api.py` | 246 | The JSON API — approve/execute, extraction, agent |
| | `server.py` | 239 | HTTP only: routing, cookies, limits |
| | `web/index.html` | 350 | One self-contained page, no external assets |
| **Harness** | `demo.py` | 174 | Rehearses the arc in a terminal, offline |
| | `personas.py` | — | Three shoppers, three month shapes |
| | `paylater_probe.html` | 256 | The P1 tripwire tool |

`web/index.html` is markup and inline script in one file, which is why it is allowed
to exceed the code limit — it is the deliverable, not a module.

### Why this shape

- **`api.py` vs `server.py`.** The API is testable without a socket; the transport is
  thin. That is why the session-isolation and rate-limit tests can hit either the
  function or a real `ThreadingHTTPServer`.
- **`cashflow.py` vs `engine.py`.** Representation and judgement are different jobs.
  Only `engine.py` can produce a verdict, which makes "the model never decides money"
  checkable by looking at one file.
- **`extraction.py` vs `agentic.py`.** The two AI jobs are separate, so a failure in
  one cannot be mistaken for the other on camera.
- **`session.py`** exists because a shared demo is hostile to judges (see
  [plan.md §6a](plan.md)).

---

## Tests — `../../product/tests/`

**154 tests, no third-party runtime dependencies, no network.**

| File | Covers |
|---|---|
| `test_engine.py` | Verdicts, floors, collisions, determinism |
| `test_agent.py` | Explainer cannot change a verdict |
| `test_ai.py` | Extraction, validation, token binding, forged tokens, loop bounds |
| `test_paylater.py` | Instrument resolution, eligibility parsing |
| `test_profile.py` | Payday profile, answer quality, pay-before-ship |
| `test_session.py` | **Cross-session isolation**, public surface, all three limit gates |
| `test_paypal.py` | Adapter behaviour, error paths |
| `test_integration.py` | Approve → execute, invoice date, forged amount rejected |

Two tests are worth reading before a Q&A: `test_one_visitor_cannot_change_anothers_verdict`
and `test_a_token_for_a_different_amount_is_rejected`.

---

## Rules for adding anything

- A new file needs a one-line docstring saying what it is **for**, not what it does.
- Nothing in `cashflow.py` or `engine.py` may import `llm.py` or `agentic.py`. The
  dependency arrow points one way: judgement never depends on the model.
- Any new endpoint that can call an LLM must go through `SESSIONS.allow_llm`.
- Any new public endpoint must return booleans or already-visible data only.
- Run `python3 scripts/preflight_deploy.py` before every commit — it checks the 300-line rule,
  the licence, secret hygiene, session-state hygiene and the health check.
