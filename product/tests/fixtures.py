"""Three shoppers whose months are shaped differently — and a wired service."""

from datetime import date, datetime

from secondthought.app.approvals import ApprovalGate
from secondthought.app.checkout import CheckoutService
from secondthought.domain import Policy
from secondthought.infra.db import Database, LedgerRepo, ProfileRepo, ReservationRepo
from secondthought.infra.gateway import SimulatedGateway

TODAY = date(2026, 11, 1)
NOW = datetime(2026, 11, 1, 10, 0)

PROFILES = {
    # comfortable: two paydays, rent well covered
    "ada": {"opening_balance": 210000,
            "paydays": [{"due": "2026-11-05", "amount_minor": 200000},
                        {"due": "2026-11-19", "amount_minor": 200000},
                        {"due": "2026-12-03", "amount_minor": 200000}],
            "obligations": [{"label": "rent", "due": "2026-11-28",
                             "amount_minor": 145000, "essential": True}]},
    # fits, but not today: a car payment lands before the next payday
    "ben": {"opening_balance": 30000,
            "paydays": [{"due": "2026-11-07", "amount_minor": 260000}],
            "obligations": [{"label": "car loan", "due": "2026-11-20",
                             "amount_minor": 31200, "essential": True},
                            {"label": "rent", "due": "2026-11-28",
                             "amount_minor": 145000, "essential": True}]},
    # genuinely squeezed: even paying in full collides with rent
    "cleo": {"opening_balance": 45000,
             "paydays": [{"due": "2026-11-05", "amount_minor": 110000}],
             "obligations": [{"label": "rent", "due": "2026-11-25",
                              "amount_minor": 130000, "essential": True}]},
}


class Wired:
    """A full stack, in memory, with the simulated gateway."""

    def __init__(self, seed: bool = True):
        self.db = Database(":memory:")
        self.profiles = ProfileRepo(self.db)
        self.reservations = ReservationRepo(self.db)
        self.ledger = LedgerRepo(self.db)
        self.gateway = SimulatedGateway()
        self.approvals = ApprovalGate()
        self.service = CheckoutService(
            gateway=self.gateway, profiles=self.profiles,
            reservations=self.reservations, ledger=self.ledger,
            approvals=self.approvals, policy=Policy())
        if seed:
            for sid, payload in PROFILES.items():
                self.profiles.save(sid, payload, NOW)

    def close(self):
        self.db.close()
