"""Tests for kill position tracking and export."""

import json
from arena.world import World
from arena.exporter import ReplayExporter


def test_graveyard_has_positions():
    """Dead organisms in graveyard have x,y coordinates."""
    w = World(width=30, height=30, initial_organisms=30, food_rate=1,
              enable_events=False, day_length=100)
    for _ in range(100):
        w.tick()
    # some organisms should have died by now
    if w.graveyard:
        entry = w.graveyard[0]
        assert "x" in entry
        assert "y" in entry
        assert isinstance(entry["x"], float)
        assert isinstance(entry["y"], float)


def test_kill_pos_in_export():
    """Kill positions appear in exported config."""
    w = World(width=30, height=30, initial_organisms=30, food_rate=1,
              enable_events=False, day_length=100)
    for _ in range(100):
        w.tick()
    exp = ReplayExporter(sample_rate=5)
    exp.set_config(w)
    for _ in range(10):
        w.tick()
        exp.capture(w)
    exp.finalize(w)
    data = json.loads(exp.to_json())
    assert "kill_pos" in data["config"]
    if data["config"]["kill_pos"]:
        pos = data["config"]["kill_pos"][0]
        assert len(pos) == 3  # [x, y, cause_code]
        assert 0 <= pos[2] <= 3  # valid cause code


def test_kill_pos_cause_codes():
    """Cause codes map correctly."""
    from arena.exporter import ReplayExporter
    # run a simulation with enough ticks for deaths
    w = World(width=30, height=30, initial_organisms=40, food_rate=1,
              enable_events=False, day_length=100)
    for _ in range(200):
        w.tick()
    exp = ReplayExporter(sample_rate=10)
    exp.set_config(w)
    exp.capture(w)
    exp.finalize(w)
    data = json.loads(exp.to_json())
    causes = set()
    for pos in data["config"]["kill_pos"]:
        causes.add(pos[2])
    # at minimum we expect starvation (0) or old age (1) in a low-food sim
    assert len(causes) > 0
