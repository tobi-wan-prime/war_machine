#!/usr/bin/env python3
"""War Machine: Arena — evolutionary simulation.

Run: python main.py [--width W] [--height H] [--pop N] [--food-rate R] [--speed S]
"""

from __future__ import annotations

import argparse
import sys
import time
import select
import msvcrt  # Windows-specific keyboard input

from arena.world import World
from arena.renderer import render, clear_screen


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="War Machine: Arena")
    p.add_argument("--width", type=int, default=80, help="Arena width (default: 80)")
    p.add_argument("--height", type=int, default=35, help="Arena height (default: 35)")
    p.add_argument("--pop", type=int, default=25, help="Initial population (default: 25)")
    p.add_argument("--food-rate", type=int, default=5, help="Food spawned per tick (default: 5)")
    p.add_argument("--speed", type=float, default=0.1, help="Seconds between ticks (default: 0.1)")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    world = World(
        width=args.width,
        height=args.height,
        initial_organisms=args.pop,
        food_rate=args.food_rate,
    )
    tick_delay = args.speed
    paused = False

    clear_screen()
    print("War Machine: Arena — starting simulation...")
    time.sleep(1)

    try:
        while True:
            # handle keyboard input (Windows)
            if msvcrt.kbhit():
                key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                if key == "q":
                    break
                elif key == "p":
                    paused = not paused
                elif key == "f":
                    tick_delay = max(0.01, tick_delay * 0.7)
                elif key == "s":
                    tick_delay = min(2.0, tick_delay * 1.4)

            if not paused:
                world.tick()

            clear_screen()
            frame = render(world)
            sys.stdout.write(frame + "\n")
            sys.stdout.flush()

            if paused:
                sys.stdout.write("  *** PAUSED ***\n")

            time.sleep(tick_delay)

    except KeyboardInterrupt:
        pass

    # final summary
    clear_screen()
    print("\n=== War Machine: Arena — Final Report ===")
    print(f"  Ticks simulated: {world.stats.tick}")
    print(f"  Total born:      {world.stats.total_born}")
    print(f"  Total died:      {world.stats.total_died}")
    print(f"  Total kills:     {world.stats.total_kills}")
    print(f"  Peak population: {world.stats.peak_population}")
    print(f"  Max generation:  {world.stats.max_generation}")
    summary = world.get_population_summary()
    if summary["count"] > 0:
        print(f"  Survivors:       {summary['count']}")
        print(f"  Avg speed:       {summary['avg_speed']}")
        print(f"  Avg size:        {summary['avg_size']}")
        print(f"  Avg aggression:  {summary['avg_aggression']}")
    print()


if __name__ == "__main__":
    main()
