"""ActionResolver — the only place where world state is mutated by actions."""
from __future__ import annotations

import logging

from dungeoneer.combat.action import ActionResult, MoveAction, MeleeAttackAction, RangedAttackAction
from dungeoneer.combat.damage import calc_melee, calc_ranged

log = logging.getLogger(__name__)


class ActionResolver:
    def resolve_move(
        self, actor: "Actor", action: MoveAction, floor: "Floor"  # type: ignore[name-defined]
    ) -> ActionResult:
        from dungeoneer.core.event_bus import bus, MoveEvent
        from dungeoneer.world.fov import compute_fov
        from dungeoneer.entities.player import Player

        actor.x += action.dx
        actor.y += action.dy

        if isinstance(actor, Player):
            compute_fov(actor.x, actor.y, floor.dungeon_map)
            bus.post(MoveEvent(actor, actor.x, actor.y))
            # Auto-pickup items on this tile
            self._auto_pickup(actor, floor)

        return ActionResult(True)

    def _auto_pickup(self, player: "Player", floor: "Floor") -> None:  # type: ignore[name-defined]
        from dungeoneer.core.event_bus import bus, LogMessageEvent
        from dungeoneer.items.ammo import AmmoPickup
        from dungeoneer.items.weapon import Weapon
        from dungeoneer.items.item import RangeType

        items_here = floor.get_items_at(player.x, player.y)
        if not items_here:
            return

        inventory_full_warned = False

        for item_e in list(items_here):  # snapshot — list mutates during loop
            item = item_e.item

            # --- Ammo pickups → straight to reserves ---
            if isinstance(item, AmmoPickup):
                player.ammo_reserves[item.ammo_type] = (
                    player.ammo_reserves.get(item.ammo_type, 0) + item.ammo_count
                )
                floor.remove_item_entity(item_e)
                log.info("Ammo pickup: %s at (%d,%d)", item.name, player.x, player.y)
                bus.post(LogMessageEvent(f"Picked up {item.name}.", (200, 220, 100)))
                continue

            # --- Melee weapons → always discard ---
            if isinstance(item, Weapon) and item.range_type == RangeType.MELEE:
                floor.remove_item_entity(item_e)
                log.info("Discarded melee weapon: %s at (%d,%d)", item.name, player.x, player.y)
                bus.post(LogMessageEvent(f"Left {item.name} behind.", (120, 100, 80)))
                continue

            # --- Ranged weapon duplicate → strip for ammo instead ---
            if isinstance(item, Weapon) and item.range_type == RangeType.RANGED:
                already_have = (
                    (player.equipped_weapon is not None and player.equipped_weapon.id == item.id)
                    or any(isinstance(i, Weapon) and i.id == item.id for i in player.inventory)
                )
                if already_have and item.ammo_type:
                    gained = item.ammo_capacity
                    player.ammo_reserves[item.ammo_type] = (
                        player.ammo_reserves.get(item.ammo_type, 0) + gained
                    )
                    floor.remove_item_entity(item_e)
                    log.info("Stripped %s for %d ammo at (%d,%d)", item.name, gained, player.x, player.y)
                    bus.post(LogMessageEvent(f"Stripped {item.name}: +{gained} {item.ammo_type}.", (180, 200, 120)))
                    continue

            # --- Default: add to inventory (Inventory.add handles consumable stacking) ---
            if player.inventory.add(item):
                floor.remove_item_entity(item_e)
                log.info("Auto-pickup: %s at (%d,%d)", item.name, player.x, player.y)
                from dungeoneer.items.consumable import Consumable
                existing = next((i for i in player.inventory if isinstance(i, Consumable) and i.id == item.id), None)
                count_str = f" ×{existing.count}" if existing and existing.count > 1 else ""
                bus.post(LogMessageEvent(f"Picked up {item.name}{count_str}.", (240, 220, 80)))
            elif not inventory_full_warned:
                inventory_full_warned = True
                bus.post(LogMessageEvent("Inventory full — can't pick up item.", (180, 80, 80)))

    def resolve_melee(
        self, actor: "Actor", action: MeleeAttackAction, floor: "Floor"  # type: ignore[name-defined]
    ) -> ActionResult:
        from dungeoneer.core.event_bus import bus, DamageEvent, DeathEvent

        target = action.target
        result = calc_melee(actor, target)

        crit_str = " CRITICAL!" if result.is_crit else ""
        colour   = (255, 100, 100) if result.is_crit else (220, 120, 80)
        msg = f"{actor.name} hits {target.name} for {result.actual} dmg.{crit_str}"
        log.debug("melee  %s→%s  raw=%d actual=%d crit=%s", actor.name, target.name, result.raw, result.actual, result.is_crit)
        bus.post(DamageEvent(actor, target, result.actual, is_ranged=False, is_crit=result.is_crit))

        if not target.alive:
            bus.post(DeathEvent(target))
            msg += f" {target.name} is down!"
            floor.remove_dead()

        return ActionResult(True, msg, colour)

    def resolve_ranged(
        self, actor: "Actor", action: RangedAttackAction, floor: "Floor"  # type: ignore[name-defined]
    ) -> ActionResult:
        from dungeoneer.core.event_bus import bus, DamageEvent, DeathEvent
        from dungeoneer.entities.player import Player
        from dungeoneer.items.item import RangeType

        # Consume ammo from player's equipped weapon
        if isinstance(actor, Player):
            w = actor.equipped_weapon
            if w is None or w.range_type != RangeType.RANGED:
                return ActionResult(False, "No ranged weapon equipped.", (180, 80, 80))
            if w.ammo_current <= 0:
                return ActionResult(False, "Out of ammo! Press R to reload.", (255, 80, 80))
            w.ammo_current -= 1

        target = action.target
        result = calc_ranged(actor, target)

        crit_str = " CRITICAL!" if result.is_crit else ""
        colour   = (255, 200, 80) if result.is_crit else (220, 180, 60)
        msg = f"{actor.name} shoots {target.name} for {result.actual} dmg.{crit_str}"
        log.debug("ranged  %s→%s  raw=%d actual=%d crit=%s", actor.name, target.name, result.raw, result.actual, result.is_crit)
        bus.post(DamageEvent(actor, target, result.actual, is_ranged=True, is_crit=result.is_crit))

        if not target.alive:
            bus.post(DeathEvent(target))
            msg += f" {target.name} is down!"
            floor.remove_dead()

        return ActionResult(True, msg, colour)

    def resolve_open_container(
        self, actor: "Actor", action: "OpenContainerAction", floor: "Floor"  # type: ignore[name-defined]
    ) -> "ActionResult":
        from dungeoneer.entities.item_entity import ItemEntity
        from dungeoneer.entities.player import Player
        from dungeoneer.core.event_bus import bus, LogMessageEvent, ObjectiveEvent

        container = action.container
        container.opened = True
        log.info("Container opened at (%d,%d)  items=%s  credits=%d  objective=%s",
                 container.x, container.y, [i.name for i in container.items],
                 container.credits, container.is_objective)

        # Award credits if any
        credits_str = ""
        if container.credits > 0 and isinstance(actor, Player):
            actor.credits += container.credits
            credits_str = f"  +{container.credits} cr"

        # Mission objective — special handling
        if container.is_objective:
            bus.post(ObjectiveEvent(credits_gained=container.credits))
            return ActionResult(
                True,
                f"Data Core secured!{credits_str} — EXTRACTING.",
                (0, 240, 180),
            )

        # Normal container
        if not container.items:
            msg = f"The {container.name} is empty.{credits_str}"
            return ActionResult(True, msg.strip(), (120, 100, 80))

        for item in container.items:
            floor.add_item_entity(ItemEntity(container.x, container.y, item))
        names = ", ".join(i.name for i in container.items)
        return ActionResult(True, f"Opened {container.name}: {names}.{credits_str}", (200, 180, 80))
