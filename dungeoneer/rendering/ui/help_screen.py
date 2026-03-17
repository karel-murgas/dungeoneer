"""Help overlay — opened with F1, shows all key bindings."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t

_BG      = (10, 12, 20, 220)
_BORDER  = (80, 180, 160)
_COL_HDR = (80, 220, 200)
_COL_KEY = (80, 200, 160)
_COL_TXT = (180, 190, 210)
_COL_SEC = (120, 130, 150)
_COL_DIM = (70, 80, 95)

_PAD     = 16
_MIN_W   = 380
_MARGIN  = 40   # minimum gap between panel edge and screen edge

# Each section: (section_key, [(key_key, desc_key), ...])
_SECTIONS = [
    ("help.section.movement", [
        ("help.key.wasd",      "help.desc.wasd"),
        ("help.key.wait",      "help.desc.wait"),
        ("help.key.interact",  "help.desc.interact"),
    ]),
    ("help.section.combat", [
        ("help.key.shoot",     "help.desc.shoot"),
        ("help.key.reload",    "help.desc.reload"),
    ]),
    ("help.section.items", [
        ("help.key.heal",      "help.desc.heal"),
        ("help.key.inventory", "help.desc.inventory"),
        ("help.key.swap",      "help.desc.swap"),
    ]),
    ("help.section.general", [
        ("help.key.help",      "help.desc.help"),
        ("help.key.escape",    "help.desc.escape"),
    ]),
]


def _wrap_text(font: pygame.font.Font, text: str, max_w: int) -> list[str]:
    """Split *text* into lines that each fit within *max_w* pixels."""
    if font.size(text)[0] <= max_w:
        return [text]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if font.size(candidate)[0] <= max_w:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [text]


class HelpScreen:
    def __init__(self) -> None:
        self._font_hdr   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_key   = pygame.font.SysFont("consolas", 15, bold=True)
        self._font_desc  = pygame.font.SysFont("consolas", 15)
        self._font_title = pygame.font.SysFont("consolas", 18, bold=True)

    # ------------------------------------------------------------------

    def handle_key(self, key: int) -> bool:
        """Returns True if the help screen should close."""
        return key in (pygame.K_F1, pygame.K_ESCAPE, pygame.K_RETURN,
                       pygame.K_SPACE, pygame.K_KP_ENTER)

    # ------------------------------------------------------------------

    def _compute_layout(self, sw: int) -> tuple[int, list]:
        """Compute panel width and per-row wrapped lines.

        Returns (panel_width, layout) where layout is a list of
        (section_key, [(key_key, desc_lines), ...]) with desc_lines
        already word-wrapped to fit inside the panel.

        We iterate twice: first to find the minimum width needed for
        key badges, then clamp to screen, then wrap descriptions.
        """
        row_h_base = 22

        # --- Pass 1: find max key-badge width + title/footer/section widths ---
        max_badge_w = 0
        for _, rows in _SECTIONS:
            for key_key, _ in rows:
                kw = self._font_key.size(t(key_key))[0] + 10
                max_badge_w = max(max_badge_w, kw)

        badge_col_end = _PAD + max_badge_w + 10   # x where desc starts

        # Minimum panel width: fit title and footer without wrapping
        min_for_fixed = max(
            self._font_title.size(t("help.title"))[0] + 2 * _PAD,
            self._font_hdr.size(t("help.footer"))[0]  + 2 * _PAD,
        )
        # Also need room for at least the badge column plus some desc text
        min_content_w = badge_col_end + 60

        # Cap to screen
        max_w = sw - _MARGIN * 2
        w = max(max(min_for_fixed, min_content_w), _MIN_W)
        w = min(w, max_w)

        # Available width for description text
        desc_max_w = w - badge_col_end - _PAD

        # --- Pass 2: build layout with wrapped descriptions ---
        layout = []
        for section_key, rows in _SECTIONS:
            wrapped_rows = []
            for key_key, desc_key in rows:
                lines = _wrap_text(self._font_desc, t(desc_key), desc_max_w)
                wrapped_rows.append((key_key, lines))
            layout.append((section_key, wrapped_rows))

        # Check if any description actually needed more width (single-word overflow)
        # Recompute w to fit the longest single desc word if needed
        for _, rows in layout:
            for key_key, desc_lines in rows:
                for line in desc_lines:
                    needed = badge_col_end + self._font_desc.size(line)[0] + _PAD
                    w = min(max(w, needed), max_w)

        # Re-wrap with final w
        desc_max_w = w - badge_col_end - _PAD
        layout = []
        for section_key, rows in _SECTIONS:
            wrapped_rows = []
            for key_key, desc_key in rows:
                lines = _wrap_text(self._font_desc, t(desc_key), desc_max_w)
                wrapped_rows.append((key_key, lines))
            layout.append((section_key, wrapped_rows))

        return w, layout

    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        sw = settings.SCREEN_WIDTH
        sh = settings.SCREEN_HEIGHT

        row_h_base = 22
        sec_gap    = 10
        title_h    = 30
        footer_h   = 30
        line_h     = self._font_desc.get_height() + 2

        w, layout = self._compute_layout(sw)

        # Compute badge column end (same as in _compute_layout)
        max_badge_w = 0
        for _, rows in layout:
            for key_key, _ in rows:
                kw = self._font_key.size(t(key_key))[0] + 10
                max_badge_w = max(max_badge_w, kw)
        badge_col_end = _PAD + max_badge_w + 10

        # Compute total height
        total_h = _PAD + title_h
        for section_key, rows in layout:
            total_h += 14 + sec_gap + 2   # section header + separator
            for _, desc_lines in rows:
                row_h = max(row_h_base, len(desc_lines) * line_h + 4)
                total_h += row_h
        total_h += footer_h + _PAD

        # Clamp panel to screen height
        total_h = min(total_h, sh - _MARGIN * 2)

        ox = (sw - w) // 2
        oy = (sh - total_h) // 2

        # Background panel
        panel = pygame.Surface((w, total_h), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, w, total_h), 2)

        # Title
        title = self._font_title.render(t("help.title"), True, _COL_HDR)
        screen.blit(title, (ox + (w - title.get_width()) // 2, oy + _PAD))
        pygame.draw.line(screen, (40, 70, 65),
                         (ox + _PAD, oy + _PAD + title_h - 4),
                         (ox + w - _PAD, oy + _PAD + title_h - 4))

        cy = oy + _PAD + title_h + 4

        for section_key, rows in layout:
            # Section header
            sec_surf = self._font_hdr.render(t(section_key), True, _COL_SEC)
            screen.blit(sec_surf, (ox + _PAD, cy))
            cy += 16

            pygame.draw.line(screen, (30, 45, 42),
                             (ox + _PAD, cy),
                             (ox + w - _PAD, cy))
            cy += 4

            for key_key, desc_lines in rows:
                row_h = max(row_h_base, len(desc_lines) * line_h + 4)

                key_label = t(key_key)
                key_surf  = self._font_key.render(key_label, True, _COL_KEY)
                key_w     = key_surf.get_width() + 10
                badge     = pygame.Rect(ox + _PAD, cy + 1, key_w, row_h - 4)
                pygame.draw.rect(screen, (18, 35, 32), badge)
                pygame.draw.rect(screen, (45, 90, 80), badge, 1)
                screen.blit(key_surf, (ox + _PAD + 5, cy + 2))

                for i, line in enumerate(desc_lines):
                    desc_surf = self._font_desc.render(line, True, _COL_TXT)
                    screen.blit(desc_surf, (ox + badge_col_end, cy + 2 + i * line_h))

                cy += row_h

            cy += sec_gap

        # Footer
        pygame.draw.line(screen, (40, 70, 65),
                         (ox + _PAD, cy), (ox + w - _PAD, cy))
        cy += 6
        footer = self._font_hdr.render(t("help.footer"), True, _COL_DIM)
        screen.blit(footer, (ox + (w - footer.get_width()) // 2, cy))
