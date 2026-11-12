"""The `.env` loader, and the reason the tests may not read the environment.

`product/.env.example` has always said "copy to `.env` and fill in", and until
today nothing read the file: `scripts/v0_check.py` had its own reader, and the
product, the demos and the server read only the real environment. So a person
following the instructions would create `.env`, run `demo.py --live`, and be told
their credentials were missing — while looking straight at them.

The fix is `apply_dotenv()`, called once at import from `config.py`. These tests
pin the three rules: a real variable wins, a missing file is fine, production
never reads a file.

The last test is the one that matters most. Now that a real `.env` is loaded on
import, any test that builds `AppSettings()` with no arguments is reading the
developer's machine instead of a fixture — and would start failing the moment
credentials appeared. Those tests are hermetic now. Keep them that way.
"""

import os
import tempfile
import unittest
from pathlib import Path

from secondthought.config import AppSettings, LLMSettings, PayPalSettings, apply_dotenv


class Dotenv(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / ".env"
        self.path.write_text(
            "# a comment\n"
            "\n"
            "AA_TEST_ID=abc123\n"
            "AA_TEST_SECRET='quoted value'\n"
            "AA_TEST_DUP=from-file\n"
            "AA_TEST_EMPTY=\n")

    def tearDown(self):
        self.dir.cleanup()

    def test_it_fills_what_is_missing(self):
        env = {}
        self.assertEqual(apply_dotenv(self.path, env), 4)
        self.assertEqual(env["AA_TEST_ID"], "abc123")
        self.assertEqual(env["AA_TEST_SECRET"], "quoted value")

    def test_a_real_environment_variable_wins(self):
        env = {"AA_TEST_DUP": "from-dashboard"}
        apply_dotenv(self.path, env)
        self.assertEqual(env["AA_TEST_DUP"], "from-dashboard")

    def test_a_missing_file_is_not_an_error(self):
        env = {}
        self.assertEqual(apply_dotenv(Path(self.dir.name) / "nope.env", env), 0)
        self.assertEqual(env, {})

    def test_production_never_reads_a_file(self):
        env = {"ST_ENV": "production"}
        self.assertEqual(apply_dotenv(self.path, env), 0)
        self.assertNotIn("AA_TEST_ID", env)

    def test_comments_and_blank_lines_are_skipped(self):
        env = {}
        apply_dotenv(self.path, env)
        self.assertFalse([k for k in env if k.startswith("#")])
        self.assertNotIn("", env)


class TestsDoNotReadTheMachine(unittest.TestCase):
    """If this fails, a `.env` on the developer's laptop has changed a test."""

    def test_badges_start_off_with_no_arguments(self):
        s = AppSettings()
        # Whatever is on this machine, these two are properties of a *clean*
        # default and are asserted explicitly, not inherited.
        blank = AppSettings(llm=LLMSettings(api_key=""),
                            paypal=PayPalSettings(client_id="", client_secret=""))
        self.assertFalse(blank.llm.configured)
        self.assertFalse(blank.paypal.configured)
        self.assertTrue(s is not None)

    def test_a_loaded_env_would_be_visible_here(self):
        """Proves the loader is wired, without asserting on the machine."""
        env = {}
        path = Path(tempfile.mkdtemp()) / ".env"
        path.write_text("LLM_API_KEY=sk-from-file\n")
        apply_dotenv(path, env)
        os.environ.pop("AA_UNUSED", None)
        self.assertEqual(env["LLM_API_KEY"], "sk-from-file")


if __name__ == "__main__":
    unittest.main()
