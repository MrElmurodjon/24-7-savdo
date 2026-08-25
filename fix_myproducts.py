with open("bot/handlers.py", "r", encoding="utf-8") as f:
    code = f.read()

start = code.find("async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):")
end = code.find("async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):")

if start != -1 and end != -1:
    new_func = """async def my_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    products = await get_user_products(user_id)

    if not products:
        await update.message.reply_text(
            "?? Sizda hali mahsulot yo'q.\\n? Mahsulot qo'shish tugmasini bosing!",
            reply_markup=main_menu_keyboard()
        )
        return

    await update.message.reply_text(
        f"?? <b>Sizning mahsulotlaringiz:</b> {len(products)} ta",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )

    CAT_ICONS = {
        'kochat': '??', 'meva': '??', 'sabzavot': '??',
        'parranda': '??', 'tuxum': '??'
    }

    for p in products:
        price_fmt = f"{int(p.price):,}".replace(',', ' ')
        icon = CAT_ICONS.get(p.category, '??')
        
        if getattr(p, 'location_lat', None) and getattr(p, 'location_lon', None):
            loc = f"<a href='https://www.google.com/maps?q={p.location_lat},{p.location_lon}'>Manzilni ko'rish</a>"
        else:
            loc = p.location_text or "-"
            
        qty = f"\\n?? Soni: {p.quantity} dona" if getattr(p, 'quantity', None) else ""
        desc = f"\\n?? Qo'shimcha: {p.description}" if getattr(p, 'description', None) else ""

        sold_tag = "? <b>SOTILDI</b> ?\\n\\n" if getattr(p, 'is_sold', False) else ""
        text = (
            f"{sold_tag}{icon} <b>{p.name}</b>\\n"
            f"?? Narxi: {price_fmt} so'm{qty}\\n"
            f"?? Telefon: {p.phone}\\n"
            f"?? Manzil: {loc}"
            f"{desc}\\n"
            f"?? Sana: {p.created_at.strftime('%d.%m.%Y')}"
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
    
    code = code[:start] + new_func + code[end:]
    
    with open("bot/handlers.py", "w", encoding="utf-8") as f:
        f.write(code)
