"""Spatial hash grid for O(1) neighbor lookups."""

from __future__ import annotations

from typing import TypeVar, Protocol

T = TypeVar("T")


class HasPosition(Protocol):
    x: float
    y: float


class SpatialHash[T: HasPosition]:
    """Grid-based spatial index. Objects are bucketed by cell position."""

    def __init__(self, cell_size: float = 8.0):
        self.cell_size = cell_size
        self._buckets: dict[tuple[int, int], list[T]] = {}

    def clear(self) -> None:
        self._buckets.clear()

    def _key(self, x: float, y: float) -> tuple[int, int]:
        return int(x // self.cell_size), int(y // self.cell_size)

    def insert(self, obj: T) -> None:
        key = self._key(obj.x, obj.y)
        bucket = self._buckets.get(key)
        if bucket is None:
            self._buckets[key] = [obj]
        else:
            bucket.append(obj)

    def bulk_insert(self, objects: list[T]) -> None:
        self.clear()
        for obj in objects:
            self.insert(obj)

    def query_radius(self, cx: float, cy: float, radius: float) -> list[T]:
        """Return all objects within radius of (cx, cy)."""
        results: list[T] = []
        r_sq = radius * radius
        min_kx = int((cx - radius) // self.cell_size)
        max_kx = int((cx + radius) // self.cell_size)
        min_ky = int((cy - radius) // self.cell_size)
        max_ky = int((cy + radius) // self.cell_size)

        for kx in range(min_kx, max_kx + 1):
            for ky in range(min_ky, max_ky + 1):
                bucket = self._buckets.get((kx, ky))
                if bucket is None:
                    continue
                for obj in bucket:
                    dx = obj.x - cx
                    dy = obj.y - cy
                    if dx * dx + dy * dy <= r_sq:
                        results.append(obj)
        return results

    def nearest(self, cx: float, cy: float, radius: float,
                exclude: T | None = None) -> T | None:
        """Return nearest object within radius, optionally excluding one."""
        best: T | None = None
        best_dist_sq = radius * radius
        min_kx = int((cx - radius) // self.cell_size)
        max_kx = int((cx + radius) // self.cell_size)
        min_ky = int((cy - radius) // self.cell_size)
        max_ky = int((cy + radius) // self.cell_size)

        for kx in range(min_kx, max_kx + 1):
            for ky in range(min_ky, max_ky + 1):
                bucket = self._buckets.get((kx, ky))
                if bucket is None:
                    continue
                for obj in bucket:
                    if obj is exclude:
                        continue
                    dx = obj.x - cx
                    dy = obj.y - cy
                    d_sq = dx * dx + dy * dy
                    if d_sq < best_dist_sq:
                        best_dist_sq = d_sq
                        best = obj
        return best
