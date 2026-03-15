"""Weapon-swap dropdown — opened with C, anchored under the HUD weapon line."""
from __future__ import annotations

import pygame

from dungeoneer.items.weapon import Weapon

_PAD     = 10
_ROW_H   = 26
_W       = 420
_BG      = (14, 14, 24, 230)
_BORDER  = (80, 180, 160)
_SEL_BG  = (30, 80, 70)
_COL_WPN = (180, 200, 255)
_COL_EQ  = (80, 220, 180)
_COL_DIM = (100, 100, 120)
_COL_KEY = (80, 100, 120)
_COL_HDR = (80, 180, 160)
_BTN_HOV = (40, 100, 85)
_BTN_NRM = (20, 35, 30)

_ANCHOR_X = 12
_ANCHOR_Y = 76


class WeaponPickerUI:
    def __init__(self) -> None:
        self._font      = pygame.font.SysFont("consolas", 15, bold=False)
        self._font_bold = pygame.font.SysFont("consolas", 15, bold=True)
        self._selected    = 0
        self._hovered_btn: str | None = None
        # Populated during draw()
        self._weapon_rects: dict[int, pygame.Rect] = {}  # index → rect
        self._btn_rects:    dict[str, pygame.Rect] = {}  # "close" → rect

    # ------------------------------------------------------------------

    def open(self, player: "Player") -> None:  # type: ignore[name-defined]
        weapons = self._weapons(player)
        eq = player.equipped_weapon
        self._selected = weapons.index(eq) if eq and eq in weapons else 0

    @staticmethod
    def _weapons(player: "Player") -> list[Weapon]:  # type: ignore[name-defined]
        return [i for i in player.inventory if isinstance(i, Weapon)]

    # ------------------------------------------------------------------
    # Keyboard input
    # ------------------------------------------------------------------

    def handle_key(self, key: int, player: "Player"):  # type: ignore[name-defined]
        """Returns EquipAction, 'close', or None."""
        from dungeoneer.combat.action import EquipAction

        weapons = self._weapons(player)
        n = len(weapons)

        if key in (pygame.K_ESCAPE, pygame.K_c):
            return "close"
        if n == 0:
            return None
        if key in (pygame.K_UP, pygame.K_w):
            self._selected = max(0, self._selected - 1)
            return None
        if key in (pygame.K_DOWN, pygame.K_s):
            self._selected = min(n - 1, self._selected + 1)
            return None
        if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_e):
            self._selected = min(self._selected, n - 1)
            return EquipAction(weapons[self._selected])
        return None

    # ------------------------------------------------------------------
    # Mouse input
    # ------------------------------------------------------------------

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        for idx, rect in self._weapon_rects.items():
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
        """Returns EquipAction, 'close', or None."""
        from dungeoneer.combat.action import EquipAction

        if event.button != 1:
            return None

        weapons = self._weapons(player)

        for name, rect in self._btn_rects.items():
            if rect.collidepoint(event.pos):
                if name == "close":
                    return "close"

        for idx, rect in self._weapon_rects.items():
            if rect.collidepoint(event.pos):
                self._selected = idx
                if idx < len(weapons):
                    return EquipAction(weapons[idx])

        return None

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        weapons = self._weapons(player)
        n = len(weapons)

        rows = max(1, n)
        h = _PAD + 20 + rows * _ROW_H + _PAD + 28 + _PAD

        ox, oy = _ANCHOR_X, _ANCHOR_Y

        panel = pygame.Surface((_W, h), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, h), 2)

        # Header
        hdr = self._font_bold.render("SWAP WEAPON", True, _COL_HDR)
        screen.blit(hdr, (ox + _PAD, oy + _PAD))
        pygame.draw.line(screen, (40, 60, 55),
                         (ox + _PAD, oy + _PAD + 18), (ox + _W - _PAD, oy + _PAD + 18))

        list_y = oy + _PAD + 22
        self._weapon_rects = {}

        if n == 0:
            screen.blit(self._font.render("(no weapons in inventory)", True, _COL_DIM),
                        (ox + _PAD, list_y + 4))
        else:
            self._selected = min(self._selected, n - 1)
            eq = player.equipped_weapon
            for i, wpn in enumerate(weapons):
                row_y  = list_y + i * _ROW_H
                row_rect = pygame.Rect(ox + 4, row_y, _W - 8, _ROW_H - 2)
                self._weapon_rects[i] = row_rect

                if i == self._selected:
                    pygame.draw.rect(screen, _SEL_BG, row_rect)

                is_eq = wpn is eq
                col   = _COL_EQ if is_eq else _COL_WPN
                label = f"{'▶ ' if is_eq else '  '}{wpn.name}"

                from dungeoneer.items.item import RangeType
                if hasattr(wpn, "range_type") and wpn.range_type == RangeType.RANGED:
                    burst   = f"  ×{wpn.shots}" if wpn.shots > 1 else ""
                    reserve = player.ammo_reserves.get(wpn.ammo_type, 0)
                    stat    = (f"{wpn.damage_min}–{wpn.damage_max} dmg{burst}"
                               f"  {wpn.ammo_current}/{wpn.ammo_capacity}+{reserve}"
                               f"  ~{wpn.range_tiles}t")
                elif hasattr(wpn, "stat_line"):
                    stat = wpn.stat_line()
                else:
                    stat = ""
                stat_s = self._font.render(stat, True, _COL_DIM)
                stat_x = ox + _W - _PAD - stat_s.get_width()

                # Clip name so it never overlaps the stat column
                name_max_w = stat_x - _PAD - (ox + _PAD)
                name_s = self._font_bold.render(label, True, col)
                if name_s.get_width() > name_max_w:
                    name_s = name_s.subsurface((0, 0, name_max_w, name_s.get_height()))
                screen.blit(name_s, (ox + _PAD, row_y + 5))
                screen.blit(stat_s, (stat_x, row_y + 5))

        # Footer close button
        footer_y = oy + h - _PAD - 22
        pygame.draw.line(screen, (40, 60, 55),
                         (ox + _PAD, footer_y - 4), (ox + _W - _PAD, footer_y - 4))

        self._btn_rects = {}
        close_label = "[C/Esc] Close"
        close_w = self._font.size(close_label)[0] + 14
        close_rect = pygame.Rect(ox + _PAD, footer_y, close_w, 20)
        self._btn_rects["close"] = close_rect
        is_hov = self._hovered_btn == "close"
        pygame.draw.rect(screen, _BTN_HOV if is_hov else _BTN_NRM, close_rect)
        pygame.draw.rect(screen, _BORDER if is_hov else (45, 70, 60), close_rect, 1)
        screen.blit(self._font.render(close_label, True,
                                      (180, 220, 200) if is_hov else _COL_KEY),
                    (ox + _PAD + 7, footer_y + 2))

        hint = "  [↑↓] Navigate   [E/Enter] Equip"
        hint_s = self._font.render(hint, True, _COL_KEY)
        screen.blit(hint_s, (ox + _PAD + close_w + 4, footer_y + 2))
