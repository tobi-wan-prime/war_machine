"""Export simulation frames for web replay."""

from __future__ import annotations

import json
from dataclasses import dataclass
from .world import World
from .pheromones import PheromoneMap


@dataclass
class FrameData:
    tick: int
    organisms: list[dict]
    food: list[dict]
    stats: dict
    events: list[str]
    pheromones: dict | None = None
    territory: dict | None = None


class ReplayExporter:
    """Captures simulation frames at a given sample rate for web replay."""

    def __init__(self, sample_rate: int = 2):
        self.sample_rate = sample_rate
        self.frames: list[FrameData] = []
        self.config: dict = {}

    def set_config(self, world: World) -> None:
        self.config = {
            "width": world.width,
            "height": world.height,
            "food_rate": world.food_rate,
            "terrain": world.terrain.to_lists(),
        }

    def capture(self, world: World) -> None:
        if world.stats.tick % self.sample_rate != 0:
            return

        tracker = world.species_tracker
        orgs = []
        for o in world.organisms:
            # use species color if available, else genome color
            sp = tracker.get_species_for(o.id)
            if sp:
                r, g, b = sp.color
            else:
                r, g, b = o.genome.color
                brightness = r + g + b
                if brightness < 150:
                    scale = 150 / max(brightness, 1)
                    r = min(255, int(r * scale))
                    g = min(255, int(g * scale))
                    b = min(255, int(b * scale))

            orgs.append({
                "id": o.id,
                "x": round(o.x, 2),
                "y": round(o.y, 2),
                "r": r, "g": g, "b": b,
                "size": round(o.genome.size, 2),
                "aggro": round(o.genome.aggression, 2),
                "speed": round(o.genome.speed, 2),
                "energy": round(o.energy, 1),
                "gen": o.generation,
                "age": o.age,
                "mxa": o.max_age,
                "sp": sp.id if sp else 0,
                "mem": o.genome.memory_capacity,
                "kills": o.kills,
                "bh": o.behavior,
                "pid": o.parent_id,
                "ch": o.children,
                "gn": [round(g, 2) for g in o.genome.genes[:8]] + [round(o.genome.stamina, 2)],
                "ad": round(o.adaptation, 2),
                "sc": o.scars,
                "ft": round(o.fatigue, 2),
            })

        # sample food (cap at 200 for file size)
        food_list = world.food[:200]
        food = [{"x": round(f.x, 2), "y": round(f.y, 2)} for f in food_list]

        summary = world.get_population_summary()
        events = world.events.get_active_descriptions() if world.events else []

        # capture pheromone heatmaps (cap entries for file size)
        food_phero = world.pheromones.get_heatmap(PheromoneMap.FOOD, threshold=0.05)
        danger_phero = world.pheromones.get_heatmap(PheromoneMap.DANGER, threshold=0.05)
        # limit to strongest 150 cells each
        if len(food_phero) > 150:
            food_phero.sort(key=lambda t: t[2], reverse=True)
            food_phero = food_phero[:150]
        if len(danger_phero) > 150:
            danger_phero.sort(key=lambda t: t[2], reverse=True)
            danger_phero = danger_phero[:150]

        phero = None
        if food_phero or danger_phero:
            phero = {
                "cs": world.pheromones.cell_size,
                "food": [[c, r, round(v, 2)] for c, r, v in food_phero],
                "danger": [[c, r, round(v, 2)] for c, r, v in danger_phero],
            }

        # territory map
        terr_data = world.territory.get_territory_map(threshold=0.15)
        # cap at 200 cells for file size
        if len(terr_data) > 200:
            terr_data.sort(key=lambda t: t[3], reverse=True)
            terr_data = terr_data[:200]

        # build territory export (with species colors for rendering)
        terr_export = None
        if terr_data:
            terr_export = {
                "cs": world.territory.cell_size,
                "cells": [],
            }
            for c, r, sp_id, strength in terr_data:
                sp = tracker.get_species_by_id(sp_id)
                if sp:
                    sr, sg, sb = sp.color
                    terr_export["cells"].append([c, r, sr, sg, sb, strength])

        self.frames.append(FrameData(
            tick=world.stats.tick,
            organisms=orgs,
            food=food,
            stats={
                "pop": summary["count"],
                "food": summary.get("food_available", 0),
                "born": world.stats.total_born,
                "died": world.stats.total_died,
                "kills": world.stats.total_kills,
                "max_gen": world.stats.max_generation,
                "avg_aggro": summary.get("avg_aggression", 0),
                "avg_size": summary.get("avg_size", 0),
                "avg_speed": summary.get("avg_speed", 0),
                "avg_energy": summary.get("avg_energy", 0),
                "avg_gen": summary.get("avg_generation", 0),
                "matings": summary.get("matings", 0),
                "avg_memory": summary.get("avg_memory", 0),
                "time_of_day": summary.get("time_of_day", 0.5),
                "light_level": summary.get("light_level", 1.0),
                "shares": summary.get("shares", 0),
                "d_starved": summary.get("deaths_starved", 0),
                "d_old_age": summary.get("deaths_old_age", 0),
                "d_combat": summary.get("deaths_combat", 0),
                "d_meteor": summary.get("deaths_meteor", 0),
                "symbiosis": summary.get("symbiosis", 0),
                "genetics": summary.get("genetics", {}),
                "species": tracker.get_summary(),
            },
            events=events,
            pheromones=phero,
            territory=terr_export,
        ))

    def finalize(self, world: World) -> None:
        """Capture end-of-simulation data like phylogeny and death log."""
        self.config["phylogeny"] = world.species_tracker.get_phylogeny()
        # death log: {organism_id: cause} for tracked organism death lookup
        self.config["deaths"] = {
            g["id"]: g.get("cause", "unknown") for g in world.graveyard
        }
        # kill positions: [x, y, cause_code] for kill heatmap
        # cause codes: 0=starved, 1=old_age, 2=combat, 3=meteor
        cause_map = {"starved": 0, "old_age": 1, "combat": 2, "meteor": 3}
        self.config["kill_pos"] = [
            [g.get("x", 0), g.get("y", 0), cause_map.get(g.get("cause", ""), 0)]
            for g in world.graveyard if "x" in g
        ]
        # combat log: individual kills with killer/victim IDs
        self.config["combat_log"] = [
            {"k": g["killer"], "v": g["id"], "t": g["tick"]}
            for g in world.graveyard
            if g.get("cause") == "combat" and g.get("killer", 0) > 0
        ]
        # food chain: list of {killer, victim, count} for predation network
        self.config["food_chain"] = [
            {"k": k, "v": v, "n": n}
            for (k, v), n in sorted(
                world.stats.food_chain.items(),
                key=lambda x: x[1], reverse=True,
            )
        ]

    def to_json(self) -> str:
        data = {
            "config": self.config,
            "frame_count": len(self.frames),
            "frames": [
                {
                    "t": f.tick,
                    "o": f.organisms,
                    "f": f.food,
                    "s": f.stats,
                    "e": f.events,
                    **({"ph": f.pheromones} if f.pheromones else {}),
                    **({"tr": f.territory} if f.territory else {}),
                }
                for f in self.frames
            ],
        }
        return json.dumps(data, separators=(",", ":"))
