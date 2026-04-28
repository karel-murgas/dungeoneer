"""Profile, LifetimeStats, GameplayFlags dataclasses + JSON serialization."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class LifetimeStats:
    kills_total: int = 0
    kills_by_enemy: dict[str, int] = field(default_factory=dict)
    kills_by_weapon: dict[str, int] = field(default_factory=dict)
    deaths_total: int = 0
    deaths_by_killer: dict[str, int] = field(default_factory=dict)
    hp_healed: int = 0
    bullets_shot: int = 0
    crits_ranged: int = 0
    crits_melee: int = 0
    containers_hacked: int = 0
    nodes_hacked: int = 0
    containers_fully_hacked: int = 0
    containers_failed: int = 0
    runs_won: int = 0
    credits_lifetime: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "kills_total": self.kills_total,
            "kills_by_enemy": dict(self.kills_by_enemy),
            "kills_by_weapon": dict(self.kills_by_weapon),
            "deaths_total": self.deaths_total,
            "deaths_by_killer": dict(self.deaths_by_killer),
            "hp_healed": self.hp_healed,
            "bullets_shot": self.bullets_shot,
            "crits_ranged": self.crits_ranged,
            "crits_melee": self.crits_melee,
            "containers_hacked": self.containers_hacked,
            "nodes_hacked": self.nodes_hacked,
            "containers_fully_hacked": self.containers_fully_hacked,
            "containers_failed": self.containers_failed,
            "runs_won": self.runs_won,
            "credits_lifetime": self.credits_lifetime,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "LifetimeStats":
        return cls(
            kills_total=d.get("kills_total", 0),
            kills_by_enemy=d.get("kills_by_enemy", {}),
            kills_by_weapon=d.get("kills_by_weapon", {}),
            deaths_total=d.get("deaths_total", 0),
            deaths_by_killer=d.get("deaths_by_killer", {}),
            hp_healed=d.get("hp_healed", 0),
            bullets_shot=d.get("bullets_shot", 0),
            crits_ranged=d.get("crits_ranged", 0),
            crits_melee=d.get("crits_melee", 0),
            containers_hacked=d.get("containers_hacked", 0),
            nodes_hacked=d.get("nodes_hacked", 0),
            containers_fully_hacked=d.get("containers_fully_hacked", 0),
            containers_failed=d.get("containers_failed", 0),
            runs_won=d.get("runs_won", 0),
            credits_lifetime=d.get("credits_lifetime", 0),
        )


@dataclass
class GameplayFlags:
    use_minigame: bool = True
    use_aim_minigame: bool = True
    use_heal_minigame: bool = True
    use_melee_minigame: bool = True
    heal_threshold_pct: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "use_minigame": self.use_minigame,
            "use_aim_minigame": self.use_aim_minigame,
            "use_heal_minigame": self.use_heal_minigame,
            "use_melee_minigame": self.use_melee_minigame,
            "heal_threshold_pct": self.heal_threshold_pct,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GameplayFlags":
        return cls(
            use_minigame=d.get("use_minigame", True),
            use_aim_minigame=d.get("use_aim_minigame", True),
            use_heal_minigame=d.get("use_heal_minigame", True),
            use_melee_minigame=d.get("use_melee_minigame", True),
            heal_threshold_pct=d.get("heal_threshold_pct", 100),
        )


@dataclass
class Profile:
    name: str
    language: str = "en"
    difficulty: str = "normal"
    tutorial_enabled: bool = False
    tutorial_seen: list[str] = field(default_factory=list)
    credits: int = 0
    flags: GameplayFlags = field(default_factory=GameplayFlags)
    stats: LifetimeStats = field(default_factory=LifetimeStats)
    perks: dict = field(default_factory=dict)
    skills: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: _now_iso())
    updated_at: str = field(default_factory=lambda: _now_iso())

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "difficulty": self.difficulty,
            "tutorial_enabled": self.tutorial_enabled,
            "tutorial_seen": list(self.tutorial_seen),
            "credits": self.credits,
            "flags": self.flags.to_dict(),
            "stats": self.stats.to_dict(),
            "perks": dict(self.perks),
            "skills": dict(self.skills),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Profile":
        return cls(
            name=d["name"],
            language=d.get("language", "en"),
            difficulty=d.get("difficulty", "normal"),
            tutorial_enabled=d.get("tutorial_enabled", False),
            tutorial_seen=d.get("tutorial_seen", []),
            credits=d.get("credits", 0),
            flags=GameplayFlags.from_dict(d.get("flags", {})),
            stats=LifetimeStats.from_dict(d.get("stats", {})),
            perks=d.get("perks", {}),
            skills=d.get("skills", {}),
            created_at=d.get("created_at", _now_iso()),
            updated_at=d.get("updated_at", _now_iso()),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
