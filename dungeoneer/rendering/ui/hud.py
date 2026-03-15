"""HUD — health bar, weapon info, floor depth, controls hint."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.items.item import RangeType


class HUD:
    def __init__(self) -> None:
        self._font_large = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_small = pygame.font.SysFont("consolas", 14)

    def draw(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT

        # --- HP bar (top-left) ---
        bar_x, bar_y = 12, 12
        bar_w, bar_h = 200, 20
        ratio = max(0.0, player.hp / player.max_hp)
        pygame.draw.rect(screen, (60, 20, 20),   (bar_x, bar_y, bar_w, bar_h))
        fill_col = settings.COL_HP_FULL if ratio > 0.4 else settings.COL_HP_LOW
        pygame.draw.rect(screen, fill_col, (bar_x, bar_y, int(bar_w * ratio), bar_h))
        pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_w, bar_h), 1)
        hp_text = self._font_large.render(
            f"HP {player.hp}/{player.max_hp}", True, settings.COL_WHITE
        )
        screen.blit(hp_text, (bar_x + 4, bar_y + 1))

        # --- Equipped weapon (below HP) ---
        _KEY  = (80, 100, 125)   # dim key-hint colour
        _WY   = bar_y + bar_h + 6

        c_surf = self._font_small.render("[C] ", True, _KEY)
        screen.blit(c_surf, (bar_x, _WY))
        wpn_x = bar_x + c_surf.get_width()

        w = player.equipped_weapon
        if w:
            if w.range_type == RangeType.RANGED:
                ammo_col = (180, 200, 255) if w.ammo_current > 0 else (255, 80, 80)
                reserve  = player.ammo_reserves.get(w.ammo_type, 0)
                weapon_str = (
                    f"{w.name}  {w.damage_min}–{w.damage_max} dmg"
                    f"  {w.ammo_current}/{w.ammo_capacity}  ~{w.range_tiles}t"
                    f"  [{w.ammo_type}: {reserve}]"
                )
                reload_hint = True
            else:
                ammo_col   = (200, 180, 120)
                weapon_str = f"{w.name}  {w.damage_min}–{w.damage_max} dmg"
                reload_hint = False

            w_surf = self._font_small.render(weapon_str, True, ammo_col)
            screen.blit(w_surf, (wpn_x, _WY))

            if reload_hint:
                r_surf = self._font_small.render("  [R]", True, _KEY)
                screen.blit(r_surf, (wpn_x + w_surf.get_width(), _WY))
        else:
            no_w = self._font_small.render("—", True, (120, 80, 80))
            screen.blit(no_w, (wpn_x, _WY))

        # --- Quick heal tip (below weapon line) ---
        from dungeoneer.items.consumable import Consumable
        healables = [i for i in player.inventory if isinstance(i, Consumable) and i.heal_amount > 0]
        missing = player.max_hp - player.hp
        if missing <= 0:
            heal_str = "[H] Full HP"
            heal_col = (70, 90, 75)
        elif healables:
            exact = [i for i in healables if i.heal_amount <= missing]
            chosen = max(exact, key=lambda c: c.heal_amount) if exact \
                else min(healables, key=lambda c: c.heal_amount)
            count_str = f"  x{chosen.count}" if chosen.count > 1 else ""
            overheal  = chosen.heal_amount > missing
            heal_str  = f"[H] {chosen.name}  +{chosen.heal_amount} HP{count_str}"
            if overheal:
                heal_str += "  !"
            heal_col = (200, 160, 60) if overheal else (90, 200, 110)
        else:
            heal_str = "[H] --"
            heal_col = (80, 80, 90)
        ht_surf = self._font_small.render(heal_str, True, heal_col)
        screen.blit(ht_surf, (bar_x, bar_y + bar_h + 6 + 20))

        # --- Floor depth + credits (top-right) ---
        depth_text = self._font_large.render(
            f"FLOOR {player.floor_depth}", True, (120, 200, 180)
        )
        screen.blit(depth_text, (sw - depth_text.get_width() - 12, 12))

        cr_text = self._font_large.render(
            f"¥ {player.credits}", True, (200, 190, 80)
        )
        screen.blit(cr_text, (sw - cr_text.get_width() - 12, 12 + depth_text.get_height() + 4))

        # --- Controls hint (bottom-right) ---
        hint_surf = self._font_small.render(t("hud.help_hint"), True, (80, 95, 115))
        screen.blit(hint_surf, (sw - hint_surf.get_width() - 12, sh - hint_surf.get_height() - 10))
