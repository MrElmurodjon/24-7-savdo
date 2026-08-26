"""
Dashboard views — statistika, mahsulotlar, sozlamalar
"""
import os
import asyncio
import logging
import mimetypes
from datetime import timedelta, date
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.utils import timezone
from django.db.models import Count, Q, Sum
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.paginator import Paginator

from marketplace.models import Product, ProductImage, BotSettings

logger = logging.getLogger(__name__)


# ===================== AUTH =====================

def login_required_custom(view_func):
    """Oddiy session-based login decorator"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return redirect('dashboard:login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def login_view(request):
    if request.session.get('is_admin'):
        return redirect('dashboard:index')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        if (username == settings.ADMIN_USERNAME and
                password == settings.ADMIN_PASSWORD):
            request.session['is_admin'] = True
            request.session['admin_name'] = username
            return redirect('dashboard:index')
        else:
            error = "Login yoki parol noto'g'ri!"

    return render(request, 'dashboard/login.html', {'error': error})


def logout_view(request):
    request.session.flush()
    return redirect('dashboard:login')


# ===================== DASHBOARD =====================

@login_required_custom
def index(request):
    """Asosiy statistika sahifasi (Filtrlar bilan)"""
    products = Product.objects.filter(is_active=True)
    
    # URL dan filtrlarni olish
    region_filter = request.GET.get('region', '').strip()
    district_filter = request.GET.get('district', '').strip()
    period = request.GET.get('period', 'all')  # all, today, week, month
    
    if region_filter:
        products = products.filter(region__icontains=region_filter)
    if district_filter:
        products = products.filter(district__icontains=district_filter)
        
    now = timezone.now()
    today = now.date()
    
    # Vaqt filtri grafikka chiziladigan kunlar sonini (days_to_plot) ham belgilaydi
    if period == 'today':
        products = products.filter(created_at__date=today)
        days_to_plot = 7  # Bugun bo'lsa ham solishtirish uchun 1 haftalik grafik chizamiz
    elif period == 'week':
        start_date = today - timedelta(days=7)
        products = products.filter(created_at__date__gte=start_date)
        days_to_plot = 7
    elif period == 'month':
        start_date = today - timedelta(days=30)
        products = products.filter(created_at__date__gte=start_date)
        days_to_plot = 30
    else:
        # Barchasi tanlanganda grafikka oxirgi 30 kunni ko'rsatamiz
        days_to_plot = 30
        
    total = products.count()
    kochat_count = products.filter(category='kochat').count()
    meva_count = products.filter(category='meva').count()
    sabzavot_count = products.filter(category='sabzavot').count()
    parranda_count = products.filter(category='parranda').count()
    tuxum_count = products.filter(category='tuxum').count()
    
    # Grafik uchun ma'lumot tayyorlash (Meva va Ko'chat alohida)
    chart_labels = []
    chart_kochat_data = []
    chart_meva_data = []
    chart_sabzavot_data = []
    chart_parranda_data = []
    chart_tuxum_data = []
    
    # Baza filterini olib tashlab, grafik uchun xuddi shu location filterlar bilan
    base_qs_for_chart = Product.objects.filter(is_active=True)
    if region_filter:
        base_qs_for_chart = base_qs_for_chart.filter(region__icontains=region_filter)
    if district_filter:
        base_qs_for_chart = base_qs_for_chart.filter(district__icontains=district_filter)
        
    for i in range(days_to_plot - 1, -1, -1):
        d = today - timedelta(days=i)
        c_kochat = base_qs_for_chart.filter(created_at__date=d, category='kochat').count()
        c_meva = base_qs_for_chart.filter(created_at__date=d, category='meva').count()
        c_sabzavot = base_qs_for_chart.filter(created_at__date=d, category='sabzavot').count()
        c_parranda = base_qs_for_chart.filter(created_at__date=d, category='parranda').count()
        c_tuxum = base_qs_for_chart.filter(created_at__date=d, category='tuxum').count()
        
        chart_kochat_data.append(c_kochat)
        chart_meva_data.append(c_meva)
        chart_sabzavot_data.append(c_sabzavot)
        chart_parranda_data.append(c_parranda)
        chart_tuxum_data.append(c_tuxum)
        chart_labels.append(d.strftime('%d.%m'))

    # Barcha viloyat va tumanlar ro'yxatini select lar uchun olib kelish
    regions = Product.objects.exclude(region='').values_list('region', flat=True).distinct()
    
    # Agar region tanlangan bo'lsa, tumanlar o'sha regionniki bo'ladi
    if region_filter:
        districts = Product.objects.filter(region__icontains=region_filter).exclude(district='').values_list('district', flat=True).distinct()
    else:
        districts = Product.objects.exclude(district='').values_list('district', flat=True).distinct()

    recent_products = products.prefetch_related('images').order_by('-created_at')[:5]

    context = {
        'total': total,
        'kochat_count': kochat_count,
        'meva_count': meva_count,
        'sabzavot_count': sabzavot_count,
        'parranda_count': parranda_count,
        'tuxum_count': tuxum_count,
        'chart_kochat_data': json.dumps(chart_kochat_data),
        'chart_meva_data': json.dumps(chart_meva_data),
        'chart_sabzavot_data': json.dumps(chart_sabzavot_data),
        'chart_parranda_data': json.dumps(chart_parranda_data),
        'chart_tuxum_data': json.dumps(chart_tuxum_data),
        'chart_labels': json.dumps(chart_labels),
        'recent_products': recent_products,
        'active_page': 'index',
        'regions': regions,
        'districts': districts,
        'region_filter': region_filter,
        'district_filter': district_filter,
        'period': period,
    }
    return render(request, 'dashboard/index.html', context)


# ===================== PRODUCTS =====================

@login_required_custom
def products_view(request):
    """Mahsulotlar ro'yxati"""
    category = request.GET.get('category', '')
    search = request.GET.get('search', '')
    date_filter = request.GET.get('date', '')

    products = Product.objects.all().prefetch_related('images').order_by('-created_at')

    if category:
        products = products.filter(category=category)
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(phone__icontains=search) |
            Q(description__icontains=search) | Q(telegram_username__icontains=search)
        )
    if date_filter:
        try:
            filter_date = date.fromisoformat(date_filter)
            products = products.filter(created_at__date=filter_date)
        except ValueError:
            pass

    context = {
        'products': products,
        'category': category,
        'search': search,
        'date_filter': date_filter,
        'active_page': 'products',
        'total_count': products.count(),
    }
    return render(request, 'dashboard/products.html', context)


@login_required_custom
def product_detail(request, pk):
    """Mahsulot batafsil ko'rish"""
    product = get_object_or_404(Product, pk=pk)
    images = product.images.all().order_by('order')
    context = {
        'product': product,
        'images': images,
        'active_page': 'products',
    }
    return render(request, 'dashboard/product_detail.html', context)


@login_required_custom
def product_edit(request, pk):
    """Mahsulotni tahrirlash"""
    product = get_object_or_404(Product, pk=pk)

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.price = request.POST.get('price', product.price)
        product.phone = request.POST.get('phone', product.phone)
        product.description = request.POST.get('description', product.description)
        if product.category == 'kochat':
            product.age = request.POST.get('age', product.age)
            qty = request.POST.get('quantity')
            if qty:
                try:
                    product.quantity = int(qty)
                except ValueError:
                    pass
        product.is_active = request.POST.get('is_active') == 'on'
        product.save()

        # Telegram kanalda ham yangilash
        if product.telegram_message_id:
            try:
                from marketplace.models import BotSettings
                bot_settings = BotSettings.get_settings()
                if bot_settings.bot_token:
                    from telegram import Bot
                    from bot.channel import edit_product_in_channel
                    bot = Bot(token=bot_settings.bot_token)
                    images = product.images.all()
                    asyncio.run(edit_product_in_channel(bot, product, images))
            except Exception as e:
                logger.error(f"Telegram yangilashda xato: {e}")

        return redirect('dashboard:products')

    images = product.images.all().order_by('order')
    context = {
        'product': product,
        'images': images,
        'active_page': 'products',
    }
    return render(request, 'dashboard/product_edit.html', context)


@login_required_custom
@require_POST
def product_delete(request, pk):
    """Mahsulotni o'chirish"""
    product = get_object_or_404(Product, pk=pk)

    # Telegram kanaldan o'chirish
    if product.telegram_message_id:
        try:
            bot_settings = BotSettings.get_settings()
            if bot_settings.bot_token:
                from telegram import Bot
                from bot.channel import delete_product_from_channel
                bot = Bot(token=bot_settings.bot_token)
                asyncio.run(delete_product_from_channel(bot, product))
        except Exception as e:
            logger.error(f"Telegram o'chirishda xato: {e}")

    product.delete()
    return redirect('dashboard:products')


@login_required_custom
@require_POST
def product_toggle(request, pk):
    """Mahsulotni faol/nofaol qilish"""
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=['is_active'])
    return JsonResponse({'status': 'ok', 'is_active': product.is_active})

@login_required_custom
@require_POST
def product_mark_sold(request, pk):
    """Mahsulotni sotildi deb belgilash"""
    from django.utils import timezone
    product = get_object_or_404(Product, pk=pk)
    
    # Toggle (agar qayta bosilsa)
    if product.is_sold:
        product.is_sold = False
        product.is_active = True
        product.sold_at = None
    else:
        product.is_sold = True
        product.is_active = False # Sotilgan bo'lsa faol emas bo'ladi
        product.sold_at = timezone.now()
        
    product.save()

    # Telegram kanalni yangilash (SOTILDI yozuvi qo'shish yoki olib tashlash)
    if product.telegram_message_id:
        try:
            bot_settings = BotSettings.get_settings()
            if bot_settings.bot_token:
                from telegram import Bot
                from bot.channel import edit_product_in_channel
                bot = Bot(token=bot_settings.bot_token)
                images = product.images.all()
                asyncio.run(edit_product_in_channel(bot, product, images))
        except Exception as e:
            logger.error(f"Telegram yangilashda xato: {e}")

    # Sahifaga qarab qayerga qaytishni hal qilamiz
    next_url = request.GET.get('next', 'dashboard:products')
    return redirect(next_url)

@login_required_custom
def sold_products_view(request):
    """Sotilgan mahsulotlar sahifasi"""
    products_list = Product.objects.filter(is_sold=True).order_by('-sold_at')
    
    # Qidiruv va Filtr
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if q:
        products_list = products_list.filter(
            Q(name__icontains=q) | 
            Q(description__icontains=q) |
            Q(phone__icontains=q)
        )
    if category:
        products_list = products_list.filter(category=category)
    if date_from:
        products_list = products_list.filter(sold_at__gte=date_from)
    if date_to:
        products_list = products_list.filter(sold_at__lte=f"{date_to} 23:59:59")
        
    # Xulosa hisobot (nechta ko'chat, nechta meva sotilgani)
    summary_qs = products_list.order_by().values('category').annotate(count=Count('id'))
    # Barcha kategoriyalar uchun default 0 qilib sozlaymiz
    all_categories = ['kochat', 'meva', 'sabzavot', 'parranda', 'tuxum']
    summary = {cat: 0 for cat in all_categories}
    for item in summary_qs:
        summary[item['category']] = item['count'] or 0
    
    paginator = Paginator(products_list, 20)
    page_number = request.GET.get('page')
    products = paginator.get_page(page_number)
    
    context = {
        'products': products,
        'summary': summary,
        'active_menu': 'sold_products',
        'q': q,
        'category': category,
        'date_from': date_from,
        'date_to': date_to,
        'categories': Product.CATEGORY_CHOICES,
    }
    return render(request, 'dashboard/sold_products.html', context)


# ===================== SOZLAMALAR =====================

@login_required_custom
def settings_view(request):
    """Sozlamalar sahifasi"""
    bot_settings = BotSettings.get_settings()
    success = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'save_bot':
            bot_settings.bot_token = request.POST.get('bot_token', '').strip()
            channel_id = request.POST.get('channel_id', '').strip()
            # Kanal ID avtomatik tuzatish — -100 qo'shish
            if channel_id and channel_id.isdigit():
                channel_id = '-100' + channel_id
            bot_settings.channel_id = channel_id
            bot_settings.channel_username = request.POST.get('channel_username', '').strip()
            bot_settings.channel_url = request.POST.get('channel_url', '').strip()
            bot_settings.welcome_message = request.POST.get('welcome_message', '').strip()
            bot_settings.is_active = request.POST.get('is_active') == 'on'
            bot_settings.save()
            success = "✅ Sozlamalar saqlandi!"

        elif action == 'test_bot':
            try:
                from telegram import Bot
                import asyncio
                bot = Bot(token=bot_settings.bot_token)
                async def _test():
                    me = await bot.get_me()
                    return me.username
                username = asyncio.run(_test())
                success = f"✅ Bot ulandi: @{username}"
            except Exception as e:
                error = f"❌ Bot ulanmadi: {str(e)}"

        elif action == 'test_channel':
            try:
                from telegram import Bot
                import asyncio
                bot = Bot(token=bot_settings.bot_token)
                async def _test_ch():
                    chat = await bot.get_chat(bot_settings.channel_id)
                    return chat.title
                title = asyncio.run(_test_ch())
                success = f"✅ Kanal topildi: {title}"
            except Exception as e:
                error = f"❌ Kanal topilmadi: {str(e)}"

    context = {
        'bot_settings': bot_settings,
        'success': success,
        'error': error,
        'active_page': 'settings',
    }
    return render(request, 'dashboard/settings.html', context)


# ===================== DATABASE YUKLAB OLISH =====================

@login_required_custom
def download_database(request):
    """SQLite database ni yuklab olish"""
    db_path = settings.DATABASES['default']['NAME']

    if not os.path.exists(db_path):
        return HttpResponse("Database topilmadi!", status=404)

    file_size = os.path.getsize(db_path)
    filename = f"quva_nihol_db_{timezone.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"

    response = FileResponse(
        open(db_path, 'rb'),
        content_type='application/octet-stream'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['Content-Length'] = file_size
    return response


# ===================== MURAKKAB STATISTIKA =====================

@login_required_custom
def advanced_stats_view(request):
    """Murakkab statistika sahifasi (Daraxtsimon ko'rinish va Fuzzy Matching natijalari)"""
    products = Product.objects.filter(is_active=True)
    
    # Filtrlar
    region_filter = request.GET.get('region', '').strip()
    category_filter = request.GET.get('category', '').strip()
    q = request.GET.get('q', '').strip().lower()
    
    if region_filter:
        products = products.filter(region__icontains=region_filter)
    if category_filter:
        products = products.filter(category=category_filter)
        
    # Daraxt strukturasini yig'ish: Region -> District -> Category -> Product Name -> Count
    tree = {}
    total_count = 0
    
    for p in products:
        # Qidiruv filtrini qo'llash (Name yoki Standardized name bo'yicha)
        if q:
            match_name = p.name.lower()
            match_std = (p.standardized_name or "").lower()
            if q not in match_name and q not in match_std:
                continue
                
        reg = p.region or "Noma'lum hudud"
        dist = p.district or "Noma'lum tuman"
        cat = p.get_category_display()
        if reg not in tree:
            tree[reg] = {}
        if dist not in tree[reg]:
            tree[reg][dist] = {}
        if cat not in tree[reg][dist]:
            tree[reg][dist][cat] = []
            
        tree[reg][dist][cat].append(p)
        total_count += 1
        
    context = {
        'tree': tree,
        'total_count': total_count,
        'regions': Product.objects.exclude(region='').values_list('region', flat=True).distinct(),
        'region_filter': region_filter,
        'category_filter': category_filter,
        'q': request.GET.get('q', ''),
        'active_menu': 'advanced_stats',
    }
    return render(request, 'dashboard/advanced_stats.html', context)


@login_required_custom
def advanced_stats_detail(request):
    """Batafsil mahsulotlarni JSON formatda qaytaradi"""
    reg = request.GET.get('region', '')
    dist = request.GET.get('district', '')
    cat_display = request.GET.get('category', '') # e.g. "🌱 Ko'chat"
    prod_name = request.GET.get('name', '')

    # Reverse category display mapping
    cat_code = None
    for code, display in Product.CATEGORY_CHOICES:
        if display == cat_display:
            cat_code = code
            break

    qs = Product.objects.filter(is_active=True)
    
    if reg:
        if reg != "Noma'lum hudud":
            qs = qs.filter(region=reg)
        else:
            qs = qs.filter(Q(region='') | Q(region__isnull=True))
            
    if dist:
        if dist != "Noma'lum tuman":
            qs = qs.filter(district=dist)
        else:
            qs = qs.filter(Q(district='') | Q(district__isnull=True))

    if cat_code:
        qs = qs.filter(category=cat_code)

    if prod_name:
        if prod_name != "Noma'lum":
            qs = qs.filter(Q(standardized_name__iexact=prod_name) | Q(name__iexact=prod_name))
        else:
            qs = qs.filter(Q(standardized_name='') | Q(standardized_name__isnull=True), Q(name='') | Q(name__isnull=True))

    data = []
    for p in qs:
        image_url = p.images.first().image.url if p.images.exists() else None
        data.append({
            'id': p.id,
            'name': p.name,
            'price': p.format_price(),
            'phone': p.phone,
            'location_text': p.location_text or '',
            'location_lat': p.location_lat,
            'location_lon': p.location_lon,
            'created_at': p.created_at.strftime('%d.%m.%Y %H:%M'),
            'image_url': image_url,
            'edit_url': f'/dashboard/products/{p.id}/edit/',
            'delete_url': f'/dashboard/products/{p.id}/delete/'
        })

    return JsonResponse({'status': 'ok', 'products': data})

@login_required_custom
def orchard_stats_view(request):
    """Daraxt / Bog' statistikasi"""
    from marketplace.models import OrchardRecord
    records = OrchardRecord.objects.filter(is_active=True).order_by('region', 'district', 'tree_type')
    
    # Tree struktura: Viloyat -> Tuman -> Daraxt turi -> (records list, total yield)
    tree = {}
    total_trees = 0
    total_yield = 0
    
    for r in records:
        reg = r.region or "Noma'lum viloyat"
        dist = r.district or "Noma'lum tuman"
        tree_type = (r.tree_type or "Noma'lum").capitalize()
        
        if reg not in tree:
            tree[reg] = {}
        if dist not in tree[reg]:
            tree[reg][dist] = {}
        if tree_type not in tree[reg][dist]:
            tree[reg][dist][tree_type] = {'records': [], 'total_count': 0, 'total_yield': 0}
            
        yld = r.get_estimated_yield_kg()
        tree[reg][dist][tree_type]['records'].append({
            'id': r.id,
            'count': r.tree_count,
            'age': r.tree_age,
            'bearing_age': r.bearing_age,
            'ready_month': r.get_ready_month_display_uz(),
            'yield': yld,
            'phone': r.phone,
            'location': r.location_text or '',
            'created_at': r.created_at.strftime('%d.%m.%Y'),
        })
        tree[reg][dist][tree_type]['total_count'] += r.tree_count
        tree[reg][dist][tree_type]['total_yield'] += yld
        
        total_trees += r.tree_count
        total_yield += yld
        
    context = {
        'tree': tree,
        'total_trees': total_trees,
        'total_yield_tonnes': round(total_yield / 1000, 2),
        'active_menu': 'orchard_stats'
    }
    return render(request, 'dashboard/orchard_stats.html', context)


@login_required_custom
@require_POST
def orchard_delete(request, pk):
    from marketplace.models import OrchardRecord
    r = get_object_or_404(OrchardRecord, pk=pk)
    r.is_active = False
    r.save()
    return redirect('dashboard:orchard_stats')
