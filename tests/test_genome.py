"""Tests for the genome system."""

import random
from arena.genome import Genome, NUM_GENES


def test_random_genome_has_correct_length():
    g = Genome.random()
    assert len(g.genes) == NUM_GENES


def test_all_genes_in_range():
    random.seed(42)
    for _ in range(100):
        g = Genome.random()
        for gene in g.genes:
            assert 0.0 <= gene <= 1.0


def test_mutation_preserves_length():
    g = Genome.random()
    m = g.mutate()
    assert len(m.genes) == NUM_GENES


def test_mutation_stays_clamped():
    random.seed(42)
    g = Genome(genes=[0.0] * NUM_GENES)
    for _ in range(50):
        g = g.mutate()
    for gene in g.genes:
        assert 0.0 <= gene <= 1.0

    g = Genome(genes=[1.0] * NUM_GENES)
    for _ in range(50):
        g = g.mutate()
    for gene in g.genes:
        assert 0.0 <= gene <= 1.0


def test_crossover():
    a = Genome(genes=[0.0] * NUM_GENES)
    b = Genome(genes=[1.0] * NUM_GENES)
    child = Genome.crossover(a, b)
    assert len(child.genes) == NUM_GENES


def test_trait_ranges():
    random.seed(42)
    for _ in range(100):
        g = Genome.random()
        assert 0.5 <= g.speed <= 2.0
        assert 1.0 <= g.sense_range <= 7.0
        assert 0.0 <= g.aggression <= 1.0
        assert 0.3 <= g.size <= 2.0
        assert 0.5 <= g.efficiency <= 1.5
        assert 50 <= g.reproduce_threshold <= 150
        assert 0.01 <= g.mutation_rate <= 0.20
        r, gr, bl = g.color
        assert 0 <= r <= 255
        assert 0 <= gr <= 255
        assert 0 <= bl <= 255
