"""EntityRenderer: draws actors and items.

Drone enemies use the animated sci-fi drone sprite sheet (4 frames, 48×48,
scaled to 32×32). All other actors use coloured circles as before.
"""
from __future__ import annotations

import os

import pygame

from dungeoneer.core import settings
from dungeoneer.items.item import ItemType, RangeType
from dungeoneer.items.weapon import Weapon
from dungeoneer.rendering.spritesheet import SpriteSheet
from dungeoneer.rendering import procedural_sprites

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


def _loot_sprite_key(item: "Item") -> str:  # type: ignore[name-defined]
    """Return the procedural-sprite key appropriate for *item*."""
    if item.item_type == ItemType.CREDITS:
        return "item_hack_credits"
    if item.item_type == ItemType.AMMO:
        return "item_loot_ammo"
    if item.item_type == ItemType.CONSUMABLE:
        return "item_loot_consumable"
    if item.item_type == ItemType.ARMOR:
        return "item_loot_armor"
    if item.item_type == ItemType.WEAPON:
        if isinstance(item, Weapon) and item.range_type == RangeType.RANGED:
            return "item_loot_ranged"
        return "item_loot_melee"
    return "item_loot"

# Drone idle animation: 4 frames at 150 ms each
_DRONE_FRAME_MS = 150
_DRONE_FRAME_COUNT = 4
_DRONE_SPRITE_SIZE = 48   # source frame size
_DRONE_DRAW_SIZE = 32     # target size (= TILE_SIZE)


class EntityRenderer:
    def __init__(self) -> None:
        self._drone_frames: list[pygame.Surface] | None = None
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        path = os.path.join(_ASSETS_DIR, "entities", "drone_idle.png")
        if os.path.exists(path):
            sheet = SpriteSheet(path, _DRONE_SPRITE_SIZE, _DRONE_SPRITE_SIZE)
            self._drone_frames = [
                pygame.transform.scale(
                    sheet.get_tile_surface(i),
                    (_DRONE_DRAW_SIZE, _DRONE_DRAW_SIZE),
                )
                for i in range(_DRONE_FRAME_COUNT)
            ]

    def _current_drone_frame(self) -> pygame.Surface | None:
        if not self._drone_frames:
            return None
        idx = (pygame.time.get_ticks() // _DRONE_FRAME_MS) % _DRONE_FRAME_COUNT
        return self._drone_frames[idx]

    def draw(
        self,
        screen: pygame.Surface,
        floor: "Floor",    # type: ignore[name-defined]
        camera: "Camera",  # type: ignore[name-defined]
        hide_player: bool = False,
    ) -> None:
        self._init()
        ts = settings.TILE_SIZE
        half = ts // 2

        # Draw containers
        for container in floor.containers:
            if not floor.dungeon_map.visible[container.y, container.x]:
                continue
            sx, sy = camera.world_to_screen(container.x, container.y)
            if getattr(container, "is_objective", False):
                key = "vault_open" if container.opened else "vault_closed"
            else:
                key = "container_open" if container.opened else "container_closed"
            screen.blit(procedural_sprites.get(key), (sx, sy))

        # Draw item entities first (so actors render on top).
        # Credits sharing a tile with other loot are drawn smaller and offset
        # so both icons remain visible; alone they render at normal size.
        credit_entities: list = []
        non_credit_tiles: set = set()
        for item_e in floor.item_entities:
            if not floor.dungeon_map.visible[item_e.y, item_e.x]:
                continue
            if item_e.item.item_type == ItemType.CREDITS:
                credit_entities.append(item_e)
                continue
            non_credit_tiles.add((item_e.x, item_e.y))
            sx, sy = camera.world_to_screen(item_e.x, item_e.y)
            screen.blit(procedural_sprites.get(_loot_sprite_key(item_e.item)), (sx, sy))
        for item_e in credit_entities:
            sx, sy = camera.world_to_screen(item_e.x, item_e.y)
            sprite = procedural_sprites.get("item_hack_credits")
            if (item_e.x, item_e.y) in non_credit_tiles:
                # Stacked with other loot — shrink and nudge to top-right
                small = pygame.transform.scale(sprite, (ts * 2 // 3, ts * 2 // 3))
                screen.blit(small, (sx + ts // 3, sy - ts // 4))
            else:
                screen.blit(sprite, (sx, sy))

        # Draw actors
        for actor in floor.actors:
            if not floor.dungeon_map.visible[actor.y, actor.x]:
                continue
            sx, sy = camera.world_to_screen(actor.x, actor.y)

            is_drone = getattr(actor, "is_drone", False)
            actor_type = type(actor).__name__  # "Player" or "Enemy"

            if is_drone:
                frame = self._current_drone_frame()
                if frame is not None:
                    screen.blit(frame, (sx, sy))
                else:
                    pygame.draw.circle(screen, actor.render_colour, (sx + half, sy + half), half - 3)
            elif actor_type == "Player":
                if hide_player:
                    continue
                screen.blit(procedural_sprites.get("player"), (sx, sy))
            elif actor_type == "Enemy":
                screen.blit(procedural_sprites.get("guard"), (sx, sy))
            else:
                pygame.draw.circle(screen, actor.render_colour, (sx + half, sy + half), half - 3)

            self._draw_hp_bar(screen, sx, sy, ts, actor)

    def _draw_hp_bar(
        self,
        screen: pygame.Surface,
        sx: int, sy: int, ts: int,
        actor: "Actor",  # type: ignore[name-defined]
    ) -> None:
        if actor.hp >= actor.max_hp:
            return
        bar_w = ts - 4
        bar_h = 4
        ratio = max(0.0, actor.hp / actor.max_hp)
        pygame.draw.rect(screen, (60, 20, 20), (sx + 2, sy - 6, bar_w, bar_h))
        fill_col = settings.COL_HP_FULL if ratio > 0.4 else settings.COL_HP_LOW
        pygame.draw.rect(
            screen, fill_col, (sx + 2, sy - 6, round(bar_w * ratio), bar_h)
        )
