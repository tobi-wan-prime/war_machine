"""Pheromone trail system — chemical signals left by organisms.

Two channels:
  FOOD  — deposited when an organism eats. Guides foragers toward food-rich areas.
  DANGER — deposited when an organism dies or is attacked. Warns prey away.

The map operates at a coarser resolution than the world grid (cell_size world-units
per pheromone cell) for performance. Each tick, values decay and diffuse to neighbors.
"""

from __future__ import annotations


class PheromoneMap:
    """Grid of pheromone intensities with decay and diffusion."""

    # Channel indices
    FOOD = 0
    DANGER = 1
    _N_CHANNELS = 2

    def __init__(self, width: int, height: int, cell_size: float = 2.0,
                 decay: float = 0.92, diffusion: float = 0.12):
        self.world_width = width
        self.world_height = height
        self.cell_size = cell_size
        self.decay = decay
        self.diffusion = diffusion

        self.cols = max(1, int(width / cell_size))
        self.rows = max(1, int(height / cell_size))

        # flat arrays: [channel][row * cols + col]
        size = self.rows * self.cols
        self._grid: list[list[float]] = [
            [0.0] * size for _ in range(self._N_CHANNELS)
        ]
        self._scratch: list[list[float]] = [
            [0.0] * size for _ in range(self._N_CHANNELS)
        ]

    def _idx(self, wx: float, wy: float) -> int:
        """Convert world coordinates to flat index."""
        col = min(int(wx / self.cell_size), self.cols - 1)
        row = min(int(wy / self.cell_size), self.rows - 1)
        if col < 0:
            col = 0
        if row < 0:
            row = 0
        return row * self.cols + col

    def deposit(self, channel: int, wx: float, wy: float, amount: float) -> None:
        """Add pheromone at a world position."""
        idx = self._idx(wx, wy)
        self._grid[channel][idx] += amount

    def sample(self, channel: int, wx: float, wy: float) -> float:
        """Read pheromone intensity at a world position."""
        return self._grid[channel][self._idx(wx, wy)]

    def gradient(self, channel: int, wx: float, wy: float) -> tuple[float, float]:
        """Return (dx, dy) pointing toward increasing pheromone concentration.

        Samples the 3x3 neighborhood around the cell and computes a
        weighted direction vector. Returns (0, 0) if flat.
        """
        col = min(int(wx / self.cell_size), self.cols - 1)
        row = min(int(wy / self.cell_size), self.rows - 1)
        if col < 0:
            col = 0
        if row < 0:
            row = 0

        grid = self._grid[channel]
        gx = 0.0
        gy = 0.0

        for dr in (-1, 0, 1):
            nr = row + dr
            if nr < 0 or nr >= self.rows:
                continue
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nc = col + dc
                if nc < 0 or nc >= self.cols:
                    continue
                val = grid[nr * self.cols + nc]
                gx += dc * val
                gy += dr * val

        return gx, gy

    def tick(self) -> None:
        """Decay and diffuse all channels."""
        cols = self.cols
        rows = self.rows
        decay = self.decay
        diff = self.diffusion
        keep = 1.0 - diff

        for ch in range(self._N_CHANNELS):
            src = self._grid[ch]
            dst = self._scratch[ch]

            # dst is already zeroed from previous tick swap

            for r in range(rows):
                row_off = r * cols
                for c in range(cols):
                    idx = row_off + c
                    center = src[idx] * decay

                    if center < 0.001:
                        continue

                    # keep fraction at center, spread rest to neighbors
                    dst[idx] += center * keep

                    # count valid neighbors for equal spread
                    n_neighbors = 0
                    if r > 0:
                        n_neighbors += 1
                    if r < rows - 1:
                        n_neighbors += 1
                    if c > 0:
                        n_neighbors += 1
                    if c < cols - 1:
                        n_neighbors += 1

                    if n_neighbors == 0:
                        dst[idx] += center * diff
                        continue

                    per = center * diff / n_neighbors
                    if r > 0:
                        dst[(r - 1) * cols + c] += per
                    if r < rows - 1:
                        dst[(r + 1) * cols + c] += per
                    if c > 0:
                        dst[row_off + c - 1] += per
                    if c < cols - 1:
                        dst[row_off + c + 1] += per

            # swap
            self._grid[ch] = dst
            self._scratch[ch] = src
            # clear scratch for next tick
            for i in range(len(src)):
                src[i] = 0.0

    def get_heatmap(self, channel: int, threshold: float = 0.05) -> list[tuple[int, int, float]]:
        """Return list of (col, row, intensity) for cells above threshold.

        Used for export/rendering. Intensity is clamped to [0, 1].
        """
        result: list[tuple[int, int, float]] = []
        grid = self._grid[channel]
        max_val = max(grid) if grid else 0.0
        if max_val < threshold:
            return result

        for r in range(self.rows):
            row_off = r * self.cols
            for c in range(self.cols):
                val = grid[row_off + c]
                if val >= threshold:
                    result.append((c, r, min(1.0, val / max_val)))
        return result
