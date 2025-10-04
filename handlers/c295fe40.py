from telethon import events, Button
import random
import asyncio
import json
from database import users, pokedata, battles_db, matchmaking

# Battle state dictionaries
battle_data = {}
battle_state = {}
invitecode = {}
textic = {}
room = {}
selected_move = {}
selected_action = {}  # New: Track player actions (move/switch/run)
switch_queue = {}     # New: Track switch requests
turn_queue = {}       # New: Track turn completion
roomids = []
rs_lobby = []
rd_lobby = []
cs_lobby = []
cd_lobby = []
searchmsg = {}
selectteam = {}
room_userids = {}

# Battle action types
ACTION_MOVE = "move"
ACTION_SWITCH = "switch"
ACTION_RUN = "run"

# Type effectiveness chart (complete)
type1_modifier = {
    "normal": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 0.5, "ghost": 0, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 1},
    "fire": {"normal": 1, "fire": 0.5, "water": 0.5, "electric": 1, "grass": 2, "ice": 2, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 2, "rock": 0.5, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 2, "fairy": 1},
    "water": {"normal": 1, "fire": 2, "water": 0.5, "electric": 1, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 1, "ground": 2, "flying": 1, "psychic": 1, "bug": 1, "rock": 2, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 1, "fairy": 1},
    "electric": {"normal": 1, "fire": 1, "water": 2, "electric": 0.5, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 1, "ground": 0, "flying": 2, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 1, "fairy": 1},
    "grass": {"normal": 1, "fire": 0.5, "water": 2, "electric": 1, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 0.5, "ground": 2, "flying": 0.5, "psychic": 1, "bug": 0.5, "rock": 2, "ghost": 1, "dragon": 0.5, "dark": 1, "steel": 0.5, "fairy": 1},
    "ice": {"normal": 1, "fire": 0.5, "water": 0.5, "electric": 1, "grass": 2, "ice": 0.5, "fighting": 1, "poison": 1, "ground": 2, "flying": 2, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 2, "dark": 1, "steel": 0.5, "fairy": 1},
    "fighting": {"normal": 2, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 2, "fighting": 1, "poison": 0.5, "ground": 1, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "rock": 2, "ghost": 0, "dragon": 1, "dark": 2, "steel": 2, "fairy": 0.5},
    "poison": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 2, "ice": 1, "fighting": 1, "poison": 0.5, "ground": 0.5, "flying": 1, "psychic": 1, "bug": 1, "rock": 0.5, "ghost": 0.5, "dragon": 1, "dark": 1, "steel": 0, "fairy": 2},
    "ground": {"normal": 1, "fire": 2, "water": 1, "electric": 2, "grass": 0.5, "ice": 1, "fighting": 1, "poison": 2, "ground": 1, "flying": 0, "psychic": 1, "bug": 0.5, "rock": 2, "ghost": 1, "dragon": 1, "dark": 1, "steel": 2, "fairy": 1},
    "flying": {"normal": 1, "fire": 1, "water": 1, "electric": 0.5, "grass": 2, "ice": 1, "fighting": 2, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 2, "rock": 0.5, "ghost": 1, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 1},
    "psychic": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 2, "poison": 2, "ground": 1, "flying": 1, "psychic": 0.5, "bug": 1, "rock": 1, "ghost": 1, "dragon": 1, "dark": 0, "steel": 0.5, "fairy": 1},
    "bug": {"normal": 1, "fire": 0.5, "water": 1, "electric": 1, "grass": 2, "ice": 1, "fighting": 0.5, "poison": 0.5, "ground": 1, "flying": 0.5, "psychic": 2, "bug": 1, "rock": 1, "ghost": 0.5, "dragon": 1, "dark": 2, "steel": 0.5, "fairy": 0.5},
    "rock": {"normal": 1, "fire": 2, "water": 1, "electric": 1, "grass": 1, "ice": 2, "fighting": 0.5, "poison": 1, "ground": 0.5, "flying": 2, "psychic": 1, "bug": 2, "rock": 1, "ghost": 1, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 1},
    "ghost": {"normal": 0, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 2, "bug": 1, "rock": 1, "ghost": 2, "dragon": 1, "dark": 0.5, "steel": 1, "fairy": 1},
    "dragon": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 2, "dark": 1, "steel": 0.5, "fairy": 0},
    "dark": {"normal": 1, "fire": 1, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 0.5, "poison": 1, "ground": 1, "flying": 1, "psychic": 2, "bug": 1, "rock": 1, "ghost": 2, "dragon": 1, "dark": 0.5, "steel": 1, "fairy": 0.5},
    "steel": {"normal": 1, "fire": 0.5, "water": 0.5, "electric": 0.5, "grass": 1, "ice": 2, "fighting": 1, "poison": 1, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 2, "ghost": 1, "dragon": 1, "dark": 1, "steel": 0.5, "fairy": 2},
    "fairy": {"normal": 1, "fire": 0.5, "water": 1, "electric": 1, "grass": 1, "ice": 1, "fighting": 2, "poison": 0.5, "ground": 1, "flying": 1, "psychic": 1, "bug": 1, "rock": 1, "ghost": 1, "dragon": 2, "dark": 2, "steel": 0.5, "fairy": 1}
}

def register_battle_handlers(bot):
    @bot.on(events.NewMessage(pattern='/battle_stadium'))
    async def battle_stadium(event):
        user_id = event.sender_id
        if not users.find_one({"user_id": user_id}):
            await event.reply("❌ You need to start your journey first! Use /start command.")
            return
        if battle_state.get(user_id):
            await event.reply("⚠️ You are already in a battle! Finish your current battle first.")
            return
        connect_msg = await event.reply("__**Communicating....Please stand by!**__")

        buttons = [
            [Button.inline("🎮 Quick Battle", b"quick")],
            [Button.inline("🏟️ Ranked Battle", b"ranked")],
            [Button.inline("🎯 Custom Battle", b"custom")]
        ]

        await connect_msg.edit(
            "**⚔️ Welcome to the Battle Stadium! ⚔️**\n\n"
            "Choose your battle mode:",
            buttons=buttons
        )

    @bot.on(events.CallbackQuery(pattern=b"^(quick|ranked|custom)$"))
    async def select_mode(event):
        await event.edit("__**Communicating....Please stand by!**__")
        mode = event.pattern_match.group(1).decode()

        buttons = [
            [Button.inline("1v1 Singles", f"{mode}_singles".encode())],
            [Button.inline("2v2 Doubles", f"{mode}_doubles".encode())]
        ]

        await event.edit(
            f"**{mode.title()} Battle Mode Selected**\n\n"
            "Choose battle format:",
            buttons=buttons
        )

    @bot.on(events.CallbackQuery(pattern=b"^(\w+)_(singles|doubles)$"))
    async def select_format(event):
        user_id = event.sender_id
        mode, fmt = (g.decode() for g in event.pattern_match.groups())

        await battle_create(user_id, mode, fmt)

        print("Battle data created:", battle_data)
        battle_state[user_id] = {}
        battle_state[int(user_id)]["mode"] = mode
        battle_state[int(user_id)]["fmt"] = fmt
        battle_state[int(user_id)]["team"] = battle_data[int(user_id)]["team"]
        battle_state[int(user_id)]["allowed_pokemon"] = []
        battle_state[int(user_id)]["active_pokemon"] = []
        battle_state[int(user_id)]["battle_started"] = False
        battle_state[int(user_id)]["battle_initiated"] = True
        battle_state[int(user_id)]["turn"] = 1
        battle_state[int(user_id)]["waiting_for_action"] = False
        battle_state[int(user_id)]["fainted_pokemon"] = []

        text = (
            f"**🎯 {mode.title()} {fmt.title()} Battle**\n\n"
            "Choose how to find an opponent:"
        )

        buttons = [
            [Button.inline("🔍 Matchmaking", f"{mode}_{fmt}_mm".encode())],
            [Button.inline("🎫 Create Lobby", f"{mode}_{fmt}_code".encode())]
        ]

        await event.edit(text, buttons=buttons)

    # Continue with existing handlers but with improvements...
    @bot.on(events.CallbackQuery(pattern=b"^(\w+)_(singles|doubles)_mm$"))
    async def matchmaking(event):
        mode, fmt, mm = (g.decode() for g in event.pattern_match.groups())
        user_id = event.sender_id

        # Select appropriate lobby based on mode and format
        if mode == "ranked" and fmt == "singles":
            lobby = rs_lobby
        elif mode == "ranked" and fmt == "doubles":
            lobby = rd_lobby
        elif mode == "custom" and fmt == "singles":
            lobby = cs_lobby
        elif mode == "custom" and fmt == "doubles":
            lobby = cd_lobby
        else:
            lobby = rs_lobby  # Default fallback

        searchmsg[user_id] = await event.edit("🔍 **Searching for opponent...**\n\nPlease wait...")

        if user_id in lobby:
            await event.edit("⚠️ You are already in the matchmaking queue!")
            return

        if user_id not in lobby:
            lobby.append(user_id)
            await search_for_opp_trainer(lobby)

    # Rest of the handlers continue...
    @bot.on(events.CallbackQuery(pattern=b"^(\w+)_(singles|doubles)_code$"))
    async def code_keyboard(event):
        mode, fmt, mm, ic = (g.decode() for g in event.pattern_match.groups())
        user_id = event.sender_id
        room_id = await generate_room_id()

        invitecode[user_id] = room_id

        buttons = [[Button.inline("✅ Ready", f"{user_id}_{mode}_{fmt}_done".encode())]]

        await event.edit(
            f"**🎫 Room Created**\n\n"
            f"**Room ID:** `{room_id}`\n"
            f"**Mode:** {mode.title()} {fmt.title()}\n\n"
            "Share this room ID with your opponent!",
            buttons=buttons
        )

# Continue with the rest of the battle system...

    @bot.on(events.CallbackQuery(pattern=b"^(\d+)_([a-zA-Z]+)_([a-zA-Z]+)_([a-zA-Z_]+)$"))
    async def select_pokemon(event):
        user_id_str, mode, fmt, poke = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        mode = mode.decode()
        fmt = fmt.decode()
        poke = poke.decode()

        if event.sender_id != user_id:
            await event.answer("❌ This is not your battle!", alert=True)
            return

        if user_id not in selectteam:
            selectteam[user_id] = {'pokes': [], 'mode': mode, 'fmt': fmt}

        current_team = selectteam[user_id]['pokes']
        max_pokemon = 1 if fmt == "singles" else 2

        if poke in current_team:
            current_team.remove(poke)
        elif len(current_team) < max_pokemon:
            current_team.append(poke)
        else:
            await event.answer(f"❌ Maximum {max_pokemon} Pokémon allowed for {fmt}!", alert=True)
            return

        selected_count = len(selectteam[user_id]['pokes'])
        buttons = await build_team_buttons(battle_data[user_id]["team"], user_id)

        text = (
            f"**📝 Team Selection ({selected_count}/{max_pokemon})**\n\n"
            f"**Selected:** {', '.join([p.split('_')[0].title() for p in current_team])}\n\n"
            "Select your Pokémon:"
        )

        await event.edit(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+)_([a-zA-Z]+)_([a-zA-Z]+)_done$"))
    async def done_callback(event):
        user_id_str, mode, fmt, done = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        mode = mode.decode()
        fmt = fmt.decode()

        if event.sender_id != user_id:
            await event.answer("❌ This is not your battle!", alert=True)
            return

        if user_id not in selectteam:
            await event.answer("❌ Please select your team first!", alert=True)
            return

        selected_count = len(selectteam[user_id]['pokes'])
        max_pokemon = 1 if fmt == "singles" else 2

        if selected_count < max_pokemon:
            await event.answer(f"❌ Please select {max_pokemon} Pokémon!", alert=True)
            return

        battle_state[user_id]["allowed_pokemon"] = selectteam[user_id]['pokes'].copy()

        await event.edit("✅ **Team confirmed!**\n\nWaiting for battle to start...")
        await first_battle_ui(mode, fmt, user_id, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+)_([a-zA-Z]+)_([a-zA-Z]+)_view_opp$"))
    async def view_opponent_team(event):
        user_id_str, mode, fmt, action = event.pattern_match.groups()
        user_id = int(user_id_str.decode())

        if event.sender_id != user_id:
            await event.answer("❌ This is not your battle!", alert=True)
            return

        opp_id = room[user_id]["opponent"]

        if opp_id not in battle_state or "allowed_pokemon" not in battle_state[opp_id]:
            await event.answer("❌ Opponent hasn't selected their team yet!", alert=True)
            return

        opp_team = battle_state[opp_id]["team"]
        opp_selected = battle_state[opp_id]["allowed_pokemon"]

        text = "**👁️ Opponent's Team:**\n\n"
        for poke in opp_selected:
            poke_name = poke.split('_')[0].title()
            text += f"• {poke_name}\n"

        await event.answer(text, alert=True)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+):([a-zA-Z_]+):([a-zA-Z_\s]+)$"))
    async def handle_move(event):
        user_id_str, poke, move = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        poke = poke.decode()
        move = move.decode()

        if event.sender_id != user_id:
            await event.answer("❌ This is not your turn!", alert=True)
            return

        # Record the player's action
        selected_action[user_id] = {
            "type": ACTION_MOVE,
            "pokemon": poke,
            "move": move,
            "turn": battle_state[user_id]["turn"]
        }

        room_id = room[user_id]["roomid"]
        await event.answer(f"✅ Selected {move}!")
        await awaiting_move_action(room_id, battle_state[user_id]["fmt"], move, poke, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+):pokemon_switch$"))
    async def handle_pokemon_switch(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())

        if event.sender_id != user_id:
            await event.answer("❌ This is not your turn!", alert=True)
            return

        # Show available Pokemon to switch to
        available_pokemon = []
        for poke in battle_state[user_id]["allowed_pokemon"]:
            # Don't show fainted Pokemon or currently active Pokemon
            if (poke not in battle_state[user_id]["fainted_pokemon"] and 
                poke not in battle_state[user_id]["active_pokemon"]):
                available_pokemon.append(poke)

        if not available_pokemon:
            await event.answer("❌ No Pokémon available to switch!", alert=True)
            return

        buttons = []
        for poke in available_pokemon:
            poke_name = poke.split('_')[0].title()
            hp = battle_data[user_id]["pokemon"][poke]["current_hp"]
            max_hp = battle_data[user_id]["pokemon"][poke]["final_hp"]
            buttons.append([Button.inline(f"{poke_name} ({hp}/{max_hp} HP)", 
                                        f"{user_id}:switch:{poke}".encode())])

        buttons.append([Button.inline("❌ Cancel", f"{user_id}:cancel_switch".encode())])

        await event.edit("**🔄 Select Pokémon to switch:**", buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+):switch:([a-zA-Z_]+)$"))
    async def confirm_switch(event):
        user_id_str, poke = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        poke = poke.decode()

        if event.sender_id != user_id:
            await event.answer("❌ This is not your turn!", alert=True)
            return

        # Record the switch action
        selected_action[user_id] = {
            "type": ACTION_SWITCH,
            "pokemon": poke,
            "turn": battle_state[user_id]["turn"]
        }

        room_id = room[user_id]["roomid"]
        await event.answer(f"✅ Switching to {poke.split('_')[0].title()}!")
        await awaiting_move_action(room_id, battle_state[user_id]["fmt"], None, poke, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+):cancel_switch$"))
    async def cancel_switch(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())

        # Return to battle UI
        room_id = room[user_id]["roomid"]
        fmt = battle_state[user_id]["fmt"]
        await first_battle_ui(battle_state[user_id]["mode"], fmt, user_id, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\d+):run$"))
    async def handle_run(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())

        if event.sender_id != user_id:
            await event.answer("❌ This is not your turn!", alert=True)
            return

        # Handle running away/forfeit
        opp_id = room[user_id]["opponent"]

        # End the battle
        winner_text = f"🏆 **Victory!** 🏆\n\nYour opponent forfeited the battle!"
        loser_text = f"💔 **Defeat!** 💔\n\nYou forfeited the battle!"

        try:
            await room[opp_id]["start_msg"].edit(winner_text)
            await event.edit(loser_text)
        except:
            pass

        # Clean up battle state
        cleanup_battle(user_id)
        cleanup_battle(opp_id)

async def battle_create(user_id, mode, format):
    user_dict = db_battle_extractor(user_id, mode, format)

    global battle_data
    if not isinstance(battle_data, dict):
        battle_data = {}
    battle_data.update(user_dict)

def db_battle_extractor(user_id, mode, format):
    user_data = users.find_one({"user_id": int(user_id)})

    if not user_data:
        return {}

    user_dict = {int(user_id): {
        "user_id": user_id,
        "username": user_data.get("username", "Unknown"),
        "mode": mode,
        "fmt": format,
        "team": user_data.get("team", []),
        "pokemon": user_data.get("pokemon", {}),
        "battle_stats": user_data.get("battle_stats", {})
    }}

    return user_dict

async def generate_room_id():
    while True:
        room_id = random.randint(100000, 999999)
        if room_id not in roomids:
            roomids.append(room_id)
            return room_id
        await asyncio.sleep(0.1)

async def build_team_buttons(team, user_id):
    """Return a two-column inline keyboard with team selection buttons."""
    buttons = []

    for i, poke in enumerate(team):
        poke_name = poke.split('_')[0].title()
        is_selected = user_id in selectteam and poke in selectteam[user_id]['pokes']
        emoji = "✅" if is_selected else "⚪"

        button_text = f"{emoji} {poke_name}"
        callback_data = f"{user_id}_{selectteam[user_id]['mode']}_{selectteam[user_id]['fmt']}_{poke}".encode()

        if i % 2 == 0:  # Start new row for even indices
            buttons.append([Button.inline(button_text, callback_data)])
        else:  # Add to existing row for odd indices
            buttons[-1].append(Button.inline(button_text, callback_data))

    # Add Done and View Opponent buttons
    mode = selectteam[user_id]['mode']
    fmt = selectteam[user_id]['fmt']
    buttons.append([
        Button.inline("✅ Done", f"{user_id}_{mode}_{fmt}_done".encode()),
        Button.inline("👁️ View Opponent", f"{user_id}_{mode}_{fmt}_view_opp".encode())
    ])

    return buttons

async def team_preview(p1, p2):
    p1_msg = room[p1]["start_msg"]
    p2_msg = room[p2]["start_msg"]

    p1_team = battle_data[p1]["team"]
    p2_team = battle_data[p2]["team"]

    # Initialize selectteam for both players
    selectteam[p1] = {'pokes': [], 'mode': battle_state[p1]["mode"], 'fmt': battle_state[p1]["fmt"]}
    selectteam[p2] = {'pokes': [], 'mode': battle_state[p2]["mode"], 'fmt': battle_state[p2]["fmt"]}

    p1_buttons = await build_team_buttons(p1_team, p1)
    p2_buttons = await build_team_buttons(p2_team, p2)

    max_pokemon = 1 if battle_state[p1]["fmt"] == "singles" else 2

    p1_text = (
        f"**⚔️ Battle Starting! ⚔️**\n\n"
        f"**Format:** {battle_state[p1]['fmt'].title()}\n"
        f"**Mode:** {battle_state[p1]['mode'].title()}\n\n"
        f"**Select {max_pokemon} Pokémon for battle:**"
    )

    p2_text = (
        f"**⚔️ Battle Starting! ⚔️**\n\n"
        f"**Format:** {battle_state[p2]['fmt'].title()}\n"
        f"**Mode:** {battle_state[p2]['mode'].title()}\n\n"
        f"**Select {max_pokemon} Pokémon for battle:**"
    )

    await p1_msg.edit(p1_text, buttons=p1_buttons)
    await p2_msg.edit(p2_text, buttons=p2_buttons)

async def search_for_opp_trainer(lobby):
    timeout = 120
    start_time = asyncio.get_event_loop().time()

    while True:
        current_time = asyncio.get_event_loop().time()
        if current_time - start_time > timeout:
            # Timeout handling
            for user_id in lobby[:]:
                if user_id in searchmsg:
                    try:
                        await searchmsg[user_id].edit("⏰ **Search timeout!** Please try again.")
                        lobby.remove(user_id)
                        del searchmsg[user_id]
                    except:
                        pass
            return

        if len(lobby) >= 2:
            p1 = lobby.pop(0)
            p2 = lobby.pop(0)

            room_id = await generate_room_id()

            # Setup room data
            room[p1] = {"roomid": room_id, "opponent": p2, "start_msg": searchmsg[p1]}
            room[p2] = {"roomid": room_id, "opponent": p1, "start_msg": searchmsg[p2]}

            room_userids[room_id] = [p1, p2]

            # Initialize action tracking
            selected_action[p1] = {}
            selected_action[p2] = {}

            # Start team preview
            await team_preview(p1, p2)

            # Cleanup search messages
            if p1 in searchmsg:
                del searchmsg[p1]
            if p2 in searchmsg:
                del searchmsg[p2]

            return

        await asyncio.sleep(1)

async def hp_bar(current_hp, max_hp, bars=10):
    if max_hp <= 0:
        return '▱' * bars
    ratio = current_hp / max_hp
    filled = int(bars * ratio)
    empty = bars - filled
    return ''.join(['▰'] * filled + ['▱'] * empty)

async def button_generator(moves, user_id, target_poke):
    buttons = []
    for move in moves:
        buttons.append([Button.inline(move, f"{user_id}:{target_poke}:{move}".encode())])

    # Add control buttons
    buttons.append([
        Button.inline("🔄 Switch", f"{user_id}:pokemon_switch".encode()),
        Button.inline("🏃 Run", f"{user_id}:run".encode())
    ])

    return buttons

async def first_battle_ui(mode, fmt, user_id, event):
    """Initialize the battle UI and start the first turn"""
    print(f"DEBUG: Starting battle UI for user {user_id}")

    if user_id not in room:
        print(f"DEBUG: User {user_id} not in room")
        return

    p1_id = user_id
    p2_id = room[user_id]["opponent"]

    # Set active Pokemon
    p1_active = battle_state[p1_id]["allowed_pokemon"][0]
    p2_active = battle_state[p2_id]["allowed_pokemon"][0]

    battle_state[p1_id]["active_pokemon"] = [p1_active]
    battle_state[p2_id]["active_pokemon"] = [p2_active]

    if fmt == "singles":
        # Singles battle UI
        p1_poke = battle_state[p1_id]["active_pokemon"][0]
        p1_poke_moves = battle_data[p1_id]["pokemon"][p1_poke]["moves"]
        p1_poke_buttons = await button_generator(p1_poke_moves, p1_id, p1_poke)

        p2_poke = battle_state[p2_id]["active_pokemon"][0]
        p2_poke_moves = battle_data[p2_id]["pokemon"][p2_poke]["moves"]
        p2_poke_buttons = await button_generator(p2_poke_moves, p2_id, p2_poke)

        # Generate HP bars
        p1_poke_hpbar = await hp_bar(
            battle_data[p1_id]["pokemon"][p1_poke]["current_hp"],
            battle_data[p1_id]["pokemon"][p1_poke]['final_hp']
        )
        p2_poke_hpbar = await hp_bar(
            battle_data[p2_id]["pokemon"][p2_poke]["current_hp"],
            battle_data[p2_id]["pokemon"][p2_poke]['final_hp']
        )

        p1hppercent = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"] / battle_data[p1_id]["pokemon"][p1_poke]['final_hp'] * 100
        p2hppercent = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"] / battle_data[p2_id]["pokemon"][p2_poke]['final_hp'] * 100

        p1_text = (
            f"**⚔️ Turn {battle_state[p1_id]['turn']} - Singles Battle ⚔️**\n\n"
            f"**Opponent:** {p2_poke.split('_')[0].title()} (Lv.100) {p2hppercent:.0f}%\n"
            f"{p2_poke_hpbar} {battle_data[p2_id]['pokemon'][p2_poke]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke]['final_hp']}\n\n"
            f"**Your:** {p1_poke.split('_')[0].title()} (Lv.100) {p1hppercent:.0f}%\n"
            f"{p1_poke_hpbar} {battle_data[p1_id]['pokemon'][p1_poke]['current_hp']}/{battle_data[p1_id]['pokemon'][p1_poke]['final_hp']}"
        )

        battle_state[p1_id]["turn"] = 1
        battle_state[p1_id]["waiting_for_action"] = True

        p2_text = (
            f"**⚔️ Turn {battle_state[p2_id]['turn']} - Singles Battle ⚔️**\n\n"
            f"**Opponent:** {p1_poke.split('_')[0].title()} (Lv.100) {p1hppercent:.0f}%\n"
            f"{p1_poke_hpbar} {battle_data[p1_id]['pokemon'][p1_poke]['current_hp']}/{battle_data[p1_id]['pokemon'][p1_poke]['final_hp']}\n\n"
            f"**Your:** {p2_poke.split('_')[0].title()} (Lv.100) {p2hppercent:.0f}%\n"
            f"{p2_poke_hpbar} {battle_data[p2_id]['pokemon'][p2_poke]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke]['final_hp']}"
        )

        battle_state[p2_id]["turn"] = 1
        battle_state[p2_id]["waiting_for_action"] = True

        try:
            await room[p1_id]["start_msg"].edit(p1_text, buttons=p1_poke_buttons)
            await room[p2_id]["start_msg"].edit(p2_text, buttons=p2_poke_buttons)
        except Exception as e:
            print(f"DEBUG: Error updating battle UI: {e}")

    elif fmt == "doubles":
        # Doubles battle UI (simplified for now)
        p1_poke1 = battle_state[p1_id]["active_pokemon"][0]
        p1_poke2 = battle_state[p1_id]["allowed_pokemon"][1] if len(battle_state[p1_id]["allowed_pokemon"]) > 1 else p1_poke1

        battle_state[p1_id]["active_pokemon"] = [p1_poke1, p1_poke2]
        battle_state[p2_id]["active_pokemon"] = [battle_state[p2_id]["allowed_pokemon"][0], 
                                               battle_state[p2_id]["allowed_pokemon"][1] if len(battle_state[p2_id]["allowed_pokemon"]) > 1 else battle_state[p2_id]["allowed_pokemon"][0]]

        # For doubles, just use the first Pokemon's moves for now
        p1_buttons = await button_generator(battle_data[p1_id]["pokemon"][p1_poke1]["moves"], p1_id, p1_poke1)
        p2_buttons = await button_generator(battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]["moves"], p2_id, battle_state[p2_id]["active_pokemon"][0])

        p1_text = f"**⚔️ Turn {battle_state[p1_id]['turn']} - Doubles Battle ⚔️**\n\nChoose your action with {p1_poke1.split('_')[0].title()}:"
        p2_text = f"**⚔️ Turn {battle_state[p2_id]['turn']} - Doubles Battle ⚔️**\n\nChoose your action with {battle_state[p2_id]['active_pokemon'][0].split('_')[0].title()}:"

        await room[p1_id]["start_msg"].edit(p1_text, buttons=p1_buttons)
        await room[p2_id]["start_msg"].edit(p2_text, buttons=p2_buttons)

async def move_data_extract(move):
    """Extract move data from JSON file or return defaults"""
    try:
        with open('move_data.json', 'r') as f:
            move_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default values if file not found
        return "normal", "physical", 40, 100

    move_info = move_data.get(move)
    if not move_info:
        return "normal", "physical", 40, 100

    type_name = move_info.get("type", "normal")
    category = move_info.get("category", "physical")
    power = move_info.get("power", 40)
    acc = move_info.get("accuracy", 100)

    return type_name, category, power, acc

async def type_modifier(move_type, opp_type1, opp_type2=None):
    """Calculate type effectiveness"""
    try:
        type_effect_modifier = type1_modifier[move_type.lower()][opp_type1.lower()]
        if opp_type2 and opp_type2.lower() != opp_type1.lower():
            type_effect_modifier *= type1_modifier[move_type.lower()][opp_type2.lower()]
        return type_effect_modifier
    except:
        return 1

async def accuracy_checker(accuracy):
    """Check if move hits based on accuracy"""
    if accuracy == "-" or accuracy is None:
        return True
    chance = random.randint(1, 100)
    return accuracy >= chance

async def damage_calc_fn(level, power, attack, defense, modifier=1):
    """Calculate damage using standard Pokemon damage formula"""
    if power == 0 or attack == 0 or defense == 0:
        return 0

    damage = (((((2 * level) / 5) + 2) * power * (attack / defense)) / 50 + 2) * modifier
    return max(1, int(damage))

def cleanup_battle(user_id):
    """Clean up all battle-related data for a user"""
    if user_id in battle_state:
        del battle_state[user_id]
    if user_id in battle_data:
        del battle_data[user_id]
    if user_id in selected_action:
        del selected_action[user_id]
    if user_id in room:
        room_id = room[user_id]["roomid"]
        if room_id in room_userids:
            del room_userids[room_id]
        if room_id in roomids:
            roomids.remove(room_id)
        del room[user_id]
    if user_id in selectteam:
        del selectteam[user_id]

async def check_battle_end(p1_id, p2_id):
    """Check if the battle has ended and declare winner"""
    p1_alive = any(battle_data[p1_id]["pokemon"][poke]["current_hp"] > 0 
                   for poke in battle_state[p1_id]["allowed_pokemon"])
    p2_alive = any(battle_data[p2_id]["pokemon"][poke]["current_hp"] > 0 
                   for poke in battle_state[p2_id]["allowed_pokemon"])

    if not p1_alive:
        # P2 wins
        winner_text = f"🏆 **Victory!** 🏆\n\nYou defeated your opponent!"
        loser_text = f"💔 **Defeat!** 💔\n\nAll your Pokémon have fainted!"

        try:
            await room[p2_id]["start_msg"].edit(winner_text)
            await room[p1_id]["start_msg"].edit(loser_text)
        except:
            pass

        cleanup_battle(p1_id)
        cleanup_battle(p2_id)
        return True

    elif not p2_alive:
        # P1 wins
        winner_text = f"🏆 **Victory!** 🏆\n\nYou defeated your opponent!"
        loser_text = f"💔 **Defeat!** 💔\n\nAll your Pokémon have fainted!"

        try:
            await room[p1_id]["start_msg"].edit(winner_text)
            await room[p2_id]["start_msg"].edit(loser_text)
        except:
            pass

        cleanup_battle(p1_id)
        cleanup_battle(p2_id)
        return True

    return False

async def handle_pokemon_faint(user_id, fainted_pokemon):
    """Handle when a Pokemon faints"""
    battle_state[user_id]["fainted_pokemon"].append(fainted_pokemon)

    # Remove from active Pokemon
    if fainted_pokemon in battle_state[user_id]["active_pokemon"]:
        battle_state[user_id]["active_pokemon"].remove(fainted_pokemon)

    # Check for available Pokemon to switch in
    available = [poke for poke in battle_state[user_id]["allowed_pokemon"] 
                if (poke not in battle_state[user_id]["fainted_pokemon"] and 
                    poke not in battle_state[user_id]["active_pokemon"])]

    if available:
        # Force switch to next available Pokemon
        next_pokemon = available[0]
        battle_state[user_id]["active_pokemon"].append(next_pokemon)
        return next_pokemon

    return None

async def switch_pokemon(user_id, new_pokemon):
    """Handle Pokemon switching"""
    if battle_state[user_id]["fmt"] == "singles":
        # In singles, replace the active Pokemon
        battle_state[user_id]["active_pokemon"] = [new_pokemon]
    else:
        # In doubles, this would be more complex
        # For now, just replace the first active Pokemon
        if battle_state[user_id]["active_pokemon"]:
            battle_state[user_id]["active_pokemon"][0] = new_pokemon
        else:
            battle_state[user_id]["active_pokemon"] = [new_pokemon]

    return True

async def move_handler(user_id, fmt, move, poke, event):
    """Handle move execution with proper damage calculation"""
    print(f"DEBUG: Move handler called - User: {user_id}, Move: {move}, Pokemon: {poke}")

    try:
        if user_id not in room:
            print(f"DEBUG: User {user_id} not in room")
            return False

        opponent_id = room[user_id]["opponent"]

        if opponent_id not in battle_state:
            print(f"DEBUG: Opponent {opponent_id} not in battle_state")
            return False

        attacker_pokemon = battle_data[user_id]["pokemon"][poke]
        opponent_active = battle_state[opponent_id]["active_pokemon"][0]
        defender_pokemon = battle_data[opponent_id]["pokemon"][opponent_active]

        # Get move data
        move_type, category, power, accuracy = await move_data_extract(move)

        # Check if move hits
        if not await accuracy_checker(accuracy):
            damage = 0
            hit_text = f"{poke.split('_')[0].title()}'s {move} missed!"
        else:
            # Calculate damage
            if category.lower() == "physical":
                attack_stat = attacker_pokemon["stats"]["att"]
                defense_stat = defender_pokemon["stats"]["def"]
            elif category.lower() == "special":
                attack_stat = attacker_pokemon["stats"]["spa"]
                defense_stat = defender_pokemon["stats"]["spd"]
            else:  # Status moves
                attack_stat = defense_stat = 1
                power = 0

            # Get type effectiveness
            defender_type1 = defender_pokemon.get("type1", "normal")
            defender_type2 = defender_pokemon.get("type2")
            type_effectiveness = await type_modifier(move_type, defender_type1, defender_type2)

            # Calculate base damage
            damage = await damage_calc_fn(100, power, attack_stat, defense_stat, type_effectiveness)

            # Add random factor (85-100%)
            damage = int(damage * random.uniform(0.85, 1.0))

            # Apply damage
            current_hp = battle_data[opponent_id]["pokemon"][opponent_active]["current_hp"]
            new_hp = max(0, current_hp - damage)
            battle_data[opponent_id]["pokemon"][opponent_active]["current_hp"] = new_hp

            # Create hit text
            effectiveness_text = ""
            if type_effectiveness > 1:
                effectiveness_text = "\nIt's super effective!"
            elif type_effectiveness < 1 and type_effectiveness > 0:
                effectiveness_text = "\nIt's not very effective..."
            elif type_effectiveness == 0:
                effectiveness_text = "\nIt had no effect!"

            hit_text = f"{poke.split('_')[0].title()} used {move}!\n{opponent_active.split('_')[0].title()} took {damage} damage!{effectiveness_text}"

            # Check if Pokemon fainted
            if new_hp <= 0:
                hit_text += f"\n\n{opponent_active.split('_')[0].title()} fainted!"

                # Handle fainted Pokemon
                replacement = await handle_pokemon_faint(opponent_id, opponent_active)
                if replacement:
                    hit_text += f"\n{replacement.split('_')[0].title()} was sent out!"

                # Check if battle ended
                if await check_battle_end(user_id, opponent_id):
                    return True

        # Update both players with the move result
        try:
            room_id = room[user_id]["roomid"]
            p1_id, p2_id = room_userids[room_id]

            result_text = f"**📢 Battle Update**\n\n{hit_text}\n\n_Preparing next turn..._"

            await room[p1_id]["start_msg"].edit(result_text)
            await room[p2_id]["start_msg"].edit(result_text)

            # Wait a moment for players to read the result
            await asyncio.sleep(3)

            # Start next turn
            await start_new_turn(room_id)

        except Exception as e:
            print(f"DEBUG: Error in move handler: {e}")

        return True

    except Exception as e:
        print(f"DEBUG: Error in move_handler: {e}")
        return False

async def start_new_turn(room_id):
    """Start a new turn after actions are resolved"""
    try:
        p1_id, p2_id = room_userids[room_id]

        # Increment turn counter
        battle_state[p1_id]["turn"] += 1
        battle_state[p2_id]["turn"] += 1

        # Reset action tracking
        battle_state[p1_id]["waiting_for_action"] = True
        battle_state[p2_id]["waiting_for_action"] = True
        selected_action[p1_id] = {}
        selected_action[p2_id] = {}

        # Update battle UI for new turn
        await first_battle_ui(battle_state[p1_id]["mode"], battle_state[p1_id]["fmt"], p1_id, None)

    except Exception as e:
        print(f"DEBUG: Error starting new turn: {e}")

async def awaiting_move_action(room_id, fmt, move, poke, event):
    """Wait for both players to select their actions, then resolve them"""
    try:
        if room_id not in room_userids:
            return

        p1, p2 = room_userids[room_id]

        # Wait for both players to make their actions
        timeout = 60  # 60 second timeout
        start_time = asyncio.get_event_loop().time()

        while True:
            current_time = asyncio.get_event_loop().time()
            if current_time - start_time > timeout:
                # Handle timeout - auto-forfeit for players who didn't act
                for player in [p1, p2]:
                    if not selected_action.get(player) or selected_action[player].get("turn") != battle_state[player]["turn"]:
                        # Player didn't act, they forfeit
                        opponent = p2 if player == p1 else p1
                        try:
                            await room[opponent]["start_msg"].edit("🏆 **Victory!** 🏆\n\nYour opponent didn't act in time!")
                            await room[player]["start_msg"].edit("💔 **Defeat!** 💔\n\nYou took too long to act!")
                        except:
                            pass
                        cleanup_battle(p1)
                        cleanup_battle(p2)
                return

            # Check if both players have made their actions
            p1_ready = (p1 in selected_action and 
                       selected_action[p1].get("turn") == battle_state[p1]["turn"])
            p2_ready = (p2 in selected_action and 
                       selected_action[p2].get("turn") == battle_state[p2]["turn"])

            if p1_ready and p2_ready:
                # Both players ready - resolve actions
                await resolve_turn_actions(room_id)
                return

            await asyncio.sleep(1)

    except Exception as e:
        print(f"DEBUG: Error in awaiting_move_action: {e}")

async def resolve_turn_actions(room_id):
    """Resolve the actions of both players based on priority"""
    try:
        p1, p2 = room_userids[room_id]

        p1_action = selected_action[p1]
        p2_action = selected_action[p2]

        # Create action order based on priority
        actions = []

        # Switching always goes first
        if p1_action.get("type") == ACTION_SWITCH:
            actions.append((p1, p1_action))
        if p2_action.get("type") == ACTION_SWITCH:
            actions.append((p2, p2_action))

        # Then moves based on speed
        move_actions = []
        if p1_action.get("type") == ACTION_MOVE:
            move_actions.append((p1, p1_action))
        if p2_action.get("type") == ACTION_MOVE:
            move_actions.append((p2, p2_action))

        # Sort moves by speed
        if len(move_actions) > 1:
            p1_speed = battle_data[move_actions[0][0]]["pokemon"][battle_state[move_actions[0][0]]["active_pokemon"][0]]["stats"]["spe"]
            p2_speed = battle_data[move_actions[1][0]]["pokemon"][battle_state[move_actions[1][0]]["active_pokemon"][0]]["stats"]["spe"]

            if p1_speed >= p2_speed:
                actions.extend(move_actions)
            else:
                actions.extend(move_actions[::-1])
        else:
            actions.extend(move_actions)

        # Execute actions in order
        for user_id, action in actions:
            if action["type"] == ACTION_SWITCH:
                await switch_pokemon(user_id, action["pokemon"])
            elif action["type"] == ACTION_MOVE:
                # Check if Pokemon is still active and alive
                active_pokemon = battle_state[user_id]["active_pokemon"][0]
                if battle_data[user_id]["pokemon"][active_pokemon]["current_hp"] > 0:
                    result = await move_handler(user_id, battle_state[user_id]["fmt"], 
                                              action["move"], action["pokemon"], None)
                    if result:  # Battle ended
                        return

    except Exception as e:
        print(f"DEBUG: Error resolving turn actions: {e}")

async def standing_by_fn(event, user_id):
    """Show standing by message"""
    await event.edit("__Standing by...__")

# Export the register function
__all__ = ['register_battle_handlers']
