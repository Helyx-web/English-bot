"""
Database manager menggunakan SQLite.
Gratis, ringan, tidak perlu server database.
"""
import sqlite3
import os
from datetime import datetime, date
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "english_master.db")


@contextmanager
def get_db():
    """Context manager untuk koneksi database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Hasil sebagai dict-like
    conn.execute("PRAGMA journal_mode=WAL")  # Performa lebih baik
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    """Buat semua tabel jika belum ada."""
    with get_db() as conn:
        c = conn.cursor()

        # Tabel users
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id       INTEGER PRIMARY KEY,
                username      TEXT,
                first_name    TEXT,
                xp            INTEGER DEFAULT 0,
                level         INTEGER DEFAULT 1,
                coins         INTEGER DEFAULT 0,
                streak        INTEGER DEFAULT 0,
                last_study    TEXT,
                reminder_hour INTEGER DEFAULT 8,
                joined_at     TEXT DEFAULT CURRENT_TIMESTAMP,
                total_quiz    INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                daily_done    INTEGER DEFAULT 0,
                daily_date    TEXT
            )
        """)

        # Tabel vocabulary
        c.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                word          TEXT NOT NULL,
                meaning       TEXT NOT NULL,
                pronunciation TEXT,
                example       TEXT,
                example_meaning TEXT,
                part_of_speech TEXT,
                level         TEXT DEFAULT 'A1',
                category      TEXT DEFAULT 'general',
                created_at    TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabel quiz_history
        c.execute("""
            CREATE TABLE IF NOT EXISTS quiz_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER,
                word_id     INTEGER,
                quiz_type   TEXT,
                is_correct  INTEGER DEFAULT 0,
                answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (word_id) REFERENCES vocabulary(id)
            )
        """)

        # Tabel favorites
        c.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id     INTEGER,
                word_id     INTEGER,
                added_at    TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, word_id)
            )
        """)

        # Tabel progress (kata yang sudah dipelajari)
        c.execute("""
            CREATE TABLE IF NOT EXISTS progress (
                user_id        INTEGER,
                word_id        INTEGER,
                srs_level      INTEGER DEFAULT 0,
                srs_next_review TEXT,
                times_seen     INTEGER DEFAULT 1,
                last_reviewed  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, word_id)
            )
        """)

        # Tabel streak
        c.execute("""
            CREATE TABLE IF NOT EXISTS streak_log (
                user_id    INTEGER,
                date       TEXT,
                xp_gained  INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, date)
            )
        """)

        # Tabel badges
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_badges (
                user_id    INTEGER,
                badge_code TEXT,
                earned_at  TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, badge_code)
            )
        """)

        # Tabel settings
        c.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id   INTEGER PRIMARY KEY,
                language  TEXT DEFAULT 'id',
                daily_goal INTEGER DEFAULT 10,
                theme     TEXT DEFAULT 'dark',
                notifications INTEGER DEFAULT 1
            )
        """)

        print("✅ Database initialized successfully!")


# ===== USER FUNCTIONS =====

def get_or_create_user(user_id: int, username: str, first_name: str):
    """Ambil data user atau buat baru jika belum ada."""
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        if user is None:
            conn.execute(
                """INSERT INTO users (user_id, username, first_name)
                   VALUES (?, ?, ?)""",
                (user_id, username, first_name)
            )
            conn.execute(
                """INSERT OR IGNORE INTO user_settings (user_id)
                   VALUES (?)""",
                (user_id,)
            )
            user = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()

        return dict(user)


def add_xp(user_id: int, amount: int):
    """Tambah XP ke user, auto level up kalau cukup."""
    with get_db() as conn:
        user = conn.execute(
            "SELECT xp, level FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if user is None:
            return False

        new_xp = user["xp"] + amount
        current_level = user["level"]
        new_level = current_level

        # Hitung level berdasarkan XP
        # Level 1: 0-100, Level 2: 100-300, Level 3: 300-600, etc.
        xp_needed = (current_level * (current_level + 1)) * 50
        leveled_up = False

        if new_xp >= xp_needed:
            new_level = current_level + 1
            leveled_up = True

        conn.execute(
            """UPDATE users
               SET xp = ?, level = ?
               WHERE user_id = ?""",
            (new_xp, new_level, user_id)
        )

        return {
            "leveled_up": leveled_up,
            "new_xp": new_xp,
            "new_level": new_level,
            "old_level": current_level
        }


def add_coins(user_id: int, amount: int):
    """Tambah koin ke user."""
    with get_db() as conn:
        conn.execute(
            "UPDATE users SET coins = coins + ? WHERE user_id = ?",
            (amount, user_id)
        )


# ===== VOCABULARY FUNCTIONS =====

def get_vocab_by_id(vocab_id: int):
    """Ambil satu kata by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM vocabulary WHERE id = ?", (vocab_id,)
        ).fetchone()
        return dict(row) if row else None


def get_vocab_by_level(level: str, limit: int = 10):
    """Ambil kosakata berdasarkan level."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM vocabulary WHERE level = ? ORDER BY RANDOM() LIMIT ?",
            (level, limit)
        ).fetchall()
        return [dict(r) for r in rows]


def get_random_vocab(exclude_ids: list = None, limit: int = 10):
    """Ambil kata acak."""
    with get_db() as conn:
        if exclude_ids:
            placeholders = ",".join("?" * len(exclude_ids))
            rows = conn.execute(
                f"SELECT * FROM vocabulary WHERE id NOT IN ({placeholders}) "
                f"ORDER BY RANDOM() LIMIT ?",
                exclude_ids + [limit]
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM vocabulary ORDER BY RANDOM() LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


def search_vocab(keyword: str):
    """Cari kata berdasarkan keyword."""
    keyword = f"%{keyword.lower()}%"
    with get_db() as conn:
        rows = conn.execute(
            """SELECT * FROM vocabulary
               WHERE LOWER(word) LIKE ? OR LOWER(meaning) LIKE ?
               LIMIT 20""",
            (keyword, keyword)
        ).fetchall()
        return [dict(r) for r in rows]


def get_total_vocab():
    """Hitung total kata di database."""
    with get_db() as conn:
        row = conn.execute("SELECT COUNT(*) as count FROM vocabulary").fetchone()
        return row["count"]


# ===== PROGRESS FUNCTIONS =====

def mark_word_studied(user_id: int, word_id: int):
    """Tandai kata sebagai sudah dipelajari + SRS logic."""
    from datetime import datetime, timedelta
    now = datetime.now()

    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM progress WHERE user_id = ? AND word_id = ?",
            (user_id, word_id)
        ).fetchone()

        if existing is None:
            # Baru pertama kali dipelajari
            next_review = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            conn.execute(
                """INSERT INTO progress (user_id, word_id, srs_level, srs_next_review)
                   VALUES (?, ?, 1, ?)""",
                (user_id, word_id, next_review)
            )
        else:
            # Update SRS level
            new_level = min(existing["srs_level"] + 1, 5)
            intervals = [1, 3, 7, 14, 30]  # SRS interval dalam hari
            days = intervals[min(new_level - 1, 4)]
            next_review = (now + timedelta(days=days)).strftime("%Y-%m-%d")
            conn.execute(
                """UPDATE progress
                   SET srs_level = ?,
                       srs_next_review = ?,
                       times_seen = times_seen + 1,
                       last_reviewed = ?
                   WHERE user_id = ? AND word_id = ?""",
                (new_level, next_review, now.strftime("%Y-%m-%d"),
                 user_id, word_id)
            )


def record_quiz_result(user_id: int, word_id: int,
                       quiz_type: str, is_correct: bool):
    """Catat hasil quiz."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO quiz_history (user_id, word_id, quiz_type, is_correct)
               VALUES (?, ?, ?, ?)""",
            (user_id, word_id, quiz_type, 1 if is_correct else 0)
        )
        conn.execute(
            """UPDATE users
               SET total_quiz = total_quiz + 1,
                   total_correct = total_correct + ?
               WHERE user_id = ?""",
            (1 if is_correct else 0, user_id)
        )


# ===== STREAK FUNCTIONS =====

def update_streak(user_id: int) -> dict:
    """Update streak harian user."""
    today = date.today().strftime("%Y-%m-%d")
    yesterday = (date.today().replace(day=date.today().day - 1)
                 ).strftime("%Y-%m-%d") if date.today().day > 1 else None

    with get_db() as conn:
        user = conn.execute(
            "SELECT streak, last_study FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if user is None:
            return {}

        last = user["last_study"]
        current_streak = user["streak"]

        if last == today:
            # Sudah belajar hari ini
            pass
        elif last == yesterday:
            # Streak bertambah
            current_streak += 1
            conn.execute(
                "UPDATE users SET streak = ?, last_study = ? WHERE user_id = ?",
                (current_streak, today, user_id)
            )
        else:
            # Streak reset
            current_streak = 1
            conn.execute(
                "UPDATE users SET streak = ?, last_study = ? WHERE user_id = ?",
                (current_streak, today, user_id)
            )

        # Log streak harian
        conn.execute(
            """INSERT OR REPLACE INTO streak_log (user_id, date)
               VALUES (?, ?)""",
            (user_id, today)
        )

        return {"streak": current_streak, "updated": True}


def get_or_create_user_settings(user_id: int):
    """Ambil atau buat pengaturan user."""
    with get_db() as conn:
        settings = conn.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if settings is None:
            conn.execute(
                "INSERT INTO user_settings (user_id) VALUES (?)",
                (user_id,)
            )
            settings = conn.execute(
                "SELECT * FROM user_settings WHERE user_id = ?",
                (user_id,)
            ).fetchone()

        return dict(settings)


# ===== FAVORITES =====

def add_favorite(user_id: int, word_id: int):
    """Tambah kata ke favorit."""
    with get_db() as conn:
        conn.execute(
            """INSERT OR IGNORE INTO favorites (user_id, word_id)
               VALUES (?, ?)""",
            (user_id, word_id)
        )


def remove_favorite(user_id: int, word_id: int):
    """Hapus kata dari favorit."""
    with get_db() as conn:
        conn.execute(
            "DELETE FROM favorites WHERE user_id = ? AND word_id = ?",
            (user_id, word_id)
        )


def get_favorites(user_id: int):
    """Ambil semua kata favorit user."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT v.* FROM vocabulary v
               INNER JOIN favorites f ON v.id = f.word_id
               WHERE f.user_id = ?
               ORDER BY f.added_at DESC""",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def is_favorite(user_id: int, word_id: int) -> bool:
    """Cek apakah kata sudah ada di favorit."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM favorites WHERE user_id = ? AND word_id = ?",
            (user_id, word_id)
        ).fetchone()
        return row is not None


# ===== LEADERBOARD =====

def get_leaderboard(period: str = "all", limit: int = 10):
    """
    Ambil leaderboard.
    period: 'all', 'weekly', 'monthly'
    """
    with get_db() as conn:
        if period == "all":
            rows = conn.execute(
                """SELECT user_id, username, first_name, xp, level, streak
                   FROM users
                   ORDER BY xp DESC
                   LIMIT ?""",
                (limit,)
            ).fetchall()
        elif period in ("weekly", "monthly"):
            from datetime import datetime, timedelta
            now = datetime.now()
            if period == "weekly":
                start = now - timedelta(days=7)
            else:
                start = now - timedelta(days=30)

            rows = conn.execute(
                """SELECT u.user_id, u.username, u.first_name,
                          COALESCE(SUM(s.xp_gained), 0) as xp,
                          u.level, u.streak
                   FROM users u
                   LEFT JOIN streak_log s
                   ON u.user_id = s.user_id AND s.date >= ?
                   GROUP BY u.user_id
                   ORDER BY xp DESC
                   LIMIT ?""",
                (start.strftime("%Y-%m-%d"), limit)
            ).fetchall()
        else:
            rows = []

        return [dict(r) for r in rows]


# ===== ADMIN FUNCTIONS =====

def get_all_users():
    """Ambil semua user untuk admin."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM users ORDER BY joined_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def add_vocab(word, meaning, pronunciation, example,
              example_meaning, part_of_speech, level, category="general"):
    """ Admin: tambah kata baru."""
    with get_db() as conn:
        conn.execute(
            """INSERT INTO vocabulary
               (word, meaning, pronunciation, example, example_meaning,
                part_of_speech, level, category)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (word, meaning, pronunciation, example, example_meaning,
             part_of_speech, level, category)
        )


def delete_vocab(vocab_id: int):
    """Admin: hapus kata."""
    with get_db() as conn:
        conn.execute("DELETE FROM vocabulary WHERE id = ?", (vocab_id,))


def get_stats():
    """Statistik untuk admin panel."""
    with get_db() as conn:
        total_users = conn.execute(
            "SELECT COUNT(*) as c FROM users"
        ).fetchone()["c"]
        total_vocab = conn.execute(
            "SELECT COUNT(*) as c FROM vocabulary"
        ).fetchone()["c"]
        total_quiz = conn.execute(
            "SELECT COUNT(*) as c FROM quiz_history"
        ).fetchone()["c"]
        active_today = conn.execute(
            "SELECT COUNT(*) as c FROM streak_log WHERE date = ?",
            (date.today().strftime("%Y-%m-%d"),)
        ).fetchone()["c"]

        return {
            "total_users": total_users,
            "total_vocab": total_vocab,
            "total_quiz": total_quiz,
            "active_today": active_today
}
