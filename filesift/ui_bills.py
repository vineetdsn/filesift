"""Bill & warranty vault tab."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QComboBox, QDateEdit,
                               QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QFormLayout,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPlainTextEdit,
                               QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from . import bills as B
from . import textextract
from .ui_common import AppContext, confirm

TASK_NAME = "FileSift Reminders"


def _qdate(iso: str) -> QDate:
    d = B.parse_iso(iso)
    return QDate(d.year, d.month, d.day) if d else QDate.currentDate()


def _iso(qd: QDate) -> str:
    return qd.toString("yyyy-MM-dd")


class BillDialog(QDialog):
    def __init__(self, ctx: AppContext, bill: B.Bill | None = None, file_path: str = "",
                 text: str = "", parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.bill = bill or B.Bill(product="")
        self.setWindowTitle("Edit bill" if bill else "Add bill / warranty")
        self.setMinimumWidth(520)

        self.product = QLineEdit(self.bill.product)
        self.category = QComboBox()
        self.category.setEditable(True)
        self.category.addItems(B.CATEGORIES)
        self.category.setCurrentText(self.bill.category or "Other")
        self.store = QLineEdit(self.bill.store)
        self.purchase = QDateEdit(_qdate(self.bill.purchase_date))
        self.purchase.setCalendarPopup(True)
        self.purchase.setDisplayFormat("dd MMM yyyy")
        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 1e9)
        self.amount.setDecimals(2)
        self.amount.setValue(self.bill.amount)
        self.months = QSpinBox()
        self.months.setRange(0, 240)
        self.months.setSuffix(" months")
        self.months.setValue(self.bill.warranty_months)
        self.manual = QCheckBox("Set warranty end date manually")
        self.end = QDateEdit(_qdate(self.bill.warranty_end))
        self.end.setCalendarPopup(True)
        self.end.setDisplayFormat("dd MMM yyyy")
        self.manual.setChecked(bool(self.bill.warranty_end) and not self.bill.warranty_months)
        self.end_label = QLabel()
        self.return_days = QSpinBox()
        self.return_days.setRange(0, 365)
        self.return_days.setSuffix(" days (0 = none)")
        self.return_days.setValue(self.bill.return_days)
        self.serial = QLineEdit(self.bill.serial)
        self.invoice = QLineEdit(self.bill.invoice_no)
        self.notes = QPlainTextEdit(self.bill.notes)
        self.notes.setFixedHeight(60)

        self.file = QLineEdit(self.bill.file_path or file_path)
        browse = QPushButton("Browse...")
        browse.clicked.connect(self._browse)
        fill = QPushButton("Auto-fill from file")
        fill.clicked.connect(self._autofill)
        self.copy = QCheckBox("Copy file into the vault (recommended)")
        self.copy.setChecked(not self.bill.file_path)
        frow = QHBoxLayout()
        frow.addWidget(self.file, 1)
        frow.addWidget(browse)
        frow.addWidget(fill)

        form = QFormLayout()
        form.addRow("Product *", self.product)
        form.addRow("Category", self.category)
        form.addRow("Store / brand", self.store)
        form.addRow("Purchase date", self.purchase)
        form.addRow("Amount", self.amount)
        form.addRow("Warranty", self.months)
        form.addRow("", self.manual)
        form.addRow("Warranty ends", self.end)
        form.addRow("", self.end_label)
        form.addRow("Return window", self.return_days)
        form.addRow("Serial / IMEI", self.serial)
        form.addRow("Invoice no.", self.invoice)
        form.addRow("Notes", self.notes)
        form.addRow("Bill file", frow)
        form.addRow("", self.copy)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(buttons)

        for w in (self.purchase.dateChanged, self.months.valueChanged, self.manual.toggled, self.end.dateChanged):
            w.connect(self._update_end)
        self._update_end()

        if text:
            self._apply_fields(B.extract_bill_fields(text), from_text=True)
        elif file_path and not bill:
            self.product.setText(Path(file_path).stem)

    def _update_end(self, *_args) -> None:
        manual = self.manual.isChecked()
        self.end.setEnabled(manual)
        if manual:
            self.end_label.setText("")
            return
        e = B.compute_warranty_end(_iso(self.purchase.date()), self.months.value())
        self.end_label.setText(f"Calculated end: {e}" if e else "No warranty end (set months or a manual date)")

    def _browse(self) -> None:
        p, _ = QFileDialog.getOpenFileName(self, "Select bill", "", "Bills (*.pdf *.jpg *.jpeg *.png *.webp *.txt);;All files (*)")
        if p:
            self.file.setText(p)

    def _autofill(self) -> None:
        path = self.file.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.information(self, "Auto-fill", "Choose a bill file first.")
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            text = textextract.extract_text(path)
        finally:
            QApplication.restoreOverrideCursor()
        if not text.strip():
            QMessageBox.information(
                self, "Auto-fill",
                "No text could be read.\nInstall Tesseract OCR (for images) or `pip install PyMuPDF` (for PDFs), "
                "or fill the form manually.")
            return
        self._apply_fields(B.extract_bill_fields(text), from_text=True)

    def _apply_fields(self, f: dict, from_text: bool) -> None:
        if not f:
            return
        if "purchase_date" in f:
            self.purchase.setDate(_qdate(f["purchase_date"]))
        if "amount" in f:
            self.amount.setValue(f["amount"])
        if "warranty_months" in f:
            self.months.setValue(f["warranty_months"])
        if f.get("invoice_no") and not self.invoice.text():
            self.invoice.setText(f["invoice_no"])
        if f.get("serial") and not self.serial.text():
            self.serial.setText(f["serial"])
        if f.get("store") and not self.store.text():
            self.store.setText(f["store"])
        if from_text:
            self.notes.setPlainText((self.notes.toPlainText() + "\n" if self.notes.toPlainText() else "")
                                    + "Auto-filled from bill text: please verify the fields.")

    def _save(self) -> None:
        product = self.product.text().strip()
        if not product:
            QMessageBox.warning(self, "Missing product", "Enter the product name.")
            return
        b = self.bill
        b.product, b.category = product, self.category.currentText().strip()
        b.store, b.purchase_date = self.store.text().strip(), _iso(self.purchase.date())
        b.amount, b.warranty_months = self.amount.value(), self.months.value()
        b.return_days, b.serial = self.return_days.value(), self.serial.text().strip()
        b.invoice_no, b.notes = self.invoice.text().strip(), self.notes.toPlainText().strip()
        if self.manual.isChecked():
            b.warranty_end, b.warranty_months = _iso(self.end.date()), 0
        else:
            b.warranty_end = B.compute_warranty_end(b.purchase_date, b.warranty_months)
        path = self.file.text().strip()
        if path and os.path.exists(path):
            vault = self.ctx.settings.vault_dir
            inside = os.path.normcase(os.path.abspath(path)).startswith(os.path.normcase(str(vault)))
            if self.copy.isChecked() and not inside:
                try:
                    path = str(B.copy_to_vault(path, vault, b.category, b.purchase_date, product))
                except OSError as exc:
                    QMessageBox.warning(self, "Copy failed", f"Could not copy into the vault:\n{exc}")
                    return
        b.file_path = path
        B.save_bill(self.ctx.con, b)
        self.accept()


class BillsTab(QWidget):
    COLS = ["Product", "Category", "Store", "Purchased", "Warranty ends", "Days left", "Amount", "Serial", "File"]

    def __init__(self, ctx: AppContext, parent=None):
        super().__init__(parent)
        self.ctx = ctx
        self.bills: list[B.Bill] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search product, store, serial, category...")
        self.search.textChanged.connect(self.refresh)
        self.show_expired = QCheckBox("Show expired")
        self.show_expired.setChecked(True)
        self.show_expired.toggled.connect(self.refresh)
        self.summary = QLabel()

        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(0, 200)
        self.table.cellDoubleClicked.connect(lambda *_: self.edit_bill())

        def btn(text, fn):
            b = QPushButton(text)
            b.clicked.connect(fn)
            return b

        row1 = QHBoxLayout()
        for t, fn in (("Add bill", self.add_bill), ("Edit", self.edit_bill), ("Delete", self.delete_bill),
                      ("Open bill file", self.open_file), ("Show in folder", self.show_in_folder)):
            row1.addWidget(btn(t, fn))
        row1.addStretch(1)
        row2 = QHBoxLayout()
        row2.addWidget(btn("Export reminders (.ics)", self.export_ics))
        row2.addStretch(1)
        row2.addWidget(btn("Enable daily background reminder", self.enable_task))
        row2.addWidget(btn("Disable", self.disable_task))

        top = QHBoxLayout()
        top.addWidget(self.search, 1)
        top.addWidget(self.show_expired)
        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(self.summary)
        lay.addWidget(self.table, 1)
        lay.addLayout(row1)
        lay.addLayout(row2)
        self.reload()

    def reload(self) -> None:
        self.bills = B.list_bills(self.ctx.con)
        self.refresh()

    def refresh(self) -> None:
        q = self.search.text().strip().lower()
        today = date.today()
        rows = []
        for b in self.bills:
            if q and q not in " ".join([b.product, b.store, b.serial, b.category, b.invoice_no]).lower():
                continue
            left = b.days_left(today)
            if not self.show_expired.isChecked() and left is not None and left < 0:
                continue
            rows.append(b)
        self.table.setRowCount(len(rows))
        for r, b in enumerate(rows):
            left = b.days_left(today)
            vals = [b.product, b.category, b.store, b.purchase_date, b.warranty_end or "-",
                    "-" if left is None else ("expired" if left < 0 else str(left)),
                    f"{b.amount:,.0f}" if b.amount else "-", b.serial, Path(b.file_path).name if b.file_path else "-"]
            color = None
            if left is not None:
                color = QColor("#ffb3b3") if left < 0 else QColor("#ffe0a3") if left <= 30 else None
            for c, v in enumerate(vals):
                it = QTableWidgetItem(v)
                if c == 0:
                    it.setData(Qt.ItemDataRole.UserRole, b)
                if color:
                    it.setBackground(QBrush(color))
                    it.setForeground(QBrush(QColor("#000000")))
                self.table.setItem(r, c, it)
        active = sum(1 for b in self.bills if (b.days_left(today) or 0) >= 0 and b.warranty_end)
        soon = sum(1 for b in self.bills if b.warranty_end and 0 <= (b.days_left(today) or 0) <= 30)
        expired = sum(1 for b in self.bills if b.warranty_end and (b.days_left(today) or 0) < 0)
        spend = sum(b.amount for b in self.bills)
        self.summary.setText(f"{len(self.bills)} bills | {active} under warranty | {soon} expiring within 30 days | "
                             f"{expired} expired | total spend {spend:,.0f}")

    def _current(self) -> B.Bill | None:
        r = self.table.currentRow()
        it = self.table.item(r, 0) if r >= 0 else None
        return it.data(Qt.ItemDataRole.UserRole) if it else None

    def open_dialog(self, bill=None, file_path: str = "", text: str = "") -> bool:
        dlg = BillDialog(self.ctx, bill, file_path, text, self)
        ok = dlg.exec() == QDialog.DialogCode.Accepted
        if ok:
            self.reload()
        return ok

    def add_bill(self) -> None:
        self.open_dialog()

    def edit_bill(self) -> None:
        b = self._current()
        if b:
            self.open_dialog(b)

    def delete_bill(self) -> None:
        b = self._current()
        if b and confirm(self, "Delete bill", f"Delete the record for '{b.product}'?\n(The saved bill file is not deleted.)"):
            B.delete_bill(self.ctx.con, b.id)
            self.reload()

    def open_file(self) -> None:
        b = self._current()
        if b and b.file_path and os.path.exists(b.file_path):
            os.startfile(b.file_path)  # noqa: S606 - Windows only
        else:
            QMessageBox.information(self, "Bill file", "No file attached or the file is missing.")

    def show_in_folder(self) -> None:
        b = self._current()
        if b and b.file_path and os.path.exists(b.file_path):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(b.file_path)])

    def export_ics(self) -> None:
        p, _ = QFileDialog.getSaveFileName(self, "Export reminders", "warranty-reminders.ics", "Calendar (*.ics)")
        if p:
            n = B.export_ics(self.bills, p)
            QMessageBox.information(self, "Exported", f"{n} events written.\nImport the .ics into Google Calendar or Outlook "
                                                      "to get reminders on your phone.")

    def enable_task(self) -> None:
        script = Path(__file__).resolve().parents[1] / "run.py"
        exe = Path(sys.executable)
        pyw = exe.with_name("pythonw.exe")
        runner = pyw if pyw.exists() else exe
        cmd = ["schtasks", "/Create", "/TN", TASK_NAME, "/SC", "DAILY", "/ST", "10:00", "/F",
               "/TR", f'"{runner}" "{script}" --reminders']
        self._run_schtasks(cmd, "Daily reminder check scheduled for 10:00.")

    def disable_task(self) -> None:
        self._run_schtasks(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], "Background reminder removed.")

    def _run_schtasks(self, cmd: list[str], ok_msg: str) -> None:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                 creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, "Task Scheduler", str(exc))
            return
        if res.returncode == 0:
            QMessageBox.information(self, "Task Scheduler", ok_msg)
        else:
            QMessageBox.warning(self, "Task Scheduler", (res.stderr or res.stdout).strip())
