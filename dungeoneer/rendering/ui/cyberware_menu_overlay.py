"""In-run cyberware menu overlay — opened with K.

Shows owned perks split into ACTIVE and PASSIVE sections.
Clicking an active perk enters assign mode; the next 1-0 keypress assigns that
perk to the corresponding hotbar slot.
"""
from __future__ import annotations

from typing import Callable

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.perks import CATALOG, PerkType, get_level

# ---------------------------------------------------------------------------
# Layout / colour constants
# ---------------------------------------------------------------------------

_W   = 480
_H   = 460
_PAD = 16
_ROW_H = 26

_BG      = (8, 10, 20, 230)
_BORDER  = (60, 160, 200)
_COL_HDR = (60, 190, 230)
_COL_ACT = (80, 200, 255)     # active perk name
_COL_PAS = (120, 200, 160)    # passive perk name
_COL_DIM = (70, 90, 110)      # empty / greyed
_COL_EP  = (80, 200, 255)     # EP cost
_COL_LOW = (220, 60, 60)      # EP cost when player can't afford
_COL_KEY = (80, 100, 120)
_SEL_BG  = (20, 60, 90, 200)  # selected row background
_HOV_BG  = (15, 45, 70, 140)  # hovered row background
_ASN_BG  = (30, 80, 120, 220) # assign-mode selected row
_BTN_NRM = (18, 32, 45)
_BTN_HOV = (35, 90, 130)


class CyberwareMenuOverlay:
    """Overlay for browsing and hotbar-assigning owned cyberware during a run."""

    def __init__(
        self,
        profile,
        player,
        on_close: Callable,
        on_assign_hotbar: Callable,
    ) -> None:
        self._profile = profile
        self._player  = player
        self._on_close = on_close
        self._on_assign_hotbar = on_assign_hotbar

        self._font_hdr   = pygame.font.SysFont("consolas", 17, bold=True)
        self._font_body  = pygame.font.SysFont("consolas", 14)
        self._font_bold  = pygame.font.SysFont("consolas", 14, bold=True)
        self._font_tiny  = pygame.font.SysFont("consolas", 11)

        self._selected_idx: int = 0   # index into the combined owned-perk list
        self._assign_mode:  bool = False
        self._assign_perk_id: str | None = None
        self._hovered_btn: str | None = None

        # Populated each draw; used for mouse hit-testing
        self._row_rects:  list[tuple[pygame.Rect, str]] = []  # (rect, perk_id)
        self._btn_rects:  dict[str, pygame.Rect] = {}
        self._panel_rect: pygame.Rect | None = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _owned_ids(self, ptype: PerkType) -> list[str]:
        """Return owned (level >= 1) perk ids of the given type, catalog-ordered."""
        return [
            pid for pid, pdef in CATALOG.items()
            if pdef.type == ptype and get_level(self._profile, pid) >= 1
        ]

    def _hotbar_slot_for(self, perk_id: str) -> str | None:
        """Return the hotbar slot label ("1"–"0") if the perk is assigned, else None."""
        for i, slot in enumerate(self._profile.hotbar):
            if slot == perk_id:
                return str((i + 1) % 10)
        return None

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        actives  = self._owned_ids(PerkType.ACTIVE)
        passives = self._owned_ids(PerkType.PASSIVE)
        all_ids  = actives + passives
        n = len(all_ids)

        for event in events:
            if event.type == pygame.KEYDOWN:
                key = event.key

                # Close on Esc or K
                if key in (pygame.K_ESCAPE, pygame.K_k):
                    if self._assign_mode:
                        self._assign_mode    = False
                        self._assign_perk_id = None
                    else:
                        self._on_close()
                    return

                # Navigation
                if key in (pygame.K_UP, pygame.K_w):
                    self._selected_idx = max(0, self._selected_idx - 1)
                    continue
                if key in (pygame.K_DOWN, pygame.K_s):
                    self._selected_idx = min(n - 1, self._selected_idx + 1) if n else 0
                    continue

                # Enter selects active perk → assign mode
                if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                    if n and self._selected_idx < len(actives):
                        perk_id = actives[self._selected_idx]
                        self._assign_mode    = True
                        self._assign_perk_id = perk_id
                    continue

                # Slot keys 1–0 during assign mode
                if self._assign_mode and self._assign_perk_id:
                    slot = _key_to_slot(key)
                    if slot is not None:
                        self._on_assign_hotbar(slot, self._assign_perk_id)
                        self._assign_mode    = False
                        self._assign_perk_id = None
                        continue

                # Slot keys 1–0 while a row is selected (shortcut: select + assign)
                slot = _key_to_slot(key)
                if slot is not None and n and self._selected_idx < len(actives):
                    perk_id = actives[self._selected_idx]
                    self._on_assign_hotbar(slot, perk_id)
                    continue

            elif event.type == pygame.MOUSEMOTION:
                self._handle_mouse_motion(event.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_mouse_click(event.pos, actives)

    def _handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        for i, (rect, _) in enumerate(self._row_rects):
            if rect.collidepoint(pos):
                self._selected_idx = i
                break
        hov = None
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                hov = name
                break
        self._hovered_btn = hov

    def _handle_mouse_click(self, pos: tuple[int, int], actives: list[str]) -> None:
        # Check close button
        for name, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                if name == "close":
                    self._on_close()
                return

        # Check outside panel
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            self._on_close()
            return

        # Row click
        for i, (rect, perk_id) in enumerate(self._row_rects):
            if rect.collidepoint(pos):
                self._selected_idx = i
                if i < len(actives):
                    # Toggle assign mode on the clicked active perk
                    if self._assign_mode and self._assign_perk_id == perk_id:
                        self._assign_mode    = False
                        self._assign_perk_id = None
                    else:
                        self._assign_mode    = True
                        self._assign_perk_id = perk_id
                return

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        ox = (sw - _W) // 2
        oy = (sh - _H) // 2

        panel = pygame.Surface((_W, _H), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, _H), 2, border_radius=5)
        self._panel_rect = pygame.Rect(ox, oy, _W, _H)

        self._row_rects = []
        self._btn_rects = {}

        # --- Title ---
        title_surf = self._font_hdr.render(t("cyberware.menu.title"), True, _COL_HDR)
        screen.blit(title_surf, (ox + _PAD, oy + _PAD))
        sep_y = oy + _PAD + title_surf.get_height() + 4
        pygame.draw.line(screen, (30, 60, 80), (ox + _PAD, sep_y), (ox + _W - _PAD, sep_y))

        # Assign hint
        if self._assign_mode and self._assign_perk_id:
            hint = t("cyberware.menu.assign_hint")
            h_surf = self._font_tiny.render(hint, True, (200, 180, 80))
            screen.blit(h_surf, (ox + _W - _PAD - h_surf.get_width(), oy + _PAD + 2))

        content_y = sep_y + 8
        ep = getattr(self._player, "energy", 0)

        actives  = self._owned_ids(PerkType.ACTIVE)
        passives = self._owned_ids(PerkType.PASSIVE)
        all_ids  = actives + passives

        row_index = 0
        content_y = self._draw_section(
            screen, ox, oy, content_y,
            t("cyberware.menu.section.active"), actives, row_index, ep,
            is_active=True,
        )
        row_index += len(actives)
        content_y = self._draw_section(
            screen, ox, oy, content_y,
            t("cyberware.menu.section.passive"), passives, row_index, ep,
            is_active=False,
        )

        if not actives and not passives:
            empty = self._font_body.render(t("inv.empty"), True, _COL_DIM)
            screen.blit(empty, (ox + _PAD, content_y))

        # --- Close button ---
        footer_y = oy + _H - _PAD - 22
        pygame.draw.line(screen, (30, 60, 80),
                         (ox + _PAD, footer_y - 6), (ox + _W - _PAD, footer_y - 6))
        close_lbl = f"[Esc / K]  {t('inv.btn_close')}"
        lbl_surf = self._font_body.render(close_lbl, True, _COL_KEY)
        btn_w = lbl_surf.get_width() + 14
        btn_rect = pygame.Rect(ox + _PAD, footer_y - 1, btn_w, 22)
        self._btn_rects["close"] = btn_rect
        is_hov = self._hovered_btn == "close"
        pygame.draw.rect(screen, _BTN_HOV if is_hov else _BTN_NRM, btn_rect)
        pygame.draw.rect(screen, _BORDER if is_hov else (40, 65, 80), btn_rect, 1)
        screen.blit(lbl_surf, (ox + _PAD + 7, btn_rect.centery - lbl_surf.get_height() // 2 + 1))

    def _draw_section(
        self, screen: pygame.Surface, ox: int, oy: int, cy: int,
        header: str, ids: list[str], row_start: int, ep: int, is_active: bool,
    ) -> int:
        hdr_surf = self._font_bold.render(header, True, _COL_HDR)
        screen.blit(hdr_surf, (ox + _PAD, cy))
        cy += hdr_surf.get_height() + 4

        if not ids:
            dim = self._font_body.render("—", True, _COL_DIM)
            screen.blit(dim, (ox + _PAD + 8, cy))
            return cy + _ROW_H

        for i, perk_id in enumerate(ids):
            pdef    = CATALOG[perk_id]
            abs_idx = row_start + i
            rect    = pygame.Rect(ox + 4, cy - 2, _W - 8, _ROW_H)
            self._row_rects.append((rect, perk_id))

            # Row background
            is_sel  = abs_idx == self._selected_idx
            is_asgn = self._assign_mode and self._assign_perk_id == perk_id
            if is_asgn:
                bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                bg.fill(_ASN_BG)
                screen.blit(bg, rect.topleft)
            elif is_sel:
                bg = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
                bg.fill(_SEL_BG)
                screen.blit(bg, rect.topleft)

            text_x = ox + _PAD + 4
            text_cy = cy + (_ROW_H - self._font_body.get_height()) // 2

            if is_active:
                cost = pdef.ep_cost if pdef.ep_cost is not None else pdef.ep_per_turn
                can_fire = cost is None or ep >= cost

                # Icon (left edge)
                from dungeoneer.rendering.perk_icons import get_icon
                icon = get_icon(perk_id, size=18)
                if icon is not None:
                    icon_y = cy + (_ROW_H - 18) // 2
                    screen.blit(icon, (text_x, icon_y))
                    text_x += 22

                # EP cost label
                if cost is not None:
                    ep_str  = f"{cost} EP"
                    ep_col  = _COL_EP if can_fire else _COL_LOW
                    ep_surf = self._font_tiny.render(ep_str, True, ep_col)
                    screen.blit(ep_surf, (text_x, text_cy + 2))
                    text_x += ep_surf.get_width() + 8

                # Perk name
                name_col = _COL_ACT if can_fire else _COL_LOW
                n_surf = self._font_bold.render(t(pdef.name_key), True, name_col)
                screen.blit(n_surf, (text_x, text_cy))

                # Hotbar slot indicator (right side)
                slot = self._hotbar_slot_for(perk_id)
                if slot is not None:
                    slot_str = f"[{slot}]"
                    s_surf = self._font_tiny.render(slot_str, True, (100, 180, 220))
                    screen.blit(s_surf, (ox + _W - _PAD - s_surf.get_width() - 4, text_cy + 2))
            else:
                # Passive: name + "always on" label
                n_surf = self._font_bold.render(t(pdef.name_key), True, _COL_PAS)
                screen.blit(n_surf, (text_x, text_cy))
                ao_surf = self._font_tiny.render(
                    f"  {t('cyberware.menu.always_on')}", True, _COL_DIM
                )
                screen.blit(ao_surf, (text_x + n_surf.get_width(), text_cy + 2))

            cy += _ROW_H

        return cy + 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SLOT_KEYS = {
    pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4,
    pygame.K_6: 5, pygame.K_7: 6, pygame.K_8: 7, pygame.K_9: 8, pygame.K_0: 9,
}


def _key_to_slot(key: int) -> int | None:
    """Map pygame key 1–0 to hotbar slot index 0–9, or None."""
    return _SLOT_KEYS.get(key)
