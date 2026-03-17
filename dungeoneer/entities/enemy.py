"""Enemy entity types and loot tables."""
from __future__ import annotations

import random
from typing import Optional

from dungeoneer.core import settings
from dungeoneer.core.i18n import t
from dungeoneer.entities.actor import Actor
from dungeoneer.ai.brain import AIBrain
from dungeoneer.items.item import Item


class Enemy(Actor):
    def __init__(
        self,
        x: int, y: int,
        name: str,
        render_colour: tuple,
        *,
        max_hp: int,
        attack: int,
        defence: int,
        is_drone: bool = False,
        aim_skill: float = 2.5,
        loot_table: list[tuple[float, str]] | None = None,
    ) -> None:
        super().__init__(
            x, y, name, render_colour,
            max_hp=max_hp, attack=attack, defence=defence,
        )
        self.is_drone     = is_drone
        self.aim_skill    = aim_skill  # controls ranged accuracy sigma; higher = more consistent
        self.ai_brain     = AIBrain()
        self.ai_brain.attach(self)
        self.credits_drop = 15 if is_drone else 10
        # loot_table: list of (probability, item_id) pairs, evaluated in order
        self._loot_table  = loot_table or []

    def drop_loot(self) -> Optional[Item]:
        """Roll the loot table. Returns an Item instance or None."""
        from dungeoneer.items.weapon import make_combat_knife, make_shotgun, make_energy_sword
        from dungeoneer.items.consumable import make_stim_pack, make_medkit
        from dungeoneer.items.ammo import make_9mm_ammo

        _factories = {
            "combat_knife":  make_combat_knife,
            "shotgun":       make_shotgun,
            "energy_sword":  make_energy_sword,
            "stim_pack":     make_stim_pack,
            "medkit":        make_medkit,
            "ammo_9mm":      lambda: make_9mm_ammo(5),
        }

        roll = random.random()
        cumulative = 0.0
        for prob, item_id in self._loot_table:
            cumulative += prob
            if roll < cumulative:
                factory = _factories.get(item_id)
                return factory() if factory else None
        return None


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------

def make_guard(x: int, y: int) -> Enemy:
    from dungeoneer.items.weapon import make_combat_knife
    enemy = Enemy(
        x, y,
        name=t("entity.guard.name"),
        render_colour=settings.COL_GUARD,
        max_hp=12, attack=3, defence=1,
        is_drone=False,
        aim_skill=2.5,   # ~5% miss at d=1, ~23% miss at d=8
        loot_table=[
            (0.25, "ammo_9mm"),
            (0.20, "combat_knife"),
            (0.15, "stim_pack"),
            (0.05, "energy_sword"),
        ],
    )
    enemy.equipped_weapon = make_combat_knife()
    return enemy

def make_drone(x: int, y: int) -> Enemy:
    from dungeoneer.items.weapon import make_pistol
    enemy = Enemy(
        x, y,
        name=t("entity.drone.name"),
        render_colour=settings.COL_DRONE,
        max_hp=8, attack=2, defence=0,
        is_drone=True,
        aim_skill=4.5,   # <1% miss at d=1, ~7% miss at d=8 (precision ranged unit)
        loot_table=[
            (0.30, "ammo_9mm"),
            (0.30, "stim_pack"),
            (0.10, "medkit"),
        ],
    )
    enemy.equipped_weapon = make_pistol()
    return enemy
