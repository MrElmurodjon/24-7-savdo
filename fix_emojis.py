with open("templates/dashboard/sold_products.html", "r", encoding="utf-8") as f:
    code = f.read()

# The button HTML was:
# <button ...> \u21a9\ufe0f </button>
# <button ...> \U0001F5D1\ufe0f? </button>  <- Because '???' became 'undo?'

import re
code = re.sub(r'>\s*\u21a9\ufe0f\s*</button>', '>\u21a9\ufe0f</button>', code)
code = re.sub(r'>\s*\u21a9\ufe0f\?\s*</button>', '>\U0001F5D1\ufe0f</button>', code)

with open("templates/dashboard/sold_products.html", "w", encoding="utf-8") as f:
    f.write(code)
