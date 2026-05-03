"""RechargeNode — wall-embedded energy recharge station.

Placed on a wall tile with one cardinal floor neighbour.
Player presses E when adjacent to open the recharge overlay.
Single-use per floor.
"""
from __future__ import annotations

from dataclasses import dataclass

from dungeoneer.core.settings import RECHARGE_NODE_EP


@dataclass
class RechargeNode:
    x:           int
    y:           int
    capacity_ep: int  = RECHARGE_NODE_EP
    used:        bool = False
    sprite_key:  str  = "recharge_node"
