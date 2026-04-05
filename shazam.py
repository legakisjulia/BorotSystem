"""
integrations/shazam.py
──────────────────────
Records 8 seconds of audio from the microphone, sends it to ShazamIO,
and returns (title, artist) or (None, None) on failure.
"""

import asyncio
import os
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
from shazamio import Shazam

SAMPLE_RATE   = 44_100
RECORD_SECS   = 8
TEMP_WAV_PATH = "/tmp/boro_shazam.wav"


async def _identify_async() -> tuple[str | None, str | None]:
    print(f"[Shazam] Recording {RECORD_SECS}s …")
    audio = sd.rec(
        int(RECORD_SECS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=2,
        dtype="int16",
    )
    sd.wait()
    wav_write(TEMP_WAV_PATH, SAMPLE_RATE, audio)

    shazam = Shazam()
    try:
        result = await shazam.recognize_song(TEMP_WAV_PATH)
        track  = result.get("track", {})
        title  = track.get("title")
        artist = track.get("subtitle")
        if title and artist:
            print(f"[Shazam] Identified: {title} – {artist}")
            return title, artist
        print("[Shazam] Could not identify song.")
        return None, None
    except Exception as exc:
        print(f"[Shazam] Error: {exc}")
        return None, None
    finally:
        if os.path.exists(TEMP_WAV_PATH):
            os.remove(TEMP_WAV_PATH)


def identify() -> tuple[str | None, str | None]:
    """Synchronous wrapper — call this from the main loop."""
    return asyncio.run(_identify_async())
