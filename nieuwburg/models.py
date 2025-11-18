import re
import uuid
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.types import JSON
from datetime import datetime, date, time
from itsdangerous import URLSafeTimedSerializer as Serializer # Added for tokens
from flask import current_app # Added for tokens

# ---
# 1. NEW TENANT MODEL
# ---
class Tenant(db.Model):
    __tablename__ = 'tenant'
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    subscription_plan = db.Column(db.String(50), nullable=False) 
    paystack_reference = db.Column(db.String(100), unique=True, nullable=True)
    is_active = db.Column(db.Boolean, default=False, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Relationships ---
    users = db.relationship('User', back_populates='tenant', lazy=True)
    business_settings = db.relationship('BusinessSettings', back_populates='tenant', uselist=False, cascade="all, delete-orphan")
    quotes = db.relationship('Quote', back_populates='tenant', lazy=True)
    invoices = db.relationship('Invoice', back_populates='tenant', lazy=True)
    clients = db.relationship('Profile', back_populates='tenant', lazy=True)
    service_categories = db.relationship('ServiceCategory', back_populates='tenant', lazy=True)
    service_items = db.relationship('ServiceItem', back_populates='tenant', lazy=True)
    service_clauses = db.relationship('ServiceClause', back_populates='tenant', lazy=True)
    quote_requests = db.relationship('QuoteRequest', back_populates='tenant', lazy=True)
    jobs = db.relationship('Job', back_populates='tenant', lazy=True)
    posts = db.relationship('Post', back_populates='tenant', lazy=True)
    activities = db.relationship('ActivityLog', back_populates='tenant', lazy=True)
    
    def __repr__(self):
        return f'<Tenant {self.business_name}>'

# --- Association Tables ---
job_staff_association = db.Table('job_staff_association',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

service_clauses_association = db.Table('service_clauses_association',
    db.Column('service_item_id', db.Integer, db.ForeignKey('service_item.id'), primary_key=True),
    db.Column('service_clause_id', db.Integer, db.ForeignKey('service_clause.id'), primary_key=True)
)

# --- Main Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(256)) # Increased length from 128
    role = db.Column(db.String(20), nullable=False, default='client')
    
    password_reset_required = db.Column(db.Boolean, default=False)
    
    # --- MODIFICATION: This is our "inactive" flag ---
    is_confirmed = db.Column(db.Boolean, nullable=False, default=False) 
    
    confirmed_on = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_failed_login = db.Column(db.DateTime, nullable=True)
    referral_code = db.Column(db.String(10), unique=True, nullable=True)
    referral_points = db.Column(db.Integer, default=0)

    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='users')
    # --- END NEW TENANCY FIELDS ---

    # Relationships
    profile = db.relationship('Profile', back_populates='user', uselist=False, cascade="all, delete-orphan")
    quote_requests = db.relationship('QuoteRequest', back_populates='user', lazy=True)
    quotes = db.relationship('Quote', back_populates='user', lazy=True, cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    # --- ADDED: Token Methods (re-using your auth logic) ---
    def get_confirmation_token(self, salt='email-confirm-salt'):
        s = Serializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt=salt)

    @staticmethod
    def verify_confirmation_token(token, salt='email-confirm-salt', max_age=3600):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt=salt, max_age=max_age)
        except:
            return None
        return User.query.filter_by(email=email).first()

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    profile_image = db.Column(db.String(100), default='avatar_picture_profile_user_icon.png')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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

    # --- MODIFIED: Changed backref to back_populates ---
    user = db.relationship('User', back_populates='profile', foreign_keys=[user_id])
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True) # Nullable for existing clients
    tenant = db.relationship('Tenant', back_populates='clients')
    # --- END NEW TENANCY FIELDS ---

class QuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_type = db.Column(db.String(50), nullable=True) 
    primary_service = db.Column(db.String(100), nullable=True)
    service_frequency = db.Column(db.String(50), nullable=True)
    total_price = db.Column(db.Float, nullable=True)
    service_details = db.Column(db.Text, nullable=True)
    service_category_name = db.Column(db.String(150), nullable=True) 
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', back_populates='quote_requests')
    
    name = db.Column(db.String(150), nullable=True) 
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True) 
    subject = db.Column(db.String(150), nullable=True) 
    description = db.Column(db.Text, nullable=True) 

    request_date = db.Column(db.DateTime, default=datetime.utcnow) 
    status = db.Column(db.String(50), default='Pending') 

    job = db.relationship('Job', back_populates='quote_request', uselist=False)

    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='quote_requests')
    # --- END NEW TENANCY FIELDS ---

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
    line_items = db.relationship('QuoteLineItem', back_populates='quote', lazy=True, cascade="all, delete-orphan")
    business_address = db.Column(db.String(500), nullable=True)
    registration_number = db.Column(db.String(100), nullable=True)
    terms_and_conditions = db.Column(db.Text, nullable=True)

    # --- MODIFIED: Changed backref to back_populates ---
    user = db.relationship('User', back_populates='quotes')
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='quotes')
    # --- END NEW TENANCY FIELDS ---

class QuoteLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=True)
    
    # --- MODIFIED: Changed backref to back_populates ---
    quote = db.relationship('Quote', back_populates='line_items')
    service_item = db.relationship('ServiceItem', back_populates='quote_line_items')

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True, nullable=False)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    discount_value = db.Column(db.Float, default=0.0)
    discount_type = db.Column(db.String(10), default='R')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='Unpaid', nullable=False)
    payment_reference = db.Column(db.String(100), unique=True, nullable=True)
    payment_token = db.Column(db.String(100), unique=True, nullable=True)
    
    # --- MODIFIED: Changed relationships ---
    client = db.relationship('User', overlaps="invoices,user", foreign_keys=[user_id]) # Kept your overlaps
    user = db.relationship('User', back_populates='invoices', foreign_keys=[user_id]) # Added back_populates
    line_items = db.relationship('InvoiceLineItem', back_populates='invoice', lazy=True, cascade="all, delete-orphan")
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='invoices')
    # --- END NEW TENANCY FIELDS ---

class InvoiceLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.id'), nullable=False)
    
    # --- MODIFIED: Changed backref to back_populates ---
    invoice = db.relationship('Invoice', back_populates='line_items')

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
    service_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=True)
    service = db.relationship('ServiceItem', back_populates='jobs')
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client = db.relationship('User', foreign_keys=[client_id], backref=db.backref('jobs_as_client', lazy=True))
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='jobs')
    # --- END NEW TENANCY FIELDS ---

class BusinessSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(255), default="Nieuwburg Blitz")
    business_address = db.Column(db.String(500), default="24 A 5, Parow Park, Balfour Street, Cape Town, 7500")
    registration_number = db.Column(db.String(100), default="2025/123456/07")
    default_terms = db.Column(db.Text, default="1. All payments are due within 30 days.\n2. ...")
    
    # --- NEW TENANCY FIELDS (1-to-1) ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True, unique=True) # Start as nullable, wizard will set it
    tenant = db.relationship('Tenant', back_populates='business_settings')
    # --- END NEW TENANCY FIELDS ---
    
    @staticmethod
    def get_settings():
        """A helper to get the first (and only) settings row."""
        # This will be updated later to be tenant-aware.
        settings = BusinessSettings.query.first()
        if not settings:
            # We can't create one without a tenant_id, so we'll just return a default object
            # The setup wizard will create the real one.
            return BusinessSettings() # Return a transient, default object
        return settings

class ServiceClause(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  
    text = db.Column(db.Text, nullable=False)

    service_items = db.relationship(
        'ServiceItem', 
        secondary=service_clauses_association,
        back_populates='linked_clauses'
    )
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='service_clauses')
    # --- END NEW TENANCY FIELDS ---

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'text': self.text
        }

class StaffApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    id_number = db.Column(db.String(13))
    address = db.Column(db.Text)
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    document_filenames = db.Column(JSON, nullable=True)
    # This model remains non-tenanted

class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    calculation_method = db.Column(db.String(50), nullable=False, default='options')
    items = db.relationship('ServiceItem', back_populates='category', lazy=True, cascade="all, delete-orphan")

    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='service_categories')
    # --- END NEW TENANCY FIELDS ---

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    estimated_time_mins = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    prices = db.relationship('ServicePrice', back_populates='service_item', lazy=True, cascade="all, delete-orphan")
    
    # --- MODIFIED: Changed backref to back_populates ---
    category = db.relationship('ServiceCategory', back_populates='items')
    quote_line_items = db.relationship('QuoteLineItem', back_populates='service_item')
    jobs = db.relationship('Job', back_populates='service')
    
    linked_clauses = db.relationship(
        'ServiceClause',
        secondary=service_clauses_association,
        back_populates='service_items'
    )
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='service_items')
    # --- END NEW TENANCY FIELDS ---

class ServicePrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)
    
    # --- MODIFIED: Changed backref to back_populates ---
    service_item = db.relationship('ServiceItem', back_populates='prices')

class Booking(db.Model):
    # This model seems to be from the old system and is replaced by QuoteRequest/Job
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

    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='posts')
    # --- END NEW TENANCY FIELDS ---

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    
    # --- NEW TENANCY FIELDS ---
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenant.id'), nullable=True)
    tenant = db.relationship('Tenant', back_populates='activities')
    # --- END NEW TENANCY FIELDS ---

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)


# --- Helper Functions ---
def get_next_quote_number():
    # This will need to be made tenant-aware in Phase 3
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
    # This will need to be made tenant-aware in Phase 3
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    if not last_invoice or '-' not in last_invoice.invoice_number:
        return "INV-0061"
    try:
        last_num = int(last_invoice.invoice_number.split('-')[1])
        new_num = last_num + 1
        return f"INV-{new_num:04d}"
    except (IndexError, ValueError):
        return "INV-0061"