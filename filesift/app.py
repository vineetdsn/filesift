"""Main window and entry point — modern UI/UX Pro Max."""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QStackedWidget, QWidget)

from . import icons, store, theme
from .context import AppContext
from .page_cleanup import CleanupPage
from .page_duplicates import DuplicatesPage
from .page_scan import ScanPage
from .widgets import Sidebar


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle("FileSift — Storage Optimizer")
        self.setWindowIcon(icons.icon("brand", "#E2B170"))
        self.resize(1280, 820)
        self.setMinimumSize(1020, 680)

        central = QWidget()
        self.setCentralWidget(central)
        lay = QHBoxLayout(central)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._sidebar = Sidebar(central)
        self._stack = QStackedWidget(central)
        lay.addWidget(self._sidebar)
        lay.addWidget(self._stack, 1)

        self._scan_page = ScanPage(ctx, self._stack)
        self._dup_page = DuplicatesPage(ctx, self._stack)
        self._clean_page = CleanupPage(ctx, self._stack)

        self._stack.addWidget(self._scan_page)
        self._stack.addWidget(self._dup_page)
        self._stack.addWidget(self._clean_page)

        self._page_map = {"scan": 0, "duplicates": 1, "cleanup": 2}
        self._sidebar.page_requested.connect(self._show_page)
        self._scan_page.result_ready.connect(self._on_result)
        self._show_page("scan")

    def _show_page(self, page_id: str) -> None:
        idx = self._page_map.get(page_id, 0)
        self._stack.setCurrentIndex(idx)
        self._sidebar.set_active(page_id)

    def _on_result(self, result) -> None:
        self._dup_page.load(result.groups)
        self._clean_page.load(result.files)
        n_dups = len(result.groups)
        n_safe = self._clean_page.safe_to_delete_count()
        self._sidebar.set_badges(n_dups, n_safe)
        if n_dups > 0:
            self._show_page("duplicates")
        else:
            self._show_page("cleanup")

    def closeEvent(self, event) -> None:
        worker = getattr(self._scan_page, "_worker", None)
        if worker and worker.isRunning():
            worker.cancel()
            worker.wait(3000)
        event.accept()


def make_context() -> AppContext:
    con = store.connect()
    return AppContext(con, store.Settings(con), store.Cache(con))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    app = QApplication([a for a in argv if a != "--reminders"])
    app.setStyle("Fusion")
    theme.pick_font(app)
    theme.apply_theme(app, "dark")
    ctx = make_context()
    win = MainWindow(ctx)
    win.show()
    return app.exec()
