"""
Handler untuk admin panel.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_or_create_user, add_vocab, delete_vocab,
    get_all_users, get_stats, get_total_vocab, get_db
)
from keyboards import admin_kb, main_menu_kb, back_to_menu_kb
from utils.helpers import rate_limit, is_admin
from config import EMOJI

logger = logging.getLogger(__name__)


@rate_limit
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /admin."""
    user = update.effective_user

    if not is_admin(user.id):
        await update.message.reply_text(
            f"{EMOJI['cross']} Akses ditolak! Command ini khusus admin."
        )
        return

    stats = get_stats()

    text = (
        f"⚙️ **ADMIN PANEL**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📊 **STATISTIK:**\n"
        f"👥 Users: {stats['total_users']}\n"
        f"📚 Vocab: {stats['total_vocab']}\n"
        f"📝 Quizzes: {stats['total_quiz']}\n"
        f"🟢 Active Today: {stats['active_today']}\n\n"
        f"Pilih aksi:"
    )

    await update.message.reply_text(
        text,
        reply_markup=admin_kb(),
        parse_mode="Markdown"
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler untuk admin actions."""
    query = update.callback_query
    user = update.effective_user

    if not is_admin(user.id):
        await query.answer("❌ Akses ditolak!", show_alert=True)
        return

    await query.answer()
    data = query.data

    if data == "admin_stats":
        stats = get_stats()
        text = (
            f"📊 **STATISTIK BOT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👥 Total Users: {stats['total_users']}\n"
            f"📚 Total Vocabulary: {stats['total_vocab']}\n"
            f"📝 Total Quiz: {stats['total_quiz']}\n"
            f"🟢 Active Today: {stats['active_today']}\n"
        )
        await query.edit_message_text(
            text,
            reply_markup=admin_kb(),
            parse_mode="Markdown"
        )

    elif data == "admin_add":
        await query.edit_message_text(
            "➕ **TAMBAH KATA BARU**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Format:\n"
            "`/addword word|meaning|pronunciation|example|example_meaning|"
            "pos|level`\n\n"
            "Contoh:\n"
            "`/addword happy|bahagia|/ˈhæpi/|She is happy|"
            "Dia bahagia|Adjective|A1`",
            reply_markup=admin_kb(),
            parse_mode="Markdown"
        )

    elif data == "admin_broadcast":
        await query.edit_message_text(
            "📢 **BROADCAST MESSAGE**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Gunakan:\n"
            "`/broadcast <pesan>`\n\n"
            "Contoh:\n"
            "`/broadcast Halo semua! Tetap semangat belajar!`",
            reply_markup=admin_kb(),
            parse_mode="Markdown"
        )

    elif data == "admin_backup":
        # Backup database
        from database import DB_PATH
        try:
            with open(DB_PATH, 'rb') as f:
                await context.bot.send_document(
                    chat_id=query.message.chat_id,
                    document=f,
                    filename=f"backup_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                    caption="💾 Database backup"
                )
            await query.answer("✅ Backup berhasil!", show_alert=True)
        except Exception as e:
            logger.error(f"Backup error: {e}")
            await query.answer("❌ Backup gagal!", show_alert=True)

    elif data == "admin_users":
        users = get_all_users()
        text = f"👥 **DAFTAR USER ({len(users)})**\n"
        text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"

        for i, u in enumerate(users[:20], 1):
            name = u["first_name"] or u["username"] or "Anonim"
            text += f"**{i}.** {name} (Lvl {u['level']}, {u['xp']} XP)\n"

        if len(users) > 20:
            text += f"\n_dan {len(users) - 20} lainnya..._"

        await query.edit_message_text(
            text,
            reply_markup=admin_kb(),
            parse_mode="Markdown"
        )

    elif data == "admin_delete":
        await query.edit_message_text(
            "🗑️ **HAPUS KATA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Gunakan:\n"
            "`/deleteword <id>`\n\n"
            "Cek ID kata dengan `/vocablist`",
            reply_markup=admin_kb(),
            parse_mode="Markdown"
        )


@rate_limit
async def addword_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: tambah kosakata baru."""
    user = update.effective_user

    if not is_admin(user.id):
        return

    if not context.args:
        await update.message.reply_text(
            "Format: `/addword word|meaning|pronunciation|example|"
            "example_meaning|pos|level`",
            parse_mode="Markdown"
        )
        return

    args = " ".join(context.args)
    parts = args.split("|")

    if len(parts) < 7:
        await update.message.reply_text(
            "❌ Format salah! Butuh 7 bagian dipisah |"
        )
        return

    word, meaning, pronunciation, example, example_meaning, pos, level = \
        [p.strip() for p in parts[:7]]

    add_vocab(word, meaning, pronunciation, example,
              example_meaning, pos, level)

    await update.message.reply_text(
        f"✅ Kata ditambahkan!\n\n"
        f"**{word}** - {meaning}\n"
        f"Level: {level}",
        parse_mode="Markdown"
    )


@rate_limit
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: broadcast message ke semua user."""
    user = update.effective_user

    if not is_admin(user.id):
        return

    if not context.args:
        await update.message.reply_text("Format: `/broadcast <pesan>`",
                                         parse_mode="Markdown")
        return

    message = " ".join(context.args)
    users = get_all_users()

    success = 0
    failed = 0

    status_msg = await update.message.reply_text(
        f"📢 Broadcasting ke {len(users)} users..."
    )

    for u in users:
        try:
            await context.bot.send_message(
                chat_id=u["user_id"],
                text=f"📢 **PENGUMUMAN**\n\n{message}",
                parse_mode="Markdown"
            )
            success += 1
        except Exception as e:
            logger.error(f"Broadcast failed for {u['user_id']}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ Broadcast selesai!\n"
        f"📤 Terkirim: {success}\n"
        f"❌ Gagal: {failed}"
          )
