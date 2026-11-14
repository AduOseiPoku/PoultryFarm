from django import forms
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from .models import Flock, DailyLog, EggSale, FarmSetting, FeedPurchase, FeedDistribution
from django.utils import timezone
from decimal import Decimal

class FarmSettingForm(forms.ModelForm):
    class Meta:
        model = FarmSetting
        fields = ['farm_name', 'default_price_per_crate', 'default_price_per_loose_egg', 'low_feed_threshold_bags', 'feed_cup_weight_kg']
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'EggFarm Pro'}),
            'default_price_per_crate': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01'}),
            'default_price_per_loose_egg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01'}),
            'low_feed_threshold_bags': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 1}),
            'feed_cup_weight_kg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0.1, 'step': '0.05', 'placeholder': '1.00'}),
        }


class FlockForm(forms.ModelForm):
    class Meta:
        model = Flock
        fields = ['name', 'breed', 'housing_date', 'initial_birds', 'current_birds', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'e.g. Shed 1 - Batch A'}),
            'breed': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'e.g. Lohmann Brown'}),
            'housing_date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'initial_birds': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0}),
            'current_birds': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0}),
            'is_active': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-amber-600 focus:ring-amber-500 border-gray-300 rounded'}),
        }


class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['flock', 'date', 'collection_round', 'crates_collected', 'loose_eggs_collected', 'broken_eggs', 'mortality', 'culls', 'notes']
        widgets = {
            'flock': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'collection_round': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'crates_collected': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'id': 'id_crates'}),
            'loose_eggs_collected': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'max': 29, 'id': 'id_loose', 'placeholder': '0'}),
            'broken_eggs': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'id': 'id_broken', 'placeholder': '0'}),
            'mortality': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'placeholder': '0'}),
            'culls': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'placeholder': '0'}),
            'notes': forms.Textarea(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'rows': 2, 'placeholder': 'Optional observations (e.g. egg size, flock behaviour)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flock'].queryset = Flock.objects.filter(is_active=True)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        
        current_hour = timezone.now().hour
        if not self.initial.get('collection_round'):
            if current_hour < 12:
                self.initial['collection_round'] = 'MORNING'
            elif current_hour < 16:
                self.initial['collection_round'] = 'AFTERNOON'
            else:
                self.initial['collection_round'] = 'EVENING'

        self.fields['loose_eggs_collected'].required = False
        self.fields['broken_eggs'].required = False
        self.fields['mortality'].required = False
        self.fields['culls'].required = False
        self.fields['notes'].required = False

    def clean_loose_eggs_collected(self):
        return self.cleaned_data.get('loose_eggs_collected') or 0

    def clean_broken_eggs(self):
        return self.cleaned_data.get('broken_eggs') or 0

    def clean_mortality(self):
        return self.cleaned_data.get('mortality') or 0

    def clean_culls(self):
        return self.cleaned_data.get('culls') or 0


class EggSaleForm(forms.ModelForm):
    class Meta:
        model = EggSale
        fields = ['date', 'customer_name', 'customer_phone', 'crates_sold', 'loose_eggs_sold', 'price_per_crate', 'price_per_loose_egg', 'amount_paid', 'payment_method', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'customer_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'Buyer / Customer Name (Optional)'}),
            'customer_phone': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'e.g. +1 555-0123'}),
            'crates_sold': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'id': 'id_crates_sold'}),
            'loose_eggs_sold': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'id': 'id_loose_sold', 'placeholder': '0'}),
            'price_per_crate': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01', 'id': 'id_price_crate'}),
            'price_per_loose_egg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01', 'id': 'id_price_loose', 'placeholder': '0.00'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01', 'id': 'id_amount_paid', 'placeholder': '0.00'}),
            'payment_method': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'notes': forms.Textarea(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'rows': 2, 'placeholder': 'Payment reference or notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()

        settings = FarmSetting.get_settings()
        if not self.initial.get('price_per_crate'):
            self.initial['price_per_crate'] = settings.default_price_per_crate
        if not self.initial.get('price_per_loose_egg'):
            self.initial['price_per_loose_egg'] = settings.default_price_per_loose_egg
        
        self.fields['customer_name'].required = False
        self.fields['customer_phone'].required = False
        self.fields['loose_eggs_sold'].required = False
        self.fields['price_per_crate'].required = False
        self.fields['price_per_loose_egg'].required = False
        self.fields['amount_paid'].required = False
        self.fields['notes'].required = False

        if not self.initial.get('loose_eggs_sold'):
            self.initial['loose_eggs_sold'] = 0
        if not self.initial.get('amount_paid'):
            self.initial['amount_paid'] = Decimal('0.00')

    def clean_price_per_crate(self):
        price = self.cleaned_data.get('price_per_crate')
        if price is None or price == '':
            settings = FarmSetting.get_settings()
            return settings.default_price_per_crate
        return price

    def clean_loose_eggs_sold(self):
        return self.cleaned_data.get('loose_eggs_sold') or 0

    def clean_price_per_loose_egg(self):
        price = self.cleaned_data.get('price_per_loose_egg')
        if price is None or price == '':
            settings = FarmSetting.get_settings()
            return settings.default_price_per_loose_egg
        return price

    def clean_amount_paid(self):
        return self.cleaned_data.get('amount_paid') or Decimal('0.00')

    def clean(self):
        cleaned_data = super().clean()
        crates = cleaned_data.get('crates_sold') or 0
        loose = cleaned_data.get('loose_eggs_sold') or 0

        if crates <= 0 and loose <= 0:
            raise forms.ValidationError("You must sell at least 1 crate or 1 loose egg.")

        # Check against available stock
        total_produced = DailyLog.objects.aggregate(
            crates=Coalesce(Sum('crates_collected'), Value(0)),
            loose=Coalesce(Sum('loose_eggs_collected'), Value(0)),
        )
        total_sold = EggSale.objects.aggregate(
            crates=Coalesce(Sum('crates_sold'), Value(0)),
            loose=Coalesce(Sum('loose_eggs_sold'), Value(0)),
        )

        crates_in_stock = max(0, total_produced['crates'] - total_sold['crates'])
        loose_in_stock = max(0, total_produced['loose'] - total_sold['loose'])
        total_eggs_in_stock = (crates_in_stock * 30) + loose_in_stock
        requested_eggs = (crates * 30) + loose

        if requested_eggs > total_eggs_in_stock:
            raise forms.ValidationError(
                f"Insufficient stock! You requested {crates} crates and {loose} loose eggs ({requested_eggs} eggs), but only {crates_in_stock} crates and {loose_in_stock} loose eggs ({total_eggs_in_stock} total eggs) are in stock."
            )

        return cleaned_data


class FeedPurchaseForm(forms.ModelForm):
    """Stock-In: Record a feed delivery from supplier."""
    class Meta:
        model = FeedPurchase
        fields = ['date', 'supplier_name', 'feed_type', 'bags_purchased', 'weight_per_bag_kg', 'cost_per_bag', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'supplier_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'e.g. Central Feed Mills Ltd'}),
            'feed_type': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'bags_purchased': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 1, 'id': 'id_bags_purchased', 'placeholder': 'e.g. 50'}),
            'weight_per_bag_kg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'step': '0.5', 'id': 'id_weight_per_bag'}),
            'cost_per_bag': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'step': '0.01', 'id': 'id_cost_per_bag', 'placeholder': 'e.g. 25.50'}),
            'notes': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'Invoice # or batch number'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        self.fields['notes'].required = False


class FeedDistributionForm(forms.ModelForm):
    """Stock-Out: Record cups/scoops fed to a specific shed."""
    class Meta:
        model = FeedDistribution
        fields = ['date', 'flock', 'session', 'cups_fed', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'flock': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'session': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'cups_fed': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2.5 text-base font-bold text-amber-700 border', 'step': '0.5', 'min': '0.1', 'id': 'id_cups_fed', 'placeholder': 'e.g. 10 or 12.5'}),
            'notes': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'Optional notes (e.g. high appetite, leftover in trough)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flock'].queryset = Flock.objects.filter(is_active=True)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        self.fields['cups_fed'].label = "Feed Given (Cups / Scoops)"
        self.fields['notes'].required = False

    def clean_cups_fed(self):
        cups = self.cleaned_data.get('cups_fed')
        if not cups or cups <= 0:
            raise forms.ValidationError("Please enter a valid number of cups fed (greater than 0).")
        return cups
