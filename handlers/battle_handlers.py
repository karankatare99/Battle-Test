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
        battle_text=battle_state[user_id]["player_text"]
        # Handle move execution here
        fmt = battle_state[user_id]["fmt"]
        selected_move[user_id]={}
        selected_move[user_id]["move"]=move
        new_turn=battle_state[user_id]["turn"]+1
        selected_move[user_id]["turn"]=new_turn
        room_id=room[user_id]["roomid"]
        await event.edit(f"◌ communicating...\n\n{battle_text}")
        await asyncio.create_task(awaiting_move_action(room_id, fmt, move, poke, event))
        #await move_handler(user_id, fmt, move, poke, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):pokemon_switch$"))
    async def handle_pokemon_switch(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())
        
        # Handle Pokemon switching here
        await event.answer("Pokemon switching not implemented yet")

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
        
        # Handle timeout for each user
        for uid in lobby[:]:
            if currenttime - starttime > timeout:
                lobby.remove(uid)
                if uid in searchmsg:
                    await searchmsg[uid].edit("__Matchmaking timeout!__")
                    del searchmsg[uid]
        
        # If enough players, match two randomly
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
            
            room_userids[roomid] = {}
            room_userids[roomid]["p1"] = p1
            room_userids[roomid]["p2"] = p2
            
            await searchmsg[p1].edit("__An opposing trainer has been found!__")
            await searchmsg[p2].edit("__An opposing trainer has been found!__")
            
            await asyncio.sleep(1)
            
            p1_msg = await searchmsg[p1].edit(f"A battle against {p2} is about to start")
            p2_msg = await searchmsg[p2].edit(f"A battle against {p1} is about to start")
            
            room[p1]["start_msg"] = p1_msg
            room[p2]["start_msg"] = p2_msg
            
            await asyncio.sleep(1)
            
            del searchmsg[p1]
            del searchmsg[p2]
            
            await team_preview(p1, p2)
        
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
    for i in range(0, len(moves), 2):
        move_buttons = [Button.inline(m, f"{user_id}:{target_poke}:move:{m}") for m in moves[i:i+2]]
        buttons.append(move_buttons)
    
    buttons.append([
        Button.inline("Pokémon", f"{user_id}:pokemon_switch"),
        Button.inline("Run", f"{user_id}:run")
    ])
    
    return buttons


async def first_battle_ui(mode, fmt, user_id, event):
    print(f"DEBUG: Starting battle UI for user {user_id}")
    
    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        
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
        
        battle_state[p1_id]["player_text"] = p1_text
        battle_state[p1_id]["turn"] = 1
        
        p2_text = (
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke_hpbar} {p1hppercent:.0f}% \n"
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke_hpbar} {battle_data[p2_id]['pokemon'][p2_poke]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke]['final_hp']}"
        )
        
        battle_state[p2_id]["player_text"] = p2_text
        battle_state[p2_id]["turn"] = 1
        
        try:
            await p1_textmsg.edit(text=p1_text, buttons=p1_poke_buttons)
            await p2_textmsg.edit(text=p2_text, buttons=p2_poke_buttons)
            print(f"DEBUG: Battle UI updated successfully")
        except Exception as e:
            print(f"DEBUG: Error updating battle UI: {e}")
    
    elif fmt == "doubles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        
        p1_textmsg = room[p1_id]["start_msg"]
        p2_textmsg = room[p2_id]["start_msg"]
        
        p1_poke1 = battle_state[p1_id]["active_pokemon"][0]
        p1_poke1_moves = battle_data[p1_id]["pokemon"][p1_poke1]["moves"]
        
        p1_poke2 = battle_state[p1_id]["active_pokemon"][1]
        p1_poke2_moves = battle_data[p1_id]["pokemon"][p1_poke2]["moves"]
        
        p2_poke1 = battle_state[p2_id]["active_pokemon"][0]
        p2_poke1_moves = battle_data[p2_id]["pokemon"][p2_poke1]["moves"]
        
        p2_poke2 = battle_state[p2_id]["active_pokemon"][1]
        p2_poke2_moves = battle_data[p2_id]["pokemon"][p2_poke2]["moves"]
        
        p1_poke1_hpbar = await hp_bar(
            battle_data[p1_id]["pokemon"][p1_poke1]["current_hp"], 
            battle_data[p1_id]["pokemon"][p1_poke1]['final_hp']
        )
        p1_poke2_hpbar = await hp_bar(
            battle_data[p1_id]["pokemon"][p1_poke2]["current_hp"], 
            battle_data[p1_id]["pokemon"][p1_poke2]['final_hp']
        )
        p2_poke1_hpbar = await hp_bar(
            battle_data[p2_id]["pokemon"][p2_poke1]["current_hp"], 
            battle_data[p2_id]["pokemon"][p2_poke1]['final_hp']
        )
        p2_poke2_hpbar = await hp_bar(
            battle_data[p2_id]["pokemon"][p2_poke2]["current_hp"], 
            battle_data[p2_id]["pokemon"][p2_poke2]['final_hp']
        )
        
        p1hppercent1 = battle_data[p1_id]["pokemon"][p1_poke1]["current_hp"] / battle_data[p1_id]["pokemon"][p1_poke1]['final_hp'] * 100
        p1hppercent2 = battle_data[p1_id]["pokemon"][p1_poke2]["current_hp"] / battle_data[p1_id]["pokemon"][p1_poke2]['final_hp'] * 100
        p2hppercent1 = battle_data[p2_id]["pokemon"][p2_poke1]["current_hp"] / battle_data[p2_id]["pokemon"][p2_poke1]['final_hp'] * 100
        p2hppercent2 = battle_data[p2_id]["pokemon"][p2_poke2]["current_hp"] / battle_data[p2_id]["pokemon"][p2_poke2]['final_hp'] * 100
        
        p1_text = (
            f"__**「{p2_poke1.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke1_hpbar} {p2hppercent1:.0f}% \n"
            f"__**「{p2_poke2.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke2_hpbar} {p2hppercent2:.0f}% \n"
            f"__**「{p1_poke1.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke1_hpbar} {battle_data[p1_id]['pokemon'][p1_poke1]['current_hp']}/{battle_data[p1_id]['pokemon'][p1_poke1]['stats']['hp']}\n"
            f"__**「{p1_poke2.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke2_hpbar} {battle_data[p1_id]['pokemon'][p1_poke2]['current_hp']}/{battle_data[p1_id]['pokemon'][p1_poke2]['stats']['hp']}"
        )
        
        p2_text = (
            f"__**「{p1_poke1.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke1_hpbar} {p1hppercent1:.0f}% \n"
            f"__**「{p1_poke2.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke2_hpbar} {p1hppercent2:.0f}% \n"
            f"__**「{p2_poke1.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke1_hpbar} {battle_data[p2_id]['pokemon'][p2_poke1]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke1]['stats']['hp']}\n"
            f"__**「{p2_poke2.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke2_hpbar} {battle_data[p2_id]['pokemon'][p2_poke2]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke2]['stats']['hp']}"
        )
        
        p1_poke1_buttons = await button_generator(p1_poke1_moves, p1_id, "target")
        p2_poke1_buttons = await button_generator(p2_poke1_moves, p2_id, "target")
        
        await p1_textmsg.edit(text=p1_text, buttons=p1_poke1_buttons)
        await p2_textmsg.edit(text=p2_text, buttons=p2_poke1_buttons)


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
        power = move_info.get("power", 40)
        acc = move_info.get("Accuracy", 100)
        
        return type_name, category, power, acc
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return "normal", "physical", 40, 100


async def type_modifier(move_type, opp_type1, opp_type2=None):
    try:
        type1_mod = type1_modifier.get(move_type, {}).get(opp_type1, 1)
        type2_mod = type1_modifier.get(move_type, {}).get(opp_type2, 1) if opp_type2 else 1
        type_effect_modifier = type1_mod * type2_mod
        return type_effect_modifier
    except:
        return 1


async def accuracy_checker(accuracy):
    if accuracy == "-" or accuracy is None:
        return True
    else:
        chance = random.randint(1, 100)
        return accuracy >= chance


async def damage_calc_fn(level, power, attack, defense, modifier=1):
    if power == 0 or attack == 0 or defense == 0:
        return 0
    damage = (((((2 * level) / 5) + 2) * power * (attack / defense)) / 50 + 2) * modifier
    return max(1, int(damage))


async def move_handler(user_id, fmt, move, poke, event):
    print(f"DEBUG: Move handler called - User: {user_id}, Move: {move}, Pokemon: {poke}")
    
    if fmt == "singles":
        try:
            roomid = room[user_id]["roomid"]
            p1_id = int(room_userids[roomid]["p1"])
            p2_id = int(room_userids[roomid]["p2"])
            
            opponent_id = p2_id if user_id == p1_id else p1_id
            
            # Get move data
            move_type, category, power, accuracy = await move_data_extract(move)
            
            # Check accuracy
            if not await accuracy_checker(accuracy):
                await event.answer(f"{move} missed!", alert=True)
                return False
            
            # Calculate damage
            attacker_pokemon = battle_data[user_id]["pokemon"][poke]
            opponent_active = battle_state[opponent_id]["active_pokemon"][0]
            defender_pokemon = battle_data[opponent_id]["pokemon"][opponent_active]
            
            if category.lower() == "physical":
                attack_stat = attacker_pokemon["final_atk"]
                defense_stat = defender_pokemon["final_def"]
            else:
                attack_stat = attacker_pokemon["final_spa"]
                defense_stat = defender_pokemon["final_spd"]
            
            # Get type effectiveness
            defender_type1 = defender_pokemon.get("type1", "normal")
            defender_type2 = defender_pokemon.get("type2")
            type_eff = await type_modifier(move_type, defender_type1, defender_type2)
            
            # Calculate damage
            damage = await damage_calc_fn(100, power, attack_stat, defense_stat, type_eff)
            
            # Apply damage
            old_hp = defender_pokemon["current_hp"]
            defender_pokemon["current_hp"] = max(0, defender_pokemon["current_hp"] - damage)
            
            print(f"DEBUG: {move} dealt {damage} damage to {opponent_active}")
            
            # Update battle UI for both players
            await first_battle_ui(battle_state[user_id]["mode"], fmt, user_id, None)
            
            # Check if Pokemon fainted
            if defender_pokemon["current_hp"] <= 0:
                await event.answer(f"{opponent_active.split('_')[0]} fainted!")
                # Handle Pokemon fainting logic here
            
            return True
            
        except Exception as e:
            print(f"DEBUG: Error in move handler: {e}")
            await event.answer(f"Error executing move: {str(e)}")
            return False
    
    elif fmt == "doubles":
        await event.answer("Doubles battle moves not implemented yet")
        return True

async def awaiting_move_action(room_id, fmt, move, poke, event):
    while True:
        p1=room_userids[roomid]["p1"] 
        p2=room_userids[roomid]["p2"] 
        if selected_move[p1]["turn"]==battle_state[p1]["turn"] and selected_move[p2]["turn"]==battle_state[p2]["turn"]:
            p1_speed = battle_data[p1]["pokemon"][battle_state[p1]["active_pokemon"]]["stats"]["spe"]
            p2_speed = battle_data[p2]["pokemon"][battle_state[p2]["active_pokemon"]]["stats"]["spe"]
            if p1_speed>p2_speed:
                await move_handler(p1, fmt, move, poke, event)
                if battle_data[p2]["pokemon"][battle_state[p2]["active_pokemon"]]["stats"]["hp"] == 0:
                    return
                await move_handler(p2, fmt, move, poke, event)
            elif p2_speed>p1_speed:
                await move_handler(p2, fmt, move, poke, event)
                if battle_data[p1]["pokemon"][battle_state[p1]["active_pokemon"]]["stats"]["hp"] == 0:
                    return
                await move_handler(p1, fmt, move, poke, event)
                
            return
        await asyncio.sleep(1)
async def standing_by_fn(event, user_id):
    await event.edit("__Standingby...__")
    print(f"DEBUG: Standing by for user {user_id}")
    
    while True:
        # Check if opponent data exists
        if user_id not in room or "opponent" not in room[user_id]:
            print(f"DEBUG: Room data not ready for user {user_id}")
            await asyncio.sleep(1)
            continue
            
        opp_id = room[user_id]["opponent"]
        
        # Check if opponent exists in battle_state
        if opp_id not in battle_state:
            print(f"DEBUG: Opponent {opp_id} not in battle_state")
            await asyncio.sleep(1)
            continue
            
        # Check if opponent has finalized team selection
        if battle_state[opp_id].get("team_finalize"):
            print(f"DEBUG: Both players ready, starting battle")
            await event.edit(f"__{user_id}(You) vs {opp_id}(Opposing Trainer)__")
            await asyncio.sleep(1)
            
            mode = battle_state[int(user_id)]["mode"]
            fmt = battle_state[int(user_id)]["fmt"]
            
            # Set active Pokemon
            if fmt == "singles":
                battle_state[user_id]["active_pokemon"] = [battle_state[user_id]["allowed_pokemon"][0]]
                battle_state[opp_id]["active_pokemon"] = [battle_state[opp_id]["allowed_pokemon"][0]]
            elif fmt == "doubles":
                battle_state[user_id]["active_pokemon"] = battle_state[user_id]["allowed_pokemon"][:2]
                battle_state[opp_id]["active_pokemon"] = battle_state[opp_id]["allowed_pokemon"][:2]
            
            print(f"DEBUG: Active Pokemon set, calling first_battle_ui")
            await first_battle_ui(mode, fmt, user_id, event)
            break
        
        await asyncio.sleep(1)
