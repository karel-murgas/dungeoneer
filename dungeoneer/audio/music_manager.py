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

# Blend goes 0.0 (full calm) → 1.0 (full action).
_MUSIC_VOLUME        = 0.30   # max volume for music (kept below SFX level)
_FADE_TO_ACTION      = 1.5    # seconds for calm → action crossfade (ongoing combat)
_FADE_TO_ACTION_FAST = 0.15   # seconds for instant-alert fade (banner trigger)
_FADE_TO_CALM        = 3.0    # seconds for action → calm crossfade

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "music")


class MusicManager:
    """Crossfading background music controller.

    Call ``start()`` when the game scene opens, ``stop()`` when it exits.
    Call ``to_action()`` on enemy alert, ``to_calm()`` when combat ends.
    Call ``pause()``/``resume()`` when another scene temporarily overlays this one.
    Call ``update(dt)`` every frame.
    """

    def __init__(self) -> None:
        # Reserve channels 0 and 1 exclusively for music so SFX never
        # steal them.  pygame.mixer.set_reserved reserves the *first N*
        # channels, so we claim 2.
        pygame.mixer.set_reserved(2)
        self._ch_calm   = pygame.mixer.Channel(0)
        self._ch_action = pygame.mixer.Channel(1)

        calm_path   = os.path.join(_ASSETS_DIR, "calm.mp3")
        action_path = os.path.join(_ASSETS_DIR, "action.mp3")
        self._calm_snd   = pygame.mixer.Sound(calm_path)
        self._action_snd = pygame.mixer.Sound(action_path)

        # Current and target blend value
        self._blend        = 0.0   # 0 = calm, 1 = action
        self._target_blend = 0.0
        self._fade_rate    = 0.0   # blend units per second
        self._running      = False

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
        self._running = False

    def pause(self) -> None:
        """Temporarily silence both channels (e.g. while HackScene is active)."""
        if not self._running:
            return
        self._ch_calm.pause()
        self._ch_action.pause()

    def resume(self) -> None:
        """Unpause both channels after a temporary overlay scene."""
        if not self._running:
            return
        self._ch_calm.unpause()
        self._ch_action.unpause()

    def to_action(self, *, fast: bool = False) -> None:
        """Start crossfading toward the action track (enemy alert).

        ``fast=True`` uses a short 0.15 s fade — call this when the alert
        banner triggers so the music kicks in as soon as the "!" appears.
        A fast fade in progress is never slowed down by a subsequent call
        without ``fast``.
        """
        if not self._running:
            return
        new_rate = 1.0 / (_FADE_TO_ACTION_FAST if fast else _FADE_TO_ACTION)
        self._target_blend = 1.0
        # Never slow down a fade that is already heading to action faster.
        if new_rate > self._fade_rate:
            self._fade_rate = new_rate

    def to_calm(self) -> None:
        """Start crossfading back to the calm track (combat over)."""
        if not self._running:
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

    def _apply_volumes(self) -> None:
        """Equal-power crossfade: cos/sin curve keeps perceived loudness constant."""
        angle = self._blend * math.pi / 2.0
        self._ch_calm.set_volume(_MUSIC_VOLUME * math.cos(angle))
        self._ch_action.set_volume(_MUSIC_VOLUME * math.sin(angle))
