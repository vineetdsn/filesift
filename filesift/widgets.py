"""Reusable modern widgets: cards, buttons, toggles, rows, sidebar, preview."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import (QColor, QFont, QIcon, QImageReader, QLinearGradient,
                           QPainter, QPen, QPixmap)
from PySide6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLabel,
                               QPlainTextEdit, QPushButton, QToolButton, QVBoxLayout,
                               QWidget)

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
    """Rounded panel. kind="panel" is a flat surface; kind="content" is a light card."""

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
        if self._kind == "panel":
            p.setPen(QPen(QColor(pal.panel_border), 1))
            p.setBrush(QColor(pal.panel))
            p.drawRoundedRect(r, theme.RADIUS_CARD, theme.RADIUS_CARD)
        else:  # content
            grad = QLinearGradient(0, 0, 0, max(1, r.height()))
            grad.setColorAt(0.0, QColor(pal.card_top))
            grad.setColorAt(1.0, QColor(pal.card_bottom))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(grad)
            p.drawRoundedRect(r, theme.RADIUS_CARD, theme.RADIUS_CARD)


class StatCard(Card):
    def __init__(self, label: str, parent=None):
        super().__init__("content", parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 16)
        lay.setSpacing(2)
        self._value = QLabel(presenters.EM_DASH)
        f = self._value.font()
        f.setPointSize(theme.FONT_STAT_PT)
        f.setWeight(QFont.Weight.Light)
        self._value.setFont(f)
        self._value.setProperty("kind", "card-text")
        self._cap = QLabel(label)
        self._cap.setProperty("kind", "muted")
        cap_f = self._cap.font()
        cap_f.setPointSize(9)
        self._cap.setFont(cap_f)
        lay.addWidget(self._value)
        lay.addWidget(self._cap)

    def set_value(self, text: str) -> None:
        self._value.setText(text)


class PillButton(QPushButton):
    def __init__(self, text: str = "", primary: bool = False, parent=None):
        super().__init__(text, parent)
        self._primary = primary
        self.setProperty("primary", primary)
        self.setFixedHeight(theme.PILL_H)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pal = theme.current()
        r = self.rect()
        if self._primary:
            bg = QColor(pal.accent)
            fg = QColor(pal.on_accent)
        else:
            bg = QColor(pal.panel)
            fg = QColor(pal.text)
            p.setPen(QPen(QColor(pal.panel_border), 1))
        if self.isEnabled() and (self.isDown() or self.isChecked()):
            bg = bg.darker(112)
        if not self._primary:
            p.setBrush(bg)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), theme.PILL_RADIUS, theme.PILL_RADIUS)
            p.setPen(QPen(QColor(pal.panel_border), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r.adjusted(1, 1, -1, -1), theme.PILL_RADIUS, theme.PILL_RADIUS)
        else:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(bg)
            p.drawRoundedRect(r, theme.PILL_RADIUS, theme.PILL_RADIUS)
        p.setPen(fg)
        p.setFont(self.font())
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())


class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
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
        p.drawRoundedRect(0, 0, 44, 24, 12, 12)
        kx = 24 if on else 4
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(kx, 4, 16, 16)


class ListRow(QFrame):
    def __init__(self, icon_name: str | None = None, title: str = "",
                 subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setProperty("kind", "row")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(12)
        self._icon = QLabel()
        self._icon.setFixedSize(24, 24)
        if icon_name:
            self._icon.setPixmap(icons.icon(icon_name).pixmap(QSize(22, 22)))
        self._title = QLabel(title)
        f = self._title.font()
        f.setBold(True)
        self._title.setFont(f)
        self._sub = QLabel(subtitle)
        self._sub.setProperty("kind", "muted")
        col = QVBoxLayout()
        col.setSpacing(2)
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
    requested = Signal(str)

    def __init__(self, page_id: str, icon_name: str, parent=None):
        super().__init__(parent)
        self._page_id = page_id
        self._badge: int | None = None
        self._active = False
        self.setIcon(icons.icon(icon_name))
        self.setIconSize(QSize(26, 26))
        self.setFixedSize(theme.SIDEBAR_W, 64)
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
        if self._active:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.nav_hover))
            p.drawRoundedRect(self.rect().adjusted(8, 6, -8, -6),
                              theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)
            p.setBrush(QColor(pal.accent))
            p.drawRoundedRect(QRect(6, 16, 4, self.height() - 32), 2, 2)
        elif self.underMouse():
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.nav_hover))
            p.drawRoundedRect(self.rect().adjusted(8, 6, -8, -6),
                              theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)
        mode = QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled
        pm = self.icon().pixmap(QSize(26, 26), mode)
        p.drawPixmap((self.width() - pm.width()) // 2,
                     (self.height() - pm.height()) // 2, pm)
        text = presenters.format_badge(self._badge) if self._badge else None
        if text:
            f = self.font()
            f.setPointSize(7)
            f.setBold(True)
            p.setFont(f)
            fm = p.fontMetrics()
            tw = max(fm.horizontalAdvance(text), 14)
            cx = self.width() - tw - 6
            cy = 8
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(pal.accent))
            p.drawRoundedRect(QRect(cx, cy - 6, tw + 8, 14), 7, 7)
            p.setPen(QColor(pal.on_accent))
            p.drawText(QRect(cx, cy - 6, tw + 8, 14),
                       Qt.AlignmentFlag.AlignCenter, text)


class Sidebar(QFrame):
    page_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(theme.SIDEBAR_W)
        self.setProperty("kind", "sidebar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 18, 0, 18)
        lay.setSpacing(10)
        lay.addStretch(1)
        self._scan = NavButton("scan", "scan")
        self._dup = NavButton("duplicates", "duplicates")
        self._clean = NavButton("cleanup", "cleanup")
        for b in (self._scan, self._dup, self._clean):
            b.requested.connect(self.page_requested)
            lay.addWidget(b)
        lay.addStretch(2)

    def paintEvent(self, _e) -> None:
        p = QPainter(self)
        pal = theme.current()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(pal.panel))
        p.drawRect(self.rect())
        p.setPen(QPen(QColor(pal.panel_border), 1))
        p.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

    def set_active(self, page_id: str) -> None:
        self._scan.set_active(page_id == "scan")
        self._dup.set_active(page_id == "duplicates")
        self._clean.set_active(page_id == "cleanup")

    def set_badges(self, dups: int, safe: int) -> None:
        self._dup.set_badge(dups)
        self._clean.set_badge(safe)


class PreviewPanel(Card):
    def __init__(self, parent=None):
        super().__init__("content", parent)
        self.setMinimumWidth(300)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)
        self._image = QLabel("Select a file to preview")
        self._image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image.setMinimumHeight(280)
        self._image.setStyleSheet(
            "background:#20232E;color:#9AA0BE;border-radius:14px;")
        self._details = QPlainTextEdit()
        self._details.setReadOnly(True)
        self._details.setMaximumHeight(190)
        self._details.setPlaceholderText("File details")
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
