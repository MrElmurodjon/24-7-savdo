with open("bot/channel.py", "r", encoding="utf-8") as f:
    code = f.read()

# Let's just find "if product.is_sold:" and replace until "return caption"
start_idx = code.find("if product.is_sold:")
end_idx = code.find("return caption", start_idx) + len("return caption")

if start_idx != -1 and end_idx != -1:
    new_block = "if product.is_sold:\n        caption = caption.replace(' SOTILADI</b>', '</b>')\n        return f'\\u274c <b>SOTILDI</b> \\u274c\\n\\n{caption}'\n    return caption"
    code = code[:start_idx] + new_block + code[end_idx:]

with open("bot/channel.py", "w", encoding="utf-8") as f:
    f.write(code)
