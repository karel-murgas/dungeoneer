"""Simple synchronous publish/subscribe event bus."""
from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


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
    killer: Any = None      # Actor that dealt the killing blow (or None)
    weapon_id: Any = None   # str weapon id used for the kill (or None)

@dataclass
class TurnEndEvent(Event):
    round_number: int

@dataclass
class StairEvent(Event):
    """Player stepped on exit stairs (legacy)."""
    pass

@dataclass
class ElevatorEvent(Event):
    """Player activated an adjacent elevator."""
    elevator_x: int = 0
    elevator_y: int = 0

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

@dataclass
class EnemyBurstQueueEvent(Event):
    """Subsequent shots of an enemy burst weapon — staggered visually by GameScene."""
    events: list  # list of DamageEvent

@dataclass
class HeatChangeEvent(Event):
    """Heat value changed (gain or reduction)."""
    old_value: int
    new_value: int
    old_level: int
    new_level: int

@dataclass
class HeatLevelUpEvent(Event):
    """Heat crossed into a higher level — triggers patrol spawn."""
    new_level: int

@dataclass
class HackNodesCollectedEvent(Event):
    """Posted when hack minigame finishes — reports heat impact to HeatSystem."""
    nodes_collected:   int   # total nodes hacked (each +HEAT_HACK_NODE)
    success:           bool  # False → extra HEAT_HACK_FAIL on top
    coolant_reduction: int   # total heat removed by COOLANT nodes
    all_nodes_cleared: bool = False  # True only when every loot node was collected

@dataclass
class RoomRevealedEvent(Event):
    """Posted the first time a room enters the player's FOV."""
    room: Any

@dataclass
class HealEvent(Event):
    """Emitted by Actor.heal() — amount is the actual HP restored (clamped to max)."""
    actor: Any
    amount: int

@dataclass
class BulletFiredEvent(Event):
    """Emitted once per shot in resolve_ranged."""
    shooter: Any
    weapon_id: str

@dataclass
class ContainerLootedEvent(Event):
    """Emitted on any container open (hack or physical)."""
    container: Any
    success: bool
    was_hacked: bool


# ---------------------------------------------------------------------------
# Bus
# ---------------------------------------------------------------------------

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[type[Event], list[Callable]] = {}

    def subscribe(self, event_type: type[Event], callback: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: type[Event], callback: Callable) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def post(self, event: Event) -> None:
        for cb in self._subscribers.get(type(event), []):
            cb(event)


# Module-level singleton — scenes import and use this directly.
bus: EventBus = EventBus()
