"""Territory map — tracks which species controls which areas.

Each grid cell stores the ID of the claiming species and a claim strength.
When an organism feeds in a cell, it reinforces its species' claim there.
Claims decay over time, creating dynamic territory boundaries.

Territorial effects:
  - Organisms in their own territory get a combat bonus (+20% power)
  - Organisms with moderate aggression chase intruders in their territory
"""

from __future__ import annotations


class TerritoryMap:
    """Grid of territory claims per species."""

    def __init__(self, width: int, height: int, cell_size: float = 2.0,
                 decay: float = 0.95):
        self.world_width = width
        self.world_height = height
        self.cell_size = cell_size
        self.decay = decay

        self.cols = max(1, int(width / cell_size))
        self.rows = max(1, int(height / cell_size))
        size = self.rows * self.cols

        # per-cell: species_id that owns it (0 = unclaimed)
        self._owner: list[int] = [0] * size
        # per-cell: claim strength (0.0 = unclaimed)
        self._strength: list[float] = [0.0] * size

    def _idx(self, wx: float, wy: float) -> int:
        col = max(0, min(int(wx / self.cell_size), self.cols - 1))
        row = max(0, min(int(wy / self.cell_size), self.rows - 1))
        return row * self.cols + col

    def claim(self, wx: float, wy: float, species_id: int, amount: float = 0.5) -> None:
        """Reinforce a species' claim on a cell. If another species owns it, weaken first."""
        if species_id == 0:
            return
        idx = self._idx(wx, wy)
        owner = self._owner[idx]

        if owner == species_id or owner == 0:
            # reinforce own territory
            self._owner[idx] = species_id
            self._strength[idx] = min(1.0, self._strength[idx] + amount)
        else:
            # contest — weaken existing claim
            self._strength[idx] -= amount * 0.7
            if self._strength[idx] <= 0:
                # territory flips
                self._owner[idx] = species_id
                self._strength[idx] = amount * 0.3

    def get_owner(self, wx: float, wy: float) -> int:
        """Return species_id of the territory owner at this position (0 = unclaimed)."""
        idx = self._idx(wx, wy)
        return self._owner[idx]

    def get_strength(self, wx: float, wy: float) -> float:
        """Return claim strength at this position."""
        idx = self._idx(wx, wy)
        return self._strength[idx]

    def is_home(self, wx: float, wy: float, species_id: int) -> bool:
        """Check if a position is in a species' territory."""
        if species_id == 0:
            return False
        idx = self._idx(wx, wy)
        return self._owner[idx] == species_id and self._strength[idx] > 0.2

    def tick(self) -> None:
        """Decay all territory claims."""
        for i in range(len(self._strength)):
            self._strength[i] *= self.decay
            if self._strength[i] < 0.01:
                self._strength[i] = 0.0
                self._owner[i] = 0

    def get_territory_map(self, threshold: float = 0.1) -> list[tuple[int, int, int, float]]:
        """Return list of (col, row, species_id, strength) for claimed cells.

        Used for export/rendering.
        """
        result: list[tuple[int, int, int, float]] = []
        for r in range(self.rows):
            row_off = r * self.cols
            for c in range(self.cols):
                idx = row_off + c
                if self._strength[idx] >= threshold and self._owner[idx] != 0:
                    result.append((c, r, self._owner[idx], round(self._strength[idx], 2)))
        return result
