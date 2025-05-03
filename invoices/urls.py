from django.urls import path
from . import views

urlpatterns = [
    path('', views.invoice_list, name='invoice_list'),
    path('create/', views.invoice_create, name='invoice_create'),
    path('<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('<int:pk>/delete/', views.invoice_delete, name='invoice_delete'),
    path('customer/create/', views.customer_create, name='customer_create'),
    path('<int:pk>/edit/', views.invoice_edit, name='invoice_edit'),
    path('<int:pk>/pdf/', views.generate_pdf, name='invoice_pdf'),
    path('export/excel/', views.export_excel, name='export_excel'),
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/<int:pk>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:pk>/delete/', views.customer_delete, name='customer_delete'),
    # path('<int:pk>/mark-paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('<int:pk>/pay/', views.initiate_payment, name='initiate_payment'),
    path('payment/<int:payment_id>/status/', views.payment_status, name='payment_status'),
    path('payment-verification/', views.payment_verification_queue, name='payment_verification_queue'),
    path('payment/<int:payment_id>/verify/', views.verify_payment, name='verify_payment'),
    path('batch-payment/', views.batch_payment_selection, name='batch_payment_selection'),
    path('process-batch-payment/', views.process_batch_payment, name='process_batch_payment'),
    path('batch-verify-payments/', views.batch_verify_payments, name='batch_verify_payments'),
]
