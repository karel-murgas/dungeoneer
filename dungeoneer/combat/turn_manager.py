"""Turn manager — controls the turn order and drives AI execution."""
from __future__ import annotations

import logging

from dungeoneer.entities.player import Player

log = logging.getLogger(__name__)

_MAX_RECURSION_DEPTH = 64   # safety guard — more than this is a bug


class TurnManager:
    def __init__(self) -> None:
        self._queue: list = []
        self._index: int  = 0
        self.round: int   = 0
        self._depth: int  = 0   # recursion depth guard

    def build_queue(self, floor: "Floor") -> None:  # type: ignore[name-defined]
        """Rebuild queue: player first, then all living enemies."""
        self._queue = [a for a in floor.actors if a.alive]
        self._queue.sort(key=lambda a: 0 if isinstance(a, Player) else 1)
        self._index = 0
        log.debug(
            "build_queue  round=%d  actors=[%s]",
            self.round,
            ", ".join(a.name for a in self._queue),
        )

    def current_actor(self) -> "Actor | None":  # type: ignore[name-defined]
        while self._index < len(self._queue):
            actor = self._queue[self._index]
            if actor.alive:
                return actor
            log.debug("Skipping dead actor %s at index %d", actor.name, self._index)
            self._index += 1
        return None

    def is_player_turn(self) -> bool:
        result = isinstance(self.current_actor(), Player)
        return result

    def advance(
        self,
        floor: "Floor",                 # type: ignore[name-defined]
        resolver: "ActionResolver",     # type: ignore[name-defined]
    ) -> None:
        """Move to the next actor; if it's an AI actor, run its turn immediately."""
        self._depth += 1
        if self._depth > _MAX_RECURSION_DEPTH:
            log.error(
                "advance() recursion depth %d exceeded limit! "
                "index=%d queue_len=%d queue=[%s]",
                self._depth,
                self._index,
                len(self._queue),
                ", ".join(f"{a.name}(alive={a.alive})" for a in self._queue),
            )
            self._depth -= 1
            return

        self._index += 1
        log.debug(
            "advance  depth=%d  index→%d  queue_len=%d",
            self._depth, self._index, len(self._queue),
        )

        # If we've gone through everyone, start new round
        if self._index >= len(self._queue):
            from dungeoneer.core.event_bus import bus, TurnEndEvent
            self.round += 1
            log.debug("End of round %d — rebuilding queue", self.round)
            bus.post(TurnEndEvent(self.round))
            self.build_queue(floor)
            self._depth -= 1
            return

        actor = self.current_actor()
        if actor is None:
            # current_actor() skipped dead actors past the end of the queue.
            # Treat this as end-of-round and rebuild.
            from dungeoneer.core.event_bus import bus, TurnEndEvent
            self.round += 1
            log.debug(
                "current_actor() exhausted queue (index=%d len=%d) — "
                "ending round %d and rebuilding",
                self._index, len(self._queue), self.round,
            )
            bus.post(TurnEndEvent(self.round))
            self.build_queue(floor)
            self._depth -= 1
            return

        log.debug("advance → actor=%s (Player=%s)", actor.name, isinstance(actor, Player))

        if not isinstance(actor, Player):
            from dungeoneer.combat.action import MeleeAttackAction, RangedAttackAction
            actions_per_turn   = getattr(actor, 'actions_per_turn',   1)
            max_attacks        = getattr(actor, 'max_attacks_per_turn', 1)
            attacks_used       = 0

            for _step in range(actions_per_turn):
                try:
                    action = actor.ai_brain.take_turn(floor)
                except Exception:
                    log.exception("AI brain error for %s — skipping turn", actor.name)
                    action = None

                if action is None:
                    log.debug("AI returned None action for %s", actor.name)
                    break

                is_attack = isinstance(action, (MeleeAttackAction, RangedAttackAction))
                if is_attack and attacks_used >= max_attacks:
                    log.debug("Max attacks reached for %s — stopping multi-action", actor.name)
                    break

                valid = action.validate(actor, floor)
                log.debug(
                    "AI action %s for %s  valid=%s  step=%d",
                    type(action).__name__, actor.name, valid, _step,
                )
                if valid:
                    try:
                        result = action.execute(actor, floor, resolver)
                    except Exception:
                        log.exception(
                            "Action %s execution error for %s",
                            type(action).__name__, actor.name,
                        )
                        result = None

                    if result and result.message:
                        from dungeoneer.core.event_bus import bus, LogMessageEvent, EnemyBurstQueueEvent
                        bus.post(LogMessageEvent(result.message, result.msg_colour))
                        if result.burst_events:
                            bus.post(EnemyBurstQueueEvent(result.burst_events))

                if is_attack:
                    attacks_used += 1
                    if attacks_used >= max_attacks:
                        break

        self._depth -= 1
