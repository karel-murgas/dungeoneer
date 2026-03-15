"""Primary play scene — dungeon, input, turn loop."""
from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

import pygame

log = logging.getLogger(__name__)

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.event_bus import bus, DeathEvent, StairEvent, LogMessageEvent, ObjectiveEvent, DamageEvent
from dungeoneer.core.difficulty import Difficulty, NORMAL
from dungeoneer.world.dungeon_generator import DungeonGenerator
from dungeoneer.world.floor import Floor
from dungeoneer.world.fov import compute_fov
from dungeoneer.entities.player import Player
from dungeoneer.entities.enemy import Enemy, make_guard, make_drone
from dungeoneer.entities.item_entity import ItemEntity
from dungeoneer.entities.container_entity import ContainerEntity
from dungeoneer.combat.action_resolver import ActionResolver
from dungeoneer.combat.turn_manager import TurnManager
from dungeoneer.combat.action import (
    MoveAction, MeleeAttackAction, RangedAttackAction,
    WaitAction, ReloadAction, StairAction,
    EquipAction, UseItemAction, DropItemAction, OpenContainerAction,
)
from dungeoneer.items.item import RangeType
from dungeoneer.items.weapon import Weapon
from dungeoneer.items.consumable import Consumable
from dungeoneer.rendering.renderer import Renderer
from dungeoneer.rendering.floating_numbers import FloatingNumbers
from dungeoneer.rendering.ui.hud import HUD
from dungeoneer.rendering.ui.combat_log import CombatLog
from dungeoneer.rendering.ui.inventory_ui import InventoryUI
from dungeoneer.audio.audio_manager import AudioManager

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

FLOORS_PER_RUN = 3


class GameScene(Scene):
    def __init__(self, app: "GameApp", difficulty: Difficulty = NORMAL) -> None:
        super().__init__(app)
        self.difficulty     = difficulty
        self.resolver       = ActionResolver()
        self.turn_manager   = TurnManager()
        self.renderer       = Renderer()
        self.hud            = HUD()
        self.combat_log     = CombatLog()
        self.inventory_ui   = InventoryUI()
        self.audio          = AudioManager()
        self.floating_nums  = FloatingNumbers()
        self.player: Player | None = None
        self.floor:  Floor  | None = None
        self._game_over       = False
        self._subscribed      = False
        self._inventory_open  = False
        self._pending_advance = False   # waiting for enemy-turn delay
        self._advance_timer   = 0.0     # seconds remaining before advance fires

    def on_enter(self) -> None:
        log.info("GameScene.on_enter")
        self._subscribe_events()
        self.audio.attach()
        self._load_floor(depth=1)

    def on_exit(self) -> None:
        log.info("GameScene.on_exit  game_over=%s", self._game_over)
        self._unsubscribe_events()
        self.audio.detach()
        self.combat_log.close()

    # ------------------------------------------------------------------
    # Event subscriptions
    # ------------------------------------------------------------------

    def _subscribe_events(self) -> None:
        if not self._subscribed:
            bus.subscribe(DeathEvent,   self._on_death)
            bus.subscribe(StairEvent,   self._on_stair)
            bus.subscribe(ObjectiveEvent, self._on_objective)
            bus.subscribe(DamageEvent,  self._on_damage)
            self._subscribed = True

    def _unsubscribe_events(self) -> None:
        bus.unsubscribe(DeathEvent,   self._on_death)
        bus.unsubscribe(StairEvent,   self._on_stair)
        bus.unsubscribe(ObjectiveEvent, self._on_objective)
        bus.unsubscribe(DamageEvent,  self._on_damage)
        self._subscribed = False

    # ------------------------------------------------------------------
    # Floor loading
    # ------------------------------------------------------------------

    def _load_floor(self, depth: int, existing_player: Player | None = None) -> None:
        log.info("_load_floor  depth=%d  reusing_player=%s", depth, existing_player is not None)
        gen    = DungeonGenerator()
        result = gen.generate(
            settings.MAP_WIDTH, settings.MAP_HEIGHT,
            floor_depth=depth,
            guards=self.difficulty.guards_per_floor,
            drones=self.difficulty.drones_per_floor,
            containers=self.difficulty.containers_per_floor,
        )
        self.floor = Floor(result.dungeon_map, depth)

        player_spawn = next(s for s in result.spawns if s.kind == "player")
        if existing_player is None:
            self.player = Player(player_spawn.x, player_spawn.y, self.difficulty)
        else:
            existing_player.x = player_spawn.x
            existing_player.y = player_spawn.y
            self.player = existing_player

        self.player.floor_depth = depth
        self.floor.add_actor(self.player)

        for spawn in result.spawns:
            if spawn.kind == "guard":
                self.floor.add_actor(make_guard(spawn.x, spawn.y))
            elif spawn.kind == "drone":
                self.floor.add_actor(make_drone(spawn.x, spawn.y))
            elif spawn.kind == "container":
                self.floor.add_container(self._make_container(spawn.x, spawn.y))

        # On the final floor replace the exit stair with the mission objective
        if depth == FLOORS_PER_RUN:
            from dungeoneer.world.tile import TileType
            sx, sy = result.stair_pos
            self.floor.dungeon_map.set_type(sx, sy, TileType.FLOOR)
            obj_credits = self.difficulty.objective_credits
            self.floor.add_container(
                ContainerEntity(sx, sy, credits=obj_credits, is_objective=True, name="Corp Vault")
            )

        compute_fov(self.player.x, self.player.y, self.floor.dungeon_map)
        self.turn_manager.build_queue(self.floor)

        log.info(
            "Floor %d loaded  actors=%s  stair=%s",
            depth, [a.name for a in self.floor.actors], result.stair_pos,
        )
        self.combat_log.add(f"Floor {depth} — infiltrating facility.", (80, 200, 180))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_death(self, event: DeathEvent) -> None:
        log.info(
            "_on_death  entity=%s  is_player=%s  game_over=%s",
            event.entity.name, event.entity is self.player, self._game_over,
        )
        if event.entity is self.player:
            self._trigger_game_over(victory=False)
        elif isinstance(event.entity, Enemy):
            self._drop_loot(event.entity)

    def _drop_loot(self, enemy: Enemy) -> None:
        assert self.player is not None
        # Award credits from enemy
        if enemy.credits_drop > 0:
            self.player.credits += enemy.credits_drop
            bus.post(LogMessageEvent(f"+{enemy.credits_drop} cr.", (180, 220, 100)))
            log.info("Credits drop: %d from %s", enemy.credits_drop, enemy.name)
        # Drop item if any
        item = enemy.drop_loot()
        if item is not None:
            self.floor.add_item_entity(ItemEntity(enemy.x, enemy.y, item))
            log.info("Loot drop: %s at (%d,%d)", item.name, enemy.x, enemy.y)

    def _on_damage(self, event: DamageEvent) -> None:
        if self.floor is None:
            return
        t = event.target
        if self.floor.dungeon_map.visible[t.y, t.x]:
            self.floating_nums.add(t.x, t.y, event.amount, is_crit=event.is_crit)

    def _on_objective(self, event: ObjectiveEvent) -> None:
        self._trigger_game_over(victory=True)

    def _on_stair(self, event: StairEvent) -> None:
        assert self.player is not None
        next_depth = self.player.floor_depth + 1
        log.info("_on_stair  next_depth=%d  FLOORS_PER_RUN=%d", next_depth, FLOORS_PER_RUN)
        if next_depth > FLOORS_PER_RUN:
            self._trigger_game_over(victory=True)
        else:
            self._load_floor(next_depth, existing_player=self.player)
            self.turn_manager.build_queue(self.floor)

    def _trigger_game_over(self, *, victory: bool) -> None:
        log.info("_trigger_game_over  victory=%s  already=%s", victory, self._game_over)
        if self._game_over:
            return
        self._game_over = True
        from dungeoneer.scenes.game_over_scene import GameOverScene
        depth   = self.player.floor_depth if self.player else 1
        credits = self.player.credits if self.player else 0
        self.app.scenes.replace(GameOverScene(
            self.app, victory=victory, floor_depth=depth,
            difficulty=self.difficulty, credits_earned=credits,
        ))
        log.info("GameOverScene pushed  current_scene=%s", type(self.app.scenes.current).__name__)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._inventory_open:
                        self._inventory_open = False
                    else:
                        self.app.quit()
                    return
                if event.key == pygame.K_i:
                    self._inventory_open = not self._inventory_open
                    return

        if self._inventory_open:
            self._handle_inventory_input(events)
        else:
            self._handle_player_input(events)

    def _handle_inventory_input(self, events: List[pygame.event.Event]) -> None:
        assert self.player is not None
        assert self.floor  is not None

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            action = self.inventory_ui.handle_key(event.key, self.player)
            if action is None:
                continue

            if not action.validate(self.player, self.floor):
                continue

            result = action.execute(self.player, self.floor, self.resolver)
            if result.message:
                bus.post(LogMessageEvent(result.message, result.msg_colour))

            if result.success:
                # Equip/Use costs a turn; Drop is free
                if not isinstance(action, DropItemAction):
                    self._inventory_open = False
                    self._schedule_advance()
            break

    def _handle_player_input(self, events: List[pygame.event.Event]) -> None:
        is_pt = self.turn_manager.is_player_turn()
        if not is_pt or self._game_over or self._pending_advance:
            if not self._game_over:
                log.warning(
                    "_handle_player_input blocked  is_player_turn=%s  game_over=%s  "
                    "queue=[%s]  index=%d  player_alive=%s",
                    is_pt, self._game_over,
                    ", ".join(f"{a.name}(alive={a.alive})" for a in self.turn_manager._queue),
                    self.turn_manager._index,
                    self.player.alive if self.player else "N/A",
                )
            return

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            action = self._key_to_action(event.key)
            if action is None:
                continue

            log.debug(
                "Player action: %s  pos=(%d,%d)  hp=%d/%d",
                type(action).__name__, self.player.x, self.player.y,
                self.player.hp, self.player.max_hp,
            )

            if not action.validate(self.player, self.floor):
                if isinstance(action, StairAction):
                    bus.post(LogMessageEvent("No exit here.", (180, 80, 80)))
                elif isinstance(action, ReloadAction):
                    self.audio.play("no_ammo")
                continue

            result = action.execute(self.player, self.floor, self.resolver)
            if result.message:
                bus.post(LogMessageEvent(result.message, result.msg_colour))

            if not result.success:
                if isinstance(action, RangedAttackAction):
                    self.audio.play("no_ammo")
                continue

            if isinstance(action, ReloadAction):
                self.audio.play("reload")

            self._schedule_advance()
            break

    # ------------------------------------------------------------------
    # Turn-advance helpers
    # ------------------------------------------------------------------

    _COMBAT_DELAY = 0.14   # seconds to pause after player acts while enemies visible

    def _any_enemy_visible(self) -> bool:
        if self.floor is None:
            return False
        for actor in self.floor.actors:
            if isinstance(actor, Enemy) and actor.alive:
                if self.floor.dungeon_map.visible[actor.y, actor.x]:
                    return True
        return False

    def _schedule_advance(self) -> None:
        """Advance enemy turns — immediately if no enemy is visible, delayed otherwise."""
        if self._any_enemy_visible():
            self._pending_advance = True
            self._advance_timer   = self._COMBAT_DELAY
        else:
            self.turn_manager.advance(self.floor, self.resolver)

    def _key_to_action(self, key: int):
        assert self.player is not None
        assert self.floor  is not None

        MOVE_KEYS = {
            pygame.K_UP:    (0, -1), pygame.K_w: (0, -1),
            pygame.K_DOWN:  (0,  1), pygame.K_s: (0,  1),
            pygame.K_LEFT:  (-1, 0), pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1,  0), pygame.K_d: (1,  0),
        }
        if key in MOVE_KEYS:
            dx, dy = MOVE_KEYS[key]
            nx, ny = self.player.x + dx, self.player.y + dy
            target = self.floor.get_actor_at(nx, ny)
            if target and target is not self.player:
                return MeleeAttackAction(target)
            container = self.floor.get_container_at(nx, ny)
            if container:
                return OpenContainerAction(container)
            return MoveAction(dx, dy)

        if key in (pygame.K_PERIOD, pygame.K_KP5):
            return WaitAction()
        if key == pygame.K_r:
            return ReloadAction()
        if key in (pygame.K_GREATER, pygame.K_KP_ENTER, pygame.K_e):
            # E also opens adjacent containers (same key as stairs/interact)
            container = self._find_adjacent_container()
            if container:
                return OpenContainerAction(container)
            return StairAction()
        if key == pygame.K_f:
            return self._nearest_ranged_target()
        if key == pygame.K_h:
            return self._quick_heal()
        return None

    def _quick_heal(self):
        assert self.player is not None
        from dungeoneer.items.consumable import Consumable
        healables = [
            i for i in self.player.inventory
            if isinstance(i, Consumable) and i.heal_amount > 0
        ]
        if not healables:
            bus.post(LogMessageEvent("No healing items.", (180, 80, 80)))
            return None
        missing = self.player.max_hp - self.player.hp
        # Strongest that fits exactly; if all overheal, use the weakest to waste least
        exact = [i for i in healables if i.heal_amount <= missing]
        chosen = max(exact, key=lambda c: c.heal_amount) if exact \
            else min(healables, key=lambda c: c.heal_amount)
        return UseItemAction(chosen)

    def _find_adjacent_container(self):
        assert self.player is not None
        assert self.floor  is not None
        for c in self.floor.containers:
            if c.opened:
                continue
            if abs(self.player.x - c.x) <= 1 and abs(self.player.y - c.y) <= 1:
                return c
        return None

    @staticmethod
    def _make_container(x: int, y: int) -> ContainerEntity:
        import random
        from dungeoneer.items.consumable import make_stim_pack, make_medkit
        from dungeoneer.items.ammo import make_9mm_ammo, make_rifle_ammo
        from dungeoneer.items.weapon import make_rifle, make_shotgun

        pool = [
            (0.30, lambda: make_stim_pack()),
            (0.15, lambda: make_medkit()),
            (0.25, lambda: make_9mm_ammo(8)),
            (0.12, lambda: make_rifle_ammo(3)),
            (0.10, lambda: make_shotgun()),
            (0.08, lambda: make_rifle()),
        ]
        items = []
        count = random.randint(1, 2)
        for _ in range(count):
            roll = random.random()
            cumulative = 0.0
            for prob, factory in pool:
                cumulative += prob
                if roll < cumulative:
                    items.append(factory())
                    break
        credits = random.randint(5, 25)
        return ContainerEntity(x=x, y=y, items=items, credits=credits)

    def _nearest_ranged_target(self):
        assert self.player is not None
        assert self.floor  is not None

        w = self.player.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED:
            bus.post(LogMessageEvent("No ranged weapon equipped.", (180, 80, 80)))
            return WaitAction()

        visible_enemies = [
            a for a in self.floor.actors
            if isinstance(a, Enemy) and a.alive
            and self.floor.dungeon_map.visible[a.y, a.x]
        ]
        if not visible_enemies:
            bus.post(LogMessageEvent("No target in sight.", (180, 80, 80)))
            return WaitAction()

        nearest = min(
            visible_enemies,
            key=lambda e: abs(e.x - self.player.x) + abs(e.y - self.player.y),
        )
        return RangedAttackAction(nearest, max_range=w.range_tiles)

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self.floating_nums.update(dt)
        if self._pending_advance and not self._game_over:
            self._advance_timer -= dt
            if self._advance_timer <= 0.0:
                self._pending_advance = False
                self.turn_manager.advance(self.floor, self.resolver)

    def render(self, screen: pygame.Surface) -> None:
        if self.floor and self.player:
            self.renderer.draw(
                screen, self.floor, self.player,
                hud=self.hud,
                combat_log=self.combat_log,
            )
            self.floating_nums.draw(screen, self.renderer.camera)
            if self._inventory_open:
                self.inventory_ui.draw(screen, self.player)
