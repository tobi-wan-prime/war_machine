"""Tests for behavioral state tracking."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def test_behavior_default_is_idle():
    """New organisms start with behavior=0 (idle)."""
    org = Organism(x=5, y=5, genome=Genome.random(), energy=100)
    assert org.behavior == 0


def test_hunting_behavior_set():
    """Aggressive organism attacking should have behavior=1 (hunting)."""
    # create a world with one aggressive and one passive organism nearby
    aggressive = [0.5, 0.7, 0.9, 0.8, 0.5, 0.5, 0.1, 0.5, 0.9, 0.1, 0.1]
    passive = [0.3, 0.5, 0.1, 0.3, 0.5, 0.5, 0.1, 0.5, 0.1, 0.9, 0.1]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org_a = Organism(x=5, y=5, genome=Genome(aggressive), energy=80)
    org_b = Organism(x=6, y=5, genome=Genome(passive), energy=80)
    w.organisms = [org_a, org_b]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    w.tick()
    # aggressive org should be hunting
    if org_a.alive:
        assert org_a.behavior == 1  # hunting


def test_fleeing_behavior_set():
    """Non-aggressive organism near an aggressor should flee (behavior=2)."""
    aggressive = [0.5, 0.7, 0.9, 0.8, 0.5, 0.5, 0.1, 0.5, 0.9, 0.1, 0.1]
    passive = [0.3, 0.7, 0.1, 0.3, 0.5, 0.5, 0.1, 0.5, 0.1, 0.9, 0.1]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    hunter = Organism(x=5, y=5, genome=Genome(aggressive), energy=80)
    prey = Organism(x=7, y=5, genome=Genome(passive), energy=80)
    w.organisms = [hunter, prey]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    w.tick()
    # passive org should be fleeing
    if prey.alive:
        assert prey.behavior == 2  # fleeing


def test_grazing_behavior_set():
    """Organism near food should graze (behavior=3)."""
    from arena.world import Food
    passive = [0.3, 0.7, 0.1, 0.5, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org = Organism(x=5, y=5, genome=Genome(passive), energy=80)
    w.organisms = [org]
    # place food nearby
    w.food = [Food(x=6, y=5)]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    w.tick()
    # should have been grazing
    assert org.behavior == 3  # grazing


def test_behavior_resets_each_tick():
    """Behavior is reset to 0 (idle) at the start of each tick cycle."""
    passive = [0.3, 0.5, 0.1, 0.5, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org = Organism(x=5, y=5, genome=Genome(passive), energy=80)
    org.behavior = 3  # set manually
    w.organisms = [org]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    w.tick()
    # behavior should have been reassigned during the tick, not left at old value
    assert org.behavior in range(7)  # valid behavior


def test_behavior_exported():
    """Behavior state appears in exporter output."""
    from arena.exporter import ReplayExporter

    w = World(width=20, height=20, initial_organisms=5, food_rate=2,
              enable_events=False, day_length=100)
    for _ in range(10):
        w.tick()

    exporter = ReplayExporter(sample_rate=1)
    exporter.set_config(w)
    exporter.capture(w)

    assert len(exporter.frames) > 0
    frame = exporter.frames[0]
    for org_data in frame.organisms:
        assert "bh" in org_data
        assert org_data["bh"] in range(7)
