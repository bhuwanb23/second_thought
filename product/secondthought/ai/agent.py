"""
ai/agent.py — the model reads and proposes. The engine decides. A human approves.

The split is the product, so it is enforced structurally rather than by prompt:

  extraction → facts, each with a confidence          (extractor.py)
  decide_purchase → the engine's verdict, from facts  (domain/engine.py)
  propose → one tool call, signed for its exact args  (app/checkout.py)
  human approves → redeem → the gateway is called     (app/approvals.py)

There is no code path in which a model's output becomes a verdict. `explain()`
is the only place the model touches the answer, and it is given the verdict as
an input it may phrase but not return.

Tool naming: V4 calls the invoice tool `create_scheduled_invoice`. The signed
action is `create_reservation`, because an invoice on its own holds nothing —
the reservation is what makes the merchant unable to ship before payment. Same
call, one name, and the name with the guarantee in it wins.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from ..app.checkout import Checkout, CheckoutService
from ..domain import CashCalendar, InvalidRequest, Obligation, Payday, Policy
from ..domain.engine import decide
from .extract import Extraction, LLMError, LLMExtractor
from .template import TemplateExtractor

TOOL_FOR_VERDICT = {"DEFER": "create_reservation", "OFFER": "authorise_hold"}

_EXPLAIN_PROMPT = """Rewrite the decision below for a shopper, in one or two plain
sentences. You are not deciding anything: the decision has already been made and
must not change. Do not output JSON, a verdict, an amount, or a date that is not
already in the decision. Do not promise approval for credit. If the decision is
DEFER, say plainly that they pay on payday and the merchant ships after payment."""


@dataclass
class AgentResult:
    verdict: str
    verdict_source: str                 # always "engine"
    answer_quality: str
    provisional: bool
    questions: list
    quote: dict
    extraction: dict

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "verdict_source": self.verdict_source,
                "answer_quality": self.answer_quality, "provisional": self.provisional,
                "questions": self.questions, "quote": self.quote,
                "extraction": self.extraction}


class Agent:
    def __init__(self, service: CheckoutService, *, llm=None, explainer=None,
                 policy: Policy | None = None):
        self.service = service
        self.llm = llm
        self.explainer = explainer or llm          # wording model, may be the same
        self.policy = policy or Policy()
        self.ignored_model_verdicts: list = []

    # -- 1. text → facts ---------------------------------------------------
    def extract(self, text: str, today: date) -> Extraction:
        """Model first; template if the model is unavailable. Never a guess."""
        if self.llm is not None:
            try:
                return self.llm.extract(text, today)
            except LLMError as exc:
                fallback = TemplateExtractor().extract(text, today)
                fallback.needs_confirmation.append(
                    f"The model was unavailable ({exc}); this was read by the "
                    f"deterministic fallback.")
                return fallback
        return TemplateExtractor().extract(text, today)

    @staticmethod
    def profile_from(extraction: Extraction, today: date,
                     opening_balance: int = 0) -> dict:
        """A profile the engine can use. Refuses a `demo` extraction outright."""
        if not extraction.usable:
            raise InvalidRequest(
                "answer_quality is 'demo' — nothing usable was extracted, so there "
                "is nothing to decide. Asking for a verdict here would be a guess.")
        return {"opening_balance": extraction.fields.get("opening_balance",
                                                         opening_balance),
                "paydays": [{"due": p["due"], "amount_minor": p["amount_minor"]}
                            for p in extraction.fields.get("paydays", [])],
                "obligations": [{"label": o["label"], "due": o["due"],
                                 "amount_minor": o["amount_minor"], "essential": True}
                                for o in extraction.fields.get("obligations", [])]}

    # -- 2. facts → verdict ------------------------------------------------
    def decide_purchase(self, extraction: Extraction, amount_minor: int,
                         currency: str, today: date,
                         opening_balance: int = 0):
        """The engine's verdict from the extracted calendar. The only verdict."""
        profile = self.profile_from(extraction, today, opening_balance)
        cal = CashCalendar(
            today=today, opening_balance=profile["opening_balance"],
            paydays=[Payday(date.fromisoformat(p["due"]), p["amount_minor"])
                     for p in profile["paydays"]],
            obligations=[Obligation(o["label"], date.fromisoformat(o["due"]),
                                    o["amount_minor"], o.get("essential", True))
                         for o in profile["obligations"]])
        return decide(cal, amount_minor, currency, self.policy)

    # -- 3. verdict → words (never back the other way) ---------------------
    def explain(self, decision, text: str = "") -> dict:
        engine_verdict = decision.verdict
        wording, model_verdict = None, None
        if self.explainer is not None and callable(getattr(self.explainer, "phrase", None)):
            try:
                wording, model_verdict = self.explainer.phrase(decision, _EXPLAIN_PROMPT)
            except Exception as exc:                        # noqa: BLE001
                wording = f"(the model could not be reached: {exc})"
        if model_verdict and model_verdict != engine_verdict:
            self.ignored_model_verdicts.append(
                {"engine": engine_verdict, "model": model_verdict})
        return {"wording": wording, "verdict": engine_verdict,
                "verdict_source": "engine",
                "model_verdict_ignored": bool(model_verdict
                                              and model_verdict != engine_verdict)}

    # -- 4. the whole path, ending at the approval gate --------------------
    def run(self, shopper_id: str, merchant_id: str, amount_minor: int,
            currency: str, text: str, today: date,
            opening_balance: int = 0) -> AgentResult:
        extraction = self.extract(text, today)
        if not extraction.usable:
            return AgentResult(
                verdict="NO_DECISION", verdict_source="engine",
                answer_quality=extraction.answer_quality, provisional=True,
                questions=extraction.needs_confirmation,
                quote={"verdict": "NO_DECISION",
                       "note": "Not enough readable facts to decide. Nothing moves."},
                extraction=extraction.to_dict())

        profile = self.profile_from(extraction, today, opening_balance)
        self.service.profiles.save(f"_trial_{shopper_id}", profile,
                                   datetime.combine(today, datetime.min.time()))
        checkout = Checkout(f"_trial_{shopper_id}", merchant_id, amount_minor, currency)
        proposal = self.service.propose(checkout, today)
        return AgentResult(
            verdict=proposal["verdict"], verdict_source="engine",
            answer_quality=extraction.answer_quality,
            provisional=(extraction.answer_quality != "full"),
            questions=extraction.needs_confirmation,
            quote=proposal, extraction=extraction.to_dict())

    # -- 5. execute, but only with a token that matches these exact args ---
    def approve_and_execute(self, result: AgentResult, now: datetime | None = None) -> dict:
        q = result.quote
        if not q.get("approval_required"):
            raise InvalidRequest("there is nothing to approve for this verdict")
        return self.service.execute(q["tool"], q["proposal"], q["token"], now)


def make_agent(service, settings, *, transport=None) -> Agent:
    """The wiring rule: a key means a real model, no key means a labelled mock."""
    llm = LLMExtractor(settings.llm, transport=transport) if settings.llm.configured else None
    return Agent(service, llm=llm)
