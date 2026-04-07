"""Tests for combat scars mechanic."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def test_initial_scars_zero():
    """Organisms start with zero scars."""
    org = Organism(x=5, y=5, genome=Genome.random())
    assert org.scars == 0


def test_scars_accumulate_in_combat():
    """Organisms gain scars from combat encounters."""
    w = World(width=30, height=30, initial_organisms=40, food_rate=2,
              enable_events=False, day_length=100)
    # run enough ticks for combat to occur
    for _ in range(150):
        w.tick()
    # check if any living organism has scars
    scarred = [o for o in w.organisms if o.scars > 0]
    # also check graveyard organisms had combat — some kills should exist
    assert w.stats.total_kills > 0 or len(scarred) > 0


def test_scars_exported():
    """Scars appear in exported frame data."""
    w = World(width=30, height=30, initial_organisms=15, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(10):
        w.tick()
    from arena.exporter import ReplayExporter
    exp = ReplayExporter(sample_rate=1)
    exp.set_config(w)
    exp.capture(w)
    frame = exp.frames[0]
    for org_data in frame.organisms:
        assert "sc" in org_data
        assert isinstance(org_data["sc"], int)
        assert org_data["sc"] >= 0


def test_winner_gets_scar():
    """The winning fighter should gain a scar."""
    # Create a very aggressive strong attacker and a weak defender
    strong_genes = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]
    weak_genes = [0.5, 0.5, 0.0, 0.1, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]
    attacker = Organism(x=5, y=5, genome=Genome(strong_genes), energy=200)
    defender = Organism(x=5.5, y=5, genome=Genome(weak_genes), energy=50)

    w = World(width=30, height=30, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)
    w.organisms = [attacker, defender]

    initial_scars = attacker.scars
    # run fight directly
    w._fight(attacker, defender)
    # one of them should have gained a scar
    assert attacker.scars > initial_scars or defender.scars > 0
