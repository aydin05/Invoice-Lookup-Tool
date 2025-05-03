import uuid
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.deletion import ProtectedError
import random
import string
from accounts.models import User

from accounts.decorators import customer_or_carrier_required, carrier_required, customer_required
from dashboard.utils import log_activity
from .models import Invoice, Customer, Payment
from .forms import InvoiceForm, CustomerForm, InvoiceItemFormSet, InvoiceItemCreateFormSet, InvoiceItemEditFormSet
from django.http import HttpResponse
from django.template.loader import get_template
from .utils import render_to_pdf, export_invoices_to_excel, send_invoice_email, handle_paid_invoice, send_welcome_email, \
    send_payment_confirmation, send_payment_rejection, send_payment_initiated_notification, clean_up_invoice_payments


@login_required
@customer_or_carrier_required
def invoice_list(request):
    if request.user.is_customer():
        try:
            customer = Customer.objects.get(user=request.user)
            invoices = Invoice.objects.filter(customer=customer)

            unpaid_count = Invoice.objects.filter(
                customer=customer,
                status__in=['draft', 'sent', 'overdue']
            ).count()
        except Customer.DoesNotExist:
            invoices = Invoice.objects.none()
            unpaid_count = 0
    else:
        invoices = Invoice.objects.filter(user=request.user)
        unpaid_count = 0

    query = request.GET.get('q')
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(status__icontains=query)
        )

    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        invoices = invoices.filter(status=status_filter)

    date_from = request.GET.get('date_from')
    if date_from:
        invoices = invoices.filter(issue_date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        invoices = invoices.filter(issue_date__lte=date_to)

    invoices = invoices.order_by('-created_at')

    page = request.GET.get('page', 1)
    paginator = Paginator(invoices, 10)

    try:
        invoices_page = paginator.page(page)
    except PageNotAnInteger:
        invoices_page = paginator.page(1)
    except EmptyPage:
        invoices_page = paginator.page(paginator.num_pages)

    context = {
        'invoices': invoices_page,
        'has_unpaid_invoices': unpaid_count > 0,
        'unpaid_count': unpaid_count
    }

    return render(request, 'invoices/invoice_list.html', context)

@login_required
@carrier_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceItemCreateFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.save()

            formset.instance = invoice
            formset.save()

            log_activity(
                user=request.user,
                activity_type='invoice_created',
                description=f'Created invoice #{invoice.invoice_number} for {invoice.customer.name}',
                object_id=invoice.id,
                object_type='invoice'
            )


            total = 0
            for item in invoice.items.all():
                total += item.quantity * item.unit_price

            invoice.total_amount = total
            invoice.save()

            try:
                email_sent = send_invoice_email(invoice.id, action="created")
                if email_sent:
                    messages.success(request,
                                     f'Invoice #{invoice.invoice_number} has been created and sent to the customer.')
                else:
                    messages.warning(request,
                                     f'Invoice #{invoice.invoice_number} has been created but email could not be sent.')
            except Exception as e:
                print(f"Email error in create view: {str(e)}")
                messages.warning(request,
                                 f'Invoice #{invoice.invoice_number} has been created but there was an error sending the email.')

            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm()
        formset = InvoiceItemCreateFormSet()

    return render(request, 'invoices/invoice_form.html', {
        'form': form,
        'formset': formset,
    })


@login_required
@carrier_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceItemEditFormSet(request.POST, instance=invoice)

        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.save()

            total = 0
            for item in invoice.items.all():
                total += item.quantity * item.unit_price

            invoice.total_amount = total
            invoice.save()

            log_activity(
                user=request.user,
                activity_type='invoice_updated',
                description=f'Updated invoice #{invoice.invoice_number} for {invoice.customer.name}',
                object_id=invoice.id,
                object_type='invoice'
            )

            send_invoice_email(invoice.id, action="updated")

            messages.success(request, f'Invoice #{invoice.invoice_number} has been updated and sent to the customer.')
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceItemEditFormSet(instance=invoice)

    return render(request, 'invoices/invoice_edit.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice
    })


@login_required
@carrier_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    if request.method == 'POST':
        invoice_number = invoice.invoice_number
        customer_name = invoice.customer.name

        log_activity(
            user=request.user,
            activity_type='invoice_deleted',
            description=f'Deleted invoice #{invoice_number} for {customer_name}',
            object_type='invoice'
        )

        invoice.delete()
        messages.success(request, f'Invoice #{invoice_number} has been deleted.')
        return redirect('invoice_list')

    return render(request, 'invoices/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
@customer_or_carrier_required
def invoice_detail(request, pk):
    if request.user.is_customer():
        try:
            customer = Customer.objects.get(user=request.user)
            invoice = get_object_or_404(Invoice, pk=pk, customer=customer)
        except Customer.DoesNotExist:
            messages.error(request, "You don't have access to this invoice.")
            return redirect('invoice_list')
    else:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})

@login_required
@carrier_required
def customer_create(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)

            email = form.cleaned_data.get('email')
            existing_user = User.objects.filter(email=email).first()

            if existing_user:
                customer.user = existing_user
                if not existing_user.is_customer():
                    existing_user.role = 'customer'
                    existing_user.save()
                    messages.info(request,
                                  f'An existing user with email {email} has been linked to this customer and their role has been updated to Customer.')
                else:
                    messages.info(request, f'An existing user with email {email} has been linked to this customer.')

                customer.save()
            else:
                customer.save()

                if form.cleaned_data.get('create_account'):
                    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

                    user = User.objects.create(
                        username=form.cleaned_data.get('email'),
                        email=form.cleaned_data.get('email'),
                        company_name=customer.name,
                        phone=customer.phone,
                        role='customer'
                    )
                    user.set_password(temp_password)
                    user.save()

                    customer.user = user
                    customer.save()

                    log_activity(
                        user=request.user,
                        activity_type='customer_updated',
                        description=f'Updated customer: {customer.name}',
                        object_id=customer.id,
                        object_type='customer'
                    )

                    send_welcome_email(customer.email, temp_password)

                    messages.success(request,
                                     f'Customer "{customer.name}" has been added and a user account has been created. Login details have been sent to {customer.email}.')
                else:
                    messages.success(request, f'Customer "{customer.name}" has been added.')

            next_url = request.GET.get('next')
            if next_url == 'invoice_create':
                return redirect('invoice_create')
            return redirect('customer_list')
    else:
        form = CustomerForm()

    return render(request, 'invoices/customer_form.html', {
        'form': form,
        'is_edit': False
    })


@login_required
@customer_or_carrier_required
def generate_pdf(request, pk):
    if request.user.is_customer():
        try:
            customer = Customer.objects.get(user=request.user)
            invoice = get_object_or_404(Invoice, pk=pk, customer=customer)
        except Customer.DoesNotExist:
            return HttpResponse("Access denied", status=403)
    else:
        invoice = get_object_or_404(Invoice, pk=pk, user=request.user)

    pdf = render_to_pdf('invoices/pdf_template.html', {'invoice': invoice})

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Invoice_{invoice.invoice_number}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response

    return HttpResponse("Error generating PDF", status=400)


@login_required
@customer_or_carrier_required
def export_excel(request):
    if request.user.is_customer():
        try:
            customer = Customer.objects.get(user=request.user)
            invoices = Invoice.objects.filter(customer=customer)
        except Customer.DoesNotExist:
            invoices = Invoice.objects.none()
    else:
        invoices = Invoice.objects.filter(user=request.user)

    status_filter = request.GET.get('status')
    if status_filter and status_filter != 'all':
        invoices = invoices.filter(status=status_filter)

    date_from = request.GET.get('date_from')
    if date_from:
        invoices = invoices.filter(issue_date__gte=date_from)

    date_to = request.GET.get('date_to')
    if date_to:
        invoices = invoices.filter(issue_date__lte=date_to)

    query = request.GET.get('q')
    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(status__icontains=query)
        )

    return export_invoices_to_excel(request, invoices)


@login_required
@carrier_required
def customer_list(request):
    customers = Customer.objects.all()

    query = request.GET.get('q')
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'invoices/customer_list.html', {'customers': customers})


@login_required
@carrier_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, f'Customer "{customer.name}" has been updated.')
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer)

    return render(request, 'invoices/customer_form.html', {
        'form': form,
        'customer': customer,
        'is_edit': True
    })


@login_required
@carrier_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)

    if request.method == 'POST':
        customer_name = customer.name
        log_activity(
            user=request.user,
            activity_type='customer_deleted',
            description=f'Deleted customer: {customer_name}',
            object_type='customer'
        )
        try:
            customer.delete()
            messages.success(request, f'Customer "{customer_name}" has been deleted.')
        except ProtectedError:
            messages.error(request, f'Cannot delete customer "{customer_name}" because they have associated invoices.')
        return redirect('customer_list')

    return render(request, 'invoices/customer_confirm_delete.html', {'customer': customer})


# @login_required
# @carrier_required
# def mark_invoice_paid(request, pk):
#     invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
#
#     if request.method == 'POST':
#         # Update the invoice status to 'paid'
#         invoice.status = 'paid'
#         invoice.save()
#
#         # Handle the paid invoice (send notification and delete)
#         success = handle_paid_invoice(invoice.id)
#
#         if success:
#             messages.success(request,
#                              f'Invoice #{invoice.invoice_number} has been marked as paid. A confirmation email has been sent to the customer and the invoice has been removed from the system.')
#         else:
#             messages.warning(request,
#                              f'Invoice #{invoice.invoice_number} has been marked as paid, but there was an issue sending the confirmation email or removing the invoice.')
#
#         return redirect('invoice_list')
#
#     return render(request, 'invoices/mark_invoice_paid.html', {
#         'invoice': invoice
#     })


@login_required
@customer_or_carrier_required
def initiate_payment(request, pk):
    if not request.user.is_customer():
        messages.error(request, "Only customers can make payments.")
        return redirect('invoice_list')

    try:
        customer = Customer.objects.get(user=request.user)
        invoice = get_object_or_404(Invoice, pk=pk, customer=customer)
    except Customer.DoesNotExist:
        return HttpResponse("Access denied", status=403)

    if invoice.status == 'paid':
        messages.warning(request, "This invoice has already been paid.")
        return redirect('invoice_detail', pk=invoice.pk)

    if invoice.status == 'payment_pending':
        messages.warning(request, "Payment for this invoice is already in process.")
        return redirect('invoice_detail', pk=invoice.pk)

    clean_up_invoice_payments(invoice.id)

    if request.method == 'POST':

        original_status = invoice.status

        invoice.status = 'payment_pending'
        invoice.save()

        payment = Payment.objects.create(
            invoice=invoice,
            amount=invoice.total_amount,
            status='processing',
            previous_status=original_status,
            transaction_id=f"TRANS-{uuid.uuid4().hex[:8].upper()}"
        )

        log_activity(
            user=request.user,
            activity_type='payment_initiated',
            description=f'Initiated payment for invoice #{invoice.invoice_number}',
            object_id=payment.id,
            object_type='payment'
        )

        send_payment_initiated_notification(invoice, invoice.user.email)

        messages.success(request,
                         "Payment has been initiated. Your invoice will be marked as paid once the payment is verified.")

        return redirect('payment_status', payment_id=payment.id)

    return render(request, 'invoices/payment_form.html', {'invoice': invoice})


@login_required
def payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    invoice = payment.invoice

    if request.user.is_customer():
        try:
            customer = Customer.objects.get(user=request.user)
            if invoice.customer != customer:
                return HttpResponse("Access denied", status=403)
        except Customer.DoesNotExist:
            return HttpResponse("Access denied", status=403)
    elif request.user.is_carrier():
        if invoice.user != request.user:
            return HttpResponse("Access denied", status=403)

    return render(request, 'invoices/payment_status.html', {
        'payment': payment,
        'invoice': invoice
    })


@login_required
@carrier_required
def payment_verification_queue(request):
    payments = Payment.objects.filter(
        invoice__user=request.user,
        status__in=['processing', 'pending']
    ).select_related('invoice', 'invoice__customer').order_by('-payment_date')

    return render(request, 'invoices/payment_verification_queue.html', {
        'payments': payments
    })


@login_required
@carrier_required
def verify_payment(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    invoice = payment.invoice

    if invoice.user != request.user:
        return HttpResponse("Access denied", status=403)

    original_status = invoice.status

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        if action == 'approve':
            payment.status = 'completed'
            payment.verification_notes = notes
            payment.verified_by = request.user
            payment.verified_date = timezone.now()
            payment.save()

            invoice.status = 'paid'
            invoice.save()

            send_payment_confirmation(invoice, invoice.customer.email)

            log_activity(
                user=request.user,
                activity_type='payment_approved',
                description=f'Approved payment for invoice #{invoice.invoice_number}',
                object_id=payment.id,
                object_type='payment'
            )

            messages.success(request,
                             f"Payment for Invoice #{invoice.invoice_number} has been verified and marked as completed.")

        elif action == 'reject':
            invoice_number = invoice.invoice_number
            customer_email = invoice.customer.email

            previous_status = payment.previous_status or 'draft'
            invoice.status = previous_status
            invoice.save()

            rejection_notes = notes

            payment.delete()

            send_payment_rejection(invoice, invoice.customer.email, notes)

            log_activity(
                user=request.user,
                activity_type='payment_rejected',
                description=f'Rejected payment for invoice #{invoice.invoice_number}',
                object_id=payment.id,
                object_type='payment'
            )

            messages.warning(request, f"Payment for Invoice #{invoice.invoice_number} has been rejected.")

        return redirect('payment_verification_queue')

    return render(request, 'invoices/verify_payment.html', {
        'payment': payment,
        'invoice': invoice
    })


@login_required
def batch_payment_selection(request):
    try:
        customer = Customer.objects.get(user=request.user)
        unpaid_invoices = Invoice.objects.filter(
            customer=customer,
            status__in=['draft', 'sent', 'overdue']
        ).order_by('due_date')
    except Customer.DoesNotExist:
        unpaid_invoices = Invoice.objects.none()

    selected_ids = request.GET.getlist('invoice_ids')

    total_amount = 0
    if selected_ids:
        selected_invoices = unpaid_invoices.filter(id__in=selected_ids)
        total_amount = sum(invoice.total_amount for invoice in selected_invoices)

    return render(request, 'invoices/batch_payment_selection.html', {
        'unpaid_invoices': unpaid_invoices,
        'selected_ids': selected_ids,
        'total_amount': total_amount
    })


@login_required
def process_batch_payment(request):
    if request.method != 'POST':
        return redirect('batch_payment_selection')

    invoice_ids = request.POST.getlist('invoice_ids')

    if not invoice_ids:
        messages.error(request, "No invoices were selected for payment.")
        return redirect('batch_payment_selection')

    try:
        customer = Customer.objects.get(user=request.user)
        invoices = Invoice.objects.filter(
            id__in=invoice_ids,
            customer=customer,
            status__in=['draft', 'sent', 'overdue']
        )

        total_amount = sum(invoice.total_amount for invoice in invoices)

        batch_reference = f"BATCH-{uuid.uuid4().hex[:8].upper()}"

        for invoice in invoices:
            original_status = invoice.status

            invoice.status = 'payment_pending'
            invoice.save()

            Payment.objects.create(
                invoice=invoice,
                amount=invoice.total_amount,
                status='processing',
                previous_status=original_status,
                transaction_id=f"{batch_reference}-{invoice.invoice_number}"
            )

            send_payment_initiated_notification(invoice, invoice.user.email)

        messages.success(request,
                         f"Batch payment initiated for {len(invoices)} invoices totaling ${total_amount}. "
                         f"The payments will be marked as paid once verified."
                         )

        return redirect('invoice_list')

    except Customer.DoesNotExist:
        messages.error(request, "Customer profile not found.")
        return redirect('invoice_list')

@login_required
@carrier_required
def batch_verify_payments(request):
    if request.method == 'POST':
        payment_ids = request.POST.getlist('payment_ids')
        action = request.POST.get('action')

        if not payment_ids:
            messages.error(request, "No payments were selected.")
            return redirect('payment_verification_queue')

        payments = Payment.objects.filter(
            id__in=payment_ids,
            invoice__user=request.user,
            status__in=['processing', 'pending']
        )

        count = 0
        for payment in payments:
            invoice = payment.invoice

            if action == 'approve':
                payment.status = 'completed'
                payment.verified_by = request.user
                payment.verified_date = timezone.now()
                payment.save()

                invoice.status = 'paid'
                invoice.save()

                send_payment_confirmation(invoice, invoice.customer.email)

                count += 1

            elif action == 'reject':
                invoice_number = invoice.invoice_number
                customer_email = invoice.customer.email

                previous_status = payment.previous_status or 'draft'
                invoice.status = previous_status
                invoice.save()

                payment.delete()

                send_payment_rejection(invoice, customer_email, "Batch payment rejection")

                count += 1

        if action == 'approve':
            messages.success(request, f"Successfully approved {count} payments.")
        else:
            messages.warning(request, f"Successfully rejected {count} payments.")

        return redirect('payment_verification_queue')

    return redirect('payment_verification_queue')