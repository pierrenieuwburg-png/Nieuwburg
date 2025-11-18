import os
import uuid
from threading import Thread
from flask import Blueprint, render_template, redirect, url_for, flash, request, session as flask_session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

from .. import db, mail, oauth
from ..models import User, Profile, Tenant
from ..forms import LoginForm, RegistrationForm, RequestPasswordResetForm, ResetPasswordForm, ChangePasswordForm, UpdateProfileForm
from flask_mail import Message

bp = Blueprint('auth', __name__, url_prefix='/auth')

# --- Helper Functions ---

def generate_confirmation_token(email_or_id):
    """Generates a secure, timed token."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email_or_id, salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'my_precious_salt'))

def confirm_token(token, expiration=3600):
    """Confirms a token and returns the original data if valid."""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        data = serializer.loads(
            token,
            salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'my_precious_salt'),
            max_age=expiration
        )
    except:
        return False
    return data

def send_async_email(app, msg):
    """Sends email in a background thread."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"--- [EMAIL FAILED] ---: {e}")


# --- Standard Authentication Routes ---

@bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if user:
            # Check for account lock, confirmation, password (as before)
            if user.locked_until and user.locked_until > datetime.utcnow():
                time_remaining = user.locked_until - datetime.utcnow()
                minutes_remaining = (time_remaining.total_seconds() + 59) // 60
                message = f"Account locked. Try again in {int(minutes_remaining)} minutes."
                if is_ajax: return jsonify({'status': 'locked', 'message': message}), 403
                flash(message, 'error')
                return redirect(url_for('main.index'))

            if not user.is_confirmed and user.role == 'client':
                message = 'Please confirm your email address before logging in.'
                if is_ajax: return jsonify({'status': 'unconfirmed', 'message': message, 'email': user.email}), 401
                flash(message, 'warning')
                return redirect(url_for('main.index', action='login_from_redirect'))
            
            if not user.check_password(form.password.data):
                user.failed_login_attempts += 1
                user.last_failed_login = datetime.utcnow()
                if user.failed_login_attempts >= 10:
                    user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                    user.failed_login_attempts = 0
                db.session.commit()
                message = 'Invalid email or password.'
                if is_ajax: return jsonify({'status': 'error', 'message': message}), 401
                flash(message, 'error')
                return redirect(url_for('main.index'))

            # Successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            
            redirect_url = url_for('main.client_dashboard')
            if user.role == 'admin': redirect_url = url_for('admin.admin_spa_shell')
            elif user.role == 'staff': redirect_url = url_for('main.staff_dashboard')
            
            if is_ajax: return jsonify({'status': 'ok', 'redirect': redirect_url})
            return redirect(redirect_url)

    message = 'Invalid email or password.'
    if is_ajax: return jsonify({'status': 'error', 'message': message}), 401
    flash(message, 'error')
    return redirect(url_for('main.index'))


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if form.validate_on_submit():
        # Registration logic (as before)...
        if User.query.filter_by(email=form.email.data).first():
            message = 'An account with this email address already exists.'
            if is_ajax: return jsonify({'status': 'error', 'message': message}), 400
            flash(message, 'error')
            return redirect(url_for('main.index'))

        new_user = User(email=form.email.data, role='client', is_confirmed=False)
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.add(Profile(user=new_user)) # Add profile creation here

        token = generate_confirmation_token(new_user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        logo_url = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
        html = render_template('email/activate.html', confirm_url=confirm_url, logo_url=logo_url)
        
        try:
            msg = Message(subject="[Nieuwburg Blitz] Please confirm your email",
                          sender=current_app.config['MAIL_USERNAME'],
                          recipients=[new_user.email],
                          html=html)
            send_async_email(current_app._get_current_object(), msg)
            db.session.commit() # Commit after potential email success
            message = 'Registration successful! A confirmation email has been sent.'
            if is_ajax: return jsonify({'status': 'ok', 'message': message})
            flash(message, 'success')
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            print(f"CRITICAL: Email sending failed during registration: {e}")
            message = 'Could not send confirmation email. Please try again later.'
            if is_ajax: return jsonify({'status': 'error', 'message': message}), 500
            flash(message, 'error')
            return redirect(url_for('main.index'))

    if is_ajax and form.errors:
        first_error_field = next(iter(form.errors))
        first_error_message = form.errors[first_error_field][0]
        return jsonify({'status': 'error', 'message': first_error_message}), 400
    
    # If not AJAX or validation fails on non-AJAX, redirect back to index (where modal lives)
    flash('Registration failed. Please check the form.', 'error') # Consider flashing specific errors if needed
    return redirect(url_for('main.index'))


# --- Confirmation & Password Reset ---

@bp.route('/confirm/<token>')
def confirm_email(token):
    email = confirm_token(token) # Using the local function from your file
    if not email:
        flash('The confirmation link is invalid or has expired.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.filter_by(email=email).first_or_404()
    
    if user.is_confirmed:
        flash('Account already confirmed. Please log in.', 'success')
    else:
        # Activate the user
        user.is_confirmed = True
        user.confirmed_on = datetime.utcnow()
        
        # --- NEW LOGIC for SaaS Admins ---
        if user.role == 'admin' and user.tenant_id:
            tenant = Tenant.query.get(user.tenant_id)
            if tenant:
                tenant.is_active = True # Activate the business
                flash(f'Welcome! Your account and business "{tenant.business_name}" are now active.', 'success')
            else:
                flash('Welcome! Your account is active, but we had trouble finding your business. Please contact support.', 'warning')
        else:
            # Original logic for regular clients
            flash('Welcome! Your account is confirmed.', 'success')
        # --- END NEW LOGIC ---
            
        db.session.commit()
    
    login_user(user)
    
    # --- NEW REDIRECT LOGIC ---
    if user.role == 'admin' and user.tenant_id:
        # This is the new SaaS user, send them to the setup wizard.
        # We will create this 'admin.setup_wizard' route in the very next step.
        return redirect(url_for('admin.admin_spa_shell', path='setup-wizard'))
    elif user.role == 'staff':
        # Staff go to their dashboard
        return redirect(url_for('main.staff_dashboard'))
    else:
        # Existing clients go to their original dashboard
        return redirect(url_for('main.client_dashboard'))

@bp.route('/resend-confirmation/<email>')
def resend_confirmation(email):
    # Resend logic (as before)...
    user = User.query.filter_by(email=email).first()
    if user and not user.is_confirmed:
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        logo_url = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
        html = render_template('email/activate.html', confirm_url=confirm_url, logo_url=logo_url)
        msg = Message(subject="[Nieuwburg Blitz] Confirm Your Email (Resent)",
                      sender=current_app.config['MAIL_USERNAME'], recipients=[user.email], html=html)
        send_async_email(current_app._get_current_object(), msg)
        flash('A new confirmation email has been sent.', 'success')
    elif user and user.is_confirmed:
        flash('This account is already confirmed. Please log in.', 'info')
    else:
        flash('Could not find an account with that email.', 'error')
    return redirect(url_for('main.index', action='login_from_redirect'))


@bp.route('/request-password-reset', methods=['GET', 'POST'])
def request_password_reset():
    # Request reset logic (as before)...
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_confirmation_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            logo_url = url_for('static', filename='img/LogoBlackWithTitle.png', _external=True)
            html = render_template('email/reset_password.html', reset_url=reset_url, logo_url=logo_url)
            msg = Message(subject="[Nieuwburg Blitz] Password Reset",
                          sender=current_app.config['MAIL_USERNAME'], recipients=[user.email], html=html)
            send_async_email(current_app._get_current_object(), msg)
        flash('If an account with that email exists, reset instructions have been sent.', 'info')
        return redirect(url_for('main.index'))
    return render_template('auth/request_password_reset.html', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Reset password logic (as before)...
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    email = confirm_token(token, expiration=3600)
    if not email:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.request_password_reset'))
    
    user = User.query.filter_by(email=email).first_or_404()
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_required = False # Ensure this flag is reset
        db.session.commit()
        login_user(user)
        flash('Your password has been updated and you are now logged in!', 'success')
        return redirect(url_for('main.client_dashboard'))
    return render_template('auth/reset_password.html', form=form)


# --- Profile Management ---

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    # Pass current profile data to form for initial display on GET
    form = UpdateProfileForm(obj=current_user.profile)

    if form.validate_on_submit(): # Runs on POST
        user_profile = current_user.profile

        # ** CORRECTED FILE HANDLING **
        # Explicitly check request.files for the uploaded image
        uploaded_file = request.files.get(form.profile_image.name) # Get file using the form field name

        if uploaded_file and uploaded_file.filename != '':
            # Process the uploaded file
            filename = secure_filename(uploaded_file.filename)
            unique_filename = str(uuid.uuid4()) + "_" + filename
            try:
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                uploaded_file.save(upload_path)
                user_profile.profile_image = unique_filename
                print(f"Image saved to: {upload_path}") # Debug print
            except Exception as e:
                print(f"Error saving file: {e}") # Debug print for save errors
                flash('There was an error uploading the image.', 'error')
                # Decide if you want to redirect or render again on error
                return redirect(url_for('auth.profile'))
        # If no new file was uploaded, we simply don't update the profile_image field

        # Update other fields from the form
        user_profile.full_name = form.full_name.data
        user_profile.phone_number = form.phone_number.data
        user_profile.address = form.address.data
        
        try:
            db.session.commit()
            flash('Your profile has been updated.', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error committing profile update: {e}") # Debug print for DB errors
            flash('An error occurred while updating your profile.', 'error')
        
        return redirect(url_for('auth.profile'))
        
    # On GET request or if form validation fails, render the template
    return render_template('client/profile.html', form=form, user_profile=current_user.profile)


@bp.route('/remove-picture', methods=['POST'])
@login_required
def remove_profile_picture():
    current_user.profile.profile_image = 'avatar_picture_profile_user_icon.png'
    db.session.commit()
    flash('Your profile picture has been removed.', 'success')
    return redirect(url_for('auth.profile'))

@bp.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    user_to_delete = db.session.get(User, current_user.id)
    if user_to_delete:
        db.session.delete(user_to_delete)
        db.session.commit()
    logout_user()
    return jsonify({'status': 'ok', 'message': 'Account deleted successfully.'})

# --- Google OAuth Routes ---

@bp.route('/login/google')
def google_login():
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                email=user_info['email'],
                role='client',
                is_confirmed=True, # Google accounts are considered confirmed
                confirmed_on=datetime.utcnow()
            )
            db.session.add(user)
            # Ensure profile exists
            if not user.profile:
                 db.session.add(Profile(user=user, full_name=user_info.get('name')))
            else:
                 if not user.profile.full_name: # Only set name if not already set
                     user.profile.full_name=user_info.get('name')
            db.session.commit()
        
        login_user(user)
        flash('You have been successfully logged in with Google.', 'success')
        return redirect(url_for('main.client_dashboard'))

    flash('Google login failed. Please try again.', 'error')
    return redirect(url_for('main.index'))

@bp.route('/staff-activate/<token>', methods=['GET', 'POST'])
def staff_activate_token(token):
    try:
        user_id = confirm_token(token, expiration=86400) # 24 hours
    except:
        flash('The activation link is invalid or has expired.', 'error')
        return redirect(url_for('main.index'))

    user = db.session.get(User, user_id)

    if not user or user.role != 'staff':
        flash('Invalid user.', 'error')
        return redirect(url_for('main.index'))
        
    # Check if password already set (prevents reusing link)
    if not user.password_reset_required and user.password_hash:
        flash('This activation link has already been used.', 'warning')
        return redirect(url_for('main.index'))


    form = ChangePasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_required = False
        db.session.commit()
        login_user(user)
        flash('Your password has been set. Welcome to the team!', 'success')
        return redirect(url_for('main.staff_dashboard'))

    return render_template('staff/staff_set_password.html', form=form)