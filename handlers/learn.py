"""
Handler untuk fitur belajar kosakata.
"""
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_or_create_user, get_random_vocab, get_vocab_by_level,
    search_vocab, get_vocab_by_id, mark_word_studied,
    is_favorite, add_favorite, remove_favorite,
    get_favorites, get_total_vocab
)
from keyboards import (
    learn_menu_kb, vocab_card_kb, level_kb,
    back_to_learn_kb, back_to_menu_kb
)
from utils.helpers import rate_limit, format_vocab_card
from config import EMOJI

logger = logging.getLogger(__name__)

# Session storage untuk belajar
learn_sessions = {}


@rate_limit
async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /learn."""
    user = update.effective_user
    get_or_create_user(user.id, user.username or "", user.first_name or "")

    text = (
        f"{EMOJI['book']} **BELAJAR KOSAKATA**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Tersedia {get_total_vocab()} kosakata untuk dipelajari!\n\n"
        f"Pilih cara belajar yang kamu suka:"
    )

    await update.message.reply_text(
        text,
        reply_markup=learn_menu_kb(),
        parse_mode="Markdown"
    )


async def learn_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler untuk menu belajar."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user
    get_or_create_user(user.id, user.username or "", user.first_name or "")

    if data == "learn":
        await learn_command(update, context)
        return

    if data == "learn_random":
        await start_random_learn(update, context)

    elif data == "learn_level":
        text = (
            f"{EMOJI['graduation']} **PILIH LEVEL**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Pilih level kesulitan:\n"
            f"🟢 **A1** - Pemula\n"
            f"🟡 **A2** - Dasar\n"
            f"🔴 **B1** - Menengah"
        )
        await query.edit_message_text(
            text,
            reply_markup=level_kb(),
            parse_mode="Markdown"
        )

    elif data.startswith("level_"):
        level = data.split("_")[1]
        await start_level_learn(update, context, level)

    elif data == "learn_category":
        await show_categories(update, context)

    elif data == "learn_search":
        await query.edit_message_text(
            f"{EMOJI['search']} **CARI KATA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Ketik kata yang ingin kamu cari:\n"
            f"Contoh: `/search apple`\n\n"
            f"Atau gunakan format: `kata_inggris` atau `kata_indonesia`",
            reply_markup=back_to_learn_kb(),
            parse_mode="Markdown"
        )

    elif data == "learn_fav":
        await show_favorites(update, context)

    elif data == "learn_srs":
        await show_srs_review(update, context)

    elif data == "next_vocab":
        await next_vocab(update, context)

    elif data.startswith("fav_"):
        vocab_id = int(data.split("_")[1])
        add_favorite(user.id, vocab_id)
        await query.answer("❤️ Ditambahkan ke favorit!", show_alert=True)
        # Refresh card
        vocab = get_vocab_by_id(vocab_id)
        if vocab:
            await query.edit_message_reply_markup(
                reply_markup=vocab_card_kb(vocab_id, is_fav=True)
            )

    elif data.startswith("unfav_"):
        vocab_id = int(data.split("_")[1])
        remove_favorite(user.id, vocab_id)
        await query.answer("💔 Dihapus dari favorit!", show_alert=True)
        vocab = get_vocab_by_id(vocab_id)
        if vocab:
            await query.edit_message_reply_markup(
                reply_markup=vocab_card_kb(vocab_id, is_fav=False)
            )

    elif data.startswith("learned_"):
        vocab_id = int(data.split("_")[1])
        mark_word_studied(user.id, vocab_id)
        from database import add_xp
        result = add_xp(user.id, 5)

        msg = f"✅ Mantap! +5 XP"
        if result and result.get("leveled_up"):
            msg += f"\n🎉 LEVEL UP! Sekarang Level {result['new_level']}!"

        await query.answer(msg, show_alert=True)

    elif data.startswith("pronounce_"):
        vocab_id = int(data.split("_")[1])
        await send_pronunciation(update, context, vocab_id)


async def start_random_learn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai belajar kata acak."""
    query = update.callback_query
    user = update.effective_user

    vocabs = get_random_vocab(limit=1)
    if not vocabs:
        await query.edit_message_text(
            "❌ Belum ada kosakata di database.",
            reply_markup=back_to_learn_kb()
        )
        return

    vocab = vocabs[0]
    learn_sessions[user.id] = {"mode": "random", "current": vocab["id"]}

    is_fav = is_favorite(user.id, vocab["id"])
    text = format_vocab_card(vocab)

    await query.edit_message_text(
        text,
        reply_markup=vocab_card_kb(vocab["id"], is_fav),
        parse_mode="Markdown"
    )


async def start_level_learn(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             level: str):
    """Belajar berdasarkan level."""
    query = update.callback_query
    user = update.effective_user

    vocabs = get_vocab_by_level(level, limit=1)
    if not vocabs:
        await query.edit_message_text(
            f"❌ Belum ada kosakata level {level}.",
            reply_markup=level_kb()
        )
        return

    vocab = vocabs[0]
    learn_sessions[user.id] = {
        "mode": f"level_{level}",
        "current": vocab["id"]
    }

    is_fav = is_favorite(user.id, vocab["id"])
    text = format_vocab_card(vocab)

    await query.edit_message_text(
        text,
        reply_markup=vocab_card_kb(vocab["id"], is_fav),
        parse_mode="Markdown"
    )


async def next_vocab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan kata berikutnya."""
    query = update.callback_query
    user = update.effective_user

    session = learn_sessions.get(user.id, {})
    mode = session.get("mode", "random")
    current_id = session.get("current")

    if mode.startswith("level_"):
        level = mode.split("_")[1]
        vocabs = get_vocab_by_level(level, limit=1)
    else:
        vocabs = get_random_vocab(exclude_ids=[current_id] if current_id else None,
                                   limit=1)

    if not vocabs:
        await query.edit_message_text(
            "🎉 Kamu sudah mempelajari semua kata!",
            reply_markup=back_to_learn_kb()
        )
        return

    vocab = vocabs[0]
    learn_sessions[user.id]["current"] = vocab["id"]

    is_fav = is_favorite(user.id, vocab["id"])
    text = format_vocab_card(vocab)

    await query.edit_message_text(
        text,
        reply_markup=vocab_card_kb(vocab["id"], is_fav),
        parse_mode="Markdown"
    )


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan kategori kosakata."""
    query = update.callback_query

    from database import get_db
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category, COUNT(*) as c FROM vocabulary GROUP BY category"
        ).fetchall()

    if not rows:
        await query.edit_message_text(
            "❌ Tidak ada kategori.",
            reply_markup=back_to_learn_kb()
        )
        return

    from telegram import InlineKeyboardButton as IKB, InlineKeyboardMarkup
    keyboard = []
    for row in rows:
        keyboard.append([IKB(f"📁 {row['category'].title()} ({row['c']} kata)",
                              callback_data=f"cat_{row['category']}")])
    keyboard.append([IKB(f"{EMOJI['back']} Kembali", callback_data="learn")])

    text = (
        f"📁 **KATEGORI KOSAKATA**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Pilih kategori untuk belajar:"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan kata favorit user."""
    query = update.callback_query
    user = update.effective_user

    favs = get_favorites(user.id)

    if not favs:
        await query.edit_message_text(
            f"{EMOJI['heart']} **KATA FAVORIT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Belum ada kata favorit.\n"
            f"Tambahkan kata ke favorit dengan tombol ❤️ saat belajar!",
            reply_markup=back_to_learn_kb(),
            parse_mode="Markdown"
        )
        return

    text = f"{EMOJI['heart']} **KATA FAVORIT ({len(favs)})**\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, vocab in enumerate(favs[:15], 1):  # Maksimal 15 kata
        text += f"**{i}.** {vocab['word']} - {vocab['meaning']}\n"

    if len(favs) > 15:
        text += f"\n_dan {len(favs) - 15} kata lainnya..._"

    await query.edit_message_text(
        text,
        reply_markup=back_to_learn_kb(),
        parse_mode="Markdown"
    )


async def show_srs_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan kata yang perlu direview (SRS)."""
    query = update.callback_query
    user = update.effective_user

    from database import get_db
    from datetime import date
    today = date.today().strftime("%Y-%m-%d")

    with get_db() as conn:
        rows = conn.execute(
            """SELECT v.*, p.srs_level, p.srs_next_review
               FROM vocabulary v
               INNER JOIN progress p ON v.id = p.word_id
               WHERE p.user_id = ? AND p.srs_next_review <= ?
               ORDER BY p.srs_next_review ASC
               LIMIT 10""",
            (user.id, today)
        ).fetchall()

    if not rows:
        await query.edit_message_text(
            f"{EMOJI['brain']} **SPACED REPETITION REVIEW**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"✅ Tidak ada kata untuk direview hari ini!\n"
            f"🎉 Kerja bagus! Kembali lagi besok.",
            reply_markup=back_to_learn_kb(),
            parse_mode="Markdown"
        )
        return

    text = (
        f"{EMOJI['brain']} **SPACED REPETITION REVIEW**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📝 {len(rows)} kata perlu direview:\n\n"
    )
    for i, row in enumerate(rows, 1):
        text += f"**{i}.** {row['word']} - {row['meaning']}\n"

    await query.edit_message_text(
        text,
        reply_markup=back_to_learn_kb(),
        parse_mode="Markdown"
    )


async def send_pronunciation(update: Update, context: ContextTypes.DEFAULT_TYPE,
                              vocab_id: int):
    """Kirim audio pronunciation menggunakan gTTS."""
    query = update.callback_query

    vocab = get_vocab_by_id(vocab_id)
    if not vocab:
        return

    try:
        from gtts import gTTS
        import io

        await query.answer("🔊 Generating audio...")

        tts = gTTS(text=vocab["word"], lang='en', slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        await context.bot.send_voice(
            chat_id=query.message.chat_id,
            voice=audio_buffer,
            caption=f"🔊 **{vocab['word']}** - {vocab['pronunciation']}",
            parse_mode="Markdown"
        )

    except ImportError:
        await query.answer(
            "⚠️ Fitur audio belum diinstall. Run: pip install gTTS",
            show_alert=True
        )
    except Exception as e:
        logger.error(f"TTS error: {e}")
        await query.answer("⚠️ Gagal generate audio.", show_alert=True)


@rate_limit
async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /search."""
    if not context.args:
        await update.message.reply_text(
            f"{EMOJI['search']} **CARI KATA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Gunakan: `/search <kata>`\n"
            f"Contoh: `/search apple`",
            parse_mode="Markdown"
        )
        return

    keyword = " ".join(context.args)
    results = search_vocab(keyword)

    if not results:
        await update.message.reply_text(
            f"❌ Tidak ditemukan kata: **{keyword}**",
            parse_mode="Markdown"
        )
        return

    text = f"{EMOJI['search']} **HASIL PENCARIAN: {keyword}**\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, vocab in enumerate(results[:10], 1):
        text += f"**{i}.** {vocab['word']} ({vocab['level']})\n"
        text += f"   📖 {vocab['meaning']}\n"
        text += f"   💬 _{vocab['example']}_\n\n"

    if len(results) > 10:
        text += f"_dan {len(results) - 10} hasil lainnya..._"

    await update.message.reply_text(text, parse_mode="Markdown")


@rate_limit
async def favorite_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /favorite."""
    user = update.effective_user
    favs = get_favorites(user.id)

    if not favs:
        await update.message.reply_text(
            f"{EMOJI['heart']} **KATA FAVORIT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Belum ada kata favorit.\n"
            f"Tambahkan kata ke favorit saat belajar!",
            reply_markup=back_to_learn_kb(),
            parse_mode="Markdown"
        )
        return

    text = f"{EMOJI['heart']} **KATA FAVORIT ({len(favs)})**\n"
    text += f"━━━━━━━━━━━━━━━━━━━━━\n\n"

    for i, vocab in enumerate(favs[:20], 1):
        text += f"**{i}.** {vocab['word']} - {vocab['meaning']}\n"

    await update.message.reply_text(text, parse_mode="Markdown")
