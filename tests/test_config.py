"""Tests for configuration module."""

import pytest
from claude_plays_zelda.core.config import Config


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    return monkeypatch


def test_config_creation(mock_env):
    """Test creating a config object."""
    config = Config(anthropic_api_key="test-key")
    assert config.anthropic_api_key == "test-key"
    assert config.claude_model == "claude-3-5-sonnet-20240620"
    assert config.decision_interval == 2.0


def test_config_defaults(mock_env):
    """Test default config values."""
    config = Config(anthropic_api_key="test-key")
    assert config.action_delay == 0.5
    assert config.frame_rate == 10
    assert config.log_level == "INFO"


if __name__ == "__main__":
    pytest.main([__file__])
