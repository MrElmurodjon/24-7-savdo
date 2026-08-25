from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

MONTHS_UZ = {
    1: 'Yanvar', 2: 'Fevral', 3: 'Mart', 4: 'Aprel',
    5: 'May', 6: 'Iyun', 7: 'Iyul', 8: 'Avgust',
    9: 'Sentabr', 10: 'Oktabr', 11: 'Noyabr', 12: 'Dekabr'
}

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


def product_actions_keyboard(product_id):
    """Mahsulot uchun inline tugmalar"""
    keyboard = [
        [
            InlineKeyboardButton("✏️ Tahrirlash", callback_data=f"edit_{product_id}"),
            InlineKeyboardButton("💵 Sotildi", callback_data=f"sold_{product_id}"),
        ],
        [
            InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_{product_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def confirm_delete_keyboard(product_id):
    """O'chirishni tasdiqlash"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ha, o'chirish", callback_data=f"confirm_delete_{product_id}"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"cancel_delete_{product_id}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
