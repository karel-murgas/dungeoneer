"""Hacking minigame — full Scene implementation."""
from __future__ import annotations

import math
import random
from enum import auto, Enum
from typing import Callable, List, Optional, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.minigame.hack_node import HackMap, HackNode, LootKind, NodeType, SecurityKind
from dungeoneer.minigame.hack_generator import HackParams, generate_hack_map
from dungeoneer.minigame.hack_audio import HackAudio
from dungeoneer.rendering import procedural_sprites

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp
    from dungeoneer.items.item import Item


# ---------------------------------------------------------------------------
# Colour palette — neon cyberpunk
# ---------------------------------------------------------------------------
_BG            = (4,    8,  18)
_GRID_DOT      = (14,  26,  42)
_PANEL_BG      = (6,   12,  22)

_NEON_CYAN     = (0,   230, 220)
_NEON_GREEN    = (0,   220,  80)
_NEON_RED      = (220,  40,  80)
_NEON_ORANGE   = (220, 140,   0)
_NEON_YELLOW   = (200, 220,  60)
_NEON_MAGENTA  = (190,  40, 170)

_TEXT          = (160, 220, 200)
_TEXT_DIM      = (60,  100,  80)
_TEXT_GOOD     = _NEON_GREEN
_TEXT_WARN     = _NEON_ORANGE

_COL_ENTRY     = _NEON_CYAN
_COL_EMPTY     = (28,   44,  62)
_COL_LOOT      = _NEON_GREEN
_COL_LOOT_D    = (16,   40,  20)
_COL_SEC_HID   = (80,   58,  18)
_COL_SEC_REV   = _NEON_RED
_COL_PLAYER    = _NEON_CYAN
_COL_EDGE      = (18,   50,  70)
_COL_EDGE_D    = (12,   20,  28)
_COL_FLOW      = _NEON_CYAN

_COL_TIMER_HI  = _NEON_GREEN
_COL_TIMER_MID = _NEON_ORANGE
_COL_TIMER_LO  = _NEON_RED

_BORDER        = _NEON_CYAN


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

class _State(Enum):
    IDLE    = auto()
    MOVING  = auto()
    HACKING = auto()
    DONE    = auto()


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
_HEADER_H  = 64
_FOOTER_H  = 76
_NODE_R    = 18
_PLAYER_R  = 34
_PULSE_AMP =  5
_GLOW_LAYERS = 3


class HackScene(Scene):
    """Real-time hacking minigame scene."""

    def __init__(
        self,
        app: "GameApp",
        params: Optional[HackParams] = None,
        on_complete: Optional[Callable[[bool, List["Item"], int], None]] = None,
    ) -> None:
        super().__init__(app)
        self._params = params or HackParams()
        self._on_complete = on_complete or (lambda *_: None)

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def on_enter(self) -> None:
        p = self._params
        self._hack_map: HackMap = generate_hack_map(p)
        self._player_node: int  = self._hack_map.entry_id
        self._prev_node: int    = self._hack_map.entry_id
        self._state: _State     = _State.IDLE

        self._time_remaining: float = p.time_limit
        self._move_timer: float     = 0.0
        self._hack_timer: float     = 0.0
        self._pending_node: int     = self._player_node
        self._done_timer: float     = 0.0
        self._done_success: bool    = False

        self._result_items: List["Item"] = []
        self._result_credits: int        = 0

        self._anim_time: float     = 0.0
        self._tick_cooldown: float = 0.0   # for low-timer ticking sound
        self._timer_started: bool  = False  # timer waits for first move

        # Security effect overlay  {timer, text, sub, color}
        self._sec_overlay:  dict | None = None
        # Loot collection overlay  {timer, text, sub, color}
        self._loot_overlay: dict | None = None

        self._status: str = "Analyse the network, then move to begin."
        self._log: str    = ""
        self._show_help: bool = False

        # Audio
        self._audio = HackAudio()
        self._audio.build()

        # Fonts
        self._font_lg  = pygame.font.SysFont("consolas", 22, bold=True)
        self._font_md  = pygame.font.SysFont("consolas", 16)
        self._font_sm  = pygame.font.SysFont("consolas", 13)
        self._font_xs  = pygame.font.SysFont("consolas", 11, bold=True)

        # Pre-scale item sprites from the main game (32×32 → 28×28 to fit in node)
        _icon_size = 38
        self._item_sprites: dict[str, pygame.Surface] = {}
        for _key in ("item_loot_ammo", "item_loot_consumable", "item_loot_ranged", "item_loot"):
            _raw = procedural_sprites.get(_key)
            if _raw is not None:
                self._item_sprites[_key] = pygame.transform.scale(_raw, (_icon_size, _icon_size))
        self._font_bonus = pygame.font.SysFont("consolas", 15, bold=True)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        if self._state == _State.DONE:
            return
        if self._sec_overlay is not None:
            return

        for event in events:
            if event.type != pygame.KEYDOWN:
                continue

            key = event.key

            if key == pygame.K_F1:
                self._show_help = not self._show_help
                continue

            if key == pygame.K_ESCAPE:
                if self._state == _State.HACKING:
                    self._state  = _State.IDLE
                    self._status = "Hack cancelled."
                elif self._state == _State.IDLE:
                    self._finish(success=True)
                continue

            if self._state != _State.IDLE:
                continue

            side = _KEY_TO_SIDE.get(key)
            if side is not None:
                port_sides = self._player_port_sides()
                target = next((nb_id for nb_id, s in port_sides.items() if s == side), None)
                if target is not None:
                    self._start_move(target)

    def handle_mouse(self, pos: tuple[int, int]) -> None:
        if self._sec_overlay is not None:
            return
        if self._state != _State.IDLE:
            return
        panel = self._graph_panel_rect()
        hit = _NODE_R + 8
        for node in self._hack_map.neighbors_of(self._player_node):
            nx, ny = self._node_screen_pos(node, panel)
            if abs(pos[0] - nx) <= hit and abs(pos[1] - ny) <= hit:
                self._start_move(node.node_id)
                return

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        dt = min(dt, 0.1)
        self._anim_time += dt

        for node in self._hack_map.nodes:
            if node.flash_timer > 0:
                node.flash_timer = max(0.0, node.flash_timer - dt)

        if self._state == _State.DONE:
            self._done_timer -= dt
            if self._done_timer <= 0:
                self._on_complete(self._done_success, self._result_items, self._result_credits)
                self.app.scenes.pop()
            return

        # Security effect overlay countdown
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

        # Low-timer ticking
        if self._timer_started and not self._show_help and self._time_remaining <= 3.0:
            self._tick_cooldown -= dt
            if self._tick_cooldown <= 0:
                self._audio.play("timer_tick", volume=0.6)
                self._tick_cooldown = 0.5

        if self._state == _State.MOVING:
            self._move_timer -= dt
            if self._move_timer <= 0:
                self._arrive(self._pending_node)

        elif self._state == _State.HACKING:
            self._hack_timer -= dt
            if self._hack_timer <= 0:
                self._collect_loot(self._player_node)
                if self._state != _State.DONE:
                    self._state = _State.IDLE

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(_BG)
        self._draw_bg_grid(screen)

        # Route mouse clicks (pulled out of event queue here so as not to miss them)
        for event in pygame.event.get(pygame.MOUSEBUTTONDOWN):
            if event.button == 1:
                self.handle_mouse(event.pos)

        panel = self._graph_panel_rect()
        self._draw_header(screen)
        self._draw_graph(screen, panel)
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
    # Private — state machine
    # ------------------------------------------------------------------

    def _start_move(self, target_id: int) -> None:
        self._timer_started = True
        self._prev_node     = self._player_node
        self._pending_node  = target_id
        self._move_timer    = self._params.move_time
        self._state         = _State.MOVING
        self._status        = f"Routing to NODE-{target_id}…"
        self._audio.play("move", volume=0.5)

    def _arrive(self, target_id: int) -> None:
        self._player_node = target_id
        node = self._hack_map.get(target_id)

        if node.ntype == NodeType.SECURITY and not node.hacked:
            node.revealed = True
            self._apply_security(node)
            node.ntype  = NodeType.EMPTY
            node.hacked = True
        elif node.ntype == NodeType.LOOT and not node.hacked:
            self._hack_timer = self._params.hack_time
            self._state      = _State.HACKING
            self._status     = f"Extracting {node.loot_kind.name.replace('_', ' ').title()}…"
            self._audio.play("hack_start", volume=0.7)
        else:
            self._state  = _State.IDLE
            self._status = "Navigate to loot nodes and hack them."

    def _apply_security(self, node: HackNode) -> None:
        kind = node.security_kind
        self._audio.play("ice", volume=0.75)

        if kind == SecurityKind.TIME_PENALTY:
            self._time_remaining = max(0.0, self._time_remaining - 3.0)
            self._status = "ICE TRIGGERED — Time penalty  -3s!"
            self._log    = "[-3s]"
            self._state  = _State.IDLE
            self._sec_overlay = {
                "timer": 1.6,
                "text":  "TIME PENALTY",
                "sub":   "−3 SECONDS",
                "color": _NEON_RED,
            }

        elif kind == SecurityKind.DESTROY_LOOT:
            victims = [
                n for n in self._hack_map.nodes
                if n.ntype == NodeType.LOOT and n.active and not n.hacked and n.node_id != node.node_id
            ]
            if victims:
                v = random.choice(victims)
                v.active = False
                for nb_id in v.neighbors:
                    nb = self._hack_map.nodes[nb_id]
                    if v.node_id in nb.neighbors:
                        nb.neighbors.remove(v.node_id)
                self._status = "ICE TRIGGERED — Data cache destroyed!"
                self._sec_overlay = {
                    "timer": 1.6,
                    "text":  "DATA CORRUPTED",
                    "sub":   "CACHE NODE DESTROYED",
                    "color": _NEON_ORANGE,
                }
            else:
                self._status = "ICE TRIGGERED — No targets."
                self._sec_overlay = {
                    "timer": 1.2,
                    "text":  "ICE TRIGGERED",
                    "sub":   "NO TARGETS",
                    "color": _NEON_ORANGE,
                }
            self._state = _State.IDLE
            # Auto-finish if security destroyed the last remaining loot node
            remaining = [n for n in self._hack_map.nodes if n.ntype == NodeType.LOOT and n.active and not n.hacked]
            if not remaining:
                self._finish(success=True)

        elif kind == SecurityKind.BLOCKED:
            self._player_node = self._prev_node
            node.flash_timer  = 0.55
            self._status = "ICE TRIGGERED — Access denied!"
            self._state  = _State.IDLE
            self._sec_overlay = {
                "timer": 1.4,
                "text":  "ACCESS DENIED",
                "sub":   "NODE BLOCKED — REROUTED",
                "color": _NEON_RED,
            }

    def _collect_loot(self, node_id: int) -> None:
        node = self._hack_map.get(node_id)
        node.hacked = True
        kind = node.loot_kind

        if kind == LootKind.BONUS_TIME:
            self._time_remaining += 3.0
            self._status = "Bonus time  +3s"
            self._log    = "[+3s]"
            self._audio.play("bonus_time", volume=0.7)
            self._loot_overlay = {
                "timer": 1.4,
                "text":  "BONUS TIME",
                "sub":   "+3 SECONDS",
                "color": (80, 180, 255),
            }
        elif kind == LootKind.CREDITS:
            amount = random.randint(10, 40)
            self._result_credits += amount
            self._status = f"Credits extracted  +¥{amount}"
            self._log    = f"[+¥{amount}]"
            self._audio.play("hack_complete", volume=0.7)
            self._loot_overlay = {
                "timer": 1.4,
                "text":  "CREDITS EXTRACTED",
                "sub":   f"+¥{amount}",
                "color": _NEON_GREEN,
            }
        else:
            item = _make_loot_item(kind)
            if item is not None:
                self._result_items.append(item)
                self._status = f"Extracted: {item.name}"
                self._log    = f"[{item.name}]"
                self._loot_overlay = {
                    "timer": 1.4,
                    "text":  "DATA EXTRACTED",
                    "sub":   item.name.upper(),
                    "color": _NEON_GREEN,
                }
            self._audio.play("hack_complete", volume=0.7)

        # Auto-finish when all active loot nodes have been collected
        remaining = [n for n in self._hack_map.nodes if n.ntype == NodeType.LOOT and n.active and not n.hacked]
        if not remaining:
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
    # Private — input helpers
    # ------------------------------------------------------------------

    def _player_port_sides(self) -> dict[int, int]:
        """Return {neighbor_id: side} port assignments for the current player node."""
        player_node = self._hack_map.get(self._player_node)
        nodes = self._hack_map.nodes
        active_nbs = [nodes[nb_id] for nb_id in player_node.neighbors
                      if nodes[nb_id].active]
        return _assign_port_sides(player_node, active_nbs)

    def _compute_key_assignments(self) -> dict[int, str]:
        """Return {neighbor_node_id: key_label} based on exit port side."""
        return {nb_id: _SIDE_KEY_LABEL[side]
                for nb_id, side in self._player_port_sides().items()}

    # ------------------------------------------------------------------
    # Private — rendering helpers
    # ------------------------------------------------------------------

    def _graph_panel_rect(self) -> pygame.Rect:
        sw, sh = self.app.screen.get_size()
        m = 20
        return pygame.Rect(m, _HEADER_H + m, sw - 2*m, sh - _HEADER_H - _FOOTER_H - 2*m)

    def _node_screen_pos(self, node: HackNode, panel: pygame.Rect) -> tuple[int, int]:
        return (int(panel.x + node.sx * panel.width),
                int(panel.y + node.sy * panel.height))

    def _lerp_color(self, a: tuple, b: tuple, t: float) -> tuple:
        t = max(0.0, min(1.0, t))
        return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

    def _timer_color(self) -> tuple:
        ratio = self._time_remaining / self._params.time_limit
        if ratio > 0.5:
            return self._lerp_color(_COL_TIMER_MID, _COL_TIMER_HI, (ratio - 0.5) * 2)
        elif ratio > 0.25:
            return self._lerp_color(_COL_TIMER_LO, _COL_TIMER_MID, (ratio - 0.25) * 4)
        return _COL_TIMER_LO

    # ------------------------------------------------------------------
    # Draw — background
    # ------------------------------------------------------------------

    def _draw_bg_grid(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        step = 32
        for x in range(0, sw + step, step):
            for y in range(0, sh + step, step):
                pygame.draw.circle(screen, _GRID_DOT, (x, y), 1)

    # ------------------------------------------------------------------
    # Draw — glow
    # ------------------------------------------------------------------

    def _draw_glow(
        self,
        screen: pygame.Surface,
        color: tuple,
        cx: int, cy: int,
        radius: int,
        layers: int = 3,
        max_alpha: int = 70,
    ) -> None:
        spread = layers * 10
        size   = (radius + spread) * 2
        surf   = pygame.Surface((size, size), pygame.SRCALPHA)
        center = size // 2
        for i in range(layers, 0, -1):
            r     = radius + i * 10
            alpha = max_alpha * i // layers
            pygame.draw.circle(surf, (*color, alpha), (center, center), r)
        screen.blit(surf, (cx - center, cy - center))

    # ------------------------------------------------------------------
    # Draw — header
    # ------------------------------------------------------------------

    def _draw_header(self, screen: pygame.Surface) -> None:
        sw = screen.get_width()

        # Background
        pygame.draw.rect(screen, _PANEL_BG, (0, 0, sw, _HEADER_H))

        # Bottom border with glow line
        pygame.draw.line(screen, _NEON_CYAN,    (0, _HEADER_H - 1), (sw, _HEADER_H - 1), 1)
        pygame.draw.line(screen, (*_NEON_CYAN, 40), (0, _HEADER_H - 3), (sw, _HEADER_H - 3), 1)

        # Corner brackets
        _draw_corner_bracket(screen, 8, 8, 40, 14, _NEON_CYAN, 1)

        # Title
        title_surf = self._font_lg.render("INTRUSION PROTOCOL", True, _NEON_CYAN)
        screen.blit(title_surf, (28, 20))

        # Blinking cursor after title
        if int(self._anim_time * 2) % 2 == 0:
            cx = 28 + title_surf.get_width() + 6
            cursor_surf = self._font_lg.render("_", True, _NEON_CYAN)
            screen.blit(cursor_surf, (cx, 20))

        # ESC hint (center)
        if self._state == _State.HACKING:
            esc_text  = "[ESC]  CANCEL EXTRACTION"
            esc_color = _NEON_ORANGE
        elif not self._timer_started:
            esc_text  = "— MOVE TO START TIMER —"
            esc_color = _NEON_YELLOW
        else:
            esc_text  = "[ESC]  ABORT HACK"
            esc_color = _TEXT_DIM
        esc_surf = self._font_md.render(esc_text, True, esc_color)
        screen.blit(esc_surf, (sw // 2 - esc_surf.get_width() // 2, 22))

        # Timer number (right side)
        if not self._timer_started:
            t_color = _TEXT_DIM
            t_str   = f"{self._time_remaining:5.1f}s"
        else:
            t_color = self._timer_color()
            t_str   = f"{self._time_remaining:5.1f}s"
        t_surf = self._font_lg.render(t_str, True, t_color)
        tx = sw - t_surf.get_width() - 14
        screen.blit(t_surf, (tx, 18))

        # Full-width timer progress bar at the very bottom of the header
        bar_margin = 6
        bar_x = bar_margin
        bar_w = sw - bar_margin * 2
        bar_h = 5
        bar_y = _HEADER_H - bar_h - 2

        if not self._timer_started:
            # Not yet started — pulse the full bar to indicate "waiting"
            alpha = int(120 + 80 * math.sin(self._anim_time * 3.0))
            bar_surf = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
            bar_surf.fill((*_TEXT_DIM, alpha))
            screen.blit(bar_surf, (bar_x, bar_y))
        else:
            ratio  = self._time_remaining / self._params.time_limit
            fill_w = int(bar_w * ratio)
            # Track background
            pygame.draw.rect(screen, (14, 22, 32), (bar_x, bar_y, bar_w, bar_h))
            if fill_w > 0:
                pygame.draw.rect(screen, t_color, (bar_x, bar_y, fill_w, bar_h))
            # Leading edge glow
            if fill_w > 2:
                glow_surf = pygame.Surface((6, bar_h + 4), pygame.SRCALPHA)
                for gi in range(3):
                    pygame.draw.rect(glow_surf, (*t_color, 80 - gi * 25),
                                     (gi, 0, 6 - gi * 2, bar_h + 4))
                screen.blit(glow_surf, (bar_x + fill_w - 3, bar_y - 2))

    # ------------------------------------------------------------------
    # Draw — footer
    # ------------------------------------------------------------------

    def _draw_footer(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        fy = sh - _FOOTER_H

        pygame.draw.rect(screen, _PANEL_BG, (0, fy, sw, _FOOTER_H))
        pygame.draw.line(screen, _NEON_CYAN, (0, fy), (sw, fy), 1)
        pygame.draw.line(screen, (*_NEON_CYAN, 40), (0, fy + 2), (sw, fy + 2), 1)

        # Status
        prefix_surf = self._font_md.render("▶ ", True, _NEON_CYAN)
        screen.blit(prefix_surf, (14, fy + 12))
        status_surf = self._font_md.render(self._status, True, _TEXT)
        screen.blit(status_surf, (14 + prefix_surf.get_width(), fy + 12))

        # Log line
        if self._log:
            log_surf = self._font_sm.render(self._log, True, _NEON_GREEN)
            screen.blit(log_surf, (14, fy + 38))

        # Key layout hint (right)
        hint = "W A S D / Arrows  +  Mouse  |  [F1] Help"
        hint_surf = self._font_xs.render(hint, True, _TEXT_DIM)
        screen.blit(hint_surf, (sw - hint_surf.get_width() - 14, fy + _FOOTER_H - hint_surf.get_height() - 10))

        # Loot counter
        n_hacked  = sum(1 for n in self._hack_map.nodes if n.ntype == NodeType.LOOT and n.hacked)
        n_active  = sum(1 for n in self._hack_map.nodes if n.ntype == NodeType.LOOT and n.active)
        n_total   = n_hacked + n_active  # hacked + still-reachable; destroyed nodes excluded
        counter = f"DATA: {n_hacked}/{n_total}"
        c_surf = self._font_sm.render(counter, True, _NEON_GREEN if n_hacked > 0 else _TEXT_DIM)
        screen.blit(c_surf, (sw - c_surf.get_width() - 14, fy + 12))

    # ------------------------------------------------------------------
    # Draw — graph
    # ------------------------------------------------------------------

    def _draw_graph(self, screen: pygame.Surface, panel: pygame.Rect) -> None:
        nodes  = self._hack_map.nodes
        player = self._player_node

        key_badges: dict[int, str] = {}
        if self._state == _State.IDLE:
            key_badges = self._compute_key_assignments()

        reachable_ids = {nb.node_id for nb in self._hack_map.neighbors_of(player)}

        # Panel fill + border
        pygame.draw.rect(screen, _PANEL_BG, panel)
        _draw_corner_bracket(screen, panel.x, panel.y, 50, 16, _NEON_CYAN, 1)
        _draw_corner_bracket(screen, panel.right, panel.y, 50, 16, _NEON_CYAN, 1, flip_x=True)
        _draw_corner_bracket(screen, panel.x, panel.bottom, 50, 16, _NEON_CYAN, 1, flip_y=True)
        _draw_corner_bracket(screen, panel.right, panel.bottom, 50, 16, _NEON_CYAN, 1, flip_x=True, flip_y=True)

        # Scan line (subtle horizontal sweep)
        scan_y = int(panel.y + (self._anim_time * 60) % panel.height)
        scan_surf = pygame.Surface((panel.width, 2), pygame.SRCALPHA)
        scan_surf.fill((*_NEON_CYAN, 18))
        screen.blit(scan_surf, (panel.x, scan_y))

        # Pre-compute port-side assignments and screen rects for all active nodes
        port_sides:  dict[tuple[int, int], int]   = {}
        node_screen: dict[int, tuple[int, int]]   = {}
        node_rects:  dict[int, pygame.Rect]        = {}
        for node in nodes:
            if not node.active:
                continue
            nx, ny = self._node_screen_pos(node, panel)
            node_screen[node.node_id] = (nx, ny)
            node_rects[node.node_id]  = pygame.Rect(nx - _NODE_R, ny - _NODE_R,
                                                     _NODE_R * 2, _NODE_R * 2)
            active_nbs = [nodes[nb_id] for nb_id in node.neighbors if nodes[nb_id].active]
            for nb_id, side in _assign_port_sides(node, active_nbs).items():
                port_sides[(node.node_id, nb_id)] = side

        # --- Pre-compute all edge paths (sequential so each avoids prior segments) ---
        _obs_all = list(node_rects.values())
        routed_segs: list[tuple[int, int, int, int]] = []
        edge_paths:  dict[tuple[int, int], list[tuple[int, int]]] = {}
        for _node in nodes:
            if not _node.active:
                continue
            _nx, _ny = node_screen[_node.node_id]
            for _nb_id in _node.neighbors:
                if _nb_id < _node.node_id:
                    continue
                _nb = nodes[_nb_id]
                if not _nb.active:
                    continue
                _nbx, _nby = node_screen[_nb_id]
                _ss = port_sides.get((_node.node_id, _nb_id), _SIDE_RIGHT)
                _ts = port_sides.get((_nb_id, _node.node_id), _SIDE_LEFT)
                _sp = _node_port(_nx,  _ny,  _ss)
                _tp = _node_port(_nbx, _nby, _ts)
                _pts = _edge_path(_sp[0], _sp[1], _ss, _tp[0], _tp[1], _ts,
                                  _obs_all, routed_segs)
                edge_paths[(_node.node_id, _nb_id)] = _pts
                for _i in range(len(_pts) - 1):
                    routed_segs.append((_pts[_i][0], _pts[_i][1],
                                        _pts[_i+1][0], _pts[_i+1][1]))

        # --- Edges ---
        for node in nodes:
            if not node.active:
                continue
            nx, ny = node_screen[node.node_id]
            for nb_id in node.neighbors:
                if nb_id < node.node_id:
                    continue
                nb = nodes[nb_id]
                if not nb.active:
                    continue
                nbx, nby = node_screen[nb_id]
                src_side = port_sides.get((node.node_id, nb_id), _SIDE_RIGHT)
                tgt_side = port_sides.get((nb_id, node.node_id), _SIDE_LEFT)
                sp = _node_port(nx,  ny,  src_side)
                tp = _node_port(nbx, nby, tgt_side)
                pts = edge_paths[(node.node_id, nb_id)]
                self._draw_edge(screen, pts, sp, src_side, tp, tgt_side,
                                node.node_id, nb_id, player, node_rects)

        # Moving dot along port-routed edge
        if self._state == _State.MOVING and self._params.move_time > 0:
            progress = 1.0 - self._move_timer / self._params.move_time
            src = nodes[self._prev_node]
            dst = nodes[self._pending_node]
            snx, sny = node_screen.get(self._prev_node,
                                       self._node_screen_pos(src, panel))
            dnx, dny = node_screen.get(self._pending_node,
                                       self._node_screen_pos(dst, panel))
            _dot_key = (min(self._prev_node, self._pending_node),
                        max(self._prev_node, self._pending_node))
            pts = edge_paths.get(_dot_key)
            if pts is None:
                src_side = port_sides.get((self._prev_node, self._pending_node), _SIDE_RIGHT)
                tgt_side = port_sides.get((self._pending_node, self._prev_node), _SIDE_LEFT)
                sp = _node_port(snx, sny, src_side)
                tp = _node_port(dnx, dny, tgt_side)
                pts = _edge_path(sp[0], sp[1], src_side, tp[0], tp[1], tgt_side, _obs_all)
            elif self._prev_node > self._pending_node:
                pts = list(reversed(pts))
            mx, my = _pos_along_path(pts, progress)
            self._draw_glow(screen, _COL_PLAYER, mx, my, 5, layers=2, max_alpha=120)
            pygame.draw.circle(screen, _COL_PLAYER, (mx, my), 5)

        # --- Nodes ---
        for node in nodes:
            if not node.active:
                continue
            nx, ny = self._node_screen_pos(node, panel)
            is_player   = (node.node_id == player)
            is_reachable = (node.node_id in reachable_ids)
            self._draw_node(screen, node, nx, ny, is_player, is_reachable)

            # Key badge
            if node.node_id in key_badges:
                self._draw_key_badge(screen, nx, ny, key_badges[node.node_id])

        # --- Destroyed loot nodes (active=False) — ghosted with red X ---
        for node in nodes:
            if node.active or node.ntype != NodeType.LOOT:
                continue
            nx, ny = self._node_screen_pos(node, panel)
            nr = _NODE_R
            rect = pygame.Rect(nx - nr, ny - nr, nr * 2, nr * 2)
            ghost = pygame.Surface((nr * 2, nr * 2), pygame.SRCALPHA)
            ghost.fill((30, 6, 6, 120))
            screen.blit(ghost, rect.topleft)
            pygame.draw.rect(screen, (80, 20, 20), rect, 1)
            r = 6
            pygame.draw.line(screen, (160, 30, 30), (nx - r, ny - r), (nx + r, ny + r), 2)
            pygame.draw.line(screen, (160, 30, 30), (nx + r, ny - r), (nx - r, ny + r), 2)
            lsurf = self._font_xs.render("CORRUPT", True, (100, 30, 30))
            screen.blit(lsurf, (nx - lsurf.get_width() // 2, ny + nr + 6))

        # --- Player pulse square + corner brackets ---
        pnode = nodes[player]
        px, py = self._node_screen_pos(pnode, panel)
        pulse = _PLAYER_R + int(_PULSE_AMP * math.sin(self._anim_time * 4.5))
        p_rect = pygame.Rect(px - pulse, py - pulse, pulse * 2, pulse * 2)
        pygame.draw.rect(screen, _COL_PLAYER, p_rect, 1)
        arm = 10
        for cx2, cy2, dx2, dy2 in (
            (p_rect.left,  p_rect.top,     1,  1),
            (p_rect.right, p_rect.top,    -1,  1),
            (p_rect.left,  p_rect.bottom,  1, -1),
            (p_rect.right, p_rect.bottom, -1, -1),
        ):
            pygame.draw.line(screen, _COL_PLAYER, (cx2, cy2), (cx2 + dx2 * arm, cy2), 2)
            pygame.draw.line(screen, _COL_PLAYER, (cx2, cy2), (cx2, cy2 + dy2 * arm), 2)

        # Hack progress bar under current LOOT node
        if self._state == _State.HACKING and nodes[player].ntype == NodeType.LOOT:
            ratio = 1.0 - self._hack_timer / self._params.hack_time
            bw = _NODE_R * 2 + 14
            bh = 6
            bx = px - bw // 2
            by = py + _NODE_R + 8
            pygame.draw.rect(screen, (20, 35, 48), (bx, by, bw, bh))
            fill_w = int(bw * ratio)
            if fill_w > 0:
                pygame.draw.rect(screen, _NEON_GREEN, (bx, by, fill_w, bh))
            pygame.draw.rect(screen, _NEON_GREEN, (bx, by, bw, bh), 1)

    def _draw_edge(
        self,
        screen: pygame.Surface,
        pts: list[tuple[int, int]],
        src_port: tuple[int, int],
        src_side: int,
        tgt_port: tuple[int, int],
        tgt_side: int,
        id_a: int, id_b: int,
        player: int,
        node_rects: dict[int, pygame.Rect],
    ) -> None:
        """Draw a pre-computed edge path with node-body clipping as safety fallback."""
        is_active_edge = (id_a == player or id_b == player)
        edge_color = _NEON_CYAN if is_active_edge else _COL_EDGE
        line_w     = 2 if is_active_edge else 1

        sx, sy = src_port
        tx, ty = tgt_port

        # Per-segment clipping:
        # - first segment:  don't clip source node (path starts at its border)
        # - last segment:   don't clip target node (path ends at its border)
        # - middle segments: clip against ALL nodes (catches re-entry into src/tgt)
        n_segs = len(pts) - 1
        for i in range(n_segs):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            is_first = (i == 0)
            is_last  = (i == n_segs - 1)
            clip = [r for nid, r in node_rects.items()
                    if not (is_first and nid == id_a)
                    and not (is_last  and nid == id_b)]
            for (ax, ay), (bx, by) in _clip_ortho_segment(x1, y1, x2, y2, clip):
                pygame.draw.line(screen, edge_color, (ax, ay), (bx, by), line_w)

        # Animated data packets travelling along the full path
        path_len = sum(
            math.hypot(pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1])
            for i in range(len(pts) - 1)
        )
        if path_len < 1:
            return

        packet_alpha = 200 if is_active_edge else 80
        for i in range(2):
            t  = ((self._anim_time * 0.6 + (id_a * 7 + id_b * 13) * 0.1 + i * 0.5)) % 1.0
            px, py = _pos_along_path(pts, t)
            dot_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*edge_color, packet_alpha), (4, 4), 3)
            screen.blit(dot_surf, (px - 4, py - 4))

    def _draw_node(
        self,
        screen: pygame.Surface,
        node: HackNode,
        nx: int, ny: int,
        is_player: bool,
        is_reachable: bool,
    ) -> None:
        base_color = _node_color(node)

        # Flash override
        if node.flash_timer > 0:
            t = node.flash_timer / 0.55
            base_color = tuple(int(base_color[i] + (_NEON_RED[i] - base_color[i]) * t) for i in range(3))

        nr   = _NODE_R
        rect = pygame.Rect(nx - nr, ny - nr, nr * 2, nr * 2)

        # Soft glow behind the square
        if is_player or is_reachable:
            glow_alpha = 90 if is_player else 50
            self._draw_glow(screen, base_color, nx, ny, nr, layers=2, max_alpha=glow_alpha)

        # Outer dashed reachable ring (1px square, inflated)
        if is_reachable and not is_player:
            outer = rect.inflate(10, 10)
            o_surf = pygame.Surface((outer.width, outer.height), pygame.SRCALPHA)
            pygame.draw.rect(o_surf, (*base_color, 55), o_surf.get_rect(), 1)
            screen.blit(o_surf, (outer.x, outer.y))

        # Fill
        fill = (base_color[0] // 5, base_color[1] // 5, base_color[2] // 5)
        pygame.draw.rect(screen, fill, rect)

        # Border
        border_w = 2 if (is_player or is_reachable) else 1
        pygame.draw.rect(screen, base_color, rect, border_w)

        # Inner decoration
        self._draw_node_icon(screen, node, nx, ny)

        # Type label below
        label = _node_label(node)
        if label:
            lsurf = self._font_xs.render(label, True,
                                          base_color if is_reachable else _TEXT_DIM)
            screen.blit(lsurf, (nx - lsurf.get_width() // 2, ny + nr + 6))

    def _draw_node_icon(self, screen: pygame.Surface, node: HackNode, cx: int, cy: int) -> None:
        """Blit main-game sprites (or simple geometry) inside a node square."""
        sz = _NODE_R * 2 - 4  # fits inside the node rect
        half = sz // 2

        if node.ntype == NodeType.ENTRY:
            r = 8
            pts = [(cx - r//2, cy - r), (cx + r, cy), (cx - r//2, cy + r)]
            surf = pygame.Surface((_NODE_R*2, _NODE_R*2), pygame.SRCALPHA)
            ox = _NODE_R
            pygame.draw.polygon(surf, (*_COL_ENTRY, 200),
                                [(p[0]-cx+ox, p[1]-cy+ox) for p in pts])
            screen.blit(surf, (cx - ox, cy - ox))
            return

        if node.ntype == NodeType.SECURITY:
            if not node.revealed:
                return
            # Revealed ICE: red X
            r = 7
            pygame.draw.line(screen, _COL_SEC_REV, (cx-r, cy-r), (cx+r, cy+r), 2)
            pygame.draw.line(screen, _COL_SEC_REV, (cx+r, cy-r), (cx-r, cy+r), 2)
            return

        if node.ntype != NodeType.LOOT:
            return

        if node.hacked:
            # Greyed-out checkmark
            r = 7
            pygame.draw.line(screen, _COL_LOOT_D, (cx-r//2, cy), (cx-r//5, cy+r//2), 2)
            pygame.draw.line(screen, _COL_LOOT_D, (cx-r//5, cy+r//2), (cx+r, cy-r//2), 2)
            return

        kind = node.loot_kind

        # ---- use main-game procedural sprites ----
        if kind in (LootKind.AMMO, LootKind.RIFLE_AMMO, LootKind.SHOTGUN_AMMO):
            spr = self._item_sprites.get("item_loot_ammo")
        elif kind in (LootKind.HEAL, LootKind.MEDKIT):
            spr = self._item_sprites.get("item_loot_consumable")
        elif kind == LootKind.WEAPON:
            spr = self._item_sprites.get("item_loot_ranged")
        else:
            spr = None

        if spr is not None:
            screen.blit(spr, (cx - half, cy - half))
            return

        # ---- fallback geometry for CREDITS and BONUS_TIME ----
        if kind == LootKind.CREDITS:
            color = (180, 220, 80)
            pygame.draw.line(screen, color, (cx-5, cy-2), (cx+5, cy-2), 2)
            pygame.draw.line(screen, color, (cx-5, cy+2), (cx+5, cy+2), 2)
            pygame.draw.line(screen, color, (cx, cy+2),   (cx, cy+7),   2)
            pygame.draw.line(screen, color, (cx-5, cy-7), (cx, cy-2),   2)
            pygame.draw.line(screen, color, (cx+5, cy-7), (cx, cy-2),   2)

        elif kind == LootKind.BONUS_TIME:
            color = (80, 180, 255)
            t_surf = self._font_bonus.render("+3s", True, color)
            screen.blit(t_surf, (cx - t_surf.get_width() // 2, cy - t_surf.get_height() // 2))

    def _draw_key_badge(self, screen: pygame.Surface, nx: int, ny: int, label: str) -> None:
        bsurf = self._font_xs.render(label, True, (0, 0, 0))
        bw = bsurf.get_width() + 8
        bh = bsurf.get_height() + 4
        bx = nx - _NODE_R - bw + 4
        by = ny - _NODE_R - bh + 4
        # Glow
        glow = pygame.Surface((bw + 8, bh + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*_NEON_YELLOW, 60), (0, 0, bw + 8, bh + 8), border_radius=4)
        screen.blit(glow, (bx - 4, by - 4))
        # Fill + border
        pygame.draw.rect(screen, _NEON_YELLOW, (bx, by, bw, bh), border_radius=3)
        pygame.draw.rect(screen, (255, 255, 180), (bx, by, bw, bh), 1, border_radius=3)
        screen.blit(bsurf, (bx + 4, by + 2))

    # ------------------------------------------------------------------
    # Draw — security effect overlay
    # ------------------------------------------------------------------

    def _draw_sec_overlay(self, screen: pygame.Surface, ov: dict) -> None:
        sw, sh = screen.get_size()
        color  = ov["color"]

        # Fade out over the last 0.4s
        t      = ov["timer"]
        fade   = min(1.0, t / 0.4) if t < 0.4 else 1.0

        # Edge vignette flash
        vig = pygame.Surface((sw, sh), pygame.SRCALPHA)
        depth = 80
        for i in range(depth):
            a = int(fade * 110 * (1.0 - i / depth) ** 1.5)
            if a <= 0:
                continue
            pygame.draw.rect(vig, (*color, a),
                             (i, i, sw - 2*i, sh - 2*i), 1)
        screen.blit(vig, (0, 0))

        # Central banner
        panel_h = 90
        panel_y = sh // 2 - panel_h // 2
        banner  = pygame.Surface((sw, panel_h), pygame.SRCALPHA)
        ba      = int(fade * 200)
        banner.fill((*color, min(ba, 38)))
        screen.blit(banner, (0, panel_y))
        # Banner border lines
        line_surf = pygame.Surface((sw, 2), pygame.SRCALPHA)
        line_surf.fill((*color, int(fade * 200)))
        screen.blit(line_surf, (0, panel_y))
        screen.blit(line_surf, (0, panel_y + panel_h - 2))

        # Main text
        main_surf = self._font_lg.render(ov["text"], True,
                                         tuple(int(c * fade + (1 - fade) * 40) for c in color))
        mx = sw // 2 - main_surf.get_width() // 2
        screen.blit(main_surf, (mx, panel_y + 14))

        # Sub text
        sub_surf = self._font_md.render(ov["sub"], True,
                                        tuple(int(c * fade * 0.7) for c in color))
        sx2 = sw // 2 - sub_surf.get_width() // 2
        screen.blit(sub_surf, (sx2, panel_y + 14 + main_surf.get_height() + 6))

    # ------------------------------------------------------------------
    # Draw — help overlay (F1)
    # ------------------------------------------------------------------

    def _draw_help_overlay(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        # Dim the game behind the panel
        dim = pygame.Surface((sw, sh), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 210))
        screen.blit(dim, (0, 0))

        # Panel: use most of the screen width, max 860px
        pw = min(sw - 60, 860)
        ph = 420
        px = (sw - pw) // 2
        py = (sh - ph) // 2

        pygame.draw.rect(screen, _PANEL_BG, (px, py, pw, ph))
        pygame.draw.rect(screen, _NEON_CYAN, (px, py, pw, ph), 1)
        _draw_corner_bracket(screen, px,      py,      50, 14, _NEON_CYAN, 1)
        _draw_corner_bracket(screen, px + pw, py,      50, 14, _NEON_CYAN, 1, flip_x=True)
        _draw_corner_bracket(screen, px,      py + ph, 50, 14, _NEON_CYAN, 1, flip_y=True)
        _draw_corner_bracket(screen, px + pw, py + ph, 50, 14, _NEON_CYAN, 1, flip_x=True, flip_y=True)

        # Title
        title_surf = self._font_lg.render("// INTRUSION PROTOCOL — HELP //", True, _NEON_CYAN)
        screen.blit(title_surf, (sw // 2 - title_surf.get_width() // 2, py + 14))
        sep_y = py + 14 + title_surf.get_height() + 6
        pygame.draw.line(screen, _NEON_CYAN, (px + 20, sep_y), (px + pw - 20, sep_y), 1)

        col_l = px + 26
        col_r = px + pw // 2 + 14
        y_l   = sep_y + 14
        y_r   = sep_y + 14
        lh    = 17    # normal line height
        lh2   = 13   # 2nd-line height (sub-description)
        font  = self._font_sm

        def _section(x: int, y: int, text: str) -> int:
            s = self._font_md.render(text, True, _NEON_CYAN)
            screen.blit(s, (x, y))
            return y + 20

        def _aligned(x: int, y: int,
                     items: list[tuple[str, tuple, str]]) -> int:
            """Single-line entries; descriptions auto-align at max-label-width."""
            if not items:
                return y
            gap    = 10
            col_dx = max(font.size(lbl)[0] for lbl, _, _ in items) + gap
            for lbl, lc, desc in items:
                screen.blit(font.render(lbl,  True, lc),    (x,          y))
                screen.blit(font.render(desc, True, _TEXT), (x + col_dx, y))
                y += lh
            return y

        def _two_line(x: int, y: int,
                      items: list[tuple[str, tuple, str]]) -> int:
            """Two-line entries: name (colored) + indented description below."""
            for name, nc, desc in items:
                screen.blit(font.render(name, True, nc),       (x + 2,  y))
                screen.blit(font.render(desc, True, _TEXT_DIM),(x + 18, y + lh - 2))
                y += lh + lh2
            return y

        def _bullets(x: int, y: int,
                     items: list[tuple[tuple, str]]) -> int:
            """Bulleted single-line entries."""
            for bc, text in items:
                b = font.render("• ", True, bc)
                screen.blit(b, (x, y))
                screen.blit(font.render(text, True, _TEXT), (x + b.get_width(), y))
                y += lh
            return y

        # ── Left column ──────────────────────────────────────────────
        y_l = _section(col_l, y_l, "NODE TYPES")
        y_l = _aligned(col_l, y_l, [
            ("►  ENTRY     ", _NEON_CYAN,   "your starting position"),
            ("▪  DATA CACHE", _NEON_GREEN,  "hack to extract loot"),
            ("▪  EMPTY     ", _COL_EMPTY,   "traversal only"),
            ("▪  ICE       ", _COL_SEC_HID, "hidden trap — looks like EMPTY!"),
        ])
        y_l += 10

        y_l = _section(col_l, y_l, "ICE EFFECTS  (triggered on entry)")
        y_l = _two_line(col_l, y_l, [
            ("✖  TIME PENALTY",   _NEON_RED,    "−3 seconds removed from the clock"),
            ("✖  DATA CORRUPTED", _NEON_ORANGE, "destroys a random unhacked loot node"),
            ("✖  ACCESS DENIED",  _NEON_RED,    "blocks entry — bounces you back"),
        ])

        # ── Right column ─────────────────────────────────────────────
        y_r = _section(col_r, y_r, "TIMER")
        y_r = _bullets(col_r, y_r, [
            (_TEXT_DIM,    "Starts on your first move"),
            (_TEXT_DIM,    "Bar at top: green → orange → red"),
            ((80,180,255), "BONUS TIME node: +3 seconds"),
            (_TEXT_DIM,    "Collect all data caches to finish early"),
        ])
        y_r += 10

        y_r = _section(col_r, y_r, "CONTROLS")
        y_r = _aligned(col_r, y_r, [
            ("W / A / S / D", _NEON_YELLOW, "move to adjacent node"),
            ("Arrow keys",    _NEON_YELLOW, "same as W A S D"),
            ("Mouse click",   _NEON_YELLOW, "click a neighbour to move"),
            ("ESC",           _NEON_YELLOW, "cancel extraction / abort hack"),
            ("F1",            _NEON_YELLOW, "toggle this help (timer paused)"),
        ])

        # Close hint
        close_surf = font.render("[F1]  Close help", True, _TEXT_DIM)
        screen.blit(close_surf, (sw // 2 - close_surf.get_width() // 2, py + ph - 22))

    # ------------------------------------------------------------------
    # Draw — result overlay
    # ------------------------------------------------------------------

    def _draw_result_overlay(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        if self._done_success:
            title  = "//  HACK COMPLETE  //"
            color  = _NEON_CYAN
            lines  = [i.name for i in self._result_items]
            if self._result_credits:
                lines.append(f"+¥{self._result_credits}")
            if not lines:
                lines = ["No data extracted."]
        else:
            title  = "//  TRACE COMPLETE — ALARM  //"
            color  = _NEON_RED
            lines  = ["Security drone dispatched!"]

        # Title glow
        t_surf = self._font_lg.render(title, True, color)
        tx = sw // 2 - t_surf.get_width() // 2
        ty = sh // 2 - 50
        self._draw_glow(screen, color, sw // 2, ty + 11, 60, layers=2, max_alpha=50)
        screen.blit(t_surf, (tx, ty))

        # Separator
        sep_y = ty + t_surf.get_height() + 8
        pygame.draw.line(screen, color, (sw//2 - 120, sep_y), (sw//2 + 120, sep_y), 1)

        for i, line in enumerate(lines):
            lsurf = self._font_md.render(line, True, _TEXT)
            screen.blit(lsurf, (sw // 2 - lsurf.get_width() // 2, sep_y + 14 + i * 22))


# ---------------------------------------------------------------------------
# Pure helpers — node visuals
# ---------------------------------------------------------------------------

def _node_color(node: HackNode) -> tuple:
    if node.ntype == NodeType.ENTRY:
        return _COL_ENTRY
    if node.ntype == NodeType.LOOT:
        return _COL_LOOT_D if node.hacked else _COL_LOOT
    if node.ntype == NodeType.SECURITY:
        # Unrevealed security nodes look like EMPTY — they're a surprise
        if not node.revealed:
            return _COL_EMPTY
        return _COL_SEC_REV
    return _COL_EMPTY


def _node_label(node: HackNode) -> str:
    if node.ntype == NodeType.ENTRY:
        return "ENTRY"
    if node.ntype == NodeType.LOOT:
        return "OK" if node.hacked else ""   # icon handles the type, label only on hacked
    if node.ntype == NodeType.SECURITY:
        if not node.revealed:
            return ""   # hidden — looks like empty
        return "ICE"
    return ""


# ---------------------------------------------------------------------------
# Port-based orthogonal routing helpers
# ---------------------------------------------------------------------------

_SIDE_TOP    = 0   # exits upward
_SIDE_RIGHT  = 1   # exits rightward
_SIDE_BOTTOM = 2   # exits downward
_SIDE_LEFT   = 3   # exits leftward

# Ideal angle (atan2 convention: y-down) for each side
_SIDE_IDEAL: list[float] = [-math.pi / 2, 0.0, math.pi / 2, math.pi]

# Unit-direction vectors for each side (screen coords, y-down)
_SIDE_DX = [0, 1, 0, -1]   # TOP, RIGHT, BOTTOM, LEFT
_SIDE_DY = [-1, 0, 1, 0]   # TOP, RIGHT, BOTTOM, LEFT

# Navigation — WSAD + arrows mapped to port sides, and badge labels
_KEY_TO_SIDE: dict[int, int] = {
    pygame.K_w: _SIDE_TOP,    pygame.K_UP:    _SIDE_TOP,
    pygame.K_d: _SIDE_RIGHT,  pygame.K_RIGHT: _SIDE_RIGHT,
    pygame.K_s: _SIDE_BOTTOM, pygame.K_DOWN:  _SIDE_BOTTOM,
    pygame.K_a: _SIDE_LEFT,   pygame.K_LEFT:  _SIDE_LEFT,
}
_SIDE_KEY_LABEL: dict[int, str] = {
    _SIDE_TOP: "W", _SIDE_RIGHT: "D", _SIDE_BOTTOM: "S", _SIDE_LEFT: "A",
}


def _assign_port_sides(node: HackNode, neighbors: list[HackNode]) -> dict[int, int]:
    """
    Assign each neighbor to a unique exit side of *node*.
    Returns {neighbor_id: side}.  At most 4 neighbors supported (max degree = 4).
    """
    if not neighbors:
        return {}

    def _adiff(a: float, b: float) -> float:
        return abs((a - b + math.pi) % (2 * math.pi) - math.pi)

    nb_angles = [(nb.node_id, math.atan2(nb.sy - node.sy, nb.sx - node.sx))
                 for nb in neighbors]
    # Process most-certain assignments first (smallest angular distance to
    # their best side), so a diagonal neighbor never "steals" a cardinal side
    # from a neighbor that clearly belongs to it.
    available = list(range(4))
    result: dict[int, int] = {}
    for nb_id, angle in sorted(nb_angles,
                                key=lambda x: min(_adiff(x[1], _SIDE_IDEAL[s])
                                                  for s in range(4))):
        best = min(available, key=lambda s: _adiff(angle, _SIDE_IDEAL[s]))
        result[nb_id] = best
        available.remove(best)
    return result


def _node_port(nx: int, ny: int, side: int) -> tuple[int, int]:
    """Screen midpoint of the given side of a node centred at (nx, ny)."""
    r = _NODE_R
    if side == _SIDE_TOP:    return (nx,     ny - r)
    if side == _SIDE_RIGHT:  return (nx + r, ny    )
    if side == _SIDE_BOTTOM: return (nx,     ny + r)
    return                          (nx - r, ny    )   # _SIDE_LEFT


def _edge_path(
    sx: int, sy: int, src_side: int,
    tx: int, ty: int, tgt_side: int,
    obstacle_rects: "list[pygame.Rect] | None" = None,
    routed_segs: "list[tuple[int,int,int,int]] | None" = None,
) -> list[tuple[int, int]]:
    """
    Orthogonal route from port (sx,sy) to port (tx,ty) with obstacle avoidance.

    Rules:
    - Exits and enters perpendicular from the centre of the node side.
    - Perpendicular stub of at least NODE_R at each end before any turn.
    - The route (excluding the two stubs) must not touch any obstacle_rect.
    - Max one connection per side is guaranteed by _assign_port_sides upstream.
    """
    MIN_STUB      = _NODE_R
    CLEAR_SELF    = _NODE_R  # src/tgt nodes: stub end sits on boundary → backward move blocked
    CLEAR_INTER   = 6        # intermediate nodes: small but visible gap from node body
    BYPASS_MARGIN = _NODE_R  # preferred visual clearance for bypass candidate positions

    if not obstacle_rects:
        obstacle_rects = []

    # Identify source / target node centres from their port positions.
    src_cx = sx - _SIDE_DX[src_side] * _NODE_R
    src_cy = sy - _SIDE_DY[src_side] * _NODE_R
    tgt_cx = tx - _SIDE_DX[tgt_side] * _NODE_R
    tgt_cy = ty - _SIDE_DY[tgt_side] * _NODE_R

    def _is_endpoint(r: "pygame.Rect") -> bool:
        return (abs(r.centerx - src_cx) <= 1 and abs(r.centery - src_cy) <= 1) or \
               (abs(r.centerx - tgt_cx) <= 1 and abs(r.centery - tgt_cy) <= 1)

    # Inflate: NODE_R for src/tgt (stub sits on boundary, doubling-back blocked);
    # 2 px for intermediates (allows routing through tight node gaps).
    obs = [r.inflate(CLEAR_SELF * 2, CLEAR_SELF * 2) if _is_endpoint(r)
           else r.inflate(CLEAR_INTER * 2, CLEAR_INTER * 2)
           for r in obstacle_rects]

    # Stub end-points: one step of MIN_STUB outward from each port.
    s1x = sx + _SIDE_DX[src_side] * MIN_STUB
    s1y = sy + _SIDE_DY[src_side] * MIN_STUB
    s2x = tx + _SIDE_DX[tgt_side] * MIN_STUB
    s2y = ty + _SIDE_DY[tgt_side] * MIN_STUB

    # ------------------------------------------------------------------
    def _seg_ok(x1: int, y1: int, x2: int, y2: int) -> bool:
        """True iff the axis-aligned segment does not intersect any obstacle."""
        if x1 == x2 and y1 == y2:
            return True
        for r in obs:
            if y1 == y2:   # horizontal
                if r.top < y1 < r.bottom:
                    if min(x1, x2) < r.right and max(x1, x2) > r.left:
                        return False
            else:           # vertical
                if r.left < x1 < r.right:
                    if min(y1, y2) < r.bottom and max(y1, y2) > r.top:
                        return False
        return True

    def _build(waypoints: "list[tuple[int,int]]") -> "list[tuple[int,int]]":
        """Assemble full path and strip consecutive duplicates."""
        raw = [(sx, sy), (s1x, s1y)] + waypoints + [(s2x, s2y), (tx, ty)]
        out = [raw[0]]
        for p in raw[1:]:
            if p != out[-1]:
                out.append(p)
        return out

    def _middle_ok(pts: "list[tuple[int,int]]") -> bool:
        """Check middle segments (skip first and last stub) against node obstacles."""
        for i in range(1, len(pts) - 2):
            if not _seg_ok(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]):
                return False
        return True

    PAR_GAP = _NODE_R   # minimum perpendicular distance between parallel segments

    def _parallel_ok(pts: "list[tuple[int,int]]") -> bool:
        """No middle segment runs parallel and within PAR_GAP of any routed segment."""
        if not routed_segs:
            return True
        for i in range(1, len(pts) - 2):
            x1, y1 = pts[i];  x2, y2 = pts[i + 1]
            for ex1, ey1, ex2, ey2 in routed_segs:
                if y1 == y2 and ey1 == ey2:          # both horizontal
                    if abs(y1 - ey1) < PAR_GAP:
                        lo1, hi1 = min(x1, x2), max(x1, x2)
                        lo2, hi2 = min(ex1, ex2), max(ex1, ex2)
                        if lo1 < hi2 and lo2 < hi1:
                            return False
                elif x1 == x2 and ex1 == ex2:         # both vertical
                    if abs(x1 - ex1) < PAR_GAP:
                        lo1, hi1 = min(y1, y2), max(y1, y2)
                        lo2, hi2 = min(ey1, ey2), max(ey1, ey2)
                        if lo1 < hi2 and lo2 < hi1:
                            return False
        return True

    # ------------------------------------------------------------------
    # Build bypass offsets from every obstacle edge and every routed segment.
    bypass_ys: list[int] = []
    bypass_xs: list[int] = []
    for r in obstacle_rects:
        bypass_ys += [r.top  - BYPASS_MARGIN - 1, r.bottom + BYPASS_MARGIN + 1]
        bypass_xs += [r.left - BYPASS_MARGIN - 1, r.right  + BYPASS_MARGIN + 1]
    for ex1, ey1, ex2, ey2 in (routed_segs or []):
        if ey1 == ey2:    bypass_ys += [ey1 - PAR_GAP, ey1 + PAR_GAP]
        elif ex1 == ex2:  bypass_xs += [ex1 - PAR_GAP, ex1 + PAR_GAP]
    mid_y = (s1y + s2y) // 2
    mid_x = (s1x + s2x) // 2
    # Clamp bypass candidates to a window around the source–target bounding box
    # (BYPASS_MARGIN extra on each side) so the router doesn't emit large loops.
    _PAD   = BYPASS_MARGIN * 3
    _by_lo = min(s1y, s2y) - _PAD;  _by_hi = max(s1y, s2y) + _PAD
    _bx_lo = min(s1x, s2x) - _PAD;  _bx_hi = max(s1x, s2x) + _PAD
    bypass_ys = [v for v in bypass_ys if _by_lo <= v <= _by_hi]
    bypass_xs = [v for v in bypass_xs if _bx_lo <= v <= _bx_hi]
    bypass_ys.sort(key=lambda v: abs(v - mid_y))
    bypass_xs.sort(key=lambda v: abs(v - mid_x))

    # ------------------------------------------------------------------
    # Candidate middle waypoints (order = preference, simplest first).
    candidates: list[list[tuple[int, int]]] = []

    # 1. Straight connection (only if stubs are already co-linear)
    if s1x == s2x or s1y == s2y:
        candidates.append([])

    # 2. One-bend L-routes
    candidates.append([(s2x, s1y)])
    candidates.append([(s1x, s2y)])

    # 3. Two-bend Z/U routes around blocking nodes and routed segments
    for by in bypass_ys:
        candidates.append([(s1x, by), (s2x, by)])
    for bx in bypass_xs:
        candidates.append([(bx, s1y), (bx, s2y)])

    for waypoints in candidates:
        pts = _build(waypoints)
        if _middle_ok(pts) and _parallel_ok(pts):
            return pts

    # Fallback: choose the L-route whose first segment is perpendicular to
    # the source exit direction so the path goes *away* from the source node
    # before turning — prevents visually doubling back into it.
    # For LEFT/RIGHT exits: go vertical first (x stays at s1x, y changes).
    # For TOP/BOTTOM exits: go horizontal first (y stays at s1y, x changes).
    # Still respect the parallel-gap constraint where possible.
    if src_side in (_SIDE_LEFT, _SIDE_RIGHT):
        options = [[(s1x, s2y)], [(s2x, s1y)]]
    else:
        options = [[(s2x, s1y)], [(s1x, s2y)]]
    # Both constraints
    for waypoints in options:
        pts = _build(waypoints)
        if _middle_ok(pts) and _parallel_ok(pts):
            return pts
    # Relax parallel — still must not pass through nodes or double back
    for waypoints in options:
        pts = _build(waypoints)
        if _middle_ok(pts):
            return pts
    # Truly last resort: BFS pathfinding on a grid (guaranteed to avoid nodes).
    bfs_mid = _bfs_ortho_route(
        s1x, s1y, s2x, s2y, obstacle_rects,
        src_cx, src_cy, tgt_cx, tgt_cy,
    )
    if bfs_mid is not None:
        raw = [(sx, sy), (s1x, s1y)] + bfs_mid + [(s2x, s2y), (tx, ty)]
        out = [raw[0]]
        for p in raw[1:]:
            if p != out[-1]:
                out.append(p)
        return out
    # No valid path at all — direct stubs (visual clipping hides node body).
    return _build(options[0])


# ---------------------------------------------------------------------------
# Grid-based BFS fallback router (0-1 BFS minimising turns)
# ---------------------------------------------------------------------------

def _bfs_ortho_route(
    s1x: int, s1y: int, s2x: int, s2y: int,
    obstacle_rects: "list[pygame.Rect]",
    src_cx: int, src_cy: int, tgt_cx: int, tgt_cy: int,
) -> "list[tuple[int,int]] | None":
    """
    0-1 BFS on a pixel grid that finds an orthogonal path from (s1x,s1y) to
    (s2x,s2y) with the fewest turns, guaranteed to avoid all obstacle rects.
    Returns the middle waypoints (between the two stub endpoints) or *None*.
    """
    from collections import deque as _deque

    CELL       = _NODE_R // 3 or 4   # grid resolution (6 px for NODE_R=18)
    CLEAR      = 6                    # clearance from intermediate nodes
    CLEAR_SELF = _NODE_R              # clearance from src/tgt nodes
    PAD        = _NODE_R * 4          # grid padding around all obstacles

    if not obstacle_rects:
        return [(s1x, s1y), (s2x, s2y)]

    # --- grid bounds -----------------------------------------------------
    all_xs = [r.left for r in obstacle_rects] + [r.right for r in obstacle_rects]
    all_ys = [r.top  for r in obstacle_rects] + [r.bottom for r in obstacle_rects]
    gx0 = min(*all_xs, s1x, s2x) - PAD
    gy0 = min(*all_ys, s1y, s2y) - PAD
    gx1 = max(*all_xs, s1x, s2x) + PAD
    gy1 = max(*all_ys, s1y, s2y) + PAD
    cols = (gx1 - gx0) // CELL + 2
    rows = (gy1 - gy0) // CELL + 2

    # --- blocked cells ---------------------------------------------------
    blocked: set[tuple[int,int]] = set()
    for r in obstacle_rects:
        is_ep = (abs(r.centerx - src_cx) <= 1 and abs(r.centery - src_cy) <= 1) or \
                (abs(r.centerx - tgt_cx) <= 1 and abs(r.centery - tgt_cy) <= 1)
        cl = CLEAR_SELF if is_ep else CLEAR
        inf = r.inflate(cl * 2, cl * 2)
        c0 = max(0, (inf.left  - gx0) // CELL)
        c1 = min(cols, (inf.right  - gx0 + CELL - 1) // CELL + 1)
        r0 = max(0, (inf.top   - gy0) // CELL)
        r1 = min(rows, (inf.bottom - gy0 + CELL - 1) // CELL + 1)
        for ry in range(r0, r1):
            for cx in range(c0, c1):
                blocked.add((cx, ry))

    start = ((s1x - gx0) // CELL, (s1y - gy0) // CELL)
    end   = ((s2x - gx0) // CELL, (s2y - gy0) // CELL)
    blocked.discard(start)
    blocked.discard(end)

    # --- 0-1 BFS (cost = number of turns) --------------------------------
    _DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))   # U R D L
    INF   = float("inf")
    best:   dict[tuple[int,int,int], float]                    = {}
    parent: dict[tuple[int,int,int], tuple[int,int,int] | None] = {}
    q = _deque()

    for d in range(4):
        st = (start[0], start[1], d)
        best[st]   = 0
        parent[st] = None
        q.append((0, st))

    found_state = None
    while q:
        cost, state = q.popleft()
        if cost > best.get(state, INF):
            continue                         # stale entry
        cx, cy, cd = state
        if (cx, cy) == end:
            found_state = state
            break
        for nd in range(4):
            dx, dy = _DIRS[nd]
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if (nx, ny) in blocked:
                continue
            tc = 0 if nd == cd else 1
            nc = cost + tc
            ns = (nx, ny, nd)
            if nc < best.get(ns, INF):
                best[ns]   = nc
                parent[ns] = state
                if tc == 0:
                    q.appendleft((nc, ns))
                else:
                    q.append((nc, ns))

    if found_state is None:
        return None

    # --- reconstruct & simplify ------------------------------------------
    path: list[tuple[int,int]] = []
    st: tuple[int,int,int] | None = found_state
    while st is not None:
        path.append((gx0 + st[0] * CELL + CELL // 2,
                      gy0 + st[1] * CELL + CELL // 2))
        st = parent[st]
    path.reverse()

    # merge collinear runs
    if len(path) <= 2:
        path[0]  = (s1x, s1y)
        path[-1] = (s2x, s2y)
        return path
    simple = [path[0]]
    for i in range(1, len(path) - 1):
        px, py = simple[-1]
        cx, cy = path[i]
        nx, ny = path[i + 1]
        if (px == cx == nx) or (py == cy == ny):
            continue
        simple.append(path[i])
    simple.append(path[-1])
    # snap endpoints to actual stub positions
    simple[0]  = (s1x, s1y)
    simple[-1] = (s2x, s2y)
    return simple


def _clip_ortho_segment(
    x1: int, y1: int, x2: int, y2: int,
    skip_rects: list[pygame.Rect],
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """
    Split an axis-aligned segment into sub-segments that avoid *skip_rects*.
    Returns list of ((ax,ay),(bx,by)) pairs safe to draw.
    """
    if y1 == y2:  # horizontal
        lo, hi = (x1, x2) if x1 <= x2 else (x2, x1)
        gaps: list[tuple[int, int]] = []
        for r in skip_rects:
            if r.top < y1 < r.bottom:
                gx1, gx2 = max(lo, r.left), min(hi, r.right)
                if gx1 < gx2:
                    gaps.append((gx1, gx2))
        if not gaps:
            return [((x1, y1), (x2, y2))]
        gaps.sort()
        result, cur = [], lo
        for g0, g1 in gaps:
            if cur < g0:
                a, b = (cur, y1), (g0, y1)
                result.append((a, b) if x1 <= x2 else (b, a))
            cur = max(cur, g1)
        if cur < hi:
            a, b = (cur, y1), (hi, y1)
            result.append((a, b) if x1 <= x2 else (b, a))
        return result

    else:  # vertical
        lo, hi = (y1, y2) if y1 <= y2 else (y2, y1)
        gaps = []
        for r in skip_rects:
            if r.left < x1 < r.right:
                gy1, gy2 = max(lo, r.top), min(hi, r.bottom)
                if gy1 < gy2:
                    gaps.append((gy1, gy2))
        if not gaps:
            return [((x1, y1), (x2, y2))]
        gaps.sort()
        result, cur = [], lo
        for g0, g1 in gaps:
            if cur < g0:
                a, b = (x1, cur), (x1, g0)
                result.append((a, b) if y1 <= y2 else (b, a))
            cur = max(cur, g1)
        if cur < hi:
            a, b = (x1, cur), (x1, hi)
            result.append((a, b) if y1 <= y2 else (b, a))
        return result


def _pos_along_path(pts: list[tuple[int, int]], t: float) -> tuple[int, int]:
    """Return the point at fractional distance t ∈ [0, 1] along a polyline."""
    seg_lens: list[float] = []
    total = 0.0
    for i in range(len(pts) - 1):
        d = math.hypot(pts[i+1][0] - pts[i][0], pts[i+1][1] - pts[i][1])
        seg_lens.append(d)
        total += d
    if total == 0:
        return pts[0]
    target = t * total
    acc    = 0.0
    for i, seg_len in enumerate(seg_lens):
        if acc + seg_len >= target or i == len(seg_lens) - 1:
            if seg_len == 0:
                return pts[i]
            local_t = max(0.0, min(1.0, (target - acc) / seg_len))
            return (
                int(pts[i][0] + (pts[i+1][0] - pts[i][0]) * local_t),
                int(pts[i][1] + (pts[i+1][1] - pts[i][1]) * local_t),
            )
        acc += seg_len
    return pts[-1]


def _draw_corner_bracket(
    screen: pygame.Surface,
    x: int, y: int,
    arm: int, thickness: int,
    color: tuple,
    width: int,
    flip_x: bool = False,
    flip_y: bool = False,
) -> None:
    """Draw an L-shaped corner bracket at (x, y)."""
    dx = -1 if flip_x else 1
    dy = -1 if flip_y else 1
    # Horizontal arm
    pygame.draw.line(screen, color, (x, y), (x + dx * arm, y), width)
    # Vertical arm
    pygame.draw.line(screen, color, (x, y), (x, y + dy * thickness), width)


# ---------------------------------------------------------------------------
# Pure helpers — loot items
# ---------------------------------------------------------------------------

def _make_loot_item(kind: LootKind) -> Optional["Item"]:
    import random as _r
    from dungeoneer.items.ammo import make_9mm_ammo, make_rifle_ammo, make_shotgun_ammo
    from dungeoneer.items.consumable import make_stim_pack, make_medkit
    from dungeoneer.items.weapon import make_shotgun, make_rifle, make_smg

    if kind == LootKind.AMMO:         return make_9mm_ammo(8)
    if kind == LootKind.RIFLE_AMMO:   return make_rifle_ammo(3)
    if kind == LootKind.SHOTGUN_AMMO: return make_shotgun_ammo(4)
    if kind == LootKind.HEAL:         return make_stim_pack()
    if kind == LootKind.MEDKIT:       return make_medkit()
    if kind == LootKind.WEAPON:       return _r.choice([make_shotgun, make_rifle, make_smg])()
    return None
