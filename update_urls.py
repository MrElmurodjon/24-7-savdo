with open('dashboard/urls.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('from . import views', 'from . import views\nfrom . import webapp_views')

url_line = "    path('webapp/edit/<int:pk>/', webapp_views.webapp_product_edit, name='webapp_product_edit'),\n]"
code = code.replace(']', url_line)

with open('dashboard/urls.py', 'w', encoding='utf-8') as f:
    f.write(code)
