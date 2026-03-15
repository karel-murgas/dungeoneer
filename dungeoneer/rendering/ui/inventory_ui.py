"""Inventory overlay — drawn on top of the game when player presses I."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.items.item import ItemType, RangeType
from dungeoneer.items.weapon import Weapon
from dungeoneer.items.consumable import Consumable


_W            = 520
_H            = 390
_PAD          = 16
_ROW_H        = 32
_VISIBLE_ROWS = 7
_BG      = (14, 14, 24, 220)
_BORDER  = (60, 200, 160)
_SEL_BG  = (30, 80, 70)
_COL_EQ  = (80, 220, 180)
_COL_WPN = (180, 200, 255)
_COL_CON = (100, 220, 100)
_COL_DIM = (100, 100, 120)
_COL_KEY = (80, 100, 120)
_BTN_HOV = (40, 100, 85)
_BTN_NRM = (20, 35, 30)


class InventoryUI:
    def __init__(self) -> None:
        self._font      = pygame.font.SysFont("consolas", 16, bold=False)
        self._font_bold = pygame.font.SysFont("consolas", 16, bold=True)
        self._font_hdr  = pygame.font.SysFont("consolas", 18, bold=True)
        self._selected    = 0
        self._hovered_btn: str | None = None
        # Populated during draw(); used for mouse hit-testing
        self._item_rects: dict[int, pygame.Rect] = {}   # abs_index → row rect
        self._btn_rects:  dict[str, pygame.Rect] = {}   # "equip"|"use"|"drop"|"close" → rect

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def handle_key(self, key: int, player: "Player"):  # type: ignore[name-defined]
        """Returns an Action, 'close', or None."""
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

    # ------------------------------------------------------------------
    # Mouse input
    # ------------------------------------------------------------------

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        """Update selection on hover; track which footer button is hovered."""
        for idx, rect in self._item_rects.items():
            if rect.collidepoint(pos):
                self._selected = idx
                break
        hov = None
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                hov = name
                break
        self._hovered_btn = hov

    def handle_mouse_button(self, event: pygame.event.Event, player: "Player"):  # type: ignore[name-defined]
        """Returns an Action, 'close', or None."""
        from dungeoneer.combat.action import EquipAction, UseItemAction, DropItemAction

        items = list(player.inventory)
        n     = len(items)

        if event.button == 1:  # left click
            # Footer buttons take priority
            for name, rect in self._btn_rects.items():
                if rect.collidepoint(event.pos):
                    if name == "close":
                        return "close"
                    if n == 0:
                        return None
                    self._selected = min(self._selected, n - 1)
                    item = items[self._selected]
                    if name == "equip" and isinstance(item, Weapon):
                        return EquipAction(item)
                    if name == "use" and isinstance(item, Consumable):
                        return UseItemAction(item)
                    if name == "drop":
                        return DropItemAction(item)
                    return None
            # Item row click — just selects, no action
            for idx, rect in self._item_rects.items():
                if rect.collidepoint(event.pos):
                    self._selected = idx
                    return None

        elif event.button == 3:  # right click on item row → drop
            for idx, rect in self._item_rects.items():
                if rect.collidepoint(event.pos):
                    self._selected = idx
                    if idx < n:
                        return DropItemAction(items[idx])

        return None

    # ------------------------------------------------------------------

    def clamp_selection(self, player: "Player") -> None:  # type: ignore[name-defined]
        n = len(player.inventory)
        self._selected = min(self._selected, n - 1) if n else 0

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ox = (sw - _W) // 2
        oy = (sh - _H) // 2

        panel = pygame.Surface((_W, _H), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, _H), 2)

        items = list(player.inventory)
        n     = len(items)
        self.clamp_selection(player)

        # --- Header ---
        hdr = self._font_hdr.render(f"INVENTORY  {n}/8", True, _BORDER)
        screen.blit(hdr, (ox + _PAD, oy + _PAD))

        # --- Equipped weapon line ---
        eq_y = oy + _PAD + 28
        screen.blit(self._font.render("EQUIPPED:", True, _COL_DIM), (ox + _PAD, eq_y))
        if player.equipped_weapon:
            w = player.equipped_weapon
            eq_surf = self._font_bold.render(f"{w.name}   {w.stat_line()}", True, _COL_EQ)
            screen.blit(eq_surf, (ox + _PAD + 90, eq_y))
        else:
            screen.blit(self._font.render("— none —", True, _COL_DIM), (ox + _PAD + 90, eq_y))

        pygame.draw.line(screen, (40, 60, 55), (ox + _PAD, eq_y + 22), (ox + _W - _PAD, eq_y + 22))

        # --- Item list ---
        list_y    = eq_y + 30
        footer_y  = oy + _H - _PAD - 26
        list_max_y = footer_y - 14

        self._item_rects = {}

        if n == 0:
            screen.blit(self._font.render("(empty)", True, _COL_DIM), (ox + _PAD, list_y))
        else:
            scroll_top = max(0, self._selected - _VISIBLE_ROWS + 1)
            scroll_top = min(scroll_top, max(0, n - _VISIBLE_ROWS))
            visible = items[scroll_top: scroll_top + _VISIBLE_ROWS]

            for vi, item in enumerate(visible):
                i     = scroll_top + vi
                row_y = list_y + vi * _ROW_H
                if row_y + _ROW_H > list_max_y:
                    break

                row_rect = pygame.Rect(ox + 4, row_y - 2, _W - 8, _ROW_H - 2)
                self._item_rects[i] = row_rect

                if i == self._selected:
                    pygame.draw.rect(screen, _SEL_BG, row_rect)

                col = _COL_WPN if isinstance(item, Weapon) else _COL_CON

                stat      = item.stat_line() if hasattr(item, "stat_line") else ""
                stat_surf = self._font.render(stat, True, _COL_DIM)
                stat_x    = ox + _W - _PAD - stat_surf.get_width()

                name_max_w = stat_x - _PAD - (ox + _PAD)
                name_s = self._font_bold.render(item.name, True, col)
                if name_s.get_width() > name_max_w:
                    name_s = name_s.subsurface((0, 0, name_max_w, name_s.get_height()))
                screen.blit(name_s, (ox + _PAD, row_y + 4))
                screen.blit(stat_surf, (stat_x, row_y + 4))

            if scroll_top > 0:
                up_s = self._font.render("▲", True, _COL_DIM)
                screen.blit(up_s, (ox + _W // 2 - up_s.get_width() // 2, list_y - 14))
            if scroll_top + _VISIBLE_ROWS < n:
                down_y = list_y + min(_VISIBLE_ROWS, n) * _ROW_H
                down_s = self._font.render("▼", True, _COL_DIM)
                screen.blit(down_s, (ox + _W // 2 - down_s.get_width() // 2, min(down_y, list_max_y)))

        # --- Footer buttons ---
        pygame.draw.line(screen, (40, 60, 55),
                         (ox + _PAD, footer_y - 6), (ox + _W - _PAD, footer_y - 6))

        self._btn_rects = {}
        btn_defs = [
            ("equip", "[E] Equip"),
            ("use",   "[U] Use"),
            ("drop",  "[D] Drop"),
            ("close", "[I] Close"),
        ]
        bx = ox + _PAD
        for key, label in btn_defs:
            lbl_w = self._font.size(label)[0]
            btn_w = lbl_w + 14
            rect  = pygame.Rect(bx, footer_y - 2, btn_w, 22)
            self._btn_rects[key] = rect
            is_hov = self._hovered_btn == key
            pygame.draw.rect(screen, _BTN_HOV if is_hov else _BTN_NRM, rect)
            pygame.draw.rect(screen, _BORDER if is_hov else (45, 70, 60), rect, 1)
            col = (180, 220, 200) if is_hov else _COL_KEY
            screen.blit(self._font.render(label, True, col), (bx + 7, footer_y))
            bx += btn_w + 8
