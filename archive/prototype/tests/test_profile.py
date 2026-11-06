"""The payday profile: set up once, applied silently, shopper-owned."""

import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic import Extraction, Draft  # noqa: E402
from profile import (  # noqa: E402
    PaydayProfile, ProfileEntry, ProfileStore, from_extraction,
)

TODAY = date(2026, 11, 1)


class TestStore(unittest.TestCase):
    def test_in_memory_when_path_is_none(self):
        s = ProfileStore(path=None)
        s.put(PaydayProfile(shopper_id="maya", opening_balance=100))
        self.assertIsNotNone(s.get("maya"))
        self.assertEqual(len(s.profiles), 1)

    def test_round_trip_persists(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "p.json")
            s = ProfileStore(path=path)
            s.put(PaydayProfile(shopper_id="dev", obligations=[
                ProfileEntry("rent", 145_000, "2026-11-28", True, 0.9, True)]))
            again = ProfileStore(path=path)
            self.assertEqual(again.get("dev").obligations[0].amount_minor, 145_000)

    def test_delete(self):
        s = ProfileStore(path=None)
        s.put(PaydayProfile(shopper_id="sam"))
        self.assertTrue(s.delete("sam"))
        self.assertIsNone(s.get("sam"))


class TestFromExtraction(unittest.TestCase):
    def test_builds_a_profile_and_flags_low_confidence(self):
        ex = Extraction(obligations=[
            Draft("rent", 145_000, TODAY, True, 0.95),
            Draft("mum's meds", 4_000, TODAY, True, 0.41),
        ])
        p = from_extraction(ex, "maya", 40_000, TODAY)
        self.assertEqual(len(p.obligations), 2)
        self.assertTrue(p.obligations[0].confirmed)
        self.assertFalse(p.obligations[1].confirmed,
                         "a 41% guess must be shown to the shopper, not trusted")
        self.assertEqual(p.summary()["unconfirmed"], 1)
        self.assertEqual(p.setup_source, "extracted")

    def test_converts_to_a_calendar_the_engine_can_use(self):
        ex = Extraction(obligations=[Draft("rent", 145_000, TODAY, True, 0.9)])
        cal = from_extraction(ex, "maya", 40_000, TODAY).to_calendar(TODAY)
        self.assertEqual(cal.opening_balance, 40_000)
        self.assertEqual(sum(o.amount for o in cal.obligations), 145_000)


class TestProfileDrivesTheDecision(unittest.TestCase):
    def test_a_saved_profile_overrides_the_seeded_persona(self):
        import server
        from session import Session
        sess = Session("test-profile")          # isolated, in-memory, disposable

        base = server.build_payload("sam", session=sess)
        self.assertEqual(base["decision"]["verdict"], "OFFER")
        self.assertIsNone(base["profile"])

        # the shopper declares a large obligation we did not know about
        sess.profiles.put(PaydayProfile(
            shopper_id="sam", opening_balance=210_000,
            paydays=[ProfileEntry("pay", 200_000, d, False) for d in
                     ("2026-11-05", "2026-11-19", "2026-12-03")],
            obligations=[ProfileEntry("rent", 4_000_000, "2026-11-09", True, 0.99, True)],
            consented_at=TODAY.isoformat()))

        after = server.build_payload("sam", session=sess)
        self.assertIsNotNone(after["profile"], "the profile must be used")
        self.assertNotEqual(after["decision"]["verdict"], "OFFER",
                            "declared obligations must change the verdict")


class TestFulfilmentRule(unittest.TestCase):
    def test_risk_bearer_label_never_names_the_merchant(self):
        """
        A LABEL check, deliberately renamed to say so.

        This proves the word "merchant" never appears in `risk_bearer` — it does
        not prove a merchant cannot ship before payment, because this module has
        no shipping. The behavioural version of that guarantee is
        `product/tests/test_reservation.py::test_you_cannot_ship_before_payment`,
        where `fulfil()` raises unless the reservation is PAID.
        """
        from paylater import describe_instrument
        for inst in ("invoice", "authorize_hold", "none"):
            d = describe_instrument(inst)
            self.assertIn("risk_bearer", d)
            self.assertNotIn("merchant", d["risk_bearer"].lower(),
                             f"{inst} must not put credit risk on the merchant")
        self.assertIn("PAY BEFORE SHIP", describe_instrument("invoice")["fulfilment"])

    def test_paylater_names_paypal_as_the_risk_bearer(self):
        from paylater import describe_instrument
        self.assertEqual(describe_instrument("paylater")["risk_bearer"], "PayPal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
