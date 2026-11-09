"""Cleanup page: filtered/sorted file list with ticks and actions — Nordic Zen UI/UX."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (QAbstractListModel, QEvent, QModelIndex, QRect,
                            QSize, Qt)
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QButtonGroup, QComboBox, QHBoxLayout, QLabel,
                                QListView, QSplitter, QStyle, QStyledItemDelegate,
                                QVBoxLayout, QWidget)

from . import cleanup_logic, dialogs, fileops, presenters, theme
from .context import AppContext
from .models import FileInfo
from .widgets import Card, PillButton, PreviewPanel

ROW_H = 68


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
            return QColor(pal.warning)
        return QColor(pal.text_muted)

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        f: FileInfo | None = index.data(CleanupModel.FILE_ROLE)
        if f is None:
            return
        pal = theme.current()
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        row = option.rect.adjusted(8, 4, -8, -4)
        painter.setPen(QPen(QColor(pal.panel_border), 1))
        painter.setBrush(QColor(pal.panel))
        painter.drawRoundedRect(row, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        if bool(option.state & QStyle.StateFlag.State_Selected):
            painter.setPen(QPen(QColor(pal.accent), 1))
            painter.setBrush(QColor(pal.nav_hover))
            painter.drawRoundedRect(row, theme.RADIUS_CONTROL, theme.RADIUS_CONTROL)

        mid = row.top() + row.height() // 2

        # Minimalist category dot
        vc = self._verdict_color(f)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(vc)
        painter.drawEllipse(QRect(row.left() + 16, mid - 6, 12, 12))

        # File name & subtitle
        name_x = row.left() + 38
        name_w = row.width() - 38 - 220
        nf = QFont(painter.font())
        nf.setBold(True)
        nf.setPointSize(10)
        painter.setFont(nf)
        painter.setPen(QColor(pal.text))
        painter.drawText(QRect(name_x, row.top() + 12, name_w, 20),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         f.name)

        sf = QFont(painter.font())
        sf.setBold(False)
        sf.setPointSize(9)
        painter.setFont(sf)
        painter.setPen(QColor(pal.text_muted))
        painter.drawText(QRect(name_x, row.top() + 34, name_w, 18),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         presenters.row_subtitle(f))

        # Status micro-pill
        label = cleanup_logic.VERDICT_LABEL.get(f.bucket, "Keep")
        if f.tags:
            label = "Important"
        if f.protected:
            label += " · protected"

        pill = QRect(row.right() - 190, mid - 12, 140, 24)
        bg = QColor(vc)
        bg.setAlpha(28)
        painter.setPen(QPen(vc, 1))
        painter.setBrush(bg)
        painter.drawRoundedRect(pill, 6, 6)

        painter.setPen(vc)
        pf = QFont(painter.font())
        pf.setPointSize(8)
        pf.setBold(True)
        painter.setFont(pf)
        painter.drawText(pill, Qt.AlignmentFlag.AlignCenter, label)

        # Minimal checkbox
        tick = QRect(row.right() - 34, mid - 11, 22, 22)
        is_ticked = self._page._ticks.is_ticked(f.path)

        if is_ticked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(pal.accent))
            painter.drawRoundedRect(tick, 5, 5)
            painter.setPen(QPen(QColor(pal.on_accent), 1.5))
            painter.drawLine(tick.left() + 5, tick.center().y(),
                             tick.center().x() - 1, tick.bottom() - 6)
            painter.drawLine(tick.center().x() - 1, tick.bottom() - 6,
                             tick.right() - 5, tick.top() + 6)
        else:
            painter.setPen(QPen(QColor(pal.input_border), 1))
            painter.setBrush(QColor(pal.bg))
            painter.drawRoundedRect(tick, 5, 5)

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
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(14)

        # Header Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        page_title = QLabel("Storage Cleanup & Organization")
        ptf = page_title.font()
        ptf.setPointSize(18)
        ptf.setBold(True)
        page_title.setFont(ptf)

        self._summary = QLabel("Run a scan from the Scan & Folders tab to analyze files.")
        self._summary.setProperty("kind", "muted")
        title_box.addWidget(page_title)
        title_box.addWidget(self._summary)
        lay.addLayout(title_box)

        # Filter Card
        filter_card = Card("panel")
        filt = QHBoxLayout(filter_card)
        filt.setContentsMargins(14, 10, 14, 10)
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

        cat_lbl = QLabel("Category:")
        cat_lbl.setProperty("kind", "muted")
        filt.addWidget(cat_lbl)
        self._category = QComboBox()
        self._category.addItem("All categories")
        self._category.currentIndexChanged.connect(self._refresh)
        filt.addWidget(self._category)

        sort_lbl = QLabel("Sort:")
        sort_lbl.setProperty("kind", "muted")
        filt.addWidget(sort_lbl)
        self._sort = QComboBox()
        self._sort.addItems(list(cleanup_logic.SORTS))
        self._sort.currentIndexChanged.connect(self._refresh)
        filt.addWidget(self._sort)
        lay.addWidget(filter_card)

        # Action Buttons Toolbar
        action_card = Card("panel")
        act = QHBoxLayout(action_card)
        act.setContentsMargins(14, 8, 14, 8)
        act.setSpacing(10)

        tick_safe = PillButton("Tick Safe to Delete", primary=True)
        tick_safe.clicked.connect(self._tick_safe)
        clear = PillButton("Clear Ticks")
        clear.clicked.connect(self._clear_ticks)
        imp = PillButton("Move to Important Vault")
        imp.clicked.connect(self._move_important)
        trash = PillButton("Move to Recycle Bin", danger=True)
        theme.add_glow(trash)
        trash.clicked.connect(self._trash_ticked)

        act.addWidget(tick_safe)
        act.addWidget(clear)
        act.addStretch(1)
        act.addWidget(imp)
        act.addWidget(trash)
        lay.addWidget(action_card)

        # Splitter: List view + Preview panel
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
            self._status.setText("No files ticked for deletion.")
            return
        msg, warning = fileops.trash_confirm_text(files)
        text = msg + (("\n\n" + warning) if warning else "")
        if not dialogs.confirm(self, "Move Files to Recycle Bin", text,
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
            self._status.setText("No files ticked to move.")
            return
        base = self.ctx.settings.vault_dir / "Important"
        if not dialogs.confirm(self, "Move to Important Vault",
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
