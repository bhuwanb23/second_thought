# The jury, simulated ten ways

*I read this project's pitch as ten different judges would, including the four who can end it. The
scores are my estimates on the hackathon's own five criteria, equally weighted, Technical
Implementation breaking ties. The quotes are reconstructions — what I think each of them says out
loud, not what anyone actually said.*

**The short version.** Three of ten would champion this. Five would score it mid-table. Two would
argue against it in the room. The reason is not the code — every persona that opens the repository
comes away impressed. The reason is that **the product takes a fee away from the company running the
competition, and no pitch on earth survives a judge noticing that before you have named it yourself.**

---

## 1. The PayPal product manager who owns Pay Later

*Scores: TI 4, Design 4, Impact 2, Innovation 3, Presentation 4 → **3.4***

> "So the pitch is: a merchant's own plan book that lets them avoid our 4.99%. You have built a nice
> piece of software to route around my P&L. Pay Later is one of the two things we told analysts we are
> investing in this year — it is in the Q3 call, next to branded checkout. Why would I ship this?"

> "And the part that actually stings: you are right about the 47%. We know about the 47%. Our answer
> was to stop charging late fees and convert missed payments to financing. Your answer is to sell
> less. Those are different businesses and only one of them reports revenue."

**What would change their mind:** evidence that this *increases* PayPal's TPV — declined-then-deferred
orders that would otherwise leave the site entirely, and merchants who currently offer Klarna or
Sunbit and therefore never route the transaction through PayPal at all. Framed as "win the merchants
who are not using us", this PM becomes the most useful person in the room. Framed as "skip the
lender fee", they are the most dangerous.

---

## 2. The PayPal developer-relations engineer

*Scores: TI 5, Design 4, Impact 3, Innovation 4, Presentation 4 → **4.0***

> "This is the only repo I have opened today with a hand-rolled RSA verifier and a test that asserts
> a foreign session cannot spend another's budget. Ten tests on webhook verification alone. That is
> not a hackathon project, that is a module I would review."

> "Counter, though: no SDK. I cannot tell from the README whether you know our platform or whether
> you fought it. You say it is fine — write the paragraph. You did. Good. Now show me a live order id
> in the dashboard, because that is the one thing a careful person cannot fake and an impressive repo
> still manages to avoid."

**Their private note to the panel:** "strongest engineering here; weakest demo. If they record the
video, top three. If they don't, fourth quartile. This is a submission-quality problem, not a
product problem."

---

## 3. The risk and compliance lead

*Scores: TI 4, Design 3, Impact 3, Innovation 3, Presentation 3 → **3.2***

> "You have designed a product where a merchant extends payment terms to a consumer. In the US that is
> Regulation Z territory the moment there is a finance charge or more than four instalments; in the UK
> it is squarely inside the BNPL rules arriving this year; in India it is a digital-lending
> arrangement with a named lender. Your answer is 'two instalments at zero percent.' Fine — and you
> have stated it, which is more than most. But you have also made the merchant the underwriter with
> no capital, no data and no collections capability."

> "Where is the affordability assessment? Where is the hardship path? What happens on day 46 when the
> invoice is unpaid and the goods have shipped? I see 'pay before ship', which handles the goods. I do
> not see what happens to a person."

**What would change their mind:** a hardship route — reschedule, split, or forgive — and a statement
that the engine refuses any plan where the second instalment falls after payday. The second already
exists in the code and is never said out loud.

---

## 4. The growth judge from marketing

*Scores: TI 3, Design 5, Impact 3, Innovation 5, Presentation 2 → **3.6***

> "Gorgeous. The screen is the best-designed thing in this competition — three named months, one
> sentence as an answer, no dashboard. I would hire the person who wrote 'Pay on Sat 15 Nov — and it
> ships once you've paid.'"

> "But I could not tell you what it is for. 'A checkout that says not yet' is a great line and a
> terrible proposition. Nobody wakes up wanting a checkout that refuses them. Sell me the outcome:
> the shop keeps a sale it would have lost, and the shopper does not get a fourth payment they cannot
> make. Lead with that and the design is doing its job."

---

## 5. The fintech investor

*Scores: TI 4, Design 4, Impact 2, Innovation 4, Presentation 3 → **3.4***

> "There is no moat here and I want to say that plainly. The rules engine is a weekend of work. The
> screening is three conditions. What makes a credit product defensible is a proprietary signal and
> distribution, and you have neither: you read what the shopper typed, and you have no channel."

> "The honest version of this company is a feature inside a merchant platform — Shopify, WooCommerce,
> a PSP — or a PayPal product team. As a standalone business it dies of CAC. As a PayPal feature it is
> interesting, which tells you what the pitch should be."

**What would change their mind:** one merchant saying "I would pay $49 a month for this", and a
measured lift over the lender route on the same cohort.

---

## 6. The design lead

*Scores: TI 3, Design 5, Impact 3, Innovation 4, Presentation 4 → **3.8***

> "The restraint is the achievement: one page, three answers, empty states written by someone who
> thought about them, and a rule in the build that internal words never reach a shopper. That test —
> `test_a_decline_never_says_instalment_or_collision` — is the most sophisticated design artefact
> I have seen today, and it is a unit test."

> "What it is missing is the second act. I see the verdict; I do not see the life of the reservation.
> Where is the screen for Ben two weeks later, when the invoice is due? That is the product, and it is
> not in the demo."

---

## 7. The merchant — the actual customer, not a judge

*Scores: — (would not score; would not buy)*

> "So I let someone take the sofa home and hope they pay me on the 15th? I have forty of those already
> and they are called invoices, and I hate them. The reason I use PayPal is that PayPal chases the
> money and I do not."

> "You are telling me I save five per cent. Five per cent of a $400 sale is twenty dollars. One
> chargeback costs me more than that in a morning. Who calls the customer when it is late? Who takes
> the card? If the answer is 'the software asks them to pay', then the software is a reminder system
> with extra steps."

**This is the voice that matters most and it is not in the room.** It is also the voice our demo
never answers. The product's real user is a merchant who already extends informal credit — trades,
clinics, repairs, tuition — and who wants the *decision and the collection* handled. We handle the
decision. We do not handle collections.

---

## 8. The credit-risk data scientist

*Scores: TI 3, Design 3, Impact 3, Innovation 4, Presentation 3 → **3.2***

> "You call it AI in the title and the AI is a parser. The decision is `if buffer < floor`. I respect
> that you admit it — 'the model supplies facts, the engine supplies the verdict' is the correct
> architecture — but you cannot then claim underwriting. Underwriting is calibration; calibration is
> data; you have three personas and zero outcomes."

> "The one number you are missing is the one that decides the business: what fraction of the people
> you DEFER actually pay on the new date? You have no idea. Neither do I. Whoever measures that first
> owns this idea."

**What would change their mind:** a backtest — even a simulated one — showing that the floor rule
would have caught the late payers in a public dataset. That is two days of work and it is the
difference between a rules toy and a model.

---

## 9. The rival entrant reading your repo

*Scores: TI 4, Design 4, Impact 4, Innovation 5, Presentation 1 → **3.6***

> "Three repos in the credit cluster and this is the only one with a decision engine. Annoying. But
> they have no video and no URL, so at 11:59 tonight they are a README."

> "'A checkout that says not yet' — I wish I had written that line. I am going to remember it. I am
> also going to point out that you can only say it because you are not lending anyone real money."

---

## 10. The sponsor judge (Render, AG Grid, APIMatic)

*Scores: sponsor prize — **not eligible***

> "Nice deploy. Here is a credit code for the infrastructure, because we give those to anyone who
> shows up. For the AG Grid prize — five slots, and the field is thin — you would have won something
> real with a ledger view of instalments. You did not enter. Nothing I can do."

---

## The matrix

| Persona | TI | Design | Impact | Innov. | Present. | Mean | Would champion? |
|---|---|---|---|---|---|---|---|
| PayPal Pay Later PM | 4 | 4 | 2 | 3 | 4 | **3.4** | No — actively against |
| PayPal DevRel engineer | 5 | 4 | 3 | 4 | 4 | **4.0** | Yes, if the video exists |
| Risk & compliance | 4 | 3 | 3 | 3 | 3 | **3.2** | Reluctant no |
| Growth / marketing | 3 | 5 | 3 | 5 | 2 | **3.6** | Yes, with a different first line |
| Fintech investor | 4 | 4 | 2 | 4 | 3 | **3.4** | No — wrong shape, right instinct |
| Design lead | 3 | 5 | 3 | 4 | 4 | **3.8** | Yes |
| The merchant | — | — | 1 | — | — | **1.0** | No — would not buy |
| Credit-risk scientist | 3 | 3 | 3 | 4 | 3 | **3.2** | Not yet |
| Rival entrant | 4 | 4 | 4 | 5 | 1 | **3.6** | Would steal the line |
| Sponsor judge | — | — | — | — | — | **n/a** | Not eligible |
| **Panel mean** | **3.8** | **4.0** | **2.8** | **4.0** | **3.1** | **3.5** | **3 of 10** |

Our own scorecard says 3.0 now and 4.5 after tonight's fixes. The jury says **3.5 now and 4.0 after**
— and the gap is concentrated in one column. **Potential Impact is the weakest score in the room**,
not Presentation. We have been arguing with the wrong judge.

---

## What recurs, and how often

| Attack | Raised by | Times |
|---|---|---|
| "Why would a merchant take on credit risk / do collections?" | merchant, PM, compliance, investor | **4** |
| "This takes revenue away from PayPal's own Pay Later" | PM, sponsor, investor | **3** |
| "The AI is a parser; there is no model" | scientist, DevRel, rival | **3** |
| "I cannot tell what it is for in ten seconds" | growth, PM, merchant | **3** |
| "No video / no URL / no live call" | DevRel, rival, sponsor | **3** |
| "No moat, no distribution" | investor, rival | **2** |
| "Hardship and day-46 collection are missing" | compliance, merchant | **2** |

Six of the seven recurring attacks are about the **business**, not the build. That is the finding.

---

## The single most dangerous sentence

> **"You have built a way for merchants to avoid paying PayPal's fee, and entered it in PayPal's
> competition."**

Nobody said it out loud in the reviews above, and three personas circled it. It is worth more than
every other risk in this document combined, because it can turn a 4.0 into a 2.5 in one exchange. It
is also *partly unfair* — the pitch sells to merchants, not against PayPal, and the transaction still
runs on PayPal's rails — which is exactly why it must be defused on the first slide rather than
argued about in the Q&A that never happens.

**How to defuse it, in one sentence, on screen:** *"The sale still runs on PayPal — we are not
replacing the rail, we are replacing the lender, and we bring the transaction to the rail that would
otherwise have gone to Klarna or to nobody."*

---

## What survives all ten

Three claims survived every persona, including the hostile ones:

1. **The refusal is real and nobody else is doing it.** No commercial product in this market says "not
   yet" — the closest, Sunbit, says yes to 85–90%. The cluster has three repos and none of them can
   decline.
2. **The AI/engine boundary is right.** Every technical judge independently praised it. It is the one
   claim that gets better the harder it is examined, which is rare and worth protecting in the video.
3. **The honesty is a differentiator, not a handicap.** Two personas specifically noted the
   READY-versus-PASS distinction and the `/proof` page as evidence of a builder they would trust.
   Nobody punished us for n = 0. Several punished us for not having a video — which is a different
   accusation entirely.

---

## What the jury says to do, ranked by votes

1. **Reframe the first line** (4 votes). Not "skips the fee" — "keeps the sale, on PayPal's rail,
   where the money actually moves." Same arithmetic, no target on your back.
2. **Ship a video** (3 votes). The DevRel engineer's note is the whole submission: strongest
   engineering, weakest demo.
3. **Say what happens on day 46** (2 votes). One screen or one sentence: the invoice, the reminder, the
   pay-before-ship rule, the hardship path. It costs a paragraph and closes the compliance objection.
4. **Name the merchant explicitly** (2 votes). "A clinic, a repair shop, a tutor — someone who already
   extends credit informally and hates it." That single sentence does more for Potential Impact than
   any feature.
5. **Do not chase the scientist's backtest** (1 vote, but it is the right long-term advice). Two days
   of work, not two hours, and it belongs in "what's next", not in tonight's submission.

---

## The verdict, as the panel would write it

**Score: 3.5 / 5, sixth to twelfth place of the submissions I would expect to be judged carefully.**

> "A genuinely original consumer-facing idea, executed to a standard well above this field, wrapped in
> a business model that the sponsor has a structural reason to dislike and the customer has an
> operational reason to avoid. The engineering is not in question: the boundary between model and
> engine is better thought through than anything else we read, and it is proved rather than asserted.
> What is in question is whether a merchant wants to become a lender to save twenty dollars. The team
> has an answer; it is on slide four; it should be on slide one. Recommend: strong honourable mention
> territory if the demo exists, category win if they can show one real merchant saying yes."

That is the honest ceiling, and it is a good ceiling. It is reachable tonight with a video and one
rewritten sentence — and it is unreachable with neither.
