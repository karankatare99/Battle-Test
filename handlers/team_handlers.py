# handlers/team_handlers.py - Team management commands
from telethon import events, Button
from database import users, pokedata
from config import POKEMON_PER_PAGE

def register_team_handlers(bot):
    
    @bot.on(events.NewMessage(pattern="/team"))
    async def team_handler(event):
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        
        if not user:
            await event.respond("No profile found. Use /start first.")
            return
        
        team = user.get("team", [])
        if not team:
            text = "Your team is empty! Add to select Pokémon from your profile."
            buttons = [Button.inline("➕ Add", "team:add:page:0")]
            await event.respond(text, buttons=buttons)
            return
        
        await send_team_page(event, user)

    async def send_team_page(event, user):
        team_ids = user.get("team", [])
        pokes = list(pokedata.find({"_id": {"$in": team_ids}}))
        poke_map = {p["_id"]: p for p in pokes}
        
        text = "🏆 **Your Team:**\n\n"
        for i, poke_id in enumerate(team_ids, 1):
            poke = poke_map.get(poke_id)
            if poke:
                text += f"{i}. {poke['name']} (ID: {poke_id})\n"
            else:
                text += f"{i}. Unknown Pokémon ({poke_id})\n"
        
        buttons = [
            [Button.inline("➕ Add", "team:add:page:0")],
            [Button.inline("➖ Remove", "team:remove"), Button.inline("🔄 Switch", "team:switch")]
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
            await event.answer("No more Pokémon left in your profile to add.", alert=True)
            return
        
        total_pages = (len(available_ids) - 1) // POKEMON_PER_PAGE + 1
        start = page * POKEMON_PER_PAGE
        end = start + POKEMON_PER_PAGE
        page_items = available_ids[start:end]
        
        pokes = list(pokedata.find({"_id": {"$in": page_items}}))
        poke_map = {p["_id"]: p for p in pokes}
        
        text = f"Select a Pokémon to Add (Page {page+1}/{total_pages}):\n\n"
        for i, pid in enumerate(page_items, start+1):
            poke = poke_map.get(pid)
            if poke:
                text += f"{i}. {poke['name']} (ID: {poke['pokemon_id']})\n"
            else:
                text += f"{i}. Unknown ({pid})\n"
        
        buttons = []
        row = []
        for i, pid in enumerate(page_items, start=start):
            row.append(Button.inline(str(i % POKEMON_PER_PAGE + 1), f"team:add:{pid}".encode()))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        nav = []
        if page > 0:
            nav.append(Button.inline("◀️ Prev", f"team:add:page:{page-1}".encode()))
        if page < total_pages - 1:
            nav.append(Button.inline("Next ▶️", f"team:add:page:{page+1}".encode()))
        if nav:
            buttons.append(nav)
        
        buttons.append([Button.inline("⬅️ Back", "team:back")])
        
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(text, buttons=buttons)
        else:
            await event.respond(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"team:add:page:(.*)"))
    async def team_add_page_event(event):
        page = int(event.pattern_match.group(1))
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        await send_add_page(event, user, page)

    @bot.on(events.CallbackQuery(pattern=b"team:add:(.*)"))
    async def confirm_add_event(event):
        poke_id = event.pattern_match.group(1).decode()
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        
        team = user.get("team", [])
        if len(team) >= 6:
            await event.answer("Team is already full (6 Pokémon max)!", alert=True)
            return
        
        owned_ids = user.get("pokemon", [])
        if poke_id not in owned_ids:
            await event.answer("You don't own this Pokémon.", alert=True)
            return
        
        if poke_id not in team:
            users.update_one({"user_id": user_id}, {"$push": {"team": poke_id}})
            await event.answer("Pokémon added to team!")
        else:
            await event.answer("That Pokémon is already in your team.", alert=True)
        
        user = users.find_one({"user_id": user_id})
        await send_team_page(event, user)

    @bot.on(events.CallbackQuery(pattern=b"team:back"))
    async def back_to_team_event(event):
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        await send_team_page(event, user)

    async def send_remove_page(event, user, page=0):
        team = user.get("team", [])
        if not team:
            await event.answer("Your team is empty!", alert=True)
            return
        
        total_pages = (len(team) - 1) // POKEMON_PER_PAGE + 1
        start = page * POKEMON_PER_PAGE
        end = start + POKEMON_PER_PAGE
        page_items = team[start:end]
        
        text = f"Select a Pokémon to Remove (Page {page+1}/{total_pages}):\n\n"
        for i, poke_id in enumerate(page_items, start+1):
            poke = pokedata.find_one({"_id": poke_id}) or {}
            text += f"{i}. {poke.get('name', 'Unknown')} ({poke.get('pokemon_id', '?')})\n"
        
        buttons = []
        row = []
        for i, poke_id in enumerate(page_items, start=start):
            row.append(Button.inline(str(i % POKEMON_PER_PAGE + 1), f"team:remove:{poke_id}".encode()))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        nav = []
        if page > 0:
            nav.append(Button.inline("◀️ Prev", f"team:remove:page:{page-1}".encode()))
        if page < total_pages - 1:
            nav.append(Button.inline("Next ▶️", f"team:remove:page:{page+1}".encode()))
        if nav:
            buttons.append(nav)
        
        buttons.append([Button.inline("⬅️ Back", "team:back")])
        
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(text, buttons=buttons)
        else:
            await event.respond(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"team:remove"))
    async def team_remove_menu_event(event):
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        await send_remove_page(event, user, 0)

    @bot.on(events.CallbackQuery(pattern=b"team:remove:page:(.*)"))
    async def team_remove_page_event(event):
        page = int(event.pattern_match.group(1))
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        await send_remove_page(event, user, page)

    @bot.on(events.CallbackQuery(pattern=b"team:remove:(.*)"))
    async def confirm_remove_event(event):
        poke_key = event.pattern_match.group(1).decode()
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        
        team = user.get("team", [])
        if poke_key in team:
            users.update_one({"user_id": user_id}, {"$pull": {"team": poke_key}})
            await event.answer("Pokémon removed from team!")
        else:
            await event.answer("That Pokémon is not in your team.", alert=True)
        
        user = users.find_one({"user_id": user_id})
        await send_team_page(event, user)

    @bot.on(events.CallbackQuery(pattern=b"team:switch"))
    async def team_switch_start_event(event):
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        team = user.get("team", [])
        
        if len(team) < 2:
            await event.answer("You need at least 2 Pokémon in your team to switch.", alert=True)
            return
        
        text = "Select the first Pokémon to switch:\n\n"
        for i, key in enumerate(team, start=1):
            poke = pokedata.find_one({"_id": key}) or {}
            text += f"{i}. {poke.get('name', 'Unknown')} ({poke.get('pokemon_id', '?')})\n"
        
        buttons = []
        row = []
        for i, key in enumerate(team, start=1):
            row.append(Button.inline(str(i), f"team:switch1:{i-1}".encode()))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        buttons.append([Button.inline("⬅️ Back", "team:back")])
        await event.edit(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"team:switch1:(.*)"))
    async def team_switch_pick_second_event(event):
        first_index = int(event.pattern_match.group(1))
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        team = user.get("team", [])
        
        first_poke = pokedata.find_one({"_id": team[first_index]}) or {}
        first_name = first_poke.get("name", "Unknown")
        
        text = f"Select the second Pokémon to swap with first chosen ({first_name}):\n\n"
        for i, key in enumerate(team, start=1):
            poke = pokedata.find_one({"_id": key}) or {}
            text += f"{i}. {poke.get('name', 'Unknown')} ({poke.get('pokemon_id', '?')})\n"
        
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
        
        buttons.append([Button.inline("⬅️ Back", "team:back")])
        await event.edit(text, buttons=buttons)

    @bot.on(events.CallbackQuery(pattern=b"team:switch2:(.*)"))
    async def confirm_switch_event(event):
        first_index, second_index = map(int, event.pattern_match.group(1).decode().split(':'))
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        team = user.get("team", [])
        
        if first_index >= len(team) or second_index >= len(team):
            await event.answer("Invalid Pokémon selection.", alert=True)
            return
        
        # Swap positions
        team[first_index], team[second_index] = team[second_index], team[first_index]
        users.update_one({"user_id": user_id}, {"$set": {"team": team}})
        await event.answer("Pokémon switched!")
        
        user = users.find_one({"user_id": user_id})
        await send_team_page(event, user)