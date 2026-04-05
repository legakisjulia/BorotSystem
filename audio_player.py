"""
audio_player.py
───────────────
Central audio utility for Boro.
  • play_sound(filename)  → plays a .wav from SOUNDS_DIR (non-blocking)
  • speak(text)           → converts text to speech and reads it aloud
"""

import os
import time
import pygame
import pyttsx3
from dotenv import load_dotenv

load_dotenv()

SOUNDS_DIR = os.getenv("SOUNDS_DIR", "sounds")

# ── pygame mixer ───────────────────────────────────────────────────────────────
pygame.mixer.init()

# ── pyttsx3 TTS engine ─────────────────────────────────────────────────────────
_tts = pyttsx3.init()
_tts.setProperty("rate", 165)   # words per minute (adjust to taste)
_tts.setProperty("volume", 1.0)


def play_sound(filename: str, wait: bool = False) -> None:
    """
    Play a .wav file from SOUNDS_DIR.
    If wait=True, blocks until the sound finishes.
    """
    path = os.path.join(SOUNDS_DIR, filename)
    if not os.path.exists(path):
        print(f"[Audio] Missing sound file: {path}")
        return
    try:
        sound = pygame.mixer.Sound(path)
        sound.play()
        if wait:
            while pygame.mixer.get_busy():
                time.sleep(0.05)
    except Exception as exc:
        print(f"[Audio] Could not play {filename}: {exc}")


def speak(text: str) -> None:
    """Convert text to speech and block until done."""
    print(f"[Boro speaks] {text}")
    _tts.say(text)
    _tts.runAndWait()
