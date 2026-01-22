# 🎵 Spotify to YouTube Music Migration Tool

Transfer your liked songs from Spotify to YouTube Music automatically. This tool scrapes your Spotify liked songs and adds them to your YouTube Music library.

## ✨ Features

- **Spotify Scraper**: Automatically extracts all your liked songs from Spotify
- **YouTube Music Uploader**: Searches and adds songs to your YouTube Music "Liked Music" playlist
- **Account Verification**: Check which YouTube account is being used before uploading
- **Resume Support**: Start from any index if the process is interrupted
- **Failed Songs Log**: Tracks songs that couldn't be found for manual review
- **Environment Configuration**: All settings configurable via `.env` file

---

## 📋 Prerequisites

- **Python 3.8+**
- **Google Chrome** (for Selenium-based Spotify scraping)
- **ChromeDriver** (automatically managed by Selenium 4.6+)

---

## 🚀 Quick Start

### 1. Clone or Download the Repository

```bash
cd "C:\Users\YourUsername\Documents\Python Scripts"
git clone <repository-url> SpotifyToYoutubeMusic
cd SpotifyToYoutubeMusic
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment (Optional)

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env with your preferred settings (optional - defaults work fine)
```

---

## 📖 Usage Guide

### Step 1: Scrape Your Spotify Liked Songs

```bash
python spotify_scraper.py
```

**What happens:**

1. A Chrome browser window opens to Spotify
2. You have **2 minutes** to log in to your Spotify account
3. After login, the script navigates to your Liked Songs
4. Songs are scraped and saved to `spotify_liked_songs.csv` in batches of 10
5. Duplicates are automatically removed at the end

**Tips:**
- Don't move your mouse during scraping (the script uses mouse-wheel scrolling)
- If interrupted, just run again - it will pick up where it left off
- The CSV is updated in real-time, so no progress is lost

---

### Step 2: Verify Your YouTube Music Account

Before uploading, confirm you're using the correct YouTube account:

```bash
python check_account.py
```

This will show the most recent song from your YouTube Music history to help you identify the account.

---

### Step 3: Upload Songs to YouTube Music

```bash
python youtube_music_uploader.py
```

**First-time setup:**

1. The script will prompt you to authenticate
2. Open [YouTube Music](https://music.youtube.com) in your browser
3. Make sure you're logged in to the correct account
4. Open Developer Tools (F12) → Network tab
5. Refresh the page
6. Click any request to `music.youtube.com`
7. Copy the **cookie** value from Request Headers
8. Paste it into the terminal when prompted

**What happens:**

1. Reads songs from `spotify_liked_songs.csv`
2. For each song:
   - Searches YouTube Music for a match
   - Adds the song to your "Liked Music" playlist
3. Shows progress in real-time
4. Saves any failed songs to `failed_songs.csv`

---

## ⚙️ Configuration

All settings can be customized in the `.env` file:

### Spotify Scraper Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `SPOTIFY_URL` | `https://open.spotify.com/` | Spotify homepage URL |
| `LIKED_SONGS_URL` | `https://open.spotify.com/collection/tracks` | Liked songs page URL |
| `LOGIN_WAIT_TIME` | `120` | Seconds to wait for login |
| `CSV_FILENAME` | `spotify_liked_songs.csv` | Output CSV filename |
| `BATCH_SIZE` | `10` | Songs to save per batch |
| `SCROLL_PAUSE_TIME` | `0.3` | Pause between scrolls (seconds) |
| `SCROLL_AMOUNT` | `-80` | Scroll pixels per action |
| `SCROLL_SPEED_MULTIPLIER` | `1.0` | Speed multiplier (2.0 = 2x faster) |

### YouTube Music Uploader Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_FILE` | `headers_auth.json` | Authentication file path |
| `DELAY_BETWEEN_SONGS` | `0.5` | Delay between API calls (seconds) |
| `START_INDEX` | `1` | Song index to start from (1-indexed) |

---

## 📁 File Structure

```
SpotifyToYoutubeMusic/
├── spotify_scraper.py       # Scrapes Spotify liked songs
├── youtube_music_uploader.py # Uploads songs to YouTube Music
├── check_account.py         # Verifies YouTube Music account
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration file
├── .env                    # Your configuration (create from .env.example)
├── .gitignore              # Git ignore rules
├── README.md               # This documentation
│
├── spotify_liked_songs.csv # Generated: Your Spotify songs
├── failed_songs.csv        # Generated: Songs that couldn't be found
└── headers_auth.json       # Generated: YouTube Music authentication
```

---

## 🔧 Troubleshooting

### "No results found" for many songs

- Some songs may have different names on YouTube Music
- Check `failed_songs.csv` and manually add them

### Authentication expired

Delete `headers_auth.json` and run the uploader again:

```bash
del headers_auth.json
python youtube_music_uploader.py
```

### Songs not appearing in YouTube Music

1. Check you're logged into the correct account
2. Run `python check_account.py` to verify
3. Refresh the YouTube Music page (they may take a moment to appear)
4. Check "Liked Music" playlist, sorted by "Recently Added"

### Spotify scraper not finding songs

The Spotify web interface changes occasionally. If the scraper stops working:

1. Open Spotify in your browser
2. Right-click on a song → Inspect
3. Update the XPath/CSS selectors in `spotify_scraper.py`

### Rate limiting

If YouTube Music starts rejecting requests:

1. Increase `DELAY_BETWEEN_SONGS` in `.env` (try 1.0 or 2.0)
2. Wait a few minutes and try again

---

## 🔒 Security Notes

- **Never commit** `.env`, `headers_auth.json`, or `oauth.json` to version control
- These files contain your authentication tokens
- The `.gitignore` file is configured to exclude them automatically
- If you accidentally commit secrets, regenerate your tokens immediately

---

## 📊 How It Works

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   Spotify       │     │  spotify_liked_      │     │  youtube_music_     │
│   (Browser)     │────▶│  songs.csv           │────▶│  uploader.py        │
│                 │     │                      │     │                     │
│  - Login        │     │  - Song Name         │     │  - Search YT Music  │
│  - Scrape songs │     │  - Artist Name       │     │  - Match best song  │
└─────────────────┘     └──────────────────────┘     │  - Add to Liked     │
                                                      └─────────────────────┘
                                                               │
                                                               ▼
                                                      ┌─────────────────────┐
                                                      │  YouTube Music      │
                                                      │  "Liked Music"      │
                                                      │  Playlist           │
                                                      └─────────────────────┘
```

---

## 📜 License

This project is for personal use only. Use responsibly and in accordance with Spotify and YouTube Music Terms of Service.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## ❓ FAQ

**Q: Will this download or copy the actual audio files?**

A: No. This tool only transfers your "liked" preferences. It finds matching songs on YouTube Music and adds them to your Liked Music playlist there.

**Q: Is this against Spotify/YouTube Terms of Service?**

A: This tool is for personal use to help migrate your music preferences. It doesn't download content or bypass any paywalls.

**Q: How accurate is the matching?**

A: Very accurate, worked for all songs I had.

**Q: Can I run this for playlists other than Liked Songs?**

A: Currently, only Liked Songs is supported. Playlist support will probably be added in future when I get to take another look at this.
