from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    ACTIVITY_TYPES = (
        ('invoice_created', 'Invoice Created'),
        ('invoice_updated', 'Invoice Updated'),
        ('invoice_deleted', 'Invoice Deleted'),
        ('customer_added', 'Customer Added'),
        ('customer_updated', 'Customer Updated'),
        ('customer_deleted', 'Customer Deleted'),
        ('payment_initiated', 'Payment Initiated'),
        ('payment_approved', 'Payment Approved'),
        ('payment_rejected', 'Payment Rejected'),
        ('status_changed', 'Status Changed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=255)
    related_object_id = models.IntegerField(null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']