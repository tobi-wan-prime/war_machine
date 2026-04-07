"""Tests for terrain system."""

from arena.terrain import Terrain, TileType


def test_empty_terrain():
    t = Terrain.empty(20, 10)
    assert t.width == 20
    assert t.height == 10
    for row in t.tiles:
        for tile in row:
            assert tile == TileType.OPEN


def test_generated_terrain_has_walls():
    t = Terrain.generate(60, 30, seed=42)
    wall_count = sum(1 for row in t.tiles for tile in row if tile == TileType.WALL)
    assert wall_count > 0, "Generated terrain should have walls"


def test_generated_terrain_has_fertile():
    t = Terrain.generate(60, 30, seed=42)
    fertile_count = sum(1 for row in t.tiles for tile in row if tile == TileType.FERTILE)
    assert fertile_count > 0, "Generated terrain should have fertile zones"


def test_borders_are_open():
    t = Terrain.generate(40, 20, seed=123)
    for x in range(t.width):
        assert t.tiles[0][x] == TileType.OPEN
        assert t.tiles[t.height - 1][x] == TileType.OPEN
    for y in range(t.height):
        assert t.tiles[y][0] == TileType.OPEN
        assert t.tiles[y][t.width - 1] == TileType.OPEN


def test_passable_check():
    t = Terrain.empty(10, 10)
    assert t.is_passable(5.0, 5.0)
    t.tiles[5][5] = TileType.WALL
    assert not t.is_passable(5.0, 5.0)


def test_to_lists():
    t = Terrain.empty(5, 3)
    t.tiles[1][2] = TileType.WALL
    result = t.to_lists()
    assert result[1][2] == TileType.WALL.value
    assert result[0][0] == TileType.OPEN.value


def test_fertile_positions():
    t = Terrain.empty(10, 10)
    t.tiles[3][4] = TileType.FERTILE
    t.tiles[7][2] = TileType.FERTILE
    positions = t.get_fertile_positions()
    assert (4, 3) in positions
    assert (2, 7) in positions
    assert len(positions) == 2
