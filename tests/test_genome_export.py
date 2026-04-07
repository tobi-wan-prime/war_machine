"""Tests for genome gene export in replay data."""

from arena.world import World
from arena.exporter import ReplayExporter


def test_genes_exported_per_organism():
    """Each organism in replay frames has a gn array with 9 gene values."""
    w = World(width=30, height=30, initial_organisms=10, food_rate=5,
              enable_events=False, day_length=100)
    exporter = ReplayExporter(sample_rate=2)
    exporter.set_config(w)

    for _ in range(10):
        w.tick()
        exporter.capture(w)

    assert len(exporter.frames) > 0
    frame = exporter.frames[0]
    assert len(frame.organisms) > 0
    org = frame.organisms[0]
    assert "gn" in org
    assert len(org["gn"]) == 9
    for v in org["gn"]:
        assert 0.0 <= v <= 1.0


def test_genes_values_in_range():
    """All exported gene values are between 0 and 1."""
    w = World(width=20, height=20, initial_organisms=15, food_rate=3,
              enable_events=False, day_length=100)
    exporter = ReplayExporter(sample_rate=1)
    exporter.set_config(w)

    for _ in range(20):
        w.tick()
        exporter.capture(w)

    for frame in exporter.frames:
        for org in frame.organisms:
            for v in org["gn"]:
                assert 0.0 <= v <= 1.0, f"Gene value {v} out of range"
