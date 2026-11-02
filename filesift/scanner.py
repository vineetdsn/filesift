"""Folder walking."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable

from .models import IMAGE_EXT, FileInfo

SKIP_DIR_NAMES = {
    "$recycle.bin", "system volume information", "windows", "program files",
    "program files (x86)", "programdata", "appdata", "node_modules", ".git",
    "__pycache__", ".venv", "venv",
}


def _norm(p: str | Path) -> str:
    return os.path.normcase(os.path.abspath(str(p)))


def is_under(path: str, parents: Iterable[str]) -> bool:
    p = _norm(path)
    for parent in parents:
        q = _norm(parent)
        if p == q or p.startswith(q + os.sep):
            return True
    return False


def walk(
    roots: list[str],
    protected_dirs: list[str] | None = None,
    skip_dirs: list[str] | None = None,
    cancel: Callable[[], bool] | None = None,
) -> list[FileInfo]:
    """Return every regular file under roots.

    protected_dirs: scanned but flagged protected (never suggested for deletion).
    skip_dirs: not scanned at all.
    """
    protected = [_norm(p) for p in (protected_dirs or [])]
    skip = [_norm(p) for p in (skip_dirs or [])]
    seen: set[str] = set()
    out: list[FileInfo] = []
    stack = [str(r) for r in roots]
    while stack:
        if cancel and cancel():
            break
        current = stack.pop()
        if is_under(current, skip):
            continue
        try:
            it = os.scandir(current)
        except OSError:
            continue
        with it:
            for entry in it:
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name.lower() in SKIP_DIR_NAMES or entry.name.startswith("."):
                            continue
                        stack.append(entry.path)
                    elif entry.is_file(follow_symlinks=False):
                        key = _norm(entry.path)
                        if key in seen:
                            continue
                        seen.add(key)
                        st = entry.stat()
                        ext = os.path.splitext(entry.name)[1].lower()
                        out.append(
                            FileInfo(
                                path=entry.path,
                                size=st.st_size,
                                mtime=st.st_mtime,
                                ctime=st.st_ctime,
                                ext=ext,
                                is_image=ext in IMAGE_EXT,
                                protected=is_under(entry.path, protected),
                            )
                        )
                except OSError:
                    continue
    return out
