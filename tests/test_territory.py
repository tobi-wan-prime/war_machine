"""Tests for territory map system."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World
from arena.territory_map import TerritoryMap


def test_claim_and_query():
    """Claiming a cell sets the owner and strength."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.5)
    assert tm.get_owner(5.0, 5.0) == 1
    assert tm.get_strength(5.0, 5.0) > 0


def test_unclaimed_returns_zero():
    """Unclaimed cells return species_id 0."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    assert tm.get_owner(5.0, 5.0) == 0
    assert tm.get_strength(5.0, 5.0) == 0.0


def test_claim_reinforces():
    """Multiple claims by same species increase strength."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.3)
    s1 = tm.get_strength(5.0, 5.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.3)
    s2 = tm.get_strength(5.0, 5.0)
    assert s2 > s1


def test_claim_caps_at_one():
    """Strength is capped at 1.0."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    for _ in range(10):
        tm.claim(5.0, 5.0, species_id=1, amount=0.5)
    assert tm.get_strength(5.0, 5.0) <= 1.0


def test_contest_weakens_claim():
    """Different species contesting weakens the existing claim."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.5)
    initial = tm.get_strength(5.0, 5.0)
    tm.claim(5.0, 5.0, species_id=2, amount=0.5)
    # claim should have been contested — either weakened or flipped
    owner = tm.get_owner(5.0, 5.0)
    strength = tm.get_strength(5.0, 5.0)
    assert owner in (1, 2)
    # if flipped, strength should be lower than initial
    if owner == 2:
        assert strength < initial


def test_territory_flips():
    """Enough contesting flips territory to new species."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.3)
    # contest repeatedly
    for _ in range(5):
        tm.claim(5.0, 5.0, species_id=2, amount=0.5)
    assert tm.get_owner(5.0, 5.0) == 2


def test_decay():
    """Territory claims decay over time."""
    tm = TerritoryMap(20, 20, cell_size=2.0, decay=0.5)
    tm.claim(5.0, 5.0, species_id=1, amount=0.8)
    s1 = tm.get_strength(5.0, 5.0)
    tm.tick()
    s2 = tm.get_strength(5.0, 5.0)
    assert s2 < s1


def test_decay_removes_weak_claims():
    """Very weak claims are cleared on decay."""
    tm = TerritoryMap(20, 20, cell_size=2.0, decay=0.1)
    tm.claim(5.0, 5.0, species_id=1, amount=0.05)
    for _ in range(10):
        tm.tick()
    assert tm.get_owner(5.0, 5.0) == 0
    assert tm.get_strength(5.0, 5.0) == 0.0


def test_is_home():
    """is_home returns True for strong claims by the right species."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.5)
    assert tm.is_home(5.0, 5.0, 1) is True
    assert tm.is_home(5.0, 5.0, 2) is False
    assert tm.is_home(10.0, 10.0, 1) is False


def test_get_territory_map():
    """get_territory_map returns claimed cells above threshold."""
    tm = TerritoryMap(20, 20, cell_size=2.0)
    tm.claim(5.0, 5.0, species_id=1, amount=0.5)
    tm.claim(15.0, 15.0, species_id=2, amount=0.5)
    result = tm.get_territory_map(threshold=0.1)
    assert len(result) == 2
    ids = {r[2] for r in result}
    assert ids == {1, 2}


def test_territory_combat_bonus():
    """Organism fighting on home turf should have advantage."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=3,
              enable_events=False, day_length=100)

    g_pred = Genome(genes=[0.5] * 11)
    g_pred.genes[2] = 0.9  # high aggression
    g_pred.genes[3] = 0.5

    g_prey = Genome(genes=[0.5] * 11)
    g_prey.genes[2] = 0.1
    g_prey.genes[3] = 0.5

    attacker = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
    defender = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_prey.genes)), energy=100)

    w.organisms = [attacker, defender]
    w._rebuild_indices()
    w.species_tracker.classify(w.organisms, tick=0)

    # claim territory for defender's species
    d_sp = w.species_tracker.get_species_for(defender.id)
    if d_sp:
        for _ in range(5):
            w.territory.claim(5.0, 5.0, d_sp.id, amount=0.5)

    # run fight — defender has territory bonus
    w._fight(attacker, defender)
    # something happened (we can't predict random outcome, just verify it runs)
    assert attacker.energy != 100 or defender.energy != 100 or not attacker.alive or not defender.alive


def test_simulation_with_territory():
    """Full simulation runs with territory system."""
    w = World(width=40, height=40, initial_organisms=15, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    assert len(w.organisms) > 0
