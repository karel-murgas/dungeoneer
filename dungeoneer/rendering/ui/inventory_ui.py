"""Inventory overlay — drawn on top of the game when player presses I."""
from __future__ import annotations

import os

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.items.item import ItemType, RangeType
from dungeoneer.items.weapon import Weapon
from dungeoneer.items.consumable import Consumable


_W            = 520
_H            = 390
_PAD          = 16
_ROW_H        = 32
_ICON_SIZE    = 26   # weapon icon px in item list (fits in _ROW_H with 3px margin)
_EQUIP_ICON   = 36   # larger icon for the equipped weapon detail area
_AMMO_BADGE   = 18   # ammo badge overlaid on bottom-right corner of weapon icon

_ASSETS_ITEMS = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "items")
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
        self._btn_rects:  dict[str, pygame.Rect] = {}   # "use"|"close" → rect
        self.help_btn_rect: pygame.Rect | None = None   # [?] items help button

        # Item icons keyed by "{itemtype}_{id}" — loaded on first use, scaled to _ICON_SIZE
        # Convention: assets/items/{item.item_type.name.lower()}_{item.id}.png
        self._item_icons:  dict[str, pygame.Surface | None] = {}
        # Larger icons for the equipped-weapon detail area, scaled to _EQUIP_ICON
        self._equip_icons: dict[str, pygame.Surface | None] = {}

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def handle_key(self, key: int, player: "Player"):  # type: ignore[name-defined]
        """Returns an Action, 'close', or None."""
        from dungeoneer.combat.action import EquipAction, UseItemAction

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

        if key in (pygame.K_e, pygame.K_RETURN, pygame.K_KP_ENTER):
            if isinstance(item, Weapon):
                return EquipAction(item)
            if isinstance(item, Consumable):
                return UseItemAction(item)
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
        if self.help_btn_rect and self.help_btn_rect.collidepoint(pos):
            hov = "help"
        else:
            for name, rect in self._btn_rects.items():
                if rect.collidepoint(pos):
                    hov = name
                    break
        self._hovered_btn = hov

    def handle_mouse_button(self, event: pygame.event.Event, player: "Player"):  # type: ignore[name-defined]
        """Returns an Action, 'close', or None."""
        from dungeoneer.combat.action import EquipAction, UseItemAction

        items = list(player.inventory)
        n     = len(items)

        if event.button == 1:  # left click
            # Help button
            if self.help_btn_rect and self.help_btn_rect.collidepoint(event.pos):
                return "help"
            # Footer buttons take priority
            for name, rect in self._btn_rects.items():
                if rect.collidepoint(event.pos):
                    if name == "close":
                        return "close"
                    if n == 0:
                        return None
                    self._selected = min(self._selected, n - 1)
                    item = items[self._selected]
                    if name == "use":
                        if isinstance(item, Weapon):
                            return EquipAction(item)
                        if isinstance(item, Consumable):
                            return UseItemAction(item)
                    return None
            # Item row click — select and use/equip immediately
            for idx, rect in self._item_rects.items():
                if rect.collidepoint(event.pos):
                    self._selected = idx
                    if idx < n:
                        item = items[idx]
                        if isinstance(item, Weapon):
                            return EquipAction(item)
                        if isinstance(item, Consumable):
                            return UseItemAction(item)
                    return None

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
        hdr = self._font_hdr.render(t("inv.title").format(n=n), True, _BORDER)
        screen.blit(hdr, (ox + _PAD, oy + _PAD))

        # --- Equipped weapon line ---
        eq_y = oy + _PAD + 28
        screen.blit(self._font.render(t("inv.weapon_label"), True, _COL_DIM), (ox + _PAD, eq_y))
        if player.equipped_weapon:
            w = player.equipped_weapon
            eq_surf = self._font_bold.render(f"{w.name}   {w.stat_line()}", True, _COL_EQ)
            screen.blit(eq_surf, (ox + _PAD + 75, eq_y))
            # Large icons to the right: weapon icon, then ammo icon to its left (ranged only)
            eq_icon_key = f"weapon_{w.id}"
            if eq_icon_key not in self._equip_icons:
                path = os.path.join(_ASSETS_ITEMS, f"{eq_icon_key}.png")
                if os.path.isfile(path):
                    raw = pygame.image.load(path).convert_alpha()
                    self._equip_icons[eq_icon_key] = pygame.transform.smoothscale(
                        raw, (_EQUIP_ICON, _EQUIP_ICON)
                    )
                else:
                    self._equip_icons[eq_icon_key] = None
            eq_icon = self._equip_icons[eq_icon_key]
            icon_y = eq_y - (_EQUIP_ICON - self._font_bold.get_height()) // 2
            if eq_icon is not None:
                icon_x = ox + _W - _PAD - _EQUIP_ICON
                screen.blit(eq_icon, (icon_x, icon_y))
            # Ammo badge — small icon on bottom-right corner of weapon icon (ranged only)
            if w.range_type == RangeType.RANGED and hasattr(w, "ammo_type"):
                ammo_badge_key = f"ammo_badge_{w.ammo_type}"
                if ammo_badge_key not in self._equip_icons:
                    path = os.path.join(_ASSETS_ITEMS, f"ammo_ammo_{w.ammo_type}.png")
                    if os.path.isfile(path):
                        raw = pygame.image.load(path).convert_alpha()
                        self._equip_icons[ammo_badge_key] = pygame.transform.smoothscale(
                            raw, (_AMMO_BADGE, _AMMO_BADGE)
                        )
                    else:
                        self._equip_icons[ammo_badge_key] = None
                ammo_icon = self._equip_icons[ammo_badge_key]
                if ammo_icon is not None:
                    badge_x = ox + _W - _PAD - _AMMO_BADGE
                    badge_y = icon_y + _EQUIP_ICON - _AMMO_BADGE
                    screen.blit(ammo_icon, (badge_x, badge_y))
        else:
            screen.blit(self._font.render(t("inv.none"), True, _COL_DIM), (ox + _PAD + 75, eq_y))

        # --- Equipped armor line ---
        ar_y = eq_y + 20
        screen.blit(self._font.render(t("inv.armor_label"), True, _COL_DIM), (ox + _PAD, ar_y))
        armor = getattr(player, "equipped_armor", None)
        if armor is not None:
            ar_surf = self._font_bold.render(f"{armor.name}   {armor.stat_line()}", True, (140, 200, 100))
            screen.blit(ar_surf, (ox + _PAD + 75, ar_y))
        else:
            screen.blit(self._font.render(t("inv.none"), True, _COL_DIM), (ox + _PAD + 75, ar_y))

        pygame.draw.line(screen, (40, 60, 55), (ox + _PAD, ar_y + 22), (ox + _W - _PAD, ar_y + 22))

        # --- Item list ---
        list_y    = ar_y + 30
        footer_y  = oy + _H - _PAD - 26
        list_max_y = footer_y - 14

        self._item_rects = {}

        if n == 0:
            screen.blit(self._font.render(t("inv.empty"), True, _COL_DIM), (ox + _PAD, list_y))
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

                # Icon — convention: assets/items/{itemtype}_{id}.png
                icon_key = f"{item.item_type.name.lower()}_{item.id}"
                if icon_key not in self._item_icons:
                    path = os.path.join(_ASSETS_ITEMS, f"{icon_key}.png")
                    if os.path.isfile(path):
                        raw = pygame.image.load(path).convert_alpha()
                        self._item_icons[icon_key] = pygame.transform.smoothscale(
                            raw, (_ICON_SIZE, _ICON_SIZE)
                        )
                    else:
                        self._item_icons[icon_key] = None
                icon_surf = self._item_icons[icon_key]
                if icon_surf is not None:
                    icon_y = row_y + (_ROW_H - _ICON_SIZE) // 2
                    screen.blit(icon_surf, (ox + _PAD, icon_y))
                text_x = ox + _PAD + (_ICON_SIZE + 4 if icon_surf is not None else 0)

                stat      = item.stat_line() if hasattr(item, "stat_line") else ""
                stat_surf = self._font.render(stat, True, _COL_DIM)
                stat_x    = ox + _W - _PAD - stat_surf.get_width()

                name_max_w = stat_x - _PAD - text_x
                name_s = self._font_bold.render(item.name, True, col)
                if name_s.get_width() > name_max_w:
                    name_s = name_s.subsurface((0, 0, name_max_w, name_s.get_height()))
                screen.blit(name_s, (text_x, row_y + 4))
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
            ("use",   t("inv.btn_use")),
            ("close", t("inv.btn_close")),
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

        # --- Help button [?] on the right side of footer ---
        help_w = self._font.size("?")[0] + 14
        help_rect = pygame.Rect(ox + _W - _PAD - help_w, footer_y - 2, help_w, 22)
        self.help_btn_rect = help_rect
        is_hov = self._hovered_btn == "help"
        pygame.draw.rect(screen, _BTN_HOV if is_hov else _BTN_NRM, help_rect)
        pygame.draw.rect(screen, _BORDER if is_hov else (45, 70, 60), help_rect, 1)
        col = (180, 220, 200) if is_hov else _COL_KEY
        screen.blit(self._font.render("?", True, col),
                    (help_rect.x + 7, footer_y))
