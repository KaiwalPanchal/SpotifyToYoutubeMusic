import os
import json
from ytmusicapi import YTMusic

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use defaults

AUTH_FILE = os.getenv("AUTH_FILE", "headers_auth.json")

def check_account():
    if not os.path.exists(AUTH_FILE):
        print(f"Error: {AUTH_FILE} not found. Please run youtube_music_uploader.py first to authenticate.")
        return

    try:
        print(f"Loading credentials from {AUTH_FILE}...")
        ytmusic = YTMusic(AUTH_FILE)
        
        # We can't get the email directly, but we can get the channel name
        # by looking at library playlists or other metadata.
        print("Fetching account information...")
        
        # Get library contents to see whose account this is
        # Liked Music is usually the first place to look
        playlists = ytmusic.get_library_playlists(limit=5)
        
        # Try to find the channel identity via a search mock or history
        # History is a good way to see recent activity and confirm it's the right account
        try:
            history = ytmusic.get_history()
            if history:
                print("\nSuccess! This account is active.")
                print(f"Most recent song in history: {history[0]['title']} by {history[0]['artists'][0]['name']}")
        except:
            pass

        # Another way: get library songs count
        songs = ytmusic.get_library_songs(limit=1)
        print(f"\nConnection confirmed.")
        print("-" * 40)
        print("To confirm the identity, check your YouTube Music 'Library' -> 'Playlists'.")
        print("The songs are being added to the 'Liked Music' list of the account currently active in the headers.")
        print("-" * 40)
        
    except Exception as e:
        print(f"Error connecting to YouTube Music: {e}")
        print("Your authentication might have expired. Try deleting headers_auth.json and running the uploader again.")

if __name__ == "__main__":
    check_account()
