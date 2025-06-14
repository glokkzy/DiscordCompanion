import discord
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class AdminManager:
    def __init__(self, bot):
        self.bot = bot
    
    def has_management_role(self, member):
        """Check if user has management role"""
        if not hasattr(member, 'roles'):
            return False
        return any(role.id == Config.MANAGEMENT_ROLE_ID for role in member.roles)
    
    def has_host_role(self, member):
        """Check if user has host role"""
        if not hasattr(member, 'roles'):
            return False
        return any(role.id == Config.HOST_ROLE_ID for role in member.roles)
    
    async def send_admin_panel(self, channel):
        """Send the admin panel menu"""
        embed = discord.Embed(
            title="🛠️ Admin Panel",
            description="Management tools for bot administration",
            color=discord.Color.red()
        )
        
        embed.add_field(
            name="🔄 Refresh Menus",
            value="Refresh all bot menus in their channels",
            inline=False
        )
        
        embed.add_field(
            name="🔍 Game Search",
            value="Search through game logs and statistics",
            inline=False
        )
        
        embed.set_footer(text="Management role required")
        
        view = AdminPanelView()
        await channel.send(embed=embed, view=view)
    
    async def log_bot_action(self, user, action, details=None, guild=None):
        """Log bot usage to the designated channel"""
        try:
            if not guild:
                guild = self.bot.get_guild(Config.GUILD_ID)
            
            log_channel = guild.get_channel(Config.BOT_LOGS_CHANNEL_ID)
            if not log_channel:
                return
            
            embed = discord.Embed(
                title="📊 Bot Usage Log",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="User", value=f"{user.display_name} ({user.id})", inline=True)
            embed.add_field(name="Action", value=action, inline=True)
            embed.add_field(name="Channel", value=f"<#{getattr(user, 'channel', {}).get('id', 'Unknown')}>", inline=True)
            
            if details:
                embed.add_field(name="Details", value=details, inline=False)
            
            # Check if user has host role
            is_host = self.has_host_role(user) if hasattr(user, 'roles') else False
            embed.add_field(name="User Type", value="Host" if is_host else "Member", inline=True)
            
            await log_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error logging bot action: {e}")
    
    async def refresh_menu(self, interaction, menu_type):
        """Refresh a specific menu by purging and resending"""
        try:
            guild = interaction.guild
            channel_map = {
                "drafts": Config.DRAFTS_CHANNEL_ID,
                "find": Config.FIND_CHANNEL_ID, 
                "stats": Config.STATS_CHANNEL_ID,
                "host_setup": Config.HOST_SETUP_CHANNEL_ID
            }
            
            channel_id = channel_map.get(menu_type)
            if not channel_id:
                await interaction.response.send_message("❌ Invalid menu type", ephemeral=True)
                return
            
            channel = guild.get_channel(channel_id)
            if not channel:
                await interaction.response.send_message("❌ Channel not found", ephemeral=True)
                return
            
            # Purge channel messages from bot
            await interaction.response.defer(ephemeral=True)
            
            async for message in channel.history(limit=50):
                if message.author == self.bot.user:
                    try:
                        await message.delete()
                    except:
                        pass
            
            # Resend appropriate menu
            if menu_type == "drafts":
                await self.bot.menu_manager.send_drafts_menu(channel)
            elif menu_type == "find":
                await self.bot.menu_manager.send_find_menu(channel)
            elif menu_type == "stats":
                await self.bot.menu_manager.send_stats_menu(channel)
            elif menu_type == "host_setup":
                await self.bot.profile_manager.send_host_setup_menu(channel)
                await self.send_admin_panel(channel)
            
            await interaction.followup.send(f"✅ {menu_type.title()} menu refreshed", ephemeral=True)
            
            # Log the action
            await self.log_bot_action(
                interaction.user,
                f"Refreshed {menu_type} menu",
                f"Channel: {channel.name}",
                guild
            )
            
        except Exception as e:
            logger.error(f"Error refreshing menu: {e}")
            try:
                await interaction.followup.send("❌ Error refreshing menu", ephemeral=True)
            except:
                pass

class AdminPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Refresh Drafts", style=discord.ButtonStyle.secondary, emoji="🎮", custom_id="admin_refresh_drafts")
    async def refresh_drafts(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.admin_manager.has_management_role(interaction.user):
            await interaction.response.send_message("❌ Management role required", ephemeral=True)
            return
        await interaction.client.admin_manager.refresh_menu(interaction, "drafts")
    
    @discord.ui.button(label="Refresh Find", style=discord.ButtonStyle.secondary, emoji="🌍", custom_id="admin_refresh_find")
    async def refresh_find(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.admin_manager.has_management_role(interaction.user):
            await interaction.response.send_message("❌ Management role required", ephemeral=True)
            return
        await interaction.client.admin_manager.refresh_menu(interaction, "find")
    
    @discord.ui.button(label="Refresh Stats", style=discord.ButtonStyle.secondary, emoji="📊", custom_id="admin_refresh_stats")
    async def refresh_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.admin_manager.has_management_role(interaction.user):
            await interaction.response.send_message("❌ Management role required", ephemeral=True)
            return
        await interaction.client.admin_manager.refresh_menu(interaction, "stats")
    
    @discord.ui.button(label="Refresh Leaderboard", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="admin_refresh_leaderboard")
    async def refresh_leaderboard(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.admin_manager.has_management_role(interaction.user):
            await interaction.response.send_message("❌ Management role required", ephemeral=True)
            return
        await interaction.client.stats_manager.post_public_leaderboard(interaction)
        await interaction.client.admin_manager.log_bot_action(
            interaction.user, 
            "Refreshed leaderboard",
            "Posted new leaderboard to public channel",
            interaction.guild
        )
    
    @discord.ui.button(label="Refresh Setup", style=discord.ButtonStyle.secondary, emoji="⚙️", custom_id="admin_refresh_setup")
    async def refresh_setup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.admin_manager.has_management_role(interaction.user):
            await interaction.response.send_message("❌ Management role required", ephemeral=True)
            return
        await interaction.client.admin_manager.refresh_menu(interaction, "host_setup")
    
    @discord.ui.button(label="Game Search", style=discord.ButtonStyle.primary, emoji="🔍", custom_id="admin_game_search", row=1)
    async def game_search(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.client.admin_manager.has_management_role(interaction.user):
            await interaction.response.send_message("❌ Management role required", ephemeral=True)
            return
        
        modal = GameSearchModal()
        await interaction.response.send_modal(modal)

class GameSearchModal(discord.ui.Modal, title="Game Search"):
    def __init__(self):
        super().__init__()
    
    search_term = discord.ui.TextInput(
        label="Search Term",
        placeholder="Enter player name, game number, or 'all' for recent games",
        required=True,
        max_length=100
    )
    
    limit = discord.ui.TextInput(
        label="Number of Results",
        placeholder="Enter number of results (default: 10, max: 50)",
        required=False,
        max_length=2,
        default="10"
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            search_query = self.search_term.value.strip().lower()
            result_limit = min(int(self.limit.value or 10), 50)
            
            # Access game log data
            game_log = interaction.client.stats_manager._load_game_log()
            
            if not game_log.get("games"):
                await interaction.response.send_message("❌ No games found in log", ephemeral=True)
                return
            
            matching_games = []
            
            if search_query == "all":
                matching_games = list(game_log["games"].values())[-result_limit:]
            else:
                for game_id, game_data in game_log["games"].items():
                    # Search in player names or game number
                    if (search_query in str(game_data.get("game_number", "")).lower() or
                        any(search_query in player.lower() for player in game_data.get("team1_names", [])) or
                        any(search_query in player.lower() for player in game_data.get("team2_names", [])) or
                        search_query in game_data.get("winner", "").lower()):
                        matching_games.append(game_data)
            
            if not matching_games:
                await interaction.response.send_message(f"❌ No games found matching '{search_query}'", ephemeral=True)
                return
            
            # Sort by game number (most recent first)
            matching_games.sort(key=lambda x: x.get("game_number", 0), reverse=True)
            matching_games = matching_games[:result_limit]
            
            embed = discord.Embed(
                title=f"🔍 Game Search Results",
                description=f"Found {len(matching_games)} games matching '{search_query}'",
                color=discord.Color.gold()
            )
            
            for game in matching_games[:10]:  # Limit embed fields
                game_num = game.get("game_number", "Unknown")
                team1 = ", ".join(game.get("team1_names", []))
                team2 = ", ".join(game.get("team2_names", []))
                winner = game.get("winner", "Unknown")
                timestamp = game.get("timestamp", "Unknown")
                
                field_value = f"**Teams:** {team1} vs {team2}\n**Winner:** {winner}\n**Time:** {timestamp}"
                embed.add_field(
                    name=f"Game #{game_num}",
                    value=field_value,
                    inline=False
                )
            
            if len(matching_games) > 10:
                embed.set_footer(text=f"Showing first 10 of {len(matching_games)} results")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log the search
            await interaction.client.admin_manager.log_bot_action(
                interaction.user,
                "Game search performed",
                f"Query: '{search_query}', Results: {len(matching_games)}",
                interaction.guild
            )
            
        except ValueError:
            await interaction.response.send_message("❌ Invalid number format for results limit", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in game search: {e}")
            await interaction.response.send_message("❌ Error performing search", ephemeral=True)