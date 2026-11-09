"""Whisper-thin Swiss vector glyphs drawn cleanly in code — Nordic Zen style."""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QIconEngine, QPainter, QPainterPath, QPen, QPixmap, QPolygonF

from . import theme

_STROKE = 1.5


class _LineIconEngine(QIconEngine):
    def __init__(self, name: str, color_override: str | None = None):
        super().__init__()
        self._name = name
        self._color_override = color_override

    def paint(self, painter: QPainter, rect: QRect, mode, state):  # noqa: A002
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = rect.width(), rect.height()
        sx = w / 24.0
        sy = h / 24.0

        pal = theme.current()
        if self._color_override:
            col = QColor(self._color_override)
        elif mode == QIcon.Mode.Disabled:
            col = QColor(pal.text_muted)
            col.setAlpha(100)
        else:
            col = QColor(pal.text)

        pen = QPen(col, _STROKE)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        n = self._name
        if n == "scan":
            # Delicate magnifying lens
            painter.drawEllipse(QRectF(4.5 * sx, 4.5 * sy, 10 * sx, 10 * sy))
            painter.drawLine(QPointF(12 * sx, 12 * sy), QPointF(19 * sx, 19 * sy))

        elif n == "duplicates":
            # Clean geometric overlapping cards
            painter.drawRoundedRect(QRectF(7 * sx, 3.5 * sy, 12.5 * sx, 14 * sy), 2 * sx, 2 * sy)
            path = QPainterPath()
            path.moveTo(4.5 * sx, 7 * sy)
            path.lineTo(4.5 * sx, 20.5 * sy)
            path.lineTo(16.5 * sx, 20.5 * sy)
            painter.drawPath(path)

        elif n == "cleanup":
            # Magic wand / sparkles
            painter.drawLine(QPointF(4 * sx, 20 * sy), QPointF(15 * sx, 9 * sy))
            painter.drawLine(QPointF(17 * sx, 3 * sy), QPointF(17 * sx, 7 * sy))
            painter.drawLine(QPointF(15 * sx, 5 * sy), QPointF(19 * sx, 5 * sy))
            painter.drawLine(QPointF(7 * sx, 3 * sy), QPointF(7 * sx, 6 * sy))
            painter.drawLine(QPointF(5.5 * sx, 4.5 * sy), QPointF(8.5 * sx, 4.5 * sy))

        elif n == "folder":
            # Architectural minimal folder
            path = QPainterPath()
            path.moveTo(3.5 * sx, 6.5 * sy)
            path.lineTo(9 * sx, 6.5 * sy)
            path.lineTo(11 * sx, 8.5 * sy)
            path.lineTo(20.5 * sx, 8.5 * sy)
            path.lineTo(20.5 * sx, 18.5 * sy)
            path.lineTo(3.5 * sx, 18.5 * sy)
            path.closeSubpath()
            painter.drawPath(path)

        elif n == "trash":
            # Sleek waste basket
            painter.drawLine(QPointF(4.5 * sx, 6.5 * sy), QPointF(19.5 * sx, 6.5 * sy))
            painter.drawLine(QPointF(9.5 * sx, 4.5 * sy), QPointF(14.5 * sx, 4.5 * sy))
            path = QPainterPath()
            path.moveTo(6.5 * sx, 6.5 * sy)
            path.lineTo(7.5 * sx, 19 * sy)
            path.lineTo(16.5 * sx, 19 * sy)
            path.lineTo(17.5 * sx, 6.5 * sy)
            painter.drawPath(path)
            painter.drawLine(QPointF(10.5 * sx, 9.5 * sy), QPointF(10.5 * sx, 16 * sy))
            painter.drawLine(QPointF(13.5 * sx, 9.5 * sy), QPointF(13.5 * sx, 16 * sy))

        elif n == "important":
            # Delicate 5-point star
            star_pts = [
                QPointF(12 * sx, 3.5 * sy),
                QPointF(14.6 * sx, 8.8 * sy),
                QPointF(20.5 * sx, 9.6 * sy),
                QPointF(16.2 * sx, 13.8 * sy),
                QPointF(17.4 * sx, 19.8 * sy),
                QPointF(12 * sx, 16.8 * sy),
                QPointF(6.6 * sx, 19.8 * sy),
                QPointF(7.8 * sx, 13.8 * sy),
                QPointF(3.5 * sx, 9.6 * sy),
                QPointF(9.4 * sx, 8.8 * sy),
            ]
            painter.drawPolygon(QPolygonF(star_pts))

        elif n == "check":
            path = QPainterPath()
            path.moveTo(4.5 * sx, 12 * sy)
            path.lineTo(9.5 * sx, 17 * sy)
            path.lineTo(19.5 * sx, 7 * sy)
            painter.drawPath(path)

        elif n == "plus":
            painter.drawLine(QPointF(12 * sx, 5.5 * sy), QPointF(12 * sx, 18.5 * sy))
            painter.drawLine(QPointF(5.5 * sx, 12 * sy), QPointF(18.5 * sx, 12 * sy))

        elif n == "minus":
            painter.drawLine(QPointF(5.5 * sx, 12 * sy), QPointF(18.5 * sx, 12 * sy))

        elif n == "close":
            painter.drawLine(QPointF(6.5 * sx, 6.5 * sy), QPointF(17.5 * sx, 17.5 * sy))
            painter.drawLine(QPointF(17.5 * sx, 6.5 * sy), QPointF(6.5 * sx, 17.5 * sy))

        elif n == "image":
            # Photo frame with peak & sun
            painter.drawRoundedRect(QRectF(3.5 * sx, 4.5 * sy, 17 * sx, 15 * sy), 2 * sx, 2 * sy)
            painter.drawEllipse(QRectF(7.5 * sx, 7.5 * sy, 2.5 * sx, 2.5 * sy))
            path = QPainterPath()
            path.moveTo(3.5 * sx, 15.5 * sy)
            path.lineTo(8 * sx, 11 * sy)
            path.lineTo(13 * sx, 15.5 * sy)
            path.lineTo(16 * sx, 12.5 * sy)
            path.lineTo(20.5 * sx, 16.5 * sy)
            painter.drawPath(path)

        elif n == "file":
            # Minimal folded document
            path = QPainterPath()
            path.moveTo(5.5 * sx, 3.5 * sy)
            path.lineTo(14 * sx, 3.5 * sy)
            path.lineTo(18.5 * sx, 8 * sy)
            path.lineTo(18.5 * sx, 20.5 * sy)
            path.lineTo(5.5 * sx, 20.5 * sy)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(QPointF(14 * sx, 3.5 * sy), QPointF(14 * sx, 8 * sy))
            painter.drawLine(QPointF(14 * sx, 8 * sy), QPointF(18.5 * sx, 8 * sy))

        elif n == "disk":
            # Sleek hard drive / storage icon
            painter.drawRoundedRect(QRectF(3.5 * sx, 6 * sy, 17 * sx, 12 * sy), 2 * sx, 2 * sy)
            painter.drawLine(QPointF(3.5 * sx, 13 * sy), QPointF(20.5 * sx, 13 * sy))
            painter.drawEllipse(QRectF(16 * sx, 14.5 * sy, 1.8 * sx, 1.8 * sy))

        elif n == "shield":
            # Clean protective shield
            path = QPainterPath()
            path.moveTo(12 * sx, 3.5 * sy)
            path.lineTo(19.5 * sx, 6.5 * sy)
            path.lineTo(19.5 * sx, 12.5 * sy)
            path.cubicTo(19.5 * sx, 17 * sy, 15 * sx, 20.5 * sy, 12 * sx, 21.5 * sy)
            path.cubicTo(9 * sx, 20.5 * sy, 4.5 * sx, 17 * sy, 4.5 * sx, 12.5 * sy)
            path.lineTo(4.5 * sx, 6.5 * sy)
            path.closeSubpath()
            painter.drawPath(path)

        elif n == "more":
            # Three minimalist dots
            painter.drawEllipse(QRectF(5 * sx, 11 * sy, 2 * sx, 2 * sy))
            painter.drawEllipse(QRectF(11 * sx, 11 * sy, 2 * sx, 2 * sy))
            painter.drawEllipse(QRectF(17 * sx, 11 * sy, 2 * sx, 2 * sy))

        elif n == "moon":
            path = QPainterPath()
            path.moveTo(18 * sx, 13 * sy)
            path.arcTo(QRectF(5 * sx, 3.5 * sy, 15 * sx, 17 * sy), -45, 270)
            path.arcTo(QRectF(8 * sx, 5.5 * sy, 12 * sx, 13 * sy), 180, -180)
            painter.drawPath(path)

        elif n == "sun":
            painter.drawEllipse(QRectF(8 * sx, 8 * sy, 8 * sx, 8 * sy))
            for dx, dy in [(12, 3), (12, 21), (3, 12), (21, 12), (5.5, 5.5), (18.5, 18.5), (18.5, 5.5), (5.5, 18.5)]:
                painter.drawPoint(QPointF(dx * sx, dy * sy))

        painter.restore()

    def clone(self):
        return _LineIconEngine(self._name, self._color_override)

    def pixmap(self, size, mode, state):
        pm = QPixmap(size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        self.paint(painter, QRect(0, 0, size.width(), size.height()), mode, state)
        painter.end()
        return pm


def icon(name: str, color: str | None = None) -> QIcon:
    return QIcon(_LineIconEngine(name, color))
