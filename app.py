import os
from dotenv import load_dotenv
load_dotenv()
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, Form
from wtforms.validators import Length
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import json
import re
import uuid
import requests
import pytz
import secrets
from threading import Thread
from authlib.integrations.flask_client import OAuth
from markupsafe import Markup
from sqlalchemy.types import JSON
from wtforms import SelectField, DateField, FieldList, FormField, FloatField, TimeField, SelectMultipleField, MultipleFileField
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_mail import Mail, Message
from datetime import datetime, date, timedelta, timezone, time # Add timezone here
from wtforms import SelectField, DateField, FieldList, FormField, FloatField
from wtforms.validators import Optional
from flask import Response
from xhtml2pdf import pisa
from io import BytesIO
from flask_session import Session
from werkzeug.datastructures import FileStorage
print("--- Loaded Google Maps API Key:", os.environ.get('GOOGLE_MAPS_API_KEY'), "---")
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField
from flask_wtf.file import FileField, FileAllowed
from itsdangerous import URLSafeTimedSerializer
from flask import session as flask_session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

csrf = CSRFProtect(app)
oauth = OAuth(app)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# --- GOOGLE OAUTH CONFIG ---
CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url=CONF_URL,
    client_kwargs={
        'scope': 'openid email profile'
    }
)

import os

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) # Example: log out after 30 mins of inactivity
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_PASSWORD_SALT'] = 'a-super-secret-salt-change-it'
# --- SESSION CONFIGURATION ---
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_FILE_DIR'] = os.path.join(BASE_DIR, '.flask_session')
Session(app)

# --- UPLOAD CONFIGURATION ---
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- MAIL CONFIGURATION ---
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASSWORD')

mail = Mail(app)
db = SQLAlchemy(app)

def send_async_email(app, msg):
    with app.app_context():
        print("\n--- [EMAIL DEBUG] Attempting to send email in background thread ---")
        print(f"[EMAIL DEBUG] Mail Server Config: {app.config.get('MAIL_SERVER')}")
        print(f"[EMAIL DEBUG] Mail Port Config: {app.config.get('MAIL_PORT')}")
        print(f"[EMAIL DEBUG] Mail Use TLS Config: {app.config.get('MAIL_USE_TLS')}")
        print(f"[EMAIL DEBUG] Mail Username Config: {app.config.get('MAIL_USERNAME')}")
        print(f"[EMAIL DEBUG] Recipient(s): {msg.recipients}")
        try:
            mail.send(msg)
            print("--- [EMAIL DEBUG] SUCCESS: mail.send(msg) was executed. ---")
        except Exception as e:
            print(f"--- [EMAIL DEBUG] CRITICAL ERROR during mail.send(): {e} ---")
            import traceback
            traceback.print_exc()
        print("--- [EMAIL DEBUG] Email sending process finished. ---\n")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Association table for the many-to-many relationship between Jobs and Staff
job_staff_association = db.Table('job_staff_association',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='client')
    
    password_reset_required = db.Column(db.Boolean, default=False)
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_failed_login = db.Column(db.DateTime, nullable=True)

    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    quote_requests = db.relationship('QuoteRequest', backref='user', lazy=True, cascade="all, delete-orphan")
    quotes = db.relationship('Quote', backref='user', lazy=True, cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    profile_image = db.Column(db.String(100), default='avatar_picture_profile_user_icon.png')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    id_number = db.Column(db.String(13))
    date_of_birth = db.Column(db.Date)
    service_frequency = db.Column(db.String(50))
    service_fee = db.Column(db.Float)
    notes = db.Column(db.Text)
    strengths = db.Column(db.Text)
    documents = db.Column(JSON)
    has_id_copy = db.Column(db.Boolean, default=False)
    has_drivers_license = db.Column(db.Boolean, default=False)
    has_criminal_check = db.Column(db.Boolean, default=False)
    bank_name = db.Column(db.String(100))
    branch_code = db.Column(db.String(20))
    account_number = db.Column(db.String(50))
    account_type = db.Column(db.String(50))

class QuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_type = db.Column(db.String(50))
    primary_service = db.Column(db.String(100))
    service_frequency = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_price = db.Column(db.Float)
    service_details = db.Column(db.Text)
    job = db.relationship('Job', back_populates='quote_request', uselist=False)

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(20), unique=True, nullable=False)
    quote_date = db.Column(db.Date, nullable=False, default=date.today)
    expiry_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    discount_value = db.Column(db.Float, default=0.0)
    discount_type = db.Column(db.String(10), default='R')
    total = db.Column(db.Float, default=0.0)
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='Draft')
    acceptance_token = db.Column(db.String(100), unique=True, nullable=True)
    guest_name = db.Column(db.String(100))
    guest_email = db.Column(db.String(100))
    guest_phone = db.Column(db.String(20))
    guest_address = db.Column(db.Text)
    payment_token = db.Column(db.String(100), unique=True, nullable=True)
    deposit_paid = db.Column(db.Boolean, default=False)
    line_items = db.relationship('QuoteLineItem', backref='quote', lazy=True, cascade="all, delete-orphan")


class QuoteLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)

class SpecializedQuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    area = db.Column(db.String(100))
    message = db.Column(db.Text, nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='New') # New, Quoted, Archived

    def __repr__(self):
        return f'<SpecializedQuoteRequest {self.name}>'

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    discount_value = db.Column(db.Float, default=0.0)
    discount_type = db.Column(db.String(10), default='R') # Can be 'R' or '%'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    line_items = db.relationship('InvoiceLineItem', backref='invoice', lazy=True, cascade="all, delete-orphan")

class InvoiceLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    scheduled_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Scheduled')
    notes = db.Column(db.Text, nullable=True)
    quote_request_id = db.Column(db.Integer, db.ForeignKey('quote_request.id'), nullable=True)
    quote_request = db.relationship('QuoteRequest', back_populates='job')
    assigned_staff = db.relationship('User', secondary=job_staff_association, lazy='subquery',
    backref=db.backref('jobs_assigned', lazy=True))

class StaffApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StaffApplication {self.full_name}>'

# --- NEW MODELS FOR BOOKING & PAYMENTS ---
class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    calculation_method = db.Column(db.String(50), nullable=False, default='options')
    items = db.relationship('ServiceItem', backref='category', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ServiceCategory {self.name}>'

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    estimated_time_mins = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    prices = db.relationship('ServicePrice', backref='service_item', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<ServiceItem {self.name}>'
    
class ServicePrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)

    def __repr__(self):
        return f'<ServicePrice {self.frequency} - R{self.price}>'
    
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_email = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    address = db.Column(db.Text, nullable=True)
    booking_date = db.Column(db.Date, nullable=False)
    booking_time = db.Column(db.Time, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    estimated_time_mins = db.Column(db.Integer)
    status = db.Column(db.String(50), default='Pending Payment')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    service_details = db.Column(db.Text)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.String(300), nullable=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('posts', lazy=True))
    is_published = db.Column(db.Boolean, default=False, nullable=False)

    def __repr__(self):
        return f'<Post {self.title}>'
    
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

    def __repr__(self):
        return f'<ActivityLog {self.activity_type}>'
    
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)

def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email

def log_activity(activity_type, description, user_id=None):
    log = ActivityLog(
        activity_type=activity_type,
        description=description,
        user_id=user_id
    )
    db.session.add(log)
    db.session.commit()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_utility_functions():
    return dict(
        get_next_quote_number=get_next_quote_number,
        get_next_invoice_number=get_next_invoice_number
    )

@app.context_processor
def inject_auth_forms():
    login_form = LoginForm()
    register_form = RegistrationForm()
    return dict(login_form=login_form, register_form=register_form)

# --- ADMIN CLIENT MANAGEMENT ---
@app.route('/admin/clients')
@login_required
def admin_clients():
    if current_user.role != 'admin': return redirect(url_for('index'))
    clients = User.query.filter_by(role='client').all()
    return render_template('admin_clients.html', clients=clients)

@app.route('/admin/clients/add', methods=['GET', 'POST'])
@login_required
def admin_add_client():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    form = AddClientForm()
    if form.validate_on_submit():
        email = form.email.data
        if User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'error')
            return redirect(url_for('admin_add_client'))
        
        new_client = User(email=email, role='client')
        new_client.set_password('password') # Sets a default temporary password
        
        new_profile = Profile(
            user=new_client,
            full_name=form.full_name.data,
            phone_number=form.phone_number.data,
            address=form.address.data
        )
        
        db.session.add(new_client)
        db.session.add(new_profile)
        db.session.commit()
        log_activity('Client Created', f"Admin '{current_user.email}' created a new client: {email}", user_id=current_user.id)
        flash('New client added successfully.', 'success')
        return redirect(url_for('admin_clients'))
        
    return render_template('admin_add_client.html', form=form)

@app.route('/admin/clients/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_client(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    client = db.session.get(User, user_id)
    if not client or client.role != 'client':
        flash('Client not found.', 'error')
        return redirect(url_for('admin_clients'))

    form = EditClientForm(obj=client.profile)

    if form.validate_on_submit():
        # Update details from the form
        client.profile.full_name = form.full_name.data
        client.profile.phone_number = form.phone_number.data
        client.profile.address = form.address.data
        client.profile.notes = request.form.get('notes')
        
        # Update details from request.form for fields not in the WTForm
        client.profile.service_frequency = request.form.get('service_frequency')
        service_fee_str = request.form.get('service_fee')
        if service_fee_str and service_fee_str.strip():
            try:
                client.profile.service_fee = float(service_fee_str)
            except ValueError:
                client.profile.service_fee = None
        else:
            client.profile.service_fee = None

        db.session.commit()
        flash('Client profile updated successfully.', 'success')
        return redirect(url_for('admin_view_client', user_id=user_id))

    return render_template('admin_edit_client.html', form=form, client=client)

@app.route('/admin/clients/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_client(user_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    client_to_delete = User.query.get_or_404(user_id)
    if client_to_delete.role == 'client':
        client_email = client_to_delete.email # FIX: Capture email before deleting
        db.session.delete(client_to_delete)
        log_activity('Client Deleted', f"Admin '{current_user.email}' deleted client: {client_email}", user_id=current_user.id)
        db.session.commit()
        flash('Client has been deleted.', 'success')
    else:
        flash('This user is not a client.', 'error')
    return redirect(url_for('admin_clients'))

@app.route('/quote/accept/<int:quote_id>', methods=['POST'])
@login_required
def client_accept_quote(quote_id):
    quote = db.session.get(Quote, quote_id)
    # Security check
    if not quote or quote.user_id != current_user.id:
        flash('Quote not found or permission denied.', 'error')
        return redirect(url_for('client_dashboard'))

    # Change status and generate a unique, sharable payment token
    quote.status = 'Accepted'
    quote.payment_token = str(uuid.uuid4())
    db.session.commit()

    # Create a placeholder job in the admin panel
    new_job = Job(
        quote_request_id=None, # This quote didn't come from an online request
        scheduled_date=date.today(), # Placeholder date
        status='Pending Deposit',
        notes=f"Job created from accepted Quote #{quote.quote_number}. Awaiting 50% deposit."
    )
    # Link the job to the quote's user
    if quote.user:
        new_job.quote_request = QuoteRequest(user_id=quote.user.id, primary_service=f"From Quote {quote.quote_number}")

    db.session.add(new_job)
    db.session.commit()

    log_activity('Quote Accepted', f"Client '{current_user.email}' accepted quote {quote.quote_number}.", user_id=current_user.id)
    flash('Thank you for accepting the quote! A 50% deposit is required to secure your booking.', 'success')
    return redirect(url_for('client_dashboard'))


@app.route('/pay-for-quote/<token>', methods=['GET'])
def pay_for_quote(token):
    quote = Quote.query.filter_by(payment_token=token).first()
    if not quote or quote.status != 'Accepted':
        flash('This payment link is invalid or the quote has not been accepted.', 'error')
        return redirect(url_for('index'))
    
    deposit_amount = quote.total / 2
    paystack_key = os.environ.get('PAYSTACK_PUBLIC_KEY')
    
    return render_template(
        'pay_for_quote.html', 
        quote=quote, 
        deposit_amount=deposit_amount,
        paystack_public_key=paystack_key
    )
    
    deposit_amount = quote.total / 2
    
    paystack_key = os.environ.get('PAYSTACK_PUBLIC_KEY')
    return render_template(
        'pay_for_quote.html', 
        quote=quote, 
        deposit_amount=deposit_amount,
        paystack_public_key=paystack_key
    )

# --- ADMIN STAFF MANAGEMENT ---
@app.route('/admin/staff')
@login_required
def admin_staff():
    if current_user.role != 'admin': return redirect(url_for('index'))
    
    staff_members = User.query.filter_by(role='staff').all()
    staff_with_age = []
    
    for staff in staff_members:
        age = None
        if staff.profile.date_of_birth:
            today = date.today()
            age = today.year - staff.profile.date_of_birth.year - ((today.month, today.day) < (staff.profile.date_of_birth.month, staff.profile.date_of_birth.day))
        staff_with_age.append({'staff': staff, 'age': age})

    return render_template('admin_staff.html', staff_with_age=staff_with_age)

@app.route('/admin/staff/add', methods=['GET', 'POST'])
@login_required
def admin_add_staff():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    form = AddStaffForm()
    if form.validate_on_submit():
        email = form.email.data
        if User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'error')
            return redirect(url_for('admin_add_staff'))

        # Create the staff user, no username or PIN needed
        new_staff = User(
            email=email,
            role='staff',
            password_reset_required=True,
            is_confirmed=True 
        )
        
        # ... (Profile and DOB logic remains the same)
        new_profile = Profile(user=new_staff, full_name=form.full_name.data, 
            phone_number=form.phone_number.data, address=form.address.data, id_number=form.id_number.data)
        # ...

        db.session.add(new_staff)
        db.session.add(new_profile)
        db.session.commit()
        log_activity('Staff Created', f"Admin '{current_user.email}' created new staff member: {email}", user_id=current_user.id)
        
        # --- SEND ACTIVATION EMAIL WITH TOKEN LINK ---
        try:
            token = generate_confirmation_token(new_staff.id) # Token is based on the new User's ID
            activation_url = url_for('staff_activate_token', token=token, _external=True)
            
            msg = Message(
                subject="[Nieuwburg Blitz] Activate Your Staff Account",
                sender=app.config['MAIL_USERNAME'],
                recipients=[email]
            )
            msg.body = f"""
            Welcome to the Nieuwburg Blitz team!

            An account has been created for you. Please click the link below to set your password and activate your account. This link is valid for 24 hours.

            {activation_url}
            """
            mail.send(msg)
            flash(f"Staff member '{form.full_name.data}' created. An activation email has been sent to them.", 'success')
        except Exception as e:
            flash(f"Staff member created, but the activation email could not be sent. Error: {e}", "error")

        return redirect(url_for('admin_staff'))

    return render_template('admin_add_staff.html', form=form)

@app.route('/admin/staff/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_staff(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    staff_member = db.session.get(User, user_id)
    if not staff_member or staff_member.role != 'staff':
        flash('Staff member not found.', 'error')
        return redirect(url_for('admin_staff'))

    form = EditStaffForm(obj=staff_member.profile)

    if form.validate_on_submit():
        # --- SAVE NEW HR & VETTING FIELDS ---
        staff_member.profile.strengths = form.strengths.data
        staff_member.profile.has_id_copy = form.has_id_copy.data
        staff_member.profile.has_drivers_license = form.has_drivers_license.data
        staff_member.profile.has_criminal_check = form.has_criminal_check.data
        
        # Handle document uploads
        if form.upload_documents.data and form.upload_documents.data[0].filename != '':
            if staff_member.profile.documents is None:
                staff_member.profile.documents = []

            for file in form.upload_documents.data:
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                staff_member.profile.documents.append(unique_filename)
            
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(staff_member.profile, "documents")

        staff_member.profile.full_name = form.full_name.data

        db.session.commit()
        flash('Staff profile updated successfully.', 'success')
        return redirect(url_for('admin_view_staff', user_id=user_id))

    form.strengths.data = staff_member.profile.strengths
    form.has_id_copy.data = staff_member.profile.has_id_copy
    form.has_drivers_license.data = staff_member.profile.has_drivers_license
    form.has_criminal_check.data = staff_member.profile.has_criminal_check

    return render_template('admin_edit_staff.html', form=form, staff_member=staff_member)

@app.route('/admin/staff/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_staff(user_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    staff_to_delete = User.query.get_or_404(user_id)
    if staff_to_delete.role == 'staff':
        staff_email = staff_to_delete.email
        db.session.delete(staff_to_delete)
        
        log_activity('Staff Deleted', f"Admin '{current_user.email}' deleted staff member: {staff_email}", user_id=current_user.id)
        
        db.session.commit()
        
        flash('Staff member has been deleted.', 'success')
    else:
        flash('This user is not a staff member.', 'error')
    return redirect(url_for('admin_staff'))

def password_check(form, field):
    password = field.data
    errors = []
    if not re.search('[a-z]', password):
        errors.append('Password must contain at least one lowercase letter.')
    if not re.search('[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter.')
    if not re.search('[0-9]', password):
        errors.append('Password must contain at least one number.')
    if not re.search(r'[!@#$%^&*()_+\=-\[\]{};\':"\\|,.<>\/?]', password):
        errors.append('Password must contain at least one special character.')

    if errors:
        raise ValidationError(Markup('<br>'.join(errors)))
    
@app.route('/admin/staff/reset-password/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_staff_password(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    staff_member = db.session.get(User, user_id)
    if not staff_member or staff_member.role != 'staff':
        flash('Staff member not found.', 'error')
        return redirect(url_for('admin_staff'))

    # Set the user to require a password reset
    staff_member.password_reset_required = True
    db.session.commit()

    # --- Smart Reset Logic ---
    if staff_member.email:
        # Staff has an email: Send them a new activation link
        try:
            token = generate_confirmation_token(staff_member.id)
            activation_url = url_for('staff_activate_token', token=token, _external=True)
            msg = Message(
                subject="[Nieuwburg Blitz] Your Password Has Been Reset",
                sender=app.config['MAIL_USERNAME'],
                recipients=[staff_member.email]
            )
            msg.body = f"""
            Hello {staff_member.profile.full_name},

            An administrator has reset your password. Please click the link below to set a new password for your account. This link is valid for 24 hours.

            {activation_url}
            """
            mail.send(msg)
            flash(f"A password reset link has been sent to {staff_member.email}.", 'success')
        except Exception as e:
            flash(f"Failed to send reset email. Error: {e}", "error")
    else:
        # Staff does not have an email: Generate a new PIN and email it to the admin
        pin = str(secrets.randbelow(1000000)).zfill(6)
        staff_member.temp_pin_hash = generate_password_hash(pin)
        db.session.commit()
        
        try:
            admin_email = app.config['MAIL_USERNAME']
            manual_activation_url = url_for('staff_activate', _external=True)
            msg = Message(
                subject=f"[Nieuwburg Blitz] ACTION REQUIRED: Manual Password Reset for {staff_member.username}",
                sender=admin_email, 
                recipients=[admin_email]
            )
            msg.body = f"""
            The password for {staff_member.profile.full_name} (Username: {staff_member.username}) has been reset.

            Please instruct them to go to the following page to activate their account:
            {manual_activation_url}

            They will need their username and this new One-Time PIN: {pin}
            """
            mail.send(msg)
            flash(f"The staff member does not have an email. A new PIN has been sent to the admin email address.", 'info')
        except Exception as e:
            flash(f"Failed to send admin notification email. Error: {e}", "error")
            
    return redirect(url_for('admin_view_staff', user_id=user_id))

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        password_check
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

class RequestPasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Instructions')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.'),
        password_check
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Reset Password')

class UpdateProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[Length(min=0, max=100)])
    phone_number = StringField('Phone Number', validators=[Length(min=0, max=20)])
    address = TextAreaField('Physical Address', validators=[Length(min=0, max=500)])
    profile_image = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    submit = SubmitField('Save Changes')

class AddStaffForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Physical Address', validators=[Length(max=500)])
    id_number = StringField('South African ID Number', validators=[Length(min=13, max=13)])
    submit = SubmitField('Save Staff Member')

class AddClientForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Physical Address', validators=[Length(max=500)])
    submit = SubmitField('Save Client')

class EditStaffForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Physical Address', validators=[Optional(), Length(max=500)])
    id_number = StringField('South African ID Number', validators=[Optional(), Length(min=13, max=13)])
    strengths = TextAreaField('Strengths / Key Skills', validators=[Optional(), Length(max=1000)])
    
    has_id_copy = BooleanField('Copy of ID on file')
    has_drivers_license = BooleanField("Driver's license on file")
    has_criminal_check = BooleanField('Criminal record check complete')

    upload_documents = MultipleFileField('Upload Supporting Documents (ID, License, etc.)', validators=[
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'png', 'jpeg'], 'Documents or images only!')
    ])
    profile_image = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Update Profile')

class StaffBankingForm(FlaskForm):
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=100)])
    branch_code = StringField('Branch Code', validators=[DataRequired(), Length(max=20)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(max=50)])
    account_type = StringField('Account Type (e.g., Cheque, Savings)', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Save Banking Details')

class EditClientForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Physical Address', validators=[Length(max=500)])
    submit = SubmitField('Update Client')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Full Content', validators=[DataRequired()])
    excerpt = TextAreaField('Excerpt (Short Summary)', validators=[Optional(), Length(max=300)])
    is_published = BooleanField('Publish this post')
    submit = SubmitField('Save Post')
    

class QuoteLineItemForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()], default=1)
    unit_price = FloatField('Unit Price', validators=[DataRequired()])

class GuestQuoteForm(FlaskForm):
    client_or_guest_name = StringField('Client Name', validators=[DataRequired()])
    quote_number = StringField('Quote Number', validators=[Optional()])
    quote_date = DateField('Quote Date', default=date.today, validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    discount_value = FloatField('Discount', validators=[Optional()], default=0.0)
    discount_type = SelectField('Type', choices=[('R', 'R'), ('%', '%')], default='R')
    line_items = FieldList(FormField(QuoteLineItemForm), min_entries=1)
    submit = SubmitField('Save Quote')

class InvoiceLineItemForm(FlaskForm):
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()], default=1)
    unit_price = FloatField('Unit Price', validators=[DataRequired()])

class InvoiceForm(FlaskForm):
    client_or_guest_name = StringField('Client Name', validators=[DataRequired()])
    invoice_number = StringField('Invoice Number', validators=[Optional()])
    invoice_date = DateField('Invoice Date', default=date.today, validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[Optional()])
    discount_value = FloatField('Discount', validators=[Optional()], default=0.0)
    discount_type = SelectField('Type', choices=[('R', 'R'), ('%', '%')], default='R')
    discount = FloatField('Discount (R)', validators=[Optional()], default=0.0) 
    line_items = FieldList(FormField(InvoiceLineItemForm), min_entries=1)
    payment_advice = TextAreaField('Payment Advice', validators=[Optional()])
    submit = SubmitField('Create Invoice')

class JobForm(FlaskForm):
    scheduled_date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    start_time = TimeField('Start Time', validators=[Optional()])
    end_time = TimeField('End Time', validators=[Optional()])
    notes = TextAreaField('Job Notes', validators=[Optional(), Length(max=1000)])
    assigned_staff = SelectMultipleField('Assign Staff', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Job')

class UpdateJobStatusForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('Scheduled', 'Scheduled'),
        ('In-Progress', 'In-Progress'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    submit = SubmitField('Update')

class ChangePasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Set New Password')

class ServiceCategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    calculation_method = SelectField('Pricing Method', choices=[
        ('options', 'User picks from a list of items (e.g., Upholstery)'),
        ('quantity', 'User enters a quantity for an item (e.g., Bedrooms)'),
        ('sqm', 'User enters square meters')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Category')

class ServiceItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired(), Length(max=100)])
    estimated_time_mins = IntegerField('Estimated Time (Minutes)', validators=[Optional()], default=0)
    submit = SubmitField('Save Item')

class ServicePriceForm(FlaskForm):
    frequency = SelectField('Frequency', choices=[
        ('Once-Off', 'Once-Off'),
        ('Weekly', 'Weekly'),
        ('Bi-Weekly', 'Bi-Weekly'),
        ('Monthly', 'Monthly')
    ], validators=[DataRequired()])
    price = FloatField('Price (R)', validators=[DataRequired()])
    submit = SubmitField('Add Price')

def nl2br(value):
    """Converts newlines in a string to HTML line breaks."""
    # Use Markup from the new import
    return Markup(str(value).replace('\n', '<br>'))

app.jinja_env.filters['nl2br'] = nl2br

def to_sast(dt):
    """Converts a UTC datetime object to SAST (Africa/Johannesburg)."""
    if dt is None:
        return ""
    utc = pytz.utc
    sast = pytz.timezone('Africa/Johannesburg')
    return utc.localize(dt).astimezone(sast)

app.jinja_env.filters['to_sast'] = to_sast

# --- AUTHENTICATION & PROFILE ROUTES ---
@app.before_request
def check_password_reset_required():
    # Run this check only for authenticated users who are not on the password change page
    if current_user.is_authenticated and current_user.password_reset_required:
        if request.endpoint not in ['change_password', 'logout', 'static']:
            return redirect(url_for('change_password'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("15 per minute")
def login():
    if current_user.is_authenticated:
        redirect_url = url_for('client_dashboard')
        if current_user.role == 'admin':
            redirect_url = url_for('admin_dashboard')
        elif current_user.role == 'staff':
            redirect_url = url_for('staff_dashboard')
        return redirect(redirect_url)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if user:
            # Check if account is locked
            if user.locked_until and user.locked_until > datetime.utcnow():
                time_remaining = user.locked_until - datetime.utcnow()
                minutes_remaining = (time_remaining.total_seconds() + 59) // 60
                message = f"Account locked. Please try again in {int(minutes_remaining)} minutes."
                if is_ajax:
                    return jsonify({'status': 'locked', 'message': message}), 403
                flash(message, 'error')
                return redirect(url_for('index'))

            if not user.is_confirmed and user.role == 'client':
                message = 'Please confirm your email address before logging in.'
                if is_ajax:
                    return jsonify({'status': 'unconfirmed', 'message': message, 'email': user.email}), 401
                flash(message, 'warning')
                return redirect(url_for('index', action='login_from_redirect'))
            
            if not user.check_password(form.password.data):
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.utcnow()
                if user.failed_login_attempts >= 10:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    user.failed_login_attempts = 0
                    log_activity('Account Locked', f"Account for user '{user.email}' was locked.", user_id=user.id)
                db.session.commit()
                message = 'Please check your login details and try again.'
                if is_ajax:
                    return jsonify({'status': 'error', 'message': message}), 401
                flash(message, 'error')
                return redirect(url_for('index'))

            # --- Successful Login ---
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            
            redirect_url = url_for('client_dashboard')
            if user.role == 'admin':
                redirect_url = url_for('admin_dashboard')
            elif user.role == 'staff':
                redirect_url = url_for('staff_dashboard')
            
            if is_ajax:
                return jsonify({'status': 'ok', 'redirect': redirect_url})
            return redirect(redirect_url)

        # This block runs if the user was not found at all
        message = 'Please check your login details and try again.'
        if is_ajax:
            return jsonify({'status': 'error', 'message': message}), 401
        flash(message, 'error')
        return redirect(url_for('index'))

    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            message = 'An account with this email address already exists.'
            if is_ajax:
                return jsonify({'status': 'error', 'message': message}), 400
            flash(message, 'error')
            return redirect(url_for('register'))

        new_user = User(email=form.email.data, role='client', is_confirmed=False)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.add(Profile(user=new_user))

        token = generate_confirmation_token(new_user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        
        logo_url = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
        
        html = render_template('email/activate.html', confirm_url=confirm_url, logo_url=logo_url)
        
        try:
            msg = Message(subject="[Nieuwburg Blitz] Please confirm your email",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[new_user.email],
                          html=html)
            mail.send(msg)
            db.session.commit()
            message = 'Registration successful! A confirmation email has been sent to your address.'
            if is_ajax:
                 return jsonify({'status': 'ok', 'message': message})
            flash(message, 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            print(f"CRITICAL: Email sending failed during registration: {e}")
            message = 'Could not send confirmation email. Please check the address and try again later.'
            if is_ajax:
                 return jsonify({'status': 'error', 'message': message}), 500
            flash(message, 'error')
            return redirect(url_for('register'))

    if is_ajax and form.errors:
        first_error_field = next(iter(form.errors))
        first_error_message = form.errors[first_error_field][0]
        return jsonify({'status': 'error', 'message': first_error_message}), 400

    return render_template('register.html', form=form)

@app.route('/login/google')
def google_login():
    """Redirects to Google's authentication page."""
    redirect_uri = url_for('authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    """Callback function that Google redirects to after authentication."""
    token = oauth.google.authorize_access_token()
    # The 'userinfo' contains user data like name, email, etc.
    user_info = token.get('userinfo')
    
    if user_info:
        # Check if user already exists in the database
        user = User.query.filter_by(email=user_info['email']).first()
        
        # If user doesn't exist, create a new one
        if not user:
            new_user = User(
                email=user_info['email'],
                role='client',
                is_confirmed=True, # Social logins are confirmed by default
                confirmed_on=datetime.utcnow()
            )
            
            # Create a profile with the name from Google
            new_profile = Profile(
                user=new_user,
                full_name=user_info['name']
            )
            
            db.session.add(new_user)
            db.session.add(new_profile)
            db.session.commit()
            user = new_user

        # Log the user in
        login_user(user)
        flash('You have been successfully logged in with Google.', 'success')
        return redirect(url_for('client_dashboard'))

    flash('Google login failed. Please try again.', 'error')
    return redirect(url_for('index'))

@app.route('/resend-confirmation/<email>')
def resend_confirmation(email):
    user = User.query.filter_by(email=email).first()
    if user and not user.is_confirmed:
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('confirm_email', token=token, _external=True)
        logo_url = "https://i.ibb.co/yY51P6Q/Logo-Black-With-Title.png" # Using public URL for now
        
        html = render_template('email/activate.html', confirm_url=confirm_url, logo_url=logo_url)
        msg = Message(subject="[Nieuwburg Blitz] Please Confirm Your Email (Resent)",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[user.email],
                      html=html)
        mail.send(msg)
        flash('A new confirmation email has been sent to your address.', 'success')
    elif user and user.is_confirmed:
        flash('This account has already been confirmed. Please log in.', 'info')
    else:
        flash('Could not find an account with that email address.', 'error')
        
    return redirect(url_for('index', action='login_from_redirect'))

@app.route('/confirm/<token>')
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.filter_by(email=email).first_or_404()
    
    # Log the user in automatically if they are confirmed
    if user.is_confirmed:
        flash('Account already confirmed. You are now logged in.', 'success')
        login_user(user) # Log the user in
        return redirect(url_for('client_dashboard')) # Redirect to their dashboard
    else:
        user.is_confirmed = True
        user.confirmed_on = datetime.utcnow()
        db.session.commit()
        log_activity('Account Confirmed', f"User '{user.email}' confirmed their account.", user_id=user.id)
        flash('Welcome! Your account has been confirmed and you are now logged in.', 'success')
        login_user(user) # Log the user in
        return redirect(url_for('client_dashboard')) # Redirect to their dashboard

@app.route('/staff/banking', methods=['GET', 'POST'])
@login_required
def staff_banking():
    if current_user.role != 'staff':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    form = StaffBankingForm(obj=current_user.profile)
    
    if form.validate_on_submit():
        # Update profile with form data
        current_user.profile.bank_name = form.bank_name.data
        current_user.profile.branch_code = form.branch_code.data
        current_user.profile.account_number = form.account_number.data
        current_user.profile.account_type = form.account_type.data
        db.session.commit()

        # --- Send Notification Email to Admin ---
        try:
            admin_email = app.config['MAIL_USERNAME']
            msg = Message(
                subject=f"SECURITY ALERT: Banking Details Updated by {current_user.profile.full_name}",
                sender=admin_email,
                recipients=[admin_email]
            )
            msg.body = f"""
            The banking details for a staff member have been updated.

            Staff Member: {current_user.profile.full_name}
            Email: {current_user.email}
            Date of Change: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            Please review this change in the admin panel to ensure it is legitimate.
            """
            mail.send(msg)
        except Exception as e:
            log_activity('Email Error', f"Failed to send banking details update notification for {current_user.email}. Error: {e}")

        flash('Your banking details have been updated successfully.', 'success')
        return redirect(url_for('staff_banking'))

    return render_template('staff_banking.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/staff-activate', methods=['GET', 'POST'])
def staff_activate():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = StaffActivationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, role='staff').first()
        
        # Check if user exists, needs reset, and PIN is correct
        if user and user.password_reset_required and user.temp_pin_hash and check_password_hash(user.temp_pin_hash, form.pin.data):
            # PIN is correct. Store user ID in session to proceed to password creation.
            flask_session['staff_activation_user_id'] = user.id
            flash('PIN verified. Please set your new password.', 'success')
            return redirect(url_for('staff_set_password'))
        else:
            flash('Invalid username or PIN. Please check your details and try again.', 'error')
            
    return render_template('staff_activate.html', form=form)


@app.route('/staff-set-password', methods=['GET', 'POST'])
def staff_set_password():
    if 'staff_activation_user_id' not in flask_session:
        flash('Invalid session. Please start the activation process again.', 'error')
        return redirect(url_for('index'))

    user_id = flask_session['staff_activation_user_id']
    user = db.session.get(User, user_id)
    if not user:
        flash('User not found. Please start over.', 'error')
        return redirect(url_for('index'))

    form = ChangePasswordForm() # We can reuse the existing ChangePasswordForm
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_required = False
        db.session.commit()
        
        # Log the user in automatically
        login_user(user)
        flask_session.pop('staff_activation_user_id', None) # Clean up session
        flash('Your password has been set and you are now logged in.', 'success')
        return redirect(url_for('staff_dashboard'))
        
    return render_template('staff_set_password.html', form=form)

@app.route('/request-password-reset', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def request_password_reset():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_confirmation_token(user.email)
            reset_url = url_for('reset_password', token=token, _external=True)
            logo_url = "https://i.ibb.co/yY51P6Q/Logo-Black-With-Title.png" # Using public URL for now
            
            html = render_template('email/reset_password.html', reset_url=reset_url, logo_url=logo_url)
            msg = Message(subject="[Nieuwburg Blitz] Password Reset Instructions",
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[user.email],
                          html=html)
            mail.send(msg)
        
        flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        return redirect(url_for('index'))
    return render_template('request_password_reset.html', form=form)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        email = confirm_token(token, expiration=3600) # Token is valid for 1 hour
        user = User.query.filter_by(email=email).first_or_404()
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('request_password_reset'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_required = False 
        db.session.commit()

        login_user(user)
        flash('Your password has been updated and you are now logged in!', 'success')
        return redirect(url_for('client_dashboard')) # Redirect to their dashboard
        
    return render_template('reset_password.html', form=form)

@app.route('/create-password/<token>', methods=['GET', 'POST'])
def create_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('client_dashboard'))
    try:
        email = confirm_token(token, expiration=86400) # Link is valid for 24 hours
        user = User.query.filter_by(email=email).first_or_404()
    except:
        flash('The activation link is invalid or has expired. Please request a new one.', 'error')
        return redirect(url_for('request_password_reset'))
    
    if user.is_confirmed:
        flash('This account has already been activated. Please log in.', 'info')
        return redirect(url_for('login'))

    form = ResetPasswordForm() # We can reuse the ResetPasswordForm for this
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.is_confirmed = True
        user.confirmed_on = datetime.utcnow()
        db.session.commit()

        login_user(user)
        flash('Your account has been activated and you are now logged in!', 'success')
        return redirect(url_for('client_dashboard'))
        
    return render_template('create_password.html', form=form)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.password_reset_required:
        return redirect(url_for('index')) # No need to be here

    form = ChangePasswordForm()
    if form.validate_on_submit():
        password = form.password.data
        if len(password) < 8 or not re.search("[a-z]", password) or not re.search("[A-Z]", password) or not re.search("[0-9]", password):
            flash('Password not strong enough. Must contain uppercase, lowercase, and numbers.', 'error')
            return redirect(url_for('change_password'))

        current_user.set_password(form.password.data)
        current_user.password_reset_required = False
        db.session.commit()
        flash('Your password has been updated successfully.', 'success')

        if current_user.role == 'staff':
            return redirect(url_for('staff_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))

    return render_template('change_password.html', form=form)

@app.route('/staff-activate/<token>')
def staff_activate_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    try:
        # Use confirm_token with a 24-hour expiration (86400 seconds)
        user_id = confirm_token(token, expiration=86400)
    except:
        flash('The activation link is invalid or has expired. Please contact an administrator.', 'error')
        return redirect(url_for('index'))

    user = db.session.get(User, user_id)

    # Verify the user is a staff member who needs to set their password
    if user and user.role == 'staff' and user.password_reset_required:
        # Valid token. Store user ID in session to proceed to password creation.
        flask_session['staff_activation_user_id'] = user.id
        flash('Account verified. Please set your new password.', 'success')
        return redirect(url_for('staff_set_password'))
    else:
        flash('The activation link is invalid or has already been used.', 'error')
        return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    user_profile = current_user.profile

    if form.validate_on_submit():
        if form.profile_image.data:
            file = form.profile_image.data
            filename = secure_filename(file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
            user_profile.profile_image = unique_filename

        user_profile.full_name = form.full_name.data
        user_profile.phone_number = form.phone_number.data
        user_profile.address = form.address.data

        db.session.commit()
        flash('Your profile has been updated.', 'success')
        return redirect(url_for('view_profile'))

    elif request.method == 'GET':
        form.full_name.data = user_profile.full_name
        form.phone_number.data = user_profile.phone_number
        form.address.data = user_profile.address

    return render_template('profile.html', form=form, user_profile=user_profile)

@app.route('/remove-picture', methods=['POST'])
@login_required
def remove_profile_picture():
    profile = current_user.profile
    profile.profile_image = 'avatar_picture_profile_user_icon.png'

    db.session.add(profile)
    db.session.commit()

    flash('Your profile picture has been removed.', 'success')
    return redirect(url_for('profile'))

@app.route('/view_profile')
@login_required
def view_profile():
    return render_template('view_profile.html')

@app.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_to_delete = db.session.get(User, current_user.id) 
    
    if user_to_delete:
        user_email = user_to_delete.email
        db.session.delete(user_to_delete)
        db.session.commit()
        log_activity('Account Deleted', f"User '{user_email}' deleted their own account.", user_id=None)
    
    logout_user()
    return jsonify({'status': 'ok', 'message': 'Account deleted successfully.'})

# --- ADMIN ROUTES ---
@app.route('/admin')
@login_required
def admin_redirect():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    today = date.today()
    new_quotes_count = Quote.query.filter_by(status='Draft').count()
    upcoming_cleans_count = Job.query.filter(
        Job.scheduled_date >= today,
        Job.status.in_(['Scheduled', 'In-Progress'])
    ).count()

    active_clients_count = User.query.filter_by(role='client').count()
    staff_members_count = User.query.filter_by(role='staff').count()

    return render_template(
        'admin_dashboard.html',
        new_quotes_count=new_quotes_count,
        upcoming_cleans_count=upcoming_cleans_count,
        active_clients_count=active_clients_count,
        staff_members_count=staff_members_count
    )

@app.route('/admin/activity-log')
@login_required
def admin_activity_log():
    if current_user.role != 'admin':
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))
    
    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin_activity_log.html', logs=logs)

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    # Fetch all data
    requests = QuoteRequest.query.filter_by(status='Pending').order_by(QuoteRequest.request_date.desc()).all()
    jobs = Job.query.order_by(Job.scheduled_date).all()

    # Separate jobs into current and past for the tables
    current_jobs = [j for j in jobs if j.status in ['Scheduled', 'In-Progress']]
    
    # Prepare calendar events with color-coding
    calendar_events = []
    status_colors = {
        'Scheduled': '#007bff',    # Blue
        'In-Progress': '#ffc107', # Yellow
        'Completed': '#28a745',   # Green
        'Cancelled': '#6c757d'    # Grey
    }

    for job in jobs:
        client_name = "N/A"
        if job.quote_request and job.quote_request.user and job.quote_request.user.profile:
            client_name = job.quote_request.user.profile.full_name or job.quote_request.user.email
        
        title = client_name
        
        event = {
            'id': job.id,
            'title': title,
            'start': job.scheduled_date.isoformat(),
            'allDay': not job.start_time,
            'color': status_colors.get(job.status, '#6c757d')
        }
        if job.start_time:
            event['start'] = f"{job.scheduled_date.isoformat()}T{job.start_time.isoformat()}"
        if job.end_time:
            event['end'] = f"{job.scheduled_date.isoformat()}T{job.end_time.isoformat()}"

        calendar_events.append(event)

    events_json = json.dumps(calendar_events)
    status_form = UpdateJobStatusForm()

    return render_template('admin_bookings.html', 
                           requests=requests, 
                           current_jobs=current_jobs,
                           events_json=events_json,
                           status_form=status_form)

@app.route('/admin/schedule_job/<int:request_id>', methods=['POST'])
@login_required
def schedule_job(request_id):
    if current_user.role != 'admin':
        flash('Permission denied.', 'error')
        return redirect(url_for('index'))

    quote_request = db.session.get(QuoteRequest, request_id)
    if not quote_request:
        flash('Quote request not found.', 'error')
        return redirect(url_for('admin_bookings'))

    if quote_request.job:
        flash('This request has already been scheduled.', 'warning')
        return redirect(url_for('admin_bookings'))

    # Create a new job scheduled for today.
    # You can build a form later to make this date dynamic.
    new_job = Job(
        quote_request_id=quote_request.id,
        scheduled_date=date.today(),
        status='Scheduled'
    )

    # Update the request status
    quote_request.status = 'Scheduled'

    db.session.add(new_job)
    db.session.commit()

    flash(f'Job scheduled for {quote_request.user.profile.full_name or quote_request.user.email}.', 'success')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/staff/view/<int:user_id>')
@login_required
def admin_view_staff(user_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    staff_member = User.query.get_or_404(user_id)
    
    age = None
    if staff_member.profile.date_of_birth:
        today = date.today()
        age = today.year - staff_member.profile.date_of_birth.year - ((today.month, today.day) < (staff_member.profile.date_of_birth.month, staff_member.profile.date_of_birth.day))

    return render_template('admin_view_staff.html', staff_member=staff_member, age=age)

@app.route('/admin/applications')
@login_required
def admin_applications():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    applications = StaffApplication.query.order_by(StaffApplication.submission_date.desc()).all()
    return render_template('admin_applications.html', applications=applications)

@app.route('/admin/clients/view/<int:user_id>')
@login_required
def admin_view_client(user_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    client = User.query.get_or_404(user_id)
    return render_template('admin_view_client.html', client=client)

@app.route('/dashboard')
@login_required
def client_dashboard():
    if current_user.role != 'client':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    user_bookings = QuoteRequest.query.filter_by(user_id=current_user.id).order_by(QuoteRequest.request_date.desc()).all()
    user_quotes = Quote.query.filter_by(user_id=current_user.id).order_by(Quote.quote_date.desc()).all()
    user_invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.invoice_date.desc()).all()
    
    return render_template(
        'client_dashboard.html', 
        bookings=user_bookings,
        quotes=user_quotes,
        invoices=user_invoices
    )

@app.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))

    today = date.today()

    # Eagerly load related data to prevent slow database queries
    assigned_jobs = Job.query.options(
        db.joinedload(Job.quote_request).joinedload(QuoteRequest.user).joinedload(User.profile),
        db.joinedload(Job.assigned_staff).joinedload(User.profile)
    ).filter(Job.assigned_staff.any(id=current_user.id)).order_by(Job.scheduled_date, Job.start_time).all()

    upcoming_jobs = [j for j in assigned_jobs if j.scheduled_date >= today]
    past_jobs = [j for j in assigned_jobs if j.scheduled_date < today]

    return render_template('staff_dashboard.html', upcoming_jobs=upcoming_jobs, past_jobs=past_jobs)

def get_next_quote_number():
    last_quote = Quote.query.order_by(Quote.id.desc()).first()
    if not last_quote or '-' not in last_quote.quote_number:
        # If no last quote, or if it has a bad format, start over
        return "QU-0051"
    try:
        last_num = int(last_quote.quote_number.split('-')[1])
        new_num = last_num + 1
        return f"QU-{new_num:04d}"
    except (IndexError, ValueError):
        # Fallback in case of any other parsing error
        return "QU-0051"

@app.route('/admin/blog')
@login_required
def admin_blog():
    if current_user.role != 'admin': return redirect(url_for('index'))
    posts = Post.query.order_by(Post.created_date.desc()).all()
    return render_template('admin_blog.html', posts=posts)

@app.route('/admin/blog/add', methods=['GET', 'POST'])
@login_required
def admin_add_post():
    if current_user.role != 'admin': return redirect(url_for('index'))
    form = PostForm()
    if form.validate_on_submit():
        new_post = Post(
            title=form.title.data,
            content=form.content.data,
            excerpt=form.excerpt.data,
            author_id=current_user.id,
            is_published=form.is_published.data
        )
        db.session.add(new_post)
        db.session.commit()
        log_activity('Blog Post Created', f"Admin '{current_user.email}' created a new blog post: '{new_post.title}'", user_id=current_user.id)
        flash('Blog post has been created.', 'success')
        return redirect(url_for('admin_blog'))
    return render_template('admin_edit_post.html', form=form, title="Create New Post")

@app.route('/admin/blog/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_post(post_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    post = db.session.get(Post, post_id)
    if not post:
        flash('Post not found.', 'error')
        return redirect(url_for('admin_blog'))
    
    form = PostForm(obj=post)
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.excerpt = form.excerpt.data
        post.is_published = form.is_published.data

        log_activity('Blog Post Updated', f"Admin '{current_user.email}' updated the blog post: '{post.title}'", user_id=current_user.id)
        db.session.commit()
        flash('Blog post has been updated.', 'success')
        return redirect(url_for('admin_blog'))
        
    return render_template('admin_edit_post.html', form=form, title=f"Edit: {post.title}")

@app.route('/admin/blog/delete/<int:post_id>', methods=['POST'])
@login_required
def admin_delete_post(post_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    post = db.session.get(Post, post_id)
    if post:
        post_title = post.title
        db.session.delete(post)
        log_activity('Blog Post Deleted', f"Admin '{current_user.email}' deleted the blog post: '{post_title}'", user_id=current_user.id)
        
        db.session.commit()
        flash('Post has been deleted.', 'success')
    return redirect(url_for('admin_blog'))

@app.route('/admin/blog/toggle-status/<int:post_id>', methods=['POST'])
@login_required
def admin_toggle_post_status(post_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Permission denied'}), 403

    post = db.session.get(Post, post_id)
    if not post:
        return jsonify({'status': 'error', 'message': 'Post not found'}), 404

    try:
        data = request.json
        new_status = data.get('is_published')
        if new_status is not None:
            post.is_published = new_status
            db.session.commit()
            log_activity(
                'Blog Status Changed', 
                f"Admin '{current_user.email}' changed status of post '{post.title}' to {'Published' if new_status else 'Draft'}", 
                user_id=current_user.id
            )
            return jsonify({'status': 'ok', 'new_status': post.is_published})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

    return jsonify({'status': 'error', 'message': 'Invalid request'}), 400

@app.route('/admin/quotes')
@login_required
def admin_quotes():
    if current_user.role != 'admin': return redirect(url_for('index'))
    # Fetch both existing quotes and new specialized requests
    quotes = Quote.query.order_by(Quote.quote_date.desc()).all()
    requests = SpecializedQuoteRequest.query.filter_by(status='New').order_by(SpecializedQuoteRequest.request_date.desc()).all()
    return render_template('admin_quotes.html', quotes=quotes, requests=requests)

@app.route('/admin/quotes/new', methods=['GET', 'POST'])
@login_required
def admin_create_quote():
    if current_user.role != 'admin': return redirect(url_for('index'))
    
    form = GuestQuoteForm()
    client_list = User.query.filter_by(role='client').all()
    
    # Pre-population logic
    request_id = request.args.get('request_id', type=int)
    source_request = None
    if request_id:
        source_request = db.session.get(SpecializedQuoteRequest, request_id)
        if source_request and not form.is_submitted():
            form.client_or_guest_name.data = source_request.name
            if form.line_items:
                form.line_items[0].form.description.data = source_request.message

    if form.validate_on_submit():
        number_to_use = form.quote_number.data or get_next_quote_number()
        
        if Quote.query.filter_by(quote_number=number_to_use).first():
            form.quote_number.errors.append(f"Quote number '{number_to_use}' is already in use.")
        else:
            client_name_input = form.client_or_guest_name.data
            user = User.query.join(Profile).filter(Profile.full_name == client_name_input).first()

            quote = Quote(
                quote_number=number_to_use,
                quote_date=form.quote_date.data,
                expiry_date=form.expiry_date.data,
                status='Draft',
                discount_value=form.discount_value.data or 0.0,
                discount_type=form.discount_type.data
            )

            if user:
                quote.user_id = user.id
            else:
                quote.guest_name = client_name_input
                quote.guest_email = source_request.email if source_request else None
                quote.guest_phone = source_request.phone if source_request else None
                quote.acceptance_token = str(uuid.uuid4())

            db.session.add(quote)
            db.session.flush()
            
            subtotal = 0
            for item_data in form.line_items.data:
                item_data.pop('csrf_token', None)
                if item_data['description'] and item_data.get('quantity') is not None and item_data.get('unit_price') is not None:
                    amount = item_data['quantity'] * item_data['unit_price']
                    line_item = QuoteLineItem(quote_id=quote.id, **item_data, amount=amount)
                    db.session.add(line_item)
                    subtotal += amount
            
            quote.subtotal = subtotal
            
            discount_amount = 0
            if quote.discount_type == '%' and quote.discount_value > 0:
                discount_amount = (subtotal * quote.discount_value) / 100
            else:
                discount_amount = quote.discount_value or 0.0
            
            quote.total = subtotal - discount_amount
            
            if source_request:
                source_request.status = 'Quoted'

            log_activity('Quote Created', f"Admin '{current_user.email}' created quote {quote.quote_number}.", user_id=current_user.id)
            db.session.commit()
            flash(f'Draft quote {quote.quote_number} created successfully.', 'success')
            return redirect(url_for('admin_quotes'))

    context = {
        'form': form,
        'title': 'Create New Quote',
        'back_url': url_for('admin_quotes'),
        'doc_type': 'Quote',
        'submit_text': 'Save as Draft',
        'client_list': client_list,
        'document': None
    }
    return render_template('create_quote.html', **context)

@app.route('/admin/quotes/view/<int:quote_id>')
@login_required
def admin_view_quote(quote_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    quote = db.session.get(Quote, quote_id)
    if not quote:
        flash('Quote not found.', 'error')
        return redirect(url_for('admin_quotes'))
    return render_template('view_quote.html', quote=quote)

@app.route('/admin/quotes/edit/<int:quote_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_quote(quote_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    quote = db.session.get(Quote, quote_id)
    if not quote:
        flash('Quote not found.', 'error')
        return redirect(url_for('admin_quotes'))

    form = GuestQuoteForm(obj=quote)
    client_list = User.query.filter_by(role='client').all()

    if form.validate_on_submit():
        new_number = form.quote_number.data
        # Check for duplicates only if the number has changed
        if new_number != quote.quote_number and Quote.query.filter_by(quote_number=new_number).first():
            form.quote_number.errors.append(f"Quote number '{new_number}' is already in use.")
        else:
            client_name_input = form.client_or_guest_name.data
            user = User.query.join(Profile).filter(Profile.full_name == client_name_input).first()

            quote.quote_number = new_number
            quote.quote_date = form.quote_date.data
            quote.expiry_date = form.expiry_date.data
            # ... (rest of the function is the same) ...
            if user:
                quote.user_id = user.id
                quote.guest_name = None
            else:
                quote.user_id = None
                quote.guest_name = client_name_input
            
            QuoteLineItem.query.filter_by(quote_id=quote.id).delete()
            subtotal = 0
            for item_data in form.line_items.data:
                item_data.pop('csrf_token', None)
                if item_data['description'] and item_data['quantity'] is not None and item_data['unit_price'] is not None:
                    amount = item_data['quantity'] * item_data['unit_price']
                    line_item = QuoteLineItem(quote_id=quote.id, **item_data, amount=amount)
                    db.session.add(line_item)
                    subtotal += amount
            
            quote.subtotal = subtotal
            quote.total = subtotal

            db.session.commit()
            log_activity('Quote Updated', f"Admin '{current_user.email}' updated quote {quote.quote_number}.", user_id=current_user.id)
            flash(f'Quote {quote.quote_number} updated successfully.', 'success')
            return redirect(url_for('admin_quotes'))

    if request.method == 'GET':
        form.quote_number.data = quote.quote_number
        if quote.user:
            form.client_or_guest_name.data = quote.user.profile.full_name
        else:
            form.client_or_guest_name.data = quote.guest_name
            
    context = {
        'form': form,
        'title': f'Edit Quote: {quote.quote_number}',
        'back_url': url_for('admin_quotes'),
        'doc_type': 'Quote',
        'submit_text': 'Save Changes',
        'client_list': client_list,
        'document': quote
    }
    return render_template('edit_quote.html', **context)

@app.route('/admin/quotes/delete/<int:quote_id>', methods=['POST'])
@login_required
def admin_delete_quote(quote_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    quote_to_delete = db.session.get(Quote, quote_id)
    if quote_to_delete:
        db.session.delete(quote_to_delete)
        log_activity('Quote Deleted', f"Admin '{current_user.email}' deleted quote {quote_to_delete.quote_number}.", user_id=current_user.id)
        db.session.commit()
        flash(f'Quote {quote_to_delete.quote_number} has been deleted.', 'success')
    else:
        flash('Quote not found.', 'error')
    return redirect(url_for('admin_quotes'))

@app.route('/admin/quotes/download/<int:quote_id>')
@login_required
def admin_download_quote_pdf(quote_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    quote = db.session.get(Quote, quote_id)
    if not quote:
        flash('Quote not found.', 'error')
        return redirect(url_for('admin_quotes'))

    # This line provides the logo path to the template
    logo_path = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
    rendered_template = render_template('quote_pdf_template.html', quote=quote, logo_path=logo_path)
    
    pdf_result = BytesIO()
    pisa_status = pisa.CreatePDF(
        BytesIO(rendered_template.encode('UTF-8')),
        dest=pdf_result
    )

    if pisa_status.err:
        flash('Error generating PDF.', 'error')
        return redirect(url_for('admin_quotes'))

    pdf_result.seek(0)
    
    return Response(pdf_result.getvalue(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=Quote-{quote.quote_number}.pdf'})

def get_next_invoice_number():
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    if not last_invoice or '-' not in last_invoice.invoice_number:
        # If no last invoice, or if it has a bad format, start over
        return "INV-0061"
    try:
        last_num = int(last_invoice.invoice_number.split('-')[1])
        new_num = last_num + 1
        return f"INV-{new_num:04d}"
    except (IndexError, ValueError):
        # Fallback in case of any other parsing error
        return "INV-0061"
    
def create_invoice_from_job(job):
    """
    Automatically creates an invoice from a completed job's quote request.
    """
    if not job.quote_request or not job.quote_request.user:
        print(f"Cannot create invoice for job {job.id}: missing quote request or user.")
        return

    # Check if an invoice for this job's request has already been created
    existing_invoice = Invoice.query.join(QuoteRequest, Invoice.user_id == QuoteRequest.user_id)\
                                    .filter(QuoteRequest.id == job.quote_request.id).first()
    if existing_invoice:
        print(f"Invoice already exists for quote request {job.quote_request.id}.")
        return

    # Create the new invoice
    new_invoice = Invoice(
        invoice_number=get_next_invoice_number(),
        user_id=job.quote_request.user.id,
        invoice_date=date.today(),
        subtotal=job.quote_request.total_price,
        total=job.quote_request.total_price,
        due_date=date.today() + timedelta(days=30) # Example: Due in 30 days
    )
    db.session.add(new_invoice)
    db.session.flush() # Flush to get the new_invoice.id

    # Create line items from the service details stored in the quote request
    try:
        service_details = json.loads(job.quote_request.service_details)
        description = f"Service: {job.quote_request.primary_service} ({job.quote_request.property_type})\n"
        for service in service_details:
            description += f"- {service.get('name')}"
            if 'quantity' in service and service.get('quantity') not in ['on', 'off']:
                 description += f" (Qty: {service.get('quantity')})"
            description += "\n"

        line_item = InvoiceLineItem(
            invoice_id=new_invoice.id,
            description=description.strip(),
            quantity=1,
            unit_price=job.quote_request.total_price,
            amount=job.quote_request.total_price
        )
        db.session.add(line_item)

    except (json.JSONDecodeError, TypeError):
        # Fallback for simple cases or if details are not a valid JSON
        line_item = InvoiceLineItem(
            invoice_id=new_invoice.id,
            description=f"Service for {job.quote_request.primary_service}",
            quantity=1,
            unit_price=job.quote_request.total_price,
            amount=job.quote_request.total_price
        )
        db.session.add(line_item)
    
    log_activity('Invoice Auto-Generated', f"Invoice {new_invoice.invoice_number} created automatically for completed job ID {job.id}.", user_id=current_user.id)
    db.session.commit()
    flash(f'Invoice {new_invoice.invoice_number} has been automatically generated.', 'success')
    
@app.route('/dashboard/download/quote/<int:quote_id>')
@login_required
def client_download_quote_pdf(quote_id):
    quote = db.session.get(Quote, quote_id)
    # SECURITY CHECK: Ensure the quote exists and belongs to the logged-in user
    if not quote or quote.user_id != current_user.id:
        flash('Quote not found or you do not have permission to access it.', 'error')
        return redirect(url_for('client_dashboard'))

    logo_path = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
    rendered_template = render_template('quote_pdf_template.html', quote=quote, logo_path=logo_path)
    
    pdf_result = BytesIO()
    pisa_status = pisa.CreatePDF(BytesIO(rendered_template.encode('UTF-8')), dest=pdf_result)

    if pisa_status.err:
        flash('Error generating PDF.', 'error')
        return redirect(url_for('client_dashboard'))

    pdf_result.seek(0)
    return Response(pdf_result.getvalue(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=Quote-{quote.quote_number}.pdf'})

@app.route('/admin/invoices')
@login_required
def admin_invoices():
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoices = Invoice.query.order_by(Invoice.invoice_date.desc()).all()
    return render_template('admin_invoices.html', invoices=invoices)

@app.route('/admin/invoices/new', methods=['GET', 'POST'])
@login_required
def admin_create_invoice():
    if current_user.role != 'admin': return redirect(url_for('index'))
    
    form = InvoiceForm()
    client_list = User.query.filter_by(role='client').all()

    payment_advice_setting = Settings.query.filter_by(key='payment_advice').first()
    if not payment_advice_setting:
        default_advice = "Please use your Invoice Number as the payment reference.\n\nBank: First National Bank\nAccount Name: Nieuwburg Pty (ltd)\nAccount Number: 63157242222"
        payment_advice_setting = Settings(key='payment_advice', value=default_advice)
        db.session.add(payment_advice_setting)
        db.session.commit()

    if form.validate_on_submit():
        # THIS IS THE FIX: Only update the setting if new, non-empty data was submitted.
        if form.payment_advice.data is not None and form.payment_advice.data != payment_advice_setting.value:
            payment_advice_setting.value = form.payment_advice.data
        
        number_to_use = form.invoice_number.data or get_next_invoice_number()
        if Invoice.query.filter_by(invoice_number=number_to_use).first():
            form.invoice_number.errors.append(f"Invoice number '{number_to_use}' is already in use.")
        else:
            client_name_input = form.client_or_guest_name.data
            user = User.query.join(Profile).filter(Profile.full_name == client_name_input).first()

            if not user:
                form.client_or_guest_name.errors.append(f"Client '{client_name_input}' not found.")
            else:
                invoice = Invoice(
                    invoice_number=number_to_use,
                    user_id=user.id,
                    invoice_date=form.invoice_date.data,
                    due_date=form.due_date.data,
                    discount_value=form.discount_value.data or 0.0,
                    discount_type=form.discount_type.data
                )
                db.session.add(invoice)
                db.session.flush()

                subtotal = 0
                for item_data in form.line_items.data:
                    item_data.pop('csrf_token', None)
                    if item_data['description'] and item_data['quantity'] is not None and item_data['unit_price'] is not None:
                        amount = item_data['quantity'] * item_data['unit_price']
                        db.session.add(InvoiceLineItem(invoice_id=invoice.id, **item_data, amount=amount))
                        subtotal += amount
                
                invoice.subtotal = subtotal
                
                discount_amount = 0
                if invoice.discount_type == '%' and invoice.discount_value > 0:
                    discount_amount = (subtotal * invoice.discount_value) / 100
                else:
                    discount_amount = invoice.discount_value or 0.0
                
                invoice.total = subtotal - discount_amount

                db.session.commit()
                log_activity('Invoice Created', f"Admin '{current_user.email}' created invoice {invoice.invoice_number}.", user_id=current_user.id)
                flash(f'Invoice {invoice.invoice_number} created successfully.', 'success')
                return redirect(url_for('admin_invoices'))
    
    form.payment_advice.data = payment_advice_setting.value

    context = {
        'form': form,
        'title': 'Create New Invoice',
        'back_url': url_for('admin_invoices'),
        'doc_type': 'Invoice',
        'submit_text': 'Create Invoice',
        'client_list': client_list,
        'document': None
    }
    return render_template('create_invoice.html', **context)


@app.route('/admin/invoices/view/<int:invoice_id>')
@login_required
def admin_view_invoice(invoice_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        flash('Invoice not found.', 'error')
        return redirect(url_for('admin_invoices'))
    
    payment_advice = Settings.query.filter_by(key='payment_advice').first()
    
    return render_template('view_invoice.html', invoice=invoice, payment_advice=payment_advice)

@app.route('/admin/invoices/edit/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_invoice(invoice_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        flash('Invoice not found.', 'error')
        return redirect(url_for('admin_invoices'))

    form = InvoiceForm(obj=invoice)
    client_list = User.query.filter_by(role='client').all()
    
    payment_advice_setting = Settings.query.filter_by(key='payment_advice').first()

    if form.validate_on_submit():
        # THIS IS THE FIX: Only update the setting if new, non-empty data was submitted.
        if form.payment_advice.data is not None and form.payment_advice.data != payment_advice_setting.value:
            payment_advice_setting.value = form.payment_advice.data
        
        new_number = form.invoice_number.data
        if new_number != invoice.invoice_number and Invoice.query.filter_by(invoice_number=new_number).first():
            form.invoice_number.errors.append(f"Invoice number '{new_number}' is already in use.")
        else:
            client_name_input = form.client_or_guest_name.data
            user = User.query.join(Profile).filter(Profile.full_name == client_name_input).first()

            if not user:
                form.client_or_guest_name.errors.append(f"Client '{client_name_input}' not found.")
            else:
                invoice.invoice_number = new_number
                invoice.user_id = user.id
                invoice.invoice_date = form.invoice_date.data
                invoice.due_date = form.due_date.data
                invoice.discount_value = form.discount_value.data or 0.0
                invoice.discount_type = form.discount_type.data
                
                InvoiceLineItem.query.filter_by(invoice_id=invoice.id).delete()
                subtotal = 0
                for item_data in form.line_items.data:
                    item_data.pop('csrf_token', None)
                    if item_data['description'] and item_data['quantity'] is not None and item_data['unit_price'] is not None:
                        amount = item_data['quantity'] * item_data['unit_price']
                        db.session.add(InvoiceLineItem(invoice_id=invoice.id, **item_data, amount=amount))
                        subtotal += amount
                
                invoice.subtotal = subtotal

                discount_amount = 0
                if invoice.discount_type == '%' and invoice.discount_value > 0:
                    discount_amount = (subtotal * invoice.discount_value) / 100
                else:
                    discount_amount = invoice.discount_value or 0.0

                invoice.total = subtotal - discount_amount

                db.session.commit()
                log_activity('Invoice Updated', f"Admin '{current_user.email}' updated invoice {invoice.invoice_number}.", user_id=current_user.id)
                flash(f'Invoice {invoice.invoice_number} updated successfully.', 'success')
                return redirect(url_for('admin_invoices'))

    if request.method == 'GET':
        form.invoice_number.data = invoice.invoice_number
        form.client_or_guest_name.data = invoice.user.profile.full_name
        form.discount_value.data = invoice.discount_value or 0.0
        form.discount_type.data = invoice.discount_type
        form.payment_advice.data = payment_advice_setting.value

    context = {
        'form': form,
        'title': f'Edit Invoice: {invoice.invoice_number}',
        'back_url': url_for('admin_invoices'),
        'doc_type': 'Invoice',
        'submit_text': 'Save Changes',
        'client_list': client_list,
        'document': invoice
    }
    return render_template('edit_invoice.html', **context)

@app.route('/admin/invoices/delete/<int:invoice_id>', methods=['POST'])
@login_required
def admin_delete_invoice(invoice_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoice_to_delete = db.session.get(Invoice, invoice_id)
    if invoice_to_delete:
        invoice_number_for_log = invoice_to_delete.invoice_number 
        db.session.delete(invoice_to_delete)
        db.session.commit()

        log_activity('Invoice Deleted', f"Admin '{current_user.email}' deleted invoice {invoice_number_for_log}.", user_id=current_user.id)
        
        flash(f'Invoice {invoice_number_for_log} has been deleted.', 'success')
    else:
        flash('Invoice not found.', 'error')
    return redirect(url_for('admin_invoices'))

@app.route('/admin/invoices/download/<int:invoice_id>')
@login_required
def admin_download_invoice_pdf(invoice_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        flash('Invoice not found.', 'error')
        return redirect(url_for('admin_invoices'))

    logo_path = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
    
    payment_advice = Settings.query.filter_by(key='payment_advice').first()

    rendered_template = render_template('invoice_pdf_template.html', invoice=invoice, logo_path=logo_path, payment_advice=payment_advice)
    
    pdf_result = BytesIO()
    pisa.CreatePDF(BytesIO(rendered_template.encode('UTF-8')), dest=pdf_result)
    pdf_result.seek(0)
    
    return Response(pdf_result.getvalue(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=Invoice-{invoice.invoice_number}.pdf'})

@app.route('/dashboard/download/invoice/<int:invoice_id>')
@login_required
def client_download_invoice_pdf(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    # SECURITY CHECK: Ensure the invoice exists and belongs to the logged-in user
    if not invoice or invoice.user_id != current_user.id:
        flash('Invoice not found or you do not have permission to access it.', 'error')
        return redirect(url_for('client_dashboard'))

    logo_path = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
    payment_advice = Settings.query.filter_by(key='payment_advice').first()
    rendered_template = render_template('invoice_pdf_template.html', invoice=invoice, logo_path=logo_path, payment_advice=payment_advice)
    
    pdf_result = BytesIO()
    pisa.CreatePDF(BytesIO(rendered_template.encode('UTF-8')), dest=pdf_result)
    pdf_result.seek(0)
    
    return Response(pdf_result.getvalue(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=Invoice-{invoice.invoice_number}.pdf'})

@app.route('/admin/job/new/<int:request_id>', methods=['GET', 'POST'])
@login_required
def admin_create_job_from_request(request_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    
    quote_request = db.session.get(QuoteRequest, request_id)
    if not quote_request:
        flash('Quote request not found.', 'error')
        return redirect(url_for('admin_bookings'))

    form = JobForm()
    # Populate staff choices
    form.assigned_staff.choices = [(s.id, s.profile.full_name) for s in User.query.filter_by(role='staff').all()]

    if form.validate_on_submit():
        new_job = Job(
            quote_request_id=request_id,
            scheduled_date=form.scheduled_date.data,
            start_time=form.start_time.data,
            end_time=form.end_time.data,
            notes=form.notes.data,
            status='Scheduled'
        )
        
        # Add assigned staff
        for staff_id in form.assigned_staff.data:
            staff_member = db.session.get(User, staff_id)
            if staff_member:
                new_job.assigned_staff.append(staff_member)

        quote_request.status = 'Scheduled'
        db.session.add(new_job)
        db.session.commit()
        log_activity('Job Created', f"Admin '{current_user.email}' scheduled a new job for request ID {request_id}.", user_id=current_user.id)
        flash('Job has been scheduled successfully.', 'success')
        return redirect(url_for('admin_bookings'))
    
    # Pre-populate the date field for convenience
    form.scheduled_date.data = date.today()

    return render_template('admin_edit_job.html', form=form, quote_request=quote_request, title="Schedule New Job")


@app.route('/admin/job/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_job(job_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    
    job = db.session.get(Job, job_id)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('admin_bookings'))

    form = JobForm(obj=job)
    form.assigned_staff.choices = [(s.id, s.profile.full_name) for s in User.query.filter_by(role='staff').all()]
    
    if form.validate_on_submit():
        job.scheduled_date = form.scheduled_date.data
        job.start_time = form.start_time.data
        job.end_time = form.end_time.data
        job.notes = form.notes.data

        # Update staff assignments
        job.assigned_staff.clear()
        for staff_id in form.assigned_staff.data:
            staff_member = db.session.get(User, staff_id)
            if staff_member:
                job.assigned_staff.append(staff_member)
        
        log_activity('Job Updated', f"Admin '{current_user.email}' updated job ID {job_id}.", user_id=current_user.id)
        db.session.commit()
        flash('Job details updated.', 'success')
        return redirect(url_for('admin_bookings'))

    # Pre-populate assigned staff list on GET request
    form.assigned_staff.data = [s.id for s in job.assigned_staff]

    return render_template('admin_edit_job.html', form=form, quote_request=job.quote_request, title=f"Edit Job for {job.quote_request.user.profile.full_name}")

@app.route('/admin/job/update_status/<int:job_id>', methods=['POST'])
@login_required
def admin_update_job_status(job_id):
    if current_user.role != 'admin':
        return jsonify({'status': 'error', 'message': 'Permission denied'}), 403

    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({'status': 'error', 'message': 'Job not found'}), 404

    data = request.json
    new_status = data.get('status')

    if new_status in ['Scheduled', 'In-Progress', 'Completed', 'Cancelled']:
        job.status = new_status
        
        if job.quote_request:
            job.quote_request.status = new_status

        # --- THIS IS THE NEW LOGIC ---
        # If the job is completed, automatically generate an invoice
        if new_status == 'Completed':
            create_invoice_from_job(job)
        # --- END OF NEW LOGIC ---

        log_activity('Job Status Updated', f"Admin '{current_user.email}' updated status for job ID {job_id} to '{new_status}'.", user_id=current_user.id)
        db.session.commit()
        return jsonify({'status': 'ok', 'message': f'Job status updated to {new_status}', 'new_status': new_status})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid status provided'}), 400
    
# --- ADMIN SERVICE & PRICING MANAGEMENT ---

@app.route('/admin/service-categories')
@login_required
def admin_service_categories():
    if current_user.role != 'admin': return redirect(url_for('index'))
    categories = ServiceCategory.query.order_by(ServiceCategory.name).all()
    return render_template('admin_service_categories.html', categories=categories)

@app.route('/admin/service-categories/add', methods=['GET', 'POST'])
@login_required
def admin_add_service_category():
    if current_user.role != 'admin': return redirect(url_for('index'))
    form = ServiceCategoryForm()
    if form.validate_on_submit():
        new_category = ServiceCategory(
            name=form.name.data,
            description=form.description.data,
            calculation_method=form.calculation_method.data
        )
        db.session.add(new_category)
        db.session.commit()
        log_activity('Service Category Created', f"Admin '{current_user.email}' created service category: '{new_category.name}'", user_id=current_user.id)
        flash(f"Category '{form.name.data}' created successfully.", 'success')
        return redirect(url_for('admin_service_categories'))
    return render_template('admin_edit_service_category.html', form=form, title="Add New Service Category")

@app.route('/admin/service-categories/edit/<int:category_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_service_category(category_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    category = db.session.get(ServiceCategory, category_id)
    if not category:
        flash("Category not found.", "error")
        return redirect(url_for('admin_service_categories'))
    
    form = ServiceCategoryForm(obj=category)
    if form.validate_on_submit():
        category.name = form.name.data
        category.description = form.description.data
        category.calculation_method = form.calculation_method.data
        db.session.commit()
        log_activity('Service Category Updated', f"Admin '{current_user.email}' updated service category: '{category.name}'", user_id=current_user.id)
        flash(f"Category '{form.name.data}' has been updated.", 'success')
        return redirect(url_for('admin_service_categories'))
        
    return render_template('admin_edit_service_category.html', form=form, title=f"Edit: {category.name}")

@app.route('/admin/service-categories/delete/<int:category_id>', methods=['POST'])
@login_required
def admin_delete_service_category(category_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    category = db.session.get(ServiceCategory, category_id)
    if category:
        db.session.delete(category)
        log_activity('Service Category Deleted', f"Admin '{current_user.email}' deleted service category: '{category_name}'", user_id=current_user.id)
        db.session.commit()
        flash(f"Category '{category.name}' has been deleted.", 'success')
    else:
        flash("Category not found.", "error")
    return redirect(url_for('admin_service_categories'))

@app.route('/admin/service-categories/<int:category_id>/items', methods=['GET', 'POST'])
@login_required
def admin_manage_category_items(category_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    category = db.session.get(ServiceCategory, category_id)
    if not category:
        flash("Category not found.", "error")
        return redirect(url_for('admin_service_categories'))

    item_form = ServiceItemForm()
    price_form = ServicePriceForm()

    if 'submit_item' in request.form and item_form.validate_on_submit():
        new_item = ServiceItem(
            name=item_form.name.data,
            estimated_time_mins=item_form.estimated_time_mins.data,
            category_id=category.id
        )
        db.session.add(new_item)
        db.session.commit()
        flash(f"Item '{new_item.name}' added to {category.name}.", 'success')
        return redirect(url_for('admin_manage_category_items', category_id=category.id))

    return render_template('admin_manage_category_items.html', category=category, item_form=item_form, price_form=price_form)

@app.route('/admin/service-items/<int:item_id>/add_price', methods=['POST'])
@login_required
def admin_add_service_price(item_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    item = db.session.get(ServiceItem, item_id)
    if not item:
        flash("Service item not found.", "error")
        return redirect(url_for('admin_service_categories'))

    form = ServicePriceForm()
    if form.validate_on_submit():
        # Check if a price for this frequency already exists
        existing_price = ServicePrice.query.filter_by(service_item_id=item.id, frequency=form.frequency.data).first()
        if existing_price:
            flash(f"A price for '{form.frequency.data}' frequency already exists for this item. Please edit the existing one.", 'error')
        else:
            new_price = ServicePrice(
                frequency=form.frequency.data,
                price=form.price.data,
                service_item_id=item.id
            )
            db.session.add(new_price)
            log_activity('Service Price Added', f"Admin '{current_user.email}' added a new price (R{new_price.price} for {new_price.frequency}) to service item '{item.name}'.", user_id=current_user.id)
            db.session.commit()
            flash(f"Price added for '{form.frequency.data}'.", 'success')
    else:
        flash("There was an error with the price form.", "error")

    return redirect(url_for('admin_manage_category_items', category_id=item.category_id))

@app.route('/admin/service-prices/delete/<int:price_id>', methods=['POST'])
@login_required
def admin_delete_service_price(price_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    price = db.session.get(ServicePrice, price_id)
    if price:
        category_id = price.service_item.category_id
        db.session.delete(price)
        log_activity('Service Price Deleted', f"Admin '{current_user.email}' deleted a price ({price.frequency} - R{price.price}) from service item '{price.service_item.name}'.", user_id=current_user.id)
        db.session.commit()
        flash("Price point has been deleted.", 'success')
        return redirect(url_for('admin_manage_category_items', category_id=category_id))
    else:
        flash("Price not found.", "error")
        return redirect(url_for('admin_service_categories'))

@app.route('/admin/service-items/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_service_item(item_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    item = db.session.get(ServiceItem, item_id)
    if not item:
        flash("Service item not found.", "error")
        return redirect(url_for('admin_service_categories'))

    form = ServiceItemForm(obj=item)
    if form.validate_on_submit():
        item.name = form.name.data
        # item.price = form.price.data <-- This line has been removed
        item.estimated_time_mins = form.estimated_time_mins.data
        log_activity('Service Item Updated', f"Admin '{current_user.email}' updated service item '{item.name}'.", user_id=current_user.id)
        db.session.commit()
        flash(f"Item '{item.name}' has been updated.", 'success')
        return redirect(url_for('admin_manage_category_items', category_id=item.category_id))
    
    return render_template('admin_edit_service_item.html', form=form, item=item, title=f"Edit Item: {item.name}")

@app.route('/admin/service-items/delete/<int:item_id>', methods=['POST'])
@login_required
def admin_delete_service_item(item_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    item = db.session.get(ServiceItem, item_id)
    if item:
        category_id = item.category_id
        db.session.delete(item)
        log_activity('Service Item Deleted', f"Admin '{current_user.email}' deleted service item '{item.name}'.", user_id=current_user.id)
        db.session.commit()
        flash(f"Item '{item.name}' has been deleted.", 'success')
        return redirect(url_for('admin_manage_category_items', category_id=category_id))
    else:
        flash("Item not found.", "error")
        return redirect(url_for('admin_service_categories'))

# --- PUBLIC-FACING STAFF APPLICATION ---
@app.route('/staff-register', methods=['GET', 'POST'])
def staff_register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone_number')
        message_body = request.form.get('message')

        msg = Message(
            subject=f"New Staff Application from {full_name}",
            sender=app.config['MAIL_USERNAME'],
            recipients=['hello@nieuwburg.co.za']
        )
        msg.body = f"Application details:\n\nName: {full_name}\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message_body}"
        try:
            mail.send(msg)
            flash('Thank you for your application! We will be in contact shortly.', 'success')
        except Exception as e:
            flash(f'An error occurred. Please try again. Error: {e}', 'error')

        return redirect(url_for('index'))
        
    return render_template('staff_register.html')


# --- GENERAL PAGE ROUTES ---
BLOG_POSTS = []

@app.route('/')
def index(): return render_template('index.html')
@app.route('/blog')
def blog():
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_date.desc()).all()
    return render_template('blog.html', posts=posts)
@app.route('/blog/<int:post_id>')
def post_detail(post_id):
    post = db.session.get(Post, post_id)
    if not post:
        return redirect(url_for('blog'))
    return render_template('post_detail.html', post=post)
@app.route('/faq')
def faq(): return render_template('faq.html')
@app.route('/gallery')
def gallery(): return render_template('gallery.html')

# --- API Routes ---
@app.route('/api/quote', methods=['POST'])
def api_quote():
    data = request.json or {}
    if not current_user.is_authenticated:
        return jsonify({"status": "error", "message": "You must be logged in to request a quote."}), 401

    new_quote_request = QuoteRequest(
        property_type=data.get('property-type'),
        primary_service=data.get('primary-service'),
        service_frequency=data.get('service-frequency'),
        user_id=current_user.id
    )
    db.session.add(new_quote_request)
    log_activity('New Quote Request', f"User '{current_user.email}' submitted a new quote request.", user_id=current_user.id)
    db.session.commit()
    flash("Thank you! We've received your quote request.", "success")
    return jsonify({"status": "ok", "message": "Quote request received."})

@app.route('/api/posts')
def api_posts():
    posts = Post.query.order_by(Post.created_date.desc()).all()
    posts_data = [{
        "id": post.id,
        "title": post.title,
        "excerpt": post.excerpt or (post.content[:150] + '...'),
        "date": post.created_date.strftime('%d %B %Y')
    } for post in posts]
    return jsonify(posts_data)

@app.route('/api/staff_apply', methods=['POST'])
def api_staff_apply():
    data = request.json or {}
    try:
        new_application = StaffApplication(
            full_name=data.get('full_name'),
            age=int(data.get('age')),
            phone_number=data.get('phone_number'),
            email=data.get('email'),
            address=data.get('address')
        )
        db.session.add(new_application)
        db.session.commit()

        # Send notification email
        msg = Message(
            subject="[Nieuwburg Blitz] New Staff Application Received",
            sender=app.config['MAIL_USERNAME'],
            recipients=['hello@nieuwburg.co.za'] # Your specified email
        )
        msg.body = f"""
        A new staff application has been submitted through the website.

        Name: {data.get('full_name')}
        Age: {data.get('age')}
        Phone: {data.get('phone_number')}
        Email: {data.get('email')}
        Address: {data.get('address')}

        The application has been saved to the admin panel.
        """
        mail.send(msg)

        return jsonify({"status": "ok", "message": "Thank you! Your application has been submitted successfully."})
    except Exception as e:
        # Log the error for debugging
        print(f"Error in staff application: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred. Please try again later."}), 500
    
@app.route('/api/contact', methods=['POST'])
def api_contact():
    data = request.json
    try:
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        area = data.get('area')
        message_body = data.get('message')

        if not all([name, email, phone, message_body]):
            return jsonify({"status": "error", "message": "Please fill in all required fields."}), 400

        # Save to database
        new_request = SpecializedQuoteRequest(
            name=name, email=email, phone=phone, area=area, message=message_body
        )
        db.session.add(new_request)
        db.session.commit()

        # Send email in background
        msg = Message(
            subject=f"New Specialized Quote Request from {name}",
            sender=app.config['MAIL_USERNAME'],
            recipients=['peerinnoveer@gmail.com'], # Your "work" email
            body=f"A new specialized quote request has been saved to the admin panel.\n\n"
                 f"Name: {name}\n"
                 f"Email: {email}\n"
                 f"Phone: {phone}\n"
                 f"Area: {area or 'Not specified'}\n\n"
                 f"Message:\n{message_body}"
        )
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        
        return jsonify({"status": "ok", "message": "Thank you for your request! We will review the details and get back to you with a quote shortly."})
    except Exception as e:
        db.session.rollback()
        print(f"Error in contact form API: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500
    
@app.route('/api/services')
def api_services():
    categories = ServiceCategory.query.options(db.joinedload(ServiceCategory.items).joinedload(ServiceItem.prices)).order_by(ServiceCategory.name).all()
    
    output = []
    for category in categories:
        cat_data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'calculation_method': category.calculation_method,
            'items': []
        }
        for item in category.items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'estimated_time_mins': item.estimated_time_mins,
                'prices': [{'frequency': p.frequency, 'price': p.price} for p in item.prices]
            }
            cat_data['items'].append(item_data)
        output.append(cat_data)
        
    return jsonify(output)

@app.route('/api/availability/<string:date_str>')
def api_availability(date_str):
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    # --- Define Your Business Hours ---
    opening_time = time(8, 0)  # 8:00 AM
    closing_time = time(17, 0) # 5:00 PM
    slot_interval_mins = 30    # Check for a new slot every 30 minutes
    # --------------------------------

    existing_jobs_on_day = Job.query.filter(Job.scheduled_date == booking_date).all()
    
    available_slots = []
    current_time = datetime.combine(booking_date, opening_time)
    end_of_day = datetime.combine(booking_date, closing_time)

    while current_time < end_of_day:
        slot_is_available = True
        # Check if this slot conflicts with any existing jobs
        for job in existing_jobs_on_day:
            if job.start_time:
                job_start = datetime.combine(booking_date, job.start_time)
                # Simple check: if a job starts at this time, the slot is taken.
                # A more advanced check would consider the job's duration.
                if current_time.time() == job.start_time:
                    slot_is_available = False
                    break
        
        if slot_is_available:
            available_slots.append(current_time.strftime('%H:%M'))

        current_time += timedelta(minutes=slot_interval_mins)

    return jsonify(available_slots)

# --- REVISED: Now handles the Full Name correctly ---
@app.route('/api/create_booking', methods=['POST'])
def create_booking():
    data = request.json
    try:
        customer_email = data.get('email')
        customer_name = data.get('name') # <-- Get the name
        
        # Check if user exists, otherwise create a temporary guest user
        user = User.query.filter_by(email=customer_email).first()
        if not user:
            guest_password = str(uuid.uuid4())
            user = User(email=customer_email, role='client')
            user.set_password(guest_password)
            db.session.add(user)
            
            profile = Profile(
                user=user,
                full_name=customer_name, # <-- Use the name here
                phone_number=data.get('phone'),
                address=data.get('address')
            )
            db.session.add(profile)
            db.session.flush()

        new_request = QuoteRequest(
            user_id=user.id,
            primary_service=data.get('categoryName'),
            property_type=data.get('frequency'),
            address=data.get('address'),
            total_price=float(data.get('totalPrice')),
            service_details=json.dumps(data.get('services')),
            status='Pending'
        )
        
        db.session.add(new_request)
        db.session.commit()

        return jsonify({
            'status': 'ok',
            'message': 'Thank you! Your booking request has been received. We will contact you shortly to confirm.',
            'booking_id': new_request.id
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error creating booking request: {e}")
        return jsonify({'status': 'error', 'message': 'Could not process your booking request.'}), 500
    
@app.route('/api/recent-activity')
@login_required
def api_recent_activity():
    if current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403

    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(5).all()
    
    # Use the new SAST conversion function
    sast_timezone = pytz.timezone('Africa/Johannesburg')

    recent_logs = [{
        'timestamp': pytz.utc.localize(log.timestamp).astimezone(sast_timezone).strftime('%d %b, %H:%M'),
        'description': log.description,
        'user_email': log.user.email if log.user else 'System'
    } for log in logs]
    
    return jsonify(recent_logs)

# --- CONTEXT PROCESSOR & MAIN EXECUTION ---
@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}

# --- CONTEXT PROCESSOR FOR GOOGLE MAPS ---
@app.context_processor
def inject_google_maps_api_key():
    return dict(google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY'))

# app.py

@app.route('/initialize-payment', methods=['POST'])
def initialize_payment():
    print("--- [DEBUG] /initialize-payment endpoint called ---")
    try:
        data = request.json
        if not data:
            print("[DEBUG] ERROR: No JSON data received in request.")
            return jsonify({'error': 'No data provided'}), 400
        
        print(f"[DEBUG] Received data: {data}")

        total_price = data.get('totalPrice')
        email = data.get('email')

        if total_price is None or email is None:
            print(f"[DEBUG] ERROR: Missing 'totalPrice' or 'email'. Price: {total_price}, Email: {email}")
            return jsonify({'error': 'Missing required payment information.'}), 400

        amount_in_kobo = int(float(total_price) * 100)

        payload = {
            "email": email,
            "amount": amount_in_kobo,
            "currency": "ZAR",
            "metadata": {
                "booking_details": data
            }
        }
        headers = {
            "Authorization": f"Bearer {os.environ.get('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json"
        }

        print("[DEBUG] Sending payload to Paystack...")
        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=payload)
        response.raise_for_status() # This will raise an error for bad responses (4xx or 5xx)
        
        response_data = response.json()
        if response_data.get('status'):
            print("[DEBUG] Paystack initialization successful.")
            return jsonify(response_data['data'])
        else:
            print("[DEBUG] Paystack returned an error:", response_data.get('message'))
            return jsonify({'error': 'Could not initialize payment with provider.'}), 400

    except requests.exceptions.HTTPError as http_err:
        print(f"[DEBUG] HTTP error occurred with Paystack API: {http_err}")
        print(f"[DEBUG] Paystack response content: {response.text}")
        return jsonify({'error': f"HTTP error: {http_err}"}), 500
    except Exception as e:
        print(f"[DEBUG] A critical error occurred in initialize_payment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An internal server error occurred.'}), 500

# --- REVISED: Handles new user registration flow ---
@app.route('/payment-callback')
def payment_callback():
    reference = request.args.get('reference')
    if not reference:
        flash('Invalid payment callback.', 'error')
        return redirect(url_for('index'))

    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {"Authorization": f"Bearer {os.environ.get('PAYSTACK_SECRET_KEY')}"}

    try:
        response = requests.get(url, headers=headers)
        verification_data = response.json()

        if verification_data.get('data', {}).get('status') == 'success':
            metadata = verification_data['data']['metadata']
            
            # This part for quote deposits is unchanged and correct.
            if 'quote_id' in metadata:
                quote = db.session.get(Quote, metadata['quote_id'])
                if quote:
                    quote.deposit_paid = True
                    quote.status = 'Confirmed'
                    job = Job.query.filter(Job.notes.like(f"%Quote #{quote.quote_number}%")).first()
                    if job:
                        job.status = 'Scheduled'
                    db.session.commit()
                    log_activity('Deposit Paid', f"50% deposit paid for Quote {quote.quote_number}.", user_id=quote.user_id)
                    flash('Thank you! Your deposit has been received and your booking is confirmed.', 'success')
                    if not current_user.is_authenticated:
                        login_user(quote.user)
                    return redirect(url_for('client_dashboard'))

            # THIS IS THE NEW, CORRECT LOGIC FOR NEW BOOKINGS
            elif 'booking_details' in metadata:
                booking_data = metadata['booking_details']
                user = User.query.filter_by(email=booking_data.get('email')).first()

                is_new_user = not user
                if is_new_user:
                    # Create the new user now that payment is confirmed
                    temp_password = str(uuid.uuid4()) # Unusable password
                    user = User(email=booking_data.get('email'), role='client', is_confirmed=False)
                    user.set_password(temp_password)
                    db.session.add(user)
                    
                    profile = Profile(
                        user=user,
                        full_name=booking_data.get('name'), 
                        phone_number=booking_data.get('phone'), 
                        address=booking_data.get('address')
                    )
                    db.session.add(profile)
                    db.session.flush()

                # Create the booking records
                new_request = QuoteRequest(
                    user_id=user.id,
                    primary_service=booking_data.get('categoryName'),
                    property_type=booking_data.get('frequency'),
                    total_price=float(booking_data.get('totalPrice')),
                    service_details=json.dumps(booking_data.get('services')),
                    status='Confirmed'
                )
                db.session.add(new_request)
                db.session.flush()

                new_job = Job(
                    quote_request_id=new_request.id,
                    scheduled_date=datetime.strptime(booking_data.get('date'), '%Y-%m-%d').date(),
                    start_time=datetime.strptime(booking_data.get('time'), '%H:%M').time(),
                    status='Scheduled'
                )
                db.session.add(new_job)
                db.session.commit()
                
                # --- THIS IS THE UPDATED BLOCK WITH DEBUGGING ---
                if is_new_user:
                    print("\n--- [PAYMENT DEBUG] New user detected. Preparing to send activation email. ---")
                    try:
                        # Send the new "Welcome & Activate" email
                        token = generate_confirmation_token(user.email)
                        set_password_url = url_for('create_password', token=token, _external=True)
                        logo_url = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
                        html = render_template('email/welcome_activate.html', set_password_url=set_password_url, logo_url=logo_url)
                        msg = Message(subject="[Nieuwburg Blitz] Welcome & Activate Your Account",
                                      sender=app.config['MAIL_USERNAME'],
                                      recipients=[user.email],
                                      html=html)
                        
                        print("[PAYMENT DEBUG] Email message object created. Preparing thread.")
                        thr = Thread(target=send_async_email, args=[app, msg])
                        print("[PAYMENT DEBUG] Thread object created. Starting thread...")
                        thr.start()
                        print("[PAYMENT DEBUG] Thread started. The email process should now be running in the background.")
                        
                        flash('Booking confirmed! Please check your email to create your password and access your dashboard.', 'success')
                    except Exception as e:
                        print(f"--- [PAYMENT DEBUG] CRITICAL ERROR occurred while preparing the email thread: {e} ---")
                        import traceback
                        traceback.print_exc()
                        flash('Booking confirmed, but there was an error sending your activation email. Please contact support.', 'error')
                else:
                    flash('Payment successful! Your new booking is confirmed.', 'success')
                # --- END OF UPDATED BLOCK ---

                return redirect(url_for('index'))
        
        else:
            flash('Payment verification failed. Please contact support.', 'error')
            return redirect(url_for('index'))
            
    except Exception as e:
        db.session.rollback()
        print(f"CRITICAL ERROR in payment_callback: {e}") 
        flash(f'A critical error occurred during payment verification: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/api/jobs/by-date/<date_str>')
@login_required
def api_jobs_by_date(date_str):
    if current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403
    
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400

    jobs = Job.query.filter_by(scheduled_date=target_date).order_by(Job.start_time).all()
    
    jobs_data = []
    for job in jobs:
        client_name = "N/A"
        if job.quote_request and job.quote_request.user and job.quote_request.user.profile:
            client_name = job.quote_request.user.profile.full_name or job.quote_request.user.email

        jobs_data.append({
            "id": job.id,
            "start_time": job.start_time.strftime('%H:%M') if job.start_time else 'All Day',
            "end_time": job.end_time.strftime('%H:%M') if job.end_time else '',
            "client_name": client_name,
            "service": job.quote_request.primary_service if job.quote_request else 'N/A' # Keep it concise
        })
        
    return jsonify(jobs_data)

@app.route('/api/job/details/<int:job_id>')
@login_required
def api_job_details(job_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403
        
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    all_staff = User.query.filter_by(role='staff').all()
    
    client_name = "N/A"
    address = "N/A"
    if job.quote_request and job.quote_request.user and job.quote_request.user.profile:
        client_name = job.quote_request.user.profile.full_name or job.quote_request.user.email
        address = job.quote_request.user.profile.address

    details = {
        "id": job.id,
        "scheduled_date": job.scheduled_date.isoformat(),
        "start_time": job.start_time.strftime('%H:%M') if job.start_time else "",
        "notes": job.notes or "",
        "client_name": client_name,
        "address": address,
        "assigned_staff_ids": [s.id for s in job.assigned_staff],
        "all_staff": [{"id": s.id, "name": s.profile.full_name} for s in all_staff]
    }
    return jsonify(details)

@app.route('/api/job/update/<int:job_id>', methods=['POST'])
@login_required
def api_update_job(job_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403
        
    job = db.session.get(Job, job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
        
    data = request.json
    
    try:
        job.notes = data.get('notes', job.notes)
        
        if 'start_time' in data and data['start_time']:
            job.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        else:
            job.start_time = None
            
        if 'assigned_staff_ids' in data:
            job.assigned_staff.clear()
            for staff_id in data['assigned_staff_ids']:
                staff = db.session.get(User, staff_id)
                if staff:
                    job.assigned_staff.append(staff)
        
        db.session.commit()
        log_activity('Job Updated via API', f"Admin '{current_user.email}' updated job ID {job.id} through the calendar modal.", user_id=current_user.id)
        return jsonify({"status": "ok", "message": "Job updated successfully."})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/clients/search')
@login_required
def api_search_clients():
    if current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403
    
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    clients = User.query.join(Profile).filter(
        User.role == 'client',
        Profile.full_name.ilike(f'%{query}%')
    ).limit(10).all()
    
    client_data = [
        {"id": c.id, "name": c.profile.full_name, "email": c.email, "address": c.profile.address} 
        for c in clients
    ]
    return jsonify(client_data)


@app.route('/api/job/create', methods=['POST'])
@login_required
def api_create_job():
    if current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403
    
    data = request.json
    client_name = data.get('client_name')
    create_new_client = data.get('create_new_client', False)
    user_id = None

    # --- Client Handling ---
    user = User.query.join(Profile).filter(Profile.full_name == client_name).first()
    if user:
        user_id = user.id
    elif create_new_client:
        # Create a new user and profile
        temp_email = f"temp_{str(uuid.uuid4())[:8]}@nieuwburg.co.za"
        new_user = User(email=temp_email, role='client', is_confirmed=True)
        new_user.set_password(str(uuid.uuid4())) # Set a random, secure password
        
        new_profile = Profile(
            user=new_user,
            full_name=client_name,
            phone_number=data.get('phone'),
            address=data.get('address')
        )
        db.session.add(new_user)
        db.session.add(new_profile)
        db.session.flush()
        user_id = new_user.id
        log_activity('Client Auto-Created', f"New client '{client_name}' created from manual job entry.", user_id=current_user.id)
    else:
        return jsonify({"status": "error", "message": f"Client '{client_name}' not found."}), 400

    # --- Job and QuoteRequest Creation ---
    try:
        new_quote_request = QuoteRequest(
            user_id=user_id,
            primary_service=data.get('service'), # FIX: Use the 'service' field from the form
            status='Scheduled'
        )
        db.session.add(new_quote_request)
        db.session.flush()

        new_job = Job(
            quote_request_id=new_quote_request.id,
            scheduled_date=datetime.strptime(data.get('scheduled_date'), '%Y-%m-%d').date(),
            notes=data.get('notes') # FIX: The detailed notes now correctly go here
        )
        if 'start_time' in data and data['start_time']:
            new_job.start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        
        db.session.add(new_job)
        db.session.commit()
        
        log_activity('Job Manual Create', f"Admin '{current_user.email}' created a new job for {client_name}.", user_id=current_user.id)
        return jsonify({"status": "ok", "message": "Job created successfully."})

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@example.com').first():
            admin_user = User(email='admin@example.com', role='admin', is_confirmed=True)
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.add(Profile(user=admin_user))
            db.session.commit()
            print("Default admin user created with password 'password'.")
    app.run(debug=True)