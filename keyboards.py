"""
Semua inline keyboard untuk UI bot.
"""
from telegram import InlineKeyboardButton, InlineKeyboardButton as IKB
from telegram import InlineKeyboardMarkup
from config import EMOJI


def main_menu_kb():
    """Menu utama bot."""
    keyboard = [
        [IKB(f"{EMOJI['book']} Belajar", callback_data="learn"),
         IKB(f"{EMOJI['pencil']} Quiz", callback_data="quiz")],
        [IKB(f"{EMOJI['target']} Latihan", callback_data="practice"),
         IKB(f"{EMOJI['fire']} Daily Challenge", callback_data="daily")],
        [IKB(f"{EMOJI['chart']} Progress", callback_data="progress"),
         IKB(f"{EMOJI['trophy']} Leaderboard", callback_data="leaderboard")],
        [IKB(f"{EMOJI['heart']} Favorit", callback_data="favorites"),
         IKB(f"{EMOJI['gear']} Pengaturan", callback_data="settings")],
        [IKB(f"{EMOJI['robot']} AI Tutor", callback_data="ai_tutor"),
         IKB(f"{EMOJI['info']} Bantuan", callback_data="help")],
    ]
    return InlineKeyboardMarkup(keyboard)


def learn_menu_kb():
    """Menu belajar."""
    keyboard = [
        [IKB(f"{EMOJI['book']} Per Kategori", callback_data="learn_category"),
         IKB(f"{EMOJI['shuffle']} Acak Kata", callback_data="learn_random")],
        [IKB(f"{EMOJI['search']} Cari Kata", callback_data="learn_search"),
         IKB(f"{EMOJI['bookmark']} Favorit Saya", callback_data="learn_fav")],
        [IKB(f"{EMOJI['graduation']} Belajar per Level",
             callback_data="learn_level")],
        [IKB(f"{EMOJI['brain']} Review SRS",
             callback_data="learn_srs")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def level_kb():
    """Pilihan level."""
    keyboard = [
        [IKB("🟢 A1 - Pemula", callback_data="level_A1"),
         IKB("🟡 A2 - Dasar", callback_data="level_A2")],
        [IKB("🔴 B1 - Menengah", callback_data="level_B1")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="learn")],
    ]
    return InlineKeyboardMarkup(keyboard)


def quiz_menu_kb():
    """Menu quiz."""
    keyboard = [
        [IKB("📝 Pilihan Ganda", callback_data="quiz_multiple"),
         IKB("🔤 Tebak Bahasa Inggris", callback_data="quiz_to_english")],
        [IKB("🇮🇩 Tebak Arti", callback_data="quiz_to_indo"),
         IKB("🧩 Susun Huruf", callback_data="quiz_arrange")],
        [IKB("🔊 Listening", callback_data="quiz_listening"),
         IKB("✏️ Isi Kalimat", callback_data="quiz_fill")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def vocab_card_kb(vocab_id: int, is_fav: bool = False):
    """Keyboard untuk kartu kosakata."""
    fav_text = f"{EMOJI['heart']} Hapus Favorit" if is_fav \
        else f"{EMOJI['heart']} Tambah Favorit"
    fav_data = f"unfav_{vocab_id}" if is_fav else f"fav_{vocab_id}"

    keyboard = [
        [IKB(f"{EMOJI['speaker']} Dengarkan",
             callback_data=f"pronounce_{vocab_id}")],
        [IKB(fav_text, callback_data=fav_data),
         IKB(f"{EMOJI['check']} Sudah Hafal",
             callback_data=f"learned_{vocab_id}")],
        [IKB("➡️ Kata Berikutnya", callback_data="next_vocab")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="learn")],
    ]
    return InlineKeyboardMarkup(keyboard)


def answer_kb(options: list, session_id: str):
    """Keyboard pilihan ganda untuk quiz."""
    keyboard = []
    letters = ["A", "B", "C", "D"]
    for i, option in enumerate(options):
        keyboard.append([IKB(f"{letters[i]}. {option}",
                              callback_data=f"answer_{i}_{session_id}")])
    return InlineKeyboardMarkup(keyboard)


def back_to_menu_kb():
    """Tombol kembali ke menu utama."""
    return InlineKeyboardMarkup(
        [[IKB(f"{EMOJI['back']} Menu Utama", callback_data="menu")]]
    )


def back_to_learn_kb():
    """Tombol kembali ke menu belajar."""
    return InlineKeyboardMarkup(
        [[IKB(f"{EMOJI['back']} Menu Belajar", callback_data="learn")]]
    )


def back_to_quiz_kb():
    """Tombol kembali ke menu quiz."""
    return InlineKeyboardMarkup(
        [[IKB(f"{EMOJI['back']} Menu Quiz", callback_data="quiz")]]
    )


def settings_kb(reminder_hour: int = 8):
    """Menu pengaturan."""
    keyboard = [
        [IKB(f"🔔 Jam Reminder: {reminder_hour}:00",
             callback_data="set_reminder")],
        [IKB("🎯 Target Harian", callback_data="set_goal"),
         IKB("🌏 Bahasa", callback_data="set_lang")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def leaderboard_period_kb():
    """Pilih periode leaderboard."""
    keyboard = [
        [IKB("🌍 Global", callback_data="lb_all"),
         IKB("📅 Mingguan", callback_data="lb_weekly")],
        [IKB("🗓️ Bulanan", callback_data="lb_monthly")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def admin_kb():
    """Menu admin."""
    keyboard = [
        [IKB("➕ Tambah Kata", callback_data="admin_add"),
         IKB("✏️ Edit Kata", callback_data="admin_edit")],
        [IKB("🗑️ Hapus Kata", callback_data="admin_delete"),
         IKB("📢 Broadcast", callback_data="admin_broadcast")],
        [IKB("📊 Statistik", callback_data="admin_stats"),
         IKB("💾 Backup DB", callback_data="admin_backup")],
        [IKB("👥 List User", callback_data="admin_users"),
         IKB("🔍 Cari User", callback_data="admin_search_user")],
        [IKB(f"{EMOJI['back']} Kembali", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def arrange_letters_kb(letters: list, session_id: str):
    """Keyboard untuk menyusun huruf (word scramble)."""
    keyboard = []
    row = []
    for i, letter in enumerate(letters):
        row.append(IKB(letter.upper(), callback_data=f"letter_{i}_{session_id}"))
        if len(row) == 4:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([IKB("🔄 Reset", callback_data=f"reset_arrange_{session_id}")])
    keyboard.append([IKB("✅ Submit", callback_data=f"submit_arrange_{session_id}")])
    return InlineKeyboardMarkup(keyboard)


def cancel_kb():
    """Tombol cancel untuk state conversations."""
    return InlineKeyboardMarkup(
        [[IKB("❌ Cancel", callback_data="cancel_action")]]
  )
