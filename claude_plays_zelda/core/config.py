"""Configuration management for the AI agent."""

from typing import Optional
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger


class Config(BaseSettings):
    """Main configuration for claude-plays-zelda."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    twitch_access_token: Optional[str] = Field(None, description="Twitch access token")
    twitch_channel: Optional[str] = Field(None, description="Twitch channel name")

    # Claude Model Settings
    claude_model: str = Field("claude-3-5-sonnet-20240620", description="Claude model to use")
    max_tokens: int = Field(4096, description="Maximum tokens for Claude responses")

    # Emulator Settings
    emulator_path: Optional[str] = Field(None, description="Path to SNES emulator")
    rom_path: Optional[str] = Field(None, description="Path to Zelda ROM")
    window_title: str = Field("Snes9x", description="Emulator window title")

    # Game Loop Settings
    action_delay: float = Field(0.5, description="Delay between actions (seconds)")
    decision_interval: float = Field(2.0, description="Seconds between AI decisions")
    frame_rate: int = Field(10, description="Screen capture frame rate")

    # Vision Settings
    enable_ocr: bool = Field(True, description="Enable OCR for text reading")
    enable_object_detection: bool = Field(True, description="Enable object detection")
    screenshot_dir: Path = Field(Path("data/screenshots"), description="Screenshot directory")

    # Memory and Learning
    memory_file: Path = Field(Path("data/saves/agent_memory.json"), description="Agent memory file")
    save_state_dir: Path = Field(Path("data/saves"), description="Save state directory")
    auto_save_interval: int = Field(300, description="Auto-save interval (seconds)")

    # Streaming Settings
    enable_streaming: bool = Field(False, description="Enable Twitch streaming")
    enable_web_dashboard: bool = Field(True, description="Enable web dashboard")
    dashboard_port: int = Field(5000, description="Web dashboard port")

    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_file: Path = Field(Path("data/logs/zelda_ai.log"), description="Log file path")

    # Performance
    max_decisions_per_session: int = Field(1000, description="Max decisions per session")
    timeout_per_action: int = Field(30, description="Timeout per action (seconds)")

    def __init__(self, **kwargs):
        """Initialize config and create necessary directories."""
        super().__init__(**kwargs)
        self._create_directories()

    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        dirs = [
            self.screenshot_dir,
            self.save_state_dir,
            self.memory_file.parent,
            self.log_file.parent,
        ]

        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from a file.

        Args:
            config_path: Path to config file

        Returns:
            Config instance
        """
        import json

        with open(config_path, "r") as f:
            config_data = json.load(f)

        return cls(**config_data)

    def save_to_file(self, config_path: str):
        """
        Save configuration to a file.

        Args:
            config_path: Path to save config file
        """
        import json

        config_dict = self.model_dump()

        # Convert Path objects to strings
        for key, value in config_dict.items():
            if isinstance(value, Path):
                config_dict[key] = str(value)

        with open(config_path, "w") as f:
            json.dump(config_dict, f, indent=2)

        logger.info(f"Configuration saved to {config_path}")
