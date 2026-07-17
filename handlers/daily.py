"""
Handler untuk Daily Challenge.
"""
import logging
from datetime import date
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_or_create_user, update_streak, get_random_vocab,
    add_xp, add_coins, get_db
)
from keyboards import main_menu_kb, back_to_menu_kb
from utils.helpers import rate_limit
from config import EMOJI, DAILY_BONUS

logger = logging.getLogger(__name__)


@rate_limit
async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /daily."""
    user = update.effective_user
    user_data = get_or_create_user(
        user.id, user.username or "", user.first_name or ""
    )

    today = date.today().strftime("%Y-%m-%d")

    # Cek apakah sudah selesai daily hari ini
    if user_data["daily_done"] == 1 and user_data["daily_date"] == today:
        await update.message.reply_text(
            f"✅ Kamu sudah menyelesaikan Daily Challenge hari ini!\n\n"
            f"Kembali besok untuk challenge baru! 🔥",
            parse_mode="Markdown"
        )
        return

    # Ambil 10 kata acak untuk daily challenge
    vocabs = get_random_vocab(limit=10)

    if not vocabs:
        await update.message.reply_text(
            "❌ Belum ada kosakata di database.",
            reply_markup=back_to_menu_kb()
        )
        return

    # Simpan session
    if not hasattr(context, 'user_data'):
        context.user_data = {}
    context.user_data["daily_words"] = vocabs
    context.user_data["daily_index"] = 0

    # Tampilkan kata pertama sebagai flashcard
    vocab = vocabs[0]

    from keyboards import vocab_card_kb

    text = (
        f"🔥 **DAILY CHALLENGE**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 {today}\n"
        f"📚 Pelajari 10 kata berikut!\n"
        f"🎁 Bonus: {DAILY_BONUS} XP setelah selesai!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"**KATA 1 dari 10**\n\n"
    )

    from utils.helpers import format_vocab_card
    text = text + format_vocab_card(vocab)

    await update.message.reply_text(
        text,
        reply_markup=vocab_card_kb(vocab["id"]),
        parse_mode="Markdown"
    )

    # Update daily status
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET daily_done = 1, daily_date = ? WHERE user_id = ?",
            (today, user.id)
        )

    # Berikan bonus XP
    add_xp(user.id, DAILY_BONUS)
    add_coins(user.id, 10)
    update_streak(user.id)

    # Cek badge
    from utils.gamification import check_and_award_badges, get_user_stats_dict
    stats = get_user_stats_dict(user.id)
    new_badges = check_and_award_badges(user.id, stats)

    if new_badges:
        badge_text = "🏅 **BADGE BARU!**\n\n"
        for badge in new_badges:
            badge_text += f"{badge['emoji']} **{badge['name']}**\n"
            badge_text += f"_{badge['desc']}_\n\n"

        await update.message.reply_text(badge_text, parse_mode="Markdown")

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            f"🎉 Daily Challenge selesai!\n"
            f"💎 +{DAILY_BONUS} XP\n"
            f"🪙 +10 Coins\n"
            f"🔥 Streak: {user_data['streak']} hari\n\n"
            f"Kata hari ini: {', '.join([v['word'] for v in vocabs[:5]])}..."
        ),
        reply_markup=main_menu_kb()
  )
