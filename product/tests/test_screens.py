"""V8's measurable half: the page a stranger sees must not speak in our language.

I cannot run the outside-eye rehearsal, because it needs a person who has never
seen this. What I *can* do is remove the most likely reason it would fail — copy
that only makes sense to whoever wrote it.

The audit below is a proxy, not the test. A sentence can pass every check here and
still confuse someone, which is exactly why V8 still has to happen.
"""

import io
import json
import re
import unittest

from secondthought.config import AppSettings, LLMSettings, PayPalSettings
from secondthought.interfaces.http import App
from secondthought.interfaces.proof import render as render_proof
from secondthought.interfaces.screens import (BANNED_IN_EXPLANATION, PLAIN_LABEL,
                                              explain, money, plain_collision)


def get(app, path, query=""):
    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": query,
               "CONTENT_LENGTH": "0", "wsgi.input": io.BytesIO(b""),
               "REMOTE_ADDR": "198.51.100.61"}
    out = {}

    def sr(status, headers):
        out["status"] = status
        out["headers"] = dict(headers)

    payload = b"".join(app(environ, sr))
    return out["status"], out["headers"], payload


class PlainLanguage(unittest.TestCase):
    """No internal vocabulary in anything a shopper reads."""

    def test_a_decline_never_says_instalment_or_collision(self):
        rendered = explain({"verdict": "DECLINE", "amount_minor": 24_900,
                            "collision": "instalment 4 of 4",
                            "collision_date": "2026-12-13",
                            "safe_amount_minor": 14_000})
        sentence = f"{rendered['title']} {rendered['why']} {rendered['action']}".lower()
        for word in BANNED_IN_EXPLANATION:
            self.assertNotIn(word, sentence,
                             f"the shopper is shown the internal word {word!r}")
        self.assertNotIn("instalment", sentence)

    def test_the_decline_names_what_collides_in_plain_words(self):
        rendered = explain({"verdict": "DECLINE", "amount_minor": 24_900,
                            "collision": "instalment 4 of 4",
                            "collision_date": "2026-12-13"})
        self.assertIn("the 4th payment on a plan you already have", rendered["why"])
        self.assertNotIn("instalment", rendered["why"])

    def test_every_verdict_explains_itself_in_one_sentence(self):
        for verdict in ("OFFER", "DEFER", "DECLINE"):
            rendered = explain({"verdict": verdict, "amount_minor": 24_900,
                                "pay_on": "2026-11-06", "collision": "rent",
                                "collision_date": "2026-11-28",
                                "safe_amount_minor": 14_000})
            self.assertTrue(rendered["title"].strip())
            self.assertGreater(len(rendered["why"]), 40,
                               f"{verdict} needs a real reason, not a label")
            self.assertLess(len(rendered["why"]), 320, f"{verdict} is too long to read")
            self.assertTrue(rendered["action"])

    def test_a_defer_says_the_day_and_who_ships_when(self):
        rendered = explain({"verdict": "DEFER", "amount_minor": 24_900,
                            "pay_on": "2026-11-06"})
        self.assertIn("Fri 6 Nov", rendered["title"])
        self.assertIn("ships", rendered["title"])
        self.assertIn("Nothing is charged now", rendered["why"])

    def test_an_unknown_verdict_says_nothing_rather_than_guessing(self):
        rendered = explain({"verdict": "", "amount_minor": 1})
        self.assertIn("Nothing to decide", rendered["title"])
        self.assertEqual(rendered["action"], "")

    def test_a_missing_safe_amount_does_not_print_none(self):
        rendered = explain({"verdict": "DECLINE", "amount_minor": 24_900,
                            "collision": "rent", "collision_date": "2026-11-28",
                            "safe_amount_minor": None})
        self.assertNotIn("None", rendered["why"])
        self.assertNotIn("$0.00", rendered["why"])

    def test_the_verdict_label_is_the_only_place_the_code_word_appears(self):
        for verdict, label in PLAIN_LABEL.items():
            self.assertTrue(label.startswith(verdict))
            self.assertTrue(any(plain in label for plain in ("fits", "not this month")))
            rendered = explain({"verdict": verdict, "amount_minor": 1000})
            self.assertEqual(rendered["label"], label)


class PlainCollision(unittest.TestCase):
    def test_instalment_labels_become_sentences(self):
        self.assertEqual(plain_collision("instalment 1 of 4"),
                         "the 1st payment on a plan you already have")
        self.assertEqual(plain_collision("instalment 15 of 20"),
                         "the 15th payment on a plan you already have")
    def test_ordinary_labels_are_left_alone(self):
        for label in ("rent", "car loan", "childcare"):
            self.assertEqual(plain_collision(label), label)

    def test_nothing_becomes_nothing(self):
        self.assertEqual(plain_collision(None), "")


class ThePage(unittest.TestCase):
    def setUp(self):
        # explicit empty credentials: these assertions describe a clean machine,
        # not whatever .env happens to hold
        self.app = App(AppSettings(approval_secret="test-secret",
                                   llm=LLMSettings(api_key=""),
                                   paypal=PayPalSettings(client_id="", client_secret="")))

    def tearDown(self):
        self.app.close()

    def test_it_serves_html_to_a_first_time_visitor(self):
        status, headers, body = get(self.app, "/")
        self.assertEqual(status, "200 OK")
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"Second Thought", body)

    def test_a_stranger_can_see_all_three_months_without_clicking_anything_else(self):
        _s, _h, body = get(self.app, "/")
        for name in ("ada", "ben", "cleo"):
            self.assertIn(name.encode(), body, f"{name} is not on the first screen")

    def test_the_page_states_both_badges_honestly(self):
        _s, _h, body = get(self.app, "/")
        self.assertIn(b"AI \xc2\xb7 LLM-MOCK", body)
        self.assertIn(b"PAYMENTS \xc2\xb7 SIMULATED", body)
        self.assertIn(b"simulated", body.lower())

    def test_it_loads_nothing_from_the_network(self):
        """The preview pane has no network, and neither does a locked-down laptop."""
        _s, _h, body = get(self.app, "/")
        for pattern in (rb'src="http', rb'href="http', rb"@import", rb"googleapis",
                        rb"cdn\."):
            self.assertIsNone(re.search(pattern, body), f"external dependency: {pattern}")

    def test_the_page_does_not_use_our_vocabulary_in_the_chrome(self):
        """Body copy a shopper reads before clicking anything."""
        _s, _h, body = get(self.app, "/")
        text = body.decode().lower()
        opening = text.split("<script>")[0]          # the visible chrome, not the code
        for word in ("collision", "authorisation", "authorize", "answer_quality",
                     "instrument", "risk_bearer", "api", "json"):
            self.assertNotIn(word, opening, f"the page shows {word!r} before any click")

    def test_the_quote_endpoint_hands_the_page_sentences_not_codes(self):
        for persona in ("ada", "ben", "cleo"):
            status, _h, body = get(self.app, "/api/quote", f"persona={persona}")
            self.assertEqual(status, "200 OK")
            payload = json.loads(body)
            self.assertIn("explain", payload)
            self.assertTrue(payload["explain"]["why"])

    def test_the_page_says_the_money_is_not_real(self):
        _s, _h, body = get(self.app, "/")
        self.assertIn(b"Nothing is charged", body)

    def test_the_page_explains_the_deferred_lifecycle_without_promising_collections(self):
        _s, _h, body = get(self.app, "/")
        text = body.decode().lower()
        for phrase in ("dated invoice", "nothing ships before payment",
                       "hold can expire or be released", "contacts the merchant"):
            self.assertIn(phrase, text)
        self.assertIn("does not pretend to collect debt", text)


class ProofPage(unittest.TestCase):
    """/proof is the page that has to be boring: it is the one that gets checked."""

    def setUp(self):
        self.app = App(AppSettings(approval_secret="test-secret", llm=LLMSettings(api_key=""),
                                   paypal=PayPalSettings(client_id="", client_secret="")))

    def tearDown(self):
        self.app.close()

    def test_it_is_served(self):
        status, headers, body = get(self.app, "/proof")
        self.assertEqual(status, "200 OK")
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn(b"Proof", body)

    def test_it_shows_measured_numbers_when_there_are_some(self):
        html = render_proof({"generated_at": "2026-11-12 15:40 UTC", "git": "abc1234",
                             "summary": "all measured checks passed",
                             "checks": [{"label": "Unit tests", "value": "173 tests OK in 0.31 s",
                                         "command": "python3 -m unittest discover -s tests -q"}]})
        self.assertIn("173 tests OK in 0.31 s", html)
        self.assertIn("python3 -m unittest discover -s tests -q", html)
        self.assertIn("abc1234", html)

    def test_it_admits_when_nothing_has_been_measured(self):
        self.assertIn("No measurement file", render_proof({}))

    def test_it_never_calls_a_ready_gate_a_pass(self):
        html = render_proof({})
        self.assertIn("PARTIAL", html)
        self.assertIn("BLOCKED", html)
        self.assertIn("OPEN", html)
        self.assertNotIn('>PASS<', html)

    def test_it_says_the_money_is_simulated(self):
        self.assertIn("simulated", render_proof({}))

    def test_it_exposes_the_deferred_lifecycle_and_its_limit(self):
        html = render_proof({})
        for state in ("RESERVED", "PAID", "FULFILLED", "EXPIRED", "RELEASED", "REFUNDED"):
            self.assertIn(state, html)
        self.assertIn("not a collections service", html)


class Money(unittest.TestCase):
    def test_formatting(self):
        self.assertEqual(money(24_900), "$249.00")
        self.assertEqual(money(0), "$0.00")
        self.assertEqual(money(None), "—")


if __name__ == "__main__":
    unittest.main()
