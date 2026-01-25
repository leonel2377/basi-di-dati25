from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import Passeggero, CompagniaAerea
from app.forms import (
    LoginForm,
    RegistrationForm,
    CompagniaAereaRegistrationForm,
    LogoutForm,
    PasswordResetRequestForm,
    PasswordResetForm,
)
from app.security import request_context, is_rate_limited, record_attempt, clear_attempts
import logging
import time
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

_ATTEMPT_WINDOW_SECONDS = 300
_MAX_ATTEMPTS = 5
_REGISTER_MAX_ATTEMPTS = 5
_RESET_MAX_ATTEMPTS = 5


def _reset_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt='password-reset')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """User login per passeggeri e compagnie"""
    if current_user.is_authenticated:
        # Redirect in base al tipo di utente
        if isinstance(current_user, CompagniaAerea):
            return redirect(url_for('airline.dashboard', compagnia_id=current_user.id))
        else:
            return redirect(url_for('passenger.dashboard'))
    
    form = LoginForm()
    if request.method == 'POST' and is_rate_limited('login', max_attempts=_MAX_ATTEMPTS, window_seconds=_ATTEMPT_WINDOW_SECONDS):
        ctx = request_context()
        logger.warning(
            'Login rate limited ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('auth/login.html', form=form), 429
    if form.validate_on_submit():
        # Normalize email to lowercase
        email_lower = form.email.data.lower() if form.email.data else ''
        if form.user_type.data == 'passeggero':
            user = Passeggero.query.filter_by(email=email_lower).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                clear_attempts('login')
                ctx = request_context()
                logger.info(
                    'Login success passenger=%s ip=%s ua=%s session=%s',
                    user.email, ctx['ip'], ctx['user_agent'], ctx['session_id']
                )
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('passenger.dashboard')
                return redirect(next_page)
        else:  # compagnia
            user = CompagniaAerea.query.filter_by(email=email_lower).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=True)
                clear_attempts('login')
                ctx = request_context()
                logger.info(
                    'Login success airline=%s ip=%s ua=%s session=%s',
                    user.email, ctx['ip'], ctx['user_agent'], ctx['session_id']
                )
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('airline.dashboard', compagnia_id=user.id)
                return redirect(next_page)
        record_attempt('login', window_seconds=_ATTEMPT_WINDOW_SECONDS)
        ctx = request_context()
        logger.warning(
            'Login failed email=%s type=%s ip=%s ua=%s session=%s',
            email_lower, form.user_type.data, ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Email o password non validi', 'error')
    elif request.method == 'POST':
        record_attempt('login', window_seconds=_ATTEMPT_WINDOW_SECONDS)
        ctx = request_context()
        logger.warning(
            'Login validation failed ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    return render_template('auth/login.html', form=form)


@auth.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout"""
    form = LogoutForm()
    if form.validate_on_submit():
        ctx = request_context()
        logger.info(
            'Logout user_id=%s ip=%s ua=%s session=%s',
            current_user.get_id(), ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        logout_user()
        flash('Logout effettuato con successo.', 'info')
        return redirect(url_for('main.index'))
    flash('Richiesta di logout non valida.', 'error')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    """User registration per passeggeri"""
    if current_user.is_authenticated:
        return redirect(url_for('passenger.dashboard'))
    
    form = RegistrationForm()
    if request.method == 'POST' and is_rate_limited('register', max_attempts=_REGISTER_MAX_ATTEMPTS, window_seconds=_ATTEMPT_WINDOW_SECONDS):
        ctx = request_context()
        logger.warning(
            'Passenger registration rate limited ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('auth/register.html', form=form), 429
    if form.validate_on_submit():
        try:
            passeggero = Passeggero(
                nome=form.nome.data,
                cognome=form.cognome.data,
                email=form.email.data.lower()  # Ensure lowercase
            )
            passeggero.set_password(form.password.data)
            db.session.add(passeggero)
            db.session.commit()
            flash('Registrazione completata con successo!', 'success')
            login_user(passeggero)
            clear_attempts('register')
            ctx = request_context()
            logger.info(
                'Passenger registered email=%s ip=%s ua=%s session=%s',
                passeggero.email, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('passenger.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante registrazione passeggero: {str(e)}', exc_info=True)
            flash('Errore durante la registrazione. Riprova.', 'error')
    elif request.method == 'POST':
        record_attempt('register', window_seconds=_ATTEMPT_WINDOW_SECONDS)
        ctx = request_context()
        logger.warning(
            'Passenger registration validation failed ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    return render_template('auth/register.html', form=form)


@auth.route('/register/compagnia', methods=['GET', 'POST'])
def register_compagnia():
    """Registrazione per compagnie aeree"""
    if current_user.is_authenticated:
        if isinstance(current_user, CompagniaAerea):
            return redirect(url_for('airline.dashboard', compagnia_id=current_user.id))
        else:
            return redirect(url_for('passenger.dashboard'))
    
    form = CompagniaAereaRegistrationForm()
    if request.method == 'POST' and is_rate_limited('register', max_attempts=_REGISTER_MAX_ATTEMPTS, window_seconds=_ATTEMPT_WINDOW_SECONDS):
        ctx = request_context()
        logger.warning(
            'Airline registration rate limited ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('auth/register_compagnia.html', form=form), 429
    if form.validate_on_submit():
        try:
            compagnia = CompagniaAerea(
                nome=form.nome.data,
                codice_iata=form.codice_iata.data.upper(),
                paese=form.paese.data,
                email=form.email.data.lower()  # Ensure lowercase
            )
            compagnia.set_password(form.password.data)
            db.session.add(compagnia)
            db.session.commit()
            flash('Registrazione compagnia completata con successo!', 'success')
            login_user(compagnia)
            clear_attempts('register')
            ctx = request_context()
            logger.info(
                'Airline registered name=%s email=%s ip=%s ua=%s session=%s',
                compagnia.nome, compagnia.email, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('airline.dashboard', compagnia_id=compagnia.id))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante registrazione compagnia: {str(e)}', exc_info=True)
            flash('Errore durante la registrazione. Verifica i dati inseriti.', 'error')
    elif request.method == 'POST':
        record_attempt('register', window_seconds=_ATTEMPT_WINDOW_SECONDS)
        ctx = request_context()
        logger.warning(
            'Airline registration validation failed ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    return render_template('auth/register_compagnia.html', form=form)


@auth.route('/reset-password', methods=['GET', 'POST'])
def reset_password_request():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = PasswordResetRequestForm()
    if request.method == 'POST' and is_rate_limited('password_reset_request', max_attempts=_RESET_MAX_ATTEMPTS, window_seconds=_ATTEMPT_WINDOW_SECONDS):
        ctx = request_context()
        logger.warning(
            'Password reset request rate limited ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('auth/reset_password_request.html', form=form), 429
    if form.validate_on_submit():
        email_lower = form.email.data.lower()
        user_type = form.user_type.data
        user = None
        if user_type == 'passeggero':
            user = Passeggero.query.filter_by(email=email_lower).first()
        elif user_type == 'compagnia':
            user = CompagniaAerea.query.filter_by(email=email_lower).first()
        if user:
            serializer = _reset_serializer()
            token = serializer.dumps({'uid': user.id, 'type': user_type})
            reset_link = url_for('auth.reset_password_token', token=token, _external=True)
            ctx = request_context()
            logger.info(
                'Password reset link generated type=%s email=%s link=%s ip=%s ua=%s session=%s',
                user_type, email_lower, reset_link, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
        clear_attempts('password_reset_request')
        flash('Se l\'account esiste, riceverai un link per reimpostare la password.', 'info')
        return redirect(url_for('auth.login'))
    elif request.method == 'POST':
        record_attempt('password_reset_request', window_seconds=_ATTEMPT_WINDOW_SECONDS)
        ctx = request_context()
        logger.warning(
            'Password reset request validation failed ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    return render_template('auth/reset_password_request.html', form=form)


@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password_token(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST' and is_rate_limited('password_reset_confirm', max_attempts=_RESET_MAX_ATTEMPTS, window_seconds=_ATTEMPT_WINDOW_SECONDS):
        ctx = request_context()
        logger.warning(
            'Password reset confirm rate limited ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('auth/reset_password.html', form=PasswordResetForm(), token=token), 429
    serializer = _reset_serializer()
    try:
        data = serializer.loads(token, max_age=3600)
    except (BadSignature, SignatureExpired):
        ctx = request_context()
        logger.warning(
            'Password reset token invalid ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        return render_template('errors/400.html', reason='Token non valido o scaduto.'), 400
    user_type = data.get('type')
    user_id = data.get('uid')
    if user_type == 'passeggero':
        user = Passeggero.query.get(user_id)
    elif user_type == 'compagnia':
        user = CompagniaAerea.query.get(user_id)
    else:
        user = None
    if not user:
        ctx = request_context()
        logger.warning(
            'Password reset token user missing ip=%s ua=%s session=%s',
            ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        return render_template('errors/400.html', reason='Token non valido o scaduto.'), 400
    form = PasswordResetForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        clear_attempts('password_reset_confirm')
        ctx = request_context()
        logger.info(
            'Password reset success type=%s user_id=%s ip=%s ua=%s session=%s',
            user_type, user.id, ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Password aggiornata con successo. Ora puoi accedere.', 'success')
        return redirect(url_for('auth.login'))
    elif request.method == 'POST':
        record_attempt('password_reset_confirm', window_seconds=_ATTEMPT_WINDOW_SECONDS)
        ctx = request_context()
        logger.warning(
            'Password reset validation failed type=%s user_id=%s ip=%s ua=%s session=%s',
            user_type, user.id, ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    return render_template('auth/reset_password.html', form=form, token=token)
