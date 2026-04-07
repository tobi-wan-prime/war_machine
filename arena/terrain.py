"""Terrain system — walls and zones that shape the arena."""

from __future__ import annotations

import random
import math
from dataclasses import dataclass
from enum import Enum, auto


class TileType(Enum):
    OPEN = auto()       # normal passable terrain
    WALL = auto()       # impassable
    FERTILE = auto()    # 2x food spawn chance
    TOXIC = auto()      # drains energy (mitigated by efficiency)
    HOT = auto()        # drains energy from slow organisms, benefits fast ones
    COLD = auto()       # drains energy from small organisms, benefits large ones


@dataclass(slots=True)
class Terrain:
    """Grid-based terrain map for the arena."""
    width: int
    height: int
    tiles: list[list[TileType]]

    @classmethod
    def empty(cls, width: int, height: int) -> Terrain:
        tiles = [[TileType.OPEN for _ in range(width)] for _ in range(height)]
        return cls(width=width, height=height, tiles=tiles)

    @classmethod
    def generate(cls, width: int, height: int, seed: int | None = None) -> Terrain:
        """Generate interesting terrain with walls, fertile zones, and toxic areas."""
        if seed is not None:
            random.seed(seed)

        terrain = cls.empty(width, height)

        # create 2-4 wall segments (barriers that divide the arena)
        num_walls = random.randint(2, 4)
        for _ in range(num_walls):
            terrain._add_wall_segment()

        # create 1-3 fertile zones (circles of extra food)
        num_fertile = random.randint(1, 3)
        for _ in range(num_fertile):
            cx = random.randint(5, width - 5)
            cy = random.randint(5, height - 5)
            r = random.randint(3, 7)
            terrain._add_circle(cx, cy, r, TileType.FERTILE)

        # create 0-2 toxic zones
        num_toxic = random.randint(0, 2)
        for _ in range(num_toxic):
            cx = random.randint(5, width - 5)
            cy = random.randint(5, height - 5)
            r = random.randint(2, 4)
            terrain._add_circle(cx, cy, r, TileType.TOXIC)

        # create 0-2 hot zones
        num_hot = random.randint(0, 2)
        for _ in range(num_hot):
            cx = random.randint(5, width - 5)
            cy = random.randint(5, height - 5)
            r = random.randint(3, 6)
            terrain._add_circle(cx, cy, r, TileType.HOT)

        # create 0-2 cold zones
        num_cold = random.randint(0, 2)
        for _ in range(num_cold):
            cx = random.randint(5, width - 5)
            cy = random.randint(5, height - 5)
            r = random.randint(3, 6)
            terrain._add_circle(cx, cy, r, TileType.COLD)

        # ensure borders are open (prevent wrapping into walls)
        for x in range(width):
            terrain.tiles[0][x] = TileType.OPEN
            terrain.tiles[height - 1][x] = TileType.OPEN
        for y in range(height):
            terrain.tiles[y][0] = TileType.OPEN
            terrain.tiles[y][width - 1] = TileType.OPEN

        return terrain

    def _add_wall_segment(self) -> None:
        """Add a wall segment — either horizontal or vertical, with gaps."""
        if random.random() < 0.5:
            # horizontal wall
            y = random.randint(5, self.height - 5)
            x_start = random.randint(3, self.width // 3)
            x_end = random.randint(2 * self.width // 3, self.width - 3)
            gap_pos = random.randint(x_start + 3, x_end - 3)
            gap_size = random.randint(3, 6)
            for x in range(x_start, x_end):
                if abs(x - gap_pos) > gap_size // 2:
                    self.tiles[y][x] = TileType.WALL
                    if y + 1 < self.height:
                        self.tiles[y + 1][x] = TileType.WALL
        else:
            # vertical wall
            x = random.randint(5, self.width - 5)
            y_start = random.randint(3, self.height // 3)
            y_end = random.randint(2 * self.height // 3, self.height - 3)
            gap_pos = random.randint(y_start + 3, y_end - 3)
            gap_size = random.randint(3, 6)
            for y in range(y_start, y_end):
                if abs(y - gap_pos) > gap_size // 2:
                    self.tiles[y][x] = TileType.WALL
                    if x + 1 < self.width:
                        self.tiles[y][x + 1] = TileType.WALL

    def _add_circle(self, cx: int, cy: int, radius: int, tile_type: TileType) -> None:
        for y in range(max(1, cy - radius), min(self.height - 1, cy + radius + 1)):
            for x in range(max(1, cx - radius), min(self.width - 1, cx + radius + 1)):
                if math.hypot(x - cx, y - cy) <= radius:
                    if self.tiles[y][x] == TileType.OPEN:
                        self.tiles[y][x] = tile_type

    def get(self, x: float, y: float) -> TileType:
        ix = int(x) % self.width
        iy = int(y) % self.height
        return self.tiles[iy][ix]

    def is_passable(self, x: float, y: float) -> bool:
        return self.get(x, y) != TileType.WALL

    def is_fertile(self, x: float, y: float) -> bool:
        return self.get(x, y) == TileType.FERTILE

    def is_toxic(self, x: float, y: float) -> bool:
        return self.get(x, y) == TileType.TOXIC

    def is_hot(self, x: float, y: float) -> bool:
        return self.get(x, y) == TileType.HOT

    def is_cold(self, x: float, y: float) -> bool:
        return self.get(x, y) == TileType.COLD

    def get_fertile_positions(self) -> list[tuple[int, int]]:
        """Return all fertile tile positions."""
        positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TileType.FERTILE:
                    positions.append((x, y))
        return positions

    def to_lists(self) -> list[list[int]]:
        """Export terrain as integer grid for JSON serialization."""
        return [[t.value for t in row] for row in self.tiles]
