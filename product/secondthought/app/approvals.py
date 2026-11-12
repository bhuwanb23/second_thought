"""
app/approvals.py — a human approves, then money moves.

A proposal is signed with HMAC over the exact tool name and the exact argument
dict. The token is therefore only valid for that one action: an approval granted
for $249 cannot pay $999, and cannot be replayed after it is used.

Two properties this file adds over a signature alone:

* **Expiry** — a token is good for a short window, so a leaked token is not a
  permanent licence to move money.
* **Single use** — tokens are recorded once consumed, so a captured request
  cannot be replayed.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field

from ..config import load as load_config

DEFAULT_TTL_SECONDS = 600


class ApprovalError(Exception):
    """The approval was not good enough to move money."""


DEFAULT_SECRET = b"dev-only-change-me"


def secret_from_env() -> bytes:
    """
    Reads through config, never the environment directly — that is what keeps
    .env.example and the code from drifting apart.

    A shipped default secret is not a secret. The demo still runs, but the
    diagnostics endpoint reports 'default' so an operator can see it.
    """
    configured = load_config().approval_secret
    return configured.encode() if configured else DEFAULT_SECRET


def secret_source() -> str:
    return load_config().approval_secret_source


def _canonical(tool: str, args: dict) -> bytes:
    return json.dumps({"tool": tool, "args": args}, sort_keys=True,
                      separators=(",", ":")).encode()


def sign(tool: str, args: dict, secret: bytes | None = None) -> str:
    """The bind: this token is only meaningful for this tool and these arguments."""
    key = secret if secret is not None else secret_from_env()
    return hmac.new(key, _canonical(tool, args), hashlib.sha256).hexdigest()[:32]


def verify(tool: str, args: dict, token: str | None,
           secret: bytes | None = None) -> bool:
    if not token:
        return False
    return hmac.compare_digest(sign(tool, args, secret), token)


@dataclass
class Approval:
    """A proposal waiting for, or holding, a human's consent."""

    tool: str
    args: dict
    token: str
    issued_at: float
    ttl_seconds: int = DEFAULT_TTL_SECONDS
    nonce: str = field(default_factory=lambda: secrets.token_hex(8))

    def expired(self, now: float | None = None) -> bool:
        return (now if now is not None else time.time()) > self.issued_at + self.ttl_seconds

    def describe(self) -> dict:
        return {"tool": self.tool, "args": self.args, "token": self.token,
                "expires_in": max(0, int(self.issued_at + self.ttl_seconds - time.time()))}


class ApprovalGate:
    """
    Holds the proposals and the spent tokens.

    Deliberately in-memory: an approval is a seconds-long handshake between a
    human and a process, not a durable record. The *outcome* is durable; consent
    does not need to be.
    """

    def __init__(self, ttl_seconds: int = DEFAULT_TTL_SECONDS,
                 secret: bytes | None = None):
        self.ttl_seconds = ttl_seconds
        # A gate may be given its own key. The HTTP layer gives every visitor one,
        # so a token minted in one browser is not even a candidate in another.
        self.secret = secret
        self._pending: dict[str, Approval] = {}
        self._spent: set[str] = set()

    def propose(self, tool: str, args: dict, now: float | None = None) -> Approval:
        a = Approval(tool=tool, args=args, token=sign(tool, args, self.secret),
                     issued_at=now if now is not None else time.time(),
                     ttl_seconds=self.ttl_seconds)
        self._pending[a.nonce] = a
        return a

    def redeem(self, tool: str, args: dict, token: str | None,
               now: float | None = None) -> None:
        """Raise unless this token is genuine, unexpired, unspent, and for these args."""
        if not verify(tool, args, token, self.secret):
            raise ApprovalError("this approval does not match these arguments")
        if token in self._spent:
            raise ApprovalError("this approval has already been used")
        match = next((a for a in self._pending.values() if a.token == token), None)
        issued = match.issued_at if match else (now or time.time())
        ttl = match.ttl_seconds if match else self.ttl_seconds
        if (now if now is not None else time.time()) > issued + ttl:
            raise ApprovalError("this approval has expired")
        self._spent.add(token)
        if match:
            self._pending.pop(match.nonce, None)

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    @property
    def spent_count(self) -> int:
        return len(self._spent)
