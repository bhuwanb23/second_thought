"""
config.py — every environment variable the product reads, in one place.

The contract with `.env.example` is only as good as this being the *only* file
that touches the environment. `scripts/v0_check.py` scans the package for stray
`os.environ` reads and fails if one appears outside here, so the file that
documents the variables and the code that uses them cannot drift apart.

Nothing here prints or logs a secret. `describe()` reports whether a value is
present, never what it is.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

SANDBOX_BASE = "https://api-m.sandbox.paypal.com"
LIVE_BASE = "https://api-m.paypal.com"


_DOTENV_VALUES: dict[str, str] | None = None


def _load_dotenv() -> dict[str, str]:
    """Load local `.env` values without overriding explicit process variables."""
    global _DOTENV_VALUES
    if os.environ.get("ST_ENV", "").strip().lower() == "production":
        return {}
    if _DOTENV_VALUES is not None:
        return _DOTENV_VALUES
    _DOTENV_VALUES = {}
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.exists():
        return _DOTENV_VALUES
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        name, _, value = line.partition("=")
        name, value = name.strip(), value.strip()
        if value[:1] in ("'", '"') and value[-1:] == value[:1]:
            value = value[1:-1]
        if name:
            _DOTENV_VALUES[name] = value
    return _DOTENV_VALUES


def _get(name: str, default: str = "") -> str:
    values = _load_dotenv()
    value = os.environ[name] if name in os.environ else values.get(name, default)
    return (value or default).strip()


def _get_int(name: str, default: int) -> int:
    try:
        return int(_get(name) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class PayPalSettings:
    client_id: str = ""
    client_secret: str = ""
    webhook_id: str = ""
    env: str = "sandbox"          # sandbox | live — live is refused at runtime

    @property
    def base_url(self) -> str:
        return LIVE_BASE if self.env == "live" else SANDBOX_BASE

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    @property
    def mode(self) -> str:
        """What the badge says. Never 'live' just because credentials exist."""
        return "sandbox" if self.configured else "simulated"


@dataclass(frozen=True)
class LLMSettings:
    api_key: str = ""
    model: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    daily_call_budget: int = 1500

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    @property
    def mode(self) -> str:
        return "llm" if self.configured else "llm-mock"


@dataclass(frozen=True)
class AppSettings:
    env: str = "development"
    db_path: str = "secondthought.sqlite3"
    approval_secret: str = ""
    diag_token: str = ""
    port: int = 8000
    paypal: PayPalSettings = field(default_factory=PayPalSettings)
    llm: LLMSettings = field(default_factory=LLMSettings)

    @property
    def approval_secret_source(self) -> str:
        return "env" if self.approval_secret else "default"

    def describe(self) -> dict:
        """Safe for logs and for a diagnostics endpoint: booleans, never values."""
        return {
            "env": self.env,
            "paypal": {
                "configured": self.paypal.configured,
                "mode": self.paypal.mode,
                "api": self.paypal.env,
                "webhook": bool(self.paypal.webhook_id),
            },
            "llm": {
                "configured": self.llm.configured,
                "mode": self.llm.mode,
                "model": self.llm.model,
            },
            "approval_secret": self.approval_secret_source,
            "diag_token": "env" if self.diag_token else "unset",
            "db_path": self.db_path,
        }


def load() -> AppSettings:
    return AppSettings(
        env=_get("ST_ENV", "development"),
        db_path=_get("ST_DB_PATH", "secondthought.sqlite3"),
        approval_secret=_get("APPROVAL_SECRET"),
        diag_token=_get("DIAG_TOKEN"),
        port=_get_int("PORT", 8000),
        paypal=PayPalSettings(
            client_id=_get("PAYPAL_CLIENT_ID"),
            client_secret=_get("PAYPAL_CLIENT_SECRET"),
            webhook_id=_get("PAYPAL_WEBHOOK_ID"),
            env=_get("PAYPAL_ENV", "sandbox").lower(),
        ),
        llm=LLMSettings(
            api_key=_get("LLM_API_KEY"),
            model=_get("LLM_MODEL", "gpt-4o-mini"),
            base_url=_get("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            daily_call_budget=_get_int("LLM_DAILY_CALL_BUDGET", 1500),
        ),
    )


# The complete set of variables this product reads. Keep in step with
# .env.example — v0_check.py fails the build if these diverge.
ENV_CONTRACT = (
    "PAYPAL_CLIENT_ID",
    "PAYPAL_CLIENT_SECRET",
    "PAYPAL_WEBHOOK_ID",
    "PAYPAL_ENV",
    "LLM_API_KEY",
    "LLM_MODEL",
    "LLM_BASE_URL",
    "LLM_DAILY_CALL_BUDGET",
    "APPROVAL_SECRET",
    "DIAG_TOKEN",
    "ST_ENV",
    "ST_DB_PATH",
    "PORT",
    # read only by scripts/v0_check.py, to prove the host is a paid instance
    "RENDER_API_KEY",
)
