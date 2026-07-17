"""
Main entry point untuk English Master Bot.
Bot Telegram untuk belajar Bahasa Inggris dengan interaktif.
"""
import logging
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)

from config import BOT_TOKEN, EMOJI
from database import init_db
from vocab_data import seed_vocab

# Handlers
from handlers.basic import (
    start_command, menu_command, help_command,
    menu_callback, profile_command, stats_command
)
from handlers.learn import (
    learn_command, learn_callback, search_command, favorite_command
)
from handlers.quiz import (
    quiz_command, quiz_callback, answer_callback
)
from handlers.daily import daily_command
from handlers.progress import progress_command, leaderboard_callback
from handlers.admin import (
    admin_command, admin_callback, addword_command, broadcast_command
)

# Settings handler
from handlers.settings_handler import settings_callback

# Konfigurasi logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
# Reduce verbosity dari library
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


def main():
    """Jalankan bot."""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN tidak ditemukan!")
        print("Dapatkan token dari @BotFather di Telegram.")
        print("Lalu buat file .env dengan: BOT_TOKEN=your_token_here")
        return

    # Init database
    print("🔧 Initializing database...")
    init_db()

    # Seed vocabulary data
    print("📝 Loading vocabulary data...")
    seed_vocab()

    # Buat application
    print("🤖 Starting English Master Bot...")
    app = Application.builder().token(BOT_TOKEN).build()

    # ===== COMMAND HANDLERS =====
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("menu", menu_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("learn", learn_command))
    app.add_handler(CommandHandler("quiz", quiz_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("progress", progress_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("favorite", favorite_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("addword", addword_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # ===== CALLBACK QUERY HANDLERS =====
    app.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu$|^help$"))
    app.add_handler(CallbackQueryHandler(learn_callback, pattern="^learn|^level_|^next_vocab|^fav_|^unfav_|^learned_|^pronounce_|^cat_"))
    app.add_handler(CallbackQueryHandler(quiz_callback, pattern="^quiz"))
    app.add_handler(CallbackQueryHandler(answer_callback, pattern="^answer_"))
    app.add_handler(CallbackQueryHandler(leaderboard_callback, pattern="^leaderboard|^lb_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(settings_callback, pattern="^settings|^set_"))

    # Global catch-all callback yang belum terdaftar
    async def unknown_callback(update, context):
        query = update.callback_query
        if query:
            await query.answer()

    app.add_handler(CallbackQueryHandler(unknown_callback))

    # ===== ERROR HANDLER =====
    async def error_handler(update, context):
        """Log error."""
        logger.error(f"Exception: {context.error}", exc_info=context.error)

    app.add_error_handler(error_handler)

    # ===== START BOT =====
    print(f"\n{'='*50}")
    print(f"✅ English Master Bot is RUNNING!")
    print(f"{'='*50}\n")

    # Jalankan bot
    app.run_polling(
        allowed_updates=[
            "message",
            "callback_query",
            "edited_message",
            "chat_member"
        ],
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
