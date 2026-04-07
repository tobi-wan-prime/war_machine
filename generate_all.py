#!/usr/bin/env python3
"""Generate embedded HTML replays for all scenarios.

Creates a collection of self-contained replay files in the replays/ directory.
Each file can be opened directly in a browser — no server needed.
Also generates an index.html landing page linking to all replays.
"""

from __future__ import annotations

import os
import sys
import time

from arena.world import World
from arena.exporter import ReplayExporter
from arena.scenarios import SCENARIOS
from arena.embed import generate_embedded_html


def generate_index_html(entries: list[dict], output_dir: str) -> None:
    """Generate a landing page linking to all replay files."""
    cards_html = ""
    for e in entries:
        tags = []
        if e["events"]:
            tags.append("Events")
        if e["terrain"]:
            tags.append("Terrain")
        if e["presets"]:
            tags.append("Presets")
        tags_html = " ".join(
            f'<span class="tag">{t}</span>' for t in tags
        )

        cards_html += f"""
        <a href="{e['filename']}" class="card">
            <div class="card-header">
                <span class="card-name">{e['name']}</span>
                <span class="card-size">{e['size_kb']:.0f} KB</span>
            </div>
            <div class="card-desc">{e['description']}</div>
            <div class="card-config">{e['width']}x{e['height']} &middot; pop {e['pop']} &middot; food {e['food_rate']} &middot; {e['ticks']} ticks</div>
            <div class="card-stats">
                <div class="cs"><span class="cv">{e['final_pop']}</span> survivors</div>
                <div class="cs"><span class="cv">{e['total_born']}</span> born</div>
                <div class="cs"><span class="cv">{e['total_died']}</span> died</div>
                <div class="cs"><span class="cv">{e['total_kills']}</span> kills</div>
                <div class="cs"><span class="cv">{e['max_gen']}</span> max gen</div>
                <div class="cs"><span class="cv">{e['species']}</span> species</div>
            </div>
            <div class="card-tags">{tags_html}</div>
        </a>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>War Machine: Arena</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #0a0a12;
    color: #e0e0e0;
    font-family: 'Segoe UI', Consolas, monospace;
    padding: 30px 20px;
}}
h1 {{
    text-align: center;
    font-size: 2em;
    color: #ff6633;
    margin-bottom: 4px;
    letter-spacing: 2px;
}}
.subtitle {{
    text-align: center;
    color: #666;
    font-size: 0.9em;
    margin-bottom: 30px;
}}
.grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
    max-width: 1100px;
    margin: 0 auto;
}}
.card {{
    display: block;
    text-decoration: none;
    color: inherit;
    background: #0f0f1a;
    border: 1px solid #222;
    border-radius: 8px;
    padding: 16px;
    transition: all 0.2s;
}}
.card:hover {{
    border-color: #ff6633;
    background: #12122a;
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(255, 102, 51, 0.15);
}}
.card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
}}
.card-name {{
    font-size: 1.15em;
    font-weight: bold;
    color: #ff6633;
}}
.card-size {{
    font-size: 0.75em;
    color: #555;
}}
.card-desc {{
    color: #999;
    font-size: 0.85em;
    margin-bottom: 8px;
    line-height: 1.4;
}}
.card-config {{
    font-size: 0.75em;
    color: #555;
    margin-bottom: 8px;
}}
.card-stats {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4px;
    margin-bottom: 8px;
}}
.cs {{
    font-size: 0.75em;
    color: #666;
    background: #0a0a12;
    padding: 3px 6px;
    border-radius: 3px;
    border: 1px solid #1a1a2e;
}}
.cv {{
    color: #e0e0e0;
    font-weight: bold;
}}
.card-tags {{
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
}}
.tag {{
    font-size: 0.65em;
    padding: 2px 8px;
    border-radius: 10px;
    background: rgba(255, 102, 51, 0.1);
    border: 1px solid rgba(255, 102, 51, 0.3);
    color: #ff6633;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.footer {{
    text-align: center;
    margin-top: 30px;
    color: #333;
    font-size: 0.75em;
}}
.footer span {{ color: #ff6633; }}
.features {{
    max-width: 1100px;
    margin: 0 auto 24px;
    padding: 16px 20px;
    background: #0f0f1a;
    border: 1px solid #1a1a2e;
    border-radius: 8px;
}}
.features h2 {{
    color: #ff6633;
    font-size: 1em;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
.feat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 8px;
}}
.feat {{
    font-size: 0.8em;
    padding: 6px 10px;
    background: #0a0a12;
    border: 1px solid #1a1a2e;
    border-radius: 4px;
    line-height: 1.4;
}}
.feat b {{ color: #e0e0e0; }}
.feat {{ color: #888; }}
.section-label {{
    max-width: 1100px;
    margin: 0 auto 10px;
    color: #444;
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 1px;
}}
</style>
</head>
<body>
<h1>WAR MACHINE: ARENA</h1>
<div class="subtitle">Evolutionary Simulation &mdash; {len(entries)} Scenarios &middot; 128+ Tests &middot; Built Autonomously</div>

<div class="features">
<h2>Simulation Mechanics</h2>
<div class="feat-grid">
    <div class="feat"><b>11-Gene Genome</b> &mdash; speed, sense, aggression, size, efficiency, reproduction, mutation rate, memory, RGB color</div>
    <div class="feat"><b>Sexual Reproduction</b> &mdash; crossover + mutation when compatible organisms meet</div>
    <div class="feat"><b>Species Classification</b> &mdash; genome-distance clustering, phylogenetic tree tracking</div>
    <div class="feat"><b>Pack Hunting</b> &mdash; aggressive same-species organisms coordinate attacks on shared targets</div>
    <div class="feat"><b>Herding</b> &mdash; non-aggressive organisms seek nearby kin for safety in numbers</div>
    <div class="feat"><b>Kin Energy Sharing</b> &mdash; high-energy organisms donate to low-energy same-species neighbors</div>
    <div class="feat"><b>Cross-Species Symbiosis</b> &mdash; passive organisms of different species gain mutual energy from proximity</div>
    <div class="feat"><b>Territorial Defense</b> &mdash; moderate organisms defend claimed territory from intruders</div>
    <div class="feat"><b>Pheromone Trails</b> &mdash; food and danger chemicals diffuse through the grid, guiding decisions</div>
    <div class="feat"><b>Organism Memory</b> &mdash; genetically-sized memory stores food and danger locations</div>
    <div class="feat"><b>Day/Night Cycle</b> &mdash; light level affects sense range; night-adapted organisms gain an edge</div>
    <div class="feat"><b>Aging &amp; Death</b> &mdash; metabolic cost increases with age; tracked cause of death (starvation, old age, combat, meteor)</div>
    <div class="feat"><b>Random Events</b> &mdash; meteor strikes, migrations, food blooms, droughts, plagues</div>
    <div class="feat"><b>Procedural Terrain</b> &mdash; walls, toxic zones, and fertile areas from seeded generation</div>
</div>
</div>

<div class="features" style="margin-bottom:24px">
<h2>Viewer Features</h2>
<div class="feat-grid">
    <div class="feat"><b>Click-to-Follow</b> &mdash; track individual organisms across frames with trail rendering</div>
    <div class="feat"><b>Energy Sparkline</b> &mdash; mini lifetime energy graph for tracked organisms</div>
    <div class="feat"><b>Behavior Indicators</b> &mdash; colored dots show what each organism is doing (hunting, fleeing, grazing...)</div>
    <div class="feat"><b>Population Heatmap</b> &mdash; toggleable density overlay (H key)</div>
    <div class="feat"><b>Phylogenetic Tree</b> &mdash; species ancestry timeline with extinction markers</div>
    <div class="feat"><b>Death Cause Timeline</b> &mdash; stacked chart showing how organisms die over time</div>
    <div class="feat"><b>Behavior Distribution</b> &mdash; stacked area chart of population-wide behavioral states</div>
    <div class="feat"><b>Territory Overlay</b> &mdash; species-colored territory claims rendered on the map</div>
    <div class="feat"><b>Kill Crowns</b> &mdash; tiered visual markers for experienced predators (3/5/10+ kills)</div>
    <div class="feat"><b>Speed Presets</b> &mdash; 1x/2x/4x/8x playback with keyboard shortcuts</div>
</div>
</div>

<div class="section-label">Scenarios</div>
<div class="grid">
{cards_html}
</div>
<div class="footer">Built autonomously by <span>Claude</span> &middot; Digital organisms competing, evolving, and dying in a grid world</div>
</body>
</html>"""

    index_path = os.path.join(output_dir, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Index page -> {index_path}", file=sys.stderr)


def main() -> None:
    output_dir = os.path.join(os.path.dirname(__file__), "replays")
    os.makedirs(output_dir, exist_ok=True)

    total_t0 = time.perf_counter()
    generated = []
    index_entries = []

    for key, sc in SCENARIOS.items():
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"Generating: {sc.name} -- {sc.description}", file=sys.stderr)
        print(f"  Config: {sc.width}x{sc.height}, pop={sc.pop}, food={sc.food_rate}, "
              f"ticks={sc.ticks}", file=sys.stderr)

        world = World(
            width=sc.width, height=sc.height,
            initial_organisms=sc.pop, food_rate=sc.food_rate,
            enable_events=sc.enable_events,
            enable_terrain=sc.enable_terrain,
            terrain_seed=sc.terrain_seed,
            day_length=sc.day_length,
            genome_presets=sc.genome_presets,
        )
        exporter = ReplayExporter(sample_rate=2)
        exporter.set_config(world)

        t0 = time.perf_counter()
        for i in range(sc.ticks):
            world.tick()
            exporter.capture(world)

        elapsed = time.perf_counter() - t0
        exporter.finalize(world)
        json_data = exporter.to_json()
        html = generate_embedded_html(json_data, scenario_name=sc.name)

        filename = f"arena_{key}.html"
        output_file = os.path.join(output_dir, filename)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

        size_kb = len(html) / 1024
        sp = world.species_tracker.get_summary()
        print(f"  Done: {len(exporter.frames)} frames, {size_kb:.0f} KB, "
              f"{sp['active_count']} species, {elapsed:.1f}s", file=sys.stderr)
        generated.append((sc.name, output_file, size_kb))

        # collect stats for index page
        summary = world.get_population_summary()
        index_entries.append({
            "key": key,
            "name": sc.name,
            "description": sc.description,
            "width": sc.width,
            "height": sc.height,
            "pop": sc.pop,
            "food_rate": sc.food_rate,
            "ticks": sc.ticks,
            "events": sc.enable_events,
            "terrain": sc.enable_terrain,
            "presets": sc.genome_presets is not None,
            "filename": filename,
            "size_kb": size_kb,
            "final_pop": summary.get("count", 0),
            "total_born": world.stats.total_born,
            "total_died": world.stats.total_died,
            "total_kills": world.stats.total_kills,
            "max_gen": world.stats.max_generation,
            "species": sp.get("total_ever", 0),
        })

    # generate index page
    generate_index_html(index_entries, output_dir)

    total_elapsed = time.perf_counter() - total_t0
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"Generated {len(generated)} replays in {total_elapsed:.1f}s:", file=sys.stderr)
    for name, path, size in generated:
        print(f"  {name:12s} -> {path} ({size:.0f} KB)", file=sys.stderr)
    print(f"\nOpen replays/index.html to browse all scenarios!", file=sys.stderr)


if __name__ == "__main__":
    main()
