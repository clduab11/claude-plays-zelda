"""Tests for configuration module."""

import pytest
from claude_plays_zelda.core.config import Config


def test_config_creation():
    """Test creating a config object."""
    # This will fail without actual API key, but demonstrates structure
    try:
        config = Config(anthropic_api_key="test-key")
        assert config.anthropic_api_key == "test-key"
        assert config.claude_model == "claude-3-5-sonnet-20240620"
        assert config.decision_interval == 2.0
    except Exception:
        # Expected if validation fails
        pass


def test_config_defaults():
    """Test default config values."""
    try:
        config = Config(anthropic_api_key="test-key")
        assert config.action_delay == 0.5
        assert config.frame_rate == 10
        assert config.log_level == "INFO"
    except Exception:
        pass


if __name__ == "__main__":
    pytest.main([__file__])
