"""Persistence helpers — read/write profiles and global config to disk.

Save directory:
  Windows:  %APPDATA%/Dungeoneer/
  POSIX:    ~/.local/share/Dungeoneer/

Override for tests: set ``meta.storage._SAVE_DIR_OVERRIDE`` to a Path before
importing anything that calls ``get_save_dir()``.
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from dungeoneer.meta.global_config import GlobalConfig
from dungeoneer.meta.profile import Profile

log = logging.getLogger(__name__)

# Tests monkeypatch this to a tmp_path directory.
_SAVE_DIR_OVERRIDE: Optional[Path] = None

_NAME_RE = re.compile(r"[A-Za-z0-9 _\-]+")
_MAX_NAME_LEN = 24


# ---------------------------------------------------------------------------
# Directory helpers
# ---------------------------------------------------------------------------

def get_save_dir() -> Path:
    """Return (and create) the OS-appropriate Dungeoneer save directory."""
    if _SAVE_DIR_OVERRIDE is not None:
        base = _SAVE_DIR_OVERRIDE
    elif os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home())) / "Dungeoneer"
    else:
        base = Path.home() / ".local" / "share" / "Dungeoneer"

    base.mkdir(parents=True, exist_ok=True)
    (base / "profiles").mkdir(exist_ok=True)
    return base


def _profiles_dir() -> Path:
    return get_save_dir() / "profiles"


def _profile_path(name: str) -> Path:
    return _profiles_dir() / f"{sanitize_name(name)}.json"


def _global_path() -> Path:
    return get_save_dir() / "global.json"


# ---------------------------------------------------------------------------
# Name sanitization
# ---------------------------------------------------------------------------

def sanitize_name(raw: str) -> str:
    """Strip, whitelist [A-Za-z0-9 _-], trim to 24 chars.

    Raises ValueError if result is empty (blank-only or all-illegal input).
    """
    stripped = raw.strip()
    kept = "".join(ch for ch in stripped if _NAME_RE.fullmatch(ch))
    trimmed = kept[:_MAX_NAME_LEN].strip()
    if not trimmed:
        raise ValueError(f"Profile name {raw!r} is invalid after sanitization")
    return trimmed


# ---------------------------------------------------------------------------
# Profile CRUD
# ---------------------------------------------------------------------------

def list_profiles() -> list[str]:
    """Return display names of all saved profiles, sorted by updated_at desc."""
    results: list[tuple[str, str]] = []
    for path in _profiles_dir().glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            name = data.get("name", path.stem)
            updated = data.get("updated_at", "")
            results.append((name, updated))
        except Exception:
            log.warning("Skipping corrupt profile file: %s", path)
    results.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in results]


def profile_exists(name: str) -> bool:
    """Return True if a profile file exists for the given display name."""
    try:
        return _profile_path(name).exists()
    except ValueError:
        return False


def load_profile(name: str) -> Optional[Profile]:
    """Load and return a Profile, or None if file is missing or corrupt."""
    try:
        path = _profile_path(name)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Profile.from_dict(data)
    except Exception:
        log.exception("Failed to read profile %r", name)
        return None


def save_profile(profile: Profile) -> None:
    """Atomic write: update updated_at, write to tmpfile, rename into place."""
    profile.updated_at = datetime.now(timezone.utc).isoformat()
    path = _profile_path(profile.name)
    try:
        data = json.dumps(profile.to_dict(), ensure_ascii=False, indent=2)
        _atomic_write(path, data)
    except Exception:
        log.exception("Failed to save profile %r", profile.name)
        raise


def delete_profile(name: str) -> bool:
    """Delete a profile file.  Returns True if deleted, False if not found."""
    try:
        path = _profile_path(name)
        if path.exists():
            path.unlink()
            return True
        return False
    except Exception:
        log.exception("Failed to delete profile %r", name)
        return False


# ---------------------------------------------------------------------------
# Global config
# ---------------------------------------------------------------------------

def load_global() -> GlobalConfig:
    """Load GlobalConfig from disk; returns defaults if file is missing."""
    path = _global_path()
    try:
        if not path.exists():
            return GlobalConfig()
        data = json.loads(path.read_text(encoding="utf-8"))
        return GlobalConfig.from_dict(data)
    except Exception:
        log.exception("Failed to read global config")
        return GlobalConfig()


def save_global(cfg: GlobalConfig) -> None:
    """Write GlobalConfig to disk atomically."""
    path = _global_path()
    try:
        data = json.dumps(cfg.to_dict(), ensure_ascii=False, indent=2)
        _atomic_write(path, data)
    except Exception:
        log.exception("Failed to save global config")
        raise


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _atomic_write(path: Path, text: str) -> None:
    """Write text to path via a sibling tmpfile + rename (atomic on POSIX,
    best-effort on Windows where rename overwrites atomically since Python 3.3)."""
    dir_ = path.parent
    fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        Path(tmp).replace(path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
