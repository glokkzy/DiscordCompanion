# Overview

This is a Discord bot designed for gaming communities to facilitate team drafts, player matchmaking, and game statistics tracking. The bot provides interactive menus for creating balanced teams, finding players by region, and managing voice channels for organized gameplay.

# System Architecture

The application follows a modular architecture with separate managers handling different aspects of the bot's functionality:

- **Main Bot Controller**: Central bot instance that coordinates all managers
- **Manager Pattern**: Each feature area is handled by a dedicated manager class
- **Event-Driven**: Uses Discord.py's event system for real-time interactions
- **File-Based Storage**: JSON files for persistent data storage
- **Configuration Management**: Environment-based configuration with fallback defaults

# Key Components

## Bot Managers
- **MenuManager**: Handles interactive Discord menus for drafts and player finding
- **DraftManager**: Creates balanced teams from voice channel members
- **VoiceManager**: Creates temporary voice channels for team games
- **StatsManager**: Tracks player statistics and game history
- **MatchmakingManager**: Handles regional player notifications

## Data Storage
- **Player Statistics**: JSON file tracking wins/losses per player
- **Game Log**: JSON file with numbered game history and results
- **Configuration**: Environment variables for Discord IDs and game settings

## Discord Integration
- **Slash Commands**: Modern Discord interaction system
- **Voice Channel Management**: Automatic team channel creation
- **Role-Based Regions**: Uses Discord roles for regional matchmaking
- **Embed Messages**: Rich formatted messages for better UX

# Data Flow

1. **Game Creation**: Players join voice channel → Use draft menu → Bot creates balanced teams → Players moved to team channels
2. **Player Finding**: User selects region → Bot finds all users with regional role → Sends DM notifications
3. **Statistics**: Game completion → Winner recorded → Player stats updated → Game logged with number
4. **Menu Interaction**: User clicks button → Bot processes request → Updates UI or performs action

# External Dependencies

- **discord.py**: Primary Discord API wrapper (v2.5.2+)
- **python-dotenv**: Environment variable management
- **Python 3.11**: Runtime environment

## Discord Requirements
- Bot token with appropriate permissions
- Guild (server) access with specific channel and role IDs
- Voice channel management permissions
- Message and embed permissions

# Deployment Strategy

The bot is configured for Replit deployment with:
- **Nix Environment**: Python 3.11 with required packages
- **Automatic Installation**: Dependencies installed on startup
- **Environment Configuration**: Uses .env file for sensitive data
- **Logging**: File and console logging for debugging
- **Process Management**: Single main.py entry point

## Required Setup
1. Create Discord application and bot
2. Copy .env.example to .env and fill in actual IDs
3. Invite bot to server with proper permissions
4. Configure channel and role IDs in environment

# User Preferences

Preferred communication style: Simple, everyday language.

# Changelog

Changelog:
- June 14, 2025. Initial setup