import random, json, math, uuid
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
# Utility Functions
# -------------------------------

def create_battle(challenger_id, opponent_id, battle_type):
    battle_id = f"BATTLE-{uuid.uuid4().hex[:6].upper()}"
    battle_data = {
        "_id": battle_id,
        "type": battle_type,
        "challenger": challenger_id,
        "opponent": opponent_id,
        "state": "pending",
        "turn": None,
        "teams": {},
        "log": []
    }
    battles.insert_one(battle_data)
    return battle_id

async def send_challenge(event, challenger, opponent, battle_type):
    battle_id = create_battle(challenger, opponent, battle_type)
    battle_text = f"⚔️ <b>{challenger}</b> has challenged <b>{opponent}</b> to a <i>{battle_type}</i> battle!"
    await event.reply(
        battle_text,
        buttons=[
            [
                Button.inline("✅ Accept", f"battle:accept:{battle_id}"),
                Button.inline("❌ Decline", f"battle:decline:{battle_id}")
            ]
        ]
    )

async def accept_battle(event, battle_id, user_id):
    battle = battles.find_one({"_id": battle_id})
    if not battle or battle["state"] != "pending":
        await event.answer("⚠️ This battle is no longer available.", alert=True)
        return

    if battle["opponent"] != user_id:
        await event.answer("⚠️ Only the challenged player can accept!", alert=True)
        return

    # Update state → active
    battles.update_one({"_id": battle_id}, {"$set": {"state": "active", "turn": battle["challenger"]}})
    
    # Send PMs
    await event.respond(f"✅ Battle started! Check your PMs.")
    await event.client.send_message(battle["challenger"], f"🏟️ Your battle vs {battle['opponent']} has begun!")
    await event.client.send_message(battle["opponent"], f"🏟️ Your battle vs {battle['challenger']} has begun!")

async def decline_battle(event, battle_id, user_id):
    battle = battles.find_one({"_id": battle_id})
    if not battle:
        await event.answer("⚠️ Invalid battle.", alert=True)
        return
    
    battles.update_one({"_id": battle_id}, {"$set": {"state": "cancelled"}})
    await event.respond("❌ Battle was declined.")
# -------------------------------
# Helper to get first Pokémon
# -------------------------------
def get_first_pokemon(user_id):
    user = users.find_one({"user_id": user_id})
    if not user or not user.get("team"):
        return None
    
    poke_id = user["team"][0]
    pokemon = db["pokemon_data"].find_one({"_id": poke_id})
    return pokemon


# -------------------------------
# Start battle in PM
# -------------------------------
async def start_battle_pm(client, battle):
    challenger = battle["challenger"]
    opponent = battle["opponent"]

    # Load first Pokémon
    poke_a = get_first_pokemon(challenger)
    poke_b = get_first_pokemon(opponent)

    # Update DB with active Pokémon
    battles.update_one(
        {"_id": battle["_id"]},
        {"$set": {
            "active_pokemon": {
                "challenger": poke_a["_id"],
                "opponent": poke_b["_id"]
            },
            "turn": challenger  # challenger starts
        }}
    )

    # Send PM to both players
    await show_pokemon_ui(client, challenger, poke_a, battle["_id"])
    await show_pokemon_ui(client, opponent, poke_b, battle["_id"])

# ----------------------------
# Utility: Create HP bar
# ----------------------------
def make_hp_bar(current_hp, max_hp, length=10):
    filled = int((current_hp / max_hp) * length)
    empty = length - filled
    bar = "█" * filled + "░" * empty
    percent = int((current_hp / max_hp) * 100)
    return f"{bar} {percent}%"

# ----------------------------
# Battle UI
# ----------------------------
async def show_battle_ui(bot, player, opponent, player_poke, opp_poke):
    # HP bars
    player_hp = make_hp_bar(player_poke['hp'], player_poke['max_hp'])
    opp_hp = make_hp_bar(opp_poke['hp'], opp_poke['max_hp'])

    # Message
    text = (
        f"⚔️ **Battle Started!** ⚔️\n\n"
        f"👤 {player.first_name}'s Pokémon:\n"
        f"{player_poke['name']} HP: {player_hp}\n\n"
        f"👤 {opponent.first_name}'s Pokémon:\n"
        f"{opp_poke['name']} HP: {opp_hp}"
    )

    # Move buttons (4 moves)
    move_buttons = [
        [Button.inline(player_poke['moves'][0], data=f"move:{player.id}:0"),
         Button.inline(player_poke['moves'][1], data=f"move:{player.id}:1")],
        [Button.inline(player_poke['moves'][2], data=f"move:{player.id}:2"),
         Button.inline(player_poke['moves'][3], data=f"move:{player.id}:3")],
    ]

    # Extra buttons (Switch + Forfeit)
    extra_buttons = [
        [Button.inline("🔄 Switch", data=f"switch:{player.id}"),
         Button.inline("🏳️ Forfeit", data=f"forfeit:{player.id}")]
    ]

    # Send UI
    await bot.send_message(
        player.id,
        text,
        buttons=move_buttons + extra_buttons
    )

# -------------------------------
# Extend accept_battle to call start_battle_pm
# -------------------------------
async def accept_battle(event, battle_id, user_id):
    battle = battles.find_one({"_id": battle_id})
    if not battle or battle["state"] != "pending":
        await event.answer("⚠️ This battle is no longer available.", alert=True)
        return

    if battle["opponent"] != user_id:
        await event.answer("⚠️ Only the challenged player can accept!", alert=True)
        return

    # Update state → active
    battles.update_one({"_id": battle_id}, {"$set": {"state": "active"}})
    
    # Send PMs + start battle
    await event.respond("✅ Battle started! Check your PMs.")
    battle = battles.find_one({"_id": battle_id})  # refresh
    await start_battle_pm(event.client, battle)
# -------------------------------
# Command Handlers
# -------------------------------

@bot.on(events.NewMessage(pattern="/battleS"))
async def battle_singles(event):
    if not event.is_reply:
        await event.reply("⚠️ Reply to a user’s message to challenge them.")
        return
    
    opponent = (await event.get_reply_message()).sender_id
    challenger = event.sender_id

    if challenger == opponent:
        await event.reply("⚠️ You can’t battle yourself!")
        return

    await send_challenge(event, challenger, opponent, "singles")

@bot.on(events.NewMessage(pattern="/battleD"))
async def battle_doubles(event):
    if not event.is_reply:
        await event.reply("⚠️ Reply to a user’s message to challenge them.")
        return
    
    opponent = (await event.get_reply_message()).sender_id
    challenger = event.sender_id

    if challenger == opponent:
        await event.reply("⚠️ You can’t battle yourself!")
        return

    await send_challenge(event, challenger, opponent, "doubles")

# -------------------------------
# Button Callbacks
# -------------------------------

@bot.on(events.CallbackQuery(pattern=b"battle:accept:(.+)"))
async def on_accept(event):
    battle_id = event.pattern_match.group(1).decode("utf-8")
    await accept_battle(event, battle_id, event.sender_id)

@bot.on(events.CallbackQuery(pattern=b"battle:decline:(.+)"))
async def on_decline(event):
    battle_id = event.pattern_match.group(1).decode("utf-8")
    await decline_battle(event, battle_id, event.sender_id)
    
print("Bot running...")
bot.run_until_disconnected()
