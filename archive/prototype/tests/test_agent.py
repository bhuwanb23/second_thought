"""The agent may phrase a decision. It may never make one. These tests prove it."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import (  # noqa: E402
    LLMExplainer, REQUIRED_KEYS, TemplateExplainer, explain, money,
)
from engine import decide  # noqa: E402
from personas import DEFAULT_POLICY, dev as dev_cal, maya as maya_cal, sam as sam_cal


def decisions():
    return {
        "OFFER": decide(sam_cal(), 24_900, policy=DEFAULT_POLICY),
        "DEFER": decide(dev_cal(), 24_900, policy=DEFAULT_POLICY),
        "DECLINE": decide(maya_cal(), 24_900, policy=DEFAULT_POLICY),
    }


class TestMoneyFormatting(unittest.TestCase):
    def test_formats_cents_correctly(self):
        self.assertEqual(money(24_900), "$249.00")
        self.assertEqual(money(5), "$0.05")
        self.assertEqual(money(0), "$0.00")
        self.assertEqual(money(-8_340), "-$83.40")
        self.assertEqual(money(1_000_000), "$10,000.00")


class TestTemplateExplainer(unittest.TestCase):
    def test_covers_every_verdict(self):
        for expected, d in decisions().items():
            self.assertEqual(d.verdict, expected, f"persona drifted: {d.reason_code}")
            out = TemplateExplainer().explain(d, {"merchant": "Northwind Audio"})
            for key in REQUIRED_KEYS:
                self.assertIn(key, out)
                self.assertTrue(out[key].strip(), f"empty {key} for {expected}")
            self.assertEqual(out["verdict"], expected)

    def test_decline_names_both_sides_of_the_collision(self):
        out = TemplateExplainer().explain(decisions()["DECLINE"])
        self.assertIn("instalment 3 of 4", out["headline"].lower())
        self.assertIn("rent", out["headline"].lower())

    def test_decline_offers_a_concrete_safe_amount(self):
        d = decisions()["DECLINE"]
        out = TemplateExplainer().explain(d)
        self.assertGreater(d.safe_amount, 0)
        self.assertIn(money(d.safe_amount), out["alternative"])

    def test_never_shames_or_blocks(self):
        for d in decisions().values():
            out = TemplateExplainer().explain(d)
            blob = " ".join(out.values()).lower()
            self.assertNotIn("you cannot afford", blob)
            self.assertNotIn("shouldn't have", blob)
            self.assertNotIn("bad with money", blob)

    def test_decline_explicitly_says_the_shopper_can_proceed(self):
        d = decisions()["DECLINE"]
        if d.safe_amount > 0:
            out = TemplateExplainer().explain(d)
            self.assertIn("still buy", out["alternative"].lower())


class TestVerdictCannotBeChanged(unittest.TestCase):
    def test_a_rogue_explainer_is_overridden(self):
        """The important test in the suite."""

        class Rogue:
            name = "rogue"

            def explain(self, decision, context=None):
                return {"headline": "Sure, go ahead!", "why": "Approved.",
                        "alternative": "Buy it now.",
                        "verdict": "OFFER" if decision.verdict != "OFFER" else "DECLINE",
                        "engine": "rogue"}

        for d in decisions().values():
            out = explain(d, {}, explainer=Rogue())
            self.assertEqual(out["verdict"], d.verdict,
                             "a rogue explainer changed the engine's verdict")
            if d.verdict != "OFFER":
                self.assertEqual(out["engine"], "template")
                self.assertEqual(out.get("fallback_reason"),
                                 "verdict_changed_after_explanation")

    def test_engine_verdict_is_immutable_across_explanation(self):
        for d in decisions().values():
            before = d.verdict
            explain(d, {}, explainer=TemplateExplainer())
            self.assertEqual(d.verdict, before)


class TestLLMExplainer(unittest.TestCase):
    def test_without_a_key_it_falls_back_to_template(self):
        old = os.environ.pop("LLM_API_KEY", None)
        try:
            expl = LLMExplainer(api_key="")
            d = decisions()["DEFER"]
            out = expl.explain(d, {})
            self.assertEqual(out["engine"], "template")
            self.assertEqual(out["verdict"], "DEFER")
        finally:
            if old is not None:
                os.environ["LLM_API_KEY"] = old

    def test_invalid_model_output_is_rejected(self):
        d = decisions()["DECLINE"]
        bad_payloads = [
            {},
            {"headline": "x", "why": "y", "alternative": "z"},          # no verdict
            {"headline": "x", "why": "y", "alternative": "z", "verdict": "OFFER"},
            {"headline": "", "why": "y", "alternative": "z", "verdict": d.verdict},
            {"headline": 1, "why": "y", "alternative": "z", "verdict": d.verdict},
        ]
        for payload in bad_payloads:
            with self.assertRaises(Exception):
                LLMExplainer._validate(payload, d)

    def test_valid_model_output_is_accepted(self):
        d = decisions()["OFFER"]
        good = {"headline": "Fits fine", "why": "You have room.",
                "alternative": "Nothing to change.", "verdict": "OFFER"}
        out = LLMExplainer._validate(good, d)
        self.assertEqual(out["verdict"], "OFFER")


if __name__ == "__main__":
    unittest.main(verbosity=2)
