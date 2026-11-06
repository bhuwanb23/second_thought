"""
session.py — per-visitor state for the public demo.

Why this exists:

1. A shared demo is hostile. If one judge saves a payday profile, the next judge
   sees a different verdict for the same persona. The three personas must be
   reproducible for everyone, so nothing a visitor does can touch them.

2. Hosted filesystems are disposable. A redeploy, a restart or a spin-down wipes
   files, so anything persisted to disk is gone anyway. Better to be explicit:
   saved data lives in memory, per session, and is treated as disposable.

Personas are read-only. A profile saved by a visitor applies only to that
visitor's own session, and only to their own decisions.
"""

from __future__ import annotations

import secrets
import threading
from collections import OrderedDict

import paylater
from ledger import Ledger
from profile import ProfileStore

COOKIE = "st_sid"
MAX_SESSIONS = 400          # bound memory on a public demo
RATE_LIMIT = 30             # LLM-backed calls per session
RATE_WINDOW_SECONDS = 600

# A cookie-scoped limit is trivially bypassed by clearing cookies, so it is not
# the real protection. These two are:
IP_RATE_LIMIT = 90          # per IP per window — survives cookie clearing
GLOBAL_RATE_LIMIT = 1500    # per instance per day — the in-app spend backstop
GLOBAL_WINDOW_SECONDS = 86_400


class Session:
    def __init__(self, sid: str):
        self.sid = sid
        # all in-memory: disposable by design, never written to disk
        self.profiles = ProfileStore(path=None)
        self.ledger = Ledger(path=None)
        self.eligibility = paylater.EligibilityStore()
        self._hits: list[float] = []
        self._lock = threading.Lock()

    # -- a small token bucket, so one visitor cannot burn the LLM budget ----
    def allow(self, now: float) -> tuple[bool, int]:
        with self._lock:
            cutoff = now - RATE_WINDOW_SECONDS
            self._hits = [t for t in self._hits if t > cutoff]
            if len(self._hits) >= RATE_LIMIT:
                return False, 0
            self._hits.append(now)
            return True, RATE_LIMIT - len(self._hits)

    def reset(self) -> None:
        self.profiles.profiles = {}
        self.ledger.entries = []
        self.eligibility.records = {}
        with self._lock:
            self._hits = []


class WindowCounter:
    """A fixed-window counter. Small, honest, and easy to test."""

    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._buckets: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def allow(self, key: str, now: float) -> bool:
        with self._lock:
            cutoff = now - self.window
            hits = [t for t in self._buckets.get(key, []) if t > cutoff]
            if len(hits) >= self.limit:
                self._buckets[key] = hits
                return False
            hits.append(now)
            self._buckets[key] = hits
            # keep memory bounded on a public URL
            if len(self._buckets) > 2_000:
                for k in [k for k, v in self._buckets.items() if not v][:1_000]:
                    self._buckets.pop(k, None)
            return True

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


class SessionStore:
    def __init__(self, max_sessions: int = MAX_SESSIONS):
        self.max_sessions = max_sessions
        self._sessions: OrderedDict[str, Session] = OrderedDict()
        self._lock = threading.Lock()
        self.ip = WindowCounter(IP_RATE_LIMIT, RATE_WINDOW_SECONDS)
        self.global_ = WindowCounter(GLOBAL_RATE_LIMIT, GLOBAL_WINDOW_SECONDS)

    def allow_llm(self, session: Session, ip: str | None, now: float) -> tuple[bool, str]:
        """
        Three gates, in order of cheapness. The session limit is politeness; the
        IP limit survives cookie clearing; the global limit protects the bill if
        the provider-side spend cap is ever missed.
        """
        if not self.global_.allow("all", now):
            return False, "global budget for the day is exhausted"
        if ip and not self.ip.allow(ip, now):
            return False, "too many requests from this address"
        ok, _left = session.allow(now)
        return ok, "" if ok else "per-visitor limit reached"

    def get(self, sid: str | None) -> tuple[Session, bool]:
        """Returns (session, is_new). is_new means the caller must set the cookie."""
        with self._lock:
            is_new = not sid or sid not in self._sessions
            if sid and sid in self._sessions:
                self._sessions.move_to_end(sid)
                return self._sessions[sid], False
            new_sid = sid or secrets.token_urlsafe(12)
            s = Session(new_sid)
            self._sessions[new_sid] = s
            while len(self._sessions) > self.max_sessions:
                self._sessions.popitem(last=False)   # evict oldest, quietly
            return s, is_new

    def reset_limits(self) -> None:
        self.ip.reset()
        self.global_.reset()

    def get_by_id(self, sid: str | None) -> Session | None:
        with self._lock:
            return self._sessions.get(sid) if sid else None

    @property
    def count(self) -> int:
        return len(self._sessions)
