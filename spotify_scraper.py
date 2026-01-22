"""
Spotify Liked Songs Scraper
Opens Spotify, waits for login, then scrapes all liked songs to CSV
Uses mouse wheel scrolling at center of screen for smooth scrolling
"""

import csv
import time
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
import pyautogui

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use defaults

# Configuration - loaded from environment variables with defaults
SPOTIFY_URL = os.getenv("SPOTIFY_URL", "https://open.spotify.com/")
LIKED_SONGS_URL = os.getenv("LIKED_SONGS_URL", "https://open.spotify.com/collection/tracks")
LOGIN_WAIT_TIME = int(os.getenv("LOGIN_WAIT_TIME", "120"))  # 2 minutes in seconds
CSV_FILENAME = os.getenv("CSV_FILENAME", "spotify_liked_songs.csv")
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))
SCROLL_PAUSE_TIME = float(os.getenv("SCROLL_PAUSE_TIME", "0.3"))  # Reduced for faster scraping
SCROLL_AMOUNT = int(os.getenv("SCROLL_AMOUNT", "-80"))  # Increased base scroll amount
SCROLL_SPEED_MULTIPLIER = float(os.getenv("SCROLL_SPEED_MULTIPLIER", "1.0"))  # Adjust this to increase speed

# Container XPath
SONG_CONTAINER_XPATH = "/html/body/div[4]/div/div[2]/div[6]/div/div[2]/div[1]/div/main/section/div[4]/div/div/div[2]/div[2]"

# CSS Selectors based on actual Spotify HTML structure
SONG_NAME_CSS = "div.encore-text-body-medium.standalone-ellipsis-one-line"
ARTIST_CSS = "div.encore-text-body-small a[href*='/artist/']"


def setup_driver():
    """Setup and return Chrome WebDriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


def save_to_csv(songs, filename, mode='w'):
    """Save songs to CSV file."""
    file_exists = os.path.exists(filename) and mode == 'a'
    
    with open(filename, mode, newline='', encoding='utf-8') as csvfile:
        fieldnames = ['index', 'song_name', 'artist_name', 'scraped_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        if not file_exists or mode == 'w':
            writer.writeheader()
        
        for song in songs:
            writer.writerow(song)
    
    print(f"Saved {len(songs)} songs to {filename}")


def remove_duplicates_from_csv(filename):
    """Remove duplicate entries from CSV file based on song_name and artist_name."""
    if not os.path.exists(filename):
        return
    
    seen = set()
    unique_songs = []
    
    with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = f"{row['song_name']}|{row['artist_name']}"
            if key not in seen:
                seen.add(key)
                unique_songs.append(row)
    
    # Rewrite with unique entries and updated indices
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['index', 'song_name', 'artist_name', 'scraped_at']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, song in enumerate(unique_songs, 1):
            song['index'] = i
            writer.writerow(song)
    
    print(f"Removed duplicates. {len(unique_songs)} unique songs in CSV.")
    return len(unique_songs)


def move_mouse_to_center():
    """Move mouse cursor to the center of the screen."""
    screen_width, screen_height = pyautogui.size()
    center_x = screen_width // 2
    center_y = screen_height // 2
    pyautogui.moveTo(center_x, center_y)
    return center_x, center_y


def scroll_with_mouse(clicks=-10):
    """Scroll using mouse wheel at current cursor position."""
    pyautogui.scroll(clicks)  # Negative = scroll down


def get_song_rows(driver):
    """Get all song row elements from the container."""
    try:
        # Wait for the song container to be present
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, SONG_CONTAINER_XPATH))
        )
        
        # Get the container
        container = driver.find_element(By.XPATH, SONG_CONTAINER_XPATH)
        
        # Get all row elements - look for divs with role="row"
        song_rows = container.find_elements(By.CSS_SELECTOR, "div[role='row']")
        
        if not song_rows:
            # Fallback: get direct child divs of the tracklist
            song_rows = container.find_elements(By.CSS_SELECTOR, "div[data-testid='tracklist-row']")
        
        if not song_rows:
            # Another fallback: get all divs that contain song elements
            song_rows = container.find_elements(By.XPATH, ".//div[.//div[contains(@class, 'encore-text-body-medium')]]")
        
        return song_rows
    except Exception as e:
        print(f"Error finding song container: {e}")
        return []


def extract_song_info(row, index):
    """Extract song name and artist from a track row element using CSS selectors."""
    try:
        song_name = ""
        artist_name = ""
        
        # Get song name - div with classes encore-text-body-medium and standalone-ellipsis-one-line
        try:
            song_element = row.find_element(By.CSS_SELECTOR, SONG_NAME_CSS)
            song_name = song_element.text.strip()
        except NoSuchElementException:
            # Fallback: try just the medium text class
            try:
                song_element = row.find_element(By.CSS_SELECTOR, "div.encore-text-body-medium")
                song_name = song_element.text.strip()
            except:
                pass
        
        # Get artist name - anchor tag with href containing /artist/
        try:
            artist_elements = row.find_elements(By.CSS_SELECTOR, ARTIST_CSS)
            if artist_elements:
                artist_names = [a.text.strip() for a in artist_elements if a.text.strip()]
                artist_name = ", ".join(artist_names)
        except NoSuchElementException:
            # Fallback
            try:
                artist_elements = row.find_elements(By.CSS_SELECTOR, "a[href*='/artist/']")
                if artist_elements:
                    artist_names = [a.text.strip() for a in artist_elements if a.text.strip()]
                    artist_name = ", ".join(artist_names)
            except:
                pass
        
        if song_name:
            return {
                'index': index,
                'song_name': song_name,
                'artist_name': artist_name,
                'scraped_at': datetime.now().isoformat()
            }
    except StaleElementReferenceException:
        pass
    except Exception as e:
        pass
    
    return None


def scroll_and_scrape(driver):
    """Scroll through the page and scrape all songs, saving in batches."""
    all_songs = []
    seen_songs = set()
    batch = []
    batch_number = 0
    no_new_songs_count = 0
    max_no_new_attempts = 15
    
    print("Starting to scrape songs...")
    print(f"Scroll speed: {abs(SCROLL_AMOUNT)} clicks every {SCROLL_PAUSE_TIME}s")
    
    # Move mouse to center of screen for scrolling
    center_x, center_y = move_mouse_to_center()
    print(f"Mouse positioned at center: ({center_x}, {center_y})")
    
    # Initial wait for content
    time.sleep(1)
    
    while True:
        # Get current song elements
        rows = get_song_rows(driver)
        new_songs_found = 0
        
        if not rows:
            print("No song rows found. Trying to scroll...")
            move_mouse_to_center()
            scroll_with_mouse(SCROLL_AMOUNT)
            time.sleep(SCROLL_PAUSE_TIME)
            no_new_songs_count += 1
            if no_new_songs_count >= max_no_new_attempts:
                print("Could not find any songs after multiple attempts.")
                break
            continue
        
        for row in rows:
            song_info = extract_song_info(row, len(all_songs) + 1)
            
            if song_info:
                # Create unique key for deduplication
                song_key = f"{song_info['song_name']}|{song_info['artist_name']}"
                
                if song_key not in seen_songs:
                    seen_songs.add(song_key)
                    song_info['index'] = len(all_songs) + 1
                    all_songs.append(song_info)
                    batch.append(song_info)
                    new_songs_found += 1
                    
                    print(f"[{len(all_songs)}] {song_info['song_name']} - {song_info['artist_name']}")
                    
                    # Save batch when it reaches BATCH_SIZE
                    if len(batch) >= BATCH_SIZE:
                        batch_number += 1
                        mode = 'w' if batch_number == 1 else 'a'
                        save_to_csv(batch, CSV_FILENAME, mode)
                        print(f"--- Batch {batch_number} saved ({len(all_songs)} total songs) ---")
                        batch = []
        
        # Scroll down using mouse wheel at center - FAST
        move_mouse_to_center()
        scroll_with_mouse(int(SCROLL_AMOUNT * SCROLL_SPEED_MULTIPLIER))
        time.sleep(SCROLL_PAUSE_TIME)
        
        # Check if we found new songs
        if new_songs_found == 0:
            no_new_songs_count += 1
            if no_new_songs_count >= max_no_new_attempts:
                print("Reached end of list (no new songs found)")
                break
        else:
            no_new_songs_count = 0
    
    # Save any remaining songs in the batch
    if batch:
        batch_number += 1
        mode = 'w' if batch_number == 1 else 'a'
        save_to_csv(batch, CSV_FILENAME, mode)
        print(f"--- Final batch saved ({len(all_songs)} total songs) ---")
    
    return all_songs


def main():
    """Main function to run the Spotify scraper."""
    print("=" * 60)
    print("Spotify Liked Songs Scraper")
    print("=" * 60)
    
    # Disable pyautogui fail-safe for uninterrupted scrolling
    pyautogui.FAILSAFE = False
    
    # Setup driver
    print("\nLaunching browser...")
    driver = setup_driver()
    
    try:
        # Open Spotify
        print(f"Opening {SPOTIFY_URL}")
        driver.get(SPOTIFY_URL)
        
        # Wait for user to login
        print(f"\n{'='*60}")
        print("Please log in to your Spotify account.")
        print(f"You have {LOGIN_WAIT_TIME // 60} minutes to complete login.")
        print(f"{'='*60}\n")
        
        # Countdown timer
        for remaining in range(LOGIN_WAIT_TIME, 0, -10):
            mins, secs = divmod(remaining, 60)
            print(f"Time remaining: {mins:02d}:{secs:02d}", end='\r')
            time.sleep(10)
        
        print("\nLogin wait time complete. Proceeding...")
        
        # Navigate to liked songs
        print(f"\nNavigating to Liked Songs: {LIKED_SONGS_URL}")
        driver.get(LIKED_SONGS_URL)
        
        # Wait for page to fully load
        print("Waiting for page to load...")
        time.sleep(5)
        
        # Click on the page to ensure focus
        try:
            body = driver.find_element(By.TAG_NAME, "body")
            body.click()
        except:
            pass
        
        # Start scrolling and scraping
        songs = scroll_and_scrape(driver)
        
        # Remove duplicates from CSV
        print("\nRemoving duplicates from CSV...")
        unique_count = remove_duplicates_from_csv(CSV_FILENAME)
        
        print(f"\n{'='*60}")
        print(f"Scraping complete!")
        print(f"Total unique songs: {unique_count}")
        print(f"Saved to: {os.path.abspath(CSV_FILENAME)}")
        print(f"{'='*60}")
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        print("Removing duplicates from CSV...")
        remove_duplicates_from_csv(CSV_FILENAME)
        print(f"Songs scraped so far have been saved to {CSV_FILENAME}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            input("\nPress Enter to close the browser...")
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    main()
