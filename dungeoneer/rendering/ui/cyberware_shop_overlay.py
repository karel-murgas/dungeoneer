"""CyberwareShopOverlay — hub shop for buying/upgrading perks.

Opened from MetaScene nav bar [Cyberware].  Shows a tabbed panel (Brain/Eyes/
Hands/Body/Legs) with a scrollable perk list on the left and a detail/buy panel
on the right.  Uses QuitConfirmDialog for purchase confirmation.
"""
from __future__ import annotations

from typing import Callable, Optional, TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.perks import CATALOG, BodyPart, PerkType, get_level, set_level, total_cost_to, desc_for_level
from dungeoneer.rendering.ui.quit_confirm import QuitConfirmDialog

if TYPE_CHECKING:
    from dungeoneer.meta.profile import Profile

# ---------------------------------------------------------------------------
# Visual constants
# ---------------------------------------------------------------------------

_BG           = (8, 8, 20, 240)
_BORDER       = (60, 200, 160)
_COL_HDR      = (0, 220, 180)
_COL_SEC      = (80, 200, 170)
_COL_TXT      = (170, 185, 200)
_COL_DIM      = (70, 85, 95)
_COL_VAL      = (220, 255, 240)
_COL_OWNED    = (0, 200, 140)
_COL_PARTIAL  = (180, 220, 180)
_COL_DEF_TXT  = (80, 100, 90)
_COL_ERROR    = (220, 60, 60)

_BTN_BG       = (20, 50, 40)
_BTN_HOV      = (30, 80, 65)
_BTN_DIS      = (16, 28, 24)
_BTN_BDR      = (0, 200, 160)
_BTN_BDR_DIS  = (35, 55, 50)
_BTN_TXT      = (220, 255, 240)

_TAB_SEL_BG   = (10, 70, 58)
_TAB_NRM_BG   = (18, 32, 28)
_TAB_HOV_BG   = (25, 55, 45)
_TAB_SEL_BDR  = (0, 220, 180)
_TAB_NRM_BDR  = (50, 160, 130)
_TAB_SEL_TXT  = (0, 240, 200)
_TAB_HOV_TXT  = (180, 220, 210)
_TAB_NRM_TXT  = (110, 145, 135)

_ROW_SEL_BG   = (12, 60, 50)
_ROW_HOV_BG   = (15, 45, 38)

_PAD      = 20
_PANEL_W  = 820
_PANEL_H  = 560
_TAB_H    = 34
_LIST_W   = 280
_ROW_H    = 32
_BTN_H    = 32
_BTN_W    = 160
_SEP      = (30, 55, 50)

_TAB_ORDER = [
    BodyPart.BRAIN, BodyPart.EYES, BodyPart.HANDS, BodyPart.BODY, BodyPart.LEGS
]
_TAB_I18N = {
    BodyPart.BRAIN: "cyberware.tab.brain",
    BodyPart.EYES:  "cyberware.tab.eyes",
    BodyPart.HANDS: "cyberware.tab.hands",
    BodyPart.BODY:  "cyberware.tab.body",
    BodyPart.LEGS:  "cyberware.tab.legs",
}


class CyberwareShopOverlay:
    """Tabbed cyberware purchase overlay for the MetaScene hub."""

    def __init__(
        self,
        profile: "Profile",
        on_close: Callable,
        on_purchase: Callable,   # called with (profile) after each purchase
    ) -> None:
        self._profile    = profile
        self._on_close   = on_close
        self._on_purchase = on_purchase

        self._font_title = pygame.font.SysFont("consolas", 19, bold=True)
        self._font_tab   = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_sec   = pygame.font.SysFont("consolas", 14, bold=True)
        self._font_body  = pygame.font.SysFont("consolas", 13)
        self._font_lbl   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_btn   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_small = pygame.font.SysFont("consolas", 12)

        self._selected_tab: BodyPart = BodyPart.BRAIN
        self._selected_perk_id: str | None = None
        self._scroll_offset: int = 0

        self._confirm_dialog: Optional[QuitConfirmDialog] = None
        self._confirm_perk_id: str | None = None

        # Hit-test rects (rebuilt each render)
        self._tab_rects:  list[tuple[str, pygame.Rect, BodyPart]] = []
        self._list_rects: dict[str, pygame.Rect] = {}
        self._btn_rects:  dict[str, pygame.Rect] = {}
        self._panel_rect: Optional[pygame.Rect] = None
        self._close_rect: Optional[pygame.Rect] = None
        self._close_hov  = False
        self._hovered: str | None = None

    # ------------------------------------------------------------------
    # Public interface (mirrors other overlays in this codebase)
    # ------------------------------------------------------------------

    def handle_events(self, events: list) -> None:
        for event in events:
            # Confirm dialog has priority
            if self._confirm_dialog is not None:
                if event.type == pygame.KEYDOWN:
                    result = self._confirm_dialog.handle_key(event.key)
                    self._handle_confirm_result(result)
                elif event.type == pygame.MOUSEMOTION:
                    self._confirm_dialog.handle_mouse_motion(event.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    result = self._confirm_dialog.handle_mouse_button(event)
                    self._handle_confirm_result(result)
                continue

            if event.type == pygame.KEYDOWN:
                self._handle_key(event.key)
            elif event.type == pygame.MOUSEMOTION:
                self._handle_motion(event.pos)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_click(event.pos)
            elif event.type == pygame.MOUSEWHEEL:
                self._scroll_offset = max(0, self._scroll_offset - event.y)

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        pw, ph = _PANEL_W, _PANEL_H
        ox = (sw - pw) // 2
        oy = (sh - ph) // 2

        # Reset rects
        self._tab_rects  = []
        self._list_rects = {}
        self._btn_rects  = {}

        # Background panel
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, pw, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, pw, ph)

        # Close button [x]
        close_size = 20
        self._close_rect = pygame.Rect(
            ox + pw - _PAD - close_size, oy + _PAD // 2,
            close_size, close_size,
        )
        if self._close_hov:
            pygame.draw.rect(screen, (60, 30, 30), self._close_rect, border_radius=3)
            pygame.draw.rect(screen, (180, 60, 60), self._close_rect, 1, border_radius=3)
        x_col = (180, 60, 60) if self._close_hov else _COL_DIM
        x_s = self._font_btn.render("x", True, x_col)
        screen.blit(x_s, (
            self._close_rect.centerx - x_s.get_width() // 2,
            self._close_rect.centery - self._font_btn.get_height() // 2 + 1,
        ))

        # Title + credits balance
        cy = oy + _PAD
        title_s = self._font_title.render(t("cyberware.title"), True, _COL_HDR)
        screen.blit(title_s, (ox + _PAD, cy))
        credits_s = self._font_lbl.render(
            f"¥ {self._profile.credits}", True, (0, 200, 140)
        )
        screen.blit(credits_s, (ox + pw - _PAD - close_size - 12 - credits_s.get_width(),
                                 cy + (title_s.get_height() - credits_s.get_height()) // 2 + 1))
        cy += title_s.get_height() + 8

        # Tabs
        self._draw_tabs(screen, ox, cy, pw)
        cy += _TAB_H + 6

        # Content split
        content_h = ph - (cy - oy) - _PAD
        self._draw_list(screen, ox + _PAD, cy, _LIST_W, content_h)

        detail_x = ox + _PAD + _LIST_W + 12
        detail_w = pw - _PAD - _LIST_W - 12 - _PAD
        self._draw_detail(screen, detail_x, cy, detail_w, content_h)

        # Confirm dialog on top
        if self._confirm_dialog is not None:
            self._confirm_dialog.draw(screen)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_tabs(self, screen: pygame.Surface, ox: int, cy: int, pw: int) -> None:
        n      = len(_TAB_ORDER)
        avail  = pw - _PAD * 2
        gap    = 4
        tab_w  = (avail - gap * (n - 1)) // n
        tx     = ox + _PAD

        for body in _TAB_ORDER:
            key      = f"tab_{body.value}"
            selected = body == self._selected_tab
            hov      = self._hovered == key
            bg  = _TAB_SEL_BG if selected else (_TAB_HOV_BG if hov else _TAB_NRM_BG)
            bdr = _TAB_SEL_BDR if selected else _TAB_NRM_BDR
            col = _TAB_SEL_TXT if selected else (_TAB_HOV_TXT if hov else _TAB_NRM_TXT)

            rect = pygame.Rect(tx, cy, tab_w, _TAB_H)
            pygame.draw.rect(screen, bg, rect, border_radius=4)
            pygame.draw.rect(screen, bdr, rect, 1, border_radius=4)

            lbl = self._font_tab.render(t(_TAB_I18N[body]).upper(), True, col)
            screen.blit(lbl, (
                rect.centerx - lbl.get_width() // 2,
                rect.centery - lbl.get_height() // 2 + 1,
            ))
            self._tab_rects.append((key, rect, body))
            tx += tab_w + gap

    def _draw_list(
        self, screen: pygame.Surface,
        lx: int, ly: int, lw: int, lh: int,
    ) -> None:
        self._list_rects = {}
        perks = self._perks_for_tab()

        old_clip = screen.get_clip()
        screen.set_clip(pygame.Rect(lx, ly, lw, lh))

        visible = lh // _ROW_H
        max_off = max(0, len(perks) - visible)
        self._scroll_offset = min(self._scroll_offset, max_off)

        for i, perk in enumerate(perks):
            row_y = ly + (i - self._scroll_offset) * _ROW_H
            if row_y + _ROW_H < ly or row_y > ly + lh:
                continue

            rect      = pygame.Rect(lx, row_y, lw, _ROW_H)
            selected  = perk.id == self._selected_perk_id
            hov       = self._hovered == f"list_{perk.id}"
            level     = get_level(self._profile, perk.id)

            if selected:
                pygame.draw.rect(screen, _ROW_SEL_BG, rect)
                pygame.draw.rect(screen, _TAB_SEL_BDR, rect, 1)
            elif hov:
                pygame.draw.rect(screen, _ROW_HOV_BG, rect)

            if perk.deferred:
                col    = _COL_DEF_TXT
                prefix = "   "
            elif level >= perk.max_level:
                col    = _COL_OWNED
                prefix = "[x]"
            elif level > 0:
                col    = _COL_PARTIAL
                prefix = f"[{level}]"
            else:
                col    = _COL_TXT
                prefix = "[ ]"

            raw  = f"{prefix} {t(perk.name_key)}"
            font = self._font_body
            # Truncate to fit
            while font.size(raw)[0] > lw - 10 and len(raw) > 4:
                raw = raw[:-1]
            lbl_s = font.render(raw, True, col)
            screen.blit(lbl_s, (rect.x + 6, rect.centery - lbl_s.get_height() // 2 + 1))

            self._list_rects[f"list_{perk.id}"] = rect

        screen.set_clip(old_clip)

        # Right border separator
        pygame.draw.line(screen, _SEP, (lx + lw + 6, ly), (lx + lw + 6, ly + lh))

    def _draw_detail(
        self, screen: pygame.Surface,
        dx: int, dy: int, dw: int, dh: int,
    ) -> None:
        if self._selected_perk_id is None:
            hint = self._font_body.render(t("cyberware.locked"), True, _COL_DIM)
            screen.blit(hint, (dx, dy + 20))
            return

        perk = CATALOG.get(self._selected_perk_id)
        if perk is None:
            return

        cy    = dy
        level = get_level(self._profile, perk.id)

        # Perk name (+ icon top-right for active perks)
        name_s = self._font_sec.render(t(perk.name_key), True, _COL_HDR)
        screen.blit(name_s, (dx, cy))
        if perk.type == PerkType.ACTIVE:
            from dungeoneer.rendering.perk_icons import get_icon
            icon = get_icon(perk.id, size=32)
            if icon is not None:
                screen.blit(icon, (dx + dw - 32, cy))
        cy += max(name_s.get_height(), 32 if perk.type == PerkType.ACTIVE else 0) + 4

        # Body part + type meta line
        meta_s = self._font_small.render(
            f"{t(f'perk.body.{perk.body.value}')}  |  {t(f'perk.type.{perk.type.value}')}",
            True, _COL_DIM,
        )
        screen.blit(meta_s, (dx, cy))
        cy += meta_s.get_height() + 6

        pygame.draw.line(screen, _SEP, (dx, cy), (dx + dw, cy))
        cy += 8

        # Level indicator for multi-level perks
        if perk.max_level > 1:
            lvl_s = self._font_small.render(
                f"{t('cyberware.lvl_label')}: {level} / {perk.max_level}", True, _COL_VAL
            )
            screen.blit(lvl_s, (dx, cy))
            cy += lvl_s.get_height() + 6

        # Description (wrapped) — level-specific text
        for line in self._wrap(desc_for_level(perk.id, max(level, 1)), dw - 4):
            s = self._font_body.render(line, True, _COL_TXT)
            screen.blit(s, (dx, cy))
            cy += s.get_height() + 2
        cy += 6

        # EP cost (active perks)
        if perk.type == PerkType.ACTIVE:
            if perk.ep_cost is not None:
                ep_s = self._font_small.render(f"EP: {perk.ep_cost}", True, (80, 200, 255))
            else:
                ep_s = self._font_small.render(f"EP/turn: {perk.ep_per_turn}", True, (80, 200, 255))
            screen.blit(ep_s, (dx, cy))
            cy += ep_s.get_height() + 4

        # Deferred notice
        if perk.deferred:
            def_s = self._font_lbl.render(t("perk.deferred"), True, _COL_DEF_TXT)
            screen.blit(def_s, (dx, cy))
            return

        # Buy / Upgrade button (or "fully owned")
        cy += 4
        if level < perk.max_level:
            cost       = total_cost_to(self._profile, perk.id, level + 1)
            can_afford = self._profile.credits >= cost

            btn_rect = pygame.Rect(dx, cy, _BTN_W, _BTN_H)
            self._btn_rects["buy_btn"] = btn_rect

            hov_btn = self._hovered == "buy_btn" and can_afford
            if can_afford:
                bg, bdr = (_BTN_HOV if hov_btn else _BTN_BG), _BTN_BDR
                lbl_col = _BTN_TXT
            else:
                bg, bdr = _BTN_DIS, _BTN_BDR_DIS
                lbl_col = _COL_ERROR

            pygame.draw.rect(screen, bg, btn_rect, border_radius=4)
            pygame.draw.rect(screen, bdr, btn_rect, 1, border_radius=4)

            btn_key = "cyberware.btn.buy" if level == 0 else "cyberware.btn.upgrade"
            lbl_s = self._font_btn.render(t(btn_key), True, lbl_col)
            screen.blit(lbl_s, (
                btn_rect.centerx - lbl_s.get_width() // 2,
                btn_rect.centery - lbl_s.get_height() // 2 + 1,
            ))

            # Price right of button
            price_col = _COL_ERROR if not can_afford else _COL_DIM
            price_s   = self._font_small.render(f"¥ {cost}", True, price_col)
            screen.blit(price_s, (
                btn_rect.right + 10,
                btn_rect.centery - price_s.get_height() // 2 + 1,
            ))

            if not can_afford:
                ins_s = self._font_small.render(t("cyberware.insufficient_credits"), True, _COL_ERROR)
                screen.blit(ins_s, (dx, cy + _BTN_H + 8))
        else:
            own_s = self._font_lbl.render(t("cyberware.fully_owned"), True, _COL_OWNED)
            screen.blit(own_s, (dx, cy + 4))

    # ------------------------------------------------------------------
    # Event helpers
    # ------------------------------------------------------------------

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self._on_close()
            return

        perks = self._perks_for_tab()
        ids   = [p.id for p in perks]

        if key in (pygame.K_DOWN, pygame.K_s):
            if not ids:
                return
            if self._selected_perk_id not in ids:
                self._selected_perk_id = ids[0]
            else:
                idx = ids.index(self._selected_perk_id)
                self._selected_perk_id = ids[(idx + 1) % len(ids)]
            self._clamp_scroll(perks)

        elif key in (pygame.K_UP, pygame.K_w):
            if not ids:
                return
            if self._selected_perk_id not in ids:
                self._selected_perk_id = ids[-1]
            else:
                idx = ids.index(self._selected_perk_id)
                self._selected_perk_id = ids[(idx - 1) % len(ids)]
            self._clamp_scroll(perks)

        elif key in (pygame.K_LEFT, pygame.K_a):
            i = _TAB_ORDER.index(self._selected_tab)
            self._selected_tab    = _TAB_ORDER[(i - 1) % len(_TAB_ORDER)]
            self._selected_perk_id = None
            self._scroll_offset   = 0

        elif key in (pygame.K_RIGHT, pygame.K_d):
            i = _TAB_ORDER.index(self._selected_tab)
            self._selected_tab    = _TAB_ORDER[(i + 1) % len(_TAB_ORDER)]
            self._selected_perk_id = None
            self._scroll_offset   = 0

        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._try_buy_selected()

    def _handle_motion(self, pos: tuple) -> None:
        self._hovered  = None
        self._close_hov = bool(self._close_rect and self._close_rect.collidepoint(pos))
        if self._close_hov:
            return
        for key, rect, _ in self._tab_rects:
            if rect.collidepoint(pos):
                self._hovered = key
                return
        for key, rect in self._list_rects.items():
            if rect.collidepoint(pos):
                self._hovered = key
                return
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                self._hovered = key
                return

    def _handle_click(self, pos: tuple) -> None:
        if self._close_rect and self._close_rect.collidepoint(pos):
            self._on_close()
            return
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            self._on_close()
            return

        for key, rect, body in self._tab_rects:
            if rect.collidepoint(pos):
                if body != self._selected_tab:
                    self._selected_tab     = body
                    self._selected_perk_id = None
                    self._scroll_offset    = 0
                return

        for key, rect in self._list_rects.items():
            if rect.collidepoint(pos):
                self._selected_perk_id = key[5:]   # strip "list_"
                return

        if "buy_btn" in self._btn_rects and self._btn_rects["buy_btn"].collidepoint(pos):
            self._try_buy_selected()

    def _handle_confirm_result(self, result: str | None) -> None:
        if result == "confirm":
            self._do_purchase(self._confirm_perk_id)
        elif result == "cancel":
            self._confirm_dialog   = None
            self._confirm_perk_id  = None

    def _try_buy_selected(self) -> None:
        pid = self._selected_perk_id
        if pid is None:
            return
        perk = CATALOG.get(pid)
        if perk is None or perk.deferred:
            return
        level = get_level(self._profile, pid)
        if level >= perk.max_level:
            return
        cost = total_cost_to(self._profile, pid, level + 1)
        if self._profile.credits < cost:
            return
        self._confirm_perk_id = pid
        self._confirm_dialog  = QuitConfirmDialog("cyberware_buy_confirm")

    def _do_purchase(self, perk_id: str | None) -> None:
        self._confirm_dialog  = None
        self._confirm_perk_id = None
        if perk_id is None:
            return
        perk = CATALOG.get(perk_id)
        if perk is None or perk.deferred:
            return
        level = get_level(self._profile, perk_id)
        if level >= perk.max_level:
            return
        cost  = total_cost_to(self._profile, perk_id, level + 1)
        if self._profile.credits < cost:
            return
        self._profile.credits -= cost
        set_level(self._profile, perk_id, level + 1)
        self._on_purchase(self._profile)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _perks_for_tab(self) -> list:
        non_def = [p for p in CATALOG.values() if p.body == self._selected_tab and not p.deferred]
        deferred = [p for p in CATALOG.values() if p.body == self._selected_tab and p.deferred]
        return non_def + deferred

    def _wrap(self, text: str, max_w: int) -> list[str]:
        font = self._font_body
        if font.size(text)[0] <= max_w:
            return [text]
        words  = text.split()
        lines: list[str] = []
        cur    = ""
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

    def _clamp_scroll(self, perks: list) -> None:
        if self._selected_perk_id is None:
            return
        ids = [p.id for p in perks]
        if self._selected_perk_id not in ids:
            return
        idx = ids.index(self._selected_perk_id)
        # Guess visible rows from panel height
        visible = (_PANEL_H - 120) // _ROW_H
        if idx < self._scroll_offset:
            self._scroll_offset = idx
        elif idx >= self._scroll_offset + visible:
            self._scroll_offset = idx - visible + 1
