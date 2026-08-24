from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu_keyboard():
    """Asosiy menyu"""
    keyboard = [
        [KeyboardButton("➕ Mahsulot qo'shish")],
        [KeyboardButton("📋 Mening mahsulotlarim")],
        [KeyboardButton("ℹ️ Yordam")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def category_keyboard():
    """Mahsulot turi tanlash"""
    keyboard = [
        [KeyboardButton("🌱 Ko'chat"), KeyboardButton("🍎 Meva/Mahsulot")],
        [KeyboardButton("🥕 Sabzavot"), KeyboardButton("🐔 Parranda")],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def parranda_choice_keyboard():
    """Parranda yoki Tuxum tanlash"""
    keyboard = [
        [KeyboardButton("🐔 Parranda (Tirik)"), KeyboardButton("🥚 Tuxum")],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def location_keyboard():
    """Joylashuv yuborish"""
    keyboard = [
        [KeyboardButton("📍 Joylashuvimni yuborish", request_location=True)],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def phone_keyboard():
    """Telefon raqam yuborish"""
    keyboard = [
        [KeyboardButton("📞 Raqamimni ulashish", request_contact=True)],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def skip_keyboard():
    """O'tkazib yuborish"""
    keyboard = [
        [KeyboardButton("⏭️ O'tkazib yuborish")],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def confirm_keyboard():
    """Tasdiqlash"""
    keyboard = [
        [KeyboardButton("✅ Tasdiqlash va Yuborish")],
        [KeyboardButton("🔄 Qaytadan boshlash")],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def done_photos_keyboard():
    """Rasmlar yuborishni tugatish"""
    keyboard = [
        [KeyboardButton("✅ Rasmlar tayyor (davom ettirish)")],
        [KeyboardButton("❌ Bekor qilish")],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
