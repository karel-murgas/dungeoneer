"""Player inventory — fixed-size slot list."""
from __future__ import annotations
from typing import Iterator

from dungeoneer.items.item import Item

MAX_SLOTS = 8


class Inventory:
    def __init__(self) -> None:
        self._items: list[Item] = []

    @property
    def is_full(self) -> bool:
        return len(self._items) >= MAX_SLOTS

    def add(self, item: Item) -> bool:
        from dungeoneer.items.consumable import Consumable
        # Consumables with the same id stack onto an existing slot
        if isinstance(item, Consumable):
            existing = next(
                (i for i in self._items if isinstance(i, Consumable) and i.id == item.id),
                None,
            )
            if existing is not None:
                existing.count += item.count
                return True
        if self.is_full:
            return False
        self._items.append(item)
        return True

    def remove(self, item: Item) -> bool:
        if item in self._items:
            self._items.remove(item)
            return True
        return False

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterator[Item]:
        return iter(list(self._items))

    def __getitem__(self, idx: int) -> Item:
        return self._items[idx]
