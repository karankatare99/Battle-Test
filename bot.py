import asyncio
from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN
from handlers.user_handlers import register_user_handlers
from handlers.pokemon_handlers import register_pokemon_handlers
from handlers.team_handlers import register_team_handlers
from handlers.battle_handlers import register_battle_handlers

# Initialize bot
bot = TelegramClient("bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# DEBUG: catch all callback queries to see what data arrives
@bot.on(events.CallbackQuery)
async def debug_callback(event):
    # Print the raw callback data to console
    print("🔔 Callback received:", event.data)
    # Acknowledge so the spinner stops
    await event.answer()

def main():
    """Main function to start the bot"""
    print("Starting Pokémon Showdown Bot...")
    
    # Register all handlers
    register_user_handlers(bot)
    register_pokemon_handlers(bot)
    register_team_handlers(bot)
    register_battle_handlers(bot)
    
    print("✅ All handlers registered successfully!")
    print("🤖 Bot is running...")
    
    # Run bot
    bot.run_until_disconnected()

if __name__ == "__main__":
    main()
