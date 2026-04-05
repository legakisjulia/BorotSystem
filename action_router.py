"""
action_router.py
────────────────
Takes a parsed intent dict and executes the corresponding action.
Each action either:
  • plays a sound (fire-and-forget for simple confirmations), or
  • speaks a response (for questions / calendar reads).

All external API calls are wrapped in try/except so a failure always
triggers an error sound rather than crashing the main loop.
"""

import re
import subprocess
from audio_player import play_sound, speak
from intent_parser import (
    ACTION_IDENTIFY_SONG,
    ACTION_PLAY_SONG,
    ACTION_PLAY_PLAYLIST,
    ACTION_STOP_MUSIC,
    ACTION_ASK_GPT,
    ACTION_READ_CALENDAR,
    ACTION_WRITE_CALENDAR,
    ACTION_ADD_REMINDER,
    ACTION_SOUND_RESPONSE,
    ACTION_EXIT,
    ACTION_UNKNOWN,
)

# ── Sound constants ────────────────────────────────────────────────────────────
SND_DONE    = "yes.wav"
SND_ERROR   = "oh no.wav"
SND_WAIT    = "chitter chatter.wav"   # played while Boro thinks / records
SND_CONFUSED = "confused.wav"


# ── Reminder (macOS only) ─────────────────────────────────────────────────────

def _add_to_reminders(text: str, list_name: str = "Reminders") -> bool:
    applescript = f'''
    tell application "Reminders"
        tell list "{list_name}"
            make new reminder with properties {{name:"{text}"}}
        end tell
    end tell
    '''
    try:
        subprocess.run(["osascript", "-e", applescript], check=True)
        return True
    except Exception as exc:
        print(f"[Reminders] Error: {exc}")
        return False


# ── Parse calendar write payload ──────────────────────────────────────────────

def _split_calendar_payload(payload: str) -> tuple[str, str]:
    """
    Split 'team meeting on friday' → ('team meeting', 'friday').
    Falls back to (payload, 'today') if no date keyword is found.
    """
    # Try "on <date>" pattern
    match = re.search(r"\bon\s+(.+)$", payload, re.IGNORECASE)
    if match:
        date_str  = match.group(1).strip()
        title_str = payload[: match.start()].strip()
        return title_str, date_str
    # Try "for <date>"
    match = re.search(r"\bfor\s+(.+)$", payload, re.IGNORECASE)
    if match:
        date_str  = match.group(1).strip()
        title_str = payload[: match.start()].strip()
        return title_str, date_str
    return payload, "today"


# ── Main router ───────────────────────────────────────────────────────────────

def route(intent: dict) -> bool:
    """
    Execute the action for the given intent.
    Returns False if the user said 'exit', True otherwise.
    """
    action  = intent["action"]
    payload = intent["payload"]

    # ── Personality sounds (original Boro behavior) ────────────────────────
    if action == ACTION_SOUND_RESPONSE:
        play_sound(payload)
        return True

    # ── Exit ───────────────────────────────────────────────────────────────
    if action == ACTION_EXIT:
        play_sound("borobye.wav", wait=True)
        return False

    # ── Unknown ────────────────────────────────────────────────────────────
    if action == ACTION_UNKNOWN:
        play_sound(SND_CONFUSED)
        return True

    # ── Shazam → Spotify like ──────────────────────────────────────────────
    if action == ACTION_IDENTIFY_SONG:
        play_sound(SND_WAIT)
        from integrations import shazam, spotify
        title, artist = shazam.identify()
        if title and artist:
            ok = spotify.like_song(title, artist)
            play_sound(SND_DONE if ok else SND_ERROR)
        else:
            play_sound(SND_ERROR)
        return True

    # ── Spotify play song ──────────────────────────────────────────────────
    if action == ACTION_PLAY_SONG:
        from integrations import spotify
        ok = spotify.play_song(payload)
        play_sound(SND_DONE if ok else SND_ERROR)
        return True

    # ── Spotify play playlist ──────────────────────────────────────────────
    if action == ACTION_PLAY_PLAYLIST:
        from integrations import spotify
        ok = spotify.play_playlist(payload)
        play_sound(SND_DONE if ok else SND_ERROR)
        return True

    # ── Spotify stop ───────────────────────────────────────────────────────
    if action == ACTION_STOP_MUSIC:
        from integrations import spotify
        ok = spotify.stop()
        play_sound(SND_DONE if ok else SND_ERROR)
        return True

    # ── ChatGPT question ───────────────────────────────────────────────────
    if action == ACTION_ASK_GPT:
        play_sound(SND_WAIT)
        from integrations import chatgpt
        answer = chatgpt.ask(payload)
        if answer:
            speak(answer)
        else:
            play_sound(SND_ERROR)
        return True

    # ── Calendar read ──────────────────────────────────────────────────────
    if action == ACTION_READ_CALENDAR:
        play_sound(SND_WAIT)
        from integrations import calendar
        events = calendar.read_today()
        if not events:
            speak("You have nothing on your calendar today.")
        else:
            speak("Here's what you have today. " + ". ".join(events))
        return True

    # ── Calendar write ─────────────────────────────────────────────────────
    if action == ACTION_WRITE_CALENDAR:
        title, date_str = _split_calendar_payload(payload)
        if not title:
            play_sound(SND_ERROR)
            return True
        from integrations import calendar
        ok = calendar.write_event(title, date_str)
        play_sound(SND_DONE if ok else SND_ERROR)
        return True

    # ── macOS Reminders ────────────────────────────────────────────────────
    if action == ACTION_ADD_REMINDER:
        ok = _add_to_reminders(payload)
        play_sound(SND_DONE if ok else SND_ERROR)
        return True

    # Shouldn't reach here
    play_sound(SND_CONFUSED)
    return True
