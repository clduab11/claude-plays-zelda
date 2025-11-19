"""Unit tests for action planner."""

import pytest
from unittest.mock import Mock
from src.agent.action_planner import ActionPlanner, ActionType, Action


class TestActionPlanner:
    """Tests for ActionPlanner class."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_controller = Mock()
        self.planner = ActionPlanner(self.mock_controller)

    def test_parse_action_move_up(self):
        """Test parsing move up action."""
        action = self.planner.parse_action("move_up")
        assert action is not None
        assert action.action_type == ActionType.MOVE_UP

    def test_parse_action_attack(self):
        """Test parsing attack action."""
        action = self.planner.parse_action("attack")
        assert action is not None
        assert action.action_type == ActionType.ATTACK

    def test_parse_action_unknown(self):
        """Test parsing unknown action defaults to wait."""
        action = self.planner.parse_action("unknown_action")
        assert action is not None
        assert action.action_type == ActionType.WAIT

    def test_create_combat_sequence(self):
        """Test creating a combat sequence."""
        sequence = self.planner.create_combat_sequence("up")
        assert len(sequence) > 0
        assert any(a.action_type == ActionType.ATTACK for a in sequence)

    def test_create_exploration_sequence(self):
        """Test creating an exploration sequence."""
        sequence = self.planner.create_exploration_sequence("right", distance=3)
        assert len(sequence) > 0
        # Should have movement and wait actions
        assert any(a.action_type == ActionType.MOVE_RIGHT for a in sequence)
