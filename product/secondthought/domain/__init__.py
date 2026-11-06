"""Domain: pure rules. Imports nothing outside this package."""

from .cashflow import (  # noqa: F401
    HORIZON_DAYS, INSTALMENT_GAP_DAYS, MIN_BUFFER, CashCalendar, InvalidRequest,
    Instalment, Obligation, Payday, Policy, buffer_amount, monthly_income,
    nearest_event, next_payday, simulate, split_instalments,
)
from .engine import Decision, Option, decide  # noqa: F401
