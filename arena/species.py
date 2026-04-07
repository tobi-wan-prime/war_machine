"""Species detection via genome distance clustering.

Uses a simple leader-based clustering: each species is defined by a centroid
genome. Organisms within a threshold distance belong to that species. New
species emerge when an organism is too far from all existing centroids.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .genome import Genome, NUM_GENES
from .organism import Organism


@dataclass
class Species:
    id: int
    centroid: list[float]  # average genes of members (behavioral only, indices 0-6)
    color: tuple[int, int, int]  # display color
    member_count: int = 0
    total_born: int = 0
    peak_count: int = 0
    first_seen: int = 0
    last_seen: int = 0
    parent_id: int = 0  # species this one branched from (0 = root/unknown)
    extinct_tick: int = 0  # tick when member_count first hit 0 (0 = still alive)

    @property
    def alive(self) -> bool:
        return self.member_count > 0


# fixed species palette — visually distinct colors
SPECIES_COLORS = [
    (66, 165, 245),   # blue
    (239, 83, 80),    # red
    (102, 187, 106),  # green
    (255, 167, 38),   # orange
    (171, 71, 188),   # purple
    (38, 198, 218),   # cyan
    (255, 238, 88),   # yellow
    (236, 64, 122),   # pink
    (120, 144, 156),  # blue-grey
    (255, 138, 101),  # deep orange
    (129, 199, 132),  # light green
    (100, 181, 246),  # light blue
]

_next_species_id = 0


def _new_species_id() -> int:
    global _next_species_id
    _next_species_id += 1
    return _next_species_id


class SpeciesTracker:
    """Tracks species formation and extinction over time."""

    def __init__(self, distance_threshold: float = 0.6):
        self.threshold = distance_threshold
        self.threshold_sq = distance_threshold ** 2
        self.species: dict[int, Species] = {}
        self.organism_species: dict[int, int] = {}  # organism_id -> species_id
        self._active_species: list[Species] = []  # cached for fast lookup
        self.history: list[dict] = []  # per-tick species counts

    def _gene_distance_sq(self, genes_a: list[float], genes_b: list[float]) -> float:
        """Squared distance — avoids sqrt for comparison."""
        d = 0.0
        for i in range(7):
            diff = genes_a[i] - genes_b[i]
            d += diff * diff
        return d

    def _find_closest_species(self, genes: list[float]) -> tuple[int | None, float]:
        best_id = None
        best_dist_sq = float("inf")
        for sp in self._active_species:
            d_sq = self._gene_distance_sq(genes, sp.centroid)
            if d_sq < best_dist_sq:
                best_dist_sq = d_sq
                best_id = sp.id
        return best_id, best_dist_sq

    def classify(self, organisms: list[Organism], tick: int) -> None:
        """Assign each organism to a species. Creates new species as needed."""
        # prune extinct species (keep only recently active ones)
        if len(self.species) > 100:
            self.species = {
                sid: sp for sid, sp in self.species.items()
                if sp.member_count > 0 or tick - sp.last_seen < 50
            }

        # reset counts and cache active list
        for sp in self.species.values():
            sp.member_count = 0
        self._active_species = list(self.species.values())

        self.organism_species.clear()

        for org in organisms:
            genes = org.genome.genes
            sp_id, dist_sq = self._find_closest_species(genes)

            if sp_id is not None and dist_sq <= self.threshold_sq:
                # belongs to existing species
                self.organism_species[org.id] = sp_id
                sp = self.species[sp_id]
                sp.member_count += 1
                sp.last_seen = tick
                sp.peak_count = max(sp.peak_count, sp.member_count)
            else:
                # new species — find closest existing as parent
                parent_id = sp_id if sp_id is not None else 0
                new_id = _new_species_id()
                color_idx = new_id % len(SPECIES_COLORS)
                sp = Species(
                    id=new_id,
                    centroid=list(genes[:7]),
                    color=SPECIES_COLORS[color_idx],
                    member_count=1,
                    total_born=1,
                    peak_count=1,
                    first_seen=tick,
                    last_seen=tick,
                    parent_id=parent_id,
                )
                self.species[new_id] = sp
                self._active_species.append(sp)
                self.organism_species[org.id] = new_id

        # mark newly extinct species
        for sp in self.species.values():
            if sp.member_count == 0 and sp.extinct_tick == 0 and sp.first_seen < tick:
                sp.extinct_tick = tick

        # update centroids based on current members
        self._update_centroids(organisms)

        # record history
        snapshot = {}
        for sp in self.species.values():
            if sp.member_count > 0:
                snapshot[sp.id] = sp.member_count
        self.history.append({"tick": tick, "species": snapshot})

        # trim history
        if len(self.history) > 300:
            self.history = self.history[-300:]

    def _update_centroids(self, organisms: list[Organism]) -> None:
        """Recalculate species centroids from current members."""
        accum: dict[int, tuple[list[float], int]] = {}

        for org in organisms:
            sp_id = self.organism_species.get(org.id)
            if sp_id is None:
                continue
            if sp_id not in accum:
                accum[sp_id] = ([0.0] * 7, 0)
            genes_sum, count = accum[sp_id]
            for i in range(7):
                genes_sum[i] += org.genome.genes[i]
            accum[sp_id] = (genes_sum, count + 1)

        for sp_id, (genes_sum, count) in accum.items():
            if count > 0 and sp_id in self.species:
                self.species[sp_id].centroid = [g / count for g in genes_sum]

    def get_species_for(self, org_id: int) -> Species | None:
        sp_id = self.organism_species.get(org_id)
        if sp_id is not None:
            return self.species.get(sp_id)
        return None

    def get_species_by_id(self, species_id: int) -> Species | None:
        return self.species.get(species_id)

    def get_active_species(self) -> list[Species]:
        return sorted(
            [sp for sp in self.species.values() if sp.member_count > 0],
            key=lambda s: s.member_count,
            reverse=True,
        )

    def get_summary(self) -> dict:
        active = self.get_active_species()
        return {
            "active_count": len(active),
            "total_ever": len(self.species),
            "species": [
                {
                    "id": sp.id,
                    "count": sp.member_count,
                    "color": list(sp.color),
                    "peak": sp.peak_count,
                    "first_seen": sp.first_seen,
                }
                for sp in active[:8]  # top 8 by count
            ],
        }

    def get_genetics_stats(self, organisms: list[Organism]) -> dict:
        """Compute population genetics metrics.

        Returns:
            diversity: average within-species gene variance (0 = clones, higher = diverse)
            divergence: average pairwise centroid distance between active species
        """
        # group organisms by species
        groups: dict[int, list[list[float]]] = {}
        for org in organisms:
            sp_id = self.organism_species.get(org.id)
            if sp_id is not None:
                if sp_id not in groups:
                    groups[sp_id] = []
                groups[sp_id].append(org.genome.genes)

        # within-species diversity (average gene variance)
        total_var = 0.0
        species_count = 0
        for sp_id, gene_lists in groups.items():
            if len(gene_lists) < 2:
                continue
            n = len(gene_lists)
            sp_var = 0.0
            for gi in range(7):  # functional genes only
                mean = sum(gl[gi] for gl in gene_lists) / n
                var = sum((gl[gi] - mean) ** 2 for gl in gene_lists) / n
                sp_var += var
            total_var += sp_var / 7  # average across genes
            species_count += 1

        diversity = round(total_var / max(species_count, 1), 4)

        # between-species divergence (avg pairwise centroid distance)
        active = [sp for sp in self.species.values() if sp.member_count > 0]
        divergence = 0.0
        pairs = 0
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                d_sq = self._gene_distance_sq(active[i].centroid, active[j].centroid)
                divergence += d_sq ** 0.5
                pairs += 1

        divergence = round(divergence / max(pairs, 1), 4)

        return {
            "diversity": diversity,
            "divergence": divergence,
            "species_with_data": species_count,
        }

    def get_phylogeny(self) -> list[dict]:
        """Return phylogenetic tree data for all species ever seen.

        Each entry: {id, parent, color, first_seen, last_seen, extinct_tick, peak}.
        """
        result = []
        for sp in self.species.values():
            result.append({
                "id": sp.id,
                "parent": sp.parent_id,
                "color": list(sp.color),
                "first": sp.first_seen,
                "last": sp.last_seen,
                "ext": sp.extinct_tick,
                "peak": sp.peak_count,
            })
        # sort by first_seen for consistent ordering
        result.sort(key=lambda d: d["first"])
        return result
