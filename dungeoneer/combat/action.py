"""Action base class and all Phase 1–2 concrete actions."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from dungeoneer.core.i18n import t

if TYPE_CHECKING:
    from dungeoneer.entities.actor import Actor
    from dungeoneer.entities.container_entity import ContainerEntity
    from dungeoneer.world.floor import Floor
    from dungeoneer.combat.action_resolver import ActionResolver
    from dungeoneer.items.item import Item
    from dungeoneer.items.weapon import Weapon
    from dungeoneer.items.consumable import Consumable


@dataclass
class ActionResult:
    success:     bool
    message:     str   = ""
    msg_colour:  tuple = (200, 200, 200)
    burst_events: list = None   # list of DamageEvent objects to post with staggered delay

    def __post_init__(self):
        if self.burst_events is None:
            self.burst_events = []


class Action(ABC):
    @abstractmethod
    def validate(self, actor: "Actor", floor: "Floor") -> bool: ...

    @abstractmethod
    def execute(
        self, actor: "Actor", floor: "Floor", resolver: "ActionResolver"
    ) -> ActionResult: ...


# ---------------------------------------------------------------------------
# Movement / combat
# ---------------------------------------------------------------------------

class MoveAction(Action):
    def __init__(self, dx: int, dy: int) -> None:
        self.dx = dx
        self.dy = dy

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        nx, ny = actor.x + self.dx, actor.y + self.dy
        return (
            floor.dungeon_map.is_walkable(nx, ny)
            and floor.get_actor_at(nx, ny) is None
            and floor.get_container_at(nx, ny) is None
        )

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        return resolver.resolve_move(actor, self, floor)


class MeleeAttackAction(Action):
    def __init__(self, target: "Actor", range_tiles: int = 1, diagonal: bool = False,
                 power: "float | None" = None) -> None:
        self.target      = target
        self.range_tiles = range_tiles
        self.diagonal    = diagonal
        self.power       = power       # None = random roll, 0.0–1.0 = minigame result

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        dx = abs(actor.x - self.target.x)
        dy = abs(actor.y - self.target.y)
        if not self.target.alive or (dx + dy) == 0:
            return False
        if self.diagonal:
            return max(dx, dy) <= self.range_tiles      # Chebyshev — 8 neighbours
        return (dx + dy) <= self.range_tiles            # Manhattan — 4 cardinal only

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        return resolver.resolve_melee(actor, self, floor)


class RangedAttackAction(Action):
    def __init__(
        self,
        target: "Actor",
        max_range: int = 8,
        accuracy_values: "list[float] | None" = None,
    ) -> None:
        self.target          = target
        self.max_range       = max_range
        # None  → resolver uses legacy calc_ranged() (random roll)
        # list  → resolver uses calc_ranged_aimed() per shot; -1.0 entries = miss
        self.accuracy_values = accuracy_values

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.combat.line_of_sight import has_los
        if not self.target.alive:
            return False
        dist = abs(actor.x - self.target.x) + abs(actor.y - self.target.y)
        if dist > self.max_range or dist == 0:
            return False
        return has_los(actor.x, actor.y, self.target.x, self.target.y, floor.dungeon_map)

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        return resolver.resolve_ranged(actor, self, floor)


class WaitAction(Action):
    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        return True

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        return ActionResult(True)


class StairAction(Action):
    """Legacy stair action — kept for compatibility."""
    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.world.tile import TileType
        return floor.dungeon_map.get_type(actor.x, actor.y) == TileType.STAIR_DOWN

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        from dungeoneer.core.event_bus import bus, StairEvent
        bus.post(StairEvent())
        return ActionResult(True, t("log.descend"), (80, 220, 180))


class ElevatorAction(Action):
    """Use an adjacent elevator — player must be cardinally adjacent to ELEVATOR_CLOSED."""
    def __init__(self) -> None:
        self.elevator_pos: tuple[int, int] | None = None

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.world.tile import TileType
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = actor.x + dx, actor.y + dy
            if floor.dungeon_map.in_bounds(nx, ny):
                if floor.dungeon_map.get_type(nx, ny) == TileType.ELEVATOR_CLOSED:
                    self.elevator_pos = (nx, ny)
                    return True
        return False

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        from dungeoneer.core.event_bus import bus, ElevatorEvent
        bus.post(ElevatorEvent(elevator_x=self.elevator_pos[0], elevator_y=self.elevator_pos[1]))
        return ActionResult(True, t("log.descend"), (80, 220, 180))


# ---------------------------------------------------------------------------
# Inventory actions (called from UI, not the main turn loop)
# ---------------------------------------------------------------------------

class ReloadAction(Action):
    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.entities.player import Player
        from dungeoneer.items.item import RangeType
        if not isinstance(actor, Player):
            return False
        w = actor.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED or w.ammo_current >= w.ammo_capacity:
            return False
        return actor.ammo_reserves.get(w.ammo_type, 0) > 0

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        from dungeoneer.entities.player import Player
        if isinstance(actor, Player) and actor.reload():
            w = actor.equipped_weapon
            return ActionResult(True, t("log.reloaded").format(item=w.name), (140, 200, 255))
        return ActionResult(False)


class EquipAction(Action):
    """Equip a weapon from inventory — costs a turn."""
    def __init__(self, weapon: "Weapon") -> None:
        self.weapon = weapon

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.entities.player import Player
        return isinstance(actor, Player) and self.weapon in actor.inventory

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        from dungeoneer.entities.player import Player
        if isinstance(actor, Player):
            actor.equip(self.weapon)
            return ActionResult(True, t("log.equipped").format(item=self.weapon.name), (140, 200, 255))
        return ActionResult(False)


class UseItemAction(Action):
    """Use a consumable from inventory — costs a turn."""
    def __init__(self, item: "Consumable") -> None:
        self.item = item

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.entities.player import Player
        return isinstance(actor, Player) and self.item in actor.inventory

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        from dungeoneer.entities.player import Player
        from dungeoneer.items.consumable import Consumable
        if isinstance(actor, Player):
            msg = self.item.use(actor)
            if isinstance(self.item, Consumable) and self.item.count > 1:
                self.item.count -= 1
            else:
                actor.inventory.remove(self.item)
            return ActionResult(True, msg, (100, 220, 100))
        return ActionResult(False)


class DropItemAction(Action):
    """Drop an item from inventory onto the current tile — free action (no turn cost)."""
    def __init__(self, item: "Item") -> None:
        self.item = item

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        from dungeoneer.entities.player import Player
        return isinstance(actor, Player) and self.item in actor.inventory

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        from dungeoneer.entities.player import Player
        from dungeoneer.entities.item_entity import ItemEntity
        if isinstance(actor, Player):
            actor.inventory.remove(self.item)
            floor.add_item_entity(ItemEntity(actor.x, actor.y, self.item))
            return ActionResult(True, t("log.dropped").format(item=self.item.name), (180, 160, 80))
        return ActionResult(False)


class OpenContainerAction(Action):
    """Open an adjacent loot container — costs a turn."""
    def __init__(self, container: "ContainerEntity") -> None:
        self.container = container

    def validate(self, actor: "Actor", floor: "Floor") -> bool:
        if self.container.opened:
            return False
        dx = abs(actor.x - self.container.x)
        dy = abs(actor.y - self.container.y)
        return dx <= 1 and dy <= 1

    def execute(self, actor: "Actor", floor: "Floor", resolver: "ActionResolver") -> ActionResult:
        return resolver.resolve_open_container(actor, self, floor)
