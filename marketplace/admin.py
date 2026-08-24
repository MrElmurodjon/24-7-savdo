from django.contrib import admin
from .models import BotSettings, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'phone', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'phone']
    inlines = [ProductImageInline]


@admin.register(BotSettings)
class BotSettingsAdmin(admin.ModelAdmin):
    list_display = ['pk', 'channel_username', 'is_active', 'updated_at']
