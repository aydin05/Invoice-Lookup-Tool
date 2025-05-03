from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    company_name = forms.CharField(max_length=100, required=False)
    phone = forms.CharField(max_length=15, required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'company_name', 'phone', 'password1', 'password2']
        # Note: role is handled directly in the template and view, not in the form

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'company_name', 'phone']
        widgets = {
            'username': forms.TextInput(attrs={'readonly': 'readonly'}),
        }