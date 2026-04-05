# Boro — Voice Assistant

A modular, voice-controlled personal assistant that runs locally and integrates with Spotify, Shazam, ChatGPT, and Google Calendar.

---

## Project Structure

```
boro/
├── main.py               ← Entry point — run this
├── speech_input.py       ← Microphone + speech-to-text (silence-detection)
├── intent_parser.py      ← Classifies what you said into an action
├── action_router.py      ← Executes the action, calls integrations
├── audio_player.py       ← Plays .wav sounds + pyttsx3 TTS
├── integrations/
│   ├── spotify.py        ← Play songs, playlists, like songs
│   ├── shazam.py         ← Identify songs via ShazamIO
│   ├── chatgpt.py        ← Ask GPT-4o-mini a question
│   └── calendar.py       ← Read/write Google Calendar events
├── sounds/               ← Put all your .wav files here
│   ├── borohello.wav
│   ├── yes.wav
│   ├── confused.wav
│   └── … (all your original Boro sounds)
├── .env                  ← Your secrets (copy from .env.example)
├── .env.example          ← Template
└── requirements.txt
```

---

## One-Time Setup

### 1 — Python environment

```bash
cd boro
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

> **macOS note:** `pyaudio` requires PortAudio.
> ```bash
> brew install portaudio
> pip install pyaudio
> ```

### 2 — Copy your sound files

Place all your `.wav` files (yes.wav, no.wav, borohello.wav, etc.) inside a folder called `sounds/` in the project root.

If your sounds live somewhere else, set `SOUNDS_DIR` in `.env`.

### 3 — Create your `.env` file

```bash
cp .env.example .env
```

Then open `.env` and fill in each value (see individual sections below).

---

## API Setup

### Spotify

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) and create an app.
2. Set the **Redirect URI** to `http://localhost:8888/callback` in the app settings.
3. Copy **Client ID** and **Client Secret** into `.env`:

```
SPOTIPY_CLIENT_ID=abc123...
SPOTIPY_CLIENT_SECRET=xyz789...
SPOTIPY_REDIRECT_URI=http://localhost:8888/callback
```

4. First run will open a browser for OAuth. After you approve, a `.cache` file is saved and you won't be asked again.

> **Important:** Spotify's `/start_playback` endpoint requires a **Spotify Premium** account and an **active device** (open Spotify on your phone or desktop first).

---

### OpenAI (ChatGPT)

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys) and create a key.
2. Add to `.env`:

```
OPENAI_API_KEY=sk-...
```

---

### Google Calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project → enable **Google Calendar API**.
3. Create **OAuth 2.0 credentials** (type: Desktop app).
4. Download the JSON file and save it as `credentials.json` in the project root.
5. Add to `.env`:

```
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
```

6. First run of a calendar command opens a browser for OAuth consent. After approving, `token.json` is saved automatically.

---

## Running Boro

```bash
source .venv/bin/activate
python main.py
```

Boro will greet you and start listening. Speak naturally — it waits until you stop talking before responding.

---

## Voice Commands

| What you say | What Boro does |
|---|---|
| `"What song is this"` | Records 8 sec, identifies via Shazam, adds to Liked Songs |
| `"Play Blinding Lights"` | Plays that song on Spotify |
| `"Play playlist chill vibes"` | Plays that playlist on Spotify |
| `"Stop music"` | Pauses Spotify |
| `"What is quantum entanglement"` | Asks ChatGPT, reads 2-sentence answer aloud |
| `"Google the best coffee shops in New Orleans"` | Same — asks ChatGPT |
| `"What is on my calendar for today"` | Reads today's Google Calendar events |
| `"Add team standup to my calendar on friday"` | Creates an all-day event on Friday |
| `"Add dentist appointment to my reminders"` | Adds to macOS Reminders app |
| `"Hello"` / `"Good morning"` | Boro greets you back |
| `"Quit"` / `"Goodbye Boro"` | Shuts down |
| Any of the original personality phrases | Boro plays the matching sound |

---

## Customisation

### Adding new sounds / responses

Open `intent_parser.py` and add entries to `SOUND_RESPONSES` or `MULTI_SOUND_RESPONSES`.

### Changing the silence detection threshold

In `speech_input.py`, adjust:
- `PAUSE_THRESHOLD` — seconds of silence before Boro considers you done (default `1.0`)
- `PHRASE_TIME_LIMIT` — maximum recording length in seconds (default `15`)

### Changing the timezone for Calendar

In `integrations/calendar.py`, set `LOCAL_TZ_NAME` to your [IANA timezone](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones), e.g. `"America/New_York"`.

### Fuzzy matching sensitivity

In `intent_parser.py`, adjust `FUZZY_THRESHOLD` (0–100). Lower = more lenient matching; higher = stricter.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `No Default Input Device` | Check your mic is connected; try `python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"` |
| Spotify `Player command failed: Premium required` | You need Spotify Premium |
| Spotify `No active device` | Open Spotify on your phone/desktop first |
| Calendar `credentials.json not found` | Download OAuth credentials from Google Cloud Console |
| Shazam always fails | Ensure `sounddevice` can access your mic; try increasing `RECORD_SECS` in `shazam.py` |
| `pyaudio` install fails on macOS | `brew install portaudio` first |
