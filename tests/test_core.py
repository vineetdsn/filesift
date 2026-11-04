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

from filesift import store  # noqa: E402
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


def test_store_migration():
    """Old DB with bills table must survive opening with new store."""
    import sqlite3, tempfile, os
    tmp = tempfile.mktemp(suffix=".db")
    try:
        con_old = sqlite3.connect(tmp)
        con_old.executescript("""
            CREATE TABLE IF NOT EXISTS cache (path TEXT PRIMARY KEY, size INTEGER, mtime REAL, feat TEXT, sha TEXT, text TEXT);
            CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
            CREATE TABLE IF NOT EXISTS bills (id INTEGER PRIMARY KEY, product TEXT);
            CREATE TABLE IF NOT EXISTS reminders_sent (bill_id INTEGER, kind TEXT, stage INTEGER);
            INSERT INTO bills VALUES (1, 'TV');
            INSERT INTO settings VALUES ('vault_dir', '/some/path');
        """)
        con_old.commit()
        con_old.close()
        from filesift.store import connect, Settings
        con_new = connect(tmp)
        rows = con_new.execute("SELECT * FROM bills").fetchall()
        assert len(rows) == 1, "bills table must be preserved"
        s = Settings(con_new)
        assert "some" in str(s.vault_dir), f"vault_dir not read: {s.vault_dir}"
        con_new.close()
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


if __name__ == "__main__":
    test_scan_duplicates_and_classify()
    test_store_migration()
    print("ALL OK")
