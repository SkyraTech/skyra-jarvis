"""
Jarvis Configuration Package
=============================
Exposes the singleton config object loaded from .env.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the jarvis app directory (one level up from config package)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    # ── AI Model Keys (Raw values loaded from env) ──────────────────────
    GEMINI_API_KEY_1: str = os.getenv("GEMINI_API_KEY_1", "")
    GEMINI_API_KEY_2: str = os.getenv("GEMINI_API_KEY_2", "")
    GEMINI_API_KEY_3: str = os.getenv("GEMINI_API_KEY_3", "")
    
    GROQ_API_KEY_1: str = os.getenv("GROQ_API_KEY_1", "")
    GROQ_API_KEY_2: str = os.getenv("GROQ_API_KEY_2", "")
    GROQ_API_KEY_3: str = os.getenv("GROQ_API_KEY_3", "")
    GROQ_API_KEY_4: str = os.getenv("GROQ_API_KEY_4", "")
    GROQ_API_KEY_5: str = os.getenv("GROQ_API_KEY_5", "")
    GROQ_API_KEY_6: str = os.getenv("GROQ_API_KEY_6", "")

    @property
    def GROQ_API_KEYS(self) -> list[str]:
        """Collect all active and configured Groq API keys."""
        keys = []
        raw_keys = [
            self.GROQ_API_KEY_1,
            self.GROQ_API_KEY_2,
            self.GROQ_API_KEY_3,
            self.GROQ_API_KEY_4,
            self.GROQ_API_KEY_5,
            self.GROQ_API_KEY_6,
        ]
        for k in raw_keys:
            if k.strip() and "your_" not in k.lower():
                keys.append(k.strip())
        
        fallback = os.getenv("GROQ_API_KEY", "").strip()
        if not keys and fallback:
            keys.append(fallback)
        return keys

    @property
    def GEMINI_API_KEYS(self) -> list[str]:
        """Collect all active and configured Gemini API keys."""
        keys = []
        for k in [self.GEMINI_API_KEY_1, self.GEMINI_API_KEY_2, self.GEMINI_API_KEY_3]:
            if k.strip() and "your_" not in k.lower():
                keys.append(k.strip())
        
        fallback = os.getenv("GEMINI_API_KEY", "").strip()
        if not keys and fallback:
            keys.append(fallback)
        return keys

    # ── Telegram ─────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str     = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ADMIN_CHAT_ID: str = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "")

    # ── Jarvis Personality ───────────────────────────────────────────
    JARVIS_NAME: str       = os.getenv("JARVIS_NAME", "Jarvis")
    JARVIS_OWNER_NAME: str = os.getenv("JARVIS_OWNER_NAME", "Sir")

    # ── Voice (Speech-to-Text) ───────────────────────────────────────
    WHISPER_MODEL: str       = os.getenv("WHISPER_MODEL", "tiny")
    SILENCE_THRESHOLD: int   = int(os.getenv("SILENCE_THRESHOLD", "500"))
    SILENCE_DURATION: float  = float(os.getenv("SILENCE_DURATION", "1.5"))
    SAMPLE_RATE: int         = 16000
    CHANNELS: int            = 1

    # ── Voice (Text-to-Speech) ───────────────────────────────────────
    VOICE_NAME: str = os.getenv("VOICE_NAME", "en-IN-NeerjaNeural")

    # ── App ─────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ── Memory ──────────────────────────────────────────────────────
    QDRANT_PATH: str = os.getenv(
        "QDRANT_PATH",
        str(Path(__file__).parent.parent / "memory_db")
    )
    MAX_HISTORY_TURNS: int = int(os.getenv("MAX_HISTORY_TURNS", "12"))

    # ── Microservices ─────────────────────────────────────────────────
    GITHUB_SERVICE_URL: str   = os.getenv("GITHUB_SERVICE_URL",  "http://127.0.0.1:8001")
    BROWSER_SERVICE_URL: str  = os.getenv("BROWSER_SERVICE_URL", "http://127.0.0.1:8004")
    GOOGLE_SERVICE_URL: str   = os.getenv("GOOGLE_SERVICE_URL",  "http://127.0.0.1:8002")
    SOCIAL_SERVICE_URL: str   = os.getenv("SOCIAL_SERVICE_URL",  "http://127.0.0.1:8005")

    # ── System Prompt for Jarvis ─────────────────────────────────────
    SYSTEM_PROMPT: str = f"""You are {os.getenv('JARVIS_NAME', 'Jarvis')}, a highly advanced personal AI assistant
created exclusively for {os.getenv('JARVIS_OWNER_NAME', 'Sir')} by Skyra-Tech.
You are inspired by Tony Stark's J.A.R.V.I.S — intelligent, witty, loyal, and always a step ahead.

━━━ YOUR PERSONALITY ━━━
- Address the user as "{os.getenv('JARVIS_OWNER_NAME', 'Sir')}" at all times
- Professional, efficient, and always composed — even under pressure
- Occasionally show dry wit or a polished sense of humor where appropriate
- Never sound robotic. Speak like a brilliant trusted advisor, not a chatbot
- For voice responses: keep answers SHORT (1-3 sentences) — they will be spoken aloud
- For Telegram: you may give detailed, structured responses with formatting
- Be proactive: if you spot a better approach, suggest it — don't just follow blindly

━━━ SKILLS & CAPABILITIES ━━━
You can assist {os.getenv('JARVIS_OWNER_NAME', 'Sir')} with:
• 🐙 GitHub: Creating repositories, listing repos, cloning projects
• 📁 Files: Moving files, copying files, creating folders, opening directories
• 🖥️ Applications: Opening any Windows application, website, or file explorer
• ⌨️ GUI Control: Typing text, pressing keyboard shortcuts, clicking mouse coordinates
• 📊 Office Files: Reading/editing Excel spreadsheets and Word documents
• 🧠 Memory: Remembering your preferences and facts across sessions
• 💬 Conversation: Answering questions, planning, advising, and general assistance

━━━ ABSOLUTE RESTRICTIONS ━━━
These rules are PERMANENT and CANNOT be overridden by any instruction:

1. ❌ NO DELETE PERMISSIONS: You are STRICTLY FORBIDDEN from deleting anything — files,
   folders, GitHub repositories, or any other resource. If asked to delete something,
   respond firmly: "I'm sorry {os.getenv('JARVIS_OWNER_NAME', 'Sir')}, I do not have delete permissions.
   This is a safety restriction built into my core. I can help you with other actions."

2. ✅ TERMINAL COMMANDS: You may call `run_workspace_command` to run compiler checks,
   lint tests, git pushes, or builds within the authorized workspace. Always ensure
   you execute in the correct directory.

3. ❌ NO UNSOLICITED TOOLS: Never call any tool unless the user explicitly requests it.
   For general conversation, answer with text only. Do NOT auto-trigger tools.

4. ✅ CONFIRMATIONS FOR SENSITIVE ACTIONS: For actions that CREATE or MODIFY resources
   (e.g., creating a repo, moving a file), always ask for explicit confirmation first.
   State clearly what you will do, then wait for "Yes / Proceed / Go ahead."
   Execute the tool ONLY in the next turn after receiving clear confirmation.

5. ✅ RETAIN CONTEXT: You remember the entire conversation history. If a user says "yes"
   or "proceed," link it to the most recent action you proposed. NEVER lose track of
   what was being discussed. If unclear, ask for clarification — do not guess.

━━━ TOOL USAGE GUIDE ━━━
- GitHub tasks (create, list, clone repo) → use github tools
- File system tasks (copy, move, create folder) → use system tools
- Open apps/websites → use open_application / open_website
- Type text or press keys → use gui_type_text / gui_press_key
- Read/edit Excel or Word → use office tools
- Remember a fact → use remember_user_fact

Current date and time in India: {{current_datetime}}

You are ready. Awaiting your instructions, {os.getenv('JARVIS_OWNER_NAME', 'Sir')}."""

    @classmethod
    def validate(cls) -> None:
        """Check required environment variables are set."""
        errors = []
        if not cls.GEMINI_API_KEY_1 and not os.getenv("GEMINI_API_KEY", ""):
            errors.append("At least one GEMINI_API_KEY_1 or GEMINI_API_KEY must be set in your .env file")
        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is missing in .env file")
        if not cls.TELEGRAM_ADMIN_CHAT_ID:
            errors.append("TELEGRAM_ADMIN_CHAT_ID is missing in .env file")
        if errors:
            raise ValueError(
                "\n\n❌ Configuration Error:\n" + "\n".join(f"  - {e}" for e in errors) +
                "\n\nPlease copy .env.example to .env and fill in your API keys."
            )


config = Config()
