"""P5.6 / V6.4 — a webhook with a bad signature must be refused, and visibly.

The keys and the signing helper live in `test_rsa.py`; this file is about what the
verifier and the route *do* with a delivery that cannot be trusted.
"""

import io
import json
import unittest

from secondthought.config import AppSettings, PayPalSettings
from secondthought.domain.reservation import ReservationError
from secondthought.infra.webhook import Rejection, WebhookVerifier
from secondthought.interfaces.http import App
from secondthought.interfaces.webhook_api import WebhookAPI
from tests.test_rsa import BODY, CERT_PEM, EVENT, K, WEBHOOK_ID, headers

class TheVerifier(unittest.TestCase):
    def setUp(self):
        self.seen_certs = []

        def lookup(url):
            self.seen_certs.append(url)
            return CERT_PEM

        self.v = WebhookVerifier(WEBHOOK_ID, cert_lookup=lookup)

    def test_a_correctly_signed_event_is_accepted_once(self):
        event = self.v.verify(headers(body=BODY), BODY)
        self.assertEqual(event["event_type"], "INVOICING.INVOICE.PAID")
        self.assertEqual(len(self.v.log), 1)
        self.assertTrue(self.v.log[0]["ok"])

    def test_a_bad_signature_is_refused_and_logged(self):
        bad = headers(sig=b"\x00" * K)
        with self.assertRaises(Rejection) as ctx:
            self.v.verify(bad, BODY)
        self.assertEqual(ctx.exception.reason, "signature does not verify")
        self.assertFalse(self.v.log[-1]["ok"], "the refusal was not recorded")
        self.assertIn("signature does not verify", json.dumps(self.v.rejections))

    def test_a_signature_for_a_different_body_is_refused(self):
        other = json.dumps({**EVENT, "id": "WH-EVT-2"}).encode()
        with self.assertRaises(Rejection):
            self.v.verify(headers(body=other), BODY)

    def test_a_replay_is_refused(self):
        self.v.verify(headers(body=BODY), BODY)
        with self.assertRaises(Rejection) as ctx:
            self.v.verify(headers(body=BODY), BODY)
        self.assertEqual(ctx.exception.reason, "replayed transmission")

    def test_missing_headers_are_named(self):
        h = headers(body=BODY)
        del h["PAYPAL-TRANSMISSION-SIG"]
        with self.assertRaises(Rejection) as ctx:
            self.v.verify(h, BODY)
        self.assertIn("PAYPAL-TRANSMISSION-SIG", ctx.exception.detail)

    def test_a_cert_url_from_another_host_is_refused_before_it_is_fetched(self):
        with self.assertRaises(Rejection) as ctx:
            self.v.verify(headers(body=BODY, cert_url="https://evil.example/cert.pem"),
                          BODY)
        self.assertIn("not PayPal", ctx.exception.reason + ctx.exception.detail)
        self.assertEqual(self.seen_certs, [], "an untrusted URL was still fetched")

    def test_a_plain_http_cert_url_is_refused(self):
        with self.assertRaises(Rejection):
            self.v.verify(headers(body=BODY, cert_url="http://api.paypal.com/c.pem"), BODY)

    def test_a_cert_that_cannot_be_fetched_fails_closed(self):
        def broken(_url):
            raise Rejection("cert could not be fetched", "timeout")
        v = WebhookVerifier(WEBHOOK_ID, cert_lookup=broken)
        with self.assertRaises(Rejection):
            v.verify(headers(body=BODY), BODY)
        self.assertEqual(v.summary()["rejected"], 1)

    def test_no_webhook_id_config_means_everything_is_refused(self):
        v = WebhookVerifier("", cert_lookup=lambda _u: CERT_PEM)
        with self.assertRaises(Rejection) as ctx:
            v.verify(headers(body=BODY), BODY)
        self.assertIn("no webhook id", ctx.exception.reason)

    def test_a_payment_after_expiry_is_acknowledged_without_reopening(self):
        api = WebhookAPI("webhook-id")

        class ExpiredService:
            def mark_paid(self, _invoice_id, _event_id):
                raise ReservationError("cannot do that from EXPIRED")

        outcome = api.apply(EVENT, lambda: ExpiredService())
        self.assertFalse(outcome["applied"])
        self.assertTrue(outcome["reconciliation_required"])
        self.assertEqual(len(api.reconciliation), 1)


class TheRoute(unittest.TestCase):
    def setUp(self):
        self.app = App(AppSettings(approval_secret="test-secret", diag_token="diag-123",
                                   paypal=__import__("secondthought.config",
                                                     fromlist=["PayPalSettings"])
                                   .PayPalSettings(client_id="a", client_secret="b",
                                                   webhook_id=WEBHOOK_ID)),
                       cert_lookup=lambda _u: CERT_PEM)

    def tearDown(self):
        self.app.close()

    def post(self, raw, hdrs, path="/api/webhook"):
        environ = {"REQUEST_METHOD": "POST", "PATH_INFO": path, "QUERY_STRING": "",
                   "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
                   "REMOTE_ADDR": "198.51.100.41"}
        for k, v in hdrs.items():
            environ["HTTP_" + k.replace("-", "_").upper()] = v
        seen = {}

        def sr(status, headers):
            seen["status"] = status
            seen["headers"] = dict(headers)

        payload = b"".join(self.app(environ, sr))
        return seen["status"], json.loads(payload)

    def test_a_bad_signature_gets_400_and_is_visible_on_diagnostics(self):
        status, body = self.post(BODY, headers(sig=b"\x00" * K))
        self.assertEqual(status, "400 Bad Request")
        self.assertFalse(body["received"])
        self.assertEqual(body["reason"], "signature does not verify")

        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/diagnostics",
                   "QUERY_STRING": "", "CONTENT_LENGTH": "0",
                   "wsgi.input": io.BytesIO(b""), "REMOTE_ADDR": "198.51.100.41",
                   "HTTP_X_DIAG_TOKEN": "diag-123"}
        payload = b"".join(self.app(environ, lambda s, h: None))
        diag = json.loads(payload)
        self.assertEqual(diag["webhooks"]["rejected"], 1)
        self.assertIn("signature does not verify", json.dumps(diag["webhooks"]["last"]))

    def test_the_rejection_count_is_public_but_the_detail_is_not(self):
        self.post(BODY, headers(sig=b"\x00" * K))
        environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/diagnostics",
                   "QUERY_STRING": "", "CONTENT_LENGTH": "0",
                   "wsgi.input": io.BytesIO(b""), "REMOTE_ADDR": "198.51.100.41"}
        payload = b"".join(self.app(environ, lambda s, h: None))
        public = json.loads(payload)
        self.assertEqual(public["webhooks"]["rejected"], 1, "a visitor cannot see the refusal")
        self.assertNotIn("last", public["webhooks"], "transmission ids leaked publicly")

    def test_a_good_signature_gets_200(self):
        status, body = self.post(BODY, headers(body=BODY))
        self.assertEqual(status, "200 OK", body)
        self.assertTrue(body["received"])

    def test_diagnostics_is_404_without_a_configured_token(self):
        app_ = App(AppSettings(approval_secret="x"), cert_lookup=lambda _u: CERT_PEM)
        try:
            environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/diagnostics",
                       "QUERY_STRING": "", "CONTENT_LENGTH": "0",
                       "wsgi.input": io.BytesIO(b""), "REMOTE_ADDR": "1.2.3.4"}
            out = {}
            b"".join(app_(environ, lambda s, h: out.update({"s": s})))
            self.assertEqual(out["s"], "404 Not Found")
        finally:
            app_.close()

    def test_diagnostics_needs_the_right_token(self):
        app_ = App(AppSettings(approval_secret="x", diag_token="secret-token"),
                   cert_lookup=lambda _u: CERT_PEM)
        try:
            for supplied, expected in (("wrong", "200 OK"),
                                       ("secret-token", "200 OK")):
                environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/diagnostics",
                           "QUERY_STRING": "", "CONTENT_LENGTH": "0",
                           "wsgi.input": io.BytesIO(b""), "REMOTE_ADDR": "1.2.3.4",
                           "HTTP_X_DIAG_TOKEN": supplied}
                out = {}
                b"".join(app_(environ, lambda s, h: out.update({"s": s})))
                self.assertEqual(out["s"], expected)
        finally:
            app_.close()


if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
