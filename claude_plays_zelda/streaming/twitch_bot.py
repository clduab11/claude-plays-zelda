"""Twitch bot for chat interaction and stream management."""
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from twitchio.ext import commands
from loguru import logger


class TwitchBot(commands.Bot):
    """Twitch bot for chat commands and stream interaction."""

    def __init__(
        self,
        token: str,
        prefix: str = "!",
        initial_channels: list = None,
        stats_callback: Optional[Callable] = None,
    ):
        """
        Initialize Twitch bot.

        Args:
            token: Twitch OAuth token
            prefix: Command prefix
            initial_channels: List of channels to join
            stats_callback: Callback function to get current game stats
        """
        super().__init__(
            token=token,
            prefix=prefix,
            initial_channels=initial_channels or [],
        )

        self.stats_callback = stats_callback
        self.start_time = datetime.now()
        self.command_count = 0
        self.viewer_interactions: Dict[str, int] = {}

        # Game state for display
        self.current_stats: Dict[str, Any] = {}
        self.current_objective = "Starting adventure..."
        self.last_action = "Initializing..."
        self.deaths = 0
        self.enemies_defeated = 0

        logger.info("TwitchBot initialized")

    async def event_ready(self):
        """Called when bot is ready."""
        logger.info(f"Twitch bot logged in as {self.nick}")
        logger.info(f"Connected to channels: {[c.name for c in self.connected_channels]}")

    async def event_message(self, message):
        """Handle incoming messages."""
        if message.echo:
            return

        # Track viewer interactions
        author = message.author.name
        self.viewer_interactions[author] = self.viewer_interactions.get(author, 0) + 1

        await self.handle_commands(message)

    @commands.command(name="stats")
    async def cmd_stats(self, ctx):
        """Show current game statistics."""
        self.command_count += 1

        stats = self._get_current_stats()

        response = (
            f"📊 Stats | Hearts: {stats.get('hearts', '?')}/{stats.get('max_hearts', '?')} | "
            f"Rupees: {stats.get('rupees', 0)} | "
            f"Deaths: {self.deaths} | "
            f"Enemies: {self.enemies_defeated}"
        )

        await ctx.send(response)
        logger.debug(f"Stats command from {ctx.author.name}")

    @commands.command(name="progress")
    async def cmd_progress(self, ctx):
        """Show current progress and objective."""
        self.command_count += 1

        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        response = (
            f"🎯 Objective: {self.current_objective} | "
            f"⏱️ Uptime: {hours}h {minutes}m | "
            f"Last Action: {self.last_action}"
        )

        await ctx.send(response)
        logger.debug(f"Progress command from {ctx.author.name}")

    @commands.command(name="help")
    async def cmd_help(self, ctx):
        """Show available commands."""
        self.command_count += 1

        response = (
            "🎮 Commands: !stats (game stats) | !progress (current objective) | "
            "!deaths (death count) | !uptime (stream time) | !ai (AI info)"
        )

        await ctx.send(response)

    @commands.command(name="deaths")
    async def cmd_deaths(self, ctx):
        """Show death count."""
        self.command_count += 1

        response = f"💀 Deaths this session: {self.deaths}"
        await ctx.send(response)

    @commands.command(name="uptime")
    async def cmd_uptime(self, ctx):
        """Show stream uptime."""
        self.command_count += 1

        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)

        response = f"⏱️ Stream uptime: {hours}h {minutes}m {seconds}s"
        await ctx.send(response)

    @commands.command(name="ai")
    async def cmd_ai(self, ctx):
        """Show AI information."""
        self.command_count += 1

        response = (
            "🤖 This stream is powered by Claude AI (Anthropic). "
            "The AI makes decisions by analyzing the game screen and using "
            "computer vision + natural language reasoning. No human input!"
        )

        await ctx.send(response)

    @commands.command(name="donate")
    async def cmd_donate(self, ctx):
        """Show donation/support info."""
        self.command_count += 1

        response = (
            "💝 Thanks for watching! This is an open-source AI project. "
            "Star us on GitHub: github.com/clduab11/claude-plays-zelda"
        )

        await ctx.send(response)

    def _get_current_stats(self) -> Dict[str, Any]:
        """Get current game stats from callback or cached."""
        if self.stats_callback:
            try:
                return self.stats_callback()
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
        return self.current_stats

    def update_stats(self, stats: Dict[str, Any]):
        """Update cached game statistics."""
        self.current_stats = stats

        # Extract specific stats
        hearts = stats.get("hearts", {})
        if hearts:
            self.current_stats["hearts"] = hearts.get("current_hearts", 0)
            self.current_stats["max_hearts"] = hearts.get("max_hearts", 0)

    def update_objective(self, objective: str):
        """Update current objective display."""
        self.current_objective = objective

    def update_action(self, action: str):
        """Update last action display."""
        self.last_action = action

    def record_death(self):
        """Record a death."""
        self.deaths += 1
        logger.info(f"Death recorded. Total: {self.deaths}")

    def record_enemy_defeated(self, count: int = 1):
        """Record enemies defeated."""
        self.enemies_defeated += count

    async def send_announcement(self, message: str):
        """Send announcement to all connected channels."""
        for channel in self.connected_channels:
            try:
                await channel.send(message)
            except Exception as e:
                logger.error(f"Error sending to {channel.name}: {e}")

    def get_viewer_stats(self) -> Dict[str, Any]:
        """Get viewer interaction statistics."""
        return {
            "unique_viewers": len(self.viewer_interactions),
            "total_interactions": sum(self.viewer_interactions.values()),
            "commands_processed": self.command_count,
            "top_viewers": sorted(
                self.viewer_interactions.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
        }

    async def run_bot(self):
        """Run the bot (wrapper for async context)."""
        try:
            await self.start()
        except Exception as e:
            logger.error(f"Bot error: {e}")
            raise
