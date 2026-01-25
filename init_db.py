"""
Database initialization script
Creates tables and populates with sample data according to the ER schema
"""
from app import create_app, db
from app.models import (
    CompagniaAerea, Aeroporto, Aereo, Volo, Passeggero, Biglietto, Extra
)
from datetime import datetime, date, time, timedelta
import random

def init_database():
    """Initialize database with sample data"""
    app = create_app()
    
    with app.app_context():
        # Drop all tables (for development)
        print("Dropping existing tables...")
        db.drop_all()
        
        # Create all tables
        print("Creating tables...")
        db.create_all()
        
        # Create airports
        print("Creating airports...")
        aeroporti_data = [
            {'nome': 'Leonardo da Vinci-Fiumicino', 'città': 'Roma', 'paese': 'Italia', 'codice_iata': 'FCO'},
            {'nome': 'Malpensa', 'città': 'Milano', 'paese': 'Italia', 'codice_iata': 'MXP'},
            {'nome': 'Linate', 'città': 'Milano', 'paese': 'Italia', 'codice_iata': 'LIN'},
            {'nome': 'Charles de Gaulle', 'città': 'Parigi', 'paese': 'Francia', 'codice_iata': 'CDG'},
            {'nome': 'Heathrow', 'città': 'Londra', 'paese': 'Regno Unito', 'codice_iata': 'LHR'},
            {'nome': 'John F. Kennedy', 'città': 'New York', 'paese': 'USA', 'codice_iata': 'JFK'},
            {'nome': 'Los Angeles International', 'città': 'Los Angeles', 'paese': 'USA', 'codice_iata': 'LAX'},
            {'nome': 'Dubai International', 'città': 'Dubai', 'paese': 'Emirati Arabi', 'codice_iata': 'DXB'},
            {'nome': 'Frankfurt', 'città': 'Francoforte', 'paese': 'Germania', 'codice_iata': 'FRA'},
            {'nome': 'Schiphol', 'città': 'Amsterdam', 'paese': 'Paesi Bassi', 'codice_iata': 'AMS'},
        ]
        
        aeroporti = {}
        for ap_data in aeroporti_data:
            aeroporto = Aeroporto(**ap_data)
            db.session.add(aeroporto)
            aeroporti[ap_data['codice_iata']] = aeroporto
        
        db.session.commit()
        print(f"Created {len(aeroporti)} airports")
        
        # Create airlines
        print("Creating airlines...")
        compagnie_data = [
            {'nome': 'Alitalia', 'codice_iata': 'AZ', 'paese': 'Italia'},
            {'nome': 'Lufthansa', 'codice_iata': 'LH', 'paese': 'Germania'},
            {'nome': 'Air France', 'codice_iata': 'AF', 'paese': 'Francia'},
        ]
        
        compagnie = {}
        for comp_data in compagnie_data:
            compagnia = CompagniaAerea(
                nome=comp_data['nome'],
                codice_iata=comp_data['codice_iata'],
                paese=comp_data['paese'],
                email=f"admin@{comp_data['codice_iata'].lower()}.com"
            )
            compagnia.set_password('password123')
            db.session.add(compagnia)
            compagnie[comp_data['codice_iata']] = compagnia
        
        db.session.commit()
        print(f"Created {len(compagnie)} airlines")
        
        # Create aircrafts
        print("Creating aircrafts...")
        aerei = []
        modelli_aerei = [
            {'modello': 'Boeing 737-800', 'posti': 180},
            {'modello': 'Airbus A320', 'posti': 180},
            {'modello': 'Boeing 777-300ER', 'posti': 350},
            {'modello': 'Airbus A330', 'posti': 250},
        ]
        
        for compagnia in compagnie.values():
            for modello_data in modelli_aerei:
                aereo = Aereo(
                    modello=modello_data['modello'],
                    posti_totali=modello_data['posti'],
                    id_compagnia=compagnia.id
                )
                db.session.add(aereo)
                aerei.append(aereo)
        
        db.session.commit()
        print(f"Created {len(aerei)} aircrafts")
        
        # Create flights
        print("Creating flights...")
        voli = []
        base_date = date.today()
        
        # Route definitions: (departure, arrival, duration_hours)
        route_definitions = [
            ('FCO', 'MXP', 1),
            ('FCO', 'CDG', 2),
            ('FCO', 'LHR', 2.5),
            ('MXP', 'CDG', 1.5),
            ('MXP', 'FRA', 1.5),
            ('CDG', 'JFK', 8),
            ('LHR', 'JFK', 7.5),
            ('FRA', 'DXB', 6),
            ('AMS', 'LAX', 11),
        ]
        
        for dep_code, arr_code, dur_hours in route_definitions:
            if dep_code in aeroporti and arr_code in aeroporti:
                # Assign to random airline
                compagnia = random.choice(list(compagnie.values()))
                aereo = random.choice([a for a in aerei if a.id_compagnia == compagnia.id])
                
                for day_offset in range(7):  # Flights for next 7 days
                    for hour in [8, 12, 16, 20]:  # Multiple flights per day
                        data_partenza = base_date + timedelta(days=day_offset)
                        ora_partenza = time(hour, 0)
                        
                        # Calculate arrival
                        data_arrivo = data_partenza
                        arrivo_hours = hour + int(dur_hours)
                        arrivo_minutes = int((dur_hours - int(dur_hours)) * 60)
                        if arrivo_hours >= 24:
                            data_arrivo += timedelta(days=1)
                            arrivo_hours -= 24
                        ora_arrivo = time(arrivo_hours, arrivo_minutes)
                        
                        # Calcola prezzi base in base alla durata del volo
                        prezzo_base = dur_hours * 50  # €50 per ora di volo
                        volo = Volo(
                            data_partenza=data_partenza,
                            ora_partenza=ora_partenza,
                            data_arrivo=data_arrivo,
                            ora_arrivo=ora_arrivo,
                            posti_disponibili=aereo.posti_totali,
                            id_compagnia=compagnia.id,
                            id_aereo=aereo.id_aereo,
                            aeroporto_partenza=aeroporti[dep_code].id_aeroporto,
                            aeroporto_destinazione=aeroporti[arr_code].id_aeroporto,
                            prezzo_economy=prezzo_base,
                            prezzo_business=prezzo_base * 1.5,
                            prezzo_first=prezzo_base * 2.5
                        )
                        db.session.add(volo)
                        voli.append(volo)
        
        db.session.commit()
        print(f"Created {len(voli)} flights")
        
        # Create sample passenger
        print("Creating sample passenger...")
        passeggero = Passeggero(
            nome='Mario',
            cognome='Rossi',
            email='mario.rossi@example.com'
        )
        passeggero.set_password('password123')
        db.session.add(passeggero)
        db.session.commit()
        print("Created sample passenger")
        
        # Create extras
        print("Creating extras...")
        extra_data = [
            {'nome': 'Bagaglio Aggiuntivo', 'costo': 50.00},
            {'nome': 'Posto Più Largo', 'costo': 30.00},
            {'nome': 'Pasto Speciale', 'costo': 15.00},
            {'nome': 'Assicurazione Viaggio', 'costo': 25.00},
        ]
        
        for ex_data in extra_data:
            extra = Extra(**ex_data)
            db.session.add(extra)
        
        db.session.commit()
        print("Created extras")
        
        print("\nDatabase initialized successfully!")
        print("\nAccount di test:")
        print("\nPasseggero:")
        print("  Email: mario.rossi@example.com")
        print("  Password: password123")
        print("\nCompagnie Aeree:")
        for comp_data in compagnie_data:
            print(f"  Email: admin@{comp_data['codice_iata'].lower()}.com")
            print(f"  Password: password123")

if __name__ == '__main__':
    init_database()
