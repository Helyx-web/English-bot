"""
Handler untuk fitur quiz.
"""
import logging
import random
import uuid
from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_or_create_user, get_random_vocab, get_vocab_by_id,
    record_quiz_result, add_xp, add_coins, get_total_vocab
)
from keyboards import (
    quiz_menu_kb, answer_kb, back_to_quiz_kb,
    arrange_letters_kb, back_to_menu_kb
)
from utils.helpers import (
    rate_limit, generate_multiple_choice, generate_scrambled
)
from config import EMOJI

logger = logging.getLogger(__name__)

# Session storage untuk quiz
quiz_sessions = {}


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /quiz."""
    user = update.effective_user
    get_or_create_user(user.id, user.username or "", user.first_name or "")

    text = (
        f"{EMOJI['pencil']} **QUIZ TIME!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"Uji kemampuan Bahasa Inggrismu!\n\n"
        f"Pilih jenis quiz:"
    )

    await update.message.reply_text(
        text,
        reply_markup=quiz_menu_kb(),
        parse_mode="Markdown"
    )


async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler untuk menu quiz."""
    query = update.callback_query
    await query.answer()

    data = query.data
    user = update.effective_user
    get_or_create_user(user.id, user.username or "", user.first_name or "")

    if data == "quiz":
        await quiz_command(update, context)
        return

    quiz_types = {
        "quiz_multiple": ("multiple", "📝 Pilihan Ganda"),
        "quiz_to_english": ("to_english", "🔤 Tebak Bahasa Inggris"),
        "quiz_to_indo": ("to_indo", "🇮🇩 Tebak Arti"),
        "quiz_arrange": ("arrange", "🧩 Susun Huruf"),
        "quiz_fill": ("fill", "✏️ Isi Kalimat"),
        "quiz_listening": ("listening", "🔊 Listening Quiz"),
    }

    if data in quiz_types:
        qtype, title = quiz_types[data]
        await start_quiz(update, context, qtype, title)


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      quiz_type: str, title: str):
    """Mulai sesi quiz."""
    query = update.callback_query
    user = update.effective_user

    # Ambil 4 kata random untuk pilihan
    all_vocabs = get_random_vocab(limit=4)
    if len(all_vocabs) < 4:
        await query.edit_message_text(
            "❌ Butuh minimal 4 kosakata di database untuk quiz!",
            reply_markup=back_to_quiz_kb()
        )
        return

    correct_vocab = all_vocabs[0]

    # Buat session
    session_id = str(uuid.uuid4())[:8]
    quiz_sessions[session_id] = {
        "user_id": user.id,
        "type": quiz_type,
        "correct_vocab": correct_vocab,
        "all_vocabs": all_vocabs,
        "score": 0,
        "combo": 0,
        "best_combo": 0,
        "question_num": 1,
        "total_questions": 10,
        "correct_answers": 0,
    }

    await display_question(update, context, session_id)


async def display_question(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            session_id: str):
    """Tampilkan pertanyaan quiz."""
    query = update.callback_query
    session = quiz_sessions.get(session_id)

    if not session:
        await query.edit_message_text("❌ Sesi quiz berakhir.")
        return

    vocab = session["correct_vocab"]
    all_vocabs = session["all_vocabs"]
    qtype = session["type"]

    # Progress bar
    q_num = session["question_num"]
    total = session["total_questions"]
    progress = "█" * q_num + "░" * (total - q_num)

    if qtype == "to_indo":
        # Tunjukkan English, tebak Indonesia
        options = generate_multiple_choice(
            vocab["meaning"], all_vocabs, field="meaning"
        )
        session["options"] = options
        session["correct_index"] = options.index(vocab["meaning"])

        text = (
            f"🇮🇩 **TEBAK ARTI**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Apa arti dari:\n"
            f"📖 **{vocab['word'].upper()}**\n"
            f"🔊 {vocab['pronunciation']}\n\n"
            f"📊 Soal {q_num}/{total} | Skor: {session['score']} XP | "
            f"Combo: {session['combo']}🔥\n`[{progress}]`"
        )
        await query.edit_message_text(
            text,
            reply_markup=answer_kb(options, session_id),
            parse_mode="Markdown"
        )

    elif qtype == "to_english":
        # Tunjukkan Indonesia, tebak English
        options = generate_multiple_choice(
            vocab["word"], all_vocabs, field="word"
        )
        session["options"] = options
        session["correct_index"] = options.index(vocab["word"])

        text = (
            f"🔤 **TEBAK BAHASA INGGRIS**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Apa Bahasa Inggris dari:\n"
            f"📖 **{vocab['meaning'].upper()}**\n\n"
            f"📊 Soal {q_num}/{total} | Skor: {session['score']} XP | "
            f"Combo: {session['combo']}🔥\n`[{progress}]`"
        )
        await query.edit_message_text(
            text,
            reply_markup=answer_kb(options, session_id),
            parse_mode="Markdown"
        )

    elif qtype == "multiple":
        # Pilihan ganda dengan contoh kalimat
        options = generate_multiple_choice(
            vocab["word"], all_vocabs, field="word"
        )
        session["options"] = options
        session["correct_index"] = options.index(vocab["word"])

        # Hilangkan kata dari contoh kalimat
        blanked = vocab["example"].replace(vocab["word"], "_____")
        blanked = blanked.replace(vocab["word"].capitalize(), "_____")

        text = (
            f"📝 **PILIHAN GANDA**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Lengkapi kalimat:\n"
            f"💬 _{blanked}_\n\n"
            f"📊 Soal {q_num}/{total} | Skor: {session['score']} XP | "
            f"Combo: {session['combo']}🔥\n`[{progress}]`"
        )
        await query.edit_message_text(
            text,
            reply_markup=answer_kb(options, session_id),
            parse_mode="Markdown"
        )

    elif qtype == "arrange":
        # Susun huruf
        letters = generate_scrambled(vocab["word"])
        session["scrambled"] = letters
        session["selected_letters"] = []

        text = (
            f"🧩 **SUSUN HURUF**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"Arti: **{vocab['meaning']}**\n"
            f"Susun huruf menjadi kata yang benar!\n\n"
            f"📊 Soal {q_num}/{total} | Skor: {session['score']} XP | "
            f"Combo: {session['combo']}🔥\n`[{progress}]`"
        )
        await query.edit_message_text(
            text,
            reply_markup=arrange_letters_kb(letters, session_id),
            parse_mode="Markdown"
        )

    elif qtype == "fill":
        # Isi kalimat (mirip multiple tapi dengan hint)
        options = generate_multiple_choice(
            vocab["word"], all_vocabs, field="word"
        )
        session["options"] = options
        session["correct_index"] = options.index(vocab["word"])

        blanked = vocab["example"].replace(vocab["word"], "_____")

        text = (
            f"✏️ **ISI KALIMAT**\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"💡 Hint: {vocab['meaning']}\n\n"
            f"💬 _{blanked}_\n"
            f"📝 _{vocab['example_meaning']}_\n\n"
            f"📊 Soal {q_num}/{total} | Skor: {session['score']} XP | "
            f"Combo: {session['combo']}🔥\n`[{progress}]`"
        )
        await query.edit_message_text(
            text,
            reply_markup=answer_kb(options, session_id),
            parse_mode="Markdown"
        )

    elif qtype == "listening":
        # Listening: kirim audio dulu, lalu tebak
        try:
            from gtts import gTTS
            import io

            tts = gTTS(text=vocab["word"], lang='en', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            options = generate_multiple_choice(
                vocab["word"], all_vocabs, field="word"
            )
            session["options"] = options
            session["correct_index"] = options.index(vocab["word"])

            await context.bot.send_voice(
                chat_id=query.message.chat_id,
                voice=audio_buffer,
                caption=f"🔊 **LISTENING QUIZ**\nDengarkan dan pilih kata yang benar!"
            )

            text = (
                f"🔊 **LISTENING**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Pilih kata yang kamu dengar:\n\n"
                f"📊 Soal {q_num}/{total} | Skor: {session['score']} XP"
            )
            await query.edit_message_text(
                text,
                reply_markup=answer_kb(options, session_id),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Listening quiz error: {e}")
            # Fallback ke quiz biasa
            options = generate_multiple_choice(
                vocab["word"], all_vocabs, field="word"
            )
            session["options"] = options
            session["correct_index"] = options.index(vocab["word"])

            text = (
                f"🔊 **LISTENING** (Text mode)\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Pronunciation: {vocab['pronunciation']}\n"
                f"Pilih kata yang sesuai:\n\n"
                f"📊 Soal {q_num}/{total}"
            )
            await query.edit_message_text(
                text,
                reply_markup=answer_kb(options, session_id),
                parse_mode="Markdown"
            )


async def answer_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle jawaban quiz pilihan ganda."""
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_")

    if len(parts) < 3:
        return

    selected_index = int(parts[1])
    session_id = parts[2]

    session = quiz_sessions.get(session_id)
    if not session:
        await query.answer("❌ Sesi tidak ditemukan!", show_alert=True)
        return

    user_id = session["user_id"]
    correct_index = session["correct_index"]
    is_correct = selected_index == correct_index

    vocab = session["correct_vocab"]

    # Record result
    record_quiz_result(user_id, vocab["id"], session["type"], is_correct)

    if is_correct:
        session["combo"] += 1
        session["best_combo"] = max(session["best_combo"], session["combo"])
        session["correct_answers"] += 1

        # Hitung XP dengan combo bonus
        xp_gain = 10 + (session["combo"] - 1) * 2
        session["score"] += xp_gain

        result_msg = f"✅ Benar! +{xp_gain} XP"
        if session["combo"] >= 3:
            result_msg += f"\n🔥 Combo x{session['combo']}!"

        await query.answer(result_msg, show_alert=False)

        # Tambah XP ke user
        add_xp(user_id, xp_gain)
        add_coins(user_id, 1)

    else:
        session["combo"] = 0
        correct_answer = session["options"][correct_index]
        await query.answer(
            f"❌ Salah! Jawaban: {correct_answer}",
            show_alert=True
        )

    # Next question atau selesai
    session["question_num"] += 1

    if session["question_num"] > session["total_questions"]:
        await finish_quiz(update, context, session_id)
    else:
        # Ambil kata baru
        all_vocabs = get_random_vocab(limit=4)
        session["correct_vocab"] = all_vocabs[0]
        session["all_vocabs"] = all_vocabs
        await display_question(update, context, session_id)


async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
                       session_id: str):
    """Tampilkan hasil akhir quiz."""
    query = update.callback_query
    session = quiz_sessions.get(session_id)

    if not session:
        return

    user_id = session["user_id"]
    total = session["total_questions"]
    correct = session["correct_answers"]
    score = session["score"]
    best_combo = session["best_combo"]
    accuracy = round((correct / total) * 100, 1)

    # Bonus XP
    bonus = 0
    if accuracy == 100:
        bonus = 50
        add_xp(user_id, bonus)
    elif accuracy >= 80:
        bonus = 20
        add_xp(user_id, bonus)

    # Tambah XP dari skor
    add_xp(user_id, score)

    # Update streak
    from database import update_streak
    update_streak(user_id)

    # Emoji rating
    if accuracy == 100:
        rating = "🏆 PERFECT!"
    elif accuracy >= 80:
        rating = "🌟 EXCELLENT!"
    elif accuracy >= 60:
        rating = "👍 GOOD!"
    elif accuracy >= 40:
        rating = "💪 KEEP TRYING!"
    else:
        rating = "📚 NEED MORE PRACTICE"

    text = (
        f"🎉 **QUIZ SELESAI!**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{rating}\n\n"
        f"📊 **HASIL:**\n"
        f"✅ Benar: {correct}/{total}\n"
        f"🎯 Akurasi: {accuracy}%\n"
        f"💎 XP Earned: {score + bonus}\n"
        f"🔥 Best Combo: {best_combo}\n"
    )

    if bonus > 0:
        text += f"🎁 Bonus XP: +{bonus}\n"

    text += f"\n💬 _Tetap semangat belajar!_"

    from keyboards import main_menu_kb
    await query.edit_message_text(
        text,
        reply_markup=main_menu_kb(),
        parse_mode="Markdown"
    )

    # Hapus session
    del quiz_sessions[session_id]

    # Cek badge
    from utils.gamification import check_and_award_badges, get_user_stats_dict
    stats = get_user_stats_dict(user_id)
    new_badges = check_and_award_badges(user_id, stats)

    if new_badges:
        badge_text = "🏅 **BADGE BARU!**\n\n"
        for badge in new_badges:
            badge_text += f"{badge['emoji']} **{badge['name']}**\n"
            badge_text += f"_{badge['desc']}_\n\n"

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=badge_text,
            parse_mode="Markdown"
        )
