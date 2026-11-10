from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Flock, DailyLog, EggSale
from decimal import Decimal

class HealthCheckTests(TestCase):
    def test_health_check_endpoint(self):
        client = Client()
        response = client.get(reverse('health_check'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get('status'), 'healthy')
        self.assertEqual(data.get('database'), 'connected')

class FarmViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.flock = Flock.objects.create(
            name="Shed 1 - Test Batch",
            breed="Lohmann Brown",
            housing_date=timezone.now().date(),
            initial_birds=1000,
            current_birds=1000,
            is_active=True,
        )

    def test_dashboard_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "EggFarm")

    def test_daily_log_calculation(self):
        log = DailyLog.objects.create(
            flock=self.flock,
            date=timezone.now().date(),
            crates_collected=10,
            loose_eggs_collected=5,
            broken_eggs=3,
            mortality=2,
            culls=1,
            feed_consumed_kg=Decimal('120.5'),
        )
        self.assertEqual(log.total_good_eggs, 305)
        self.assertEqual(log.total_eggs_produced, 308)
        self.flock.refresh_from_db()
        self.assertEqual(self.flock.current_birds, 997)

    def test_egg_sale_calculation(self):
        sale = EggSale.objects.create(
            date=timezone.now().date(),
            customer_name="Test Baker",
            crates_sold=5,
            price_per_crate=Decimal('40.00'),
            loose_eggs_sold=0,
            price_per_loose_egg=Decimal('0.00'),
            amount_paid=Decimal('100.00'),
        )
        self.assertEqual(sale.total_amount, Decimal('200.00'))
        self.assertEqual(sale.balance_due, Decimal('100.00'))
        self.assertEqual(sale.payment_status, 'PARTIAL')
