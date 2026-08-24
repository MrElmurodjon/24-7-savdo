import os
import django
import asyncio
import logging
from asgiref.sync import sync_to_async
from telegram import Bot, InputMediaPhoto
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

@sync_to_async
def _get_channel_id():
    from marketplace.models import BotSettings
    settings = BotSettings.get_settings()
    return settings.channel_id

def _get_location_text(product):
    location_url = product.get_location_url()
    if location_url:
        return f"\n📍 <a href='{location_url}'>Manzilni ko'rish</a>"
    elif product.location_text:
        return f"\n📍 {product.location_text}"
    return ""

def format_kochat_message(product):
    price_formatted = f"{int(product.price):,}".replace(',', ' ')
    qty = f"\n📦 Soni: {product.quantity} dona" if product.quantity else ""
    age = f"\n📅 Yoshi: {product.age}" if product.age else ""
    desc = f"\n\n📝 Qo'shimcha: {product.description}" if product.description else ""
    location_text = _get_location_text(product)
    date_str = product.created_at.strftime("%d.%m.%Y")

    return f"""🌱 <b>KO'CHAT SOTILADI</b>

🌿 <b>Turi:</b> {product.name}{age}
💰 <b>Narxi:</b> {price_formatted} so'm/dona{qty}{location_text}
📞 <b>Telefon:</b> {product.phone}{desc}

🕐 <i>Sana: {date_str}</i>
━━━━━━━━━━━━━━━━━━━━
🏪 <b>24/7 Savdo</b>"""

def format_meva_message(product):
    price_formatted = f"{int(product.price):,}".replace(',', ' ')
    desc = f"\n\n📝 Qo'shimcha: {product.description}" if product.description else ""
    location_text = _get_location_text(product)
    date_str = product.created_at.strftime("%d.%m.%Y")

    return f"""🍎 <b>MEVA/MAHSULOT SOTILADI</b>

🌾 <b>Turi:</b> {product.name}
💰 <b>Narxi:</b> {price_formatted} so'm/kg{location_text}
📞 <b>Telefon:</b> {product.phone}{desc}

🕐 <i>Sana: {date_str}</i>
━━━━━━━━━━━━━━━━━━━━
🏪 <b>24/7 Savdo</b>"""

def format_sabzavot_message(product):
    price_formatted = f"{int(product.price):,}".replace(',', ' ')
    desc = f"\n\n📝 Qo'shimcha: {product.description}" if product.description else ""
    location_text = _get_location_text(product)
    date_str = product.created_at.strftime("%d.%m.%Y")

    return f"""🥕 <b>SABZAVOT SOTILADI</b>

🥕 <b>Turi:</b> {product.name}
💰 <b>Narxi:</b> {price_formatted} so'm{location_text}
📞 <b>Telefon:</b> {product.phone}{desc}

🕐 <i>Sana: {date_str}</i>
━━━━━━━━━━━━━━━━━━━━
🏪 <b>24/7 Savdo</b>"""

def format_parranda_message(product):
    price_formatted = f"{int(product.price):,}".replace(',', ' ')
    qty = f"\n📦 Soni: {product.quantity} ta" if product.quantity else ""
    weight = f"\n⚖️ Og'irligi: {product.weight}" if product.weight else ""
    desc = f"\n\n📝 Qo'shimcha: {product.description}" if product.description else ""
    location_text = _get_location_text(product)
    date_str = product.created_at.strftime("%d.%m.%Y")

    return f"""🐔 <b>PARRANDA SOTILADI</b>

🐔 <b>Turi:</b> {product.name}{qty}{weight}
💰 <b>Narxi:</b> {price_formatted} so'm{location_text}
📞 <b>Telefon:</b> {product.phone}{desc}

🕐 <i>Sana: {date_str}</i>
━━━━━━━━━━━━━━━━━━━━
🏪 <b>24/7 Savdo</b>"""

def format_tuxum_message(product):
    price_formatted = f"{int(product.price):,}".replace(',', ' ')
    qty = f"\n📦 Soni: {product.quantity} ta" if product.quantity else ""
    desc = f"\n\n📝 Qo'shimcha: {product.description}" if product.description else ""
    location_text = _get_location_text(product)
    date_str = product.created_at.strftime("%d.%m.%Y")

    return f"""🥚 <b>TUXUM SOTILADI</b>

🥚 <b>Turi:</b> {product.name}{qty}
💰 <b>Narxi:</b> {price_formatted} so'm{location_text}
📞 <b>Telefon:</b> {product.phone}{desc}

🕐 <i>Sana: {date_str}</i>
━━━━━━━━━━━━━━━━━━━━
🏪 <b>24/7 Savdo</b>"""

def get_caption_for_product(product):
    if product.category == 'kochat':
        return format_kochat_message(product)
    elif product.category == 'sabzavot':
        return format_sabzavot_message(product)
    elif product.category == 'parranda':
        return format_parranda_message(product)
    elif product.category == 'tuxum':
        return format_tuxum_message(product)
    else:
        return format_meva_message(product)

async def send_product_to_channel(bot: Bot, product, images) -> int | None:
    channel_id = await _get_channel_id()
    if not channel_id:
        logger.warning("Kanal ID sozlanmagan!")
        return None

    try:
        caption = get_caption_for_product(product)

        if images:
            media_group = []
            for i, img in enumerate(images):
                if img.telegram_file_id:
                    media = InputMediaPhoto(
                        media=img.telegram_file_id,
                        caption=caption if i == 0 else None,
                        parse_mode='HTML'
                    )
                else:
                    img_path = img.image.path if hasattr(img.image, 'path') else None
                    if img_path and os.path.exists(img_path):
                        with open(img_path, 'rb') as f:
                            media = InputMediaPhoto(
                                media=f.read(),
                                caption=caption if i == 0 else None,
                                parse_mode='HTML'
                            )
                    else:
                        continue
                media_group.append(media)

            if media_group:
                messages = await bot.send_media_group(chat_id=channel_id, media=media_group)
                return messages[0].message_id if messages else None
        else:
            msg = await bot.send_message(chat_id=channel_id, text=caption, parse_mode='HTML')
            return msg.message_id

    except TelegramError as e:
        logger.error(f"Kanalga yuborishda xato: {e}")
        return None

async def edit_product_in_channel(bot: Bot, product, images) -> bool:
    channel_id = await _get_channel_id()
    if not channel_id or not product.telegram_message_id:
        return False

    try:
        caption = get_caption_for_product(product)
        await bot.edit_message_caption(
            chat_id=channel_id,
            message_id=product.telegram_message_id,
            caption=caption,
            parse_mode='HTML'
        )
        return True
    except TelegramError as e:
        logger.error(f"Tahrirlashda xato: {e}")
        return False

async def delete_product_from_channel(bot: Bot, product) -> bool:
    channel_id = await _get_channel_id()
    if not channel_id or not product.telegram_message_id:
        return False

    try:
        await bot.delete_message(chat_id=channel_id, message_id=product.telegram_message_id)
        return True
    except TelegramError as e:
        logger.error(f"O'chirishda xato: {e}")
        return False
