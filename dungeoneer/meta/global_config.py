"""GlobalConfig dataclass + JSON serialization."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GlobalConfig:
    master_volume: float = 1.0
    music_volume: float = 0.30
    sfx_volume: float = 1.0
    last_active_profile: str | None = None
    last_quick_config: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "master_volume": self.master_volume,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "last_active_profile": self.last_active_profile,
            "last_quick_config": dict(self.last_quick_config),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "GlobalConfig":
        return cls(
            master_volume=d.get("master_volume", 1.0),
            music_volume=d.get("music_volume", 0.30),
            sfx_volume=d.get("sfx_volume", 1.0),
            last_active_profile=d.get("last_active_profile", None),
            last_quick_config=d.get("last_quick_config", {}),
        )
