import os
import asyncio
from twitchio.ext import commands
from loguru import logger

class TwitchBot(commands.Bot):
    def __init__(self):
        # Get credentials from environment variables
        token = os.getenv('TWITCH_OAUTH_TOKEN')
        client_id = os.getenv('TWITCH_CLIENT_ID')
        client_secret = os.getenv('TWITCH_CLIENT_SECRET')
        initial_channels = os.getenv('TWITCH_CHANNEL', '').split(',')

        if not token or not initial_channels:
            logger.warning("Twitch credentials not found. Twitch integration will be disabled.")
            self.enabled = False
            return

        super().__init__(
            token=token,
            client_id=client_id,
            client_secret=client_secret,
            prefix='!',
            initial_channels=initial_channels
        )
        self.enabled = True
        self.game_state = {}

    async def event_ready(self):
        logger.info(f'Twitch Bot logged in as | {self.nick}')

    async def event_message(self, message):
        if message.echo:
            return
        
        # Process commands
        await self.handle_commands(message)

    @commands.command(name='status')
    async def status_command(self, ctx):
        if not self.game_state:
            await ctx.send("I'm currently not playing or state is unknown.")
            return
        
        health = self.game_state.get('health', '?')
        max_health = self.game_state.get('max_health', '?')
        location = self.game_state.get('location', 'Unknown')
        
        await ctx.send(f"Health: {health}/{max_health} | Location: {location}")

    @commands.command(name='rupees')
    async def rupees_command(self, ctx):
        rupees = self.game_state.get('rupees', 0)
        await ctx.send(f"Current Rupees: {rupees}")

    def update_game_state(self, state):
        """Update the internal game state for chat responses."""
        self.game_state = state

    async def send_message(self, channel_name, message):
        """Send a message to a specific channel."""
        if not self.enabled:
            return
            
        channel = self.get_channel(channel_name)
        if channel:
            await channel.send(message)
        else:
            logger.warning(f"Channel {channel_name} not found or not connected.")

    async def start_bot(self):
        """Start the bot asynchronously."""
        if self.enabled:
            try:
                await self.start()
            except Exception as e:
                logger.error(f"Failed to start Twitch bot: {e}")
