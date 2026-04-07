"""Tests for the world simulation."""

from arena.world import World


def test_world_creation():
    w = World(width=40, height=20, initial_organisms=10, food_rate=3, enable_events=False)
    assert len(w.organisms) == 10
    assert len(w.food) == 30  # food_rate * 10


def test_world_tick_advances():
    w = World(width=40, height=20, initial_organisms=10, enable_events=False)
    w.tick()
    assert w.stats.tick == 1


def test_population_survives_100_ticks():
    w = World(width=40, height=20, initial_organisms=15, food_rate=3, enable_events=False)
    for _ in range(100):
        w.tick()
    assert len(w.organisms) > 0
    assert w.stats.total_born > 15  # some reproduction happened


def test_history_records():
    w = World(width=40, height=20, initial_organisms=10, enable_events=False)
    for _ in range(50):
        w.tick()
    assert len(w.history.snapshots) == 50


def test_events_fire():
    w = World(width=40, height=20, initial_organisms=15, food_rate=3, enable_events=True)
    event_fired = False
    for _ in range(200):
        w.tick()
        if w.last_event is not None:
            event_fired = True
    assert event_fired, "Expected at least one event in 200 ticks"


def test_population_summary_keys():
    w = World(width=40, height=20, initial_organisms=10, enable_events=False)
    w.tick()
    s = w.get_population_summary()
    assert "count" in s
    assert "avg_speed" in s
    assert "avg_size" in s
    assert "avg_aggression" in s
    assert "avg_energy" in s
    assert "avg_age" in s


def test_extinction_recovery():
    w = World(width=40, height=20, initial_organisms=1, food_rate=0, enable_events=False)
    # starve the single organism
    for _ in range(500):
        w.tick()
    # world should have reseeded
    assert len(w.organisms) > 0
    assert w.stats.reseeds > 0


def test_graveyard_capped():
    w = World(width=40, height=20, initial_organisms=20, food_rate=5, enable_events=False)
    for _ in range(1000):
        w.tick()
    assert len(w.graveyard) <= 500


def test_terrain_world():
    w = World(width=60, height=30, initial_organisms=15, food_rate=4,
              enable_events=False, enable_terrain=True, terrain_seed=42)
    wall_count = sum(1 for row in w.terrain.tiles for t in row if t.name == 'WALL')
    assert wall_count > 0
    for _ in range(100):
        w.tick()
    assert len(w.organisms) > 0


def test_mating_happens():
    w = World(width=40, height=20, initial_organisms=20, food_rate=5, enable_events=False)
    for _ in range(200):
        w.tick()
    assert w.stats.total_matings > 0, "Expected some matings in 200 ticks"


def test_matings_in_summary():
    w = World(width=40, height=20, initial_organisms=10, enable_events=False)
    w.tick()
    s = w.get_population_summary()
    assert "matings" in s
