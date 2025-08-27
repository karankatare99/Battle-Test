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

# State tracking so /add expects next msg
awaiting_pokemon = set()

# ==== Helper: Generate Pokémon ID ====
def generate_pokemon_id():
    date_part = datetime.utcnow().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"PKM-{date_part}-{random_part}"

# ==== Helper: Parse EV/IV ====
def parse_stats(ev_str, iv_str):
    # Defaults
    evs = {s: 0 for s in ["hp","atk","def","spa","spd","spe"]}
    ivs = {s: 31 for s in ["hp","atk","def","spa","spd","spe"]}

    if ev_str:
        parts = ev_str.split("/")
        for p in parts:
            p = p.strip()
            if " " in p:
                val, stat = p.split()
                stat = stat.lower()
                if stat == "spa": stat = "spa"
                if stat == "spd": stat = "spd"
                if stat == "spe": stat = "spe"
                val = min(int(val), 252)  # cap at 252
                evs[stat] = val

    if iv_str:
        parts = iv_str.split("/")
        for p in parts:
            p = p.strip()
            if " " in p:
                val, stat = p.split()
                stat = stat.lower()
                if stat == "spa": stat = "spa"
                if stat == "spd": stat = "spd"
                if stat == "spe": stat = "spe"
                ivs[stat] = int(val)

    return evs, ivs

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
        gender = random.choice(["Male","Female"])

    # Split name + item
    if "@" in first_line:
        name_part, item = first_line.split("@")
        pokemon["name"] = name_part.strip()
        pokemon["item"] = item.strip()
    else:
        pokemon["name"] = first_line.strip()
        pokemon["item"] = "None"

    pokemon["gender"] = gender
    pokemon["level"] = 100  # default

    # --- Other attributes ---
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("Ability:"):
            pokemon["ability"] = line.replace("Ability:","").strip()
        elif line.startswith("Shiny:"):
            pokemon["shiny"] = line.replace("Shiny:","").strip()
        elif line.startswith("Tera Type:"):
            pokemon["tera_type"] = line.replace("Tera Type:","").strip()
        elif line.startswith("EVs:"):
            evs_line = line.replace("EVs:", "").strip()
            evs_dict = {s.split()[1].lower(): min(int(s.split()[0]), 252) for s in evs_line.split("/")}
            for stat in ["hp", "atk", "def", "spa", "spd", "spe"]:
                pokemon[f"ev{stat}"] = evs_dict.get(stat, 0)


        elif line.startswith("IVs:"):
            ivs_line = line.replace("IVs:","").strip()
            ivs_dict = {s.split()[1].lower(): int(s.split()[0]) for s in ivs_line.split(",")}
            for stat in ["hp","atk","def","spa","spd","spe"]:
                pokemon[f"iv{stat}"] = ivs_dict.get(stat,31)
        elif line.endswith("Nature"):
            pokemon["nature"] = line.replace("Nature","").strip()
        elif line.startswith("Level:"):
            try:
                pokemon["level"] = int(line.replace("Level:","").strip())
            except:
                pokemon["level"] = 100
        elif line.startswith("- "):
            if "moves" not in pokemon:
                pokemon["moves"] = []
            pokemon["moves"].append(line.replace("- ","").strip())

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
            "pokemon": {},
            "team": []
        })
        await event.respond(f"👋 Welcome {first_name}! Your profile has been created.")
    else:
        await event.respond(f"✅ Welcome back {first_name}, you already have a profile.")

# ==== /reset command ====
@bot.on(events.NewMessage(pattern="/reset"))
async def reset_handler(event):
    user_id = event.sender_id
    users.update_one({"user_id": user_id}, {"$set": {"pokemon": {}, "team": []}})
    await event.respond("🗑️ All your Pokémon data has been reset.")

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
    user_id = event.sender_id
    existing = users.find_one({"user_id": user_id})
    if not existing:
        await event.reply("User profile not found!") 
        return
    awaiting_pokemon.add(user_id)  # mark user as waiting for Pokémon
    await event.respond(
        "Please paste the meta data of your Pokémon (only next message will be taken)!",
        buttons=[[Button.url("⚡ Open Teambuilder", SHOWDOWN_LINK)]]
    )

# ==== Handle pasted Pokémon sets ====
@bot.on(events.NewMessage)
async def handle_pokemon_set(event):
    user_id = event.sender_id
    text = event.raw_text

    if user_id in awaiting_pokemon and any(k in text for k in ["Ability:", "EVs:", "Nature", "- "]):
        pokemon = parse_showdown_set(text)
        pokemon_key = f"{pokemon.get('name','Unknown')}_{pokemon['pokemon_id']}"

        # Save to DB
        users.update_one(
            {"user_id": user_id},
            {"$set": {f"pokemon.{pokemon_key}": pokemon}},
            upsert=True
        )

        awaiting_pokemon.remove(user_id)  # clear waiting state

        # Response
        msg = f"✅ Pokémon Saved!\n\n"
        msg += f"🆔 ID: `{pokemon['pokemon_id']}`\n"
        msg += f"📛 Name: {pokemon['name']} ({pokemon['gender']})\n"
        msg += f"🎒 Item: {pokemon['item']}\n"
        msg += f"🎚️ Level: {pokemon.get('level',100)}\n"
        msg += f"✨ Shiny: {pokemon.get('shiny','No')}\n"
        msg += f"🌩️ Ability: {pokemon.get('ability','None')}\n"
        msg += f"🌈 Tera Type: {pokemon.get('tera_type','None')}\n"
        msg += f"🌿 Nature: {pokemon.get('nature','None')}\n"
        msg += f"⚔️ Moves: {', '.join(pokemon.get('moves', []))}\n\n"
        msg += "📊 EVs: " + ", ".join(
    [f"{k.upper()}={pokemon.get(f'ev{k}',0)}" for k in ['hp','atk','def','spa','spd','spe']]
) + "\n"
        msg += "🔢 IVs: " + ", ".join(
    [f"{k.upper()}={pokemon.get(f'iv{k}',31)}" for k in ['hp','atk','def','spa','spd','spe']]
)

        await event.respond(msg)
# ==== /server_reset (Owner only) ====
@bot.on(events.NewMessage(pattern="/server_reset"))
async def server_reset_handler(event):
    user_id = event.sender_id

    if user_id != owner:  # check if not owner
        await event.respond("❌ You are not authorised to use this command.")
        return

    # delete all users and reset DB
    users.delete_many({})  # wipe user collection
    auth.delete_many({})   # wipe authorised collection if you want

    await event.respond("⚠️ All user data and authorised data have been wiped from the server!")
print("Bot running...")
bot.run_until_disconnected()
