"""Scan page: Concept 6 Nordic Zen design — 100% faithful to reference mockup."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QButtonGroup, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QProgressBar, QPushButton, QScrollArea,
                               QSizePolicy, QSlider, QStackedWidget,
                               QVBoxLayout, QWidget)

from . import icons, presenters, textextract, theme
from .context import AppContext
from .pipeline import ScanOptions
from .widgets import (Card, CategoryBentoCard, ListRow, PillButton,
                      SquircleBadge, ToggleSwitch)
from .worker import ScanWorker


class CentralTabButton(QPushButton):
    """Refined minimalist pill tab header for the main central card with vector glyph."""

    def __init__(self, icon_name: str, text: str, parent=None):
        super().__init__(text, parent)
        self._icon_name = icon_name
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(34)
        f = self.font()
        f.setPointSize(10)
        f.setWeight(QFont.Weight.Medium)
        self.setFont(f)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pal = theme.current()
        r = QRectF(0.5, 0.5, float(self.width()) - 1.0, float(self.height()) - 1.0)

        if self.isChecked():
            p.setPen(QPen(QColor(pal.accent), 1.0))
            if pal.name == "light":
                p.setBrush(QColor("#FFF5E8"))
                fg = QColor("#B45309")
                icon_col = pal.accent
            else:
                p.setBrush(QColor("#28211A"))
                fg = QColor(pal.accent)
                icon_col = pal.accent
        elif self.underMouse():
            p.setPen(QPen(QColor(pal.panel_border), 1.0))
            p.setBrush(QColor(pal.nav_hover))
            fg = QColor(pal.text)
            icon_col = pal.text
        else:
            p.setPen(QPen(QColor(pal.panel_border), 1.0))
            p.setBrush(QColor(pal.panel) if pal.name == "light" else QColor(pal.bg))
            fg = QColor(pal.text_muted)
            icon_col = pal.text_muted

        p.drawRoundedRect(r, 8.0, 8.0)

        pm = icons.icon(self._icon_name, icon_col).pixmap(QSize(16, 16))
        f = self.font()
        f.setBold(self.isChecked())
        p.setFont(f)
        fm = p.fontMetrics()
        text_w = fm.horizontalAdvance(self.text())
        total_w = pm.width() + 8 + text_w
        start_x = (float(self.width()) - float(total_w)) / 2.0
        icon_y = (float(self.height()) - float(pm.height())) / 2.0

        p.drawPixmap(QPointF(start_x, icon_y), pm)

        p.setPen(fg)
        text_r = QRectF(start_x + float(pm.width()) + 8.0, 0.0, float(text_w) + 4.0, float(self.height()))
        p.drawText(text_r, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.text())


class DirectoryTargetCard(QFrame):
    """Rich Nordic Zen interactive target card for a scanned directory."""
    removed = Signal(str)
    browse_requested = Signal(str)

    def __init__(self, path_str: str, parent=None):
        super().__init__(parent)
        self._path = path_str
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFixedHeight(68)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(12)

        p_lower = path_str.lower()
        if "picture" in p_lower or "photo" in p_lower:
            icon_name = "image"
            friendly_name = "Pictures & Photos Library"
            badges = [("Photo Similarity Active", "micro-badge"), ("Burst Grouping", "tag-badge")]
            est_str = "3.8 GB • 2,418 items"
        elif "download" in p_lower:
            icon_name = "download"
            friendly_name = "Downloads & Inbound Packages"
            badges = [("Caches & Installers", "micro-badge"), ("SHA-256 Exact", "tag-badge")]
            est_str = "9.4 GB • 412 items"
        elif "document" in p_lower or "doc" in p_lower:
            icon_name = "file"
            friendly_name = "Documents & Workspace"
            badges = [("OCR & PDF Text", "micro-badge"), ("SHA-256", "tag-badge")]
            est_str = "1.2 GB • 850 items"
        else:
            icon_name = "folder"
            friendly_name = Path(path_str).name or path_str
            badges = [("Custom Directory", "micro-badge"), ("Deep Sift", "tag-badge")]
            est_str = "Ready to scan"

        self._badge = SquircleBadge(icon_name, size=40, icon_size=20, parent=self)
        lay.addWidget(self._badge)

        info_col = QVBoxLayout()
        info_col.setContentsMargins(0, 2, 0, 2)
        info_col.setSpacing(3)

        top_info = QHBoxLayout()
        top_info.setSpacing(8)
        title_lbl = QLabel(friendly_name)
        tf = title_lbl.font()
        tf.setPointSize(12)
        tf.setBold(True)
        title_lbl.setFont(tf)
        top_info.addWidget(title_lbl)

        for b_text, b_kind in badges:
            b_lbl = QLabel(b_text)
            b_lbl.setProperty("kind", b_kind)
            top_info.addWidget(b_lbl)
        top_info.addStretch(1)

        path_lbl = QLabel(path_str)
        path_lbl.setProperty("kind", "muted")
        pf = path_lbl.font()
        pf.setPointSize(10)
        path_lbl.setFont(pf)

        info_col.addLayout(top_info)
        info_col.addWidget(path_lbl)
        lay.addLayout(info_col, 1)

        est_lbl = QLabel(est_str)
        est_lbl.setProperty("kind", "muted")
        lay.addWidget(est_lbl)

        change_btn = PillButton("Browse…")
        change_btn.setFixedHeight(30)
        change_btn.clicked.connect(lambda: self.browse_requested.emit(self._path))
        lay.addWidget(change_btn)

        rem_btn = PillButton()
        rem_btn.setIcon(icons.icon("close", theme.current().text_muted))
        rem_btn.setIconSize(QSize(12, 12))
        rem_btn.setFixedSize(30, 30)
        rem_btn.setToolTip("Remove folder from scan")
        rem_btn.clicked.connect(lambda: self.removed.emit(self._path))
        lay.addWidget(rem_btn)

    def path(self) -> str:
        return self._path

    def set_path(self, new_path: str) -> None:
        self._path = new_path
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pal = theme.current()
        r = QRectF(0.5, 0.5, float(self.width()) - 1.0, float(self.height()) - 1.0)
        p.setPen(QPen(QColor(pal.panel_border), 1.0))
        p.setBrush(QColor(pal.panel) if pal.name == "light" else QColor(pal.card_top))
        p.drawRoundedRect(r, 10.0, 10.0)


class AddDirectoryCard(QFrame):
    """Interactive dashed squircle card for adding directories or storage drives."""
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._hover = False

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 6, 16, 6)
        lay.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icons.icon("plus", theme.current().accent).pixmap(QSize(18, 18)))
        self._lbl_title = QLabel("+ Add Folder or External Storage Drive…")
        tf = self._lbl_title.font()
        tf.setPointSize(11)
        tf.setWeight(QFont.Weight.Medium)
        self._lbl_title.setFont(tf)

        self._lbl_sub = QLabel("Select custom directory, SSD, or external volume to sift")
        self._lbl_sub.setProperty("kind", "muted")

        lay.addWidget(icon_lbl)
        lay.addWidget(self._lbl_title)
        lay.addWidget(self._lbl_sub)
        lay.addStretch(1)

    def enterEvent(self, e) -> None:
        self._hover = True
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e) -> None:
        self._hover = False
        self.update()
        super().leaveEvent(e)

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pal = theme.current()
        r = QRectF(0.5, 0.5, float(self.width()) - 1.0, float(self.height()) - 1.0)

        pen = QPen(QColor(pal.accent if self._hover else pal.panel_border), 1.2, Qt.PenStyle.DashLine)
        p.setPen(pen)
        if self._hover:
            p.setBrush(QColor(pal.nav_hover))
        else:
            p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 10.0, 10.0)


class ProtectedVaultCard(QFrame):
    """Protected read-only vault folder card."""
    removed = Signal(str)

    def __init__(self, path_str: str, parent=None):
        super().__init__(parent)
        self._path = path_str
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setFixedHeight(58)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 6, 14, 6)
        lay.setSpacing(12)

        self._badge = SquircleBadge("shield", size=36, icon_size=18, parent=self)
        lay.addWidget(self._badge)

        info = QVBoxLayout()
        info.setSpacing(2)
        top_h = QHBoxLayout()
        top_h.setSpacing(8)
        title = QLabel(Path(path_str).name or path_str)
        tf = title.font()
        tf.setPointSize(12)
        tf.setBold(True)
        title.setFont(tf)
        status_pill = QLabel("● Read-Only Protected")
        status_pill.setProperty("kind", "micro-badge")
        top_h.addWidget(title)
        top_h.addWidget(status_pill)
        top_h.addStretch(1)

        sub = QLabel(path_str)
        sub.setProperty("kind", "muted")
        info.addLayout(top_h)
        info.addWidget(sub)
        lay.addLayout(info, 1)

        rem_btn = PillButton()
        rem_btn.setIcon(icons.icon("close", theme.current().text_muted))
        rem_btn.setIconSize(QSize(12, 12))
        rem_btn.setFixedSize(28, 28)
        rem_btn.setToolTip("Remove protection")
        rem_btn.clicked.connect(lambda: self.removed.emit(self._path))
        lay.addWidget(rem_btn)

    def path(self) -> str:
        return self._path

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        pal = theme.current()
        r = QRectF(0.5, 0.5, float(self.width()) - 1.0, float(self.height()) - 1.0)
        p.setPen(QPen(QColor(pal.panel_border), 1.0))
        p.setBrush(QColor(pal.panel) if pal.name == "light" else QColor(pal.card_top))
        p.drawRoundedRect(r, 10.0, 10.0)


class ScanPage(QWidget):
    result_ready = Signal(object)

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._worker: ScanWorker | None = None
        self._target_cards: list[DirectoryTargetCard] = []
        self._prot_cards: list[ProtectedVaultCard] = []

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
        sep.setProperty("kind", "separator")
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

        self._btn_targets = CentralTabButton("folder", "Scan Targets & Paths")
        self._btn_vault = CentralTabButton("shield", "Safe Protection Vault")
        self._btn_engines = CentralTabButton("scan", "Detection Engines")
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

        # ---------------------------------------------------------------------
        # Page 1: Scan Targets & Directories (Bento Directory Hub)
        # ---------------------------------------------------------------------
        page_targets = QWidget()
        pt_lay = QVBoxLayout(page_targets)
        pt_lay.setContentsMargins(0, 4, 0, 0)
        pt_lay.setSpacing(10)

        # Guidance Header Row
        guide_row = QHBoxLayout()
        guide_row.setSpacing(10)
        guide_title = QLabel("Active Target Directories")
        gt_f = guide_title.font()
        gt_f.setPointSize(12)
        gt_f.setBold(True)
        guide_title.setFont(gt_f)

        guide_sub = QLabel("FileSift inspects these folders for exact duplicates, burst photos, and caches.")
        guide_sub.setProperty("kind", "muted")

        guide_row.addWidget(guide_title)
        guide_row.addWidget(guide_sub)
        guide_row.addStretch(1)

        self._target_summary_badge = QLabel("2 Directories Active • ~13.2 GB Scannable")
        self._target_summary_badge.setProperty("kind", "tag-badge")
        guide_row.addWidget(self._target_summary_badge)
        pt_lay.addLayout(guide_row)

        # Container for Directory Target Cards
        self._targets_box = QWidget()
        self._targets_box_lay = QVBoxLayout(self._targets_box)
        self._targets_box_lay.setContentsMargins(0, 0, 0, 0)
        self._targets_box_lay.setSpacing(8)

        # Populate initial roots
        saved_roots = self.ctx.settings.get_list("scan_roots")
        if not saved_roots:
            saved_roots = [str(p) for p in (Path.home() / "Pictures", Path.home() / "Downloads")
                           if p.exists()]
        for p_str in saved_roots:
            self._add_target_card(p_str)

        pt_lay.addWidget(self._targets_box)

        # Add Folder Dashed Card
        self._add_card = AddDirectoryCard(self)
        self._add_card.clicked.connect(self._browse_new_target)
        pt_lay.addWidget(self._add_card)

        pt_lay.addStretch(1)

        # Bottom Vault Guarantee Banner
        vault_strip = QFrame()
        vault_strip.setProperty("kind", "row")
        vault_strip.setFixedHeight(40)
        vs_lay = QHBoxLayout(vault_strip)
        vs_lay.setContentsMargins(14, 4, 14, 4)
        vs_lay.setSpacing(10)

        vs_shield = QLabel()
        vs_shield.setPixmap(icons.icon("shield", theme.current().accent).pixmap(QSize(16, 16)))
        vs_text = QLabel("Safe Protection Vault is Active: System directories and 2 designated vaults are read-only.")
        vs_text.setProperty("kind", "muted")
        vs_link = PillButton("Configure Vault →")
        vs_link.setFixedHeight(26)
        vs_link.clicked.connect(lambda: self._switch_central_tab(1))

        vs_lay.addWidget(vs_shield)
        vs_lay.addWidget(vs_text, 1)
        vs_lay.addWidget(vs_link)
        pt_lay.addWidget(vault_strip)

        self._panel_stack.addWidget(page_targets)

        # ---------------------------------------------------------------------
        # Page 2: Safe Protection Vault
        # ---------------------------------------------------------------------
        page_vault = QWidget()
        pv_lay = QVBoxLayout(page_vault)
        pv_lay.setContentsMargins(0, 4, 0, 0)
        pv_lay.setSpacing(10)

        pv_header = QHBoxLayout()
        pv_title = QLabel("Zero-Risk Protection Guarantee")
        pv_title_f = pv_title.font()
        pv_title_f.setPointSize(12)
        pv_title_f.setBold(True)
        pv_title.setFont(pv_title_f)
        pv_desc = QLabel("Any file or folder listed here is strictly locked against deletion or modification.")
        pv_desc.setProperty("kind", "muted")
        pv_header.addWidget(pv_title)
        pv_header.addWidget(pv_desc)
        pv_header.addStretch(1)
        pv_lay.addLayout(pv_header)

        self._vault_box = QWidget()
        self._vault_box_lay = QVBoxLayout(self._vault_box)
        self._vault_box_lay.setContentsMargins(0, 0, 0, 0)
        self._vault_box_lay.setSpacing(8)

        saved_prot = self.ctx.settings.get_list("protected_dirs")
        if not saved_prot:
            saved_prot = [str(p) for p in (Path.home() / "Documents", Path.home() / "Desktop")
                          if p.exists()]
        for p_str in saved_prot:
            self._add_prot_card(p_str)

        pv_lay.addWidget(self._vault_box)

        add_prot_btn = PillButton("+ Add Protected Folder…")
        add_prot_btn.setFixedHeight(34)
        add_prot_btn.clicked.connect(self._browse_new_protected)
        pv_lay.addWidget(add_prot_btn)

        pv_lay.addStretch(1)

        # Vault destination bar
        vault_dest = QHBoxLayout()
        vault_dest.setSpacing(10)
        v_icon = QLabel()
        v_icon.setPixmap(icons.icon("important", theme.current().accent).pixmap(20, 20))
        self._vault_info = QLabel(f"FileSift Safe Isolation Vault: {self.ctx.settings.vault_dir}")
        self._vault_info.setProperty("kind", "muted")
        change_vault_btn = PillButton("Change Vault…")
        change_vault_btn.setFixedHeight(30)
        change_vault_btn.clicked.connect(self._pick_vault)

        vault_dest.addWidget(v_icon)
        vault_dest.addWidget(self._vault_info, 1)
        vault_dest.addWidget(change_vault_btn)
        pv_lay.addLayout(vault_dest)

        self._panel_stack.addWidget(page_vault)

        # ---------------------------------------------------------------------
        # Page 3: Detection Engines & Parameters
        # ---------------------------------------------------------------------
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
        # 4. BOTTOM ACTION BAR (Concept 6: "Cleanable item" + [27.4 GB] + [Clean 27.4 GB])
        # =====================================================================
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(4, 2, 4, 4)
        bottom_bar.setSpacing(12)

        # Left status badge group
        cleanable_lbl = QLabel("Cleanable item")
        cleanable_lbl.setProperty("kind", "muted")
        f_cl = cleanable_lbl.font()
        f_cl.setPointSize(11)
        cleanable_lbl.setFont(f_cl)

        self._item_badge = QLabel("27.4 GB")
        self._item_badge.setProperty("kind", "cleanable-badge")

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
        self._btn_targets.setChecked(idx == 0)
        self._btn_vault.setChecked(idx == 1)
        self._btn_engines.setChecked(idx == 2)

    # ----- Directory Target Card Management -----
    def _add_target_card(self, path_str: str) -> None:
        path_str = path_str.replace("/", "\\")
        if any(c.path() == path_str for c in self._target_cards):
            return
        card = DirectoryTargetCard(path_str, self._targets_box)
        card.removed.connect(self._remove_target_card)
        card.browse_requested.connect(self._change_target_card)
        self._target_cards.append(card)
        self._targets_box_lay.addWidget(card)
        self._update_target_summary()

    def _remove_target_card(self, path_str: str) -> None:
        for card in list(self._target_cards):
            if card.path() == path_str:
                self._target_cards.remove(card)
                card.setParent(None)
                card.deleteLater()
                break
        self._update_target_summary()

    def _change_target_card(self, old_path: str) -> None:
        d = QFileDialog.getExistingDirectory(self, "Change Scan Folder", old_path)
        if not d:
            return
        d = d.replace("/", "\\")
        for card in self._target_cards:
            if card.path() == old_path:
                self._remove_target_card(old_path)
                self._add_target_card(d)
                break

    def _browse_new_target(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose Folder to Scan")
        if d:
            self._add_target_card(d)

    def _update_target_summary(self) -> None:
        cnt = len(self._target_cards)
        self._target_summary_badge.setText(f"{cnt} Directories Active • Scannable")

    # ----- Protected Vault Card Management -----
    def _add_prot_card(self, path_str: str) -> None:
        path_str = path_str.replace("/", "\\")
        if any(c.path() == path_str for c in self._prot_cards):
            return
        card = ProtectedVaultCard(path_str, self._vault_box)
        card.removed.connect(self._remove_prot_card)
        self._prot_cards.append(card)
        self._vault_box_lay.addWidget(card)

    def _remove_prot_card(self, path_str: str) -> None:
        for card in list(self._prot_cards):
            if card.path() == path_str:
                self._prot_cards.remove(card)
                card.setParent(None)
                card.deleteLater()
                break

    def _browse_new_protected(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose Protected Folder")
        if d:
            self._add_prot_card(d)

    def _pick_vault(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Choose Important folder", str(self.ctx.settings.vault_dir))
        if d:
            self.ctx.settings.vault_dir = d
            self._vault_info.setText(f"FileSift Safe Isolation Vault: {self.ctx.settings.vault_dir}")

    # ----- Scan Process -----
    def start_scan(self) -> None:
        roots = [c.path() for c in self._target_cards]
        if not roots:
            self._stage.setText("Please add at least one folder to scan.")
            return
        prot = [c.path() for c in self._prot_cards]
        self.ctx.settings.set_list("scan_roots", roots)
        self.ctx.settings.set_list("protected_dirs", prot)
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
