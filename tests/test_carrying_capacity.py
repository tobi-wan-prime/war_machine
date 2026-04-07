"""Tests for carrying capacity (population-dependent food spawning)."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def test_overpopulated_reduces_food():
    """When population density is high, fewer food items spawn."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=10,
              enable_events=False, day_length=100)
    # Pack with many organisms — density > 0.03 (>12 in 400 cells)
    for i in range(20):
        w.organisms.append(Organism(x=10, y=10, genome=Genome.random(), energy=100))
    w.food.clear()

    w.tick()
    food_high_pop = len(w.food)

    # now with fewer organisms — density < 0.03
    w2 = World(width=20, height=20, initial_organisms=0, food_rate=10,
               enable_events=False, day_length=100)
    w2.organisms.append(Organism(x=10, y=10, genome=Genome.random(), energy=100))
    w2.food.clear()

    w2.tick()
    food_low_pop = len(w2.food)

    # higher population should produce less food
    assert food_high_pop < food_low_pop


def test_underpopulated_boosts_food():
    """When population density is very low, more food spawns to help recovery."""
    # Very sparse: density < 0.008 (< ~5 in 80x40=3200 cells)
    w = World(width=80, height=40, initial_organisms=0, food_rate=5,
              enable_events=False, day_length=100)
    w.organisms.append(Organism(x=40, y=20, genome=Genome.random(), energy=100))
    w.food.clear()

    w.tick()
    food_sparse = len(w.food)

    # moderate pop: not in either threshold
    w2 = World(width=80, height=40, initial_organisms=0, food_rate=5,
               enable_events=False, day_length=100)
    for i in range(50):
        w2.organisms.append(Organism(x=40, y=20, genome=Genome.random(), energy=100))
    w2.food.clear()

    w2.tick()
    food_moderate = len(w2.food)

    # sparse population should get equal or more food than moderate
    assert food_sparse >= food_moderate


def test_carrying_capacity_simulation_stability():
    """Simulation remains stable with carrying capacity active."""
    w = World(width=40, height=40, initial_organisms=30, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(200):
        w.tick()
    # population should still exist (carrying capacity shouldn't crash it)
    assert len(w.organisms) > 0 or w.stats.total_born > 0
