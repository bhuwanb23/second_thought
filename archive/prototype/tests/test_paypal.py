"""The PayPal adapter: shapes, idempotency, webhook verification, error paths."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from paypal import (  # noqa: E402
    PayPalClient, PayPalError, SimulatedTransport, client_from_env,
)


class TestSimulatedClient(unittest.TestCase):
    def setUp(self):
        self.client = PayPalClient(transport=SimulatedTransport(), webhook_id="WH-1")

    def test_reports_its_mode(self):
        self.assertEqual(self.client.mode, "simulated")

    def test_order_shape(self):
        o = self.client.create_order(24_900, reference="REF-1")
        self.assertTrue(o["id"].startswith("SIM-"))
        self.assertEqual(o["status"], "PAYER_ACTION_REQUIRED")
        self.assertEqual(o["intent"], "AUTHORIZE")
        self.assertEqual(o["purchase_units"][0]["amount"]["value"], "249.00")
        self.assertTrue(any(l["rel"] == "payer-action" for l in o["links"]))

    def test_amount_formatting_has_two_decimals(self):
        o = self.client.create_order(5)
        self.assertEqual(o["purchase_units"][0]["amount"]["value"], "0.05")
        o2 = self.client.create_order(100_000)
        self.assertEqual(o2["purchase_units"][0]["amount"]["value"], "1000.00")

    def test_authorize_then_capture_chain(self):
        o = self.client.create_order(24_900)
        auth = self.client.authorize_order(o["id"])
        auth_id = auth["purchase_units"][0]["payments"]["authorizations"][0]["id"]
        self.assertTrue(auth_id.startswith("AUTH-"))
        cap = self.client.capture_authorization(auth_id, 24_900)
        self.assertEqual(cap["status"], "CAPTURED")

    def test_void(self):
        o = self.client.create_order(24_900)
        auth = self.client.authorize_order(o["id"])
        auth_id = auth["purchase_units"][0]["payments"]["authorizations"][0]["id"]
        self.assertEqual(self.client.void_authorization(auth_id)["status"], "VOIDED")

    def test_invoice_carries_the_due_date(self):
        inv = self.client.create_invoice(24_900, "2026-11-06", note="payday")
        self.assertTrue(inv["id"].startswith("INV2-"))
        self.assertEqual(inv["detail"]["payment_term"]["due_date"], "2026-11-06")
        self.assertEqual(inv["detail"]["currency_code"], "USD")

    def test_webhook_verification_accepts_and_rejects(self):
        good = {"paypal-transmission-id": "abc", "paypal-transmission-time": "t",
                "paypal-cert-url": "u", "paypal-auth-algo": "SHA256withRSA",
                "paypal-transmission-sig": "s"}
        self.assertTrue(self.client.verify_webhook(good, {"event_type": "X"}))
        self.assertFalse(self.client.verify_webhook({}, {"event_type": "X"}))


class TestIdempotency(unittest.TestCase):
    def test_same_request_id_does_not_create_two_orders(self):
        client = PayPalClient(transport=SimulatedTransport())
        a = client.create_order(24_900, request_id="fixed-request-id")
        b = client.create_order(24_900, request_id="fixed-request-id")
        self.assertEqual(a["id"], b["id"])

    def test_different_request_ids_do(self):
        client = PayPalClient(transport=SimulatedTransport())
        a = client.create_order(24_900, request_id="one")
        b = client.create_order(24_900, request_id="two")
        self.assertNotEqual(a["id"], b["id"])

    def test_every_post_carries_a_request_id(self):
        transport = SimulatedTransport()
        client = PayPalClient(transport=transport)
        client.create_order(24_900)
        client.create_invoice(24_900, "2026-11-06")
        self.assertTrue(all(c.get("request_id") for c in transport.calls),
                        "every POST must send PayPal-Request-Id")


class TestErrorPaths(unittest.TestCase):
    def test_http_error_is_wrapped(self):
        class Boom:
            mode = "live"

            def request(self, *a, **k):
                raise PayPalError(422, '{"name":"UNPROCESSABLE_ENTITY"}', "/v2/x")

        client = PayPalClient(transport=Boom())
        with self.assertRaises(PayPalError) as ctx:
            client.create_order(100)
        self.assertEqual(ctx.exception.status, 422)

    def test_client_falls_back_to_simulation_without_credentials(self):
        old_id = os.environ.pop("PAYPAL_CLIENT_ID", None)
        old_sec = os.environ.pop("PAYPAL_CLIENT_SECRET", None)
        try:
            self.assertEqual(client_from_env().mode, "simulated")
        finally:
            if old_id: os.environ["PAYPAL_CLIENT_ID"] = old_id
            if old_sec: os.environ["PAYPAL_CLIENT_SECRET"] = old_sec

    def test_forced_simulation_even_with_credentials(self):
        os.environ["PAYPAL_CLIENT_ID"] = "fake"
        os.environ["PAYPAL_CLIENT_SECRET"] = "fake"
        try:
            self.assertEqual(client_from_env(force_simulated=True).mode, "simulated")
        finally:
            os.environ.pop("PAYPAL_CLIENT_ID", None)
            os.environ.pop("PAYPAL_CLIENT_SECRET", None)


class TestEndpointsAreSandboxOnly(unittest.TestCase):
    def test_no_live_url_is_ever_constructed(self):
        import paypal as mod
        self.assertEqual(mod.SANDBOX, "https://api-m.sandbox.paypal.com")
        with open(mod.__file__) as f:
            source = f.read()
        # the live host may only appear as a named constant, never used in a call
        self.assertNotIn("api-m.paypal.com\"", source.replace(mod.LIVE, ""))


if __name__ == "__main__":
    unittest.main(verbosity=2)
