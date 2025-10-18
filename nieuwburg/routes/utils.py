import json
from datetime import date, timedelta
from flask import current_app
from flask_mail import Message
from threading import Thread

from .. import db, mail
from ..models import ActivityLog, Quote, Invoice, Job, QuoteRequest, InvoiceLineItem, User
from flask_login import current_user

def send_async_email(app, msg):
    """Sends an email in a background thread."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"--- [EMAIL SEND ERROR] --- : {e}")

def log_activity(activity_type, description, user_id=None):
    """Logs an action to the ActivityLog table."""
    if user_id is None and current_user and current_user.is_authenticated:
        user_id = current_user.id
    log = ActivityLog(
        activity_type=activity_type,
        description=description,
        user_id=user_id
    )
    db.session.add(log)
    db.session.commit()

def get_next_quote_number():
    """Generates the next sequential quote number."""
    last_quote = Quote.query.order_by(Quote.id.desc()).first()
    if not last_quote or '-' not in last_quote.quote_number:
        return "QU-0051"
    try:
        last_num = int(last_quote.quote_number.split('-')[1])
        new_num = last_num + 1
        return f"QU-{new_num:04d}"
    except (IndexError, ValueError):
        return "QU-0051"

def get_next_invoice_number():
    """Generates the next sequential invoice number."""
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    if not last_invoice or '-' not in last_invoice.invoice_number:
        return "INV-0061"
    try:
        last_num = int(last_invoice.invoice_number.split('-')[1])
        new_num = last_num + 1
        return f"INV-{new_num:04d}"
    except (IndexError, ValueError):
        return "INV-0061"

def create_invoice_from_job(job):
    """Creates an invoice from a completed job's quote request."""
    if not job.quote_request or not job.quote_request.user:
        print(f"Cannot create invoice for job {job.id}: missing data.")
        return

    if Invoice.query.filter_by(quote_request_id=job.quote_request.id).first():
        print(f"Invoice already exists for quote request {job.quote_request.id}.")
        return

    new_invoice = Invoice(
        invoice_number=get_next_invoice_number(),
        user_id=job.quote_request.user.id,
        invoice_date=date.today(),
        due_date=date.today() + timedelta(days=30),
        subtotal=job.quote_request.total_price,
        total=job.quote_request.total_price,
        quote_request_id=job.quote_request.id
    )
    db.session.add(new_invoice)
    db.session.flush()

    try:
        service_details = json.loads(job.quote_request.service_details)
        description = f"Service: {job.quote_request.primary_service} ({job.quote_request.property_type})\n"
        for service in service_details:
            description += f"- {service.get('name')}"
            if 'quantity' in service and service.get('quantity') not in ['on', 'off']:
                 description += f" (Qty: {service.get('quantity')})"
            description += "\n"
        line_item = InvoiceLineItem(
            invoice_id=new_invoice.id, description=description.strip(),
            quantity=1, unit_price=job.quote_request.total_price,
            amount=job.quote_request.total_price
        )
        db.session.add(line_item)
    except (json.JSONDecodeError, TypeError):
        line_item = InvoiceLineItem(
            invoice_id=new_invoice.id, description=f"Service for {job.quote_request.primary_service}",
            quantity=1, unit_price=job.quote_request.total_price,
            amount=job.quote_request.total_price
        )
        db.session.add(line_item)
    
    log_activity('Invoice Auto-Generated', f"Invoice {new_invoice.invoice_number} for job {job.id}.", user_id=None)
    db.session.commit()
    print(f'Invoice {new_invoice.invoice_number} has been automatically generated.')