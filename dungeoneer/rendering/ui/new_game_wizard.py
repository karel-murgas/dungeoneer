"""New Game Wizard — 4-step overlay for creating a new profile.

Steps:  1. Language  2. Agent Name  3. Difficulty  4. Tutorial

Pushed as an overlay inside MainMenuScene.  On Confirm the scene receives a
callback signal via ``_wizard_done(profile)`` to create + launch the run.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from dungeoneer.core import settings
from dungeoneer.core.i18n import t, set_language, get_language
from dungeoneer.meta.profile import Profile, GameplayFlags
from dungeoneer.meta.storage import sanitize_name, profile_exists, save_profile

if TYPE_CHECKING:
    from dungeoneer.scenes.main_menu_scene import MainMenuScene

# ---------------------------------------------------------------------------
# Visual constants (reuse main-menu palette)
# ---------------------------------------------------------------------------

_BG          = (8, 8, 20, 240)
_BORDER      = (60, 200, 160)
_COL_ACCENT  = (0, 220, 180)
_COL_SEC     = (60, 160, 140)
_COL_LBL     = (120, 150, 140)
_COL_WARN    = (220, 180, 60)
_COL_ERR     = (220, 80, 60)
_COL_INPUT   = (200, 230, 220)
_COL_CURSOR  = (0, 220, 180)

_BTN_NRM     = (20, 40, 35)
_BTN_SEL     = (10, 80, 65)
_BTN_HOV     = (35, 90, 70)
_COL_BDR_NRM = (60, 200, 160)
_COL_BDR_SEL = (0, 240, 200)
_COL_BDR_HOV = (100, 240, 200)
_COL_BTN_NRM = (140, 180, 160)
_COL_BTN_SEL = (220, 255, 240)
_COL_BTN_HOV = (200, 240, 220)
_COL_BDR_DIS = (40, 70, 60)
_COL_BTN_DIS = (70, 90, 80)

_W    = 520
_PAD  = 24
_BTN_H = 32
_BTN_W_SM = 80
_BTN_W_MD = 110
_ROW_H = 38

_STEPS = ["language", "name", "difficulty", "tutorial"]


class NewGameWizard:
    """4-step wizard overlay for creating a new profile."""

    def __init__(self, scene: "MainMenuScene") -> None:
        self._scene = scene
        self._step = 0  # 0-3

        # Choices accumulated through wizard
        self._lang       = get_language()
        self._raw_name   = ""          # raw typed text
        self._difficulty = "normal"
        self._tutorial   = False

        # UI state
        self._hovered: str | None = None
        self._btn_rects: dict[str, pygame.Rect] = {}
        self._panel_rect: pygame.Rect | None = None

        # Name step state
        self._name_error: str = ""        # validation error message
        self._name_warn: str = ""         # overwrite warning
        self._overwrite_pending = False   # waiting for overwrite confirm


        self._font_title = pygame.font.SysFont("consolas", 19, bold=True)
        self._font_step  = pygame.font.SysFont("consolas", 12, bold=True)
        self._font_lbl   = pygame.font.SysFont("consolas", 14, bold=True)
        self._font_btn   = pygame.font.SysFont("consolas", 13, bold=True)
        self._font_hint  = pygame.font.SysFont("consolas", 12)
        self._font_input = pygame.font.SysFont("consolas", 16, bold=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Return to step 1 with fresh state (call before showing)."""
        self._step = 0
        self._lang = get_language()
        self._raw_name = ""
        self._difficulty = "normal"
        self._tutorial = False
        self._name_error = ""
        self._name_warn = ""
        self._overwrite_pending = False
        self._hovered = None

    def handle_key(self, key: int) -> bool:
        """Return True if wizard consumed and is done (signals close)."""
        if key == pygame.K_ESCAPE:
            return True   # close wizard without creating profile

        if self._step == 1:  # name input
            return self._handle_name_key(key)

        if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._advance()
        return False

    def handle_text(self, char: str) -> None:
        """Handle TEXTINPUT events (name step only)."""
        if self._step == 1 and not self._overwrite_pending:
            self._raw_name += char
            self._name_error = ""
            self._name_warn = ""

    def handle_backspace(self) -> None:
        if self._step == 1 and not self._overwrite_pending:
            self._raw_name = self._raw_name[:-1]
            self._name_error = ""
            self._name_warn = ""

    def handle_motion(self, pos: tuple) -> None:
        self._hovered = self._hit_test(pos)

    def handle_click(self, pos: tuple) -> bool:
        """Return True if wizard is done (closed)."""
        if self._panel_rect and not self._panel_rect.collidepoint(pos):
            return True   # click outside = close
        hit = self._hit_test(pos)
        if hit is None:
            return False
        return self._dispatch(hit)

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT
        self._btn_rects = {}

        step_key = _STEPS[self._step]
        ph = self._compute_panel_height(step_key)
        ox = (sw - _W) // 2
        oy = (sh - ph) // 2

        panel = pygame.Surface((_W, ph), pygame.SRCALPHA)
        panel.fill(_BG)
        screen.blit(panel, (ox, oy))
        pygame.draw.rect(screen, _BORDER, (ox, oy, _W, ph), 2, border_radius=6)
        self._panel_rect = pygame.Rect(ox, oy, _W, ph)

        cy = oy + _PAD

        # Title + step label
        title_surf = self._font_title.render(t("wizard.title"), True, _COL_ACCENT)
        screen.blit(title_surf, (ox + (_W - title_surf.get_width()) // 2, cy))
        cy += title_surf.get_height() + 4
        step_surf = self._font_step.render(t(f"wizard.step.{step_key}"), True, _COL_SEC)
        screen.blit(step_surf, (ox + (_W - step_surf.get_width()) // 2, cy))
        cy += step_surf.get_height() + 10
        pygame.draw.line(screen, (30, 55, 50), (ox + _PAD, cy), (ox + _W - _PAD, cy))
        cy += 12

        # Step content
        if step_key == "language":
            cy = self._draw_language_step(screen, ox, cy)
        elif step_key == "name":
            cy = self._draw_name_step(screen, ox, cy)
        elif step_key == "difficulty":
            cy = self._draw_difficulty_step(screen, ox, cy)
        elif step_key == "tutorial":
            cy = self._draw_tutorial_step(screen, ox, cy)

        cy += 12
        pygame.draw.line(screen, (30, 55, 50), (ox + _PAD, cy), (ox + _W - _PAD, cy))
        cy += 12

        # Nav buttons: [Back] on left, [Next/Confirm] on right
        self._draw_nav(screen, ox, cy)

    # ------------------------------------------------------------------
    # Step content drawing
    # ------------------------------------------------------------------

    def _draw_language_step(self, screen: pygame.Surface, ox: int, cy: int) -> int:
        langs = [("en", "English"), ("cs", "Česky"), ("es", "Español")]
        bx = ox + _PAD
        for code, label in langs:
            btn_w = (_W - _PAD * 2 - 16) // 3
            rect = pygame.Rect(bx, cy, btn_w, _BTN_H)
            selected = self._lang == code
            self._draw_btn(screen, rect, f"lang_{code}", label, selected)
            bx += btn_w + 8
        return cy + _BTN_H + 8

    def _draw_name_step(self, screen: pygame.Surface, ox: int, cy: int) -> int:
        prompt = self._font_lbl.render(t("wizard.name.prompt"), True, _COL_LBL)
        screen.blit(prompt, (ox + _PAD, cy))
        cy += prompt.get_height() + 8

        # Input box
        box_rect = pygame.Rect(ox + _PAD, cy, _W - _PAD * 2, 34)
        pygame.draw.rect(screen, _BTN_NRM, box_rect, border_radius=4)
        pygame.draw.rect(screen, _COL_BDR_SEL, box_rect, 2, border_radius=4)

        try:
            sanitized = sanitize_name(self._raw_name) if self._raw_name.strip() else ""
        except ValueError:
            sanitized = ""

        display = sanitized if sanitized else ""
        cursor_str = display + ("" if self._overwrite_pending else "|")
        inp_surf = self._font_input.render(cursor_str, True, _COL_INPUT)
        screen.blit(inp_surf, (box_rect.x + 8,
                                box_rect.centery - inp_surf.get_height() // 2 + 1))
        cy += 38

        # Sanitized preview (greyed out)
        if self._raw_name and sanitized != self._raw_name.strip():
            hint_text = f"  -> {sanitized}" if sanitized else ""
            hint_surf = self._font_hint.render(hint_text, True, _COL_LBL)
            screen.blit(hint_surf, (ox + _PAD, cy))
            cy += hint_surf.get_height() + 4

        # Error / warning messages
        if self._name_error:
            err_surf = self._font_hint.render(self._name_error, True, _COL_ERR)
            screen.blit(err_surf, (ox + _PAD, cy))
            cy += err_surf.get_height() + 4
        if self._name_warn:
            warn_surf = self._font_hint.render(self._name_warn, True, _COL_WARN)
            screen.blit(warn_surf, (ox + _PAD, cy))
            cy += warn_surf.get_height() + 4

        # Overwrite confirm
        if self._overwrite_pending:
            q_surf = self._font_lbl.render(t("wizard.name.exists.confirm"), True, _COL_WARN)
            screen.blit(q_surf, (ox + (_W - q_surf.get_width()) // 2, cy))
            cy += q_surf.get_height() + 8
            btn_w = 160
            gap = 12
            total = btn_w * 2 + gap
            bx = ox + (_W - total) // 2
            yes_rect = pygame.Rect(bx, cy, btn_w, _BTN_H)
            no_rect  = pygame.Rect(bx + btn_w + gap, cy, btn_w, _BTN_H)
            self._draw_btn(screen, yes_rect, "overwrite_yes", t("wizard.name.exists.yes"), False)
            self._draw_btn(screen, no_rect,  "overwrite_no",  t("wizard.name.exists.no"),  False)
            cy += _BTN_H + 8

        return cy

    def _draw_difficulty_step(self, screen: pygame.Surface, ox: int, cy: int) -> int:
        diffs = [("easy", t("menu.easy")), ("normal", t("menu.normal")), ("hard", t("menu.hard"))]
        bx = ox + _PAD
        for key, label in diffs:
            btn_w = (_W - _PAD * 2 - 16) // 3
            rect = pygame.Rect(bx, cy, btn_w, _BTN_H)
            self._draw_btn(screen, rect, f"diff_{key}", label, self._difficulty == key)
            bx += btn_w + 8
        return cy + _BTN_H + 8

    def _draw_tutorial_step(self, screen: pygame.Surface, ox: int, cy: int) -> int:
        btn_w = (_W - _PAD * 2 - 8) // 2
        on_rect  = pygame.Rect(ox + _PAD, cy, btn_w, _BTN_H)
        off_rect = pygame.Rect(ox + _PAD + btn_w + 8, cy, btn_w, _BTN_H)
        self._draw_btn(screen, on_rect,  "tut_on",  t("wizard.tutorial.on"),  self._tutorial)
        self._draw_btn(screen, off_rect, "tut_off", t("wizard.tutorial.off"), not self._tutorial)
        return cy + _BTN_H + 8

    # ------------------------------------------------------------------
    # Nav buttons
    # ------------------------------------------------------------------

    def _draw_nav(self, screen: pygame.Surface, ox: int, cy: int) -> None:
        is_last = self._step == len(_STEPS) - 1
        confirm_label = t("wizard.confirm") if is_last else t("wizard.next")

        btn_w = 140
        # Back button (disabled on step 0)
        back_rect = pygame.Rect(ox + _PAD, cy, btn_w, _BTN_H)
        if self._step > 0:
            self._draw_btn(screen, back_rect, "nav_back", t("wizard.back"), False)
        else:
            self._draw_btn_disabled(screen, back_rect, t("wizard.back"))

        # Next/Confirm on right
        next_rect = pygame.Rect(ox + _W - _PAD - btn_w, cy, btn_w, _BTN_H)
        # Disable next on name step if overwrite pending
        if self._step == 1 and self._overwrite_pending:
            self._draw_btn_disabled(screen, next_rect, confirm_label)
        else:
            self._draw_btn(screen, next_rect, "nav_next", confirm_label, is_last)

    # ------------------------------------------------------------------
    # Drawing helpers
    # ------------------------------------------------------------------

    def _draw_btn(self, screen: pygame.Surface, rect: pygame.Rect,
                  key: str, label: str, selected: bool) -> None:
        hov = self._hovered == key
        if selected:
            bg, bdr, col = _BTN_SEL, _COL_BDR_SEL, _COL_BTN_SEL
        elif hov:
            bg, bdr, col = _BTN_HOV, _COL_BDR_HOV, _COL_BTN_HOV
        else:
            bg, bdr, col = _BTN_NRM, _COL_BDR_NRM, _COL_BTN_NRM
        pygame.draw.rect(screen, bg, rect, border_radius=4)
        pygame.draw.rect(screen, bdr, rect, 2, border_radius=4)
        lbl = self._font_btn.render(label, True, col)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                           rect.centery - lbl.get_height() // 2 + 1))
        self._btn_rects[key] = rect

    def _draw_btn_disabled(self, screen: pygame.Surface, rect: pygame.Rect,
                            label: str) -> None:
        pygame.draw.rect(screen, _BTN_NRM, rect, border_radius=4)
        pygame.draw.rect(screen, _COL_BDR_DIS, rect, 2, border_radius=4)
        lbl = self._font_btn.render(label, True, _COL_BTN_DIS)
        screen.blit(lbl, (rect.centerx - lbl.get_width() // 2,
                           rect.centery - lbl.get_height() // 2 + 1))

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _compute_panel_height(self, step_key: str) -> int:
        base = (
            _PAD                          # top pad
            + self._font_title.get_height() + 4
            + self._font_step.get_height() + 10
            + 1 + 12                      # sep + gap
            + _BTN_H + 8                  # content row
            + 12 + 1 + 12                 # sep + nav
            + _BTN_H                      # nav buttons
            + _PAD                        # bottom pad
        )
        if step_key == "name":
            extra = (
                self._font_lbl.get_height() + 8   # prompt
                + 38                               # input box
            )
            if self._name_error:
                extra += self._font_hint.get_height() + 4
            if self._name_warn:
                extra += self._font_hint.get_height() + 4
            if self._overwrite_pending:
                extra += self._font_lbl.get_height() + 8 + _BTN_H + 8
            return base + extra
        return base

    # ------------------------------------------------------------------
    # Hit testing and dispatch
    # ------------------------------------------------------------------

    def _hit_test(self, pos: tuple) -> str | None:
        for key, rect in self._btn_rects.items():
            if rect.collidepoint(pos):
                return key
        return None

    def _dispatch(self, hit: str) -> bool:
        """Return True to close the wizard."""
        if hit.startswith("lang_"):
            code = hit[5:]
            self._lang = code
            set_language(code)
            return False
        if hit.startswith("diff_"):
            self._difficulty = hit[5:]
            return False
        if hit == "tut_on":
            self._tutorial = True
            return False
        if hit == "tut_off":
            self._tutorial = False
            return False
        if hit == "overwrite_yes":
            self._overwrite_pending = False
            self._name_warn = ""
            self._advance()
            return False
        if hit == "overwrite_no":
            self._overwrite_pending = False
            self._name_warn = ""
            self._raw_name = ""
            return False
        if hit == "nav_back":
            if self._step > 0:
                self._step -= 1
            return False
        if hit == "nav_next":
            return self._advance()
        return False

    def _handle_name_key(self, key: int) -> bool:
        if self._overwrite_pending:
            return False
        if key == pygame.K_BACKSPACE:
            self.handle_backspace()
        elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            return self._advance()
        return False

    def _advance(self) -> bool:
        """Validate current step and advance. Return True if wizard finishes."""
        step_key = _STEPS[self._step]

        if step_key == "name":
            try:
                sanitized = sanitize_name(self._raw_name)
            except ValueError:
                self._name_error = t("wizard.name.invalid")
                return False
            # Check overwrite
            if profile_exists(sanitized) and not self._overwrite_pending:
                self._name_warn = t("wizard.name.exists.warning")
                self._overwrite_pending = True
                return False
            self._overwrite_pending = False
            self._name_warn = ""

        if self._step < len(_STEPS) - 1:
            self._step += 1
            return False

        # Final step — build profile and signal scene
        self._finish()
        return True

    def _finish(self) -> None:
        try:
            name = sanitize_name(self._raw_name)
        except ValueError:
            name = "Agent"
        profile = Profile(
            name=name,
            language=self._lang,
            difficulty=self._difficulty,
            tutorial_enabled=self._tutorial,
            flags=GameplayFlags(),
        )
        save_profile(profile)
        self._scene._wizard_done(profile)
