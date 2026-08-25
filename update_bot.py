import os
import re
with open('bot/handlers.py', 'r', encoding='utf-8') as f:
    code = f.read()

pattern = r"(text\s*=\s*\(\s*f\"\{icon\}.*?\))"
replacement = r"""sold_tag = "? <b>SOTILDI</b> ?\n\n" if getattr(p, 'is_sold', False) else ""
        text = (
            f"{sold_tag}{icon} <b>{p.name}</b>\n"
            f"?? Narx: {price_fmt} so'm\n"
            f"?? Tel: {p.phone}\n"
            f"?? Manzil: {loc}"
            f"{desc}\n"
            f"?? {p.created_at.strftime('%d.%m.%Y')}"
        )"""

code = re.sub(pattern, replacement, code, flags=re.DOTALL)
with open('bot/handlers.py', 'w', encoding='utf-8') as f:
    f.write(code)
