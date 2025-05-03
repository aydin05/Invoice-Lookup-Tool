from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib import messages
from .forms import UserRegistrationForm, UserProfileForm
from django.contrib.auth.decorators import login_required



def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)

            user.role = request.POST.get('role', 'customer')
            user.save()

            if user.role == 'customer':
                from invoices.models import Customer
                Customer.objects.create(
                    name=user.get_full_name() or user.username,
                    email=user.email,
                    phone=user.phone,
                    address="",
                    user=user
                )

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)

    context = {'form': form}

    if request.user.is_carrier():
        from invoices.models import Invoice, Customer
        invoice_count = Invoice.objects.filter(user=request.user).count()
        customer_count = Customer.objects.count()
        context.update({
            'invoice_count': invoice_count,
            'customer_count': customer_count
        })
    else:
        from invoices.models import Invoice, Customer
        try:
            customer = Customer.objects.get(user=request.user)
            invoice_count = Invoice.objects.filter(customer=customer).count()
            context.update({
                'invoice_count': invoice_count
            })
        except Customer.DoesNotExist:
            pass

    return render(request, 'accounts/profile.html', context)