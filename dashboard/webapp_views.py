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
            
        lat = request.POST.get('location_lat')
        lon = request.POST.get('location_lon')
        if lat and lon:
            try:
                product.location_lat = float(lat)
                product.location_lon = float(lon)
            except ValueError:
                pass
            
        product.save()
        
        from bot.channel import edit_product_in_channel, delete_product_from_channel, send_product_to_channel
        from marketplace.models import BotSettings, ProductImage
        from telegram import Bot
        import asyncio
        
        bot_settings = BotSettings.get_settings()
        images_updated = False
        old_image_count = product.images.count()
        
        if 'image1' in request.FILES or 'image2' in request.FILES:
            # Rasm o'zgargan bo'lsa, avval eskisini kanaldan o'chiramiz
            if bot_settings.bot_token and product.telegram_message_id:
                bot = Bot(token=bot_settings.bot_token)
                try:
                    # Eskisi album bo'lsa hammalarini o'chirishga harakat qilamiz
                    for i in range(max(1, old_image_count)):
                        try:
                            # We can't use delete_product_from_channel cleanly for albums without modifying it, 
                            # so we do it inline here or just call it multiple times.
                            # Better yet, let's just delete the main message. In most cases they only uploaded 1 image recently.
                            pass
                        except Exception:
                            pass
                    # For simplicity, let's just use the existing function and we will update delete_product_from_channel separately.
                    asyncio.run(delete_product_from_channel(bot, product, old_image_count))
                except Exception as e:
                    print("Error deleting old: ", e)
                    
            product.images.all().delete()
            if 'image1' in request.FILES:
                ProductImage.objects.create(product=product, image=request.FILES['image1'])
            if 'image2' in request.FILES:
                ProductImage.objects.create(product=product, image=request.FILES['image2'])
            images_updated = True

        if bot_settings.bot_token and product.telegram_message_id:
            bot = Bot(token=bot_settings.bot_token)
            images = list(product.images.all()) # MUST EVALUATE QUERYSET BEFORE PASSING TO ASYNC!
            try:
                if images_updated:
                    new_msg_id = asyncio.run(send_product_to_channel(bot, product, images))
                    if new_msg_id:
                        product.telegram_message_id = new_msg_id
                        product.save()
                else:
                    # Faqat text o'zgargan
                    asyncio.run(edit_product_in_channel(bot, product, images))
            except Exception as e:
                print("Error sending/editing: ", e)
                
        return render(request, 'dashboard/webapp_success.html')

    return render(request, 'dashboard/webapp_edit.html', {'product': product})
