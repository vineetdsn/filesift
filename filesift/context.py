"""AppContext: shared state passed to every page."""
from __future__ import annotations

from dataclasses import dataclass

from .store import Cache, Settings


@dataclass
class AppContext:
    con: object
    settings: Settings
    cache: Cache

    def protected_dirs(self) -> list[str]:
        base = [str(self.settings.vault_dir)]
        return base + self.settings.get_list("protected_dirs")
