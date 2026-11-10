from django import forms
from .models import Flock, DailyLog, EggSale
from django.utils import timezone
from decimal import Decimal

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
        fields = ['flock', 'date', 'collection_round', 'crates_collected', 'loose_eggs_collected', 'broken_eggs', 'mortality', 'culls', 'feed_consumed_kg', 'notes']
        widgets = {
            'flock': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'date': forms.DateInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'type': 'date'}),
            'collection_round': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'crates_collected': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'id': 'id_crates'}),
            'loose_eggs_collected': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'max': 29, 'id': 'id_loose', 'placeholder': '0'}),
            'broken_eggs': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'id': 'id_broken', 'placeholder': '0'}),
            'mortality': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'placeholder': '0'}),
            'culls': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'placeholder': '0'}),
            'feed_consumed_kg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.1', 'placeholder': '0.0'}),
            'notes': forms.Textarea(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'rows': 2, 'placeholder': 'Optional observations (e.g. egg size, flock behaviour)'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flock'].queryset = Flock.objects.filter(is_active=True)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        
        # Auto-suggest collection round based on current hour
        current_hour = timezone.now().hour
        if not self.initial.get('collection_round'):
            if current_hour < 12:
                self.initial['collection_round'] = 'MORNING'
            elif current_hour < 16:
                self.initial['collection_round'] = 'AFTERNOON'
            else:
                self.initial['collection_round'] = 'EVENING'

        # Optional fields fallback safely
        self.fields['loose_eggs_collected'].required = False
        self.fields['broken_eggs'].required = False
        self.fields['mortality'].required = False
        self.fields['culls'].required = False
        self.fields['feed_consumed_kg'].required = False
        self.fields['notes'].required = False

    def clean_loose_eggs_collected(self):
        return self.cleaned_data.get('loose_eggs_collected') or 0

    def clean_broken_eggs(self):
        return self.cleaned_data.get('broken_eggs') or 0

    def clean_mortality(self):
        return self.cleaned_data.get('mortality') or 0

    def clean_culls(self):
        return self.cleaned_data.get('culls') or 0

    def clean_feed_consumed_kg(self):
        return self.cleaned_data.get('feed_consumed_kg') or Decimal('0.0')


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
            'price_per_crate': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01', 'id': 'id_price_crate', 'placeholder': '0.00'}),
            'price_per_loose_egg': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01', 'id': 'id_price_loose', 'placeholder': '0.00'}),
            'amount_paid': forms.NumberInput(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'min': 0, 'step': '0.01', 'id': 'id_amount_paid', 'placeholder': '0.00'}),
            'payment_method': forms.Select(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border'}),
            'notes': forms.Textarea(attrs={'class': 'w-full rounded-lg border-gray-300 focus:border-amber-500 focus:ring-amber-500 shadow-sm px-4 py-2 text-sm border', 'rows': 2, 'placeholder': 'Payment reference or notes'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.initial.get('date'):
            self.initial['date'] = timezone.now().date()
        
        self.fields['customer_phone'].required = False
        self.fields['loose_eggs_sold'].required = False
        self.fields['price_per_loose_egg'].required = False
        self.fields['amount_paid'].required = False
        self.fields['notes'].required = False

        if not self.initial.get('price_per_loose_egg'):
            self.initial['price_per_loose_egg'] = Decimal('0.00')
        if not self.initial.get('loose_eggs_sold'):
            self.initial['loose_eggs_sold'] = 0
        if not self.initial.get('amount_paid'):
            self.initial['amount_paid'] = Decimal('0.00')

    def clean_loose_eggs_sold(self):
        return self.cleaned_data.get('loose_eggs_sold') or 0

    def clean_price_per_loose_egg(self):
        return self.cleaned_data.get('price_per_loose_egg') or Decimal('0.00')

    def clean_amount_paid(self):
        return self.cleaned_data.get('amount_paid') or Decimal('0.00')
