"""Tests for organism genealogy (parent tracking, offspring counting)."""

from arena.genome import Genome
from arena.organism import Organism


def test_initial_organism_has_no_parent():
    """Organisms created without parents have parent_id=0."""
    o = Organism(x=5, y=5, genome=Genome.random())
    assert o.parent_id == 0


def test_initial_organism_has_no_children():
    """Fresh organisms start with children=0."""
    o = Organism(x=5, y=5, genome=Genome.random())
    assert o.children == 0


def test_asexual_child_has_parent_id():
    """Asexual reproduction sets child's parent_id to parent's id."""
    parent = Organism(x=5, y=5, genome=Genome.random(), energy=200)
    child = parent.reproduce(20, 20)
    assert child.parent_id == parent.id


def test_asexual_increments_children():
    """Asexual reproduction increments parent's children count."""
    parent = Organism(x=5, y=5, genome=Genome.random(), energy=200)
    parent.reproduce(20, 20)
    assert parent.children == 1
    parent.energy = 200
    parent.reproduce(20, 20)
    assert parent.children == 2


def test_sexual_child_has_parent_id():
    """Sexual reproduction sets child's parent_id to the initiating parent."""
    mom = Organism(x=5, y=5, genome=Genome.random(), energy=200)
    dad = Organism(x=6, y=5, genome=Genome.random(), energy=200)
    child = mom.mate(dad, 20, 20)
    assert child.parent_id == mom.id


def test_sexual_increments_both_parents():
    """Sexual reproduction increments children count on both parents."""
    mom = Organism(x=5, y=5, genome=Genome.random(), energy=200)
    dad = Organism(x=6, y=5, genome=Genome.random(), energy=200)
    mom.mate(dad, 20, 20)
    assert mom.children == 1
    assert dad.children == 1


def test_child_generation_is_parent_plus_one():
    """Child generation is parent generation + 1."""
    parent = Organism(x=5, y=5, genome=Genome.random(), energy=200, generation=3)
    child = parent.reproduce(20, 20)
    assert child.generation == 4


def test_genealogy_exported():
    """Parent ID and children count appear in replay frame data."""
    from arena.exporter import ReplayExporter
    from arena.world import World

    w = World(width=30, height=30, initial_organisms=15, food_rate=5,
              enable_events=False, day_length=100)
    exporter = ReplayExporter(sample_rate=2)
    exporter.set_config(w)

    for _ in range(100):
        w.tick()
        exporter.capture(w)

    # check that at least some frame has organisms with pid and ch fields
    found = False
    for frame in exporter.frames:
        for o in frame.organisms:
            if "pid" in o and "ch" in o:
                found = True
                break
        if found:
            break
    assert found, "Expected pid and ch fields in exported organism data"
