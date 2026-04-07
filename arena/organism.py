"""Organism — a living entity in the arena."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .genome import Genome

_next_id = 0


def _new_id() -> int:
    global _next_id
    _next_id += 1
    return _next_id


@dataclass(slots=True)
class Organism:
    x: float
    y: float
    genome: Genome
    energy: float = 100.0
    age: int = 0
    id: int = field(default_factory=_new_id)
    generation: int = 0
    kills: int = 0
    alive: bool = True
    death_cause: str = ""  # "", "starved", "old_age", "combat", "meteor"
    killed_by: int = 0  # ID of the organism that killed this one (0 = N/A)
    behavior: int = 0  # 0=idle, 1=hunting, 2=fleeing, 3=grazing, 4=mating, 5=herding, 6=defending
    parent_id: int = 0  # 0 = no parent (initial population)
    children: int = 0  # number of offspring produced
    adaptation: float = 0.0  # 0.0-1.0 environmental adaptation level
    scars: int = 0  # number of combat encounters survived
    fatigue: float = 0.0  # 0.0-1.0 exhaustion level (reduces speed + combat)
    # memory: list of (x, y, type, tick_created) — type 0=food, 1=danger
    _memories: list = field(default_factory=list)

    # --- derived stats -----------------------------------------------------
    @property
    def max_energy(self) -> float:
        return 100 + self.genome.size * 50

    @property
    def energy_cost_per_tick(self) -> float:
        """Basal metabolic cost — bigger, faster, smarter, and more enduring organisms burn more."""
        return (0.5 + self.genome.speed * 0.3 + self.genome.size * 0.4
                + self.genome.memory_capacity * 0.03
                + self.genome.stamina * 0.05)

    @property
    def effective_speed(self) -> float:
        """Speed reduced by fatigue — exhausted organisms move slower."""
        return self.genome.speed * (1.0 - self.fatigue * 0.5)

    @property
    def combat_power(self) -> float:
        fatigue_penalty = 1.0 - self.fatigue * 0.4  # up to 40% combat reduction
        return (self.genome.size * 0.6 + self.genome.aggression * 0.4) * fatigue_penalty

    @property
    def fatigue_gain_rate(self) -> float:
        """How quickly this organism accumulates fatigue. Low stamina = fast fatigue."""
        return 1.0 - self.genome.stamina * 0.6  # 0.4x–1.0x multiplier

    @property
    def fatigue_recovery_rate(self) -> float:
        """How quickly this organism recovers from fatigue. High stamina = fast recovery."""
        return 1.0 + self.genome.stamina * 0.8  # 1.0x–1.8x multiplier

    # --- actions -----------------------------------------------------------
    @property
    def max_age(self) -> int:
        """Larger organisms live longer, but speed costs lifespan."""
        return int(200 + self.genome.size * 100 - self.genome.speed * 30)

    @property
    def age_factor(self) -> float:
        """1.0 when young, increases metabolic cost as organism ages."""
        ratio = self.age / max(self.max_age, 1)
        if ratio < 0.7:
            return 1.0
        return 1.0 + (ratio - 0.7) * 3.0  # accelerating cost after 70% lifespan

    def move_toward(self, tx: float, ty: float, world_w: int, world_h: int) -> None:
        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)
        if dist < 0.01:
            return
        speed = self.effective_speed
        nx = dx / dist * min(speed, dist)
        ny = dy / dist * min(speed, dist)
        self.x = (self.x + nx) % world_w
        self.y = (self.y + ny) % world_h

    def flee_from(self, tx: float, ty: float, world_w: int, world_h: int) -> None:
        """Move away from (tx, ty) at full speed."""
        dx = self.x - tx
        dy = self.y - ty
        dist = math.hypot(dx, dy)
        if dist < 0.01:
            # if right on top, pick random direction
            angle = random.uniform(0, 2 * math.pi)
            dx, dy = math.cos(angle), math.sin(angle)
            dist = 1.0
        speed = self.effective_speed
        nx = dx / dist * speed
        ny = dy / dist * speed
        self.x = (self.x + nx) % world_w
        self.y = (self.y + ny) % world_h

    def wander(self, world_w: int, world_h: int) -> None:
        angle = random.uniform(0, 2 * math.pi)
        speed = self.effective_speed * 0.5
        self.x = (self.x + math.cos(angle) * speed) % world_w
        self.y = (self.y + math.sin(angle) * speed) % world_h

    def tick_metabolism(self) -> None:
        self.energy -= self.energy_cost_per_tick * self.age_factor
        self.age += 1
        if self.energy <= 0:
            self.alive = False
            self.death_cause = "starved"
        elif self.age >= self.max_age:
            self.alive = False
            self.death_cause = "old_age"

    def eat(self, food_energy: float) -> None:
        gained = food_energy * self.genome.efficiency
        self.energy = min(self.energy + gained, self.max_energy)

    def can_reproduce(self) -> bool:
        return self.energy >= self.genome.reproduce_threshold

    def reproduce(self, world_w: int, world_h: int) -> Organism:
        """Asexual reproduction — clone with mutation."""
        child_genome = self.genome.mutate()
        cost = self.genome.reproduce_threshold * 0.5
        self.energy -= cost
        offset_x = random.uniform(-2, 2)
        offset_y = random.uniform(-2, 2)
        child = Organism(
            x=(self.x + offset_x) % world_w,
            y=(self.y + offset_y) % world_h,
            genome=child_genome,
            energy=cost * 0.8,
            generation=self.generation + 1,
            parent_id=self.id,
        )
        self.children += 1
        return child

    def mate(self, partner: Organism, world_w: int, world_h: int) -> Organism:
        """Sexual reproduction — crossover between two parents."""
        child_genome = Genome.crossover(self.genome, partner.genome)
        cost_self = self.genome.reproduce_threshold * 0.3
        cost_partner = partner.genome.reproduce_threshold * 0.3
        self.energy -= cost_self
        partner.energy -= cost_partner
        offset_x = random.uniform(-2, 2)
        offset_y = random.uniform(-2, 2)
        child = Organism(
            x=(self.x + offset_x) % world_w,
            y=(self.y + offset_y) % world_h,
            genome=child_genome,
            energy=(cost_self + cost_partner) * 0.7,
            generation=max(self.generation, partner.generation) + 1,
            parent_id=self.id,
        )
        self.children += 1
        partner.children += 1
        return child

    def can_mate(self) -> bool:
        """Can this organism participate in sexual reproduction?"""
        return self.energy >= self.genome.reproduce_threshold * 0.6 and self.age > 5

    # --- memory system -------------------------------------------------------
    _MEM_FOOD = 0
    _MEM_DANGER = 1

    def remember_food(self, x: float, y: float, tick: int) -> None:
        """Record a food location in memory."""
        self._add_memory(x, y, self._MEM_FOOD, tick)

    def remember_danger(self, x: float, y: float, tick: int) -> None:
        """Record a danger location in memory."""
        self._add_memory(x, y, self._MEM_DANGER, tick)

    def _add_memory(self, x: float, y: float, mtype: int, tick: int) -> None:
        cap = self.genome.memory_capacity
        self._memories.append((x, y, mtype, tick))
        # evict oldest if over capacity
        if len(self._memories) > cap:
            self._memories = self._memories[-cap:]

    def recall_food(self, current_tick: int, max_age: int = 80) -> tuple[float, float] | None:
        """Return the most recent remembered food location, if fresh enough."""
        for x, y, mtype, tick in reversed(self._memories):
            if mtype == self._MEM_FOOD and current_tick - tick <= max_age:
                return x, y
        return None

    def recall_danger(self, current_tick: int, max_age: int = 60) -> list[tuple[float, float]]:
        """Return all remembered danger locations that are fresh enough."""
        result = []
        for x, y, mtype, tick in self._memories:
            if mtype == self._MEM_DANGER and current_tick - tick <= max_age:
                result.append((x, y))
        return result

    def forget_old(self, current_tick: int, max_age: int = 100) -> None:
        """Prune memories older than max_age ticks."""
        self._memories = [
            m for m in self._memories if current_tick - m[3] <= max_age
        ]

    def distance_to(self, other: Organism) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def distance_to_point(self, px: float, py: float) -> float:
        return math.hypot(self.x - px, self.y - py)
