import json
import os
import discord
import logging
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class StatsManager:
    def __init__(self, bot):
        self.bot = bot
        self.stats_file = Config.PLAYER_STATS_FILE
        self.log_file = Config.GAME_LOG_FILE
        self._ensure_data_directory()
        self._load_stats()
        self._load_game_log()
    
    def _ensure_data_directory(self):
        """Ensure the data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    def _load_stats(self):
        """Load player statistics from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    self.player_stats = json.load(f)
            else:
                self.player_stats = {}
        except Exception as e:
            logger.error(f"Error loading stats: {e}")
            self.player_stats = {}
    
    def _save_stats(self):
        """Save player statistics to file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.player_stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def _load_game_log(self):
        """Load game log from file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.game_log = json.load(f)
            else:
                self.game_log = {"games": [], "last_game_number": 0}
        except Exception as e:
            logger.error(f"Error loading game log: {e}")
            self.game_log = {"games": [], "last_game_number": 0}
    
    def _save_game_log(self):
        """Save game log to file"""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.game_log, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving game log: {e}")
    
    def get_player_stats(self, user_id):
        """Get statistics for a player"""
        user_id = str(user_id)
        if user_id not in self.player_stats:
            self.player_stats[user_id] = {
                "games_played": 0,
                "wins": 0,
                "losses": 0
            }
        return self.player_stats[user_id].copy()
    
    def get_next_game_number(self):
        """Get the next game number"""
        self.game_log["last_game_number"] += 1
        self._save_game_log()
        return self.game_log["last_game_number"]
    
    async def update_game_stats(self, game_data, winning_team):
        """Update player statistics after a game"""
        team1_ids = game_data['team1']
        team2_ids = game_data['team2']
        
        # Determine winners and losers
        if winning_team == 1:
            winners = team1_ids
            losers = team2_ids
        else:
            winners = team2_ids
            losers = team1_ids
        
        # Update winner stats
        for user_id in winners:
            user_id = str(user_id)
            stats = self.get_player_stats(user_id)
            stats['games_played'] += 1
            stats['wins'] += 1
            self.player_stats[user_id] = stats
        
        # Update loser stats
        for user_id in losers:
            user_id = str(user_id)
            stats = self.get_player_stats(user_id)
            stats['games_played'] += 1
            stats['losses'] += 1
            self.player_stats[user_id] = stats
        
        self._save_stats()
    
    async def log_game_start(self, guild, game_number, team1, team2):
        """Log when a game starts"""
        log_entry = {
            "game_number": game_number,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "started",
            "team1": [{"id": member.id, "name": member.display_name} for member in team1],
            "team2": [{"id": member.id, "name": member.display_name} for member in team2],
            "winner": None
        }
        
        self.game_log["games"].append(log_entry)
        self._save_game_log()
        
        # Send to log channel if configured
        await self._send_game_log(guild, f"🎮 **Game #{game_number} Started**", log_entry)
    
    async def log_game_end(self, guild, game_data, winner):
        """Log when a game ends"""
        game_number = game_data['game_number']
        
        # Find the game in the log
        for game in self.game_log["games"]:
            if game["game_number"] == game_number:
                game["status"] = "completed" if winner > 0 else "cancelled"
                game["winner"] = winner if winner > 0 else None
                game["end_timestamp"] = datetime.utcnow().isoformat()
                break
        
        self._save_game_log()
        
        # Send to log channel
        if winner == 0:
            message = f"❌ **Game #{game_number} Cancelled**"
        else:
            winning_team = "Team 1" if winner == 1 else "Team 2"
            message = f"🎉 **Game #{game_number} Completed - {winning_team} Wins!**"
        
        # Find the log entry
        log_entry = None
        for game in self.game_log["games"]:
            if game["game_number"] == game_number:
                log_entry = game
                break
        
        await self._send_game_log(guild, message, log_entry)
    
    async def _send_game_log(self, guild, title, log_entry):
        """Send game log to the designated channel"""
        try:
            log_channel = guild.get_channel(Config.LOG_CHANNEL_ID)
            if not log_channel:
                return
            
            embed = discord.Embed(
                title=title,
                color=discord.Color.blue(),
                timestamp=datetime.fromisoformat(log_entry["timestamp"])
            )
            
            team1_names = [player["name"] for player in log_entry["team1"]]
            team2_names = [player["name"] for player in log_entry["team2"]]
            
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
            
            if log_entry.get("winner"):
                winning_team = "Team 1" if log_entry["winner"] == 1 else "Team 2"
                embed.add_field(
                    name="🏆 Winner",
                    value=winning_team,
                    inline=False
                )
            
            await log_channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error sending game log: {e}")
    
    def get_leaderboard(self, limit=10):
        """Get leaderboard sorted by wins"""
        leaderboard = []
        
        for user_id, stats in self.player_stats.items():
            # Skip non-user entries like _comment, _format
            if user_id.startswith('_') or not isinstance(stats, dict):
                continue
            if stats.get('games_played', 0) > 0:
                leaderboard.append((int(user_id), stats))
        
        # Sort by wins, then by win rate
        leaderboard.sort(key=lambda x: (x[1]['wins'], x[1]['wins']/x[1]['games_played']), reverse=True)
        
        return leaderboard[:limit]
    
    async def post_public_leaderboard(self, interaction):
        """Post leaderboard to public channel"""
        leaderboard = self.get_leaderboard()
        
        embed = discord.Embed(
            title="🏆 Current Leaderboard",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )
        
        if not leaderboard:
            embed.description = "No games played yet!"
        else:
            description = ""
            for i, (user_id, stats) in enumerate(leaderboard[:10], 1):
                try:
                    user = interaction.client.get_user(user_id)
                    name = user.display_name if user else f"User {user_id}"
                    win_rate = (stats['wins'] / stats['games_played']) * 100 if stats['games_played'] > 0 else 0
                    description += f"{i}. **{name}** - {stats['wins']}W/{stats['losses']}L ({win_rate:.1f}%)\n"
                except Exception:
                    continue
            embed.description = description
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        # Send to leaderboard channel
        try:
            leaderboard_channel = interaction.guild.get_channel(Config.LEADERBOARD_CHANNEL_ID)
            if leaderboard_channel:
                await leaderboard_channel.send(embed=embed)
                await interaction.response.send_message("✅ Leaderboard posted!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Leaderboard channel not found!", ephemeral=True)
        except Exception as e:
            logger.error(f"Error posting leaderboard: {e}")
            await interaction.response.send_message("❌ Error posting leaderboard!", ephemeral=True)
