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

battles_db = db["battles"]

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

    battles_db.delete_many({})

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

# -------------------------------

# BATTLE SYSTEM WITH DOUBLES SUPPORT

# -------------------------------

import uuid

from math import ceil

from telethon import events, Button

# In-memory battles (renamed to avoid conflict with MongoDB collection)

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

    # Set active Pokémon based on battle type

    if battle["type"] == "singles":

        # Singles: first Pokemon in team

        if battle["battle_state"]["challenger"] and battle["battle_state"]["opponent"]:

            battle["active"] = {

                "challenger": [battle["battle_state"]["challenger"][0]],

                "opponent": [battle["battle_state"]["opponent"][0]]

            }

    elif battle["type"] == "doubles":

        # Doubles: first two Pokemon in team

        if len(battle["battle_state"]["challenger"]) >= 2 and len(battle["battle_state"]["opponent"]) >= 2:

            battle["active"] = {

                "challenger": battle["battle_state"]["challenger"][:2],

                "opponent": battle["battle_state"]["opponent"][:2]

            }

        else:

            return False  # Not enough Pokemon for doubles

    return True

def get_hp_bar(current, max_hp, length=10):

    """Generate a simple text HP bar."""

    if max_hp <= 0:

        return "▱" * length

    ratio = current / max_hp

    filled = ceil(ratio * length)

    empty = length - filled

    return "▰" * filled + "▱" * empty

def create_battle(challenger_id, opponent_id, battle_type):

    bid = f"BATTLE-{uuid.uuid4().hex[:6].upper()}"

    battle_storage[bid] = {

        "id": bid,

        "challenger": challenger_id,

        "opponent": opponent_id,

        "type": battle_type,

        "state": "pending",

        "pending_action": {"challenger": {}, "opponent": {}},  # Will store multiple actions for doubles

        "forced_switch": {"challenger": [], "opponent": []},    # Track which positions need switches

        "turn": 1,

        "message_ids": {"challenger": None, "opponent": None} # Track message IDs

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

    # Build text WITHOUT damage numbers

    text = f"{attacker['name']} used {move.get('Name', move_key)}!\n"

    if crit > 1.0:

        text += "A critical hit!\n"

    if phrase:

        text += f"{phrase}\n"

    return damage, text

def get_perspective_name(pokemon_name, side, perspective):

    """Get the appropriate name for a Pokemon based on perspective."""

    if side == perspective:

        return pokemon_name

    else:

        return f"Opposing {pokemon_name}"

async def send_battle_ui(bid, battle_texts=None, buttons=None):

    battle = battle_storage.get(bid)

    if not battle or "active" not in battle:

        return

    def hp_bar(current, max_hp, length=15):

        filled = int(length * current / max_hp) if max_hp > 0 else 0

        return "▰" * filled + "▱" * (length - filled)

    # Build UI based on battle type

    if battle["type"] == "singles":

        challenger = battle["active"]["challenger"][0]

        opponent = battle["active"]["opponent"][0]

        challenger_fainted = challenger["hp"] <= 0

        opponent_fainted = opponent["hp"] <= 0

        # Build challenger UI

        c_text = (

            f"⚔️ Singles Battle Turn {battle.get('turn', 1)}\n\n"

            f"{challenger['name']}: {challenger['hp']}/{challenger['max_hp']} HP\n"

            f"{hp_bar(challenger['hp'], challenger['max_hp'])}\n\n"

            f"Opposing {opponent['name']}: {opponent['hp']}/{opponent['max_hp']} HP\n"

            f"{hp_bar(opponent['hp'], opponent['max_hp'])}"

        )

        # Build opponent UI

        o_text = (

            f"⚔️ Singles Battle Turn {battle.get('turn', 1)}\n\n"

            f"{opponent['name']}: {opponent['hp']}/{opponent['max_hp']} HP\n"

            f"{hp_bar(opponent['hp'], opponent['max_hp'])}\n\n"

            f"Opposing {challenger['name']}: {challenger['hp']}/{challenger['max_hp']} HP\n"

            f"{hp_bar(challenger['hp'], challenger['max_hp'])}"

        )

        # Buttons for singles

        c_buttons = []

        o_buttons = []

        if challenger_fainted or len(battle["forced_switch"]["challenger"]) > 0:

            c_text += "\n\n💀 Your Pokémon fainted! Choose a replacement:"

            team = battle["battle_state"]["challenger"]

            for idx, pkm in enumerate(team):

                if pkm["hp"] > 0 and pkm["id"] != challenger["id"]:

                    c_buttons.append([Button.inline(

                        f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",

                        f"battle:forced_switch:{bid}:challenger:0:{idx}"

                    )])

        elif battle["state"] == "active" and buttons == True:

            for move in challenger.get("moves", []):

                c_buttons.append([Button.inline(move, f"battle:move:{bid}:0:{move}:0")])

            c_buttons.append([

                Button.inline("🔄 Switch", f"battle:switch:{bid}:challenger:0"),

                Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")

            ])

        if opponent_fainted or len(battle["forced_switch"]["opponent"]) > 0:

            o_text += "\n\n💀 Your Pokémon fainted! Choose a replacement:"

            team = battle["battle_state"]["opponent"]

            for idx, pkm in enumerate(team):

                if pkm["hp"] > 0 and pkm["id"] != opponent["id"]:

                    o_buttons.append([Button.inline(

                        f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",

                        f"battle:forced_switch:{bid}:opponent:0:{idx}"

                    )])

        elif battle["state"] == "active" and buttons == True:

            for move in opponent.get("moves", []):

                o_buttons.append([Button.inline(move, f"battle:move:{bid}:0:{move}:0")])

            o_buttons.append([

                Button.inline("🔄 Switch", f"battle:switch:{bid}:opponent:0"),

                Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")

            ])

    else:  # doubles

        challenger_1 = battle["active"]["challenger"][0]

        challenger_2 = battle["active"]["challenger"][1]

        opponent_1 = battle["active"]["opponent"][0]

        opponent_2 = battle["active"]["opponent"][1]

        # Build challenger UI for doubles

        c_text = (

            f"⚔️ Doubles Battle Turn {battle.get('turn', 1)}\n\n"

            f"Your Team:\n"

            f"1. {challenger_1['name']}: {challenger_1['hp']}/{challenger_1['max_hp']} HP\n"

            f"   {hp_bar(challenger_1['hp'], challenger_1['max_hp'])}\n"

            f"2. {challenger_2['name']}: {challenger_2['hp']}/{challenger_2['max_hp']} HP\n"

            f"   {hp_bar(challenger_2['hp'], challenger_2['max_hp'])}\n\n"

            f"Opponent Team:\n"

            f"1. Opposing {opponent_1['name']}: {opponent_1['hp']}/{opponent_1['max_hp']} HP\n"

            f"   {hp_bar(opponent_1['hp'], opponent_1['max_hp'])}\n"

            f"2. Opposing {opponent_2['name']}: {opponent_2['hp']}/{opponent_2['max_hp']} HP\n"

            f"   {hp_bar(opponent_2['hp'], opponent_2['max_hp'])}"

        )

        # Build opponent UI for doubles

        o_text = (

            f"⚔️ Doubles Battle Turn {battle.get('turn', 1)}\n\n"

            f"Your Team:\n"

            f"1. {opponent_1['name']}: {opponent_1['hp']}/{opponent_1['max_hp']} HP\n"

            f"   {hp_bar(opponent_1['hp'], opponent_1['max_hp'])}\n"

            f"2. {opponent_2['name']}: {opponent_2['hp']}/{opponent_2['max_hp']} HP\n"

            f"   {hp_bar(opponent_2['hp'], opponent_2['max_hp'])}\n\n"

            f"Opponent Team:\n"

            f"1. Opposing {challenger_1['name']}: {challenger_1['hp']}/{challenger_1['max_hp']} HP\n"

            f"   {hp_bar(challenger_1['hp'], challenger_1['max_hp'])}\n"

            f"2. Opposing {challenger_2['name']}: {challenger_2['hp']}/{challenger_2['max_hp']} HP\n"

            f"   {hp_bar(challenger_2['hp'], challenger_2['max_hp'])}"

        )

        # Buttons for doubles

        c_buttons = []

        o_buttons = []

        # Check for forced switches

        if len(battle["forced_switch"]["challenger"]) > 0:

            c_text += f"\n\n💀 Choose replacement for position {battle['forced_switch']['challenger'][0] + 1}:"

            team = battle["battle_state"]["challenger"]

            active_ids = [p["id"] for p in battle["active"]["challenger"]]

            for idx, pkm in enumerate(team):

                if pkm["hp"] > 0 and pkm["id"] not in active_ids:

                    c_buttons.append([Button.inline(

                        f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",

                        f"battle:forced_switch:{bid}:challenger:{battle['forced_switch']['challenger'][0]}:{idx}"

                    )])

        elif battle["state"] == "active" and buttons == True:

            # Action selection for doubles

            if len(battle["pending_action"]["challenger"]) == 0:

                c_text += "\n\nChoose action for Pokémon 1:"

                c_buttons.append([Button.inline("🎯 Select Move", f"battle:select_pokemon:{bid}:challenger:0")])

                c_buttons.append([Button.inline("🔄 Switch", f"battle:switch:{bid}:challenger:0")])

            elif len(battle["pending_action"]["challenger"]) == 1:

                c_text += "\n\nChoose action for Pokémon 2:"

                c_buttons.append([Button.inline("🎯 Select Move", f"battle:select_pokemon:{bid}:challenger:1")])

                c_buttons.append([Button.inline("🔄 Switch", f"battle:switch:{bid}:challenger:1")])

            c_buttons.append([Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")])

        if len(battle["forced_switch"]["opponent"]) > 0:

            o_text += f"\n\n💀 Choose replacement for position {battle['forced_switch']['opponent'][0] + 1}:"

            team = battle["battle_state"]["opponent"]

            active_ids = [p["id"] for p in battle["active"]["opponent"]]

            for idx, pkm in enumerate(team):

                if pkm["hp"] > 0 and pkm["id"] not in active_ids:

                    o_buttons.append([Button.inline(

                        f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",

                        f"battle:forced_switch:{bid}:opponent:{battle['forced_switch']['opponent'][0]}:{idx}"

                    )])

        elif battle["state"] == "active" and buttons == True:

            # Action selection for doubles

            if len(battle["pending_action"]["opponent"]) == 0:

                o_text += "\n\nChoose action for Pokémon 1:"

                o_buttons.append([Button.inline("🎯 Select Move", f"battle:select_pokemon:{bid}:opponent:0")])

                o_buttons.append([Button.inline("🔄 Switch", f"battle:switch:{bid}:opponent:0")])

            elif len(battle["pending_action"]["opponent"]) == 1:

                o_text += "\n\nChoose action for Pokémon 2:"

                o_buttons.append([Button.inline("🎯 Select Move", f"battle:select_pokemon:{bid}:opponent:1")])

                o_buttons.append([Button.inline("🔄 Switch", f"battle:switch:{bid}:opponent:1")])

            o_buttons.append([Button.inline("🏳️ Forfeit", f"battle:forfeit:{bid}")])

    # Add battle text if provided

    if battle_texts:

        if "challenger" in battle_texts:

            c_text += f"\n\n{battle_texts['challenger']}"

        if "opponent" in battle_texts:

            o_text += f"\n\n{battle_texts['opponent']}"

    # Update messages

    try:

        if battle["message_ids"]["challenger"] and buttons == True:

            await bot.edit_message(battle["challenger"], battle["message_ids"]["challenger"], c_text, buttons=c_buttons)

        elif battle["message_ids"]["challenger"] and buttons == False:

            await bot.edit_message(battle["challenger"], battle["message_ids"]["challenger"], c_text)

        else:

            if buttons == True and battle.get('turn', 1) == 1:

                msg = await bot.send_message(battle["challenger"], c_text, buttons=c_buttons)

                battle["message_ids"]["challenger"] = msg.id

        if battle["message_ids"]["opponent"] and buttons == True:

            await bot.edit_message(battle["opponent"], battle["message_ids"]["opponent"], o_text, buttons=o_buttons)

        elif battle["message_ids"]["opponent"] and buttons == False:

            await bot.edit_message(battle["opponent"], battle["message_ids"]["opponent"], o_text)

        else:

            if buttons == True and battle.get('turn', 1) == 1:

                msg = await bot.send_message(battle["opponent"], o_text, buttons=o_buttons)

                battle["message_ids"]["opponent"] = msg.id

    except Exception as e:

        print(f"UI update failed: {e}")

async def animate_battle_sequence(bid, actions_results):

    """

    Animate the battle sequence step by step with perspective-aware texts.

    actions_results = [(action_text_challenger, action_text_opponent, hp_changes), ...]

    """

    battle = battle_storage.get(bid)

    if not battle:

        return

    # Process each action with animation

    for i, (text_challenger, text_opponent, hp_changes) in enumerate(actions_results):

        # Show action text

        battle_texts = {

            "challenger": text_challenger,

            "opponent": text_opponent

        }

        await send_battle_ui(bid, battle_texts, buttons=False)

        await asyncio.sleep(1.5) # Animation delay

        # Apply HP changes if any

        if hp_changes:

            for key, damage in hp_changes.items():

                if damage > 0:

                    side, pos = key.split("_")

                    pos = int(pos)

                    battle["active"][side][pos]["hp"] = max(0, battle["active"][side][pos]["hp"] - damage)

        # Update UI with HP changes

        await send_battle_ui(bid, battle_texts, buttons=False)

        if i < len(actions_results) - 1: # Not the last action

            await asyncio.sleep(1.0)

async def process_doubles_action(battle, side, pos, action, target_pos):

    """Process one action in doubles: move or switch. Returns perspective texts and damage info."""

    if action.startswith("switch:"):

        # Extract Pokémon index

        try:

            idx = int(action.split(":")[1])

            old_pkm = battle["active"][side][pos]

            new_pkm = battle["battle_state"][side][idx]

            if new_pkm["hp"] <= 0:

                base_text = f"{new_pkm['name']} has fainted and cannot battle!"

                return base_text, base_text, {}

            battle["active"][side][pos] = new_pkm

            base_text = f"{new_pkm['name']} was switched in!"

            return base_text, base_text, {}

        except (IndexError, ValueError, KeyError):

            base_text = "❌ Switch failed - invalid Pokémon selection!"

            return base_text, base_text, {}

    else:

        # Regular move

        try:

            attacker = battle["active"][side][pos]

            

            # Determine target based on target_pos

            if target_pos == 0:  # challenger pos 0

                defender = battle["active"]["challenger"][0]

                target_side = "challenger"

                target_position = 0

            elif target_pos == 1:  # challenger pos 1

                defender = battle["active"]["challenger"][1]

                target_side = "challenger"

                target_position = 1

            elif target_pos == 2:  # opponent pos 0

                defender = battle["active"]["opponent"][0]

                target_side = "opponent"

                target_position = 0

            elif target_pos == 3:  # opponent pos 1

                defender = battle["active"]["opponent"][1]

                target_side = "opponent"

                target_position = 1

            else:

                return "Invalid target!", "Invalid target!", {}

            if attacker["hp"] <= 0:

                base_text = f"{attacker['name']} has fainted and cannot attack!"

                return base_text, base_text, {}

            if defender["hp"] <= 0:

                base_text = f"{attacker['name']} tried to attack, but the target has already fainted!"

                return base_text, base_text, {}

            dmg, base_text = calculate_damage(attacker, defender, action)

            # Build perspective texts

            challenger_attacker = get_perspective_name(attacker["name"], side, "challenger")

            challenger_defender = get_perspective_name(defender["name"], target_side, "challenger")

            

            opponent_attacker = get_perspective_name(attacker["name"], side, "opponent")

            opponent_defender = get_perspective_name(defender["name"], target_side, "opponent")

            text_challenger = base_text.replace(attacker["name"], challenger_attacker, 1).replace(defender["name"], challenger_defender)

            text_opponent = base_text.replace(attacker["name"], opponent_attacker, 1).replace(defender["name"], opponent_defender)

            # Return damage info for HP changes

            hp_changes = {f"{target_side}_{target_position}": dmg} if dmg > 0 else {}

            return text_challenger, text_opponent, hp_changes

        except Exception as e:

            print(f"Move processing error: {e}")

            base_text = f"{battle['active'][side][pos]['name']} used {action}!\nBut something went wrong!"

            return base_text, base_text, {}

async def resolve_doubles_turn(bid):

    """Resolve a full doubles turn with animation."""

    battle = battle_storage.get(bid)

    if not battle:

        return

    # Get all actions

    challenger_actions = battle["pending_action"]["challenger"]

    opponent_actions = battle["pending_action"]["opponent"]

    # Ensure both sides have chosen actions for all active Pokemon

    if len(challenger_actions) < 2 or len(opponent_actions) < 2:

        return

    # Collect all actions with speed for ordering

    all_actions = []

    

    # Add challenger actions

    for pos, action_data in challenger_actions.items():

        speed = battle["active"]["challenger"][pos].get("spe", 0)

        all_actions.append((speed, "challenger", pos, action_data))

    

    # Add opponent actions  

    for pos, action_data in opponent_actions.items():

        speed = battle["active"]["opponent"][pos].get("spe", 0)

        all_actions.append((speed, "opponent", pos, action_data))

    # Sort by speed (highest first), with switches going first

    def action_priority(action):

        speed, side, pos, action_data = action

        # Switches go first

        if action_data["action"].startswith("switch:"):

            return (1, -speed)  # Higher priority, then by reverse speed

        else:

            return (0, -speed)  # Lower priority, then by reverse speed

    all_actions.sort(key=action_priority, reverse=True)

    actions_results = []

    # Process each action in order

    for speed, side, pos, action_data in all_actions:

        action = action_data["action"]

        target = action_data.get("target", 0)

        

        # Check if the Pokemon is still able to act

        if battle["active"][side][pos]["hp"] <= 0:

            base_text = f"{battle['active'][side][pos]['name']} has fainted and cannot act!"

            actions_results.append((base_text, base_text, {}))

            continue

        text_chal, text_opp, hp_changes = await process_doubles_action(

            battle, side, pos, action, target

        )

        actions_results.append((text_chal, text_opp, hp_changes))

        # Apply damage immediately to affect subsequent actions in the same turn

        if hp_changes:

            for key, damage in hp_changes.items():

                if damage > 0:

                    target_side, target_pos = key.split("_")

                    target_pos = int(target_pos)

                    current_hp = battle["active"][target_side][target_pos]["hp"]

                    new_hp = max(0, current_hp - damage)

                    battle["active"][target_side][target_pos]["hp"] = new_hp

                    

                    # Check if target fainted

                    if new_hp <= 0:

                        battle["forced_switch"][target_side].append(target_pos)

    # Animate the entire sequence

    await animate_battle_sequence(bid, actions_results)

    # Clear pending actions for next turn

    battle["pending_action"] = {"challenger": {}, "opponent": {}}

    battle["turn"] = battle.get("turn", 1) + 1

    # Check for battle end conditions

    challenger_healthy = [p for p in battle["battle_state"]["challenger"] if p["hp"] > 0]

    opponent_healthy = [p for p in battle["battle_state"]["opponent"] if p["hp"] > 0]

    if len(challenger_healthy) == 0:

        await end_battle(bid, "opponent")

        return

    elif len(opponent_healthy) == 0:

        await end_battle(bid, "challenger")

        return

    elif len(challenger_healthy) < 2 or len(opponent_healthy) < 2:

        # Switch to singles if one side has only 1 Pokemon left

        battle["type"] = "singles"

        

        # Set active Pokemon to the remaining healthy ones

        if len(challenger_healthy) >= 1:

            battle["active"]["challenger"] = [challenger_healthy[0]]

        if len(opponent_healthy) >= 1:

            battle["active"]["opponent"] = [opponent_healthy[0]]

    # Refresh battle UI for next turn

    await send_battle_ui(bid, buttons=True)

async def resolve_singles_turn(bid):

    """Resolve a singles turn (existing logic)."""

    battle = battle_storage.get(bid)

    if not battle:

        return

    # Get actions

    challenger_action = battle["pending_action"]["challenger"].get(0, {}).get("action")

    opponent_action = battle["pending_action"]["opponent"].get(0, {}).get("action")

    # Ensure both sides have chosen an action

    if not challenger_action or not opponent_action:

        return

    # Determine order by speed if both are moves

    challenger_speed = battle["active"]["challenger"][0].get("spe", 0)

    opponent_speed = battle["active"]["opponent"][0].get("spe", 0)

    # Switches typically go first, then by speed

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

    actions_results = []

    # Process first action

    first_other = "opponent" if first == "challenger" else "challenger"

    text_chal_1, text_opp_1, hp_changes_1 = await process_singles_action(

        battle, first, first_other, battle["pending_action"][first][0]["action"]

    )

    actions_results.append((text_chal_1, text_opp_1, hp_changes_1))

    # Check if defender fainted after first move

    defender_fainted = False

    if hp_changes_1 and f"{first_other}_0" in hp_changes_1:

        # Apply damage to check faint

        current_hp = battle["active"][first_other][0]["hp"]

        damage = hp_changes_1[f"{first_other}_0"]

        if current_hp - damage <= 0:

            defender_fainted = True

            battle["forced_switch"][first_other].append(0)

            # Add faint message

            fainted_name = battle["active"][first_other][0]["name"]

            base_faint_text = f"{fainted_name} fainted and couldn't use its move!"

            actions_results.append((base_faint_text, base_faint_text, {}))

    # Process second action only if defender didn't faint

    if not defender_fainted:

        second_other = "challenger" if second == "opponent" else "opponent"

        text_chal_2, text_opp_2, hp_changes_2 = await process_singles_action(

            battle, second, second_other, battle["pending_action"][second][0]["action"]

        )

        actions_results.append((text_chal_2, text_opp_2, hp_changes_2))

        # Check if first attacker fainted from second move

        if hp_changes_2 and f"{first}_0" in hp_changes_2:

            current_hp = battle["active"][first][0]["hp"]

            damage = hp_changes_2[f"{first}_0"]

            if current_hp - damage <= 0:

                battle["forced_switch"][first].append(0)

    # Animate the entire sequence

    await animate_battle_sequence(bid, actions_results)

    # Clear pending actions for next turn

    battle["pending_action"] = {"challenger": {}, "opponent": {}}

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

    # Refresh battle UI for next turn

    await send_battle_ui(bid, buttons=True)

async def process_singles_action(battle, side, other_side, action):

    """Process one action in singles: move or switch. Returns perspective texts and damage info."""

    if action.startswith("switch:"):

        # Extract Pokémon index

        try:

            idx = int(action.split(":")[1])

            old_pkm = battle["active"][side][0]

            new_pkm = battle["battle_state"][side][idx]

            if new_pkm["hp"] <= 0:

                base_text = f"{new_pkm['name']} has fainted and cannot battle!"

                return base_text, base_text, {}

            battle["active"][side][0] = new_pkm

            base_text = f"{new_pkm['name']} was switched in!"

            return base_text, base_text, {}

        except (IndexError, ValueError, KeyError):

            base_text = "❌ Switch failed - invalid Pokémon selection!"

            return base_text, base_text, {}

    else:

        # Regular move

        try:

            attacker = battle["active"][side][0]

            defender = battle["active"][other_side][0]

            if attacker["hp"] <= 0:

                base_text = f"{attacker['name']} has fainted and cannot attack!"

                return base_text, base_text, {}

            dmg, base_text = calculate_damage(attacker, defender, action)

            # Build perspective texts

            challenger_attacker = get_perspective_name(attacker["name"], side, "challenger")

            challenger_defender = get_perspective_name(defender["name"], other_side, "challenger")

            

            opponent_attacker = get_perspective_name(attacker["name"], side, "opponent")

            opponent_defender = get_perspective_name(defender["name"], other_side, "opponent")

            text_challenger = base_text.replace(attacker["name"], challenger_attacker, 1).replace(defender["name"], challenger_defender)

            text_opponent = base_text.replace(attacker["name"], opponent_attacker, 1).replace(defender["name"], opponent_defender)

            # Return damage info for HP changes

            hp_changes = {f"{other_side}_0": dmg} if dmg > 0 else {}

            return text_challenger, text_opponent, hp_changes

        except Exception as e:

            print(f"Move processing error: {e}")

            base_text = f"{battle['active'][side][0]['name']} used {action}!\nBut something went wrong!"

            return base_text, base_text, {}

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

    await send_battle_ui(bid, buttons=True)

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

@bot.on(events.CallbackQuery(pattern=b"battle:forced_switch:(.+):(.+):(.+):(.+)"))

async def cb_forced_switch(event):

    bid = event.pattern_match.group(1).decode()

    side = event.pattern_match.group(2).decode()

    pos = int(event.pattern_match.group(3).decode())

    idx = int(event.pattern_match.group(4).decode())

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

        # Check if Pokemon is already active

        active_ids = [p["id"] for p in battle["active"][side]]

        if target_pokemon["id"] in active_ids:

            return await event.answer("❌ That Pokémon is already active!", alert=True)

    except (IndexError, KeyError):

        return await event.answer("❌ Invalid Pokémon selection!", alert=True)

    # Perform the forced switch

    battle["active"][side][pos] = target_pokemon

    

    # Remove this position from forced switches

    if pos in battle["forced_switch"][side]:

        battle["forced_switch"][side].remove(pos)

    await event.edit(f"✅ {target_pokemon['name']} was sent out!")

    # Check if both sides are ready (no forced switches needed)

    if not battle["forced_switch"]["challenger"] and not battle["forced_switch"]["opponent"]:

        await send_battle_ui(bid, buttons=True)

# Pokemon selection for move (doubles)

@bot.on(events.CallbackQuery(pattern=b"battle:select_pokemon:(.+):(.+):(.+)"))

async def cb_select_pokemon(event):

    bid = event.pattern_match.group(1).decode()

    side = event.pattern_match.group(2).decode()

    pos = int(event.pattern_match.group(3).decode())

    battle = battle_storage.get(bid)

    if not battle:

        return await event.answer("❌ Battle not found.", alert=True)

    user_id = event.sender_id

    expected_side = "challenger" if user_id == battle["challenger"] else "opponent"

    if side != expected_side:

        return await event.answer("❌ Invalid request.", alert=True)

    # Show move selection for this Pokemon

    active_pokemon = battle["active"][side][pos]

    if active_pokemon["hp"] <= 0:

        return await event.answer("❌ That Pokémon has fainted!", alert=True)

    text = f"Select a move for {active_pokemon['name']}:"

    buttons = []

    for move in active_pokemon.get("moves", []):

        buttons.append([Button.inline(move, f"battle:move_select:{bid}:{pos}:{move}")])

    buttons.append([Button.inline("⬅️ Back", f"battle:back_to_action:{bid}:{side}")])

    await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"battle:move_select:(.+):(.+):(.+)"))

async def cb_move_select(event):

    bid = event.pattern_match.group(1).decode()

    pos = int(event.pattern_match.group(2).decode())

    move = event.pattern_match.group(3).decode()

    battle = battle_storage.get(bid)

    if not battle:

        return await event.answer("❌ Battle not found.", alert=True)

    user_id = event.sender_id

    side = "challenger" if user_id == battle["challenger"] else "opponent"

    # Show target selection

    if battle["type"] == "singles":

        # Singles: only one target

        target = 2 if side == "challenger" else 0  # opponent's position

        battle["pending_action"][side][pos] = {"action": move, "target": target}

        await event.edit("Move registered! Waiting for opponent...")

        

        # Check if both players have selected actions

        if len(battle["pending_action"]["challenger"]) > 0 and len(battle["pending_action"]["opponent"]) > 0:

            await resolve_singles_turn(bid)

    else:

        # Doubles: show target selection

        text = f"Select target for {move}:"

        buttons = []

        

        # All 4 positions as targets

        if side == "challenger":

            buttons.append([Button.inline(f"Your {battle['active']['challenger'][0]['name']}", f"battle:target:{bid}:{pos}:{move}:0")])

            buttons.append([Button.inline(f"Your {battle['active']['challenger'][1]['name']}", f"battle:target:{bid}:{pos}:{move}:1")])

            buttons.append([Button.inline(f"Opp {battle['active']['opponent'][0]['name']}", f"battle:target:{bid}:{pos}:{move}:2")])

            buttons.append([Button.inline(f"Opp {battle['active']['opponent'][1]['name']}", f"battle:target:{bid}:{pos}:{move}:3")])

        else:

            buttons.append([Button.inline(f"Opp {battle['active']['challenger'][0]['name']}", f"battle:target:{bid}:{pos}:{move}:0")])

            buttons.append([Button.inline(f"Opp {battle['active']['challenger'][1]['name']}", f"battle:target:{bid}:{pos}:{move}:1")])

            buttons.append([Button.inline(f"Your {battle['active']['opponent'][0]['name']}", f"battle:target:{bid}:{pos}:{move}:2")])

            buttons.append([Button.inline(f"Your {battle['active']['opponent'][1]['name']}", f"battle:target:{bid}:{pos}:{move}:3")])

        buttons.append([Button.inline("⬅️ Back", f"battle:select_pokemon:{bid}:{side}:{pos}")])

        await event.edit(text, buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"battle:target:(.+):(.+):(.+):(.+)"))

async def cb_target_select(event):

    bid = event.pattern_match.group(1).decode()

    pos = int(event.pattern_match.group(2).decode())

    move = event.pattern_match.group(3).decode()

    target = int(event.pattern_match.group(4).decode())

    battle = battle_storage.get(bid)

    if not battle:

        return await event.answer("❌ Battle not found.", alert=True)

    user_id = event.sender_id

    side = "challenger" if user_id == battle["challenger"] else "opponent"

    # Register the action

    battle["pending_action"][side][pos] = {"action": move, "target": target}

    await event.edit(f"Move {move} targeted! Waiting for all actions...")

    # Check if all actions are selected

    if battle["type"] == "doubles":

        if len(battle["pending_action"]["challenger"]) == 2 and len(battle["pending_action"]["opponent"]) == 2:

            await resolve_doubles_turn(bid)

        else:

            await send_battle_ui(bid, buttons=True)

@bot.on(events.CallbackQuery(pattern=b"battle:back_to_action:(.+):(.+)"))

async def cb_back_to_action(event):

    bid = event.pattern_match.group(1).decode()

    side = event.pattern_match.group(2).decode()

    await send_battle_ui(bid, buttons=True)

@bot.on(events.CallbackQuery(pattern=b"battle:move:(.+):(.+):(.+):(.+)"))

async def cb_move(event):

    bid = event.pattern_match.group(1).decode()

    pos = int(event.pattern_match.group(2).decode())

    move_selected = event.pattern_match.group(3).decode()

    target = int(event.pattern_match.group(4).decode())

    battle = battle_storage.get(bid)

    if not battle:

        return await event.answer("❌ Battle not found.", alert=True)

    user_id = event.sender_id

    side = "challenger" if user_id == battle["challenger"] else "opponent"

    if pos in battle["forced_switch"][side]:

        return await event.answer("❌ You must choose a replacement Pokémon first!", alert=True)

    active_pokemon = battle["active"][side][pos]

    if move_selected not in active_pokemon.get("moves", []):

        return await event.answer("❌ Your Pokémon doesn't know that move!", alert=True)

    battle["pending_action"][side][pos] = {"action": move_selected, "target": target}

    await event.edit("Move registered! Waiting for opponent...")

    if battle["type"] == "singles":

        if len(battle["pending_action"]["challenger"]) > 0 and len(battle["pending_action"]["opponent"]) > 0:

            await resolve_singles_turn(bid)

    else:

        if len(battle["pending_action"]["challenger"]) == 2 and len(battle["pending_action"]["opponent"]) == 2:

            await resolve_doubles_turn(bid)

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

@bot.on(events.CallbackQuery(pattern=b"battle:switch:(.+):(.+):(.+)"))

async def cb_switch(event):

    bid = event.pattern_match.group(1).decode()

    side = event.pattern_match.group(2).decode()

    pos = int(event.pattern_match.group(3).decode())

    battle = battle_storage.get(bid)

    if not battle:

        return await event.answer("❌ Battle not found.", alert=True)

    user_id = event.sender_id

    expected_side = "challenger" if user_id == battle["challenger"] else "opponent"

    if side != expected_side:

        return await event.answer("❌ Invalid switch request.", alert=True)

    # Check if player needs forced switch first

    if pos in battle["forced_switch"][side]:

        return await event.answer("❌ You must choose a replacement Pokémon first!", alert=True)

    # List the player's team

    team = battle["battle_state"][side]

    active_pokemon = battle["active"][side][pos]

    # Only show Pokémon that are NOT fainted and not already active

    buttons = []

    active_ids = [p["id"] for p in battle["active"][side]]

    for idx, pkm in enumerate(team):

        if pkm["hp"] > 0 and pkm["id"] not in active_ids:

            buttons.append([Button.inline(

                f"{pkm['name']} ({pkm['hp']}/{pkm['max_hp']} HP)",

                f"battle:choose_switch:{bid}:{side}:{pos}:{idx}"

            )])

    if not buttons:

        return await event.answer("⚠ No healthy Pokémon to switch to.", alert=True)

    await event.edit("🔄 Choose a Pokémon to switch in:", buttons=buttons)

@bot.on(events.CallbackQuery(pattern=b"battle:choose_switch:(.+):(.+):(.+):(.+)"))

async def cb_choose_switch(event):

    bid = event.pattern_match.group(1).decode()

    side = event.pattern_match.group(2).decode()

    pos = int(event.pattern_match.group(3).decode())

    idx = int(event.pattern_match.group(4).decode())

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

        active_ids = [p["id"] for p in battle["active"][side]]

        if target_pokemon["id"] in active_ids:

            return await event.answer("❌ That Pokémon is already active!", alert=True)

    except (IndexError, KeyError):

        return await event.answer("❌ Invalid Pokémon selection!", alert=True)

    # Register switch action

    battle["pending_action"][side][pos] = {"action": f"switch:{idx}", "target": 0}

    await event.edit(f"🔄 Switch to {target_pokemon['name']} registered! Waiting for opponent...")

    # If all actions chosen → resolve turn

    if battle["type"] == "singles":

        if len(battle["pending_action"]["challenger"]) > 0 and len(battle["pending_action"]["opponent"]) > 0:

            await resolve_singles_turn(bid)

    else:

        if len(battle["pending_action"]["challenger"]) == 2 and len(battle["pending_action"]["opponent"]) == 2:

            await resolve_doubles_turn(bid)

print("Bot running...")

bot.run_until_disconnected()