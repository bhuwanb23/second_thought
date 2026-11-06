# Submission kit — copy, video and checklist

Everything a judge reads or hears, written out. Edit the specifics, keep the structure.

---

## 1. The "Tools used" field (required — paste this in)

> **PayPal developer tools:** Orders v2 (`AUTHORIZE`, capture, void), Invoicing API
> (`/v2/invoicing/invoices` with `payment_term.due_date`), webhooks with
> `/v1/notifications/verify-webhook-signature`, OAuth2 client credentials, `PayPal-Request-Id`
> idempotency, and the JS SDK v6 `findEligibleMethods()` eligibility check for Pay Later.
> Everything runs against the sandbox.
>
> **AI tools:** <MODEL NAME> via an OpenAI-compatible chat-completions API with **tool calling**,
> used for two jobs: (1) extracting a shopper's free-text month description into structured
> obligations, (2) driving an agent loop over a tool surface (`extract_obligations`,
> `decide_purchase`, `create_scheduled_invoice`, `authorize_payment`). The completion itself is
> produced by a deterministic integer-cent engine; the model never decides a verdict and never
> moves money without a human approval token bound to the exact arguments.

If AG Grid or APIMatic end up in the build, add a line each — **only if actually used.** Naming
a sponsor tool you didn't use is worse than omitting it.

---

## 2. Short description (the box judges skim)

> **Two fields, not one.** The rules require the short tagline **and** a full text description of
> features and functionality. The tagline below is only the first. Draft both in the Devpost draft
> opened in week one — see [P7.4](P7_record_and_submit.md).

> **Second Thought — the checkout that tells you the truth about your next four weeks.**
> Every BNPL tool is built to increase instalment take-up. Second Thought decides whether an
> instalment actually fits the person at the checkout — offering it, scheduling it to their
> payday as a real PayPal invoice, or declining it and naming the bill it collides with. They
> can always override.

---

## 3. The video — 2:40, recorded by 10 Nov

| Time | Beat | On screen |
|---|---|---|
| 0:00–0:15 | "Maya is buying headphones for $249. She's offered four payments of $62.25. Nothing on this screen tells her the third one lands the day after rent." | Storefront, Pay Later messaging |
| 0:15–0:40 | **DECLINE.** "Instalment 3 of 4 lands the same day as rent. She'd be $36.75 below her cushion. Her lowest point would be $113 with rent still to clear." | Verdict card + the balance curve dipping below the cushion line |
| 0:40–1:00 | The calendar: rent, car loan, her existing plan, this purchase's four payments. "This is what she can't see at checkout." | Calendar/AG Grid view |
| 1:00–1:20 | **The AI reads her words.** She types "rent 1450 on the 28th, car loan 312 on the 20th, mum's meds about 40". The model extracts three obligations with confidence scores; the 41% one is flagged to confirm. | The extraction card, live |
| 1:20–1:45 | **The invoice that saves the sale.** She picks the cheaper option or defers: agent proposes → *stops for approval* → she taps Approve → a real invoice appears, due 6 Nov. | The approval step, then the `INV2-` id |
| 1:45–2:05 | **A better month.** Dev, paid Thursday: same product, **DEFER**, invoice dated to payday. Sam, comfortable: **OFFER**, Pay Later renders. "Three shoppers, three answers, because there are three situations." | Persona switch, all three verdicts |
| 2:05–2:20 | **It can't be gamed.** A token approved for $249 fails against $999. A forged webhook is rejected. Duplicate `PayPal-Request-Id` doesn't double-charge. | Terminal or the JSON panel |
| 2:20–2:40 | "Half of BNPL users paid late last year. The harm isn't catastrophic default — it's a payment landing two days before payday. PayPal grows financial services on trust. This is what trust looks like at the moment of decision." | Closing card with the sourced numbers + their sources |

### What the video must contain, or the score suffers

- The **AI visible** — extraction on screen, and the agent's approval stop
- **One failure path** — the forged token is the best one
- A **real PayPal artefact** — an `INV2-` invoice id or an `AUTH-` id, on screen
- The **mode badge** (`SANDBOX · SIMULATED|LIVE`, `AI · LLM|LLM-MOCK`)
- **Under 3:00**, public, unlisted is not allowed

### Script variants for Pay Later

Run `PAYLATER_SANDBOX_TEST.md` first. Then:

- **Pay Later works:** show `isEligible("paylater") → true` and the `productCode`, then the button.
- **It doesn't:** say so in one sentence — *"Pay Later availability depends on the shopper's
  country and the merchant account, and it isn't enabled in this sandbox, so we gate on
  `findEligibleMethods()` and fall back to a real authorisation hold"* — then **make the invoice
  the hero**.

**Never fake a Pay Later offer screen.** Eligibility metadata is honest; a painted checkout is
not, and a PayPal engineer will spot it.

### Trademark hygiene

- **No brand logos** beyond what the PayPal SDK renders natively. Don't paste logos into slides.
- **No television, film or product references.** The AG Grid sponsorship page's example names
  are trademarks — do not reuse them as persona names or store names.
- **Keep personas generic.** "Maya", "Dev", "Sam" and "Northwind Audio" are invented and safe.
- **Don't name real retailers** in the demo. (The research quotes mention specific stores —
  those stay in the research library and out of the submission.)
- Music: use something licensed or nothing at all.

---

### Name the host, too

Prize eligibility for sponsor tools is by **use**, and Render is being used for the hosted demo.
Name it in the tools field alongside the AI provider. The plan targets a **paid starter instance**
(free instances sleep after ~15 minutes idle, and a cold start inside a judge's window is a lost
Presentation score) — confirm the price and whether the $50 credit applies before P5.

---

## 4. README requirements before the final push

Already in place in `product/README.md`, verify at submission:

```
[x] First line is the one-sentence pitch, identical wording to the video
[x] "PayPal APIs used" — literal endpoint paths, not product names
[x] "AI tools used" — model named, jobs named
[x] Sandbox-only statement
[x] "What is live, what is simulated" table
[x] Test output pasted, with the count
[x] Run instructions that work from a clean clone
[x] Licence visible in the GitHub About panel (17% of this field fails this)
[x] .env.example, .env gitignored, no secrets in history
[x] Live demo URL that answers /healthz until 15 Dec
```

---

## 5. Timeline — execution only, concept locked 1 Nov

**Locked 1 Nov** (`LOCK.md`). The idea, scope and pitch are frozen; only the two
tripwires can change anything, and both are pre-committed.

| Date | Work | Tripwire |
|---|---|---|
| **1 Nov** | ✅ Engine, agent, PayPal adapter, profile, fulfilment rule, **155 tests**, UI, probe page, all five review rounds | — |
| **2 Nov** | **Pay Later probe first** (`product/probe/v1_probe.html`) — closes tripwire 1 and fixes the OFFER wording. Then sandbox client ID + secret → `product/demo.py --live`. **Start conversations.** | ⚠️ 1 |
| **3 Nov** | `LLM_API_KEY` → badge reads `LLM`. Conversations continue | ⚠️ 2 |
| **4 Nov** | Conversations finish and are recorded in the table. **Apply the pre-committed decision rules — no reinterpretation.** Deploy to Render starter; verify `/healthz` | ⚠️ 2 |
| **5 Nov** | **AG Grid decision: in or out.** Write the answer down | — |
| **6–8 Nov** | Polish UI and README only. No new features | — |
| **9 Nov** | **Feature freeze** | — |
| **10 Nov** | Record and upload the 2:40 video. Quote a shopper if permission was given | — |
| **11 Nov** | Submit — a day early. Deadline is 12 Nov 12:00 PT = **13 Nov 01:30 IST** | — |

**Conversations are time-boxed to 2–4 Nov and run in parallel with building.** They are not a
reason to lose a day, and finishing with three instead of five is acceptable if the count is stated.

**Do not start a framework rewrite at any point.** The canonical product is working, tested and small;
that is the asset.

---

## 6. The five questions a judge will ask, and the answers

**"Isn't this just a calculator?"**
No — the calculator is the easy part. The product is the *instrument resolution*: knowing that a
front-of-month collision is fixable with an invoice and a late-month collision is not, and having
the PayPal API path for each verdict.

**"Why would PayPal want to reduce its own BNPL volume?"**
PayPal funds the merchant upfront and carries the credit risk on every instalment, so a badly
timed instalment costs PayPal more than a notional sale. And a shopper who gets a clear reason
returns; one who is silently blacklisted churns. The CEO calls financial services the growth
engine — this protects the engine.

**"Whose data is this?"**
The shopper's. See `product/README.md`. Consented input, arithmetic only, no adverse
action, always overridable.

**"What happens when the model is wrong?"**
It cannot change a decision. If extraction is wrong, the shopper sees low confidence and
corrects it; if the explanation is wrong, the verdict is unchanged and the template takes over.
There is a test for each.

**"Show me a failure."**
A token for $249 rejected against $999; a forged webhook rejected; a duplicate request id not
double-charging; an overdrawing option marked infeasible even at `buffer_pct=0`.
