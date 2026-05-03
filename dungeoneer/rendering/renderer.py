"""Master renderer — orchestrates all draw layers."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.rendering.camera import Camera
from dungeoneer.rendering.tile_renderer import TileRenderer
from dungeoneer.rendering.entity_renderer import EntityRenderer
from dungeoneer.rendering.range_overlay import RangeOverlay


class Renderer:
    def __init__(self) -> None:
        self.camera          = Camera()
        self.tile_renderer   = TileRenderer()
        self.range_overlay   = RangeOverlay()
        self.entity_renderer = EntityRenderer()

    def draw(
        self,
        screen: pygame.Surface,
        floor: "Floor",    # type: ignore[name-defined]
        player: "Player",  # type: ignore[name-defined]
        hud: "HUD | None" = None,          # type: ignore[name-defined]
        combat_log: "CombatLog | None" = None,  # type: ignore[name-defined]
        hide_player: bool = False,
    ) -> None:
        screen.fill(settings.COL_BLACK)

        self.camera.center_on(
            player.x, player.y,
            floor.dungeon_map.width, floor.dungeon_map.height
        )

        # Clip tiles/entities to the viewport so they never bleed into HUD bands.
        vp_h = settings.SCREEN_HEIGHT - settings.VIEWPORT_Y_TOP - settings.VIEWPORT_Y_BOTTOM
        screen.set_clip(pygame.Rect(0, settings.VIEWPORT_Y_TOP, settings.SCREEN_WIDTH, vp_h))

        self.tile_renderer.draw(screen, floor.dungeon_map, self.camera)
        self.range_overlay.draw(screen, floor, player, self.camera)
        self.entity_renderer.draw(screen, floor, self.camera, hide_player=hide_player)

        screen.set_clip(None)

        # Subtle separator lines between tile viewport and HUD bands.
        _sep = (30, 40, 55)
        pygame.draw.line(screen, _sep,
                         (0, settings.VIEWPORT_Y_TOP - 1),
                         (settings.SCREEN_WIDTH - 1, settings.VIEWPORT_Y_TOP - 1))
        pygame.draw.line(screen, _sep,
                         (0, settings.SCREEN_HEIGHT - settings.VIEWPORT_Y_BOTTOM),
                         (settings.SCREEN_WIDTH - 1, settings.SCREEN_HEIGHT - settings.VIEWPORT_Y_BOTTOM))

        if hud:
            hud.draw(screen, player)
        if combat_log:
            combat_log.draw(screen)
