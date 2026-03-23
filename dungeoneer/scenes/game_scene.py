"""Primary play scene — dungeon, input, turn loop."""
from __future__ import annotations

import logging
from typing import List, TYPE_CHECKING

import pygame

log = logging.getLogger(__name__)

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.event_bus import bus, DeathEvent, StairEvent, ElevatorEvent, LogMessageEvent, ObjectiveEvent, DamageEvent, MissEvent
from dungeoneer.core.difficulty import Difficulty, NORMAL
from dungeoneer.core.i18n import t
from dungeoneer.world.dungeon_generator import DungeonGenerator
from dungeoneer.world.floor import Floor
from dungeoneer.world.tile import TileType
from dungeoneer.world.fov import compute_fov
from dungeoneer.entities.player import Player
from dungeoneer.entities.enemy import Enemy, make_guard, make_drone
from dungeoneer.entities.item_entity import ItemEntity
from dungeoneer.entities.container_entity import ContainerEntity
from dungeoneer.combat.action_resolver import ActionResolver
from dungeoneer.combat.turn_manager import TurnManager
from dungeoneer.combat.action import (
    MoveAction, MeleeAttackAction, RangedAttackAction,
    WaitAction, ReloadAction, StairAction, ElevatorAction,
    EquipAction, UseItemAction, OpenContainerAction,
)
from dungeoneer.items.item import RangeType
from dungeoneer.items.weapon import Weapon
from dungeoneer.items.consumable import Consumable
from dungeoneer.rendering.renderer import Renderer
from dungeoneer.rendering.floating_numbers import FloatingNumbers
from dungeoneer.rendering.ui.hud import HUD
from dungeoneer.rendering.ui.combat_log import CombatLog
from dungeoneer.rendering.ui.inventory_ui import InventoryUI
from dungeoneer.rendering.ui.weapon_picker import WeaponPickerUI
from dungeoneer.rendering.ui.help_screen import HelpScreen
from dungeoneer.rendering.ui.alert_banner import AlertBanner
from dungeoneer.rendering.ui.quit_confirm import QuitConfirmDialog
from dungeoneer.rendering.ui.cheat_menu import CheatMenuOverlay
from dungeoneer.rendering.ui.tutorial_overlay import TutorialManager, TutorialOverlay
from dungeoneer.rendering.ui.minimap_overlay import MinimapOverlay
from dungeoneer.audio.audio_manager import AudioManager
from dungeoneer.audio.music_manager import MusicManager

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp

FLOORS_PER_RUN = 3


class GameScene(Scene):
    def __init__(
        self,
        app: "GameApp",
        difficulty: Difficulty = NORMAL,
        use_minigame: bool = True,
        use_aim_minigame: bool = True,
        use_heal_minigame: bool = True,
        use_melee_minigame: bool = True,
        heal_threshold_pct: int = 100,
        use_tutorial: bool = False,
        map_size: str = "large",
    ) -> None:
        super().__init__(app)
        self.difficulty          = difficulty
        self.use_minigame        = use_minigame
        self.use_aim_minigame    = use_aim_minigame
        self.use_heal_minigame   = use_heal_minigame
        self.use_melee_minigame  = use_melee_minigame
        self.heal_threshold_pct  = heal_threshold_pct
        self.map_size            = map_size
        self.resolver       = ActionResolver()
        self.turn_manager   = TurnManager()
        self.renderer       = Renderer()
        self.hud            = HUD(heal_threshold_pct=heal_threshold_pct)
        self.combat_log     = CombatLog()
        self.inventory_ui   = InventoryUI()
        self.weapon_picker  = WeaponPickerUI()
        self.help_screen    = HelpScreen()
        self.quit_confirm     = QuitConfirmDialog()
        self.overheal_confirm = QuitConfirmDialog(key_prefix="overheal_confirm")
        self.cheat_menu       = CheatMenuOverlay()
        self.tutorial_manager = TutorialManager(enabled=use_tutorial)
        self.tutorial_overlay = TutorialOverlay()
        self.minimap          = MinimapOverlay()
        self.alert_banner   = AlertBanner()
        self.audio          = AudioManager()
        self.music          = MusicManager()
        self.floating_nums  = FloatingNumbers()
        self.player: Player | None = None
        self.floor:  Floor  | None = None
        self._game_over          = False
        self._subscribed         = False
        self._inventory_open     = False
        self._weapon_picker_open = False
        self._help_open          = False
        self._quit_confirm_open     = False
        self._overheal_confirm_open = False
        self._overheal_pending: "Consumable | None" = None
        self._cheat_menu_open    = False
        self._minimap_open       = False
        self._tutorial_open      = False                # tutorial overlay active
        self._tutorial_queue:    list[str] = []        # steps waiting to be shown
        self._heal_overlay       = None                 # HealOverlay instance when healing
        self._had_visible_enemies = False  # for alert-banner trigger detection
        self._pending_advance    = False   # waiting for enemy-turn delay
        self._advance_timer      = 0.0     # seconds remaining before advance fires
        self._burst_queue: list  = []      # [(time_remaining, DamageEvent), ...]
        self._hack_just_completed = False  # advance enemy turns once hack scene pops
        self._held_move_key: int | None = None   # key currently held for auto-repeat
        self._move_hold_timer: float    = 0.0    # seconds until next auto-repeat step
        self._aim_target: Enemy | None = None   # currently highlighted ranged target
        self._aim_overlay = None                # AimOverlay instance when aiming
        self._melee_overlay = None              # MeleeOverlay instance when charging melee
        # Elevator animation state machine: None | "opening" | "entering" | "closing" | "descending"
        self._elevator_phase: str | None = None
        self._elevator_timer: float = 0.0
        self._elevator_pos: tuple[int, int] | None = None  # (x, y) of elevator tile
        self._hint_font   = pygame.font.SysFont("consolas", 14, bold=True)

    def on_enter(self) -> None:
        log.info("GameScene.on_enter")
        self._subscribe_events()
        self.audio.attach()
        self._load_floor(depth=1)
        self.music.start()
        self._maybe_show_tutorial("movement")

    def on_exit(self) -> None:
        log.info("GameScene.on_exit  game_over=%s", self._game_over)
        self._unsubscribe_events()
        self.audio.detach()
        self.music.stop()
        self.combat_log.close()

    def on_resume(self) -> None:
        """Called when a scene pushed on top of this one (e.g. HackScene) pops."""
        self.music.resume()
        # Keep _aim_target if enemy is still alive and visible
        tgt = self._aim_target
        if tgt is not None and (
            not tgt.alive
            or self.floor is None
            or not self.floor.dungeon_map.visible[tgt.y, tgt.x]
        ):
            self._aim_target = None
        self._aim_overlay = None  # discard any stale overlay

        if self._hack_just_completed and not self._game_over:
            self._hack_just_completed = False
            # Recompute FOV so a freshly spawned drone's visibility is up-to-date,
            # then trigger the alert banner immediately (before the player can act).
            if self.player and self.floor:
                compute_fov(self.player.x, self.player.y, self.floor.dungeon_map)
                now_visible = self._any_enemy_visible()
                if now_visible and not self._had_visible_enemies:
                    self.alert_banner.trigger()
                    self.music.to_action(fast=True)
                    self._maybe_show_tutorial("enemy")
                self._had_visible_enemies = now_visible
            self._schedule_advance()

    # ------------------------------------------------------------------
    # Event subscriptions
    # ------------------------------------------------------------------

    def _subscribe_events(self) -> None:
        if not self._subscribed:
            bus.subscribe(DeathEvent,     self._on_death)
            bus.subscribe(StairEvent,     self._on_stair)
            bus.subscribe(ElevatorEvent,  self._on_elevator)
            bus.subscribe(ObjectiveEvent, self._on_objective)
            bus.subscribe(DamageEvent,    self._on_damage)
            bus.subscribe(MissEvent,      self._on_miss)
            self._subscribed = True

    def _unsubscribe_events(self) -> None:
        bus.unsubscribe(DeathEvent,     self._on_death)
        bus.unsubscribe(StairEvent,     self._on_stair)
        bus.unsubscribe(ElevatorEvent,  self._on_elevator)
        bus.unsubscribe(ObjectiveEvent, self._on_objective)
        bus.unsubscribe(DamageEvent,  self._on_damage)
        bus.unsubscribe(MissEvent,    self._on_miss)
        self._subscribed = False

    # ------------------------------------------------------------------
    # Floor loading
    # ------------------------------------------------------------------

    def _load_floor(self, depth: int, existing_player: Player | None = None) -> None:
        log.info("_load_floor  depth=%d  reusing_player=%s", depth, existing_player is not None)
        if self.map_size == "small":
            mw, mh = settings.MAP_WIDTH_SMALL, settings.MAP_HEIGHT_SMALL
        else:
            mw, mh = settings.MAP_WIDTH, settings.MAP_HEIGHT
        gen    = DungeonGenerator()
        result = gen.generate(
            mw, mh,
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

        # On the final floor replace the elevator with the mission objective.
        # The vault is placed on the walkable floor tile adjacent to the elevator.
        if depth == FLOORS_PER_RUN:
            ex, ey = result.stair_pos  # elevator position
            self.floor.dungeon_map.set_type(ex, ey, TileType.WALL)  # revert to wall
            # Find the adjacent floor tile (the one side the elevator was accessible from)
            vault_x, vault_y = ex, ey
            for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                if self.floor.dungeon_map.is_walkable(ex + dx, ey + dy):
                    vault_x, vault_y = ex + dx, ey + dy
                    break
            obj_credits = self.difficulty.objective_credits
            self.floor.add_container(
                ContainerEntity(vault_x, vault_y, credits=obj_credits, is_objective=True, name=t("entity.corp_vault.name"))
            )

        compute_fov(self.player.x, self.player.y, self.floor.dungeon_map)
        self.turn_manager.build_queue(self.floor)
        self._had_visible_enemies = False

        log.info(
            "Floor %d loaded  actors=%s  stair=%s",
            depth, [a.name for a in self.floor.actors], result.stair_pos,
        )
        self.combat_log.add(t("log.floor_enter").format(n=depth), (80, 200, 180))

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
        # Drop credits on floor (chance-based)
        enemy.roll_credits()
        if enemy.credits_drop > 0:
            from dungeoneer.items.credits import make_credits
            credit_item = make_credits(enemy.credits_drop)
            self.floor.add_item_entity(ItemEntity(enemy.x, enemy.y, credit_item))
            log.info("Credits drop: %d from %s", enemy.credits_drop, enemy.name)
        # Drop item if any
        item = enemy.drop_loot()
        if item is not None:
            self.floor.add_item_entity(ItemEntity(enemy.x, enemy.y, item))
            log.info("Loot drop: %s at (%d,%d)", item.name, enemy.x, enemy.y)

    def _on_damage(self, event: DamageEvent) -> None:
        if self.floor is None:
            return
        tgt = event.target
        if self.floor.dungeon_map.visible[tgt.y, tgt.x]:
            self.floating_nums.add(tgt.x, tgt.y, event.amount, is_crit=event.is_crit)

    def _on_miss(self, event: MissEvent) -> None:
        if self.floor is None:
            return
        tgt = event.target
        if self.floor.dungeon_map.visible[tgt.y, tgt.x]:
            self.floating_nums.add_miss(tgt.x, tgt.y)

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
            self.music.to_calm()

    def _on_elevator(self, event: ElevatorEvent) -> None:
        """Start elevator animation: open → enter → close → descend."""
        self._elevator_pos = (event.elevator_x, event.elevator_y)
        self._elevator_phase = "opening"
        self._elevator_timer = 0.35  # time to show doors opening
        # Open the elevator doors
        self.floor.dungeon_map.set_type(event.elevator_x, event.elevator_y, TileType.ELEVATOR_OPEN)
        self.audio.play("elevator_open", 0.5)
        log.info("Elevator animation started at (%d,%d)", event.elevator_x, event.elevator_y)

    def _elevator_descend(self) -> None:
        """Complete the elevator sequence — load next floor or trigger victory."""
        assert self.player is not None
        next_depth = self.player.floor_depth + 1
        log.info("_elevator_descend  next_depth=%d  FLOORS_PER_RUN=%d", next_depth, FLOORS_PER_RUN)
        if next_depth > FLOORS_PER_RUN:
            self._trigger_game_over(victory=True)
        else:
            self._load_floor(next_depth, existing_player=self.player)
            self.turn_manager.build_queue(self.floor)
            self.music.to_calm()

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
            difficulty=self.difficulty, use_minigame=self.use_minigame,
            use_aim_minigame=self.use_aim_minigame,
            use_melee_minigame=self.use_melee_minigame,
            credits_earned=credits, audio=self.audio,
            map_size=self.map_size,
        ))
        log.info("GameOverScene pushed  current_scene=%s", type(self.app.scenes.current).__name__)

    def _go_to_menu(self) -> None:
        from dungeoneer.scenes.main_menu_scene import MainMenuScene
        from dungeoneer.core.i18n import get_language
        self.app.scenes.replace(
            MainMenuScene(
                self.app,
                difficulty=self.difficulty,
                use_minigame=self.use_minigame,
                use_aim_minigame=self.use_aim_minigame,
                use_melee_minigame=self.use_melee_minigame,
                use_tutorial=self.tutorial_manager.enabled,
                map_size=self.map_size,
                language=get_language(),
            )
        )

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    _HOLD_MOVE_KEYS = frozenset({
        pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
        pygame.K_w, pygame.K_s, pygame.K_a, pygame.K_d,
    })

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        # Track held movement keys for auto-repeat (KEYUP always clears, regardless of overlays)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in self._HOLD_MOVE_KEYS:
                if not self._cheat_menu_open:
                    self._held_move_key   = event.key
                    self._move_hold_timer = self._MOVE_HOLD_INITIAL
            elif event.type == pygame.KEYUP and event.key == self._held_move_key:
                self._held_move_key = None

        # Aim overlay takes exclusive input while active
        if self._aim_overlay is not None:
            for event in events:
                self._aim_overlay.handle_event(event)
            return

        # Heal overlay takes exclusive input while active
        if self._heal_overlay is not None:
            for event in events:
                self._heal_overlay.handle_event(event)
            return

        # Melee overlay takes exclusive input while active
        if self._melee_overlay is not None:
            for event in events:
                self._melee_overlay.handle_event(event)
            return

        # Tutorial overlay takes exclusive input while active
        if self._tutorial_open:
            for event in events:
                self.tutorial_overlay.handle_event(event)
            return

        for event in events:
            if self._cheat_menu_open:
                if event.type == pygame.MOUSEMOTION:
                    self.cheat_menu.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    action = self.cheat_menu.handle_mouse_button(event)
                    if action:
                        if action == "close":
                            self._cheat_menu_open = False
                        else:
                            self._apply_cheat(action)
                elif event.type == pygame.KEYDOWN:
                    action = self.cheat_menu.handle_key(event.key)
                    if action:
                        if action == "close":
                            self._cheat_menu_open = False
                        else:
                            self._apply_cheat(action)
                continue  # absorb all input while cheat menu is open

            if self._quit_confirm_open:
                if event.type == pygame.MOUSEMOTION:
                    self.quit_confirm.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    result = self.quit_confirm.handle_mouse_button(event)
                    if result == "confirm":
                        self._go_to_menu()
                        return
                    elif result == "cancel":
                        self._quit_confirm_open = False
                elif event.type == pygame.KEYDOWN:
                    result = self.quit_confirm.handle_key(event.key)
                    if result == "confirm":
                        self._go_to_menu()
                        return
                    elif result == "cancel":
                        self._quit_confirm_open = False
                continue  # absorb all input while quit dialog is open

            if self._overheal_confirm_open:
                if event.type == pygame.MOUSEMOTION:
                    self.overheal_confirm.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    result = self.overheal_confirm.handle_mouse_button(event)
                    if result == "confirm":
                        self._overheal_confirm_open = False
                        self._do_launch_heal(self._overheal_pending)
                        self._overheal_pending = None
                    elif result == "cancel":
                        self._overheal_confirm_open = False
                        self._overheal_pending = None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_h:
                        result = "confirm"
                    else:
                        result = self.overheal_confirm.handle_key(event.key)
                    if result == "confirm":
                        self._overheal_confirm_open = False
                        self._do_launch_heal(self._overheal_pending)
                        self._overheal_pending = None
                    elif result == "cancel":
                        self._overheal_confirm_open = False
                        self._overheal_pending = None
                continue  # absorb all input while overheal dialog is open

            if self._minimap_open:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_m, pygame.K_ESCAPE):
                        self._minimap_open = False
                continue

            if self._help_open:
                if event.type == pygame.MOUSEMOTION:
                    self.help_screen.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.help_screen.handle_mouse_button(event):
                        self._help_open = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1 or self.help_screen.handle_key(event.key):
                        self._help_open = False
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:
                    self._help_open = True
                    return
                if event.key == pygame.K_F11:
                    self._cheat_menu_open = not self._cheat_menu_open
                    return
                if event.key == pygame.K_m:
                    self._minimap_open = True
                    return
                if event.key == pygame.K_ESCAPE:
                    if self._inventory_open:
                        self._inventory_open = False
                    elif self._weapon_picker_open:
                        self._weapon_picker_open = False
                    else:
                        self._quit_confirm_open = True
                    return
                if event.key == pygame.K_TAB:
                    self._cycle_aim_target()
                    return
                if event.key == pygame.K_i:
                    self._inventory_open = not self._inventory_open
                    self._weapon_picker_open = False
                    return
                if event.key == pygame.K_c:
                    if self._weapon_picker_open:
                        self._weapon_picker_open = False
                    else:
                        self._weapon_picker_open = True
                        self._inventory_open = False
                        self.weapon_picker.open(self.player)
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                wp_r = self.hud.weapon_rect if self.hud else None
                hl_r = self.hud.heal_rect   if self.hud else None
                if wp_r and wp_r.collidepoint(event.pos):
                    if self._weapon_picker_open:
                        self._weapon_picker_open = False
                    else:
                        self._weapon_picker_open = True
                        self._inventory_open = False
                        self.weapon_picker.open(self.player)
                    return
                if hl_r and hl_r.collidepoint(event.pos):
                    self._launch_heal()
                    return

        if (self._quit_confirm_open or self._overheal_confirm_open or self._cheat_menu_open
                or self._minimap_open or self._heal_overlay is not None
                or self._melee_overlay is not None):
            return

        if self._inventory_open:
            self._handle_inventory_input(events)
        elif self._weapon_picker_open:
            self._handle_weapon_picker_input(events)
        else:
            self._handle_player_input(events)

    def _handle_inventory_input(self, events: List[pygame.event.Event]) -> None:
        assert self.player is not None
        assert self.floor  is not None

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.inventory_ui.handle_mouse_motion(event.pos)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                action = self.inventory_ui.handle_mouse_button(event, self.player)
            elif event.type == pygame.KEYDOWN:
                action = self.inventory_ui.handle_key(event.key, self.player)
            else:
                continue

            if action == "close":
                self._inventory_open = False
                return
            if action is None:
                continue

            if not action.validate(self.player, self.floor):
                continue

            result = action.execute(self.player, self.floor, self.resolver)
            if result.message:
                bus.post(LogMessageEvent(result.message, result.msg_colour))

            if result.success:
                if isinstance(action, UseItemAction):
                    self.audio.play("heal")
                self._inventory_open = False
                self._schedule_advance()
            break

    def _handle_weapon_picker_input(self, events: List[pygame.event.Event]) -> None:
        assert self.player is not None
        assert self.floor  is not None

        for event in events:
            if event.type == pygame.MOUSEMOTION:
                self.weapon_picker.handle_mouse_motion(event.pos)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                result = self.weapon_picker.handle_mouse_button(event, self.player)
            elif event.type == pygame.KEYDOWN:
                result = self.weapon_picker.handle_key(event.key, self.player)
            else:
                continue

            if result == "close":
                self._weapon_picker_open = False
                return
            if result is None:
                continue

            action = result
            if not action.validate(self.player, self.floor):
                continue

            outcome = action.execute(self.player, self.floor, self.resolver)
            if outcome.message:
                bus.post(LogMessageEvent(outcome.message, outcome.msg_colour))

            if outcome.success:
                self._weapon_picker_open = False
                # Tutorial: show melee tutorial when player equips a melee weapon
                if isinstance(action, EquipAction):
                    w = self.player.equipped_weapon
                    if w and w.range_type == RangeType.MELEE:
                        self._maybe_show_tutorial("melee")
                self._schedule_advance()
            break

    def _handle_player_input(self, events: List[pygame.event.Event]) -> None:
        if self.alert_banner.is_blocking:
            return
        if self._elevator_phase is not None:
            return  # block all input during elevator animation
        self._check_tutorial_triggers()
        if self._tutorial_open:
            return
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
            # LMB on a visible enemy or adjacent container
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                enemy = self._enemy_at_screen_pos(*event.pos)
                if enemy is not None:
                    w = self.player.equipped_weapon
                    if w and w.range_type == RangeType.RANGED:
                        self._aim_target = enemy
                        self._launch_aim(enemy)
                        break
                    else:
                        reach = w.range_tiles if w else 1
                        diag  = w.diagonal    if w else False
                        action = MeleeAttackAction(enemy, range_tiles=reach, diagonal=diag)
                        if action.validate(self.player, self.floor):
                            if self.use_melee_minigame:
                                self._launch_melee(enemy)
                                break
                            result = action.execute(self.player, self.floor, self.resolver)
                            if result.message:
                                bus.post(LogMessageEvent(result.message, result.msg_colour))
                            if result.success:
                                self._schedule_advance()
                            break
                container = self._container_at_screen_pos(*event.pos)
                if container is not None:
                    action = OpenContainerAction(container)
                    if action.validate(self.player, self.floor):
                        if not container.is_objective and self.use_minigame:
                            self._launch_hack(container)
                        else:
                            result = action.execute(self.player, self.floor, self.resolver)
                            if result.message:
                                bus.post(LogMessageEvent(result.message, result.msg_colour))
                            if result.success:
                                self._schedule_advance()
                    else:
                        bus.post(LogMessageEvent(t("log.container_already_open"), (120, 100, 80)))
                        self.audio.play("action_denied")
                    break
                continue

            if event.type != pygame.KEYDOWN:
                continue

            key = event.key

            if key == pygame.K_h:
                self._launch_heal()
                continue   # no immediate turn advance
            else:
                action = self._key_to_action(key)
                if action is None:
                    continue

            log.debug(
                "Player action: %s  pos=(%d,%d)  hp=%d/%d",
                type(action).__name__, self.player.x, self.player.y,
                self.player.hp, self.player.max_hp,
            )

            if not action.validate(self.player, self.floor):
                if isinstance(action, (StairAction, ElevatorAction)):
                    bus.post(LogMessageEvent(t("log.no_exit"), (180, 80, 80)))
                    self.audio.play("action_denied")
                elif isinstance(action, OpenContainerAction):
                    bus.post(LogMessageEvent(t("log.container_already_open"), (120, 100, 80)))
                    self.audio.play("action_denied")
                elif isinstance(action, ReloadAction):
                    w = self.player.equipped_weapon
                    if w is None or w.range_type != RangeType.RANGED:
                        bus.post(LogMessageEvent(t("log.no_ranged"), (180, 80, 80)))
                    elif w.ammo_current >= w.ammo_capacity:
                        bus.post(LogMessageEvent(t("log.reload_full"), (120, 140, 100)))
                    else:
                        bus.post(LogMessageEvent(t("log.reload_no_reserves"), (180, 80, 80)))
                    self.audio.play("no_ammo")
                continue

            # Non-objective containers trigger the hack minigame (when enabled).
            if (
                isinstance(action, OpenContainerAction)
                and not action.container.is_objective
                and self.use_minigame
            ):
                self._launch_hack(action.container)
                break

            # Ranged attack → intercept for aim minigame
            if isinstance(action, RangedAttackAction):
                if self.use_aim_minigame:
                    self._launch_aim(action.target)
                    break
                else:
                    # Minigame OFF: simulate using player's aim_skill from difficulty
                    from dungeoneer.combat.damage import simulate_aim_enemy
                    w = self.player.equipped_weapon
                    dist = abs(self.player.x - action.target.x) + abs(self.player.y - action.target.y)
                    shots = getattr(w, "shots", 1) if w else 1
                    action.accuracy_values = [simulate_aim_enemy(dist, self.player.aim_skill) for _ in range(shots)]

            # Melee attack → intercept for power-charge minigame
            if isinstance(action, MeleeAttackAction):
                if self.use_melee_minigame:
                    self._launch_melee(action.target)
                    break
                # else: fall through to normal random-roll execution

            result = action.execute(self.player, self.floor, self.resolver)
            if result.message:
                bus.post(LogMessageEvent(result.message, result.msg_colour))

            if not result.success:
                if isinstance(action, RangedAttackAction):
                    self.audio.play("no_ammo")
                continue

            if isinstance(action, ReloadAction):
                self.audio.play("reload")
            elif isinstance(action, UseItemAction):
                self.audio.play("heal")

            # Schedule staggered burst effects (e.g. SMG 3-round burst)
            burst = result.burst_events
            if burst:
                bus.post(burst[0])  # first shot fires immediately
                for i, ev in enumerate(burst[1:], start=1):
                    self._burst_queue.append((i * self._BURST_INTERVAL, ev))
                self._schedule_advance(extra_delay=(len(burst) - 1) * self._BURST_INTERVAL)
            else:
                self._schedule_advance()

            # Alert banner: trigger when first enemy becomes visible this encounter.
            # fast=True so the action track is audible within the banner animation.
            now_visible = self._any_enemy_visible()
            if now_visible and not self._had_visible_enemies:
                self.alert_banner.trigger()
                self.music.to_action(fast=True)
                self._maybe_show_tutorial("enemy")
            self._had_visible_enemies = now_visible
            break

    # ------------------------------------------------------------------
    # Turn-advance helpers
    # ------------------------------------------------------------------

    _COMBAT_DELAY      = 0.14   # seconds to pause after player acts while enemies visible
    _BURST_INTERVAL    = 0.09   # seconds between burst shots (visual/audio only)
    _MOVE_HOLD_INITIAL = 0.25   # initial hold delay before auto-repeat begins
    _MOVE_HOLD_REPEAT  = 0.10   # interval between repeated steps (~10 steps/sec)

    def _any_enemy_visible(self) -> bool:
        if self.floor is None:
            return False
        for actor in self.floor.actors:
            if isinstance(actor, Enemy) and actor.alive:
                if self.floor.dungeon_map.visible[actor.y, actor.x]:
                    return True
        return False

    def _schedule_advance(self, extra_delay: float = 0.0) -> None:
        """Advance enemy turns — immediately if no enemy is visible, delayed otherwise."""
        if self._any_enemy_visible():
            self._pending_advance = True
            self._advance_timer   = self._COMBAT_DELAY + extra_delay
        else:
            self.turn_manager.advance(self.floor, self.resolver)
            self._update_music_state()

    def _is_any_enemy_alert(self) -> bool:
        """True if any living enemy is actively hunting the player (CombatState / SearchState)."""
        from dungeoneer.ai.states import CombatState, SearchState
        if self.floor is None:
            return False
        for actor in self.floor.actors:
            if isinstance(actor, Enemy) and actor.alive:
                state = getattr(actor.ai_brain, "current_state", None)
                if isinstance(state, (CombatState, SearchState)):
                    return True
        return False

    def _update_music_state(self) -> None:
        """Switch music to action or calm.

        Action continues as long as EITHER:
          - any enemy is visible to the player, OR
          - any enemy knows about the player (CombatState / SearchState).
        """
        if self._is_any_enemy_alert() or self._any_enemy_visible():
            self.music.to_action()
        else:
            self.music.to_calm()

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
                bus.post(LogMessageEvent(t("log.tile_occupied"), (180, 120, 80)))
                return None
            container = self.floor.get_container_at(nx, ny)
            if container:
                return OpenContainerAction(container)
            return MoveAction(dx, dy)

        if key in (pygame.K_PERIOD, pygame.K_KP5, pygame.K_SPACE):
            return WaitAction()
        if key == pygame.K_r:
            return ReloadAction()
        if key in (pygame.K_GREATER, pygame.K_KP_ENTER, pygame.K_e):
            # E also opens adjacent containers (same key as elevator/interact)
            container = self._find_adjacent_container()
            if container:
                return OpenContainerAction(container)
            return ElevatorAction()
        if key == pygame.K_f:
            w = self.player.equipped_weapon
            if w and w.range_type == RangeType.MELEE:
                reach = w.range_tiles
                diag  = w.diagonal
                target = self._aim_target
                if target is not None and target.alive and self.floor.dungeon_map.visible[target.y, target.x]:
                    action = MeleeAttackAction(target, range_tiles=reach, diagonal=diag)
                    if action.validate(self.player, self.floor):
                        return action
                return self._nearest_melee_target()
            # For ranged: use _aim_target if set and still valid, else pick nearest
            target = self._aim_target
            if target is None or not target.alive or not self.floor.dungeon_map.visible[target.y, target.x]:
                return self._nearest_ranged_target()
            return RangedAttackAction(target, max_range=w.range_tiles if w else 8)
        return None

    def _launch_heal(self) -> None:
        """Launch the healing rhythm overlay for the best available consumable."""
        assert self.player is not None
        from dungeoneer.items.consumable import Consumable

        healables = [
            i for i in self.player.inventory
            if isinstance(i, Consumable) and i.heal_amount > 0
        ]
        if not healables:
            bus.post(LogMessageEvent(t("log.no_heals"), (180, 80, 80)))
            self.audio.play("action_denied")
            return

        if self.player.max_hp - self.player.hp <= 0:
            bus.post(LogMessageEvent(t("log.full_hp"), (120, 120, 140)))
            self.audio.play("action_denied")
            return

        # Pick best fitting item; fall back to smallest overheal item.
        # Threshold scales the "safe" window: at 80% we trust a good minigame score,
        # at 120% we only consider an item safe if even its max output won't overheal.
        missing = self.player.max_hp - self.player.hp
        thr = self.heal_threshold_pct / 100.0
        exact = [i for i in healables if i.heal_amount * thr <= missing]
        consumable = max(exact, key=lambda c: c.heal_amount) if exact else min(healables, key=lambda c: c.heal_amount)

        if not exact:
            # All available items would overheal — ask the player to confirm.
            self._overheal_pending = consumable
            self._overheal_confirm_open = True
            return

        self._do_launch_heal(consumable)

    def _do_launch_heal(self, consumable) -> None:
        """Actually launch heal (minigame or flat) for the given consumable."""
        if not self.use_heal_minigame:
            self._on_heal_complete(consumable, consumable.heal_amount)
            return

        from dungeoneer.minigame.heal_scene import HealOverlay

        def on_complete(actual_heal: int) -> None:
            self._on_heal_complete(consumable, actual_heal)

        self.music.duck(0.20)
        self._heal_overlay = HealOverlay(
            consumable=consumable,
            player=self.player,
            on_complete=on_complete,
            audio_manager=self.audio,
            difficulty=self.difficulty,
        )

    def _on_heal_complete(self, consumable, actual_heal: int) -> None:
        """Called by HealOverlay when the rhythm minigame finishes."""
        self._heal_overlay = None
        self.music.unduck()
        if actual_heal < 0:   # cancelled
            bus.post(LogMessageEvent(t("log.heal_cancel"), (120, 120, 140)))
            return

        assert self.player is not None
        # Remove / decrement the item from inventory
        if consumable.count > 1:
            consumable.count -= 1
        else:
            self.player.inventory.remove(consumable)

        real = self.player.heal(actual_heal)
        self.audio.play("heal")
        bus.post(LogMessageEvent(t("log.heal_restored").format(n=real), (80, 220, 140)))
        self._schedule_advance()

    def _find_adjacent_container(self):
        assert self.player is not None
        assert self.floor  is not None
        for c in self.floor.containers:
            if c.opened:
                continue
            if abs(self.player.x - c.x) <= 1 and abs(self.player.y - c.y) <= 1:
                return c
        return None

    def _adjacent_elevator_pos(self) -> tuple[int, int] | None:
        """Return (x, y) of a cardinally adjacent ELEVATOR_CLOSED tile, or None."""
        if self.player is None or self.floor is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = self.player.x + dx, self.player.y + dy
            if self.floor.dungeon_map.in_bounds(nx, ny):
                if self.floor.dungeon_map.get_type(nx, ny) == TileType.ELEVATOR_CLOSED:
                    return (nx, ny)
        return None

    # ------------------------------------------------------------------
    # Tutorial helpers
    # ------------------------------------------------------------------

    def _maybe_show_tutorial(self, step: str) -> None:
        """Enqueue a tutorial step (used from alert-banner sites and on_enter)."""
        self._enqueue_tutorial(step)

    def _enqueue_tutorial(self, step: str) -> None:
        """Mark step as pending and show it immediately or queue it."""
        if not self.tutorial_manager.should_show(step):
            return
        self._tutorial_queue.append(step)
        if not self._tutorial_open:
            self._drain_tutorial_queue()

    def _drain_tutorial_queue(self) -> None:
        """Show the next queued step if nothing is currently displayed."""
        if not self._tutorial_open and self._tutorial_queue:
            step = self._tutorial_queue.pop(0)
            self._tutorial_open = True
            self.tutorial_overlay.show(step, on_close=self._on_tutorial_close)

    def _on_tutorial_close(self) -> None:
        self._tutorial_open = False
        # Re-check conditions (e.g. a container became visible while we were reading
        # the movement tutorial) and then show the next queued step.
        self._check_tutorial_triggers()
        self._drain_tutorial_queue()

    def _check_tutorial_triggers(self) -> None:
        """Enqueue any tutorial steps whose conditions are now met.

        Safe to call at any time — each step is only ever enqueued once
        (should_show() marks it as seen on the first call).
        """
        if self.player is None:
            return
        from dungeoneer.items.consumable import Consumable
        from dungeoneer.items.weapon import Weapon
        from dungeoneer.items.item import RangeType
        # Container tutorial: player can see an unopened container
        if self.floor and any(
            not c.opened and self.floor.dungeon_map.visible[c.y, c.x]
            for c in self.floor.containers
        ):
            self._enqueue_tutorial("container")
        # Ammo tutorial: clip empty OR an extra ranged weapon is in inventory
        w = self.player.equipped_weapon
        clip_empty = (
            w is not None
            and w.range_type == RangeType.RANGED
            and w.ammo_current == 0
        )
        extra_ranged = any(
            isinstance(it, Weapon) and it.range_type == RangeType.RANGED
            for it in self.player.inventory
        )
        if clip_empty or extra_ranged:
            self._enqueue_tutorial("ammo")
        # Medipack tutorial: player has a consumable
        if any(isinstance(it, Consumable) for it in self.player.inventory):
            self._enqueue_tutorial("medipack")

    # ------------------------------------------------------------------
    # Hack minigame integration
    # ------------------------------------------------------------------

    def _launch_hack(self, container: "ContainerEntity") -> None:
        self._held_move_key = None  # stop auto-repeat movement when minigame starts

        def on_complete(success: bool, items, credits: int) -> None:
            self._on_hack_complete(success, items, credits, container)

        self.music.pause()

        from dungeoneer.minigame.hack_scene_grid import HackGridScene
        from dungeoneer.minigame.hack_grid_generator import HackGridParams
        params = HackGridParams.for_difficulty(self.difficulty)
        self.app.scenes.push(HackGridScene(self.app, params=params, on_complete=on_complete))

    def _on_hack_complete(
        self, success: bool, items, credits: int, container: "ContainerEntity"
    ) -> None:
        assert self.player is not None
        assert self.floor  is not None

        container.opened = True

        if success:
            credits_str = ""
            if credits > 0:
                self.player.credits += credits
                credits_str = f"  +¥{credits}"
            bus.post(LogMessageEvent(t("log.hack_success").format(container=container.name, credits=credits_str), (200, 180, 80)))
            for item in items:
                self.floor.add_item_entity(ItemEntity(self.player.x, self.player.y, item))
            self.resolver._auto_pickup(self.player, self.floor)
        else:
            from dungeoneer.ai.states import CombatState
            bus.post(LogMessageEvent(t("log.hack_fail"), (220, 60, 60)))
            sx, sy = self._find_drone_spawn(container)
            drone = make_drone(sx, sy)
            drone.ai_brain.set_state(CombatState())
            self.floor.add_actor(drone)
            log.info("Spawned alert drone at (%d,%d) after failed hack", sx, sy)

        self._hack_just_completed = True

    # ------------------------------------------------------------------
    # Aim minigame integration
    # ------------------------------------------------------------------

    def _launch_aim(self, target: Enemy) -> None:
        from dungeoneer.minigame.aim_scene import AimOverlay

        assert self.player is not None
        w = self.player.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED:
            return

        if w.ammo_current <= 0:
            bus.post(LogMessageEvent(t("log.no_ammo"), (180, 80, 80)))
            return

        shots = getattr(w, "shots", 1)

        def on_complete(results: list) -> None:
            self._on_aim_complete(target, results)

        self._aim_overlay = AimOverlay(
            weapon=w, player=self.player, target=target,
            shots=shots, on_complete=on_complete,
            needle_speed_mult=self.difficulty.aim_needle_speed_mult,
        )

    def _on_aim_complete(self, target: Enemy, results: list) -> None:
        assert self.player is not None
        assert self.floor  is not None

        w = self.player.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED:
            return

        action = RangedAttackAction(
            target,
            max_range=w.range_tiles,
            accuracy_values=results,
        )
        if not action.validate(self.player, self.floor):
            return

        result = action.execute(self.player, self.floor, self.resolver)
        if result.message:
            bus.post(LogMessageEvent(result.message, result.msg_colour))

        burst = result.burst_events
        if burst:
            bus.post(burst[0])
            for i, ev in enumerate(burst[1:], start=1):
                self._burst_queue.append((i * self._BURST_INTERVAL, ev))
            self._schedule_advance(extra_delay=(len(burst) - 1) * self._BURST_INTERVAL)
        else:
            self._schedule_advance()

        now_visible = self._any_enemy_visible()
        if now_visible and not self._had_visible_enemies:
            self.alert_banner.trigger()
            self.music.to_action(fast=True)
            self._maybe_show_tutorial("enemy")
        self._had_visible_enemies = now_visible

    # ------------------------------------------------------------------
    # Melee minigame integration
    # ------------------------------------------------------------------

    def _launch_melee(self, target: Enemy) -> None:
        from dungeoneer.minigame.melee_scene import MeleeOverlay

        assert self.player is not None
        w = self.player.equipped_weapon

        def on_complete(power: float) -> None:
            self._on_melee_complete(target, power)

        self._melee_overlay = MeleeOverlay(
            weapon=w, player=self.player, target=target,
            on_complete=on_complete,
            freq_mult=self.difficulty.melee_freq_mult,
        )

    def _on_melee_complete(self, target: Enemy, power: float) -> None:
        assert self.player is not None
        assert self.floor  is not None

        if power < 0.0:
            return  # cancelled — no turn spent

        w = self.player.equipped_weapon
        reach = w.range_tiles if w else 1
        diag  = w.diagonal    if w else False
        action = MeleeAttackAction(target, range_tiles=reach, diagonal=diag, power=power)
        if not action.validate(self.player, self.floor):
            return

        result = action.execute(self.player, self.floor, self.resolver)
        if result.message:
            bus.post(LogMessageEvent(result.message, result.msg_colour))
        if result.success:
            self._schedule_advance()

        now_visible = self._any_enemy_visible()
        if now_visible and not self._had_visible_enemies:
            self.alert_banner.trigger()
            self.music.to_action(fast=True)
            self._maybe_show_tutorial("enemy")
        self._had_visible_enemies = now_visible

    # ------------------------------------------------------------------
    # Cheat / debug menu
    # ------------------------------------------------------------------

    def _apply_cheat(self, action: str) -> None:
        """Execute a cheat action from CheatMenuOverlay."""
        assert self.player is not None
        assert self.floor  is not None

        if action.startswith("spawn_item:"):
            item_id = action.split(":", 1)[1]
            item = self._make_cheat_item(item_id)
            if item is not None:
                self.resolver.give_item(self.player, item)
                bus.post(LogMessageEvent(f"[CHEAT] {item.name}", (80, 220, 120)))

        elif action.startswith("spawn_enemy:"):
            enemy_id = action.split(":", 1)[1]
            pos = self._cheat_find_spawn_pos()
            if pos is None:
                return
            tx, ty = pos
            if enemy_id == "guard":
                enemy = make_guard(tx, ty)
            else:
                enemy = make_drone(tx, ty)
            self.floor.add_actor(enemy)
            self.turn_manager.build_queue(self.floor)
            bus.post(LogMessageEvent(f"[CHEAT] {enemy.name}", (80, 220, 120)))

        elif action == "spawn_container":
            pos = self._cheat_find_spawn_pos()
            if pos is None:
                return
            tx, ty = pos
            container = self._make_container(tx, ty)
            self.floor.add_container(container)
            bus.post(LogMessageEvent("[CHEAT] chest spawned", (80, 220, 120)))

        elif action.startswith("hp:"):
            mode = action[3:]
            if mode == "full":
                self.player.hp = self.player.max_hp
            elif mode == "1":
                self.player.hp = 1
            elif mode == "+10":
                self.player.hp = min(self.player.max_hp, self.player.hp + 10)
            elif mode == "+20":
                self.player.hp = min(self.player.max_hp, self.player.hp + 20)
            bus.post(LogMessageEvent(f"[CHEAT] HP → {self.player.hp}/{self.player.max_hp}", (80, 220, 120)))

        elif action == "credits:+100":
            self.player.credits += 100
            bus.post(LogMessageEvent(f"[CHEAT] +¥100 → ¥{self.player.credits}", (80, 220, 120)))

    @staticmethod
    def _make_cheat_item(item_id: str):
        """Return a fresh item instance for the given id, or None if unknown."""
        from dungeoneer.items.weapon import (
            make_pistol, make_combat_knife, make_shotgun,
            make_smg, make_energy_sword, make_rifle,
        )
        from dungeoneer.items.consumable import make_stim_pack, make_medkit
        from dungeoneer.items.ammo import make_9mm_ammo, make_rifle_ammo, make_shotgun_ammo
        from dungeoneer.items.armor import make_basic_armor

        _factories = {
            "pistol":        make_pistol,
            "combat_knife":  make_combat_knife,
            "shotgun":       make_shotgun,
            "smg":           make_smg,
            "energy_sword":  make_energy_sword,
            "rifle":         make_rifle,
            "stim_pack":     make_stim_pack,
            "medkit":        make_medkit,
            "ammo_9mm":      lambda: make_9mm_ammo(10),
            "ammo_rifle":    lambda: make_rifle_ammo(6),
            "ammo_shell":    lambda: make_shotgun_ammo(8),
            "basic_armor":   make_basic_armor,
        }
        factory = _factories.get(item_id)
        return factory() if factory else None

    def _cheat_find_spawn_pos(self) -> tuple[int, int] | None:
        """Find a free walkable tile adjacent to (or near) the player."""
        assert self.player is not None
        assert self.floor  is not None
        dm = self.floor.dungeon_map
        px, py = self.player.x, self.player.y
        for r in range(1, 8):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    if abs(dx) != r and abs(dy) != r:
                        continue
                    tx, ty = px + dx, py + dy
                    if not dm.in_bounds(tx, ty) or not dm.is_walkable(tx, ty):
                        continue
                    if self.floor.get_actor_at(tx, ty) is not None:
                        continue
                    return tx, ty
        return None

    def _find_drone_spawn(self, container: "ContainerEntity") -> tuple[int, int]:
        """Find the best tile to spawn a drone near a container: walkable, LOS to player,
        closest to DRONE_PREFERRED_DIST away from the player."""
        from dungeoneer.combat.line_of_sight import has_los
        from dungeoneer.core.settings import DRONE_PREFERRED_DIST

        assert self.player is not None
        assert self.floor  is not None

        cx, cy = container.x, container.y
        px, py = self.player.x, self.player.y
        dm = self.floor.dungeon_map

        candidates: list[tuple[int, int]] = []
        for dy in range(-8, 9):
            for dx in range(-8, 9):
                tx, ty = cx + dx, cy + dy
                if not dm.in_bounds(tx, ty) or not dm.is_walkable(tx, ty):
                    continue
                if (tx, ty) == (px, py):
                    continue
                if self.floor.get_actor_at(tx, ty) is not None:
                    continue
                candidates.append((tx, ty))

        if not candidates:
            return cx, cy

        los_candidates = [
            (x, y) for x, y in candidates
            if has_los(x, y, px, py, dm)
        ]
        pool = los_candidates if los_candidates else candidates
        return min(pool, key=lambda p: abs(abs(p[0] - px) + abs(p[1] - py) - DRONE_PREFERRED_DIST))

    @staticmethod
    def _make_container(x: int, y: int) -> ContainerEntity:
        import random
        from dungeoneer.items.consumable import make_stim_pack, make_medkit
        from dungeoneer.items.ammo import make_9mm_ammo, make_rifle_ammo
        from dungeoneer.items.weapon import make_rifle, make_shotgun
        from dungeoneer.items.armor import make_basic_armor

        pool = [
            (0.27, lambda: make_stim_pack()),
            (0.13, lambda: make_medkit()),
            (0.22, lambda: make_9mm_ammo(8)),
            (0.11, lambda: make_rifle_ammo(3)),
            (0.10, lambda: make_shotgun()),
            (0.08, lambda: make_rifle()),
            (0.09, lambda: make_basic_armor()),
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
        return ContainerEntity(x=x, y=y, items=items, credits=credits, name=t("entity.crate.name"))

    def _visible_enemies_in_weapon_range(self) -> list:
        """Return visible living enemies within current weapon's range, sorted by distance."""
        if self.player is None or self.floor is None:
            return []
        w = self.player.equipped_weapon
        max_range = w.range_tiles if w else 1
        diag = w.diagonal if w else False

        def in_range(e):
            dx = abs(e.x - self.player.x)
            dy = abs(e.y - self.player.y)
            dist = max(dx, dy) if diag else (dx + dy)
            return dist <= max_range

        return sorted(
            [
                a for a in self.floor.actors
                if isinstance(a, Enemy) and a.alive
                and self.floor.dungeon_map.visible[a.y, a.x]
                and in_range(a)
            ],
            key=lambda e: abs(e.x - self.player.x) + abs(e.y - self.player.y),
        )

    def _cycle_aim_target(self) -> None:
        """Cycle _aim_target through enemies in current weapon range (Tab key handler)."""
        if self.player is None or self.floor is None:
            return
        enemies = self._visible_enemies_in_weapon_range()
        if not enemies:
            self._aim_target = None
            return
        if self._aim_target not in enemies:
            self._aim_target = enemies[0]
        else:
            idx = enemies.index(self._aim_target)
            self._aim_target = enemies[(idx + 1) % len(enemies)]

    def _enemy_at_screen_pos(self, mx: int, my: int) -> "Enemy | None":
        """Return a visible living enemy whose tile is under the given screen pixel, or None."""
        if self.player is None or self.floor is None:
            return None
        cam = self.renderer.camera
        tile_x = (mx + cam.offset_x) // settings.TILE_SIZE
        tile_y = (my + cam.offset_y) // settings.TILE_SIZE
        for actor in self.floor.actors:
            if (
                isinstance(actor, Enemy) and actor.alive
                and actor.x == tile_x and actor.y == tile_y
                and self.floor.dungeon_map.visible[actor.y, actor.x]
            ):
                return actor
        return None

    def _container_at_screen_pos(self, mx: int, my: int):
        """Return an unopened adjacent container whose tile is under the given screen pixel, or None."""
        if self.player is None or self.floor is None:
            return None
        cam = self.renderer.camera
        tile_x = (mx + cam.offset_x) // settings.TILE_SIZE
        tile_y = (my + cam.offset_y) // settings.TILE_SIZE
        for container in self.floor.containers:
            if (
                not container.opened
                and container.x == tile_x and container.y == tile_y
                and abs(self.player.x - tile_x) <= 1 and abs(self.player.y - tile_y) <= 1
            ):
                return container
        return None

    def _nearest_ranged_target(self):
        assert self.player is not None
        assert self.floor  is not None

        w = self.player.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED:
            bus.post(LogMessageEvent(t("log.no_ranged"), (180, 80, 80)))
            self.audio.play("action_denied")
            return None

        visible_enemies = [
            a for a in self.floor.actors
            if isinstance(a, Enemy) and a.alive
            and self.floor.dungeon_map.visible[a.y, a.x]
        ]
        if not visible_enemies:
            bus.post(LogMessageEvent(t("log.no_target"), (180, 80, 80)))
            self.audio.play("action_denied")
            return None

        nearest = min(
            visible_enemies,
            key=lambda e: abs(e.x - self.player.x) + abs(e.y - self.player.y),
        )
        return RangedAttackAction(nearest, max_range=w.range_tiles)

    def _nearest_melee_target(self):
        assert self.player is not None
        assert self.floor  is not None

        w = self.player.equipped_weapon
        reach = w.range_tiles if w else 1
        diag  = w.diagonal    if w else False

        def dist(e):
            dx = abs(e.x - self.player.x)
            dy = abs(e.y - self.player.y)
            return max(dx, dy) if diag else (dx + dy)

        in_reach = [
            a for a in self.floor.actors
            if isinstance(a, Enemy) and a.alive
            and self.floor.dungeon_map.visible[a.y, a.x]
            and dist(a) <= reach
        ]
        if not in_reach:
            bus.post(LogMessageEvent(t("log.no_melee"), (180, 80, 80)))
            self.audio.play("action_denied")
            return None

        return MeleeAttackAction(min(in_reach, key=dist), range_tiles=reach, diagonal=diag)

    # ------------------------------------------------------------------
    # Scene interface
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self.alert_banner.update(dt)
        self.floating_nums.update(dt)
        self.music.update(dt)

        # Elevator animation state machine
        if self._elevator_phase is not None:
            self._elevator_timer -= dt
            if self._elevator_timer <= 0.0:
                ex, ey = self._elevator_pos
                if self._elevator_phase == "opening":
                    # Move player into the elevator
                    self.player.x, self.player.y = ex, ey
                    self._elevator_phase = "entering"
                    self._elevator_timer = 0.25
                elif self._elevator_phase == "entering":
                    # Close the elevator doors
                    self.floor.dungeon_map.set_type(ex, ey, TileType.ELEVATOR_CLOSED)
                    self.audio.play("elevator_close", 0.5)
                    self._elevator_phase = "closing"
                    self._elevator_timer = 0.4
                elif self._elevator_phase == "closing":
                    # Descend to next floor
                    self._elevator_phase = None
                    self._elevator_pos = None
                    self._elevator_descend()

        if self._aim_overlay is not None:
            self._aim_overlay.update(dt)
            if not self._aim_overlay.is_active:
                self._aim_overlay = None
                # Keep _aim_target if enemy is still alive and visible
                tgt = self._aim_target
                if tgt is not None and (
                    not tgt.alive
                    or self.floor is None
                    or not self.floor.dungeon_map.visible[tgt.y, tgt.x]
                ):
                    self._aim_target = None

        if self._heal_overlay is not None:
            _ho = self._heal_overlay
            _ho.update(dt)
            if not _ho.is_active:
                self._heal_overlay = None

        if self._melee_overlay is not None:
            self._melee_overlay.update(dt)
            if not self._melee_overlay.is_active:
                self._melee_overlay = None

        # Fire deferred burst-shot DamageEvents at staggered intervals
        if self._burst_queue:
            remaining = []
            for timer, ev in self._burst_queue:
                timer -= dt
                if timer <= 0.0:
                    bus.post(ev)
                else:
                    remaining.append((timer, ev))
            self._burst_queue = remaining

        if self._pending_advance and not self._game_over:
            self._advance_timer -= dt
            if self._advance_timer <= 0.0:
                self._pending_advance = False
                self.turn_manager.advance(self.floor, self.resolver)
                self._update_music_state()

        # Auto-repeat movement when a move key is held
        if self._held_move_key is not None and self.player is not None and self.floor is not None:
            self._move_hold_timer -= dt
            if self._move_hold_timer <= 0.0:
                can_act = (
                    not self._game_over
                    and not self._pending_advance
                    and self.turn_manager.is_player_turn()
                    and self._aim_overlay is None
                    and self._heal_overlay is None
                    and self._melee_overlay is None
                    and self._elevator_phase is None
                    and not self._inventory_open
                    and not self._weapon_picker_open
                    and not self._help_open
                    and not self._quit_confirm_open
                    and not self._overheal_confirm_open
                    and not self._cheat_menu_open
                    and not self._tutorial_open
                    and not self.alert_banner.is_blocking
                    and not self._had_visible_enemies
                    and not self._is_any_enemy_alert()
                )
                if can_act:
                    action = self._key_to_action(self._held_move_key)
                    if isinstance(action, MoveAction) and action.validate(self.player, self.floor):
                        result = action.execute(self.player, self.floor, self.resolver)
                        if result.message:
                            bus.post(LogMessageEvent(result.message, result.msg_colour))
                        if result.success:
                            self._schedule_advance()
                            now_visible = self._any_enemy_visible()
                            if now_visible and not self._had_visible_enemies:
                                self.alert_banner.trigger()
                                self.music.to_action(fast=True)
                                self._maybe_show_tutorial("enemy")
                            self._had_visible_enemies = now_visible
                            self._move_hold_timer = self._MOVE_HOLD_REPEAT
                    else:
                        # Obstacle/enemy in the way — stop repeating until key is re-pressed
                        self._held_move_key = None

    def render(self, screen: pygame.Surface) -> None:
        if self.floor and self.player:
            self.renderer.draw(
                screen, self.floor, self.player,
                hud=self.hud,
                combat_log=self.combat_log,
            )
            self.floating_nums.draw(screen, self.renderer.camera)
            self.alert_banner.draw(screen, self.renderer.camera, self.player.x, self.player.y)
            # Elevator hint — shown when player is adjacent to a closed elevator
            if (
                self._adjacent_elevator_pos() is not None
                and self._elevator_phase is None
                and not self._inventory_open
                and not self._weapon_picker_open
                and not self._help_open
                and not self._quit_confirm_open
                and not self._overheal_confirm_open
                and not self._cheat_menu_open
                and not self._minimap_open
                and self._aim_overlay is None
                and self._heal_overlay is None
                and self._melee_overlay is None
            ):
                cam = self.renderer.camera
                ts  = settings.TILE_SIZE
                sx, sy = cam.world_to_screen(self.player.x, self.player.y)
                hint_surf = self._hint_font.render(t("hint.elevator_descend"), True, (220, 220, 100))
                hw = hint_surf.get_width()
                hh = hint_surf.get_height()
                pad = 4
                box = pygame.Surface((hw + pad * 2, hh + pad * 2), pygame.SRCALPHA)
                pygame.draw.rect(box, (20, 20, 30, 90), box.get_rect(), border_radius=3)
                pygame.draw.rect(box, (180, 160, 60, 100), box.get_rect(), 1, border_radius=3)
                hint_surf.set_alpha(160)
                box.blit(hint_surf, (pad, pad))
                bx = sx + ts // 2 - (hw + pad * 2) // 2
                by = sy - hh - pad * 2 - 6
                screen.blit(box, (bx, by))
            # Targeting highlight — yellow outline around selected aim target
            if self._aim_target is not None and self._aim_target.alive:
                cam = self.renderer.camera
                sx = self._aim_target.x * settings.TILE_SIZE - cam.offset_x
                sy = self._aim_target.y * settings.TILE_SIZE - cam.offset_y
                pygame.draw.rect(screen, (240, 220, 0), (sx, sy, settings.TILE_SIZE, settings.TILE_SIZE), 2)
            # Aim overlay (in-world arc, no scene push)
            if self._aim_overlay is not None:
                cam = self.renderer.camera
                self._aim_overlay.render(screen, cam.offset_x, cam.offset_y)
            # Heal overlay (centred panel, no scene push)
            if self._heal_overlay is not None:
                self._heal_overlay.render(screen)
            # Melee overlay (in-world power bar, no scene push)
            if self._melee_overlay is not None:
                cam = self.renderer.camera
                self._melee_overlay.render(screen, cam.offset_x, cam.offset_y)
            if self._inventory_open:
                self.inventory_ui.draw(screen, self.player)
            elif self._weapon_picker_open:
                self.weapon_picker.draw(screen, self.player)
            if self._help_open:
                self.help_screen.draw(screen)
            if self._quit_confirm_open:
                self.quit_confirm.draw(screen)
            if self._overheal_confirm_open:
                self.overheal_confirm.draw(screen)
            if self._cheat_menu_open:
                self.cheat_menu.draw(screen)
            if self._minimap_open:
                self.minimap.draw(screen, self.floor, self.player)
            if self._tutorial_open:
                self.tutorial_overlay.draw(screen)
