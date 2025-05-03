# Invoice Lookup System

A comprehensive web application for managing invoices, customers, and payments built with Django. The system supports two types of users: carriers (businesses that create invoices) and customers (who can view and pay their invoices).

## Features

### For Carriers
- **Invoice Management**: Create, edit, view, and delete invoices
- **Customer Management**: Add, edit, and manage customer information
- **Payment Verification**: Verify and process customer payments
- **Dashboard**: Get an overview of invoice status, payments, and recent activities
- **Export Options**: Export invoice data to Excel and PDF formats
- **Batch Operations**: Process multiple payments at once

### For Customers
- **Invoice Access**: View all invoices created for them
- **Payment Processing**: Pay invoices online through the system
- **Batch Payments**: Pay multiple invoices at once
- **Dashboard**: Get an overview of invoice status and payment history
- **PDF Downloads**: Download invoice PDFs for record-keeping

## Screenshots

*Add screenshots of your application here*

## Tech Stack

- **Backend**: Python 3.11, Django 5.1.7
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Database**: PostgreSQL
- **Additional Libraries**:
  - xhtml2pdf (for PDF generation)
  - xlwt (for Excel export)
  - FontAwesome (for icons)
  - Chart.js (for dashboard visualizations)

## Installation

### Prerequisites
- Python 3.11+
- PostgreSQL
- pip

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/invoice_lookup_system.git 
   cd invoice_lookup_system
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the PostgreSQL database:
   ```sql
   CREATE DATABASE invoice_lookup;
   CREATE USER user WITH PASSWORD 'password';
   GRANT ALL PRIVILEGES ON DATABASE invoice_lookup TO user;
   ```

5. Update the database settings in `invoice_lookup_system/settings.py` if needed:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'invoice_lookup',
           'USER': 'user',
           'PASSWORD': 'password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

6. Configure email settings in `settings.py`:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'your-smtp-server.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'your-email@example.com'
   EMAIL_HOST_PASSWORD = 'your-email-password'
   DEFAULT_FROM_EMAIL = 'Your Name <your-email@example.com>'
   ```

7. Run migrations:
   ```bash
   python manage.py migrate
   ```

8. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

9. Run the development server:
   ```bash
   python manage.py runserver
   ```

10. Access the application at http://localhost:8000

## Project Structure

- **accounts**: User authentication and profile management
- **dashboard**: Dashboard views and activity logging
- **invoices**: Core functionality for invoices, customers, and payments
- **templates**: HTML templates
- **static**: CSS, JavaScript, and image files

## Usage Guide

### For Carriers

1. **Creating a Customer**
   - Navigate to Customers > Add Customer
   - Fill in the customer details
   - Optionally create a user account for the customer

2. **Creating an Invoice**
   - Navigate to Invoices > Create Invoice
   - Select a customer (or create a new one)
   - Add invoice items
   - Set due date and status
   - Save the invoice

3. **Verifying Payments**
   - Navigate to Payments
   - Review pending payment verifications
   - Approve or reject each payment

### For Customers

1. **Viewing Invoices**
   - Log in with your customer account
   - View all invoices assigned to you

2. **Paying an Invoice**
   - Click on an invoice to view details
   - Click "Pay Now" to process payment
   - Enter payment information

3. **Batch Payments**
   - Select "Pay Multiple Invoices" option
   - Choose which invoices to pay
   - Process a single payment for all selected invoices
