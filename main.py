"""
main.py  —  Boro Voice Assistant
─────────────────────────────────
Entry point. Runs an infinite loop:
  1. listen for speech (blocks until silence)
  2. parse the transcript into an intent
  3. route the intent to the correct action
  4. repeat (or exit on "quit" / "goodbye boro")

Usage:
    python main.py
"""

import sys
import os
from dotenv import load_dotenv

# Load .env before importing anything that reads env vars
load_dotenv()

# Ensure project root is on the path so relative imports work
sys.path.insert(0, os.path.dirname(__file__))

from speech_input  import listen
from intent_parser import parse
from action_router import route
from audio_player  import play_sound


def main() -> None:
    print("=" * 50)
    print("  Boro is awake. Say something!")
    print("  (Say 'quit' or 'goodbye Boro' to exit)")
    print("=" * 50)

    play_sound("borohello.wav")

    while True:
        text = listen()
        if not text:
            continue

        intent = parse(text)
        print(f"[Intent] action={intent['action']}  payload='{intent['payload']}'")

        keep_running = route(intent)
        if not keep_running:
            print("Boro: Goodbye! 👋")
            break


if __name__ == "__main__":
    main()
