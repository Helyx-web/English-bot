# 🎓 English Master Bot

Telegram bot untuk belajar Bahasa Inggris yang interaktif dan menyenangkan! Dilengkapi dengan 200+ kosakata, quiz, gamification, dan Spaced Repetition System (SRS).

## ✨ Fitur

- 📚 **200+ Kosakata** dengan arti, pronunciation, dan contoh kalimat
- 📝 **Beragam Quiz**: Pilihan ganda, tebak arti, susun huruf, listening
- 🔥 **Daily Challenge** dengan bonus XP harian
- 🧠 **Spaced Repetition (SRS)** seperti Anki
- 🎮 **Gamification**: XP, Level, Badge, Leaderboard
- 🤖 **AI Tutor** untuk tanya jawab grammar
- 📊 **Progress Tracking** dengan statistik detail
- ❤️ **Favorit** untuk menyimpan kata penting
- 🔔 **Reminder** belajar harian
- 🪙 **Coins System** yang bisa ditukar materi
- 🏆 **Leaderboard** global, mingguan, bulanan
- 🔊 **Pronunciation Audio** dengan Google TTS

## 🚀 Cara Menjalankan

### 1. Dapatkan Bot Token

1. Buka Telegram, cari **@BotFather**
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Copy token yang diberikan

### 2. Setup Lokal

```bash
# Clone / download project
cd english_master_bot

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Buat file .env
cp .env.example .env
# Edit .env, isi BOT_TOKEN dan ADMIN_IDS

# Jalankan bot
python main.py
```

### 3. Mendapatkan ADMIN ID

1. Buka Telegram, cari **@userinfobot**
2. Kirih `/start`
3. Copy ID yang muncul ke file `.env`

### 4. Deploy ke Cloud (Gratis)

#### Render (Recommended)
1. Fork/upload project ke GitHub
2. Buka [render.com](https://render.com)
3. New → Web Service → pilih repo
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `python main.py`
6. Tambahkan Environment Variables: `BOT_TOKEN`, `ADMIN_IDS`
7. Deploy!

#### Railway
1. Buka [railway.app](https://railway.app)
2. New Project → Deploy from GitHub
3. Tambahkan Environment Variables
4. Deploy!

#### Koyeb
1. Buka [koyeb.com](https://koyeb.com)
2. Create Service → GitHub
3. Set command: `python main.py`
4. Tambahkan Environment Variables
5. Deploy!

## 📋 Commands

| Command | Deskripsi |
|---------|-----------|
| `/start` | Mulai bot |
| `/menu` | Menu utama |
| `/help` | Bantuan |
| `/learn` | Belajar kosakata |
| `/quiz` | Mulai quiz |
| `/daily` | Daily challenge |
| `/progress` | Lihat progres |
| `/profile` | Profil & statistik |
| `/favorite` | Kata favorit |
| `/search <kata>` | Cari kosakata |
| `/settings` | Pengaturan |
| `/admin` | Panel admin |

## 🛠️ Admin Commands

```bash
# Tambah kata baru
/addword word|meaning|pronunciation|example|example_meaning|pos|level

# Contoh:
/addword beautiful|cantik|/ˈbjuːtɪfəl/|She is beautiful|Dia cantik|Adjective|A2

# Broadcast message
/broadcast Halo semua! Tetap semangat!

# Backup database (via admin panel)
/admin → 💾 Backup DB
```

## 📁 Struktur Project

```
english_master_bot/
├── main.py              # Entry point
├── config.py            # Konfigurasi
├── database.py          # Database manager (SQLite)
├── vocab_data.py        # 200+ kosakata
├── keyboards.py         # Inline keyboard UI
├── handlers/
│   ├── basic.py         # Command dasar
│   ├── learn.py         # Belajar kosakata
│   ├── quiz.py          # Quiz system
│   ├── daily.py         # Daily challenge
│   ├── progress.py      # Progress & leaderboard
│   ├── admin.py         # Admin panel
│   └── settings_handler.py
├── utils/
│   ├── helpers.py       # Helper functions
│   └── gamification.py  # XP, Level, Badge
├── requirements.txt
├── .env.example
└── README.md
```

## 📊 Database Schema

- **users** - Data pengguna
- **vocabulary** - Bank kosakata
- **quiz_history** - Riwayat quiz
- **favorites** - Kata favorit
- **progress** - Progress + SRS
- **streak_log** - Log streak harian
- **user_badges** - Badge yang diraih
- **user_settings** - Pengaturan user

## 🎮 Gamification

### XP & Level
- +10 XP per jawaban benar
- +2 XP bonus per combo (streak jawaban benar)
- +5 XP per kata dipelajari
- +50 XP bonus daily challenge
- +50 XP bonus perfect score

### Badges
| Badge | Cara Mendapat |
|-------|---------------|
| 📚 First Step | Belajar kata pertama |
| 🎯 Quiz Master | 50 quiz selesai |
| 💯 Perfect | 10 combo benar |
| 📅 Weekly Warrior | Streak 7 hari |
| 🎓 Word Scholar | 100 kata dipelajari |
| ⭐ Rising Star | Level 5 |
| 🚀 Superstar | Level 10 |

## 📝 License

Free to use for educational purposes.

---

Made with ❤️ for Indonesian English learners
