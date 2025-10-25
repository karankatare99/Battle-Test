# config.py - Configuration and Environment Variables
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
OWNER_ID = int(os.getenv('OWNER_ID'))

# Database Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.getenv('DB_NAME', 'pokemon_showdown')

# Battle Configuration
POKEMON_PER_PAGE = 15
SHOWDOWN_LINK = "https://play.pokemonshowdown.com/teambuilder"