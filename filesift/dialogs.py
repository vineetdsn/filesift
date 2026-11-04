"""Frameless modal dialogs built on Card."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QVBoxLayout)

from . import theme
from .widgets import Card, PillButton


class ConfirmDialog(QDialog):
    def __init__(self, title: str, text: str, parent=None, ok_text: str = "OK"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        card = Card("content")
        root.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(14)
        title_lbl = QLabel(title)
        f = title_lbl.font()
        f.setPointSize(13)
        f.setBold(True)
        title_lbl.setFont(f)
        title_lbl.setProperty("kind", "card-text")
        msg = QLabel(text)
        msg.setProperty("kind", "card-text")
        msg.setWordWrap(True)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        row = QHBoxLayout()
        row.addStretch(1)
        cancel = PillButton("Cancel")
        ok = PillButton(ok_text, primary=True)
        cancel.clicked.connect(self.reject)
        ok.clicked.connect(self.accept)
        cancel.setDefault(True)
        cancel.setFocus()
        row.addWidget(cancel)
        row.addWidget(ok)
        lay.addWidget(title_lbl)
        lay.addWidget(msg)
        lay.addLayout(row)
        theme.add_glow(card)
        self.setFixedWidth(420)


class MessageDialog(QDialog):
    def __init__(self, title: str, text: str, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        card = Card("content")
        root.addWidget(card)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 22, 24, 18)
        lay.setSpacing(14)
        title_lbl = QLabel(title)
        f = title_lbl.font()
        f.setPointSize(13)
        f.setBold(True)
        title_lbl.setFont(f)
        title_lbl.setProperty("kind", "card-text")
        msg = QLabel(text)
        msg.setProperty("kind", "card-text")
        msg.setWordWrap(True)
        msg.setTextFormat(Qt.TextFormat.PlainText)
        ok = PillButton("OK", primary=True)
        ok.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(ok)
        lay.addWidget(title_lbl)
        lay.addWidget(msg)
        lay.addLayout(row)
        theme.add_glow(card)
        self.setFixedWidth(420)


def confirm(parent, title: str, text: str, ok_text: str = "OK") -> bool:
    dlg = ConfirmDialog(title, text, parent, ok_text=ok_text)
    return dlg.exec() == QDialog.DialogCode.Accepted


def message(parent, title: str, text: str) -> None:
    dlg = MessageDialog(title, text, parent)
    dlg.exec()
