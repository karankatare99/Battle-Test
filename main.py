import random, json, math
import string
import asyncio
from datetime import datetime
from collections import Counter

from telethon import TelegramClient, events, Button
from pymongo import MongoClient
from bson import ObjectId

# ==== Your credentials (rotate before public deploy) ====
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
pokedata = db["pokemon_data"]

# Battle collections
battles = db["battles"]
matchmaking = db["matchmaking"]

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
                val = min(int(val), 252)
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

    evs = {s: 0 for s in ["hp","atk","def","spa","spd","spe"]}
    ivs = {s: 31 for s in ["hp","atk","def","spa","spd","spe"]}

    first_line = lines[0]
    if "(M)" in first_line:
        gender = "Male"; first_line = first_line.replace("(M)", "").strip()
    elif "(F)" in first_line:
        gender = "Female"; first_line = first_line.replace("(F)", "").strip()
    else:
        gender = random.choice(["Male","Female"])

    if "@" in first_line:
        name_part, item = first_line.split("@")
        pokemon["name"] = name_part.strip()
        pokemon["item"] = item.strip()
    else:
        pokemon["name"] = first_line.strip()
        pokemon["item"] = "None"

    pokemon["gender"] = gender
    pokemon["level"] = 100
    pokemon["nature"] = "None"
    pokemon["shiny"] = "No"
    pokemon["moves"] = []

    for line in lines[1:]:
        line = line.strip()
        if line.startswith("Ability:"):
            pokemon["ability"] = line.replace("Ability:", "").strip()
        elif line.startswith("Shiny:"):
            pokemon["shiny"] = line.replace("Shiny:", "").strip()
        elif line.startswith("Tera Type:"):
            pokemon["tera_type"] = line.replace("Tera Type:", "").strip()
        elif line.startswith("Level:"):
            try:
                pokemon["level"] = int(line.replace("Level:", "").strip())
            except:
                pokemon["level"] = 100
        elif line.startswith("Nature"):
            pokemon["nature"] = line.replace("Nature", "").strip()
        elif line.startswith("EVs:"):
            ev_line = line.replace("EVs:", "").strip()
            evs_parsed, _ = parse_stats(ev_line, None)
            evs.update(evs_parsed)
        elif line.startswith("IVs:"):
            iv_line = line.replace("IVs:", "").strip()
            _, ivs_parsed = parse_stats(None, iv_line)
            ivs.update(ivs_parsed)
        elif line.startswith("- "):
            pokemon["moves"].append(line.replace("- ", "").strip())
    
    for stat in ["hp","atk","def","spa","spd","spe"]:
        pokemon[f"ev{stat}"] = evs[stat]
        pokemon[f"iv{stat}"] = ivs[stat]
    print(pokemon)
    add_final_stats(pokemon) 
    pokemon["pokemon_id"] = generate_pokemon_id()
     
    return pokemon


with open("kanto_data.json", "r") as f:
    kanto_data = json.load(f)

nature_chart = {
    "Adamant": {"atk": 1.1, "spa": 0.9},
    "Lonely": {"atk": 1.1, "def": 0.9},
    "Brave": {"atk": 1.1, "spe": 0.9},
    "Naughty": {"atk": 1.1, "spd": 0.9},
    "Bold": {"def": 1.1, "atk": 0.9},
    "Impish": {"def": 1.1, "spa": 0.9},
    "Relaxed": {"def": 1.1, "spe": 0.9},
    "Lax": {"def": 1.1, "spd": 0.9},
    "Modest": {"spa": 1.1, "atk": 0.9},
    "Mild": {"spa": 1.1, "def": 0.9},
    "Quiet": {"spa": 1.1, "spe": 0.9},
    "Rash": {"spa": 1.1, "spd": 0.9},
    "Calm": {"spd": 1.1, "atk": 0.9},
    "Gentle": {"spd": 1.1, "def": 0.9},
    "Sassy": {"spd": 1.1, "spe": 0.9},
    "Careful": {"spd": 1.1, "spa": 0.9},
    "Timid": {"spe": 1.1, "atk": 0.9},
    "Hasty": {"spe": 1.1, "def": 0.9},
    "Jolly": {"spe": 1.1, "spa": 0.9},
    "Naive": {"spe": 1.1, "spd": 0.9},
}

def calculate_stat(base, iv, ev, level, nature, stat):
    if stat == "hp":
        if base == 1:  # Shedinja case
            return 1
        return math.floor(((2 * base + iv + ev // 4) * level) / 100) + level + 10
    else:
        stat_val = math.floor(((2 * base + iv + ev // 4) * level) / 100) + 5
        if nature in nature_chart:
            if stat in nature_chart[nature]:
                stat_val = math.floor(stat_val * nature_chart[nature][stat])
        return stat_val

def add_final_stats(pokemon):
    name = pokemon["name"] 
    level = pokemon["name"] 
    base_stats = kanto_data[name]["Base_Stats"]
    hp = base_stats["Hp"]
    atk = base_stats["Attack"]
    defense = base_stats["Defense"]
    spa = base_stats["Sp.Attack"]
    spd = base_stats["Sp.Defense"]
    spe = base_stats["Speed"]
    level = level
    nature = nature

    final_stats = {}
    final_stats["hp"] = calculate_stat(hp, pokemon["ivhp"] , pokemon["evhp"], level, nature, "hp")
    final_stats["atk"] = calculate_stat(atk, pokemon["ivatk"], pokemon["evatk"], level, nature, "atk")
    final_stats["def"] = calculate_stat(defense, pokemon["ivdef"], pokemon["evdef"], level, nature, "def")
    final_stats["spa"] = calculate_stat(spa, pokemon["ivspa"], pokemon["evspa"], level, nature, "spa")
    final_stats["spd"] = calculate_stat(spd, pokemon["ivspd"], pokemon["evspd"], level, nature, "spd")
    final_stats["spe"] = calculate_stat(spe, pokemon["ivspe"], pokemon["evspe"], level, nature, "spe")

    pokemon.update(final_stats)
    return pokemon
# ==== /start ====
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
        users.insert_one({"user_id": user_id, "name": first_name, "pokemon": [], "team": []})
        await event.respond(f"👋 Welcome {first_name}! Your profile has been created.")
    else:
        await event.respond(f"✅ Welcome back {first_name}, you already have a profile.")

# ==== /reset ====
@bot.on(events.NewMessage(pattern="/reset"))
async def reset_handler(event):
    user_id = event.sender_id
    users.update_one({"user_id": user_id}, {"$set": {"pokemon": [], "team": []}})
    await event.respond("🗑️ All your Pokémon data has been reset.")

# ==== /authorise ====
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

# ==== /authlist ====
@bot.on(events.NewMessage(pattern="/authlist"))
async def authlist_handler(event):
    authorised_users = list(auth.find())
    if not authorised_users:
        await event.respond("📂 No authorised users yet.")
        return
    msg = "👑 Authorised Users:\n"
    for u in authorised_users:
        msg += f"- {u['name']} ({u['user_id']})\n"
    await event.respond(msg)

# ==== /add ====
SHOWDOWN_LINK = "https://play.pokemonshowdown.com/teambuilder"

@bot.on(events.NewMessage(pattern="/add"))
async def add_pokemon(event):
    user_id = event.sender_id
    existing = users.find_one({"user_id": user_id})
    if not existing:
        await event.reply("User profile not found!")
        return
    awaiting_pokemon.add(user_id)
    await event.respond(
        "Please paste the meta data of your Pokémon (only next message will be taken)!",
        buttons=[[Button.url("⚡ Open Teambuilder", SHOWDOWN_LINK)]]
    )

# Handle pasted set
@bot.on(events.NewMessage)
async def handle_pokemon_set(event):
    user_id = event.sender_id
    text = event.raw_text
    if user_id in awaiting_pokemon and any(k in text for k in ["Ability:", "EVs:", "Nature", "- "]):
        pokemon = parse_showdown_set(text)
        pokemon_key = f"{pokemon.get('name','Unknown')}_{pokemon['pokemon_id']}"
        users.update_one({"user_id": user_id}, {"$push": {"pokemon": pokemon_key}}, upsert=True)
        pokedata.update_one({"_id": pokemon_key}, {"$set": pokemon}, upsert=True)
        awaiting_pokemon.remove(user_id)
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
        msg += "📊 EVs: " + ", ".join([f"{k.upper()}={pokemon.get(f'ev{k}',0)}" for k in ['hp','atk','def','spa','spd','spe']]) + "\n"
        msg += "🔢 IVs: " + ", ".join([f"{k.upper()}={pokemon.get(f'iv{k}',31)}" for k in ['hp','atk','def','spa','spd','spe']])
        await event.respond(msg)

# ==== /server_reset (Owner only) ====
@bot.on(events.NewMessage(pattern="/server_reset"))
async def server_reset_handler(event):
    user_id = event.sender_id
    if user_id != owner:
        await event.respond("❌ You are not authorised to use this command.")
        return
    users.delete_many({})
    auth.delete_many({})
    pokedata.delete_many({})
    battles.delete_many({})
    matchmaking.delete_many({})
    await event.respond("⚠️ All data wiped from the server!")

# ==== /pokemon ====
@bot.on(events.NewMessage(pattern="/pokemon"))
async def pokemon_list_handler(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("pokemon"):
        await event.respond("❌ You don’t have any Pokémon yet.")
        return
    pokemon_ids = user["pokemon"]
    pokes = pokedata.find({"_id": {"$in": pokemon_ids}})
    names = [poke["name"] for poke in pokes]
    counts = Counter(names)
    await send_pokemon_page(event, counts, 0)

async def send_pokemon_page(event, counts, page):
    per_page = 25
    poke_list = [f"{name} ({count})" if count > 1 else name for name, count in counts.items()]
    total_pages = (len(poke_list) - 1) // per_page + 1
    start = page * per_page
    end = start + per_page
    page_items = poke_list[start:end]
    text = f"📜 Your Pokémon (Page {page+1}/{total_pages})\n\n"
    text += "\n".join(page_items) if page_items else "No Pokémon on this page."
    buttons = []
    if page > 0:
        buttons.append(Button.inline("⬅️ Prev", data=f"pokemon:{page-1}"))
    if page < total_pages - 1:
        buttons.append(Button.inline("➡️ Next", data=f"pokemon:{page+1}"))
    await event.respond(text, buttons=[buttons] if buttons else None)

@bot.on(events.CallbackQuery(pattern=b"pokemon:(\d+)"))
async def callback_pokemon_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("pokemon"):
        await event.answer("❌ No Pokémon found.", alert=True)
        return
    pokemon_ids = user["pokemon"]
    pokes = pokedata.find({"_id": {"$in": pokemon_ids}})
    names = [poke["name"] for poke in pokes]
    counts = Counter(names)
    await event.edit("Loading...", buttons=None)
    await send_pokemon_page(event, counts, page)

POKEMON_PER_PAGE = 15

# ==== /team ====
@bot.on(events.NewMessage(pattern="/team"))
async def team_handler(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    if not user:
        await event.respond("❌ No profile found. Use /start first.")
        return
    team = user.get("team", [])
    if not team:
        text = "⚠️ Your team is empty!\n\nUse ➕ Add to select Pokémon from your profile."
        buttons = [[Button.inline("➕ Add", b"team:addpage:0")]]
        await event.respond(text, buttons=buttons)
        return
    await send_team_page(event, user)

async def send_team_page(event, user):
    team_ids = user.get("team", [])
    pokes = list(pokedata.find({"_id": {"$in": team_ids}}))
    poke_map = {p["_id"]: p for p in pokes}
    text = "⚔️ Your Team:\n\n"
    for i, poke_id in enumerate(team_ids, 1):
        poke = poke_map.get(poke_id)
        if poke:
            text += f"{i}. {poke['name']} (ID: {poke['_id']})\n"
        else:
            text += f"{i}. ❓ Unknown Pokémon ({poke_id})\n"
    buttons = [
        [Button.inline("➕ Add", b"team:addpage:0"), Button.inline("➖ Remove", b"team:remove")],
        [Button.inline("🔄 Switch", b"team:switch")]
    ]
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

async def send_add_page(event, user, page=0):
    team_ids = user.get("team", [])
    owned_ids = user.get("pokemon", [])
    available_ids = [pid for pid in owned_ids if pid not in team_ids]
    if not available_ids:
        await event.answer("❌ No more Pokémon left in your profile to add.", alert=True)
        return
    total_pages = (len(available_ids) - 1) // POKEMON_PER_PAGE + 1
    start = page * POKEMON_PER_PAGE
    end = start + POKEMON_PER_PAGE
    page_items = available_ids[start:end]
    pokes = list(pokedata.find({"_id": {"$in": page_items}}))
    poke_map = {p["_id"]: p for p in pokes}
    text = f"➕ Select a Pokémon to Add (Page {page+1}/{total_pages})\n\n"
    for i, pid in enumerate(page_items, start=1):
        poke = poke_map.get(pid)
        if poke:
            text += f"{i}. {poke['name']} (ID: {poke['_id']})\n"
        else:
            text += f"{i}. ❓ Unknown ({pid})\n"
    buttons = []
    row = []
    for i, pid in enumerate(page_items, start=start):
        row.append(Button.inline(str((i % POKEMON_PER_PAGE) + 1), f"team:add:{pid}".encode()))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    nav = []
    if page > 0: nav.append(Button.inline("⬅️ Prev", f"team:addpage:{page-1}".encode()))
    if page < total_pages - 1: nav.append(Button.inline("➡️ Next", f"team:addpage:{page+1}".encode()))
    if nav: buttons.append(nav)
    buttons.append([Button.inline("⬅️ Back", b"team:back")])
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"team:addpage:(\d+)"))
async def team_add_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_add_page(event, user, page)

@bot.on(events.CallbackQuery(pattern=b"team:add:(.+)"))
async def confirm_add(event):
    poke_id = event.pattern_match.group(1).decode()
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])
    if len(team) >= 6:
        await event.answer("⚠️ Team is already full (6 Pokémon max)!", alert=True)
        return
    owned_ids = user.get("pokemon", [])
    if poke_id not in owned_ids:
        await event.answer("❌ You don’t own this Pokémon.", alert=True)
        return
    if poke_id not in team:
        users.update_one({"user_id": user_id}, {"$push": {"team": poke_id}})
        await event.answer("✅ Pokémon added to team!")
    else:
        await event.answer("⚠️ That Pokémon is already in your team.", alert=True)
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)

@bot.on(events.CallbackQuery(pattern=b"team:back"))
async def back_to_team(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)

async def send_remove_page(event, user, page=0):
    team = user.get("team", [])
    if not team:
        await event.answer("⚠️ Your team is empty!", alert=True)
        return
    total_pages = (len(team) - 1) // POKEMON_PER_PAGE + 1
    start = page * POKEMON_PER_PAGE
    end = start + POKEMON_PER_PAGE
    page_items = team[start:end]
    text = f"➖ Select a Pokémon to Remove (Page {page+1}/{total_pages})\n\n"
    for i, poke_id in enumerate(page_items, start=1):
        poke = pokedata.find_one({"_id": poke_id}) or {}
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"
    buttons = []
    row = []
    for i, poke_id in enumerate(page_items, start=start):
        row.append(Button.inline(str((i % POKEMON_PER_PAGE) + 1), f"team:remove:{poke_id}".encode()))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row: buttons.append(row)
    nav = []
    if page > 0: nav.append(Button.inline("⬅️ Prev", f"team:removepage:{page-1}".encode()))
    if page < total_pages - 1: nav.append(Button.inline("➡️ Next", f"team:removepage:{page+1}".encode()))
    if nav: buttons.append(nav)
    buttons.append([Button.inline("⬅️ Back", b"team:back")])
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"team:remove$"))
async def team_remove_menu(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_remove_page(event, user, 0)

@bot.on(events.CallbackQuery(pattern=b"team:removepage:(\d+)"))
async def team_remove_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_remove_page(event, user, page)

@bot.on(events.CallbackQuery(pattern=b"team:remove:(.+)"))
async def confirm_remove(event):
    poke_key = event.pattern_match.group(1).decode()
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])
    if poke_key in team:
        users.update_one({"user_id": user_id}, {"$pull": {"team": poke_key}})
        await event.answer("🗑 Pokémon removed from team!")
    else:
        await event.answer("⚠️ That Pokémon is not in your team.", alert=True)
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)

@bot.on(events.CallbackQuery(pattern=b"team:switch$"))
async def team_switch_start(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])
    if len(team) < 2:
        await event.answer("⚠️ You need at least 2 Pokémon in your team to switch.", alert=True)
        return
    text = "🔄 Select the first Pokémon to switch:\n\n"
    for i, key in enumerate(team, start=1):
        poke = pokedata.find_one({"_id": key}) or {}
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"
    buttons = []
    row = []
    for i, key in enumerate(team, start=1):
        row.append(Button.inline(str(i), f"team:switch1:{i-1}".encode()))
        if len(row) == 5:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([Button.inline("⬅️ Back", b"team:back")])
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"team:switch1:(\d+)"))
async def team_switch_pick_second(event):
    first_index = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])
    first_poke = pokedata.find_one({"_id": team[first_index]}) or {}
    first_name = first_poke.get("name", "Unknown")
    text = f"🔄 Select the second Pokémon to swap with (first chosen: {first_name})\n\n"
    for i, key in enumerate(team, start=1):
        poke = pokedata.find_one({"_id": key}) or {}
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"
    buttons = []
    row = []
    for i in range(len(team)):
        if i == first_index: continue
        row.append(Button.inline(str(i+1), f"team:switch2:{first_index}:{i}".encode()))
        if len(row) == 5:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([Button.inline("⬅️ Back", b"team:back")])
    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"team:switch2:(\d+):(\d+)"))
async def confirm_switch(event):
    first_index = int(event.pattern_match.group(1))
    second_index = int(event.pattern_match.group(2))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])
    if first_index >= len(team) or second_index >= len(team):
        await event.answer("⚠️ Invalid Pokémon selection.", alert=True)
        return
    team[first_index], team[second_index] = team[second_index], team[first_index]
    users.update_one({"user_id": user_id}, {"$set": {"team": team}})
    await event.answer("✅ Pokémon switched!")
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)

# ==== /summary ====
active_summaries = {}

@bot.on(events.NewMessage(pattern=r"^/summary (.+)"))
async def summary_handler(event):
    query = event.pattern_match.group(1).strip().lower()
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    if not user or "pokemon" not in user or not user["pokemon"]:
        await event.reply("❌ You don’t have any Pokémon.")
        return
    matches = []
    for poke_id in user["pokemon"]:
        poke = pokedata.find_one({"_id": poke_id}) or {}
        if not poke: continue
        name_lower = poke.get("name","").lower()
        poke_id_lower = poke.get("pokemon_id","").lower()
        if query == name_lower or query == poke_id_lower or query in name_lower:
            matches.append((poke_id, poke))
    if not matches:
        await event.reply("❌ No Pokémon found.")
        return
    active_summaries[user_id] = matches
    if len(matches) == 1:
        await send_summary(event, matches[0][1])
    else:
        await send_summary_list(event, matches, 0)

async def send_summary_list(event, matches, page=0):
    total_pages = (len(matches) - 1) // POKEMON_PER_PAGE + 1
    start = page * POKEMON_PER_PAGE
    end = start + POKEMON_PER_PAGE
    page_items = matches[start:end]
    text = f"⚠️ Multiple Pokémon found (Page {page+1}/{total_pages}):\n\n"
    for i, (_, poke) in enumerate(page_items, start=1):
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"
    buttons = []
    row = []
    for i, (poke_id, poke) in enumerate(page_items, start=start):
        row.append(Button.inline(str((i % POKEMON_PER_PAGE) + 1), f"summary:show:{poke_id}".encode()))
        if len(row) == 5:
            buttons.append(row); row = []
    if row: buttons.append(row)
    nav = []
    if page > 0: nav.append(Button.inline("⬅️ Prev", f"summary:page:{page-1}".encode()))
    if page < total_pages - 1: nav.append(Button.inline("➡️ Next", f"summary:page:{page+1}".encode()))
    if nav: buttons.append(nav)
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.reply(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"summary:page:(\d+)"))
async def summary_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    matches = active_summaries.get(user_id)
    if not matches:
        await event.answer("❌ No active summary search.", alert=True)
        return
    await send_summary_list(event, matches, page)

@bot.on(events.CallbackQuery(pattern=b"summary:show:(.+)"))
async def summary_show(event):
    poke_id = event.pattern_match.group(1).decode()
    poke = pokedata.find_one({"_id": poke_id})
    if not poke:
        await event.answer("❌ Pokémon not found.", alert=True)
        return
    await send_summary(event, poke)

async def send_summary(event, poke):
    text = (
        f"📜 Pokémon Summary\n\n"
        f"🆔 `{poke.get('pokemon_id','?')}`\n"
        f"✨ Name: {poke.get('name','Unknown')}\n"
        f"♀️ Gender: {poke.get('gender','?')}\n"
        f"⭐ Level: {poke.get('level','?')}\n"
        f"💠 Ability: {poke.get('ability','None')}\n"
        f"🔮 Tera Type: {poke.get('tera_type','None')}\n"
        f"🎒 Item: {poke.get('item','None')}\n\n"
        f"📊 EVs:\n"
        f"HP: {poke.get('evhp',0)} | Atk: {poke.get('evatk',0)} | Def: {poke.get('evdef',0)}\n"
        f"SpA: {poke.get('evspa',0)} | SpD: {poke.get('evspd',0)} | Spe: {poke.get('evspe',0)}\n\n"
        f"🧬 IVs:\n"
        f"HP: {poke.get('ivhp',31)} | Atk: {poke.get('ivatk',31)} | Def: {poke.get('ivdef',31)}\n"
        f"SpA: {poke.get('ivspa',31)} | SpD: {poke.get('ivspd',31)} | Spe: {poke.get('ivspe',31)}\n\n"
        f"⚔️ Moves: {', '.join(poke.get('moves', [])) if poke.get('moves') else 'None'}"
    )
    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text)
    else:
        await event.reply(text)

# =========================
# ===== BATTLE: MVP =======
# =========================

def is_private_chat(event):
    return getattr(event, "is_private", False)

def now_utc():
    return datetime.utcnow()

def seconds_between(a, b):
    return int((b - a).total_seconds())

def est_wait_time(queue_len):
    return 30 if queue_len >= 1 else 60

def team_has_six(user_doc):
    return len(user_doc.get("team", [])) >= 6

def render_queue_text(start_ts, qlen, mode_str):
    elapsed = seconds_between(start_ts, now_utc())
    eta = est_wait_time(qlen)
    mm_e, ss_e = divmod(elapsed, 60)
    mm_eta, ss_eta = divmod(eta, 60)
    return (
        f"🔎 Finding a {mode_str} match…\n"
        f"⏳ Estimated wait: {mm_eta:02d}:{ss_eta:02d}\n"
        f"🕒 Time elapsed: {mm_e:02d}:{ss_e:02d}\n\n"
        f"Tap Cancel to leave the queue."
    )

def render_team_preview(user_doc, pick_count):
    team_ids = user_doc.get("team", [])
    if not team_ids:
        return "❌ No team found."
    pokes = list(pokedata.find({"_id": {"$in": team_ids}}))
    pmap = {p["_id"]: p for p in pokes}
    lines = ["👥 Team Preview", f"Pick {pick_count} Pokémon:"]
    for i, pid in enumerate(team_ids, 1):
        nm = pmap.get(pid, {}).get("name", "Unknown")
        lines.append(f"{i}. {nm} ({pid})")
    return "\n".join(lines)

def render_opponent_team(user_doc):
    team_ids = user_doc.get("team", [])
    if not team_ids:
        return "❌ Opponent has no team."
    pokes = list(pokedata.find({"_id": {"$in": team_ids}}))
    pmap = {p["_id"]: p for p in pokes}
    lines = ["👀 Opponent Team (6 shown)", "You can’t see which 3/4 they’ll bring."]
    for i, pid in enumerate(team_ids, 1):
        nm = pmap.get(pid, {}).get("name", "Unknown")
        lines.append(f"{i}. {nm} ({pid})")
    return "\n".join(lines)

def leave_queue(user_id):
    matchmaking.delete_many({"user_id": user_id})

def preview_buttons(user_doc, pick, battle_id, side):
    team_ids = user_doc.get("team", [])
    buttons = []
    row = []
    for idx, pid in enumerate(team_ids):
        lab = str(idx+1)
        row.append(Button.inline(lab, f"battle:teampick:{battle_id}:{side}:{idx}".encode()))
        if len(row) == 5:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([Button.inline(f"✅ Lock ({pick} required)", f"battle:lock:{battle_id}:{side}".encode())])
    return buttons

# /battle entry (PM-only)
@bot.on(events.NewMessage(pattern=r"^/battle$"))
async def battle_entry(event):
    if not is_private_chat(event):
        await event.respond("⚠️ Please use /battle in a private chat (PM).")
        return
    buttons = [
        [Button.inline("🏆 Ranked", b"battle:ranked")],
        [Button.inline("🎮 Casual", b"battle:casual")]
    ]
    await event.respond("Choose a battle mode:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"battle:ranked"))
async def battle_ranked(event):
    await event.answer("⚠️ Ranked is still in development.", alert=True)

@bot.on(events.CallbackQuery(pattern=b"battle:casual"))
async def battle_casual(event):
    buttons = [
        [Button.inline("⚔️ Single (3v3 from 6)", b"battle:queue:single")],
        [Button.inline("🛡️ Double (4v4 from 6)", b"battle:queue:double")]
    ]
    await event.edit("Select a format:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"battle:queue:(single|double)"))
async def battle_queue(event):
    fmt = event.pattern_match.group(1).decode()
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    if not user:
        await event.answer("❌ No profile found. Use /start first.", alert=True); return
    if not team_has_six(user):
        await event.answer("❌ A full team of 6 is required.", alert=True); return

    leave_queue(user_id)
    start_ts = now_utc()
    matchmaking.insert_one({"user_id": user_id, "format": fmt, "status": "searching", "started_at": start_ts})
    mode_str = "Singles (3/6)" if fmt == "single" else "Doubles (4/6)"
    qcount = matchmaking.count_documents({"format": fmt, "status": "searching"})
    msg = await event.edit(
        render_queue_text(start_ts, qcount, mode_str),
        buttons=[[Button.inline("❌ Cancel", b"battle:cancelq")]]
    )

    opp = matchmaking.find_one({"format": fmt, "status": "searching", "user_id": {"$ne": user_id}})
    if opp:
        await pair_and_start_preview(fmt, user_id, opp["user_id"], msg); return

    timeout = 10 * 60
    interval = 10
    elapsed = 0
    while elapsed < timeout:
        await asyncio.sleep(interval)
        elapsed += interval
        me = matchmaking.find_one({"user_id": user_id, "format": fmt, "status": "searching"})
        if not me:
            try: await msg.edit("❌ You left the queue.")
            except: pass
            return
        opp = matchmaking.find_one({"format": fmt, "status": "searching", "user_id": {"$ne": user_id}})
        if opp:
            await pair_and_start_preview(fmt, user_id, opp["user_id"], msg); return
        try:
            qcount = matchmaking.count_documents({"format": fmt, "status": "searching"})
            await msg.edit(
                render_queue_text(start_ts, qcount, mode_str),
                buttons=[[Button.inline("❌ Cancel", b"battle:cancelq")]]
            )
        except:
            pass

    leave_queue(user_id)
    try: await msg.edit("⌛ No opponent found within 10 minutes. Queue cancelled.")
    except: pass

@bot.on(events.CallbackQuery(pattern=b"battle:cancelq"))
async def cancel_queue(event):
    user_id = event.sender_id
    leave_queue(user_id)
    await event.edit("❌ Queue cancelled.", buttons=None)

async def pair_and_start_preview(fmt, p1_id, p2_id, queue_msg):
    leave_queue(p1_id); leave_queue(p2_id)
    pick = 3 if fmt == "single" else 4
    battle = {
        "format": fmt,
        "status": "preview",
        "p1_id": p1_id,
        "p2_id": p2_id,
        "pick_count": pick,
        "created_at": now_utc(),
        "preview_started_at": now_utc(),
        "p1_selected": [],
        "p2_selected": [],
        "p1_locked": False,
        "p2_locked": False,
        "timer_secs": 90
    }
    res = battles.insert_one(battle)
    battle_id = str(res.inserted_id)
    try: await queue_msg.edit("✅ Opponent found! Opening Team Preview…")
    except: pass

    p1 = users.find_one({"user_id": p1_id}) or {}
    p2 = users.find_one({"user_id": p2_id}) or {}
    p1_text_self = render_team_preview(p1, pick) + f"\n\n⏱ 90s to choose.\nBattle ID: {battle_id}"
    p2_text_self = render_team_preview(p2, pick) + f"\n\n⏱ 90s to choose.\nBattle ID: {battle_id}"
    p1_text_opp = render_opponent_team(p2)
    p2_text_opp = render_opponent_team(p1)
    btns1 = preview_buttons(p1, pick, battle_id, side="p1")
    btns2 = preview_buttons(p2, pick, battle_id, side="p2")

    await bot.send_message(p1_id, p1_text_opp)
    await bot.send_message(p1_id, p1_text_self, buttons=btns1)
    await bot.send_message(p2_id, p2_text_opp)
    await bot.send_message(p2_id, p2_text_self, buttons=btns2)

    asyncio.create_task(preview_timer_task(battle_id))

@bot.on(events.CallbackQuery(pattern=b"battle:teampick:([0-9a-fA-F]+):([a-z0-9]+):(\d+)"))
async def team_pick_toggle(event):
    battle_id = event.pattern_match.group(1).decode()
    side = event.pattern_match.group(2).decode()
    idx = int(event.pattern_match.group(3).decode())
    user_id = event.sender_id

    battle = battles.find_one({"_id": ObjectId(battle_id)})
    if not battle or battle.get("status") != "preview":
        await event.answer("❌ Preview not active.", alert=True); return
    if (side == "p1" and battle.get("p1_id") != user_id) or (side == "p2" and battle.get("p2_id") != user_id):
        await event.answer("❌ Not your preview.", alert=True); return

    pick = battle.get("pick_count", 3 if battle.get("format") == "single" else 4)
    user = users.find_one({"user_id": user_id}) or {}
    team_ids = user.get("team", [])
    if idx < 0 or idx >= len(team_ids):
        await event.answer("❌ Invalid slot.", alert=True); return
    pid = team_ids[idx]

    sel_key = "p1_selected" if side == "p1" else "p2_selected"
    selected = list(battle.get(sel_key, []))
    if pid in selected:
        selected.remove(pid)
    else:
        if len(selected) >= pick:
            await event.answer(f"⚠️ You can only pick {pick}.", alert=True); return
        selected.append(pid)  # preserve order

    battles.update_one({"_id": battle["_id"]}, {"$set": {sel_key: selected}})

    text = render_team_preview(user, pick) + f"\n\nSelected: {len(selected)}/{pick}"
    btns = preview_buttons(user, pick, str(battle["_id"]), side)
    try: await event.edit(text, buttons=btns)
    except: pass

@bot.on(events.CallbackQuery(pattern=b"battle:lock:([0-9a-fA-F]+):([a-z0-9]+)"))
async def team_lock(event):
    battle_id = event.pattern_match.group(1).decode()
    side = event.pattern_match.group(2).decode()
    user_id = event.sender_id

    battle = battles.find_one({"_id": ObjectId(battle_id)})
    if not battle or battle.get("status") != "preview":
        await event.answer("❌ Preview not active.", alert=True); return
    if (side == "p1" and battle.get("p1_id") != user_id) or (side == "p2" and battle.get("p2_id") != user_id):
        await event.answer("❌ Not your preview.", alert=True); return

    pick = battle.get("pick_count", 3 if battle.get("format") == "single" else 4)
    sel_key = "p1_selected" if side == "p1" else "p2_selected"
    lock_key = "p1_locked" if side == "p1" else "p2_locked"
    selected = battle.get(sel_key, [])
    if len(selected) != pick:
        await event.answer(f"⚠️ Select exactly {pick} Pokémon before locking.", alert=True); return

    battles.update_one({"_id": battle["_id"]}, {"$set": {lock_key: True}})
    await event.answer("✅ Locked!", alert=False)

    battle = battles.find_one({"_id": battle["_id"]})
    if battle.get("p1_locked") and battle.get("p2_locked"):
        await start_battle_ready(battle)

async def preview_timer_task(battle_id):
    tick = 5
    total = 90
    elapsed = 0
    while elapsed < total:
        await asyncio.sleep(tick)
        elapsed += tick
        battle = battles.find_one({"_id": ObjectId(battle_id)})
        if not battle or battle.get("status") != "preview":
            return
        if battle.get("p1_locked") and battle.get("p2_locked"):
            await start_battle_ready(battle)
            return

    battle = battles.find_one({"_id": ObjectId(battle_id)})
    if not battle or battle.get("status") != "preview":
        return
    pick = battle.get("pick_count", 3 if battle.get("format") == "single" else 4)
    p1_ok = len(battle.get("p1_selected", [])) == pick
    p2_ok = len(battle.get("p2_selected", [])) == pick
    if p1_ok and p2_ok:
        battles.update_one({"_id": battle["_id"]}, {"$set": {"p1_locked": True, "p2_locked": True}})
        await start_battle_ready(battle)
    else:
        battles.update_one({"_id": battle["_id"]}, {"$set": {"status": "cancelled"}})
        try: await bot.send_message(battle["p1_id"], "⏰ Team preview expired, match cancelled.")
        except: pass
        try: await bot.send_message(battle["p2_id"], "⏰ Team preview expired, match cancelled.")
        except: pass

# Lead order equals pick order
def build_battle_sides_from_picks(battle):
    fmt = battle.get("format", "single")
    p1_sel = battle.get("p1_selected", [])
    p2_sel = battle.get("p2_selected", [])
    if fmt == "single":
        p1_active = p1_sel[:1]; p1_bench = p1_sel[1:]
        p2_active = p2_sel[:1]; p2_bench = p2_sel[1:]
    else:
        p1_active = p1_sel[:2]; p1_bench = p1_sel[2:]
        p2_active = p2_sel[:2]; p2_bench = p2_sel[2:]
    return {"p1_active": p1_active, "p1_bench": p1_bench, "p2_active": p2_active, "p2_bench": p2_bench}

def names_for_ids(id_list):
    if not id_list: return []
    pokes = list(pokedata.find({"_id": {"$in": id_list}}))
    pmap = {p["_id"]: p for p in pokes}
    return [pmap.get(pid, {}).get("name", "Unknown") for pid in id_list]

def format_lead_message(fmt, active_ids, bench_ids):
    active_names = names_for_ids(active_ids)
    bench_names = names_for_ids(bench_ids)
    if fmt == "single":
        lead_line = f"Lead: {active_names[0] if active_names else 'Unknown'}"
    else:
        lead_line = f"Leads: {', '.join(active_names) if active_names else 'Unknown'}"
    bench_line = f"Bench: {', '.join(bench_names) if bench_names else 'None'}"
    return f"{lead_line}\n{bench_line}"

async def start_battle_ready(battle):
    fmt = battle.get("format", "single")
    picks = build_battle_sides_from_picks(battle)
    battles.update_one(
        {"_id": battle["_id"]},
        {"$set": {
            "status": "active",
            "p1_active": picks["p1_active"],
            "p1_bench": picks["p1_bench"],
            "p2_active": picks["p2_active"],
            "p2_bench": picks["p2_bench"],
            "turn": 1
        }}
    )
    p1_msg = "✅ Team locked. Battle starts!\n\n" + format_lead_message(fmt, picks["p1_active"], picks["p1_bench"])
    p2_msg = "✅ Team locked. Battle starts!\n\n" + format_lead_message(fmt, picks["p2_active"], picks["p2_bench"])
    try: await bot.send_message(battle["p1_id"], p1_msg)
    except: pass
    try: await bot.send_message(battle["p2_id"], p2_msg)
    except: pass

print("Bot running...")
bot.run_until_disconnected()
