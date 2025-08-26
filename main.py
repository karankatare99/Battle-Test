import random
import string
from datetime import datetime
from telethon import TelegramClient, events, Button
from pymongo import MongoClient

# ==== Your credentials ====
API_ID = 27715449
API_HASH = "dd3da7c5045f7679ff1f0ed0c82404e0"
BOT_TOKEN = "8474337967:AAH_mbpp4z1nOTDGyoJrM5r0Rii-b_TUcvA"

# ==== Setup Bot ====
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ==== Setup MongoDB (local VPS) ====
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["pokemon_showdown"]
users = db["users"]
auth = db["authorised"]
owner = 6735548827


# ==== Helper: Generate Pokémon ID ====
def generate_pokemon_id():
    date_part = datetime.utcnow().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"PKM-{date_part}-{random_part}"


# ==== Helper: Parse Pokémon Showdown Set ====
def parse_showdown_set(text):
    lines = text.strip().splitlines()
    pokemon = {}

    # --- First line: Name, Gender, Item ---
    first_line = lines[0]

    # Extract gender if present
    gender = None
    if "(M)" in first_line:
        gender = "Male"
        first_line = first_line.replace("(M)", "").strip()
    elif "(F)" in first_line:
        gender = "Female"
        first_line = first_line.replace("(F)", "").strip()
    else:
        # If not specified, assign random gender
        gender = random.choice(["Male", "Female"])

    # Split name + item
    if "@" in first_line:
        name_part, item = first_line.split("@")
        pokemon["name"] = name_part.strip()
        pokemon["item"] = item.strip()
    else:
        pokemon["name"] = first_line.strip()
        pokemon["item"] = "None"

    pokemon["gender"] = gender

    # --- Other attributes ---
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("Ability:"):
            pokemon["ability"] = line.replace("Ability:", "").strip()
        elif line.startswith("Shiny:"):
            pokemon["shiny"] = line.replace("Shiny:", "").strip()
        elif line.startswith("Tera Type:"):
            pokemon["tera_type"] = line.replace("Tera Type:", "").strip()
        elif line.startswith("EVs:"):
            pokemon["evs"] = line.replace("EVs:", "").strip()
        elif line.startswith("IVs:"):
            pokemon["ivs"] = line.replace("IVs:", "").strip()
        elif line.endswith("Nature"):
            pokemon["nature"] = line.replace("Nature", "").strip()
        elif line.startswith("- "):  # Moves
            if "moves" not in pokemon:
                pokemon["moves"] = []
            pokemon["moves"].append(line.replace("- ", "").strip())

    # Add Pokémon ID
    pokemon["pokemon_id"] = generate_pokemon_id()
    return pokemon


# ==== /start command ====
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = event.sender_id
    first_name = event.sender.first_name

    authorised = auth.find_one({"user_id": user_id})
    if not authorised and user_id != owner:
        await event.respond("❌ You are not authorised to use this bot.")
        return

    existing = users.find_one({"user_id": user_id})
    if not existing:
        users.insert_one({
            "user_id": user_id,
            "name": first_name,
            "pokemon": [],
            "team": []
        })
        await event.respond(f"👋 Welcome {first_name}! Your profile has been created.")
    else:
        await event.respond(f"✅ Welcome back {first_name}, you already have a profile.")


# ==== /authorise (reply to user) ====
@bot.on(events.NewMessage(pattern="/authorise"))
async def authorise_handler(event):
    user_id = event.sender_id
    if not event.is_reply:
        await event.respond("⚠️ Please reply to a user's message with /authorise.")
        return

    reply_msg = await event.get_reply_message()
    target_id = reply_msg.sender_id
    target = await bot.get_entity(target_id)

    if user_id != owner:
        await event.reply("❌ You are not the Owner!")
        return

    existing = auth.find_one({"user_id": target_id})
    if existing:
        await event.respond(f"✅ {target.first_name} is already authorised.")
    else:
        auth.insert_one({"user_id": target_id, "name": target.first_name})
        await event.respond(f"🔐 {target.first_name} has been authorised!")


# ==== /authlist command ====
@bot.on(events.NewMessage(pattern="/authlist"))
async def authlist_handler(event):
    authorised_users = list(auth.find())
    if not authorised_users:
        await event.respond("📂 No authorised users yet.")
        return

    msg = "👑 Authorised Users:\n"
    for user in authorised_users:
        msg += f"- {user['name']} ({user['user_id']})\n"
    await event.respond(msg)


# ==== /add Pokémon command ====
SHOWDOWN_LINK = "https://play.pokemonshowdown.com/teambuilder"

@bot.on(events.NewMessage(pattern="/add"))
async def add_pokemon(event):
    await event.respond(
        "Please paste the meta data of your Pokémon!",
        buttons=[[Button.url("⚡ Open Teambuilder", SHOWDOWN_LINK)]]
    )


# ==== Handle pasted Pokémon sets ====
@bot.on(events.NewMessage)
async def handle_pokemon_set(event):
    text = event.raw_text
    if any(keyword in text for keyword in ["Ability:", "EVs:", "Nature", "- "]):
        pokemon = parse_showdown_set(text)

        user_id = event.sender_id

# Construct key like Pikachu_25
        pokemon_key = f"{pokemon.get('name', 'Unknown')}_{pokemon['pokemon_id']}"

# Update or insert the pokemon info under that key
        users.update_one(
    {"user_id": user_id},
    {"$set": {f"pokemon.{pokemon_key}": pokemon}},
    upsert=True
)

        # Response message
        msg = f"✅ Pokémon Saved!\n\n"
        msg += f"🆔 ID: `{pokemon['pokemon_id']}`\n"
        msg += f"📛 Name: {pokemon.get('name', 'Unknown')} ({pokemon['gender']})\n"
        msg += f"🎒 Item: {pokemon.get('item', 'None')}\n"
        msg += f"✨ Shiny: {pokemon.get('shiny', 'No')}\n"
        msg += f"🌩️ Ability: {pokemon.get('ability', 'None')}\n"
        msg += f"🌈 Tera Type: {pokemon.get('tera_type', 'None')}\n"
        msg += f"📊 EVs: {pokemon.get('evs', 'None')}\n"
        msg += f"🔢 IVs: {pokemon.get('ivs', 'None')}\n"
        msg += f"🌿 Nature: {pokemon.get('nature', 'None')}\n"
        msg += f"⚔️ Moves: {', '.join(pokemon.get('moves', []))}"

        await event.respond(msg)


print("Bot running...")
bot.run_until_disconnected()
