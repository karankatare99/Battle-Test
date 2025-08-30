import random
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
    if not lines:
        return {}

    pokemon = {}
    evs = {s: 0 for s in ["hp","atk","def","spa","spd","spe"]}
    ivs = {s: 31 for s in ["hp","atk","def","spa","spd","spe"]}

    # FIX: use the first line of the text
    first_line = lines.strip()
    if "(M)" in first_line:
        gender = "Male"; first_line = first_line.replace("(M)", "").strip()
    elif "(F)" in first_line:
        gender = "Female"; first_line = first_line.replace("(F)", "").strip()
    else:
        gender = random.choice(["Male","Female"])

    if "@" in first_line:
        name_part, item = first_line.split("@", 1)
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
        if not line:
            continue
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
        elif "Nature" in line:
            # Accept "Jolly Nature" or "Nature: Jolly"
            pokemon["nature"] = line.replace("Nature", "").replace(":", "").strip()
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

    pokemon["pokemon_id"] = generate_pokemon_id()
    return pokemon

# ==== NEW: Base stats + nature + stat calc ===================================
# HP: floor(((2B + I + floor(E/4)) * L)/100) + L + 10
# Other: floor((floor(((2B + I + floor(E/4)) * L)/100) + 5) * N)
# N = 1.1 / 1.0 / 0.9; Shedinja HP = 1. [Gen 3+]
BASE_STATS = {
    # Minimal examples; extend or load from DB
    "pikachu":   {"hp":35, "atk":55,  "def":40, "spa":50,  "spd":50,  "spe":90},
    "charizard": {"hp":78, "atk":84,  "def":78, "spa":109, "spd":85,  "spe":100},
    "shedinja":  {"hp":1,  "atk":90,  "def":45, "spa":30,  "spd":30,  "spe":40},
    "ceruledge": {"hp":75, "atk":125, "def":80, "spa":60,  "spd":100, "spe":85},
}

def nature_multipliers(nature_name: str):
    name = (nature_name or "None").strip().lower()
    inc_dec = {
        "lonely": ("atk","def"),
        "adamant": ("atk","spa"),
        "naughty": ("atk","spd"),
        "brave": ("atk","spe"),
        "bold": ("def","atk"),
        "impish": ("def","spa"),
        "lax": ("def","spd"),
        "relaxed": ("def","spe"),
        "modest": ("spa","atk"),
        "mild": ("spa","def"),
        "rash": ("spa","spd"),
        "quiet": ("spa","spe"),
        "calm": ("spd","atk"),
        "gentle": ("spd","def"),
        "careful": ("spd","spa"),
        "sassy": ("spd","spe"),
        "timid": ("spe","atk"),
        "hasty": ("spe","def"),
        "jolly": ("spe","spa"),
        "naive": ("spe","spd"),
        # neutral
        "hardy": None, "docile": None, "bashful": None, "quirky": None, "serious": None, "none": None
    }

    mult = {"atk":1.0,"def":1.0,"spa":1.0,"spd":1.0,"spe":1.0}
    pair = inc_dec.get(name)
    if pair:
        up, down = pair
        mult[up] = 1.1
        mult[down] = 0.9
    return mult

def normalize_species(name: str):
    return (name or "").strip().lower()

def get_base_stats(species_name: str):
    return BASE_STATS.get(normalize_species(species_name))

def clamp(v, lo, hi):
    try:
        v = int(v)
    except:
        v = lo
    return max(lo, min(hi, v))

def calc_stats(species_name: str, level: int, evs: dict, ivs: dict, nature_name: str):
    base = get_base_stats(species_name)
    if not base:
        return None

    L = int(level or 100)
    E = {k: clamp(evs.get(k, 0), 0, 252) for k in ["hp","atk","def","spa","spd","spe"]}
    I = {k: clamp(ivs.get(k, 31), 0, 31) for k in ["hp","atk","def","spa","spd","spe"]}
    mult = nature_multipliers(nature_name)

    # HP
    if normalize_species(species_name) == "shedinja":
        stat_hp = 1
    else:
        stat_hp = ((2*base["hp"] + I["hp"] + (E["hp"]//4)) * L) // 100 + L + 10

    # Other stats
    def other(k):
        base_term = ((2*base[k] + I[k] + (E[k]//4)) * L) // 100 + 5
        return int(base_term * mult.get(k, 1.0))

    stat_atk = other("atk")
    stat_def = other("def")
    stat_spa = other("spa")
    stat_spd = other("spd")
    stat_spe = other("spe")

    total = stat_hp + stat_atk + stat_def + stat_spa + stat_spd + stat_spe
    return {
        "stat_hp": stat_hp,
        "stat_atk": stat_atk,
        "stat_def": stat_def,
        "stat_spa": stat_spa,
        "stat_spd": stat_spd,
        "stat_spe": stat_spe,
        "total_stats_sum": total,
    }
# ==== END NEW ================================================================

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

        # Compute calculated stats and attach before saving
        evs = {k: pokemon.get(f"ev{k}", 0) for k in ["hp","atk","def","spa","spd","spe"]}
        ivs = {k: pokemon.get(f"iv{k}", 31) for k in ["hp","atk","def","spa","spd","spe"]}
        level = pokemon.get("level", 100)
        nature = pokemon.get("nature", "None")

        calc = calc_stats(pokemon.get("name"), level, evs, ivs, nature)
        if calc:
            pokemon.update(calc)

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

        # Show calculated totals if present
        if calc:
            msg += "\n\n🧮 Stats: "
            msg += f"HP {pokemon['stat_hp']}, Atk {pokemon['stat_atk']}, Def {pokemon['stat_def']}, "
            msg += f"SpA {pokemon['stat_spa']}, SpD {pokemon['stat_spd']}, Spe {pokemon['stat_spe']}"
            msg += f"\nΣ Total: {pokemon['total_stats_sum']}"

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

POKEMON_PER_PAGE = 15  # ==== /team ====

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
    page_items = team[sta
