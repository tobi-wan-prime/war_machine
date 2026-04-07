"""Tests for organism memory system."""

from arena.genome import Genome, MEMORY
from arena.organism import Organism


def _make_org(memory_gene: float = 0.5) -> Organism:
    g = Genome.random()
    g.genes[MEMORY] = memory_gene
    return Organism(x=10.0, y=10.0, genome=g)


def test_memory_capacity_gene():
    """Memory capacity scales with the memory gene."""
    # MEMORY is gene index 7
    g_low = Genome(genes=[0.5] * 7 + [0.0] + [0.5] * 3)   # MEMORY=0.0
    g_high = Genome(genes=[0.5] * 7 + [1.0] + [0.5] * 3)  # MEMORY=1.0
    assert g_low.memory_capacity == 1
    assert g_high.memory_capacity == 8


def test_remember_and_recall_food():
    """Organism can remember and recall food locations."""
    org = _make_org(memory_gene=0.5)
    org.remember_food(20.0, 30.0, tick=10)
    result = org.recall_food(current_tick=15)
    assert result is not None
    assert result == (20.0, 30.0)


def test_recall_food_expires():
    """Food memory expires after max_age ticks."""
    org = _make_org(memory_gene=0.5)
    org.remember_food(20.0, 30.0, tick=10)
    result = org.recall_food(current_tick=200, max_age=80)
    assert result is None


def test_remember_danger():
    """Organism can remember and recall danger locations."""
    org = _make_org(memory_gene=0.5)
    org.remember_danger(5.0, 5.0, tick=10)
    org.remember_danger(15.0, 15.0, tick=12)
    dangers = org.recall_danger(current_tick=20)
    assert len(dangers) == 2


def test_memory_capacity_limits():
    """Memory evicts oldest entries when over capacity."""
    org = _make_org(memory_gene=0.0)  # capacity=1
    assert org.genome.memory_capacity == 1
    org.remember_food(10.0, 10.0, tick=1)
    org.remember_food(20.0, 20.0, tick=2)
    result = org.recall_food(current_tick=5)
    assert result == (20.0, 20.0)  # only the newer one survives


def test_forget_old():
    """forget_old prunes expired memories."""
    org = _make_org(memory_gene=1.0)  # capacity=8
    org.remember_food(10.0, 10.0, tick=1)
    org.remember_danger(20.0, 20.0, tick=2)
    org.remember_food(30.0, 30.0, tick=200)
    org.forget_old(current_tick=200, max_age=100)
    # first two should be forgotten, third should remain
    assert org.recall_food(current_tick=200) == (30.0, 30.0)
    assert len(org.recall_danger(current_tick=200)) == 0


def test_memory_metabolic_cost():
    """Higher memory capacity increases metabolic cost."""
    g_low = Genome(genes=[0.5] * 7 + [0.0] + [0.5] * 3)
    g_high = Genome(genes=[0.5] * 7 + [1.0] + [0.5] * 3)
    o_low = Organism(x=0, y=0, genome=g_low)
    o_high = Organism(x=0, y=0, genome=g_high)
    assert o_high.energy_cost_per_tick > o_low.energy_cost_per_tick


def test_memory_not_inherited():
    """Children don't inherit parent memories."""
    org = _make_org(memory_gene=0.5)
    org.remember_food(20.0, 30.0, tick=10)
    org.energy = 200  # enough to reproduce
    child = org.reproduce(80, 40)
    assert child.recall_food(current_tick=15) is None
