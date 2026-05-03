"""Perk catalog — single source of truth for all perk definitions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PerkType(Enum):
    ACTIVE = "active"
    PASSIVE = "passive"


class BodyPart(Enum):
    BRAIN = "brain"
    EYES = "eyes"
    HANDS = "hands"
    BODY = "body"
    LEGS = "legs"


@dataclass(frozen=True)
class PerkDef:
    id: str
    name_key: str
    desc_key: str
    type: PerkType
    body: BodyPart
    ep_cost: int | None          # EP per activation (ACTIVE only, None for PASSIVE)
    ep_per_turn: int | None      # EP drained per turn (toggle perks like cloak)
    prices: tuple[int, ...]      # credit cost per level; len == max_level
    max_level: int
    deferred: bool               # not yet implementable — shown greyed in shop
    target_required: bool        # activation needs a tile/entity target pick


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------

CATALOG: dict[str, PerkDef] = {p.id: p for p in [
    # ---- ACTIVE perks ----
    PerkDef(
        id="scanner",
        name_key="perk.scanner.name",
        desc_key="perk.scanner.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.EYES,
        ep_cost=8,
        ep_per_turn=None,
        prices=(600,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="reflex_fibres",
        name_key="perk.reflex_fibres.name",
        desc_key="perk.reflex_fibres.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.LEGS,
        ep_cost=8,
        ep_per_turn=None,
        prices=(700,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="cloak",
        name_key="perk.cloak.name",
        desc_key="perk.cloak.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.BODY,
        ep_cost=None,
        ep_per_turn=2,
        prices=(800,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="recoil_comp",
        name_key="perk.recoil_comp.name",
        desc_key="perk.recoil_comp.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.HANDS,
        ep_cost=10,
        ep_per_turn=None,
        prices=(700, 1800),
        max_level=2,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="nanobots",
        name_key="perk.nanobots.name",
        desc_key="perk.nanobots.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.BODY,
        ep_cost=15,
        ep_per_turn=None,
        prices=(800,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="neural_protection",
        name_key="perk.neural_protection.name",
        desc_key="perk.neural_protection.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.BRAIN,
        ep_cost=15,
        ep_per_turn=None,
        prices=(500, 1500),
        max_level=2,
        deferred=True,
        target_required=False,
    ),
    PerkDef(
        id="trap",
        name_key="perk.trap.name",
        desc_key="perk.trap.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.LEGS,
        ep_cost=12,
        ep_per_turn=None,
        prices=(600,),
        max_level=1,
        deferred=True,
        target_required=True,
    ),
    PerkDef(
        id="surge_contacts",
        name_key="perk.surge_contacts.name",
        desc_key="perk.surge_contacts.desc",
        type=PerkType.ACTIVE,
        body=BodyPart.HANDS,
        ep_cost=20,
        ep_per_turn=None,
        prices=(700,),
        max_level=1,
        deferred=True,
        target_required=True,
    ),

    # ---- PASSIVE perks ----
    PerkDef(
        id="smartlink",
        name_key="perk.smartlink.name",
        desc_key="perk.smartlink.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.EYES,
        ep_cost=None,
        ep_per_turn=None,
        prices=(350,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="muscle_implants",
        name_key="perk.muscle_implants.name",
        desc_key="perk.muscle_implants.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.HANDS,
        ep_cost=None,
        ep_per_turn=None,
        prices=(350,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="skeleton",
        name_key="perk.skeleton.name",
        desc_key="perk.skeleton.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.BODY,
        ep_cost=None,
        ep_per_turn=None,
        prices=(400,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="lenses",
        name_key="perk.lenses.name",
        desc_key="perk.lenses.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.EYES,
        ep_cost=None,
        ep_per_turn=None,
        prices=(500,),
        max_level=1,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="protocol_smg",
        name_key="perk.protocol_smg.name",
        desc_key="perk.protocol_smg.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.BRAIN,
        ep_cost=None,
        ep_per_turn=None,
        prices=(500, 1500, 3000),
        max_level=3,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="protocol_shotgun",
        name_key="perk.protocol_shotgun.name",
        desc_key="perk.protocol_shotgun.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.BRAIN,
        ep_cost=None,
        ep_per_turn=None,
        prices=(500, 1500, 3000),
        max_level=3,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="protocol_rifle",
        name_key="perk.protocol_rifle.name",
        desc_key="perk.protocol_rifle.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.BRAIN,
        ep_cost=None,
        ep_per_turn=None,
        prices=(500, 1500, 3000),
        max_level=3,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="protocol_sword",
        name_key="perk.protocol_sword.name",
        desc_key="perk.protocol_sword.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.BRAIN,
        ep_cost=None,
        ep_per_turn=None,
        prices=(500, 1500, 3000),
        max_level=3,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="network_scan",
        name_key="perk.network_scan.name",
        desc_key="perk.network_scan.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.BRAIN,
        ep_cost=None,
        ep_per_turn=None,
        prices=(700, 1000, 1500),
        max_level=3,
        deferred=False,
        target_required=False,
    ),
    PerkDef(
        id="mech_arm",
        name_key="perk.mech_arm.name",
        desc_key="perk.mech_arm.desc",
        type=PerkType.PASSIVE,
        body=BodyPart.HANDS,
        ep_cost=None,
        ep_per_turn=None,
        prices=(800,),
        max_level=1,
        deferred=True,
        target_required=False,
    ),
]}


def get_perk(perk_id: str) -> PerkDef:
    """Return PerkDef by id; raises KeyError for unknown ids."""
    return CATALOG[perk_id]


def desc_for_level(perk_id: str, level: int) -> str:
    """Return the localised description for *perk_id* at *level*.

    Tries ``perk.{id}.desc.{level}`` first; falls back to ``perk.{id}.desc``.
    """
    from dungeoneer.core.i18n import t
    leveled_key = f"perk.{perk_id}.desc.{level}"
    result = t(leveled_key)
    return result if result != leveled_key else t(f"perk.{perk_id}.desc")
