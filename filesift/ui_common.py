"""Shared UI helpers: app context, preview panel, safe delete."""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImageReader, QPixmap
from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget
from send2trash import send2trash

from .models import FileInfo, human_size
from .store import Cache, Settings


@dataclass
class AppContext:
    con: object  # sqlite3.Connection
    settings: Settings
    cache: Cache


def load_thumb(path: str, box: int = 360) -> QPixmap:
    reader = QImageReader(path)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.isValid() and size.width() > 0:
        size.scale(QSize(box, box), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)
    img = reader.read()
    return QPixmap.fromImage(img) if not img.isNull() else QPixmap()


def fmt_date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        self.image = QLabel("Select a file to preview")
        self.image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image.setMinimumSize(300, 300)
        self.image.setStyleSheet("background:#222;color:#aaa;border:1px solid #444;")
        self.info = QLabel()
        self.info.setWordWrap(True)
        self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        lay.addWidget(self.image, 1)
        lay.addWidget(self.info)
        self.setMinimumWidth(320)

    def show_file(self, fi: FileInfo | None) -> None:
        if fi is None:
            self.image.setPixmap(QPixmap())
            self.image.setText("Select a file to preview")
            self.info.setText("")
            return
        pm = load_thumb(fi.path) if fi.is_image else QPixmap()
        if pm.isNull():
            self.image.setPixmap(QPixmap())
            self.image.setText(f"No preview\n{fi.ext or 'file'}")
        else:
            self.image.setPixmap(pm)
        res = f"{fi.width}x{fi.height}  " if fi.width else ""
        extra = f"\nTags: {', '.join(fi.tags)}" if fi.tags else ""
        why = f"\nWhy: {', '.join(fi.reasons)}" if fi.reasons else ""
        self.info.setText(f"{fi.path}\n{res}{human_size(fi.size)}  |  {fmt_date(fi.best_date)}"
                          f"  |  {fi.category}{extra}{why}")


def trash_files(paths: list[str]) -> tuple[list[str], list[str]]:
    """Send files to the Recycle Bin. Returns (deleted, errors)."""
    done, errors = [], []
    for p in paths:
        try:
            send2trash(os.path.normpath(p))
            done.append(p)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{p}: {exc}")
    return done, errors


def move_files(paths: list[str], dest_dir: Path) -> tuple[list[tuple[str, str]], list[str]]:
    moved, errors = [], []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for p in paths:
        try:
            target = dest_dir / Path(p).name
            n = 2
            while target.exists():
                target = dest_dir / f"{Path(p).stem} ({n}){Path(p).suffix}"
                n += 1
            shutil.move(p, target)
            moved.append((p, str(target)))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{p}: {exc}")
    return moved, errors


def confirm(parent, title: str, text: str) -> bool:
    box = QMessageBox(QMessageBox.Icon.Question, title, text,
                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, parent)
    box.setDefaultButton(QMessageBox.StandardButton.No)
    return box.exec() == QMessageBox.StandardButton.Yes


def show_errors(parent, errors: list[str]) -> None:
    if errors:
        QMessageBox.warning(parent, "Some files failed", "\n".join(errors[:15]))
