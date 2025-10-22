import asyncio
import os
import signal
import sys
import time
from telethon import TelegramClient, events
from config import API_ID, API_HASH, BOT_TOKEN
from handlers.user_handlers import register_user_handlers
from handlers.pokemon_handlers import register_pokemon_handlers
from handlers.team_handlers import register_team_handlers
from handlers.battle_handlers import register_battle_handlers

# Try to import psutil, but don't fail if it's not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️ psutil not available, using basic session cleanup")

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
    """Clean up any locked session files with multiple strategies"""
    session_file = "bot.session"
    session_files = [session_file, f"{session_file}-journal", f"{session_file}-wal", f"{session_file}-shm"]
    
    # Strategy 1: Check for running processes that might be using the file (if psutil available)
    if PSUTIL_AVAILABLE:
        try:
            for proc in psutil.process_iter(['pid', 'name', 'open_files']):
                try:
                    if proc.info['open_files']:
                        for file_info in proc.info['open_files']:
                            if session_file in file_info.path:
                                print(f"⚠️ Found process {proc.info['name']} (PID: {proc.info['pid']}) using session file")
                                # Don't kill the process, just note it
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
        except Exception as e:
            print(f"⚠️ Could not check running processes: {e}")
    
    # Strategy 2: Force remove session files with retries
    for file_path in session_files:
        if os.path.exists(file_path):
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    os.remove(file_path)
                    print(f"🗑️ Removed {file_path}")
                    break
                except PermissionError:
                    if attempt < max_retries - 1:
                        print(f"⚠️ Permission denied, retrying in 1 second... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(1)
                    else:
                        print(f"❌ Could not remove {file_path} after {max_retries} attempts")
                except OSError as e:
                    print(f"⚠️ Could not remove {file_path}: {e}")
                    break

def create_fresh_session():
    """Create a completely fresh session with unique name"""
    timestamp = int(time.time())
    session_name = f"bot_session_{timestamp}"
    print(f"🔄 Creating fresh session: {session_name}")
    return TelegramClient(session_name, API_ID, API_HASH)

def create_memory_session():
    """Create an in-memory session to avoid file locking issues"""
    print("🔄 Creating in-memory session to avoid file locking...")
    return TelegramClient(None, API_ID, API_HASH)  # None creates in-memory session

async def start_bot():
    """Start the bot with proper error handling"""
    global bot
    
    try:
        # Clean up any existing session files
        cleanup_session()
        
        # Try to start with existing session first
        try:
            await bot.start(bot_token=BOT_TOKEN)
            print("✅ Bot started successfully with existing session!")
        except Exception as e:
            print(f"⚠️ Failed to start with existing session: {e}")
            print("🔄 Attempting to create fresh session...")
            
            # Create a completely fresh session
            bot = create_fresh_session()
            try:
                await bot.start(bot_token=BOT_TOKEN)
                print("✅ Bot started successfully with fresh session!")
            except Exception as e2:
                print(f"⚠️ Failed to start with fresh session: {e2}")
                print("🔄 Attempting to create in-memory session...")
                
                # Final fallback: in-memory session
                bot = create_memory_session()
                await bot.start(bot_token=BOT_TOKEN)
                print("✅ Bot started successfully with in-memory session!")
        
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
