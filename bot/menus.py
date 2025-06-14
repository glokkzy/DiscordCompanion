import discord
from discord.ext import commands
import logging

logger = logging.getLogger(__name__)

class MenuManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def send_drafts_menu(self, channel):
        """Send the main drafts menu"""
        embed = discord.Embed(
            title="🎮 Game Drafts",
            description="Welcome to the game drafts system! Create or view active games.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📝 Create Game",
            value="Start a new game draft from your voice channel",
            inline=False
        )
        
        embed.add_field(
            name="👁️ View Games",
            value="See all currently active games",
            inline=False
        )
        
        view = self.DraftsMenuView()
        await channel.send(embed=embed, view=view)
    
    async def send_find_menu(self, channel):
        """Send the regional find menu"""
        embed = discord.Embed(
            title="🔍 Find Players",
            description="Looking for players? Select your region to notify others!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🌅 East",
            value="Eastern time zone players",
            inline=True
        )
        
        embed.add_field(
            name="🌇 Central", 
            value="Central time zone players",
            inline=True
        )
        
        embed.add_field(
            name="🌄 West",
            value="Western time zone players", 
            inline=True
        )
        
        view = self.FindMenuView()
        await channel.send(embed=embed, view=view)
    
    class DraftsMenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)  # Persistent view
        
        @discord.ui.button(label="Create Game", style=discord.ButtonStyle.green, emoji="📝")
        async def create_game(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle create game button"""
            # Check if user is in a voice channel
            if not interaction.user.voice or not interaction.user.voice.channel:
                await interaction.response.send_message(
                    "❌ You must be in a voice channel to create a game!",
                    ephemeral=True
                )
                return
            
            voice_channel = interaction.user.voice.channel
            members = [member for member in voice_channel.members if not member.bot]
            
            if len(members) < interaction.client.draft_manager.min_players:
                await interaction.response.send_message(
                    f"❌ You need at least {interaction.client.draft_manager.min_players} players to start a game!",
                    ephemeral=True
                )
                return
                
            # Start the draft process
            await interaction.client.draft_manager.start_draft(interaction, voice_channel, members)
        
        @discord.ui.button(label="View Games", style=discord.ButtonStyle.secondary, emoji="👁️")
        async def view_games(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Handle view games button"""
            active_games = interaction.client.active_games
            
            if not active_games:
                embed = discord.Embed(
                    title="🎮 Active Games",
                    description="No active games currently running.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🎮 Active Games",
                color=discord.Color.blue()
            )
            
            for game_id, game_data in active_games.items():
                team1_names = [f"<@{uid}>" for uid in game_data['team1']]
                team2_names = [f"<@{uid}>" for uid in game_data['team2']]
                
                embed.add_field(
                    name=f"Game #{game_data['game_number']}",
                    value=f"**Team 1:** {', '.join(team1_names)}\n**Team 2:** {', '.join(team2_names)}",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    class FindMenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)  # Persistent view
        
        @discord.ui.button(label="East", style=discord.ButtonStyle.primary, emoji="🌅")
        async def find_east(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._handle_region_find(interaction, "east")
        
        @discord.ui.button(label="Central", style=discord.ButtonStyle.primary, emoji="🌇")
        async def find_central(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._handle_region_find(interaction, "central")
        
        @discord.ui.button(label="West", style=discord.ButtonStyle.primary, emoji="🌄")
        async def find_west(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._handle_region_find(interaction, "west")
        
        async def _handle_region_find(self, interaction: discord.Interaction, region: str):
            """Handle regional player finding"""
            await interaction.client.matchmaking_manager.handle_region_find(interaction, region)
