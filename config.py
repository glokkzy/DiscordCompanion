import os

class Config:
    """Configuration class for the Discord bot"""
    
    # Discord IDs - These should be set in your environment or updated here
    GUILD_ID = int(os.getenv("GUILD_ID", "123456789012345678"))  # Your Discord server ID
    
    # Channel IDs
    DRAFTS_CHANNEL_ID = int(os.getenv("DRAFTS_CHANNEL_ID", "123456789012345678"))  # Channel for drafts menu
    FIND_CHANNEL_ID = int(os.getenv("FIND_CHANNEL_ID", "123456789012345678"))  # Channel for find menu
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "123456789012345678"))  # Channel for game logs
    
    # Voice channel category for creating game channels
    VOICE_CATEGORY_ID = int(os.getenv("VOICE_CATEGORY_ID", "123456789012345678"))
    
    # Regional role IDs for matchmaking
    EAST_ROLE_ID = int(os.getenv("EAST_ROLE_ID", "123456789012345678"))
    CENTRAL_ROLE_ID = int(os.getenv("CENTRAL_ROLE_ID", "123456789012345678"))
    WEST_ROLE_ID = int(os.getenv("WEST_ROLE_ID", "123456789012345678"))
    
    # Game settings
    MIN_PLAYERS = int(os.getenv("MIN_PLAYERS", "2"))  # Minimum players for a game
    MAX_PLAYERS = int(os.getenv("MAX_PLAYERS", "10"))  # Maximum players for a game
    
    # File paths
    PLAYER_STATS_FILE = "data/player_stats.json"
    GAME_LOG_FILE = "data/game_log.json"
    
    @classmethod
    def get_regional_roles(cls):
        """Get dictionary of regional roles"""
        return {
            "east": cls.EAST_ROLE_ID,
            "central": cls.CENTRAL_ROLE_ID,
            "west": cls.WEST_ROLE_ID
        }
