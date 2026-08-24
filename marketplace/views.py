from django.http import JsonResponse
from .models import Product

def api_products(request):
    products = Product.objects.filter(is_active=True).values(
        'id', 'category', 'name', 'price', 'phone', 'created_at'
    )
    return JsonResponse(list(products), safe=False)
