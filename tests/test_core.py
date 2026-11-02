"""Smoke tests for the core logic. Run:  python -m pytest tests  (or python tests/test_core.py)"""
import os
import shutil
import sys
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from filesift import bills, reminders, store  # noqa: E402
from filesift.duplicates import find_duplicates, pick_keeper  # noqa: E402
from filesift.pipeline import ScanOptions, run_scan  # noqa: E402


def _photo(path, seed, size=(400, 300), scale=1.0, fmt="JPEG", quality=90):
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 255, (12, 16, 3), dtype=np.uint8)
    im = Image.fromarray(base).resize(size, Image.Resampling.BICUBIC)
    if scale != 1.0:
        im = im.resize((int(size[0] * scale), int(size[1] * scale)))
    im.save(path, fmt, **({"quality": quality} if fmt == "JPEG" else {}))


def test_scan_duplicates_and_classify():
    tmp = Path(tempfile.mkdtemp())
    try:
        _photo(tmp / "a.jpg", 1)
        shutil.copy(tmp / "a.jpg", tmp / "a_copy.jpg")           # exact duplicate
        _photo(tmp / "a_small.jpg", 1, scale=0.5, quality=60)     # similar (resized)
        _photo(tmp / "other.jpg", 2)                              # unrelated
        _photo(tmp / "Screenshot_2020-01-01-10-00-00.png", 3, size=(1080, 2400), fmt="PNG")
        old = time.time() - 900 * 86400
        os.utime(tmp / "Screenshot_2020-01-01-10-00-00.png", (old, old))
        (tmp / "doc.pdf").write_bytes(b"%PDF-1.4 same")
        (tmp / "doc2.pdf").write_bytes(b"%PDF-1.4 same")

        con = store.connect(":memory:")
        res = run_scan(ScanOptions([str(tmp)], similar=True), store.Cache(con))
        kinds = sorted((g.kind, len(g.files)) for g in res.groups)
        assert ("similar", 3) in kinds, kinds          # a, a_copy, a_small
        assert ("exact", 2) in kinds, kinds            # the two PDFs
        assert all("other.jpg" not in [f.name for f in g.files] for g in res.groups)

        shot = next(f for f in res.files if f.name.startswith("Screenshot"))
        assert shot.category == "screenshot" and shot.bucket == "delete", (shot.category, shot.score)

        grp = next(g for g in res.groups if len(g.files) == 3)
        assert pick_keeper(grp, "Highest resolution").name in ("a.jpg", "a_copy.jpg")

        # protected folders are never proposed for deletion
        res2 = run_scan(ScanOptions([str(tmp)], protected_dirs=[str(tmp)]), store.Cache(con))
        assert all(f.bucket == "keep" for f in res2.files)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def test_bills_and_reminders():
    con = store.connect(":memory:")
    assert bills.add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)
    assert bills.parse_warranty_months("1 year warranty on product") == 12
    assert bills.parse_warranty_months("Warranty: 24 months") == 24
    f = bills.extract_bill_fields("Croma Retail\nInvoice No: INV-1234\n12/03/2024\nTotal Amount Rs. 45,999.00\n2 years warranty")
    assert f["purchase_date"] == "2024-03-12" and f["amount"] == 45999.0
    assert f["invoice_no"] == "INV-1234" and f["warranty_months"] == 24

    today = date(2025, 1, 1)
    b = bills.Bill(product="TV", purchase_date="2024-02-01", warranty_months=12, return_days=0)
    bills.save_bill(con, b)
    assert b.warranty_end == "2025-02-01"
    due = reminders.due_reminders(con, today)                 # 31 days left -> nothing
    assert due == []
    due = reminders.due_reminders(con, date(2025, 1, 5))      # 27 days -> stage 30
    assert [(d.kind, d.stage) for d in due] == [("warranty", 30)]
    assert reminders.due_reminders(con, date(2025, 1, 6)) == []  # already sent
    due = reminders.due_reminders(con, date(2025, 1, 30))     # 2 days -> stage 7
    assert due and due[0].stage == 7
    out = Path(tempfile.mkdtemp()) / "w.ics"
    assert bills.export_ics(bills.list_bills(con), out) == 1
    assert "BEGIN:VEVENT" in out.read_text()


if __name__ == "__main__":
    test_scan_duplicates_and_classify()
    test_bills_and_reminders()
    print("ALL OK")
