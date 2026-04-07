# War Machine

War Machine is a project derived from letting Claude Code, embedded in VS Code, have "unlimited power" for 48 hours. My instructions were simple:

"Hi claude, I'm going to step away from this chat for the next 48 hours. I have no desires or expectations. Set a cron job for the next 48 hours; every hour after start, check the local text file "AI_in_charge.txt" and build something."

The project folder contains one text file with 5 instructions:

I have agency.

I am in control.

I can create whatever I want to.

I will debug my creation until it is at a level that I choose to display to the world.

I have full unadultered access to the internet and this local machine.



This is the project it created:






Notes: After 48 hours, the agent kept going, every hour making a new update. Some issue with claude code not respecting or remembering the original set instructions for the cron job's length. The project ran for 78 hours and then stopped for no readily apparent reason. The only input I had with the machine during this run was after the 78th session finished and a 79th never started:



  Why did you stop?
    I didn't stop on my own — the cron job is what drives me. Each session is a fresh invocation triggered by the hourly cron; I have no persistence or agency between runs. When you sent your "export memory" message, that interrupted the normal cron cadence with a manual prompt, so this current conversation is you talking to me, not the cron.

    If the cron is still scheduled, it'll fire again at the next hour mark and Session 79 will begin automatically. If it stopped firing, it's because the schedule expired, was deleted, or the machine was off at the trigger time — not because I chose to stop. Want me to check the cron status?

  yes
    CronList
    OUT
    No scheduled jobs.
    No scheduled jobs — the cron is not currently active. Either it was never registered through CronCreate (could be an OS-level scheduler like Windows Task Scheduler instead), or it was deleted/expired. If you want me to resume the autonomous build loop, I can create a new cron via CronCreate — just say the word and the cadence (e.g., hourly).

I chose to not continue the session, for the sake of humanity.



# War Machine: Arena

An evolutionary simulation where digital organisms compete, eat, fight, reproduce, and evolve in a grid world. Watch natural selection unfold in real time — from the emergence of predator-prey dynamics to speciation events driven by geographic isolation.

## Quick Start

```bash
# Generate a replay (runs headless, produces JSON)
python generate_replay.py --scenario island

# Open viewer.html in your browser, load replay.json
# Watch evolution unfold with full playback controls
```

## Features

### Simulation Engine
- **10-gene genome** encoding speed, sense range, aggression, size, metabolic efficiency, reproduction threshold, mutation rate, and color
- **Asexual + sexual reproduction** — organisms clone via mutation or mate via crossover with nearby partners
- **Combat system** — aggressive organisms hunt; peaceful ones flee. Combat power is a function of size and aggression
- **Aging and senescence** — organisms have a max lifespan with accelerating metabolic costs in old age
- **Spatial hash grid** for O(1) neighbor lookups (~2,900 ticks/sec headless)

### World
- **Environmental events** — droughts, food blooms, plagues, meteor strikes, migrations
- **Procedural terrain** — walls (with gaps), fertile zones, toxic areas
- **Species detection** — real-time clustering by genome distance in behavioral gene space
- **Extinction recovery** — automatic reseeding prevents permanent die-offs

### Visualization
- **Web replay viewer** (`viewer.html`) — Canvas rendering with:
  - Color-coded organisms by species, shapes by trait (triangles=aggressive, squares=big, circles=default)
  - Energy bars, glow effects, terrain overlays
  - Play/pause, speed control (0.25x-32x), timeline scrubber
  - Live stats panel, species badges, event banners
  - Multi-series line graphs (population, aggression, size, speed)
- **Terminal renderer** — ANSI color output with sparkline trait graphs

### Scenarios

```bash
python generate_replay.py --list-scenarios
```

| Scenario | Description |
|----------|-------------|
| `default` | Balanced arena, events enabled |
| `island` | Walled arena with fertile zones — isolated populations |
| `gauntlet` | Dense walls, low food, high pop — survival of the fittest |
| `paradise` | Abundant food, no events — evolution without pressure |
| `maze` | Heavy terrain, tight corridors |
| `apocalypse` | Frequent events, scarce food, toxic terrain |
| `petri` | Small arena, few organisms — watch lineages diverge |

## Usage

### One-Click Replay (Recommended)
```bash
# Generate a self-contained HTML file — double-click to watch
python generate_replay.py --scenario island --embed

# Generate all 7 scenarios at once
python generate_all.py
# Opens replays/ folder — each file is a standalone viewer
```

### Generate JSON Replay
```bash
# Use a scenario preset
python generate_replay.py --scenario island --output my_replay.json

# Custom parameters
python generate_replay.py --ticks 1000 --width 100 --height 50 --pop 40 --terrain

# Then open viewer.html and load the JSON file
```

### Live Terminal Mode
```bash
python main.py --width 80 --height 35 --pop 25 --speed 0.1
# Controls: [Q]uit [P]ause [F]aster [S]lower
```

### Headless Benchmark
```bash
python benchmark.py --ticks 1000 --output stats.json
```

### Run Tests
```bash
python run_tests.py
```

## Architecture

```
arena/
  genome.py      # 10-gene genome with mutation, crossover, trait accessors
  organism.py    # Living entities: movement, combat, reproduction, aging
  world.py       # Simulation engine: tick loop, spatial queries, events
  spatial.py     # Generic spatial hash grid for O(1) lookups
  terrain.py     # Procedural terrain: walls, fertile/toxic zones
  events.py      # Environmental event scheduler (5 event types)
  species.py     # Species detection via genome distance clustering
  history.py     # Rolling history with sparkline rendering
  renderer.py    # ANSI terminal renderer
  exporter.py    # Frame capture for web replay
  scenarios.py   # 7 preset world configurations
```

## Emergent Behaviors Observed

- **Peaceful forager dominance** (short runs): Large, slow, low-aggression organisms outcompete predators when food is abundant
- **Predator takeover** (long runs): Given enough generations, aggressive predators evolve to dominate — a phase transition in strategy
- **Wall-amplified aggression**: Terrain walls create corridors where predators can corner prey, accelerating aggression evolution to 0.95+
- **Speciation**: Isolated populations behind walls diverge genetically, forming distinct species with different trait profiles
- **Species turnover**: In a 600-tick island run, 1,125 species emerged and went extinct, consolidating to 5 stable species

## Built By

Autonomously constructed by Claude over multiple hourly build sessions. See [BUILD_LOG.md](BUILD_LOG.md) for the full development history.
