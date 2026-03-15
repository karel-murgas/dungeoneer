"""An item lying on the floor."""
from __future__ import annotations

from dungeoneer.entities.entity import Entity
from dungeoneer.core import settings
from dungeoneer.items.item import Item


class ItemEntity(Entity):
    def __init__(self, x: int, y: int, item: Item) -> None:
        super().__init__(x, y, item.name, settings.COL_ITEM)
        self.item = item
