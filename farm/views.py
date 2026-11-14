from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, Value, Count, Q
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import Flock, DailyLog, EggSale, FarmSetting, FeedPurchase, FeedDistribution
from .forms import (
    FlockForm, DailyLogForm, EggSaleForm, FarmSettingForm, 
    FeedPurchaseForm, FeedDistributionForm
)

def dashboard(request):
    today = timezone.now().date()
    seven_days_ago = today - timedelta(days=6)

    # 1. Combined Flock Stats (1 query: birds sum + count)
    flock_stats = Flock.objects.filter(is_active=True).aggregate(
        total_birds=Coalesce(Sum('current_birds'), Value(0)),
        flocks_count=Count('id')
    )
    total_live_birds = flock_stats['total_birds']
    flocks_count = flock_stats['flocks_count']

    # 2. Combined DailyLog Stats (1 query: today's collection + all-time collection)
    log_stats = DailyLog.objects.aggregate(
        today_crates=Coalesce(Sum('crates_collected', filter=Q(date=today)), Value(0)),
        today_loose=Coalesce(Sum('loose_eggs_collected', filter=Q(date=today)), Value(0)),
        today_broken=Coalesce(Sum('broken_eggs', filter=Q(date=today)), Value(0)),
        today_mortality=Coalesce(Sum('mortality', filter=Q(date=today)), Value(0)),
        all_time_crates=Coalesce(Sum('crates_collected'), Value(0)),
        all_time_loose=Coalesce(Sum('loose_eggs_collected'), Value(0)),
    )
    today_crates = log_stats['today_crates']
    today_loose = log_stats['today_loose']
    today_broken = log_stats['today_broken']
    today_mortality = log_stats['today_mortality']

    today_good_eggs = (today_crates * 30) + today_loose
    today_total_eggs = today_good_eggs + today_broken
    today_breakage_pct = round((today_broken / today_total_eggs * 100), 2) if today_total_eggs > 0 else 0.0
    today_hdp = round((today_total_eggs / total_live_birds * 100), 2) if total_live_birds > 0 else 0.0

    # 3. Combined EggSale Stats (1 query: today's sales + all-time sales)
    sale_stats = EggSale.objects.aggregate(
        today_crates=Coalesce(Sum('crates_sold', filter=Q(date=today)), Value(0)),
        today_revenue=Coalesce(Sum('total_amount', filter=Q(date=today)), Value(Decimal('0.00'))),
        all_time_crates=Coalesce(Sum('crates_sold'), Value(0)),
        all_time_loose=Coalesce(Sum('loose_eggs_sold'), Value(0)),
    )
    today_crates_sold = sale_stats['today_crates']
    today_revenue = sale_stats['today_revenue']

    # Stock on Hand derived from the consolidated queries
    crates_in_stock = max(0, log_stats['all_time_crates'] - sale_stats['all_time_crates'])
    loose_in_stock = max(0, log_stats['all_time_loose'] - sale_stats['all_time_loose'])

    # 4. Feed Inventory & Financial Metrics
    total_feed_purchased_bags = FeedPurchase.objects.aggregate(
        total=Coalesce(Sum('bags_purchased'), Value(0))
    )['total']
    total_feed_fed_bags = FeedDistribution.objects.aggregate(
        total=Coalesce(Sum('bags_fed'), Value(Decimal('0.00')))
    )['total']
    current_feed_bags = max(Decimal('0.00'), Decimal(total_feed_purchased_bags) - total_feed_fed_bags)

    # Today's Feeding Summary
    today_feed_stats = FeedDistribution.objects.filter(date=today).aggregate(
        kg=Coalesce(Sum('total_kg_fed'), Value(Decimal('0.00'))),
        cost=Coalesce(Sum('total_cost'), Value(Decimal('0.00'))),
    )
    today_feed_kg = today_feed_stats['kg']
    today_feed_cost = today_feed_stats['cost']

    # Today's Net Margin = Today's Egg Revenue - Today's Feed Cost
    today_net_margin = today_revenue - today_feed_cost

    # Grams per bird across active flock today
    today_grams_per_bird = (
        round((float(today_feed_kg) * 1000) / total_live_birds, 1)
        if total_live_birds > 0 else 0.0
    )

    settings = FarmSetting.get_settings()
    is_feed_low = current_feed_bags <= settings.low_feed_threshold_bags

    # 5. 7-Day Trend Chart Queries
    chart_dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    chart_labels = [d.strftime('%b %d') for d in chart_dates]

    logs_by_date = {
        item['date']: item
        for item in DailyLog.objects.filter(date__gte=seven_days_ago, date__lte=today)
        .values('date')
        .annotate(
            crates=Coalesce(Sum('crates_collected'), Value(0)),
            broken=Coalesce(Sum('broken_eggs'), Value(0)),
        )
    }

    sales_by_date = {
        item['date']: item['crates']
        for item in EggSale.objects.filter(date__gte=seven_days_ago, date__lte=today)
        .values('date')
        .annotate(
            crates=Coalesce(Sum('crates_sold'), Value(0)),
        )
    }

    chart_crates_produced = [logs_by_date.get(d, {}).get('crates', 0) for d in chart_dates]
    chart_broken_eggs = [logs_by_date.get(d, {}).get('broken', 0) for d in chart_dates]
    chart_crates_sold = [sales_by_date.get(d, 0) for d in chart_dates]

    # Recent activity lists
    recent_logs = DailyLog.objects.select_related('flock')[:6]
    recent_sales = EggSale.objects.all()[:6]
    recent_feedings = FeedDistribution.objects.select_related('flock')[:5]

    context = {
        'flocks_count': flocks_count,
        'total_live_birds': total_live_birds,
        'today_crates': today_crates,
        'today_loose': today_loose,
        'today_broken': today_broken,
        'today_good_eggs': today_good_eggs,
        'today_total_eggs': today_total_eggs,
        'today_breakage_pct': today_breakage_pct,
        'today_hdp': today_hdp,
        'today_mortality': today_mortality,
        'today_crates_sold': today_crates_sold,
        'today_revenue': today_revenue,
        'crates_in_stock': crates_in_stock,
        'loose_in_stock': loose_in_stock,
        # Feed context
        'current_feed_bags': current_feed_bags,
        'today_feed_kg': today_feed_kg,
        'today_feed_cost': today_feed_cost,
        'today_net_margin': today_net_margin,
        'today_grams_per_bird': today_grams_per_bird,
        'is_feed_low': is_feed_low,
        'low_feed_threshold': settings.low_feed_threshold_bags,
        # Lists & charts
        'recent_logs': recent_logs,
        'recent_sales': recent_sales,
        'recent_feedings': recent_feedings,
        'chart_labels': json.dumps(chart_labels),
        'chart_crates_produced': json.dumps(chart_crates_produced),
        'chart_broken_eggs': json.dumps(chart_broken_eggs),
        'chart_crates_sold': json.dumps(chart_crates_sold),
    }
    return render(request, 'farm/dashboard.html', context)


# -------------------------------------------------------------
# FEED INVENTORY & DISTRIBUTION VIEWS
# -------------------------------------------------------------

def feed_dashboard(request):
    """Warehouse inventory overview, low-stock warnings, and historical logs."""
    today = timezone.now().date()

    # 1. Storehouse Balances
    purchases_agg = FeedPurchase.objects.aggregate(
        total_bags=Coalesce(Sum('bags_purchased'), Value(0)),
        total_spent=Coalesce(Sum('total_cost'), Value(Decimal('0.00'))),
    )
    distributions_agg = FeedDistribution.objects.aggregate(
        total_bags=Coalesce(Sum('bags_fed'), Value(Decimal('0.00'))),
        total_kg=Coalesce(Sum('total_kg_fed'), Value(Decimal('0.00'))),
        total_fed_cost=Coalesce(Sum('total_cost'), Value(Decimal('0.00'))),
    )

    total_purchased_bags = purchases_agg['total_bags']
    total_spent = purchases_agg['total_spent']
    total_fed_bags = distributions_agg['total_bags']
    total_fed_kg = distributions_agg['total_kg']
    total_fed_cost = distributions_agg['total_fed_cost']

    bags_in_stock = max(Decimal('0.00'), Decimal(total_purchased_bags) - total_fed_bags)
    kg_in_stock = bags_in_stock * Decimal('50.00')

    # 2. Average Daily Burn Rate (last 7 days) to estimate remaining days
    seven_days_ago = today - timedelta(days=6)
    last_week_fed = FeedDistribution.objects.filter(date__gte=seven_days_ago).aggregate(
        total=Coalesce(Sum('bags_fed'), Value(Decimal('0.00')))
    )['total']
    daily_burn_rate = round(float(last_week_fed) / 7.0, 1) if last_week_fed > 0 else 0.0
    days_remaining = int(float(bags_in_stock) / daily_burn_rate) if daily_burn_rate > 0 else 999

    settings = FarmSetting.get_settings()
    is_feed_low = bags_in_stock <= settings.low_feed_threshold_bags

    # 3. Paginated Feed Distribution Ledger
    distributions_qs = FeedDistribution.objects.select_related('flock').order_by('-date')
    paginator = Paginator(distributions_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 4. Recent Deliveries
    recent_purchases = FeedPurchase.objects.all().order_by('-date')[:5]

    context = {
        'bags_in_stock': bags_in_stock,
        'kg_in_stock': kg_in_stock,
        'total_purchased_bags': total_purchased_bags,
        'total_spent': total_spent,
        'total_fed_bags': total_fed_bags,
        'total_fed_cost': total_fed_cost,
        'daily_burn_rate': daily_burn_rate,
        'days_remaining': days_remaining,
        'is_feed_low': is_feed_low,
        'low_threshold': settings.low_feed_threshold_bags,
        'distributions': page_obj,
        'page_obj': page_obj,
        'recent_purchases': recent_purchases,
    }
    return render(request, 'farm/feed_dashboard.html', context)


def feed_distribute_create(request):
    """Stock-Out: Record bags fed to a shed."""
    if request.method == 'POST':
        form = FeedDistributionForm(request.POST)
        if form.is_valid():
            dist = form.save()
            messages.success(request, f"Feeding recorded: {dist.bags_fed} bags fed to {dist.flock.name} ({dist.grams_per_bird} g/bird)!")
            return redirect('feed_dashboard')
    else:
        form = FeedDistributionForm()
    return render(request, 'farm/feed_form.html', {'form': form, 'title': 'Record Shed Feeding (Stock-Out)'})


def feed_purchase_create(request):
    """Stock-In: Record new feed delivery from supplier."""
    if request.method == 'POST':
        form = FeedPurchaseForm(request.POST)
        if form.is_valid():
            purchase = form.save()
            messages.success(request, f"Delivery recorded: {purchase.bags_purchased} bags received from {purchase.supplier_name}!")
            return redirect('feed_dashboard')
    else:
        form = FeedPurchaseForm()
    return render(request, 'farm/feed_purchase_form.html', {'form': form, 'title': 'Receive Feed Delivery (Stock-In)'})


# -------------------------------------------------------------
# CORE APP VIEWS
# -------------------------------------------------------------

def log_list(request):
    logs_qs = DailyLog.objects.select_related('flock').order_by('-date')
    paginator = Paginator(logs_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'farm/log_list.html', {'logs': page_obj, 'page_obj': page_obj})


def log_create(request):
    if request.method == 'POST':
        form = DailyLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(request, f"Daily log for {log.flock.name} on {log.date} ({log.get_collection_round_display()}) recorded successfully!")
            return redirect('log_list')
    else:
        form = DailyLogForm()
    return render(request, 'farm/log_form.html', {'form': form, 'title': 'Record Daily Production'})


def log_edit(request, pk):
    log = get_object_or_404(DailyLog, pk=pk)
    if request.method == 'POST':
        form = DailyLogForm(request.POST, instance=log)
        if form.is_valid():
            form.save()
            messages.success(request, "Daily log updated successfully!")
            return redirect('log_list')
    else:
        form = DailyLogForm(instance=log)
    return render(request, 'farm/log_form.html', {'form': form, 'title': f'Edit Log: {log.flock.name} ({log.date})'})


def sales_list(request):
    sales_qs = EggSale.objects.all().order_by('-date')
    status_filter = request.GET.get('status')
    if status_filter:
        sales_qs = sales_qs.filter(payment_status=status_filter)
    
    totals = sales_qs.aggregate(
        total_sales_amount=Coalesce(Sum('total_amount'), Value(Decimal('0.00'))),
        total_unpaid=Coalesce(
            Sum(
                F('total_amount') - F('amount_paid'),
                filter=Q(payment_status__in=['UNPAID', 'PARTIAL'])
            ),
            Value(Decimal('0.00'))
        )
    )

    paginator = Paginator(sales_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'farm/sales_list.html', {
        'sales': page_obj,
        'page_obj': page_obj,
        'total_sales_amount': totals['total_sales_amount'],
        'total_unpaid': totals['total_unpaid'],
        'current_status': status_filter,
    })


def sales_create(request):
    if request.method == 'POST':
        form = EggSaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            messages.success(request, f"Sale to {sale.customer_name} ({sale.crates_sold} crates @ ${sale.price_per_crate}) recorded!")
            return redirect('sales_list')
    else:
        form = EggSaleForm()
    return render(request, 'farm/sales_form.html', {'form': form, 'title': 'Record Egg Sale'})


def inventory_view(request):
    total_produced = DailyLog.objects.aggregate(
        crates=Coalesce(Sum('crates_collected'), Value(0)),
        loose=Coalesce(Sum('loose_eggs_collected'), Value(0)),
        broken=Coalesce(Sum('broken_eggs'), Value(0)),
    )
    total_crates_collected = total_produced['crates']
    total_loose_collected = total_produced['loose']
    total_broken = total_produced['broken']

    total_sold = EggSale.objects.aggregate(
        crates=Coalesce(Sum('crates_sold'), Value(0)),
        loose=Coalesce(Sum('loose_eggs_sold'), Value(0)),
    )
    total_crates_sold = total_sold['crates']
    total_loose_sold = total_sold['loose']

    crates_in_stock = max(0, total_crates_collected - total_crates_sold)
    loose_in_stock = max(0, total_loose_collected - total_loose_sold)

    total_good_produced = (total_crates_collected * 30) + total_loose_collected
    overall_breakage_pct = round((total_broken / (total_good_produced + total_broken) * 100), 2) if (total_good_produced + total_broken) > 0 else 0.0

    context = {
        'total_crates_collected': total_crates_collected,
        'total_loose_collected': total_loose_collected,
        'total_crates_sold': total_crates_sold,
        'total_loose_sold': total_loose_sold,
        'crates_in_stock': crates_in_stock,
        'loose_in_stock': loose_in_stock,
        'total_broken': total_broken,
        'overall_breakage_pct': overall_breakage_pct,
    }
    return render(request, 'farm/inventory.html', context)


def flock_list(request):
    flocks = Flock.objects.with_mortality().order_by('-is_active', 'name')
    return render(request, 'farm/flock_list.html', {'flocks': flocks})


def flock_create(request):
    if request.method == 'POST':
        form = FlockForm(request.POST)
        if form.is_valid():
            flock = form.save()
            messages.success(request, f"Flock '{flock.name}' created successfully!")
            return redirect('flock_list')
    else:
        form = FlockForm()
    return render(request, 'farm/flock_form.html', {'form': form, 'title': 'Add New Flock / Shed'})


def farm_settings_view(request):
    settings = FarmSetting.get_settings()
    if request.method == 'POST':
        form = FarmSettingForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, "Farm settings updated successfully!")
            return redirect('farm_settings')
    else:
        form = FarmSettingForm(instance=settings)
    return render(request, 'farm/settings.html', {'form': form, 'settings': settings})
