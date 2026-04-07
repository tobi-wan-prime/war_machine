"""World — the arena where organisms live, eat, fight, and reproduce."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .genome import Genome
from .organism import Organism
from .spatial import SpatialHash
from .history import History
from .events import EventScheduler, EventType, Event
from .terrain import Terrain, TileType
from .species import SpeciesTracker
from .pheromones import PheromoneMap
from .territory_map import TerritoryMap


@dataclass
class Food:
    x: float
    y: float
    energy: float = 20.0


@dataclass
class WorldStats:
    tick: int = 0
    total_born: int = 0
    total_died: int = 0
    total_kills: int = 0
    total_matings: int = 0
    max_generation: int = 0
    peak_population: int = 0
    reseeds: int = 0
    total_shares: int = 0
    total_energy_shared: float = 0.0
    deaths_starved: int = 0
    deaths_old_age: int = 0
    deaths_combat: int = 0
    deaths_meteor: int = 0
    total_symbiosis: int = 0
    total_symbiosis_energy: float = 0.0
    # food chain: {(killer_sp_id, victim_sp_id): kill_count}
    food_chain: dict = field(default_factory=dict)


class World:
    def __init__(self, width: int = 80, height: int = 40,
                 initial_organisms: int = 20, food_rate: int = 5,
                 enable_events: bool = True, enable_terrain: bool = False,
                 terrain_seed: int | None = None,
                 day_length: int = 100,
                 genome_presets: list[tuple[float, list[float]]] | None = None):
        self.width = width
        self.height = height
        self.food_rate = food_rate
        self.day_length = day_length  # ticks per full day/night cycle
        self.organisms: list[Organism] = []
        self.food: list[Food] = []
        self.stats = WorldStats()
        self.graveyard: list[dict] = []
        self.history = History(max_len=300)
        self.last_event: Event | None = None

        # terrain
        if enable_terrain:
            self.terrain = Terrain.generate(width, height, seed=terrain_seed)
            self._fertile_spots = self.terrain.get_fertile_positions()
        else:
            self.terrain = Terrain.empty(width, height)
            self._fertile_spots = []

        # spatial indices
        self._org_grid: SpatialHash[Organism] = SpatialHash(cell_size=8.0)
        self._food_grid: SpatialHash[Food] = SpatialHash(cell_size=8.0)

        # species tracking
        self.species_tracker = SpeciesTracker(distance_threshold=0.6)

        # pheromone trails
        self.pheromones = PheromoneMap(width, height, cell_size=2.0,
                                       decay=0.92, diffusion=0.12)

        # territory map
        self.territory = TerritoryMap(width, height, cell_size=2.0, decay=0.97)

        # environmental events
        self.events = EventScheduler(width, height) if enable_events else None

        # seed initial population (on passable tiles)
        if genome_presets:
            # spawn organisms with specific genome templates + small variation
            remaining = initial_organisms
            for fraction, template in genome_presets:
                count = max(1, int(initial_organisms * fraction))
                count = min(count, remaining)
                for _ in range(count):
                    genes = [max(0.0, min(1.0, t + random.gauss(0, 0.03)))
                             for t in template]
                    x, y = self._random_passable_pos()
                    org = Organism(x=x, y=y, genome=Genome(genes=genes))
                    self.organisms.append(org)
                    self.stats.total_born += 1
                remaining -= count
            # fill any remainder with random
            for _ in range(remaining):
                x, y = self._random_passable_pos()
                org = Organism(x=x, y=y, genome=Genome.random())
                self.organisms.append(org)
                self.stats.total_born += 1
        else:
            for _ in range(initial_organisms):
                x, y = self._random_passable_pos()
                org = Organism(x=x, y=y, genome=Genome.random())
                self.organisms.append(org)
                self.stats.total_born += 1

        # seed initial food
        for _ in range(food_rate * 10):
            self._spawn_food()

    @property
    def time_of_day(self) -> float:
        """0.0 = midnight, 0.25 = dawn, 0.5 = noon, 0.75 = dusk."""
        return (self.stats.tick % self.day_length) / self.day_length

    @property
    def is_night(self) -> bool:
        """Night = time outside 0.2-0.8 range (roughly 40% of the cycle)."""
        t = self.time_of_day
        return t < 0.2 or t > 0.8

    @property
    def light_level(self) -> float:
        """0.0 = pitch dark, 1.0 = full daylight. Smooth sine curve."""
        return 0.5 + 0.5 * math.sin(self.time_of_day * 2 * math.pi - math.pi / 2)

    def effective_sense(self, org: Organism) -> float:
        """Sense range adjusted for light level. High sense_range gene = night vision."""
        base = org.genome.sense_range
        light = self.light_level
        # at full light, sense = 100% base
        # at zero light, sense = 30% + 70% * (sense_range_gene)
        # organisms with high sense gene retain more vision at night
        night_retention = 0.3 + 0.7 * org.genome.genes[1]  # raw gene 0-1
        factor = light + (1.0 - light) * night_retention
        return base * factor

    def _random_passable_pos(self) -> tuple[float, float]:
        for _ in range(100):
            x = random.uniform(0, self.width)
            y = random.uniform(0, self.height)
            if self.terrain.is_passable(x, y):
                return x, y
        return random.uniform(0, self.width), random.uniform(0, self.height)

    def _spawn_food(self, x: float | None = None, y: float | None = None) -> None:
        if x is None or y is None:
            # bias food spawning toward fertile zones
            if self._fertile_spots and random.random() < 0.3:
                fx, fy = random.choice(self._fertile_spots)
                x = fx + random.uniform(-0.5, 0.5)
                y = fy + random.uniform(-0.5, 0.5)
            else:
                x, y = self._random_passable_pos()
        self.food.append(Food(x=x, y=y, energy=random.uniform(10, 30)))

    def _clamp_to_passable(self, org: Organism) -> None:
        """If organism moved into a wall, revert to previous position."""
        if not self.terrain.is_passable(org.x, org.y):
            # nudge away from wall
            best_x, best_y = org.x, org.y
            for angle_i in range(8):
                angle = angle_i * math.pi / 4
                test_x = (org.x + math.cos(angle) * 1.5) % self.width
                test_y = (org.y + math.sin(angle) * 1.5) % self.height
                if self.terrain.is_passable(test_x, test_y):
                    best_x, best_y = test_x, test_y
                    break
            org.x = best_x
            org.y = best_y

    def _rebuild_indices(self) -> None:
        self._org_grid.bulk_insert(self.organisms)
        self._food_grid.bulk_insert(self.food)

    def tick(self) -> None:
        self.stats.tick += 1

        # --- environmental events ---
        effective_food_rate = self.food_rate
        if self.events:
            new_event = self.events.tick(self.stats.tick)
            if new_event:
                self.last_event = new_event
                self._apply_instant_event(new_event)

            if self.events.has_active(EventType.DROUGHT):
                effective_food_rate = max(1, self.food_rate // 2)
            if self.events.has_active(EventType.PLAGUE):
                for org in self.organisms:
                    if org.alive and random.random() < 0.1:
                        org.energy -= random.uniform(2, 8)

        # night reduces food spawning (plants don't grow as fast)
        if self.is_night:
            effective_food_rate = max(1, int(effective_food_rate * 0.6))

        # carrying capacity — reduce food when overpopulated, boost when sparse
        pop = len(self.organisms)
        area = self.width * self.height
        density = pop / max(area, 1)
        # equilibrium at ~0.02 organisms per cell (e.g. 64 for 80x40)
        if density > 0.03:
            # overpopulated — halve food spawning
            effective_food_rate = max(1, effective_food_rate // 2)
        elif density < 0.008 and pop > 0:
            # underpopulated — boost food to help recovery
            effective_food_rate = int(effective_food_rate * 1.5)

        # spawn food (cap total food to prevent unbounded accumulation)
        max_food = area // 4
        if len(self.food) < max_food:
            for _ in range(effective_food_rate):
                self._spawn_food()

        # fertile zone bonus food
        if self._fertile_spots:
            for _ in range(len(self._fertile_spots) // 5):
                fx, fy = random.choice(self._fertile_spots)
                self._spawn_food(fx + random.uniform(-0.5, 0.5),
                                 fy + random.uniform(-0.5, 0.5))

        # bloom: extra food near epicenter
        if self.events and self.events.has_active(EventType.BLOOM):
            for ev in self.events.active_events:
                if ev.type == EventType.BLOOM:
                    for _ in range(int(ev.intensity * 3)):
                        angle = random.uniform(0, 2 * math.pi)
                        r = random.uniform(0, ev.radius)
                        self._spawn_food(
                            x=(ev.x + math.cos(angle) * r) % self.width,
                            y=(ev.y + math.sin(angle) * r) % self.height,
                        )

        # rebuild spatial indices
        self._rebuild_indices()

        # --- organism behavior ---
        new_organisms: list[Organism] = []
        eaten_food: set[int] = set()
        mated_this_tick: set[int] = set()  # organisms that already mated
        # pack targeting: map target_id -> list of attacker organisms converging
        pack_targets: dict[int, list[Organism]] = {}

        for org in self.organisms:
            if not org.alive:
                continue

            sense = self.effective_sense(org)
            nearest_other = self._org_grid.nearest(org.x, org.y, sense, exclude=org)

            acted = False
            org.behavior = 0  # reset to idle

            if nearest_other and nearest_other.alive:
                dist = org.distance_to(nearest_other)

                # aggressive organisms attack
                if org.genome.aggression > 0.5 and org.energy > 30:
                    # check if a pack mate is already targeting someone nearby
                    pack_target = self._get_pack_target(org, nearest_other, pack_targets)
                    target = pack_target if pack_target else nearest_other

                    org.move_toward(target.x, target.y, self.width, self.height)
                    self._clamp_to_passable(org)

                    # register this organism as converging on the target
                    tid = target.id
                    if tid not in pack_targets:
                        pack_targets[tid] = []
                    pack_targets[tid].append(org)

                    if org.distance_to(target) < 1.5:
                        self._pack_fight(org, target, pack_targets.get(tid, []))
                    org.behavior = 1  # hunting
                    acted = True

                # sexual reproduction — mate with nearby non-aggressive partner
                elif (not acted and dist < 2.5
                      and org.can_mate() and nearest_other.can_mate()
                      and org.id not in mated_this_tick
                      and nearest_other.id not in mated_this_tick
                      and org.genome.aggression < 0.5
                      and nearest_other.genome.aggression < 0.5):
                    child = org.mate(nearest_other, self.width, self.height)
                    self._clamp_to_passable(child)
                    new_organisms.append(child)
                    mated_this_tick.add(org.id)
                    mated_this_tick.add(nearest_other.id)
                    self.stats.total_born += 1
                    self.stats.total_matings += 1
                    self.stats.max_generation = max(self.stats.max_generation, child.generation)
                    org.behavior = 4  # mating
                    acted = True

                # territorial defense: moderate-aggro organisms chase intruders on home turf
                elif (not acted and 0.3 <= org.genome.aggression <= 0.6
                      and org.energy > 40):
                    org_sp_t = self.species_tracker.get_species_for(org.id)
                    if (org_sp_t and self.territory.is_home(org.x, org.y, org_sp_t.id)):
                        other_sp_t = self.species_tracker.get_species_for(nearest_other.id)
                        if other_sp_t and other_sp_t.id != org_sp_t.id and dist < sense * 0.5:
                            # chase the intruder
                            org.move_toward(nearest_other.x, nearest_other.y, self.width, self.height)
                            self._clamp_to_passable(org)
                            if org.distance_to(nearest_other) < 1.5:
                                self._fight(org, nearest_other)
                            org.behavior = 6  # defending
                            acted = True

                # non-aggressive organisms flee from aggressive neighbors
                elif org.genome.aggression < 0.3 and nearest_other.genome.aggression > 0.5 and dist < sense * 0.7:
                    org.flee_from(nearest_other.x, nearest_other.y, self.width, self.height)
                    self._clamp_to_passable(org)
                    org.behavior = 2  # fleeing
                    acted = True

            # seek food via spatial hash
            if not acted:
                nearby_food = self._food_grid.query_radius(org.x, org.y, sense)
                nearby_food = [f for f in nearby_food if id(f) not in eaten_food]
                if nearby_food:
                    nearest_food = min(nearby_food, key=lambda f: org.distance_to_point(f.x, f.y))
                    org.move_toward(nearest_food.x, nearest_food.y, self.width, self.height)
                    self._clamp_to_passable(org)
                    if org.distance_to_point(nearest_food.x, nearest_food.y) < 1.0:
                        org.eat(nearest_food.energy)
                        eaten_food.add(id(nearest_food))
                        # deposit food pheromone where we ate
                        self.pheromones.deposit(PheromoneMap.FOOD, org.x, org.y, 1.0)
                        # remember this food location
                        org.remember_food(org.x, org.y, self.stats.tick)
                        # claim territory for our species
                        org_sp = self.species_tracker.get_species_for(org.id)
                        if org_sp:
                            self.territory.claim(org.x, org.y, org_sp.id)
                    org.behavior = 3  # grazing
                    acted = True

            # follow memory / pheromone trail / wander
            if not acted:
                # 1. check remembered danger — flee from nearest
                danger_mems = org.recall_danger(self.stats.tick)
                if danger_mems and org.genome.aggression < 0.4:
                    # flee from nearest remembered danger
                    nearest_d = min(danger_mems, key=lambda d: org.distance_to_point(d[0], d[1]))
                    if org.distance_to_point(nearest_d[0], nearest_d[1]) < org.genome.sense_range:
                        org.flee_from(nearest_d[0], nearest_d[1], self.width, self.height)
                        self._clamp_to_passable(org)
                        org.behavior = 2  # fleeing
                        acted = True

                # 2. check pheromone danger
                if not acted:
                    danger = self.pheromones.sample(PheromoneMap.DANGER, org.x, org.y)
                    if danger > 0.1 and org.genome.aggression < 0.4:
                        dgx, dgy = self.pheromones.gradient(PheromoneMap.DANGER, org.x, org.y)
                        if abs(dgx) > 0.01 or abs(dgy) > 0.01:
                            org.flee_from(org.x + dgx, org.y + dgy, self.width, self.height)
                            self._clamp_to_passable(org)
                            org.behavior = 2  # fleeing
                            acted = True

                # 3. navigate toward remembered food location
                if not acted:
                    food_mem = org.recall_food(self.stats.tick)
                    if food_mem:
                        fx, fy = food_mem
                        dist_to_mem = org.distance_to_point(fx, fy)
                        if dist_to_mem > 1.5:
                            org.move_toward(fx, fy, self.width, self.height)
                            self._clamp_to_passable(org)
                            org.behavior = 3  # grazing (seeking remembered food)
                            acted = True

                # 4. herd with same-species kin (seek nearby kin)
                if not acted and org.genome.aggression < 0.6:
                    kin = self._find_nearest_kin(org, sense * 1.5)
                    if kin:
                        kin_dist = org.distance_to(kin)
                        if kin_dist > 3.0:
                            # move toward kin (herding)
                            org.move_toward(kin.x, kin.y, self.width, self.height)
                            self._clamp_to_passable(org)
                            org.behavior = 5  # herding
                            acted = True
                        # if already close to kin (< 3.0), don't herd — try other actions

                # 5. follow food pheromone gradient
                if not acted:
                    fgx, fgy = self.pheromones.gradient(PheromoneMap.FOOD, org.x, org.y)
                    if abs(fgx) > 0.05 or abs(fgy) > 0.05:
                        org.move_toward(
                            org.x + fgx * 3, org.y + fgy * 3,
                            self.width, self.height,
                        )
                        self._clamp_to_passable(org)
                    else:
                        org.wander(self.width, self.height)
                        self._clamp_to_passable(org)

            # environmental zone effects
            in_harsh = False
            adapt_shield = 1.0 - org.adaptation * 0.6  # up to 60% damage reduction
            if self.terrain.is_toxic(org.x, org.y):
                in_harsh = True
                toxic_dmg = 3.0 * (1.5 - org.genome.efficiency) * adapt_shield
                org.energy -= max(0.3, toxic_dmg)
            if self.terrain.is_hot(org.x, org.y):
                in_harsh = True
                if org.genome.genes[0] < 0.4:  # slow
                    org.energy -= 1.5 * adapt_shield
                elif org.genome.genes[0] > 0.7:  # fast
                    org.energy += 0.3 + org.adaptation * 0.2
            if self.terrain.is_cold(org.x, org.y):
                in_harsh = True
                if org.genome.genes[3] < 0.3:  # small
                    org.energy -= 1.5 * adapt_shield
                elif org.genome.genes[3] > 0.6:  # large
                    org.energy += 0.3 + org.adaptation * 0.2
            # adaptation grows in harsh zones, decays outside
            if in_harsh:
                org.adaptation = min(1.0, org.adaptation + 0.005)
            else:
                org.adaptation = max(0.0, org.adaptation - 0.002)

            # fatigue: fighting and fleeing exhaust, idle/grazing recovers
            # stamina gene modifies accumulation and recovery rates
            if org.behavior in (1, 2, 6):  # hunting, fleeing, defending
                org.fatigue = min(1.0, org.fatigue + 0.02 * org.fatigue_gain_rate)
            elif org.behavior in (0, 3, 5):  # idle, grazing, herding
                org.fatigue = max(0.0, org.fatigue - 0.01 * org.fatigue_recovery_rate)
            # mating (4) doesn't change fatigue

            # metabolism + memory pruning
            org.tick_metabolism()
            if self.stats.tick % 10 == 0:
                org.forget_old(self.stats.tick)

            # asexual reproduction (fallback if no mate found)
            if org.alive and org.can_reproduce() and org.id not in mated_this_tick:
                child = org.reproduce(self.width, self.height)
                self._clamp_to_passable(child)
                new_organisms.append(child)
                self.stats.total_born += 1
                self.stats.max_generation = max(self.stats.max_generation, child.generation)

        # remove eaten food
        if eaten_food:
            self.food = [f for f in self.food if id(f) not in eaten_food]

        # add newborns
        self.organisms.extend(new_organisms)

        # --- kin energy sharing ---
        # non-aggressive organisms share energy with nearby same-species kin
        if self.stats.tick % 3 == 0:  # every 3 ticks for performance
            self._kin_energy_sharing()

        # --- cross-species symbiosis ---
        # non-aggressive organisms near different-species non-aggressive organisms gain energy
        if self.stats.tick % 5 == 0:  # every 5 ticks for performance
            self._symbiosis()

        # remove dead — deposit danger pheromone at death sites
        for org in self.organisms:
            if not org.alive:
                self.stats.total_died += 1
                cause = org.death_cause or "unknown"
                if cause == "starved":
                    self.stats.deaths_starved += 1
                elif cause == "old_age":
                    self.stats.deaths_old_age += 1
                elif cause == "combat":
                    self.stats.deaths_combat += 1
                elif cause == "meteor":
                    self.stats.deaths_meteor += 1
                self.graveyard.append({
                    "id": org.id, "age": org.age, "gen": org.generation,
                    "kills": org.kills, "tick": self.stats.tick,
                    "cause": cause,
                    "x": round(org.x, 1), "y": round(org.y, 1),
                    "killer": org.killed_by,
                })
                self.pheromones.deposit(PheromoneMap.DANGER, org.x, org.y, 2.0)

        self.organisms = [o for o in self.organisms if o.alive]
        self.stats.peak_population = max(self.stats.peak_population, len(self.organisms))

        # cap graveyard
        if len(self.graveyard) > 500:
            self.graveyard = self.graveyard[-250:]

        # tick pheromone decay and diffusion
        self.pheromones.tick()

        # tick territory decay
        self.territory.tick()

        # classify species every 5 ticks (expensive operation)
        if self.stats.tick % 5 == 0 and self.organisms:
            self.species_tracker.classify(self.organisms, self.stats.tick)

        # record history
        summary = self.get_population_summary()
        self.history.record(
            tick=self.stats.tick,
            population=summary["count"],
            food_count=summary.get("food_available", 0),
            avg_speed=summary.get("avg_speed", 0),
            avg_size=summary.get("avg_size", 0),
            avg_aggression=summary.get("avg_aggression", 0),
            avg_generation=summary.get("avg_generation", 0),
            total_born=self.stats.total_born,
            total_died=self.stats.total_died,
            total_kills=self.stats.total_kills,
        )

        # population safeguard
        if len(self.organisms) == 0:
            self.stats.reseeds += 1
            for _ in range(10):
                x, y = self._random_passable_pos()
                org = Organism(x=x, y=y, genome=Genome.random())
                self.organisms.append(org)
                self.stats.total_born += 1

    def _apply_instant_event(self, event: Event) -> None:
        if event.type == EventType.METEOR:
            for org in self.organisms:
                if org.alive:
                    dist = math.hypot(org.x - event.x, org.y - event.y)
                    if dist < event.radius:
                        damage = event.intensity * (1 - dist / event.radius)
                        org.energy -= damage
                        if org.energy <= 0:
                            org.alive = False
                            org.death_cause = "meteor"

        elif event.type == EventType.MIGRATION:
            count = int(event.intensity)
            for _ in range(count):
                x, y = self._random_passable_pos()
                org = Organism(x=x, y=y, genome=Genome.random(), energy=80)
                self.organisms.append(org)
                self.stats.total_born += 1

    def _find_nearest_kin(self, org: Organism, radius: float) -> Organism | None:
        """Find the nearest same-species organism within radius."""
        org_sp = self.species_tracker.get_species_for(org.id)
        if not org_sp:
            return None

        nearby = self._org_grid.query_radius(org.x, org.y, radius)
        best: Organism | None = None
        best_dist_sq = radius * radius

        for other in nearby:
            if other is org or not other.alive:
                continue
            other_sp = self.species_tracker.get_species_for(other.id)
            if not other_sp or other_sp.id != org_sp.id:
                continue
            dx = org.x - other.x
            dy = org.y - other.y
            d_sq = dx * dx + dy * dy
            if d_sq < best_dist_sq:
                best_dist_sq = d_sq
                best = other

        return best

    def _kin_energy_sharing(self) -> None:
        """Non-aggressive organisms share energy with nearby same-species kin.

        Donor: aggression < 0.4, energy > 70% of max
        Recipient: same species, within 2.5 cells, energy < 40% of max
        Transfer: 8% of donor's energy
        """
        tracker = self.species_tracker
        shared_this_round: set[int] = set()

        for org in self.organisms:
            if not org.alive or org.id in shared_this_round:
                continue
            if org.genome.aggression >= 0.4:
                continue
            if org.energy < org.max_energy * 0.7:
                continue

            # find nearby organisms
            nearby = self._org_grid.query_radius(org.x, org.y, 2.5)
            org_sp = tracker.get_species_for(org.id)
            if not org_sp:
                continue

            for other in nearby:
                if other is org or not other.alive:
                    continue
                if other.id in shared_this_round:
                    continue
                # must be same species
                other_sp = tracker.get_species_for(other.id)
                if not other_sp or other_sp.id != org_sp.id:
                    continue
                # recipient must be low energy
                if other.energy >= other.max_energy * 0.4:
                    continue

                # transfer energy
                amount = org.energy * 0.08
                org.energy -= amount
                other.energy = min(other.energy + amount, other.max_energy)
                shared_this_round.add(org.id)
                self.stats.total_shares += 1
                self.stats.total_energy_shared += amount
                break  # one donation per tick per donor

    def _symbiosis(self) -> None:
        """Cross-species mutualism — nearby non-aggressive organisms of different
        species gain a small energy bonus from proximity.

        Both organisms must have aggression < 0.35 and be within 3.0 cells.
        Each eligible pair generates 1.5 energy for each partner per tick.
        An organism can only benefit from one symbiotic partner per round.
        """
        tracker = self.species_tracker
        bonused: set[int] = set()

        for org in self.organisms:
            if not org.alive or org.id in bonused:
                continue
            if org.genome.aggression >= 0.35:
                continue

            org_sp = tracker.get_species_for(org.id)
            if not org_sp:
                continue

            nearby = self._org_grid.query_radius(org.x, org.y, 3.0)
            for other in nearby:
                if other is org or not other.alive:
                    continue
                if other.id in bonused:
                    continue
                if other.genome.aggression >= 0.35:
                    continue

                other_sp = tracker.get_species_for(other.id)
                if not other_sp or other_sp.id == org_sp.id:
                    continue  # must be *different* species

                # symbiotic energy bonus
                bonus = 1.5
                org.energy = min(org.energy + bonus, org.max_energy)
                other.energy = min(other.energy + bonus, other.max_energy)
                bonused.add(org.id)
                bonused.add(other.id)
                self.stats.total_symbiosis += 1
                self.stats.total_symbiosis_energy += bonus * 2
                break  # one symbiotic partner per round

    def _get_pack_target(self, org: Organism, default_target: Organism,
                         pack_targets: dict[int, list[Organism]]) -> Organism | None:
        """Check if a same-species pack mate is already targeting someone nearby.

        If so, converge on that target instead. Creates coordinated pack attacks.
        """
        org_sp = self.species_tracker.get_species_for(org.id)
        if not org_sp:
            return None

        sense = self.effective_sense(org)
        nearby_kin = self._org_grid.query_radius(org.x, org.y, sense)

        for kin in nearby_kin:
            if kin is org or not kin.alive:
                continue
            kin_sp = self.species_tracker.get_species_for(kin.id)
            if not kin_sp or kin_sp.id != org_sp.id:
                continue
            # check if this kin is attacking a target we can see
            for tid, attackers in pack_targets.items():
                if kin in attackers:
                    # find the actual target organism
                    for target_org in self.organisms:
                        if target_org.id == tid and target_org.alive:
                            # only join if target is within our sense range
                            if org.distance_to(target_org) < sense:
                                return target_org
                    break  # kin found, don't check more pack_targets

        return None

    def _pack_fight(self, attacker: Organism, defender: Organism,
                    pack_members: list[Organism]) -> None:
        """Combat with pack bonus. Nearby same-species allies boost attack power."""
        defender.remember_danger(defender.x, defender.y, self.stats.tick)

        # count nearby pack members who are close to the target
        pack_bonus = 0.0
        nearby_allies: list[Organism] = []
        for ally in pack_members:
            if ally is attacker or not ally.alive:
                continue
            if ally.distance_to(defender) < 3.0:
                pack_bonus += ally.combat_power * 0.3  # each ally adds 30% of their combat power
                nearby_allies.append(ally)

        # territory bonus: +20% if fighting on home turf
        a_sp = self.species_tracker.get_species_for(attacker.id)
        d_sp = self.species_tracker.get_species_for(defender.id)
        a_terr = 1.2 if (a_sp and self.territory.is_home(attacker.x, attacker.y, a_sp.id)) else 1.0
        d_terr = 1.2 if (d_sp and self.territory.is_home(defender.x, defender.y, d_sp.id)) else 1.0

        a_power = (attacker.combat_power + pack_bonus) * a_terr * random.uniform(0.8, 1.2)
        d_power = defender.combat_power * d_terr * random.uniform(0.8, 1.2)

        # pack combat fatigues all participants (stamina reduces gain)
        attacker.fatigue = min(1.0, attacker.fatigue + 0.06 * attacker.fatigue_gain_rate)
        defender.fatigue = min(1.0, defender.fatigue + 0.05 * defender.fatigue_gain_rate)
        for ally in nearby_allies:
            ally.fatigue = min(1.0, ally.fatigue + 0.04 * ally.fatigue_gain_rate)

        if a_power > d_power:
            energy_stolen = defender.energy * 0.5
            # split energy among pack (attacker gets 60%, allies split 40%)
            if nearby_allies:
                attacker_share = energy_stolen * 0.6
                ally_share = energy_stolen * 0.4 / len(nearby_allies)
                attacker.eat(attacker_share)
                for ally in nearby_allies:
                    ally.eat(ally_share)
            else:
                attacker.eat(energy_stolen)

            defender.alive = False
            defender.death_cause = "combat"
            defender.killed_by = attacker.id
            attacker.kills += 1
            attacker.scars += 1
            for ally in nearby_allies:
                ally.scars += 1
            self.stats.total_kills += 1
            self._record_kill(attacker, defender)
            attacker.remember_food(attacker.x, attacker.y, self.stats.tick)
        else:
            energy_stolen = attacker.energy * 0.3
            defender.eat(energy_stolen)
            attacker.energy -= energy_stolen
            defender.scars += 1
            if attacker.energy <= 0:
                attacker.alive = False
                attacker.death_cause = "combat"
                attacker.killed_by = defender.id
                defender.kills += 1
                self.stats.total_kills += 1
                self._record_kill(defender, attacker)

    def _fight(self, attacker: Organism, defender: Organism) -> None:
        # defender remembers this danger location
        defender.remember_danger(defender.x, defender.y, self.stats.tick)

        # territory bonus
        a_sp = self.species_tracker.get_species_for(attacker.id)
        d_sp = self.species_tracker.get_species_for(defender.id)
        a_terr = 1.2 if (a_sp and self.territory.is_home(attacker.x, attacker.y, a_sp.id)) else 1.0
        d_terr = 1.2 if (d_sp and self.territory.is_home(defender.x, defender.y, d_sp.id)) else 1.0

        a_power = attacker.combat_power * a_terr * random.uniform(0.8, 1.2)
        d_power = defender.combat_power * d_terr * random.uniform(0.8, 1.2)

        # combat fatigues both participants (stamina reduces gain)
        attacker.fatigue = min(1.0, attacker.fatigue + 0.08 * attacker.fatigue_gain_rate)
        defender.fatigue = min(1.0, defender.fatigue + 0.05 * defender.fatigue_gain_rate)

        if a_power > d_power:
            energy_stolen = defender.energy * 0.5
            attacker.eat(energy_stolen)
            defender.alive = False
            defender.death_cause = "combat"
            defender.killed_by = attacker.id
            attacker.kills += 1
            attacker.scars += 1
            self.stats.total_kills += 1
            self._record_kill(attacker, defender)
            # attacker remembers this as a good hunting spot
            attacker.remember_food(attacker.x, attacker.y, self.stats.tick)
        else:
            energy_stolen = attacker.energy * 0.3
            defender.eat(energy_stolen)
            attacker.energy -= energy_stolen
            defender.scars += 1
            if attacker.energy <= 0:
                attacker.alive = False
                attacker.death_cause = "combat"
                attacker.killed_by = defender.id
                defender.kills += 1
                self.stats.total_kills += 1
                self._record_kill(defender, attacker)

    def _record_kill(self, killer: Organism, victim: Organism) -> None:
        """Record a species-level kill for the food chain."""
        k_sp = self.species_tracker.get_species_for(killer.id)
        v_sp = self.species_tracker.get_species_for(victim.id)
        if k_sp and v_sp:
            key = (k_sp.id, v_sp.id)
            self.stats.food_chain[key] = self.stats.food_chain.get(key, 0) + 1

    def get_population_summary(self) -> dict:
        if not self.organisms:
            return {"count": 0}
        n = len(self.organisms)
        avg_speed = sum(o.genome.speed for o in self.organisms) / n
        avg_size = sum(o.genome.size for o in self.organisms) / n
        avg_aggro = sum(o.genome.aggression for o in self.organisms) / n
        avg_gen = sum(o.generation for o in self.organisms) / n
        avg_energy = sum(o.energy for o in self.organisms) / n
        avg_age = sum(o.age for o in self.organisms) / n
        avg_memory = sum(o.genome.memory_capacity for o in self.organisms) / n
        return {
            "count": n,
            "avg_speed": round(avg_speed, 2),
            "avg_size": round(avg_size, 2),
            "avg_aggression": round(avg_aggro, 2),
            "avg_generation": round(avg_gen, 1),
            "avg_energy": round(avg_energy, 1),
            "avg_age": round(avg_age, 1),
            "food_available": len(self.food),
            "max_generation": self.stats.max_generation,
            "matings": self.stats.total_matings,
            "avg_memory": round(avg_memory, 1),
            "time_of_day": round(self.time_of_day, 3),
            "light_level": round(self.light_level, 3),
            "shares": self.stats.total_shares,
            "deaths_starved": self.stats.deaths_starved,
            "deaths_old_age": self.stats.deaths_old_age,
            "deaths_combat": self.stats.deaths_combat,
            "deaths_meteor": self.stats.deaths_meteor,
            "symbiosis": self.stats.total_symbiosis,
            "genetics": self.species_tracker.get_genetics_stats(self.organisms),
        }
