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

_ASSETS_DIR    = os.path.join(os.path.dirname(__file__), "..", "assets")
_ASSETS_ITEMS  = os.path.join(_ASSETS_DIR, "items")
_ASSETS_TILES  = os.path.join(_ASSETS_DIR, "tiles")

_loot_pngs: dict[str, pygame.Surface | None] = {}
_container_pngs: dict[str, pygame.Surface | None] = {}


def _try_container_png(key: str, tile_size: int) -> "pygame.Surface | None":
    """Return container tile PNG scaled to tile_size, or None if not found."""
    if key not in _container_pngs:
        path = os.path.join(_ASSETS_TILES, f"{key}.png")
        if os.path.isfile(path):
            raw = pygame.image.load(path).convert_alpha()
            _container_pngs[key] = pygame.transform.scale(raw, (tile_size, tile_size))
        else:
            _container_pngs[key] = None
    return _container_pngs[key]
_SMALL_DROP_ITEMS = {"stim_pack"}   # rendered at 2/3 tile size on the floor


def _try_loot_png(item: "Item", tile_size: int) -> "pygame.Surface | None":  # type: ignore[name-defined]
    """Return a PNG icon scaled to tile_size, or None if no asset exists."""
    key = f"{item.item_type.name.lower()}_{item.id}"
    if key not in _loot_pngs:
        path = os.path.join(_ASSETS_ITEMS, f"{key}.png")
        if os.path.isfile(path):
            raw = pygame.image.load(path).convert_alpha()
            _loot_pngs[key] = pygame.transform.smoothscale(raw, (tile_size, tile_size))
        else:
            _loot_pngs[key] = None
    return _loot_pngs[key]


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

        # Draw containers — behave like tiles: show in fog-of-war, hide only unseen
        fog_overlay = pygame.Surface((ts, ts), pygame.SRCALPHA)
        fog_overlay.fill((0, 0, 0, 170))
        for container in floor.containers:
            dmap = floor.dungeon_map
            if not dmap.explored[container.y, container.x]:
                continue
            sx, sy = camera.world_to_screen(container.x, container.y)
            visible = dmap.visible[container.y, container.x]
            if getattr(container, "is_objective", False):
                key = "vault_open" if container.opened else "vault_closed"
                screen.blit(procedural_sprites.get(key), (sx, sy))
            else:
                png_key = "container_locker_open" if container.opened else "container_locker"
                surf = _try_container_png(png_key, ts) or procedural_sprites.get(
                    "container_open" if container.opened else "container_closed"
                )
                screen.blit(surf, (sx, sy))
            if not visible:
                screen.blit(fog_overlay, (sx, sy))

        # Draw item entities first (so actors render on top).
        # Credits drawn first at full size; other items render on top of them.
        credit_entities: list = []
        other_entities: list = []
        for item_e in floor.item_entities:
            if not floor.dungeon_map.visible[item_e.y, item_e.x]:
                continue
            if item_e.item.item_type == ItemType.CREDITS:
                credit_entities.append(item_e)
            else:
                other_entities.append(item_e)
        for item_e in credit_entities:
            sx, sy = camera.world_to_screen(item_e.x, item_e.y)
            sprite = _try_loot_png(item_e.item, ts) or procedural_sprites.get("item_hack_credits")
            screen.blit(sprite, (sx, sy))
        for item_e in other_entities:
            sx, sy = camera.world_to_screen(item_e.x, item_e.y)
            # PNG icon if asset exists; procedural fallback otherwise.
            # TODO: remove fallback once all item icons are available as PNG assets.
            surf = _try_loot_png(item_e.item, ts) or procedural_sprites.get(_loot_sprite_key(item_e.item))
            if item_e.item.item_type == ItemType.AMMO:
                half = ts // 2
                surf = pygame.transform.smoothscale(surf, (half, half))
                screen.blit(surf, (sx + ts // 4, sy + ts // 4))
            elif item_e.item.id in _SMALL_DROP_ITEMS:
                small = round(ts * 2 / 3)
                surf = pygame.transform.smoothscale(surf, (small, small))
                offset = (ts - small) // 2
                screen.blit(surf, (sx + offset, sy + offset))
            else:
                screen.blit(surf, (sx, sy))

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
