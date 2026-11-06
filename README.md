# PayPal AI Hackathon 2026 — Second Thought

A payday-aware checkout layer that sometimes says **"not yet"**. Concept locked; build complete and
tested; verification and submission in progress.

**Deadline: 12 Nov 2026, 12:00 PT = 13 Nov 01:30 IST.** Submitting **11 Nov**.

| Start here | |
|---|---|
| **[`START_HERE.md`](START_HERE.md)** | Two-minute orientation |
| **[`docs/research/07_concepts/C02_THE_IDEA.md`](docs/research/07_concepts/C02_THE_IDEA.md)** | The product, in full |
| **[`docs/plan/plan.md`](docs/plan/plan.md)** | The master plan: eight phases, exit conditions, unverified register |
| **[`docs/plan/LOCK.md`](docs/plan/LOCK.md)** | What is frozen, and the two tripwires |
| **[`docs/plan/REPO_STRUCTURE.md`](docs/plan/REPO_STRUCTURE.md)** | How the code is laid out, and why |
| **[`product/`](product/)** | The active application — 154 tests, no third-party runtime dependencies |

---

## Structure

This workspace has three parts, and they do not overlap:

| Part | What it is | Why it is separate |
|---|---|---|
| **[`docs/research/`](docs/research/)** | Rules, intent, field scan, evidence of pain, API capability, sponsors, concepts | Records **what is true**, with sources. Internal — not the submission |
| **[`docs/plan/`](docs/plan/)** | Master plan, eight phase documents, lock, decisions, submission kit | Records **what to do by when** |
| **[`product/`](product/)** | The canonical working product, its tests and Render config | **This is the active application** |
| **[`archive/prototype/`](archive/prototype/)** | The earlier implementation | Frozen reference only; not deployed |

`docs/README.md` explains the split in more detail.

---

## The product in four lines

1. At the moment Pay Later would be offered, **project the shopper's next 45 days**.
2. **Offer** it if it fits. **Reserve it for payday** if it fits but not today — and the merchant
   ships only after payment (*pay before ship*; no merchant credit).
3. **Decline to surface credit** if it collides with rent, name the bill and date, and quote the
   **safe amount** that would fit.
4. The AI reads the shopper's own words and drives the actions; a deterministic engine makes every
   decision about money; a human approves any money movement.

**PayPal pays for it — the shopper benefits, the merchant embeds it.**

---

## Verify it in three commands

```bash
cd product
python3 -m unittest discover -s tests -q     # 154 tests … OK
python3 scripts/preflight_deploy.py          # deployment configuration checks
python3 -m secondthought.cli                # three shoppers, three verdicts
```

Then: `python3 scripts/serve.py` and open `http://localhost:8000`.

The full architecture is documented in [`docs/architecture/`](docs/architecture/).
The historical prototype is preserved in [`archive/`](archive/).

---

## Honesty rules that do not bend

- **The mode badge is never faked.** No key → `AI · LLM-MOCK`. No credentials → `SIMULATED`. Both are
  named strengths, not embarrassments.
- **The model never decides money.** Verdicts, amounts and dates come from an integer-cent engine.
- **Every claim has a source.** Three claims were cut during review for being outdated or overstated;
  they are listed in `docs/research/README.md`.
- **Sandbox only.** No live credentials, no real money.
- **"Researched", not "validated"** — until real shoppers have been asked.

---

## Timeline

| Date | Work |
|---|---|
| 2 Nov | **Pay Later probe** (closes tripwire 1) · start conversations |
| 3 Nov | Live AI key; conversations continue |
| 4 Nov | Conversations close; deploy to Render |
| 5 Nov | AG Grid decision, written down |
| 9 Nov | **Feature freeze** |
| 10 Nov | Record the 2:40 video |
| 11 Nov | **Submit** |

Full detail: [`docs/plan/plan.md`](docs/plan/plan.md)
