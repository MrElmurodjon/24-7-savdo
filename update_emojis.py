with open("templates/dashboard/sold_products.html", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace("?? Qidirish...", "\U0001F50D Qidirish...")
code = code.replace("?? Ko'rish", "\U0001F4CD Ko'rish")
code = code.replace("? Sotilganlar", "\u2705 Sotilganlar")
code = code.replace("??", "\u21a9\ufe0f")
code = code.replace("???", "\U0001F5D1\ufe0f")

with open("templates/dashboard/sold_products.html", "w", encoding="utf-8") as f:
    f.write(code)
