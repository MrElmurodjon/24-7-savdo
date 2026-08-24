"""
Telegram bot — asosiy fayl
"""
import os
import sys
import logging
import django
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, filters, ContextTypes
)
from marketplace.models import BotSettings
from .states import *
from .handlers import (
    start, help_command, add_product, cancel,
    choose_category, my_products,
    # Ko'chat
    kochat_name, kochat_age, kochat_price, kochat_quantity,
    kochat_photos, kochat_location, kochat_phone, kochat_description,
    # Meva
    meva_name, meva_price, meva_photos, meva_location, meva_phone, meva_description,
    # Sabzavot
    sabzavot_name, sabzavot_price, sabzavot_photos,
    sabzavot_location, sabzavot_phone, sabzavot_description,
    # Parranda Choice
    parranda_choice,
    # Parranda
    parranda_type, parranda_quantity, parranda_weight,
    parranda_description, parranda_location, parranda_phone,
    parranda_price, parranda_photos,
    # Tuxum
    tuxum_type, tuxum_quantity, tuxum_description,
    tuxum_location, tuxum_phone, tuxum_price, tuxum_photos,
    # Confirm
    confirm,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global xato handler — barcha xatolarni loglaydi va foydalanuvchiga xabar beradi"""
    logger.error(f"Xato yuz berdi: {context.error}", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                f"⚠️ Xato yuz berdi: {str(context.error)[:200]}\n\n"
                "Qaytadan /start bosing.",
            )
        except Exception:
            pass


def create_application(token: str):
    """Bot applicationni yaratish"""
    app = Application.builder().token(token).build()

    # Conversation handler — mahsulot qo'shish
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("➕ Mahsulot qo'shish"), add_product),
        ],
        states={
            CHOOSING_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, choose_category),
            ],
            # Ko'chat states
            KOCHAT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_name),
            ],
            KOCHAT_AGE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_age),
            ],
            KOCHAT_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_price),
            ],
            KOCHAT_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_quantity),
            ],
            KOCHAT_PHOTOS: [
                MessageHandler(filters.PHOTO, kochat_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_photos),
            ],
            KOCHAT_LOCATION: [
                MessageHandler(filters.LOCATION, kochat_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_location),
            ],
            KOCHAT_PHONE: [
                MessageHandler(filters.CONTACT, kochat_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_phone),
            ],
            KOCHAT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, kochat_description),
            ],
            # Meva states
            MEVA_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, meva_name),
            ],
            MEVA_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, meva_price),
            ],
            MEVA_PHOTOS: [
                MessageHandler(filters.PHOTO, meva_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, meva_photos),
            ],
            MEVA_LOCATION: [
                MessageHandler(filters.LOCATION, meva_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, meva_location),
            ],
            MEVA_PHONE: [
                MessageHandler(filters.CONTACT, meva_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, meva_phone),
            ],
            MEVA_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, meva_description),
            ],
            # Sabzavot states
            SABZAVOT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, sabzavot_name)],
            SABZAVOT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sabzavot_price)],
            SABZAVOT_PHOTOS: [
                MessageHandler(filters.PHOTO, sabzavot_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sabzavot_photos)
            ],
            SABZAVOT_LOCATION: [
                MessageHandler(filters.LOCATION, sabzavot_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sabzavot_location)
            ],
            SABZAVOT_PHONE: [
                MessageHandler(filters.CONTACT, sabzavot_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, sabzavot_phone)
            ],
            SABZAVOT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, sabzavot_description)],
            # Parranda states
            PARRANDA_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_choice)],
            PARRANDA_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_type)],
            PARRANDA_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_quantity)],
            PARRANDA_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_weight)],
            PARRANDA_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_description)],
            PARRANDA_LOCATION: [
                MessageHandler(filters.LOCATION, parranda_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_location)
            ],
            PARRANDA_PHONE: [
                MessageHandler(filters.CONTACT, parranda_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_phone)
            ],
            PARRANDA_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_price)],
            PARRANDA_PHOTOS: [
                MessageHandler(filters.PHOTO, parranda_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, parranda_photos)
            ],
            # Tuxum states
            TUXUM_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_type)],
            TUXUM_QUANTITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_quantity)],
            TUXUM_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_description)],
            TUXUM_LOCATION: [
                MessageHandler(filters.LOCATION, tuxum_location),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_location)
            ],
            TUXUM_PHONE: [
                MessageHandler(filters.CONTACT, tuxum_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_phone)
            ],
            TUXUM_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_price)],
            TUXUM_PHOTOS: [
                MessageHandler(filters.PHOTO, tuxum_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, tuxum_photos)
            ],
            # Confirm
            CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, confirm),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            CommandHandler('start', cancel),
            MessageHandler(filters.Regex("❌ Bekor qilish"), cancel),
        ],
        allow_reentry=True,
    )

    # Handlerlarni ro'yxatdan o'tkazish
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("📋 Mening mahsulotlarim"), my_products))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ Yordam"), help_command))

    # Global error handler
    app.add_error_handler(error_handler)

    return app


def run_bot():
    """Botni ishga tushirish"""
    settings = BotSettings.get_settings()
    token = settings.bot_token

    if not token:
        from django.conf import settings as django_settings
        token = django_settings.BOT_TOKEN

    if not token:
        logger.error("❌ Bot token topilmadi! Dashboard > Sozlamalar dan token kiriting.")
        return

    logger.info("🤖 Bot ishga tushmoqda...")
    app = create_application(token)
    app.run_polling(drop_pending_updates=True, stop_signals=None)
