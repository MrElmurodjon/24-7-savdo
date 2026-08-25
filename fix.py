import re

with open("bot/handlers.py", "r", encoding="utf-8") as f:
    code = f.read()

start = code.find("async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):")
end = code.find("async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):")

new_func = """async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    products = await get_user_products(user_id)

    if not products:
        await update.message.reply_text(
            "\\U0001F6AB Sizda hali mahsulot yo'q.\\n\\u2795 Mahsulot qo'shish tugmasini bosing!",
            reply_markup=main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        f"\\U0001F4CB <b>Sizning mahsulotlaringiz:</b> {len(products)} ta",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )

    CAT_ICONS = {
        'kochat': '\\U0001F331', 'meva': '\\U0001F34E', 'sabzavot': '\\U0001F955',
        'parranda': '\\U0001F414', 'tuxum': '\\U0001F95A'
    }

    for p in products:
        price_fmt = f"{int(p.price):,}".replace(',', ' ')
        icon = CAT_ICONS.get(p.category, '\\U0001F4E6')
        
        if getattr(p, 'location_lat', None) and getattr(p, 'location_lon', None):
            loc = f"<a href='https://www.google.com/maps?q={p.location_lat},{p.location_lon}'>Manzilni ko'rish</a>"
        else:
            loc = p.location_text or "-"
            
        qty = f"\\n\\U0001F4E6 Soni: {p.quantity} dona" if getattr(p, 'quantity', None) else ""
        desc = f"\\n\\U0001F4DD Qo'shimcha: {p.description}" if getattr(p, 'description', None) else ""

        sold_tag = "\\u274c <b>SOTILDI</b> \\u274c\\n\\n" if getattr(p, 'is_sold', False) else ""
        text = (
            f"{sold_tag}{icon} <b>{p.name}</b>\\n"
            f"\\U0001F4B0 Narxi: {price_fmt} so'm{qty}\\n"
            f"\\U0001F4DE Telefon: {p.phone}\\n"
            f"\\U0001F4CD Manzil: {loc}"
            f"{desc}\\n"
            f"\\U0001F4C5 Sana: {p.created_at.strftime('%d.%m.%Y')}"
        )
        
        first_image = await sync_to_async(lambda p=p: p.images.first())()
        if first_image and (getattr(first_image, 'telegram_file_id', None) or getattr(first_image, 'image', None)):
            if getattr(first_image, 'telegram_file_id', None):
                await update.message.reply_photo(
                    photo=first_image.telegram_file_id,
                    caption=text,
                    parse_mode='HTML',
                    reply_markup=product_actions_keyboard(p.id, getattr(p, 'is_sold', False))
                )
            else:
                import os
                if hasattr(first_image.image, 'path') and os.path.exists(first_image.image.path):
                    with open(first_image.image.path, 'rb') as photo_file:
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=text,
                            parse_mode='HTML',
                            reply_markup=product_actions_keyboard(p.id, getattr(p, 'is_sold', False))
                        )
                else:
                    await update.message.reply_text(text, parse_mode='HTML', disable_web_page_preview=True, reply_markup=product_actions_keyboard(p.id, getattr(p, 'is_sold', False)))
        else:
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                disable_web_page_preview=True,
                reply_markup=product_actions_keyboard(p.id, getattr(p, 'is_sold', False))
            )

\n\n"""

# Evaluate unicode escapes safely using codecs
import codecs
new_func = codecs.decode(new_func, 'unicode_escape')
code = code[:start] + new_func + code[end:]

with open("bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(code)
