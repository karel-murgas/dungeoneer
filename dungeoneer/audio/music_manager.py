"""MusicManager — crossfading background music for explore / combat states.

Uses two reserved mixer channels so both tracks play simultaneously and
volume can be blended smoothly.  Channel 0 = calm, Channel 1 = action.

Equal-power crossfade (cos/sin curve) maintains constant perceived loudness
throughout the blend — a linear ramp would cause a dip in the middle.
"""
from __future__ import annotations

import math
import os

import pygame

from dungeoneer.core import settings

# Blend goes 0.0 (full calm) → 1.0 (full action).
_FADE_TO_ACTION      = 1.5    # seconds for calm → action crossfade (ongoing combat)
_FADE_TO_ACTION_FAST = 0.15   # seconds for instant-alert fade (banner trigger)
_FADE_TO_CALM        = 3.0    # seconds for action → calm crossfade
_FADE_TO_VAULT_MS    = 1200   # ms crossfade into vault music (calm/action fade out, vault fades in)

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "music")


class MusicManager:
    """Crossfading background music controller.

    Call ``start()`` when the game scene opens, ``stop()`` when it exits.
    Call ``to_action()`` on enemy alert, ``to_calm()`` when combat ends.
    Call ``pause()``/``resume()`` when another scene temporarily overlays this one.
    Call ``update(dt)`` every frame.
    """

    def __init__(self) -> None:
        # Ensure enough total channels so SFX never starves.
        # Default is 8; raise to 16 to give 13 free channels for SFX.
        pygame.mixer.set_num_channels(16)
        # Reserve channels 0, 1, and 2 exclusively for music so SFX never
        # steal them.  pygame.mixer.set_reserved reserves the *first N*
        # channels, so we claim 3.
        pygame.mixer.set_reserved(3)
        self._ch_calm   = pygame.mixer.Channel(0)
        self._ch_action = pygame.mixer.Channel(1)
        self._ch_vault  = pygame.mixer.Channel(2)

        calm_path   = os.path.join(_ASSETS_DIR, "calm.mp3")
        action_path = os.path.join(_ASSETS_DIR, "action.mp3")
        self._calm_snd   = pygame.mixer.Sound(calm_path)
        self._action_snd = pygame.mixer.Sound(action_path)
        self._vault_snd: pygame.mixer.Sound | None = None  # loaded on first use

        # Current and target blend value
        self._blend        = 0.0   # 0 = calm, 1 = action
        self._target_blend = 0.0
        self._fade_rate    = 0.0   # blend units per second
        self._running      = False
        self._duck_factor  = 1.0   # volume multiplier for ducking (1.0 = normal)
        self._vault_mode   = False  # True once vault music has been started

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin playback from the calm state."""
        if self._running:
            return
        self._blend        = 0.0
        self._target_blend = 0.0
        self._ch_calm.play(self._calm_snd, loops=-1)
        self._ch_action.play(self._action_snd, loops=-1)
        self._apply_volumes()
        self._running = True

    def stop(self) -> None:
        """Stop all music immediately."""
        self._ch_calm.stop()
        self._ch_action.stop()
        self._ch_vault.stop()
        self._running = False
        self._vault_mode = False

    def pause(self) -> None:
        """Temporarily silence all music channels (e.g. while HackScene is active)."""
        if not self._running and not self._vault_mode:
            return
        self._ch_calm.pause()
        self._ch_action.pause()
        self._ch_vault.pause()

    def resume(self) -> None:
        """Unpause all music channels after a temporary overlay scene."""
        if not self._running and not self._vault_mode:
            return
        self._ch_calm.unpause()
        self._ch_action.unpause()
        self._ch_vault.unpause()

    def start_vault(self) -> None:
        """Switch to vault music track (idempotent — safe to call on each re-entry).

        Fades out the calm/action crossfade channels and starts vault.mp3 looping
        on the dedicated channel.  The vault track plays until ``stop()`` is called
        (i.e. until the run ends, whether by death or escape).
        """
        if self._vault_mode:
            return  # already in vault mode — re-entry, do nothing

        self._vault_mode = True
        # Fade out calm/action over _FADE_TO_VAULT_MS
        self._ch_calm.fadeout(_FADE_TO_VAULT_MS)
        self._ch_action.fadeout(_FADE_TO_VAULT_MS)
        self._running = False  # stop the calm↔action crossfade updates

        # Load vault track lazily
        if self._vault_snd is None:
            vault_path = os.path.join(_ASSETS_DIR, "vault.mp3")
            self._vault_snd = pygame.mixer.Sound(vault_path)

        vol = settings.MASTER_VOLUME * settings.MUSIC_VOLUME * self._duck_factor
        self._ch_vault.play(self._vault_snd, loops=-1, fade_ms=_FADE_TO_VAULT_MS)
        self._ch_vault.set_volume(vol)

    def to_action(self, *, fast: bool = False) -> None:
        """Start crossfading toward the action track (enemy alert).

        ``fast=True`` uses a short 0.15 s fade — call this when the alert
        banner triggers so the music kicks in as soon as the "!" appears.
        A fast fade in progress is never slowed down by a subsequent call
        without ``fast``.
        """
        if not self._running or self._vault_mode:
            return
        new_rate = 1.0 / (_FADE_TO_ACTION_FAST if fast else _FADE_TO_ACTION)
        self._target_blend = 1.0
        # Never slow down a fade that is already heading to action faster.
        if new_rate > self._fade_rate:
            self._fade_rate = new_rate

    def to_calm(self) -> None:
        """Start crossfading back to the calm track (combat over)."""
        if not self._running or self._vault_mode:
            return
        self._target_blend = 0.0
        self._fade_rate     = 1.0 / _FADE_TO_CALM

    def update(self, dt: float) -> None:
        """Advance crossfade.  Call once per frame with delta-time in seconds."""
        if not self._running:
            return
        if self._blend == self._target_blend:
            return

        step = self._fade_rate * dt
        if self._target_blend > self._blend:
            self._blend = min(self._blend + step, self._target_blend)
        else:
            self._blend = max(self._blend - step, self._target_blend)

        self._apply_volumes()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def duck(self, factor: float = 0.25) -> None:
        """Lower music volume temporarily (e.g. during a minigame)."""
        self._duck_factor = max(0.0, min(1.0, factor))
        if self._running or self._vault_mode:
            self._apply_volumes()

    def unduck(self) -> None:
        """Restore full music volume after ducking."""
        self._duck_factor = 1.0
        if self._running or self._vault_mode:
            self._apply_volumes()

    def refresh_volume(self) -> None:
        """Re-apply volumes after settings change. Safe to call any time."""
        if self._running or self._vault_mode:
            self._apply_volumes()

    def _apply_volumes(self) -> None:
        """Apply volumes to whichever music channel(s) are active."""
        vol = settings.MASTER_VOLUME * settings.MUSIC_VOLUME * self._duck_factor
        if self._vault_mode:
            self._ch_vault.set_volume(vol)
        else:
            angle = self._blend * math.pi / 2.0
            self._ch_calm.set_volume(vol * math.cos(angle))
            self._ch_action.set_volume(vol * math.sin(angle))
