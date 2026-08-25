import re

with open("bot/handlers.py", "r", encoding="utf-8") as f:
    code = f.read()

old_block = r"for p in products:\s+price_fmt =.*?await update\.message\.reply_text\(.*?reply_markup=product_actions_keyboard\(p\.id, p\.is_sold\)\s+\)"
new_block = """for p in products:
        price_fmt = f"{int(p.price):,}".replace(',', ' ')
        icon = CAT_ICONS.get(p.category, '??')
        
        if getattr(p, 'location_lat', None) and getattr(p, 'location_lon', None):
            loc = f"<a href='https://www.google.com/maps?q={p.location_lat},{p.location_lon}'>Ko'rish</a>"
        else:
            loc = p.location_text or "—"
            
        qty = f"\\n?? Soni: {p.quantity}" if getattr(p, 'quantity', None) else ""
        desc = f"\\n?? Qo'shimcha: {p.description}" if getattr(p, 'description', None) else ""

        sold_tag = "? <b>SOTILDI</b> ?\\n\\n" if getattr(p, 'is_sold', False) else ""
        text = (
            f"{sold_tag}{icon} <b>{p.name}</b>\\n"
            f"?? Narx: {price_fmt} so'm{qty}\\n"
            f"?? Tel: {p.phone}\\n"
            f"?? Manzil: {loc}"
            f"{desc}\\n"
            f"?? {p.created_at.strftime('%d.%m.%Y')}"
        )
        
        # Get photo if available
        first_image = await sync_to_async(lambda: p.images.first())()
        
        if first_image and (first_image.telegram_file_id or first_image.image):
            if first_image.telegram_file_id:
                await update.message.reply_photo(
                    photo=first_image.telegram_file_id,
                    caption=text,
                    parse_mode='HTML',
                    reply_markup=product_actions_keyboard(p.id, p.is_sold)
                )
            else:
                import os
                if os.path.exists(first_image.image.path):
                    with open(first_image.image.path, 'rb') as photo_file:
                        await update.message.reply_photo(
                            photo=photo_file,
                            caption=text,
                            parse_mode='HTML',
                            reply_markup=product_actions_keyboard(p.id, p.is_sold)
                        )
                else:
                    await update.message.reply_text(text, parse_mode='HTML', reply_markup=product_actions_keyboard(p.id, p.is_sold))
        else:
            await update.message.reply_text(
                text,
                parse_mode='HTML',
                reply_markup=product_actions_keyboard(p.id, p.is_sold)
            )"""

code = re.sub(old_block, new_block, code, flags=re.DOTALL)

with open("bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(code)
