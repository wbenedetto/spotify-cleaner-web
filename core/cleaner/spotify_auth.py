import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import uuid

def get_spotify_oauth():
    temp_cache = f"/tmp/spotify_cache_{uuid.uuid4()}"
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
        scope="playlist-read-private playlist-modify-private playlist-modify-public",
        show_dialog=True,
        cache_path=temp_cache
    )
