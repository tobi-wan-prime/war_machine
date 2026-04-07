"""Tests for species phylogenetic tracking."""

from arena.genome import Genome
from arena.organism import Organism
from arena.species import SpeciesTracker


def test_new_species_has_parent():
    """When a species splits, the new species records its parent."""
    tracker = SpeciesTracker(distance_threshold=0.3)

    # create organisms from two distinct genome clusters
    g1 = Genome(genes=[0.1] * 11)
    g2 = Genome(genes=[0.9] * 11)
    org_a = Organism(x=0, y=0, genome=g1)
    org_b = Organism(x=0, y=0, genome=g2)

    # first classify — both should be different species
    tracker.classify([org_a, org_b], tick=0)

    sp_a = tracker.get_species_for(org_a.id)
    sp_b = tracker.get_species_for(org_b.id)
    assert sp_a is not None and sp_b is not None
    assert sp_a.id != sp_b.id

    # one of them should have a parent (the one created second)
    # the first species has parent_id=0 (root), second has parent pointing to closest
    species_list = list(tracker.species.values())
    has_parent = [sp for sp in species_list if sp.parent_id != 0]
    # at least one species should have a parent
    assert len(has_parent) >= 1


def test_root_species_has_no_parent():
    """The very first species should have parent_id=0."""
    tracker = SpeciesTracker(distance_threshold=0.6)

    g = Genome(genes=[0.5] * 11)
    org = Organism(x=0, y=0, genome=g)
    tracker.classify([org], tick=0)

    sp = tracker.get_species_for(org.id)
    assert sp is not None
    # first ever species — closest species was None, so parent=0
    assert sp.parent_id == 0


def test_extinction_tick_recorded():
    """When a species goes extinct, extinct_tick is set."""
    tracker = SpeciesTracker(distance_threshold=0.6)

    g = Genome(genes=[0.5] * 11)
    org = Organism(x=0, y=0, genome=g)
    tracker.classify([org], tick=0)
    sp = tracker.get_species_for(org.id)
    assert sp is not None
    sp_id = sp.id

    # now classify with no organisms — species goes extinct
    tracker.classify([], tick=5)

    sp = tracker.get_species_by_id(sp_id)
    assert sp is not None
    assert sp.extinct_tick == 5


def test_alive_species_no_extinction():
    """Species with members should not have extinct_tick set."""
    tracker = SpeciesTracker(distance_threshold=0.6)

    g = Genome(genes=[0.5] * 11)
    org = Organism(x=0, y=0, genome=g)
    tracker.classify([org], tick=0)
    tracker.classify([org], tick=5)

    sp = tracker.get_species_for(org.id)
    assert sp is not None
    assert sp.extinct_tick == 0


def test_get_phylogeny_returns_all_species():
    """get_phylogeny returns data for all species ever seen."""
    tracker = SpeciesTracker(distance_threshold=0.3)

    g1 = Genome(genes=[0.1] * 11)
    g2 = Genome(genes=[0.9] * 11)
    org_a = Organism(x=0, y=0, genome=g1)
    org_b = Organism(x=0, y=0, genome=g2)
    tracker.classify([org_a, org_b], tick=0)

    phylo = tracker.get_phylogeny()
    assert len(phylo) >= 2
    ids = {p["id"] for p in phylo}
    assert len(ids) == len(phylo)  # all unique IDs


def test_phylogeny_has_required_fields():
    """Each phylogeny entry has all required fields."""
    tracker = SpeciesTracker(distance_threshold=0.6)

    g = Genome(genes=[0.5] * 11)
    org = Organism(x=0, y=0, genome=g)
    tracker.classify([org], tick=0)

    phylo = tracker.get_phylogeny()
    assert len(phylo) >= 1
    entry = phylo[0]
    for key in ("id", "parent", "color", "first", "last", "ext", "peak"):
        assert key in entry, f"Missing key: {key}"


def test_phylogeny_sorted_by_first_seen():
    """Phylogeny entries are sorted by first_seen tick."""
    tracker = SpeciesTracker(distance_threshold=0.3)

    g1 = Genome(genes=[0.1] * 11)
    g2 = Genome(genes=[0.9] * 11)
    org_a = Organism(x=0, y=0, genome=g1)
    tracker.classify([org_a], tick=0)

    org_b = Organism(x=0, y=0, genome=g2)
    tracker.classify([org_a, org_b], tick=10)

    phylo = tracker.get_phylogeny()
    firsts = [p["first"] for p in phylo]
    assert firsts == sorted(firsts)
