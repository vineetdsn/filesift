"""Headless UI smoke test. Run: python tests/test_ui_smoke.py"""
import os, shutil, sys, tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from PIL import Image
from PySide6.QtWidgets import QApplication

from filesift import store
from filesift.app import MainWindow
from filesift.context import AppContext
from filesift.pipeline import ScanOptions, run_scan
from filesift.selection import ToggleResult


def _photo(path, seed, size=(400, 300), fmt="JPEG"):
    rng = np.random.default_rng(seed)
    base = rng.integers(0, 255, (12, 16, 3), dtype=np.uint8)
    im = Image.fromarray(base).resize(size, Image.Resampling.BICUBIC)
    im.save(path, fmt)


def test_smoke():
    qapp = QApplication.instance() or QApplication([])
    tmp = Path(tempfile.mkdtemp())
    try:
        _photo(tmp / "a.jpg", 1)
        shutil.copy(tmp / "a.jpg", tmp / "b.jpg")
        shutil.copy(tmp / "a.jpg", tmp / "c.jpg")
        _photo(tmp / "z.jpg", 9)

        con = store.connect(":memory:")
        ctx = AppContext(con, store.Settings(con), store.Cache(con))
        win = MainWindow(ctx)

        result = run_scan(ScanOptions([str(tmp)]), ctx.cache)
        win._on_result(result)

        state = win._dup_page._state
        assert state is not None
        assert state.group_count() == 1, f"Expected 1 group, got {state.group_count()}"

        state.auto_select("Highest resolution")
        assert len(state.marked_files()) == 2, f"Expected 2 marked, got {len(state.marked_files())}"

        state.clear()
        g = state.group_at(0)
        paths = [f.path for f in g.files]
        state.toggle(paths[0])
        state.toggle(paths[1])
        result2 = state.toggle(paths[2])
        assert result2 == ToggleResult.REFUSED_LAST
        assert len(state.marked_files()) == 2

        import filesift.fileops as fo
        import filesift.dialogs as dl
        trashed = []
        orig_trash = fo.trash_files
        orig_confirm = dl.confirm
        fo.trash_files = lambda ps: (trashed.extend(ps) or list(ps), [])
        dl.confirm = lambda *a, **k: True
        try:
            win._dup_page._delete()
        finally:
            fo.trash_files = orig_trash
            dl.confirm = orig_confirm

        assert len(trashed) == 2, f"Expected 2 trashed, got {len(trashed)}"
        assert state.group_count() == 0, f"Expected 0 groups, got {state.group_count()}"
        assert win._clean_page._model.rowCount() == 4, f"Expected 4 rows, got {win._clean_page._model.rowCount()}"

        win.close()
        print("SMOKE OK")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    test_smoke()
    print("ALL TESTS PASSED")
