import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from flask_session import Session
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config import Config
from datetime import datetime

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
oauth = OAuth()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

def create_app(config_class=Config):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize Flask extensions here
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login' # Blueprint name 'auth', route 'login'
    mail.init_app(app)
    csrf.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)
    Session(app)

    # User loader function for Flask-Login
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Context Processors ---
    @app.context_processor
    def inject_now():
        """Injects the current UTC time into all templates."""
        return {'now': datetime.utcnow()}

    @app.context_processor
    def inject_auth_forms():
        """Injects login and registration forms into all templates."""
        from .forms import LoginForm, RegistrationForm
        login_form = LoginForm()
        register_form = RegistrationForm()
        return dict(login_form=login_form, register_form=register_form)

    # Configure Google OAuth within the app context
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    with app.app_context():
        # Import and register Blueprints
        from .routes.main import bp as main_bp
        from .routes.auth import bp as auth_bp
        from .routes.admin import bp as admin_bp
        from .routes.api import bp as api_bp
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(admin_bp, url_prefix='/admin')
        app.register_blueprint(api_bp, url_prefix='/api')

    return app