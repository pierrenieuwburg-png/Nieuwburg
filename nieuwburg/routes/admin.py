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
                     SpecializedQuoteRequest, ActivityLog, QuoteLineItem, InvoiceLineItem, Settings)
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

# --- NEW: Catch-all route for the SPA shell ---
# This will serve the base HTML for any admin path the user navigates to.
# React/Vue router will take over on the client-side to render the correct component.
@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
@admin_required
def admin_spa_shell(path):
    # Always render the single admin base/shell template
    return render_template('admin/admin_base.html')

# --- Dashboard & Logs ---
# @bp.route('/') # Now handled by admin_spa_shell
# @admin_required
# def dashboard():
#     today = date.today()
#     new_quotes_count = SpecializedQuoteRequest.query.filter_by(status='New').count()
#     upcoming_cleans_count = Job.query.filter(Job.scheduled_date >= today, Job.status.in_(['Scheduled', 'In-Progress'])).count()
#     active_clients_count = User.query.filter_by(role='client').count()
#     staff_members_count = User.query.filter_by(role='staff').count()
#     # No longer rendering specific template, just the shell
#     return render_template('admin/admin_base.html') # Pass data if needed by shell

# @bp.route('/activity-log') # Now handled by admin_spa_shell
# @admin_required
# def activity_log():
#     # logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all() # Data fetching moves to API
#     return render_template('admin/admin_base.html')

# --- Client Management ---
# @bp.route('/clients') # Now handled by admin_spa_shell
# @admin_required
# def clients():
#     # clients = User.query.filter_by(role='client').order_by(User.id.desc()).all() # Data fetching moves to API
#     return render_template('admin/admin_base.html')

# @bp.route('/clients/add', methods=['GET', 'POST']) # GET handled by shell, POST should move to API if not already there
# @admin_required
# def add_client():
#     # ... logic was mostly for form handling, covered by API now ...
#     return render_template('admin/admin_base.html') # Render shell

# @bp.route('/clients/edit/<int:user_id>', methods=['GET', 'POST']) # GET handled by shell, POST should move to API
# @admin_required
# def edit_client(user_id):
#     # ... logic was mostly for form handling, covered by API now ...
#     return render_template('admin/admin_base.html') # Render shell

# @bp.route('/clients/view/<int:user_id>') # Now handled by admin_spa_shell
# @admin_required
# def view_client(user_id):
#     # client = db.session.get(User, user_id) # Data fetching moves to API
#     return render_template('admin/admin_base.html') # Render shell

@bp.route('/clients/delete/<int:user_id>', methods=['POST']) # KEEP POST action
@admin_required
def delete_client(user_id):
    # This remains as it's an action, not a page view
    client_to_delete = db.session.get(User, user_id)
    if client_to_delete and client_to_delete.role == 'client':
        client_email = client_to_delete.email
        # Consider related data cleanup (quotes, invoices, etc.) or rely on cascade delete
        db.session.delete(client_to_delete)
        log_activity('Client Deleted', f"Admin '{current_user.email}' deleted client: {client_email}")
        db.session.commit()
        flash('Client has been deleted.', 'success')
        # Redirect might not be needed if called via AJAX, return JSON instead
        # return redirect(url_for('admin.clients')) # Original
        return jsonify({'status': 'ok', 'message': 'Client deleted successfully.'})
    else:
        flash('This user is not a client or not found.', 'error')
        # return redirect(url_for('admin.clients')) # Original
        return jsonify({'status': 'error', 'message': 'User not found or is not a client.'}), 404

# --- Staff Management ---
# @bp.route('/staff') # Now handled by admin_spa_shell
# @admin_required
# def staff():
#     # staff_members = User.query.filter_by(role='staff').all() # Data fetching moves to API
#     return render_template('admin/admin_base.html')

# @bp.route('/staff/add', methods=['GET', 'POST']) # GET handled by shell, POST should move to API
# @admin_required
# def add_staff():
#     # ... logic was mostly for form handling, covered by API now ...
#     return render_template('admin/admin_base.html')

# @bp.route('/staff/view/<int:user_id>') # Now handled by admin_spa_shell
# @admin_required
# def view_staff(user_id):
#     # staff_member = db.session.get(User, user_id) # Data fetching moves to API
#     return render_template('admin/admin_base.html')

# @bp.route('/staff/edit/<int:user_id>', methods=['GET', 'POST']) # GET handled by shell, POST should move to API
# @admin_required
# def edit_staff(user_id):
    # ... logic was mostly for form handling, covered by API now ...
#    return render_template('admin/admin_base.html')

@bp.route('/staff/delete/<int:user_id>', methods=['POST']) # KEEP POST action
@admin_required
def delete_staff(user_id):
    # This remains as it's an action
    staff_to_delete = db.session.get(User, user_id)
    if staff_to_delete and staff_to_delete.role == 'staff':
        staff_email = staff_to_delete.email
        # Consider related data cleanup (job assignments?)
        db.session.delete(staff_to_delete)
        log_activity('Staff Deleted', f"Admin '{current_user.email}' deleted staff member: {staff_email}")
        db.session.commit()
        flash('Staff member has been deleted.', 'success')
        # return redirect(url_for('admin.staff')) # Original
        return jsonify({'status': 'ok', 'message': 'Staff member deleted successfully.'})
    else:
        flash('This user is not a staff member or not found.', 'error')
        # return redirect(url_for('admin.staff')) # Original
        return jsonify({'status': 'error', 'message': 'User not found or is not a staff member.'}), 404


@bp.route('/staff/reset-password/<int:user_id>', methods=['POST']) # KEEP POST action
@admin_required
def reset_staff_password(user_id):
    # This remains as it's an action
    staff_member = db.session.get(User, user_id)
    if not staff_member or staff_member.role != 'staff':
        # flash('Staff member not found.', 'error') # Original Flash
        # return redirect(url_for('admin.staff'))   # Original Redirect
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
            # flash(message, 'success') # Original Flash
        except Exception as e:
            message = f"Failed to send reset email. Error: {e}"
            # flash(message, "error") # Original Flash
    else:
        message = "Cannot reset password automatically as the user has no email address."
        # flash(message, "error") # Original Flash

    # return redirect(url_for('admin.view_staff', user_id=user_id)) # Original Redirect
    return jsonify({'status': 'ok' if email_sent else 'warning', 'message': message})


# @bp.route('/applications') # Now handled by admin_spa_shell
# @admin_required
# def admin_applications():
#     # applications = StaffApplication.query.order_by(StaffApplication.submission_date.desc()).all() # Data -> API
#     return render_template('admin/admin_base.html')

# --- Booking & Job Management ---
# @bp.route('/bookings') # Now handled by admin_spa_shell
# @admin_required
# def admin_bookings():
#     # jobs = Job.query.order_by(Job.scheduled_date.desc()).all() # Data -> API
#     return render_template('admin/admin_base.html')

# --- (Other routes for quotes, invoices, blog, services etc. GET routes are handled by shell) ---
# @bp.route('/quotes') # Handled by shell
# @admin_required
# def admin_quotes():
#     return render_template('admin/admin_base.html')

# @bp.route('/quotes/new', methods=['GET', 'POST']) # GET handled by shell, POST potentially API
# @admin_required
# def admin_create_quote():
#     return render_template('admin/admin_base.html')

# @bp.route('/invoices') # Handled by shell
# @admin_required
# def admin_invoices():
#     return render_template('admin/admin_base.html')

# @bp.route('/invoices/new', methods=['GET', 'POST']) # GET handled by shell, POST potentially API
# @admin_required
# def admin_create_invoice():
#     return render_template('admin/admin_base.html')

# @bp.route('/services') # Handled by shell
# @admin_required
# def admin_service_categories():
#     return render_template('admin/admin_base.html')

# @bp.route('/services/category/add', methods=['GET', 'POST']) # GET handled by shell, POST potentially API
# @admin_required
# def admin_add_service_category():
#     return render_template('admin/admin_base.html')

# @bp.route('/blog') # Handled by shell
# @admin_required
# def admin_blog():
#     return render_template('admin/admin_base.html')

# @bp.route('/blog/add', methods=['GET', 'POST']) # GET handled by shell, POST potentially API
# @admin_required
# def admin_add_post():
#     return render_template('admin/admin_base.html')

# --- Keep POST actions for deletion etc., but return JSON ---

@bp.route('/quotes/delete/<int:quote_id>', methods=['POST'])
@admin_required
def delete_quote(quote_id):
    quote = db.session.get(Quote, quote_id)
    if quote:
        # Check permissions if necessary (e.g., only admin can delete?)
        quote_num = quote.quote_number
        db.session.delete(quote)
        db.session.commit()
        log_activity('Quote Deleted', f"Admin '{current_user.email}' deleted quote {quote_num}")
        # flash(f'Quote {quote_num} deleted.', 'success') # Original
        # return redirect(url_for('admin.admin_quotes')) # Original
        return jsonify({'status': 'ok', 'message': f'Quote {quote_num} deleted.'})
    else:
        # flash('Quote not found.', 'error') # Original
        # return redirect(url_for('admin.admin_quotes')) # Original
         return jsonify({'status': 'error', 'message': 'Quote not found.'}), 404

@bp.route('/invoices/delete/<int:invoice_id>', methods=['POST'])
@admin_required
def delete_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if invoice:
        # Check permissions if necessary
        invoice_num = invoice.invoice_number
        db.session.delete(invoice)
        db.session.commit()
        log_activity('Invoice Deleted', f"Admin '{current_user.email}' deleted invoice {invoice_num}")
        # flash(f'Invoice {invoice_num} deleted.', 'success') # Original
        # return redirect(url_for('admin.admin_invoices')) # Original
        return jsonify({'status': 'ok', 'message': f'Invoice {invoice_num} deleted.'})
    else:
        # flash('Invoice not found.', 'error') # Original
        # return redirect(url_for('admin.admin_invoices')) # Original
        return jsonify({'status': 'error', 'message': 'Invoice not found.'}), 404

# --- Routes that were previously rendering edit/view pages are now covered by the shell ---
# @bp.route('/quotes/view/<int:quote_id>')
# @admin_required
# def view_quote(quote_id):
#     return render_template('admin/admin_base.html') # Shell

# @bp.route('/quotes/edit/<int:quote_id>', methods=['GET', 'POST'])
# @admin_required
# def edit_quote(quote_id):
#     return render_template('admin/admin_base.html') # Shell

# @bp.route('/invoices/view/<int:invoice_id>')
# @admin_required
# def view_invoice(invoice_id):
#     return render_template('admin/admin_base.html') # Shell

# @bp.route('/invoices/edit/<int:invoice_id>', methods=['GET', 'POST'])
# @admin_required
# def edit_invoice(invoice_id):
#     return render_template('admin/admin_base.html') # Shell

# --- Any other admin routes rendering specific templates should also be commented out ---
# --- Ensure any necessary POST/PUT/DELETE actions are kept or moved to api.py ---