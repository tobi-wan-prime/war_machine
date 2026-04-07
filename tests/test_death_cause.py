"""Tests for cause of death tracking."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def test_starvation_death_cause():
    """Organism that runs out of energy has death_cause='starved'."""
    org = Organism(x=5, y=5, genome=Genome.random(), energy=1.0)
    # drain energy via metabolism
    for _ in range(20):
        org.tick_metabolism()
        if not org.alive:
            break
    assert not org.alive
    assert org.death_cause == "starved"


def test_old_age_death_cause():
    """Organism that reaches max_age has death_cause='old_age'."""
    org = Organism(x=5, y=5, genome=Genome.random(), energy=10000.0)
    org.age = org.max_age - 1
    org.tick_metabolism()
    assert not org.alive
    assert org.death_cause == "old_age"


def test_combat_death_cause():
    """Organism killed in combat has death_cause='combat'."""
    # create a strong attacker and weak defender
    strong_genes = [0.5, 0.5, 0.9, 0.9, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]
    weak_genes = [0.5, 0.5, 0.1, 0.1, 0.5, 0.5, 0.1, 0.5, 0.5, 0.5, 0.5]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    attacker = Organism(x=5, y=5, genome=Genome(strong_genes), energy=100)
    defender = Organism(x=5.5, y=5, genome=Genome(weak_genes), energy=50)
    w.organisms = [attacker, defender]

    # run many fights until one dies
    for _ in range(50):
        w._fight(attacker, defender)
        if not defender.alive or not attacker.alive:
            break

    # at least one should be dead with combat cause
    dead = [o for o in [attacker, defender] if not o.alive]
    assert len(dead) > 0
    for d in dead:
        assert d.death_cause == "combat"


def test_death_stats_tracked_in_world():
    """World tracks death cause counters."""
    w = World(width=20, height=20, initial_organisms=15, food_rate=1,
              enable_events=False, day_length=100)
    for _ in range(200):
        w.tick()

    total_tracked = (w.stats.deaths_starved + w.stats.deaths_old_age
                     + w.stats.deaths_combat + w.stats.deaths_meteor)
    # total tracked should equal total_died
    assert total_tracked == w.stats.total_died
    # at least some deaths should have occurred
    assert w.stats.total_died > 0


def test_graveyard_has_cause():
    """Graveyard entries include cause of death."""
    w = World(width=20, height=20, initial_organisms=10, food_rate=1,
              enable_events=False, day_length=100)
    for _ in range(150):
        w.tick()

    assert len(w.graveyard) > 0
    for entry in w.graveyard:
        assert "cause" in entry
        assert entry["cause"] in ("starved", "old_age", "combat", "meteor", "unknown")


def test_death_stats_in_summary():
    """Population summary includes death breakdown."""
    w = World(width=20, height=20, initial_organisms=10, food_rate=1,
              enable_events=False, day_length=100)
    for _ in range(100):
        w.tick()

    summary = w.get_population_summary()
    assert "deaths_starved" in summary
    assert "deaths_old_age" in summary
    assert "deaths_combat" in summary
    assert "deaths_meteor" in summary


def test_alive_organism_has_no_death_cause():
    """Living organisms have empty death_cause."""
    org = Organism(x=5, y=5, genome=Genome.random(), energy=100.0)
    assert org.alive
    assert org.death_cause == ""


def test_killed_by_tracks_killer():
    """Combat death records the killer's ID."""
    strong_genes = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]
    weak_genes = [0.5, 0.5, 0.0, 0.1, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5]

    w = World(width=20, height=20, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    attacker = Organism(x=5, y=5, genome=Genome(strong_genes), energy=200)
    defender = Organism(x=5.5, y=5, genome=Genome(weak_genes), energy=30)
    w.organisms = [attacker, defender]

    for _ in range(50):
        w._fight(attacker, defender)
        if not defender.alive or not attacker.alive:
            break

    dead = [o for o in [attacker, defender] if not o.alive]
    assert len(dead) > 0
    for d in dead:
        assert d.killed_by > 0, "killed_by should record the killer's ID"


def test_graveyard_has_killer():
    """Graveyard entries for combat deaths include killer ID."""
    w = World(width=30, height=30, initial_organisms=20, food_rate=2,
              enable_events=False, day_length=100)
    for _ in range(200):
        w.tick()

    combat_deaths = [g for g in w.graveyard if g["cause"] == "combat"]
    if len(combat_deaths) > 0:
        for g in combat_deaths:
            assert "killer" in g
            assert g["killer"] > 0
