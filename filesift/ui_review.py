"""Duplicates tab and Cleanup (old screenshots / junk / important) tab."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QHBoxLayout, QHeaderView, QLabel,
                               QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
                               QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .duplicates import KEEPER_RULES, pick_keeper
from .models import DupGroup, FileInfo, human_size
from .scanner import is_under
from .ui_common import (AppContext, PreviewPanel, confirm, fmt_date, move_files, show_errors,
                        trash_files)

FILE_ROLE = Qt.ItemDataRole.UserRole
GROUP_ROLE = Qt.ItemDataRole.UserRole + 1
MAX_ROWS = 20000


class _SizeItem(QTableWidgetItem):
    """Sorts by raw byte count instead of the '1.2 MB' text."""

    def __lt__(self, other) -> bool:
        return (self.data(Qt.ItemDataRole.UserRole + 2) or 0) < (other.data(Qt.ItemDataRole.UserRole + 2) or 0)


class DuplicatesTab(QWidget):
    changed = Signal()  # files were deleted

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.groups: list[DupGroup] = []
        self._busy = False

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["File", "Size", "Resolution", "Date", "Folder"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tree.setColumnWidth(0, 260)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.currentItemChanged.connect(self._on_current)
        self.preview = PreviewPanel()

        self.rule = QComboBox()
        self.rule.addItems(list(KEEPER_RULES))
        auto = QPushButton("Auto-select duplicates to delete")
        auto.clicked.connect(self.auto_select)
        clear = QPushButton("Clear selection")
        clear.clicked.connect(self.clear_selection)
        self.delete_btn = QPushButton("Move selected to Recycle Bin")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.summary = QLabel("Run a scan first.")
        self.status = QLabel("")

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Keep:"))
        bar.addWidget(self.rule)
        bar.addWidget(auto)
        bar.addWidget(clear)
        bar.addStretch(1)
        bar.addWidget(self.delete_btn)

        split = QSplitter()
        split.addWidget(self.tree)
        split.addWidget(self.preview)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)

        lay = QVBoxLayout(self)
        lay.addWidget(self.summary)
        lay.addLayout(bar)
        lay.addWidget(split, 1)
        lay.addWidget(self.status)

    # ----- data -----
    def load(self, groups: list[DupGroup]) -> None:
        self.groups = groups
        self._busy = True
        self.tree.clear()
        for gi, g in enumerate(groups):
            top = QTreeWidgetItem([f"Group {gi + 1} - {g.kind} - {len(g.files)} files - "
                                   f"{human_size(g.wasted)} reclaimable"])
            top.setData(0, GROUP_ROLE, g)
            top.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tree.addTopLevelItem(top)
            for f in g.files:
                child = QTreeWidgetItem([
                    f.name + ("  (protected)" if f.protected else ""), human_size(f.size),
                    f"{f.width}x{f.height}" if f.width else "-", fmt_date(f.best_date),
                    f.path.rsplit("\\", 1)[0] if "\\" in f.path else f.path])
                child.setData(0, FILE_ROLE, f)
                flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
                if not f.protected:
                    flags |= Qt.ItemFlag.ItemIsUserCheckable
                child.setFlags(flags)
                child.setCheckState(0, Qt.CheckState.Unchecked)
                top.addChild(child)
            top.setExpanded(True)
        self._busy = False
        total = sum(g.wasted for g in groups)
        self.summary.setText(f"{len(groups)} duplicate groups found. Up to {human_size(total)} reclaimable. "
                             "Tick the copies you want to delete, or use auto-select. "
                             "At least one file per group is always kept.")
        self.status.setText("")

    def _children(self, top: QTreeWidgetItem):
        return [top.child(i) for i in range(top.childCount())]

    def _on_current(self, cur, _prev) -> None:
        fi = cur.data(0, FILE_ROLE) if cur else None
        self.preview.show_file(fi)

    def _on_item_changed(self, item: QTreeWidgetItem, _col: int) -> None:
        if self._busy or item.parent() is None:
            return
        kids = self._children(item.parent())
        # protected children are never checked, so they count as "kept" automatically
        if all(k.checkState(0) == Qt.CheckState.Checked for k in kids):
            self._busy = True
            item.setCheckState(0, Qt.CheckState.Unchecked)
            self._busy = False
            self.status.setText("Cannot select every copy in a group: at least one must be kept.")

    # ----- actions -----
    def auto_select(self) -> None:
        rule = self.rule.currentText()
        self._busy = True
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            g: DupGroup = top.data(0, GROUP_ROLE)
            keeper = pick_keeper(g, rule)
            for child in self._children(top):
                f: FileInfo = child.data(0, FILE_ROLE)
                if f.protected:
                    continue
                child.setCheckState(0, Qt.CheckState.Unchecked if f is keeper
                                    else Qt.CheckState.Checked)
        self._busy = False
        self.status.setText(f"Auto-selected using '{rule}'. Review, then move to Recycle Bin.")

    def clear_selection(self) -> None:
        self._busy = True
        for i in range(self.tree.topLevelItemCount()):
            for c in self._children(self.tree.topLevelItem(i)):
                if c.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                    c.setCheckState(0, Qt.CheckState.Unchecked)
        self._busy = False

    def checked_files(self) -> list[FileInfo]:
        out = []
        for i in range(self.tree.topLevelItemCount()):
            for c in self._children(self.tree.topLevelItem(i)):
                if c.checkState(0) == Qt.CheckState.Checked:
                    out.append(c.data(0, FILE_ROLE))
        return out

    def delete_selected(self) -> None:
        files = self.checked_files()
        if not files:
            self.status.setText("Nothing selected.")
            return
        size = sum(f.size for f in files)
        if not confirm(self, "Move to Recycle Bin",
                       f"Move {len(files)} files ({human_size(size)}) to the Recycle Bin?\n"
                       "You can restore them from the Recycle Bin."):
            return
        done, errors = trash_files([f.path for f in files])
        self.ctx.cache.forget(done)
        gone = set(done)
        self._busy = True
        for i in reversed(range(self.tree.topLevelItemCount())):
            top = self.tree.topLevelItem(i)
            for c in self._children(top):
                if c.data(0, FILE_ROLE).path in gone:
                    top.removeChild(c)
            if top.childCount() < 2:
                self.tree.takeTopLevelItem(i)
        self._busy = False
        freed = sum(f.size for f in files if f.path in gone)
        self.status.setText(f"Moved {len(done)} files to the Recycle Bin, freed {human_size(freed)}.")
        show_errors(self, errors)
        self.changed.emit()


class CleanupTab(QWidget):
    changed = Signal()
    add_bill = Signal(str, str)  # path, extracted text

    COLS = ["", "File", "Category", "Why", "Age (days)", "Size", "Score", "Verdict"]
    BUCKET_LABEL = {"delete": "Safe to delete", "review": "Review", "keep": "Keep"}

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.files: list[FileInfo] = []
        self._busy = False

        self.bucket = QComboBox()
        self.bucket.addItems(["All", "Safe to delete", "Review", "Keep", "Important (tagged)"])
        self.category = QComboBox()
        self.category.addItem("All categories")
        self.bucket.currentIndexChanged.connect(self.refresh)
        self.category.currentIndexChanged.connect(self.refresh)

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 28)
        self.table.setColumnWidth(1, 240)
        self.table.setColumnWidth(3, 260)
        self.table.currentCellChanged.connect(self._on_current)
        self.preview = PreviewPanel()

        sel_del = QPushButton("Tick all 'Safe to delete'")
        sel_del.clicked.connect(self.tick_safe)
        clear = QPushButton("Clear ticks")
        clear.clicked.connect(self.clear_ticks)
        trash = QPushButton("Move ticked to Recycle Bin")
        trash.clicked.connect(self.trash_ticked)
        imp = QPushButton("Move ticked to Important folder")
        imp.clicked.connect(self.move_important)
        bill = QPushButton("Add selected as bill...")
        bill.clicked.connect(self.emit_bill)

        top = QHBoxLayout()
        top.addWidget(QLabel("Show:"))
        top.addWidget(self.bucket)
        top.addWidget(self.category)
        top.addStretch(1)
        top.addWidget(sel_del)
        top.addWidget(clear)
        bottom = QHBoxLayout()
        bottom.addWidget(bill)
        bottom.addStretch(1)
        bottom.addWidget(imp)
        bottom.addWidget(trash)

        split = QSplitter()
        split.addWidget(self.table)
        split.addWidget(self.preview)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)

        self.summary = QLabel("Run a scan first.")
        self.status = QLabel("")
        lay = QVBoxLayout(self)
        lay.addWidget(self.summary)
        lay.addLayout(top)
        lay.addWidget(split, 1)
        lay.addLayout(bottom)
        lay.addWidget(self.status)

    def load(self, files: list[FileInfo]) -> None:
        self.files = files
        cats = sorted({f.category for f in files})
        self._busy = True
        self.category.clear()
        self.category.addItem("All categories")
        self.category.addItems(cats)
        self._busy = False
        n = {b: sum(1 for f in files if f.bucket == b) for b in ("delete", "review", "keep")}
        imp = sum(1 for f in files if f.tags)
        sz = sum(f.size for f in files if f.bucket == "delete")
        self.summary.setText(
            f"{len(files)} files scanned: {n['delete']} safe to delete ({human_size(sz)}), "
            f"{n['review']} to review, {n['keep']} to keep, {imp} tagged important. "
            "Nothing is deleted until you confirm.")
        self.refresh()

    def _visible(self) -> list[FileInfo]:
        b = self.bucket.currentIndex()
        cat = self.category.currentText()
        out = []
        for f in self.files:
            if b == 1 and f.bucket != "delete":
                continue
            if b == 2 and f.bucket != "review":
                continue
            if b == 3 and f.bucket != "keep":
                continue
            if b == 4 and not f.tags:
                continue
            if self.category.currentIndex() > 0 and f.category != cat:
                continue
            out.append(f)
        out.sort(key=lambda f: (-f.score, f.best_date))
        return out

    def refresh(self) -> None:
        if self._busy:
            return
        rows = self._visible()
        shown = rows[:MAX_ROWS]
        self._busy = True
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(shown))
        for r, f in enumerate(shown):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsSelectable)
            chk.setCheckState(Qt.CheckState.Unchecked)
            chk.setData(FILE_ROLE, f)
            name = QTableWidgetItem(f.name)
            name.setToolTip(f.path)
            why = ", ".join(f.reasons)
            if f.tags:
                why = "important: " + ", ".join(f.tags)
            age = QTableWidgetItem()
            age.setData(Qt.ItemDataRole.DisplayRole, f.age_days())
            size = _SizeItem(human_size(f.size))
            size.setData(Qt.ItemDataRole.UserRole + 2, f.size)
            score = QTableWidgetItem()
            score.setData(Qt.ItemDataRole.DisplayRole, f.score)
            verdict = QTableWidgetItem(self.BUCKET_LABEL[f.bucket] + (" (protected)" if f.protected else ""))
            for c, it in enumerate([chk, name, QTableWidgetItem(f.category), QTableWidgetItem(why),
                                    age, size, score, verdict]):
                self.table.setItem(r, c, it)
        self.table.setSortingEnabled(True)
        self._busy = False
        extra = f" (showing first {MAX_ROWS})" if len(rows) > MAX_ROWS else ""
        self.status.setText(f"{len(rows)} files match{extra}.")

    def _file_at(self, row: int) -> FileInfo | None:
        it = self.table.item(row, 0)
        return it.data(FILE_ROLE) if it else None

    def _on_current(self, row, _c, _pr, _pc) -> None:
        self.preview.show_file(self._file_at(row) if row >= 0 else None)

    def _ticked(self) -> list[FileInfo]:
        out = []
        for r in range(self.table.rowCount()):
            it = self.table.item(r, 0)
            if it and it.checkState() == Qt.CheckState.Checked:
                out.append(it.data(FILE_ROLE))
        return out

    def tick_safe(self) -> None:
        for r in range(self.table.rowCount()):
            f = self._file_at(r)
            if f and f.bucket == "delete" and not f.protected:
                self.table.item(r, 0).setCheckState(Qt.CheckState.Checked)

    def clear_ticks(self) -> None:
        for r in range(self.table.rowCount()):
            self.table.item(r, 0).setCheckState(Qt.CheckState.Unchecked)

    def _forget(self, paths: set[str]) -> None:
        self.files = [f for f in self.files if f.path not in paths]
        self.ctx.cache.forget(list(paths))
        self.load(self.files)
        self.changed.emit()

    def trash_ticked(self) -> None:
        files = [f for f in self._ticked() if not f.protected]
        if not files:
            self.status.setText("Nothing ticked.")
            return
        warn = sum(1 for f in files if f.bucket == "keep" or f.tags)
        extra = f"\n\nWARNING: {warn} of them are marked Keep/Important." if warn else ""
        if not confirm(self, "Move to Recycle Bin",
                       f"Move {len(files)} files ({human_size(sum(f.size for f in files))}) "
                       f"to the Recycle Bin?{extra}"):
            return
        done, errors = trash_files([f.path for f in files])
        self._forget(set(done))
        self.status.setText(f"Moved {len(done)} files to the Recycle Bin.")
        show_errors(self, errors)

    def move_important(self) -> None:
        files = [f for f in self._ticked() if not f.protected]
        if not files:
            self.status.setText("Nothing ticked.")
            return
        base = self.ctx.settings.vault_dir / "Important"
        if not confirm(self, "Move to Important folder",
                       f"Move {len(files)} files into\n{base}\\<category> ?"):
            return
        moved_all, errors = [], []
        groups: dict[str, list[str]] = {}
        for f in files:
            groups.setdefault(f.tags[0] if f.tags else f.category.capitalize(), []).append(f.path)
        for sub, paths in groups.items():
            m, e = move_files(paths, base / sub)
            moved_all += m
            errors += e
        self._forget({src for src, _ in moved_all})
        self.status.setText(f"Moved {len(moved_all)} files into {base}.")
        show_errors(self, errors)

    def emit_bill(self) -> None:
        row = self.table.currentRow()
        f = self._file_at(row) if row >= 0 else None
        if f is None:
            self.status.setText("Select a row first.")
            return
        self.add_bill.emit(f.path, f.text)


def protected_dirs_for(ctx: AppContext) -> list[str]:
    return [str(ctx.settings.vault_dir)] + ctx.settings.get_list("protected_dirs")


__all__ = ["DuplicatesTab", "CleanupTab", "protected_dirs_for", "is_under"]
