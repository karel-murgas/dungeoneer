"""Primary play scene — dungeon, input, turn loop."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame

log = logging.getLogger(__name__)

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.event_bus import bus, DeathEvent, StairEvent, ElevatorEvent, LogMessageEvent, ObjectiveEvent, DamageEvent, MissEvent, EnemyBurstQueueEvent, HeatLevelUpEvent, TurnEndEvent, RoomRevealedEvent
from dungeoneer.systems.heat import HeatSystem
from dungeoneer.systems.encounter import EncounterSystem
from dungeoneer.core.difficulty import Difficulty, NORMAL
from dungeoneer.core.i18n import t
from dungeoneer.world.dungeon_generator import DungeonGenerator
from dungeoneer.world.floor import Floor
from dungeoneer.world.tile import TileType
from dungeoneer.world.fov import compute_fov
from dungeoneer.entities.player import Player
from dungeoneer.entities.enemy import (
    Enemy, make_guard, make_drone, make_dog,
    make_heavy, make_turret, make_sniper_drone, make_riot_guard,
)
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
from dungeoneer.rendering.ui.help_catalog import (
    HelpCatalogOverlay, _TAB_EXPLORATION, _TAB_AIMING, _TAB_MELEE, _TAB_HEALING,
    _TAB_ITEMS, _TAB_HEAT, _TAB_VAULT,
)
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
        self.help_catalog   = HelpCatalogOverlay()
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
        self.heat_system: HeatSystem | None = None
        self.encounter_system: EncounterSystem | None = None
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
        self._fov_debug_on       = False   # F10: paint LOS/FOV mismatches
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
        self._vault_overlay = None              # VaultOverlay instance when draining
        self._vault_container = None            # the objective ContainerEntity
        self._vault_credits_banked: int = 0     # credits accumulated across sessions
        self._vault_fully_drained: bool = False
        self._vault_session_state: dict | None = None  # cursor/drain state saved between sessions
        # Elevator animation state machine: None | "opening" | "entering" | "closing" | "descending"
        self._elevator_phase: str | None = None
        self._elevator_timer: float = 0.0
        self._elevator_pos: tuple[int, int] | None = None  # (x, y) of elevator tile
        # Arrival animation (reverse): None | "arrive_closed" | "arrive_open" | "arrive_exit" | "arrive_closing"
        self._arrival_phase: str | None = None
        self._arrival_timer: float = 0.0
        self._arrival_elevator_pos: tuple[int, int] | None = None
        self._arrival_spawn_pos: tuple[int, int] | None = None
        self._hint_font   = pygame.font.SysFont("consolas", 14, bold=True)

    def on_enter(self) -> None:
        log.info(f"GameScene.on_enter  tutorial_enabled={self.tutorial_manager.enabled}")
        self._subscribe_events()
        self.audio.attach()
        self._load_floor(depth=1)
        self.music.start()

    def on_exit(self) -> None:
        log.info("GameScene.on_exit  game_over=%s", self._game_over)
        self._unsubscribe_events()
        if self.encounter_system is not None:
            self.encounter_system.teardown()
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
                compute_fov(self.player.x, self.player.y, self.floor.dungeon_map, rooms=self.floor.rooms)
                now_visible = self._any_enemy_visible()
                if now_visible and not self._had_visible_enemies:
                    self.alert_banner.trigger()
                    self.music.to_action(fast=True)
                    self._maybe_show_tutorial("enemy")
                    bus.post(LogMessageEvent(t("log.room_encounter"), colour=(220, 80, 60)))
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
            bus.subscribe(DamageEvent,          self._on_damage)
            bus.subscribe(MissEvent,            self._on_miss)
            bus.subscribe(EnemyBurstQueueEvent, self._on_enemy_burst)
            bus.subscribe(HeatLevelUpEvent,     self._on_heat_level_up)
            bus.subscribe(TurnEndEvent,         self._on_turn_end_heat)
            self._subscribed = True

    def _unsubscribe_events(self) -> None:
        bus.unsubscribe(DeathEvent,     self._on_death)
        bus.unsubscribe(StairEvent,     self._on_stair)
        bus.unsubscribe(ElevatorEvent,  self._on_elevator)
        bus.unsubscribe(ObjectiveEvent, self._on_objective)
        bus.unsubscribe(DamageEvent,          self._on_damage)
        bus.unsubscribe(MissEvent,            self._on_miss)
        bus.unsubscribe(EnemyBurstQueueEvent, self._on_enemy_burst)
        bus.unsubscribe(HeatLevelUpEvent,     self._on_heat_level_up)
        bus.unsubscribe(TurnEndEvent,         self._on_turn_end_heat)
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
        # Heat system must exist before generate() call so tier_cap is correct.
        # On floor 1 the player is freshly created below, so we bootstrap with
        # a temporary player if needed, then hand it to HeatSystem after.
        result = gen.generate(
            mw, mh,
            floor_depth=depth,
            containers=self.difficulty.containers_per_floor,
        )
        self.floor = Floor(result.dungeon_map, depth)
        self.floor.rooms = result.rooms

        player_spawn = next(s for s in result.spawns if s.kind == "player")
        if existing_player is None:
            self.player = Player(player_spawn.x, player_spawn.y, self.difficulty)
        else:
            existing_player.x = player_spawn.x
            existing_player.y = player_spawn.y
            self.player = existing_player

        # Create / reuse HeatSystem (created once, persists for the whole run)
        if self.heat_system is None:
            self.heat_system = HeatSystem(self.player)
            self.heat_system.subscribe()
        self.hud.heat_system = self.heat_system

        self.player.floor_depth = depth
        self.floor.add_actor(self.player)

        for spawn in result.spawns:
            if spawn.kind == "container":
                self.floor.add_container(self._make_container(spawn.x, spawn.y))

        # On the final floor keep the elevator for extraction and place the vault
        # in the same room but at least 3 tiles away so [E] doesn't trigger both.
        if depth == FLOORS_PER_RUN:
            import random as _rnd
            ex, ey = result.stair_pos  # exit elevator stays as ELEVATOR_CLOSED
            # Find the room containing the elevator and pick a far floor tile for vault
            vault_x, vault_y = None, None
            candidates = []
            for room in result.rooms:
                if room.x <= ex < room.x + room.w and room.y <= ey < room.y + room.h:
                    for ty in range(room.y, room.y + room.h):
                        for tx in range(room.x, room.x + room.w):
                            if not self.floor.dungeon_map.is_walkable(tx, ty):
                                continue
                            if max(abs(tx - ex), abs(ty - ey)) >= 3:
                                candidates.append((tx, ty))
                    break
            if candidates:
                vault_x, vault_y = _rnd.choice(candidates)
            else:
                # Fallback: adjacent tile (shouldn't happen in normal maps)
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    if self.floor.dungeon_map.is_walkable(ex + dx, ey + dy):
                        vault_x, vault_y = ex + dx, ey + dy
                        break
            if vault_x is not None:
                obj_credits = self.difficulty.objective_credits
                self.floor.add_container(
                    ContainerEntity(vault_x, vault_y, credits=obj_credits,
                                    is_objective=True, name=t("entity.corp_vault.name"))
                )
            # Reset vault state for this run (only on floor 1 load, but depth==FLOORS_PER_RUN
            # means a fresh run reaching floor 3 — vault is always fresh here)
            self._vault_credits_banked = 0
            self._vault_fully_drained = False
            self._vault_overlay = None
            self._vault_container = None
            self._vault_session_state = None
            self.hud.vault_credits_banked = 0

        # Start the arrival animation from the entry elevator on every floor
        # (floor 1: game start; floors 2+: descending from above).
        # Player is temporarily placed at the elevator tile (hidden); after the
        # animation they step out to the adjacent spawn position.
        self._arrival_phase = None
        self._arrival_elevator_pos = None
        self._arrival_spawn_pos = None
        entry_ex, entry_ey = result.entry_pos
        # Find the walkable tile adjacent to the entry elevator
        entry_spawn_x, entry_spawn_y = entry_ex, entry_ey
        for adx, ady in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if self.floor.dungeon_map.is_walkable(entry_ex + adx, entry_ey + ady):
                entry_spawn_x, entry_spawn_y = entry_ex + adx, entry_ey + ady
                break
        # Move player into elevator tile for the animation start
        self.player.x, self.player.y = entry_ex, entry_ey
        self._arrival_elevator_pos = (entry_ex, entry_ey)
        self._arrival_spawn_pos = (entry_spawn_x, entry_spawn_y)
        self._arrival_phase = "arrive_closed"
        self._arrival_timer = 0.35
        fov_x, fov_y = entry_spawn_x, entry_spawn_y

        # Tear down previous floor's encounter system, then create a new one.
        # Must happen before compute_fov so that the starting-room RoomRevealedEvent
        # is handled by the new EncounterSystem.
        if self.encounter_system is not None:
            self.encounter_system.teardown()
        end_room = self.floor.room_for_tile(*result.stair_pos)
        self.encounter_system = EncounterSystem(
            self.floor, self.heat_system, self.difficulty, end_room, self.turn_manager
        )
        try:
            bus.unsubscribe(RoomRevealedEvent, self._on_room_revealed)
        except (KeyError, ValueError):
            pass
        bus.subscribe(RoomRevealedEvent, self._on_room_revealed)
        compute_fov(fov_x, fov_y, self.floor.dungeon_map, rooms=self.floor.rooms)
        self.turn_manager.build_queue(self.floor)
        self._had_visible_enemies = False

        log.info(
            "Floor %d loaded  actors=%s  stair=%s  entry=%s",
            depth, [a.name for a in self.floor.actors], result.stair_pos, result.entry_pos,
        )
        self.combat_log.add(t("log.floor_enter").format(n=depth), (80, 200, 180))

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_room_revealed(self, event: RoomRevealedEvent) -> None:
        log.debug("RoomRevealedEvent  room=(%d,%d,%dx%d)", event.room.x, event.room.y, event.room.w, event.room.h)

    def _on_death(self, event: DeathEvent) -> None:
        log.info(
            "_on_death  entity=%s  is_player=%s  game_over=%s",
            event.entity.name, event.entity is self.player, self._game_over,
        )
        if event.entity is self.player:
            self._trigger_game_over(victory=False)
        elif isinstance(event.entity, Enemy):
            self._drop_loot(event.entity)
            self._maybe_show_tutorial("heat")

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

    def _on_enemy_burst(self, event: EnemyBurstQueueEvent) -> None:
        """Stagger subsequent shots of an enemy burst weapon (e.g. turret double-tap)."""
        for i, dmg_ev in enumerate(event.events, start=1):
            self._burst_queue.append((i * self._BURST_INTERVAL, dmg_ev))

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
            # Final extraction: award vault credits before victory
            if self._vault_credits_banked > 0:
                total = self._vault_credits_banked
                if self._vault_fully_drained:
                    bonus = round(total * settings.VAULT_FULL_DRAIN_BONUS)
                    self.player.credits += bonus
                    bus.post(LogMessageEvent(
                        t("log.vault_bonus").format(bonus=bonus), (200, 200, 80)
                    ))
                self.player.credits += total
                bus.post(LogMessageEvent(
                    t("log.vault_extract").format(credits=self.player.credits), (80, 230, 160)
                ))
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

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        # Track held movement keys for auto-repeat (KEYUP always clears, regardless of overlays)
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in self._HOLD_MOVE_KEYS:
                if not self._cheat_menu_open:
                    self._held_move_key   = event.key
                    self._move_hold_timer = self._MOVE_HOLD_INITIAL
            elif event.type == pygame.KEYUP and event.key == self._held_move_key:
                self._held_move_key = None

        # Help catalog takes priority over all overlays (F1 always works)
        if self._help_open:
            for event in events:
                if event.type == pygame.MOUSEMOTION:
                    self.help_catalog.handle_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.help_catalog.handle_click(event.pos):
                        self._help_open = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F1 or self.help_catalog.handle_key(event.key):
                        self._help_open = False
            return

        # F1 opens help with a context-sensitive tab
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                if self._aim_overlay is not None:
                    self.help_catalog.open_tab(_TAB_AIMING)
                elif self._melee_overlay is not None:
                    self.help_catalog.open_tab(_TAB_MELEE)
                elif self._heal_overlay is not None:
                    self.help_catalog.open_tab(_TAB_HEALING)
                elif self._vault_overlay is not None:
                    self.help_catalog.open_tab(_TAB_VAULT)
                else:
                    self.help_catalog.open_tab(_TAB_EXPLORATION)
                self._help_open = True
                return

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

        # Vault overlay takes exclusive input while active
        if self._vault_overlay is not None:
            for event in events:
                self._vault_overlay.handle_event(event)
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
                elif event.type == pygame.MOUSEWHEEL:
                    self.cheat_menu.handle_scroll(event.y)
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

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self._cheat_menu_open = not self._cheat_menu_open
                    return
                if event.key == pygame.K_F10:
                    self._fov_debug_on = not self._fov_debug_on
                    bus.post(LogMessageEvent(
                        f"[debug] FOV/LOS overlay: {'ON' if self._fov_debug_on else 'OFF'}",
                        (220, 120, 220),
                    ))
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
                if event.key == pygame.K_p:
                    settings.HACK_WEAPON_USE_PNG = not settings.HACK_WEAPON_USE_PNG
                    return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                wp_r = self.hud.weapon_rect   if self.hud else None
                hl_r = self.hud.heal_rect     if self.hud else None
                hb_r = self.hud.help_btn_rect if self.hud else None
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
                if hb_r and hb_r.collidepoint(event.pos):
                    self.help_catalog.open_tab(_TAB_EXPLORATION)
                    self._help_open = True
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

    def _handle_inventory_input(self, events: list[pygame.event.Event]) -> None:
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
            if action == "help":
                self.help_catalog.open_tab(_TAB_ITEMS)
                self._help_open = True
                return
            if action is None:
                continue

            # Heal consumables route through the same flow as [H] — honours
            # use_heal_minigame / overheal threshold instead of flat-healing.
            if isinstance(action, UseItemAction):
                item = action.item
                if isinstance(item, Consumable) and item.heal_amount > 0:
                    if not action.validate(self.player, self.floor):
                        continue
                    self._inventory_open = False
                    self._launch_heal_for(item)
                    return

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

    def _handle_weapon_picker_input(self, events: list[pygame.event.Event]) -> None:
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

    def _handle_player_input(self, events: list[pygame.event.Event]) -> None:
        if self.alert_banner.is_blocking:
            return
        if self._elevator_phase is not None or self._arrival_phase is not None:
            return  # block all input during elevator animations
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
                        if container.is_objective:
                            self._launch_vault(container)
                        elif self.use_minigame:
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

            # Objective containers → vault drain minigame
            if isinstance(action, OpenContainerAction) and action.container.is_objective:
                self._launch_vault(action.container)
                break

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

            # Melee attack (from [F] key) — intercept for power-charge minigame
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
                bus.post(LogMessageEvent(t("log.room_encounter"), colour=(220, 80, 60)))
            self._had_visible_enemies = now_visible
            break

    # ------------------------------------------------------------------
    # Turn-advance helpers
    # ------------------------------------------------------------------

    _COMBAT_DELAY      = 0.14   # seconds to pause after player acts while enemies visible
    _ENEMY_INTER_DELAY = 0.08   # seconds between individual enemy turns (visual pacing)
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
            # No enemies on screen — process all remaining AI turns instantly.
            # Advance at least once: the player's action does not touch the
            # turn_manager index, so right now current_actor() is still the
            # player and a plain `while not is_player_turn()` loop would be
            # a no-op. Use do-while semantics.
            _safety = 256
            while _safety > 0:
                self.turn_manager.advance(self.floor, self.resolver)
                _safety -= 1
                if self.turn_manager.is_player_turn():
                    break
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
            # Entry elevator: show "no way back" and consume the keypress
            if self._adjacent_entry_elevator_pos() is not None:
                bus.post(LogMessageEvent(t("hint.elevator_no_return"), (160, 130, 90)))
                self.audio.play("action_denied")
                return None
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

        self._launch_heal_for(consumable)

    def _launch_heal_for(self, consumable) -> None:
        """Route a specific consumable through overheal confirm + minigame (or flat heal)."""
        assert self.player is not None
        missing = self.player.max_hp - self.player.hp
        if missing <= 0:
            bus.post(LogMessageEvent(t("log.full_hp"), (120, 120, 140)))
            self.audio.play("action_denied")
            return
        thr = self.heal_threshold_pct / 100.0
        if consumable.heal_amount * thr > missing:
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
            if abs(self.player.x - c.x) + abs(self.player.y - c.y) <= 1:
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

    def _adjacent_entry_elevator_pos(self) -> tuple[int, int] | None:
        """Return (x, y) of a cardinally adjacent ELEVATOR_ENTRY tile, or None."""
        if self.player is None or self.floor is None:
            return None
        for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = self.player.x + dx, self.player.y + dy
            if self.floor.dungeon_map.in_bounds(nx, ny):
                if self.floor.dungeon_map.get_type(nx, ny) == TileType.ELEVATOR_ENTRY:
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
            log.debug(f"Tutorial step '{step}' not shown (disabled or already seen)")
            return
        log.info(f"Tutorial step '{step}' enqueued")
        self._tutorial_queue.append(step)
        if not self._tutorial_open:
            self._drain_tutorial_queue()
        else:
            log.debug(f"Tutorial step '{step}' queued (tutorial already open)")

    def _drain_tutorial_queue(self) -> None:
        """Show the next queued step if nothing is currently displayed."""
        if not self._tutorial_open and self._tutorial_queue:
            step = self._tutorial_queue.pop(0)
            self._tutorial_open = True
            log.info(f"Showing tutorial step '{step}'")
            self.tutorial_overlay.show(step, on_close=self._on_tutorial_close)
        elif self._tutorial_open:
            log.debug("Tutorial already open, not draining queue")
        elif not self._tutorial_queue:
            log.debug("Tutorial queue empty")

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

        def on_cancel() -> None:
            self.music.resume()

        self.music.pause()

        from dungeoneer.minigame.hack_scene_grid import HackGridScene
        from dungeoneer.minigame.hack_grid_generator import HackGridParams
        params = HackGridParams.for_difficulty(self.difficulty)
        if self.heat_system is not None:
            modifier = self.heat_system.hack_time_modifier()
            params.time_limit = max(settings.HEAT_HACK_TIME_FLOOR,
                                    params.time_limit + modifier)
        self.app.scenes.push(HackGridScene(
            self.app, params=params, on_complete=on_complete, on_cancel=on_cancel
        ))

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
        self._maybe_show_tutorial("heat")

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
            bus.post(LogMessageEvent(t("log.room_encounter"), colour=(220, 80, 60)))
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
            bus.post(LogMessageEvent(t("log.room_encounter"), colour=(220, 80, 60)))
        self._had_visible_enemies = now_visible

    # ------------------------------------------------------------------
    # Vault drain minigame integration
    # ------------------------------------------------------------------

    def _launch_vault(self, container: "ContainerEntity") -> None:
        """Open the vault drain overlay for an objective container."""
        if self._vault_fully_drained:
            bus.post(LogMessageEvent(t("log.vault_empty"), (120, 100, 80)))
            return
        if self._vault_overlay is not None:
            return  # already open
        from dungeoneer.ai.states import CombatState
        if any(
            isinstance(a, Enemy) and isinstance(a.ai_brain.current_state, CombatState)
            for a in self.floor.actors
        ):
            bus.post(LogMessageEvent(t("log.vault_in_combat"), (200, 100, 60)))
            return

        self._held_move_key = None
        self._vault_container = container
        self._maybe_show_tutorial("vault")

        def on_complete(credits_this_session: int, fully_drained: bool) -> None:
            self._on_vault_complete(credits_this_session, fully_drained)

        from dungeoneer.minigame.vault_scene import VaultOverlay
        self._vault_overlay = VaultOverlay(
            total_credits=container.credits,
            credits_already_drained=self._vault_credits_banked,
            player=self.player,
            heat_system=self.heat_system,
            difficulty=self.difficulty,
            on_complete=on_complete,
            session_state=self._vault_session_state,
        )
        self.music.start_vault()

    def _on_vault_complete(self, credits_this_session: int, fully_drained: bool) -> None:
        if self._vault_overlay is not None:
            self._vault_session_state = self._vault_overlay.get_session_state()
        self._vault_overlay = None
        if credits_this_session > 0:
            self._vault_credits_banked += credits_this_session
            self.hud.vault_credits_banked = self._vault_credits_banked
            bus.post(LogMessageEvent(
                t("log.vault_drained").format(credits=credits_this_session),
                (80, 230, 160),
            ))
        if fully_drained:
            self._vault_fully_drained = True

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
            _cheat_factories = {
                "guard":        make_guard,
                "drone":        make_drone,
                "dog":          make_dog,
                "heavy":        make_heavy,
                "turret":       make_turret,
                "sniper_drone": make_sniper_drone,
                "riot_guard":   make_riot_guard,
            }
            factory = _cheat_factories.get(enemy_id, make_drone)
            enemy = factory(tx, ty)
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

        elif action.startswith("heat_level:"):
            level = int(action.split(":", 1)[1])
            if self.heat_system is not None:
                new_heat = (level - 1) * settings.HEAT_PER_LEVEL
                self.heat_system.set_heat(new_heat)
                from dungeoneer.systems.heat import LEVEL_NAMES
                bus.post(LogMessageEvent(f"[CHEAT] Heat → {LEVEL_NAMES[level]}", (80, 220, 120)))

        elif action == "vault:open":
            pos = self._cheat_find_spawn_pos()
            if pos is None:
                return
            tx, ty = pos
            vault = ContainerEntity(tx, ty, credits=300,
                                    is_objective=True, name=t("entity.corp_vault.name"))
            self.floor.add_container(vault)
            self._vault_session_state = None
            self._vault_credits_banked = 0
            self._vault_fully_drained = False
            self._cheat_menu_open = False
            self._launch_vault(vault)
            bus.post(LogMessageEvent("[CHEAT] vault spawned", (80, 220, 120)))

        elif action.startswith("vault:credits:"):
            amount = int(action.split(":")[-1])
            self._vault_credits_banked = 0
            self._vault_fully_drained = False
            self._vault_overlay = None
            self._vault_session_state = None
            # Spawn a fresh vault container so the player can open it
            pos = self._cheat_find_spawn_pos()
            if pos is None:
                return
            tx, ty = pos
            vault = ContainerEntity(tx, ty, credits=amount,
                                    is_objective=True, name=t("entity.corp_vault.name"))
            self.floor.add_container(vault)
            bus.post(LogMessageEvent(f"[CHEAT] vault credits set to {amount}", (80, 220, 120)))

        elif action == "vault:drain50":
            if self._vault_container is not None:
                self._vault_credits_banked = self._vault_container.credits // 2
                bus.post(LogMessageEvent("[CHEAT] vault drained 50%", (80, 220, 120)))
            else:
                bus.post(LogMessageEvent("[CHEAT] no vault container set", (180, 80, 80)))

        elif action == "vault:reset":
            self._vault_credits_banked = 0
            self._vault_fully_drained = False
            self._vault_overlay = None
            self._vault_container = None
            self._vault_session_state = None
            bus.post(LogMessageEvent("[CHEAT] vault state reset", (80, 220, 120)))

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

    def _on_turn_end_heat(self, _event: TurnEndEvent) -> None:
        """Add heat only when at least one enemy is in CombatState (active combat)."""
        if self.heat_system is None or self.floor is None:
            return
        from dungeoneer.ai.states import CombatState
        in_combat = any(
            isinstance(a, Enemy) and isinstance(a.ai_brain.current_state, CombatState)
            for a in self.floor.actors
        )
        if in_combat:
            self.heat_system.add_heat(settings.HEAT_COMBAT_ROUND)

    def _on_heat_level_up(self, event: HeatLevelUpEvent) -> None:
        """Spawn a patrol when heat crosses into a new level (levels 2–5)."""
        if self.player is None or self.floor is None or self._game_over:
            return

        # Force-close vault overlay — player can re-enter after combat
        if self._vault_overlay is not None:
            self._vault_overlay.force_close()

        if self.encounter_system is not None:
            self.encounter_system.spawn_patrol(self.player.x, self.player.y)

        from dungeoneer.systems.heat import LEVEL_NAMES
        lvl_name = LEVEL_NAMES[event.new_level]
        bus.post(LogMessageEvent(
            t("log.heat_level_up").format(level=lvl_name),
            (220, 100, 40),
        ))
        self.alert_banner.trigger()

    def _find_patrol_spawn(self) -> tuple[int, int] | None:
        """Find a free walkable tile 4–8 tiles from the player for a patrol spawn."""
        import random as _rnd
        from dungeoneer.combat.line_of_sight import has_los
        assert self.player is not None
        assert self.floor is not None
        px, py = self.player.x, self.player.y
        dm = self.floor.dungeon_map
        candidates: list[tuple[int, int]] = []
        for dy in range(-9, 10):
            for dx in range(-9, 10):
                tx, ty = px + dx, py + dy
                dist = abs(dx) + abs(dy)
                if dist < 4 or dist > 9:
                    continue
                if not dm.in_bounds(tx, ty) or not dm.is_walkable(tx, ty):
                    continue
                if self.floor.get_actor_at(tx, ty) is not None:
                    continue
                candidates.append((tx, ty))
        if not candidates:
            return None
        los_cands = [(x, y) for x, y in candidates if has_los(x, y, px, py, dm)]
        pool = los_cands if los_cands else candidates
        return _rnd.choice(pool)

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

    def _draw_fov_debug(self, screen: pygame.Surface) -> None:
        """F10 overlay: paint visibility/LOS mismatches and enemy reachability.

        Red tile  — in dungeon_map.visible[] but has_los(player→tile) is False
                    (i.e. player FOV believes the tile is visible, but the
                    shared LOS check disagrees).
        Cyan tile — has_los is True but visible[] is False (FOV undershoots LOS).
        Magenta X — living enemy whose tile is NOT LOS-reachable from the player
                    (helps spot bad enemy spawn placements).
        Yellow circle — origin used for the debug check (player position).
        """
        if self.player is None or self.floor is None:
            return
        from dungeoneer.combat.line_of_sight import has_los

        ts   = settings.TILE_SIZE
        cam  = self.renderer.camera
        dmap = self.floor.dungeon_map
        px, py = self.player.x, self.player.y

        red  = pygame.Surface((ts, ts), pygame.SRCALPHA)
        red.fill((255, 40, 40, 110))
        cyan = pygame.Surface((ts, ts), pygame.SRCALPHA)
        cyan.fill((40, 200, 255, 90))

        # Iterate only the on-screen tile rectangle for speed.
        x0 = max(0, cam.offset_x // ts - 1)
        y0 = max(0, cam.offset_y // ts - 1)
        x1 = min(dmap.width,  (cam.offset_x + settings.SCREEN_WIDTH ) // ts + 2)
        y1 = min(dmap.height, (cam.offset_y + settings.SCREEN_HEIGHT) // ts + 2)

        for y in range(y0, y1):
            for x in range(x0, x1):
                v = bool(dmap.visible[y, x])
                if not v and not dmap.explored[y, x]:
                    continue   # never-seen tiles can't carry useful debug info
                los = has_los(px, py, x, y, dmap)
                if v == los:
                    continue
                sx, sy = cam.world_to_screen(x, y)
                screen.blit(red if v and not los else cyan, (sx, sy))

        # Magenta X on enemies whose tile fails has_los from the player.
        for actor in self.floor.actors:
            if not isinstance(actor, Enemy) or not actor.alive:
                continue
            if has_los(px, py, actor.x, actor.y, dmap):
                continue
            sx, sy = cam.world_to_screen(actor.x, actor.y)
            pygame.draw.line(screen, (255, 0, 220), (sx + 2, sy + 2),
                             (sx + ts - 2, sy + ts - 2), 2)
            pygame.draw.line(screen, (255, 0, 220), (sx + ts - 2, sy + 2),
                             (sx + 2, sy + ts - 2), 2)

        sx, sy = cam.world_to_screen(px, py)
        pygame.draw.circle(screen, (255, 230, 60),
                           (sx + ts // 2, sy + ts // 2), ts // 3, 2)

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

        # Elevator animation state machine (descent)
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

        # Arrival animation state machine (ascending from elevator on a new floor)
        # Sequence: closed → open (hero inside) → hero steps out → closed
        if self._arrival_phase is not None:
            self._arrival_timer -= dt
            if self._arrival_timer <= 0.0:
                aex, aey = self._arrival_elevator_pos
                asx, asy = self._arrival_spawn_pos
                if self._arrival_phase == "arrive_closed":
                    # Open the elevator doors, reveal player inside
                    self.floor.dungeon_map.set_type(aex, aey, TileType.ELEVATOR_OPEN)
                    self.audio.play("elevator_open", 0.5)
                    self._arrival_phase = "arrive_open"
                    self._arrival_timer = 0.25
                elif self._arrival_phase == "arrive_open":
                    # Player steps out next to the elevator
                    self.player.x, self.player.y = asx, asy
                    self._arrival_phase = "arrive_exit"
                    self._arrival_timer = 0.35
                elif self._arrival_phase == "arrive_exit":
                    # Close the elevator doors
                    self.floor.dungeon_map.set_type(aex, aey, TileType.ELEVATOR_ENTRY)
                    self.audio.play("elevator_close", 0.5)
                    self._arrival_phase = "arrive_closing"
                    self._arrival_timer = 0.4
                elif self._arrival_phase == "arrive_closing":
                    # Animation done — recompute FOV from player's actual position
                    self._arrival_phase = None
                    self._arrival_elevator_pos = None
                    self._arrival_spawn_pos = None
                    compute_fov(self.player.x, self.player.y, self.floor.dungeon_map, rooms=self.floor.rooms)
                    self._maybe_show_tutorial("movement")

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

        if self._vault_overlay is not None and not self._tutorial_open:
            _vault_ov = self._vault_overlay
            _vault_ov.update(dt)
            if not _vault_ov.is_active:
                self._vault_overlay = None

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
                # If more enemy turns remain, pace them with a short inter-enemy delay.
                if not self.turn_manager.is_player_turn() and not self._game_over:
                    self._pending_advance = True
                    self._advance_timer   = self._ENEMY_INTER_DELAY

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
                    and self._vault_overlay is None
                    and self._elevator_phase is None
                    and self._arrival_phase is None
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
                                bus.post(LogMessageEvent(t("log.room_encounter"), colour=(220, 80, 60)))
                            self._had_visible_enemies = now_visible
                            self._move_hold_timer = self._MOVE_HOLD_REPEAT
                    else:
                        # Obstacle/enemy in the way — stop repeating until key is re-pressed
                        self._held_move_key = None

    def render(self, screen: pygame.Surface) -> None:
        if self.floor and self.player:
            hide_player = (
                self._elevator_phase == "closing"
                or self._arrival_phase == "arrive_closed"
            )
            self.renderer.draw(
                screen, self.floor, self.player,
                hud=self.hud,
                combat_log=self.combat_log,
                hide_player=hide_player,
            )
            if self._fov_debug_on:
                self._draw_fov_debug(screen)
            self.floating_nums.draw(screen, self.renderer.camera)
            self.alert_banner.draw(screen, self.renderer.camera, self.player.x, self.player.y)
            # Elevator / entry-elevator hints
            _no_overlay = (
                self._elevator_phase is None
                and self._arrival_phase is None
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
                and self._vault_overlay is None
            )
            _hint_text: str | None = None
            _hint_col: tuple = (220, 220, 100)
            if _no_overlay:
                if self._find_adjacent_container() is not None:
                    _hint_text = t("hint.container_open")
                    _hint_col  = (80, 200, 200)
                elif self._adjacent_elevator_pos() is not None:
                    if self.player and self.player.floor_depth == FLOORS_PER_RUN:
                        _hint_text = t("hint.elevator_extract")
                    else:
                        _hint_text = t("hint.elevator_descend")
                elif self._adjacent_entry_elevator_pos() is not None:
                    _hint_text = t("hint.elevator_no_return")
                    _hint_col  = (160, 130, 90)
            if _hint_text is not None:
                cam = self.renderer.camera
                ts  = settings.TILE_SIZE
                sx, sy = cam.world_to_screen(self.player.x, self.player.y)
                hint_surf = self._hint_font.render(_hint_text, True, _hint_col)
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
            # Vault overlay (centred panel, no scene push)
            if self._vault_overlay is not None:
                self._vault_overlay.render(screen)
            if self._inventory_open:
                self.inventory_ui.draw(screen, self.player)
            elif self._weapon_picker_open:
                self.weapon_picker.draw(screen, self.player)
            if self._help_open:
                self.help_catalog.draw(screen)
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
