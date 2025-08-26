from telethon import TelegramClient, events
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
# ==== /start command ====
@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = event.sender_id
    first_name = event.sender.first_name

    # Check if user is authorised
    authorised = auth.find_one({"user_id": user_id})
    if not authorised and user_id != owner:
        await event.respond("❌ You are not authorised to use this bot.")
        return

    # Check if already in users DB
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
        await event.reply("You are not Owner!") 
        return
    # Check if already authorised
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
        buttons=[
            [Button.url("⚡ Open Teambuilder", SHOWDOWN_LINK)]
        ]
    )
print("Bot running...")
bot.run_until_disconnected()
