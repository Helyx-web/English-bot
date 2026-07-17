"""
Sistem gamifikasi: XP, Level, Badge.
"""
from database import get_db, get_or_create_user
from config import BASE_XP_PER_CORRECT, COMBO_BONUS, DAILY_BONUS

# Definisi badges
BADGES = {
    "first_word": {"name": "📚 First Step", "desc": "Belajar kata pertama",
                    "emoji": "📚", "condition": lambda s: s.get("words_studied", 0) >= 1},
    "quiz_master": {"name": "🎯 Quiz Master",
                     "desc": "Selesaikan 50 quiz",
                     "emoji": "🎯",
                     "condition": lambda s: s.get("total_quiz", 0) >= 50},
    "perfect_score": {"name": "💯 Perfect",
                       "desc": "10 jawaban benar beruntun",
                       "emoji": "💯",
                       "condition": lambda s: s.get("best_combo", 0) >= 10},
    "week_streak": {"name": "📅 Weekly Warrior",
                     "desc": "Streak 7 hari",
                     "emoji": "📅",
                     "condition": lambda s: s.get("streak", 0) >= 7},
    "month_streak": {"name": "🗓️ Monthly Master",
                      "desc": "Streak 30 hari",
                      "emoji": "🗓️",
                      "condition": lambda s: s.get("streak", 0) >= 30},
    "vocabulary_50": {"name": "📖 Word Collector",
                       "desc": "Pelajari 50 kata",
                       "emoji": "📖",
                       "condition": lambda s: s.get("words_studied", 0) >= 50},
    "vocabulary_100": {"name": "🎓 Word Scholar",
                        "desc": "Pelajari 100 kata",
                        "emoji": "🎓",
                        "condition": lambda s: s.get("words_studied", 0) >= 100},
    "level_5": {"name": "⭐ Rising Star",
                 "desc": "Capai Level 5",
                 "emoji": "⭐",
                 "condition": lambda s: s.get("level", 1) >= 5},
    "level_10": {"name": "🚀 Superstar",
                  "desc": "Capai Level 10",
                  "emoji": "🚀",
                  "condition": lambda s: s.get("level", 1) >= 10},
    "daily_challenge": {"name": "🔥 Challenger",
                         "desc": "Selesaikan Daily Challenge",
                         "emoji": "🔥",
                         "condition": lambda s: s.get("daily_total", 0) >= 1},
    "coin_collector": {"name": "🪙 Rich Learner",
                        "desc": "Kumpulkan 1000 koin",
                        "emoji": "🪙",
                        "condition": lambda s: s.get("coins", 0) >= 1000},
}


def check_and_award_badges(user_id: int, stats: dict) -> list:
    """
    Cek apakah user berhak dapat badge baru.
    Return list badge yang baru didapat.
    """
    newly_earned = []

    with get_db() as conn:
        for code, badge in BADGES.items():
            # Cek apakah sudah punya
            existing = conn.execute(
                "SELECT 1 FROM user_badges WHERE user_id = ? AND badge_code = ?",
                (user_id, code)
            ).fetchone()

            if existing is None and badge["condition"](stats):
                # Berikan badge baru
                conn.execute(
                    "INSERT OR IGNORE INTO user_badges (user_id, badge_code) VALUES (?, ?)",
                    (user_id, code)
                )
                newly_earned.append(badge)

    return newly_earned


def get_user_badges(user_id: int) -> list:
    """Ambil semua badge milik user."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT badge_code, earned_at FROM user_badges
               WHERE user_id = ?
               ORDER BY earned_at DESC""",
            (user_id,)
        ).fetchall()

        result = []
        for row in rows:
            code = row["badge_code"]
            if code in BADGES:
                badge = BADGES[code].copy()
                badge["earned_at"] = row["earned_at"]
                result.append(badge)

        return result


def get_xp_for_next_level(current_level: int) -> int:
    """Hitung XP yang dibutuhkan untuk naik ke level berikutnya."""
    return (current_level * (current_level + 1)) * 50


def get_xp_progress(user_id: int) -> dict:
    """Ambil progress XP user."""
    user = get_or_create_user(user_id, "", "")
    current_xp = user["xp"]
    current_level = user["level"]

    # XP di level saat ini
    if current_level > 1:
        xp_at_current_level_start = ((current_level - 1) * current_level) * 50
    else:
        xp_at_current_level_start = 0

    xp_in_current_level = current_xp - xp_at_current_level_start
    xp_needed = get_xp_for_next_level(current_level)
    xp_at_current_level_start_next = (current_level * (current_level + 1)) * 50
    xp_in_level = xp_needed - xp_at_current_level_start
    progress_pct = min(100, round((xp_in_current_level / xp_in_level) * 100, 1))

    return {
        "current_xp": current_xp,
        "level": current_level,
        "xp_in_level": xp_in_current_level,
        "xp_needed": xp_in_level,
        "progress_pct": progress_pct
    }


def get_user_stats_dict(user_id: int) -> dict:
    """Kumpulkan semua statistik user dalam satu dict (untuk badge check)."""
    from database import get_db
    
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        if not user:
            return {}

        words_studied = conn.execute(
            "SELECT COUNT(*) as c FROM progress WHERE user_id = ?",
            (user_id,)
        ).fetchone()["c"]

        best_combo = conn.execute(
            "SELECT MAX(combo) as m FROM quiz_history WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        best_combo_val = best_combo["m"] if best_combo and best_combo["m"] else 0

        daily_total = conn.execute(
            "SELECT COUNT(DISTINCT daily_date) as c FROM users WHERE user_id = ? AND daily_date IS NOT NULL",
            (user_id,)
        ).fetchone()["c"]

        return {
            "total_quiz": user["total_quiz"],
            "total_correct": user["total_correct"],
            "level": user["level"],
            "streak": user["streak"],
            "coins": user["coins"],
            "words_studied": words_studied,
            "best_combo": best_combo_val,
            "daily_total": daily_total,
        }
