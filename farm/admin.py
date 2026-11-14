from django.contrib import admin
from .models import Flock, DailyLog, EggSale, FarmSetting

@admin.register(FarmSetting)
class FarmSettingAdmin(admin.ModelAdmin):
    list_display = ('farm_name', 'default_price_per_crate', 'default_price_per_loose_egg', 'updated_at')

@admin.register(Flock)
class FlockAdmin(admin.ModelAdmin):
    list_display = ('name', 'breed', 'initial_birds', 'current_birds', 'housing_date', 'age_in_weeks', 'is_active')
    list_filter = ('is_active', 'breed')
    search_fields = ('name', 'breed')

@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'flock', 'collection_round', 'crates_collected', 'loose_eggs_collected', 'broken_eggs', 'total_eggs_produced', 'breakage_percentage', 'hen_day_production_pct', 'mortality')
    list_filter = ('flock', 'date', 'collection_round')
    search_fields = ('flock__name', 'notes')

@admin.register(EggSale)
class EggSaleAdmin(admin.ModelAdmin):
    list_display = ('date', 'customer_name', 'crates_sold', 'price_per_crate', 'total_amount', 'amount_paid', 'payment_status', 'payment_method')
    list_filter = ('payment_status', 'payment_method', 'date')
    search_fields = ('customer_name', 'customer_phone', 'notes')
