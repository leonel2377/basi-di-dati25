from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Passeggero, Volo, Biglietto, Extra
from app.forms import BigliettoForm, PassengerProfileForm
from app.security import is_rate_limited, record_attempt, clear_attempts, request_context
from datetime import date
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

passenger = Blueprint('passenger', __name__)


def get_passeggero():
    """Helper per ottenere il passeggero dell'utente corrente"""
    if not current_user.is_authenticated:
        return None
    if isinstance(current_user, Passeggero):
        return current_user
    return None


@passenger.route('/dashboard')
@login_required
def dashboard():
    """Passenger dashboard"""
    passeggero = get_passeggero()
    if not passeggero:
        flash('Accesso negato. Solo i passeggeri possono accedere.', 'error')
        return redirect(url_for('main.index'))
    biglietti = Biglietto.query.filter_by(id_passeggero=passeggero.id).order_by(Biglietto.data_acquisto.desc()).all()
    return render_template('passenger/dashboard.html', passeggero=passeggero, biglietti=biglietti)


@passenger.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
    """Passenger profile management"""
    passeggero = get_passeggero()
    if not passeggero:
        flash('Accesso negato. Solo i passeggeri possono accedere.', 'error')
        return redirect(url_for('main.index'))
    form = PassengerProfileForm(obj=passeggero)
    if request.method == 'POST' and is_rate_limited('passenger_profile', max_attempts=10):
        ctx = request_context()
        logger.warning(
            'Passenger profile rate limited user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('passenger/profile.html', passeggero=passeggero, form=form), 429
    if form.validate_on_submit():
        try:
            passeggero.nome = form.nome.data
            passeggero.cognome = form.cognome.data
            db.session.commit()
            flash('Profilo aggiornato con successo!', 'success')
            clear_attempts('passenger_profile')
            ctx = request_context()
            logger.info(
                'Passenger profile updated user_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('passenger.profilo'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante aggiornamento profilo: {str(e)}', exc_info=True)
            flash('Errore durante l\'aggiornamento del profilo. Riprova.', 'error')
    elif request.method == 'POST':
        record_attempt('passenger_profile')
        ctx = request_context()
        logger.warning(
            'Passenger profile validation failed user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    return render_template('passenger/profile.html', passeggero=passeggero, form=form)


@passenger.route('/acquista/<int:volo_id>', methods=['GET', 'POST'])
@login_required
def acquista_biglietto(volo_id):
    """Purchase ticket for a flight"""
    passeggero = get_passeggero()
    if not passeggero:
        flash('Accesso negato. Solo i passeggeri possono acquistare biglietti.', 'error')
        return redirect(url_for('main.index'))
    volo = Volo.query.get_or_404(volo_id)
    form = BigliettoForm()
    
    # Get available extras
    extra_disponibili = Extra.query.all()
    
    if request.method == 'POST' and is_rate_limited('ticket_purchase', max_attempts=10):
        ctx = request_context()
        logger.warning(
            'Ticket purchase rate limited user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('passenger/book.html', volo=volo, form=form, extra_disponibili=extra_disponibili, prezzi={
            'economy': float(volo.prezzo_economy),
            'business': float(volo.prezzo_business),
            'first': float(volo.prezzo_first)
        }), 429
    if form.validate_on_submit():
        try:
            # Reload flight for pricing and sanity checks
            volo = Volo.query.get_or_404(volo_id)
            
            # Atomically decrement seats to avoid overbooking
            updated_rows = (
                Volo.query.filter(
                    Volo.id_volo == volo_id,
                    Volo.posti_disponibili > 0
                ).update(
                    {Volo.posti_disponibili: Volo.posti_disponibili - 1},
                    synchronize_session=False
                )
            )
            if updated_rows == 0:
                db.session.rollback()
                flash('Nessun posto disponibile su questo volo.', 'error')
                return redirect(url_for('main.search_flights'))
            
            # Get price based on class from volo
            prezzi = {
                'economy': float(volo.prezzo_economy),
                'business': float(volo.prezzo_business),
                'first': float(volo.prezzo_first)
            }
            prezzo = prezzi.get(form.classe.data, float(volo.prezzo_economy))
            
            # Create ticket
            biglietto = Biglietto(
                data_acquisto=date.today(),
                prezzo=prezzo,
                classe=form.classe.data,
                posto=form.posto.data if form.posto.data else None,
                id_passeggero=passeggero.id,
                id_volo=volo_id
            )
            db.session.add(biglietto)
            
            # Add extras if selected
            extra_ids = request.form.getlist('extra')
            for extra_id in extra_ids:
                extra = Extra.query.get(extra_id)
                if extra:
                    biglietto.extra.append(extra)
                    prezzo += float(extra.costo)
            
            # Update ticket price with extras
            biglietto.prezzo = prezzo
            
            db.session.commit()
            
            flash(f'Biglietto acquistato con successo! ID: {biglietto.id_biglietto}', 'success')
            logger.info(f'Biglietto {biglietto.id_biglietto} acquistato da passeggero {passeggero.id} per volo {volo_id}')
            clear_attempts('ticket_purchase')
            ctx = request_context()
            logger.info(
                'Ticket purchase success user_id=%s volo_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], volo_id, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('passenger.dashboard'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante acquisto biglietto: {str(e)}', exc_info=True)
            record_attempt('ticket_purchase')
            ctx = request_context()
            logger.warning(
                'Ticket purchase failed user_id=%s volo_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], volo_id, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            flash('Errore durante l\'acquisto del biglietto. Riprova più tardi.', 'error')
            return redirect(url_for('main.search_flights'))
    elif request.method == 'POST':
        record_attempt('ticket_purchase')
        ctx = request_context()
        logger.warning(
            'Ticket purchase validation failed user_id=%s volo_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], volo_id, ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    # Prepara i prezzi per il template
    prezzi = {
        'economy': float(volo.prezzo_economy),
        'business': float(volo.prezzo_business),
        'first': float(volo.prezzo_first)
    }
    
    return render_template('passenger/book.html', volo=volo, form=form, extra_disponibili=extra_disponibili, prezzi=prezzi)


@passenger.route('/biglietto/<int:biglietto_id>')
@login_required
def view_biglietto(biglietto_id):
    """View ticket details"""
    passeggero = get_passeggero()
    if not passeggero:
        flash('Accesso negato. Solo i passeggeri possono accedere.', 'error')
        return redirect(url_for('main.index'))
    biglietto = Biglietto.query.get_or_404(biglietto_id)
    
    if biglietto.id_passeggero != passeggero.id:
        flash('Accesso negato.', 'error')
        return redirect(url_for('passenger.dashboard'))
    
    return render_template('passenger/biglietto_details.html', biglietto=biglietto)
