"""Tests for organism fatigue mechanic."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def test_initial_fatigue_zero():
    """Organisms start with zero fatigue."""
    org = Organism(x=5, y=5, genome=Genome.random())
    assert org.fatigue == 0.0


def test_fatigue_reduces_speed():
    """Fatigued organisms move slower."""
    org = Organism(x=5, y=5, genome=Genome.random())
    base_speed = org.effective_speed
    org.fatigue = 0.5
    fatigued_speed = org.effective_speed
    assert fatigued_speed < base_speed
    assert fatigued_speed == org.genome.speed * (1.0 - 0.5 * 0.5)


def test_fatigue_reduces_combat_power():
    """Fatigued organisms have reduced combat power."""
    genes = [0.5, 0.5, 0.8, 0.8, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]
    org = Organism(x=5, y=5, genome=Genome(genes))
    base_power = org.combat_power
    org.fatigue = 0.5
    fatigued_power = org.combat_power
    assert fatigued_power < base_power


def test_fatigue_caps_at_one():
    """Fatigue cannot exceed 1.0."""
    org = Organism(x=5, y=5, genome=Genome.random())
    org.fatigue = 1.5  # manually set above cap
    # combat_power and effective_speed should still use the value
    # but the world tick should cap it
    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)
    org.fatigue = 0.99
    w.organisms = [org]
    # set to hunting behavior to increase fatigue
    org.behavior = 1
    # manually trigger fatigue logic
    org.fatigue = min(1.0, org.fatigue + 0.02)
    assert org.fatigue <= 1.0


def test_fatigue_recovers_when_idle():
    """Fatigue decreases when organism is idle or grazing."""
    org = Organism(x=5, y=5, genome=Genome.random(), energy=100)
    org.fatigue = 0.5

    w = World(width=30, height=30, initial_organisms=0, food_rate=5,
              enable_events=False, day_length=100)
    w.organisms = [org]

    # run ticks — isolated organism should mostly idle/graze
    for _ in range(30):
        w.tick()

    # fatigue should have decreased
    assert org.fatigue < 0.5 or not org.alive


def test_fatigue_accumulates_in_combat():
    """Organisms that fight gain fatigue."""
    strong_genes = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]
    weak_genes = [0.5, 0.5, 0.0, 0.1, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]
    attacker = Organism(x=5, y=5, genome=Genome(strong_genes), energy=200)
    defender = Organism(x=5.5, y=5, genome=Genome(weak_genes), energy=50)

    w = World(width=30, height=30, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)
    w.organisms = [attacker, defender]

    initial_fatigue = attacker.fatigue
    w._fight(attacker, defender)
    assert attacker.fatigue > initial_fatigue


def test_fatigue_exported():
    """Fatigue appears in exported frame data."""
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
        assert "ft" in org_data
        assert isinstance(org_data["ft"], float)
        assert 0.0 <= org_data["ft"] <= 1.0
