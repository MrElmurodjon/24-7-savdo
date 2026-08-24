"""
run.py — Django + Telegram Bot ni birga ishga tushirish
Ishlatish: python run.py
"""
import os
import sys
import asyncio
import threading
import subprocess
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_django():
    """Django dev server ni ishga tushirish"""
    print("🌐 Django server boshlanyapti: http://0.0.0.0:8000")
    subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])


def run_telegram_bot():
    """Telegram botni ishga tushirish — o'z event loop bilan"""
    time.sleep(2)  # Django ni kutib turish

    django.setup()
    from bot.bot import create_application, BotSettings
    from django.conf import settings as django_settings

    settings = BotSettings.get_settings()
    token = settings.bot_token

    if not token:
        token = django_settings.BOT_TOKEN

    if not token:
        print("❌ Bot token topilmadi! Dashboard > Sozlamalar dan token kiriting.")
        return

    print("🤖 Telegram bot boshlanyapti...")

    async def start_bot():
        app = create_application(token)
        async with app:
            await app.start()
            await app.updater.start_polling(drop_pending_updates=True)
            print("✅ Bot polling ishga tushdi!")
            # Bot to'xtamasin
            while True:
                await asyncio.sleep(1)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_bot())
    except Exception as e:
        print(f"❌ Bot xatosi: {e}")
    finally:
        loop.close()


if __name__ == '__main__':
    print("=" * 50)
    print("🌿  24/7 SAVDO — Marketplace Tizimi")
    print("=" * 50)

    # Migratsiyalarni tekshirish
    print("📦 Migratsiyalar bajarilmoqda...")
    os.system(f'{sys.executable} manage.py migrate')
    print("✅ Migratsiyalar tayyor\n")

    # Django va botni alohida threadlarda ishga tushirish
    django_thread = threading.Thread(target=run_django, daemon=True)
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)

    django_thread.start()
    bot_thread.start()

    print("\n" + "=" * 50)
    print("✅ Tizim ishga tushdi!")
    print("📊 Dashboard: http://0.0.0.0:8000")
    print("⛔ To'xtatish uchun: Ctrl+C")
    print("=" * 50 + "\n")

    try:
        django_thread.join()
        bot_thread.join()
    except KeyboardInterrupt:
        print("\n👋 Tizim to'xtatildi.")
