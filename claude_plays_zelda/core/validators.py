"""Configuration validators for enhanced validation."""

import os
from pathlib import Path
from typing import Any, Optional, List, Dict
from loguru import logger


class ConfigValidators:
    """Collection of configuration validators."""

    @staticmethod
    def validate_api_key(key: str, key_name: str = "API key") -> str:
        """
        Validate API key format.

        Args:
            key: API key to validate
            key_name: Name of the key for error messages

        Returns:
            Validated key

        Raises:
            ValueError: If key is invalid
        """
        if not key or not isinstance(key, str):
            raise ValueError(f"{key_name} must be a non-empty string")

        if len(key) < 10:
            raise ValueError(f"{key_name} appears too short (minimum 10 characters)")

        # Check for common placeholders
        placeholders = [
            "your_key_here",
            "YOUR_KEY",
            "REPLACE_ME",
            "TODO",
            "changeme",
        ]
        if any(placeholder.lower() in key.lower() for placeholder in placeholders):
            raise ValueError(
                f"{key_name} appears to be a placeholder value. " "Please set a valid API key."
            )

        logger.debug(f"{key_name} validated successfully")
        return key

    @staticmethod
    def validate_path(
        path: Any,
        must_exist: bool = False,
        must_be_file: bool = False,
        must_be_dir: bool = False,
        create_if_missing: bool = False,
    ) -> Path:
        """
        Validate and normalize path.

        Args:
            path: Path to validate
            must_exist: Whether path must already exist
            must_be_file: Whether path must be a file
            must_be_dir: Whether path must be a directory
            create_if_missing: Create directory if it doesn't exist

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is invalid
        """
        if not path:
            raise ValueError("Path cannot be empty")

        path = Path(path)

        # Check existence requirements
        if must_exist and not path.exists():
            raise ValueError(f"Path does not exist: {path}")

        if path.exists():
            if must_be_file and not path.is_file():
                raise ValueError(f"Path must be a file: {path}")
            if must_be_dir and not path.is_dir():
                raise ValueError(f"Path must be a directory: {path}")

        # Create directory if requested
        if create_if_missing and must_be_dir and not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")

        return path

    @staticmethod
    def validate_port(port: int) -> int:
        """
        Validate network port number.

        Args:
            port: Port number to validate

        Returns:
            Validated port

        Raises:
            ValueError: If port is invalid
        """
        if not isinstance(port, int):
            raise ValueError("Port must be an integer")

        if port < 1 or port > 65535:
            raise ValueError(f"Port must be between 1 and 65535, got {port}")

        # Warn about privileged ports
        if port < 1024:
            logger.warning(
                f"Port {port} is a privileged port and may require " "elevated permissions"
            )

        return port

    @staticmethod
    def validate_positive_number(
        value: float,
        name: str = "value",
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> float:
        """
        Validate positive number with optional bounds.

        Args:
            value: Value to validate
            name: Name for error messages
            min_value: Optional minimum value (exclusive)
            max_value: Optional maximum value (exclusive)

        Returns:
            Validated value

        Raises:
            ValueError: If value is invalid
        """
        if not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a number")

        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")

        if min_value is not None and value <= min_value:
            raise ValueError(f"{name} must be greater than {min_value}, got {value}")

        if max_value is not None and value >= max_value:
            raise ValueError(f"{name} must be less than {max_value}, got {value}")

        return value

    @staticmethod
    def validate_model_name(model: str, valid_models: List[str]) -> str:
        """
        Validate Claude model name.

        Args:
            model: Model name to validate
            valid_models: List of valid model names

        Returns:
            Validated model name

        Raises:
            ValueError: If model is invalid
        """
        if not model or not isinstance(model, str):
            raise ValueError("Model name must be a non-empty string")

        if model not in valid_models:
            raise ValueError(f"Invalid model '{model}'. Valid models: {', '.join(valid_models)}")

        return model

    @staticmethod
    def validate_log_level(level: str) -> str:
        """
        Validate logging level.

        Args:
            level: Log level to validate

        Returns:
            Validated log level

        Raises:
            ValueError: If level is invalid
        """
        valid_levels = ["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]

        level = level.upper()
        if level not in valid_levels:
            raise ValueError(
                f"Invalid log level '{level}'. " f"Valid levels: {', '.join(valid_levels)}"
            )

        return level

    @staticmethod
    def validate_interval(
        interval: float,
        name: str = "interval",
        min_seconds: float = 0.01,
        max_seconds: float = 3600.0,
    ) -> float:
        """
        Validate time interval.

        Args:
            interval: Interval in seconds
            name: Name for error messages
            min_seconds: Minimum allowed interval
            max_seconds: Maximum allowed interval

        Returns:
            Validated interval

        Raises:
            ValueError: If interval is invalid
        """
        if not isinstance(interval, (int, float)):
            raise ValueError(f"{name} must be a number")

        if interval < min_seconds:
            raise ValueError(f"{name} must be at least {min_seconds} seconds, got {interval}")

        if interval > max_seconds:
            raise ValueError(f"{name} must be at most {max_seconds} seconds, got {interval}")

        return interval

    @staticmethod
    def validate_environment_var(
        var_name: str,
        required: bool = True,
        default: Optional[str] = None,
    ) -> Optional[str]:
        """
        Validate and retrieve environment variable.

        Args:
            var_name: Environment variable name
            required: Whether variable is required
            default: Default value if not set

        Returns:
            Variable value or default

        Raises:
            ValueError: If required variable is missing
        """
        value = os.environ.get(var_name)

        if value is None:
            if required and default is None:
                raise ValueError(f"Required environment variable '{var_name}' is not set")
            return default

        if not value.strip():
            if required:
                raise ValueError(f"Environment variable '{var_name}' is empty")
            return default

        return value

    @staticmethod
    def validate_emulator_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate emulator configuration.

        Args:
            config: Emulator configuration dictionary

        Returns:
            Validated configuration

        Raises:
            ValueError: If configuration is invalid
        """
        required_fields = ["type", "rom_path"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Emulator config missing required field: {field}")

        # Validate emulator type
        valid_types = ["fceux", "snes9x", "retroarch"]
        if config["type"] not in valid_types:
            logger.warning(
                f"Unknown emulator type '{config['type']}'. "
                f"Supported types: {', '.join(valid_types)}"
            )

        # Validate ROM path if it should exist
        rom_path = Path(config["rom_path"])
        if not rom_path.exists():
            logger.warning(
                f"ROM file not found at: {rom_path}. "
                "Please ensure the ROM file exists before starting."
            )

        # Validate FPS if present
        if "fps" in config:
            fps = config["fps"]
            if not isinstance(fps, int) or fps < 1 or fps > 240:
                raise ValueError(f"Invalid FPS value: {fps}. Must be between 1 and 240.")

        return config

    @staticmethod
    def validate_vision_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate computer vision configuration.

        Args:
            config: Vision configuration dictionary

        Returns:
            Validated configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate confidence thresholds
        if "ocr" in config and "confidence_threshold" in config["ocr"]:
            threshold = config["ocr"]["confidence_threshold"]
            if not 0 <= threshold <= 100:
                raise ValueError(f"OCR confidence threshold must be 0-100, got {threshold}")

        if "object_detection" in config:
            obj_config = config["object_detection"]
            for key in ["confidence_threshold", "nms_threshold"]:
                if key in obj_config:
                    value = obj_config[key]
                    if not 0 <= value <= 1:
                        raise ValueError(f"Object detection {key} must be 0-1, got {value}")

        # Validate screen capture interval
        if "screen_capture" in config and "interval" in config["screen_capture"]:
            interval = config["screen_capture"]["interval"]
            ConfigValidators.validate_interval(
                interval, name="screen capture interval", min_seconds=0.01, max_seconds=10.0
            )

        return config

    @staticmethod
    def validate_ai_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AI agent configuration.

        Args:
            config: AI configuration dictionary

        Returns:
            Validated configuration

        Raises:
            ValueError: If configuration is invalid
        """
        # Validate decision interval
        if "decision_interval" in config:
            ConfigValidators.validate_interval(
                config["decision_interval"],
                name="decision interval",
                min_seconds=0.1,
                max_seconds=60.0,
            )

        # Validate memory settings
        if "memory" in config:
            mem_config = config["memory"]
            if "max_history" in mem_config:
                max_history = mem_config["max_history"]
                if not isinstance(max_history, int) or max_history < 1:
                    raise ValueError(f"max_history must be positive integer, got {max_history}")

        # Validate context settings
        if "context" in config:
            ctx_config = config["context"]
            if "max_tokens" in ctx_config:
                max_tokens = ctx_config["max_tokens"]
                if not isinstance(max_tokens, int) or max_tokens < 1000:
                    raise ValueError(f"max_tokens must be at least 1000, got {max_tokens}")

        return config
