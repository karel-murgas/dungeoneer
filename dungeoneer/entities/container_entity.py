"""ContainerEntity — loot crate / chest on the dungeon floor."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from dungeoneer.items.item import Item


@dataclass
class ContainerEntity:
    x:            int
    y:            int
    items:        List["Item"] = field(default_factory=list)
    opened:       bool         = False
    name:         str          = "Crate"
    credits:      int          = 0
    is_objective: bool         = False
