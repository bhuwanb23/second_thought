"""V5, part one — two cookie jars, adversarially.

The scenario is a public URL in a submission: judge A plays with it, then judge B
opens it. B must see exactly what the spec says and nothing A did. These tests use
two independent clients with separate cookie strings, because that is what two
browsers are.
"""

import io
import json
import tempfile
import unittest
from pathlib import Path

from secondthought.config import AppSettings, LLMSettings, PayPalSettings
from secondthought.interfaces.http import App

HOSTILE = {"opening_balance": 1_000_000,
           "paydays": [{"due": "2026-11-04", "amount_minor": 9_000_000}],
           "obligations": [{"label": "rent", "due": "2026-11-09",
                            "amount_minor": 4_000_000, "essential": True}]}


class Client:
    """One visitor: a cookie string and an IP."""

    def __init__(self, app, ip="203.0.113.7"):
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


def app(**kwargs):
    return App(AppSettings(approval_secret="test-secret", **kwargs))


class TwoCookieJars(unittest.TestCase):
    def setUp(self):
        self.app = app()
        self.a = Client(self.app, ip="198.51.100.1")
        self.b = Client(self.app, ip="203.0.113.9")

    def tearDown(self):
        self.app.close()

    def test_a_and_b_are_given_different_sessions_and_keys(self):
        self.a.call("/api/session")
        self.b.call("/api/session")
        self.assertNotEqual(self.a.cookie, self.b.cookie)
        sa = self.app.sessions.read_cookie(self.a.cookie.split("=", 1)[1])
        sb = self.app.sessions.read_cookie(self.b.cookie.split("=", 1)[1])
        self.assertIsNot(sa, sb)
        self.assertNotEqual(sa.secret, sb.secret, "sessions share a signing key")

    def test_b_sees_the_untouched_persona_after_a_saves_and_executes(self):
        before_status, before = self.b.call("/api/quote", query="persona=maya")
        self.assertEqual(before_status, "200 OK")
        self.assertEqual(before["verdict"], "DEFER")
        self.assertEqual(before["profile"], "persona-default")

        # A saves a hostile profile and executes a real plan
        status, saved = self.a.call("/api/profile", "POST", {"profile": HOSTILE})
        self.assertEqual(status, "200 OK")
        status, plan = self.a.call("/api/plan", "POST", {"persona": "me"})
        self.assertEqual(status, "200 OK", plan)
        self.assertTrue(plan["approval_required"])
        status, done = self.a.call("/api/execute", "POST",
                                   {"tool": plan["tool"], "args": plan["proposal"],
                                    "token": plan["token"]})
        self.assertEqual(status, "200 OK", done)
        self.assertIn(done["state"], ("RESERVED", "AUTHORISED"),
                      "the plan did not execute for its own session")

        # and B, at the same moment, still sees the spec
        status, after = self.b.call("/api/quote", query="persona=maya")
        self.assertEqual(after["verdict"], before["verdict"],
                         "judge A's profile changed the verdict judge B sees")
        self.assertEqual(after["profile"], "persona-default")

    def test_a_can_still_use_its_own_profile(self):
        self.a.call("/api/profile", "POST", {"profile": HOSTILE})
        status, out = self.a.call("/api/quote", query="persona=me&amount_minor=24900")
        self.assertEqual(status, "200 OK", out)
        self.assertEqual(out["profile"], "session")
        self.assertEqual(out["verdict"], "OFFER")   # a million in the bank

    def test_saving_a_profile_cannot_write_a_persona(self):
        self.a.call("/api/profile", "POST", {"profile": HOSTILE})
        stored = self.app.defaults.get("ben")
        self.assertEqual(stored["opening_balance"], 30_000,
                         "a visitor's write reached the persona store")

    def test_one_session_cannot_execute_anothers_approval(self):
        self.a.call("/api/session")
        _, plan = self.a.call("/api/plan", "POST", {"persona": "maya"})
        self.b.call("/api/session")
        status, out = self.b.call("/api/execute", "POST",
                                  {"tool": plan["tool"], "args": plan["proposal"],
                                   "token": plan["token"]})
        self.assertEqual(status, "403 Forbidden", out)
        self.assertIn("approval refused", out["error"])

    def test_a_tampered_cookie_gets_a_fresh_session_not_someone_elses(self):
        self.a.call("/api/profile", "POST", {"profile": HOSTILE})
        real = self.a.cookie.split("=", 1)[1]
        sid, boot, sig = real.split(".")
        forger = Client(self.app, ip="198.51.100.2")
        forger.cookie = f"st_sid={sid}.{boot}.{'0' * len(sig)}"
        status, out = forger.call("/api/session")
        self.assertEqual(status, "200 OK")
        self.assertFalse(out["session"]["has_profile"],
                         "a forged signature adopted another visitor's session")
        self.assertNotEqual(forger.cookie, self.a.cookie)


class RateLimit(unittest.TestCase):
    def setUp(self):
        self.app = app()
        self.a = Client(self.app, ip="198.51.100.11")
        self.b = Client(self.app, ip="203.0.113.11")

    def tearDown(self):
        self.app.close()

    def test_the_thirty_first_model_call_is_refused_and_the_second_session_is_not(self):
        codes = [self.a.call("/api/extract", "POST", {"text": "rent 1450 on the 28th"})[0]
                 for _ in range(30)]
        self.assertEqual(set(codes), {"200 OK"}, "a legitimate call was throttled early")
        status, out = self.a.call("/api/extract", "POST", {"text": "one more"})
        self.assertEqual(status, "429 Too Many Requests", out)
        self.assertIn("session limit", out["reason"])

        status_b, out_b = self.b.call("/api/extract", "POST", {"text": "rent 1450 on the 28th"})
        self.assertEqual(status_b, "200 OK", "a second session was punished for the first")

    def test_both_sessions_are_counted_separately_even_from_one_network(self):
        b_same_network = Client(self.app, ip="198.51.100.11")
        for _ in range(30):
            self.a.call("/api/extract", "POST", {"text": "x"})
        self.assertEqual(self.a.call("/api/extract", "POST", {"text": "x"})[0],
                         "429 Too Many Requests")
        self.assertEqual(b_same_network.call("/api/extract", "POST", {"text": "x"})[0],
                         "200 OK", "one visitor's budget was spent by another")

    def test_clearing_the_cookie_does_not_buy_a_new_budget(self):
        """The IP cap exists so a cookie-cycling client cannot loop forever."""
        statuses = []
        for _ in range(100):
            client = Client(self.app, ip="198.51.100.13")     # a fresh jar every time
            statuses.append(client.call("/api/profile", "POST", {"profile": HOSTILE})[0])
        self.assertIn("429 Too Many Requests", statuses,
                      "rotating cookies bypassed the limit entirely")
        first_throttle = statuses.index("429 Too Many Requests")
        self.assertGreaterEqual(first_throttle, 30,
                               "the IP cap fired before one session's budget could be used")
        self.assertEqual(first_throttle, 90, "the backstop is not the documented 3x")

    def test_the_window_expires(self):
        now = [1000.0]
        self.app.clock = lambda: now[0]
        for _ in range(30):
            self.a.call("/api/extract", "POST", {"text": "x"})
        self.assertEqual(self.a.call("/api/extract", "POST", {"text": "x"})[0],
                         "429 Too Many Requests")
        now[0] += 601
        self.assertEqual(self.a.call("/api/extract", "POST", {"text": "x"})[0], "200 OK")

    def test_the_persona_buttons_never_consume_the_model_budget(self):
        for _ in range(40):
            self.a.call("/api/quote", query="persona=maya")
        self.assertEqual(self.a.call("/api/extract", "POST", {"text": "x"})[0], "200 OK")


class Healthz(unittest.TestCase):
    def test_it_reveals_booleans_and_nothing_else(self):
        secret_settings = AppSettings(approval_secret="super-secret-value",
                                      diag_token="diag-token-value",
                                      llm=LLMSettings(api_key="sk-live-key-value"),
                                      paypal=PayPalSettings(client_id="client-id-value",
                                                            client_secret="client-secret-value"))
        app_ = App(secret_settings)
        try:
            client = Client(app_)
            status, body = client.call("/healthz")
            self.assertEqual(status, "200 OK")
            text = json.dumps(body)
            for leak in ("super-secret-value", "diag-token-value", "sk-live-key-value",
                         "client-id-value", "client-secret-value"):
                self.assertNotIn(leak, text, f"/healthz leaked {leak}")
            self.assertEqual(set(body), {"status", "ai_mode", "payments_mode", "checks"})
            self.assertTrue(all(isinstance(v, bool) for v in body["checks"].values()))
            self.assertEqual(body["ai_mode"], "llm")
            self.assertEqual(body["payments_mode"], "sandbox")
        finally:
            app_.close()

    def test_it_answers_logged_out(self):
        app_ = app()
        try:
            status, body = Client(app_).call("/healthz")   # no cookie at all
            self.assertEqual(status, "200 OK")
            self.assertEqual(body["status"], "ok")
        finally:
            app_.close()


class Restart(unittest.TestCase):
    """Item 6, in process: a new boot is what a redeploy looks like from inside."""

    def test_an_old_cookie_after_a_restart_yields_a_clean_session(self):
        first = app()
        client = Client(first)
        client.call("/api/profile", "POST", {"profile": HOSTILE})
        _, session_before = client.call("/api/session")
        self.assertTrue(session_before["session"]["has_profile"])
        old_cookie = client.cookie
        first.close()

        second = app()                                   # the redeploy
        self.assertNotEqual(second.boot, session_before["boot"])
        returning = Client(second)
        returning.cookie = old_cookie
        status, body = returning.call("/api/session")
        self.assertEqual(status, "200 OK", "a stale cookie crashed the new process")
        self.assertEqual(body["session"]["has_profile"], False)
        self.assertNotEqual(returning.cookie, old_cookie, "the stale cookie was accepted")

    def test_the_personas_still_answer_after_a_restart(self):
        first = app()
        Client(first).call("/api/profile", "POST", {"profile": HOSTILE})
        first.close()
        second = app()
        try:
            status, out = Client(second).call("/api/quote", query="persona=maya")
            self.assertEqual(status, "200 OK")
            self.assertEqual(out["verdict"], "DEFER")
        finally:
            second.close()

    def test_a_cookie_from_an_unknown_session_is_not_trusted(self):
        app_ = app()
        try:
            ghost = Client(app_)
            ghost.cookie = f"st_sid=never-existed.{app_.boot}.{'a' * 32}"
            status, body = ghost.call("/api/session")
            self.assertEqual(status, "200 OK")
            self.assertFalse(body["session"]["has_profile"])
        finally:
            app_.close()


class DatabaseConfiguration(unittest.TestCase):
    def test_http_app_uses_the_configured_database_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "secondthought.sqlite3")
            app_ = app(db_path=path)
            try:
                self.assertEqual(app_.db.path, path)
                self.assertTrue(Path(path).exists())
            finally:
                app_.close()


if __name__ == "__main__":
    unittest.main()
