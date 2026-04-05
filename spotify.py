"""
integrations/spotify.py
───────────────────────
Wraps spotipy for Boro.
  • play_song(query)      → search for track and play it
  • play_playlist(query)  → search for playlist and play it
  • stop()                → pause playback
  • like_song(title, artist) → add a song to Liked Songs by search
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

load_dotenv()

SCOPE = (
    "user-library-modify,"
    "user-read-playback-state,"
    "user-modify-playback-state,"
    "user-read-currently-playing"
)

_sp: spotipy.Spotify | None = None


def _client() -> spotipy.Spotify:
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8888/callback"),
                scope=SCOPE,
            )
        )
    return _sp


def play_song(query: str) -> bool:
    """Search for a track and start playback. Returns True on success."""
    try:
        sp = _client()
        results = sp.search(q=query, type="track", limit=1)
        items = results["tracks"]["items"]
        if not items:
            print(f"[Spotify] No track found for: {query}")
            return False
        track = items[0]
        print(f"[Spotify] Playing: {track['name']} – {track['artists'][0]['name']}")
        sp.start_playback(uris=[track["uri"]])
        return True
    except Exception as exc:
        print(f"[Spotify] play_song error: {exc}")
        return False


def play_playlist(query: str) -> bool:
    """Search for a playlist and start playback. Returns True on success."""
    try:
        sp = _client()
        results = sp.search(q=query, type="playlist", limit=1)
        items = results["playlists"]["items"]
        if not items:
            print(f"[Spotify] No playlist found for: {query}")
            return False
        pl = items[0]
        print(f"[Spotify] Playing playlist: {pl['name']}")
        sp.start_playback(context_uri=pl["uri"])
        return True
    except Exception as exc:
        print(f"[Spotify] play_playlist error: {exc}")
        return False


def stop() -> bool:
    """Pause playback. Returns True on success."""
    try:
        _client().pause_playback()
        return True
    except Exception as exc:
        print(f"[Spotify] stop error: {exc}")
        return False


def like_song(title: str, artist: str) -> bool:
    """Search for a song and add it to the user's Liked Songs."""
    try:
        sp = _client()
        results = sp.search(q=f"{title} {artist}", type="track", limit=1)
        items = results["tracks"]["items"]
        if not items:
            print(f"[Spotify] Like: could not find '{title}' by '{artist}'")
            return False
        song_id = items[0]["id"]
        sp.current_user_saved_tracks_add([song_id])
        print(f"[Spotify] Liked: {title} by {artist}")
        return True
    except Exception as exc:
        print(f"[Spotify] like_song error: {exc}")
        return False
