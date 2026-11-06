"""V5, part two — no unauthenticated money action, by any route.

The pass condition is absolute: nothing moves without a token that matches the
exact tool and the exact arguments, issued to this session, unspent, unexpired.
Every way of failing that is a test here, including the two tool names V5 uses,
which this product deliberately does not recognise.
"""

import io
import json
import unittest

from secondthought.app.approvals import ApprovalGate
from secondthought.config import AppSettings, PayPalSettings
from secondthought.infra.paypal_live import PayPalLiveGateway
from secondthought.interfaces.http import App


class Client:
    def __init__(self, app, ip="198.51.100.21"):
        self.app = app
        self.ip = ip
        self.cookie = ""

    def call(self, path, method="GET", body=None, query=""):
        raw = json.dumps(body).encode() if body else b""
        env = {"REQUEST_METHOD": method, "PATH_INFO": path, "QUERY_STRING": query,
               "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
               "REMOTE_ADDR": self.ip}
        if self.cookie:
            env["HTTP_COOKIE"] = self.cookie
        out = {}

        def sr(status, headers):
            out["status"] = status
            out["headers"] = dict(headers)

        payload = b"".join(self.app(env, sr))
        set_cookie = out["headers"].get("Set-Cookie", "")
        if set_cookie:
            self.cookie = set_cookie.split(";")[0]
        return out["status"], json.loads(payload)


class NoUnauthenticatedMoneyAction(unittest.TestCase):
    def setUp(self):
        self.app = App(AppSettings(approval_secret="test-secret"))
        self.c = Client(self.app)
        self.c.call("/api/session")
        _, plan = self.c.call("/api/plan", "POST", {"persona": "maya"})
        self.plan = plan

    def tearDown(self):
        self.app.close()

    def _execute(self, payload):
        return self.c.call("/api/execute", "POST", payload)

    # -- 5. the tool names V5 uses are refused, not quietly mapped ---------
    def test_the_names_from_the_spec_are_unknown_tools_not_shortcuts(self):
        for name in ("create_scheduled_invoice", "authorize_payment",
                     "capture_payment", "refund", "../../etc/passwd", ""):
            status, out = self._execute({"tool": name})
            self.assertEqual(status, "400 Bad Request", f"{name!r} was not refused")
            self.assertEqual(out["error"], "unknown tool")
            self.assertIn("create_reservation", out["accepted"])

    def test_a_valid_tool_with_no_token_is_forbidden(self):
        status, out = self._execute({"tool": self.plan["tool"],
                                     "args": self.plan["proposal"]})
        self.assertEqual(status, "403 Forbidden")
        self.assertEqual(out["error"], "approval required")

    def test_a_made_up_token_is_forbidden(self):
        for token in ("deadbeef", "0" * 32, self.plan["token"][:-1] + "f",
                      " " + self.plan["token"]):
            status, out = self._execute({"tool": self.plan["tool"],
                                         "args": self.plan["proposal"], "token": token})
            self.assertEqual(status, "403 Forbidden", f"{token!r} was accepted")

    def test_an_altered_amount_is_forbidden(self):
        args = dict(self.plan["proposal"])
        args["amount_minor"] += 1
        status, out = self._execute({"tool": self.plan["tool"], "args": args,
                                     "token": self.plan["token"]})
        self.assertEqual(status, "403 Forbidden")
        self.assertIn("does not match", out["reason"])

    def test_an_altered_due_date_is_forbidden(self):
        if "due_date" not in self.plan["proposal"]:
            self.skipTest("this persona has no invoice due date")
        args = dict(self.plan["proposal"])
        args["due_date"] = "2027-06-01"
        status, _out = self._execute({"tool": self.plan["tool"], "args": args,
                                      "token": self.plan["token"]})
        self.assertEqual(status, "403 Forbidden")

    def test_a_token_cannot_be_spent_twice(self):
        payload = {"tool": self.plan["tool"], "args": self.plan["proposal"],
                   "token": self.plan["token"]}
        first, _ = self._execute(payload)
        self.assertEqual(first, "200 OK")
        second, out = self._execute(payload)
        self.assertEqual(second, "403 Forbidden", "a replay was accepted")
        self.assertIn("already been used", out["reason"])

    def test_an_expired_token_is_forbidden(self):
        session = self.app.sessions.read_cookie(self.c.cookie.split("=", 1)[1])
        session.approvals = ApprovalGate(ttl_seconds=-1, secret=session.secret)
        _, plan = self.c.call("/api/plan", "POST", {"persona": "maya"})
        status, out = self._execute({"tool": plan["tool"], "args": plan["proposal"],
                                     "token": plan["token"]})
        self.assertEqual(status, "403 Forbidden")
        self.assertIn("expired", out["reason"])

    def test_a_token_is_bound_to_its_tool(self):
        other = "authorise_hold" if self.plan["tool"] == "create_reservation" \
            else "create_reservation"
        status, _out = self._execute({"tool": other, "args": self.plan["proposal"],
                                      "token": self.plan["token"]})
        self.assertEqual(status, "403 Forbidden")

    # -- and the honest path still works -----------------------------------
    def test_the_gateway_is_not_called_until_a_real_token_arrives(self):
        before = len(self.app.gateway.calls)
        self._execute({"tool": self.plan["tool"], "args": self.plan["proposal"]})
        self.assertEqual(len(self.app.gateway.calls), before,
                         "a refused call still reached PayPal")
        status, _ = self._execute({"tool": self.plan["tool"],
                                   "args": self.plan["proposal"],
                                   "token": self.plan["token"]})
        self.assertEqual(status, "200 OK")
        self.assertEqual(len(self.app.gateway.calls), before + 1)

    def test_a_non_object_args_field_is_refused_not_crashed(self):
        status, out = self._execute({"tool": self.plan["tool"], "args": "not-an-object",
                                     "token": self.plan["token"]})
        self.assertEqual(status, "403 Forbidden")
        self.assertIn("error", out)

    def test_every_refusal_is_recorded_with_its_reason(self):
        self._execute({"tool": "create_scheduled_invoice"})
        self._execute({"tool": self.plan["tool"], "args": self.plan["proposal"]})
        reasons = [a["reason"] for a in self.app.attempts]
        self.assertIn("unknown tool", reasons)
        self.assertIn("no token", reasons)


class OtherSurface(unittest.TestCase):
    def setUp(self):
        self.app = App(AppSettings(approval_secret="test-secret"))
        self.c = Client(self.app)

    def tearDown(self):
        self.app.close()

    def test_there_is_no_route_that_moves_money_on_a_get(self):
        for path in ("/api/execute", "/api/plan", "/api/profile"):
            status, _ = self.c.call(path)
            self.assertIn(status, ("404 Not Found", "405 Method Not Allowed",
                                   "400 Bad Request"), path)
        self.assertEqual(self.app.gateway.calls, [])

    def test_an_oversized_body_does_not_wedge_the_worker(self):
        raw = json.dumps({"profile": {"x": "a" * 200_000}}).encode()
        env = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api/profile", "QUERY_STRING": "",
               "CONTENT_LENGTH": str(len(raw)), "wsgi.input": io.BytesIO(raw),
               "REMOTE_ADDR": "198.51.100.31"}
        payload = b"".join(self.app(env, lambda s, h: None))
        self.assertIn(b"error", payload)

    def test_responses_are_not_cacheable(self):
        env = {"REQUEST_METHOD": "GET", "PATH_INFO": "/api/quote", "QUERY_STRING": "",
               "CONTENT_LENGTH": "0", "wsgi.input": io.BytesIO(b""),
               "REMOTE_ADDR": "198.51.100.32"}
        seen = {}

        def sr(status, headers):
            seen.update(dict(headers))

        b"".join(self.app(env, sr))
        self.assertEqual(seen.get("Cache-Control"), "no-store")
        self.assertEqual(seen.get("X-Content-Type-Options"), "nosniff")

    def test_a_500_does_not_echo_internals(self):
        def explode(_environ):
            raise RuntimeError("secret detail: /home/user/db.sqlite3 password=hunter2")
        original = self.app._handle
        self.app._handle = explode
        try:
            payload = b"".join(self.app({"REQUEST_METHOD": "GET", "PATH_INFO": "/x"},
                                        lambda s, h: None))
        finally:
            self.app._handle = original
        self.assertNotIn(b"hunter2", payload)
        self.assertNotIn(b"/home/user", payload)
        self.assertIn(b"internal error", payload)


class GatewaySelection(unittest.TestCase):
    def test_configured_paypal_uses_the_sandbox_adapter(self):
        app_ = App(AppSettings(
            approval_secret="test-secret",
            paypal=PayPalSettings(client_id="client", client_secret="secret",
                                  env="sandbox")))
        try:
            self.assertIsInstance(app_.gateway, PayPalLiveGateway)
        finally:
            app_.close()


if __name__ == "__main__":
    unittest.main()
