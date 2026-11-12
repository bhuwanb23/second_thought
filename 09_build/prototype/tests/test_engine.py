"""Tests for the deterministic engine, including the red-team cases from the PRD."""

import sys
import os
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import (  # noqa: E402
    CashCalendar, Obligation, Instalment, Payday, Policy,
    InvalidRequest, decide, split_instalments, simulate, buffer_amount,
    add_months, monthly_income, next_payday,
)


# A persona with clear headroom: $4,000/mo across two paydays, modest obligations.
def roomy_calendar(today: date = date(2026, 11, 1)) -> CashCalendar:
    return CashCalendar(
        today=today,
        opening_balance=210_000,
        paydays=[Payday(today + timedelta(days=4), 200_000),
                 Payday(today + timedelta(days=18), 200_000),
                 Payday(today + timedelta(days=32), 200_000)],
        obligations=[Obligation("rent", today + timedelta(days=9), 145_000),
                     Obligation("childcare", today + timedelta(days=12), 60_000)],
        instalments=[],
    )


# Tight persona: rent lands right where instalment 3 falls.
def tight_calendar(today: date = date(2026, 11, 1)) -> CashCalendar:
    return CashCalendar(
        today=today,
        opening_balance=40_000,
        paydays=[Payday(today + timedelta(days=2), 180_000),
                 Payday(today + timedelta(days=16), 180_000),
                 Payday(today + timedelta(days=30), 180_000)],
        obligations=[Obligation("rent", today + timedelta(days=30), 145_000),
                     Obligation("car loan", today + timedelta(days=16), 31_200)],
        instalments=[Instalment("PLAN-A", 2, today + timedelta(days=9), 41_000),
                     Instalment("PLAN-A", 3, today + timedelta(days=23), 41_000)],
    )


class TestInstalmentSplit(unittest.TestCase):
    def test_sums_exactly(self):
        for amount in (0, 1, 3, 100, 9999, 10000, 24900, 100001):
            for n in (1, 2, 3, 4, 5):
                parts = split_instalments(amount, n)
                self.assertEqual(sum(parts), amount, f"{amount}/{n} lost a cent")
                self.assertEqual(len(parts), n)

    def test_largest_remainder_distribution(self):
        self.assertEqual(split_instalments(9999, 4), [2500, 2500, 2500, 2499])
        self.assertEqual(split_instalments(10000, 4), [2500, 2500, 2500, 2500])
        self.assertEqual(split_instalments(10001, 4), [2501, 2500, 2500, 2500])

    def test_rejects_bad_input(self):
        with self.assertRaises(InvalidRequest):
            split_instalments(-1, 4)
        with self.assertRaises(InvalidRequest):
            split_instalments(100, 0)


class TestDateMath(unittest.TestCase):
    def test_31st_rolls_down_in_february(self):
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
        self.assertEqual(add_months(date(2028, 1, 31), 1), date(2028, 2, 29))  # leap year

    def test_31st_rolls_down_in_30_day_month(self):
        self.assertEqual(add_months(date(2026, 3, 31), 1), date(2026, 4, 30))


class TestSimulation(unittest.TestCase):
    def test_min_balance_and_date(self):
        cal = roomy_calendar()
        min_bal, min_date, curve = simulate(cal)
        self.assertEqual(len(curve), 46)
        self.assertEqual(min_bal, min(c for _, c in curve))
        self.assertEqual(min_date, min(curve, key=lambda x: x[1])[0])

    def test_extra_debits_are_applied(self):
        cal = roomy_calendar()
        base_min, _, _ = simulate(cal)
        reduced_min, _, _ = simulate(cal, [(cal.today, -50_000, "test")])
        self.assertEqual(reduced_min, base_min - 50_000)

    def test_buffer_is_positive_even_with_zero_pct(self):
        cal = tight_calendar()
        floor = buffer_amount(cal, Policy(buffer_pct=0))
        self.assertGreater(floor, 0, "policy floor must protect one week of essentials")


class TestVerdicts(unittest.TestCase):
    def test_roomy_shopper_is_offered(self):
        d = decide(roomy_calendar(), 24_900)
        self.assertEqual(d.verdict, "OFFER")
        self.assertEqual(d.reason_code, "fits_comfortably")
        self.assertTrue(d.overridable)

    def test_tight_shopper_does_not_get_a_blind_offer(self):
        d = decide(tight_calendar(), 24_900)
        self.assertIn(d.verdict, ("DEFER", "DECLINE"))
        self.assertLessEqual(d.safe_amount, 24_900)

    def test_large_tight_purchase_declines_or_defers_with_a_collision(self):
        d = decide(tight_calendar(), 61_000)
        self.assertIn(d.verdict, ("DEFER", "DECLINE"))
        self.assertIsNotNone(d.collision, "a refusal must name what it collided with")

    def test_absurd_purchase_always_declines(self):
        d = decide(tight_calendar(), 5_000_000)
        self.assertEqual(d.verdict, "DECLINE")

    def test_safe_amount_actually_passes(self):
        cal = tight_calendar()
        d = decide(cal, 61_000)
        # Guard first: without this the test passes vacuously if safe_amount
        # regresses to 0, which is the failure it exists to catch.
        self.assertGreater(d.safe_amount, 0,
                           "this calendar must produce a positive safe amount, "
                           "otherwise the assertion below proves nothing")
        again = decide(cal, d.safe_amount)
        self.assertNotEqual(again.verdict, "DECLINE",
                            "the safe amount we offer must itself be feasible")

    def test_rejects_invalid_amounts(self):
        cal = roomy_calendar()
        for bad in (0, -100):
            with self.assertRaises(InvalidRequest):
                decide(cal, bad)
        with self.assertRaises(InvalidRequest):
            decide(cal, 24.99)  # float, not minor units

    def test_deterministic(self):
        cal = tight_calendar()
        first = decide(cal, 24_900).to_dict()
        for _ in range(20):
            self.assertEqual(decide(cal, 24_900).to_dict(), first)

    def test_options_are_complete(self):
        d = decide(tight_calendar(), 24_900)
        kinds = {o.kind for o in d.options}
        self.assertIn("PAY_IN_4", kinds)
        self.assertIn("DEFER_TO_PAYDAY", kinds)

    def test_instalments_never_exceed_amount(self):
        d = decide(roomy_calendar(), 24_900)
        p4 = next(o for o in d.options if o.kind == "PAY_IN_4")
        self.assertEqual(sum(a for _, a in p4.debits), 24_900)

    def test_same_day_instalment_collision_detected(self):
        today = date(2026, 11, 1)
        cal = tight_calendar(today)
        # put an existing instalment exactly where PAY_IN_4's third payment lands
        cal.instalments.append(
            Instalment("PLAN-B", 2, today + timedelta(days=28), 30_000))
        d = decide(cal, 40_000)
        if d.verdict != "OFFER":
            self.assertIsNotNone(d.collision)


class TestBufferEnforcement(unittest.TestCase):
    def test_safe_amount_is_the_exact_boundary(self):
        """safe_amount must be the largest feasible size: one unit more must fail."""
        cal = tight_calendar()
        d = decide(cal, 61_000)
        self.assertGreater(d.safe_amount, 0, "a tight-but-not-broke shopper needs a usable figure")
        self.assertEqual(decide(cal, d.safe_amount).verdict, "OFFER",
                         "safe_amount is by definition the largest size that passes")
        self.assertNotEqual(decide(cal, d.safe_amount + 1).verdict, "OFFER",
                            "one minor unit more must break the offer")

    def test_raising_the_buffer_reduces_the_safe_amount(self):
        cal = tight_calendar()
        loose = decide(cal, 61_000, policy=Policy(buffer_pct=5)).safe_amount
        tight = decide(cal, 61_000, policy=Policy(buffer_pct=40)).safe_amount
        self.assertGreaterEqual(loose, tight)

    def test_overdraw_is_never_feasible_even_with_a_zero_buffer(self):
        cal = tight_calendar()
        d = decide(cal, 5_000_000, policy=Policy(buffer_pct=0))
        self.assertEqual(d.verdict, "DECLINE")
        for o in d.options:
            if o.overdraws:
                self.assertFalse(o.feasible, f"{o.kind} overdraws but was marked feasible")


class TestCalendarHelpers(unittest.TestCase):
    def test_monthly_income_annualises_twice_monthly_pay(self):
        cal = roomy_calendar()  # 200000 every 14 days
        inc = monthly_income(cal)
        self.assertGreater(inc, 400_000)   # more than one payday per month
        self.assertLess(inc, 500_000)

    def test_next_payday_is_in_the_future(self):
        cal = roomy_calendar()
        nxt = next_payday(cal, cal.today)
        self.assertIsNotNone(nxt)
        self.assertGreater(nxt, cal.today)


if __name__ == "__main__":
    unittest.main(verbosity=2)
