"""
YouTube Music Uploader
Reads songs from a CSV and adds them to your YouTube Music Liked Songs.
Uses ytmusicapi with browser-based authentication.

SETUP:
1. Run this script
2. Follow the instructions to paste your browser headers
3. The script will then start adding songs
"""

import csv
import time
import os
import json
import hashlib

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use defaults

# ============================================================
# CONFIGURATION - loaded from environment variables with defaults
# ============================================================
CSV_FILENAME = os.getenv("CSV_FILENAME", "spotify_liked_songs.csv")
AUTH_FILE = os.getenv("AUTH_FILE", "headers_auth.json")
DELAY_BETWEEN_SONGS = float(os.getenv("DELAY_BETWEEN_SONGS", "0.5"))  # Seconds to wait between API calls
START_INDEX = int(os.getenv("START_INDEX", "1"))  # Start from this index (1-indexed, matches CSV)


def generate_sapisid_hash(sapisid, origin="https://music.youtube.com"):
    """Generate the authorization hash from SAPISID cookie."""
    import time
    timestamp = str(int(time.time()))
    hash_input = f"{timestamp} {sapisid} {origin}"
    hash_value = hashlib.sha1(hash_input.encode()).hexdigest()
    return f"SAPISIDHASH {timestamp}_{hash_value}"


def extract_sapisid_from_cookie(cookie_string):
    """Extract SAPISID from cookie string."""
    for part in cookie_string.split(';'):
        part = part.strip()
        if part.startswith('SAPISID='):
            return part.split('=', 1)[1]
    return None


def setup_browser_auth():
    """
    Setup browser-based authentication.
    This requires copying headers from a browser request to YouTube Music.
    """
    print("\n" + "=" * 60)
    print("Browser Authentication Setup")
    print("=" * 60)
    print("""
To authenticate, follow these steps:

1. Open YouTube Music in your browser: https://music.youtube.com
2. Make sure you're logged in
3. Open Developer Tools (F12 or right-click > Inspect)
4. Go to the "Network" tab
5. Refresh the page
6. Click on any request to music.youtube.com (look for "browserId" or similar)
7. In "Request Headers", find and copy:
   - The "cookie" value
   
Then paste it below when prompted.
""")
    
    print("Press Enter when you're ready to paste your cookie...")
    input()
    
    print("Paste your full cookie value and press Enter:")
    cookie = input().strip()
    
    if not cookie:
        print("No cookie provided. Exiting.")
        return None
    
    # Extract SAPISID for authorization
    sapisid = extract_sapisid_from_cookie(cookie)
    if not sapisid:
        print("Warning: Could not extract SAPISID from cookie. Authentication may fail.")
    
    # Create headers in the format ytmusicapi expects
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "cookie": cookie,
        "origin": "https://music.youtube.com",
        "x-goog-authuser": "0",
        "x-origin": "https://music.youtube.com"
    }
    
    # Add authorization if we have SAPISID
    if sapisid:
        headers["authorization"] = generate_sapisid_hash(sapisid)
    
    with open(AUTH_FILE, 'w') as f:
        json.dump(headers, f, indent=2)
    
    print(f"\n✓ Authentication saved to {AUTH_FILE}")
    return headers


def load_ytmusic():
    """Load YTMusic with header-based authentication."""
    # Import here to catch any import errors
    from ytmusicapi import YTMusic
    
    if not os.path.exists(AUTH_FILE):
        print(f"Authentication file not found: {AUTH_FILE}")
        headers = setup_browser_auth()
        if not headers:
            return None
    
    try:
        print(f"Loading authentication from {AUTH_FILE}...")
        
        # Load headers and update authorization hash (it's time-based)
        with open(AUTH_FILE, 'r') as f:
            headers = json.load(f)
        
        sapisid = extract_sapisid_from_cookie(headers.get('cookie', ''))
        if sapisid:
            headers["authorization"] = generate_sapisid_hash(sapisid)
            with open(AUTH_FILE, 'w') as f:
                json.dump(headers, f, indent=2)
        
        ytmusic = YTMusic(AUTH_FILE)
        
        # Test the connection
        print("Testing connection...")
        ytmusic.get_library_songs(limit=1)
        print(f"✓ Connected successfully!")
        return ytmusic
    except Exception as e:
        print(f"Error: {e}")
        print("\nAuthentication may be expired or invalid. Let's set up again.")
        if os.path.exists(AUTH_FILE):
            os.remove(AUTH_FILE)
        headers = setup_browser_auth()
        if headers:
            try:
                from ytmusicapi import YTMusic
                return YTMusic(AUTH_FILE)
            except Exception as e2:
                print(f"Still failing: {e2}")
                return None
        return None


def load_songs_from_csv(filename):
    """Load songs from CSV file."""
    songs = []
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            songs.append({
                'index': int(row['index']),
                'song_name': row['song_name'],
                'artist_name': row['artist_name']
            })
    return songs


def search_and_like_song(ytmusic, song_name, artist_name):
    """
    Search for a song on YouTube Music and add it to Liked Songs.
    Returns: (success: bool, video_id: str or None, message: str)
    """
    try:
        # Build search query
        query = f"{song_name} {artist_name}"
        
        # Search for the song
        results = ytmusic.search(query, filter="songs", limit=5)
        
        if not results:
            return False, None, "No results found"
        
        # Get the first (best) result
        best_match = results[0]
        video_id = best_match.get('videoId')
        
        if not video_id:
            return False, None, "No video ID in result"
        
        # Like the song (adds to Liked Songs)
        ytmusic.rate_song(video_id, 'LIKE')
        
        result_title = best_match.get('title', 'Unknown')
        artists = best_match.get('artists', [{}])
        result_artist = artists[0].get('name', 'Unknown') if artists else 'Unknown'
        
        return True, video_id, f"Matched: {result_title} - {result_artist}"
    
    except Exception as e:
        return False, None, f"Error: {str(e)}"


def main():
    """Main function to upload songs to YouTube Music."""
    print("=" * 60)
    print("YouTube Music Uploader")
    print("=" * 60)
    
    # Initialize YouTube Music API
    ytmusic = load_ytmusic()
    if ytmusic is None:
        print("Failed to initialize YouTube Music API.")
        return
    
    # Load songs from CSV
    print(f"\nLoading songs from {CSV_FILENAME}...")
    songs = load_songs_from_csv(CSV_FILENAME)
    total_songs = len(songs)
    print(f"Found {total_songs} songs in CSV.")
    
    # Filter songs based on START_INDEX
    songs_to_process = [s for s in songs if s['index'] >= START_INDEX]
    print(f"Processing {len(songs_to_process)} songs (starting from index {START_INDEX})...")
    
    input("\nPress Enter to start adding songs to your YouTube Music library...")
    
    # Track progress
    success_count = 0
    failed_songs = []
    
    print("\n" + "-" * 60)
    
    for song in songs_to_process:
        idx = song['index']
        name = song['song_name']
        artist = song['artist_name']
        
        print(f"[{idx}/{total_songs}] {name} - {artist}")
        
        success, video_id, message = search_and_like_song(ytmusic, name, artist)
        
        if success:
            print(f"    ✓ {message}")
            success_count += 1
        else:
            print(f"    ✗ {message}")
            failed_songs.append({
                'index': idx,
                'song_name': name,
                'artist_name': artist,
                'reason': message
            })
        
        # Rate limiting delay
        time.sleep(DELAY_BETWEEN_SONGS)
    
    # Summary
    print("\n" + "=" * 60)
    print("Upload Complete!")
    print(f"Successfully added: {success_count}/{len(songs_to_process)}")
    print(f"Failed: {len(failed_songs)}")
    
    # Save failed songs to a file
    if failed_songs:
        failed_filename = "failed_songs.csv"
        with open(failed_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['index', 'song_name', 'artist_name', 'reason'])
            writer.writeheader()
            writer.writerows(failed_songs)
        print(f"Failed songs saved to: {failed_filename}")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
