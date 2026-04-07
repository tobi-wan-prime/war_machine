"""Genome encoding for organisms.

Each organism carries a genome — a list of floating-point genes that control
its behavior, perception, and physical traits. Mutation introduces variation;
selection does the rest.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Self


# Gene indices — each index maps to a trait
SPEED = 0           # movement speed (0.0–1.0)
SENSE_RANGE = 1     # how far the organism can "see"
AGGRESSION = 2      # tendency to attack vs flee
SIZE = 3            # body size — affects energy cost and combat
EFFICIENCY = 4      # metabolic efficiency (energy gained per food)
REPRODUCE_THRESH = 5  # energy threshold to trigger reproduction
MUTATION_RATE = 6   # self-encoded mutation rate
MEMORY = 7          # memory capacity (cognitive ability)
COLOR_R = 8         # red channel (for rendering lineage)
COLOR_G = 9         # green channel
COLOR_B = 10        # blue channel
STAMINA = 11        # fatigue resistance (marathon vs sprinter)

NUM_GENES = 12


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass(slots=True)
class Genome:
    genes: list[float] = field(default_factory=lambda: [random.random() for _ in range(NUM_GENES)])

    def __post_init__(self) -> None:
        # pad short gene lists (backwards compat with 11-gene genomes)
        while len(self.genes) < NUM_GENES:
            self.genes.append(random.random())

    # --- trait accessors ---------------------------------------------------
    @property
    def speed(self) -> float:
        return 0.5 + self.genes[SPEED] * 1.5  # 0.5 – 2.0 cells/tick

    @property
    def sense_range(self) -> float:
        return 1.0 + self.genes[SENSE_RANGE] * 6.0  # 1 – 7 cells

    @property
    def aggression(self) -> float:
        return self.genes[AGGRESSION]

    @property
    def size(self) -> float:
        return 0.3 + self.genes[SIZE] * 1.7  # 0.3 – 2.0

    @property
    def efficiency(self) -> float:
        return 0.5 + self.genes[EFFICIENCY] * 1.0  # 0.5 – 1.5

    @property
    def reproduce_threshold(self) -> float:
        return 50 + self.genes[REPRODUCE_THRESH] * 100  # 50 – 150

    @property
    def mutation_rate(self) -> float:
        return 0.01 + self.genes[MUTATION_RATE] * 0.19  # 1%–20%

    @property
    def memory_capacity(self) -> int:
        """Number of memory slots — 1 to 8."""
        return 1 + int(self.genes[MEMORY] * 7)

    @property
    def stamina(self) -> float:
        """Fatigue resistance — 0.0 (glass cannon) to 1.0 (marathon runner)."""
        return self.genes[STAMINA]

    @property
    def color(self) -> tuple[int, int, int]:
        return (
            int(self.genes[COLOR_R] * 255),
            int(self.genes[COLOR_G] * 255),
            int(self.genes[COLOR_B] * 255),
        )

    # --- reproduction ------------------------------------------------------
    def mutate(self) -> Self:
        """Return a mutated copy of this genome."""
        new_genes = []
        for g in self.genes:
            if random.random() < self.mutation_rate:
                g += random.gauss(0, 0.1)
                g = _clamp(g)
            new_genes.append(g)
        return Genome(genes=new_genes)

    @classmethod
    def crossover(cls, a: Genome, b: Genome) -> Genome:
        """Single-point crossover between two parents."""
        point = random.randint(1, NUM_GENES - 1)
        child_genes = a.genes[:point] + b.genes[point:]
        child = cls(genes=child_genes)
        return child.mutate()

    def distance(self, other: Genome) -> float:
        """Euclidean distance in gene space (excluding color genes)."""
        # only compare behavioral genes (0-7), not color (8-10)
        return sum((a - b) ** 2 for a, b in zip(self.genes[:8], other.genes[:8])) ** 0.5

    @classmethod
    def random(cls) -> Genome:
        return cls()
