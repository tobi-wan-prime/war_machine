"""Tests for the pheromone trail system."""

from arena.pheromones import PheromoneMap


def test_deposit_and_sample():
    """Depositing pheromone makes it readable at that location."""
    pm = PheromoneMap(20, 20, cell_size=2.0)
    pm.deposit(PheromoneMap.FOOD, 5.0, 5.0, 1.0)
    val = pm.sample(PheromoneMap.FOOD, 5.0, 5.0)
    assert val > 0, f"Expected positive pheromone, got {val}"
    # danger channel should still be zero
    assert pm.sample(PheromoneMap.DANGER, 5.0, 5.0) == 0.0


def test_decay():
    """Pheromone decays each tick."""
    pm = PheromoneMap(20, 20, cell_size=2.0, decay=0.5, diffusion=0.0)
    pm.deposit(PheromoneMap.FOOD, 5.0, 5.0, 1.0)
    initial = pm.sample(PheromoneMap.FOOD, 5.0, 5.0)
    pm.tick()
    after = pm.sample(PheromoneMap.FOOD, 5.0, 5.0)
    assert after < initial, f"Expected decay: {after} should be < {initial}"
    assert abs(after - initial * 0.5) < 0.01, f"Expected ~50% decay, got {after}"


def test_diffusion():
    """Pheromone spreads to neighboring cells."""
    pm = PheromoneMap(20, 20, cell_size=2.0, decay=1.0, diffusion=0.5)
    # deposit in the middle
    pm.deposit(PheromoneMap.FOOD, 10.0, 10.0, 4.0)
    pm.tick()
    center = pm.sample(PheromoneMap.FOOD, 10.0, 10.0)
    neighbor = pm.sample(PheromoneMap.FOOD, 12.0, 10.0)  # one cell to the right
    assert neighbor > 0, "Expected diffusion to neighbor"
    assert center > neighbor, "Center should be stronger than neighbor"


def test_gradient():
    """Gradient points toward higher concentration."""
    pm = PheromoneMap(20, 20, cell_size=2.0)
    # deposit one cell to the right (cell_size=2.0, so 2 world units apart)
    pm.deposit(PheromoneMap.FOOD, 12.0, 10.0, 5.0)
    gx, gy = pm.gradient(PheromoneMap.FOOD, 10.0, 10.0)
    assert gx > 0, f"Expected positive gradient toward deposit, got gx={gx}"


def test_heatmap():
    """Heatmap returns cells above threshold."""
    pm = PheromoneMap(20, 20, cell_size=2.0)
    pm.deposit(PheromoneMap.DANGER, 5.0, 5.0, 2.0)
    hm = pm.get_heatmap(PheromoneMap.DANGER, threshold=0.05)
    assert len(hm) > 0, "Expected at least one heatmap cell"
    col, row, intensity = hm[0]
    assert 0 < intensity <= 1.0, f"Intensity should be (0, 1], got {intensity}"


def test_full_decay():
    """After many ticks with no deposits, pheromone goes to zero."""
    pm = PheromoneMap(10, 10, cell_size=2.0, decay=0.5, diffusion=0.1)
    pm.deposit(PheromoneMap.FOOD, 5.0, 5.0, 1.0)
    for _ in range(50):
        pm.tick()
    val = pm.sample(PheromoneMap.FOOD, 5.0, 5.0)
    assert val < 0.001, f"Expected near-zero after 50 decays, got {val}"


def test_two_channels_independent():
    """Food and danger channels don't interfere."""
    pm = PheromoneMap(20, 20, cell_size=2.0)
    pm.deposit(PheromoneMap.FOOD, 5.0, 5.0, 3.0)
    pm.deposit(PheromoneMap.DANGER, 15.0, 15.0, 3.0)
    assert pm.sample(PheromoneMap.FOOD, 15.0, 15.0) == 0.0
    assert pm.sample(PheromoneMap.DANGER, 5.0, 5.0) == 0.0
    assert pm.sample(PheromoneMap.FOOD, 5.0, 5.0) > 0
    assert pm.sample(PheromoneMap.DANGER, 15.0, 15.0) > 0
