"""Population history tracking and sparkline rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from collections import deque


@dataclass
class Snapshot:
    tick: int
    population: int
    food_count: int
    avg_speed: float
    avg_size: float
    avg_aggression: float
    avg_generation: float
    births: int
    deaths: int
    kills: int


class History:
    """Rolling history of simulation snapshots for graphing."""

    def __init__(self, max_len: int = 200):
        self.snapshots: deque[Snapshot] = deque(maxlen=max_len)
        self._prev_born: int = 0
        self._prev_died: int = 0
        self._prev_kills: int = 0

    def record(self, tick: int, population: int, food_count: int,
               avg_speed: float, avg_size: float, avg_aggression: float,
               avg_generation: float, total_born: int, total_died: int,
               total_kills: int) -> None:
        births = total_born - self._prev_born
        deaths = total_died - self._prev_died
        kills = total_kills - self._prev_kills
        self._prev_born = total_born
        self._prev_died = total_died
        self._prev_kills = total_kills

        self.snapshots.append(Snapshot(
            tick=tick, population=population, food_count=food_count,
            avg_speed=avg_speed, avg_size=avg_size,
            avg_aggression=avg_aggression, avg_generation=avg_generation,
            births=births, deaths=deaths, kills=kills,
        ))

    def sparkline(self, attr: str, width: int = 40, label: str = "") -> str:
        """Render a sparkline for the given attribute using Unicode blocks."""
        blocks = " _.:oO#@"
        if len(self.snapshots) < 2:
            return f"{label}: (waiting for data)"

        # sample evenly across history
        values = [getattr(s, attr) for s in self.snapshots]
        if len(values) > width:
            step = len(values) / width
            sampled = [values[int(i * step)] for i in range(width)]
        else:
            sampled = values

        lo = min(sampled)
        hi = max(sampled)
        span = hi - lo if hi > lo else 1.0

        chars = []
        for v in sampled:
            idx = int((v - lo) / span * (len(blocks) - 1))
            chars.append(blocks[idx])

        current = sampled[-1]
        return f"{label}{''.join(chars)} {current:.1f}"

    def to_dicts(self) -> list[dict]:
        return [
            {
                "tick": s.tick, "population": s.population,
                "food": s.food_count, "avg_speed": s.avg_speed,
                "avg_size": s.avg_size, "avg_aggression": s.avg_aggression,
                "avg_generation": s.avg_generation,
                "births": s.births, "deaths": s.deaths, "kills": s.kills,
            }
            for s in self.snapshots
        ]
