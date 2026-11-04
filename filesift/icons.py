"""Line icons drawn in code — no asset files needed."""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QIcon, QIconEngine, QPainter, QPen, QPixmap, QPolygon

_STROKE = 2.0

# (name -> list of (x1,y1,x2,y2) lines in a 24x24 grid)
_SHAPES: dict[str, list[tuple[int, int, int, int]]] = {
    "scan": [(4, 4, 14, 14), (11, 14, 14, 11), (18, 18, 21, 21), (17, 17, 21, 21)],
    "duplicates": [(4, 7, 16, 7), (16, 7, 20, 11), (20, 11, 20, 17), (12, 17, 20, 17),
                   (4, 11, 4, 19), (4, 19, 12, 19), (12, 19, 12, 11), (4, 11, 12, 11)],
    "cleanup": [(5, 18, 18, 5), (5, 5, 11, 11), (14, 5, 19, 10), (12, 8, 16, 4),
                (8, 16, 4, 20)],
    "folder": [(3, 7, 3, 19), (3, 19, 21, 19), (21, 19, 21, 9), (21, 9, 11, 9),
               (11, 9, 9, 7), (9, 7, 3, 7)],
    "trash": [(6, 7, 6, 20), (10, 7, 10, 20), (14, 7, 14, 20), (18, 7, 18, 20),
              (4, 7, 20, 7), (9, 4, 15, 4), (15, 4, 15, 7), (9, 4, 9, 7)],
    "important": [(12, 3, 14, 9), (14, 9, 20, 9), (15, 13, 12, 11), (9, 13, 12, 11),
                  (10, 9, 12, 3), (7, 21, 12, 18), (12, 18, 17, 21)],
    "check": [(5, 13, 10, 18), (10, 18, 20, 6)],
    "plus": [(12, 4, 12, 20), (4, 12, 20, 12)],
    "minus": [(4, 12, 20, 12)],
    "close": [(6, 6, 18, 18), (18, 6, 6, 18)],
    "image": [(4, 6, 4, 18), (4, 18, 20, 18), (20, 18, 20, 6), (20, 6, 4, 6),
              (8, 11, 8, 11), (16, 11, 16, 11)],
    "file": [(6, 3, 6, 21), (6, 3, 14, 3), (14, 3, 18, 7), (18, 7, 18, 21),
             (6, 21, 18, 21), (14, 3, 14, 7), (14, 7, 18, 7)],
}

# single points drawn as small dots
_POINTS: dict[str, list[tuple[int, int]]] = {
    "image": [(9, 11), (14, 14), (17, 16)],
}


class _LineIconEngine(QIconEngine):
    def __init__(self, name: str):
        super().__init__()
        self._name = name

    def paint(self, painter: QPainter, rect: QRect, mode, state):  # noqa: A002
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        sx = rect.width() / 24.0
        sy = rect.height() / 24.0
        pen = QPen(QColor("#9AA0BE"), _STROKE)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        for x1, y1, x2, y2 in _SHAPES.get(self._name, ()):
            painter.drawLine(QPoint(int(x1 * sx), int(y1 * sy)),
                             QPoint(int(x2 * sx), int(y2 * sy)))
        if self._name == "important":
            poly = QPolygon([QPoint(int(12 * sx), int(4 * sy)),
                             QPoint(int(15 * sx), int(10 * sy)),
                             QPoint(int(21 * sx), int(11 * sy)),
                             QPoint(int(16 * sx), int(15 * sy)),
                             QPoint(int(18 * sx), int(21 * sy)),
                             QPoint(int(12 * sx), int(18 * sy)),
                             QPoint(int(6 * sx), int(21 * sy)),
                             QPoint(int(8 * sx), int(15 * sy)),
                             QPoint(int(3 * sx), int(11 * sy)),
                             QPoint(int(9 * sx), int(10 * sy))])
            painter.drawPolygon(poly)
        for px, py in _POINTS.get(self._name, ()):
            painter.setBrush(QColor("#9AA0BE"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPoint(int(px * sx), int(py * sy)),
                                int(1.2 * sx), int(1.2 * sy))
        painter.restore()

    def clone(self):
        return _LineIconEngine(self._name)

    def pixmap(self, size, mode, state):
        pm = QPixmap(size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        self.paint(painter, QRect(0, 0, size.width(), size.height()), mode, state)
        painter.end()
        return pm


def icon(name: str) -> QIcon:
    return QIcon(_LineIconEngine(name))
