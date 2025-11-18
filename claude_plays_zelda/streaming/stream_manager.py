"""Stream manager for coordinating streaming components."""

import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger

from claude_plays_zelda.streaming.twitch_bot import TwitchBot
from claude_plays_zelda.streaming.obs_controller import OBSController
from claude_plays_zelda.streaming.highlight_generator import HighlightGenerator


class StreamManager:
    """Manages all streaming components and coordination."""

    def __init__(
        self,
        twitch_token: Optional[str] = None,
        twitch_channel: Optional[str] = None,
        obs_host: str = "localhost",
        obs_port: int = 4455,
        obs_password: Optional[str] = None,
        highlight_dir: str = "data/highlights",
    ):
        """
        Initialize stream manager.

        Args:
            twitch_token: Twitch OAuth token
            twitch_channel: Twitch channel name
            obs_host: OBS WebSocket host
            obs_port: OBS WebSocket port
            obs_password: OBS WebSocket password
            highlight_dir: Directory for highlight clips
        """
        self.is_streaming = False
        self.start_time: Optional[datetime] = None

        # Initialize components
        self.twitch_bot: Optional[TwitchBot] = None
        if twitch_token and twitch_channel:
            self.twitch_bot = TwitchBot(
                token=twitch_token,
                initial_channels=[twitch_channel],
                stats_callback=self._get_game_stats,
            )

        self.obs_controller = OBSController(
            host=obs_host,
            port=obs_port,
            password=obs_password,
        )

        self.highlight_generator = HighlightGenerator(
            output_dir=highlight_dir,
        )

        # Game state for streaming
        self.current_stats: Dict[str, Any] = {}
        self.current_decision: Dict[str, Any] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()

        # Threading for async bot
        self._bot_thread: Optional[threading.Thread] = None
        self._bot_loop: Optional[asyncio.AbstractEventLoop] = None

        logger.info("StreamManager initialized")

    def start_streaming(self):
        """Start all streaming components."""
        logger.info("Starting streaming components...")

        self.is_streaming = True
        self.start_time = datetime.now()

        # Connect to OBS
        if self.obs_controller.connect():
            logger.info("OBS connected")
            self.obs_controller.start_streaming()
        else:
            logger.warning("OBS connection failed, continuing without OBS")

        # Start Twitch bot in separate thread
        if self.twitch_bot:
            self._start_twitch_bot()

        # Start highlight generator
        self.highlight_generator.start()

        logger.info("Streaming started successfully")

    def stop_streaming(self):
        """Stop all streaming components."""
        logger.info("Stopping streaming components...")

        self.is_streaming = False

        # Stop OBS
        if self.obs_controller.is_connected:
            self.obs_controller.stop_streaming()
            self.obs_controller.disconnect()

        # Stop Twitch bot
        if self.twitch_bot and self._bot_loop:
            self._bot_loop.call_soon_threadsafe(self._bot_loop.stop)

        # Stop highlight generator
        self.highlight_generator.stop()

        logger.info("Streaming stopped")

    def _start_twitch_bot(self):
        """Start Twitch bot in separate thread."""
        def run_bot():
            self._bot_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._bot_loop)
            try:
                self._bot_loop.run_until_complete(self.twitch_bot.run_bot())
            except Exception as e:
                logger.error(f"Twitch bot error: {e}")
            finally:
                self._bot_loop.close()

        self._bot_thread = threading.Thread(target=run_bot, daemon=True)
        self._bot_thread.start()
        logger.info("Twitch bot thread started")

    def update_game_state(self, stats: Dict[str, Any]):
        """
        Update current game state for streaming display.

        Args:
            stats: Current game statistics
        """
        self.current_stats = stats

        if self.twitch_bot:
            self.twitch_bot.update_stats(stats)

        # Update OBS overlay
        if self.obs_controller.is_connected:
            self.obs_controller.update_overlay(stats)

    def update_decision(self, decision: Dict[str, Any]):
        """
        Update current AI decision for display.

        Args:
            decision: Current decision with action and reasoning
        """
        self.current_decision = decision

        action = decision.get("action", "")
        reasoning = decision.get("reasoning", "")[:100]

        if self.twitch_bot:
            self.twitch_bot.update_action(f"{action}: {reasoning}")

        # Update OBS with decision
        if self.obs_controller.is_connected:
            self.obs_controller.update_decision_overlay(decision)

    def update_objective(self, objective: str):
        """
        Update current objective.

        Args:
            objective: Current game objective
        """
        if self.twitch_bot:
            self.twitch_bot.update_objective(objective)

    def record_highlight_event(self, event_type: str, frame=None, metadata: Dict[str, Any] = None):
        """
        Record a highlight-worthy event.

        Args:
            event_type: Type of event (boss_defeat, puzzle_solve, death, etc.)
            frame: Current game frame
            metadata: Additional event metadata
        """
        self.highlight_generator.record_event(
            event_type=event_type,
            frame=frame,
            metadata=metadata or {},
        )

        # Announce significant events
        if self.twitch_bot and event_type in ["boss_defeat", "dungeon_complete"]:
            asyncio.run_coroutine_threadsafe(
                self.twitch_bot.send_announcement(
                    f"🎉 {event_type.replace('_', ' ').title()}!"
                ),
                self._bot_loop,
            )

    def record_death(self):
        """Record a death event."""
        if self.twitch_bot:
            self.twitch_bot.record_death()

        self.record_highlight_event("death")

    def record_enemy_defeated(self, count: int = 1):
        """Record enemies defeated."""
        if self.twitch_bot:
            self.twitch_bot.record_enemy_defeated(count)

    def _get_game_stats(self) -> Dict[str, Any]:
        """Get current game stats for Twitch bot."""
        return self.current_stats

    def get_stream_stats(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        stats = {
            "is_streaming": self.is_streaming,
            "uptime": None,
            "obs_connected": self.obs_controller.is_connected,
            "twitch_connected": self.twitch_bot is not None,
            "highlights_recorded": self.highlight_generator.get_event_count(),
        }

        if self.start_time:
            uptime = datetime.now() - self.start_time
            stats["uptime"] = str(uptime).split(".")[0]

        if self.twitch_bot:
            stats["viewer_stats"] = self.twitch_bot.get_viewer_stats()

        return stats

    def generate_highlight_reel(self, output_path: str = None) -> Optional[str]:
        """
        Generate highlight reel from recorded events.

        Args:
            output_path: Output path for highlight video

        Returns:
            Path to generated video or None
        """
        return self.highlight_generator.generate_reel(output_path)
