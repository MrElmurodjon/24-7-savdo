"""
run.py — Django + Telegram Bot ni birga ishga tushirish
Ishlatish: python run.py
"""
import os
import sys
import threading
import subprocess
import time
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_django():
    """Django dev server ni ishga tushirish"""
    print("🌐 Django server boshlanyapti: http://127.0.0.1:8000")
    subprocess.run([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])


def run_telegram_bot():
    """Telegram botni ishga tushirish"""
    time.sleep(2)  # Django ni kutib turish

    django.setup()
    from bot.bot import run_bot
    print("🤖 Telegram bot boshlanyapti...")
    run_bot()


if __name__ == '__main__':
    print("=" * 50)
    print("🌿  QUVA NIHOL — Marketplace Tizimi")
    print("=" * 50)

    # Migratsiyalarni tekshirish
    print("📦 Migratsiyalar bajarilmoqda...")
    os.system(f'{sys.executable} manage.py migrate --run-syncdb 2>/dev/null || {sys.executable} manage.py migrate')
    print("✅ Migratsiyalar tayyor\n")

    # Django va botni alohida threadlarda ishga tushirish
    django_thread = threading.Thread(target=run_django, daemon=True)
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)

    django_thread.start()
    bot_thread.start()

    print("\n" + "=" * 50)
    print("✅ Tizim ishga tushdi!")
    print("📊 Dashboard: http://127.0.0.1:8000")
    print("🔑 Login: admin / admin123")
    print("💡 Bot tokenini Dashboard > Sozlamalar dan kiriting")
    print("⛔ To'xtatish uchun: Ctrl+C")
    print("=" * 50 + "\n")

    try:
        django_thread.join()
        bot_thread.join()
    except KeyboardInterrupt:
        print("\n👋 Tizim to'xtatildi.")
