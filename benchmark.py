#!/usr/bin/env python3
"""Headless benchmark — run N ticks and dump stats to JSON.

Usage: python benchmark.py [--ticks N] [--output FILE] [--pop N] [--width W] [--height H]
"""

from __future__ import annotations

import argparse
import json
import time
import sys

from arena.world import World


def main() -> None:
    p = argparse.ArgumentParser(description="War Machine: Arena — Headless Benchmark")
    p.add_argument("--ticks", type=int, default=500, help="Number of ticks to simulate")
    p.add_argument("--output", type=str, default=None, help="Output JSON file (default: stdout)")
    p.add_argument("--width", type=int, default=80)
    p.add_argument("--height", type=int, default=40)
    p.add_argument("--pop", type=int, default=25)
    p.add_argument("--food-rate", type=int, default=5)
    p.add_argument("--sample-interval", type=int, default=10,
                   help="Record snapshot every N ticks (default: 10)")
    args = p.parse_args()

    world = World(width=args.width, height=args.height,
                  initial_organisms=args.pop, food_rate=args.food_rate)

    print(f"Running {args.ticks} ticks...", file=sys.stderr)
    t0 = time.perf_counter()

    for i in range(args.ticks):
        world.tick()
        if (i + 1) % 100 == 0:
            elapsed = time.perf_counter() - t0
            tps = (i + 1) / elapsed
            print(f"  Tick {i + 1}/{args.ticks}  ({tps:.0f} ticks/sec)  "
                  f"pop={len(world.organisms)}", file=sys.stderr)

    elapsed = time.perf_counter() - t0

    result = {
        "config": {
            "width": args.width, "height": args.height,
            "initial_pop": args.pop, "food_rate": args.food_rate,
            "ticks": args.ticks,
        },
        "performance": {
            "elapsed_seconds": round(elapsed, 3),
            "ticks_per_second": round(args.ticks / elapsed, 1),
        },
        "final_stats": {
            "tick": world.stats.tick,
            "population": len(world.organisms),
            "total_born": world.stats.total_born,
            "total_died": world.stats.total_died,
            "total_kills": world.stats.total_kills,
            "peak_population": world.stats.peak_population,
            "max_generation": world.stats.max_generation,
        },
        "final_traits": world.get_population_summary(),
        "history": world.history.to_dicts(),
        "top_killers": _top_killers(world),
    }

    output = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"\nResults written to {args.output}", file=sys.stderr)
    else:
        print(output)

    # summary to stderr
    print(f"\n=== Benchmark Complete ===", file=sys.stderr)
    print(f"  {args.ticks} ticks in {elapsed:.2f}s ({args.ticks/elapsed:.0f} tps)", file=sys.stderr)
    print(f"  Final pop: {len(world.organisms)}", file=sys.stderr)
    print(f"  Max gen: {world.stats.max_generation}", file=sys.stderr)
    print(f"  Peak pop: {world.stats.peak_population}", file=sys.stderr)


def _top_killers(world: World) -> list[dict]:
    """Get the top 5 killers from graveyard + living organisms."""
    all_orgs = [
        {"id": o.id, "kills": o.kills, "gen": o.generation, "age": o.age, "alive": True}
        for o in world.organisms if o.kills > 0
    ] + [
        {**g, "alive": False}
        for g in world.graveyard if g.get("kills", 0) > 0
    ]
    all_orgs.sort(key=lambda x: x.get("kills", 0), reverse=True)
    return all_orgs[:5]


if __name__ == "__main__":
    main()
