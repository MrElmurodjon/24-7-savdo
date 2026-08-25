with open("bot/handlers.py", "r", encoding="utf-8") as f:
    code = f.read()

import re
old_block = r"caption = get_caption_for_product\(product\)\s+sold_caption = f\".*?<b>SOTILDI</b>.*?\\n\\n\{caption\}\"\s+await bot\.edit_message_caption\(\s+chat_id=channel_id,\s+message_id=product\.telegram_message_id,\s+caption=sold_caption,\s+parse_mode='HTML'\s+\)"

new_block = r"""caption = get_caption_for_product(product)
                    await bot.edit_message_caption(
                        chat_id=channel_id,
                        message_id=product.telegram_message_id,
                        caption=caption,
                        parse_mode='HTML'
                    )"""

code = re.sub(old_block, new_block, code, flags=re.DOTALL)

with open("bot/handlers.py", "w", encoding="utf-8") as f:
    f.write(code)
