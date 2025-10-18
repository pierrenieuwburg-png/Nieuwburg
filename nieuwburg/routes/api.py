from flask import Blueprint, jsonify, request, current_app, flash, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_ 
import secrets
from .. import db
from ..models import (Post, ServiceCategory, ServiceItem, Job, User, Profile,
                     QuoteRequest, StaffApplication, SpecializedQuoteRequest, ActivityLog)
from ..forms import AddClientForm, AddStaffForm
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
                    'view_url': url_for('admin.view_client', user_id=new_client.id) # Include view URL
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
    # ... (recent_activity implementation) ...
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
            "view_url": url_for('admin.view_client', user_id=client.id)
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
            "view_url": url_for('admin.view_staff', user_id=staff.id)
        })

    return jsonify(staff_data)