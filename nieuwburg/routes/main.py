from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .. import db
from ..models import Post, User, Quote, Invoice, QuoteRequest, Job
from ..forms import PlacementApplicationForm
from datetime import date

bp = Blueprint('main', __name__)

# --- Public Facing Page Routes ---

@bp.route('/')
def index():
    return render_template('public/index.html')

@bp.route('/blog')
def blog():
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_date.desc()).all()
    return render_template('public/blog.html', posts=posts)

@bp.route('/blog/<int:post_id>')
def post_detail(post_id):
    post = db.session.get(Post, post_id)
    if not post or (not post.is_published and (not current_user.is_authenticated or current_user.role != 'admin')):
        flash('Post not found.', 'error')
        return redirect(url_for('main.blog'))
    return render_template('public/post_detail.html', post=post)

@bp.route('/faq')
def faq():
    return render_template('public/faq.html')

@bp.route('/gallery')
def gallery():
    return render_template('public/gallery.html')

@bp.route('/blitz-dock')
def blitz_dock():
    return render_template('public/blitz_dock.html')

@bp.route('/about-us')
def about_us():
    return render_template('public/about.html')

# --- Placements Routes ---

@bp.route('/placements/housekeeper')
def housekeeper_placement():
    return render_template('placements/housekeeper.html')

@bp.route('/placements/nanny')
def nanny_placement():
    return render_template('placements/nanny.html')

@bp.route('/placements/carer')
def carer_placement():
    return render_template('placements/carer.html')

@bp.route('/placements/apply/<service_type>', methods=['GET', 'POST'])
def placement_apply(service_type):
    if service_type not in ['housekeeper', 'nanny', 'carer']:
        return redirect(url_for('main.index'))
    form = PlacementApplicationForm()
    if form.validate_on_submit():
        # In a real app, you would send an email here
        flash('Thank you for your application! We will be in contact with you shortly.', 'success')
        return redirect(url_for('main.index'))
    return render_template('placements/placement_apply.html', form=form, service_type=service_type)


# --- Authenticated User Dashboards ---

@bp.route('/dashboard')
@login_required
def client_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin.admin_spa_shell'))
    if current_user.role == 'staff':
        return redirect(url_for('main.staff_dashboard'))

    user_bookings = QuoteRequest.query.filter_by(user_id=current_user.id).order_by(QuoteRequest.request_date.desc()).all()
    user_quotes = Quote.query.filter_by(user_id=current_user.id).order_by(Quote.quote_date.desc()).all()
    user_invoices = Invoice.query.filter_by(user_id=current_user.id).order_by(Invoice.invoice_date.desc()).all()
    
    return render_template(
        'client/client_dashboard.html', 
        bookings=user_bookings,
        quotes=user_quotes,
        invoices=user_invoices
    )

@bp.route('/staff/dashboard')
@login_required
def staff_dashboard():
    if current_user.role != 'staff':
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))

    today = date.today()
    assigned_jobs = Job.query.options(
        db.joinedload(Job.quote_request).joinedload(QuoteRequest.user).joinedload(User.profile),
        db.joinedload(Job.assigned_staff).joinedload(User.profile)
    ).filter(Job.assigned_staff.any(id=current_user.id)).order_by(Job.scheduled_date, Job.start_time).all()

    upcoming_jobs = [j for j in assigned_jobs if j.scheduled_date >= today]
    past_jobs = [j for j in assigned_jobs if j.scheduled_date < today]

    return render_template('staff/staff_dashboard.html', upcoming_jobs=upcoming_jobs, past_jobs=past_jobs)