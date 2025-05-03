from io import BytesIO
from django.template.loader import get_template
from xhtml2pdf import pisa
import xlwt
from django.http import HttpResponse
from .models import Invoice, Payment
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from datetime import datetime


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


def export_invoices_to_excel(request, invoices):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="invoices_{}.xls"'.format(
        datetime.now().strftime('%Y%m%d%H%M%S')
    )

    # Create workbook and worksheet
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Invoices')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Invoice #', 'Customer', 'Issue Date', 'Due Date', 'Status', 'Total Amount']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    for invoice in invoices:
        row_num += 1
        row = [
            invoice.invoice_number,
            invoice.customer.name,
            invoice.issue_date.strftime('%Y-%m-%d'),
            invoice.due_date.strftime('%Y-%m-%d'),
            invoice.get_status_display(),
            str(invoice.total_amount)
        ]

        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    # Create a second sheet for detailed items
    ws_items = wb.add_sheet('Invoice Items')

    # Sheet header
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Invoice #', 'Description', 'Quantity', 'Unit Price', 'Total']

    for col_num in range(len(columns)):
        ws_items.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body
    font_style = xlwt.XFStyle()

    for invoice in invoices:
        for item in invoice.items.all():
            row_num += 1
            row = [
                invoice.invoice_number,
                item.description,
                str(item.quantity),
                str(item.unit_price),
                str(item.quantity * item.unit_price)
            ]

            for col_num in range(len(row)):
                ws_items.write(row_num, col_num, row[col_num], font_style)

    wb.save(response)
    return response


def send_invoice_email(invoice_id, action="created"):
    print(f"Starting to send email for invoice {invoice_id}, action: {action}")
    """
    Send an email to the customer when an invoice is created or updated
    """
    try:
        invoice = Invoice.objects.get(pk=invoice_id)
        print(f"Found invoice: {invoice.invoice_number}")
        customer_email = invoice.customer.email
        print(f"Customer email: {customer_email}")

        if not customer_email:
            print("No customer email found")
            return False

        # Set the subject and from_email
        subject = f'Invoice #{invoice.invoice_number} {action}'
        from_email = settings.DEFAULT_FROM_EMAIL

        # Load HTML email template
        context = {
            'invoice': invoice,
            'action': action,
            'company_name': invoice.user.company_name or invoice.user.get_full_name() or invoice.user.username,
        }

        html_content = render_to_string('invoices/email_template.html', context)
        text_content = strip_tags(html_content)  # Plain text version of the email

        # Create the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [customer_email]
        )

        email.attach_alternative(html_content, "text/html")

        # Attach PDF invoice
        pdf_file = create_invoice_pdf(invoice)
        email.attach(f'Invoice_{invoice.invoice_number}.pdf', pdf_file, 'application/pdf')

        # Send the email
        email.send()
        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        return False

def create_invoice_pdf(invoice):
    """
    Create a PDF file for the invoice and return the file content
    """
    from io import BytesIO
    from django.template.loader import get_template
    from xhtml2pdf import pisa

    template = get_template('invoices/pdf_template.html')
    html = template.render({'invoice': invoice})

    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    if not pdf.err:
        return result.getvalue()
    return None


def handle_paid_invoice(invoice_id):
    """
    Send notification to customer about payment and delete the invoice
    """
    try:
        invoice = Invoice.objects.get(pk=invoice_id)

        # Only proceed if the invoice is in 'paid' status
        if invoice.status != 'paid':
            return False

        # Send notification email to customer
        customer_email = invoice.customer.email

        # Set the subject and from_email
        subject = f'Payment Confirmation for Invoice #{invoice.invoice_number}'
        from_email = settings.DEFAULT_FROM_EMAIL

        # Load HTML email template
        context = {
            'invoice': invoice,
            'company_name': invoice.user.company_name or invoice.user.get_full_name() or invoice.user.username,
        }

        html_content = render_to_string('invoices/payment_confirmation_email.html', context)
        text_content = strip_tags(html_content)  # Plain text version of the email

        # Create the email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            from_email,
            [customer_email]
        )

        email.attach_alternative(html_content, "text/html")

        # Attach a final copy of the invoice PDF
        pdf_file = create_invoice_pdf(invoice)
        email.attach(f'Invoice_{invoice.invoice_number}_Paid.pdf', pdf_file, 'application/pdf')

        # Send the email
        email.send()

        # Delete the invoice
        invoice.delete()

        return True
    except Exception as e:
        print(f"Error handling paid invoice: {str(e)}")
        return False


def send_welcome_email(email, password):
    """Send welcome email with login credentials"""
    subject = 'Welcome to Invoice Lookup System'
    html_message = render_to_string('invoices/welcome_email.html', {
        'email': email,
        'password': password,
        'login_url': settings.BASE_URL + '/accounts/login/'  # Update with your actual URL
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    send_mail(
        subject,
        plain_message,
        from_email,
        [email],
        html_message=html_message,
        fail_silently=False,
    )



def send_payment_initiated_notification(invoice, email):
    """Send notification to carrier that payment has been initiated"""
    subject = f'Payment Initiated for Invoice #{invoice.invoice_number}'
    html_message = render_to_string('invoices/payment_initiated_email.html', {
        'invoice': invoice,
        'customer': invoice.customer.name,
        'amount': invoice.total_amount,
        'date': datetime.now()
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        send_mail(
            subject,
            plain_message,
            from_email,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending payment initiated notification: {str(e)}")
        return False


def send_payment_confirmation(invoice, email):
    """Send payment confirmation to customer"""
    subject = f'Payment Confirmation for Invoice #{invoice.invoice_number}'
    html_message = render_to_string('invoices/payment_confirmation_email.html', {
        'invoice': invoice,
        'amount': invoice.total_amount,
        'date': datetime.now()
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        # Create email
        message = EmailMultiAlternatives(
            subject,
            plain_message,
            from_email,
            [email]
        )
        message.attach_alternative(html_message, "text/html")

        # Attach PDF if available
        try:
            from .utils import create_invoice_pdf
            pdf_file = create_invoice_pdf(invoice)
            if pdf_file:
                message.attach(f'Receipt_{invoice.invoice_number}.pdf', pdf_file, 'application/pdf')
        except Exception as e:
            print(f"Error attaching PDF: {str(e)}")

        # Send email
        message.send()
        return True
    except Exception as e:
        print(f"Error sending payment confirmation: {str(e)}")
        return False


def send_payment_rejection(invoice, email, reason=""):
    """Send payment rejection notification to customer"""
    subject = f'Payment Not Processed for Invoice #{invoice.invoice_number}'
    html_message = render_to_string('invoices/payment_rejected_email.html', {
        'invoice': invoice,
        'amount': invoice.total_amount,
        'reason': reason,
        'date': datetime.now()
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL

    try:
        send_mail(
            subject,
            plain_message,
            from_email,
            [email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending payment rejection: {str(e)}")
        return False


def clean_up_invoice_payments(invoice_id):
    """
    Check if an invoice has any payment records, and clean them up if needed
    """
    try:
        invoice = Invoice.objects.get(pk=invoice_id)
        # Check if there are any existing payments
        existing_payments = Payment.objects.filter(invoice=invoice)

        if existing_payments.exists():
            # If any payment records exist, delete them unless they're completed
            for payment in existing_payments:
                if payment.status != 'completed':
                    payment.delete()

        # Ensure invoice status is correct
        if invoice.status == 'payment_pending':
            # Reset to default status if there are no active payments
            if not Payment.objects.filter(invoice=invoice, status__in=['pending', 'processing']).exists():
                invoice.status = 'draft'
                invoice.save()

        return True
    except Exception as e:
        print(f"Error cleaning up payments: {str(e)}")
        return False