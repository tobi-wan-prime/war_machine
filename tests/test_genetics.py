"""Tests for population genetics statistics."""

from arena.genome import Genome
from arena.organism import Organism
from arena.species import SpeciesTracker
from arena.world import World


def test_genetics_stats_keys():
    """Genetics stats returns diversity and divergence keys."""
    tracker = SpeciesTracker()
    orgs = [Organism(x=5, y=5, genome=Genome.random()) for _ in range(10)]
    tracker.classify(orgs, tick=1)
    stats = tracker.get_genetics_stats(orgs)
    assert "diversity" in stats
    assert "divergence" in stats
    assert "species_with_data" in stats


def test_clones_have_zero_diversity():
    """Identical organisms within a species have zero diversity."""
    genes = [0.5] * 11
    tracker = SpeciesTracker()
    orgs = [Organism(x=5, y=5, genome=Genome(list(genes))) for _ in range(10)]
    tracker.classify(orgs, tick=1)
    stats = tracker.get_genetics_stats(orgs)
    assert stats["diversity"] == 0.0


def test_diverse_population_has_positive_diversity():
    """Organisms with varied genes show positive diversity."""
    tracker = SpeciesTracker(distance_threshold=2.0)  # loose threshold so all are same species
    orgs = []
    for i in range(20):
        genes = [i / 20.0] * 11  # spread across gene space
        orgs.append(Organism(x=5, y=5, genome=Genome(genes)))
    tracker.classify(orgs, tick=1)
    stats = tracker.get_genetics_stats(orgs)
    assert stats["diversity"] > 0


def test_divergence_between_distinct_species():
    """Two distinct species show positive divergence."""
    tracker = SpeciesTracker(distance_threshold=0.3)
    orgs_a = [Organism(x=5, y=5, genome=Genome([0.1]*11)) for _ in range(5)]
    orgs_b = [Organism(x=5, y=5, genome=Genome([0.9]*11)) for _ in range(5)]
    tracker.classify(orgs_a + orgs_b, tick=1)
    stats = tracker.get_genetics_stats(orgs_a + orgs_b)
    assert stats["divergence"] > 0


def test_single_species_zero_divergence():
    """One species has zero divergence (no pairs to compare)."""
    tracker = SpeciesTracker(distance_threshold=2.0)
    orgs = [Organism(x=5, y=5, genome=Genome([0.5]*11)) for _ in range(10)]
    tracker.classify(orgs, tick=1)
    stats = tracker.get_genetics_stats(orgs)
    assert stats["divergence"] == 0.0


def test_genetics_in_population_summary():
    """Genetics stats appear in population summary."""
    w = World(width=30, height=30, initial_organisms=15, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(10):
        w.tick()
    summary = w.get_population_summary()
    assert "genetics" in summary
    assert "diversity" in summary["genetics"]
    assert "divergence" in summary["genetics"]
