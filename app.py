from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SubmitField, TextAreaField, Form
from wtforms.validators import Length
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_wtf.csrf import CSRFProtect
from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from datetime import datetime
import json
import os
import re
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_mail import Mail, Message
from datetime import datetime
from datetime import date
from datetime import timedelta
from datetime import datetime, date, timedelta, timezone # Add timezone here
from wtforms import SelectField, DateField, FieldList, FormField, FloatField
from wtforms.validators import Optional
from flask import Response
from xhtml2pdf import pisa
from io import BytesIO
from flask_session import Session
from werkzeug.datastructures import FileStorage

app = Flask(__name__)

csrf = CSRFProtect(app)

# --- CONFIGURATION ---
app.config['SECRET_KEY'] = 'a-very-secret-key-that-you-should-change'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30) # Example: log out after 30 mins of inactivity
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
app.config['MAIL_PASSWORD'] = os.environ.get('EMAIL_PASS')
mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
# Association table for the many-to-many relationship between Jobs and Staff
job_staff_association = db.Table('job_staff_association',
    db.Column('job_id', db.Integer, db.ForeignKey('job.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False, default='client')
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

class QuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    property_type = db.Column(db.String(50))
    primary_service = db.Column(db.String(100))
    service_frequency = db.Column(db.String(50))
    status = db.Column(db.String(20), default='Pending')
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quote_number = db.Column(db.String(20), unique=True, nullable=False)
    quote_date = db.Column(db.Date, nullable=False, default=date.today)
    expiry_date = db.Column(db.Date)
    subtotal = db.Column(db.Float, default=0.0)
    total = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    line_items = db.relationship('QuoteLineItem', backref='quote', lazy=True, cascade="all, delete-orphan")

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
    
    # Foreign key to link back to the original quote request
    quote_request_id = db.Column(db.Integer, db.ForeignKey('quote_request.id'), nullable=True)
    quote_request = db.relationship('QuoteRequest', backref=db.backref('job', uselist=False))
    
    # Many-to-many relationship with Staff (User model)
    assigned_staff = db.relationship('User', secondary=job_staff_association, lazy='subquery',
        backref=db.backref('jobs_assigned', lazy=True))

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

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
        db.session.delete(client_to_delete)
        db.session.commit()
        flash('Client has been deleted.', 'success')
    else:
        flash('This user is not a client.', 'error')
    return redirect(url_for('admin_clients'))

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
        if email and User.query.filter_by(email=email).first():
            flash('A user with this email already exists.', 'error')
            return redirect(url_for('admin_add_staff'))

        new_staff = User(email=email, role='staff')
        new_staff.set_password(str(uuid.uuid4())) # Assign a random initial password

        id_number = form.id_number.data
        dob = None
        if id_number:
            try:
                year_prefix = "19" if int(id_number[0:2]) > 30 else "20" # Simple check for century
                dob_str = year_prefix + id_number[0:6]
                dob = datetime.strptime(dob_str, '%Y%m%d').date()
            except (ValueError, IndexError):
                flash('Invalid ID Number format for date of birth calculation.', 'error')
                # Continue without a DOB or return, depending on your policy
        
        new_profile = Profile(
            user=new_staff,
            full_name=form.full_name.data,
            phone_number=form.phone_number.data,
            address=form.address.data,
            id_number=id_number,
            date_of_birth=dob
        )

        db.session.add(new_staff)
        db.session.add(new_profile)
        db.session.commit()
        flash('New staff member added.', 'success')
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
        # Check if a new file has been uploaded before trying to save it
        if form.profile_image.data and isinstance(form.profile_image.data, FileStorage):
            file = form.profile_image.data
            if file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                staff_member.profile.profile_image = unique_filename

        # Update all other profile fields from the form
        staff_member.profile.full_name = form.full_name.data
        staff_member.profile.phone_number = form.phone_number.data
        staff_member.profile.address = form.address.data
        id_number = form.id_number.data
        staff_member.profile.id_number = id_number

        # This is the line that was missing
        staff_member.profile.notes = request.form.get('notes')

        staff_member.profile.service_frequency = request.form.get('service_frequency')
        service_fee_str = request.form.get('service_fee')
        if service_fee_str and service_fee_str.strip():
            try:
                staff_member.profile.service_fee = float(service_fee_str)
            except ValueError:
                staff_member.profile.service_fee = None
        else:
            staff_member.profile.service_fee = None

        if id_number and len(id_number) == 13:
            try:
                year_prefix = "19" if int(id_number[0:2]) > 30 else "20"
                dob_str = year_prefix + id_number[0:6]
                staff_member.profile.date_of_birth = datetime.strptime(dob_str, '%Y%m%d').date()
            except (ValueError, IndexError):
                flash('Invalid ID Number format. Date of birth not updated.', 'warning')
        else:
            staff_member.profile.date_of_birth = None

        db.session.commit()
        flash('Staff profile updated successfully.', 'success')
        return redirect(url_for('admin_view_staff', user_id=user_id))

    return render_template('admin_edit_staff.html', form=form, staff_member=staff_member)

@app.route('/admin/staff/delete/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_staff(user_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    staff_to_delete = User.query.get_or_404(user_id)
    if staff_to_delete.role == 'staff':
        db.session.delete(staff_to_delete)
        db.session.commit()
        flash('Staff member has been deleted.', 'success')
    else:
        flash('This user is not a staff member.', 'error')
    return redirect(url_for('admin_staff'))

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

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
    email = StringField('Email (Optional)', validators=[Email(), Length(max=100)])
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
    profile_image = FileField('Update Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Update Profile')

class EditClientForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = TextAreaField('Physical Address', validators=[Length(max=500)])
    submit = SubmitField('Update Client')

class QuoteLineItemForm(Form):
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()], default=1)
    unit_price = FloatField('Unit Price', validators=[DataRequired()])

class QuoteForm(FlaskForm):
    client = SelectField('Client', coerce=int, validators=[DataRequired()])
    quote_date = DateField('Quote Date', default=date.today, validators=[DataRequired()])
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    line_items = FieldList(FormField(QuoteLineItemForm), min_entries=1)
    submit = SubmitField('Create Quote')

class InvoiceLineItemForm(Form):
    description = TextAreaField('Description', validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()], default=1)
    unit_price = FloatField('Unit Price', validators=[DataRequired()])

class InvoiceForm(FlaskForm):
    client = SelectField('Client', coerce=int, validators=[DataRequired()])
    invoice_date = DateField('Invoice Date', default=date.today, validators=[DataRequired()])
    due_date = DateField('Due Date', validators=[Optional()])
    line_items = FieldList(FormField(InvoiceLineItemForm), min_entries=1)
    submit = SubmitField('Create Invoice')

# --- AUTHENTICATION & PROFILE ROUTES ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if not user or not user.check_password(form.password.data):
            flash('Please check your login details and try again.', 'error')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('client_dashboard'))

    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        password = form.password.data
        if len(password) < 8 or not re.search("[a-z]", password) or not re.search("[A-Z]", password) or not re.search("[0-9]", password):
            flash('Password must contain an uppercase letter, a lowercase letter, and a number.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(email=form.email.data).first():
            flash('Email address already exists.', 'error')
            return redirect(url_for('register'))

        new_user = User(email=form.email.data, role='client')
        new_user.set_password(form.password.data)
        db.session.add(new_user)

        new_profile = Profile(user=new_user)
        db.session.add(new_profile)

        db.session.commit()

        login_user(new_user)

        flash('Welcome! Please complete your profile.', 'success')
        return redirect(url_for('profile'))

    for field, errors in form.errors.items():
        for error in errors:
            flash(error, 'error')

    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
#@csrf.exempt
def delete_account():
    user_to_delete = db.session.get(User, current_user.id) 
    
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
    
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
    return render_template('admin_dashboard.html')

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    # Corrected query:
    requests = QuoteRequest.query.order_by(QuoteRequest.request_date.desc()).all()

    jobs = Job.query.order_by(Job.scheduled_date).all()

    calendar_events = []
    for job in jobs:
        if job.quote_request and job.quote_request.user:
            client_name = job.quote_request.user.profile.full_name or job.quote_request.user.email
            title = f"{job.quote_request.primary_service} - {client_name}"
        else:
            title = "Scheduled Job"

        event = {
            'title': title,
            'start': job.scheduled_date.isoformat(),
            'allDay': True
        }
        calendar_events.append(event)

    events_json = json.dumps(calendar_events)

    return render_template('admin_bookings.html', requests=requests, events_json=events_json)

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
    return render_template('client_dashboard.html', bookings=user_bookings)

def get_next_quote_number():
    last_quote = Quote.query.order_by(Quote.id.desc()).first()
    if not last_quote:
        return "QU-0051"
    last_num = int(last_quote.quote_number.split('-')[1])
    new_num = last_num + 1
    return f"QU-{new_num:04d}"

@app.route('/admin/quotes')
@login_required
def admin_quotes():
    if current_user.role != 'admin': return redirect(url_for('index'))
    quotes = Quote.query.order_by(Quote.quote_date.desc()).all()
    return render_template('admin_quotes.html', quotes=quotes)

@app.route('/admin/quotes/new', methods=['GET', 'POST'])
@login_required
def admin_create_quote():
    if current_user.role != 'admin': return redirect(url_for('index'))
    form = QuoteForm()
    form.client.choices = [(u.id, u.profile.full_name or u.email) for u in User.query.filter_by(role='client').all()]

    if form.validate_on_submit():
        new_quote_number = get_next_quote_number()
        quote = Quote(
            quote_number=new_quote_number,
            user_id=form.client.data,
            quote_date=form.quote_date.data,
            expiry_date=form.expiry_date.data
        )
        db.session.add(quote)
        
        subtotal = 0
        for item_form in form.line_items.data:
            amount = item_form['quantity'] * item_form['unit_price']
            line_item = QuoteLineItem(
                quote=quote,
                description=item_form['description'],
                quantity=item_form['quantity'],
                unit_price=item_form['unit_price'],
                amount=amount
            )
            subtotal += amount
            db.session.add(line_item)
            
        quote.subtotal = subtotal
        quote.total = subtotal
        
        db.session.commit()
        flash(f'Quote {new_quote_number} created successfully.', 'success')
        return redirect(url_for('admin_quotes'))

    context = {
        'form': form,
        'title': 'Create New Quote',
        'back_url': url_for('admin_quotes'),
        'doc_type': 'Quote',
        'submit_text': 'Create Quote'
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

    form = QuoteForm(obj=quote)
    form.client.choices = [(u.id, u.profile.full_name or u.email) for u in User.query.filter_by(role='client').all()]

    if form.validate_on_submit():
        quote.user_id = form.client.data
        quote.quote_date = form.quote_date.data
        quote.expiry_date = form.expiry_date.data

        for item in quote.line_items:
            db.session.delete(item)

        subtotal = 0
        for item_data in form.line_items.data:
            amount = item_data['quantity'] * item_data['unit_price']
            line_item = QuoteLineItem(
                quote=quote,
                description=item_data['description'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                amount=amount
            )
            subtotal += amount
            db.session.add(line_item)
        
        quote.subtotal = subtotal
        quote.total = subtotal

        db.session.commit()
        flash(f'Quote {quote.quote_number} updated successfully.', 'success')
        return redirect(url_for('admin_quotes'))

    elif request.method == 'GET':
        form.client.data = quote.user_id

    context = {
        'form': form,
        'title': f'Edit Quote: {quote.quote_number}',
        'back_url': url_for('admin_quotes'),
        'doc_type': 'Quote',
        'submit_text': 'Save Changes'
    }
    return render_template('edit_quote.html', **context)

@app.route('/admin/quotes/delete/<int:quote_id>', methods=['POST'])
@login_required
def admin_delete_quote(quote_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    quote_to_delete = db.session.get(Quote, quote_id)
    if quote_to_delete:
        db.session.delete(quote_to_delete)
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

    rendered_template = render_template('quote_pdf_template.html', quote=quote)
    
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
    if not last_invoice:
        return "INV-0061"
    last_num = int(last_invoice.invoice_number.split('-')[1])
    new_num = last_num + 1
    return f"INV-{new_num:04d}"

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
    form.client.choices = [(u.id, u.profile.full_name or u.email) for u in User.query.filter_by(role='client').all()]

    if form.validate_on_submit():
        new_invoice_number = get_next_invoice_number()
        invoice = Invoice(
            invoice_number=new_invoice_number,
            user_id=form.client.data,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data
        )
        db.session.add(invoice)
        
        subtotal = 0
        for item_form in form.line_items.data:
            amount = item_form['quantity'] * item_form['unit_price']
            line_item = InvoiceLineItem(
                invoice=invoice,
                description=item_form['description'],
                quantity=item_form['quantity'],
                unit_price=item_form['unit_price'],
                amount=amount
            )
            subtotal += amount
            db.session.add(line_item)
            
        invoice.subtotal = subtotal
        invoice.total = subtotal
        
        db.session.commit()
        flash(f'Invoice {new_invoice_number} created successfully.', 'success')
        return redirect(url_for('admin_invoices'))

    context = {
        'form': form,
        'title': 'Create New Invoice',
        'back_url': url_for('admin_invoices'),
        'doc_type': 'Invoice',
        'submit_text': 'Create Invoice'
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
    return render_template('view_invoice.html', invoice=invoice)

@app.route('/admin/invoices/edit/<int:invoice_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_invoice(invoice_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        flash('Invoice not found.', 'error')
        return redirect(url_for('admin_invoices'))

    form = InvoiceForm(obj=invoice)
    form.client.choices = [(u.id, u.profile.full_name or u.email) for u in User.query.filter_by(role='client').all()]

    if form.validate_on_submit():
        invoice.user_id = form.client.data
        invoice.invoice_date = form.invoice_date.data
        invoice.due_date = form.due_date.data

        for item in invoice.line_items:
            db.session.delete(item)

        subtotal = 0
        for item_data in form.line_items.data:
            amount = item_data['quantity'] * item_data['unit_price']
            line_item = InvoiceLineItem(
                invoice=invoice,
                description=item_data['description'],
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                amount=amount
            )
            subtotal += amount
            db.session.add(line_item)
        
        invoice.subtotal = subtotal
        invoice.total = subtotal

        db.session.commit()
        flash(f'Invoice {invoice.invoice_number} updated successfully.', 'success')
        return redirect(url_for('admin_invoices'))

    elif request.method == 'GET':
        form.client.data = invoice.user_id

    context = {
        'form': form,
        'title': f'Edit Invoice: {invoice.invoice_number}',
        'back_url': url_for('admin_invoices'),
        'doc_type': 'Invoice',
        'submit_text': 'Save Changes'
    }
    return render_template('edit_invoice.html', **context)

@app.route('/admin/invoices/delete/<int:invoice_id>', methods=['POST'])
@login_required
def admin_delete_invoice(invoice_id):
    if current_user.role != 'admin': return redirect(url_for('index'))
    invoice_to_delete = db.session.get(Invoice, invoice_id)
    if invoice_to_delete:
        db.session.delete(invoice_to_delete)
        db.session.commit()
        flash(f'Invoice {invoice_to_delete.invoice_number} has been deleted.', 'success')
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

    rendered_template = render_template('invoice_pdf_template.html', invoice=invoice)
    pdf_result = BytesIO()
    pisa.CreatePDF(BytesIO(rendered_template.encode('UTF-8')), dest=pdf_result)
    pdf_result.seek(0)
    
    return Response(pdf_result.getvalue(),
                    mimetype='application/pdf',
                    headers={'Content-Disposition': f'attachment;filename=Invoice-{invoice.invoice_number}.pdf'})

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
def blog(): return render_template('blog.html')
@app.route('/faq')
def faq(): return render_template('faq.html')
@app.route('/gallery')
def gallery(): return render_template('gallery.html')

# --- API Routes ---
@app.route('/api/quote', methods=['POST'])
def api_quote():
    data = request.json or {}
    if current_user.is_authenticated:
        new_quote_request = QuoteRequest(
            property_type=data.get('property-type'),
            primary_service=data.get('primary-service'),
            service_frequency=data.get('service-frequency'),
            user_id=current_user.id
        )
        db.session.add(new_quote_request)
        db.session.commit()
    return jsonify({"status": "ok", "message": "Thank you! We've received your quote request."})

@app.route('/api/posts')
def api_posts():
    return jsonify([{"id": p["id"], "title": p["title"], "excerpt": p["excerpt"], "date": p["date"]} for p in BLOG_POSTS])

# --- CONTEXT PROCESSOR & MAIN EXECUTION ---
@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@example.com').first():
            admin_user = User(email='admin@example.com', role='admin')
            admin_user.set_password('password')
            db.session.add(admin_user)
            db.session.add(Profile(user=admin_user))
            db.session.commit()
            print("Default admin user created.")
    app.run(debug=True)