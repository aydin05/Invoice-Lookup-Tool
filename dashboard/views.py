from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count

from dashboard.models import ActivityLog
from invoices.models import Invoice, Customer, Payment


@login_required
def dashboard(request):
    if request.user.is_customer():
        try:
            customer = Customer.objects.get(user=request.user)
            invoices = Invoice.objects.filter(customer=customer)
        except Customer.DoesNotExist:
            invoices = Invoice.objects.none()
    else:
        invoices = Invoice.objects.filter(user=request.user)

    total_invoices = invoices.count()
    total_amount = invoices.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    status_counts = invoices.values('status').annotate(count=Count('id'))

    latest_invoices = invoices.order_by('-created_at')[:5]

    if request.user.is_carrier():
        recent_activities = ActivityLog.objects.filter(user=request.user)[:4]
        customer_count = Customer.objects.count()
        pending_payments = Payment.objects.filter(
            invoice__user=request.user,
            status__in=['pending', 'processing']
        ).count()

        context = {
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'status_counts': status_counts,
            'latest_invoices': latest_invoices,
            'customer_count': customer_count,
            'pending_payments': pending_payments,
            'recent_activities': recent_activities,
        }
    else:
        context = {
            'total_invoices': total_invoices,
            'total_amount': total_amount,
            'status_counts': status_counts,
            'latest_invoices': latest_invoices
        }

    return render(request, 'dashboard/dashboard.html', context)
