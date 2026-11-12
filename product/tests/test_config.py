import os
import unittest
from unittest.mock import patch

import secondthought.config as config


class ConfigSafety(unittest.TestCase):
    def test_production_processes_ignore_local_dotenv_values(self):
        with patch.dict(os.environ, {
            "ST_ENV": "production",
            "PAYPAL_CLIENT_ID": "",
            "PAYPAL_CLIENT_SECRET": "",
        }, clear=False), \
                patch.object(config, "_DOTENV_VALUES",
                              {"PAYPAL_CLIENT_ID": "local-only-id"}):
            settings = config.load()
        self.assertFalse(settings.paypal.configured)

    def test_blank_values_fall_back_to_declared_defaults(self):
        with patch.dict(os.environ, {"TEST_EMPTY": ""}, clear=False), \
                patch.object(config, "_DOTENV_VALUES", {}):
            self.assertEqual(config._get("TEST_EMPTY", "fallback"), "fallback")


if __name__ == "__main__":
    unittest.main()
