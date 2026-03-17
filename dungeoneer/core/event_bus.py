"""Simple synchronous publish/subscribe event bus."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Type


# ---------------------------------------------------------------------------
# Event base
# ---------------------------------------------------------------------------

@dataclass
class Event:
    pass


# ---------------------------------------------------------------------------
# Game events
# ---------------------------------------------------------------------------

@dataclass
class MoveEvent(Event):
    actor: Any
    x: int
    y: int

@dataclass
class DamageEvent(Event):
    attacker: Any
    target: Any
    amount: int
    is_ranged: bool = False
    is_crit:   bool = False

@dataclass
class DeathEvent(Event):
    entity: Any

@dataclass
class LootEvent(Event):
    actor: Any
    item: Any

@dataclass
class TurnStartEvent(Event):
    actor: Any
    round_number: int

@dataclass
class TurnEndEvent(Event):
    round_number: int

@dataclass
class FloorClearEvent(Event):
    pass

@dataclass
class StairEvent(Event):
    """Player stepped on exit stairs."""
    pass

@dataclass
class ObjectiveEvent(Event):
    """Player secured the mission objective (Corp Vault)."""
    credits_gained: int

@dataclass
class MissEvent(Event):
    attacker: Any
    target:   Any

@dataclass
class LogMessageEvent(Event):
    message: str
    colour: tuple = field(default_factory=lambda: (200, 200, 200))


# ---------------------------------------------------------------------------
# Bus
# ---------------------------------------------------------------------------

class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[Type[Event], List[Callable]] = {}

    def subscribe(self, event_type: Type[Event], callback: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: Type[Event], callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def post(self, event: Event) -> None:
        for cb in self._subscribers.get(type(event), []):
            cb(event)


# Module-level singleton — scenes import and use this directly.
bus: EventBus = EventBus()
