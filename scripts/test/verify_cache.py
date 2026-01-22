
import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

# Mock environment variables if needed
os.environ['TAIPEI_TZ'] = 'Asia/Taipei'

# Import app but avoid running it
from app import load_data_cache, DATA_STORE, DATA_CACHE_FILE

def verify_cache_loading():
    print(f"Checking {DATA_CACHE_FILE}...")
    if not os.path.exists(DATA_CACHE_FILE):
        print("Error: data_cache.json not found!")
        return

    # Load cache directly to see what keys to expect
    with open(DATA_CACHE_FILE, 'r') as f:
        raw_cache = json.load(f)
    
    users_in_cache = list(raw_cache.get('users', {}).keys())
    print(f"Users found in file: {users_in_cache}")
    
    if not users_in_cache:
        print("No users found in cache file. Cannot verify.")
        return

    # Run the function under test
    print("Running load_data_cache()...")
    load_data_cache()
    
    # Check if DATA_STORE has the user keys
    print("\nVerifying DATA_STORE content...")
    success = True
    for user_id in users_in_cache:
        if user_id in DATA_STORE:
            print(f"✅ User {user_id} found in DATA_STORE")
            
            # Check if topics are loaded
            topics = DATA_STORE[user_id].get('topics', {})
            print(f"   - Topics count: {len(topics)}")
            if len(topics) == 0:
                print(f"   ⚠️ Warning: No topics loaded for user {user_id}")
                
        else:
            print(f"❌ User {user_id} NOT found in DATA_STORE")
            success = False
            
    if success:
        print("\n✅ Verification SUCCESS: All users loaded correctly.")
    else:
        print("\n❌ Verification FAILED: Some users missing from memory.")

if __name__ == "__main__":
    verify_cache_loading()
