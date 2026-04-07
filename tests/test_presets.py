"""Tests for genome presets and predator vs prey scenario."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World
from arena.scenarios import SCENARIOS


def test_predator_prey_scenario_exists():
    """Predator vs prey scenario is registered."""
    assert "predator_prey" in SCENARIOS
    sc = SCENARIOS["predator_prey"]
    assert sc.pop == 40
    assert sc.genome_presets is not None
    assert len(sc.genome_presets) == 2


def test_genome_presets_seed_populations():
    """World with genome presets creates organisms with specified traits."""
    # predators: high aggression (gene 2)
    # prey: low aggression (gene 2)
    presets = [
        (0.5, [0.8, 0.5, 0.9, 0.3, 0.5, 0.5, 0.3, 0.3, 0.5, 0.5, 0.5]),  # aggressive
        (0.5, [0.3, 0.5, 0.1, 0.8, 0.5, 0.5, 0.3, 0.5, 0.5, 0.5, 0.5]),  # passive
    ]
    w = World(width=20, height=20, initial_organisms=20, food_rate=3,
              enable_events=False, day_length=100, genome_presets=presets)

    assert len(w.organisms) == 20

    # should have a mix of aggressive and passive organisms
    high_aggro = [o for o in w.organisms if o.genome.aggression > 0.5]
    low_aggro = [o for o in w.organisms if o.genome.aggression < 0.5]
    assert len(high_aggro) >= 5  # ~50% should be aggressive
    assert len(low_aggro) >= 5   # ~50% should be passive


def test_genome_presets_none_uses_random():
    """When genome_presets is None, random genomes are used (default behavior)."""
    w = World(width=20, height=20, initial_organisms=10, food_rate=3,
              enable_events=False, day_length=100, genome_presets=None)
    assert len(w.organisms) == 10
    # random genomes should have varied aggression levels
    aggros = [o.genome.aggression for o in w.organisms]
    assert max(aggros) != min(aggros)  # not all identical


def test_genome_presets_variation():
    """Preset organisms have small random variation from template."""
    template = [0.5] * 11
    presets = [(1.0, template)]
    w = World(width=20, height=20, initial_organisms=10, food_rate=3,
              enable_events=False, day_length=100, genome_presets=presets)

    # all organisms should be close to 0.5 but not exactly identical
    speeds = [o.genome.genes[0] for o in w.organisms]
    assert all(0.3 < s < 0.7 for s in speeds)  # within variation range
    # at least some should differ (random gaussian noise)
    assert len(set(round(s, 4) for s in speeds)) > 1


def test_predator_prey_simulation_runs():
    """Predator vs prey scenario runs without errors."""
    sc = SCENARIOS["predator_prey"]
    w = World(
        width=sc.width, height=sc.height,
        initial_organisms=sc.pop, food_rate=sc.food_rate,
        enable_events=sc.enable_events, day_length=sc.day_length,
        genome_presets=sc.genome_presets,
    )
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    assert len(w.organisms) > 0


def test_war_scenario_exists():
    """War scenario is registered with two factions."""
    assert "war" in SCENARIOS
    sc = SCENARIOS["war"]
    assert sc.pop == 40
    assert sc.genome_presets is not None
    assert len(sc.genome_presets) == 2
    assert sc.enable_terrain is True


def test_war_simulation_runs():
    """War scenario runs without errors."""
    sc = SCENARIOS["war"]
    w = World(
        width=sc.width, height=sc.height,
        initial_organisms=sc.pop, food_rate=sc.food_rate,
        enable_events=sc.enable_events,
        enable_terrain=sc.enable_terrain,
        terrain_seed=sc.terrain_seed,
        day_length=sc.day_length,
        genome_presets=sc.genome_presets,
    )
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    assert len(w.organisms) > 0


def test_ecosystem_scenario_exists():
    """Ecosystem scenario is registered with four species presets."""
    assert "ecosystem" in SCENARIOS
    sc = SCENARIOS["ecosystem"]
    assert sc.pop == 60
    assert sc.genome_presets is not None
    assert len(sc.genome_presets) == 4
    assert sc.enable_terrain is True
    assert sc.enable_events is True


def test_ecosystem_simulation_runs():
    """Ecosystem scenario runs without errors."""
    sc = SCENARIOS["ecosystem"]
    w = World(
        width=sc.width, height=sc.height,
        initial_organisms=sc.pop, food_rate=sc.food_rate,
        enable_events=sc.enable_events,
        enable_terrain=sc.enable_terrain,
        terrain_seed=sc.terrain_seed,
        day_length=sc.day_length,
        genome_presets=sc.genome_presets,
    )
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    assert len(w.organisms) > 0


def test_swarm_scenario_exists():
    """Swarm scenario is registered with correct parameters."""
    assert "swarm" in SCENARIOS
    sc = SCENARIOS["swarm"]
    assert sc.pop == 80
    assert sc.width == 40
    assert sc.height == 25
    assert sc.genome_presets is None  # random genomes


def test_swarm_simulation_runs():
    """Swarm scenario runs without errors despite extreme density."""
    sc = SCENARIOS["swarm"]
    w = World(
        width=sc.width, height=sc.height,
        initial_organisms=sc.pop, food_rate=sc.food_rate,
        enable_events=sc.enable_events, day_length=sc.day_length,
    )
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    assert len(w.organisms) > 0


def test_gladiator_scenario_exists():
    """Gladiator scenario is registered with two ultra-aggressive factions."""
    assert "gladiator" in SCENARIOS
    sc = SCENARIOS["gladiator"]
    assert sc.pop == 30
    assert sc.genome_presets is not None
    assert len(sc.genome_presets) == 2
    assert sc.enable_terrain is True
    # both factions should be highly aggressive (gene index 2)
    for frac, genes in sc.genome_presets:
        assert genes[2] >= 0.85  # aggression


def test_gladiator_simulation_runs():
    """Gladiator scenario runs without errors."""
    sc = SCENARIOS["gladiator"]
    w = World(
        width=sc.width, height=sc.height,
        initial_organisms=sc.pop, food_rate=sc.food_rate,
        enable_events=sc.enable_events,
        enable_terrain=sc.enable_terrain,
        terrain_seed=sc.terrain_seed,
        day_length=sc.day_length,
        genome_presets=sc.genome_presets,
    )
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    # high-aggro scenario may have heavy casualties but should have some survivors
    assert w.stats.total_kills > 0
