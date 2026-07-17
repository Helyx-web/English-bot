"""
Handler untuk command dasar: /start, /help, /menu, dll.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_or_create_user, update_streak, get_total_vocab, get_stats
)
from keyboards import main_menu_kb
from utils.helpers import (
    rate_limit, is_admin, get_random_quote,
    get_level_title, get_streak_emoji, calculate_accuracy
)
from config import EMOJI

logger = logging.getLogger(__name__)


@rate_limit
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start."""
    user = update.effective_user
    get_or_create_user(user.id, user.username or "", user.first_name or "")
    update_streak(user.id)

    total_vocab = get_total_vocab()

    welcome_text = (
        f"{EMOJI['graduation']} **Selamat Datang di English Master Bot!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Halo **{user.first_name}**! 👋\n\n"
        f"📘 Bot ini akan membantumu belajar Bahasa Inggris dengan:\n"
        f"  • {total_vocab}+ kosakata lengkap\n"
        f"  • Quiz interaktif & seru\n"
        f"  • Sistem XP & Level seperti game\n"
        f"  • Daily Challenge dengan bonus\n"
        f"  • Spaced Repetition (SRS)\n"
        f"  • AI Tutor untuk bertanya\n\n"
        f"{EMOJI['rocket']} **Mari mulai belajar!** Pilih menu di bawah:\n\n"
        f"💬 _{get_random_quote()}_"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


@rate_limit
async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /menu."""
    user = update.effective_user
    get_or_create_user(user.id, user.username or "", user.first_name or "")

    text = (
        f"{EMOJI['gear']} **MENU UTAMA**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Hai **{user.first_name}**! 👋\n"
        f"Pilih fitur yang ingin kamu gunakan.\n\n"
        f"💬 _{get_random_quote()}_"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


@rate_limit
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help."""
    text = (
        f"{EMOJI['info']} **PANDUAN PENGGUNAAN**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**COMMANDS TERSEDIA:**\n\n"
        f"`/start` - Mulai bot & menu utama\n"
        f"`/menu` - Tampilkan menu utama\n"
        f"`/help` - Bantuan ini\n"
        f"`/learn` - Belajar kosakata baru\n"
        f"`/quiz` - Mulai quiz\n"
        f"`/daily` - Daily Challenge\n"
        f"`/progress` - Lihat progresmu\n"
        f"`/profile` - Profile & statistik\n"
        f"`/favorite` - Kata favoritmu\n"
        f"`/search <kata>` - Cari kata\n"
        f"`/settings` - Pengaturan\n"
        f"`/admin` - Panel admin (admin only)\n\n"
        f"**FITUR UTAMA:**\n\n"
        f"📚 **Belajar** - Pelajari kosakata baru\n"
        f"📝 **Quiz** - Uji kemampuanmu\n"
        f"🎯 **Latihan** - Latihan soal\n"
        f"🔥 **Daily Challenge** - Tantangan harian\n"
        f"📊 **Progress** - Pantau perkembangan\n"
        f"🏆 **Leaderboard** - Ranking terbaik\n"
        f"❤️ **Favorit** - Simpan kata penting\n"
        f"🤖 **AI Tutor** - Tanya jawab grammar\n\n"
        f"💡 _Tip: Belajar sedikit setiap hari lebih efektif!_"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


@rate_limit
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler untuk menu navigasi."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu":
        user = update.effective_user
        get_or_create_user(user.id, user.username or "",
                           user.first_name or "")

        text = (
            f"{EMOJI['gear']} **MENU UTAMA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Pilih fitur yang ingin kamu gunakan."
        )

        await query.edit_message_text(
            text,
            reply_markup=main_menu_kb(),
            parse_mode="Markdown"
        )

    elif data == "help":
        from handlers import help_command
        await help_command(update, context)


@rate_limit
async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /profile."""
    user = update.effective_user
    user_data = get_or_create_user(user.id, user.username or "",
                                    user.first_name or "")
    update_streak(user.id)

    from database import get_db
    from utils.gamification import get_xp_progress, get_user_badges

    with get_db() as conn:
        words_studied = conn.execute(
            "SELECT COUNT(*) as c FROM progress WHERE user_id = ?",
            (user.id,)
        ).fetchone()["c"]

        fav_count = conn.execute(
            "SELECT COUNT(*) as c FROM favorites WHERE user_id = ?",
            (user.id,)
        ).fetchone()["c"]

    xp_info = get_xp_progress(user.id)
    badges = get_user_badges(user.id)
    accuracy = calculate_accuracy(user_data["total_quiz"],
                                   user_data["total_correct"])

    # Progress bar
    progress_blocks = int(xp_info["progress_pct"] / 10)
    progress_bar = "█" * progress_blocks + "░" * (10 - progress_blocks)

    title = get_level_title(user_data["level"])
    streak_emoji = get_streak_emoji(user_data["streak"])

    badge_text = " ".join([b["emoji"] for b in badges[:10]]) if badges else "Belum ada badge"

    text = (
        f"👤 **PROFILE**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Nama:** {user.first_name}\n"
        f"**Username:** @{user.username or '-'}\n"
        f"**Title:** {title}\n\n"
        f"📊 **STATISTIK:**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⭐ **Level:** {user_data['level']}\n"
        f"💎 **XP:** {user_data['xp']} ({xp_info['progress_pct']}% to next)\n"
        f"`[{progress_bar}]`\n"
        f"🪙 **Coins:** {user_data['coins']}\n"
        f"🔥 **Streak:** {user_data['streak']} hari {streak_emoji}\n"
        f"📚 **Kata Dipelajari:** {words_studied}\n"
        f"📝 **Total Quiz:** {user_data['total_quiz']}\n"
        f"🎯 **Akurasi:** {accuracy}%\n"
        f"❤️ **Favorit:** {fav_count}\n\n"
        f"🏅 **BADGES:** {len(badges)}/{len(badges)}\n"
        f"{badge_text}\n"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )


@rate_limit
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk statistik global (admin)."""
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text(
            f"{EMOJI['cross']} Command ini khusus admin!"
        )
        return

    stats = get_stats()
    text = (
        f"📊 **STATISTIK BOT**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 **Total Users:** {stats['total_users']}\n"
        f"📚 **Total Vocabulary:** {stats['total_vocab']}\n"
        f"📝 **Total Quiz Taken:** {stats['total_quiz']}\n"
        f"🟢 **Active Today:** {stats['active_today']}\n"
    )

    await update.message.reply_text(text, parse_mode="Markdown")
