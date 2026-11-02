from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from .pipeline import ScanOptions, run_scan
from .store import Cache, connect


class ScanWorker(QThread):
    progress = Signal(str, int, int)
    finished_ok = Signal(object)
    failed = Signal(str)

    def __init__(self, opts: ScanOptions, parent=None):
        super().__init__(parent)
        self.opts = opts
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        con = None
        try:
            con = connect()  # own connection: sqlite objects are thread-bound
            result = run_scan(self.opts, Cache(con), self.progress.emit, lambda: self._cancel)
            if self._cancel:
                self.failed.emit("Scan cancelled")
            else:
                self.finished_ok.emit(result)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            if con:
                con.close()
