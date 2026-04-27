"""StatsTracker — subscribes to game events and accumulates RunStats for one run."""
from __future__ import annotations

from typing import TYPE_CHECKING

from dungeoneer.core.stats import RunStats
from dungeoneer.core.event_bus import (
    bus,
    DeathEvent,
    DamageEvent,
    HealEvent,
    BulletFiredEvent,
    ContainerLootedEvent,
    HackNodesCollectedEvent,
)

if TYPE_CHECKING:
    from dungeoneer.entities.player import Player
    from dungeoneer.entities.enemy import Enemy


class StatsTracker:
    """Owns a RunStats and listens to events for the duration of one run."""

    def __init__(self, player: "Player", credit_baseline: int = 0) -> None:
        self._player = player
        self._credit_baseline = credit_baseline
        self.run = RunStats()
        self._subscribed = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def subscribe(self) -> None:
        if not self._subscribed:
            bus.subscribe(DeathEvent, self._on_death)
            bus.subscribe(DamageEvent, self._on_damage)
            bus.subscribe(HealEvent, self._on_heal)
            bus.subscribe(BulletFiredEvent, self._on_bullet)
            bus.subscribe(ContainerLootedEvent, self._on_container)
            bus.subscribe(HackNodesCollectedEvent, self._on_hack_nodes)
            self._subscribed = True

    def unsubscribe(self) -> None:
        if self._subscribed:
            bus.unsubscribe(DeathEvent, self._on_death)
            bus.unsubscribe(DamageEvent, self._on_damage)
            bus.unsubscribe(HealEvent, self._on_heal)
            bus.unsubscribe(BulletFiredEvent, self._on_bullet)
            bus.unsubscribe(ContainerLootedEvent, self._on_container)
            bus.unsubscribe(HackNodesCollectedEvent, self._on_hack_nodes)
            self._subscribed = False

    def finalize(self) -> RunStats:
        """Freeze the run: compute credits_earned and return the completed RunStats."""
        earned = max(0, self._player.credits - self._credit_baseline)
        self.run.credits_earned = earned
        return self.run

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _on_death(self, event: DeathEvent) -> None:
        from dungeoneer.entities.player import Player
        from dungeoneer.entities.enemy import Enemy

        entity = event.entity
        killer = event.killer
        weapon_id = event.weapon_id

        if isinstance(entity, Player):
            self.run.deaths_total += 1
            if isinstance(killer, Enemy):
                eid = killer.enemy_id
                self.run.deaths_by_killer[eid] = self.run.deaths_by_killer.get(eid, 0) + 1

        elif isinstance(entity, Enemy) and isinstance(killer, Player):
            self.run.kills_total += 1
            eid = entity.enemy_id
            self.run.kills_by_enemy[eid] = self.run.kills_by_enemy.get(eid, 0) + 1
            if weapon_id is not None:
                self.run.kills_by_weapon[weapon_id] = self.run.kills_by_weapon.get(weapon_id, 0) + 1

    def _on_damage(self, event: DamageEvent) -> None:
        from dungeoneer.entities.player import Player
        if isinstance(event.attacker, Player) and event.is_crit:
            self.run.crits_total += 1

    def _on_heal(self, event: HealEvent) -> None:
        from dungeoneer.entities.player import Player
        if isinstance(event.actor, Player):
            self.run.hp_healed += event.amount

    def _on_bullet(self, event: BulletFiredEvent) -> None:
        from dungeoneer.entities.player import Player
        if isinstance(event.shooter, Player):
            self.run.bullets_shot += 1

    def _on_container(self, event: ContainerLootedEvent) -> None:
        if event.was_hacked:
            if event.success:
                self.run.containers_hacked += 1
            else:
                self.run.containers_failed += 1

    def _on_hack_nodes(self, event: HackNodesCollectedEvent) -> None:
        self.run.nodes_hacked += event.nodes_collected
        if event.all_nodes_cleared:
            self.run.containers_fully_hacked += 1
