"""Range overlay — tints visible floor tiles within the equipped weapon's range."""
from __future__ import annotations

import pygame

from dungeoneer.core import settings
from dungeoneer.items.item import RangeType


# Colours (R, G, B, A)
_COL_RANGE_NEAR  = (40,  190, 160,  28)   # dim teal — well within range
_COL_RANGE_EDGE  = (60,  220, 190,  60)   # brighter teal — at the range boundary
_COL_ENEMY_NEAR  = (220,  70,  50,  60)   # red — targetable enemy
_COL_ENEMY_EDGE  = (255, 100,  60,  90)   # brighter red — enemy exactly at range limit
_COL_NO_AMMO     = ( 90,  90, 110,  22)   # grey — weapon empty, range still shown dimly


class RangeOverlay:
    def __init__(self) -> None:
        ts = settings.TILE_SIZE
        self._surf = pygame.Surface((ts, ts), pygame.SRCALPHA)

    def draw(
        self,
        screen: pygame.Surface,
        floor:  "Floor",   # type: ignore[name-defined]
        player: "Player",  # type: ignore[name-defined]
        camera: "Camera",  # type: ignore[name-defined]
    ) -> None:
        w = player.equipped_weapon
        if w is None or w.range_type != RangeType.RANGED:
            return

        max_range   = w.range_tiles
        has_ammo    = w.ammo_current > 0
        ts          = settings.TILE_SIZE
        dmap        = floor.dungeon_map

        # Build set of enemy positions that are in range + have LOS
        from dungeoneer.entities.enemy import Enemy
        from dungeoneer.combat.line_of_sight import has_los

        enemy_range: set[tuple[int, int]] = set()
        if has_ammo:
            for actor in floor.actors:
                if isinstance(actor, Enemy) and actor.alive:
                    if not dmap.visible[actor.y, actor.x]:
                        continue
                    dist = abs(actor.x - player.x) + abs(actor.y - player.y)
                    if dist <= max_range and has_los(
                        player.x, player.y, actor.x, actor.y, dmap
                    ):
                        enemy_range.add((actor.x, actor.y))

        for dy in range(-max_range, max_range + 1):
            for dx in range(-max_range, max_range + 1):
                dist = abs(dx) + abs(dy)
                if dist == 0 or dist > max_range:
                    continue
                tx, ty = player.x + dx, player.y + dy
                if not (0 <= tx < dmap.width and 0 <= ty < dmap.height):
                    continue
                if not dmap.visible[ty, tx]:
                    continue
                if not dmap.walkable[ty, tx]:
                    continue  # skip walls — only tint open floor

                sx, sy = camera.world_to_screen(tx, ty)
                # Off-screen cull
                if sx + ts < 0 or sy + ts < 0:
                    continue
                if sx > settings.SCREEN_WIDTH or sy > settings.SCREEN_HEIGHT:
                    continue

                at_edge = (dist == max_range)

                if not has_ammo:
                    col = _COL_NO_AMMO
                elif (tx, ty) in enemy_range:
                    col = _COL_ENEMY_EDGE if at_edge else _COL_ENEMY_NEAR
                else:
                    col = _COL_RANGE_EDGE if at_edge else _COL_RANGE_NEAR

                self._surf.fill(col)
                screen.blit(self._surf, (sx, sy))
