"""SQLite storage: feature cache, bills, reminder log, settings."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

APP_DIR = Path.home() / ".filesift"
DB_PATH = APP_DIR / "filesift.db"
DEFAULT_VAULT = Path.home() / "Documents" / "FileSift Vault"

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    path TEXT PRIMARY KEY, size INTEGER, mtime REAL, feat TEXT, sha TEXT, text TEXT
);
CREATE TABLE IF NOT EXISTS bills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product TEXT NOT NULL, category TEXT DEFAULT '', store TEXT DEFAULT '',
    purchase_date TEXT DEFAULT '', amount REAL DEFAULT 0,
    warranty_months INTEGER DEFAULT 0, warranty_end TEXT DEFAULT '',
    return_days INTEGER DEFAULT 0, serial TEXT DEFAULT '', invoice_no TEXT DEFAULT '',
    notes TEXT DEFAULT '', file_path TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS reminders_sent (
    bill_id INTEGER, kind TEXT, stage INTEGER, PRIMARY KEY (bill_id, kind, stage)
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT);
"""


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


class Settings:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def get(self, key: str, default: str = "") -> str:
        row = self.con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        self.con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, value))
        self.con.commit()

    def get_list(self, key: str) -> list[str]:
        try:
            return list(json.loads(self.get(key, "[]")))
        except ValueError:
            return []

    def set_list(self, key: str, values: list[str]) -> None:
        self.set(key, json.dumps(values))

    @property
    def vault_dir(self) -> Path:
        return Path(self.get("vault_dir", str(DEFAULT_VAULT)))

    @vault_dir.setter
    def vault_dir(self, p: Path | str) -> None:
        self.set("vault_dir", str(p))


class Cache:
    """Per-file cache keyed by (path, size, mtime) so re-scans are fast."""

    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def get(self, path: str, size: int, mtime: float) -> sqlite3.Row | None:
        row = self.con.execute("SELECT * FROM cache WHERE path=?", (path,)).fetchone()
        if row and row["size"] == size and abs(row["mtime"] - mtime) < 1e-6:
            return row
        return None

    def put(self, path: str, size: int, mtime: float, feat: dict | None = None,
            sha: str | None = None, text: str | None = None) -> None:
        old = self.get(path, size, mtime)
        feat_s = json.dumps(feat) if feat is not None else (old["feat"] if old else None)
        sha = sha if sha is not None else (old["sha"] if old else None)
        text = text if text is not None else (old["text"] if old else None)
        self.con.execute(
            "INSERT OR REPLACE INTO cache(path,size,mtime,feat,sha,text) VALUES(?,?,?,?,?,?)",
            (path, size, mtime, feat_s, sha, text),
        )

    def commit(self) -> None:
        self.con.commit()

    def forget(self, paths: list[str]) -> None:
        self.con.executemany("DELETE FROM cache WHERE path=?", [(p,) for p in paths])
        self.con.commit()
