# Fixed Battle System Module

This Python script includes the battle system refactored to edit existing messages rather than sending new ones.

```python
import random, json, math, uuid
from math import ceil
import string
import asyncio
from datetime import datetime
from collections import Counter
from telethon import TelegramClient, events, Button
from pymongo import MongoClient

# ==== Setup Bot ====
API_ID = 27715449
API_HASH = "dd3da7c5045f7679ff1f0ed0c82404e0"
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# ==== Setup MongoDB ====
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["pokemon_showdown"]
users = db["users"]
auth = db["authorised"]
pokedata = db["pokemon_data"]

# In-memory battles
battles = {}
battle_map = {}
owner = 6735548827

# Nature chart for stat calculation (import your existing chart here)
nature_chart = {/* ... */}

# Load moves data
try:
    with open("moves.json", "r", encoding="utf-8") as f:
        MOVES = json.load(f)
except FileNotFoundError:
    MOVES = {}
    print("Warning: moves.json not found. Battle system may not work correctly.")

# Helper functions omitted for brevity: parse_stats, calculate_stat, add_final_stats, get_user_team, init_battle_pokemon, load_battle_pokemon
# Include your existing implementations

# 1. Track message IDs in battle data

def create_battle(challenger_id, opponent_id, battle_type):
    bid = f"BATTLE-{uuid.uuid4().hex[:6].upper()}"
    battles[bid] = {
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

# 2. Edit UI messages instead of sending new ones
async def send_battle_ui(bid):
    battle = battles.get(bid)
    if not battle or "active" not in battle:
        return

    challenger = battle["active"]["challenger"]
    opponent = battle["active"]["opponent"]

    def hp_bar(current, max_hp, length=20):
        filled = int(length * current / max_hp) if max_hp > 0 else 0
        return "🟩" * filled + "⬜" * (length - filled)

    # Build texts and buttons for both sides (similar to original code)
    # ...

    # Send or edit challenger UI
    if battle["message_ids"]["challenger"]:
        await bot.edit_message(
            battle["challenger"],
            battle["message_ids"]["challenger"],
            c_text,
            buttons=c_buttons
        )
    else:
        msg = await bot.send_message(battle["challenger"], c_text, buttons=c_buttons)
        battle["message_ids"]["challenger"] = msg.id

    # Send or edit opponent UI
    if battle["message_ids"]["opponent"]:
        await bot.edit_message(
            battle["opponent"],
            battle["message_ids"]["opponent"],
            o_text,
            buttons=o_buttons
        )
    else:
        msg = await bot.send_message(battle["opponent"], o_text, buttons=o_buttons)
        battle["message_ids"]["opponent"] = msg.id

# 3. Use event.answer() for callbacks
@bot.on(events.CallbackQuery(pattern=b"battle:move:(.+):(.+)"))
async def cb_move(event):
    bid = event.pattern_match.group(1).decode()
    move_selected = event.pattern_match.group(2).decode()
    battle = battles.get(bid)
    if not battle:
        return await event.answer("❌ Battle not found.", alert=True)

    user_id = event.sender_id
    side = "challenger" if user_id == battle["challenger"] else "opponent"
    if battle["forced_switch"][side]:
        return await event.answer("❌ You must choose a replacement Pokémon first!", alert=True)

    battle["pending_action"][side] = move_selected
    await event.answer(f"✅ You selected {move_selected}. Waiting for opponent...")

    if battle["pending_action"]["challenger"] and battle["pending_action"]["opponent"]:
        await resolve_turn(bid)

# 4. process forced switch and send acknowledgment via send_message
@bot.on(events.CallbackQuery(pattern=b"battle:forced_switch:(.+):(.+):(.+)"))
async def cb_forced_switch(event):
    bid = event.pattern_match.group(1).decode()
    side = event.pattern_match.group(2).decode()
    idx = int(event.pattern_match.group(3).decode())
    battle = battles.get(bid)
    # validation omitted
    battle["active"][side] = battle["battle_state"][side][idx]
    battle["forced_switch"][side] = False
    await bot.send_message(event.sender_id, f"✅ {battle['active'][side]['name']} was sent out!")
    if not battle["forced_switch"]["challenger"] and not battle["forced_switch"]["opponent"]:
        await send_battle_ui(bid)

# 5. resolve_turn ends with editing UI
async def resolve_turn(bid):
    battle = battles.get(bid)
    # ... process actions ...
    # send turn results as separate messages
    # clear actions and increment turn
    if not any(p["hp"] > 0 for p in battle["battle_state"]["challenger"]):
        await end_battle(bid, "opponent")
        return
    if not any(p["hp"] > 0 for p in battle["battle_state"]["opponent"]):
        await end_battle(bid, "challenger")
        return
    await send_battle_ui(bid)

# Include your remaining command handlers (battle_singles, battle_doubles, accept/decline, etc.) as before.

if __name__ == "__main__":
    print("Bot running...")
    bot.run_until_disconnected()
```

Save this as `battle_system_fixed.py` and integrate your existing helpers and data structures.