import discord
import random
import asyncio
import logging
from config import Config

logger = logging.getLogger(__name__)

class DraftManager:
    def __init__(self, bot):
        self.bot = bot
        self.min_players = Config.MIN_PLAYERS
        self.max_players = Config.MAX_PLAYERS
    
    async def start_draft(self, interaction, voice_channel, members):
        """Start the draft process"""
        if len(members) % 2 != 0:
            await interaction.response.send_message(
                "❌ You need an even number of players to create balanced teams!",
                ephemeral=True
            )
            return
        
        # Create teams
        shuffled_members = members.copy()
        random.shuffle(shuffled_members)
        
        mid_point = len(shuffled_members) // 2
        team1 = shuffled_members[:mid_point]
        team2 = shuffled_members[mid_point:]
        
        # Create draft embed
        embed = discord.Embed(
            title="🎮 Game Draft Created",
            description="Teams have been randomly generated!",
            color=discord.Color.green()
        )
        
        team1_names = [member.display_name for member in team1]
        team2_names = [member.display_name for member in team2]
        
        embed.add_field(
            name="🔴 Team 1",
            value="\n".join(team1_names),
            inline=True
        )
        
        embed.add_field(
            name="🔵 Team 2", 
            value="\n".join(team2_names),
            inline=True
        )
        
        view = self.DraftControlView(voice_channel, team1, team2)
        await interaction.response.send_message(embed=embed, view=view)
    
    async def start_game(self, interaction, voice_channel, team1, team2):
        """Actually start the game with voice channel management"""
        try:
            # Create voice channels and move players
            game_data = await self.bot.voice_manager.create_game_channels(
                interaction.guild, voice_channel, team1, team2
            )
            
            if not game_data:
                await interaction.followup.send(
                    "❌ Failed to create game channels. Please try again.",
                    ephemeral=True
                )
                return
            
            # Get next game number and log the game
            game_number = self.bot.stats_manager.get_next_game_number()
            
            # Store active game
            game_id = f"{interaction.guild.id}_{game_number}"
            self.bot.active_games[game_id] = {
                'game_number': game_number,
                'team1': [member.id for member in team1],
                'team2': [member.id for member in team2],
                'category_id': game_data['category'].id,
                'team1_channel_id': game_data['team1_channel'].id,
                'team2_channel_id': game_data['team2_channel'].id,
                'started_by': interaction.user.id,
                'voice_channel_name': voice_channel.name
            }
            
            # Log game start
            await self.bot.stats_manager.log_game_start(
                interaction.guild, game_number, team1, team2
            )
            
            # Create game control embed
            embed = discord.Embed(
                title=f"🎮 Game #{game_number} Started!",
                description="Players have been moved to their team channels.",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="🔴 Team 1",
                value=f"{game_data['team1_channel'].mention}\n" + 
                      "\n".join([member.mention for member in team1]),
                inline=True
            )
            
            embed.add_field(
                name="🔵 Team 2",
                value=f"{game_data['team2_channel'].mention}\n" + 
                      "\n".join([member.mention for member in team2]),
                inline=True
            )
            
            view = self.GameControlView(game_id)
            await interaction.edit_original_response(embed=embed, view=view)
            
        except Exception as e:
            logger.error(f"Error starting game: {e}")
            await interaction.followup.send(
                "❌ An error occurred while starting the game.",
                ephemeral=True
            )
    
    class DraftControlView(discord.ui.View):
        def __init__(self, voice_channel, team1, team2):
            super().__init__(timeout=300)  # 5 minute timeout
            self.voice_channel = voice_channel
            self.team1 = team1
            self.team2 = team2
        
        @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="❌", custom_id="draft_cancel")
        async def cancel_draft(self, interaction: discord.Interaction, button: discord.ui.Button):
            embed = discord.Embed(
                title="❌ Draft Cancelled",
                description="The game draft has been cancelled.",
                color=discord.Color.red()
            )
            await interaction.response.edit_message(embed=embed, view=None)
        
        @discord.ui.button(label="Reroll Teams", style=discord.ButtonStyle.secondary, emoji="🎲", custom_id="draft_reroll")
        async def reroll_teams(self, interaction: discord.Interaction, button: discord.ui.Button):
            # Reroll teams
            all_members = self.team1 + self.team2
            random.shuffle(all_members)
            
            mid_point = len(all_members) // 2
            self.team1 = all_members[:mid_point]
            self.team2 = all_members[mid_point:]
            
            # Update embed
            embed = discord.Embed(
                title="🎮 Teams Rerolled!",
                description="New random teams have been generated!",
                color=discord.Color.orange()
            )
            
            team1_names = [member.display_name for member in self.team1]
            team2_names = [member.display_name for member in self.team2]
            
            embed.add_field(
                name="🔴 Team 1",
                value="\n".join(team1_names),
                inline=True
            )
            
            embed.add_field(
                name="🔵 Team 2",
                value="\n".join(team2_names),
                inline=True
            )
            
            await interaction.response.edit_message(embed=embed, view=self)
        
        @discord.ui.button(label="Start Game", style=discord.ButtonStyle.success, emoji="🚀", custom_id="draft_start_game")
        async def start_game(self, interaction: discord.Interaction, button: discord.ui.Button):
            await interaction.client.draft_manager.start_game(
                interaction, self.voice_channel, self.team1, self.team2
            )
    
    class GameControlView(discord.ui.View):
        def __init__(self, game_id):
            super().__init__(timeout=None)  # Persistent view
            self.game_id = game_id
        
        @discord.ui.button(label="Team 1 Wins", style=discord.ButtonStyle.success, emoji="🔴", custom_id="game_team1_wins")
        async def team1_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._handle_game_end(interaction, 1)
        
        @discord.ui.button(label="Team 2 Wins", style=discord.ButtonStyle.success, emoji="🔵", custom_id="game_team2_wins")
        async def team2_wins(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._handle_game_end(interaction, 2)
        
        @discord.ui.button(label="Cancel Game", style=discord.ButtonStyle.danger, emoji="❌", custom_id="game_cancel")
        async def cancel_game(self, interaction: discord.Interaction, button: discord.ui.Button):
            await self._handle_game_end(interaction, 0)  # 0 = cancelled
        
        async def _handle_game_end(self, interaction: discord.Interaction, winner: int):
            """Handle game ending with winner (1, 2, or 0 for cancelled)"""
            if self.game_id not in interaction.client.active_games:
                await interaction.response.send_message(
                    "❌ This game is no longer active.",
                    ephemeral=True
                )
                return
            
            game_data = interaction.client.active_games[self.game_id]
            
            # Update stats if not cancelled
            if winner > 0:
                await interaction.client.stats_manager.update_game_stats(
                    game_data, winner
                )
            
            # Log game end
            await interaction.client.stats_manager.log_game_end(
                interaction.guild, game_data, winner
            )
            
            # Clean up voice channels
            await interaction.client.voice_manager.cleanup_game_channels(
                interaction.guild, game_data
            )
            
            # Remove from active games
            del interaction.client.active_games[self.game_id]
            
            # Update message
            if winner == 0:
                embed = discord.Embed(
                    title="❌ Game Cancelled",
                    description=f"Game #{game_data['game_number']} has been cancelled.",
                    color=discord.Color.red()
                )
            else:
                winning_team = "Team 1" if winner == 1 else "Team 2"
                embed = discord.Embed(
                    title=f"🎉 {winning_team} Wins!",
                    description=f"Game #{game_data['game_number']} has ended.",
                    color=discord.Color.gold()
                )
            
            await interaction.response.edit_message(embed=embed, view=None)
