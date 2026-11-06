"""
interfaces/session.py — one visitor, one box, and nothing shared.

The defect this prevents is specific and embarrassing: a public demo where the
first judge to save a profile changes the verdict the second judge sees. On a URL
in a submission, that makes the three personas non-reproducible — and a judge who
cannot reproduce the demo has no reason to score it.

So the rule is structural, not procedural:

  * A visitor's saved profile lives **only inside their session object**. There is
    no code path that writes it anywhere a second visitor can read.
  * Persona defaults live in a separate store that this layer never writes to.
  * Each session gets its own approval key, so an approval token minted in one
    browser is not merely rejected in another — it fails the signature.
  * Sessions are **in memory, deliberately**. A restart loses them, which is the
    correct outcome: the alternative is serving a judge a cookie that points at
    state that no longer exists.

Rate limiting is keyed on the session *and* on the caller's IP. Cookies alone are
not enough — clearing a cookie must not hand anyone a fresh budget — and the IP
cap is set above what one session can spend, so a second real visitor on the same
network is not punished for the first one's consumption.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field

from ..app.approvals import ApprovalGate

SESSION_TTL = 3600           # a demo session is an hour, not a week
LLM_PER_SESSION = 30         # inside the window
LLM_PER_IP = 90              # cookie-cycling backstop, 3x one session
LLM_WINDOW = 600             # 10 minutes


@dataclass
class Session:
    id: str
    secret: bytes
    created_at: float
    profile: dict | None = None          # the visitor's own — never shared
    llm_calls: list = field(default_factory=list)
    profile_writes: list = field(default_factory=list)
    approvals: ApprovalGate = None

    def __post_init__(self):
        if self.approvals is None:
            self.approvals = ApprovalGate(secret=self.secret)

    @property
    def public(self) -> dict:
        return {"session": self.id[:8], "has_profile": self.profile is not None,
                "age_seconds": int(time.time() - self.created_at)}


class SessionStore:
    """In-memory by design. A restart empties it, and that is the point."""

    def __init__(self, secret: bytes, *, ttl: int = SESSION_TTL,
                 per_session: int = LLM_PER_SESSION, per_ip: int = LLM_PER_IP,
                 window: int = LLM_WINDOW):
        self.secret = secret
        self.ttl = ttl
        self.per_session = per_session
        self.per_ip = per_ip
        self.window = window
        self.boot = secrets.token_hex(6)      # invalidates every cookie on restart
        self._sessions: dict[str, Session] = {}
        self._ip_calls: dict[str, list] = {}
        self.swept = 0

    # -- sessions ----------------------------------------------------------
    def new(self) -> Session:
        s = Session(id=secrets.token_urlsafe(18), secret=secrets.token_bytes(32),
                    created_at=time.time())
        self._sessions[s.id] = s
        return s

    def get(self, sid: str | None, now: float | None = None) -> Session | None:
        if not sid:
            return None
        s = self._sessions.get(sid)
        if s is None:
            return None
        if (now or time.time()) - s.created_at > self.ttl:
            self._sessions.pop(sid, None)
            return None
        return s

    def sweep(self, now: float | None = None) -> int:
        now = now or time.time()
        dead = [k for k, v in self._sessions.items() if now - v.created_at > self.ttl]
        for k in dead:
            self._sessions.pop(k, None)
        self.swept += len(dead)
        return len(dead)

    @property
    def count(self) -> int:
        return len(self._sessions)

    # -- the cookie --------------------------------------------------------
    def issue_cookie(self, s: Session) -> str:
        """`sid.boot.signature` — the boot id makes an old cookie honestly dead."""
        return f"{s.id}.{self.boot}.{self._sign(s.id)}"

    def read_cookie(self, raw: str | None) -> Session | None:
        """Never raises, never adopts a session it cannot verify."""
        if not raw:
            return None
        parts = raw.split(".")
        if len(parts) != 3:
            return None
        sid, boot, sig = parts
        if not hmac.compare_digest(sig, self._sign(sid)):
            return None
        if not hmac.compare_digest(boot, self.boot):
            return None                      # issued before the last restart
        return self.get(sid)

    def _sign(self, sid: str) -> str:
        return hmac.new(self.secret, sid.encode(), hashlib.sha256).hexdigest()[:32]

    # -- budget ------------------------------------------------------------
    def allow_llm(self, session: Session, ip: str, now: float | None = None) -> tuple:
        """(allowed, reason) for model-backed requests."""
        return self._allow(session.llm_calls, ip, now, "model-backed")

    def allow_profile(self, session: Session, ip: str,
                      now: float | None = None) -> tuple:
        """(allowed, reason) for profile mutations, separate from model budget."""
        return self._allow(session.profile_writes, ip, now, "profile")

    def _allow(self, session_calls: list, ip: str, now: float | None,
               label: str) -> tuple:
        """Apply the same session/IP window to a specific request category."""
        now = now or time.time()
        cutoff = now - self.window
        session_calls[:] = [t for t in session_calls if t > cutoff]
        if len(session_calls) >= self.per_session:
            return False, (f"session limit: {self.per_session} {label} requests per "
                           f"{self.window // 60} minutes")
        calls = [t for t in self._ip_calls.get(ip, []) if t > cutoff]
        if len(calls) >= self.per_ip:
            return False, (f"network limit: {self.per_ip} {label} requests per "
                           f"{self.window // 60} minutes from this address")
        session_calls.append(now)
        calls.append(now)
        self._ip_calls[ip] = calls
        return True, f"{self.per_session - len(session_calls)} {label} requests left"
