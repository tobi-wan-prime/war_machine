"""Tests for kin energy sharing."""

from arena.genome import Genome
from arena.organism import Organism
from arena.world import World
from arena.species import SpeciesTracker


def test_sharing_happens():
    """Energy sharing occurs between same-species organisms."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=5,
              enable_events=False, day_length=100)

    # create two organisms with identical genomes (same species)
    g = Genome(genes=[0.5] * 11)
    g.genes[2] = 0.1  # low aggression (willing to share)

    donor = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g.genes)), energy=150.0)
    recipient = Organism(x=5.5, y=5.5, genome=Genome(genes=list(g.genes)), energy=20.0)

    w.organisms = [donor, recipient]
    w._rebuild_indices()

    # classify species so they're recognized as same species
    w.species_tracker.classify(w.organisms, tick=0)

    # verify they're the same species
    sp_d = w.species_tracker.get_species_for(donor.id)
    sp_r = w.species_tracker.get_species_for(recipient.id)
    assert sp_d is not None and sp_r is not None
    assert sp_d.id == sp_r.id

    # run sharing
    w._kin_energy_sharing()
    assert w.stats.total_shares > 0, "Expected at least one share"


def test_no_sharing_with_aggressive():
    """Aggressive organisms don't share energy."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=5,
              enable_events=False, day_length=100)

    g = Genome(genes=[0.5] * 11)
    g.genes[2] = 0.9  # high aggression

    donor = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g.genes)), energy=150.0)
    recipient = Organism(x=5.5, y=5.5, genome=Genome(genes=list(g.genes)), energy=20.0)

    w.organisms = [donor, recipient]
    w._rebuild_indices()
    w.species_tracker.classify(w.organisms, tick=0)

    w._kin_energy_sharing()
    assert w.stats.total_shares == 0, "Aggressive organisms shouldn't share"


def test_no_sharing_with_different_species():
    """Organisms don't share energy with different species."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=5,
              enable_events=False, day_length=100)

    g1 = Genome(genes=[0.1] * 11)
    g1.genes[2] = 0.1  # low aggression
    g2 = Genome(genes=[0.9] * 11)
    g2.genes[2] = 0.1  # low aggression

    donor = Organism(x=5.0, y=5.0, genome=g1, energy=150.0)
    recipient = Organism(x=5.5, y=5.5, genome=g2, energy=20.0)

    w.organisms = [donor, recipient]
    w._rebuild_indices()
    w.species_tracker = SpeciesTracker(distance_threshold=0.3)
    w.species_tracker.classify(w.organisms, tick=0)

    # verify different species
    sp_d = w.species_tracker.get_species_for(donor.id)
    sp_r = w.species_tracker.get_species_for(recipient.id)
    assert sp_d is not None and sp_r is not None
    assert sp_d.id != sp_r.id

    w._kin_energy_sharing()
    assert w.stats.total_shares == 0, "Different species shouldn't share"


def test_donor_loses_energy():
    """Donor loses energy when sharing."""
    w = World(width=20, height=20, initial_organisms=0, food_rate=5,
              enable_events=False, day_length=100)

    g = Genome(genes=[0.5] * 11)
    g.genes[2] = 0.1

    donor = Organism(x=5.0, y=5.0, genome=Genome(genes=list(g.genes)), energy=150.0)
    recipient = Organism(x=5.5, y=5.5, genome=Genome(genes=list(g.genes)), energy=20.0)

    w.organisms = [donor, recipient]
    w._rebuild_indices()
    w.species_tracker.classify(w.organisms, tick=0)

    initial_donor = donor.energy
    initial_recipient = recipient.energy
    w._kin_energy_sharing()

    assert donor.energy < initial_donor, "Donor should lose energy"
    assert recipient.energy > initial_recipient, "Recipient should gain energy"


def test_shares_tracked_in_summary():
    """Shares count appears in population summary."""
    w = World(width=20, height=20, initial_organisms=5, food_rate=3, day_length=100)
    w.tick()
    s = w.get_population_summary()
    assert "shares" in s
