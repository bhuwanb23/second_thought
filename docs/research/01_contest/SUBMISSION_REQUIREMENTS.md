# 01 — Submission requirements and the one-pager template

Source: Devpost "Requirements" + Official Rules §4–§5.

---

## The checklist

| # | Requirement | Notes |
|---|---|---|
| 1 | **Project name** | |
| 2 | **Short description** | One or two sentences. This is what most judges skim first. |
| 3 | **Thumbnail image** | Optional but affects listing click-through |
| 4 | **Demo video link** | Uploaded to YouTube/Vimeo/Youku and **public**. Judges are not required to watch past 3:00. |
| 5 | **Repository URL** | **Public**, with visible licensing. Working project required. |
| 6 | **PayPal developer tools and AI tools used** | Written out explicitly — not buried in the README |
| 7 | **Sandbox-only confirmation** | No live PayPal credentials, no real money |
| 8 | **New vs. existing project** | If it existed before 1 Oct 2026, state what changed |
| 9 | **Setup / run instructions** | Must let a judge run it during judging |
| 10 | **Availability until 15 Dec 2026 08:00 PT** | Hosted URL or reliable run path |

## The video — the highest-leverage 3 minutes

Presentation is 20% of the score, and the video is the only artefact every judge is guaranteed to consume. Structure that maps directly onto the criteria:

| Time | Content | Criterion it serves |
|---|---|---|
| 0:00–0:15 | Who this is for, and the sentence that names the pain. Real user, real number. | Impact |
| 0:15–0:35 | The problem shown, not described — the failing screen, the held funds, the denied checkout. | Impact |
| 0:35–2:20 | **The product working end-to-end, live, unedited.** Real sandbox money moving. Every screen you want scored. | Tech Implementation + Design |
| 2:20–2:45 | How it's built: the PayPal APIs by name, the agent architecture, the safety model. | Tech Implementation |
| 2:45–3:00 | Why it matters to PayPal specifically, one line. | Innovation + Impact |

Rules of thumb:
- **Record the working product, not slides.** A talking-head intro over static slides wastes the criterion the video is meant to earn.
- **Show the money move.** A PayPal sandbox transaction completing on screen is worth more than any diagram.
- **Show one failure path** — a declined authorisation, a blocked oversized payment, a rejected webhook signature. It proves non-trivial implementation.
- Never exceed 3:00. Aim for 2:40 to leave the last seconds uncut.

## README skeleton (machine-readable and human-readable)

```
# <Name>
<One sentence: what it does, for whom, using what.>

## The problem
<specific audience + sourced pain + why existing tools don't solve it>

## What it does
<numbered walkthrough matching the video>

## PayPal APIs used
- Orders v2 — AUTHORIZE / CAPTURE (files cited)
- Webhooks — signature-verified
- <each with the endpoint path>

## AI tools used
<model + framework + how they are used>

## How it works
<diagram + the deterministic/agentic boundary — say what the model is NOT allowed to decide>

## Try it
<live URL, no login> · <run locally in 3 commands>

## Tests
<paste the suite output — this is a Technological Implementation signal>

## Safety and scope
Sandbox only. No live credentials. <threat model link>

## What we'd build next
```

---

## One-pager template (per concept)

Each file in `../07_concepts/one_pagers/C06.md` follows this shape:

1. **The sentence** — one line a judge could repeat
2. **Who hurts and how much** — named audience, sourced number, evidence id
3. **What the user does** — the 5-step flow
4. **What the agent decides vs. what code decides** — the safety boundary, stated explicitly
5. **PayPal surface** — every API, with the reason it is the right primitive
6. **Why now** — the dated PayPal signal this answers
7. **Why this is not already covered** — field evidence with counts
8. **Demo script** — the 8 screens in order
9. **Judge-score self-assessment** — five criteria, honest numbers
10. **What could make this derivative** — and the escape route
