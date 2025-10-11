from telethon import events, Button
from telethon.errors.rpcerrorlist import MessageNotModifiedError
import random
import asyncio
import json
import re
from database import users, pokedata, battles_db, matchmaking

# Battle state dictionaries
battle_data = {}
battle_state = {}
invitecode = {}
textic = {}
room = {}
selected_move = {}
player_move_done = {}
roomids = []
rs_lobby = []
rd_lobby = []
cs_lobby = []
cd_lobby = []
searchmsg = {}
selectteam = {}
room_userids = {}
movetext = {}
status_effects = {}
# all moves (sample list; keep synced with moves.json if you have it)
all_moves = ["Cut", "Drill Peck", "Egg Bomb", "Gust", "Horn Attack", "Hydro Pump", "Mega Kick", "Mega Punch", "Pay Day", "Peck", "Pound", "Rock Throw", "Scratch", "Slam", "Sonic Boom", "Strength", "Swift"]
# Only damage dealing moves (sample)
only_damage_moves = all_moves.copy()
# Never miss moves
never_miss_moves = ["Swift"]
# Paralyze moves
paralyze_moves = ["Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz", "Body Slam", "Lick", "Thunder", "Thunder Punch", "Thunder Shock", "Thunderbolt", "Splishy Splash"]
paralyze_moves30 = ["Body Slam", "Lick", "Thunder", "Splishy Splash"]
paralyze_moves10 = ["Thunder Punch", "Thunder Shock", "Thunderbolt"]
always_paralyze_moves = ["Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz"]
# flinch moves
flinch_moves = []
flinch_moves10 = []
flinch_moves20 = []
flinch_moves30 = []
always_flinch_moves = []
# burn moves
burn_moves = ["Sizzly Slide"]
burn_moves10 = []
burn_moves20 = []
always_burn_moves = ["Sizzly Slide"]
# Type effectiveness chart (partial / example)
type1_modifier = {
    "normal": {"normal": 1, "rock": 0.5, "ghost": 0, "steel": 1},
    "fire": {"grass": 2, "water": 0.5, "fire": 0.5, "rock": 0.5, "steel": 2},
    "water": {"fire": 2, "water": 0.5, "grass": 0.5, "ground": 2},
    "electric": {"water": 2, "ground": 0, "flying": 2, "electric": 0.5},
    # add the rest as you need
}


def register_battle_handlers(bot):

    @bot.on(events.NewMessage(pattern='/battle_stadium'))
    async def battle_stadium(event):
        user_id = event.sender_id
        if not event.is_private:
            return

        if battle_state.get(user_id):
            await event.reply("This action cant be done")
            return

        connect_msg = await event.reply("__**Communicating....Please stand by!**__")

        text = (
            "╭─「 __**Battle Stadium**__ 」\n"
            "├ __**Select a mode below:**__\n"
            "├ ⫸__**Ranked Battles**__⫷ — __Battle other player and rank up!__\n"
            "└ ⫸__**Casual Battles**__⫷ — __Play casual matches with friends__\n"
        )

        buttons = [
            [Button.inline("Ranked Battles", data=b"mode:ranked")],
            [Button.inline("Casual Battles", data=b"mode:casual")]
        ]

        await connect_msg.edit(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"^mode:(ranked|casual)$"))
    async def select_mode(event):
        await event.edit("__**Communicating....Please stand by!**__")
        mode = event.pattern_match.group(1).decode()

        text = (
            "╭─「 __**Battle Stadium**__ 」\n"
            "├ __**Select a format below:**__\n"
            "├ ⫸__**Single Battles**__⫷ — __Battle using one Pokémon at a time__\n"
            "└ ⫸__**Double Battles**__⫷ — __Battle using two Pokémons at a time__\n"
        )

        buttons = [
            [Button.inline("Single Battle", data=f"{mode}:singles".encode())],
            [Button.inline("Doubles Battle", data=f"{mode}:doubles".encode())]
        ]

        await event.edit(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"^(ranked|casual):(singles|doubles)$"))
    async def select_format(event):
        user_id = event.sender_id
        await event.edit("__**Communicating....Please stand by!**__")
        mode, fmt = (g.decode() for g in event.pattern_match.groups())

        await event.edit("__**Preparing battle requirements...**__")
        await battle_create(user_id, mode, fmt)
        print("here you go", battle_data)

        battle_state[user_id] = {}
        battle_state[int(user_id)]["mode"] = mode
        battle_state[int(user_id)]["fmt"] = fmt
        battle_state[int(user_id)]["team"] = battle_data[int(user_id)]["team"]
        battle_state[int(user_id)]["allowed_pokemon"] = []
        battle_state[int(user_id)]["active_pokemon"] = []
        battle_state[int(user_id)]["battle_started"] = False
        battle_state[int(user_id)]["battle_initiated"] = True

        text = (
            "╭─「 __**Battle Stadium**__ 」\n"
            "├ __**How do you wanna matchmake? **__\n"
            "├ ⫸__**Search an opponent**__⫷ — __Search for an opposing trainer around the globe__\n"
            "└ ⫸__**Invite Code**__⫷ — __Battle with an opposing trainer using invite code! __\n"
        )

        buttons = [
            [Button.inline("Search an Opponent", data=f"{mode}:{fmt}:random".encode())],
            [Button.inline("Invite Code", data=f"{mode}:{fmt}:invitecode".encode())]
        ]

        await event.edit(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"^(ranked|casual):(singles|doubles):(random|invitecode)$"))
    async def matchmaking(event):
        mode, fmt, mm = (g.decode() for g in event.pattern_match.groups())

        if mm == "invitecode":
            while True:
                code = random.randint(0, 9999)
                if code not in invitecode:
                    invitecode[event.sender_id] = {}
                    invitecode[event.sender_id]["mode"] = mode
                    invitecode[event.sender_id]["fmt"] = fmt
                    invitecode[event.sender_id]["code"] = code
                    break

            text = (
                "╭─「 __**Battle Stadium**__ 」\n"
                f"├ __**Invite Code ⫸{code}⫷**__\n"
                "└ ⫸__**Enter Code**__⫷ — __Battle with an opposing trainer by entering invite code obtained from them! __\n"
            )

            buttons = [
                [Button.inline("Enter Code", data=f"{mode}:{fmt}:{mm}:enter_code".encode())]
            ]

            await event.edit(text, buttons=buttons)

        if mm == "random":
            user_id = event.sender_id

            if mode == "ranked" and fmt == "singles":
                lobby = rs_lobby
            elif mode == "ranked" and fmt == "doubles":
                lobby = rd_lobby
            elif mode == "casual" and fmt == "singles":
                lobby = cs_lobby
            elif mode == "casual" and fmt == "doubles":
                lobby = cd_lobby
            else:
                await event.edit("Something went wrong!\nMatchmaking Cancelled")
                return

            if user_id in lobby:
                await event.edit("You are already in lobby\nSearching for an opposing trainer...")
                return

            if user_id not in lobby:
                lobby.append(user_id)
                msg = await event.edit("__Searching for an opposing trainer__")
                searchmsg[user_id] = msg
                asyncio.create_task(search_for_opp_trainer(lobby))

    @bot.on(events.CallbackQuery(pattern=b"^(ranked|casual):(singles|doubles):(random|invitecode):(enter_code)$"))
    async def code_keyboard(event):
        mode, fmt, mm, ic = (g.decode() for g in event.pattern_match.groups())

        if ic == "enter_code":
            if event.sender_id in invitecode:
                del invitecode[event.sender_id]

            text = (
                "╭─「 __**Battle Stadium**__ 」\n"
                "└ ⫸__**Enter Code**__⫷ — __Battle with an opposing trainer by entering invite code obtained from them! __\n"
                "└ __**Code**__⫸__**Enter Code**__⫷ __\n"
            )

            await event.edit(text)

            textic[event.sender_id] = {
                "mode": mode,
                "fmt": fmt
            }

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):(ranked|casual):(singles|doubles):select:(.+)$"))
    async def select_pokemon(event):
        user_id_str, mode, fmt, poke = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        mode = mode.decode()
        fmt = fmt.decode()
        poke = poke.decode()

        print(mode, fmt)

        if mode == "ranked" and fmt == "singles":
            limit = 3
        elif mode == "ranked" and fmt == "doubles":
            limit = 4
        elif mode == "casual" and fmt == "doubles":
            limit = 6
        elif mode == "casual" and fmt == "singles":
            limit = 6
        else:
            limit = 0

        # init storage once
        if user_id not in selectteam:
            selectteam[user_id] = {"pokes": []}

        current_team = selectteam[user_id]["pokes"]

        if poke in current_team:
            # remove if already selected
            current_team.remove(poke)
            action_text = f"Removed {poke.split('_')[0]}"
        else:
            # check BEFORE adding
            if len(current_team) >= limit:
                await event.answer(
                    f"Maximum number of Pokémon can be selected: {limit}",
                    alert=True
                )
                return

            # safe to add
            current_team.append(poke)
            action_text = f"Added {poke.split('_')[0]}"

        # Show selected Pokemon with checkmarks
        p1p = []
        for i in battle_state[int(user_id)]["team"]:
            element = i.split("_")[0]
            if i in selectteam[user_id]["pokes"]:
                p1p.append(f"✅ {element}")
            else:
                p1p.append(f"⬜ {element}")

        p1p_text = "\n".join(f"__**⫸ {poke_name} ⫷**__" for poke_name in p1p)

        selected_count = len(selectteam[user_id]["pokes"])
        text = (
            f"╭─「 __**Team Preview ({selected_count}/{limit} selected)**__ 」\n\n"
            "├「__**Your Team**__」\n\n"
            f"{p1p_text}\n\n"
            f"__**{action_text}**__"
        )

        # Regenerate buttons with updated selection state
        p1team = battle_state[user_id]["team"]
        buttons = await build_team_buttons(p1team, user_id)

        try:
            await event.edit(text, buttons=buttons)
        except Exception as e:
            print(f"Edit failed: {e}")
            # Send toast notification instead
            await event.answer(action_text)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):(ranked|casual):(singles|doubles):(done)$"))
    async def done_callback(event):
        user_id_str, mode, fmt, done = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        mode = mode.decode()
        fmt = fmt.decode()

        print(f"DEBUG: Done callback triggered for user {user_id}")
        print(f"DEBUG: selectteam={selectteam}")

        if mode == "ranked" and fmt == "singles":
            limit = 3
        elif mode == "ranked" and fmt == "doubles":
            limit = 4
        elif mode == "casual" and fmt == "doubles":
            limit = 6
        elif mode == "casual" and fmt == "singles":
            limit = 6
        else:
            limit = 0

        if not selectteam.get(user_id):
            await event.answer(f"Selected no of Pokémon : 0/{limit}", alert=True)
            return

        selected_count = len(selectteam[user_id]['pokes'])

        if selected_count < limit:
            await event.answer(f"Please select {limit} Pokémon. Currently selected: {selected_count}", alert=True)
            return

        # Team selection is complete
        battle_state[user_id]["allowed_pokemon"] = selectteam[user_id]['pokes'].copy()
        battle_state[user_id]["team_finalize"] = True

        print(f"DEBUG: Team finalized for user {user_id}")
        await standing_by_fn(event, user_id)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):(ranked|casual):(singles|doubles):(opp_team)$"))
    async def view_opponent_team(event):
        user_id_str, mode, fmt, action = event.pattern_match.groups()
        user_id = int(user_id_str.decode())

        if user_id not in room or "opponent" not in room[user_id]:
            await event.answer("No opponent found!", alert=True)
            return

        opp_id = room[user_id]["opponent"]

        if opp_id not in battle_state or "team" not in battle_state[opp_id]:
            await event.answer("Opponent team not ready!", alert=True)
            return

        opp_team = battle_state[opp_id]["team"]

        opp_pokemon = []
        for poke_id in opp_team:
            poke_name = poke_id.split("_")[0]
            opp_pokemon.append(poke_name)

        opp_text = "\n".join(f"__**⫸ {poke} ⫷**__" for poke in opp_pokemon)

        text = (
            "╭─「 __**Opponent Team**__ 」\n\n"
            "├「__**Opponent's Team**__」\n\n"
            f"{opp_text}"
        )

        await event.answer(text, alert=True)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):(.+):move:(.+)$"))
    async def handle_move(event):
        user_id_str, poke, move = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        poke = poke.decode()
        move = move.decode()

        print(f"DEBUG: Move callback received for user {user_id} - {poke} uses {move}")

        # Get battle text and context
        battle_text = battle_state.get(user_id, {}).get("player_text", "")
        user_state = battle_state.get(user_id)
        if not user_state:
            await event.answer("Battle state not found.", alert=True)
            return

        fmt = user_state["fmt"]
        room_id = room[user_id]["roomid"]

        # Record selected move for this turn
        selected_move[user_id] = {
            "move": move,
            "pokemon": poke,
            "turn": battle_state[user_id].get("turn", 1)
        }

        # Edit the message to indicate the player is communicating
        text_data = room[user_id]["start_msg"]
        try:
            await text_data.edit(f"◌ communicating...\n{battle_text}")
        except MessageNotModifiedError:
            pass
        except Exception:
            # ignore other edit errors in UI path
            pass

        # Only ONE player should create the task (use the smaller ID as leader)
        p1_id = int(room_userids[room_id]["p1"])
        p2_id = int(room_userids[room_id]["p2"])

        p1_turn = selected_move.get(p1_id, {}).get("turn")
        p2_turn = selected_move.get(p2_id, {}).get("turn")
        current_turn = battle_state[user_id].get("turn", 1)

        p1_ready = (p1_turn == current_turn)
        p2_ready = (p2_turn == current_turn)

        if p1_ready and p2_ready and user_id == min(p1_id, p2_id):
            print(f"DEBUG: Both players ready, {user_id} (leader) starting move resolution")
            # spawn resolution task (no need to pass the move/poke; selected_move holds that)
            asyncio.create_task(awaiting_move_action(room_id, fmt, None, None, event))

        print(f"DEBUG: Move callback handled for user {user_id}")

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):pokemon_switch$"))
    async def handle_pokemon_switch(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())

        # Show available Pokemon to switch to
        await show_switch_menu(user_id, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):switch_to:(.+)$"))
    async def handle_switch_to_pokemon(event):
        user_id_str, poke = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        poke = poke.decode()

        # Check if this is a forced switch (after fainting) or voluntary
        # If active Pokemon HP is 0, this is forced
        active_poke = battle_state[user_id]["active_pokemon"][0]
        is_forced = (battle_data[user_id]["pokemon"][active_poke]["current_hp"] <= 0)

        # Execute the switch
        await switch_pokemon(user_id, poke, event, is_forced=is_forced)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):cancel_switch$"))
    async def handle_cancel_switch(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())

        # Return to battle UI
        fmt = battle_state[user_id]["fmt"]
        mode = battle_state[user_id]["mode"]
        await battle_ui(fmt, user_id, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):run$"))
    async def handle_run(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())

        # Handle running from battle
        await event.edit("You ran away from the battle!")
        # Clean up battle state
        if user_id in battle_state:
            del battle_state[user_id]
        if user_id in room:
            opp_id = room[user_id].get("opponent")
            if opp_id and opp_id in battle_state:
                # Notify opponent
                try:
                    opp_msg = room[opp_id].get("start_msg")
                    if opp_msg:
                        await opp_msg.edit("Opponent ran away! You win!")
                        del battle_state[opp_id]
                except:
                    pass
            room.pop(user_id, None)
            battle_data.pop(user_id, None)
            invitecode.pop(user_id, None)
            textic.pop(user_id, None)
            movetext.pop(user_id, None)
            room_userids.pop(user_id, None)
            searchmsg.pop(user_id, None)
            selectteam.pop(user_id, None)
            selected_move.pop(user_id, None)
            if opp_id:
                room.pop(opp_id, None)
                battle_data.pop(opp_id, None)
                invitecode.pop(opp_id, None)
                textic.pop(opp_id, None)
                movetext.pop(opp_id, None)
                room_userids.pop(opp_id, None)
                searchmsg.pop(opp_id, None)
                selectteam.pop(opp_id, None)
                selected_move.pop(opp_id, None)


async def battle_create(user_id, mode, format):
    user_dict = db_battle_extractor(user_id, mode, format)
    global battle_data
    if not isinstance(battle_data, dict):
        battle_data = {}
    battle_data.update(user_dict)


def db_battle_extractor(user_id, mode, format):
    user_data = users.find_one({"user_id": int(user_id)})
    if user_data is None:
        raise ValueError(f"No user found with id {user_id}")

    user_dict = {}
    user_poke = {}
    user_dict[user_id] = {}
    user_dict[user_id]["mode"] = mode
    user_dict[user_id]["fmt"] = format

    user_team = user_data["team"]
    user_dict[user_id]["team"] = user_team

    for i in user_team:
        poke = pokedata.find_one({"_id": i})
        if poke:
            poke["current_hp"] = poke["final_hp"]
            user_poke[i] = poke

    user_dict[user_id]["pokemon"] = user_poke
    return user_dict


async def generate_room_id():
    while True:
        room_id = random.randint(0, 999999)
        if room_id not in roomids:
            roomids.append(room_id)
            return room_id
        await asyncio.sleep(0.1)


async def build_team_buttons(team, id):
    """Return a two-column inline keyboard with Done + View Opponent buttons."""
    buttons = []
    mode = battle_state[id]["mode"]
    fmt = battle_state[id]["fmt"]

    # Two buttons per row for Pokémon selection
    for i in range(0, len(team), 2):
        row = []
        for j in range(2):
            if i + j < len(team):
                poke_data = team[i + j]
                poke = poke_data.split("_")[0]

                # Check if this Pokemon is selected
                if id in selectteam and poke_data in selectteam[id]["pokes"]:
                    button_text = f"✅ {poke}"
                else:
                    button_text = f"⬜ {poke}"

                row.append(Button.inline(button_text, f"{id}:{mode}:{fmt}:select:{poke_data}"))
        buttons.append(row)

    # Add Done + View Opponent buttons at the bottom
    buttons.append([
        Button.inline("Done", f"{id}:{mode}:{fmt}:done"),
        Button.inline("View Opponent Team", f"{id}:{mode}:{fmt}:opp_team")
    ])

    return buttons


async def team_preview(p1, p2):
    p1_msg = room[p1]["start_msg"]
    p2_msg = room[p2]["start_msg"]

    await p1_msg.edit("__**Communicating...Please stand by**__")
    await p2_msg.edit("__**Communicating...Please stand by**__")

    p1p = []
    p2p = []

    for i in battle_state[int(p1)]["team"]:
        element = i.split("_")[0]
        p1p.append(element)

    for i in battle_state[int(p2)]["team"]:
        element = i.split("_")[0]
        p2p.append(element)

    p1p_text = "\n".join(f"__**⫸ {poke} ⫷**__" for idx, poke in enumerate(p1p))
    p2p_text = "\n".join(f"__**⫸ {poke} ⫷**__" for idx, poke in enumerate(p2p))

    textp1 = (
        "╭─「 __**Team Preview**__ 」\n\n"
        "├「__**Your Team**__」\n\n"
        f"{p1p_text}"
    )

    p1team = battle_state[p1]["team"]
    p2team = battle_state[p2]["team"]

    buttons_p1 = await build_team_buttons(p1team, p1)
    buttons_p2 = await build_team_buttons(p2team, p2)

    textp2 = (
        "╭─「 __**Team Preview**__ 」\n\n"
        "├「__**Your Team**__」\n\n"
        f"{p2p_text}"
    )

    await p1_msg.edit(textp1, buttons=buttons_p1)
    await p2_msg.edit(textp2, buttons=buttons_p2)


async def search_for_opp_trainer(lobby):
    timeout = 120
    starttime = asyncio.get_event_loop().time()

    while True:
        currenttime = asyncio.get_event_loop().time()

        # Check for matches FIRST (before timeout)
        if len(lobby) >= 2:
            p1, p2 = random.sample(lobby, 2)
            try:
                lobby.remove(p1)
                lobby.remove(p2)
            except ValueError:
                # they might have been removed concurrently
                continue

            team_color = random.choice(["red", "blue"])
            room[p1] = {"team_colour": team_color}
            room[p2] = {"team_colour": "blue" if team_color == "red" else "red"}

            roomid = await generate_room_id()
            room[p1]["roomid"] = roomid
            room[p2]["roomid"] = roomid
            room[p1]["battle_msg"] = ""
            room[p2]["battle_msg"] = ""
            room[p1]["opponent"] = p2
            room[p2]["opponent"] = p1

            room_userids[roomid] = {
                "p1": p1,
                "p2": p2
            }

            room[p1]["start_msg"] = searchmsg[p1]
            room[p2]["start_msg"] = searchmsg[p2]

            del searchmsg[p1]
            del searchmsg[p2]

            await team_preview(p1, p2)
            break

        # Check for timeout - remove players who have waited too long
        for uid in lobby[:]:  # Create a copy of the list to iterate
            if currenttime - starttime > timeout:
                try:
                    lobby.remove(uid)
                except ValueError:
                    pass
                if uid in searchmsg:
                    await searchmsg[uid].edit("__Matchmaking timeout!__")
                    del searchmsg[uid]

        # If lobby is now empty, exit
        if len(lobby) == 0:
            break

        await asyncio.sleep(1)


async def button_generator(moves, user_id, poke):
    """Generate buttons for a Pokémon's move list."""
    buttons = []
    for i in range(0, len(moves), 2):
        row = []
        for j in range(2):
            if i + j < len(moves):
                move = moves[i + j]
                row.append(Button.inline(move, f"{user_id}:{poke}:move:{move}"))
        buttons.append(row)

    # Add extra action buttons
    buttons.append([
        Button.inline("Switch Pokémon", f"{user_id}:pokemon_switch"),
        Button.inline("Run", f"{user_id}:run")
    ])

    return buttons


async def hp_bar(current_hp, max_hp):
    """Generate HP bar visualization."""
    if max_hp == 0:
        percentage = 0
    else:
        percentage = (current_hp / max_hp) * 100

    # 10-segment bar
    filled = int(percentage / 10)
    empty = 10 - filled

    if percentage > 50:
        color = "🟩"
    elif percentage > 20:
        color = "🟨"
    else:
        color = "🟥"

    return color * filled + "⬜" * empty


async def type_modifier(move_type, defender_type1, defender_type2=None):
    """Calculate type effectiveness multiplier. Returns a numeric multiplier or string message."""
    move_type = (move_type or "normal").lower()
    defender_type1 = (defender_type1 or "normal").lower()

    modifier = type1_modifier.get(move_type, {}).get(defender_type1, 1)

    if defender_type2:
        defender_type2 = defender_type2.lower()
        modifier *= type1_modifier.get(move_type, {}).get(defender_type2, 1)

    return modifier


async def move_data_extract(move):
    try:
        with open("moves.json", "r") as f:
            move_data = json.load(f)

        key = move.replace(" ", "-").lower()

        if key not in move_data:
            return "normal", "physical", 40, 100

        move_info = move_data[key]
        type_name = move_info.get("Type", "normal")
        category = move_info.get("Category", "physical")
        power = move_info.get("Power", 0)
        acc = move_info.get("Accuracy", 100)

        return type_name, category, power, acc
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return "normal", "physical", 50, 100


async def accuracy_checker(accuracy, move):
    """Return True if the move hits."""
    if move in never_miss_moves:
        return True
    if accuracy is None:
        return True
    try:
        acc = float(accuracy)
    except Exception:
        return True

    acc_pct = acc * 100.0 if acc <= 1.0 else acc
    roll = random.uniform(0, 100)
    return roll <= acc_pct


def interpret_type_effect(type_eff):
    """Return (multiplier, effect_text) given a numeric or string type effectiveness."""
    mapping = {
        0.0: "It does not affect",
        0.25: "It's extremely ineffective",
        0.5: "It's not very effective",
        1.0: "Effective",
        2.0: "It's super effective",
        4.0: "It's extremely effective",
    }

    # Numeric case
    if isinstance(type_eff, (int, float)):
        mult = float(type_eff)
        text = mapping.get(mult, "Effective")
        return mult, text

    s = str(type_eff).lower()
    if "no effect" in s or "does not" in s or "doesn't" in s:
        return 0.0, mapping[0.0]
    if "extremely ineffective" in s or "0.25" in s:
        return 0.25, mapping[0.25]
    if "not very" in s or "0.5" in s:
        return 0.5, mapping[0.5]
    if "super" in s or "2x" in s or "2×" in s:
        return 2.0, mapping[2.0]
    if "extremely effective" in s or "4x" in s or "4×" in s:
        return 4.0, mapping[4.0]

    m = re.search(r"(\d+(\.\d+)?)\s*[x×]", s)
    if m:
        mult = float(m.group(1))
        return mult, mapping.get(mult, "Effective")

    return 1.0, mapping[1.0]


async def damage_calc_fn(level, power, attack, defense, type_multiplier, move):
    """Calculate Pokémon-style damage.
    `type_multiplier` must be numeric.
    Returns: (damage:int, is_critical:bool)
    """
    try:
        type_mult = float(type_multiplier)
    except Exception:
        type_mult = 1.0
    if move == "Pay Day":
        return 20, False
    is_critical = (random.randint(1, 24) == 1)
    critical_mult = 1.5 if is_critical else 1.0

    base = ((((2 * level) / 5) + 2) * power * (attack / (defense if defense > 0 else 1))) / 50 + 2
    damage = base * type_mult * critical_mult * random.uniform(0.85, 1.0)

    return max(1, int(damage)), is_critical  # ensure at least 1 damage


async def first_battle_ui(mode, fmt, user_id, event):
    """Initialize the first battle UI for both players."""
    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])

        # Initialize turn counter only if not already present
        battle_state[p1_id].setdefault("turn", 1)
        battle_state[p2_id].setdefault("turn", 1)

        p1_textmsg = room[p1_id]["start_msg"]
        p2_textmsg = room[p2_id]["start_msg"]

        p1_poke = battle_state[p1_id]["active_pokemon"][0]
        p2_poke = battle_state[p2_id]["active_pokemon"][0]

        p1_poke_moves = battle_data[p1_id]["pokemon"][p1_poke]["moves"]
        p1_poke_buttons = await button_generator(p1_poke_moves, p1_id, p1_poke)

        p2_poke_moves = battle_data[p2_id]["pokemon"][p2_poke]["moves"]
        p2_poke_buttons = await button_generator(p2_poke_moves, p2_id, p2_poke)

        print(f"DEBUG: Battle data ready for {user_id}")

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
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke_hpbar} {p2hppercent:.0f}% \n"
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke_hpbar} {battle_data[p1_id]['pokemon'][p1_poke]['current_hp']}/{battle_data[p1_id]['pokemon'][p1_poke]['final_hp']}"
        )

        p2_text = (
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke_hpbar} {p1hppercent:.0f}% \n"
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke_hpbar} {battle_data[p2_id]['pokemon'][p2_poke]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke]['final_hp']}"
        )

        battle_state[p1_id]["player_text"] = p1_text
        battle_state[p2_id]["player_text"] = p2_text

        await p1_textmsg.edit(p1_text, buttons=p1_poke_buttons)
        await p2_textmsg.edit(p2_text, buttons=p2_poke_buttons)

        print(f"DEBUG: First battle UI initialized for room {roomid}")


async def paralyze_check(move):
    chance = 0
    if move in paralyze_moves10:
        chance = 10
    if move in paralyze_moves30:
        chance = 30
    if move in always_paralyze_moves:
        return True
    rvalue = random.randint(1, 100)
    return chance >= rvalue


async def flinch_check(move):
    chance = 0
    if move in flinch_moves10:
        chance = 10
    if move in flinch_moves20:
        chance = 20
    if move in flinch_moves30:
        chance = 30
    if move in always_flinch_moves:
        return True
    rvalue = random.randint(1, 100)
    return chance >= rvalue


async def burn_check(move):
    chance = 0
    if move in burn_moves10:
        chance = 10
    if move in burn_moves20:
        chance = 20
    if move in always_burn_moves:
        return True
    rvalue = random.randint(1, 100)
    return chance >= rvalue


async def paralysis_checker():
    chance = random.randint(1, 100)
    return True if chance <= 25 else False


async def move_handler(user_id, move, poke, fmt, event):
    """Resolve a single player's chosen move and apply effects to defender.
    Returns True on success, False on error.
    """

    print(f"DEBUG: Move handler called - User: {user_id}, Move: {move}, Pokemon: {poke}")

    try:
        if fmt != "singles":
            # For now only singles implemented
            return False

        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        opponent_id = p2_id if user_id == p1_id else p1_id

        # Ensure movetext containers exist
        movetext.setdefault(p1_id, {"text_sequence": [], "hp_update_at": 999})
        movetext.setdefault(p2_id, {"text_sequence": [], "hp_update_at": 999})

        # Initialize status effects for room if needed
        if roomid not in status_effects:
            status_effects[roomid] = {}
            conditions = ["paralysis", "burn", "poison", "sleep", "confusion", "freeze", "flinch"]
            status_effects[roomid][p1_id] = {cond: [] for cond in conditions}
            status_effects[roomid][p2_id] = {cond: [] for cond in conditions}

        # Attacker and defender data
        attacker_poke_id = poke
        defender_poke_id = battle_state[opponent_id]["active_pokemon"][0]

        attacker_pokemon = battle_data[user_id]["pokemon"][attacker_poke_id]
        defender_pokemon = battle_data[opponent_id]["pokemon"][defender_poke_id]

        attacker_name = attacker_poke_id.split("_")[0]
        defender_name = defender_poke_id.split("_")[0]

        # invalid move
        if move not in all_moves:
            used_text_self = f"{attacker_name} used {move}"
            miss_text = f"This move can't be used!"
            used_text_opp = f"Opposing {attacker_name} used {move}!"

            movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
            movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])
            movetext[user_id]["hp_update_at"] = 999
            movetext[opponent_id]["hp_update_at"] = 999
            print("DEBUG movetext (invalid move):", movetext)
            return True

        # Check paralysis / flinch status on attacker
        if attacker_poke_id in status_effects[roomid][user_id]["paralysis"]:
            if await paralysis_checker():
                used_text_self = f"{attacker_name} is paralyzed! It can't move!"
                used_text_opp = f"Opposing {attacker_name} is paralyzed! It can't move!"
                movetext[user_id]["text_sequence"].extend([used_text_self])
                movetext[opponent_id]["text_sequence"].extend([used_text_opp])
                movetext[user_id]["hp_update_at"] = 999
                movetext[opponent_id]["hp_update_at"] = 999
                return True

        if attacker_poke_id in status_effects[roomid][user_id]["flinch"]:
            used_text_self = f"{attacker_name} flinched and couldn't move!"
            used_text_opp = f"Opposing {attacker_name} flinched and couldn't move!"
            movetext[user_id]["text_sequence"].extend([used_text_self])
            movetext[opponent_id]["text_sequence"].extend([used_text_opp])
            movetext[user_id]["hp_update_at"] = 999
            movetext[opponent_id]["hp_update_at"] = 999
            # remove flinch effect for this pokemon
            try:
                status_effects[roomid][user_id]["flinch"].remove(attacker_poke_id)
            except ValueError:
                pass
            return True

        # Move data
        move_type, category, power, accuracy = await move_data_extract(move)

        # Accuracy check
        hit = await accuracy_checker(accuracy, move)
        if not hit:
            used_text_self = f"{attacker_name} used {move}!"
            miss_text = f"{defender_name} avoided the attack!"
            used_text_opp = f"Opposing {attacker_name} used {move}!"
            movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
            movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])
            movetext[user_id]["hp_update_at"] = 999
            movetext[opponent_id]["hp_update_at"] = 999
            return True

        # Stats selection
        if category.lower() == "physical":
            attack_stat = attacker_pokemon.get("final_atk", attacker_pokemon.get("stats", {}).get("atk", 50))
            defense_stat = defender_pokemon.get("final_def", defender_pokemon.get("stats", {}).get("def", 50))
        else:
            attack_stat = attacker_pokemon.get("final_spa", attacker_pokemon.get("stats", {}).get("spa", 50))
            defense_stat = defender_pokemon.get("final_spd", defender_pokemon.get("stats", {}).get("spd", 50))

        # Type effectiveness (numeric multiplier)
        type_multiplier_raw = await type_modifier(move_type, defender_pokemon.get("type1", "normal"), defender_pokemon.get("type2"))
        type_mult, effect_text = interpret_type_effect(type_multiplier_raw)

        # Damage calculation
        damage, is_critical = await damage_calc_fn(100, power, attack_stat, defense_stat, type_mult, move)

        # Apply damage to defender's current HP
        old_hp = defender_pokemon.get("current_hp", defender_pokemon.get("final_hp", 100))
        new_hp = max(0, old_hp - damage)
        defender_pokemon["current_hp"] = new_hp
        # also update stats.hp if structure exists
        if "stats" in defender_pokemon:
            defender_pokemon["stats"]["hp"] = new_hp

        print(f"DEBUG: {attacker_name} (user {user_id}) attacks {defender_name} (user {opponent_id}) for {damage} damage (HP: {old_hp} -> {new_hp})")

        # Build text sequences
        used_text_self = f"{attacker_name} used {move}!"
        used_text_opp = f"Opposing {attacker_name} used {move}!"
        crit_text = "A critical hit!" if is_critical else None

        seq_self = [used_text_self]
        if crit_text:
            seq_self.append(crit_text)
        if power > 0 and effect_text != "Effective":
            seq_self.append(effect_text)

        seq_opp = [used_text_opp]

        # Status inflictions
        if move in paralyze_moves:
            par = await paralyze_check(move)
            par_list = status_effects[roomid][opponent_id]["paralysis"]
            if defender_poke_id in par_list:
                seq_self.append(f"The Opposing {defender_name} is already paralyzed!")
                seq_opp.append(f"{defender_name} is already paralyzed!")
            elif par:
                par_list.append(defender_poke_id)
                seq_self.append(f"The Opposing {defender_name} is paralyzed! It may be unable to move")
                seq_opp.append(f"{defender_name} is paralyzed! It may be unable to move")

        if move in burn_moves:
            br = await burn_check(move)
            br_list = status_effects[roomid][opponent_id]["burn"]
            if defender_poke_id in br_list:
                seq_self.append(f"The Opposing {defender_name} is already burned!")
                seq_opp.append(f"{defender_name} is already burned!")
            elif br:
                br_list.append(defender_poke_id)
                seq_self.append(f"The Opposing {defender_name} was burned!")
                seq_opp.append(f"{defender_name} was burned!")

        # Append sequences
        movetext[user_id]["text_sequence"].extend(seq_self)
        movetext[opponent_id]["text_sequence"].extend(seq_opp)
        movetext[user_id]["hp_update_at"] = 1
        movetext[opponent_id]["hp_update_at"] = 1

        # Update UIs
        await battle_ui(fmt, user_id, event)
        return True

    except Exception as e:
        print(f"ERROR in move_handler: {e}")
        import traceback
        traceback.print_exc()
        return False


async def battle_ui(fmt, user_id, event):
    """Configure the battle UI for singles battles."""
    if fmt != "singles":
        return

    roomid = room[user_id]["roomid"]
    p1_id = int(room_userids[roomid]["p1"])
    p2_id = int(room_userids[roomid]["p2"])

    # Do not reset turn here; ensure it's set elsewhere only when battle starts
    # Messages
    p1_textmsg = room[p1_id]["start_msg"]
    p2_textmsg = room[p2_id]["start_msg"]

    # Active Pokémon
    p1_poke = battle_state[p1_id]["active_pokemon"][0]
    p2_poke = battle_state[p2_id]["active_pokemon"][0]

    # Moves & Buttons
    p1_poke_moves = battle_data[p1_id]["pokemon"][p1_poke]["moves"]
    p1_poke_buttons = await button_generator(p1_poke_moves, p1_id, p1_poke)

    p2_poke_moves = battle_data[p2_id]["pokemon"][p2_poke]["moves"]
    p2_poke_buttons = await button_generator(p2_poke_moves, p2_id, p2_poke)

    # Helper to read HP info
    async def get_hp_info(pid, poke):
        current_hp = min(battle_data[pid]["pokemon"][poke]["current_hp"], battle_data[pid]["pokemon"][poke]["final_hp"])
        final_hp = battle_data[pid]["pokemon"][poke]["final_hp"]
        hp_bar_str = await hp_bar(current_hp, final_hp)
        hp_percent = (current_hp / final_hp * 100) if final_hp else 0
        return current_hp, final_hp, hp_bar_str, hp_percent

    p1_current_hp, p1_final_hp, p1_poke_hpbar, p1hppercent = await get_hp_info(p1_id, p1_poke)
    p2_current_hp, p2_final_hp, p2_poke_hpbar, p2hppercent = await get_hp_info(p2_id, p2_poke)

    # Main battle texts (initial / final placeholders; will be updated in sequence)
    p1_text_main = (
        f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p2_poke_hpbar} {p2hppercent:.0f}% \n"
        f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p1_poke_hpbar} {p1_current_hp}/{p1_final_hp}"
    )

    p2_text_main = (
        f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p1_poke_hpbar} {p1hppercent:.0f}% \n"
        f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p2_poke_hpbar} {p2_current_hp}/{p2_final_hp}"
    )

    # Get text sequences safely
    p1_textsequence = movetext.get(p1_id, {}).get("text_sequence", [])
    p2_textsequence = movetext.get(p2_id, {}).get("text_sequence", [])

    max_len = max(len(p1_textsequence), len(p2_textsequence))
    old_text = None

    for idx in range(max_len):
        i = p1_textsequence[idx] if idx < len(p1_textsequence) else ""
        j = p2_textsequence[idx] if idx < len(p2_textsequence) else ""

        if idx == 0:
            # first display includes player_text (previously stored)
            p1_text_to_send = f"{i}\n\n{battle_state[p1_id].get('player_text','')}"
            p2_text_to_send = f"{j}\n\n{battle_state[p2_id].get('player_text','')}"
            try:
                await p1_textmsg.edit(p1_text_to_send)
                await p2_textmsg.edit(p2_text_to_send)
            except MessageNotModifiedError:
                pass
            await asyncio.sleep(1.0)

            # then show the main battle view
            p1_text_to_send = f"{i}\n\n{p1_text_main}"
            p2_text_to_send = f"{j}\n\n{p2_text_main}"
        else:
            p1_text_to_send = f"{i}\n\n{p1_text_main}"
            p2_text_to_send = f"{j}\n\n{p2_text_main}"

        if p1_text_to_send != old_text:
            try:
                await p1_textmsg.edit(p1_text_to_send)
                await p2_textmsg.edit(p2_text_to_send)
            except MessageNotModifiedError:
                pass
            old_text = p1_text_to_send
            await asyncio.sleep(1.0)

    # After sequences, recompute HP bars to reflect damage applied
    p1_current_hp, p1_final_hp, p1_poke_hpbar, p1hppercent = await get_hp_info(p1_id, p1_poke)
    p2_current_hp, p2_final_hp, p2_poke_hpbar, p2hppercent = await get_hp_info(p2_id, p2_poke)

    p1_final_text = (
        f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p2_poke_hpbar} {p2hppercent:.0f}% \n"
        f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p1_poke_hpbar} {p1_current_hp}/{p1_final_hp}"
    )

    p2_final_text = (
        f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p1_poke_hpbar} {p1hppercent:.0f}% \n"
        f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p2_poke_hpbar} {p2_current_hp}/{p2_final_hp}"
    )

    # Update stored player_text and then show final UI with action buttons
    battle_state[p1_id]["player_text"] = p1_final_text
    battle_state[p2_id]["player_text"] = p2_final_text

    try:
        await p1_textmsg.edit(p1_final_text, buttons=p1_poke_buttons)
        await p2_textmsg.edit(p2_final_text, buttons=p2_poke_buttons)
    except MessageNotModifiedError:
        pass
    except Exception:
        # ignore UI edit errors
        pass

    print(f"DEBUG: Battle UI updated for room {roomid}")


async def show_switch_menu(user_id, event):
    """Show the Pokemon switching menu."""
    fmt = battle_state[user_id]["fmt"]

    if fmt == "singles":
        allowed_pokemon = battle_state[user_id]["allowed_pokemon"]
        active_pokemon = battle_state[user_id]["active_pokemon"][0]

        # Get available Pokemon to switch to (not fainted, not currently active)
        available_pokemon = []
        for poke_id in allowed_pokemon:
            if poke_id != active_pokemon and battle_data[user_id]["pokemon"][poke_id]["current_hp"] > 0:
                available_pokemon.append(poke_id)

        if not available_pokemon:
            await event.answer("No Pokemon available to switch!", alert=True)
            return

        # Build switch buttons
        buttons = []
        for poke_id in available_pokemon:
            poke_name = poke_id.split("_")[0]
            poke_hp = battle_data[user_id]["pokemon"][poke_id]["current_hp"]
            poke_max_hp = battle_data[user_id]["pokemon"][poke_id]["final_hp"]
            button_text = f"{poke_name} ({poke_hp}/{poke_max_hp} HP)"
            buttons.append([Button.inline(button_text, f"{user_id}:switch_to:{poke_id}")])

        # Add cancel button
        buttons.append([Button.inline("Cancel", f"{user_id}:cancel_switch")])

        text = "Select a Pokémon to switch to:"
        await event.edit(text, buttons=buttons)


async def show_forced_switch_menu(user_id, user_msg):
    """Show the Pokemon switching menu when forced to switch (Pokemon fainted)."""
    fmt = battle_state[user_id]["fmt"]

    if fmt == "singles":
        allowed_pokemon = battle_state[user_id]["allowed_pokemon"]

        # Get available Pokemon to switch to (not fainted)
        available_pokemon = []
        for poke_id in allowed_pokemon:
            if battle_data[user_id]["pokemon"][poke_id]["current_hp"] > 0:
                available_pokemon.append(poke_id)

        if not available_pokemon:
            return

        # Build switch buttons
        buttons = []
        for poke_id in available_pokemon:
            poke_name = poke_id.split("_")[0]
            poke_hp = battle_data[user_id]["pokemon"][poke_id]["current_hp"]
            poke_max_hp = battle_data[user_id]["pokemon"][poke_id]["final_hp"]
            button_text = f"{poke_name} ({poke_hp}/{poke_max_hp} HP)"
            buttons.append([Button.inline(button_text, f"{user_id}:switch_to:{poke_id}")])

        text = "Your Pokémon fainted! Choose a Pokémon to send out:"
        await user_msg.edit(text, buttons=buttons)


async def switch_pokemon(user_id, new_poke_id, event, is_forced=False):
    """Execute Pokemon switch."""
    fmt = battle_state[user_id]["fmt"]

    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        opponent_id = p2_id if user_id == p1_id else p1_id

        old_poke = battle_state[user_id]["active_pokemon"][0]
        old_poke_name = old_poke.split("_")[0]
        new_poke_name = new_poke_id.split("_")[0]

        # Update active Pokemon
        battle_state[user_id]["active_pokemon"][0] = new_poke_id

        # Prepare switch messages
        user_switch_text = f"{old_poke_name}, come back!\nGo, {new_poke_name}!"
        opp_switch_text = f"Opponent withdrew {old_poke_name}!\nOpponent sent out {new_poke_name}!"

        # Initialize movetext for both players
        movetext.setdefault(p1_id, {"text_sequence": [], "hp_update_at": 999})
        movetext.setdefault(p2_id, {"text_sequence": [], "hp_update_at": 999})

        movetext[user_id]["text_sequence"] = [user_switch_text]
        movetext[opponent_id]["text_sequence"] = [opp_switch_text]

        # If this is a voluntary switch (not forced by fainting), record it as the player's turn action
        if not is_forced:
            selected_move[user_id] = {
                "move": "SWITCH",
                "pokemon": new_poke_id,
                "turn": battle_state[user_id].get("turn", 1)
            }

            # Show "communicating" message
            text_data = room[user_id]["start_msg"]
            battle_text = battle_state[user_id].get("player_text", "")
            try:
                await text_data.edit(f"◌ communicating...\n\n{battle_text}")
            except MessageNotModifiedError:
                pass
            except Exception:
                pass

            # Trigger move action processing
            asyncio.create_task(awaiting_move_action(roomid, fmt, None, None, event))
        else:
            # Forced switch (after fainting) - just update UI immediately
            await battle_ui(fmt, user_id, event)


async def check_fainted_pokemon(user_id):
    """Check if active Pokemon has fainted and return True if it has."""
    active_poke = battle_state[user_id]["active_pokemon"][0]
    current_hp = battle_data[user_id]["pokemon"][active_poke]["current_hp"]
    return current_hp <= 0


async def handle_fainted_pokemon(user_id, event):
    """Handle when a Pokemon faints - prompt for switch or end battle."""
    roomid = room[user_id]["roomid"]
    p1_id = int(room_userids[roomid]["p1"])
    p2_id = int(room_userids[roomid]["p2"])
    opponent_id = p2_id if user_id == p1_id else p1_id

    active_poke = battle_state[user_id]["active_pokemon"][0]
    poke_name = active_poke.split("_")[0]

    # Initialize movetext
    movetext.setdefault(p1_id, {"text_sequence": [], "hp_update_at": 999})
    movetext.setdefault(p2_id, {"text_sequence": [], "hp_update_at": 999})

    # Add faint message
    user_faint_text = f"{poke_name} fainted!"
    opp_faint_text = f"Opposing {poke_name} fainted!"

    movetext[user_id]["text_sequence"].append(user_faint_text)
    movetext[opponent_id]["text_sequence"].append(opp_faint_text)

    # Check if user has any Pokemon left
    allowed_pokemon = battle_state[user_id]["allowed_pokemon"]
    available_pokemon = []
    for poke_id in allowed_pokemon:
        if battle_data[user_id]["pokemon"][poke_id]["current_hp"] > 0:
            available_pokemon.append(poke_id)

    if not available_pokemon:
        # User has no Pokemon left - they lose
        return "lost"

    # User still has Pokemon - force them to switch
    return "switch_required"


async def awaiting_move_action(room_id, fmt, move, poke, event):
    p1_id = int(room_userids[room_id]["p1"])
    p2_id = int(room_userids[room_id]["p2"])

    # Ensure both players have entries in selected_move
    for uid in [p1_id, p2_id]:
        if uid not in selected_move:
            selected_move[uid] = {}

    print(f"DEBUG: awaiting_move_action triggered for room {room_id}, fmt={fmt}")

    # Wait until both players have selected a move for the current turn
    while True:
        p1_turn = selected_move.get(p1_id, {}).get("turn")
        p2_turn = selected_move.get(p2_id, {}).get("turn")
        p1_ready = (p1_turn == battle_state[p1_id].get("turn", 1))
        p2_ready = (p2_turn == battle_state[p2_id].get("turn", 1))

        if p1_ready and p2_ready:
            print(f"DEBUG: Both players have selected moves for turn {battle_state[p1_id].get('turn', 1)}")
            break
        await asyncio.sleep(0.3)  # avoid busy waiting

    # Get moves
    p1_move = selected_move[p1_id].get("move")
    p2_move = selected_move[p2_id].get("move")

    # Determine turn order - switches always go first, then by speed
    p1_is_switch = (p1_move == "SWITCH")
    p2_is_switch = (p2_move == "SWITCH")

    if p1_is_switch and p2_is_switch:
        turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
    elif p1_is_switch:
        turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
    elif p2_is_switch:
        turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]), (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]
    else:
        p1_speed = battle_data[p1_id]["pokemon"][battle_state[p1_id]["active_pokemon"][0]]["stats"]["spe"]
        p2_speed = battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]["stats"]["spe"]
        p1_poke = battle_data[p1_id]["pokemon"][battle_state[p1_id]["active_pokemon"][0]]
        p2_poke = battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]
        if room_id in status_effects:
            if p1_poke in status_effects[room_id][p1_id]["paralysis"]:
                p1_speed = p1_speed / 2
            if p2_poke in status_effects[room_id][p2_id]["paralysis"]:
                p2_speed = p2_speed / 2

        if p1_speed >= p2_speed:
            turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
        else:
            turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]), (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]

    # Resolve each action in order
    for uid, mv, pokemon in turn_order:
        print(f"DEBUG: Executing action {mv} for user {uid}")

        # Check if attacker's Pokemon has fainted before executing move
        if await check_fainted_pokemon(uid):
            print(f"DEBUG: {uid}'s Pokemon has fainted, cannot execute action")
            continue

        # If this is a switch, perform switch UI (the actual switch was already recorded)
        if mv == "SWITCH":
            # The selected_move recorded the new pokemon id, update active pokemon now
            new_poke_id = selected_move[uid].get("pokemon")
            if new_poke_id:
                battle_state[uid]["active_pokemon"][0] = new_poke_id
                # display switch text
                await switch_pokemon(uid, new_poke_id, event, is_forced=False)
            continue

        # Regular move: resolve it
        await move_handler(uid, mv, pokemon, fmt, event)

        # Check if defender fainted after the move
        defender_id = p2_id if uid == p1_id else p1_id
        if await check_fainted_pokemon(defender_id):
            faint_result = await handle_fainted_pokemon(defender_id, event)

            if faint_result == "lost":
                winner_id = uid
                loser_id = defender_id

                winner_msg = room[winner_id]["start_msg"]
                loser_msg = room[loser_id]["start_msg"]

                try:
                    await winner_msg.edit("🎉 You won the battle! 🎉")
                    await loser_msg.edit("You lost the battle!")
                except Exception:
                    pass

                # Clean up battle state
                for player_id in [p1_id, p2_id]:
                    battle_state.pop(player_id, None)
                    room.pop(player_id, None)

                print(f"DEBUG: Battle ended - Winner: {winner_id}")
                return

    # Increment turn counter
    battle_state[p1_id]["turn"] = battle_state[p1_id].get("turn", 1) + 1
    battle_state[p2_id]["turn"] = battle_state[p2_id].get("turn", 1) + 1

    # After turn resolution, check for fainted pokemon and prompt forced switches if needed
    for uid in [p1_id, p2_id]:
        if await check_fainted_pokemon(uid):
            faint_result = await handle_fainted_pokemon(uid, event)
            if faint_result == "switch_required":
                user_msg = room[uid]["start_msg"]
                await show_forced_switch_menu(uid, user_msg)

    print(f"DEBUG: Turn resolved for room {room_id}")


async def standing_by_fn(event, user_id):
    # Initial standing by message
    try:
        await event.edit("__Standingby...__")
    except MessageNotModifiedError:
        pass
    except Exception:
        pass

    print(f"DEBUG: Standing by for user {user_id}")

    while True:
        # Check opponent assignment
        room_data = room.get(user_id)
        if not room_data or "opponent" not in room_data:
            print(f"DEBUG: Room data not ready for user {user_id}")
            await asyncio.sleep(1)
            continue

        opp_id = room_data["opponent"]
        opp_state = battle_state.get(opp_id)

        # Check opponent existence in battle_state
        if not opp_state:
            print(f"DEBUG: Opponent {opp_id} not in battle_state")
            await asyncio.sleep(1)
            continue

        # Check if opponent finalized team
        if opp_state.get("team_finalize"):
            print(f"DEBUG: Both players ready for user {user_id}")

            # Determine leader: smaller user_id starts the battle UI
            if user_id < opp_id:
                print(f"DEBUG: Leader {user_id} starting battle UI")
                try:
                    await event.edit(f"__{user_id}(You) vs {opp_id}(Opposing Trainer)__")
                except MessageNotModifiedError:
                    pass
                except Exception:
                    pass

                await asyncio.sleep(1)

                user_state = battle_state[user_id]
                mode = user_state["mode"]
                fmt = user_state["fmt"]

                # Set active Pokémon based on format
                if fmt == "singles":
                    user_state["active_pokemon"] = [user_state["allowed_pokemon"][0]]
                    opp_state["active_pokemon"] = [opp_state["allowed_pokemon"][0]]
                elif fmt == "doubles":
                    user_state["active_pokemon"] = user_state["allowed_pokemon"][:2]
                    opp_state["active_pokemon"] = opp_state["allowed_pokemon"][:2]

                print(f"DEBUG: Active Pokémon set, calling first_battle_ui")
                await first_battle_ui(mode, fmt, user_id, None)
            else:
                print(f"DEBUG: Non-leader {user_id}, waiting for battle UI update")

            break  # Stop loop for both players

        # Wait before rechecking
        await asyncio.sleep(1)
