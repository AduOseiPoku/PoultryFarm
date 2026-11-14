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
        self.assertContains(response, "Oppong Farms")

    def test_mobile_drawer_navigation_present(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        # Ensure mobile drawer toggle button and inline SVG are present
        self.assertContains(response, 'id="mobile-drawer-toggle"')
        self.assertContains(response, 'onclick="openMobileDrawer()"')
        # Ensure mobile drawer aside panel and backdrop are present
        self.assertContains(response, 'id="mobile-drawer-panel"')
        self.assertContains(response, 'id="mobile-drawer-backdrop"')
        self.assertContains(response, 'id="mobile-drawer-close"')
        self.assertContains(response, 'onclick="closeMobileDrawer()"')
        # Ensure drawer JS functions are declared
        self.assertContains(response, 'function openMobileDrawer()')
        self.assertContains(response, 'function closeMobileDrawer()')

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

    def test_egg_sale_optional_customer_name(self):
        # Create some inventory first
        DailyLog.objects.create(
            flock=self.flock,
            date=timezone.now().date(),
            crates_collected=10,
            loose_eggs_collected=0,
            broken_eggs=0,
        )

        # Model creation without customer_name
        sale = EggSale.objects.create(
            date=timezone.now().date(),
            customer_name="",
            crates_sold=3,
            price_per_crate=Decimal('40.00'),
        )
        self.assertEqual(sale.customer_name, "")
        self.assertIn("Walk-in Buyer", str(sale))

        # Form submission without customer_name
        response = self.client.post(reverse('sales_create'), {
            'date': timezone.now().date().isoformat(),
            'customer_name': '',
            'crates_sold': 2,
            'price_per_crate': '40.00',
            'loose_eggs_sold': '0',
            'price_per_loose_egg': '0.00',
            'amount_paid': '80.00',
            'payment_method': 'CASH',
        })
        self.assertEqual(response.status_code, 302)
        created_sale = EggSale.objects.filter(crates_sold=2).latest('created_at')
        self.assertEqual(created_sale.customer_name, "")

    def test_egg_sale_stock_validation_prevents_overselling(self):
        # Setup: 5 crates in stock (150 eggs)
        DailyLog.objects.create(
            flock=self.flock,
            date=timezone.now().date(),
            crates_collected=5,
            loose_eggs_collected=0,
            broken_eggs=0,
        )

        # Try selling 6 crates (180 eggs) -> should fail
        response = self.client.post(reverse('sales_create'), {
            'date': timezone.now().date().isoformat(),
            'customer_name': 'Greedy Buyer',
            'crates_sold': 6,
            'price_per_crate': '40.00',
            'loose_eggs_sold': '0',
            'price_per_loose_egg': '0.00',
            'amount_paid': '0.00',
            'payment_method': 'CASH',
        })
        self.assertEqual(response.status_code, 200)  # Re-rendered with form errors
        self.assertFalse(EggSale.objects.filter(customer_name='Greedy Buyer').exists())
        self.assertContains(response, "Insufficient stock")

    def test_egg_sale_stock_validation_prevents_zero_eggs(self):
        # Setup: 5 crates in stock
        DailyLog.objects.create(
            flock=self.flock,
            date=timezone.now().date(),
            crates_collected=5,
            loose_eggs_collected=0,
            broken_eggs=0,
        )

        # Try selling 0 crates and 0 loose eggs -> should fail
        response = self.client.post(reverse('sales_create'), {
            'date': timezone.now().date().isoformat(),
            'customer_name': 'Zero Buyer',
            'crates_sold': 0,
            'price_per_crate': '40.00',
            'loose_eggs_sold': '0',
            'price_per_loose_egg': '0.00',
            'amount_paid': '0.00',
            'payment_method': 'CASH',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EggSale.objects.filter(customer_name='Zero Buyer').exists())

    def test_feed_distribution_in_cups(self):
        from .models import FeedDistribution
        response = self.client.post(reverse('feed_distribute_create'), {
            'date': timezone.now().date().isoformat(),
            'flock': self.flock.id,
            'session': 'MORNING',
            'cups_fed': '12.0',
            'notes': 'Normal morning feeding',
        })
        self.assertEqual(response.status_code, 302)
        dist = FeedDistribution.objects.latest('created_at')
        self.assertEqual(dist.cups_fed, Decimal('12.0'))
        self.assertEqual(dist.total_kg_fed, Decimal('12.00'))
        self.assertEqual(dist.bags_fed, Decimal('0.24'))
        self.assertEqual(dist.grams_per_bird, 12.0)
