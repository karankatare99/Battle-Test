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
selected_move={}
roomids = []
rs_lobby = []
rd_lobby = []
cs_lobby = []
cd_lobby = []
searchmsg = {}
selectteam = {}
room_userids = {}
movetext = {}
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
        print("here you go yayyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy", battle_data)
        
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
    
    # Get battle text
        battle_text = battle_state[user_id].get("player_text", "")
        fmt = battle_state[user_id]["fmt"]
    
    # Record selected move and increment turn
        if user_id not in selected_move:
            selected_move[user_id] = {}
        selected_move[user_id] = {
    "move": move,
    "turn": battle_state[user_id]["turn"]
}
    
    # Edit the message to indicate the player is communicating
        room_id = room[user_id]["roomid"]
        text_data = room[user_id]["start_msg"]
        try:
            await text_data.edit(f"◌ communicating...\n\n{battle_text}")
        except MessageNotModifiedError:
            pass

    # Fire-and-forget: process move asynchronously
        asyncio.create_task(awaiting_move_action(room_id, fmt, move, poke, event))
    
        print(f"DEBUG: Move callback handled for user {user_id} (task scheduled)")

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
        await battle_ui(mode, fmt, user_id, event)

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
                except:
                    pass
            del room[user_id]


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
            lobby.remove(p1)
            lobby.remove(p2)
            
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
                lobby.remove(uid)
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
    """Calculate type effectiveness multiplier."""
    move_type = move_type.lower()
    defender_type1 = defender_type1.lower()
    
    modifier = type1_modifier.get(move_type, {}).get(defender_type1, 1)
    
    if defender_type2:
        defender_type2 = defender_type2.lower()
        modifier *= type1_modifier.get(move_type, {}).get(defender_type2, 1)
    
    # Return text based on effectiveness
    if modifier == 0:
        return "It does not effect"
    elif modifier == 0.25:
        return "It's extremely ineffective"
    elif modifier == 0.5:
        return "It's not very effective"
    elif modifier == 1:
        return "Effective"
    elif modifier == 2:
        return "It's super effective"
    elif modifier == 4:
        return "It's extremely effective"
    else:
        return "Effective"


async def move_data_extract(move):
    try:
        with open("moves.json", "r") as f:
            move_data = json.load(f)
        
        move = move.replace(" ", "-").lower()
        
        if move not in move_data:
            return "normal", "physical", 40, 100
        
        move_info = move_data[move]
        type_name = move_info.get("Type", "normal")
        category = move_info.get("Category", "physical")
        power = move_info.get("power", 50)
        acc = move_info.get("Accuracy", 100)
        
        return type_name, category, power, acc
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return "normal", "physical", 50, 100




async def accuracy_checker(accuracy):
    """Return True if the move hits.
    Accepts:
      - None → always hits
      - fraction (0.0–1.0)
      - percent (0–100)
    """
    if accuracy is None:
        return True
    try:
        acc = float(accuracy)
    except Exception:
        return True

    # Convert fraction → percent
    acc_pct = acc * 100.0 if acc <= 1.0 else acc
    roll = random.uniform(0, 100)
    return roll <= acc_pct
import re

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

    # String case
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

    # Fallback: try to parse numeric multiplier like "2x"
    m = re.search(r"(\d+(\.\d+)?)\s*[x×]", s)
    if m:
        mult = float(m.group(1))
        return mult, mapping.get(mult, "Effective")

    return 1.0, mapping[1.0]
    
import random

async def damage_calc_fn(level, power, attack, defense, type_multiplier):
    """Calculate Pokémon-style damage.
    `type_multiplier` must be numeric.
    Returns: (damage:int, is_critical:bool)
    """
    try:
        type_mult = float(type_multiplier)
    except Exception:
        type_mult = 1.0

    is_critical = (random.randint(1, 24) == 1)
    critical_mult = 1.5 if is_critical else 1.0

    # Simplified Pokémon damage formula
    base = ((((2 * level) / 5) + 2) * power * (attack / (defense if defense > 0 else 1))) / 50 + 2
    damage = base * type_mult * critical_mult * random.uniform(0.85, 1.0)

    return max(1, int(damage)), is_critical  # ensure at least 1 damage

async def first_battle_ui(mode, fmt, user_id, event):
    """Initialize the first battle UI for both players."""
    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        
        # Initialize turn counter
        battle_state[p1_id]["turn"] = 1
        battle_state[p2_id]["turn"] = 1
        
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

async def move_handler(user_id, move, poke, fmt, event):
    print(f"DEBUG: Move handler called - User: {user_id}, Move: {move}, Pokemon: {poke}")

    if fmt == "singles":
        try:
            roomid = room[user_id]["roomid"]
            p1_id = int(room_userids[roomid]["p1"])
            p2_id = int(room_userids[roomid]["p2"])
            opponent_id = p2_id if user_id == p1_id else p1_id

            # Extract move data
            move_type, category, power, accuracy = await move_data_extract(move)

            # Initialize movetext containers
            if p1_id not in movetext:
                movetext[p1_id] = {}
            if p2_id not in movetext:
                movetext[p2_id] = {}

            # Pokémon data
            attacker_pokemon = battle_data[user_id]["pokemon"][poke]
            opponent_active = battle_state[opponent_id]["active_pokemon"][0]
            defender_pokemon = battle_data[opponent_id]["pokemon"][opponent_active]

            self_pokemon = poke.split("_")[0]
            opp_pokemon = opponent_active.split("_")[0]

            # ✅ Accuracy check
            hit = await accuracy_checker(accuracy)
            if not hit:
                user_movetext1 = f"{self_pokemon} used {move}!"
                user_movetext2 = f"Opposing {opp_pokemon} avoided the attack!"
                opp_movetext1 = f"Opposing {self_pokemon} used {move}!"

                movetext[user_id]["text_sequence"] = [user_movetext1, user_movetext2]
                movetext[user_id]["hp_update_at"] = 999  # No HP change
                movetext[opponent_id]["text_sequence"] = [opp_movetext1, user_movetext2]
                movetext[opponent_id]["hp_update_at"] = 999
                return True

            # ✅ Attack/Defense stats
            if category.lower() == "physical":
                attack_stat = attacker_pokemon["final_atk"]
                defense_stat = defender_pokemon["final_def"]
            else:
                attack_stat = attacker_pokemon["final_spa"]
                defense_stat = defender_pokemon["final_spd"]

            # ✅ Type effectiveness
            type_eff_raw = await type_modifier(
                move_type, defender_pokemon.get("type1", "normal"), defender_pokemon.get("type2")
            )
            type_mult, effect_text = interpret_type_effect(type_eff_raw)

            # ✅ Damage calculation
            damage, is_critical = await damage_calc_fn(100, power, attack_stat, defense_stat, type_mult)
            old_hp = defender_pokemon["current_hp"]
            defender_pokemon["current_hp"] = max(0, defender_pokemon["current_hp"] - damage)

            # ✅ Build move text
            used_text = f"{self_pokemon} used {move}!"
            crit_text = "A critical hit!" if is_critical else None

            if is_critical and effect_text != "Effective":
                seq = [used_text, crit_text, effect_text]
            elif is_critical:
                seq = [used_text, crit_text]
            elif effect_text != "Effective":
                seq = [used_text, effect_text]
            else:
                seq = [used_text, ""]

            hp_update_at = 1  # Show HP change after 1 sec

            opp_seq = [f"Opposing {self_pokemon} used {move}!"] + seq[1:]

            movetext[user_id]["text_sequence"] = seq
            movetext[user_id]["hp_update_at"] = hp_update_at
            movetext[opponent_id]["text_sequence"] = opp_seq
            movetext[opponent_id]["hp_update_at"] = hp_update_at

            print(f"DEBUG: Move resolved - Damage: {damage}, Defender HP: {old_hp} → {defender_pokemon['current_hp']}")
            return True

        except Exception as e:
            print(f"ERROR in move_handler: {e}")
            import traceback
            traceback.print_exc()
            return False


async def battle_ui(mode, fmt, user_id, event):
    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        
        p1_textmsg = room[p1_id]["start_msg"]
        p2_textmsg = room[p2_id]["start_msg"]
        
        p1_poke = battle_state[p1_id]["active_pokemon"][0]
        p2_poke = battle_state[p2_id]["active_pokemon"][0]
        
        # Check if Pokemon are fainted before generating buttons
        p1_fainted = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"] <= 0
        p2_fainted = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"] <= 0
        
        if not p1_fainted:
            p1_poke_moves = battle_data[p1_id]["pokemon"][p1_poke]["moves"]
            p1_poke_buttons = await button_generator(p1_poke_moves, p1_id, p1_poke)
        else:
            p1_poke_buttons = None
        
        if not p2_fainted:
            p2_poke_moves = battle_data[p2_id]["pokemon"][p2_poke]["moves"]
            p2_poke_buttons = await button_generator(p2_poke_moves, p2_id, p2_poke)
        else:
            p2_poke_buttons = None
        
        print(f"DEBUG: Battle data ready for {user_id}")
        
        # Get pre-damage HP if stored, otherwise use current HP
        p1_current_hp = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]
        p2_current_hp = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"]
        
        p1_pre_hp = battle_state[p1_id].get("pre_damage_hp", p1_current_hp)
        p2_pre_hp = battle_state[p2_id].get("pre_damage_hp", p2_current_hp)
        
        # Generate HP bars for OLD and NEW state
        p1_poke_hpbar_old = await hp_bar(p1_pre_hp, battle_data[p1_id]["pokemon"][p1_poke]['final_hp'])
        p2_poke_hpbar_old = await hp_bar(p2_pre_hp, battle_data[p2_id]["pokemon"][p2_poke]['final_hp'])
        p1_poke_hpbar_new = await hp_bar(p1_current_hp, battle_data[p1_id]["pokemon"][p1_poke]['final_hp'])
        p2_poke_hpbar_new = await hp_bar(p2_current_hp, battle_data[p2_id]["pokemon"][p2_poke]['final_hp'])
        
        p1hppercent_old = p1_pre_hp / battle_data[p1_id]["pokemon"][p1_poke]['final_hp'] * 100
        p2hppercent_old = p2_pre_hp / battle_data[p2_id]["pokemon"][p2_poke]['final_hp'] * 100
        p1hppercent_new = p1_current_hp / battle_data[p1_id]["pokemon"][p1_poke]['final_hp'] * 100
        p2hppercent_new = p2_current_hp / battle_data[p2_id]["pokemon"][p2_poke]['final_hp'] * 100
        
        # OLD text with pre-damage HP
        p1_text_old = (
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__"
            f"{p2_poke_hpbar_old} {p2hppercent_old:.0f}% "
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__"
            f"{p1_poke_hpbar_old} {p1_pre_hp}/{battle_data[p1_id]['pokemon'][p1_poke]['final_hp']}"
        )
        p2_text_old = (
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__"
            f"{p1_poke_hpbar_old} {p1hppercent_old:.0f}% "
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__"
            f"{p2_poke_hpbar_old} {p2_pre_hp}/{battle_data[p2_id]['pokemon'][p2_poke]['final_hp']}"
        )
        
        # FINAL text with updated HP
        p1_text_final = (
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__"
            f"{p2_poke_hpbar_new} {p2hppercent_new:.0f}% "
async def battle_ui(mode, fmt, user_id, event):
    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])

        p1_textmsg = room[p1_id]["start_msg"]
        p2_textmsg = room[p2_id]["start_msg"]

        p1_poke = battle_state[p1_id]["active_pokemon"][0]
        p2_poke = battle_state[p2_id]["active_pokemon"][0]

        p1_speed = battle_data[p1_id]["pokemon"][p1_poke]["stats"]["spe"]
        p2_speed = battle_data[p2_id]["pokemon"][p2_poke]["stats"]["spe"]

        # Determine move order
        if p1_speed >= p2_speed:
            fast_id, slow_id = p1_id, p2_id
        else:
            fast_id, slow_id = p2_id, p1_id

        # Helper for reuse
        async def get_ui_data(pid):
            poke = battle_state[pid]["active_pokemon"][0]
            fainted = battle_data[pid]["pokemon"][poke]["current_hp"] <= 0
            poke_moves = battle_data[pid]["pokemon"][poke]["moves"] if not fainted else []
            buttons = await button_generator(poke_moves, pid, poke) if not fainted else None
            current_hp = battle_data[pid]["pokemon"][poke]["current_hp"]
            pre_hp = battle_state[pid].get("pre_damage_hp", current_hp)
            final_hp = battle_data[pid]["pokemon"][poke]["final_hp"]
            hpbar_old = await hp_bar(pre_hp, final_hp)
            hpbar_new = await hp_bar(current_hp, final_hp)
            hp_old_percent = pre_hp / final_hp * 100
            hp_new_percent = current_hp / final_hp * 100
            return {
                "poke": poke,
                "buttons": buttons,
                "hpbar_old": hpbar_old,
                "hpbar_new": hpbar_new,
                "hp_old": pre_hp,
                "hp_new": current_hp,
                "hp_old_percent": hp_old_percent,
                "hp_new_percent": hp_new_percent
            }

        p1 = await get_ui_data(p1_id)
        p2 = await get_ui_data(p2_id)

        # Pre-damage text
        def gen_text(p1_data, p2_data, use_new=False, view_self=True):
            opp, self_ = (p2_data, p1_data) if view_self else (p1_data, p2_data)
            opp_bar = opp["hpbar_new"] if use_new else opp["hpbar_old"]
            self_bar = self_["hpbar_new"] if use_new else self_["hpbar_old"]
            opp_hp = opp["hp_new"] if use_new else opp["hp_old"]
            self_hp = self_["hp_new"] if use_new else self_["hp_old"]
            opp_per = opp["hp_new_percent"] if use_new else opp["hp_old_percent"]
            self_per = self_["hp_new_percent"] if use_new else self_["hp_old_percent"]

            return (
                f"__**「{opp['poke'].split('_')[0].capitalize()}(Lv.100)」**__"
                f"{opp_bar} {opp_per:.0f}% "
                f"__**「{self_['poke'].split('_')[0].capitalize()}(Lv.100)」**__"
                f"{self_bar} {self_hp}/{battle_data[view_self and p1_id or p2_id]['pokemon'][self_['poke']]['final_hp']}"
            )

        p1_textmsg_data = room[p1_id]["start_msg"]
        p2_textmsg_data = room[p2_id]["start_msg"]

        async def play_sequence(pid, msg_obj, opponent_msg_obj, use_new_hp_at):
            data_self = p1 if pid == p1_id else p2
            data_opp = p2 if pid == p1_id else p1
            moves = movetext[pid]["text_sequence"]

            for idx, i in enumerate(moves):
                show_final_hp = (idx >= use_new_hp_at)
                text_self = f"{i}\n\n{gen_text(data_self, data_opp, use_new=show_final_hp, view_self=True)}"
                text_opp = f"{i}\n\n{gen_text(data_self, data_opp, use_new=show_final_hp, view_self=False)}"

                try:
                    if idx == len(moves) - 1:
                        await msg_obj.edit(text=text_self, buttons=data_self["buttons"])
                        await opponent_msg_obj.edit(text=text_opp, buttons=data_opp["buttons"])
                    else:
                        await msg_obj.edit(text=text_self)
                        await opponent_msg_obj.edit(text=text_opp)
                    await asyncio.sleep(1)
                except MessageNotModifiedError:
                    continue
                except Exception as e:
                    print(f"DEBUG: Error in sequence for {pid}: {e}")

        # Play fast Pokémon’s move first
        await play_sequence(fast_id, 
                            room[fast_id]["start_msg"], 
                            room[slow_id]["start_msg"], 
                            movetext.get(fast_id, {}).get("hp_update_at", len(movetext[fast_id]["text_sequence"]) - 1))

        # Then slow Pokémon’s move
        await play_sequence(slow_id, 
                            room[slow_id]["start_msg"], 
                            room[fast_id]["start_msg"], 
                            movetext.get(slow_id, {}).get("hp_update_at", len(movetext[slow_id]["text_sequence"]) - 1))

        # Cleanup
        battle_state[p1_id].pop("pre_damage_hp", None)
        battle_state[p2_id].pop("pre_damage_hp", None)
        
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
        if p1_id not in movetext:
            movetext[p1_id] = {}
        if p2_id not in movetext:
            movetext[p2_id] = {}
        
        movetext[user_id]["text_sequence"] = [user_switch_text]
        movetext[opponent_id]["text_sequence"] = [opp_switch_text]
        
        # If this is a voluntary switch (not forced by fainting), record it as the player's turn action
        if not is_forced:
            if user_id not in selected_move:
                selected_move[user_id] = {}
            selected_move[user_id] = {
                "move": "SWITCH",
                "pokemon": new_poke_id,
                "turn": battle_state[user_id]["turn"]
            }
            
            # Show "communicating" message
            room_id = room[user_id]["roomid"]
            text_data = room[user_id]["start_msg"]
            battle_text = battle_state[user_id].get("player_text", "")
            try:
                await text_data.edit(f"◌ communicating...\n\n{battle_text}")
            except MessageNotModifiedError:
                pass
            
            # Trigger move action processing
            asyncio.create_task(awaiting_move_action(room_id, fmt, "SWITCH", new_poke_id, event))
        else:
            # Forced switch (after fainting) - just update UI immediately
            await battle_ui(battle_state[user_id]["mode"], fmt, user_id, event)


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
    if p1_id not in movetext:
        movetext[p1_id] = {}
    if p2_id not in movetext:
        movetext[p2_id] = {}
    
    # Add faint message
    user_faint_text = f"{poke_name} fainted!"
    opp_faint_text = f"Opposing {poke_name} fainted!"
    
    if user_id in movetext and "text_sequence" in movetext[user_id]:
        movetext[user_id]["text_sequence"].append(user_faint_text)
    else:
        movetext[user_id]["text_sequence"] = [user_faint_text]
    
    if opponent_id in movetext and "text_sequence" in movetext[opponent_id]:
        movetext[opponent_id]["text_sequence"].append(opp_faint_text)
    else:
        movetext[opponent_id]["text_sequence"] = [opp_faint_text]
    
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
        p1_ready = (p1_turn == battle_state[p1_id]["turn"])
        p2_ready = (p2_turn == battle_state[p2_id]["turn"])

        if p1_ready and p2_ready:
            print(f"DEBUG: Both players have selected moves for turn {battle_state[p1_id]['turn']}")
            break
        await asyncio.sleep(0.5)  # avoid busy waiting
    print("got out")
    # Get moves
    p1_move = selected_move[p1_id]["move"]
    p2_move = selected_move[p2_id]["move"]

    # Determine turn order - switches always go first, then by speed
    p1_is_switch = (p1_move == "SWITCH")
    p2_is_switch = (p2_move == "SWITCH")
    
    if p1_is_switch and p2_is_switch:
        # Both switching - order by user ID
        turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
    elif p1_is_switch:
        # P1 switching goes first
        turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
    elif p2_is_switch:
        # P2 switching goes first
        turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]), (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]
    else:
        # Both using moves - sort by speed
        p1_speed = battle_data[p1_id]["pokemon"][battle_state[p1_id]["active_pokemon"][0]]["stats"]["spe"]
        p2_speed = battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]["stats"]["spe"]
        
        if p1_speed >= p2_speed:
            turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
        else:
            turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]), (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]

    # Resolve each move
    for uid, mv, pokemon in turn_order:
        print(f"DEBUG: Executing action {mv} for user {uid}")
        
        # Check if attacker's Pokemon has fainted before executing move
        if await check_fainted_pokemon(uid):
            print(f"DEBUG: {uid}'s Pokemon has fainted, cannot execute action")
            continue
        
        # If this is a switch, skip the move handler (switch already happened)
        if mv == "SWITCH":
            print(f"DEBUG: {uid} switched Pokemon, turn is over")
            continue
        
        await move_handler(uid, mv, pokemon, fmt, event)
        
        # Check if defender's Pokemon fainted after the move
        defender_id = p2_id if uid == p1_id else p1_id
        if await check_fainted_pokemon(defender_id):
            faint_result = await handle_fainted_pokemon(defender_id, event)
            
            if faint_result == "lost":
                # Defender has lost the battle
                winner_id = uid
                loser_id = defender_id
                
                # Show victory/defeat messages
                winner_msg = room[winner_id]["start_msg"]
                loser_msg = room[loser_id]["start_msg"]
                
                await winner_msg.edit("🎉 You won the battle! 🎉")
                await loser_msg.edit("You lost the battle!")
                
                # Clean up battle state
                for player_id in [p1_id, p2_id]:
                    if player_id in battle_state:
                        del battle_state[player_id]
                    if player_id in room:
                        del room[player_id]
                
                print(f"DEBUG: Battle ended - Winner: {winner_id}")
                return

    # Increment turn counter
    battle_state[p1_id]["turn"] += 1
    battle_state[p2_id]["turn"] += 1

    # Update battle UI after moves are resolved
    await battle_ui(battle_state[p1_id]["mode"], fmt, p1_id, event)
    
    # Check if any Pokemon need to switch after the UI update
    for uid in [p1_id, p2_id]:
        if await check_fainted_pokemon(uid):
            faint_result = await handle_fainted_pokemon(uid, event)
            if faint_result == "switch_required":
                # Show switch menu to the player
                user_msg = room[uid]["start_msg"]
                await show_forced_switch_menu(uid, user_msg)

    print(f"DEBUG: Turn {battle_state[p1_id]['turn'] - 1} resolved for room {room_id}")

    
from telethon.errors.rpcerrorlist import MessageNotModifiedError
import asyncio

async def standing_by_fn(event, user_id):
    # Initial standing by message
    try:
        await event.edit("__Standingby...__")
    except MessageNotModifiedError:
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
