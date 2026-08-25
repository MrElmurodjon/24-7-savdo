from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.index, name='index'),
    path('dashboard/products/', views.products_view, name='products'),
    path('dashboard/products/<int:pk>/', views.product_detail, name='product_detail'),
    path('dashboard/products/<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('dashboard/products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('dashboard/products/<int:pk>/toggle/', views.product_toggle, name='product_toggle'),
    path('dashboard/settings/', views.settings_view, name='settings'),
    path('dashboard/download-db/', views.download_database, name='download_db'),
    path('dashboard/advanced-stats/', views.advanced_stats_view, name='advanced_stats'),
    path('dashboard/advanced-stats/detail/', views.advanced_stats_detail, name='advanced_stats_detail'),
    path('dashboard/orchard-stats/', views.orchard_stats_view, name='orchard_stats'),
    path('dashboard/orchard-stats/<int:pk>/delete/', views.orchard_delete, name='orchard_delete'),
]
