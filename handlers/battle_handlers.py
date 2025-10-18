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
pending_texts={}
movetext = {}
status_effects = {}
process_turn={}
stats_modifier={}
battlefield_effects={}

#all moves
all_moves = ["Absorb", "Acid", "Acid Armor", "Agility", "Air Slash", "Amnesia", "Aqua Jet", "Aurora Beam","Mega Drain","Baddy Bad","Barrage","Barrier","Bite","Bone Club","Bouncy Bubble","Bug Buzz","Bulk Up","Brick Break","Bubble","Bubble Beam"]
#Only damage dealing moves
only_damage_moves = ["Cut", "Drill Peck", "Egg Bomb", "Gust", "Horn Attack", "Hydro Pump", "Mega Kick", "Mega Punch", "Pay Day", "Peck", "Pound", "Rock Throw", "Scratch", "Slam", "Sonic Boom", "Strength", "Swift", "Tackle", "Vine Whip", "Water Gun", "Wing Attack"]
#Never miss moves
never_miss_moves = ["Swift"]
#reflect type breaker moves
rlsavbreak_moves=["Brick Break"]
#Paralyze moves
paralyze_moves = ["Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz", "Body Slam", "Lick", "Thunder", "Thunder Punch", "Thunder Shock", "Thunderbolt", "Splishy Splash"]
paralyze_moves30 = ["Body Slam", "Lick", "Thunder", "Splishy Splash"]
paralyze_moves10 = ["Thunder Punch", "Thunder Shock", "Thunderbolt"]
always_paralyze_moves = ["Thunder Wave", "Glare", "Stun Spore", "Buzzy Buzz"]
#flinch moves
flinch_moves = ["Air Slash","Bite","Bone Club"]
flinch_moves10=["Bite","Bone Club"]
flinch_moves20=[]
flinch_moves30=["Air Slash"]
always_flinch_moves=[]
#burn moves
burn_moves=["Sizzly Slide"]
burn_moves10=[]
burn_moves20=[]
always_burn_moves=["Sizzly Slide"]
#poison moves
poison_moves=[""]
poison_moves20=[]
poison_moves30=[]
poison_moves40=[]
always_burn_moves=[""]
#freeze moves
freeze_moves=[]
freeze_moves10=[]
#confusion moves
confusion_moves=[]
confusion_moves10=[]
confusion_moves20=[]
always_confusion_moves=[]
status_indeptheffect={}
#draindamage moves
draindamage_moves=["Absorb","Mega Drain","Leech Life","Bouncy Bubble"]
#stat modifier moves
atk1_buff_moves=["Growth","Meditate","Sharpen"] # these moves raise attack stat by one stage
atk2_buff_moves=["Sword Dance"] # these moves raise attack stat by two stage
def1_buff_moves=["Defense Curl","Harden","Withdraw"] # these moves raise defense stat by one stage
def2_buff_moves=["Acid Armor","Barrier"] # these moves raise defense stat by two stage
spe2_buff_moves=["Agility"] # these moves raise speed stat by two stage
spd2_buff_moves=["Amnesia"] # these moves raise sp defense stat by two stage
atkdef1_buff_moves=["Bulk Up"]
spaspd1_buff_moves=["Calm Mind"]
spaspdspe1_buff_moves=["Quiver Dance"]
miscellaneous_buff_moves=["Shell Smash"]
#0hko moves
zerohitko_moves=["Guillotine","Fissure","Horn Drill"]
#recoil moves
recoil_moves=["Double Edge","Flare Blitz","Submission","Take Down"]
recoil25_moves=["Double Edge","Flare Blitz"]
recoil33_moves=["Submission","Take Down"]
#selfko moves
selfko_moves=["Self Destruct","Explosion"]
#priority moves
priority_moves=["Quick Attack","Aqua Jet","Sucker Punch","Fake Out","Zippy Zap"]
priority01_moves=["Quick Attack","Aqua Jet","Sucker Punch"]
#multiturn moves
multiturn_moves= ["Barrage"]
#debuff moves
debuff_moves=["Acid","Aurora Beam"]
debuffspd10_moves=["Acid","Bug Buzz"]
debbuffatk10_moves=["Aurora Beam"]
debuffspe10_moves=["Bubble","Bubble Beam"]
#refect moves
reflect_moves=["Baddy Bad"]
#sound moves
sound_moves=["Bug Buzz"]
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
        power = move_info.get("Power", 0)
        acc = move_info.get("Accuracy", 100)
        
        return type_name, category, power, acc
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return "normal", "physical", 50, 100




async def accuracy_checker(accuracy,move):
    """Return True if the move hits.
    Accepts:
      - None → always hits
      - fraction (0.0–1.0)
      - percent (0–100)
    """
    if move in never_miss_moves:
        return True
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

async def damage_calc_fn(level, power, attack, defense, type_multiplier,move,effect=None):
    """Calculate Pokémon-style damage.
    `type_multiplier` must be numeric.
    Returns: (damage:int, is_critical:bool)
    """
    
    try:
        type_mult = float(type_multiplier)
    except Exception:
        type_mult = 1.0
    if move == "Pay Day":
        return 20,False
    is_critical = (random.randint(1, 24) == 1)
    critical_mult = 1.5 if is_critical else 1.0

    # Simplified Pokémon damage formula
    base = ((((2 * level) / 5) + 2) * power * (attack / (defense if defense > 0 else 1))) / 50 + 2
    if effect == "confusion":
        return base,False
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

async def final_battle_ui(fmt, user_id, event):
    """Initialize the first battle UI for both players."""
    if fmt == "singles":
        roomid = room[user_id]["roomid"]
        p1_id = int(room_userids[roomid]["p1"])
        p2_id = int(room_userids[roomid]["p2"])
        
        # Initialize turn counter
        
        
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
    if chance >= rvalue:
        return True
    else:
        return False

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
    if chance >= rvalue:
        return True
    else:
        return False

async def burn_check(move):
    chance = 0
    if move in burn_moves10:
        chance = 10
    if move in burn_moves20:
        chance = 20
    if move in always_burn_moves:
        return True
    rvalue = random.randint(1, 100)
    if chance >= rvalue:
        return True
    else:
        return False
async def confusion_check(move):
    chance = 0
    if move in confusion_moves10:
        chance = 10
    if move in confusion_moves20:
        chance = 20
    if move in always_confusion_moves:
        return True
    rvalue = random.randint(1, 100)
    if chance >= rvalue:
        return True
    else:
        return False

async def poison_check(move):
    chance = 0
    if move in poison_moves20:
        chance = 20
    if move in poison_moves30:
        chance = 30
    if move in burn_moves40:
        chance = 40
    if move in always_burn_moves:
        return True
    rvalue = random.randint(1, 100)
    if chance >= rvalue:
        return True
    else:
        return False
async def freeze_check(move):
    chance = 0
    if move in freeze_moves10:
        chance = 10        
    rvalue = random.randint(1, 100)
    if chance >= rvalue:
        return True
    else:
        return False
async def paralysis_checker():
    chance = random.randint(1,100)
    return True if chance <= 25 else False
async def freeze_checker():
    chance = random.randint(1,100)
    return True if chance <= 66 else False
async def drain_damage(damage,drain):
    heal = damage*drain
    return heal
async def stat_multiplier(stage):
    if stage>0:
        multiplier = 2+stage/2
        return multiplier
    if stage<0:
        multiplier = 2/2+stage
        return multiplier
    else:
        return 1
async def hits(move):
    if move == "Barrage":
        def barrage_hits():
            hits = random.choices(
                population=[2, 3, 4, 5],
                weights=[3/8, 3/8, 1/8, 1/8],
                k=1
            )[0]
            return hits
        return barrage_hits()
async def debuff_checker(chance):
    rvalue= random.randint(1,100)
    return True if chance>=rvalue else False 
async def move_handler(user_id, move, poke, fmt, event):
    print(f"DEBUG: Move handler called - User: {user_id}, Move: {move}, Pokemon: {poke}")

    if fmt == "singles":
        try:         
            roomid = room[user_id]["roomid"]
            p1_id = int(room_userids[roomid]["p1"])
            p2_id = int(room_userids[roomid]["p2"])
            opponent_id = p2_id if user_id == p1_id else p1_id
            battlefield_effects.setdefault(roomid, {}).setdefault(user_id, {}).setdefault("reflect", {"status": False, "maxturn": 5, "turn": 0})
            battlefield_effects[roomid].setdefault(opponent_id, {}).setdefault("reflect", {"status": False, "maxturn": 5, "turn": 0})
            if roomid not in stats_modifier:
                stats_modifier[roomid] = {}
                stats_modifier[roomid][user_id]={}
                stats_modifier[roomid][opponent_id]={}
            if poke not in stats_modifier[roomid][user_id]:
                userpoke=poke
                stats_modifier[roomid][user_id][userpoke]={"atk":0,"def":0,"spa":0,"spd":0,"spe":0}
            if poke not in stats_modifier[roomid][user_id]:
                opppoke=battle_state[opponent_id]["active_pokemon"][0]
                stats_modifier[roomid][user_id][userpoke]={"atk":0,"def":0,"spa":0,"spd":0,"spe":0}
                
            if roomid not in status_effects:
                status_effects[roomid] = {}
                # Define all possible conditions (status ailments)
                conditions = ["paralysis", "burn", "poison", "sleep", "confusion", "freeze","flinch"]

                # Initialize both players’ status lists
                status_effects[roomid][user_id] = {cond: [] for cond in conditions}
                status_effects[roomid][opponent_id] = {cond: [] for cond in conditions}
            if roomid not in status_indeptheffect:
                status_indeptheffect[roomid] = {}  
                conditions=["confusion"]
                # Initialize both players’ status lists
                status_indeptheffect[roomid][user_id] = {cond: {} for cond in conditions}
                status_indeptheffect[roomid][opponent_id] = {cond: {} for cond in conditions}
            if roomid not in pending_texts:
                pending_texts[roomid] = {}
                pending_texts[roomid][p1_id]=[]
                pending_texts[roomid][p2_id]=[]
            # Extract move data
            move_type, category, power, accuracy = await move_data_extract(move)

            # Initialize movetext containers
            movetext.setdefault(p1_id, {"text_sequence": [], "hp_update_at": 999})
            movetext.setdefault(p2_id, {"text_sequence": [], "hp_update_at": 999})

            # Pokémon data
            attacker_pokemon = battle_data[user_id]["pokemon"][poke]
            opponent_active = battle_state[opponent_id]["active_pokemon"][0]
            defender_pokemon = battle_data[opponent_id]["pokemon"][opponent_active]

            self_pokemon = poke.split("_")[0]
            opp_pokemon = opponent_active.split("_")[0]
            if move not in all_moves:
                # Missed attack text
                used_text_self = f"{self_pokemon} used {move}"
                miss_text = f"This move cant be used!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!"
                
                # Append (not overwrite)
                movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
                movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])

                movetext[user_id]["hp_update_at"] = 999
                movetext[opponent_id]["hp_update_at"] = 999
                
                return True
            if poke in status_effects[roomid][user_id]["confusion"] and status_indeptheffect[roomid][user_id]["confusion"][poke]["turn"]>status_indeptheffect[roomid][user_id]["confusion"][poke]["max_turn"]:
               status_effects[roomid][user_id]["confusion"].remove(poke) 
               del status_indeptheffect[roomid][user_id]["confusion"][poke]
               used_text_self = f"{self_pokemon} snapped out of its confusion!"
               used_text_opp = f"Opposing {self_pokemon} snapped out of its confusion!"
               movetext[roomid][p1_id]["text_sequence"].append(used_text_self)
               movetext[roomid][p2_id]["text_sequence"].append(used_text_opp)
            #paralysis check
            if poke in status_effects[roomid][user_id]["paralysis"] or poke in status_effects[roomid][user_id]["flinch"] or poke in status_effects[roomid][user_id]["freeze"] or poke in status_effects[roomid][user_id]["confusion"] :
                paralysis = await paralysis_checker()
                if paralysis:
                    # Missed attack text
                    used_text_self = f"{self_pokemon} is paralyzed It cant move!"
                    miss_text = f""
                    used_text_opp = f"Opposing {self_pokemon} is paralyzed It cant move!"

                    # Append (not overwrite)
                    movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
                    movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])

                    movetext[user_id]["hp_update_at"] = 999
                    movetext[opponent_id]["hp_update_at"] = 999
            
                    return True
                #flinch check
                if poke in status_effects[roomid][user_id]["flinch"]:
                    print(poke, "got flinched")
                    
                    status_effects[roomid][user_id]["flinch"].remove(poke)
                    return True
                freeze = await freeze_checker()
                if freeze:
                    # Missed attack text
                    used_text_self = f"{self_pokemon} is frozen solid!"
                    miss_text = f""
                    used_text_opp = f"Opposing {self_pokemon} is frozen solid!"

                    # Append (not overwrite)
                    movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
                    movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])

                    movetext[user_id]["hp_update_at"] = 999
                    movetext[opponent_id]["hp_update_at"] = 999
            
                    return True
                confusion = await confusion_checker()
                
                if confusion:
                    attack_stat = attacker_pokemon["final_atk"]
                    defense_stat = attacker_pokemon["final_def"]
                    damage, is_critical = await damage_calc_fn(100, 40, attack_stat, defense_stat, type_mult, move, "confusion")
                    # Store damage for the OPPONENT (who is receiving the damage)
                    maxhp=attacker_pokemon["final_hp"] 
                    curhp=attacker_pokemon["current_hp"] - damage
                    attacker_pokemon["current_hp"]= curhp
                    # ✅ Build text sequences
                    used_text_self = f"{self_pokemon} is confused!\nIt hurts itself from confusion"
                    used_text_opp = f"Opposing {self_pokemon} is confused!\nIt hurts itself from confusion"
                    seq_self = [used_text_self]
                    seq_opp = [used_text_opp]
                    # ✅ Append to movetext (don’t replace)
                    movetext[user_id]["text_sequence"].extend(seq_self)
                    movetext[opponent_id]["text_sequence"].extend(seq_opp)
                    movetext[user_id]["hp_update_at"] = 1
                    movetext[opponent_id]["hp_update_at"] = 1
            #check for stat modifier moves
            if move in atk1_buff_moves:
                stats_modifier[roomid][user_id][poke]["atk"]+=1
                # ✅ Build text sequences
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Attack rose!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Attack rose!"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in atk2_buff_moves:
                stats_modifier[roomid][user_id][poke]["atk"]+=2
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Attack rose sharply!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Attack rose! sharply"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in def1_buff_moves:
                stats_modifier[roomid][user_id][poke]["def"]+=1
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Defense rose!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Defense rose!"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in def2_buff_moves:
                stats_modifier[roomid][user_id][poke]["def"]+=2 
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Defense rose sharply!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Defense rose! sharply"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in spe2_buff_moves:
                stats_modifier[roomid][user_id][poke]["spe"]+=2 
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Speed rose sharply!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Speed rose! sharply"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in spd2_buff_moves:
                stats_modifier[roomid][user_id][poke]["spd"]+=2 
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Special Defense rose sharply!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Special Defense rose sharply!"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in atkdef1_buff_moves:
                stats_modifier[roomid][user_id][poke]["atk"]+=1
                stats_modifier[roomid][user_id][poke]["def"]+=1
                used_text_self = f"{self_pokemon} used {move}!/n{self_pokemon}'s Attack rose!/n{self_pokemon}'s Defense rose!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!/nOpposing {self_pokemon}'s Attack rose!/nOpposing {self_pokemon}'s Defense rose!"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in spaspd1_buff_moves:
                stats_modifier[roomid][user_id][poke]["spa"]+=1
                stats_modifier[roomid][user_id][poke]["spd"]+=1
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Special Attack rose!\n{self_pokemon}'s Special Defense rose!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Special Attack rose!\nOpposing {self_pokemon}'s Special Defense rose!"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in spaspdspe1_buff_moves:
                stats_modifier[roomid][user_id][poke]["spa"]+=1
                stats_modifier[roomid][user_id][poke]["spd"]+=1
                stats_modifier[roomid][user_id][poke]["spe"]+=1
                used_text_self = f"{self_pokemon} used {move}!\n{self_pokemon}'s Special Attack rose!\n{self_pokemon}'s Special Defense rose!\n{self_pokemon}'s Speed rose!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!\nOpposing {self_pokemon}'s Special Attack rose!\nOpposing {self_pokemon}'s Special Defense rose!\nOpposing{self_pokemon}'s Speed rose!"
                # Build attacker’s sequence
                seq_self = [used_text_self]
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)
                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1                
                await battle_ui(fmt, user_id, event)
                return True
            if move in miscellaneous_buff_moves:
                if move == "Shell Smash":
                    stats_modifier[roomid][user_id][poke]["atk"]+=2
                    stats_modifier[roomid][user_id][poke]["def"]-=1
                    stats_modifier[roomid][user_id][poke]["spa"]+=2
                    stats_modifier[roomid][user_id][poke]["spd"]-=1
                    stats_modifier[roomid][user_id][poke]["spe"]+=2
                    used_text_self = f"{self_pokemon} used {move}!/n{self_pokemon}'s Attack rose sharply!\n{self_pokemon}'s Defense fell!/n{self_pokemon}'s Special Attack rose sharply!/n{self_pokemon}'s Special Defense fell!\n{self_pokemon}'s Speed rose sharply!"
                    used_text_opp = f"Opposing {self_pokemon} used {move}!/nOpposing {self_pokemon}'s Attack rose sharply!\nOpposing {self_pokemon}'s Defense fell!/nOpposing {self_pokemon}'s Special Attack rose sharply!/nOpposing {self_pokemon}'s Special Defense fell!\nOpposing {self_pokemon}'s Speed rose sharply!"    
                    # Build attacker’s sequence
                    seq_self = [used_text_self]
                    # Build opponent’s sequence
                    seq_opp = [used_text_opp]
                    # ✅ Append to movetext (don’t replace)
                    movetext[user_id]["text_sequence"].extend(seq_self)
                    movetext[opponent_id]["text_sequence"].extend(seq_opp)
                    movetext[user_id]["hp_update_at"] = 1
                    movetext[opponent_id]["hp_update_at"] = 1                
                    await battle_ui(fmt, user_id, event)
                    return True
            # ✅ Accuracy check
            hit = await accuracy_checker(accuracy,move)
            if not hit:
                # Missed attack text
                used_text_self = f"{self_pokemon} used {move}!"
                miss_text = f"Opposing {opp_pokemon} avoided the attack!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!"

                # Append (not overwrite)
                movetext[user_id]["text_sequence"].extend([used_text_self, miss_text])
                movetext[opponent_id]["text_sequence"].extend([used_text_opp, miss_text])

                movetext[user_id]["hp_update_at"] = 999
                movetext[opponent_id]["hp_update_at"] = 999
                return True

            # ✅ Attack/Defense stats
            if category.lower() == "physical":
                stage_atk = stats_modifier[roomid][user_id][poke]["atk"]
                multiplier_atk=await stat_multiplier(stage_atk)
                attack_stat = attacker_pokemon["final_atk"]*multiplier_atk
                stage_def = stats_modifier[roomid][opponent_id][opponent_active]["def"]
                multiplier_def=await stat_multiplier(stage_def)
                defense_stat = defender_pokemon["final_def"]*multiplier_def
            else:
                stage_atk = stats_modifier[roomid][user_id][poke]["spa"]
                multiplier_atk=await stat_multiplier(stage_atk)
                attack_stat = attacker_pokemon["final_spa"]*multiplier_atk
                stage_def = stats_modifier[roomid][opponent_id][opponent_active]["spd"]
                multiplier_def=await stat_multiplier(stage_def)
                defense_stat = defender_pokemon["final_spd"]*multiplier_def

            # ✅ Type effectiveness
            type_eff_raw = await type_modifier(
                move_type, defender_pokemon.get("type1", "normal"), defender_pokemon.get("type2")
            )
            type_mult, effect_text = interpret_type_effect(type_eff_raw)
            if move in zerohitko_moves:
                if type_mult!=0:
                    damage = defender_pokemon["current_hp"]
                    defender_pokemon["current_hp"]-=damage
                    # ✅ Build text sequences
                    used_text_self = f"{self_pokemon} used {move}!"
                    used_text_opp = f"Opposing {self_pokemon} used {move}!"
                    # Build attacker’s sequence
                    seq_self = [used_text_self]
                    if power > 0 and effect_text != "Effective":
                        seq_self.append(effect_text)
                    # Build opponent’s sequence
                    seq_opp = [used_text_opp]
                    if power > 0 and effect_text != "Effective":
                        seq_opp.append(effect_text)
                    # ✅ Append to movetext (don’t replace)
                    movetext[user_id]["text_sequence"].extend(seq_self)
                    movetext[opponent_id]["text_sequence"].extend(seq_opp)

                    movetext[user_id]["hp_update_at"] = 1
                    movetext[opponent_id]["hp_update_at"] = 1
                
                    await battle_ui(fmt, user_id, event)
                    return True
                else:
                    used_text_self = f"{self_pokemon} used {move}!"
                    used_text_opp = f"Opposing {self_pokemon} used {move}!"
                    # Build attacker’s sequence
                    seq_self = [used_text_self]
                    if power > 0 and effect_text != "Effective":
                        seq_self.append(effect_text)
                    # Build opponent’s sequence
                    seq_opp = [used_text_opp]
                    if power > 0 and effect_text != "Effective":
                        seq_opp.append(effect_text)
                    # ✅ Append to movetext (don’t replace)
                    movetext[user_id]["text_sequence"].extend(seq_self)
                    movetext[opponent_id]["text_sequence"].extend(seq_opp)

                    movetext[user_id]["hp_update_at"] = 1
                    movetext[opponent_id]["hp_update_at"] = 1
                
                    await battle_ui(fmt, user_id, event)
                    return True
            if move in multiturn_moves:
                hits = await hits(move)
                Critical = False
                for i in range(1,hits+1):
                    damage, is_critical = await damage_calc_fn(100, power, attack_stat, defense_stat, type_mult, move)
                    defender_pokemon["current_hp"] -= damage
                    if is_critical:
                        Critical= True
                # ✅ Build text sequences
                used_text_self = f"{self_pokemon} used {move}!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!"
                crit_text = "A critical hit!" if Critical else None

                # Build attacker’s sequence
                seq_self = [used_text_self]
                if crit_text:
                    seq_self.append(crit_text)
                if power > 0 and effect_text != "Effective":
                    seq_self.append(effect_text)
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                if crit_text:
                    seq_opp.append(crit_text)
                if power > 0 and effect_text != "Effective":
                    seq_opp.append(effect_text)
                seq_self.append(f"Hit {hits} times!")
                seq_opp.append(f"Hit {hits} times!")
                battle_ui(fmt, user_id, event)
                return True
            # ✅ Damage calculation
            damage, is_critical = await damage_calc_fn(100, power, attack_stat, defense_stat, type_mult, move)
            '''if battlefield_effects[roomid][opponent_id]["reflect"]["status"] is True:
                reflect = battlefield_effects[roomid][opponent_id]["reflect"]
                maxturns= 5
                turn = reflect["turn"]
                current_turn=battle_state["user_id"]["turn"]
                if current_turn<maxturns+turn:
                    damage = damage/2 if category.lower== "physical" else damage
                if current_turn>=maxturns+turn:  
                    reflect["status"]= False
                    reflect["turn"]=0'''
            if move in selfko_moves:
                attacker_pokemon["current_hp"]=0
            if move in recoil_moves:
                if move in recoil25_moves:
                    recoil=1/4
                if move in recoil33_moves:
                    recoil=1/3
                curhp=defender_pokemon["current_hp"] - damage
                defender_pokemon["current_hp"]= curhp
                curhp=attacker_pokemon["current_hp"]
                recoil_damage = curhp*recoil
                attacker_pokemon["current_hp"] = max(0,curhp-recoil_damage)
                # ✅ Build text sequences
                used_text_self = f"{self_pokemon} used {move}!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!"
                crit_text = "A critical hit!" if is_critical else None

                # Build attacker’s sequence
                seq_self = [used_text_self]
                if crit_text:
                    seq_self.append(crit_text)
                if power > 0 and effect_text != "Effective":
                    seq_self.append(effect_text)
                seq_self.append(f"The opposing {opp_pokemon} was damaged by the recoil")
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                seq_opp.append(f"{opp_pokemon} was damaged by the recoil")
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)

                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1
                
                await battle_ui(fmt, user_id, event)
                return True
            if move in draindamage_moves:
                drain = 1/2
                heal = await drain_damage(damage,drain)
                maxhp=defender_pokemon["final_hp"] 
                curhp=defender_pokemon["current_hp"] - damage
                defender_pokemon["current_hp"]= curhp
                maxhp=attacker_pokemon["final_hp"] 
                curhp=attacker_pokemon["current_hp"] + heal
                attacker_pokemon["current_hp"]= curhp
                
                # ✅ Build text sequences
                used_text_self = f"{self_pokemon} used {move}!"
                used_text_opp = f"Opposing {self_pokemon} used {move}!"
                crit_text = "A critical hit!" if is_critical else None

                # Build attacker’s sequence
                seq_self = [used_text_self]
                if crit_text:
                    seq_self.append(crit_text)
                if power > 0 and effect_text != "Effective":
                    seq_self.append(effect_text)
                seq_self.append(f"The opposing {opp_pokemon} had its energy drained!")
                # Build opponent’s sequence
                seq_opp = [used_text_opp]
                seq_opp.append(f"{opp_pokemon} had its energy drained!")
                # ✅ Append to movetext (don’t replace)
                movetext[user_id]["text_sequence"].extend(seq_self)
                movetext[opponent_id]["text_sequence"].extend(seq_opp)

                movetext[user_id]["hp_update_at"] = 1
                movetext[opponent_id]["hp_update_at"] = 1
                
                await battle_ui(fmt, user_id, event)
                return True

            if move in reflect_moves:
                '''reflect=battlefield_effects[roomid][user_id]["reflect"]
                reflect["status"]=True
                reflect["maxturn"]=5
                reflect["turn"]=battle_state[user_id]["turn"]'''
            # Store damage for the OPPONENT (who is receiving the damage)
            maxhp=defender_pokemon["final_hp"] 
            curhp=defender_pokemon["current_hp"] - damage
            defender_pokemon["current_hp"]= curhp
            print(f"DEBUG: {self_pokemon} (user {user_id}) attacks {opp_pokemon} (user {opponent_id}) for {damage} damage")

            # ✅ Build text sequences
            used_text_self = f"{self_pokemon} used {move}!"
            used_text_opp = f"Opposing {self_pokemon} used {move}!"
            crit_text = "A critical hit!" if is_critical else None

            # Build attacker’s sequence
            seq_self = [used_text_self]
            if crit_text:
                seq_self.append(crit_text)
            if power > 0 and effect_text != "Effective":
                seq_self.append(effect_text)
            # Build opponent’s sequence
            seq_opp = [used_text_opp]
            #debuff check
            if move in debuff_moves:
                if move in debuffspd10_moves:
                    chance = 10
                    debuff=await debuff_checker(chance)
                    if debuff:
                        stats_modifier[roomid][opponent_id][opponent_active]["spd"]-=1
                        usertxt = f"The Opposing {opp_pokemon}'s special defense fell!"
                        opptxt = f"{opp_pokemon}'s special defense fell!"
                        seq_self.append(usertxt)
                        seq_opp.append(opptxt)
                if move in debuffatk10_moves:
                    chance = 10
                    debuff=await debuff_checker(chance)
                    if debuff:
                        stats_modifier[roomid][opponent_id][opponent_active]["atk"]-=1
                        usertxt = f"The Opposing {opp_pokemon}'s attack fell!"
                        opptxt = f"{opp_pokemon}'s attack fell!"
                        seq_self.append(usertxt)
                        seq_opp.append(opptxt)
                if move in debuffspe10_moves:
                    chance = 10
                    debuff=await debuff_checker(chance)
                    if debuff:
                        stats_modifier[roomid][opponent_id][opponent_active]["spe"]-=1
                        usertxt = f"The Opposing {opp_pokemon}'s speed fell!"
                        opptxt = f"{opp_pokemon}'s speed fell!"
                        seq_self.append(usertxt)
                        seq_opp.append(opptxt)
            #paralyze check
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
            if move in flinch_moves:
                print("flinch moves condition met")
                flinch = await flinch_check(move)
                flinch_list = status_effects[roomid][opponent_id]["flinch"]

                
                if flinch:
                    print("flinch pokemon is appending")
                    flinch_list.append(opponent_active)
                    used_text_opp= f"{self_pokemon} flinched and couldn't move!"
                    
                    used_text_self = f"Opposing {self_pokemon} flinched and couldn't move!"
                    seq_self.append(used_text_self)
                    seq_opp.append(used_text_opp)
                    if opponent_active in flinch_list:
                        print("flinch pokemon not found")
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
            if move in poison_moves:
                poison = await poison_check(move)
                poison_list = status_effects[roomid][opponent_id]["poison"]

                if opponent_active in burn_list:
                    poison_textuser = f"The Opposing {opp_pokemon} is already poisoned!"
                    poison_textopp = f"{opp_pokemon} is already poisoned!"
                    seq_self.append(poison_textuser)
                    seq_opp.append(poison_textopp)
                elif poison:
                    poison_textuser = f"The Opposing {opp_pokemon} was poisoned!"
                    poison_textopp = f"{opp_pokemon} was poisoned!"
                    poison_list.append(opponent_active)
                    seq_self.append(poison_textuser)
                    seq_opp.append(poison_textopp)

            if move in confusion_moves:
                confusion = await confusion__check(move)
                confusion_list = status_effects[roomid][opponent_id]["confusion"]

                if opponent_active in confusion_list:
                    confusion_textuser = f"The Opposing {opp_pokemon} is already confused!"
                    confusion_textopp = f"{opp_pokemon} is already confused!"
                    seq_self.append(confusion_textuser)
                    seq_opp.append(confusion_textopp)
                elif confusion:
                    confusion_textuser = f"The Opposing {opp_pokemon} is confused!"
                    confusion_textopp = f"{opp_pokemon} is confused!"
                    confusion_list.append(opponent_active)
                    maxturn=random.randint(2,6)
                    status_indeptheffect[roomid][opponent_id]["confusion"][opponent_active]={"turn":0,"max_turn":maxturn}
                    seq_self.append(confusion_textuser)
                    seq_opp.append(confusion_textopp)
            
            # ✅ Append to movetext (don’t replace)
            movetext[user_id]["text_sequence"].extend(seq_self)
            movetext[opponent_id]["text_sequence"].extend(seq_opp)

            movetext[user_id]["hp_update_at"] = 1
            movetext[opponent_id]["hp_update_at"] = 1
            
            print(
                f"DEBUG: Move resolved - {self_pokemon} used {move}, "
                f"Damage: {damage} will be applied to {opp_pokemon}"
            )
            
            await battle_ui(fmt, user_id, event)
            return True

        except Exception as e:
            print(f"ERROR in move_handler: {e}")
            import traceback
            traceback.print_exc()
            return False
import asyncio
import re

async def battle_ui(fmt, user_id, event):
    """Configure the battle UI for both players."""
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
        
        
        p1_textsequence=movetext[p1_id]["text_sequence"]
        p2_textsequence=movetext[p2_id]["text_sequence"]
        for i,j in zip(p1_textsequence,p2_textsequence):
            if i==0 or j==0:
                p1_text0= f"{i}\n\n{battle_state[p1_id]['player_text']}"
                p2_text0= f"{j}\n\n{battle_state[p2_id]['player_text']}"
                p1_text1= f"{i}\n\n{p1_text}"
                p2_text1= f"{j}\n\n{p2_text}"
                await p1_textmsg.edit(text=p1_text0)
                await p2_textmsg.edit(text=p2_text0)
                await asyncio.sleep(2)
                await p1_textmsg.edit(text=p1_text1)
                await p2_textmsg.edit(text=p2_text1)
            if i!=0 or j!=0:
                p1_text2= f"{i}\n\n{p1_text}"
                p2_text2= f"{j}\n\n{p2_text}"
                await p1_textmsg.edit(text=p1_text2)
                await p2_textmsg.edit(text=p2_text2)
                await asyncio.sleep(2)
        await p1_textmsg.edit(p1_text)
        await p2_textmsg.edit(p2_text)
        print(status_effects)
        
        battle_state[p1_id]["player_text"] = p1_text
        battle_state[p2_id]["player_text"] = p2_text
        movetext[p1_id]["text_sequence"]=[]
        movetext[p2_id]["text_sequence"]=[]
        print(f"DEBUG: First battle UI initialized for room {roomid}")
    
    
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
        del stats_modifier[roomid][user_id][battle_state[user_id]["active_pokemon"][0]]
        stats_modifier[roomid][user_id][new_poke_id]={"atk":0,"def":0,"spa":0,"spd":0,"spe":0}
        
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


async def endturneffect_battleui(fmt,user_id,event):
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
        
        p2_text = (
            f"__**「{p1_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p1_poke_hpbar} {p1hppercent:.0f}% \n"
            f"__**「{p2_poke.split('_')[0].capitalize()}(Lv.100)」**__\n"
            f"{p2_poke_hpbar} {battle_data[p2_id]['pokemon'][p2_poke]['current_hp']}/{battle_data[p2_id]['pokemon'][p2_poke]['final_hp']}"
        )
        #burn
        if p1_poke not in status_effects[roomid][p1_id]["burn"] :
            return
        if p2_poke not in status_effects[roomid][p2_id]["burn"]:
            return
        p1_burntextuser=""
        p1_burntextopp=""
        p2_burntextuser=""
        p2_burntextopp=""
        if p1_poke in status_effects[roomid][p1_id]["burn"]:
            curhp = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]
            damage = curhp//8
            newhp = curhp-damage
            battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]=newhp
            p1_burntextuser=f"{p1_poke} was hurt by its burn!"
            p1_burntextopp=f"Opposing {p1_poke} was hurt by its burn!"
            await p1_textmsg.edit(text=f"{p1_burntextuser}\n\n{p1_text}")
            await p2_textmsg.edit(text=f"{p1_burntextopp}\n\n{p2_text}")
        await asyncio.sleep(1.5)
        if p2_poke in status_effects[roomid][p2_id]["burn"]:
            curhp = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"]
            damage = curhp//8
            newhp = curhp-damage
            battle_data[p2_id]["pokemon"][p12poke]["current_hp"]=newhp
            p2_burntextuser=f"{p2_poke} was hurt by its burn!"
            p2_burntextopp=f"Opposing {p2_poke} was hurt by its burn!"
            await p1_textmsg.edit(text=f"{p2_burntextuser}\n\n{p1_text}")
            await p2_textmsg.edit(text=f"{p2_burntextopp}\n\n{p2_text}")
        if not p1_poke in status_effects[roomid][p1_id]["poison"] or p2_poke in status_effects[roomid][p2_id]["poison"]:
            return
        p1_posiontextuser=""
        p1_poisontextopp=""
        p2_poisontextuser=""
        p2_poisontextopp=""
        if p1_poke in status_effects[roomid][p1_id]["poison"]:
            curhp = battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]
            damage = curhp//8
            newhp = curhp-damage
            battle_data[p1_id]["pokemon"][p1_poke]["current_hp"]=newhp
            p1_poisontextuser=f"{p1_poke} was hurt by its poison!"
            p1_poisontextopp=f"Opposing {p1_poke} was hurt by its poison!"
            await p1_textmsg.edit(text=f"{p1_poisontextuser}\n\n{p1_text}")
            await p2_textmsg.edit(text=f"{p1_poisontextopp}\n\n{p2_text}")
        await asyncio.sleep(1.5)
        if p2_poke in status_effects[roomid][p2_id]["poison"]:
            curhp = battle_data[p2_id]["pokemon"][p2_poke]["current_hp"]
            damage = curhp//8
            newhp = curhp-damage
            battle_data[p2_id]["pokemon"][p12poke]["current_hp"]=newhp
            p2_poisontextuser=f"{p2_poke} was hurt by its poiosn!"
            p2_poisontextopp=f"Opposing {p2_poke} was hurt by its poison!"
            await p1_textmsg.edit(text=f"{p2_poisontextuser}\n\n{p1_text}")
            await p2_textmsg.edit(text=f"{p2_poisontextopp}\n\n{p2_text}")

async def priority_value(move):
    if move in priority01_moves:
        return 1
    else: 
        return 0
async def awaiting_move_action(room_id, fmt, move, poke, event):
    p1_id = int(room_userids[room_id]["p1"])
    p2_id = int(room_userids[room_id]["p2"])

    for uid in [p1_id, p2_id]:
        selected_move.setdefault(uid, {})

    print(f"DEBUG: awaiting_move_action triggered for room {room_id}, fmt={fmt}")

    # Wait until both players have selected a move
    while True:
        p1_turn = selected_move.get(p1_id, {}).get("turn")
        p2_turn = selected_move.get(p2_id, {}).get("turn")
        p1_ready = (p1_turn == battle_state[p1_id]["turn"])
        p2_ready = (p2_turn == battle_state[p2_id]["turn"])

        if p1_ready and p2_ready:
            # Lock the turn processing to one coroutine only
            if process_turn.get(room_id, False):
                print(f"DEBUG: Turn already being processed for room {room_id}, skipping duplicate")
                return
            process_turn[room_id] = True
            print(f"DEBUG: Turn lock acquired for room {room_id}")
            break

        await asyncio.sleep(0.5)

    try:
        print("got out - processing turn")
        
        # Define all possible conditions (status ailments)
        conditions = ["paralysis", "burn", "poison", "sleep", "confusion", "freeze", "flinch"]
        if room_id not in status_effects:
            status_effects[room_id] = {}
        # Ensure both players have all conditions initialized
        for pid in [p1_id, p2_id]:
            status_effects[room_id].setdefault(pid, {})
            for cond in conditions:
                status_effects[room_id][pid].setdefault(cond, [])
        room_stats = stats_modifier.setdefault(room_id, {})
        p1_stats = room_stats.setdefault(p1_id, {})
        p2_stats = room_stats.setdefault(p2_id, {})
        p1_active = battle_state[p1_id]["active_pokemon"][0]
        p2_active = battle_state[p2_id]["active_pokemon"][0]
        p1_stats.setdefault(p1_active, {"atk":0,"def":0,"spa":0,"spd":0,"spe":0})
        p2_stats.setdefault(p2_active, {"atk":0,"def":0,"spa":0,"spd":0,"spe":0})
        p1_stage = p1_stats[p1_active]["spe"]
        p2_stage = p2_stats[p2_active]["spe"]
        # Get moves
        p1_move = selected_move[p1_id]["move"]
        p2_move = selected_move[p2_id]["move"]
        p1_priority=await priority_value(p1_move)
        p2_priority=await priority_value(p2_move)
        # Determine turn order
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
            print(stats_modifier)
            # Both use moves → decide by speed (consider paralysis)
            
            p1_multiplier = await stat_multiplier(p1_stage)
            p2_multiplier = await stat_multiplier(p2_stage)
            p1_speed = battle_data[p1_id]["pokemon"][battle_state[p1_id]["active_pokemon"][0]]["stats"]["spe"]*p1_multiplier
            p2_speed = battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]["stats"]["spe"]*p2_multiplier
            p1_poke = battle_data[p1_id]["pokemon"][battle_state[p1_id]["active_pokemon"][0]]
            p2_poke = battle_data[p2_id]["pokemon"][battle_state[p2_id]["active_pokemon"][0]]

            if room_id in status_effects:
                if p1_id in status_effects[room_id]:
                    if p1_poke in status_effects[room_id][p1_id]["paralysis"]:
                        p1_speed /= 2
                if p2_id in status_effects[room_id]:
                    if p2_poke in status_effects[room_id][p2_id]["paralysis"]:
                        p2_speed /= 2

            if p1_speed >= p2_speed:
                if p2_priority>p1_priority:
                    turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]),
                              (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]
                else:
                    turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]),
                              (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
            if p2_speed >= p1_speed:
                if p1_priority>p2_priority:
                    turn_order = [(p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0]),
                              (p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0])]
                else:
                    turn_order = [(p2_id, p2_move, battle_state[p2_id]["active_pokemon"][0]),
                              (p1_id, p1_move, battle_state[p1_id]["active_pokemon"][0])]
            
        # --- Main move resolution loop ---
        for uid, mv, pokemon in turn_order:
            print(f"DEBUG: Executing action {mv} for user {uid}")

            if await check_fainted_pokemon(uid):
                print(f"DEBUG: {uid}'s Pokemon has fainted, cannot execute action")
                continue

            if mv == "SWITCH":
                print(f"DEBUG: {uid} switched Pokemon, turn is over")
                continue

            await move_handler(uid, mv, pokemon, fmt, event)
            # Check if defender fainted
            defender_id = p2_id if uid == p1_id else p1_id
            if await check_fainted_pokemon(uid):
                faint_result = await handle_fainted_pokemon(uid, event)
                if faint_result == "lost":
                    winner_id = defenderid
                    loser_id = uid

                    winner_msg = room[winner_id]["start_msg"]
                    loser_msg = room[loser_id]["start_msg"]
                    await winner_msg.edit("🎉 You won the battle! 🎉")
                    await loser_msg.edit("You lost the battle!")

                    for player_id in [p1_id, p2_id]:
                        battle_state.pop(player_id, None)
                        room.pop(player_id, None)

                    print(f"DEBUG: Battle ended - Winner: {winner_id}")
                    return
            # Check if defender fainted
            defender_id = p2_id if uid == p1_id else p1_id
            if await check_fainted_pokemon(defender_id):
                faint_result = await handle_fainted_pokemon(defender_id, event)
                if faint_result == "lost":
                    winner_id = uid
                    loser_id = defender_id

                    winner_msg = room[winner_id]["start_msg"]
                    loser_msg = room[loser_id]["start_msg"]
                    await winner_msg.edit("🎉 You won the battle! 🎉")
                    await loser_msg.edit("You lost the battle!")

                    for player_id in [p1_id, p2_id]:
                        battle_state.pop(player_id, None)
                        room.pop(player_id, None)

                    print(f"DEBUG: Battle ended - Winner: {winner_id}")
                    return
        await asyncio.sleep(1.5)
        await endturneffect_battleui(fmt, p1_id, event)
        # Increment turn counter
        battle_state[p1_id]["turn"] += 1
        battle_state[p2_id]["turn"] += 1

        #call final battle ui 
        await final_battle_ui(fmt, p1_id, event)

        # Handle fainted Pokémon after the UI update
        for uid in [p1_id, p2_id]:
            if await check_fainted_pokemon(uid):
                faint_result = await handle_fainted_pokemon(uid, event)
                if faint_result == "switch_required":
                    user_msg = room[uid]["start_msg"]
                    await show_forced_switch_menu(uid, user_msg)
        selected_move[p1_id] = {}
        selected_move[p2_id] = {}
        print(f"DEBUG: Turn {battle_state[p1_id]['turn'] - 1} resolved for room {room_id}")

    finally:
        process_turn[room_id] = False
        print(f"DEBUG: Turn lock released for room {room_id}")

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
