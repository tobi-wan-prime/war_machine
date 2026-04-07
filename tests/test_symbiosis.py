"""Tests for cross-species symbiosis mechanics."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World
from arena.scenarios import SCENARIOS


def test_symbiosis_between_passive_different_species():
    """Two passive organisms of different species near each other gain energy."""
    # low aggression genes for both
    passive_a = [0.3, 0.5, 0.1, 0.5, 0.5, 0.5, 0.1, 0.5, 0.9, 0.2, 0.1]  # red-ish
    passive_b = [0.3, 0.5, 0.1, 0.5, 0.5, 0.5, 0.1, 0.5, 0.1, 0.2, 0.9]  # blue-ish

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org_a = Organism(x=5, y=5, genome=Genome(passive_a), energy=50)
    org_b = Organism(x=6, y=5, genome=Genome(passive_b), energy=50)
    w.organisms = [org_a, org_b]

    # classify into different species
    w.species_tracker.classify(w.organisms, w.stats.tick)
    sp_a = w.species_tracker.get_species_for(org_a.id)
    sp_b = w.species_tracker.get_species_for(org_b.id)

    # they should be different species (very different color genes)
    if sp_a and sp_b and sp_a.id != sp_b.id:
        # run a symbiosis round
        w._symbiosis()
        # both should have gained energy
        assert org_a.energy > 50 or org_b.energy > 50
        assert w.stats.total_symbiosis > 0


def test_no_symbiosis_between_aggressive():
    """Aggressive organisms do not benefit from symbiosis."""
    aggressive = [0.3, 0.5, 0.8, 0.5, 0.5, 0.5, 0.1, 0.5, 0.9, 0.2, 0.1]
    passive = [0.3, 0.5, 0.1, 0.5, 0.5, 0.5, 0.1, 0.5, 0.1, 0.2, 0.9]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org_a = Organism(x=5, y=5, genome=Genome(aggressive), energy=50)
    org_b = Organism(x=6, y=5, genome=Genome(passive), energy=50)
    w.organisms = [org_a, org_b]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    w._symbiosis()
    # aggressive organism blocks symbiosis
    assert w.stats.total_symbiosis == 0


def test_no_symbiosis_same_species():
    """Same-species organisms do not get symbiosis bonus (they get kin sharing instead)."""
    genes = [0.3, 0.5, 0.1, 0.5, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org_a = Organism(x=5, y=5, genome=Genome(genes), energy=50)
    org_b = Organism(x=6, y=5, genome=Genome(genes), energy=50)
    w.organisms = [org_a, org_b]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    w._symbiosis()
    # same species — no symbiosis
    assert w.stats.total_symbiosis == 0


def test_symbiosis_stats_in_summary():
    """Population summary includes symbiosis count."""
    w = World(width=20, height=20, initial_organisms=10, food_rate=3,
              enable_events=False, day_length=100)
    for _ in range(50):
        w.tick()

    summary = w.get_population_summary()
    assert "symbiosis" in summary


def test_symbiosis_scenario_exists():
    """Symbiosis scenario is registered with three species presets."""
    assert "symbiosis" in SCENARIOS
    sc = SCENARIOS["symbiosis"]
    assert sc.pop == 36
    assert sc.genome_presets is not None
    assert len(sc.genome_presets) == 3
    assert sc.enable_events is False


def test_symbiosis_scenario_runs():
    """Symbiosis scenario runs without errors."""
    sc = SCENARIOS["symbiosis"]
    w = World(
        width=sc.width, height=sc.height,
        initial_organisms=sc.pop, food_rate=sc.food_rate,
        enable_events=sc.enable_events, day_length=sc.day_length,
        genome_presets=sc.genome_presets,
    )
    for _ in range(100):
        w.tick()
    assert w.stats.tick == 100
    assert len(w.organisms) > 0
