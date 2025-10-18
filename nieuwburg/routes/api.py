from flask import Blueprint, jsonify, request, current_app, flash
from flask_login import current_user, login_required
from datetime import datetime, time, timedelta, date
import json
import pytz
import uuid
from werkzeug.utils import secure_filename
import os
import requests

from .. import db
from ..models import (Post, ServiceCategory, ServiceItem, Job, User, Profile,
                     QuoteRequest, StaffApplication, SpecializedQuoteRequest, ActivityLog)
from .utils import log_activity, send_async_email

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/posts')
def posts():
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
    try:
        # A simple age calculation for the model
        id_number = request.form.get('id_number')
        age = 0
        if id_number and len(id_number) == 13:
            current_year = int(str(date.today().year)[2:])
            birth_year = int(id_number[:2])
            age = current_year - birth_year if current_year >= birth_year else (100 + current_year) - birth_year

        new_application = StaffApplication(
            full_name=request.form.get('full_name'),
            id_number=id_number,
            age=age,
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