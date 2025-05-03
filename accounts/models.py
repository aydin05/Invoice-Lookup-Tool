from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    CARRIER = 'carrier'
    CUSTOMER = 'customer'

    ROLE_CHOICES = [
        (CARRIER, 'Carrier'),
        (CUSTOMER, 'Customer'),
    ]

    company_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=CUSTOMER)

    def is_carrier(self):
        return self.role == self.CARRIER

    def is_customer(self):
        return self.role == self.CUSTOMER