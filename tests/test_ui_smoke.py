"""Headless UI smoke test (no windows shown). Run: python tests/test_ui_smoke.py"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from filesift import app as fsapp, store, ui_review, ui_common  # noqa: E402
from filesift.pipeline import ScanOptions, run_scan  # noqa: E402
from test_core import _photo  # noqa: E402


def test_ui_flow():
    qapp = QApplication.instance() or QApplication([])
    tmp = Path(tempfile.mkdtemp())
    try:
        _photo(tmp / "a.jpg", 1)
        shutil.copy(tmp / "a.jpg", tmp / "b.jpg")
        shutil.copy(tmp / "a.jpg", tmp / "c.jpg")
        _photo(tmp / "z.jpg", 9)

        con = store.connect(":memory:")
        ctx = ui_common.AppContext(con, store.Settings(con), store.Cache(con))
        win = fsapp.MainWindow(ctx)
        res = run_scan(ScanOptions([str(tmp)]), ctx.cache)
        win.on_result(res)

        d = win.dups
        assert d.tree.topLevelItemCount() == 1
        d.auto_select()
        assert len(d.checked_files()) == 2

        # ticking every copy must be refused
        top = d.tree.topLevelItem(0)
        for i in range(top.childCount()):
            top.child(i).setCheckState(0, Qt.CheckState.Checked)
        assert len(d.checked_files()) == 2, "last copy must stay unchecked"

        ui_review.confirm = lambda *a, **k: True
        trashed = []
        ui_review.trash_files = lambda paths: (trashed.extend(paths) or paths, [])
        d.delete_selected()
        assert len(trashed) == 2 and d.tree.topLevelItemCount() == 0

        c = win.cleanup
        assert c.table.rowCount() == 4
        win.bills.reload()
        win.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_ui_flow()
    print("UI OK")
