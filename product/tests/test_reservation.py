"""The pay-before-ship promise, tested as an invariant rather than a slogan."""

import unittest
from datetime import date, datetime

from secondthought.domain.reservation import (
    ReservationError, State, new_reservation,
)

NOW = datetime(2026, 11, 1, 9, 0)
HOLD = datetime(2026, 11, 8, 0, 0)


def make(**kw):
    base = dict(id="RES-1", shopper_id="dev", merchant_id="northwind",
                amount_minor=24900, currency="USD", due_date=date(2026, 11, 6),
                hold_until=HOLD, now=NOW)
    base.update(kw)
    return new_reservation(**base)


class TestThePromise(unittest.TestCase):
    def test_a_new_reservation_is_not_shippable(self):
        r = make()
        self.assertIs(r.state, State.RESERVED)
        self.assertFalse(r.owes_shipping)

    def test_you_cannot_ship_before_payment(self):
        r = make()
        with self.assertRaises(ReservationError) as ctx:
            r.fulfil(NOW)
        self.assertIn("PAID", str(ctx.exception))

    def test_you_cannot_ship_an_expired_reservation(self):
        r = make()
        r.expire(datetime(2026, 11, 9))
        with self.assertRaises(ReservationError):
            r.fulfil(datetime(2026, 11, 9, 1))

    def test_payment_makes_it_shippable(self):
        r = make()
        r.pay("PAY-1", NOW)
        self.assertIs(r.state, State.PAID)
        self.assertTrue(r.owes_shipping)
        r.fulfil(NOW)
        self.assertIs(r.state, State.FULFILLED)

    def test_you_cannot_ship_twice(self):
        r = make()
        r.pay("PAY-1", NOW)
        r.fulfil(NOW)
        with self.assertRaises(ReservationError):
            r.fulfil(NOW)


class TestPaymentHandling(unittest.TestCase):
    def test_a_retried_webhook_does_not_double_pay(self):
        r = make()
        r.pay("PAY-1", NOW)
        r.pay("PAY-1", NOW)                       # same reference, delivered again
        self.assertIs(r.state, State.PAID)
        self.assertEqual(sum(e.kind == "paid" for e in r.events), 1)

    def test_a_second_different_payment_is_refused(self):
        r = make()
        r.pay("PAY-1", NOW)
        with self.assertRaises(ReservationError):
            r.pay("PAY-2", NOW)

    def test_you_cannot_pay_an_expired_reservation(self):
        r = make()
        r.expire(datetime(2026, 11, 9))
        with self.assertRaises(ReservationError):
            r.pay("PAY-1", datetime(2026, 11, 9, 1))


class TestExpiryAndCancellation(unittest.TestCase):
    def test_expiry_is_refused_before_the_hold_ends(self):
        r = make()
        with self.assertRaises(ReservationError):
            r.expire(datetime(2026, 11, 7))       # one day early

    def test_a_shopper_can_cancel_before_paying(self):
        r = make()
        r.cancel(NOW, "changed my mind")
        self.assertIs(r.state, State.RELEASED)
        with self.assertRaises(ReservationError):
            r.fulfil(NOW)

    def test_a_paid_order_can_be_refunded(self):
        r = make()
        r.pay("PAY-1", NOW)
        r.refund(NOW)
        self.assertIs(r.state, State.REFUNDED)

    def test_a_bad_reservation_is_refused_at_creation(self):
        with self.assertRaises(ReservationError):
            make(amount_minor=0)
        with self.assertRaises(ReservationError):
            make(hold_until=datetime(2026, 10, 1))

    def test_every_transition_is_logged(self):
        r = make()
        r.pay("PAY-1", NOW)
        r.fulfil(NOW)
        self.assertEqual([e.kind for e in r.events],
                         ["reserved", "paid", "fulfilled"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestWebhookRetriesAfterShipping(unittest.TestCase):
    def test_a_retry_after_fulfilment_is_ignored_not_fatal(self):
        """PayPal may deliver the same event again after we already shipped."""
        r = make()
        r.pay("PAY-1", NOW)
        r.fulfil(NOW)
        r.pay("PAY-1", NOW)                     # late duplicate delivery
        self.assertIs(r.state, State.FULFILLED)
        self.assertEqual(sum(e.kind == "paid" for e in r.events), 1)
