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
        
        qty = request.POST.get('quantity')
        if qty:
            try:
                product.quantity = int(qty)
            except ValueError:
                pass
                
        loc = request.POST.get('location_text')
        if loc:
            product.location_text = loc
            
        product.save()
        
        images_updated = False
        if 'image1' in request.FILES or 'image2' in request.FILES:
            from marketplace.models import ProductImage
            product.images.all().delete()
            if 'image1' in request.FILES:
                ProductImage.objects.create(product=product, image=request.FILES['image1'])
            if 'image2' in request.FILES:
                ProductImage.objects.create(product=product, image=request.FILES['image2'])
            images_updated = True
        
        from bot.channel import edit_product_in_channel, delete_product_from_channel, send_product_to_channel
        from marketplace.models import BotSettings
        from telegram import Bot
        import asyncio
        
        bot_settings = BotSettings.get_settings()
        if bot_settings.bot_token and product.telegram_message_id:
            bot = Bot(token=bot_settings.bot_token)
            images = product.images.all()
            try:
                if images_updated:
                    # Rasm o'zgargan bo'lsa postni o'chirib qayta yuboramiz
                    asyncio.run(delete_product_from_channel(bot, product))
                    new_msg_id = asyncio.run(send_product_to_channel(bot, product, images))
                    if new_msg_id:
                        product.telegram_message_id = new_msg_id
                        product.save()
                else:
                    # Faqat text o'zgargan
                    asyncio.run(edit_product_in_channel(bot, product, images))
            except Exception:
                pass
                
        return render(request, 'dashboard/webapp_success.html')

    return render(request, 'dashboard/webapp_edit.html', {'product': product})
