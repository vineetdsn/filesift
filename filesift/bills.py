"""Bill / warranty vault: storage, date maths, text auto-fill, .ics export."""
from __future__ import annotations

import calendar
import re
import shutil
import sqlite3
from dataclasses import dataclass, fields
from datetime import date, datetime, timedelta
from pathlib import Path

CATEGORIES = ["Phone", "Laptop/PC", "TV/Display", "AC/Cooler", "Appliance", "Kitchen",
              "Furniture", "Vehicle", "Accessories", "Service/AMC", "Other"]


@dataclass
class Bill:
    product: str
    id: int | None = None
    category: str = ""
    store: str = ""
    purchase_date: str = ""  # ISO yyyy-mm-dd
    amount: float = 0.0
    warranty_months: int = 0
    warranty_end: str = ""   # ISO, derived from purchase_date + warranty_months unless set manually
    return_days: int = 0
    serial: str = ""
    invoice_no: str = ""
    notes: str = ""
    file_path: str = ""

    @property
    def warranty_end_date(self) -> date | None:
        return parse_iso(self.warranty_end)

    @property
    def return_end_date(self) -> date | None:
        pd = parse_iso(self.purchase_date)
        return pd + timedelta(days=self.return_days) if pd and self.return_days else None

    def days_left(self, today: date | None = None) -> int | None:
        end = self.warranty_end_date
        return (end - (today or date.today())).days if end else None


def parse_iso(s: str) -> date | None:
    try:
        return date.fromisoformat(s) if s else None
    except ValueError:
        return None


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def compute_warranty_end(purchase_iso: str, months: int) -> str:
    pd = parse_iso(purchase_iso)
    return add_months(pd, months).isoformat() if pd and months > 0 else ""


# ---------- DB access ----------
_FIELDS = [f.name for f in fields(Bill) if f.name != "id"]


def _row_to_bill(r: sqlite3.Row) -> Bill:
    return Bill(**{k: r[k] for k in r.keys()})


def list_bills(con: sqlite3.Connection) -> list[Bill]:
    rows = con.execute("SELECT * FROM bills ORDER BY CASE WHEN warranty_end='' THEN 1 ELSE 0 END, warranty_end").fetchall()
    return [_row_to_bill(r) for r in rows]


def save_bill(con: sqlite3.Connection, b: Bill) -> int:
    if not b.warranty_end and b.warranty_months:
        b.warranty_end = compute_warranty_end(b.purchase_date, b.warranty_months)
    vals = [getattr(b, k) for k in _FIELDS]
    if b.id is None:
        cur = con.execute(
            f"INSERT INTO bills({','.join(_FIELDS)}) VALUES({','.join('?' * len(_FIELDS))})", vals)
        b.id = cur.lastrowid
    else:
        con.execute(f"UPDATE bills SET {','.join(k + '=?' for k in _FIELDS)} WHERE id=?", vals + [b.id])
        con.execute("DELETE FROM reminders_sent WHERE bill_id=?", (b.id,))  # dates may have changed
    con.commit()
    return b.id


def delete_bill(con: sqlite3.Connection, bill_id: int) -> None:
    con.execute("DELETE FROM bills WHERE id=?", (bill_id,))
    con.execute("DELETE FROM reminders_sent WHERE bill_id=?", (bill_id,))
    con.commit()


# ---------- vault ----------
def _safe(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "_", s).strip(" .") or "file"


def copy_to_vault(src: str | Path, vault: Path, category: str, purchase_iso: str, product: str) -> Path:
    year = purchase_iso[:4] if purchase_iso else "Undated"
    dest_dir = vault / "Bills" / year / _safe(category or "Other")
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = Path(src)
    dest = dest_dir / f"{_safe(product)}{src.suffix.lower()}"
    n = 2
    while dest.exists():
        if dest.stat().st_size == src.stat().st_size and src.resolve() == dest.resolve():
            return dest
        dest = dest_dir / f"{_safe(product)} ({n}){src.suffix.lower()}"
        n += 1
    shutil.copy2(src, dest)
    return dest


# ---------- auto-fill from text ----------
_MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_abbr) if m}
_NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "ten": 10}


def parse_warranty_months(text: str) -> int:
    low = text.lower()
    for m in re.finditer(r"(\d+|one|two|three|four|five|six|ten)\s*[- ]?\s*(years?|yrs?|months?|mos?)\b[^.\n]{0,25}?warrant"
                         r"|warrant\w*[^.\n]{0,30}?(\d+|one|two|three|four|five|six|ten)\s*[- ]?\s*(years?|yrs?|months?|mos?)\b", low):
        num = m.group(1) or m.group(3)
        unit = m.group(2) or m.group(4)
        n = int(num) if num.isdigit() else _NUM_WORDS[num]
        return n * 12 if unit.startswith(("y",)) else n
    return 0


def _try_date(d: str, m: str, y: str) -> str:
    try:
        mm = int(m) if m.isdigit() else _MONTHS[m[:3].lower()]
        yy = int(y) + (2000 if len(y) == 2 else 0)
        return date(yy, mm, int(d)).isoformat()
    except (ValueError, KeyError):
        return ""


def find_dates(text: str) -> list[str]:
    out: list[str] = []
    for m in re.finditer(r"\b(\d{4})-(\d{2})-(\d{2})\b", text):
        try:
            out.append(date(int(m[1]), int(m[2]), int(m[3])).isoformat())
        except ValueError:
            pass
    for m in re.finditer(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})\b", text):
        v = _try_date(m[1], m[2], m[3])
        if v:
            out.append(v)
    for m in re.finditer(r"\b(\d{1,2})[ \-]([A-Za-z]{3})[a-z]*[ ,\-]+(\d{2,4})\b", text):
        v = _try_date(m[1], m[2], m[3])
        if v:
            out.append(v)
    return out


def extract_bill_fields(text: str) -> dict:
    """Best-effort guess of bill fields from OCR/PDF text. Always verify in the form."""
    res: dict = {}
    dates = [d for d in find_dates(text) if d <= date.today().isoformat()]
    if dates:
        res["purchase_date"] = dates[0]
    amt = re.search(r"(?:grand\s*total|total\s*amount|amount\s*paid|net\s*amount|total|amount)[^\d\n]{0,15}"
                    r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)", text, re.I)
    if amt:
        try:
            res["amount"] = float(amt.group(1).replace(",", ""))
        except ValueError:
            pass
    inv = re.search(r"(?:invoice|bill|receipt)\s*(?:no\.?|number|#)\s*[:\-]?\s*([A-Za-z0-9/\-]{3,})", text, re.I)
    if inv:
        res["invoice_no"] = inv.group(1)
    ser = re.search(r"(?:serial\s*(?:no\.?|number)|s/n|imei)\s*[:\-]?\s*([A-Za-z0-9]{6,})", text, re.I)
    if ser:
        res["serial"] = ser.group(1)
    months = parse_warranty_months(text)
    if months:
        res["warranty_months"] = months
    for line in text.splitlines():
        line = line.strip()
        if len(line) > 2 and re.search(r"[A-Za-z]{3}", line):
            res["store"] = line[:60]
            break
    return res


# ---------- calendar export ----------
def export_ics(bills: list[Bill], path: str | Path) -> int:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//FileSift//Warranty//EN"]
    n = 0
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for b in bills:
        for kind, d in (("Warranty ends", b.warranty_end_date), ("Return window ends", b.return_end_date)):
            if not d:
                continue
            n += 1
            summary = f"{kind}: {b.product}".replace(",", " ").replace("\n", " ")
            lines += [
                "BEGIN:VEVENT", f"UID:filesift-{b.id}-{n}@local", f"DTSTAMP:{stamp}",
                f"DTSTART;VALUE=DATE:{d.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(d + timedelta(days=1)).strftime('%Y%m%d')}",
                f"SUMMARY:{summary}",
            ]
            for trig in ("-P30D", "-P7D", "-P1D"):
                lines += ["BEGIN:VALARM", "ACTION:DISPLAY", f"DESCRIPTION:{summary}",
                          f"TRIGGER:{trig}", "END:VALARM"]
            lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    Path(path).write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return n
