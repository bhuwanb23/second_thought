"""
Session isolation — the defect this prevents:

A shared demo where one judge's saved profile changes the verdict the next judge
sees. On a public URL that makes the three personas non-reproducible, and a judge
who cannot reproduce the demo has no reason to score it.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import server  # noqa: E402
from profile import ProfileEntry, PaydayProfile  # noqa: E402
from session import Session, SessionStore  # noqa: E402


def _hostile_profile(shopper_id="dev"):
    """A profile that would definitely change the verdict if it leaked."""
    return PaydayProfile(
        shopper_id=shopper_id, opening_balance=1000,
        obligations=[ProfileEntry("rent", 4_000_000, "2026-11-09", True, 0.99, True)],
        consented_at="2026-11-01")


class TestIsolation(unittest.TestCase):
    def test_one_visitor_cannot_change_anothers_verdict(self):
        a, b = Session("judge-a"), Session("judge-b")
        before = server.build_payload("dev", session=b)
        self.assertEqual(before["decision"]["verdict"], "DEFER")

        a.profiles.put(_hostile_profile())            # judge A saves a profile
        after = server.build_payload("dev", session=b)  # judge B reloads

        self.assertIsNone(after["profile"], "judge B must not see judge A's profile")
        self.assertEqual(after["decision"]["verdict"], before["decision"]["verdict"],
                         "the persona must be reproducible for every visitor")

    def test_the_saving_visitor_still_gets_their_own_answer(self):
        a = Session("judge-a")
        a.profiles.put(_hostile_profile())
        mine = server.build_payload("dev", session=a)
        self.assertIsNotNone(mine["profile"])
        self.assertNotEqual(mine["decision"]["verdict"], "DEFER")

    def test_personas_are_read_only(self):
        """Nothing a visitor does may mutate the seeded persona constants."""
        import personas
        snapshot = repr(personas.PERSONAS)
        a = Session("vandal")
        a.profiles.put(_hostile_profile())
        a.ledger.record("dev", 24_900, "USD", "invoice", "INV2-TEST",
                        today=server.TODAY)
        server.build_payload("dev", session=a)
        self.assertEqual(repr(personas.PERSONAS), snapshot)

    def test_ledgers_are_separate(self):
        a, b = Session("a"), Session("b")
        a.ledger.record("dev", 24_900, "USD", "invoice", "INV2-A", today=server.TODAY)
        self.assertEqual(len(a.ledger.entries), 1)
        self.assertEqual(len(b.ledger.entries), 0)

    def test_reset_only_touches_one_session(self):
        a, b = Session("a"), Session("b")
        a.profiles.put(_hostile_profile())
        a.reset()
        b.profiles.put(_hostile_profile("maya"))
        self.assertEqual(len(a.profiles.profiles), 0)
        self.assertEqual(len(b.profiles.profiles), 1)


class TestStore(unittest.TestCase):
    def test_a_new_visitor_gets_a_cookie_and_a_session(self):
        store = SessionStore()
        s, is_new = store.get(None)
        self.assertTrue(is_new)
        self.assertTrue(s.sid)

    def test_a_returning_cookie_keeps_its_session(self):
        store = SessionStore()
        s1, _ = store.get(None)
        s2, is_new = store.get(s1.sid)
        self.assertFalse(is_new)
        self.assertIs(s1, s2)

    def test_eviction_is_bounded(self):
        store = SessionStore(max_sessions=3)
        for _ in range(10):
            store.get(None)
        self.assertEqual(store.count, 3)


class TestRateLimit(unittest.TestCase):
    def test_a_visitor_cannot_burn_the_llm_budget(self):
        s = Session("spam")
        ok, _ = s.allow(1000.0)
        self.assertTrue(ok)
        for i in range(30):
            s.allow(1000.0 + i * 0.01)
        blocked, _ = s.allow(1001.0)
        self.assertFalse(blocked, "the 31st LLM call in the window must be refused")

    def test_the_window_recovers(self):
        s = Session("patient")
        for _ in range(31):
            s.allow(0.0)
        self.assertFalse(s.allow(0.0)[0])
        self.assertTrue(s.allow(10_000.0)[0], "after the window, calls are allowed again")


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestPublicSurface(unittest.TestCase):
    """
    /healthz is public and unauthenticated. These hit a real server over HTTP,
    because the thing being tested is the route, not a helper function.
    """

    @classmethod
    def setUpClass(cls):
        import threading
        from http.server import ThreadingHTTPServer
        import server
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _get(self, path):
        import json
        import urllib.error
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{self.port}{path}", timeout=5) as r:
                return r.status, json.loads(r.read() or b"{}")
        except urllib.error.HTTPError as e:
            return e.code, {}

    def test_healthz_reports_only_two_booleans(self):
        code, body = self._get("/healthz")
        self.assertEqual(code, 200)
        self.assertEqual(set(body), {"ok", "paypal_live", "ai_live"},
                         "no session counts, no config, no internal flags")
        self.assertIsInstance(body["paypal_live"], bool)
        self.assertIsInstance(body["ai_live"], bool)

    def test_diagnostics_is_404_without_a_token(self):
        self.assertEqual(self._get("/diagnostics")[0], 404,
                         "an unset DIAG_TOKEN must never authorise")

    def test_diagnostics_is_404_with_the_wrong_token(self):
        self.assertEqual(self._get("/diagnostics?token=guess")[0], 404)


class TestLimitGates(unittest.TestCase):
    def test_an_ip_limit_survives_cookie_clearing(self):
        """A new session does not reset the IP budget — that is the point."""
        from session import IP_RATE_LIMIT, Session, SessionStore
        store = SessionStore()
        for i in range(IP_RATE_LIMIT):
            store.ip.allow("203.0.113.9", 100.0)
        fresh = Session("brand-new-cookie")      # attacker clears cookies
        ok, why = store.allow_llm(fresh, "203.0.113.9", 100.5)
        self.assertFalse(ok)
        self.assertIn("address", why)

    def test_the_global_budget_is_the_last_line(self):
        from session import GLOBAL_RATE_LIMIT, Session, SessionStore
        store = SessionStore()
        for i in range(GLOBAL_RATE_LIMIT):
            store.global_.allow("all", 100.0)
        ok, why = store.allow_llm(Session("x"), "198.51.100.7", 101.0)
        self.assertFalse(ok)
        self.assertIn("global", why)

    def test_a_normal_visitor_is_unaffected(self):
        from session import Session, SessionStore
        store = SessionStore()
        ok, why = store.allow_llm(Session("normal"), "192.0.2.44", 1.0)
        self.assertTrue(ok, why)
