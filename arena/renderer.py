"""Terminal renderer for the arena simulation."""

from __future__ import annotations

import sys
from .world import World


# ANSI escape helpers
def _rgb_fg(r: int, g: int, b: int) -> str:
    return f"\033[38;2;{r};{g};{b}m"

RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"
FOOD_COLOR = _rgb_fg(50, 200, 50)
BG_CHAR = DIM + "." + RESET
FOOD_CHAR = FOOD_COLOR + "+" + RESET


def clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")


def render(world: World) -> str:
    """Render the world state to a string for terminal display."""
    # build grid
    grid: list[list[str]] = [[BG_CHAR for _ in range(world.width)] for _ in range(world.height)]

    # place food
    for f in world.food:
        fx, fy = int(f.x) % world.width, int(f.y) % world.height
        grid[fy][fx] = FOOD_CHAR

    # place organisms (larger ones rendered on top)
    sorted_orgs = sorted(world.organisms, key=lambda o: o.genome.size)
    for org in sorted_orgs:
        ox, oy = int(org.x) % world.width, int(org.y) % world.height
        r, g, b = org.genome.color
        # ensure minimum brightness
        brightness = r + g + b
        if brightness < 150:
            scale = 150 / max(brightness, 1)
            r = min(255, int(r * scale))
            g = min(255, int(g * scale))
            b = min(255, int(b * scale))

        # pick glyph based on dominant trait
        if org.genome.aggression > 0.7:
            glyph = "A"   # aggressive
        elif org.genome.size > 1.2:
            glyph = "#"   # big
        elif org.genome.speed > 1.5:
            glyph = ">"   # fast
        else:
            glyph = "o"   # default

        grid[oy][ox] = _rgb_fg(r, g, b) + glyph + RESET

    # assemble frame
    summary = world.get_population_summary()
    stats_line = (
        f"{BOLD}Tick {world.stats.tick}{RESET} | "
        f"Pop: {summary['count']} | "
        f"Food: {summary.get('food_available', 0)} | "
        f"Gen: {summary.get('max_generation', 0)} | "
        f"Born: {world.stats.total_born} | "
        f"Died: {world.stats.total_died} | "
        f"Kills: {world.stats.total_kills}"
    )

    trait_line = ""
    if summary["count"] > 0:
        trait_line = (
            f"  Avg Speed: {summary.get('avg_speed', 0):.1f} | "
            f"Size: {summary.get('avg_size', 0):.1f} | "
            f"Aggro: {summary.get('avg_aggression', 0):.2f} | "
            f"Energy: {summary.get('avg_energy', 0):.0f} | "
            f"Gen: {summary.get('avg_generation', 0):.1f}"
        )

    border = "-" * world.width
    frame_lines = []
    frame_lines.append(f"+{border}+")
    for row in grid:
        frame_lines.append(f"|{''.join(row)}|")
    frame_lines.append(f"+{border}+")
    frame_lines.append(stats_line)
    if trait_line:
        frame_lines.append(trait_line)

    # sparkline graphs from history
    h = world.history
    if len(h.snapshots) >= 5:
        graph_width = min(50, world.width - 10)
        frame_lines.append("")
        frame_lines.append(h.sparkline("population", width=graph_width, label="  Pop  "))
        frame_lines.append(h.sparkline("avg_aggression", width=graph_width, label="  Aggro"))
        frame_lines.append(h.sparkline("avg_size", width=graph_width, label="  Size "))
        frame_lines.append(h.sparkline("avg_speed", width=graph_width, label="  Speed"))

    # active events
    if world.events and world.events.active_events:
        event_descs = world.events.get_active_descriptions()
        event_color = _rgb_fg(255, 100, 50)
        frame_lines.append(f"  {event_color}!! {' | '.join(event_descs)} !!{RESET}")

    frame_lines.append(f"{DIM}[Q]uit  [P]ause  [F]aster  [S]lower{RESET}")

    return "\n".join(frame_lines)
