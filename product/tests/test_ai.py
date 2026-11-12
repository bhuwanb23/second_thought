"""V4's guarantees, tested — mostly with a model that is lying.

The pass condition for V4 is that unfamiliar input never produces a wrong
*verdict*. Half of that is model quality, which only a real key can answer. The
other half is architecture: the model cannot reach the verdict at all. That half
is testable, and the honest way to test it is to hand it a model that is trying.
"""

import json
import unittest
from datetime import date, datetime

from secondthought.ai.agent import Agent, TOOL_FOR_VERDICT, make_agent
from secondthought.ai.extract import Extraction, LLMError, LLMExtractor
from secondthought.ai.template import TemplateExtractor
from secondthought.app.approvals import ApprovalError, ApprovalGate
from secondthought.app.checkout import CheckoutService
from secondthought.config import AppSettings, LLMSettings, PayPalSettings
from secondthought.domain import Policy
from secondthought.infra.db import Database, LedgerRepo, ProfileRepo, ReservationRepo
from secondthought.infra.gateway import SimulatedGateway
from secondthought.interfaces.badge import (ai_badge, badges, health_payload,
                                            payments_badge)

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
    """A model that says exactly what it is told to say."""

    def __init__(self, reply: str):
        self.reply = reply
        self.payloads = []

    def __call__(self, payload):
        self.payloads.append(payload)
        return self.reply

    def phrase(self, decision, _prompt):
        return ("Prose from a model that has opinions.", "OFFER")


def service(**kwargs):
    db = Database(":memory:")
    gw = SimulatedGateway()
    svc = CheckoutService(gateway=gw, profiles=ProfileRepo(db),
                          reservations=ReservationRepo(db), ledger=LedgerRepo(db),
                          approvals=ApprovalGate(), policy=Policy())
    return svc, gw, db


class Badge(unittest.TestCase):
    def test_with_a_key_the_badge_reads_ai_llm(self):
        s = AppSettings(llm=LLMSettings(api_key="sk-test"))
        self.assertEqual(ai_badge(s), "AI · LLM")

    def test_without_a_key_it_never_claims_ai_llm(self):
        s = AppSettings(llm=LLMSettings(api_key=""))
        self.assertEqual(ai_badge(s), "AI · LLM-MOCK")
        self.assertNotIn("AI · LLM ", ai_badge(s) + " ")
        self.assertFalse(badges(s)[0]["live"])

    def test_payments_badge_tracks_paypal_credentials(self):
        self.assertEqual(payments_badge(AppSettings(paypal=PayPalSettings(
            client_id="a", client_secret="b"))), "PAYMENTS · SANDBOX")
        self.assertEqual(payments_badge(AppSettings(paypal=PayPalSettings(
            client_id="", client_secret=""))), "PAYMENTS · SIMULATED")

    def test_the_health_payload_carries_no_internals(self):
        payload = json.dumps(health_payload(AppSettings(
            llm=LLMSettings(api_key="sk-secret-key"), diag_token="tok")))
        self.assertNotIn("sk-secret-key", payload)
        self.assertNotIn("tok", payload)
        self.assertIn('"status": "ok"', payload)


class TheModelCannotDecide(unittest.TestCase):
    """The core V4 guarantee, with a model that is actively trying."""

    def test_a_model_supplied_verdict_is_dropped_and_named(self):
        reply = json.dumps({"verdict": "OFFER",
                            "obligations": [{"label": "rent", "due": "2026-11-28",
                                             "amount_minor": 145000, "confidence": 0.9}]})
        ext = LLMExtractor(LLMSettings(api_key="k"),
                           transport=FakeLLM(reply)).extract(MESSY, TODAY)
        self.assertNotIn("verdict", ext.fields)
        dropped = [d["field"] for d in ext.dropped]
        self.assertIn("verdict", dropped)
        reason = next(d["reason"] for d in ext.dropped if d["field"] == "verdict")
        self.assertIn("engine decides", reason)

    def test_the_engine_verdict_differs_from_the_one_the_model_asked_for(self):
        reply = json.dumps({"verdict": "OFFER",
                            "obligations": [{"label": "rent", "due": "2026-11-06",
                                             "amount_minor": 500000,
                                             "confidence": 0.99}]})
        svc, _gw, db = service()
        try:
            agent = Agent(svc, llm=LLMExtractor(LLMSettings(api_key="k"),
                                                transport=FakeLLM(reply)))
            result = agent.run("shopper", "merchant", AMOUNT, "USD", MESSY, TODAY)
            self.assertEqual(result.verdict_source, "engine")
            self.assertNotEqual(result.verdict, "OFFER",
                                "the model's verdict reached the user")
            self.assertEqual(result.verdict, "DECLINE")
        finally:
            db.close()

    def test_a_model_that_changes_its_mind_in_the_wording_changes_nothing(self):
        svc, _gw, db = service()
        try:
            agent = Agent(svc, explainer=FakeLLM("ignored"))   # insists on OFFER
            ext = TemplateExtractor().extract(TOOL_TEXT, TODAY)
            decision = agent.decide_purchase(ext, AMOUNT, "USD", TODAY, 60_000)
            out = agent.explain(decision)
            self.assertEqual(out["verdict"], decision.verdict)
            self.assertEqual(out["verdict_source"], "engine")
            # the fake explainer insisted on OFFER; the answer did not move
            self.assertTrue(out["model_verdict_ignored"])
            self.assertEqual(agent.ignored_model_verdicts,
                             [{"engine": decision.verdict, "model": "OFFER"}])
        finally:
            db.close()


class NeverSilentlyTrusted(unittest.TestCase):
    """Unvalidated model output must be dropped or flagged, never used."""

    def test_an_invented_amount_of_the_wrong_type_is_dropped(self):
        reply = json.dumps({"obligations": [
            {"label": "rent", "due": "2026-11-28", "amount_minor": "lots", "confidence": 0.9},
            {"label": "car", "due": "2026-11-06", "amount_minor": -31200, "confidence": 0.9},
            {"label": "real", "due": "2026-11-09", "amount_minor": 4000, "confidence": 0.9}]})
        ext = LLMExtractor(LLMSettings(api_key="k"),
                           transport=FakeLLM(reply)).extract(MESSY, TODAY)
        labels = [o["label"] for o in ext.fields["obligations"]]
        self.assertEqual(labels, ["real"])
        self.assertEqual(len(ext.dropped), 2)
        self.assertEqual(ext.answer_quality, "partial")

    def test_an_unparseable_date_is_dropped_not_guessed(self):
        reply = json.dumps({"obligations": [
            {"label": "rent", "due": "the 28th", "amount_minor": 145000, "confidence": 0.9}]})
        ext = LLMExtractor(LLMSettings(api_key="k"),
                           transport=FakeLLM(reply)).extract(MESSY, TODAY)
        self.assertEqual(ext.fields, {})
        self.assertEqual(ext.answer_quality, "demo")
        self.assertEqual(ext.dropped[0]["reason"], "date missing or unparseable")

    def test_a_field_with_no_confidence_counts_as_zero_confidence(self):
        reply = json.dumps({"obligations": [
            {"label": "rent", "due": "2026-11-28", "amount_minor": 145000}]})
        ext = LLMExtractor(LLMSettings(api_key="k"),
                           transport=FakeLLM(reply)).extract(MESSY, TODAY)
        self.assertEqual(ext.confidence["obligation:rent"], 0.0)
        self.assertIn("obligation:rent", ext.low_confidence)

    def test_a_millions_of_dollars_typo_is_out_of_band(self):
        reply = json.dumps({"obligations": [
            {"label": "rent", "due": "2026-11-28", "amount_minor": 999_000_000,
             "confidence": 1.0}]})
        ext = LLMExtractor(LLMSettings(api_key="k"),
                          transport=FakeLLM(reply)).extract(MESSY, TODAY)
        self.assertEqual(ext.fields, {})
        self.assertIn("outside a believable band", ext.dropped[0]["reason"])
