"""Scan page: Concept 6 Nordic Zen design — 100% faithful to reference mockup."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QButtonGroup, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QListWidget, QListWidgetItem,
                               QProgressBar, QPushButton, QSlider,
                               QStackedWidget, QVBoxLayout, QWidget)

from . import icons, presenters, textextract, theme
from .context import AppContext
from .pipeline import ScanOptions
from .widgets import Card, CategoryBentoCard, ListRow, PillButton, ToggleSwitch
from .worker import ScanWorker


class CentralTabButton(QPushButton):
    """Refined minimalist pill tab header for the main central card."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(32)
        f = self.font()
        f.setPointSize(10)
        f.setWeight(QFont.Weight.Medium)
        self.setFont(f)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        r = self.rect().adjusted(1, 1, -1, -1)

        if self.isChecked():
            p.setPen(QPen(QColor(pal.accent), 1))
            p.setBrush(QColor(pal.card_top))
            fg = QColor(pal.text)
        elif self.underMouse():
            p.setPen(QPen(QColor(pal.panel_border), 1))
            p.setBrush(QColor(pal.nav_hover))
            fg = QColor(pal.text)
        else:
            p.setPen(QPen(QColor(pal.panel_border), 1))
            p.setBrush(QColor(pal.bg))
            fg = QColor(pal.text_muted)

        p.drawRoundedRect(r, 7, 7)
        p.setPen(fg)
        p.setFont(self.font())
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())


class ScanPage(QWidget):
    result_ready = Signal(object)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._worker: ScanWorker | None = None
        self._stat_cards = []

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # =====================================================================
        # 1. HEADER (Concept 6: "File Cards" + Subtitle + Action CTA)
        # =====================================================================
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 4)
        top_bar.setSpacing(14)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        page_title = QLabel("File Cards")
        ptf = page_title.font()
        ptf.setPointSize(21)
        ptf.setWeight(QFont.Weight.DemiBold)
        page_title.setFont(ptf)

        page_desc = QLabel("Premium storage cleaner for FileSift.")
        page_desc.setProperty("kind", "muted")
        page_desc_f = page_desc.font()
        page_desc_f.setPointSize(11)
        page_desc.setFont(page_desc_f)

        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        top_bar.addLayout(title_box, 1)

        # Header Right Actions
        hdr_actions = QHBoxLayout()
        hdr_actions.setSpacing(10)

        self._hdr_more = PillButton("…")
        self._hdr_more.setFixedSize(38, 36)
        self._hdr_more.setCursor(Qt.CursorShape.PointingHandCursor)

        self._start_top = PillButton("Clean 27.4 GB", primary=True)
        self._start_top.setFixedHeight(36)
        theme.add_glow(self._start_top)
        self._start_top.clicked.connect(self.start_scan)

        hdr_actions.addWidget(self._hdr_more)
        hdr_actions.addWidget(self._start_top)
        top_bar.addLayout(hdr_actions)
        root.addLayout(top_bar)

        # Whisper-thin separator line
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #25242C; border: none;")
        root.addWidget(sep)

        # =====================================================================
        # 2. TOP 3 BENTO CARDS (Xcode Caches | Chrome Cache | Orphaned Installers)
        # =====================================================================
        bento_row = QHBoxLayout()
        bento_row.setSpacing(14)

        self._bento_caches = CategoryBentoCard(
            "xcode",
            "Xcode Caches",
            "14.2 GB",
            checked=True,
            parent=self,
        )
        self._bento_photos = CategoryBentoCard(
            "browser",
            "Chrome Cache",
            "3.8 GB",
            checked=True,
            parent=self,
        )
        self._bento_installers = CategoryBentoCard(
            "download",
            "Orphaned Installers",
            "9.4 GB",
            checked=True,
            parent=self,
        )

        bento_row.addWidget(self._bento_caches)
        bento_row.addWidget(self._bento_photos)
        bento_row.addWidget(self._bento_installers)
        root.addLayout(bento_row)

        # =====================================================================
        # 3. LARGE CENTRAL BENTO PANEL (Concept 6 Hero Frame)
        # =====================================================================
        self._main_panel = Card("panel", self)
        panel_lay = QVBoxLayout(self._main_panel)
        panel_lay.setContentsMargins(18, 16, 18, 16)
        panel_lay.setSpacing(14)

        # Top tab selector inside the panel
        tab_bar = QHBoxLayout()
        tab_bar.setSpacing(8)

        self._btn_targets = CentralTabButton("📁 Scan Targets & Paths")
        self._btn_vault = CentralTabButton("🛡 Safe Protection Vault")
        self._btn_engines = CentralTabButton("⚡ Detection Engines")
        self._btn_targets.setChecked(True)

        self._tab_group = QButtonGroup(self)
        self._tab_group.addButton(self._btn_targets, 0)
        self._tab_group.addButton(self._btn_vault, 1)
        self._tab_group.addButton(self._btn_engines, 2)
        self._tab_group.idClicked.connect(self._switch_central_tab)

        tab_bar.addWidget(self._btn_targets)
        tab_bar.addWidget(self._btn_vault)
        tab_bar.addWidget(self._btn_engines)
        tab_bar.addStretch(1)
        panel_lay.addLayout(tab_bar)

        # Stacked pages for the central panel
        self._panel_stack = QStackedWidget(self._main_panel)
        panel_lay.addWidget(self._panel_stack, 1)

        # Page 1: Scan Targets & Directories
        page_targets = QWidget()
        pt_lay = QVBoxLayout(page_targets)
        pt_lay.setContentsMargins(0, 4, 0, 0)
        pt_lay.setSpacing(10)

        self._roots = QListWidget()
        self._roots.setAlternatingRowColors(False)
        self._roots.setStyleSheet("background: transparent; border: none; font-size: 13px; color: #E4E4E7;")
        pal = theme.current()
        saved_roots = self.ctx.settings.get_list("scan_roots")
        if not saved_roots:
            saved_roots = [str(p) for p in (Path.home() / "Pictures", Path.home() / "Downloads")
                           if p.exists()]
        for s in saved_roots:
            item = QListWidgetItem(icons.icon("folder", pal.accent), s)
            self._roots.addItem(item)

        pt_actions = QHBoxLayout()
        pt_actions.setSpacing(10)
        add_folder_btn = PillButton("+ Add Folder…")
        add_folder_btn.setFixedHeight(32)
        rem_folder_btn = PillButton("Remove")
        rem_folder_btn.setFixedHeight(32)
        add_folder_btn.clicked.connect(lambda: self._add_folder(self._roots))
        rem_folder_btn.clicked.connect(lambda: self._remove_folder(self._roots))

        pt_actions.addWidget(add_folder_btn)
        pt_actions.addWidget(rem_folder_btn)
        pt_actions.addStretch(1)

        targets_hint = QLabel("Select local directories to analyze for duplicate files, photo burst sequences, and clutter.")
        targets_hint.setProperty("kind", "muted")

        pt_lay.addWidget(targets_hint)
        pt_lay.addWidget(self._roots, 1)
        pt_lay.addLayout(pt_actions)
        self._panel_stack.addWidget(page_targets)

        # Page 2: Safe Protection Vault
        page_vault = QWidget()
        pv_lay = QVBoxLayout(page_vault)
        pv_lay.setContentsMargins(0, 4, 0, 0)
        pv_lay.setSpacing(10)

        vault_hint = QLabel("Files located in protected directories will NEVER be deleted. Preserved documents route to Vault.")
        vault_hint.setProperty("kind", "muted")

        self._prot = QListWidget()
        self._prot.setAlternatingRowColors(False)
        self._prot.setStyleSheet("background: transparent; border: none; font-size: 13px; color: #E4E4E7;")
        saved_prot = self.ctx.settings.get_list("protected_dirs")
        for s in saved_prot:
            item = QListWidgetItem(icons.icon("shield", pal.accent), s)
            self._prot.addItem(item)

        prot_actions = QHBoxLayout()
        prot_actions.setSpacing(10)
        add_prot_btn = PillButton("+ Add Protected…")
        add_prot_btn.setFixedHeight(32)
        rem_prot_btn = PillButton("Remove")
        rem_prot_btn.setFixedHeight(32)
        add_prot_btn.clicked.connect(lambda: self._add_folder(self._prot))
        rem_prot_btn.clicked.connect(lambda: self._remove_folder(self._prot))

        prot_actions.addWidget(add_prot_btn)
        prot_actions.addWidget(rem_prot_btn)
        prot_actions.addStretch(1)

        # Vault destination bar
        vault_dest = QHBoxLayout()
        vault_dest.setSpacing(10)
        v_icon = QLabel()
        v_icon.setPixmap(icons.icon("important", "#E0A96D").pixmap(20, 20))
        self._vault_info = QLabel(f"FileSift Vault Destination: {self.ctx.settings.vault_dir}")
        self._vault_info.setStyleSheet("color: #E4E4E7; font-size: 12px;")
        change_vault_btn = PillButton("Change Vault…")
        change_vault_btn.setFixedHeight(30)
        change_vault_btn.clicked.connect(self._pick_vault)

        vault_dest.addWidget(v_icon)
        vault_dest.addWidget(self._vault_info, 1)
        vault_dest.addWidget(change_vault_btn)

        pv_lay.addWidget(vault_hint)
        pv_lay.addWidget(self._prot, 1)
        pv_lay.addLayout(prot_actions)
        pv_lay.addLayout(vault_dest)
        self._panel_stack.addWidget(page_vault)

        # Page 3: Detection Engines & Parameters
        page_engines = QWidget()
        pe_lay = QVBoxLayout(page_engines)
        pe_lay.setContentsMargins(0, 4, 0, 0)
        pe_lay.setSpacing(14)

        self._similar = ToggleSwitch()
        self._similar.setChecked(True)
        row_sim = ListRow("image", "Find Similar Photos & Burst Shots",
                          "Detects resized, recompressed, or slight variations of the same photograph using perceptual hashing.")
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

        pe_lay.addWidget(row_sim)
        pe_lay.addWidget(row_dist)
        pe_lay.addWidget(row_text)
        pe_lay.addStretch(1)
        self._panel_stack.addWidget(page_engines)

        root.addWidget(self._main_panel, 1)

        # =====================================================================
        # 4. BOTTOM ACTION BAR (Concept 6: "Cleanable item" + [0x] + [Clean 27.4 GB])
        # =====================================================================
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 2, 4, 4)
        bottom_bar.setSpacing(12)

        # Left status badge group
        cleanable_lbl = QLabel("Cleanable item")
        cleanable_lbl.setStyleSheet("color: #8E8E9A; font-size: 13px;")

        self._item_badge = QLabel("27.4 GB")
        self._item_badge.setStyleSheet(
            "color: #E0A96D; background: #222129; border: 1px solid #33313E; "
            "border-radius: 10px; padding: 2px 10px; font-size: 11px; font-weight: bold;"
        )

        self._bottom_more = PillButton("…")
        self._bottom_more.setFixedSize(36, 32)
        self._bottom_more.setCursor(Qt.CursorShape.PointingHandCursor)

        self._stage = QLabel("Ready to sift — Choose targets and start scan.")
        self._stage.setProperty("kind", "muted")

        self._bar = QProgressBar()
        self._bar.setRange(0, 1)
        self._bar.setValue(0)
        self._bar.setFixedHeight(6)
        self._bar.setVisible(False)

        bottom_bar.addWidget(cleanable_lbl)
        bottom_bar.addWidget(self._item_badge)
        bottom_bar.addWidget(self._bottom_more)
        bottom_bar.addWidget(self._stage)
        bottom_bar.addWidget(self._bar, 1)
        bottom_bar.addStretch(1)

        self._cancel = PillButton("Cancel")
        self._cancel.setFixedHeight(38)
        self._cancel.setEnabled(False)
        self._cancel.setVisible(False)
        self._cancel.clicked.connect(self._cancel_scan)

        self._start = PillButton("Clean 27.4 GB", primary=True)
        self._start.setFixedHeight(38)
        theme.add_glow(self._start)
        self._start.clicked.connect(self.start_scan)

        bottom_bar.addWidget(self._cancel)
        bottom_bar.addWidget(self._start)
        root.addLayout(bottom_bar)

    def _switch_central_tab(self, idx: int) -> None:
        self._panel_stack.setCurrentIndex(idx)

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
            self._vault_info.setText(f"FileSift Vault Destination: {self.ctx.settings.vault_dir}")

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
        self._start_top.setEnabled(False)
        self._cancel.setEnabled(True)
        self._bar.setVisible(True)
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
        self._start_top.setEnabled(True)
        self._cancel.setEnabled(False)
        self._cancel.setVisible(False)
        self._bar.setVisible(False)
        self._bar.setRange(0, 1)
        self._bar.setValue(0)

    def _on_done(self, result) -> None:
        self._reset()
        stats = presenters.scan_stats(result)
        reclaim_str = presenters.format_bytes(stats.reclaimable_bytes)
        self._item_badge.setText(reclaim_str)
        self._start.setText(f"Clean {reclaim_str}")
        self._start_top.setText(f"Clean {reclaim_str}")
        self._stage.setText(presenters.done_text(stats))
        self.result_ready.emit(result)

    def _on_failed(self, msg: str) -> None:
        self._reset()
        self._stage.setText(f"Scan failed: {msg}")
