from django.db import models
from django.utils import timezone


class BotSettings(models.Model):
    """Telegram bot sozlamalari"""
    bot_token = models.CharField(max_length=200, blank=True, verbose_name="Bot Token")
    channel_id = models.CharField(max_length=100, blank=True, verbose_name="Kanal ID")
    channel_username = models.CharField(max_length=100, blank=True, verbose_name="Kanal Username (@...)")
    channel_url = models.URLField(max_length=200, blank=True, verbose_name="Kanal havolasi (Ssilkasi)")
    welcome_message = models.TextField(
        blank=True,
        default="🌿 Quva Nihol Marketplacega Xush Kelibsiz!\n\nBu yerda ko'chat va meva-sabzavot sotish mumkin.",
        verbose_name="Xush kelibsiz xabari"
    )
    is_active = models.BooleanField(default=True, verbose_name="Bot faolmi?")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bot Sozlamalari"
        verbose_name_plural = "Bot Sozlamalari"

    def __str__(self):
        return f"Bot Sozlamalari (#{self.pk})"

    @classmethod
    def get_settings(cls):
        """Joriy sozlamalarni qaytaradi yoki yangi yaratadi"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class Product(models.Model):
    """Mahsulot modeli"""
    CATEGORY_CHOICES = [
        ('kochat', "🌱 Ko'chat"),
        ('meva', '🍎 Meva/Mahsulot'),
        ('sabzavot', '🥕 Sabzavot'),
        ('parranda', '🐔 Parranda'),
        ('tuxum', '🥚 Tuxum'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Mahsulot turi")
    name = models.CharField(max_length=200, verbose_name="Turi/Nomi")
    standardized_name = models.CharField(max_length=200, blank=True, verbose_name="Standart nomi (To'g'rilangan)")
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Narxi (so'm)")
    quantity = models.IntegerField(null=True, blank=True, verbose_name="Soni (dona)")
    age = models.CharField(max_length=50, blank=True, verbose_name="Yoshi")
    weight = models.CharField(max_length=50, blank=True, verbose_name="Og'irligi/Massasi")
    gender = models.CharField(max_length=50, blank=True, verbose_name="Jinsi (Erkak/Urg'ochi)")
    milk_yield = models.CharField(max_length=50, blank=True, verbose_name="Sut berishi (litrda)")
    phone = models.CharField(max_length=20, verbose_name="Telefon raqami")
    location_lat = models.FloatField(null=True, blank=True, verbose_name="Kenglik")
    location_lon = models.FloatField(null=True, blank=True, verbose_name="Uzunlik")
    location_text = models.CharField(max_length=300, blank=True, verbose_name="Manzil matni")
    region = models.CharField(max_length=100, blank=True, verbose_name="Viloyat")
    district = models.CharField(max_length=100, blank=True, verbose_name="Tuman/Shahar")
    description = models.TextField(blank=True, verbose_name="Qo'shimcha ma'lumot")

    # Telegram ma'lumotlari
    telegram_message_id = models.BigIntegerField(null=True, blank=True, verbose_name="Telegram xabar ID")
    telegram_user_id = models.BigIntegerField(null=True, blank=True, verbose_name="Telegram foydalanuvchi ID")
    telegram_username = models.CharField(max_length=100, blank=True, verbose_name="Telegram username")
    telegram_full_name = models.CharField(max_length=200, blank=True, verbose_name="Telegram ism")

    is_active = models.BooleanField(default=True, verbose_name="Faolmi?")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Qo'shilgan sana")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan sana")

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_category_display()} — {self.name} ({self.price:,} so'm)"

    def get_location_url(self):
        if self.location_lat and self.location_lon:
            return f"https://www.google.com/maps?q={self.location_lat},{self.location_lon}"
        return None

    def format_price(self):
        return f"{int(self.price):,}".replace(',', ' ')


class ProductImage(models.Model):
    """Mahsulot rasmlari"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Mahsulot")
    image = models.ImageField(upload_to='products/%Y/%m/', verbose_name="Rasm")
    telegram_file_id = models.CharField(max_length=200, blank=True, verbose_name="Telegram file ID")
    order = models.IntegerField(default=0, verbose_name="Tartib")

    class Meta:
        verbose_name = "Rasm"
        verbose_name_plural = "Rasmlar"
        ordering = ['order']

    def __str__(self):
        return f"Rasm #{self.order} — {self.product.name}"
