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
        import yaml

        path = Path(config_path)
        with open(path, "r") as f:
            if path.suffix in ['.yaml', '.yml']:
                config_data = yaml.safe_load(f)
                # Flatten nested config if needed, or adjust Config model to match yaml structure
                # The current config.yaml has nested keys (emulator: ...), but Config model is flat.
                # We need to flatten it or update Config model.
                # For now, let's assume we flatten it or map it.
                
                # Actually, looking at config.yaml, it has sections: claude, emulator, etc.
                # But Config class has flat fields: emulator_path, rom_path.
                # We need to map the yaml structure to the flat Config fields.
                
                flat_config = {}
                if 'claude' in config_data:
                    flat_config['anthropic_api_key'] = config_data['claude'].get('api_key')
                    flat_config['claude_model'] = config_data['claude'].get('model')
                    flat_config['max_tokens'] = config_data['claude'].get('max_tokens')
                
                if 'emulator' in config_data:
                    flat_config['emulator_path'] = config_data['emulator'].get('executable_path')
                    flat_config['rom_path'] = config_data['emulator'].get('rom_path')
                    flat_config['window_title'] = config_data['emulator'].get('window_name')
                
                if 'cv' in config_data:
                    flat_config['enable_ocr'] = True # Assumed if cv section exists
                    flat_config['enable_object_detection'] = True
                
                # Merge with any other top level keys
                for k, v in config_data.items():
                    if k not in ['claude', 'emulator', 'cv', 'agent', 'game', 'streaming', 'logging']:
                        flat_config[k] = v
                        
                # Filter out None values to let defaults/env vars take precedence
                config_data = {k: v for k, v in flat_config.items() if v is not None}
                
            else:
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
