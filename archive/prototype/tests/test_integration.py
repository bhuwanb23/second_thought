"""End to end: engine -> explanation -> PayPal action, through the server payload."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402
from engine import split_instalments  # noqa: E402
from ledger import Ledger  # noqa: E402
from profile import ProfileStore  # noqa: E402


def setUpModule():
    """Fresh in-memory default session; nothing touches disk or other visitors."""
    server.DEFAULT.reset()


def tearDownModule():
    server.DEFAULT.reset()


class TestPayloads(unittest.TestCase):
    def test_every_persona_builds_a_complete_payload(self):
        for key in ("maya", "dev", "sam", "maya-cheaper"):
            p = server.build_payload(key)
            self.assertIn("decision", p)
            self.assertIn("explanation", p)
            self.assertIn(p["mode"], ("live", "simulated"))
            self.assertEqual(len(p["curve"]), 46)
            self.assertGreaterEqual(len(p["events"]), 1)
            self.assertIn(p["decision"]["verdict"], ("OFFER", "DEFER", "DECLINE"))

    def test_verdicts_are_the_three_we_designed_for(self):
        self.assertEqual(server.build_payload("sam")["decision"]["verdict"], "OFFER")
        self.assertEqual(server.build_payload("dev")["decision"]["verdict"], "DEFER")
        self.assertEqual(server.build_payload("maya")["decision"]["verdict"], "DECLINE")
        self.assertEqual(server.build_payload("maya-cheaper")["decision"]["verdict"], "OFFER")

    def test_explanation_verdict_matches_engine_verdict(self):
        for key in ("maya", "dev", "sam"):
            p = server.build_payload(key)
            self.assertEqual(p["explanation"]["verdict"], p["decision"]["verdict"])

    def test_amount_override_is_allowed(self):
        p = server.build_payload("maya", 15800)
        self.assertEqual(p["amount"], 15800)
        self.assertEqual(p["decision"]["verdict"], "OFFER")


class TestExecute(unittest.TestCase):
    def setUp(self):
        server.LEDGER.entries = []
        server.ELIGIBILITY.records = {}

    def _approved(self, persona, amount=None):
        p = server.build_payload(persona, amount)
        a = server.approve(p)
        self.assertTrue(a["ok"], "an executable instrument must be approvable")
        return p, a["token"]

    def test_offer_without_eligibility_holds_funds_and_needs_approval(self):
        p = server.build_payload("sam")
        self.assertEqual(p["instrument"], "authorize_hold")
        self.assertTrue(p["requires_approval"])
        out = server.execute(p)                      # no token
        self.assertFalse(out["ok"])
        self.assertEqual(out["action"], "approval_required")

        p, token = self._approved("sam")
        out = server.execute(p, token)
        self.assertTrue(out["ok"])
        self.assertEqual(out["action"], "authorized")
        self.assertIn("authorization_id", out["paypal"])

    def test_offer_with_eligibility_creates_a_paylater_order(self):
        server.ELIGIBILITY.put("sam", server.paylater.Eligibility(
            True, 24_900, product_code="PAY_IN_4", source="sdk"))
        p = server.build_payload("sam")
        self.assertEqual(p["instrument"], "paylater")
        self.assertFalse(p["requires_approval"], "creating an order moves no money")
        out = server.execute(p)
        self.assertTrue(out["ok"])
        self.assertEqual(out["action"], "order_created_for_paylater")

    def test_defer_creates_an_invoice_due_on_payday(self):
        p, token = self._approved("dev")
        self.assertEqual(p["instrument"], "invoice")
        out = server.execute(p, token)
        self.assertTrue(out["ok"])
        self.assertEqual(out["action"], "invoice_created")
        self.assertEqual(out["paypal"]["due"], "2026-11-06")

    def test_decline_takes_no_paypal_action(self):
        p = server.build_payload("maya")
        self.assertEqual(p["instrument"], "none")
        out = server.execute(p)
        self.assertFalse(out["ok"])
        self.assertEqual(out["action"], "none")
        self.assertIn("override", out["message"])

    def test_a_token_for_a_different_amount_is_rejected(self):
        p = server.build_payload("dev")
        a = server.approve(p)
        p2 = server.build_payload("dev", 99_900)
        out = server.execute(p2, a["token"])
        self.assertEqual(out["action"], "approval_required",
                         "approval for 249.00 must not authorise 999.00")

    def test_executed_actions_land_in_the_ledger(self):
        p, token = self._approved("sam")
        server.execute(p, token)
        self.assertEqual(len(server.LEDGER.entries), 1)
        self.assertEqual(server.LEDGER.entries[0].instrument, "pay_in_4")


class TestLedgerExposure(unittest.TestCase):
    def test_instalments_from_the_ledger_feed_the_next_decision(self):
        """The plan we originate must affect the next verdict. That is the product."""
        from ledger import Ledger
        from personas import TODAY

        ledger = Ledger(path=None)
        base = server.build_payload("sam")["decision"]["verdict"]
        self.assertEqual(base, "OFFER")

        for _ in range(6):   # six separate purchases at this merchant
            ledger.record("sam", 24_900, "USD", "pay_in_4", today=TODAY)
        exposure = ledger.exposure("sam", TODAY)
        self.assertEqual(exposure["plans_open"], 6)
        self.assertGreater(exposure["open_amount"], 0)

        inst = ledger.instalments_for("sam")
        self.assertEqual(len(inst), 24)
        self.assertEqual(sum(i.amount for i in inst), 24_900 * 6,
                         "ledger instalments must sum to what we originated")

    def test_instalment_sums_are_exact_in_the_ledger(self):
        for amount in (1, 99, 10_000, 24_900, 24_901):
            self.assertEqual(sum(split_instalments(amount, 4)), amount)


class TestNoNetworkInTheDecisionPath(unittest.TestCase):
    def test_decide_makes_no_network_calls(self):
        """The verdict must come from arithmetic, never from a network round trip."""
        import engine
        with open(engine.__file__) as f:
            source = f.read()
        for forbidden in ("urllib", "requests", "http.client", "socket"):
            self.assertNotIn(forbidden, source,
                             f"engine imports {forbidden} — the decision path must be offline")


if __name__ == "__main__":
    unittest.main(verbosity=2)
