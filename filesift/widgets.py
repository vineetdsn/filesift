"""Reusable Nordic Zen widgets: architectural cards, champagne gold buttons, Swiss sidebar — UI/UX Pro Max."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QIcon, QImageReader, QLinearGradient,
                           QPainter, QPainterPath, QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QFrame, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QSizePolicy,
                               QToolButton, QVBoxLayout, QWidget)

from . import icons, presenters, theme
from .models import FileInfo


def _load_thumb(path: str, box: int = 360) -> QPixmap:
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and size.width() > 0:
        size.scale(QSize(box, box), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)
    img = reader.read()
    return QPixmap.fromImage(img) if not img.isNull() else QPixmap()


class Card(QFrame):
    """Architectural rounded panel with whisper-thin border and matte depth."""

    def __init__(self, kind: str = "panel", parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setProperty("kind", kind)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        r = self.rect().adjusted(1, 1, -1, -1)
        p.setPen(QPen(QColor(pal.panel_border), 1))
        if self._kind == "panel":
            p.setBrush(QColor(pal.panel))
        else:  # content / elevated
            grad = QLinearGradient(0, 0, 0, max(1, r.height()))
            grad.setColorAt(0.0, QColor(pal.card_top))
            grad.setColorAt(1.0, QColor(pal.card_bottom))
            p.setBrush(grad)
        p.drawRoundedRect(r, theme.RADIUS_CARD, theme.RADIUS_CARD)


class StatCard(Card):
    """Minimalist Scandinavian bento metric card with brushed champagne gold numbers."""

    def __init__(self, label: str, parent=None):
        super().__init__("content", parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(4)

        self._cap = QLabel(label.upper())
        self._cap.setProperty("kind", "muted")
        cap_f = self._cap.font()
        cap_f.setPointSize(9)
        cap_f.setBold(True)
        cap_f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        self._cap.setFont(cap_f)

        self._value = QLabel(presenters.EM_DASH)
        f = self._value.font()
        f.setPointSize(theme.FONT_STAT_PT)
        f.setWeight(QFont.Weight.DemiBold)
        self._value.setFont(f)
        self._value.setProperty("kind", "card-text")

        # Color highlight: soft brushed champagne gold & warm copper
        if "reclaim" in label.lower() or "safe" in label.lower():
            self._value.setStyleSheet("color: #E2B170; font-weight: 600;")
        elif "duplicate" in label.lower():
            self._value.setStyleSheet("color: #D97706; font-weight: 600;")
        else:
            self._value.setStyleSheet("color: #F0EFEA; font-weight: 600;")

        lay.addWidget(self._cap)
        lay.addWidget(self._value)

    def set_value(self, text: str) -> None:
        self._value.setText(text)


class PillButton(QPushButton):
    """Brushed Champagne Gold & architectural matte button with subtle satin depth."""

    def __init__(self, text: str = "", primary: bool = False, danger: bool = False, parent=None):
        super().__init__(text, parent)
        self._primary = primary
        self._danger = danger
        self.setProperty("primary", primary)
        self.setFixedHeight(theme.PILL_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        f = self.font()
        f.setBold(primary or danger)
        self.setFont(f)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        r = self.rect().adjusted(1, 1, -1, -1)
        rad = 12 if self._primary or self._danger else theme.RADIUS_CONTROL

        if self._primary:
            grad = QLinearGradient(0, 0, r.width(), 0)
            if self.underMouse() and self.isEnabled():
                grad.setColorAt(0.0, QColor("#EAC188"))
                grad.setColorAt(1.0, QColor("#D8A665"))
            else:
                grad.setColorAt(0.0, QColor(pal.accent))
                grad.setColorAt(1.0, QColor(pal.copper))
            p.setBrush(grad)
            p.setPen(QPen(QColor(pal.accent), 1))
            fg = QColor(pal.on_accent)
        elif self._danger:
            bg = QColor(pal.danger)
            if self.underMouse() and self.isEnabled():
                bg = bg.lighter(110)
            p.setBrush(bg)
            p.setPen(QPen(QColor(pal.danger), 1))
            fg = QColor("#FFFFFF")
        else:
            bg = QColor(pal.panel)
            border = QColor(pal.panel_border)
            if self.underMouse() and self.isEnabled():
                bg = QColor(pal.nav_hover)
                border = QColor(pal.accent)
            p.setBrush(bg)
            p.setPen(QPen(border, 1))
            fg = QColor(pal.text)

        if not self.isEnabled():
            p.setBrush(QColor(pal.panel).lighter(105))
            p.setPen(QPen(QColor(pal.panel_border), 1))
            fg = QColor(pal.text_muted)
        elif self.isDown() or self.isChecked():
            p.setBrush(QColor(pal.panel_border))

        p.drawRoundedRect(r, rad, rad)
        p.setPen(fg)
        p.setFont(self.font())
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())


class ToggleSwitch(QAbstractButton):
    """Accessible toggle switch with warm copper/champagne gold track."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(48, 26)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggled.connect(self.update)

    def hitButton(self, pos):  # noqa: N802
        return self.contentsRect().contains(pos)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        on = self.isChecked()

        track = QColor(pal.accent) if on else QColor(pal.input_border)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track)
        p.drawRoundedRect(0, 0, 48, 26, 13, 13)

        kx = 25 if on else 3
        knob_color = QColor(pal.on_accent) if on else QColor("#FFFFFF")
        p.setBrush(knob_color)
        p.drawEllipse(kx, 3, 20, 20)


class ListRow(QFrame):
    """Clean architectural option row with whisper-thin border and generous spacing."""

    def __init__(self, icon_name: str | None = None, title: str = "",
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("kind", "row")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setMinimumHeight(62)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(14)

        self._icon = QLabel()
        self._icon.setFixedSize(26, 26)
        if icon_name:
            self._icon.setPixmap(icons.icon(icon_name, "#E2B170").pixmap(QSize(24, 24)))

        self._title = QLabel(title)
        f = self._title.font()
        f.setBold(True)
        f.setPointSize(13)
        self._title.setFont(f)

        self._sub = QLabel(subtitle)
        self._sub.setProperty("kind", "muted")
        self._sub.setWordWrap(True)

        col = QVBoxLayout()
        col.setContentsMargins(0, 2, 0, 2)
        col.setSpacing(3)
        col.addWidget(self._title)
        col.addWidget(self._sub)

        lay.addWidget(self._icon)
        lay.addLayout(col, 1)
        self._trail: QWidget | None = None

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        p.setPen(QPen(QColor(pal.panel_border), 1))
        p.setBrush(QColor(pal.panel))
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1),
                          theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

    def set_title(self, t: str) -> None:
        self._title.setText(t)

    def set_subtitle(self, t: str) -> None:
        self._sub.setText(t)

    def set_trailing(self, w: QWidget) -> None:
        if self._trail is not None:
            self._trail.setParent(None)
        self._trail = w
        self.layout().addWidget(w)

    def trailing(self) -> QWidget | None:
        return self._trail


class NavButton(QToolButton):
    """Nordic Zen squircle navigation item with warm champagne indicator and micro-badge."""
    requested = Signal(str)

    def __init__(self, page_id: str, icon_name: str, label: str = "", parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self._label = label or page_id.capitalize()
        self._icon_name = icon_name
        self._badge: int | None = None
        self._active = False
        self.setText(self._label)
        self.setIcon(icons.icon(icon_name))
        self.setIconSize(QSize(20, 20))
        self.setFixedSize(190, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(lambda: self.requested.emit(self._page_id))

    def set_active(self, on: bool) -> None:
        self._active = on
        self.update()

    def set_badge(self, n: int | None) -> None:
        self._badge = n
        self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        w = self.width()
        h = self.height()
        btn_rect = self.rect().adjusted(4, 2, -4, -2)

        if self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.nav_hover))
            p.drawRoundedRect(btn_rect, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)
            # Left champagne gold indicator pill
            p.setBrush(QColor(pal.accent))
            p.drawRoundedRect(QRect(4, 9, 3, h - 18), 1.5, 1.5)
        elif self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.nav_hover))
            p.drawRoundedRect(btn_rect, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        # Icon
        icon_color = pal.accent if self._active else pal.text_muted
        pm = icons.icon(self._icon_name, icon_color).pixmap(QSize(20, 20))
        p.drawPixmap(14, (h - pm.height()) // 2, pm)

        # Label Text
        f = self.font()
        f.setPointSize(11)
        f.setBold(self._active)
        p.setFont(f)
        text_color = QColor(pal.text) if self._active else QColor(pal.text_muted)
        p.setPen(text_color)
        text_rect = QRect(44, 0, w - 50, h)
        p.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self._label)

        # Champagne micro-badge
        text = presenters.format_badge(self._badge) if self._badge else None
        if text:
            bf = self.font()
            bf.setPointSize(8)
            bf.setBold(True)
            p.setFont(bf)
            fm = p.fontMetrics()
            tw = max(fm.horizontalAdvance(text), 14)
            bw = tw + 10
            bh = 18
            bx = w - bw - 10
            by = (h - bh) // 2

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.accent))
            p.drawRoundedRect(QRect(bx, by, bw, bh), 9, 9)

            p.setPen(QColor(pal.on_accent))
            p.drawText(QRect(bx, by, bw, bh), Qt.AlignmentFlag.AlignCenter, text)


class ThemeSegmentedPill(QWidget):
    """Dual-segment pill switcher: [ ☀️ Light | 🌙 Dark ] with active segment highlight."""
    theme_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(190, 36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._mode = theme.current().name

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self.update()

    def mousePressEvent(self, e) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            new_mode = "light" if e.pos().x() < self.width() / 2 else "dark"
            if new_mode != self._mode:
                self._mode = new_mode
                self.theme_requested.emit(self._mode)
                self.update()

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        w = float(self.width())
        h = float(self.height())
        r = h / 2.0

        # Outer rounded pill track
        p.setPen(QPen(QColor(pal.panel_border), 1))
        p.setBrush(QColor(pal.bg))
        p.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), r, r)

        seg_w = (w - 6) / 2.0
        seg_h = h - 6
        active_x = 3.0 if self._mode == "light" else (3.0 + seg_w)

        # Active segment pill with champagne border
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(pal.card_top))
        p.drawRoundedRect(QRectF(active_x, 3.0, seg_w, seg_h), seg_h / 2.0, seg_h / 2.0)
        p.setPen(QPen(QColor(pal.accent), 1))
        p.drawRoundedRect(QRectF(active_x, 3.0, seg_w, seg_h), seg_h / 2.0, seg_h / 2.0)

        f = self.font()
        f.setPointSize(9)
        f.setBold(True)
        p.setFont(f)

        # Light label
        light_col = QColor(pal.text) if self._mode == "light" else QColor(pal.text_muted)
        p.setPen(light_col)
        p.drawText(QRectF(3.0, 3.0, seg_w, seg_h), Qt.AlignmentFlag.AlignCenter, "☀️ Light")

        # Dark label
        dark_col = QColor(pal.text) if self._mode == "dark" else QColor(pal.text_muted)
        p.setPen(dark_col)
        p.drawText(QRectF(3.0 + seg_w, 3.0, seg_w, seg_h), Qt.AlignmentFlag.AlignCenter, "🌙 Dark")


class Sidebar(QFrame):
    """Full Scandinavian minimalist sidebar with brand header and theme switcher."""
    page_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(theme.SIDEBAR_W)
        self.setProperty("kind", "sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 20, 10, 16)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # App Brand Header
        brand_box = QWidget()
        brand_box.setFixedWidth(190)
        brand_lay = QHBoxLayout(brand_box)
        brand_lay.setContentsMargins(8, 0, 8, 16)
        brand_lay.setSpacing(12)
        brand_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        logo_lbl = QLabel()
        logo_lbl.setFixedSize(26, 26)
        logo_lbl.setPixmap(icons.icon("brand", "#E2B170").pixmap(QSize(24, 24)))

        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(1)
        title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        title_lbl = QLabel("FileSift")
        tf = title_lbl.font()
        tf.setPointSize(15)
        tf.setBold(True)
        title_lbl.setFont(tf)

        sub_lbl = QLabel("Storage Optimizer")
        sub_lbl.setProperty("kind", "muted")
        sf = sub_lbl.font()
        sf.setPointSize(9)
        sub_lbl.setFont(sf)

        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)

        brand_lay.addWidget(logo_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        brand_lay.addLayout(title_box)
        lay.addWidget(brand_box)

        # Section Label
        section_lbl = QLabel("TOOLS & STORAGE")
        section_lbl.setFixedWidth(180)
        section_lbl.setProperty("kind", "muted")
        sec_f = section_lbl.font()
        sec_f.setPointSize(8)
        sec_f.setBold(True)
        sec_f.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.8)
        section_lbl.setFont(sec_f)
        section_lbl.setStyleSheet("color: #71717A; padding: 4px 6px;")
        lay.addWidget(section_lbl)

        # Navigation Buttons
        self._scan = NavButton("scan", "scan", "Scan & Overview")
        self._dup = NavButton("duplicates", "duplicates", "Duplicates")
        self._clean = NavButton("cleanup", "cleanup", "Clean Up")

        for b in (self._scan, self._dup, self._clean):
            b.requested.connect(self.page_requested)
            lay.addWidget(b)

        lay.addStretch(1)

        # Dual-segment theme switcher pill [ ☀️ Light | 🌙 Dark ]
        self._theme_pill = ThemeSegmentedPill(self)
        self._theme_pill.theme_requested.connect(self._on_theme_changed)
        lay.addWidget(self._theme_pill)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        pal = theme.current()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(pal.panel))
        p.drawRect(self.rect())
        p.setPen(QPen(QColor(pal.panel_border), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

    def _on_theme_changed(self, mode: str) -> None:
        app = QApplication.instance()
        if app:
            theme.apply_theme(app, mode)
            self._theme_pill.set_mode(mode)
            for widget in app.topLevelWidgets():
                widget.update()

    def set_active(self, page_id: str) -> None:
        self._scan.set_active(page_id == "scan")
        self._dup.set_active(page_id == "duplicates")
        self._clean.set_active(page_id == "cleanup")

    def set_badges(self, dups: int, safe: int) -> None:
        self._dup.set_badge(dups)
        self._clean.set_badge(safe)


class PreviewPanel(Card):
    """Architectural file preview card with formatted details and thumbnail."""

    def __init__(self, parent=None):
        super().__init__("content", parent)
        self.setMinimumWidth(320)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        head = QLabel("FILE PREVIEW")
        head.setProperty("kind", "muted")
        hf = head.font()
        hf.setPointSize(9)
        hf.setBold(True)
        head.setFont(hf)
        lay.addWidget(head)

        self._image = QLabel("Select a file to preview")
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setMinimumHeight(260)
        pal = theme.current()
        self._image.setStyleSheet(
            f"background: {pal.bg}; color: {pal.text_muted}; border: 1px dashed {pal.panel_border}; border-radius: 12px; font-size: 13px;"
        )

        self._details = QPlainTextEdit()
        self._details.setReadOnly(True)
        self._details.setMaximumHeight(200)
        self._details.setPlaceholderText("File metadata and details will appear here...")

        lay.addWidget(self._image, 1)
        lay.addWidget(self._details)

    def show_file(self, fi: FileInfo | None) -> None:
        if fi is None:
            self._image.setPixmap(QPixmap())
            self._image.setText("Select a file to preview")
            self._details.setPlainText("")
            return
        pm = _load_thumb(fi.path, 360) if fi.is_image else QPixmap()
        if pm.isNull():
            self._image.setPixmap(QPixmap())
            self._image.setText(presenters.placeholder_label(fi))
        else:
            self._image.setPixmap(pm)
        self._details.setPlainText(presenters.preview_details(fi))


class StorageGauge(QWidget):
    """Segmented horizontal storage bar with rounded corners."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(10)
        self._ratios = [0.24, 0.14, 0.08, 0.04]  # sys, media, docs, dups

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        w = float(self.width())
        h = float(self.height())
        r = 5.0

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(pal.card_bottom))
        p.drawRoundedRect(QRectF(0, 0, w, h), r, r)

        colors = [
            QColor("#3E3E48"),
            QColor(pal.accent),
            QColor(pal.success),
            QColor(pal.danger),
        ]

        x = 0.0
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(0, 0, w, h), r, r)
        p.setClipPath(clip_path)

        for ratio, col in zip(self._ratios, colors):
            seg_w = max(4.0, w * ratio)
            p.setBrush(col)
            p.drawRect(QRectF(x, 0, seg_w - 2.0, h))
            x += seg_w


class DiskUsageCard(Card):
    """Nordic Zen disk capacity & storage visualizer."""

    def __init__(self, parent=None):
        super().__init__("panel", parent)
        import shutil
        from pathlib import Path

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        root_dir = Path.home().anchor or "C:\\"
        try:
            usage = shutil.disk_usage(root_dir)
            total_gb = usage.total / (1024 ** 3)
            used_gb = usage.used / (1024 ** 3)
            free_gb = usage.free / (1024 ** 3)
        except Exception:
            total_gb, used_gb, free_gb = 1000.0, 420.0, 580.0

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(icons.icon("disk", "#E2B170").pixmap(QSize(22, 22)))

        info_box = QVBoxLayout()
        info_box.setSpacing(1)
        clean_root = root_dir.rstrip(r"\/")
        title_lbl = QLabel(f"Local Disk ({clean_root}) — {used_gb:.1f} GB of {total_gb:.1f} GB Used")
        tf = title_lbl.font()
        tf.setBold(True)
        tf.setPointSize(12)
        title_lbl.setFont(tf)

        sub_lbl = QLabel(f"{free_gb:.1f} GB Available storage • Solid State Drive")
        sub_lbl.setProperty("kind", "muted")
        info_box.addWidget(title_lbl)
        info_box.addWidget(sub_lbl)

        badge_lbl = QLabel("● Ready to Sift")
        badge_lbl.setStyleSheet(
            "color: #E2B170; background: #222228; border: 1px solid #3A3A44; border-radius: 10px; padding: 3px 10px; font-size: 11px; font-weight: bold;"
        )

        top_row.addWidget(icon_lbl)
        top_row.addLayout(info_box, 1)
        top_row.addWidget(badge_lbl)
        lay.addLayout(top_row)

        self._gauge = StorageGauge()
        lay.addWidget(self._gauge)

        legend = QHBoxLayout()
        legend.setSpacing(18)
        items = [
            ("#3E3E48", "System & Apps"),
            ("#E2B170", "Photos & Media"),
            ("#98C379", "Documents"),
            ("#E06C75", "Caches & Dups"),
            ("#6A6A76", f"Free ({free_gb:.0f} GB)"),
        ]
        for col_hex, name in items:
            dot_lbl = QLabel(f"● {name}")
            dot_lbl.setStyleSheet(f"color: {col_hex}; font-size: 11px;")
            legend.addWidget(dot_lbl)
        legend.addStretch(1)
        lay.addLayout(legend)


class CategoryBentoCard(Card):
    """Concept 6 Bento Quick Cleaner Card with Apple-style toggle and large metric."""
    toggled = Signal(bool)

    def __init__(self, icon_name: str, title: str, stat_val: str, subtitle: str, checked: bool = True, parent=None):
        super().__init__("content", parent)
        self.setMinimumHeight(114)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(10)

        self._icon = QLabel()
        self._icon.setPixmap(icons.icon(icon_name, "#E2B170").pixmap(QSize(20, 20)))

        self._title = QLabel(title)
        tf = self._title.font()
        tf.setPointSize(12)
        tf.setWeight(QFont.Weight.DemiBold)
        self._title.setFont(tf)

        self._toggle = ToggleSwitch()
        self._toggle.setChecked(checked)
        self._toggle.toggled.connect(self.toggled.emit)

        top.addWidget(self._icon)
        top.addWidget(self._title, 1)
        top.addWidget(self._toggle)
        lay.addLayout(top)

        self._stat = QLabel(stat_val)
        sf = self._stat.font()
        sf.setPointSize(19)
        sf.setWeight(QFont.Weight.DemiBold)
        self._stat.setFont(sf)
        self._stat.setProperty("kind", "card-text")

        self._sub = QLabel(subtitle)
        self._sub.setProperty("kind", "muted")
        sub_f = self._sub.font()
        sub_f.setPointSize(10)
        self._sub.setFont(sub_f)

        lay.addWidget(self._stat)
        lay.addWidget(self._sub)

    def is_checked(self) -> bool:
        return self._toggle.isChecked()

    def set_stat(self, val: str) -> None:
        self._stat.setText(val)

