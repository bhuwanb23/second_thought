"""The product must say how much it actually knows."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from profile import PaydayProfile, ProfileEntry, answer_quality  # noqa: E402


class TestAnswerQuality(unittest.TestCase):
    def test_no_profile_is_labelled_a_demo(self):
        q = answer_quality(None)
        self.assertEqual(q["grade"], "demo")
        self.assertIn("not your real data", q["note"])

    def test_confirmed_profile_is_full(self):
        p = PaydayProfile(shopper_id="x", obligations=[
            ProfileEntry("rent", 145_000, "2026-11-28", True, 0.95, True)])
        self.assertEqual(answer_quality(p)["grade"], "full")

    def test_unconfirmed_lines_make_it_partial_and_say_how_many(self):
        p = PaydayProfile(shopper_id="x", obligations=[
            ProfileEntry("rent", 145_000, "2026-11-28", True, 0.95, True),
            ProfileEntry("meds", 4_000, "2026-11-05", True, 0.41, False)])
        q = answer_quality(p)
        self.assertEqual(q["grade"], "partial")
        self.assertIn("1 line", q["note"])

    def test_the_payload_carries_it(self):
        import server
        from session import Session
        sess = Session("test-quality")
        self.assertEqual(server.build_payload("maya", session=sess)["answer_quality"]["grade"],
                         "demo")


if __name__ == "__main__":
    unittest.main(verbosity=2)
