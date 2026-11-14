from django.db import models, transaction
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from django.utils import timezone
from decimal import Decimal

class FarmSetting(models.Model):
    """Stores global farm configurations such as default egg pricing."""
    default_price_per_crate = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('40.00'),
        help_text="Default selling price per full crate (30 eggs)"
    )
    default_price_per_loose_egg = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Default selling price per individual loose egg"
    )
    farm_name = models.CharField(max_length=150, default="EggFarm Pro")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Farm Settings (Crate: GH₵{self.default_price_per_crate})"

    @classmethod
    def get_settings(cls):
        """Returns the singleton settings instance, creating it if it doesn't exist."""
        setting, _ = cls.objects.get_or_create(id=1)
        return setting


class FlockQuerySet(models.QuerySet):
    def with_mortality(self):
        """Annotates each flock with its cumulative mortality in a single query."""
        return self.annotate(
            annotated_mortality=Coalesce(Sum('daily_logs__mortality'), Value(0))
        )

class Flock(models.Model):
    name = models.CharField(max_length=100, help_text="e.g. Shed 1 - Lohmann Brown")
    breed = models.CharField(max_length=100, blank=True, null=True, help_text="e.g. Lohmann Brown, Hy-Line, ISA Brown")
    housing_date = models.DateField(default=timezone.now, help_text="Date the birds were placed in the shed")
    initial_birds = models.PositiveIntegerField(help_text="Starting number of birds")
    current_birds = models.PositiveIntegerField(help_text="Live birds currently in flock")
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = FlockQuerySet.as_manager()

    def __str__(self):
        return f"{self.name} ({self.current_birds} birds)"

    @property
    def total_mortality(self):
        if hasattr(self, 'annotated_mortality'):
            return self.annotated_mortality or 0
        return sum(log.mortality for log in self.daily_logs.all())

    @property
    def age_in_weeks(self):
        days = (timezone.now().date() - self.housing_date).days
        return max(0, days // 7)


class DailyLog(models.Model):
    ROUND_CHOICES = [
        ('MORNING', 'Morning (1st Round)'),
        ('AFTERNOON', 'Afternoon (2nd Round)'),
        ('EVENING', 'Evening (3rd Round)'),
        ('GENERAL', 'General / Full Day'),
    ]

    flock = models.ForeignKey(Flock, on_delete=models.CASCADE, related_name='daily_logs')
    date = models.DateField(default=timezone.now, db_index=True)
    collection_round = models.CharField(max_length=15, choices=ROUND_CHOICES, default='MORNING', help_text="Collection batch")
    
    # Bird count change
    mortality = models.PositiveIntegerField(default=0, help_text="Dead birds collected this round")
    culls = models.PositiveIntegerField(default=0, help_text="Sick/culled birds removed this round")
    
    # Egg collections
    crates_collected = models.PositiveIntegerField(default=0, help_text="Full crates of good eggs (30 eggs/crate)")
    loose_eggs_collected = models.PositiveIntegerField(default=0, help_text="Loose good eggs (< 30)")
    broken_eggs = models.PositiveIntegerField(default=0, help_text="Cracked, broken, or soft-shelled eggs")
    
    # Feed & Notes
    feed_consumed_kg = models.DecimalField(max_digits=6, decimal_places=2, default=0.0, help_text="Total feed in kg")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['-date', '-created_at']),
        ]

    def __str__(self):
        return f"{self.flock.name} - {self.date} ({self.get_collection_round_display()})"

    @property
    def total_good_eggs(self):
        return (self.crates_collected * 30) + self.loose_eggs_collected

    @property
    def total_eggs_produced(self):
        return self.total_good_eggs + self.broken_eggs

    @property
    def breakage_percentage(self):
        total = self.total_eggs_produced
        if total > 0:
            return round((self.broken_eggs / total) * 100, 2)
        return 0.0

    @property
    def hen_day_production_pct(self):
        if self.flock.current_birds > 0:
            return round((self.total_eggs_produced / self.flock.current_birds) * 100, 2)
        return 0.0

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        old_loss = 0
        if not is_new:
            old_instance = DailyLog.objects.get(pk=self.pk)
            old_loss = old_instance.mortality + old_instance.culls

        new_loss = self.mortality + self.culls
        net_difference = new_loss - old_loss

        with transaction.atomic():
            super().save(*args, **kwargs)
            if net_difference != 0:
                self.flock.current_birds = max(0, self.flock.current_birds - net_difference)
                self.flock.save(update_fields=['current_birds'])


class EggSale(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PAID', 'Fully Paid'),
        ('PARTIAL', 'Partially Paid'),
        ('UNPAID', 'Credit / Unpaid'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('CASH', 'Cash'),
        ('TRANSFER', 'Bank Transfer'),
        ('POS', 'POS / Card'),
        ('OTHER', 'Other'),
    ]

    date = models.DateField(default=timezone.now, db_index=True)
    customer_name = models.CharField(max_length=150, help_text="Buyer name or store")
    customer_phone = models.CharField(max_length=20, blank=True, null=True)
    
    crates_sold = models.PositiveIntegerField(default=0, help_text="Number of crates (30 eggs/crate)")
    loose_eggs_sold = models.PositiveIntegerField(default=0, help_text="Loose eggs sold")
    price_per_crate = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price per crate")
    price_per_loose_egg = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PAID', db_index=True)
    payment_method = models.CharField(max_length=15, choices=PAYMENT_METHOD_CHOICES, default='CASH')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['payment_status', '-date']),
            models.Index(fields=['-date', '-created_at']),
        ]

    def __str__(self):
        return f"{self.date} - {self.customer_name} ({self.crates_sold} crates)"

    @property
    def balance_due(self):
        return max(Decimal('0.00'), self.total_amount - self.amount_paid)

    def save(self, *args, **kwargs):
        crates_total = Decimal(self.crates_sold) * Decimal(self.price_per_crate)
        loose_total = Decimal(self.loose_eggs_sold) * Decimal(self.price_per_loose_egg)
        self.total_amount = crates_total + loose_total

        if self.amount_paid >= self.total_amount and self.total_amount > 0:
            self.payment_status = 'PAID'
        elif self.amount_paid > Decimal('0.00'):
            self.payment_status = 'PARTIAL'
        else:
            self.payment_status = 'UNPAID'

        super().save(*args, **kwargs)
