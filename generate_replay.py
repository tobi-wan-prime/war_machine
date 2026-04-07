#!/usr/bin/env python3
"""Generate a replay JSON file for the web viewer.

Usage:
  python generate_replay.py                          # default scenario
  python generate_replay.py --scenario gauntlet      # use a preset
  python generate_replay.py --ticks 1000 --terrain   # custom config
  python generate_replay.py --list-scenarios         # show available presets
"""

from __future__ import annotations

import argparse
import sys
import time

from arena.world import World
from arena.exporter import ReplayExporter
from arena.scenarios import SCENARIOS, list_scenarios
from arena.embed import generate_embedded_html


def main() -> None:
    p = argparse.ArgumentParser(description="Generate replay for War Machine viewer")
    p.add_argument("--scenario", type=str, default=None,
                   help="Use a preset scenario (see --list-scenarios)")
    p.add_argument("--list-scenarios", action="store_true",
                   help="List available scenarios and exit")
    p.add_argument("--ticks", type=int, default=None)
    p.add_argument("--width", type=int, default=None)
    p.add_argument("--height", type=int, default=None)
    p.add_argument("--pop", type=int, default=None)
    p.add_argument("--food-rate", type=int, default=None)
    p.add_argument("--sample-rate", type=int, default=2)
    p.add_argument("--terrain", action="store_true", default=None)
    p.add_argument("--terrain-seed", type=int, default=None)
    p.add_argument("--embed", action="store_true",
                   help="Generate self-contained HTML (no JSON file needed)")
    p.add_argument("--output", type=str, default=None)
    args = p.parse_args()

    if args.list_scenarios:
        print(list_scenarios())
        return

    # start from scenario defaults or built-in defaults
    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"Unknown scenario '{args.scenario}'. Use --list-scenarios.", file=sys.stderr)
            sys.exit(1)
        sc = SCENARIOS[args.scenario]
        width = args.width or sc.width
        height = args.height or sc.height
        pop = args.pop or sc.pop
        food_rate = args.food_rate or sc.food_rate
        ticks = args.ticks or sc.ticks
        enable_events = sc.enable_events
        enable_terrain = args.terrain if args.terrain is not None else sc.enable_terrain
        terrain_seed = args.terrain_seed if args.terrain_seed is not None else sc.terrain_seed
        print(f"Scenario: {sc.name} -- {sc.description}", file=sys.stderr)
    else:
        width = args.width or 80
        height = args.height or 40
        pop = args.pop or 25
        food_rate = args.food_rate or 5
        ticks = args.ticks or 500
        enable_events = True
        enable_terrain = bool(args.terrain)
        terrain_seed = args.terrain_seed

    day_length = 100
    genome_presets = None
    if args.scenario and args.scenario in SCENARIOS:
        day_length = SCENARIOS[args.scenario].day_length
        genome_presets = SCENARIOS[args.scenario].genome_presets

    world = World(
        width=width, height=height,
        initial_organisms=pop, food_rate=food_rate,
        enable_events=enable_events,
        enable_terrain=enable_terrain,
        terrain_seed=terrain_seed,
        day_length=day_length,
        genome_presets=genome_presets,
    )
    exporter = ReplayExporter(sample_rate=args.sample_rate)
    exporter.set_config(world)

    print(f"Simulating {ticks} ticks ({width}x{height}, pop={pop}, food={food_rate})...",
          file=sys.stderr)
    t0 = time.perf_counter()

    for i in range(ticks):
        world.tick()
        exporter.capture(world)
        if (i + 1) % 100 == 0:
            elapsed = time.perf_counter() - t0
            sp_count = len(world.species_tracker.get_active_species())
            print(f"  Tick {i+1}/{ticks}  ({(i+1)/elapsed:.0f} tps)  "
                  f"pop={len(world.organisms)}  species={sp_count}  "
                  f"frames={len(exporter.frames)}",
                  file=sys.stderr)

    elapsed = time.perf_counter() - t0
    exporter.finalize(world)
    json_data = exporter.to_json()
    sp_summary = world.species_tracker.get_summary()

    if args.embed:
        # generate self-contained HTML
        scenario_label = args.scenario.title() if args.scenario else "Custom"
        html_data = generate_embedded_html(json_data, scenario_name=scenario_label)
        output_file = args.output or "arena_replay.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_data)
        size_kb = len(html_data) / 1024
        print(f"\nSelf-contained replay saved to {output_file}", file=sys.stderr)
        print(f"  {len(exporter.frames)} frames, {size_kb:.0f} KB", file=sys.stderr)
        print(f"  {sp_summary['active_count']} active species "
              f"({sp_summary['total_ever']} total observed)", file=sys.stderr)
        print(f"  Simulated in {elapsed:.2f}s", file=sys.stderr)
        print(f"\nDouble-click {output_file} to watch!", file=sys.stderr)
    else:
        output_file = args.output or "replay.json"
        with open(output_file, "w") as f:
            f.write(json_data)
        size_kb = len(json_data) / 1024
        print(f"\nReplay saved to {output_file}", file=sys.stderr)
        print(f"  {len(exporter.frames)} frames, {size_kb:.0f} KB", file=sys.stderr)
        print(f"  {sp_summary['active_count']} active species "
              f"({sp_summary['total_ever']} total observed)", file=sys.stderr)
        print(f"  Simulated in {elapsed:.2f}s", file=sys.stderr)
        print(f"\nOpen viewer.html in a browser and load {output_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
