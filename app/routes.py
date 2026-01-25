from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Aeroporto, Volo, Biglietto
from app.forms import FlightSearchForm
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_, or_, func

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Home page"""
    aeroporti = Aeroporto.query.order_by(Aeroporto.città).all()
    return render_template('index.html', aeroporti=aeroporti)


@main.route('/search', methods=['GET', 'POST'])
def search_flights():
    """Flight search - available to anonymous users"""
    form = FlightSearchForm()
    
    # Populate airport choices
    aeroporti = Aeroporto.query.order_by(Aeroporto.città).all()
    form.aeroporto_partenza.choices = [(a.id_aeroporto, f"{a.città} ({a.codice_iata})") for a in aeroporti]
    form.aeroporto_destinazione.choices = [(a.id_aeroporto, f"{a.città} ({a.codice_iata})") for a in aeroporti]
    
    results = []
    search_performed = False
    
    if form.validate_on_submit():
        search_performed = True
        aeroporto_partenza_id = form.aeroporto_partenza.data
        aeroporto_destinazione_id = form.aeroporto_destinazione.data
        data_partenza = form.data_partenza.data
        
        # Search for direct flights
        voli_diretti = Volo.query.filter(
            and_(
                Volo.aeroporto_partenza == aeroporto_partenza_id,
                Volo.aeroporto_destinazione == aeroporto_destinazione_id,
                Volo.data_partenza == data_partenza,
                Volo.posti_disponibili > 0
            )
        ).all()
        
        for volo in voli_diretti:
            results.append({
                'type': 'direct',
                'volo': volo,
                'stops': 0,
                'prezzo': float(volo.prezzo_economy)  # Prezzo economy (prezzo minimo disponibile)
            })
        
        # Search for flights with one stop (minimum 2 hours layover)
        # Find first leg: departure -> intermediate
        first_leg = Volo.query.filter(
            and_(
                Volo.aeroporto_partenza == aeroporto_partenza_id,
                Volo.data_partenza == data_partenza,
                Volo.posti_disponibili > 0
            )
        ).all()
        
        for volo1 in first_leg:
            # Calculate arrival datetime
            datetime_arrivo1 = datetime.combine(volo1.data_arrivo, volo1.ora_arrivo)
            # Minimum layover: 2 hours
            min_departure_time = datetime_arrivo1 + timedelta(hours=2)
            
            # Find second leg: intermediate -> destination
            second_leg = Volo.query.filter(
                and_(
                    Volo.aeroporto_partenza == volo1.aeroporto_destinazione,
                    Volo.aeroporto_destinazione == aeroporto_destinazione_id,
                    Volo.data_partenza >= min_departure_time.date(),
                    Volo.posti_disponibili > 0
                )
            ).all()
            
            for volo2 in second_leg:
                datetime_partenza2 = datetime.combine(volo2.data_partenza, volo2.ora_partenza)
                
                # Check if layover is at least 2 hours
                if datetime_partenza2 >= min_departure_time:
                    layover_hours = (datetime_partenza2 - datetime_arrivo1).total_seconds() / 3600
                    
                    results.append({
                        'type': 'connecting',
                        'voli': [volo1, volo2],
                        'stops': 1,
                        'layover_hours': layover_hours,
                        'prezzo': float(volo1.prezzo_economy + volo2.prezzo_economy)  # Prezzo economy per entrambi i voli
                    })
        
        # Sort results
        sort_by = request.args.get('sort', 'prezzo')
        if sort_by == 'prezzo':
            results.sort(key=lambda x: x['prezzo'])
        elif sort_by == 'durata':
            # Calculate duration for sorting
            for result in results:
                if result['type'] == 'direct':
                    volo = result['volo']
                    dt_partenza = datetime.combine(volo.data_partenza, volo.ora_partenza)
                    dt_arrivo = datetime.combine(volo.data_arrivo, volo.ora_arrivo)
                    result['durata'] = (dt_arrivo - dt_partenza).total_seconds() / 60
                else:
                    volo1, volo2 = result['voli']
                    dt_partenza = datetime.combine(volo1.data_partenza, volo1.ora_partenza)
                    dt_arrivo = datetime.combine(volo2.data_arrivo, volo2.ora_arrivo)
                    result['durata'] = (dt_arrivo - dt_partenza).total_seconds() / 60
            results.sort(key=lambda x: x.get('durata', 0))
        elif sort_by == 'soste':
            results.sort(key=lambda x: x['stops'])
    
    return render_template('search.html', form=form, results=results, search_performed=search_performed)


@main.route('/volo/<int:volo_id>')
def volo_details(volo_id):
    """Flight details page"""
    volo = Volo.query.get_or_404(volo_id)
    return render_template('flight_details.html', volo=volo)
