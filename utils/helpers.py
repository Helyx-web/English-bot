"""
Helper functions untuk berbagai keperluan.
"""
import random
import logging
from datetime import datetime
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

# Anti-spam: rate limiting per user
user_last_action = {}
RATE_LIMIT_SECONDS = 1.5  # Minimal 1.5 detik antara command


def rate_limit(func):
    """Decorator untuk anti-spam."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user:
            now = datetime.now().timestamp()
            last = user_last_action.get(user.id, 0)

            if now - last < RATE_LIMIT_SECONDS:
                if update.callback_query:
                    await update.callback_query.answer(
                        "⏳ Sabar cuy, terlalu cepat!",
                        show_alert=False
                    )
                return

            user_last_action[user.id] = now

        return await func(update, context)
    return wrapper


def is_admin(user_id: int) -> bool:
    """Cek apakah user adalah admin."""
    from config import ADMIN_IDS
    return user_id in ADMIN_IDS


def format_vocab_card(vocab: dict) -> str:
    """Format tampilan kartu kosakata."""
    level_emoji = {"A1": "🟢", "A2": "🟡", "B1": "🔴"}
    emoji = level_emoji.get(vocab["level"], "⚪")

    pos_translation = {
        "Noun": "Kata Benda",
        "Verb": "Kata Kerja",
        "Adjective": "Kata Sifat",
        "Adverb": "Kata Keterangan"
    }
    pos_id = pos_translation.get(vocab["part_of_speech"],
                                  vocab["part_of_speech"])

    text = (
        f"{emoji} **{vocab['word'].upper()}**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📖 **Arti:** {vocab['meaning']}\n"
        f"🔊 **Cara Baca:** {vocab['pronunciation']}\n"
        f"🏷️ **Jenis:** {pos_id}\n"
        f"📊 **Level:** {vocab['level']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💬 **Contoh:**\n"
        f"_{vocab['example']}_\n"
        f"📝 _{vocab['example_meaning']}_\n"
    )
    return text


def generate_multiple_choice(correct: str, all_words: list,
                              field: str = "meaning") -> list:
    """
    Generate 4 pilihan (1 benar, 3 salah) lalu diacak.
    """
    choices = [correct]
    pool = [w for w in all_words if w[field] != correct]
    random.shuffle(pool)

    for item in pool[:3]:
        choices.append(item[field])

    random.shuffle(choices)
    return choices


def generate_scrambled(word: str) -> list:
    """Acak huruf dari sebuah kata."""
    letters = list(word.lower())
    # Pastikan tidak sama dengan aslinya
    attempts = 0
    while attempts < 10:
        random.shuffle(letters)
        if "".join(letters) != word.lower():
            break
        attempts += 1
    return letters


MOTIVATIONAL_QUOTES = [
    "Learning English opens new doors! 🚪✨",
    "Practice makes perfect! Keep going! 💪",
    "Every expert was once a beginner! 🌟",
    "Don't be afraid to make mistakes! 📚",
    "Your only limit is you! Break free! 🚀",
    "Consistency beats intensity! Show up daily! ⭐",
    "Language is the road map of a culture! 🗺️",
    "The beautiful thing about learning is nobody can take it away! 💎",
    "Today's effort is tomorrow's success! ⚡",
    "Speak even if your voice shakes! 🎤",
    "One language sets you in a corridor for life! 🌍",
    "To learn a language is to have one more window! 🪟",
    "Mistakes are proof that you are trying! ✅",
    "The expert in anything was once a beginner! 🎓",
    "Learning never exhausts the mind! 🧠",
]

def get_random_quote() -> str:
    """Ambil quote motivasi random."""
    return random.choice(MOTIVATIONAL_QUOTES)


def get_level_title(level: int) -> str:
    """Title berdasarkan level user."""
    titles = {
        1: "🐣 Beginner",
        2: "🌱 Learner",
        3: "🌿 Student",
        4: "🌳 Scholar",
        5: "🏆 Achiever",
        6: "💎 Expert",
        7: "👑 Master",
        8: "🎖️ Grandmaster",
        9: "🔥 Legend",
        10: "⭐ Mythic",
    }
    if level >= 10:
        return "⭐ Mythic"
    return titles.get(level, "🐣 Beginner")


def get_streak_emoji(streak: int) -> str:
    """Emoji berdasarkan streak."""
    if streak >= 30:
        return "🔥🔥🔥"
    elif streak >= 14:
        return "🔥🔥"
    elif streak >= 7:
        return "🔥"
    elif streak >= 3:
        return "✨"
    elif streak >= 1:
        return "🌱"
    return "💤"


def calculate_accuracy(total_quiz: int, total_correct: int) -> float:
    """Hitung persentase akurasi."""
    if total_quiz == 0:
        return 0.0
    return round((total_correct / total_quiz) * 100, 1)
