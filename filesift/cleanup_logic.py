"""Pure cleanup filtering, sorting and tick management — no Qt."""
from __future__ import annotations

from dataclasses import dataclass

from .models import FileInfo, human_size

MAX_ROWS = 20000
VERDICT_FILTERS = ("All", "Safe to delete", "Review", "Keep", "Important")
BUCKET_FOR = {"Safe to delete": "delete", "Review": "review", "Keep": "keep"}
VERDICT_LABEL = {"delete": "Safe to delete", "review": "Review", "keep": "Keep"}
SORTS = ("Score", "Oldest first", "Largest first")


def matches(f: FileInfo, verdict: str, category: str) -> bool:
    if verdict == "Safe to delete" and f.bucket != "delete":
        return False
    if verdict == "Review" and f.bucket != "review":
        return False
    if verdict == "Keep" and f.bucket != "keep":
        return False
    if verdict == "Important" and not f.tags:
        return False
    if category and category != "All categories" and f.category != category:
        return False
    return True


def categories(files: list[FileInfo]) -> list[str]:
    return sorted({f.category for f in files})


def sort_key(sort: str):
    if sort == "Oldest first":
        return lambda f: (f.best_date, f.path)
    if sort == "Largest first":
        return lambda f: (-f.size, f.path)
    return lambda f: (-f.score, f.best_date, f.path)


def filter_and_sort(files: list[FileInfo], verdict: str, category: str, sort: str) -> list[FileInfo]:
    return sorted([f for f in files if matches(f, verdict, category)], key=sort_key(sort))


def match_status(total: int) -> str:
    if total > MAX_ROWS:
        return f"{total} files match (showing first {MAX_ROWS})."
    return f"{total} files match."


@dataclass
class CleanupSummary:
    total: int
    delete: int
    review: int
    keep: int
    delete_size: int
    important: int


def summarize(files: list[FileInfo]) -> CleanupSummary:
    return CleanupSummary(
        total=len(files),
        delete=sum(1 for f in files if f.bucket == "delete"),
        review=sum(1 for f in files if f.bucket == "review"),
        keep=sum(1 for f in files if f.bucket == "keep"),
        delete_size=sum(f.size for f in files if f.bucket == "delete"),
        important=sum(1 for f in files if f.tags),
    )


def summary_text(s: CleanupSummary) -> str:
    return (
        f"{s.total} files scanned: "
        f"{s.delete} safe to delete ({human_size(s.delete_size)}), "
        f"{s.review} to review, {s.keep} to keep, "
        f"{s.important} tagged important. "
        "Nothing is deleted until you confirm."
    )


def without_paths(files: list[FileInfo], paths: set[str]) -> list[FileInfo]:
    return [f for f in files if f.path not in paths]


class TickSet:
    def __init__(self):
        self._ticked: set[str] = set()

    def toggle(self, f: FileInfo) -> bool:
        if f.protected:
            return False
        if f.path in self._ticked:
            self._ticked.discard(f.path)
        else:
            self._ticked.add(f.path)
        return True

    def tick_all_safe(self, visible: list[FileInfo]) -> None:
        for f in visible:
            if not f.protected and f.bucket == "delete":
                self._ticked.add(f.path)

    def clear(self) -> None:
        self._ticked.clear()

    def is_ticked(self, path: str) -> bool:
        return path in self._ticked

    def actionable(self, visible: list[FileInfo]) -> list[FileInfo]:
        return [f for f in visible if f.path in self._ticked and not f.protected]

    def discard(self, paths: set[str]) -> None:
        self._ticked -= paths
