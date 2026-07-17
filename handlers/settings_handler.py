"""
Handler untuk pengaturan.
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from database import get_or_create_user, get_or_create_user_settings, get_db
from keyboards import settings_kb, main_menu_kb
from utils.helpers import rate_limit
from config import EMOJI

logger = logging.getLogger(__name__)


async def settings_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback untuk pengaturan."""
    query = update.callback_query
    user = update.effective_user
    await query.answer()

    settings = get_or_create_user_settings(user.id)

    text = (
        f"⚙️ **PENGATURAN**\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔔 **Reminder:** {settings['reminder_hour']:02d}:00\n"
        f"🎯 **Target Harian:** {settings['daily_goal']} kata\n\n"
        f"Pilih yang ingin diubah:"
    )

    await query.edit_message_text(
        text,
        reply_markup=settings_kb(settings["reminder_hour"]),
        parse_mode="Markdown"
    )
