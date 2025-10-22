from telethon import events, Button
from collections import Counter
from database import users, pokedata
from pokemon_utils import parse_showdown_set
from config import SHOWDOWN_LINK, POKEMON_PER_PAGE

# Global state for awaiting pokemon
awaiting_pokemon = set()
active_summaries = {}

def register_pokemon_handlers(bot):
    
    @bot.on(events.NewMessage(pattern="/add"))
    async def add_pokemon(event):
        user_id = event.sender_id
        
        try:
            existing = users.find_one({"user_id": user_id})
            if not existing:
                await event.reply("User profile not found!")
                return
            
            awaiting_pokemon.add(user_id)
            await event.respond(
                "Please paste the meta data of your Pokémon (only next message will be taken!):",
                buttons=[Button.url("Open Teambuilder", SHOWDOWN_LINK)]
            )
        except Exception as e:
            print(f"Error in add_pokemon: {e}")
            await event.respond("❌ An error occurred. Please try again later.")

    @bot.on(events.NewMessage)
    async def handle_pokemon_set(event):
        user_id = event.sender_id
        text = event.raw_text
        
        if user_id in awaiting_pokemon and any(k in text for k in ["Ability:", "EVs:", "Nature:", "- "]):
            try:
                pokemon = parse_showdown_set(text)
                pokemon_key = f"{pokemon.get('name', 'Unknown')}-{pokemon['pokemon_id']}"
                
                users.update_one(
                    {"user_id": user_id},
                    {"$push": {"pokemon": pokemon_key}},
                    upsert=True
                )
                pokedata.update_one(
                    {"_id": pokemon_key},
                    {"$set": pokemon},
                    upsert=True
                )
                
                awaiting_pokemon.remove(user_id)
                
                # Build response message
                msg = f"✅ Pokémon Saved!\n"
                msg += f"🆔 ID: {pokemon['pokemon_id']}\n"
                msg += f"📛 Name: {pokemon['name']} ({pokemon['gender']})\n"
                msg += f"🎒 Item: {pokemon['item']}\n"
                msg += f"📊 Level: {pokemon.get('level', 100)}\n"
                msg += f"✨ Shiny: {pokemon.get('shiny', 'No')}\n"
                msg += f"🌟 Ability: {pokemon.get('ability', 'None')}\n"
                msg += f"🔮 Tera Type: {pokemon.get('tera_type', 'None')}\n"
                msg += f"🧬 Nature: {pokemon.get('nature', 'Hardy')}\n"
                msg += f"⚔️ Moves: {', '.join(pokemon.get('moves', []))}\n"
                
                # Display calculated stats
                stats = pokemon.get("stats", {})
                if stats:
                    msg += f"\n📈 Calculated Stats:\n"
                    msg += f"HP: {stats.get('hp', '?')} | ATK: {stats.get('atk', '?')} | DEF: {stats.get('def', '?')}\n"
                    msg += f"SPA: {stats.get('spa', '?')} | SPD: {stats.get('spd', '?')} | SPE: {stats.get('spe', '?')}\n"
                    evs = pokemon["ev_stats"]
                    ivs = pokemon["iv_stats"]
                    msg += "📊 EVs: " + ", ".join(f"{k.upper()}={evs[f'ev_{k}']}" for k in ['hp','atk','def','spa','spd','spe']) + "\n"
                    msg += "🔢 IVs: " + ", ".join(f"{k.upper()}={ivs[f'iv_{k}']}" for k in ['hp','atk','def','spa','spd','spe'])
                
                await event.respond(msg)
            except Exception as e:
                print(f"Error in handle_pokemon_set: {e}")
                awaiting_pokemon.discard(user_id)  # Remove from awaiting set
                await event.respond("❌ An error occurred while processing your Pokémon data. Please try again.")

    @bot.on(events.NewMessage(pattern="/pokemon"))
    async def pokemon_list_handler(event):
        user_id = event.sender_id
        user = users.find_one({"user_id": user_id})
        
        if not user or not user.get("pokemon"):
            await event.respond("You don't have any Pokémon yet.")
            return
        
        pokemon_ids = user["pokemon"]
        pokes = pokedata.find({"_id": {"$in": pokemon_ids}})
        names = [poke["name"] for poke in pokes]
        counts = Counter(names)
        
        await send_pokemon_page(event, counts, 0)

    async def send_pokemon_page(event, counts, page):
        per_page = 25
        pokemon_list = [f"{name} ({count})" if count > 1 else name for name, count in counts.items()]
        total_pages = (len(pokemon_list) - 1) // per_page + 1
        
        start = page * per_page
        end = start + per_page
        page_items = pokemon_list[start:end]
        
        text = f"Your Pokémon (Page {page+1}/{total_pages}):\n"
        text += "\n".join(page_items) if page_items else "No Pokémon on this page."
        
        buttons = []
        if page > 0:
            buttons.append(Button.inline("◀️ Prev", data=f"pokemon:page:{page-1}"))
        if page < total_pages - 1:
            buttons.append(Button.inline("Next ▶️", data=f"pokemon:page:{page+1}"))
        
        await event.respond(text, buttons=buttons if buttons else None)

    @bot.on(events.CallbackQuery(pattern=b"pokemon:page:(.*)"))
    async def callback_pokemon_page(event):
        page = int(event.pattern_match.group(1))
        user_id = event.sender_id
        
        user = users.find_one({"user_id": user_id})
        if not user or not user.get("pokemon"):
            await event.answer("No Pokémon found.", alert=True)
            return
        
        pokemon_ids = user["pokemon"]
        pokes = pokedata.find({"_id": {"$in": pokemon_ids}})
        names = [poke["name"] for poke in pokes]
        counts = Counter(names)
        
        await event.edit("Loading...", buttons=None)
        await send_pokemon_page(event, counts, page)

    @bot.on(events.NewMessage(pattern=r"/summary (.+)"))
    async def summary_handler(event):
        query = event.pattern_match.group(1).strip().lower()
        user_id = event.sender_id
        
        user = users.find_one({"user_id": user_id})
        if not user or "pokemon" not in user or not user["pokemon"]:
            await event.reply("You don't have any Pokémon.")
            return
        
        matches = []
        for poke_id in user["pokemon"]:
            poke = pokedata.find_one({"_id": poke_id}) or {}
            if not poke:
                continue
            
            name_lower = poke.get("name", "").lower()
            poke_id_lower = poke.get("pokemon_id", "").lower()
            
            if (query == name_lower or query == poke_id_lower or query in name_lower):
                matches.append((poke_id, poke))
        
        if not matches:
            await event.reply("No Pokémon found.")
            return
        
        active_summaries[user_id] = matches
        if len(matches) == 1:
            await send_summary(event, matches[0][1])
        else:
            await send_summary_list(event, matches, 0)

    async def send_summary_list(event, matches, page=0):
        total_pages = (len(matches) - 1) // POKEMON_PER_PAGE + 1
        start = page * POKEMON_PER_PAGE
        end = start + POKEMON_PER_PAGE
        page_items = matches[start:end]
        
        text = f"Multiple Pokémon found (Page {page+1}/{total_pages}):\n"
        for i, (_, poke) in enumerate(page_items, start+1):
            text += f"{i}. {poke.get('name', 'Unknown')} ({poke.get('pokemon_id', '?')})\n"
        
        buttons = []
        row = []
        for i, (poke_id, poke) in enumerate(page_items, start=start):
            row.append(Button.inline(str(i % POKEMON_PER_PAGE + 1), f"summary:show:{poke_id}".encode()))
            if len(row) == 5:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        nav = []
        if page > 0:
            nav.append(Button.inline("◀️ Prev", f"summary:page:{page-1}".encode()))
        if page < total_pages - 1:
            nav.append(Button.inline("Next ▶️", f"summary:page:{page+1}".encode()))
        if nav:
            buttons.append(nav)
        
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(text, buttons=buttons)
        else:
            await event.reply(text, buttons=buttons)

    async def send_summary(event, poke):
        stats = poke.get("stats", {})
        text = f"🔍 **Pokémon Summary** ({poke.get('pokemon_id', '?')})\n\n"
        text += f"📛 **Name:** {poke.get('name', 'Unknown')}\n"
        text += f"⚥ **Gender:** {poke.get('gender', '?')}\n"
        text += f"📊 **Level:** {poke.get('level', '?')}\n"
        text += f"🌟 **Ability:** {poke.get('ability', 'None')}\n"
        text += f"🔮 **Tera Type:** {poke.get('tera_type', 'None')}\n"
        text += f"🎒 **Item:** {poke.get('item', 'None')}\n"
        text += f"🧬 **Nature:** {poke.get('nature', 'Hardy')}\n"
        
        if stats:
            text += f"\n📈 **Final Stats:**\n"
            text += f"HP: {stats.get('hp', '?')} | ATK: {stats.get('atk', '?')} | DEF: {stats.get('def', '?')}\n"
            text += f"SPA: {stats.get('spa', '?')} | SPD: {stats.get('spd', '?')} | SPE: {stats.get('spe', '?')}\n"
        
        text += f"\n🔥 **EVs:** HP:{poke.get('ev_hp', 0)} Atk:{poke.get('ev_atk', 0)} Def:{poke.get('ev_def', 0)} SpA:{poke.get('ev_spa', 0)} SpD:{poke.get('ev_spd', 0)} Spe:{poke.get('ev_spe', 0)}\n"
        text += f"💎 **IVs:** HP:{poke.get('iv_hp', 31)} Atk:{poke.get('iv_atk', 31)} Def:{poke.get('iv_def', 31)} SpA:{poke.get('iv_spa', 31)} SpD:{poke.get('iv_spd', 31)} Spe:{poke.get('iv_spe', 31)}\n"
        text += f"\n⚔️ **Moves:** {', '.join(poke.get('moves', []))} " if poke.get('moves') else "None"
        
        if isinstance(event, events.CallbackQuery.Event):
            await event.edit(text)
        else:
            await event.reply(text)

    @bot.on(events.CallbackQuery(pattern=b"summary:page:(.*)"))
    async def summary_page_event(event):
        page = int(event.pattern_match.group(1))
        user_id = event.sender_id
        matches = active_summaries.get(user_id)
        if not matches:
            await event.answer("No active summary search.", alert=True)
            return
        await send_summary_list(event, matches, page)

    @bot.on(events.CallbackQuery(pattern=b"summary:show:(.*)"))
    async def summary_show_event(event):
        poke_id = event.pattern_match.group(1).decode()
        poke = pokedata.find_one({"_id": poke_id})
        if not poke:
            await event.answer("Pokémon not found.", alert=True)
            return
        await send_summary(event, poke)
