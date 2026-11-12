"""Resolving the OFFER branch: every path must end in a real PayPal action."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paylater import (  # noqa: E402
    INSTRUMENT_AUTHORIZE, INSTRUMENT_INVOICE, INSTRUMENT_NONE, INSTRUMENT_PAYLATER,
    Eligibility, EligibilityStore, choose_instrument, describe_instrument,
    parse_sdk_result,
)


class TestSdkParsing(unittest.TestCase):
    def test_reads_a_real_findEligibleMethods_result(self):
        e = parse_sdk_result({"eligible": True, "currency": "USD", "country": "US",
                              "details": {"productCode": "PAY_IN_4",
                                          "countryCode": "US"}}, 24_900)
        self.assertTrue(e.eligible)
        self.assertEqual(e.product_code, "PAY_IN_4")
        self.assertEqual(e.source, "sdk")

    def test_unknown_shapes_become_unknown_never_hopeful(self):
        for payload in ({}, {"eligible": "yes"}, {"eligible": 1}, None, [], "x"):
            e = parse_sdk_result(payload, 24_900)
            self.assertIsNone(e.eligible, f"{payload!r} must not be read as eligible")
            self.assertEqual(e.source, "unknown")

    def test_false_is_preserved(self):
        self.assertFalse(parse_sdk_result({"eligible": False}, 24_900).eligible)


class TestInstrumentChoice(unittest.TestCase):
    def test_offer_with_eligibility_is_paylater(self):
        e = Eligibility(True, 24_900, product_code="PAY_IN_4", source="sdk")
        self.assertEqual(choose_instrument("OFFER", e), INSTRUMENT_PAYLATER)

    def test_offer_without_eligibility_falls_back_to_a_real_call(self):
        self.assertEqual(choose_instrument("OFFER", None), INSTRUMENT_AUTHORIZE)
        self.assertEqual(
            choose_instrument("OFFER", Eligibility(False, 24_900)), INSTRUMENT_AUTHORIZE)
        self.assertEqual(
            choose_instrument("OFFER", Eligibility(None, 24_900)), INSTRUMENT_AUTHORIZE)

    def test_defer_always_invoices(self):
        self.assertEqual(choose_instrument("DEFER", None), INSTRUMENT_INVOICE)

    def test_decline_never_shows_an_instrument(self):
        for e in (None, Eligibility(True, 24_900), Eligibility(False, 24_900)):
            self.assertEqual(choose_instrument("DECLINE", e), INSTRUMENT_NONE)

    def test_every_instrument_has_a_documented_paypal_call(self):
        for inst in (INSTRUMENT_PAYLATER, INSTRUMENT_AUTHORIZE,
                     INSTRUMENT_INVOICE, INSTRUMENT_NONE):
            d = describe_instrument(inst)
            self.assertIn("paypal_call", d)
            self.assertTrue(d["paypal_call"])


class TestStore(unittest.TestCase):
    def test_round_trip(self):
        s = EligibilityStore()
        e = Eligibility(True, 24_900, source="sdk")
        s.put("maya", e)
        self.assertEqual(s.get("maya").product_code, e.product_code)
        self.assertIsNone(s.get("nobody"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
