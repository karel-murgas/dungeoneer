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
    ) -> None:
        screen.fill(settings.COL_BLACK)

        self.camera.center_on(
            player.x, player.y,
            floor.dungeon_map.width, floor.dungeon_map.height
        )

        self.tile_renderer.draw(screen, floor.dungeon_map, self.camera)
        self.range_overlay.draw(screen, floor, player, self.camera)
        self.entity_renderer.draw(screen, floor, self.camera)

        if hud:
            hud.draw(screen, player)
        if combat_log:
            combat_log.draw(screen)
