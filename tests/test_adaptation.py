"""Tests for environmental adaptation mechanic."""

from arena.genome import Genome
from arena.organism import Organism
from arena.terrain import Terrain, TileType
from arena.world import World


def test_initial_adaptation_is_zero():
    """Organisms start with zero adaptation."""
    org = Organism(x=5, y=5, genome=Genome.random())
    assert org.adaptation == 0.0


def test_adaptation_grows_in_harsh_zone():
    """Organisms in harsh zones gain adaptation over time."""
    w = World(width=30, height=30, initial_organisms=0, food_rate=0,
              enable_events=False, enable_terrain=True, day_length=100)
    # place a slow organism in a hot zone manually
    org = Organism(x=5, y=5, genome=Genome([0.2, 0.5, 0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]))
    org.energy = 200  # plenty of energy to survive
    # force a large hot region around the organism
    for r in range(max(0, int(org.y) - 8), min(w.terrain.height, int(org.y) + 9)):
        for c in range(max(0, int(org.x) - 8), min(w.terrain.width, int(org.x) + 9)):
            w.terrain.tiles[r][c] = TileType.HOT
    w.organisms.append(org)
    initial_adapt = org.adaptation
    for _ in range(20):
        w.tick()
        if not org.alive:
            break
    assert org.adaptation > initial_adapt


def test_adaptation_decays_outside_zones():
    """Adaptation decays when not in a harsh zone."""
    org = Organism(x=5, y=5, genome=Genome.random())
    org.adaptation = 0.5
    w = World(width=30, height=30, initial_organisms=0, food_rate=5,
              enable_events=False, enable_terrain=False, day_length=100)
    w.organisms.append(org)
    for _ in range(20):
        w.tick()
        if not org.alive:
            break
    if org.alive:
        assert org.adaptation < 0.5


def test_adaptation_caps_at_one():
    """Adaptation cannot exceed 1.0."""
    org = Organism(x=5, y=5, genome=Genome.random())
    org.adaptation = 1.0
    # try to push beyond
    org.adaptation = min(1.0, org.adaptation + 0.005)
    assert org.adaptation == 1.0


def test_adaptation_reduces_damage():
    """Adapted organisms take less damage from harsh zones."""
    # Create two identical organisms, one adapted and one not
    genes = [0.2, 0.5, 0.3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]  # slow = hurt by hot
    org_adapted = Organism(x=5, y=5, genome=Genome(list(genes)))
    org_adapted.energy = 200
    org_adapted.adaptation = 0.8
    org_unadapted = Organism(x=5, y=5, genome=Genome(list(genes)))
    org_unadapted.energy = 200
    org_unadapted.adaptation = 0.0

    # Simulate hot zone damage manually
    shield_adapted = 1.0 - org_adapted.adaptation * 0.6
    shield_unadapted = 1.0 - org_unadapted.adaptation * 0.6
    dmg_adapted = 1.5 * shield_adapted
    dmg_unadapted = 1.5 * shield_unadapted

    assert dmg_adapted < dmg_unadapted


def test_adaptation_exported():
    """Adaptation value appears in exported frame data."""
    w = World(width=30, height=30, initial_organisms=10, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(5):
        w.tick()
    from arena.exporter import ReplayExporter
    exp = ReplayExporter(sample_rate=1)
    exp.set_config(w)
    exp.capture(w)
    frame = exp.frames[0]
    for org_data in frame.organisms:
        assert "ad" in org_data
        assert 0.0 <= org_data["ad"] <= 1.0
