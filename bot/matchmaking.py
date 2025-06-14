import discord
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class MatchmakingManager:
    def __init__(self, bot):
        self.bot = bot
        self.regional_roles = Config.get_regional_roles()
    
    async def handle_region_find(self, interaction, region, location=None):
        """Handle regional player finding with optional location"""
        try:
            # Get the role for this region
            role_id = self.regional_roles.get(region)
            if not role_id:
                await interaction.response.send_message(
                    "❌ Invalid region selected.",
                    ephemeral=True
                )
                return
            
            role = interaction.guild.get_role(role_id)
            if not role:
                await interaction.response.send_message(
                    "❌ Regional role not found. Please contact an administrator.",
                    ephemeral=True
                )
                return
            
            # Get all members with this role
            members_with_role = [member for member in role.members if not member.bot]
            
            if not members_with_role:
                await interaction.response.send_message(
                    f"❌ No players found in the {region.title()} region.",
                    ephemeral=True
                )
                return
            
            # Send confirmation to the user
            region_emoji = {"east": "🌅", "central": "🌇", "west": "🌄"}
            location_text = f" ({location})" if location else ""
            try:
                await interaction.response.send_message(
                    f"{region_emoji.get(region, '🌍')} Looking for players in the **{region.title()}{location_text}** region...\n"
                    f"Sending DMs to {len(members_with_role)} players!",
                    ephemeral=True
                )
            except discord.errors.NotFound:
                # Interaction expired, try followup
                await interaction.followup.send(
                    f"{region_emoji.get(region, '🌍')} Looking for players in the **{region.title()}{location_text}** region...\n"
                    f"Sending DMs to {len(members_with_role)} players!",
                    ephemeral=True
                )
            
            # Send DMs to all members with the role
            await self._send_region_notifications(
                interaction.user, 
                members_with_role, 
                region,
                interaction.guild,
                location
            )
            
        except Exception as e:
            logger.error(f"Error in region find: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while finding players.",
                ephemeral=True
            )
    
    async def _send_region_notifications(self, requester, members, region, guild, location=None):
        """Send DM notifications to regional players"""
        region_emoji = {"east": "🌅", "central": "🌇", "west": "🌄"}
        emoji = region_emoji.get(region, "🌍")
        
        location_text = f" ({location})" if location else ""
        in_game_name = self.bot.profile_manager.get_in_game_name(requester.id)
        embed = discord.Embed(
            title=f"{emoji} Player Looking for Game!",
            description=f"**{requester.display_name}** ({in_game_name}) is looking for players in the **{region.title()}{location_text}** region!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📍 Server",
            value=guild.name,
            inline=True
        )
        
        embed.add_field(
            name="🕐 Time",
            value=f"<t:{int(discord.utils.utcnow().timestamp())}:R>",
            inline=True
        )
        
        embed.add_field(
            name="💬 Join the Action",
            value=f"Head over to {guild.name} to join the game!",
            inline=False
        )
        
        # Send DMs with delays to avoid rate limits
        successful_dms = 0
        failed_dms = 0
        
        for member in members:
            if member.id == requester.id:
                continue  # Don't DM the requester
            
            try:
                await member.send(embed=embed)
                successful_dms += 1
                await asyncio.sleep(1)  # Rate limit protection
                
            except discord.Forbidden:
                # User has DMs disabled
                failed_dms += 1
                continue
            except Exception as e:
                logger.error(f"Error sending DM to {member}: {e}")
                failed_dms += 1
                continue
        
        # Log the results
        logger.info(f"Region find notification: {successful_dms} successful, {failed_dms} failed DMs")
        
        # Optionally send a follow-up to the requester with results
        try:
            result_embed = discord.Embed(
                title="📬 Notification Results",
                description=f"Successfully notified **{successful_dms}** players in the {region.title()} region!",
                color=discord.Color.green()
            )
            
            if failed_dms > 0:
                result_embed.add_field(
                    name="ℹ️ Note",
                    value=f"{failed_dms} players couldn't be reached (DMs disabled)",
                    inline=False
                )
            
            await requester.send(embed=result_embed)
            
        except Exception as e:
            logger.error(f"Error sending results to requester: {e}")
