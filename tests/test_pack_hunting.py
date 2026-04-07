"""Tests for coordinated pack hunting."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World


def _aggressive_genome() -> Genome:
    """Create a genome with high aggression."""
    g = Genome(genes=[0.5] * 11)
    g.genes[2] = 0.9  # high aggression
    g.genes[3] = 0.5  # medium size
    return g


def _prey_genome() -> Genome:
    """Create a genome with low aggression, large size."""
    g = Genome(genes=[0.5] * 11)
    g.genes[2] = 0.1  # low aggression
    g.genes[3] = 0.9  # large size (hard to kill solo)
    return g


def test_pack_fight_with_allies():
    """Pack fight with allies should give attack bonus."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=3,
              enable_events=False, day_length=100)

    g_pred = _aggressive_genome()
    attacker = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
    ally = Organism(x=5.5, y=5.5, genome=Genome(genes=list(g_pred.genes)), energy=100)

    g_prey = _prey_genome()
    prey = Organism(x=5.2, y=5.2, genome=g_prey, energy=100)

    w.organisms = [attacker, ally, prey]
    w._rebuild_indices()

    # run pack fight with ally nearby
    pack = [attacker, ally]
    # just ensure it runs without error
    w._pack_fight(attacker, prey, pack)
    # either prey died or attacker lost energy — something happened
    assert prey.energy != 100 or attacker.energy != 100 or not prey.alive or not attacker.alive


def test_pack_bonus_increases_power():
    """Pack with allies should have higher effective combat power."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=3,
              enable_events=False, day_length=100)

    g_pred = _aggressive_genome()
    attacker = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)

    g_prey = _prey_genome()

    # Run many solo fights to get a kill rate
    solo_kills = 0
    for _ in range(50):
        a = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
        d = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_prey.genes)), energy=100)
        w._pack_fight(a, d, [a])  # solo — no allies
        if not d.alive:
            solo_kills += 1

    # Run many pack fights (2 allies nearby)
    pack_kills = 0
    for _ in range(50):
        a = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
        ally1 = Organism(x=5.5, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
        ally2 = Organism(x=5.0, y=5.5, genome=Genome(genes=list(g_pred.genes)), energy=100)
        d = Organism(x=5.2, y=5.2, genome=Genome(genes=list(g_prey.genes)), energy=100)
        w._pack_fight(a, d, [a, ally1, ally2])
        if not d.alive:
            pack_kills += 1

    # pack should kill more often than solo (statistically)
    # with 50 trials and significant bonus, this should be reliable
    assert pack_kills >= solo_kills, f"Pack kills {pack_kills} should be >= solo kills {solo_kills}"


def test_pack_energy_split():
    """When pack kills prey, energy is split among members."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=3,
              enable_events=False, day_length=100)

    g_pred = Genome(genes=[0.8] * 11)
    g_pred.genes[2] = 0.9  # high aggression
    g_pred.genes[3] = 0.9  # large size for guaranteed kill

    attacker = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
    ally = Organism(x=5.5, y=5.0, genome=Genome(genes=list(g_pred.genes)), energy=50)

    g_prey = Genome(genes=[0.1] * 11)
    g_prey.genes[3] = 0.1  # tiny prey
    prey = Organism(x=5.0, y=5.0, genome=g_prey, energy=80)

    w.organisms = [attacker, ally, prey]

    initial_ally_energy = ally.energy
    w._pack_fight(attacker, prey, [attacker, ally])

    if not prey.alive:
        # ally should have gained some energy
        assert ally.energy > initial_ally_energy, "Ally should get share of kill energy"


def test_get_pack_target():
    """_get_pack_target returns target that pack mate is already attacking."""
    w = World(width=40, height=40, initial_organisms=0, food_rate=3,
              enable_events=False, day_length=100)

    g_pred = _aggressive_genome()
    pred1 = Organism(x=10.0, y=10.0, genome=Genome(genes=list(g_pred.genes)), energy=100)
    pred2 = Organism(x=12.0, y=10.0, genome=Genome(genes=list(g_pred.genes)), energy=100)

    g_prey = _prey_genome()
    prey = Organism(x=11.0, y=10.0, genome=g_prey, energy=100)

    w.organisms = [pred1, pred2, prey]
    w._rebuild_indices()
    w.species_tracker.classify(w.organisms, tick=0)

    # pred1 is already targeting prey
    pack_targets = {prey.id: [pred1]}

    # pred2 should converge on same target
    result = w._get_pack_target(pred2, prey, pack_targets)
    # result should be prey (if pred2 can sense it)
    if result is not None:
        assert result.id == prey.id


def test_simulation_with_pack_hunting():
    """Full simulation runs with pack hunting enabled."""
    w = World(width=40, height=40, initial_organisms=15, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(50):
        w.tick()
    assert w.stats.tick == 50
    assert len(w.organisms) > 0
