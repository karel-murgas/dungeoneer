"""Grid-traversal hacking minigame scene — maze-grid variant.

Map is rendered as a network of lines (corridors) and circles (nodes),
like a PCB or circuit-board trace diagram.

Visual language
---------------
  Corridors   — thin lines connecting node circles
  Entry node  — cyan filled circle with ▶ arrow
  Loot node   — green filled circle with item icon
  Empty node  — small dim grey circle (junction / waypoint)
  Security    — hidden: looks IDENTICAL to an empty node
                revealed: red circle with X (replaces the empty look)
  Player      — pulsing yellow square that tracks the current position

Movement
--------
Only explicitly connected cells (via the `connections` graph) can be
traversed.  Corridor cells carry direction from node to node; you cannot
jump between two parallel corridors even if they're physically adjacent.
"""
from __future__ import annotations

import math
import os
import random
from enum import auto, Enum
from typing import Callable, List, Optional, Tuple, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.core.i18n import t
from dungeoneer.minigame.hack_node import LootKind, SecurityKind
from dungeoneer.minigame.hack_grid_map import GridCell, GridCellType, HackGridMap, Pos
from dungeoneer.minigame.hack_grid_generator import HackGridParams, generate_grid_map
from dungeoneer.minigame.hack_audio import HackAudio
from dungeoneer.rendering import procedural_sprites

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp
    from dungeoneer.items.item import Item


# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
_BG            = (4,    8,  18)
_GRID_DOT      = (14,  26,  42)
_PANEL_BG      = (6,   12,  22)

_NEON_CYAN     = (0,   230, 220)
_NEON_GREEN    = (0,   220,  80)
_NEON_RED      = (220,  40,  80)
_NEON_ORANGE   = (220, 140,   0)
_NEON_YELLOW   = (200, 220,  60)

_TEXT          = (160, 220, 200)
_TEXT_DIM      = (60,  100,  80)

_COL_TIMER_HI  = _NEON_GREEN
_COL_TIMER_MID = _NEON_ORANGE
_COL_TIMER_LO  = _NEON_RED

# Network colours
_COL_WIRE      = (22,   55,  78)    # normal corridor line
_COL_WIRE_LIT  = (0,   160, 180)    # corridor adjacent to player
_COL_NODE_EMPTY = (38,  60,  76)    # empty / junction node fill
_COL_NODE_EMPTY_RIM = (55, 90, 110) # rim of empty node


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
_HEADER_H = 64
_FOOTER_H = 76


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class _State(Enum):
    IDLE    = auto()
    MOVING  = auto()
    HACKING = auto()
    DONE    = auto()


_DIR_MAP: dict[int, Pos] = {
    pygame.K_w:     (0, -1),
    pygame.K_UP:    (0, -1),
    pygame.K_s:     (0,  1),
    pygame.K_DOWN:  (0,  1),
    pygame.K_a:     (-1, 0),
    pygame.K_LEFT:  (-1, 0),
    pygame.K_d:     (1,  0),
    pygame.K_RIGHT: (1,  0),
}

_ARROW_CHARS: dict[Pos, str] = {
    (0, -1): "↑",
    (0,  1): "↓",
    (-1, 0): "←",
    (1,  0): "→",
}


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------

def _make_loot_item(kind: LootKind) -> Optional["Item"]:
    from dungeoneer.items.ammo import make_9mm_ammo, make_rifle_ammo, make_shotgun_ammo
    from dungeoneer.items.consumable import make_stim_pack, make_medkit
    from dungeoneer.items.weapon import make_shotgun, make_rifle, make_smg
    from dungeoneer.items.armor import make_basic_armor

    if kind == LootKind.AMMO:         return make_9mm_ammo(8)
    if kind == LootKind.RIFLE_AMMO:   return make_rifle_ammo(3)
    if kind == LootKind.SHOTGUN_AMMO: return make_shotgun_ammo(4)
    if kind == LootKind.HEAL:         return make_stim_pack()
    if kind == LootKind.MEDKIT:       return make_medkit()
    if kind == LootKind.WEAPON:       return random.choice([make_shotgun, make_rifle, make_smg])()
    if kind == LootKind.ARMOR:        return make_basic_armor()
    return None


def _draw_corner_bracket(
    screen: pygame.Surface,
    x: int, y: int,
    arm: int, thickness: int,
    color: tuple,
    width: int,
    flip_x: bool = False,
    flip_y: bool = False,
) -> None:
    dx = -1 if flip_x else 1
    dy = -1 if flip_y else 1
    pygame.draw.line(screen, color, (x, y), (x + dx * arm, y), width)
    pygame.draw.line(screen, color, (x, y), (x, y + dy * thickness), width)


def _draw_glow_circle(
    screen: pygame.Surface,
    color: tuple,
    cx: int, cy: int,
    radius: int,
    layers: int = 3,
    max_alpha: int = 80,
) -> None:
    size   = (radius + layers * 8) * 2
    surf   = pygame.Surface((size, size), pygame.SRCALPHA)
    center = size // 2
    for i in range(layers, 0, -1):
        r     = radius + i * 8
        alpha = max_alpha * i // layers
        pygame.draw.circle(surf, (*color, alpha), (center, center), r)
    screen.blit(surf, (cx - center, cy - center))


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------

class HackGridScene(Scene):
    """Maze-grid hacking minigame: move cell-by-cell through a wire network."""

    def __init__(
        self,
        app: "GameApp",
        params: Optional[HackGridParams] = None,
        on_complete: Optional[Callable[[bool, List["Item"], int], None]] = None,
    ) -> None:
        super().__init__(app)
        self._params      = params or HackGridParams()
        self._on_complete = on_complete or (lambda *_: None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        p = self._params
        self._grid_map: HackGridMap = generate_grid_map(p)
        self._player_pos: Pos       = self._grid_map.entry_pos
        self._prev_pos:   Pos       = self._grid_map.entry_pos
        self._state:     _State     = _State.IDLE

        self._time_remaining: float = p.time_limit
        self._move_timer:     float = 0.0
        self._hack_timer:     float = 0.0
        self._pending_pos:    Pos   = self._player_pos
        self._done_timer:     float = 0.0
        self._done_success:   bool  = False

        self._anim_time:     float = 0.0
        self._tick_cooldown: float = 0.0
        self._timer_started: bool  = False

        self._result_items:   List["Item"] = []
        self._result_credits: int          = 0

        self._sec_overlay:  dict | None = None
        self._loot_overlay: dict | None = None

        # Auto-movement: keep going in a direction until node/intersection
        self._auto_dir:      Optional[Pos] = None   # current auto direction
        self._queued_dir:    Optional[Pos] = None   # direction pressed during MOVING
        self._last_node_pos: Pos           = self._grid_map.entry_pos  # for BLOCKED rollback

        self._status: str = t("hack.status.initial")
        self._log:    str = ""
        self._show_help:  bool = False

        # Cache which connections to draw (avoid redrawing both directions)
        self._wire_pairs: List[Tuple[Pos, Pos]] = []
        self._rebuild_wire_pairs()

        # Audio
        self._audio = HackAudio()
        self._audio.build()
        _music_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "audio", "music", "hacking.mp3"
        )
        pygame.mixer.music.load(_music_path)
        pygame.mixer.music.set_volume(0.30)
        pygame.mixer.music.play(-1)

        # Fonts
        self._font_lg  = pygame.font.SysFont("consolas", 22, bold=True)
        self._font_md  = pygame.font.SysFont("consolas", 16)
        self._font_sm  = pygame.font.SysFont("consolas", 13)
        self._font_xs  = pygame.font.SysFont("consolas", 11, bold=True)
        self._font_ico = pygame.font.SysFont("consolas", 12, bold=True)
        # Pre-scale item sprites for loot node icons
        self._item_sprites: dict[str, pygame.Surface] = {}
        for _key in (
            "item_loot_ammo", "item_loot_consumable",
            "item_loot_ranged", "item_loot_armor", "item_loot",
            "item_hack_credits", "item_hack_bonus_time", "item_hack_mystery",
        ):
            _raw = procedural_sprites.get(_key)
            if _raw is not None:
                self._item_sprites[_key] = _raw   # will be scaled at draw time

    def on_exit(self) -> None:
        pygame.mixer.music.fadeout(300)

    def _rebuild_wire_pairs(self) -> None:
        """Collect unique (a, b) edge pairs where a < b for single-pass drawing."""
        seen: set[frozenset] = set()
        self._wire_pairs = []
        for pos, nbs in self._grid_map.connections.items():
            for nb in nbs:
                key = frozenset({pos, nb})
                if key not in seen:
                    seen.add(key)
                    # Always store (smaller, larger) so a < b
                    self._wire_pairs.append(
                        (pos, nb) if pos < nb else (nb, pos)
                    )

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        if self._state == _State.DONE:
            return
        if self._sec_overlay is not None:
            return

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._state == _State.IDLE:
                    self._handle_click(event.pos)
                continue

            if event.type != pygame.KEYDOWN:
                continue
            key = event.key

            if key == pygame.K_F1:
                self._show_help = not self._show_help
                continue

            if key in (pygame.K_q, pygame.K_ESCAPE):
                if self._state == _State.HACKING:
                    self._state  = _State.IDLE
                    self._status = t("hack.status.cancelled")
                elif self._state == _State.IDLE:
                    self._finish(success=True)
                continue

            direction = _DIR_MAP.get(key)
            if direction is not None:
                if self._state == _State.IDLE:
                    self._try_start_auto(direction)
                elif self._state == _State.MOVING:
                    # Queue for application at next _arrive()
                    self._queued_dir = direction

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        dt = min(dt, 0.1)
        self._anim_time += dt

        for cell in self._grid_map.cells.values():
            if cell.flash_timer > 0:
                cell.flash_timer = max(0.0, cell.flash_timer - dt)

        if self._state == _State.DONE:
            self._done_timer -= dt
            if self._done_timer <= 0:
                self._on_complete(
                    self._done_success, self._result_items, self._result_credits
                )
                self.app.scenes.pop()
            return

        if self._sec_overlay is not None:
            self._sec_overlay["timer"] -= dt
            if self._sec_overlay["timer"] <= 0:
                self._sec_overlay = None

        if self._loot_overlay is not None:
            self._loot_overlay["timer"] -= dt
            if self._loot_overlay["timer"] <= 0:
                self._loot_overlay = None

        if self._timer_started and not self._show_help and self._sec_overlay is None:
            self._time_remaining = max(0.0, self._time_remaining - dt)
            if self._time_remaining == 0.0:
                self._finish(success=False)
                return

        if self._timer_started and not self._show_help and self._time_remaining <= 3.0:
            self._tick_cooldown -= dt
            if self._tick_cooldown <= 0:
                self._audio.play("timer_tick", volume=0.6)
                self._tick_cooldown = 0.5

        if self._state == _State.MOVING:
            self._move_timer -= dt
            if self._move_timer <= 0:
                self._arrive(self._pending_pos)

        elif self._state == _State.HACKING:
            self._hack_timer -= dt
            if self._hack_timer <= 0:
                self._collect_loot(self._player_pos)
                if self._state != _State.DONE:
                    self._state = _State.IDLE

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(_BG)
        self._draw_bg_grid(screen)

        panel = self._panel_rect()
        self._draw_header(screen)
        self._draw_network(screen, panel)
        self._draw_footer(screen)

        if self._loot_overlay is not None:
            self._draw_sec_overlay(screen, self._loot_overlay)
        elif self._sec_overlay is not None:
            self._draw_sec_overlay(screen, self._sec_overlay)

        if self._state == _State.DONE:
            self._draw_result_overlay(screen)

        if self._show_help:
            self._draw_help_overlay(screen)

    # ------------------------------------------------------------------
    # State machine
    # ------------------------------------------------------------------

    def _compute_lit_cells(self) -> set[Pos]:
        """
        Follow each corridor outward from the player until a node is reached.
        Returns all physical cells that should be highlighted (player + all
        corridor cells + the first node in each direction).
        """
        gm     = self._grid_map
        player = self._player_pos
        lit: set[Pos] = {player}
        for start_nb in gm.connections.get(player, set()):
            prev, cur = player, start_nb
            while True:
                lit.add(cur)
                if cur in gm.node_positions:
                    break   # stop at the neighboring node (inclusive)
                nexts = [n for n in gm.connections.get(cur, set()) if n != prev]
                if not nexts:
                    break   # dead-end corridor
                prev, cur = cur, nexts[0]
        return lit

    def _try_start_auto(self, direction: Pos) -> None:
        """Begin auto-movement in *direction* from current position."""
        dc, dr = direction
        target: Pos = (self._player_pos[0] + dc, self._player_pos[1] + dr)
        if target in self._grid_map.connections.get(self._player_pos, set()):
            self._auto_dir   = direction
            self._queued_dir = None
            self._start_move(target)
        else:
            self._auto_dir   = None
            self._queued_dir = None

    def _try_continue_auto(self) -> None:
        """Called after arriving at a plain PATH cell — continue if appropriate."""
        # Apply queued direction change first
        if self._queued_dir is not None:
            self._try_start_auto(self._queued_dir)
            return

        if self._auto_dir is None:
            return

        # Stop at nodes (ENTRY, EMPTY, LOOT, SECURITY) — player decides next step
        if self._player_pos in self._grid_map.node_positions:
            self._auto_dir = None
            return

        # Continue straight
        dc, dr = self._auto_dir
        target: Pos = (self._player_pos[0] + dc, self._player_pos[1] + dr)
        if target in self._grid_map.connections.get(self._player_pos, set()):
            self._start_move(target)
        else:
            self._auto_dir = None

    def _handle_click(self, screen_pos: Tuple[int, int]) -> None:
        """Navigate to the adjacent node under the mouse cursor (if reachable)."""
        panel   = self._panel_rect()
        clicked = self._screen_to_cell(screen_pos[0], screen_pos[1], panel)
        if clicked is None:
            return
        direction = self._reachable_node_dirs().get(clicked)
        if direction is not None:
            self._try_start_auto(direction)

    def _screen_to_cell(self, mx: int, my: int, panel: pygame.Rect) -> Optional[Pos]:
        """Convert screen pixel position to the nearest physical grid cell."""
        gm = self._grid_map
        pc = gm.phys_cols - 1
        pr = gm.phys_rows - 1
        if pc == 0 or pr == 0:
            return None
        col = round((mx - panel.x) * pc / panel.width)
        row = round((my - panel.y) * pr / panel.height)
        if 0 <= col < gm.phys_cols and 0 <= row < gm.phys_rows:
            return (col, row)
        return None

    def _reachable_node_dirs(self) -> dict[Pos, Pos]:
        """Return {node_pos: first_step_direction} for every adjacent reachable node."""
        gm     = self._grid_map
        player = self._player_pos
        result: dict[Pos, Pos] = {}
        for start_nb in gm.connections.get(player, set()):
            direction: Pos = (start_nb[0] - player[0], start_nb[1] - player[1])
            prev, cur = player, start_nb
            while True:
                if cur in gm.node_positions:
                    result[cur] = direction
                    break
                nexts = [n for n in gm.connections.get(cur, set()) if n != prev]
                if not nexts:
                    break
                prev, cur = cur, nexts[0]
        return result

    def _start_move(self, target: Pos) -> None:
        self._timer_started = True
        self._prev_pos      = self._player_pos
        self._pending_pos   = target
        self._move_timer    = self._params.step_time
        self._state         = _State.MOVING
        self._audio.play("move", volume=0.35)

    def _arrive(self, target: Pos) -> None:
        self._player_pos = target
        # Track last safe node for BLOCKED rollback — skip live (unhacked) security nodes
        if target in self._grid_map.node_positions:
            _c = self._grid_map.cells.get(target)
            _live_sec = (
                _c is not None
                and _c.cell_type == GridCellType.SECURITY
                and not _c.hacked
            )
            if not _live_sec:
                self._last_node_pos = target
        cell = self._grid_map.cells.get(target)
        if cell is None:
            self._state  = _State.IDLE
            self._status = t("hack.status.navigate")
            return

        if (
            cell.cell_type == GridCellType.SECURITY
            and not cell.hacked
            and cell.active
        ):
            self._auto_dir   = None
            self._queued_dir = None
            cell.revealed = True
            self._apply_security(cell)
            cell.hacked = True

        elif (
            cell.cell_type == GridCellType.LOOT
            and not cell.hacked
            and cell.active
        ):
            self._auto_dir   = None
            self._queued_dir = None
            self._hack_timer = self._params.hack_time
            self._state      = _State.HACKING
            _loot_key = f"hack.loot.{cell.loot_kind.name.lower()}"
            self._status = t("hack.status.extracting").format(kind=t(_loot_key))
            self._audio.play("hack_start", volume=0.7)

        else:
            self._state  = _State.IDLE
            self._status = t("hack.status.navigate")
            self._try_continue_auto()

    def _apply_security(self, cell: GridCell) -> None:
        kind = cell.security_kind
        self._audio.play("ice", volume=0.75)

        if kind == SecurityKind.TIME_PENALTY:
            self._time_remaining = max(0.0, self._time_remaining - 3.0)
            self._status = t("hack.status.time_penalty")
            self._log    = "[-3s]"
            self._state  = _State.IDLE
            self._sec_overlay = {
                "timer": 1.6,
                "text":  t("hack.overlay.time_title"),
                "sub":   t("hack.overlay.time_sub"),
                "color": _NEON_RED,
            }

        elif kind == SecurityKind.DESTROY_LOOT:
            victims = [
                self._grid_map.cells[p]
                for p in self._grid_map.loot_positions
                if p in self._grid_map.cells
                and self._grid_map.cells[p].active
                and not self._grid_map.cells[p].hacked
                and (self._grid_map.cells[p].col, self._grid_map.cells[p].row)
                    != (cell.col, cell.row)
            ]
            if victims:
                v = random.choice(victims)
                v.active = False
                self._status = t("hack.status.cache_destroyed")
                self._sec_overlay = {
                    "timer": 1.6,
                    "text":  t("hack.overlay.cache_title"),
                    "sub":   t("hack.overlay.cache_sub"),
                    "color": _NEON_RED,
                }
            else:
                self._status = t("hack.status.no_targets")
                self._sec_overlay = {
                    "timer": 1.2,
                    "text":  t("hack.overlay.notgt_title"),
                    "sub":   t("hack.overlay.notgt_sub"),
                    "color": _NEON_RED,
                }
            self._state = _State.IDLE
            if self._grid_map.active_loot_remaining() == 0:
                self._finish(success=True)

        elif kind == SecurityKind.BLOCKED:
            self._player_pos = self._last_node_pos
            cell.flash_timer = 0.6
            self._status = t("hack.status.access_denied")
            self._state  = _State.IDLE
            self._sec_overlay = {
                "timer": 1.4,
                "text":  t("hack.overlay.denied_title"),
                "sub":   t("hack.overlay.denied_sub"),
                "color": _NEON_RED,
            }

    def _collect_loot(self, pos: Pos) -> None:
        cell = self._grid_map.cells.get(pos)
        if cell is None:
            return
        cell.hacked = True
        kind = cell.loot_kind

        # Resolve MYSTERY to a random non-mystery kind
        if kind == LootKind.MYSTERY:
            kind = random.choice([k for k in LootKind if k != LootKind.MYSTERY])
            cell.loot_kind = kind   # update cell so display shows the result

        if kind == LootKind.BONUS_TIME:
            self._time_remaining += 3.0
            self._status = t("hack.status.bonus_time")
            self._log    = "[+3s]"
            self._audio.play("bonus_time", volume=0.7)
            self._loot_overlay = {
                "timer": 1.4,
                "text":  t("hack.overlay.bonus_title"),
                "sub":   t("hack.overlay.bonus_sub"),
                "color": (80, 180, 255),
            }
        elif kind == LootKind.CREDITS:
            amount = random.randint(10, 40)
            self._result_credits += amount
            self._status = t("hack.status.credits").format(n=amount)
            self._log    = f"[+¥{amount}]"
            self._audio.play("hack_complete", volume=0.7)
            self._loot_overlay = {
                "timer": 1.4,
                "text":  t("hack.overlay.credits_title"),
                "sub":   f"+¥{amount}",
                "color": _NEON_GREEN,
            }
        else:
            item = _make_loot_item(kind)
            if item is not None:
                self._result_items.append(item)
                self._status = t("hack.status.extracted").format(item=item.name)
                self._log    = f"[{item.name}]"
                self._loot_overlay = {
                    "timer": 1.4,
                    "text":  t("hack.overlay.data_title"),
                    "sub":   item.name.upper(),
                    "color": _NEON_GREEN,
                }
            self._audio.play("hack_complete", volume=0.7)

        if self._grid_map.active_loot_remaining() == 0:
            self._finish(success=True)

    def _finish(self, success: bool) -> None:
        self._done_success = success
        self._done_timer   = 2.2
        self._state        = _State.DONE
        if not success:
            self._result_items   = []
            self._result_credits = 0
            self._audio.play("fail", volume=0.8)
        else:
            self._audio.play("success", volume=0.8)

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    def _panel_rect(self) -> pygame.Rect:
        sw, sh = self.app.screen.get_size()
        m = 20
        return pygame.Rect(m, _HEADER_H + m, sw - 2 * m, sh - _HEADER_H - _FOOTER_H - 2 * m)

    def _cell_center(self, col: int, row: int, panel: pygame.Rect) -> Tuple[int, int]:
        """Map physical grid coordinates to screen pixels."""
        gm = self._grid_map
        # Spread node positions evenly across the panel
        pc = gm.phys_cols - 1  # max physical column index
        pr = gm.phys_rows - 1
        x = panel.x + int(col * panel.width  / pc)
        y = panel.y + int(row * panel.height / pr)
        return x, y

    def _node_radius(self, panel: pygame.Rect) -> int:
        """Radius of a node circle in pixels."""
        gm = self._grid_map
        # Spacing between adjacent nodes = 2 physical units
        spacing_x = panel.width  / (gm.logical_cols - 1)
        spacing_y = panel.height / (gm.logical_rows - 1)
        return max(10, int(min(spacing_x, spacing_y) * 0.30))

    def _lerp_color(self, a: tuple, b: tuple, t: float) -> tuple:
        t = max(0.0, min(1.0, t))
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _timer_color(self) -> tuple:
        ratio = self._time_remaining / self._params.time_limit
        if ratio > 0.5:
            return self._lerp_color(_COL_TIMER_MID, _COL_TIMER_HI, (ratio - 0.5) * 2)
        if ratio > 0.25:
            return self._lerp_color(_COL_TIMER_LO, _COL_TIMER_MID, (ratio - 0.25) * 4)
        return _COL_TIMER_LO

    # ------------------------------------------------------------------
    # Draw — background dot grid
    # ------------------------------------------------------------------

    def _draw_bg_grid(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        step = 32
        for x in range(0, sw + step, step):
            for y in range(0, sh + step, step):
                pygame.draw.circle(screen, _GRID_DOT, (x, y), 1)

    # ------------------------------------------------------------------
    # Draw — header (same chrome as classic)
    # ------------------------------------------------------------------

    def _draw_header(self, screen: pygame.Surface) -> None:
        sw = screen.get_width()
        pygame.draw.rect(screen, _PANEL_BG, (0, 0, sw, _HEADER_H))
        pygame.draw.line(screen, _NEON_CYAN,    (0, _HEADER_H - 1), (sw, _HEADER_H - 1), 1)
        pygame.draw.line(screen, (*_NEON_CYAN, 40), (0, _HEADER_H - 3), (sw, _HEADER_H - 3), 1)
        _draw_corner_bracket(screen, 8, 8, 40, 14, _NEON_CYAN, 1)

        title_surf = self._font_lg.render(t("hack.header.title"), True, _NEON_CYAN)
        screen.blit(title_surf, (28, 20))
        if int(self._anim_time * 2) % 2 == 0:
            screen.blit(self._font_lg.render("_", True, _NEON_CYAN),
                        (28 + title_surf.get_width() + 6, 20))

        if self._state == _State.HACKING:
            esc_text, esc_color = t("hack.header.esc_cancel"), _NEON_ORANGE
        elif not self._timer_started:
            esc_text, esc_color = t("hack.header.move_start"), _NEON_YELLOW
        else:
            esc_text, esc_color = t("hack.header.esc_abort"), _TEXT_DIM
        es = self._font_md.render(esc_text, True, esc_color)
        screen.blit(es, (sw // 2 - es.get_width() // 2, 22))

        t_color = _TEXT_DIM if not self._timer_started else self._timer_color()
        ts = self._font_lg.render(f"{self._time_remaining:5.1f}s", True, t_color)
        screen.blit(ts, (sw - ts.get_width() - 14, 18))

        bar_x, bar_w, bar_h = 6, sw - 12, 5
        bar_y = _HEADER_H - bar_h - 2
        if not self._timer_started:
            alpha = int(120 + 80 * math.sin(self._anim_time * 3.0))
            bsurf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bsurf.fill((*_TEXT_DIM, alpha))
            screen.blit(bsurf, (bar_x, bar_y))
        else:
            ratio  = self._time_remaining / self._params.time_limit
            fill_w = int(bar_w * ratio)
            pygame.draw.rect(screen, (14, 22, 32), (bar_x, bar_y, bar_w, bar_h))
            if fill_w > 0:
                pygame.draw.rect(screen, t_color, (bar_x, bar_y, fill_w, bar_h))

    # ------------------------------------------------------------------
    # Draw — footer (same chrome as classic)
    # ------------------------------------------------------------------

    def _draw_footer(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        fy = sh - _FOOTER_H
        pygame.draw.rect(screen, _PANEL_BG, (0, fy, sw, _FOOTER_H))
        pygame.draw.line(screen, _NEON_CYAN,    (0, fy), (sw, fy), 1)
        pygame.draw.line(screen, (*_NEON_CYAN, 40), (0, fy + 2), (sw, fy + 2), 1)

        prefix = self._font_md.render(">> ", True, _NEON_CYAN)
        screen.blit(prefix, (14, fy + 12))
        screen.blit(self._font_md.render(self._status, True, _TEXT),
                    (14 + prefix.get_width(), fy + 12))
        if self._log:
            screen.blit(self._font_sm.render(self._log, True, _NEON_GREEN),
                        (14, fy + 38))

        hint_s = self._font_xs.render(t("hack.footer.hint"), True, _TEXT_DIM)
        screen.blit(hint_s, (sw - hint_s.get_width() - 14,
                              fy + _FOOTER_H - hint_s.get_height() - 10))

        n_hacked = sum(
            1 for p in self._grid_map.loot_positions
            if p in self._grid_map.cells and self._grid_map.cells[p].hacked
        )
        n_active = sum(
            1 for p in self._grid_map.loot_positions
            if p in self._grid_map.cells
            and self._grid_map.cells[p].active
            and not self._grid_map.cells[p].hacked
        )
        counter = t("hack.footer.counter").format(n=n_hacked, total=n_hacked + n_active)
        cs = self._font_sm.render(counter, True, _NEON_GREEN if n_hacked > 0 else _TEXT_DIM)
        screen.blit(cs, (sw - cs.get_width() - 14, fy + 12))

    # ------------------------------------------------------------------
    # Draw — main network
    # ------------------------------------------------------------------

    def _draw_network(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        gm      = self._grid_map
        player  = self._player_pos
        node_r  = self._node_radius(panel)

        # Panel background + corner brackets
        pygame.draw.rect(screen, _PANEL_BG, panel)
        _draw_corner_bracket(screen, panel.x,     panel.y,      50, 16, _NEON_CYAN, 1)
        _draw_corner_bracket(screen, panel.right,  panel.y,      50, 16, _NEON_CYAN, 1, flip_x=True)
        _draw_corner_bracket(screen, panel.x,     panel.bottom,  50, 16, _NEON_CYAN, 1, flip_y=True)
        _draw_corner_bracket(screen, panel.right,  panel.bottom, 50, 16, _NEON_CYAN, 1, flip_x=True, flip_y=True)

        # Scan line animation
        scan_y = int(panel.y + (self._anim_time * 60) % panel.height)
        ssurf = pygame.Surface((panel.width, 2), pygame.SRCALPHA)
        ssurf.fill((*_NEON_CYAN, 16))
        screen.blit(ssurf, (panel.x, scan_y))

        # Cells on lit paths (player → all neighboring nodes, through corridors)
        lit_cells       = self._compute_lit_cells()
        player_neighbors: set[Pos] = set(gm.neighbors(player[0], player[1]))

        # ------------------------------------------------------------------
        # 1. Corridor LINES
        # ------------------------------------------------------------------
        for a, b in self._wire_pairs:
            ax, ay = self._cell_center(a[0], a[1], panel)
            bx, by = self._cell_center(b[0], b[1], panel)

            # A wire is "lit" if both endpoints are on lit paths from player
            is_lit = (a in lit_cells and b in lit_cells)

            pygame.draw.line(
                screen,
                _COL_WIRE_LIT if is_lit else _COL_WIRE,
                (ax, ay), (bx, by),
                2 if is_lit else 1,
            )

            # Animated data packet along lit edges — always travels away from player
            if is_lit:
                da = abs(a[0] - player[0]) + abs(a[1] - player[1])
                db = abs(b[0] - player[0]) + abs(b[1] - player[1])
                if db < da:
                    ax, ay, bx, by = bx, by, ax, ay
                t_packet = (self._anim_time * 1.8) % 1.0
                px = int(ax + (bx - ax) * t_packet)
                py = int(ay + (by - ay) * t_packet)
                pygame.draw.circle(screen, _NEON_CYAN, (px, py), 2)

        # ------------------------------------------------------------------
        # 2. Node SQUARES
        # ------------------------------------------------------------------
        for pos in gm.node_positions:
            cell = gm.cells.get(pos)
            if cell is None:
                continue
            cx, cy = self._cell_center(pos[0], pos[1], panel)
            is_player   = (pos == player)
            is_adjacent = pos in player_neighbors and not is_player
            self._draw_node_circle(screen, cell, cx, cy, node_r, is_player, is_adjacent, panel)

        # ------------------------------------------------------------------
        # 4. WASD direction arrows (only in IDLE, overlaid near player)
        # ------------------------------------------------------------------
        if self._state == _State.IDLE:
            px, py = self._cell_center(player[0], player[1], panel)
            for (dc, dr), char in _ARROW_CHARS.items():
                nb: Pos = (player[0] + dc, player[1] + dr)
                if nb in player_neighbors:
                    # Position arrow halfway between player cell and neighbor
                    nbx, nby = self._cell_center(nb[0], nb[1], panel)
                    hx = int((px + nbx) / 2)
                    hy = int((py + nby) / 2)
                    asurf = self._font_xs.render(char, True, _NEON_YELLOW)
                    screen.blit(asurf, (hx - asurf.get_width() // 2,
                                        hy - asurf.get_height() // 2))

        # ------------------------------------------------------------------
        # 5. Moving dot (interpolated between cells)
        # ------------------------------------------------------------------
        if self._state == _State.MOVING and self._params.step_time > 0:
            progress = 1.0 - self._move_timer / self._params.step_time
            sx, sy = self._cell_center(self._prev_pos[0],    self._prev_pos[1],    panel)
            ex, ey = self._cell_center(self._pending_pos[0], self._pending_pos[1], panel)
            mx = int(sx + (ex - sx) * progress)
            my = int(sy + (ey - sy) * progress)
            _draw_glow_circle(screen, _NEON_YELLOW, mx, my, 5, layers=2, max_alpha=100)
            pygame.draw.circle(screen, _NEON_YELLOW, (mx, my), 4)

        # ------------------------------------------------------------------
        # 6. Player square (drawn on top of everything, including nodes)
        # ------------------------------------------------------------------
        self._draw_player(screen, panel, node_r)

        # ------------------------------------------------------------------
        # 7. Hack progress bar (below current loot node)
        # ------------------------------------------------------------------
        if self._state == _State.HACKING:
            hcell = gm.cells.get(self._player_pos)
            if hcell and hcell.cell_type == GridCellType.LOOT:
                hcx, hcy = self._cell_center(self._player_pos[0], self._player_pos[1], panel)
                ratio  = 1.0 - self._hack_timer / self._params.hack_time
                bw, bh = node_r * 2 + 8, 5
                bx = hcx - bw // 2
                by = hcy + node_r + 6
                pygame.draw.rect(screen, (16, 28, 38), (bx, by, bw, bh))
                fw = int(bw * ratio)
                if fw > 0:
                    pygame.draw.rect(screen, _NEON_GREEN, (bx, by, fw, bh))
                pygame.draw.rect(screen, _NEON_GREEN, (bx, by, bw, bh), 1)

    def _draw_node_circle(
        self,
        screen: pygame.Surface,
        cell: GridCell,
        cx: int, cy: int,
        node_r: int,
        is_player: bool,
        is_adjacent: bool,
        panel: pygame.Rect,
    ) -> None:
        ct = cell.cell_type

        # Determine visual type
        # Security hidden looks IDENTICAL to EMPTY (that's the whole point)
        if ct == GridCellType.SECURITY and not cell.revealed:
            visual = "empty"
        elif ct == GridCellType.SECURITY and cell.revealed:
            visual = "security_revealed"
        elif ct == GridCellType.LOOT and not cell.hacked:
            visual = "loot"
        elif ct == GridCellType.LOOT and cell.hacked:
            visual = "loot_done"
        elif ct == GridCellType.LOOT and not cell.active:
            visual = "loot_destroyed"
        elif ct == GridCellType.ENTRY:
            visual = "entry"
        else:
            visual = "empty"   # EMPTY, or destroyed loot

        # Override: destroyed loot shows a distinct ghosted state
        if ct == GridCellType.LOOT and not cell.active:
            visual = "loot_destroyed"

        # ---------------------------------------------------------------
        # Square geometry helpers
        # ---------------------------------------------------------------
        nr      = node_r                          # half-size of full node
        sm      = max(4, node_r - 4)              # half-size of small (empty) node
        rect    = pygame.Rect(cx - nr, cy - nr, nr * 2, nr * 2)
        sm_rect = pygame.Rect(cx - sm, cy - sm, sm * 2, sm * 2)

        # ---------------------------------------------------------------
        # Body — all nodes are now SQUARES
        # ---------------------------------------------------------------
        if visual == "entry":
            pygame.draw.rect(screen, (0, 55, 68), rect)
            pygame.draw.rect(screen, _NEON_CYAN, rect, 2)
            # Right-pointing triangle drawn as a polygon (font ▶ unreliable)
            ar = max(4, nr - 5)
            pygame.draw.polygon(screen, _NEON_CYAN, [
                (cx - ar * 2 // 3, cy - ar),
                (cx + ar,          cy),
                (cx - ar * 2 // 3, cy + ar),
            ])

        elif visual == "loot":
            fill = (14, 72, 28) if is_adjacent else (10, 55, 20)
            rim_w = max(2, int(2 + math.sin(self._anim_time * 8))) \
                if (is_player and self._state == _State.HACKING) else 2
            pygame.draw.rect(screen, fill, rect)
            pygame.draw.rect(screen, _NEON_GREEN, rect, rim_w)
            self._draw_loot_icon(screen, cell, cx, cy, node_r)

        elif visual == "loot_done":
            # Fill + border matching empty-node style, grey icon overlay on interior
            pygame.draw.rect(screen, (10, 28, 12), rect)
            self._draw_loot_icon(screen, cell, cx, cy, node_r)
            inner = rect.inflate(-4, -4)
            grey = pygame.Surface((inner.width, inner.height), pygame.SRCALPHA)
            grey.fill((8, 8, 8, 170))
            screen.blit(grey, inner.topleft)
            pygame.draw.rect(screen, _COL_NODE_EMPTY_RIM, rect, 1)

        elif visual == "loot_destroyed":
            pygame.draw.rect(screen, (22, 8, 8), rect)
            pygame.draw.rect(screen, (60, 18, 18), rect, 1)
            r2 = nr // 2
            pygame.draw.line(screen, (100, 25, 25),
                             (cx - r2, cy - r2), (cx + r2, cy + r2), 2)
            pygame.draw.line(screen, (100, 25, 25),
                             (cx + r2, cy - r2), (cx - r2, cy + r2), 2)

        elif visual == "security_revealed":
            kind = cell.security_kind
            if kind == SecurityKind.BLOCKED:
                rim_col, fill_col = _NEON_RED, (50, 8, 14)
                sym, sym_col = None, _NEON_RED
            elif kind == SecurityKind.TIME_PENALTY:
                rim_col, fill_col = _NEON_RED, (45, 8, 14)
                sym, sym_col = "-3s", _NEON_RED
            else:  # DESTROY_LOOT
                rim_col, fill_col = _NEON_RED, (45, 8, 14)
                sym, sym_col = "DEL", _NEON_RED

            pygame.draw.rect(screen, fill_col, rect)
            pygame.draw.rect(screen, rim_col, rect, 2)

            if sym is None:
                r2 = nr // 2
                pygame.draw.line(screen, _NEON_RED,
                                 (cx - r2, cy - r2), (cx + r2, cy + r2), 2)
                pygame.draw.line(screen, _NEON_RED,
                                 (cx + r2, cy - r2), (cx - r2, cy + r2), 2)
            else:
                s = self._font_ico.render(sym, True, sym_col)
                screen.blit(s, (cx - s.get_width() // 2,
                                cy - s.get_height() // 2))

        else:
            # EMPTY (and hidden SECURITY — identical look)
            pygame.draw.rect(screen, _COL_NODE_EMPTY, sm_rect)
            pygame.draw.rect(screen, _COL_NODE_EMPTY_RIM, sm_rect, 1)

        # Flash override (BLOCKED)
        if cell.flash_timer > 0:
            alpha = min(220, int(cell.flash_timer * 400))
            pad   = nr + 4
            fsurf = pygame.Surface((pad * 2, pad * 2), pygame.SRCALPHA)
            pygame.draw.rect(fsurf, (*_NEON_RED, alpha), (0, 0, pad * 2, pad * 2))
            screen.blit(fsurf, (cx - pad, cy - pad))

    def _draw_loot_icon(
        self,
        screen: pygame.Surface,
        cell: GridCell,
        cx: int, cy: int,
        node_r: int,
    ) -> None:
        kind = cell.loot_kind
        icon_size = max(12, int(node_r * 1.7))

        sprite_key = {
            LootKind.AMMO:         "item_loot_ammo",
            LootKind.RIFLE_AMMO:   "item_loot_ammo",
            LootKind.SHOTGUN_AMMO: "item_loot_ammo",
            LootKind.HEAL:         "item_loot_consumable",
            LootKind.MEDKIT:       "item_loot_consumable",
            LootKind.WEAPON:       "item_loot_ranged",
            LootKind.ARMOR:        "item_loot_armor",
            LootKind.CREDITS:      "item_hack_credits",
            LootKind.BONUS_TIME:   "item_hack_bonus_time",
            LootKind.MYSTERY:      "item_hack_mystery",
        }.get(kind, "item_loot")

        sprite = self._item_sprites.get(sprite_key)
        if sprite:
            scaled = pygame.transform.scale(sprite, (icon_size, icon_size))
            screen.blit(scaled, (cx - icon_size // 2, cy - icon_size // 2))
        else:
            s = self._font_ico.render("■", True, _NEON_GREEN)
            screen.blit(s, (cx - s.get_width() // 2, cy - s.get_height() // 2))

    def _draw_player(
        self, screen: pygame.Surface, panel: pygame.Rect, node_r: int
    ) -> None:
        """Pulsing square around player's position, interpolated during MOVING."""
        if self._state == _State.MOVING and self._params.step_time > 0:
            progress = 1.0 - self._move_timer / self._params.step_time
            sx, sy = self._cell_center(self._prev_pos[0],    self._prev_pos[1],    panel)
            ex, ey = self._cell_center(self._pending_pos[0], self._pending_pos[1], panel)
            px = int(sx + (ex - sx) * progress)
            py = int(sy + (ey - sy) * progress)
        else:
            px, py = self._cell_center(self._player_pos[0], self._player_pos[1], panel)

        base  = node_r + 6
        pulse = base + int(3 * math.sin(self._anim_time * 4.5))
        p_rect = pygame.Rect(px - pulse, py - pulse, pulse * 2, pulse * 2)
        pygame.draw.rect(screen, _NEON_YELLOW, p_rect, 2)

        arm = max(4, min(10, pulse // 3))
        for bx, by, dx, dy in (
            (p_rect.left,  p_rect.top,      1,  1),
            (p_rect.right, p_rect.top,     -1,  1),
            (p_rect.left,  p_rect.bottom,   1, -1),
            (p_rect.right, p_rect.bottom,  -1, -1),
        ):
            pygame.draw.line(screen, _NEON_YELLOW, (bx, by), (bx + dx * arm, by), 2)
            pygame.draw.line(screen, _NEON_YELLOW, (bx, by), (bx, by + dy * arm), 2)

    # ------------------------------------------------------------------
    # Draw — overlays (ported from classic HackScene)
    # ------------------------------------------------------------------

    def _draw_sec_overlay(self, screen: pygame.Surface, ov: dict) -> None:
        sw, sh = screen.get_size()
        color  = ov["color"]

        # Fade out over the last 0.4 s
        tmr  = ov["timer"]
        fade = min(1.0, tmr / 0.4) if tmr < 0.4 else 1.0

        # Edge vignette flash
        vig   = pygame.Surface((sw, sh), pygame.SRCALPHA)
        depth = 80
        for i in range(depth):
            a = int(fade * 110 * (1.0 - i / depth) ** 1.5)
            if a <= 0:
                continue
            pygame.draw.rect(vig, (*color, a), (i, i, sw - 2 * i, sh - 2 * i), 1)
        screen.blit(vig, (0, 0))

        # Central translucent banner
        panel_h = 90
        panel_y = sh // 2 - panel_h // 2
        banner  = pygame.Surface((sw, panel_h), pygame.SRCALPHA)
        banner.fill((*color, min(int(fade * 200), 38)))
        screen.blit(banner, (0, panel_y))
        line_surf = pygame.Surface((sw, 2), pygame.SRCALPHA)
        line_surf.fill((*color, int(fade * 200)))
        screen.blit(line_surf, (0, panel_y))
        screen.blit(line_surf, (0, panel_y + panel_h - 2))

        # Main text
        main_s = self._font_lg.render(
            ov["text"], True,
            tuple(int(c * fade + (1 - fade) * 40) for c in color),
        )
        screen.blit(main_s, (sw // 2 - main_s.get_width() // 2, panel_y + 14))

        # Sub text
        sub_s = self._font_md.render(
            ov["sub"], True,
            tuple(int(c * fade * 0.7) for c in color),
        )
        screen.blit(sub_s, (sw // 2 - sub_s.get_width() // 2,
                            panel_y + 14 + main_s.get_height() + 6))

    def _draw_result_overlay(self, screen: pygame.Surface) -> None:
        sw, sh  = screen.get_size()
        success = self._done_success
        vsurf   = pygame.Surface((sw, sh), pygame.SRCALPHA)
        vsurf.fill((0, 0, 0, 160))
        screen.blit(vsurf, (0, 0))

        color  = _NEON_GREEN if success else _NEON_RED
        title  = t("hack.result.success") if success else t("hack.result.fail")
        tsurf  = self._font_lg.render(title, True, color)
        cy2    = sh // 2
        screen.blit(tsurf, (sw // 2 - tsurf.get_width() // 2, cy2 - 60))
        pygame.draw.line(screen, color, (sw // 2 - 160, cy2 - 30), (sw // 2 + 160, cy2 - 30), 1)

        y = cy2 - 10
        if success:
            if not self._result_items and self._result_credits == 0:
                s = self._font_sm.render(t("hack.result.no_data"), True, _TEXT_DIM)
                screen.blit(s, (sw // 2 - s.get_width() // 2, y))
            else:
                for item in self._result_items:
                    s = self._font_sm.render(f"  + {item.name}", True, _NEON_GREEN)
                    screen.blit(s, (sw // 2 - s.get_width() // 2, y))
                    y += 20
                if self._result_credits > 0:
                    s = self._font_sm.render(f"  + ¥{self._result_credits}", True, _NEON_YELLOW)
                    screen.blit(s, (sw // 2 - s.get_width() // 2, y))
        else:
            s = self._font_sm.render(t("hack.result.drone"), True, _NEON_RED)
            screen.blit(s, (sw // 2 - s.get_width() // 2, y))

    def _draw_help_overlay(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        # Dim background
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 210))
        screen.blit(dim, (0, 0))

        # Panel
        pw = min(sw - 60, 860)
        ph = 440
        px = (sw - pw) // 2
        py = (sh - ph) // 2
        pygame.draw.rect(screen, _PANEL_BG, (px, py, pw, ph))
        pygame.draw.rect(screen, _NEON_CYAN, (px, py, pw, ph), 1)
        _draw_corner_bracket(screen, px,      py,      50, 14, _NEON_CYAN, 1)
        _draw_corner_bracket(screen, px + pw, py,      50, 14, _NEON_CYAN, 1, flip_x=True)
        _draw_corner_bracket(screen, px,      py + ph, 50, 14, _NEON_CYAN, 1, flip_y=True)
        _draw_corner_bracket(screen, px + pw, py + ph, 50, 14, _NEON_CYAN, 1, flip_x=True, flip_y=True)

        # Title
        title_s = self._font_lg.render(t("hack.help.title"), True, _NEON_CYAN)
        screen.blit(title_s, (sw // 2 - title_s.get_width() // 2, py + 14))
        sep_y = py + 14 + title_s.get_height() + 6
        pygame.draw.line(screen, _NEON_CYAN, (px + 20, sep_y), (px + pw - 20, sep_y), 1)

        col_l = px + 26
        col_r = px + pw // 2 + 14
        y_l   = sep_y + 14
        y_r   = sep_y + 14
        lh    = 17
        lh2   = 13
        font  = self._font_sm

        def _section(x: int, y: int, text: str) -> int:
            s = self._font_md.render(text, True, _NEON_CYAN)
            screen.blit(s, (x, y))
            return y + 20

        def _aligned(x: int, y: int,
                     items: list) -> int:
            if not items:
                return y
            gap    = 10
            col_dx = max(font.size(lbl)[0] for lbl, _, _ in items) + gap
            for lbl, lc, desc in items:
                screen.blit(font.render(lbl,  True, lc),    (x,          y))
                screen.blit(font.render(desc, True, _TEXT), (x + col_dx, y))
                y += lh
            return y

        def _two_line(x: int, y: int, items: list) -> int:
            for name, nc, desc in items:
                pygame.draw.rect(screen, nc, (x, y + 4, 5, 5))
                screen.blit(font.render(name, True, nc),        (x + 9,  y))
                screen.blit(font.render(desc, True, _TEXT_DIM), (x + 9, y + lh - 2))
                y += lh + lh2
            return y

        def _bullets(x: int, y: int, items: list) -> int:
            for bc, text in items:
                b = font.render("• ", True, bc)
                screen.blit(b, (x, y))
                screen.blit(font.render(text, True, _TEXT), (x + b.get_width(), y))
                y += lh
            return y

        # ── Left column — node types ──────────────────────────────────
        y_l = _section(col_l, y_l, t("hack.help.node_types"))
        y_l = _aligned(col_l, y_l, [
            (t("hack.help.node.entry.lbl"), _NEON_CYAN,         t("hack.help.node.entry.desc")),
            (t("hack.help.node.cache.lbl"), _NEON_GREEN,        t("hack.help.node.cache.desc")),
            (t("hack.help.node.empty.lbl"), _COL_NODE_EMPTY_RIM, t("hack.help.node.empty.desc")),
            (t("hack.help.node.ice.lbl"),   _TEXT_DIM,           t("hack.help.node.ice.desc")),
        ])
        y_l += 10

        y_l = _section(col_l, y_l, t("hack.help.ice_section"))
        y_l = _two_line(col_l, y_l, [
            (t("hack.help.ice.time.lbl"),    _NEON_RED, t("hack.help.ice.time.desc")),
            (t("hack.help.ice.corrupt.lbl"), _NEON_RED, t("hack.help.ice.corrupt.desc")),
            (t("hack.help.ice.blocked.lbl"), _NEON_RED,    t("hack.help.ice.blocked.desc")),
        ])

        # ── Right column — loot & controls ───────────────────────────
        y_r = _section(col_r, y_r, t("hack.help.timer"))
        y_r = _bullets(col_r, y_r, [
            (_TEXT_DIM,         t("hack.help.timer.1")),
            (_TEXT_DIM,         t("hack.help.timer.2")),
            ((80, 180, 255),    t("hack.help.timer.3")),
            (_TEXT_DIM,         t("hack.help.timer.4")),
        ])
        y_r += 10

        y_r = _section(col_r, y_r, t("hack.help.controls"))
        y_r = _aligned(col_r, y_r, [
            (t("hack.help.ctrl.wasd.key"),   _NEON_YELLOW, t("hack.help.ctrl.wasd.desc")),
            (t("hack.help.ctrl.arrows.key"), _NEON_YELLOW, t("hack.help.ctrl.arrows.desc")),
            (t("hack.help.ctrl.esc.key"),    _NEON_YELLOW, t("hack.help.ctrl.esc.desc")),
            (t("hack.help.ctrl.f1.key"),     _NEON_YELLOW, t("hack.help.ctrl.f1.desc")),
        ])
        y_r += 10
        y_r = _section(col_r, y_r, t("hack.help.grid_section"))
        y_r = _bullets(col_r, y_r, [
            (_NEON_CYAN, t("hack.help.grid.automove")),
            (_NEON_CYAN, t("hack.help.grid.stop")),
            (_TEXT_DIM,  t("hack.help.grid.lit")),
        ])

        # Close hint
        close_s = font.render(t("hack.help.close"), True, _TEXT_DIM)
        screen.blit(close_s, (sw // 2 - close_s.get_width() // 2, py + ph - 22))
