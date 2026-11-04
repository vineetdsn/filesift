"""Cleanup page: filtered/sorted file list with ticks and actions."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (QAbstractListModel, QEvent, QModelIndex, QRect,
                           QSize, Qt)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QHBoxLayout, QLabel,
                                QListView, QSplitter, QStyledItemDelegate,
                                QVBoxLayout, QWidget)

from . import cleanup_logic, dialogs, fileops, presenters, theme
from .context import AppContext
from .models import FileInfo
from .widgets import PillButton, PreviewPanel

ROW_H = 64


class CleanupModel(QAbstractListModel):
    FILE_ROLE = Qt.ItemDataRole.UserRole + 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self._files: list[FileInfo] = []

    def set_files(self, files: list[FileInfo]) -> None:
        self.beginResetModel()
        self._files = files
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._files)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == CleanupModel.FILE_ROLE:
            return self._files[index.row()]
        return None

    def file_at(self, row: int) -> FileInfo | None:
        return self._files[row] if 0 <= row < len(self._files) else None


class RowDelegate(QStyledItemDelegate):
    def __init__(self, page: "CleanupPage", parent=None):
        super().__init__(parent)
        self._page = page

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        return QSize(option.rect.width() or 600, ROW_H)

    def _verdict_color(self, f: FileInfo) -> QColor:
        pal = theme.current()
        if f.tags:
            return QColor(pal.accent)
        if f.bucket == "delete":
            return QColor(pal.accent)
        if f.bucket == "review":
            return QColor(pal.danger)
        return QColor(pal.text_muted)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        f: FileInfo | None = index.data(CleanupModel.FILE_ROLE)
        if f is None:
            return
        pal = theme.current()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        row = option.rect.adjusted(8, 4, -8, -4)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(pal.panel))
        painter.drawRoundedRect(row, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)
        if option.state & 0x80:  # QStyle.State_Selected
            painter.setBrush(QColor(pal.nav_hover))
            painter.drawRoundedRect(row, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        # category dot
        mid = row.top() + row.height() // 2
        painter.setBrush(self._verdict_color(f))
        painter.drawEllipse(QRect(row.left() + 14, mid - 9, 18, 18))

        # name + subtitle
        name_x = row.left() + 42
        name_w = row.width() - 42 - 200
        nf = QFont(painter.font())
        nf.setBold(True)
        painter.setFont(nf)
        painter.setPen(QColor(pal.text))
        painter.drawText(QRect(name_x, row.top() + 9, name_w, 18),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         f.name)
        sf = QFont(painter.font())
        sf.setBold(False)
        sf.setPointSize(8)
        painter.setFont(sf)
        painter.setPen(QColor(pal.text_muted))
        painter.drawText(QRect(name_x, row.top() + 30, name_w, 18),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         presenters.row_subtitle(f))

        # verdict pill
        label = cleanup_logic.VERDICT_LABEL.get(f.bucket, "Keep")
        if f.tags:
            label = "Important"
        if f.protected:
            label += " · protected"
        vc = self._verdict_color(f)
        pill = QRect(row.right() - 178, mid - 11, 130, 22)
        bg = QColor(vc)
        bg.setAlpha(48)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(bg)
        painter.drawRoundedRect(pill, 11, 11)
        painter.setPen(vc)
        pf = QFont(painter.font())
        pf.setPointSize(8)
        painter.setFont(pf)
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, label)

        # tick box
        tick = QRect(row.right() - 34, mid - 11, 22, 22)
        painter.setPen(QPen(QColor(pal.input_border), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(tick, 5, 5)
        if self._page._ticks.is_ticked(f.path):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(pal.accent))
            painter.drawRoundedRect(tick.adjusted(4, 4, -4, -4), 3, 3)
            painter.setPen(QColor(pal.on_accent))
            painter.drawLine(tick.left() + 6, tick.center().y(),
                             tick.center().x() - 1, tick.bottom() - 6)
            painter.drawLine(tick.center().x() - 1, tick.bottom() - 6,
                             tick.right() - 5, tick.top() + 6)
        painter.restore()

    def editorEvent(self, event, model, option, index: QModelIndex) -> bool:
        if event.type() == QEvent.Type.MouseButtonPress and index.isValid():
            f: FileInfo | None = index.data(CleanupModel.FILE_ROLE)
            if f is None:
                return False
            row = option.rect.adjusted(8, 4, -8, -4)
            mid = row.top() + row.height() // 2
            tick = QRect(row.right() - 34, mid - 11, 22, 22)
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            if tick.contains(pos):
                self._page._ticks.toggle(f)
                self._page._view.update(index)
                return True
        return super().editorEvent(event, model, option, index)


class CleanupPage(QWidget):
    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self._all: list[FileInfo] = []
        self._model = CleanupModel()
        self._ticks = cleanup_logic.TickSet()

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 22)
        lay.setSpacing(14)

        self._summary = QLabel("Run a scan first.")
        self._summary.setProperty("kind", "muted")
        lay.addWidget(self._summary)

        # filter pills + combos
        filt = QHBoxLayout()
        filt.setSpacing(8)
        self._verdict_group = QButtonGroup(self)
        self._verdict_group.setExclusive(True)
        for i, name in enumerate(cleanup_logic.VERDICT_FILTERS):
            b = PillButton(name)
            b.setCheckable(True)
            b.setChecked(i == 0)
            b.clicked.connect(self._refresh)
            self._verdict_group.addButton(b)
            filt.addWidget(b)
        filt.addStretch(1)
        filt.addWidget(QLabel("Category:"))
        self._category = QComboBox()
        self._category.addItem("All categories")
        self._category.currentIndexChanged.connect(self._refresh)
        filt.addWidget(self._category)
        filt.addWidget(QLabel("Sort:"))
        self._sort = QComboBox()
        self._sort.addItems(list(cleanup_logic.SORTS))
        self._sort.currentIndexChanged.connect(self._refresh)
        filt.addWidget(self._sort)
        lay.addLayout(filt)

        # actions
        act = QHBoxLayout()
        act.setSpacing(10)
        tick_safe = PillButton("Tick all safe to delete")
        tick_safe.clicked.connect(self._tick_safe)
        clear = PillButton("Clear ticks")
        clear.clicked.connect(self._clear_ticks)
        imp = PillButton("Move to Important folder")
        imp.clicked.connect(self._move_important)
        trash = PillButton("Move to Recycle Bin", primary=True)
        theme.add_glow(trash)
        trash.clicked.connect(self._trash_ticked)
        act.addWidget(tick_safe)
        act.addWidget(clear)
        act.addStretch(1)
        act.addWidget(imp)
        act.addWidget(trash)
        lay.addLayout(act)

        self._view = QListView()
        self._view.setModel(self._model)
        self._view.setItemDelegate(RowDelegate(self, self._view))
        self._view.setSpacing(6)
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
    def load(self, files: list[FileInfo]) -> None:
        self._all = list(files)
        self._ticks.clear()
        self._category.blockSignals(True)
        self._category.clear()
        self._category.addItem("All categories")
        self._category.addItems(cleanup_logic.categories(self._all))
        self._category.blockSignals(False)
        self._summary.setText(
            cleanup_logic.summary_text(cleanup_logic.summarize(self._all)))
        self._refresh()

    def _current_verdict(self) -> str:
        for b in self._verdict_group.buttons():
            if b.isChecked():
                return b.text()
        return "All"

    def _refresh(self) -> None:
        verdict = self._current_verdict()
        category = self._category.currentText() or "All categories"
        sort = self._sort.currentText()
        visible = cleanup_logic.filter_and_sort(self._all, verdict, category, sort)
        self._model.set_files(visible[:cleanup_logic.MAX_ROWS])
        self._status.setText(cleanup_logic.match_status(len(visible)))

    def safe_to_delete_count(self) -> int:
        return sum(1 for f in self._all if f.bucket == "delete")

    # ----- actions -----
    def _on_clicked(self, index: QModelIndex) -> None:
        self._preview.show_file(self._model.file_at(index.row()))

    def _tick_safe(self) -> None:
        self._ticks.tick_all_safe(
            [self._model.file_at(i) for i in range(self._model.rowCount())
             if self._model.file_at(i)])
        self._view.viewport().update()

    def _clear_ticks(self) -> None:
        self._ticks.clear()
        self._view.viewport().update()

    def _ticked_files(self) -> list[FileInfo]:
        return self._ticks.actionable(
            [self._model.file_at(i) for i in range(self._model.rowCount())
             if self._model.file_at(i)])

    def _forget(self, paths: set[str]) -> None:
        self._all = cleanup_logic.without_paths(self._all, paths)
        self._ticks.discard(paths)
        self.ctx.cache.forget(list(paths))
        self._summary.setText(
            cleanup_logic.summary_text(cleanup_logic.summarize(self._all)))
        self._refresh()

    def _trash_ticked(self) -> None:
        files = self._ticked_files()
        if not files:
            self._status.setText("Nothing ticked.")
            return
        msg, warning = fileops.trash_confirm_text(files)
        text = msg + (("\n\n" + warning) if warning else "")
        if not dialogs.confirm(self, "Move to Recycle Bin", text,
                               ok_text="Move to Recycle Bin"):
            return
        done, errors = fileops.trash_files([f.path for f in files])
        if done:
            self._forget(set(done))
        if errors:
            dialogs.message(self, "Some files failed",
                            fileops.error_dialog_text(errors))
        self._status.setText(f"Moved {len(done)} files to the Recycle Bin.")

    def _move_important(self) -> None:
        files = self._ticked_files()
        if not files:
            self._status.setText("Nothing ticked.")
            return
        base = self.ctx.settings.vault_dir / "Important"
        if not dialogs.confirm(self, "Move to Important folder",
                                fileops.move_confirm_text(files, base),
                                ok_text="Move"):
            return
        moved_all: list[tuple[str, str]] = []
        errors: list[str] = []
        groups: dict[str, list[str]] = {}
        for f in files:
            groups.setdefault(fileops.important_destination(f, base).name, []).append(f.path)
        for sub, paths in groups.items():
            m, e = fileops.move_files(paths, base / sub)
            moved_all += m
            errors += e
        if moved_all:
            self._forget({src for src, _ in moved_all})
        if errors:
            dialogs.message(self, "Some files failed",
                            fileops.error_dialog_text(errors))
        self._status.setText(f"Moved {len(moved_all)} files into {base}.")
