"""The live adapter, driven by a fake transport — request construction, offline.

V3's pass condition is that five specific calls reach PayPal and leave five
specific artifacts. These tests check the half that can be checked without an
account: that the bytes we send are the bytes the API documents, and that the
responses we get back are parsed into the right objects.

What they cannot check is whether the sandbox accepted them. Only the dashboard
can answer that, which is why V3 is not marked passed until a human looks.
"""

import base64
import unittest
from datetime import date

from secondthought.app.ports import GatewayError, PaymentGateway
from secondthought.config import PayPalSettings
from secondthought.infra.fake_paypal import FakePayPal
from secondthought.infra.gateway import SimulatedGateway
from secondthought.infra.paypal_live import PayPalLiveGateway, _minor, money

SANDBOX = PayPalSettings(client_id="test-client-id", client_secret="test-secret",
                         env="sandbox")


def wired(**kwargs):
    fake = FakePayPal()
    gw = PayPalLiveGateway(SANDBOX, transport=fake, poll_every=0,
                           on_approval=kwargs.pop("on_approval", None), **kwargs)
    return gw, fake


def header(fake, path_fragment, name):
    for r in fake.requests:
        if path_fragment in r["path"]:
            return r["headers"].get(name.lower(), "")
    return ""


class OAuth(unittest.TestCase):
    def test_it_sends_http_basic_client_credentials(self):
        gw, fake = wired()
        gw.http.token(force=True)
        r = fake.requests[0]
        self.assertEqual(r["path"], "/v1/oauth2/token")
        expected = base64.b64encode(b"test-client-id:test-secret").decode()
        self.assertEqual(r["headers"]["authorization"], f"Basic {expected}")

    def test_the_token_is_cached_not_refetched(self):
        gw, fake = wired()
        first = gw.http.token()
        second = gw.http.token()
        self.assertEqual(first["access_token"], second["access_token"])
        token_calls = [r for r in fake.requests if r["path"] == "/v1/oauth2/token"]
        self.assertEqual(len(token_calls), 1, "a second call refetched the token")
        self.assertTrue(second.get("cached"))

    def test_the_expiry_is_visible_and_the_reuse_window_is_shortened(self):
        gw, _fake = wired()
        fresh = gw.http.token()
        self.assertEqual(fresh["expires_in"], 32400)      # what PayPal actually said
        cached = gw.http.token()
        # we retire the token a minute early, so the reported window is smaller
        self.assertLess(cached["expires_in"], 32400)
        self.assertGreater(cached["expires_in"], 32000)


class Orders(unittest.TestCase):
    def test_the_order_is_created_with_authorize_intent_and_a_request_id(self):
        gw, fake = wired()
        gw.create_order(amount_minor=24900, currency="USD", reference="bt-001",
                        request_id="st-auth-bt-001")
        r = next(x for x in fake.requests if x["path"] == "/v2/checkout/orders")
        self.assertEqual(r["body"]["intent"], "AUTHORIZE")
        self.assertEqual(r["body"]["purchase_units"][0]["amount"]["value"], "249.00")
        self.assertEqual(r["headers"]["paypal-request-id"], "st-auth-bt-001")
        self.assertEqual(r["headers"]["content-type"], "application/json")

    def test_the_approval_url_is_handed_to_the_caller(self):
        seen = []
        gw, _fake = wired(on_approval=seen.append)
        gw.authorise(amount_minor=24900, currency="USD", reference="bt-001")
        self.assertTrue(seen and "checkoutnow" in seen[0],
                        f"no approval URL surfaced: {seen}")

    def test_authorise_returns_the_authorisation_id_from_the_payments_object(self):
        gw, _fake = wired()
        auth = gw.authorise(amount_minor=24900, currency="USD", reference="bt-001")
        self.assertTrue(auth.id.startswith("AUTH-DRY"), auth.id)
        self.assertEqual(auth.status, "CREATED")
        self.assertEqual(auth.expires_on, date(2026, 11, 5))
        self.assertEqual(auth.amount_minor, 24900)

    def test_capture_asks_for_the_full_representation_and_parses_the_amount(self):
        gw, fake = wired()
        auth = gw.authorise(amount_minor=24900, currency="USD", reference="bt-001")
        cap = gw.capture_authorisation(auth.id)
        r = next(x for x in fake.requests if x["path"].endswith("/capture"))
        self.assertEqual(r["body"], {"final_capture": True})
        self.assertEqual(r["headers"]["prefer"], "return=representation")
        self.assertEqual(cap.status, "COMPLETED")
        self.assertEqual(cap.amount_minor, 24900, "amount came back wrong")
        self.assertTrue(cap.id.startswith("CAP-DRY"))


class Void(unittest.TestCase):
    def test_a_204_with_no_body_counts_as_a_successful_void(self):
        gw, fake = wired()
        auth = gw.authorise(amount_minor=24900, currency="USD", reference="bt-001")
        gw.void_authorisation(auth.id)          # must not raise on an empty 204
        r = next(x for x in fake.requests if x["path"].endswith("/void"))
        self.assertEqual(r["method"], "POST")
        self.assertEqual(fake.auths[auth.id]["status"], "VOIDED")

    def test_a_void_that_does_not_report_voided_is_an_error(self):
        gw, fake = wired()
        with self.assertRaises(GatewayError):
            gw.void_authorisation("AUTH-DOES-NOT-EXIST")


class Invoices(unittest.TestCase):
    def test_the_due_date_goes_into_payment_term_due_date(self):
        gw, fake = wired()
        gw.create_invoice(amount_minor=24900, currency="USD",
                          due_date=date(2026, 11, 6), reference="bt-001")
        r = next(x for x in fake.requests if x["path"] == "/v2/invoicing/invoices")
        term = r["body"]["detail"]["payment_term"]
        self.assertEqual(term["term_type"], "DUE_ON_DATE_SPECIFIED")
        self.assertEqual(term["due_date"], "2026-11-06")
        self.assertEqual(r["body"]["items"][0]["unit_amount"]["value"], "249.00")

    def test_the_id_is_parsed_from_an_href_because_there_is_no_id(self):
        gw, fake = wired()
        inv = gw.create_invoice(amount_minor=24900, currency="USD",
                               due_date=date(2026, 11, 6), reference="bt-001")
        self.assertTrue(inv.id.startswith("INV2-DRY"), inv.id)
        self.assertIn(inv.id, fake.invoices)

    def test_the_invoice_reads_back_with_the_due_date_it_was_given(self):
        gw, _fake = wired()
        inv = gw.create_invoice(amount_minor=24900, currency="USD",
                               due_date=date(2026, 11, 6), reference="bt-001")
        self.assertEqual(inv.due_date, date(2026, 11, 6))
        self.assertEqual(inv.status, "DRAFT")
        self.assertEqual(inv.amount_minor, 24900)

    def test_sending_moves_it_out_of_draft(self):
        gw, _fake = wired()
        inv = gw.create_invoice(amount_minor=24900, currency="USD",
                               due_date=date(2026, 11, 6), reference="bt-001")
        gw.send_invoice(inv.id)
        self.assertEqual(gw.get_invoice(inv.id).status, "UNPAID")


class Idempotency(unittest.TestCase):
    def test_the_same_request_id_does_not_create_a_second_order(self):
        gw, fake = wired()
        a = gw.create_order(amount_minor=24900, currency="USD",
                            reference="bt-1", request_id="same-id")
        b = gw.create_order(amount_minor=24900, currency="USD",
                            reference="bt-1", request_id="same-id")
        self.assertEqual(a["id"], b["id"])
        self.assertEqual(len(fake.orders), 1, "a retry created a second order")

    def test_a_different_request_id_does_create_a_second_order(self):
        gw, fake = wired()
        a = gw.create_order(amount_minor=24900, currency="USD",
                            reference="bt-1", request_id="id-one")
        b = gw.create_order(amount_minor=24900, currency="USD",
                            reference="bt-1", request_id="id-two")
        self.assertNotEqual(a["id"], b["id"])
        self.assertEqual(len(fake.orders), 2)


class Safety(unittest.TestCase):
    def test_direct_token_requests_are_also_blocked_for_live(self):
        live = PayPalSettings(client_id="x", client_secret="y", env="live")
        fake = FakePayPal()
        gw = PayPalLiveGateway(live, transport=fake)
        with self.assertRaises(GatewayError):
            gw.http.token(force=True)
        self.assertEqual(fake.requests, [])

    def test_it_refuses_to_run_against_the_live_environment(self):
        live = PayPalSettings(client_id="x", client_secret="y", env="live")
        gw = PayPalLiveGateway(live, transport=FakePayPal())
        with self.assertRaises(GatewayError) as ctx:
            gw.create_order(amount_minor=100, currency="USD", reference="r",
                            request_id="rid")
        self.assertIn("refusing", str(ctx.exception))
        self.assertEqual(gw.http.settings.base_url, "https://api-m.paypal.com")

    def test_the_live_gateway_satisfies_the_same_protocol_as_the_simulated_one(self):
        gw, _fake = wired()
        for impl in (gw, SimulatedGateway()):
            for name in [n for n in dir(PaymentGateway) if not n.startswith("_")]:
                self.assertTrue(hasattr(impl, name), f"{impl} is missing {name}")


class Money(unittest.TestCase):
    def test_minor_units_never_touch_floating_point(self):
        self.assertEqual(money(24900), "249.00")
        self.assertEqual(money(5), "0.05")
        self.assertEqual(money(0), "0.00")
        self.assertEqual(money(123456789), "1234567.89")

    def test_parsing_round_trips(self):
        for value in ("249.00", "0.05", "1000.00"):
            self.assertEqual(money(_minor(value)), value)


class DueDateIsComputed(unittest.TestCase):
    def test_the_invoice_due_date_is_the_payday_the_engine_chose(self):
        import demo
        due, math_row = demo.invoice_due_date(date(2026, 11, 2), 24900)
        self.assertEqual(math_row["verdict"], "DEFER")
        self.assertEqual(due.isoformat(), math_row["next_payday"])

    def test_it_moves_when_today_moves_so_it_is_not_hardcoded(self):
        import demo
        a, _ = demo.invoice_due_date(date(2026, 11, 2), 24900)
        b, _ = demo.invoice_due_date(date(2026, 11, 9), 24900)
        self.assertNotEqual(a, b)


if __name__ == "__main__":
    unittest.main()
