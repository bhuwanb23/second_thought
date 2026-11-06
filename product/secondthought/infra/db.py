"""
infra/db.py — durable state, in one file the whole way down.

SQLite because the promise needs to survive a restart: a reservation that says
"paid, awaiting shipment" must still say that after a redeploy. Sessions and
approvals stay in memory; anything a merchant or shopper could be held to is
here.

Webhook idempotency lives here too. PayPal will deliver an event more than once;
`webhook_seen()` is what makes that harmless.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
    shopper_id TEXT PRIMARY KEY,
    payload    TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reservations (
    id           TEXT PRIMARY KEY,
    shopper_id   TEXT NOT NULL,
    merchant_id  TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    currency     TEXT NOT NULL,
    due_date     TEXT NOT NULL,
    hold_until   TEXT NOT NULL,
    invoice_id   TEXT,
    payment_ref  TEXT,
    state        TEXT NOT NULL,
    payload      TEXT NOT NULL,
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_res_open ON reservations(state, hold_until);

CREATE TABLE IF NOT EXISTS ledger (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    shopper_id   TEXT NOT NULL,
    merchant_id  TEXT NOT NULL,
    amount_minor INTEGER NOT NULL,
    kind         TEXT NOT NULL,
    ref          TEXT,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ledger_shopper ON ledger(shopper_id);

CREATE TABLE IF NOT EXISTS webhook_events (
    event_id     TEXT PRIMARY KEY,
    kind         TEXT NOT NULL,
    received_at  TEXT NOT NULL
);
"""


class Database:
    def __init__(self, path: str | Path = "secondthought.sqlite3"):
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    @contextmanager
    def tx(self):
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        self._conn.close()


class ProfileRepo:
    def __init__(self, db: Database):
        self.db = db

    def save(self, shopper_id: str, payload: dict, now: datetime) -> None:
        with self.db.tx() as c:
            c.execute(
                "INSERT INTO profiles(shopper_id, payload, updated_at) VALUES(?,?,?) "
                "ON CONFLICT(shopper_id) DO UPDATE SET payload=excluded.payload, "
                "updated_at=excluded.updated_at",
                (shopper_id, json.dumps(payload), now.isoformat()))

    def get(self, shopper_id: str) -> dict | None:
        row = self.db._conn.execute(
            "SELECT payload FROM profiles WHERE shopper_id=?", (shopper_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def delete(self, shopper_id: str) -> bool:
        with self.db.tx() as c:
            cur = c.execute("DELETE FROM profiles WHERE shopper_id=?", (shopper_id,))
        return cur.rowcount > 0


class ReservationRepo:
    def __init__(self, db: Database):
        self.db = db

    def save(self, r, now: datetime) -> None:
        payload = json.dumps(r.to_dict())
        with self.db.tx() as c:
            c.execute(
                "INSERT INTO reservations(id, shopper_id, merchant_id, amount_minor, currency,"
                " due_date, hold_until, invoice_id, payment_ref, state, payload, created_at,"
                " updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET state=excluded.state,"
                " invoice_id=excluded.invoice_id, payment_ref=excluded.payment_ref,"
                " payload=excluded.payload, updated_at=excluded.updated_at",
                (r.id, r.shopper_id, r.merchant_id, r.amount_minor, r.currency,
                 r.due_date.isoformat(), r.hold_until.isoformat(), r.invoice_id,
                 r.payment_ref, r.state.value, payload,
                 now.isoformat(), now.isoformat()))

    def get(self, rid: str):
        row = self.db._conn.execute(
            "SELECT payload FROM reservations WHERE id=?", (rid,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_open(self) -> list[dict]:
        rows = self.db._conn.execute(
            "SELECT payload FROM reservations WHERE state='RESERVED'").fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def list_for_shopper(self, shopper_id: str) -> list[dict]:
        rows = self.db._conn.execute(
            "SELECT payload FROM reservations WHERE shopper_id=? ORDER BY created_at DESC",
            (shopper_id,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def by_invoice(self, invoice_id: str):
        row = self.db._conn.execute(
            "SELECT payload FROM reservations WHERE invoice_id=?", (invoice_id,)).fetchone()
        return json.loads(row["payload"]) if row else None


class LedgerRepo:
    def __init__(self, db: Database):
        self.db = db

    def add(self, shopper_id: str, merchant_id: str, amount_minor: int,
            kind: str, ref: str, now: datetime) -> None:
        with self.db.tx() as c:
            c.execute(
                "INSERT INTO ledger(shopper_id, merchant_id, amount_minor, kind, ref, created_at)"
                " VALUES(?,?,?,?,?,?)",
                (shopper_id, merchant_id, amount_minor, kind, ref, now.isoformat()))

    def open_plans(self, shopper_id: str) -> list[dict]:
        rows = self.db._conn.execute(
            "SELECT merchant_id, amount_minor, kind, ref, created_at FROM ledger "
            "WHERE shopper_id=? ORDER BY created_at DESC", (shopper_id,)).fetchall()
        return [dict(r) for r in rows]

    def exposure_minor(self, shopper_id: str) -> int:
        row = self.db._conn.execute(
            "SELECT COALESCE(SUM(amount_minor),0) AS total FROM ledger WHERE shopper_id=?",
            (shopper_id,)).fetchone()
        return int(row["total"])


class WebhookRepo:
    """Exactly-once processing for an at-least-once delivery model."""

    def __init__(self, db: Database):
        self.db = db

    def seen(self, event_id: str) -> bool:
        row = self.db._conn.execute(
            "SELECT 1 FROM webhook_events WHERE event_id=?", (event_id,)).fetchone()
        return row is not None

    def mark(self, event_id: str, kind: str, now: datetime) -> None:
        with self.db.tx() as c:
            c.execute(
                "INSERT OR IGNORE INTO webhook_events(event_id, kind, received_at)"
                " VALUES(?,?,?)", (event_id, kind, now.isoformat()))

    def claim(self, event_id: str, kind: str, now: datetime) -> bool:
        """Atomically claim an event ID; false means it was already processed."""
        with self.db.tx() as c:
            cur = c.execute(
                "INSERT OR IGNORE INTO webhook_events(event_id, kind, received_at)"
                " VALUES(?,?,?)", (event_id, kind, now.isoformat()))
        return cur.rowcount == 1

    def release(self, event_id: str) -> None:
        """Release a claim when application failed before the event was handled."""
        with self.db.tx() as c:
            c.execute("DELETE FROM webhook_events WHERE event_id=?", (event_id,))


def iso_now() -> datetime:
    return datetime.now().replace(microsecond=0)


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)
