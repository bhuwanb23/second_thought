# Research Framework — PayPal AI Hackathon 2026
### A repeatable funnel for turning 549 competitors and a vague brief into one defensible idea

**How to use this document.** It is the method. The instruments it references are:
- `RESEARCH_WORKBOOK.xlsx` — 9 sheets, pre-filled with everything established on 1 Nov 2026
- `tools/scan_field.py` — re-runnable competitor scanner (writes `03_field/METHOD.md/`)
- `DOSSIER.md` — the facts: rules, prizes, judging, PayPal surface area, submission checklist

Run the phases in order. Do not skip Phase 1 — it is the phase everyone skips, and it is the one that answers your actual question.

---

## 1. The premise

A hackathon is not a school assignment with a rubric. It is **a company paying money to see something it has not managed to build itself.** The rubric is written after the intent. So the winning question is never "what's a cool use of PayPal + AI?" It is:

> **What can PayPal not build themselves right now, that they would recognise instantly if a stranger built it in ten days?**

That question has a discoverable answer, because PayPal talks about its own gaps constantly — to investors, at conferences, in its changelog. Your instinct that "they genuinely need something specific" is correct, and it is *documented*. Section 6 states it.

### The three failure modes this framework exists to prevent

| Failure | What it looks like | Cost |
|---|---|---|
| **Innovator's bias** | You fall in love with the first idea that feels clever and spend the research phase confirming it | 11 days on a 549th clone |
| **Analysis paralysis** | "Research" that never converges because there is always one more source | Miss the deadline, or decide on day 9 |
| **Reading the brief literally** | Optimising for the words on Devpost ("build an agent, an app…") which are deliberately open | Build something generic because the brief was generic |

The framework forces convergence: every phase has a **gate** and a **time box**. If you miss a gate, you cut scope, not the schedule.

---

## 2. The model: what actually makes an entry win

Judging is five criteria at equal weight, then a tie-break on the first one. But *winning* is a different equation, because you are also competing for attention against a large field:

```
        Judge score (0–5, equal-weight average)
        × Crowding factor   — how many near-duplicates the judge has already seen
        × Intent factor     — how directly it answers what PayPal asked for
        × Feasibility       — can one person finish and demo it
        = Expected value
```

| Term | Weight in practice | Why |
|---|---|---|
| **Judge score** | Essential but not sufficient | Most competent entries land 3.5–4.2. Ties are common; the tiebreak is Technological Implementation |
| **Crowding factor** | **The most under-priced term** | Judge #4 who has seen 30 mandate-wrapped shopping agents scores yours lower no matter how good it is. Novelty is not a bonus, it is a discount on everyone else |
| **Intent factor** | High, and asymmetric | A project that answers the CEO's stated priority gets read charitably. A project that doesn't gets read as "generic hackathon entry" |
| **Feasibility** | Binary in effect | An unfinished brilliant idea scores zero. A finished good idea scores. |

**Live formula used in the workbook:**

```
EV = (JudgeScore/5) × CrowdingFactor × IntentFactor × (Feasibility/5) × 100
where  CrowdingFactor = 1 / (1 + competing_entries / 15)
       IntentFactor   = 0.6 + 0.1 × intent_fit
```

The crowding divisor of 15 is deliberately harsh. At 86 competitors the factor is 0.149 — you would need to be *five times* better than a green-space idea to draw level. That reflects how judging actually feels, not how entrants imagine it.

**The one legitimate way to beat a crowded cluster:** win on *segment*, not concept. "A mandate-based shopping agent" is the 87th. "Mandate-based procurement for dental practices ordering consumables, where the practice manager must approve each order" is the first. Judges cluster by headline; differentiate in the noun.

---

## 3. The funnel — seven phases

```
   PHASE          QUESTION                                    OUTPUT                        GATE
   1  Intent      What is PayPal asking for?                  Intent signal log (24)        ≥5 signals at strength 4+
   2  Field       Who already answered it?                     Cluster density map           know your 3 nearest rivals
   3  Pain        Does a real audience hurt?                   Pain ledger                   ≥5 rows, ≥3 quantified
   4  Capability  What is technically unclaimed?               Capability gap matrix         2–3 products, 1 under-used
   5  Generate    What are the candidate answers?              Concept pipeline (24+)        ≥20 candidates, deduped
   6  Score       Which one survives?                          EV ranking + gate sheet       top 3 pass all Stage-1 gates
   7  Red team    How will a judge dismiss it?                 Kill/keep decision            no unexplained kill criteria
```

Time box for the whole funnel: **2 days.** You have 11. Research that runs longer than that is procrastination wearing a lab coat.

---

### Phase 1 — Intent archaeology
**Question:** what is PayPal demonstrably asking for?
**Time box:** 3 hours. **Instrument:** `01_Intent_Signals` (24 rows already filled).

**Source hierarchy — respect it.** A shipped product or a CEO's unscripted answer outranks a press release, which outranks a blog, which outranks a third-party summary. Most entrants only read the last tier.

Tier 1 — primary, dated, hard to fake:
- **Earnings call transcripts** (last 2 quarters). The Q&A section is worth more than the prepared remarks: analysts ask "what's actually working", and executives answer candidly. This is where you find admissions of weakness.
- **`developer.paypal.com` pages and their "Last updated" stamps.** What was touched in the last 60 days is what's being pushed. (`ai-tools/agent-tools` was updated 29 Oct 2026 — three days before this research.)
- **Conference talks by named product owners** (GTC, Ai4, Google Cloud Next). A CTO demoing an internal tool is the strongest possible signal: they built it themselves, which means they want it.
- **Developer changelogs / new endpoints** — the diff of what appeared this year.

Tier 2 — curated narrative: PayPal Newsroom, developer blog, investor day decks, the acquisition history (what they bought = what they can't build).

Tier 3 — signal about the *competition*: the hackathon's own design. Read the award names as a rubric. **Only one of the five honourable mentions is product-specific: "Best Use of Agentic Commerce."** That is not decoration; it is the one thing they chose to name.

Tier 4 — corroboration only: trade press, analyst summaries, SEO blog posts. Useful for dates and numbers, never for interpretation.

**Method — the "said it out loud" test.** A signal earns strength 5 only if a PayPal executive or an official doc states the need in their own words. Strength 4 = a shipped product or partnership implies it. Strength 3 = pattern across several sources. Anything below 3 does not get to influence a decision.

**Gate:** at least five strength-4+ signals that point at the same *area*. If your signals scatter, you have not read enough.

---

### Phase 2 — Field mapping
**Question:** who already answered it, and how well?
**Time box:** 30 min setup, then 5 min/day. **Instrument:** `tools/scan_field.py` → `02_Field_Map`.

The Devpost gallery is unpublished, but entrants publish repos. Today's scan: **549 public repos**, classified into 22 concept clusters with a 13-marker depth score.

```
python3 tools/scan_field.py          # full scan, ~90s, writes a dated snapshot
python3 tools/scan_field.py --diff-only
```

Run it daily until submission. Two things change fast: the count (the field is growing ~20–35 repos/day) and the tail (someone may enter your lane late — better to know on day 6 than on day 12).

**What to extract, in order of value:**
1. **Density per cluster** — where the crowd is.
2. **Average depth per cluster** — where the *good* competitors are. Disputes averages 4.9/13; shopping-agent averages 2.3/13. A crowded-but-shallow cluster is more attackable than a crowded-and-deep one.
3. **The top 10 repos by depth** — read them. Not to copy: to know exactly what "state of the art" looks like, so you can be visibly past it.
4. **The disqualification rate** — 17% of repos have no licence. That is your competition's hygiene level.

**Gate:** you can name the three closest repos to your concept and state, in one sentence each, precisely how you differ. If you cannot, you are not differentiated — you are hopeful.

---

### Phase 3 — Pain evidence
**Question:** is there a real audience with a documented, quantified problem?
**Time box:** 3 hours. **Instrument:** `04_Pain_Ledger`.

"Impact" is 20% of the score, and judges are explicitly told to check whether *"the solution actually addresses that problem based on what's demonstrated."* Invented personas lose to sourced ones.

**Where the evidence actually is** (best first):
1. **PayPal Community forums** — users describing failures in their own words, searchable by product.
2. **CFPB Consumer Complaint Database** — public, dated, filterable by company. Cluster the narratives and you have a quantified, citable pain.
3. **App Store / Play Store reviews** of PayPal, Venmo, Xoom, and Braintree-powered apps, sorted newest.
4. **G2 / Capterra** reviews of PayPal Braintree and rival PSPs — merchants describe what they wish existed.
5. **Reddit** — r/freelance, r/smallbusiness, r/ecommerce, r/paypal. Unprompted, therefore credible.
6. **PayPal's own job postings** for AI/commerce roles — a company hires for what it cannot yet do.
7. **World Bank / BIS / CFI** for the social-impact angle, when you need a global number.

**Gate:** ≥5 ledger rows, ≥3 with a number attached (a count, a cost, a rate), and you can say the audience in one sentence with a size and a geography.

---

### Phase 4 — Capability inventory
**Question:** which parts of the platform are technically unclaimed?
**Time box:** 1 hour. **Instrument:** `03_Capability_Gap`.

This is where you buy Technological Implementation — 20% of the score **and the tiebreaker**. It is also the cheapest differentiation available, because it is measurable: 3% of the field uses Subscriptions, 9% uses AUTHORIZE-then-capture, 0% uses the Donations SDK, 1% uses JS SDK v6.

**Rule:** pick 2–3 PayPal capabilities, at least one from the under-10% band, and make sure at least one is *visibly* on screen during the demo. Depth that only exists in the README scores nothing.

**Checklist for technical depth a judge can verify in 60 seconds:**
- [ ] Server-side OAuth (client_credentials), not a hardcoded token
- [ ] Webhook endpoint with **signature verification** (26% of the field bothers)
- [ ] Idempotency keys on create/capture
- [ ] A state machine — order status comes from events, not from polling in a loop
- [ ] Error, retry and void paths (what happens when capture fails?)
- [ ] Sandbox credentials in env vars, `.env.example` committed, nothing leaked
- [ ] An explicit "PayPal APIs used" table in the README

---

### Phase 5 — Structured generation
**Question:** what are the plausible answers?
**Time box:** 2 hours. **Instrument:** `05_Concept_Pipeline` (24 pre-scored; add your own).

Do not brainstorm free-form. Brainstorming produces what you already know. Use **combinatorial forcing** — take one item from each column and write the sentence:

| Pain (from P-ledger) | × Audience (specific) | × PayPal primitive (from gap matrix) | × AI capability | → Concept |
|---|---|---|---|---|
| can't prove authorisation | × dental practice manager | × AUTHORIZE + Mandate | × document parsing | × "approval evidence for supply orders" |

Generate 30. Discard 20 immediately as obvious (cross-check against `08_Anti_Lame`). Score the remaining 10.

**The anti-lame rule:** if the concept appears in `08_Anti_Lame` — the twelve ideas that arrive first because they are the ones everyone had — it is not automatically disqualified, but you must write the sentence *"this is different because ____"* and that sentence must survive Phase 7. "Better UX" and "better execution" are not differences. Segment, primitive, or business model are.

---

### Phase 6 — Gates and scoring
**Question:** which survives contact with the rules?
**Time box:** 1 hour. **Instrument:** `06_Gates` + the EV column.

Two kinds of gate, applied in this order:

**Hard gates (binary, from Stage 1 of judging).** Fail any → discard regardless of score.
1. PayPal usage central — removing it breaks the product
2. AI doing real work — a model reads unstructured input or makes a decision
3. Runs end-to-end in sandbox — create → approve → capture → webhook → confirm
4. No dependency on gated access (Store Sync approval, ACP credentials, production)
5. Demoable without a licence that could expire before 15 Dec

**Scored gates (the five criteria, scored 1–5 as a judge would).** Then apply the EV formula. Rank.

**Tie-break rule, imported from the actual rules:** when two candidates are within 3 EV points, choose the one with the higher **Technological Implementation** score — because that is the official tiebreaker. This is not a stylistic preference; it is how the contest resolves ties.

---

### Phase 7 — Red team, then freeze
**Question:** how will a judge dismiss this?
**Time box:** 1 hour. **Instrument:** `06_Gates` (red-team prompts).

Run these five prompts, verbatim, against your top concept, ideally with a different model than the one you built with:

1. "You are a PayPal product manager judging this hackathon. Here is the concept and the video script. Write the three sentences you would put in your scoring notes to justify a low score."
2. "List every way this product could *appear* to use PayPal meaningfully while actually being superficial."
3. "What is the most likely way this demo fails live?"
4. "Which existing repo would a judge treat as a near-duplicate?"
5. "Say my one-line pitch back to me as a sceptic. If it sounds generic, say so."

**The final test — the 15-second rule.** Write the opening line of the video and the first two sentences of the Devpost description. Give them to someone with no context. If they cannot repeat back *what it does and who it's for*, the concept is not ready — regardless of your score.

Then **freeze and log it** in `07_Decision_Log`. On day 8, when you are tired and doubting, the log is the difference between finishing and restarting.

---

## 4. Decision rules (pin these above your desk)

1. **Crowding beats cleverness.** A 4.2-quality idea in a green cluster outranks a 4.8 in a red one. The formula says so and the judges behave that way.
2. **One main award, one sponsor pool.** Target no more than two named prizes. Multiple sponsor tools do not multiply prizes — they only multiply eligibility while dividing attention.
3. **Depth must be visible.** If a technical achievement doesn't appear on screen during the demo, it scores only in the README — assume half credit.
4. **Never enter a red cluster without a segment wedge.** "For [specific job title] doing [specific task]" is the only accepted wedge.
5. **Feasibility is not a soft score.** An unfinished idea scores zero; a finished adequate one scores. When in doubt, cut the feature, not the deadline.
6. **Ties go to Technological Implementation.** It is the official tiebreaker; optimise for it over Design when they conflict.
7. **The last two days belong to artefacts** — README, licence, video, description. These are 20% of the score and the most common cause of total failure.

---

## 5. Research failure modes to watch in yourself

| Symptom | What's really happening | Fix |
|---|---|---|
| "Let me check one more competitor repo" | Avoiding the decision | Hard stop at the gate count; the field will look different by the deadline regardless |
| Falling for an idea in Phase 1 | Innovator's bias | Score it *first* in the pipeline, before you have feelings about it |
| Everything scores 4/5 | You are scoring your preferences, not a judge's | Re-score with the `06_Gates` red-team prompts in front of you |
| Wanting to combine three ideas | Fear of committing | Combining is how hackathon projects die at 60% |
| Research feels productive on day 4 | It is not, any more | Phase 1–4 = 2 days total. After that, build |

---

## 6. The answer, as of 1 Nov 2026

You asked what they are waiting for. Here is the evidence-backed answer, and it is narrower than the brief suggests.

### 6.1 PayPal's own stated problem, in three sentences

1. **The CEO says their role in agentic commerce is trust, not checkout.** Lores, Q3'26 call: *"both will have to validate that this is a real consumer that can pay, this is a real merchant that has the product… it's really all about trust and about the security."*
2. **The CEO says their own services are under-attached and under-monetised.** Lores, same call: *"Services like payouts or risk as a service or invoicing… either we have not been able to attach them properly, or we have not been able to monetize them properly. That's going to be a key priority."*
3. **The CTO built the missing tool himself.** Venkatesan, Ai4, Aug 2026: a **Merchant AI Integration Agent** that reads a merchant's codebase, upgrades, validates and certifies its PayPal integration — *weeks to hours*.

Read those together. PayPal's strategic problem in late 2026 is not "can an agent buy something" — they have shipped that (Copilot, Perplexity, Glance, Meta's Muse, ChatGPT via ACP, Google via UCP). Their problem is the **boring layer around it**: proving each agent transaction is legitimate, getting small merchants technically ready, and attaching the services that actually earn margin.

### 6.2 Where that intersects the empty field

The field has run to the loud part of the brief. 549 repos, and the density is: mandates/guardrails **86**, invoicing/AR **60**, reconciliation **51**, disputes **49**, shopping agents **47**, agent trust **38**.

Meanwhile: merchant-integration tooling **2**, BNPL/credit **3**, nonprofit/donations **5**, agriculture **6**, a2a **9**, remittance **1**, education **1**.

### 6.3 The top of the EV ranking today

From `05_Concept_Pipeline` (24 candidates scored; EV = judge score × crowding × intent × feasibility):

| Rank | Concept | Cluster count | Intent | EV | Why it ranks here |
|---|---|---|---|---|---|
| **1** | **C01 — Merchant PayPal-integration doctor**: reads a store/repo, finds the PayPal integration, upgrades it to SDK v6 + Orders v2, validates in sandbox, issues a certification report | 2 | 5 | **68.3** | Answers signal S08 (the CTO literally built this internally), highest tech-implementation ceiling → wins the tiebreak, near-empty cluster, and demos brilliantly: broken integration in, certified integration out |
| **2** | **C02 — BNPL decision agent**: decides at checkout whether Pay Later genuinely helps *this* buyer, with affordability evidence | 3 | 5 | **61.6** | Financial services = 20% of PayPal's transaction margin and double-digit growth (S04), and only 3 entries touch it. Low build cost |
| **3** | **C24 — Open-source PayPal MCP extension** for Invoicing/Payouts/Subscriptions with policy enforcement | 2 | 4 | **53.6** | Deep, credible, tiny field. Weakness: dev-tool aesthetics |
| **4** | **C06 — Goal-bound family remittance** (voice note → itemised needs → verified bills → split payment) | 1 | 3 | **48.6** | Highest raw judge score (Impact 5, Innovation 5), empty lane. Weakness: intent fit is only 3 |
| **5** | **C08 — Nonprofit field-payout agent** using the Donations SDK (0% usage) + Payouts | 5 | 3 | **45.4** | Their own "social impact" category is underserved; two under-used products |

**The honest tension in this ranking.** C01, C02 and C24 win on *odds and intent*; C06 and C08 win on *judging score*. That is the real strategic choice, and it is a choice about who you are as a builder:

- If you are strong technically and can build a polished console: **C01** is the highest-EV idea on the board, and nobody expects a dev tool from a hackathon — which is exactly why it will be remembered in a room of 549 shopping agents.
- If you are strong on story, design and video, and the product needs to make a judge *feel* something: **C06** scores 4.8/5 against the five criteria and sits in an empty lane, but you must accept weaker intent fit and a harder regulatory framing.

Both are defensible. What is not defensible is entering the mandate/shopping lane at rank 23.

### 6.4 What is still unverified — do this before you commit

The funnel is complete except for Phase 3, which needs primary data I cannot gather from here:

1. **Fill the pain ledger.** 5 rows, 3 quantified, from CFPB complaints + PayPal Community for whichever of C01/C02/C06 you are leaning toward.
2. **Read the 3 nearest competitor repos** for your chosen concept (from `03_field/FIELD_MAP.md` top-10 list). Write the one-sentence difference.
3. **Confirm no gated-access dependency.** If the concept needs Store Sync approval or ACP credentials, it fails gate G7.
4. **Run the 15-second rule** — pitch it to someone with no context.

---

## 7. The 48-hour narrowing sprint

If you want to be building by Tuesday evening, this is the schedule:

| Slot | Do | Output |
|---|---|---|
| **Hour 0–1** | Read `01_Intent_Signals` and `02_Field_Map` end to end. Decide the *two* clusters you will consider. | Shortlist of 2 clusters |
| **Hour 1–3** | Phase 3 for those two clusters: CFPB + PayPal Community + Reddit. Fill `04_Pain_Ledger`. | ≥5 sourced pains, ≥3 quantified |
| **Hour 3–4** | Read the top-3 nearest repos for each cluster. Note exactly what they do and don't do. | Differentiation sentences |
| **Hour 4–5** | Phase 5: generate 20 concepts with the forcing table. Add them to `05_Concept_Pipeline` with real competitor counts from the scanner. | Pipeline of ~20 |
| **Hour 5–6** | Phase 6: hard gates, then EV. Take the top 3. | 3 survivors |
| **Hour 6–7** | Phase 7: red-team all 3 with the five prompts. Write the video opening line for each. | 1 winner |
| **Hour 7** | Log the decision. Re-run `scan_field.py`. | Frozen concept |
| **Day 2** | **Start building.** Sandbox app, one curl round-trip, repo + licence + deployed placeholder URL. | Building, not researching |

---

## 8. Sources index

**Primary — PayPal's own words and products**
- Q3 FY2026 earnings call, 27 Oct 2026 (Lores, Miller) — trust thesis, VAS attach admission, financial services, Venmo, 24M AI-resolved contacts
- Q2 FY2026 call, 28 Jul 2026 — agentic payments material "from 2028"; near-term AI value is cost and speed
- Ai4 2026, 10 Aug 2026 — CTO Venkatesan, Merchant AI Integration Agent
- NVIDIA GTC 2026, 18 Mar 2026 — Farahani, "plug and play" SMB agentic platform
- Google Cloud Next '26, 23 Apr 2026 — NL data agent, 7.5B records migrated
- Meta Muse support, 23 Sep 2026; Glance partnership, 15 Oct 2026
- Agentic commerce services launch, 28 Oct 2025; Cymbio acquisition closed 5 Feb 2026; Copilot Checkout, 8 Jan 2026
- `developer.paypal.com/ai-tools/agent-tools` (last updated 29 Oct 2026)
- `developer.paypal.com/agent-ready/overview` (last updated 13 Oct 2026)
- `docs.paypal.ai/growth/agentic-commerce/*` — Store Sync limitations
- `github.com/paypal/agent-toolkit`, `github.com/paypaldev/*` official starter repos

**Primary — the contest**
- Devpost listing, Official Rules §1–§8, all 10 sponsor detail pages, resources page

**Derived — this research**
- `03_field/snapshots/snapshot_2026-11-01.json` — 549 repos, machine-readable
- `03_field/FIELD_MAP.md` — cluster density report
- `03_field/CLUSTERS.csv`

**Secondary — used for dates and numbers only**
- Trade press summarising the calls and launches; AP2/UCP/ACP specification coverage
