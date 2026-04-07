"""Tests for organism behavior."""

from arena.genome import Genome
from arena.organism import Organism


def test_organism_creation():
    org = Organism(x=10.0, y=20.0, genome=Genome.random())
    assert org.alive
    assert org.energy == 100.0
    assert org.age == 0
    assert org.kills == 0


def test_metabolism_drains_energy():
    org = Organism(x=10.0, y=20.0, genome=Genome.random())
    initial = org.energy
    org.tick_metabolism()
    assert org.energy < initial
    assert org.age == 1


def test_organism_dies_at_zero_energy():
    org = Organism(x=10.0, y=20.0, genome=Genome.random(), energy=0.1)
    org.tick_metabolism()
    assert not org.alive


def test_organism_dies_of_old_age():
    org = Organism(x=10.0, y=20.0, genome=Genome.random(), energy=10000)
    org.age = org.max_age
    org.tick_metabolism()
    assert not org.alive


def test_eating_increases_energy():
    org = Organism(x=10.0, y=20.0, genome=Genome.random(), energy=50.0)
    org.eat(20.0)
    assert org.energy > 50.0


def test_eating_capped_at_max():
    org = Organism(x=10.0, y=20.0, genome=Genome.random(), energy=200.0)
    org.eat(1000.0)
    assert org.energy <= org.max_energy


def test_reproduction():
    org = Organism(x=40.0, y=20.0, genome=Genome.random(), energy=200.0)
    assert org.can_reproduce()
    child = org.reproduce(80, 40)
    assert child.alive
    assert child.generation == org.generation + 1
    assert org.energy < 200.0  # parent spent energy


def test_flee_moves_away():
    org = Organism(x=40.0, y=20.0, genome=Genome.random())
    threat_x, threat_y = 38.0, 20.0
    initial_dist = org.distance_to_point(threat_x, threat_y)
    org.flee_from(threat_x, threat_y, 80, 40)
    new_dist = org.distance_to_point(threat_x, threat_y)
    assert new_dist > initial_dist


def test_move_toward():
    org = Organism(x=10.0, y=10.0, genome=Genome.random())
    target_x, target_y = 20.0, 10.0
    initial_dist = org.distance_to_point(target_x, target_y)
    org.move_toward(target_x, target_y, 80, 40)
    new_dist = org.distance_to_point(target_x, target_y)
    assert new_dist < initial_dist


def test_age_factor_increases_with_age():
    org = Organism(x=10.0, y=10.0, genome=Genome.random())
    young_factor = org.age_factor
    org.age = int(org.max_age * 0.9)
    old_factor = org.age_factor
    assert old_factor > young_factor


def test_sexual_reproduction():
    a = Organism(x=40.0, y=20.0, genome=Genome.random(), energy=200.0)
    b = Organism(x=41.0, y=20.0, genome=Genome.random(), energy=200.0)
    a.age = 10
    b.age = 10
    assert a.can_mate()
    assert b.can_mate()
    child = a.mate(b, 80, 40)
    assert child.alive
    assert child.generation == max(a.generation, b.generation) + 1
    assert a.energy < 200.0
    assert b.energy < 200.0


def test_can_mate_requires_age():
    org = Organism(x=10.0, y=10.0, genome=Genome.random(), energy=200.0)
    org.age = 0
    assert not org.can_mate()  # too young
    org.age = 10
    assert org.can_mate()


def test_can_mate_requires_energy():
    org = Organism(x=10.0, y=10.0, genome=Genome.random(), energy=10.0)
    org.age = 10
    assert not org.can_mate()  # not enough energy
