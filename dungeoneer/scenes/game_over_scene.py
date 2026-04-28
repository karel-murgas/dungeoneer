"""Game over / run summary screen."""
from __future__ import annotations

from typing import List, TYPE_CHECKING

import pygame

from dungeoneer.core.scene import Scene
from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.core.difficulty import Difficulty

if TYPE_CHECKING:
    from dungeoneer.core.game import GameApp
    from dungeoneer.core.stats import RunStats

_BTN_W  = 230
_BTN_H  = 44
_BTN_NRM = (20, 40, 35)
_BTN_HOV = (35, 90, 70)
_COL_BORDER     = (60, 200, 160)
_COL_BORDER_HOV = (100, 240, 200)

_COL_SEC  = (0, 180, 140)
_COL_LBL  = (140, 160, 155)
_COL_VAL  = (210, 245, 230)
_COL_DIM  = (70, 85, 95)
_COL_SEP  = (30, 55, 48)

_STAT_ROW_H = 20   # px per stat row
_STAT_FONT_SIZE = 15


class GameOverScene(Scene):
    def __init__(
        self, app: "GameApp", *, victory: bool, floor_depth: int,
        difficulty: Difficulty | None = None,
        use_minigame: bool = True,
        use_aim_minigame: bool = True,
        use_melee_minigame: bool = True,
        credits_earned: int = 0,
        credits_before: int = 0,
        profile=None,
        run_stats: "RunStats | None" = None,
        audio=None,
        map_size: str = "large",
    ) -> None:
        super().__init__(app)
        self.victory             = victory
        self.floor_depth         = floor_depth
        self._difficulty         = difficulty
        self._use_minigame       = use_minigame
        self._use_aim_minigame   = use_aim_minigame
        self._use_melee_minigame = use_melee_minigame
        self._map_size           = map_size
        self._credits_earned  = credits_earned
        self._credits_before  = credits_before
        self._profile         = profile
        self._run_stats       = run_stats
        self._audio           = audio
        self._font_big   = pygame.font.SysFont("consolas", 52, bold=True)
        self._font_med   = pygame.font.SysFont("consolas", 26)
        self._font_small = pygame.font.SysFont("consolas", 18)
        self._font_stat  = pygame.font.SysFont("consolas", _STAT_FONT_SIZE)
        self._font_stat_b= pygame.font.SysFont("consolas", _STAT_FONT_SIZE, bold=True)
        self._font_btn   = pygame.font.SysFont("consolas", 18, bold=True)
        self._btn_menu: pygame.Rect | None = None
        self._hovered: bool = False

    def on_enter(self) -> None:
        if self._audio:
            self._audio.play("victory" if self.victory else "defeat", volume=0.85)

    def handle_events(self, events: List[pygame.event.Event]) -> None:
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._go_to_menu()

            elif event.type == pygame.MOUSEMOTION:
                self._hovered = bool(
                    self._btn_menu and self._btn_menu.collidepoint(event.pos)
                )

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._btn_menu and self._btn_menu.collidepoint(event.pos):
                    self._go_to_menu()

    def update(self, dt: float) -> None:
        pass

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((8, 8, 16))
        sw, sh = settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT

        if self.victory:
            title  = t("gameover.victory")
            colour = (0, 220, 180)
            sub    = t("gameover.victory_sub")
        else:
            title  = t("gameover.defeat")
            colour = (220, 60, 60)
            sub    = t("gameover.defeat_sub")

        cy = sh // 6

        # Title
        t_surf = self._font_big.render(title, True, colour)
        screen.blit(t_surf, (sw // 2 - t_surf.get_width() // 2, cy))
        cy += t_surf.get_height() + 10

        # Subtitle
        s_surf = self._font_med.render(sub, True, (180, 180, 180))
        screen.blit(s_surf, (sw // 2 - s_surf.get_width() // 2, cy))
        cy += s_surf.get_height() + 14

        # Floors cleared
        depth_surf = self._font_small.render(
            t("gameover.floors").format(n=self.floor_depth), True, (120, 120, 140)
        )
        screen.blit(depth_surf, (sw // 2 - depth_surf.get_width() // 2, cy))
        cy += depth_surf.get_height() + 8

        # Credits earned
        cr_colour = (80, 220, 120) if self._credits_earned > 0 else (100, 100, 120)
        cr_surf = self._font_med.render(
            t("gameover.credits").format(n=self._credits_earned), True, cr_colour
        )
        screen.blit(cr_surf, (sw // 2 - cr_surf.get_width() // 2, cy))
        cy += cr_surf.get_height() + 6

        # Credits pool
        if self._profile is not None:
            pool = self._credits_before + self._credits_earned
            pool_surf = self._font_small.render(
                t("gameover.credits_pool").format(n=pool), True, (100, 160, 130)
            )
            screen.blit(pool_surf, (sw // 2 - pool_surf.get_width() // 2, cy))
            cy += pool_surf.get_height() + 6

        # Run stats block
        if self._run_stats is not None:
            cy += 10
            cy = self._draw_stats_block(screen, sw, cy)

        # Button
        btn_y = sh * 5 // 6 - _BTN_H // 2
        self._btn_menu = pygame.Rect(sw // 2 - _BTN_W // 2, btn_y, _BTN_W, _BTN_H)

        is_hov = self._hovered
        pygame.draw.rect(screen, _BTN_HOV if is_hov else _BTN_NRM,
                         self._btn_menu, border_radius=4)
        pygame.draw.rect(screen, _COL_BORDER_HOV if is_hov else _COL_BORDER,
                         self._btn_menu, 2, border_radius=4)
        lbl = self._font_btn.render(t("gameover.menu"), True,
                                    (220, 255, 240) if is_hov else (140, 180, 160))
        screen.blit(lbl, (self._btn_menu.centerx - lbl.get_width() // 2,
                           self._btn_menu.centery - lbl.get_height() // 2))

    # ------------------------------------------------------------------
    # Stats block
    # ------------------------------------------------------------------

    def _draw_stats_block(self, screen: pygame.Surface, sw: int, cy: int) -> int:
        rs = self._run_stats
        panel_w = 480
        ox = (sw - panel_w) // 2

        # Section header
        hdr = self._font_stat_b.render(t("gameover.run_stats_header"), True, _COL_SEC)
        screen.blit(hdr, (ox, cy))
        cy += hdr.get_height() + 3
        pygame.draw.line(screen, _COL_SEP, (ox, cy), (ox + panel_w, cy))
        cy += 7

        # "Killed by" — only on defeat, only if we know the killer
        if not self.victory and rs.deaths_by_killer:
            killer_id = max(rs.deaths_by_killer, key=lambda k: rs.deaths_by_killer[k])
            killer_name = t(f"entity.{killer_id}.name")
            kb_surf = self._font_stat_b.render(
                t("gameover.killed_by").format(name=killer_name), True, (220, 80, 80)
            )
            screen.blit(kb_surf, (ox, cy))
            cy += kb_surf.get_height() + 10
            pygame.draw.line(screen, _COL_SEP, (ox, cy), (ox + panel_w, cy))
            cy += 7

        # Stat rows
        rows = self._build_stat_rows(rs)
        for label, value in rows:
            cy = self._draw_stat_row(screen, ox, cy, panel_w, label, value)

        return cy

    def _build_stat_rows(self, rs: "RunStats") -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []

        # Kills — total then per weapon (weapons with at least 1 kill)
        rows.append((t("stats.kills_total"), str(rs.kills_total)))
        for weapon_id, count in sorted(rs.kills_by_weapon.items(),
                                        key=lambda x: x[1], reverse=True):
            rows.append(("  " + t(f"item.{weapon_id}.name"),
                          t("stats.kills_count").format(n=count)))

        # Ammo + crits
        rows.append((t("stats.bullets_shot"), str(rs.bullets_shot)))
        if rs.crits_ranged:
            rows.append(("  " + t("stats.crits_ranged"), str(rs.crits_ranged)))
        if rs.crits_melee:
            rows.append(("  " + t("stats.crits_melee"), str(rs.crits_melee)))

        # Healing
        rows.append((t("stats.hp_healed"), str(rs.hp_healed)))

        # Hacking — only show section if any hack activity occurred
        if rs.containers_hacked or rs.containers_failed or rs.nodes_hacked:
            rows.append((t("stats.containers_hacked"), str(rs.containers_hacked)))
            if rs.containers_fully_hacked:
                rows.append(("  " + t("stats.containers_fully_hacked"),
                              str(rs.containers_fully_hacked)))
            if rs.containers_failed:
                rows.append((t("stats.containers_failed"), str(rs.containers_failed)))
            if rs.nodes_hacked:
                rows.append((t("stats.nodes_hacked"), str(rs.nodes_hacked)))

        return rows

    def _draw_stat_row(self, screen: pygame.Surface, ox: int, cy: int,
                        panel_w: int, label: str, value: str) -> int:
        lbl_surf = self._font_stat.render(label, True, _COL_LBL)
        val_surf = self._font_stat_b.render(value, True, _COL_VAL)
        screen.blit(lbl_surf, (ox, cy))
        screen.blit(val_surf, (ox + panel_w - val_surf.get_width(), cy))
        return cy + _STAT_ROW_H

    # ------------------------------------------------------------------

    def _go_to_menu(self) -> None:
        if self._profile is not None:
            from dungeoneer.meta.storage import load_global
            from dungeoneer.scenes.meta_scene import MetaScene
            self.app.scenes.replace(MetaScene(self.app, self._profile, load_global()))
        else:
            from dungeoneer.scenes.main_menu_scene import MainMenuScene
            self.app.scenes.replace(MainMenuScene(self.app))
