import discord
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class VoiceManager:
    def __init__(self, bot):
        self.bot = bot
    
    async def create_game_channels(self, guild, original_channel, team1, team2):
        """Create voice channels for the game"""
        try:
            # Create a category for this game
            category_name = f"Game - {original_channel.name}"
            category = await guild.create_category(category_name)
            
            # Create team voice channels
            team1_channel = await guild.create_voice_channel(
                "🔴 Team 1",
                category=category
            )
            
            team2_channel = await guild.create_voice_channel(
                "🔵 Team 2", 
                category=category
            )
            
            # Move players to their respective channels
            await self._move_players_to_teams(team1, team2, team1_channel, team2_channel)
            
            return {
                'category': category,
                'team1_channel': team1_channel,
                'team2_channel': team2_channel
            }
            
        except Exception as e:
            logger.error(f"Error creating game channels: {e}")
            return None
    
    async def _move_players_to_teams(self, team1, team2, team1_channel, team2_channel):
        """Move players to their respective team channels"""
        try:
            # Move team 1 players
            for member in team1:
                if member.voice and member.voice.channel:
                    await member.move_to(team1_channel)
                    await asyncio.sleep(0.5)  # Small delay to avoid rate limits
            
            # Move team 2 players
            for member in team2:
                if member.voice and member.voice.channel:
                    await member.move_to(team2_channel)
                    await asyncio.sleep(0.5)
                    
        except Exception as e:
            logger.error(f"Error moving players: {e}")
    
    async def cleanup_game_channels(self, guild, game_data):
        """Clean up voice channels after game ends"""
        try:
            # Get the category and channels
            category = guild.get_channel(game_data['category_id'])
            team1_channel = guild.get_channel(game_data['team1_channel_id'])
            team2_channel = guild.get_channel(game_data['team2_channel_id'])
            
            # Move players back to a general channel if possible
            general_voice = None
            for channel in guild.voice_channels:
                if channel.category != category and not channel.name.startswith(('🔴', '🔵')):
                    general_voice = channel
                    break
            
            # Move players out of team channels
            if team1_channel:
                for member in team1_channel.members:
                    if general_voice:
                        await member.move_to(general_voice)
                    else:
                        await member.move_to(None)  # Disconnect if no general channel
                await team1_channel.delete()
            
            if team2_channel:
                for member in team2_channel.members:
                    if general_voice:
                        await member.move_to(general_voice)
                    else:
                        await member.move_to(None)
                await team2_channel.delete()
            
            # Delete the category
            if category:
                await category.delete()
                
        except Exception as e:
            logger.error(f"Error cleaning up game channels: {e}")
    
    async def handle_voice_state_update(self, member, before, after):
        """Handle voice state updates for cleanup"""
        # This can be used for additional voice state management
        # For example, auto-cleanup if all players leave
        pass
