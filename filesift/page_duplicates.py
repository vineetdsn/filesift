"""Duplicates page: group list with tile grid, selection and delete — Nordic Zen UI/UX."""
from __future__ import annotations

from PySide6.QtCore import (QAbstractListModel, QEvent, QModelIndex, QPoint,
                            QRect, QRectF, QSize, Qt)
from PySide6.QtGui import QColor, QFont, QImageReader, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QListView,
                                QSplitter, QStyledItemDelegate,
                                QVBoxLayout, QWidget)

from . import dialogs, fileops, presenters, theme
from .context import AppContext
from .duplicates import KEEPER_RULES
from .models import DupGroup, FileInfo
from .selection import LAST_COPY_MSG, SelectionState, ToggleResult
from .widgets import Card, PillButton, PreviewPanel

TILE_W = 168
TILE_H = 196
THUMB_H = 120
HEADER_H = 46


def _load_thumb(path: str, box: int) -> QPixmap:
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and size.width() > 0:
        size.scale(QSize(box, box), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)
    img = reader.read()
    return QPixmap.fromImage(img) if not img.isNull() else QPixmap()


class GroupModel(QAbstractListModel):
    GROUP_ROLE = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self._state: SelectionState | None = None

    def set_state(self, state: SelectionState) -> None:
        self.beginResetModel()
        self._state = state
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid() or self._state is None:
            return 0
        return self._state.group_count()

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._state is None:
            return None
        if role == GroupModel.GROUP_ROLE:
            return self._state.group_at(index.row())
        return None

    def refresh(self) -> None:
        self.beginResetModel()
        self.endResetModel()


class GroupDelegate(QStyledItemDelegate):
    def __init__(self, page: "DuplicatesPage", parent=None):
        super().__init__(parent)
        self._page = page

    def _group(self, index: QModelIndex) -> DupGroup | None:
        return index.data(GroupModel.GROUP_ROLE)

    def _tiles(self, group: DupGroup, row: QRect) -> list[tuple[FileInfo, QRect]]:
        cols = max(1, (row.width() - 24) // (TILE_W + 10))
        out = []
        x0, y0 = row.left() + 14, row.top() + HEADER_H
        for i, f in enumerate(group.files):
            r, c = i // cols, i % cols
            out.append((f, QRect(x0 + c * (TILE_W + 10), y0 + r * (TILE_H + 10),
                                  TILE_W, TILE_H)))
        return out

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        group = self._group(index)
        if group is None:
            return QSize(0, 0)
        w = option.rect.width() or 600
        cols = max(1, (w - 24) // (TILE_W + 10))
        rows = max(1, (len(group.files) + cols - 1) // cols)
        return QSize(w, HEADER_H + rows * (TILE_H + 10) + 12)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        group = self._group(index)
        if group is None:
            return
        pal = theme.current()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        bg = option.rect.adjusted(6, 6, -6, -6)
        painter.setPen(QPen(QColor(pal.panel_border), 1))
        painter.setBrush(QColor(pal.panel))
        painter.drawRoundedRect(bg, theme.RADIUS_CARD, theme.RADIUS_CARD)

        header_rect = QRect(bg.left() + 14, bg.top() + 8, bg.width() - 28, HEADER_H - 12)
        f = QFont(painter.font())
        f.setPointSize(12)
        f.setBold(True)
        painter.setFont(f)
        painter.setPen(QColor(pal.text))
        header_text = presenters.group_header(index.row() + 1, group)
        painter.drawText(header_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, header_text)

        for f, r in self._tiles(group, option.rect):
            self._paint_tile(painter, f, r)
        painter.restore()

    def _paint_tile(self, painter: QPainter, f: FileInfo, r: QRect) -> None:
        pal = theme.current()
        marked = self._page._state.is_marked(f.path)

        painter.setPen(Qt.PenStyle.NoPen)
        tile_bg = QColor(pal.card_top) if not marked else QColor(pal.danger).darker(280)
        painter.setBrush(tile_bg)
        painter.drawRoundedRect(r, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        if marked:
            painter.setPen(QPen(QColor(pal.danger), 1.5))
        else:
            painter.setPen(QPen(QColor(pal.accent), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(r.adjusted(1, 1, -1, -1), theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        thumb = r.adjusted(6, 6, -6, -(TILE_H - THUMB_H - 6))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(pal.bg))
        painter.drawRoundedRect(thumb, theme.RADIUS_CONTROL - 2, theme.RADIUS_CONTROL - 2)

        pm = self._page.thumb(f)
        if not pm.isNull():
            scaled = pm.scaled(thumb.size(), Qt.AspectRatioMode.KeepAspectRatio,
                               Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(thumb.left() + (thumb.width() - scaled.width()) // 2,
                               thumb.top() + (thumb.height() - scaled.height()) // 2, scaled)
        else:
            painter.setPen(QColor(pal.text_muted))
            painter.drawText(thumb, Qt.AlignmentFlag.AlignCenter,
                             presenters.placeholder_label(f))

        badge_w, badge_h = 52, 20
        badge_rect = QRect(r.right() - badge_w - 6, r.top() + 6, badge_w, badge_h)
        painter.setPen(Qt.PenStyle.NoPen)
        if marked:
            painter.setBrush(QColor(pal.danger))
            badge_text = "DELETE"
            badge_fg = QColor("#FFFFFF")
        else:
            painter.setBrush(QColor(pal.accent))
            badge_text = "KEEP"
            badge_fg = QColor(pal.on_accent)

        painter.drawRoundedRect(badge_rect, 6, 6)
        painter.setPen(badge_fg)
        bf = QFont(painter.font())
        bf.setPointSize(8)
        bf.setBold(True)
        painter.setFont(bf)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, badge_text)

        name, size, meta = presenters.tile_lines(f)
        painter.setPen(QColor(pal.text))
        nf = QFont(painter.font())
        nf.setBold(True)
        nf.setPointSize(9)
        painter.setFont(nf)
        painter.drawText(QRect(r.left() + 8, thumb.bottom() + 6, r.width() - 16, 16),
                         Qt.AlignmentFlag.AlignLeft, _elide(name, r.width() - 16, painter))

        painter.setPen(QColor(pal.text_muted))
        sf = QFont(painter.font())
        sf.setBold(False)
        sf.setPointSize(8)
        painter.setFont(sf)
        painter.drawText(QRect(r.left() + 8, thumb.bottom() + 23, r.width() - 16, 14),
                         Qt.AlignmentFlag.AlignLeft, size)
        painter.drawText(QRect(r.left() + 8, thumb.bottom() + 38, r.width() - 16, 14),
                         Qt.AlignmentFlag.AlignLeft, meta)

    def editorEvent(self, event, model, option, index: QModelIndex) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and index.isValid():
            group = self._group(index)
            if group is None:
                return False
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            for f, r in self._tiles(group, option.rect):
                if r.contains(pos):
                    res = self._page._state.toggle(f.path)
                    self._page._model.refresh()
                    self._page._update_marked()
                    if res == ToggleResult.REFUSED_LAST:
                        self._page._status.setText(LAST_COPY_MSG)
                    elif res == ToggleResult.REFUSED_PROTECTED:
                        self._page._status.setText("Protected files are kept automatically.")
                    return True
        return super().editorEvent(event, model, option, index)


def _elide(text: str, width: int, painter: QPainter) -> str:
    fm = painter.fontMetrics()
    if fm.horizontalAdvance(text) <= width:
        return text
    ell = "…"
    while text and fm.horizontalAdvance(text + ell) > width:
        text = text[:-1]
    return text + ell if text else ell


class DuplicatesPage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._state = SelectionState([])
        self._model = GroupModel()
        self._model.set_state(self._state)
        self._thumbs: dict[str, QPixmap] = {}

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        page_title = QLabel("Duplicate Files Review")
        ptf = page_title.font()
        ptf.setPointSize(18)
        ptf.setBold(True)
        page_title.setFont(ptf)

        self._summary = QLabel("Run a scan from the Scan & Folders tab to find duplicates.")
        self._summary.setProperty("kind", "muted")
        title_box.addWidget(page_title)
        title_box.addWidget(self._summary)
        lay.addLayout(title_box)

        # Controls & action toolbar
        tool_card = Card("panel")
        bar = QHBoxLayout(tool_card)
        bar.setContentsMargins(14, 10, 14, 10)
        bar.setSpacing(10)

        keep_lbl = QLabel("Keeper Rule:")
        kf = keep_lbl.font()
        kf.setBold(True)
        keep_lbl.setFont(kf)
        bar.addWidget(keep_lbl)

        self._rule = QComboBox()
        self._rule.addItems(list(KEEPER_RULES))
        self._rule.setMinimumWidth(160)
        bar.addWidget(self._rule)

        auto = PillButton("Auto-select Keepers")
        auto.clicked.connect(self._auto_select)
        clear = PillButton("Clear Selection")
        clear.clicked.connect(self._clear_selection)
        bar.addWidget(auto)
        bar.addWidget(clear)
        bar.addStretch(1)

        self._marked_lbl = QLabel("Nothing marked")
        self._marked_lbl.setProperty("kind", "muted")
        mf = self._marked_lbl.font()
        mf.setBold(True)
        self._marked_lbl.setFont(mf)
        bar.addWidget(self._marked_lbl)

        self._delete_btn = PillButton("Move to Recycle Bin", danger=True)
        theme.add_glow(self._delete_btn)
        self._delete_btn.clicked.connect(self._delete)
        bar.addWidget(self._delete_btn)
        lay.addWidget(tool_card)

        # Splitter: List view + Preview panel
        self._view = QListView()
        self._view.setModel(self._model)
        self._view.setItemDelegate(GroupDelegate(self, self._view))
        self._view.setSpacing(8)
        self._view.clicked.connect(self._on_clicked)
        self._preview = PreviewPanel()

        split = QSplitter()
        split.addWidget(self._view)
        split.addWidget(self._preview)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        lay.addWidget(split, 1)

        self._status = QLabel("")
        self._status.setProperty("kind", "muted")
        lay.addWidget(self._status)

    # ----- data -----
    def load(self, groups: list[DupGroup]) -> None:
        self._state = SelectionState(groups)
        self._model.set_state(self._state)
        self._thumbs.clear()
        self._update_summary()

    def _update_summary(self) -> None:
        self._summary.setText(
            presenters.duplicates_summary(self._state.group_count(),
                                           self._state.total_reclaimable()))
        self._update_marked()

    def _update_marked(self) -> None:
        self._marked_lbl.setText(
            presenters.marked_text(len(self._state.marked_files()),
                                   self._state.marked_size()))

    def thumb(self, f: FileInfo) -> QPixmap:
        if f.path in self._thumbs:
            return self._thumbs[f.path]
        pm = _load_thumb(f.path, THUMB_H) if f.is_image else QPixmap()
        if len(self._thumbs) > 800:
            self._thumbs.clear()
        self._thumbs[f.path] = pm
        return pm

    # ----- actions -----
    def _auto_select(self) -> None:
        self._state.auto_select(self._rule.currentText())
        self._model.refresh()
        self._update_marked()
        self._status.setText(f"Automatically marked duplicates using rule '{self._rule.currentText()}'.")

    def _clear_selection(self) -> None:
        self._state.clear()
        self._model.refresh()
        self._update_marked()
        self._status.setText("Selection cleared.")

    def _on_clicked(self, index: QModelIndex) -> None:
        group = index.data(GroupModel.GROUP_ROLE)
        if group and group.files:
            self._preview.show_file(group.files[0])

    def _delete(self) -> None:
        files = self._state.marked_files()
        if not files:
            self._status.setText("No duplicate files marked for deletion.")
            return
        msg, warning = fileops.trash_confirm_text(files)
        text = msg + (("\n\n" + warning) if warning else "")
        if not dialogs.confirm(self, "Move Duplicates to Recycle Bin", text,
                               ok_text="Move to Recycle Bin"):
            return
        done, errors = fileops.trash_files([f.path for f in files])
        if done:
            self.ctx.cache.forget(done)
            self._model.beginResetModel()
            self._state.remove_files(set(done))
            self._model.endResetModel()
        if errors:
            dialogs.message(self, "Some files failed",
                            fileops.error_dialog_text(errors))
        freed = sum(f.size for f in files if f.path in set(done))
        self._status.setText(f"Safely moved {len(done)} files to Recycle Bin"
                             + (f" (freed {freed // 1024} KB)" if done else "") + ".")
        self._update_summary()
