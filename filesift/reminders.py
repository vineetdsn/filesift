"""Warranty / return-window reminder logic (UI-independent)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from .bills import Bill, list_bills

STAGES = (30, 7, 1, 0)  # days before the date; 0 = on/after the date


@dataclass
class Reminder:
    bill: Bill
    kind: str   # warranty | return
    stage: int
    days_left: int

    @property
    def message(self) -> str:
        what = "Warranty" if self.kind == "warranty" else "Return window"
        if self.days_left < 0:
            return f"{what} of {self.bill.product} expired {-self.days_left} day(s) ago"
        if self.days_left == 0:
            return f"{what} of {self.bill.product} ends today"
        return f"{what} of {self.bill.product} ends in {self.days_left} day(s)"


def stage_for(days_left: int) -> int | None:
    """Smallest stage whose window the date is inside. Expired items older than 14 days are ignored."""
    if days_left < -14:
        return None
    for s in sorted(STAGES):
        if days_left <= s:
            return s
    return None


def due_reminders(con: sqlite3.Connection, today: date | None = None, mark_sent: bool = True) -> list[Reminder]:
    today = today or date.today()
    out: list[Reminder] = []
    for b in list_bills(con):
        for kind, end in (("warranty", b.warranty_end_date), ("return", b.return_end_date)):
            if not end:
                continue
            left = (end - today).days
            stage = stage_for(left)
            if stage is None:
                continue
            seen = con.execute(
                "SELECT 1 FROM reminders_sent WHERE bill_id=? AND kind=? AND stage=?",
                (b.id, kind, stage)).fetchone()
            if seen:
                continue
            out.append(Reminder(b, kind, stage, left))
            if mark_sent:
                con.execute("INSERT OR IGNORE INTO reminders_sent VALUES(?,?,?)", (b.id, kind, stage))
    con.commit()
    return out
