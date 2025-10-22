# config.py - Configuration and Environment Variables
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_required_env(key, default=None):
    """Get required environment variable with error handling"""
    value = os.getenv(key, default)
    if value is None:
        print(f"❌ Error: Required environment variable '{key}' is not set!")
        print("Please create a .env file with the following variables:")
        print("API_ID=your_api_id")
        print("API_HASH=your_api_hash")
        print("BOT_TOKEN=your_bot_token")
        print("OWNER_ID=your_owner_id")
        sys.exit(1)
    return value

# Bot Configuration
try:
    API_ID = int(get_required_env('API_ID'))
    API_HASH = get_required_env('API_HASH')
    BOT_TOKEN = get_required_env('BOT_TOKEN')
    OWNER_ID = int(get_required_env('OWNER_ID'))
except ValueError as e:
    print(f"❌ Error: Invalid environment variable format: {e}")
    sys.exit(1)

# Database Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'pokemon_showdown')

# Battle Configuration
POKEMON_PER_PAGE = 15
SHOWDOWN_LINK = "https://play.pokemonshowdown.com/teambuilder"