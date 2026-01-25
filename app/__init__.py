from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login - può essere Passeggero o CompagniaAerea"""
    from app.models import Passeggero, CompagniaAerea
    if not user_id:
        return None
    # Expected format: "p-<id>" or "c-<id>"
    if isinstance(user_id, str) and '-' in user_id:
        prefix, raw_id = user_id.split('-', 1)
        try:
            numeric_id = int(raw_id)
        except ValueError:
            return None
        if prefix == 'p':
            return Passeggero.query.get(numeric_id)
        if prefix == 'c':
            return CompagniaAerea.query.get(numeric_id)
        return None
    # Backward compatibility for sessions without prefix
    try:
        numeric_id = int(user_id)
    except (ValueError, TypeError):
        return None
    user = Passeggero.query.get(numeric_id)
    if user:
        return user
    return CompagniaAerea.query.get(numeric_id)

def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Enforce SECRET_KEY in non-debug environments
    default_secret = 'dev-secret-key-change-in-production'
    debug_env = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    if app.config.get('SECRET_KEY') == default_secret and not (debug_env or app.testing):
        raise RuntimeError('SECRET_KEY must be set in production.')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/flight_booking.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flight Booking startup')
    
    # Register error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        try:
            from app.security import request_context
            ctx = request_context()
            app.logger.warning(
                'CSRF error reason=%s ip=%s ua=%s session=%s user_id=%s',
                error.description, ctx['ip'], ctx['user_agent'], ctx['session_id'], ctx['user_id']
            )
        except Exception:
            app.logger.warning('CSRF error reason=%s', error.description)
        return render_template('errors/400.html', reason=error.description), 400

    @app.context_processor
    def inject_logout_form():
        from app.forms import LogoutForm
        return {'logout_form': LogoutForm()}
    
    # Register blueprints
    from app.routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.airline import airline as airline_blueprint
    app.register_blueprint(airline_blueprint, url_prefix='/airline')
    
    from app.passenger import passenger as passenger_blueprint
    app.register_blueprint(passenger_blueprint, url_prefix='/passenger')
    
    return app

