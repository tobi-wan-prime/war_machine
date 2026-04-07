"""Tests for the day/night cycle system."""

import math
from arena.world import World
from arena.genome import Genome
from arena.organism import Organism


def test_time_of_day_cycles():
    """Time of day cycles from 0 to 1 over day_length ticks."""
    w = World(width=20, height=20, initial_organisms=5, food_rate=3, day_length=100)
    assert w.time_of_day == 0.0  # tick 0

    for _ in range(25):
        w.tick()
    assert abs(w.time_of_day - 0.25) < 0.02

    for _ in range(25):
        w.tick()
    assert abs(w.time_of_day - 0.50) < 0.02

    for _ in range(50):
        w.tick()
    # should wrap around to 0
    assert abs(w.time_of_day - 0.0) < 0.02


def test_light_level_range():
    """Light level stays in [0, 1] and peaks at noon."""
    w = World(width=20, height=20, initial_organisms=5, food_rate=3, day_length=100)

    # run a full cycle and track min/max
    levels = []
    for _ in range(100):
        w.tick()
        levels.append(w.light_level)

    assert min(levels) >= 0.0
    assert max(levels) <= 1.0
    assert max(levels) > 0.9  # should reach near-full brightness


def test_is_night():
    """Night detection works correctly."""
    w = World(width=20, height=20, initial_organisms=5, food_rate=3, day_length=100)
    # tick 0 = time_of_day 0.0 — should be night
    assert w.is_night

    # tick 50 = time_of_day 0.5 — should be day
    for _ in range(50):
        w.tick()
    assert not w.is_night


def test_effective_sense_reduces_at_night():
    """Effective sense range is reduced during night."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=3, day_length=100)

    # create a test organism with medium sense range
    org = Organism(x=10.0, y=10.0, genome=Genome.random())

    # at midnight (tick 0, light ~0)
    night_sense = w.effective_sense(org)

    # advance to noon
    for _ in range(50):
        w.tick()
    day_sense = w.effective_sense(org)

    assert day_sense > night_sense, f"Day sense {day_sense} should exceed night sense {night_sense}"


def test_effective_sense_high_gene_retains_more():
    """Organisms with high sense_range gene retain more vision at night."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=3, day_length=100)
    # tick 0 = midnight

    g_sharp = Genome(genes=[0.5] * 11)
    g_sharp.genes[1] = 1.0  # max sense_range gene
    org_sharp = Organism(x=10.0, y=10.0, genome=g_sharp)

    g_dull = Genome(genes=[0.5] * 11)
    g_dull.genes[1] = 0.0  # min sense_range gene
    org_dull = Organism(x=10.0, y=10.0, genome=g_dull)

    night_sharp = w.effective_sense(org_sharp)
    night_dull = w.effective_sense(org_dull)

    # sharp-eyed organism should retain more vision at night
    # (note: base sense_range also differs since it's derived from genes[1])
    # but the ratio of effective/base should be higher for sharp eyes
    ratio_sharp = night_sharp / org_sharp.genome.sense_range
    ratio_dull = night_dull / org_dull.genome.sense_range
    assert ratio_sharp > ratio_dull, f"Sharp ratio {ratio_sharp} should exceed dull ratio {ratio_dull}"


def test_summary_includes_time():
    """Population summary includes time_of_day and light_level."""
    w = World(width=20, height=20, initial_organisms=5, food_rate=3, day_length=100)
    w.tick()
    s = w.get_population_summary()
    assert "time_of_day" in s
    assert "light_level" in s
    assert 0 <= s["time_of_day"] <= 1
    assert 0 <= s["light_level"] <= 1
