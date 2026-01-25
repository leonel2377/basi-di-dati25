from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import CompagniaAerea, Aeroporto, Aereo, Volo, Biglietto
from app.forms import CompagniaAereaForm, AereoForm, AeroportoForm, VoloForm
from app.security import is_rate_limited, record_attempt, clear_attempts, request_context
from datetime import datetime, date, time
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

airline = Blueprint('airline', __name__)


def get_compagnia():
    """Helper per ottenere la compagnia aerea dell'utente corrente"""
    if not current_user.is_authenticated:
        return None
    if isinstance(current_user, CompagniaAerea):
        return current_user
    return None


@airline.route('/dashboard')
@login_required
def dashboard():
    """Airline dashboard"""
    compagnia = get_compagnia()
    if not compagnia:
        flash('Accesso negato. Solo le compagnie aeree possono accedere.', 'error')
        return redirect(url_for('main.index'))
    
    compagnia_id = compagnia.id
    
    # Statistics
    total_voli = Volo.query.filter_by(id_compagnia=compagnia_id).count()
    total_biglietti = Biglietto.query.join(Volo).filter(Volo.id_compagnia == compagnia_id).count()
    
    total_ricavi = db.session.query(func.sum(Biglietto.prezzo)).join(Volo).filter(
        Volo.id_compagnia == compagnia_id
    ).scalar() or 0
    
    # Most popular routes
    tratte_popolari = db.session.query(
        Volo.aeroporto_partenza,
        Volo.aeroporto_destinazione,
        func.count(Biglietto.id_biglietto).label('num_biglietti')
    ).join(Biglietto).filter(
        Volo.id_compagnia == compagnia_id
    ).group_by(
        Volo.aeroporto_partenza,
        Volo.aeroporto_destinazione
    ).order_by(func.count(Biglietto.id_biglietto).desc()).limit(5).all()
    
    # Get airports for display
    aeroporti = Aeroporto.query.all()
    
    return render_template('airline/dashboard.html', 
                         compagnia=compagnia,
                         total_voli=total_voli,
                         total_biglietti=total_biglietti,
                         total_ricavi=float(total_ricavi),
                         tratte_popolari=tratte_popolari,
                         aeroporti=aeroporti)


@airline.route('/profilo', methods=['GET', 'POST'])
@login_required
def profilo():
    """Modifica profilo compagnia"""
    compagnia = get_compagnia()
    if not compagnia:
        flash('Accesso negato. Solo le compagnie aeree possono accedere.', 'error')
        return redirect(url_for('main.index'))
    
    form = CompagniaAereaForm(obj=compagnia)
    if request.method == 'POST' and is_rate_limited('airline_profile', max_attempts=10):
        ctx = request_context()
        logger.warning(
            'Airline profile rate limited user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        return render_template('airline/profilo.html', form=form, compagnia=compagnia), 429
    if form.validate_on_submit():
        try:
            compagnia.nome = form.nome.data
            compagnia.codice_iata = form.codice_iata.data.upper()
            compagnia.paese = form.paese.data
            db.session.commit()
            flash('Profilo aggiornato con successo!', 'success')
            clear_attempts('airline_profile')
            ctx = request_context()
            logger.info(
                'Airline profile updated user_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('airline.profilo'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante aggiornamento profilo compagnia: {str(e)}', exc_info=True)
            flash('Errore durante l\'aggiornamento del profilo. Riprova.', 'error')
    elif request.method == 'POST':
        record_attempt('airline_profile')
        ctx = request_context()
        logger.warning(
            'Airline profile validation failed user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    return render_template('airline/profilo.html', form=form, compagnia=compagnia)


@airline.route('/aerei', methods=['GET', 'POST'])
@login_required
def gestisci_aerei():
    """Manage aircrafts"""
    compagnia = get_compagnia()
    if not compagnia:
        flash('Accesso negato. Solo le compagnie aeree possono accedere.', 'error')
        return redirect(url_for('main.index'))
    
    compagnia_id = compagnia.id
    form = AereoForm()
    
    if request.method == 'POST' and is_rate_limited('airline_aircraft', max_attempts=10):
        ctx = request_context()
        logger.warning(
            'Airline aircraft rate limited user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        aerei = Aereo.query.filter_by(id_compagnia=compagnia_id).all()
        return render_template('airline/aerei.html', form=form, compagnia=compagnia, aerei=aerei), 429
    if form.validate_on_submit():
        try:
            aereo = Aereo(
                modello=form.modello.data,
                posti_totali=form.posti_totali.data,
                id_compagnia=compagnia_id
            )
            db.session.add(aereo)
            db.session.commit()
            flash('Aereo aggiunto con successo!', 'success')
            logger.info(f'Aereo {aereo.modello} aggiunto da compagnia {compagnia_id}')
            clear_attempts('airline_aircraft')
            ctx = request_context()
            logger.info(
                'Airline aircraft created user_id=%s aereo_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], aereo.id_aereo, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('airline.gestisci_aerei'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante aggiunta aereo: {str(e)}', exc_info=True)
            flash('Errore durante l\'aggiunta dell\'aereo. Riprova.', 'error')
    elif request.method == 'POST':
        record_attempt('airline_aircraft')
        ctx = request_context()
        logger.warning(
            'Airline aircraft validation failed user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    aerei = Aereo.query.filter_by(id_compagnia=compagnia_id).all()
    return render_template('airline/aerei.html', form=form, compagnia=compagnia, aerei=aerei)


@airline.route('/voli', methods=['GET', 'POST'])
@login_required
def gestisci_voli():
    """Manage flights"""
    compagnia = get_compagnia()
    if not compagnia:
        flash('Accesso negato. Solo le compagnie aeree possono accedere.', 'error')
        return redirect(url_for('main.index'))
    
    compagnia_id = compagnia.id
    form = VoloForm()
    
    # Populate choices
    aerei = Aereo.query.filter_by(id_compagnia=compagnia_id).all()
    form.id_aereo.choices = [(a.id_aereo, f"{a.modello} ({a.posti_totali} posti)") for a in aerei]
    
    aeroporti = Aeroporto.query.order_by(Aeroporto.città).all()
    form.aeroporto_partenza.choices = [(a.id_aeroporto, f"{a.città} ({a.codice_iata})") for a in aeroporti]
    form.aeroporto_destinazione.choices = [(a.id_aeroporto, f"{a.città} ({a.codice_iata})") for a in aeroporti]
    
    # Check if company has aircrafts
    has_aircrafts = len(aerei) > 0
    
    if request.method == 'POST' and is_rate_limited('airline_flight', max_attempts=10):
        ctx = request_context()
        logger.warning(
            'Airline flight rate limited user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        voli = Volo.query.filter_by(id_compagnia=compagnia_id).order_by(Volo.data_partenza.desc()).limit(50).all()
        return render_template('airline/voli.html', form=form, compagnia=compagnia, voli=voli, has_aircrafts=has_aircrafts), 429
    if form.validate_on_submit():
        try:
            aereo = Aereo.query.get(form.id_aereo.data)
            
            # Validate that aircraft belongs to company
            if not aereo or aereo.id_compagnia != compagnia_id:
                flash('Aereo non valido o non appartenente alla tua compagnia.', 'error')
                return redirect(url_for('airline.gestisci_voli'))
            
            if form.posti_disponibili.data is not None and form.posti_disponibili.data > aereo.posti_totali:
                flash('I posti disponibili non possono superare i posti totali dell\'aereo.', 'error')
                return redirect(url_for('airline.gestisci_voli'))
            
            volo = Volo(
                data_partenza=form.data_partenza.data,
                ora_partenza=form.ora_partenza.data,
                data_arrivo=form.data_arrivo.data,
                ora_arrivo=form.ora_arrivo.data,
                posti_disponibili=form.posti_disponibili.data if form.posti_disponibili.data else aereo.posti_totali,
                id_compagnia=compagnia.id,
                id_aereo=form.id_aereo.data,
                aeroporto_partenza=form.aeroporto_partenza.data,
                aeroporto_destinazione=form.aeroporto_destinazione.data,
                prezzo_economy=form.prezzo_economy.data,
                prezzo_business=form.prezzo_business.data,
                prezzo_first=form.prezzo_first.data
            )
            db.session.add(volo)
            db.session.commit()
            flash('Volo creato con successo!', 'success')
            logger.info(f'Volo {volo.id_volo} creato da compagnia {compagnia_id}')
            clear_attempts('airline_flight')
            ctx = request_context()
            logger.info(
                'Airline flight created user_id=%s volo_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], volo.id_volo, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('airline.gestisci_voli'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante creazione volo: {str(e)}', exc_info=True)
            flash('Errore durante la creazione del volo. Verifica i dati inseriti.', 'error')
    elif request.method == 'POST':
        record_attempt('airline_flight')
        ctx = request_context()
        logger.warning(
            'Airline flight validation failed user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    voli = Volo.query.filter_by(id_compagnia=compagnia_id).order_by(Volo.data_partenza.desc()).limit(50).all()
    return render_template('airline/voli.html', form=form, compagnia=compagnia, voli=voli, has_aircrafts=has_aircrafts)


@airline.route('/aeroporti', methods=['GET', 'POST'])
@login_required
def gestisci_aeroporti():
    """Manage airports"""
    compagnia = get_compagnia()
    if not compagnia:
        flash('Accesso negato. Solo le compagnie aeree possono accedere.', 'error')
        return redirect(url_for('main.index'))
    
    form = AeroportoForm()
    
    if request.method == 'POST' and is_rate_limited('airline_airport', max_attempts=10):
        ctx = request_context()
        logger.warning(
            'Airline airport rate limited user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
        flash('Troppi tentativi. Riprova tra qualche minuto.', 'error')
        aeroporti = Aeroporto.query.order_by(Aeroporto.città).all()
        return render_template('airline/aeroporti.html', form=form, aeroporti=aeroporti), 429
    if form.validate_on_submit():
        try:
            aeroporto = Aeroporto(
                nome=form.nome.data,
                città=form.città.data,
                paese=form.paese.data,
                codice_iata=form.codice_iata.data.upper()
            )
            db.session.add(aeroporto)
            db.session.commit()
            flash('Aeroporto aggiunto con successo!', 'success')
            logger.info(f'Aeroporto {aeroporto.codice_iata} aggiunto da compagnia {compagnia.id}')
            clear_attempts('airline_airport')
            ctx = request_context()
            logger.info(
                'Airline airport created user_id=%s aeroporto_id=%s ip=%s ua=%s session=%s',
                ctx['user_id'], aeroporto.id_aeroporto, ctx['ip'], ctx['user_agent'], ctx['session_id']
            )
            return redirect(url_for('airline.gestisci_aeroporti'))
        except Exception as e:
            db.session.rollback()
            logger.error(f'Errore durante aggiunta aeroporto: {str(e)}', exc_info=True)
            flash('Errore durante l\'aggiunta dell\'aeroporto. Verifica che il codice IATA non sia già utilizzato.', 'error')
    elif request.method == 'POST':
        record_attempt('airline_airport')
        ctx = request_context()
        logger.warning(
            'Airline airport validation failed user_id=%s ip=%s ua=%s session=%s',
            ctx['user_id'], ctx['ip'], ctx['user_agent'], ctx['session_id']
        )
    
    aeroporti = Aeroporto.query.order_by(Aeroporto.città).all()
    return render_template('airline/aeroporti.html', form=form, aeroporti=aeroporti)
