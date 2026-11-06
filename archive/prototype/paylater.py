"""
paylater.py — resolving the OFFER branch honestly.

The problem this solves: Pay Later eligibility is only knowable on the client.
PayPal's JS SDK v6 does it in the browser:

    const methods = await sdk.findEligibleMethods({currencyCode, countryCode, amount});
    if (methods.isEligible("paylater")) {
      const { productCode, countryCode } = methods.getDetails("paylater");
    }

A server cannot call that. So the server must not pretend to know. Instead:

  1. server proposes an instrument and an amount
  2. the storefront calls findEligibleMethods and POSTs the result back
  3. the server resolves which instrument to actually use

Three outcomes, and every one of them ends in a real PayPal action:

  paylater        -> order with intent CAPTURE, handed to the Pay Later button
  authorize_hold  -> order with intent AUTHORIZE, captured on the schedule we set
  invoice         -> /v2/invoicing/invoices with a due date

If eligibility cannot be determined, we do NOT show a Pay Later button, because
a Pay Later button that does nothing is exactly the decorative integration that
fails Stage 1.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

INSTRUMENT_PAYLATER = "paylater"
INSTRUMENT_AUTHORIZE = "authorize_hold"
INSTRUMENT_INVOICE = "invoice"
INSTRUMENT_NONE = "none"


@dataclass
class Eligibility:
    eligible: bool | None          # None means "we do not know yet"
    amount_minor: int
    currency: str = "USD"
    country: str = "US"
    product_code: str = ""
    paylater_country: str = ""
    source: str = "unknown"        # "sdk" | "simulated" | "unknown"

    def to_dict(self) -> dict:
        return {
            "eligible": self.eligible,
            "amount_minor": self.amount_minor,
            "currency": self.currency,
            "country": self.country,
            "product_code": self.product_code,
            "country_code": self.paylater_country,
            "source": self.source,
        }


UNKNOWN = "unknown"


def parse_sdk_result(payload: dict, amount_minor: int) -> Eligibility:
    """
    Accept what the storefront posts back from findEligibleMethods().

    Anything we do not recognise becomes eligible=None — never a hopeful True.
    """
    if not isinstance(payload, dict):
        return Eligibility(eligible=None, amount_minor=amount_minor)
    eligible = payload.get("eligible")
    if not isinstance(eligible, bool):
        eligible = None
    details = payload.get("details") or {}
    return Eligibility(
        eligible=eligible,
        amount_minor=amount_minor,
        currency=str(payload.get("currency") or "USD"),
        country=str(payload.get("country") or "US"),
        product_code=str(details.get("productCode") or ""),
        paylater_country=str(details.get("countryCode") or ""),
        source="sdk" if eligible is not None else UNKNOWN,
    )


def choose_instrument(verdict: str, eligibility: Eligibility | None) -> str:
    """
    The rule that keeps the demo honest.

    A DECLINE never shows a payment instrument. An OFFER prefers Pay Later, and
    falls back to an authorisation hold when Pay Later is not available — which
    is the common case outside the US and for many sandbox accounts.
    """
    if verdict == "DECLINE":
        return INSTRUMENT_NONE
    if verdict == "DEFER":
        return INSTRUMENT_INVOICE
    # OFFER
    if eligibility and eligibility.eligible is True:
        return INSTRUMENT_PAYLATER
    return INSTRUMENT_AUTHORIZE


def describe_instrument(instrument: str) -> dict:
    return {
        INSTRUMENT_PAYLATER: {
            "label": "Pay Later",
            "requires": "client eligibility confirmed by findEligibleMethods()",
            "paypal_call": "order intent=CAPTURE, handed to <paypal-paylater-button>",
            "honest_note": "the instalment schedule is PayPal's; we do not model it",
            "fulfilment": "PayPal pays the merchant upfront and carries the credit risk. "
                          "The merchant ships as normal.",
            "risk_bearer": "PayPal",
        },
        INSTRUMENT_AUTHORIZE: {
            "label": "PayPal authorisation hold",
            "requires": "nothing extra — works in every sandbox",
            "paypal_call": "order intent=AUTHORIZE then capture on schedule",
            "honest_note": "funds are held, not extended on trust",
            "fulfilment": "Funds are held now and captured on the approved date. "
                          "The merchant ships under its normal policy because the money "
                          "is already reserved.",
            "risk_bearer": "nobody",  # funds already held
        },
        INSTRUMENT_INVOICE: {
            "label": "Reserve now, pay on payday",
            "requires": "nothing extra",
            "paypal_call": "POST /v2/invoicing/invoices with payment_term.due_date",
            "honest_note": "the shopper pays when the money is actually there",
            "fulfilment": "PAY BEFORE SHIP. The merchant reserves the item and the price "
                          "but ships only after the invoice clears on the due date. The "
                          "merchant never extends credit and never carries the risk that "
                          "PayPal carries under Pay Later.",
            "risk_bearer": "nobody",  # pay before ship
        },
        INSTRUMENT_NONE: {
            "label": "No instrument offered",
            "requires": "—",
            "paypal_call": "no call",
            "honest_note": "the shopper may still override and pay in full",
            "fulfilment": "Nothing is offered, so there is nothing to fulfil. The shopper "
                          "can still buy in full.",
            "risk_bearer": "nobody",
        },
    }[instrument]


@dataclass
class EligibilityStore:
    """Last eligibility result per shopper, as posted by the storefront."""

    records: dict[str, Eligibility] = field(default_factory=dict)

    def put(self, shopper: str, eligibility: Eligibility) -> None:
        self.records[shopper] = eligibility

    def get(self, shopper: str) -> Eligibility | None:
        return self.records.get(shopper)
