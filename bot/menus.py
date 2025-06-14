import discord
import logging
from config import Config

logger = logging.getLogger(__name__)

class MenuManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def send_drafts_menu(self, channel):
        """Send the main drafts menu"""
        embed = discord.Embed(
            title="🎮 Team Drafts",
            description="Create balanced teams for your games!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="📝 Create Game",
            value="Start a new draft from your voice channel",
            inline=True
        )
        
        embed.add_field(
            name="👀 View Games",
            value="See all currently active games",
            inline=True
        )
        
        view = DraftsMenuView()
        await channel.send(embed=embed, view=view)
    
    async def send_find_menu(self, channel):
        """Send the regional find menu"""
        embed = discord.Embed(
            title="🌍 Find Players",
            description="Search for players in your region!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="🌅 East",
            value="Find players in the East region",
            inline=True
        )
        
        embed.add_field(
            name="🌇 Central", 
            value="Find players in the Central region",
            inline=True
        )
        
        embed.add_field(
            name="🌄 West",
            value="Find players in the West region", 
            inline=True
        )
        
        view = FindMenuView()
        await channel.send(embed=embed, view=view)
    
    async def send_stats_menu(self, channel):
        """Send the stats menu"""
        embed = discord.Embed(
            title="📊 Player Statistics",
            description="Track your wins, losses, and performance!",
            color=discord.Color.gold()
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
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Create Game", style=discord.ButtonStyle.green, emoji="📝", custom_id="drafts_create_game")
    async def create_game(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle create game button"""
        # Check if user is whitelisted
        if not interaction.client.profile_manager.is_whitelisted(interaction.user.id):
            await interaction.response.send_message(
                "❌ You need to be added by a host to use this bot. Contact an administrator.",
                ephemeral=True
            )
            return
            
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                "❌ You must be in a voice channel to create a game!",
                ephemeral=True
            )
            return
        
        voice_channel = interaction.user.voice.channel
        members = [member for member in voice_channel.members if not member.bot]
        
        if len(members) < Config.MIN_PLAYERS:
            await interaction.response.send_message(
                f"❌ Need at least {Config.MIN_PLAYERS} players in voice channel!",
                ephemeral=True
            )
            return
        
        await interaction.client.draft_manager.start_draft(interaction, voice_channel, members)
    
    @discord.ui.button(label="View Games", style=discord.ButtonStyle.blurple, emoji="👀", custom_id="drafts_view_games")
    async def view_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle view games button"""
        active_games = interaction.client.active_games
        
        if not active_games:
            await interaction.response.send_message(
                "📭 No active games currently running.",
                ephemeral=True
            )
            return
        
        embed = discord.Embed(
            title="🎮 Active Games",
            color=discord.Color.blue()
        )
        
        for game_id, game_data in active_games.items():
            team1_names = [member.display_name for member in game_data['team1']]
            team2_names = [member.display_name for member in game_data['team2']]
            
            embed.add_field(
                name=f"Game #{game_data['game_number']}",
                value=f"**Team 1:** {', '.join(team1_names)}\n**Team 2:** {', '.join(team2_names)}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class FindMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
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

class LocationMenuView(discord.ui.View):
    def __init__(self, region):
        super().__init__(timeout=300)
        self.region = region
        
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
        super().__init__(timeout=None)
    
    @discord.ui.button(label="My Stats", style=discord.ButtonStyle.primary, emoji="👤", custom_id="stats_my_stats")
    async def my_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Show user's personal stats"""
        stats = interaction.client.stats_manager.get_player_stats(interaction.user.id)
        
        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Stats",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Games Played", value=str(stats['games_played']), inline=True)
        embed.add_field(name="Wins", value=str(stats['wins']), inline=True)
        embed.add_field(name="Losses", value=str(stats['losses']), inline=True)
        
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
        player_input = self.player_name.value.strip()
        
        target_user = None
        if interaction.guild and interaction.guild.members:
            for member in interaction.guild.members:
                if (player_input.lower() in member.display_name.lower() or 
                    player_input.lower() in member.name.lower() or
                    player_input == str(member.id) or
                    player_input == f"<@{member.id}>" or
                    player_input == f"<@!{member.id}>"):
                    target_user = member
                    break
        
        if not target_user:
            await interaction.response.send_message(
                f"❌ Player '{player_input}' not found. Try using their exact username.",
                ephemeral=True
            )
            return
        
        stats = interaction.client.stats_manager.get_player_stats(target_user.id)
        
        embed = discord.Embed(
            title=f"📊 {target_user.display_name}'s Stats", 
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Games Played", value=str(stats['games_played']), inline=True)
        embed.add_field(name="Wins", value=str(stats['wins']), inline=True)
        embed.add_field(name="Losses", value=str(stats['losses']), inline=True)
        
        if stats['games_played'] > 0:
            win_rate = (stats['wins'] / stats['games_played']) * 100
            embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)