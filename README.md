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
# Install dependencies
pip install -r requirements.txt

# Or use the provided script (Linux/Mac)
chmod +x install_dependencies.sh
./install_dependencies.sh
```

**Note**: The bot will work even if `psutil` fails to install - it will use basic session cleanup instead.

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

1. **SQLite Database Lock Error**: 
   - The bot now has multiple fallback strategies
   - If you see "database is locked", the bot will automatically try:
     - Fresh session file
     - In-memory session (no file locking)
   - If the issue persists, check for other bot instances running

2. **Database Connection**: Check MongoDB is running
3. **Missing Files**: Ensure `kanto_data.json` and `moves.json` exist
4. **Environment Variables**: Verify all required variables are set in `.env`
5. **Permissions**: Check file permissions for session files
6. **Network**: Ensure bot can connect to Telegram servers

### Session File Issues
If you continue to have session file problems:
```bash
# Remove all session files manually
rm -f bot.session* bot_session_*

# Or on Windows
del bot.session* bot_session_*
```
