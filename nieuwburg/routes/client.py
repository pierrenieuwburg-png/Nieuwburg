from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from sqlalchemy import or_, desc
from sqlalchemy.orm import joinedload
from ..models import User, QuoteRequest, Quote, Invoice, Job, Profile
from .. import db
from datetime import datetime

bp = Blueprint('client', __name__, url_prefix='/client')

def check_client_access():
    """Helper to ensure the user is authenticated and is a client."""
    if not current_user.is_authenticated or current_user.role != 'client':
        return False
    return True

# ==========================================
#               CLIENT SPA SHELL
# ==========================================

@bp.route('/', defaults={'path': ''})
@bp.route('/<path:path>')
@login_required
def client_spa_shell(path):
    """
    Serves the Client Portal React App.
    Note: This assumes you will use the same App.jsx but route to /client/...
    """
    if not check_client_access():
        return render_template('errors/403.html'), 403
    return render_template('client/client_dashboard.html', user=current_user)

# ==========================================
#               CLIENT API
# ==========================================

@bp.route('/api/dashboard', methods=['GET'])
@login_required
def get_client_dashboard():
    if not check_client_access(): return jsonify({"message": "Unauthorized"}), 403

    # 1. Pending Quotes (Requests or Formal Drafts awaiting approval)
    pending_requests = QuoteRequest.query.filter_by(user_id=current_user.id, status='Pending').count()
    pending_formal = Quote.query.filter_by(user_id=current_user.id, status='Sent').count()
    
    # 2. Unpaid Invoices
    unpaid_invoices = Invoice.query.filter_by(user_id=current_user.id, status='Unpaid').count()

    # 3. Upcoming Jobs
    upcoming_jobs = Job.query.filter(
        Job.client_id == current_user.id,
        Job.status.in_(['Scheduled', 'En Route', 'In Progress'])
    ).count()

    return jsonify({
        "stats": {
            "pending_quotes": pending_requests + pending_formal,
            "unpaid_invoices": unpaid_invoices,
            "upcoming_jobs": upcoming_jobs
        },
        "profile": {
            "name": current_user.profile.full_name if current_user.profile else current_user.email,
            "address": current_user.profile.address if current_user.profile else ""
        }
    })

@bp.route('/api/my-quotes', methods=['GET'])
@login_required
def get_my_quotes():
    if not check_client_access(): return jsonify({"message": "Unauthorized"}), 403

    # 1. Fetch Requests (Leads)
    requests = QuoteRequest.query.filter_by(user_id=current_user.id).order_by(QuoteRequest.request_date.desc()).all()
    
    # 2. Fetch Formal Quotes
    formal_quotes = Quote.query.filter_by(user_id=current_user.id).order_by(Quote.quote_date.desc()).all()

    combined_data = []

    # Normalize Requests
    for r in requests:
        combined_data.append({
            "id": r.id,
            "type": "request",
            "display_id": f"REQ-{r.id}",
            "service_title": r.primary_service or "General Request",
            "date": r.request_date.strftime('%d %b %Y'),
            "sort_date": r.request_date.isoformat(),
            "status": r.status,
            "amount": r.total_price or 0.0,
            "is_actionable": False # Requests are just for tracking
        })

    # Normalize Formal Quotes
    for q in formal_quotes:
        combined_data.append({
            "id": q.id,
            "type": "formal",
            "display_id": q.quote_number,
            "service_title": "Formal Quote", # Could be improved by fetching first line item
            "date": q.quote_date.strftime('%d %b %Y'),
            "sort_date": q.quote_date.strftime('%Y-%m-%d'),
            "status": q.status,
            "amount": q.total,
            "is_actionable": q.status == 'Sent' # These can be Accepted/Rejected
        })

    # Sort combined list by date (newest first)
    combined_data.sort(key=lambda x: x['sort_date'], reverse=True)

    return jsonify(combined_data)

@bp.route('/api/my-invoices', methods=['GET'])
@login_required
def get_my_invoices():
    if not check_client_access(): return jsonify({"message": "Unauthorized"}), 403

    invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.invoice_date.desc()).all()
    
    data = [{
        "id": inv.id,
        "number": inv.invoice_number,
        "date": inv.invoice_date.strftime('%d %b %Y'),
        "due_date": inv.due_date.strftime('%d %b %Y') if inv.due_date else '-',
        "total": inv.total,
        "status": inv.status,
        "payment_token": inv.payment_token # Frontend uses this for the "Pay Now" button
    } for inv in invoices]

    return jsonify(data)

@bp.route('/api/my-bookings', methods=['GET'])
@login_required
def get_my_bookings():
    if not check_client_access(): return jsonify({"message": "Unauthorized"}), 403

    # Fetch jobs where this user is the client
    # We join 'Service' to show the fancy name (e.g., "Exterior Painting")
    jobs = Job.query.options(joinedload(Job.service)).filter(
        Job.client_id == current_user.id
    ).order_by(Job.scheduled_date.desc()).all()

    data = [{
        "id": j.id,
        "date": j.scheduled_date.strftime('%d %b %Y'),
        "time": j.start_time.strftime('%H:%M') if j.start_time else "TBD",
        "service_name": j.service.name if j.service else "Custom Service",
        "status": j.status,
        "notes": j.notes, # Often contains arrival instructions
        "staff_assigned": len(j.assigned_staff) > 0
    } for j in jobs]

    return jsonify(data)

@bp.route('/api/profile', methods=['POST'])
@login_required
def update_my_profile():
    """Allows the client to update their own contact details."""
    if not check_client_access(): return jsonify({"message": "Unauthorized"}), 403

    data = request.json
    profile = current_user.profile
    
    if not profile:
        # Should not happen, but safety net
        profile = Profile(user_id=current_user.id, tenant_id=current_user.tenant_id)
        db.session.add(profile)

    # Update fields
    profile.full_name = data.get('full_name', profile.full_name)
    profile.phone_number = data.get('phone_number', profile.phone_number)
    profile.address = data.get('address', profile.address)
    
    db.session.commit()
    return jsonify({"message": "Profile updated successfully"})