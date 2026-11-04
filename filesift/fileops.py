"""Pure file operations — no Qt."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from send2trash import send2trash

from .models import FileInfo, human_size


def unique_target(dest_dir: Path, name: str) -> Path:
    stem = Path(name).stem
    suffix = Path(name).suffix
    target = dest_dir / name
    n = 2
    while target.exists():
        target = dest_dir / f"{stem} ({n}){suffix}"
        n += 1
    return target


def trash_files(paths: list[str]) -> tuple[list[str], list[str]]:
    done, errors = [], []
    for p in paths:
        try:
            send2trash(os.path.normpath(p))
            done.append(p)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{Path(p).name}: {exc}")
    return done, errors


def move_files(paths: list[str], dest_dir: Path) -> tuple[list[tuple[str, str]], list[str]]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    moved, errors = [], []
    for p in paths:
        try:
            target = unique_target(dest_dir, Path(p).name)
            shutil.move(p, target)
            moved.append((p, str(target)))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{Path(p).name}: {exc}")
    return moved, errors


def important_destination(f: FileInfo, vault: Path) -> Path:
    sub = f.tags[0] if f.tags else f.category.capitalize()
    return vault / sub


def trash_confirm_text(files: list[FileInfo]) -> tuple[str, str | None]:
    total = sum(f.size for f in files)
    warn_count = sum(1 for f in files if f.bucket == "keep" or f.tags)
    msg = (f"Move {len(files)} file{'s' if len(files) != 1 else ''} "
           f"({human_size(total)}) to the Recycle Bin?\n"
           "You can restore them from the Recycle Bin.")
    warning = (f"{warn_count} file{'s are' if warn_count != 1 else ' is'} "
               f"marked Keep or Important." if warn_count else None)
    return msg, warning


def move_confirm_text(files: list[FileInfo], dest: Path) -> str:
    return (f"Move {len(files)} file{'s' if len(files) != 1 else ''} "
            f"into\n{dest}?")


def error_dialog_text(errors: list[str]) -> str:
    shown = errors[:15]
    text = "\n".join(shown)
    if len(errors) > 15:
        text += f"\n…and {len(errors) - 15} more errors."
    return text
