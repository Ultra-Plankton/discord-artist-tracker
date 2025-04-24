import os
import json
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from keep_alive import keep_alive  # comment this out on Railway

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())

spotify = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

artist_file = "tracked_artists.json"

# Load artist list from file
def load_artists():
    if not os.path.exists(artist_file):
        with open(artist_file, 'w') as f:
            json.dump({}, f)
    with open(artist_file, 'r') as f:
        return json.load(f)

def save_artists(data):
    with open(artist_file, 'w') as f:
        json.dump(data, f, indent=2)

artist_latest = {}
tracked_artists = load_artists()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_releases.start()

@tasks.loop(minutes=60)
async def check_releases():
    channel = bot.get_channel(CHANNEL_ID)
    for name, artist_id in tracked_artists.items():
        try:
            results = spotify.artist_albums(artist_id, album_type="album,single", limit=1)
            latest = results['items'][0]
            album_name = latest['name']
            album_url = latest['external_urls']['spotify']

            if artist_latest.get(artist_id) != album_name:
                artist_latest[artist_id] = album_name
                await channel.send(f"🎶 **{name}** released something new: [{album_name}]({album_url})")
        except Exception as e:
            print(f"Error checking {name}: {e}")

@bot.command()
async def track(ctx, *, artist_name):
    results = spotify.search(q=f"artist:{artist_name}", type='artist')
    if results['artists']['items']:
        artist = results['artists']['items'][0]
        tracked_artists[artist['name']] = artist['id']
        save_artists(tracked_artists)
        await ctx.send(f"✅ Now tracking **{artist['name']}**.")
    else:
        await ctx.send("❌ Artist not found.")

@bot.command()
async def untrack(ctx, *, artist_name):
    if artist_name in tracked_artists:
        del tracked_artists[artist_name]
        save_artists(tracked_artists)
        await ctx.send(f"🛑 Stopped tracking **{artist_name}**.")
    else:
        await ctx.send("❌ Artist not currently tracked.")

@bot.command()
async def list_artists(ctx):
    if tracked_artists:
        artist_list = '\n'.join(f"• {a}" for a in tracked_artists.keys())
        await ctx.send(f"🎧 Currently tracking:\n{artist_list}")
    else:
        await ctx.send("No artists are currently being tracked.")

keep_alive()  # Comment out if deploying on Railway
bot.run(TOKEN)
