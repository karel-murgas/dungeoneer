"""ActionResolver — the only place where world state is mutated by actions."""
from __future__ import annotations

import logging

from dungeoneer.combat.action import ActionResult, MoveAction, MeleeAttackAction, RangedAttackAction
from dungeoneer.combat.damage import calc_melee, calc_ranged, calc_ranged_aimed, simulate_aim, simulate_aim_enemy
from dungeoneer.core.i18n import t

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

    def give_item(self, player: "Player", item: "Item") -> bool:  # type: ignore[name-defined]
        """Apply one item to the player using the same rules as floor auto-pickup.

        Returns True if the item was consumed/equipped (caller should remove the
        floor entity).  Returns False only when the inventory is full and the item
        could not be added — the caller is responsible for the "inv full" message
        so it can deduplicate across multiple items in one step.
        """
        from dungeoneer.core.event_bus import bus, LogMessageEvent
        from dungeoneer.items.ammo import AmmoPickup
        from dungeoneer.items.armor import Armor
        from dungeoneer.items.credits import CreditPickup
        from dungeoneer.items.weapon import Weapon
        from dungeoneer.items.item import RangeType
        # --- Credits → straight to player wallet ---
        if isinstance(item, CreditPickup):
            player.credits += item.amount
            log.info("Credits pickup: %d", item.amount)
            bus.post(LogMessageEvent(t("log.credits_drop").format(n=item.amount), (180, 220, 100)))
            return True
        # --- Ammo → straight to reserves ---
        if isinstance(item, AmmoPickup):
            player.ammo_reserves[item.ammo_type] = (
                player.ammo_reserves.get(item.ammo_type, 0) + item.ammo_count
            )
            log.info("Ammo pickup: %s", item.name)
            bus.post(LogMessageEvent(t("log.pickup_ammo").format(item=item.name), (200, 220, 100)))
            return True

        # --- Armor → auto-equip if slot empty, else discard ---
        if isinstance(item, Armor):
            if player.equipped_armor is not None:
                log.info("Discarded duplicate armor: %s", item.name)
                bus.post(LogMessageEvent(t("log.armor_duplicate").format(item=player.equipped_armor.name), (120, 100, 80)))
            else:
                player.equipped_armor = item
                log.info("Auto-equipped armor: %s", item.name)
                bus.post(LogMessageEvent(t("log.armor_equip").format(item=item.name, bonus=item.defense_bonus), (180, 220, 140)))
            return True

        # --- Weapon duplicates → strip ranged for ammo, discard melee ---
        if isinstance(item, Weapon):
            already_have = (
                (player.equipped_weapon is not None and player.equipped_weapon.id == item.id)
                or any(isinstance(i, Weapon) and i.id == item.id for i in player.inventory)
            )
            if already_have:
                if item.range_type == RangeType.RANGED and item.ammo_type:
                    gained = item.ammo_capacity
                    player.ammo_reserves[item.ammo_type] = (
                        player.ammo_reserves.get(item.ammo_type, 0) + gained
                    )
                    log.info("Stripped %s for %d ammo", item.name, gained)
                    bus.post(LogMessageEvent(t("log.ammo_strip").format(item=item.name, n=gained, ammo=item.ammo_type), (180, 200, 120)))
                else:
                    log.info("Discarded duplicate melee weapon: %s", item.name)
                    bus.post(LogMessageEvent(t("log.item_duplicate").format(item=item.name), (120, 100, 80)))
                return True

        # --- Default: add to inventory (Inventory.add handles consumable stacking) ---
        if player.inventory.add(item):
            log.info("Auto-pickup: %s", item.name)
            bus.post(LogMessageEvent(t("log.pickup_item").format(item=item.name, count=""), (240, 220, 80)))
            return True

        return False  # inventory full

    def _auto_pickup(self, player: "Player", floor: "Floor") -> None:  # type: ignore[name-defined]
        from dungeoneer.core.event_bus import bus, LogMessageEvent

        items_here = floor.get_items_at(player.x, player.y)
        if not items_here:
            return

        inventory_full_warned = False
        for item_e in list(items_here):  # snapshot — list mutates during loop
            consumed = self.give_item(player, item_e.item)
            if consumed:
                floor.remove_item_entity(item_e)
            elif not inventory_full_warned:
                inventory_full_warned = True
                bus.post(LogMessageEvent(t("log.inv_full"), (180, 80, 80)))

    def resolve_melee(
        self, actor: "Actor", action: MeleeAttackAction, floor: "Floor"  # type: ignore[name-defined]
    ) -> ActionResult:
        from dungeoneer.core.event_bus import bus, DamageEvent, DeathEvent

        target = action.target
        if action.power is not None:
            from dungeoneer.combat.damage import calc_melee_aimed
            result = calc_melee_aimed(actor, target, action.power)
        else:
            result = calc_melee(actor, target)

        crit_str = t("log.crit") if result.is_crit else ""
        colour   = (255, 100, 100) if result.is_crit else (220, 120, 80)
        msg = t("log.melee_hit").format(attacker=actor.name, target=target.name, dmg=result.actual, crit=crit_str)
        log.debug("melee  %s→%s  raw=%d actual=%d crit=%s", actor.name, target.name, result.raw, result.actual, result.is_crit)
        bus.post(DamageEvent(actor, target, result.actual, is_ranged=False, is_crit=result.is_crit))

        if target.alive:
            brain = getattr(target, "ai_brain", None)
            if brain is not None:
                brain.alert(actor.x, actor.y)

        if not target.alive:
            bus.post(DeathEvent(target))
            msg += t("log.is_down").format(name=target.name)
            floor.remove_dead()

        return ActionResult(True, msg, colour)

    def resolve_ranged(
        self, actor: "Actor", action: RangedAttackAction, floor: "Floor"  # type: ignore[name-defined]
    ) -> ActionResult:
        from dungeoneer.core.event_bus import bus, DamageEvent, DeathEvent, MissEvent
        from dungeoneer.entities.player import Player
        from dungeoneer.items.item import RangeType

        # Validate weapon before entering burst loop
        if isinstance(actor, Player):
            w = actor.equipped_weapon
            if w is None or w.range_type != RangeType.RANGED:
                return ActionResult(False, t("log.no_ranged"), (180, 80, 80))
            if w.ammo_current <= 0:
                return ActionResult(False, t("log.no_ammo"), (255, 80, 80))

        target = action.target
        weapon = getattr(actor, "equipped_weapon", None)
        shots = getattr(weapon, "shots", 1) if weapon else 1

        # Resolve accuracy values for this attack:
        #   - action.accuracy_values set  → use them (from AimScene or simulate_aim in GameScene)
        #   - None + enemy                → simulate statistically
        #   - None + player               → legacy random roll (fallback only)
        accuracy_values = action.accuracy_values
        if accuracy_values is None and not isinstance(actor, Player):
            dist      = abs(actor.x - target.x) + abs(actor.y - target.y)
            aim_skill = getattr(actor, "aim_skill", 2.5)
            accuracy_values = [simulate_aim_enemy(dist, aim_skill) for _ in range(shots)]

        # For player burst weapons (shots > 1), DamageEvents are collected and returned
        # so GameScene can post them with staggered delays for visual/audio effect.
        # For single-shot and enemy actions, post immediately as usual.
        is_player_burst = isinstance(actor, Player) and shots > 1

        total_actual = 0
        any_crit = False
        burst_events = []
        shots_fired = 0

        for i in range(shots):
            if not target.alive:
                break
            # Consume ammo for each shot (even misses — the shot was fired)
            if isinstance(actor, Player):
                w = actor.equipped_weapon
                if w is None or w.range_type != RangeType.RANGED:
                    break
                if w.ammo_current <= 0:
                    break
                w.ammo_current -= 1
            shots_fired += 1

            if accuracy_values is not None:
                acc = accuracy_values[i] if i < len(accuracy_values) else -1.0
                result = calc_ranged_aimed(actor, target, acc)
            else:
                result = calc_ranged(actor, target)

            if result.actual > 0:
                total_actual += result.actual
                if result.is_crit:
                    any_crit = True
                log.debug("ranged  %s→%s  raw=%d actual=%d crit=%s", actor.name, target.name, result.raw, result.actual, result.is_crit)
                dmg_event = DamageEvent(actor, target, result.actual, is_ranged=True, is_crit=result.is_crit)
                if is_player_burst:
                    burst_events.append(dmg_event)
                else:
                    bus.post(dmg_event)
            else:
                log.debug("ranged  %s→%s  MISS (acc=%.2f)", actor.name, target.name, accuracy_values[i] if accuracy_values else -1)
                bus.post(MissEvent(actor, target))

        if shots_fired == 0:
            return ActionResult(False, t("log.no_ammo"), (255, 80, 80))

        # Mark target so drone AI knows to return fire rather than flee.
        if isinstance(actor, Player):
            target.was_shot_at = True

        if total_actual == 0:
            # All shots fired but all missed
            msg = t("log.ranged_miss").format(attacker=actor.name, target=target.name)
            return ActionResult(True, msg, (140, 140, 140))

        hit_count = len(burst_events) if is_player_burst else (1 if total_actual > 0 else 0)
        crit_str  = t("log.crit") if any_crit else ""
        colour    = (255, 200, 80) if any_crit else (220, 180, 60)
        burst_str = f" ({hit_count}×)" if hit_count > 1 else ""
        msg = t("log.ranged_hit").format(attacker=actor.name, target=target.name, burst=burst_str, dmg=total_actual, crit=crit_str)

        if target.alive:
            brain = getattr(target, "ai_brain", None)
            if brain is not None:
                brain.alert(actor.x, actor.y)

        if not target.alive:
            bus.post(DeathEvent(target))
            msg += t("log.is_down").format(name=target.name)
            floor.remove_dead()

        return ActionResult(True, msg, colour, burst_events=burst_events)

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
            credits_str = f"  +¥{container.credits}"

        # Mission objective — special handling
        if container.is_objective:
            bus.post(ObjectiveEvent(credits_gained=container.credits))
            return ActionResult(
                True,
                t("log.container_secured").format(credits=credits_str),
                (0, 240, 180),
            )

        # Normal container
        if not container.items:
            return ActionResult(True, t("log.container_empty").format(name=container.name, credits=credits_str), (120, 100, 80))

        for item in container.items:
            floor.add_item_entity(ItemEntity(container.x, container.y, item))
        names = ", ".join(i.name for i in container.items)
        return ActionResult(True, t("log.container_open").format(name=container.name, items=names, credits=credits_str), (200, 180, 80))
