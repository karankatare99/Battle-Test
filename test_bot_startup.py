#!/usr/bin/env python3
"""
test_bot_startup.py - Test script to verify bot can start without critical errors
"""

import asyncio
import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from config import API_ID, API_HASH, BOT_TOKEN, OWNER_ID
        print("✅ Config imports successful")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from database import mongo_client, db
        print("✅ Database imports successful")
    except Exception as e:
        print(f"❌ Database import failed: {e}")
        return False
    
    try:
        from pokemon_utils import kanto_data, moves_data
        print("✅ Pokemon utils imports successful")
    except Exception as e:
        print(f"❌ Pokemon utils import failed: {e}")
        return False
    
    try:
        from handlers.user_handlers import register_user_handlers
        from handlers.pokemon_handlers import register_pokemon_handlers
        from handlers.team_handlers import register_team_handlers
        from handlers.battle_handlers import register_battle_handlers
        print("✅ Handler imports successful")
    except Exception as e:
        print(f"❌ Handler imports failed: {e}")
        return False
    
    return True

def test_session_cleanup():
    """Test session cleanup functionality"""
    print("Testing session cleanup...")
    
    try:
        from bot import cleanup_session, create_fresh_session, create_memory_session
        print("✅ Session functions imported successfully")
        
        # Test cleanup (should not fail even if no files exist)
        cleanup_session()
        print("✅ Session cleanup executed successfully")
        
        # Test session creation (don't actually create, just test function exists)
        print("✅ Session creation functions available")
        
        return True
    except Exception as e:
        print(f"❌ Session cleanup test failed: {e}")
        return False

async def test_bot_initialization():
    """Test bot initialization without actually starting"""
    print("Testing bot initialization...")
    
    try:
        from telethon import TelegramClient
        from config import API_ID, API_HASH
        
        # Test creating client (don't start it)
        client = TelegramClient("test_session", API_ID, API_HASH)
        print("✅ Bot client creation successful")
        
        # Test in-memory session
        memory_client = TelegramClient(None, API_ID, API_HASH)
        print("✅ In-memory session creation successful")
        
        return True
    except Exception as e:
        print(f"❌ Bot initialization test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running bot startup tests...\n")
    
    tests = [
        ("Import Test", test_imports),
        ("Session Cleanup Test", test_session_cleanup),
        ("Bot Initialization Test", lambda: asyncio.run(test_bot_initialization()))
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Bot should start successfully.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
