"""
Telegram bot handlerlari — barcha conversation logikasi
Django ORM async muhitda sync_to_async orqali ishlatiladi
Rasmlar Telegramdan yuklab olinib, Django media ga saqlanadi
"""
import os
import sys
import logging
import uuid
import django
from pathlib import Path
from asgiref.sync import sync_to_async
from telegram import Update, Message
from telegram.ext import ContextTypes, ConversationHandler

# Django sozlamalari
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings as django_settings
from django.core.files.base import ContentFile
from marketplace.models import Product, ProductImage, BotSettings
from .states import *
from .keyboards import *
from .keyboards import parranda_choice_keyboard
from .utils import standardize_product_name, reverse_geocode
from .channel import send_product_to_channel

logger = logging.getLogger(__name__)

# Foydalanuvchi ma'lumotlari vaqtincha saqlanadi
user_data_store = {}


# ====== Django ORM uchun async wrapperlar ======
@sync_to_async
def get_bot_welcome():
    s = BotSettings.get_settings()
    msg = s.welcome_message or "🌿 24/7 Savdo Marketplacega Xush Kelibsiz!"
    if "Quva Nihol" in msg:
        s.welcome_message = msg.replace("Quva Nihol", "24/7 Savdo")
        s.save()
        msg = s.welcome_message
    return msg

@sync_to_async
def get_channel_url():
    s = BotSettings.get_settings()
    return s.channel_url if s else ""

@sync_to_async
def create_product(data, user_id, username, full_name):
    # Standart nomlash va geocoding
    original_name = data.get('name', '')
    std_name = standardize_product_name(original_name)
    lat = data.get('location_lat')
    lon = data.get('location_lon')
    region, district = reverse_geocode(lat, lon)

    product = Product.objects.create(
        category=data.get('category', 'meva'),
        name=std_name, # <-- Asl ismni ham to'g'rilanganiga almashtiramiz
        standardized_name=std_name,
        price=data.get('price', 0),
        quantity=data.get('quantity'),
        age=data.get('age', ''),
        weight=data.get('weight', ''),
        gender=data.get('gender', ''),
        milk_yield=data.get('milk_yield', ''),
        phone=data.get('phone', ''),
        location_lat=lat,
        location_lon=lon,
        location_text=data.get('location_text', ''),
        region=region,
        district=district,
        description=data.get('description', ''),
        telegram_user_id=user_id,
        telegram_username=username or '',
        telegram_full_name=full_name or '',
    )
    return product

@sync_to_async
def save_product_image(product, image_bytes, file_id, order):
    """Rasmni Django media ga saqlash"""
    filename = f"product_{product.id}_{order}_{uuid.uuid4().hex[:8]}.jpg"
    img = ProductImage(
        product=product,
        telegram_file_id=file_id,
        order=order
    )
    img.image.save(filename, ContentFile(image_bytes), save=True)
    return img

@sync_to_async
def get_product_images(product):
    return list(product.images.all())

@sync_to_async
def save_product_message_id(product, msg_id):
    product.telegram_message_id = msg_id
    product.save(update_fields=['telegram_message_id'])

@sync_to_async
def get_user_products(user_id):
    return list(
        Product.objects.filter(
            telegram_user_id=user_id, is_active=True
        ).order_by('-created_at')[:10]
    )


# ====== HANDLERS ======

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    welcome = await get_bot_welcome()

    await update.message.reply_text(
        f"{welcome}\n\n"
        f"📌 Bu bot orqali ko'chat va meva-sabzavotlaringizni sotishingiz mumkin.\n\n"
        f"✅ Ma'lumotlaringiz avtomatik ravishda kanalga joylashtiriladi.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Yordam"""
    await update.message.reply_text(
        "📖 <b>Yordam</b>\n\n"
        "➕ <b>Mahsulot qo'shish</b> — yangi ko'chat yoki meva qo'shish\n"
        "📋 <b>Mening mahsulotlarim</b> — qo'shgan mahsulotlaringiz ro'yxati\n\n"
        "❓ Savol bo'lsa: @admin ga murojaat qiling",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mahsulot qo'shishni boshlash"""
    user_id = update.effective_user.id
    user_data_store[user_id] = {'photos': [], 'photo_bytes': []}

    await update.message.reply_text(
        "📦 <b>Mahsulot turini tanlang:</b>",
        parse_mode='HTML',
        reply_markup=category_keyboard()
    )
    return CHOOSING_CATEGORY


async def choose_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kategoriya tanlash"""
    user_id = update.effective_user.id
    text = update.message.text

    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)

    if "Ko'chat" in text or "kochat" in text.lower():
        user_data_store[user_id]['category'] = 'kochat'
        await update.message.reply_text(
            "🌱 <b>Ko'chat qo'shish</b>\n\n"
            "1️⃣ Ko'chat turini kiriting:\n"
            "<i>Masalan: Olma, Nok, Gilos, Terak...</i>",
            parse_mode='HTML',
            reply_markup=skip_keyboard()
        )
        return KOCHAT_NAME

    elif "Meva" in text or "Mahsulot" in text:
        user_data_store[user_id]['category'] = 'meva'
        await update.message.reply_text(
            "🍎 <b>Meva/Mahsulot qo'shish</b>\n\n"
            "1️⃣ Meva/Mahsulot turini kiriting:\n"
            "<i>Masalan: Olma, Shaftoli, Uzum, Bodring...</i>",
            parse_mode='HTML',
            reply_markup=skip_keyboard()
        )
        return MEVA_NAME

    elif "Sabzavot" in text:
        user_data_store[user_id]['category'] = 'sabzavot'
        await update.message.reply_text(
            "🥕 <b>Sabzavot qo'shish</b>\n\n"
            "1️⃣ Sabzavot turini kiriting:\n"
            "<i>Masalan: Kartoshka, Sabzi, Piyoz...</i>",
            parse_mode='HTML',
            reply_markup=skip_keyboard()
        )
        return SABZAVOT_NAME

    elif "Parranda" in text:
        await update.message.reply_text(
            "🐔 <b>Parranda qo'shish</b>\n\n"
            "Tirik parranda sotyapsizmi yoki tuxumini?",
            parse_mode='HTML',
            reply_markup=parranda_choice_keyboard()
        )
        return PARRANDA_CHOICE

    elif "Bog'" in text or "Daraxt" in text:
        user_data_store[user_id]['category'] = 'daraxt'
        await update.message.reply_text(
            "🌳 <b>Bog'/Daraxt (Taxminiy hosil hisobi)</b>\n\n"
            "1️⃣ Qanday daraxt?\n<i>Masalan: Olma, Nok, Gilos...</i>",
            parse_mode='HTML',
            reply_markup=skip_keyboard()
        )
        return DARAXT_TYPE

    else:
        await update.message.reply_text("❗ Iltimos, quyidagi tugmalardan birini tanlang!")
        return CHOOSING_CATEGORY


# ===================== KO'CHAT HANDLERS =====================

async def kochat_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if "❌" in update.message.text or "Bekor" in update.message.text:
        return await cancel(update, context)
    user_data_store[user_id]['name'] = update.message.text
    await update.message.reply_text(
        "2️⃣ Ko'chatning <b>yoshini</b> kiriting:\n"
        "<i>Masalan: 1 yil, 2 yil, 6 oy...</i>",
        parse_mode='HTML',
        reply_markup=skip_keyboard()
    )
    return KOCHAT_AGE


async def kochat_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    if "O'tkazib" not in text:
        user_data_store[user_id]['age'] = text
    await update.message.reply_text(
        "3️⃣ Ko'chatning <b>narxini</b> kiriting (so'mda):\n"
        "<i>Masalan: 25000</i>",
        parse_mode='HTML',
        reply_markup=skip_keyboard()
    )
    return KOCHAT_PRICE


async def kochat_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    try:
        price = float(text.replace(' ', '').replace(',', ''))
        user_data_store[user_id]['price'] = price
    except ValueError:
        await update.message.reply_text("❗ Iltimos, faqat raqam kiriting! Masalan: 25000")
        return KOCHAT_PRICE
    await update.message.reply_text(
        "4️⃣ Ko'chatlar <b>sonini</b> kiriting (dona):\n"
        "<i>Masalan: 50</i>",
        parse_mode='HTML',
        reply_markup=skip_keyboard()
    )
    return KOCHAT_QUANTITY


async def kochat_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    if "O'tkazib" not in text:
        try:
            user_data_store[user_id]['quantity'] = int(text)
        except ValueError:
            await update.message.reply_text("❗ Iltimos, faqat raqam kiriting!")
            return KOCHAT_QUANTITY
    await update.message.reply_text(
        "5️⃣ Ko'chatning <b>rasmlarini</b> yuboring 📸\n"
        "⚠️ Kamida 2 ta rasm yuborish shart!\n\n"
        "Barcha rasmlarni yuborganingizdan so'ng tugmani bosing 👇",
        parse_mode='HTML',
        reply_markup=done_photos_keyboard()
    )
    return KOCHAT_PHOTOS


async def _handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id, next_state, next_msg, next_markup):
    """Rasmlarni qabul qilish (umumiy)"""
    if update.message.text:
        text = update.message.text
        if "❌" in text or "Bekor" in text:
            return await cancel(update, context)
        if "Rasmlar tayyor" in text or "davom" in text:
            photos = user_data_store[user_id].get('photos', [])
            if len(photos) < 2:
                await update.message.reply_text(
                    f"❗ Kamida 2 ta rasm kerak! Hozir {len(photos)} ta yuborilgan.\n"
                    "Yana rasm yuboring 👇"
                )
                return None  # qolsin
            await update.message.reply_text(next_msg, parse_mode='HTML', reply_markup=next_markup)
            return next_state

    if update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id

        # Rasmni yuklab olish
        try:
            file = await context.bot.get_file(file_id)
            photo_bytearray = await file.download_as_bytearray()
            photo_bytes = bytes(photo_bytearray)
        except Exception as e:
            logger.error(f"Rasm yuklab olishda xato: {e}")
            photo_bytes = None

        user_data_store[user_id]['photos'].append(file_id)
        if 'photo_bytes' not in user_data_store[user_id]:
            user_data_store[user_id]['photo_bytes'] = []
        user_data_store[user_id]['photo_bytes'].append(photo_bytes)

        count = len(user_data_store[user_id]['photos'])
        if count < 2:
            msg = f"✅ Rasm qabul qilindi ({count} ta)\nYana rasm yuboring 👇"
        else:
            msg = f"✅ Rasm qabul qilindi ({count} ta)\nTayyor tugmasini bosing yoki yana rasm qo'shishingiz mumkin"
        await update.message.reply_text(msg, reply_markup=done_photos_keyboard())
        return None  # qolsin

    await update.message.reply_text("📸 Iltimos, rasm yuboring!")
    return None


async def kochat_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = await _handle_photos(
        update, context, user_id,
        KOCHAT_LOCATION,
        "6️⃣ 📍 <b>Manzilni yuboring</b>\nTelegram location funksiyasidan foydalaning 👇",
        location_keyboard()
    )
    return result if result is not None else KOCHAT_PHOTOS


async def kochat_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text):
        return await cancel(update, context)
    if update.message.location:
        loc = update.message.location
        user_data_store[user_id]['location_lat'] = loc.latitude
        user_data_store[user_id]['location_lon'] = loc.longitude
        user_data_store[user_id]['location_text'] = f"{loc.latitude:.4f}, {loc.longitude:.4f}"
        await update.message.reply_text(
            "✅ Manzil qabul qilindi!\n\n"
            "7️⃣ 📞 <b>Telefon raqamingizni kiriting</b>\n"
            "<i>Masalan: +998901234567</i>",
            parse_mode='HTML',
            reply_markup=phone_keyboard()
        )
        return KOCHAT_PHONE
    else:
        await update.message.reply_text("📍 Joylashuvingizni yuboring!", reply_markup=location_keyboard())
        return KOCHAT_LOCATION


async def kochat_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text:
        text = update.message.text
        if "❌" in text or "Bekor" in text:
            return await cancel(update, context)
        user_data_store[user_id]['phone'] = text
    elif update.message.contact:
        user_data_store[user_id]['phone'] = update.message.contact.phone_number
    await update.message.reply_text(
        "8️⃣ 📝 <b>Qo'shimcha ma'lumot kiriting</b> (ixtiyoriy):\n"
        "<i>Masalan: Sog'lom, kasalligi yo'q, organik...</i>",
        parse_mode='HTML',
        reply_markup=skip_keyboard()
    )
    return KOCHAT_DESCRIPTION


async def kochat_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    if "O'tkazib" not in text:
        user_data_store[user_id]['description'] = text
    return await show_confirm(update, context, user_id)


# ===================== MEVA HANDLERS =====================

async def meva_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if "❌" in update.message.text or "Bekor" in update.message.text:
        return await cancel(update, context)
    user_data_store[user_id]['name'] = update.message.text
    await update.message.reply_text(
        "2️⃣ <b>Narxini</b> kiriting (so'mda):\n<i>Masalan: 8000 (kg uchun)</i>",
        parse_mode='HTML', reply_markup=skip_keyboard()
    )
    return MEVA_PRICE


async def meva_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    try:
        price = float(text.replace(' ', '').replace(',', ''))
        user_data_store[user_id]['price'] = price
    except ValueError:
        await update.message.reply_text("❗ Iltimos, faqat raqam kiriting!")
        return MEVA_PRICE
    await update.message.reply_text(
        "3️⃣ 📸 <b>Rasmlarni yuboring</b>\n⚠️ Kamida 2 ta rasm kerak!",
        parse_mode='HTML', reply_markup=done_photos_keyboard()
    )
    return MEVA_PHOTOS


async def meva_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    result = await _handle_photos(
        update, context, user_id,
        MEVA_LOCATION,
        "4️⃣ 📍 <b>Manzilni yuboring</b>",
        location_keyboard()
    )
    return result if result is not None else MEVA_PHOTOS


async def meva_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text):
        return await cancel(update, context)
    if update.message.location:
        loc = update.message.location
        user_data_store[user_id]['location_lat'] = loc.latitude
        user_data_store[user_id]['location_lon'] = loc.longitude
        user_data_store[user_id]['location_text'] = f"{loc.latitude:.4f}, {loc.longitude:.4f}"
        await update.message.reply_text(
            "✅ Manzil qabul qilindi!\n\n5️⃣ 📞 <b>Telefon raqamingizni kiriting</b>",
            parse_mode='HTML', reply_markup=phone_keyboard()
        )
        return MEVA_PHONE
    else:
        await update.message.reply_text("📍 Joylashuvingizni yuboring!", reply_markup=location_keyboard())
        return MEVA_LOCATION


async def meva_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text:
        text = update.message.text
        if "❌" in text or "Bekor" in text:
            return await cancel(update, context)
        user_data_store[user_id]['phone'] = text
    elif update.message.contact:
        user_data_store[user_id]['phone'] = update.message.contact.phone_number
    await update.message.reply_text(
        "6️⃣ 📝 <b>Qo'shimcha ma'lumot</b> (ixtiyoriy):",
        parse_mode='HTML', reply_markup=skip_keyboard()
    )
    return MEVA_DESCRIPTION


async def meva_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    if "O'tkazib" not in text:
        user_data_store[user_id]['description'] = text
    return await show_confirm(update, context, user_id)


# ===================== TASDIQLASH =====================

async def show_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    data = user_data_store.get(user_id, {})
    category = data.get('category', '')
    price_fmt = f"{int(data.get('price', 0)):,}".replace(',', ' ')
    photos_count = len(data.get('photos', []))

    if category == 'kochat':
        summary = (
            f"📋 <b>Ma'lumotlarni tekshiring:</b>\n\n"
            f"🏷️ Tur: Ko'chat\n"
            f"🌿 Nomi: {data.get('name', '—')}\n"
            f"📅 Yoshi: {data.get('age', '—')}\n"
            f"💰 Narxi: {price_fmt} so'm\n"
            f"📦 Soni: {data.get('quantity', '—')} dona\n"
            f"📍 Manzil: {'Bor ✅' if data.get('location_lat') else '—'}\n"
            f"📸 Rasmlar: {photos_count} ta\n"
            f"📞 Telefon: {data.get('phone', '—')}\n"
            f"📝 Qo'shimcha: {data.get('description', '—')}"
        )
    elif category == 'sabzavot':
        summary = (
            f"📋 <b>Ma'lumotlarni tekshiring:</b>\n\n"
            f"🏷️ Tur: Sabzavot\n"
            f"🥕 Nomi: {data.get('name', '—')}\n"
            f"💰 Narxi: {price_fmt} so'm\n"
            f"📍 Manzil: {'Bor ✅' if data.get('location_lat') else '—'}\n"
            f"📸 Rasmlar: {photos_count} ta\n"
            f"📞 Telefon: {data.get('phone', '—')}\n"
            f"📝 Qo'shimcha: {data.get('description', '—')}"
        )
    elif category == 'parranda':
        summary = (
            f"📋 <b>Ma'lumotlarni tekshiring:</b>\n\n"
            f"🏷️ Tur: Parranda\n"
            f"🐔 Nomi: {data.get('name', '—')}\n"
            f"📦 Soni: {data.get('quantity', '—')} ta\n"
            f"⚖️ Og'irligi: {data.get('weight', '—')}\n"
            f"💰 Narxi: {price_fmt} so'm\n"
            f"📍 Manzil: {'Bor ✅' if data.get('location_lat') else '—'}\n"
            f"📸 Rasmlar: {photos_count} ta\n"
            f"📞 Telefon: {data.get('phone', '—')}\n"
            f"📝 Qo'shimcha: {data.get('description', '—')}"
        )
    elif category == 'tuxum':
        summary = (
            f"📋 <b>Ma'lumotlarni tekshiring:</b>\n\n"
            f"🏷️ Tur: Tuxum\n"
            f"🥚 Nomi: {data.get('name', '—')}\n"
            f"📦 Soni: {data.get('quantity', '—')} ta\n"
            f"💰 Narxi: {price_fmt} so'm\n"
            f"📍 Manzil: {'Bor ✅' if data.get('location_lat') else '—'}\n"
            f"📸 Rasmlar: {photos_count} ta (Talab: 2 ta)\n"
            f"📞 Telefon: {data.get('phone', '—')}\n"
            f"📝 Qo'shimcha: {data.get('description', '—')}"
        )
    else:
        summary = (
            f"📋 <b>Ma'lumotlarni tekshiring:</b>\n\n"
            f"🏷️ Tur: Meva/Mahsulot\n"
            f"🍎 Nomi: {data.get('name', '—')}\n"
            f"💰 Narxi: {price_fmt} so'm\n"
            f"📍 Manzil: {'Bor ✅' if data.get('location_lat') else '—'}\n"
            f"📸 Rasmlar: {photos_count} ta\n"
            f"📞 Telefon: {data.get('phone', '—')}\n"
            f"📝 Qo'shimcha: {data.get('description', '—')}"
        )

    await update.message.reply_text(summary, parse_mode='HTML', reply_markup=confirm_keyboard())
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)

    if "Qaytadan" in text:
        user_data_store[user_id] = {'photos': [], 'photo_bytes': []}
        await update.message.reply_text("🔄 Qaytadan boshlanmoqda...", reply_markup=category_keyboard())
        return CHOOSING_CATEGORY

    if "Tasdiqlash" in text or "Yuborish" in text:
        data = user_data_store.get(user_id, {})
        await update.message.reply_text("⏳ Ma'lumotlar saqlanmoqda...")

        try:
            if data.get('category') == 'daraxt':
                orchard = await create_orchard(
                    data, user_id,
                    update.effective_user.username,
                    update.effective_user.full_name,
                )
                logger.info(f"Daraxt qo'shildi: ID={orchard.id}")
                
                await update.message.reply_text(
                    f"🎉 <b>Muvaffaqiyatli!</b>\n\n"
                    f"✅ Bog' / Daraxt ma'lumotlari saqlandi.\n"
                    f"Dashboarddagi Taxminiy Hosil bo'limida ko'rinadi.\n\n"
                    f"Yana qo'shish uchun tugmani bosing 👇",
                    parse_mode='HTML',
                    reply_markup=main_menu_keyboard()
                )
            else:
                # Mahsulot yaratish
                product = await create_product(
                    data, user_id,
                    update.effective_user.username,
                    update.effective_user.full_name,
                )
                logger.info(f"Mahsulot yaratildi: ID={product.id}, {product.name}")

                # Rasmlarni saqlash (fayl sifatida + file_id)
                images = []
                photo_ids = data.get('photos', [])
                photo_bytes_list = data.get('photo_bytes', [])

                for i, file_id in enumerate(photo_ids):
                    pb = photo_bytes_list[i] if i < len(photo_bytes_list) else None
                    if pb:
                        img = await save_product_image(product, pb, file_id, i)
                    else:
                        # Faqat file_id bilan
                        img = await save_product_image(product, b'', file_id, i)
                    images.append(img)

                logger.info(f"Rasmlar saqlandi: {len(images)} ta")

                # Kanalga yuborish
                msg_id = await send_product_to_channel(context.bot, product, images)
                if msg_id:
                    await save_product_message_id(product, msg_id)
                    logger.info(f"Kanalga yuborildi: msg_id={msg_id}")

                channel_url = await get_channel_url()
                channel_text = ""
                if msg_id:
                    channel_text = "✅ Kanalga joylashtirildi\n"
                    if channel_url:
                        channel_text += f"👀 Siz e'loningizni bu yerdagi kanaldan ko'rishingiz mumkin: {channel_url}\n"
                else:
                    channel_text = "⚠️ Kanalga joylashtirishda xato (sozlamalarni tekshiring)\n"

                await update.message.reply_text(
                    f"🎉 <b>Muvaffaqiyatli!</b>\n\n"
                    f"✅ Ma'lumotlar saqlandi\n"
                    f"{channel_text}\n"
                    f"Yana mahsulot qo'shish uchun tugmani bosing 👇",
                    parse_mode='HTML',
                    reply_markup=main_menu_keyboard(),
                    disable_web_page_preview=True
                )

        except Exception as e:
            logger.error(f"Saqlashda xato: {e}", exc_info=True)
            await update.message.reply_text(
                f"❌ Xato yuz berdi: {str(e)[:300]}\nQaytadan urinib ko'ring.",
                reply_markup=main_menu_keyboard()
            )

        finally:
            if user_id in user_data_store:
                del user_data_store[user_id]

        return ConversationHandler.END

    return CONFIRM


async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    products = await get_user_products(user_id)

    if not products:
        await update.message.reply_text(
            "📭 Sizda hali mahsulot yo'q.\n➕ Mahsulot qo'shish tugmasini bosing!",
            reply_markup=main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        f"📋 <b>Sizning mahsulotlaringiz:</b> {len(products)} ta",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )

    CAT_ICONS = {
        'kochat': '🌱', 'meva': '🍎', 'sabzavot': '🥕',
        'parranda': '🐔', 'tuxum': '🥚'
    }

    for p in products:
        price_fmt = f"{int(p.price):,}".replace(',', ' ')
        icon = CAT_ICONS.get(p.category, '📦')
        loc = p.location_text or (f"📍 Koordinata bor" if p.location_lat else "—")
        desc = f"\n📝 {p.description}" if p.description else ""

        sold_tag = "❌ <b>SOTILDI</b> ❌\n\n" if getattr(p, 'is_sold', False) else ""
        text = (
            f"{sold_tag}{icon} <b>{p.name}</b>\n"
            f"💰 Narx: {price_fmt} so'm\n"
            f"📞 Tel: {p.phone}\n"
            f"📍 Manzil: {loc}"
            f"{desc}\n"
            f"📅 {p.created_at.strftime('%d.%m.%Y')}"
        )
        await update.message.reply_text(
            text,
            parse_mode='HTML',
            reply_markup=product_actions_keyboard(p.id, p.is_sold)
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_data_store:
        del user_data_store[user_id]
    await update.message.reply_text(
        "❌ Bekor qilindi.\nBosh menyuga qaytdingiz.",
        reply_markup=main_menu_keyboard()
    )
    return ConversationHandler.END


# ================= SABZAVOT HANDLERS =================
async def sabzavot_name(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    user_data_store[user_id]['name'] = text
    await update.message.reply_text("💰 Narxini kiriting (so'mda):\n<i>Faqat raqam yozing, masalan: 5000000</i>", parse_mode='HTML', reply_markup=skip_keyboard())
    return SABZAVOT_PRICE

async def sabzavot_price(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    try:
        user_data_store[user_id]['price'] = float(text.replace(' ', '').replace(',', ''))
    except ValueError:
        await update.message.reply_text("❗ Iltimos, faqat raqam kiriting! Masalan: 5000")
        return SABZAVOT_PRICE
    await update.message.reply_text("📸 Sabzavot rasmlarini yuboring.\nBarcha rasmlarni yuborib bo'lgach, 'Rasmlar tayyor' tugmasini bosing.", parse_mode='HTML', reply_markup=done_photos_keyboard())
    return SABZAVOT_PHOTOS

async def sabzavot_photos(update, context):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.text and "tayyor" in update.message.text.lower():
        if not user_data_store[user_id].get('photos'):
            await update.message.reply_text("Iltimos, kamida 1 ta rasm yuboring yoki 'O'tkazib yuborish' uchun yozing (Hozircha majburiy emas, lekin rasm kutilmoqda).", reply_markup=done_photos_keyboard())
            return SABZAVOT_PHOTOS
        await update.message.reply_text("📍 Joylashuvingizni yuboring (yoki matn shaklida yozing):", reply_markup=location_keyboard())
        return SABZAVOT_LOCATION
    
    if update.message.photo:
        photo = update.message.photo[-1]
        user_data_store[user_id].setdefault('photos', []).append(photo.file_id)
        return SABZAVOT_PHOTOS
        
    await update.message.reply_text("Iltimos, rasm yuboring yoki 'Rasmlar tayyor' tugmasini bosing.")
    return SABZAVOT_PHOTOS

async def sabzavot_location(update, context):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.location:
        user_data_store[user_id]['location_lat'] = update.message.location.latitude
        user_data_store[user_id]['location_lon'] = update.message.location.longitude
    elif update.message.text:
        user_data_store[user_id]['location_text'] = update.message.text
    await update.message.reply_text("📞 Telefon raqamingizni yuboring (yoki yozib qoldiring):", reply_markup=phone_keyboard())
    return SABZAVOT_PHONE

async def sabzavot_phone(update, context):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.contact:
        user_data_store[user_id]['phone'] = update.message.contact.phone_number
    elif update.message.text:
        user_data_store[user_id]['phone'] = update.message.text
    await update.message.reply_text("📝 Qo'shimcha ma'lumot yozing (ixtiyoriy):", reply_markup=skip_keyboard())
    return SABZAVOT_DESCRIPTION

async def sabzavot_description(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    if "O'tkazib" not in text: user_data_store[user_id]['description'] = text
    return await show_confirm(update, context, user_id)


# ================= PARRANDA HANDLERS =================
async def parranda_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    
    if "Tuxum" in text:
        user_data_store[user_id]['category'] = 'tuxum'
        await update.message.reply_text("🥚 Qanday parranda tuxumi?\n<i>Masalan: Tovuq, Bedana, Guli-guli</i>", parse_mode='HTML', reply_markup=skip_keyboard())
        return TUXUM_TYPE
    else:
        user_data_store[user_id]['category'] = 'parranda'
        await update.message.reply_text("🐔 Parranda turini yozing:\n<i>Masalan: Tovuq, G'oz, Kurka</i>", parse_mode='HTML', reply_markup=skip_keyboard())
        return PARRANDA_TYPE

async def parranda_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    user_data_store[user_id]['name'] = text
    await update.message.reply_text("🔢 Nechta (soni)?", reply_markup=skip_keyboard())
    return PARRANDA_QUANTITY

async def parranda_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    if "O'tkazib" not in text:
        try:
            user_data_store[user_id]['quantity'] = int(text)
        except ValueError:
            await update.message.reply_text("❗ Faqat raqam kiriting!")
            return PARRANDA_QUANTITY
    await update.message.reply_text("⚖️ O'rtacha og'irligi/massasi qancha?\n<i>Masalan: 2.5 kg</i>", parse_mode='HTML', reply_markup=skip_keyboard())
    return PARRANDA_WEIGHT

async def parranda_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    if "O'tkazib" not in text: user_data_store[user_id]['weight'] = text
    await update.message.reply_text("📝 Qo'shimcha ma'lumot (ixtiyoriy):", reply_markup=skip_keyboard())
    return PARRANDA_DESCRIPTION

async def parranda_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    if "O'tkazib" not in text: user_data_store[user_id]['description'] = text
    await update.message.reply_text("📍 Joylashuvingizni yuboring:", reply_markup=location_keyboard())
    return PARRANDA_LOCATION

async def parranda_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.location:
        user_data_store[user_id]['location_lat'] = update.message.location.latitude
        user_data_store[user_id]['location_lon'] = update.message.location.longitude
    elif update.message.text:
        user_data_store[user_id]['location_text'] = update.message.text
    await update.message.reply_text("📞 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
    return PARRANDA_PHONE

async def parranda_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.contact:
        user_data_store[user_id]['phone'] = update.message.contact.phone_number
    elif update.message.text:
        user_data_store[user_id]['phone'] = update.message.text
    await update.message.reply_text("💰 Narxini kiriting (so'mda):", reply_markup=skip_keyboard())
    return PARRANDA_PRICE

async def parranda_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    try:
        user_data_store[user_id]['price'] = float(text.replace(' ', '').replace(',', ''))
    except ValueError:
        await update.message.reply_text("❗ Iltimos, faqat raqam kiriting!")
        return PARRANDA_PRICE
    await update.message.reply_text("📸 Parrandaning rasmlarini yuboring.\n⚠️ Kamida 2 ta rasm yuborish shart!\nBarcha rasmlarni yuborganingizdan so'ng tugmani bosing 👇", reply_markup=done_photos_keyboard())
    return PARRANDA_PHOTOS

async def parranda_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _handle_photos(update, context, update.effective_user.id, CONFIRM, "Tasdiqlash", confirm_keyboard())

# ================= TUXUM HANDLERS =================
async def tuxum_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    user_data_store[user_id]['name'] = f"{text} tuxumi"
    await update.message.reply_text("🔢 Nechta (soni)?", reply_markup=skip_keyboard())
    return TUXUM_QUANTITY

async def tuxum_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    if "O'tkazib" not in text:
        try:
            user_data_store[user_id]['quantity'] = int(text)
        except ValueError:
            await update.message.reply_text("❗ Faqat raqam kiriting!")
            return TUXUM_QUANTITY
    await update.message.reply_text("📝 Qo'shimcha ma'lumot (ixtiyoriy):", reply_markup=skip_keyboard())
    return TUXUM_DESCRIPTION

async def tuxum_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    if "O'tkazib" not in text: user_data_store[user_id]['description'] = text
    await update.message.reply_text("📍 Joylashuvingizni yuboring:", reply_markup=location_keyboard())
    return TUXUM_LOCATION

async def tuxum_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.location:
        user_data_store[user_id]['location_lat'] = update.message.location.latitude
        user_data_store[user_id]['location_lon'] = update.message.location.longitude
    elif update.message.text:
        user_data_store[user_id]['location_text'] = update.message.text
    await update.message.reply_text("📞 Telefon raqamingizni yuboring:", reply_markup=phone_keyboard())
    return TUXUM_PHONE

async def tuxum_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text): return await cancel(update, context)
    if update.message.contact:
        user_data_store[user_id]['phone'] = update.message.contact.phone_number
    elif update.message.text:
        user_data_store[user_id]['phone'] = update.message.text
    await update.message.reply_text("💰 Narxini kiriting (so'mda):", reply_markup=skip_keyboard())
    return TUXUM_PRICE

async def tuxum_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text: return await cancel(update, context)
    try:
        user_data_store[user_id]['price'] = float(text.replace(' ', '').replace(',', ''))
    except ValueError:
        await update.message.reply_text("❗ Iltimos, faqat raqam kiriting!")
        return TUXUM_PRICE
    await update.message.reply_text("📸 Tuxum rasmlarini yuboring.\n⚠️ Aynan 2 ta rasm yuborish shart!\nIkkalasini ham yuborganingizdan so'ng tugmani bosing 👇", reply_markup=done_photos_keyboard())
    return TUXUM_PHOTOS

async def tuxum_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Rasmlarni qabul qilish xuddi boshqasi kabi, lekin 2 ta rasm tekshiruvi bo'ladi
    if update.message.text:
        text = update.message.text
        if "❌" in text or "Bekor" in text: return await cancel(update, context)
        if "tayyor" in text.lower():
            photos = user_data_store[user_id].get('photos', [])
            if len(photos) != 2:
                await update.message.reply_text(f"⚠️ Siz hozir {len(photos)} ta rasm yubordingiz. Iltimos, rasmlar soni AYNAN 2 ta bo'lishi kerak!")
                return TUXUM_PHOTOS
            await update.message.reply_text("Ma'lumotlar saqlashga tayyor. Tasdiqlaysizmi?", reply_markup=confirm_keyboard())
            return CONFIRM
        
        await update.message.reply_text("Iltimos, rasm yuboring yoki 'Rasmlar tayyor' tugmasini bosing.")
        return TUXUM_PHOTOS
        
    if update.message.photo:
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        if 'photos' not in user_data_store[user_id]:
            user_data_store[user_id]['photos'] = []
            user_data_store[user_id]['photo_bytes'] = []
            
        user_data_store[user_id]['photos'].append(file_id)
        try:
            new_file = await context.bot.get_file(file_id)
            byte_arr = await new_file.download_as_bytearray()
            user_data_store[user_id]['photo_bytes'].append(byte_arr)
        except Exception as e:
            logger.error(f"Rasm yuklashda xato: {e}")
            
        count = len(user_data_store[user_id]['photos'])
        if count == 2:
             await update.message.reply_text(f"✅ {count} ta rasm qabul qilindi. Tasdiqlash uchun tugmani bosing 👇", reply_markup=done_photos_keyboard())
        elif count > 2:
             await update.message.reply_text(f"⚠️ Aynan 2 ta rasm so'ralgan edi. Siz {count} ta yubordingiz. Ortiqchalari olinmaydi. Tasdiqlash uchun tugmani bosing 👇")
        else:
             await update.message.reply_text(f"✅ {count}-rasm qabul qilindi. Yana 1 ta rasm yuboring.")
        return TUXUM_PHOTOS


# ================= DARAXT / BOG' HANDLERS =================

@sync_to_async
def create_orchard(data, user_id, username, full_name):
    from marketplace.models import OrchardRecord
    from .utils import reverse_geocode
    lat = data.get('location_lat')
    lon = data.get('location_lon')
    region, district = reverse_geocode(lat, lon)
    return OrchardRecord.objects.create(
        tree_type=data.get('tree_type', ''),
        tree_count=data.get('tree_count', 1),
        tree_age=data.get('tree_age', 1),
        bearing_age=data.get('bearing_age', 1),
        ready_month=data.get('ready_month', 1),
        phone=data.get('phone', ''),
        location_lat=lat,
        location_lon=lon,
        location_text=data.get('location_text', ''),
        region=region,
        district=district,
        description=data.get('description', ''),
        telegram_user_id=user_id,
        telegram_username=username or '',
        telegram_full_name=full_name or '',
    )


async def daraxt_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    user_data_store[user_id]['tree_type'] = text
    await update.message.reply_text(
        "🔢 Nechta daraxt bor?\n<i>Faqat raqam yozing, masalan: 50</i>",
        parse_mode='HTML', reply_markup=skip_keyboard()
    )
    return DARAXT_COUNT


async def daraxt_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    try:
        user_data_store[user_id]['tree_count'] = int(text.replace(' ', ''))
    except ValueError:
        await update.message.reply_text("❗ Faqat raqam kiriting!")
        return DARAXT_COUNT
    await update.message.reply_text(
        "📅 Daraxtlar necha yillik?\n<i>Faqat raqam, masalan: 5</i>",
        parse_mode='HTML', reply_markup=skip_keyboard()
    )
    return DARAXT_AGE


async def daraxt_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    try:
        user_data_store[user_id]['tree_age'] = int(text.replace(' ', ''))
    except ValueError:
        await update.message.reply_text("❗ Faqat raqam kiriting!")
        return DARAXT_AGE
    await update.message.reply_text(
        "🌸 Daraxt necha yoshdan meva bera boshlaydi?\n<i>Masalan: 4</i>",
        parse_mode='HTML', reply_markup=skip_keyboard()
    )
    return DARAXT_BEARING_AGE


async def daraxt_bearing_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    try:
        user_data_store[user_id]['bearing_age'] = int(text.replace(' ', ''))
    except ValueError:
        await update.message.reply_text("❗ Faqat raqam kiriting!")
        return DARAXT_BEARING_AGE
    await update.message.reply_text(
        "📅 Meva qaysi oyda to'liq tayyor bo'ladi?\n<i>Oy raqamini yozing: 1=Yanvar, 6=Iyun, 9=Sentabr...</i>",
        parse_mode='HTML', reply_markup=skip_keyboard()
    )
    return DARAXT_READY_MONTH


async def daraxt_ready_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    try:
        month = int(text.strip())
        if not 1 <= month <= 12:
            raise ValueError
        user_data_store[user_id]['ready_month'] = month
    except ValueError:
        await update.message.reply_text("❗ 1 dan 12 gacha raqam kiriting (1=Yanvar, 12=Dekabr)!")
        return DARAXT_READY_MONTH
    await update.message.reply_text(
        "📍 Joylashuvingizni yuboring (yoki matn shaklida yozing):",
        reply_markup=location_keyboard()
    )
    return DARAXT_LOCATION


async def daraxt_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text):
        return await cancel(update, context)
    if update.message.location:
        user_data_store[user_id]['location_lat'] = update.message.location.latitude
        user_data_store[user_id]['location_lon'] = update.message.location.longitude
    elif update.message.text:
        user_data_store[user_id]['location_text'] = update.message.text
    await update.message.reply_text(
        "📞 Telefon raqamingizni yuboring:",
        reply_markup=phone_keyboard()
    )
    return DARAXT_PHONE


async def daraxt_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message.text and ("❌" in update.message.text or "Bekor" in update.message.text):
        return await cancel(update, context)
    if update.message.contact:
        user_data_store[user_id]['phone'] = update.message.contact.phone_number
    elif update.message.text:
        user_data_store[user_id]['phone'] = update.message.text
    await update.message.reply_text(
        "📝 Qo'shimcha ma'lumot yozing (ixtiyoriy):",
        reply_markup=skip_keyboard()
    )
    return DARAXT_DESCRIPTION


async def daraxt_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    if "❌" in text or "Bekor" in text:
        return await cancel(update, context)
    if "O'tkazib" not in text:
        user_data_store[user_id]['description'] = text

    data = user_data_store.get(user_id, {})
    months = {1:'Yanvar',2:'Fevral',3:'Mart',4:'Aprel',5:'May',6:'Iyun',
              7:'Iyul',8:'Avgust',9:'Sentabr',10:'Oktabr',11:'Noyabr',12:'Dekabr'}
    month_name = months.get(data.get('ready_month', 1), '?')

    summary = (
        f"📋 <b>Ma'lumotlarni tekshiring:</b>\n\n"
        f"🌳 Daraxt turi: {data.get('tree_type', '—')}\n"
        f"🔢 Soni: {data.get('tree_count', '—')} ta\n"
        f"📅 Yoshi: {data.get('tree_age', '—')} yil\n"
        f"🌸 Meva berish yoshi: {data.get('bearing_age', '—')} yoshdan\n"
        f"📆 Meva tayyor oyi: {month_name}\n"
        f"📞 Telefon: {data.get('phone', '—')}\n"
        f"📍 Manzil: {'Bor ✅' if data.get('location_lat') else data.get('location_text', '—')}\n"
        f"📝 Qo'shimcha: {data.get('description', '—')}"
    )

    await update.message.reply_text(summary, parse_mode='HTML', reply_markup=confirm_keyboard())
    return CONFIRM


# ================= CALLBACK QUERY HANDLERS (Sotildi / Edit / Delete) =================

@sync_to_async
def get_product_by_id(product_id):
    from marketplace.models import Product
    try:
        return Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return None

@sync_to_async
def mark_product_sold(product_id):
    from marketplace.models import Product
    from django.utils import timezone
    try:
        p = Product.objects.get(id=product_id)
        p.is_active = False
        p.is_sold = True
        p.sold_at = timezone.now()
        p.save(update_fields=['is_active', 'is_sold', 'sold_at'])
        return p
    except Product.DoesNotExist:
        return None

@sync_to_async
def delete_product_db(product_id):
    from marketplace.models import Product
    try:
        p = Product.objects.get(id=product_id)
        p.delete()
        return True
    except Product.DoesNotExist:
        return False


async def product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("sold_"):
        product_id = int(data.split("_")[1])
        product = await mark_product_sold(product_id)
        if product:
            # Kanalda sotildi deb belgilash
            from .channel import edit_product_in_channel, _get_channel_id
            from telegram import Bot
            from django.conf import settings as ds
            from marketplace.models import BotSettings
            settings = await sync_to_async(BotSettings.get_settings)()
            token = settings.bot_token or ds.BOT_TOKEN
            channel_id = await _get_channel_id()
            if channel_id and product.telegram_message_id and token:
                try:
                    bot = context.bot
                    from .channel import get_caption_for_product
                    caption = get_caption_for_product(product)
                    sold_caption = f"✅ <b>SOTILDI</b>\n\n{caption}"
                    await bot.edit_message_caption(
                        chat_id=channel_id,
                        message_id=product.telegram_message_id,
                        caption=sold_caption,
                        parse_mode='HTML'
                    )
                except Exception as e:
                    logger.error(f"Sotildi belgilashda xato: {e}")
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"✅ <b>{product.name}</b> sotildi deb belgilandi!", parse_mode='HTML')
        else:
            await query.message.reply_text("❌ Mahsulot topilmadi.")

    elif data.startswith("delete_"):
        product_id = int(data.split("_")[1])
        product = await get_product_by_id(product_id)
        if product:
            from .keyboards import confirm_delete_keyboard
            await query.edit_message_reply_markup(reply_markup=confirm_delete_keyboard(product_id))
        else:
            await query.message.reply_text("❌ Mahsulot topilmadi.")

    elif data.startswith("confirm_delete_"):
        product_id = int(data.split("_")[2])
        product = await get_product_by_id(product_id)
        if product:
            # Kanaldan o'chirish
            from .channel import delete_product_from_channel
            await delete_product_from_channel(context.bot, product)
            name = product.name
            await delete_product_db(product_id)
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text(f"🗑️ <b>{name}</b> o'chirildi.", parse_mode='HTML')
        else:
            await query.message.reply_text("❌ Mahsulot topilmadi.")

    elif data.startswith("cancel_delete_"):
        await query.edit_message_reply_markup(reply_markup=product_actions_keyboard(int(data.split("_")[2])))

    elif data.startswith("edit_"):
        product_id = int(data.split("_")[1])
        await query.message.reply_text(
            f"✏️ Mahsulotni tahrirlash uchun Dashboard ga o'ting:\n"
            f"https://savdo-24-7.uz/dashboard/products/{product_id}/edit/",
            disable_web_page_preview=True
        )
