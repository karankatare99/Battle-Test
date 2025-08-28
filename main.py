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
pokedata = db["pokemon_data"]
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

        elif not line.startswith("IVs:"):
            for stat in ["hp","atk","def","spa","spd","spe"]:
                pokemon[f"iv{stat}"] = 31
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
            "pokemon": [],
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
    {"$push": {"pokemon": pokemon_key}},
    upsert=True
        )
        pokedata.update_one(
            {"_id": pokemon_key},   # use pokemon_key as unique id
            {"$set": pokemon},      # store the dict
            upsert=True)

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

from collections import Counter

# ==== /pokemon command ====
@bot.on(events.NewMessage(pattern="/pokemon"))
async def pokemon_list_handler(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})

    if not user or not user.get("pokemon"):
        await event.respond("❌ You don’t have any Pokémon yet.")
        return

    # Fetch full pokedata for each stored ID
    pokemon_ids = user["pokemon"]  # list of keys like ["Pikachu_25", "Bulbasaur_1"]
    pokemons = pokedata.find({"_id": {"$in": pokemon_ids}})

    names = [poke["name"] for poke in pokemons]
    counts = Counter(names)

    # Store pagination in a dict for session
    page = 0
    await send_pokemon_page(event, counts, page)


async def send_pokemon_page(event, counts, page):
    per_page = 25
    poke_list = [f"{name} ({count})" if count > 1 else name for name, count in counts.items()]
    total_pages = (len(poke_list) - 1) // per_page + 1

    start = page * per_page
    end = start + per_page
    page_items = poke_list[start:end]

    text = f"📜 **Your Pokémon** (Page {page+1}/{total_pages})\n\n"
    text += "\n".join(page_items) if page_items else "No Pokémon on this page."

    # Navigation buttons
    buttons = []
    if page > 0:
        buttons.append(Button.inline("⬅️ Prev", data=f"pokemon:{page-1}"))
    if page < total_pages - 1:
        buttons.append(Button.inline("➡️ Next", data=f"pokemon:{page+1}"))

    await event.respond(text, buttons=[buttons] if buttons else None)


# ==== Handle button callbacks ====
@bot.on(events.CallbackQuery(pattern=b"pokemon:(\d+)"))
async def callback_pokemon_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})

    if not user or not user.get("pokemon"):
        await event.answer("❌ No Pokémon found.", alert=True)
        return

    pokemon_ids = user["pokemon"]
    pokemons = pokedata.find({"_id": {"$in": pokemon_ids}})
    names = [poke["name"] for poke in pokemons]
    counts = Counter(names)

    await event.edit("Loading...", buttons=None)  # placeholder
    await send_pokemon_page(event, counts, page)


POKEMON_PER_PAGE = 15


# ==== /team Command ====
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

# ==== Render team ====
async def send_team_page(event, user):
    team_ids = user.get("team", [])
    
    # Fetch Pokémon details from pokedata
    pokes = list(pokedata.find({"_id": {"$in": team_ids}}))
    poke_map = {p["_id"]: p for p in pokes}

    text = "⚔️ **Your Team**:\n\n"
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


# ==== Show Add Pokémon page (paginated) ====
async def send_add_page(event, user, page=0):
    team_ids = user.get("team", [])
    owned_ids = user.get("pokemon", [])   # now just a list of IDs
    available_ids = [pid for pid in owned_ids if pid not in team_ids]

    if not available_ids:
        await event.answer("❌ No more Pokémon left in your profile to add.", alert=True)
        return

    total_pages = (len(available_ids) - 1) // POKEMON_PER_PAGE + 1
    start = page * POKEMON_PER_PAGE
    end = start + POKEMON_PER_PAGE
    page_items = available_ids[start:end]

    # Fetch Pokémon details from pokedata
    pokes = list(pokedata.find({"_id": {"$in": page_items}}))
    poke_map = {p["_id"]: p for p in pokes}

    # Text list
    text = f"➕ **Select a Pokémon to Add** (Page {page+1}/{total_pages})\n\n"
    for i, pid in enumerate(page_items, start=1):
        poke = poke_map.get(pid)
        if poke:
            text += f"{i}. {poke['name']} (ID: {poke['_id']})\n"
        else:
            text += f"{i}. ❓ Unknown ({pid})\n"

    # Numbered buttons
    buttons = []
    row = []
    for i, pid in enumerate(page_items, start=start):
        row.append(Button.inline(str((i % POKEMON_PER_PAGE) + 1), f"team:add:{pid}".encode()))
        if len(row) == 5:  # 5 buttons per row
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Navigation
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅️ Prev", f"team:addpage:{page-1}".encode()))
    if page < total_pages - 1:
        nav.append(Button.inline("➡️ Next", f"team:addpage:{page+1}".encode()))
    if nav:
        buttons.append(nav)

    # Back button
    buttons.append([Button.inline("⬅️ Back", b"team:back")])

    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)


# ==== Open Add Pokémon menu ====
@bot.on(events.CallbackQuery(pattern=b"team:addpage:(\d+)"))
async def team_add_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_add_page(event, user, page)


# ==== Confirm Add ====
@bot.on(events.CallbackQuery(pattern=b"team:add:(.+)"))
async def confirm_add(event):
    poke_id = event.pattern_match.group(1).decode()  # Pokémon ID string
    user_id = event.sender_id

    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])

    if len(team) >= 6:
        await event.answer("⚠️ Team is already full (6 Pokémon max)!", alert=True)
        return

    # Make sure user actually owns this Pokémon
    owned_ids = user.get("pokemon", [])
    if poke_id not in owned_ids:
        await event.answer("❌ You don’t own this Pokémon.", alert=True)
        return

    if poke_id not in team:
        users.update_one({"user_id": user_id}, {"$push": {"team": poke_id}})
        await event.answer("✅ Pokémon added to team!")
    else:
        await event.answer("⚠️ That Pokémon is already in your team.", alert=True)

    # Reload user + refresh UI
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)


# ==== Back button to team ====
@bot.on(events.CallbackQuery(pattern=b"team:back"))
async def back_to_team(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)

# ==== Show Remove Pokémon page (paginated) ====
async def send_remove_page(event, user, page=0):
    team = user.get("team", [])

    if not team:
        await event.answer("⚠️ Your team is empty!", alert=True)
        return

    total_pages = (len(team) - 1) // POKEMON_PER_PAGE + 1
    start = page * POKEMON_PER_PAGE
    end = start + POKEMON_PER_PAGE
    page_items = team[start:end]

    # Build text list
    text = f"➖ **Select a Pokémon to Remove** (Page {page+1}/{total_pages})\n\n"
    for i, poke_id in enumerate(page_items, start=1):
        poke = pokedata.find_one({"_id": poke_id}) or {}
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"

    # Numbered buttons
    buttons = []
    row = []
    for i, poke_id in enumerate(page_items, start=start):
        row.append(Button.inline(
            str((i % POKEMON_PER_PAGE) + 1),
            f"team:remove:{poke_id}".encode()
        ))
        if len(row) == 5:  # 5 per row
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Navigation
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅️ Prev", f"team:removepage:{page-1}".encode()))
    if page < total_pages - 1:
        nav.append(Button.inline("➡️ Next", f"team:removepage:{page+1}".encode()))
    if nav:
        buttons.append(nav)

    # Back button
    buttons.append([Button.inline("⬅️ Back", b"team:back")])

    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.respond(text, buttons=buttons)

# ==== Open Remove Pokémon menu ====
@bot.on(events.CallbackQuery(pattern=b"team:remove$"))
async def team_remove_menu(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_remove_page(event, user, 0)


# ==== Paginate Remove ====
@bot.on(events.CallbackQuery(pattern=b"team:removepage:(\d+)"))
async def team_remove_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    await send_remove_page(event, user, page)


# ==== Confirm Remove ====
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

# ==== Switch Pokémon (Step 1: Select first Pokémon) ====
@bot.on(events.CallbackQuery(pattern=b"team:switch$"))
async def team_switch_start(event):
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])

    if len(team) < 2:
        await event.answer("⚠️ You need at least 2 Pokémon in your team to switch.", alert=True)
        return

    text = "🔄 **Select the first Pokémon to switch**:\n\n"
    for i, key in enumerate(team, start=1):
        poke = pokedata.find_one({"_id": key}) or {}
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"

    buttons = []
    row = []
    for i, key in enumerate(team, start=1):
        row.append(Button.inline(str(i), f"team:switch1:{i-1}".encode()))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([Button.inline("⬅️ Back", b"team:back")])

    await event.edit(text, buttons=buttons)


# ==== Switch Pokémon (Step 2: Select second Pokémon) ====
@bot.on(events.CallbackQuery(pattern=b"team:switch1:(\d+)"))
async def team_switch_pick_second(event):
    first_index = int(event.pattern_match.group(1))
    user_id = event.sender_id
    user = users.find_one({"user_id": user_id})
    team = user.get("team", [])

    first_poke = pokedata.find_one({"_id": team[first_index]}) or {}
    first_name = first_poke.get("name", "Unknown")

    text = f"🔄 **Select the second Pokémon to swap with** (first chosen: {first_name})\n\n"

    for i, key in enumerate(team, start=1):
        poke = pokedata.find_one({"_id": key}) or {}
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"

    buttons = []
    row = []
    for i in range(len(team)):
        if i == first_index:
            continue
        row.append(Button.inline(str(i+1), f"team:switch2:{first_index}:{i}".encode()))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([Button.inline("⬅️ Back", b"team:back")])

    await event.edit(text, buttons=buttons)

# ==== Confirm Switch ====
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

    # Swap positions
    team[first_index], team[second_index] = team[second_index], team[first_index]
    users.update_one({"user_id": user_id}, {"$set": {"team": team}})

    await event.answer("✅ Pokémon switched!")
    user = users.find_one({"user_id": user_id})
    await send_team_page(event, user)

# Cache for active searches {user_id: [matches]}
active_summaries = {}

POKEMON_PER_PAGE = 15

# ==== /summary command ====
@bot.on(events.NewMessage(pattern=r"^/summary (.+)"))
async def summary_handler(event):
    query = event.pattern_match.group(1).strip().lower()
    user_id = event.sender_id

    user = users.find_one({"user_id": user_id})
    if not user or "pokemon" not in user or not user["pokemon"]:
        await event.reply("❌ You don’t have any Pokémon.")
        return

    matches = []

    # search by name or ID
    for poke_id in user["pokemon"]:
        poke = pokedata.find_one({"_id": poke_id}) or {}
        if not poke:
            continue
        name_lower = poke.get("name","").lower()
        poke_id_lower = poke.get("pokemon_id","").lower()
        if query == name_lower or query == poke_id_lower or query in name_lower:
            matches.append((poke_id, poke))

    if not matches:
        await event.reply("❌ No Pokémon found.")
        return

    # store in cache for pagination
    active_summaries[user_id] = matches

    if len(matches) == 1:
        await send_summary(event, matches[0][1])
    else:
        await send_summary_list(event, matches, 0)


# ==== Send Summary List with Pagination ====
async def send_summary_list(event, matches, page=0):
    total_pages = (len(matches) - 1) // POKEMON_PER_PAGE + 1
    start = page * POKEMON_PER_PAGE
    end = start + POKEMON_PER_PAGE
    page_items = matches[start:end]

    text = f"⚠️ Multiple Pokémon found (Page {page+1}/{total_pages}):\n\n"
    for i, (_, poke) in enumerate(page_items, start=1):
        text += f"{i}. {poke.get('name','Unknown')} ({poke.get('pokemon_id','?')})\n"

    # numbered buttons
    buttons = []
    row = []
    for i, (poke_id, poke) in enumerate(page_items, start=start):
        row.append(Button.inline(
            str((i % POKEMON_PER_PAGE) + 1),
            f"summary:show:{poke_id}".encode()
        ))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # nav buttons
    nav = []
    if page > 0:
        nav.append(Button.inline("⬅️ Prev", f"summary:page:{page-1}".encode()))
    if page < total_pages - 1:
        nav.append(Button.inline("➡️ Next", f"summary:page:{page+1}".encode()))
    if nav:
        buttons.append(nav)

    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text, buttons=buttons)
    else:
        await event.reply(text, buttons=buttons)


# ==== Pagination handler ====
@bot.on(events.CallbackQuery(pattern=b"summary:page:(\d+)"))
async def summary_page(event):
    page = int(event.pattern_match.group(1))
    user_id = event.sender_id

    matches = active_summaries.get(user_id)
    if not matches:
        await event.answer("❌ No active summary search.", alert=True)
        return

    await send_summary_list(event, matches, page)
# ==== Show summary for selected Pokémon ====
@bot.on(events.CallbackQuery(pattern=b"summary:show:(.+)"))
async def summary_show(event):
    poke_id = event.pattern_match.group(1).decode()
    user_id = event.sender_id

    # Fetch Pokémon from database
    poke = pokedata.find_one({"_id": poke_id})
    if not poke:
        await event.answer("❌ Pokémon not found.", alert=True)
        return

    await send_summary(event, poke)

# ==== Render one Pokémon summary ====
async def send_summary(event, poke):
    text = (
        f"📜 **Pokémon Summary**\n\n"
        f"🆔 `{poke.get('pokemon_id','?')}`\n"
        f"✨ Name: {poke.get('name','Unknown')}\n"
        f"♀️ Gender: {poke.get('gender','?')}\n"
        f"⭐ Level: {poke.get('level','?')}\n"
        f"💠 Ability: {poke.get('ability','None')}\n"
        f"🔮 Tera Type: {poke.get('tera_type','None')}\n"
        f"🎒 Item: {poke.get('item','None')}\n\n"
        f"📊 **EVs:**\n"
        f"HP: {poke.get('evhp',0)} | Atk: {poke.get('evatk',0)} | Def: {poke.get('evdef',0)}\n"
        f"SpA: {poke.get('evspa',0)} | SpD: {poke.get('evspd',0)} | Spe: {poke.get('evspe',0)}\n\n"
        f"🧬 **IVs:**\n"
        f"HP: {poke.get('ivhp',31)} | Atk: {poke.get('ivatk',31)} | Def: {poke.get('ivdef',31)}\n"
        f"SpA: {poke.get('ivspa',31)} | SpD: {poke.get('ivspd',31)} | Spe: {poke.get('ivspe',31)}\n\n"
        f"⚔️ **Moves:** {', '.join(poke.get('moves', [])) if poke.get('moves') else 'None'}"
    )

    if isinstance(event, events.CallbackQuery.Event):
        await event.edit(text)
    else:
        await event.reply(text)
        
print("Bot running...")
bot.run_until_disconnected()
