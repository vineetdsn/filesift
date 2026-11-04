"""Scan page: folder selection, options, stats and progress."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QProgressBar, QPushButton, QSlider,
                               QVBoxLayout, QWidget)

from . import presenters, textextract
from .context import AppContext
from .pipeline import ScanOptions
from .widgets import Card, ListRow, PillButton, StatCard, ToggleSwitch
from .worker import ScanWorker

STAT_LABELS = ["Files scanned", "Total size", "Duplicate groups", "Reclaimable",
               "Safe to delete"]


class ScanPage(QWidget):
    result_ready = Signal(object)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._worker: ScanWorker | None = None
        self._stat_cards: list[StatCard] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(16)

        # --- folder cards ---
        folders = QHBoxLayout()
        folders.setSpacing(16)
        folders.addWidget(self._folder_card("Folders to scan", "scan_roots",
                                            "Add the folders you want cleaned up."), 1)
        folders.addWidget(self._folder_card("Protected folders", "protected_dirs",
                                            "Scanned but never deleted (e.g. albums)."), 1)
        root.addLayout(folders, 1)

        # --- important folder + options ---
        root.addWidget(self._important_row())
        root.addWidget(self._options_card())

        # --- stat cards ---
        stats = QHBoxLayout()
        stats.setSpacing(12)
        for label in STAT_LABELS:
            card = StatCard(label)
            self._stat_cards.append(card)
            stats.addWidget(card, 1)
        root.addLayout(stats)

        # --- progress + actions ---
        self._bar = QProgressBar()
        self._bar.setRange(0, 1)
        self._bar.setValue(0)
        self._stage = QLabel("Idle")
        self._stage.setProperty("kind", "muted")
        self._start = PillButton("Start scan", primary=True)
        self._cancel = PillButton("Cancel")
        self._cancel.setEnabled(False)
        self._start.clicked.connect(self.start_scan)
        self._cancel.clicked.connect(self._cancel_scan)
        actions = QHBoxLayout()
        actions.addWidget(self._start)
        actions.addWidget(self._cancel)
        actions.addStretch(1)
        actions.addWidget(self._bar, 1)
        root.addLayout(actions)
        root.addWidget(self._stage)

    # ----- folder cards -----
    def _folder_card(self, title: str, settings_key: str, hint: str) -> Card:
        card = Card("panel")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(8)
        head = QLabel(title)
        f = head.font()
        f.setBold(True)
        head.setFont(f)
        sub = QLabel(hint)
        sub.setProperty("kind", "muted")
        sub.setWordWrap(True)
        lst = QListWidget()
        lst.setAlternatingRowColors(False)
        if settings_key == "scan_roots":
            saved = self.ctx.settings.get_list("scan_roots")
            if not saved:
                saved = [str(p) for p in (Path.home() / "Pictures", Path.home() / "Downloads")
                         if p.exists()]
            self._roots = lst
        else:
            saved = self.ctx.settings.get_list("protected_dirs")
            self._prot = lst
        for s in saved:
            lst.addItem(QListWidgetItem(s))
        btn_row = QHBoxLayout()
        add = PillButton("Add folder…")
        rem = PillButton("Remove")
        add.clicked.connect(lambda: self._add_folder(lst))
        rem.clicked.connect(lambda: self._remove_folder(lst))
        btn_row.addWidget(add)
        btn_row.addWidget(rem)
        btn_row.addStretch(1)
        lay.addWidget(head)
        lay.addWidget(sub)
        lay.addWidget(lst, 1)
        lay.addLayout(btn_row)
        return card

    def _add_folder(self, lst: QListWidget) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose folder")
        if not d:
            return
        d = d.replace("/", "\\")
        existing = [lst.item(i).text() for i in range(lst.count())]
        if d not in existing:
            lst.addItem(QListWidgetItem(d))

    def _remove_folder(self, lst: QListWidget) -> None:
        for it in lst.selectedItems():
            lst.takeItem(lst.row(it))

    @staticmethod
    def _items(lst: QListWidget) -> list[str]:
        return [lst.item(i).text() for i in range(lst.count())]

    # ----- important + options -----
    def _important_row(self) -> ListRow:
        self._vault_label = ListRow("important", "Important folder",
                                    str(self.ctx.settings.vault_dir))
        change = PillButton("Change")
        change.clicked.connect(self._pick_vault)
        self._vault_label.set_trailing(change)
        return self._vault_label

    def _pick_vault(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Choose Important folder", str(self.ctx.settings.vault_dir))
        if d:
            self.ctx.settings.vault_dir = d
            self._vault_label.set_subtitle(str(self.ctx.settings.vault_dir))

    def _options_card(self) -> Card:
        card = Card("panel")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)
        head = QLabel("Options")
        f = head.font()
        f.setBold(True)
        head.setFont(f)
        lay.addWidget(head)

        self._similar = ToggleSwitch()
        self._similar.setChecked(True)
        row_sim = ListRow("image", "Find similar images",
                          "Resized or recompressed copies of the same photo.")
        row_sim.set_trailing(self._similar)

        self._distance = QSlider(Qt.Orientation.Horizontal)
        self._distance.setRange(2, 12)
        self._distance.setValue(6)
        self._distance.setFixedWidth(160)
        self._distance_lbl = QLabel("distance 6")
        dist_box = QWidget()
        dh = QHBoxLayout(dist_box)
        dh.setContentsMargins(0, 0, 0, 0)
        dh.setSpacing(8)
        dh.addWidget(self._distance)
        dh.addWidget(self._distance_lbl)
        self._distance.valueChanged.connect(
            lambda v: self._distance_lbl.setText(f"distance {v}"))
        row_dist = ListRow("scan", "Match strictness", "Lower = only near-identical, higher = more matches.")
        row_dist.set_trailing(dist_box)

        self._text = ToggleSwitch()
        ocr = textextract.ocr_available()
        pdf = textextract.has_pdf_support()
        self._text.setChecked(ocr or pdf)
        self._text.setEnabled(ocr or pdf)
        status = (f"OCR (Tesseract): {'found' if ocr else 'not installed'}   |   "
                  f"PDF (PyMuPDF): {'found' if pdf else 'not installed'}")
        row_text = ListRow("file", "Read text with OCR / PDF",
                           f"Finds bills, IDs, OTPs. Slower. {status}")
        row_text.set_trailing(self._text)

        lay.addWidget(row_sim)
        lay.addWidget(row_dist)
        lay.addWidget(row_text)
        return card

    # ----- scan -----
    def start_scan(self) -> None:
        roots = self._items(self._roots)
        if not roots:
            self._stage.setText("Add at least one folder to scan.")
            return
        self.ctx.settings.set_list("scan_roots", roots)
        self.ctx.settings.set_list("protected_dirs", self._items(self._prot))
        opts = ScanOptions(
            roots=roots,
            protected_dirs=self.ctx.protected_dirs(),
            similar=self._similar.isChecked(),
            max_distance=self._distance.value(),
            use_text=self._text.isChecked(),
        )
        self._worker = ScanWorker(opts, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._start.setEnabled(False)
        self._cancel.setEnabled(True)
        self._bar.setRange(0, 0)
        self._stage.setText("Starting…")
        self._worker.start()

    def _cancel_scan(self) -> None:
        if self._worker:
            self._worker.cancel()

    def _on_progress(self, stage: str, done: int, total: int) -> None:
        self._stage.setText(presenters.stage_text(stage, done, total))
        if total > 0:
            self._bar.setRange(0, total)
            self._bar.setValue(done)
        else:
            self._bar.setRange(0, 0)

    def _reset(self) -> None:
        self._start.setEnabled(True)
        self._cancel.setEnabled(False)
        self._bar.setRange(0, 1)
        self._bar.setValue(0)

    def _on_done(self, result) -> None:
        self._reset()
        stats = presenters.scan_stats(result)
        for card, text in zip(self._stat_cards, presenters.stat_texts(stats)):
            card.set_value(text)
        self._stage.setText(presenters.done_text(stats))
        self.result_ready.emit(result)

    def _on_failed(self, msg: str) -> None:
        self._reset()
        self._stage.setText(msg)
