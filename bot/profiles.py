import json
import os
import discord
import logging
from config import Config

logger = logging.getLogger(__name__)

class ProfileManager:
    def __init__(self, bot):
        self.bot = bot
        self._ensure_data_directory()
        self.whitelist_file = "data/host_whitelist.json"
        self.profiles_file = "data/user_profiles.json"
        self.whitelist = self._load_whitelist()
        self.profiles = self._load_profiles()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        if not os.path.exists("data"):
            os.makedirs("data")
    
    def _load_whitelist(self):
        """Load host whitelist from file"""
        try:
            if os.path.exists(self.whitelist_file):
                with open(self.whitelist_file, 'r') as f:
                    return json.load(f)
            return {"hosts": []}
        except Exception as e:
            logger.error(f"Error loading whitelist: {e}")
            return {"hosts": []}
    
    def _save_whitelist(self):
        """Save host whitelist to file"""
        try:
            with open(self.whitelist_file, 'w') as f:
                json.dump(self.whitelist, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving whitelist: {e}")
    
    def _load_profiles(self):
        """Load user profiles from file"""
        try:
            if os.path.exists(self.profiles_file):
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading profiles: {e}")
            return {}
    
    def _save_profiles(self):
        """Save user profiles to file"""
        try:
            with open(self.profiles_file, 'w') as f:
                json.dump(self.profiles, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving profiles: {e}")
    
    async def add_host(self, host_id, in_game_name, guild):
        """Add a host to the whitelist and assign role"""
        if str(host_id) not in self.whitelist["hosts"]:
            self.whitelist["hosts"].append(str(host_id))
            self._save_whitelist()
        
        # Also add their profile
        self.profiles[str(host_id)] = {
            "in_game_name": in_game_name,
            "is_host": True
        }
        self._save_profiles()
        
        # Assign host role
        try:
            member = guild.get_member(host_id)
            if member:
                host_role = guild.get_role(Config.HOST_ROLE_ID)
                if host_role and host_role not in member.roles:
                    await member.add_roles(host_role)
        except Exception as e:
            logger.error(f"Error adding host role: {e}")
    
    def is_whitelisted(self, user_id):
        """Check if user is whitelisted (either host or has profile)"""
        return str(user_id) in self.whitelist["hosts"] or str(user_id) in self.profiles
    
    def get_in_game_name(self, user_id):
        """Get user's in-game name"""
        profile = self.profiles.get(str(user_id))
        if profile:
            return profile.get("in_game_name", "Unknown")
        return "Unknown"
    
    def has_profile(self, user_id):
        """Check if user has a profile"""
        return str(user_id) in self.profiles
    
    async def send_host_setup_menu(self, channel):
        """Send the host setup menu (admin only)"""
        embed = discord.Embed(
            title="🛠️ Host Setup",
            description="Setup new hosts and user profiles for the bot",
            color=discord.Color.orange()
        )
        
        embed.add_field(
            name="⚙️ Setup",
            value="Add a new host and their profile",
            inline=False
        )
        
        embed.set_footer(text="Admin only - Setup new hosts to use the bot")
        
        view = HostSetupView()
        await channel.send(embed=embed, view=view)

class HostSetupView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Setup", style=discord.ButtonStyle.primary, emoji="⚙️", custom_id="host_setup")
    async def setup_host(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle setup button - admin only"""
        if interaction.user.id != Config.ADMIN_USER_ID:
            await interaction.response.send_message(
                "❌ Only the bot admin can use this feature.",
                ephemeral=True
            )
            return
        
        modal = HostSetupModal()
        await interaction.response.send_modal(modal)

class HostSetupModal(discord.ui.Modal, title="Host Setup"):
    def __init__(self):
        super().__init__()
    
    host_id = discord.ui.TextInput(
        label="Host User ID",
        placeholder="Enter the Discord user ID of the host",
        required=True,
        max_length=20
    )
    
    in_game_name = discord.ui.TextInput(
        label="In-Game Name", 
        placeholder="Enter the host's in-game name",
        required=True,
        max_length=50
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            host_user_id = int(self.host_id.value.strip())
            game_name = self.in_game_name.value.strip()
            
            # Add to whitelist and profile
            await interaction.client.profile_manager.add_host(host_user_id, game_name, interaction.guild)
            
            embed = discord.Embed(
                title="✅ Host Added Successfully",
                color=discord.Color.green()
            )
            
            embed.add_field(name="Host ID", value=str(host_user_id), inline=True)
            embed.add_field(name="In-Game Name", value=game_name, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except ValueError:
            await interaction.response.send_message(
                "❌ Invalid user ID. Please enter a valid Discord user ID (numbers only).",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Error in host setup: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while setting up the host.",
                ephemeral=True
            )