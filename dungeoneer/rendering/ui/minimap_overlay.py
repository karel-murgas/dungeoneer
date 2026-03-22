"""Minimap overlay — toggle with M key.

Renders a simplified top-down view of the dungeon the player has explored so far.
Uses solid-colour rectangles (no textures).

Legend:
  - Dark grey: explored wall
  - Medium grey: explored floor
  - Black: unexplored (fog of war)
  - Cyan: player position
  - Red: visible enemies
  - Yellow: unopened containers (chests)
  - Blue: elevator / vault
  - Dim coloured dots: items on floor (only in explored area)
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.world.tile import TileType

if TYPE_CHECKING:
    from dungeoneer.world.floor import Floor
    from dungeoneer.entities.player import Player

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

_BG        = (6, 6, 14, 230)
_BORDER    = (60, 200, 160)
_TITLE_COL = (0, 220, 180)

_COL_UNEXPLORED = (6, 6, 14)
_COL_WALL       = (35, 35, 50)
_COL_FLOOR      = (55, 50, 65)
_COL_FLOOR_VIS  = (75, 68, 85)       # currently visible floor (slightly brighter)

_COL_PLAYER     = (0, 220, 180)      # cyan
_COL_ENEMY      = (220, 60, 60)      # red
_COL_CONTAINER  = (240, 210, 40)     # yellow
_COL_ELEVATOR   = (40, 120, 220)     # blue
_COL_VAULT      = (40, 120, 220)     # blue (same as elevator — objective marker)
_COL_ITEM       = (160, 150, 60, 160)  # dim yellow

_LEGEND_COL     = (140, 150, 165)
_LEGEND_KEY_COL = (80, 200, 170)

_PAD    = 16
_MARGIN = 24      # gap between panel edge and screen edge


class MinimapOverlay:
    """Full-screen minimap overlay."""

    def __init__(self) -> None:
        self._font_title = pygame.font.SysFont("consolas", 20, bold=True)
        self._font_legend = pygame.font.SysFont("consolas", 13)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, floor: "Floor", player: "Player") -> None:
        sw, sh = screen.get_size()
        dmap = floor.dungeon_map

        # --- panel size ---------------------------------------------------
        panel_w = sw - _MARGIN * 2
        panel_h = sh - _MARGIN * 2

        # --- background ---------------------------------------------------
        bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        bg.fill(_BG)
        pygame.draw.rect(bg, _BORDER, bg.get_rect(), 1, border_radius=4)

        # --- title --------------------------------------------------------
        title_surf = self._font_title.render(t("minimap.title"), True, _TITLE_COL)
        title_y = _PAD
        bg.blit(title_surf, ((panel_w - title_surf.get_width()) // 2, title_y))

        # --- compute cell size to fit map in available space --------------
        content_top = title_y + title_surf.get_height() + 8
        legend_h = 20
        avail_w = panel_w - _PAD * 2
        avail_h = panel_h - content_top - _PAD - legend_h - 4

        cell_w = avail_w / dmap.width
        cell_h = avail_h / dmap.height
        cell = min(cell_w, cell_h)
        # Clamp to at least 2px so tiles are always visible
        cell = max(cell, 2.0)

        map_px_w = int(cell * dmap.width)
        map_px_h = int(cell * dmap.height)
        ox = _PAD + (avail_w - map_px_w) // 2
        oy = content_top + (avail_h - map_px_h) // 2

        # --- draw tiles ---------------------------------------------------
        map_surf = pygame.Surface((map_px_w, map_px_h))
        map_surf.fill(_COL_UNEXPLORED)

        for ty in range(dmap.height):
            for tx in range(dmap.width):
                if not dmap.explored[ty, tx]:
                    continue
                px = int(tx * cell)
                py = int(ty * cell)
                pw = max(1, int((tx + 1) * cell) - px)
                ph = max(1, int((ty + 1) * cell) - py)

                tile_type = dmap.get_type(tx, ty)
                if tile_type == TileType.WALL:
                    col = _COL_WALL
                elif tile_type in (TileType.ELEVATOR_CLOSED, TileType.ELEVATOR_OPEN):
                    col = _COL_ELEVATOR
                elif dmap.visible[ty, tx]:
                    col = _COL_FLOOR_VIS
                else:
                    col = _COL_FLOOR
                map_surf.fill(col, (px, py, pw, ph))

        # --- draw items on floor (explored tiles only) --------------------
        item_surf = pygame.Surface((map_px_w, map_px_h), pygame.SRCALPHA)
        for item_e in floor.item_entities:
            if not dmap.explored[item_e.y, item_e.x]:
                continue
            if not dmap.visible[item_e.y, item_e.x]:
                continue
            cx = int((item_e.x + 0.5) * cell)
            cy = int((item_e.y + 0.5) * cell)
            r = max(1, int(cell * 0.25))
            pygame.draw.circle(item_surf, _COL_ITEM, (cx, cy), r)
        map_surf.blit(item_surf, (0, 0))

        # --- draw containers (unopened only) ------------------------------
        for container in floor.containers:
            if container.opened:
                continue
            if not dmap.explored[container.y, container.x]:
                continue
            px = int(container.x * cell)
            py = int(container.y * cell)
            pw = max(1, int((container.x + 1) * cell) - px)
            ph = max(1, int((container.y + 1) * cell) - py)
            if getattr(container, "is_objective", False):
                col = _COL_VAULT
            else:
                col = _COL_CONTAINER
            map_surf.fill(col, (px, py, pw, ph))

        # --- draw visible enemies -----------------------------------------
        for actor in floor.actors:
            if actor is player:
                continue
            if not actor.alive:
                continue
            if not dmap.visible[actor.y, actor.x]:
                continue
            px = int(actor.x * cell)
            py = int(actor.y * cell)
            pw = max(1, int((actor.x + 1) * cell) - px)
            ph = max(1, int((actor.y + 1) * cell) - py)
            map_surf.fill(_COL_ENEMY, (px, py, pw, ph))

        # --- draw player --------------------------------------------------
        px = int(player.x * cell)
        py = int(player.y * cell)
        pw = max(1, int((player.x + 1) * cell) - px)
        ph = max(1, int((player.y + 1) * cell) - py)
        map_surf.fill(_COL_PLAYER, (px, py, pw, ph))

        bg.blit(map_surf, (ox, oy))

        # --- legend -------------------------------------------------------
        legend_y = oy + map_px_h + 4
        legend_items = [
            (_COL_PLAYER, t("minimap.legend.player")),
            (_COL_ENEMY, t("minimap.legend.enemy")),
            (_COL_CONTAINER, t("minimap.legend.container")),
            (_COL_ELEVATOR, t("minimap.legend.elevator")),
        ]
        lx = _PAD
        for col, label in legend_items:
            # colour swatch
            pygame.draw.rect(bg, col, (lx, legend_y + 2, 10, 10))
            lx += 14
            lbl = self._font_legend.render(label, True, _LEGEND_COL)
            bg.blit(lbl, (lx, legend_y))
            lx += lbl.get_width() + 16

        # Close hint on the right
        hint = self._font_legend.render(t("minimap.hint_close"), True, _LEGEND_KEY_COL)
        bg.blit(hint, (panel_w - _PAD - hint.get_width(), legend_y))

        # --- blit panel to screen -----------------------------------------
        screen.blit(bg, (_MARGIN, _MARGIN))
