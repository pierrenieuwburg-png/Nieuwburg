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

# --- Dashboard & Logs ---
@bp.route('/')
@admin_required
def dashboard():
    today = date.today()
    new_quotes_count = SpecializedQuoteRequest.query.filter_by(status='New').count()
    upcoming_cleans_count = Job.query.filter(Job.scheduled_date >= today, Job.status.in_(['Scheduled', 'In-Progress'])).count()
    active_clients_count = User.query.filter_by(role='client').count()
    staff_members_count = User.query.filter_by(role='staff').count()
    return render_template('admin/admin_dashboard.html', 
                           new_quotes_count=new_quotes_count, 
                           upcoming_cleans_count=upcoming_cleans_count, 
                           active_clients_count=active_clients_count, 
                           staff_members_count=staff_members_count)

@bp.route('/activity-log')
@admin_required
def activity_log():
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin/admin_activity_log.html', logs=logs)

# --- Client Management ---
@bp.route('/clients')
@admin_required
def clients():
    clients = User.query.filter_by(role='client').order_by(User.id.desc()).all()
    return render_template('admin/admin_clients.html', clients=clients)

@bp.route('/clients/add', methods=['GET', 'POST'])
@admin_required
def add_client():
    form = AddClientForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('A user with this email already exists.', 'error')
            return redirect(url_for('admin.add_client'))
        
        new_client = User(email=form.email.data, role='client', is_confirmed=True)
        new_client.set_password('password') # Default temporary password
        new_profile = Profile(user=new_client, full_name=form.full_name.data, phone_number=form.phone_number.data, address=form.address.data)
        
        db.session.add(new_client)
        db.session.add(new_profile)
        db.session.commit()
        log_activity('Client Created', f"Admin '{current_user.email}' created a new client: {form.email.data}")
        flash('New client added successfully.', 'success')
        return redirect(url_for('admin.clients'))
        
    return render_template('admin/admin_add_client.html', form=form, title="Add New Client")

@bp.route('/clients/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_client(user_id):
    client = db.session.get(User, user_id)
    if not client or client.role != 'client':
        flash('Client not found.', 'error')
        return redirect(url_for('admin.clients'))
    
    form = EditClientForm(obj=client.profile)
    if form.validate_on_submit():
        client.profile.full_name = form.full_name.data
        client.profile.phone_number = form.phone_number.data
        client.profile.address = form.address.data
        # Note: notes, service_frequency, service_fee might need separate handling if not in EditClientForm
        db.session.commit()
        log_activity('Client Updated', f"Admin '{current_user.email}' updated profile for {client.email}")
        flash('Client profile updated successfully.', 'success')
        return redirect(url_for('admin.view_client', user_id=user_id))
    
    # Pre-populate non-form fields if necessary for display
    return render_template('admin/admin_edit_client.html', form=form, client=client, title=f"Edit Client: {client.profile.full_name or client.email}")

@bp.route('/clients/view/<int:user_id>')
@admin_required
def view_client(user_id):
    client = db.session.get(User, user_id)
    if not client or client.role != 'client':
        flash('Client not found.', 'error')
        return redirect(url_for('admin.clients'))
    return render_template('admin/admin_view_client.html', client=client)

@bp.route('/clients/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_client(user_id):
    client_to_delete = db.session.get(User, user_id)
    if client_to_delete and client_to_delete.role == 'client':
        client_email = client_to_delete.email # Log email before deleting
        db.session.delete(client_to_delete)
        db.session.commit()
        log_activity('Client Deleted', f"Admin '{current_user.email}' deleted client: {client_email}")
        flash('Client has been deleted.', 'success')
    else:
        flash('This user is not a client.', 'error')
    return redirect(url_for('admin.clients'))

# --- Staff Management ---
@bp.route('/staff')
@admin_required
def staff():
    staff_members = User.query.filter_by(role='staff').all()
    staff_with_age = []
    for s in staff_members:
        age = None
        if s.profile and s.profile.date_of_birth:
            today = date.today()
            age = today.year - s.profile.date_of_birth.year - ((today.month, today.day) < (s.profile.date_of_birth.month, s.profile.date_of_birth.day))
        staff_with_age.append({'staff': s, 'age': age})
    return render_template('admin/admin_staff.html', staff_with_age=staff_with_age)

@bp.route('/staff/add', methods=['GET', 'POST'])
@admin_required
def add_staff():
    form = AddStaffForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash('A user with this email already exists.', 'error')
            return redirect(url_for('admin.add_staff'))

        new_staff = User(
            email=form.email.data,
            role='staff',
            password_reset_required=True, # Require password set on first login
            is_confirmed=True # Staff don't need email confirmation
        )
        # Set a temporary secure password (or handle activation differently)
        # temp_password = secrets.token_urlsafe(16) 
        # new_staff.set_password(temp_password) 
        
        new_profile = Profile(user=new_staff, full_name=form.full_name.data, 
            phone_number=form.phone_number.data, address=form.address.data, id_number=form.id_number.data)

        db.session.add(new_staff)
        db.session.add(new_profile)
        db.session.commit()
        log_activity('Staff Created', f"Admin created new staff member: {form.email.data}")
        
        # Send activation email
        try:
            token = generate_confirmation_token(new_staff.id) # Use ID for staff activation
            activation_url = url_for('auth.staff_activate_token', token=token, _external=True)
            msg = Message(subject="[Nieuwburg Blitz] Activate Your Staff Account", sender=current_app.config['MAIL_USERNAME'], recipients=[new_staff.email])
            msg.body = f"Welcome! An account has been created for you. Please click this link to set your password: {activation_url}"
            send_async_email(current_app._get_current_object(), msg)
            flash(f"Staff member '{form.full_name.data}' created. An activation email has been sent.", 'success')
        except Exception as e:
            flash(f"Staff member created, but the activation email could not be sent. Error: {e}", "error")

        return redirect(url_for('admin.staff'))

    return render_template('admin/admin_add_staff.html', form=form, title="Add New Staff Member")

@bp.route('/staff/view/<int:user_id>')
@admin_required
def view_staff(user_id):
    staff_member = db.session.get(User, user_id)
    if not staff_member or staff_member.role != 'staff':
        flash("Staff member not found.", "error")
        return redirect(url_for('admin.staff'))

    age = None
    if staff_member.profile and staff_member.profile.date_of_birth:
        today = date.today()
        age = today.year - staff_member.profile.date_of_birth.year - ((today.month, today.day) < (staff_member.profile.date_of_birth.month, staff_member.profile.date_of_birth.day))
    
    return render_template('admin/admin_view_staff.html', staff_member=staff_member, age=age)

@bp.route('/staff/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_staff(user_id):
    staff_member = db.session.get(User, user_id)
    if not staff_member or staff_member.role != 'staff':
        flash('Staff member not found.', 'error')
        return redirect(url_for('admin.staff'))

    form = EditStaffForm(obj=staff_member.profile)
    if form.validate_on_submit():
        staff_member.profile.full_name = form.full_name.data
        staff_member.profile.phone_number = form.phone_number.data
        staff_member.profile.address = form.address.data
        staff_member.profile.id_number = form.id_number.data
        staff_member.profile.strengths = form.strengths.data
        staff_member.profile.has_id_copy = form.has_id_copy.data
        staff_member.profile.has_drivers_license = form.has_drivers_license.data
        staff_member.profile.has_criminal_check = form.has_criminal_check.data
        
        # Handle file uploads
        if form.upload_documents.data and form.upload_documents.data[0].filename != '':
            if staff_member.profile.documents is None:
                staff_member.profile.documents = []
            for file in form.upload_documents.data:
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                staff_member.profile.documents.append(unique_filename)
            flag_modified(staff_member.profile, "documents") # Important for JSON field

        db.session.commit()
        log_activity('Staff Updated', f"Admin updated profile for {staff_member.email}")
        flash('Staff profile updated successfully.', 'success')
        return redirect(url_for('admin.view_staff', user_id=user_id))
    
    # Pre-populate non-obj fields on GET request
    if request.method == 'GET':
        form.strengths.data = staff_member.profile.strengths
        form.has_id_copy.data = staff_member.profile.has_id_copy
        form.has_drivers_license.data = staff_member.profile.has_drivers_license
        form.has_criminal_check.data = staff_member.profile.has_criminal_check

    return render_template('admin/admin_edit_staff.html', form=form, staff_member=staff_member, title=f"Edit Staff: {staff_member.profile.full_name}")

@bp.route('/staff/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_staff(user_id):
    staff_to_delete = db.session.get(User, user_id)
    if staff_to_delete and staff_to_delete.role == 'staff':
        staff_email = staff_to_delete.email
        db.session.delete(staff_to_delete)
        db.session.commit()
        log_activity('Staff Deleted', f"Admin deleted staff member: {staff_email}")
        flash('Staff member has been deleted.', 'success')
    else:
        flash('This user is not a staff member.', 'error')
    return redirect(url_for('admin.staff'))

@bp.route('/applications')
@admin_required
def admin_applications():
    applications = StaffApplication.query.order_by(StaffApplication.submission_date.desc()).all()
    return render_template('admin/admin_applications.html', applications=applications)

# --- Booking & Job Management ---
@bp.route('/bookings')
@admin_required
def admin_bookings():
    jobs = Job.query.order_by(Job.scheduled_date.desc()).all()
    return render_template('admin/admin_bookings.html', current_jobs=jobs)

# --- Quotes & Invoices ---
@bp.route('/quotes')
@admin_required
def admin_quotes():
    quotes = Quote.query.order_by(Quote.id.desc()).all()
    return render_template('admin/admin_quotes.html', quotes=quotes)

@bp.route('/quotes/new', methods=['GET', 'POST'])
@admin_required
def admin_create_quote():
    form = GuestQuoteForm()
    if form.validate_on_submit():
        new_quote = Quote()
        form.populate_obj(new_quote)
        new_quote.quote_number = get_next_quote_number() # Use helper
        db.session.add(new_quote)
        db.session.commit()
        log_activity('Quote Created', f"Admin '{current_user.email}' created quote {new_quote.quote_number}")
        flash('Quote created.', 'success')
        return redirect(url_for('admin.admin_quotes'))
    return render_template('shared/_form.html', form=form, title="Create New Quote", doc_type="Quote", back_url=url_for('admin.admin_quotes'), submit_text="Save Quote")

@bp.route('/invoices')
@admin_required
def admin_invoices():
    invoices = Invoice.query.order_by(Invoice.id.desc()).all()
    return render_template('admin/admin_invoices.html', invoices=invoices)

@bp.route('/invoices/new', methods=['GET', 'POST'])
@admin_required
def admin_create_invoice():
    form = InvoiceForm()
    if form.validate_on_submit():
        new_invoice = Invoice()
        form.populate_obj(new_invoice)
        new_invoice.invoice_number = get_next_invoice_number() # Use helper
        db.session.add(new_invoice)
        db.session.commit()
        log_activity('Invoice Created', f"Admin '{current_user.email}' created invoice {new_invoice.invoice_number}")
        flash('Invoice created.', 'success')
        return redirect(url_for('admin.admin_invoices'))
    return render_template('shared/_form.html', form=form, title="Create New Invoice", doc_type="Invoice", back_url=url_for('admin.admin_invoices'), submit_text="Save Invoice")
    
# --- Services & Blog ---
@bp.route('/services')
@admin_required
def admin_service_categories():
    categories = ServiceCategory.query.all()
    return render_template('admin/admin_service_categories.html', categories=categories)

@bp.route('/blog')
@admin_required
def admin_blog():
    posts = Post.query.all()
    return render_template('admin/admin_blog.html', posts=posts)

# --- ADDED: Placeholder Routes for Edit/View/Delete Quotes & Invoices ---
@bp.route('/quotes/view/<int:quote_id>')
@admin_required
def view_quote(quote_id):
    quote = db.session.get(Quote, quote_id)
    if not quote:
        flash('Quote not found.', 'error')
        return redirect(url_for('admin.admin_quotes'))
    return render_template('shared/_view.html', document=quote, doc_type='Quote', back_url=url_for('admin.admin_quotes'))

@bp.route('/quotes/edit/<int:quote_id>', methods=['GET', 'POST'])
@admin_required
def edit_quote(quote_id):
    quote = db.session.get(Quote, quote_id)
    if not quote:
        flash('Quote not found.', 'error')
        return redirect(url_for('admin.admin_quotes'))
    form = GuestQuoteForm(obj=quote)
    if form.validate_on_submit():
        form.populate_obj(quote)
        db.session.commit()
        log_activity('Quote Updated', f"Admin '{current_user.email}' updated quote {quote.quote_number}")
        flash('Quote updated successfully.', 'success')
        return redirect(url_for('admin.admin_quotes'))
    return render_template('shared/_form.html', form=form, title=f"Edit Quote {quote.quote_number}", doc_type="Quote", back_url=url_for('admin.admin_quotes'), submit_text="Update Quote", document=quote)

@bp.route('/quotes/delete/<int:quote_id>', methods=['POST'])
@admin_required
def delete_quote(quote_id):
    quote = db.session.get(Quote, quote_id)
    if quote:
        quote_num = quote.quote_number
        db.session.delete(quote)
        db.session.commit()
        log_activity('Quote Deleted', f"Admin '{current_user.email}' deleted quote {quote_num}")
        flash(f'Quote {quote_num} deleted.', 'success')
    return redirect(url_for('admin.admin_quotes'))
    
@bp.route('/invoices/view/<int:invoice_id>')
@admin_required
def view_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        flash('Invoice not found.', 'error')
        return redirect(url_for('admin.admin_invoices'))
    return render_template('shared/_view.html', document=invoice, doc_type='Invoice', back_url=url_for('admin.admin_invoices'))

@bp.route('/invoices/edit/<int:invoice_id>', methods=['GET', 'POST'])
@admin_required
def edit_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        flash('Invoice not found.', 'error')
        return redirect(url_for('admin.admin_invoices'))
    form = InvoiceForm(obj=invoice)
    if form.validate_on_submit():
        form.populate_obj(invoice)
        db.session.commit()
        log_activity('Invoice Updated', f"Admin '{current_user.email}' updated invoice {invoice.invoice_number}")
        flash('Invoice updated successfully.', 'success')
        return redirect(url_for('admin.admin_invoices'))
    return render_template('shared/_form.html', form=form, title=f"Edit Invoice {invoice.invoice_number}", doc_type="Invoice", back_url=url_for('admin.admin_invoices'), submit_text="Update Invoice", document=invoice)

@bp.route('/invoices/delete/<int:invoice_id>', methods=['POST'])
@admin_required
def delete_invoice(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if invoice:
        invoice_num = invoice.invoice_number
        db.session.delete(invoice)
        db.session.commit()
        log_activity('Invoice Deleted', f"Admin '{current_user.email}' deleted invoice {invoice_num}")
        flash(f'Invoice {invoice_num} deleted.', 'success')
    return redirect(url_for('admin.admin_invoices'))