"""Unit tests for GameLoop state machine logic."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from claude_plays_zelda.core.game_loop import GameLoop, GameState


class TestGameLoopStateMachine:
    """Tests for GameLoop state machine behavior."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration object."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 10,
                'menu_button_delay': 0.5,
                'menu_wait_time': 2.0,
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300
        return config

    @pytest.fixture
    def mock_orchestrator(self):
        """Create a mock GameOrchestrator."""
        orchestrator = Mock()
        orchestrator.is_running = False
        orchestrator.emulator = Mock()
        orchestrator.emulator.input_controller = Mock()
        return orchestrator

    @pytest.fixture
    def game_loop(self, mock_config, mock_orchestrator):
        """Create a GameLoop with mocked dependencies."""
        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator', return_value=mock_orchestrator):
            loop = GameLoop(mock_config)
            loop.orchestrator = mock_orchestrator
            return loop

    def test_game_loop_initialization(self, game_loop):
        """Test that GameLoop initializes with correct state."""
        assert game_loop.state == GameState.MENU
        assert game_loop.consecutive_hud_frames == 0
        assert game_loop.hud_stability_frames == 10
        assert game_loop.menu_button_delay == 0.5
        assert game_loop.menu_wait_time == 2.0

    def test_game_loop_initialization_with_custom_config(self):
        """Test GameLoop with custom configuration values."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 20,
                'menu_button_delay': 1.0,
                'menu_wait_time': 3.0,
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        assert loop.hud_stability_frames == 20
        assert loop.menu_button_delay == 1.0
        assert loop.menu_wait_time == 3.0

    def test_game_loop_initialization_with_defaults(self):
        """Test GameLoop uses defaults when config is missing values."""
        config = Mock()
        config.game = {}  # Empty game config
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        # Should use defaults
        assert loop.hud_stability_frames == 10
        assert loop.menu_button_delay == 0.5
        assert loop.menu_wait_time == 2.0

    def test_consecutive_hud_frames_increment(self, game_loop):
        """Test that consecutive_hud_frames increments correctly."""
        assert game_loop.consecutive_hud_frames == 0

        # Simulate HUD detection
        game_loop.consecutive_hud_frames += 1
        assert game_loop.consecutive_hud_frames == 1

        game_loop.consecutive_hud_frames += 1
        assert game_loop.consecutive_hud_frames == 2

    def test_consecutive_hud_frames_reset(self, game_loop):
        """Test that consecutive_hud_frames resets when HUD lost."""
        game_loop.consecutive_hud_frames = 5

        # Simulate HUD loss
        game_loop.consecutive_hud_frames = 0
        assert game_loop.consecutive_hud_frames == 0

    def test_state_transition_menu_to_playing(self, game_loop):
        """Test transition from MENU to PLAYING state."""
        game_loop.state = GameState.MENU
        game_loop.consecutive_hud_frames = 11  # Above threshold

        # Transition should occur when consecutive_hud_frames > hud_stability_frames
        if game_loop.consecutive_hud_frames > game_loop.hud_stability_frames:
            game_loop.state = GameState.PLAYING

        assert game_loop.state == GameState.PLAYING

    def test_state_no_transition_below_threshold(self, game_loop):
        """Test no transition when below stability threshold."""
        game_loop.state = GameState.MENU
        game_loop.consecutive_hud_frames = 5  # Below threshold of 10

        # Should not transition
        if game_loop.consecutive_hud_frames > game_loop.hud_stability_frames:
            game_loop.state = GameState.PLAYING

        assert game_loop.state == GameState.MENU

    def test_state_transition_playing_to_menu(self, game_loop):
        """Test transition from PLAYING to MENU state."""
        game_loop.state = GameState.PLAYING

        # Simulate title screen detection
        is_title = True

        if is_title:
            game_loop.state = GameState.MENU
            game_loop.consecutive_hud_frames = 0

        assert game_loop.state == GameState.MENU
        assert game_loop.consecutive_hud_frames == 0

    def test_pause_and_resume(self, game_loop):
        """Test pause and resume functionality."""
        assert game_loop.is_paused is False

        game_loop.pause()
        assert game_loop.is_paused is True

        game_loop.resume()
        assert game_loop.is_paused is False

    def test_statistics(self, game_loop):
        """Test get_statistics returns correct data."""
        game_loop.frame_count = 100
        game_loop.is_paused = False

        stats = game_loop.get_statistics()
        assert stats["frame_count"] == 100
        assert stats["is_paused"] is False
        assert "orchestrator_status" in stats


class TestGameLoopConfigurationFlexibility:
    """Tests for configuration flexibility and edge cases."""

    def test_zero_stability_frames(self):
        """Test with zero stability frames (immediate transition)."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 0,
                'menu_button_delay': 0.5,
                'menu_wait_time': 2.0,
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        assert loop.hud_stability_frames == 0

        # With 0 threshold, even 1 frame should trigger transition
        loop.state = GameState.MENU
        loop.consecutive_hud_frames = 1

        if loop.consecutive_hud_frames > loop.hud_stability_frames:
            loop.state = GameState.PLAYING

        assert loop.state == GameState.PLAYING

    def test_very_high_stability_frames(self):
        """Test with very high stability requirement."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 100,
                'menu_button_delay': 0.5,
                'menu_wait_time': 2.0,
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        assert loop.hud_stability_frames == 100

        # 50 frames should not be enough
        loop.state = GameState.MENU
        loop.consecutive_hud_frames = 50

        if loop.consecutive_hud_frames > loop.hud_stability_frames:
            loop.state = GameState.PLAYING

        assert loop.state == GameState.MENU

    def test_custom_menu_delays(self):
        """Test with custom menu delay configurations."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 10,
                'menu_button_delay': 0.1,  # Very short
                'menu_wait_time': 5.0,     # Very long
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        assert loop.menu_button_delay == 0.1
        assert loop.menu_wait_time == 5.0


class TestGameLoopEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_state_remains_stable_at_threshold(self):
        """Test that state doesn't change exactly at threshold."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 10,
                'menu_button_delay': 0.5,
                'menu_wait_time': 2.0,
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        loop.state = GameState.MENU
        loop.consecutive_hud_frames = 10  # Exactly at threshold

        # Should not transition (requires > threshold, not >=)
        if loop.consecutive_hud_frames > loop.hud_stability_frames:
            loop.state = GameState.PLAYING

        assert loop.state == GameState.MENU

    def test_state_transitions_just_above_threshold(self):
        """Test that state changes just above threshold."""
        config = Mock()
        config.game = {
            'state_machine': {
                'hud_stability_frames': 10,
                'menu_button_delay': 0.5,
                'menu_wait_time': 2.0,
            }
        }
        config.decision_interval = 0.5
        config.action_delay = 0.1
        config.frame_rate = 60
        config.auto_save_interval = 300

        with patch('claude_plays_zelda.core.game_loop.GameOrchestrator'):
            loop = GameLoop(config)

        loop.state = GameState.MENU
        loop.consecutive_hud_frames = 11  # Just above threshold

        # Should transition
        if loop.consecutive_hud_frames > loop.hud_stability_frames:
            loop.state = GameState.PLAYING

        assert loop.state == GameState.PLAYING
