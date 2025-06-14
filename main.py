import discord
from discord.ext import commands
import asyncio
import logging
import os
from dotenv import load_dotenv
from config import Config
from bot.menus import MenuManager
from bot.drafts import DraftManager
from bot.voice_manager import VoiceManager
from bot.stats import StatsManager
from bot.matchmaking import MatchmakingManager
from bot.profiles import ProfileManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GameBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None
        )
        
        # Initialize managers
        self.menu_manager = MenuManager(self)
        self.draft_manager = DraftManager(self)
        self.voice_manager = VoiceManager(self)
        self.stats_manager = StatsManager(self)
        self.matchmaking_manager = MatchmakingManager(self)
        self.profile_manager = ProfileManager(self)
        
        # Store active games
        self.active_games = {}
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        logger.info("Setting up bot...")
        
        # Add views that need to persist across restarts
        from bot.menus import DraftsMenuView, FindMenuView, StatsMenuView
        from bot.profiles import HostSetupView
        self.add_view(DraftsMenuView())
        self.add_view(FindMenuView())
        self.add_view(StatsMenuView())
        self.add_view(HostSetupView())
        
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Send menus to designated channels
        await self.send_startup_menus()
        
    async def send_startup_menus(self):
        """Send the main menus to configured channels"""
        try:
            guild = self.get_guild(Config.GUILD_ID)
            if not guild:
                logger.error("Could not find configured guild")
                return
                
            # Check for existing menus and only send if needed
            drafts_channel = guild.get_channel(Config.DRAFTS_CHANNEL_ID)
            if drafts_channel and not await self._has_bot_menu(drafts_channel):
                await self.menu_manager.send_drafts_menu(drafts_channel)
                logger.info("Sent drafts menu to channel")
                
            find_channel = guild.get_channel(Config.FIND_CHANNEL_ID)
            if find_channel and not await self._has_bot_menu(find_channel):
                await self.menu_manager.send_find_menu(find_channel)
                logger.info("Sent find menu to channel")
                
            stats_channel = guild.get_channel(Config.STATS_CHANNEL_ID)
            if stats_channel and not await self._has_bot_menu(stats_channel):
                await self.menu_manager.send_stats_menu(stats_channel)
                logger.info("Sent stats menu to channel")
                
            # Send host setup menu (admin only channel)
            host_setup_channel = guild.get_channel(Config.HOST_SETUP_CHANNEL_ID)
            if host_setup_channel and not await self._has_bot_menu(host_setup_channel):
                await self.profile_manager.send_host_setup_menu(host_setup_channel)
                logger.info("Sent host setup menu to channel")
                
        except Exception as e:
            logger.error(f"Error sending startup menus: {e}")
    
    async def _has_bot_menu(self, channel):
        """Check if channel already has a bot menu"""
        try:
            async for message in channel.history(limit=20):
                if message.author == self.user and message.embeds:
                    return True
            return False
        except Exception:
            return False
    
    async def on_voice_state_update(self, member, before, after):
        """Handle voice state changes"""
        await self.voice_manager.handle_voice_state_update(member, before, after)

# Create bot instance
bot = GameBot()

@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup_command(ctx):
    """Setup command for administrators to send menus manually"""
    await bot.menu_manager.send_drafts_menu(ctx.channel)
    await ctx.send("✅ Menus have been set up!")

@bot.command(name='stats')
async def stats_command(ctx, member: discord.Member = None):
    """Show player statistics"""
    if member is None:
        member = ctx.author
    
    stats = bot.stats_manager.get_player_stats(member.id)
    
    embed = discord.Embed(
        title=f"📊 Stats for {member.display_name}",
        color=discord.Color.blue()
    )
    
    embed.add_field(name="Games Played", value=stats['games_played'], inline=True)
    embed.add_field(name="Wins", value=stats['wins'], inline=True)
    embed.add_field(name="Losses", value=stats['losses'], inline=True)
    
    if stats['games_played'] > 0:
        win_rate = (stats['wins'] / stats['games_played']) * 100
        embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='leaderboard')
async def leaderboard_command(ctx):
    """Show the leaderboard"""
    leaderboard = bot.stats_manager.get_leaderboard()
    
    embed = discord.Embed(
        title="🏆 Leaderboard",
        color=discord.Color.gold()
    )
    
    if not leaderboard:
        embed.description = "No games played yet!"
        await ctx.send(embed=embed)
        return
    
    description = ""
    for i, (user_id, stats) in enumerate(leaderboard[:10], 1):
        try:
            user = bot.get_user(user_id)
            name = user.display_name if user else f"User {user_id}"
            win_rate = (stats['wins'] / stats['games_played']) * 100 if stats['games_played'] > 0 else 0
            description += f"{i}. **{name}** - {stats['wins']}W/{stats['losses']}L ({win_rate:.1f}%)\n"
        except Exception:
            continue
    
    embed.description = description
    await ctx.send(embed=embed)

if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    try:
        bot.run(token)
    except discord.LoginFailure:
        logger.error("Invalid Discord token")
    except Exception as e:
        logger.error(f"Error running bot: {e}")
