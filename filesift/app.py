"""Main window, scan tab, tray reminders and entry point."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QGroupBox, QHBoxLayout, QLabel,
                               QListWidget, QMainWindow, QMessageBox, QProgressBar, QPushButton,
                               QSlider, QStyle, QSystemTrayIcon, QTabWidget, QVBoxLayout, QWidget)

from . import __version__, store, textextract
from .models import human_size
from .pipeline import ScanOptions
from .reminders import due_reminders
from .ui_bills import BillsTab
from .ui_common import AppContext
from .ui_review import CleanupTab, DuplicatesTab, protected_dirs_for
from .worker import ScanWorker


class ScanTab(QWidget):
    def __init__(self, ctx: AppContext, on_result, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.on_result = on_result
        self.worker: ScanWorker | None = None

        self.roots = QListWidget()
        self.prot = QListWidget()
        saved = ctx.settings.get_list("scan_roots") or [str(p) for p in (Path.home() / "Pictures", Path.home() / "Downloads") if p.exists()]
        self.roots.addItems(saved)
        self.prot.addItems(ctx.settings.get_list("protected_dirs"))

        def box(title, lst, hint):
            g = QGroupBox(title)
            lay = QVBoxLayout(g)
            lay.addWidget(QLabel(hint))
            lay.addWidget(lst)
            row = QHBoxLayout()
            add, rem = QPushButton("Add folder..."), QPushButton("Remove")
            add.clicked.connect(lambda: self._add(lst))
            rem.clicked.connect(lambda: self._remove(lst))
            row.addWidget(add)
            row.addWidget(rem)
            row.addStretch(1)
            lay.addLayout(row)
            return g

        self.similar = QCheckBox("Find similar images (resized / recompressed copies)")
        self.similar.setChecked(True)
        self.strict = QSlider(Qt.Orientation.Horizontal)
        self.strict.setRange(2, 12)
        self.strict.setValue(6)
        self.strict_label = QLabel()
        self.strict.valueChanged.connect(self._strict_changed)
        self._strict_changed()
        self.text = QCheckBox("Read text with OCR / PDF (finds bills, IDs, OTPs; slower)")
        ocr, pdf = textextract.ocr_available(), textextract.has_pdf_support()
        self.text.setChecked(ocr or pdf)
        self.text.setEnabled(ocr or pdf)
        self.text_status = QLabel(
            f"OCR (Tesseract): {'found' if ocr else 'not installed'}   |   PDF text (PyMuPDF): "
            f"{'found' if pdf else 'not installed'}")

        opts = QGroupBox("Options")
        ol = QVBoxLayout(opts)
        ol.addWidget(self.similar)
        srow = QHBoxLayout()
        srow.addWidget(QLabel("Strict"))
        srow.addWidget(self.strict, 1)
        srow.addWidget(QLabel("Loose"))
        srow.addWidget(self.strict_label)
        ol.addLayout(srow)
        ol.addWidget(self.text)
        ol.addWidget(self.text_status)
        self.vault_label = QLabel()
        vbtn = QPushButton("Change vault folder...")
        vbtn.clicked.connect(self._pick_vault)
        vrow = QHBoxLayout()
        vrow.addWidget(self.vault_label, 1)
        vrow.addWidget(vbtn)
        ol.addLayout(vrow)
        self._vault_text()

        self.start = QPushButton("Start scan")
        self.start.clicked.connect(self.start_scan)
        self.cancel = QPushButton("Cancel")
        self.cancel.setEnabled(False)
        self.cancel.clicked.connect(lambda: self.worker and self.worker.cancel())
        self.bar = QProgressBar()
        self.stage = QLabel("Idle")

        lay = QVBoxLayout(self)
        two = QHBoxLayout()
        two.addWidget(box("Folders to scan", self.roots, "Subfolders are included."))
        two.addWidget(box("Protected folders", self.prot,
                          "Scanned but never suggested for deletion (e.g. your organised albums). "
                          "The bill vault is always protected."))
        lay.addLayout(two, 1)
        lay.addWidget(opts)
        row = QHBoxLayout()
        row.addWidget(self.start)
        row.addWidget(self.cancel)
        row.addWidget(self.bar, 1)
        lay.addLayout(row)
        lay.addWidget(self.stage)

    def _strict_changed(self) -> None:
        v = self.strict.value()
        self.strict_label.setText(f"distance {v}" + (" (recommended)" if v == 6 else ""))

    def _vault_text(self) -> None:
        self.vault_label.setText(f"Vault folder (bills + 'Important'): {self.ctx.settings.vault_dir}")

    def _pick_vault(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose vault folder", str(self.ctx.settings.vault_dir))
        if d:
            self.ctx.settings.vault_dir = d
            self._vault_text()

    def _add(self, lst: QListWidget) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose folder")
        if d and d not in [lst.item(i).text() for i in range(lst.count())]:
            lst.addItem(d.replace("/", "\\"))

    @staticmethod
    def _remove(lst: QListWidget) -> None:
        for it in lst.selectedItems():
            lst.takeItem(lst.row(it))

    @staticmethod
    def _items(lst: QListWidget) -> list[str]:
        return [lst.item(i).text() for i in range(lst.count())]

    def start_scan(self) -> None:
        roots = self._items(self.roots)
        if not roots:
            QMessageBox.information(self, "Scan", "Add at least one folder to scan.")
            return
        self.ctx.settings.set_list("scan_roots", roots)
        self.ctx.settings.set_list("protected_dirs", self._items(self.prot))
        opts = ScanOptions(
            roots=roots,
            protected_dirs=protected_dirs_for(self.ctx),
            similar=self.similar.isChecked(),
            max_distance=self.strict.value(),
            use_text=self.text.isChecked(),
        )
        self.worker = ScanWorker(opts, self)
        self.worker.progress.connect(self._progress)
        self.worker.finished_ok.connect(self._done)
        self.worker.failed.connect(self._failed)
        self.start.setEnabled(False)
        self.cancel.setEnabled(True)
        self.worker.start()

    def _progress(self, stage: str, done: int, total: int) -> None:
        self.stage.setText(f"{stage}..." + (f" {done}/{total}" if total else ""))
        self.bar.setRange(0, total if total else 0)
        self.bar.setValue(done)

    def _reset(self) -> None:
        self.start.setEnabled(True)
        self.cancel.setEnabled(False)
        self.bar.setRange(0, 1)
        self.bar.setValue(0)

    def _done(self, result) -> None:
        self._reset()
        total = sum(f.size for f in result.files)
        self.stage.setText(f"Done: {len(result.files)} files ({human_size(total)}), "
                           f"{len(result.groups)} duplicate groups.")
        self.on_result(result)

    def _failed(self, msg: str) -> None:
        self._reset()
        self.stage.setText(msg)


class MainWindow(QMainWindow):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.setWindowTitle(f"FileSift {__version__}")
        self.resize(1250, 800)

        self.dups = DuplicatesTab(ctx)
        self.cleanup = CleanupTab(ctx)
        self.bills = BillsTab(ctx)
        self.scan = ScanTab(ctx, self.on_result)
        self.cleanup.add_bill.connect(self.new_bill_from_file)
        self.dups.changed.connect(lambda: None)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.scan, "1. Scan")
        self.tabs.addTab(self.dups, "2. Duplicates")
        self.tabs.addTab(self.cleanup, "3. Cleanup (old / junk / important)")
        self.tabs.addTab(self.bills, "4. Bills & Warranty")
        self.setCentralWidget(self.tabs)

        self.tray = QSystemTrayIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView), self)
        self.tray.setToolTip("FileSift")
        self.tray.show()
        QTimer.singleShot(1500, self.check_reminders)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_reminders)
        self.timer.start(60 * 60 * 1000)

    def on_result(self, result) -> None:
        self.dups.load(result.groups)
        self.cleanup.load(result.files)
        self.tabs.setCurrentWidget(self.dups if result.groups else self.cleanup)

    def new_bill_from_file(self, path: str, text: str) -> None:
        self.tabs.setCurrentWidget(self.bills)
        self.bills.open_dialog(file_path=path, text=text)

    def check_reminders(self) -> None:
        due = due_reminders(self.ctx.con)
        if due:
            show_reminders(self.tray, due)
            self.bills.refresh()


def show_reminders(tray: QSystemTrayIcon, due) -> None:
    lines = [d.message for d in due[:6]]
    if len(due) > 6:
        lines.append(f"...and {len(due) - 6} more")
    tray.showMessage("FileSift: warranty reminder", "\n".join(lines), QSystemTrayIcon.MessageIcon.Warning, 15000)


def make_context() -> AppContext:
    con = store.connect()
    return AppContext(con, store.Settings(con), store.Cache(con))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv if argv is None else argv
    app = QApplication(argv)
    app.setStyle("Fusion")
    ctx = make_context()

    if "--reminders" in argv:  # headless run from Task Scheduler
        due = due_reminders(ctx.con)
        if not due:
            return 0
        tray = QSystemTrayIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView))
        tray.show()
        show_reminders(tray, due)
        QTimer.singleShot(20000, app.quit)
        return app.exec()

    win = MainWindow(ctx)
    win.show()
    return app.exec()
