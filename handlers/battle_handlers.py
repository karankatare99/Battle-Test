from telethon import events, Button
from telethon.errors.rpcerrorlist import MessageNotModifiedError
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
player_move_done={}
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

#all moves
all_moves = ["Cut", "Drill Peck", "Egg Bomb", "Gust", "Horn Attack", "Hydro Pump", "Mega Kick", "Mega Punch", "Pay Day", "Peck", "Pound", "Rock Throw", "Scratch", "Slam", "Sonic Boom", "Strength", "Swift", "Tackle", "Vine Whip", "Water Gun", "Wing Attack","Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz", "Body Slam", "Lick", "Thunder", "Thunder Punch", "Thunder Shock", "Thunderbolt", "Splishy Splash","Sizzly Slide"]
#Only damage dealing moves
only_damage_moves = ["Cut", "Drill Peck", "Egg Bomb", "Gust", "Horn Attack", "Hydro Pump", "Mega Kick", "Mega Punch", "Pay Day", "Peck", "Pound", "Rock Throw", "Scratch", "Slam", "Sonic Boom", "Strength", "Swift", "Tackle", "Vine Whip", "Water Gun", "Wing Attack"]
#Never miss moves
never_miss_moves = ["Swift"]
#Paralyze moves
paralyze_moves = ["Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz", "Body Slam", "Lick", "Thunder", "Thunder Punch", "Thunder Shock", "Thunderbolt", "Splishy Splash"]
paralyze_moves30 = ["Body Slam", "Lick", "Thunder", "Splishy Splash"]
paralyze_moves10 = ["Thunder Punch", "Thunder Shock", "Thunderbolt"]
always_paralyze_moves = ["Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz"]
#flinch moves
flinch_moves = []
flinch_moves10=[]
flinch_moves20=[]
flinch_moves30=[]
always_flinch_moves=[]
#burn moves
burn_moves=["Sizzly Slide"]
burn_moves10=[]
burn_moves20=[]
always_burn_moves=["Sizzly Slide"]

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

def init_movetext(user_id):
    """Initialize movetext structure with all required fields."""
    if user_id not in movetext:
        movetext[user_id] = {
            "text_sequence": [],
            "damage": 0,
            "move_hit": True,
            "hp_update_at": 1  # Which text index to update HP after
        }
    return movetext[user_id]

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
            await event.answer(action_text)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):(ranked|casual):(singles|doubles):(done)$"))
    async def done_callback(event):
        user_id_str, mode, fmt, done = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        mode = mode.decode()
        fmt = fmt.decode()
        
        print(f"DEBUG: Done callback triggered for user {user_id}")
        
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
        
        await show_switch_menu(user_id, event)
    
    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):switch_to:(.+)$"))
    async def handle_switch_to_pokemon(event):
        user_id_str, poke = event.pattern_match.groups()
        user_id = int(user_id_str.decode())
        poke = poke.decode()
        
        active_poke = battle_state[user_id]["active_pokemon"][0]
        is_forced = (battle_data[user_id]["pokemon"][active_poke]["current_hp"] <= 0)
        
        await switch_pokemon(user_id, poke, event, is_forced=is_forced)
    
    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):cancel_switch$"))
    async def handle_cancel_switch(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())
        
        fmt = battle_state[user_id]["fmt"]
        mode = battle_state[user_id]["mode"]
        await battle_ui(mode, fmt, user_id, event)

    @bot.on(events.CallbackQuery(pattern=b"^(\\d+):run$"))
    async def handle_run(event):
        user_id_str = event.pattern_match.group(1)
        user_id = int(user_id_str.decode())
        
        await event.edit("You ran away from the battle!")
        
        if user_id in battle_state:
            del battle_state[user_id]
        if user_id in room:
            opp_id = room[user_id].get("opponent")
            if opp_id and opp_id in battle_state:
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
                
                # Check if this pokemon is selected
                is_selected = (id in selectteam and poke_data in selectteam[id]["pokes"])
                check = "✅" if is_selected else "⬜"
                
                row.append(Button.inline(
                    f"{check} {poke}",
                    data=f"{id}:{mode}:{fmt}:select:{poke_data}".encode()
                ))
        buttons.append(row)
    
    # Bottom row: Done and View Opponent Team buttons
    buttons.append([
        Button.inline("Done", data=f"{id}:{mode}:{fmt}:done".encode()),
        Button.inline("View Opponent Team", data=f"{id}:{mode}:{fmt}:opp_team".encode())
    ])
    
    return buttons


async def button_generator(movelist, user_id, poke):
    """Generate move buttons"""
    buttons = []
    for i in range(0, len(movelist), 2):
        row = []
        for j in range(2):
            if i + j < len(movelist):
                move = movelist[i + j]
                row.append(Button.inline(
                    move,
                    data=f"{user_id}:{poke}:move:{move}".encode()
                ))
        buttons.append(row)
    return buttons


# Import necessary helper functions from other modules
from handlers.helpers import (
    hp_bar,
    accuracy_checker,
    interpret_type_effect,
    type_modifier,
    damage_calc_fn,
    search_for_opp_trainer,
    paralyze_check,
    burn_check,
    end_of_turn_effects
)


async def move_handler(user_id, move, poke, fmt, event):
    """Handle move execution and damage calculation."""
    try:
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        opponent_id = p2_id if user_id == p1_id else p1_id
        
        # Initialize movetext for both players
        init_movetext(user_id)
        init_movetext(opponent_id)
        
        # Get active pokemon
        user_active = battle_state[user_id]["active_pokemon"][0]
        opponent_active = battle_state[opponent_id]["active_pokemon"][0]
        
        attacker_pokemon = battle_data[user_id]["pokemon"][user_active]
        defender_pokemon = battle_data[opponent_id]["pokemon"][opponent_active]
        
        self_pokemon = user_active.split("_")[0]
        opp_pokemon = opponent_active.split("_")[0]
        
        print(f"DEBUG: {self_pokemon} (user {user_id}) attacking {opp_pokemon} (user {opponent_id}) with {move}")
        
        # Get move data from Pokemon's moves
        move_info = next((m for m in attacker_pokemon["moves"] if m["name"] == move), None)
        if not move_info:
            print(f"ERROR: Move {move} not found in {self_pokemon}'s moveset")
            return False
        
        power = move_info.get("power", 0)
        accuracy = move_info.get("accuracy", 100)
        category = move_info.get("category", "physical")
        move_type = move_info.get("type", "normal")
        
        # Status effect checks
        if roomid in status_effects:
            if user_id in status_effects[roomid]:
                # Paralysis check
                if user_active in status_effects[roomid][user_id]["paralysis"]:
                    paralyze_chance = random.randint(1, 4)
                    if paralyze_chance == 1:
                        used_text_self = f"{self_pokemon} is paralyzed! It can't move!"
                        used_text_opp = f"Opposing {self_pokemon} is paralyzed! It can't move!"
                        
                        movetext[user_id]["text_sequence"].extend([used_text_self, ""])
                        movetext[opponent_id]["text_sequence"].extend([used_text_opp, ""])
                        movetext[user_id]["hp_update_at"] = 999
                        movetext[opponent_id]["hp_update_at"] = 999
                        return True
                
                # Flinch check
                if user_active in status_effects[roomid][user_id]["flinch"]:
                    used_text_self = f"{self_pokemon} flinched and couldn't move!"
                    used_text_opp = f"Opposing {self_pokemon} flinched and couldn't move!"
                    
                    movetext[user_id]["text_sequence"].extend([used_text_self, ""])
                    movetext[opponent_id]["text_sequence"].extend([used_text_opp, ""])
                    movetext[user_id]["hp_update_at"] = 999
                    movetext[opponent_id]["hp_update_at"] = 999
                    status_effects[roomid][user_id]["flinch"].remove(user_active)
                    return True
        
        # Accuracy check
        hit = await accuracy_checker(accuracy, move)
        if not hit:
            used_text_self = f"{self_pokemon} used {move}!"
            miss_text = f"Opposing {opp_pokemon} avoided the attack!"
            used_text_opp = f"Opposing {self_pokemon} used {move}!"
            
            movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
            movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])
            movetext[user_id]["hp_update_at"] = 999
            movetext[opponent_id]["hp_update_at"] = 999
            return True
        
        # Attack/Defense stats
        if category.lower() == "physical":
            attack_stat = attacker_pokemon["final_atk"]
            defense_stat = defender_pokemon["final_def"]
        else:
            attack_stat = attacker_pokemon["final_spa"]
            defense_stat = defender_pokemon["final_spd"]
        
        # Type effectiveness
        type_eff_raw = await type_modifier(
            move_type, defender_pokemon.get("type1", "normal"), defender_pokemon.get("type2")
        )
        type_mult, effect_text = interpret_type_effect(type_eff_raw)
        
        # Damage calculation
        damage, is_critical = await damage_calc_fn(100, power, attack_stat, defense_stat, type_mult, move)
        
        # FIXED: Store damage for the OPPONENT (who is receiving the damage)
        # Do NOT modify final_hp here - that's a max HP value!
        movetext[opponent_id]["damage"] = damage
        
        print(f"DEBUG: {self_pokemon} attacks {opp_pokemon} for {damage} damage")
        
        # Build text sequences
        used_text_self = f"{self_pokemon} used {move}!"
        used_text_opp = f"Opposing {self_pokemon} used {move}!"
        crit_text = "A critical hit!" if is_critical else None
        
        # Build attacker's sequence
        seq_self = [used_text_self]
        if crit_text:
            seq_self.append(crit_text)
        if power > 0 and effect_text != "Effective":
            seq_self.append(effect_text)
        
        # Build opponent's sequence
        seq_opp = [used_text_opp]
        if crit_text:
            seq_opp.append(crit_text)
        if power > 0 and effect_text != "Effective":
            seq_opp.append(effect_text)
        
        # Paralyze check
        if move in paralyze_moves:
            paralyze = await paralyze_check(move)
            paralyze_list = status_effects[roomid][opponent_id]["paralysis"]
            
            if opponent_active in paralyze_list:
                paralyze_textuser = f"The Opposing {opp_pokemon} is already paralyzed!"
                paralyze_textopp = f"{opp_pokemon} is already paralyzed!"
                seq_self.append(paralyze_textuser)
                seq_opp.append(paralyze_textopp)
            elif paralyze:
                paralyze_textuser = f"The Opposing {opp_pokemon} is paralyzed!\nIt may be unable to move"
                paralyze_textopp = f"{opp_pokemon} is paralyzed!\nIt may be unable to move"
                paralyze_list.append(opponent_active)
                seq_self.append(paralyze_textuser)
                seq_opp.append(paralyze_textopp)
        
        # Burn check
        if move in burn_moves:
            burn = await burn_check(move)
            burn_list = status_effects[roomid][opponent_id]["burn"]
            
            if opponent_active in burn_list:
                burn_textuser = f"The Opposing {opp_pokemon} is already burned!"
                burn_textopp = f"{opp_pokemon} is already burned!"
                seq_self.append(burn_textuser)
                seq_opp.append(burn_textopp)
            elif burn:
                burn_textuser = f"The Opposing {opp_pokemon} was burned!"
                burn_textopp = f"{opp_pokemon} was burned!"
                burn_list.append(opponent_active)
                seq_self.append(burn_textuser)
                seq_opp.append(burn_textopp)
        
        # Append to movetext (don't replace)
        movetext[user_id]["text_sequence"].extend(seq_self)
        movetext[opponent_id]["text_sequence"].extend(seq_opp)
        
        # Set when to apply HP update (after first text message)
        movetext[user_id]["hp_update_at"] = 1
        movetext[opponent_id]["hp_update_at"] = 1
        
        print(f"DEBUG: Move resolved - {self_pokemon} used {move}, Damage: {damage} will be applied to {opp_pokemon}")
        return True
        
    except Exception as e:
        print(f"ERROR in move_handler: {e}")
        import traceback
        traceback.print_exc()
        return False


async def battle_ui(mode, fmt, user_id, event):
    """
    FIXED: Configure the battle UI with proper HP bar updates and damage application.
    Shows move sequences and updates HP bars at the correct timing.
    """
    if fmt != "singles":
        return
    
    roomid = room[user_id]["roomid"]
    p1_id = int(room_userids[roomid]["p1"])
    p2_id = int(room_userids[roomid]["p2"])
    
    # Initialize movetext if not already done
    init_movetext(p1_id)
    init_movetext(p2_id)
    
    # Messages
    p1_textmsg = room[p1_id]["start_msg"]
    p2_textmsg = room[p2_id]["start_msg"]
    
    # Active Pokémon
    p1_poke = battle_state[p1_id]["active_pokemon"][0]
    p2_poke = battle_state[p2_id]["active_pokemon"][0]
    
    # Helper function to get current HP displays
    async def get_current_hp_display():
        """Return formatted HP display for both sides with current HP values."""
        p1_hp = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]
        p1_max_hp = battle_data[p1_id]["pokemon"][p1_poke]["final_hp"]
        p2_hp = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"]
        p2_max_hp = battle_data[p2_id]["pokemon"][p2_poke]["final_hp"]
        
        p1_hpbar = await hp_bar(p1_hp, p1_max_hp)
        p2_hpbar = await hp_bar(p2_hp, p2_max_hp)
        
        p1_percent = p1_hp / p1_max_hp * 100 if p1_max_hp > 0 else 0
        p2_percent = p2_hp / p2_max_hp * 100 if p2_max_hp > 0 else 0
        
        p1_display = (
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_hpbar} {p2_percent:.0f}% \n"
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_hpbar} {p1_hp}/{p1_max_hp}"
        )
        
        p2_display = (
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_hpbar} {p1_percent:.0f}% \n"
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_hpbar} {p2_hp}/{p2_max_hp}"
        )
        
        return p1_display, p2_display
    
    # Get text sequences
    p1_textsequence = movetext[p1_id]["text_sequence"]
    p2_textsequence = movetext[p2_id]["text_sequence"]
    
    # Get HP update index
    p1_hp_update_at = movetext[p1_id].get("hp_update_at", 1)
    p2_hp_update_at = movetext[p2_id].get("hp_update_at", 1)
    
    # Process text sequence and apply damage at correct timing
    max_len = max(len(p1_textsequence), len(p2_textsequence))
    
    for idx in range(max_len):
        # Get text for this index (or empty if sequence ended)
        p1_text = p1_textsequence[idx] if idx < len(p1_textsequence) else ""
        p2_text = p2_textsequence[idx] if idx < len(p2_textsequence) else ""
        
        # Skip empty entries
        if not p1_text and not p2_text:
            continue
        
        # Get current HP display BEFORE applying damage for this turn
        p1_hp_display, p2_hp_display = await get_current_hp_display()
        
        # Show move text with current HP bars
        p1_full_text = f"{p1_text}\n\n{p1_hp_display}"
        p2_full_text = f"{p2_text}\n\n{p2_hp_display}"
        
        try:
            await p1_textmsg.edit(p1_full_text)
            await p2_textmsg.edit(p2_full_text)
            await asyncio.sleep(1.5)
        except MessageNotModifiedError:
            pass
        except Exception as e:
            print(f"DEBUG: UI edit error: {e}")
        
        # FIXED: Apply damage AFTER showing the move text (at specified index)
        # P1's damage goes to P2, P2's damage goes to P1
        if idx == p1_hp_update_at:
            p1_damage = movetext[p1_id].get("damage", 0)
            if p1_damage > 0:
                # P1 attacked, so P2 takes damage
                old_hp = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"]
                new_hp = max(0, old_hp - p1_damage)
                battle_data[p2_id]["pokemon"][p2_poke]["current_hp"] = new_hp
                print(f"DEBUG: {p2_poke} took {p1_damage} damage — HP: {old_hp} → {new_hp}")
        
        if idx == p2_hp_update_at:
            p2_damage = movetext[p2_id].get("damage", 0)
            if p2_damage > 0:
                # P2 attacked, so P1 takes damage
                old_hp = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]
                new_hp = max(0, old_hp - p2_damage)
                battle_data[p1_id]["pokemon"][p1_poke]["current_hp"] = new_hp
                print(f"DEBUG: {p1_poke} took {p2_damage} damage — HP: {old_hp} → {new_hp}")
    
    # After all text sequences, get final HP display
    p1_final_display, p2_final_display = await get_current_hp_display()
    
    # Update battle_state with final display text
    battle_state[p1_id]["player_text"] = p1_final_display
    battle_state[p2_id]["player_text"] = p2_final_display
    
    # Generate move buttons
    p1_poke_moves = battle_data[p1_id]["pokemon"][p1_poke]["moves"]
    p1_buttons = await button_generator(p1_poke_moves, p1_id, p1_poke)
    
    p2_poke_moves = battle_data[p2_id]["pokemon"][p2_poke]["moves"]
    p2_buttons = await button_generator(p2_poke_moves, p2_id, p2_poke)
    
    # Check if Pokemon fainted
    p1_fainted = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"] <= 0
    p2_fainted = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"] <= 0
    
    # Update UI with buttons (or no buttons if fainted)
    try:
        if not p1_fainted:
            await p1_textmsg.edit(p1_final_display, buttons=p1_buttons)
        else:
            await p1_textmsg.edit(p1_final_display)
    except MessageNotModifiedError:
        pass
    
    try:
        if not p2_fainted:
            await p2_textmsg.edit(p2_final_display, buttons=p2_buttons)
        else:
            await p2_textmsg.edit(p2_final_display)
    except MessageNotModifiedError:
        pass
    
    # Clear movetext for next turn
    movetext[p1_id] = {"text_sequence": [], "damage": 0, "move_hit": True, "hp_update_at": 1}
    movetext[p2_id] = {"text_sequence": [], "damage": 0, "move_hit": True, "hp_update_at": 1}
    
    print(f"DEBUG: Battle UI updated for room {roomid}")


async def first_battle_ui(mode, fmt, user_id, event):
    """Initialize the first battle UI without move sequences."""
    if fmt != "singles":
        return
    
    roomid = room[user_id]["roomid"]
    p1_id = int(room_userids[roomid]["p1"])
    p2_id = int(room_userids[roomid]["p2"])
    
    # Initialize movetext
    init_movetext(p1_id)
    init_movetext(p2_id)
    
    # Initialize turn counter
    battle_state[p1_id]["turn"] = 1
    battle_state[p2_id]["turn"] = 1
    
    # Initialize status effects if not already
    if roomid not in status_effects:
        status_effects[roomid] = {
            p1_id: {"paralysis": [], "burn": [], "flinch": []},
            p2_id: {"paralysis": [], "burn": [], "flinch": []}
        }
    
    # Messages
    p1_textmsg = room[p1_id]["start_msg"]
    p2_textmsg = room[p2_id]["start_msg"]
    
    # Active Pokémon
    p1_poke = battle_state[p1_id]["active_pokemon"][0]
    p2_poke = battle_state[p2_id]["active_pokemon"][0]
    
    # HP info
    p1_hp = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]
    p1_max_hp = battle_data[p1_id]["pokemon"][p1_poke]["final_hp"]
    p2_hp = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"]
    p2_max_hp = battle_data[p2_id]["pokemon"][p2_poke]["final_hp"]
    
    p1_hpbar = await hp_bar(p1_hp, p1_max_hp)
    p2_hpbar = await hp_bar(p2_hp, p2_max_hp)
    
    p1_percent = p1_hp / p1_max_hp * 100
    p2_percent = p2_hp / p2_max_hp * 100
    
    # Battle text
    p1_text = (
        f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p2_hpbar} {p2_percent:.0f}% \n"
        f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p1_hpbar} {p1_hp}/{p1_max_hp}"
    )
    
    p2_text = (
        f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p1_hpbar} {p1_percent:.0f}% \n"
        f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
        f"{p2_hpbar} {p2_hp}/{p2_max_hp}"
    )
    
    # Store player text for later use
    battle_state[p1_id]["player_text"] = p1_text
    battle_state[p2_id]["player_text"] = p2_text
    
    # Generate buttons
    p1_moves = battle_data[p1_id]["pokemon"][p1_poke]["moves"]
    p1_buttons = await button_generator(p1_moves, p1_id, p1_poke)
    
    p2_moves = battle_data[p2_id]["pokemon"][p2_poke]["moves"]
    p2_buttons = await button_generator(p2_moves, p2_id, p2_poke)
    
    # Update messages
    await p1_textmsg.edit(p1_text, buttons=p1_buttons)
    await p2_textmsg.edit(p2_text, buttons=p2_buttons)
    
    print(f"DEBUG: First battle UI initialized for room {roomid}")


async def show_switch_menu(user_id, event):
    """Show the Pokemon switching menu."""
    fmt = battle_state[user_id]["fmt"]
    
    if fmt == "singles":
        allowed_pokemon = battle_state[user_id]["allowed_pokemon"]
        active_pokemon = battle_state[user_id]["active_pokemon"][0]
        
        # Get available Pokemon to switch to
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
        init_movetext(p1_id)
        init_movetext(p2_id)
        
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
    init_movetext(p1_id)
    init_movetext(p2_id)
    
    # Add faint message
    user_faint_text = f"{poke_name} fainted!"
    opp_faint_text = f"Opposing {poke_name} fainted!"
    
    if "text_sequence" in movetext[user_id]:
        movetext[user_id]["text_sequence"].append(user_faint_text)
    else:
        movetext[user_id]["text_sequence"] = [user_faint_text]
    
    if "text_sequence" in movetext[opponent_id]:
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
    """Wait for both players to select moves, then execute them in turn order."""
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
        await asyncio.sleep(0.5)
    
    # Get moves
    p1_move = selected_move[p1_id]["move"]
    p2_move = selected_move[p2_id]["move"]
    
    # Determine turn order - switches always go first, then by speed
    p1_is_switch = (p1_move == "SWITCH")
    p2_is_switch = (p2_move == "SWITCH")
    
    if p1_is_switch and p2_is_switch:
        turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), 
                      (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
    elif p1_is_switch:
        turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), 
                      (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
    elif p2_is_switch:
        turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]), 
                      (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]
    else:
        # Both using moves - sort by speed
        p1_speed = battle_data[p1_id]["pokemon"][battle_state[p1_id]["active_pokemon"][0]]["stats"]["spe"]
        p2_speed = battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]["stats"]["spe"]
        
        p1_poke = battle_state[p1_id]["active_pokemon"][0]
        p2_poke = battle_state[p2_id]["active_pokemon"][0]
        
        if room_id in status_effects:
            if p1_id in status_effects[room_id]:
                if p1_poke in status_effects[room_id][p1_id]["paralysis"]:
                    p1_speed = p1_speed / 2
            if p2_id in status_effects[room_id]:
                if p2_poke in status_effects[room_id][p2_id]["paralysis"]:
                    p2_speed = p2_speed / 2
        
        if p1_speed >= p2_speed:
            turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]), 
                          (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
        else:
            turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]), 
                          (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]
    
    # Resolve each move
    for uid, mv, pokemon in turn_order:
        print(f"DEBUG: Executing action {mv} for user {uid}")
        
        # Check if attacker's Pokemon has fainted before executing move
        if await check_fainted_pokemon(uid):
            print(f"DEBUG: {uid}'s Pokemon has fainted, cannot execute action")
            continue
        
        # If this is a switch, skip the move handler (switch already happened)
        if mv == "SWITCH":
            print(f"DEBUG: {uid} switched Pokemon")
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
                    battle_state.pop(player_id, None)
                    room.pop(player_id, None)
                
                print(f"DEBUG: Battle ended - Winner: {winner_id}")
                return
    
    # Apply end-of-turn effects (burn, poison, etc.)
    print("DEBUG: === END-OF-TURN EFFECTS ===")
    had_effects = await end_of_turn_effects(room_id, p1_id, p2_id, 
                                            battle_state[p1_id]["active_pokemon"][0],
                                            battle_state[p2_id]["active_pokemon"][0])
    
    # Update battle UI after moves are resolved
    await battle_ui(battle_state[p1_id]["mode"], fmt, p1_id, event)
    
    # Increment turn counter
    battle_state[p1_id]["turn"] += 1
    battle_state[p2_id]["turn"] += 1
    
    # Check if any Pokemon need to switch after the UI update
    for uid in [p1_id, p2_id]:
        if await check_fainted_pokemon(uid):
            faint_result = await handle_fainted_pokemon(uid, event)
            if faint_result == "switch_required":
                # Show switch menu to the player
                user_msg = room[uid]["start_msg"]
                await show_forced_switch_menu(uid, user_msg)
    
    print(f"DEBUG: Turn {battle_state[p1_id]['turn'] - 1} resolved for room {room_id}")


async def standing_by_fn(event, user_id):
    """Wait for opponent to be ready and start battle."""
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
            
            break
        
        await asyncio.sleep(1)
