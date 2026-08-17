# Jarvis — Personal AI Assistant
### by Skyra-Tech

A locally-running, voice-enabled, Telegram-integrated AI assistant powered by Google Gemini Pro.

---

## 🚀 Quick Start (3 Steps)

### Step 1 — Install Python
Download Python 3.11+ from [python.org](https://python.org)
> ⚠️ Check **"Add Python to PATH"** during installation!

### Step 2 — Run Installer
Double-click **`install.bat`**
- Creates virtual environment
- Installs all dependencies
- Opens `.env` for you to fill in API keys

### Step 3 — Fill Your API Keys in `.env`
```
GEMINI_API_KEY         = Get from aistudio.google.com
TELEGRAM_BOT_TOKEN     = Get from @BotFather on Telegram
TELEGRAM_ADMIN_CHAT_ID = Get from @userinfobot on Telegram
```

### Step 4 — Start Jarvis
Double-click **`run.bat`**

---

## 🎤 How to Use

### Voice (Laptop Microphone)
1. Jarvis starts listening automatically
2. **Speak** — Jarvis detects your voice
3. Pause for 1.5 seconds → Jarvis processes
4. Jarvis **speaks back** to you

### Telegram (Your Phone, Anywhere)
1. Open your Telegram bot
2. Send **/start** to begin
3. Type any message → Jarvis replies
4. Send a **voice note** → Jarvis transcribes + replies

### Telegram Commands
| Command | What it does |
|---|---|
| `/start` | Welcome message |
| `/help` | Show all commands |
| `/clear` | Clear conversation memory |
| `/status` | Show system stats |
| `/mute` | Stop laptop voice output |
| `/unmute` | Resume laptop voice output |

---

## 📁 Project Structure

```
jarvis/
├── main.py                    ← Entry point (run this)
├── config.py                  ← All settings from .env
├── core/
│   ├── brain.py               ← Gemini AI (the intelligence)
│   ├── voice_listener.py      ← Microphone + Whisper STT
│   └── speaker.py             ← Edge TTS voice output
├── integrations/
│   └── telegram_bot.py        ← Telegram bot
├── requirements.txt           ← Python dependencies
├── install.bat                ← One-click installer
├── run.bat                    ← One-click launcher
├── .env                       ← Your API keys (create from .env.example)
└── .env.example               ← Template
```

---

## ⚙️ Run Options

```bash
# Full mode (voice + Telegram)
python main.py

# Telegram only (no microphone)
python main.py --no-voice

# Voice only (no Telegram)
python main.py --no-telegram

# List available microphones
python main.py --list-mics
```

---

## 🔧 Troubleshooting

### "No module named sounddevice"
```bash
pip install sounddevice
```

### "No module named faster_whisper"
```bash
pip install faster-whisper
```

### Microphone not detected
```bash
python main.py --list-mics
```
This shows all available microphones. Your laptop mic should be in the list.

### Whisper model downloading
First run downloads the Whisper model (~75MB for `tiny`).
This only happens once. After that it's cached locally.

### Voice sensitivity too low/high
Edit `.env`:
```
SILENCE_THRESHOLD=500   # Higher = less sensitive (raise if background noise)
                        # Lower = more sensitive (lower if Jarvis doesn't hear you)
```

---

## 🌐 Getting API Keys

### Gemini API Key (Free)
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **"Get API Key"**
3. Click **"Create API key"**
4. Copy and paste into `.env`

### Telegram Bot Token (Free)
1. Open Telegram → search **@BotFather**
2. Send `/newbot`
3. Name: `Skyra Jarvis` | Username: `SkyraJarvisBot`
4. Copy the token into `.env`

### Your Telegram Chat ID (Free)
1. Open Telegram → search **@userinfobot**
2. Send `/start`
3. It shows your ID number → copy into `.env`

---

## 🛣️ Coming Next (Roadmap)

- [ ] **Google Calendar** — "What's on my schedule today?"
- [ ] **Gmail** — "Summarize my unread emails"
- [ ] **GitHub** — "Create an issue in SkyraChat repo"
- [ ] **App Control** — "Open Antigravity IDE"
- [ ] **Screen Vision** — Jarvis sees your screen
- [ ] **Wake Word** — "Hey Jarvis" (always listening)
- [ ] **Google Sheets** — "Add today's expense"
