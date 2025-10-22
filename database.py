# database.py - Database connection and models
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import MONGO_URI, DB_NAME
import sys

def connect_to_database():
    """Connect to MongoDB with error handling"""
    try:
        # Test connection with timeout
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        # Test the connection
        mongo_client.admin.command('ping')
        print("✅ Connected to MongoDB successfully!")
        return mongo_client
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        print(f"❌ Error: Could not connect to MongoDB: {e}")
        print("Please check your MongoDB connection settings.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error connecting to MongoDB: {e}")
        sys.exit(1)

# MongoDB connection
mongo_client = connect_to_database()
db = mongo_client[DB_NAME]

# Collections
users = db["users"]
auth = db["authorised"]
pokedata = db["pokemon_data"]
battles_db = db["battles"]
matchmaking = db["matchmaking"]