# Pokémon Showdown Telegram Bot

A Telegram bot for managing Pokémon teams and battles.

## Setup Instructions

### 1. Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# Telegram Bot Configuration
# Get these values from https://my.telegram.org/apps
API_ID=your_api_id_here
API_HASH=your_api_hash_here

# Bot Token from @BotFather
BOT_TOKEN=your_bot_token_here

# Owner User ID (your Telegram user ID)
OWNER_ID=your_owner_id_here

# Database Configuration (optional - defaults provided)
MONGO_URI=mongodb://localhost:27017/
DB_NAME=pokemon_showdown
```

### 2. Required Files
Ensure these files are present in the project directory:
- `kanto_data.json` - Pokémon base stats data
- `moves.json` - Move data

### 3. Database Setup
Make sure MongoDB is running and accessible at the configured URI.

### 4. Installation
```bash
pip install -r requirements.txt
```

### 5. Running the Bot
```bash
python bot.py
```

## Features Fixed

✅ **SQLite Database Lock Issues**: Fixed session management and cleanup
✅ **Async Task Cleanup**: Proper shutdown handling with signal handlers
✅ **Error Handling**: Added comprehensive error handling for:
- Database operations
- Environment variables
- JSON file operations
- Network operations
- User input validation

✅ **Production Ready**: Bot now handles errors gracefully and provides user feedback

## Commands

- `/start` - Initialize user profile
- `/add` - Add a new Pokémon
- `/pokemon` - List your Pokémon
- `/summary <name>` - Get detailed Pokémon info
- `/team` - Manage your battle team
- `/reset` - Reset your Pokémon data
- `/authorise` - Authorize users (owner only)
- `/authlist` - List authorized users
- `/serverreset` - Reset all server data (owner only)

## Troubleshooting

If you encounter issues:

1. **Database Connection**: Check MongoDB is running
2. **Missing Files**: Ensure `kanto_data.json` and `moves.json` exist
3. **Environment Variables**: Verify all required variables are set in `.env`
4. **Permissions**: Check file permissions for session files
5. **Network**: Ensure bot can connect to Telegram servers
