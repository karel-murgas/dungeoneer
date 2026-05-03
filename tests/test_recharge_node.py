"""Tests for Step 4: recharge node entity, generation, and action."""
from __future__ import annotations

import math
import pytest

from dungeoneer.core import settings
from dungeoneer.entities.recharge_node import RechargeNode
from dungeoneer.entities.player import Player
from dungeoneer.core.difficulty import NORMAL
from dungeoneer.combat.action import RechargeAction
from dungeoneer.combat.action_resolver import ActionResolver
from dungeoneer.world.dungeon_generator import DungeonGenerator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_player(energy: int = 100) -> Player:
    p = Player(5, 5, NORMAL)
    p.energy = energy
    return p


def make_resolver() -> ActionResolver:
    return ActionResolver()


# ---------------------------------------------------------------------------
# Generation tests
# ---------------------------------------------------------------------------

class TestRechargeNodeGeneration:
    def test_generation_places_nodes_in_range(self):
        """Each generated floor has RECHARGE_NODES_PER_FLOOR nodes."""
        min_n, max_n = settings.RECHARGE_NODES_PER_FLOOR
        for seed in range(20):
            gen = DungeonGenerator(seed=seed)
            result = gen.generate(50, 50)
            node_spawns = [s for s in result.spawns if s.kind == "recharge_node"]
            assert min_n <= len(node_spawns) <= max_n, (
                f"seed={seed}: expected {min_n}–{max_n} nodes, got {len(node_spawns)}"
            )

    def test_nodes_placed_on_wall_tiles(self):
        """Recharge nodes are embedded in wall tiles."""
        from dungeoneer.world.tile import TileType
        for seed in range(10):
            gen = DungeonGenerator(seed=seed)
            result = gen.generate(50, 50)
            for spawn in result.spawns:
                if spawn.kind != "recharge_node":
                    continue
                tile = result.dungeon_map.get_type(spawn.x, spawn.y)
                assert tile == TileType.WALL, (
                    f"seed={seed}: node at ({spawn.x},{spawn.y}) is on {tile}, expected WALL"
                )


# ---------------------------------------------------------------------------
# RechargeAction tests
# ---------------------------------------------------------------------------

class TestRechargeAction:
    def _make_floor_stub(self):
        """Minimal floor stub with dungeon_map that always passes validation."""
        class MapStub:
            def in_bounds(self, x, y): return True
        class FloorStub:
            dungeon_map = MapStub()
        return FloorStub()

    def test_full_recharge_adds_energy_marks_used(self):
        player = make_player(energy=80)
        node = RechargeNode(5, 6)  # adjacent to player at (5,5)
        resolver = make_resolver()
        floor = self._make_floor_stub()

        action = RechargeAction(node, amount_ep=50)
        assert action.validate(player, floor)

        result = resolver.resolve_recharge(player, action, floor)

        assert result.success
        assert player.energy == min(130, settings.ENERGY_MAX)  # capped at 100
        assert node.used is True

    def test_actual_added_capped_at_energy_max(self):
        player = make_player(energy=80)
        node = RechargeNode(5, 6)
        resolver = make_resolver()
        floor = self._make_floor_stub()

        result = resolver.resolve_recharge(player, RechargeAction(node, 50), floor)

        assert result.success
        assert player.energy == settings.ENERGY_MAX  # 80 + 50 > 100 → capped

    def test_heat_applied_on_requested_amount(self):
        """Heat is based on requested EP, not actual gained — incentive to choose right amount."""
        from unittest.mock import MagicMock
        player = make_player(energy=95)  # only 5 EP missing
        node = RechargeNode(5, 6)
        resolver = make_resolver()
        floor = self._make_floor_stub()
        heat_system = MagicMock()

        resolver.resolve_recharge(player, RechargeAction(node, 50), floor, heat_system)

        expected_heat = int(math.ceil(50 * settings.RECHARGE_HEAT_PER_EP))
        heat_system.add_heat.assert_called_once_with(expected_heat)

    def test_used_node_fails_validate(self):
        player = make_player(energy=50)
        node = RechargeNode(5, 6, used=True)
        floor = self._make_floor_stub()

        action = RechargeAction(node, 25)
        assert not action.validate(player, floor)

    def test_out_of_range_fails_validate(self):
        player = make_player(energy=50)
        node = RechargeNode(10, 10)  # far away
        floor = self._make_floor_stub()

        action = RechargeAction(node, 25)
        assert not action.validate(player, floor)

    def test_zero_actual_ep_options_computed_correctly(self):
        """When player is full, overlay helper should report 0 actual EP."""
        import importlib
        import sys
        # Import the helper without needing a running pygame display
        import pygame
        pygame.display.init()
        try:
            pygame.display.set_mode((1, 1), pygame.NOFRAME)
            from dungeoneer.rendering.ui.recharge_overlay import _compute_options
            player = make_player(energy=settings.ENERGY_MAX)
            node = RechargeNode(0, 0)
            opts = _compute_options(node, player)
            assert all(o["disabled"] for o in opts), "All options should be disabled when full"
            assert all(o["ep_actual"] == 0 for o in opts)
        finally:
            pygame.display.quit()
