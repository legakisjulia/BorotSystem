"""
intent_parser.py
────────────────
Converts a raw transcript string into a structured intent dict:

    {
        "action":  <str>,   # one of the ACTION_* constants below
        "payload": <str>,   # the part of the sentence relevant to the action
        "raw":     <str>,   # original transcript
    }

Matching order:
  1. Exact / substring match against keyword patterns (fast, zero-cost).
  2. Fuzzy match via rapidfuzz as a fallback with a tunable threshold.
  3. Predefined conversational responses (keeps existing Boro sounds alive).
"""

import re
import random
from rapidfuzz import fuzz

# ── Action constants ───────────────────────────────────────────────────────────
ACTION_IDENTIFY_SONG   = "identify_song"
ACTION_PLAY_SONG       = "play_song"
ACTION_PLAY_PLAYLIST   = "play_playlist"
ACTION_STOP_MUSIC      = "stop_music"
ACTION_ASK_GPT         = "ask_gpt"
ACTION_READ_CALENDAR   = "read_calendar"
ACTION_WRITE_CALENDAR  = "write_calendar"
ACTION_ADD_REMINDER    = "add_reminder"
ACTION_SOUND_RESPONSE  = "sound_response"   # existing Boro personality sounds
ACTION_EXIT            = "exit"
ACTION_UNKNOWN         = "unknown"

FUZZY_THRESHOLD = 72  # 0-100; lower = more lenient

# ── Keyword patterns ───────────────────────────────────────────────────────────
# Each entry: (list-of-trigger-substrings, action)
# First match wins, so put more-specific patterns first.
_KEYWORD_RULES = [
    # Shazam
    (["what song is this", "what is this song", "identify song", "name this song"], ACTION_IDENTIFY_SONG),
    # Calendar read
    (["what is on my calendar", "what's on my calendar", "my schedule", "today's events", "what do i have today"], ACTION_READ_CALENDAR),
    # Calendar write — must come before generic "add … reminder" so "add … calendar" wins
    (["add to my calendar", "add .* to my calendar", "put .* on my calendar", "schedule .* on", "add .* on my calendar"], ACTION_WRITE_CALENDAR),
    # Reminders
    (["add .* to my reminders", "remind me", "add reminder"], ACTION_ADD_REMINDER),
    # Spotify playlist
    (["play playlist", "start playlist", "queue playlist"], ACTION_PLAY_PLAYLIST),
    # Spotify stop
    (["stop music", "pause music", "stop playing", "pause song"], ACTION_STOP_MUSIC),
    # Spotify play (generic — comes after playlist so "play playlist" matches above first)
    (["play ", "play song", "start song", "play track"], ACTION_PLAY_SONG),
    # ChatGPT question triggers
    (["what is ", "what are ", "who is ", "who are ", "google ", "search for ", "tell me about ", "explain "], ACTION_ASK_GPT),
    # Exit
    (["exit", "quit", "goodbye boro", "shut down"], ACTION_EXIT),
]

# ── Fuzzy fallback rules ───────────────────────────────────────────────────────
_FUZZY_RULES = [
    (["what song is this", "identify this song"],                             ACTION_IDENTIFY_SONG),
    (["what is on my calendar", "read my schedule"],                          ACTION_READ_CALENDAR),
    (["add to my calendar", "put on calendar"],                               ACTION_WRITE_CALENDAR),
    (["remind me", "add reminder"],                                           ACTION_ADD_REMINDER),
    (["play playlist", "start playlist"],                                     ACTION_PLAY_PLAYLIST),
    (["stop music", "pause music"],                                           ACTION_STOP_MUSIC),
    (["play music", "play song"],                                             ACTION_PLAY_SONG),
    (["what is", "who is", "google", "search for"],                          ACTION_ASK_GPT),
    (["exit", "quit", "goodbye"],                                             ACTION_EXIT),
]

# ── Existing Boro conversational sound map (preserved from original) ────────────
SOUND_RESPONSES: dict[str, list[str]] = {
    "yes.wav":              ["feeling good today", "its hot out", "go get coffee", "go for coffee", "need some fresh air", "running late again", "beautiful day out", "time for a walk", "busy morning ahead", "sounds better today"],
    "no.wav":               ["should i do this", "was that the plan", "anyone would notice", "did that actually work", "make sense"],
    "sigh.wav":             ["aren't i so smart", "its been a long day", "can't wake up today"],
    "oh no.wav":            ["fall over", "can you believe that", "total disaster", "that's gonna hurt", "not again", "a mess"],
    "thank you.wav":        ["i'll be back", "you did so good", "that was awesome", "you crushed it", "nice job today", "you're amazing", "that was perfect", "love your energy", "love the energy", "good job", "well done", "yay"],
    "i agree.wav":          ["why don't you say hello boro", "thats ok", "you're so silly", "don't you think", "do you think"],
    "hmph.wav":             ["you aren't moving fast enough", "you aren't really getting it", "can't focus right now", "can you be quieter", "can you stop beeping", "why are you being sassy", "i do not sound crazy"],
    "uh oh.wav":            ["lets take on the day", "let get this bread", "i've got this", "lets do this", "making me sad"],
    "wow.wav":              ["isn't this so cool", "so cool", "omg", "are you excited", "this is so exciting"],
    "borohello.wav":        ["hello", "hi", "hey", "greetings", "sup", "good morning", "good afternoon"],
    "borobye.wav":          ["bye", "goodbye", "good night", "goodnight", "see you", "good evening"],
    "scream.wav":           ["following you", "evil", "scream"],
    "groan.wav":            ["fed up", "good greif", "exhausting", "rough day", "not this again", "that bad huh", "here we go again", "tell me about it"],
    "chitter chatter.wav":  ["feeling ok", "that's what she said", "im serious", "mad about it"],
    "sassy.wav":            ["don't you have something better to do", "stop that", "trouble", "ridiculous", "don't have enough time", "making me mad", "making me angry", "don't even think about it", "leave it alone", "don't you dare"],
    "ha.wav":               ["ha", "he he", "hehe", "lol", "lmao", "hee"],
}

MULTI_SOUND_RESPONSES: dict[str, list[str]] = {
    "how are you":   ["sigh.wav", "yes.wav"],
    "do you like this": ["no.wav", "yes.wav"],
    "is that right": ["sigh.wav", "yes.wav"],
    "do you understand": ["hmph.wav", "sigh.wav"],
    "ahh":           ["oh no.wav", "scream.wav"],
}

FALLBACK_SOUNDS = ["confused.wav"]


def _extract_payload(text: str, action: str) -> str:
    """Strip the command verb from the text to get the meaningful payload."""
    removals = {
        ACTION_PLAY_SONG:      r"^(play|start|queue|play song|play track)\s*",
        ACTION_PLAY_PLAYLIST:  r"^(play playlist|start playlist|queue playlist)\s*",
        ACTION_ASK_GPT:        r"^(what is|what are|who is|who are|google|search for|tell me about|explain)\s*",
        ACTION_WRITE_CALENDAR: r"^(add|put|schedule)\s*|(\s*(to|on) (my )?calendar.*$)",
        ACTION_ADD_REMINDER:   r"^(add|remind me|add reminder)\s*|(\s*(to|in) (my )?reminders.*$)",
    }
    pattern = removals.get(action)
    if pattern:
        return re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
    return text


def _check_sound_responses(text: str) -> dict | None:
    """Return a sound-response intent if the text matches any predefined phrase."""
    # Multi-responses first
    for phrase, sounds in MULTI_SOUND_RESPONSES.items():
        if phrase in text:
            return {"action": ACTION_SOUND_RESPONSE, "payload": random.choice(sounds), "raw": text}
    # Single responses
    for sound_file, phrases in SOUND_RESPONSES.items():
        for phrase in phrases:
            if phrase in text:
                return {"action": ACTION_SOUND_RESPONSE, "payload": sound_file, "raw": text}
    return None


def parse(text: str) -> dict:
    """Main entry-point. Returns an intent dict."""
    if not text:
        return {"action": ACTION_UNKNOWN, "payload": "", "raw": text}

    # 1. Predefined sound responses (highest priority for personality)
    sound_intent = _check_sound_responses(text)
    if sound_intent:
        return sound_intent

    # 2. Exact / substring keyword match
    for triggers, action in _KEYWORD_RULES:
        for trigger in triggers:
            # Support simple regex patterns (e.g. "add .* to my calendar")
            if re.search(trigger, text, re.IGNORECASE):
                return {
                    "action":  action,
                    "payload": _extract_payload(text, action),
                    "raw":     text,
                }

    # 3. Fuzzy fallback
    best_score  = 0
    best_action = ACTION_UNKNOWN
    for phrases, action in _FUZZY_RULES:
        for phrase in phrases:
            score = fuzz.partial_ratio(text, phrase)
            if score > best_score:
                best_score  = score
                best_action = action

    if best_score >= FUZZY_THRESHOLD:
        return {
            "action":  best_action,
            "payload": _extract_payload(text, best_action),
            "raw":     text,
        }

    return {"action": ACTION_UNKNOWN, "payload": text, "raw": text}
