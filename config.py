"""
Konfigurasi utama bot.
Ambil token dari @BotFather di Telegram.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Ambil token dari environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Admin IDs (isi Telegram ID kamu, dapat dari @userinfobot)
ADMIN_IDS = [
    int(x) for x in os.getenv("ADMIN_IDS", "123456789").split(",")
    if x.strip()
]

# Channel untuk update (opsional)
UPDATE_CHANNEL = "@yourchannel"

# Konstanta gamifikasi
BASE_XP_PER_CORRECT = 10
COMBO_BONUS = 5
DAILY_BONUS = 50
LEVEL_UP_BASE = 100  # XP pertama untuk naik level

# Warna dan emoji untuk UI
EMOJI = {
    "book": "📚",
    "pencil": "📝",
    "target": "🎯",
    "fire": "🔥",
    "chart": "📊",
    "trophy": "🏆",
    "heart": "❤️",
    "gear": "⚙️",
    "robot": "🤖",
    "info": "ℹ️",
    "check": "✅",
    "cross": "❌",
    "star": "⭐",
    "brain": "🧠",
    "lightning": "⚡",
    "back": "🔙",
    "search": "🔍",
    "shuffle": "🔀",
    "calendar": "📅",
    "coin": "🪙",
    "medal": "🏅",
    "crown": "👑",
    "rocket": "🚀",
    "bell": "🔔",
    "speaker": "🔊",
    "magnify": "🔎",
    "white_check": "☑️",
    "gem": "💎",
    "sparkles": "✨",
    "warning": "⚠️",
    "bulb": "💡",
    "clock": "🕐",
    "pin": "📌",
    "bookmark": "🔖",
    "graduation": "🎓",
    "muscle": "💪",
    "party": "🎉",
}
