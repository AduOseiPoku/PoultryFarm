from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Flocks
    path('flocks/', views.flock_list, name='flock_list'),
    path('flocks/add/', views.flock_create, name='flock_create'),

    # Daily Logs
    path('logs/', views.log_list, name='log_list'),
    path('logs/add/', views.log_create, name='log_create'),
    path('logs/<int:pk>/edit/', views.log_edit, name='log_edit'),

    # Sales
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/add/', views.sales_create, name='sales_create'),

    # Egg Inventory
    path('inventory/', views.inventory_view, name='inventory'),

    # Feed Management & Inventory
    path('feed/', views.feed_dashboard, name='feed_dashboard'),
    path('feed/distribute/', views.feed_distribute_create, name='feed_distribute_create'),
    path('feed/purchase/', views.feed_purchase_create, name='feed_purchase_create'),

    # Pricing & Farm Settings
    path('settings/', views.farm_settings_view, name='farm_settings'),
]
