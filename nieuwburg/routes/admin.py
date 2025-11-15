import os
import uuid
import json
import secrets
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, jsonify, Response, current_app)
from flask_login import login_required, current_user
from functools import wraps
from datetime import date, datetime
from werkzeug.utils import secure_filename
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.security import generate_password_hash
from io import BytesIO
from xhtml2pdf import pisa
from flask_mail import Message
from threading import Thread

from .. import db
from ..models import (User, Profile, Post, Quote, Invoice, Job, ServiceCategory,
                     ServiceItem, ServicePrice, StaffApplication, QuoteRequest,
                     ActivityLog, QuoteLineItem, InvoiceLineItem, Settings)

from ..forms import (PostForm, EditClientForm, AddClientForm, AddStaffForm, EditStaffForm,
                    GuestQuoteForm, InvoiceForm, JobForm, UpdateJobStatusForm,
                    ServiceCategoryForm, ServiceItemForm, ServicePriceForm)

from .utils import (log_activity, get_next_quote_number, get_next_invoice_number,
                     create_invoice_from_job, send_async_email)
from .auth import generate_confirmation_token


bp = Blueprint('admin', __name__, url_prefix='/admin')

# --- Admin Decorator ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/clients/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_client(user_id):
    client_to_delete = db.session.get(User, user_id)
    if client_to_delete and client_to_delete.role == 'client':
        client_email = client_to_delete.email
        db.session.delete(client_to_delete)
        log_activity('Client Deleted', f"Admin '{current_user.email}' deleted client: {client_email}")
        db.session.commit()
        flash('Client has been deleted.', 'success')
        return jsonify({'status': 'ok', 'message': 'Client deleted successfully.'})
    else:
        flash('This user is not a client or not found.', 'error')
        return jsonify({'status': 'error', 'message': 'User not found or is not a client.'}), 404

@bp.route('/staff/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_staff(user_id):
    staff_to_delete = db.session.get(User, user_id)
    if staff_to_delete and staff_to_delete.role == 'staff':
        staff_email = staff_to_delete.email
        db.session.delete(staff_to_delete)
        log_activity('Staff Deleted', f"Admin '{current_user.email}' deleted staff member: {staff_email}")
        db.session.commit()
        flash('Staff member has been deleted.', 'success')
        return jsonify({'status': 'ok', 'message': 'Staff member deleted successfully.'})
    else:
        flash('This user is not a staff member or not found.', 'error')
        return jsonify({'status': 'error', 'message': 'User not found or is not a staff member.'}), 404


@bp.route('/staff/reset-password/<int:user_id>', methods=['POST']) # KEEP POST action
@admin_required
def reset_staff_password(user_id):
    staff_member = db.session.get(User, user_id)
    if not staff_member or staff_member.role != 'staff':
        return jsonify({'status': 'error', 'message': 'Staff member not found.'}), 404

    staff_member.password_reset_required = True
    db.session.commit()
    message = f"Password reset initiated for {staff_member.email}."
    email_sent = False

    if staff_member.email:
        try:
            token = generate_confirmation_token(staff_member.id)
            activation_url = url_for('auth.staff_activate_token', token=token, _external=True)
            msg = Message(subject="[Nieuwburg Blitz] Your Password Has Been Reset", sender=current_app.config['MAIL_USERNAME'], recipients=[staff_member.email])
            msg.body = f"Hello {staff_member.profile.full_name},\n\nAn administrator has reset your password. Please click the link below to set a new password. This link is valid for 24 hours.\n\n{activation_url}"
            send_async_email(current_app._get_current_object(), msg)
            message = f"A password reset link has been sent to {staff_member.email}."
            email_sent = True
        except Exception as e:
            message = f"Failed to send reset email. Error: {e}"
    else:
        message = "Cannot reset password automatically as the user has no email address."
    return jsonify({'status': 'ok' if email_sent else 'warning', 'message': message})

@bp.route('/quotes/view/<int:quote_id>') # Define a URL for the view page
@admin_required
def view_quote_details(quote_id): # <-- This function name matches the url_for
    """Displays the full details of a single quote request."""
    quote = db.session.get(QuoteRequest, quote_id)

    if not quote:
        flash('Quote request not found.', 'error')
        return redirect(url_for('admin.admin_spa_shell')) # Redirect to admin home

    # We will create this new template in the next step
    return render_template('admin/admin_view_quote.html', quote=quote)

@bp.route('/quotes/delete/<int:quote_id>', methods=['POST'])
@admin_required
def delete_quote(quote_id):
    quote = db.session.get(Quote, quote_id)
    if quote:
        quote_num = quote.quote_number
        db.session.delete(quote)
        db.session.commit()
        log_activity('Quote Deleted', f"Admin '{current_user.email}' deleted quote {quote_num}")
        return jsonify({'status': 'ok', 'message': f'Quote {quote_num} deleted.'})
    else:
         return jsonify({'status': 'error', 'message': 'Quote not found.'}), 404

@bp.route('/invoices/delete/<int:invoice_id>', methods=['POST'])
@admin_required
def delete_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if invoice:
        invoice_num = invoice.invoice_number
        db.session.delete(invoice)
        db.session.commit()
        log_activity('Invoice Deleted', f"Admin '{current_user.email}' deleted invoice {invoice_num}")
        return jsonify({'status': 'ok', 'message': f'Invoice {invoice_num} deleted.'})
    else:
        return jsonify({'status': 'error', 'message': 'Invoice not found.'}), 404
    
@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
@admin_required
def admin_spa_shell(path):
    return render_template('admin/admin_base.html')