"""Tests for environmental zones (hot, cold, toxic trait-dependent effects)."""

from arena.genome import Genome
from arena.organism import Organism
from arena.terrain import Terrain, TileType
from arena.world import World
from arena.scenarios import SCENARIOS


def test_hot_zone_exists_in_tiletype():
    """HOT tile type is defined."""
    assert hasattr(TileType, 'HOT')


def test_cold_zone_exists_in_tiletype():
    """COLD tile type is defined."""
    assert hasattr(TileType, 'COLD')


def test_terrain_generates_hot_cold():
    """Generated terrain can contain hot and cold zones."""
    # use seed that generates hot/cold zones
    found_hot = False
    found_cold = False
    for seed in range(20):
        t = Terrain.generate(80, 40, seed=seed)
        for row in t.tiles:
            for tile in row:
                if tile == TileType.HOT:
                    found_hot = True
                if tile == TileType.COLD:
                    found_cold = True
        if found_hot and found_cold:
            break
    assert found_hot, "No HOT zones generated in 20 seeds"
    assert found_cold, "No COLD zones generated in 20 seeds"


def test_hot_zone_hurts_slow():
    """Slow organisms lose energy in hot zones."""
    slow_genes = [0.1, 0.5, 0.2, 0.5, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]
    org = Organism(x=5, y=5, genome=Genome(slow_genes), energy=100)

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, enable_terrain=True, terrain_seed=1, day_length=100)
    # manually set the tile under organism to HOT
    w.terrain.tiles[5][5] = TileType.HOT
    w.organisms = [org]

    initial_energy = org.energy
    w.tick()
    # slow organism should lose more energy than normal metabolism
    # (metabolism alone drains ~0.6-0.8 per tick for this genome)
    assert org.energy < initial_energy - 1.0


def test_cold_zone_hurts_small():
    """Small organisms lose energy in cold zones."""
    small_genes = [0.5, 0.5, 0.2, 0.1, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]
    org = Organism(x=5, y=5, genome=Genome(small_genes), energy=100)

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, enable_terrain=True, terrain_seed=1, day_length=100)
    w.terrain.tiles[5][5] = TileType.COLD
    w.organisms = [org]

    initial_energy = org.energy
    w.tick()
    assert org.energy < initial_energy - 1.0


def test_toxic_mitigated_by_efficiency():
    """High-efficiency organisms take less toxic damage than low-efficiency ones."""
    low_eff = [0.5, 0.5, 0.2, 0.5, 0.0, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]
    high_eff = [0.5, 0.5, 0.2, 0.5, 1.0, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]

    org_low = Organism(x=5, y=5, genome=Genome(low_eff), energy=100)
    org_high = Organism(x=5, y=5, genome=Genome(high_eff), energy=100)

    w1 = World(width=20, height=20, initial_organisms=0, food_rate=0,
               enable_events=False, enable_terrain=True, terrain_seed=1, day_length=100)
    w1.terrain.tiles[5][5] = TileType.TOXIC
    w1.organisms = [org_low]
    w1.tick()

    w2 = World(width=20, height=20, initial_organisms=0, food_rate=0,
               enable_events=False, enable_terrain=True, terrain_seed=1, day_length=100)
    w2.terrain.tiles[5][5] = TileType.TOXIC
    w2.organisms = [org_high]
    w2.tick()

    # high efficiency organism should retain more energy
    assert org_high.energy > org_low.energy


def test_biomes_scenario_exists():
    """Biomes scenario is defined."""
    assert "biomes" in SCENARIOS


def test_biomes_scenario_runs():
    """Biomes scenario runs without error."""
    sc = SCENARIOS["biomes"]
    w = World(width=sc.width, height=sc.height, initial_organisms=sc.pop,
              food_rate=sc.food_rate, enable_events=sc.enable_events,
              enable_terrain=sc.enable_terrain, terrain_seed=sc.terrain_seed,
              day_length=sc.day_length, genome_presets=sc.genome_presets)
    for _ in range(100):
        w.tick()
    assert w.stats.tick == 100
