from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tif", ".tiff", ".heic", ".heif"}


@dataclass
class FileInfo:
    path: str
    size: int
    mtime: float
    ctime: float
    ext: str
    is_image: bool
    width: int = 0
    height: int = 0
    fmt: str = ""
    camera: bool = False
    gps: bool = False
    taken: float | None = None
    dhash: int | None = None
    blur: float | None = None
    sha: str | None = None
    category: str = "other"
    tags: list[str] = field(default_factory=list)
    text: str = ""
    text_checked: bool = False
    score: int = 0
    bucket: str = "keep"  # delete | review | keep
    reasons: list[str] = field(default_factory=list)
    protected: bool = False

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def best_date(self) -> float:
        if self.taken:
            return self.taken
        return min(self.mtime, self.ctime) if self.ctime else self.mtime

    def age_days(self, now: float | None = None) -> int:
        now = now or time.time()
        return max(0, int((now - self.best_date) / 86400))

    @property
    def pixels(self) -> int:
        return self.width * self.height


@dataclass
class DupGroup:
    kind: str  # exact | similar
    files: list[FileInfo]

    @property
    def wasted(self) -> int:
        """Bytes that would be freed if only the biggest file were kept."""
        sizes = sorted(f.size for f in self.files)
        return sum(sizes[:-1])


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n} B"
