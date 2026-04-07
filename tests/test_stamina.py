"""Tests for the stamina gene — fatigue resistance evolution."""

from arena.genome import Genome, STAMINA, NUM_GENES
from arena.organism import Organism
from arena.world import World


def test_genome_has_stamina():
    """Genome includes stamina gene at index 11."""
    g = Genome.random()
    assert len(g.genes) == NUM_GENES
    assert 0.0 <= g.genes[STAMINA] <= 1.0
    assert 0.0 <= g.stamina <= 1.0


def test_short_gene_list_padded():
    """11-gene lists are padded to 12 for backwards compat."""
    g = Genome([0.5] * 11)
    assert len(g.genes) == NUM_GENES
    assert 0.0 <= g.genes[STAMINA] <= 1.0


def test_stamina_reduces_fatigue_gain():
    """High stamina organisms accumulate fatigue slower."""
    # low stamina (0.0) → gain rate 1.0
    low = Organism(x=5, y=5, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 0.0]))
    # high stamina (1.0) → gain rate 0.4
    high = Organism(x=5, y=5, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 1.0]))

    assert low.fatigue_gain_rate > high.fatigue_gain_rate
    assert abs(low.fatigue_gain_rate - 1.0) < 0.01
    assert abs(high.fatigue_gain_rate - 0.4) < 0.01


def test_stamina_increases_recovery():
    """High stamina organisms recover from fatigue faster."""
    low = Organism(x=5, y=5, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 0.0]))
    high = Organism(x=5, y=5, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 1.0]))

    assert high.fatigue_recovery_rate > low.fatigue_recovery_rate
    assert abs(low.fatigue_recovery_rate - 1.0) < 0.01
    assert abs(high.fatigue_recovery_rate - 1.8) < 0.01


def test_stamina_affects_combat_fatigue():
    """High-stamina fighters gain less fatigue from combat."""
    strong_genes_low_stam = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5, 0.0]
    strong_genes_high_stam = [0.5, 0.5, 1.0, 1.0, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5, 1.0]
    weak_genes = [0.5, 0.5, 0.0, 0.1, 0.5, 0.5, 0.0, 0.5, 0.5, 0.5, 0.5, 0.5]

    a_low = Organism(x=5, y=5, genome=Genome(strong_genes_low_stam), energy=200)
    a_high = Organism(x=5, y=5, genome=Genome(strong_genes_high_stam), energy=200)
    d1 = Organism(x=5.5, y=5, genome=Genome(weak_genes), energy=50)
    d2 = Organism(x=5.5, y=5, genome=Genome(weak_genes), energy=50)

    w = World(width=30, height=30, initial_organisms=0, food_rate=0,
              enable_events=False, day_length=100)

    w.organisms = [a_low, d1]
    w._fight(a_low, d1)
    fatigue_low = a_low.fatigue

    w.organisms = [a_high, d2]
    w._fight(a_high, d2)
    fatigue_high = a_high.fatigue

    # high stamina fighter should have less fatigue after combat
    assert fatigue_high < fatigue_low


def test_stamina_metabolic_cost():
    """High stamina organisms burn slightly more energy."""
    low = Organism(x=5, y=5, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 0.0]))
    high = Organism(x=5, y=5, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 1.0]))

    assert high.energy_cost_per_tick > low.energy_cost_per_tick


def test_stamina_exported():
    """Stamina appears in exported genome data."""
    w = World(width=30, height=30, initial_organisms=15, food_rate=5,
              enable_events=False, day_length=100)
    for _ in range(5):
        w.tick()
    from arena.exporter import ReplayExporter
    exp = ReplayExporter(sample_rate=1)
    exp.set_config(w)
    exp.capture(w)
    frame = exp.frames[0]
    for org_data in frame.organisms:
        assert len(org_data["gn"]) == 9  # 8 behavioral + stamina
        assert isinstance(org_data["gn"][8], float)
        assert 0.0 <= org_data["gn"][8] <= 1.0


def test_stamina_inherited():
    """Stamina gene is inherited and mutated like other genes."""
    parent = Organism(x=15, y=15, genome=Genome([0.5]*8 + [0.5, 0.5, 0.5, 0.8]),
                      energy=200)
    child = parent.reproduce(30, 30)
    # child should have a stamina gene close to parent's (with mutation)
    assert 0.0 <= child.genome.stamina <= 1.0
