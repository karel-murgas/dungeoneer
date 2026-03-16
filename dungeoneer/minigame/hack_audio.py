"""Procedural audio for the hacking minigame.

All sounds are synthesised from numpy waveforms — no audio files required.
Follows the same pattern as dungeoneer.audio.audio_manager.
"""
from __future__ import annotations

import numpy as np
import pygame

_SR = 44100  # sample rate


class HackAudio:
    """Self-contained audio for HackScene.  Call build() once after mixer init."""

    def __init__(self) -> None:
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._built = False

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build(self) -> None:
        """Build all sounds.  Safe to call multiple times (no-op after first)."""
        if self._built:
            return
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=_SR, size=-16, channels=2, buffer=512)
        self._sounds = {
            "move":          self._to_sound(self._gen_move()),
            "hack_start":    self._to_sound(self._gen_hack_start()),
            "hack_complete": self._to_sound(self._gen_hack_complete()),
            "ice":           self._to_sound(self._gen_ice()),
            "timer_tick":    self._to_sound(self._gen_timer_tick()),
            "success":       self._to_sound(self._gen_success()),
            "fail":          self._to_sound(self._gen_fail()),
            "bonus_time":    self._to_sound(self._gen_bonus_time()),
        }
        self._built = True

    def play(self, name: str, volume: float = 1.0) -> None:
        sound = self._sounds.get(name)
        if sound:
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()

    # ------------------------------------------------------------------
    # Synthesis helpers (same interface as AudioManager)
    # ------------------------------------------------------------------

    def _noise(self, ms: int, vol: float = 1.0, exp: float = 1.0) -> np.ndarray:
        n = int(_SR * ms / 1000)
        t = np.linspace(0.0, 1.0, n, dtype=np.float32)
        envelope = (1.0 - t) ** exp
        rng = np.random.default_rng(seed=42)
        noise = rng.uniform(-1.0, 1.0, n).astype(np.float32)
        return (noise * envelope * vol * 32767).astype(np.int16)

    def _tone(
        self,
        freq_start: float,
        ms: int,
        vol: float = 1.0,
        freq_end: float | None = None,
        waveform: str = "sine",
        exp: float = 1.0,
    ) -> np.ndarray:
        n = int(_SR * ms / 1000)
        t = np.linspace(0.0, ms / 1000, n, dtype=np.float32)
        if freq_end is not None:
            freq  = np.linspace(freq_start, freq_end, n, dtype=np.float32)
            phase = np.cumsum(2.0 * np.pi * freq / _SR)
        else:
            phase = 2.0 * np.pi * freq_start * t
        if waveform == "square":
            wave = np.sign(np.sin(phase)).astype(np.float32)
        else:
            wave = np.sin(phase).astype(np.float32)
        envelope = np.linspace(1.0, 0.0, n, dtype=np.float32) ** exp
        return (wave * envelope * vol * 32767).astype(np.int16)

    def _mix(self, *arrays: np.ndarray) -> np.ndarray:
        length = max(len(a) for a in arrays)
        result = np.zeros(length, dtype=np.float32)
        for a in arrays:
            result[: len(a)] += a.astype(np.float32)
        peak = np.max(np.abs(result))
        if peak > 32767:
            result = result * (32767 / peak)
        return result.astype(np.int16)

    def _concat(self, *arrays: np.ndarray) -> np.ndarray:
        return np.concatenate(arrays).astype(np.int16)

    def _silence(self, ms: int) -> np.ndarray:
        return np.zeros(int(_SR * ms / 1000), dtype=np.int16)

    def _to_sound(self, mono: np.ndarray) -> pygame.mixer.Sound:
        stereo = np.column_stack([mono, mono])
        return pygame.sndarray.make_sound(stereo)

    # ------------------------------------------------------------------
    # Individual generators
    # ------------------------------------------------------------------

    def _gen_move(self) -> np.ndarray:
        """Short soft click — moving between nodes."""
        click = self._noise(18, vol=0.28, exp=2.5)
        tick  = self._tone(1800, 18, vol=0.18, freq_end=900, exp=2.0)
        return self._mix(click, tick)

    def _gen_hack_start(self) -> np.ndarray:
        """Subtle electronic hum when arriving at a loot node."""
        hum = self._tone(440, 80, vol=0.30, freq_end=660, exp=1.2)
        buzz = self._tone(880, 40, vol=0.12, waveform="square", exp=2.0)
        return self._mix(hum, self._concat(self._silence(40), buzz))

    def _gen_hack_complete(self) -> np.ndarray:
        """Two-note ascending chime — loot extracted."""
        lo = self._tone(523, 80, vol=0.55, exp=1.5)   # C5
        hi = self._tone(783, 120, vol=0.65, exp=1.2)  # G5
        return self._concat(lo, hi)

    def _gen_ice(self) -> np.ndarray:
        """Harsh descending alert — ICE node triggered."""
        alarm = self._tone(1200, 60, vol=0.70, freq_end=300, waveform="square", exp=0.8)
        burst = self._noise(40, vol=0.50, exp=1.5)
        return self._mix(alarm, self._concat(self._silence(20), burst))

    def _gen_timer_tick(self) -> np.ndarray:
        """Short sharp tick — played repeatedly when timer is low."""
        tick = self._tone(2000, 22, vol=0.45, freq_end=1400, exp=1.8)
        return tick

    def _gen_success(self) -> np.ndarray:
        """Clean three-note ascending arpeggio — hack complete / exit."""
        a = self._tone(523, 70,  vol=0.55, exp=1.5)   # C5
        b = self._tone(659, 70,  vol=0.60, exp=1.5)   # E5
        c = self._tone(783, 130, vol=0.65, exp=1.2)   # G5
        shimmer = self._tone(1046, 200, vol=0.20, exp=2.5)  # C6 tail
        return self._mix(
            self._concat(a, b, c),
            self._concat(self._silence(210), shimmer),
        )

    def _gen_fail(self) -> np.ndarray:
        """Descending alarm — time expired / security breach."""
        sweep = self._tone(900, 180, vol=0.70, freq_end=160, waveform="square", exp=0.6)
        rumble = self._noise(200, vol=0.35, exp=0.8)
        return self._mix(sweep, rumble)

    def _gen_bonus_time(self) -> np.ndarray:
        """Quick rising double-tone — bonus time collected."""
        a = self._tone(660, 55, vol=0.50, exp=1.8)   # E5
        b = self._tone(880, 90, vol=0.55, exp=1.4)   # A5
        return self._concat(a, b)
