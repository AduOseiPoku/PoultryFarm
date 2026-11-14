from django import forms
from .models import Flock, DailyLog, EggSale, FarmSetting, FeedPurchase, FeedDistribution
from django.utils import timezone
from decimal import Decimal

class FarmSettingForm(forms.ModelForm):
    class Meta:
        model = FarmSetting
        fields = ['farm_name', 'default_price_per_crate', 'default_price_per_loose_egg', 'low_feed_threshold_bags']
        widgets = {
            'farm_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'EggFarm Pro'}),
            'default_price_per_crate': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01'}),
            'default_price_per_loose_egg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01'}),
            'low_feed_threshold_bags': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 1}),
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
            'customer_name': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'Buyer / Customer Name'}),
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
    """Stock-Out: Record bags fed to a specific shed."""
    class Meta:
        model = FeedDistribution
        fields = ['date', 'flock', 'session', 'feed_type', 'bags_fed', 'weight_per_bag_kg', 'cost_per_bag', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'flock': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'session': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'feed_type': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'Layer Mash'}),
            'bags_fed': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'step': '0.1', 'id': 'id_bags_fed', 'placeholder': 'e.g. 2.5'}),
            'weight_per_bag_kg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'step': '0.5', 'id': 'id_dist_weight'}),
            'cost_per_bag': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'step': '0.01', 'id': 'id_dist_cost', 'placeholder': 'Optional override'}),
            'notes': forms.TextInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'placeholder': 'Notes (e.g. appetite, leftover)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flock'].queryset = Flock.objects.filter(is_active=True)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        
        # Pre-fill with the cost of the latest purchase
        if not self.initial.get('cost_per_bag'):
            last_p = FeedPurchase.objects.order_by('-date').first()
            if last_p:
                self.initial['cost_per_bag'] = last_p.cost_per_bag

        self.fields['cost_per_bag'].required = False
        self.fields['notes'].required = False
