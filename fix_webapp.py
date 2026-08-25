with open("dashboard/webapp_views.py", "r", encoding="utf-8") as f:
    code = f.read()

new_block = """    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.price = request.POST.get('price', product.price)
        product.phone = request.POST.get('phone', product.phone)
        product.description = request.POST.get('description', product.description)
        
        # Soni (quantity)
        qty = request.POST.get('quantity')
        if qty:
            try:
                product.quantity = int(qty)
            except ValueError:
                pass
                
        # Lokatsiya text
        loc = request.POST.get('location_text')
        if loc:
            product.location_text = loc
            
        product.save()
        
        # Rasm (Image)
        if 'image' in request.FILES:
            from marketplace.models import ProductImage
            # Delete old image if you only want 1, or just add. Let's delete old for simplicity
            product.images.all().delete()
            ProductImage.objects.create(product=product, image=request.FILES['image'])
        
        # update channel if needed"""

import re
code = re.sub(r"    if request\.method == 'POST':.*?# update channel if needed", new_block, code, flags=re.DOTALL)

with open("dashboard/webapp_views.py", "w", encoding="utf-8") as f:
    f.write(code)
