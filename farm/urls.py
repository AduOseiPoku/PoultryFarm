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

    # Inventory
    path('inventory/', views.inventory_view, name='inventory'),
]
