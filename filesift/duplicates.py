"""Exact (byte-identical) and similar-image duplicate detection."""
from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Callable

from .models import DupGroup, FileInfo
from .store import Cache

Progress = Callable[[str, int, int], None]
CHUNK = 1024 * 1024


def _hash_file(path: str, partial: bool = False) -> str | None:
    h = hashlib.blake2b(digest_size=20)
    try:
        with open(path, "rb") as f:
            if partial:
                h.update(f.read(65536))
            else:
                while chunk := f.read(CHUNK):
                    h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


class _UnionFind:
    def __init__(self, n: int):
        self.p = list(range(n))

    def find(self, x: int) -> int:
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[rb] = ra


def _exact_groups(files: list[FileInfo], cache: Cache | None, progress: Progress | None,
                  cancel: Callable[[], bool] | None) -> list[list[FileInfo]]:
    by_size: dict[int, list[FileInfo]] = defaultdict(list)
    for f in files:
        if f.size > 0:
            by_size[f.size].append(f)
    cands = [g for g in by_size.values() if len(g) > 1]

    # stage 1: partial hash
    total = sum(len(g) for g in cands)
    done = 0
    by_partial: dict[tuple[int, str], list[FileInfo]] = defaultdict(list)
    for g in cands:
        for f in g:
            if cancel and cancel():
                return []
            ph = _hash_file(f.path, partial=True)
            if ph:
                by_partial[(f.size, ph)].append(f)
            done += 1
            if progress and done % 50 == 0:
                progress("Quick hash", done, total)

    # stage 2: full hash (cached)
    cands2 = [g for g in by_partial.values() if len(g) > 1]
    total = sum(len(g) for g in cands2)
    done = 0
    by_sha: dict[str, list[FileInfo]] = defaultdict(list)
    for g in cands2:
        for f in g:
            if cancel and cancel():
                return []
            row = cache.get(f.path, f.size, f.mtime) if cache else None
            sha = row["sha"] if row and row["sha"] else None
            if not sha:
                sha = _hash_file(f.path)
                if sha and cache:
                    cache.put(f.path, f.size, f.mtime, sha=sha)
            if sha:
                f.sha = sha
                by_sha[sha].append(f)
            done += 1
            if progress and done % 10 == 0:
                progress("Full hash", done, total)
    if cache:
        cache.commit()
    return [g for g in by_sha.values() if len(g) > 1]


def _popcount(x: int) -> int:
    return x.bit_count()


def _similar_unions(images: list[FileInfo], uf: _UnionFind, index: dict[int, int],
                    max_distance: int, cancel: Callable[[], bool] | None) -> None:
    """Union images whose dHash hamming distance <= max_distance (banded LSH)."""
    unique: dict[int, list[int]] = defaultdict(list)
    for f in images:
        h = f.dhash
        if h is None or _popcount(h) <= 3 or _popcount(h) >= 61:
            continue  # flat/blank images hash to garbage
        unique[h].append(index[id(f)])
    for idxs in unique.values():
        for i in idxs[1:]:
            uf.union(idxs[0], i)

    hashes = list(unique.keys())
    n_bands = max(1, min(max_distance + 1, 16))
    buckets: list[dict[int, list[int]]] = [defaultdict(list) for _ in range(n_bands)]
    for hi, h in enumerate(hashes):
        for b in range(n_bands):
            lo, hi_bit = b * 64 // n_bands, (b + 1) * 64 // n_bands
            buckets[b][(h >> lo) & ((1 << (hi_bit - lo)) - 1)].append(hi)

    checked: set[tuple[int, int]] = set()
    files_by_idx = {index[id(f)]: f for f in images}
    for bucket in buckets:
        for members in bucket.values():
            if len(members) < 2 or len(members) > 1000:
                continue
            if cancel and cancel():
                return
            for a in range(len(members)):
                for b in range(a + 1, len(members)):
                    pair = (members[a], members[b])
                    if pair in checked:
                        continue
                    checked.add(pair)
                    ha, hb = hashes[pair[0]], hashes[pair[1]]
                    if _popcount(ha ^ hb) > max_distance:
                        continue
                    fa = files_by_idx[unique[ha][0]]
                    fb = files_by_idx[unique[hb][0]]
                    if fa.width and fb.width and fa.height and fb.height:
                        ra, rb = fa.width / fa.height, fb.width / fb.height
                        if abs(ra - rb) > 0.12 * max(ra, rb):
                            continue
                    uf.union(unique[ha][0], unique[hb][0])


def find_duplicates(
    files: list[FileInfo],
    cache: Cache | None = None,
    similar: bool = True,
    max_distance: int = 6,
    progress: Progress | None = None,
    cancel: Callable[[], bool] | None = None,
) -> list[DupGroup]:
    exact = _exact_groups(files, cache, progress, cancel)
    if cancel and cancel():
        return []

    nodes: list[FileInfo] = []
    seen: set[int] = set()
    for g in exact:
        for f in g:
            if id(f) not in seen:
                seen.add(id(f))
                nodes.append(f)
    images: list[FileInfo] = []
    if similar:
        for f in files:
            if f.is_image and f.dhash is not None:
                images.append(f)
                if id(f) not in seen:
                    seen.add(id(f))
                    nodes.append(f)
    index = {id(f): i for i, f in enumerate(nodes)}
    uf = _UnionFind(len(nodes))
    for g in exact:
        for f in g[1:]:
            uf.union(index[id(g[0])], index[id(f)])
    if similar:
        if progress:
            progress("Finding similar images", 0, 0)
        _similar_unions(images, uf, index, max_distance, cancel)

    comps: dict[int, list[FileInfo]] = defaultdict(list)
    for f in nodes:
        comps[uf.find(index[id(f)])].append(f)
    groups: list[DupGroup] = []
    for members in comps.values():
        if len(members) < 2:
            continue
        shas = {m.sha for m in members}
        kind = "exact" if len(shas) == 1 and None not in shas else "similar"
        groups.append(DupGroup(kind, sorted(members, key=lambda m: m.path)))
    groups.sort(key=lambda g: g.wasted, reverse=True)
    return groups


KEEPER_RULES = {
    "Highest resolution": lambda f: (-f.pixels, -f.size, f.best_date),
    "Largest file size": lambda f: (-f.size, f.best_date),
    "Oldest file": lambda f: (f.best_date, -f.size),
    "Newest file": lambda f: (-f.best_date, -f.size),
    "Shortest path": lambda f: (len(f.path), f.best_date),
}


def pick_keeper(group: DupGroup, rule: str) -> FileInfo:
    # protected files always win: they must never be proposed for deletion
    prot = [f for f in group.files if f.protected]
    pool = prot or group.files
    return min(pool, key=KEEPER_RULES[rule])
