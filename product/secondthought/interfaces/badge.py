"""
interfaces/badge.py — the two words a demo must never get wrong.

The badge is not decoration. A demo that shows a real model while running a
template, or real PayPal while running a simulation, is the failure this whole
design is arranged against. So the badge is computed from configuration and
nothing else, and there is no argument anywhere that overrides it.

`health_payload` is the same discipline for `/healthz`: booleans and short
status words, never a key, a path or a version string.
"""

from __future__ import annotations

AI_LIVE = "AI · LLM"
AI_MOCK = "AI · LLM-MOCK"
PAY_LIVE = "PAYMENTS · SANDBOX"
PAY_SIM = "PAYMENTS · SIMULATED"


def ai_badge(settings) -> str:
    """`AI · LLM` only when a key is actually loaded."""
    return AI_LIVE if settings.llm.configured else AI_MOCK


def payments_badge(settings) -> str:
    return PAY_LIVE if settings.paypal.configured else PAY_SIM


def badges(settings) -> list[dict]:
    return [
        {"id": "ai", "label": ai_badge(settings), "live": settings.llm.configured,
         "detail": settings.llm.model if settings.llm.configured else "template fallback"},
        {"id": "payments", "label": payments_badge(settings),
         "live": settings.paypal.configured,
         "detail": "sandbox API" if settings.paypal.configured else "in-memory gateway"},
    ]


def health_payload(settings) -> dict:
    """Booleans and status words only — safe to expose without a token."""
    return {
        "status": "ok",
        "ai_mode": "llm" if settings.llm.configured else "llm-mock",
        "payments_mode": "sandbox" if settings.paypal.configured else "simulated",
        "checks": {"ai_key": settings.llm.configured,
                   "paypal_credentials": settings.paypal.configured,
                   "approval_secret": settings.approval_secret_source == "env",
                   "database": bool(settings.db_path)},
    }
