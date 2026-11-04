"""Pure selection state for the Duplicates page — no Qt."""
from __future__ import annotations

from enum import Enum

from .duplicates import pick_keeper
from .models import DupGroup, FileInfo


class ToggleResult(Enum):
    MARKED = "marked"
    UNMARKED = "unmarked"
    REFUSED_LAST = "refused_last"
    REFUSED_PROTECTED = "refused_protected"


LAST_COPY_MSG = "Cannot select every copy in a group: at least one must be kept."


class SelectionState:
    def __init__(self, groups: list[DupGroup]):
        self._groups: list[DupGroup] = list(groups)
        self._marked: set[str] = set()
        self._keepers: set[str] = set()
        self._path_to_gidx: dict[str, int] = {}
        for i, g in enumerate(self._groups):
            for f in g.files:
                self._path_to_gidx[f.path] = i

    def group_count(self) -> int:
        return len(self._groups)

    def groups(self) -> list[DupGroup]:
        return list(self._groups)

    def group_at(self, idx: int) -> DupGroup:
        return self._groups[idx]

    def is_marked(self, path: str) -> bool:
        return path in self._marked

    def is_keeper(self, path: str) -> bool:
        return path in self._keepers

    def _group_of(self, path: str) -> DupGroup | None:
        idx = self._path_to_gidx.get(path)
        return self._groups[idx] if idx is not None else None

    def toggle(self, path: str) -> ToggleResult:
        g = self._group_of(path)
        if g is None:
            return ToggleResult.REFUSED_PROTECTED
        fi = next((f for f in g.files if f.path == path), None)
        if fi is None or fi.protected:
            return ToggleResult.REFUSED_PROTECTED
        if path in self._marked:
            self._marked.discard(path)
            return ToggleResult.UNMARKED
        non_prot = [f for f in g.files if not f.protected]
        currently_unmarked = [f for f in non_prot if f.path not in self._marked]
        if len(currently_unmarked) == 1 and currently_unmarked[0].path == path:
            has_protected = any(f.protected for f in g.files)
            if not has_protected:
                return ToggleResult.REFUSED_LAST
        self._marked.add(path)
        self._keepers.discard(path)
        return ToggleResult.MARKED

    def auto_select(self, rule: str) -> None:
        self._marked.clear()
        self._keepers.clear()
        for g in self._groups:
            keeper = pick_keeper(g, rule)
            self._keepers.add(keeper.path)
            for f in g.files:
                if not f.protected and f.path != keeper.path:
                    self._marked.add(f.path)

    def clear(self) -> None:
        self._marked.clear()
        self._keepers.clear()

    def marked_files(self) -> list[FileInfo]:
        result = []
        for g in self._groups:
            for f in g.files:
                if f.path in self._marked:
                    result.append(f)
        return result

    def marked_size(self) -> int:
        return sum(f.size for f in self.marked_files())

    def remove_files(self, paths: set[str]) -> list[int]:
        self._marked -= paths
        self._keepers -= paths
        for p in paths:
            self._path_to_gidx.pop(p, None)
        removed_indices = []
        new_groups = []
        for i, g in enumerate(self._groups):
            remaining = [f for f in g.files if f.path not in paths]
            if len(remaining) < 2:
                removed_indices.append(i)
            else:
                g.files[:] = remaining
                new_groups.append(g)
        self._groups = new_groups
        self._path_to_gidx = {}
        for i, g in enumerate(self._groups):
            for f in g.files:
                self._path_to_gidx[f.path] = i
        return removed_indices

    def total_reclaimable(self) -> int:
        return sum(g.wasted for g in self._groups)
