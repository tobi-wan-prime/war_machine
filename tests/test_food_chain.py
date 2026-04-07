"""Tests for food chain (species-level kill tracking)."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def test_food_chain_initially_empty():
    """Food chain starts empty."""
    w = World(width=20, height=20, initial_organisms=10, food_rate=3,
              enable_events=False, day_length=100)
    assert w.stats.food_chain == {}


def test_food_chain_records_kills():
    """After combat, food chain records killer/victim species pairs."""
    # create aggressive and passive organisms with very different genomes
    aggressive = [0.5, 0.7, 0.95, 0.9, 0.5, 0.5, 0.1, 0.5, 0.95, 0.05, 0.05]
    passive = [0.3, 0.5, 0.05, 0.2, 0.5, 0.5, 0.1, 0.5, 0.05, 0.05, 0.95]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    org_a = Organism(x=5, y=5, genome=Genome(aggressive), energy=100)
    org_b = Organism(x=5.5, y=5, genome=Genome(passive), energy=50)
    w.organisms = [org_a, org_b]
    w.species_tracker.classify(w.organisms, w.stats.tick)

    # fight until someone dies
    for _ in range(50):
        w._fight(org_a, org_b)
        if not org_a.alive or not org_b.alive:
            break

    # food chain should have at least one entry if a kill happened
    if w.stats.total_kills > 0:
        assert len(w.stats.food_chain) > 0
        # all values should be positive
        for v in w.stats.food_chain.values():
            assert v > 0


def test_food_chain_in_simulation():
    """Food chain accumulates during a full simulation with combat."""
    w = World(width=30, height=30, initial_organisms=20, food_rate=3,
              enable_events=False, day_length=100)
    for _ in range(200):
        w.tick()

    # if any kills happened, food chain should have entries
    if w.stats.total_kills > 0:
        assert len(w.stats.food_chain) > 0


def test_food_chain_exported():
    """Food chain data appears in exporter output."""
    from arena.exporter import ReplayExporter

    w = World(width=30, height=30, initial_organisms=15, food_rate=3,
              enable_events=False, day_length=100)
    exporter = ReplayExporter(sample_rate=2)
    exporter.set_config(w)

    for _ in range(100):
        w.tick()
        exporter.capture(w)

    exporter.finalize(w)

    # food chain should be in config
    assert "food_chain" in exporter.config
    assert isinstance(exporter.config["food_chain"], list)

    # each entry should have k, v, n keys
    for entry in exporter.config["food_chain"]:
        assert "k" in entry
        assert "v" in entry
        assert "n" in entry
        assert entry["n"] > 0
