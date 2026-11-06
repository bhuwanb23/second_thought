# 01 — Rules, dates and eligibility

Source: Devpost listing + Official Rules §1–§8 (retrieved 1 Nov 2026). Verified against the live listing.

---

## Key dates

| Event | Date | Your local time (IST) |
|---|---|---|
| Submission period opens | Thu **1 Oct 2026**, 9:15 am PT | 1 Oct, 21:45 IST |
| **Submission deadline** | Thu **12 Nov 2026**, 12:00 pm PT | **13 Nov, 01:30 IST** |
| Judging period | Tue 1 Dec 2026, 2:00 pm PT → Tue 15 Dec 2026, 8:00 am PT | 2 Dec 03:30 → 15 Dec 21:30 IST |
| Winners announced | on/around Mon **21 Dec 2026**, 2:00 pm PT | 22 Dec, 03:30 IST |

Devpost displays the deadline as "Nov 12 @ 3:00pm EST" — that is the same moment (12:00 pm PT). **Trust the PT time in the rules.**

**Two timing rules that are easy to miss:**
1. Edits lock at close. README, video link, repo and description must be final by 12 Nov 12:00 PT.
2. Your **project must stay available free of charge until the judging period ends (15 Dec 08:00 PT)**. A hosted demo or run instructions that break in December fail the requirement.

---

## Eligibility

**Open to:** individuals at the age of majority in their country, teams of eligible individuals, and organisations. One Representative per team/organisation enters the submission.

**Not open to:** residents of or organisations domiciled in Brazil, Quebec, Russia, Crimea, Cuba, Iran, North Korea, or any comprehensively OFAC-sanctioned country. Employees/agents of PayPal and Devpost, judges, and their immediate families/households. Projects that received financial or preferential support from PayPal or Devpost.

**India is eligible.** All materials must be in English.

---

## What you must build

> "Build or update an application that integrates the **PayPal developer platform** (using the free **sandbox** environment) along with an **AI tool, model, or platform** of your choice."

- PayPal scope explicitly includes **Venmo, Braintree, Xoom, Honey, Zettle, Paidy, Hyperwallet, Simility, Swift Financial**.
- Sponsor tools are optional. Any AI tool is fine, **as long as PayPal integration is central**.
- Projects can be **new or existing** — existing ones must show meaningful progress **after 1 Oct 2026**, and you should explain what changed.
- Must be "capable of being successfully installed and running consistently on the platform for which it is intended", and must function as depicted in the video and description.
- Third-party SDKs/APIs must be used within their terms.

---

## Multiple submissions

Allowed — but each must be **unique and substantially different**. Realistically only worth doing with a second person, and each needs its own repo, video and description.

---

## IP and ownership

- Your submission stays your IP. PayPal gets a non-exclusive licence to use it for judging, and a right to promote it and your name/likeness for 3 years.
- Must be your original work, solely owned by you, not infringing anything.
- Open source components are fine if you comply with their licences and add meaningful functionality on top.

---

## What disqualifies people in practice

Observed in the 549-repo field scan and confirmed against the rules:

| Risk | Evidence |
|---|---|
| **No licence visible in the repo About section** | **17% of scanned repos have no detectable licence.** A `LICENSE` file is not enough — GitHub must detect it and show it in About. |
| Mockup instead of a working build | Explicitly stated as not meeting the requirement |
| Video over 3 minutes, or unlisted | Judges are not required to watch past 3:00 |
| Secrets committed | Run a scanner before the final push |
| Demo dead during judging | Requirement runs to 15 Dec |
| PayPal used decoratively | Stage 1 is pass/fail on "reasonably applies the required APIs" |
