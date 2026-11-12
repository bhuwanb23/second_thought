"""End to end: profile -> quote -> propose -> approve -> pay -> ship."""

import unittest
from datetime import date, datetime, timedelta

from secondthought.app.approvals import ApprovalError
from secondthought.app.checkout import Checkout
from secondthought.domain.reservation import ReservationError, State
from tests.fixtures import NOW, TODAY, Wired


def co(shopper, amount=24900, merchant="northwind"):
    return Checkout(shopper_id=shopper, merchant_id=merchant,
                    amount_minor=amount, currency="USD")


class TestTheThreeOutcomes(unittest.TestCase):
    def setUp(self):
        self.w = Wired()

    def tearDown(self):
        self.w.close()

    def test_offer(self):
        q = self.w.service.quote(co("ada"), TODAY)
        self.assertEqual(q["verdict"], "OFFER")
        self.assertEqual(q["instrument"], "authorise_hold")
        self.assertEqual(q["risk_bearer"], "paypal")

    def test_defer_is_pay_before_ship(self):
        q = self.w.service.quote(co("ben"), TODAY)
        self.assertEqual(q["verdict"], "DEFER")
        self.assertEqual(q["instrument"], "reservation")
        self.assertIn("PAY BEFORE SHIP", q["fulfilment"])
        self.assertEqual(q["risk_bearer"], "nobody")

    def test_decline_quotes_a_safe_amount(self):
        q = self.w.service.quote(co("cleo"), TODAY)
        self.assertEqual(q["verdict"], "DECLINE")
        self.assertEqual(q["instrument"], "none")
        self.assertIsNotNone(q["safe_amount_minor"])
        self.assertLess(q["safe_amount_minor"], q["amount_minor"])
        self.assertTrue(q["overridable"])

    def test_decline_proposes_nothing(self):
        p = self.w.service.propose(co("cleo"), TODAY)
        self.assertFalse(p["approval_required"])
        self.assertNotIn("token", p)


class TestApprovalGate(unittest.TestCase):
    def setUp(self):
        self.w = Wired()

    def tearDown(self):
        self.w.close()

    def test_nothing_moves_without_approval(self):
        p = self.w.service.propose(co("ben"), TODAY)
        self.assertTrue(p["approval_required"])
        self.assertEqual(self.w.gateway.calls, [], "no gateway call before consent")

    def test_a_token_for_a_different_amount_is_refused(self):
        p = self.w.service.propose(co("ben"), TODAY)
        args = dict(p["proposal"])
        args["amount_minor"] = 99900          # swap the amount, keep the token
        with self.assertRaises(ApprovalError):
            self.w.service.execute("create_reservation", args, p["token"])
        self.assertEqual(self.w.gateway.calls, [])

    def test_a_token_cannot_be_replayed(self):
        p = self.w.service.propose(co("ben"), TODAY)
        args = dict(p["proposal"])
        self.w.service.execute("create_reservation", args, p["token"], NOW)
        with self.assertRaises(ApprovalError):
            self.w.service.execute("create_reservation", args, p["token"], NOW)


class TestTheReservationLifecycle(unittest.TestCase):
    def setUp(self):
        self.w = Wired()
        p = self.w.service.propose(co("ben"), TODAY)
        self.args = dict(p["proposal"])
        self.result = self.w.service.execute("create_reservation", self.args,
                                             p["token"], NOW)
        self.rid = self.result["reservation"]["id"]

    def tearDown(self):
        self.w.close()

    def test_reserving_creates_a_real_invoice_due_on_payday(self):
        self.assertEqual(self.result["state"], "RESERVED")
        self.assertTrue(self.result["invoice"]["id"].startswith("INV2-"))
        self.assertEqual(self.result["invoice"]["due_date"], self.args["due_date"])

    def test_the_merchant_cannot_ship_before_payment(self):
        with self.assertRaises(ReservationError):
            self.w.service.fulfil(self.rid, NOW)
        self.assertEqual(self.w.service.reservations.get(self.rid)["state"], "RESERVED")

    def test_payment_then_shipping(self):
        inv = self.result["invoice"]["id"]
        r = self.w.service.mark_paid(inv, "PAY-ABC", NOW)
        self.assertIs(r.state, State.PAID)
        out = self.w.service.fulfil(self.rid, NOW)
        self.assertEqual(out["state"], "FULFILLED")

    def test_a_retried_webhook_is_harmless(self):
        inv = self.result["invoice"]["id"]
        for _ in range(3):
            self.w.service.mark_paid(inv, "PAY-ABC", NOW)
        row = self.w.service.reservations.get(self.rid)
        self.assertEqual(row["state"], "PAID")
        self.assertEqual(sum(e["kind"] == "paid" for e in row["events"]), 1)

    def test_an_unpaid_hold_expires_and_releases(self):
        row = self.w.service.reservations.get(self.rid)
        later = datetime.fromisoformat(row["hold_until"]) + timedelta(hours=1)
        expired = self.w.service.expire_overdue(later)
        self.assertIn(self.rid, expired)
        self.assertEqual(self.w.service.reservations.get(self.rid)["state"], "EXPIRED")

    def test_a_paid_reservation_never_expires(self):
        self.w.service.mark_paid(self.result["invoice"]["id"], "PAY-ABC", NOW)
        row = self.w.service.reservations.get(self.rid)
        later = datetime.fromisoformat(row["hold_until"]) + timedelta(days=5)
        self.assertEqual(self.w.service.expire_overdue(later), [])


class TestOfferBranch(unittest.TestCase):
    def setUp(self):
        self.w = Wired()

    def tearDown(self):
        self.w.close()

    def test_an_offer_holds_funds_with_a_three_day_validity(self):
        p = self.w.service.propose(co("ada"), TODAY)
        out = self.w.service.execute("authorise_hold", dict(p["proposal"]), p["token"], NOW)
        self.assertEqual(out["state"], "AUTHORISED")
        self.assertTrue(out["authorisation"]["id"].startswith("AUTH-"))

    def test_capturing_twice_does_not_charge_twice(self):
        p = self.w.service.propose(co("ada"), TODAY)
        out = self.w.service.execute("authorise_hold", dict(p["proposal"]), p["token"], NOW)
        aid = out["authorisation"]["id"]
        first = self.w.gateway.capture_authorisation(aid)
        second = self.w.gateway.capture_authorisation(aid)
        self.assertEqual(first.amount_minor, second.amount_minor)
        self.assertEqual(second.reference, "already captured")


class TestUnknownShopper(unittest.TestCase):
    def setUp(self):
        self.w = Wired()

    def tearDown(self):
        self.w.close()

    def test_a_shopper_with_no_profile_is_told_so(self):
        with self.assertRaises(Exception):
            self.w.service.quote(co("nobody"), TODAY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
