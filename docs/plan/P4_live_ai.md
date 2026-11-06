# P4 — Live AI

**Status:** ⬜ **not started** — needs `LLM_API_KEY`
**Owner:** you · **Window:** 3 Nov · **Hours:** 1.0
**Exit condition:** the UI badge reads **`AI · LLM`**, and the extraction runs against a real provider

---

## Purpose

Right now, with no key, the badge reads **`AI · LLM-MOCK`**. That is honest and deliberate — and it
is also the single most damaging thing a judge can see, because "AI is bolt-on" is the most common
failure in this field.

This phase removes the word MOCK from the recording, the legitimate way.

Serves: **Technological Implementation** + **Innovation** (AI genuinely used).

---

## P4.1 — Possession check and key (15 min)

```bash
cd 09_build/prototype && grep -c '^LLM_API_KEY=..' .env 2>/dev/null || echo "no key yet"
```

Any OpenAI-compatible endpoint works. Set in `.env`:

```
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
# optional, for non-OpenAI hosts:
# LLM_BASE_URL=https://api.openai.com/v1
```

`gpt-4o-mini` is the default because the job is extraction and tool selection — small, fast, cheap,
and good enough. Do not reach for a large model; latency in a live demo costs more than it buys.

---

## P4.2 — Validate the AI actually does both jobs (20 min)

The design has two AI jobs. Prove both, live:

**Job 1 — extraction from prose**

```bash
curl -s -X POST localhost:8000/api/extract -H 'Content-Type: application/json' \
  -d '{"text":"rent 1450 on the 28th, car loan 312 on the 20th, mum'"'"'s meds about 40"}'
```

Expect: three obligations, per-line confidence, and **the low-confidence line flagged** (the 41%-ish
one), plus `"engine":"llm"`.

**Job 2 — the agent loop with a human gate**

```bash
curl -s -X POST localhost:8000/api/agent -H 'Content-Type: application/json' \
  -d '{"persona":"dev"}'
```

Expect a trace that calls `decide_purchase`, then proposes `create_scheduled_invoice`, then **stops
at `approval_required`**. That stop is the product's ethical spine: the agent proposes, the human
approves, then it executes.

| Check | Must be true |
|---|---|
| `engine` in the response | `llm` — not `rules`, not `llm-mock` |
| Low-confidence line | Flagged for confirmation, not silently trusted |
| Agent trace | Ends at `approval_required` — it must not execute alone |
| Verdict from the model vs the engine | Identical. `explain()` discards model output on mismatch |

---

## P4.3 — Confirm the badge on screen (5 min)

Reload the page. The header must read **`AI · LLM`** (or your provider's name).

- `AI · LLM-MOCK` → the key is not being read. Check `.env` is in the working directory of the
  server process, and restart the server.
- The badge must **never** be edited in the HTML. It is derived from `describe(MODEL)`.

---

## P4.4 — Record the evidence (10 min)

In `../../09_build/prototype/README.md`, state:

- the model and provider actually used
- the date of the live extraction run
- one verbatim example of the extraction output, including the flagged low-confidence line

This is what makes "AI is used" verifiable rather than claimed.

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| Badge still `LLM-MOCK` | Key not read by the running process. Restart the server, re-check `.env` |
| Provider returns 401/429 | 401 = bad key; 429 = rate limit. Retry once. If it persists, **this is submission at risk** — escalate the same day, do not absorb it |
| Model will not tool-call reliably | Two attempts, then **keep the labelled mock** and say on camera: *"the model path is wired; here it is running scripted because [reason]"*. Judges respect this far more than a crash on video |
| Extraction is wrong on the demo sentence | Change the demo sentence, not the model. The video sentence must be one the model reliably reads |
| Tempted to hide the mock badge | **Never.** It is a named strength in every document |

**The key is mandatory.** Stage 1 requires AI that is genuinely used, and a labelled mock is not that.
`MockChat` is legitimate as a *development* mode and as a labelled demonstration — it is not an
acceptable final state for the submission. If a key genuinely cannot be obtained, say so to me
immediately; that is a risk to escalate, not a fallback to absorb.

What is never legitimate is `LLM-MOCK` on screen during a recording you describe as live.

---

## Exit criteria

- [ ] `LLM_API_KEY` set, `.env` gitignored, key never committed
- [ ] `/api/extract` returns `"engine":"llm"` with a flagged low-confidence line
- [ ] `/api/agent` trace stops at `approval_required`
- [ ] Badge reads `AI · LLM` on a page reload
- [ ] Model, provider and run date recorded in the README
- [ ] `python3 -m unittest discover -s tests` still **OK**
