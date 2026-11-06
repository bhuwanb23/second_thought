"""V4, part two — degradation, the template reader, and the tool call.

Same guarantees as test_ai.py, tested through the parts a user actually touches:
what happens to text the reader cannot parse, what the fallback admits about
itself, and whether a proposal can be spent as anything other than what was
signed.
"""

import json
import unittest
from datetime import date

from secondthought.ai.agent import Agent, TOOL_FOR_VERDICT, make_agent
from secondthought.ai.extract import Extraction, LLMError, LLMExtractor
from secondthought.ai.template import TemplateExtractor
from secondthought.app.approvals import ApprovalError, ApprovalGate
from secondthought.app.checkout import CheckoutService
from secondthought.config import AppSettings, LLMSettings
from secondthought.domain import Policy
from secondthought.infra.db import Database, LedgerRepo, ProfileRepo, ReservationRepo
from secondthought.infra.gateway import SimulatedGateway

TODAY = date(2026, 11, 2)
AMOUNT = 24_900

MESSY = ("rent's 1450 on the 28th, car loan 312 every second friday, oh and "
         "mum's meds ~40 a month")
NO_AMOUNTS = ("things have been tight since the shop cut my hours and I'm not "
              "really sure how the month is going to go")
OTHER_PHRASING = ("Salary lands on the 15th, 2,400 a month. Rent is due the 1st "
                  "and it's 1,375. Gym comes out automatically, twenty nine "
                  "dollars, on the 3rd.")
TOOL_TEXT = ("Salary's 2,400 on the 15th, rent's 1,375 on the 1st, "
             "car loan 312 every second friday")


class FakeLLM:
    def __init__(self, reply: str):
        self.reply = reply

    def __call__(self, _payload):
        return self.reply


def service():
    db = Database(":memory:")
    gw = SimulatedGateway()
    svc = CheckoutService(gateway=gw, profiles=ProfileRepo(db),
                          reservations=ReservationRepo(db), ledger=LedgerRepo(db),
                          approvals=ApprovalGate(), policy=Policy())
    return svc, gw, db


class GracefulDegradation(unittest.TestCase):
    def test_text_with_no_amounts_is_demo_and_produces_no_verdict(self):
        ext = TemplateExtractor().extract(NO_AMOUNTS, TODAY)
        self.assertEqual(ext.answer_quality, "demo")
        self.assertFalse(ext.usable)
        svc, _gw, db = service()
        try:
            result = Agent(svc).run("s", "m", AMOUNT, "USD", NO_AMOUNTS, TODAY)
            self.assertEqual(result.verdict, "NO_DECISION")
            self.assertTrue(result.questions)
            self.assertEqual(result.quote["verdict"], "NO_DECISION")
        finally:
            db.close()

    def test_a_model_returning_prose_instead_of_json_degrades_to_demo(self):
        ext = LLMExtractor(LLMSettings(api_key="k"),
                           transport=FakeLLM("Sure! Their rent is about $1,450.")).extract(
                               MESSY, TODAY)
        self.assertEqual(ext.answer_quality, "demo")
        self.assertEqual(ext.fields, {})
        self.assertEqual(ext.dropped[0]["reason"], "model did not return JSON")

    def test_a_profile_cannot_be_built_from_a_demo_extraction(self):
        with self.assertRaises(Exception):
            Agent.profile_from(Extraction(answer_quality="demo"), TODAY)

    def test_when_the_model_fails_the_fallback_says_so(self):
        class Broken:
            def __call__(self, _payload):
                raise LLMError("HTTP 401: invalid api key")
        svc, _gw, db = service()
        try:
            agent = Agent(svc, llm=LLMExtractor(LLMSettings(api_key="k"),
                                                transport=Broken()))
            ext = agent.extract(MESSY, TODAY)
            self.assertEqual(ext.mode, "template")
            self.assertTrue(any("model was unavailable" in q
                                for q in ext.needs_confirmation))
            self.assertTrue(ext.fields["obligations"], "fallback found nothing at all")
        finally:
            db.close()

    def test_the_daily_budget_stops_rather_than_overspends(self):
        llm = LLMExtractor(LLMSettings(api_key="k", daily_call_budget=2),
                           transport=FakeLLM('{"obligations": []}'))
        llm.extract("a", TODAY)
        llm.extract("b", TODAY)
        with self.assertRaises(LLMError) as ctx:
            llm.extract("c", TODAY)
        self.assertIn("budget", str(ctx.exception))


class TemplateReading(unittest.TestCase):
    """What the lesser mode actually gets — stated, not implied."""

    def test_it_reads_the_messy_passage(self):
        ext = TemplateExtractor().extract(MESSY, TODAY)
        got = {o["label"]: o["amount_minor"] for o in ext.fields["obligations"]}
        self.assertEqual(got.get("rent's"), 145_000)
        self.assertEqual(got.get("car loan friday"), 31_200)
        self.assertEqual(ext.answer_quality, "partial")

    def test_it_flags_the_inferred_friday_and_the_approximate_meds(self):
        ext = TemplateExtractor().extract(MESSY, TODAY)
        self.assertIn("obligation:car loan friday", ext.low_confidence)
        self.assertIn("obligation:mum's meds", ext.low_confidence)
        self.assertTrue(any("which Friday" in q for q in ext.needs_confirmation))
        self.assertTrue(any("approximate" in q for q in ext.needs_confirmation))

    def test_it_says_when_no_income_was_mentioned(self):
        ext = TemplateExtractor().extract(MESSY, TODAY)
        self.assertNotIn("paydays", ext.fields)
        self.assertTrue(any("No income" in q for q in ext.needs_confirmation))
        self.assertNotEqual(ext.answer_quality, "full")

    def test_it_reads_a_different_phrasing(self):
        ext = TemplateExtractor().extract(OTHER_PHRASING, TODAY)
        self.assertEqual(ext.fields["paydays"][0]["amount_minor"], 240_000)
        self.assertEqual(ext.fields["paydays"][0]["due"], "2026-11-15")
        self.assertEqual(ext.fields["obligations"][0]["amount_minor"], 137_500)

    def test_it_admits_what_it_could_not_read(self):
        # "twenty nine dollars" is a number the template cannot parse
        ext = TemplateExtractor().extract(OTHER_PHRASING, TODAY)
        self.assertTrue(ext.dropped)
        self.assertTrue(any("no amount I can read" in d["reason"] for d in ext.dropped))


class TheToolCall(unittest.TestCase):
    def setUp(self):
        self.svc, self.gw, self.db = service()
        self.agent = Agent(self.svc, policy=Policy())

    def tearDown(self):
        self.db.close()

    def _proposal(self):
        return self.agent.run("shopper", "merchant", AMOUNT, "USD", TOOL_TEXT, TODAY, 60_000)

    def test_extraction_to_decision_to_proposal(self):
        result = self._proposal()
        self.assertEqual(result.verdict, "DEFER")
        self.assertEqual(result.verdict_source, "engine")
        self.assertEqual(result.quote["tool"], TOOL_FOR_VERDICT["DEFER"])
        self.assertTrue(result.quote["approval_required"])
        self.assertEqual(result.quote["due_date"], "2026-11-15",
                         "the invoice was not dated to the payday")

    def test_a_tampered_amount_is_refused(self):
        q = self._proposal().quote
        tampered = dict(q["proposal"])
        tampered["amount_minor"] += 50_000
        with self.assertRaises(ApprovalError):
            self.svc.execute(q["tool"], tampered, q["token"])

    def test_a_tampered_due_date_is_refused(self):
        q = self._proposal().quote
        tampered = dict(q["proposal"])
        tampered["due_date"] = "2027-01-01"
        with self.assertRaises(ApprovalError):
            self.svc.execute(q["tool"], tampered, q["token"])

    def test_a_token_for_one_tool_cannot_be_used_for_another(self):
        q = self._proposal().quote
        args = {"shopper_id": "shopper", "merchant_id": "merchant",
                "amount_minor": AMOUNT, "currency": "USD"}
        with self.assertRaises(ApprovalError):
            self.svc.execute("authorise_hold", args, q["token"])

    def test_the_honest_arguments_do_produce_an_invoice(self):
        result = self._proposal()
        done = self.agent.approve_and_execute(result)
        self.assertEqual(done["state"], "RESERVED")
        self.assertTrue(done["invoice"]["id"].startswith("INV2-"))
        self.assertEqual(done["invoice"]["due_date"], "2026-11-15")
        self.assertEqual(len(self.gw.calls), 1, "the gateway was called more than once")

    def test_nothing_moves_before_approval(self):
        self._proposal()
        self.assertEqual(self.gw.calls, [], "a proposal reached the gateway")


class Wiring(unittest.TestCase):
    def test_a_key_means_a_real_model_and_no_key_means_no_model(self):
        svc, _gw, db = service()
        try:
            self.assertIsNone(make_agent(svc, AppSettings()).llm)
            self.assertIsNotNone(make_agent(
                svc, AppSettings(llm=LLMSettings(api_key="k"))).llm)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
