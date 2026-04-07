"""Predefined simulation scenarios."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Scenario:
    name: str
    description: str
    width: int
    height: int
    pop: int
    food_rate: int
    enable_events: bool
    enable_terrain: bool
    terrain_seed: int | None
    ticks: int
    day_length: int = 100  # ticks per full day/night cycle
    genome_presets: list[tuple[float, list[float]]] | None = None


SCENARIOS: dict[str, Scenario] = {
    "default": Scenario(
        name="Default",
        description="Standard arena — balanced parameters, events enabled",
        width=80, height=40, pop=25, food_rate=5,
        enable_events=True, enable_terrain=False, terrain_seed=None, ticks=500,
    ),
    "island": Scenario(
        name="Island",
        description="Walled arena with fertile zones — isolated populations evolve independently",
        width=80, height=40, pop=30, food_rate=4,
        enable_events=True, enable_terrain=True, terrain_seed=42, ticks=600,
    ),
    "gauntlet": Scenario(
        name="Gauntlet",
        description="Dense walls, low food, high pop — survival of the fittest",
        width=60, height=30, pop=40, food_rate=2,
        enable_events=True, enable_terrain=True, terrain_seed=99, ticks=400,
    ),
    "paradise": Scenario(
        name="Paradise",
        description="Abundant food, no events — watch evolution without pressure",
        width=80, height=40, pop=15, food_rate=10,
        enable_events=False, enable_terrain=False, terrain_seed=None, ticks=800, day_length=200,
    ),
    "maze": Scenario(
        name="Maze",
        description="Heavy terrain with many walls — organisms must navigate tight corridors",
        width=80, height=40, pop=20, food_rate=4,
        enable_events=True, enable_terrain=True, terrain_seed=7, ticks=500,
    ),
    "apocalypse": Scenario(
        name="Apocalypse",
        description="Frequent events, scarce food, toxic terrain — can life persist?",
        width=60, height=30, pop=30, food_rate=2,
        enable_events=True, enable_terrain=True, terrain_seed=666, ticks=500, day_length=60,
    ),
    "petri": Scenario(
        name="Petri Dish",
        description="Small arena, few organisms — watch individual lineages diverge",
        width=40, height=20, pop=8, food_rate=3,
        enable_events=False, enable_terrain=False, terrain_seed=None, ticks=400,
    ),
    "colony": Scenario(
        name="Colony",
        description="Large population with terrain — watch herds form, packs hunt, colonies emerge",
        width=100, height=50, pop=50, food_rate=8,
        enable_events=True, enable_terrain=True, terrain_seed=314, ticks=600,
    ),
    "predator_prey": Scenario(
        name="Predator vs Prey",
        description="Two rival populations — fast aggressive hunters vs large cooperative herders",
        width=80, height=40, pop=40, food_rate=6,
        enable_events=True, enable_terrain=False, terrain_seed=None, ticks=600,
        genome_presets=[
            # 40% predators: fast, high sense, aggressive, small, low efficiency, low repro thresh
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.4, [0.8, 0.7, 0.85, 0.35, 0.4, 0.45, 0.3, 0.3, 0.9, 0.2, 0.1]),
            # 60% prey: slow, medium sense, non-aggressive, large, efficient, high repro, good memory
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.6, [0.3, 0.5, 0.1, 0.8, 0.7, 0.55, 0.3, 0.7, 0.2, 0.8, 0.3]),
        ],
    ),
    "war": Scenario(
        name="War",
        description="Two aggressive factions in walled terrain — territorial warfare and speciation",
        width=80, height=40, pop=40, food_rate=5,
        enable_events=True, enable_terrain=True, terrain_seed=137, ticks=700,
        day_length=80,
        genome_presets=[
            # 50% Faction A: fast, aggressive, small — red-hued raiders
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.5, [0.75, 0.6, 0.75, 0.4, 0.5, 0.5, 0.35, 0.4, 0.95, 0.15, 0.1]),
            # 50% Faction B: slower, aggressive, large — blue-hued defenders
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.5, [0.4, 0.65, 0.7, 0.75, 0.55, 0.55, 0.35, 0.5, 0.1, 0.2, 0.9]),
        ],
    ),
    "symbiosis": Scenario(
        name="Symbiosis",
        description="Three peaceful species — watch cross-species mutualism emerge",
        width=60, height=30, pop=36, food_rate=3,
        enable_events=False, enable_terrain=False, terrain_seed=None, ticks=600,
        day_length=120,
        genome_presets=[
            # 33% Species A: slow, passive, efficient, large — green grazers
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.34, [0.25, 0.5, 0.1, 0.7, 0.8, 0.6, 0.3, 0.6, 0.2, 0.85, 0.2]),
            # 33% Species B: medium speed, passive, small — yellow foragers
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.33, [0.5, 0.6, 0.15, 0.4, 0.6, 0.55, 0.3, 0.5, 0.9, 0.8, 0.1]),
            # 33% Species C: fast, passive, medium — cyan scouts
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.33, [0.7, 0.7, 0.05, 0.5, 0.5, 0.5, 0.3, 0.7, 0.1, 0.7, 0.9]),
        ],
    ),
    "ecosystem": Scenario(
        name="Ecosystem",
        description="Full ecosystem — predators, grazers, scouts, and defenders with terrain and events",
        width=100, height=50, pop=60, food_rate=7,
        enable_events=True, enable_terrain=True, terrain_seed=256, ticks=800,
        day_length=100,
        genome_presets=[
            # 20% Apex predators: fast, aggressive, small, low repro — red hunters
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.20, [0.85, 0.75, 0.9, 0.35, 0.4, 0.5, 0.3, 0.3, 0.95, 0.1, 0.1]),
            # 35% Grazers: slow, passive, large, efficient, high memory — green herders
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.35, [0.25, 0.5, 0.1, 0.75, 0.8, 0.6, 0.25, 0.7, 0.15, 0.85, 0.2]),
            # 25% Scouts: fast, passive, small, high sense, good memory — cyan explorers
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.25, [0.7, 0.8, 0.15, 0.4, 0.55, 0.5, 0.3, 0.8, 0.1, 0.65, 0.9]),
            # 20% Defenders: medium, territorial, large, sturdy — purple sentinels
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.20, [0.4, 0.6, 0.5, 0.7, 0.6, 0.55, 0.3, 0.5, 0.6, 0.2, 0.8]),
        ],
    ),
    "biomes": Scenario(
        name="Biomes",
        description="Hot, cold, toxic, and fertile zones — organisms must adapt to survive their environment",
        width=80, height=40, pop=30, food_rate=5,
        enable_events=False, enable_terrain=True, terrain_seed=404, ticks=700,
        day_length=120,
        genome_presets=[
            # 25% Desert runners: fast, small, efficient — built for hot zones
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.25, [0.85, 0.5, 0.2, 0.3, 0.7, 0.5, 0.4, 0.4, 0.95, 0.6, 0.1]),
            # 25% Arctic tanks: slow, large, durable — built for cold zones
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.25, [0.2, 0.6, 0.15, 0.85, 0.6, 0.65, 0.3, 0.5, 0.3, 0.5, 0.95]),
            # 25% Generalists: medium everything — survive anywhere
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.25, [0.5, 0.5, 0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.9, 0.3]),
            # 25% Toxic specialists: high efficiency — thrive where others can't
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.25, [0.4, 0.4, 0.25, 0.5, 0.95, 0.6, 0.35, 0.6, 0.6, 0.2, 0.6]),
        ],
    ),
    "swarm": Scenario(
        name="Swarm",
        description="Massive population in tiny arena — pure chaos, rapid evolution, extreme selection pressure",
        width=40, height=25, pop=80, food_rate=6,
        enable_events=False, enable_terrain=False, terrain_seed=None, ticks=500,
        day_length=80,
    ),
    "gladiator": Scenario(
        name="Gladiator",
        description="Small combat pit with two ultra-aggressive factions — fight to extinction",
        width=30, height=20, pop=30, food_rate=3,
        enable_events=False, enable_terrain=True, terrain_seed=55, ticks=400,
        day_length=60,
        genome_presets=[
            # 50% Berserkers: max aggro, fast, small — glass cannons
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.5, [0.9, 0.6, 0.95, 0.3, 0.3, 0.45, 0.4, 0.2, 1.0, 0.15, 0.05]),
            # 50% Juggernauts: high aggro, slow, huge — damage sponges
            #                     SPD  SENS AGG  SIZE EFF  REP  MUT  MEM  R    G    B
            (0.5, [0.2, 0.5, 0.85, 0.95, 0.5, 0.6, 0.3, 0.3, 0.1, 0.15, 0.95]),
        ],
    ),
}


def list_scenarios() -> str:
    lines = ["Available scenarios:", ""]
    for key, sc in SCENARIOS.items():
        lines.append(f"  {key:12s}  {sc.description}")
    return "\n".join(lines)
