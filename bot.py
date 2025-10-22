import asyncio
import os
import signal
import sys
from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN
from handlers.user_handlers import register_user_handlers
from handlers.pokemon_handlers import register_pokemon_handlers
from handlers.team_handlers import register_team_handlers
from handlers.battle_handlers import register_battle_handlers

# Initialize bot with proper session handling
bot = TelegramClient("bot", API_ID, API_HASH)

# DEBUG: catch all callback queries to see what data arrives
@bot.on(events.CallbackQuery)
async def debug_callback(event):
    # Print the raw callback data to console
    print("🔔 Callback received:", event.data)
    # Acknowledge so the spinner stops
    await event.answer()

def cleanup_session():
    """Clean up any locked session files"""
    session_file = "bot.session"
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
            print("🗑️ Removed existing session file")
        except OSError as e:
            print(f"⚠️ Could not remove session file: {e}")

async def start_bot():
    """Start the bot with proper error handling"""
    try:
        # Clean up any existing session files
        cleanup_session()
        
        # Start the bot
        await bot.start(bot_token=BOT_TOKEN)
        print("✅ Bot started successfully!")
        
        # Register all handlers
        register_user_handlers(bot)
        register_pokemon_handlers(bot)
        register_team_handlers(bot)
        register_battle_handlers(bot)
        
        print("✅ All handlers registered successfully!")
        print("🤖 Bot is running...")
        
        # Run until disconnected
        await bot.run_until_disconnected()
        
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        return False
    finally:
        # Clean shutdown
        await cleanup_bot()
    
    return True

async def cleanup_bot():
    """Clean shutdown of the bot"""
    try:
        if bot.is_connected():
            await bot.disconnect()
        print("✅ Bot disconnected cleanly")
    except Exception as e:
        print(f"⚠️ Error during bot cleanup: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    asyncio.create_task(cleanup_bot())
    sys.exit(0)

def main():
    """Main function to start the bot"""
    print("Starting Pokémon Showdown Bot...")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run the bot
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        print("👋 Bot shutdown complete")

if __name__ == "__main__":
    main()
