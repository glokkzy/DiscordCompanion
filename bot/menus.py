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
    
    async def send_stats_menu(self, channel):
        """Send the stats menu"""
        embed = discord.Embed(
            title="📊 Player Statistics",
            description="View your stats or check the leaderboard!",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="👤 My Stats",
            value="View your personal statistics",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Leaderboard",
            value="See the top players",
            inline=True
        )
        
        embed.add_field(
            name="🔍 Player Stats",
            value="Check another player's stats",
            inline=True
        )
        
        view = StatsMenuView()
        await channel.send(embed=embed, view=view)

class DraftsMenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)  # Persistent view
        
        @discord.ui.button(label="Create Game", style=discord.ButtonStyle.green, emoji="📝", custom_id="drafts_create_game")
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
        
        @discord.ui.button(label="View Games", style=discord.ButtonStyle.secondary, emoji="👁️", custom_id="drafts_view_games")
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
        
        @discord.ui.button(label="East", style=discord.ButtonStyle.primary, emoji="🌅", custom_id="find_east")
        async def find_east(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._show_location_menu(interaction, "east")
        
        @discord.ui.button(label="Central", style=discord.ButtonStyle.primary, emoji="🌇", custom_id="find_central")
        async def find_central(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._show_location_menu(interaction, "central")
        
        @discord.ui.button(label="West", style=discord.ButtonStyle.primary, emoji="🌄", custom_id="find_west")
        async def find_west(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._show_location_menu(interaction, "west")
        
        async def _show_location_menu(self, interaction: discord.Interaction, region: str):
            """Show location-specific menu for region"""
            region_emoji = {"east": "🌅", "central": "🌇", "west": "🌄"}
            
            embed = discord.Embed(
                title=f"{region_emoji.get(region, '🌍')} {region.title()} Region Locations",
                description=f"Select a specific location in the {region.title()} region:",
                color=discord.Color.blue()
            )
            
            view = LocationMenuView(region)
            try:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            except discord.errors.NotFound:
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        async def _handle_region_find(self, interaction: discord.Interaction, region: str, location: str = None):
            """Handle regional player finding with location"""
            await interaction.client.matchmaking_manager.handle_region_find(interaction, region, location)

class LocationMenuView(discord.ui.View):
    def __init__(self, region):
        super().__init__(timeout=300)  # 5 minute timeout
        self.region = region
        
        # Add location-specific buttons based on region
        if region == "east":
            self.add_item(LocationButton("Ashburn", "ashburn", "🏢"))
            self.add_item(LocationButton("Ohio", "ohio", "🌽"))
        elif region == "central":
            self.add_item(LocationButton("Iowa", "iowa", "🌾"))
            self.add_item(LocationButton("San Antonio", "san_antonio", "🌵"))
        elif region == "west":
            self.add_item(LocationButton("San Francisco", "san_francisco", "🌉"))
            self.add_item(LocationButton("Quincy", "quincy", "🏔️"))

class LocationButton(discord.ui.Button):
    def __init__(self, label, location_id, emoji):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.secondary,
            emoji=emoji,
            custom_id=f"location_{location_id}"
        )
        self.location_id = location_id
        self.location_name = label
    
    async def callback(self, interaction: discord.Interaction):
        # Get the parent view to access region
        view = self.view
        region = view.region if hasattr(view, 'region') else 'unknown'
        
        try:
            await interaction.client.matchmaking_manager.handle_region_find(
                interaction, region, self.location_name
            )
        except Exception as e:
            logger.error(f"Error in location button callback: {e}")
            try:
                await interaction.response.send_message(
                    "❌ Error processing request. Please try again.",
                    ephemeral=True
                )
            except:
                pass

class StatsMenuView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)  # Persistent view
        
        @discord.ui.button(label="My Stats", style=discord.ButtonStyle.primary, emoji="👤", custom_id="stats_my_stats")
        async def my_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Show user's personal stats"""
            stats = interaction.client.stats_manager.get_player_stats(interaction.user.id)
            
            embed = discord.Embed(
                title=f"📊 Stats for {interaction.user.display_name}",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Games Played", value=stats['games_played'], inline=True)
            embed.add_field(name="Wins", value=stats['wins'], inline=True)
            embed.add_field(name="Losses", value=stats['losses'], inline=True)
            
            if stats['games_played'] > 0:
                win_rate = (stats['wins'] / stats['games_played']) * 100
                embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        @discord.ui.button(label="Leaderboard", style=discord.ButtonStyle.success, emoji="🏆", custom_id="stats_leaderboard")
        async def leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Show the leaderboard in public channel"""
            await interaction.client.stats_manager.post_public_leaderboard(interaction)
        
        @discord.ui.button(label="Player Stats", style=discord.ButtonStyle.secondary, emoji="🔍", custom_id="stats_player_lookup")
        async def player_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
            """Show modal to look up another player's stats"""
            modal = PlayerStatsModal()
            await interaction.response.send_modal(modal)

class PlayerStatsModal(discord.ui.Modal, title="Player Stats Lookup"):
    def __init__(self):
        super().__init__()
    
    player_name = discord.ui.TextInput(
        label="Player Name",
        placeholder="Enter the player's username or mention them (@username)",
        required=True,
        max_length=100
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        # Try to find the user by mention or username
        player_input = self.player_name.value.strip()
        
        # Remove @ if user used mention format
        if player_input.startswith('@'):
            player_input = player_input[1:]
        
        # Try to find user in the guild
        user = None
        for member in interaction.guild.members:
            if (member.display_name.lower() == player_input.lower() or 
                member.name.lower() == player_input.lower() or
                str(member) == player_input):
                user = member
                break
        
        if not user:
            await interaction.response.send_message(
                f"❌ Could not find player '{player_input}'. Try using their exact username.",
                ephemeral=True
            )
            return
        
        stats = interaction.client.stats_manager.get_player_stats(user.id)
        
        embed = discord.Embed(
            title=f"📊 Stats for {user.display_name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Games Played", value=stats['games_played'], inline=True)
        embed.add_field(name="Wins", value=stats['wins'], inline=True)
        embed.add_field(name="Losses", value=stats['losses'], inline=True)
        
        if stats['games_played'] > 0:
            win_rate = (stats['wins'] / stats['games_played']) * 100
            embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
