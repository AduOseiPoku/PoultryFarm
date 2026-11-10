from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, F, Value, Count, Q
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import json

from .models import Flock, DailyLog, EggSale
from .forms import FlockForm, DailyLogForm, EggSaleForm

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
        # Today
        today_crates=Coalesce(Sum('crates_collected', filter=Q(date=today)), Value(0)),
        today_loose=Coalesce(Sum('loose_eggs_collected', filter=Q(date=today)), Value(0)),
        today_broken=Coalesce(Sum('broken_eggs', filter=Q(date=today)), Value(0)),
        today_mortality=Coalesce(Sum('mortality', filter=Q(date=today)), Value(0)),
        # All-time
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
        # Today
        today_crates=Coalesce(Sum('crates_sold', filter=Q(date=today)), Value(0)),
        today_revenue=Coalesce(Sum('total_amount', filter=Q(date=today)), Value(Decimal('0.00'))),
        # All-time
        all_time_crates=Coalesce(Sum('crates_sold'), Value(0)),
        all_time_loose=Coalesce(Sum('loose_eggs_sold'), Value(0)),
    )
    today_crates_sold = sale_stats['today_crates']
    today_revenue = sale_stats['today_revenue']

    # Stock on Hand derived from the consolidated queries (0 extra queries)
    crates_in_stock = max(0, log_stats['all_time_crates'] - sale_stats['all_time_crates'])
    loose_in_stock = max(0, log_stats['all_time_loose'] - sale_stats['all_time_loose'])

    # 4 & 5. 7-Day Trend Chart Queries (2 bulk grouped queries)
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

    # 6 & 7. Recent activity lists (2 queries)
    recent_logs = DailyLog.objects.select_related('flock')[:6]
    recent_sales = EggSale.objects.all()[:6]

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
        'recent_logs': recent_logs,
        'recent_sales': recent_sales,
        'chart_labels': json.dumps(chart_labels),
        'chart_crates_produced': json.dumps(chart_crates_produced),
        'chart_broken_eggs': json.dumps(chart_broken_eggs),
        'chart_crates_sold': json.dumps(chart_crates_sold),
    }
    return render(request, 'farm/dashboard.html', context)


def log_list(request):
    logs_qs = DailyLog.objects.select_related('flock').order_by('-date')
    paginator = Paginator(logs_qs, 20)  # Paginate 20 records per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'farm/log_list.html', {'logs': page_obj, 'page_obj': page_obj})


def log_create(request):
    if request.method == 'POST':
        form = DailyLogForm(request.POST)
        if form.is_valid():
            log = form.save()
            messages.success(request, f"Daily log for {log.flock.name} on {log.date} recorded successfully!")
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
    
    # Combined into a single aggregate query
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

    paginator = Paginator(sales_qs, 20)  # Paginate 20 records per page
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
            messages.success(request, f"Sale to {sale.customer_name} ({sale.crates_sold} crates) recorded!")
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
