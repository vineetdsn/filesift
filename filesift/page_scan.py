"""Scan page: folder selection, bento storage breakdown, options, and progress — Nordic Zen UI/UX."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QFileDialog, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QProgressBar, QScrollArea,
                               QSlider, QVBoxLayout, QWidget)

from . import icons, presenters, textextract, theme
from .context import AppContext
from .pipeline import ScanOptions
from .widgets import (Card, CategoryBentoCard, DiskUsageCard, ListRow,
                      PillButton, StatCard, ToggleSwitch)
from .worker import ScanWorker

STAT_LABELS = [
    "Files scanned",
    "Total size",
    "Duplicate groups",
    "Reclaimable space",
]


class ScanPage(QWidget):
    result_ready = Signal(object)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._worker: ScanWorker | None = None
        self._stat_cards: list[StatCard] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Scroll Area for responsive vertical breathing room
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        root = QVBoxLayout(container)
        root.setContentsMargins(32, 24, 32, 28)
        root.setSpacing(18)

        # --- Top Header & Action Row (Concept 6 Style) ---
        top_bar = QHBoxLayout()
        top_bar.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        page_title = QLabel("Storage Overview & Sifter")
        ptf = page_title.font()
        ptf.setPointSize(19)
        ptf.setWeight(QFont.Weight.DemiBold)
        page_title.setFont(ptf)

        page_desc = QLabel("Intelligent duplicate detection, photo similarity hashing, and storage reclamation.")
        page_desc.setProperty("kind", "muted")
        page_desc_f = page_desc.font()
        page_desc_f.setPointSize(11)
        page_desc.setFont(page_desc_f)

        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        top_bar.addLayout(title_box, 1)

        # Action Buttons on Top Right
        action_btn_box = QHBoxLayout()
        action_btn_box.setSpacing(10)

        self._cancel = PillButton("Cancel")
        self._cancel.setFixedHeight(38)
        self._cancel.setEnabled(False)
        self._cancel.clicked.connect(self._cancel_scan)

        self._start = PillButton("Start Deep Scan ⚡", primary=True)
        self._start.setFixedHeight(38)
        theme.add_glow(self._start)
        self._start.clicked.connect(self.start_scan)

        action_btn_box.addWidget(self._cancel)
        action_btn_box.addWidget(self._start)
        top_bar.addLayout(action_btn_box)

        root.addLayout(top_bar)

        # --- 1. Disk Usage Hero Card ---
        self._disk_card = DiskUsageCard(container)
        root.addWidget(self._disk_card)

        # --- 2. Concept 6 Category Bento Cards (3 Modular Cards) ---
        bento_row = QHBoxLayout()
        bento_row.setSpacing(14)

        self._bento_caches = CategoryBentoCard(
            "trash",
            "Temporary & App Caches",
            "14.2 GB",
            "System cache, temporary files, and app logs",
            checked=True,
            parent=container,
        )
        self._bento_photos = CategoryBentoCard(
            "image",
            "Duplicate & Similar Photos",
            "3.8 GB",
            "Perceptual image hashing & burst shots",
            checked=True,
            parent=container,
        )
        self._bento_installers = CategoryBentoCard(
            "file",
            "Orphaned Installers & Media",
            "9.4 GB",
            "Downloaded packages, archives & large media",
            checked=True,
            parent=container,
        )

        bento_row.addWidget(self._bento_caches)
        bento_row.addWidget(self._bento_photos)
        bento_row.addWidget(self._bento_installers)
        root.addLayout(bento_row)

        # --- 3. 2-Column Bento: Folders to Scan & Protection Vault ---
        folders_grid = QHBoxLayout()
        folders_grid.setSpacing(14)
        folders_grid.addWidget(self._folder_card(
            "Folders to Scan",
            "scan_roots",
            "Directories checked for duplicate files and clutter."
        ), 1)
        folders_grid.addWidget(self._protected_vault_card(), 1)
        root.addLayout(folders_grid)

        # --- 4. Detection Parameters Bento Card ---
        root.addWidget(self._options_card())

        # --- 5. Scan Summary & Progress Bento Section ---
        summary_card = Card("panel", container)
        sum_lay = QVBoxLayout(summary_card)
        sum_lay.setContentsMargins(18, 16, 18, 16)
        sum_lay.setSpacing(12)

        stats_head = QLabel("SCAN SUMMARY & METRICS")
        stats_head.setProperty("kind", "muted")
        shf = stats_head.font()
        shf.setPointSize(9)
        shf.setBold(True)
        stats_head.setFont(shf)
        sum_lay.addWidget(stats_head)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        for label in STAT_LABELS:
            card = StatCard(label, summary_card)
            self._stat_cards.append(card)
            stats_row.addWidget(card, 1)
        sum_lay.addLayout(stats_row)

        # Progress bar & stage readout
        self._bar = QProgressBar(summary_card)
        self._bar.setRange(0, 1)
        self._bar.setValue(0)
        self._bar.setFixedHeight(8)
        sum_lay.addWidget(self._bar)

        self._stage = QLabel("Ready — Click 'Start Deep Scan' or select custom directories above.", summary_card)
        self._stage.setProperty("kind", "muted")
        sum_lay.addWidget(self._stage)

        root.addWidget(summary_card)

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ----- Folder Cards -----
    def _folder_card(self, title: str, settings_key: str, hint: str) -> Card:
        card = Card("panel")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        header_row = QHBoxLayout()
        head = QLabel(title)
        f = head.font()
        f.setPointSize(12)
        f.setBold(True)
        head.setFont(f)
        header_row.addWidget(head)
        header_row.addStretch(1)

        sub = QLabel(hint)
        sub.setProperty("kind", "muted")
        sub.setWordWrap(True)

        lst = QListWidget()
        lst.setAlternatingRowColors(False)
        lst.setMinimumHeight(110)

        pal = theme.current()
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
            item = QListWidgetItem(icons.icon("folder", pal.accent), s)
            lst.addItem(item)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        add = PillButton("+ Add Folder…")
        add.setFixedHeight(30)
        rem = PillButton("Remove")
        rem.setFixedHeight(30)
        add.clicked.connect(lambda: self._add_folder(lst))
        rem.clicked.connect(lambda: self._remove_folder(lst))
        btn_row.addWidget(add)
        btn_row.addWidget(rem)
        btn_row.addStretch(1)

        lay.addLayout(header_row)
        lay.addWidget(sub)
        lay.addWidget(lst, 1)
        lay.addLayout(btn_row)
        return card

    def _protected_vault_card(self) -> Card:
        card = Card("panel")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        head = QLabel("Protected Folders & Safe Vault")
        f = head.font()
        f.setPointSize(12)
        f.setBold(True)
        head.setFont(f)

        sub = QLabel("Files in protected folders are NEVER deleted. Preserved files route to the Vault.")
        sub.setProperty("kind", "muted")
        sub.setWordWrap(True)

        lst = QListWidget()
        lst.setAlternatingRowColors(False)
        lst.setMinimumHeight(80)
        self._prot = lst

        pal = theme.current()
        saved = self.ctx.settings.get_list("protected_dirs")
        for s in saved:
            item = QListWidgetItem(icons.icon("shield", pal.accent), s)
            lst.addItem(item)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        add = PillButton("+ Add Protected…")
        add.setFixedHeight(30)
        rem = PillButton("Remove")
        rem.setFixedHeight(30)
        add.clicked.connect(lambda: self._add_folder(lst))
        rem.clicked.connect(lambda: self._remove_folder(lst))
        btn_row.addWidget(add)
        btn_row.addWidget(rem)
        btn_row.addStretch(1)

        # Vault destination row
        vault_box = QHBoxLayout()
        vault_box.setSpacing(8)
        vault_icon = QLabel()
        vault_icon.setPixmap(icons.icon("important", "#E2B170").pixmap(18, 18))

        self._vault_info = QLabel(f"Vault: {self.ctx.settings.vault_dir}")
        self._vault_info.setProperty("kind", "muted")
        vf = self._vault_info.font()
        vf.setPointSize(10)
        self._vault_info.setFont(vf)

        change_vault = PillButton("Change…")
        change_vault.setFixedHeight(28)
        change_vault.clicked.connect(self._pick_vault)

        vault_box.addWidget(vault_icon)
        vault_box.addWidget(self._vault_info, 1)
        vault_box.addWidget(change_vault)

        lay.addWidget(head)
        lay.addWidget(sub)
        lay.addWidget(lst, 1)
        lay.addLayout(btn_row)
        lay.addLayout(vault_box)
        return card

    def _add_folder(self, lst: QListWidget) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose folder")
        if not d:
            return
        d = d.replace("/", "\\")
        existing = [lst.item(i).text() for i in range(lst.count())]
        if d not in existing:
            pal = theme.current()
            item = QListWidgetItem(icons.icon("folder", pal.accent), d)
            lst.addItem(item)

    def _remove_folder(self, lst: QListWidget) -> None:
        for it in lst.selectedItems():
            lst.takeItem(lst.row(it))

    @staticmethod
    def _items(lst: QListWidget) -> list[str]:
        return [lst.item(i).text() for i in range(lst.count())]

    def _pick_vault(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Choose Important folder", str(self.ctx.settings.vault_dir))
        if d:
            self.ctx.settings.vault_dir = d
            self._vault_info.setText(f"Vault: {self.ctx.settings.vault_dir}")

    # ----- Options Bento Card -----
    def _options_card(self) -> Card:
        card = Card("panel")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        head = QLabel("SCAN & DETECTION ENGINES")
        head.setProperty("kind", "muted")
        hf = head.font()
        hf.setPointSize(9)
        hf.setBold(True)
        head.setFont(hf)
        lay.addWidget(head)

        self._similar = ToggleSwitch()
        self._similar.setChecked(True)
        row_sim = ListRow("image", "Find Similar Photos & Burst Shots",
                          "Detects resized, recompressed, or slight variations of the same photograph.")
        row_sim.set_trailing(self._similar)

        self._distance = QSlider(Qt.Orientation.Horizontal)
        self._distance.setRange(2, 12)
        self._distance.setValue(6)
        self._distance.setFixedWidth(140)
        self._distance_lbl = QLabel("Balanced (6)")
        dist_box = QWidget()
        dh = QHBoxLayout(dist_box)
        dh.setContentsMargins(0, 0, 0, 0)
        dh.setSpacing(10)
        dh.addWidget(self._distance)
        dh.addWidget(self._distance_lbl)

        def _update_dist_lbl(v: int) -> None:
            if v <= 4:
                desc = f"Strict ({v})"
            elif v <= 8:
                desc = f"Balanced ({v})"
            else:
                desc = f"Relaxed ({v})"
            self._distance_lbl.setText(desc)

        self._distance.valueChanged.connect(_update_dist_lbl)
        row_dist = ListRow("scan", "Match Strictness",
                           "Lower = only near-identical files. Higher = matches more crops/resizes.")
        row_dist.set_trailing(dist_box)

        self._text = ToggleSwitch()
        ocr = textextract.ocr_available()
        pdf = textextract.has_pdf_support()
        self._text.setChecked(ocr or pdf)
        self._text.setEnabled(ocr or pdf)

        ocr_badge = "Available" if ocr else "Not Installed"
        pdf_badge = "Available" if pdf else "Not Installed"
        status = f"OCR: {ocr_badge}  |  PDF Engine: {pdf_badge}"

        row_text = ListRow("file", "Read Text in Documents & Images",
                           f"Identifies bills, invoices, receipts, and sensitive documents. {status}")
        row_text.set_trailing(self._text)

        lay.addWidget(row_sim)
        lay.addWidget(row_dist)
        lay.addWidget(row_text)
        return card

    # ----- Scan Process -----
    def start_scan(self) -> None:
        roots = self._items(self._roots)
        if not roots:
            self._stage.setText("Please add at least one folder to scan.")
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
        self._stage.setText("Scanning directories…")
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
        stat_values = [
            f"{stats.files_scanned:,}",
            presenters.format_bytes(stats.bytes_scanned),
            f"{stats.duplicate_groups:,}",
            presenters.format_bytes(stats.reclaimable_bytes),
        ]
        for card, val in zip(self._stat_cards, stat_values):
            card.set_value(val)
        self._stage.setText(presenters.done_text(stats))
        self.result_ready.emit(result)

    def _on_failed(self, msg: str) -> None:
        self._reset()
        self._stage.setText(f"Scan failed: {msg}")
