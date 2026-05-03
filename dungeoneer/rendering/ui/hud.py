"""HUD — health bar, weapon info, floor depth, controls hint."""
from __future__ import annotations

import math

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.items.item import RangeType

_SHADOW = (0, 0, 0)
_PANEL  = (10, 10, 18, 185)   # dark navy, semi-transparent
_M      = 6                    # panel margin


_HEAT_COLOURS = [
    (80,  200,  80),   # level 1  GHOST    — green
    (180, 210,  60),   # level 2  TRACE    — yellow-green
    (220, 150,  40),   # level 3  ALERT    — orange
    (220,  60,  60),   # level 4  PURSUIT  — red
    (180,  20,  20),   # level 5  BURN     — deep red
]


_EP_BAR_COL    = (80, 200, 255)   # neon-blue energy fill
_EP_BAR_EMPTY  = (20, 40, 60)     # energy bar background
_EP_SLOT_DIM   = (25, 35, 50)     # hotbar slot background (empty)
_EP_SLOT_LIT   = (30, 80, 120)    # hotbar slot background (assigned)
_EP_SLOT_LOW   = (100, 30, 30)    # hotbar slot border when EP insufficient
_EP_SLOT_BDR   = (60, 140, 200)   # hotbar slot border (normal)
_EP_SLOT_W     = 54
_EP_SLOT_H     = 44

_TIP_W         = 240    # hotbar tooltip width
_TIP_BG        = (8, 10, 20, 220)
_TIP_BDR       = (60, 160, 200)


def _wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    if font.size(text)[0] <= max_w:
        return [text]
    words, lines, cur = text.split(), [], ""
    for word in words:
        cand = (cur + " " + word).strip()
        if font.size(cand)[0] <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [text]


class HUD:
    def __init__(self, heal_threshold_pct: int = 100) -> None:
        self._heal_threshold_pct = heal_threshold_pct
        self._font_large = pygame.font.SysFont("consolas", 18, bold=True)
        self._font_small = pygame.font.SysFont("consolas", 14)
        self._font_tiny  = pygame.font.SysFont("consolas", 11)
        self.weapon_rect:   pygame.Rect | None = None
        self.heal_rect:     pygame.Rect | None = None
        self.help_btn_rect: pygame.Rect | None = None
        self.heat_system = None          # set by GameScene after HeatSystem is created
        self.vault_credits_banked: int = 0  # set by GameScene when vault credits change
        self.profile      = None         # set by GameScene; provides hotbar + perks
        self._hotbar_rects: list[pygame.Rect] = []  # updated each frame for mouse hit-testing

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _blit_text(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        text: str,
        color: tuple,
        pos: tuple,
    ) -> pygame.Surface:
        """Render *text* with a 1-px drop-shadow; return the main surface."""
        shadow = font.render(text, True, _SHADOW)
        screen.blit(shadow, (pos[0] + 1, pos[1] + 1))
        surf = font.render(text, True, color)
        screen.blit(surf, pos)
        return surf

    @staticmethod
    def _draw_panel(screen: pygame.Surface, x: int, y: int, w: int, h: int) -> None:
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill(_PANEL)
        screen.blit(panel, (x, y))

    # ------------------------------------------------------------------
    # Main draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT

        bar_x, bar_y = 12, 12
        bar_w, bar_h = 200, 20
        _KEY  = (80, 100, 125)
        line_h = self._font_small.get_height() + 2

        # ── pre-compute left-column strings & colours ──────────────────

        ratio = max(0.0, player.hp / player.max_hp)

        # weapon
        w = player.equipped_weapon
        if w:
            if w.range_type == RangeType.RANGED:
                ammo_col   = (180, 200, 255) if w.ammo_current > 0 else (255, 80, 80)
                reserve    = player.ammo_reserves.get(w.ammo_type, 0)
                weapon_str = (
                    f"{w.name}  {w.damage_min}–{w.damage_max} dmg"
                    f"  {w.ammo_current}/{w.ammo_capacity}  ~{w.range_tiles}t"
                    f"  [{w.ammo_type}: {reserve}]"
                )
                reload_hint = True
            else:
                ammo_col    = (200, 180, 120)
                weapon_str  = f"{w.name}  {w.damage_min}–{w.damage_max} dmg"
                reload_hint = False
        else:
            ammo_col    = (120, 80, 80)
            weapon_str  = "—"
            reload_hint = False

        # heal
        from dungeoneer.items.consumable import Consumable
        healables = [i for i in player.inventory if isinstance(i, Consumable) and i.heal_amount > 0]
        missing   = player.max_hp - player.hp
        if missing <= 0:
            heal_str = t("hud.full_hp")
            heal_col = (70, 90, 75)
        elif healables:
            thr    = self._heal_threshold_pct / 100.0
            exact  = [i for i in healables if i.heal_amount * thr <= missing]
            chosen = max(exact, key=lambda c: c.heal_amount) if exact \
                     else min(healables, key=lambda c: c.heal_amount)
            count_str = f"  x{chosen.count}" if chosen.count > 1 else ""
            overheal  = chosen.heal_amount > missing
            heal_str  = f"[H] {chosen.name}  +{chosen.heal_amount} HP{count_str}"
            if overheal:
                heal_str += "  !"
            heal_col = (200, 160, 60) if overheal else (90, 200, 110)
        else:
            heal_str = t("hud.no_heal")
            heal_col = (80, 80, 90)

        # armor
        armor = getattr(player, "equipped_armor", None)
        if armor is not None:
            armor_str = f"{t('hud.armor_label')} {armor.name}  -{armor.defense_bonus} dmg"
            armor_col = (140, 200, 100)
        else:
            armor_str = f"{t('hud.armor_label')} {t('hud.armor_none')}"
            armor_col = (60, 80, 55)

        # ── size left panel to fit the widest element ──────────────────
        c_w       = self._font_small.size("[C] ")[0]
        rl_w      = self._font_small.size("  [R]")[0] if reload_hint else 0
        wpn_w     = c_w + self._font_small.size(weapon_str)[0] + rl_w
        panel_w   = max(bar_w,
                        wpn_w,
                        self._font_small.size(heal_str)[0],
                        self._font_small.size(armor_str)[0]) + 2 * _M
        panel_h   = bar_h + 3 * line_h + 3 * _M

        # ── draw left panel ────────────────────────────────────────────
        self._draw_panel(screen, bar_x - _M, bar_y - _M, panel_w, panel_h)

        # HP bar
        pygame.draw.rect(screen, (60, 20, 20),    (bar_x, bar_y, bar_w, bar_h))
        fill_col = settings.COL_HP_FULL if ratio > 0.4 else settings.COL_HP_LOW
        pygame.draw.rect(screen, fill_col, (bar_x, bar_y, round(bar_w * ratio), bar_h))
        pygame.draw.rect(screen, (180, 180, 180), (bar_x, bar_y, bar_w, bar_h), 1)
        self._blit_text(screen, self._font_large,
                        f"HP {player.hp}/{player.max_hp}",
                        settings.COL_WHITE, (bar_x + 4, bar_y + 1))

        # weapon line
        _WY = bar_y + bar_h + _M
        self.weapon_rect = pygame.Rect(bar_x - _M, _WY, panel_w, line_h)
        self.heal_rect   = pygame.Rect(bar_x - _M, _WY + line_h, panel_w, line_h)

        # hover highlights
        mx, my = pygame.mouse.get_pos()
        _HOVER = (255, 255, 255, 28)
        for rect in (self.weapon_rect, self.heal_rect):
            if rect.collidepoint(mx, my):
                hl = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
                hl.fill(_HOVER)
                screen.blit(hl, rect.topleft)

        key_surf = self._blit_text(screen, self._font_small, "[C] ", _KEY, (bar_x, _WY))
        wpn_surf = self._blit_text(screen, self._font_small, weapon_str, ammo_col,
                                   (bar_x + c_w, _WY))
        if reload_hint:
            self._blit_text(screen, self._font_small, "  [R]", _KEY,
                            (bar_x + c_w + wpn_surf.get_width(), _WY))

        # heal line
        self._blit_text(screen, self._font_small, heal_str, heal_col,
                        (bar_x, _WY + line_h))

        # armor line
        self._blit_text(screen, self._font_small, armor_str, armor_col,
                        (bar_x, _WY + 2 * line_h))

        # ── right panel (floor depth + credits [+ vault pending]) ────
        depth_str  = t("hud.floor").format(n=player.floor_depth)
        cr_str     = f"¥ {player.credits}"
        vault_str  = (
            t("hud.vault_pending").format(n=self.vault_credits_banked)
            if self.vault_credits_banked > 0 else None
        )
        lh_large   = self._font_large.get_height()
        lh_small   = self._font_small.get_height()
        r_w = max(self._font_large.size(depth_str)[0],
                  self._font_large.size(cr_str)[0])
        if vault_str:
            r_w = max(r_w, self._font_small.size(vault_str)[0])
        r_h = 2 * lh_large + 4 + 2 * _M
        if vault_str:
            r_h += lh_small + 4
        r_x  = sw - r_w - 12
        self._draw_panel(screen, r_x - _M, 12 - _M, r_w + 2 * _M, r_h)

        self._blit_text(screen, self._font_large, depth_str, (120, 200, 180), (r_x, 12))
        self._blit_text(screen, self._font_large, cr_str, (200, 190, 80),
                        (r_x, 12 + lh_large + 4))
        if vault_str:
            self._blit_text(screen, self._font_small, vault_str, (60, 210, 180),
                            (r_x, 12 + 2 * lh_large + 8))

        # ── heat bar (centre-top) ─────────────────────────────────────
        self._draw_heat_bar(screen)

        # ── energy bar (centre-top, below heat bar) ───────────────────
        self._draw_energy_bar(screen, player)

        # ── hotbar (bottom-left) ──────────────────────────────────────
        self._draw_hotbar(screen, player)

        # ── help button [?] to the left of the right panel ───────────
        f1_text = t("hud.help_hint")
        f1_probe = self._font_small.render(f1_text, True, (0, 0, 0))
        icon_d  = 16                              # diameter of ? circle
        btn_pad = 5
        btn_w   = btn_pad + icon_d + 4 + f1_probe.get_width() + btn_pad
        btn_h   = r_h                             # same height as right panel
        btn_x   = r_x - _M - 6 - btn_w           # 6 px gap
        btn_y   = 12 - _M
        self.help_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        hov = self.help_btn_rect.collidepoint(mx, my)
        btn_bdr = (80, 180, 150) if hov else (38, 65, 55)
        lbl_col = (180, 230, 210) if hov else (80, 110, 95)
        self._draw_panel(screen, btn_x, btn_y, btn_w, btn_h)
        pygame.draw.rect(screen, btn_bdr, self.help_btn_rect, 1, border_radius=3)
        # ? icon circle — vertically centred inside the panel
        icon_cx = btn_x + btn_pad + icon_d // 2
        icon_cy = btn_y + btn_h // 2
        pygame.draw.circle(screen, btn_bdr, (icon_cx, icon_cy), icon_d // 2)
        q_surf = self._font_small.render("?", True, (200, 240, 220) if hov else (100, 140, 120))
        screen.blit(q_surf, (icon_cx - q_surf.get_width() // 2,
                              icon_cy - self._font_small.get_height() // 2 + 1))
        # F1 label — vertically centred, right of the icon
        f1_surf = self._font_small.render(f1_text, True, lbl_col)
        screen.blit(f1_surf, (btn_x + btn_pad + icon_d + 4,
                               icon_cy - self._font_small.get_height() // 2 + 1))

    # ------------------------------------------------------------------
    # Heat bar
    # ------------------------------------------------------------------

    def _draw_heat_bar(self, screen: pygame.Surface) -> None:
        if self.heat_system is None:
            return

        from dungeoneer.systems.heat import LEVEL_NAMES
        level    = self.heat_system.level
        progress = self.heat_system.progress
        fill_col = _HEAT_COLOURS[level - 1]

        bar_w, bar_h = 180, 14
        bar_x = (settings.SCREEN_WIDTH - bar_w) // 2
        bar_y = 16

        lbl_h  = self._font_small.get_height()
        panel_h = bar_h + lbl_h + 3 * _M
        self._draw_panel(screen, bar_x - _M, bar_y - _M, bar_w + 2 * _M, panel_h)

        # Background track
        pygame.draw.rect(screen, (30, 15, 15), (bar_x, bar_y, bar_w, bar_h))

        # Fill
        fill_w = round(bar_w * progress)
        if fill_w > 0:
            pygame.draw.rect(screen, fill_col, (bar_x, bar_y, fill_w, bar_h))

        # Pulse overlay at level 5
        if level == 5 and fill_w > 0:
            alpha = int(30 + 25 * math.sin(pygame.time.get_ticks() / 200))
            pulse = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            pulse.fill((255, 80, 80, alpha))
            screen.blit(pulse, (bar_x, bar_y))

        # Border
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_w, bar_h), 1)

        # Level name label
        lbl = t("hud.heat_level").format(n=level, name=LEVEL_NAMES[level])
        lbl_surf = self._font_small.render(lbl, True, fill_col)
        screen.blit(lbl_surf, (bar_x + (bar_w - lbl_surf.get_width()) // 2,
                                bar_y + bar_h + 2))

    # ------------------------------------------------------------------
    # Energy bar
    # ------------------------------------------------------------------

    def _draw_energy_bar(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        ep     = getattr(player, "energy", 0)
        ep_max = settings.ENERGY_MAX

        bar_w, bar_h = 180, 10
        bar_x = (settings.SCREEN_WIDTH - bar_w) // 2

        # Position just below the heat panel
        # Heat bar is at bar_y=16 with panel_h = bar_h_heat + lbl_h + 3*_M ≈ 46
        # Add a small gap so the two panels sit close but separate.
        bar_y = 70

        lbl_text = f"{ep} / {ep_max} {t('hud.energy')}"
        lbl_surf = self._font_tiny.render(lbl_text, True, _EP_BAR_COL)
        lbl_h    = lbl_surf.get_height()

        panel_h = bar_h + lbl_h + 2 * _M
        self._draw_panel(screen, bar_x - _M, bar_y - _M, bar_w + 2 * _M, panel_h)

        # Background track
        pygame.draw.rect(screen, _EP_BAR_EMPTY, (bar_x, bar_y, bar_w, bar_h))

        # Fill
        if ep_max > 0:
            fill_w = round(bar_w * min(1.0, ep / ep_max))
            if fill_w > 0:
                pygame.draw.rect(screen, _EP_BAR_COL, (bar_x, bar_y, fill_w, bar_h))

        # Border
        pygame.draw.rect(screen, (60, 120, 160), (bar_x, bar_y, bar_w, bar_h), 1)

        # Label centred below bar
        screen.blit(lbl_surf, (bar_x + (bar_w - lbl_surf.get_width()) // 2,
                                bar_y + bar_h + 2))

    # ------------------------------------------------------------------
    # Hotbar
    # ------------------------------------------------------------------

    def _draw_hotbar(self, screen: pygame.Surface, player: "Player") -> None:  # type: ignore[name-defined]
        profile = self.profile
        if profile is None:
            return

        from dungeoneer.perks import CATALOG, get_perk
        from dungeoneer.core.settings import ENERGY_MAX

        ep = getattr(player, "energy", 0)

        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT
        n  = 10
        gap = 4
        total_w = n * _EP_SLOT_W + (n - 1) * gap
        sx = 12
        # Vertically centre the hotbar in the bottom HUD band.
        band_top = sh - settings.VIEWPORT_Y_BOTTOM
        sy = band_top + (settings.VIEWPORT_Y_BOTTOM - _EP_SLOT_H) // 2

        self._hotbar_rects = []
        for i in range(n):
            rx = sx + i * (_EP_SLOT_W + gap)
            rect = pygame.Rect(rx, sy, _EP_SLOT_W, _EP_SLOT_H)
            self._hotbar_rects.append(rect)

            perk_id = profile.hotbar[i] if i < len(profile.hotbar) else None
            slot_key = str((i + 1) % 10)  # 1–9, 0 for slot 10

            if perk_id and perk_id in CATALOG:
                pdef = CATALOG[perk_id]
                cost = pdef.ep_cost if pdef.ep_cost is not None else pdef.ep_per_turn
                can_fire = cost is None or ep >= cost
                bdr = _EP_SLOT_BDR if can_fire else _EP_SLOT_LOW
                pygame.draw.rect(screen, _EP_SLOT_LIT, rect, border_radius=3)
                pygame.draw.rect(screen, bdr, rect, 1, border_radius=3)

                # Slot number (top-left)
                k_surf = self._font_tiny.render(slot_key, True, (120, 160, 200))
                screen.blit(k_surf, (rx + 3, sy + 2))

                # EP cost (top-right)
                if cost is not None:
                    ep_str   = str(cost)
                    ep_col   = (80, 200, 255) if can_fire else (200, 60, 60)
                    ep_surf  = self._font_tiny.render(ep_str, True, ep_col)
                    screen.blit(ep_surf, (rx + _EP_SLOT_W - ep_surf.get_width() - 3, sy + 2))

                # Icon centred in slot (fallback: name abbreviation)
                from dungeoneer.rendering.perk_icons import get_icon
                icon = get_icon(perk_id, size=28)
                if icon is not None:
                    screen.blit(icon, (rx + (_EP_SLOT_W - 28) // 2,
                                       sy + (_EP_SLOT_H - 28) // 2))
                else:
                    name = t(pdef.name_key)
                    abbr = name[:7] if len(name) > 7 else name
                    ab_surf = self._font_tiny.render(abbr, True, (160, 200, 220))
                    screen.blit(ab_surf, (rx + _EP_SLOT_W // 2 - ab_surf.get_width() // 2,
                                          sy + _EP_SLOT_H - ab_surf.get_height() - 2))
            else:
                pygame.draw.rect(screen, _EP_SLOT_DIM, rect, border_radius=3)
                pygame.draw.rect(screen, (40, 55, 70), rect, 1, border_radius=3)

                k_surf = self._font_tiny.render(slot_key, True, (60, 75, 90))
                screen.blit(k_surf, (rx + 3, sy + 2))

        # Tooltip for hovered slot
        mx, my = pygame.mouse.get_pos()
        for i, rect in enumerate(self._hotbar_rects):
            if rect.collidepoint(mx, my):
                perk_id = profile.hotbar[i] if i < len(profile.hotbar) else None
                if perk_id and perk_id in CATALOG:
                    from dungeoneer.perks import get_level
                    lvl = get_level(self.profile, perk_id)
                    self._draw_hotbar_tooltip(screen, CATALOG[perk_id], rect, ep, lvl)
                break

    def _draw_hotbar_tooltip(
        self,
        screen: pygame.Surface,
        pdef: "PerkDef",  # type: ignore[name-defined]
        slot_rect: pygame.Rect,
        ep: int,
        level: int = 1,
    ) -> None:
        from dungeoneer.rendering.perk_icons import get_icon
        from dungeoneer.core.i18n import t as _t
        from dungeoneer.perks.catalog import desc_for_level

        pad = 8
        icon = get_icon(pdef.id, size=24)
        icon_w = 24 + 6 if icon is not None else 0

        name_surf = self._font_small.render(_t(pdef.name_key), True, (80, 200, 255))
        desc_lines = _wrap_text(self._font_tiny, desc_for_level(pdef.id, level), _TIP_W - 2 * pad)

        cost = pdef.ep_cost if pdef.ep_cost is not None else pdef.ep_per_turn
        ep_text = (
            f"EP/turn: {cost}" if pdef.ep_per_turn is not None else f"EP: {cost}"
        ) if cost is not None else None

        row_h  = self._font_tiny.get_height() + 2
        content_h = (
            max(name_surf.get_height(), 24) + 4
            + len(desc_lines) * row_h
            + (self._font_tiny.get_height() + 6 if ep_text else 0)
        )
        tip_h = content_h + 2 * pad

        # Position above the slot, clamped to screen
        tx = max(0, min(slot_rect.centerx - _TIP_W // 2,
                        settings.SCREEN_WIDTH - _TIP_W))
        ty = slot_rect.top - tip_h - 6

        # Background
        tip_surf = pygame.Surface((_TIP_W, tip_h), pygame.SRCALPHA)
        tip_surf.fill(_TIP_BG)
        screen.blit(tip_surf, (tx, ty))
        pygame.draw.rect(screen, _TIP_BDR, (tx, ty, _TIP_W, tip_h), 1, border_radius=4)

        cx = tx + pad
        cy = ty + pad

        # Icon + name on first line
        if icon is not None:
            screen.blit(icon, (cx, cy + (name_surf.get_height() - 24) // 2))
            cx += icon_w
        screen.blit(name_surf, (cx, cy))
        cy += max(name_surf.get_height(), 24) + 4
        cx = tx + pad

        # Description
        for line in desc_lines:
            s = self._font_tiny.render(line, True, (170, 185, 200))
            screen.blit(s, (cx, cy))
            cy += row_h

        # EP cost
        if ep_text:
            cy += 2
            can = cost is None or ep >= cost
            ep_col = (80, 200, 255) if can else (200, 60, 60)
            ep_s = self._font_tiny.render(ep_text, True, ep_col)
            screen.blit(ep_s, (cx, cy))
