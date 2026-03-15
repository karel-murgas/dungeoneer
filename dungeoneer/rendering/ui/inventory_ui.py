"""Inventory overlay — drawn on top of the game when player presses I."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.items.item import ItemType, RangeType
from dungeoneer.items.weapon import Weapon
from dungeoneer.items.consumable import Consumable


_W           = 520
_H           = 380
_PAD         = 16
_ROW_H       = 32
_VISIBLE_ROWS = 7   # max rows shown at once; scroll if more
_BG      = (14, 14, 24, 220)
_BORDER  = (60, 200, 160)
_SEL_BG  = (30, 80, 70)
_COL_EQ  = (80, 220, 180)
_COL_WPN = (180, 200, 255)
_COL_CON = (100, 220, 100)
_COL_DIM = (100, 100, 120)
_COL_KEY = (80, 100, 120)


class InventoryUI:
    def __init__(self) -> None:
        self._font      = pygame.font.SysFont("consolas", 16, bold=False)
        self._font_bold = pygame.font.SysFont("consolas", 16, bold=True)
        self._font_hdr  = pygame.font.SysFont("consolas", 18, bold=True)
        self._selected  = 0
        self._surf: pygame.Surface | None = None   # cached background panel

    # ------------------------------------------------------------------
    # Input handling (called by GameScene when inventory is open)
    # Returns an action or None
    # ------------------------------------------------------------------

    def handle_key(self, key: int, player: "Player") -> "Action | None":  # type: ignore[name-defined]
        from dungeoneer.combat.action import EquipAction, UseItemAction, DropItemAction

        items = list(player.inventory)
        n     = len(items)

        if key in (pygame.K_UP, pygame.K_w):
            self._selected = max(0, self._selected - 1)
            return None
        if key in (pygame.K_DOWN, pygame.K_s):
            self._selected = min(n - 1, self._selected + 1) if n else 0
            return None

        if n == 0:
            return None

        self._selected = min(self._selected, n - 1)
        item = items[self._selected]

        if key == pygame.K_e and isinstance(item, Weapon):
            return EquipAction(item)
        if key == pygame.K_u and isinstance(item, Consumable):
            return UseItemAction(item)
        if key == pygame.K_d:
            return DropItemAction(item)
        return None

    def clamp_selection(self, player: "Player") -> None:  # type: ignore[name-defined]
        n = len(player.inventory)
        if n == 0:
            self._selected = 0
        else:
            self._selected = min(self._selected, n - 1)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ox = (sw - _W) // 2
        oy = (sh - _H) // 2

        # Semi-transparent panel
        panel = pygame.Surface((_W, _H), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, _H), 2)

        items = list(player.inventory)
        n     = len(items)
        self.clamp_selection(player)

        # --- Header ---
        hdr = self._font_hdr.render(
            f"INVENTORY  {n}/{player.inventory._Inventory__class_max() if hasattr(player.inventory, '_Inventory__class_max') else 8}",
            True, _BORDER,
        )
        # Simpler: just use len
        hdr = self._font_hdr.render(
            f"INVENTORY  {n}/8", True, _BORDER,
        )
        screen.blit(hdr, (ox + _PAD, oy + _PAD))

        # --- Equipped weapon line ---
        eq_y = oy + _PAD + 28
        eq_label = self._font.render("EQUIPPED:", True, _COL_DIM)
        screen.blit(eq_label, (ox + _PAD, eq_y))
        if player.equipped_weapon:
            w = player.equipped_weapon
            eq_text = f"{w.name}   {w.stat_line()}"
            eq_surf  = self._font_bold.render(eq_text, True, _COL_EQ)
            screen.blit(eq_surf, (ox + _PAD + 90, eq_y))
        else:
            screen.blit(self._font.render("— none —", True, _COL_DIM), (ox + _PAD + 90, eq_y))

        pygame.draw.line(screen, (40, 60, 55), (ox + _PAD, eq_y + 22), (ox + _W - _PAD, eq_y + 22))

        # --- Item list ---
        list_y = eq_y + 30
        list_max_y = oy + _H - _PAD - 18 - 10  # stop before footer
        if n == 0:
            empty = self._font.render("(empty)", True, _COL_DIM)
            screen.blit(empty, (ox + _PAD, list_y))
        else:
            # Scroll window: show _VISIBLE_ROWS items around selection
            scroll_top = max(0, self._selected - _VISIBLE_ROWS + 1)
            scroll_top = min(scroll_top, max(0, n - _VISIBLE_ROWS))
            visible = items[scroll_top: scroll_top + _VISIBLE_ROWS]

            for vi, item in enumerate(visible):
                i = scroll_top + vi
                row_y = list_y + vi * _ROW_H
                if row_y + _ROW_H > list_max_y:
                    break
                # Selection highlight
                if i == self._selected:
                    pygame.draw.rect(screen, _SEL_BG, (ox + 4, row_y - 2, _W - 8, _ROW_H - 2))

                # Item colour
                col = _COL_WPN if isinstance(item, Weapon) else _COL_CON
                name_surf = self._font_bold.render(item.name, True, col)
                screen.blit(name_surf, (ox + _PAD, row_y + 4))

                # Stat line (right-aligned)
                stat = item.stat_line() if hasattr(item, "stat_line") else ""
                stat_surf = self._font.render(stat, True, _COL_DIM)
                screen.blit(stat_surf, (ox + _W - _PAD - stat_surf.get_width(), row_y + 4))

            # Scroll indicators
            if scroll_top > 0:
                up_surf = self._font.render("▲", True, _COL_DIM)
                screen.blit(up_surf, (ox + _W // 2 - up_surf.get_width() // 2, list_y - 14))
            if scroll_top + _VISIBLE_ROWS < n:
                down_y = list_y + min(_VISIBLE_ROWS, n) * _ROW_H
                down_surf = self._font.render("▼", True, _COL_DIM)
                screen.blit(down_surf, (ox + _W // 2 - down_surf.get_width() // 2, min(down_y, list_max_y)))

        # --- Footer hint ---
        footer_y = oy + _H - _PAD - 18
        pygame.draw.line(screen, (40, 60, 55), (ox + _PAD, footer_y - 6), (ox + _W - _PAD, footer_y - 6))
        hints = "[E] Equip   [U] Use   [D] Drop   [I/Esc] Close"
        hint_surf = self._font.render(hints, True, _COL_KEY)
        screen.blit(hint_surf, (ox + _PAD, footer_y))
