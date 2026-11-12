# PayPal AI Hackathon 2026 — Second Thought

Second Thought is a payday-aware checkout layer that sometimes says **“not yet.”** It projects a
shopper’s next 45 days before offering Pay Later, then gives a deterministic, explainable verdict:
offer today, reserve for payday, or decline with a safer amount.

The canonical application is in [`product/`](product/). The earlier prototype is preserved in
[`09_build/prototype/`](09_build/prototype/) for reference and is not deployed.

## Start here

| Resource | Purpose |
|---|---|
| [`START_HERE.md`](START_HERE.md) | Two-minute orientation |
| [`product/README.md`](product/README.md) | Product setup, architecture, API, and validation |
| [`product/SECURITY.md`](product/SECURITY.md) | Implemented controls, threat model, and known limitations |
| [Live demo](https://second-thought-h61b.onrender.com) | Free Render deployment; may sleep after inactivity |
| [Live proof page](https://second-thought-h61b.onrender.com/proof) | Measured local/deployment evidence |
| [`assets/demo/`](assets/demo/) | Judge-ready demo video, poster, and YouTube upload notes |
| [`docs/research/07_concepts/C02_THE_IDEA.md`](docs/research/07_concepts/C02_THE_IDEA.md) | Product concept and rationale |
| [`docs/plan/plan.md`](docs/plan/plan.md) | Master plan and verification register |
| [`docs/plan/REPO_STRUCTURE.md`](docs/plan/REPO_STRUCTURE.md) | Repository layout and ownership |

## Repository structure

| Part | Purpose |
|---|---|
| [`product/`](product/) | Active application, tests, deployment configuration, and runtime docs |
| [`assets/demo/`](assets/demo/) | Clean shareable media for the submission |
| [`docs/research/`](docs/research/) | Research, evidence, and sourced product decisions |
| [`docs/plan/`](docs/plan/) | Delivery plan, decisions, and submission materials |
| [`09_build/prototype/`](09_build/prototype/) | Frozen earlier prototype; reference only |

## Verify the product

```bash
cd product
python -m unittest discover -s tests -q
python scripts/preflight_deploy.py
python -m secondthought.cli
python scripts/serve.py
```

Open `http://localhost:8000` after starting the server. The full architecture and API details are
documented in [`product/README.md`](product/README.md).

## Product principles

- The mode badge is honest: simulated mode is explicit, and sandbox mode is never presented as
  production.
- The model interprets shopper language; the deterministic engine decides money, dates, and verdicts.
- PayPal calls are sandbox-only. No live production credentials or real money are used.
- Every financial action is explainable and requires the appropriate user confirmation.

## Demo video

The submission-ready package is in [`assets/demo/`](assets/demo/):

- [`second-thought-demo.mp4`](assets/demo/second-thought-demo.mp4) — 60-second, 1920×1080 MP4 with
  narration, music, and UI sound design.
- [`second-thought-poster.jpg`](assets/demo/second-thought-poster.jpg) — poster frame for YouTube.
- [`README.md`](assets/demo/README.md) — upload title, description, chapter notes, and checklist.

Upload the MP4 to YouTube as **Public** or **Unlisted** with no password. Only the first three
minutes are reviewed; this cut is intentionally well below that limit.
