# database.py - Database connection and models
from pymongo import MongoClient
from config import MONGO_URI, DB_NAME

# MongoDB connection
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]

# Collections
users = db["users"]
auth = db["authorised"]
pokedata = db["pokemon_data"]
battles_db = db["battles"]
matchmaking = db["matchmaking"]