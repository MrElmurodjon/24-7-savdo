import os
import re

with open("bot/keyboards.py", "r", encoding="utf-8") as f:
    code = f.read()

if "WebAppInfo" not in code:
    code = code.replace(
        "from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton",
        "from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo"
    )

code = re.sub(
    r'InlineKeyboardButton\(.*?"edit_\{product_id\}"\)',
    r'InlineKeyboardButton("?? Tahrirlash", web_app=WebAppInfo(url=f"https://savdo-24-7.uz/webapp/edit/{product_id}/"))',
    code
)

with open("bot/keyboards.py", "w", encoding="utf-8") as f:
    f.write(code)
