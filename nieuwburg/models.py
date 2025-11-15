import re
import uuid
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.types import JSON
from datetime import datetime, date, time

# --- Association Tables ---
job_staff_association = db.Table('job_staff_association',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# === NEW: Association table for Services and T&C Clauses ===
service_clauses_association = db.Table('service_clauses_association',
    db.Column('service_item_id', db.Integer, db.ForeignKey('service_item.id'), primary_key=True),
    db.Column('service_clause_id', db.Integer, db.ForeignKey('service_clause.id'), primary_key=True)
)
# === END OF NEW CODE ===


# --- Main Models ---
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
    
    referral_code = db.Column(db.String(10), unique=True, nullable=True)
    referral_points = db.Column(db.Integer, default=0)

    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False, cascade="all, delete-orphan")
    #quote_requests = db.relationship('QuoteRequest', lazy=True, cascade="all, delete-orphan")
    quote_requests = db.relationship('QuoteRequest', back_populates='user', lazy=True)
    quotes = db.relationship('Quote', backref='user', lazy=True, cascade="all, delete-orphan")
    invoices = db.relationship('Invoice', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

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
    
    # Fields used by specialized quote form / contact form
    name = db.Column(db.String(150), nullable=True) 
    email = db.Column(db.String(150), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(255), nullable=True) # Single definition
    subject = db.Column(db.String(150), nullable=True) 
    description = db.Column(db.Text, nullable=True) # Use this for the 'message'

    # Common fields
    request_date = db.Column(db.DateTime, default=datetime.utcnow) 
    status = db.Column(db.String(50), default='Pending') # Unified status field

    # Relationships
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

    # === NEW: Fields for per-quote settings ===
    business_address = db.Column(db.String(500), nullable=True)
    registration_number = db.Column(db.String(100), nullable=True)
    terms_and_conditions = db.Column(db.Text, nullable=True)
    # === END OF NEW CODE ===

class QuoteLineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote.id'), nullable=False)

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
    client = db.relationship('User', overlaps="invoices,user")
    line_items = db.relationship('InvoiceLineItem', backref='invoice_list', lazy=True, cascade="all, delete-orphan")

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
    service_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=True)
    service = db.relationship('ServiceItem', backref=db.backref('jobs', lazy=True))
    client_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client = db.relationship('User', foreign_keys=[client_id], backref=db.backref('jobs_as_client', lazy=True))

class BusinessSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(255), default="Nieuwburg Blitz")
    business_address = db.Column(db.String(500), default="24 A 5, Parow Park, Balfour Street, Cape Town, 7500")
    registration_number = db.Column(db.String(100), default="2025/123456/07")
    default_terms = db.Column(db.Text, default="1. All payments are due within 30 days.\n2. ...")
    
    # We will add the T&C clause library here in Step 2
    
    @staticmethod
    def get_settings():
        """A helper to get the first (and only) settings row."""
        settings = BusinessSettings.query.first()
        if not settings:
            settings = BusinessSettings()
            db.session.add(settings)
            db.session.commit()
        return settings

class ServiceClause(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)  
    text = db.Column(db.Text, nullable=False)

    # === NEW: Link to ServiceItem (many-to-many) ===
    service_items = db.relationship(
        'ServiceItem', 
        secondary=service_clauses_association,
        back_populates='linked_clauses'
    )
    # === END OF NEW CODE ===

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

class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    calculation_method = db.Column(db.String(50), nullable=False, default='options')
    items = db.relationship('ServiceItem', backref='category', lazy=True, cascade="all, delete-orphan")

class ServiceItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    estimated_time_mins = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('service_category.id'), nullable=False)
    prices = db.relationship('ServicePrice', backref='service_item', lazy=True, cascade="all, delete-orphan")
    
    # === NEW: Link to ServiceClause (many-to-many) ===
    linked_clauses = db.relationship(
        'ServiceClause',
        secondary=service_clauses_association,
        back_populates='service_items'
    )
    # === END OF NEW CODE ===

class ServicePrice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    service_item_id = db.Column(db.Integer, db.ForeignKey('service_item.id'), nullable=False)

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

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref=db.backref('activities', lazy=True))

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)


# --- Helper Functions ---
def get_next_quote_number():
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
    last_invoice = Invoice.query.order_by(Invoice.id.desc()).first()
    if not last_invoice or '-' not in last_invoice.invoice_number:
        return "INV-0061"
    try:
        last_num = int(last_invoice.invoice_number.split('-')[1])
        new_num = last_num + 1
        return f"INV-{new_num:04d}"
    except (IndexError, ValueError):
        return "INV-0061"