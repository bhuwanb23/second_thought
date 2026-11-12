# P6 — Polish & freeze

**Status:** ⬜ **not started**
**Owner:** you + agent · **Window:** 5–9 Nov · **Hours:** 8.0
**Exit condition:** AG Grid decided in writing · README final · **feature freeze 9 Nov**

---

## Purpose

This is the phase where projects either gain the last five Design points or lose the whole thing to
scope creep. The rule: **after 5 Nov you are not adding capability, only clarity.**

Serves: **Design** (20%) and protects the tiebreak (**Technological Implementation**).

---

## P6.1 — AG Grid: in or out, decided 5 Nov, written down (60 min)

**Default: OUT.** Take it only if all four are true:

- [ ] It can be done in **≤3 hours** without touching the engine or the API
- [ ] It is used **genuinely** — a real balance-curve grid with real projected data, not a bolt-on table
- [ ] It does not break any of the 103 tests
- [ ] It leaves ≥4 h of slack before the freeze

If AG Grid requires React + Studio Agent Framework to be *judgeable* as a sponsor integration, the
honest answer is out: a half-integration earns no prize and risks the demo. Prize: $10,000 / 5
places — but only for an integration a judge would call genuine.

**Write the decision and the reason in `DECISION_LOG.md`,** whatever it is. An undocumented decision
reads as an oversight; a documented "out" reads as judgement.

---

## P6.2 — APIMatic (10 min)

**Out.** Not free, and an unused sponsor tool earns nothing. Note it once in the DECISION_LOG next
to AG Grid. Do not revisit.

---

## P6.3 — README final pass (120 min)

The README is read by a machine as well as a human — automated analysis is explicitly permitted, so
**literal API names must appear**.

- [ ] One-sentence pitch above the fold
- [ ] **Tools used** section: `Orders v2`, `AUTHORIZE`, `Invoicing v2`, `Webhooks`,
      `Transaction Search`, `OAuth2`, the JS SDK v6 eligibility call, and the model name — spelled out
- [ ] The three verdicts with the three real personas and their numbers
- [ ] **Live vs simulated matrix** — the mode badge explained as a strength
- [ ] Setup in ≤5 commands, verification with `preflight.sh`
- [ ] Sandbox-only statement: **no live credentials, no real money**
- [ ] New project, started after 1 Oct 2026
- [ ] The approval-gate test named explicitly (`test_forged_amount_token_is_rejected`)
- [ ] Every statistic carries a source and a date; the 1.83% charge-off counterweight is present
- [ ] Screenshot of the real sandbox invoice from P3.3
- [ ] Data & privacy line, linking `DATA_AND_PRIVACY.md`

---

## P6.4 — Repo shape decision (20 min)

Assumption **A2** keeps the code at `../../09_build/prototype` and pushes *that folder* as the repo.
Revisit only if all of these hold:

- [ ] Promotion to repo root is done by **file move only** (no code edits)
- [ ] `render.yaml` still resolves and the deploy is re-verified after the move
- [ ] The clean-clone test (P5.5) still passes

Otherwise: keep A2 and change nothing. A judge who opens a repo with a clear README and a working
build does not penalise a folder name.

---

## P6.5 — Claims and compliance sweep (60 min)

Go through every judge-visible word. **Any claim without a source gets deleted, not softened.**

| Check | Rule |
|---|---|
| Every statistic | Has a source and a date, or is removed |
| Credit-bureau claim | **Absent** — it was removed as outdated; do not let it back in |
| "Volume preserved" | **Absent** — replaced by the stated trade |
| "Validated" | **Absent** — "researched", or "tested with n shoppers" per P2 |
| 549 repos | **Internal only.** Registrants are not submissions; it is not evidence for a judge |
| Pay Later wording | Matches what P1 actually returned |
| AI claims | Match what P4 actually ran |
| Live claims | Match what P3 actually verified |
| Sandbox confirmation | Present and unambiguous |
| Trademarks | No PayPal logo, no implied endorsement, generic personas |

Then:

```bash
cd 09_build/prototype && bash scripts/preflight.sh && python3 -m unittest discover -s tests -q
```

---

## P6.6 — Polish within the freeze (rest of the window)

Only these, in this order, stopping when time runs out:

1. **Empty and error states** — a judge will click something unexpected
2. **One consistent visual pass** — spacing, colour, type; nothing new
3. **The balance curve** — the single most legible artefact in the demo; make it readable at 1080p
4. **Loading states** on the extraction and agent cards
5. The `answer_quality` line — make sure it is impossible to miss

**Banned after 5 Nov:** new endpoints, new personas, new APIs, framework changes, refactors,
"while I'm here" edits to `engine.py`.

---

## P6.7 — Clean-clone test, on a clean machine (20 min)

The P5.5 clone test ran on your own machine, which has your Python, your shell profile and possibly
your environment. Repeat it somewhere that has **none of it** — a fresh container, a VM, or a
different computer:

```bash
docker run --rm -v "$PWD":/w -w /w python:3.11-slim sh -c \
  "python3 -m unittest discover -s tests -q && python3 demo.py | tail -5"
```

No `.env`, no network. If a judge clones it and it needs a credential to pass its own tests, that is a
failed submission, not a rough edge.

## P6.8 — Feature freeze, 9 Nov

- [ ] Tag the repo (`v1.0-submission`)
- [ ] `git status` clean
- [ ] Last full run: tests **OK**, preflight **ALL CHECKS PASSED**, demo rehearsed end to end
- [ ] Freeze noted in `DECISION_LOG.md`
- [ ] Clean-clone test repeated in a container with no inherited environment (P6.7)

**After the freeze, only these may change:** a broken link, a typo, a secret leak, or a demo that
will not start. Nothing else — and each change gets re-verified with the full test suite.

---

## Failure modes → pre-committed response

| Symptom | Response |
|---|---|
| Behind on 6 Nov | Cut in the [ladder](plan.md#6-contingency-ladder--what-gets-cut-in-this-order) order: AG Grid → polish items. Never cut the README |
| Tempted to add a feature on 7 Nov | The feature is not the submission. The *recorded proof* is |
| AG Grid half-done on 8 Nov | Revert it. A broken sponsor integration is worse than none |
| Tests fail during polish | Stop. Fix or revert. A red suite at freeze is unacceptable |
| Someone suggests a framework rewrite | No. The prototype is working, tested and small — that is the asset |

---

## Exit criteria

- [ ] AG Grid and APIMatic decisions written in `DECISION_LOG.md`, with reasons
- [ ] README passes every row of P6.3
- [ ] Claims sweep complete; no unsourced number survives
- [ ] Sandbox-only confirmation present
- [ ] `v1.0-submission` tagged, working tree clean
- [ ] Feature freeze recorded
