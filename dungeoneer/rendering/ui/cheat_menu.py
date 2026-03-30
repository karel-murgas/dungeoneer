"""Cheat / debug menu overlay — opened with F11 during a run.

Lets the developer spawn items, enemies, a chest, or adjust player stats.
This is a developer tool and intentionally bypasses normal game rules.
"""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
_BG       = (8, 10, 18, 235)
_BORDER   = (60, 160, 140)
_COL_HDR  = (60, 210, 190)     # section header
_COL_ITEM = (170, 190, 210)    # normal row
_COL_SEL  = (100, 230, 200)    # selected row text
_COL_DIM  = (60, 75, 90)       # inactive / section bg
_ROW_SEL  = (20, 55, 50, 200)  # selected row background (RGBA)
_ROW_HOV  = (15, 40, 35, 140)  # hovered row background (RGBA)

_W        = 440
_ROW_H    = 22
_PAD      = 14
_SECT_GAP = 6    # extra gap above a section header
_SCROLL_SPEED = 30  # pixels per wheel tick

# ---------------------------------------------------------------------------
# Menu data — list of (kind, label_key, action_id)
# kind: "section" → non-selectable header, "item" → selectable row
# ---------------------------------------------------------------------------
_ROWS: list[tuple[str, str, str | None]] = [
    ("section", "cheat.section.items",     None),
    ("item",    "item.pistol.name",         "spawn_item:pistol"),
    ("item",    "item.combat_knife.name",   "spawn_item:combat_knife"),
    ("item",    "item.shotgun.name",        "spawn_item:shotgun"),
    ("item",    "item.smg.name",            "spawn_item:smg"),
    ("item",    "item.energy_sword.name",   "spawn_item:energy_sword"),
    ("item",    "item.rifle.name",          "spawn_item:rifle"),
    ("item",    "item.stim_pack.name",      "spawn_item:stim_pack"),
    ("item",    "item.medkit.name",         "spawn_item:medkit"),
    ("item",    "cheat.item.ammo_9mm",      "spawn_item:ammo_9mm"),
    ("item",    "cheat.item.ammo_rifle",    "spawn_item:ammo_rifle"),
    ("item",    "cheat.item.ammo_shell",    "spawn_item:ammo_shell"),
    ("item",    "item.basic_armor.name",    "spawn_item:basic_armor"),
    ("section", "cheat.section.enemies",   None),
    ("item",    "entity.guard.name",        "spawn_enemy:guard"),
    ("item",    "entity.drone.name",        "spawn_enemy:drone"),
    ("item",    "entity.dog.name",          "spawn_enemy:dog"),
    ("item",    "entity.heavy.name",        "spawn_enemy:heavy"),
    ("item",    "entity.turret.name",       "spawn_enemy:turret"),
    ("item",    "entity.sniper_drone.name", "spawn_enemy:sniper_drone"),
    ("item",    "entity.riot_guard.name",   "spawn_enemy:riot_guard"),
    ("section", "cheat.section.container", None),
    ("item",    "cheat.spawn_chest",        "spawn_container"),
    ("section", "cheat.section.player",    None),
    ("item",    "cheat.hp.full",            "hp:full"),
    ("item",    "cheat.hp.set1",            "hp:1"),
    ("item",    "cheat.hp.plus10",          "hp:+10"),
    ("item",    "cheat.hp.plus20",          "hp:+20"),
    ("item",    "cheat.credits.plus100",    "credits:+100"),
    ("section", "cheat.section.heat",       None),
    ("item",    "cheat.heat.level1",        "heat_level:1"),
    ("item",    "cheat.heat.level2",        "heat_level:2"),
    ("item",    "cheat.heat.level3",        "heat_level:3"),
    ("item",    "cheat.heat.level4",        "heat_level:4"),
    ("item",    "cheat.heat.level5",        "heat_level:5"),
]

# Indices of selectable rows (kind == "item")
_SELECTABLE = [i for i, (kind, _, _a) in enumerate(_ROWS) if kind == "item"]

# Pre-compute the content-y (in pixels from content top) of every row.
# Used for auto-scroll-to-selection.
def _compute_row_content_y() -> dict[int, int]:
    cy = 0
    result: dict[int, int] = {}
    for row_i, (kind, _, _) in enumerate(_ROWS):
        if kind == "section":
            cy += _SECT_GAP
            result[row_i] = cy
            cy += _ROW_H
        else:
            result[row_i] = cy
            cy += _ROW_H
    return result

_ROW_CONTENT_Y = _compute_row_content_y()


class CheatMenuOverlay:
    """Scrollable cheat/debug overlay — toggled by F11."""

    def __init__(self) -> None:
        self._font_title = pygame.font.SysFont("consolas", 17, bold=True)
        self._font_sect  = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_item  = pygame.font.SysFont("consolas", 14)
        self._font_hint  = pygame.font.SysFont("consolas", 12)
        self._sel_idx    = 0          # index into _SELECTABLE
        self._hovered_action: str | None = None
        self._hovered_close  = False
        self._scroll_offset: int = 0  # pixels scrolled from content top
        # Computed in draw(), used by input handlers:
        self._content_h: int = 0      # total height of all rows
        self._view_h: int = 0         # visible height for rows
        self._content_top: int = 0    # screen-y where content area starts
        # Built each draw call:
        self._row_rects: dict[int, tuple[pygame.Rect, str]] = {}  # row_index → (rect, action)
        self._panel_rect: pygame.Rect | None = None
        self._close_rect: pygame.Rect | None = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _clamp_scroll(self) -> None:
        max_scroll = max(0, self._content_h - self._view_h)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

    def _scroll_to_sel(self) -> None:
        """Ensure the currently selected row is visible."""
        row_i = _SELECTABLE[self._sel_idx]
        row_top = _ROW_CONTENT_Y[row_i]
        row_bot = row_top + _ROW_H
        if row_top < self._scroll_offset:
            self._scroll_offset = row_top
        elif row_bot > self._scroll_offset + self._view_h:
            self._scroll_offset = row_bot - self._view_h
        self._clamp_scroll()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_key(self, key: int) -> str | None:
        """Return an action id or None.  Esc → 'close'."""
        if key in (pygame.K_ESCAPE, pygame.K_F11):
            return "close"
        if key in (pygame.K_UP, pygame.K_w):
            self._sel_idx = (self._sel_idx - 1) % len(_SELECTABLE)
            self._scroll_to_sel()
        elif key in (pygame.K_DOWN, pygame.K_s):
            self._sel_idx = (self._sel_idx + 1) % len(_SELECTABLE)
            self._scroll_to_sel()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            row_i = _SELECTABLE[self._sel_idx]
            return _ROWS[row_i][2]
        return None

    def handle_scroll(self, delta: int) -> None:
        """delta > 0 = scroll up (content moves up), delta < 0 = scroll down."""
        self._scroll_offset -= delta * _SCROLL_SPEED
        self._clamp_scroll()

    def handle_mouse_motion(self, pos: tuple[int, int]) -> None:
        self._hovered_action = None
        self._hovered_close  = bool(self._close_rect and self._close_rect.collidepoint(pos))
        for _row_i, (rect, action) in self._row_rects.items():
            if rect.collidepoint(pos):
                self._hovered_action = action
                break

    def handle_mouse_button(self, event: pygame.event.Event) -> str | None:
        if event.button != 1:
            return None
        # Close button
        if self._close_rect and self._close_rect.collidepoint(event.pos):
            return "close"
        # Click outside panel → close
        if self._panel_rect and not self._panel_rect.collidepoint(event.pos):
            return "close"
        # Row click
        for _row_i, (rect, action) in self._row_rects.items():
            if rect.collidepoint(event.pos):
                for si, ri in enumerate(_SELECTABLE):
                    if ri == _row_i:
                        self._sel_idx = si
                        break
                return action
        return None

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT

        title_h = 26
        sep_h   = 2
        hint_h  = 18
        # Height above the scrollable content area
        header_h = _PAD + title_h + sep_h + _SECT_GAP
        # Height below the scrollable content area
        footer_h = _SECT_GAP + hint_h + _PAD

        # Total content height (all rows, no cap)
        content_h = 0
        for kind, _, _ in _ROWS:
            if kind == "section":
                content_h += _SECT_GAP + _ROW_H
            else:
                content_h += _ROW_H
        self._content_h = content_h

        # Panel height: cap at 92% of screen
        max_h     = round(sh * 0.92)
        natural_h = _PAD * 2 + header_h + content_h + footer_h - _PAD  # _PAD counted once in header
        # Simpler: header_h already includes the top _PAD
        natural_h = header_h + content_h + footer_h
        panel_h   = min(natural_h, max_h)

        # Scrollable view height
        self._view_h = panel_h - header_h - footer_h
        self._clamp_scroll()

        ox = (sw - _W) // 2
        oy = (sh - panel_h) // 2
        self._panel_rect = pygame.Rect(ox, oy, _W, panel_h)
        self._content_top = oy + header_h

        # Background
        panel = pygame.Surface((_W, panel_h), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, panel_h), 2)

        # Close button [×] in top-right corner
        _CLOSE_SIZE = 18
        _CLOSE_PAD  = 6
        close_x = ox + _W - _CLOSE_SIZE - _CLOSE_PAD
        close_y = oy + _CLOSE_PAD
        self._close_rect = pygame.Rect(close_x, close_y, _CLOSE_SIZE, _CLOSE_SIZE)
        close_col = (220, 80, 80) if self._hovered_close else (120, 60, 60)
        m = 4
        pygame.draw.line(screen, close_col,
                         (close_x + m, close_y + m),
                         (close_x + _CLOSE_SIZE - m, close_y + _CLOSE_SIZE - m), 2)
        pygame.draw.line(screen, close_col,
                         (close_x + _CLOSE_SIZE - m, close_y + m),
                         (close_x + m, close_y + _CLOSE_SIZE - m), 2)

        # Title
        cy = oy + _PAD
        title_surf = self._font_title.render(t("cheat.title"), True, _COL_HDR)
        screen.blit(title_surf, (ox + (_W - title_surf.get_width()) // 2, cy))
        cy += title_h
        pygame.draw.line(screen, (40, 90, 80), (ox + _PAD, cy), (ox + _W - _PAD, cy))
        cy += sep_h + _SECT_GAP
        # cy is now at the top of the scrollable content area

        # --- Scrollable content ---
        clip_rect = pygame.Rect(ox, cy, _W, self._view_h)
        screen.set_clip(clip_rect)

        self._row_rects = {}
        sel_row_i = _SELECTABLE[self._sel_idx]
        content_cy = cy - self._scroll_offset  # screen y of content[0]

        for row_i, (kind, label_key, action) in enumerate(_ROWS):
            row_screen_y = content_cy + _ROW_CONTENT_Y[row_i]

            # Skip rows entirely outside the clip
            if row_screen_y + _ROW_H <= cy or row_screen_y >= cy + self._view_h:
                continue

            if kind == "section":
                lbl = self._font_sect.render(t(label_key).upper(), True, _COL_DIM)
                screen.blit(lbl, (ox + _PAD + 4, row_screen_y + _SECT_GAP + 3))
            else:
                row_rect = pygame.Rect(ox + 2, row_screen_y, _W - 4, _ROW_H)
                self._row_rects[row_i] = (row_rect, action)

                is_sel = (row_i == sel_row_i)
                is_hov = (action == self._hovered_action and not is_sel)

                if is_sel:
                    bg = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                    bg.fill(_ROW_SEL)
                    screen.blit(bg, row_rect.topleft)
                elif is_hov:
                    bg = pygame.Surface((row_rect.width, row_rect.height), pygame.SRCALPHA)
                    bg.fill(_ROW_HOV)
                    screen.blit(bg, row_rect.topleft)

                col = _COL_SEL if is_sel else _COL_ITEM
                lbl = self._font_item.render(t(label_key), True, col)
                screen.blit(lbl, (ox + _PAD + 16, row_screen_y + 3))

                if is_sel:
                    pygame.draw.polygon(
                        screen, _COL_SEL,
                        [(ox + _PAD + 4,  row_screen_y + _ROW_H // 2),
                         (ox + _PAD + 10, row_screen_y + 4),
                         (ox + _PAD + 10, row_screen_y + _ROW_H - 4)],
                    )

        screen.set_clip(None)
        # --- End scrollable content ---

        # Scrollbar (only when content overflows)
        if self._content_h > self._view_h:
            _SB_W   = 4
            _SB_PAD = 3
            sb_x    = ox + _W - _SB_W - _SB_PAD
            sb_top  = cy
            sb_h    = self._view_h
            # Track
            pygame.draw.rect(screen, (30, 50, 45), (sb_x, sb_top, _SB_W, sb_h))
            # Thumb
            ratio      = self._view_h / self._content_h
            thumb_h    = max(16, round(sb_h * ratio))
            thumb_top  = sb_top + round((sb_h - thumb_h) * self._scroll_offset / max(1, self._content_h - self._view_h))
            pygame.draw.rect(screen, _BORDER, (sb_x, thumb_top, _SB_W, thumb_h), border_radius=2)

        # Hint line (always at the bottom, outside clip)
        hint_y = oy + panel_h - _PAD - hint_h
        hint = self._font_hint.render(t("cheat.hint"), True, (80, 110, 100))
        screen.blit(hint, (ox + (_W - hint.get_width()) // 2, hint_y))
