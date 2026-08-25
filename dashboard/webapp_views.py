from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from marketplace.models import Product
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt

@csrf_exempt
@xframe_options_exempt
def webapp_product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
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
        
        # update channel if needed
        from bot.channel import edit_product_in_channel
        from marketplace.models import BotSettings
        from telegram import Bot
        import asyncio
        
        bot_settings = BotSettings.get_settings()
        if bot_settings.bot_token and product.telegram_message_id:
            bot = Bot(token=bot_settings.bot_token)
            images = product.images.all()
            try:
                asyncio.run(edit_product_in_channel(bot, product, images))
            except Exception:
                pass
                
        return render(request, 'dashboard/webapp_success.html')

    return render(request, 'dashboard/webapp_edit.html', {'product': product})
