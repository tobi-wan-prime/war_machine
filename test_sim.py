"""Quick smoke test — run 100 ticks and print stats."""

from arena.world import World

world = World(width=40, height=20, initial_organisms=15, food_rate=3)

print("Running 100 ticks...")
for i in range(100):
    world.tick()
    if i % 20 == 0:
        s = world.get_population_summary()
        print(f"  Tick {world.stats.tick:>4}: pop={s['count']}, food={s.get('food_available',0)}, "
              f"gen={s.get('max_generation',0)}, kills={world.stats.total_kills}")

print("\nFinal stats:")
print(f"  Total born:      {world.stats.total_born}")
print(f"  Total died:      {world.stats.total_died}")
print(f"  Total kills:     {world.stats.total_kills}")
print(f"  Peak population: {world.stats.peak_population}")
print(f"  Max generation:  {world.stats.max_generation}")

s = world.get_population_summary()
if s["count"] > 0:
    print(f"  Survivors:       {s['count']}")
    print(f"  Avg speed:       {s['avg_speed']}")
    print(f"  Avg size:        {s['avg_size']}")
    print(f"  Avg aggression:  {s['avg_aggression']}")
    print(f"  Avg generation:  {s['avg_generation']}")

print("\nSmoke test PASSED")
