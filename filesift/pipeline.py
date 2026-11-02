"""End-to-end scan: walk -> features -> duplicates -> text -> classify."""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable

from . import textextract
from .classify import classify, needs_text
from .duplicates import find_duplicates
from .features import analyze_image, apply_features
from .models import DupGroup, FileInfo
from .scanner import walk
from .store import Cache

Progress = Callable[[str, int, int], None]


@dataclass
class ScanOptions:
    roots: list[str]
    protected_dirs: list[str] = field(default_factory=list)
    skip_dirs: list[str] = field(default_factory=list)
    similar: bool = True
    max_distance: int = 6
    use_text: bool = False  # OCR / PDF text (slower)


@dataclass
class ScanResult:
    files: list[FileInfo]
    groups: list[DupGroup]


def run_scan(opts: ScanOptions, cache: Cache, progress: Progress | None = None,
             cancel: Callable[[], bool] | None = None) -> ScanResult:
    def prog(stage: str, done: int, total: int) -> None:
        if progress:
            progress(stage, done, total)

    def cancelled() -> bool:
        return bool(cancel and cancel())

    prog("Listing files", 0, 0)
    files = walk(opts.roots, opts.protected_dirs, opts.skip_dirs, cancel)
    if cancelled():
        return ScanResult([], [])

    # --- image features (cached) ---
    images = [f for f in files if f.is_image]
    todo: list[FileInfo] = []
    for f in images:
        row = cache.get(f.path, f.size, f.mtime)
        if row and row["feat"]:
            apply_features(f, json.loads(row["feat"]))
        else:
            todo.append(f)
    done = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f, feat in zip(todo, pool.map(lambda x: analyze_image(x.path), todo)):
            apply_features(f, feat)
            cache.put(f.path, f.size, f.mtime, feat=feat)
            done += 1
            if done % 25 == 0:
                prog("Reading images", done, len(todo))
                if cancelled():
                    break
    cache.commit()
    if cancelled():
        return ScanResult([], [])

    # --- duplicates ---
    groups = find_duplicates(files, cache, opts.similar, opts.max_distance, prog, cancel)
    if cancelled():
        return ScanResult([], [])

    # --- text (OCR / PDF) ---
    if opts.use_text:
        ocr_ok, pdf_ok = textextract.ocr_available(), textextract.has_pdf_support()
        targets = [f for f in files if needs_text(f)
                   and ((f.ext == ".pdf" and pdf_ok) or (f.is_image and ocr_ok))]
        pending: list[FileInfo] = []
        for f in targets:
            row = cache.get(f.path, f.size, f.mtime)
            if row and row["text"] is not None:
                f.text, f.text_checked = row["text"], True
            else:
                pending.append(f)
        done = 0
        with ThreadPoolExecutor(max_workers=3) as pool:
            for f, txt in zip(pending, pool.map(lambda x: textextract.extract_text(x.path), pending)):
                f.text, f.text_checked = txt, True
                cache.put(f.path, f.size, f.mtime, text=txt)
                done += 1
                if done % 5 == 0:
                    prog("Reading text (OCR)", done, len(pending))
                    if cancelled():
                        break
        cache.commit()

    # --- classify ---
    now = time.time()
    for f in files:
        classify(f, now)
    return ScanResult(files, groups)
