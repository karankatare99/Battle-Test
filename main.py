import random, json, math, uuid
from math import ceil
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
    pokemon["shiny"] = False
    pokemon["moves"] = []
    pokemon["iv_stats"] = {}
    pokemon["ev_stats"] = {}
    pokemon["stats"] = {}
    
    for line in lines[1:]:
        line = line.strip()
        if line.startswith("Ability:"):
            pokemon["ability"] = line.replace("Ability:", "").strip()
        elif line.startswith("Shiny:"):
            pokemon["shiny"] = True
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
        pokemon["ev_stats"][f"ev{stat}"] = evs[stat]
        pokemon["iv_stats"][f"iv{stat}"] = ivs[stat]
    
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
        if base == 1: # Shedinja case
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
    level = pokemon["level"]
    nature = pokemon["nature"]
    
    base_stats = kanto_data[name]["Base_Stats"]
    hp = base_stats["Hp"]
    atk = base_stats["Attack"]
    defense = base_stats["Defense"]
    spa = base_stats["Sp.Attack"]
    spd = base_stats["Sp.Defense"]
    spe = base_stats["Speed"]
    
    final_stats = {}
    final_stats["hp"] = calculate_stat(hp, pokemon["iv_stats"]["ivhp"] , pokemon["ev_stats"]["evhp"], level, nature, "hp")
    final_stats["atk"] = calculate_stat(atk, pokemon["iv_stats"]["ivatk"], pokemon["ev_stats"]["evatk"], level, nature, "atk")
    final_stats["def"] = calculate_stat(defense, pokemon["iv_stats"]["ivdef"], pokemon["ev_stats"]["evdef"], level, nature, "def")
    final_stats["spa"] = calculate_stat(spa, pokemon["iv_stats"]["ivspa"], pokemon["ev_stats"]["evspa"], level, nature, "spa")
    final_stats["spd"] = calculate_stat(spd, pokemon["iv_stats"]["ivspd"], pokemon["ev_stats"]["evspd"], level, nature, "spd")
    final_stats["spe"] = calculate_stat(spe, pokemon["iv_stats"]["ivspe"], pokemon["ev_stats"]["evspe"], level, nature, "spe")
    
    pokemon["stats"].update(final_stats)
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
        await event.respond("❌ You don't have any Pokémon yet.")
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
        await event.answer("❌ You don't own this Pokémon.", alert=True)
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
        await event.reply("❌ You don't have any Pokémon.")
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

# ===============================
# ANIMATED BATTLE SYSTEM 
# ===============================

# In-memory battles
battle_storage = {} # battle_id -> battle info
battle_map = {} # user_id -> battle_id

type_chart = {
    "Normal": {"Rock": 0.5, "Ghost": 0, "Steel": 0.5},
    "Fire": {"Bug": 2, "Steel": 2, "Grass": 2, "Ice": 2, "Rock": 0.5, "Fire": 0.5, "Water": 0.5, "Dragon": 0.5},
    "Water": {"Ground": 2,"Rock": 2, "Fire": 2, "Water": 0.5,"Grass": 0.5,"Dragon": 0.5},
    "Electric": {"Flying": 2,"Water": 2, "Grass": 0.5,"Electric": 0.5,"Dragon": 0.5,"Ground": 0},
    "Grass": {"Ground": 2,"Rock": 2, "Water": 2, "Flying": 0.5,"Poison": 0.5,"Bug": 0.5,"Steel": 0.5,"Fire": 0.5,"Grass": 0.5,"Dragon": 0.5},
    "Ice": {"Flying": 2,"Ground": 2, "Grass": 2, "Dragon": 2, "Steel": 0.5,"Fire": 0.5,"Water": 0.5,"Ice": 0.5},
    "Fighting": {"Normal": 2,"Rock": 2, "Steel": 2, "Ice": 2, "Dark": 2, "Flying": 0.5,"Poison": 0.5,"Bug": 0.5,"Psychic": 0.5,"Fairy": 0.5,"Ghost": 0},
    "Poison": {"Grass": 2, "Fairy": 2, "Poison": 0.5,"Ground": 0.5,"Rock": 0.5,"Ghost": 0.5,"Steel": 0},
    "Ground": {"Poison": 2,"Rock": 2, "Steel": 2, "Fire": 2, "Electric": 2,"Bug": 0.5,"Grass": 0.5,"Flying": 0},
    "Flying": {"Fighting": 2,"Bug": 2, "Grass": 2, "Rock": 0.5, "Steel": 0.5,"Electric": 0.5},
    "Psychic": {"Fighting": 2,"Poison": 2,"Steel": 0.5,"Psychic": 0.5,"Dark": 0},
    "Bug": {"Grass": 2, "Psychic": 2, "Dark": 2, "Fighting": 0.5,"Flying": 0.5,"Poison": 0.5,"Ghost": 0.5,"Steel": 0.5,"Fire": 0.5,"Fairy": 0.5},
    "Rock": {"Flying": 2,"Bug": 2, "Fire": 2, "Ice": 2, "Fighting": 0.5,"Ground": 0.5,"Steel": 0.5},
    "Ghost": {"Ghost": 2, "Psychic": 2, "Dark": 0.5, "Normal": 0},
    "Dragon": {"Dragon": 2,"Steel": 0.5,"Fairy": 0},
    "Dark": {"Ghost": 2, "Psychic": 2, "Fighting": 0.5,"Dark": 0.5,"Fairy": 0.5},
    "Steel": {"Rock": 2, "Ice": 2, "Fairy": 2, "Steel": 0.5,"Fire": 0.5,"Water": 0.5,"Electric": 0.5},
    "Fairy": {"Fighting": 2,"Dragon": 2,"Dark": 2, "Poison": 0.5,"Steel": 0.5,"Fire": 0.5}
}

# Load moves data
try:
    with open("moves.json", "r", encoding="utf-8") as f:
        MOVES = json.load(f)
except FileNotFoundError:
    MOVES = {}
    print("Warning: moves.json not found. Battle system may not work correctly.")

# -------------------------------
# Helper Functions
# -------------------------------

def get_user_team(user_id):
    """Fetch user's team Pokémon from DB (sync)."""
    user = db.users.find_one({"user_id": user_id})
    if not user or "team" not in user:
        return []
    
    team = []
    for pkm_id in user["team"]:
        pkm = db.pokemon_data.find_one({"_id": pkm_id})
        if pkm:
            team.append(pkm)
    return team

def init_battle_pokemon(bid):
    """Fetch both players' Pokémon and store in battle memory."""
    battle = battle_storage.get(bid)
    if not battle:
        return False
    
    # Fetch Pokémon for both players
    battle["pokemon"] = {
        "challenger": get_user_team(battle["challenger"]),
        "opponent": get_user_team(battle["opponent"])
    }
    return True

def load_battle_pokemon(bid):
    """Load Pokémon into battle state with full stats for damage calculation."""
    battle = battle_storage.get(bid)
    if not battle or "pokemon" not in battle:
        return False
    
    battle["battle_state"] = {
        "challenger": [],
        "opponent": []
    }
    
    # Load challenger Pokémon with error handling
    for pkm in battle["pokemon"]["challenger"]:
        try:
            # Get types from kanto_data if available
            types = []
            if pkm["name"] in kanto_data:
                types = kanto_data[pkm["name"]].get("Types", [])
            
            battle["battle_state"]["challenger"].append({
                "id": pkm["_id"],
                "name": pkm["name"],
                "hp": pkm["stats"]["hp"],
                "max_hp": pkm["stats"]["hp"],
                "atk": pkm["stats"]["atk"],
                "def": pkm["stats"]["def"],
                "spa": pkm["stats"]["spa"],
                "spd": pkm["stats"]["spd"],
                "spe": pkm["stats"]["spe"],
                "level": pkm.get("level", 50),
                "types": types or [pkm.get("tera_type", "Normal")],
                "moves": pkm.get("moves", []),
                "tera_type": pkm.get("tera_type", None),
                "status": None
            })
        except KeyError as e:
            print(f"Error loading challenger pokemon: {e}")
    
    # Load opponent Pokémon with error handling
    for pkm in battle["pokemon"]["opponent"]:
        try:
            # Get types from kanto_data if available
            types = []
            if pkm["name"] in kanto_data:
                types = kanto_data[pkm["name"]].get("Types", [])
            
            battle["battle_state"]["opponent"].append({
                "id": pkm["_id"],
                "name": pkm["name"],
                "hp": pkm["stats"]["hp"],
                "max_hp": pkm["stats"]["hp"],
                "atk": pkm["stats"]["atk"],
                "def": pkm["stats"]["def"],
                "spa": pkm["stats"]["spa"],
                "spd": pkm["stats"]["spd"],
                "spe": pkm["stats"]["spe"],
                "level": pkm.get("level", 50),
                "types": types or [pkm.get("tera_type", "Normal")],
                "moves": pkm.get("moves", []),
                "tera_type": pkm.get("tera_type", None),
                "status": None
            })
        except KeyError as e:
            print(f"Error loading opponent pokemon: {e}")
    
    # Set active Pokémon (first in team)
    if battle["battle_state"]["challenger"] and battle["battle_state"]["opponent"]:
        battle["active"] = {
            "challenger": battle["battle_state"]["challenger"][0],
            "opponent": battle["battle_state"]["opponent"][0]
        }
    
    return True

def create_battle(challenger_id, opponent_id, battle_type):
    bid = f"BATTLE-{uuid.uuid4().hex[:6].upper()}"
    battle_storage[bid] = {
        "id": bid,
        "challenger": challenger_id,
        "opponent": opponent_id,
        "type": battle_type,
        "state": "pending",
        "pending_action": {"challenger": None, "opponent": None},
        "forced_switch": {"challenger": False, "opponent": False},
        "turn": 1,
        "message_ids": {"challenger": None, "opponent": None}
    }
    return bid

def get_type_multiplier(move_type, defender_types):
    """
    Returns (multiplier, phrase_text) for the move vs defender's types.
    Supports dual-types.
    """
    total = 1.0
    phrases = []
    
    for d_type in defender_types:
        mult = type_chart.get(move_type, {}).get(d_type, 1)
        total *= mult
        
        if mult == 0:
            phrases.append(f"It doesn't affect opposing {d_type} types!")
        elif mult == 4:
            phrases.append("Extremely Effective!")
        elif mult == 2:
            phrases.append("Super Effective!")
        elif mult == 0.5:
            phrases.append("Not Very Effective.")
        elif mult == 0.25:
            phrases.append("Mostly Ineffective.")
    
    # Determine overall effectiveness
    if total == 0:
        return total, "It doesn't affect the opposing Pokémon!"
    elif total >= 2:
        return total, "It's super effective!"
    elif total <= 0.5:
        return total, "It's not very effective..."
    else:
        return total, ""

def calculate_damage(attacker, defender, move_key):
    """
    Returns (damage, battle_text) for one move.
    attacker/defender = dicts with at least:
    {name, level, types, atk, def, spa, spd}
    """
    move_key = move_key.lower().replace(" ", "-")
    
    if move_key not in MOVES:
        return 0, f"{attacker['name']} used {move_key}!\nBut the move failed!"
    
    move = MOVES[move_key]
    
    # Status move = no damage
    if move.get("Category") == "Status":
        return 0, f"{attacker['name']} used {move['Name']}!\n{move.get('Effects', 'The move had an effect!')}"
    
    # Handle power
    power = move.get("Power", "—")
    if power in ["—", None, ""]:
        return 0, f"{attacker['name']} used {move.get('Name', move_key)}!"
    
    try:
        power = int(power)
    except (ValueError, TypeError):
        return 0, f"{attacker['name']} used {move.get('Name', move_key)}!"
    
    # Accuracy check
    acc = move.get("Accuracy", 100)
    if acc not in ["—", None, ""]:
        try:
            if random.randint(1, 100) > int(acc):
                return 0, f"{attacker['name']} used {move.get('Name', move_key)}!\n{attacker['name']}'s attack missed!"
        except (ValueError, TypeError):
            pass
    
    # Crit (1/24 chance)
    crit = 1.5 if random.randint(1, 24) == 1 else 1.0
    
    # Random factor (85–100%)
    rand = random.uniform(0.85, 1.0)
    
    # Stats
    if move.get("Category") == "Physical":
        A = attacker.get("atk", 100)
        D = defender.get("def", 100)
    else: # Special
        A = attacker.get("spa", 100)
        D = defender.get("spd", 100)
    
    L = attacker.get("level", 50)
    
    # STAB (same type bonus)
    move_type = move.get("Type", "Normal")
    stab = 1.5 if move_type in attacker.get("types", []) else 1.0
    
    # Type multiplier
    multiplier, phrase = get_type_multiplier(move_type, defender.get("types", ["Normal"]))
    
    # Damage formula
    damage = (((((2 * L / 5) + 2) * power * A / D) / 50) + 2)
    damage *= stab * multiplier * rand * crit
    damage = max(1, int(damage)) # at least 1
    
    # Build text
    text = f"{attacker['name']} used {move.get('Name', move_key)}!\n"
    if crit > 1.0:
        text += "A critical hit!\n"
    if phrase:
        text += f"{phrase}\n"
    text += f"{defender['name']} lost {damage} HP!"
    
    return damage, text

async def send_battle_ui(bid, battle_text=""):
    """Send battle UI with optional battle text animation"""
    battle = battle_storage.get(bid)
    if not battle or "active" not in battle:
        return
    
    challenger = battle["active"]["challenger"]
    opponent = battle["active"]["opponent"]
    
    def hp_bar(current, max_hp, length=20):
        filled = int(length * current / max_hp) if max_hp > 0 else 0
        return "🟩" * filled + "⬜" * (length - filled)
    
    challenger_fainted = challenger["hp"] <= 0
    opponent_fainted = opponent["hp"] <= 0
    
    # Build challenger UI (opponent appears as "Opposing")
    c_text = f"⚔️ Battle Turn {battle.get('turn', 1)}\n\n"
    
    if battle_text:
        c_text += f"📢 {battle_text}\n\n"
    
    c_text += (
        f"Your {challenger['name']}: {challenger['hp']}/{challenger['max_hp']} HP\n"
        f"{hp_bar(challenger['hp'], challenger['max_hp'])}\n\n"
        f"Opposing {opponent['name']}: {opponent['hp']}/{opponent['max_hp']} HP\n"
        f"{hp_bar(opponent['hp'], opponent['max_hp'])}"
    )
    
    # Build opponent UI (challenger appears as "Opposing")  
    o_text = f"⚔️ Battle Turn {battle.get('turn', 1)}\n\n"
    
    if battle_text:
        # For opponent, swap the perspective in battle text
        opponent_battle_text = battle_text.replace("Your ", "Temp_Your_")
        opponent_battle_text = opponent_battle_text.replace("Opposing ", "Your ")
        opponent_battle_text = opponent_battle_text.replace("Temp_Your_", "Opposing ")
        o_text += f"📢 {opponent_battle_text}\n\n"
    
    o_text += (
        f"Your {opponent['name']}: {opponent['hp']}/{opponent['max_hp']} HP\n"
        f"{hp_bar(opponent['hp'], opponent['max_hp'])}\n\n"
        f"Opposing {challenger['name']}: {challenger['hp']}/{challenger['max_hp']} HP\n"
        f"{hp_bar(challenger['hp'], challenger['max_hp'])}"
    )
    
    # Build challenger buttons
    c_buttons = []
    if challenger_fainted or battle["forced_switch"]["challenger"]:
        c_text += "\n\n💀 Your Pokémon fainted! Choose a replacement:"
        team = battle["battle_state"]["challenger"]
        for idx, pkm in enumerate(team):
            if pkm["hp"] > 0 and pkm["id"] != challenger["id"]:
                c_buttons.append([Button.inline(
                    f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",
                    f"battle:forced_switch:{bid}:challenger:{idx}"
                )])
        if not c_buttons:
            c_buttons = [[Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")]]
    elif battle["state"] == "active":
        for move in challenger.get("moves", []):
            c_buttons.append([Button.inline(move, f"battle:move:{bid}:{move}")])
        c_buttons.append([
            Button.inline("🔄 Switch", f"battle:switch:{bid}:challenger"),
            Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")
        ])
    
    # Build opponent buttons
    o_buttons = []
    if opponent_fainted or battle["forced_switch"]["opponent"]:
        o_text += "\n\n💀 Your Pokémon fainted! Choose a replacement:"
        team = battle["battle_state"]["opponent"]
        for idx, pkm in enumerate(team):
            if pkm["hp"] > 0 and pkm["id"] != opponent["id"]:
                o_buttons.append([Button.inline(
                    f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",
                    f"battle:forced_switch:{bid}:opponent:{idx}"
                )])
        if not o_buttons:
            o_buttons = [[Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")]]
    elif battle["state"] == "active":
        for move in opponent.get("moves", []):
            o_buttons.append([Button.inline(move, f"battle:move:{bid}:{move}")])
        o_buttons.append([
            Button.inline("🔄 Switch", f"battle:switch:{bid}:opponent"),
            Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")
        ])
    
    # Update existing messages instead of sending new ones
    try:
        if battle["message_ids"]["challenger"]:
            await bot.edit_message(battle["challenger"], battle["message_ids"]["challenger"], c_text, buttons=c_buttons)
        else:
            msg = await bot.send_message(battle["challenger"], c_text, buttons=c_buttons)
            battle["message_ids"]["challenger"] = msg.id
            
        if battle["message_ids"]["opponent"]:
            await bot.edit_message(battle["opponent"], battle["message_ids"]["opponent"], o_text, buttons=o_buttons)
        else:
            msg = await bot.send_message(battle["opponent"], o_text, buttons=o_buttons)
            battle["message_ids"]["opponent"] = msg.id
            
    except Exception as e:
        print(f"UI update failed: {e}")

async def animate_battle_sequence(bid, sequence_steps):
    """Animate battle sequence with timed updates"""
    for step in sequence_steps:
        battle_text = step.get("text", "")
        delay = step.get("delay", 1.0)
        hp_changes = step.get("hp_changes", {})
        
        # Apply HP changes if any
        battle = battle_storage.get(bid)
        if battle and hp_changes:
            for side, change in hp_changes.items():
                if side in battle["active"] and change != 0:
                    new_hp = max(0, battle["active"][side]["hp"] + change)
                    battle["active"][side]["hp"] = new_hp
        
        # Update UI with current step
        await send_battle_ui(bid, battle_text)
        
        # Wait before next step
        if delay > 0:
            await asyncio.sleep(delay)

async def get_action_result(battle, side, other_side, action):
    """Get the result text and damage for an action without applying HP changes yet"""
    if action.startswith("switch:"):
        try:
            idx = int(action.split(":")[1])
            old_pkm = battle["active"][side]
            new_pkm = battle["battle_state"][side][idx]
            
            if new_pkm["hp"] <= 0:
                return f"{new_pkm['name']} has fainted and cannot battle!", 0
            
            battle["active"][side] = new_pkm
            return f"🔄 {new_pkm['name']} was switched in!", 0
        except (IndexError, ValueError, KeyError):
            return "❌ Switch failed - invalid Pokémon selection!", 0
    else:
        # Regular move
        attacker = battle["active"][side]
        defender = battle["active"][other_side]
        
        if attacker["hp"] <= 0:
            return f"{attacker['name']} has fainted and cannot attack!", 0
        
        # Calculate damage but don't apply it yet
        dmg, text = calculate_damage(attacker, defender, action)
        
        # Format text with proper perspective
        if side == "challenger":
            text = text.replace(f"{attacker['name']}", f"Your {attacker['name']}")
            text = text.replace(f"{defender['name']}", f"Opposing {defender['name']}")
        else:
            text = text.replace(f"{attacker['name']}", f"Your {attacker['name']}")
            text = text.replace(f"{defender['name']}", f"Opposing {defender['name']}")
        
        return text, dmg

async def resolve_turn(bid):
    """Resolve a full turn with animated sequence"""
    battle = battle_storage.get(bid)
    if not battle:
        return
    
    challenger_action = battle["pending_action"]["challenger"]
    opponent_action = battle["pending_action"]["opponent"]
    
    # Ensure both sides have chosen an action
    if not challenger_action or not opponent_action:
        return
    
    # Determine move order by speed (switches go first)
    challenger_speed = battle["active"]["challenger"].get("spe", 0)
    opponent_speed = battle["active"]["opponent"].get("spe", 0)
    
    challenger_switches = challenger_action.startswith("switch:")
    opponent_switches = opponent_action.startswith("switch:")
    
    if challenger_switches and not opponent_switches:
        first, second = "challenger", "opponent"
    elif opponent_switches and not challenger_switches:
        first, second = "opponent", "challenger"
    else:
        # Both switch or both attack - determine by speed
        first, second = (
            ("challenger", "opponent")
            if challenger_speed >= opponent_speed
            else ("opponent", "challenger")
        )
    
    # Create animated sequence
    sequence = []
    
    # Process first action
    first_action_text, first_damage = await get_action_result(battle, first, second, battle["pending_action"][first])
    
    # Split the action text to get move announcement vs effects
    first_lines = first_action_text.split("\n")
    first_move_announcement = first_lines[0] if first_lines else first_action_text
    
    # Add first move announcement
    sequence.append({
        "text": first_move_announcement,
        "delay": 1.0
    })
    
    # Add damage and effects
    if first_damage > 0:
        sequence.append({
            "text": first_action_text,
            "hp_changes": {second: -first_damage},
            "delay": 1.5
        })
    else:
        sequence.append({
            "text": first_action_text,
            "delay": 1.0
        })
    
    # Check if second Pokemon can still move
    defender_hp_after_first = max(0, battle["active"][second]["hp"] - first_damage)
    second_can_move = defender_hp_after_first > 0
    
    if second_can_move:
        # Process second action
        second_action_text, second_damage = await get_action_result(battle, second, first, battle["pending_action"][second])
        
        second_lines = second_action_text.split("\n")
        second_move_announcement = second_lines[0] if second_lines else second_action_text
        
        # Add second move announcement
        sequence.append({
            "text": second_move_announcement,
            "delay": 1.0
        })
        
        # Add second damage and effects
        if second_damage > 0:
            sequence.append({
                "text": second_action_text,
                "hp_changes": {first: -second_damage},
                "delay": 1.5
            })
        else:
            sequence.append({
                "text": second_action_text,
                "delay": 1.0
            })
    else:
        # Second Pokemon fainted, can't move
        battle["forced_switch"][second] = True
        sequence.append({
            "text": f"{battle['active'][second]['name']} fainted and couldn't use its move!",
            "delay": 1.0
        })
    
    # Run the animated sequence
    await animate_battle_sequence(bid, sequence)
    
    # Check for additional forced switches after all damage is applied
    if battle["active"][first]["hp"] <= 0:
        battle["forced_switch"][first] = True
    if battle["active"][second]["hp"] <= 0:
        battle["forced_switch"][second] = True
    
    # Clear pending actions for next turn
    battle["pending_action"] = {"challenger": None, "opponent": None}
    battle["turn"] = battle.get("turn", 1) + 1
    
    # Check for battle end conditions
    challenger_has_healthy = any(p["hp"] > 0 for p in battle["battle_state"]["challenger"])
    opponent_has_healthy = any(p["hp"] > 0 for p in battle["battle_state"]["opponent"])
    
    if not challenger_has_healthy:
        await end_battle(bid, "opponent")
        return
    elif not opponent_has_healthy:
        await end_battle(bid, "challenger")
        return
    
    # Final UI update for next turn (clear battle text)
    await asyncio.sleep(1.0)  # Small delay before clearing battle text
    await send_battle_ui(bid)

async def end_battle(bid, winner_side):
    """End the battle and declare winner."""
    battle = battle_storage.get(bid)
    if not battle:
        return
    
    winner_id = battle[winner_side]
    loser_id = battle["challenger"] if winner_side == "opponent" else battle["opponent"]
    
    try:
        winner_entity = await bot.get_entity(winner_id)
        loser_entity = await bot.get_entity(loser_id)
        
        winner_name = winner_entity.first_name
        loser_name = loser_entity.first_name
        
        result_text = f"🏆 Battle Ended!\n\n🎉 {winner_name} wins!\n💔 {loser_name} lost!"
        
        await bot.send_message(winner_id, result_text)
        await bot.send_message(loser_id, result_text)
        
    except Exception as e:
        print(f"Failed to send battle results: {e}")
    
    # Cleanup
    battle_storage.pop(bid, None)
    battle_map.pop(battle["challenger"], None)
    battle_map.pop(battle["opponent"], None)

# -------------------------------
# Battle Commands
# -------------------------------

@bot.on(events.NewMessage(pattern=r"/battleS"))
async def battle_singles(event):
    if not event.is_reply:
        return await event.reply("⚠️ Reply to a user to challenge them to a Singles battle.")
    
    reply_msg = await event.get_reply_message()
    opp = reply_msg.sender_id
    me = event.sender_id
    
    if me == opp:
        return await event.reply("❌ You can't battle yourself!")
    
    # Check if users have teams
    my_team = get_user_team(me)
    opp_team = get_user_team(opp)
    
    if not my_team:
        return await event.reply("❌ You don't have any Pokémon in your team!")
    
    if not opp_team:
        return await event.reply("❌ Your opponent doesn't have any Pokémon in their team!")
    
    bid = create_battle(me, opp, "singles")
    challenger_name = event.sender.first_name
    
    await event.reply(
        f"🔥 {challenger_name} challenged you to a Singles battle!",
        buttons=[
            [Button.inline("✅ Accept", f"battle:accept:{bid}".encode()),
             Button.inline("❌ Decline", f"battle:decline:{bid}".encode())]
        ]
    )

@bot.on(events.NewMessage(pattern=r"/battleD"))
async def battle_doubles(event):
    if not event.is_reply:
        return await event.reply("⚠️ Reply to a user to challenge them to a Doubles battle.")
    
    reply_msg = await event.get_reply_message()
    opp = reply_msg.sender_id
    me = event.sender_id
    
    if me == opp:
        return await event.reply("❌ You can't battle yourself!")
    
    # Check if users have teams
    my_team = get_user_team(me)
    opp_team = get_user_team(opp)
    
    if len(my_team) < 2:
        return await event.reply("❌ You need at least 2 Pokémon for doubles!")
    
    if len(opp_team) < 2:
        return await event.reply("❌ Your opponent needs at least 2 Pokémon for doubles!")
    
    bid = create_battle(me, opp, "doubles")
    challenger_name = event.sender.first_name
    
    await event.reply(
        f"🔥 {challenger_name} challenged you to a Doubles battle!",
        buttons=[
            [Button.inline("✅ Accept", f"battle:accept:{bid}".encode()),
             Button.inline("❌ Decline", f"battle:decline:{bid}".encode())]
        ]
    )

# -------------------------------
# Accept / Decline
# -------------------------------

@bot.on(events.CallbackQuery(pattern=b"battle:accept:(.+)"))
async def cb_accept(event):
    bid = event.pattern_match.group(1).decode()
    battle = battle_storage.get(bid)
    
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    if event.sender_id != battle["opponent"]:
        return await event.answer("Only the challenged user can accept.", alert=True)
    
    if battle["state"] != "pending":
        return await event.answer("This battle is not available.", alert=True)
    
    battle["state"] = "active"
    battle_map[battle["challenger"]] = bid
    battle_map[battle["opponent"]] = bid
    
    # Initialize battle Pokémon
    if not init_battle_pokemon(bid):
        return await event.edit("❌ Failed to load Pokémon data!")
    
    if not load_battle_pokemon(bid):
        return await event.edit("❌ Failed to initialize battle state!")
    
    await event.edit("✅ Battle accepted! Check your PMs to continue.")
    
    # Send battle interface to both players
    await send_battle_ui(bid)

@bot.on(events.CallbackQuery(pattern=b"battle:decline:(.+)"))
async def cb_decline(event):
    bid = event.pattern_match.group(1).decode()
    battle = battle_storage.get(bid)
    
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    if event.sender_id != battle["opponent"]:
        return await event.answer("Only the challenged user can decline.", alert=True)
    
    battle["state"] = "cancelled"
    battle_storage.pop(bid, None) # Clean up
    
    await event.edit("❌ Battle declined.")

# Forced switch handler
@bot.on(events.CallbackQuery(pattern=b"battle:forced_switch:(.+):(.+):(.+)"))
async def cb_forced_switch(event):
    bid = event.pattern_match.group(1).decode()
    side = event.pattern_match.group(2).decode()
    idx = int(event.pattern_match.group(3).decode())
    
    battle = battle_storage.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    user_id = event.sender_id
    expected_side = "challenger" if user_id == battle["challenger"] else "opponent"
    
    if side != expected_side:
        return await event.answer("❌ Invalid switch request.", alert=True)
    
    # Validate switch target
    try:
        target_pokemon = battle["battle_state"][side][idx]
        if target_pokemon["hp"] <= 0:
            return await event.answer("❌ That Pokémon has fainted!", alert=True)
    except (IndexError, KeyError):
        return await event.answer("❌ Invalid Pokémon selection!", alert=True)
    
    # Perform the forced switch
    battle["active"][side] = target_pokemon
    battle["forced_switch"][side] = False # Clear forced switch flag
    
    await event.edit(f"✅ {target_pokemon['name']} was sent out!")
    
    # Check if both sides are ready (no forced switches needed)
    if not battle["forced_switch"]["challenger"] and not battle["forced_switch"]["opponent"]:
        await send_battle_ui(bid)

@bot.on(events.CallbackQuery(pattern=b"battle:move:(.+):(.+)"))
async def cb_move(event):
    bid = event.pattern_match.group(1).decode()
    move_selected = event.pattern_match.group(2).decode()
    
    battle = battle_storage.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    user_id = event.sender_id
    side = "challenger" if user_id == battle["challenger"] else "opponent"
    
    if battle["forced_switch"][side]:
        return await event.answer("❌ You must choose a replacement Pokémon first!", alert=True)
    
    active_pokemon = battle["active"][side]
    if move_selected not in active_pokemon.get("moves", []):
        return await event.answer("❌ Your Pokémon doesn't know that move!", alert=True)
    
    battle["pending_action"][side] = move_selected
    
    await event.answer(f"✅ You selected {move_selected}. Waiting for opponent...")
    
    # Check if both players have chosen actions
    if battle["pending_action"]["challenger"] and battle["pending_action"]["opponent"]:
        await resolve_turn(bid)

@bot.on(events.CallbackQuery(pattern=b"battle:forfeit:(.+)"))
async def cb_forfeit(event):
    bid = event.pattern_match.group(1).decode()
    battle = battle_storage.get(bid)
    
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    user_id = event.sender_id
    
    if user_id == battle["challenger"]:
        await end_battle(bid, "opponent")
    elif user_id == battle["opponent"]:
        await end_battle(bid, "challenger")
    else:
        return await event.answer("❌ You are not in this battle.", alert=True)

@bot.on(events.CallbackQuery(pattern=b"battle:switch:(.+):(.+)"))
async def cb_switch(event):
    bid = event.pattern_match.group(1).decode()
    side = event.pattern_match.group(2).decode()
    
    battle = battle_storage.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    user_id = event.sender_id
    expected_side = "challenger" if user_id == battle["challenger"] else "opponent"
    
    if side != expected_side:
        return await event.answer("❌ Invalid switch request.", alert=True)
    
    # Check if player needs forced switch first
    if battle["forced_switch"][side]:
        return await event.answer("❌ You must choose a replacement Pokémon first!", alert=True)
    
    # List the player's team
    team = battle["battle_state"][side]
    active_pokemon = battle["active"][side]
    
    # Only show Pokémon that are NOT fainted and not already active
    buttons = []
    for idx, pkm in enumerate(team):
        if pkm["hp"] > 0 and pkm["id"] != active_pokemon["id"]:
            buttons.append([Button.inline(
                f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",
                f"battle:choose_switch:{bid}:{side}:{idx}"
            )])
    
    if not buttons:
        return await event.answer("⚠ No healthy Pokémon to switch to.", alert=True)
    
    await event.edit("🔄 Choose a Pokémon to switch in:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"battle:choose_switch:(.+):(.+):(.+)"))
async def cb_choose_switch(event):
    bid = event.pattern_match.group(1).decode()
    side = event.pattern_match.group(2).decode()
    idx = int(event.pattern_match.group(3).decode())
    
    battle = battle_storage.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    user_id = event.sender_id
    expected_side = "challenger" if user_id == battle["challenger"] else "opponent"
    
    if side != expected_side:
        return await event.answer("❌ Invalid switch request.", alert=True)
    
    # Validate switch target
    try:
        target_pokemon = battle["battle_state"][side][idx]
        if target_pokemon["hp"] <= 0:
            return await event.answer("❌ That Pokémon has fainted!", alert=True)
        
        if target_pokemon["id"] == battle["active"][side]["id"]:
            return await event.answer("❌ That Pokémon is already active!", alert=True)
            
    except (IndexError, KeyError):
        return await event.answer("❌ Invalid Pokémon selection!", alert=True)
    
    # Register switch action
    battle["pending_action"][side] = f"switch:{idx}"
    
    await event.edit(f"🔄 Switch to {target_pokemon['name']} registered! Waiting for opponent...")
    
    # If both actions chosen → resolve turn
    if battle["pending_action"]["challenger"] and battle["pending_action"]["opponent"]:
        await resolve_turn(bid)

print("Bot running...")
bot.run_until_disconnected()
