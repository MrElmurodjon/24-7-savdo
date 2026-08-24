## QUVA NIHOL — Ishga Tushirish

### Birinchi marta:
```
python manage.py migrate
python run.py
```

### Oddiy ishlatish:
```
python run.py
```

### Faqat Dashboard (Bot o'chiq):
```
python manage.py runserver
```

### Faqat Bot:
```
python -c "from bot.bot import run_bot; run_bot()"
```

---

### Sozlamalar:
1. `http://127.0.0.1:8000` → Login: **admin** / **admin123**
2. Dashboard → Sozlamalar → Bot token kiriting
3. Kanal ID kiriting (masalan: -1001234567890)
4. Bot kanal administratori bo'lishi kerak!

### .env fayli:
```
BOT_TOKEN=your_bot_token_here
CHANNEL_ID=-1001234567890
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```
