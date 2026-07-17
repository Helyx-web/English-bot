"""
Handler untuk progress dan leaderboard.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_or_create_user, get_leaderboard, get_db
)
from keyboards import back_to_menu_kb, leaderboard_period_kb
from utils.helpers import (
    rate_limit, calculate_accuracy, get_level_title
)
from utils.gamification import get_xp_progress, get_user_badges
from config import EMOJI

logger = logging.getLogger(__name__)


@rate_limit
async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /progress."""
    user = update.effective_user
    user_data = get_or_create_user(
        user.id, user.username or "", user.first_name or ""
    )

    with get_db() as conn:
        words_studied = conn.execute(
            "SELECT COUNT(*) as c FROM progress WHERE user_id = ?",
            (user.id,)
        ).fetchone()["c"]

        fav_count = conn.execute(
            "SELECT COUNT(*) as c FROM favorites WHERE user_id = ?",
            (user.id,)
        ).fetchone()["c"]

        # Statistik mingguan
        from datetime import datetime, timedelta
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        weekly_quiz = conn.execute(
            "SELECT COUNT(*) as c FROM quiz_history WHERE user_id = ? AND answered_at >= ?",
            (user.id, week_ago)
        ).fetchone()["c"]
        weekly_correct = conn.execute(
            "SELECT COUNT(*) as c FROM quiz_history WHERE user_id = ? AND is_correct = 1 AND answered_at >= ?",
            (user.id, week_ago)
        ).fetchone()["c"]

    xp_info = get_xp_progress(user.id)
    accuracy = calculate_accuracy(user_data["total_quiz"],
                                   user_data["total_correct"])
    weekly_accuracy = calculate_accuracy(weekly_quiz, weekly_correct)

    progress_blocks = int(xp_info["progress_pct"] / 10)
    progress_bar = "█" * progress_blocks + "░" * (10 - progress_blocks)

    text = (
        f"📊 **PROGRESS BELAJAR**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 **{user.first_name}**\n"
        f"🎖️ {get_level_title(user_data['level'])}\n\n"
        f"⭐ **Level:** {user_data['level']}\n"
        f"💎 **Total XP:** {user_data['xp']}\n"
        f"📈 **Progress ke Level {user_data['level'] + 1}:**\n"
        f"`[{progress_bar}]` {xp_info['progress_pct']}%\n"
        f"({xp_info['xp_in_level']}/{xp_info['xp_needed']} XP)\n\n"
        f"📚 **STATISTIK BELAJAR:**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📖 Kata Dipelajari: {words_studied}\n"
        f"📝 Total Quiz: {user_data['total_quiz']}\n"
        f"🎯 Akurasi Total: {accuracy}%\n"
        f"❤️ Favorit: {fav_count}\n\n"
        f"📅 **MINGGU INI:**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 Quiz: {weekly_quiz}\n"
        f"🎯 Akurasi: {weekly_accuracy}%\n\n"
        f"🔥 **Streak:** {user_data['streak']} hari\n"
        f"🪙 **Coins:** {user_data['coins']}\n"
    )

    await update.message.reply_text(
        text,
        reply_markup=back_to_menu_kb(),
        parse_mode="Markdown"
    )


async def leaderboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback untuk leaderboard."""
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "leaderboard":
        text = (
            f"🏆 **LEADERBOARD**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Pilih periode:"
        )
        await query.edit_message_text(
            text,
            reply_markup=leaderboard_period_kb(),
            parse_mode="Markdown"
        )
        return

    if data.startswith("lb_"):
        period = data.split("_")[1]
        period_names = {
            "all": "🌍 GLOBAL",
            "weekly": "📅 MINGGUAN",
            "monthly": "🗓️ BULANAN"
        }

        entries = get_leaderboard(period=period, limit=10)

        if not entries:
            await query.edit_message_text(
                "❌ Belum ada data leaderboard.",
                reply_markup=back_to_menu_kb()
            )
            return

        medals = ["🥇", "🥈", "🥉"]
        text = (
            f"{period_names.get(period, '🏆 LEADERBOARD')}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for i, entry in enumerate(entries, 1):
            name = entry["first_name"] or entry["username"] or "Anonim"
            if i <= 3:
                text += f"{medals[i-1]} **{name}**\n"
            else:
                text += f"**{i}.** {name}\n"
            text += f"   Level {entry['level']} | {entry['xp']} XP | 🔥{entry['streak']}\n"

        await query.edit_message_text(
            text,
            reply_markup=back_to_menu_kb(),
            parse_mode="Markdown"
  )
