"""OBS WebSocket controller for stream automation."""

import json
from typing import Dict, Any, Optional
from loguru import logger

try:
    import obsws_python as obs
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    logger.warning("obsws-python not installed, OBS control disabled")


class OBSController:
    """Controls OBS Studio via WebSocket for stream automation."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 4455,
        password: Optional[str] = None,
    ):
        """
        Initialize OBS controller.

        Args:
            host: OBS WebSocket host
            port: OBS WebSocket port
            password: OBS WebSocket password
        """
        self.host = host
        self.port = port
        self.password = password
        self.client = None
        self.is_connected = False

        # Scene and source names
        self.scenes = {
            "main": "Zelda Gameplay",
            "starting": "Starting Soon",
            "ending": "Stream Ending",
            "brb": "Be Right Back",
        }

        self.sources = {
            "game_capture": "Game Capture",
            "ai_overlay": "AI Thought Overlay",
            "stats_overlay": "Stats Overlay",
            "webcam": "Webcam",
        }

        logger.info(f"OBSController initialized (host={host}, port={port})")

    def connect(self) -> bool:
        """
        Connect to OBS WebSocket.

        Returns:
            True if connection successful
        """
        if not OBS_AVAILABLE:
            logger.error("OBS WebSocket library not available")
            return False

        try:
            self.client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password,
            )
            self.is_connected = True
            logger.info("Connected to OBS WebSocket")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Disconnect from OBS WebSocket."""
        if self.client:
            try:
                self.client = None
                self.is_connected = False
                logger.info("Disconnected from OBS")
            except Exception as e:
                logger.error(f"Error disconnecting from OBS: {e}")

    def start_streaming(self) -> bool:
        """
        Start OBS streaming.

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            self.client.start_stream()
            logger.info("OBS streaming started")
            return True
        except Exception as e:
            logger.error(f"Failed to start streaming: {e}")
            return False

    def stop_streaming(self) -> bool:
        """
        Stop OBS streaming.

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            self.client.stop_stream()
            logger.info("OBS streaming stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop streaming: {e}")
            return False

    def start_recording(self) -> bool:
        """
        Start OBS recording.

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            self.client.start_record()
            logger.info("OBS recording started")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            return False

    def stop_recording(self) -> bool:
        """
        Stop OBS recording.

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            self.client.stop_record()
            logger.info("OBS recording stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            return False

    def set_scene(self, scene_name: str) -> bool:
        """
        Switch to a scene.

        Args:
            scene_name: Name of scene to switch to

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            self.client.set_current_program_scene(scene_name)
            logger.debug(f"Switched to scene: {scene_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set scene: {e}")
            return False

    def update_overlay(self, stats: Dict[str, Any]):
        """
        Update the stats overlay with current game state.

        Args:
            stats: Current game statistics
        """
        if not self.is_connected:
            return

        try:
            # Format overlay text
            hearts = stats.get("hearts", {})
            current_hearts = hearts.get("current_hearts", 0) if isinstance(hearts, dict) else stats.get("hearts", 0)
            max_hearts = hearts.get("max_hearts", 0) if isinstance(hearts, dict) else 0
            rupees = stats.get("rupees", 0)

            overlay_text = (
                f"❤️ {current_hearts}/{max_hearts}  "
                f"💎 {rupees}"
            )

            # Update text source (if configured)
            self._update_text_source("stats_text", overlay_text)

        except Exception as e:
            logger.error(f"Failed to update overlay: {e}")

    def update_decision_overlay(self, decision: Dict[str, Any]):
        """
        Update the AI decision overlay.

        Args:
            decision: Current AI decision
        """
        if not self.is_connected:
            return

        try:
            action = decision.get("action", "thinking")
            reasoning = decision.get("reasoning", "")[:150]

            overlay_text = f"🤖 Action: {action}\n💭 {reasoning}"

            self._update_text_source("ai_thought_text", overlay_text)

        except Exception as e:
            logger.error(f"Failed to update decision overlay: {e}")

    def _update_text_source(self, source_name: str, text: str):
        """
        Update a text source in OBS.

        Args:
            source_name: Name of the text source
            text: New text content
        """
        if not self.is_connected:
            return

        try:
            settings = {"text": text}
            self.client.set_input_settings(source_name, settings, True)
        except Exception as e:
            logger.debug(f"Could not update text source {source_name}: {e}")

    def show_source(self, source_name: str, scene_name: Optional[str] = None):
        """
        Show a source in a scene.

        Args:
            source_name: Name of source to show
            scene_name: Scene name (None = current scene)
        """
        if not self.is_connected:
            return

        try:
            scene = scene_name or self._get_current_scene()
            self.client.set_scene_item_enabled(
                scene,
                self._get_scene_item_id(scene, source_name),
                True
            )
        except Exception as e:
            logger.error(f"Failed to show source: {e}")

    def hide_source(self, source_name: str, scene_name: Optional[str] = None):
        """
        Hide a source in a scene.

        Args:
            source_name: Name of source to hide
            scene_name: Scene name (None = current scene)
        """
        if not self.is_connected:
            return

        try:
            scene = scene_name or self._get_current_scene()
            self.client.set_scene_item_enabled(
                scene,
                self._get_scene_item_id(scene, source_name),
                False
            )
        except Exception as e:
            logger.error(f"Failed to hide source: {e}")

    def _get_current_scene(self) -> str:
        """Get current program scene name."""
        try:
            return self.client.get_current_program_scene().current_program_scene_name
        except Exception:
            return ""

    def _get_scene_item_id(self, scene_name: str, source_name: str) -> int:
        """Get scene item ID for a source."""
        try:
            return self.client.get_scene_item_id(scene_name, source_name).scene_item_id
        except Exception:
            return -1

    def get_stream_status(self) -> Dict[str, Any]:
        """
        Get current stream status.

        Returns:
            Stream status dictionary
        """
        if not self.is_connected:
            return {"connected": False}

        try:
            status = self.client.get_stream_status()
            return {
                "connected": True,
                "streaming": status.output_active,
                "duration": status.output_duration if status.output_active else 0,
                "bytes": status.output_bytes if status.output_active else 0,
            }
        except Exception as e:
            logger.error(f"Failed to get stream status: {e}")
            return {"connected": True, "error": str(e)}

    def take_screenshot(self, source_name: str, file_path: str) -> bool:
        """
        Take a screenshot of a source.

        Args:
            source_name: Name of source to capture
            file_path: Path to save screenshot

        Returns:
            True if successful
        """
        if not self.is_connected:
            return False

        try:
            self.client.save_source_screenshot(
                source_name,
                "png",
                file_path,
                1920,
                1080,
                100
            )
            logger.debug(f"Screenshot saved: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False
