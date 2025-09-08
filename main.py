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

    
# -------------------------------
# In-memory battles
# -------------------------------
import uuid
from math import ceil
from telethon import events, Button

battles = {}      # battle_id -> battle info
battle_map = {}   # user_id -> battle_id

type_chart = {
    "Normal":     {"Rock": 0.5, "Ghost": 0,   "Steel": 0.5},
    "Fire":       {"Bug": 2,   "Steel": 2,   "Grass": 2,   "Ice": 2,   "Rock": 0.5, "Fire": 0.5, "Water": 0.5, "Dragon": 0.5},
    "Water":      {"Ground": 2,"Rock": 2,    "Fire": 2,    "Water": 0.5,"Grass": 0.5,"Dragon": 0.5},
    "Electric":   {"Flying": 2,"Water": 2,   "Grass": 0.5,"Electric": 0.5,"Dragon": 0.5,"Ground": 0},
    "Grass":      {"Ground": 2,"Rock": 2,    "Water": 2,   "Flying": 0.5,"Poison": 0.5,"Bug": 0.5,"Steel": 0.5,"Fire": 0.5,"Grass": 0.5,"Dragon": 0.5},
    "Ice":        {"Flying": 2,"Ground": 2,  "Grass": 2,   "Dragon": 2, "Steel": 0.5,"Fire": 0.5,"Water": 0.5,"Ice": 0.5},
    "Fighting":   {"Normal": 2,"Rock": 2,    "Steel": 2,   "Ice": 2,    "Dark": 2,   "Flying": 0.5,"Poison": 0.5,"Bug": 0.5,"Psychic": 0.5,"Fairy": 0.5,"Ghost": 0},
    "Poison":     {"Grass": 2, "Fairy": 2,   "Poison": 0.5,"Ground": 0.5,"Rock": 0.5,"Ghost": 0.5,"Steel": 0},
    "Ground":     {"Poison": 2,"Rock": 2,    "Steel": 2,   "Fire": 2,   "Electric": 2,"Bug": 0.5,"Grass": 0.5,"Flying": 0},
    "Flying":     {"Fighting": 2,"Bug": 2,   "Grass": 2,   "Rock": 0.5, "Steel": 0.5,"Electric": 0.5},
    "Psychic":    {"Fighting": 2,"Poison": 2,"Steel": 0.5,"Psychic": 0.5,"Dark": 0},
    "Bug":        {"Grass": 2, "Psychic": 2, "Dark": 2,    "Fighting": 0.5,"Flying": 0.5,"Poison": 0.5,"Ghost": 0.5,"Steel": 0.5,"Fire": 0.5,"Fairy": 0.5},
    "Rock":       {"Flying": 2,"Bug": 2,     "Fire": 2,    "Ice": 2,    "Fighting": 0.5,"Ground": 0.5,"Steel": 0.5},
    "Ghost":      {"Ghost": 2, "Psychic": 2, "Dark": 0.5,  "Normal": 0},
    "Dragon":     {"Dragon": 2,"Steel": 0.5,"Fairy": 0},
    "Dark":       {"Ghost": 2, "Psychic": 2, "Fighting": 0.5,"Dark": 0.5,"Fairy": 0.5},
    "Steel":      {"Rock": 2,  "Ice": 2,     "Fairy": 2,   "Steel": 0.5,"Fire": 0.5,"Water": 0.5,"Electric": 0.5},
    "Fairy":      {"Fighting": 2,"Dragon": 2,"Dark": 2,    "Poison": 0.5,"Steel": 0.5,"Fire": 0.5}
}


with open("moves.json", "r", encoding="utf-8") as f:
    MOVES = json.load(f)
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
    battle = battles.get(bid)
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
    battle = battles.get(bid)
    if not battle or "pokemon" not in battle:
        return False

    battle["battle_state"] = {
        "challenger": [],
        "opponent": []
    }

    # Challenger Pokémon
    for pkm in battle["pokemon"]["challenger"]:
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
            "level": pkm.get("level", 50),   # default level
            "types": pkm.get("types", [pkm.get("tera_type")]),  # for STAB
            "moves": pkm["moves"],
            "tera_type": pkm.get("tera_type", None),
            "status": None
        })

    # Opponent Pokémon
    for pkm in battle["pokemon"]["opponent"]:
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
            "types": pkm.get("types", [pkm.get("tera_type")]),
            "moves": pkm["moves"],
            "tera_type": pkm.get("tera_type", None),
            "status": None
        })

    # Set active Pokémon (first in team)
    battle["active"] = {
        "challenger": battle["battle_state"]["challenger"][0],
        "opponent": battle["battle_state"]["opponent"][0]
    }

    return True

def get_hp_bar(current, max_hp, length=10):
    """Generate a simple text HP bar."""
    ratio = current / max_hp
    filled = ceil(ratio * length)
    empty = length - filled
    return "🟩"*filled + "⬜"*empty

async def send_battle_interface(user_id, battle):
    """Send battle interface with moves, switch, and forfeit."""
    active_self = battle["active"]["challenger"] if user_id == battle["challenger"] else battle["active"]["opponent"]
    active_opp = battle["active"]["opponent"] if user_id == battle["challenger"] else battle["active"]["challenger"]

    # HP bars
    self_hp_bar = get_hp_bar(active_self["hp"], active_self["max_hp"])
    opp_hp_bar = get_hp_bar(active_opp["hp"], active_opp["max_hp"])

    # Buttons: Moves
    buttons = []
    for move in active_self["moves"]:
        buttons.append([Button.inline(move, f"battle:move:{battle['id']}:{move}")])

    # Switch and Forfeit
    buttons.append([Button.inline("🔄 Switch", f"battle:switch:{battle['id']}")])
    buttons.append([Button.inline("🏳️ Forfeit", f"battle:forfeit:{battle['id']}")])

    await bot.send_message(
        user_id,
        f"⚔️ Battle Start!\n\n"
        f"Your Pokémon: {active_self['name']} {self_hp_bar} {active_self['hp']}/{active_self['max_hp']}\n"
        f"Opponent Pokémon: {active_opp['name']} {opp_hp_bar} {active_opp['hp']}/{active_opp['max_hp']}\n",
        buttons=buttons
    )
    
    

def create_battle(challenger_id, opponent_id, battle_type):
    """Create a new battle entry."""
    bid = f"BATTLE-{uuid.uuid4().hex[:6].upper()}"
    battles[bid] = {
        "id": bid,
        "challenger": challenger_id,
        "opponent": opponent_id,
        "type": battle_type,
        "state": "pending",
        "pending_moves": {
            "challenger": None,
            "opponent": None
        }
    }
    
    return bid
async def send_move_menu(bid):
    battle = battles[bid]

    challenger_id = battle["challenger"]
    opponent_id = battle["opponent"]

    # Challenger move menu
    msg_challenger = await bot.send_message(
        challenger_id,
        "Choose your move:",
        buttons=[
            [Button.inline("Thunderbolt", f"battle:move:Thunderbolt")],
            [Button.inline("Quick Attack", f"battle:move:Quick Attack")],
        ]
    )

    # Opponent move menu
    msg_opponent = await bot.send_message(
        opponent_id,
        "Choose your move:",
        buttons=[
            [Button.inline("Tackle", f"battle:move:Tackle")],
            [Button.inline("Growl", f"battle:move:Growl")],
        ]
    )

    # Store these messages in the battle
    battle["move_msg_challenger"] = msg_challenger
    battle["move_msg_opponent"] = msg_opponent

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
        else:
            phrases.append("Effective.")

    return total, " ".join(phrases)

def calculate_damage(attacker, defender, move_key):
    """
    Returns (damage, battle_text) for one move.
    attacker/defender = dicts with at least:
      {name, level, types, atk, def, spa, spd}
    """
    move = MOVES[move_key]

    # Status move = no damage
    if move["Category"] == "Status":
        return 0, f"{attacker['name']} used {move['Name']}!\n{move['Effects']}"

    # Handle power
    power = move["Power"]
    if power in ["—", None]:
        return 0, f"{attacker['name']} used {move['Name']}!"
    power = int(power)

    # Accuracy check
    acc = move["Accuracy"]
    if acc not in ["—", None]:
        if random.randint(1, 100) > int(acc):
            # Miss
            if random.choice([True, False]):
                return 0, f"{attacker['name']} avoided the attack!"
            else:
                return 0, f"Opposing {defender['name']} avoided the attack!"

    # Crit (1/24 chance)
    crit = 1.5 if random.randint(1, 24) == 1 else 1.0

    # Random factor (85–100%)
    rand = random.uniform(0.85, 1.0)

    # Stats
    if move["Category"] == "Physical":
        A = attacker["atk"]
        D = defender["def"]
    else:  # Special
        A = attacker["spa"]
        D = defender["spd"]

    L = attacker["level"]

    # STAB (same type bonus)
    stab = 1.5 if move["Type"] in attacker["types"] else 1.0

    # Type multiplier
    multiplier, phrase = get_type_multiplier(move["Type"], defender["types"])

    # Damage formula
    damage = (((((2 * L / 5) + 2) * power * A / D) / 50) + 2)
    damage *= stab * multiplier * rand * crit
    damage = max(1, int(damage))  # at least 1

    # Build text
    text = f"{attacker['name']} used {move['Name']}!\n"
    if crit > 1.0:
        text += "A critical hit!\n"
    if phrase:
        text += f"It was {phrase}\n"
    text += f"{defender['name']} lost {damage} HP!"

    return damage, text
    
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
        return await event.reply("❌ You can’t battle yourself!")

    bid = create_battle(me, opp, "singles")
    await event.reply(
        f"🔥 <a href='tg://user?id={me}'>Player</a> challenged <a href='tg://user?id={opp}'>Opponent</a> to a Singles battle!",
        buttons=[
            [Button.inline("✅ Accept", f"battle:accept:{bid}".encode()),
             Button.inline("❌ Decline", f"battle:decline:{bid}".encode())]
        ],
        parse_mode="html"
    )

@bot.on(events.NewMessage(pattern=r"/battleD"))
async def battle_doubles(event):
    if not event.is_reply:
        return await event.reply("⚠️ Reply to a user to challenge them to a Doubles battle.")
    reply_msg = await event.get_reply_message()
    opp = reply_msg.sender_id
    me = event.sender_id
    if me == opp:
        return await event.reply("❌ You can’t battle yourself!")

    bid = create_battle(me, opp, "doubles")
    await event.reply(
        f"🔥 <a href='tg://user?id={me}'>Player</a> challenged <a href='tg://user?id={opp}'>Opponent</a> to a Doubles battle!",
        buttons=[
            [Button.inline("✅ Accept", f"battle:accept:{bid}".encode()),
             Button.inline("❌ Decline", f"battle:decline:{bid}".encode())]
        ],
        parse_mode="html"
    )

# -------------------------------
# Accept / Decline
# -------------------------------
@bot.on(events.CallbackQuery(pattern=b"battle:accept:(.+)"))
async def cb_accept(event):
    bid = event.pattern_match.group(1).decode()
    battle = battles.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)

    if event.sender_id != battle["opponent"]:
        return await event.answer("Only the challenged user can accept.", alert=True)

    if battle["state"] != "pending":
        return await event.answer("This battle is not available.", alert=True)

    battle["state"] = "active"
    battle_map[battle["challenger"]] = bid
    battle_map[battle["opponent"]] = bid

    # -----------------------------
    # Initialize battle Pokémon (sync DB)
    # -----------------------------
    init_battle_pokemon(bid)
    load_battle_pokemon(bid)

    await event.edit("✅ Battle accepted! Check your PMs to continue.")

    # Send battle interface to both players
    await send_battle_interface(battle["challenger"], battle)
    await send_battle_interface(battle["opponent"], battle)

@bot.on(events.CallbackQuery(pattern=b"battle:decline:(.+)"))
async def cb_decline(event):
    bid = event.pattern_match.group(1).decode()
    battle = battles.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)

    if event.sender_id != battle["opponent"]:
        return await event.answer("Only the challenged user can decline.", alert=True)

    battle["state"] = "cancelled"
    await event.edit("❌ Battle cancelled by opponent.")

@bot.on(events.CallbackQuery(pattern=b"battle:move:(.+):(.+)"))
async def cb_move(event):
    bid = event.pattern_match.group(1).decode()
    move_selected = event.pattern_match.group(2).decode()
    
    battle = battles.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)
    
    user_id = event.sender_id
    side = "challenger" if user_id == battle["challenger"] else "opponent"
    
    # Save the chosen move
    battle["pending_moves"][side] = move_selected
    
    # Save message ID safely
    msg_key = f"move_msg_{side}"
    battle[msg_key] = event.message.id if event.message else None
    
    # Update user's own message
    try:
        await event.edit(f"✅ You selected {move_selected}. Waiting for opponent...")
    except Exception as e:
        print(f"Edit {side} msg failed: {e}")
    
    # If both moves are selected
    if battle["pending_moves"]["challenger"] and battle["pending_moves"]["opponent"]:
        # Get active Pokémon
        atk_challenger = battle["active"]["challenger"]
        atk_opponent = battle["active"]["opponent"]
        
        # Moves
        move_challenger = battle["pending_moves"]["challenger"]
        move_opponent = battle["pending_moves"]["opponent"]
        
        # Calculate damages
        dmg_to_opponent, text_challenger = calculate_damage(atk_challenger, atk_opponent, move_challenger)
        dmg_to_challenger, text_opponent = calculate_damage(atk_opponent, atk_challenger, move_opponent)
        
        # Apply damage
        atk_opponent["hp"] = max(0, atk_opponent["hp"] - dmg_to_opponent)
        atk_challenger["hp"] = max(0, atk_challenger["hp"] - dmg_to_challenger)
        
        # Build final messages
        challenger_text = f"{text_challenger}\n{text_opponent}"
        opponent_text = f"{text_opponent}\n{text_challenger}"
        
        # Edit challenger's message
        if battle.get("move_msg_challenger"):
            try:
                await bot.edit_message(battle["challenger"], battle["move_msg_challenger"], challenger_text)
            except Exception as e:
                print(f"Final challenger msg edit failed: {e}")
        
        # Edit opponent's message
        if battle.get("move_msg_opponent"):
            try:
                await bot.edit_message(battle["opponent"], battle["move_msg_opponent"], opponent_text)
            except Exception as e:
                print(f"Final opponent msg edit failed: {e}")
        
        # Reset moves for next turn
        battle["pending_moves"] = {"challenger": None, "opponent": None}
        
        # TODO: Call function to check fainted Pokémon, switch, or continue turn
        
print("Bot running...")
bot.run_until_disconnected()
