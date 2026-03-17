"""AudioManager — procedurally generated sound effects.

All sounds are built from numpy waveforms at startup.
No audio files required.
"""
from __future__ import annotations

import numpy as np
import pygame

from dungeoneer.core import settings
from dungeoneer.core.event_bus import (
    bus, DamageEvent, DeathEvent, MoveEvent, StairEvent
)
from dungeoneer.entities.player import Player

_SR = 44100   # sample rate


class AudioManager:
    def __init__(self) -> None:
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=_SR, size=-16, channels=2, buffer=512)

        rng = np.random.default_rng(seed=0)
        self._rng = rng
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._build_sounds()
        self._pending_sounds: list = []  # [(time_remaining, name, volume)]

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def attach(self) -> None:
        """Subscribe to game events."""
        bus.subscribe(DamageEvent, self._on_damage)
        bus.subscribe(DeathEvent,  self._on_death)
        bus.subscribe(MoveEvent,   self._on_move)
        bus.subscribe(StairEvent,  self._on_stair)

    def detach(self) -> None:
        """Unsubscribe from game events."""
        bus.unsubscribe(DamageEvent, self._on_damage)
        bus.unsubscribe(DeathEvent,  self._on_death)
        bus.unsubscribe(MoveEvent,   self._on_move)
        bus.unsubscribe(StairEvent,  self._on_stair)

    def play(self, name: str, volume: float = 1.0) -> None:
        sound = self._sounds.get(name)
        if sound:
            actual = max(0.0, min(1.0, volume * settings.SFX_VOLUME * settings.MASTER_VOLUME))
            sound.set_volume(actual)
            sound.play()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_damage(self, event: DamageEvent) -> None:
        if isinstance(event.attacker, Player):
            if event.is_ranged:
                weapon = getattr(event.attacker, "equipped_weapon", None)
                weapon_id = getattr(weapon, "id", "") if weapon else ""
                sound = "smg_shot" if weapon_id == "smg" else "pistol_shot"
                self.play(sound)
            else:
                self.play("melee_hit")
        else:
            # Enemy attack sound
            self.play("drone_shot" if event.is_ranged else "melee_hit", 0.55)
        # Impact sound on the target side
        self.play("hit_taken", 0.35)

    def _on_death(self, event: DeathEvent) -> None:
        if isinstance(event.entity, Player):
            self.play("player_death")
        else:
            self.play("enemy_death")

    def _on_move(self, event: MoveEvent) -> None:
        self.play("footstep", 0.14)

    def _on_stair(self, event: StairEvent) -> None:
        self.play("stair", 0.6)

    # ------------------------------------------------------------------
    # Sound construction helpers
    # ------------------------------------------------------------------

    def _noise(self, ms: int, vol: float = 1.0, exp: float = 1.0) -> np.ndarray:
        """White noise with exponential decay envelope. Returns mono int16."""
        n = int(_SR * ms / 1000)
        t = np.linspace(0.0, 1.0, n, dtype=np.float32)
        envelope = (1.0 - t) ** exp
        noise = self._rng.uniform(-1.0, 1.0, n).astype(np.float32)
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
        """Sine/square wave with optional pitch sweep. Returns mono int16."""
        n = int(_SR * ms / 1000)
        t = np.linspace(0.0, ms / 1000, n, dtype=np.float32)

        if freq_end is not None:
            freq = np.linspace(freq_start, freq_end, n, dtype=np.float32)
            phase = np.cumsum(2.0 * np.pi * freq / _SR)
        else:
            phase = 2.0 * np.pi * freq_start * t

        if waveform == "square":
            wave = np.sign(np.sin(phase)).astype(np.float32)
        else:
            wave = np.sin(phase).astype(np.float32)

        envelope = np.linspace(1.0, 0.0, n, dtype=np.float32) ** exp
        return (wave * envelope * vol * 32767).astype(np.int16)

    def _mix(self, *mono_arrays: np.ndarray) -> np.ndarray:
        """Mix mono arrays of different lengths; normalise if clipping."""
        length = max(len(a) for a in mono_arrays)
        result = np.zeros(length, dtype=np.float32)
        for a in mono_arrays:
            result[: len(a)] += a.astype(np.float32)
        peak = np.max(np.abs(result))
        if peak > 32767:
            result = result * (32767 / peak)
        return result.astype(np.int16)

    def _silence(self, ms: int) -> np.ndarray:
        return np.zeros(int(_SR * ms / 1000), dtype=np.int16)

    def _concat(self, *mono_arrays: np.ndarray) -> np.ndarray:
        return np.concatenate(mono_arrays).astype(np.int16)

    def _to_sound(self, mono: np.ndarray) -> pygame.mixer.Sound:
        stereo = np.column_stack([mono, mono])
        return pygame.sndarray.make_sound(stereo)

    # ------------------------------------------------------------------
    # Individual sound builders
    # ------------------------------------------------------------------

    def _build_sounds(self) -> None:
        self._sounds = {
            "footstep":    self._to_sound(self._gen_footstep()),
            "melee_hit":   self._to_sound(self._gen_melee_hit()),
            "pistol_shot": self._to_sound(self._gen_pistol_shot()),
            "smg_shot":    self._to_sound(self._gen_smg_shot()),
            "drone_shot":  self._to_sound(self._gen_drone_shot()),
            "hit_taken":   self._to_sound(self._gen_hit_taken()),
            "enemy_death": self._to_sound(self._gen_enemy_death()),
            "player_death":self._to_sound(self._gen_player_death()),
            "stair":       self._to_sound(self._gen_stair()),
            "reload":      self._to_sound(self._gen_reload()),
            "no_ammo":     self._to_sound(self._gen_no_ammo()),
            "heal":        self._to_sound(self._gen_heal()),
            "victory":     self._to_sound(self._gen_victory()),
            "defeat":      self._to_sound(self._gen_defeat()),
        }

    def _gen_footstep(self) -> np.ndarray:
        # Very short (35 ms) low-passed noise thud.
        # Low-pass by smoothing the noise array with a short window.
        raw = self._noise(35, vol=0.45, exp=1.5)
        # Running average → low-pass effect
        window = 12
        kernel = np.ones(window, dtype=np.float32) / window
        smooth = np.convolve(raw.astype(np.float32), kernel, mode="same")
        return smooth.astype(np.int16)

    def _gen_melee_hit(self) -> np.ndarray:
        # Sharp noise burst (70 ms) + low thud underneath
        burst = self._noise(70, vol=0.75, exp=2.0)
        thud  = self._tone(90, 70, vol=0.4, exp=1.5)
        return self._mix(burst, thud)

    def _gen_pistol_shot(self) -> np.ndarray:
        # Gunshot: very sharp initial bang + decaying tail
        bang  = self._noise(18, vol=0.95, exp=0.6)   # loud fast peak
        tail  = self._noise(130, vol=0.35, exp=1.8)  # softer tail
        # Layer: bang at start, tail runs longer
        return self._mix(
            self._concat(bang, self._silence(1)),
            self._concat(self._silence(5), tail),
        )

    def _gen_smg_shot(self) -> np.ndarray:
        # Shorter, snappier than pistol — faster decay, higher pitch crack
        bang = self._noise(10, vol=0.85, exp=0.5)   # sharp crack
        tail = self._noise(60, vol=0.25, exp=2.5)   # quick fade
        return self._mix(
            self._concat(bang, self._silence(1)),
            self._concat(self._silence(3), tail),
        )

    def _gen_drone_shot(self) -> np.ndarray:
        # Energy weapon: high-to-low pitch sweep ("pew")
        sweep = self._tone(1400, 110, vol=0.7, freq_end=220, exp=1.2)
        click = self._noise(15, vol=0.3, exp=0.8)
        return self._mix(sweep, click)

    def _gen_hit_taken(self) -> np.ndarray:
        # Short descending tone — target flinches
        return self._tone(380, 90, vol=0.55, freq_end=160, exp=1.2)

    def _gen_enemy_death(self) -> np.ndarray:
        # Noise burst + descending crunch
        crunch = self._noise(140, vol=0.7, exp=1.5)
        fall   = self._tone(250, 180, vol=0.45, freq_end=60, exp=0.8)
        return self._mix(crunch, fall)

    def _gen_player_death(self) -> np.ndarray:
        # Low ominous rumble + slow fade
        rumble = self._tone(55, 500, vol=0.8, freq_end=30, exp=0.5)
        noise  = self._noise(400, vol=0.3, exp=0.7)
        return self._mix(rumble, noise)

    def _gen_stair(self) -> np.ndarray:
        # Ascending two-note arpeggio (satisfying level-clear cue)
        note1 = self._tone(440, 120, vol=0.55, exp=1.5)
        gap   = self._silence(30)
        note2 = self._tone(660, 150, vol=0.60, exp=1.5)
        return self._concat(note1, gap, note2)

    def _gen_reload(self) -> np.ndarray:
        # Phase 1 — magazine insertion: mid-range clack
        ins_noise = self._noise(50, vol=0.65, exp=1.4)
        ins_tone  = self._tone(420, 50, vol=0.40, freq_end=300, exp=1.5)
        insert    = self._mix(ins_noise, ins_tone)

        gap = self._silence(70)

        # Phase 2 — slide/bolt snap forward: sharp metallic crack
        snap_noise = self._noise(22, vol=0.75, exp=0.7)
        snap_tone  = self._tone(1100, 22, vol=0.35, waveform="square", exp=2.5)
        snap       = self._mix(snap_noise, snap_tone)

        return self._concat(insert, gap, snap)

    def _gen_no_ammo(self) -> np.ndarray:
        # Dry low click — empty chamber
        return self._tone(220, 30, vol=0.45, waveform="square", exp=1.0)

    def _gen_victory(self) -> np.ndarray:
        # Triumphant 4-note ascending arpeggio + shimmer tail
        n1 = self._tone(330, 110, vol=0.55, exp=1.8)   # E4
        n2 = self._tone(440, 110, vol=0.60, exp=1.8)   # A4
        n3 = self._tone(550, 130, vol=0.65, exp=1.6)   # C#5
        n4 = self._tone(660, 260, vol=0.70, exp=1.2)   # E5  (longer sustain)
        shimmer = self._tone(880, 220, vol=0.30, freq_end=1100, exp=1.4)
        tail = self._mix(n4, self._concat(self._silence(40), shimmer))
        return self._concat(
            n1, self._silence(20),
            n2, self._silence(20),
            n3, self._silence(20),
            tail,
        )

    def _gen_defeat(self) -> np.ndarray:
        # Somber descending tone + low rumble — distinct from player_death stab
        thud  = self._noise(60, vol=0.55, exp=1.2)
        fall  = self._tone(220, 500, vol=0.65, freq_end=55, exp=0.7)
        rumble = self._tone(60, 400, vol=0.30, freq_end=35, exp=0.5)
        body  = self._mix(fall, rumble)
        return self._concat(self._mix(thud, body[:len(thud)]), body[len(thud):])

    def _gen_heal(self) -> np.ndarray:
        # Stim injector: short mechanical click → warm ascending shimmer
        click  = self._tone(1100, 18, vol=0.45, waveform="square", exp=1.0)
        gap    = self._silence(20)
        shimmer = self._tone(280, 260, vol=0.55, freq_end=560, exp=1.4)
        return self._concat(self._mix(click, shimmer[:len(click)]), gap, shimmer)
