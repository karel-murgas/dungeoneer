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
        tier: int = 1,
        is_drone: bool = False,
        aim_skill: float = 2.5,
        # --- AI behaviour flags ---
        can_move: bool = True,          # False = immobile (Turret)
        preferred_dist: int = 0,        # 0 = use global DRONE_PREFERRED_DIST; >0 = override
        retreat_when_close: bool = True, # False = never retreats even when player is close (Heavy)
        always_retreat: bool = False,    # True = always retreats if dist < preferred_dist (Sniper)
        actions_per_turn: int = 1,      # extra actions per turn (Dog=2, Turret=2)
        max_attacks_per_turn: int = 1,  # max attacks per turn (Dog=1, Turret=2)
        sprite_key: str = "guard",      # key into procedural_sprites; "drone_animated" = spritesheet
        loot_table: list[tuple[float, str]] | None = None,
        credits_range: tuple[int, int] = (0, 0),
        credits_chance: float = 0.0,
    ) -> None:
        super().__init__(
            x, y, name, render_colour,
            max_hp=max_hp, attack=attack, defence=defence,
        )
        self.tier         = tier
        self.is_drone     = is_drone
        self.aim_skill    = aim_skill  # controls ranged accuracy sigma; higher = more consistent
        self.can_move     = can_move
        self.preferred_dist = preferred_dist
        self.retreat_when_close = retreat_when_close
        self.always_retreat     = always_retreat
        self.actions_per_turn   = actions_per_turn
        self.max_attacks_per_turn = max_attacks_per_turn
        self.sprite_key         = sprite_key
        self.ai_brain     = AIBrain()
        self.ai_brain.attach(self)
        self._credits_range = credits_range
        self._credits_chance = credits_chance
        self.credits_drop = 0  # rolled on death via roll_credits()
        # loot_table: list of (probability, item_id) pairs, evaluated in order
        self._loot_table  = loot_table or []

    def roll_credits(self) -> int:
        """Roll credit drop: chance for a random amount in range."""
        if self._credits_chance > 0 and random.random() < self._credits_chance:
            self.credits_drop = random.randint(*self._credits_range)
        else:
            self.credits_drop = 0
        return self.credits_drop

    def drop_loot(self) -> Optional[Item]:
        """Roll the loot table. Returns an Item instance or None."""
        from dungeoneer.items.weapon import make_shotgun, make_energy_sword
        from dungeoneer.items.consumable import make_stim_pack, make_medkit
        from dungeoneer.items.ammo import make_9mm_ammo

        from dungeoneer.items.ammo import make_rifle_ammo
        _factories = {
            "shotgun":       make_shotgun,
            "energy_sword":  make_energy_sword,
            "stim_pack":     make_stim_pack,
            "medkit":        make_medkit,
            "ammo_9mm":      lambda: make_9mm_ammo(5),
            "ammo_rifle":    lambda: make_rifle_ammo(3),
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
        tier=1,
        is_drone=False,
        aim_skill=2.5,   # ~5% miss at d=1, ~23% miss at d=8
        sprite_key="guard",
        loot_table=[
            (0.25, "ammo_9mm"),
            (0.15, "stim_pack"),
            (0.05, "energy_sword"),
        ],
        credits_range=(3, 10),
        credits_chance=0.50,
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
        tier=1,
        is_drone=True,
        aim_skill=4.5,   # <1% miss at d=1, ~7% miss at d=8 (precision ranged unit)
        sprite_key="drone_animated",
        loot_table=[
            (0.30, "ammo_9mm"),
            (0.30, "stim_pack"),
            (0.10, "medkit"),
        ],
        credits_range=(8, 18),
        credits_chance=0.50,
    )
    enemy.equipped_weapon = make_pistol()
    return enemy

def make_dog(x: int, y: int) -> Enemy:
    """Tier 1 — fast melee, 2 moves per turn but only 1 attack."""
    from dungeoneer.items.weapon import make_k9_bite
    enemy = Enemy(
        x, y,
        name=t("entity.dog.name"),
        render_colour=settings.COL_DOG,
        max_hp=6, attack=1, defence=0,
        tier=1,
        is_drone=False,
        aim_skill=2.5,
        actions_per_turn=2,
        max_attacks_per_turn=1,
        sprite_key="dog",
        loot_table=[
            (0.15, "stim_pack"),
        ],
        credits_range=(2, 8),
        credits_chance=0.30,
    )
    enemy.equipped_weapon = make_k9_bite()
    return enemy

def make_heavy(x: int, y: int) -> Enemy:
    """Tier 2 — armoured ranged, approaches to medium range before shooting."""
    from dungeoneer.items.weapon import make_pistol
    enemy = Enemy(
        x, y,
        name=t("entity.heavy.name"),
        render_colour=settings.COL_HEAVY,
        max_hp=15, attack=3, defence=3,
        tier=2,
        is_drone=True,
        aim_skill=1.5,   # low accuracy — compensated by high defence
        preferred_dist=4,
        retreat_when_close=False,  # never retreats
        sprite_key="heavy",
        loot_table=[
            (0.30, "ammo_9mm"),
            (0.10, "medkit"),
        ],
        credits_range=(10, 20),
        credits_chance=0.60,
    )
    enemy.equipped_weapon = make_pistol()
    return enemy

def make_turret(x: int, y: int) -> Enemy:
    """Tier 2 — immobile, fires twice per turn; returns to Idle when LOS lost."""
    from dungeoneer.items.weapon import make_pistol
    enemy = Enemy(
        x, y,
        name=t("entity.turret.name"),
        render_colour=settings.COL_TURRET,
        max_hp=12, attack=2, defence=1,
        tier=2,
        is_drone=True,
        aim_skill=3.0,   # medium accuracy
        can_move=False,
        actions_per_turn=1,
        max_attacks_per_turn=1,
        sprite_key="turret",
        loot_table=[
            (0.50, "ammo_9mm"),
        ],
        credits_range=(5, 12),
        credits_chance=0.40,
    )
    gun = make_pistol()
    gun.shots = 2  # double-tap with visual stagger so player can react
    enemy.equipped_weapon = gun
    return enemy

def make_sniper_drone(x: int, y: int) -> Enemy:
    """Tier 3 — long-range rifle, always retreats to keep max distance."""
    from dungeoneer.items.weapon import make_rifle
    enemy = Enemy(
        x, y,
        name=t("entity.sniper_drone.name"),
        render_colour=settings.COL_SNIPER,
        max_hp=6, attack=3, defence=0,
        tier=3,
        is_drone=True,
        aim_skill=6.0,   # very high accuracy
        preferred_dist=7,
        always_retreat=True,
        sprite_key="sniper_drone",
        loot_table=[
            (0.40, "ammo_rifle"),
            (0.10, "medkit"),
        ],
        credits_range=(12, 25),
        credits_chance=0.60,
    )
    enemy.equipped_weapon = make_rifle()
    return enemy

def make_riot_guard(x: int, y: int) -> Enemy:
    """Tier 3 — heavily armoured melee; forces player to use ranged weapons."""
    from dungeoneer.items.weapon import make_combat_knife
    enemy = Enemy(
        x, y,
        name=t("entity.riot_guard.name"),
        render_colour=settings.COL_RIOT_GUARD,
        max_hp=16, attack=4, defence=4,
        tier=3,
        is_drone=False,
        aim_skill=2.5,
        sprite_key="riot_guard",
        loot_table=[
            (0.20, "medkit"),
            (0.20, "ammo_9mm"),
        ],
        credits_range=(15, 30),
        credits_chance=0.70,
    )
    enemy.equipped_weapon = make_combat_knife()
    return enemy
