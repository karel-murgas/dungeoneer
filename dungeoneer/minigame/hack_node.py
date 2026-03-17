"""Data model for the hacking minigame node graph."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import auto, Enum
from typing import List, Optional


class NodeType(Enum):
    ENTRY    = auto()
    EMPTY    = auto()
    LOOT     = auto()
    SECURITY = auto()


class LootKind(Enum):
    AMMO         = auto()
    RIFLE_AMMO   = auto()
    SHOTGUN_AMMO = auto()
    HEAL         = auto()
    MEDKIT       = auto()
    WEAPON       = auto()
    CREDITS      = auto()
    BONUS_TIME   = auto()
    ARMOR        = auto()
    MYSTERY      = auto()   # resolves to a random non-mystery kind on collection


class SecurityKind(Enum):
    TIME_PENALTY = auto()
    DESTROY_LOOT = auto()
    BLOCKED      = auto()


@dataclass
class HackNode:
    node_id:       int
    ntype:         NodeType

    # Normalised layout position in [0, 1] — renderer scales to any viewport
    sx: float = 0.0
    sy: float = 0.0

    # Type-specific payload
    loot_kind:     Optional[LootKind]     = None
    security_kind: Optional[SecurityKind] = None

    # State
    hacked:   bool = False  # LOOT node has been collected
    revealed: bool = True   # SECURITY nodes start False (hidden)
    active:   bool = True   # False = destroyed by destroy_loot effect

    # flash_timer > 0 means render a red flash overlay (blocked FX)
    flash_timer: float = 0.0

    # Adjacency: list of node_ids (equals list index)
    neighbors: List[int] = field(default_factory=list)


@dataclass
class HackMap:
    nodes:    List[HackNode]
    entry_id: int = 0

    def get(self, node_id: int) -> HackNode:
        return self.nodes[node_id]

    def neighbors_of(self, node_id: int) -> List[HackNode]:
        """Return active neighbor nodes."""
        return [self.nodes[nid] for nid in self.nodes[node_id].neighbors
                if self.nodes[nid].active]
