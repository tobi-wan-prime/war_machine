"""Environmental events that disrupt the ecosystem."""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    DROUGHT = auto()       # food spawning halved
    BLOOM = auto()         # massive food surge
    PLAGUE = auto()         # random organisms lose energy
    METEOR = auto()         # kills organisms in a radius
    MIGRATION = auto()      # new random organisms appear


@dataclass
class Event:
    type: EventType
    tick_start: int
    duration: int
    x: float = 0.0        # epicenter for localized events
    y: float = 0.0
    radius: float = 0.0
    intensity: float = 1.0

    @property
    def description(self) -> str:
        names = {
            EventType.DROUGHT: "DROUGHT -- food scarce",
            EventType.BLOOM: "BLOOM -- food surge",
            EventType.PLAGUE: "PLAGUE -- energy drain",
            EventType.METEOR: "METEOR STRIKE",
            EventType.MIGRATION: "MIGRATION -- newcomers",
        }
        return names.get(self.type, str(self.type))

    def is_active(self, tick: int) -> bool:
        return self.tick_start <= tick < self.tick_start + self.duration


class EventScheduler:
    """Generates random environmental events on a schedule."""

    def __init__(self, world_width: int, world_height: int,
                 min_interval: int = 50, max_interval: int = 150):
        self.world_width = world_width
        self.world_height = world_height
        self.min_interval = min_interval
        self.max_interval = max_interval
        self._next_event_tick = random.randint(30, 80)
        self.active_events: list[Event] = []
        self.event_log: list[Event] = []

    def tick(self, current_tick: int) -> Event | None:
        """Check if a new event should fire. Returns the event or None."""
        # expire old events
        self.active_events = [e for e in self.active_events if e.is_active(current_tick)]

        # check if it's time for a new event
        if current_tick < self._next_event_tick:
            return None

        event = self._generate_event(current_tick)
        self.active_events.append(event)
        self.event_log.append(event)
        self._next_event_tick = current_tick + random.randint(self.min_interval, self.max_interval)
        return event

    def _generate_event(self, tick: int) -> Event:
        etype = random.choice(list(EventType))
        cx = random.uniform(0, self.world_width)
        cy = random.uniform(0, self.world_height)

        if etype == EventType.DROUGHT:
            return Event(type=etype, tick_start=tick, duration=random.randint(20, 50),
                         intensity=random.uniform(0.3, 0.7))

        elif etype == EventType.BLOOM:
            return Event(type=etype, tick_start=tick, duration=random.randint(10, 30),
                         x=cx, y=cy, radius=random.uniform(10, 25),
                         intensity=random.uniform(2.0, 5.0))

        elif etype == EventType.PLAGUE:
            return Event(type=etype, tick_start=tick, duration=random.randint(15, 40),
                         intensity=random.uniform(1.0, 3.0))

        elif etype == EventType.METEOR:
            return Event(type=etype, tick_start=tick, duration=1,
                         x=cx, y=cy, radius=random.uniform(5, 15),
                         intensity=random.uniform(50, 200))

        else:  # MIGRATION
            return Event(type=etype, tick_start=tick, duration=1,
                         intensity=random.uniform(3, 8))

    def has_active(self, etype: EventType) -> bool:
        return any(e.type == etype for e in self.active_events)

    def get_active_descriptions(self) -> list[str]:
        return [e.description for e in self.active_events]
