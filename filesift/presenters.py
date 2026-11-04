"""Pure text/number formatters — no Qt imports."""
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime

from .models import FileInfo, human_size

EM_DASH = "—"


def format_badge(n: int) -> str | None:
    if n <= 0:
        return None
    return str(n) if n <= 999 else "999+"


@dataclass(frozen=True)
class ScanStats:
    files: int
    total_size: int
    groups: int
    reclaimable: int
    safe: int


def scan_stats(result) -> ScanStats:
    return ScanStats(
        files=len(result.files),
        total_size=sum(f.size for f in result.files),
        groups=len(result.groups),
        reclaimable=sum(g.wasted for g in result.groups),
        safe=sum(1 for f in result.files if f.bucket == "delete"),
    )


def stat_texts(stats: ScanStats | None) -> list[str]:
    if stats is None:
        return [EM_DASH] * 5
    return [
        str(stats.files),
        human_size(stats.total_size),
        str(stats.groups),
        human_size(stats.reclaimable),
        str(stats.safe),
    ]


def stage_text(stage: str, done: int, total: int) -> str:
    if total == 0:
        return f"{stage}…"
    return f"{stage}… {done}/{total}"


def done_text(stats: ScanStats) -> str:
    return (f"Done: {stats.files} files ({human_size(stats.total_size)}), "
            f"{stats.groups} duplicate groups.")


def group_header(number: int, g) -> str:
    return f"Group {number} · {g.kind} · {len(g.files)} files · {human_size(g.wasted)} reclaimable"


def duplicates_summary(n_groups: int, reclaimable: int) -> str:
    if n_groups == 0:
        return "No duplicates found."
    return f"{n_groups} duplicate groups · {human_size(reclaimable)} reclaimable"


def marked_text(count: int, size: int) -> str:
    if count == 0:
        return "Nothing marked"
    return f"{count} marked · {human_size(size)}"


def tile_lines(f: FileInfo) -> tuple[str, str, str]:
    res = f"{f.width}×{f.height}" if f.width and f.height else ""
    date_str = datetime.fromtimestamp(f.best_date).strftime("%Y-%m-%d")
    return f.name, human_size(f.size), f"{res}  {date_str}".strip()


def row_subtitle(f: FileInfo, now: float | None = None) -> str:
    now = now or time.time()
    age = f.age_days(now)
    info = f.tags[0] if f.tags else (", ".join(f.reasons[:2]) if f.reasons else "")
    return f"{f.category} · {info} · {age}d · {human_size(f.size)}"


def preview_details(f: FileInfo) -> str:
    lines = [f.path]
    if f.width and f.height:
        lines.append(f"{f.width}×{f.height} px")
    lines.append(human_size(f.size))
    lines.append(datetime.fromtimestamp(f.best_date).strftime("%Y-%m-%d"))
    lines.append(f"Category: {f.category}")
    if f.tags:
        lines.append(f"Tags: {', '.join(f.tags)}")
    if f.reasons:
        lines.append(f"Reasons: {', '.join(f.reasons)}")
    return "\n".join(lines)


def placeholder_label(f: FileInfo) -> str:
    return f.ext.lstrip(".").upper() or "FILE"


def fit_size(w: int, h: int, box_w: int, box_h: int) -> tuple[int, int]:
    if w <= 0 or h <= 0:
        return box_w, box_h
    scale = min(box_w / w, box_h / h, 1.0)
    return max(1, int(w * scale)), max(1, int(h * scale))
