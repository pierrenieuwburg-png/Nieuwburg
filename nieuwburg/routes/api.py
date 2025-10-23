from flask import Blueprint, jsonify, request, current_app, flash, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified
import secrets
import json
import requests
import pytz
import os
import uuid
import traceback
from werkzeug.utils import secure_filename
from datetime import date
from .. import db
from ..models import (Post, ServiceCategory, ServiceItem, Job, User, Profile,
                     QuoteRequest, StaffApplication, SpecializedQuoteRequest, ActivityLog, Invoice)
from ..forms import AddClientForm, AddStaffForm, EditStaffForm, EditClientForm
from .auth import generate_confirmation_token
from .. import mail
from flask_mail import Message
from .utils import log_activity, send_async_email # Keep existing utils import


bp = Blueprint('api', __name__, url_prefix='/api')

# --- Add Client API Route ---
@bp.route('/admin/clients', methods=['POST'])
@login_required
# @admin_required # Optional decorator
def api_add_client():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    data = request.json
    form = AddClientForm(data=data) # Use WTForms for validation

    if form.validate():
        # Check for existing email (form validator might do this, but double-check)
        if User.query.filter_by(email=form.email.data).first():
            return jsonify({'message': 'A user with this email already exists.'}), 400

        try:
            new_client = User(
                email=form.email.data,
                role='client',
                is_confirmed=True # Admins create confirmed clients
            )
            # Set a default secure password (user can reset later if needed)
            temp_password = secrets.token_urlsafe(12)
            new_client.set_password(temp_password)

            new_profile = Profile(
                user=new_client, # Associate profile with user
                full_name=form.full_name.data,
                phone_number=form.phone_number.data,
                address=form.address.data
            )

            db.session.add(new_client)
            # Ensure profile is added if not automatically cascaded
            # Check your User model's relationship for cascade settings
            # If unsure, adding explicitly is safer:
            db.session.add(new_profile)
            db.session.commit()

            log_activity('Client Created (API)', f"Admin '{current_user.email}' created client: {form.email.data}")

            # Return success message and potentially the new client's basic info
            return jsonify({
                'message': 'Client added successfully!',
                'client': { # Send back basic data to potentially update UI further if needed
                    'id': new_client.id,
                    'full_name': new_profile.full_name,
                    'email': new_client.email,
                    'phone_number': new_profile.phone_number, # Send back all relevant data
                    'address': new_profile.address,
                    #'view_url': url_for('admin.view_client', user_id=new_client.id) # Include view URL
                }
             }), 201 # 201 Created status

        except Exception as e:
            db.session.rollback()
            print(f"Error adding client via API: {e}") # Log the error server-side
            return jsonify({'message': 'Database error occurred.'}), 500

    else:
        # Collect validation errors
        errors = [f"{field}: {', '.join(error_list)}" for field, error_list in form.errors.items()]
        return jsonify({'message': f"Validation failed: {'; '.join(errors)}"}), 400
    
@bp.route('/admin/clients/<int:user_id>', methods=['PUT']) # Using PUT as it's an update
@login_required
def update_client_details(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    client = User.query.options(joinedload(User.profile)).filter(
        User.id == user_id, User.role == 'client'
    ).first()

    if not client or not client.profile:
        return jsonify({"message": "Client or profile not found"}), 404

    data = request.json
    if not data:
        return jsonify({"message": "No input data provided"}), 400

    # Use EditClientForm fields as a guide
    profile = client.profile
    profile.full_name = data.get('full_name', profile.full_name)
    profile.phone_number = data.get('phone_number', profile.phone_number)
    profile.address = data.get('address', profile.address)
    profile.service_frequency = data.get('service_frequency', profile.service_frequency)
    # Handle service_fee carefully - it might come as a string or number
    service_fee_input = data.get('service_fee', profile.service_fee)
    try:
         profile.service_fee = float(service_fee_input) if service_fee_input not in [None, ''] else None
    except (ValueError, TypeError):
         profile.service_fee = profile.service_fee # Keep old value on conversion error

    profile.notes = data.get('notes', profile.notes) # Assuming notes field

    try:
        db.session.commit()
        log_activity('Client Updated (API)', f"Admin '{current_user.email}' updated profile for {client.email}")

         # Fetch updated data to return
        updated_data = get_client_details(user_id).get_json()

        return jsonify({
            "message": "Client profile updated successfully.",
            "client": updated_data
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating client via API (User ID: {user_id}): {e}")
        return jsonify({'message': f'Database error occurred: {e}'}), 500
    
@bp.route('/admin/dashboard-stats', methods=['GET'])
@login_required
def get_dashboard_stats():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        today = date.today()
        # These queries match the logic previously in admin.py's dashboard route
        new_quotes_count = SpecializedQuoteRequest.query.filter_by(status='New').count() # Counts new specialized requests
        upcoming_cleans_count = Job.query.filter(
            Job.scheduled_date >= today,
            Job.status.in_(['Scheduled', 'In-Progress']) # Counts jobs scheduled for today or later that are not completed/cancelled
        ).count()
        active_clients_count = User.query.filter_by(role='client').count() # Counts all users with role 'client'
        staff_members_count = User.query.filter_by(role='staff').count() # Counts all users with role 'staff'

        stats_data = {
            "new_quotes_count": new_quotes_count,
            "upcoming_cleans_count": upcoming_cleans_count,
            "active_clients_count": active_clients_count,
            "staff_members_count": staff_members_count
        }
        return jsonify(stats_data)
    except Exception as e:
        print(f"Error fetching dashboard stats: {e}") # Log error server-side
        return jsonify({"message": "Error fetching dashboard statistics."}), 500
    
@bp.route('/admin/staff/<int:user_id>', methods=['GET'])
@login_required
def get_staff_details(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        # Fetch staff member with their profile data
        staff_member = User.query.options(joinedload(User.profile)).filter(
            User.id == user_id, User.role == 'staff'
        ).first()

        if not staff_member:
            return jsonify({"message": "Staff member not found"}), 404

        # Calculate age if date_of_birth exists
        age = None
        if staff_member.profile and staff_member.profile.date_of_birth:
            today = date.today()
            dob = staff_member.profile.date_of_birth
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        # Prepare profile data, handling potential None values
        profile_data = {}
        if staff_member.profile:
            profile_data = {
                "full_name": staff_member.profile.full_name or 'N/A',
                "phone_number": staff_member.profile.phone_number or 'N/A',
                "address": staff_member.profile.address or 'N/A',
                "profile_image": staff_member.profile.profile_image or 'avatar_picture_profile_user_icon.png',
                "id_number": staff_member.profile.id_number or 'N/A',
                "date_of_birth": staff_member.profile.date_of_birth.strftime('%d %B %Y') if staff_member.profile.date_of_birth else 'N/A',
                "age": age,
                "strengths": staff_member.profile.strengths or '',
                "notes": staff_member.profile.notes or '',
                "documents": staff_member.profile.documents or [], # Ensure it's a list
                "has_id_copy": staff_member.profile.has_id_copy or False,
                "has_drivers_license": staff_member.profile.has_drivers_license or False,
                "has_criminal_check": staff_member.profile.has_criminal_check or False,
                # Add banking details if needed later
            }
        else: # Default if profile is missing
             profile_data = {
                "full_name": 'N/A', "phone_number": 'N/A', "address": 'N/A', "profile_image": 'avatar_picture_profile_user_icon.png',
                "id_number": 'N/A', "date_of_birth": 'N/A', "age": None, "strengths": '', "notes": '', "documents": [],
                "has_id_copy": False, "has_drivers_license": False, "has_criminal_check": False
             }

        staff_data = {
            "id": staff_member.id,
            "email": staff_member.email,
            "profile": profile_data,
            # Add job history or other relevant data if needed
        }
        return jsonify(staff_data)

    except Exception as e:
        print(f"Error fetching staff details for ID {user_id}: {e}")
        return jsonify({"message": "Error fetching staff data."}), 500
    
@bp.route('/admin/staff/<int:user_id>', methods=['PUT', 'POST'])
@login_required
def update_staff_details(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    staff_member = User.query.options(joinedload(User.profile)).filter(
        User.id == user_id, User.role == 'staff'
    ).first()

    if not staff_member or not staff_member.profile:
        return jsonify({"message": "Staff member or profile not found"}), 404

    # Use request.form for text fields when using multipart/form-data
    # Use EditStaffForm fields as a guide for expected data
    profile = staff_member.profile
    profile.full_name = request.form.get('full_name', profile.full_name)
    profile.phone_number = request.form.get('phone_number', profile.phone_number)
    profile.address = request.form.get('address', profile.address)
    profile.id_number = request.form.get('id_number', profile.id_number)
    profile.strengths = request.form.get('strengths', profile.strengths)
    profile.notes = request.form.get('notes', profile.notes) # Assuming notes field exists

    # Handle boolean checkboxes (value will be 'true' or 'false' string from FormData)
    profile.has_id_copy = request.form.get('has_id_copy') == 'true'
    profile.has_drivers_license = request.form.get('has_drivers_license') == 'true'
    profile.has_criminal_check = request.form.get('has_criminal_check') == 'true'

    try:
        # --- Handle Profile Picture Upload ---
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                # Consider adding ALLOWED_EXTENSIONS check from config.py if needed
                filename = secure_filename(file.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                # TODO: Delete old profile image file if replacing
                file.save(upload_path)
                profile.profile_image = unique_filename
                print(f"Profile image saved to: {upload_path}")

        # --- Handle Document Uploads ---
        if 'upload_documents' in request.files:
            uploaded_files = request.files.getlist('upload_documents')
            new_filenames = []
            if profile.documents is None: # Initialize if null
                profile.documents = []

            for file in uploaded_files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + "_" + filename
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    new_filenames.append(unique_filename)

            if new_filenames:
                # Append new documents to existing list
                profile.documents.extend(new_filenames)
                flag_modified(profile, "documents") # Mark JSON field as modified for SQLAlchemy

        db.session.commit()
        log_activity('Staff Updated (API)', f"Admin '{current_user.email}' updated profile for {staff_member.email}")

        # Fetch updated data to return (optional but good for UI sync)
        updated_data = get_staff_details(user_id).get_json() # Reuse the GET endpoint logic

        return jsonify({
            "message": "Staff profile updated successfully.",
            "staffMember": updated_data # Return updated data
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error updating staff via API (User ID: {user_id}): {e}")
        return jsonify({'message': f'Database error occurred: {e}'}), 500

@bp.route('/admin/staff', methods=['POST'])
@login_required
def api_add_staff():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    data = request.json
    form = AddStaffForm(data=data) # Use WTForms for validation
    
    # ** Get the new checkbox value from the JSON payload **
    send_email = data.get('send_activation_email', False) # Default to False if not provided

    if form.validate():
        if User.query.filter_by(email=form.email.data).first():
            return jsonify({'message': 'A user with this email already exists.'}), 400

        try:
            new_staff = User(
                email=form.email.data,
                role='staff',
                is_confirmed=True,
                password_reset_required=True # They will need to set password
            )
            
            new_profile = Profile(
                user=new_staff,
                full_name=form.full_name.data,
                phone_number=form.phone_number.data,
                address=form.address.data,
                id_number=form.id_number.data
            )

            db.session.add(new_staff)
            db.session.add(new_profile)
            db.session.commit()

            log_activity('Staff Created (API)', f"Admin '{current_user.email}' created staff: {form.email.data}")

            success_message = f"Staff member '{form.full_name.data}' created."

            # ** Conditionally send the email **
            if send_email:
                try:
                    token = generate_confirmation_token(new_staff.id) 
                    activation_url = url_for('auth.staff_activate_token', token=token, _external=True)
                    msg = Message(subject="[Nieuwburg Blitz] Activate Your Staff Account",
                                  sender=current_app.config['MAIL_USERNAME'],
                                  recipients=[new_staff.email])
                    msg.body = f"Welcome! An account has been created for you. Please click this link to set your password: {activation_url}"
                    send_async_email(current_app._get_current_object(), msg)
                    success_message += " An activation email has been sent."
                except Exception as e:
                    print(f"Failed to send activation email for {new_staff.email}: {e}")
                    success_message += " Email sending failed."
            else:
                success_message += " No activation email was sent."

            return jsonify({'message': success_message}), 201

        except Exception as e:
            db.session.rollback()
            print(f"Error adding staff via API: {e}")
            return jsonify({'message': 'Database error occurred.'}), 500

    else:
        errors = [f"{field}: {', '.join(error_list)}" for field, error_list in form.errors.items()]
        return jsonify({'message': f"Validation failed: {'; '.join(errors)}"}), 400

@bp.route('/posts')
def posts():
    # ... (posts implementation) ...
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_date.desc()).limit(3).all()
    posts_data = [{
        "id": post.id,
        "title": post.title,
        "excerpt": post.excerpt or (post.content[:150] + '...'),
        "date": post.created_date.strftime('%d %B %Y')
    } for post in posts]
    return jsonify(posts_data)


@bp.route('/services')
def services():
    # ... (services implementation) ...
    categories = ServiceCategory.query.options(db.joinedload(ServiceCategory.items).joinedload(ServiceItem.prices)).order_by(ServiceCategory.name).all()
    output = []
    for category in categories:
        cat_data = {
            'id': category.id, 'name': category.name, 'description': category.description,
            'calculation_method': category.calculation_method, 'items': []
        }
        for item in category.items:
            item_data = {
                'id': item.id, 'name': item.name, 'estimated_time_mins': item.estimated_time_mins,
                'prices': [{'frequency': p.frequency, 'price': p.price} for p in item.prices]
            }
            cat_data['items'].append(item_data)
        output.append(cat_data)
    return jsonify(output)


@bp.route('/availability/<string:date_str>')
def availability(date_str):
    # ... (availability implementation) ...
    from datetime import time, timedelta # Added for clarity, though it might be covered by imports above
    try:
        booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

    opening_time = time(8, 0)
    closing_time = time(17, 0)
    slot_interval_mins = 30
    
    existing_jobs_on_day = Job.query.filter(Job.scheduled_date == booking_date).all()
    
    available_slots = []
    current_time_dt = datetime.combine(booking_date, opening_time)
    end_of_day_dt = datetime.combine(booking_date, closing_time)

    while current_time_dt < end_of_day_dt:
        slot_is_available = True
        for job in existing_jobs_on_day:
            if job.start_time and current_time_dt.time() == job.start_time:
                slot_is_available = False
                break
        
        if slot_is_available:
            available_slots.append(current_time_dt.strftime('%H:%M'))

        current_time_dt += timedelta(minutes=slot_interval_mins)

    return jsonify(available_slots)


@bp.route('/recent-activity')
@login_required
def recent_activity():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403

    logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(5).all()
    sast_timezone = pytz.timezone('Africa/Johannesburg')

    recent_logs = [{
        'timestamp': pytz.utc.localize(log.timestamp).astimezone(sast_timezone).strftime('%d %b, %H:%M'),
        'description': log.description,
        'user_email': log.user.email if log.user else 'System'
    } for log in logs]
    
    return jsonify(recent_logs)


@bp.route('/contact', methods=['POST'])
def contact():
    # ... (contact implementation) ...
    data = request.json
    try:
        new_request = SpecializedQuoteRequest(
            name=data.get('name'), email=data.get('email'), phone=data.get('phone'), 
            area=data.get('area'), message=data.get('message')
        )
        db.session.add(new_request)
        db.session.commit()
        log_activity("Specialized Request", f"New site contact form submission from {data.get('name')}.")
        # Email sending logic would go here
        return jsonify({"status": "ok", "message": "Thank you! Your request has been sent."})
    except Exception as e:
        db.session.rollback()
        print(f"API Contact Error: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500


@bp.route('/staff_apply', methods=['POST'])
def staff_apply():
    # ... (staff_apply implementation) ...
    import os
    import uuid
    from datetime import date # Already imported
    from werkzeug.utils import secure_filename # Already imported
    
    try:
        id_number = request.form.get('id_number')
        age = 0 # Placeholder if ID number isn't valid/provided
        if id_number and len(id_number) == 13:
            try: # Add error handling for year calculation
                current_year = int(str(date.today().year)[2:])
                birth_year = int(id_number[:2])
                # Basic age calc - might be off by 1 year depending on month/day
                age = current_year - birth_year if current_year >= birth_year else (100 + current_year) - birth_year
            except ValueError:
                age = 0 # Default if ID parsing fails

        new_application = StaffApplication(
            full_name=request.form.get('full_name'),
            id_number=id_number, # Store ID number regardless of age calc
            # age=age, # Storing age might not be necessary if DOB is captured later
            phone_number=request.form.get('phone_number'),
            email=request.form.get('email'),
            address=request.form.get('address')
        )

        uploaded_filenames = []
        files = request.files.getlist('documents')
        if files:
            for file in files:
                if file and file.filename != '':
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + "_" + filename
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename))
                    uploaded_filenames.append(unique_filename)
        
        if uploaded_filenames:
            new_application.document_filenames = uploaded_filenames

        db.session.add(new_application)
        db.session.commit()
        log_activity("Staff Application", f"New staff application from {request.form.get('full_name')}.")
        # Email notification logic would go here
        return jsonify({"status": "ok", "message": "Application submitted successfully."})
    except Exception as e:
        db.session.rollback()
        print(f"API Staff Apply Error: {e}")
        return jsonify({"status": "error", "message": "An unexpected error occurred."}), 500


@bp.route('/quote', methods=['POST'])
@login_required
def quote():
    # ... (quote implementation) ...
    data = request.json or {}
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

@bp.route('/admin/jobs/current', methods=['GET'])
@login_required
def get_current_jobs():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        # Fetch jobs that are scheduled or in progress
        # Eagerly load related data for efficiency
        current_jobs = Job.query.options(
            joinedload(Job.quote_request).joinedload(QuoteRequest.user).joinedload(User.profile),
            joinedload(Job.assigned_staff).joinedload(User.profile) # Also load staff profiles
        ).filter(
            Job.status.in_(['Scheduled', 'In-Progress'])
        ).order_by(Job.scheduled_date.asc(), Job.start_time.asc()).all()

        jobs_data = []
        for job in current_jobs:
            client_name = "N/A",
            primary_service = "N/A"
            if job.quote_request and job.quote_request.user:
                client_name = job.quote_request.user.profile.full_name or job.quote_request.user.email if job.quote_request.user.profile else job.quote_request.user.email
                primary_service = job.quote_request.primary_service or "N/A"

            assigned_staff_names = [
                staff.profile.full_name or staff.email
                for staff in job.assigned_staff if staff.profile
            ] or ["None"] # Use ["None"] if list is empty

            jobs_data.append({
                "id": job.id,
                "scheduled_date": job.scheduled_date.strftime('%d %b %Y') if job.scheduled_date else 'N/A',
                "scheduled_date_iso": job.scheduled_date.isoformat() if job.scheduled_date else None, # <-- ADD THIS LINE
                "start_time": job.start_time.strftime('%H:%M') if job.start_time else '--:--',
                "client_name": client_name,
                "service": primary_service,
                "status": job.status,
                "assigned_staff": ", ".join(assigned_staff_names)
            })
        return jsonify(jobs_data)

    except Exception as e:
        print(f"Error fetching current jobs: {e}")
        return jsonify({"message": "Error fetching current job data."}), 500

# --- NEW: API Endpoint for New Confirmed Bookings ---
@bp.route('/admin/bookings/new', methods=['GET'])
@login_required
def get_new_bookings():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        # Fetch QuoteRequests with status 'Confirmed'
        new_bookings = QuoteRequest.query.options(
            joinedload(QuoteRequest.user).joinedload(User.profile)
        ).filter(
            QuoteRequest.status == 'Confirmed'
        ).order_by(QuoteRequest.request_date.desc()).all()

        bookings_data = []
        for req in new_bookings:
            client_name = "N/A"
            client_phone = "No phone"
            if req.user:
                 client_name = req.user.profile.full_name or req.user.email if req.user.profile else req.user.email
                 client_phone = req.user.profile.phone_number or "No phone" if req.user.profile else "No phone"


            bookings_data.append({
                "id": req.id,
                "request_date": req.request_date.strftime('%d %b %Y, %H:%M') if req.request_date else 'N/A',
                "client_name": client_name,
                "client_phone": client_phone,
                "service": req.primary_service or "N/A",
                "property_type": req.property_type or "N/A",
                "address": req.address or "N/A", # Assuming address might be added to QuoteRequest
                "total_price": req.total_price if req.total_price is not None else 'N/A',
                "user_id": req.user_id # Include user_id if needed for links
            })
        return jsonify(bookings_data)
    except Exception as e:
        print(f"Error fetching new bookings: {e}")
        return jsonify({"message": "Error fetching new booking data."}), 500

# --- NEW: API Endpoint for All Quote Requests ---
@bp.route('/admin/quotes', methods=['GET'])
@login_required
def get_all_quotes():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        # Fetch all QuoteRequests, ordered by request date descending
        # Eagerly load related user and profile data
        quotes = QuoteRequest.query.options(
            joinedload(QuoteRequest.user).joinedload(User.profile)
        ).order_by(QuoteRequest.request_date.desc()).all()

        quotes_data = []
        for req in quotes:
            client_name = "N/A"
            client_phone = "N/A"
            if req.user:
                 client_name = req.user.profile.full_name or req.user.email if req.user.profile else req.user.email
                 client_phone = req.user.profile.phone_number or "N/A" if req.user.profile else "N/A"

            quotes_data.append({
                "id": req.id,
                "request_date": req.request_date.strftime('%d %b %Y, %H:%M') if req.request_date else 'N/A',
                "client_name": client_name,
                "client_phone": client_phone,
                "service": req.primary_service or "N/A",
                "property_type": req.property_type or "N/A",
                "frequency": req.service_frequency or "N/A", # Assuming service_frequency field exists
                "address": req.address or "N/A",
                "total_price": req.total_price if req.total_price is not None else None, # Return as number or null
                "status": req.status or "Unknown",
                "user_id": req.user_id # Include user_id if needed for links
            })
        return jsonify(quotes_data)
    except Exception as e:
        print(f"Error fetching all quotes: {e}") # Log the error
        return jsonify({"message": "Error fetching quote data."}), 500
    
# --- NEW: API Endpoint for All Invoices ---
@bp.route('/admin/invoices', methods=['GET'])
@login_required
def get_all_invoices():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        # Fetch all Invoices, ordered by issue date descending
        # Eagerly load related user and profile data via the client relationship
        # Assuming Invoice model has a relationship like client = db.relationship('User', backref='invoices')
        invoices = Invoice.query.options(
            joinedload(Invoice.client).joinedload(User.profile)
        ).order_by(Invoice.invoice_date.desc()).all()

        invoices_data = []
        for inv in invoices:
            client_name = "N/A"
            if inv.client:
                 client_name = inv.client.profile.full_name or inv.client.email if inv.client.profile else inv.client.email

            invoices_data.append({
                "id": inv.id,
                "invoice_number": inv.invoice_number or f"INV-{inv.id}", # Generate if missing
                "client_name": client_name,
                "client_id": inv.client_id,
                "issue_date": inv.invoice_date.strftime('%d %b %Y') if inv.invoice_date else 'N/A',
                "due_date": inv.due_date.strftime('%d %b %Y') if inv.due_date else 'N/A',
                "total_amount": inv.total_amount if inv.total_amount is not None else None, # Return as number or null
                "status": inv.status or "Unknown" # e.g., 'Paid', 'Unpaid', 'Overdue'
            })
        return jsonify(invoices_data)
    except Exception as e:
    # Print the exception AND the full traceback
        print(f"Error fetching all invoices: {e}") 
    traceback.print_exc() # <--- ADD THIS LINE
    return jsonify({"message": "Error fetching invoice data."}), 500

@bp.route('/create_booking', methods=['POST'])
def create_booking():
    # ... (create_booking implementation) ...
    data = request.json
    try:
        customer_email = data.get('email')
        customer_name = data.get('name')
        
        user = User.query.filter_by(email=customer_email).first()
        if not user:
            guest_password = str(uuid.uuid4())
            user = User(email=customer_email, role='client')
            user.set_password(guest_password)
            db.session.add(user)
            profile = Profile(user=user, full_name=customer_name, phone_number=data.get('phone'), address=data.get('address'))
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

        return jsonify({'status': 'ok', 'message': 'Booking request received.', 'booking_id': new_request.id})
    except Exception as e:
        db.session.rollback()
        print(f"Error creating booking request: {e}")
        return jsonify({'status': 'error', 'message': 'Could not process your booking request.'}), 500


@bp.route('/initialize-payment', methods=['POST'])
def initialize_payment():
    # ... (initialize_payment implementation) ...
    import os # Added for clarity
    
    try:
        data = request.json
        payload = {
            "email": data.get('email'),
            "amount": int(float(data.get('totalPrice')) * 100),
            "currency": "ZAR",
            "metadata": {"booking_details": data}
        }
        headers = {
            "Authorization": f"Bearer {os.environ.get('PAYSTACK_SECRET_KEY')}",
            "Content-Type": "application/json"
        }
        response = requests.post("https://api.paystack.co/transaction/initialize", headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        if response_data.get('status'):
            return jsonify(response_data['data'])
        else:
            return jsonify({'error': 'Could not initialize payment with provider.'}), 400
    except Exception as e:
        return jsonify({'error': f'An internal server error occurred: {e}'}), 500
    
@bp.route('/admin/clients/<int:user_id>', methods=['GET'])
@login_required
def get_client_details(user_id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        # Fetch client with their profile data efficiently
        client = User.query.options(joinedload(User.profile)).filter(
            User.id == user_id, User.role == 'client'
        ).first()

        if not client:
            return jsonify({"message": "Client not found"}), 404

        # Prepare profile data, handling potential None values
        profile_data = {}
        if client.profile:
            profile_data = {
                "full_name": client.profile.full_name or 'N/A',
                "phone_number": client.profile.phone_number or 'N/A',
                "address": client.profile.address or 'N/A',
                "service_frequency": client.profile.service_frequency or 'N/A',
                "service_fee": client.profile.service_fee, # Keep as number or None
                "notes": client.profile.notes or '' # Default to empty string
            }
        else: # Handle case where profile might somehow be missing
             profile_data = {
                "full_name": 'N/A', "phone_number": 'N/A', "address": 'N/A',
                "service_frequency": 'N/A', "service_fee": None, "notes": ''
             }


        # Optional: Fetch related data like booking history (simplified example)
        # You might want more details or pagination for a large history
        bookings = QuoteRequest.query.filter_by(user_id=client.id).order_by(QuoteRequest.request_date.desc()).limit(10).all()
        booking_history = [{
            "id": b.id,
            "request_date": b.request_date.strftime('%d %b %Y') if b.request_date else 'N/A',
            "primary_service": b.primary_service or 'N/A',
            "status": b.status or 'Unknown',
            "property_type": b.property_type or 'N/A',
            "service_frequency": b.service_frequency or 'N/A' # Different from profile frequency
        } for b in bookings]

        client_data = {
            "id": client.id,
            "email": client.email,
            "profile": profile_data,
            "booking_history": booking_history # Add booking history
        }
        return jsonify(client_data)

    except Exception as e:
        print(f"Error fetching client details for ID {user_id}: {e}")
        return jsonify({"message": "Error fetching client data."}), 500

@bp.route('/admin/clients/search')
@login_required
def search_clients():
    # ... (search_clients implementation) ...
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403

    query = request.args.get('q', '').strip().lower()
    clients_query = User.query.outerjoin(User.profile).filter(User.role == 'client')

    if query:
        search_term = f"%{query}%"
        clients_query = clients_query.filter(
            or_(
                User.email.ilike(search_term),
                Profile.full_name.ilike(search_term)
            )
        )

    clients = clients_query.order_by(Profile.full_name, User.email).all()
    clients_data = []
    for client in clients:
        full_name = client.profile.full_name if client.profile else 'N/A'
        phone_number = client.profile.phone_number if client.profile else 'N/A'
        address = client.profile.address if client.profile else 'N/A'
        clients_data.append({
            "id": client.id,
            "full_name": full_name,
            "email": client.email,
            "phone_number": phone_number,
            "address": address,
            #"view_url": url_for('admin.view_client', user_id=client.id)
        })
    return jsonify(clients_data)

@bp.route('/admin/staff/search')
@login_required
def search_staff():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"error": "Permission denied"}), 403

    query = request.args.get('q', '').strip().lower()
    staff_query = User.query.outerjoin(User.profile).filter(User.role == 'staff')

    if query:
        search_term = f"%{query}%"
        staff_query = staff_query.filter(
            or_(
                User.email.ilike(search_term),
                Profile.full_name.ilike(search_term)
            )
        )

    staff_list = staff_query.order_by(Profile.full_name, User.email).all()

    staff_data = []
    for staff in staff_list:
        age = None
        if staff.profile and staff.profile.date_of_birth:
            today = date.today()
            age = today.year - staff.profile.date_of_birth.year - ((today.month, today.day) < (staff.profile.date_of_birth.month, staff.profile.date_of_birth.day))
        
        staff_data.append({
            "id": staff.id,
            "full_name": staff.profile.full_name if staff.profile else 'N/A',
            "email": staff.email,
            "phone_number": staff.profile.phone_number if staff.profile else 'N/A',
            "profile_image": staff.profile.profile_image if staff.profile else None,
            "age": age,
            #"view_url": url_for('admin.view_staff', user_id=staff.id)
        })

    return jsonify(staff_data)

@bp.route('/admin/applications', methods=['GET'])
@login_required
def get_staff_applications():
    if not current_user.is_authenticated or current_user.role != 'admin':
        return jsonify({"message": "Permission denied"}), 403

    try:
        applications = StaffApplication.query.order_by(StaffApplication.submission_date.desc()).all()
        apps_data = []
        for app in applications:
            apps_data.append({
                "id": app.id,
                "submission_date": app.submission_date.strftime('%d %b %Y, %H:%M') if app.submission_date else 'N/A', # Format date
                "full_name": app.full_name,
                "id_number": app.id_number or 'N/A',
                "email": app.email,
                "phone_number": app.phone_number,
                "document_filenames": app.document_filenames or [] # Return list or empty list
            })
        return jsonify(apps_data)
    except Exception as e:
        print(f"Error fetching staff applications: {e}")
        return jsonify({"message": "Error fetching application data."}), 500