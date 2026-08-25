with open("templates/dashboard/webapp_edit.html", "r", encoding="utf-8") as f:
    code = f.read()

code = code.replace('<form method="POST">', '<form method="POST" enctype="multipart/form-data">')

extra_fields = """
        <div class="form-group">
            <label>Soni (ixtiyoriy)</label>
            <input type="number" name="quantity" value="{{ product.quantity|default_if_none:'' }}">
        </div>
        <div class="form-group">
            <label>Manzil (matn ko'rinishida)</label>
            <input type="text" name="location_text" value="{{ product.location_text|default_if_none:'' }}">
        </div>
        <div class="form-group">
            <label>Yangi Rasm yuklash (ixtiyoriy)</label>
            <input type="file" name="image" accept="image/*">
        </div>
"""

code = code.replace('        <button type="submit">Saqlash</button>', extra_fields + '        <button type="submit">Saqlash</button>')

with open("templates/dashboard/webapp_edit.html", "w", encoding="utf-8") as f:
    f.write(code)
