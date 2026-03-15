"""Floor: spatial container for the current dungeon level."""
from __future__ import annotations

from typing import Optional

from dungeoneer.world.map import DungeonMap
from dungeoneer.entities.actor import Actor
from dungeoneer.entities.item_entity import ItemEntity
from dungeoneer.entities.container_entity import ContainerEntity


class Floor:
    def __init__(self, dungeon_map: DungeonMap, depth: int = 1) -> None:
        self.dungeon_map  = dungeon_map
        self.depth        = depth
        self.actors:        list[Actor]           = []
        self.item_entities: list[ItemEntity]      = []
        self.containers:    list[ContainerEntity] = []

    # ------------------------------------------------------------------
    # Spatial queries
    # ------------------------------------------------------------------

    def get_actor_at(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y and actor.alive:
                return actor
        return None

    def get_item_at(self, x: int, y: int) -> Optional[ItemEntity]:
        for item_e in self.item_entities:
            if item_e.x == x and item_e.y == y:
                return item_e
        return None

    def get_items_at(self, x: int, y: int) -> list[ItemEntity]:
        return [ie for ie in self.item_entities if ie.x == x and ie.y == y]

    def remove_dead(self) -> list[Actor]:
        dead = [a for a in self.actors if not a.alive]
        self.actors = [a for a in self.actors if a.alive]
        return dead

    def remove_item_entity(self, item_e: ItemEntity) -> None:
        self.item_entities.remove(item_e)

    def add_actor(self, actor: Actor) -> None:
        self.actors.append(actor)

    def add_item_entity(self, item_e: ItemEntity) -> None:
        self.item_entities.append(item_e)

    def get_container_at(self, x: int, y: int) -> Optional[ContainerEntity]:
        for c in self.containers:
            if c.x == x and c.y == y and not c.opened:
                return c
        return None

    def add_container(self, container: ContainerEntity) -> None:
        self.containers.append(container)
