"""Tests for species detection."""

from arena.genome import Genome
from arena.organism import Organism
from arena.species import SpeciesTracker


def test_identical_genomes_same_species():
    tracker = SpeciesTracker(distance_threshold=0.6)
    g = Genome(genes=[0.5] * 11)
    orgs = [
        Organism(x=0, y=0, genome=Genome(genes=list(g.genes))),
        Organism(x=1, y=1, genome=Genome(genes=list(g.genes))),
    ]
    tracker.classify(orgs, tick=1)
    sp1 = tracker.get_species_for(orgs[0].id)
    sp2 = tracker.get_species_for(orgs[1].id)
    assert sp1 is not None
    assert sp2 is not None
    assert sp1.id == sp2.id


def test_distant_genomes_different_species():
    tracker = SpeciesTracker(distance_threshold=0.3)
    org_a = Organism(x=0, y=0, genome=Genome(genes=[0.0] * 11))
    org_b = Organism(x=1, y=1, genome=Genome(genes=[1.0] * 11))
    tracker.classify([org_a, org_b], tick=1)
    sp_a = tracker.get_species_for(org_a.id)
    sp_b = tracker.get_species_for(org_b.id)
    assert sp_a is not None
    assert sp_b is not None
    assert sp_a.id != sp_b.id


def test_species_summary():
    tracker = SpeciesTracker(distance_threshold=0.6)
    orgs = [Organism(x=i, y=0, genome=Genome.random()) for i in range(10)]
    tracker.classify(orgs, tick=1)
    summary = tracker.get_summary()
    assert "active_count" in summary
    assert "total_ever" in summary
    assert "species" in summary
    assert summary["active_count"] > 0


def test_species_history_recorded():
    tracker = SpeciesTracker(distance_threshold=0.6)
    orgs = [Organism(x=i, y=0, genome=Genome.random()) for i in range(5)]
    tracker.classify(orgs, tick=1)
    tracker.classify(orgs, tick=2)
    assert len(tracker.history) == 2


def test_genome_distance():
    a = Genome(genes=[0.0] * 11)
    b = Genome(genes=[1.0] * 11)
    dist = a.distance(b)
    # distance across 8 behavioral genes, each differing by 1.0
    # sqrt(8) ~= 2.828
    assert 2.8 < dist < 2.9

    c = Genome(genes=[0.0] * 11)
    assert a.distance(c) == 0.0
