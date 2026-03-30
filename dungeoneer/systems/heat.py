"""Heat system — tracks facility alert level raised by player actions.

Heat levels (1–5):
  1 GHOST    — undetected
  2 TRACE    — anomaly detected
  3 ALERT    — security response
  4 PURSUIT  — active pursuit
  5 BURN     — execution order

Heat accumulates from combat rounds, hacked nodes, and failed hacks.
It persists across floors (stored on Player.heat).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from dungeoneer.core import settings
from dungeoneer.core.event_bus import (
    bus,
    HackNodesCollectedEvent,
    HeatChangeEvent,
    HeatLevelUpEvent,
)

if TYPE_CHECKING:
    from dungeoneer.entities.player import Player

# Level names (index = level, 1-based; index 0 unused)
LEVEL_NAMES = ["", "GHOST", "TRACE", "ALERT", "PURSUIT", "BURN"]

# Colours per level (RGB)
LEVEL_COLOURS = [
    (80,  180,  80),   # 0 — unused
    (80,  200,  80),   # 1 GHOST    — green
    (180, 210,  60),   # 2 TRACE    — yellow-green
    (220, 150,  40),   # 3 ALERT    — orange
    (220,  60,  60),   # 4 PURSUIT  — red
    (180,  20,  20),   # 5 BURN     — deep red
]

# Tier cap per level (which enemy tiers can spawn on next floor)
_TIER_CAP = {1: 1, 2: 1, 3: 2, 4: 2, 5: 3}


class HeatSystem:
    """Manages heat state and reacts to game events to update it."""

    def __init__(self, player: "Player") -> None:
        self._player = player
        self._subscribed = False

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def heat(self) -> int:
        return self._player.heat

    @property
    def level(self) -> int:
        """Current heat level (1–5)."""
        raw = self._player.heat // settings.HEAT_PER_LEVEL + 1
        return min(raw, settings.HEAT_MAX_LEVEL)

    @property
    def progress(self) -> float:
        """Fill fraction within the current level bar (0.0–1.0).
        At max level the bar stays full."""
        if self.level >= settings.HEAT_MAX_LEVEL:
            return 1.0
        return (self._player.heat % settings.HEAT_PER_LEVEL) / settings.HEAT_PER_LEVEL

    @property
    def level_name(self) -> str:
        return LEVEL_NAMES[self.level]

    @property
    def level_colour(self) -> tuple:
        return LEVEL_COLOURS[self.level]

    # ------------------------------------------------------------------
    # Public mutators
    # ------------------------------------------------------------------

    def add_heat(self, amount: int) -> None:
        """Increase heat by *amount*. Posts HeatChangeEvent (and HeatLevelUpEvent if needed)."""
        if amount <= 0:
            return
        old_val = self._player.heat
        old_lvl = self.level
        max_heat = settings.HEAT_MAX_LEVEL * settings.HEAT_PER_LEVEL
        self._player.heat = min(old_val + amount, max_heat)
        new_lvl = self.level
        bus.post(HeatChangeEvent(old_val, self._player.heat, old_lvl, new_lvl))
        if new_lvl > old_lvl:
            bus.post(HeatLevelUpEvent(new_lvl))

    def reduce_heat(self, amount: int) -> None:
        """Decrease heat by *amount* (minimum 0). Posts HeatChangeEvent."""
        if amount <= 0:
            return
        old_val = self._player.heat
        old_lvl = self.level
        self._player.heat = max(0, old_val - amount)
        new_lvl = self.level
        bus.post(HeatChangeEvent(old_val, self._player.heat, old_lvl, new_lvl))

    def set_heat(self, value: int) -> None:
        """Directly set heat to *value* (clamped). Used by cheat menu."""
        old_val = self._player.heat
        old_lvl = self.level
        max_heat = settings.HEAT_MAX_LEVEL * settings.HEAT_PER_LEVEL
        self._player.heat = max(0, min(value, max_heat))
        new_lvl = self.level
        bus.post(HeatChangeEvent(old_val, self._player.heat, old_lvl, new_lvl))
        if new_lvl > old_lvl:
            bus.post(HeatLevelUpEvent(new_lvl))

    # ------------------------------------------------------------------
    # Derived values used by other systems
    # ------------------------------------------------------------------

    def tier_cap(self) -> int:
        """Max enemy tier that may spawn on the next floor load."""
        return _TIER_CAP[self.level]

    def hack_time_modifier(self) -> float:
        """Seconds to add/subtract from the base hack time_limit.
        Positive at low heat (more time), negative at high heat (less time)."""
        return settings.HEAT_HACK_TIME_OFFSET - self.level

    # ------------------------------------------------------------------
    # EventBus wiring
    # ------------------------------------------------------------------

    def subscribe(self) -> None:
        if not self._subscribed:
            bus.subscribe(HackNodesCollectedEvent, self._on_hack_nodes)
            self._subscribed = True

    def unsubscribe(self) -> None:
        if self._subscribed:
            bus.unsubscribe(HackNodesCollectedEvent, self._on_hack_nodes)
            self._subscribed = False

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_hack_nodes(self, event: HackNodesCollectedEvent) -> None:
        gain = event.nodes_collected * settings.HEAT_HACK_NODE
        if not event.success:
            gain += settings.HEAT_HACK_FAIL
        if gain > 0:
            self.add_heat(gain)
        if event.coolant_reduction > 0:
            self.reduce_heat(event.coolant_reduction)
