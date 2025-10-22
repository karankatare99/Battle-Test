from telethon import events, Button
from database import users, auth
from config import OWNER_ID

def register_user_handlers(bot):
    
    @bot.on(events.NewMessage(pattern="/start"))
    async def start_handler(event):
        user_id = event.sender_id
        first_name = event.sender.first_name
        
        try:
            # Check authorization
            authorised = auth.find_one({"user_id": user_id})
            if not authorised and user_id != OWNER_ID:
                await event.respond("You are not authorised to use this bot.")
                return
            
            # Check if user exists
            existing = users.find_one({"user_id": user_id})
            if not existing:
                users.insert_one({
                    "user_id": user_id,
                    "name": first_name,
                    "pokemon": [],
                    "team": []
                })
                await event.respond(f"👋 Welcome {first_name}! Your profile has been created.")
            else:
                await event.respond(f"✅ Welcome back {first_name}, you already have a profile.")
        except Exception as e:
            print(f"Error in start_handler: {e}")
            await event.respond("❌ An error occurred. Please try again later.")

    @bot.on(events.NewMessage(pattern="/reset"))
    async def reset_handler(event):
        user_id = event.sender_id
        try:
            users.update_one({"user_id": user_id}, {"$set": {"pokemon": [], "team": []}})
            await event.respond("🗑️All your Pokémon data has been reset.")
        except Exception as e:
            print(f"Error in reset_handler: {e}")
            await event.respond("❌ An error occurred while resetting your data.")

    @bot.on(events.NewMessage(pattern="/authorise"))
    async def authorise_handler(event):
        user_id = event.sender_id
        
        try:
            if not event.is_reply:
                await event.respond("Please reply to a user's message with /authorise.")
                return
            
            reply_msg = await event.get_reply_message()
            target_id = reply_msg.sender_id
            target = await bot.get_entity(target_id)
            
            if user_id != OWNER_ID:
                await event.reply("You are not the Owner!")
                return
            
            existing = auth.find_one({"user_id": target_id})
            if existing:
                await event.respond(f"{target.first_name} is already authorised.")
            else:
                auth.insert_one({"user_id": target_id, "name": target.first_name})
                await event.respond(f"{target.first_name} has been authorised!")
        except Exception as e:
            print(f"Error in authorise_handler: {e}")
            await event.respond("❌ An error occurred while authorising the user.")

    @bot.on(events.NewMessage(pattern="/authlist"))
    async def authlist_handler(event):
        try:
            authorised_users = list(auth.find())
            if not authorised_users:
                await event.respond("No authorised users yet.")
                return
            
            msg = "Authorised Users:\n"
            for u in authorised_users:
                msg += f"- {u['name']} ({u['user_id']})\n"
            await event.respond(msg)
        except Exception as e:
            print(f"Error in authlist_handler: {e}")
            await event.respond("❌ An error occurred while fetching the auth list.")

    @bot.on(events.NewMessage(pattern="/serverreset"))
    async def server_reset_handler(event):
        user_id = event.sender_id
        if user_id != OWNER_ID:
            await event.respond("You are not authorised to use this command.")
            return
        
        try:
            users.delete_many({})
            auth.delete_many({})
            from database import pokedata, battles_db, matchmaking
            pokedata.delete_many({})
            battles_db.delete_many({})
            matchmaking.delete_many({})
            await event.respond("All data wiped from the server!")
        except Exception as e:
            print(f"Error in server_reset_handler: {e}")
            await event.respond("❌ An error occurred while resetting the server.")