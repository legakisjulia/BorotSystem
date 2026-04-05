"""
speech_input.py
───────────────
Records from the microphone and returns transcribed text only after the
user has stopped speaking (silence-detection via SpeechRecognition's
built-in listen(), which dynamically adjusts for ambient noise).
"""

import speech_recognition as sr

recognizer = sr.Recognizer()

# How long a pause counts as "done speaking" (seconds).
# Increase if Boro cuts you off; decrease for snappier response.
PAUSE_THRESHOLD = 1.0
# How long to wait before giving up if no speech starts (seconds).
PHRASE_TIME_LIMIT = 15


def listen() -> str:
    """
    Block until the user speaks, then return the lowercased transcript.
    Returns an empty string on failure.
    """
    recognizer.pause_threshold = PAUSE_THRESHOLD

    with sr.Microphone() as source:
        print("\n[Boro] Listening…")
        recognizer.adjust_for_ambient_noise(source, duration=0.4)
        try:
            audio = recognizer.listen(
                source,
                phrase_time_limit=PHRASE_TIME_LIMIT,
            )
        except sr.WaitTimeoutError:
            print("[Boro] No speech detected.")
            return ""

    try:
        text = recognizer.recognize_google(audio).lower().strip()
        print(f"[You] {text}")
        return text
    except sr.UnknownValueError:
        print("[Boro] Couldn't understand that.")
        return ""
    except sr.RequestError as exc:
        print(f"[Boro] Speech API error: {exc}")
        return ""
