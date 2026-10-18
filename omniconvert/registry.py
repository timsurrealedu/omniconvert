"""Converter registry and the routing graph built from it."""

from __future__ import annotations

import heapq
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

# convert(src, dst, src_fmt, dst_fmt, options) -> list of files written
ConvertFn = Callable[[Path, Path, str, str, dict], list[Path]]

ALIASES = {
    "jpeg": "jpg",
    "tif": "tiff",
    "htm": "html",
    "markdown": "md",
    "text": "txt",
    "tex": "latex",
}


def normalize(fmt: str) -> str:
    fmt = fmt.lower().lstrip(".")
    return ALIASES.get(fmt, fmt)


def detect(path: Path) -> str:
    if not path.suffix:
        raise ValueError(f"Cannot detect format of '{path}' (no extension)")
    return normalize(path.suffix)


@dataclass(frozen=True)
class Converter:
    name: str
    pairs: frozenset[tuple[str, str]]
    func: ConvertFn
    cost: int
    available: Callable[[], bool]
    hint: str
    # False: only usable as a one-step route (stops nonsense like docx -> png -> gif -> mp4).
    chainable: bool = True


CONVERTERS: list[Converter] = []


def pairs(sources: Iterable[str], targets: Iterable[str]) -> set[tuple[str, str]]:
    return {(s, t) for s, t in itertools.product(sources, targets) if s != t}


def register(
    name: str,
    edges: set[tuple[str, str]],
    cost: int = 1,
    available: Callable[[], bool] = lambda: True,
    hint: str = "",
    chainable: bool = True,
) -> Callable[[ConvertFn], ConvertFn]:
    def deco(func: ConvertFn) -> ConvertFn:
        CONVERTERS.append(Converter(name, frozenset(edges), func, cost, available, hint, chainable))
        return func

    return deco


Step = tuple[Converter, str, str]


def plan(src: str, dst: str, include_unavailable: bool = False) -> list[Step] | None:
    """Cheapest chain of converters from src to dst (Dijkstra over formats)."""
    usable = [c for c in CONVERTERS if include_unavailable or c.available()]
    tie = itertools.count()
    queue: list = [(0, next(tie), src, [])]
    seen: set[str] = set()
    while queue:
        cost, _, fmt, route = heapq.heappop(queue)
        if fmt == dst:
            return route
        if fmt in seen:
            continue
        seen.add(fmt)
        for conv in usable:
            for s, t in conv.pairs:
                if not conv.chainable and (route or t != dst):
                    continue
                if s == fmt and t not in seen:
                    heapq.heappush(queue, (cost + conv.cost, next(tie), t, route + [(conv, s, t)]))
    return None


def all_formats() -> set[str]:
    return {f for c in CONVERTERS for pair in c.pairs for f in pair}


def reachable(src: str) -> set[str]:
    return {f for f in all_formats() if f != src and plan(src, f)}
