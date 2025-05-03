from django import forms
from .models import Invoice, InvoiceItem, Customer
from django.forms import inlineformset_factory



class CustomerForm(forms.ModelForm):
    email = forms.EmailField(required=True)  # Ensure email is required
    create_account = forms.BooleanField(
        initial=True,
        required=False,
        help_text="Create a user account for this customer"
    )

    class Meta:
        model = Customer
        fields = ['name', 'email', 'phone', 'address', 'create_account']

class InvoiceForm(forms.ModelForm):
    send_email = forms.BooleanField(initial=True, required=False, help_text="Send an email notification to the customer")

    class Meta:
        model = Invoice
        fields = ['invoice_number', 'customer', 'issue_date', 'due_date', 'status', 'notes']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem
        fields = ['description', 'quantity', 'unit_price']

InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    fields=['description', 'quantity', 'unit_price'],
    extra=1,
    can_delete=True
)

InvoiceItemCreateFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    fields=['description', 'quantity', 'unit_price'],
    extra=1,
    can_delete=True
)

InvoiceItemEditFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    fields=['description', 'quantity', 'unit_price'],
    extra=0,
    can_delete=True
)