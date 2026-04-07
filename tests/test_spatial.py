"""Tests for spatial hash grid."""

from dataclasses import dataclass
from arena.spatial import SpatialHash


@dataclass
class Point:
    x: float
    y: float


def test_insert_and_query():
    sh: SpatialHash[Point] = SpatialHash(cell_size=10.0)
    p = Point(5.0, 5.0)
    sh.insert(p)
    results = sh.query_radius(5.0, 5.0, 1.0)
    assert p in results


def test_query_excludes_distant():
    sh: SpatialHash[Point] = SpatialHash(cell_size=10.0)
    near = Point(5.0, 5.0)
    far = Point(50.0, 50.0)
    sh.insert(near)
    sh.insert(far)
    results = sh.query_radius(5.0, 5.0, 3.0)
    assert near in results
    assert far not in results


def test_nearest():
    sh: SpatialHash[Point] = SpatialHash(cell_size=10.0)
    a = Point(1.0, 1.0)
    b = Point(5.0, 5.0)
    c = Point(20.0, 20.0)
    sh.insert(a)
    sh.insert(b)
    sh.insert(c)
    result = sh.nearest(0.0, 0.0, 30.0)
    assert result is a


def test_nearest_with_exclude():
    sh: SpatialHash[Point] = SpatialHash(cell_size=10.0)
    a = Point(1.0, 1.0)
    b = Point(3.0, 3.0)
    sh.insert(a)
    sh.insert(b)
    result = sh.nearest(0.0, 0.0, 30.0, exclude=a)
    assert result is b


def test_bulk_insert_clears():
    sh: SpatialHash[Point] = SpatialHash(cell_size=10.0)
    sh.insert(Point(100.0, 100.0))
    sh.bulk_insert([Point(1.0, 1.0)])
    results = sh.query_radius(100.0, 100.0, 5.0)
    assert len(results) == 0
    results = sh.query_radius(1.0, 1.0, 5.0)
    assert len(results) == 1
